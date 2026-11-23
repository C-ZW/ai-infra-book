# 附錄 A：NexusPay 完整本地靶機與一鍵啟動環境索引

本附錄彙整《邊界失守》全書共用的多租戶即時結算與 API 閘道基準靶機 **NexusPay** 之本地容器拓樸、一鍵管理腳本、系統基準常數，以及全書 37 章的本地實驗與外部授權靶場（PortSwigger Web Security Academy、pwn.college、Cryptopals）檢查點總表。

所有本地實驗環境均綁定本機迴路位址 `127.0.0.1`，不對外網暴露，零雲端費用且離線可重現。

---

## 一、NexusPay 本地靶機拓樸與基準常數

NexusPay 本地實驗環境位於專案目錄 `books/vuln-hunting/labs/`，由 `docker-compose.yml` 與 `setup.sh` 統一編排五個核心容器組件。

```text
+-----------------------------------------------------------------------------------+
| Host Machine (127.0.0.1 only, Zero External Exposure)                             |
|                                                                                   |
|  [Browser / curl / Caido / Burp / Python Exploit Scripts]                         |
|         |                                       |                                 |
|         | HTTP :8080                            | Direct HTTP :3000               |
|         v                                       v                                 |
|  +--------------------+                +--------------------+                     |
|  | nexus-nginx        |  proxy_pass    | nexus-api          |                     |
|  | nginx:1.27-alpine  | -------------> | node:22-alpine     |                     |
|  | read_timeout = 30s |  keepalive 32  | keepAlive = 5000ms |                     |
|  +--------------------+                +--------------------+                     |
|                                           |              |                        |
|                        TCP :5432          |              | TCP :6379              |
|                 +-------------------------+              +--------------+         |
|                 v                                                       v         |
|  +------------------------------+                        +---------------------+  |
|  | nexus-pg (PostgreSQL 16)     |                        | nexus-redis         |  |
|  | DB: nexuspay                 |                        | redis:7-alpine      |  |
|  | tenant-alpha / tenant-beta   |                        | Session / RateLimit |  |
|  | balance_cents = 10,000 ($100)|                        | Idempotency / Locks |  |
|  +------------------------------+                        +---------------------+  |
|                                                                                   |
|  +-----------------------------------------------------------------------------+  |
|  | nexus-bin (Profile: bin | Platform: linux/amd64 | Ubuntu 24.04)             |  |
|  | Tools: gcc, clang, llvm, gdb, afl++, rustc/cargo, strace, ltrace, patchelf  |  |
|  | Mount: ./workspace -> /workspace (cap_add: SYS_PTRACE, seccomp: unconfined) |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

### 1. 容器服務與連線端點清單

| 容器名稱 | 映像檔／建置來源 | 本機綁定埠號 | 核心組態與初始狀態 | 適用篇章 |
|---|---|---|---|---|
| `nexus-nginx` | `nginx:1.27-alpine`（掛載 `./nginx/nginx.conf`） | `127.0.0.1:8080` | `proxy_read_timeout 30s`、`proxy_http_version 1.1`、`upstream keepalive 32`；攔截 `/internal/` 回傳 `403` | Part I–III、Part VI |
| `nexus-api` | `./api/Dockerfile`（`node:22-alpine`） | `127.0.0.1:3000` | `server.keepAliveTimeout = 5000`（`5 s`）、`JWT_TTL_SECONDS = 900`、`JWKS_CACHE_TTL_SECONDS = 300`；提供 `/health` 與 `/v1/accounts` 基準路由 | Part I–III、Part V–VI |
| `nexus-pg` | `postgres:16-alpine`（掛載 `./db/init.sql`） | `127.0.0.1:5432` | 帳號 `nexus`／密碼 `nexuspass`／資料庫 `nexuspay`；預設建立 `tenants`、`accounts`、`ledger_entries` 三表與兩組測試商戶 | Part I–III、Part VI |
| `nexus-redis` | `redis:7-alpine` | `127.0.0.1:6379` | 供會話狀態、JWKS 快取、滑動視窗限流、WebSocket 單次 Ticket 與冪等鍵實驗使用 | Part I–III、Part VI |
| `nexus-bin` | `./bin/Dockerfile`（`ubuntu:24.04`，`linux/amd64`） | 互動式 Shell（無對外埠） | 啟用 `SYS_PTRACE` 與 `seccomp:unconfined`；預裝 `gcc`、`clang`、`llvm`、`gdb`、`afl++`、`rust/cargo`、`patchelf`；掛載 `./workspace` 至 `/workspace` | Part IV–V |

### 2. 預置資料庫結構與測試帳戶基準

`labs/db/init.sql` 於容器首次啟動或重置時自動寫入以下基準資料（對齊全書基準常數：單戶測試餘額 `10,000` 整數分，即 `$100.00`；單次提領上限 `10,000` 分）：

| 資料表 | 關鍵欄位與型別 | 預置測試資料 | 安全不變量（Invariants） |
|---|---|---|---|
| `tenants` | `id TEXT PRIMARY KEY`, `name TEXT` | `tenant-alpha`（Alpha Merchant）<br>`tenant-beta`（Beta Merchant） | 租戶上下文必須由已驗證之憑證強綁定，禁止跨租戶查詢或修改 |
| `accounts` | `id TEXT PRIMARY KEY`, `tenant_id TEXT`, `owner_email TEXT`, `balance_cents BIGINT DEFAULT 10000`, `withdraw_limit_cents BIGINT DEFAULT 10000` | `acct-alpha-01`（`tenant-alpha`, `alice@alpha.local`, `10000`, `10000`）<br>`acct-beta-01`（`tenant-beta`, `bob@beta.local`, `10000`, `10000`） | 任意併發序列下 `balance_cents >= 0`，單次提領不得超過 `withdraw_limit_cents`（`10,000`） |
| `ledger_entries` | `id BIGSERIAL PRIMARY KEY`, `account_id TEXT`, `tenant_id TEXT`, `delta_cents BIGINT`, `idempotency_key TEXT` | 初始為空，隨轉帳／提領交易寫入 | 所有帳戶之 `10000 + SUM(delta_cents)` 必須恆等於當前 `balance_cents` |

### 3. 全書基準常數速查（對齊 `_meta/running-examples.md`）

| 基準常數名稱 | 固定數值與單位 | 對應實驗與驗證場景 |
|---|---|---|
| 閘道與後端逾時邊界 | Nginx `proxy_read_timeout = 30 s`；Node.js `keepAliveTimeout = 5 s` | Keep-Alive 連線複用、CL.TE / TE.CL / H2.CL 請求走私（Ch01, Ch03, Ch11, Ch12, Ch14） |
| 帳本餘額與併發規格 | 單戶初始餘額 `10,000` 分（`$100.00`）；單次提領上限 `10,000` 分；尖峰 `2,000 req/s` | BOLA 越權、TOCTOU 雙花與原子扣款修補（Ch01, Ch06, Ch08, Ch12, Ch35） |
| JWT 與 JWKS 快取規格 | `RS256`（`2048-bit` RSA），有效期 `900 s`（15 分鐘）；JWKS 快取 TTL `300 s` | 演算法混淆、`kid` 路徑穿越、JWKS 快取投毒（Ch04, Ch05, Ch06, Ch15） |
| GraphQL 深度與批次上限 | 預設巢狀深度上限 `8` 層；單次 Batch 請求上限 `20` 個操作 | Alias Batching 繞過限流、查詢放大 DoS（Ch07, Ch14） |
| HTTP/2 單封包併發視窗 | 同連線最後 1 位元組同步送達 `20` 個請求，到達抖動 `< 1 ms` | Single-Packet Attack 觸發微秒級競爭視窗（Ch03, Ch12, Ch35） |
| x86_64 記憶體對齊與 ASLR | 指標 `8 bytes`；Stack / `ptmalloc2` chunk 對齊 `16 bytes`；最小 chunk `32 bytes`（`0x20`）；ASLR `28 bits` 熵（頁大小 `4 KiB`） | ELF 解剖、ROP 對齊、堆積利用與資訊洩漏（Ch20, Ch22, Ch23, Ch24, Ch25, Ch27） |
| `ptmalloc2` tcache 與 Safe-Linking | 每條 tcache bin 上限 `7` 個 chunk（`0x20`–`0x410` 共 `64` bins）；掩碼 `(pos >> 12) ^ ptr` | 現代 glibc 堆積 UAF、House of Botcake（Ch23, Ch24, Ch25） |
| `libnexus-parse` TLV 封包規格 | 檔頭固定 `8 bytes`（`magic: 2B`, `type: 2B`, `len: 4B` uint32）；合法 payload 上限 `65,536 bytes`（`64 KiB`） | 逆向工程、Rust/C FFI 溢位、AFL++ 與 Z3/angr 求解（Ch20, Ch21, Ch25, Ch28, Ch29, Ch30） |
| V8 Sandbox（Ubercage）與核心 SLUB | V8 沙箱保留 `1 TiB` 位址空間、`32 bits` 壓縮偏移；核心頁 `4 KiB`、SLUB `kmalloc-32` 至 `kmalloc-4096` | 執行時期沙箱邊界與核心堆積隔離（Ch13, Ch17, Ch26, Ch27） |
| AES-GCM 與密碼學基準 | 區塊 `128 bits`（`16 bytes`）；標準 Nonce `96 bits`（`12 bytes`） | Padding Oracle、Nonce 重用洩漏 GHASH 金鑰 `H`（Ch04, Ch15） |
| AFL++ 覆蓋率位圖與吞吐 | 邊緣位圖 `65,536 bytes`（`64 KiB`）；單核 Persistent Mode 基準吞吐 `5,000 exec/s` | 灰箱 Fuzzing 吞吐量與碰撞率分析（Ch29, Ch30, Ch31） |
| 漏洞分流與修復 SLA | 嚴重 SLA `24 小時`、高危 SLA `7 天`；CVSS v4.0 搭配 EPSS `≥ 0.1` 或列入 CISA KEV 立即處置 | 漏洞報告、SDLC 閘門治理與白板面試（Ch33, Ch34, Ch35, Ch36） |

---

## 二、一鍵啟動與環境操作指令

進入 `books/vuln-hunting/labs` 目錄後，可直接透過 `./setup.sh` 管理所有實驗容器生命週期：

```bash
cd books/vuln-hunting/labs

# 1. 啟動核心 Web / API / PostgreSQL 16 / Redis 7 靶機（適用 Part I–III、Part VI）
./setup.sh up

# 2. 檢視所有容器執行狀態與健康檢查結果
./setup.sh status

# 3. 驗證核心閘道與資料庫基準連線
curl -s http://127.0.0.1:3000/health | jq .
curl -s http://127.0.0.1:8080/v1/accounts | jq .

# 4. 建置並啟動 x86_64 原生二進位／逆向／Fuzzing 容器（適用 Part IV–V）
#    （Apple Silicon Mac 會自動透過 Docker linux/amd64 模擬層執行）
./setup.sh up-bin

# 5. 進入 nexus-bin 容器互動式 Bash 終端（工作目錄掛載於 /workspace）
./setup.sh shell-bin

# 6. 清空資料庫與 Redis 資料卷並重置回初始基準狀態（每戶恢復 10,000 分）
./setup.sh reset

# 7. 停止並移除所有實驗容器
./setup.sh down
```

---

## 三、全書各章本地實驗與外部靶場檢查點總表

下表列出全書 37 章的完整實驗配置，讀者可直接搭配各章「動手做」小節於本地環境或外部靶場實作與延伸驗證。

### Part I — 攻擊者心智模型與邊界理論（Ch01–Ch03）

| 章節 | 狀態 | 難度／時間 | 本地實驗環境與核心任務 | 外部靶場對照檢查點（PortSwigger / 其他） |
|---|---|---|---|---|
| **Ch01** 信任邊界、攻擊面與漏洞的形式化模型 | 已完稿 | 入門／45 分鐘 | `./setup.sh up` 啟動基準拓樸；盤點 Nginx `:8080`、API `:3000`、PG `:5432`、Redis `:6379` 暴露面，建立 3 條信任邊界與 `$100.00` 帳本不變量威脅矩陣 | **PortSwigger**：*API testing*（HTTP 方法枚舉與 OpenAPI 探索）、*Information disclosure*（從錯誤堆疊還原狀態機） |
| **Ch02** 現代偵察、黑箱與白箱審計工作流 | 已完稿 | 入門／45 分鐘 | 設定 Caido / Burp MITM 代理與 CA 憑證信任鏈（`NODE_EXTRA_CA_CERTS`）；黑箱挖掘 3 個未公開影子端點，白箱以 `rg` 10 分鐘完成 Source-to-Sink 追蹤 | **PortSwigger**：*Exploiting an API endpoint using documentation*（Practitioner）、*Finding and exploiting an unused API endpoint*（Practitioner） |
| **Ch03** 協議解析差異與 HTTP 請求走私 | 已完稿 | 進階／45 分鐘 | 本地執行 `lab_smuggle.mjs`（前端代理 `:18080` 看 `Content-Length`、後端 `:18081` 看 `Transfer-Encoding`），以 Python raw socket 重現 `CL.TE` 繞過 `/internal/admin` 並修補 | **PortSwigger**：*HTTP request smuggling, basic CL.TE vulnerability*（Practitioner）、*basic TE.CL vulnerability*（Practitioner）、*H2.CL request smuggling*（Practitioner/Expert） |

### Part II — Web、API、現代協定與後端漏洞挖掘（Ch04–Ch14）

| 章節 | 狀態 | 難度／時間 | 本地實驗環境與核心任務 | 外部靶場對照檢查點（PortSwigger / 其他） |
|---|---|---|---|---|
| **Ch04** 身分驗證與會話機制破口 | 已完稿 | 進階／60 分鐘 | 本地 NexusPay Auth 容器重現 `RS256 → HS256` 公鑰混淆、JWT `kid` 路徑穿越（`../../../../dev/null`）與 OAuth `redirect_uri` 繞過；以 `jose` 白名單與原子 `UPDATE ... RETURNING *` 修補 Refresh Token 競爭 | **PortSwigger**：*JWT authentication bypass via algorithm confusion*（Practitioner）、*JWT authentication bypass via kid header path traversal*（Practitioner）、*OAuth account hijacking via redirect_uri* |
| **Ch05** 企業單點登入與認證深水區 | 已完稿 | 進階／60 分鐘 | 本地 SAML SP 端點（`/v1/auth/saml/acs`）實作 XSW #3 未簽章 Assertion 注入與 `<NameID>` XML 註解截斷（`<!-- -->`），並以嚴格 Reference 子樹綁定與 ID 防重放修補 | **PortSwigger**：*Authentication vulnerabilities* 模組之進階 MFA 狀態機跳步與驗證繞過關卡（Practitioner/Expert） |
| **Ch06** 授權模型崩壞：BOLA、BFLA 與多租戶隔離失效 | 已完稿 | 進階／45 分鐘 | 以 Python `authz_matrix_scan.py` 對兩租戶（`1001` vs `1002`）自動化掃描 BOLA、BOPLA（竄改 `feeRate: 0`）與 BFLA；導入 PostgreSQL RLS 與嚴格 DTO 白名單修補 | **PortSwigger**：*Access control vulnerabilities* — *IDOR/BOLA*、*Method-based access control can be circumvented*（Practitioner）、*Multi-step process with no access control on one step*（Practitioner） |
| **Ch07** 非 REST 現代後端協定安全 | 已完稿 | 進階／45 分鐘 | 對本地 GraphQL 閘道構造 `20` 個 Alias × `5` 層巢狀查詢驗證放大效應並加入 AST 查詢成本上限（`500`）；重現 WebSocket CSWSH 並以 `Origin` 白名單＋Redis 單次 Ticket（`TTL = 30 s`）修補 | **PortSwigger**：*GraphQL API vulnerabilities*（*Accessing private GraphQL posts*、*Bypassing GraphQL brute force protections*）、*WebSockets*（*Cross-site WebSocket hijacking*） |
| **Ch08** 注入家族的本質：資料與控制平面的混同 | 已完稿 | 進階／60 分鐘 | 針對 NexusPay 報表排序參數撰寫 Python 二分搜尋盲注腳本（`128` 次請求萃取 32 字元 hex token）、驗證 Redis RESP 與參數注入（`--`），並以白名單列舉與參數化修補 | **PortSwigger**：*Blind SQL injection with time delays and information retrieval*（Practitioner）、*Server-side template injection*（Practitioner/Expert）、*Blind OS command injection*（Practitioner） |
| **Ch09** 檔案處理、路徑穿越與複合解析器攻擊面 | 已完稿 | 進階／60 分鐘 | 本地檔案服務構造惡意 ZIP（`../../../../app/config/webhook.json`）重現 Zip Slip，以及透過 `/v1/invoices/import` 載入外部 DTD 完成 OOB XXE 讀取本機檔案；以 `path.resolve` 前綴斷言與禁用外部實體修補 | **PortSwigger**：*Path traversal*（*traversal sequences stripped non-recursively*）、*XXE*（*Exploiting blind XXE to exfiltrate data using a malicious external DTD*）、*File upload*（*polyglot web shell upload*） |
| **Ch10** 瀏覽器安全模型與客戶端攻擊鏈 | 已完稿 | 挑戰／60 分鐘 | 啟動本地雙來源靶機（`:8080` 目標站與 `:9090` 攻擊站），串接未驗 `event.origin` 之 `postMessage` 與 DOM XSS 竊取敏感狀態，再以 Nonce-based Strict CSP 修補 | **PortSwigger**：*XSS*（*CSP bypass / dangling markup*，Expert）、*CORS*（*trusted insecure protocols*，Practitioner/Expert）、*DOM-based*（*web messages and JSON.parse*）、*CSRF*（*SameSite Lax bypass via cookie refresh*） |
| **Ch11** SSRF、URL Parser 混淆與 Web Cache Poisoning / Deception | 已完稿 | 進階／45 分鐘 | 利用 URL 解析差異與替代 IP 表示法（`0177.0.0.1`）繞過 Webhook 黑名單存取內網 `:9000/internal/metrics`，並實作自訂 `lookup` IP Pinning 修補；測試 Nginx Unkeyed Header 快取投毒 | **PortSwigger**：*SSRF*（*blacklist-based input filter*、*filter bypass via open redirection*）、*Web cache poisoning*（*unkeyed header / parameter cloaking*）、*Web cache deception*（*path mapping / delimiters*） |
| **Ch12** 競爭條件、HTTP/2 單封包攻擊、分散式狀態機與商業邏輯漏洞 | 已完稿 | 進階／45 分鐘 | 以 Python `h2` 單封包腳本對 `/v1/withdraw` 同步送出 `20` 個提領請求（抖動 `< 1 ms`），在 `READ COMMITTED` 下突破 `10,000` 分餘額限制完成雙花；以單條條件式原子 `UPDATE` ＋ `Idempotency-Key` 修補 | **PortSwigger**：*Race conditions*（*Limit overrun race conditions*、*Multi-endpoint race conditions*）、*Business logic vulnerabilities*（*Insufficient workflow validation*） |
| **Ch13** 反序列化、原型鏈汙染與 Node.js 執行時期漏洞 | 已完稿 | 進階／60 分鐘 | 本地啟動 `ch13-nodejs` 靶機，利用未過濾 `__proto__` 的 `deepMerge` 觸發 Prototype Pollution → `child_process` RCE Gadget，並實測 `^(a+)+$` ReDoS 阻塞事件迴圈；改用 `Object.create(null)`、`--disable-proto=throw` 與 `re2` 修補 | **PortSwigger**：*Prototype pollution*（*Server-side prototype pollution* / *RCE via child_process*，Practitioner/Expert）、*Insecure deserialization* |
| **Ch14** 防禦對抗與繞過技術 | 已完稿 | 進階／45 分鐘 | 啟動本地 `waf-nginx`（`SecRequestBodyNoFilesLimit 8192`）＋ Express（`100 KiB` 上限），以 `> 8,192 bytes` JSON Padding 繞過 WAF 檢查，並利用 `X-Forwarded-For` 與大小寫路徑繞過限流；從應用程式層根因修補 | **PortSwigger**：*SQL injection with filter bypass via XML encoding*（Practitioner）、*Authentication* 模組之 `X-Forwarded-For` IP 封鎖繞過關卡 |

### Part III — 密碼學、AI 系統、雲端原生與供應鏈（Ch15–Ch19）

| 章節 | 狀態 | 難度／時間 | 本地實驗環境與核心任務 | 外部靶場對照檢查點（Cryptopals / PortSwigger / 其他） |
|---|---|---|---|---|
| **Ch15** 密碼學工程實戰破口 | 已完稿 | 進階／60 分鐘 | 本地撰寫 AES-CBC Padding Oracle 逐位元組解密腳本（驗證 `0x02 0x02` 邊界處理）與 AES-GCM `96-bit` Nonce 重用明文差還原／GHASH 金鑰 `H` 偽造；遷移至隨機 Nonce AEAD 與 `crypto.timingSafeEqual` | **Cryptopals**：Set 2 Challenge 10–13（CBC 實作與 ECB Cut-and-Paste）、Set 3 Challenge 17（CBC Padding Oracle）、Set 3 Challenge 22–23（PRNG 狀態預測） |
| **Ch16** AI / LLM 與 Agent 系統攻擊面 | 已完稿 | 進階／60 分鐘 | 本地啟動模擬之 NexusPay Tool-Calling Agent 與多租戶向量檢索服務，在發票備註植入 Indirect Prompt Injection 誘導呼叫 `issue_refund` 並跨租戶洩漏 RAG 文件；於工具層加上獨立於 LLM 的確定性 Policy Gate 修補 | **PortSwigger**：*Web LLM attacks* — *Exploiting LLM APIs with excessive agency*、*Exploiting vulnerabilities in LLM APIs*、*Indirect prompt injection*、*Exploiting insecure output handling in LLMs*（Expert） |
| **Ch17** 容器隔離與 Kubernetes 權限提升 | 已完稿 | 進階／60 分鐘 | 本地建立 `kind` 叢集（`nexuspay-lab`），部署含 `pods/create` 權限與自動掛載 Token 之弱化 `worker-sa`，演練建立特權／`hostPath` Pod 竊取 `nexuspay-db-secret`；套用 Pod Security Standards（`restricted`）與最小 RBAC 修補 | 本地 `kind` 隔離叢集完整驗證（可選對照 Kubernetes Goat / pwn.college *System Security* 容器命名空間關卡） |
| **Ch18** 雲端 IAM、中繼資料服務與橫向移動 | 已完稿 | 進階／50 分鐘 | 本地啟動 **LocalStack**（啟用 `iam,lambda,sts,secretsmanager,s3`）與 IMDS 模擬器，由 SSRF 竊取 IMDSv1 臨時憑證，串接 `iam:PassRole` + `lambda:CreateFunction` 提權讀取生產密鑰；強制 IMDSv2（Hop Limit 1）與 IAM 邊界修補 | 本地 LocalStack 零費用模擬（零風險選做延伸：CloudGoat / Flaws2.cloud） |
| **Ch19** 軟體供應鏈與 CI/CD 管線攻防 | 已完稿 | 進階／45 分鐘 | 本地模擬私有套件代理與 GitHub Actions 工作流，重現 Dependency Confusion 與 `pull_request_target` 結合 PR 標題之 Script Injection 竊取 Token；以名稱空間鎖定、環境變數隔離（`env:`）與 Action Commit SHA 釘選修補 | 本地模擬器完整驗證（對照 GitHub Security Lab *Actions Worm / Script Injection* 公開案例） |

### Part IV — 逆向工程、記憶體安全、FFI 與現代系統利用（Ch20–Ch27）

| 章節 | 狀態 | 難度／時間 | 本地實驗環境與核心任務 | 外部靶場對照檢查點（pwn.college / 其他） |
|---|---|---|---|---|
| **Ch20** 二進位執行環境與記憶體佈局 | 已完稿 | 入門至進階／50 分鐘 | `./setup.sh up-bin && ./setup.sh shell-bin` 進入 `nexus-bin`；編譯 C 基準版 `libnexus-parse`，以 `readelf`、`objdump`、`checksec` 與 `gdb` 檢視 `8-byte` TLV 檔頭小端序佈局、`16-byte` 堆疊對齊、Canary 與 ASLR `28-bit` 熵 | **pwn.college**：*Program Security* -> *Assembly Crash Course* 與 *Debugging Refresher* |
| **Ch21** 無原始碼逆向工程實戰 | 已完稿 | 進階／50 分鐘 | 將含隱藏除錯分支的 `libnexus-parse.so` 以 `strip -s` 移除符號，透過 Ghidra 靜態反編譯與 `objdump`/`gdb` 交叉引用（XREF），從 `memcpy`/`malloc` 逆推還原 `nexus_tlv_ctx_t` 結構體偏移與漏洞觸發條件 | **pwn.college**：*Program Security* -> *Reverse Engineering* |
| **Ch22** 堆疊溢位、控制流劫持與 ROP 鏈構造 | 已完稿 | 進階／60 分鐘 | 於 `nexus-bin` 針對未檢查 `len <= 65,536` 的堆疊緩衝區構造 Format String 洩漏 Canary/libc 基底，並串接含 `ret` 對齊 gadget 之 64 位元 ROP 鏈 | **pwn.college**：*Program Security* -> *Memory Errors* 與 *Return Oriented Programming* |
| **Ch23** 堆積管理器解剖與基礎記憶體損毀原語 | 已完稿 | 進階／60 分鐘 | 於 `nexus-bin` 透過 `gdb` 觀察 `ptmalloc2` `0x20` chunk、tcache（上限 `7` 個）與 UAF，實算 Safe-Linking `(pos >> 12) ^ ptr` 解碼與任意寫入原語 | **pwn.college**：*Program Security* -> *Dynamic Allocator Misuse* |
| **Ch24** 現代堆積進階利用與分配器對照 | 已完稿 | 挑戰／75 分鐘 | 於現代 glibc（無 `__free_hook`、Full RELRO）容器環境演練 House of Botcake 重疊 chunk 與 FSOP 控制流劫持，對比 hardened allocator 防禦效果 | **pwn.college**：*Software Exploitation* -> 進階堆積與 `_IO_FILE` 利用模組 |
| **Ch25** Rust、`unsafe` 與 C FFI 邊界漏洞 | 已完稿 | 進階／50 分鐘 | 在 `nexus-bin` 編譯 Rust + C FFI 版 `libnexus-parse`，重現 `len = 0xFFFF_FFF8` 加 `8` 之 32 位元溢位回繞、`u32 → i32` 符號轉型與跨邊界生命週期 UAF；以 `cargo miri`、ASan/UBSan 偵測並改用 `checked_add` 與安全切片重構 | **pwn.college**：*Program Security* -> *Memory Errors*（有號／無號整數溢位與 `malloc(0)` 邊界關卡） |
| **Ch26** JS 引擎 JIT 類型混淆與 V8 Ubercage 沙箱架構 | 已完稿 | 挑戰／75 分鐘 | 本地容器以 `--allow-natives-syntax` 與 `--trace-turbo` 觀察 V8 Map / Elements Kind 與範圍分析錯誤，驗證 `1 TiB` Ubercage `32-bit` 壓縮指標隔離邊界 | 本地 V8 教學容器（對照公開 Chromium V8 歷史 CVE 最小化 PoC 分析） |
| **Ch27** Linux 核心漏洞利用實戰 | 已完稿 | 挑戰／90 分鐘 | 本地 QEMU + Buildroot Linux Kernel VM 掛載漏洞驅動，以 GDB 遠端除錯 SLUB `kmalloc-*` UAF 完成提權，並驗證 SMEP/SMAP/KASLR 與 `sysctl` 限制 `io_uring`/eBPF 之防護 | **pwn.college**：*System Security* -> *Kernel Security* |

### Part V — 規模化自動化挖掘與真實開源 0-day 實戰（Ch28–Ch32）

| 章節 | 狀態 | 難度／時間 | 本地實驗環境與核心任務 | 外部靶場／真實專案銜接檢查點 |
|---|---|---|---|---|
| **Ch28** 靜態分析、變體分析與自動化規則工程 | 已完稿 | 進階／60 分鐘 | 本地安裝 Semgrep 與 CodeQL CLI，針對 NexusPay TS + C 程式碼庫撰寫 3 條客製化規則（含跨檔案 `TaintTracking` 與 Barrier 消除誤報），實測召回率與誤報率 | 將客製化 CodeQL / Semgrep 查詢遷移至 GitHub 真實開源專案執行變體分析 |
| **Ch29** 灰箱 Fuzzing 工程實戰 | 已完稿 | 進階／60 分鐘 | 於 `nexus-bin` 為 `libnexus-parse` C 版撰寫 AFL++ Persistent Mode Harness（搭配 ASan/UBSan，吞吐 `5,000+ exec/s`），為 Rust 版撰寫 `cargo-fuzz` + `arbitrary` 結構感知 Harness，產出 Crash 並以 `afl-tmin` 最小化 | **pwn.college**：*Software Exploitation* 二進位挑戰（以 Fuzzing + ASan 快速定位解析器崩潰） |
| **Ch30** 符號執行、約束求解與混合式 Fuzzing | 已完稿 | 進階／45 分鐘 | 於本地容器編譯含 `magic == 0x4E58` 與 32 位元校驗和保護的 `nexus_tlv_sym.c`，分別撰寫 `solve_tlv_z3.py`（`z3.BitVec`）與 `solve_tlv_angr.py` 自動解出 `20 bytes` 觸發種子並回灌 AFL++ | **pwn.college**：*Program Security / Reverse Engineering*（Symbolic Execution 關卡） |
| **Ch31** 真實開源專案 Fuzzing 與 OSS-Fuzz 實戰 | 已完稿 | 進階／60 分鐘 | 本地 clone 真實開源中型 C/Rust 解析器，獨立改造靜態連結建置、撰寫 `FuzzedDataProvider` Harness 與語法字典檔，以 `llvm-cov` 產出 HTML 覆蓋率報告突破瓶頸（`18% -> 60%+`），並撰寫 ClusterFuzzLite 設定 | **Google OSS-Fuzz / ClusterFuzzLite**：真實開源解析庫本地覆蓋率優化與上游 PR 準備 |
| **Ch32** 漏洞利用鏈串接、AI 輔助審計與開源 0-day 挖掘工作流 | 已完稿 | 挑戰／60 分鐘 | 對本地 clone 之真實開源專案執行「90 天 Git 高變動熱點測繪 → Semgrep/CodeQL 確定性初篩 → 切出 `< 1,000` 行 `slice.txt` 交由受約束 AI 產生可證偽假設 → 本地確定性 PoC 淘汰誤報」完整工作流 | 真實開源專案 7 天 0-day 審計工作流與標準化審計筆記產出 |

### Part VI — 漏洞揭露、AppSec 防禦工程與資安職涯落地（Ch33–Ch37）

| 章節 | 狀態 | 難度／時間 | 本地實驗環境與核心任務 | 外部標準／實戰產出檢查點 |
|---|---|---|---|---|
| **Ch33** 漏洞揭露、嚴重度量化與 Bug Bounty 實戰運作 | 已完稿 | 進階／45 分鐘 | 針對 NexusPay 跨層攻擊鏈撰寫標準 CVD/GHSA 漏洞報告，實算 CVSS v4.0 向量（含 `AT` 與 Vulnerable/Subsequent System）並結合 EPSS `≥ 0.1` 判定 `24 小時` / `7 天` SLA | 對齊 FIRST CVSS v4.0 規範、GHSA 提交流程與公開 VDP Safe Harbor 邊界檢查 |
| **Ch34** 企業級 AppSec 工程與 SDLC 防線設計 | 已完稿 | 進階／45 分鐘 | 本地建立 `nexuspay-paved-road/`，實作 Socket 層 IP Pinning 之 `safeHttpGet`（阻斷 `169.254.169.254` 與 `::ffff:127.0.0.1`）與強制綁定 `tenantId` 之 `TenantDbClient`，搭配 `.semgrep/paved-road.yaml` 達成 `0` 誤報 CI 阻斷閘門 | 對齊企業 Paved Road 框架設計與 PR 阻斷閘門誤報率 `< 3%`–`< 5%` 工程基準 |
| **Ch35** 完整實戰演練：NexusPay 端到端紅藍對抗復盤 | 已完稿 | 挑戰／90 分鐘 | 啟動完整版 NexusPay 綜合靶場，計時獨立完成跨層攻擊鏈（Web 代理/授權/單封包雙花 → 雲端憑證 → 原生 FFI）之自動化 PoC，隨後套用藍隊分階段修補（`24 小時` 止血 / `7 天` 根治）與回歸測試 | 全書紅藍對抗總驗收（Capstone） |
| **Ch36** 從後端工程師到資安專家：職涯轉型與面試實戰 | 已完稿 | 進階／60 分鐘 | 任務一：將兩項後端開發經歷依四段式公式轉譯為資安履歷條目；任務二：計時 45 分鐘完成「商戶 Webhook 回呼與批次 TLV 對帳匯出服務」白板 Threat Modeling（嚴格執行 `5 / 15 / 15 / 10 分鐘` 時間盒） | 對照附錄 D 白板題庫與現場 Code Review 評分標準自評 |
| **Ch37** 資安證照 ROI 評析與可驗證的能力證明體系 | 已完稿 | 進階／45 分鐘 | 抽樣 10 份目標職缺 JD 訊號，套用預算與工時矩陣選定最佳投資組合（如 Portfolio C：BSCP ＋ 開源 CodeQL/Fuzzing PR ＋ 可重現 Write-up），並在本地初始化 `security-research-portfolio` 公開索引倉庫 | 對齊 2026-11 證照 ROI 基準與五層 Proof-of-Work 金字塔 |

---

## 四、常見本地環境排障指南（Troubleshooting）

### 1. Apple Silicon（M1/M2/M3/M4）執行 `nexus-bin` 二進位容器

- **現象**：在 macOS ARM64 主機啟動 `./setup.sh up-bin` 時提示平台不符，或 GDB 無法使用 `ptrace`。
- **解法**：`docker-compose.yml` 已明確設定 `platform: linux/amd64`、`cap_add: [SYS_PTRACE]` 與 `security_opt: ["seccomp:unconfined"]`。請確認 Docker Desktop 已開啟 **Use Rosetta for x86_64/amd64 emulation on Apple Silicon**（Settings -> General），即可在容器內獲得與真實 x86_64 Linux 伺服器一致的暫存器（`rdi`, `rsi`, `rsp`, `rip`）、ELF 佈局與 `ptmalloc2` 行為。

### 2. AFL++ 搭配 AddressSanitizer（ASan）啟動時立即報錯退出

- **現象**：在 `nexus-bin` 內對開啟 `-fsanitize=address` 的目標執行 `afl-fuzz` 時，出現 `Fork server handshake failed` 或記憶體配置失敗。
- **解法**：
  1. 64 位元環境下 ASan 需要映射約 `16 TiB`–`20 TiB` 的虛擬影子記憶體（Shadow Memory），啟動 `afl-fuzz` 時**必須加上 `-m none`** 關閉虛擬記憶體上限限制。
  2. 容器環境若無權修改宿主機 `/proc/sys/kernel/core_pattern`，請於執行前匯出環境變數：
     ```bash
     export AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1
     export AFL_SKIP_CPUFREQ=1
     afl-fuzz -i seeds -o findings -m none -- ./target_asan @@
     ```

### 3. 本地代理（Caido / Burp Suite）攔截 Node.js 或 `curl` HTTPS 流量出現憑證錯誤

- **現象**：在 Ch02 等實驗將流量導向 `127.0.0.1:8080` 代理時，Node.js 或 `curl` 拋出 `UNABLE_TO_VERIFY_LEAF_SIGNATURE` 或 TLS 握手失敗。
- **解法**：切勿在安全審計工具鏈中養成關閉憑證驗證（如 `NODE_TLS_REJECT_UNAUTHORIZED=0`）的壞習慣，否則將無法在實驗中觀測真實的憑證驗證邊界。請匯出代理的 Root CA 憑證（PEM 格式）並顯式注入信任根：
  ```bash
  export SSL_CERT_FILE="$HOME/.certs/proxy-ca.crt"
  export NODE_EXTRA_CA_CERTS="$HOME/.certs/proxy-ca.crt"
  ```

### 4. 連接埠衝突或雙花實驗後帳本狀態異常

- **現象**：啟動 `./setup.sh up` 時報錯 `Bind for 127.0.0.1:5432 failed: port is already allocated`，或完成 Ch06/Ch12 實驗後測試帳戶餘額已被扣至 `0` 甚至負值。
- **解法**：
  - 若本機已安裝原生 PostgreSQL 或 Redis 佔用 `:5432` / `:6379`，可先暫停本機服務，或於 `labs/docker-compose.yml` 調整左側宿主機映射埠（容器內部網路 `postgres:5432` 與 `redis:6379` 不受影響）。
  - 每次完成會破壞資料狀態的漏洞利用實驗後，執行 `./setup.sh reset` 即可一鍵銷毀舊資料卷並重新載入 `db/init.sql`，將 `acct-alpha-01` 與 `acct-beta-01` 餘額恢復為 `10,000` 分基準值。
