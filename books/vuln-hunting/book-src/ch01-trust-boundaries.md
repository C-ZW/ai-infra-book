# 第 1 章：信任邊界、攻擊面與漏洞模型

我們會用同一套系統貫穿全書 37 章的實戰演練：**NexusPay**。它是本書虛構的多租戶即時結算平台（對應本地 Docker 靶機 `books/vuln-hunting/labs/`），架構完全比照現代後端生產環境：最外層是 Nginx 反向代理與 Node.js API 閘道，中間是 PostgreSQL 多租戶帳本（單一測試帳戶基準餘額為 `10,000` 分，即 `$100.00`）與 Redis 快取，往內則串接了負責客服與對帳的 AI Agent、Kubernetes 叢集，以及為了衝高吞吐量而用 Rust/C 寫成的原生封包解析模組 `libnexus-parse`。

看這樣一套系統時，功能開發與漏洞挖掘的視角截然不同。寫功能時，我們關心正常流程怎麼跑通、已知的錯誤怎麼接住；但找漏洞時，我們盯著的是另一件事：**有哪些狀態是系統設計師心裡預設「絕不可能發生」，卻沒有在程式碼或架構上真正封死的？** 本章就從 NexusPay 的提領流程出發，拆解這條防線是怎麼在跨元件邊界上被鑿穿的。

---

## 從你已知的出發

為什麼 PostgreSQL 明明設了 `CHECK (balance >= 0)`，扣款時也乖乖用了 `SELECT ... FOR UPDATE` 列鎖，帳戶裡的錢還是會被多領走，甚至餘額越領越多？

因為資料庫的 ACID 約束，只管得到「已經走進資料庫」的那一行 SQL。只要走出資料庫的邊界，這個約束就毫無知覺：如果後端 API 只檢查了提領金額不超過上限 `amount <= 10000`，卻漏檢查 `amount > 0`，攻擊者傳入 `-5000`，資料庫執行 `10000 - (-5000)` 得到 `15000`，完全符合 `balance >= 0`，帳本卻憑空多出 `$50.00`。又或者，前端 Nginx 與後端 Node.js 對 HTTP 請求邊界的切法不同、應用層查快取時漏帶租戶前綴、甚至底層 C/Rust 模組解析封包時發生整數溢位，這些跨層狀態的錯位，資料庫連看都看不到。這正是把「資料庫約束」放大到整個系統的**安全不變量**（Security Invariant）：不管外部送來多詭異的輸入、多極端的併發時序，系統在身分、帳務、權限與記憶體上的鐵律都絕對不能被打破。一旦存在一條從外部輸入就能觸發、把系統推向違規狀態的路徑，那條路徑就是安全漏洞。

---

## 機制與推導

### 攻擊者目標與實質影響

攻擊者花力氣跨越系統邊界，不是為了看伺服器噴一個 `500 Internal Server Error`，而是為了打破安全不變量，換取實質的控制權或金流利益：

在業務層面，最直接的就是掏空或灌水帳本。比如繞過 NexusPay 單次 `10,000` 分的提領上限，在極短時間窗內重複出金（雙花攻擊，見第 12 章），或是傳入特殊數值讓餘額無中生有。

在權限層面，目標則是突破隔離。例如穿透前端反向代理的路徑限制直達內部管理 API，或拿租戶 A 的憑證去偷看、扣減租戶 B 的帳戶資產（見第 6 章）。

更常見的是把單點破口串成跨層攻擊鏈。攻擊者先利用前端代理與後端伺服器的協定解析差異發動 HTTP 請求走私（見第 3 章），偷渡未授權請求進入內網，再一步步把邊緣的小破口放大成整個叢集的控制權。

### 一般 Bug 與安全漏洞的分界：安全不變量

假設 NexusPay 在匯出月底對帳單時，因為浮點數四捨五入少算了一分錢，這是一般的功能 Bug。它雖然算錯了，但觸發條件與結果都是固定的，既沒有讓別人偷看到資料，也沒有讓使用者憑空變出錢來。

但換成下面這段提領邏輯，性質就完全不同了：

```javascript
// 看似正常、實則洞開的提領檢查
if (req.body.amount <= 10000 && account.balance >= req.body.amount) {
  account.balance -= req.body.amount;
}
```

只要呼叫端在 JSON 裡送出 `{"amount": -5000}`，`-5000 <= 10000` 為真，餘額減去負數反而暴增 `5,000` 分；或者在多步驟結帳流程裡，跳過前面的付款確認，直接打最後一步的出金 API。這就是**安全漏洞**——外部使用者只要構造一組特定輸入，就能讓系統一步步走到「未認證卻能改資料」或「不入金卻能加餘額」的禁止狀態。

在實戰中，我們要守住的安全不變量可以歸納為四條底線：

1. **身分與租戶隔離**：任何操作都必須確認「你是誰」，而且租戶 A 的憑證永遠只能碰租戶 A 的資源，絕不能跨界讀寫租戶 B 的資料。
2. **資金守恆與流程順序**：沒有合法的外部入金，帳本總金額絕不能增加；多步驟流程（像 MFA 驗證或先扣款後出金）必須一步步照順序走，不能跳關。
3. **資料與指令分離**：使用者傳進來的字串（不管是姓名、發票備註還是 AI 對話），永遠只能當作純資料處理，絕不能在傳遞過程中被 SQL 引擎、系統 Shell、瀏覽器 DOM 或大型語言模型當成控制指令執行。
4. **記憶體與執行環境邊界**：底層程式讀寫記憶體時，絕不能超出當初配置的緩衝區長度；容器裡的行程也只能待在自己的命名空間裡，不能摸到宿主機核心。

---

### 信任邊界與 NexusPay 四層架構

一套系統裡，只要資料從「不受控的地方」流向「有權限的地方」，或是從「租戶 A」流向「共用服務」，中間跨過的那條分水嶺就叫做**信任邊界**（Trust Boundary）。

很多漏洞的根源，都是開發者對信任邊界抱著錯誤的期待——以為「上游應該已經幫我檢查過了」，或是以為「連得進這個 port 的都是自己人」。守住信任邊界的唯一原則，就是接收端在跨越邊界的入口處，親自把關來源身分、資料格式與業務限制。

把開頭提到的 **NexusPay** 攤開來看，全書 37 章的所有攻防，都發生在以下四個層級與四道信任邊界（TB-1 到 TB-4）上：

```
  [不可信外部輸入: 公網商戶 / 瀏覽器 / 惡意 Webhook / 攻擊者]
                            │
   ══════════ TB-1: 邊緣與協定邊界 (2,000 req/s 尖峰) ══════════
                            ▼
  ┌──────────────────────────────────────────────────────────┐
  │ Layer 1: 邊緣與代理層                                    │
  │  Nginx 反向代理 (proxy_read_timeout = 30 s)              │
  │  Node.js 22 API Gateway (keepAliveTimeout = 5 s)         │
  └─────────────────────────┬────────────────────────────────┘
                            │
   ══════════ TB-2: 應用、授權與資料儲存邊界 ═════════════════
                            ▼
  ┌──────────────────────────────────────────────────────────┐
  │ Layer 2: 應用與帳本層                                    │
  │  TypeScript REST / GraphQL / gRPC / WebSocket 服務       │
  │  PostgreSQL 16 多租戶帳本 (單戶基準 10,000 分 = $100.00) │
  │  Redis 7 (Session / Rate Limit / 分散式鎖)               │
  └──────────┬──────────────────────────────┬────────────────┘
             │                              │
   ══ TB-3: AI 與編排邊界 ══════   ══ TB-4: 原生二進位與核心邊界 ══
             ▼                              ▼
  ┌─────────────────────────┐  ┌─────────────────────────────┐
  │ Layer 3: AI 與雲端編排  │  │ Layer 4: 原生執行時期與核心 │
  │  MCP / Tool-Use Agent   │  │  libnexus-parse (Rust/C FFI)│
  │  多租戶 RAG 向量庫      │  │  TLV 檔頭 8B / 上限 64 KiB  │
  │  K8s Pod / IAM / CI/CD  │  │  V8 Isolate / Linux Kernel  │
  └─────────────────────────┘  └─────────────────────────────┘
```

這四道邊界各自有明確的系統參數，也各自藏著最容易踩坑的盲點：

先看 **TB-1**（邊緣與協定邊界）。公網流量先打進 Nginx（`proxy_read_timeout = 30 s`），再轉發給後端 Node.js 22 閘道（`keepAliveTimeout = 5 s`），系統設計承受的尖峰流量是 `2,000 req/s`。這裡最致命的誤會，就是以為「Nginx 看到的 HTTP 請求，跟 Node.js 看到的一定是同一個請求」。只要兩邊對標頭或連線逾時的處理差了一點點，就會衍生出第 3 章的請求走私與第 14 章的 WAF 繞過。

接著往內走到 **TB-2**（應用、授權與資料儲存邊界）。這裡躺著 PostgreSQL 16 多租戶帳本（每個測試帳戶初始餘額固定為 `10,000` 分，即 `$100.00`）與 Redis 7 快取。所有從 HTTP 請求帶進來的 `tenant_id`、`account_id` 與 `amount` 在通過檢查前全部不可信，身分認證、租戶比對與原子扣款都必須在這一層一次鎖死。

再看左下角的 **TB-3**（AI 與雲端編排邊界）。NexusPay 用了 AI Agent 協助客服查詢與自動對帳，Agent 會透過 MCP 呼叫內部退款工具、讀取多租戶 RAG 向量庫，而整套服務跑在 Kubernetes Pod 上。當商戶在發票備註裡塞一段惡意提示詞，純文字資料就在這裡跨過邊界，搖身一變成了指揮 AI 越權退款的控制指令（見第 16 至 19 章）。

最後是右下角的 **TB-4**（原生二進位與核心邊界）。為了高速解析銀行對帳封包，Node.js 透過 N-API 呼叫底層 Rust/C 寫的 `libnexus-parse`。這種二進位 TLV 封包有著固定 `8 bytes` 的檔頭（`magic: 2B`、`type: 2B`、`len: 4B` 無號整數），並規定合法負載上限為 `65,536 bytes`（`64 KiB`）。一旦跨越這條線，就離開了 JavaScript 的記憶體保護傘；只要長度和指標沒算準，寫爆的直接是行程記憶體（見第 20 至 27 章）。

---

### 順著資料流抓破口：Source、Sink 與 Sanitizer

畫出信任邊界之後，拿到一份十萬行的原始碼，該從哪裡看起？

答案是追著「外部資料」跑。先看這段常見的報表匯出程式碼：

```javascript
// 從網址參數拿檔名，直接拼進系統指令壓縮回傳
const file = req.query.reportName; 
exec(`tar -czf /tmp/out.tar.gz /var/nexus/reports/${file}`);
```

不管是人工看 code 還是用 CodeQL 這類靜態分析工具，抓漏洞的手法都是緊盯三個角色——也就是**污點追蹤**（Taint Tracking）的三元組：

第一個角色是 **Source**（來源），也就是不可信資料跨過邊界流進程式的入口。像上面那行 `req.query.reportName`，或是平常寫後端天天碰的 `req.params`、`req.body`、`req.headers`、Webhook payload、上傳的檔案內容，乃至於傳給 C/Rust FFI 的那塊緩衝區指標與長度，全都是帶毒的 Source。

第二個角色是 **Sink**（匯點），也就是真正執行危險動作、會改變系統狀態或碰觸底層資源的終點。上面例子裡的 `exec(...)` 就是典型的命令執行 Sink；其他像是不帶參數化的 SQL 查詢（`prisma.$queryRawUnsafe`）、讀寫檔案（`fs.open`）、對外發請求（`fetch(userUrl)`），或是 C 語言裡的 `memcpy(dst, src, len)`，只要外部髒資料一路沒被攔住、原封不動流進 Sink，漏洞就爆了。

夾在兩者中間把關的，就是第三個角色 **Sanitizer**（淨化器）。它的工作是在資料抵達 Sink 之前，把危險因子洗掉、跳脫，或是乾脆用結構化的方式把資料跟指令隔開。不過，不同寫法的 Sanitizer，防禦力天差地遠：

| 防禦做法 | 怎麼運作 | 常見寫法 | 為什麼常被繞過 |
|---|---|---|---|
| 黑名單過濾（Filtering） | 看到已知的壞字元就擋掉或刪掉 | 檢查字串有沒有 `../`、`SELECT`、`127.0.0.1` | 駭客改用雙重 URL 編碼、大小寫混穿、或把 IP 寫成八進位／十六進位就穿過去了 |
| 編碼與轉義（Escaping） | 把控制字元跳脫成普通字元 | HTML 實體編碼、Shell 引號跳脫 | 貼錯地方（拿防 XSS 的 HTML 轉義去擋 SQL 注入），或者後面某個元件又自作聰明解碼了一次 |
| 結構隔離與白名單（Parameterization / Allowlist） | 從語法結構上鎖死「資料永遠只是資料」，或只准許清單內的固定值 | SQL Prepared Statement、排序欄位用 Enum 對照、`execFile` 傳參數陣列（並加上 `--` 防止參數被當成選項） | 開發者為了動態拼資料表名或欄位名，圖方便又退回字串拼接 |

所以看 code 時，千萬別看到中間有呼叫一個 `sanitize()` 函式就安心收工。**真正要追到底的是：從 Source 到 Sink 的每一條 if/else 分支，是不是都走了對的結構隔離？而且在通過檢查之後、送進 Sink 之前，有沒有人又多做了一次解碼或字串拆解，把原本鎖好的防護給拆了？**

---

### 用 STRIDE 與攻擊樹盤點威脅

知道怎麼追單一資料流之後，面對整套系統時，我們還需要兩套工具來幫忙抓出所有潛在破口：**STRIDE** 用來橫向掃描，確保六大類威脅都沒有漏看；**攻擊樹**（Attack Tree）則用來縱向拆解，算出哪一條攻擊路線對駭客來說最省力。

#### STRIDE 六大威脅維度

拿到架構圖時，不用對著整張圖空想，而是指著圖上的每一條跨邊界連線與儲存節點，逐一用 STRIDE 六個字母拷問它：

- **S — Spoofing**（偽造身分）：能不能假冒別人？例如偽造 JWT 簽章、偷拿別人的 Session，或是冒充內部微服務直接打後端。
- **T — Tampering**（竄改資料）：能不能半路偷改資料？例如把提領金額改成負數、偷改請求裡的租戶 ID，或是靠記憶體溢位覆寫掉相鄰變數。
- **R — Repudiation**（否認行為）：幹了壞事能不能死不認帳？例如盜領之後順手刪掉操作紀錄，或是系統根本沒留不可竄改的稽核日誌，出事完全追不到人。
- **I — Information Disclosure**（資訊洩漏）：能不能看到不該看的東西？例如改個編號就看到別家商戶的帳本餘額（BOLA），或是伺服器報錯時直接把資料庫結構與環境變數噴給前端。
- **D — Denial of Service**（阻斷服務）：能不能把系統搞掛？例如送一個超深巢狀的 GraphQL 查詢卡死 Node.js 事件迴圈，或送畸形封包讓底層 C/Rust 模組直接崩潰重啟。
- **E — Elevation of Privilege**（權限提升）：能不能越級打怪？例如一般商戶呼叫管理員專用 API（BFLA）、哄騙 AI Agent 幫自己執行高權限退款，甚至從容器裡逃逸到宿主機核心。

#### 攻擊樹與攻擊成本實算

用 STRIDE 列出所有可能出事的地方後，我們還要回答一個最現實的工程問題：**攻擊者會先挑哪一條路下手？**

這時候就輪到**攻擊樹**上場了。把攻擊者的最終目的（比如「破壞 NexusPay 提領帳本」）放在樹根，往下拆解出達成目標的各條分支：必須全部湊齊才能成功的條件標為 `AND`，只要挑一條走通就行的路線標為 `OR`。

下面我們直接拿 NexusPay 的提領 API（`POST /v1/tenants/:tid/withdraw`），把橫跨 **TB-1、TB-2 與 TB-4 三條信任邊界**的三種攻擊走法擺在一起，用真實系統參數推算一遍狀態變化與攻擊成本：

```text
=== Worked Example: NexusPay 提領 API 跨三條信任邊界之狀態轉移與攻擊成本推導 ===

[系統基準常數（依全書基準數字表）]
- 帳戶 acct_A 初始測試餘額 B_0 = 10,000 分 ($100.00)
- 單次提領上限 W_max = 10,000 分
- 系統設計尖峰吞吐量 = 2,000 req/s
- 原生憑證解析器 libnexus-parse TLV 檔頭 = 8 bytes (len 為 uint32)，合法 payload 上限 = 65,536 bytes

[帳本安全不變量 Inv_ledger]
- Inv_1 (非負餘額): B_db >= 0
- Inv_2 (資金守恆與正值提領): B_db + ∑ successful_withdrawals == B_0 + ∑ verified_deposits 且單筆提領 amount > 0 (無外部入金時 B_db + W_total == 10,000 分)
- Inv_3 (租戶隔離): caller.tenant_id == acct.tenant_id
- Inv_4 (記憶體安全): FFI 目的緩衝區須有效、存活且可寫，並在無溢位算術下滿足 0 <= offset <= alloc_size 且 0 <= write_len <= alloc_size - offset

-------------------------------------------------------------------------
路徑 1 (TB-2 應用層 ↔ PostgreSQL 16 交易邊界): 併發檢查與扣款分離 (TOCTOU)
-------------------------------------------------------------------------
假設資料表未設非負 CHECK 約束，且後端邏輯先執行 SELECT balance FROM accounts WHERE id = $1 檢查 >= amount，
通過後即觸發外部出金並獨立執行 UPDATE accounts SET balance = balance - $1 WHERE id = $2。
攻擊者對同一帳戶同時送出 N = 5 筆 amount = 10,000 的請求，且 5 筆皆在首次扣款寫回前完成讀取。

狀態轉移表 (非原子讀寫且無 DB 非負約束，t_2..t_4 為各筆出金與扣款皆完成後之快照):
步驟 | 執行主體 | 讀取餘額 B_read | 通過檢查? | 累積已出金 W_total | DB 餘額 B_db | Inv_ledger 狀態
-----|----------|-----------------|-----------|--------------------|--------------|-----------------
t_0  | 初始狀態 | -               | -         | 0                  | 10,000       | 成立 (All True)
t_1  | Req #1..5| 皆讀得 10,000   | 5/5 通過  | 0                  | 10,000       | 成立
t_2  | Req #1   | -               | -         | 10,000             | 0            | 成立
t_3  | Req #2   | -               | -         | 20,000             | -10,000      | 違背 Inv_1 (且已超額出金)
t_4  | Req #3..5| -               | -         | 50,000             | -40,000      | 違背 Inv_1 (超額出金 40,000)

數值驗證:
- 5 筆請求僅佔一秒尖峰請求量（2,000 req/s）的 0.25%（5 / 2,000 = 0.0025）；只要相關請求在首筆扣款提交前完成讀取即可觸發競態。
- 第 2 筆成功時即產生超額出金；5 筆皆成功時超額提領金額 ΔW = W_total - B_0 = (5 × 10,000) - 10,000 = 40,000 分 ($400.00)。

-------------------------------------------------------------------------
路徑 2 (TB-1 邊緣輸入與授權邊界): 單筆請求負數金額或租戶欄位繞過
-------------------------------------------------------------------------
分支 2A (缺下界檢查): 僅驗證 amount <= 10,000，未驗證 amount > 0，且扣款僅更新 B_db = B_0 - amount 而未實際匯出正值資金 (W_total = 0)。
輸入: amount = -5,000
檢查結果: (-5,000 <= 10,000) == true
狀態轉移: B_1 = B_0 - amount = 10,000 - (-5,000) = 15,000 分 ($150.00)，此時 B_1 + W_total = 15,000 != 10,000
結果: 僅需 1 次請求即違反單筆正值提領規則並令帳本餘額憑空增加 5,000 分 ($50.00)，違背 Inv_2。

分支 2B (租戶檢查缺失): 呼叫端持 tenant_A Token，但路徑參數填入 :tid = tenant_B，
目標帳戶 acct_B 餘額 10,000 分。
狀態轉移: B_B(after) = 10,000 - 10,000 = 0（未授權扣減他戶餘額；若出金目的地由呼叫端指定且完成結算，攻擊者即可實收 10,000 分 = $100.00）。
結果: 僅需 1 次請求即違背 Inv_3。

-------------------------------------------------------------------------
路徑 3 (TB-4 Node.js ↔ libnexus-parse FFI 邊界): TLV 長度整數溢位
-------------------------------------------------------------------------
假設提領須附帶硬體簽章 TLV 封包，傳入 libnexus-parse 前未強制驗證 0 < len <= 65,536，
且原生程式以 32 位元無號整數計算緩衝區配置: alloc_size = (len + 8) mod 2^32。
輸入: magic = 0x4E58 (2B), type = 0x0001 (2B), len = 0xFFFF_FFF8 (4B = 4,294,967,288)
數值計算:
- 若誤用有號 32 位元比較: 0xFFFF_FFF8 解讀為 -8，(-8 <= 65,536) == true (繞過上限檢查)
- 配置大小: (4,294,967,288 + 8) mod 4,294,967,296 = 4,294,967,296 mod 4,294,967,296 = 0 bytes
- 後續若實作對這個容量只有 0 byte 的目的區域執行任何正長度寫入（write_len > 0），寫入量 > alloc_size (0 bytes)，立即違背 Inv_4。

-------------------------------------------------------------------------
攻擊樹彙整比較 (Root Goal: 破壞 Inv_ledger，取「最低前置成本」路徑)
-------------------------------------------------------------------------
[Root: 破壞 NexusPay 提領安全不變量] (OR 閘)
  ├── [OR 路徑 1 (TB-2)] 併發雙花 (AND: 具合法帳戶 ∧ N >= 2 筆併發請求於首筆扣款前讀得餘額 ∧ 非原子扣款)
  │     最小成功請求數 = 2 次 (表中以 5 次展示) | 時序同步依賴 = 高 (須落在讀寫競態視窗內)
  ├── [OR 路徑 2 (TB-1)] 負值/跨租戶提領 (AND: 具最低權限 Token ∧ 缺下界或租戶比對)
  │     最小請求數 = 1 次    | 時序同步依賴 = 無 (0 ms)  | 前置同步成本 = 最低 (最優先防禦!)
  └── [OR 路徑 3 (TB-4)] FFI 緩衝區溢位 (AND: 提領管線可達 FFI ∧ len 驗證與無號溢位失守)
        最小請求數 = 1 次    | 記憶體利用門檻 = 高 (需視實作寫入行為與緩解機制而定)
```

把這三條路徑攤開來比對，結論非常震撼：

路徑 3 的 FFI 整數溢位聽起來最酷炫，但攻擊者得先跨過有號／無號數值檢查，還要克服現代作業系統的記憶體保護才能穩定控制程式；路徑 1 的併發雙花雖然能用 5 筆請求從 `10,000` 分帳戶裡超額領出 `40,000` 分（`$400.00`），但至少還得對準毫秒級的讀寫時間窗同時發包。

反觀**路徑 2**，既不用算記憶體偏移，也不用搶併發時間差，只要隨手打一筆 `curl` 把金額改成 `-5,000` 或把網址上的 `:tid` 換成別人的租戶 ID，當場就能得手。**面對同樣的破壞目標，攻擊者永遠會挑最省事、前置條件最少的那條路走。** 如果團隊花了好幾個月去加固底層 C/Rust 模組，卻忘了在 API 入口檢查正整數跟租戶歸屬，整道防線照樣一戳就破。

---

## 故障模式與防禦

看懂攻擊者怎麼挑軟柿子捏之後，我們回頭檢視後端架構，就會發現大部分被攻破的系統，都栽在以下四種常見的設計盲點上。

### 故障模式 1：只在最外層擋，內層完全不設防

想像一下，團隊在 Nginx 或雲端 WAF 上設了嚴格的規則，擋掉所有長得像 SQL 注入或跨租戶的路徑，然後後端微服務就放心地寫出 `SELECT * FROM accounts WHERE id = '${req.body.id}'`。

只要所有流量都乖乖走同一條路，看起來好像沒事。但真實系統裡，總會有內部微服務直接打 container port、新增了一支 GraphQL 端點忘了掛同一套規則，或是像第 3 章、第 14 章會講到的：Nginx 與後端 Node.js 對特殊 URL 編碼或 HTTP Header 的解讀根本不一樣。一旦外層被繞過，裡面就是毫無防備的軟肚子。

要根治這個問題，防線就必須**緊貼著 Sink 與資源本身**。邊緣的 WAF 和 Nginx 只能當作幫你擋掉大半雜訊的濾網；真正攸關生死的規則——像是 SQL 參數化查詢、餘額不得為負的 `CHECK` 約束、還有「這筆資料到底屬不屬於這個租戶」的權限核對——都必須在執行操作與讀寫資料庫的那一刻親自強制執行。

### 故障模式 2：先檢查、再修改的時間差（TOCTOU）

很多後端工程師寫扣款時，很自然會寫出這樣的兩段式邏輯：

```javascript
// 第一步：先查餘額夠不夠 (Check)
const acct = await db.query('SELECT balance FROM accounts WHERE id = $1', [id]);
if (acct.balance >= amount) {
  // 第二步：呼叫外部銀行 API 出金，再回來扣款 (Use)
  await bankApi.Payout(id, amount);
  await db.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, id]);
}
```

這就是典型的 **TOCTOU**（Time-of-Check to Time-of-Use，檢查與使用分離）。在第一步 `SELECT` 讀出餘額 `10,000` 分的那一瞬間，「餘額充足」這件事確實是真的；但等過了幾毫秒、到第二步真正執行 `UPDATE` 的時候，另外四筆一模一樣的併發請求早就趁這段空檔也都讀到了 `10,000` 分，結果就是前面 Worked Example 路徑 1 算給你看過的——`10,000` 分的帳戶被領走 `50,000` 分。同樣的毛病也常出現在檔案處理：先檢查路徑是不是合法檔案，下一行才呼叫作業系統開檔，結果中間幾微秒內檔案早就被換成指向敏感設定檔的符號連結（Symlink，詳見第 9 章與第 12 章）。

對付 TOCTOU 的鐵則很簡單：**能用一條原子操作搞定的事，絕不拆成「先讀、再算、後寫」兩步。** 在 NexusPay 裡，我們應該把所有檢查條件全部塞進同一條 SQL `UPDATE` 語句，讓資料庫在拿著列鎖的當下一次做完判斷與扣款：

```sql
UPDATE accounts
SET balance = balance - $1
WHERE id = $2
  AND tenant_id = $3
  AND balance >= $1
  AND $1 > 0
  AND $1 <= 10000
RETURNING balance;
```

只要傳進去的 `$2`（帳戶）與 `$3`（租戶）是從已驗證的登入憑證拿到的，而且後端嚴格規定「只有當這條 SQL 成功更新了 1 列並回傳新餘額時，才准呼叫外部出金 API」，這短短幾行 SQL 就同時鎖死了三件事：金額必須是介於 `1` 到 `10,000` 之間的正數、帳戶確實屬於該租戶、而且扣款當下餘額一定夠扣。不管外面同時湧進多少併發請求，資料庫的列鎖都會強迫它們排隊逐一檢查，把路徑 1 的雙花跟路徑 2 的負數提領一次封死。

### 故障模式 3：出錯時居然選擇「放行」（Fail-Open，OWASP A10:2025）

先看一段在緊急修搶線上故障時，很容易不小心寫出來的權限檢查中介層：

```typescript
try {
  const isAllowed = await permService.verify(req.user, req.params.tenantId);
  if (!isAllowed) return res.status(403).send('Forbidden');
} catch (err) {
  // 權限服務偶爾連線逾時，先記個 log 放行，免得影響線上商戶結帳！
  logger.warn('Permission service timeout, skipping check', err);
}
return next();
```

開發者心裡想的是「高可用性」與「優雅降級」，但在攻擊者眼裡，這簡直是天上掉下來的禮物。回想一下 NexusPay 的基準設定：最外層 Nginx 的 `proxy_read_timeout` 是 `30 s`，後端 Node.js 的 `keepAliveTimeout` 是 `5 s`。攻擊者只要故意塞爆內部權限服務的連線池，或是送出會讓權限解析器拋出例外的怪異封包，程式一跳進 `catch`，後面那句 `return next()` 就會把所有沒權限的請求當成貴賓直接放行。

這種「遇到例外就預設放行」的毛病叫做 **Fail-Open**，也是 **OWASP Top 10:2025 A10**（Mishandling of Exceptional Conditions，特殊情況處理不當）點名的頭號殺手。同理，在 C/Rust FFI 邊界上，如果算緩衝區大小發現整數溢位，卻只印一行警告或回傳未初始化的指標繼續往下跑，下場一樣是記憶體被寫穿。

守住這關沒有別的捷徑，就是徹底貫徹 **Fail-Closed**（失敗即拒絕）：凡是跟身分、權限、金額、記憶體邊界有關的檢查，只要遇到逾時、解析失敗、型別不對或下游服務掛點，一律當場回傳 `401`、`403` 或 `503` 並中斷流程，絕對不准在 `catch` 區塊裡偷偷放行。

### 故障模式 4：一層解一次，每層看到的都不是同一個東西

想像一筆請求進到系統：第一關的檢查模組拿原始字串掃了一遍，確定裡面沒有 `../` 就蓋章放行；結果到了第二關的業務模組，順手呼叫了一次 `decodeURIComponent()` 把 `%2e%2e%2f` 解碼成了 `../`；又或者，JavaScript 層明明檢查了 JSON 裡的數字長度，傳進底層 C 函式時卻被截斷成 32 位元整數。當好幾層元件各自拿著原始輸入重複解析時，前面做的檢查跟後面真正拿來用的值，早就不是同一個東西了。

要避免這種各說各話的慘劇，最乾淨的做法是 **Parse, Don't Validate**（在入口一次解析成型，別讓下游自己切字串）。當不可信的原始輸入剛跨過信任邊界時，就在入口處做唯一一次嚴格解析，把它轉換成型別明確、欄位固定的內部資料結構（例如確定是 `1` 到 `10,000` 之間的正整數金額、確定已經正規化並核對過權限的租戶 ID）。從這一刻起，後面的所有函式都只准拿這個轉好的結構辦事，誰都不准再回頭去碰、去解碼最原始的那串外部字串。

### 跨層防禦重點對照

| 常見威脅 | 容易被穿破的寫法 | 真正能鎖死不變量的防線 |
|---|---|---|
| 帳本變負數與併發雙花 | 先 `SELECT` 讀出餘額在程式裡比大小，再發 `UPDATE` | 單條帶條件的原子 `UPDATE ... WHERE balance >= $1 AND $1 > 0` + 資料庫 `CHECK (balance >= 0)` + 冪等鍵 |
| 跨租戶偷看或偷改（BOLA） | 只在前端畫面藏按鈕，或用正規表達式擋 URL | 後端全面從驗證過的 Token 取出 `tenant_id` 綁定查詢，並搭配 PostgreSQL RLS 把關（見第 6 章） |
| 前後端對 HTTP 請求切法不同 | 只靠外層 WAF 攔截特定網址字串 | 對齊 Nginx 與 Node.js 的 HTTP 標頭解析規則、拒收不合規範的模糊標頭，並調好 Keep-Alive 逾時設定（見第 3 章） |
| FFI 長度溢位與記憶體越界 | 只在 JS 層看 `buf.length`，或用有號整數比大小 | 在 Rust/C 入口處強制用無號整數檢查上限（`<= 65536`）並用 `checked_add` 防止加法溢位，一不合規立刻中止 |

---

## 動手做

- **難度**：入門
- **預估時間**：45 分鐘

現在我們用本地 Docker Compose（零雲端費用）把 NexusPay 的四個核心元件（Nginx + Node.js 22 + PostgreSQL 16 + Redis 7）跑起來。這個最小化環境故意留了幾個常見的部署與程式破口，請你站在攻擊者的角度，實際打打看它的網路連接埠與提領 API，把所有暴露在外的破口找出來。

### 步驟 1：建立本地最小化 NexusPay 拓樸

建一個空目錄 `nexuspay-ch01-lab/`，在裡面放三個檔案。首先是 `app.mjs`，裡面實作了我們剛剛討論過的提領 API，並保留了還沒修補的邊界漏洞：

```javascript
// app.mjs
import http from 'node:http';

const balances = new Map([
  ['tenant_a:acct_1', 10000], // $100.00 (整數分)
  ['tenant_b:acct_2', 10000],
]);

const server = http.createServer((req, res) => {
  if (req.method === 'GET' && req.url === '/health') {
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', service: 'nexuspay-gateway' }));
    return;
  }

  if (req.method === 'POST' && req.url?.startsWith('/v1/tenants/')) {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      const parts = req.url.split('/'); // ['', 'v1', 'tenants', tid, 'withdraw']
      const tid = parts[3];
      const { accountId, amount } = JSON.parse(body || '{}');
      const key = `${tid}:${accountId}`;

      // 破口：沒核對呼叫者的租戶身分，也沒檢查 amount > 0
      const current = balances.get(key) ?? 0;
      if (amount <= 10000 && current >= amount) {
        const next = current - amount;
        balances.set(key, next);
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: true, account: key, balance: next }));
      } else {
        res.writeHead(400, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ ok: false, error: 'insufficient_or_limit' }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end('not found');
});

server.keepAliveTimeout = 5000; // 5 s，對齊全書基準常數
server.listen(3000, '0.0.0.0');
```

接著建立 `nginx.conf`（只轉發 `/health` 與 `/v1/`）和 `docker-compose.yml`。注意看 `docker-compose.yml` 裡面的 `ports` 設定，這裡重現了許多團隊在寫開發或部署腳本時最常犯的錯——順手把內部服務直接綁到宿主機的 `0.0.0.0`：

```nginx
# nginx.conf
events {}
http {
  server {
    listen 8080;
    proxy_read_timeout 30s; # 對齊全書基準常數

    location /v1/ {
      proxy_pass http://app:3000;
    }
    location /health {
      proxy_pass http://app:3000;
    }
  }
}
```

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "127.0.0.1:8080:8080"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - app

  app:
    image: node:22-alpine
    working_dir: /srv
    volumes:
      - ./app.mjs:/srv/app.mjs:ro
    command: ["node", "/srv/app.mjs"]
    ports:
      - "0.0.0.0:3000:3000" # 危險設定：繞過 Nginx 直接暴露應用埠

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: nexus
      POSTGRES_PASSWORD: nexus_dev_password
      POSTGRES_DB: nexuspay
    ports:
      - "0.0.0.0:5432:5432" # 危險設定：未限定本機回環或私有網路

  redis:
    image: redis:7-alpine
    ports:
      - "0.0.0.0:6379:6379" # 危險設定：無密碼且對外暴露
```

### 步驟 2：啟動環境並實測邊界破口

把容器跑起來，依序從網路連接埠和 HTTP 提領請求兩個方向做測試：

```bash
docker compose up -d
# 1. 檢查哪些容器把連接埠直接綁到了 0.0.0.0
docker compose ps
# 2. 比較走 Nginx (8080) 與直接打 Node.js (3000) 的差異
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:3000/health
# 3. 測試外部能不能直接連上 Redis 與 PostgreSQL
nc -zv 127.0.0.1 6379
nc -zv 127.0.0.1 5432
# 4. 送出負數提領金額，觀察帳戶餘額變化
curl -s -X POST http://127.0.0.1:8080/v1/tenants/tenant_a/withdraw \
  -H 'content-type: application/json' \
  -d '{"accountId":"acct_1","amount":-5000}'
```

做完測試後，試著把這 4 個容器各自的暴露風險整理成一張 STRIDE 表格。收工前記得執行 `docker compose down -v` 把環境清乾淨。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地實驗跑通後，推薦到 **PortSwigger Web Security Academy** 免費靶場挑下面兩個主題練手，體驗一下在沒有原始碼的黑箱環境裡，怎麼靠外部反應摸出系統邊界：

1. **API testing**（API 偵察與隱藏端點）：很多人打靶場時只會乖乖點網頁上的按鈕。試著改掉這個習慣——看到 `/api/v1/users/123`，就順手測測看 `GET`、`POST`、`PUT`、`PATCH`、`DELETE` 會回什麼，找找看有沒有沒鎖到的 Swagger/OpenAPI 文件，並從報錯訊息反推後端還藏了哪些欄位。
2. **Information disclosure**（資訊洩漏）：遇到系統噴出錯誤堆疊、版本號或忘了刪的設定檔時，別只當成小疏失看過就算。那些資訊就是幫你畫出後端狀態機、看穿哪些邊界沒設防的最佳路標。

---

### 參考解答

#### 1. 實測結果與兩個致命破口

跑完 `docker compose ps` 與 `curl` 指令，你會馬上看到兩處大洞：

第一是**網路邊界完全被繞過**。`app`（`3000`）、`postgres`（`5432`）和 `redis`（`6379`）全都綁在 `0.0.0.0` 上。這代表攻擊者根本不需要經過 Nginx（`8080`），直接連 `3000` 埠就能打進 Node.js，你在 Nginx 寫的限流與路徑白名單形同虛設；更糟的是，如果這台機器有公網 IP，外面的人連密碼都不用就能直接連進 `6379` 把 Redis 裡的 Session 全偷走或改掉。

第二是**帳本資金守恆被一招打破**。第 4 步送出 `amount = -5000` 後，因為程式只檢查了 `-5000 <= 10000` 和 `10000 >= -5000`，畫面直接回傳：
`{"ok":true,"account":"tenant_a:acct_1","balance":15000}`
只發了一筆請求，帳戶餘額就從原本的 `10,000` 分（`$100.00`）變成了 `15,000` 分（`$150.00`）。而且因為程式直接拿 URL 上的 `tid` 去組 key，沒跟登入身分核對，任何人把網址改成 `/v1/tenants/tenant_b/withdraw` 就能隨便動用別家租戶的錢。

#### 2. NexusPay 基準環境威脅對照表

| 元件 | 實際暴露位址 | 被繞過／失守的邊界 | STRIDE 威脅 | 被打破的不變量 | 怎麼修 |
|---|---|---|---|---|---|
| `nginx:8080` | `127.0.0.1:8080` | TB-1（公網 ↔ 邊緣） | T / D（前後端請求切分差異、連線逾時 `30 s` vs `5 s`） | 請求邊界一致性與連線可用性 | 嚴格檢查 HTTP 定界標頭、對齊前後端 Keep-Alive 逾時並限制請求大小 |
| `app:3000` | `0.0.0.0:3000` | TB-1 旁路（直連後端） | S / T / E（跳過代理層；負數提領與跨租戶存取） | `Inv_2` 資金守恆與 `Inv_3` 租戶隔離 | 拔掉 `docker-compose.yml` 的對外 `ports`；在程式裡補上正整數與租戶權限檢查 |
| `postgres:5432` | `0.0.0.0:5432` | TB-2 旁路（直連資料庫） | I / T（整份多租戶帳本外洩或遭竄改） | 帳本機密性與完整性 | 拔掉對外 `ports` 映射、改用強密碼與內部 TLS，並在資料表啟用 RLS |
| `redis:6379` | `0.0.0.0:6379` | TB-2 旁路（直連無密碼快取） | S / T / I（直接讀寫 Session 與限流計數器） | 登入狀態與限流機制可靠性 | 拔掉對外 `ports` 映射，只留在 Docker 內網，並加上 Redis ACL 密碼 |

#### 3. 修補程式碼

先把 `docker-compose.yml` 裡面 `app`、`postgres`、`redis` 三個服務的 `ports` 區塊全部刪掉，只留 `nginx` 的 `127.0.0.1:8080:8080`，強迫所有外部流量只能走大門進來。

接著在 `app.mjs` 處理提領的地方，把金額的型別、下界與上界一次鎖緊：

```javascript
if (!Number.isSafeInteger(amount) || amount <= 0 || amount > 10000) {
  res.writeHead(400, { 'content-type': 'application/json' });
  res.end(JSON.stringify({ ok: false, error: 'invalid_amount' }));
  return;
}
```

---

## 自我檢核

- **難度**：入門
- **預估時間**：20 分鐘

先別急著往下滑看答案，試著用剛剛看過的四道邊界與不變量觀念，回答下面 4 個真實開發場景的問題：

1. **資料庫約束的盲區**：某團隊在 PostgreSQL 的帳戶表加上了 `CHECK (balance >= 0)`，還把交易隔離等級調到最嚴格的 `SERIALIZABLE`，接著拍胸脯保證：「我們的帳本總金額絕對不可能無故變多！」請舉出兩個例子，說明為什麼就算這兩個資料庫設定都正常運作，帳本裡的錢還是會被非法灌水？
2. **找出 Source、Sink 與失效的淨化順序**：有個下載報表的 API 是這樣寫的：(1) 先檢查 `req.query.file` 字串裡有沒有包含 `"../"`，有的話就拒絕；(2) 通過後呼叫 `decodeURIComponent()` 解碼；(3) 把解碼後的檔名拼到 `/var/nexus/reports/` 後面並打開檔案。請問這段流程的 Source、Sink 和 Sanitizer 各是誰？為什麼這道防線一戳就破？
3. **攻擊樹的成本比較**：現在針對 NexusPay 提領 API 有兩條攻擊路線：路線 X 必須在 `< 1 ms` 的時間窗內同時塞進 `20` 筆併發請求才能搶到競態漏洞；路線 Y 只要把網址上的 `:tid` 換成別家商戶的 ID，送出 `1` 筆普通請求就能把對方的錢領走。在攻擊樹上，駭客會優先挑哪一條？這對我們排修補順序有什麼啟發？
4. **抓出 Fail-Open 破口**：看看下面這段 TypeScript 寫的權限檢查中介層，它會在什麼時候放進不該放行的人？這對應到 OWASP Top 10:2025 的哪一個風險類別？

```typescript
async function requireMerchantOwner(req: Request, res: Response, next: NextFunction) {
  try {
    const allowed = await authClient.checkOwnership(req.user.id, req.params.acctId);
    if (!allowed) return res.status(403).json({ error: 'forbidden' });
  } catch (err) {
    logger.warn('auth service timeout, degrading gracefully', { err });
  }
  return next();
}
```

---

### 參考解答

1. **資料庫約束的盲區**：
   - 第一種是**負數提領**。`CHECK (balance >= 0)` 只管結果不能小於零，但如果提領 API 沒擋掉負數，傳入 `amount = -5000` 時，資料庫算完 `10000 - (-5000) = 15000` 覺得完全大於零，高興地存進去了，帳戶卻憑空多出 `5,000` 分。
   - 第二種是**重複入金**（缺少冪等性）。當外部金流商的儲值成功 Webhook 因為網路抖動重送了一次，而後端沒有檢查冪等鍵（Idempotency Key）就乖乖執行了兩次 `UPDATE accounts SET balance = balance + 10000`。對資料庫來說，這兩筆都是合法正當的交易，但帳本總額就這樣平白無故多了一倍。
2. **找出 Source、Sink 與失效的淨化順序**：
   - **Source** 是 `req.query.file`；**Sink** 是最後打開並讀取檔案的動作（如 `fs.readFile`）；中間那個有瑕疵的 **Sanitizer** 則是第一步的 `"../"` 黑名單檢查。
   - **為什麼守不住**：因為它**先檢查、後解碼**。攻擊者只要把 `../` 經過 URL 編碼變成 `%2e%2e%2f`（如果框架本身會先自動解一次，就送雙重編碼 `%252e%252e%252f`），第一步檢查時根本看不到字面上的 `"../"` 就放行了；結果第二步 `decodeURIComponent()` 一解開，真正的 `../` 才跑出來，直接讀光伺服器上的敏感檔案。正確做法是先解碼完畢，再用 `path.resolve` 與 `path.relative` 確認最終路徑真的落在 `/var/nexus/reports/` 目錄裡面，而且開檔時加上禁止跟隨符號連結的旗標（如 `O_NOFOLLOW`，詳見第 9 章）。
3. **攻擊樹的成本比較**：
   - 駭客當然選**路線 Y**。路線 Y 只要打 `1` 發請求、零時序要求就能穩定拿錢；路線 X 還得拼網路延遲、在毫秒內湊齊併發。
   - **修補啟發**：排資安修補優先順序時，不要被漏洞聽起來有多高深給騙了，永遠要先堵住攻擊樹上「前置條件最少、動手成本最低」的那條路（先把輸入正整數檢查跟租戶身分核對鎖好，再去調資料庫鎖定細節）。
4. **抓出 Fail-Open 破口**：
   - 只要 `authClient.checkOwnership` 因為網路瞬斷、連線池滿了或權限服務重啟而丟出例外，程式就會跳進 `catch` 區塊。這時它只印了一行 `logger.warn`，完全沒有 `return` 中斷請求，結果往下走到最後一行的 `return next()`，直接把沒驗證過權限的請求放進後面的業務邏輯裡。
   - 這是標準的 **Fail-Open** 漏洞，屬於 **OWASP Top 10:2025 的 A10**（Mishandling of Exceptional Conditions）。修法很明確：在 `catch` 區塊裡直接 `return res.status(503).json({ error: 'auth_unavailable' })` 拒絕請求，絕不往下呼叫 `next()`。

---

## 延伸閱讀

- **OWASP Top 10:2025**（https://owasp.org/Top10/）：重點對照 `A01 Broken Access Control` 與新獨立出來的 `A10 Mishandling of Exceptional Conditions`，看看真實世界裡有多少系統栽在例外處理與 Fail-Open 上。
- **OWASP API Security Top 10:2023**（https://owasp.org/API-Security/）：從排名第一的 API1（BOLA）一路看到 API10，當作檢查自家後端 API 邊界有沒有漏風的實戰清單。
- **MITRE CWE Top 25**（https://cwe.mitre.org/top25/）：統計最常出事的軟體弱點（如 CWE-79、CWE-89、CWE-862、CWE-787），可以拿來跟本章講的 Source-to-Sink 還有四類安全不變量互相對照。
- **Bruce Schneier, *Attack Trees***（Dr. Dobb's Journal, 1999）：提出攻擊樹模型的經典文章，示範怎麼把駭客的攻擊目標拆成 `AND`/`OR` 分支，並幫每條路標上成本與可行性。
- **Adam Shostack, *Threat Modeling: Designing for Security***（Wiley, 2014）：把資料流圖（DFD）跟 STRIDE 威脅建模帶進日常開發流程的必讀指南，特別推薦看他怎麼畫出跨信任邊界的那條線。
- **Alexis King, *"Parse, Don't Validate"***（2019）：用非常清楚的例子解釋為什麼不該在程式各處零散地做字串檢查，而應該在跨越邊界的那一刻，一次把外部輸入解析成結構明確的內部型別。
- **PortSwigger Web Security Academy**（https://portswigger.net/web-security）：做完本章本地實驗後，直接去刷 *API testing* 與 *Information disclosure* 兩個牌組，練習從外部 HTTP 回應反推後端邊界。
