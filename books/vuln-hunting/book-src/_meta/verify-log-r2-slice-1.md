# P4 Round-2 跨模型審查裁決與外科修補日誌（Slice 1: Ch01–Ch05）

- **審查面板**：`codex:gpt-6.2-sol:medium`（Round-2 快取：`books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/`）
- **負責範圍**：`ch01-trust-boundaries.md`、`ch02-recon-and-audit-workflow.md`、`ch03-http-smuggling.md`、`ch04-authentication-and-sessions.md`、`ch05-enterprise-sso-and-mfa.md`
- **基準核對**：全數對齊 `_meta/running-examples.md` 全書基準數字表，零變更基準常數。

---

## 1. `ch01-trust-boundaries.md`

### `verdict == "incorrect"` 裁決與修補（6 項全數修正）

1. **ACID 交易保證範圍與已宣告約束的表述**
   - **審查意見**：原句將整體 ACID 交易保證等同於已宣告約束；即使某欄未設 `CHECK`，交易寫入仍受原子性與隔離級別規範。
   - **裁決與修補**：成立。修訂第 16 行，明確區分「納入資料庫交易管理的資料操作（受原子性與隔離性保護）」與「特定業務一致性僅涵蓋已由交易邏輯或宣告約束強制檢查的資料表狀態」，以及未納入同一交易的外部副作用。
2. **資料庫授權預設假設的表述**
   - **審查意見**：資料庫本身可依自身角色、權限與 PostgreSQL RLS 執行授權判斷，問題在於應用層共用連線池角色時未將終端商戶身分與租戶脈絡綁定至資料庫操作。
   - **裁決與修補**：成立。修訂第 16 行，精確表述為「當應用層以共用連線池角色存取資料庫且未啟用並綁定列級安全（RLS）脈絡時，資料庫本身無法區分不同終端商戶的應用層授權」。
3. **跨信任邊界接收端重新解析與單一權威解析原則之協調**
   - **審查意見**：若接收端收到的是已具完整性保護且來源可驗證的結構化表示，可直接依該表示檢查本層授權與業務約束，無須對原始字串重複解析（避免製造新的解析器分歧）。
   - **裁決與修補**：成立。修訂第 55 行，明確區分「未經驗證的原始輸入須在邊界入口完成權威解析」與「已具完整性保護的結構化表示仍須強制檢查本層的授權與業務約束」。
4. **FFI 記憶體安全不變量 `Inv_4` 的無溢位邊界不等式**
   - **審查意見**：僅寫 `0 <= offset + write_len <= alloc_size` 無法排除負偏移或固定寬度整數溢位折返。
   - **裁決與修補**：成立。修訂第 154 行 `Inv_4` 為「FFI 目的緩衝區須有效、存活且可寫，並在無溢位算術下滿足 `0 <= offset <= alloc_size` 且 `0 <= write_len <= alloc_size - offset`」。
5. **攻擊樹根目標可達性與「整體安全性等於零」修辭**
   - **審查意見**：狀態機模型未將整體安全性定義為純量數值 0，應表述為提領安全不變量仍可被擊穿、攻擊樹根目標仍處於可達狀態。
   - **裁決與修補**：成立。修訂第 213 行表述為「該提領安全不變量依然會被輕易擊穿，攻擊樹的根目標仍處於可達狀態」。
6. **Nginx `30 s` 與 Node.js `5 s` 逾時參數與請求切分分歧的因果區分**
   - **審查意見**：`proxy_read_timeout = 30 s` 與 `keepAliveTimeout = 5 s` 分別對應不同計時事件，請求定界分歧源於 HTTP 標頭解析差異與持久連線複用。
   - **裁決與修補**：成立。修訂第 264 行跨層防禦表與第 429 行威脅矩陣，將定界標頭嚴格校驗與上游 Keep-Alive／逾時生命週期協調分開精確表述。

### 關鍵 `imprecise` 補強

- **功能缺陷與安全漏洞的狀態空間區分**（第 42 行）：補充「在所有可行執行軌跡上的每個狀態均維持於安全狀態子集 `I` 內」與功能規格偏離之對照。
- **Worked Example 狀態轉移表快照語意**（第 163 行）：註明 `t_2..t_4` 為各筆出金與扣款皆完成後之狀態快照。
- **路徑正規化與符號連結 TOCTOU**（第 229、481 行）：區分字面路徑檢查與檔案系統 TOCTOU，並將 `path.relative` 包含關係檢查精確化為完整路徑元件比對（`rel !== '..' && !rel.startsWith('..' + path.sep) && !path.isAbsolute(rel)`）與 `O_NOFOLLOW` 防護。
- 其餘針對閉卷審查環境未附外部書籍／PortSwigger 目錄全文之 `imprecise` 標記（已由 `_meta/landscape-2026-11.md` 驗證），予以維持。

---

## 2. `ch02-recon-and-audit-workflow.md`

### `verdict == "incorrect"` 裁決與修補（8 項全數修正）

1. **Node.js 與 `curl` 的 CA 信任來源表述**
   - **審查意見**：應按官方預設建置（內建 Mozilla CA 束、未開啟系統 CA 旗標）與 `curl` 的 TLS 後端條件精確描述，並在自我檢核第 1 題明示 CLI 已配置代理 Dispatcher 轉發流量。
   - **裁決與修補**：成立。修訂第 44 行與第 353 行自我檢核題幹，明確交代預設建置條件與代理轉發配置前提。
2. **Certificate Pinning 與雙向 mTLS 的失敗邊界區分**
   - **審查意見**：Pinning 是下游會話 A 客戶端拒收代理葉憑證；mTLS 是上游會話 B 伺服器要求代理出示客戶端憑證並以對應私鑰完成持有證明（私鑰本身不傳送給對端）。
   - **裁決與修補**：成立。修訂第 198 行，將下游會話 A 的 Certificate Pinning 與上游會話 B 的 mTLS 客戶端憑證持有證明分別精確說明。
3. **Soft-404 導致「100% 誤報」的比例表述**
   - **審查意見**：命中清單中的誤報率為 `F / (T + F)`，僅在 `T = 0` 時為 100%；實際現象是將字典中所有未知路徑全數誤判為命中。
   - **裁決與修補**：成立。修訂第 73 行，改為「把字典裡所有未知路徑全數誤判為有效命中，產出海量誤報並淹沒真正的端點」。
4. **Soft-404 基線向量的動態標頭剝除與交叉驗證**
   - **審查意見**：`X-Request-Id` 每次請求皆變動，不能直接以原始值要求相等；且符合基線的回應應標為疑似軟 404 並搭配方法與 `Accept` 切換交叉確認。
   - **裁決與修補**：成立。修訂第 75 行，明確寫出實測主體長度、剝除動態 `X-Request-Id`／nonce 後之結構特徵，以及搭配 HTTP 方法與 `Accept` 標頭切換交叉確認。
5. **步驟二 Soft-404 腳本與內文的方法／標頭一致性**
   - **審查意見**：內文提及測試 `OPTIONS` 與 `POST`，但腳本迴圈僅有 `GET` 與 `POST`，且基線請求未帶與候選請求相同的 `Content-Type` 標頭。
   - **裁決與修補**：成立。修訂第 273–293 行，在基線迴圈補齊一致的 `-H "Content-Type: application/json"`，並將候選探測方法迴圈擴充為 `GET POST OPTIONS`，與內文完全一致。
6. **`legacy-export` 的 APS 評分級距映射**
   - **審查意見**：`Complexity=3` 時得分 `81..108` 皆 `≥ 72`，兩者均屬 **P0**；僅在 `Complexity=2` 時得分 `54..72` 才分別落入 **P1** 至 **P0**。
   - **裁決與修補**：成立。修訂第 342 行，將 `81..108`（均為 **P0**）與 `54..72`（**P1** 至 **P0**）分開明確標示，並對齊 2.4 節 `Sink_Impact` 定義。
7. **`routes-health` 的跨越信任邊界數計算**
   - **審查意見**：依 2.4 節定義，客戶端進入 Nginx 計第 1 道邊界，Nginx 轉發至 NestJS Controller 計第 2 道邊界，故 `Boundary_Crossings = 2`，得分應為 `4 × 2 × 1 × 1 = 8`。
   - **裁決與修補**：成立。修訂第 342 行，將 `routes-health` 的 `Boundary` 由 `1` 修正為 `2`，總分修正為 `8`。
8. **低頻冷路徑「放大為 100% 確定性突破口」的表述與延伸閱讀 RFC 節號**
   - **審查意見**：APS 為優先序分數而非 100% 成功率；此外 `CONNECT` 位於 RFC 9110 §9.3.6，而 HTTP/1.1 連線持久性位於 RFC 9112 第 9 節（§9.3）而非第 6 節，ALPN 則定義於 RFC 7301。
   - **裁決與修補**：成立。修訂第 376 行冷路徑風險表述，並修正第 382–383 行 RFC 9110 §9.3.6、RFC 9112 第 6 節與第 9 節（§9.3），以及補入 RFC 7301（TLS ALPN）。

---

## 3. `ch03-http-smuggling.md`

### `verdict == "incorrect"` 裁決與修補（3 項全數修正）

1. **TCP 位元組流「永久錯位」的表述**
   - **審查意見**：解析分歧造成的是該持久連線上前後端對後續位元組訊息歸屬失步；一旦後續位元組被消費完畢或因語法錯誤關閉連線，該連線即終止或改變狀態，並非永久錯位。
   - **裁決與修補**：成立。修訂第 13 行，改為「導致該條持久 TCP 連線上前後端對後續位元組的訊息歸屬失去同步，將攻擊者構造的請求前綴嫁接到同一連線上緊隨其後的無辜使用者請求上（直到該連線因解析錯誤關閉或完成後續位元組消費為止）」。
2. **chunked 格式「區塊資料後方必須跟著 `\r\n0\r\n\r\n`」的通用性表述**
   - **審查意見**：chunked 訊息可包含多個非零資料區塊及可選尾端欄位；只有在單一資料區塊且無尾端欄位時，該資料區塊後方才會直接緊接 `\r\n0\r\n\r\n`。
   - **裁決與修補**：成立。修訂第 113 行，明確限定為「在單一資料區塊且無尾端欄位的 chunked 訊息中，區塊資料後方必須跟著該區塊結尾 `\r\n` 與終止區塊 `0\r\n\r\n`（共 `\r\n0\r\n\r\n`）」。
3. **HTTP/2 malformed 請求的錯誤處置層級（串流級 vs 連線級）**
   - **審查意見**：HTTP/2 為多工連線，RFC 9113 將欄位或 `content-length` 違規定義為串流級錯誤（以該串流的 `PROTOCOL_ERROR` 或 `400` 拒絕），無須關閉承載其他合法串流的整條 HTTP/2 連線；HTTP/1.1 則回 `400 Bad Request` 並關閉該 H1.1 連線。
   - **裁決與修補**：成立。修訂第 275 行縱深防禦表，將 HTTP/1.1（回 `400` 並關閉連線）與 HTTP/2（以該串流的 `PROTOCOL_ERROR` 或 `400` 拒絕且絕不降級轉發）分協定精確列明。

### 關鍵 `imprecise` 補強

- **自我檢核第 3 題 (a) 的 `DATA` frame 長度語意**（第 520 行）：明確註明為「無填補（unpadded）`DATA` frame 實際資料總長為 `30` bytes」，排除 Padding 位元組造成的歧義。

---

## 4. `ch04-authentication-and-sessions.md`

### `verdict == "incorrect"` 裁決與修補（3 項全數修正）

1. **演算法混淆根因小結語意反轉**
   - **審查意見**：原句「把用於驗簽的公鑰資料與演算法信任策略綁在一起」在字面上描述的是正確防禦（綁定金鑰與演算法策略），漏寫了「容許未經驗證的 Token Header 動態指定不相容的 `HS256` 並把公鑰當成對稱密鑰代入」這個漏洞前提。
   - **裁決與修補**：成立。修訂第 128 行，精確寫出「只要驗證端未將金鑰型別與允許的演算法白名單鎖死在伺服器端設定，反而容許未經驗證的 Token Header 動態指定 `HS256` 並把公開的 RSA 公鑰位元組當成對稱密鑰代入……」。
2. **PEM 金鑰檔尾換行（`451` vs `450` bytes）與 `LF` vs `CRLF`（`451` vs `460` bytes）的位元組差值**
   - **審查意見**：`451` 與 `450` bytes 的 1-byte 差異來自「檔尾是否保留最後一個 `\n`」；若整份 9 行 PEM 由 `LF` 改為 `CRLF`，9 處換行會多出 9 bytes（`451 + 9 = 460` bytes）。原句將兩者混寫於同一括號。
   - **裁決與修補**：成立。修訂第 74 行，將「檔尾是否保留換行字元 `\n`（`451` vs `450` bytes）」與「行尾換行採用 `LF` 還是 `CRLF`（9 處換行共差 9 bytes，即 `451` vs `460` bytes）」分開精確列出。
3. **Refresh Token 輪換在資料庫交易中的併發行為與家族撤銷提交（Commit before 401）**
   - **審查意見**：在 `SERIALIZABLE` 隔離下，併發更新同一列會對敗方拋出序列化失敗而非回傳 0 列讀取 `used = true`；而在 `READ COMMITTED` 的原子條件更新下，列鎖會讓敗方等待首筆提交後重評 `WHERE used = false` 並取得 0 列。此外，觸發家族撤銷（`SET revoked = true WHERE family_id = $1`）後必須先 `COMMIT` 提交交易，才能回傳 `401`，否則例外回滾會使撤銷失效。
   - **裁決與修補**：成立。修訂第 236 行與第 276–284 行參考解答，明確採用 `READ COMMITTED` 列鎖保護之原子條件更新，並強調家族撤銷 `UPDATE` 必須先行 `COMMIT` 提交後再回傳 `401`。

### 關鍵 `imprecise` 補強

- **`exp` 與 `iat` 型別與正時間差檢查**（第 218–226 行）：在程式碼範例中明確檢查 `typeof payload.exp === 'number'`、`typeof payload.iat === 'number'`、`payload.exp > payload.iat` 且 `payload.exp - payload.iat <= 900`。
- **RSA 公鑰取得來源描述**（第 74 行）：將「OIDC Discovery 端點」精確化為「OIDC Discovery 端點指向的 JWKS 位址或公開金鑰端點」。

---

## 5. `ch05-enterprise-sso-and-mfa.md`

### `verdict == "incorrect"` 裁決與修補（2 項算術與索引全數修正）

1. **Worked Example 中 Exclusive C14N 單行 `<saml:Assertion>` 的位元組長度計算**
   - **審查意見**：起始標籤 `<saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion" ID="_assert_legit_01" IssueInstant="2026-11-21T02:00:00Z" Version="2.0">` 實測為 `139` bytes（原寫 `140`），加上 `<saml:Issuer>`（`51` bytes）、`<saml:Subject>` 子樹（`78` bytes）與 `</saml:Assertion>`（`17` bytes），總長為 `139 + 51 + 78 + 17 = 285` bytes（原寫 `286` bytes）。
   - **裁決與修補**：成立。逐字元核對 ASCII 長度確為 `139 + 51 + 78 + 17 = 285` bytes，修訂第 128 行與第 130 行。
2. **Worked Example 中 DOM 前序走訪（Pre-order DFS）的元素索引**
   - **審查意見**：從 `<samlp:Response>`（元素 0）起算，合法 `<saml:Assertion ID="_assert_legit_01">` 為元素 6，`<saml:Issuer>` 為元素 7，`<ds:Signature>` 子樹共 11 個元素（元素 8..18），其後的 `<saml:Subject>` 為元素 19，第二個 `<saml:NameID>` 為元素 20（`NodeList[1]`），原寫「元素 17」漏計了 `<ds:Transforms>` 下的子元素數。
   - **裁決與修補**：成立。修訂第 143–145 行，明確標出元素 7..18 之分佈，並將 `<saml:Subject>` 與第二個 `<saml:NameID>` 修正為元素 19 與元素 20（`NodeList[1]`）。

### 關鍵 `imprecise` 補強

- **NexusPay SAML SP Entity ID 與 `expectedAudience` 設定說明**（第 259 行）：於程式碼註解標明 NexusPay 將 SP Entity ID 與 ACS URL 設為同一 URI，分別核對 `Audience` 與 `Destination`/`Recipient`。
- **WebAuthn 獨立挑戰流程鍵與 MFA Redis Lua 原子消費**（第 292–293 行）：將 Redis 挑戰鍵改為 `webauthn:chal:<challengeId>` 並綁定 `{ challenge, userId, sessionId, operation }` 避免同會話並行覆寫；將 MFA 驗證額度遞增與挑戰／備援碼單次消費整合為 Redis Lua 單一原子步驟。

---

## 6. 工具鏈驗證結果

- `python3 tools/md-reader/lint_book.py books/vuln-hunting/book-src --lang zh-TW --config books/vuln-hunting/book-src/_meta/lint.config.json`：Ch01–Ch05 **0 errors, 0 warnings**。
- `python3 tools/md-reader/check_diagrams.py books/vuln-hunting/book-src`：Ch01–Ch05 **0 errors, 0 warnings**。
