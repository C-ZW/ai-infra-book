# 附錄 B · 術語表

這份術語表把全書出現的關鍵概念與重要英文名詞收成一條一行的速查清單，定義刻意壓到「資深工程師看一眼就想起來」的密度。每條句尾的「（見 …，領域 X）」指向正文裡把它講深的那個條目；想看機制、取捨與陷阱，回到該條目。定義與正文一致，不在此新增書裡沒講的概念。按英文（或中文音序）字母分組，未必有對應英文者排在 Z 之後的「中文索引」。

## A–B

**ABAC（Attribute-Based Access Control）**：以「主體／資源／環境的屬性」即時運算授權，而非預先綁角色，換靈活與細粒度但難審計。（見 RBAC vs ABAC，領域 F）

**ABI / 漂移（drift）**：宣告的期望狀態與真實基礎設施悄悄分叉的現象；IaC 的核心敵人之一。（見 IaC，領域 Q）

**ACID**：交易的原子性／一致性／隔離性／持久性四保證，強一致哲學的代名詞；與 BASE 為光譜兩端。（見 ACID vs BASE，領域 B）

**ADR（Architecture Decision Record）**：記錄一個有架構影響的決策、其脈絡（forces）、選擇與後果的短文件，補回隨人離職而蒸發的「決策理由」。（見 架構決策紀錄 ADR，領域 T）

**AEAD**：同時提供加密與完整性的對稱加密模式；TLS 1.3 只留 AEAD cipher。（見 TLS / mTLS，領域 N）

**ALB（Application Load Balancer）**：AWS 的 L7 負載均衡器，可做路徑/標頭路由，但非完整 API 閘道。（見 ALB vs API Gateway vs KrakenD vs Kong，領域 H）

**anti-entropy**：副本間週期性比對差異並修補，使資料最終收斂的背景修復機制；常與 gossip 搭配。（見 gossip / anti-entropy，領域 M）

**AOF（Append-Only File）**：Redis 把每條寫指令追加進日誌的持久化模式，比 RDB 丟得少但檔案大、重放慢。（見 持久化，領域 G）

**API gateway**：擺在外部 client 與後端服務群之間的反向代理，集中認證、限流、TLS 終結、路由等橫切關注。（見 API gateway 的角色，領域 H）

**at-least-once**：訊息至少送達一次的交付語意（多數系統預設），代價是消費端必須自己處理重複。（見 交付語意三選一 / at-least-once 與重複處理，領域 A）

**at-most-once**：訊息至多送達一次的交付語意，不重複但可能丟。（見 交付語意三選一，領域 A）

**AuthN / AuthZ（認證 / 授權）**：AuthN 問「你是誰」、AuthZ 問「你能做什麼」，兩者正交；OIDC 補的是 AuthN 那塊。（見 認證 vs 授權，領域 F）

**backpressure（背壓）**：下游處理不過來時把「慢下來」訊號往上游傳，避免緩衝無限長大；穩定管線的守恆律。（見 背壓 backpressure，領域 E）

**back-of-the-envelope（量級估算）**：不建系統、用幾個硬數字把設計會撞到哪面牆算到正確數量級的判斷工具。（見 量級估算與容量直覺，領域 U）

**BASE（Basically Available, Soft state, Eventually consistent）**：以可用性與最終一致換強一致的哲學；ACID 的對立端。（見 ACID vs BASE，領域 B）

**blameless postmortem（無咎事後檢討）**：事故後把經驗轉成「下次不會再犯」的書面學習，對事不對人。（見 事故應變與無咎事後檢討，領域 V）

**blocking I/O（阻塞 I/O）**：發起 I/O 的呼叫會把該執行緒停住等到資料就緒；與非阻塞相對。（見 阻塞 vs 非阻塞 I/O，領域 D）

**blue-green**：同時備好新舊兩套環境、一次性把流量整批切到新版的發布策略，回退快但需雙倍資源。（見 blue-green / canary / rolling，領域 Q）

**B-tree**：就地維護有序的索引/儲存結構，讀放大低、寫較分散；與 LSM-tree 為兩大流派。（見 LSM-tree vs B-tree / 索引與查詢計畫，領域 O、B）

**budget（deadline budget）**：跨多跳呼叫時把總時間預算逐跳遞減傳遞，避免下游各自從零計時導致總延遲失控。（見 timeout / deadline / budget，領域 P）

**Bull / BullMQ**：Node.js 以 Redis 為後端的 job queue 函式庫，定位是 background job processing 而非訊息傳遞。（見 Bull / BullMQ，領域 A）

**bulkhead（艙壁隔離）**：把資源（執行緒池、連線池）分艙，一艙耗盡不波及其他，防局部故障擴散。（見 bulkhead 艙壁隔離，領域 P）

## C–D

**canary**：先把新版放給一小撮流量觀察、再逐步放大的發布策略，縮小 blast radius。（見 blue-green / canary / rolling，領域 Q）

**CAP**：分散式系統在分區時只能在一致性與可用性間二選一的定理（Brewer 2000 猜想，Gilbert-Lynch 2002 證明）。（見 CAP / PACELC，領域 B）

**cardinality（基數）爆炸**：time series 數＝各標籤取值數的乘積，把高基數欄位（如 user_id）放進 label 會炸掉時序庫。（見 cardinality 爆炸，領域 I）

**CAS（Compare-And-Swap）**：「比對舊值相符才寫」的原子操作，樂觀並發控制的基礎。（見 樂觀 vs 悲觀並發控制，領域 B）

**cache-aside（look-aside）**：讀未命中時應用自己回填快取的策略；最常見、但有並發回填與失效裂縫。（見 快取策略，領域 G）

**CDC（Change Data Capture）**：讀資料庫交易日誌（WAL/binlog）解析成變更串流餵下游，可靠且不漏地擷取每筆變更。（見 CDC 變更資料擷取，領域 L）

**circuit breaker（斷路器）**：下游故障率超閾值時主動切斷呼叫、快速失敗，防慢逾時耗盡資源池釀級聯失敗。（見 circuit breaker，領域 E）

**coalescing（合併）**：把短時間內對同一目標的多個請求併成一次，去重式地省下重複工作。（見 批次 / coalescing / debounce，領域 S）

**cohesion（內聚）**：模組內部元素為同一目的服務的程度，越高越好；與耦合互補。（見 耦合 vs 內聚，領域 K）

**cold start（冷啟動）**：執行單位第一次服務請求須先付的一次性成本（載碼、建 runtime、建連線、JIT）。（見 冷啟動與暖機，領域 S）

**connection pool（連線池）**：預建、保活、可重借的連線集合，攤平建連成本並當天然並發閘門。（見 連線池 connection pool / 連線池調校，領域 N、S）

**consensus（共識）**：一組節點在部分故障與不可靠網路下對某值（通常是 replicated log 下一條目）達成不可推翻的一致決定。（見 共識 consensus，領域 M）

**consistent hashing**：把 key 與節點映到同一個 hash 環，節點增減只搬動相鄰一段 key，避免 `% N` 的全量重映射。（見 consistent hashing，領域 M）

**coordinated omission**：負載測試/量測在系統卡住時漏記被延誤的請求，導致 p99 被嚴重低估的陷阱。（見 tail latency 與長尾 / 負載測試，領域 S、I）

**CQRS（Command Query Responsibility Segregation）**：把改狀態的寫模型與讀查詢模型拆成兩個各自最佳化的模型；常與 event sourcing 搭配。（見 Event sourcing 與 CQRS，領域 K）

**CRDT（Conflict-free Replicated Data Type）**：設計成合併天然可交換的資料型別，多副本各自更新後總能收斂到同一結果，無需協調。（見 衝突解決，領域 L）

**CronJob（K8s）**：依 cron 時間表反覆建立 Job 的控制器；它只排程，真正執行語意落在它生出的 Job 上。（見 K8s CronJob，領域 J）

**cursor / keyset pagination**：以「上一頁最後一筆的排序鍵值」當座標往下翻，避開深分頁的 offset 掃描成本與漂移。（見 分頁 pagination，領域 H）

**DLQ（dead-letter queue，死信佇列）**：反覆處理失敗、超過上限的訊息的最終停放處，防毒訊息無限重投卡住 head。（見 DLQ 死信與毒訊息，領域 A）

**deadlock（死結）**：多個交易互相等對方手上的鎖形成環、誰也不放；靠 wait-for graph 偵測或逾時打破。（見 鎖與死結，領域 B）

**debounce**：只在一連串事件「停下來」後才觸發一次，與只取頭/尾的合併語意不同。（見 批次 / coalescing / debounce，領域 S）

**decoupling（解耦）**：有意識地剪掉「A 對 B 的假設」這些繩子，換兩端各自變動的自由。（見 解耦 decoupling，領域 K）

**dedup（去重）**：在 at-least-once 之上於操作前判斷「這筆見過嗎」，讓不冪等操作對外表現得像只執行一次。（見 去重 dedup，領域 A）

**DNS-based service discovery**：用名字→IP 解析做服務發現，但 DNS 快取模型與實例頻繁變動天生矛盾。（見 DNS 與服務發現，領域 N）

**Docker / 容器**：同一 host kernel 上被 namespace（隔離視野）＋cgroup（限制資源）罩住的一群普通行程，非輕量 VM。（見 Docker，領域 Q）

**DORA 四指標**：部署頻率、變更前置時間、變更失敗率、復原時間；證明速度與穩定不是取捨。（見 DORA 四指標，領域 V）

**dual-write 問題**：一個操作要原子地更新兩個無共同交易邊界的系統，兩次寫之間的崩潰會讓兩端分叉。（見 dual-write 問題與 outbox / outbox / saga，領域 L、A）

**durable execution（持久化工作流）**：把長流程的狀態與進度持久化，讓行程崩潰後能「從斷點繼續」而非從頭重來或卡死。（見 持久化工作流與 durable execution，領域 K）

## E–G

**EDA（Event-Driven Architecture）**：用「事件＝已發生的事實」廣播取代「命令＝叫你做事」，產生者不必認識任何消費者。（見 事件驅動架構 EDA，領域 K）

**error budget（錯誤預算）**：1 − SLO 給出的「允許不可靠的額度」，把可靠性變成可消費、可談判的數字。（見 SLI / SLO / error budget / SRE 文化，領域 I、V）

**eventual consistency（最終一致性）**：副本短暫不一致但保證最終收斂；高可用低延遲的代價。（見 一致性光譜 / 最終一致 · 補償 · 對帳，領域 B）

**event loop**：單執行緒輪詢就緒事件、跑 callback 的並發機制；鐵律是主執行緒永不同步阻塞。（見 event loop，領域 D）

**event sourcing（事件溯源）**：不存當前狀態、改存導致它的不可變事件序列，當前狀態由 replay 算出。（見 Event sourcing 與 CQRS，領域 K）

**Envoy**：service mesh 常用的 sidecar 代理，承載 mTLS、重試、熔斷、路由、可觀測性。（見 service mesh，領域 N）

**EOS（exactly-once semantics, Kafka）**：Kafka 以冪等 producer ＋ 交易把「讀-處理-寫」串成原子，得到端到端有效一次的效果。（見 Kafka / exactly-once 的真相，領域 A）

**ETag**：資源版本指紋，配 conditional request 做樂觀並發控制（If-Match）。（見 樂觀 vs 悲觀並發控制，領域 B）

**eviction（驅逐）**：記憶體滿時依某種「未來最不可能被用」的近似（LRU/LFU/TTL）丟掉既有鍵；與過期不同。（見 驅逐 eviction，領域 G）

**exactly-once**：被最常誤用的詞；真相是「傳輸恰好一次」幾乎不可得，可得的是「效果有效一次」＝at-least-once ＋ 冪等/去重。（見 exactly-once 的真相，領域 A）

**fail-fast**：一偵測到不對就立刻、大聲失敗、不帶壞狀態續跑，把問題暴露在離源頭最近處。（見 錯誤處理哲學，領域 U）

**fallback（降級）**：主路徑失敗時回一個次等但仍可用的結果，「部分可用 > 完全不可用」。（見 fallback · 降級，領域 P）

**fan-out**：一發多收；SNS 把一則訊息推給所有訂閱端點是典型。（見 SNS，領域 A）

**fencing token**：分散式鎖發放的單調遞增記號，讓被搶走鎖的舊持有者的延遲寫入能被資源端拒絕。（見 分散式鎖，領域 M）

**FIFO ordering**：每個 key（partition key）內訊息照發生序消費，而非全域單一總序（那會塌掉吞吐）。（見 訊息順序 ordering / SQS，領域 A）

**fsync**：強制把寫入落穩到磁碟的呼叫；fsync 越勤丟得越少但吞吐越低，是持久化的核心旋鈕。（見 持久化，領域 G）

**full-text search（全文搜尋）**：靠 inverted index 把「掃所有文件找詞」翻轉成「查一個詞直接拿含它的文件清單」。（見 全文搜尋與 inverted index，領域 O）

**gap / next-key lock**：InnoDB 鎖在索引區間上、用來擋 phantom 的鎖；查詢命不命中索引直接決定鎖多大一片。（見 鎖與死結 / PostgreSQL vs MySQL，領域 B）

**golden path / paved road（鋪路）**：把「照建議做」那條路修到比任何其他選擇都明顯省力，靠引力而非強制推採用。（見 鋪路 paved road／golden path，領域 T）

**gossip**：節點隨機互傳狀態、讓成員/故障/設定資訊最終傳遍叢集並趨同，無中央瓶頸。（見 gossip / anti-entropy，領域 M）

**graceful shutdown（優雅退場）**：結束時停收新工作→做完手上工作→釋放資源→退出，不硬斷進行中的請求。（見 graceful shutdown，領域 P）

**GraphQL**：由 client 決定回傳資料形狀的查詢式 API 範式；解 over/under-fetching 但有 N+1 與快取難題。（見 API 範式對照，領域 H）

**gRPC / Protobuf**：以 `.proto` 當 IDL、跑 HTTP/2、Protobuf 二進位序列化的跨語言 RPC 框架。（見 gRPC / Protobuf，領域 N）

## H–L

**HLC（Hybrid Logical Clock）**：混合牆鐘與邏輯時鐘，既能比因果先後又貼近物理時間。（見 邏輯時鐘與排序，領域 M）

**health check（liveness / readiness）**：liveness 答「該不該重啟我」、readiness 答「該不該送流量給我」，兩者語意不可混。（見 health check，領域 P）

**HPA（Horizontal Pod Autoscaler）**：K8s 依指標自動增減 Pod 數的控制器。（見 Kubernetes，領域 Q）

**HTTP/1.1 · 2 · 3**：keep-alive 重用連線、HTTP/2 多工、HTTP/3 用 QUIC 解 TCP 層 head-of-line blocking。（見 HTTP/1.1 · 2 · 3，領域 N）

**HS256 / RS256**：HS256 對稱簽章（同一把密鑰簽與驗）、RS256 非對稱簽章（私鑰簽、公鑰驗，配 JWKS 發布公鑰）。（見 對稱 vs 非對稱簽章，領域 F）

**IaC（Infrastructure as Code）**：把基礎設施期望狀態寫成可版控程式碼、由工具收斂現實，治「雪花伺服器」與漂移。（見 IaC，領域 Q）

**idempotency（冪等）**：`f(f(x)) = f(x)`，重複執行不改變淨效果；at-least-once 之上的安全網。（見 冪等 idempotency，領域 A）

**inverted index（倒排索引）**：詞→文件清單的索引結構，全文搜尋的核心。（見 全文搜尋與 inverted index，領域 O）

**isolation level（隔離級別）**：用「容許哪些讀寫交錯異常」（dirty/non-repeatable/phantom/write-skew）定義，而非用「鎖什麼」。（見 隔離級別與異常，領域 B）

**jitter**：在退避間隔加隨機抖動，讓多個 client 重試時刻錯開，避免同步重試把下游再打垮。（見 重試、退避、jitter，領域 A）

**JWKS（JSON Web Key Set）**：發布驗章用公鑰的端點，讓驗證方按 `kid` 取對應公鑰、支援輪替。（見 對稱 vs 非對稱簽章 / JWT，領域 F）

**JWT（JSON Web Token）**：自包含、可簽章的 token 格式，三段 base64url 以 `.` 連接，驗章通過即信任 claims。（見 JWT，領域 F）

**Kafka**：分散式、可持久化、可重放的 append-only commit log；以 partition、consumer group、offset 為核心抽象。（見 Kafka，領域 A）

**Kong / KrakenD**：API 閘道；Kong 偏外掛生態（Lua/插件）、KrakenD 偏無狀態高效能聚合。（見 ALB vs API Gateway vs KrakenD vs Kong，領域 H）

**Kubernetes**：宣告式控制迴圈系統，靠 controller 持續把實際狀態收斂到期望狀態，自我修復是其自然結果。（見 Kubernetes，領域 Q）

**L4 vs L7 load balancing**：L4 只看 IP/port 轉發、L7 看 HTTP 內容（路徑、標頭）可做更聰明路由但較貴。（見 負載均衡 L4 vs L7，領域 N）

**Lambda**：事件驅動 serverless 運算，一個 execution environment 同一瞬間只服務一個 invocation，N 並發＝N 個環境。（見 Lambda，領域 J）

**Lamport clock**：邏輯時鐘，給事件單調遞增計數以推因果先後，不依賴不可信的牆鐘。（見 邏輯時鐘與排序，領域 M）

**leader election**：在崩潰/復活、訊息延遲下選出且只選出一個 leader，難點是保證任一時刻最多一個有效 leader（防 split-brain）。（見 leader election，領域 M）

**load shedding（卸載）**：過載時依真實飽和度主動丟一部分工作，保住剩下那部分的品質；與 rate limiting 觸發條件不同。（見 load shedding，領域 E）

**long-poll**：client 發請求後 server 一直掛著到有資料才回，再立刻重連，模擬 server 推送的退路機制。（見 SSE / long-poll / WebTransport，領域 C）

**LRU / LFU**：最近最少使用 / 最不常使用的驅逐策略；各有被特定存取樣式打敗的弱點。（見 驅逐 eviction，領域 G）

**LSM-tree**：先追加再合併整理的儲存流派，寫放大低、讀放大較高；與 B-tree 相對。（見 LSM-tree vs B-tree，領域 O）

## M–O

**MCU（Multipoint Control Unit）**：WebRTC 多方架構，伺服器把多路混成一路再下發，省 client 解碼但伺服器重。（見 WebRTC，領域 C）

**mesh（WebRTC）**：多方各自全網狀直連的架構，無中心伺服器但人數一多連線數爆炸。（見 WebRTC，領域 C）

**metastable failure（亞穩定故障）**：觸發事件讓系統進入自我維持的過載壞狀態，即使觸發消失也卡在低 goodput 出不來。（見 retry storm 與 metastable failure，領域 E）

**migration（漸進式遷移）**：把一次性 big-bang cutover 拆成許多次可回退小步，新舊並存、流量逐步轉移。（見 漸進式遷移與淘汰，領域 T）

**mTLS（雙向 TLS）**：client 與 server 互相用憑證驗身分，service mesh 內服務間通訊的常用底座。（見 TLS / mTLS，領域 N）

**multi-tenancy（多租戶）**：同一套系統服務多個獨立客戶，核心取捨是隔離強度 vs 資源效率（row/schema/db-per-tenant）。（見 多租戶隔離，領域 B）

**MVCC（多版本並發控制）**：寫不就地覆蓋、改寫新版本；讀去找對自己可見的版本，讀寫不互等。（見 MVCC，領域 B）

**N+1 查詢**：取清單 1 次再為每項各查 1 次，總 1+N 次往返；問題在次數而非單次慢。（見 N+1 查詢，領域 S）

**namespace / cgroup**：容器隔離的兩組 Linux 原語——namespace 隔離視野、cgroup 限制資源。（見 Docker，領域 Q）

**non-blocking I/O（非阻塞 I/O）**：無資料時 `read()` 立刻返回、執行緒去做別的，靠就緒通知（epoll/kqueue）回頭處理。（見 阻塞 vs 非阻塞 I/O，領域 D）

**NoSQL**：一組為特定存取模式放棄關係模型某部分（換水平擴展/寫吞吐/貼合資料形狀）的家族（文件/KV/寬欄/圖/時序）。（見 SQL vs NoSQL，領域 O）

**OAuth2 / OAuth 2.1**：授權委派框架（給第三方有限存取權），2.1 收斂為強制 PKCE、棄用隱式流程等安全預設。（見 OAuth2 / OIDC / OAuth 2.1，領域 F）

**offset pagination**：用「跳過 N 筆」當翻頁座標；簡單但深分頁時掃描成本高、資料變動會漂。（見 分頁 pagination，領域 H）

**OIDC（OpenID Connect）**：架在 OAuth2 上補認證（AuthN）那塊、發 ID token 的協定。（見 OAuth2 / OIDC / OAuth 2.1 / 認證 vs 授權，領域 F）

**OpenAPI**：以機器可讀契約描述 REST API（路徑、schema、狀態碼），讓契約可驗證、可生碼。（見 REST 設計 · 版本化 · OpenAPI 契約，領域 H）

**outbox**：把「對外發訊息」與業務寫入放進同一筆本地交易（寫 outbox 表），再由獨立投遞器搬出去，解 dual-write。（見 outbox / saga / dual-write 問題與 outbox，領域 A、L）

## P–R

**p99 / p999（尾延遲分位數）**：延遲分布尾端，使用者體驗由它主導而非平均；長尾會被組合放大。（見 tail latency 與長尾 / SLI / SLO，領域 S、I）

**PACELC**：CAP 的延伸——分區時在 A/C 取捨，否則（Else）在延遲 L 與一致性 C 取捨（Abadi 提出）。（見 CAP / PACELC，領域 B）

**partition（分區）**：網路被切開使節點互不可達，分散式失敗模型的核心威脅；也指 Kafka 等的並行/順序單位。（見 分散式失敗模型 / CAP，領域 M、B）

**partition key**：決定訊息落哪個 partition 的鍵，同 key 內保序、不同 key 間可並行。（見 訊息順序 ordering，領域 A）

**phantom read（幻讀）**：同一交易內兩次範圍查詢結果集因他人插入而改變的異常；可重複讀以下級別可能出現。（見 隔離級別與異常，領域 B）

**poison message（毒訊息）**：內容讓 consumer 每次都崩潰/拒絕的訊息，無 DLQ 時會無限重投卡住佇列。（見 DLQ 死信與毒訊息，領域 A）

**PostgreSQL vs MySQL**：兩者都用 MVCC，但實作隔離走相反路線（SSI 序列化快照 vs next-key lock），在 RR 保證、擋 phantom、真 serializable 上分得最開。（見 PostgreSQL vs MySQL，領域 B）

**probe（liveness / readiness probe）**：K8s 探針，設定欄位語意決定何時重啟或摘流量；機制本質見 health check。（見 Kubernetes / health check，領域 Q、P）

**QUIC**：HTTP/3 的底層傳輸，跑在 UDP 上、把 TLS 內建、解 TCP 層 head-of-line blocking。（見 HTTP/1.1 · 2 · 3，領域 N）

**quorum（R + W > N）**：無主複製靠「讀寫多數重疊」達成一致，調 R/W 在一致性、可用性、延遲間取捨。（見 quorum，領域 M）

**race condition（競態）**：多單元並發存取共享狀態、結果取決於交錯時序的不確定 bug；原子性是解藥之一。（見 race condition 與原子性，領域 D）

**RabbitMQ**：AMQP broker，以 exchange＋binding＋routing key 把「發布」與「投遞」解耦，consumer 從 queue 取。（見 RabbitMQ，領域 A）

**rate limiting**：事前依預設速率上限在門口擋超量請求，把保護從事後救火變事前配額；與 load shedding 觸發條件不同。（見 rate limiting，領域 E）

**RBAC（Role-Based Access Control）**：把權限綁到角色、使用者綁角色來授權；簡單可審計但細粒度與跨維度條件較弱。（見 RBAC vs ABAC，領域 F）

**RDB（Redis snapshot）**：Redis 定點把整份記憶體快照到磁碟的持久化，快但崩潰會丟兩次快照間的寫入。（見 持久化，領域 G）

**reconciliation（對帳）**：對兩份本該一致的資料做「持續驗證＋主動修復」，因為任何長跑同步管線最終都會漂移。（見 對帳 reconciliation / 最終一致 · 補償 · 對帳，領域 L、B）

**Redis**：記憶體型資料結構儲存，指令單執行緒序列執行故天然原子，代價是慢指令會阻塞全部。（見 Redis，領域 G）

**Redis Pub/Sub vs Streams**：Pub/Sub 不持久、訂閱者不在就丟（at-most-once）；Streams 持久、可重放、有 consumer group。（見 Redis Pub/Sub vs Streams，領域 A）

**Redlock**：Redis 多節點分散式鎖演算法；其安全性有爭議，關鍵互斥仍須配 fencing token。（見 分散式鎖，領域 M）

**replication lag（複製延遲）**：副本非同步重放 WAL/binlog 落後主庫的時間差，會打破「讀己之寫」直覺。（見 複製延遲與讀己之寫，領域 B）

**replication（複製）**：把同份資料存多節點以容錯/讀擴展/就近服務；按「誰能接受寫入」分單主/多主/無主三範式。（見 複製策略，領域 M）

**REST**：以資源為中心、用統一 HTTP 介面操作的架構約束；真正的保證來自可機器驗證的契約而非漂亮 URL。（見 REST 設計 · 版本化 · OpenAPI 契約，領域 H）

**retry storm（重試風暴）**：下游一慢、上游重試把一個失敗放大成多個請求，正回饋把小故障滾成大災難。（見 retry storm 與 metastable failure，領域 E）

**RFC 流程（設計文件）**：把有實質後果的技術決定在動手前寫成文件、公開徵求意見、留下決議的慣例。（見 RFC／設計文件流程，領域 T）

**rolling**：逐批替換實例的發布策略，過程中新舊版本同時在線（須 schema 與訊息相容）。（見 blue-green / canary / rolling，領域 Q）

**runbook**：把「這類事故怎麼處理」事先寫下的操作手冊，縮短事故應變的決策時間。（見 事故應變與無咎事後檢討，領域 V）

## S–T

**S3 / 物件儲存**：以不可變物件（bytes＋metadata＋key）存於扁平 bucket、經 HTTP 存取，無目錄樹、無部分就地更新。（見 S3 / 物件儲存，領域 G）

**saga**：用一串本地交易＋對應補償動作完成跨服務「交易」，失敗時逐步補償回滾，換的是不要分散式鎖定。（見 outbox / saga，領域 A）

**schema 演進**：生產者與消費者不同時升級，故 schema 改動須維持前向/後向相容，舊版對端仍能正確讀寫。（見 序列化與 schema 演進 / 零停機 schema 遷移，領域 A、B）

**SFU（Selective Forwarding Unit）**：WebRTC 多方架構，伺服器只轉發不混流，伺服器較輕、client 收多路。（見 WebRTC，領域 C）

**service discovery（服務發現）**：在實例自動擴縮漂移的環境裡，讓呼叫端知道目標服務現在跑在哪些 IP:port。（見 DNS 與服務發現，領域 N）

**service mesh**：把服務間通訊的橫切關注（mTLS、重試、熔斷、路由、可觀測性）下放到 sidecar，成平台層統一策略。（見 service mesh，領域 N）

**sharding（分片）**：把大資料集水平切分到多機，每台存一部分；把規模問題換成跨分片協調問題。（見 分片 partition，領域 B）

**SLI / SLO**：SLI＝可靠性的量測指標、SLO＝對它的目標值；兩者把可靠性變成可談判數字，配 error budget。（見 SLI / SLO / error budget，領域 I）

**SNS**：全託管 pub/sub，把一則訊息推給所有訂閱端點（fan-out）；常配 SNS→SQS 做扇出緩衝。（見 SNS，領域 A）

**Socket.io**：架在 WebSocket 之上的即時函式庫，補上 fallback、rooms、自動重連、redis-adapter 等應用層能力（非協定本身）。（見 Socket.io，領域 C）

**SQL vs NoSQL**：本質是資料模型與一致性/擴展取捨之爭，不是查詢語言之爭。（見 SQL vs NoSQL，領域 O）

**SQS**：全託管分散式佇列，pull 模型，靠 visibility timeout 達成至少一次（沒成功刪就重投）。（見 SQS，領域 A）

**SRE（Site Reliability Engineering）**：用軟體工程方法做維運，文化核心是 toil、error budget、SLO-driven 三個互鎖概念。（見 SRE 文化，領域 V）

**SSE（Server-Sent Events）**：基於 HTTP 的單向 server→client 文字串流，比 WebSocket 簡單、自帶斷線重連。（見 SSE / long-poll / WebTransport，領域 C）

**SSI（Serializable Snapshot Isolation）**：PostgreSQL 達成真 serializable 的路線，在快照隔離上偵測危險的讀寫相依環並中止其一。（見 PostgreSQL vs MySQL / 隔離級別與異常，領域 B）

**state machine replication（狀態機複製）**：所有節點對同一指令序列達成共識、按同序套用，使狀態收斂相同。（見 共識 consensus，領域 M）

**sticky session**：負載均衡把同一使用者的連線固定打到同一台 server，是長連線狀態水平擴展的權宜手段。（見 連線狀態與水平擴展，領域 C）

**tail latency（尾延遲）**：延遲分布尾端（p99/p999/max），即使每個元件平均快、整體尾巴仍被放大並主導。（見 tail latency 與長尾，領域 S）

**technical debt（技術債）**：為趕快出貨而寫下「還不太對」的程式碼，像借錢——加速短期但以利息形式拖慢之後（Cunningham 原意是「已理解問題仍選擇寫不完整版」）。（見 技術債管理，領域 T）

**timeout / deadline**：替任何跨行程呼叫設硬上限，超過就放棄、回明確錯誤、把資源還回去；逾時無法區分「慢」與「死」。（見 timeout / deadline / budget / 失敗偵測，領域 P、J）

**TLS 1.3**：當前現役主力（RFC 8446），握手縮到 1-RTT、強制前向保密、只留 AEAD。（見 TLS / mTLS，領域 N）

**token 撤銷**：自包含 token「持有即有效」與「想立刻撤銷」的矛盾，常用短 TTL＋refresh 或 denylist 折衷。（見 token 生命週期與撤銷，領域 F）

**toil（瑣務）**：手動、重複、可自動化、無長期價值的維運工作；SRE 以收斂 toil 為核心指標。（見 SRE 文化，領域 V）

**trace / span**：分散式追蹤把一個請求穿越多服務的因果路徑重建成一棵 span 樹，靠 trace context 跨服務傳播。（見 分散式追蹤，領域 I）

**TrueTime**：Google Spanner 用有界誤差的時鐘區間提供外部一致性的時間機制。（見 邏輯時鐘與排序，領域 M）

**TTL（Time To Live）**：資料/快取項的存活時限，到期主動清除（與記憶體滿時的驅逐不同）。（見 驅逐 eviction / 資料生命週期，領域 G、O）

**12-factor app**：Heroku 2011 整理的雲原生應用十二原則（config 外置、process 無狀態、log 當 stream…）。（見 12-factor app，領域 Q）

**2PC（兩階段提交）**：協調者用 prepare→commit 兩階段讓跨資源交易一起提交或一起回滾；阻塞且有協調者單點。（見 2PC 與分散式交易，領域 M）

## U–Z

**utilization（利用率）與 ρ→1**：佇列延遲隨利用率非線性上升，逼近 100% 時爆炸；故 80% 利用率延遲可能已是 50% 的數倍。（見 排隊直覺，領域 E）

**vector clock（向量時鐘）**：每節點各記一個計數向量，能判斷兩事件是因果先後還是並發（無法比序即衝突）。（見 邏輯時鐘與排序，領域 M）

**visibility timeout**：SQS 訊息被取走後對其他 consumer 隱形的一段時間；沒在內刪掉就重新可見、被重投。（見 SQS，領域 A）

**WAL（Write-Ahead Logging，預寫日誌）**：改資料頁前先把變更順序追加進日誌並落穩，是崩潰恢復與 CDC 的共同基礎。（見 WAL 預寫日誌，領域 O）

**warmup（暖機）**：在真實流量到達前主動把冷啟動的一次性成本付掉，讓首個真實請求落在已熱環境。（見 冷啟動與暖機，領域 S）

**webhook**：伺服器對伺服器的回呼——事件發生時提供方主動對你登記的 URL 發 HTTP POST，把輪詢反轉成通知。（見 webhooks，領域 A）

**WebRTC**：瀏覽器/App 間直傳即時音視訊與資料、不經伺服器中轉媒體；拆媒體/傳輸/信令三塊，多方分 SFU/MCU/mesh。（見 WebRTC，領域 C）

**WebSocket（RFC 6455）**：從 HTTP 升級而來的全雙工長連線協定，握手後脫離 HTTP 語意改用 frame，兩端隨時可送。（見 WebSocket，領域 C）

**WebTransport**：基於 HTTP/3/QUIC 的新雙向傳輸，支援多串流與不可靠資料報，成熟度仍在演進。（見 SSE / long-poll / WebTransport，領域 C）

**write-behind（write-back）**：寫先進快取、非同步回寫底層儲存，吞吐高但崩潰會丟未回寫的資料。（見 快取策略，領域 G）

**write-skew（寫偏斜）**：兩交易各自讀後寫、單獨看都合法但合起來違反不變量的異常；需 serializable 才完全擋。（見 隔離級別與異常，領域 B）

**write-through**：寫同時更新快取與底層儲存，一致性好但每次寫多一跳延遲。（見 快取策略，領域 G）

**YAGNI（You Aren't Gonna Need It）**：源於 Extreme Programming——真的需要時才實作，別為預見可能需要而先做；對抗過度工程。（見 簡單性 vs 過度工程，領域 U）

## 中文索引（無單一對應英文者）

**並發 ≠ 平行**：並發是「結構」（把工作拆成可交錯推進的單元），平行是「執行」（同一瞬間多核一起跑），兩者正交。（見 並發 ≠ 平行，領域 D）

**並發模型比較**：thread / event-loop / actor / coroutine / CSP 五大模型，差別歸結為「共享記憶體 vs 傳訊息」「搶佔 vs 協作讓出」兩軸。（見 並發模型比較，領域 D）

**分散式失敗模型**：partial failure——任一節點/連線/訊息可獨立失敗，且發請求無回應時無法區分「丟了/在處理/回應丟了/掛了」。（見 分散式失敗模型，領域 M）

**分散式鎖**：跨機器無共享記憶體，靠外部協調者（Redis/ZooKeeper/etcd/DB）發放鎖記號達成互斥；正確性須配 fencing token。（見 分散式鎖，領域 M）

**可逆 vs 不可逆決策（one-way / two-way door）**：拆出「反悔的代價」這軸——不可逆決策要慢要多方會診，可逆決策可快、可由小團隊拍板。（見 可逆 vs 不可逆決策，領域 U）

**可觀測性與品質工具地圖**：工具是用來換保證的、且會老化（停維護/改授權/被取代），選型除「能做什麼」更要看「還活著嗎」。（見 可觀測性與品質工具地圖，領域 I）

**失效 · 雪崩 · 穿透 · 擊穿**：四類快取失效災難——大量同時過期（雪崩）、查不存在的鍵繞過快取（穿透）、熱鍵過期瞬間擊穿到 DB。（見 失效 · 雪崩 · 穿透 · 擊穿，領域 G）

**自建 vs 採用**：每加一個相依都是「省自己不寫」換「交出一部分控制權」；判準是「這塊是不是我的核心競爭力」。（見 自建 vs 採用與相依管理，領域 U）

**同步 vs 非同步通訊**：A 呼叫 B 要不要卡住等回應——同步阻塞等結果、非同步發完即走、結果之後回送。（見 同步 vs 非同步通訊，領域 K）

**告警設計**：對「使用者正在受影響的症狀」告警而非「某零件壞了的原因」，症狀少而穩定且自動涵蓋沒想到的故障模式。（見 告警設計，領域 V）

**技術選型**：在資訊不對稱下選一個並承擔維護後果，真正風險常不在「它好不好」而在「它把你綁多深」（退場成本）。（見 技術選型，領域 U）

**資料同步**：把「變更」從一端搬到另一端，差別只在怎麼界定變更、何時搬、搬多少。（見 資料同步總覽，領域 L）

**資料生命週期**：每筆資料該活多久、老了去哪、被「刪除」時到底發生什麼（軟刪除/封存/合規刪除）。（見 資料生命週期，領域 O）

**跨區與異質庫同步**：在 multi-region 高延遲＋隨時分區、且來源與目的地是不同庫的雙重約束下同步，並想清楚實際拿到什麼一致性。（見 跨區與異質庫同步，領域 L）

**慣例的自動化強制**：靠人記憶的慣例會衰減為零，把它從「人的善意」搬到「機器的硬閘」，讓不照做的程式碼進不來。（見 慣例的自動化強制，領域 T）

**衝突解決**：多處獨立更新同一值時決定「最後算誰的」，且須讓所有副本收斂到同一確定結果（LWW/CRDT/應用層合併）。（見 衝突解決，領域 L）

**簡單性 vs 過度工程**：過度工程是替還沒出現的需求預付複雜度（過早抽象、過早最佳化）；用 YAGNI 對抗。（見 簡單性 vs 過度工程，領域 U）

**錯誤處理哲學**：每個會出錯處都要決定「誰知道、哪一層處理、處理到什麼程度」，先分類錯誤再對不同錯誤選 fail-fast 或容錯。（見 錯誤處理哲學，領域 U）

**負載測試**：在真實流量形狀下逼出 p99/p999 長尾與吞吐天花板，而非跑很多次取平均。（見 負載測試，領域 I）

**測試策略**：把有限測試預算分配到各層（單元/整合/端到端），在「真實度 vs 速度穩定」軸上用最低成本買最高信心。（見 測試策略，領域 I）

**無狀態 vs 有狀態**：無狀態實例兩次請求間不持有處理所必需的記憶體狀態，可隨意替換；有狀態則殺掉就丟。（見 無狀態 vs 有狀態，領域 J）

**從 log 算 metric 的陷阱**：聚合正確性取決於樣本完整性，而 log 在高流量下會被取樣/丟/截斷，三者都不保證。（見 從 log 算 metric 的陷阱，領域 I）

**程式碼審查**：表面抓 bug（其實最弱），真正保護的是知識擴散、設計把關與集體所有權。（見 程式碼審查，領域 V）

**分支與發布策略**：規則骨子裡決定整合頻率，而整合頻率直接決定合併衝突有多痛、壞變更多快被發現、發布有多敢頻繁。（見 分支與發布策略，領域 V）

**多層快取與優雅降級**：串多級快取（CDN→行程內→Redis→DB），離請求越近越快越小越易分叉；某層掛了要能退到下一層而非整鏈倒。（見 多層快取與優雅降級，領域 G）

**與 AI 協作的工程工作流**：當寫程式一部分可委派給「會生成但不為結果負責」的協作者時，工作流須重新設計委派/驗收/信任邊界（原理層，不綁工具）。（見 與 AI 協作的工程工作流 / AI 怎麼移動判斷的天平，領域 T、U）

**AI 輔助的大規模變更**：讓 AI 做「單調重複量大但每處判斷淺」的苦工，工作流要防它「製造一千個一致的錯誤」。（見 AI 輔助的大規模變更，領域 T）
