# 全書大綱（內部文件，非書籍內容）

書名：《保證與取捨——後端與分散式系統的概念地圖》
形態：**通用資深後端概念參考書**。約 **150 條目 / 22 領域 / 8 個 Part**。純觀念，無練習。每條照 `style-guide.md` 的五段模板；自足、不指向其他書；不提任何作者個人系統。

> **改版說明**：取代舊個人書（`chNN-*.md` 作廢）。每個**領域**＝一個檔（大領域可切 2 檔）；每個概念是檔內一個 `##`。

## 全書脊椎

每一條都在回答同一件事：**你想要什麼保證（guarantee），你願意付什麼取捨（trade-off）。** 五段模板把它拆成：定義 → 解法空間 → 各方案的保證與取捨 → 何時需要 → 常見誤解與陷阱。

## 兩副透鏡（Part 0 前置）

T（推動）與 U（判斷）放最前面，當讀全書的眼鏡：讀每條技術概念時，同時想「我會怎麼**判斷/選**它（U）＋怎麼讓**團隊採用**它（T）」。T/U 並融入「與 AI 協作」維度（原理層，見 style-guide）。

---

## 完整 TOC

標記：`[問]`＝問題條目（五段：定義/解法空間/保證對照/何時需要/誤解陷阱）；`[工]`＝工具條目（五段：是什麼機制/用法地圖/保證限制/替代取捨/誤解陷阱）。

### Part 0 — 透鏡：怎麼判斷、怎麼推動

**T 工程實踐與團隊推動**（檔 `T-driving-adoption.md`）
- `[問]` 推動工具/慣例的採用（誘因、轉換成本、信任；top-down vs bottom-up vs 鋪路；含 AI 維度）
- `[問]` RFC／設計文件流程
- `[問]` 鋪路 paved road／golden path（讓對的做法＝最省力）
- `[問]` 慣例的自動化強制（linter/formatter/CI gate/codegen）
- `[問]` 漸進式遷移與淘汰（strangler、expand-contract 用在流程、退役舊東西）
- `[問]` 架構決策紀錄 ADR
- `[問]` 技術債管理（量化、排序、何時還/何時忍；含 AI 維度）
- `[問]` **與 AI 協作的工程工作流**（什麼交給 AI、review gate、信任邊界、驗收）
- `[問]` **AI 輔助的大規模變更**（codemod/遷移/重構：AI 做苦工、人定方向與驗收）

**U 工程判斷與決策**（檔 `U-judgment.md`）
- `[問]` 可逆 vs 不可逆決策（one-way / two-way doors）
- `[問]` 自建 vs 採用 + 相依管理（何時加 dependency、供應鏈風險、NIH vs 過度相依）
- `[問]` 簡單性 vs 過度工程（YAGNI、過早抽象/最佳化）
- `[問]` 技術選型（評估框架、PoC、退場成本）
- `[問]` 錯誤處理哲學（fail-fast vs 韌性、錯誤分類、重試 vs 傳播 vs 降級）
- `[問]` **AI 怎麼移動判斷的天平**（自建成本↓、過度工程變便宜、「能跑沒人懂」的新風險）
- `[問]` 量級估算與容量直覺（back-of-envelope：IOPS/記憶體/頻寬天花板；快速判斷要不要 cache/分片）

### Part 1 — 訊息、交付與整合

**A 訊息交付與佇列**（檔可切 `A1-delivery-semantics.md` / `A2-messaging-tools.md`）
- `[問]` 交付語意三選一（at-most / at-least / exactly-once 全景＋何時要哪個）
- `[問]` at-least-once 與重複處理（解法空間：冪等/去重/可重放…）
- `[問]` exactly-once 的真相（交付不可能、處理＝at-least+去重）
- `[問]` 冪等 idempotency（含冪等鍵生命週期、client vs server 負責、TTL）
- `[問]` 去重 dedup（key / window / store）
- `[問]` 訊息順序 ordering（FIFO / partition key）
- `[問]` 重試、退避、jitter
- `[問]` DLQ 死信與毒訊息
- `[問]` outbox / saga（跨服務交付一致；含 choreography vs orchestration 取捨）
- `[問]` webhooks（伺服器對伺服器回呼：交付/重試/簽章/冪等）
- `[問]` 序列化與 schema 演進（JSON/Protobuf/Avro、向前後相容、schema registry）
- `[工]` SQS（Standard vs FIFO、visibility timeout）
- `[工]` SNS（fan-out、SNS→SQS）
- `[工]` Kafka（log/partition/consumer group/EOS）
- `[工]` RabbitMQ（exchange/routing/ack/confirms）
- `[工]` Bull / BullMQ（Redis-backed delayed/job queue）
- `[問]` Redis Pub/Sub vs Streams（發布訂閱 vs 持久化流的交付取捨；內部機制見 G 的 Redis）

**L 資料同步與整合**（檔 `L-data-sync.md`）
- `[問]` 資料同步總覽（full vs incremental、push vs pull、batch vs streaming）
- `[問]` CDC 變更資料擷取
- `[問]` dual-write 問題 → outbox / event-carried state transfer
- `[問]` 衝突解決（LWW / 版本向量 / CRDT——CRDT 講到 state-based vs op-based 收斂語意）
- `[問]` 對帳 reconciliation（怎麼確認兩邊一致、漂移怎麼修）
- `[問]` 跨區 / 異質庫同步（multi-region、PG↔MySQL 類）

### Part 2 — 資料、一致性與儲存

**B 資料一致性與交易**（檔可切 `B1-consistency-isolation.md` / `B2-replication-cap.md`）
- `[問]` 一致性光譜（線性 / 因果 / 讀己之寫 / 最終一致）
- `[問]` 隔離級別與異常（dirty / non-repeatable / phantom / write-skew）
- `[問]` MVCC
- `[問]` 鎖與死結（行/gap/next-key、wait-for graph）
- `[問]` 樂觀 vs 悲觀並發控制（CAS、version/ETag、conditional request）
- `[問]` 複製延遲與讀己之寫（read replica）
- `[問]` 分片 partition（水平切分、路由）
- `[問]` 最終一致 · 補償 · 對帳
- `[問]` CAP / PACELC
- `[問]` ACID vs BASE（交易/一致性保證模型；與 CAP/PACELC 同層）
- `[問]` 索引與查詢計畫（B-tree、覆蓋/複合索引、計畫）
- `[問]` 多租戶隔離（row / schema / db-per-tenant）
- `[問]` 零停機 schema 遷移（expand-contract、遷移期 dual-write、backfill；加欄位/改型別/拆表怎麼不停機；與 A 的「序列化與 schema 演進」分工：那條講線上協定相容、這條講資料庫結構變更，並與 Q 的部署協調呼應）
- `[工]` PostgreSQL vs MySQL（隔離預設、SSI vs next-key 的本質差）

**O 儲存引擎與資料模型**（檔 `O-storage-engines.md`）
- `[問]` LSM-tree vs B-tree（寫放大 vs 讀放大）
- `[問]` WAL 預寫日誌
- `[問]` SQL vs NoSQL（文件/KV/寬欄/圖/時序各擅場）
- `[問]` 全文搜尋 · inverted index（只講 inverted index 資料結構與機制；相關度排序屬已排除的搜尋域）
- `[問]` 資料生命週期（retention / TTL / 封存 / 軟刪除 / 合規刪除）

**G 快取與儲存**（檔 `G-caching.md`）
- `[問]` 快取策略（cache-aside / write-through / write-behind）
- `[問]` 失效 · 雪崩 · 穿透 · 擊穿
- `[問]` 驅逐 eviction（LRU/LFU/TTL/LRM…）
- `[問]` 持久化（RDB vs AOF、fsync 取捨）
- `[問]` 多層快取與優雅降級
- `[工]` Redis（單執行緒內幕、io-threads、授權/Valkey；cache/lock/queue/pubsub/leaderboard/rate-limit 多重角色）
- `[工]` S3 / 物件儲存（資料交接、大 payload offload）

### Part 3 — 連線、網路與 API

**C 即時傳輸**（檔 `C-realtime-transport.md`）
- `[問]` server→client 推送全景（推 vs 拉）
- `[問]` 連線狀態與水平擴展（sticky session / backplane）
- `[工]` WebSocket（frame/ping-pong/RFC 6455）
- `[工]` SSE / long-poll / WebTransport（對照）
- `[工]` Socket.io（fallback/rooms/redis-adapter）
- `[工]` WebRTC（媒體/傳輸/信令三塊；SFU vs MCU vs mesh）

**N 網路與協定**（檔 `N-network-protocols.md`）
- `[問]` HTTP/1.1 · 2 · 3（keep-alive/多工/QUIC）
- `[工]` gRPC / Protobuf
- `[問]` 連線池 connection pool
- `[問]` 負載均衡 L4 vs L7（演算法/健康檢查）
- `[問]` TLS / mTLS（握手、憑證管理）
- `[問]` DNS · 服務發現 service discovery
- `[問]` service mesh（sidecar / Envoy）

**H API 與閘道**（檔 `H-api-gateway.md`）
- `[問]` REST 設計 · 版本化 · OpenAPI 契約
- `[問]` 分頁 pagination（offset vs cursor/keyset、深分頁）
- `[問]` API 範式對照 REST vs GraphQL vs gRPC
- `[問]` API gateway 的角色（authz/限流/轉換/聚合）
- `[工]` ALB vs API Gateway vs KrakenD vs Kong

**F 身分與存取**（檔 `F-identity-access.md`）
- `[問]` 認證 vs 授權（AuthN vs AuthZ；OIDC 在哪一塊）
- `[問]` token 生命週期與撤銷（短 TTL + refresh / denylist）
- `[問]` 對稱 vs 非對稱簽章（HS256 / RS256 / JWKS）
- `[問]` RBAC vs ABAC
- `[工]` JWT（結構、簽非加密）
- `[工]` OAuth2 / OIDC / OAuth 2.1（grant 類型、現況）

### Part 4 — 並發、過載與韌性

**D 並發與執行模型**（檔 `D-concurrency.md`）
- `[問]` 並發 ≠ 平行
- `[問]` event loop（單執行緒並發、libuv 相位）
- `[問]` 阻塞 vs 非阻塞 I/O
- `[問]` thread pool / worker threads（CPU 密集怎麼辦）
- `[問]` race condition · 原子性（跨 DB/cache/runtime）
- `[問]` 並發模型比較（thread / event-loop / actor / coroutine / CSP 的取捨）

**E 過載與流量控制**（檔 `E-overload.md`）
- `[問]` 背壓 backpressure（有界佇列/阻塞/丟棄）
- `[問]` rate limiting（token bucket vs leaky bucket；含分散式限流：多節點計數同步、中央 vs 本地）
- `[問]` load shedding
- `[問]` circuit breaker（三態）
- `[問]` retry storm · metastable failure
- `[問]` 排隊直覺（utilization、為什麼 ρ→1 爆炸——本書自足講到直覺夠用）

**P 韌性與容錯**（檔 `P-resilience.md`）
- `[問]` timeout / deadline / budget
- `[問]` bulkhead 艙壁隔離
- `[問]` health check（liveness / readiness）
- `[問]` graceful shutdown
- `[問]` fallback · 降級

**S 效能與延遲**（檔 `S-performance.md`）
- `[問]` 冷啟動與暖機 cold start & warmup
- `[問]` tail latency 與長尾（成因機制，非觀測）
- `[問]` N+1 查詢
- `[問]` 批次 / coalescing / debounce
- `[問]` 連線池調校

### Part 5 — 分散式系統核心

**M 分散式系統核心**（檔可切 `M1-consensus-replication.md` / `M2-coordination-time.md`）
- `[問]` 分散式失敗模型（partial failure；crash-stop / crash-recovery / Byzantine；為什麼 partial failure 比 fail-stop 難——M 的第一原理錨點）
- `[問]` 共識 consensus（Raft / Paxos、replicated log）
- `[問]` leader election
- `[問]` 分散式鎖（Redlock / fencing token）
- `[問]` quorum（R+W>N）
- `[問]` 邏輯時鐘與排序（Lamport / vector / HLC / TrueTime）
- `[問]` 複製策略（單主 / 多主 / 無主 Dynamo 式）
- `[問]` 2PC 與分散式交易
- `[問]` consistent hashing
- `[問]` gossip / anti-entropy
- `[問]` 時間與日期處理（UTC / epoch / timezone / DST 的應用層坑）

### Part 6 — 架構、雲端與發布

**K 系統設計與解耦**（檔 `K-decoupling.md`）
- `[問]` 解耦 decoupling（時間/空間/同步性/資料/實作耦合；各手段解哪種）
- `[問]` 耦合 vs 內聚
- `[問]` 同步 vs 非同步通訊
- `[問]` 事件驅動架構 EDA（事件作為通訊：event notification vs event-carried state transfer）
- `[問]` Event sourcing 與 CQRS（狀態＝不可變事件序列、讀寫分離；引 L 的 CDC、B 的一致性）
- `[問]` 持久化工作流與 durable execution（Temporal/Step Functions：長流程狀態持久化以便重試/恢復；vs saga 的補償邏輯）

**J 雲端與編排原語**（檔 `J-cloud-primitives.md`）
- `[工]` Lambda（冷啟動/SnapStart/payload/併發）
- `[問]` 無狀態 vs 有狀態（為什麼 serverless 要無狀態；「持久化是主動的、記憶體狀態重啟即失憶」也在此點明）
- `[工]` K8s CronJob（schedule/concurrencyPolicy/非 exactly-once）
- `[問]` 時間與排程（單調鐘 vs 牆鐘、漏跑/補跑）
- `[問]` 失敗偵測（逾時是唯一手段、慢 vs 死）

**Q 部署與發布**（檔 `Q-deployment.md`）
- `[問]` blue-green / canary / rolling
- `[工]` Docker（容器隔離原理）
- `[工]` Kubernetes（Pod/Service/HPA 核心物件）
- `[問]` IaC（宣告式、漂移、冪等 apply）
- `[問]` 12-factor app（聚焦容器/serverless 時代哪些 factor 仍成立、哪些需更新：config/stateless/logs-as-streams）
- `[問]` config 與機密管理

### Part 7 — 觀測與營運文化

**I 可觀測性與品質**（檔 `I-observability.md`）
- `[問]` 三本柱 metric / log / trace
- `[問]` 從 log 算 metric 的陷阱（取樣/遺漏/視窗）
- `[問]` cardinality 爆炸
- `[問]` SLI / SLO / error budget · p99/p999
- `[問]` 告警設計（症狀 vs 原因、告警疲勞）
- `[問]` 負載測試（開放 vs 封閉模型、coordinated omission）
- `[問]` 分散式追蹤（trace context 傳播、span、取樣）
- `[問]` 測試策略（unit / integration / contract / e2e；contract testing）
- `[問]` 可觀測性與品質工具地圖（各類別選什麼、為什麼：日誌採集 FluentBit/Fluentd、Node 診斷 Clinic.js、負載測試 k6/Vegeta、相依掃描 Snyk——定位/現況/替代）

**V 營運與事故文化**（檔 `V-ops-culture.md`）
- `[問]` 事故應變與無咎事後檢討（incident response、blameless postmortem、runbook）
- `[問]` SRE 文化（toil、error budget 當談判工具、SLO-driven）
- `[問]` DORA 四指標（deploy frequency / lead time / MTTR / change failure rate）
- `[問]` 程式碼審查（審什麼、怎麼給/收回饋、它在保護什麼）
- `[問]` 分支與發布策略（trunk-based vs git-flow，配 CD）

---

## 每條目模板（照 style-guide「五段模板」；此處不重複，僅提醒）

- 問題條目：`### 定義與原理` / `### 解法空間` / `### 各方案的保證與取捨` / `### 何時需要` / `### 常見誤解與陷阱` / `### 延伸閱讀`
- 工具條目：`### 是什麼與內部機制` / `### 在哪些系統扮演什麼角色` / `### 保證與限制` / `### 跟替代品的取捨` / `### 常見誤解與陷阱` / `### 延伸閱讀`
- 每條 ≥1 具體案例：技術條目（A–S、V 技術面）帶真實數字的 worked example；判斷/實踐/文化條目（T、U、V 軟性面）用具體情境/案例代替數字（見 style-guide）。對照表是招牌；可貼不可執行 pseudo-code。

## 檔案與命名規範

- **一個領域一個檔**，命名 `<領域字母>-<英文 slug>.md`（如 `A1-delivery-semantics.md`、`M2-coordination-time.md`）。**目標每檔 ≤7 條，方便一個 agent 寫好一檔**：A（17 條）切 3 檔、B（13 條）切 2 檔、M（10 條）切 2 檔、I（9 條）切 2 檔；其餘領域一檔即可。
- 領域檔開頭 `# <字母> — <領域名>`＋前言；每概念 `##`；五段 `###`。**切多檔的領域，每檔 h1 用子題區分**（如 A 三檔：`# A · 交付語意與重複處理`、`# A · 順序、重試與跨服務交付`、`# A · 訊息工具對照`），別三檔同名，否則 reader 側欄分不開。
- reader 設定 `book.config.json` 依 Part 0→7 順序把領域檔分組（groups 標題＝Part 名）。
- **閱讀/打包順序微調（reviewer 採納，config 依此排）**：L（資料同步）歸入 **Part 2**（與 B/O/G 同組，因它與一致性/對帳同源）；**Part 3 順序為 N → C → H → F**（網路基礎先於即時傳輸、身分緊鄰 API）。outline 上方 TOC 的區塊位置未動，以本行為準。
- 附錄（全部寫完後編）：`appendix-A-guarantee-cheatsheet.md`（保證速查：問題×各工具保證一覽）、`appendix-B-glossary.md`（術語表）、`appendix-C-reading-map.md`（外部延伸閱讀總地圖）。

## 跨領域去重：owning 條目（避免平行 agent 把同一主題寫兩次）

同一主題在兩處出現時，**機制/原理只在 owning 條目深講一次，另一處從自己的角度切入、用「（見 X）」帶過、不重講機制**：

| 主題 | owning（深講） | 另一處（只引用） |
|---|---|---|
| 連線池 connection pool | **N**「連線池」（機制與語意） | S「連線池調校」只講調參/監控 |
| 時間/時鐘 | **M**「邏輯時鐘與排序」＋「時間與日期處理」 | J「時間與排程」只講排程觸發語意（單調鐘量逾時、漏跑/補跑） |
| outbox | **A**「outbox/saga」（交付機制） | L「dual-write→outbox」從資料同步角度引 A |
| 對帳/最終一致 | 對帳機制 **L**「reconciliation」 | B「最終一致·補償·對帳」只講一致性模型面 |
| 冷啟動 | **S**「冷啟動與暖機」（通用機制） | J「Lambda」只點 Lambda 特有的 SnapStart 等 |
| 負載均衡/ALB | LB 機制 **N**「負載均衡 L4 vs L7」 | H「ALB vs API Gateway…」從 API 閘道角度比 |
| 複製/分片 | 策略 **M**「複製策略」「consistent hashing」 | B「複製延遲」「分片」講一致性後果與 DB 操作面 |
| schema 變更 | 協定相容 **A**「序列化與 schema 演進」；DB 結構 **B**「零停機 schema 遷移」 | 兩者互引、各守一面 |
| rate limiting / 限流 | 機制 **E**「rate limiting」 | H「API gateway 的角色」只講「閘道層做限流」、引 E |
| 降級 fallback | 通用 **P**「fallback · 降級」 | G「多層快取與優雅降級」只講快取層降級、引 P |
| 冪等 idempotency | 定義/原理 **A**「冪等」 | B「樂觀並發控制」、M「分散式鎖/2PC」、Q「IaC 冪等 apply」只引用、不重講定義 |
| 重試/退避/jitter | 做法 **A**「重試、退避、jitter」 | E「retry storm」講放大機制、P「timeout/budget」只引做法 |
| circuit breaker | 三態機制 **E**「circuit breaker」 | P「fallback·降級」引它當觸發機制、不重講三態 |
| health check | 機制/定義 **P**「health check」 | J「失敗偵測」講分散式視角、Q「K8s」只點 probe 設定語意 |
| event sourcing / CQRS | 原理 **K**「Event sourcing 與 CQRS」 | A「Kafka」只說 log 天然支援 ES、L「CDC」引 K |
| Protobuf 序列化 | **A**「序列化與 schema 演進」 | N「gRPC/Protobuf」只講 gRPC 怎麼用 Protobuf 當 IDL＋傳輸語意 |
| Redis 內部 | **G**「Redis」 | A「Redis Pub/Sub vs Streams」只講交付語意差異、引 G |

## 全域不涵蓋（守住核心，任何條目都不展開）

- **特定應用域**：feed/timeline 設計、推薦/搜尋排序、串流處理、資料湖/倉、向量資料庫、ML serving、邊緣運算。
- **範圍外**：前端/行動端/UI、DevOps 工具鏈品牌操作、特定雲廠牌 console 操作、敏捷/Scrum 流程、估點方法論、職涯階梯/影響力/招募/績效。
- **資安只收與本書主題交界的**：TLS/mTLS 當傳輸協定（N）、config/secrets 當部署實踐（Q）、JWT/OAuth/RBAC 當身分（F）——這些**在範圍內**。**不收**：加密演算法內部、注入/XSS/CSRF 等應用層攻防、KMS/HSM 進階機密、滲透測試。
- **絕對禁止**（見 style-guide）：作者個人系統/履歷、糾錯口吻、指向其他書、練習段、AI 工具版本。
