# 第 2 章：現代偵察、黑箱與白箱審計工作流

在找漏洞時，我們面對的第一個難題往往不是技術不夠深，而是**資訊過載**。一套像 NexusPay 這樣的生產環境，動輒有十幾個微服務、上百支 API 端點，以及將近二十萬行的程式碼。如果不懂得篩選與收斂，不管是對著黑箱服務亂打 Payload，還是拉下原始碼從第一行開始讀，都會在無關痛癢的邊角邏輯裡耗光時間。

本章要建立一套結合「黑箱流量探測」與「白箱逆向追蹤」的實戰工作流，讓你在最短時間內摸清系統的真實邊界，把火力集中在最容易打破安全不變量的那幾條路徑上。

---

## 從你已知的出發

為什麼線上環境明明掛了 WAF、公開的 OpenAPI 文件也審查過好幾輪，攻擊者還是能不費吹灰之力找到一個沒設防的舊版匯出端點，一擊打穿資料庫？

排查系統瓶頸時，我們會看 CPU Flamegraph 從最耗時的葉節點（Leaf Frame）往回追呼叫堆疊；白箱安全審計也是同樣的逆向收斂：先鎖定原始 SQL 拼接、命令執行或檔案讀寫等高危 **Sink**（匯點），再順著呼叫圖往回追外部輸入 **Source**（來源）。但兩者有一個致命差異——Flamegraph 只看得到像 NexusPay 尖峰 `2,000 req/s` 這種高頻熱路徑，佔比低於 `0.1%` 的冷分支幾乎隱形；偏偏高危漏洞最愛躲在平時沒人呼叫的異常重試、除錯介面或忘了下線的舊版端點裡。只要外部請求摸得到（Reachable），就算日常流量是零，也是隨時能引爆的破口。

---

## 機制與推導

### 攻擊者目標與實質影響

偵察與審計工作流的目標很純粹：用最低的探測噪音，畫出系統真實的攻擊面地圖。

首先，在目標鎖定上，攻擊者想找出沒被納入 WAF 或 API 閘道保護的「影子端點」（像是 `/internal/metrics` 或除錯介面），直接拿到內部路由與參數規格。

其次，透過黑箱流量特徵與白箱語意追蹤，能快速鎖定沒做好認證防護的邊界與敏感資料流（Sinks），把前期盲目摸索的時間壓到最低。

最後，這階段產出的端點與參數清單，會直接變成後續攻擊鏈的導航圖——哪支 API 可以測試協定走私（見第 3 章）、哪個認證口可以偽造身分（見第 4 章）、哪個欄位能打進資料庫（見第 8 章），全靠這一步定錨。

---

### MITM 代理的底層機制與 TLS 信任鏈

黑箱偵察的第一步不是開自動掃描器狂轟濫炸，而是在客戶端與目標系統之間架起中間人（MITM）HTTP 代理。實務上最常用的是 Burp Suite，或是用 Rust 寫成的輕量級代理 Caido。

很多人只把代理當成「看 Request 和 Response 的視窗」，結果一遇到 HTTPS 憑證報錯、HTTP/2 多工降級、或是 Node.js CLI 拒絕連線就卡關。要排解這些問題，得先把代理拆回底層的 TCP 與 TLS 狀態機來看。

當你把瀏覽器或測試腳本的代理設成 `127.0.0.1:8080`，並連線到 `https://api.nexuspay.local/v1/transfers` 時，底層其實不是一條加密通道直通到底，而是**兩條完全獨立的 TLS 會話**在代理肚子裡接力拼起來的：

```text
[客戶端 / 瀏覽器] <=== TLS 會話 A ===> [MITM 代理 (127.0.0.1:8080)] <=== TLS 會話 B ===> [NexusPay Nginx]
  1. TCP 連至 127.0.0.1:8080            2. 回覆 HTTP/1.1 200               5. 代理扮成標準 TLS 客戶端
     並送出明文 HTTP CONNECT 請求          Connection Established              與上游完成真實交握
  3. 發起 TLS 會話 A ClientHello        4. 讀取 SNI 並用本地 CA 私鑰       6. 轉發解密與改寫後的明文
     (解析並驗證動態簽發的葉憑證)          即時簽發/快取目標網域葉憑證        HTTP/1.1 或 HTTP/2 幀
```

看懂這張圖，就能抓出決定攔截成敗的三個關鍵環節：

第一個環節是**明文隧道交握**（`HTTP CONNECT`）。因為 TCP 連線連的是代理的 `127.0.0.1:8080`，客戶端沒辦法一開始就直接送加密的 HTTPS 封包。它必須先送一行明文的 `CONNECT api.nexuspay.local:443 HTTP/1.1`，等代理回傳 `HTTP/1.1 200 Connection Established`，代理才會把這個 TCP socket 切換給內部的 TLS 引擎接手。

第二個環節是 **SNI 擷取與動態簽發葉憑證**。接著客戶端在 TLS 會話 A 送出 `ClientHello`，代理從明文的 **SNI**（Server Name Indication）擴充欄位讀出你想連的網域 `api.nexuspay.local`，同時從 ALPN 欄位協商要用 `h2` 還是 `http/1.1`。這時代理會拿安裝時產生的**本地 Root CA 私鑰**，當場簽發一張帶有 `SAN = DNS:api.nexuspay.local` 的 X.509v3 葉憑證（Leaf Certificate），並存進記憶體快取裡重複使用，省下每次重新產生 RSA 2048-bit 或 ECDSA P-256 金鑰對的 CPU 開銷。

第三個環節是**不同執行環境的憑證信任庫差異**。只要目標沒開憑證釘扎（Certificate Pinning）或雙向 mTLS，會話 A 能不能建起來，全看客戶端信不信任代理那張 Root CA。瀏覽器通常會直接讀作業系統的信任庫（像 macOS Keychain），但很多命令列工具根本不理作業系統的設定：

```bash
# Node.js 預設只認內建編譯的 Mozilla CA 清單，必須用環境變數掛上代理 CA
export NODE_EXTRA_CA_CERTS="$HOME/.certs/proxy-ca.crt"

# curl 可透過環境變數或 --cacert 指定代理 CA，千萬別養成加 -k 關掉驗證的壞習慣
export SSL_CERT_FILE="$HOME/.certs/proxy-ca.crt"
```

為什麼測試時不要圖方便加 `-k`（忽略 TLS 驗證）？因為真實目標的憑證過期、網域不符或簽發者異常，本身就是極有價值的偵察線索，一關掉驗證就全看不見了。另外，當目標 Nginx 同時支援 `h2` 與 `http/1.1` 時，要注意代理在會話 A 與會話 B 之間有沒有偷偷幫你把 `h2` 降級成 `http/1.1`。做第 3 章的協定走私測試前，一定要先確認代理保留了原始的協定版本與連線標頭。

---

### 黑箱指紋識別與結構化探測

掛上代理之後，黑箱偵察的重點不是亂塞攻擊字串，而是**從伺服器的回應細節，反推後端的技術棧、中介軟體順序與隱藏介面**。

#### 1. 從報錯形狀與超時行為看穿後端框架

正式環境的反向代理通常會把 `Server` 或 `X-Powered-By` 標頭洗掉，但框架跟資料庫在遇到異常時的預設反應卻很難藏得住。

先看邊緣代理與後端的連線超時。在 NexusPay 的基準架構裡，前端 Nginx 的 `proxy_read_timeout` 設為 `30 s`，後端 Node.js 的 `keepAliveTimeout` 則是 `5 s`。當後端卡住超過 `30 s` 沒回音，Nginx 會吐出 `504 Gateway Time-out`；而如果 Node.js 剛好在閒置滿 `5 s` 關閉連線的那一瞬間，Nginx 又拿同一條連線轉發新請求，就會因為連線被重設而偶發噴出 `502 Bad Gateway`。光是觀察這兩種錯誤碼與時間差，就能看出前面擋了一層反向代理。

再看輸入驗證的報錯格式。試著把原本該傳整數的 `amountCents` 改成字串 `"abc"` 送出去：

```json
{"message":["amountCents must be an integer number"],"error":"Bad Request","statusCode":400}
```

看到這種固定帶 `message` 陣列、`error` 與 `statusCode` 的 `400 Bad Request`，十之八九是 NestJS 預設的 `ValidationPipe`（搭配 `class-validator`）。如果缺欄位時回傳的是 `422 Unprocessable Entity` 外加 `detail` 陣列，背後通常是 Python 的 FastAPI / Pydantic；要是連 JSON 語法都故意少寫一個括號，伺服器卻直接噴出 `SyntaxError: Unexpected token`，就知道請求在進業務邏輯前是被 Node.js 的 JSON 解析層（像 Express `body-parser`）攔下來的。

同理，把原本該填 UUID 的參數換成單引號或亂碼，如果收到 `500` 還夾帶 `22P02`（`invalid input syntax for type uuid`）這類 SQLSTATE 錯誤碼，馬上就能確定底層資料庫是 PostgreSQL，而且後端沒做好全域例外遮罩。

#### 2. 挖出藏在前端 JS 裡的 API 規格

現在的前後端分離系統（SPA），最常把後端底細賣掉的往往不是伺服器，而是打包送到瀏覽器的前端 JavaScript 檔案。

第一步先找有沒有忘了關的規格文件。除了常見的 `/swagger.json`、`/openapi.json`、`/v3/api-docs`，很多 NestJS 專案會把文件掛在 `/api/docs-json` 或 `/internal/spec`。更常見的疏失是在打包上線時，把 `.js.map`（Source Map）一起丟上了靜態目錄。只要抓到 `.js.map`，裡面的 `sources`、`names` 和 `sourcesContent` 欄位就能直接把前端 TypeScript 原始碼的目錄結構、DTO 定義跟所有 API 路徑還原出來。

就算沒有 Source Map，對著代理攔到的所有 `.js` 檔跑一輪正規表達式搜尋（比對 `"/v1/`、`"/api/`、`"/internal/`、`fetch(`、`axios.`），也常常能挖出管理後台專用、或是還沒對外開放的隱藏端點。

#### 3. 軟 404 基線校準與隱藏參數探測

如果前端檔案裡沒線索，得靠字典檔探測路徑時，最容易踩到的坑就是**軟 404**（Soft 404）。很多 SPA 閘道遇到不認識的路徑，不會乖乖回 `404`，而是統一回傳 `200 OK` 外加同一份 `index.html`，或是統一回傳 `401 Unauthorized`。如果掃描工具只看 HTTP 狀態碼，就會把五千個不存在的路徑全部當成命中，瞬間被假警報淹沒。

對付軟 404 的標準做法是**先抓基線向量**（Baseline Vector）。在開掃之前，先隨手打 3 個絕對不存在的隨機路徑（例如 `/v1/probe_8a91f`、`/v1/probe_8a91f.json`、`/v1/probe_8a91f/`），把回應的狀態碼、位元組長度、單字數、行數、`Content-Type`，以及拿掉動態欄位（像 `X-Request-Id` 或隨機 nonce）後的結構特徵記下來。開始掃描後，只要回應長得跟這組基線一模一樣，就直接當成軟 404 濾掉；只有那些狀態碼、長度或結構偏離基線的回應，才是真正值得細看的候選端點。

摸出端點之後，還可以從兩個方向繼續深挖：

- **切換 HTTP 方法**：文件上只寫了 `GET /v1/accounts/export`，不妨順手試試 `POST`、`PUT`、`PATCH`、`DELETE` 和 `OPTIONS`。有時候開發者只對 `GET` 掛了權限檢查，其他方法卻落入預設路由，或者能從 `405 Method Not Allowed` 回傳的 `Allow` 標頭看出這支路由還支援哪些操作。
- **塞入隱藏參數測試反應**：在 JSON body 或網址參數裡試著塞進 `debug`、`admin`、`role`、`isInternal`、`sortBy` 這類常見的內部欄位。怎麼知道後端有沒有偷讀這個欄位？秘訣是**故意傳錯型別**——比如送出 `{"debug": ["array_probe"]}`。如果一個沒事的端點突然從 `200 OK` 變成 `400` 型別驗證失敗，或是回應時間與快取行為明顯改變，就代表後端某層驗證器或程式真的有在處理這個隱藏參數！

---

### 白箱 Source-to-Sink 逆向審計法（30 分鐘快速分流）

拿到原始碼進入白箱審計時，後端工程師最容易犯的毛病，就是用「寫功能」的習慣從頭讀 code——先看 `package.json`、再看資料庫 Schema、接著一個個 Service 慢慢往下看。面對一個近二十萬行、上百支端點的程式碼庫，這樣讀半小時大概只看完了半個模組，真正會出事的漏洞早就不知道藏在哪個角落了。

呼應開頭講的逆向收斂思維，白箱審計一開始的 30 分鐘必須嚴格執行**三階段逆向分流**：

| 時間分配 | 審計階段 | 核心動作 | 階段產出 |
|---|---|---|---|
| `0–8 分鐘` | **第一階段：盤點入口與認證管線** | 掃描全域路由表（Controller 裝飾器、Express `Router`、Nginx `location`）以及請求經過的中介層順序（Middleware → Guard → Interceptor → Pipe），把所有標記免認證（如 `@Public()`）或沒開白名單過濾的入口全部圈出來。 | 完整的端點清單，以及標註了「免認證／弱檢查」的入口清單 |
| `8–18 分鐘` | **第二階段：從高危 Sink 往回追** | 用 `rg` 直接搜出整個專案裡的高危 Sink（原始 SQL、命令執行、檔案讀寫、對外發 HTTP、反序列化、動態物件合併），再從每個命中點順著呼叫鏈往回推，看哪幾條能連回第一階段的外部入口。 | 直接濾掉幾百條安全的普通 CRUD，只留下少數真正摸得到高危 Sink 的呼叫鏈 |
| `18–30 分鐘` | **第三階段：緊盯關鍵業務與跨邊界轉換** | 鎖定扣款轉帳、權限變更、Webhook、多租戶查詢與檔案處理端點，一層層檢查 DTO 驗證有沒有漏掉 Header、原始 Query 或 Path 參數。 | 可直接拿來寫 POC 驗證的 Source-to-Sink 追蹤表與優先檢查清單 |

以 NexusPay 這種 TypeScript / Node.js 後端來說，第二階段用 `rg` 搜尋時，盯準的就是那些**為了彈性或效能而繞過框架保護的底層 API**：

- **資料庫操作**：重點搜 `\$queryRawUnsafe`、`\$executeRawUnsafe`、TypeORM 的 `.createQueryBuilder(` 搭配 `.orderBy(` 或 `.where(` 字串拼接，還有原生 `pg` 套件的 `.query(` 模板字串。
- **系統指令與檔案讀寫**：重點搜 `child_process`（特別是 `exec`、`execSync` 與開了 `shell: true` 的 `spawn`），以及 `fs.` 搭配 `path.join` 或 `path.resolve` 卻沒檢查最終路徑前綴的地方。
- **對外網路請求**：重點搜 `fetch(`、`axios(`、`http.request(` 裡面直接塞了使用者傳入的網址或路徑片段的呼叫點。
- **動態物件與程式執行**：重點搜 `Object.assign(`、手寫遞迴的 `merge(` 或 `cloneDeep(`、帶了 `reviver` 的 `JSON.parse(`，以及 `vm.runIn` 和 `eval(`。

這裡我們先用 `rg` 做快速人工定位；到了第 28 章，我們會把這些搜尋模式升級成 CodeQL 與 Semgrep 的跨檔案自動化語意規則，第 29 章則會進一步用覆蓋率導引的 Fuzzing 來轟炸原生解析器。

---

### 攻擊面優先序評分模型（APS）

不管跑完黑箱還是白箱，手上通常都會列出一長串（40 到 80 個）看起來有點可疑的端點。如果沒有一套排優先順序的標準，很容易在一個「只會漏出無關緊要版本號」的小問題上磨了兩天，卻放過就躺在隔壁的未授權轉帳或 SQL 注入。

為了讓排優先序有客觀依據，我們用四個維度相乘，算出一支端點的 **APS**（Attack Surface Priority Score，攻擊面優先序分數）：

```text
APS = Exposure × Boundary_Crossings × Input_Complexity × Sink_Impact
```

這四個維度都按 `1` 到 `4` 分級，乘出來的總分介於 `1` 到 `256` 之間：

1. **暴露程度**（`Exposure`）：不用登入就能打的公開端點或 Webhook 給 `4` 分；一般註冊用戶或商戶能打的給 `3` 分；要管理員特權才能打的給 `2` 分；只限內網或 mTLS 服務互打的給 `1` 分（但要確認前端代理沒設錯把它轉發出去）。
2. **跨越的信任邊界數**（`Boundary_Crossings`）：算算看外部輸入從進門到最後改變狀態，一共跨過了幾層不同的行程或解析器（從客戶端進 Nginx 算第 1 道，往後每經過 Node.js、PostgreSQL、Redis 或底層 C 模組就往上加，最高計到 `4` 分）。跨越多層，兩邊解析器雞同鴨講的機率就越高。
3. **輸入結構複雜度**（`Input_Complexity`）：只收簡單布林、固定列舉或整數 ID 給 `1` 分；收普通字串或一般扁平 JSON 給 `2` 分；收巢狀物件、動態 key 名稱、多步驟參數或網址給 `3` 分；收 ZIP/XML/PDF 二進位複合檔、自訂排序條件或表達式給 `4` 分。
4. **匯點破壞力**（`Sink_Impact`）：只影響單次查詢或普通日誌給 `1` 分；能跨租戶偷看資料或污染快取給 `2` 分；能改動核心帳本、改權限或打內網 SSRF 給 `3` 分；能做到任意程式碼執行（RCE）、任意寫檔或完全繞過登入給 `4` 分。

算出來分數 **`≥ 72` 的直接列為 P0**（馬上動手深挖並打 POC 驗證），`32–71` 列為 **P1**，`< 32` 的等主線查完有空再看。

試著用這把尺量一下：一支公開免登入（`4`）、跨過 3 道邊界（`3`）、接收動態巢狀篩選物件（`3`）、而且底層確定接了原始 SQL 拼接能拿來繞過認證或控制系統（`4`）的端點，分數高達 `4 × 3 × 3 × 4 = 144` 分；相反地，一支要管理員權限（`2`）、只跨 1 道邊界（`1`）、只傳一個布林開關（`1`）、頂多影響快取狀態（`2`）的端點，算出來只有 `2 × 1 × 1 × 2 = 4` 分。時間該花在哪裡，一算就清楚。

---

### Worked Example：追蹤 `POST /v1/transfers` 五層呼叫鏈與污點傳播

現在我們把前面講的白箱三階段分流跟黑箱封包對齊，實際拿 NexusPay 的核心轉帳端點 `POST /v1/transfers` 跑一遍。

按照全書基準設定，NexusPay 單一測試帳戶的初始餘額是 `10,000` 分（`$100.00`），單次轉帳／提領上限也是 `10,000` 分。這套後端共有 `184,000` 行 TypeScript 程式碼、`112` 支註冊路由，但對外公開的 OpenAPI 文件只列了 `98` 支。

我們在白箱第二階段跑了一行 `rg -n "queryRawUnsafe|\\.query\\(" src/`，只花 `0.9 s` 就從十八萬行程式碼裡抓出 `7` 個檔案；其中 `src/transfers/ledger.repo.ts:112` 正好躺在 `POST /v1/transfers` 的呼叫鏈上。下面我們把攻擊者送出的真實 HTTP 封包（為方便閱讀省略部分 JWT 簽章字元）從第 1 層一路追到第 5 層，算清楚每個位元組與污點狀態的變化：

```text
=== [1] 觸發請求線路報文 (Wire Request — 精確位元組計算) ===
POST /v1/transfers HTTP/1.1
Host: api.nexuspay.local
Authorization: Bearer eyJhbGciOiJSUzI1NiIs... (RS256 JWT, TTL 900 s, sub=usr_1042, tenantId=tnt_alpha)
Content-Type: application/json
X-Idempotency-Key: idem-9921-a
Content-Length: 121

{"fromAccountId":"acc_1001","toAccountId":"acc_9999","amountCents":2500,"currency":"USD","routeTag":"fast' ORDER BY 1--"}

位元組核對：
  {"fromAccountId":"acc_1001",         -> 28 bytes
  "toAccountId":"acc_9999",            -> 25 bytes (累計 53 bytes)
  "amountCents":2500,                  -> 19 bytes (累計 72 bytes)
  "currency":"USD",                    -> 17 bytes (累計 89 bytes)
  "routeTag":"fast' ORDER BY 1--"}     -> 32 bytes (累計 121 bytes，與 Content-Length: 121 完全吻合)
  其中 routeTag 字串值 "fast' ORDER BY 1--" 長度 = 18 字元 (18 bytes <= @MaxLength(64) 上限)

=== [2] 五層呼叫鏈與污點傳播表 ===
Layer | 元件與程式碼位置                           | 接收資料與邊界參數                        | 校驗 / 淨化機制                          | 污點狀態
------+--------------------------------------------+-------------------------------------------+------------------------------------------+------------------
L1    | Nginx 反向代理                             | 完整 HTTP/1.1 報文 (Body = 121 bytes)     | 僅檢請求大小與路徑前綴 /v1/；            | TAINTED (全未淨化)
      | (nginx/conf.d/gateway.conf:42)             | proxy_read_timeout = 30 s                 | 不解析 JSON 欄位語意                     |
      |                                            | Node keepAliveTimeout = 5 s               |                                          |
------+--------------------------------------------+-------------------------------------------+------------------------------------------+------------------
L2    | NestJS JwtAuthGuard                        | Authorization Bearer Token (RS256)        | 驗證簽章 (JWKS 快取 300 s) 與過期時間；  | auth = CLEAN
      | (src/auth/jwt-auth.guard.ts:28)            | 解出 req.user = {sub:usr_1042, tnt_alpha} | 僅認證身分，未核對 fromAccountId 歸屬    | body = TAINTED
------+--------------------------------------------+-------------------------------------------+------------------------------------------+------------------
L3    | NestJS ValidationPipe + CreateTransferDto  | Body 121 bytes -> DTO 實例                | amountCents: @IsInt @Min(1) @Max(10000)  | amountCents = CLEAN
      | (src/transfers/dto/create-transfer.dto:19) | 同時 Header X-Idempotency-Key 繞過 Pipe   | routeTag: @IsString @MaxLength(64)       | routeTag = TAINTED
      |                                            |                                           | (未限制字元白名單，18 <= 64 合法通過)    | idemKey = TAINTED
------+--------------------------------------------+-------------------------------------------+------------------------------------------+------------------
L4    | TransfersController -> TransfersService    | dto.fromAccountId="acc_1001"              | 檢查餘額 10,000 >= 2,500 (扣款後將為     | routeTag = TAINTED
      | (src/transfers/transfers.service.ts:84)    | dto.amountCents=2500, dto.routeTag(18 B)  | 7,500)；將 routeTag 直接拼接進路由查詢   | (跨行程準備送出)
------+--------------------------------------------+-------------------------------------------+------------------------------------------+------------------
L5    | PostgreSQL 16 Raw SQL Sink                 | 執行拼接 SQL：                            | 使用 prisma.$queryRawUnsafe(...)         | SINK HIT!
      | (src/transfers/ledger.repo.ts:112)         | SELECT fee_bps FROM routing_rules         | 完全缺乏參數化綁定 ($1)                  | 單引號跳脫資料平面
      |                                            | WHERE tag = 'fast' ORDER BY 1--'          |                                          | 進入 SQL 控制平面
------+--------------------------------------------+-------------------------------------------+------------------------------------------+------------------

=== [3] 攻擊面優先序評分 (APS) 與白箱剪枝效益 ===
1. APS 計算：
   - Exposure = 3 (需已註冊商戶 Token，非匿名但極易取得)
   - Boundary_Crossings = 3 (Client -> Nginx -> NestJS -> PostgreSQL 跨越 3 道關鍵邊界)
   - Input_Complexity = 2 (扁平 JSON DTO 含自由字串欄位)
   - Sink_Impact = 3..4 (若該 Raw SQL 注入用於篡改帳本費率或餘額狀態為 3 [54 分, P1]；若結合資料庫高權限角色達成完整認證繞過或命令執行則為 4 [72 分, P0])
   - 總分 = 3 × 3 × 2 × (3..4) = 54..72 分 -> 落入 P1 至 P0 優先驗證級別！

2. 白箱剪枝效益量化：
   - 原始程式碼總量 = 184,000 LOC (112 條註冊路由)
   - Phase 1–2 逆向篩選後保留 = 7 個命中 Raw Sink 的檔案，其中在轉帳模組追蹤中確認 1 條註冊路由（POST /v1/transfers）可由外部 HTTP Source 直接觸發（占全系統 112 條註冊路由的 1/112 ≈ 0.89%）
   - 黑箱 vs 白箱交叉印證耗時：15 分鐘內完成定位，而非逐行閱讀整個 Repository。
```

仔細看這張表的 **L3**，這裡藏著一個無數團隊踩過的坑：在 `CreateTransferDto` 上面，`routeTag` 欄位明明**有掛驗證裝飾器**（`@IsString()` 和 `@MaxLength(64)`）。很多工程師在做 Code Review 時，看到 DTO 欄位有掛裝飾器就放心跳過了。

但檢查「它是字串」而且「長度 `18 bytes <= 64`」，跟「擋掉 SQL 單引號控制字元」完全是兩碼子事！從污點追蹤的角度來看，`routeTag` 過了 L3 之後依然是帶毒的 `TAINTED` 狀態，只是披上了一層「已通過 `ValidationPipe`」的保護色，最後在 L5 一頭撞進 `prisma.$queryRawUnsafe(...)` 引爆 SQL 注入。

---

## 故障模式與防禦

搞懂偵察與審計怎麼跑之後，我們來看看實戰中最常讓審計人員漏看、或是讓系統防線失守的四種故障模式。

### 故障模式 1：MITM 代理攔不到流量，或偷偷降級了協定

在測行動端 App、桌面程式或內部微服務時，有時就算你已經把代理的 Root CA 裝進系統信任庫，代理畫面上還是半個請求都看不到，日誌裡只有一排瞬間斷線的 TLS Alert。

這通常有兩個原因：第一是客戶端在會話 A 寫死了**憑證釘扎**（Certificate Pinning），只認得官方伺服器那張公鑰的 SPKI SHA-256 雜湊值，代理現場簽出來的葉憑證當場被拒收；第二是上游伺服器在會話 B 要求**雙向 TLS**（mTLS），而你的代理沒有掛上合法的客戶端憑證跟私鑰，握手直接失敗。另外還有一個隱形盲點：有些舊版代理在轉發給上游時，會預設把 `HTTP/2` 強制降級成 `HTTP/1.1`，導致那些只有在 `HTTP/2` 下才會觸發的漏洞完全測不出來。

在防禦與測試上，可以這樣處理：
- **站在防禦方**：對敏感 App 與內部微服務啟用 mTLS，確實能大幅拉高外人掛代理側錄的門檻；但千萬別把客戶端的 Certificate Pinning 當成無敵鐵布衫，因為攻擊者只要拿到客戶端環境的控制權，照樣能進記憶體把檢查憑證的函式換掉。
- **站在授權測試方**：測試自家系統時，直接用執行環境提供的信任旗標（像 Node.js 的 `NODE_EXTRA_CA_CERTS`）或測試版建置參數掛載憑證，並檢查代理的 ALPN 設定，確保前後端走的 HTTP 協定版本跟正式環境一致。

### 故障模式 2：以為「沒寫進文件的 API 就沒人知道」（OWASP API9）

很多團隊靠人工手寫 Swagger / OpenAPI 文件，或是只幫前端用得到的 API 加上文件註解；偏偏外層的 Nginx 反向代理為了省事，直接把整個目錄前綴一股腦往後端轉發：

```nginx
location /v1/ {
    proxy_pass http://nexuspay_api:3000;
}
```

結果就是，好幾年前留下來的 `/v1/transfers/legacy-export`、工程師除錯完忘記拔掉的 `/v1/debug/routes-health`，甚至原本只打算給內部排程器打的 `/v1/internal/ledger-snapshot`，全都被這條寬鬆的 `location /v1/` 暴露到公網上。這正是 **OWASP API Security Top 10:2023 API9**（Improper Inventory Management，資產清單管理不當）點名的經典破口。只看著 OpenAPI 文件做測試的團隊根本不知道它們存在，攻擊者卻能從前端 `.js` 檔或字典掃描裡一抓一個準。

要堵住影子 API，必須雙管齊下：
1. **讓程式碼成為唯一的路由真相**：在 CI 管線裡自動啟動服務並匯出框架實際註冊的路由樹（如 Express 或 NestJS 的 Router 清單），直接跟公開的 OpenAPI 規格做比對（Schema Diff）。只要發現有沒登記在規格書上的幽靈路由，立刻擋下 PR 不准合併。
2. **在閘道層改用嚴格路徑白名單**：Nginx 或 API Gateway 絕不能無腦轉發整個 `/v1/` 前綴，而是由審查過的 OpenAPI 規格自動產生允許的「路徑 + HTTP 方法」白名單，不在清單上的請求在最外層就回傳 `404`。

### 故障模式 3：把 Source Map 跟資料庫報錯直接噴給前端

如果在打包上線時沒把 `.js.map` 拿掉，或是沒把框架預設的錯誤堆疊攔下來，攻擊者只要隨便送一個型別不對的參數，伺服器就會熱情地把完整的原始碼路徑、TypeScript 函式名稱、ORM 查詢語句和資料庫錯誤碼雙手奉上（對應 MITRE CWE-209 錯誤訊息洩漏）。

防禦這點非常明確：
- **建置時徹底剝離 Source Map**：在 CI 打包完後，把 `.map` 檔直接上傳到內部的錯誤追蹤系統（像私有部署的 Sentry），並從最終上線的 Docker 映像檔與 CDN 目錄裡刪得一乾二淨。
- **掛上全域例外遮罩**：在 NestJS 或 Express 掛上全域的 `AllExceptionsFilter`，對外一律只回傳標準錯誤碼跟一組隨機的 `traceId`，真正的錯誤堆疊與 SQLSTATE 只准寫進內部日誌。同時，把未授權路徑的 `401`、`403` 與 `404` 回應格式統一，別讓攻擊者靠回應長相猜出內部有哪些隱藏路由。

### 故障模式 4：迷信全域 `ValidationPipe`，忽略了框架生命週期

在白箱審計 NestJS 專案時，最常聽到開發者自信滿滿地說：「我們在 `main.ts` 開了全域的 `app.useGlobalPipes(new ValidationPipe({ whitelist: true }))`，所有外部輸入都有 DTO 把關，不可能有問題！」

會有這種錯覺，是因為忘了 NestJS 處理一筆請求的固定順序：

```text
Middleware → Guards → Interceptors (前置) → Pipes → Route Handler → Interceptors (後置)
(任一階段若拋出未處理的例外，則直接跳進 Exception Filters)
```

看清楚 `Pipes` 的位置了嗎？它排在第四關！這意味著有三個地方可以輕易繞過它：
1. **在 `Pipes` 之前跑的元件**：所有的 `Middleware` 跟 `Guards` 都跑在 `Pipes` 前面。如果你在自訂的認證 Middleware 或限流 Guard 裡直接去讀 `req.query` 或 `req.headers`，那時候 `ValidationPipe` 根本還沒上班，讀到的全是原汁原味的髒資料。
2. **沒綁定 DTO 類別的裝飾器**：只要開發者在 Controller 方法裡偷懶寫了 `@Req() req: Request` 直接拿 `req.body`，或是寫了 `@Headers('x-idempotency-key') key: string`、`@Query('sort') sort: string` 這種只標了基本型別 `string`、沒綁 DTO 類別也沒單獨掛 Pipe 的參數，全域 `ValidationPipe` 就會直接跳過它（就像前面 Worked Example 裡的 `X-Idempotency-Key` 一樣）。
3. **只開 `whitelist: true` 加上寬鬆的 `@IsString()`**：就算欄位有進 DTO，如果只掛了一個不限字元的 `@IsString()` 或 `@IsObject()`，壞字元照樣能大搖大擺走過 `ValidationPipe`，一路殺進底層的 Sink。

要鎖死這些破口，團隊應該用 ESLint 規則禁止在業務 Controller 裡直接拿 `@Req()`；所有的 `@Headers()`、`@Param()`、`@Query()` 都必須綁上帶有嚴格正規表達式或格式限制（像 `@IsUUID('4')`、`@Matches(/^[a-zA-Z0-9_-]{1,32}$/)`）的 DTO。更重要的是，像「這個帳戶到底屬不屬於這個租戶」或「餘額夠不夠扣」這種核心安全不變量，一定要壓到 Guard 跟資料庫交易層去檢查，絕不能只靠外層的 Pipe。

---

## 動手做

- **難度**：入門
- **預估時間**：45 分鐘

現在我們要在本地跑起 NexusPay 測試環境，親手把 MITM 代理（Caido 或 Burp Suite Community Edition）的 TLS 信任鏈接通，接著用黑箱指紋識別、前端 JS 採礦與軟 404 基線校準，挖出 **3 個沒寫在公開 OpenAPI 文件上的影子端點**；最後切回白箱視角，用 `rg` 在 10 分鐘內追出它們對應的原始碼與高危 Sink，算出 APS 分數。

### 步驟 1：架好本地代理與 TLS 信任鏈

1. 啟動本地 NexusPay 測試環境（Nginx 預設監聽 `https://api.nexuspay.local:8443`，公開的 OpenAPI 文件在 `https://api.nexuspay.local:8443/api-docs-json`）。
2. 打開 Caido 或 Burp Suite，確認代理監聽在 `127.0.0.1:8080`，並把代理的 Root CA 憑證匯出成 `~/.certs/proxy-ca.crt`。
3. 在**絕不加 `-k` 忽略憑證檢查**的前提下，設定環境變數讓命令列工具信任這張代理憑證，並透過代理抓下公開的 OpenAPI 規格：

```bash
export HTTP_PROXY="http://127.0.0.1:8080"
export HTTPS_PROXY="http://127.0.0.1:8080"
export SSL_CERT_FILE="$HOME/.certs/proxy-ca.crt"
export NODE_EXTRA_CA_CERTS="$HOME/.certs/proxy-ca.crt"

# 驗證 TLS 交握成功，且無任何憑證報錯
curl -v https://api.nexuspay.local:8443/api-docs-json -o openapi-public.json
jq '.paths | keys' openapi-public.json
```

### 步驟 2：黑箱偵察——校準軟 404 基線並挖出 3 個影子端點

1. **從前端 JS 找線索**：把測試瀏覽器的代理設到 `127.0.0.1:8080`，登入 NexusPay 商戶測試帳號（初始餘額 `10,000` 分）。到代理的 HTTP History 篩出所有 `.js` 檔案，搜尋 `/v1/`、`internal`、`legacy`、`debug` 這些關鍵字。
2. **先抓軟 404 基線，再掃候選路徑與方法**：先打三個隨機路徑記下狀態碼與回應長度當作基線，接著帶著相同的認證 Header 掃描常見的內部路徑，並同時測試 `GET`、`POST` 與 `OPTIONS` 三種方法：

```bash
# 1. 建立軟 404 基線向量
for p in probe_71f2a probe_99c0b probe_33d1e; do
  curl -s -o /dev/null -w "%{http_code} %{size_download}\n" \
    -H "Authorization: Bearer $MERCHANT_TOKEN" \
    -H "Content-Type: application/json" \
    "https://api.nexuspay.local:8443/v1/$p"
done

# 2. 比對候選端點與基線的差異，並切換 HTTP 方法測試
for path in internal/ledger-snapshot transfers/legacy-export debug/routes-health metrics admin/config; do
  for method in GET POST OPTIONS; do
    code_len=$(curl -s -X "$method" -o /dev/null -w "%{http_code}:%{size_download}" \
      -H "Authorization: Bearer $MERCHANT_TOKEN" \
      -H "Content-Type: application/json" \
      "https://api.nexuspay.local:8443/v1/$path")
    echo "$method /v1/$path -> $code_len"
  done
done
```

### 步驟 3：白箱交叉驗證（10 分鐘 Source-to-Sink 定位）

切進 NexusPay 後端原始碼目錄，用兩行 `rg` 指令找出剛剛那 3 個影子端點寫在哪個 Controller 裡、有沒有誤標 `@Public()`，以及底層有沒有碰到高危 Sink：

```bash
# 第一階段：列出所有 Controller 路由與免認證標記
rg -n "@Controller\(|@(Get|Post|Put|Delete|Patch)\(|@Public\(" src/

# 第二階段：直接搜出所有高危 Sink
rg -n "queryRawUnsafe|executeRawUnsafe|\.query\(|exec\(|execSync\(|readFileSync" src/
```

找出來之後，請幫這 3 個影子端點各算一次 APS 四維度分數，排出修補優先順序。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地演練完後，請到 **PortSwigger Web Security Academy** 挑戰下面兩組官方實驗室，檢驗自己在純黑箱環境下的偵察手感：

- **Information disclosure** 系列：
  - *Information disclosure in error messages*（Apprentice）
  - *Source code disclosure via backup files*（Apprentice）
  - *Information disclosure in version control history*（Apprentice）
- **API testing** 系列：
  - *Exploiting an API endpoint using documentation*（Practitioner）
  - *Finding and exploiting an unused API endpoint*（Practitioner）

> **卡點提示**：
> - 打備份檔與版本控制洩漏那兩關時，先去看看 `robots.txt` 或常見靜態目錄有沒有露餡；如果抓到 `.git` 目錄下的二進位物件，想想看怎麼在本地把它還原回看得懂的原始碼。
> - 打 *unused API endpoint* 時，別只盯著網址改參數。仔細看前端點按鈕時發出去的 API 路徑，試著對同一個資源路徑輪流換上 `GET`、`PATCH`、`DELETE` 等不同方法，並盯緊狀態碼跟 `Content-Type` 的報錯提示。

---

### 參考解答

#### 1. TLS 信任鏈驗證結果

掛上 `SSL_CERT_FILE` 後，`curl -v` 會顯示伺服器憑證是由 Burp 或 Caido 的 Local CA 簽發的（Subject 為 `CN=api.nexuspay.local`），並順利回傳 `HTTP 200` 抓下 `openapi-public.json`。如果還是跳出 `self-signed certificate in certificate chain`，請檢查環境變數指到的檔案是不是標準 PEM 格式，以及路徑有沒有打錯。

#### 2. 基線比對與 3 個影子端點

前面三個長度都是 15 bytes 的隨機路徑（像 `/v1/probe_71f2a`），回傳的都是固定的 `404 77`（也就是 NestJS 預設的 `{"message":"Cannot GET /v1/probe_71f2a","error":"Not Found","statusCode":404}`，剛好 `77 bytes`）。只要挑出回應偏離 `404:77`、又不在 `openapi-public.json` 裡面的路徑，就能抓出這 3 個影子端點：

- **`GET /v1/debug/routes-health`**：從前端打包進 `main.*.js` 的殘留字串（或字典掃描）抓到的。它回傳 `200 OK`（約 `480 bytes`），因為開發者只加了 `@ApiExcludeEndpoint()` 把它從文件裡藏起來，卻順手標了 `@Public()` 免認證，結果直接把內部微服務連線狀態跟 Node.js 版本號暴露給全世界。
- **`POST /v1/transfers/legacy-export`**：打 `GET` 時跟基線一樣回 `404`，但從舊版 JS 區塊發現線索改打 `POST` 後，卻回傳 `400 Bad Request`（`ValidationPipe` 抱怨缺少必填欄位）。這證明舊版匯出路由根本沒刪，一般商戶帶著 Token 就能打，而且後端還直接拿傳進來的檔名丟進 `path.join` 處理。
- **`GET /v1/internal/ledger-snapshot`**：原本只給內部排程器呼叫的帳本快照端點，因為 Nginx 寫了寬鬆的 `location /v1/` 轉發而直接暴露在公網入口。視建置版本的 Guard 設定，它可能回傳 `403` 或只檢查了有沒有登入卻沒檢查管理員角色，是第 6 章越權測試的頭號目標。

#### 3. 白箱定位與 APS 優先序排序

跑完 `rg` 後，可以在 `src/debug/debug.controller.ts`、`src/transfers/transfers.controller.ts` 和 `src/internal/ledger-snapshot.controller.ts` 找到這三支路由的原始碼。

算 APS 分數時，如果 `POST /v1/transfers/legacy-export` 接收的是巢狀篩選物件（`Complexity = 3`），而且確認能碰到核心帳本寫入或任意檔案讀寫的高危 Sink（`Sink_Impact = 3..4`），它的分數就是 `Exposure(3) × Boundary(3) × Complexity(3) × Sink_Impact(3..4) = 81..108` 分（就算只收扁平字串 `Complexity = 2`，也有 `54..72` 分），直接衝上 **P0 / P1** 第一順位！相較之下，`GET /v1/debug/routes-health` 雖然免登入（`Exposure = 4`），但跨 2 道邊界（`2`）、無複雜輸入（`1`）、只做單純狀態讀取（`1`），算出來只有 `4 × 2 × 1 × 1 = 8` 分。所以我們當然先把火力拿去打 `legacy-export`，而不是先花兩天去寫 `routes-health` 的報告。

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

試著不看前面的筆記，獨立推導下面 4 個實戰問題：

1. **自動化測試腳本的憑證報錯**：你寫了一支 Node.js 腳本（用官方預設安裝的 Node.js 22 執行），裡面已經設好把請求導向本機的 Caido 代理（`http://127.0.0.1:8080`）。明明你已經把 Caido 的 Root CA 加進 macOS 的系統鑰匙圈（Keychain）並設為「永遠信任」，用 Chrome 看同一個網站完全正常，跑這支 Node.js 腳本時卻一直噴 `UNABLE_TO_VERIFY_LEAF_SIGNATURE`。為什麼會這樣？在**不關掉 TLS 驗證**的前提下，該怎麼一行指令修好？
2. **設計軟 404 過濾規則**：某個後端服務前面掛了 SPA 路由回退規則，只要打到不存在的網址，一律回傳 `HTTP 200 OK`、標頭帶 `Content-Type: text/html; charset=utf-8`，內容則是固定 `2,048 bytes` 的 `index.html`（裡面嵌了一組每次請求都會變的 `32 bytes` 隨機 CSP nonce）。如果你拿一份 5,000 個路徑的字典去掃它，要怎麼設計過濾跟交叉驗證條件，才不會被 5,000 個假 `200 OK` 淹沒，同時又不會漏掉真正有反應的 API？
3. **抓出繞過 NestJS `ValidationPipe` 的破口**：某團隊在 NestJS 專案開啟了全域的 `ValidationPipe({ whitelist: true, forbidNonWhitelisted: true })`，並規定所有 `POST` 請求都必須綁定 DTO。現在有一支處理商戶 Webhook 回呼的路由與自訂租戶解析 Middleware，請寫出請求進入 NestJS 後經過各個元件的生命週期順序，並指出攻擊者能從哪兩個位置把未經 DTO 白名單過濾的髒資料偷渡進後端？
4. **冷路徑為什麼會拿到破百的 APS 高分**：有一支只在「每月月底結算失敗、且帶了特殊重試標頭」時才會走到的舊版相容端點，在線上 CPU Flamegraph 裡的耗時佔比低於 `0.01%`。為什麼這支在效能圖上幾乎看不見的函式，在安全審計的 APS 評分裡卻可能拿到超過 `100` 分的 P0 等級？請給出一組實際的四維度分數來說明。

---

### 參考解答

1. **Node.js 憑證信任庫差異與解法**：
   - **原因**：Chrome 瀏覽器會直接讀 macOS 系統的 Keychain 信任庫；但官方建置的 Node.js 在編譯時是把 Mozilla 的 CA 根憑證清單靜態包進執行檔裡，預設根本不會去讀 macOS Keychain。所以當 Caido 代理現場簽發葉憑證給 Node.js 時，Node.js 在自己的內建清單裡找不到 Caido 這張 Root CA，當場就報 `UNABLE_TO_VERIFY_LEAF_SIGNATURE`。
   - **正確解法**：執行前加上環境變數 `export NODE_EXTRA_CA_CERTS=/path/to/caido-ca.crt`，把代理的根憑證外掛進 Node.js 的信任清單裡（千萬別設 `NODE_TLS_REJECT_UNAUTHORIZED=0` 把整個 TLS 驗證關掉）。
2. **軟 404 過濾與交叉驗證設計**：
   - **第一步（抓基線與正規化比對）**：先打 3 個隨機 UUID 路徑確認基線是 `status = 200`、`Content-Type = text/html`、長度 `2,048 bytes`。比對時先把回應裡那段 `32 bytes` 的動態 nonce 挖掉再算雜湊（或比對長度是否落在 `2,048 ± 16 bytes` 且 DOM 結構相同）。只要同時符合這三個條件的回應，就標記為軟 404 濾掉；只要 `Content-Type` 變成 `application/json`、狀態碼變成 `400/401/403/405/500`，或是長度明顯不一樣，就留下來。
   - **第二步（切換標頭與方法防漏抓）**：怕有些真路由剛好也是回傳差不多長度的 HTML，掃描時可以同步加上 `Accept: application/json` 標頭，並搭配 `POST` 或 `OPTIONS` 方法再打一次。很多 SPA 回退規則只對 `GET` 生效，一遇到 `POST` 就會露出馬腳，回傳真正的 `400`、`401` 或 `405`。
3. **NestJS 生命週期與兩個 Pipe 繞過點**：
   - **生命週期順序**：`Middleware → Guards → Interceptors（前置）→ Pipes → Route Handler → Interceptors（後置）`（中間只要拋出沒接住的例外，就會轉進 `Exception Filters`）。
   - **繞過寫法一**：寫在 `Middleware` 或 `Guard` 裡面的輸入讀取（比如在 Middleware 裡直接拿 `req.headers['x-tenant-id']` 或 `req.query` 做判斷），因為它們在 `Pipes` 之前就執行了。
   - **繞過寫法二**：在 Controller 方法裡直接用 `@Req() req: Request` 讀 `req.body`，或是用 `@Headers('x-tag') tag: string`、`@Query('sort') sort: string` 這種只標了基本型別 `string`、沒綁 DTO 類別也沒單獨掛 Pipe 的參數裝飾器。全域 `ValidationPipe` 對基本型別不會套用 DTO 的 `whitelist` 規則，髒資料會直接穿過去。
4. **冷路徑拿高 APS 的實例與原因**：
   - **實算範例**：假設這支月底重試端點因為 Nginx 寬鬆轉發，一般登入商戶都能打得到（`Exposure = 3`，若免登入則是 `4`），請求進來會跨過 `Nginx → Node.js → 外部子行程/檔案系統` 共 3 道邊界（`Boundary_Crossings = 3`），接收的是複合式的 XML/ZIP 批次對帳檔（`Input_Complexity = 4`），而且底層剛好接了任意檔案寫入或命令執行 Sink（`Sink_Impact = 4`）。乘起來就是 `3 × 3 × 4 × 4 = 144` 分（免登入更高達 `192` 分），遠超過 `72` 分的 P0 線！
   - **視角差異**：效能看的是「日常累計花掉多少時間」，所以只管高頻熱路徑；但資安看的是「能不能碰到、撞上去會不會死」。只要門沒鎖好，平常一百年沒人走一次的冷門通道，攻擊者只要主動送一發請求就能當場打穿系統。

---

## 延伸閱讀

- **RFC 9110（HTTP Semantics）與 RFC 9112（HTTP/1.1）**：重點看 RFC 9110 §9.3.6 的 `CONNECT` 隧道機制，以及 RFC 9112 第 6 節訊息長度與第 9.3 節持久連線規範，把代理轉發的底層規矩摸透。
- **RFC 8446（TLS 1.3）、RFC 6066（SNI）與 RFC 7301（ALPN）**：了解 MITM 代理在 TLS 握手時是怎麼偷看 `server_name` 並協商 `h2` 或 `http/1.1` 的。
- **OWASP API Security Top 10:2023 — API9: Improper Inventory Management**：看看真實世界裡有多少企業栽在忘了下線的舊版 API 與文件不同步。
- **NestJS Official Documentation — Request Lifecycle**：把 Middleware、Guards、Interceptors、Pipes 和 Filters 的執行順序印在腦子裡，做白箱 Code Review 時才不會被表面的全域設定騙過。
- **PortSwigger Web Security Academy — *Information disclosure* 與 *API testing* 學習路徑**：免費且品質極高的線上靶場，適合練熟報錯分析與隱藏端點挖掘。
- **Caido Architecture & Burp Suite Documentation**：對照現代用 Rust/Tokio 寫成的輕量代理跟老牌 JVM 代理在憑證管理與流量過濾上的設計思路。

