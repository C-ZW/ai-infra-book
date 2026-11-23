# 附錄 B：開源專案 0-day 審計與黑箱 Bug Bounty 實戰 Checklist

本附錄從《邊界失守》已完稿之 30 個章節（`ch01`–`ch21`, `ch25`, `ch28`–`ch32`, `ch34`, `ch36`, `ch37`）萃取出一套可直接用於**開源專案白箱 0-day 審計**與**黑箱／灰箱 Bug Bounty 實戰**的可勾選檢查清單（Checklist）。

每項檢核點均標註對應章節、攻擊者尋找的破口原語（Source / Sink / Invariant Violation）以及結構性防禦基線（Paved Road）。建議在審計新目標時將本頁複製至個人審計筆記中逐項勾選。

---

## 一、邊緣協議、代理分歧與快取／WAF 邊界（Ch01–Ch03, Ch11, Ch14）

### 1. HTTP 請求走私與連線生命週期邊界（Ch01, Ch03）
- [ ] **雙標頭與空白混淆探測（CL.TE / TE.CL）**：檢查前端反向代理（Nginx / CDN / Envoy）與後端應用伺服器（Node.js `llhttp` / Gunicorn / Go `net/http`）對同時攜帶 `Content-Length` 與 `Transfer-Encoding: chunked`（含 `Transfer-Encoding: xchunked`、Tab `\t`、垂直空白或換行摺疊）的優先序是否一致。
- [ ] **HTTP/2 降級走私（H2.CL / H2.TE / CRLF 注入）**：當邊緣閘道終止 HTTP/2 並降級轉發為 HTTP/1.1 時，確認是否拒絕 H2 `:path` 或自訂 Header Value 內含 `\r\n` 的請求，以及是否嚴格校驗 H2 `content-length` 偽標頭與實際 `DATA` 訊框位元組總和一致。
- [ ] **Keep-Alive 逾時視窗對齊**：核對反向代理讀取逾時（如 NexusPay 基準 `proxy_read_timeout = 30 s`）與後端閒置連線關閉逾時（如 Node.js `keepAliveTimeout = 5 s`）。後端之 Keep-Alive 逾時必須大於上游代理的閒置連線重用超時，避免連線關閉瞬間發生 Socket 複用錯位。
- [ ] **前端路由存取控制繞過驗證**：若前端 Nginx 以 `location /internal/ { return 403; }` 阻擋內部路由，測試能否透過走私請求的殘留前綴或路徑正規化差異（如 `/v1/../internal/admin`、`/internal%2fadmin`）在同一條後端 Keep-Alive 連線上觸達後端控制器。

### 2. URL 解析分歧、SSRF 與 DNS Rebinding（Ch11, Ch34）
- [ ] **多解析器語法分歧（WHATWG `new URL()` vs RFC 3986 / Legacy Parser）**：白箱搜出所有外部 URL 驗證函式與實際發起請求的 HTTP Client。確認兩者是否使用同一個 URL 解析器；黑箱測試 `http://expected-host@127.0.0.1:8080/`、反斜線 `http://127.0.0.1\@expected-host/`、多重 `@` 與 Unicode 網域（Punycode）轉換差異。
- [ ] **IP 字面量替代格式繞過**：測試十進位整數 IP（`http://2130706433/`、`http://2852039166/`）、八進位（`http://0177.0.0.1/`）、十六進位（`http://0x7f000001/`）、省略零寫法（`http://127.1/`）以及 IPv4-mapped IPv6 位址（`http://[::ffff:127.0.0.1]/`、`http://[::ffff:169.254.169.254]/`）。
- [ ] **HTTP 重新導向跳板（301 / 302 / 307 / 308）**：確認伺服器端 HTTP Client 是否預設跟隨重導向。若未設定 `redirect: 'manual'`（或 `maxRedirects: 0`），攻擊者可提供合法的公網 HTTPS URL，再由該伺服器回傳 `302 Found` 導向 `http://169.254.169.254/latest/meta-data/`。
- [ ] **DNS Rebinding 與 Socket 層 IP Pinning**：確認防禦端是否在「驗證通過」後又讓底層 HTTP 函式庫自行重新發起第二次 DNS 查詢。安全基線必須在自訂 `lookup` / `connect` 掛鉤中解析一次 DNS、檢查所有回傳之 IPv4/IPv6 紀錄皆不屬於保留網段（`0.0.0.0/8`、`10.0.0.0/8`、`100.64.0.0/10`、`127.0.0.0/8`、`169.254.0.0/16`、`172.16.0.0/12`、`192.168.0.0/16`、`::1/128`、`fc00::/7`、`fe80::/10`），並直接鎖定該 IP 建立連線。

### 3. Web Cache Poisoning / Deception 與 WAF 繞過（Ch11, Ch14）
- [ ] **Unkeyed Header 與參數投毒**：附加 Cache Buster（`?cb=rand`）測試 `X-Forwarded-Host`、`X-Forwarded-Scheme`、`X-Original-URL`、`X-Rewrite-URL` 是否影響回應中之靜態資源 URL 或重導向位址，且該標頭未被納入 CDN/Nginx `proxy_cache_key`。
- [ ] **Web Cache Deception 路徑混淆**：在動態 API 端點後方附加靜態副檔名（如 `/v1/accounts/profile/nonexistent.css`、`/v1/accounts;foo.js`、`%2f..%2fstatic.png`），觀察源站是否忽略後綴回傳 `200 OK` 敏感個資、同時邊緣快取因匹配 `.css`/`.js` 規則而將其公開快取。
- [ ] **WAF 主體檢查截斷（Oversized Body Padding）**：檢查 WAF（如 ModSecurity `SecRequestBodyNoFilesLimit 8192` 且搭配 `ProcessPartial`）與後端 Body Parser（如 Express `100 KiB` 上限）的長度落差。在 JSON/Form 前段填充超過 `8,192 bytes` 的無害字元，將攻擊 Payload 置於截斷線之後。
- [ ] **Content-Type / Charset 與參數汙染（HPP）**：測試 `charset=ibm037` / `utf-16be`、`multipart/form-data` 邊界變形，以及同名參數重複傳遞時 WAF（讀第一個）與後端框架（Express 轉陣列、PHP/Go 讀特定位置）的取值分歧。
- [ ] **限流器（Rate Limiter）信任鏈破口**：確認應用程式是否誤設 `app.set('trust proxy', true)` 導致無條件信任客戶端偽造的 `X-Forwarded-For`、`X-Real-IP`、`Forwarded`；測試路徑大小寫（`/v1/Auth/OTP`）、尾斜線或尾隨空白是否產生獨立的限流計數鍵。

---

## 二、身分驗證、企業 SSO 與多租戶授權（Ch04–Ch07）

### 1. JWT、OAuth 2.0 / OIDC 與會話管理（Ch04）
- [ ] **JWT 演算法強制白名單**：白箱確認驗簽函式是否顯式鎖定 `algorithms: ['RS256']`。黑箱測試 `alg: "none"`（含大小寫變體）與 `RS256 → HS256` 演算法混淆（擷取 `/.well-known/jwks.json` 公鑰轉為精確 PEM 位元組作為 HMAC 密鑰簽署 Token）。
- [ ] **JWT Header 動態參數注入（`kid` / `jku` / `x5u`）**：
  - `kid`：測試目錄穿越（`../../../../dev/null` 搭配空密鑰簽章）、SQL 注入或命令注入。
  - `jku` / `x5u`：確認是否嚴格限制白名單網域並走防 SSRF 通道；檢查 JWKS 快取（如 NexusPay 基準 `300 s`）在金鑰輪換或撤銷時是否存在過期金鑰重放視窗。
- [ ] **JWT 聲明（Claims）完整性**：確認除了驗簽與 `exp`（如基準 `900 s`）外，是否嚴格驗證 `iss`、`aud` 與業務上下文一致，防止跨服務（Cross-Service）Token 混用。
- [ ] **OAuth 2.0 `redirect_uri` 與 `state` / PKCE**：測試 `redirect_uri` 是否存在前綴比對繞過（`https://app.example.com.evil.com`）、目錄穿越（`/oauth/callback/../../open-redirect`）或參數保留；確認授權流程強制綁定不可預測之 `state` 與 PKCE（`code_challenge_method=S256`）。
- [ ] **Refresh Token 輪換競爭（Rotation Race）**：以單封包或高併發同時送出多個相同 `refresh_token`，確認資料庫是否使用單一原子更新（`UPDATE refresh_tokens SET used = true WHERE token_hash = $1 AND used = false RETURNING *`）並實作 Token Family 異常重用即全家族撤銷。

### 2. SAML 2.0、WebAuthn 與 MFA 狀態機（Ch05）
- [ ] **XML Signature Wrapping（XSW #1–#8）**：檢查 SAML SP 在驗證 `<ds:Signature>` 後，是否直接對整份 XML Document 執行全域查詢（如 `getElementsByTagName("NameID")[0]` 或 `//saml:Assertion`），而非強制只從已通過簽章校驗的 `<ds:Reference URI="#id">` 節點子樹內提取身分聲明。
- [ ] **XML Canonicalization（C14N）註解截斷**：測試在 `<saml:NameID>` 內插入 XML 註解（如 `admin@nexuspay.example<!-- -->.evil.com`），確認解析器取值使用的是完整文字節點拼接而非遭註解截斷的第一段字串。
- [ ] **Assertion ID 防重放與 Recipient / Audience 綁定**：確認 SP 在 `NotOnOrAfter` 時間窗內將已消費的 `Assertion/@ID` 寫入 Redis 唯一快取阻止重放，且拒絕未授權的 IdP-initiated 無 `InResponseTo` 登入。
- [ ] **WebAuthn / Passkey 驗證邊界**：確認註冊與驗證階段之 `challenge` 為密碼學隨機、單次消費且強綁定當前 `user_id` 會話；嚴格核對 `clientDataJSON.origin`、`authData.rpIdHash`、`User Present (UP)` 與 `User Verified (UV)` 位元旗標。
- [ ] **MFA 狀態機跳步**：測試完成第一階段密碼驗證取得半認證 Token（Pre-Auth Token）後，能否直接攜帶該 Token 存取業務 API，或在 MFA 驗證請求中替換 `user_id`、重放舊 OTP、利用未綁定帳號的速率限制暴力破解 6 位數驗證碼。

### 3. 多租戶授權矩陣（BOLA / BOPLA / BFLA）與非 REST 協定（Ch06, Ch07）
- [ ] **BOLA（物件層級授權）與跨租戶路徑參數混用**：建立「角色 × 租戶 × 端點」授權矩陣。測試以租戶 B 的有效 JWT 存取 `/v1/tenants/{tenant_B}/accounts/{account_A}`（利用路徑只驗 `tenant_B == jwt.tid`，但底層 SQL 僅用 `WHERE id = account_A` 查詢而漏加 `AND tenant_id = jwt.tid` 的破口）。
- [ ] **BOPLA（屬性層級授權 / Mass Assignment）**：於 `POST` / `PATCH` / `PUT` 請求主體注入未列於前端表單的敏感欄位（如 `role: "admin"`, `tenantId: "..."`, `isVerified: true`, `feeRate: 0`, `balanceCents: 999999`）；同時檢視 `GET` 回應是否將完整資料庫 ORM Entity 直接序列化回傳而外洩雜湊或密鑰欄位。
- [ ] **BFLA（功能層級授權）與管理路由探測**：以低權限角色（如 `merchant_operator`）測試管理員端點、切換 HTTP Method（`GET` / `POST` / `PUT` / `DELETE`）、附加 `X-HTTP-Method-Override`，並檢查啟動期是否實施全域 Fail-Closed 路由策略斷言（見 Ch34）。
- [ ] **GraphQL 深度、批次放大與 Resolver 授權**：
  - 檢查是否關閉生產環境 Introspection 與未設防的 Field Suggestion。
  - 測試單一 Query 內塞入 `20+` 個 Alias（如 `a1: verifyPin(...)`, `a2: verifyPin(...)`）能否繞過 HTTP 層 Rate Limiter，或結合巢狀深度（突破基準 `8` 層／批次 `20` 個操作上限）造成 `20 × 4^5 = 20,480` 級別的 Resolver 放大 DoS。
  - 確認授權檢查位於每一個 GraphQL Field / Edge Resolver 或 DataLoader 內部，而非僅放在頂層 Query 入口。
- [ ] **gRPC 與 WebSocket（CSWSH）邊界**：
  - gRPC：檢查是否意外開啟 Server Reflection；確認每個 Unary 與 Streaming Interceptor 皆驗證 Metadata 中的 JWT 與租戶權限；檢查 Protobuf `repeated` 欄位長度上限與整數轉型。
  - WebSocket：檢查 HTTP Upgrade 握手是否僅依賴 Cookie 卻未驗證 `Origin` 白名單與單次短效 Ticket（如 Redis `TTL = 30 s`），防止跨站 WebSocket 劫持（CSWSH）；確認連線建立後的每一則 `subscribe` / `message` 訊框均重新核對 `session.tenantId`。

---

## 三、注入家族、複合解析器、客戶端與密碼學／AI 邊界（Ch08–Ch10, Ch13, Ch15, Ch16）

### 1. 注入家族與現代 ORM 殘留面（Ch08）
- [ ] **ORM 動態識別符與 Raw Escape Hatch**：白箱搜尋 Prisma / TypeORM / Knex / Sequelize 中的 `$queryRawUnsafe`、`query()`、`whereRaw`、`orderByRaw`，以及動態傳入 `orderBy`、`select`、`groupBy` 欄位名稱之處；黑箱以二分搜尋時間盲注或布林條件差（如 `CASE WHEN (...) THEN id ELSE amount END`）驗證。
- [ ] **NoSQL 與 Redis 協議／Lua 注入**：檢查 JSON 查詢物件是否允許注入 `{"$ne": null}`、`{"$gt": ""}`、`{"$where": "..."}`；檢查拼接至 Redis 鍵名或佇列參數的輸入是否可夾帶 `\r\n`（RESP 協議注入）或傳入 `redis.eval()` 觸發 Lua 沙箱逃逸。
- [ ] **OS Command Injection 與參數注入（Argument Injection）**：
  - 禁止使用會啟動 Shell 的 `child_process.exec` / `system` / `popen`。
  - 即使已改用不經 Shell 的 `execFile` / `spawn`，仍須檢查使用者輸入是否可由 `-` 或 `--` 開頭（如 `--upload-pack=...`、`--output=...`）被目標執行檔解析為命令列旗標；外部參數前必須加上 `--` 終止旗標解析並強制驗證格式。
- [ ] **SSTI（伺服器端模板注入）**：定位動態將使用者字串傳入 `render_template_string`、`ejs.render`、`Handlebars.compile`、`Nunjucks.renderString` 的呼叫點，而非將使用者資料作為已編譯模板的 Context 變數傳入。

### 2. 檔案處理、解壓縮與複合解析器（Ch09）
- [ ] **Path Traversal 與前綴比對陷阱**：檢查路徑拼接後是否以 `path.resolve(BASE_DIR, userInput)` 正規化，並確認檢查條件為 `resolvedPath.startsWith(BASE_DIR + path.sep)`（注意：若漏加結尾 `path.sep`，`/app/uploads-secret/key.pem` 會繞過 `.startsWith("/app/uploads")`）。
- [ ] **Zip Slip 與 Tar Symlink 兩階段逃逸**：審計解壓縮迴圈是否逐一驗證每個 Entry 的正規化目標路徑不得跳出目標目錄，並明確拒絕封存檔內的符號連結（Symlink）、硬連結（Hardlink）與特殊裝置檔。
- [ ] **XXE（XML 外部實體與參數實體 OOB 外帶）**：檢查所有 XML / SOAP / SAML / SVG / DOCX / XLSX 解析器是否顯式禁用 `DOCTYPE` 宣告、外部一般實體與外部參數實體（`%entity;` 搭配外部 DTD）。
- [ ] **Headless Browser PDF 渲染與影像委派（ImageMagick / Ghostscript）**：若系統將商戶輸入的 HTML / SVG / Markdown 交由 Headless Chrome 或 `wkhtmltopdf` 轉為 PDF，測試 `<iframe src="http://169.254.169.254/...">`、`<script>` 與 `file:///etc/passwd` 本地讀取；檢查影像處理管線是否使用嚴格的 `policy.xml` 停用高危 Coder並限制記憶體配額。

### 3. 瀏覽器安全模型、DOM 與 Node.js 執行時期（Ch10, Ch13）
- [ ] **CORS 動態反射與憑證濫用**：檢查伺服器在回傳 `Access-Control-Allow-Credentials: true` 時，是否直接反射請求的 `Origin`、使用錯誤的正則（如 `/nexuspay\.com$/` 漏錨點開頭或未跳脫 `.`），或允許 `Origin: null`（可由沙箱 `iframe` 觸發）。
- [ ] **`postMessage` 跨視窗攻擊鏈**：在前端程式碼搜尋 `addEventListener("message", ...)`。確認接收端是否嚴格比對 `event.origin === "https://expected.origin"`，以及發送端 `targetWindow.postMessage(secret, targetOrigin)` 是否禁止使用 `"*"` 萬用字元。
- [ ] **CSPT（Client-Side Path Traversal）與 Strict CSP**：檢查前端 `fetch(\`/api/items/\${param}\`)` 的 `param` 是否來自 URL Query / Hash 且未做 `encodeURIComponent`，能否透過 `../../other-endpoint` 劫持攜帶憑證的 API 回應；確認 CSP 採用 Nonce-based 或 Hash-based 策略，不依賴包含 JSONP / Angular 舊版端點的寬鬆網域白名單。
- [ ] **Prototype Pollution 與 RCE Gadget Chain**：搜尋遞迴物件合併（`merge`、`extend`、`clone`）、路徑賦值（`set(obj, path, val)`）與 Query Parser。確認是否攔截 `__proto__`、`constructor`、`prototype` 鍵名，或使用 `Object.create(null)` / `Map` 並於 Node.js 啟動參數加上 `--disable-proto=throw`；排查遭汙染後可觸發的 `child_process.fork`/`spawn`（`shell`, `env.NODE_OPTIONS`）與模板引擎 Gadget。
- [ ] **不安全反序列化與 ReDoS**：禁止對不可信輸入呼叫 `node-serialize`、未限制 Schema 的 YAML `load()`、Python `pickle`、PHP `unserialize`；掃描所有接受外部輸入的正則表達式是否含巢狀量詞（如 `^(a+)+$`），必要時替換為線性時間引擎 `re2` 並限制輸入長度。

### 4. 密碼學實作破口與 AI / LLM Agent 邊界（Ch15, Ch16）
- [ ] **AES-CBC Padding Oracle 與 ECB 模式**：禁止在任何新系統使用 AES-ECB 或自建未先驗證 MAC 的 AES-CBC（Mac-then-Encrypt / Decrypt-then-Verify）。若維護舊系統，確認密文在進入解密函式前必先以 Encrypt-then-MAC 驗證完整性，且所有驗簽／填充錯誤均回傳完全相同的狀態碼、回應內容與處理時間。
- [ ] **AES-GCM `96-bit` Nonce 唯一性與 AAD 綁定**：確認 AES-GCM（區塊 `128 bits`、標準 Nonce `96 bits`）絕不使用固定 Nonce、可預測計數器重設或在同金鑰下重用 Nonce（重用一次即洩漏 `P1 ⊕ P2` 並可解出 GHASH 驗證金鑰 `H` 偽造任意密文）；確認將租戶 ID、用戶 ID 與欄位用途納入 AAD（Additional Authenticated Data）防範密文剪貼替換。
- [ ] **恆定時間比對與密碼學隨機數（CSPRNG）**：所有 HMAC 簽章（如 Webhook `X-Nexus-Signature`）、API Token 與重設密碼雜湊比對，必須先檢查位元組長度相等再呼叫 `crypto.timingSafeEqual(a, b)`；所有 Token、Nonce、OTP 與重設連結嚴禁使用 `Math.random()`（V8 `xorshift128+` 可由少數輸出完整預測內部 `128-bit` 狀態），必須使用 `crypto.randomBytes` 或 `crypto.randomUUID`。
- [ ] **LLM Indirect Prompt Injection 與確定性 Tool-Use / MCP 閘門**：
  - 盤點所有會進入 LLM Context 的外部不可信資料（發票備註、Webhook 內容、客服信件、網頁擷取、RAG 檢索區塊）。
  - **核心原則**：絕不依賴 System Prompt 叮嚀模型「不要聽從外部指令」作為安全邊界。
  - 所有 MCP Server 與 Tool-Use 呼叫（如 `issue_refund`、SQL 查詢、HTTP 請求）必須經過**獨立於 LLM 上下文之外的確定性 Policy Engine**，由當前登入會話的 JWT/Session 直接綁定 `tenant_id` 與允許的操作範圍；高風險寫入操作必須強制實施 Human-in-the-loop 確認，且 RAG 向量資料庫檢索必須在 Metadata Filter 層級強制注入 `tenant_id`。

---

## 四、高併發競爭條件與分散式狀態機（Ch12）

- [ ] **HTTP/2 Single-Packet Attack 壓測（`20` 請求 `< 1 ms` 抖動）**：針對所有涉及「額度檢查、餘額提領（如 NexusPay `10,000` 分上限）、優惠券兌換、邀請碼領取、免費試用開通、投票／按讚計數」的端點，使用單一 HTTP/2 連線扣住各 Stream 最後 `1 byte` `DATA` 訊框再於單一 TCP 封包同步釋放，實測微秒級併發視窗。
- [ ] **消滅 Check-Then-Act（先讀後寫）反模式**：白箱檢查業務程式碼是否在 `READ COMMITTED`（PostgreSQL 預設隔離等級）下先執行 `SELECT balance FROM accounts WHERE id = $1`，在應用層判斷 `if (balance >= amount)` 後再執行 `UPDATE accounts SET balance = balance - $2`。
- [ ] **資料庫條件式原子更新與 `CHECK` 約束**：確認扣款與狀態轉移改寫為單條具備前置條件的原子 SQL：
  ```sql
  UPDATE accounts
     SET balance_cents = balance_cents - $1
   WHERE id = $2
     AND tenant_id = $3
     AND balance_cents >= $1
  RETURNING balance_cents;
  ```
  並於資料表 Schema 加上 `CHECK (balance_cents >= 0)` 作為底層硬性兜底。
- [ ] **外部 RPC 移出資料庫交易鎖**：確認程式碼未在持有資料庫 Row Lock（`SELECT ... FOR UPDATE`）期間同步等待外部風控 API 或第三方支付回呼，應拆分為「建立 `PENDING` 狀態並預扣款 → 釋放 DB 連線呼叫外部 RPC → 依結果轉移為 `SETTLED` 或補償沖正（`COMPENSATED`）」之確定性狀態機。
- [ ] **原子冪等鍵（Idempotency-Key）與精度捨入**：確認寫入操作強制綁定 `(tenant_id, idempotency_key)` 資料庫 `UNIQUE` 約束（或 Redis `SET key val NX EX ttl` 搭配 Lua Token 比對解鎖）；確認所有金額運算一律使用**整數最小貨幣單位**（如整數分 `BIGINT`），嚴禁使用 IEEE 754 `float`/`double` 或不一致的 `round()` / `floor()` 造成分位差套利。

---

## 五、雲端原生、Kubernetes 與 CI/CD 供應鏈（Ch17–Ch19）

### 1. 容器隔離與 Kubernetes RBAC（Ch17）
- [ ] **Pod 安全基線（Pod Security Standards — Restricted）**：檢查 Deployment / Pod Manifest 是否存在 `privileged: true`、`hostNetwork: true`、`hostPID: true`、`hostIPC: true`、掛載敏感 `hostPath`（如 `/var/run/docker.sock`、`/proc`、`/etc`、`/`），或未設定 `allowPrivilegeEscalation: false`、`runAsNonRoot: true` 與 `capabilities.drop: ["ALL"]`（嚴禁賦予 `CAP_SYS_ADMIN`、`CAP_DAC_READ_SEARCH`、`CAP_BPF`、`CAP_SYS_PTRACE` 於生產業務容器）。
- [ ] **ServiceAccount Token 自動掛載最小化**：非必須與 Kubernetes API Server 通訊的業務 Pod，必須顯式設定 `automountServiceAccountToken: false`，防止應用層 SSRF 或任意檔案讀取直接外洩 `/var/run/secrets/kubernetes.io/serviceaccount/token`。
- [ ] **RBAC 隱蔽提權路徑審計**：盤點所有 Role / ClusterRole，檢查非管理員帳號是否擁有以下可直接等價於 Cluster-Admin 的提權原語：
  - `pods/create` 或 `deployments/create`（可建立掛載高權限 SA 或節點 `hostPath` 的 Pod）
  - `secrets/get`、`secrets/list`、`secrets/watch`（尤其針對跨 Namespace 或 ClusterRole）
  - `pods/exec`、`pods/ephemeralcontainers`
  - `impersonate`（偽冒高權限使用者／群組）
  - `bind` 與 `escalate`（突破 RBAC 防止越權授權之內建限制）
- [ ] **網路出口隔離（Egress NetworkPolicy）**：確認多租戶工作負載已部署預設拒絕之 NetworkPolicy，阻斷業務 Pod 對雲端中繼資料 IP `169.254.169.254/32`、Kubelet `:10250` 與非必要內網網段的連線。

### 2. 雲端 IAM 與中繼資料服務（Ch18）
- [ ] **強制 IMDSv2 與容器 Hop Limit**：確認所有雲端運算節點（如 AWS EC2 / EKS Node）已強制設定 `HttpTokens = required`（停用 IMDSv1 GET 請求）且 `HttpPutResponseHopLimit = 1`（防止容器內透過 SSRF 轉發 `PUT` Token 請求至宿主節點 IMDS）。
- [ ] **IAM 提權原語與信任策略審查**：
  - 搜尋包含 `iam:PassRole` 且 `Resource: "*"` 的 Policy（攻擊者可結合 `lambda:CreateFunction` / `ec2:RunInstances` / `ecs:RegisterTaskDefinition` 將高權限 Role 綁定至新工作負載竊取憑證）。
  - 檢查 `lambda:UpdateFunctionCode`、`iam:CreateAccessKey`、`iam:UpdateAssumeRolePolicy`、`iam:AttachRolePolicy`。
  - 檢查跨帳號 `sts:AssumeRole` 的 Trust Policy 是否過於寬鬆（如允許整個外部 AWS Account root 而未限制特定 Role ARN 或未強制校驗 `sts:ExternalId` 防範 Confused Deputy）。

### 3. 軟體供應鏈與 CI/CD 管線（Ch19）
- [ ] **Dependency Confusion 與安裝期腳本**：確認私有套件（npm / PyPI / Cargo）已在公開註冊表註冊名稱空間（Scoped Package 如 `@nexuspay/*`），並在 `.npmrc` / 建置設定強制指定 Scope 僅向內部 Registry 拉取；在 CI 中評估使用 `--ignore-scripts` 並審計第三方相依之 `postinstall` 與 Rust `build.rs` 變更。
- [ ] **GitHub Actions `pull_request_target` 與 Script Injection**：
  - 搜尋 `.github/workflows/*.yml` 中的 `on: pull_request_target` 或 `workflow_run`。確認在擁有寫入權限或可讀取 Secrets 的 Context 下，**絕不直接執行 `actions/checkout` 檢出外部 PR 的不可信 `head.sha`** 並執行 `npm install` / `cargo test` / `make`。
  - 確認 `run:` 腳本區塊內**絕不直接插值不可信上下文**（如 `${{ github.event.pull_request.title }}`、`body`、`head.ref`、`comment.body`、`commits[*].message`）。所有外部變數必須先透過 `env:` 注入為環境變數，再於 Shell 中以雙引號 `"$PR_TITLE"` 安全存取。
- [ ] **第三方 Action SHA 釘選與 OIDC 短效憑證**：所有外部 GitHub Actions 必須釘選至完整 `40 字元 Commit SHA`（而非易被竄改的 `@v3` / `@main` 標籤）；每個 Job 顯式設定 `permissions: contents: read` 最小權限；雲端部署全面改用 OIDC 換取短效 Token，移除長效靜態 `AWS_SECRET_ACCESS_KEY` 或全域 `NPM_TOKEN`。

---

## 六、無原始碼逆向、二進位記憶體與 Rust / C FFI 邊界（Ch20, Ch21, Ch25）

> 註：進階堆疊 ROP（`ch22`）、`ptmalloc2` 堆積原語（`ch23`）、現代 FSOP / House of Botcake（`ch24`）、V8 Ubercage（`ch26`）與 Linux 核心利用（`ch27`）為本書預留章節，此處聚焦已完稿之 ELF 解剖、無原始碼逆向與 Rust/C FFI 實戰清單。

### 1. ELF 緩解盤點與無原始碼逆向（Ch20, Ch21）
- [ ] **二進位保護基線檢核（`checksec` / `readelf`）**：拿到目標執行檔或共用函式庫（`.so` / `.node`）時，立即確認四大緩解是否全數啟用：
  - **NX（No-Execute）**：`GNU_STACK` 區段權限為 `RW`（不可含 `E`）。
  - **PIE（Position Independent Executable）**：ELF 類型為 `DYN`，配合系統 `28-bit` ASLR 熵隨機化基底。
  - **Stack Canary**：關鍵函式含 `__stack_chk_fail` 與 `fs:0x28` 校驗。
  - **Full RELRO**：包含 `BIND_NOW`，確保 `.got.plt` 在程式啟動後即標記為唯讀。
- [ ] **Ghidra 危險 Sink 逆向追蹤（XREF-first）**：面對 `strip -s` 無符號二進位檔，先在 Symbol Tree 鎖定匯入之外部高危函式（`memcpy`、`memmove`、`strcpy`、`snprintf`、`malloc`、`realloc`、`free`、`system`），利用交叉引用（XREF）逆推呼叫者。
- [ ] **結構體偏移與整數算術還原**：在反編譯視窗觀察基底指標加固定偏移（如 `[rdi + 0x0]`, `[rdi + 0x2]`, `[rdi + 0x4]`）與陣列索引位移（如 `shl eax, 3` 代表乘上 `8 bytes`），手動建立對應的 C `struct` 定義套回參數型別，檢查 `count * sizeof(item)` 是否在傳入 `malloc` 前發生 32 位元截斷或溢位。

### 2. Rust、`unsafe` 與 C FFI / N-API 跨界審計（Ch25）
- [ ] **FFI 長度算術溢位與回繞（Integer Wrap-around）**：審計所有類似 `libnexus-parse`（`8 bytes` 檔頭、`len: uint32`、上限 `65,536 bytes`）的解析邊界。確認程式絕未在檢查 `len <= 65536` 前先計算 `total = len + 8`（當 `len = 0xFFFF_FFF8` 時，32 位元無號加法回繞為 `0`，導致配置 `0` 或最小 `0x20` chunk 卻隨後拷貝巨量資料）。一律強制使用 `len.checked_add(HEADER_SIZE)`。
- [ ] **有號／無號整數隱式轉型（`u32` ↔ `i32` / `size_t`）**：檢查 Rust `as` 轉型與 C 函式簽章（如將 `u32` 轉為 `i32` 後以 `if (len < 65536)` 檢查，攻擊者傳入 `0x8000_0000` 在有號比較為負數通過檢查，隨後傳給接受 `size_t` 的 `memcpy` 被轉回巨額無號數）。建議啟用 Clippy 規則 `#![deny(clippy::cast_possible_truncation, clippy::cast_sign_loss, clippy::cast_possible_wrap)]`。
- [ ] **Rust `unsafe` Soundness 不變量**：
  - `slice::from_raw_parts(ptr, len)`：確認 `ptr` 非空（即使 `len == 0` 亦不可傳入 `null`）、已對齊，且整個 `len` 範圍在該生命週期內均為有效已初始化記憶體。
  - 嚴禁對同一塊記憶體同時建立共享參考 `&T` 與可變參考 `&mut T`（Aliasing UB），或讀取尚未完整寫入的 `MaybeUninit<T>::assume_init()`。
- [ ] **跨分配器釋放與 N-API 外部 Buffer 生命週期**：
  - 確認由 Rust `Vec`/`Box` 配置的記憶體必由 Rust 釋放，由 C `malloc` 配置的記憶體必由 C `free` 釋放，絕不跨分配器混用。
  - 在 Node.js N-API / Addon 邊界，確認背景 Worker 執行緒不會在非同步任務中持有一份指向 JS `Buffer` 內部記憶體的裸指標，而未透過 `napi_create_reference` 延長其 GC 生命週期（否則 V8 GC 回收後即引發 Worker 執行緒 UAF）。
- [ ] **Panic 跨越 FFI 邊界（Unwind across FFI）**：所有 `extern "C"` 匯出函式必須以 `std::panic::catch_unwind` 包裹頂層邏輯並轉為明確的整數錯誤碼回傳，防止 Rust Panic 跨越 C / Node.js ABI 堆疊引發未定義行為（或使用 `extern "C-unwind"` 搭配明確異常規範）。

---

## 七、CodeQL 變體分析、灰箱／混合式 Fuzzing 與 AI 輔助 0-day 工作流（Ch28–Ch32）

### 1. 靜態與變體分析（Semgrep / CodeQL）（Ch28, Ch34）
- [ ] **從單一 CVE / Bug 到變體規則（Variant Analysis）**：每當人工發現一處漏洞或閱讀近期公開 CVE Patch 時，先抽離出三元組：
  1. **Source**：攻擊者可控輸入進入點（HTTP Request、RPC 參數、FFI Buffer、檔案讀取）。
  2. **Sink**：危險操作點（Raw SQL、命令執行、`memcpy`、未綁定租戶之 DB 查詢）。
  3. **Missing Barrier / Sanitizer**：原本應存在卻被繞過或遺漏的檢查（如 `checked_add`、`TenantDbClient`、`SafeHttpClient`）。
- [ ] **降低誤報的 Barrier 工程**：在 CodeQL `TaintTracking::Configuration`（或新式 `DataFlow::ConfigSig`）中，務必將型別轉換為整數／布林值、白名單列舉比對與組織內部的 Paved Road 安全封裝函式註冊為 `isBarrier`，將規則誤報率壓至 `< 5%`。

### 2. 灰箱 Fuzzing、混合式求解與真實開源專案（Ch29–Ch31）
- [ ] **高吞吐 Fuzzing Harness 設計**：
  - C/C++：使用 `afl-clang-fast` 搭配 `__AFL_LOOP(10000)` Persistent Mode，確保單核吞吐量達到基準 `5,000+ exec/s`，且每次迴圈內完整重置全域狀態並釋放動態記憶體（防範記憶體洩漏拖垮執行速度）。
  - Rust：使用 `cargo-fuzz` 結合 `arbitrary::Arbitrary` 派生巨集實施結構感知（Structure-Aware）Fuzzing，跳過無效語法解析直接轟擊核心狀態機。
- [ ] **Sanitizers 全套掛載**：編譯 Fuzzing 目標時務必同時開啟 `ASan`（捕捉 `1-byte` 越界與 UAF）、`UBSan`（捕捉有號溢位、未對齊指標與除以零），Rust `unsafe` 模組額外執行 `cargo +nightly miri test` 檢查 Stacked Borrows / Tree Borrows 違規。
- [ ] **覆蓋率停滯診斷與 Z3 / angr 破壁**：
  - 使用 `llvm-cov` 產出 HTML 覆蓋率報告，定位被標為紅色的 0% 覆蓋深層分支。
  - 若卡在固定魔數（如 `magic == 0x4E58`）、字串關鍵字或多欄位結構：建立 AFL++ 語法字典檔（`-x dict.txt`）、開啟 `CMPLOG`（`AFL_LLVM_CMPLOG=1`），並用 `FuzzedDataProvider` 拆分輸入串流。
  - 若卡在 `32-bit` 校驗和（CRC32 / 自訂 Checksum）或複雜算術約束（純隨機猜測期望次數 `2^32 ≈ 4.29 × 10^9` 次）：切出該分支約束條件，以 Python `z3-solver`（`BitVec`）或 `angr` 在數十毫秒內解出合法的種子檔案，直接丟入 AFL++ `queue/` 目錄回灌突破。

### 3. 7 天開源專案 0-day 審計與 AI 輔助工作流（Ch32）
- [ ] **Day 1 — 攻擊面與 90 天 Git 熱點測繪**：鎖定近 90 天內高頻修改、剛完成重構、新增協定解析器或跨語言 FFI 綁定的檔案（`git log --since="90 days ago" --name-only`），畫出信任邊界圖與所有外部輸入入口。
- [ ] **Day 2 — 確定性靜態掃描初篩**：執行 Semgrep 與 CodeQL 基礎規則集，先確認專案自身的單元測試可在本地 100% 跑通（建立後續動態驗證基線）。
- [ ] **Day 3–4 — 受約束的程式碼切片（`< 1,000` 行）與 AI 假設生成**：將高風險呼叫鏈切為包含完整型別定義、常數上限與下游 Sink 的獨立切片，要求 AI 輔助審計器僅輸出「具備明確檔案行號、前置條件、Source-to-Sink 路徑與可證偽測試方式」的漏洞假設，嚴格禁止無根據的泛泛猜測。
- [ ] **Day 5–6 — 本地確定性 PoC 與 Fuzzing 實證淘汰誤報**：針對每一個候選假設，親手撰寫單元測試、Python 攻擊腳本或微型 Fuzzing Harness。**沒有在本地跑出實際越權回應、帳本不變量破壞或 ASan Stack Trace 的假設一律淘汰**，絕不提交未經實證的 AI 幻覺報告。
- [ ] **Day 7 — 影響鏈串接與協調揭露報告（CVD / GHSA）**：評估單一中低危原語能否與其他原語串接（Exploit Chaining）升級為高危影響；附上最小化可重現 PoC、CVSS v4.0 向量分析與根因修補 Patch，依專案 VDP / GHSA 管道負責任提交。
