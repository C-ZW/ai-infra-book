# 第 14 章 防禦對抗與繞過技術（WAF、代理正規化與 Rate Limit 破口）

系統上線前，團隊通常會在 API 閘道前方掛上 WAF（如 Nginx 搭配 ModSecurity 與 OWASP Core Rule Set），再替登入、OTP 驗證與轉帳端點加上 Redis 滑動視窗限流器（Rate Limiter）。直覺上，這兩道防線能把明顯的 SQL 注入、XSS 和暴力破解擋在門外，讓後端 Express 或 NestJS 服務專心處理乾淨的請求。

但邊界防護元件本身也是解析器。承接第 3 章的 HTTP 請求解析分歧與第 11 章的快取正規化落差，本章直接拆解 WAF 與限流器的設定邊界，看看攻擊者怎麼利用「**邊緣元件看到的請求**」跟「**後端實際執行的請求**」之間的認知落差長驅直入，以及我們該怎麼從應用程式層把根因徹底封死。

---

## 從你已知的出發

為什麼 WAF 明明開啟了攔截 `SELECT` 與 `__proto__` 的規則，Redis 限流器也設了每分鐘最多 `5` 次嘗試，攻擊者卻還是能把一模一樣的 SQL 注入 payload 送進後端，甚至在幾秒內暴力測完上千組 OTP？

因為邊緣元件為了扛住高吞吐量並避免誤殺正常流量，在解析請求時做了許多妥協。舉例來說，不少 WAF 預設只檢查請求主體的前 `8,192 bytes`（`8 KiB`），超過的部分直接放行；但後端 Express `body-parser` 預設卻能吃下 `102,400 bytes`（`100 KiB`）。

攻擊者只要在 JSON 前面塞滿 `8,200` 個無害的 `'A'` 字元，把惡意欄位擠到第 `8,193` 個位元組之後，WAF 看完前段覺得一切正常就蓋章放行，後端卻把整包 JSON 照單全收。同樣地，只要前後端對 Unicode 跳脫、重複參數、路徑大小寫或 `X-Forwarded-For` 標頭的解讀不一致，外層防護就會瞬間失守。

---

## 機制與推導

### 攻擊者目標與實質影響

攻擊者研究 WAF、代理正規化與限流器，目的不是為了炫技，而是要把前面幾章的攻擊手法送進受保護的生產環境。

最直接的目標是穿透「虛擬修補」（Virtual Patching）。很多團隊發現後端有 SQL 注入（第 8 章）、XXE（第 9 章）、SSRF（第 11 章）或原型污染（第 13 章）時，會先在 WAF 加一條關鍵字攔截規則爭取改 code 的時間。一旦攻擊者找到主體截斷、編碼差異或參數污染破口，原本被擋下的 payload 就能原封不動直達後端 Sink。

另一個重災區是瓦解身分認證與業務防爆破防線。只要繞過 IP 或端點級的 Rate Limiter，攻擊者就能對 NexusPay 商戶登入、6 位數 OTP 驗證（`10^6` 種組合）、密碼重設碼或優惠券兌換端點發動高併發暴力破解與憑證填充（Credential Stuffing），直接接管商戶帳號並盜領資金。

此外，攻擊者也會利用路徑正規化差異（像大小寫、尾斜線、矩陣參數 `;`）去探測隱藏的管理介面，讓原本應該被反向代理 ACL 擋在門外的 `/internal/` 或 `/admin/` 請求，一路穿透到後端路由器。

---

### 1. WAF 的先天限制：為什麼正規表達式贏不了後端解析器

商業雲端 WAF 與開源 ModSecurity（搭配 OWASP CRS）之所以容易在邊界被繞過，不是因為規則寫得不夠多，而是受限於三個先天的架構包袱：

第一是**延遲與 CPU 預算**。在 NexusPay 尖峰 `2,000 req/s` 的流量下，WAF 必須在幾毫秒內決定放行或阻斷，無法對每筆請求啟動完整的 SQL AST、JS 或 XML DOM 解析器。因此 WAF 只能依賴正規表達式與啟發式計分（Inbound Anomaly Score），並限制回溯深度與掃描長度，以免發生指數回溯卡死（ReDoS，見第 13 章）。

第二是**缺乏後端執行時期的上下文**。WAF 不知道後端 Node.js 路由表怎麼切參數，不知道 MySQL 與 PostgreSQL 對空白字元或註解的方言差異，更不知道 Express `body-parser` 到底支援哪些 `Content-Type` 與字元集。

第三是**為了可用性而做的預設放行**（Fail-Open / Partial Inspection）。為了怕大型檔案上傳或複雜 JSON 報表被誤殺，許多 WAF 在請求主體超過檢查上限時，不會直接回傳 `413 Payload Too Large`，而是常被設成「只檢查前段視窗、放行完整請求」（例如 ModSecurity 的 `SecRequestBodyLimitAction ProcessPartial`）。

把一筆請求從邊緣 WAF 走進後端 Express 的過程攤開來看，最常發生解析錯位的就是下面四個節點：

```text
客戶端請求
  │
  ├─[節點 A: 請求主體截斷]──▶ WAF 僅檢查前 8,192 bytes (ProcessPartial)
  │                              後段 > 8 KiB 的惡意 JSON 欄位直接放行
  │
  ├─[節點 B: 編碼與字元集]──▶ WAF 以 UTF-8 掃描 \u005f\u005fproto\u005f\u005f
  │                              Express body-parser 自動解碼為 __proto__
  │
  ├─[節點 C: 參數與路徑]────▶ WAF 檢查第一個 ?id=1 或比對精確路徑 /v1/Admin
  │                              Express 收到陣列 ["1", "union..."] 或不分大小寫匹配
  │
  └─[節點 D: 來源 IP 信任]──▶ Nginx / Express trust proxy 誤信偽造的 X-Forwarded-For
                                 Redis 滑動視窗針對假 IP 計數，限流器形同失效
```

---

### 2. 請求主體檢查上限與截斷繞過（Oversized Body）

在實戰中，這是命中率最高、也最穩定的 WAF 繞過手法。它完全不需要花俏的 SQL 變形語法，單純就是打「檢查長度上限」的數字差。

在生產環境裡，不少雲端 WAF（如早期或預設配置的 AWS WAF 經典檢查上限 `8,192 bytes`，即 `8 KiB`；部分代理方案預設也只看前 `8 KiB` 到 `128 KiB`）與自建的 ModSecurity（設定 `SecRequestBodyLimitAction ProcessPartial` 搭配較小的 `SecRequestBodyNoFilesLimit` 時），遇到超長請求都不會直接擋掉。它們只拿緩衝區的前 `N` 個位元組跑規則比對，剩下的位元組直接原封不動轉給後端。

但後端框架能吞下的資料量通常大得多。以 Node.js Express 為例，`express.json()`（底層是 `body-parser`）預設的 `limit` 是 `100kb`，換算成精確位元組數是 **`100 × 1024 = 102,400 bytes`**。

`8,192 bytes` 跟 `102,400 bytes` 之間，整整差了 **`94,208 bytes`** 的三不管地帶。只要 WAF 開了部分檢查（`ProcessPartial`），而且沒有強制檢查前段被切斷的文字必須是合法閉合的 JSON（或沒有阻斷 `REQBODY_ERROR`），這段落差就能直接穿過。

攻擊者只要在 JSON 最前面塞一個無害的長字串欄位當墊背（Padding Field），把真正的攻擊 payload 往後推到第 `8,193` 個位元組之後，WAF 看完前 `8 KiB` 只見滿滿的 `'A'` 就放行了，後端 Express `body-parser` 卻會把整包請求收進來完整解析。

#### Worked Example：計算跨過 WAF `8,192 bytes` 檢查上限的 JSON Padding Payload

假設 NexusPay 前方的 WAF 請求主體檢查上限是 `8,192 bytes`（開啟 `ProcessPartial` 且只對前段視窗掃描攻擊特徵），後端 Express API 閘道則使用預設的 `express.json()`（上限 `100 KiB = 102,400 bytes`）。

攻擊者想打 `/v1/merchant/preferences`，送出帶有原型污染與 SQL 注入的排序設定 `{"__proto__":{"isAdmin":true},"sort":"id; SELECT pg_sleep(5)--"}`。直接送會被 WAF 攔下，我們實際算一遍要塞多少填充位元組才能穿過去：

```text
[1] 目標惡意後段（必須完全落在 8,192 bytes 之後）：
    payload_tail = ',"__proto__":{"isAdmin":true},"sort":"id; SELECT pg_sleep(5)--"}'
    逐段計數：',' (1) + '"__proto__"' (11) + ':' (1) + '{"isAdmin":true}' (16)
            + ',' (1) + '"sort"' (6) + ':' (1) + '"id; SELECT pg_sleep(5)--"' (26) + '}' (1)
    len(payload_tail) = 64 bytes

[2] 計算前置 JSON 結構與填充長度：
    外層開頭與 padding 鍵名：
    prefix = '{"pad":"'          -> 8 bytes
    padding 字元（純 ASCII 'A'）：N bytes
    padding 字串結尾引號：'"'     -> 1 byte

    要讓 payload_tail 的第一個位元組（0-indexed）落在 offset >= 8,192，
    必須滿足：
      len(prefix) + N + 1 >= 8,192
      8 + N + 1 >= 8,192
      N >= 8,183 bytes

    保留 17 bytes 安全餘裕（取整數 N = 8,200，確保就算邊界按 1-indexed 算也不越線）：
      N = 8,200 bytes（8,200 個 'A'）

[3] 驗證各區段位元組偏移量（0-indexed）：
    Offset 0     .. 7     : '{"pad":"'                     (8 bytes)
    Offset 8     .. 8,207 : 'A' * 8200                     (8,200 bytes)
    Offset 8,208          : '"'                            (1 byte)
    --- WAF 8,192 bytes 檢查邊界在 Offset 8,191 結束 ---
    --- WAF 前段視窗只看到 '{"pad":"AAA...AAA'（無任何攻擊關鍵字特徵）---
    Offset 8,209 .. 8,272 : ',"__proto__":{"isAdmin":true},"sort":"id; SELECT pg_sleep(5)--"}' (64 bytes)

[4] 總請求主體長度檢核：
    Total Content-Length = 8 + 8,200 + 1 + 64 = 8,273 bytes
    對照邊界條件：
      8,273 bytes >  8,192 bytes  (超過 WAF 檢查上限，後段 81 bytes 未受檢)
      8,273 bytes <= 102,400 bytes (遠低於 Express body-parser 預設 100 KiB 上限)

[5] 後端 Express body-parser 實際解析結果：
    req.body.pad   = "AAAA...AAAA" (長度 8,200)
    req.body.sort  = "id; SELECT pg_sleep(5)--"
    req.body["__proto__"] = { isAdmin: true } (建立自有屬性，若後續流入 deepMerge 或未參數化 SQL Sink 就觸發漏洞)
```

除了塞長字串，另一種主體檢查盲點是利用 `Transfer-Encoding: chunked`（第 3 章談過如何用它走私請求，這裡看它對 WAF 掃描的影響）。有些輕量級代理在收齊完整請求前不會重組大塊 chunk。

一旦遇到合法但少見的 chunk extension（像 `5;ext=foo\r\nhello\r\n`），或是把資料切得極碎（每個 chunk 只有 1 到 2 個位元組，如 `1\r\nU\r\n1\r\nN\r\n...`），要是 WAF 逐塊獨立跑正規表達式，而不是重組完再掃描，敏感關鍵字被拆散後就會直接躲過檢查。

---

### 3. 參數污染（HPP）與編碼／字元集分歧

如果 WAF 把門檻鎖得很死，只要請求超過 `8 KiB` 就一律回 `413` 拒收，攻擊者就會改從**語法解析的差異**下手。

#### HTTP 參數污染（HTTP Parameter Pollution, HPP）

當網址或表單裡同一個參數名稱出現兩次以上（例如 `?merchant_id=101&merchant_id=102`），到底該聽哪一個的？HTTP 的 RFC 規範並沒有硬性規定。結果就是各家後端框架各自為政：

| 後端框架 / 取值介面（預設組態） | `?id=1&id=2` 的解析結果 | 與 WAF 常見落差 |
|---|---|---|
| **Node.js / Express**（預設 `qs` 解析器，`req.query.id`） | 陣列 `["1", "2"]` | WAF 只對單一字串跑正規表達式，遇到陣列型態或串接後的結果可能漏判，還會害後端發生型別混淆 |
| **PHP**（原生 `$_GET['id']` / `parse_str`） | 後面蓋掉前面，取最後一個值 `"2"` | 如果 WAF 只檢查第一個出現的 `"1"`，攻擊者把髒東西塞在第二個同名參數就過關了 |
| **Python Flask / Werkzeug**（`request.args.get("id")`） | `MultiDict.get()` 取第一個值 `"1"` | 如果 WAF 只檢查最後一個值，或對整條查詢字串的切法不同，就會出現反方向的漏判 |
| **ASP.NET / IIS**（`Request.QueryString["id"]`） | 用逗號拼成一個字串 `"1,2"` | 攻擊者可以把 SQL 拆成 `?q=SELECT/*&q=*/password FROM users`，兩段單獨看都像普通字串，後端一拼起來就變成完整的 SQL 注入 |

在 Express 裡，HPP 甚至不用搭配 SQL 注入就能搞垮業務邏輯。來看這段常見的權限過濾寫法：

```javascript
// 開發者以為 req.query.id 一定是字串
const id = req.query.id;
if (typeof id === 'string' && id.startsWith('admin_')) {
  return res.status(403).send('Forbidden');
}
const records = await db.find({ accountId: id });
```

開發者心裡想的是擋掉 `'admin_'` 開頭的字串。但攻擊者只要傳入 `?id=admin_1&id=user_2`，Express 的 `req.query.id` 就會變成陣列 `["admin_1", "user_2"]`。

這時 `typeof id === 'string'` 直接變成 `false`，輕鬆跳過前面的黑名單檢查；把陣列丟進某些 ORM 時還會被自動展開成 `WHERE account_id IN ('admin_1', 'user_2')`，當場把管理員的資料撈出來。

#### JSON Unicode 跳脫與重複鍵值（Duplicate Keys）

照 JSON 規範（RFC 8259），字串裡可以用 `\uXXXX` 表示 Unicode 字元。當後端 V8 引擎執行 `JSON.parse()` 時，會自動把 `"\u005f\u005fproto\u005f\u005f"` 或 `"\u0027 OR 1=1--"` 還原成 `"__proto__"` 與 `"' OR 1=1--"`。

要是前方的 WAF 只拿原始位元組當純文字掃描，沒有先把 JSON 的 Unicode 跳脫序列解開，看到 `\u0053ELECT` 或 `\u003cscript\u003e` 時根本認不出是 `SELECT` 和 `<script>`，自然不會觸發攔截。

同一個 JSON 物件裡如果出現兩個一模一樣的 key（例如 `{"role":"merchant","role":"admin"}`），也是經典破口。RFC 8259 並未強制禁止重複鍵名。如果 WAF 的簡易解析器看第一個鍵值 `role = "merchant"` 覺得沒問題就放行，但後端的 V8 `JSON.parse()` 照 ECMA-262 規範走「後寫覆蓋前寫」（Last-Write-Wins），後端最後拿到的就會是 `role: "admin"`。

#### Content-Type 與字元集（Charset）差異

許多後端解析器或自訂解碼中介層，會根據 `Content-Type` 標頭裡的 `charset` 參數（底層常呼叫 `iconv-lite` 或語言內建轉碼器），把收到的位元組流轉成字串。

現代標準的 Express `body-parser.json()` 已經強制檢查字元集必須是 `utf-` 開頭（看到 `ibm037` 會直接回 `415 Unsupported Media Type`）；但在支援 `utf-16be` / `utf-16le` 的管線，或允許 `ibm037`（EBCDIC）、`shift_jis` 的傳統 Java Servlet 與自建微服務閘道裡，這招依然管用。

只要前方的 WAF 只按 UTF-8 / ASCII 去掃描原始位元組，又沒有直接拒收非 UTF-8 的 `charset`，那些特殊編碼的位元組在 WAF 眼裡就像一團亂碼而不會命中關鍵字，等進到後端被解碼器轉回標準字串，惡意指令就瞬間復活了。

上傳檔案常用的 `multipart/form-data` 也有同樣毛病。要是 WAF 對 `boundary` 的格式要求很死板，而後端套件（如 `multer` 或 `busboy`）容錯度較高，攻擊者只要把標頭寫成 `multipart/form-data; boundary="----abc"; charset=utf-8`，或多塞幾個空白與換行，就可能讓 WAF 解析失敗跳過檢查，後端卻照常把欄位讀出來。

---

### 4. Rate Limit 與邊緣存取控制繞過

看完了 WAF，接著看另一道邊緣防線：用來防暴力破解的 Nginx `limit_req` 或 Express + Redis 滑動視窗限流器。這套機制在實務上最常栽在三個設定細節。

#### `X-Forwarded-For` 信任鏈錯位

在有反向代理的架構裡，請求通常走 `Client → CDN → Nginx → Express` 這條路。每一層代理都可能依設定去附加（append）、覆寫或拿掉 `X-Forwarded-For`（XFF）標頭。如果最外層代理沒有把外部傳進來的 XFF 洗掉重寫，而是直接把上一跳的來源 IP 往後接，送到應用程式手上的位址鏈就會混入攻擊者自己捏造的假 IP：

```text
真實來源 IP: 203.0.113.50
攻擊者偽造標頭: X-Forwarded-For: 1.2.3.4

經過 1 層 Nginx 附加後，Express 收到的標頭為：
  X-Forwarded-For: 1.2.3.4, 203.0.113.50
```

面對這串標頭，後端最常犯兩種致命錯誤：

第一種是**自己切字串並盲信最左邊的 IP**。許多開發者寫 Express 中介層時，順手寫出 `req.headers['x-forwarded-for'].split(',')[0].trim()`，再拿這個 IP 去組 Redis 限流鍵 `rl:ip:${ip}`。攻擊者只要在發請求時每次隨機換一個 `X-Forwarded-For: 10.0.${a}.${b}`，每次進來都會開一個全新的 Redis 計數器，限流器當場報廢。

第二種是**在 Express 設定 `app.set('trust proxy', true)` 過度信任**。在 Express 裡把 `trust proxy` 設成布林值 `true`，代表告訴框架「整條 XFF 鏈上的每一跳我都信」，Express 就會直接拿鏈上**最左邊（第一個）位址**當作 `req.ip`。只要最外層代理是用附加（append）而不是覆寫，設成 `true` 就等於完全相信攻擊者自己填的第一個 IP。

正確做法是精確指定前面有幾層受你控制的代理（例如前面只有 1 層 Nginx 就設整數 `app.set('trust proxy', 1)`，或是明確列出受信任代理的 CIDR 網段），讓解析器**從最右邊往左數第 `N` 跳**，抓出真正連進邊緣閘道的那個客戶端 IP。

#### IPv6 `/64` 子網輪換

就算你把 `X-Forwarded-For` 鎖死了，每次都乖乖抓真實的 TCP 來源 IP，只要你的服務支援 IPv6，而且限流器是拿「完整的單一 IPv6 位址（`/128`）」當作 Redis 鍵值，防線還是會被穿破。

原因在於，一個標準的 IPv6 `/64` 子網前綴，底下就包含了 **`2^64`（約 `1.84 × 10^19`）個不同的 `/128` 位址**。現在許多雲端主機商租一台 VPS 就會直接配給你整段可路由的 `/64` 前綴。

攻擊者只要在 Linux 主機上下一行 `ip -6 route add local <prefix>::/64 dev lo` 並搭配 `IP_FREEBIND`，就能在同一台機器上，每次發送 OTP 驗證請求時隨機換掉後面的 64-bit Interface Identifier（從 `2001:db8:abcd:1234::1` 一路換到 `2001:db8:abcd:1234::ffff`）。對限流器來說，每一發請求都是「全新的 `/128` IP」，單一 IP 的計數器永遠停在 `1`，根本碰不到限流門檻。

#### 端點大小寫、尾斜線與路徑正規化差異

如果限流器或存取控制清單（ACL）是靠比對網址字串來決定要不要限流，它跟後端框架路由器（Router）之間的行為差異，就會立刻露出破口。

先看**大小寫差異**。Express 預設的 `case sensitive routing` 是 `false`。所以在 Express 眼裡，`/v1/auth/otp/verify`、`/v1/auth/OTP/Verify` 跟 `/v1/Auth/otp/verify` 全都是同一個端點，會交給同一個 Handler 處理。但如果前面的限流器或 Nginx `location = /v1/auth/otp/verify` 是區分大小寫的精確比對，攻擊者只要把路徑裡的英文字母隨便改幾個大寫（共有 `2^k` 種排列組合），就能繞過針對該端點設下的嚴格限流。

再看**尾斜線與多餘路徑段**。Express 預設的 `strict routing` 也是 `false`，所以 `/v1/auth/otp/verify/` 跟 `/v1/auth/otp/verify` 完全互通。此外，當 Nginx、Envoy 或 Spring 等元件遇到 `/v1/auth/otp/verify/.`、`/v1/auth/otp//verify` 或帶了矩陣參數的 `/v1/auth/otp/verify;foo=bar` 時，前面的限流器往往認不得這條路，只好套用最寬鬆的全站預設規則；結果進到後端路由器被正規化之後，照樣執行敏感的 OTP 驗證。

至於 GraphQL 端點，攻擊者還能把上百次查詢塞進同一個 HTTP 請求的 Alias Batching 裡，直接把「按 HTTP 請求次數計費」的限流器廢掉（見第 7 章）。

---

## 故障模式與防禦

看懂這些繞過手法後，千萬別掉進「被繞過一次、就去 WAF 多加一條正規表達式」的無底洞。那樣做只會讓規則庫越來越肥、延遲越來越高，而且永遠追不上攻擊者換編碼的速度。真正能一勞永逸的做法，是把「邊緣與後端的設定對齊」，並直接在應用程式層把漏洞根因拔掉。

### 1. 消除主體檢查落差：對齊長度上限並關掉部分放行

首先，絕對不要讓「WAF 只看前 `8 KiB`、後端卻收 `100 KiB`」這種設定上線。在 ModSecurity 裡，請把 `SecRequestBodyLimitAction` 明確設成 `Reject`（只要超長就直接回 `413` 擋掉，絕不靜默放行），並確保 WAF 的完整檢查上限**大於或等於**後端框架的接收上限。

舉例來說，如果後端 Express API 平常只收小型 JSON 指令，那就直接把 `express.json({ limit: '8kb' })` 往下調，讓它跟 WAF 的檢查視窗完全對齊；如果業務真的需要傳 `100 KiB` 的 JSON，那就把 WAF 的檢查視窗調大到能完整覆蓋 `100 KiB`。

同時，在 API 閘道與 Express 中介層把 `Content-Type` 鎖死：只准許業務真的有用到的 `application/json` 等白名單格式，而且只要標頭裡有帶 `charset`，就只准是 `utf-8`，看到 `utf-16` 或 `ibm037` 一律當場回 `415` 拒收。

### 2. 在應用程式層用嚴格 Schema 封死 HPP 與重複鍵值

別指望 WAF 幫你檢查參數型別。在資料剛進到 Express 或 NestJS 的邊界時，就應該用 `Zod`、`Ajv` 或 `class-validator` 把型別鎖死：

如果 `req.query.id` 預期是個單一字串或 UUID，Schema 驗證器就必須強制要求 `typeof val === 'string'`。只要有人用 HPP 送進 `?id=1&id=2` 變成了陣列，第一時間就回 `400 Bad Request` 踢掉，絕不允許程式自動轉成字串或偷偷取第一個值。

針對 JSON 主體，可以在進業務邏輯前先掃描原始字串擋掉重複的 key；更重要的是在業務層全面落實參數化查詢（第 8 章）、用 `Object.create(null)` 或明確的欄位白名單（第 6、13 章）。只要後端沒有危險的 Sink，就算攻擊者的 payload 真的穿過了 WAF，打進來也只是一串普通文字，完全起不了作用。

### 3. 修復 Rate Limiter 的信任鏈與計數鍵值

要讓 Redis 滑動視窗限流器真正守住大門，我們必須把 IP 抓取、IPv6 子網、路由路徑跟業務帳號這四個維度一次補齊：

第一，**精確設定代理跳數**。在最外層受控的 Nginx 或 CDN 上直接覆寫（而不是附加）客戶端 IP 標頭；在 Express 裡則照實際的反向代理層數設定整數（例如前面有 1 層 Nginx 就設 `app.set('trust proxy', 1)`），嚴禁偷懶設成 `true`。

第二，**把 IPv6 位址收斂到子網前綴**。在計算限流鍵之前，只要發現來源 IP 是 IPv6，一律先把它截斷並正規化成 `/64`（高風險端點甚至可以縮到 `/56`）網路前綴。這樣不管攻擊者手上的 `/64` 子網怎麼輪換後面的 `2^64` 個位址，在 Redis 裡都會撞上同一個計數器。

第三，**讓限流鍵跟後端路由器的匹配結果對齊**。最穩的做法是直接把限流中介層掛在目標路由處理器上（像 `app.post('/v1/auth/otp/verify', otpLimiter, handler)`），或是直接拿路由器已經匹配好的路徑識別值（如 Express 的 `req.route.path`）來組 key，確保不管網址大小寫或尾斜線怎麼變，只要能打中這支 API，就一定共用同一個計數桶。

第四，**綁定業務帳號維度**。永遠記住：IP 只是輔助（公司行號共用 NAT 很容易誤殺無辜，攻擊者租用分散式代理池也很容易換 IP）。凡是登入、OTP 驗證、重設密碼或提領這類敏感操作，**都必須同時針對 `account_id`、`email` 或 `merchant_id` 建立獨立的 Redis 失敗計數器與指數退避鎖定**，直接從業務狀態機把暴力破解的路封死。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

現在我們在本地把 NexusPay 的邊緣防護環境（Nginx + ModSecurity OWASP CRS + Express API Gateway + Redis 7）跑起來。你會親手用超長 JSON 跟假標頭穿過這道防線，接著再修改設定與程式碼把它徹底修好。

### 實驗步驟

1. **啟動本地靶機環境**：
   這組容器包含了 `waf-nginx`（故意設成 `SecRequestBodyNoFilesLimit 8192` 與 `SecRequestBodyLimitAction ProcessPartial`）、`nexuspay-api`（使用 Express 預設 `100 KiB` 上限與錯誤的 `app.set('trust proxy', true)`）以及 `redis`：
   ```bash
   docker compose -f labs/ch14-waf-bypass/docker-compose.yml up -d
   ```

2. **任務一：實測 `8,192 bytes` 主體截斷與 Unicode 跳脫繞過**
   - 先送一筆短請求 `POST http://localhost:8080/v1/merchant/preferences`，內容填 `{"sort":"id; SELECT 1--"}`，確認會被 Nginx 上的 ModSecurity 攔下來並回傳 `403 Forbidden`。
   - 照著前面 Worked Example 算出的數字，組一包超過 `8,192 bytes` 的 JSON padding 請求送出去，看看是不是直接拿到 `200 OK`，而且後端真的收到了那段惡意的 `sort` 欄位。
   - 接著試試看把請求縮回 `8 KiB` 以內，但把關鍵字改成 Unicode 跳脫的 `\u0053ELECT`，觀察 WAF 預設規則跟後端 `JSON.parse()` 誰被騙過了。

3. **任務二：繞過 `X-Forwarded-For` 與路徑大小寫 Rate Limiter**
   - 對 `POST http://localhost:8080/v1/auth/otp/verify` 連續打 `6` 次請求（系統設定每分鐘最多 `5` 次），確認第 `6` 次會撞牆收到 `429 Too Many Requests`。
   - 接著測試兩招繞過手法：（a）每次發請求時都換一個隨機的 `X-Forwarded-For` 標頭；（b）固定用同一個已經被封鎖的 IP，但把網址改成大寫加尾斜線的 `/v1/auth/OTP/verify/`。看看這兩招是不是都能暢行無阻地打進後端。

4. **任務三：從設定與應用程式層完成根因修補**
   - 先修 Nginx ModSecurity 設定：把 `SecRequestBodyLimitAction` 改成 `Reject`，同時把後端 Express 的 `express.json({ limit: '8kb' })` 調成跟 WAF 一樣大。
   - 再修 Express 閘道程式碼：把 `app.set('trust proxy', 1)` 鎖定為 1 跳、在路由比對前先把 URI 正規化、用 Zod schema 強制規定 `sort` 只能填白名單內的欄位名，並替 `/v1/auth/otp/verify` 換上同時綁定 `merchant_id` 與正規化 IP（IPv6 `/64` 前綴）的雙維度限流器。
   - 重新跑一次剛剛的測試腳本，確認超長請求會收到 `413`、Unicode 跳脫的非法 `sort` 欄位會被 Schema 用 `400` 擋下，而且不管怎麼換 `X-Forwarded-For` 或改網址大小寫，OTP 驗證到了第 `6` 次都會準時噴出 `429`。

- **外部靶場檢查點（PortSwigger Web Security Academy）**：
  本地練完後，可挑戰 PortSwigger Academy *SQL injection* 的 *SQL injection with filter bypass via XML encoding*，以及 *Authentication* 下用 `X-Forwarded-For` 繞過 IP 封鎖的 Practitioner 題目。先發探測請求摸清前置過濾器與後端解析器在「編碼、標頭信任、截斷長度」上的落差，再構造 payload。

### 參考解答

下面這支 Python 腳本可以直接用來驗證任務一與任務二的所有繞過情境：

```python
# verify_ch14.py - 分項對照驗證任務一 (8,192 bytes 截斷與 Unicode 跳脫) 與任務二 (XFF / 路徑大小寫獨立繞過)
import urllib.request
import urllib.error
import json

BASE = "http://localhost:8080"

def post_json(path, body_bytes, headers=None):
    hdrs = {"Content-Type": "application/json; charset=utf-8"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(BASE + path, data=body_bytes, headers=hdrs, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()

# 1. 短 payload 應被 ModSecurity 擋下 (預期 403)
short_payload = json.dumps({"sort": "id; SELECT 1--"}).encode()
st_short, _ = post_json("/v1/merchant/preferences", short_payload)
print("1. Short payload status (expected 403):", st_short)

# 2A. 超過 8,192 bytes 的填充 payload 繞過 ProcessPartial，並確認後端實際解析出 sort 欄位
padded_obj = {
    "pad": "A" * 8200,
    "sort": "id; SELECT 1--"
}
padded_payload = json.dumps(padded_obj, separators=(",", ":")).encode()
assert len(padded_payload) > 8192
st_pad, body_pad = post_json("/v1/merchant/preferences", padded_payload)
print("2A. Padded payload len:", len(padded_payload), "status:", st_pad, "parsed body:", body_pad)

# 2B. 8 KiB 內使用 JSON Unicode 跳脫 (\u0053ELECT)，測試 WAF 字面規則與後端 JSON.parse() 差異
unicode_payload = b'{"sort":"id; \\u0053ELECT 1--"}'
st_uni, body_uni = post_json("/v1/merchant/preferences", unicode_payload)
print("2B. Unicode escaped payload status:", st_uni, "parsed body:", body_uni)

# 3A. 基準對照：固定 IP 與標準路徑連續發送 6 次（前 5 次業務驗證失敗回傳 401，第 6 次觸發 429 限流拒絕）
otp_body = json.dumps({"merchant_id": "m_1001", "otp": "000000"}).encode()
baseline_statuses = [
    post_json("/v1/auth/otp/verify", otp_body, headers={"X-Forwarded-For": "198.51.100.1"})[0]
    for _ in range(6)
]
print("3A. Baseline rate limit statuses (expected 1..5 == 401, 6th == 429):", baseline_statuses)

# 3B. 單獨驗證 X-Forwarded-For 輪換繞過（路徑固定為標準 /v1/auth/otp/verify）
xff_bypass_statuses = [
    post_json("/v1/auth/otp/verify", otp_body, headers={"X-Forwarded-For": f"198.51.100.{i + 10}"})[0]
    for i in range(10)
]
print("3B. XFF rotation statuses on canonical path (vulnerable expected all 401, patched triggers 429 on merchant):", xff_bypass_statuses)

# 3C. 單獨驗證路徑大小寫與尾斜線繞過（固定同一個已被限流的 IP 198.51.100.1）
path_bypass_statuses = [
    post_json("/v1/auth/OTP/verify/", otp_body, headers={"X-Forwarded-For": "198.51.100.1"})[0]
    for _ in range(6)
]
print("3C. Path case/slash bypass statuses with fixed IP:", path_bypass_statuses)
```

任務三的修補分成兩塊。第一塊是把 Nginx ModSecurity 的部分檢查關掉，超過 `8,192 bytes` 一律拒收：

```nginx
# /etc/nginx/modsec/modsecurity.conf
SecRequestBodyLimit 8192
SecRequestBodyNoFilesLimit 8192
SecRequestBodyLimitAction Reject
```

第二塊是把 Express 閘道的信任跳數、字元集、重複 JSON key、網址正規化、白名單 Schema 與雙維度限流器一次補齊：

```typescript
// nexuspay-api/src/gateway.ts
import express from "express";
import net from "node:net";
import { z } from "zod";

const app = express();
// 精確指定信任前方 1 層 Nginx 代理，禁止設為 true
app.set("trust proxy", 1);

// 1. 精確解析 Content-Type 媒體類型與 charset 參數，僅接受 UTF-8 application/json，並在讀取原始字串時拒絕重複鍵
app.use((req, res, next) => {
  if (req.method === "POST") {
    const parts = (req.headers["content-type"] || "")
      .toLowerCase()
      .split(";")
      .map((s) => s.trim())
      .filter(Boolean);
    const mediaType = parts[0] || "";
    const charsetParam = parts.slice(1).find((p) => p.startsWith("charset="));
    if (mediaType !== "application/json" || (charsetParam && charsetParam !== "charset=utf-8")) {
      return res.status(415).json({ error: "unsupported_media_type_or_charset" });
    }
  }
  next();
});

app.use(
  express.json({
    limit: "8kb",
    verify: (_req, _res, buf) => {
      // 在 JSON.parse 執行前檢查原始字串是否存在重複鍵名，防範末值覆寫解析分歧
      const text = buf.toString("utf8");
      const keyRegex = /"([^"\\]*(?:\\.[^"\\]*)*)"\s*:/g;
      const seen = new Set<string>();
      let match: RegExpExecArray | null;
      while ((match = keyRegex.exec(text)) !== null) {
        if (seen.has(match[1])) throw new Error("duplicate_json_key");
        seen.add(match[1]);
      }
    },
  })
);

// 2. 僅以第一個問號切分 pathname 做正規化（轉小寫、合併重複斜線、剝除矩陣參數與尾斜線），完整保留原始 query string
app.use((req, _res, next) => {
  const qIdx = req.url.indexOf("?");
  const rawPath = qIdx >= 0 ? req.url.slice(0, qIdx) : req.url;
  const query = qIdx >= 0 ? req.url.slice(qIdx + 1) : undefined;
  let normPath = rawPath
    .replace(/;[^/]*/g, "")
    .replace(/\/+/g, "/")
    .toLowerCase();
  if (normPath.length > 1 && normPath.endsWith("/")) {
    normPath = normPath.slice(0, -1);
  }
  req.url = query !== undefined ? `${normPath}?${query}` : normPath;
  next();
});

// 3. 應用程式層白名單 Schema（不依賴 WAF 擋 SQLi，僅允許列舉內的合法排序欄位）
const PrefSchema = z.object({
  sort: z.enum(["created_at", "amount", "status"]),
}).strict();

app.post("/v1/merchant/preferences", (req, res) => {
  const parsed = PrefSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "invalid_preferences" });
  }
  return res.status(200).json({ ok: true, sort: parsed.data.sort });
});

// 4. 以業務主鍵 (merchant_id) 與正規化 IP (IPv6 /64 前綴) 雙維度綁定於路由層的 OTP 限流器示範
// （注意：此處使用單行程 Map 作為雙維度計數示範；生產環境應以 Redis 實作具 TTL、滑動視窗與狀態機鎖定之分散式計數器）
function normalizeRateLimitIp(rawIp: string): string {
  const ip = rawIp.replace(/^::ffff:/i, "");
  if (net.isIPv6(ip)) {
    const [head, tail = ""] = ip.split("::");
    const headParts = head ? head.split(":") : [];
    const tailParts = tail ? tail.split(":") : [];
    const missing = Math.max(0, 8 - (headParts.length + tailParts.length));
    const full = [...headParts, ...Array(missing).fill("0"), ...tailParts].map((h) => h.padStart(4, "0"));
    return `${full.slice(0, 4).join(":")}::/64`;
  }
  return ip;
}

const OtpSchema = z.object({
  merchant_id: z.string().min(1).max(64),
  otp: z.string().regex(/^[0-9]{6}$/),
}).strict();

const otpAttemptBuckets = new Map<string, number>();

app.post("/v1/auth/otp/verify", (req, res) => {
  const parsed = OtpSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({ error: "invalid_otp_payload" });
  }
  const merchantKey = `rl:otp:merchant:${parsed.data.merchant_id}`;
  const ipKey = `rl:otp:ip:${normalizeRateLimitIp(req.ip || "unknown")}`;
  const mCount = (otpAttemptBuckets.get(merchantKey) || 0) + 1;
  const ipCount = (otpAttemptBuckets.get(ipKey) || 0) + 1;
  otpAttemptBuckets.set(merchantKey, mCount);
  otpAttemptBuckets.set(ipKey, ipCount);
  if (mCount > 5 || ipCount > 5) {
    return res.status(429).json({ error: "too_many_otp_attempts" });
  }
  return res.status(401).json({ ok: false, remaining: 5 - Math.max(mCount, ipCount) });
});
```

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

1. 某微服務前方掛了雲端 WAF，該規則集的請求主體檢查視窗上限為 `16,384 bytes`（`16 KiB`），且設定為超長時僅檢查前段並放行完整請求；後端 NestJS / Express 則維持預設的 `100 KiB`（`102,400 bytes`）JSON 上限。如果攻擊者送出單一位元組 ASCII 編碼的 `{"comment":"<16,370 個 'Z' 字元>","role":"admin"}`，請問 WAF 能否掃描到 `"role":"admin"` 欄位？若要讓 `,"role":"admin"}` 的第一個位元組完全落到 `16,384 bytes` 視窗之外，`"comment"` 裡面至少要塞幾個 `'Z'` 字元？
2. 某套系統架構前方是基於 Python Flask（`request.args.get("role")`）撰寫的輕量級權限審查代理，審查通過後會將原始查詢字串原封不動轉發給後端的 PHP 帳務服務（使用 `$_GET['role']` 取值）。當攻擊者發送 `?role=viewer&role=superadmin` 時，前置 Flask 代理與後端 PHP 服務各自會讀到什麼值？為什麼這會造成權限繞過？
3. 某網站的流量固定依序經過 `Client → Cloudflare → AWS ALB → Nginx → Express` 共 `3` 層受控的反向代理（最外層的 Cloudflare 已經驗證並覆寫了真實客戶端 IP）。如果開發者把 Express 的 `app.set('trust proxy', 1)` 設成 `1`，這對 `req.ip` 跟限流器會造成什麼災難？在這套固定三層代理的架構下，應該設成多少才對？
4. 某團隊為了保護 `POST /v1/payout/confirm` 端點，在 Nginx 設定了精確路徑限流 `location = /v1/payout/confirm`，並對 IPv6 來源位址先截斷為 `/64` 前綴才計數；後端則交給預設組態的 Express 路由 `app.post('/v1/payout/confirm', ...)` 處理。為什麼攻擊者在同一個 IPv6 `/64` 子網下，連來源 IP 都不用換，依然能靠變換 URL 發動無限制的確認請求？應該怎麼從 Nginx 與 Express 兩端修補？

### 參考解答

1. **只塞 `16,370` 個 `'Z'` 時，WAF 還看得到半截的 `"role"`，無法完全躲過掃描。** 我們實際算一下位元組：開頭的 `{"comment":"` 佔 `12 bytes`，加上 `16,370` 個 `'Z'` 與結尾引號 `"`，前段總長只有 `12 + 16,370 + 1 = 16,383 bytes`（佔用 offset `0..16,382`），這會讓後段的第一個字元 `,` 剛好落在 offset `16,383`（即第 `16,384` 個位元組，仍在視窗內）。要讓後段 `,"role":"admin"}` 的第一個位元組落在 offset `>= 16,384`，必須滿足 `12 + N + 1 >= 16,384`，算出來至少要塞 **`N >= 16,371` 個 `'Z'` 字元**。
2. **前置的 Flask 代理呼叫 `request.args.get("role")` 時會取第一個出現的值 `"viewer"`，判定為一般唯讀權限而放行；但後端 PHP 的 `$_GET['role']` 會以後面出現的同名參數覆蓋前面，最終拿到 `"superadmin"`。** 這就是典型的 HTTP 參數污染（HPP）解析分歧。要徹底堵住這個破口，邊緣代理或應用程式入口必須用嚴格 Schema 拒絕任何包含重複鍵名的查詢字串（只要同一個 key 出現兩次就直接回 `400 Bad Request`），或由前置代理將解析後的單一正規化參數重新序列化再往下游傳遞。
3. **設成 `1` 代表 Express 只往回退 1 跳（只把直連它的 `Nginx` 當成代理），結果就會把 `Nginx` 的上一跳（`AWS ALB` 的內網 IP）當成真實客戶端 `req.ip`。所有經過那台 `ALB` 的正常使用者都會共用同一個限流計數器，馬上造成全站大誤殺。** 在固定經過 `Cloudflare → ALB → Nginx → Express` 這 `3` 層受控代理的架構下，應該把 `trust proxy` 設為 **`3`**（或明確填入這三層受信任代理的 CIDR 白名單），讓 Express 從右往左跳過 3 層代理，抓出真正的客戶端 IP。
4. **因為 Nginx 的 `location = /v1/payout/confirm` 是區分大小寫且不含尾斜線的精確字串匹配，但後端 Express 預設 `case sensitive routing` 與 `strict routing` 都是 `false`。** 攻擊者只要改打 `/v1/payout/Confirm`、`/v1/PAYOUT/confirm` 或加上尾斜線的 `/v1/payout/confirm/`，就不會命中 Nginx 那條精確限流規則，但轉發到後端 Express 時卻還是會進到同一個處理函式。修法是在後端把限流器直接綁在 Express 的目標路由 Handler 上（並加上 `merchant_id` 業務帳號維度計數），同時在入口處把 URI pathname 統一轉小寫、剝除尾斜線與矩陣參數後再做比對。

---

## 延伸閱讀

- **OWASP Core Rule Set (CRS) 官方文件**：了解 Paranoia Level（PL1–PL4）的設計取捨、Anomaly Scoring 計分機制與規則測試方法（https://coreruleset.org/docs/）。
- **ModSecurity v3 Reference Manual**：查閱 `SecRequestBodyLimit`、`SecRequestBodyNoFilesLimit` 與 `SecRequestBodyLimitAction`（`Reject` vs `ProcessPartial`）的行為定義（https://github.com/owasp-modsecurity/ModSecurity/wiki/Reference-Manual-%28v3.x%29）。
- **Express.js `trust proxy` 與 `body-parser` 官方文件**：掌握多層代理下 `X-Forwarded-For` 的計算方式，以及 `express.json()` 預設 `limit: '100kb'` 與字元集解碼的實作細節（https://expressjs.com/en/guide/behind-proxies.html）。
- **PortSwigger Research — Parser Differentials & WAF Bypasses**：深入研究 HTTP 標頭、JSON/Unicode 與 Multipart 邊界解析分歧的真實案例與探測技巧（https://portswigger.net/research）。
