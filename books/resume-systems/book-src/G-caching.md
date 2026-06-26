# G · 快取與儲存

快取用「一份較快但可能過時的副本」換吞吐與延遲，代價是多了一致性與失效的責任；本領域回答的是：你願意讓資料舊多久、容忍多大一致性裂縫，換多少 IOPS 與延遲省下來。本檔含七個條目：快取策略（cache-aside／write-through／write-behind）、失效與三種快取災難（雪崩／穿透／擊穿）、驅逐 eviction、快取存的持久化（RDB vs AOF）、多層快取與快取層降級，外加兩個工具條目——Redis（本書 Redis 內部機制的 owning 條目）與 S3／物件儲存。邊界：通用 fallback／降級機制在領域 P，本檔的「優雅降級」只談快取層那一段；交付語意與 Redis Pub/Sub vs Streams 的交付差異在領域 A，本檔的 Redis 只深講內部機制與多重角色；分散式鎖的正確性（Redlock／fencing token）在領域 M，本檔只點 Redis 作為鎖底層的限制。

## 快取策略（cache-aside / write-through / write-behind）

### 定義與原理

快取策略要回答的不是「要不要快取」，而是**讀路徑誰負責填快取、寫路徑何時更新快取與底層儲存、兩者的先後**。三個維度組合出常見的三種模式：讀觸發填充（cache-aside / look-aside）、寫同步雙更（write-through）、寫非同步回寫（write-behind / write-back）。第一原理只有一條：**快取與資料庫是兩份獨立狀態，任何「先寫哪個、後寫哪個、中間能不能崩」的排列，都對應一種一致性風險與一種效能收益。** 選策略＝選你能接受哪種裂縫。

### 解法空間

- **cache-aside（旁路快取）**：應用程式自己讀寫快取。讀：先查快取，miss 就讀 DB、回填快取、設 TTL。寫：更新 DB 後**刪除**（而非更新）快取項，讓下次讀重新填。快取只是 DB 的旁路副本，DB 是真相來源。
- **read-through**：把「miss 就回填」的邏輯收進快取層／client library，應用程式只對快取讀；語意接近 cache-aside，差別是回填責任在快取元件而非業務碼。
- **write-through（寫穿）**：寫時同步寫快取**與** DB，兩者都成功才回應。讀永遠命中且新鮮，代價是寫延遲＝兩段之和。
- **write-behind / write-back（回寫）**：寫只更新快取就回應，由背景批次／非同步把髒項刷回 DB。寫延遲最低、可合併多次寫，但快取崩潰會丟掉未刷回的資料。
- **write-around**：寫只進 DB、不碰快取，靠後續讀 miss 自然回填。適合寫多讀少、避免把一次性寫資料灌進快取。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| cache-aside | DB 為真相；快取最終一致 | 讀多寫少、可容忍短暫舊讀 | 寫後「先更 DB 再刪快取」仍有罕見競態（見下）；miss 風暴要配防擊穿 |
| read-through | 同上，回填邏輯集中 | 想把快取邏輯藏進元件 | 快取元件需懂 DB schema，耦合上移 |
| write-through | 讀恆新鮮、恆命中 | 讀後立即重讀、要求一致 | 寫延遲＝cache+DB；冷資料也被寫進快取浪費記憶體 |
| write-behind | 寫延遲最低、可合併寫 | 高頻寫、可容忍丟少量最新寫 | 快取崩潰丟未刷回資料；需處理刷回失敗、順序、背壓（見領域 E） |
| write-around | 不污染快取 | 一次性寫、寫多讀少 | 寫後立即讀必 miss，首讀延遲高 |

worked example（cache-aside 寫競態）：兩個請求同時對同一鍵操作——A 讀 DB 得舊值 `v1`、B 更新 DB 為 `v2` 並刪快取、A 才把 `v1` 回填快取。此後快取卡在 `v1` 直到 TTL 到期。發生機率低（要求 A 的讀回填晚於 B 的刪），但在高並發熱鍵上一天可命中數次；防法是回填時用 `SET ... NX` 加短 TTL，或在寫路徑用延遲雙刪（更 DB→刪快取→延遲數百 ms 再刪一次）。即使如此也只是**降低**機率，不能消滅——這正是「快取與 DB 兩份狀態」的本質代價。

### 何時需要

- 讀遠多於寫、且讀可容忍毫秒到秒級的舊值 → cache-aside（預設首選，最簡單、爆炸半徑小）。
- 寫後極可能立刻被讀、且要求讀到自己剛寫的值（讀己之寫，見領域 B）→ write-through。
- 寫吞吐是瓶頸、且業務能接受「崩潰丟掉最後幾秒寫入」→ write-behind（通常用於計數器、metrics、可重算的聚合，不用於金流）。
- over-engineering 警訊：讀寫比接近 1:1、或資料總量小到 DB 自帶的 buffer pool 已能全駐記憶體時，外加一層快取只是多一個失效來源。

### 常見誤解與陷阱

- **「寫時更新快取比刪除好」**：更新快取看似省一次 miss，但兩個並發寫可能讓快取與 DB 的最終值不一致（寫順序在兩個系統可能相反）。cache-aside 標準做法是**刪除**讓下次讀重填，把一致性責任收斂到單一回填路徑。
- **「write-through 保證一致」**：它保證**讀命中時新鮮**，但若寫快取成功、寫 DB 失敗（或反之）而沒有原子提交，仍會分叉；要嘛接受短暫不一致，要嘛用 outbox 類機制（見領域 A）讓兩段最終一致。
- **把 write-behind 當持久儲存**：回寫快取的記憶體狀態是易失的；崩潰即失憶（見領域 J）。未刷回的寫就是會丟，這不是 bug 是設計取捨。

### 延伸閱讀

- AWS 白皮書〈Database Caching Strategies Using Redis〉（cache-aside / write-through 對照）：https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/welcome.html
- Redis 官方〈Client-side caching〉（read-through 與失效追蹤）：https://redis.io/docs/latest/develop/reference/client-side-caching/

## 失效 · 雪崩 · 穿透 · 擊穿

### 定義與原理

快取的省力來自「命中」，而命中率被三類失效災難侵蝕，它們的根因不同、解法也不同：

- **雪崩（cache avalanche）**：大量鍵在同一時刻集體失效（或快取整體重啟），瞬間把流量全打到 DB。根因是失效時間集中。
- **穿透（cache penetration）**：查詢的鍵**在 DB 裡根本不存在**，快取永遠 miss、每次都打到 DB（常見於惡意掃描不存在的 ID）。根因是「不存在」這個答案沒被快取。
- **擊穿（cache breakdown / hotspot invalid）**：**單一熱門鍵**過期的瞬間，大量並發請求同時 miss、同時去 DB 重建。根因是熱鍵＋同時重建。

三者的共通脊椎：**快取失效那一刻，後端要不要、會不會被流量擊垮。** 失效是快取最難的部分，因為它牽涉時間（何時過期）、空間（哪些鍵）與並發（多少請求同時撞上）。

### 解法空間

- **抗雪崩**：給 TTL 加隨機抖動（jitter），如 `base + rand(0, spread)`，把集體到期攤平到一段時間；快取重啟時預熱（warmup）熱資料；分層 TTL（見「多層快取」）。
- **抗穿透**：把「查無此鍵」也快取成空值（null caching）並設較短 TTL；或在快取前置 **Bloom filter**——一個機率資料結構，能斷言「一定不存在」（無偽陰性），擋掉根本不該查 DB 的鍵。
- **抗擊穿**：重建時用**互斥鎖／single-flight**，只放一個請求去 DB 重建、其餘等待結果；或對極熱鍵設「邏輯過期」（值永不物理過期，存一個過期時間戳，過期後由背景或單一請求非同步刷新，其餘讀仍回舊值）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| TTL 加 jitter | 失效時間分散、削平 DB 尖峰 | 大量同生成批次的鍵 | spread 太小無效、太大讓部分鍵過早失效降命中率 |
| null caching | 不存在的鍵也命中、擋穿透 | 大量查不存在 ID | 空值 TTL 要短，否則「之後真的新增」被舊空值遮住；佔記憶體 |
| Bloom filter | 「一定不存在」零誤判、省 DB 查詢 | 鍵空間大、穿透流量明顯 | 有偽陽性（誤判存在→仍查一次 DB）；刪除難（標準 Bloom 不支援刪除，用 counting/cuckoo 變體） |
| single-flight 鎖 | 同鍵同時只一個重建 | 少數超熱鍵 | 鎖超時要短於重建時間上限，否則鎖過期又群起重建；鎖本身是熱點 |
| 邏輯過期 | 熱鍵永不集體 miss | 不可容忍任何一次直穿 DB 的熱鍵 | 過期後短暫回舊值（最終一致）；需背景刷新機制 |

worked example（擊穿）：一個熱門商品頁的快取項 TTL 到期，當下讀取速率 5,000 QPS（均勻分佈≈每毫秒 5 個）。重建一次約需 20 ms，這段空窗內約有 **100 個**請求到達。沒有保護時，這約 100 個全部 miss、全部去 DB 重建同一份資料（相對穩態瞬間放大約 100×），20 ms 後快取才填回。加 single-flight 後：只有第 1 個請求去 DB，其餘約 99 個等同一把鎖、共享它的結果，空窗後的請求直接命中新快取——**重建空窗內打到 DB 的查詢從約 100 降為 1**。

### 何時需要

- 鍵集中由同一批次生成（例如夜間批次預熱整批）→ 一定要 jitter，否則隔天同一時刻集體到期。
- 對外開放、ID 可被枚舉的查詢端點 → 需要 null caching 或 Bloom filter 擋穿透。
- 有明確的少數超熱鍵（首頁、熱門商品、明星貼文）→ 需要 single-flight 或邏輯過期。
- over-engineering 警訊：流量小、DB 扛得住整批 miss 時，這些保護是多餘複雜度——先量「失效瞬間 DB 能不能撐」再決定。

### 常見誤解與陷阱

- **把三者混為一談**：雪崩是「多鍵同時失效」、擊穿是「單熱鍵失效」、穿透是「鍵不存在」。解法不同——對穿透加 jitter 沒用，對擊穿加 Bloom filter 沒用。先分類再開藥。
- **null caching 沒設短 TTL**：之後真的新增了該鍵，卻被長 TTL 的空值遮住，變成「明明有資料卻查不到」。
- **single-flight 鎖超時設太長**：若鎖 TTL 比重建還久而重建卡住，所有等待者一路阻塞直到鎖過期；若太短，鎖過期瞬間又是一輪群起重建（驚群再現）。
- **以為 Bloom filter 零誤判**：它只保證「說不存在就一定不存在」（無偽陰性），但會偽陽性（說存在其實不存在），偽陽性只是多查一次 DB、不影響正確性，但別把它當精確集合用。

### 延伸閱讀

- Burton Bloom, "Space/Time Trade-offs in Hash Coding with Allowable Errors", CACM 1970（Bloom filter 原始論文）：https://dl.acm.org/doi/10.1145/362686.362692
- Redis 官方〈Key eviction〉（含 TTL 與隨機抖動討論）：https://redis.io/docs/latest/develop/reference/eviction/

## 驅逐 eviction（LRU / LFU / TTL / LRM…）

### 定義與原理

驅逐回答的是：**記憶體滿了、又要寫新資料時，丟掉哪一個既有鍵。** 它和「過期（expiration）」是兩回事——過期是 TTL 到了主動清除（被動於存取時、或主動由背景採樣清除），驅逐是記憶體達上限時被動騰位。驅逐策略的第一原理：**用「哪些鍵未來最不可能被用到」的某種近似，換最高的留存命中率，但任何近似都有它被打敗的存取樣式。** 沒有對所有 workload 最佳的策略，只有對你的存取分布最不糟的。

### 解法空間

以 Redis 的 `maxmemory-policy` 為座標（OSS 預設為 `noeviction`，達上限即對寫入回錯）。8.6 起共 **10 種**策略（2026-06），維度是「候選範圍 × 淘汰準則」：

- **候選範圍**：`allkeys-*`（所有鍵都可淘汰）vs `volatile-*`（只淘汰設了 TTL 的鍵）。
- **淘汰準則**：
  - **LRU（Least Recently Used）**：淘汰最久沒被**存取**（讀或寫）的。Redis 是近似 LRU——對採樣的 `maxmemory-samples`（預設 5）個鍵比 idle time，非全域精確 LRU。
  - **LFU（Least Frequently Used）**：淘汰存取**頻率**最低的，用帶衰減的計數器近似，避免「曾經很熱、現在已冷」的鍵賴著不走。
  - **TTL（`volatile-ttl`）**：淘汰剩餘 TTL 最短的（快過期的先走）。
  - **Random**：隨機淘汰，最省 CPU、最不智慧。
  - **LRM（Least Recently Modified，8.6 新增 `volatile-lrm`／`allkeys-lrm`，2026-06）**：類似 LRU 但時間戳**只在寫入時更新、讀取不更新**。用於「被狂讀但不再被改」的鍵應該先被淘汰的場景。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| `noeviction`（OSS 預設） | 絕不丟資料；滿了就拒寫 | 快取即真相、丟資料不可接受 | 滿了寫入直接報錯，呼叫端必須處理；不是快取慣用 |
| `allkeys-lru` | 近似留住最近用過的 | 通用快取、所有鍵都是可丟副本 | 近似非精確；掃描型存取（一次性遍歷）會污染 recency |
| `allkeys-lfu` | 留住長期高頻鍵 | 熱度穩定、有明顯熱鍵 | 計數器需暖機；突發熱鍵起步慢 |
| `volatile-lru/lfu/ttl` | 只在有 TTL 的鍵中淘汰 | 快取與持久資料**共用**同一實例 | 若可淘汰的鍵都沒設 TTL，行為退化同 `noeviction`（無鍵可淘→寫入報錯） |
| `*-lrm`（8.6+） | 只看「最近是否被改」 | 讀重寫少、想先淘汰只讀不改的冷資料 | 被高頻讀但不更新的鍵會被優先淘汰——這正是它的目的，但若你其實想留住熱讀資料就選錯了 |
| `*-random` | O(1) 最省 CPU | 鍵價值均等、極端吞吐 | 命中率最差；幾乎只在診斷或特殊場景用 |

worked example（LRU vs LFU）：一個快取**容量上限 1,000 個鍵**，其中 10 個是長期熱鍵（每秒各被讀 100 次），快取已被它們與其他常用鍵占滿。某段時間做了一次全表掃描、陸續讀進 **5,000 個一次性的冷鍵**——容量只有 1,000，每個新冷鍵進來都得驅逐一個既有鍵：在 LRU 下，這些剛被讀的冷鍵 recency 最新、排在驅逐隊尾，反而把 10 個真正的熱鍵擠出去（掃描污染）；在 LFU 下，熱鍵的頻率計數（每秒 100 次）遠高於只被讀一次的冷鍵，冷鍵先被淘汰、10 個熱鍵留存。這就是讀重、且有掃描型查詢時 LFU 勝過 LRU 的典型情形。

### 何時需要

- 快取實例**純做快取**、所有鍵都是可重算副本 → `allkeys-lru`（最常見預設）或 `allkeys-lfu`（熱度穩定時）。
- 同一實例**混放**快取與不可丟的持久資料 → `volatile-*`，並確保持久資料**不設 TTL**、快取資料設 TTL，讓淘汰只動快取那批。
- 存取以讀為壓倒多數、且想保留「正在被更新」的活資料而非「只被狂讀的死資料」→ 考慮 `*-lrm`（8.6+）。
- over-engineering 警訊：資料量遠小於 `maxmemory` 時，永遠觸發不到驅逐，糾結策略是浪費——TTL（過期）才是你實際在用的清理機制。

### 常見誤解與陷阱

- **把驅逐當過期**：到了 TTL 自動消失是過期；記憶體滿才丟是驅逐。`noeviction` 下 TTL 仍會讓鍵過期，只是滿了不會再額外驅逐。
- **`volatile-*` 卻沒鍵設 TTL**：若所有鍵都沒 expire，`volatile-*` 找不到可淘汰的鍵，寫入會像 `noeviction` 一樣報錯——靜默地退化成「滿了就掛」。
- **以為 Redis LRU 是精確的**：它是採樣近似；`maxmemory-samples` 越大越準也越耗 CPU（10 已接近真 LRU）。把它當教科書精確 LRU 會在邊角案例上對不上。
- **LFU 計數器是線性的**：Redis LFU 用對數型計數器並隨時間衰減（`lfu-log-factor`／`lfu-decay-time`），不是單純累加；不懂衰減會誤判它的行為。

### 延伸閱讀

- Redis 官方〈Key eviction〉（policies、近似 LRU、LFU 計數器）：https://redis.io/docs/latest/develop/reference/eviction/
- Redis 8.6 〈What's new〉（`volatile-lrm`／`allkeys-lrm`）：https://redis.io/docs/latest/develop/whats-new/8-6/

## 持久化（RDB vs AOF、fsync 取捨）

### 定義與原理

記憶體型儲存的資料是易失的，重啟即失憶（見領域 J）。持久化是**主動**把記憶體狀態寫到磁碟，讓崩潰／重啟後能還原。它要回答的核心取捨是：**你願意在崩潰時丟掉「最後多久」的寫入（durability window），換多大的寫入吞吐與重啟速度。** 這是一條連續光譜：fsync 越勤、丟得越少，但每次寫都等磁碟、吞吐越低。

### 解法空間

以 Redis 兩種機制為座標：

- **RDB（snapshot）**：定期把整個資料集做 point-in-time 快照（fork 子行程、寫成緊湊二進位檔）。重啟時載入單一檔案、最快；但兩次快照之間崩潰，會丟掉自上次快照以來的全部寫入。
- **AOF（Append Only File）**：把每個改寫指令追加到 log，重啟時重放還原。durability 由 fsync 策略決定：
  - `appendfsync always`：每次寫都 fsync，最安全、最慢（每寫一筆等一次磁碟）。
  - `appendfsync everysec`：每秒 fsync 一次（預設），崩潰最多丟約 1 秒寫入——延遲與安全的折衷點。
  - `appendfsync no`：交給 OS 決定何時刷盤，最快、丟失窗口不可控（可能丟掉 OS buffer 中數十秒的寫）。
  - AOF 會隨指令累積膨脹，靠 **AOF rewrite**（重寫成等效的最小指令集）壓縮。
- **混合（aof-use-rdb-preamble）**：AOF 檔以 RDB 格式做前段（快速載入基底）＋其後增量指令，兼顧重啟速度與低丟失窗口。

### 各方案的保證與取捨

| 方案/做法 | 保證（崩潰丟失窗口） | 適用場景 | 注意事項 |
|---|---|---|---|
| RDB only | 丟「上次快照→崩潰」全部寫入 | 可容忍丟幾分鐘、要快重啟／備份 | fork 在大資料集上短暫吃 CPU/記憶體（copy-on-write）；快照頻率＝丟失上限 |
| AOF `always` | 幾乎零丟失（已回應即落盤） | 不可丟任何已確認寫 | 吞吐大降；每寫等磁碟，延遲被 fsync 主導 |
| AOF `everysec`（預設） | 最多約 1 秒 | 多數場景的甜蜜點 | 「約 1 秒」非硬保證；磁碟卡頓時實際窗口更大 |
| AOF `no` | 不可控（OS 決定） | 純快取、丟失無所謂、要最高吞吐 | 等同沒怎麼保證，別用在需要 durability 的資料 |
| RDB＋AOF 混合 | ≈ AOF 的丟失窗口＋RDB 的快重啟 | 同時要低丟失與快恢復 | 設定較複雜；佔較多磁碟 |

worked example（fsync 與丟失量）：一個 Redis 以 `appendfsync everysec` 跑、承受 50,000 writes/s。崩潰時最後一次 fsync 之後、尚未落盤的寫入最壞情況約 1 秒份 ＝ **約 50,000 筆**寫入面臨丟失風險。若改 `appendfsync always`，理論丟失趨近 0，但每筆寫都要等一次 fsync——在一顆每次 fsync 約 1 ms 的磁碟上，序列 fsync 把單執行緒寫入吞吐天花板壓到約 1,000 writes/s 量級（除非批次合併多筆寫共用一次 fsync）。50,000→約 1,000 的差距，就是「零丟失」的標價。

### 何時需要

- 資料是**可重算的快取副本** → 可以乾脆關閉持久化，或只留 RDB 當暖機加速；崩潰直接從 DB 重建。
- 資料**只在 Redis 裡有真相**（如某些 session、計數）→ 至少 AOF `everysec`；不可丟的金流類別資料，要嘛 `always`＋接受吞吐代價，要嘛根本不該只放記憶體型儲存。
- 要快速備份／搬遷整份資料 → RDB 快照檔最方便。
- over-engineering 警訊：對純快取開 `appendfsync always` 是拿吞吐換一份你本來就會從 DB 重建的資料，純浪費。

### 常見誤解與陷阱

- **以為 `everysec` 保證「只丟 1 秒」**：那是正常情況的近似。若磁碟 I/O 卡住、fsync 排隊，背景 fsync 落後，實際丟失窗口會超過 1 秒。durability 是統計性的，不是硬上限。
- **以為開了 AOF 就不會丟**：fsync 之前的寫仍在 OS page cache，崩潰會丟。`always` 才接近零丟，且代價巨大。
- **把持久化當高可用**：持久化解的是「單機崩潰後能還原」，不是「崩潰期間還能服務」。後者要複製／副本（見領域 M）；磁碟壞了、單點仍會停。
- **RDB fork 的記憶體尖峰**：fork 用 copy-on-write，寫入越多的瞬間、被複製的頁越多，記憶體可能短暫接近翻倍；在記憶體吃緊的機器上做快照可能觸發 OOM。

### 延伸閱讀

- Redis 官方〈Persistence〉（RDB / AOF / 混合 / fsync 策略）：https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/
- 〈Redis persistence demystified〉(antirez)：http://oldblog.antirez.com/post/redis-persistence-demystified.html

## 多層快取與優雅降級

### 定義與原理

多層快取＝在請求路徑上**串多級快取**，每級各有不同的容量、延遲、命中率與一致性特性：典型是 client/CDN → 應用程式行程內（local，如 LRU map）→ 分散式快取（remote，如 Redis）→ DB。第一原理：**離請求越近的層越快但越小、越容易與真相分叉；越遠的層越大越一致但越慢。** 而「優雅降級」在快取脈絡下特指：**當某一層（尤其遠端快取）掛了，請求路徑要能退到下一層或退到 DB，而不是整條鏈一起倒。** 通用的 fallback／降級機制（含 circuit breaker 觸發）見領域 P，本條只談快取層自身的降級。

### 解法空間

- **分層 TTL**：近端層（local）給很短 TTL（秒級，容忍些微不一致換低延遲），遠端層（Redis）給較長 TTL，DB 為真相。
- **快取掛掉時的降級路徑**：遠端快取不可用時，退到「直接打 DB」並對 DB 套保護（限流／single-flight，見領域 E），避免快取一掛就把整批流量灌爆 DB（這本身就是雪崩的一種觸發）。
- **本地快取兜底**：遠端不可用時，短暫用行程內 local cache 撐住熱資料（可能更舊，但好過直接 503）。
- **失效傳播**：多層下，一次寫要讓**每一層**都失效——常見漏洞是更新了 DB 與 Redis、卻忘了行程內 local cache，導致那台機器持續回舊值直到 local TTL 到。可用 pub/sub 廣播失效事件通知各節點清 local（見領域 A 的 Pub/Sub 交付語意）。
- **stale-while-revalidate**：返回過期值的同時非同步刷新（HTTP 與應用層皆有此模式），用「可控的舊」換可用性。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| 分層 TTL | 近端極低延遲＋遠端較一致 | 讀密集、可容忍近端秒級舊值 | local 各節點獨立過期，同一時刻不同機器可能回不同值 |
| 快取掛→退 DB＋限流 | 遠端快取故障不致命 | 遠端快取非單點不可或缺 | 退 DB 瞬間流量暴增，必須配 DB 側保護否則換 DB 雪崩 |
| local cache 兜底 | 遠端掛時仍回（較舊的）值 | 可接受短暫更舊資料的讀 | 失效難傳播；故障期一致性更鬆 |
| pub/sub 廣播失效 | 多節點 local 同步失效 | 有行程內快取的水平部署 | pub/sub 是 at-most-once，漏訊息→某節點殘留舊值（見領域 A） |
| stale-while-revalidate | 刷新期間零等待、零 miss 風暴 | 可容忍短暫舊值的熱資料 | 過期窗口內回舊值；需背景刷新且要防刷新風暴 |

worked example（分層命中率）：請求路徑 local → Redis → DB。設 local 命中率 80%、Redis 對 local-miss 的命中率 90%、其餘打 DB。每 1,000 個請求：local 命中 800、剩 200 進 Redis、Redis 命中 180、最後 20 打 DB。**只有 2% 的請求最終觸及 DB。** 若延遲為 local 0.01 ms、Redis 0.5 ms、DB 10 ms，平均讀延遲 ≈ 0.8×0.01 + 0.18×0.5 + 0.02×10 ≈ **0.298 ms**，相較全打 DB 的 10 ms 降約 97%。但代價是：寫一次資料要失效兩層，且 local 的 80% 那批可能在各節點回到秒級舊值。

### 何時需要

- 單一遠端快取已成延遲或頻寬瓶頸、且熱資料高度集中 → 加 local 層吃掉大部分讀。
- 遠端快取的可用性會直接決定服務可用性（快取一掛服務就掛）→ 必須設計快取層降級路徑（退 DB＋DB 保護）。
- over-engineering 警訊：流量不大、單層 Redis 命中率已高（>95%）時，再加 local 層帶來的失效複雜度與跨節點不一致，往往大於它省的那點延遲。

### 常見誤解與陷阱

- **「快取掛了退 DB 就好」卻沒保護 DB**：遠端快取一掛，原本被擋住的全部讀瞬間直撲 DB——這是把快取故障升級成 DB 故障的典型路徑。退 DB 必須同時上限流／single-flight。
- **忘了 local 層的失效**：更新時只清了 Redis、漏清各節點行程內 cache，造成「部分機器一直回舊值」，且因為是少數機器、難重現難 debug。
- **層數越多越好**：每加一層就多一處要失效、多一種不一致來源、多一個故障點。層數是成本不是免費的命中率。
- **把多層快取降級當通用 fallback**：本條只解「快取層自己掛了怎麼退」；服務間呼叫的整體降級、預設值、熔斷觸發是更廣的韌性主題（見領域 P）。

### 延伸閱讀

- RFC 5861〈HTTP Cache-Control Extensions for Stale Content〉（stale-while-revalidate / stale-if-error）：https://www.rfc-editor.org/rfc/rfc5861
- Redis 官方〈Client-side caching〉（行程內快取與失效追蹤 invalidation）：https://redis.io/docs/latest/develop/reference/client-side-caching/

## Redis

### 是什麼與內部機制

Redis 是記憶體型資料結構儲存，把 string / hash / list / set / sorted set / stream / bitmap / HyperLogLog 等結構放在記憶體裡，以單一行程提供低延遲存取。最關鍵的內部事實：**指令的執行是單執行緒的**——所有指令在單一 main thread 上序列執行，因此每個指令對資料的操作天然原子、不需鎖；這也是 Redis 簡單與可預測的根源，代價是**一個慢指令（如對大集合做 `KEYS *` 或 `SORT`）會阻塞所有其他指令**。

Redis 6.0 起加入 **threaded I/O（`io-threads`）**：把網路 socket 的 response 寫回（及視設定的 read/parse）卸載到多執行緒，但**指令執行本身永遠仍在單一執行緒、永不平行**。注意預設只卸載寫回（`io-threads-do-writes`）、**讀路徑的 parse 預設不卸載**，需另設 `io-threads-do-reads yes` 才生效（官方註明讀的卸載通常幫助不大）。Redis 8 重寫了 I/O threading 實作、效能顯著提升（並以 SIMD 加速 CRC64 等）（2026-06）。**易錯 nuance：即使在 Redis 8，`io-threads` 預設仍為 1（等於關閉），需手動設為 4–8 才生效**——「Redis 8 預設開啟 I/O threading」是錯的。

持久化（RDB / AOF / fsync）見本領域「持久化」條目；驅逐策略（`maxmemory-policy`）見本領域「驅逐」條目。

授權演進（load-bearing 老化事實，2026-06）：

- **BSD-3-Clause**（至 2024-03）→ **2024-03 改雙授權 SSPLv1 / RSALv2**（皆非 OSI 開源授權，引發社群分裂）→ **2025-05 隨 Redis 8 加入 AGPLv3**，成為**三授權（tri-license）**：使用者可三選一（RSALv2、SSPLv1、AGPLv3），其中**只有 AGPLv3 是 OSI 認可的開源授權**。產品名自 8.0 起為「Redis Open Source」，RediSearch/RedisJSON 等模組併入核心同受三授權。回加 AGPLv3 與原作者 antirez 於 2024-11 回歸 Redis 公司有關。當前 Redis 已是 **8.x**（非 7.x）。
- **Valkey**：由 **Linux Foundation** 主導、2024-03（宣布 2024-03-28）自 **Redis 7.2.4** fork、採 **BSD-3-Clause** 開源授權，AWS / Google Cloud / Oracle 等支持。當前已到 9.x（2026-06）。主要 Linux distro 與雲端（如 AWS ElastiCache、Google Memorystore for Valkey）已普遍轉向 Valkey。

### 在哪些系統扮演什麼角色

Redis 的價值在於「一個元件、多重角色」，因為它的資料結構直接對映多種系統需求：

- **快取**：最主流用途，配 TTL ＋ `maxmemory-policy`（見本領域前述條目）。
- **分散式鎖**：用 `SET key val NX PX ttl` 取鎖。但 Redis 鎖**不保證分散式正確性**——Redlock 演算法與其爭議、fencing token 的必要性見領域 M；本條只說它常被當鎖底層、且單實例鎖在 failover 時可能雙重持有。
- **佇列／延遲任務**：用 List（`LPUSH`/`BRPOP`）做簡單佇列，或 Stream（`XADD`/`XREADGROUP`）做帶 consumer group 的 at-least-once 佇列；交付語意（Pub/Sub at-most-once vs Stream at-least-once）見領域 A。Redis-backed job queue（如 BullMQ）即建於此。
- **Pub/Sub**：`PUBLISH`/`SUBSCRIBE` 做即時廣播，fire-and-forget、at-most-once（離線訂閱者永久錯過）——常用於多節點快取失效廣播、WebSocket backplane（見領域 C）。
- **排行榜 leaderboard**：Sorted Set（`ZADD`/`ZRANGE`/`ZRANK`）以分數排序，天然支援 top-N 與名次查詢。
- **限流 rate limiting**：用計數器＋TTL，或更精確的滑動視窗／token bucket（常以 Lua script 保證多步原子）；限流機制本身見領域 E，本條只說 Redis 因單執行緒原子性適合做計數底層。

### 保證與限制

- **保證**：單執行緒序列執行 → 單指令原子；多步原子可用 `MULTI/EXEC`（transaction，非回滾型）或 Lua script（單執行緒內整段原子執行）。`WAIT` 可要求寫已複製到 N 個副本後才回（但仍非強一致同步複製）。
- **限制**：
  - **複製是非同步的**：master 回應 client 後才異步推給 replica，master 崩潰時未複製的寫會丟（見領域 M 的複製延遲）。
  - **單執行緒 = 單慢指令全堵**：一個 O(N) 大指令會卡住整個實例。
  - **記憶體上限即容量上限**：資料超過 `maxmemory` 就驅逐或拒寫；它不是無限磁碟儲存。
  - **持久化是 best-effort**：`everysec` 仍可能丟約 1 秒（見「持久化」條目）。

worked example（單執行緒延遲放大）：Redis 單執行緒每秒能處理數十萬個 O(1) 小指令（如 `GET`/`SET`，單指令微秒級）。但若有一個請求對一個 100 萬元素的 set 跑 `SMEMBERS`（O(N)、假設耗時 50 ms），在這 50 ms 內**所有**其他指令排隊等待——對一個本來 p99 < 1 ms 的實例，這一個慢指令會把同窗口內所有請求的尾延遲推到 50 ms 以上。這就是「禁用 `KEYS *`／大範圍 O(N) 指令於生產」的根本原因，不是慣例而是單執行緒模型的直接後果。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Redis（Redis Ltd.） | 全功能、模組生態、單執行緒原子 | 要最新功能與商業支援 | 8.x 為三授權，純開源只有 AGPLv3 那條；商用以服務形式提供須留意 SSPL/RSAL |
| Valkey | 語意與 Redis 7.2.4 相容、BSD 開源 | 要無爭議開源授權、避雲鎖定 | 與 Redis 8+ 新功能逐漸分流，非永遠對等 |
| Memcached | 純 KV 快取、多執行緒、極簡 | 只要最單純的 KV 快取、想吃多核 | 無豐富資料結構、無持久化、無複製；功能少即優勢也是限制 |
| 嵌入式 local cache（如行程內 LRU） | 零網路延遲 | 單機熱資料兜底 | 不跨節點共享、失效難傳播；屬「多層快取」的 local 層 |

授權正是當前選 Redis vs Valkey 的核心取捨：要無爭議的 OSI 開源、避免商用服務化的授權義務 → Valkey（BSD）；要 Redis 8+ 最新功能與生態 → Redis（接受三授權，純開源走 AGPLv3）。

### 常見誤解與陷阱

- **「Redis 是單執行緒所以慢／吃不滿多核」**：單執行緒指的是**指令執行**；網路 I/O 自 6.0 起可多執行緒。單實例吃不滿多核是真的，但解法是多實例／cluster 分片，不是把執行多執行緒化（那會破壞原子性前提）。
- **「Redis 8 預設開了 io-threads」**：錯，預設仍是 1（關閉），須手動設。
- **「Redis 是 BSD／還在 7.x」**：過時（2026-06）。2024 起已改授權、現為 8.x 三授權；純 BSD 開源那條已由 Valkey 接手。
- **把 Redis 當主資料庫**：它的複製非同步、持久化 best-effort、容量受記憶體限——可當真相來源但要清楚 durability 與一致性的代價，金流類資料通常仍以持久化 DB 為真相、Redis 為快取。
- **`MULTI/EXEC` 當成可回滾交易**：Redis transaction 不回滾，`EXEC` 中某指令執行期錯誤不會撤銷前面已執行的指令；它保證的是「中間不被別的 client 插隊」，不是 ACID 的原子回滾。
- **用單實例 Redis 鎖當分散式互斥的正確性保證**：failover／網路分區下可能兩個 client 同時持鎖，正確性需 fencing token（見領域 M）。

### 延伸閱讀

- Redis 官方文件（資料結構、persistence、eviction、client-side caching）：https://redis.io/docs/latest/
- Redis 8 GA 公告（I/O threading 重寫、效能）：https://redis.io/blog/redis-8-ga/
- Redis 授權頁（RSALv2 / SSPLv1 / AGPLv3 三授權）：https://redis.io/legal/licenses/
- Valkey 專案（Linux Foundation、BSD fork）：https://valkey.io/

## S3 / 物件儲存

### 是什麼與內部機制

S3（Amazon Simple Storage Service）是物件儲存：資料以**不可變的物件**（object＝bytes ＋ metadata ＋ key）存在扁平的 bucket 命名空間裡，透過 HTTP API（`PUT`/`GET`/`DELETE`/multipart upload）存取，**沒有檔案系統的目錄樹、沒有部分就地更新**——改一個物件＝整個重寫（覆蓋）。它不是掛載的磁碟，是經網路的 HTTP 端點，因此延遲是毫秒到數十毫秒級（非記憶體／本地磁碟的微秒級），但容量近乎無限、單位儲存成本極低。

內部機制的核心是**冗餘換耐久**：物件被切片、加上 erasure coding，**跨單一 region 內至少 3 個可用區（AZ）冗餘存放**，設計耐久度達 **99.999999999%（11 個 9）**（2026-06）——直觀上，存 1,000 萬個物件平均約每一萬年才預期丟一個。一致性上，S3 現提供**強讀後寫一致性（strong read-after-write consistency）**：`PUT` 成功後立即 `GET` 必讀到新版本（早年的最終一致性已不再是限制）。

大小：單一物件最大 **50 TB**（2025-12 由 5 TB 上調，2026-06）；單次 `PUT` 上限 **5 GB**，更大要用 **multipart upload**（每片 5 MB–5 GB，可平行上傳、斷點續傳，物件範圍 5 MB–50 TB）。

### 在哪些系統扮演什麼角色

- **大 payload offload（與訊息系統交接）**：訊息佇列有單則大小上限（如 SQS 單則 1 MiB，見領域 A），超過就把實際 payload 放 S3、訊息只帶一個 S3 物件鍵（claim-check 模式）。消費端拿到鍵再去 S3 取大物件——用一次額外往返換掉訊息系統的大小限制。
- **服務間資料交接**：批次產物、報表、匯出檔、備份（如 RDB 快照）丟 S3，下游服務或排程任務按鍵取用，把「傳大檔」從同步請求路徑卸到物件儲存。
- **靜態資源與媒體**：圖片、影片、前端打包產物存 S3、常配 CDN 邊緣快取。
- **資料湖／log 落地（與本書邊界）**：log 採集（如 Fluent Bit `out_s3`）與資料湖把 S3 當底層儲存層；資料湖／倉本身的查詢與建模在本書範圍外。

### 保證與限制

- **保證**：11 個 9 耐久度（跨 ≥3 AZ）；強讀後寫一致性；物件不可變（版本化可保留歷史版本）；近乎無限容量。
- **限制**：
  - **延遲是網路 HTTP 級**：首位元組延遲毫秒到數十毫秒，不適合每請求高頻小讀寫（那是快取／DB 的活）。
  - **無部分更新**：改一個 byte 也得重寫整個物件；不能像檔案系統 seek-and-write。
  - **無交易、無跨物件原子**：每個物件操作各自獨立，沒有「同時原子更新兩個物件」。
  - **list 操作較貴且非即時排序**：大量物件下 `LIST` 是分頁掃描，別當資料庫查詢用。
  - **可用性 ≠ 耐久度**：11 個 9 是**耐久度**（資料不丟），可用度 SLA（能不能取到）是另一個較低的數字；耐久不等於永遠可讀。

worked example（claim-check 省成本）：一個圖片處理管線每天傳 100 萬則任務訊息，每則平均帶一張 3 MB 原圖。若把原圖塞進訊息（超過 SQS 1 MiB 上限根本不行，假設用支援大訊息的系統），佇列要扛 100 萬 × 3 MB ＝ **約 3 TB/日**的訊息流量，且 broker 記憶體／儲存壓力巨大。改 claim-check：原圖 `PUT` 到 S3（3 TB/日 落在便宜的物件儲存），訊息只帶約 100 bytes 的 S3 鍵 ＋ metadata ＝ 佇列流量降到 100 萬 × 約 100 bytes ＝ **約 100 MB/日**，降約 3 萬倍。代價是消費端每則多一次 S3 `GET`（約 20–50 ms）與最終一致的清理責任（任務失敗的 S3 物件要有 lifecycle 規則回收）。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| S3 / 物件儲存 | 11 個 9 耐久、近乎無限、強讀後寫一致 | 大檔、不可變物件、備份、offload | HTTP 級延遲；無部分更新／跨物件原子 |
| 區塊儲存（如 EBS） | 低延遲、可掛載、可隨機寫 | 需檔案系統語意、資料庫底層磁碟 | 單機掛載、容量有上限、隨 AZ／實例綁定 |
| 網路檔案系統（如 EFS/NFS） | POSIX 檔案語意、多機共享 | 多機共享檔案、需目錄樹 | 比物件儲存貴、延遲較高、擴展性不如 S3 |
| Redis / 記憶體快取 | 微秒級延遲 | 熱小資料、需極低延遲 | 容量受記憶體限、易失、貴；非大檔倉庫 |

選擇準則：要存的是**大的、不常改的、要極高耐久的整塊資料** → S3；要**隨機就地更新、低延遲、檔案系統語意** → 區塊／檔案儲存；要**極低延遲的熱小資料** → 快取。把 S3 當高頻小 KV 讀寫用會被延遲與每請求成本懲罰。

### 常見誤解與陷阱

- **把 S3 當檔案系統**：它沒有目錄、沒有就地部分更新、`LIST` 不是廉價排序查詢。`a/b/c.txt` 裡的 `/` 只是鍵字串的一部分，不是真目錄。
- **以為 11 個 9 = 永遠讀得到**：那是耐久度（資料極不可能丟），不等於可用度；region/AZ 事件期間仍可能短暫取不到。耐久 ≠ 可用。
- **忽略最終一致以外的非原子性**：S3 物件讀後寫已是強一致，但「同時原子更新兩個物件」不存在；需要跨物件一致要在應用層自己處理。
- **claim-check 漏清理**：把大 payload offload 到 S3 後，失敗或過期的物件若沒有 lifecycle 規則回收，會無聲累積成可觀成本。
- **小檔海量塞 S3**：每個 `PUT`/`GET` 都是一次計費請求，幾百萬個微小物件的請求費與 list 成本可能遠超預期；海量小資料更適合打包或放 KV/DB。

### 延伸閱讀

- Amazon S3 FAQs（物件大小、耐久度、一致性）：https://aws.amazon.com/s3/faqs/
- AWS 文件〈Multipart upload limits〉（5 MB–5 GB 分片、5 GB 單 PUT 上限）：https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html
- AWS what's-new〈Amazon S3 increases the maximum object size to 50 TB〉（2025-12）：https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/
