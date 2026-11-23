# P4 Round-2 Adjudication & Surgical-Fix Log — `slice-r2-3` (Ch11–Ch15)

- **Reviewer Panel**: `codex:gpt-6.2-sol:medium` (`books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/ch11..ch15.json`)
- **Adjudicator**: `p4-final-1` (`gemini-3.8-flash-high`)
- **Scope**:
  - `ch11-ssrf-parsers-and-cache.md`
  - `ch12-race-conditions-and-logic.md`
  - `ch13-deserialization-and-nodejs-runtime.md`
  - `ch14-waf-and-defense-bypass.md`
  - `ch15-applied-crypto-flaws.md`
- **Verification Summary**:
  - `lint_book.py`: `Chapters: 37; PASS` (0 errors, 0 warnings)
  - `check_diagrams.py`: `{"passed": true, "findings": []}` (0 syntax errors, 0 misalignments)
  - Base-numbers compliance: 100% strictly aligned with `_meta/running-examples.md` (zero constants altered).
  - Structural invariants: All 6 verbatim H2 headings preserved, first H3 `### 攻擊者目標與實質影響` preserved, difficulty/time/`### 參考解答` in both `## 動手做` and `## 自我檢核` verified.
  - Prose quality: Zero simplified characters, zero banned vocabulary (zh-TW), zero Pitfall #13 bold-flanking syntax defects (`**「...」**` / `**（...）**`).

---

## 1. `ch11-ssrf-parsers-and-cache.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| 嚴格依循 RFC 3986 解析器不把 `\` 視為分隔符因此將其當作 userinfo 放行 | `incorrect` | **Accepted (Grammar Precision)** | 修正第 38 行：嚴格依循 RFC 3986 語法驗證的解析器會因 userinfo 出現未編碼反斜線直接拒絕；僅依 RFC 3986 分隔符寬鬆切分欄位而未驗證字元集合法性的寬鬆解析器（如特定版本未加字元檢查的 `urllib.parse.urlsplit` 或正則）才會將 `127.0.0.1:8080\` 當作 userinfo、將後端主機回傳並放行。 |
| 只要間隔超過最小 TTL 第二次查詢同樣會拿到新紀錄 | `incorrect` | **Accepted (DNS Resolution Precision)** | 修正第 105 行與第 501 行自我檢核解答：明列第二次查詢取得新紀錄的前提為間隔超過相關解析快取的有效存活時間、客戶端未重用既有連線而重新發起 DNS 解析，且權威 DNS 確已切換回應。 |
| Webhook 回傳 202 Accepted 即構成 Blind SSRF | `incorrect` | **Accepted (Security Model Precision)** | 修正第 109 行：明確界定「當呼叫者能誘導伺服器對非預期目標發起未獲授權的請求，且無法直接取得目標回應內容時」才構成 Blind SSRF，避免混淆回應狀態與漏洞成因。 |
| 快取層忽略 GET body，某些框架將其合併進 req.params 優先採用 | `incorrect` | **Accepted (Framework & Cache Key Precision)** | 修正第 143 行：精確說明「共享快取層在計算 `GET` 請求的有效快取鍵時通常不納入請求主體，但若後端應用程式或中介軟體實際讀取了 `GET` 主體並用它產生可共享回應，且快取鍵未涵蓋該主體，就構成 Unkeyed Input」。 |
| 惡意 HTML 會被寫入公開快取鍵在 60 秒內感染每一位使用者 | `incorrect` | **Accepted (Cache Policy & Scope Precision)** | 修正第 139 行：補充「且源站產生的惡意 HTML 回應符合該節點的共享快取寫入條件而被存入公開快取鍵中，在該快取項目的有效新鮮期內，後續命中同一快取鍵與變體的請求都會收到這份受污染的回應（實質執行影響仍取決於瀏覽器執行脈絡與 CSP 等防護）」。 |
| ASCII 示意圖標示「CDN 依靜態快取規則寫入共享快取 (例如忽略源站禁存標頭且符合快取條件)」 | `incorrect` | **Accepted (Diagram Text Precision)** | 修正第 192 行圖解文字為「CDN 依靜態快取規則判定符合條件並寫入共享快取（受代理組態與快取資格規範）」。 |
| 任務 1A 方案一參考解答與題目驗證器匹配性 | `incorrect` | **Accepted (Vulnerability Path Clarity)** | 修正第 328 行：明確解釋 `validator.js` 中 `0177.0.0.1` 因不以 `'127.'` 開頭且符合純數字點號正則 `/^[0-9.]+$/` 而直接跳過 `dns.lookup()` 判定並放行，隨後 `fetch()`（WHATWG）自動將八進位正規化為 `127.0.0.1:9000`，精確送達目標端點。 |
| 任務 1A 補充對照（反斜線與 @ 混淆）作為參考解答 | `incorrect` | **Accepted (Scope Distinction)** | 修正第 330 行：將補充對照明確標註為「展示跨元件解析器切分權威部分的差異」，並指出 WHATWG fetch 會將路徑改寫為 `/@allowed.merchant.example/internal/metrics`，適用於後端忽略前置路徑段或以萬用字元匹配的場景。 |
| 任務 1B 安全驗證「解析所有 A/AAAA 記錄並全數檢查」 | `incorrect` | **Accepted (API Semantic Precision)** | 修正第 396 行註解：將「解析所有 A/AAAA 記錄」修正為「透過系統名稱解析介面取得此次查詢的全部候選位址並全數檢查」，並於第 407 行註明 lookup 回呼在單次請求連線建立時提供釘選保護。 |
| 關鍵 `imprecise` 補強 | `imprecise` | **Polished / Accepted** | 修正第 7 行「驗證與執行元件常採用不同解析器或正規化策略」；第 33 行精確說明 WHATWG 修剪首尾 C0/空格並移除字串中所有 Tab/LF/CR；第 47 行嚴格區分 IPv6 回環 `::1`、未指定 `::` 與 IPv4-mapped IPv6 之位址語意；第 223 行補充 `Cache-Control: no-store, private` 配合共享快取遵守源站策略。其餘閉卷書目年份標記予以維持。 |

---

## 2. `ch12-race-conditions-and-logic.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| 單封包攻擊將網路抖動壓縮至 `< 1 ms`，直接打穿毫秒級應用層鎖 | `incorrect` | **Accepted (Concurrency Model Precision)** | 修正第 9 行：明確指出在本書模型假設下，單封包攻擊將伺服器端到達抖動壓縮到 `< 1 ms`，打穿的是「未獲原子同步或缺乏適當臨界區保護的毫秒級檢查與外部 API 呼叫 TOCTOU 視窗」；強調正確涵蓋臨界區的互斥鎖仍會序列化處理操作。 |
| 骨架腳本 `[等待 100 ms 確保前段全部到達伺服器核心]` | `incorrect` | **Accepted (Timing Terminology Fix)** | 修正第 43 行與第 273 行：標示為「示意等待約 100 ms 客戶端排程，讓前段訊框先行送出至伺服器端緩衝」，避免將示意客戶端計時誤稱為保證交付。 |
| 以受影響列數 `rowCount === 1` 作為扣款成功的唯一憑證 | `incorrect` | **Accepted (Transaction Integrity Precision)** | 修正第 146 行防禦表格與第 316 行自我檢核解答：精確表述為「以 `rowCount === 1` 表示命中扣款條件，持久扣款以交易成功提交及持久化冪等記錄為準，外部出金另以出金狀態持久化確認與對帳」。 |
| 原生記憶體中的 Data Race 屬於執行緒層級的記憶體損毀原語 | `incorrect` | **Accepted (UB Terminology Precision)** | 修正第 11 行：表述為「多執行緒 C/Rust 原生記憶體中的 Data Race（缺乏適當同步的衝突記憶體存取，在底層語言中屬於未定義行為，可能造成記憶體損毀或型別混淆）」。 |
| 關鍵 `imprecise` 補強 | `imprecise` | **Polished / Accepted** | 修正第 5 行：明述 PostgreSQL `READ COMMITTED` 下每條普通 `SELECT` 可見該敘述開始前已提交資料與本交易先前的寫入；第 33 行明述路由業務邏輯以完整主體為執行前提時才等待接收完成；第 52 行交代 Nginx `30 s` 與 Node.js `5 s` 逾時與請求重疊程度取決於代理緩衝與連線池；第 78 行精確說明 `REPEATABLE READ` 下偵測到同列更新衝突觸發 `40001`；第 92 行與第 286 行標明 Worked Example 時間軸與交易順序為示意模型。 |

---

## 3. `ch13-deserialization-and-nodejs-runtime.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| 回溯型 NFA 遇到量詞或分支時預設採用貪婪匹配 | `incorrect` | **Accepted (Automata Precision)** | 修正第 149 行：分別說明量詞的重複次數優先順序（貪婪量詞優先嘗試較多次重複）與交替分支的宣告順序（由左至右依序嘗試）。 |
| 巢狀量詞或重疊分支在尾端出現無法匹配字元時引擎被迫窮舉所有組合 | `incorrect` | **Accepted (Backtracking Model Precision)** | 修正第 149 行：在逐路徑回溯模型中，當模式存在可產生指數多種切分方式的具歧義巢狀量詞或重疊交替分支時，只要輸入尾端條件使每條候選切分路徑均匹配失敗（如無法匹配的字元 `!`），未做記憶化的回溯引擎才會被迫逐一探索所有組合，時間退化為 `O(2^n)`。 |
| 單次同步匹配阻塞達 5.37 s 超過 Node.js `keepAliveTimeout = 5 s` 使其他保活連線逾時中斷 | `incorrect` | **Accepted (Event Loop Lifecycle Precision)** | 修正第 174 行：精確說明「單次同步匹配阻塞估算達 5.37 s，期間同一 Worker 的 Event Loop 完全無法處理任何其他 I/O 回呼或計時器；若有連線正處於 Node.js `keepAliveTimeout = 5 s` 的閒置保活計時視窗，此同步阻塞將延後該計時器的處理，連線是否中斷或逾時取決於連線狀態、計時起點與事件迴圈恢復後的處置」。 |
| 一個同步的 `regex.test(input)` 只要阻塞超過 5 s 整個 Worker 行程瞬間失聯 | `incorrect` | **Accepted (Threshold & Impact Precision)** | 修正第 179 行：精確指出「同步匹配在執行期間會完全佔用該 Worker 的事件迴圈並延後所有非同步回呼；在此期間該 Worker 無法推進其他請求與健康檢查，若阻塞持續至觸發用戶端逾時或探針門檻，便可能導致斷線或觸發容器重啟」。 |
| 執行任何正則前檢查字元數與位元組長度 `input.length <= MAX_LEN && Buffer.byteLength(input, 'utf8') <= MAX_LEN` | `incorrect` | **Accepted (Encoding Unit Precision)** | 修正第 208 行：明確區分 `input.length` 檢查的是 JavaScript 字串的 UTF-16 碼元數（code units），而 `Buffer.byteLength(input, 'utf8')` 檢查的是 UTF-8 位元組長度，嚴格限制 UTF-8 上限不超過 128 位元組。 |
| 關鍵 `imprecise` 補強 | `imprecise` | **Polished / Accepted** | 修正第 175 行：明述在每項完成前都不輸出回應的串行簡化模型中，第 6 個請求於 26.85 s 開始服務、32.2 s 完成，可能觸發 Nginx 30 s 逾時；第 340 行將 PoC 檢查標註為「檢查檔案是否於本輪建立並印出子行程 PID，佐證 RCE 成立」。 |

---

## 4. `ch14-waf-and-defense-bypass.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| 防禦對抗是所有 Web 與 API 漏洞進入實戰利用的「前置放大器」 | `incorrect` | **Accepted (Scope Precision)** | 修正第 23 行：精確限定為「當目標匯點前方設有會攔截攻擊請求的 WAF 或限流器時，突破該道邊緣控制便成為該攻擊路徑的前置條件」。 |
| HPP 繞過 blacklists 對 ORM 與 String() 的影響 | `incorrect` | **Accepted (Type Coercion & Branch Precision)** | 修正第 428 行自我檢核解答：明確區分兩分支——在 JavaScript 中陣列與字串嚴格比較 `["pending", "approved"] === "approved"` 回傳 `false` 繞過黑名單；傳入將陣列展開為集合條件的下游 ORM 時產生 `IN ('pending', 'approved')` 造成越權；若下游以 `String(status)` 處理則轉為逗號字串 `"pending,approved"`，其結果取決於資料庫與查詢語意。 |
| WAF 預設只按 UTF-8/ASCII 掃描且未拒絕非 UTF-8 charset 即看不出關鍵字放行 | `incorrect` | **Accepted (Inspection Model Precision)** | 修正第 141 行：表述為「編碼不一致可能導致特定逐位元組關鍵字規則漏判；若該請求未命中其他規則或因解析容錯而放行，後端解碼器便會將其轉回標準字串交給業務邏輯」。 |
| 每一層代理在轉發時會把上一跳來源 IP 附加到 XFF 標頭尾端 | `incorrect` | **Accepted (Proxy Behavior Precision)** | 修正第 153 行：表述為「在多層代理拓樸中，每層代理可能依設定附加、覆寫或移除 XFF；若最外層代理未覆寫外部傳入的標頭，後續代理又採取附加（append）上一跳來源 IP 的策略，送達應用程式的位址鏈就會包含未經信任的客戶端偽造值」。 |
| 限流鍵須先對 pathname 轉小寫、合併重複斜線、剝除尾斜線與 `;` 矩陣參數 | `incorrect` | **Accepted (Router Semantics Precision)** | 修正第 206 行：表述為「限流鍵應直接使用已由路由器匹配完成的路由識別值（例如 Express 的 `req.route.path`），或直接將限流中介軟體綁定在目標路由處理器上；若需在全域中介層自行依路徑字串計算鍵值，必須審慎評估是否改寫 URI 及其對路由行為的影響」。 |
| 參考修補程式碼強制僅接受 UTF-8 `application/json` | `incorrect` | **Accepted (Parser Completeness Fix)** | 修正第 330–339 行：透過嚴格拆解 `Content-Type` 媒體類型與參數，精確比對 `mediaType === "application/json"` 與 `charset=utf-8`，排除非預期格式。 |
| 參考修補程式碼對 pathname 做正規化並保留原始 query string | `incorrect` | **Accepted (URI Split Fix)** | 修正第 347–349 行：以 `req.url.indexOf("?")` 只於第一個問號處切分，原樣保留問號後續的所有 query string（含內部任何問號）。 |
| 參考修補程式碼落實了拒絕 JSON 重複鍵的防禦 | `incorrect` | **Accepted (Pre-Parse Inspection Fix)** | 修正第 343 行：在 `express.json` 中配置 `verify` 回呼，在 `JSON.parse` 執行前直接掃描原始位元組字串中的鍵名，一旦發現重複鍵立即拋出例外阻斷，防止 ECMA-262 末值覆寫分歧。 |
| 參考解答之 OTP 限流器實作 | `incorrect` | **Accepted (Lab Scope Precision)** | 修正第 374 行註解：明確標註範例為「教學環境單行程 Map 示意；生產環境應以 Redis 實作具 TTL、滑動視窗與狀態機鎖定之分散式計數器」。 |
| 測試腳本確認修補全數被阻斷 | `incorrect` | **Accepted (Assertion & Status Precision)** | 修正第 285–306 行：在 `verify_ch14.py` 中明確區分業務失敗狀態碼（前 5 次合格請求回傳 `401`）與限流狀態碼（第 6 次回傳 `429`），並標註修補後各項斷言（超長請求 `413`、Schema 阻斷 `400`、限流 `429`）。 |

---

## 5. `ch15-applied-crypto-flaws.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| 唯一可能產生歧義的情況是解密後的倒數第 2 個位元組恰好等於 0x02 | `incorrect` | **Accepted (Padding Length Generalization)** | 修正第 75 行、第 382 行與第 558 行：精確說明歧義可能來自任一合法的 2 至 16 位元組填充；固定前 15 個位元組後，倒數第二個位元組至多指定一種可能的較長填充長度，因此至多出現一個額外合法候選。翻轉倒數第二個位元組可破壞任何較長填充並保留 `0x01`。 |
| 試探值會湊成合法的 0x02 0x02 填充而通過檢查 | `incorrect` | **Accepted (Suffix Matching Precision)** | 修正第 75 行與第 558 行：明確指出 `0x02` 候選只有在末兩個位元組皆為 `0x02` 時才通過；較長填充要求整段後綴等於對應長度。 |
| 精確離散期望值為 `16 × 128.5 = 2,056` 次，含確認請求為 `2,057` 次 | `incorrect` | **Accepted (Probabilistic Discrete Model)** | 修正第 79 行、第 542 行與第 558 行：主要試探的精確離散期望值為 `16 × 128.5 = 2,056` 次；在中間狀態位元組獨立均勻假設下，每區塊另有 1 或 2 次末位元組確認請求，總期望約為 `2,057.002` 次。 |
| 同金鑰下重用 96-bit Nonce 立即洩漏明文差值與 GHASH 驗證金鑰 H | `incorrect` | **Accepted (Base-Number & Mathematical Harmony)** | 修正第 31 行與第 140–141 行：嚴格保留全書基準表常數描述，同時精確補齊數學推導——重用會立即暴露重疊區段明文 XOR 並破壞認證安全；標籤差值消去遮罩後得到對 `H` 的多項式方程，單區塊等長無 AAD 時可唯一直接解出，多區塊時解出至多 `d` 個候選根，只有在方程可唯一決定或有驗證端 Tag Oracle 排除其餘候選時，才能確認唯一的 `H`。 |
| 搭配第三筆重用紀錄或驗證端 Tag Oracle 即可從候選根中篩選出唯一正確的 H | `incorrect` | **Accepted (Set Reduction Condition)** | 修正第 187 行：精確表述為「若再配合同一金鑰下提供額外獨立約束的重用紀錄，或能對剩餘候選根產生可區分驗證結果的 Tag Oracle，即可在共同候選根收斂為唯一值時確認正確的 `H`」。 |
| V8 `xorshift128+` 狀態僅 128 bits，3–5 筆輸出即可完全反推 | `incorrect` | **Accepted (Linear Algebra Rank Precision)** | 修正第 234 行與第 257 行表格：明確指出前 3 筆輸出的約束秩至多為 117（未達 128），必須連續觀察 4 到 5 個完整輸出才能使位元向量約束在 `GF(2)` 上達到滿秩 `128` 並唯一解出內部狀態。 |
| 啟動時檢查環境變數存在性與熵長度（拒絕預設字串） | `incorrect` | **Accepted (Entropy Assurance Precision)** | 修正第 258 行防禦表格：表述為「啟動時檢查環境變數存在性、格式與位元組長度（拒絕已知預設字串，並由 CSPRNG/KMS 保障金鑰真實熵）」。 |

---

## 結論與交接狀態

- **負責 Slice**：`slice-r2-3`（Ch11–Ch15 全部完工）。
- **審查缺陷修復率**：100%（所有 genuine `incorrect` 缺陷與 substantive `imprecise` 精度問題全數完成外科手術級修復）。
- **工具鏈狀態**：
  - `lint_book.py`: `Chapters: 37; PASS` (0 errors, 0 warnings)
  - `check_diagrams.py`: `{"passed": true, "findings": []}`
