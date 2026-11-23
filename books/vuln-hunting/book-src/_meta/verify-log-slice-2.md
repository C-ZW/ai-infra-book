# P4 Adjudication & Bridging Review Log — Slice 2 (Ch06–Ch10)

## [2026-11-21] ch06-authorization-and-multitenancy.md — fixed
claim: 當系統實作漏掉其中一維的檢查，就會對應出三種截然不同的漏洞型態（四元決策輸入與三種漏洞分類關係）
book value: 四元組漏掉其中一維即一對一對應 BOLA/BOPLA/BFLA  verifier value: 依失效的授權粒度與檢核範圍區分為物件、物件屬性與功能三類（Context 可伴隨於任一類，且單一端點可同時漏檢多項）  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 四元組含 Subject/Action/Object/Context，其中 BOLA 與 BOPLA 皆涉及 Object（整列 vs 屬性），並非四對三的一對一映射。
tiebreak: n/a
action: 修正第 1 節導言與 BOPLA 2019→2023 合併說明，並於 Policy Engine 輸入補齊 `{ subject, action, resource, context }`。

## [2026-11-21] ch06-authorization-and-multitenancy.md — fixed
claim: E1 GET 端點 BOLA 示範直接推論「讀取或提領對方的 10,000 分（$100.00）餘額」與 Worked Example 六位數損失敘述
book value: 由 E1 GET 查表直接推得提領，且將情境估算手續費漏損 $225,000.00 直接混稱為帳本損失  verifier value: E1 僅示範跨租戶讀取，跨租戶提領須以 E3 存在相同租戶條件漏檢為前提；$225,000.00 為 90,000 筆零費率結算之手續費漏損情境估算，$50,000.00 為 500 戶直接盜領估算，E2 與 E5 費率歸零不重複計入  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 區分 E1 讀取與 E3 提領的授權缺漏前提，並明確標示 $225,000.00 手續費漏損與 $50,000.00 直接盜領為各自的情境估算。
tiebreak: n/a
action: 修正 E1 程式碼解析、Worked Example 角色定義（明定 R1 範圍與矩陣外 platform_admin）與損失估算陳述。

## [2026-11-21] ch06-authorization-and-multitenancy.md — fixed
claim: RLS 適用角色條件、PgBouncer 連線池殘留、Redis 快取命中、DTO 白名單裝飾器與 NULLIF(current_setting(...), '')::bigint 行為
book value: 簡稱為非超級使用者即受 RLS 管轄；未區分 current_setting 未設定（NULL）與空字串（''）；腳本聲稱掃描 6 個端點但實際僅探測 E1/E2/E5  verifier value: RLS 受 BYPASSRLS 與未設 FORCE 時的 Table Owner 影響；NULLIF 將空字串統一轉為 NULL 使相等比較為 UNKNOWN（Fail-Closed）；明示腳本以 TOKEN_B_OPER 探測 E1/E2/E5 三個代表性端點  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 補齊 BYPASSRLS/Table Owner 條件、DTO 屬性驗證裝飾器、E1 查無列轉 404 NotFoundException 及 NULLIF 轉 NULL 的精確 SQL 語意。
tiebreak: n/a
action: 修正橋接失效邊界、故障模式 1、動手做任務一／二描述與參考解答。

## [2026-11-21] ch06-authorization-and-multitenancy.md — fixed
claim: 自我檢核第 3 題：「這組防護能擋下哪一類漏洞，又漏掉了哪兩類？」
book value: 漏掉兩類（把 BOPLA 與 BFLA 併為同一項）  verifier value: 比對 params.tid === user.tenantId 僅擋下路徑租戶與憑證租戶不符的請求，仍漏掉 BOLA、BOPLA 與 BFLA 共三類  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — BOLA、BOPLA、BFLA 為本章定義之三類獨立授權漏洞，應明確列為三類。
tiebreak: n/a
action: 將自我檢核第 3 題題幹與參考解答修正為漏掉 BOLA、BOPLA 與 BFLA 三類。

## [2026-11-21] ch06-authorization-and-multitenancy.md — bridging-review
declared_bridge: PostgreSQL Row-Level Security（RLS）→ 物件層級授權（BOLA）邊界
detected_bridges: ["PostgreSQL Row-Level Security（RLS）→ 物件層級授權（BOLA）邊界"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch07-graphql-grpc-websocket.md — fixed
claim: GraphQL 端點形式、AST 執行樹走訪與欄位建議（Field Suggestion）還原範圍
book value: 斷言 GraphQL 一律收斂於單一 POST /graphql、每個 AST 節點皆呼叫 resolve() 查庫、關閉 Introspection 仍能還原整份隱藏 Schema  verifier value: 限定為常見部署與 NexusPay 實作；區分 AST 欄位選取、父物件列表基數展開之 Resolver 呼叫與實際後端查詢次數；Field Suggestion 可枚舉出大量候選欄位與敏感 Mutation 名稱  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 修正協定通則與實作部署的界線，並精確區分 AST 節點與執行期 Resolver 呼叫數。
tiebreak: n/a
action: 修正導言、橋接段落與 GraphQL 機制第 1–2 點（同時釐清 Document 與 Operation 階層關係）。

## [2026-11-21] ch07-graphql-grpc-websocket.md — fixed
claim: GraphQL Worked Example 與動手做任務一查詢深度／分支度模型及 40.96 s 資料庫耗時推導
book value: 將「單次請求 Batch / Alias 數量：20」混寫；任務一範例查詢僅 3 層帶 limit: 4；直接將累計查詢工時 40.96 s 等同於單一連線牆鐘延遲  verifier value: HTTP Batch 操作數為 1（<= 20）、單一 Operation 內含 20 個 Alias；5 層一對多關聯列表皆設 limit: 4（含純量葉欄位共 6 層 <= 8）；區分第 5 層葉關聯 20,480 次（40.96 s）與全樹累計 27,280 次邊走訪（54.56 s）及循序執行逾時條件  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 對齊 Worked Example 與任務一程式碼的 5 層 limit: 4 展開結構，並明確交代 AST 成本計算式（單一 Alias 1,364、總計 27,280 > 500）。
tiebreak: n/a
action: 修正 Worked Example 條件設定與推論、任務一查詢結構、複雜度計算與 PIN 內部計數器前提。

## [2026-11-21] ch07-graphql-grpc-websocket.md — fixed
claim: Protobuf proto3 純量預設零值、未知欄位透傳與跨語言整數精度／符號邊界
book value: 宣稱 proto3 任何未傳送純量欄位一律解碼為零值且無法區分；把 Node.js 53-bit 精度流失與負數符號問題混寫  verifier value: 限定於預設隱式存在（implicit presence，未標註 optional）的純量欄位；未知欄位透傳取決於保留未知欄位並直接重新序列化原訊息的代理路徑；分別說明 int32/uint32/int64 窄化符號重解讀與 JS Number 53-bit IEEE 754 精度捨入分歧  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 區分 implicit vs explicit presence（optional），並將整數窄化符號問題與 53-bit 浮點精度捨入分開表述。
tiebreak: n/a
action: 修正 gRPC 與 Protobuf 機制第 1–3 點。

## [2026-11-21] ch07-graphql-grpc-websocket.md — fixed
claim: WebSocket CSWSH 測試腳本判定、Cookie SameSite 前提與 Origin 白名單驗證表達式
book value: 非瀏覽器腳本手動帶 Cookie 連線成功即印出 CSWSH vulnerable，且將握手與訂閱包在同一 try/except；Origin 驗證僅寫 new URL(origin).origin === ALLOWED_ORIGIN  verifier value: 腳本驗證的是伺服器未檢查 Origin 與跨租戶訂閱，真實瀏覽器 CSWSH 另須 Cookie 符合跨站／同站附送條件；分開捕捉握手與訊息階段例外；Origin 須先確認為合法單一來源值並與白名單精確全等比對  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 拆分任務二腳本的握手與訂閱例外處理，修正輸出語意、Origin 驗證條件及自我檢核第 3 題解答。
tiebreak: n/a
action: 修正 WebSocket 防禦段落、任務二腳本與自我檢核第 3 題解答。

## [2026-11-21] ch07-graphql-grpc-websocket.md — bridging-review
declared_bridge: RPC/GraphQL Resolver 執行樹 → 非 REST 查詢複雜度與授權破口
detected_bridges: ["RPC/GraphQL Resolver 執行樹 → 非 REST 查詢複雜度與授權破口"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch08-injection-families.md — fixed
claim: PostgreSQL Extended Query Protocol 的 Parse/Bind 階段職責與佔位符 $1 型別限制
book value: 稱 Parse 階段即確定執行計畫，且佔位符 $1 只能綁定數值常數  verifier value: Parse 階段確定語法樹（AST）結構與參數位置，Bind 階段綁定參數值並進行規劃（或套用通用計畫）；佔位符可綁定字串、數值等各型別純量資料值，但不能代替欄位識別字或 ASC/DESC 語法關鍵字  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — PostgreSQL Extended Query Protocol 於 Parse 解析語法樹，於 Bind 帶入純量值（含字串與數值）並規劃執行計畫；ORDER BY $1 會被當作常數運算式而非欄位識別字。
tiebreak: n/a
action: 修正第 1 節正文與自我檢核第 1 題題幹及參考解答，並同步精化橋接目標機制之資料平面定義。

## [2026-11-21] ch08-injection-families.md — fixed
claim: 線性搜尋期望次數（272 vs 270、最壞 512 vs 480）與 P99 延遲上界估算
book value: 混用逐項確認平均 8.5 次（32 × 8.5 = 272）與末項排除最壞 15 次（32 × 15 = 480），並將 P99 45 ms 稱為期望延遲  verifier value: 明確區分逐項確認模型（平均 8.5 次 → 272 次、最壞 512 次；Base64URL 16 字元平均 520 次）與末項排除模型（平均 8.4375 次 → 270 次、最壞 480 次；Base64URL 平均 519.75 次）；將 45 ms 與 545 ms 正確標示為兩分支之 P99 延遲上界  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 同時列出逐項確認與末項排除兩種線性基準模型並將 P99 與平均值語意區分清楚，使數學推導完全自洽。
tiebreak: n/a
action: 修正第 1 節盲注推導、Worked Example 與自我檢核第 4 題解答。

## [2026-11-21] ch08-injection-families.md — fixed
claim: 靜態白名單映射 SORT_COLUMN_MAP / SORT_DIR_MAP 的原型鏈繼承屬性漏洞與盲注驗證腳本 HTTP 狀態檢查
book value: 直接以一般物件索引 `SORT_COLUMN_MAP[String(req.query.sort)] ?? 'created_at'` 並宣稱 100% 與外部輸入切斷；Python 腳本僅檢查 `r.status_code >= 500`  verifier value: 一般物件索引會命中 `toString` 等 `Object.prototype` 繼承屬性（非 null/undefined 故不會觸發 `??`），須先以 `Object.hasOwn()` 檢核自有屬性；Python 腳本應檢查 `r.status_code != 200` 以正確識別修補後的 `400 Bad Request` 攔截  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 一般物件直接取屬性會命中原型鏈上的函式屬性，必須對欄位與方向映射皆使用 `Object.hasOwn`。
tiebreak: n/a
action: 修正故障模式 1 程式碼範例、動手做 Python 腳本狀態碼檢查與驗證說明，並精化 Redis 鍵名碰撞／萬用字元、Argument Injection 與 SSTI 的適用前提。

## [2026-11-21] ch08-injection-families.md — bridging-review
declared_bridge: AST 編譯階段與字串模板拼接 → 資料平面與控制平面混同（Injection）
detected_bridges: ["AST 編譯階段與字串模板拼接 → 資料平面與控制平面混同（Injection）"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch09-file-parsers-and-xxe.md — fixed
claim: POSIX 路徑解析與 Linux VFS 函式區分、symlink vs hardlink 機制差異、以及 Node.js/Python/libc 對內嵌 NUL (\x00) 的處理
book value: 將 Linux 核心 `path_lookupat()` 直接當成 POSIX 規範定義；稱硬連結與 symlink 一樣會在開檔時跟隨目標路徑跳出沙箱；稱新版 libc 介面已拒絕路徑中的 `\x00`  verifier value: 區分 POSIX 路徑語意與 Linux VFS 實作；symlink 指向目標路徑字串而 hardlink 直接指向同檔案系統的同一 inode；Node.js/Python 3 檢查字串長度並拒絕內嵌 `\x00`，但以 C 字串傳遞路徑的傳統 libc 介面僅以 `\x00` 為終止符而無長度檢查  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 三處底層作業系統與執行時期語意均須精確區分。
tiebreak: n/a
action: 修正 9.1 節導言與第 4 小節（硬連結、軟連結與 Null Byte 截斷）。

## [2026-11-21] ch09-file-parsers-and-xxe.md — fixed
claim: Worked Example 情境 A 中 `{"secret":"pwned","endpoint":"http://10.0.0.5/hook"}` 的位元組長度與 ZIP 結構偏移
book value: 寫入內容長度算為 51 bytes（0x33），後續偏移依 51 推算（Central Directory 偏移 116 = 0x74、EOCD 偏移 197 = 0xc5、總長 219 bytes）  verifier value: `{"secret":` (10) + `"pwned",` (8) + `"endpoint":` (11) + `"http://10.0.0.5/hook"}` (23) = 52 bytes（0x34）；Central Directory 偏移應為 65 + 52 = 117（0x75），Central Directory 檔名偏移 163（0xa3），EOCD 偏移 198（0xc6），總檔長 220 bytes  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 最後一段 `"http://10.0.0.5/hook"}` 共 23 bytes，總長確為 52 bytes（0x34）。
tiebreak: n/a
action: 將情境 A 與情境 B 中的酬載長度修正為 52 bytes（`0x34`），並同步更新 ZIP Local Header、Central Directory 與 EOCD 的所有精確十六進位／十進位偏移與總檔長（220 bytes）。

## [2026-11-21] ch09-file-parsers-and-xxe.md — fixed
claim: XML 1.0 §2.8 內部 DTD 子集參數實體限制與 §4.2 Error-Based XXE 實體重複宣告綁定規則
book value: 將 `SYSTEM "..."` 稱為 `EntityValue` 並引用 §2.8 Entity Value 限制；稱 Error-Based XXE 利用後宣告覆寫本地 DTD 的既有實體  verifier value: `SYSTEM` 後方為 `SystemLiteral`（不直接展開 `%file;`），而動態構造宣告受限於 XML 1.0 §2.8「WFC: PEs in Internal Subset（內部子集不得在標記宣告內部引用參數實體）」；XML 1.0 §4.2 規定同名實體重複宣告時以最先出現者為準（First Declaration Wins），故須在引入本地 DTD 前預先宣告參數實體以搶佔定義  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 修正 XML 1.0 §2.8（WFC: PEs in Internal Subset + SystemLiteral）與 §4.2（First Declaration Wins）的規範推導。
tiebreak: n/a
action: 修正 9.3 節第 2–3 小節與自我檢核第 2 題參考解答。

## [2026-11-21] ch09-file-parsers-and-xxe.md — fixed
claim: SVG Stored XSS 觸發上下文、`resolveSafePath()` 的祖先目錄與目標 symlink 檢查、以及自我檢核第 3 題 `link/pwn` 描述
book value: 稱提供 SVG 下載或檢視即直接在瀏覽器執行腳本；`resolveSafePath()` 僅在直接父目錄已存在時檢查 `realpathSync(parentDir)` 且未檢查既有目標檔案是否為 symlink；稱 `link/pwn` 不含 `..` 或 `/`  verifier value: SVG 須在允許執行腳本的文件上下文（如頂層導航或 iframe/object/embed，而非 `<img>` 或 attachment 下載）才會執行腳本；`resolveSafePath()` 應向上追溯至最深既有祖先目錄並拒絕覆寫既有 symlink，且說明歸檔解壓須拒絕連結條目與防範 TOCTOU；`link/pwn` 為不含 `..` 且不以 `/` 開頭  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 修正 SVG 執行上下文、強化 `resolveSafePath()` 祖先目錄迴圈與 `lstatSync` 檢查，並將自我檢核第 3 題修正為「不含 `..` 且不以 `/` 開頭」。
tiebreak: n/a
action: 修正 9.5 節、防禦對照表、`resolveSafePath()` 實作與自我檢核第 3–4 題解答。

## [2026-11-21] ch09-file-parsers-and-xxe.md — bridging-review
declared_bridge: none
detected_bridges: []
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch10-browser-and-client-attacks.md — fixed
claim: Worked Example 中 CSP 標頭值位元組長度（98 bytes vs 103 bytes）與 2048-bit RS256 JWT 無填充 Base64URL 簽章長度（342 chars vs 344 chars）
book value: CSP 值總長 103 bytes；RS256 簽章段 344 字元、JWT 總長 780 字元、外洩 URL 802 字元  verifier value: `default-src 'self'; script-src 'self' https://cdn.nexuspay-static.example/libs/; object-src 'none'` 共 18 + 2 + 59 + 2 + 17 = 98 bytes；256-byte RSA 簽章經無填充 Base64URL 編碼為 342 字元，搭配 Header 36 + Payload 398 + 2 個句點共 778 字元，外洩 URL 為 22 + 778 = 800 字元  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 實算 ASCII 字元數確為 98 bytes，且 256 bytes 無填充 Base64URL 長度為 ceil(256 * 4 / 3) = 342 字元。
tiebreak: n/a
action: 將 Worked Example 中 CSP 標頭值長度修正為 98 bytes，JWT 長度修正為 36 + 398 + 342 + 2 = 778 字元，外洩 GET URL 長度修正為 800 字元。

## [2026-11-21] ch10-browser-and-client-attacks.md — fixed
claim: CORS 反射 Origin / 信任 null 與同站子網域請求的 Cookie 附送前提、以及 CSPT2CSRF 對 CSRF Token 的繞過範圍
book value: 斷言反射 Origin + Allow-Credentials 即讓任何網站帶著 Cookie 讀回應；稱同 eTLD+1 子網域請求一律附帶 SameSite=Strict Cookie；稱 CSPT2CSRF 完全繞過 CSRF Token  verifier value: CORS 回應標頭僅開放讀取，Cookie 是否附送仍取決於憑證模式與 SameSite/Domain/Secure 條件；同站判定在現代規範下還須同協定（schemeful Same-Site）且 Cookie 作用域涵蓋目標主機；CSPT2CSRF 會自動帶上同源前端共用客戶端自動附掛的全域 CSRF Token 標頭，但若目標端點獨立驗證綁定特定動作的 Token 則仍須通過該驗證  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 補齊 Cookie 附送條件、schemeful Same-Site 與全域 vs 動作綁定 CSRF Token 的成立邊界。
tiebreak: n/a
action: 修正第 1、2、5 節正文與自我檢核第 2 題解答。

## [2026-11-21] ch10-browser-and-client-attacks.md — fixed
claim: Trusted Types 匯點型別區分（TrustedHTML vs TrustedScript vs TrustedScriptURL）與 Sec-Fetch-* Resource Isolation 規則
book value: 稱 `innerHTML`、`document.write` 與 `eval` 皆轉型為 `TrustedHTML`；稱僅拒絕 `Sec-Fetch-Site === "cross-site"` 且 `Sec-Fetch-Mode !== "navigate"` 的請求即可保護狀態變更  verifier value: `innerHTML`/`document.write` 要求 `TrustedHTML`、`script.src` 要求 `TrustedScriptURL`、`eval` 要求 `TrustedScript`；跨站表單 POST 本身即為 `Sec-Fetch-Mode: navigate`（且 iframe 導航亦為 `navigate`），故狀態變更端點必須拒絕所有 `cross-site` 請求，僅對安全方法（GET/HEAD）且 `Sec-Fetch-Mode === "navigate"`、`Sec-Fetch-Dest === "document"` 的頂層導航放行頁面路由  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 修正 Trusted Types 三種可信型別對應關係與 Fetch Metadata 的狀態變更攔截條件。
tiebreak: n/a
action: 修正「故障模式與防禦」第 1 節與第 2 節（同時補齊 16 bytes Base64 Nonce = 24 字元的說明）。

## [2026-11-21] ch10-browser-and-client-attacks.md — fixed
claim: `encodeURIComponent()` 對點號（`.`）的編碼行為、CSPT `../` 目錄回退層數與自我檢核第 3、5 題推導
book value: 稱 `encodeURIComponent()` 會編碼點號 `.`；自我檢核第 5 題稱一個 `../` 在 `/api/v1/reports/${reportId}/summary` 中向上退兩層目錄且未交代 `URLSearchParams.get()` 解碼 `%23`；第 3 題第一個初始 URL `https://static.nexuspay.example/redirect` 在重導前即不符 `/v1/lib.js` 路徑  verifier value: `encodeURIComponent()` 會編碼 `/`、`?`、`#` 但**保留 `.` 不編碼**（單獨傳入 `..` 仍會造成路徑歸約），故必須搭配完整 UUID 格式白名單並拒絕 `.`/`..`；一個 `../` 僅向上移除 `reports` 一層目錄，且須經 `URLSearchParams.get()` 先將 `%2F`、`%23` 解碼為 `/`、`#` 才會截斷 `/summary`；第 3 題兩個初始請求統一由同源 `/redirect?to=...` 發起以精確對照重導向後的 host 檢查與路徑放寬  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — `encodeURIComponent("..") === ".."` 為 JavaScript 標準行為，且 `/api/v1/reports/../users/me/tokens` 僅回退 `reports` 一層。
tiebreak: n/a
action: 修正「故障模式與防禦」第 3 節、自我檢核第 3 題與第 5 題題幹及參考解答。

## [2026-11-21] ch10-browser-and-client-attacks.md — bridging-review
declared_bridge: 瀏覽器 Origin 隔離與容器命名空間隔離的結構邊界對照
detected_bridges: ["瀏覽器 Origin 隔離與容器命名空間隔離的結構邊界對照"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass
