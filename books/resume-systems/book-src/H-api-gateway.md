# H · API 與閘道

這個領域回答「對外那層 HTTP 介面要怎麼設計、怎麼演進、怎麼擺一個共用的入口」。本檔含四個問題條目（REST 設計與版本化、分頁、REST/GraphQL/gRPC 範式對照、API gateway 的角色）與一個工具對照（ALB／API Gateway／KrakenD／Kong）。邊界：限流的「機制」（token bucket、分散式計數）在領域 E，本檔只講「閘道層這個位置上做限流」這件事；負載均衡的 L4/L7 機制在領域 N，本檔的工具對照只從「API 閘道」角度切入。

## REST 設計 · 版本化 · OpenAPI 契約

### 定義與原理

REST 是一組架構約束（Fielding 2000 博士論文），核心是「以資源（resource）為中心、用統一介面操作」：資源有 URI、用 HTTP 方法表達意圖（GET 讀、PUT 整體取代、PATCH 局部更新、DELETE 刪、POST 建立或非冪等動作）、用狀態碼表達結果、回應自帶足夠資訊讓 client 知道下一步。對後端工程師而言，REST 真正的保證來自三件可機器驗證的東西，而不是 URL 長得漂不漂亮：

1. **方法語意（method semantics）**：GET/PUT/DELETE 是冪等的（重送結果一致，見 冪等 idempotency，領域 A），POST 不是；GET 應該安全（safe，無副作用）。這直接決定「逾時後能不能重試」。
2. **版本相容**：介面一旦有外部 client，就進入「不能隨意破壞」的契約狀態。
3. **契約描述**：用 OpenAPI（前身 Swagger）把端點、參數、schema、錯誤碼寫成一份機器可讀的 YAML/JSON，讓 client SDK、mock server、契約測試都從同一份真相生成。

OpenAPI 當前最新版為 **3.2.0（2025-09 發布）**；**3.1.0（2021-02）** 是重要里程碑，它讓 OpenAPI 的 schema 與 **JSON Schema Draft 2020-12** 完全對齊（先前版本是自訂的 schema 子集，工具鏈各自為政）（2026-06）。

### 解法空間

「怎麼把外部介面演進而不破壞既有 client」的辦法，由弱到強：

- **不破壞式變更（additive change）**：只加可選欄位、加新端點、加新的可選 query param。舊 client 看不到也不受影響。這是第一選擇，多數變更都能塞進這條路。
- **URI 版本化**：`/v1/orders` → `/v2/orders`。最直白、最好快取與路由、好觀察（log 裡看得到版本），代價是「v2 不是 orders 的新版，而是另一個 orders」，語意潔癖者不愛，但工程上最省心。
- **header 版本化**：`Accept: application/vnd.api+json; version=2` 或自訂 header。URI 乾淨，但版本藏在 header 裡，CDN/快取要把它納入 cache key，debug 時 log 不標版本就抓瞎。
- **media type / content negotiation**：用 `Accept` 協商表述格式，是 header 版本化的「正統 REST」變體，實務上採用率低、工具支援零散。
- **欄位層級演進**：不動端點版本，靠「新增欄位、舊欄位標 deprecated 但保留、設下線日期」滾動。配合 OpenAPI 的 `deprecated: true` 與 sunset header（RFC 8594）讓 client 有機器可讀的下線預告。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 不破壞式變更 | 舊 client 零影響 | 絕大多數日常演進 | 「可選」要真的可選；新增 enum 值對嚴格驗證的舊 client 仍可能是破壞性變更 |
| URI 版本化 `/v2` | 版本顯式、好路由/快取/觀察 | 對外公開 API、多 client | 版本爆炸時要設淘汰機制；v1/v2 並存期程式碼會分叉 |
| header 版本化 | URI 乾淨、語意純 | 內部 API、單一團隊掌控 client | cache key 必須含 header，否則回錯版本；log 要顯式記版本 |
| media type 協商 | 最符合 REST 原意 | 教科書場景、強協商需求 | 工具/CDN 支援零散，團隊認知成本高，實務罕見 |
| 欄位演進 + sunset | 細粒度、不需端點翻版 | 持續演進、想避免大版本 | 必須真的執行下線（設日期、發告警），否則 deprecated 欄位永遠死不了 |

**保證的邊界**：OpenAPI 只是「描述」，不是「強制」。它保證「有一份契約」，不保證「實作符合契約」——那要靠 contract testing（見 測試策略，領域 I）把生成的契約拿去比對真實回應。

Worked example：一個 API 日均 200 萬次呼叫、其中 `GET /v1/orders` 佔 60%（約 120 萬次/日）。要把回應裡的 `amount`（整數分）改成帶幣別的物件 `{ currency, minor_units }`。直接改型別＝破壞性，120 萬次/日的 client 全炸。不破壞式做法：新增 `amount_v2` 物件欄位、`amount` 標 deprecated 並設 sunset 為 90 天後；這 90 天內兩欄位都回傳，monitoring 盯「仍只讀舊 `amount` 的 client」比例，降到接近 0 才移除。代價：90 天內回應 payload 多一個欄位（約多 30 bytes/筆 × 120 萬 = 約 36 MB/日 額外出流量），換零中斷遷移，划算。

### 何時需要

- **介面一有外部 client（前端團隊、第三方、行動 App 舊版）就需要版本策略**——因為你無法強迫所有 client 同步升級。
- **只有內部、單一團隊、可同時部署 client 與 server** 時，版本化常是 over-engineering：直接改、一起部署即可，別為「未來可能有外部 client」預先扛版本維護成本（YAGNI，見 簡單性 vs 過度工程，領域 U）。
- **OpenAPI 契約** 在「多 client、要自動生成 SDK、要 mock、要契約測試」時報酬率最高；只有一個 client 且改動頻繁時，維護 spec 與實作同步本身就是負擔，可延後。

### 常見誤解與陷阱

- **「REST 就是 CRUD over HTTP」**：方法語意（冪等、安全）才是 REST 給你的工程保證；把刪除做成 `GET /delete?id=1` 會讓爬蟲、預抓取、重試把資料刪掉。
- **「PATCH 是冪等的」**：規格上 PATCH 不保證冪等（取決於 patch 文件語意）；`PATCH {op: increment}` 重送兩次就加兩次。需要冪等時自己加冪等鍵（見 冪等 idempotency，領域 A）。
- **「200 + body 裡放 error」**：用 200 包失敗會讓 client、LB、監控全以為成功，吃掉所有基於狀態碼的告警與重試。錯誤就回 4xx/5xx。
- **「新增 enum 值是安全的」**：對用嚴格 schema 驗證、或用 exhaustive switch 的舊 client，多一個 enum 值可能直接拋例外。新增 enum 值對某些 client 是破壞性的。
- **「URI 版本化 vs header 版本化有對錯」**：沒有。URI 版本好觀察、header 版本 URI 乾淨，按團隊掌控 client 的程度選，別當宗教戰爭。

### 延伸閱讀

- Roy Fielding, "Architectural Styles and the Design of Network-based Software Architectures"（2000，REST 原始論文）：https://ics.uci.edu/~fielding/pubs/dissertation/top.htm
- OpenAPI Specification 3.2.0：https://spec.openapis.org/oas/v3.2.0.html
- RFC 9110, HTTP Semantics（方法的 safe/idempotent 定義）：https://www.rfc-editor.org/rfc/rfc9110.html
- RFC 8594, The Sunset HTTP Header Field：https://www.rfc-editor.org/rfc/rfc8594.html

## 分頁 pagination（offset vs cursor/keyset、深分頁）

### 定義與原理

分頁解的問題：一個查詢可能命中幾十萬筆，不能一次全回。要把結果切成頁，每頁穩定、可往下翻、不漏不重。難點全在「資料是動態的」——翻頁的同時有人在插入/刪除，於是「第 2 頁」這個概念本身就會漂移。第一原理：分頁是在「用什麼當『接著上次往下』的座標」上做取捨。offset 用「跳過 N 筆」當座標，cursor/keyset 用「上一頁最後一筆的排序鍵值」當座標。

### 解法空間

- **offset/limit**：`ORDER BY created_at LIMIT 20 OFFSET 1000`。直觀、能跳到任意頁碼。代價是資料庫必須掃過並丟棄前 1000 筆才能拿到第 1001 筆——OFFSET 越大越慢（深分頁問題）。
- **keyset / cursor pagination（seek method）**：用「上一頁最後一筆的排序鍵」當錨點：`WHERE (created_at, id) < (:last_ts, :last_id) ORDER BY created_at DESC, id DESC LIMIT 20`。配合索引，每頁都是一次 index seek，與翻到第幾頁無關，成本恆定。代價：不能跳到任意頁碼（只能下一頁/上一頁），排序鍵必須唯一（否則邊界會漏或重，所以常複合一個 tie-breaker 如 `id`）。
- **不透明 cursor（opaque token）**：把 keyset 的座標（排序欄位值 + tie-breaker）編碼成 base64 token 回給 client，client 下次帶回來。好處是內部座標格式可演進、client 不依賴它，也能塞入排序方向、過濾條件的雜湊防止竄改。
- **快照/具現化分頁**：對「報表式、要求整份一致」的需求，先把結果集固定成一個快照（暫存表、或帶 snapshot id 的 search context，如搜尋引擎的 scroll/PIT），整輪翻頁都讀同一份。代價是要維護伺服器端狀態與其 TTL。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| offset/limit | 可跳任意頁碼、實作最簡 | 後台分頁、總筆數小、淺頁 | 深 OFFSET 線性變慢；翻頁中有插入/刪除會重複或漏資料 |
| keyset/cursor | 每頁成本恆定、邊界穩定 | 無限下拉、API feed、大表 | 不能跳頁；排序鍵須唯一（補 tie-breaker）；換排序欄位 cursor 失效 |
| opaque cursor | 內部座標可演進、可防竄改 | 對外公開 API | client 不能自行構造 cursor；token 過期/格式變更要處理 |
| 快照/PIT 分頁 | 整輪翻頁強一致 | 匯出、對帳、報表 | 伺服器端狀態 + TTL；不適合高併發長期保留 |

Worked example：一張 5,000 萬列的 `events` 表，要翻到第 10,000 頁、每頁 20 筆。offset 寫法 `LIMIT 20 OFFSET 199980`：即使 `created_at` 有索引，資料庫仍須沿索引讀並丟棄前 199,980 筆，這頁的延遲隨頁碼線性上升，深處可達數百毫秒到秒級。keyset 寫法帶上一頁最後一筆的 `(created_at, id)`：`WHERE (created_at, id) < (:ts, :id) ORDER BY created_at DESC, id DESC LIMIT 20`，走複合索引一次 seek 取 20 筆，無論第 1 頁或第 10,000 頁都是個位數毫秒。代價：失去「直接跳到第 10,000 頁」的能力——但「真的有人類會手動翻到第 1 萬頁嗎」通常答案是否，所以這個能力的損失多半不痛。

### 何時需要

- **無限下拉、活動流、時間線、API 給程式消費** → keyset/cursor，因為這些場景天然只往下翻、且資料量大。
- **後台管理介面、總筆數已知且不大（幾千筆內）、使用者要看「第幾頁／共幾頁」** → offset 夠用，別過度設計。
- **匯出/對帳要求「這份結果在我翻完前不變」** → 快照/PIT。
- 反過來：**對一張會持續成長的大表用 offset 做對外 feed**，幾乎注定在資料變多後變慢——這是最常見的「上線時沒事、半年後 P99 爆掉」陷阱。

### 常見誤解與陷阱

- **「offset 分頁結果穩定」**：在翻頁過程中有人在列表頂端插入一筆，所有後續頁的內容會整體位移一格，於是你會在下一頁重看到一筆、或漏掉一筆。offset 對動態資料不穩定。
- **「cursor 可以跳頁」**：不行。cursor 只能順著排序往前/後，要「跳到第 N 頁」就得回到 offset。需求若真要跳頁，承認它、別硬把 cursor 包成假頁碼。
- **「`COUNT(*)` 算總頁數很便宜」**：對大表，每次分頁都跑一次精確 `COUNT(*)` 可能比查那頁資料還貴。要嘛快取近似總數、要嘛只回「有沒有下一頁」（多取一筆判斷），別每頁精算總數。
- **「排序鍵不唯一也沒差」**：用非唯一欄位（如只用 `created_at`）當 keyset 座標，同一時間戳的多筆會在頁邊界漏或重。永遠補一個唯一 tie-breaker（如 `id`）進排序與 WHERE。

### 延伸閱讀

- Markus Winand, "Pagination Done the PostgreSQL Way"／Use-The-Index-Luke 的 seek method：https://use-the-index-luke.com/no-offset
- GraphQL Cursor Connections Specification（cursor 分頁的事實標準）：https://relay.dev/graphql/connections.htm

## API 範式對照（REST vs GraphQL vs gRPC）

### 定義與原理

這是一個「分類型」條目：三者不是同一軸上的競品，而是針對不同問題優化的三種介面風格。底層都可以跑在 HTTP 上，差別在「資料形狀由誰決定、契約有多硬、傳輸有多省」。

- **REST**：資源導向、HTTP 動詞、回應形狀由 server 端點決定。文字（JSON）、人類可讀、快取友善（GET 可被 HTTP 快取層快取）。
- **GraphQL**：單一端點，client 用 query 語言宣告「我要哪些欄位」，server 照單回傳。解的是「REST 端點要嘛回太多（over-fetch）、要嘛回太少而得呼叫好幾個端點（under-fetch / N 次往返）」。
- **gRPC**：以 Protobuf 為 IDL、跑在 HTTP/2 上的二進位 RPC，強型別 schema 由 `.proto` 生成雙邊 stub，支援 streaming。解的是「服務間呼叫要省頻寬、要強契約、要 streaming」（傳輸與 Protobuf 機制見 gRPC / Protobuf，領域 N；序列化相容見 序列化與 schema 演進，領域 A）。

### 解法空間

把選擇拆成幾個正交維度，每個維度三者落在不同位置：

- **資料形狀誰決定**：REST＝server（端點固定）；GraphQL＝client（query 指定）；gRPC＝schema（`.proto` 固定方法與訊息）。
- **契約硬度**：gRPC 最硬（編譯期型別檢查）；REST 靠 OpenAPI（描述式、非強制）；GraphQL 有強 schema 但欄位選擇由 client 動態決定。
- **傳輸效率**：gRPC（Protobuf 二進位 + HTTP/2 多工）通常最省；REST/GraphQL 多走 JSON over HTTP/1.1 或 2，較肥但可讀。
- **快取**：REST 的 GET 天然吃 HTTP 快取（CDN/瀏覽器/反向代理）；GraphQL 多為 POST 單端點，HTTP 層快取幾乎失效，要在應用層自己做；gRPC 同理難用 HTTP 快取。
- **瀏覽器/邊界友善度**：REST 最友善；GraphQL 友善；gRPC 在瀏覽器需 gRPC-Web 代理（瀏覽器不能直接開 HTTP/2 trailers），多用於後端對後端。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| REST + OpenAPI | HTTP 快取友善、生態最廣、人類可讀 | 對外公開 API、CRUD 資源、需 CDN 快取 | over/under-fetch；多資源組合要多次往返；契約非強制 |
| GraphQL | client 精準取欄位、單請求組合多資源 | 多端裝置欄位需求各異、聚合多後端 | HTTP 快取失效要自建；N+1 解析要 dataloader；query 複雜度需限制防 DoS |
| gRPC | 強型別契約、二進位省頻寬、雙向 streaming | 內部微服務間、低延遲高吞吐、streaming | 瀏覽器需 gRPC-Web；不可讀難 curl；HTTP 快取難用 |

Worked example：一個行動 App 的訂單詳情頁要顯示「訂單 + 買家名 + 3 個品項縮圖」。REST 下若端點各自獨立，client 要打 `GET /orders/1`、`GET /users/9`、再加 3 個 `GET /products/{id}`，共 5 次往返；在 200ms RTT 的行動網路上、若序列依賴，肉眼可感的等待。GraphQL 下一個 query 把這幾塊一次取回、且只取真正用到的欄位（如不要訂單的 50 個內部欄位、只要 5 個），單次往返、payload 也更小。但代價：server 端要小心 N+1——一個 query 拉 100 筆訂單、每筆再各查一次買家，就是 1 + 100 次 DB 查詢，必須用 dataloader 把同批 user id 合併成一次 `WHERE id IN (...)`（N+1 機制見 N+1 查詢，領域 S）。

### 何時需要

- **對外公開、希望吃 CDN 快取、希望第三方能 curl 來試** → REST。它的快取與通用性是 GraphQL/gRPC 換不來的。
- **多種前端（web/iOS/Android）對同一資料的欄位需求差異大、或一個畫面要聚合多個後端** → GraphQL 的精準取欄與單請求聚合報酬率最高。
- **後端服務之間、延遲與吞吐敏感、要 streaming、團隊能接受二進位不可讀** → gRPC。
- **over-engineering 警示**：一個只有單一 web 前端、CRUD 為主的內部系統硬上 GraphQL，換來的是 schema 維護、複雜度限制、快取自建的成本，卻沒吃到「多端差異化取欄」的好處——這時 REST 更簡單（見 簡單性 vs 過度工程，領域 U）。

### 常見誤解與陷阱

- **「GraphQL 比 REST 快」**：GraphQL 省的是「往返次數」與「over-fetch 的 payload」，不是單次查詢的執行速度；用錯（N+1、無複雜度限制）反而更慢、更危險。
- **「GraphQL 不用想快取」**：恰恰相反，它放棄了 HTTP 層快取，快取得在應用層（persisted query、欄位級快取）自己重建。
- **「gRPC 一定比 REST 省」**：對小 payload、低頻呼叫，Protobuf 省的位元組可能被「不可讀、難 debug、要維護 stub 生成」的工程成本蓋過。省頻寬的價值要量級夠大才顯現。
- **「GraphQL 端點不會被打爆」**：開放的 GraphQL 端點若不限制 query 深度/複雜度，一個深層巢狀 query 就能放大成天量 DB 查詢，是一種 DoS 面。複雜度與深度限制是必備防線。
- **「三選一」**：實務上常混用——對外 REST、內部服務間 gRPC、BFF 層用 GraphQL 聚合。它們不互斥。

### 延伸閱讀

- GraphQL Specification（官方規格）：https://spec.graphql.org/
- gRPC 官方文件（Core concepts）：https://grpc.io/docs/what-is-grpc/core-concepts/
- "GraphQL Cursor Connections Specification"（分頁互通）：https://relay.dev/graphql/connections.htm
- RFC 9110, HTTP Semantics（REST 倚賴的方法與快取語意）：https://www.rfc-editor.org/rfc/rfc9110.html

## API gateway 的角色

### 定義與原理

API gateway 是擺在「外部 client」與「後端服務群」之間的一層反向代理，把每個後端服務都要各自做、又不該各自做的橫切關注（cross-cutting concerns）集中到一個位置。它解的核心問題：在微服務下，認證、限流、TLS 終結、路由、轉換、聚合若散落在每個服務裡，會重複實作、版本漂移、難一致治理。把它們上提到閘道層，後端服務就能專注業務邏輯。

閘道層典型承擔五類職責：

1. **路由**：依 host/path/header 把請求導到對的後端（L7 路由機制見 負載均衡 L4 vs L7，領域 N）。
2. **認證/授權（authn/authz）**：在邊界驗 token（JWT 驗簽、OAuth introspection）、做粗粒度授權，後端只收已驗身分的請求（驗 token 機制見 token 生命週期與撤銷，領域 F）。
3. **限流（rate limiting）**：在閘道這個位置上保護後端不被打爆——本檔只講「為什麼把限流放在閘道層」這個架構決定；token bucket／分散式計數的機制見 rate limiting，領域 E。
4. **轉換（transformation）**：改寫 request/response（header 注入、協定轉換如 REST↔gRPC、欄位重塑）。
5. **聚合（aggregation）**：把一次外部請求扇出成多個後端呼叫、合併回應（BFF 模式的一種落地）。

### 解法空間

「橫切關注要擺哪」有幾種架構落點，閘道只是其中之一：

- **集中式 API gateway**：所有外部流量先進閘道。單一治理點、好觀察，代價是它本身成為關鍵路徑上的單點，要自己做高可用。
- **每服務內嵌 library**：把 authn/限流做成共用函式庫塞進每個服務。沒有額外網路跳，但語言綁定、升級要全服務重部署、難一致。
- **service mesh sidecar**：把橫切關注下沉到每個 pod 旁的 sidecar proxy（Envoy），對服務間（east-west）流量做 mTLS、重試、限流（見 service mesh，領域 N）。閘道管南北向（north-south、對外），mesh 管東西向（east-west、服務間），兩者常並存而非互斥。
- **BFF（Backend for Frontend）**：為每種前端各設一個聚合層，把「聚合」這個職責從通用閘道拆出來、貼近特定前端需求。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 集中式 gateway | 單一治理點、橫切關注一致 | 對外 API、多後端、要統一 authz/限流 | 自己是關鍵路徑單點，要 HA；邏輯堆太多會變「分散式單體」 |
| 每服務 library | 無額外跳、延遲低 | 同語言單體式、少量服務 | 語言綁定、升級要全部重部署、易漂移 |
| mesh sidecar | east-west mTLS/重試/限流、語言無關 | 服務間流量治理、零信任內網 | 運維複雜度高；管的是服務間、非對外邊界 |
| BFF | 聚合貼近前端、解耦通用閘道 | 多前端、各自聚合需求不同 | 每種前端一層、數量增多；與通用閘道職責要劃清 |

Worked example：一個系統有 12 個微服務、對外 1 個 API。若每個服務各自實作 JWT 驗簽，等於 12 份驗簽碼、12 套金鑰輪替邏輯、12 個出錯點；某次 JWKS 端點換位址，要改 12 個服務、12 次部署。把驗簽上提到閘道：閘道驗完把 `X-User-Id` 等可信 header 注入後端、後端信任內網來源即可，金鑰輪替只改一處。限流同理：與其每個服務各算各的，閘道在入口處對「每 API key 每秒 100 次」集中計數（分散式計數同步見 rate limiting，領域 E），超過就回 429，後端完全不被打到。代價：閘道現在是所有外部流量的必經點，它掛＝全掛，所以它本身要多副本 + 健康檢查（見 health check，領域 P）。

### 何時需要

- **多個後端服務 + 對外有 client + 需要統一的認證/限流/觀察** → 閘道報酬率最高。
- **單一服務、單體、團隊小** → 閘道是 over-engineering：那層橫切關注用中介層（middleware）在應用內做掉即可，多一層代理只是徒增延遲與運維面。
- **服務間（east-west）流量治理需求** 該找 mesh，不是把內部呼叫也硬塞進對外閘道。
- 判準：當「同一段橫切邏輯被複製到第 3 個服務」時，就該考慮上提到閘道；在那之前，提早建閘道是預支複雜度。

### 常見誤解與陷阱

- **「閘道能扛所有橫切關注」**：把業務邏輯、複雜編排、資料轉換全堆進閘道，它會長成一個「分散式單體」——所有團隊都要改它、它變成部署瓶頸與單點。閘道該薄，只放真正橫切的東西。
- **「閘道驗了 token，後端就不用管授權」**：閘道做的是粗粒度（authn + 邊界授權）；細粒度（這個 user 能不能改這筆訂單）是業務規則，必須在後端做。把細粒度授權外包給閘道會漏（見 RBAC vs ABAC，領域 F）。
- **「閘道做限流就萬無一失」**：閘道限流是 best-effort 的第一道閘；多閘道實例間的計數要同步，否則每個實例各算各的會放大 N 倍（分散式限流機制見 rate limiting，領域 E）。且閘道擋不住「已進來的慢請求」拖垮後端，那要靠後端自己的 timeout/bulkhead（見 timeout / deadline / budget，領域 P）。
- **「閘道是免費的可用性」**：它在關鍵路徑上，沒做多副本與健康檢查時，它的故障率就是全系統的下限。閘道要比它保護的後端更可靠。

### 延伸閱讀

- Microservices.io, "API Gateway / Backends for Frontends" pattern：https://microservices.io/patterns/apigateway.html
- Sam Newman, "Pattern: Backends For Frontends"：https://samnewman.io/patterns/architectural/bff/

## ALB vs API Gateway vs KrakenD vs Kong

### 是什麼與內部機制

四者都坐在「client 與後端之間」，但機制與定位差很多。本條從「API 閘道」角度比；純 L4/L7 負載均衡機制見 負載均衡 L4 vs L7（領域 N）。

- **AWS ALB（Application Load Balancer）**：AWS 全託管的 L7 負載均衡器，以 listener → rule → target group 為核心，支援 host/path/header-based 路由。它本質是「路由 + 健康檢查 + TLS 終結」，不是功能完整的 API 閘道——不做 per-request 的 request/response 轉換、原生 authz 有限（可掛 OIDC/Cognito listener auth，但非 per-request 細粒度）、無原生限流（要搭 AWS WAF 做 rate-based rule）。計費走 LCU（Load Balancer Capacity Unit）模型，高吞吐下單位成本低、延遲低（2026-06）。
- **AWS API Gateway**：AWS 全託管的 API 閘道，提供限流、authz（JWT / Lambda authorizer / IAM）、request transformation、usage plans、API keys。分 **REST API**（功能最完整，含 VTL mapping template、usage plans、API keys、private endpoint）與 **HTTP API**（較新、約便宜 70%、延遲較低、支援 JWT authorizer，但無 VTL、無 usage plans、無 API keys）。
- **KrakenD**：以 **Go** 寫的 stateless、declarative、高效能 API 閘道，**無 runtime database**，啟動時讀一份 JSON 設定就跑。招牌是 **native API aggregation**（把多個後端回應合併、過濾、重塑欄位）。治理需精確：捐給基金會的不是整個 KrakenD，而是其**核心 framework 於 2021-05 捐成 Linux Foundation 主持的 `Lura Project`**；KrakenD Community/Enterprise 是 Lura engine 的兩個實作。KrakenD（公司）於 **2025-09 被 Shop Circle 收購**，團隊與路線維持，Lura framework 續留 Linux Foundation（2026-06）。
- **Kong**：建在 **NGINX + OpenResty（Lua）** 上的 API 閘道，控制面有資料庫（PostgreSQL，或 DB-less 宣告式模式），招牌是 **Lua plugin 生態**——每個 plugin 是掛進 NGINX 請求生命週期各 phase 的 Lua 模組。提供 OSS（自架）與 Konnect（SaaS 控制面）兩種形態（2026-06）。

### 在哪些系統扮演什麼角色

- **ALB**：當你只需要把外部 L7 流量路由到一群容器/EC2/Lambda 上、不需要 per-request authz 或轉換時，ALB 是最省、最低延遲的入口。常作為 EKS/ECS 服務的對外入口、或 API Gateway 後面再接的一層。
- **API Gateway**：當入口要 throttling + authz + 轉換 + usage plan（給第三方發 API key 並計量）時用它；尤其與 Lambda 組成 serverless API 時是預設搭配。
- **KrakenD**：當核心需求是「把多個後端 API 在閘道層聚合成一個對外回應、且要極高吞吐、不想維護有狀態控制面」時最契合（BFF/聚合場景）。
- **Kong**：當你要一個 plugin 可插拔、跨雲/自架、生態成熟的閘道，且願意維運它的控制面/資料庫時。

### 保證與限制

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| AWS ALB | L7 路由 + 健康檢查 + TLS 終結、低延遲低成本、全託管 | 容器/EC2 對外入口、純路由 | 無原生限流（需 WAF）、無 per-request 轉換、authz 僅粗粒度 |
| AWS API Gateway (REST) | 限流 + authz + VTL 轉換 + usage plans + API keys、全託管 | serverless API、要計量/發 key、要轉換 | 較貴、有額外延遲；VTL 學習曲線；強綁 AWS |
| AWS API Gateway (HTTP) | 便宜約 70%、低延遲、JWT authorizer、全託管 | 簡單 proxy + JWT auth | 無 VTL/usage plans/API keys/private endpoint |
| KrakenD | 無狀態、宣告式、極高吞吐、原生聚合 | 多後端聚合（BFF）、高流量 | 無 runtime plugin 系統；治理屬 Lura/LF，公司屬 Shop Circle（2025 起） |
| Kong | plugin 生態豐富、跨雲自架、可 DB-less | 需可插拔 plugin、混合雲、自架掌控 | 自架要維運 NGINX/控制面（DB 模式還要顧 PostgreSQL）；自架運維成本 |

**限流（保證邊界）**：AWS API Gateway 的 REST API **帳戶層預設限流為每個 Region、每秒 10,000 RPS steady-state、burst 5,000**（這是跨該帳戶該 Region 所有 REST API 的合計，用 token bucket，可開 case 申請調高；部分較新 Region 如 Cape Town、Milan、Jakarta、UAE 等預設較低，為 2,500 RPS / 1,250 burst）。AWS 官方明言這些是 **best-effort 的目標值、非保證上限**，超過會回 `429 Too Many Requests`（2026-06）。

Worked example：一個 serverless API 上線初期 200 RPS，遠在 10,000 RPS 帳戶上限內，看似無虞。但帳戶層上限是「該 Region 所有 REST API 合計」——若同帳戶同 Region 另有批次作業偶發衝到 9,000 RPS，兩者相加逼近 10,000，你的低流量 API 也會跟著吃 429。正解：別只靠帳戶層預設，在 stage/method 設 per-stage throttle、或對第三方用 usage plan 設 per-key 限制，把不同 API 的流量彼此隔離（這呼應 bulkhead 艙壁隔離，領域 P；限流計數機制見 rate limiting，領域 E）。

### 跟替代品的取捨

選型沿幾條軸：

- **託管 vs 自架**：ALB / API Gateway 全託管（綁 AWS、零運維、但綁定與計費隨流量走）；KrakenD / Kong 可自架（跨雲、可掌控、但你扛升級與高可用）。
- **有狀態 vs 無狀態控制面**：KrakenD 無 runtime DB、啟動讀 JSON，部署與水平擴展極簡；Kong 的 DB 模式有 PostgreSQL 控制面（也可 DB-less），plugin 生態換來運維面。
- **聚合 vs 可插拔**：要「把多後端合併成一個回應」KrakenD 原生最強；要「靠社群 plugin 拼裝各種能力」Kong 生態最廣；ALB 兩者都不做（它只路由）；API Gateway 兩者有限度地做。
- **延遲/成本**：純路由場景 ALB 通常延遲最低、LCU 計費在高吞吐下最省；API Gateway 多一層功能、單位成本與延遲較高，換來 authz/轉換/計量。

經驗法則：需 VTL 轉換 / usage plans / API keys → API Gateway REST；只要便宜快速 proxy + 簡單 JWT auth → API Gateway HTTP；純 L7 路由到容器/EC2、不需 per-request authz/轉換 → ALB；要跨雲自架 + 多後端聚合 → KrakenD；要跨雲自架 + plugin 生態 → Kong。

### 常見誤解與陷阱

- **「ALB 是 API 閘道」**：ALB 是 L7 LB，它路由與終結 TLS，但不做 per-request 轉換、無原生限流、authz 僅粗粒度。把它當完整閘道用，限流與細粒度 authz 會落空（限流得另搭 WAF）。
- **「KrakenD 是 CNCF 專案」**：錯。捐給 Linux Foundation 的是其 framework `Lura Project`（**不是 CNCF**，兩者不可混用），且嚴格說是 framework 而非 KrakenD 本身；別寫成「KrakenD 仍是獨立開源公司」——2025-09 起公司已屬 Shop Circle（2026-06）。
- **「API Gateway 的 10,000 RPS 是我這支 API 的額度」**：那是帳戶層、該 Region 所有 REST API 合計的 best-effort 目標，不是 per-API 保證；要隔離得用 per-stage/per-key 設定。
- **「Kong DB-less 就沒有狀態問題」**：DB-less 移除了 PostgreSQL 控制面，但宣告式設定的同步、plugin 的執行期狀態仍要顧；它簡化的是控制面、不是消滅所有狀態考量。
- **「閘道選型只看功能表」**：四者真正的分水嶺是「託管 vs 自架」帶來的運維與綁定取捨。功能能補，但「誰半夜被叫起來修閘道」這件事選型時就決定了（見 自建 vs 採用，領域 U）。

### 延伸閱讀

- AWS, "Throttle requests to your REST APIs"（帳戶層限流官方文件）：https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html
- AWS, "Choosing between REST APIs and HTTP APIs"：https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
- KrakenD, "Open Source"（Lura / Linux Foundation 治理）：https://www.krakend.io/open-source/
- Linux Foundation 新聞稿, "Open Source API Gateway KrakenD Becomes Linux Foundation Project"：https://www.linuxfoundation.org/press/press-release/open-source-api-gateway-krakend-becomes-linux-foundation-project
- Kong Gateway 官方文件：https://docs.konghq.com/gateway/
