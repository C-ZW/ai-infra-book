# Adjudication & Bridging Review Log — Slice 1 (`ch01`–`ch05`)

## [2026-11-21] ch01-trust-boundaries.md — fixed
claim: 資料庫 ACID 成立的前提，是所有狀態變更都必須經過單一資料庫引擎排程，且呼叫端本身沒有被置換。
book value: 所有狀態變更都必須經過單一資料庫引擎排程，且呼叫端本身沒有被置換  verifier value: ACID 保證涵蓋已納入該資料庫交易管理且受已宣告約束涵蓋的資料表狀態，無法自動延伸至未納入同一交易的外部系統副作用與上游解析層  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — ACID guarantees apply to data managed within the transaction boundary even for untrusted callers or distributed protocols; the actual boundary gap is cross-layer states and external side effects outside the DB transaction.
tiebreak: n/a
action: Revised bridge failure boundary and transaction guarantee description to accurately scope ACID guarantees to transaction-managed table states and constraints.

## [2026-11-21] ch01-trust-boundaries.md — fixed
claim: 把任意後端系統抽象為一個確定性或非確定性狀態機 M = (S, s_0, Σ, δ, I)，其中 δ: S × Σ → S。
book value: 確定性或非確定性狀態機 δ: S × Σ → S  verifier value: 將排程選擇與環境事件納入輸入字母表 Σ 後以 δ: S × Σ → S 表示，或對非確定性模型採 δ: S × Σ → 𝒫(S)，且單步符號 σ_i ∈ Σ、序列 w = (σ_1, ..., σ_k) ∈ Σ*  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — A single-valued function δ: S × Σ → S is deterministic; explicitly noted δ: S × Σ → 𝒫(S) for nondeterministic transitions and distinguished single symbol σ_i ∈ Σ from sequence w ∈ Σ*.
tiebreak: n/a
action: Updated state machine signature, alphabet definition, and reachability predicate s_j ∈ S \ I along feasible execution prefixes.

## [2026-11-21] ch01-trust-boundaries.md — fixed
claim: Inv_2 (資金守恆)、5 筆請求在 2,000 req/s 容量下僅佔 0.25% 尖峰頻寬 (到達視窗 < 2 ms)、最小請求數 = 2..5 次、僅需 1 次請求即令餘額憑空增加 5,000 分違背 Inv_2、攻擊者永遠沿著攻擊樹中成本最低的 OR 分支前進。
book value: Inv_2 僅列提款累計上限且混列 2..5 次最小請求數與 < 2 ms 推論  verifier value: Inv_2 納入當前餘額 B_db + ∑ successful_withdrawals == B_0 + ∑ verified_deposits 且單筆 amount > 0；5 筆占一秒尖峰請求量 0.25%；最小超額請求數為 2 次；理性攻擊者在可比影響下優先選擇已知且可達之低成本分支  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — Including B_db and amount > 0 in Inv_2 makes the negative-withdrawal violation of Inv_2 mathematically exact; 2 full-balance withdrawals suffice to exceed B_0.
tiebreak: n/a
action: Updated Inv_2/Inv_4 formulas, explicit non-atomic table premises, request count ratios, minimum request count (2), and attack tree heuristic phrasing.

## [2026-11-21] ch01-trust-boundaries.md — fixed
claim: 動手做直連 Redis/Node.js 描述與自我檢核 Q1 情境 B（使帳本總資金非法增加的第二個例子）。
book value: 實驗直連讀寫 Redis Session/限流與情境 B 偷領他戶資金使總資金增加  verifier value: 實驗展示 0.0.0.0 埠暴露與直連 app:3000 避開 Nginx；自我檢核 Q1 情境 B 改為缺少唯一冪等鍵約束的外部入金 Webhook 重複入帳，使帳本總資金在滿足 balance >= 0 與 SERIALIZABLE 下仍非法增加  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — Unauthorized withdrawal decreases or transfers balance rather than increasing total ledger balance; duplicate deposit credit without idempotency key directly increases total ledger balance while satisfying balance >= 0.
tiebreak: n/a
action: Refined lab observation scope to match app.mjs and replaced Self-Check Q1 Scenario B with duplicate idempotency-unprotected deposit credit; refined Q2 path containment and symlink checks.

## [2026-11-21] ch02-recon-and-audit-workflow.md — fixed
claim: MITM 代理交握圖序號、會話 A 建立條件、SyntaxError 歸因、.js.map 揭露範圍與 Allow 標頭範圍。
book value: 圖示步驟 2/3 順序顛倒；完全取決於信任 Root CA；幾乎確定是 Express body-parser；拿回整個前端專案與所有端點；直接讀出後端支援的全部方法  verifier value: 修正圖示為先 CONNECT 後 200 再 TLS 交握；在一般憑證鏈驗證場景（無 Pinning/mTLS 且葉憑證合法）下取決於信任代理 Root CA；JSON 解析錯誤指向 JS/Node 解析層；.js.map 揭露該建置區塊涵蓋之原始碼與端點；Allow 標頭反映回應層對該資源宣告的方法  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — Diagram step ordering and overly sweeping black-box fingerprinting claims needed precision to match protocol and build-chunk boundaries.
tiebreak: n/a
action: Fixed ASCII diagram step numbers (1–6) and tightened black-box fingerprinting, source map, and Allow header scope statements.

## [2026-11-21] ch02-recon-and-audit-workflow.md — fixed
claim: APS 評分範例因子對應（Input_Complexity 與 Sink_Impact）及 NestJS 請求生命週期 Exception Filters 順序。
book value: 自由字串排序條件填 3、Raw SQL 未區分影響級距即填 4；Exception Filters 列為每筆正常請求最後必經階段  verifier value: 對齊級距定義（動態鍵名與巢狀篩選物件為 3，複合 XML/ZIP 為 4；Sink_Impact 依跨表讀寫/帳本竄改 3 或完整認證繞過/RCE 4 區分 54..72 分）；Exception Filters 標明為任一階段拋出未捕獲例外時的處理分支  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — Aligning Input_Complexity and Sink_Impact with section 2.4's rubric and separating Exception Filters from the normal request return path makes the model internally consistent.
tiebreak: n/a
action: Updated APS examples in sections 2.4, 2.5, Lab reference answer, and Self-Check A4; updated NestJS lifecycle diagram in section 2.4.4 and Self-Check A3.

## [2026-11-21] ch02-recon-and-audit-workflow.md — fixed
claim: 動手做基線 JSON 位元組長度（404 94 vs 404 77）與自我檢核 Q2 軟 404 過濾條件。
book value: {"message":"Cannot GET /v1/...","error":"Not Found","statusCode":404} 標為 94 bytes；僅靠 status/type/length 保證零漏報  verifier value: 代入 15-byte 測試路徑 /v1/probe_71f2a 時精確長度為 23 + 15 + 39 = 77 bytes（404 77），且基線與候選探測使用一致認證標頭並涵蓋 GET/POST；軟 404 過濾結合剝除動態 nonce 後的 HTML 殼層結構特徵與 Accept: application/json 及 POST/OPTIONS 方法交叉驗證  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — Direct byte count of `{"message":"Cannot GET /v1/probe_71f2a","error":"Not Found","statusCode":404}` is 77 bytes.
tiebreak: n/a
action: Fixed baseline byte count to `404 77` (`77 bytes`), added auth header and GET/POST loop to the probe script, and refined Soft-404 filtering criteria in Self-Check Q2/A2.

## [2026-11-21] ch03-http-smuggling.md — fixed
claim: 解析器邊界分歧的雙向效應、HTTP/1.1 訊息定界本質與殘留位元組緩衝區位置。
book value: 分歧僅描述後端早停留下尾巴、稱 HTTP/1.1 為無外框純文字串流協定、稱殘留位元組必留在核心 TCP socket 緩衝區  verifier value: 明確區分後端早停（殘留位元組成為下一筆請求開頭）與後端晚停（吞併下一筆請求開頭進前一筆主體）及連線繼續複用前提；說明 HTTP/1.1 在 TCP 串流上以內嵌文字起始行與標頭語法界定邊界且主體可含二進位資料；殘留位元組位於連線接收緩衝區（核心或應用程式串流緩衝區）  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — As shown in lab_smuggle.mjs (`buf = buf.subarray(bodyEnd)`), unconsumed bytes often reside in the application's user-space stream buffer as well as kernel socket buffers.
tiebreak: n/a
action: Updated opening derivation, HTTP/1.1 framing description, and stream buffer state transition explanation.

## [2026-11-21] ch03-http-smuggling.md — fixed
claim: TE.CL Worked Example 與自我檢核 Q2 內層走私請求缺少 Host 標頭；RFC 9112 §5.1 冒號前空白處理規則；時間差探測與租戶分池隔離粒度。
book value: TE.CL 內層 POST 請求未含 Host 標頭（Chunk 長度 0x39 / 0x35）；冒號前空白寫嚴格解析器會拒收或忽略；租戶分池寫成可防止污染其他使用者  verifier value: TE.CL 內層請求已封閉標頭，補上 Host 標頭並重算精確區塊長度（Worked Example 為 85 bytes = 0x55，外層總長 96 bytes；自我檢核 Q2 為 70 bytes = 0x46）；RFC 9112 §5.1 要求伺服器對冒號前空白以 400 拒絕；區分每請求獨立上游連線與按租戶分池（後者僅限制跨租戶污染）  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — In TE.CL the smuggled inner POST request closes its own headers with `\r\n\r\n`, so unlike CL.TE it cannot borrow the victim's Host header and must carry its own Host header to pass RFC 9112 §3.2 validation.
tiebreak: n/a
action: Added `Host` header to TE.CL worked example (recomputed chunk length `55\r\n` = 85 bytes) and Self-Check Q2/A2 (recomputed chunk length `46\r\n` = 70 bytes); clarified RFC 9112 §5.1 rejection vs vulnerable ignore behavior, buffering proxy assumption in timing probes, and per-request vs per-tenant connection isolation.

## [2026-11-21] ch04-authentication-and-sessions.md — fixed
claim: JWT Header 查表與信任根邊界、alg: none 觸發條件、PKCS#1 vs X.509 SPKI 公鑰格式名稱、HMAC 長金鑰雜湊行為與 PKCE plain 降級條件。
book value: 先讀 Header 決定哪把金鑰即任意身分偽造；PUBLIC KEY 標為 PKCS#8 SPKI；差一個位元組 HMAC 永遠不同；plain 降級僅攔截 code 即可兌換  verifier value: 驗簽前可解析 kid 作為伺服器預先限定之可信金鑰集內的查表提示，允許未驗證 Header 改變演算法政策、金鑰類型或可信金鑰來源才構成信任根倒置；BEGIN PUBLIC KEY 修正為 X.509 SPKI；說明 >64B PEM 先經 SHA-256 壓縮為 K'；區分未啟用 PKCE（攔截 code 即可兌換）與降級為 plain（觀測或指定授權請求參數即得知 verifier）  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — `BEGIN PUBLIC KEY` is X.509 SubjectPublicKeyInfo (SPKI), whereas PKCS#8 is a private-key format; constrained `kid` lookup in a trusted JWKS is standard practice.
tiebreak: n/a
action: Updated bridge failure boundary, `alg: none` condition, X.509 SPKI terminology (in prose and Lab tip), HMAC key derivation explanation, and PKCE plain downgrade requirements.

## [2026-11-21] ch04-authentication-and-sessions.md — fixed
claim: Refresh Token 輪換 UPDATE 回傳 0 列時的重用判定、自我檢核 Q2 撤權後最長存取視窗（300 s vs 899 s）與 Q3 OAuth redirect_uri 參數外洩條件。
book value: UPDATE 回傳 0 列立即判定為 Token Reuse；撤銷金鑰後仍可存取 900 s；重導向至 next 直接外洩另一查詢參數 code  verifier value: UPDATE 回傳 0 列時須先檢查持久化記錄是否為已存在且 used = true（排除自然過期或無效雜湊）才觸發整個 family_id 撤銷；區分立即自權威 JWKS 移除舊公鑰（上限 min(899 s, 300 s) = 300 s）與保留舊公鑰／僅停用帳號（上限 899 s ≈ 15 分鐘）；明定開放重導向端點保留查詢字串或經寬鬆 Referrer-Policy 外洩 Referer  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — Zero updated rows on a multi-predicate WHERE clause can be caused by expiry or unknown hash; checking `used = true` on the existing row within a transaction accurately isolates token reuse.
tiebreak: n/a
action: Updated Refresh Token rotation transaction logic, middleware lifetime claim checks, and Self-Check Q2/A2 and Q3/A3 derivations.

## [2026-11-21] ch05-enterprise-sso-and-mfa.md — fixed
claim: Exclusive C14N 空白文字節點行為、286 bytes 正規化輸入與 32 bytes SHA-256 摘要區分、XSW #1/#3 圖表一致性、惡意 Assertion 子節點位置及標準 XML DOM 限定名稱查詢（getElementsByTagNameNS / saml:NameID）。
book value: 稱 C14N 消除空白、寫 SHA-256 Digest 位元組長度 = 285 bytes、稱惡意 Assertion 為 <samlp:Response> 第一個子節點、使用 getElementsByTagName("NameID")[0] 查詢 <saml:NameID>、Comment("") 無空白  verifier value: Exclusive C14N 保留節點集內文字空白（範例將已簽章 Assertion 寫為緊湊單行，正規化輸入精確為 286 bytes，SHA-256 摘要輸出為 32 bytes）；統一 XSW #1 圖表為包裹已簽章 Response；明定惡意 Assertion 為 <saml:Issuer> 之後的第一個 <saml:Assertion>（第 2 個元素子節點）；改用 getElementsByTagNameNS(SAML_NS, "NameID")[0] 或 getElementsByTagName("saml:NameID")[0]；<!-- --> 對應 Comment(" ")  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — In standard XML DOM, `getElementsByTagName` matches qualified name `saml:NameID`, and Exclusive C14N preserves inter-element whitespace text nodes while producing a 32-byte SHA-256 digest from the 286-byte compact canonicalized `<saml:Assertion>`.
tiebreak: n/a
action: Updated XMLDSig diagram, XSW #1/#3 topology diagram, Section 5.3 Worked Example XML and byte-count derivation (286-byte C14N input -> 32-byte SHA-256 digest), DOM namespace queries, and `Comment(" ")` node representation.

## [2026-11-21] ch05-enterprise-sso-and-mfa.md — fixed
claim: SP-initiated InResponseTo 會話綁定、Assertion/@ID 防重放 TTL 涵蓋 Clock Skew、WebAuthn 七項驗證邊界（含 signCount 風險政策與公鑰驗簽）及 MFA 嘗試次數原子遞增時機。
book value: 僅單次作廢 InResponseTo 即防登入 CSRF；防重放 TTL 僅計 NotOnOrAfter 剩餘秒數；WebAuthn 寫五項邊界且要求 signCount 嚴格遞增；核發或驗證 MFA 時皆執行 INCR  verifier value: InResponseTo 須綁定發起登入的瀏覽器會話並原子消費；防重放 TTL 須覆蓋 NotOnOrAfter 剩餘秒數加容許時鐘偏差 clockSkewSeconds；WebAuthn 明列七項驗證邊界（含憑證歸屬與公鑰驗簽，signCount 異常依 RP 風險政策處置）；MFA 挑戰於核發時初始化為 0，僅在每次驗證請求前原子 INCR 檢查額度（> 5 即刪除挑戰）並於核准時原子銷毀挑戰  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — Incrementing attempts at challenge issuance would waste an attempt, and replay TTL must include clock skew so an assertion cannot be replayed during the skew acceptance window after nominal `NotOnOrAfter`.
tiebreak: n/a
action: Updated Section 5.5 replay/CSRF requirements, Section 5.6 WebAuthn 7-item checklist, Section 5.7 TOTP hit-rate formula, and Section 3 Defense code and MFA attempt counter protocol.

---

## Bridging Review Summary (Slice 1: `ch01`–`ch05`)

| Chapter | Declared Bridge (`outline.md`) | Detected Bridge | Isomorphism Score | Conversational / Everyday Analogies | Verdict |
|---|---|---|---|---|---|
| `ch01-trust-boundaries.md` | 資料庫 ACID 不變量 → 安全不變量（Invariant） | 資料庫 ACID 不變量 → 安全不變量（Security Invariant），明確標出成立邊界與失效邊界 | 5 | None | `pass` |
| `ch02-recon-and-audit-workflow.md` | 系統效能 Profiling（Flamegraph 找熱點）→ 攻擊面測繪與 Source-to-Sink 追蹤 | 系統效能 Profiling（Flamegraph 找熱點）→ 攻擊面測繪與 Source-to-Sink 追蹤，明確標出成立邊界與失效邊界 | 5 | None | `pass` |
| `ch03-http-smuggling.md` | 分散式前後端序列化 Schema 漂移 → HTTP 解析器分歧（Parser Differential） | 分散式前後端序列化 Schema 漂移 → HTTP 解析器分歧（Parser Differential），明確標出成立邊界與失效邊界 | 5 | None | `pass` |
| `ch04-authentication-and-sessions.md` | 分散式快取一致性與過期視窗 → Token / JWKS 驗證與撤銷失效 | 分散式快取一致性與過期視窗 → Token / JWKS 驗證與撤銷失效，明確標出成立邊界與失效邊界 | 5 | None | `pass` |
| `ch05-enterprise-sso-and-mfa.md` | `none`（承接 Ch04 驗證信任鏈直接剖析 SAML/WebAuthn 協定） | `none`（直接承接 Ch04 認證信任鏈切入 XMLDSig 與 WebAuthn） | 5 | None | `pass` |
