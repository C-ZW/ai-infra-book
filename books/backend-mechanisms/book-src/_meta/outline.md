# 全書大綱《機制之下》（內部文件，非書籍內容）

書名：**《機制之下——後端與分散式系統如何運作、為何如此》**（id `mech`）。
形態：**深讀版敘事技術書**。把姊妹書 `rsys`（《保證與取捨》，速查／概念地圖）的同一批主題，重寫成**可以坐下來讀的敘事章**——一主題一章，太薄／關係太緊的合併。

## 規模

**139 章**（從 `rsys` 的 ~150 個概念衍生，套用 12 處合併）＋ 2 附錄（術語表、延伸閱讀總地圖）。依 8 個 Part 分組。這是一本份量很大的書（DDIA 量級或更大）——使用者明確要的就是這個深度。

> **granularity 定案（2026-06-21 閘）：139 章照拆，一主題一章。** 使用者要的是深度而非更少章；deeper 的標竿（見 style-guide「深度的操作型標準」與 consensus 樣章）會把較薄的主題用真實的 edge case 填成緊湊的一章。**唯一例外**：若某章在 fan-out 時發現真的薄到「不湊字數就撐不起一章」，該 agent 在 flags 標記、留待 P3 與相鄰章合併（不准為湊長度而灌水）。

## 全書脊椎

和 `rsys` 同一條：**你想要什麼保證（guarantee），你願意付什麼取捨（trade-off）。** 差別在呈現——本書用敘事讓取捨「作為故事裡的後果」浮現，不攤成對照表。寫法見 `style-guide.md`。

## Part 結構與順序

沿用 `rsys` 的 reader 分組順序（兩書 Part 對得起來、互為深淺版本）：

- **Part 0 — 兩副透鏡：判斷與推動**（T 推動、U 判斷）
- **Part 1 — 訊息與交付**（A）
- **Part 2 — 資料、一致性與儲存**（B、O、G、L）
- **Part 3 — 連線、網路與 API**（N → C → H → F）
- **Part 4 — 並發、過載與韌性**（D、E、P、S）
- **Part 5 — 分散式系統核心**（M）
- **Part 6 — 架構、雲端與發布**（K、J、Q）
- **Part 7 — 觀測與營運文化**（I、V）

> **結構定案（2026-06-21 閘）：沿用 `rsys`，Part 0（T/U）放最前面。** （曾考慮移到全書最後當反思收尾，使用者選擇沿用。）

---

## 完整章清單

格式：**〈章標題〉**（`slug`）— 涵蓋 `rsys` 主題；敘事角度。檔名用 slug（不帶章號；章號於打包時加）。

### Part 0 — 兩副透鏡：判斷與推動（13 章）

- **推動採用：誘因、轉換成本與信任**（`adoption`）— 推動工具/慣例的採用；top-down vs bottom-up vs 鋪路的張力，含 AI 維度。
- **把決定寫下來：RFC、設計文件與 ADR**（`design-docs`）—〔合併〕RFC／設計文件流程 ＋ 架構決策紀錄 ADR；為什麼把決定寫下來、寫給未來的人看。
- **鋪路：讓對的做法最省力**（`paved-road`）—〔合併〕paved road/golden path ＋ 慣例的自動化強制（linter/formatter/CI gate/codegen）；把「對的做法」變成阻力最小的路。
- **漸進式遷移與淘汰：strangler 與 expand-contract**（`incremental-migration`）— 漸進式遷移與淘汰；怎麼在不停機、不大爆炸下換掉舊東西。
- **技術債：量化、排序、何時還**（`tech-debt`）— 技術債管理；含 AI 維度（AI 能還債也能製造「能跑沒人懂」的債）。
- **與 AI 協作：委派、驗收與信任邊界**（`ai-collaboration`）—〔合併〕與 AI 協作的工程工作流 ＋ AI 輔助的大規模變更；只寫原理層（review gate/信任邊界/驗收），不寫工具品牌。
- **兩扇門：可逆與不可逆決策**（`reversible-decisions`）— 可逆 vs 不可逆（one-way/two-way doors）。
- **簡單性與過度工程：YAGNI 的兩面**（`simplicity`）— 簡單性 vs 過度工程；過早抽象/最佳化的代價。
- **自建還是採用：相依的長期成本**（`build-vs-buy`）— 自建 vs 採用 + 相依管理；NIH vs 過度相依、供應鏈風險。
- **技術選型：評估、PoC 與退場成本**（`tech-selection`）— 技術選型；評估框架與退場成本。
- **錯誤處理哲學：fail-fast、傳播、重試還是降級**（`error-philosophy`）— 錯誤處理哲學；錯誤分類與該往哪走。
- **信封背面：量級估算與容量直覺**（`capacity-estimation`）— 量級估算與容量直覺；IOPS/記憶體/頻寬天花板的快速判斷。
- **AI 怎麼移動判斷的天平**（`ai-judgment`）— AI 怎麼移動判斷的天平；自建成本↓、過度工程變便宜、「能跑沒人懂」的新風險。

### Part 1 — 訊息與交付（14 章）

- **三種交付語意：at-most、at-least、exactly-once**（`delivery-semantics`）—〔合併〕交付語意三選一 ＋ exactly-once 的真相；交付不可能 exactly-once、處理＝at-least＋去重。
- **重複是常態：冪等與去重**（`idempotency-dedup`）—〔合併〕at-least-once 與重複處理 ＋ 冪等 ＋ 去重；本章 **owns 冪等**（定義/冪等鍵生命週期/client vs server）。
- **訊息順序：FIFO 與 partition key**（`message-ordering`）— 訊息順序。
- **重試、退避與 jitter**（`retry-backoff`）— 重試、退避、jitter；本章 **owns 重試做法**。
- **死信與毒訊息：DLQ**（`dlq`）— DLQ 死信與毒訊息。
- **跨服務的交付一致：outbox 與 saga**（`outbox-saga`）— outbox/saga；本章 **owns outbox 機制**，含 choreography vs orchestration。
- **Webhooks：伺服器對伺服器的回呼**（`webhooks`）— webhooks；交付/重試/簽章/冪等。
- **序列化與 schema 演進**（`schema-evolution`）— 序列化與 schema 演進；本章 **owns 協定相容/Protobuf**（向前後相容、schema registry）。
- **SQS：Standard 與 FIFO**（`sqs`）— SQS。
- **SNS：fan-out 與 SNS→SQS**（`sns`）— SNS。
- **Kafka：log、partition 與 consumer group**（`kafka`）— Kafka；log 天然支援 event sourcing（見〈Event sourcing 與 CQRS〉）。
- **RabbitMQ：exchange、routing 與 confirms**（`rabbitmq`）— RabbitMQ。
- **BullMQ：Redis 上的延遲與工作佇列**（`bullmq`）— Bull/BullMQ。
- **Redis Pub/Sub 與 Streams：交付語意的取捨**（`redis-pubsub-streams`）— Redis Pub/Sub vs Streams；Redis 內部機制見〈Redis 的內部〉。

### Part 2 — 資料、一致性與儲存（28 章）

**B 一致性與交易（12 章）**
- **一致性光譜：線性、因果、讀己之寫、最終一致**（`consistency-spectrum`）—〔吸收〕最終一致·補償的一致性模型面；對帳機制指向〈對帳〉。
- **隔離級別與異常：dirty、phantom 到 write-skew**（`isolation-levels`）— 隔離級別與異常。
- **MVCC：讓讀不擋寫**（`mvcc`）— MVCC。
- **鎖與死結：行鎖、gap、next-key 與 wait-for graph**（`locks-deadlock`）— 鎖與死結。
- **樂觀與悲觀並發控制：CAS、版本與 ETag**（`optimistic-pessimistic`）— 樂觀 vs 悲觀並發控制；冪等定義見〈重複是常態〉。
- **複製延遲與讀己之寫**（`replication-lag`）— 複製延遲與讀己之寫；複製策略機制見〈複製策略〉。
- **分片：水平切分與路由**（`sharding`）— 分片；路由與 consistent hashing 的關係指向〈consistent hashing〉。
- **一致性與交易的保證模型：ACID、BASE、CAP、PACELC**（`guarantee-models`）—〔合併〕CAP/PACELC ＋ ACID vs BASE。
- **索引與查詢計畫：B-tree、覆蓋索引與 planner**（`indexes-query-plan`）— 索引與查詢計畫。
- **多租戶隔離：row、schema、db-per-tenant**（`multitenancy`）— 多租戶隔離。
- **零停機 schema 遷移：expand-contract 與 backfill**（`zero-downtime-migration`）— 零停機 schema 遷移；本章 **owns DB 結構變更**，協定相容見〈序列化與 schema 演進〉。
- **PostgreSQL 與 MySQL：兩種隔離哲學**（`postgres-vs-mysql`）— PostgreSQL vs MySQL；SSI vs next-key 的本質差。

**O 儲存引擎與資料模型（5 章）**
- **LSM-tree 與 B-tree：寫放大換讀放大**（`lsm-vs-btree`）— LSM-tree vs B-tree。
- **WAL：先寫日誌，再改資料**（`wal`）— WAL 預寫日誌。
- **SQL 與 NoSQL：資料模型各擅其場**（`sql-vs-nosql`）— SQL vs NoSQL。
- **倒排索引：全文搜尋的資料結構**（`inverted-index`）— 全文搜尋·inverted index（只講資料結構與機制，不碰相關度排序）。
- **資料的生命週期：retention、TTL、軟刪除與合規刪除**（`data-lifecycle`）— 資料生命週期。

**G 快取與儲存（5 章）**
- **快取策略：cache-aside、write-through、write-behind**（`cache-strategies`）—〔吸收〕多層快取與優雅降級（快取層降級，通用 fallback 見〈fallback 與降級〉）。
- **快取的失效災難：雪崩、穿透、擊穿**（`cache-failures`）— 失效·雪崩·穿透·擊穿。
- **驅逐：LRU、LFU、TTL 與 LRM**（`eviction`）— 驅逐 eviction。
- **Redis 的內部：單執行緒、I/O threads、持久化與多重角色**（`redis-internals`）—〔合併〕Redis[工] ＋ 持久化（RDB vs AOF）；本章 **owns Redis 內部**。
- **物件儲存：S3 與大 payload 的交接**（`object-storage`）— S3/物件儲存。

**L 資料同步與整合（6 章）**
- **資料同步的全景：full/incremental、push/pull、batch/streaming**（`data-sync-overview`）— 資料同步總覽。
- **CDC：從資料庫變更長出事件流**（`cdc`）— CDC；引〈Event sourcing 與 CQRS〉。
- **dual-write 問題與 event-carried state transfer**（`dual-write`）— dual-write→outbox；outbox 機制見〈跨服務的交付一致〉，event notification vs state transfer 見〈事件驅動架構〉。
- **衝突解決：LWW、版本向量與 CRDT**（`conflict-resolution`）— 衝突解決；本章 **owns 衝突解決**（state-based vs op-based 收斂）。
- **對帳：怎麼確認兩邊一致、漂移怎麼修**（`reconciliation`）— 對帳 reconciliation；本章 **owns 對帳**。
- **跨區與異質庫同步**（`cross-region-sync`）— multi-region、PG↔MySQL 類。

### Part 3 — 連線、網路與 API（22 章）

**N 網路與協定（7 章）**
- **HTTP/1.1、HTTP/2、HTTP/3：keep-alive、多工與 QUIC**（`http-versions`）— HTTP 三版。
- **gRPC 與 Protobuf：用 IDL 定義服務**（`grpc-protobuf`）— gRPC/Protobuf；Protobuf 相容性見〈序列化與 schema 演進〉，本章只講 gRPC 怎麼用它當 IDL＋傳輸。
- **連線池：為什麼不每次都重開連線**（`connection-pool`）— 連線池；本章 **owns 連線池機制**，調參見〈連線池調校〉。
- **負載均衡：L4 與 L7、演算法與健康檢查**（`load-balancing`）— 負載均衡；本章 **owns LB 機制**。
- **TLS 與 mTLS：握手與憑證管理**（`tls-mtls`）— TLS/mTLS。
- **DNS 與服務發現**（`dns-service-discovery`）— DNS·服務發現。
- **Service mesh：把網路關注點下沉到 sidecar**（`service-mesh`）— service mesh（sidecar/Envoy）。

**C 即時傳輸（5 章）**
- **server→client 推送的全景：推還是拉**（`push-overview`）— server→client 推送全景。
- **WebSocket：frame、ping-pong 與水平擴展**（`websocket`）—〔合併〕WebSocket[工] ＋ 連線狀態與水平擴展（sticky session/backplane）。
- **SSE、long-poll 與 WebTransport**（`sse-webtransport`）— SSE/long-poll/WebTransport 對照。
- **Socket.io：fallback、rooms 與 redis-adapter**（`socketio`）— Socket.io。
- **WebRTC：媒體、傳輸與信令**（`webrtc`）— WebRTC（SFU vs MCU vs mesh）。

**H API 與閘道（5 章）**
- **REST 設計、版本化與 OpenAPI 契約**（`rest-design`）— REST 設計·版本化·OpenAPI。
- **分頁：offset 與 cursor/keyset、深分頁**（`pagination`）— 分頁。
- **REST、GraphQL 與 gRPC：三種 API 範式**（`api-paradigms`）— API 範式對照。
- **API gateway 的角色：authz、限流、轉換與聚合**（`api-gateway-role`）— API gateway 角色；限流機制見〈rate limiting〉、LB 見〈負載均衡〉。
- **API 閘道對照：ALB、API Gateway、KrakenD、Kong**（`gateway-comparison`）— 閘道[工]。

**F 身分與存取（5 章）**
- **認證與授權：AuthN、AuthZ 與 OIDC 的位置**（`authn-authz`）— 認證 vs 授權。
- **token 的生命週期與撤銷**（`token-lifecycle`）— token 生命週期與撤銷（短 TTL+refresh/denylist）。
- **JWT 與簽章：結構、HS256/RS256 與 JWKS**（`jwt-signing`）—〔合併〕對稱 vs 非對稱簽章 ＋ JWT[工]；簽章不是加密。
- **RBAC 與 ABAC：兩種授權模型**（`rbac-abac`）— RBAC vs ABAC。
- **OAuth2、OIDC 與 OAuth 2.1：grant 類型與現況**（`oauth-oidc`）— OAuth2/OIDC/OAuth 2.1。

### Part 4 — 並發、過載與韌性（22 章）

**D 並發與執行模型（6 章）**
- **並發不是平行：兩個常被混用的詞**（`concurrency-vs-parallelism`）— 並發 ≠ 平行。
- **event loop：單執行緒怎麼同時做很多事**（`event-loop`）— event loop（libuv 相位）。
- **阻塞與非阻塞 I/O**（`blocking-io`）— 阻塞 vs 非阻塞 I/O。
- **thread pool 與 worker threads：CPU 密集怎麼辦**（`thread-pool`）— thread pool/worker threads。
- **race condition 與原子性：跨 DB、cache、runtime**（`race-condition`）— race condition·原子性。
- **並發模型比較：thread、event-loop、actor、coroutine、CSP**（`concurrency-models`）— 並發模型比較。

**E 過載與流量控制（6 章）**
- **背壓：當下游跟不上**（`backpressure`）— 背壓；本章 **owns 背壓**。
- **rate limiting：token bucket、leaky bucket 與分散式限流**（`rate-limiting`）— rate limiting；本章 **owns 限流**（含分散式計數同步）。
- **load shedding：主動丟掉一部分流量**（`load-shedding`）— load shedding。
- **circuit breaker：三態與半開試探**（`circuit-breaker`）— circuit breaker；本章 **owns 三態機制**。
- **retry storm 與 metastable failure**（`retry-storm`）— retry storm·metastable；放大機制，重試做法見〈重試、退避與 jitter〉。
- **排隊的直覺：為什麼利用率逼近 1 會爆炸**（`queueing-intuition`）— 排隊直覺（utilization、ρ→1；自足講到直覺夠用）。

**P 韌性與容錯（5 章）**
- **timeout、deadline 與 budget：把等待變成有界**（`timeout-budget`）— timeout/deadline/budget。
- **bulkhead：艙壁隔離**（`bulkhead`）— bulkhead。
- **health check：liveness 與 readiness**（`health-check`）— health check；本章 **owns health check**。
- **graceful shutdown：怎麼好好地關掉一個行程**（`graceful-shutdown`）— graceful shutdown。
- **fallback 與降級：壞掉時退到哪**（`fallback`）— fallback·降級；本章 **owns fallback**，觸發機制 circuit breaker 見〈circuit breaker〉。

**S 效能與延遲（5 章）**
- **冷啟動與暖機：第一個請求為什麼那麼慢**（`cold-start`）— 冷啟動與暖機；本章 **owns 冷啟動**，Lambda 特有的 SnapStart 見〈Lambda〉。
- **長尾延遲：p99 從哪裡來**（`tail-latency`）— tail latency（成因機制，非觀測）。
- **N+1 查詢：一個迴圈打爆資料庫**（`n-plus-one`）— N+1 查詢。
- **批次、coalescing 與 debounce**（`batching-coalescing`）— 批次/coalescing/debounce。
- **連線池調校**（`pool-tuning`）— 連線池調校；機制見〈連線池〉，本章只講調參/監控。

### Part 5 — 分散式系統核心（11 章）

- **為什麼分散式這麼難：partial failure 與失敗模型**（`partial-failure`）— 分散式失敗模型；M 的第一原理錨點。
- **共識：讓一群會當機的機器同意一件事**（`consensus`）— 共識（Raft/Paxos、replicated log）。**← P1 樣章（深度標竿）。**
- **leader election：選出唯一的寫入點**（`leader-election`）— leader election。
- **分散式鎖：Redlock、fencing token 與「鎖其實是租約」**（`distributed-lock`）— 分散式鎖；本章 **owns fencing**。
- **quorum：R + W > N 的鴿巢原理**（`quorum`）— quorum。
- **邏輯時鐘與排序：Lamport、向量時鐘、HLC 與 TrueTime**（`logical-clocks`）— 邏輯時鐘與排序；本章 **owns 時鐘/排序**。
- **複製策略：單主、多主、無主**（`replication-strategies`）— 複製策略；本章 **owns 複製範式**，一致性後果見〈複製延遲與讀己之寫〉。
- **2PC 與分散式交易：原子提交與它的阻塞代價**（`two-phase-commit`）— 2PC 與分散式交易。
- **consistent hashing：節點進出時少搬一點資料**（`consistent-hashing`）— consistent hashing；本章 **owns consistent hashing**。
- **gossip 與 anti-entropy**（`gossip-anti-entropy`）— gossip/anti-entropy。
- **時間與日期：UTC、epoch、timezone 與 DST 的應用層坑**（`time-and-dates`）— 時間與日期處理。

### Part 6 — 架構、雲端與發布（15 章）

**K 系統設計與解耦（5 章）**
- **解耦：時間、空間、同步性、資料、實作五種耦合**（`decoupling`）—〔合併〕解耦 ＋ 耦合 vs 內聚。
- **同步與非同步通訊**（`sync-vs-async`）— 同步 vs 非同步通訊。
- **事件驅動架構：event notification 與 event-carried state transfer**（`event-driven`）— EDA；本章 **owns 兩種事件風格**。
- **Event sourcing 與 CQRS：狀態是不可變事件序列**（`event-sourcing-cqrs`）— Event sourcing 與 CQRS；本章 **owns ES/CQRS**，引〈CDC〉〈一致性光譜〉。
- **durable execution：Temporal、Step Functions 與長流程**（`durable-execution`）— 持久化工作流；vs saga 補償（見〈跨服務的交付一致〉）。

**J 雲端與編排原語（4 章）**
- **無狀態與有狀態：為什麼 serverless 要無狀態**（`stateless-stateful`）— 無狀態 vs 有狀態。
- **Lambda：冷啟動、SnapStart、payload 與併發**（`lambda`）— Lambda[工]；通用冷啟動見〈冷啟動與暖機〉。
- **K8s CronJob：schedule、concurrencyPolicy 與「不是 exactly-once」**（`cronjob`）—〔合併〕CronJob[工] ＋ 時間與排程（單調鐘 vs 牆鐘、漏跑/補跑）。
- **失敗偵測：逾時是唯一手段、慢與死分不開**（`failure-detection`）— 失敗偵測；第一原理見〈為什麼分散式這麼難〉。

**Q 部署與發布（6 章）**
- **blue-green、canary 與 rolling**（`deployment-strategies`）— 發布策略。
- **Docker：容器隔離的原理**（`docker`）— Docker[工]（namespace/cgroup/seccomp）。
- **Kubernetes：Pod、Service、HPA 與調度**（`kubernetes`）— K8s[工] 核心物件；probe 設定語意引〈health check〉。
- **IaC：宣告式、漂移與冪等 apply**（`iac`）— IaC；冪等定義見〈重複是常態〉。
- **12-factor：哪些在容器/serverless 時代仍成立**（`twelve-factor`）— 12-factor app。
- **config 與機密管理**（`config-secrets`）— config 與機密管理。

### Part 7 — 觀測與營運文化（14 章）

**I 可觀測性與品質（9 章）**
- **三本柱：metric、log 與 trace**（`three-pillars`）— 三本柱；trace 機制深講見〈分散式追蹤〉。
- **從 log 算 metric 的陷阱：取樣、遺漏與視窗**（`log-to-metric`）— 從 log 算 metric。
- **cardinality 爆炸：一個 label 如何拖垮監控**（`cardinality`）— cardinality 爆炸。
- **SLI、SLO 與 error budget：p99 與 p999**（`sli-slo`）— SLI/SLO/error budget；error budget 當談判工具見〈SRE 文化〉。
- **告警設計：症狀 vs 原因、告警疲勞**（`alerting`）— 告警設計。
- **負載測試：開放與封閉模型、coordinated omission**（`load-testing`）— 負載測試。
- **分散式追蹤：trace context 傳播、span 與取樣**（`distributed-tracing`）— 分散式追蹤。
- **測試策略：unit、integration、contract、e2e**（`testing-strategy`）— 測試策略（含 contract testing）。
- **可觀測性與品質工具地圖**（`quality-tooling`）— 工具地圖（FluentBit/Clinic.js/k6/Vegeta/Snyk 定位與現況）。

**V 營運與事故文化（5 章）**
- **事故應變與無咎事後檢討**（`incident-response`）— incident response、blameless postmortem、runbook。
- **SRE 文化：toil、error budget 當談判工具**（`sre-culture`）— SRE 文化。
- **DORA 四指標**（`dora-metrics`）— deploy frequency/lead time/MTTR/change failure rate。
- **程式碼審查：審什麼、它在保護什麼**（`code-review`）— 程式碼審查。
- **分支與發布策略：trunk-based vs git-flow**（`branching-strategy`）— 分支與發布策略，配 CD。

---

## 12 處合併決定（彙整）

1. 交付語意三選一 ＋ exactly-once 的真相 → 〈三種交付語意〉
2. at-least-once 與重複處理 ＋ 冪等 ＋ 去重 → 〈重複是常態〉
3. CAP/PACELC ＋ ACID vs BASE → 〈一致性與交易的保證模型〉
4. Redis[工] ＋ 持久化（RDB/AOF）→ 〈Redis 的內部〉
5. 快取策略 ＋ 多層快取與優雅降級 → 〈快取策略〉
6. WebSocket[工] ＋ 連線狀態與水平擴展 → 〈WebSocket〉
7. 對稱 vs 非對稱簽章 ＋ JWT[工] → 〈JWT 與簽章〉
8. RFC/設計文件 ＋ ADR → 〈把決定寫下來〉
9. paved road ＋ 慣例自動化強制 → 〈鋪路〉
10. 與 AI 協作工作流 ＋ AI 輔助大規模變更 → 〈與 AI 協作〉
11. 解耦 ＋ 耦合 vs 內聚 → 〈解耦〉
12. CronJob[工] ＋ 時間與排程 → 〈K8s CronJob〉

另有 2 處「吸收」（不算獨立合併）：B「最終一致·補償·對帳」的一致性模型面吸收進〈一致性光譜〉（對帳機制歸 L）；同理 G「多層快取」吸收進〈快取策略〉。

## owning 章（章內去重；只在本書內、不跨書）

同一機制只在 owning 章深講一次；別章需要時給最小說明＋「（見〈章名〉）」。深讀書比 `rsys` 寬鬆：別章可為敘事完整**簡述**，但不重講整套推導。

| 機制 | owning 章 | 別章只引用 |
|---|---|---|
| 冪等 | 〈重複是常態〉 | 〈樂觀與悲觀並發控制〉〈分散式鎖〉〈2PC〉〈IaC〉 |
| 重試做法 | 〈重試、退避與 jitter〉 | 〈retry storm〉〈timeout、deadline 與 budget〉 |
| outbox | 〈跨服務的交付一致〉 | 〈dual-write 問題〉〈durable execution〉 |
| 協定相容/Protobuf | 〈序列化與 schema 演進〉 | 〈gRPC 與 Protobuf〉 |
| DB 結構變更 | 〈零停機 schema 遷移〉 | 〈序列化與 schema 演進〉（互引） |
| 對帳 | 〈對帳〉 | 〈一致性光譜〉 |
| 衝突解決 | 〈衝突解決〉 | 〈複製策略〉 |
| 連線池 | 〈連線池〉 | 〈連線池調校〉 |
| 負載均衡 | 〈負載均衡〉 | 〈API 閘道對照〉〈API gateway 的角色〉 |
| 複製/分片範式 | 〈複製策略〉〈consistent hashing〉 | 〈複製延遲與讀己之寫〉〈分片〉 |
| 時鐘/邏輯排序 | 〈邏輯時鐘與排序〉 | 〈K8s CronJob〉〈時間與日期〉（應用層面另講） |
| rate limiting | 〈rate limiting〉 | 〈API gateway 的角色〉 |
| circuit breaker | 〈circuit breaker〉 | 〈fallback 與降級〉 |
| fallback | 〈fallback 與降級〉 | 〈快取策略〉 |
| health check | 〈health check〉 | 〈失敗偵測〉〈Kubernetes〉 |
| 冷啟動 | 〈冷啟動與暖機〉 | 〈Lambda〉 |
| 背壓 | 〈背壓〉 | 〈rate limiting〉〈排隊的直覺〉 |
| event sourcing/CQRS | 〈Event sourcing 與 CQRS〉 | 〈Kafka〉〈CDC〉 |
| 兩種事件風格 | 〈事件驅動架構〉 | 〈dual-write 問題〉 |
| Redis 內部 | 〈Redis 的內部〉 | 〈Redis Pub/Sub 與 Streams〉〈BullMQ〉〈分散式鎖〉（Redlock） |
| fencing | 〈分散式鎖〉 | 〈leader election〉 |
| partial failure | 〈為什麼分散式這麼難〉 | 〈失敗偵測〉〈共識〉 |

## 全域不涵蓋（沿用 `rsys`，任何章都不展開）

- **特定應用域**：feed/timeline 設計、推薦/搜尋排序、串流處理、資料湖/倉、向量資料庫、ML serving、邊緣運算。
- **範圍外**：前端/行動端/UI、DevOps 工具鏈品牌操作、特定雲廠牌 console 操作、敏捷/Scrum 流程、估點方法論、職涯階梯/招募/績效。
- **資安只收交界**：TLS/mTLS（N）、config/secrets（Q）、JWT/OAuth/RBAC（F）在內；加密演算法內部、注入/XSS/CSRF、KMS/HSM 進階、滲透測試不收。
- **絕對禁止**（見 style-guide）：作者個人系統/履歷、糾錯口吻、指向其他書（含 `rsys`）、練習段、AI 工具版本。

## 附錄（全章寫完後編）

- `appendix-a-glossary.md` — 術語表（從實際寫出的章彙整）。
- `appendix-b-reading-map.md` — 延伸閱讀總地圖（各章外部連結匯整，僅外部來源）。

> `rsys` 有的「保證速查表」附錄**本書不做**——那正是 `rsys` 的形態，本書是敘事版。

## 檔案與打包

- 一章一檔，檔名 `<slug>.md`（上表的 slug），h1＝章標題。
- reader 分組順序（`web/book.config.json`）：Part 0→7，groups 標題＝Part 名；章號於打包時加在 doc 標題（如「第 12 章 · 共識」）。
- id `mech`（全域唯一，登記簿 `../../../profile/books.json`）。
