# 第 4 章：身分驗證與會話機制破口

在微服務架構裡，工程團隊常把身分驗證拆成兩個看似乾淨的步驟：先由登入服務簽發一組憑證，再讓下游的 API 閘道與業務服務各自拿公鑰或 Session Store 驗票。只要簽章演算法用上 `RS256`（2048-bit RSA）、Access Token 的過期時間設成 `900 s`（15 分鐘），系統看起來就已經固若金湯了。

但攻擊者拆解驗證系統時，根本不會去硬撞 RSA 的數學難題，而是盯著「**系統怎麼挑選信任根、怎麼解析跳轉網址、怎麼更新會話狀態**」。只要驗證端傻傻聽從未驗證的 JWT Header 去決定該用哪種演算法或哪把金鑰，或是 OAuth 伺服器在比對 `redirect_uri` 時留了後門，乃至於 Refresh Token 在併發請求下少了單次消費的原子鎖，整道身分防線就會在密碼學毫髮無傷時當場崩潰。

---

## 從你已知的出發

為什麼系統明明採用了工業級的 `RS256` 非對稱簽章，駭客連伺服器的私鑰長什麼樣都沒看過，卻只靠公開的 `/jwks.json` 公鑰端點，就能在自己電腦上憑空簽出一張 100% 通過驗簽的 `role: "admin"` 管理員 Token？

問題出在「**誰有資格決定驗票規則**」與無狀態憑證的**快取過期時間差**。以 NexusPay 為例，API 閘道會把 Auth Service 的 JWKS 公鑰集快取在本地端（硬性 `TTL = 300 s`），並簽發有效期 `900 s` 的 `RS256` Access Token；若沒額外黑名單，後台就算緊急撤換金鑰或停權帳號，下游仍有長達 `300 s` 到 `900 s` 的時間窗會繼續放行舊票。更致命的是，JWT 的 Header（包含 `alg`、`kid`、`jku`）在驗簽通過前完全由攻擊者控制！一旦驗證程式允許未經驗證的 Header 反過來指揮伺服器「改用 `HS256` 對稱演算法」或「去讀某個路徑的金鑰檔」，攻擊者就能把公開的 RSA 公鑰當成對稱密鑰來偽造簽章，直接奪取最高權限。

---

## 機制與推導

### 攻擊者目標與實質影響

打穿身分驗證與會話機制，最直接的戰果就是拿到合法、甚至帶有管理員特權的通行證。

第一是**任意偽造身分與全面接管帳號**。利用 JWT 演算法混淆（把 `RS256` 降級成 `HS256`）或 `kid` 參數注入，攻擊者想簽誰的 `sub`、想給自己什麼 `role` 都能自己印票，商戶與管理員帳號形同虛設。

第二是**直搗核心金流業務**。一旦跨過身分檢查大門，就能直接呼叫 NexusPay 的內部帳務 API，把受害者帳戶裡的資金全部轉走或提領一空（見第 12 章）。

第三是**作為後續跨層攻擊的跳板**。手上拿著一張有效期 `900 s` 的偽造特權 JWT，就能長驅直入去打第 6 章的多租戶授權邊界，或是第 7 章的 GraphQL / gRPC 內部管理端點。

---

### JWT 驗證管線與信任根倒置

按照 RFC 7519 與 RFC 7515 的規定，一組 JWS（JSON Web Signature）格式的 JWT 是由三段 Base64URL 字串用句點 `.` 串起來的：`Header.Payload.Signature`。前面兩段 `Header` 跟 `Payload` 只是沒加密的 JSON 字串；第三段 `Signature` 則是把 `ASCII(Base64URL(Header) + "." + Base64URL(Payload))` 這段 **Signing Input** 拿去算簽章或 MAC 的結果。

一條安全的驗證管線，順序絕對不能亂：**必須先由伺服器自己的固定設定來決定「只准用哪種演算法、只認哪一把金鑰」，驗過簽章確定沒被動手腳之後，才准相信裡面的內容。**

偏偏很多早期或封裝不良的 JWT 驗證寫法，為了「自動相容多種金鑰與格式」，把這個順序完全倒過來了：

```text
+-------------------------------------------------------------------+
|  Attacker-Controlled Input: Header.Payload.Signature              |
+---------------------------------+---------------------------------+
                                  |
         (1) 還沒驗簽，就先解開 Header 看攻擊者寫了什麼！
                                  v
+-------------------------------------------------------------------+
|  Header Fields:                                                   |
|    - alg: "none" / "HS256"    --> 聽攻擊者的話切換驗簽演算法      |
|    - kid: "../../dev/null"    --> 聽攻擊者的話去讀指定檔案或資料庫|
|    - jku / jwk: attacker URL  --> 聽攻擊者的話去外部抓公鑰        |
+---------------------------------+---------------------------------+
                                  |
         (2) 拿攻擊者挑好的演算法和金鑰來驗攻擊者自己簽的票！
                                  v
+-------------------------------------------------------------------+
|  Trust Root Inverted: 驗簽當然通過 -> 伺服器乖乖相信偽造的 Claims |
+-------------------------------------------------------------------+
```

只要順序一倒置，下面這四種經典攻擊就會接連引爆。

#### 1. `alg: none` 空簽章繞過

JWS 規範裡留了一個叫 `alg: "none"` 的特殊格式，原本是用來表示「這張 Token 沒有簽章保護」。如果後端用的驗證套件沒有預設封死這個分支（或是轉小寫後放行了 `None`、`NONE`），又沒在呼叫時強制要求必帶有效簽章，攻擊者只要把 Header 改成 `{"alg":"none","typ":"JWT"}`、把 Payload 裡的 `role` 改成 `"admin"`，最後把第三段簽章清空（注意最後那個句點要留著，長得像 `Header.Payload.`），伺服器就會把它當成驗簽通過直接放行！

#### 2. 非對稱轉對稱的演算法混淆（`RS256` → `HS256`）

先看這行在無數舊版 Node.js 專案裡出現過的驗票程式碼：

```typescript
// 致命寫法：沒有限定 algorithms 白名單，套件也沒區分公鑰與對稱密鑰的型別
jwt.verify(token, publicKeyPem);
```

為什麼這行程式碼會害死人？因為在正常情況下，伺服器簽發的是 `RS256`（RSA 非對稱簽章）：登入服務用**私鑰**簽名，API 閘道讀進硬碟上的 `publicKeyPem`（**公鑰**）來驗票。

但如果底層的驗證函式在只收到一個 `publicKeyPem` 字串時，沒有檢查「這明明是一把 RSA 公鑰，不能拿來跑對稱加密」，那當攻擊者送來一張標著 `header.alg === "HS256"` 的 Token 時，驗證函式就會順著 Header 的指示切換到 `HS256`（HMAC-SHA256 對稱驗證），然後**直接把那串 `publicKeyPem` 公鑰文字當成 HMAC 的共享密鑰 $K$**，去算 $\text{HMAC-SHA256}(K, \text{Signing Input})$！

別忘了，RSA 公鑰本來就是公開給所有人看的（從 `/.well-known/jwks.json` 或公開端點就能直接抓下來轉成標準 X.509 SPKI PEM 格式）。攻擊者只要拿一模一樣的 `publicKeyPem` 位元組當作 HMAC 密鑰，在自己電腦上就能算出分毫不差的 `HS256` 簽章！

在實戰打這個漏洞時，最容易卡關的細節是**公鑰字串的每一個位元組都必須跟伺服器載入的一字不差**：
- 檔案結尾到底有沒有多一個換行字元 `\n`？（有換行是 `451 bytes`，沒換行是 `450 bytes`）
- 每一行換行是用 `LF`（`\n`）還是 `CRLF`（`\r\n`）？（9 處換行就會差上 `9 bytes`，變成 `451` vs `460 bytes`）
- 外框標頭是用 X.509 SPKI 的 `BEGIN PUBLIC KEY`，還是 PKCS#1 的 `BEGIN RSA PUBLIC KEY`？

只要差了任何一個 byte，因為長度超過 SHA-256 的 `64 bytes` 區塊大小，HMAC 第一步先跑 SHA-256 壓縮出來的衍生金鑰 $K'$ 就會天差地遠，算出來的簽章也就完全對不上了。

#### 3. `kid`（Key ID）路徑穿越與 SQL 注入

系統為了支援定期換金鑰，通常會在 JWT Header 放一個 `kid` 欄位，告訴驗證端「請用第幾號金鑰來驗我」。如果開發者沒有先用嚴格白名單（像是只准出現 UUID 或 `[a-zA-Z0-9_-]{1,64}`）檢查 `header.kid`，而是直接拿它去拼檔案路徑或 SQL 查詢，在還沒驗簽之前就會先爆出兩大漏洞：

第一種是**路徑穿越**（Path Traversal）。假設後端寫了 `fs.readFileSync(path.join('/app/keys', header.kid))` 去讀對稱密鑰檔。攻擊者只要把 `kid` 填成 `../../../../dev/null`，在 Linux 系統上讀出來的就是長度為 `0` 的空檔案（空字串 `b""`）。千萬別以為空金鑰不能算 HMAC！在標準 HMAC-SHA256 裡，傳入空金鑰 `b""` 會自動被補零到 `64 bytes` 區塊大小，接著照常算出一個固定不變的雜湊值。攻擊者只要在本地用空字串 `""` 當密鑰簽名，就能一舉通關！同理，如果指向已知開啟標準 ASLR 的 Linux 容器裡的 `/proc/sys/kernel/randomize_va_space`（內容固定是 `"2\n"`），一樣能算出完全可預測的簽章。

第二種是 **SQL 注入**。如果後端寫的是 `SELECT secret FROM signing_keys WHERE kid = '${kid}'`，然後拿查出來的 `secret` 當作 HMAC 密鑰，攻擊者只要在 `kid` 塞進 `' UNION SELECT 'my_custom_key' -- `，資料庫就會乖乖吐回 `'my_custom_key'`，讓攻擊者用自己挑的密碼完成驗簽。

#### 4. 自帶 `jwk` 公鑰與 `jku` 快取投毒

JWS 規範裡還有兩個危險的 Header 欄位：一個叫 `jwk`（直接在 Header 裡附上公鑰本身），另一個叫 `jku`（JWK Set URL，告訴伺服器去哪個網址下載公鑰集）。

如果驗證端笨到直接相信 Header 裡內嵌的 `jwk`，攻擊者只要自己生一對 RSA-2048 金鑰，用自己的私鑰簽名、再把自己的公鑰塞進 `jwk` 送過去，就等於「自己發證自己審」。

更隱蔽的是 **`jku` 快取投毒**。要是伺服器不檢查 `jku` 的網域就傻傻發 HTTP 請求去抓金鑰，而且抓回來之後，直接用裡面的 `kid` 當 key 寫進跟正常驗證共用的全域快取表（在 NexusPay 裡這個本地快取的 `TTL = 300 s`），那攻擊者只要架一個惡意網址回傳與官方金鑰同名的 `kid`，就能把官方快取裡的公鑰掉包成自己的公鑰，在接下來的 `300 s` 內通殺整個系統。

---

### Worked Example：把 NexusPay 的 `RS256` 公鑰轉成 `HS256` 偽造管理員 JWT

現在我們直接拿 NexusPay 的基準參數（`RS256` 2048-bit RSA、有效期 `900 s`），一步步推算怎麼把公開的公鑰變成偽造管理員 Token 的密鑰。

假設我們從 NexusPay 的公開端點 `GET /.well-known/jwks.json` 抓到了 RSA-2048 公鑰（模數 $n$ 長 `256 bytes`、指數 $e = 65537$），把它轉成標準 X.509 SPKI PEM 格式後，連同最後一行的換行字元 `\n` 總共是 **`451 bytes`**。而後端 API 閘道剛好用了前面提過的問題寫法，既沒鎖定 `['RS256']`，也允許直接拿這塊 `451 bytes` 的 Buffer 去驗 `HS256`：

```text
[1] 構造偽造 Header 與 Payload（對齊 NexusPay 900 s 有效期基準）
Header JSON (27 bytes):
  {"alg":"HS256","typ":"JWT"}
  -> Base64URL (無 '=' 填充, 36 bytes):
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9

Payload JSON (67 bytes, exp - iat = 1795140900 - 1795140000 = 900 s):
  {"sub":"usr_1042","role":"admin","iat":1795140000,"exp":1795140900}
  -> Base64URL (無 '=' 填充, 90 bytes):
  eyJzdWIiOiJ1c3JfMTA0MiIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTc5NTE0MDAwMCwiZXhwIjoxNzk1MTQwOTAwfQ

[2] 組合 Signing Input
  Length = 36 + 1 ('.') + 90 = 127 bytes
  Signing Input:
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfMTA0MiIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTc5NTE0MDAwMCwiZXhwIjoxNzk1MTQwOTAwfQ

[3] 以 451-byte PEM 公鑰位元組計算 HMAC-SHA256
  K = readFileBytes("public.pem")  // 長度 451 bytes: "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----\n"
  因 len(K) = 451 > SHA-256 block size (64 bytes):
    HMAC 先計算 K' = SHA-256(K) (32 bytes)，右側補 32 個 0x00 成為 64 bytes
  輸出 MAC = HMAC-SHA256(K, Signing Input) -> 32 bytes (256 bits)
  -> Base64URL (ceil(32 * 8 / 6) = 43 bytes，對某組實際產生的 2048-bit RSA SPKI PEM):
  AP23Qv1HqS8svbaRv6Gt6jP2vehKFe19BtvPaxrQAfE

[4] 驗證條件對照
  環境條件                                   | 攻擊結果
  -------------------------------------------+----------------------------------------------------
  未鎖定演算法且允許以該 PEM 緩衝區驗 HS256  | 通過驗簽；若下游直接依 role 授權則取得 "admin" 權限 (樣本宣告 exp - iat = 900 s)
  PEM 少一個結尾 '\n'                        | 密鑰變為 450 bytes，K' 完全不同，驗簽失敗 (401)
  鎖定 ['RS256']                             | 拒絕 alg=HS256，在驗簽前直接回傳 Invalid algorithm
```

看完這段實算，你會發現整場攻擊裡**根本沒有半點「破解 RSA 私鑰」的成分**。純粹是因為驗證端沒把演算法白名單與金鑰型別鎖死，讓攻擊者能指鹿為馬，拿大家都看得到的公鑰當成對稱密鑰，簽出一張通行無阻的管理員憑證。

---

### OAuth 2.0 / OIDC 授權碼劫持與跳轉破口

當系統接上 OAuth 2.0 或 OpenID Connect（OIDC）做第三方登入時，戰場就從單一 Token 擴大到了**使用者瀏覽器**、**客戶端網站**（Client）與**授權伺服器**（Authorization Server）三方之間的跳轉狀態機。

根據 RFC 6749 與最新的 **RFC 9700**（OAuth 2.0 Security Best Current Practice），最常用的 Authorization Code Flow 要能安全運作，全靠守住兩條鐵律：
1. **授權碼（`code`）只准被送到事先白名單登記好的那一個 `redirect_uri`。**
2. **最後拿著 `code` 回呼的那個人，必須跟一開始發起登入的是同一個瀏覽器會話（靠 `state` 與 PKCE 綁定）。**

只要這兩條鐵律有一條沒鎖緊，帳號就會在跳轉過程中被半路攔截。

#### 1. `redirect_uri` 比對太寬鬆與開放重導向串接

使用者點下「同意授權」後，授權伺服器會回一個 `302 Found`，叫瀏覽器跳轉去 `redirect_uri?code=xyz&state=123`。

很多開發者在授權伺服器檢查 `redirect_uri` 時，沒做**完整字串一字不差的精確比對**（Exact String Matching），而是圖方便寫了前綴比對（像是 `url.startsWith("https://app.nexuspay.local/callback")`）或寬鬆的正規表達式。這馬上會引來三種攻擊套路：

- **路徑穿越串接開放重導向**：如果只檢查開頭是 `https://app.nexuspay.local/callback`，攻擊者可以把網址改成 `https://app.nexuspay.local/callback/../logout?next=https://evil.example`。它完全符合開頭前綴檢查，但瀏覽器一跳過去就會把 `..` 消掉，改打到同網站底下的 `/logout` 開放重導向端點，接著順手把整串 `?code=xyz` 透過第二次 `302` 直接轉送給駭客的伺服器！
- **透過 `Referer` 標頭偷漏 `code`**：就算跳過去的同源頁面（例如 `/callback/../help`）不會自動跳轉，只要那個頁面上有載入任何外站圖片或腳本，而且沒設嚴格的 `Referrer-Policy: no-referrer`，瀏覽器去抓外站圖片時，就會把網址列上帶著 `?code=xyz` 的完整網址塞進 `Referer` 標頭送出去。
- **不同 URL 解析器各說各話**：要是授權伺服器用舊版 RFC 3986 規則檢查網址主機名，瀏覽器卻照著 WHATWG URL 標準去解讀反斜線 `\` 與 `@` 符號，就會發生「伺服器檢查以為是自己人，瀏覽器跳過去卻連到駭客網域」的慘劇（我們在第 11 章會專門拆解 URL 解析器差異）。

#### 2. 漏驗 `state`（Login CSRF）與 PKCE 降級

那如果不偷別人的 `code`，反過來**把駭客自己的 `code` 塞給受害者用**呢？

這就是漏掉 `state` 參數檢查時會爆出的 **Login CSRF**（強制帳號綁定）。假設客戶端在 `/v1/auth/oauth/callback` 收回呼時，沒檢查網址上的 `state` 是不是跟當前瀏覽器 Cookie 裡的隨機碼一致：攻擊者可以先用自己的 Google / GitHub 帳號按登入，在拿到 `code` 的瞬間先攔下來不用掉，然後把這個 `/v1/auth/oauth/callback?code=<駭客的code>` 連結貼給已登入 NexusPay 的受害者點。受害者一點下去，他的 NexusPay 商戶帳號就神不知鬼不覺地跟駭客的 Google 帳號綁在一起了！從此駭客只要用自己的 Google 帳號按一鍵登入，就能直接進到受害者的商戶後台。

至於在 SPA 前端或手機 App 這種沒辦法藏好 `client_secret` 的公開環境，RFC 7636 規定必須強制使用 **PKCE**：發起登入前先在本地生一組隨機密碼 `code_verifier`，算成雜湊值 `code_challenge = BASE64URL(SHA256(code_verifier))` 加上 `code_challenge_method=S256` 先交給授權伺服器保管；等最後要拿 `code` 換 Token 時，必須交出原本那組 `code_verifier` 核對無誤才給換。

這裡有兩個常見破口：第一是伺服器根本沒強制要求帶 PKCE，導致半路攔到 `code` 的人直接就能把 Token 換走；第二是伺服器居然允許把演算法降級成 `code_challenge_method=plain`（也就是不雜湊，`code_challenge` 直接等於 `code_verifier`），那在前面能看到請求網址的人早就知道謎底了，PKCE 當場形同虛設。

---

### 會話生命週期與 Refresh Token 的併發雙花

就算你完全不用無狀態 JWT，改用最傳統的伺服器端 Session（像 Express + Redis Session Store），或是改用「短效 Access Token + 長效 Refresh Token」的標準雙層設計，只要在更新狀態時忘了考慮**原子性**，一樣會被打穿。

#### 1. Session Fixation（會話固定攻擊）

有些系統在一開始還沒登入時，就會先發給瀏覽器一個匿名的 Session ID（或者允許從網址參數、預先塞入的 Cookie 讀取 `sid`）。如果使用者輸入完帳號密碼跟 MFA 驗證通過後，後端程式只寫了一句 `req.session.userId = user.id`，卻忘了呼叫 `req.session.regenerate()` 換發一組全新的 Session ID，那就糟了——攻擊者只要在登入前先想辦法把一組自己知道的 `sid` 塞給受害者，等受害者乖乖登進去之後，攻擊者拿著手上一模一樣的舊 `sid`，當場就升格成已登入狀態。

#### 2. Refresh Token 輪換競爭（Rotation Race Condition）

為了兼顧無狀態 Access Token 的速度與隨時撤銷的能力，現在業界最推薦的做法是 **Refresh Token Rotation + Reuse Detection**（輪換加上重用偵測）：每當你拿第一代 `RT_1` 來換新的 Access Token 時，`RT_1` 當場作廢，伺服器發給你第二代 `RT_2`；萬一之後有人又拿已經作廢的 `RT_1` 來換票，系統就知道這張憑證可能被偷了，會立刻把整個家族（`family_id`）底下所有的 Refresh Token 全部撤銷踢下線！

聽起來無懈可擊對吧？但看看下面這段「先查再改」的後端實作：

```typescript
// 致命的 TOCTOU 時間差：併發請求能同時通過檢查，換出兩條合法分支！
const record = await db.refreshTokens.findOne({ tokenHash, revoked: false });
if (!record) throw new UnauthorizedError('Invalid or reused token');
// <--- 只要兩筆併發請求在同一毫秒抵達這裡，兩邊都會拿到 revoked: false！
await db.refreshTokens.markRevoked(record.id);
const nextToken = await db.refreshTokens.createNew(record.familyId);
```

看到第 1 章講過的 **TOCTOU**（檢查與使用分離）了嗎？當攻擊者（或是使用者開了兩個瀏覽器分頁同時在背景刷 Token）在幾毫秒內同時送出兩筆帶著同一個 `RT_1` 的 `POST /v1/auth/refresh` 請求，兩筆請求在第一步 `findOne` 時都會讀到 `revoked: false`，接著各自往下跑，分別換出兩張合法的第二代憑證 `RT_2a` 跟 `RT_2b`！

這下子，「一張 Refresh Token 只能用一次」的鐵律當場被打破，攻擊者就能握著分岔出來的另一條合法分支長期潛伏在系統裡。怎麼用 HTTP/2 Single-Packet Attack 在 `< 1 ms` 內百發百中打出這種併發漏洞，我們會在第 12 章完整揭曉；至於企業 SSO 常用的 SAML 2.0 XML 簽章繞過與 WebAuthn，則留到下一章拆解。

---

## 故障模式與防禦

把前面看過的七種認證與會話破口攤開來，每一個都有非常明確的工程修補底線：

| 常見破口 | 為什麼會出事 | 被打穿的後果 | 真正能鎖死邊界的防線 |
|---|---|---|---|
| **JWT `alg: none` 與 `RS256→HS256`** | 驗票函式聽從未驗證的 `header.alg` 去挑演算法，還拿公鑰去跑 HMAC | 不需私鑰就能自己印出 `admin` Token | 驗票端**硬性寫死** `algorithms: ['RS256']`，並改用 `jose` 這種在型別層就嚴格區分非對稱公鑰與對稱密鑰的現代套件 |
| **`kid` 路徑穿越與 SQL 注入** | 直接拿 `header.kid` 去拼檔案路徑或 SQL 語句 | 讀 `/dev/null` 用空字串簽過 HMAC，或靠 SQL 注入自訂密鑰 | 對 `kid` 強制跑正規表達式白名單（如 UUIDv4），而且只准在預先載入記憶體的 `Map` 裡查表，絕不直接碰檔案或資料庫 |
| **`jku` / `jwk` 信任根投毒** | 相信 Header 內嵌的 `jwk` 或照著 `jku` 網址去抓公鑰寫入共用快取 | 駭客自備公私鑰驗簽，並污染長達 `300 s` 的本地 JWKS 快取 | 完全忽略封包裡的 `jwk` 與 `jku`；只准從伺服器設定檔寫死的唯一內部 OIDC 網址抓 JWKS |
| **OAuth `redirect_uri` 比對太鬆** | 只比對網址開頭前綴，或先消掉 `..` 正規化後才比對 | 授權碼 `code` 被開放重導向或 `Referer` 標頭拐去駭客網站 | 對已註冊的 `redirect_uri` 做**一字不差的完整字串相等比對**（Exact Match），並加上 `Referrer-Policy: no-referrer` |
| **漏驗 `state` 或 PKCE 降級** | 回呼時沒核對 Cookie 裡的 `state`，或允許 `code_challenge_method=plain` | 受害者帳號被強制綁到駭客第三方登入；攔到 `code` 直接換走 Token | 強制把高熵隨機 `state` 綁定 HttpOnly Cookie；全面強制要求 PKCE `S256`，不帶或填 `plain` 一律拒收 |
| **無狀態 JWT 無法緊急撤銷** | 只靠 `900 s` 過期時間與 `300 s` JWKS 快取，沒有即時撤銷通道 | 員工離職停權或改密碼後，舊 Token 還能繼續狂打 API 長達 `15` 分鐘 | 遇到改密碼、登出、停權或大額提領時，把 Token 的 `jti` 寫進 Redis 短期黑名單（只存到該 Token 的 `exp` 到期為止） |
| **Refresh Token 併發雙花** | 把「檢查有沒有用過」跟「標記為已使用」拆成兩次資料庫查詢 | 併發請求同時換出多張合法的新 Refresh Token | 改用資料庫單條原子更新 `UPDATE ... SET used = true WHERE token_hash = $1 AND used = false RETURNING *` |

### 防禦實作範本：把 NexusPay 驗票中介層一次鎖死

要把上面這些原則落實到程式碼裡，核心觀念只有一個：**所有的安全規則（用哪種演算法、去哪抓公鑰、誰簽的、能活多久）全部由伺服器端的固定常數說了算，絕不看 Token Header 的臉色。**

下面是用 Node.js 22 搭配現代 `jose` 套件寫出的標準驗票實作，同時把 NexusPay 的 `300 s` JWKS 快取、`900 s` 有效期上限跟 Redis `jti` 撤銷檢查全部鎖在一起：

```typescript
import { createRemoteJWKSet, jwtVerify } from 'jose';

// 1. 寫死唯一的內部可信 JWKS 網址，完全不理會 Token Header 裡的 jku 或 jwk
const NEXUS_JWKS = createRemoteJWKSet(
  new URL('https://auth.nexuspay.internal/.well-known/jwks.json'),
  { cacheMaxAge: 300_000 } // 對齊全書基準：300 s (5 分鐘) 本地 JWKS 快取
);

export async function verifyNexusAccessToken(token: string) {
  // 2. 硬性鎖死只准 RS256；jose 套件也會在型別層擋掉拿 RSA 公鑰去驗 HMAC 的荒唐行為
  const { payload } = await jwtVerify(token, NEXUS_JWKS, {
    algorithms: ['RS256'],
    issuer: 'https://auth.nexuspay.internal',
    audience: 'nexuspay-api',
    maxTokenAge: '900s', // 距離簽發時間 iat 絕不超過 900 s
  });

  // 3. 明確檢查 exp 與 iat 都是正數，且壽命不超過 900 s (15 分鐘)
  if (
    typeof payload.exp !== 'number' ||
    typeof payload.iat !== 'number' ||
    payload.exp <= payload.iat ||
    payload.exp - payload.iat > 900
  ) {
    throw new Error('Invalid token lifetime claims');
  }

  // 4. 強制要求 jti，並查 Redis 黑名單確認這張票有沒有被提前撤銷
  if (!payload.jti || (await isTokenRevokedInRedis(payload.jti))) {
    throw new Error('Token revoked or missing jti');
  }
  return payload;
}
```

至於 Refresh Token 的換票邏輯，則要把「檢查 `used = false`」跟「改成 `used = true`」壓進同一條 PostgreSQL 的 `UPDATE ... RETURNING` 原子語句裡，而且要特別小心一個交易回滾的陷阱：

在 PostgreSQL 預設的 `READ COMMITTED` 隔離等級下，當你執行 `UPDATE refresh_tokens SET used = true WHERE token_hash = $1 AND used = false AND revoked = false AND expires_at > NOW() RETURNING *` 時，資料庫會自動對那一行加上列級排他鎖（Row-Level Exclusive Lock）。就算有 5 筆併發請求在同一毫秒衝進來，也只有第 1 筆能成功更新並拿到回傳的 `1` 列資料；後面排隊的 4 筆等鎖放開後重新檢查 `WHERE used = false`，全部只會拿到 `0` 列！

拿到 `0` 列的時候，程式就立刻去查這張 `token_hash` 到底在不在：如果紀錄存在、而且 `used` 已經是 `true` 了，就代表有人拿用過的舊票來重刷（Token Reuse）！這時要馬上執行 `UPDATE refresh_tokens SET revoked = true WHERE family_id = $1` 把整個家族的票全廢掉，而且**千千萬萬記得要先執行 `COMMIT` 把這次撤銷存進資料庫，最後才往外丟 `401 Unauthorized` 給前端**（如果你還沒 `COMMIT` 就直接 `throw new UnauthorizedException()`，外層的交易管理員一看到例外自動幫你 `ROLLBACK`，你剛剛辛苦撤銷整個家族的動作就跟著一起被還原取消了！）。另外，關於比對 HMAC 或密碼雜湊時為什麼一定要用 `crypto.timingSafeEqual` 防止時序側通道偷猜字元，我們會在第 15 章詳細推導。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

這次實驗我們要在本地的 NexusPay 測試環境（Node.js 22 + PostgreSQL 16）裡親手打穿並修補四個破口：先玩 JWT 的 `RS256 → HS256` 演算法混淆與 `kid` 路徑穿越，接著測試 OAuth `redirect_uri` 路徑繞過，最後用併發腳本打出 Refresh Token 的雙花並把它修成原子更新。

### 步驟 1：實測 JWT 演算法混淆與 `kid` `/dev/null` 繞過

1. 啟動本地 NexusPay Auth 與 Gateway 容器，打 `GET /.well-known/jwks.json` 把 `RS256` 公鑰抓下來，轉成標準的 X.509 SPKI PEM 字串（先印出 `Buffer.byteLength(pem)` 確認含結尾換行剛好是 `451 bytes`）。
2. 對著還沒鎖定 `algorithms` 的舊版驗票路由，用這 `451 bytes` 的公鑰當作 HMAC 密鑰，自己簽一張 `alg: "HS256"`、`role: "admin"` 的偽造 Token 送過去，驗證能不能直接拿到管理員帳本資料。
3. 對著另一個用檔案系統讀 `kid` 的測試端點，把 Header 裡的 `kid` 填成 `../../../../dev/null`，並用空字串 `""` 當密鑰算出 HMAC-SHA256 簽章送出，確認能順利過關。
4. 把後端驗票函式換成前面寫的 `jose` `jwtVerify`（鎖死 `['RS256']` 並加上 `kid` 的 `/^[a-zA-Z0-9_-]{1,64}$/` 記憶體查表），重新打一次上面兩組攻擊封包，確認全部被擋下來回傳 `401 Unauthorized`。

### 步驟 2：實測 OAuth `redirect_uri` 繞過與 Refresh Token 原子化修補

1. 在本地模擬的 `/oauth/authorize` 端點上，試著把 `redirect_uri` 設成 `/callback/../health?next=https://attacker.local` 這種帶了 `..` 的路徑，看看只檢查前綴的授權伺服器是不是照常放行並把 `code` 洩漏出去。
2. 寫一小段併發測試腳本（例如用 `Promise.all` 同時發 5 個 `fetch`），帶著同一張還沒用過的 `refresh_token` 同時打向 `POST /v1/auth/refresh`。觀察舊版「先 `SELECT` 再 `UPDATE`」的寫法是不是會一口氣吐出好幾組成功的新 Token。
3. 把換票 SQL 改寫成單條帶 `WHERE used = false` 的原子 `UPDATE ... RETURNING *`，並補上「重用時先 `COMMIT` 撤銷整個 `family_id` 再回 `401`」的防禦邏輯。再跑一次 5 併發腳本，確認只會有 1 筆成功、剩下 4 筆當場觸發家族全面撤銷。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地四個修補都驗證通過後，強烈建議到 **PortSwigger Web Security Academy** 把下面兩大系列的官方實驗室刷過一遍：

- **JWT attacks** 系列：
  - *JWT authentication bypass via unverified signature*
  - *JWT authentication bypass via flawed signature verification*（`alg: none`）
  - *JWT authentication bypass via jwk header injection*
  - *JWT authentication bypass via kid header path traversal*
  - *JWT authentication bypass via algorithm confusion*
- **OAuth authentication** 系列：
  - *Authentication bypass via OAuth implicit flow*
  - *Forced OAuth profile linking*（漏驗 `state` 的 Login CSRF）
  - *OAuth account hijacking via redirect_uri*

> **卡點提示**：
> - **打 `RS256 → HS256` 一直拿到 `401`？** 九成九是你手上的 PEM 公鑰跟伺服器記憶體裡的那一份差了一兩個字元！檢查看看伺服器用的是 `BEGIN PUBLIC KEY`（SPKI）還是 `BEGIN RSA PUBLIC KEY`（PKCS#1），還有最後一行後面有沒有多或少一個 `\n`。在沒公開 `/jwks.json` 的進階關卡裡，可以先拿兩張合法登入發給你的真實 JWT，用 `rsa_sign2n` 工具從兩組簽章反推出伺服器的 RSA 公鑰模數與 PEM 格式。
> - **打 `kid` `/dev/null` 簽章一直不對？** 檢查你的腳本是不是不小心把字串 `"null"` 當成密鑰傳進去了！`/dev/null` 讀出來是長度為 `0` 的空位元組 `b""`（空字串 `""`），而且算完 Base64URL 記得要把尾巴的 `=` 號拔掉。
> - **打 OAuth `redirect_uri` 時外站網址被擋掉？** 既然不能直接填外站，就回頭去翻翻看目標網站自己網域底下有哪些頁面可以借刀殺人（比如有沒有會自動跳轉的頁、有沒有可以貼外部圖片讓 `Referer` 外洩的留言板或靜態頁），再用 `/callback/../頁面` 跳過去。

---

### 參考解答

#### 1. JWT 演算法混淆與 `kid` 修補驗證要點

在寫腳本把 JWKS 轉成 SPKI PEM 算 HMAC-SHA256 時，養成好習慣先印出 `Buffer.byteLength(pem)`（標準 2048-bit RSA SPKI PEM 含尾端換行是 `451 bytes`）。

修補上線後，你的自動化回歸測試應該連打三發偽造 Token：`alg: "none"`、`alg: "HS256"` 以及 `kid: "../../../../dev/null"`。這三發都必須在驗票中介層第一關就被攔下來回傳 `401`，連碰都不准碰到後面的業務 Controller。

#### 2. OAuth 精確比對與 Refresh Token 原子消費 SQL

首先，OAuth 授權端檢查 `redirect_uri` 時，直接改成用陣列嚴格相等比對（`registeredUris.includes(req.query.redirect_uri)`），絕對不准用 `startsWith`，也不准先幫路徑做 `..` 正規化再比對。

其次，Refresh Token 的單次消費與重用偵測，必須用下面這條帶列鎖的原子 SQL（在 `READ COMMITTED` 交易內執行）：

```sql
UPDATE refresh_tokens
SET used = true, used_at = NOW()
WHERE token_hash = $1
  AND used = false
  AND revoked = false
  AND expires_at > NOW()
RETURNING id, family_id, user_id;
```

當這條 SQL 回傳 `0` 列時，馬上查一下這個 `token_hash` 在資料庫裡的狀態：如果這筆紀錄確實存在，而且 `used` 已經變成 `true`，就抓到重用攻擊了！立刻跑一行 `UPDATE refresh_tokens SET revoked = true WHERE family_id = $1`，**先呼叫 `COMMIT` 把撤銷結果寫死進磁碟**，最後才回傳 `401`。這樣再用 5 併發腳本去撞時，第 1 個搶到列鎖的請求剛換出新票，後面 4 個排隊進來的請求馬上就會觸發 Reuse Detection，把剛剛換出來的新票連同整個家族一起原地作廢！

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

試著不翻前面的解答，回答下面 4 個在架構審查與面試裡最常被問到的問題：

1. **為什麼 `RS256 → HS256` 換行格式一變就會失敗**：在演算法混淆攻擊中，為什麼攻擊者手上半點私鑰都沒有，只靠公開的 RSA 公鑰就能簽出讓伺服器點頭放行的 `admin` Token？如果伺服器是在 Linux 容器裡讀取 `LF` 換行的 `public.pem`（共 `451 bytes`），而攻擊者在 Windows 筆電上把公鑰存成了 `CRLF` 換行（9 處換行共變成 `460 bytes`）才拿去算 HMAC，送出去的 Token 會發生什麼事？為什麼？
2. **精算無狀態 JWT 的撤權空窗期**：某系統的 API 閘道把本地 JWKS 公鑰快取的硬性過期時間設為 `TTL = 300 s`（5 分鐘，到期立刻重抓），而簽發出去的 JWT Access Token 有效期是 `900 s`（15 分鐘），系統目前**沒有**設 Redis `jti` 黑名單。現在有位工程師突然離職，管理員在後台緊急撤銷他的權限，請分別算出他在被撤權前一秒剛拿到手的那張舊 Token，在下面兩種做法下最多還能繼續打 API 多久？
   - (a) 管理員除了在資料庫停用他的帳號，還立刻去 Auth Service 把簽發那張 Token 的舊公鑰從 JWKS 清單裡拔掉。
   - (b) 管理員只在資料庫把他的帳號設為停用（或是金鑰輪換時為了怕影響別人，暫時把舊公鑰留在 JWKS 裡）。
3. **串接前綴比對與 `Referer` 外洩偷走 OAuth `code`**：某網站的 OAuth 授權伺服器在檢查 `redirect_uri` 時，只寫了 `uri.startsWith("https://portal.example.com/oauth")`。剛好 `portal.example.com` 上面有一個舊頁面 `/oauth/partner-Promo`，這個頁面不會自動跳轉，但裡面有用 `<img>` 載入外部合作商 `https://ads.evil.example/banner.png` 的圖片，而且全站忘了設 `Referrer-Policy`（或是設成了寬鬆的 `unsafe-url`）。請問攻擊者該怎麼構造授權連結，才能不靠伺服器 `302` 跳轉就把受害者的 Authorization Code 偷到手？
4. **Refresh Token 撤銷為什麼會被自己的 `401` 吃掉**：某工程師照著書上寫了單條原子的 `UPDATE ... WHERE used = false RETURNING *` 來防 Refresh Token 併發雙花，也在發現回傳 `0` 列且 `used = true` 時補上了 `await db.query('UPDATE refresh_tokens SET revoked = true WHERE family_id = $1', [familyId])`，接著下一行馬上寫 `throw new UnauthorizedException('Token reuse detected')`。結果上線實測時發現，一旦有人重刷舊 Token，雖然當次請求有收到 `401`，但家族裡的新 Token 居然完全沒被撤銷，還是能繼續用！請問是哪裡出了包？該怎麼修？

---

### 參考解答

1. **公鑰當對稱密鑰的原理與 `LF` vs `CRLF` 差異**：
   - **原理**：因為驗票程式沒鎖死只准跑 `RS256`，也沒檢查傳進去的金鑰型別。當攻擊者把 Header 改成 `alg: "HS256"`，驗票程式就傻傻切換成 HMAC-SHA256 對稱驗簽，直接把伺服器上那串原本用來驗 RSA 的公鑰文字當成對稱密鑰來算 MAC。既然公鑰誰都抓得到，攻擊者拿同一串字在自己電腦上算 HMAC，算出來當然一模一樣。
   - **`CRLF` vs `LF` 的後果**：驗簽會直接失敗（回傳 `401`）。因為 HMAC-SHA256 遇到長度超過 `64 bytes` 的密鑰時，會先把整串密鑰位元組丟進 SHA-256 壓出一個 `32 bytes` 的衍生金鑰 $K'$。`460 bytes`（`CRLF`）跟 `451 bytes`（`LF`）差了 9 個 `\r` 位元組，SHA-256 算出來的 $K'$ 完全不同，後面算出來的簽章自然半個字都對不上。
2. **無狀態 JWT 的兩段撤權時間窗**：
   - **(a) 同時從 JWKS 拔掉舊公鑰**：這張在撤權前一秒拿到的 Token 雖然自己還能活 `899 s`，但下游 API 閘道上的本地 JWKS 快取最多過 **`300 s`**（5 分鐘）就會到期重抓；一重抓發現舊公鑰沒了，這張票就再也驗不過了。所以最多只能再活 $\min(899\text{ s}, 300\text{ s}) = \mathbf{300\text{ s}}$。
   - **(b) 只停用資料庫帳號、沒拔公鑰**：只要閘道還認得那把公鑰，而且驗票時沒去查資料庫或 Redis 黑名單，無狀態驗簽就只看 Token 自己寫的 `exp`。所以這張票可以一路暢通無阻用到它自己過期為止，也就是最長達 **`899 s`（約 15 分鐘，上限為 `900 s`）**。
3. **利用同源頁面與 `Referer` 偷出 OAuth `code`**：
   - 攻擊者只要把授權連結裡的 `redirect_uri` 設成 `https://portal.example.com/oauth/partner-Promo`（或是透過 `/oauth/callback/../partner-Promo` 繞過去）。
   - 因為它完全符合 `startsWith("https://portal.example.com/oauth")`，授權伺服器就會開心地回 `302`，把受害者的瀏覽器導向 `https://portal.example.com/oauth/partner-Promo?code=SECRET_CODE`。
   - 受害者瀏覽器一打開這個頁面，看到裡面有 `<img src="https://ads.evil.example/banner.png">`，就會立刻發請求去向 `ads.evil.example` 抓圖；而在寬鬆的 `Referrer-Policy` 下，瀏覽器會自動在抓圖請求的 `Referer` 標頭裡附上當前頁面的完整網址（包含尾巴那串 `?code=SECRET_CODE`），駭客只要看自己圖片伺服器的存取日誌，就能把 `code` 撿走！
   - **修法**：`redirect_uri` 一定要用完整字串相等比對，並且全站加上 `Referrer-Policy: no-referrer`（或至少 `strict-origin-when-cross-origin`）。
4. **交易回滾把家族撤銷吃掉的陷阱**：
   - **出包原因**：那位工程師把整個換票函式包在同一個資料庫交易（Transaction，例如 `@Transactional()` 或 `BEGIN ...`）裡面。當他執行完 `UPDATE ... SET revoked = true` 之後，還沒 `COMMIT` 就直接 `throw new UnauthorizedException()`，外層框架一接住這個未處理的例外，就盡責地幫他執行了 `ROLLBACK`！結果剛剛把整個 `family_id` 標為 `revoked = true` 的修改，就隨著交易回滾被一併清掉了。
   - **正確修法**：抓到 Token Reuse 並執行完家族撤銷的 `UPDATE` 之後，**一定要先把這筆交易 `COMMIT` 提交落盤**（或者把家族撤銷丟進一條獨立且必定 `COMMIT` 的新資料庫連線／交易裡執行），確認寫死進資料庫之後，最後才往外丟 `401` 錯誤。

---

## 延伸閱讀

- **RFC 7515 / RFC 7519 / RFC 8725（JWT Best Current Practices）**：特別推薦讀 **RFC 8725**，裡面把十年來所有血淋淋的 JWT 實作慘案（包含 `alg: none`、演算法混淆、`jku`/`kid` 注入）全部整理成了標準防禦條文。
- **RFC 9700 — *OAuth 2.0 Security Best Current Practice***（2025 年正式定版）：全面翻新了 OAuth 2.0 的安全要求，明令 `redirect_uri` 必須做完整字串精確比對、全面強制 PKCE `S256`、廢棄 Implicit Flow，並詳細定義了 Refresh Token 輪換與重用偵測的標準做法。
- **PortSwigger Web Security Academy — *JWT attacks* 與 *OAuth 2.0 authentication vulnerabilities***：把本章講的每一個變體都做成了可以親手打穿的互動靶機，是鞏固手感最好的練習場。
- **Node.js `jose` 套件官方文件**：對照看看現代密碼學套件是怎麼靠 TypeScript 型別系統（區分 `KeyLike` 公私鑰與對稱 `Uint8Array`）與強制 `algorithms` 參數，從 API 設計源頭讓開發者想寫出演算法混淆漏洞都很難。

