# 《邊界失守：從後端系統到獨立漏洞挖掘與資安工程》大綱（Outline — 完整版 37 章）

- **書名**：邊界失守（副標：從後端系統到獨立漏洞挖掘與資安工程）
- **Slug / Registry ID**：`vuln-hunting` / `vuln`
- **書型（Form）**：`instructional`（六段固定骨架＋實作 Lab＋逐章靶場對照＋教學測試，內文採深度長文水準剖析機制與真實 CVE）
- **語言與語域**：`zh-TW` / `specialist`（資深後端工程師轉進獨立漏洞挖掘與資安工程）
- **總章節數**：37 章（6 大篇），外加完稿後由實作彙整的 4 份附錄（附錄 A：NexusPay 完整本地靶機與 Docker/QEMU 環境索引、附錄 B：開源專案 0-day 審計與黑箱 Bug Bounty 實戰 Checklist、附錄 C：CWE Top 25 / OWASP Top 10:2025 / API Top 10 / CVSS v4.0 速查表、附錄 D：AppSec / Product Security / VR 面試白板題庫與程式碼審計現場題）

---

## 一、貫穿全書的主軸（Spine）

**「邊界系統 NexusPay」**——一套參數固定、架構寫實的多租戶即時結算與 API 閘道平台。全書 37 章反覆回到它的四層實體邊界，展示「後端工程師每天寫出的正常系統，在攻擊者眼中如何逐層瓦解，又如何反向建構縱深防禦」：

1. **邊緣、協定與應用層（Ch01–Ch15）**：WAF/Nginx 反向代理 → Node.js（TypeScript）REST/GraphQL/gRPC/WebSocket API Gateway、SSO/Auth Service、檔案解析服務 → PostgreSQL 16（多租戶帳本）＋ Redis 7（Session／Rate Limit／分散式鎖）。
2. **AI 輔助、雲端與編排層（Ch16–Ch19）**：內建商戶客服與帳務查詢 AI Agent（Tool-Use/MCP + RAG）、Kubernetes 多租戶叢集、ServiceAccount/RBAC、雲端 IAM/IMDS 與 CI/CD 建置供應鏈。
3. **原生二進位、執行時期與核心層（Ch20–Ch27）**：以 Rust + C FFI 實作並透過 N-API 掛載至 Node.js 的二進位 TLV 解析與腳本沙箱 `libnexus-parse`（涵蓋無原始碼逆向、現代 `ptmalloc2` 進階堆積、V8 JIT/Ubercage 沙箱與宿主 Linux 核心 SLUB/`io_uring`/eBPF 邊界）。
4. **自動化挖掘、揭露與職涯收束（Ch28–Ch37）**：將跨層原語以 CodeQL、AFL++/`cargo-fuzz`、Z3/angr 混合式 Fuzzing 與 AI 輔助審計規模化，推向真實開源 0-day 與 Bug Bounty，並收束於企業 AppSec 防禦工程、NexusPay 端到端紅藍復盤、資安面試實戰與證照／Proof-of-Work 能力證明體系。

---

## 二、全書基準數字表（Base-Numbers Table — Single Source of Truth）

| 基準常數 | 數值與單位 | 所屬概念（NexusPay / 系統模型） | 引用章節 |
|---|---|---|---|
| NexusPay 閘道請求逾時 | `30 s`（Nginx `proxy_read_timeout`），Node.js `keepAliveTimeout = 5 s` | 反向代理與後端連線生命週期邊界 | Ch01, Ch03, Ch11, Ch12, Ch14 |
| NexusPay 帳戶餘額與併發規格 | 單戶測試餘額 `10,000`（整數分，即 `$100.00`）；單次提領上限 `10,000`；併發尖峰 `2,000 req/s` | 多租戶帳本不變量與競爭條件雙花分析 | Ch01, Ch06, Ch08, Ch12, Ch35 |
| JWT Access Token 規格 | RS256（2048-bit RSA），有效期 `900 s`（15 分鐘）；JWKS 快取 TTL `300 s` | 身分驗證與金鑰輪換邊界 | Ch04, Ch05, Ch06, Ch15 |
| GraphQL 查詢深度與批次上限 | 預設巢狀深度上限 `8` 層；單次 Batch 請求上限 `20` 個操作 | 非 REST API 資源耗盡與授權繞過邊界 | Ch07, Ch14 |
| 單封包併發視窗（HTTP/2） | 同連線最後 1 位元組同步送達 `20` 個請求，伺服器端到達抖動 `< 1 ms` | Single-Packet Attack 與 TOCTOU 視窗量化 | Ch03, Ch12, Ch35 |
| 64 位元 x86_64 堆疊與堆積對齊 | 指標寬度 `8 bytes`；Stack / `ptmalloc2` chunk 最小對齊 `16 bytes`；最小可用 chunk 大小 `32 bytes`（`0x20`） | 二進位記憶體佈局與堆積利用 | Ch20, Ch22, Ch23, Ch24, Ch25 |
| Linux x86_64 ASLR 熵位元數 | 使用者空間 `mmap` / 堆積典型隨機化 `28 bits`（頁大小 `4 KiB = 4,096 bytes`，`12 bits` 頁內偏移固定） | 記憶體隨機化暴力猜測成本與資訊洩漏必要性 | Ch20, Ch22, Ch23, Ch27 |
| `ptmalloc2` tcache 容量與 Safe-Linking | 每條 tcache bin 上限 `7` 個 chunk（涵蓋 `0x20`–`0x410` 共 `64` bins）；Safe-Linking 掩碼為 `(pos >> 12) ^ ptr` | glibc 現代堆積緩解與繞過推導 | Ch23, Ch24, Ch25 |
| `libnexus-parse` TLV 封包規格 | 檔頭固定 `8 bytes`（`magic: 2B`、`type: 2B`、`len: 4B` uint32）；合法 payload 上限 `65,536 bytes`（`64 KiB`） | Rust/C FFI 解析邊界、逆向與 Fuzzing 目標 | Ch20, Ch21, Ch25, Ch28, Ch29, Ch30 |
| V8 Sandbox（Ubercage）位址空間 | 保留 `1 TiB` 連續虛擬位址空間；內部壓縮指標為 `32 bits` 相對偏移 | 現代執行時期記憶體隔離邊界 | Ch13, Ch26 |
| Linux 核心除錯與 SLUB 基準 | x86_64 頁大小 `4 KiB`；SLUB 常見物件快取級距 `kmalloc-32` 至 `kmalloc-4096`（2 的冪次對齊） | 核心堆積噴灑與隔離邊界 | Ch17, Ch27 |
| AES-GCM 規格與 Nonce 限制 | 區塊大小 `128 bits`（`16 bytes`）；標準 Nonce `96 bits`（`12 bytes`）；同金鑰下 Nonce 重用立即洩漏 GHASH 驗證金鑰 `H` | 實務密碼學破口與認證加密邊界 | Ch04, Ch15 |
| AFL++ 覆蓋率位圖規格 | 預設邊緣覆蓋率 map 大小 `65,536 bytes`（`64 KiB`）；單核 Persistent Mode 基準吞吐 `5,000 exec/s` | 灰箱 Fuzzing 覆蓋率收斂與效能瓶頸 | Ch29, Ch30, Ch31 |
| 漏洞修復與分流門檻 | 高危 SLA `7 天`、嚴重 SLA `24 小時`；CVSS v4.0 搭配 EPSS `≥ 0.1` 或列入 CISA KEV 視為立即處置 | 漏洞揭露、嚴重度評定與 AppSec 治理 | Ch33, Ch34, Ch35, Ch36 |

---

## 三、橋接登記表與淡出排程（Bridge Registry & Fade-out）

- **前三分之一（Ch01–Ch12）**：外部後端機制橋接上限每章 1 個；任何來源全書 ≤3 次。
- **中三分之一（Ch13–Ch24）**：優先引用書內既有概念；僅在跨領域轉折使用外部橋接。
- **後三分之一（Ch25–Ch37）**：全面淡出（全部為 `none`），純用資安原生詞彙。

| 章節 | 淡出階段 | 核准橋接來源（機制對機制） | 累計使用次數 |
|---|---|---|---|
| ch01 | 前段 | 資料庫 ACID 不變量 → 安全不變量（Invariant） | DB 交易/不變量 (1/3) |
| ch02 | 前段 | 系統效能 Profiling（Flamegraph 找熱點）→ 攻擊面測繪與 Source-to-Sink 追蹤 | Profiling (1/3) |
| ch03 | 前段 | 分散式前後端序列化 Schema 漂移 → HTTP 解析器分歧（Parser Differential） | 解析/序列化 (1/3) |
| ch04 | 前段 | 分散式快取一致性與過期視窗 → Token / JWKS 驗證與撤銷失效 | 快取機制 (1/3) |
| ch05 | 前段 | `none`（承接 Ch04 驗證信任鏈直接剖析 SAML/WebAuthn 協定） | — |
| ch06 | 前段 | PostgreSQL Row-Level Security（RLS）→ 物件層級授權（BOLA）邊界 | DB 交易/不變量 (2/3) |
| ch07 | 前段 | RPC/GraphQL Resolver 執行樹 → 非 REST 查詢複雜度與授權破口 | 解析/序列化 (2/3) |
| ch08 | 前段 | AST 編譯階段與字串模板拼接 → 資料平面與控制平面混同（Injection） | 解析/序列化 (3/3) |
| ch09 | 前段 | `none`（直接以檔案系統 inode/symlink 與多層解析器狀態機推導） | — |
| ch10 | 前段 | 瀏覽器 Origin 隔離與容器命名空間隔離的結構邊界對照 | 行程/隔離 (1/3) |
| ch11 | 前段 | CDN/Nginx 快取鍵設計 → Web Cache Poisoning 的 Unkeyed Input | 快取機制 (2/3) |
| ch12 | 前段 | 資料庫 Isolation Level 與樂觀鎖 → TOCTOU 與單封包雙花攻擊 | DB 交易/不變量 (3/3) |
| ch13 | 中段 | `none`（直接以 JS Prototype 鏈與書內 Ch08 匯點模型推導） | — |
| ch14 | 中段 | `none`（承接 Ch03 解析分歧與 Ch11 快取層剖析 WAF/代理對抗） | — |
| ch15 | 中段 | `none`（直接以協定狀態機與位元組區塊推導密碼學實作破口） | — |
| ch16 | 中段 | `none`（以 Ch08 資料/控制平面混同延伸至 LLM Prompt 與 Tool-Use 邊界） | — |
| ch17 | 中段 | Linux 行程模型與容器 `chroot`/Namespace → 核心隔離逃逸邊界 | 行程/隔離 (2/3) |
| ch18 | 中段 | `none`（以 Ch06 授權圖與 Ch11 SSRF 延伸至雲端 IAM 控制平面） | — |
| ch19 | 中段 | CI/CD 建置管線 DAG → 供應鏈信任傳遞與投毒點 | CI/CD DAG (1/3) |
| ch20 | 中段 | 作業系統虛擬記憶體頁表 → ELF 與 64 位元行程位址空間 | 行程/隔離 (3/3) |
| ch21 | 中段 | `none`（直接以 Ch20 ELF 區段與呼叫慣例切入靜態反編譯） | — |
| ch22 | 中段 | `none`（直接以 Ch20 堆疊幀推導控制流劫持與 ROP） | — |
| ch23 | 中段 | `none`（直接以 `ptmalloc2` chunk 結構與位址算術推導） | — |
| ch24 | 中段 | `none`（承接 Ch23 tcache/unsorted bin 推導進階堆積利用） | — |
| ch25–ch37 | 後段 | `none`（全部原生詞彙） | — |

---

## 四、各章詳細規格（37 章）

### Part I — 攻擊者心智模型與邊界理論（Ch01–Ch03）

#### `ch01` — 信任邊界、攻擊面與漏洞的形式化模型
- **檔案**：`ch01-trust-boundaries.md`
- **目標**：建立「漏洞＝合法輸入打破系統隱含不變量」的工程化視角，能針對任意後端架構繪製信任邊界圖、Source-to-Sink 污點路徑與量化攻擊樹。
- **Must-cover**：信任邊界（Trust Boundary）、不變量違背模型、Source/Sink/Sanitizer 三元組、STRIDE 與攻擊樹量化、NexusPay 四層架構與初始威脅模型。
- **Must-NOT-cover**：具體漏洞利用手法（見 ch03–ch27）、CVSS v4.0 計算細節（見 ch33）。
- **Spine 接觸**：建立 NexusPay 完整架構圖、初始信任邊界與 `$100.00`（`10,000` 分）帳本不變量。
- **Worked example**：計算 NexusPay 提領 API 在 3 條信任邊界上的攻擊路徑成本與不變量破壞條件（具體狀態轉移表與數值驗證）。
- **Lab**：啟動 NexusPay 本地基準環境，盤點全部 HTTP/TCP/Redis/DB 暴露面並產出威脅矩陣。

#### `ch02` — 現代偵察、黑箱與白箱審計工作流
- **檔案**：`ch02-recon-and-audit-workflow.md`
- **目標**：掌握系統化的漏洞挖掘作業流程——黑箱如何從 HTTP 流量反推後端架構與隱藏端點，白箱如何在大型程式碼庫內 30 分鐘定位高危 Sink。
- **Must-cover**：MITM 代理（Burp/Caido 機制與 TLS 憑證信任鏈）、黑箱指紋識別與參數探測、白箱 Source-to-Sink 逆向審計法、攻擊面優先序排序。
- **Must-NOT-cover**：CodeQL/Semgrep 規則語法（見 ch28）、灰箱 Fuzzing（見 ch29）。
- **Spine 接觸**：對 NexusPay API Gateway 執行黑箱代理攔截＋白箱 TypeScript 原始碼路由盤點。
- **Worked example**：追蹤 `POST /v1/transfers` 從 Nginx → NestJS Guard/Pipe → Service → Raw SQL 的 5 層呼叫鏈與污點傳播表。
- **Lab**：本地 MITM 代理攔截 NexusPay 流量，找出 3 個未列於公開 OpenAPI 文件的內部端點；附 PortSwigger Recon/Proxy 基礎檢查點。

#### `ch03` — 協議解析差異與 HTTP 請求走私
- **檔案**：`ch03-http-smuggling.md`
- **目標**：從 RFC 9112/9113 線路格式推導前端代理與後端伺服器之間的解析分歧，獨立構造並偵測 CL.TE、TE.CL 與 H2.CL 請求走私。
- **Must-cover**：HTTP/1.1 Keep-Alive 連線複用、`Content-Length` 與 `Transfer-Encoding: chunked` 優先序歧義、HTTP/2 降級至 HTTP/1.1 的標頭注入、時間差探測法與緩解。
- **Must-NOT-cover**：Web Cache Poisoning 細節（見 ch11）、HTTP/2 Single-Packet 競爭條件（見 ch12）、WAF 繞過對抗（見 ch14）。
- **Spine 接觸**：剖析 NexusPay 的 Nginx（`30 s`）與 Node.js（`keepAliveTimeout = 5 s`）連線複用與請求切分邊界。
- **Worked example**：逐位元組計算一段 `CL.TE` 走私封包（精確 `Content-Length` 與 `0\r\n\r\n` 截斷點）。
- **Lab**：本地舊版代理＋Node.js 靶機以 Python raw socket 重現 CL.TE 繞過 `/internal/admin`；對應 PortSwigger *HTTP request smuggling* Practitioner/Expert 實驗檢查點。

---

### Part II — Web、API、現代協定與後端漏洞挖掘（Ch04–Ch14）

#### `ch04` — 身分驗證與會話機制破口
- **檔案**：`ch04-authentication-and-sessions.md`
- **目標**：拆解現代無狀態與有狀態驗證機制（JWT、OAuth 2.0/OIDC、Cookie/Session）的實作破口，能審計出簽章繞過、憑證劫持與重放漏洞。
- **Must-cover**：JWT Header 注入（`alg: none`、RS256→HS256 演算法混淆、`kid` 注入、`jku`/JWKS 快取投毒）、OAuth 2.0 Authorization Code 劫持（`redirect_uri` 解析差異、缺失 `state`/PKCE）、Session Fixation 與 Refresh Token 輪換競爭。
- **Must-NOT-cover**：SAML 2.0 與 WebAuthn（見 ch05）、底層密碼學實作側通道（見 ch15）。
- **Spine 接觸**：審計 NexusPay 的 RS256 JWT（`900 s` 過期、JWKS 快取 `300 s`）與 OAuth 登入回呼。
- **Worked example**：示範將 RS256 公鑰 PEM bytes 作為 HMAC-SHA256 密鑰偽造 `role: "admin"` JWT 的驗證條件對照與 Base64URL 計算。
- **Lab**：本地 NexusPay Auth Service 重現 `kid`/JWKS 偽造與 OAuth `redirect_uri` 竊碼；對應 PortSwigger *JWT attacks* 與 *OAuth authentication* 實驗檢查點。

#### `ch05` — 企業單點登入與認證深水區（SAML 2.0、WebAuthn 與 MFA 繞過）
- **檔案**：`ch05-enterprise-sso-and-mfa.md`
- **目標**：掌握 B2B 企業系統極高頻的 SAML 2.0 XML 簽章破口、WebAuthn/Passkey 驗證邊界與 MFA 邏輯繞過。
- **Must-cover**：SAML 2.0 Assertion 結構與 XML Signature Wrapping（XSW #1–#8 原理）、XML 註解截斷（`admin<!-- -->@corp.com`）、IdP-initiated vs SP-initiated 重放、WebAuthn/FIDO2 挑戰值（challenge）與 `rpId`/`origin` 驗證漏檢、MFA 狀態機跳步與備援碼暴力破解。
- **Must-NOT-cover**：XML External Entity（XXE 見 ch09）、基礎 JWT/OAuth（見 ch04）。
- **Spine 接觸**：審計 NexusPay 企業商戶後台的 SAML 2.0 SSO 整合與 MFA 提領確認流程。
- **Worked example**：比對同一份 SAML Response 在 XML Canonicalization（C14N）驗證器與 DOM `getElementsByTagName("NameID")[0]` 解析器下的節點選取分歧，精確標出 XSW 插入位置。
- **Lab**：在本地 NexusPay SAML SP 靶機構造 XSW 與註解截斷登入任意商戶管理員並修補；對應 PortSwigger *Authentication* 進階 MFA 繞過實驗檢查點。

#### `ch06` — 授權模型崩壞：BOLA、BFLA 與多租戶隔離失效
- **檔案**：`ch06-authorization-and-multitenancy.md`
- **目標**：系統化挖掘 OWASP API Top 10 榜首漏洞（BOLA/BOPLA/BFLA），並理解多租戶系統在 ORM、快取鍵與資料庫層的隔離失效模式。
- **Must-cover**：OWASP API1 BOLA、API3 BOPLA（Mass Assignment 與過度資料暴露）、API5 BFLA、多租戶 `tenant_id` 漏檢、防禦架構（集中式 Policy Engine、PostgreSQL RLS）。
- **Must-NOT-cover**：GraphQL 專屬授權與查詢攻擊（見 ch07）、SQL 語法注入（見 ch08）。
- **Spine 接觸**：審計 NexusPay 多租戶帳本 API（`/v1/tenants/:tid/accounts/:aid`）與 NestJS DTO 白名單過濾。
- **Worked example**：分析 4 角色 × 6 資源端點授權矩陣，計算跨租戶 UUID 替換與 `{"isVerified": true, "feeRate": 0}` 竄改結算手續費的帳本損失。
- **Lab**：撰寫自動化授權矩陣腳本掃描 NexusPay API，以 PostgreSQL RLS + 嚴格 DTO 修補；對應 PortSwigger *Access control vulnerabilities* 實驗檢查點。

#### `ch07` — 非 REST 現代後端協定安全（GraphQL、gRPC 與 WebSocket）
- **檔案**：`ch07-graphql-grpc-websocket.md`
- **目標**：針對現代微服務與即時系統常用的 GraphQL、gRPC/Protobuf 與 WebSocket，建立專屬的攻擊面盤點與漏洞挖掘方法。
- **Must-cover**：GraphQL Introspection/欄位推測、Alias Batching 繞過 Rate Limit、巢狀循環 DoS（突破深度 `8` 層／批次 `20` 筆限制）、Resolver 層級 BOLA；gRPC Reflection 暴露、Protobuf 未知欄位/整數編碼邊界與 Metadata 驗證缺失；WebSocket CSWSH（Cross-Site WebSocket Hijacking）與訊息層授權漏檢。
- **Must-NOT-cover**：HTTP/2 請求走私（見 ch03）、瀏覽器 SOP/CORS 基礎（見 ch10）。
- **Spine 接觸**：審計 NexusPay 的商戶即時報表 GraphQL 端點、內部帳務 gRPC 服務與即時到帳通知 WebSocket 閘道。
- **Worked example**：計算一個 5 層深度 × 每層 4 個關聯邊的 GraphQL 查詢搭配 `20` 個 Alias 展開後的資料庫查詢放大倍數（`20 × 4^5 = 20,480` 次 resolver 呼叫）。
- **Lab**：對 NexusPay GraphQL/WebSocket 靶機實作 Alias Batching 繞過與 CSWSH 劫持，並導入查詢成本分析與 Origin/Ticket 驗證；對應 PortSwigger *GraphQL* 與 *WebSockets* 實驗檢查點。

#### `ch08` — 注入家族的本質：資料與控制平面的混同
- **檔案**：`ch08-injection-families.md`
- **目標**：掌握 SQLi（含現代 ORM 殘留面與盲注）、NoSQL/Redis 協議注入、OS Command Injection 與 SSTI 的共通本質與進階利用。
- **Must-cover**：ORM（Prisma/TypeORM `orderBy`/raw fragment）SQLi、Boolean/Time-Based 盲注二分搜尋、Redis RESP 協議注入與 Lua 沙箱、Command Injection（`exec` vs `execFile`、Argument Injection `--`）、SSTI 模板沙箱逃逸。
- **Must-NOT-cover**：瀏覽器 DOM XSS（見 ch10）、Prototype Pollution（見 ch13）、Prompt Injection（見 ch16）。
- **Spine 接觸**：挖掘 NexusPay 報表排序參數的 PostgreSQL 時間盲注與 Redis 佇列鍵名注入。
- **Worked example**：推導 PostgreSQL 時間盲注以二分搜尋萃取 32 字元 hex token 的精確請求數（`32 × 4 = 128` 次 vs 線性平均 `272` 次）與網路抖動閾值。
- **Lab**：撰寫 Python 盲注萃取腳本並以白名單參數化修補；對應 PortSwigger *SQL injection* / *SSTI* / *OS command injection* Practitioner/Expert 檢查點。

#### `ch09` — 檔案處理、路徑穿越與複合解析器攻擊面
- **檔案**：`ch09-file-parsers-and-xxe.md`
- **目標**：掌握後端檔案上傳、解壓縮、XML 與多媒體處理管線中極易導致 RCE 或任意檔案讀寫的解析器漏洞。
- **Must-cover**：Path Traversal（正規化順序、`..` 編碼、前綴比對 `startsWith("/uploads")` 繞過 `/uploads-secret`）、Zip Slip 與 Tar Symlink 逃逸、XXE（Out-of-Band Exfiltration、盲注與 Error-Based）、SVG/PDF（SSRF/XSS/Headless Chrome 本機檔案讀取）與影像處理庫（ImageMagick/Ghostscript/libvips 委派與記憶體邊界）。
- **Must-NOT-cover**：底層 C 記憶體溢位利用細節（見 ch22–ch24）。
- **Spine 接觸**：審計 NexusPay 的商戶對帳單 ZIP 批次匯入、發票 XML/PDF 產生器與商戶 Logo 上傳管線。
- **Worked example**：構造一個惡意 ZIP 歸檔的檔名與中央目錄位元組結構（`../../../../app/config/webhook.json`）與一個含外部 DTD 的 OOB XXE payload，追蹤路徑拼接結果。
- **Lab**：在本地 NexusPay 檔案服務重現 Zip Slip 覆寫設定檔與 XXE 讀取本地密鑰，並實作 `path.resolve` 邊界檢核與禁用外部實體；對應 PortSwigger *Path traversal* / *XXE* / *File upload* 實驗檢查點。

#### `ch10` — 瀏覽器安全模型與客戶端攻擊鏈
- **檔案**：`ch10-browser-and-client-attacks.md`
- **目標**：精通瀏覽器核心安全不變量（SOP、CORS、CSP、SameSite），能將 DOM XSS、CSPT、CSRF 與 XS-Leaks 串接成帳號接管。
- **Must-cover**：SOP 精確邊界、CORS 錯誤配置、DOM XSS 與 `postMessage` 來源驗證缺失、CSP 剖析與繞過、CSRF 與 SameSite=Lax 例外、Client-Side Path Traversal（CSPT）與 XS-Leaks。
- **Must-NOT-cover**：V8 引擎記憶體損毀與 JIT 類型混淆（見 ch26）。
- **Spine 接觸**：審計 NexusPay 商戶管理後台 SPA、OAuth popup `postMessage` 與 CSP 標頭。
- **Worked example**：拆解含 `script-src 'self' https://cdn.example.com` 的 CSP，計算如何結合開放重導向與 DOM gadget 繞過並外洩敏感狀態。
- **Lab**：在 NexusPay 後台串接 `postMessage` + DOM XSS，改以 Nonce-based Strict CSP 修補；對應 PortSwigger *XSS* / *CORS* / *DOM-based* / *CSRF* Expert 檢查點。

#### `ch11` — SSRF、URL Parser 混淆與 Web Cache Poisoning / Deception
- **檔案**：`ch11-ssrf-parsers-and-cache.md`
- **目標**：掌握 URL Parser 差異造成的 SSRF 防護繞過，以及結合 CDN/Nginx 快取鍵缺陷的 Web Cache Poisoning 與 Cache Deception。
- **Must-cover**：WHATWG URL vs RFC 3986 差異、DNS Rebinding（TTL=0 時間視窗）、Blind SSRF、Web Cache Poisoning（Unkeyed Headers/Params）與 Web Cache Deception（路徑副檔名混淆）。
- **Must-NOT-cover**：雲端 IMDSv1/v2 與 IAM 提權（見 ch18）。
- **Spine 接觸**：審計 NexusPay Webhook 驗證器與 Nginx 靜態快取層。
- **Worked example**：對比 Node.js `url.parse()`、WHATWG `new URL()` 與 `curl` 對同一畸形 URL 的解析差異表與 DNS Rebinding 時序視窗。
- **Lab**：繞過 NexusPay Webhook 黑名單存取內網端點，並對 Nginx 快取投毒；對應 PortSwigger *SSRF* / *Web cache poisoning* / *Web cache deception* 檢查點。

#### `ch12` — 競爭條件、HTTP/2 單封包攻擊、分散式狀態機與商業邏輯漏洞
- **檔案**：`ch12-race-conditions-and-logic.md`
- **目標**：發掘自動化掃描器抓不到的高價值商業邏輯漏洞——利用 HTTP/2 單封包攻擊精準觸發 TOCTOU，打破資料庫隔離與分散式鎖不變量。
- **Must-cover**：TOCTOU 微秒視窗、HTTP/2 Single-Packet Attack（`20` 請求、`< 1 ms` 抖動）、PostgreSQL `READ COMMITTED` vs `SERIALIZABLE` 雙花、Redis `SET NX` 鎖失效、多步驟工作流跳步與精度套利。
- **Must-NOT-cover**：多執行緒 C/Rust 記憶體 Data Race（見 ch25）。
- **Spine 接觸**：直接攻擊 NexusPay 核心提領 API（餘額 `10,000` 分，單封包 `20` 併發提領）。
- **Worked example**：計算 `READ COMMITTED` 下 `20` 個併發提領在 `< 1 ms` 內同時讀到 `10,000` 分時的重複出金總額與交易交錯時序。
- **Lab**：用 Python HTTP/2 單封包腳本對 NexusPay 實測雙花並以原子扣款＋冪等鍵修補；對應 PortSwigger *Race conditions* 與 *Business logic* 實驗檢查點。

#### `ch13` — 反序列化、原型鏈汙染與 Node.js 執行時期漏洞
- **檔案**：`ch13-deserialization-and-nodejs-runtime.md`
- **目標**：深入動態語言與 Node.js 生態獨有的高危漏洞面——從 Prototype Pollution 尋找 RCE Gadget Chain、反序列化物件注入到 ReDoS。
- **Must-cover**：`__proto__`/`constructor.prototype` 深度合併汙染、伺服器端 Prototype Pollution → `child_process`/`NODE_OPTIONS`/模板 RCE Gadget、不安全反序列化（YAML/JSON reviver）、ReDoS 指數回溯與 Event Loop 飢餓。
- **Must-NOT-cover**：V8 C++ JIT 與 Ubercage 沙箱（見 ch26）。
- **Spine 接觸**：審計 NexusPay Node.js 閘道的深層設定合併函式與 Webhook 正則驗證器。
- **Worked example**：計算 `^(a+)+$` 在 `n = 28` 個 `'a'` 接 `'!'` 的回溯步數（`2^28 ≈ 2.68 × 10^8`）與阻塞時間；追蹤 `Object.prototype.shell` / `NODE_OPTIONS` gadget 路徑。
- **Lab**：在 NexusPay 設定端點觸發 Prototype Pollution → RCE，改用 `Object.create(null)`、`--disable-proto=throw` 與 RE2 修補；對應 PortSwigger *Prototype pollution* 與 *Insecure deserialization* 檢查點。

#### `ch14` — 防禦對抗與繞過技術（WAF、代理正規化與 Rate Limit 破口）
- **檔案**：`ch14-waf-and-defense-bypass.md`
- **目標**：理解真實線上目標與本地靶機的最大落差——為何教科書 payload 會被 WAF/CDN/Rate Limiter 擋下，以及如何從底層正規化差異系統化繞過與驗證真實防護效力。
- **Must-cover**：WAF 正則／簽章檢測 vs 語法解析器的結構限制、HTTP 參數汙染（HPP）、Multipart/JSON/Charset 編碼差異、Chunked/Oversized Body 截斷檢查上限（如 8 KiB / 128 KiB 檢查截斷）、IP/Token Rate Limit 繞過（`X-Forwarded-For` 信任鏈、IPv6 /64 輪換、端點大小寫與尾斜線正規化）。
- **Must-NOT-cover**：HTTP Request Smuggling 基礎（見 ch03）、GraphQL Batching（見 ch07）。
- **Spine 接觸**：在 NexusPay 前方掛載 ModSecurity/OWASP CRS 規則集與 Redis 滑動視窗限流器，進行攻防實測。
- **Worked example**：計算一段超過 WAF `8,192 bytes` 請求主體檢查上限的 JSON padding payload，如何讓後端 Express `body-parser`（預設上限 `100 KiB`）完整解析後段注入欄位。
- **Lab**：本地 Nginx + ModSecurity CRS 靶機實戰繞過預設規則集與錯誤設定的 `X-Forwarded-For` 限流器，接著從應用程式層根因修補而非只加 WAF 規則。

---

### Part III — 密碼學、AI 系統、雲端原生與供應鏈（Ch15–Ch19）

#### `ch15` — 密碼學工程實戰破口
- **檔案**：`ch15-applied-crypto-flaws.md`
- **目標**：從工程師實作密碼學原語時反覆犯下的致命錯誤切入，獨立識別並利用 Padding Oracle、AES-GCM Nonce Reuse、Timing Side-Channel 與弱 PRNG。
- **Must-cover**：AES-CBC Padding Oracle（PKCS#7 逐位元組解密）、AES-GCM（`128-bit` 區塊、`96-bit` Nonce）重複使用 Nonce 洩漏明文與 GHASH 金鑰 `H`、HMAC 非恆定時間比對、V8 `Math.random()`（xorshift128+）狀態預測、金鑰管理與輪換破口。
- **Must-NOT-cover**：純數論證明與後量子密碼學理論。
- **Spine 接觸**：審計 NexusPay 的加密 Webhook 簽章比對與加密 Cookie 模組。
- **Worked example**：推導 AES-CBC Padding Oracle 破解 `16-byte` 區塊的最壞查詢數（`4,096` 次，平均 `2,048` 次）與 AES-GCM Nonce 重用還原 `P1 ⊕ P2`。
- **Lab**：撰寫本地 Padding Oracle 解密腳本與微秒時間側通道量測腳本，遷移至隨機 Nonce AES-GCM 與 `timingSafeEqual`；對應 Cryptopals Set 2–3 關鍵關卡檢查點。

#### `ch16` — AI / LLM 與 Agent 系統攻擊面
- **檔案**：`ch16-ai-and-agent-security.md`
- **目標**：掌握 2026 年 AppSec / Product Security 必考的新興攻擊面——把資料/控制平面混同延伸至 LLM 提示注入、Agent Tool-Use/MCP 權限邊界與 RAG 多租戶隔離。
- **Must-cover**：Direct vs Indirect Prompt Injection（外部文件／Webhook 內容劫持 Agent 行為）、Excessive Agency 與 Tool-Use / MCP Server 參數注入（由自然語言觸發 SQLi/SSRF/未授權退款）、RAG 向量資料庫跨租戶檢索洩漏與文件投毒、系統提示外洩與防禦架構（確定性權限閘門、最小權限工具、Human-in-the-loop、輸出結構驗證）。
- **Must-NOT-cover**：模型權重對抗樣本（Adversarial ML 梯度攻擊）。
- **Spine 接觸**：審計 NexusPay 內建的商戶帳務查詢 AI Agent（透過 MCP 呼叫內部帳本與退款工具，並檢索多租戶 RAG 知識庫）。
- **Worked example**：追蹤一筆夾帶於商戶發票備註欄的 Indirect Prompt Injection，如何在缺乏確定性租戶權限邊界時誘導 Agent 呼叫 `issue_refund(account_id, amount=10000)` 並越權外洩他戶帳單。
- **Lab**：在本地模擬的 NexusPay Tool-Calling Agent 靶機重現 Indirect Prompt Injection 觸發未授權工具呼叫與 RAG 跨租戶洩漏，再以確定性 Policy Layer（獨立於 LLM 上下文的權限驗證）封堵；對應 PortSwigger *Web LLM attacks* 檢查點。

#### `ch17` — 容器隔離與 Kubernetes 權限提升
- **檔案**：`ch17-containers-and-kubernetes.md`
- **目標**：從 Linux 核心原語理解容器真實隔離邊界，能識別危險 Pod 設定、容器逃逸路徑與 Kubernetes RBAC 提權鏈。
- **Must-cover**：Namespaces、cgroups、Capabilities（`CAP_SYS_ADMIN`、`CAP_DAC_READ_SEARCH`、`CAP_BPF`）、seccomp-bpf、容器逃逸向量（`privileged`、`hostPath` 掛載 `docker.sock`/`/proc`）、ServiceAccount Token 自動掛載、RBAC 隱蔽提權（`pods/create`、`impersonate`、`bind`/`escalate`）。
- **Must-NOT-cover**：Linux 核心記憶體漏洞利用（見 ch27）、雲端帳號級 IAM 提權（見 ch18）。
- **Spine 接觸**：審計 NexusPay K8s Worker Pod、Ingress 與 RBAC 配置。
- **Worked example**：在 5 個 ServiceAccount × 4 條 RoleBinding 權限圖中，推導從低權限 `worker-sa` 透過 `pods/create` 掛載節點根目錄完成 Cluster-Admin 提權的最短 3 步路徑。
- **Lab**：本地 `kind` 叢集部署弱化版 NexusPay manifests，演練 Pod 橫向取得 Secret 並套用 Pod Security Standards（Restricted）修補。

#### `ch18` — 雲端 IAM、中繼資料服務與橫向移動
- **檔案**：`ch18-cloud-iam-and-lateral-movement.md`
- **目標**：將 SSRF 與工作負載入侵銜接至雲端控制平面，系統化評估 IAM 權限圖、中繼資料防護與跨帳號橫向移動。
- **Must-cover**：IMDSv1 vs IMDSv2（PUT Token + Hop Limit 1）、IAM 策略評估邏輯（Explicit Deny > Allow）、經典提權原語（`iam:PassRole` + Compute、`sts:AssumeRole` 信任策略寬鬆、`lambda:UpdateFunctionCode`）、物件儲存暴露與 CloudTrail 偵測。
- **Must-NOT-cover**：多雲 UI 操作清單。
- **Spine 接觸**：模擬 NexusPay 經由 Webhook SSRF 觸及中繼資料服務並串接角色權限存取帳本備份儲存桶。
- **Worked example**：分析 IAM Policy JSON，推導 `iam:PassRole` 搭配 `Resource: "*"` 如何將開發部署權限升級為讀取生產密鑰。
- **Lab**：本地容器化雲端模擬器（LocalStack / IAM 路徑分析）演練 IMDSv1 竊取與角色提權，並標註銜接 CloudGoat / Flaws2 的零風險延伸路徑。

#### `ch19` — 軟體供應鏈與 CI/CD 管線攻防
- **檔案**：`ch19-supply-chain-and-cicd.md`
- **目標**：掌握從依賴套件到 CI/CD 建置與映像檔發佈的供應鏈攻擊面，能審計管線注入與套件投毒。
- **Must-cover**：npm / Cargo Dependency Confusion、Lockfile 篡改與 `postinstall`/`build.rs` 建置期執行、GitHub Actions `pull_request_target` 結合 PR 標題/分支名 Script Injection、Runner Secret 外洩、OIDC 無長效金鑰部署、SLSA、Sigstore/Cosign 簽章與 SBOM。
- **Must-NOT-cover**：執行期應用 RCE（見 ch08/ch13）。
- **Spine 接觸**：審計 NexusPay monorepo（TS + Rust/C）CI/CD 建置與映像檔發佈管線。
- **Worked example**：逐行拆解含 `${{ github.event.pull_request.title }}` 的 workflow，示範 45 字元 PR 標題注入竊取 `NPM_TOKEN` 與影響半徑。
- **Lab**：本地建置私有 npm 代理與模擬 CI runner，重現 Dependency Confusion 與 workflow 注入並以 commit SHA 鎖定與安全環境變數修補。

---

### Part IV — 逆向工程、記憶體安全、FFI 與現代系統利用（Ch20–Ch27）

#### `ch20` — 二進位執行環境與記憶體佈局
- **檔案**：`ch20-binary-and-memory-layout.md`
- **目標**：建立閱讀 ELF、x86_64/ARM64 組合語言與行程虛擬記憶體佈局的紮實能力，理解四大基礎緩解（NX、ASLR、Stack Canary、PIE/RELRO）。
- **Must-cover**：ELF 區段（`.text`/`.data`/`.bss`/`.got`/`.plt`）、x86_64 System V ABI（暫存器傳參、`16-byte` 堆疊對齊與 Stack Frame）、虛擬記憶體頁權限（R/W/X）、NX、ASLR（`28-bit` 熵與 `4 KiB` 頁偏移不變）、Stack Canary（`0x00` 首字節）與 Full/Partial RELRO。
- **Must-NOT-cover**：靜態反編譯逆向工程（見 ch21）、ROP 與堆積細節（見 ch22–ch24）。
- **Spine 接觸**：首次進入 NexusPay 原生模組 `libnexus-parse`（C 基準版），觀察 `8-byte` TLV 檔頭在記憶體中的實際位元組排列。
- **Worked example**：計算 `28-bit` ASLR 空間（`2^28 = 268,435,456`）在 `1,000 req/s` 下的期望暴力猜測耗時（約 `1.34 × 10^5` 秒 ≈ 1.55 天），論證 Info Leak 的必要性。
- **Lab**：用 `readelf`、`objdump`、`checksec`、`gdb`（pwndbg）解剖 `libnexus-parse`；對應 pwn.college *Program Security / Assembly & Debugging* 模組檢查點。

#### `ch21` — 無原始碼逆向工程實戰
- **檔案**：`ch21-reverse-engineering.md`
- **目標**：擺脫「只能審計有原始碼的專案」的限制，能對 stripped ELF 二進位檔進行靜態反編譯、資料結構還原與漏洞點快速定位。
- **Must-cover**：Ghidra 反編譯器運作原理（P-code 與 SSA 還原）、Stripped Binary 識別函式邊界與標準庫（FLIRT/FIDB 簽章）、從組合語言還原 `struct` 偏移與陣列索引、交叉引用（XREF）由危險 Sink（`memcpy`/`strcpy`/`malloc`）逆推輸入來源、靜態分析與 GDB 動態驗證交互印證。
- **Must-NOT-cover**：Windows PE 加殼／反除錯保護（超出版面範圍，僅簡要提及差異）。
- **Spine 接觸**：針對刻意移除偵錯符號（`strip -s`）的 `libnexus-parse.so` 發布版二進位檔，無原始碼還原其 TLV 結構與隱藏的除錯 opcode 分支。
- **Worked example**：給定一段 18 行 x86_64 組合語言（含 `[rdi+0x4]`、`shl eax, 3`、`call malloc`），逐步還原 C 結構體欄位偏移表與整數溢位條件。
- **Lab**：在 Ghidra 載入 stripped `libnexus-parse.so`，還原完整 struct 定義並找出隱藏漏洞函式；對應 pwn.college *Reverse Engineering* 模組檢查點。

#### `ch22` — 堆疊溢位、控制流劫持與 ROP 鏈構造
- **檔案**：`ch22-stack-overflow-and-rop.md`
- **目標**：理解從緩衝區溢位到繞過 NX/ASLR/Canary 的完整控制流劫持推導，能獨立構造 Ret2libc 與 ROP 鏈。
- **Must-cover**：堆疊溢位與 Saved RIP 覆寫、Format String 資訊洩漏與任意寫、Ret2libc 與 ROP Gadget 串接、x86_64 `movaps` `16-byte` 堆疊對齊陷阱、Stack Pivoting、硬體／編譯器防禦（Intel CET Shadow Stack、ARM PAC、CFI）。
- **Must-NOT-cover**：堆積管理器與 UAF（見 ch23–ch24）。
- **Spine 接觸**：剖析 `libnexus-parse` C 版未檢查 `len <= 65,536` 的堆疊複製破口。
- **Worked example**：精確計算 `buf[64]` 到 Saved RIP 的偏移（`64 + 8 + 8 = 80 bytes`）與含對齊 `ret` gadget、`pop rdi; ret`、`"/bin/sh"`、`system@libc` 的完整 64 位元 ROP payload。
- **Lab**：對開啟 NX+ASLR+Canary 的 `libnexus-parse` 用 `pwntools` 串接 Format String 洩漏＋ROP；對應 pwn.college *Memory Errors* 與 *Return Oriented Programming* 模組檢查點。

#### `ch23` — 堆積管理器解剖與基礎記憶體損毀原語
- **檔案**：`ch23-heap-internals-and-primitives.md`
- **目標**：徹底看懂 glibc `ptmalloc2` 資料結構與配置演算法，理解 UAF、Double Free 與 Heap Overflow 如何轉化為任意讀寫原語，以及 Safe-Linking 繞過條件。
- **Must-cover**：`malloc_chunk`（`prev_size`/`size`/`A,M,P` 旗標、最小 `0x20` bytes）、tcache（每 bin 上限 `7` 個）、fastbin/unsorted/small/large bin 演算法、UAF 與 Double Free、Safe-Linking（`(pos >> 12) ^ ptr`）、tcache `key` 與 Pointer Mangling。
- **Must-NOT-cover**：FSOP 與進階複合堆積技術（見 ch24）。
- **Spine 接觸**：分析 `libnexus-parse` 批次解析多個 TLV 封包時錯誤處理提早 `free()` 未清零引發的 UAF。
- **Worked example**：給定真實 tcache chunk 位址 `pos = 0x55555555a2a0` 與目標位址 `target = 0x55555555a400`，逐位元計算 Safe-Linking 編碼值 `(0x55555555a2a0 >> 12) ^ 0x55555555a400 = 0x55555555a ^ 0x55555555a400 = 0x55500000f15a` 並驗證 `16-byte` 對齊。
- **Lab**：在現代 glibc 下用 `gdb` 追蹤 `libnexus-parse` tcache 狀態，完成 Heap Leak → Safe-Linking 解碼 → 任意寫原語；對應 pwn.college *Dynamic Allocator Misuse* 模組檢查點。

#### `ch24` — 現代堆積進階利用與分配器對照
- **檔案**：`ch24-advanced-heap-and-allocators.md`
- **目標**：突破 glibc 2.34+ 移除 `__free_hook`/`__malloc_hook` 後的現代堆積利用僵局，掌握 House of Botcake、FSOP（`_IO_FILE` 劫持）與非 glibc 分配器（jemalloc/mimalloc）的安全結構差異。
- **Must-cover**：為何現代 glibc 無法再靠覆寫 `__free_hook` 一鍵拿 shell、House of Botcake（結合 tcache 填滿 `7` 個＋unsorted bin 合併達成重疊 chunk 與繞過 double-free 檢查）、FSOP（File Stream Oriented Programming：偽造 `_IO_FILE_plus` 與 `_IO_wfile_jumps` vtable 檢查繞過達成任意函式呼叫）、jemalloc / mimalloc 隔離中繼資料（out-of-band metadata）對攻擊原語的改變。
- **Must-NOT-cover**：Linux 核心 SLUB 堆積（見 ch27）。
- **Spine 接觸**：在移除所有舊版 hook 且開啟 Full RELRO 的現代 glibc 環境下，將 `libnexus-parse` 的 UAF/重疊 chunk 轉化為完整控制流劫持。
- **Worked example**：逐步推演 House of Botcake 的 10 次 `malloc`/`free` 操作序列（填滿 `7` 個 tcache + 2 個鄰接 chunk 合併 + 取 1 補 1），列出每一步各 bin 的 chunk 位址與大小狀態表。
- **Lab**：在現代 glibc 容器對 Full RELRO 目標完成 House of Botcake → 任意寫 → FSOP 控制流劫持，並對照改用 hardened allocator（如 mimalloc secure mode）後的防禦效果。

#### `ch25` — Rust、`unsafe` 與 C FFI 邊界漏洞
- **檔案**：`ch25-rust-unsafe-and-ffi.md`
- **目標**：打破「用 Rust 就絕對安全」的迷思，專攻現代高效能後端與原生 Runtime 最常見的破口——`unsafe` soundness 違背、C FFI ABI 錯配與 Node.js N-API 跨界記憶體錯誤。
- **Must-cover**：Safe vs `unsafe` soundness 契約、懸垂指標／`&mut` aliasing 違背／`MaybeUninit` 未初始化讀取、C FFI `#[repr(C)]` 對齊與符號號轉型（`u32`→`i32`）、跨分配器 `free`、Node.js N-API / `Buffer` 外部記憶體生命週期與 GC 競爭、Release 模式整數溢位 wrapping。
- **Must-NOT-cover**：Rust 基礎語法教學、Fuzzing 工具鏈（見 ch29）。
- **Spine 接觸**：審計 NexusPay 重寫為 Rust + C FFI 並透過 N-API 掛載至 Node.js 的 `libnexus-parse`，找出殘留的跨界長度截斷與生命週期 UAF。
- **Worked example**：追蹤 TLV `len = 0xFFFF_FFF8`（uint32）在 `len + 8` 32 位元加法溢位回繞成 `0` 導致配置 0-byte buffer 卻拷貝超長資料的完整暫存器與位元組計算。
- **Lab**：編譯並審計 NexusPay Rust/C FFI 原生模組，用 `Miri` 與 `AddressSanitizer` 抓出 `unsafe` UB 與跨界讀取，並以 `checked_add` 與安全切片重構。

#### `ch26` — JS 引擎 JIT 類型混淆與 V8 Ubercage 沙箱架構
- **檔案**：`ch26-jit-type-confusion-and-ubercage.md`
- **目標**：打通現代 JS 執行時期漏洞的完整上下游——從 JIT 編譯器最佳化假設錯誤產生的 Type Confusion（型別混淆），到 V8 Sandbox（Ubercage）如何把記憶體損毀關在 `1 TiB` 籠內與逃逸思維。
- **Must-cover**：JS 動態物件記憶體表示（V8 Map / Hidden Class、Elements Kind、Tagged Pointer）、TurboFan / Maglev 最佳化管線中的範圍分析（Range Analysis）與 Check Elimination 錯誤如何導致越界讀寫（OOB R/W → `addrof` / `fakeobj` 原語）、V8 Sandbox（Ubercage：`1 TiB` 連續虛擬位址空間、`32-bit` 壓縮偏移指標、間接程式碼表）隔離架構與沙箱逃逸邊界。
- **Must-NOT-cover**：完整 Chrome 瀏覽器多行程 IPC（Mojo）0-day 實戰（聚焦單一 JS 引擎與沙箱邊界原理）。
- **Spine 接觸**：分析 NexusPay 內嵌客製化規則腳本引擎（基於 V8 Isolate）的隔離假設，評估為何「只靠 V8 Isolate 跑不信任腳本」不足以取代作業系統行程隔離。
- **Worked example**：給定一段觸發範圍分析邊界錯誤的精簡 JS 函式，逐步推導編譯器推算範圍 `[0, 0]` 與實際執行值 `-1` 的差異如何導致陣列長度覆寫，並計算 Ubercage 內 `32-bit` 壓縮指標無法定址沙箱外位址的算術邊界。
- **Lab**：在本地容器執行精簡版教學用 V8 歷史公開漏洞分析（使用 `--allow-natives-syntax` 與 `--trace-turbo` 觀察 IR 節點與物件記憶體佈局），實際驗證開啟 V8 Sandbox 前後的記憶體邊界差異。

#### `ch27` — Linux 核心漏洞利用實戰
- **檔案**：`ch27-linux-kernel-exploitation.md`
- **目標**：從使用者空間跨入 Ring 0，能建立 QEMU + GDB 核心除錯環境，理解 SLUB 堆積管理、`io_uring`/eBPF 核心攻擊面，並在受控模組上完成經典本地提權（LPE）。
- **Must-cover**：User Space ↔ Kernel Space 系統呼叫切換與 `task_struct`/`cred` 權限結構、SLUB 分配器（`kmalloc-32`..`kmalloc-4096` 物件快取與跨快取噴灑）、核心 UAF 與 Race Condition、`io_uring` 共享環形緩衝區生命週期與 eBPF Verifier 範圍追蹤漏洞形態、核心緩解（KASLR、SMEP、SMAP、KPTI）與常見繞過（`modprobe_path` 覆寫、Kernel ROP）。
- **Must-NOT-cover**：Windows 核心驅動與 iOS XNU 內核。
- **Spine 接觸**：分析 NexusPay 容器宿主節點的核心攻擊面（為何 Ch17 的容器隔離一旦遇上核心提權或 `io_uring`/eBPF 破口即全面瓦解）。
- **Worked example**：計算 `struct cred` 在 `kmalloc-192`（或對應 SLUB 快取）中的物件佈局與 `uid`/`euid` 欄位偏移，示範 UAF 堆積噴灑命中目標物件的覆蓋率估算。
- **Lab**：在本地 QEMU + Buildroot/BusyBox 最小化 Linux Kernel VM 中掛載特製漏洞驅動模組，透過 GDB 單步除錯完成 `cred` 或 `modprobe_path` 本地提權，再驗證開啟 SMEP/SMAP/KASLR 與 `sysctl` 禁用非特權 `io_uring`/eBPF 的防護效果；對應 pwn.college *Kernel Security* 模組檢查點。

---

### Part V — 規模化自動化挖掘與真實開源 0-day 實戰（Ch28–Ch32）

#### `ch28` — 靜態分析、變體分析與自動化規則工程
- **檔案**：`ch28-static-and-variant-analysis.md`
- **目標**：把人工一次挖一個洞的能力規模化——撰寫客製化 Semgrep 與 CodeQL 污點查詢，從單一 CVE 橫向掃出整個生態的同類變體（Variant Analysis）。
- **Must-cover**：AST/CFG/Call Graph/Data-Flow 基礎、Semgrep 語法樹與 Taint Mode、CodeQL 資料庫建置與 `TaintTracking`（Source/Sink/Barrier）、變體分析工作流（從 CVE Patch 反推根因 → 寫規則掃描多個專案）。
- **Must-NOT-cover**：動態 Fuzzing（見 ch29）、符號執行（見 ch30）。
- **Spine 接觸**：針對 NexusPay 整個 TS + C/Rust monorepo，將前章人工發現的 BOLA、SQLi 與 FFI 長度未檢模式轉化為自動化規則。
- **Worked example**：完整撰寫並逐行解析一支 CodeQL TaintTracking 查詢，從 Express/NestJS `req.query` 追蹤到未參數化 SQL Sink，並加入 Barrier 消除 90% 誤報。
- **Lab**：本地安裝免費 Semgrep 與 CodeQL CLI，對 NexusPay 撰寫並驗證 3 條客製規則（TS + C）並量測召回率與誤報率。

#### `ch29` — 灰箱 Fuzzing 工程實戰
- **檔案**：`ch29-fuzzing-engineering.md`
- **目標**：獨立為 C/C++ 與 Rust 解析器撰寫高效能 Fuzzing Harness，運用 Sanitizers 抓出記憶體損毀與邏輯崩潰，並進行語料庫最小化與 Crash 根因分類。
- **Must-cover**：AFL++ `64 KiB` 邊緣覆蓋率位圖（`cur_loc ^ (prev_loc >> 1)`）、Persistent Mode（提升至 `5,000+ exec/s`）、Sanitizers 原理與開銷（ASan 影子記憶體、UBSan、MSan）、Rust `cargo-fuzz` + `arbitrary` 結構感知 Fuzzing、Seed Corpus 設計與 `afl-tmin`/`afl-cmin`。
- **Must-NOT-cover**：符號執行混合 Fuzzing（見 ch30）、外部大型開源專案 OSS-Fuzz 提交實戰（見 ch31）。
- **Spine 接觸**：為 NexusPay 的 `libnexus-parse`（C 版與 Rust FFI 版）撰寫結構感知 Fuzzing Harness 挖出深層狀態機與整數溢位 Crash。
- **Worked example**：計算 AFL++ `fork()` 模式（`200 exec/s`）與 Persistent Mode（`5,000 exec/s`）跑滿 100 萬次變異的時間差（`83.3 分鐘` vs `3.3 分鐘`），以及 `64 KiB` 位圖雜湊碰撞機率估算。
- **Lab**：本地 Linux 容器對 `libnexus-parse` 跑 AFL++（ASan）與 `cargo-fuzz`，實際產出 Crash、最小化 PoC 與 stack trace 定位。

#### `ch30` — 符號執行、約束求解與混合式 Fuzzing
- **檔案**：`ch30-symbolic-execution-and-hybrid-fuzzing.md`
- **目標**：突破純灰箱 Fuzzing 卡在魔數比對（magic bytes）、校驗和（CRC32/checksum）與深層分支的覆蓋率天花板，能結合 Z3 與 angr 自動求解到達深層漏洞的輸入。
- **Must-cover**：符號執行（Symbolic Execution）原理、路徑條件（Path Constraints）與 SMT Solver（Z3 位元向量 `BitVec` 求解）、狀態爆炸（Path Explosion）問題與緩解策略、angr 在 ELF 二進位檔尋找目標位址輸入、混合式 Fuzzing（Hybrid Fuzzing：AFL++ 探索淺層分支＋符號引擎解開卡關分支並把解出的種子回灌語料庫）。
- **Must-NOT-cover**：形式化定理證明（如 Coq/TLA+，僅聚焦漏洞輸入求解）。
- **Spine 接觸**：針對 `libnexus-parse` 中須同時滿足 `magic == 0x4E58`、特定旗標組合與 32-bit 校驗和才能進入的深層解析分支，示範純 Fuzzing 失敗 vs 符號求解秒破。
- **Worked example**：計算純隨機／灰箱變異猜中 32-bit 精確魔數分支的期望嘗試次數（`2^32 ≈ 4.29 × 10^9` 次，於 `5,000 exec/s` 下需約 `9.9 天`），對比 Z3 單次約束求解耗時（`< 50 ms`）。
- **Lab**：用 Python `z3-solver` 與 `angr` 解開 `libnexus-parse` 的深層校驗和保護分支並將產出種子餵回 AFL++，觀測覆蓋率躍升。

#### `ch31` — 真實開源專案 Fuzzing 與 OSS-Fuzz 實戰
- **檔案**：`ch31-real-world-oss-fuzzing.md`
- **目標**：跨越「自己寫的教學程式」與「真實世界複雜開源專案」的鴻溝，能獨立挑選一個外部開源 C/Rust 函式庫，從建置系統改造、寫出高覆蓋 Harness、解決覆蓋率停滯到提交上游修補。
- **Must-cover**：挑選高勝率開源 Fuzzing 目標的判準（未納入 OSS-Fuzz 或 Harness 覆蓋率低的解析器/協定庫/壓縮庫）、處理複雜建置系統（CMake/Autotools/Cargo + 外部依賴靜態連結）、覆蓋率報告分析（`llvm-cov` 找卡關函式並改進 Harness 與字典檔）、Crash 去重（stack hash）與真假陽性判別、ClusterFuzzLite PR 閘門與 OSS-Fuzz 整合規範。
- **Must-NOT-cover**：漏洞揭露法規與 CVE 申請流程（見 ch33）。
- **Spine 接觸**：對比 NexusPay 所依賴的外部開源解析套件，建立第三方依賴安全驗證流程（不把供應商程式碼當黑箱信任）。
- **Worked example**：剖析一份真實風格的 `llvm-cov` 覆蓋率瓶頸報告（整體行覆蓋率停在 `18%`），透過加入 `FuzzedDataProvider` 拆分輸入參數與 24 條語法字典檔，展示覆蓋率拉升至 `60%+` 的具體量化過程。
- **Lab（真實開源目標）**：從本地 clone 一個真實開源中型 C 或 Rust 解析庫，獨立撰寫並執行 AFL++ 或 `cargo-fuzz` Harness、產出 `llvm-cov` HTML 覆蓋率報告、完成至少一次覆蓋率瓶頸優化，並演練 ClusterFuzzLite 設定檔撰寫。

#### `ch32` — 漏洞利用鏈串接、AI 輔助審計與開源 0-day 挖掘工作流
- **檔案**：`ch32-chaining-ai-and-0day-workflow.md`
- **目標**：把低危原語串成高危影響，並建立「人工架構洞察＋確定性靜態/動態工具＋AI Agent 假設生成與交叉驗證」的現代開源 0-day 挖掘節奏。
- **Must-cover**：漏洞原語分類與利用鏈（Exploit Chaining）思維、挑選高報酬真實目標（近期重構、跨語言邊界、複雜權限狀態機）、AI Agent 輔助程式碼審計工程方法（切分上下文、約束假設生成、以 PoC 與確定性工具濾除幻覺與誤報）、7 天開源專案 0-day 審計作業節奏。
- **Must-NOT-cover**：AI 應用自身安全漏洞（見 ch16）。
- **Spine 接觸**：串接 NexusPay 的三段獨立中低危原語（資訊洩漏 → SSRF/代理分歧 → 權限提升／帳本操控），示範影響力升級。
- **Worked example**：給定 4 個孤立低/中危發現，以依賴圖與前置條件表推導 2 條高危攻擊鏈，對比單獨回報 vs 串鏈回報的風險差異。
- **Lab（真實開源目標）**：挑選一個本地 clone 的真實中型開源 TypeScript/Rust 專案，完整執行「攻擊面盤點 → CodeQL/Semgrep 初篩 → 人工＋AI 輔助深讀 → 最小化 PoC 驗證」流程並產出標準化審計筆記。

---

### Part VI — 漏洞揭露、AppSec 防禦工程與資安職涯落地（Ch33–Ch37）

#### `ch33` — 漏洞揭露、嚴重度量化與 Bug Bounty 實戰運作
- **檔案**：`ch33-disclosure-and-bug-bounty.md`
- **目標**：將挖出的漏洞轉化為被廠商認可的 CVE、獎金與業界信用——精通 CVSS v4.0/EPSS/KEV 量化溝通、撰寫一次過關的漏洞報告，並建立可持續的靶場與 Bug Bounty 實戰運作。
- **Must-cover**：CVSS v4.0 向量結構（Base/Threat/Environmental、`AT`、Vulnerable vs Subsequent System）、EPSS 與 CISA KEV 排序、協調漏洞揭露（CVD）、GHSA 與 CVE 申請流程、高品質漏洞報告結構（Impact-first、最小可重現 PoC、根因與修補建議）、Bug Bounty 選標、時間 ROI、避開重複（Duplicate）與法律 Safe Harbor 邊界。
- **Must-NOT-cover**：求職面試與履歷轉譯（見 ch36）。
- **Spine 接觸**：為 Ch32 串接出的 NexusPay 完整攻擊鏈撰寫可直接提交給 CNA 與安全團隊的標準漏洞報告與 CVSS v4.0 評分。
- **Worked example**：針對同一個 NexusPay 跨系統漏洞，逐項對比 CVSS v3.1 與 CVSS v4.0 分數差異，並結合 EPSS `≥ 0.1` 判定 `24 小時` 或 `7 天` SLA。
- **Lab**：完成一份含自動化 PoC 的標準漏洞報告並依評審清單自檢；制定 12 週個人進階實戰計畫（鎖定 2 個公開 VDP/Bug Bounty 範圍之合法偵察腳本與指標追蹤）。

#### `ch34` — 企業級 AppSec 工程與 SDLC 防線設計
- **檔案**：`ch34-appsec-engineering-and-sdlc.md`
- **目標**：將攻擊者思維反轉為可規模化的防禦工程——設計讓開發者「寫出漏洞比寫安全程式碼更難」的 Paved Road（安全預設框架），並建置低誤報自動化安全閘門（直接對齊 Senior AppSec / Product Security 職責）。
- **Must-cover**：Paved Road / Secure-by-Default 框架設計（統一授權中介層、強制參數化查詢層、安全 HTTP Client 封裝防 SSRF）、規模化輕量 Threat Modeling（設計文件審查整合）、CI/CD 安全閘門設計（Semgrep/CodeQL 客製化規則與誤報率控制 `< 5%`、Secret Scanning、SCA 與可達性分析 Reachability Analysis）、漏洞管理 SLA 治理（`24 小時` / `7 天`）與與開發團隊協作的工程取捨。
- **Must-NOT-cover**：企業合規稽核文件（ISO 27001/SOC2 條文背誦）。
- **Spine 接觸**：為 NexusPay 設計整套「結構性消滅整類漏洞」的安全基礎設施重構藍圖（而非逐個修補單點 Bug）。
- **Worked example**：量化一個 50 人工程團隊每日 100 個 PR 下，SAST 誤報率 `30%`（每日 30 件假警報消耗約 `7.5` 工程師小時導致團隊關閉規則）vs 客製化高精準規則誤報率 `< 3%` 的投入產出比。
- **Lab**：為 NexusPay 實作一個安全預設封裝模組（含防 SSRF HTTP Client ＋強制租戶上下文的 DB Wrapper）與低誤報 CI 安全檢查管線，驗證可自動攔截前章多數回歸漏洞。

#### `ch35` — 完整實戰演練：NexusPay 端到端紅藍對抗復盤
- **檔案**：`ch35-nexuspay-red-blue-capstone.md`
- **目標**：將全書 34 章的知識融會貫通——在不給提示的端到端場景下，完整執行一次對 NexusPay 全系統的「黑箱偵察 → 跨層利用鏈突破（Web → Cloud → FFI）→ 影響評估 → 架構級藍隊防禦重構與回歸驗證」。
- **Must-cover**：全系統攻擊路徑圖（從邊緣代理分歧、授權/競爭漏洞、雲端憑證橫向到原生 FFI 模組崩潰與執行）、攻擊鏈各環節的最小可重現自動化腳本、紅隊事後報告（Executive Summary + Technical Root Cause）、藍隊分階段修補計畫（`24 小時` 緊急止血、`7 天` 根因修復、長期架構防線）與回歸測試驗證。
- **Must-NOT-cover**：引入未在 Ch01–Ch34 出現過的全新攻擊類別。
- **Spine 接觸**：全書 Spine 總結戰——同時涵蓋 NexusPay 所有四層邊界與基準常數。
- **Worked example**：以完整時間軸與事件鏈記錄一次 6 階段端到端滲透（從初始 `curl` 探測到突破 `$100.00` 帳本不變量與取得內部密鑰），並對照修補前後的偵測告警與阻斷點。
- **Lab（Capstone 總驗收）**：啟動完整版 NexusPay 綜合靶場，計時獨立完成至少 3 條跨層攻擊鏈的探索與 PoC 驗證，隨後套用藍隊修補並執行自動化安全回歸套件驗證全數阻斷。

#### `ch36` — 從後端工程師到資安專家：職涯轉型與面試實戰
- **檔案**：`ch36-security-career-and-interviews.md`
- **目標**：把全書累積的攻防能力與資深後端底蘊，精準轉譯為資安職缺錄取優勢——涵蓋角色選擇、履歷資安化轉譯與資安四大面試關卡實戰。
- **Must-cover**：職涯矩陣（AppSec Engineer、Product Security Engineer、Vulnerability Researcher、Cloud Security Engineer 的日常工作、技術權重與轉職路徑）、資深後端轉資安的結構性優勢與常見面試地雷、四大面試關卡（現場 Code Review 找洞、45 分鐘 Threat Modeling 白板設計、事件回應與修補權衡、跨團隊影響力）。
- **Must-NOT-cover**：一般後端演算法刷題（LeetCode）教學、資安證照評析與公開作品集／Proof-of-Work 建構策略（見 ch37）。
- **Spine 接觸**：以 NexusPay 作為「45 分鐘 Product Security 白板系統設計面試」完整示範題。
- **Worked example**：完整拆解一場 45 分鐘 Product Security 面試（5 分鐘釐清邊界、15 分鐘威脅建模、15 分鐘縱深防禦與權衡、10 分鐘監控與 `24 小時`/`7 天` 應變機制），並給出資深 vs 初階回答對照。
- **Lab（職涯實作）**：產出兩份可直接投入面試的資產：（1）針對目標資安職缺的「後端經歷資安化轉譯」專案描述；（2）45 分鐘計時白板 Threat Modeling 模擬自測與評分表。

#### `ch37` — 資安證照 ROI 評析與可驗證的能力證明體系
- **檔案**：`ch37-certifications-and-proof-of-work.md`
- **目標**：建立清醒的外部訊號投資策略——辨識不同資安證照在 HR 濾網與技術面試官眼中的真實權重，並建構比證照更具說服力的「可驗證能力證明（Proof of Work）」體系。
- **Must-cover**：證照的真實訊號價值（實戰上機考 vs 選擇題背誦證照；科技產品公司 vs 金融／顧問／合規組織的採信差異）、主流證照 ROI 矩陣（Web/AppSec：BSCP、OSWE/WEB-300、GWAPT；攻防/滲透：OSCP、CPTS；底層利用：OSED/OSEE；雲端/K8s：CKS、AWS Security Specialty；管理：CISSP——剖析費用、準備工時、適配職位與常見錢坑）、比證照更具殺傷力的 Proof of Work 金字塔（真實 CVE/GHSA 編號、Bug Bounty 公開 Hacktivity、開源安全修補 PR 與 CodeQL/Semgrep/OSS-Fuzz Harness 貢獻、具可重現 PoC 的深度技術 Write-up、主流 CTF 與靶場公開戰績）、依個人預算與目標職位規劃 6–12 個月「證照＋實證產出」最佳組合。
- **Must-NOT-cover**：面試流程與白板題拆解（見 ch36）、漏洞揭露流程與 CVSS 撰寫細節（見 ch33）。
- **Spine 接觸**：顯式說明本章不直接操作 NexusPay 靶機（聚焦外部職涯訊號與市場驗證），但示範如何把對類似 NexusPay 系統所寫的漏洞分析、CodeQL 規則與 Fuzzer Harness 轉化為公開可驗證的 Proof of Work 項目。
- **Worked example**：建立量化投報比較表，對比 4 種轉職投入路徑（例如高價考試路徑 vs 低成本實戰考 BSCP ＋ 2 個開源 GHSA/PR ＋ 1 套 CodeQL/Fuzzing 公開專案）在 16 週內的現金成本、工時分配與對兩類雇主（科技產品公司 AppSec/VR vs 顧問／金融合規團隊）的履歷訊號強度。
- **Lab（策略實作）**：依自身目標公司類型與預算，套用決策框架產出個人 6 個月「證照＋Proof-of-Work」執行藍圖與可公開驗證的 GitHub / Write-up 索引結構。
