# S · 效能與延遲

這個領域處理的是「同一段邏輯，為什麼在真實負載下比在開發機慢、或慢得不穩定」。不是談演算法複雜度（那是程式本身的事），而是談**系統交界處**的延遲來源：第一次呼叫特別慢（冷啟動）、平均很快但偶爾很慢（長尾）、一個請求悄悄變成上百次 I/O（N+1）、太多細碎呼叫該合併（批次）、以及把連線這個稀缺資源調到剛好（連線池調校）。本檔含五條：冷啟動與暖機、tail latency 與長尾、N+1 查詢、批次／coalescing／debounce、連線池調校。脊椎仍是保證與取捨——每條都在問「你想要 p99 多低、你願意為它付多少常駐成本與複雜度」。邊界：連線池本身的機制（取得/歸還/語意）在領域 N 深講，本檔的「連線池調校」只談調參與監控；Lambda 特有的 SnapStart 在領域 J；過載下 ρ→1 的排隊爆炸在領域 E；p99/p999 的觀測與 SLO 在領域 I。

## 冷啟動與暖機

### 定義與原理

冷啟動（cold start）指一個執行單位**第一次**服務請求時，必須先付一筆只在「冷」狀態才付的一次性成本：載入程式碼、建立 runtime、初始化相依、建連線、預熱快取與 JIT。暖機（warmup）是反過來——在真正流量到達前，主動先把這些一次性成本付掉，讓第一個真實請求落在「已熱」的環境上。

第一原理是：**幾乎所有高效能執行體都把成本攤平到「之後的每一次呼叫」上，代價是「第一次呼叫」特別貴。** 三個典型來源層層疊加：

- **環境層**：新的容器/行程/函式環境要被排程、拉映像、解壓、啟動 runtime。serverless 與自動擴容的 pod 在擴容瞬間最明顯。
- **行程層**：載入並連結相依、讀設定、建立連線池（每條 TCP+TLS 握手）、預載入 in-process 快取。
- **執行體層**：JIT 與分層編譯。JVM HotSpot 啟動時全部走 interpreter（tier 0），方法被呼叫到門檻才升級——預設 `Tier3CompileThreshold≈2000` 進 C1（含 profiling）、`Tier4CompileThreshold≈15000` 進 C2（重度最佳化）；在跨過這些門檻前，熱路徑跑的是慢版本（2026-06）。V8（Node）類似，從 Ignition interpreter 到 TurboFan 也需要被多次執行才會被最佳化。

關鍵分辨：冷啟動是**狀態問題**，不是 bug。它總會發生在「每一個新環境的第一次」，所以高擴容比、低 QPS、突發尖峰、頻繁部署的系統受害最深；穩定高流量的長壽行程幾乎感覺不到。

### 解法空間

- **保溫（keep-warm / 常駐）**：讓環境不要被回收。serverless 用 provisioned/預留環境（見領域 J），長壽服務用 min-replicas 不縮到 0。直接消滅冷啟動，代價是常駐成本。
- **預初始化快照**：在啟動後、服務前先跑完 init，把記憶體狀態存成快照，之後從快照恢復而非重跑 init（Lambda SnapStart 是此類，見領域 J；CRaC 等屬同一思路）。
- **主動暖機請求**：部署後對新實例打一批合成請求，把熱路徑、連線、JIT 先跑熱，再放進負載均衡輪轉。配合 readiness probe 在「真的熱了」之前不收流量（見領域 P 的 health check）。
- **延遲/惰性初始化收斂**：把「只有第一次才需要、且昂貴」的初始化挪出請求路徑——例如建立連線池在啟動時就建滿 min connections，而不是等第一個請求才現連。
- **減少 init 本身**：縮小相依、砍掉啟動時的同步 I/O、用更輕的 runtime、AOT 編譯（如 GraalVM native image）把 JIT 暖機成本前移到 build 時。
- **流量塑形**：用漸進放量（canary/rolling，見領域 Q）讓新實例承接的初始流量緩慢爬升，避免一個冷實例瞬間吃滿。

### 各方案的保證與取捨

| 方案/做法 | 保證（消除哪段冷成本） | 適用場景 | 注意事項 |
|---|---|---|---|
| 常駐保溫（min-replicas / provisioned） | 消除環境+行程冷啟動；p99 平穩 | 對延遲敏感、流量有底盤的服務 | 你為「沒在用的容量」付錢；尖峰超過保溫量時仍冷啟 |
| 預初始化快照（SnapStart 類） | 消除大部分 init/JIT 暖機，恢復快 | init 重（大量相依/框架）的函式 | 快照恢復後**唯一性狀態被複製**（隨機種子、連線、暫存 ID 須在恢復鉤子重生）；非所有 runtime 支援（見領域 J） |
| 主動暖機請求 + readiness gate | 消除「第一個真實請求」的冷峰 | 自部署的長壽服務、容器化 | 合成請求要打到真實熱路徑（光打 /health 沒暖到業務碼）；暖機沒蓋到的路徑仍冷 |
| 啟動時建滿連線池 | 消除「首次查詢現連」延遲 | DB/下游連線昂貴的服務 | 啟動變慢、下游連線數在擴容瞬間放大（見連線池調校） |
| AOT / native image | 把 JIT 暖機移到 build 時 | 短壽、高擴容、要極速啟動 | 失去 JIT 的 peak 最佳化（長跑吞吐可能略低）、build 複雜、反射需設定 |

**worked example（量化保溫成本）**：一個函式冷啟動 init 耗 800 ms、熱呼叫 40 ms。平均 QPS 20、但每天部署 3 次、且自動縮放每小時回收一次環境。若不保溫，每個新環境的第一個請求多付約 760 ms；在 p99 觀測上，只要冷啟比例 >1% 就會把 p99 從 40 ms 拉到接近 800 ms（長尾被冷啟主導，見 tail latency）。改成預留 2 個常駐環境後，冷啟比例壓到突發尖峰才出現的 <0.1%，p99 回到 ~60 ms——代價是 2 個環境的常駐費用，無論有沒有流量都計。決策就是「常駐月費」對「p99 從 800 降到 60」這筆交換值不值。

### 何時需要

- **需要**：對 p99/p999 有硬 SLO 的同步請求路徑；流量會縮到 0 又突然來（活動、cron 觸發的批次喚醒）；init 很重（大框架、大量相依、JIT 語言）；高擴容比（一個尖峰要拉起幾十個新實例）。
- **過度**：穩定高流量、行程長壽、init 很輕的服務——它天然全熱，加保溫只是燒錢。離線批次/非同步 worker 對單次延遲不敏感，冷啟動被吞吐攤平，通常不必處理。先量「冷啟動佔請求比例」與「冷/熱延遲差」，差小或佔比低就別做。

### 常見誤解與陷阱

- **把保溫當「永遠不冷」**：保溫量是固定的，尖峰超過保溫量的那部分流量還是落在冷啟環境上。保溫降低冷啟「頻率」，不保證「絕不發生」。
- **暖機只打健康檢查端點**：沒走到真實業務碼、沒觸發真正的 DB 查詢與 JIT 熱路徑，等於沒暖。暖機請求要盡量擬真。
- **快照恢復忘了重生唯一性狀態**：從同一份記憶體快照恢復出多個環境，會共用恢復前產生的隨機種子、快取的時間、開到一半的連線。必須在恢復鉤子裡重建這些（見領域 J）。
- **把惰性初始化留在請求路徑**：「第一次用到才建」會把冷成本轉嫁給某個倒楣的真實請求，而非啟動階段。能在 init 期做完的就別惰性。
- **AOT 一律更快的迷思**：native image 啟動快，但放棄了 JIT 在長跑時依 profile 做的 peak 最佳化；長壽高吞吐服務的穩態吞吐可能反而輸給 JIT 暖機後的版本。

### 延伸閱讀

- [Understanding the Lambda execution environment lifecycle (AWS Lambda Developer Guide)](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)
- [Understanding and Remediating Cold Starts: An AWS Lambda Perspective (AWS Compute Blog)](https://aws.amazon.com/blogs/compute/understanding-and-remediating-cold-starts-an-aws-lambda-perspective/)
- [Tiered Compilation in JVM (Baeldung)](https://www.baeldung.com/jvm-tiered-compilation)
- [How Tiered Compilation works in OpenJDK (Microsoft for Java Developers)](https://devblogs.microsoft.com/java/how-tiered-compilation-works-in-openjdk/)

## tail latency 與長尾

### 定義與原理

tail latency 指延遲分布的尾端——p99、p999、最大值，而非平均或中位數。「長尾」是說：即使每個元件平均很快，**整體分布的尾巴會被放大、且被尾巴主導**。這條只談尾巴是怎麼長出來的（成因機制）；如何量它（p99/p999、coordinated omission）在領域 I。

第一原理有兩個：

**(1) fan-out 放大尾巴。** 一個請求若需要並行向 N 個後端取結果並全部等齊，整體延遲是這 N 個的**最大值**。即使每個後端只有 1% 機率變慢，整體碰到「至少一個慢」的機率是 1−0.99^N。N=100 時是 1−0.99^100 ≈ **63%**——也就是說，p99 的單機慢，在 fan-out 100 下會變成「多數請求都慢」。這是 Dean & Barroso〈The Tail at Scale〉（CACM, 2013）的核心觀察。

**(2) 變異來源無所不在且會疊加。** 單一元件的尾巴來自：共享資源競爭（CPU、鎖、連線池排隊）、背景活動（GC pause、compaction、log flush、快取失效後的回填）、排隊（ρ→1 時等待時間爆炸，見領域 E）、冷啟動（見上條）、網路重傳與 head-of-line blocking、以及偶發的慢碟/慢鄰居。請求路徑越長、串接的元件越多，這些獨立尾巴沿路徑相乘/相加，端到端尾巴遠比任一段嚴重。

平均值會騙人：一個服務平均 20 ms、p99 200 ms，若它在每個使用者操作裡被呼叫 10 次（串接或 fan-out），使用者體感的是尾巴而非平均。

### 解法空間

- **hedged requests（對沖請求）**：發給後端 A，若到了 p95 還沒回，**再發一份**給後端 B，取先回的。用少量額外負載換大幅尾巴下降——原論文示範對沖可把高百分位延遲砍掉一大截。
- **tied requests（綁定請求）**：同時發兩份但讓它們能互相取消——一份開始處理就通知另一份放棄，避免雙倍浪費。針對「尾巴主要來自佇列等待、一旦開始處理就快」的情況。
- **減少 fan-out 寬度或要求齊全度**：能不齊就不齊。用「夠好就回」（收到 95% 後端就回、慢的那 5% 走補資料）取代「等齊 100%」。
- **隔離背景活動**：把 GC、compaction、batch job 排到離峰或獨立資源，別和線上請求搶 CPU/IO（bulkhead，見領域 P）。
- **micro-partition + 動態再平衡**：把資料切成遠多於機器數的小分片，讓慢機器上的分片能快速搬走，避免單台慢機器拖累固定的一塊。
- **timeout/deadline budget**：給每段設預算，超時即放棄/降級（見領域 P），讓尾巴有上界、不無限拖。
- **加速最慢段**：用 profiling 找出貢獻尾巴的那個元件（慢查詢、鎖競爭、冷快取），對症處理——往往 80% 尾巴來自一兩個點。

### 各方案的保證與取捨

| 方案/做法 | 保證（對尾巴的效果） | 適用場景 | 注意事項 |
|---|---|---|---|
| hedged requests | 砍高百分位（p99/p999），效果顯著 | 可冪等重發、後端有多副本 | 增加總負載（典型多 5–10%）；必須冪等，否則重複副作用；過載時對沖會火上澆油（要設上限） |
| tied requests | 砍尾巴且幾乎不增浪費 | 尾巴主因是佇列等待 | 需要後端支援「開始即取消同伴」的協定，較複雜 |
| 降低 fan-out 齊全度 | 直接削掉「等最慢」的成本 | 結果可容忍部分缺失 | 改變正確性語意（回的是近似/部分結果），要產品端認可 |
| 隔離背景活動 / bulkhead | 消除 GC/compaction 撞線上 | 有明顯背景峰值的儲存/服務 | 需要資源隔離能力；排程錯了反而製造新峰 |
| timeout + 降級 | 給尾巴上界、可預期 | 任何有 SLO 的同步路徑 | 設太短砍掉本來會成功的慢請求（誤殺）；設太長等於沒設 |

**worked example（fan-out 放大）**：搜尋頁向 50 個分片並行查、等齊才回。單分片 p99 = 100 ms、中位數 = 10 ms。整體碰到「至少一個分片落在它自己 p99 尾巴」的機率 = 1−0.99^50 ≈ **39.5%**——意思是約四成的搜尋請求端到端 ≥100 ms，儘管單分片中位數只有 10 ms。加上 hedged requests（過了 30 ms 還沒回就對沖到副本），把單分片有效 p99 從 100 ms 壓到約 35 ms，整體「至少一慢」的尾巴隨之大幅收斂——代價是約多打了百分之幾的查詢量到副本上。

### 何時需要

- **需要**：高 fan-out 的讀路徑（搜尋、聚合、儀表板）；對 p99/p999 有硬 SLO；使用者一次操作串接多個服務（尾巴沿路徑放大）；後端有多副本可供對沖。
- **過度**：低 fan-out、單一後端、對單次延遲不敏感的非同步/批次工作。對沖/綁定請求在「無多副本」「副作用非冪等」「系統已接近過載」時不但無益還有害——這時該先處理過載與容量（見領域 E），而不是加對沖。

### 常見誤解與陷阱

- **用平均/中位數做容量與 SLO 決策**：尾巴才是使用者體感與級聯逾時的來源。盯 p99/p999（見領域 I）。
- **對沖請求未設上限**：系統一旦變慢，每個請求都觸發對沖 → 負載翻倍 → 更慢 → 更多對沖，演成 retry storm（見領域 E）。對沖必須有比率上限與熔斷。
- **對沖打到非冪等操作**：對寫入或有副作用的呼叫對沖會造成重複執行。對沖只用於可安全重發者（見領域 A 的冪等）。
- **把尾巴歸給單一兇手**：尾巴常是多個獨立來源疊加（GC + 鎖 + 冷快取 + 排隊），逐一量化貢獻、別只猜一個。
- **忽略 coordinated omission**：負載產生器若在系統卡住時也跟著不發請求，會系統性低估尾巴（見領域 I）。

### 延伸閱讀

- [The Tail at Scale — Dean & Barroso, Communications of the ACM 56(2):74–80, 2013 (PDF)](https://www.barroso.org/publications/TheTailAtScale.pdf)
- [The Tail at Scale — summary (the morning paper)](https://blog.acolyer.org/2015/01/15/the-tail-at-scale/)

## N+1 查詢

### 定義與原理

N+1 查詢是：取一份清單花 1 次查詢（拿到 N 個項目），接著為**每一個項目各發一次**後續查詢去補它的關聯資料，總共 1+N 次 round-trip。問題不在每次查詢本身慢，而在**次數**——N 個各自獨立的網路+解析+執行往返，把本該 2 次的事變成 N+1 次。

第一原理是延遲的可加性：每次 DB round-trip 有一筆**固定成本**（網路 RTT、查詢規劃、連線取得、結果序列化），即使每筆查的資料很小。N+1 把這筆固定成本乘以 N。它最典型出現在三個地方：ORM 的惰性關聯載入（存取 `order.customer` 觸發一次查詢）、迴圈裡發查詢、以及 GraphQL resolver 對清單的每個元素獨立解析欄位。

它是**隱性**的：在開發機上 N=5、資料在快取、看起來秒回；上線後 N=500、跨網段、DB 有負載，同一段碼就慢上百倍且難以從程式碼一眼看出（查詢藏在 ORM 的屬性存取後面）。

### 解法空間

- **eager loading / join**：在第一次查詢就把關聯一起取回（SQL JOIN，或 ORM 的 `include`/`JOIN FETCH`/`prefetch_related`）。1 次查詢拿齊。
- **IN-list 批次（兩段式）**：先查清單拿到 N 個 id，再用一次 `WHERE fk IN (id1,…,idN)` 把所有關聯一次撈回，記憶體裡 join。2 次查詢、不放大。
- **per-request 批次載入器（DataLoader 模式）**：在同一個事件迴圈 tick 內收集所有 `load(id)` 呼叫，coalesce 成單一批次查詢（`WHERE id IN (...)`），並在請求範圍內去重/快取。專治 GraphQL 的 resolver N+1，把 1+N 變 1+1（見批次／coalescing）。
- **查詢層投影**：只取需要的欄位、用資料庫端聚合/子查詢一次算完，避免「拉回來再逐筆補」。
- **快取關聯**：高重複的關聯（如商品分類）放快取，讓 N 次查詢多數命中快取而非 DB（見領域 G）。
- **偵測**：ORM 的 query log、APM 的「同一 SQL 模板在一個請求內被執行多次」告警、測試裡斷言「一個端點的查詢數 ≤ 門檻」。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| JOIN / eager loading | 1 次查詢取齊主表+關聯 | 關聯基數低、確定要用到 | 多個一對多 JOIN 造成笛卡兒乘積（行數爆炸、重複資料）；過度 eager 反而拉回用不到的欄 |
| IN-list 兩段式 | 固定 2 次查詢、不隨 N 放大 | 一對多、想避免 JOIN 爆行 | IN 清單過長（上萬）會撐爆查詢規劃/parser，須分批（如每批 1000） |
| DataLoader（per-request batch） | 1+1 次；同 tick 自動合併+去重 | GraphQL、巢狀 resolver | 快取是 request-scoped（別跨請求重用，會讀到舊資料）；只在同一 tick 內的 load 才會合併 |
| 關聯快取 | N 次查詢多數命中快取 | 關聯資料變動慢、重複率高 | 失效一致性問題（見領域 G）；只解重複關聯，不解「清單本身」的 N+1 |

**worked example**：訂單列表頁顯示 50 筆訂單，每筆要顯示客戶名。N+1 寫法 = 1 次查 50 筆訂單 + 50 次各查一個客戶 = 51 次 round-trip。設單次 DB round-trip 固定成本 2 ms（網路+規劃），純資料傳輸忽略，則 51 × 2 = **102 ms** 花在往返上。改成 IN-list：1 次查訂單 + 1 次 `SELECT … WHERE id IN (50 個 customer_id)` = 2 × 2 = **4 ms**。同樣的資料、同一個結果，延遲差 25 倍——而且 N 越大差距越大（N=500 時是 1002 ms vs 4 ms）。

### 何時需要

- **需要修**：任何「列表 + 逐項補關聯」的讀路徑；ORM 重的應用（惰性載入是預設行為，極易誤觸）；GraphQL 服務（巢狀查詢天然 N+1）；任何在迴圈裡發查詢的地方。
- **可以放著**：N 恆定且很小（如固定取 3 筆關聯）、且該路徑非熱點時，修它的收益低於複雜度。但要警惕「N 現在小不代表以後小」——資料長大後 N+1 會自己變嚴重。先用查詢計數測，超門檻才動手。

### 常見誤解與陷阱

- **以為 ORM 會自動避免**：絕大多數 ORM 預設惰性載入，存取關聯屬性就靜默發查詢——N+1 是 ORM 的預設陷阱，不是例外。
- **用 JOIN 一律解決**：一對多的 eager JOIN 會把主表行數乘上關聯數（笛卡兒膨脹），50 筆訂單 × 每筆 20 個明細 = 1000 行重複的訂單欄位回傳。這時 IN-list 兩段式才對。
- **開發機看不出來**：小資料 + 本機 DB（RTT ≈ 0）讓 N+1 在開發時無感。必須在「真實 RTT + 真實 N」下量。
- **DataLoader 跨請求共用快取**：DataLoader 的快取是設計給單一請求生命週期的；跨請求重用 instance 會發舊資料。每個請求建新的。
- **修了主關聯、漏了巢狀**：GraphQL 裡 A→B→C 每層都可能 N+1，只在 A→B 加 loader、B→C 仍逐筆。每一層關聯都要套。

### 延伸閱讀

- [Solving the N+1 Problem with DataLoader (GraphQL.js docs)](https://www.graphql-js.org/docs/n1-dataloader/)
- [graphql/dataloader (GitHub README — batching & caching semantics)](https://github.com/graphql/dataloader)
- [Batching (GraphQL Java documentation)](https://graphql-java.com/documentation/batching/)

## 批次 / coalescing / debounce

### 定義與原理

這三者都在做同一件事——**把多個小操作合併成較少的大操作**——但觸發語意不同，混用會出錯：

- **批次（batching）**：累積到「夠多」或「等夠久」就一次處理一整批。把 N 次固定成本（連線、RTT、規劃、commit）攤平成 1 次。典型參數：max batch size + max wait（湊不滿也別等太久）。
- **coalescing（合併/去重）**：把「指向同一目標的重複請求」收斂成一次實際工作，其餘等同一個結果。最常見是 **single-flight**：N 個並行請求要同一個還沒好的快取 key，只讓一個去後端、其餘共享它的結果（防快取擊穿，見領域 G）。
- **debounce**：高頻觸發時，**只在停止觸發一段時間後**才真正執行一次——「等它安定下來」。對照 **throttle**：固定時間窗內最多執行一次（限頻率，不等安定）。

第一原理都是「固定成本攤平 + 重複工作去除」：每次操作有與 payload 大小無關的固定開銷，合併把這筆開銷除以合併數。

辨析：批次是**主動湊量**（為了攤平固定成本）；coalescing 是**被動去重**（恰好撞在一起的相同工作只做一次）；debounce 是**抑制抖動**（連續觸發只認最後一次）。三者可疊加。

### 解法空間

- **size-or-time 批次窗**：累積到 N 筆或等到 T 毫秒（先到者觸發），兩個旋鈕一起調。寫入聚合、批次 insert、批次 ack 都用這個。
- **per-tick 批次（DataLoader 模式）**：在事件迴圈一個 tick 內把所有 `load()` 合併成一次後端呼叫（見 N+1 查詢）。延遲幾乎為零（下一個 tick 就發），無需固定等待窗。
- **single-flight / request coalescing**：用「進行中請求表」攔截對同一 key 的並行請求，第一個去做、其餘掛在它的 future 上等結果。
- **micro-batching（串流）**：把連續事件流切成小時間窗（如每 100 ms）成批處理，在「逐筆低延遲」與「批次高吞吐」間取折衷。
- **debounce / throttle**：對使用者輸入、resize、自動儲存、webhook 風暴等高頻觸發，debounce 等安定、throttle 限頻率。
- **寫入合併（write coalescing / write-behind）**：對同一筆資料的多次更新先在記憶體合併，再一次落盤/落 DB（見領域 G 的 write-behind）。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| size-or-time 批次 | 固定成本除以批量；吞吐↑ | 高頻小寫入、批次 ack/insert | 引入最多 T 的延遲；批越大單批失敗影響越多筆（要能部分重試/拆批） |
| per-tick batch（DataLoader） | 1+N → 1+1，延遲幾乎 0 | 同一 tick 內的重複/平行載入 | 只合併同 tick 內的；快取 request-scoped（見 N+1） |
| single-flight coalescing | 並行重複請求只打一次後端 | 熱 key 重建、防擊穿 | 第一個請求慢/失敗會連累全體（要設 timeout、失敗別快取）；只合併「同 key 且重疊時間」的 |
| debounce | 抖動期間只執行最後一次 | 輸入、自動儲存、UI 事件 | 持續觸發會無限延後執行（要設 maxWait 上限）；不適合「每次都得處理」的事件 |
| throttle | 每窗最多一次 | 限制下游呼叫頻率 | 會丟棄窗內其餘觸發（若不能丟，要改用佇列） |

**worked example（批次攤平固定成本）**：要寫 10,000 筆事件到 DB。逐筆 insert：每筆一次 round-trip + commit，設固定成本 1 ms/筆 → 10,000 × 1 = **10 s**。改用批次 insert（每批 500 筆、一次 `INSERT … VALUES (…),(…),…` + 一次 commit）：批數 = 10000/500 = 20 批，設每批固定成本仍 ~1 ms + 傳輸 1 ms = 2 ms → 20 × 2 = **40 ms**。同樣 10,000 筆，延遲從 10 s 降到 40 ms（250 倍），代價是：批量 500 引入最多「湊滿一批的等待」延遲、且一批若違反約束，整批 insert 失敗需拆批重試。批太大（如 50000 筆一批）又會撐爆單一交易、鎖太久、失敗代價過高——所以批量要在「攤平收益」與「單批風險」間取點。

### 何時需要

- **批次**：高頻小操作且每次固定成本佔比高（DB 寫入、外部 API 呼叫、訊息 ack）；下游支援批次介面；能容忍最多 T 的延遲。低頻或對單筆即時性要求高（如付款確認）就別批。
- **coalescing**：熱 key 在快取失效瞬間會被一群請求同時打（thundering herd），用 single-flight 收斂（見領域 G 的擊穿）。
- **debounce**：來源會「連發然後安定」（搜尋輸入、視窗調整、檔案監看），且只關心最終狀態。若每個事件都有獨立意義（每筆交易）就絕不能 debounce——會吃掉事件。

### 常見誤解與陷阱

- **batch 等待窗無上限**：只設 max size 不設 max wait，低流量時湊不滿一批會無限期卡住第一筆。size **與** time 兩個觸發都要有。
- **debounce 吃掉必須處理的事件**：對「每筆都得落地」的事件用 debounce，等於主動丟資料。debounce 只適合「只認最終狀態」的場景。
- **debounce 沒有 maxWait**：使用者持續打字，debounce 永遠在重置計時器、真正的搜尋永不執行。要設 maxWait 保證最遲一定觸發。
- **single-flight 不處理 leader 失敗**：被選去做事的那個請求若 hang 住，掛在它身上的全部一起 hang。必須給 leader 設 timeout，失敗時讓其餘 fallback，且失敗結果別寫快取。
- **批太大放大失敗半徑**：一批 N 筆，任一筆出錯可能讓整批回滾。批量要讓「單批失敗的重做成本」可接受，並設計成可拆批重試。
- **混淆 debounce 與 throttle**：要「限頻率、每窗都動一次」用 throttle；要「等安定、只動最後一次」用 debounce。選錯會是「該動時沒動」或「不該動時一直動」。

### 延伸閱讀

- [graphql/dataloader (GitHub — per-tick batching & coalescing)](https://github.com/graphql/dataloader)
- [golang.org/x/sync/singleflight (Go package — request coalescing)](https://pkg.go.dev/golang.org/x/sync/singleflight)

## 連線池調校

### 定義與原理

連線池的機制（為什麼要池化、取得/歸還/語意、leak 與 validation）在領域 N 深講。這條只談**調參與監控**：在池已經就位的前提下，怎麼把「池大小、逾時、生命週期」這幾個旋鈕調到剛好。

第一原理反直覺：**池不是越大越快。** 資料庫能並行有效處理的查詢數，大致受限於它的核心數與磁碟——再多的連線只是讓查詢在 DB 內部排隊、互相搶 CPU/鎖、製造 context switch，整體吞吐反而下降、延遲上升。HikariCP 官方〈About Pool Sizing〉給的經驗公式是 `connections = ((core_count × 2) + effective_spindle_count)`，其中 core 用**資料庫伺服器的實體核心數**、spindle 在資料全在快取時趨近 0、SSD 約為 1（2026-06）。也就是說一台 4 核、SSD 的 DB，最佳池大小約 `(4×2)+1 = 9`，「湊個整數叫 10」——往往遠小於工程師憑直覺設的數字。

另一個第一原理：**池大小是乘上實例數的。** 每個應用實例各開一個池，DB 看到的總連線 = 池大小 × 實例數。autoscale 到 50 個實例、每個池 20，就是 1000 條連線打向 DB——很容易撞穿 DB 的 `max_connections`。serverless 尤其致命：每個函式環境各自開連線、擴容瞬間連線數暴增，這是要在 DB 前面擺 PgBouncer/Accelerate 一類 pooler 的根本原因。

### 解法空間

- **算池大小，別猜**：用 `(cores×2)+spindle` 起步，再依負載測試微調。盯的是「DB 端的並行有效查詢數」，不是「應用端想要的並發」。
- **設連線取得逾時**：池滿時請求等不到連線該快速失敗，而非無限等。HikariCP `connectionTimeout` 預設 30,000 ms（30 s）——對線上請求往往太長，常調到 1–5 s 讓它 fail-fast（2026-06）。
- **設連線生命週期上限**：`maxLifetime`（連線最長壽命，到期回收重建，避開 DB 端/中間設備的閒置斷線）、`idleTimeout`（閒置連線回收到 minimumIdle）。要小於 DB/防火牆的閒置超時。
- **min/max 與預熱**：把 min 設足夠（甚至 = max）讓啟動就建滿，避免首次查詢現連的冷成本（見冷啟動與暖機）；max 依上面公式封頂。
- **前置 pooler（多實例/serverless）**：在 DB 前擺 PgBouncer，把上千個應用端連線收斂成 DB 能承受的數十條。模式要選對：session（最安全、相容所有功能、預設）、transaction（連線僅在交易期間綁定，併發最高、但 prepared statement/advisory lock/temp table 等 session 狀態不跨交易保留）、statement（最激進、禁多語句交易）。`default_pool_size` 預設約 20（2026-06）。
- **監控**：盯 active/idle/waiting 連線數、取得連線的等待時間、取得逾時次數、池耗盡事件、連線建立速率。這些指標比 CPU 更早預警「池配錯了」。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 公式定池大小（`(cores×2)+spindle`） | 吞吐接近 DB 上限、避免內部排隊 | 直連 DB 的服務 | 是起點不是終點，須用負載測試校正；用 DB 實體核心數，不是應用核心數 |
| 短 `connectionTimeout`（1–5 s） | 池滿時快速失敗、不堆積 | 線上同步請求 | 太短在正常尖峰誤殺；要配合 max 池大小與監控一起調 |
| `maxLifetime` < DB/FW 閒置超時 | 避免用到已被對端默默關掉的死連線 | 有 idle timeout 的 DB/中間設備 | 設太短頻繁重建連線（握手成本）；要比下游 timeout 略小留餘裕 |
| PgBouncer transaction 模式 | 上千客戶端收斂成數十 DB 連線 | 多實例/serverless、短交易 | session 狀態（prepared statement/advisory lock/temp table）不跨交易保留，ORM 預設要相容調整 |
| 連線池指標監控 | 提早發現耗盡/等待/泄漏 | 所有用池的服務 | 沒有 waiting/timeout 指標等於盲調；只看 CPU 看不到池問題 |

**worked example（池大小撞穿 DB）**：應用每實例 HikariCP `maximumPoolSize=20`，autoscale 從 5 個實例擴到 30。DB 的 `max_connections=200`。直連時 DB 看到的連線 = 20 × 30 = **600**，遠超 200——新連線被拒、應用端報「too many connections」、整片掛掉，而且這發生在「流量大到要擴容」的最糟時刻。兩個修法：(a) 把每實例池調到符合 `(cores×2)+spindle`——若 DB 是 8 核 SSD，最佳並行查詢約 `(8×2)+1=17`，那麼**全體**實例共享的有效並發應接近 17 而非 600，逐實例池該設得很小（如 2–4）並前置 pooler；(b) 擺 PgBouncer，應用端開 600 條到 PgBouncer，PgBouncer 用 transaction 模式把對 DB 的實際連線壓在 `default_pool_size`（如 20）內。多實例/serverless 幾乎一定要走 (b)。

### 何時需要

- **需要認真調**：DB 連線是瓶頸或接近 `max_connections`；多實例/autoscale/serverless（連線數會乘上實例數）；看到「取得連線等待時間」或「too many connections」上升。
- **可以用預設**：單實例、低並發、DB 連線遠未飽和的服務——預設池（如 HikariCP `maximumPoolSize=10`）通常夠用，過早調校是 over-engineering。先量「池等待時間」與「DB 連線數 / max_connections」兩個指標，有壓力再動。

### 常見誤解與陷阱

- **池越大越快**：超過 DB 能並行有效處理的數量後，加連線只增加 DB 內部排隊與爭用，吞吐降、延遲升。池大小是個有最佳值的凹函數，不是越大越好。
- **忘了乘以實例數**：每實例池 × 實例數才是 DB 看到的總連線。憑單實例直覺設池，一擴容就撞穿 `max_connections`。
- **連線取得逾時用預設 30 s**：線上請求在池滿時會排隊等到 30 s 才失敗，期間請求堆積、執行緒佔住——往往該調到 1–5 s 快速失敗（2026-06）。
- **`maxLifetime` 沒小於下游閒置超時**：DB 或防火牆默默關掉閒置連線，池卻以為它還活著，下次借出時才在查詢中途爆「connection reset」。`maxLifetime` 要比下游的 idle timeout 短。
- **在 transaction 模式 pooler 下用 session 狀態**：PgBouncer transaction 模式不保證同一連線跨交易，prepared statement / advisory lock / temp table / session 變數會錯亂。ORM（如某些預設用 prepared statement 的）要設定相容（見領域 N、B）。
- **只看 CPU 不看池指標**：池耗盡時 CPU 可能很閒（大家都在等連線），光看 CPU 完全看不出問題。必須監控 active/idle/waiting 與取得逾時次數。

### 延伸閱讀

- [About Pool Sizing (brettwooldridge/HikariCP Wiki)](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)
- [HikariCP configuration knobs (HikariCP README)](https://github.com/brettwooldridge/HikariCP#configuration-knobs-baby)
- [PgBouncer configuration (pgbouncer.org)](https://www.pgbouncer.org/config.html)
- [PgBouncer pooling modes / features (pgbouncer.org)](https://www.pgbouncer.org/features.html)
