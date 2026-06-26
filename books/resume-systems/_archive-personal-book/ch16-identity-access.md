# ch16 — 身分與存取：JWT、OAuth2 與 RBAC

> **本章解決什麼問題**：這是 Part IV 倒數第三站。你接過 JWT/OAuth2 登入、做過 RBAC——這些都是你「會用」的名詞，登入流程怎麼接你閉著眼睛都能畫。但本章要挖的是你大概沒深想過的那一層：**一張簽出去的 token，你要怎麼把它收回來？** 答案出乎意料地難——JWT 的「無狀態」這個賣點，正是它最深的故障源。你登出了，token 其實還活著；你封了一個帳號，他手上那張 token 在過期前照樣暢行無阻。本章先拆穿一個你很可能一直記錯的事（OAuth2 不是登入協定），再把 JWT 的簽章機制、access/refresh 的分工、以及「無狀態的撤銷困境」挖到底，最後算一筆 HS256 vs RS256 在多服務驗 token 時的金鑰分發帳。具體 IdP 產品不碰，OIDC 一句話帶過，加密演算法內部不展開。

## 從你已知的出發

你接過 JWT 登入。流程你太熟了：使用者輸帳密 → 後端驗證 → 簽一張 JWT 回去 → 之後每個請求帶 `Authorization: Bearer <token>` → 後端驗簽、放行。LetsTalk、NeoBards 都是這套。你也接過第三方登入——「用 Google 登入」那種，OAuth2 的 redirect、code、token 換來換去。RBAC 你也做過：使用者有個 `role` 欄位，admin 能做的事 user 不能，中間用 middleware 擋。

這些東西你**用得對**。流程沒接錯、token 沒簽歪、權限沒放穿。但「用得對」和「懂它底下」之間，這一章有三個落差要補。

**第一個落差，你可能一直把 OAuth2 當成「登入協定」。** 它不是。OAuth2 是**授權（authorization）框架**，回答的是「這個 app 能拿到什麼資源」，**不是**「這個使用者是誰」（authentication）。你以為的「用 Google 登入」，真正做身分認證的那一層是 OIDC（OpenID Connect），它是疊在 OAuth2 上面的另一張皮。你當年把整套都叫「OAuth 登入」，把兩件事混成一件——這個混淆不只是用詞不精確，它會讓你在設計時把「授權」和「認證」的責任邊界劃錯。

**第二個落差，你大概沒認真想過 JWT 的 payload 是「只簽不加密」。** 你印象裡 JWT 是「加密過的 token」——畢竟它看起來是一串亂碼。但那串「亂碼」只是 base64url 編碼，**不是加密**。任何人拿到你的 JWT，貼到 jwt.io 上，payload 裡的 `userId`、`role`、`email` 全都看得一清二楚。簽章保護的是**完整性**（沒被竄改），**不是機密性**（不被看見）。你要是當年在 JWT payload 裡塞過什麼不該被使用者看到的東西，那東西其實一直是公開的。

**第三個落差，也是本章的心臟——你登出之後，token 真的失效了嗎？** 你前端清掉 localStorage、跳轉回登入頁，使用者「登出」了。但那張 JWT 本身呢？它還在使用者手上、簽章還是有效的、過期時間還沒到。如果他在登出前把 token 複製下來，登出後拿那張 token 去打 API——**會過。** 因為你的後端驗 token 的方式是「驗簽 + 看過期時間」，這兩項它都還滿足。你「登出」的只是前端的狀態，不是 token 的效力。

這就帶出本章真正要挖穿的老問題：

**JWT 一旦簽出去，在它過期之前，你幾乎沒辦法讓它即時失效。** 封禁一個帳號、強制一個裝置登出、撤銷一個洩漏的 token——這些「即時生效」的需求，撞上 JWT「無狀態自驗」的設計，會撞出一個你當年大概靠「反正 token TTL 設短一點」糊弄過去、但從沒攤開看清楚的困境。這一章就把它攤開。

## OAuth2 是授權框架，不是登入

先把這個最常見的誤解校正掉，因為它影響你怎麼劃責任邊界。

**OAuth 2.0（RFC 6749）解決的問題是「委派存取」（delegated access）**：使用者想讓**第三方 app** 代表他去存取**另一個服務**上的資源，但**不想把自己的帳密交給那個 app**。

經典場景：一個第三方相簿沖印 app 想讀你 Google Photos 裡的照片。沒有 OAuth 的世界，你只能把 Google 帳密給那個 app——災難。OAuth 的世界，你被導到 Google、在 Google 上授權「允許這個 app 讀我的照片」、Google 發一張 **access token** 給那個 app，那個 app 拿 token 去 Google Photos API 取照片。**全程那個 app 沒碰到你的 Google 密碼。**

看清楚這裡面 OAuth 在回答什麼問題：**「這個 app 能對這些資源做什麼」**（what can this app do）。它**沒有**回答「使用者是誰」。access token 證明的是「持有者被授權存取某些資源」，**它不證明身分**——這是關鍵。一張 OAuth access token 不告訴拿到它的 app「剛剛是誰授權了這張 token」。

> **我以為 vs 實際**：你以為「用 Google 登入」＝OAuth。實際上做**登入**（認證、回答「你是誰」）的是 **OIDC（OpenID Connect）**——它是 2014 年疊在 OAuth2 上的**身分層**，多發一張 **ID token**（一定是 JWT），裡面裝著「使用者是誰」的 claims（sub、email、name、認證時間）。OAuth 管 authorization（能做什麼），OIDC 管 authentication（你是誰）。你當年把整套叫「OAuth 登入」，其實是 OIDC 在做登入、OAuth 在做後續的資源授權。（本章不展開 OIDC 全論——只要記住這條責任邊界：access token 用來存取資源、不該拿來當「使用者是誰」的證明；要證明身分用 ID token。把 access token 當登入憑證用，是一個有名的反模式。）

為什麼這個校正重要？因為**把「授權」和「認證」混為一談，會讓你在設計時犯一類具體的錯**：拿 access token 去推斷使用者身分。access token 是給「資源伺服器」看的、用來判斷「能不能存取這個資源」；它的受眾（audience）、它的內容，都不保證能拿來認證使用者。你若在自己的 app 裡用 access token 當「這個人已登入、他是 userX」的依據，就可能被一張「別的 app 拿到的、同一個使用者授權的 access token」騙過——這就是 token substitution 攻擊的土壤。

### 四種 grant，與現在的方向

OAuth2 定義了幾種拿到 token 的流程（grant type），對應不同的 client 形態。你當年大概只認真接過其中一兩種，但該知道現在的方向：

| Grant | 用途 | 2026 現況 |
|---|---|---|
| **Authorization Code** | 有後端的 web app／native app（最主流） | **推薦**，且**所有用它的 client 都強制要搭 PKCE** |
| **Client Credentials** | 沒有使用者、機器對機器（service to service） | 保留，正當用途 |
| **Implicit**（`response_type=token`） | 早期給純前端 SPA（token 直接回在 URL fragment） | **被移除**（不安全：token 漏在 URL/瀏覽器歷史） |
| **Resource Owner Password Credentials（ROPC）** | client 直接收使用者帳密去換 token | **被移除**（違背 OAuth「app 不該碰密碼」的初衷） |

這裡有一個**老兵記憶必須校正的事實**，而且它很容易被寫錯：

> **我以為 vs 實際**（時效，2026-06）：你可能聽說「OAuth 2.1 出了，把這些都標準化了」。**OAuth 2.1 在 2026-06 仍然是 IETF 的 Internet-Draft（草案），最新是 draft-15（2026-03-02 發布、Standards Track，預計 2026-09-03 到期），尚未成為 RFC。** 所以正確的講法是「OAuth 2.1 仍在 draft 階段」，**不要寫成「OAuth 2.1 標準／RFC」**——坊間「OAuth 2.1 Is Here」之類的標題很容易讓人誤以為它已凍結成正式標準（landscape §14）。

雖然還是 draft，但**方向已經非常明確、業界也照著走**，四個重點變更你該記住：

1. **PKCE（Proof Key for Code Exchange）對所有用 authorization code flow 的 client 強制必要**——不只 native/SPA，連有後端的 web app 也要。PKCE 用一組一次性的 `code_verifier`／`code_challenge` 把「授權碼被攔截後拿去換 token」這條攻擊路堵死。
2. **移除 implicit grant**——token 不再直接回在 URL，純前端 SPA 改走 authorization code + PKCE。
3. **移除 ROPC（password）grant**——app 不該經手使用者密碼，這條路徹底關掉。
4. **redirect URI 必須 exact string matching（精確比對）**——不准用前綴比對、不准用萬用字元。這擋的是「攻擊者註冊一個長得很像的 redirect URI、把授權碼導去自己那」的開放重導向攻擊。

```
 OAuth 2.1（仍是 draft-15，2026-06，非 RFC）的四個方向：
 ┌──────────────────────────────────────────────┐
 │ ① PKCE 對所有 auth code client 強制必要      │
 │ ② 移除 implicit grant（token 不再走 URL）    │
 │ ③ 移除 ROPC/password grant（app 不碰密碼）   │
 │ ④ redirect URI 精確字串比對（不准萬用字元）  │
 └──────────────────────────────────────────────┘
```

## JWT 機制：三段、簽章不等於加密

OAuth 講完了（它只是把 token 發給誰、怎麼發的框架），現在挖**那張 token 本身長什麼樣**。最常見的形態是 JWT（JSON Web Token，RFC 7519）。

一張 JWT 是三段 base64url 字串、用 `.` 隔開：

```
 eyJhbGciOiJIUzI1NiJ9 . eyJzdWIiOiI5OTMwMjEiLCJyb2xlIjoiYWRtaW4ifQ . dBjft...
 └────── header ──────┘ └──────────── payload ────────────────────┘ └ signature ┘
        (JOSE 標頭)            (claims，宣告)                          (簽章)
```

- **header**：JSON，宣告簽章演算法等，如 `{"alg":"HS256","typ":"JWT"}`。
- **payload**：JSON，裝 **claims**（宣告），如 `{"sub":"993021","role":"admin","exp":1750000000}`。標準 claims 有 `sub`（主體/使用者）、`exp`（過期時間）、`iat`（簽發時間）、`iss`（簽發者）、`aud`（受眾）、`jti`（token 唯一 ID）等。
- **signature**：對 `base64url(header) + "." + base64url(payload)` 用某把金鑰算出的簽章。

驗證一張 JWT，後端做的是：**(1)** 重算簽章、跟第三段比對——一致才代表沒被竄改、確實是可信來源簽的；**(2)** 檢查 `exp` 沒過期（以及 `iss`/`aud` 等）。**注意這整個過程不需要查資料庫**——只要有金鑰就能在本地完成。這就是 JWT 的賣點，也是它的詛咒，後面會看到。

### 簽章不是加密——payload 是公開的

這是你最該校正的一點。預設的 JWT（也就是 JWS，JSON Web Signature）**只簽不加密**。

base64 不是加密，base64url 也不是——它是**編碼**，是把 bytes 換成 URL 安全字元的可逆轉換，**沒有任何祕密**。任何人拿到你的 JWT，把中間那段 base64url 解碼，payload 裡的 `sub`、`role`、`email` 全都是明文。

> **這一段值得你停下來。** 因為你大概一直把 JWT 那串看起來像亂碼的東西當成「加密過、別人看不懂」。它看起來亂，只是因為 base64url 編碼後的 bytes 不是人類可讀的字元——但它**毫無機密性**。簽章保護的是**完整性與真實性**（integrity & authenticity：這內容沒被改、是持金鑰的人簽的），**不是機密性**（confidentiality：內容不被看見）。你能驗出「有人改了 payload 就簽章對不上」，但你**擋不住任何人讀 payload**。

要機密性得用 **JWE（JSON Web Encryption）**——那是另一種結構（五段而非三段），把 claims 真的加密起來。但實務上絕大多數 JWT 是 JWS（只簽），所以**鐵律是：JWT payload 裡不放任何不能讓 token 持有者看到的東西**（密碼、信用卡、內部敏感 ID 都不行）。你當年若在 payload 塞過敏感資訊，那資訊一直是對使用者公開的。

### access token vs refresh token：兩張票，兩種職責

成熟的設計不會只發一張 token，而是發兩張，職責分開：

| | **access token** | **refresh token** |
|---|---|---|
| 用途 | 帶在每個 API 請求上、證明「我有權存取」 | 拿來**換**一張新的 access token |
| 出示給誰 | 每個資源伺服器（高頻、到處跑） | 只給 authorization server（低頻、只在續期時） |
| 典型 TTL | **短**（15–60 分鐘） | **長**（數天～數週） |
| 形態 | 常是 JWT（自驗、無狀態） | 常是 opaque（不透明字串，伺服器端可查可撤） |
| 洩漏的代價 | 有限（很快過期） | 大（能一直換新 access token）——所以要能撤、要輪替 |

這個拆分的**動機**正是本章的核心問題：因為 access token 難撤銷，就讓它**短命**（壞了也很快自己失效）；因為使用者不想每 15 分鐘重登入一次，就給一張**長命但可撤銷**的 refresh token 去默默換新。**access token 換無狀態的高效驗證、refresh token 保留可撤銷的控制權**——這個分工不是慣例，是被「JWT 難撤銷」這個事實逼出來的設計。下一節把這個逼迫過程講透。

## 無狀態的撤銷困境

現在進本章的心臟。慢一點。

JWT 的賣點是**無狀態自驗**：資源伺服器拿到 token，靠金鑰在**本地**驗簽 + 看過期，**不必查任何中央 session 存儲**。這讓它水平擴展極好——十台、一百台服務各自驗 token，誰都不必去問一個中央的 session 庫「這張 token 還有效嗎」。

但「不必查中央存儲」這個優點，反過來說就是：**沒有任何中央存儲記得『這張 token 是否該失效』。** 於是問題來了——

**你要怎麼讓一張已經簽出去的 JWT 提前失效？**

傳統 session 的世界，這不是問題：session 狀態存在伺服器端（一個 session 表、一個 Redis key）。使用者登出，你刪掉那筆 session；要封誰，你刪掉他所有 session。下一個請求帶著舊 session ID 來，伺服器一查「查無此 session」，當場拒絕。**狀態在伺服器手上，所以撤銷只是一個 DELETE。**

JWT 的世界，這個 DELETE **無處可下手**——因為**根本沒有那筆狀態**。token 的「我有效」這件事，不記在伺服器任何地方，而是**自帶在 token 裡**（簽章對 + 沒過期 = 有效）。伺服器驗 token 時不查任何存儲，所以你「在存儲裡刪掉它」這個動作**沒有對象**。

> **核心困境一句話**：JWT 把「是否有效」這個狀態從伺服器端**移進了 token 自己**。這讓驗證無狀態（不必查庫，好擴展），但也讓撤銷無從下手（沒有庫可以刪）。**無狀態驗證和即時撤銷，是同一枚硬幣的兩面，你不能既要又要。**

### 把問題具體化：14 分鐘的窗口

回到你封禁帳號的場景。把它變成可以手追的時序：

- 你的 access token TTL 設 **15 分鐘**。
- 某使用者在 `T=0:00`（時鐘上的整點）剛換到一張新的 access token，所以這張的 `exp` 是 `T=15:00`。
- `T=1:00`，你發現他在搞鬼，後端把他**封禁**（`users.banned = true`）。

問題：**從 T=1:00 你按下封禁，到他那張 token 真正打不動 API，中間有多久？**

如果你的驗 token 邏輯是純 JWT 自驗（驗簽 + 看 `exp`），答案是——**14 分鐘**（從 1:00 到 15:00）。在這 14 分鐘裡，他那張 token 簽章仍對、`exp` 仍在未來，**每一個資源伺服器都會放行他**。你在資料庫裡把 `banned` 設成 true 了，但**沒有人會去查那個欄位**——因為 JWT 驗證的全部意義就是「不查庫」。

```
 T=0:00  使用者換到新 access token，exp = T=15:00
   │
 T=1:00  你按下「封禁」（DB: banned=true）
   │      ↓ 但純 JWT 驗證不查 DB……
   │  ┌────────────────────────────────────────┐
   │  │  T=1:00 ── 14 分鐘的「殭屍 token」窗口 ──┐│
   │  │  封了，但 token 還簽得對、還沒過期       ││
   │  │  每個資源伺服器照樣放行                  ││
   │  └─────────────────────────────────────────┘│
   ▼                                              ▼
 T=15:00 token 自然過期，他終於打不動了 ◄─────────┘
```

這 14 分鐘就是**殭屍 token 窗口**——帳號死了，token 還在走。對「使用者被盜、要立刻踢掉」「內容違規、要立刻封口」這類需求，14 分鐘可能就是出大事的 14 分鐘。

### 三種對策，與各自交回去的代價

要縮短或消滅這個窗口，有三條路，而每一條都在**還回 JWT 的某個優點**：

**對策一：把 access token TTL 設短（+ refresh 輪替）。**

把 access token 從 15 分鐘改成 **5 分鐘**，殭屍窗口最多就是 5 分鐘。再短到 1 分鐘，窗口 1 分鐘。極限地說，TTL 趨近零，窗口趨近零——但 TTL 越短，使用者就越頻繁地要用 refresh token 去換新 access token，**refresh 的流量越大、authorization server 的負載越重**。這條路**不消滅窗口，只壓縮它**：你拿「更頻繁的續期成本」去換「更短的殭屍窗口」。這也是為什麼要把 token 拆成短命 access + 長命 refresh——讓頻繁的那張是廉價可拋的，讓珍貴的那張低頻出現、且**可撤**。

封禁時你做的事是：在 DB 標記封禁、並讓他的 **refresh token 失效**（refresh token 多半是 opaque、可撤）。這樣他手上的 access token 最多再活一個 TTL（≤5 分鐘），到期想 refresh 時被拒，徹底出局。**封禁在「下一次 refresh」時才真正咬死他，殭屍窗口 = access token 的剩餘壽命。**

**對策二：撤銷 denylist（黑名單）。**

維護一份「被撤銷的 token」名單（通常存 Redis，存 token 的 `jti` 而非整張 token，並設 TTL 等於 token 剩餘壽命，過期自動清掉）。每個資源伺服器驗 token 時，**除了驗簽 + 看 exp，再多查一次 denylist**：在名單上就拒。

這條路能做到**接近即時撤銷**——你按下封禁、把 `jti` 寫進 denylist，下一個請求查 denylist 命中、當場拒。殭屍窗口縮到「寫入 denylist 並讓所有節點看到」的傳播延遲（次秒級）。

**但看清楚你付了什麼：** 為了查 denylist，每個資源伺服器**每個請求都多了一次對 Redis（或某中央存儲）的查詢**。驗 token 的成本從「驗簽（純本地）」變成「驗簽 + 查 Redis」。

> **這就是 denylist 的諷刺**：你引入 JWT 就是為了**無狀態、不查中央存儲**。現在為了能撤銷，你**又把中央存儲查詢加回來了**。denylist 把 JWT 最大的優點（無狀態自驗）**還了回去**——驗證重新依賴一個中央狀態（denylist），那它跟傳統 session「查中央 session 庫」在本質上越來越像，只是查的東西從「這 session 在不在」變成「這 token 在不在黑名單」。**這正是「短命 access + 長命可撤 refresh」那個拆分存在的理由**——它讓你**不必**對高頻的 access token 查 denylist（靠它短命自然失效），只在低頻的 refresh 環節保留撤銷能力，把「查中央存儲」的成本壓在最少的地方。

**對策三：版本號 / token 版本戳（折衷）。**

在使用者記錄上放一個 `token_version` 整數，簽 token 時把當下版本寫進 payload。要「撤銷某使用者的所有 token」時，就把 DB 裡他的 `token_version` +1。驗 token 時比對「token 裡的版本 == DB 裡的當前版本」，不符就拒。這比逐 token 的 denylist 粗（只能「撤這個人全部 token」、不能撤單一 token），但它換來的好處是 denylist 的記憶體不會無限增長——代價同樣是「每次驗 token 要查一次使用者的 version」，本質上還是把中央查詢加回來了，只是查得更輕。

把三條路擺成決策表：

| 對策 | 撤銷生效時間 | 交回去的代價 | 適合 |
|---|---|---|---|
| **短 TTL + refresh 輪替** | ≤ 一個 access TTL（壓不到零） | 更頻繁的 refresh 流量 | 大多數場景的預設、可接受秒～分鐘級窗口 |
| **denylist（查每個請求）** | 近即時（次秒級） | 每請求多查中央存儲——把無狀態優勢還回去 | 必須「立刻踢掉」的高敏感操作 |
| **token version（查使用者）** | 近即時，但只能整人撤 | 每請求查使用者 version；無法撤單一 token | 「封禁整個帳號」夠用、不需撤單一 token |

> **我以為 vs 實際**：你當年大概以為「JWT 登出 = 前端清掉 token 就好」。實際上前端清掉只是讓**這個瀏覽器**不再帶它，那張 token 本身**仍然有效**——複製出去照用。真正的撤銷，要嘛靠「短命 + 讓 refresh 失效」等它自己死，要嘛靠「把中央狀態加回來（denylist/version）」。**沒有「無狀態又能即時撤銷」這個免費選項**——這就是 JWT 撤銷困境的全部。

## RBAC：role/permission 模型，與該塞進 token 嗎

最後一塊：權限。你做過 RBAC（Role-Based Access Control），底子就是一個 `role` 欄位 + middleware 擋。把它挖一層。

**RBAC 的模型**：不直接把權限綁在使用者上，而是中間隔一層**角色（role）**——

```
 使用者 ──多對多── 角色（role） ──多對多── 權限（permission）
  user                admin                     reward:write
  user                editor                    settlement:read
                      viewer                    mail:send …
```

使用者被指派一個或多個角色，角色綁定一組權限。判斷「這人能不能做 X」＝「他的角色裡有沒有哪個含 X 權限」。好處是**管理收斂**：100 個編輯共用一個 `editor` 角色，要改編輯能做什麼，改一個角色定義就好，不必改 100 個人。

### RBAC vs ABAC 的分界

你該知道 RBAC 的邊界在哪、什麼時候它不夠用。它的對照組是 **ABAC（Attribute-Based Access Control，基於屬性的存取控制）**：

- **RBAC**：用**角色**決定權限。角色是預先定義好的、相對靜態的（admin / editor / viewer）。判斷只看「你是什麼角色」。
- **ABAC**：用**屬性 + 政策**決定權限。把使用者屬性、資源屬性、操作、環境屬性（時間、地點、裝置）全納入一條政策規則。例如「只有資源的擁有者本人、且在台灣境內、且在上班時間，才能匯出這份資料」——這種**條件式、上下文相關**的細粒度控制，RBAC 表達不出來（你不可能為每種條件組合都開一個角色，那會角色爆炸）。

判準：**角色結構穩定、責任分明 → RBAC**（簡單、好管、好稽核「誰能做什麼」）；**需要細粒度、隨上下文變、條件頻繁更新 → ABAC**（NIST 在多業務情境下傾向推薦 ABAC，因為它能用屬性組合出大量政策而不必逐一列舉使用者-資源對；代價是「分析或變更某個人實際有哪些權限」變難——RBAC 是預先把結構排好換取易於稽核，ABAC 反過來，易於設定但難以回答「這個人到底能碰什麼」）。實務上很多系統是 **RBAC 打底 + 少數 ABAC 規則補細粒度**的混合，不是二選一。（2026-06）

### token 裡塞權限 vs 每次查：本章和撤銷困境的回響

這是 RBAC 落到 JWT 上時的關鍵取捨，而且它**直接呼應前面的撤銷困境**。

**做法 A：把權限/角色塞進 JWT payload。**簽 token 時把 `role: admin` 或 `permissions: [...]` 寫進去。好處：判權限**不查庫**，純看 token，快、無狀態。

**做法 B：token 裡只放使用者身分（`sub`），每次請求**現查**他當前的權限**（查 DB/快取）。好處：權限**即時準確**。

看出來這跟 access/refresh、denylist 是同一個張力了嗎？**塞進 token = 用「過時的風險」換「無狀態的快」；每次查 = 用「查庫的成本」換「即時準確」。** 而塞進 token 的「過時風險」具體會怎麼咬你：

> **找出「把權限塞進 JWT」何時反咬你**：你把 `role: admin` 簽進一張 TTL 30 分鐘的 token。中途你把這人降權（admin → viewer，DB 改了）。但他手上那張 token 裡**還寫著 `admin`**，而你判權限只看 token——於是**接下來最多 30 分鐘，他仍是 admin**。這跟封禁的殭屍窗口是**完全同一個病**：token 裡的資訊（權限）是簽發那一刻的快照，DB 改了 token 不會跟著改。權限變更越是「必須立刻生效」（降權、收回危險權限），就越不該把權限塞進長命 token——要嘛 token 短命，要嘛關鍵權限現查。

決策框架：**權限穩定、變更不急（一般 role）→ 可塞進 token 換無狀態**；**權限敏感、變更要立刻生效（危險操作、降權封禁）→ 現查，別信 token 裡的快照**。一個常見的折衷是「粗粒度角色塞 token（夠用且穩定）+ 危險操作現查一次當前權限」。

## token introspection 與 HS256 vs RS256：金鑰怎麼分

收尾兩個機制問題，都跟「多服務」場景有關。

### token introspection（RFC 7662）：opaque token 的即時查詢

前面說 refresh token 常是 **opaque（不透明）**——它不像 JWT 自帶資訊，本身只是個隨機字串，所有資訊存在 authorization server。那資源伺服器拿到一張 opaque token，怎麼知道它有效、帶什麼權限？

答案是 **token introspection（RFC 7662）**：資源伺服器拿著 token 去打 authorization server 的 introspection endpoint，問「這張 token 還 active 嗎、帶什麼 scope」，authorization server 回一個 JSON（`active: true/false` + metadata）。

這正是 JWT 自驗的**反面**：

- **JWT（自驗）**：資源伺服器本地驗簽，**不問**任何人——無狀態、快、但難撤銷。
- **opaque + introspection**：資源伺服器**每次都問** authorization server——有狀態（中央說了算）、可即時撤銷（authorization server 一改 active 狀態，下次查就是 false），但每次驗 token 多一次網路往返。

看到沒？這又是同一枚硬幣。introspection 用「每次問中央」換「即時撤銷」——本質上跟 denylist 是同一個權衡的不同實作。**「無狀態自驗」和「即時可撤」這兩個，你永遠只能挑一個當主軸，另一個靠補丁逼近。**

### HS256 vs RS256：多服務驗 token 的金鑰分發帳

JWT 簽章用什麼演算法，在**多服務**場景下會變成一個**金鑰分發**問題。手算一筆帳。

- **HS256（對稱、HMAC-SHA256）**：簽和驗用**同一把祕鑰**。誰要驗 token，誰就得有那把祕鑰。
- **RS256（非對稱、RSA-SHA256）**：簽用**私鑰**、驗用**公鑰**。authorization server 拿私鑰簽，所有人拿公鑰驗。公鑰**可以公開散佈**。

把你的場景具體化：一個 authorization server 簽 token，**N 個資源伺服器**要驗 token。算金鑰怎麼分：

**HS256 的帳：** 那把祕鑰**簽和驗共用**，所以 N 個資源伺服器**每一個都得拿到那把祕鑰**才能驗。問題立刻出來——

1. **攻擊面 = N**：N 個服務都持有那把祕鑰。**任何一個被攻破，攻擊者就能偽造 token**（因為簽和驗同一把鑰）——他能簽一張 `role: admin` 的 token 騙過**整個系統**。N 越大，這個「任一被破即全盤淪陷」的風險越大。
2. **金鑰輪替是惡夢**：要換祕鑰，得**同時**把新鑰推到 N 個服務（不然有的用新鑰簽、有的拿舊鑰驗，對不上），或維護「過渡期同時接受新舊鑰」的邏輯。N 大時這是運維災難。

**RS256 的帳：** 私鑰**只有 authorization server 一個持有**，N 個資源伺服器**只拿公鑰**——

1. **攻擊面 = 1**：只有 authorization server 持私鑰。某個資源伺服器被攻破，攻擊者拿到的是**公鑰**——他能**讀**、能**驗** token，但**簽不出**新 token（簽需要私鑰）。**淪陷一個下游，不等於能偽造全系統的 token**。這是質的差別。
2. **金鑰輪替乾淨**：搭 **JWKS（JSON Web Key Set）**——authorization server 把公鑰掛在一個固定 URL（每把公鑰有 `kid` 鍵 ID），資源伺服器去抓、按 token header 的 `kid` 挑對應公鑰驗。輪替時 authorization server 在 JWKS 多掛一把新公鑰、用新私鑰簽，資源伺服器自動抓到新公鑰——**不必同步推鑰到 N 個服務**。

```
 HS256：N 個服務都要「簽=驗」的同一把祕鑰
   auth ──祕鑰──► svc1   ┐
        ──祕鑰──► svc2   ├─ 攻擊面 = N，任一破即可偽造全系統
        ──祕鑰──► svc3   ┘  輪替要同步推 N 把

 RS256：私鑰只在 auth，公鑰隨意散
   auth(私鑰簽)──公鑰──► svc1  ┐
              ──公鑰──► svc2  ├─ 攻擊面 = 1，下游破只能讀/驗、不能偽造
              ──公鑰──► svc3  ┘  輪替靠 JWKS 自動抓，不必同步推
```

> **決策框架，一句話**：**單一服務既簽又驗**（一個 monolith 自己發、自己用）→ **HS256** 夠了（簡單、快、沒有分發問題，祕鑰只在一處）。**一處簽、多處驗**（微服務、SSO、token 給別人驗）→ **RS256**——讓「能驗」和「能簽」分開，下游只能驗不能偽造，輪替靠 JWKS。你當年若是單體後端自簽自驗，HS256 是對的選擇；一旦拆成多服務、或要把 token 交給你不完全信任的服務去驗，HS256 的「驗者即可偽造」就是不該承受的風險，該換 RS256。

## 故障模式與防禦

身分與存取這個老問題會怎麼壞、壞了長什麼樣、怎麼防。至少一個綁定你真實的系統。

| 故障 | 壞了長什麼樣（可觀測徵兆） | 怎麼防 |
|---|---|---|
| **登出/封禁不即時生效**（殭屍 token 窗口，**你 LetsTalk/NeoBards 的 JWT 登入若純自驗**） | 帳號已封、使用者仍能打 API 一段時間；客服回報「我封了他怎麼還在發訊息」；稽核發現封禁時間與最後活動時間差一個 TTL | access token 短命（≤5–15 分鐘）+ refresh 可撤；高敏感操作上 denylist 即時撤；把「殭屍窗口最長 = access TTL」當設計常數，明說它不是零 |
| **把敏感資訊放進 JWT payload**（以為 base64 = 加密） | 沒有立刻可見的徵兆——直到有人解開 token 把內部 ID/個資貼出來；滲透測試/資安稽核才抓到 | 鐵律：payload 只放「可公開給 token 持有者看」的東西；要機密性用 JWE 或乾脆別放、改現查；別把密碼/卡號/內部敏感鍵塞進去 |
| **把權限塞進長命 token、降權不生效** | 降權後使用者仍以舊角色行動一個 TTL；「我明明把他從 admin 降了，他怎麼還刪得掉東西」 | 危險權限現查、別信 token 快照；或縮短 token TTL；粗粒度穩定角色才塞 token |
| **HS256 + 多服務：一個服務被破即可偽造全系統** | 某下游服務淪陷後，出現「簽得對但來歷不明」的 admin token；難追，因為簽章驗證通過、看起來合法 | 一處簽多處驗就用 RS256，讓下游只持公鑰（能驗不能簽）；HS256 只留給自簽自驗的單體 |
| **把 access token 當登入憑證/拿來認證身分**（OAuth/OIDC 責任混淆） | 偶發的 token substitution——A app 拿到的、同使用者授權的 token 被 B 處當「使用者已登入」接受 | 認證用 ID token（OIDC）、access token 只用來存取資源；驗 `aud`（受眾）確認 token 是發給「我」的 |
| **redirect URI 用前綴/萬用比對**（開放重導向） | 授權碼被導去攻擊者註冊的相似 URI；帳號被接管，但日誌看起來是「正常的 OAuth 流程」 | redirect URI **精確字串比對**（OAuth 2.1 方向）；搭 PKCE 讓攔到的授權碼也換不出 token |
| **refresh token 洩漏卻無法察覺/撤銷** | 攻擊者拿洩漏的 refresh token 持續換新 access token，帳號「永遠在線」；換 IP/裝置但 session 不斷 | refresh token **輪替（rotation）**：每次 refresh 發新的、舊的作廢；偵測「舊 refresh 被重用」→ 判定洩漏、撤銷整條 token 家族 |

注意這張表裡最陰險的兩類。一是**「沒有立刻徵兆」**（敏感資訊放 payload、access token 當登入用）——它們不會報錯、不會當機，要等資安稽核或被攻擊才現形，所以**設計時就要擋，不能等觀測抓**。二是**「簽得對但不該放行」**（HS256 下游被破偽造、權限快照過時）——簽章驗證通過讓它看起來完全合法，日誌也是一筆正常請求，**最難追**。通用的「靜默故障為什麼最致命」分類見《正常意外》（fail）；並發正確性（如 refresh 輪替的 race）想證明見《把系統寫成定理：TLA+》（tla）。

## 紙上推演

### 推演一：手追「封禁後，token 還活 14 分鐘」——各對策第幾秒生效 **[20 分鐘]** ★★

某使用者在時鐘 `T=0:00` 換到新 access token（TTL 15 分鐘，`exp = T=15:00`）。你在 `T=1:00` 按下封禁。

**問**：分四種驗證策略，各算出「從 T=1:00 按下封禁，到他真正打不動 API」的延遲——(a) 純 JWT 自驗（驗簽 + 看 exp，不查任何庫）；(b) 短 TTL：access TTL 改 5 分鐘、封禁時讓 refresh 失效（他正好也是 T=0:00 換的）；(c) denylist：封禁時把 `jti` 寫進 Redis denylist、每請求查；(d) token introspection：access token 改成 opaque、每請求向 authorization server introspect。對每種，說出它**用什麼換了什麼**。

### 推演二：判斷三個場景該用哪種 OAuth grant（含哪個已被 2.1 淘汰）**[15 分鐘]** ★★

**問**：為下面三個 client 各選一種 grant，並指出題目裡若有「已被 OAuth 2.1 方向淘汰」的選項是哪個、為什麼淘汰——(a) 一個有後端的 web app（伺服器端能保管祕密），要代表使用者存取資源；(b) 一個排程任務，沒有使用者、純機器對機器去呼叫另一個內部 API；(c) 一個純前端 SPA（沒有後端、跑在瀏覽器），早期有人提議「直接用 implicit grant 讓 token 回在 URL fragment」。

### 推演三：設計一套讓「即時封禁」可行的 token 策略，並說它犧牲了什麼 **[20 分鐘]** ★★★

你的產品出了新需求：**檢舉成立後，必須能在 5 秒內讓被封者徹底打不動任何 API**（用於即時封口違規內容）。你現在是純 JWT 自驗、access TTL 30 分鐘。

**問**：(a) 為什麼你現在的架構**做不到** 5 秒？最壞情況殭屍窗口多長？(b) 設計一套能滿足「5 秒內生效」的 token 策略——可以用短 TTL、denylist、introspection、token version 任意組合。(c) 你的設計**交回去了** JWT 的哪個優點？具體多了什麼成本（每請求、每秒多少次中央查詢，用你 LetsTalk ~3,200 並發連線的量級估個數量級）？(d) 一句話：有沒有「無狀態又能 5 秒即時封禁」的免費午餐？

### 推演解答

**推演一解答。**

(a) **純 JWT 自驗：14 分鐘**。從 T=1:00 到 T=15:00（token 自然過期）他都打得動——驗簽過、exp 在未來，而**沒有任何一步去查 DB 的 banned 欄位**。你在 DB 設了 banned=true，但沒人讀它。**用「無狀態（不查庫）」換來了「撤銷完全失效」。**

(b) **短 TTL（5 分鐘）+ 封禁時撤 refresh**：他 T=0:00 換的 access token `exp = T=5:00`。封禁（T=1:00）讓他的 refresh 失效。他手上的 access token 仍能用到 T=5:00（最多 **4 分鐘**殭屍窗口），T=5:00 過期後想 refresh 換新 → refresh 已撤 → 被拒、出局。**殭屍窗口 = access token 剩餘壽命（≤TTL）。用「更頻繁 refresh 的成本」換「更短的窗口」——但壓不到零。**

(c) **denylist：近即時（次秒級）**。封禁時把這張 token 的 `jti` 寫進 Redis denylist。下一個請求驗 token 時多查一次 denylist、命中、拒。延遲 ≈ 寫入 + 傳播到讀取節點的時間（次秒）。**用「每請求多查一次 Redis」換「近即時撤銷」——把無狀態優勢還回去了。**

(d) **introspection：近即時（次秒級）**。access token 改 opaque，每請求向 authorization server introspect。封禁時 authorization server 把該 token 標記 inactive，下一次 introspect 回 `active:false` → 拒。**用「每請求一次網路往返到中央」換「即時撤銷且中央說了算」——比 denylist 更徹底地放棄了自驗，每次都問中央。**

共通結論：(a) 是「全無狀態、零撤銷能力」，(c)(d) 是「全查中央、近即時撤銷」，(b) 是中間——**撤銷的即時性，跟「查中央存儲的頻率」嚴格正相關，你只能在這條軸上選位置，沒有兩端通吃。**

**推演二解答。**

(a) **Authorization Code（+ PKCE）**。有後端能保管 client secret，是最主流、最安全的流程；OAuth 2.1 方向是**所有**用 authorization code 的 client（含有後端的）都該搭 PKCE。

(b) **Client Credentials**。沒有使用者、純機器對機器，client 用自己的身分（client id + secret）直接換 token，不涉及使用者授權。這是 client credentials 的正當用途。

(c) **Authorization Code + PKCE**（不是 implicit）。implicit grant 讓 token 直接回在 URL fragment——token 會漏進瀏覽器歷史、referer、各種旁路，**已被 OAuth 2.1 方向移除**。純前端 SPA 現在的正解是 authorization code + PKCE：用一次性的 code_verifier/code_challenge，讓即使授權碼被攔截也換不出 token，補上「SPA 沒有後端能藏 secret」的缺口。**淘汰的是 (c) 題目裡提的 implicit。**（另外 ROPC/password grant 也被移除——app 不該經手使用者密碼。）

**推演三解答。**

(a) **做不到 5 秒，因為純 JWT 自驗根本不查任何中央狀態**——你封禁只是改了 DB，但驗 token 的路徑不讀 DB。最壞情況：某人剛換到新 token 你就封他，殭屍窗口 = 整個 TTL = **30 分鐘**。30 分鐘 ≫ 5 秒，差三個數量級。

(b) 要 5 秒內生效，必須把「是否被撤銷」這個狀態**移回中央、且每請求查**。最直接：**denylist**——封禁時把 `jti`（或對「整人封禁」用 `token_version` +1）寫進 Redis，每個資源伺服器每請求查一次。傳播到全節點次秒級，遠在 5 秒內。可搭配把 access TTL 也縮短（如 5 分鐘）當第二道保險、並縮短 denylist 條目的存活（= token 剩餘壽命，過期自動清，控制 denylist 大小）。

(c) **交回去了 JWT 的無狀態自驗**——驗 token 從「純本地驗簽」變成「驗簽 + 查 Redis denylist」。成本：**每個請求多一次 Redis 查詢**。估量級：~3,200 並發連線，假設每連線平均每秒約 1 個需鑑權的請求，就是**~3,200 次/秒**的額外 denylist 查詢（數量級 10³/s）。Redis 單機輕鬆扛這個量（它的瓶頸遠在更高，見 ch17），但你**已經不再是無狀態**了——驗證重新依賴一個中央存儲的可用性：**denylist 的 Redis 掛了，你要嘛 fail-open（放行、撤銷失效）要嘛 fail-close（全拒、服務中斷），兩個都難。**（這正是「短命 access + 長命可撤 refresh」想避免的：別讓高頻 access token 去查中央，把撤銷能力集中在低頻的 refresh。）

(d) **沒有免費午餐**。「5 秒即時封禁」要求驗 token 那一刻能看到「最新的撤銷狀態」，而最新狀態只存在中央——所以你**必須**每請求（或夠高頻地）查中央，這就放棄了無狀態。無狀態自驗和即時撤銷是同一枚硬幣兩面，5 秒這個硬指標逼你選了「即時撤銷」那一面，代價就是把無狀態交出去。

## 自我檢核

口頭自答，講得出來才算過關：

1. OAuth2 解決的是什麼問題（一句話）？為什麼說它是**授權**框架不是登入協定？做登入（認證）的那一層是誰？把 access token 當「使用者是誰」的證明，會出什麼問題？
2. JWT 三段各是什麼？為什麼說「簽章不是加密、payload 是公開的」？base64url 和加密差在哪？這推出什麼鐵律？
3. access token 和 refresh token 的職責怎麼分？這個拆分是被哪個問題逼出來的（提示：撤銷）？
4. 「無狀態的撤銷困境」一句話是什麼？為什麼 JWT 的「無狀態自驗」和「即時撤銷」是同一枚硬幣的兩面、不能既要又要？
5. 縮短 TTL、denylist、token version 三種撤銷對策，各**交回去**了什麼？為什麼說 denylist「把無狀態優勢還回去了」？
6. RBAC 的 role/permission 模型長什麼樣？它和 ABAC 的分界在哪、各自適合什麼？「把權限塞進 JWT」會在什麼時候反咬你（跟封禁的殭屍窗口是不是同一個病）？
7. HS256 vs RS256 在「一處簽、多處驗」場景下的金鑰分發帳怎麼算？為什麼 HS256 下「任一驗者被破即可偽造全系統」、RS256 沒這問題？你當年自簽自驗該用哪個、拆成多服務後呢？
8. token introspection（RFC 7662）跟 JWT 自驗是什麼關係（提示：同一枚硬幣的反面）？它用什麼換了即時撤銷？
9. OAuth 2.1 現在的狀態是什麼（draft 還是 RFC，2026-06）？它的四個方向是哪四個？implicit 和 ROPC 為什麼被移除？

## 延伸閱讀

- **The OAuth 2.1 Authorization Framework（draft-ietf-oauth-v2-1-15）**（[IETF Datatracker](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/)）：本章「OAuth 2.1 仍是 draft、不是 RFC」的一手出處。讀它對 PKCE 強制、移除 implicit/ROPC、redirect URI 精確比對的條文——別讀二手「2.1 Is Here」標題（會誤導成已成標準，landscape §14）。
- **RFC 7519 — JSON Web Token (JWT)**（[RFC Editor](https://www.rfc-editor.org/rfc/rfc7519.html)）：JWT 的權威定義。讀它的 §3「JWT 是 JWS 或 JWE」——本章「預設只簽（JWS）不加密、payload 是 base64url 不是密文」的源頭；要機密性才用 JWE。
- **RFC 7662 — OAuth 2.0 Token Introspection**（[RFC Editor](https://www.rfc-editor.org/info/rfc7662)）：opaque/可撤 token 怎麼向 authorization server 即時查 `active` 狀態。讀「active 的定義由 authorization server 決定（未過期、未撤銷、可用於此資源）」——本章「introspection 是 JWT 自驗的反面」的依據。
- **OpenID Connect**（[oauth.net/openid-connect](https://oauth.net/openid-connect/)）：補上本章一句話帶過的 OIDC——它如何在 OAuth2 上加一個身分層、發 ID token 回答「你是誰」。讀「OAuth 管授權、OIDC 管認證」這條責任邊界，校正「用 OAuth 登入」的口語混淆。
- **RS256 vs HS256: A deep dive into JWT signing algorithms**（[WorkOS](https://workos.com/blog/rs256-vs-hs256-jwt-signing-algorithms)）：把本章金鑰分發帳講得最清楚的一篇——HS256 共用祕鑰（驗者即可偽造、攻擊面 = N）vs RS256 公私鑰分離（下游只持公鑰、搭 JWKS 輪替）。對照本章「一處簽多處驗用 RS256」的決策框架。
- **RBAC vs. ABAC: What is the difference?**（[WorkOS](https://workos.com/blog/rbac-vs-abac)）：RBAC（角色決定權限、好稽核）與 ABAC（屬性 + 政策、細粒度但難回答「這人能碰什麼」）的分界與取捨，含 NIST 在多業務情境傾向 ABAC 的脈絡。讀「何時 RBAC 夠、何時要 ABAC」那段。
- 想把這條安全帶接回你的真實系統與全書——撤銷困境裡「每請求查中央存儲」的成本與 Redis 脾氣見 **ch17（快取與 Redis 內部）**；refresh 輪替的並發 race 屬於並發老問題、想證明它正確見《把系統寫成定理：TLA+》（tla）；「靜默故障為什麼最難抓」（簽得對卻不該放行、payload 洩漏無徵兆）的通用分類見《正常意外》（fail）。
