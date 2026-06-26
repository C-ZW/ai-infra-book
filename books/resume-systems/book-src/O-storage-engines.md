# O · 儲存引擎與資料模型

這個領域解的是「資料落到磁碟之前那一層」的問題：同樣一張表，底下用什麼結構排列位元組，決定了你寫得快還是讀得快、放不放得下、刪不刪得乾淨。本檔含五條：底層結構的兩大流派（LSM-tree vs B-tree）、所有引擎賴以存活的崩潰保護（WAL）、資料模型的選型地圖（SQL vs NoSQL 各家族）、全文搜尋的核心資料結構（inverted index）、以及資料的「死法」（retention / TTL / 封存 / 軟刪除 / 合規刪除）。邊界：交易隔離與一致性語意在領域 B、快取與物件儲存在領域 G、跨庫同步與對帳在領域 L——本檔只談「單機引擎怎麼把資料存好、查到、刪掉」。

## LSM-tree vs B-tree（寫放大 vs 讀放大）

### 定義與原理

一個儲存引擎的核心抉擇是：**資料在磁碟上要「就地維護有序」還是「先追加、之後再整理」。** 這個抉擇分出兩大流派。

**B-tree（實務上多為 B+tree）**：把鍵維持在一棵高扇出、平衡的樹裡，所有資料在葉節點且就地（in-place）更新。一次查詢從根走到葉，路徑長度約 `log_B(N)`（B 是每頁能放的鍵數，常數百到上千）。一次寫入要找到對應頁、改它、刷回磁碟——**改一個值就要改寫整個頁（page，常見 4–16 KiB）**，這是 B-tree 的寫放大來源。讀則很直接：一條路徑到底，命中即得。

**LSM-tree（Log-Structured Merge tree）**：寫入永不就地更新。新值先進記憶體裡的有序結構（memtable），滿了就整批 flush 成一個不可變的有序檔（SSTable，sorted string table），檔與檔之間靠背景 **compaction（壓實）** 逐層合併、丟棄被覆蓋的舊版本與墓碑（tombstone）。寫入因此是「順序追加」，對 SSD/HDD 都友善——但代價是**一個鍵的最新值可能散在多個 SSTable**，讀取得從新到舊一層層找（靠 bloom filter 與每層稀疏索引剪枝），這是 LSM 的讀放大來源。

一句話的脊椎：**B-tree 把整理成本付在寫入當下（就地維護有序），LSM 把它延後到背景 compaction（換取寫入是純追加）。** 兩者都是「在寫放大、讀放大、空間放大之間選你願意付的那個」。

**代表系統現況（2026-06，已查證）**：
- **LSM 流派**：RocksDB（Meta，基於 LevelDB 演化，最新穩定版約 11.0.x／2026-04）、LevelDB、Apache Cassandra（5.0 起導入 BTI SSTable 格式與 Unified Compaction Strategy）、TiKV、CockroachDB 底層皆 LSM。
- **B-tree 流派**：PostgreSQL（heap 表 + B-tree 次級索引）、MySQL InnoDB（clustered B+tree，主鍵即葉節點順序；InnoDB 自 MySQL 5.5 起為預設引擎、8.4 LTS 仍然）。

### 解法空間

「我要怎麼把有序資料存上磁碟」這題的辦法，沿一條軸展開：

- **純 B+tree（就地更新）**：傳統 RDBMS 預設。讀延遲穩定、範圍掃描漂亮、空間放大低；寫入受隨機 I/O 與頁改寫拖累。
- **純 LSM（追加 + compaction）**：寫密集、SSD 友善。寫吞吐高、壓縮率好；讀延遲受層數與 compaction 進度影響、有尾延遲。
- **可調 LSM compaction 策略**：同樣 LSM，換 compaction 策略就換取捨——
  - **Leveled（分層）**：每層大小遞增、層內不重疊鍵，讀放大低（一個鍵每層至多一個 SSTable），寫放大高。
  - **Size-tiered（分桶）**：同大小的 SSTable 攢夠就合併，寫放大低，但同一鍵可能散在多桶、讀放大與空間放大高。
  - **Unified / 混合**：Cassandra 5.0 的 UCS、RocksDB 的 universal compaction，用一個密度參數在 leveled 與 tiered 之間連續調節。
- **Fractal/Bw-tree 等變體**：在 B-tree 葉子掛 delta buffer 攢寫、延後合併，想取兩者之長；實作複雜，較少見。
- **混合儲存**：同一個系統熱資料走一種、冷資料走另一種（見「資料生命週期」本領域）。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| B+tree（PostgreSQL／InnoDB） | 穩定低讀延遲、優秀範圍掃描、低空間放大、就地讀即最新 | 讀多寫少、需要強範圍查詢與複雜索引、OLTP | 隨機寫成本高；頁分裂（page split）造成碎片；高寫入吞吐會被 I/O 與鎖頂住 |
| LSM（RocksDB／Cassandra） | 高寫吞吐（順序寫）、好壓縮率、SSD 壽命友善 | 寫密集、時序、KV、append-heavy 工作負載 | 讀放大與尾延遲（多 SSTable 查找）；compaction 吃 CPU/I/O、會與前台爭資源；刪除靠墓碑、空間延遲回收 |
| Leveled compaction | 讀放大低（每鍵每層 ≤1 SSTable）、空間放大低 | 讀偏多的 LSM 工作負載 | 寫放大最高（一筆資料可能被重寫多次） |
| Size-tiered compaction | 寫放大低 | 寫極密、可容忍讀放大的工作負載 | 空間放大高（合併前舊版本佔位）、讀要查多桶 |

**Worked example（寫放大量級感）**：假設 leveled LSM 共 5 層、層間放大係數 10，最壞情況下一筆資料從 L0 一路被 compaction 重寫到 L4，每下一層都被讀出再寫回，**寫放大可達約 5×10/2 ≈ 25 倍**（粗估，與資料分布有關）。對照同樣一筆 100-byte 的更新打進 B+tree：若它落在一個 16 KiB 的頁，最小刷盤單位就是那 16 KiB，**頁層級寫放大約 16384/100 ≈ 164 倍**——這正解釋了「為什麼小筆高頻更新的工作負載，LSM 常常整體寫放大反而更低」這個反直覺結論：B-tree 的放大藏在頁粒度裡。

### 何時需要

- **選 B-tree**：工作負載讀多於寫、需要可預測的低讀延遲（如金融讀路徑）、大量範圍查詢與排序、需要豐富的次級索引與外鍵——絕大多數 OLTP 系統的預設選擇就對了。
- **選 LSM**：寫入是瓶頸（時序、事件日誌、計數器、IoT、寫密集 KV）、資料量大且要好壓縮、能接受讀有尾延遲。
- **不需要操心這層**：用通用 RDBMS 跑一般 CRUD 時，引擎的預設結構已經夠好，與其換引擎不如先加對索引、修掉 N+1（見 N+1 查詢，領域 S）。選錯結構是「寫吞吐撞到天花板」或「冷資料壓不下去」時才該重新審視的決策，不是起手式。

### 常見誤解與陷阱

- **「LSM 一定比 B-tree 寫得快」**：只在「寫放大佔主導」時成立。鍵很大、value 很大、或讀路徑被 compaction 尾延遲拖累時，LSM 不一定贏。
- **「LSM 的刪除立刻釋放空間」**：錯。LSM 刪除只是寫一個墓碑，真正的空間要等 compaction 把墓碑與被覆蓋的舊版本都清掉才回收；墓碑過多（大量刪除/TTL 過期）會讓讀變慢，這是時序資料庫的經典陷阱（見「資料生命週期」本領域）。
- **「B-tree 沒有寫放大」**：頁粒度本身就是寫放大；隨機寫造成的頁分裂與碎片還會放大它。
- **「compaction 是免費的背景工作」**：它與前台讀寫爭 CPU/I/O，調不好會造成週期性延遲尖峰。
- **把 compaction 策略當成不可調的常數**：同一個 LSM 引擎換策略（leveled↔tiered↔unified）就是換一整組讀/寫/空間放大取捨，是個第一級調校旋鈕。

### 延伸閱讀

- Patrick O'Neil et al., *The Log-Structured Merge-Tree (LSM-Tree)*（1996 原始論文）: https://www.cs.umb.edu/~poneil/lsmtree.pdf
- Luo & Carey, *LSM-based Storage Techniques: A Survey*（VLDB Journal 2020）: https://arxiv.org/abs/1812.07527
- RocksDB Wiki — RocksDB Overview: https://github.com/facebook/rocksdb/wiki/RocksDB-Overview
- Apache Cassandra — Unified Compaction Strategy: https://cassandra.apache.org/_/blog/Apache-Cassandra-5.0-Features-Unified-Compaction-Strategy.html

## WAL 預寫日誌

### 定義與原理

**Write-Ahead Logging（WAL，預寫日誌）的鐵律一句話：在把任何資料頁的變更寫到它最終的位置之前，先把「這個變更」以順序追加的方式寫進一個日誌、並讓它落穩（durable）。** 之所以叫「預寫」，就是日誌寫在資料頁之前。

它解的是**崩潰原子性與持久性**：行程在改了一半資料頁時被斷電/被 kill，磁碟上會是個半完成的爛狀態。有了 WAL，重啟時引擎重放（replay）日誌——已提交但未刷到資料頁的，redo 補上；未提交卻已沾染資料頁的，undo 回滾——把資料庫帶回一個一致的點。WAL 是 ACID 裡 **D（durability）與 A（atomicity）** 的物理實作基礎（隔離與一致性語意見領域 B）。

第一原理：**順序寫遠快於隨機寫。** WAL 把「許多筆散落各處的隨機資料頁更新」轉成「一條順序追加的日誌」，先讓日誌落穩拿到 durability，資料頁可以稍後再從容刷回（checkpoint）。這也是 LSM 與 B-tree 引擎都帶 WAL 的原因——RocksDB 有 WAL、PostgreSQL 有 WAL、InnoDB 有 redo log，本質都是同一招。

### 解法空間

WAL 的設計變奏圍繞「日誌何時算落穩、落穩到哪」：

- **fsync 時機（per-commit vs 批次 group commit）**：每筆交易提交都 fsync（最安全、最慢）vs 把多筆並發提交的 fsync 合併成一次（group commit，攤平 fsync 成本）。
- **fsync 嚴格度**：嚴格 fsync（等磁碟回報落穩）vs 放寬（只寫到 OS page cache 就回、靠定時 flush）——後者快但崩潰會丟最後一小段。
- **日誌格式**：physical logging（記改了哪個 byte/頁的影像）／logical logging（記「做了什麼操作」）／physiological（折衷：頁內邏輯、頁間物理，InnoDB redo log 走這路）。
- **checkpoint 策略**：多久把資料頁刷回一次、刷多少——影響崩潰後要重放多長的日誌（recovery 時間）與平時的 I/O 平滑度。
- **WAL 的二次利用**：同一條日誌天然能當複製串流（PostgreSQL 邏輯/物理複製、MySQL binlog）與 CDC 來源（見 CDC，領域 L）——WAL 不只防崩潰，它是真相的有序流水帳。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 每筆提交 fsync | 提交即持久，崩潰零丟失（在磁碟誠實的前提下） | 金流、不可丟的交易 | 受單次 fsync 延遲限制吞吐；高頻提交須配 group commit |
| group commit | 攤平 fsync 成本，吞吐大增、仍零丟失 | 高並發 OLTP | 個別交易延遲略增（要等湊批）；需引擎支援 |
| 放寬 fsync（如每秒 flush） | 吞吐最高 | 可容忍崩潰丟最後 ~1 秒的場景（快取、計數、可重算資料） | 崩潰會丟最後一個 flush 窗口的已「提交」資料——名義 durable、實際不是 |
| WAL 當複製/CDC 來源 | 下游可重建狀態、順序一致 | 複製、CDC、event sourcing | 日誌保留期、消費者落後、格式相容性都要管（見領域 L） |

**Worked example（fsync 主導吞吐）**：一顆需要 fsync 落穩的 SSD，單次 durable fsync 約 1 ms。若每筆交易各自 fsync，單執行緒提交吞吐天花板 ≈ 1000 commits/s。開 group commit、把同一個 ~1 ms 窗口內到達的 100 筆並發提交合併成一次 fsync，**有效吞吐躍升到約 100,000 commits/s**——這就是為什麼高並發資料庫離不開 group commit：瓶頸從來不是 CPU，是那一次次 fsync。

### 何時需要

- **任何宣稱「提交後資料不會因崩潰而丟」的系統，必有等價於 WAL 的機制**——你用 RDBMS 就已經在用它，不必自己造。
- **要自己實作 WAL** 的場景：寫自訂儲存引擎、嵌入式 KV、需要崩潰一致的本地佇列/狀態機。
- **可以放寬甚至省略 durable WAL**：資料本身可重算或可從上游重放（快取、衍生視圖、能從 Kafka 重放的物化結果）——這時硬要 per-commit fsync 是付了持久性的成本卻不需要那個保證。
- **要動 WAL 的 fsync 旋鈕**：當崩潰丟失的容忍度與吞吐需求有明確結論時，才去調 `synchronous_commit`／`innodb_flush_log_at_trx_commit` 這類參數，並寫進文件——這是個「拿持久性換吞吐」的明確取捨，不該是某人隨手改的。

### 常見誤解與陷阱

- **「寫進 WAL 就持久了」**：只有當 `write()` 後接了成功的 `fsync()`（且磁碟/控制器沒在說謊地快取）才持久。很多「資料神祕消失」的事故是 OS page cache 或磁碟 write cache 在 fsync 上撒謊。
- **「WAL 讓寫變慢」**：恰恰相反——它把隨機資料頁寫換成順序日誌寫，通常讓整體寫更快；慢的是不必要的 per-commit fsync，那是另一回事。
- **把放寬 fsync 的設定當預設值帶上線**：開發環境圖快關掉 durable fsync、忘了上 production，崩潰才發現提交其實沒落穩。
- **忽略 checkpoint 與 WAL 保留**：WAL 無限長會塞爆磁碟；checkpoint 太疏會讓崩潰恢復重放很久（recovery 時間 = RTO 的一部分）。
- **以為 WAL 防得了應用層邏輯錯誤**：WAL 保證的是「把你下的指令原子且持久地做下去」，它忠實地把一筆錯誤刪除也持久化了——它防崩潰，不防 bug。

### 延伸閱讀

- C. Mohan et al., *ARIES: A Transaction Recovery Method...*（WAL 恢復的奠基論文，1992）: https://dl.acm.org/doi/10.1145/128765.128770
- PostgreSQL 官方文件 — Write-Ahead Logging (WAL): https://www.postgresql.org/docs/current/wal-intro.html
- MySQL 官方文件 — InnoDB redo log: https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html

## SQL vs NoSQL（文件 / KV / 寬欄 / 圖 / 時序各擅場）

### 定義與原理

「SQL vs NoSQL」表面是查詢語言之爭，**本質是資料模型與一致性／擴展取捨之爭**。關係模型（SQL）的核心保證是：固定 schema、宣告式 join、跨列跨表的 ACID 交易；它把「資料如何被查」與「資料如何被存」解耦，讓你事後才決定查法。NoSQL 不是單一東西，而是一組「為了某個特定存取模式而放棄關係模型某部分」的家族——放棄通常換來水平擴展、寫吞吐、或更貼合資料形狀的模型。

判斷的第一原理：**先問存取模式，再選模型。** 關係庫讓你「先存好、查法之後想」；多數 NoSQL 要你「先想清楚怎麼查，再決定怎麼存」（尤其寬欄與 KV 是圍繞主要查詢設計 partition key 的）。

### 解法空間

這是個「分類型」條目——以下是各模型的機制與擅場，而非單一解法：

- **關係（SQL）**：列存於表、固定 schema、B-tree 索引、宣告式 join 與多表 ACID 交易。擅長：實體關係複雜、需要事後任意查詢與報表、需要強交易一致性。代表：PostgreSQL、MySQL。
- **文件（document）**：以巢狀 JSON-like 文件為單位存取，schema 彈性、聚合資料就近放在一個文件裡（避 join）。擅長：聚合根明確、欄位多變、讀寫以「整份文件」為粒度。代表：MongoDB、Couchbase。
- **鍵值（KV）**：`key → opaque value`，O(1) 查找、無查詢結構。擅長：快取、session、極簡高速查找。代表：Redis（見 Redis，領域 G）、DynamoDB（KV/文件混合）。
- **寬欄（wide-column）**：`(partition key, clustering key) → 列`，圍繞查詢設計的 LSM 引擎，寫吞吐極高、線性水平擴展。擅長：寫密集、已知查詢路徑、大規模時間序列化資料。代表：Cassandra、HBase、ScyllaDB。
- **圖（graph）**：節點＋邊為一等公民，遍歷（traversal）是原生操作、不靠遞迴 join。擅長：多跳關係查詢（社交、推薦的鄰接、權限鏈、詐欺偵測的關聯）。代表：Neo4j、Amazon Neptune。
- **時序（time-series）**：以時間為主軸、針對 append-only 與時間範圍聚合最佳化（常配自動 retention/降採樣）。擅長：監控指標、IoT、事件計數。代表：TimescaleDB（PostgreSQL 擴充）、InfluxDB、Prometheus。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 關係（PostgreSQL/MySQL） | 固定 schema、多表 ACID、宣告式任意查詢、外鍵完整性 | 複雜實體關係、報表、強交易 | 水平擴展（分片）需自己做、跨分片 join/交易困難（見分片，領域 B） |
| 文件（MongoDB） | 彈性 schema、單文件原子更新、聚合就近 | 聚合根清楚、欄位多變 | 跨文件交易雖支援但昂貴；schema 彈性會養出「隱形 schema 漂移」 |
| KV（Redis/DynamoDB） | O(1) 查找、極高吞吐、易水平擴展 | 快取、session、簡單查找 | 無原生 join/二級查詢（DynamoDB 靠 GSI 補）；查法綁死 key 設計 |
| 寬欄（Cassandra） | 線性水平擴展、寫吞吐極高、可調一致性 | 寫密集、已知查詢、跨區 | 一張表服務一種查詢（要反正規化、寫多份）；無 join；最終一致為常態 |
| 圖（Neo4j） | 原生多跳遍歷、關係即一等公民 | 深度關聯查詢 | 水平擴展與跨分片遍歷較難；超大圖的分區是公開難題 |
| 時序（TimescaleDB/InfluxDB） | 時間範圍查詢/聚合最佳化、自動 retention | 指標、IoT、事件 | 非時間維度的查詢弱；高基數 tag 會撐爆索引（見 cardinality 爆炸，領域 I） |

**Worked example（反正規化的代價）**：一個寬欄資料庫要同時支援「依使用者查訂單」與「依商品查訂單」兩種查詢，沒有 join，於是把同一筆訂單**寫進兩張表**（一張 partition by user、一張 partition by product）。10 萬筆訂單就變成磁碟上 20 萬筆列，寫入吞吐與儲存翻倍——這是寬欄模型用「寫放大與儲存成本」換「讀路徑無 join、可線性擴展」的具體標價。換成關係庫，這是一張表加兩個索引就解決的事，但那兩個索引的維護成本與單機擴展上限，又是另一邊的標價。

### 何時需要

- **預設先用關係庫**：除非有明確理由，PostgreSQL/MySQL 能服務絕大多數系統到很大規模；「NoSQL 比較潮/比較快」不是理由。
- **轉向某 NoSQL 家族的觸發點**：
  - 查詢路徑單一且寫吞吐撞單機天花板 → 寬欄/KV。
  - 資料天生是巢狀聚合、且幾乎不跨聚合查 → 文件。
  - 核心問題是「多跳關係遍歷」、用 join 寫到自己都怕 → 圖。
  - 資料是「時間戳 + 值」且查詢都是時間範圍聚合 → 時序。
- **polyglot persistence（混用）很常見也很正常**：交易資料在關係庫、快取在 Redis、指標在時序庫——別硬要一個庫包山包海。但每多一種庫就多一份維運、一致性與資料同步負擔（見領域 L）。

### 常見誤解與陷阱

- **「NoSQL 沒有 schema」**：應該說 schema 在「寫時不強制、讀時隱含存在」。應用程式仍假設欄位形狀；沒有 DB 把關，schema 漂移會在讀路徑炸開。
- **「NoSQL 一定比 SQL 快/可擴展」**：快的是「它被設計來服務的那一種查詢」；換個查法常常更慢甚至做不到。關係庫也能分片擴展，只是工你來做。
- **「文件庫可以避免所有 join」**：只在聚合邊界與查詢邊界吻合時成立；一旦要跨聚合關聯，你會在應用層手刻 join，那更糟。
- **「上 NoSQL 就放棄了交易」**：不一定——許多 NoSQL 提供單鍵/單文件原子性，部分（如 MongoDB、DynamoDB）有多項交易，但通常較貴、範圍受限。要看清楚它保證的交易邊界，而非二分法。
- **用時序庫存高基數維度**：把 user_id 當 tag 塞進時序庫，基數爆炸會拖垮它——時序庫的甜蜜點是「低基數標籤 + 高頻時間點」。

### 延伸閱讀

- Martin Kleppmann, *Designing Data-Intensive Applications*, Ch. 2（資料模型與查詢語言）: https://dataintensive.net/
- Codd, *A Relational Model of Data for Large Shared Data Banks*（1970 關係模型原典）: https://dl.acm.org/doi/10.1145/362384.362685
- MongoDB 官方文件 — Data Modeling Introduction: https://www.mongodb.com/docs/manual/data-modeling/
- Apache Cassandra 官方文件 — Data Modeling: https://cassandra.apache.org/doc/latest/cassandra/developing/data-modeling/index.html

## 全文搜尋與 inverted index

### 定義與原理

關係庫的 `LIKE '%word%'` 為什麼慢到不能用？因為它對每一列做子字串掃描，是 O(N × 文件長度) 的全表掃描，且無法走索引。**全文搜尋的核心資料結構是 inverted index（倒排索引）**，它把這題從「掃所有文件找詞」翻轉成「查一個詞直接拿到含它的文件清單」——這就是「倒排」的意思：不是 `文件 → 詞`，而是 `詞 → 文件清單`。

機制三步：
1. **Analysis（分析）**：把文件文字切成 token（tokenization）、正規化（小寫、去標點、stemming 把 running→run、去 stop words）。中文/日文無空格，需斷詞器（如 jieba、ICU），這步直接決定搜得到搜不到。
2. **建立 postings**：對每個 term（正規化後的詞），維護一個 **posting list**——含該 term 的文件 ID 列表，常附位置資訊（positions，用於片語查詢「恰好相鄰」）與詞頻（term frequency）。
3. **查詢**：把查詢字也跑一遍同樣的 analysis，得到 term，去 inverted index 取各 term 的 posting list，再對多個 list 做交集（AND）／聯集（OR）／差集（NOT），得到候選文件集。

範圍界定：**本條只講 inverted index 這個資料結構與機制。** 拿到候選文件後「哪篇最相關、怎麼排序」（TF-IDF、BM25、向量檢索）屬於相關度排序，是搜尋域、本書全域不涵蓋，不展開。

### 解法空間

「我要支援關鍵字搜尋」的辦法：

- **`LIKE '%x%'`／全表掃描**：零建置、能跑，但 O(N) 不可規模化、不能用索引、無斷詞與正規化。
- **資料庫內建全文索引**：PostgreSQL 的 `tsvector`/`tsquery` + GIN 索引、MySQL 的 `FULLTEXT` 索引——本質就是在 RDBMS 裡建一個 inverted index，省一個外部系統。
- **trigram 索引**（如 PostgreSQL `pg_trgm`）：把字串切成 3-gram 建索引，能加速模糊/子字串匹配，但不是真正的詞級全文搜尋。
- **專用搜尋引擎**：Elasticsearch / OpenSearch、Apache Lucene（前兩者的底層）、Apache Solr——獨立的 inverted index 系統，附完整 analysis pipeline、分散式分片、近即時索引。
- **嵌入式搜尋庫**：Lucene、Tantivy、SQLite FTS5——把 inverted index 嵌進你的行程，免維運外部叢集。

posting list 本身還有壓縮機制：文件 ID 排序後存差值（delta encoding）再做 variable-byte/Roaring bitmap 壓縮，這是搜尋引擎能把巨大索引塞進記憶體的關鍵。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| `LIKE '%x%'` | 零建置、即時最新 | 資料量小（千級）、偶爾查 | O(N) 掃描，資料一大就垮；無斷詞/正規化 |
| PostgreSQL GIN + tsvector | 真正詞級索引、與交易資料同庫同交易、即時 | 中等規模、不想多養一個系統 | analysis 能力與 ranking 不如專用引擎；中文需額外斷詞配置 |
| pg_trgm 三元組 | 加速模糊/子字串/拼錯容忍 | 自動完成、相似字串 | 非詞級語意；索引較大 |
| Elasticsearch/OpenSearch（Lucene） | 強 analysis、分散式、近即時、豐富查詢 | 大規模、複雜搜尋、需求高 | 額外系統與維運；與來源庫之間是最終一致（要同步，見領域 L）；非交易性 |

**Worked example（倒排的量級）**：一個含 100 萬篇文件、平均每篇 200 個 term 的語料，總共約 2 億個 token。要查「同時含 `payment` 與 `refund`」的文件：`LIKE` 路徑要掃 100 萬篇做子字串比對；inverted index 路徑只取 `payment` 的 posting list（假設命中 5,000 篇）與 `refund` 的（假設 3,000 篇），對兩個已排序的 ID 列表做交集，成本約 O(5000 + 3000) = 8,000 次比較——**從百萬級降到萬級**，這就是倒排把搜尋從掃描變成查找的具體效益。

### 何時需要

- **需要 inverted index/全文搜尋**：使用者要對自由文字下關鍵字、片語、布林查詢，且資料量讓 `LIKE` 不可行。
- **先用 DB 內建全文**：中小規模、且搜尋不是核心競爭力時，PostgreSQL GIN/MySQL FULLTEXT 足夠，省掉一個分散式系統與一條資料同步管線。
- **才上 Elasticsearch/OpenSearch**：規模、近即時、複雜 analysis（多語言、同義詞、自訂分詞）或高查詢吞吐成為真實需求時。引入它＝引入一條「來源庫 → 搜尋索引」的同步管線與它的最終一致性問題。
- **over-engineering 警訊**：為了「未來可能要搜尋」就先架一座 ES 叢集，卻只有幾萬筆資料——這是用維運複雜度換一個還沒到來的需求。

### 常見誤解與陷阱

- **「全文搜尋就是 `LIKE` 加速版」**：不是。`LIKE '%x%'` 是子字串匹配、無語意；全文搜尋有 analysis（斷詞、stemming、stop words），兩者結果與能力都不同。
- **忽略 analysis 階段**：索引與查詢必須用**同一套** analyzer，否則建索引時 `Running` 存成 `run`、查詢時 `running` 沒被 stem，就搜不到。中文不配斷詞器，等於沒切詞。
- **把 Elasticsearch 當主資料庫**：它是搜尋索引、近即時、非交易性，且與來源庫最終一致——它可能丟你的權威資料，不該當 source of truth。
- **以為 inverted index 自帶排序相關性**：資料結構只給你「哪些文件含這些詞」；「哪篇最相關」是另一層（ranking，本書不涵蓋）。
- **位置資訊的成本**：要支援片語查詢（"machine learning" 恰好相鄰）就得存 positions，索引顯著變大——不需要片語就別開。

### 延伸閱讀

- Manning, Raghavan & Schütze, *Introduction to Information Retrieval*, Ch. 1（The inverted index）: https://nlp.stanford.edu/IR-book/
- PostgreSQL 官方文件 — Full Text Search: https://www.postgresql.org/docs/current/textsearch.html
- Apache Lucene — 官方文件: https://lucene.apache.org/core/

## 資料生命週期（retention / TTL / 封存 / 軟刪除 / 合規刪除）

### 定義與原理

資料不是寫進去就永遠躺著——它有生命週期。**這條解的問題是：每一筆資料應該活多久、老了去哪、被「刪除」時到底發生了什麼。** 把這件事當設計問題而非事後補救，是區分「成熟系統」與「磁碟總有一天會滿、且某天收到合規刪除令時手忙腳亂」的分水嶺。

核心是區分幾種語意上完全不同的「結束」：

- **Retention（保留期）**：資料保留多久的政策，到期即清。
- **TTL（time-to-live）**：給單筆資料的存活時長，由引擎自動到期清除（Redis key TTL、DynamoDB TTL、時序庫的 retention policy）。
- **封存（archival）**：不刪，但從熱儲存搬到冷儲存（如物件儲存／冷層，見 S3，領域 G）——降成本、仍可取回。
- **軟刪除（soft delete）**：不真的刪，標記 `deleted_at`／`is_deleted`，列還在、只是查詢過濾掉它。可復原、可審計。
- **合規刪除（hard / compliant delete）**：把資料**真正地、不可復原地**從所有副本（含備份、快取、衍生索引、日誌）抹掉，以滿足法規（GDPR Art. 17 right to erasure、CCPA 等）。

關鍵張力：**軟刪除 ≠ 合規刪除。** 軟刪除對使用者「看起來刪了」，但資料仍在磁碟——對「右被遺忘權」這種法規要求是**不合規**的。這兩個被混為一談是本領域最危險的陷阱。

### 解法空間

- **TTL 自動過期**：引擎層設每筆資料存活時長，背景回收。最省心，但回收是惰性/批次的（過期 ≠ 立刻被刪，見陷阱）。
- **分區輪替（partition rotation）**：按時間分區（如每日一個 partition），過期就 `DROP PARTITION`——比逐列刪快得多，是時序資料的標準做法。
- **冷熱分層 + 封存**：熱層保留近期、過期搬冷層（物件儲存/Glacier 類），保留可取回性、砍成本。
- **軟刪除**：寫 `deleted_at`，配合查詢層統一過濾與唯一索引處理（軟刪除的列仍佔用唯一鍵，需設計）。
- **合規硬刪除管線**：收到刪除請求 → 在主庫硬刪 → 連鎖刪除/匿名化所有衍生資料（搜尋索引、快取、analytics、日誌）→ 處理備份（標記「beyond use」或等備份輪替過期）→ 留下「已刪除」的稽核憑證（但憑證本身不含個資）。
- **匿名化/假名化替代刪除**：法規允許時，用不可逆匿名化（讓資料無法再關聯到個人）取代物理刪除，保留統計價值。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| TTL 自動過期 | 引擎自動回收、零維運 | 快取、session、可丟的時序資料 | 過期是惰性/背景的，「過期」與「實際被刪」之間有窗口；不適合當合規刪除手段 |
| 分區輪替 DROP | O(1) 砍掉整段時間資料 | 時序/日誌、按時間 retention | 需一開始就按時間分區；粒度受分區大小限制 |
| 封存到冷層 | 大幅降成本、仍可取回 | 法規要求長期保存、低頻存取 | 取回有延遲與費用；冷層資料也受合規刪除約束 |
| 軟刪除 | 可復原、保留審計與外鍵完整性 | 使用者「刪除」可反悔、需稽核 | **不是合規刪除**；deleted 列仍佔空間與唯一鍵；查詢全得記得過濾，漏一處就外洩 |
| 合規硬刪除 | 法規意義上真正抹除、不可復原 | GDPR/CCPA 刪除請求 | 必須涵蓋所有副本（備份/快取/索引/日誌）；不可復原，誤刪無救；要有稽核軌跡 |

**Worked example（合規刪除的爆炸半徑）**：一筆使用者資料在系統裡的副本遠不只主庫一份：主庫 1 份、read replica 2 份、Redis 快取 1 份、Elasticsearch 搜尋索引 1 份、資料倉/analytics 1 份、每日備份保留 30 天 = 30 份、應用日誌裡夾帶的 PII = 不定份。收到一筆 GDPR Art. 17 刪除請求，「真正刪掉」要協調**這 36+ 處**。漏掉備份或搜尋索引，就是名義合規、實際外洩。GDPR 違規上限為 **€20M 或全球年營業額 4%**（取高者，2026-06 查證），所以合規刪除是「一個刪除動作要設計成一條覆蓋全副本的管線」，不是 `DELETE FROM users WHERE id=?` 一行了事。

### 何時需要

- **每個存使用者資料的系統都需要一套生命週期政策**——區別只在嚴格度。沒有政策＝磁碟無限增長 + 法規來敲門時的危機。
- **必須有合規硬刪除**：處理 EU/加州/受 GDPR-CCPA 影響使用者的個資時，是法律義務、非選配。
- **軟刪除足夠的場景**：內部資料、需要「垃圾桶/復原」、需保留審計鏈、且不受被遺忘權約束。
- **TTL/分區輪替足夠**：資料本質短命或純時序（快取、session、原始日誌、指標）。
- **over-engineering 警訊**：對一個不含任何個資的內部工具，套一整套合規刪除管線是浪費——先確認資料分類，再決定嚴格度。

### 常見誤解與陷阱

- **把軟刪除當合規刪除**：最危險的一條。`deleted_at IS NOT NULL` 的列資料還躺在磁碟與備份裡，對「右被遺忘權」完全不合規。
- **忘了備份與衍生副本**：主庫刪了，備份/快取/搜尋索引/analytics/日誌裡的影子還在。合規刪除的爆炸半徑是「所有副本」，不是一張表。
- **TTL 過期 ≠ 立刻刪除**：Redis 的過期是惰性 + 取樣式背景回收，DynamoDB TTL 官方說明刪除是 best-effort、通常於數日內完成——「設了 TTL」不等於「過期那一秒資料就不在了」，安全/合規敏感場景別倚賴它的即時性。
- **軟刪除列撐爆唯一索引**：軟刪一個 `email` 後使用者想用同 email 重註冊，卻被唯一索引擋住——軟刪除與唯一約束的互動要一開始就設計（如把 email 加進部分索引條件、或刪除時改寫值）。
- **LSM 引擎的刪除是墓碑**：在 Cassandra/RocksDB 上「刪除」只是寫墓碑，空間要等 compaction 才回收；大量刪除/TTL 過期累積的墓碑會拖慢讀取（見「LSM-tree vs B-tree」本領域）——以為刪了就釋放空間是錯的。
- **無限保留「以防萬一」**：留越多資料＝越大的外洩面與合規負擔。資料是負債也是資產；該過期就讓它過期。

### 延伸閱讀

- GDPR Art. 17 — Right to erasure（'right to be forgotten'）原文: https://gdpr-info.eu/art-17-gdpr/
- UK ICO — Right to erasure（合規實作指引）: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/
- DynamoDB 官方文件 — Time to Live (TTL)（過期刪除非即時的說明）: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html
