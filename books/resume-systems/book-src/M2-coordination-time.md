# M · 協調、雜湊與時間

本領域處理分散式系統裡「沒有單一全域真相、節點之間要協調卻又彼此不完全信任」的問題：誰能獨佔資源（分散式鎖）、事件之間誰先誰後（邏輯時鐘與排序）、資料該落在哪個節點且擴縮時搬動最少（consistent hashing）、狀態怎麼在沒有中央協調者的情況下趨同（gossip / anti-entropy），以及最被低估的一類坑——把實體世界的「時間與日期」對應進系統的應用層陷阱。共識、leader election、quorum、複製策略等核心機制在領域 M 的另一檔深講，本檔聚焦「協調原語、資料放置與時間」這一面。本檔的 consistent hashing 與時鐘是本書的 owning 條目：分片在領域 B 只談一致性後果，排程觸發語意在領域 J 只談漏跑/補跑。

## 分散式鎖（Redlock / fencing token）

### 定義與原理

分散式鎖要回答的問題是：在多台機器、多個行程同時想做同一件「同一時間只能有一個人做」的事（扣同一筆庫存、跑同一個批次、寫同一個檔案）時，怎麼保證互斥（mutual exclusion）。單機上互斥靠作業系統的 mutex；跨機器沒有共享記憶體，只能靠一個外部協調者（Redis、ZooKeeper、etcd、資料庫）發放「鎖」這個共識性的記號。

分散式鎖的第一原理麻煩在於：**鎖的擁有權是有時效的，而持有者隨時可能「失聯但沒死」**。為了避免持有者崩潰後鎖永遠卡住，鎖一定帶 TTL（lease，租約）。但 TTL 一旦存在，就出現一個無法靠鎖本身消除的裂縫：行程 A 拿到鎖、TTL 30 秒，A 在第 5 秒進入一個 40 秒的 GC stop-the-world 暫停（或被 OS 換出、或網路黑洞）。鎖在第 30 秒過期，協調者把鎖發給 B；A 在第 45 秒醒來，**它不知道自己已經失去鎖**，仍然以為持有鎖去寫資料——此刻 A 和 B 同時在臨界區。這不是 bug，是「靠時間判定存活」的根本限制（見領域 J 的失敗偵測：逾時是唯一手段，無法區分「慢」與「死」）。

### 解法空間

- **單實例 Redis 鎖（`SET key val NX PX ttl`）**：原子地「不存在才設、帶過期」，`val` 用唯一隨機值，解鎖用 Lua 腳本比對 `val` 再刪（避免刪到別人的鎖）。簡單、快，但單點，且有上述 TTL 裂縫。
- **Redlock（多 Redis 實例多數決）**：向 N 個獨立 Redis（典型 5 個）依序請求鎖，在多數（≥⌊N/2⌋+1，即 3 個）成功且總耗時遠小於 TTL 時才算拿到。設計目的是消除單點。
- **共識系統發鎖（ZooKeeper / etcd）**：用順序節點（ephemeral sequential znode）或 lease + 線性化 KV。持有者 session 斷線，協調者主動讓鎖過期；znode 的版本號或 etcd 的 revision 天然單調遞增，可直接當 fencing token。
- **fencing token（柵欄記號）**：不論用哪種鎖，每次發鎖附帶一個**單調遞增的整數**。受保護的資源（資料庫、儲存）在每次寫入時檢查 token，**拒絕比已見過的最大 token 還小的寫入**。這把「正確性」從「鎖服務 + 時鐘」轉移到「資源端的版本檢查」，是唯一能堵住 TTL 裂縫的辦法。
- **完全不用分散式鎖**：把臨界操作改成資源端的條件寫入（CAS / 樂觀並發，見領域 B），或用單一分區序列化（同一 key 永遠路由到同一 consumer，見訊息順序，領域 A）。很多「需要分散式鎖」的需求其實是這兩者能更便宜解掉。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 單實例 Redis `SET NX PX` | 高效能、近似互斥（efficiency lock） | 偶爾重複做也只是浪費、不會錯（去重器、避免重複寄信） | 單點故障；TTL 裂縫仍在；不提供 fencing token |
| Redlock（多數決） | 容忍少數 Redis 掛掉 | 想去單點但仍是 efficiency 用途 | Martin Kleppmann 2016 指出：仍假設有界的網路延遲、行程暫停與時鐘誤差，三者皆可能被現實打破，且**不產生 fencing token**；不適合「正確性依賴鎖」 |
| ZooKeeper / etcd lease | 線性化、session 斷即釋放、內建單調版本號 | 正確性關鍵（leader 唯一性、單一寫入者） | 比 Redis 重、延遲高；仍需把版本號當 fencing token 帶到資源端才完整 |
| fencing token（疊加在任一鎖上） | 把互斥落實到資源端，堵住 TTL 裂縫 | 任何「兩個持有者同時寫會出錯」的場景 | 資源端必須能拒絕舊 token（要可改寫、有條件寫入能力）；只發 token 而資源不檢查＝沒用 |

關鍵分界是 Kleppmann 的「efficiency vs correctness」：若鎖只是**最佳化**（避免重複工作，偶爾兩個人同時做不會壞資料），單實例 Redis 鎖足夠；若鎖關係到**正確性**（同時兩個寫入者就會損壞資料），就**必須**有 fencing token，且光有鎖服務不夠——資源端要驗 token。

### 何時需要

需要分散式鎖的真實場景比直覺少。先問三題：(1) 臨界資源能不能自己做條件寫入？能就用 CAS / 樂觀並發（領域 B），不需要鎖。(2) 能不能把同一實體的操作路由到單一節點/單一 partition 序列化？能就用分區（領域 A），天然互斥。(3) 偶爾重複執行會不會壞？不會壞就用便宜的 efficiency lock，會壞就上 fencing token。只有在「資源無法條件寫入、又無法分區、且重複會損壞」三者皆中時，才真正需要帶 fencing token 的強分散式鎖。把分散式鎖當成第一選擇，通常是 over-engineering，且引入一個新的可用性瓶頸。

### 常見誤解與陷阱

- **以為拿到鎖就安全**：TTL 裂縫讓「持有鎖」永遠只是「直到某個時間點之前大概持有」。沒有 fencing token，再貴的鎖服務都救不了 GC 暫停 + 過期續發。
- **Redlock 的時鐘假設**：Redlock 的多數決安全性依賴各節點的時鐘以接近的速率前進；若某節點時鐘跳變（NTP 校正、VM 遷移），鎖可能提早過期或重複發放。
- **TTL 設太短**：為了快速釋放把 TTL 設成幾秒，結果正常 GC 或慢查詢就讓鎖過期，臨界區內的人變成「無照駕駛」。TTL 要大於臨界操作的合理最壞耗時，但越大、崩潰後卡死越久——這是個取捨，不是有最佳值。
- **解鎖刪到別人的鎖**：A 過期、B 拿到，A 醒來直接 `DEL key` 把 B 的鎖刪了。解鎖必須「比對自己的唯一值再刪」（Lua 原子腳本），不能無條件刪。
- **冪等定義不在這裡重講**：分散式鎖常被誤當成「保證只執行一次」的手段，但鎖會過期、會重複發；真正的「重複也不出錯」要靠冪等（見冪等，領域 A），鎖只降低重複機率、不消除。

### 延伸閱讀

- Martin Kleppmann, "How to do distributed locking"（Redlock 批評與 fencing token 的經典論述）：https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html
- Redis 官方分散式鎖文件（Redlock 演算法描述）：https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/
- ZooKeeper Recipes — Locks（順序節點實作鎖）：https://zookeeper.apache.org/doc/current/recipes.html#sc_recipes_Locks

## 邏輯時鐘與排序（Lamport / vector / HLC / TrueTime）

### 定義與原理

分散式系統裡沒有可信的全域時間：每台機器的牆鐘（wall clock）各走各的，NTP 校正會讓時鐘**往回跳**，跨機房的時鐘誤差可達數十毫秒。所以你**不能用 `timestamp` 比大小來判斷兩個事件的先後**——這是分散式系統最常見的隱性 bug 來源。

Leslie Lamport 在 1978 年的論文〈Time, Clocks, and the Ordering of Events in a Distributed System〉（CACM 21(7):558–565，2000 年獲 Dijkstra 獎）給出第一原理：我們真正需要的不是「絕對時間」，而是**因果順序**（causality）——事件 a「happens-before」事件 b（記作 a → b），當且僅當：a、b 在同一行程且 a 在前；或 a 是送訊息、b 是收該訊息；或有傳遞鏈 a → c → b。沒有 happens-before 關係的兩事件是**並行的**（concurrent），它們之間沒有客觀的先後，硬要排序只能靠人為規則打破平手。邏輯時鐘就是用計數器來捕捉這個偏序，而非依賴會騙人的牆鐘。

### 解法空間

- **Lamport timestamp（純量邏輯時鐘）**：每個行程一個整數計數器 C。本地事件 C++；送訊息附帶 C；收訊息時 `C = max(C_local, C_msg) + 1`。保證：若 a → b 則 `C(a) < C(b)`。但**反向不成立**——`C(a) < C(b)` 不代表 a → b，可能只是並行。配上行程 ID 當 tie-breaker 可得全序（total order），但這個全序是任意的，不反映真實因果。
- **vector clock（向量時鐘）**：每個行程維護一個長度 = 節點數的向量 V，只增自己那格，收訊息時逐格取 max。保證：`V(a) < V(b) ⇔ a → b`，且能**偵測並行**（兩向量互不 ≤ 即並行）——這是 Lamport 純量做不到的。代價：向量大小隨節點數線性成長，跨服務傳遞成本高。
- **version vector（版本向量）**：vector clock 用在資料副本上的變體，每個副本一格，用來偵測寫入衝突（見衝突解決，領域 L）。
- **Hybrid Logical Clock（HLC）**：Kulkarni、Demirbas 等於 OPODIS 2014 論文〈Logical Physical Clocks〉提出。把牆鐘（physical time）與一個邏輯計數器組成 tuple `(pt, c)`，取本地實體鐘、收到的 HLC、本地 HLC 三者最大值，只有當實體時間沒前進時才 bump 計數器。保證：單調遞增、捕捉因果、又貼近真實時間（誤差不超過 NTP 偏移上界），且塞得進 64 位元欄位。CockroachDB、MongoDB cluster time、YugabyteDB 用它排序交易。
- **TrueTime（Google Spanner）**：不假裝時鐘準，而是把時鐘的**不確定性**顯式表示成一個區間 `[earliest, latest]`，半寬 ε（epsilon）在 Google 機房靠 GPS + 原子鐘維持，典型 ε 約數毫秒（常引用 < 4ms）。寫入交易做 **commit-wait**：等 2ε 過後才提交，確保任何後續交易的時間區間一定在它之後，由此得到外部一致性（external consistency）。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Lamport timestamp | a→b ⇒ C(a)<C(b)；加 ID 得全序 | 只需「一致的全序」、不需偵測並行（如全序廣播） | 反向不成立；無法判斷兩事件是否並行；全序是任意的、不反映因果 |
| vector clock | V(a)<V(b) ⇔ a→b；可偵測並行 | 需要知道「誰因果在前、誰是衝突」（衝突偵測、因果一致） | 大小隨節點數線性成長；節點動態增減時 GC 舊條目麻煩 |
| HLC `(pt, c)` | 單調、捕捉因果、貼近牆鐘、64-bit | 分散式資料庫排序交易、做一致性快照、無原子鐘可用時 | 仍受 NTP 偏移上界約束；不是真實時間、不能當絕對 timestamp 對外承諾 |
| TrueTime（commit-wait） | 外部一致性（線性化 + 反映真實時間先後） | 全球跨區、需要外部一致性的強交易系統 | 需要 GPS + 原子鐘硬體；每筆寫入付 2ε（約 8ms）commit-wait 延遲；非自架可得 |

**Worked example（commit-wait 成本）**：Spanner 在 ε ≈ 4ms 時，每筆寫入交易要 commit-wait 約 2ε = 8ms 才提交。若一條請求鏈含 3 筆序列寫入，光 commit-wait 就疊加約 24ms——這是「外部一致性」換來的、無法消除的延遲底價。對照 HLC：不付這個 wait，但放棄了「timestamp 嚴格反映真實世界先後」的保證，只保證單調與因果。**這就是脊椎：你想要的保證越強（外部一致性），付的取捨越具體（每寫一次都等 2ε）。**

### 何時需要

- **只要排序、不跨機器比時間**：用 Lamport 或直接讓單一節點/單一 partition 序列化（領域 A 的順序）就夠，別上向量時鐘。
- **要偵測寫入衝突 / 因果一致**：用 vector / version vector（衝突解決見領域 L）。
- **分散式資料庫要單調且貼近真實時間的排序、又不想要原子鐘**：HLC 是現代主流答案。
- **需要外部一致性（read 一定看到所有先於它真實完成的 write）且願意付硬體與延遲**：才需要 TrueTime 等級。絕大多數應用**不需要**——把「事件用牆鐘排序」改成「用單調鐘量間隔、用邏輯時鐘排因果」就解決九成問題。

### 常見誤解與陷阱

- **用 `Date.now()` / `System.currentTimeMillis()` 比兩個跨機器事件的先後**：牆鐘會被 NTP 往回校、跨機器有偏差，這個比較隨時會給出錯誤的因果。量「經過多久」要用單調鐘（monotonic clock，見時間與日期處理），判因果要用邏輯時鐘。
- **以為 Lamport `C(a) < C(b)` 代表 a 因果在 b 前**：只有 a → b ⇒ C(a) < C(b)，反向不成立。要區分「並行」必須用向量時鐘。
- **把 HLC 的 timestamp 當成可對外承諾的精確時間**：HLC 的計數器部分讓它可能略超前真實牆鐘，它是排序工具不是計時工具。
- **以為自己「需要 Spanner 等級」**：commit-wait 的延遲與原子鐘的硬體門檻很高；多數系統用最終一致 + 因果排序就夠（見一致性光譜，領域 B）。

### 延伸閱讀

- Leslie Lamport, "Time, Clocks, and the Ordering of Events in a Distributed System"（CACM 1978，邏輯時鐘原典）：https://lamport.azurewebsites.net/pubs/time-clocks.pdf
- Kulkarni, Demirbas, et al., "Logical Physical Clocks and Consistent Snapshots in Globally Distributed Databases"（HLC，OPODIS 2014）：https://cse.buffalo.edu/tech-reports/2014-04.pdf
- Corbett et al., "Spanner: Google's Globally-Distributed Database"（TrueTime，OSDI 2012）：https://research.google.com/archive/spanner-osdi2012.pdf

## consistent hashing

### 定義與原理

問題：你有一份資料（或請求）想分散到 N 個節點上，最自然的做法是 `node = hash(key) % N`。它的致命缺陷是**N 一變，幾乎全部 key 都要重新映射**。從 4 台加到 5 台，`% 4` 變 `% 5`，平均約 80% 的 key 落到不同節點——對快取叢集就是瞬間 cache miss 風暴，對有狀態儲存就是幾乎全部資料都要搬遷。

Consistent hashing（David Karger 等，1997 年 STOC 論文〈Consistent Hashing and Random Trees: Distributed Caching Protocols for Relieving Hot Spots on the World Wide Web〉，原為 web 快取設計）的核心洞見：把節點和 key **都雜湊到同一個環狀空間**（hash ring，例如 0 到 2³²−1 首尾相接）。一個 key 順時針找到的第一個節點就是它的歸屬。這樣**加減一個節點，只影響環上相鄰的一段 key**，期望搬動量是 K/N（K 為 key 總數），而非全部。這是本書 owning 條目；領域 B 的分片只談分片後的一致性後果與 DB 操作面。

### 解法空間

- **基本環（每節點一個點）**：節點少時環上分佈不均，某節點可能負責一大段、負載傾斜（hot spot）。
- **virtual node（vnode，虛擬節點）**：每個實體節點在環上放 V 個點（如 V=100~200），用「節點 ID + 序號」雜湊。實體節點負責的是分散在環上的許多小段，分佈更均勻、且加減節點時負載均攤到所有節點而非單一鄰居。Dynamo、Cassandra、memcached client、Riak 都用 vnode。
- **rendezvous hashing（HRW，highest random weight）**：對每個 (key, node) 算 `hash(key, node)`，取最大值的 node。免維護環、加減節點同樣只搬一小部分，且不需 vnode 就分佈均勻；代價是查一個 key 要對所有節點算雜湊（O(N)），節點極多時較慢。
- **jump consistent hash（Google）**：一個無需儲存、O(ln N) 時間把 key 映到 `[0, N)` 桶的演算法，記憶體極省、分佈均勻；但桶只能從尾端增減（不能任意移除中間節點），適合節點編號連續、只在尾部擴縮的場景。
- **bounded-load consistent hashing**：在環的基礎上加「單節點負載上限」，超載就順延到下一個節點，避免熱 key 把單一節點打爆。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| `hash(key) % N` | 分佈均勻、O(1) | N 永遠不變的固定分區 | N 一變幾乎全部 key 重映射，禁用於會擴縮的叢集 |
| 基本環（無 vnode） | 加減節點只搬 K/N | 教學/原型 | 節點少時負載傾斜嚴重；移除節點時負載全壓到單一鄰居 |
| 環 + vnode | 均勻 + 加減節點負載均攤 | 快取叢集、Dynamo 式 KV、分片路由 | vnode 數要夠（數百）才均勻；過多會吃記憶體與 metadata |
| rendezvous (HRW) | 均勻、免維護環狀態 | 節點數中等、要避免 vnode 複雜度 | 查 key 為 O(N)，節點極多時慢 |
| jump consistent hash | 極省記憶體、O(ln N) | 桶只在尾端增減（如固定編號的 shard） | 不能任意移除中間節點 |

**Worked example（搬動量對照）**：1,000 萬個 key、4 個節點。用 `% N` 從 4 加到 5：約 1,000萬 × (1 − 1/5) = 約 **800 萬** key 改變歸屬（80%）。用 consistent hashing 從 4 加到 5：理論只搬約 K/N_new = 1,000萬 / 5 = **約 200 萬** key（20%，新節點從各舊節點各接一小段）。差距 4 倍，對快取就是 miss 率從 80% 降到 20%。

### 何時需要

當節點集合**會動態變化**（自動擴縮、節點故障替換、滾動部署）且資料/連線有狀態綁定（快取、sticky 路由、有狀態分片）時，需要 consistent hashing 把擴縮的搬動成本壓到最小。若節點數固定不變、或無狀態（任一節點都能處理任一請求，靠 L4/L7 LB 輪詢即可，見負載均衡，領域 N），就**不需要**——直接 round-robin 或 `% N` 更簡單。把 consistent hashing 用在無狀態服務上是徒增複雜度。

### 常見誤解與陷阱

- **以為環自動均勻**：沒有 vnode，節點少時環上分佈很傾斜，一個節點可能扛 40% 流量。均勻來自 vnode（或 rendezvous），不是環本身。
- **熱 key 問題不被環解決**：consistent hashing 均勻分佈的是 **key 空間**，不是 **流量**。若單一 key 超熱（某爆紅商品），它永遠落在同一節點，環救不了——要靠 key 拆分/複製或 bounded-load 變體。
- **移除節點時的負載突刺**：基本環移掉一個節點，它那段全部順延到單一鄰居，可能把鄰居壓垮。vnode 把這份負載打散到多個節點才平滑。
- **vnode 數量被當無關緊要**：太少（如每節點 1~10 個）仍傾斜；要數百個才接近均勻——但要平衡 metadata 與記憶體開銷。

### 延伸閱讀

- Karger et al., "Consistent Hashing and Random Trees..."（STOC 1997，consistent hashing 原典）：https://www.akamai.com/site/en/documents/research-paper/consistent-hashing-and-random-trees-distributed-caching-protocols-for-relieving-hot-spots-on-the-world-wide-web-technical-publication.pdf
- Thaler & Ravishankar, "Using Name-Based Mappings to Increase Hit Rates"（rendezvous/HRW hashing）：https://www.eecs.umich.edu/techreports/cse/96/CSE-TR-316-96.pdf
- Lamping & Veach, "A Fast, Minimal Memory, Consistent Hash Algorithm"（jump consistent hash）：https://arxiv.org/abs/1406.2294

## gossip / anti-entropy

### 定義與原理

問題：在一個沒有中央協調者、節點數可能成百上千、且節點會隨時加入/離開/故障的叢集裡，怎麼讓「成員清單」「故障狀態」「設定」「資料副本」這類資訊**最終傳遍每個節點並趨同**，而不靠一個會成為瓶頸與單點的中央伺服器？

Gossip（流言/八卦協定，又稱 epidemic protocol，疫情式協定）借用流行病傳播的數學：每個節點**週期性地隨機挑幾個對等節點交換資訊**，被感染（收到新資訊）的節點再去感染別人。Alan Demers 等 1987 年 PODC 論文〈Epidemic Algorithms for Replicated Database Maintenance〉是奠基之作，提出兩大機制：**anti-entropy**（反熵——隨機配對、比對並調和兩邊的完整狀態差異，把副本間的「熵」降下來）與 **rumor mongering**（謠言傳播——只散播「最近的更新」，傳夠多次沒人沒聽過就停）。核心保證是**機率性最終一致**：資訊以 O(log N) 個回合傳遍全網，且容忍訊息遺失與節點故障（沒有單點）。

### 解法空間

- **anti-entropy（背景對帳）**：節點隨機選對端，比對全部（或一段）狀態的摘要（如 Merkle tree 根雜湊），只傳差異把兩邊調和一致。pull（我問你有什麼新的）比 push 收斂快。代價：要掃整份狀態、頻寬與 CPU 開銷較大，通常低頻跑。對應領域 L 的 reconciliation 對帳，是把漂移最終修平的底層機制。
- **rumor mongering / dissemination（前景擴散）**：只傳「熱」更新（rumor），每次隨機轉發給 k 個節點，當遇到「已知道」的節點達一定次數就把該 rumor 標為冷、停止傳。快、省頻寬，但有極小機率某些節點漏掉（所以通常搭配 anti-entropy 兜底）。
- **failure detection（SWIM 式）**：Das、Gupta、Motivala 2002 年的 SWIM 協定用 gossip 散播成員與故障狀態：節點隨機 ping 對端、ping 不到就請其他節點代 ping（間接探測，避免單一網路抖動誤判），疑似失效標 suspect、確認後標 dead 並 gossip 出去。把「成員管理」與「故障偵測」都做成 gossip。
- **push / pull / push-pull**：push 在感染初期快、後期慢（多數人已知）；pull 後期快；push-pull 結合兩者，收斂最快，是多數實作的選擇。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| anti-entropy（全狀態調和） | 一定收斂、修補任何漂移 | 背景對帳、資料副本最終一致 | 掃整份狀態，開銷大，需低頻跑；常配 Merkle tree 降比對成本 |
| rumor mongering（只傳熱更新） | 快、省頻寬、O(log N) 回合 | 即時擴散成員/設定變更 | 有極小機率漏節點，需 anti-entropy 兜底 |
| SWIM 故障偵測 | 成員與故障狀態 gossip 散播、間接探測防誤判 | 大規模叢集的成員管理（Consul、Serf 用之） | 偵測延遲 vs 誤判率要調參；網路分割時可能誤標大量節點 dead |
| 中央協調者（對照） | 強一致、即時 | 小叢集、需要即時強成員視圖 | 單點、瓶頸；節點數大時不可行——這正是 gossip 存在的理由 |

**Worked example（收斂回合數）**：1,000 個節點的叢集，gossip 每回合每節點隨機聯絡幾個對端。資訊傳遍全網所需回合數約與 log₂(N) 成正比：log₂(1000) ≈ **10 回合**。若每回合間隔 1 秒，一條成員變更約 10 秒內擴散到全部 1,000 節點——且過程中容忍部分節點當機與封包遺失，沒有任何中央節點參與。對照中央協調者：要嘛 1,000 個節點同時連它（連線數爆炸），要嘛它一掛全叢集失明。

### 何時需要

當叢集**夠大（數十到數千節點）**、需要**去中心化的成員管理/故障偵測/最終一致狀態傳播**、且能接受**秒級而非即時的收斂延遲**時，gossip 是標準答案（Cassandra、Consul、Serf、Dynamo 式系統都用）。若叢集很小（個位數節點）或需要**即時、強一致的成員視圖**（如需要精確的 leader 唯一性判定），用共識系統（領域 M 的另一檔）或中央協調者更直接——gossip 的機率性與收斂延遲此時反而是負擔。

### 常見誤解與陷阱

- **以為 gossip 是即時的**：它是**最終**一致，收斂要數個回合（秒級）。任何依賴「立刻全網一致」的邏輯不能建在 gossip 上。
- **把 gossip 當強一致成員視圖**：網路分割時，兩側可能各自 gossip 出不同的「誰活著」，這正是它換來可用性的代價。要強一致成員（fencing、leader 唯一性）得靠共識。
- **只用 rumor mongering 不配 anti-entropy**：謠言傳播有極小漏網機率，長期會累積漂移；必須有低頻 anti-entropy 把漂移最終修平（這是 Demers 論文的核心論點之一）。
- **故障偵測誤判**：SWIM 式偵測在網路抖動下可能把活著的節點標 dead，間接探測（請第三方代 ping）就是為降低這種誤判而設；偵測門檻調太敏感會在尖峰流量時誤殺一片節點。

### 延伸閱讀

- Demers et al., "Epidemic Algorithms for Replicated Database Maintenance"（PODC 1987，anti-entropy 原典）：https://dl.acm.org/doi/10.1145/41840.41841
- Das, Gupta, Motivala, "SWIM: Scalable Weakly-consistent Infection-style Process Group Membership Protocol"（2002）：https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf
- DeCandia et al., "Dynamo: Amazon's Highly Available Key-value Store"（SOSP 2007，gossip 用於成員/故障）：https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf

## 時間與日期處理（UTC / epoch / timezone / DST 的應用層坑）

### 定義與原理

這是最被資深工程師低估、卻最常在生產踩雷的一類問題：把「時間」這個實體世界概念正確地對應進系統。三個必須分清的概念：

- **瞬間（instant）vs 民用時間（civil / wall time）**：「現在這個物理瞬間」是絕對的、全球唯一的；「2026-06-21 14:00」這種民用時間是相對於某個 timezone 才有意義的。把兩者混為一談是萬惡之源。
- **UTC vs epoch**：UTC 是協調世界時（含閏秒概念的民用標準）；**Unix epoch time** 是「自 1970-01-01T00:00:00Z 起經過的秒數」，且**刻意忽略閏秒**（每天固定當 86,400 秒），所以 epoch 不是嚴格的物理流逝秒數，但它單調、無時區、是儲存與傳輸瞬間的事實標準。
- **timezone ≠ 固定偏移**：timezone（如 `America/New_York`）是一組**隨歷史變動的規則**，含 DST（daylight saving time，日光節約時間）轉換、歷史上偏移的修改等。它由 **IANA tz database** 維護（每年發布數個版本，如 2026b），規則每年改數次（某國臨時改 DST、某地廢除 DST）。`UTC+8` 是固定偏移，`America/New_York` 不是——後者夏天 UTC−4、冬天 UTC−5。

第一原理：**儲存與運算用絕對瞬間（UTC / epoch），只在「對人顯示」與「對人輸入」的最後一哩才套 timezone**。時間/時鐘的因果排序面是本領域另一條目（見邏輯時鐘與排序）的範疇；排程的觸發語意（漏跑/補跑）在領域 J 只談那一面，這裡聚焦應用層的存、算、顯示坑。

### 解法空間

- **一律以 UTC / epoch 儲存**：DB 欄位用 `timestamptz`（PostgreSQL 內部存 UTC）或存 epoch 整數；絕不存「不帶時區的本地時間」（naive datetime），那是把未來自己坑死的根源。
- **顯示層才轉 timezone**：在 render 前用使用者的 IANA timezone（不是固定偏移）把 UTC 轉成本地時間。需要的是 zone ID（`Asia/Taipei`），不是 `+08:00`。
- **量「經過多久」用單調鐘（monotonic clock）**：`CLOCK_MONOTONIC` / `performance.now()` / `System.nanoTime()`，它不受 NTP 校正與 DST 影響、只會前進、可能在不同開機間無意義但「兩次讀數相減」永遠正確。**永遠別用牆鐘相減算時長**（牆鐘會往回跳，可能算出負的耗時）。
- **保持 tzdata 更新**：系統與執行時的 IANA tz database 要隨 OS/runtime 更新，否則某國剛改的 DST 規則沒進來，排程與顯示就會在那個區錯一小時。
- **用正確的日期時間函式庫**：避開語言內建的有缺陷 API。JavaScript 的 `Date` 不支援非本地時區、DST 處理不可靠；其替代 **Temporal API 已於 2026 年 3 月 TC39 會議進入 Stage 4、預定納入 ECMAScript 2027**（Firefox 139 自 2025-05、Chrome 144 自 2026-01 已預設支援），其 `ZonedDateTime` 正確處理 DST 轉換下的日期運算（2026-06）。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| 存 UTC / epoch | 絕對、單調、無時區歧義 | 所有「瞬間」的儲存與傳輸 | epoch 忽略閏秒；顯示時必須轉 timezone，別直接給人看 |
| 存 naive local datetime | （反例）看似直覺 | 幾乎沒有正確用途 | DST 那兩小時無法表達/有歧義；跨區搬家即錯亂；強烈不建議 |
| timezone 用 IANA zone ID | 正確含 DST 與歷史規則 | 對人顯示/排程在本地時間 | 依賴 tzdata 更新；規則每年改，需隨 OS/runtime 同步 |
| timezone 用固定偏移 `+08:00` | 簡單 | 該地永不實施 DST 且偏移永不變 | 對有 DST 的地區會錯一小時；別拿固定偏移代替 zone ID |
| 單調鐘量時長 | 不受 NTP/DST 影響、永遠單調 | timeout、量耗時、rate limit 視窗 | 不同行程/開機間數值無可比性，只能同源相減 |

**Worked example（DST 那兩小時的坑）**：在 `America/New_York`，2025 年 11 月 2 日當地時鐘從 02:00 退回 01:00（DST 結束）。於是「2025-11-02 01:30」**在當地出現兩次**——一次是 UTC−4 的 01:30（epoch X），一次是一小時後 UTC−5 的 01:30（epoch X+3600）。若你把使用者排的「01:30 提醒」存成 naive local time，系統無法判斷該對應哪個瞬間，可能不觸發、觸發兩次、或差一小時。反向地，春天「跳過」的那一小時（02:00 直接跳到 03:00），naive 的「02:30」是**不存在的瞬間**。存 UTC / epoch 從根本上沒有這個歧義——因為瞬間是唯一的，歧義只發生在「把民用時間反推成瞬間」時，而那一步應在輸入端用明確 zone 一次解析掉。

### 何時需要

幾乎**任何**碰到使用者可見時間、排程、跨時區、計費週期、保留期（retention）的系統都需要嚴守這些規則——成本極低（就是「存 UTC、顯示轉 zone、量時長用單調鐘」三條紀律），不守的代價是難重現的「差一小時」「DST 當天出錯」的 bug。唯一可放鬆的場景：純內部、單一固定時區、永不顯示給跨區使用者、且不依賴時長精度的拋棄式腳本——但即便如此，存 UTC 也不會更貴，沒有理由不存。

### 常見誤解與陷阱

- **用牆鐘相減算時長**：NTP 校正會讓牆鐘往回跳，`end - start` 可能是負數或暴衝。量耗時/timeout/rate-limit 視窗一律用單調鐘。
- **把 timezone 當固定偏移存**：存 `+08:00` 而非 `Asia/Taipei`，對有 DST 的地區（如多數歐美時區）會在 DST 切換後錯一小時。zone ID 才含完整規則。
- **以為 UTC 沒有 DST 就萬事大吉**：UTC 確實無 DST，但「使用者排的本地時間提醒」仍要在輸入端用使用者的 zone 正確轉成 UTC——轉換點才是出錯處，存成 UTC 後就安全。
- **tzdata 不更新**：某國臨時宣布廢除/改動 DST（近年屢見），若伺服器 tzdata 沒更新，該區的顯示與排程就錯一小時，且很難察覺。
- **閏秒與 epoch 的細節**：epoch 每天當 86,400 秒、忽略閏秒，所以兩個 epoch 相差不完全等於物理流逝秒數（極端精度場景才在意）；多數系統靠 NTP 用 leap smear（把閏秒抹平到一段時間）規避，但要知道這個前提存在。
- **以為內建 Date 型別可靠**：很多語言的原生日期 API（典型如 JavaScript `Date`）在時區/DST 上行為怪異，該用成熟函式庫或新標準（如 Temporal）。

### 延伸閱讀

- IANA Time Zone Database（tz database 官方，含 NEWS 變更日誌）：https://www.iana.org/time-zones
- RFC 9557 / RFC 3339（Internet 日期時間格式，含時區標註）：https://www.rfc-editor.org/rfc/rfc3339
- TC39 Temporal proposal（JavaScript 新日期時間 API，DST-aware）：https://tc39.es/proposal-temporal/docs/
