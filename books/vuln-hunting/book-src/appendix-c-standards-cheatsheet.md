# 附錄 C：CWE Top 25 / OWASP Top 10:2025 / OWASP API Top 10:2023 / CVSS v4.0 與本書章節速查對照表

本附錄將業界四大主流安全分類與嚴重度量化標準——**OWASP Top 10:2025**、**OWASP API Security Top 10:2023**、**MITRE CWE Top 25**（2025–2026 基準版）以及 **FIRST CVSS v4.0 + EPSS + CISA KEV**——與《邊界失守》全書 37 章（含 30 個已完稿章節與 7 個標註 `[尚未完稿預留章節]` 之架構槽位）及 **NexusPay** 系統模型完整對齊（外部基準截至 2026-11，對齊 `_meta/landscape-2026-11.md`）。

無論你在撰寫漏洞揭露報告（GHSA / Bug Bounty）、設計企業 SDLC 安全閘門，或準備 Product Security / AppSec 面試，皆可透過本表在 30 秒內完成「標準編號 ↔ 底層機制章節 ↔ 結構性防禦（Paved Road）」的雙向查找。

---

## 一、OWASP Top 10:2025 與本書章節對照表

OWASP Top 10:2025（2025 年底釋出、2026 年初正式定版）延續以資料驅動與根因聚合為核心的分類邏輯：A01 維持為 Broken Access Control（已併入 SSRF），A02 升為 Security Misconfiguration，A03 聚焦 Software Supply Chain Failures，並於 A10 新增 Mishandling of Exceptional Conditions。

| OWASP Top 10:2025 項目 | 核心失效機制 | 對應本書章節 | NexusPay 代表性攻擊場景 | 結構性防禦（Paved Road / 架構控制） |
|---|---|---|---|---|
| **A01:2025 — Broken Access Control**（含 SSRF） | 缺少物件／功能層級授權、多租戶隔離漏檢、CORS 錯誤設定、路徑穿越、URL 解析分歧與 DNS Rebinding 引發之 SSRF | **Ch06**, **Ch07**, **Ch09**, **Ch10**, **Ch11**, **Ch18**, **Ch34** | 跨租戶讀取 `/v1/tenants/:tid/accounts/:aid`；Webhook 藉由 DNS Rebinding 或 IPv6 映射存取 `169.254.169.254` 竊取 IAM 憑證 | 全域 Fail-Closed 授權中介層＋啟動期路由斷言、`TenantDbClient` 搭配 PostgreSQL RLS、Socket 層 IP Pinning 之 `SafeHttpClient` |
| **A02:2025 — Security Misconfiguration** | 雲端／容器權限過度開放、代理與後端逾時／正規化不一致、預設開啟除錯與 GraphQL Introspection、WAF 主體截斷設定不當 | **Ch02**, **Ch03**, **Ch07**, **Ch11**, **Ch14**, **Ch17**, **Ch18** | Nginx `proxy_read_timeout = 30 s` 與 Node.js `keepAliveTimeout = 5 s` 錯位；K8s Pod 自動掛載高權限 SA Token；WAF `8,192 bytes` 截斷放行超長 Payload | Pod Security Standards（`restricted`）、`automountServiceAccountToken: false`、IMDSv2 `Hop Limit = 1`、IaC 與代理設定 CI 自動化基線檢查 |
| **A03:2025 — Software Supply Chain Failures** | 相依套件名稱混淆（Dependency Confusion）、惡意安裝腳本、CI/CD `pull_request_target` 注入、缺乏建置簽章與可達性分析 | **Ch19**, **Ch28**, **Ch31**, **Ch34** | PR 標題夾帶 Shell 指令注入 GitHub Actions 竊取 `NPM_TOKEN`；內部 `@nexuspay/*` 套件遭公網同名高版本覆蓋 | 私有 Scope 強制綁定、Action 釘選 `40 字元 Commit SHA`、不可信變數隔離於 `env:`、OIDC 短效部署、SCA 可達性分析（Reachability Analysis） |
| **A04:2025 — Cryptographic Failures** | 使用弱加密模式（ECB / 無 MAC 之 CBC）、AES-GCM Nonce 重用、非恆定時間簽章比對、使用非密碼學 PRNG（`Math.random()`） | **Ch04**, **Ch15** | AES-CBC Padding Oracle 逐位元組解密 Cookie；AES-GCM `96-bit` Nonce 重用洩漏明文與 GHASH 金鑰 `H`；HMAC 時序側通道 | 全面採用隨機 Nonce AEAD（並將租戶上下文綁入 AAD）、強制 `crypto.timingSafeEqual` 與 `crypto.randomBytes` |
| **A05:2025 — Injection** | 資料平面與控制平面混同：SQLi（含 ORM raw/orderBy）、NoSQL/Redis 注入、OS 命令／參數注入、SSTI、XXE、DOM XSS 與 LLM Prompt Injection | **Ch08**, **Ch09**, **Ch10**, **Ch13**, **Ch16**, **Ch28** | 報表排序欄位觸發 PostgreSQL 時間盲注；發票備註夾帶 Indirect Prompt Injection 誘導 AI Agent 執行未授權退款 | 參數化查詢＋動態識別符白名單、禁用外部 XML 實體、Strict CSP、CodeQL `TaintTracking` 阻斷閘門、獨立於 LLM 的確定性 Tool Policy Gate |
| **A06:2025 — Insecure Design** | 缺乏威脅建模與業務邏輯不變量保護、高併發 TOCTOU 雙花、多步驟狀態機跳步、過度授權的 AI Agent 架構 | **Ch01**, **Ch12**, **Ch16**, **Ch34**, **Ch36** | HTTP/2 單封包同步送達 `20` 個提領請求（抖動 `< 1 ms`），於 `READ COMMITTED` 下擊穿 `$100.00`（`10,000` 分）餘額上限 | 30 分鐘輕量威脅建模、單條條件式原子 `UPDATE ... WHERE balance >= $1`＋DB `CHECK` 約束、唯一 `Idempotency-Key` |
| **A07:2025 — Authentication Failures** | JWT `alg: none` 與 `RS256 → HS256` 混淆、`kid` 路徑注入、OAuth `redirect_uri` 劫持、SAML XSW 與註解截斷、WebAuthn/MFA 繞過 | **Ch04**, **Ch05** | 以公開 JWKS RSA 公鑰偽造 `HS256` 管理員 Token；於 SAML Assertion 插入未簽章節點（XSW #3）或 `<!-- -->` 截斷冒充商戶管理員 | 強制鎖定驗簽演算法白名單、SAML 僅從已驗簽 Reference 子樹提取 `NameID`、Refresh Token 原子輪換與 Family 異常撤銷 |
| **A08:2025 — Software or Data Integrity Failures** | 不安全反序列化、Prototype Pollution、未驗證外部 Webhook / 建置產物完整性、客戶端狀態未驗章信任 | **Ch13**, **Ch19**, **Ch25** | `deepMerge` 未攔截 `__proto__` 污染 `Object.prototype` 並觸發 `child_process` RCE Gadget | `Object.create(null)`、`--disable-proto=throw`、Schema 嚴格驗證（Zod）、Sigstore/Cosign 映像檔簽章 |
| **A09:2025 — Security Logging and Alerting Failures** | 缺乏對安全不變量破壞（如帳本負餘額、高頻重試、內網 IP 探測、FFI 子行程 SIGSEGV）的高訊號即時告警，或告警噪音過高導致麻痺 | **Ch34**, **Ch36**, `ch35 [尚未完稿預留章節]` | 攻擊者發動單封包雙花或 SSRF 探測 IMDS 時無專屬對帳／出口連線告警，或真實告警被 30% SAST/WAF 誤報淹沒 | 非同步帳本不變量巡檢告警、容器出口連線異常即告警、將 CI 阻斷規則誤報率控制在 `< 3%`–`< 5%` |
| **A10:2025 — Mishandling of Exceptional Conditions** | 錯誤處理路徑提前釋放記憶體卻未清零指標（UAF）、整數溢位回繞、Rust Panic 跨越 FFI 邊界、例外發生時 Fail-Open 放行權限、ReDoS 耗盡事件迴圈 | **Ch01**, **Ch13**, **Ch20**, **Ch25**, **Ch29**, `ch23–ch24 [尚未完稿預留章節]` | `libnexus-parse` 在錯誤分支提前 `free()` 或 `len + 8` 32 位元溢位回繞為 `0` 導致堆積損毀；驗證中介層捕捉超時例外後未 `return` 而繼續執行後續路由 | 錯誤路徑嚴格 Fail-Closed、`checked_add` 防溢位、`catch_unwind` 保護 FFI 邊界、AFL++ 搭配 ASan/UBSan 覆蓋異常分支 |

---

## 二、OWASP API Security Top 10:2023 與本書章節對照表

截至 2026-11，**OWASP API Security Top 10:2023** 仍為 API 安全領域之現行正式標準，與本書 Part I–III 的 NexusPay 多租戶 API 閘道實驗直接對應：

| OWASP API Top 10:2023 編號與名稱 | 核心破口原語 | 對應本書章節 | NexusPay 審計與修補要點 |
|---|---|---|---|
| **API1:2023 — Broken Object Level Authorization（BOLA）** | 端點接收物件 ID（如 `:account_id`、`:report_id`），卻未驗證當前呼叫者的 `jwt.tenant_id` / `sub` 是否擁有該物件 | **Ch06**, **Ch07**, **Ch28**, **Ch34** | 以 `TenantDbClient` 強制綁定 `AuthContext.tenantId` 並啟用 PostgreSQL RLS；以 CodeQL 查詢未帶 `tenant_id` 之資料表存取 |
| **API2:2023 — Broken Authentication** | JWT 驗簽瑕疵、JWKS 快取投毒（`300 s` 視窗）、OAuth 授權碼外洩、Refresh Token 併發重用、SAML XSW 與 MFA 跳步 | **Ch04**, **Ch05** | 鎖定 `RS256`、`kid` 格式白名單、Refresh Token 單條原子 `UPDATE` 輪換、WebAuthn `origin`/`rpIdHash` 強驗證 |
| **API3:2023 — Broken Object Property Level Authorization（BOPLA）** | 包含 **Mass Assignment**（寫入未授權屬性如 `feeRate: 0`, `isVerified: true`）與 **Excessive Data Exposure**（回應外洩內部敏感欄位） | **Ch06**, **Ch07**, **Ch13** | 讀寫分離之嚴格 DTO 白名單（禁止將 Request Body 直接塞入 ORM `update()`），拒絕未知屬性並攔截 `__proto__` |
| **API4:2023 — Unrestricted Resource Consumption** | GraphQL 巢狀深度（突破 `8` 層）與 Alias 批次放大（`20` 個操作 × 指數關聯）、ReDoS 阻塞 Node.js 事件迴圈、ZIP Bomb 與超長 TLV 封包 | **Ch07**, **Ch09**, **Ch13**, **Ch14**, **Ch25** | GraphQL AST 靜態查詢複雜度上限、線性正則引擎 `re2`、檔案解壓大小與數量硬上限、FFI `len <= 65,536 bytes` 檢查 |
| **API5:2023 — Broken Function Level Authorization（BFLA）** | 一般商戶或操作員角色呼叫管理員路由（如 `/v1/admin/...`）、利用 HTTP Method 切換或未掛載 Guard 的新路由越權執行管理功能 | **Ch06**, **Ch34** | 全域預設拒絕（Default-Deny）授權攔截器；啟動期與 CI 掃描所有路由 Metadata，未宣告 `@Policy` 或 `@PublicEndpoint` 即阻斷建置 |
| **API6:2023 — Unrestricted Access to Sensitive Business Flows** | 自動化腳本或 HTTP/2 單封包併發（`20` 請求 `< 1 ms` 抖動）濫用提領、轉帳、優惠券兌換或 OTP 驗證流程，打破商業不變量 | **Ch12**, **Ch14** | 條件式原子扣款 SQL、強制 `Idempotency-Key` 唯一約束、綁定業務實體（`merchant_id` / `account_id`）而非僅依賴 `X-Forwarded-For` 的限流器 |
| **API7:2023 — Server Side Request Forgery（SSRF）** | Webhook 測試、發票匯入、頭像抓取或 AI Agent 工具呼叫被誘導連線至內部微服務或雲端 IMDS（`169.254.169.254`） | **Ch09**, **Ch11**, **Ch16**, **Ch18**, **Ch34** | 使用 Socket 層單次 DNS 解析＋IP Pinning＋停用自動重導向之 `SafeHttpClient`，搭配 K8s Egress NetworkPolicy 與 IMDSv2 |
| **API8:2023 — Security Misconfiguration** | 反向代理與後端解析／逾時分歧、CORS 萬用字元配憑證、gRPC Reflection 裸露、快取鍵遺漏敏感標頭 | **Ch03**, **Ch07**, **Ch10**, **Ch11**, **Ch14** | 統一前後端 HTTP 正規化與逾時階層、嚴格比對 CORS Origin 白名單、移除生產環境除錯端點 |
| **API9:2023 — Improper Inventory Management** | 未記錄於公開 OpenAPI 文件的舊版路由（`/v0/...`）、內部測試端點（`/internal/debug`）或影子微服務仍暴露於公網閘道 | **Ch01**, **Ch02**, **Ch34** | 結合黑箱 Soft-404 探測與白箱路由表靜態匯出比對，確保 OpenAPI 規格由程式碼路由定義單一來源自動生成 |
| **API10:2023 — Unsafe Consumption of APIs** | 無條件信任上游第三方 API、IdP 回呼、外部 Webhook 或 RAG 外部文件內容，未做結構驗證、重放保護與執行時期隔離即寫入資料庫或交由 Agent/FFI 執行 | **Ch05**, **Ch09**, **Ch11**, **Ch16**, **Ch25**, **Ch32** | 將所有外部 API 與合作夥伴回呼視為不可信 Source：強制驗簽與時間戳防重放、Schema 驗證、外部檔案於沙箱子行程解析、AI 工具層實施確定性權限閘門 |

---

## 三、MITRE CWE Top 25（2025–2026 基準版）與本書章節速查表

下表涵蓋 MITRE CWE Top 25 最危險軟體弱點（基於近 40,000 筆 CVE 與 CISA KEV 實戰權重），列出每一項 CWE 在本書的深入剖析章節、底層破口機制與自動化偵測方法（CodeQL / Semgrep / Fuzzing）：

| 排名區間與 CWE 編號 | CWE 正式名稱與台灣工程術語 | 對應本書章節 | 底層破口機制與自動化挖掘策略 |
|---|---|---|---|
| **CWE-79** | Cross-site Scripting（XSS，跨站腳本攻擊） | **Ch10**, **Ch16** | DOM Sink（`innerHTML`、未驗來源之 `postMessage`）、SVG/檔案上傳、LLM 輸出未淨化渲染；以 Strict CSP 與上下文感知編碼防禦 |
| **CWE-89** | SQL Injection（SQL 注入） | **Ch02**, **Ch08**, **Ch28**, **Ch34** | 字串插值拼接 SQL、ORM `orderBy` / `$queryRawUnsafe` 殘留面；以 CodeQL `TaintTracking` 追蹤 Request Source 至 SQL Sink |
| **CWE-352** | Cross-Site Request Forgery（CSRF，跨站請求偽造） | **Ch07**, **Ch10** | 狀態變更請求僅依賴自動攜帶之 Cookie（含 `SameSite=Lax` 頂層導航例外與 WebSocket CSWSH）；強制 Anti-CSRF Token / `Origin` 驗證 |
| **CWE-862** | Missing Authorization（缺少授權檢查） | **Ch06**, **Ch07**, **Ch16**, **Ch34** | 新增路由、GraphQL Resolver 或 AI Agent 工具忘記掛載權限檢查（BFLA / BOLA）；以全域 Fail-Closed 中介層與啟動期路由斷言根治 |
| **CWE-787** | Out-of-bounds Write（記憶體越界寫入） | **Ch20**, **Ch21**, **Ch25**, **Ch29**, **Ch30**, `ch22–ch24, ch26–ch27 [尚未完稿預留章節]` | 堆疊／堆積緩衝區溢位、FFI 長度算術回繞後 `memcpy`；以 AFL++ / `cargo-fuzz` 搭配 AddressSanitizer（ASan）自動化捕捉 |
| **CWE-22** | Path Traversal（路徑穿越） | **Ch04**, **Ch09**, **Ch10** | `../` 序列未正規化、`startsWith` 漏尾斜線、Zip Slip 歸檔路徑逃逸、JWT `kid` 檔案路徑注入與客戶端 CSPT |
| **CWE-416** | Use After Free（UAF，釋放後重用） | **Ch25**, **Ch29**, `ch23, ch24, ch27 [尚未完稿預留章節]` | 錯誤分支提前 `free()` 未清空指標、Rust FFI / Node.js N-API 跨界記憶體與 GC 生命週期競爭；以 ASan 與 Miri 偵測 |
| **CWE-78** | OS Command Injection（作業系統命令注入） | **Ch08**, **Ch13**, **Ch19** | 呼叫 `exec`/`system` 拼接字串、Prototype Pollution 污染 `child_process` 的 `shell`/`NODE_OPTIONS`，或 GitHub Actions `run:` 插值注入 |
| **CWE-94** | Code Injection（程式碼注入 / SSTI） | **Ch08**, **Ch13**, **Ch19** | 伺服器端模板注入（SSTI）、動態 `eval`/`Function`、CI/CD 腳本注入 |
| **CWE-20** | Improper Input Validation（輸入驗證不當） | **Ch01**, **Ch03**, **Ch07**, **Ch14**, **Ch25** | 未校驗協定欄位不變量、Protobuf/TLV 長度與型別邊界，或僅依賴前端／WAF 表層過濾 |
| **CWE-125** | Out-of-bounds Read（記憶體越界讀取） | **Ch20**, **Ch21**, **Ch25**, **Ch29** | TLV `len` 大於實際接收 Buffer 長度導致讀取相鄰堆積記憶體外洩位址或密鑰；以 ASan 搭配 Fuzzing 秒級檢出 |
| **CWE-287** | Improper Authentication（身分驗證不當） | **Ch04**, **Ch05** | JWT 演算法混淆（`RS256 → HS256`）、SAML XSW 簽章繞過、WebAuthn Challenge 重放、MFA 狀態機跳步 |
| **CWE-434** | Unrestricted Upload of File with Dangerous Type（危險檔案上傳） | **Ch09** | 僅驗 `Content-Type` 或副檔名黑名單，遭 Polyglot 檔案、SVG XSS、設定檔覆寫或影像解析器 RCE 突破 |
| **CWE-502** | Deserialization of Untrusted Data（不安全反序列化） | **Ch13** | 反序列化不可信 JSON/YAML/二進位物件觸發 Gadget Chain，或透過 `__proto__` 污染原型鏈達成 RCE |
| **CWE-863** | Incorrect Authorization（授權邏輯錯誤） | **Ch06**, **Ch07**, **Ch17**, **Ch18** | 有做權限檢查但邏輯有誤（如只驗 `jwt.tid == param.tid` 卻未驗目標資源歸屬該 `tid`、K8s RBAC 賦予 `pods/create`、IAM `PassRole` 萬用資源） |
| **CWE-918** | Server-Side Request Forgery（SSRF，伺服器端請求偽造） | **Ch11**, **Ch18**, **Ch34** | URL 解析器差異、替代 IP 表示法、302 重導向與 DNS Rebinding 繞過黑名單，存取內網與雲端 IMDS |
| **CWE-119** | Improper Restriction of Operations within Memory Buffer（記憶體緩衝區邊界限制不當） | **Ch20**, **Ch21**, **Ch25**, **Ch29**, `ch22–ch24 [尚未完稿預留章節]` | C/C++ 與 Rust `unsafe` 指標算術越界、未檢查陣列索引上限 |
| **CWE-476** | NULL Pointer Dereference（空指標解參考） | **Ch25**, **Ch29**, **Ch31** | `malloc` 失敗回傳 `NULL` 未檢查，或傳入 `null` 指標給 `slice::from_raw_parts` 引發 UB 與服務崩潰（DoS） |
| **CWE-798** | Use of Hard-coded Credentials（寫死金鑰與憑證） | **Ch04**, **Ch15**, **Ch19**, **Ch34** | 原始碼或容器映像檔內嵌靜態 JWT Secret、API Key 或長效雲端金鑰；以 Pre-commit / PR Secret Scanning 與自動撤銷防禦 |
| **CWE-190** | Integer Overflow or Wraparound（整數溢位或回繞） | **Ch21**, **Ch25**, **Ch29**, **Ch30** | `uint32` 長度 `len + 8` 或 `count * size` 溢位回繞為極小值，繞過上限檢查並配置過小堆積空間；強制使用 `checked_add` / `checked_mul` |
| **CWE-362** | Concurrent Execution using Shared Resource with Improper Synchronization（競爭條件 / TOCTOU） | **Ch04**, **Ch11**, **Ch12**, **Ch25** | HTTP/2 單封包雙花提領、Refresh Token 併發輪換、DNS Rebinding 檢查與連線時序差、多執行緒共享記憶體 Data Race |
| **CWE-276 / CWE-269** | Incorrect Default Permissions / Improper Privilege Management（權限配置與管理不當） | **Ch17**, **Ch18**, **Ch19** | 容器預設以 `root` 執行、自動掛載預設 SA Token、GitHub Actions `GITHUB_TOKEN` 預設讀寫權限過大 |
| **CWE-611** | Improper Restriction of XML External Entity Reference（XXE，XML 外部實體注入） | **Ch09** | XML / SAML / 發票匯入解析器未禁用外部 DTD 與參數實體，導致本機任意檔案讀取與內網 SSRF |
| **CWE-400 / CWE-1333** | Uncontrolled Resource Consumption / Inefficient Regular Expression Complexity（資源耗盡與 ReDoS） | **Ch07**, **Ch13**, **Ch29** | 指數回溯正則阻塞 Node.js 單執行緒事件迴圈、GraphQL Alias 查詢放大、解析器無窮迴圈 |
| **CWE-444** | Inconsistent Interpretation of HTTP Requests（HTTP 請求走私） | **Ch03**, **Ch11**, **Ch14** | 前後端對 `Content-Length`、`Transfer-Encoding` 或 HTTP/2 降級標頭解析分歧，污染 Keep-Alive 連線池 |

---

## 四、CVSS v4.0 + EPSS + CISA KEV 嚴重度量化與 SLA 分流速查表

FIRST 於 2023-11 正式發布 **CVSS v4.0**（對齊 `_meta/landscape-2026-11.md` 與 `ch33 [尚未完稿預留章節]`、`ch34`、`ch36`）。相較於舊版 v3.1，CVSS v4.0 廢除了籠統的 `Scope (S:U/C)`，改為：
1. 新增 **Attack Requirements（`AT:N/P`）**：精確區分「無額外前置條件（`AT:N`）」與「依賴目標端特定部署配置或微秒級競爭條件視窗（`AT:P`）」。
2. 將影響面明確拆分為 **Vulnerable System（受漏洞影響系統本身：`VC` / `VI` / `VA`）** 與 **Subsequent System（跨邊界受牽連之下游系統：`SC` / `SI` / `SA`）**。

### 1. CVSS v4.0 Base 指標群速查表

| 指標群組 | 指標名稱與代號 | 可選值與判定標準（資安工程實務判準） |
|---|---|---|
| **Exploitability（可利用性）** | **Attack Vector (`AV`)** | `N`（Network，可由公網 HTTP/API 觸發）、`A`（Adjacent）、`L`（Local，需本機/容器內執行）、`P`（Physical） |
| **Exploitability（可利用性）** | **Attack Complexity (`AC`)** | `L`（Low，攻擊者可穩定構造輸入）、`H`（High，需繞過未知動態隨機化如未洩漏之 `28-bit` ASLR 或目標端特製防禦） |
| **Exploitability（可利用性）** | **Attack Requirements (`AT`)** | `N`（None，預設狀態即可觸發）、`P`（Present，依賴併發競爭視窗、特定快取命中時序或中間人位置） |
| **Exploitability（可利用性）** | **Privileges Required (`PR`)** | `N`（None，匿名可達）、`L`（Low，需一般商戶／租戶測試帳號）、`H`（High，需管理員權限） |
| **Exploitability（可利用性）** | **User Interaction (`UI`)** | `N`（None，純伺服器端觸發）、`P`（Passive，受害者僅需瀏覽頁面）、`A`（Active，受害者需點擊確認或上傳特定檔案） |
| **Vulnerable System Impact（當前系統影響）** | **Confidentiality (`VC`)**<br>**Integrity (`VI`)**<br>**Availability (`VA`)** | `H`（High，完全控制／全表讀取／行程崩潰）、`L`（Low，受限範圍讀寫／局部延遲）、`N`（None，對當前元件無直接影響） |
| **Subsequent System Impact（下游系統影響）** | **Confidentiality (`SC`)**<br>**Integrity (`SI`)**<br>**Availability (`SA`)** | `H` / `L` / `N`：評估突破當前元件後，對**下游獨立信任邊界**（如由 Webhook SSRF 竊取雲端 IAM 憑證進而讀取生產資料庫，或由 AI Agent 越權操作帳務核心）造成的機密性、完整性與可用性損害 |

### 2. NexusPay 典型漏洞之 CVSS v4.0 向量實算範例

```text
[案例 1：NexusPay Webhook SSRF 串接雲端 IMDSv1 竊取生產資料庫密鑰（Ch11 + Ch18）]
- 條件：一般已登入商戶（PR:L）註冊惡意 Webhook URL，無須額外競爭條件（AC:L / AT:N / UI:N）。
- 影響拆分：
  * Vulnerable System（Webhook 派發 Worker 本身）：僅被用作網路跳板，自身記憶體未損毀 -> VC:L/VI:N/VA:N
  * Subsequent System（雲端 IAM 控制平面與生產帳本資料庫）：遭竊取 Role 憑證並完整讀取跨租戶帳本 -> SC:H/SI:H/SA:N
- CVSS v4.0 向量：
  CVSS:4.0/AV:N/AC:L/AT:N/PR:L/UI:N/VC:L/VI:N/VA:N/SC:H/SI:H/SA:N
  （基準分數：8.6 High；若結合公開可達與 EPSS >= 0.1 則升級為 24 小時 SLA）

[案例 2：NexusPay HTTP/2 單封包併發提領雙花（Ch12）]
- 條件：已登入商戶（PR:L）利用 HTTP/2 單封包同步送出 20 個請求（到達抖動 < 1 ms），需滿足資料庫交易交錯時序（AT:P）。
- 影響拆分：直接破壞帳本核心完整性（突破 10,000 分提領上限造成財務損失），無下游跨系統跳板 -> VC:N/VI:H/VA:N/SC:N/SI:N/SA:N
- CVSS v4.0 向量：
  CVSS:4.0/AV:N/AC:L/AT:P/PR:L/UI:N/VC:N/VI:H/VA:N/SC:N/SI:N/SA:N

[案例 3：libnexus-parse 未認證 TLV 長度整數回繞導致堆積溢位 RCE（Ch25 + Ch29）]
- 條件：外部匿名端點直接將二進位封包傳入 FFI（AV:N / PR:N / UI:N），len = 0xFFFF_FFF8 + 8 回繞觸發越界寫入奪取 API 伺服器控制權並連帶存取資料庫。
- CVSS v4.0 向量：
  CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:H/SI:H/SA:H
  （基準分數：10.0 Critical -> 立即啟動 24 小時緊急止血 SLA）
```

### 3. 企業 AppSec 三維分流與修復 SLA 決策矩陣（對齊 `_meta/running-examples.md` 與 Ch34）

實務上絕不可單靠靜態 CVSS 分數派工，必須結合 **可達性分析（Reachability）**、**EPSS（Exploit Prediction Scoring System，未來 30 天實戰被利用機率）** 與 **CISA KEV（已知被活躍利用漏洞目錄）**：

| 優先級與 SLA 門檻 | 判定條件（必須同時評估可達性與威脅情報） | 標準工程處置動作 |
|---|---|---|
| **P0 — 嚴重（Critical）**<br>**修復 SLA：`24 小時`** | 生產環境**外部可達（Reachable）**，且滿足任一項：<br>1. 列入 **CISA KEV** 或已觀測到線上活躍利用<br>2. **CVSS v4.0 ≥ 9.0** 且 **EPSS `≥ 0.1`**（10%）<br>3. 直接破壞核心資產不變量（跨租戶帳本竄改、RCE、雲端生產密鑰外洩） | 1. `0–15 分鐘`：開啟 Feature Flag 停用受影響端點、套用閘道緊急阻斷規則或輪換外洩金鑰，同時保留鑑識日誌。<br>2. `24 小時內`：部署熱修（Hotfix）並執行歷史資料完整性回溯清查；逾期未緩解則自動凍結該服務非安全相關之部署。 |
| **P1 — 高危（High）**<br>**修復 SLA：`7 天`** | 生產環境**可達（Reachable）**，且滿足任一項：<br>1. **CVSS v4.0 7.0–8.9**（或具備 **EPSS `≥ 0.1`** 之可達中危漏洞）<br>2. 需特定前置條件（`AT:P` 或 `PR:L`）之 BOLA、SSRF、高併發競爭或容器逃逸風險 | 1. 強制排入當週 Sprint 於 **`7 天` 內**完成根因修復。<br>2. 將單點修復轉化為 Paved Road 封裝與客製化 Semgrep / CodeQL CI 回歸規則（誤報率 `< 5%`）。<br>3. 若需展延，必須部署補償性控制並申請最長 `14–30 天` 自動到期之 Time-boxed Waiver。 |
| **P2 / P3 — 中低危或不可達**<br>**常規排程：`30–90 天`** | 1. 位於 `devDependencies` 或靜態呼叫圖確認生產環境**不可達（Unreachable）**（即使帳面 CVSS ≥ 9.0）<br>2. CVSS v4.0 < 7.0 且 **EPSS `< 0.1`**、無跨信任邊界實質危害 | 不觸發緊急傳呼、不中斷日常迭代；歸入定期相依套件更新或藉由全面推廣 Paved Road 框架批次消滅。 |
