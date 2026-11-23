# 第 11 章：SSRF、URL Parser 混淆與 Web Cache Poisoning / Deception

## 從你已知的出發

為什麼商戶登記 Webhook 時，後端明明擋掉了 `127.0.0.1`、`localhost` 與 `10.0.0.0/8`，攻擊者送出的通知請求還是打進了本機 `9000` 埠的內部管理介面？又為什麼 Nginx 快取鍵已經把 `$scheme$request_method$host$request_uri` 全包進去了，一般商戶打開首頁卻還是載入到攻擊者植入的惡意腳本，甚至在未登入狀態下直接從 CDN 讀走別人的帳戶金鑰？

問題都出在同一個盲點：**負責「檢查規則」的元件，跟最後真正「執行動作」的元件，看到的根本不是同一個東西**。在 Webhook 場景裡，前置驗證器與底層 HTTP 客戶端用了不同世代的 URL 解析器，或是兩次 DNS 查詢之間出現了毫秒級的時間差；而在邊緣快取場景裡，CDN 與後端 Node.js 對「哪些標頭會改變回應內容」以及「怎麼折疊路徑裡的 `..%2f`」各有各的解讀。本章就把這兩條最常被鑿穿的跨元件邊界擺在一起，從字元級的解析差異一路拆解到連線層與快取層的根治方案。

---

## 機制與推導

### 攻擊者目標與實質影響

這兩類漏洞盯上的都是跨元件的認知落差，但奪取控制權與資料的方向各有分工：

先看 **SSRF（Server-Side Request Forgery，伺服器端請求偽造）與 URL 解析器混淆**。攻擊者的目標是挾持擁有內網位置與高信任權限的後端伺服器，替自己發起連線。一旦得手，就能繞過邊界防火牆掃描內網連接埠、直連只綁在 `127.0.0.1` 或私有網段的無密碼管理介面（像是內部 Prometheus、Redis 或未設防的微服務），甚至靠 Blind SSRF 的時間差探測內網存活主機（若進一步打進雲端中繼資料服務 IMDS 偷走 IAM 憑證，就會串成第 18 章的雲端控制平面提權）。

再看 **Web Cache Poisoning**（快取投毒）與 **Web Cache Deception**（快取欺騙）。這兩種手法都在操弄邊緣共享快取（CDN / Nginx）與源站之間的落差，但攻擊方向正好相反。

**Cache Poisoning 是「由外寫入」**：把夾帶惡意腳本或錯誤重導向的回應塞進正常頁面的公開快取鍵裡，讓單次請求的注入瞬間放大成全站級別的 Stored XSS 或服務癱瘓。**Cache Deception 則是「由內竊取」**：騙已登入的受害者點開一條「源站看來是個人敏感 API、快取層看來卻是公開靜態檔案」的網址，誘使快取層把受害者的個資、API 金鑰或帳本餘額存下來，攻擊者隨後只要發一筆匿名請求就能直接領走。

---

### URL Parser 分歧：RFC 3986 與 WHATWG 的正面衝突

很多後端工程師直覺以為「一個 URL 就只有一種拆法」。偏偏現代軟體堆疊裡同時活著兩套互不相容的標準，外加好幾十種寬鬆的自製實作：

一套是歷史悠久的 **RFC 3986**（URI Generic Syntax），定義了嚴謹的 `scheme://authority/path?query#fragment` 切分格式。像早期的 `curl`、Python `urllib.parse`、還有 Node.js 傳統的 `url.parse()` 大致走這個脈絡，但遇到反斜線 `\`、多個 `@` 或八進位 IPv4 時，各家的容錯與轉換規則卻五花八門。

另一套則是現代瀏覽器與新版執行環境（如 Node.js 的 `new URL()`、`fetch` / `undici`）全面採用的 **WHATWG URL Standard**。為了遷就瀏覽器網址列裡千奇百怪的人類輸入，WHATWG 規定解析前要先砍掉首尾的 C0 控制字元與空白，再把字串裡所有的 ASCII Tab、LF 與 CR（`\t` `0x09`、`\n` `0x0A`、`\r` `0x0D`）全部拔掉；遇到 `http`、`https`、`ws`、`wss`、`ftp`、`file` 這些特殊協定（special schemes）時，會自動把反斜線 `\` 轉成正斜線 `/`，還會把八進位、十六進位跟純十進位大整數的 IPv4 自動換算成標準的點分十進位。

只要系統裡的「網址檢查器（Validator）」跟「HTTP 發起器（Fetcher）」用了不同套解析器，對主機位址（Authority / Host）的切法或正規化方式對不上，駭客就能構造出「檢查器看是合法外部網域 A、發起器打出去卻連向內網主機 B」的雙面 URL。

#### 1. 使用者資訊（Userinfo）與反斜線 `\@` 的切分歧義

先看這串混合了反斜線與 `@` 的網址：

```text
http://127.0.0.1:8080\@webhook.merchant.example/cb
```

標準的網址格式是 `http://user:pass@host:port/path`。如果前置檢查器用的是嚴格驗證 RFC 3986 字元集的解析器，看到 userinfo 裡有沒編碼的反斜線就會直接拒絕；但如果檢查器只按 RFC 3986 的分隔符號（`/`、`?`、`#`）寬鬆切欄位（例如沒加額外字元檢查的 Python `urllib.parse.urlsplit`，或是常見的手寫正規表達式 `^https?://(?:[^/@]+@)?([^/:?#]+)`），它根本不把 `\` 當成路徑起點，於是把前面的 `127.0.0.1:8080\` 當成帳號密碼（userinfo），把 `@` 後面的 `webhook.merchant.example` 當成真正的主機名稱，開心蓋章放行。

結果這串網址一交給遵循 WHATWG 標準的 Node.js `new URL()` 或 `fetch()`（以及會先把 `\` 轉為 `/` 的 Node.js `url.parse()`），解析器看到 `\` 的那一刻就認定主機欄位已經結束了！於是主機瞬間變成 `127.0.0.1`、連接埠是 `8080`，而後面那串 `/@webhook.merchant.example/cb` 則全部退化成普通路徑。

#### 2. 空白與控制字元偷偷被吃掉

如果安全檢查是直接拿原始字串或正規表達式，去比對主機有沒有等於 `127.0.0.1` 或 `localhost`，攻擊者只要在網址中間塞進一個 Tab 或換行字元：

```text
http://12	7.0.0.1/admin   （中間夾了 \t 0x09）
http://local\rhost/       （中間夾了 \r 0x0D）
```

字面上的字串比對當然不會命中黑名單。但只要把這串字丟進 `fetch()`，WHATWG 解析器在進狀態機之前就會先把 `\t`、`\n`、`\r` 統統剝除，把網址完美還原成 `127.0.0.1` 與 `localhost`（後者再透過名稱解析指向本機回環位址）。這也是為什麼驗證流程除了必須統一解析器，遇到任何解析異常或怪異字元時，都得堅持預設拒絕（Fail-Closed）。

#### 3. IPv4 的花式變裝與 IPv6 映射位址

底層作業系統的 `inet_aton()` 與 WHATWG 解析器看得懂各種非標準的 IPv4 寫法，但 Node.js 舊版的 `url.parse()` 或單純的字串字首黑名單（像 `host.startsWith('127.')`）卻完全認不出來：

- **十六進位寫法**：`http://0x7f000001/` 或 `http://0x7f.0.0.1/`。
- **八進位寫法**：`http://0177.0.0.1/` 或 `http://0177.0000.0000.0001/`（八進位的 `0177` 換算成十進位正是 `1×64 + 7×8 + 7 = 127`）。
- **純十進位整數（DWORD）**：`http://2130706433/`（把四段數字展開：`127 × 256^3 + 0 × 256^2 + 0 × 256 + 1 = 2,130,706,433`）。
- **省略零寫法**：`http://127.1/`、`http://127.0.1/`。
- **IPv6 回環、未指定位址與 IPv4 映射位址**：這三種寫法的語意各不相同——`http://[::1]/` 是標準的 IPv6 回環位址（Loopback）；`http://[::]/` 是 IPv6 未指定位址（Unspecified，在多數 Linux 環境下連線時會直接路由到本機監聽介面）；而 `http://[::ffff:127.0.0.1]/` 則是把 IPv4 回環位址映射進 IPv6 的寫法（WHATWG 解析器還會自動把它轉成十六進位的 `http://[::ffff:7f00:1]/`，如果你的黑名單只傻傻檢查字串裡有沒有 `"127.0.0.1"`，當場就會被穿過）。

#### 4. Scheme 大小寫與 IDNA Unicode 正規化

有些自製解析器如果沒先對主機名稱做 Punycode（IDNA）正規化，或對 Unicode 全形與相容字元處理不一致，攻擊者傳入 `http://ⓛⓞⓒⓐⓛⓗⓞⓢⓣ/` 時，外層黑名單看不懂就放行了，進到下層支援 NFKC 正規化的網路函式庫時，卻被自動還原成 `localhost` 打進本機。

下面我們把這幾種經典的解析器認知落差擺進 Worked Example，直接對照傳統寬鬆解析器、Node.js `url.parse()` 與 WHATWG `new URL()` 面對同一串輸入時的真實輸出：

```text
=== Worked Example: URL 解析器分歧對照（寬鬆 RFC 3986 / legacy url.parse vs WHATWG new URL） ===

測試案例 1：反斜線與 @ 混淆（寬鬆 RFC 3986 分隔符解析 vs WHATWG / Node.js）
輸入 URL：http://127.0.0.1:8080\@webhook.merchant.example/cb

- 僅按 RFC 3986 分隔符切分的寬鬆解析（如未檢查非法字元的 urllib.parse.urlsplit 或正則擷取）
  -> hostname: 'webhook.merchant.example' （'\' 不視為路徑分隔符，'127.0.0.1:8080\' 被當成 userinfo）
- WHATWG new URL(u)（與預先正規化 '\' 為 '/' 的 Node.js url.parse）
  -> hostname: '127.0.0.1', port: '8080'   （'\' 被正規化為 '/'，pathname 變 '/@webhook.merchant.example/cb'）
- 實質後果：若前置 Validator 採上述寬鬆 RFC 3986 正則／跨語言閘道檢查，而後端 Fetcher 用 Node.js fetch(u)，
  Validator 會放行 'webhook.merchant.example'，Fetcher 卻實際向 127.0.0.1:8080 發起連線！

測試案例 2：Fragment (#) 與 @ 優先序混淆
輸入 URL：http://webhook.merchant.example#@127.0.0.1:8080/

- Node.js WHATWG new URL(u).hostname -> 'webhook.merchant.example'
- 部分未先切斷 '#' 的舊式手寫正則 `^https?://([^/]+)` 搭配贪婪 '@' 截斷邏輯：
  擷取 authority 時若只往後找最後一個 '@'，就會誤判主機為 '127.0.0.1:8080'（或反過來被繞過）。

測試案例 3：Node.js url.parse() vs WHATWG new URL() 的 IPv4 正規化與控制字元差異
輸入 URL：http://0177.0.0.1:8080/internal  與  http://2130706433:8080/internal

- Node.js legacy url.parse("http://0177.0.0.1:8080/internal").hostname
  -> '0177.0.0.1'                （保留原始八進位字串，不轉為 '127.0.0.1'，繞過 host.startsWith('127.')）
- Node.js legacy url.parse("http://2130706433:8080/internal").hostname
  -> '2130706433'                （保留原始十進位 DWORD 字串，繞過字首黑名單）
- Node.js WHATWG new URL("http://0177.0.0.1:8080/internal").hostname
  -> '127.0.0.1'                 （八進位 0177 = 127，WHATWG 自動正規化為標準點分十進位）
- Node.js WHATWG new URL("http://2130706433:8080/internal").hostname
  -> '127.0.0.1'                 （DWORD 2130706433 = 127.0.0.1，WHATWG 自動正規化）
- Node.js WHATWG new URL("http://12\t7.0.0.1:8080/internal").hostname
  -> '127.0.0.1'                 （自動剝除 \t 0x09，繞過未剝除控制字元的字面黑名單）
```

---

### DNS Rebinding 與 TOCTOU 時間差

假設團隊吃過虧，把檢查器跟發起器全部統一改成 `new URL()`，還乖乖加上了「先查 DNS 拿到 IP，確認不在私有網段（`127.0.0.0/8`、`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`、`169.254.0.0/16`、`::1`、`fc00::/7`）才准放行」的規則。這樣總安全了吧？

很遺憾，只要沒鎖住連線層，**DNS Rebinding（DNS 重新綁定）** 照樣能把這道防線打穿。

問題的根源正是第 1 章提過的 **TOCTOU**（Time-of-Check to Time-of-Use，檢查與使用分離）。檢查器呼叫 `dns.lookup(hostname)` 拿到一個合法的公網 IP、確認沒問題之後，交給下層 HTTP 客戶端的卻是**原本那串網域名稱**，而不是剛剛檢查過的那個 IP 位址。等到 HTTP 客戶端真正要建立新的 TCP 連線、而且本地解析器又沒命中 DNS 快取時，它就會**再呼叫一次**底層的 `getaddrinfo()` 去查同一個網域。

只要攻擊者自己架設這個網域的權威 DNS 伺服器（Authoritative Name Server），就能在前後兩次查詢之間瞬間變臉（以下假設解析環境未強制拉長 `TTL=0` 的快取時間）：

```text
時間軸 (ms)     NexusPay Webhook Worker               攻擊者權威 DNS (rebind.evil.test)
──────────────────────────────────────────────────────────────────────────────────────────
t = 0 ms        1. Validator 解析 URL
                2. 呼叫 dns.lookup("rebind.evil.test") ──> 收到 Query #1
t = 12 ms       <── 回傳 A 記錄: 93.184.216.34 (TTL = 0)
                3. 檢查 IP 93.184.216.34：非私有網段，允許！
t = 13 ms       4. 呼叫 fetch("http://rebind.evil.test:8080/admin")
                5. 建立新連線且無本地 DNS 快取，再次呼叫 getaddrinfo() ──> 送出 Query #2
t = 25 ms       <── 回傳 A 記錄: 127.0.0.1 (TTL = 0)
t = 26 ms       6. 向 127.0.0.1:8080 發起 TCP 握手並送出 HTTP 請求 ──> 觸及本機內部管理端點
```

這裡有個實務細節常讓工程師誤以為自己免疫：很多容器或雲端環境的上游 DNS 解析器會強制設定最小快取時間（例如就算權威 DNS 回傳 `TTL=0`，本地還是強迫快取 `1` 到 `5` 秒，此處為部署環境假設值）。遇到這種防護，單靠毫秒級連續查兩次確實會讀到快取裡舊的公網 IP。

但攻擊者馬上能換兩招拆解：
第一招是**多筆 A 記錄輪替**。權威 DNS 一次回傳 `[93.184.216.34, 127.0.0.1]` 兩筆紀錄；如果檢查器只偷懶看第一筆 `ips[0]` 就放行，而後面的 HTTP 客戶端因為連不上第一筆公網 IP（攻擊者故意把該公網 IP 的 port 關掉）、或是照輪詢機制自動 fallback 改連第二筆未受檢的 `ips[1]`，防線當場破功。
第二招是**算準快取過期再延遲觸發**。在 NexusPay 這類非同步架構裡，「登記時驗證網址」跟「背景佇列實際發送 Webhook（或失敗重試）」往往隔了好幾秒甚至幾分鐘。只要兩者間隔超過那 `5` 秒的本地快取存活期，發送端又沒有重用舊連線而重新觸發 DNS 解析，第二次查詢就會乖乖找上攻擊者的權威 DNS，拿到新鮮出爐的 `127.0.0.1`。

---

### Blind SSRF 與側通道推斷

並不是每個 SSRF 漏洞都會好心地把內網網頁的 HTML 或 JSON 原封不動吐回前端。像在 NexusPay 的非同步 Webhook 架構裡，商戶觸發測試按鈕後，API 往往只冷冷回一句「已排入佇列（`202 Accepted`）」或「目標連線失敗」。這種能逼伺服器往內網亂打、卻看不到回應內容的狀況，就叫做 **Blind SSRF**。

就算沒有直接回顯，攻擊者還是有三種辦法把戰果榨乾：

第一是 **Out-of-Band（OOB）外帶互動**。先讓伺服器連向攻擊者自己在公網架的 DNS 或 HTTP 監聽器，直接從連線紀錄看穿伺服器的對外出口 IP（受遞迴解析器與 NAT／代理影響）以及 `User-Agent` 標頭，一眼摸清底層用的是哪套 HTTP 函式庫跟版本。

第二是**錯誤狀態與時間差側通道**。打向內網某個關閉的連接埠時，作業系統通常幾毫秒內就會收到 `RST`（`ECONNREFUSED`）馬上報錯；但如果是打向不存在的內網 IP 或被防火牆 `DROP` 的網段，連線就會一直卡到 HTTP 客戶端的連線逾時（connect timeout）或 TCP SYN 重傳逾時才失敗（如果前端是同步等待結果，甚至會一路頂到入口 Nginx 的 `proxy_read_timeout = 30 s` 而噴出 `504`）。更別提有些貼心的 Webhook 後台會把每次投遞收到的 `200 OK` 或 `404 Not Found` 狀態碼記在歷史列表裡，這等於直接送給攻擊者一台內網連接埠與路由掃描器。

第三則是**射後不理的狀態改變（Fire-and-Forget）**。只要內網裡躺著任何「單靠一筆 GET 或無認證 POST 就能觸發動作」的脆弱服務——像是沒設密碼的內部 Jenkins 建置端點、舊版 Elasticsearch 的狀態變更 API，或是能透過 URL 參數夾帶命令的內部管理介面——Blind SSRF 造成的破壞力跟能讀回回應的 Full-Read SSRF 完全沒兩樣。

---

### Web Cache Poisoning：當 Unkeyed Input 遇上共享快取

現在把鏡頭從後端往外拉到 NexusPay 大門口的 Nginx 與 CDN 邊緣快取。Web 快取的運作邏輯很單純：只要判斷兩筆請求「長得一樣」，就直接把上一筆存下來的回應拿出來餵給下一位使用者，幫後端省下重複運算的力氣。

那快取層是怎麼判斷兩筆請求「長得一樣」的？它並不會笨到把整包 HTTP 請求拿去做雜湊，而是只挑出少數幾個關鍵欄位拼成一把 **Cache Key（快取鍵）**。來看一行最標準的 Nginx 快取設定：

```nginx
proxy_cache_key "$scheme$request_method$host$request_uri";
```

這行設定看似天衣無縫，其實暗藏了一個超大的安全前提：**凡是會被寫進共享快取的回應，在沒有另外用 `Vary` 標頭區分版本的前提下，除了協定、方法、Host 與網址路徑這四個變數之外，請求裡的其他所有東西（額外的 HTTP Header、Cookie、甚至請求主體）都絕對不能影響後端吐出來的內容！**

任何沒有被放進 `proxy_cache_key`（也沒有納入有效 `Vary` 變體選擇）、卻被後端拿來決定回應內容的輸入欄位，就叫做 **Unkeyed Input（未鍵入輸入）**。

一旦系統裡存在 Unkeyed Input，攻擊者就能按以下三步曲發動精準的**快取投毒（Web Cache Poisoning）**：

#### 第一步：掛上 Cache Buster 探測未鍵入輸入

在尋找破口的測試階段，攻擊者最怕兩件事：一是不小心把半成品的測試 payload 寫進正式首頁的快取裡驚動管理員；二是首頁剛好已經有別人留下的正常快取（`HIT`），導致自己的測試請求根本沒打到後端源站，誤以為漏洞不存在。

所以在查詢字串有被納入快取鍵的前提下，老手測試時一定會先在網址後面掛一個隨機的**快取破壞參數（Cache Buster）**，比如 `?cb=98421`，確保每一發測試都擁有自己獨立的快取鍵、百分之百穿透到源站。接著開始輪番餵入各種常見的未鍵入標頭，看源站會不會傻傻把它們反射進回應裡：

- `X-Forwarded-Host`、`X-Host`、`X-Forwarded-Server`：許多前端框架或後端模板超愛用它來動態拼湊靜態資源網址（像 `<script src="https://<X-Forwarded-Host>/app.js">`）、OpenGraph 標籤或絕對重導向連結。
- `X-Forwarded-Scheme` / `X-Forwarded-Proto`：如果故意傳入 `http`，有些後端會立刻回傳 `302 Found` 強迫跳轉到 `http://...`，再配上一顆竄改過的 `X-Forwarded-Host`，馬上就能把整站流量劫持走。
- `X-Original-URL` / `X-Rewrite-URL`：部分框架或舊版中介軟體看到這兩個標頭時，會優先拿它來覆蓋掉真正的請求路徑！結果快取層看到的快取鍵明明是 `/static/logo.png`，源站實際執行的卻是 `/error?msg=<script>...`，最後這包錯誤頁就被存進了 `/static/logo.png` 的快取裡。

#### 第二步：算準可快取性與 Age 過期視窗

確認某個標頭會被反射後，接著看回應標頭裡的 `Cache-Control: public, max-age=60`、第一次請求的 `X-Cache: MISS`、第二次請求的 `X-Cache: HIT`，以及最重要的 `Age` 標頭。

假設快取有效期限是 `max-age=60`，而你現在看到的回應帶著 `Age: 52`，簡單算一下 `60 - 52 = 8`，就知道這份舊快取再過約 **8 秒**就會過期（stale），屆時下一筆進來的請求就會觸發源站重新抓取。

#### 第三步：拔掉 Cache Buster 精準投毒

算準第 8 秒舊快取剛過期的那一刻，攻擊者拔掉 `?cb=98421`，對真正的公開網址（如 `/login` 或 `/portal`）送出夾帶惡意標頭的請求：

```http
GET /portal HTTP/1.1
Host: nexuspay.example
X-Forwarded-Host: attacker.example"><script>alert(document.domain)</script>
```

只要這筆請求搶在正常使用者之前碰到快取層、順利拿到 `MISS` 並讓源站吐回符合共享快取寫入條件的 `200 OK` HTML，這包帶著 XSS 腳本的回應就會正式霸占 `/portal` 的公開快取鍵。在接下來的 `60` 秒新鮮期內（而且攻擊者每 60 秒還能自動補刀一次），全天下所有訪問 `https://nexuspay.example/portal` 的正常用戶，不用點任何釣魚連結，就會直接從 CDN 收到這份毒網頁（實際腳本能否執行仍視瀏覽器環境與 CSP 防護而定）。

除了標準的 HTTP Header，實戰中還有兩種防不勝防的隱蔽變體：
一種叫 **Parameter Cloaking（參數隱匿）**。很多 CDN 為了拉高快取命中率，會自動把 `utm_source`、`fbclid` 這類行銷追蹤參數從快取鍵裡剔除（變成 Unkeyed Query Parameter）。如果 CDN 只認得用 `&` 切分參數，後端特定框架卻同時把分號 `;` 也當成參數分隔符，攻擊者只要送出 `GET /api/config?utm_source=1;callback=alert(1)`：CDN 以為整串都只是 `utm_source` 的值而把它整段從快取鍵抹掉（快取鍵變成乾淨的 `/api/config`），後端卻從分號後面切出了 `callback=alert(1)` 並吐回惡意 JSONP 腳本，直接把 `/api/config` 的公開快取給毒死。
另一種則是 **Fat GET Request**。攻擊者發送 `GET /search?q=1`，卻在底下的 HTTP Request Body 裡偷偷塞入 `q=<script>...`。共享快取層在算 `GET` 請求的快取鍵時根本不會去看 Request Body，但如果後端路由剛好掛了不分方法的主體解析器、甚至把 `req.body` 的欄位合併進查詢參數裡優先讀取，這個 GET 主體就成了最危險的 Unkeyed Input。

---

### Web Cache Deception：路徑正規化與副檔名的雙重誤會

看完「由外寫入」的快取投毒，再來看剛好鏡像反轉的 **Web Cache Deception（快取欺騙）**。在這裡，**快取鍵本身完全沒問題**，出事的是**快取層的「快取決策規則」跟後端源站的「路由解析器」對同一條網址路徑產生了完全不同的解讀**。

最常出事的現場，就是工程師為了幫 Node.js 減壓，在 Nginx 或 CDN 上寫了這段「只要看到靜態副檔名就強制快取 1 小時」的加速規則：

```nginx
# 常見卻極危險的寫法：只看網址結尾副檔名就強制快取，還硬把源站的 Cache-Control 蓋掉
location ~* \.(css|js|png|jpg|ico)$ {
    proxy_pass http://nexuspay_backend;
    proxy_cache static_cache;
    proxy_cache_valid 200 60m;
    proxy_ignore_headers Cache-Control Expires Set-Cookie;
}
```

為了怕後端框架預設吐出的防快取標頭讓加速失效，工程師還貼心地加了一行 `proxy_ignore_headers Cache-Control Expires Set-Cookie`。殊不知，只要遇到下面三種路徑混淆手法，這段設定馬上就會變成出賣用戶個資的提款機：

#### 1. 尾隨路徑忽略（Path Mapping Discrepancy）

有些後端框架或傳統 REST 路由器在處理 `/v1/merchant/profile` 時，就算收到的是 `/v1/merchant/profile/nonexistent.css`，也會自動忽略後面多出來的路徑片段，照常根據使用者的 Cookie 查出商戶個人資料並回傳 `200 OK` JSON。但外層 Nginx 的正規表達式 `\.(css|js|...)$` 一看到網址結尾是 `.css`，加上 `proxy_ignore_headers` 把源站的保護標頭全無視了，就二話不說把這包內含商戶 API 私鑰的 `200 OK` 回應存進公開的 `static_cache` 裡。

#### 2. 路徑分隔符號認知落差（Delimiter Discrepancy）

就算後端路由寫得很嚴格，看到 `/v1/merchant/profile/a.css` 會乖乖回傳 `404`，只要快取層跟源站對「哪個字元代表路徑結束」認知不同，照樣會出事。最經典的就是分號 `;`（Matrix Parameters）：像 Java Spring / Tomcat 這類伺服器預設會把 `;` 後面的字串當成路徑參數直接切掉，但許多 CDN 卻把 `;v=1.css` 當成一般檔名的一部分。攻擊者只要騙已登入的受害者載入 `/v1/merchant/profile;v=1.css`，後端切掉分號執行 `/v1/merchant/profile` 吐出敏感個資，CDN 則看到結尾是 `.css` 把它存進公開快取。

#### 3. 點段正規化差異（Dot-Segment Normalization Discrepancy）

這是近年各大商用 CDN 與源站之間最常爆出快取欺騙的頭號破口。假設團隊學乖了，不再看 `.css` 副檔名，把 CDN 快取規則改成「只快取前綴為 `/static/` 目錄下的路徑」；偏偏 CDN 在比對這條前綴規則時，**不會**先把百分比編碼的斜線 `%2f` 解開並折疊裡面的 `..` 點段。

這時攻擊者只要構造這條路徑，誘使帶著 Session Cookie 的受害者發出請求：

```http
GET /static/..%2f..%2fv1/merchant/profile HTTP/1.1
```

我們來看看這條網址流過兩個元件時發生了什麼事：

```text
[Victim (帶著合法的 Session Cookie)]
   │
   ▼  GET /static/..%2f..%2fv1/merchant/profile
┌──────────────────────────────────────────────────────────┐
│ CDN / Nginx 邊緣快取                                     │
│ 1. 規則檢查：路徑字面開頭是 /static/ -> 命中靜態快取規則 │
│ 2. Cache Key = "/static/..%2f..%2fv1/merchant/profile"   │
│ 3. Cache MISS -> 原封不動把原始路徑轉發給後端源站        │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼  先解碼 %2f 為 / -> 再折疊兩個 ../ 點段
┌──────────────────────────────────────────────────────────┐
│ NexusPay 後端源站 (Nginx / Node.js)                      │
│ 正規化後的實際路由變成 /v1/merchant/profile              │
│ 驗證受害者 Cookie 成功 -> 回傳 200 OK + 帳戶機密 JSON    │
└──────────────────────────┬───────────────────────────────┘
                           │
                           ▼  CDN 依靜態快取規則判定符合條件並寫入共享快取
[Attacker (完全匿名、不帶任何 Cookie)]
   │
   ▼  GET /static/..%2f..%2fv1/merchant/profile
   └──> CDN Cache HIT！直接從邊緣節點領走受害者的機密 JSON
```

在 CDN 眼裡，因為斜線被編碼成了 `%2f`，未先解碼的路徑匹配器不把 `..%2f` 當成往上跳一層的 `/../` 目錄，只看到字串乖乖以 `/static/` 開頭，當場蓋章認定這是公開靜態檔案。但請求一進到後端源站，伺服器先把 `%2f` 解碼回 `/`，接著把 `/static/../../v1/merchant/profile` 裡的兩個點段一折疊，路徑瞬間變回 `/v1/merchant/profile`！只要代理組態與快取資格允許寫入，受害者的機密資料就被鎖進 `/static/..%2f..%2fv1/merchant/profile` 這把公開快取鍵裡，等著攻擊者匿名取貨。

---

## 故障模式與防禦

看清解析器分歧與時間差是怎麼鑿穿邊界的，我們把這兩大類漏洞最常踩坑的「假修補（故障模式）」與真正能鎖死不變量的工程防線整理如下。

### 故障模式 1：用字串黑名單擋 SSRF，或檢查完把原始網址丟給 `fetch()`

很多團隊修 SSRF 時，第一反應就是寫個正規表達式擋掉 `127.0.0.1`、`localhost` 和 `10.` 開頭的字串；講究一點的會先呼叫一次 `dns.lookup()` 檢查 IP，沒問題就把原本那串 `rawUrl` 傳給 `fetch(rawUrl)`，而且還忘了關掉 HTTP `30x` 自動重導向。

這三種做法全都守不住：字串黑名單隨便用八進位 `0177.0.0.1`、整數 `2130706433`、IPv6 映射位址 `[::ffff:127.0.0.1]` 或外部指向本機的網域（如 `localtest.me`）就能穿過；檢查完把原始網域交給 `fetch()` 會直接掉進 DNS Rebinding 的 TOCTOU 時間窗；而只要沒關自動重導向，攻擊者只要先給一個合法的公網網址 `https://evil.example/ok`，等伺服器連過去時回傳 `302 Found -> Location: http://127.0.0.1:8080/admin`，HTTP 客戶端就會傻傻自己跳進內網。

要真正鎖死 SSRF，必須在應用層與網路層同時築起四道防線：

| 防禦層級 | 容易被穿破的寫法 | 真正能鎖死邊界的工程做法 |
|---|---|---|
| **URL 與 IP 格式檢查** | 用字串字首或舊版 `url.parse()` 比對黑名單 | **統一用 WHATWG `new URL()` 解析，並轉成標準二進位位址做 CIDR 攔截**：一律透過 `net.BlockList` 阻斷所有保留與私有網段（涵蓋 `0.0.0.0/8`、RFC 1918 私有網段、`127.0.0.0/8`、`169.254.0.0/16`、`100.64.0.0/10`、以及 IPv6 的 `::/128`、`::1/128`、`fc00::/7`、`fe80::/10` 與 `::ffff:0:0/96` 映射位址）。 |
| **DNS 解析與連線建立** | `dns.lookup()` 檢查只看第一筆 `ips[0]`，通過後把網域名稱交給 HTTP Client 重新解析 | **全數檢查候選 IP + 連線層 IP Pinning（釘選）**：以 `dns.lookup(host, { all: true })` 取出所有回傳位址，只要有任一筆落入保留網段就當場拒絕；通過後在底層 `http.request` / `undici` 的自訂 `lookup` 回呼裡直接回傳那顆已驗證的 IP，絕不讓底層再發第二次 DNS 查詢（同時保留原本的 `Host` 標頭與 TLS SNI）。 |
| **HTTP 重導向處理** | 沿用 HTTP Client 預設的自動跟隨重導向（`redirect: "follow"`） | **預設禁止重導向（`redirect: "manual"`）**：遇到 `3xx` 直接拒絕；若業務非得跟隨重導向不可，每一跳（Hop）都必須重新跑完「URL 解析 → DNS 全數檢查 → CIDR 攔截 → IP Pinning」全套流程，並嚴格限制最大跳數（如 `<= 3`）。 |
| **架構與網路隔離** | 只靠應用程式碼裡的 `if/else` 把關，漏掉某個第三方 PDF/SVG 轉檔套件的內部請求 | **網路層 Egress 強制隔離**：把所有需要代替使用者往外抓資料的服務（如 Webhook Worker）關進獨立的子網段或 K8s Namespace，規定只能透過帶有嚴格 ACL 的 Egress Proxy（如 Envoy / Squid）出網，並在 K8s `NetworkPolicy` 明確封死任何連往內網 CIDR 與雲端 IMDS（`169.254.169.254`）的封包。 |

### 故障模式 2：放任外部覆寫標頭穿透進源站，忘了對齊快取鍵與 `Vary`

當邊緣的 Nginx 或 CDN 沒有先把外部使用者偽造的 `X-Forwarded-Host`、`X-Original-URL`、`X-Rewrite-URL` 洗乾淨，直接原封不動轉發給後端，而這幾個標頭又不在 `proxy_cache_key` 裡面時，整座共享快取就成了任人塗鴉的公佈欄。

防禦 Web Cache Poisoning 的原則很明確：**消除所有未受追蹤的輸入影響**。
第一，在最外層的反向代理（Nginx / CDN）入口處，除非架構明確需要且已經做好安全對齊，否則一律清空或由代理自己覆寫這些敏感標頭：

```nginx
proxy_set_header X-Forwarded-Host "";
proxy_set_header X-Original-URL "";
proxy_set_header X-Rewrite-URL "";
```

第二，如果後端確實需要根據某個請求標頭來改變可共享回應的內容（例如看 `Accept-Encoding` 決定壓縮格式，或看 `Origin` 動態決定 CORS 回應標頭），源站在回傳時就必須老老實實掛上對應的 `Vary` 標頭（如 `Vary: Accept-Encoding, Origin`），或是直接把該欄位加進 `proxy_cache_key`，絕不能讓快取層跟源站各看各的。

### 故障模式 3：只看副檔名就硬上快取，還無視源站的 `Cache-Control`

為了貪圖快取命中率，在 Nginx 寫下 `location ~* \.(css|js|png)$` 就強制快取，甚至加上 `proxy_ignore_headers Cache-Control Set-Cookie` 把後端的保護機制拔掉，這正是引發 Web Cache Deception 的元兇。

要徹底杜絕快取欺騙，必須從源站標頭與邊緣規則兩頭同時鎖緊：
1. **絕對不單憑網址結尾副檔名決定快取**，更嚴禁在有動態 API 的上游設定 `proxy_ignore_headers Cache-Control Set-Cookie`。
2. **源站對所有動態與驗證端點預設拒快取**：凡是會讀寫 Cookie、驗證身分或吐出個人動態資料的路由，由後端中介軟體統一預設打上 `Cache-Control: no-store, private`，並確保外層代理百分百尊重源站的快取指令。
3. **快取層實施雙重條件核對**：只有當「請求路徑明確落在專用靜態目錄下（如 `^~ /static/assets/`，且沒有未折疊的點段）」**而且**「源站明確回傳 `Cache-Control: public, max-age=...`、同時回應的 `Content-Type` 也真的是靜態資源型別（絕不快取 `Content-Type: application/json` 或 `text/html` 的 `.css` 請求）」時，才准許寫入共享快取。
4. **統一先解碼正規化、再比對路由規則**：在邊緣層一定要先做完 URI 解碼與點段折疊（`..`），再去跑快取規則與路由分派，不給 `..%2f` 任何偷渡的空間。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

現在我們在本地隔離環境（零雲端費用）親手拆解並修補 NexusPay 的兩道邊緣防線：一邊是負責派發結算通知的 Webhook 驗證器與抓取器，另一邊則是擋在 API 前方的 Nginx 快取組態。

### 實驗一：突破 Webhook SSRF 黑名單並實作連線層 IP Pinning

先看下面這段從 NexusPay 抽出來、還沒修補的 Webhook 檢查器（`validator.js`）與背景發送器（`fetcher.js`）：

```javascript
// validator.js（有漏洞的實作）
const url = require('url');
const dns = require('dns').promises;

async function validateWebhookUrl(rawUrl) {
  const parsed = url.parse(rawUrl); // 破口 1：用舊版 url.parse()，不會把八進位或 DWORD IPv4 正規化
  if (!['http:', 'https:'].includes(parsed.protocol)) throw new Error('Invalid protocol');
  const host = parsed.hostname;
  if (!host || host === 'localhost' || host.startsWith('127.')) {
    throw new Error('Blocked host');
  }
  // 破口 2：誤以為只由數字跟點號組成的主機已經被上面的 startsWith('127.') 擋完了而跳過 DNS 查詢；
  // 對一般網域也只查一次字首、沒做連線層 IP Pinning (留下 TOCTOU 時間窗)
  if (!/^[0-9.]+$/.test(host)) {
    const { address } = await dns.lookup(host);
    if (address.startsWith('127.') || address.startsWith('10.')) {
      throw new Error('Blocked private IP');
    }
  }
  return rawUrl; // 原封不動把原始字串傳給下一層
}

// fetcher.js
async function sendWebhook(rawUrl) {
  // 破口 3：改用 WHATWG fetch()，跟 url.parse() 解析規則不同，而且會重新查 DNS 並自動跟隨 3xx 重導向
  const res = await fetch(rawUrl, { method: 'POST', body: JSON.stringify({ event: 'settled' }) });
  return res.status;
}
```

- **任務 1A**：請構造出至少兩條能合法通過 `validateWebhookUrl()` 檢查，卻會讓 `sendWebhook()` 實際把 POST 請求打向本機 `http://127.0.0.1:9000/internal/metrics` 的畸形 URL。
- **任務 1B**：改寫上面兩支函式，統一換成 WHATWG `new URL()`、搭配 `net.BlockList` 完整攔截保留網段、加上自訂 `lookup` 回呼（IP Pinning）並拒絕 `3xx` 重導向，確認 `0177.0.0.1`、`[::ffff:127.0.0.1]` 與 `\@` 混淆全部被擋下。

### 實驗二：Nginx 快取投毒與快取欺騙實測

接著看這份問題百出的本地 Nginx 快取設定：

```nginx
proxy_cache_path /tmp/nginx_cache levels=1:2 keys_zone=nexus_cache:10m max_size=50m;

server {
    listen 8080;
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_cache nexus_cache;
        proxy_cache_key "$scheme$request_method$host$request_uri";
        proxy_cache_valid 200 60s;
        add_header X-Cache-Status $upstream_cache_status;
    }
    location ~* \.(css|js)$ {
        proxy_pass http://127.0.0.1:3000;
        proxy_cache nexus_cache;
        proxy_cache_valid 200 300s;
        proxy_ignore_headers Cache-Control;
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

後端 Node.js（跑在 `3000` 埠）有兩支路由：第一支是 `GET /portal`，它會讀取 `req.headers['x-forwarded-host']` 來拼湊 `<script src="//<x-forwarded-host>/app.js"></script>` 並回傳 `200 OK`；第二支是 `GET /api/v1/profile/*`，因為用了寬鬆的前綴路由（或經過點段正規化後落到 `/api/v1/profile`），收到請求時會驗證 `Authorization` 標頭並回傳該名商戶的機密 JSON 個資。

- **任務 2A（Cache Poisoning）**：用 `curl` 掛上 Cache Buster `?cb=991` 測試 `X-Forwarded-Host` 是否為未鍵入且會被反射的標頭；確認無誤後，對公開路徑 `/portal` 下手投毒，再用一筆不帶任何特殊標頭的普通請求驗證 `X-Cache-Status: HIT` 且回應裡已被植入惡意腳本網址。
- **任務 2B（Cache Deception）**：構造一條能同時觸發 Nginx `location ~* \.(css|js)$` 快取規則與後端 `/api/v1/profile` 個資回應的網址；先帶著 `Authorization: Bearer secret-token` 模擬受害者請求一次，接著不帶任何憑證發送匿名請求，驗證能否直接從 Nginx 快取裡偷出剛剛那包個資，最後寫出修補後的 Nginx 設定。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地實驗過關後，推薦到 **PortSwigger Web Security Academy** 挑下面三個主題（Practitioner / Expert 等級）驗收手感：

- **SSRF**：挑戰 *SSRF with blacklist-based input filter* 與 *SSRF with filter bypass via open redirection vulnerability*。卡關時先試試 `127.1`、`0177.0.0.1`、`[::]` 等替代寫法，並仔細分辨報錯訊息是「網址格式解析失敗」還是「命中黑名單被擋」；如果主端點鎖死白名單網域，就去找找站內有沒有開放重導向（Open Redirect）端點能當跳板。
- **Web cache poisoning**：挑戰 *Web cache poisoning with an unkeyed header* 與 *Web cache poisoning via an unkeyed query parameter* / *Parameter cloaking*。記住鐵則：在爆破標頭前一定要先掛上 `?cb=1234` Cache Buster，等親眼看到 `X-Cache: miss` 轉 `hit` 且輸入被反射出來，才拔掉 Cache Buster 看準 `Age` 時間窗一擊投毒。
- **Web cache deception**：挑戰 *Exploiting path mapping for web cache deception*、*Exploiting path delimiters for web cache deception* 與 *Exploiting origin server normalization for web cache deception*。測試訣竅是先在敏感路徑後面加上不存在的 `.css`、分號 `;a.js` 或編碼斜線 `..%2f`，只要同時滿足「源站依然回傳 `200 OK` 原頁面」與「快取層出現 `X-Cache: miss -> hit`」，就抓到能偷資料的邊界落差了。

---

### 參考解答

#### 任務 1A：構造繞過檢查的雙面 URL

```text
方案一（利用 url.parse() 不正規化八進位/DWORD IPv4 且跳過純數字主機查找，而 WHATWG fetch() 自動正規化）：
http://0177.0.0.1:9000/internal/metrics   （或 http://2130706433:9000/internal/metrics）

方案二（利用 IPv4-mapped IPv6 繞過只檢查 '127.' 與 '10.' 的字首黑名單）：
http://[::ffff:127.0.0.1]:9000/internal/metrics

補充對照（若前置檢查器是只按 RFC 3986 分隔符切分的寬鬆正則／跨語言解析器，而後端為 WHATWG fetch()）：
http://127.0.0.1:9000\@allowed.merchant.example/internal/metrics
```

來看看這三種方案為什麼能穿過 `validator.js`：
- **方案一**：`url.parse()` 把 `parsed.hostname` 原樣留成字串 `'0177.0.0.1'` 或 `'2130706433'`。它們開頭都不是 `'127.'`，而且因為整串只由數字跟點號組成，完全符合 `/^[0-9.]+$/`，於是程式誤以為這是已經檢查過的普通 IPv4，連 `dns.lookup()` 都跳過就直接放行！結果一進到 `sendWebhook()` 的 `fetch()`（遵循 WHATWG 標準），解析器自動把八進位 `0177.0.0.1` 或十進位整數 `2130706433` 換算成標準的 `127.0.0.1:9000`，精準把 POST 請求打進本機內部端點。
- **方案二**：`url.parse()` 拆出來的主機是 `'::ffff:127.0.0.1'`，`dns.lookup()` 回傳的 IPv4 映射位址字首也不是 `'127.'` 或 `'10.'`，輕鬆通過檢查並連進本機 `9000` 埠（同理，因為 `fetch()` 預設會自動跟隨 `3xx` 重導向，只要餵一個會回傳 `302 Location: http://127.0.0.1:9000/internal/metrics` 的外部可控網址，一樣能長驅直入）。
- **補充對照**：展示了跨元件對 `@` 與反斜線 `\` 的切分落差。只按 RFC 3986 分隔符切欄位的寬鬆解析器會把 `127.0.0.1:9000\` 當成 `userinfo`、把 `allowed.merchant.example` 當成 `hostname` 放行；等到進了 `fetch()`（WHATWG），特殊協定裡的 `\` 被自動轉成 `/`，主機瞬間變成 `127.0.0.1:9000`，後面的 `/@allowed.merchant.example/internal/metrics` 則變成請求路徑（適用於後端路由忽略前置路徑段或以萬用字元匹配的場景）。

#### 任務 1B：統一解析器、CIDR 攔截與連線層 IP Pinning 實作

```javascript
// safe-webhook.js
const dns = require('dns').promises;
const net = require('net');
const http = require('http');
const https = require('https');

// 用標準二進位 CIDR BlockList 把所有私有、本機與保留網段一次鎖死
const BLOCKED_CIDRS = new net.BlockList();
for (const [netAddr, prefix] of [
  ['0.0.0.0', 8],       // 本網路
  ['10.0.0.0', 8],      // RFC 1918 私有網段
  ['100.64.0.0', 10],   // Carrier-Grade NAT
  ['127.0.0.0', 8],     // Loopback 回環網段
  ['169.254.0.0', 16],  // Link-Local / 雲端 IMDS
  ['172.16.0.0', 12],   // RFC 1918 私有網段
  ['192.0.0.0', 24],    // IETF Protocol Assignments
  ['192.0.2.0', 24],    // TEST-NET-1
  ['192.168.0.0', 16],  // RFC 1918 私有網段
  ['198.18.0.0', 15],   // Benchmarking
  ['198.51.100.0', 24], // TEST-NET-2
  ['203.0.113.0', 24],  // TEST-NET-3
  ['224.0.0.0', 4],     // Multicast
  ['240.0.0.0', 4],     // Reserved
]) {
  BLOCKED_CIDRS.addSubnet(netAddr, prefix, 'ipv4');
}
for (const [netAddr, prefix] of [
  ['::', 128],          // Unspecified 未指定位址
  ['::1', 128],         // Loopback (含展開形式 0:0:0:0:0:0:0:1)
  ['fc00::', 7],        // Unique Local Address (fc00::/7，含 fc 與 fd)
  ['fe80::', 10],       // Link-Local (fe80:: ~ febf::)
  ['ff00::', 8],        // Multicast
]) {
  BLOCKED_CIDRS.addSubnet(netAddr, prefix, 'ipv6');
}

function isPrivateOrReservedIp(ip) {
  const norm = ip.toLowerCase();
  // 先拆解 IPv4-mapped IPv6（如 ::ffff:127.0.0.1 或 WHATWG 正規化後的 ::ffff:7f00:1）
  if (norm.startsWith('::ffff:')) {
    const tail = norm.slice(7);
    if (net.isIPv4(tail)) return BLOCKED_CIDRS.check(tail, 'ipv4');
    const hexMatch = tail.match(/^([0-9a-f]{1,4}):([0-9a-f]{1,4})$/);
    if (hexMatch) {
      const hi = parseInt(hexMatch[1], 16);
      const lo = parseInt(hexMatch[2], 16);
      const v4 = `${(hi >> 8) & 255}.${hi & 255}.${(lo >> 8) & 255}.${lo & 255}`;
      return BLOCKED_CIDRS.check(v4, 'ipv4');
    }
  }
  if (net.isIPv4(norm)) return BLOCKED_CIDRS.check(norm, 'ipv4');
  if (net.isIPv6(norm)) return BLOCKED_CIDRS.check(norm, 'ipv6');
  return true; // 任何無法識別的格式一律視為危險（Fail-Closed）
}

async function safeFetchWebhook(rawUrl) {
  const parsed = new URL(rawUrl); // 驗證與發送統一採用 WHATWG new URL()
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('Blocked protocol');
  }

  // 剝掉 IPv6 字面值外圍的方括號；若本身不是 IP 字面值，就查出該網域所有的候選位址並逐一檢查
  const cleanHost = parsed.hostname.replace(/^\[|\]$/g, '');
  const literalFamily = net.isIP(cleanHost);
  const records = literalFamily
    ? [{ address: cleanHost, family: literalFamily }]
    : await dns.lookup(cleanHost, { all: true });
  if (!records.length || records.some((r) => isPrivateOrReservedIp(r.address))) {
    throw new Error('Blocked private or reserved IP');
  }
  const pinned = records[0];

  // 在底層連線的 lookup 回呼裡直接釘選剛剛驗證過的 IP，徹底消滅 DNS Rebinding 時間窗，並拒絕所有 3xx 重導向
  const transport = parsed.protocol === 'https:' ? https : http;
  return new Promise((resolve, reject) => {
    const req = transport.request(
      parsed,
      {
        method: 'POST',
        agent: false,
        lookup: (_host, opts, cb) =>
          opts && opts.all
            ? cb(null, [{ address: pinned.address, family: pinned.family }])
            : cb(null, pinned.address, pinned.family),
        headers: { 'Content-Type': 'application/json' },
      },
      (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400) {
          res.resume();
          return reject(new Error('Redirects are disabled'));
        }
        resolve(res.statusCode);
      }
    );
    req.on('error', reject);
    req.write(JSON.stringify({ event: 'settled' }));
    req.end();
  });
}
```

#### 任務 2A 與 2B：快取投毒、快取欺騙驗證指令與 Nginx 修補設定

```bash
# 2A-1. 掛上 Cache Buster (?cb=991) 探測 X-Forwarded-Host 是否會被源站反射
curl -i -s "http://127.0.0.1:8080/portal?cb=991" -H "X-Forwarded-Host: evil.example" | grep -E "X-Cache-Status|evil.example"

# 2A-2. 確認反射且 X-Cache-Status: MISS 後，拔掉 cb 直接對公開快取鍵 /portal 投毒
curl -i -s "http://127.0.0.1:8080/portal" -H "X-Forwarded-Host: evil.example"

# 2A-3. 模擬正常使用者發送不帶特殊標頭的請求，看到 X-Cache-Status: HIT 且畫面載入 evil.example 的腳本
curl -i -s "http://127.0.0.1:8080/portal"

# 2B-1. 模擬受害者帶著憑證訪問偽裝成 .css 的個資路徑（因 Nginx 忽略 Cache-Control 且強制快取 200 回應 300 秒，個資被寫入共享快取）
curl -i -s "http://127.0.0.1:8080/api/v1/profile/leak.css" -H "Authorization: Bearer secret-token"

# 2B-2. 攻擊者不帶任何憑證直接請求同一條網址，拿到 X-Cache-Status: HIT 並讀出受害者的機密 JSON
curl -i -s "http://127.0.0.1:8080/api/v1/profile/leak.css"
```

修補後的 Nginx 組態要把外部傳來的覆寫型標頭洗乾淨、拔掉看副檔名就硬快取的危險規則，並確保動態 API 一律關閉共享快取：

```nginx
# 修補版 Nginx 設定
server {
    listen 8080;

    # 清空外部傳入的未鍵入覆寫標頭，不讓它們污染源站回應
    proxy_set_header X-Forwarded-Host "";
    proxy_set_header X-Original-URL "";
    proxy_set_header X-Rewrite-URL "";

    location / {
        proxy_pass http://127.0.0.1:3000;
        # 動態路由預設關閉共享代理快取
        proxy_no_cache 1;
        proxy_cache_bypass 1;
    }

    # 只針對明確的靜態資產目錄前綴開啟快取，且完全尊重源站的 Cache-Control 與 Set-Cookie
    location ^~ /static/assets/ {
        proxy_pass http://127.0.0.1:3000;
        proxy_cache nexus_cache;
        proxy_cache_key "$scheme$request_method$host$request_uri";
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先合上前面的範例，試著用自己的話回答這四個實戰架構審查問題：

1. 某支付系統的前置 WAF 用簡易正規表達式檢查網址主機不含 `127.0.0.1` 或 `localhost`，後端微服務則用 Node.js 的 `fetch()` 發送請求。請說明為什麼攻擊者傳入 `http://0x7f.0.0.1:8080/admin`、`http://12\t7.0.0.1:8080/admin` 或 `http://127.0.0.1:8080\@partner.example/` 時，前置檢查會放行，後端卻會直接打進本機？
2. 團隊把網址解析統一換成 `new URL()`，也在發請求前先呼叫 `dns.lookup()` 確認 IP 不屬於私有網段，但沒做連線層的 IP Pinning。請問這段空檔為什麼還會被 DNS Rebinding 攻破？就算公司的容器 DNS 解析器強制把所有紀錄至少快取 `5` 秒（忽略 `TTL=0`），攻擊者還是有哪兩種方法能穿過去？
3. 在做 Web Cache Poisoning 測試時，為什麼老手一定會先在網址後面加上 `?cb=<隨機數>` 當作 Cache Buster？如果某個 CDN 為了拉高命中率，設定把 `utm_content` 從快取鍵中剔除（只認 `&` 分隔參數），而後端框架卻同時把 `;` 當成參數分隔符，攻擊者該如何發動 **Parameter Cloaking** 投毒？
4. 某團隊為了保護動態個資，把 Nginx 的靜態副檔名快取規則拔掉，改用 CDN 的前綴規則「只快取 `/static/` 開頭的路徑」。為什麼攻擊者構造 `GET /static/..%2f..%2fv1/merchant/profile` 騙已登入的受害者點開，還是能發動 Web Cache Deception 偷走個資？這跟 Cache Poisoning 在攻擊方向與根源上有什麼本質不同？

---

### 參考解答

1. **解析器對十六進位 IPv4、控制字元與反斜線 `\` 的認知差異**：
   - 面對 `http://0x7f.0.0.1:8080/admin` 與 `http://12\t7.0.0.1:8080/admin` 時，只比對字面字串 `"127.0.0.1"` 的前置 WAF 認不出十六進位 `0x7f`（等於 `127`）或夾了 Tab（`\t`）的主機字串而直接放行；但後端的 `fetch()` 遵循 WHATWG URL Standard，會先自動剝除 `\t`、`\n`、`\r` 控制字元，並將十六進位／八進位／DWORD 整數 IPv4 統一換算成標準點分十進位的 `'127.0.0.1'` 打進本機。
   - 面對 `http://127.0.0.1:8080\@partner.example/` 時，只認 `/`、`?`、`#` 分隔符而沒擋掉反斜線的寬鬆解析器，會把 `@` 前面的 `127.0.0.1:8080\` 當成帳號密碼（userinfo）、把 `partner.example` 當成主機名稱放行；但 `fetch()`（WHATWG）一看到特殊協定裡的 `\` 就會自動把它轉成 `/`，認定主機欄位到此結束，於是真正連出去的主機就變成了 `127.0.0.1:8080`，後面的 `/@partner.example/` 則全退化成普通路徑。
2. **缺少 IP Pinning 的 TOCTOU 與 `5` 秒快取突破法**：
   - `dns.lookup()` 檢查完之後，如果把原始網域名稱交給 `fetch()`，在 `fetch()` 實際建立新 TCP 連線且未命中本地快取時，底層會再發起第二次 DNS 查詢。只要攻擊者的權威 DNS 在第二次查詢時改回傳 `127.0.0.1`，連線就會直接打向本機。
   - 就算解析器強制快取 `5` 秒，攻擊者還是能用兩招破解：第一招是**單次回傳多筆 A 記錄**（第一筆放合法的公網 IP 騙過只看 `records[0]` 的檢查器，第二筆塞 `127.0.0.1`，並故意關掉公網 IP 的連接埠，逼 HTTP 客戶端在第一筆連線失敗或輪詢時自動 fallback 連向第二筆 `127.0.0.1`）；第二招是**利用非同步佇列延遲**（只要「檢查網址」跟「背景排程真正發送或重試請求」中間隔了超過 `5` 秒，等本地快取一過期且發送端未重用舊連線而重新查 DNS 時，就會從權威 DNS 拿到切換後的 `127.0.0.1`）。
3. **Cache Buster 的作用與 Parameter Cloaking 投毒法**：
   - 在查詢字串有被納入有效快取鍵的前提下，掛上隨機的 Cache Buster 能把測試請求隔離到獨立的快取鍵：一來**避免在測試階段誤把半成品 payload 寫進正式首頁污染真實用戶**，二來**避免因為正式路徑剛好已被他人快取（`HIT`）而沒打到源站，誤判為漏洞不存在**。
   - 針對 `utm_content` 的 **Parameter Cloaking**：攻擊者送出 `GET /api/config?utm_content=1;callback=evil()`。只認 `&` 的 CDN 以為整串都是 `utm_content` 的值，在算快取鍵時把它整段抹除，快取鍵變成乾淨的 `/api/config`；但認得 `;` 的後端卻從分號後面切出了 `callback=evil()` 並吐回惡意 JSONP 回應，直接寫入 `/api/config` 的公開快取。
4. **`..%2f` 點段正規化差異與兩類快取漏洞的本質不同**：
   - **為什麼 `/static/..%2f..%2fv1/merchant/profile` 會中招**：未先解碼 `%2f` 的 CDN 前綴匹配器只看到字串以 `/static/` 開頭，不把 `..%2f` 當成 `/../` 目錄點段，當場命中靜態快取規則；但後端源站先把 `%2f` 解碼回 `/` 再折疊兩個 `../` 點段，實際執行 `/v1/merchant/profile` 並吐回受害者個資，結果被 CDN 存進該公開快取鍵供攻擊者匿名領走。
   - **與 Cache Poisoning 的本質差異**：Poisoning 是「**由外寫入**」，根源在於**快取鍵（與 `Vary`）漏掉了會影響源站輸出的輸入欄位（Unkeyed Input）**；Deception 則是「**由內竊取**」，根源在於**快取層與源站對路徑／副檔名與點段正規化的解析不一致**，且快取層無視源站的 `Cache-Control` 保護硬把私有動態回應存進了共享快取。

---

## 延伸閱讀

1. Orange Tsai, *A New Era of SSRF — Exploiting URL Parser in Trending Programming Languages!*（Black Hat USA 2017）：系統性拆解 `curl`、Node.js、Python、Go、PHP 等主流語言 URL 解析器分歧的經典必讀研究。
2. WHATWG URL Living Standard（https://url.spec.whatwg.org/）與 IETF RFC 3986（*Uniform Resource Identifier (URI): Generic Syntax*）：直接對照兩套標準在特殊協定、反斜線正規化與控制字元剝除上的規則差異。
3. James Kettle, *Practical Web Cache Poisoning*（PortSwigger Research / Black Hat USA 2018）與 *Web Cache Entanglement*（2020）：完整建立 Unkeyed Input、Fat GET 與 Parameter Cloaking 的實戰挖掘方法論。
4. PortSwigger Research, *Gotta cache 'em all: bending the rules of web cache exploitation*（2024）：深入剖析各大現代 CDN 與源站之間在路徑分隔符（Path Delimiters）與點段正規化（Normalization）上的最新 Cache Deception 破口。
