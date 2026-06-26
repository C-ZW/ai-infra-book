# F · 身分與存取

身分與存取要回答兩個分得很開的問題：**這個請求是誰發的（認證）**、以及**他能不能做這件事（授權）**。本領域把這兩件事拆乾淨，再往下挖支撐它們的機制——token 怎麼生、怎麼撤、用什麼簽、怎麼驗，以及權限怎麼建模（RBAC 還是 ABAC）。檔內六條：認證 vs 授權、token 生命週期與撤銷、對稱 vs 非對稱簽章、RBAC vs ABAC、JWT、OAuth2/OIDC/OAuth 2.1。傳輸層的身分（TLS/mTLS）與機密管理不在這裡——前者在網路協定（領域 N）、後者在部署（領域 Q）；本領域只管「應用層的人/服務是誰、能做什麼」。

## 認證 vs 授權（AuthN vs AuthZ；OIDC 在哪一塊）

### 定義與原理

兩個常被混講、實際上正交的問題：

- **認證（authentication，AuthN）**：**你是誰**。驗證一個身分主張為真——這個請求確實來自它聲稱的那個 principal（人、服務、裝置）。輸出是一個**已驗證的身分**。
- **授權（authorization，AuthZ）**：**你能做什麼**。在已知身分（或匿名）的前提下，判斷某個操作對某個資源是否被允許。輸出是 allow / deny。

第一原理上它們順序固定但職責不同：先認證、後授權。一個系統可以**只認證不授權**（登入了就什麼都能做）、也可以**只授權不認證**（匿名但有 rate limit、有 IP allowlist 這種以非身分屬性做的決策）。把兩者綁死是常見的耦合來源——例如把「是不是管理員」這個授權判斷塞進登入流程，之後想加一個「管理員但唯讀」的角色就得動認證碼。

**OIDC 落在認證這一塊。** OAuth 2.0 本質是**授權**框架（delegated authorization：讓 App 拿到「代表使用者去存取某資源」的權限），它本身**不**定義「使用者是誰」。OIDC（OpenID Connect）是疊在 OAuth 2.0 上的**身分層（identity layer）**，補上認證：它讓 client 能驗證使用者身分、拿到使用者基本資料，產物是一個叫 **ID Token** 的簽章 JWT（2026-06）。一句話記法：**OAuth 給你 access token（去做事的授權憑證）、OIDC 給你 ID Token（你是誰的認證結果）**（OAuth/OIDC 機制見 OAuth2 / OIDC / OAuth 2.1，本領域；JWT 結構見 JWT，本領域）。

### 解法空間

認證的做法（驗「你是誰」）：

- **密碼 + 工作階段（session）**：登入後伺服器發 session id（存 cookie），狀態在 server 端。簡單、撤銷容易（刪 session 即可），但需要共享 session store 才能水平擴展。
- **token-based（無狀態）**：登入後發自包含的簽章 token（如 JWT），之後每個請求帶它、伺服器本地驗簽。免查 store、易擴展，代價是撤銷難（見 token 生命週期與撤銷，本領域）。
- **聯合身分（federated）/SSO**：把認證委派給 IdP（identity provider），用 OIDC、SAML、或社交登入。自己不存密碼。
- **多因素（MFA）**：在密碼之外加 TOTP / WebAuthn / passkey 等第二因素，抵抗憑證外洩。
- **mTLS / API key**：服務對服務常用——憑證或金鑰即身分（mTLS 在領域 N、API key 管理在領域 Q）。

授權的做法（判「你能做什麼」）：

- **ACL（access control list）**：每個資源掛一張「誰能做什麼」的清單。直觀但難規模化。
- **RBAC**：權限綁角色、使用者綁角色（見 RBAC vs ABAC，本領域）。
- **ABAC / policy-based**：用主體/資源/環境屬性寫規則決策（見 RBAC vs ABAC，本領域）。
- **能力（capability）/ scope**：token 本身攜帶「能做哪些事」的範圍宣告（OAuth scope）。
- **關係式（ReBAC）**：以「主體與資源的關係圖」判權（如「文件擁有者的同團隊成員可讀」）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Session（有狀態認證） | 即時可撤銷、server 完全掌控 | 單體或有共享 session store 的服務 | 擴展需 sticky session 或集中 store；跨域 cookie 麻煩 |
| JWT/token（無狀態認證） | 免查 store、易水平擴展 | 多服務、無共享 store、邊緣驗證 | 撤銷困難；token 一旦簽發到 expiry 前都有效 |
| OIDC / SSO（聯合認證） | 自己不碰密碼、集中 MFA/稽核 | 多 App 共用登入、企業整合 | 強相依 IdP；IdP 故障＝全員登不進 |
| RBAC（授權） | 角色集中管理、易稽核 | 角色數有限、權限隨組織結構 | 角色爆炸（role explosion）；細粒度需求會撐爆 |
| ABAC（授權） | 細粒度、規則表達力強 | 多維度條件（時間/地點/資源屬性） | 規則難測難稽核、「為何被拒」難解釋 |

關鍵取捨是**撤銷即時性 vs 擴展性**（認證側）與**集中可稽核 vs 細粒度表達力**（授權側）。沒有免費的：越無狀態越好擴展、就越難即時收回；越細粒度越精準、就越難說清「現在誰能做什麼」。

### 何時需要

- **只需認證、授權平凡**（登入即全權，如內部單一用途工具）：別上 RBAC/ABAC，一個 `is_logged_in` 就夠，加角色是 over-engineering。
- **多角色但維度單純**（admin / editor / viewer）：RBAC 剛好，別跳 ABAC。
- **決策依賴資源屬性或環境**（「只能改自己部門的單」「上班時間才能匯出」）：這時 RBAC 撐不住，需要 ABAC 或 ReBAC。
- **多個 App 要共用登入、或要接第三方登入**：上 OIDC，別自己滾 SSO。
- **內部服務對服務**：通常不需要完整 OAuth dance，mTLS 或簽章的服務 token 更輕。

判準：**授權的維度數**決定模型——一維（角色）用 RBAC，多維（屬性/關係）才付 ABAC/ReBAC 的複雜度成本。

### 常見誤解與陷阱

- **把認證當授權**：「他登入了」不等於「他能做這件事」。最典型的漏洞是 IDOR——驗了身分卻沒驗「這筆資源是不是他的」（拿別人的 order id 就能讀別人的單）。**每個敏感操作都要獨立做授權檢查**，不能靠「進得來就是自己人」。
- **OAuth 當登入用**：純 OAuth（沒有 OIDC）只給你 access token，它證明「App 拿到了存取某 API 的授權」，**不**證明「使用者是誰」。把 access token 當登入憑證、用它去 userinfo 端點推使用者身分，是經典的混淆攻擊面（這正是 OIDC 用獨立 ID Token 解決的問題）。
- **授權檢查放在前端**：前端隱藏按鈕只是 UX，不是授權。授權必須在伺服器端、在每個進入點重做。
- **角色 = 權限**：角色是權限的**集合的命名**，不是權限本身。把業務邏輯直接綁角色名（`if role == "manager"`）會讓角色語意僵化，應綁到具體權限（`if can("approve_refund")`）。

### 延伸閱讀

- [The OAuth 2.0 Authorization Framework — RFC 6749](https://www.rfc-editor.org/rfc/rfc6749)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [NIST SP 800-162: Guide to Attribute Based Access Control (ABAC) Definition and Considerations](https://csrc.nist.gov/pubs/sp/800/162/upd2/final)

## token 生命週期與撤銷（短 TTL + refresh / denylist）

### 定義與原理

一個 token 是一張「持有即有效」的通行證。它的生命週期是：**簽發（issue）→ 使用（present/validate）→ 過期或撤銷（expire/revoke）**。核心矛盾來自一個第一原理：

> **自包含的簽章 token 是無狀態的——伺服器靠本地驗簽就能信它，不查任何 store。但這正意味著伺服器手上沒有「這張 token 還算不算數」的開關。** token 一旦簽發，在 expiry 之前都驗得過，即使背後的使用者已被停權、密碼已洩漏、權限已收回。

這就是「無狀態的便利」與「即時撤銷的需要」之間的根本張力。短 TTL（time to live）就是這個張力的妥協產物。

### 解法空間

- **短命 access token + 長命 refresh token**：access token TTL 設很短（典型 15–60 分鐘），到期就用 refresh token（長命，存得更安全）去換新的。撤銷時撤 refresh token，access token 最多再活一個 TTL 就自然死。**這是業界主流結構**。
- **denylist（撤銷清單）**：維護一份「已撤銷 token id（jti）」的清單，每次驗 token 時查它。能即時撤銷，但**抵銷了無狀態的好處**（又要查 store 了）。通常只存「到期前被提早撤銷的少數」，靠 TTL 讓清單自動瘦身。
- **token introspection（RFC 7662）**：用 opaque token（不自包含），resource server 每次向 authorization server 查 token 是否 `active`。本質是把「是否有效」這個權威留在 server 端，撤銷即時但每次驗都要一次網路往返（2026-06）。
- **token 撤銷端點（RFC 7009）**：標準化「主動通知 authorization server 作廢某 token」的端點，常配合上面任一機制（2026-06）。
- **refresh token 輪替（rotation）**：每次用 refresh token 換新 access token 時，同時發一張新的 refresh token、作廢舊的。若偵測到舊 refresh token 被重用（reuse detection），代表它被竊，立刻撤整條鏈。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 短 TTL + refresh | 撤銷延遲 ≤ 一個 access TTL、驗證仍無狀態 | 多數 web/mobile/API | 撤銷不是即時，洩漏的 access token 在 TTL 內仍可用 |
| denylist（jti 清單） | access token 也能即時撤銷 | 高敏感操作、需即時收回 | 每次驗都查 store，犧牲無狀態；清單須隨 TTL 清理 |
| introspection（opaque） | 完全即時、權威集中、可帶最新權限 | 集中式 authz server、可承受往返 | 每請求一次往返，延遲與可用性綁 authz server |
| refresh rotation + reuse detection | 偵測 refresh token 竊用、限縮爆炸半徑 | 公開 client（SPA/mobile） | 網路抖動可能誤判合法重用、誤撤整條鏈 |

取捨軸線是**撤銷即時性 ←→ 驗證成本（無狀態程度）**。短 TTL 是「用時間換無狀態」——你接受「最多晚一個 TTL 才生效」來換「平常不查 store」。要真正即時，就得放棄純無狀態（denylist 或 introspection）。

### 何時需要

- **一般 API**：短 TTL（如 15 分鐘 access）+ refresh 通常夠。15 分鐘的撤銷延遲對絕大多數場景可接受。
- **高敏感操作**（轉帳、改權限、刪資料）：即使有短 TTL，這類操作宜搭 denylist 或重新驗證（step-up auth），不能容忍 15 分鐘的撤銷窗口。
- **內部服務間 token**：壽命可更短、輪替更頻繁，因為換 token 的成本低、不影響使用者體驗。
- **不需要撤銷的場景**（如極短命的單次操作 token）：別建 denylist，徒增複雜度。

**worked example（撤銷延遲量化）**：access token TTL 設 15 分鐘。某使用者帳號於 10:00:00 被停權（撤掉其 refresh token）。他手上那張 access token 簽發於 09:50:00、到 10:05:00 才過期——所以在停權後**最長 5 分鐘**內，這張舊 access token 仍能通過本地驗簽、繼續存取。若這 5 分鐘不可接受，就必須把該 token 的 jti 放進 denylist、讓驗證路徑去查它（代價：每次驗證多一次 store 查詢）。把 TTL 縮到 1 分鐘能把窗口壓到 ≤1 分鐘，但 refresh 頻率提高 15 倍，authz server 負載與 refresh 往返也隨之上升——這就是「撤銷延遲」與「refresh 開銷」的直接對價。

### 常見誤解與陷阱

- **「JWT 可以撤銷」**：純 JWT **不能**真正撤銷——它自包含、本地驗簽，server 沒有它的記錄可以作廢。所謂「撤銷 JWT」要嘛是縮 TTL（讓它快點自然死）、要嘛是退回查 store（denylist/introspection，那就不再是純無狀態 JWT 了）。
- **把 refresh token 當 access token 用**：refresh token 應**只**用於換新 access token，不該拿去存取資源 API。它壽命長、權力大，曝險面要最小化。
- **denylist 不清理**：denylist 只需存「未到 expiry 卻被提早撤銷」的 token。若不依 TTL 清理，清單會無限長大、查詢變慢——它應該是個有 TTL 的快取，不是永久表。
- **TTL 設太長圖省事**：把 access token TTL 設成幾天，等於放棄了撤銷能力——一旦洩漏，幾天內都無解。短 TTL 是這套設計的前提，不是可選項。
- **登出只清前端**：前端刪掉 token 不等於 token 失效。真正的登出要在 server 端撤掉 refresh token（並視需要把 access token 加入 denylist），否則被竊的 token 照樣能用。

### 延伸閱讀

- [OAuth 2.0 Token Revocation — RFC 7009](https://www.rfc-editor.org/rfc/rfc7009)
- [OAuth 2.0 Token Introspection — RFC 7662](https://www.rfc-editor.org/rfc/rfc7662)
- [JSON Web Token Best Current Practices — RFC 8725](https://www.rfc-editor.org/rfc/rfc8725)

## 對稱 vs 非對稱簽章（HS256 / RS256 / JWKS）

### 定義與原理

簽章解決的是**完整性與來源**：拿到一個 token，怎麼確定它是某個可信方簽的、中途沒被改？兩種密碼學路線：

- **對稱簽章（symmetric / MAC）**：簽與驗用**同一把密鑰**（shared secret）。代表演算法 **HS256**（HMAC-SHA256）。能驗的人就能簽——驗章方等於也握有簽章能力。
- **非對稱簽章（asymmetric / digital signature）**：簽用**私鑰**、驗用**公鑰**，兩把不同。代表演算法 **RS256**（RSASSA-PKCS1-v1_5 + SHA-256）、**ES256**（ECDSA P-256 + SHA-256）。私鑰留在簽發方手上，公鑰可以公開散佈；**握有公鑰只能驗、不能偽造**。

第一原理上的分水嶺：**信任邊界**。對稱簽章要求所有驗證方都共享同一個能簽的祕密——驗證方越多，祕密外洩面越大；非對稱讓「簽的能力」集中在一處（私鑰），「驗的能力」自由散佈（公鑰），這對「一處簽發、多服務驗證」的分散式系統是決定性的差別。

**JWKS（JSON Web Key Set，RFC 7517）** 是配套基建：authorization server 把它的**公鑰**以 JSON 格式發布在一個 HTTPS 端點（`/.well-known/jwks.json`），各 resource server 動態抓公鑰來驗 token，並靠 token header 裡的 `kid`（key id）對上是哪一把——這讓**金鑰輪替不必停機**（2026-06）。

### 解法空間

驗證一個 token 簽章，你的選擇：

- **HS256（共享密鑰）**：發行方與驗證方事先約好一把 secret。最快、最簡單，但密鑰必須安全送達每個驗證方。
- **RS256 / ES256（公私鑰）**：私鑰只在發行方，公鑰公開。驗證方拿公鑰即可，永遠碰不到簽章能力。
- **JWKS 端點**：不把公鑰寫死在各服務，而是讓它們從發行方的 JWKS URL 動態拉、依 `kid` 選鑰、快取一段時間。輪替金鑰時發行方加一把新鑰、舊鑰留一段過渡期，驗證方下次拉就自動更新。
- **ES256 vs RS256**：兩者都是非對稱；ECDSA 金鑰更短、簽章更小（P-256 公鑰約 64 bytes vs RSA-2048 約 256 bytes），同安全強度下更省頻寬，現代系統常選 ES256。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| HS256（對稱） | 完整性＋來源，驗證極快 | 單一信任域、發=驗同方 | 每個驗證方都握有簽章能力，secret 一漏即可偽造任何 token |
| RS256（非對稱） | 同上，且驗證方無法偽造 | 一處簽發、多服務/第三方驗證 | 金鑰較大、簽驗較慢；要管私鑰保護與公鑰散佈 |
| ES256（非對稱，ECC） | 同 RS256，金鑰/簽章更小更快 | 頻寬敏感、行動端、現代部署 | 對隨機數品質敏感（nonce 重用會洩私鑰）；舊環境支援度略低 |
| JWKS 端點 | 公鑰動態散佈＋無停機輪替 | 公鑰需被多方、跨組織取得 | 驗證方須快取公鑰並處理 fetch 失敗；JWKS URL 不可被掉包 |

### 何時需要

- **發行與驗證是同一個服務（或同一信任域內少數服務）**：HS256 夠了，別為了「看起來高級」上 RS256。共享一把 secret 在這裡是合理的。
- **token 由身分服務簽、被多個下游 API（甚至第三方）驗**：必須非對稱（RS256/ES256）。否則你得把能簽的 secret 發給每個下游，任何一個被攻破就能假冒身分服務簽出任意 token。**OIDC ID Token 在這種「一處簽、多方/第三方驗」的情境下因此常用非對稱簽**——RP（依賴方）只拿 IdP 的公鑰即可驗。（規格只要求 OP 必須支援 RS256；當 RP 是持有 `client_secret` 的機密 client 時，ID Token 也允許設 `id_token_signed_response_alg=HS256` 用對稱簽，此時驗證方就是持有該 secret 的那一方。）
- **要支援金鑰輪替而不停機**：上 JWKS。
- **頻寬/延遲敏感或行動端**：在非對稱裡優先 ES256。

判準很乾脆：**驗證方數量與信任域**。驗證方只有自己 → 對稱；驗證方是「別人」或會增長 → 非對稱。

### 常見誤解與陷阱

- **`alg: none` 攻擊**：JWT header 的 `alg` 欄位若被驗證庫盲信，攻擊者把它改成 `none`（不簽）就可能繞過驗章。**驗證方必須在伺服器端寫死預期演算法**，不能讓 token 自己宣告用什麼演算法驗。
- **演算法混淆（RS256→HS256 confusion）**：經典漏洞——服務用 RS256 的**公鑰**當作 HS256 的**密鑰**來驗。公鑰是公開的，攻擊者拿它當 HMAC secret 自己簽一個 HS256 token，就通過了。**根因是把「對稱密鑰」和「非對稱公鑰」當成可互換的『一把 key』**。防法同上：驗證方鎖死演算法類別，不接受 token 指定。
- **以為簽章 = 加密**：簽章只保證**完整性與來源**，**不**保證機密性——JWT payload 是 base64url 編碼、人人可解讀（見 JWT，本領域）。別把祕密放進去。
- **把 HS256 secret 當密碼隨便設**：HS256 的安全性完全取決於 secret 的熵。用弱 secret（短字串、可猜的詞）等於沒簽——可被離線暴力破解。secret 應為高熵隨機值。
- **JWKS 不快取或快取太久**：每次驗都打 JWKS URL 會拖垮延遲、且把可用性綁死那個端點；快取太久又會在輪替後驗不過新 token。需有合理 TTL ＋ 遇未知 `kid` 時主動 refresh 的策略。

### 延伸閱讀

- [JSON Web Signature (JWS) — RFC 7515](https://www.rfc-editor.org/rfc/rfc7515)
- [JSON Web Key (JWK) — RFC 7517](https://www.rfc-editor.org/rfc/rfc7517)
- [JSON Web Algorithms (JWA) — RFC 7518](https://www.rfc-editor.org/rfc/rfc7518)

## RBAC vs ABAC

### 定義與原理

兩種授權建模法，差在「用什麼來下判斷」：

- **RBAC（role-based access control，角色式）**：權限（permission）綁在**角色**上，使用者綁角色。判斷時看「這個使用者有沒有一個帶此權限的角色」。間接層是固定的：使用者 → 角色 → 權限。RBAC 由 Ferraiolo 與 Kuhn 於 **1992** 年形式化，後整合 Sandhu 等人 1996 的模型，成為美國國家標準 **ANSI/INCITS 359-2004**（2012 修訂）（2026-06）。
- **ABAC（attribute-based access control，屬性式）**：判斷時對**屬性**求值一條規則——主體屬性（部門、職級）、資源屬性（擁有者、機密等級）、環境屬性（時間、IP、裝置）。沒有固定的角色中介層，決策是「對這些屬性，這條 policy 允不允許」。權威定義在 **NIST SP 800-162**，常見落地語言是 **XACML**（2026-06）。

第一原理上的差別：**RBAC 是「先把使用者分組、組決定能做什麼」（靜態、可枚舉）；ABAC 是「每次請求現算一條規則」（動態、組合式）。** RBAC 能離線回答「誰能做 X」（列出有該權限的角色、再列出有該角色的人）；ABAC 通常不能——因為答案取決於請求當下的環境屬性。

### 解法空間

授權模型其實是一個光譜，不只兩點：

- **ACL**：直接列「資源 → (主體, 操作)」。最原始，無中介層。
- **RBAC**：加一層角色當中介。可再加層級（role hierarchy，經理角色繼承員工角色的權限）。
- **RBAC + 屬性（有時稱 RAdAC / dynamic RBAC）**：以角色為主、用少量屬性微調（如「editor 角色但只能改自己建立的」）。實務上最常見的折衷。
- **ABAC**：純規則式，角色只是眾多屬性之一。
- **ReBAC（relationship-based）**：以「主體與資源之間的關係圖」判權（「文件擁有者的協作者可編輯」），適合社交/協作/檔案共享這種關係主導的領域。
- **PBAC（policy-based）**：把 policy 外部化成獨立決策點（PDP），應用呼叫它問 allow/deny——ABAC/ReBAC 常以此架構落地。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| ACL | 最直觀、無學習成本 | 資源少、規則少 | 規模化即崩潰，難回答「某人能碰哪些東西」 |
| RBAC | 集中管理、易稽核、可離線枚舉「誰能做 X」 | 角色維度單純、權限隨組織結構 | 細粒度需求導致角色爆炸；難表達「資源相關」條件 |
| RBAC + 屬性 | 保留 RBAC 可稽核性、補上少量動態條件 | 多數企業 App 的甜蜜點 | 屬性條件散在程式碼裡會難維護，需收斂 |
| ABAC | 細粒度、任意維度、規則集中可改 | 條件多維（時間/地點/資源屬性/合規） | 「為何被拒」難解釋、規則組合難窮舉測試 |
| ReBAC | 關係主導場景的天然表達、可枚舉關係 | 協作/共享/社交圖權限 | 需維護關係圖與一致性，查詢可能變圖遍歷 |

核心取捨：**可稽核性/可枚舉性 ←→ 表達力/細粒度**。RBAC 那端「現在誰能做什麼」一目了然、好稽核，但撐不起多維條件；ABAC 那端什麼條件都寫得出來，代價是你**很難回答「到底誰能做 X」**，也很難窮舉測試所有規則組合。

### 何時需要

- **角色數有限、權限對齊職務**（admin / editor / viewer / billing）：RBAC，別過度設計。
- **開始為了個案一直加角色**（出現 `editor-but-only-marketing`、`viewer-except-finance` 這種角色）：這是 **role explosion 的訊號**，代表你真正需要的是屬性條件——往 RBAC+屬性 或 ABAC 走。
- **決策依賴資源本身或環境**（「只能存取自己部門的」「機密等級 ≥ 我的才能讀」「只在公司網段內可匯出」）：RBAC 無法乾淨表達，需 ABAC。
- **權限由「關係」定義**（擁有者、協作者、團隊成員）：ReBAC。
- **合規驅動、需要把 policy 與程式碼分離、集中審計**：PBAC/ABAC 架構（外部 PDP）。

判準：**數一下你的授權決策依賴幾個維度**。一維（職務）→ RBAC；二三維且其一是資源/環境屬性 → RBAC+屬性 或 ABAC；關係主導 → ReBAC。

**worked example（role explosion 的數字）**：假設權限軸有 3 種操作（read/write/delete）、資源歸屬有 5 個部門、再加「自己的 vs 全部」2 種範圍。用純 RBAC 把每種組合做成一個角色，理論上需要 3 × 5 × 2 = **30 個角色**才能覆蓋；再加一個正交維度（如「上班時間限定」）就翻倍到 60。角色數隨維度**相乘**膨脹——這就是 role explosion。改用 ABAC，這些條件是 3 條規則（操作 × `resource.dept == user.dept` × `time in business_hours`）的組合，**規則數隨維度相加**而非相乘。維度一多，ABAC 的「相加」就贏過 RBAC 的「相乘」。

### 常見誤解與陷阱

- **「ABAC 比 RBAC 高級，所以用 ABAC」**：ABAC 的細粒度是有代價的——規則難稽核、難測、「為何被拒」難排查。角色維度單純時硬上 ABAC 是 over-engineering。多數系統的正解是 **RBAC 為骨架、屬性為微調**。
- **role explosion 沒被當成訊號**：角色數量爆炸不是「再多建幾個角色」能解的，那是模型選錯的症狀——你需要的是把「資源/環境條件」從角色裡抽出來變成屬性。
- **ABAC 規則無法窮舉測試**：屬性組合是笛卡爾積，規則集一大就有覆蓋不到的死角（某組屬性意外被 allow）。ABAC 必須配規則測試、衝突偵測、與「預設 deny」的兜底。
- **角色綁了業務語意**：把角色名直接寫進業務判斷（`if role == "manager"`）會讓角色不能改名、不能拆分。應綁到具體權限（capability），角色只是權限的集合。
- **RBAC 不能回答的問題硬塞進角色**：「使用者只能看自己的資料」這種 **資源相關（resource-scoped）** 條件不是角色能表達的（角色是全域的），硬塞會做出一堆 per-user 角色。這類條件本質是屬性/關係，該用 ABAC/ReBAC。

### 延伸閱讀

- [NIST SP 800-162: Guide to Attribute Based Access Control (ABAC)](https://csrc.nist.gov/pubs/sp/800/162/upd2/final)
- [NIST CSRC: Role Based Access Control (RBAC) project](https://csrc.nist.gov/projects/role-based-access-control)
- [Adding Attributes to Role-Based Access Control (Kuhn, Coyne, Weil, 2010)](https://csrc.nist.gov/files/pubs/journal/2010/06/adding-attributes-to-rolebased-access-control/final/docs/kuhn-coyne-weil-10.pdf)

## JWT

### 是什麼與內部機制

JWT（JSON Web Token，RFC 7519）是一種**自包含、可簽章的 token 格式**：把一組 claim（鍵值對的宣告）打包成一個緊湊字串，攜帶資訊並用簽章保護其完整性。它通常以 **JWS（JSON Web Signature，RFC 7515）** 的形式存在——三段 base64url 編碼、用 `.` 連接（2026-06）：

```
header.payload.signature        # 示意，不可執行
```

- **header**：JSON，含 `alg`（簽章演算法，如 `HS256`/`RS256`/`ES256`）與 `typ`（`JWT`），常有 `kid`（指向 JWKS 裡哪把鑰）。
- **payload（claims）**：JSON，含註冊 claim 如 `iss`（簽發者）、`sub`（主體）、`exp`（到期，epoch 秒）、`iat`（簽發時間）、`aud`（受眾）、`jti`（token 唯一 id），以及自訂 claim。
- **signature**：對 `base64url(header) + "." + base64url(payload)` 算的簽章。HS256 用 HMAC + 共享密鑰；RS256/ES256 用私鑰簽。

驗證流程（示意）：

```
parts = token.split(".")                          # 必須剛好 3 段
header = json(base64url_decode(parts[0]))
assert header.alg in EXPECTED_ALGS                # 鎖死演算法，不信 token 自報
key = resolve_key(header.kid)                      # 從 JWKS 或本地拿
assert verify_sig(parts[0]+"."+parts[1], parts[2], key)
claims = json(base64url_decode(parts[1]))
assert claims.exp > now() and claims.iss == EXPECTED_ISS and EXPECTED_AUD in claims.aud
# 通過 → 信任 claims；不查任何 store（這正是它「無狀態」的來源）
```

關鍵：**驗章只用到本地（或快取的）金鑰，不需查資料庫**——這是 JWT 能水平擴展、能在邊緣驗證的根本原因，也是它難撤銷的根本原因（見 token 生命週期與撤銷，本領域）。

### 在哪些系統扮演什麼角色

- **無狀態認證 / API 授權**：登入後發 JWT 當 access token，各服務本地驗簽即知身分與權限，免共享 session store。微服務常用——閘道驗一次、下游信 claim。
- **OIDC ID Token**：OIDC 的認證結果就是一個簽章 JWT（見 OAuth2 / OIDC / OAuth 2.1，本領域）。
- **OAuth access token 的承載格式**：OAuth 的 access token 可以是 opaque（不透明、靠 introspection 驗）也可以是 JWT（自驗）；用 JWT 時 resource server 本地驗、省一次往返。
- **服務間斷言 / 短命憑證**：服務對服務傳遞身分與 scope，或當作極短命的一次性授權券。
- **不該扮演的角色**：當「session 替身但又要即時撤銷」——這是它做不好的事。

### 保證與限制

**保證**：

- **完整性與來源**：簽章保證 payload 沒被竄改、確實由持有對應金鑰者簽發。
- **無狀態驗證**：驗章不需查 store，O(1) 本地運算（加上可選的 JWKS 快取）。
- **自描述**：claim 自帶 `exp`/`iss`/`aud` 等，驗證方據以判時效與受眾。

**限制**：

- **不保證機密性**：payload 只是 base64url **編碼**、不是加密——任何人都能解讀內容。要機密性得用 JWE（JSON Web Encryption）另外加密。
- **難以即時撤銷**：簽發後到 `exp` 前都有效，server 沒有作廢開關（除非退回查 denylist/introspection，那就犧牲無狀態）。
- **大小**：claim 越多 token 越大，且每個請求都帶——塞太多會撐大 header、增加每請求頻寬。
- **時鐘相依**：`exp`/`nbf` 的判斷靠驗證方時鐘；時鐘飄移會誤判（通常留少量 clock skew 容忍）。

**worked example（撐大頻寬）**：一個塞了完整使用者 profile（角色清單、權限明細、偏好設定）的 JWT 可輕易到 **2 KB**。若一個服務每秒處理 10,000 個請求、每個請求都在 header 帶這張 token，光 token 的入站頻寬就是 10,000 × 2 KB = **約 20 MB/s（≈160 Mbps）**。把 token 瘦身到只放 `sub` + 角色 id（約 300 bytes），同樣 QPS 下降到約 3 MB/s——這是「把授權細節塞進 token 求免查 store」的隱性代價。**結論：JWT 放身分與粗粒度 scope，細粒度權限該查（快取的）授權服務，別全塞進每個請求都背的 token。**

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| JWT（自包含簽章 token） | 無狀態驗證、自描述、易擴展 | 多服務、邊緣驗證、OIDC ID Token | 難即時撤銷；不加密；每請求都背其大小 |
| Opaque token + introspection | 即時撤銷、token 本身不洩資訊 | 集中 authz、可承受每請求往返 | 每次驗一次網路往返，可用性綁 authz server |
| Server-side session（cookie） | 即時撤銷、state 全在 server | 單體/有共享 session store | 需集中 store 或 sticky；跨域 cookie 麻煩 |
| PASETO | 同 JWT 但演算法版本化、不可選 `none` | 想避開 JWT 演算法陷阱 | 生態與函式庫支援度不如 JWT 廣 |

選擇軸線同前：**JWT 換來無狀態擴展、付出撤銷困難**；opaque/session 換來即時掌控、付出每請求查 store 或共享 state。

### 常見誤解與陷阱

- **「JWT 是加密的，所以可以放敏感資料」**：**簽章 ≠ 加密**。JWS 的 payload 是明文 base64url，貼到任何解碼器都看得到。別放密碼、信用卡、PII。要保密用 JWE。
- **盲信 `alg`**：見對稱 vs 非對稱簽章（本領域）的 `alg: none` 與 RS256→HS256 confusion——驗證方必須在 server 端鎖死演算法，不接受 token 自報。
- **不驗 `exp`/`aud`/`iss`**：只驗簽不驗 claim，等於放過過期 token、放過簽給別的受眾的 token。簽章對了只代表「沒被改」，**claim 仍要逐一檢查**。
- **把 JWT 當 session 又想登出即失效**：做不到（沒有 server 端開關）。需要即時登出就配 denylist 或改用 session（見 token 生命週期與撤銷，本領域）。
- **不設 `exp` 或設超長**：無到期或超長到期的 JWT 一旦洩漏近乎永久有效。一定要設合理短的 `exp`。

### 延伸閱讀

- [JSON Web Token (JWT) — RFC 7519](https://www.rfc-editor.org/rfc/rfc7519)
- [JSON Web Signature (JWS) — RFC 7515](https://www.rfc-editor.org/rfc/rfc7515)
- [JSON Web Token Best Current Practices — RFC 8725](https://www.rfc-editor.org/rfc/rfc8725)

## OAuth2 / OIDC / OAuth 2.1

### 是什麼與內部機制

三個常被並提、職責不同的東西：

- **OAuth 2.0（RFC 6749）**：**委派授權（delegated authorization）** 框架。讓一個 client（App）在使用者同意下，拿到一個 **access token**，去代表使用者存取 resource server 上的受保護資源——**而不必拿到使用者的密碼**。它解的是「讓第三方 App 替我去某服務做事，但別給它我的密碼」。它**不**回答「使用者是誰」。
- **OIDC（OpenID Connect Core 1.0）**：疊在 OAuth 2.0 之上的**身分／認證層**。在授權請求加上 `openid` scope，authorization server（此時稱 OpenID Provider）除了 access token 外，再發一個 **ID Token**——一個簽章 JWT，載明「使用者是誰、何時/如何完成認證」。OIDC 把 OAuth 從「授權」補上「認證」（2026-06）。
- **OAuth 2.1（draft-ietf-oauth-v2-1）**：把 OAuth 2.0（RFC 6749）＋這十年累積的安全 BCP **整併簡化**成一份文件的進行中努力。**2026-06 仍是 IETF Internet-Draft、尚未成為 RFC**，最新為 **draft-15（2026-03-02 發布，Standards Track，預定 2026-09-03 到期）**（2026-06）。

OAuth 的核心角色與 grant（授權類型）：

- **角色**：resource owner（使用者）、client（App）、authorization server（發 token）、resource server（持資源、驗 token）。
- **authorization code grant**（主流）：client 把使用者導到 authorization server 登入＋同意 → 拿到一次性 `code` → client 在後端用 `code` 換 access token（＋OIDC 的 ID Token）。**搭配 PKCE** 防 code 被攔截後盜用。
- **client credentials grant**：服務對服務、無使用者，client 用自己的憑證直接換 token。
- **refresh token grant**：用 refresh token 換新 access token（見 token 生命週期與撤銷，本領域）。
- **（已被 2.1 淘汰的）**：implicit grant（token 直接從瀏覽器回傳，易洩）、ROPC（client 直接收使用者密碼，違背 OAuth 初衷）。

OAuth 2.1 相對 2.0 的四大變更（2026-06）：

1. **所有用 authorization code flow 的 client 強制 PKCE**（不再只限公開 client）。
2. **移除 implicit grant**（`response_type=token`）。
3. **移除 Resource Owner Password Credentials（ROPC）grant**。
4. **redirect URI 必須 exact string matching**（不再允許部分比對，杜絕開放重定向類攻擊）。

### 在哪些系統扮演什麼角色

- **第三方登入 / 社交登入**（用 X 帳號登入 Y）：OIDC（authorization code + PKCE），拿 ID Token 認身分。
- **企業 SSO**：OIDC 或 SAML 接 IdP，一次登入多個內部 App。
- **API 授權 / 委派存取**：純 OAuth——讓 App 拿 access token 去呼叫 API，scope 控制範圍。
- **服務對服務**：client credentials grant（無使用者參與）。
- **行動 / SPA 公開 client**：authorization code + PKCE（implicit 已不該用）。

### 保證與限制

**保證**：

- **密碼不外洩給 client**：OAuth 的根本價值——第三方 App 永遠拿不到使用者密碼，只拿到範圍受限、可撤銷、會過期的 token。
- **範圍限定（scope）**：access token 帶 scope，把 client 能做的事框死在使用者同意的範圍內。
- **認證與授權分離（配 OIDC）**：ID Token 管「你是誰」、access token 管「你能做什麼」，職責清楚。

**限制**：

- **OAuth ≠ 認證**：純 OAuth 不告訴你使用者是誰；要認證必須加 OIDC。把 access token 拿來推身分是誤用。
- **複雜度**：完整的 OAuth/OIDC dance（重定向、code 交換、PKCE、token 驗證、JWKS）不輕，自己實作易出安全漏洞——強烈建議用成熟函式庫/IdP。
- **2.1 尚未定案**：寫程式可以提早採用 2.1 的安全做法（PKCE、exact redirect matching），但**「OAuth 2.1 標準/RFC」的說法在 2026-06 不準確——它仍是 draft**。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| OAuth 2.0 authz code + PKCE | 委派授權、密碼不外洩、防 code 攔截 | 第三方/行動/SPA 存取 API | 流程複雜；只授權不認證（要身分需加 OIDC） |
| OIDC（疊在 OAuth 上） | 上述＋標準化認證（ID Token） | 第三方登入、SSO、需知使用者是誰 | 強相依 IdP 可用性；ID Token 要正確驗（iss/aud/sig） |
| OAuth 2.1（draft） | 同 2.0 但預設更安全、移除危險 grant | 想對齊最新安全 BCP 的新系統 | 仍是 draft（draft-15，2026-06），非凍結標準 |
| SAML 2.0 | 成熟的企業 SSO、XML 斷言 | 既有企業 IdP、政府/大型組織 | 笨重、XML、行動/SPA 體驗差 |
| 自建 session 登入 | 簡單、即時撤銷、無外部相依 | 單一 App、無第三方存取需求 | 不解委派授權；多 App 共用登入時重造輪子 |

判準：**要不要「讓第三方代表使用者去存取資源」**——要，就 OAuth；**還要不要知道「使用者是誰」**——要，就加 OIDC；只是自家單一 App 的登入、沒有委派需求，OAuth/OIDC 是殺雞用牛刀，server-side session 更簡單。

### 常見誤解與陷阱

- **「用 OAuth 做登入」**：純 OAuth 是**授權**協定，不是登入協定。把 access token 當登入憑證會落入混淆攻擊（拿到某 App 的 token 不代表使用者在你這邊也通過認證）。**要登入用 OIDC 的 ID Token**，並驗 `iss`/`aud`/`nonce`。
- **「OAuth 2.1 已經是標準了」**：不準確。2026-06 它仍是 IETF draft（draft-15），尚未成為 RFC。可以採用它的安全做法，但別對外宣稱依循「OAuth 2.1 標準」。
- **還在用 implicit grant**：把 token 直接從瀏覽器 fragment 回傳的 implicit flow 已被安全 BCP 與 2.1 淘汰——SPA 應改用 **authorization code + PKCE**。
- **ROPC（拿使用者密碼換 token）**：違背 OAuth「不讓 client 碰密碼」的初衷，已被 2.1 移除。除非極端遺留情境，否則不該用。
- **redirect URI 寬鬆比對**：允許部分比對或萬用字元的 redirect URI 是開放重定向＋code 竊取的破口。2.1 要求 **exact match**，是該照做的硬規則。
- **不驗 state / PKCE**：省掉 `state`（防 CSRF）或 PKCE（防 code 攔截）會直接開洞。這些不是可選的「加分項」，是 flow 安全的前提。

### 延伸閱讀

- [The OAuth 2.0 Authorization Framework — RFC 6749](https://www.rfc-editor.org/rfc/rfc6749)
- [The OAuth 2.1 Authorization Framework — draft-ietf-oauth-v2-1（IETF Datatracker，2026-06 仍為 draft）](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)
- [Proof Key for Code Exchange (PKCE) — RFC 7636](https://www.rfc-editor.org/rfc/rfc7636)
