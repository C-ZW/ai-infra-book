# 第 34 章：企業級 AppSec 工程與 SDLC 防線設計

前兩章我們把視角從單點挖洞一路拉高到跨層利用鏈、AI 輔助審計，以及第 33 章的嚴重度量化（CVSS v4.0、EPSS、CISA KEV）與協調揭露。當你能熟練地站在攻擊者角度拆解系統之後，一旦轉身成為企業內部的 AppSec（應用安全）或 Product Security 工程師，馬上就會迎來一個更棘手的挑戰：**怎麼把攻擊者的破防思維，反過來變成一套能保護整間公司、又不會拖垮開發速度的防禦工程？**

靠人工一張單一張單地追著修，永遠跑不贏業務團隊每天發 PR 的速度。今天你在結帳微服務好不容易修掉一個 SSRF，下禮拜行銷團隊開一個新服務，工程師順手寫了一行原生 `fetch(userUrl)`，一模一樣的洞又原封不動長了出來。真正的企業級 AppSec 工程，不是把資安團隊變成卡在每個 PR 前面的人工審核瓶頸，更不是在 CI 裡塞滿誤報率高達 `30%` 的預設掃描器把大家逼瘋；而是鋪好一條 **Paved Road**（安全預設路徑），讓開發者「順著最省力的方式寫 code 就自然是安全的」，再搭配誤報率 `< 3%–5%` 的高精準 CI 閘門與可達性分析，把防線牢牢釘進日常的軟體開發生命週期（SDLC）裡。

---

## 從你已知的出發

為什麼很多公司明明買了昂貴的商業 SAST（靜態程式碼分析）與 SCA（相依套件掃描）工具，把它們全掛上 GitHub Actions 的 PR 檢查，結果三個月後不是被開發團隊聯名要求關掉，就是大家習慣看都不看就直接在程式碼裡塞一行 `// nosemgrep` 跳過？

因為預設的全量掃描規則根本不懂你們家的系統架構。當一個 50 人的工程團隊每天發 100 個 PR，而掃描器每天跳出 30 個假警報（比如把完全不會打進生產環境的本地文件產生器套件報成 Critical，或是把內部固定常數拼接誤判成 SQL 注入），工程師每天光寫豁免單就得燒掉將近一個全職人力，久而久之就會對所有資安警報徹底麻痺（Alert Fatigue）。這正是傳統 SDLC 防線的兩大死穴：一是**底層框架沒封死危險操作，害同類漏洞不斷回歸復發**；二是**把高噪音的猜測型規則放進 PR 阻斷層，親手摧毀了工程團隊對資安閘門的信任**。接下來我們就從 NexusPay 的架構出發，把這兩件事徹底翻轉過來。

---

## 機制與推導

### 攻擊者目標與實質影響

在每天上百個 Commit 高速推進的 SDLC 裡，攻擊者佔盡了天然的不對稱便宜：**防守方必須守住過去五年寫下的每一行歷史程式碼、外加今天新合併的每一個 PR；而攻擊者只要在某個新上線的邊緣路由裡，找到一次忘記掛上的權限檢查或一行裸寫的 HTTP 請求，就能一槍打穿防線。**

拿全書的 **NexusPay** 多租戶支付平台來說，如果 SDLC 缺乏結構性的工程防線，攻擊者最常從下面三個裂縫拿到實質利益：

第一是**新功能上線帶來的權限與業務邏輯退化**（BOLA / BFLA）。比如財務團隊趕著上線一支新的月結對帳單匯出 API，寫 Controller 的工程師一時忘記掛上授權 Decorator，或是寫 SQL 時漏加了 `WHERE tenant_id = $1`，外部攻擊者只要改個參數就能跨租戶看光別家商戶的帳本明細與餘額，直接打破第 1 章定下的租戶隔離不變量。

第二是**繞過安全規範的內網橫向移動**（SSRF 逃逸）。某個新微服務為了測試商戶 Webhook，沒有用公司統一的安全套件，而是直接呼叫 Node.js 原生的 `fetch()`。攻擊者馬上就能利用 HTTP `302` 重新導向或短 TTL 的 DNS Rebinding（見第 11 章），穿過 DMZ 去偷讀內網服務或雲端中繼資料位址 `169.254.169.254` 的短期 IAM 憑證。

第三是**假警報海嘯掩護了真正的致命破口**（Alert Fatigue）。當資安管線每天吐出幾百張分不清真假的套件與靜態掃描工單時，真正符合第 33 章標準——也就是 `EPSS ≥ 0.1`、而且在線上公開路由直接可達（Reachable）的致命漏洞——反而被埋在垃圾警報堆裡沒人理會，白白錯過 `24 小時` 的黃金止血時間窗。

所以 AppSec 工程師的核心任務不是去當「抓出最多單點 Bug 的糾察隊」，而是用架構封裝把整類漏洞從程式碼庫裡連根拔起，並把 CI 閘門的訊噪比調到開發者心服口服的水準。

---

### Paved Road 與 Secure-by-Default 框架設計

什麼叫做 **Paved Road**（安全預設路徑，也常被稱為 Golden Path）？一句話講完：**把安全的寫法包成最順手、最省事的共用元件，讓工程師偷懶照著預設方式寫就自然不會出洞；反過來，如果誰想繞過共用元件去碰底層的危險 API，不但寫起來很麻煩，還會在 CI 裡立刻被抓出來審核。**

與其寫一百頁的《安全編碼規範》求大家「寫 SQL 記得綁 `tenant_id`、發 HTTP 請求記得擋內網 IP、開新路由記得掛 Guard」，不如直接把這些安全不變量寫死在 NexusPay 的三個基礎設施封裝層裡：

#### 第一根支柱：預設拒絕的統一授權中介層（Fail-Closed Authorization）

看看一般 Express 或 NestJS 專案最容易出事的寫法：預設所有路由都是公開的，得靠工程師自己在每個 Controller 方法上面乖乖貼一行 `@UseGuards(AuthGuard)`。只要有人趕下班少貼了一行，那支 API 就直接對全網裸奔了。

Paved Road 的做法是把預設值徹底倒過來，改成**全域預設拒絕**（Default-Deny）：

```typescript
// 只有明確貼上 @Policy 或 @PublicEndpoint 的路由才准放行，兩者都沒貼就一律擋死
@Policy({ auth: 'jwt', tenantScoped: true, roles: ['merchant_admin'] })
@Post('/v1/tenants/:tid/payouts')
async createPayout(...) { ... }

@PublicEndpoint({ reason: 'liveness_probe', ticket: 'SEC-1042' })
@Get('/healthz')
async healthCheck() { ... }
```

光有 Decorator 還不夠，我們還要在**應用程式啟動測試與 CI 路由表斷言**裡加上一道硬檢查：每次跑測試啟動 Server 時，自動掃過路由表上的所有端點 Metadata。只要發現任何一個路由既沒有貼 `@Policy`、也沒有明確標記 `@PublicEndpoint`，啟動測試就當場失敗，連 PR 都別想合併。只要全域攔截器涵蓋了所有路由器，這招就能從架構上徹底消滅「新增 API 忘了掛權限檢查」的人為疏失（至於 `@Policy` 裡面的角色權限有沒有開太寬，再交給設計審查與授權矩陣測試去把關）。

#### 第二根支柱：強制綁定租戶上下文的資料庫封裝（Tenant-Scoped DB Wrapper）

為什麼 BOLA（跨租戶越權）跟 SQL 注入抓都抓不完？因為大多數專案都讓業務邏輯直接去拿底層的資料庫連線池（像是直接呼叫 `pool.query(...)` 或 `prisma.$queryRawUnsafe(...)`）。工程師寫十條查詢，只要有一條忘了在 `WHERE` 後面加上 `AND tenant_id = $2`，租戶隔離就破功了。

要一勞永逸，就得把裸連線池藏起來，只給業務層用封裝好的 **`TenantDbClient`**：

1. **從型別與呼叫介面強制要求租戶憑證**：`TenantDbClient` 只開放一個 `queryScoped(ctx: AuthContext, sql: string, params: unknown[])` 方法。呼叫端如果不把認證中介層驗過的 `AuthContext`（裡面帶有非空的 `tenantId`）傳進來，連編譯跟執行期第一關都過不了。
2. **交易內自動綁定 PostgreSQL 列級安全性（RLS）**：`queryScoped` 在借出資料庫連線後，會先開啟一個明確的交易（`BEGIN`），接著自動執行參數化的 `SELECT set_config('app.current_tenant_id', $1, true)`（這在 PostgreSQL 裡等同於只在當前交易內有效的 `SET LOCAL`），然後才跑業務查詢並 `COMMIT`。只要資料表有啟用對應的 RLS 政策、而且應用程式用的資料庫帳號受 RLS 約束（不是 `BYPASSRLS` 或超管帳號），就算工程師寫 SQL 時真的忘記寫 `WHERE tenant_id = ...`，PostgreSQL 引擎底層也會自動幫你把別家租戶的資料列濾得一乾二淨。
3. **把跨租戶逃生門關進鐵籠子**：當然，系統總有些背景結算或全站對帳批次真的需要跨租戶查資料。這些特例必須改用另一個獨立的 `SystemDbClient`，而且只要誰在程式碼裡引入了 `SystemDbClient`，CI 的客製化規則跟 `CODEOWNERS` 就會自動跳出來，強制要求 AppSec 團隊簽核放行。

#### 第三根支柱：防 SSRF 與 DNS Rebinding 的安全出站封裝（SafeHttpClient）

還記得第 11 章我們怎麼打穿那些用正規表達式防 SSRF 的程式碼嗎？如果工程師只是在呼叫 `fetch(url)` 之前，先用字串檢查網址裡有沒有 `127.0.0.1` 或 `localhost`，攻擊者只要丟一個八進位／十進位 IP、IPv4-mapped IPv6 位址（`[::ffff:169.254.169.254]`）、利用 HTTP `302` 轉址，或者用短 TTL 的 **DNS Rebinding**（在預檢 DNS 時回傳合法公網 IP，等下一毫秒 `fetch` 真正建立 TCP 連線時瞬間切成 `127.0.0.1`），防線就瞬間瓦解了。

一個真正能扛住實戰攻擊的 `SafeHttpClient`（或 `safeFetch`），必須在**底層 Socket 建立連線的那一刻**把 TOCTOU（檢查與使用分離）的時間差徹底歸零：

1. **嚴格鎖死協定與標準埠號**：只准許 `https:` 與 `http:`（正式環境甚至可以預設只准 `https:`），並強制協定只能走標準埠號（`https:` 對 `443`、`http:` 對 `80`），把 `file://`、`gopher://` 與亂打內網非標準 Port 的路全封死。
2. **展開所有 IPv4 / IPv6 格式並核對私有網段黑名單**：不靠字串比對，而是把解析出來的每個 IPv4 與 IPv6 位址（包含把 `::ffff:0:0/96` 這類 IPv4-mapped IPv6 拆開還原成 32-bit 整數）拿去做位元遮罩比對，一口氣擋掉 `127.0.0.0/8`、`10.0.0.0/8`、`172.16.0.0/12`、`192.168.0.0/16`、`169.254.0.0/16`、`100.64.0.0/10`、`0.0.0.0/8` 以及 IPv6 的 `::1/128`、`fc00::/7`、`fe80::/10`。
3. **自訂 `lookup` 鎖定已驗證的 IP 建立 TCP 連線**：這是最關鍵的一步。我們先呼叫一次 `dns.lookup(host, { all: true })`，確認解析出來的每一個 IP 都乾淨無毒後，直接把第一個合法的 `resolvedIp` 釘死在 `http.request` 的自訂 `lookup` 回呼裡。這樣底層 Socket 連線時根本不會去發第二次 DNS 查詢，同時又能保留原本的 `hostname` 讓 TLS SNI 與 HTTP `Host` 標頭正常運作，把 DNS Rebinding 徹底廢掉。
4. **預設關閉自動跟隨重新導向**：把轉址設為手動處理（一旦收到 `3xx` 狀態碼就直接拒絕或要求重頭走一遍步驟 1 到 3 的 IP 驗證），絕不讓 `302 Found` 帶著連線偷偷溜進內網。

---

### 規模化輕量威脅建模（Lightweight Threat Modeling）

鋪好程式碼層的 Paved Road 之後，我們把防線再往前推一步：在工程師還沒動手寫 code、還在寫設計文件（RFC / Design Doc）的時候，怎麼做威脅建模（Threat Modeling）？

很多公司推不動威脅建模，是因為資安部門要求「不管改什麼功能，都要畫一張超複雜的 DFD 資料流圖，再填滿 20 頁的 STRIDE 試算表」。在一個每天上百個 PR 的敏捷團隊裡，這種官僚流程只會逼大家假裝沒改架構、偷偷繞過審查。

要讓威脅建模在高速團隊裡真正活下來，秘訣是「**只攔高風險變更的觸發器**」加上「**30 分鐘四問快篩**」：

首先，占日常開發八成以上的改動——像是改前端畫面排版、調文案、或是在既有封裝內改商業計算公式——**完全不需要找 AppSec 開會**。只有在設計文件碰到了下面這 **5 條高風險邊界觸發條件**時，才自動打上標籤、排一場 30 分鐘的輕量設計審查：
- 新增或修改登入認證、多租戶授權邏輯、JWT 或 Session 的生命週期。
- 新增會由伺服器對外發起網路請求的功能（例如 Webhook 回呼、遠端抓檔、第三方 API 串接）或新增跨微服務邊界。
- 改動資料庫的多租戶隔離方式，或是新增儲存敏感個資／金鑰的資料表。
- 引入新的檔案格式解析器、反序列化機制，或新增底層 C/Rust FFI 原生模組。
- 新增或修改密碼學演算法、金鑰管理與簽章驗證流程。

進到這 30 分鐘的設計審查會議時，也不用寫長篇大論，大家只要對著架構白板回答 **4 個核心問題**就能收工：
1. **我們要建什麼？** 標出新開的外部輸入點（Source）、跨越的信任邊界（TB-1 到 TB-4），以及最後碰到底層資源的危險操作（Sink）。
2. **哪條安全不變量可能會破功？** 站在駭客角度想，這裡最肥的目標是什麼？（比如能不能跨租戶偷看帳本？能不能突破單筆 `$100.00` 的提領上限？能不能把 `libnexus-parse` 的緩衝區寫爆？）
3. **現有的 Paved Road 擋得住嗎？** 先確認這個新功能有沒有乖乖用上 `SafeHttpClient`、`TenantDbClient` 跟預設拒絕的 `@Policy`。只要現成的 Paved Road 就擋得住，直接打勾通過；只有遇到 Paved Road 沒覆蓋到的新場景，才需要動腦設計專門的防禦邏輯。
4. **怎麼讓 CI 自動幫我們盯著它不退化？** 在散會前定下一條能自動跑在 CI 裡的回歸測試（比如寫一個故意不帶 `tenantId` 的負向單元測試，或加一條 Semgrep 規則），確保三個月後別人來重構這塊程式碼時，不會把今天定好的防線順手刪掉。

---

### CI/CD 安全閘門設計：低誤報 SAST、Secret Scanning 與可達性分析

當程式碼寫好、發起 Pull Request 進到 CI/CD 管線時，AppSec 最重要的工程紀律就是：**只有誤報率極低（`< 3%–5%`）、而且修法一清二楚的規則，才准放進 PR 阻斷閘門（Blocking Gate）；其他所有帶猜測性質的深層掃描，一律移到背景非同步分診（Async Audit）。**

#### 1. 兩層式 SAST 架構：為什麼 Paved Road 能把誤報率壓到 `< 3%`？

為什麼一般開箱即用的通用 SAST 規則誤報率動輒 `30%`？因為通用規則不認識你們家的架構，它看到任何字串拼接就先喊「可能有 SQL 注入！」，看到任何 URL 變數就先喊「可能有 SSRF！」，完全不管上游是不是早就擋掉了。

但當你建好了前面那三根 Paved Road 支柱，你在 PR 阻斷層要寫的 Semgrep 或 CodeQL 規則就徹底變簡單了——**你根本不用去猜那條複雜的跨檔案資料流到底安不安全，你只要抓「誰敢在業務目錄裡繞過 Paved Road、直接呼叫危險的原生 API」就好了！**

我們把 SAST 拆成乾淨的兩層：

- **第一層：PR 同步阻斷閘門（Blocking Gate，目標誤報率 `< 3%–5%`）**。只放針對內部封裝規範的 AST 結構檢查規則。例如：
  - 在 `src/services/` 業務目錄底下，誰敢直接呼叫全域 `fetch(...)` 或 `import axios`，不乖乖用 `safeFetch`，立刻阻斷 PR！
  - 在業務目錄底下，誰敢直接對連線池呼叫 `pool.query(...)`，不走 `TenantDbClient.queryScoped(...)`，立刻阻斷 PR！
  - 誰敢在 Controller 貼 `@PublicEndpoint` 卻沒填核准工單編號，立刻阻斷 PR！
  這種「抓違規 API 呼叫」的語法樹比對非常精準，只要鎖定目錄範圍與匯入名稱，誤報率可以輕鬆壓在 `3%` 以下。而且開發者看到紅燈時，錯誤訊息直接告訴他「請把 `fetch` 換成 `src/security/safe-http.ts` 的 `safeFetch`」，花 30 秒改一行就能過關，完全不會產生怨氣。
- **第二層：非同步夜間深層掃描（Async / Nightly Audit）**。那些耗時十幾分鐘的跨檔案 CodeQL 污點追蹤、或是剛寫出來還在調校的實驗性規則，全部放到每天半夜的背景排程去跑。掃出來的結果先流進 AppSec 團隊的分診佇列（或是接上第 32 章教的確定性驗證管線刷掉誤報），確定真的是漏洞之後，再開成附帶 PoC 的修補工單派給開發團隊，絕不拿還沒確認的猜測去卡大家的日常 PR。

#### 2. Secret Scanning 與外洩金鑰秒級自動撤銷

把 AWS 金鑰（`AKIA...`）、GitHub Token（`ghp_...`）或 Stripe 正式金鑰（`sk_live_...`）不小心寫進程式碼推上 Git，只要 Commit 一進到遠端歷史紀錄，就必須當成已經外洩處理。

完整的金鑰防線要雙管齊下：第一關是在開發者本機的 `pre-commit` Hook 與 CI 的 PR Diff 檢查裡，同時用高精準的前綴特徵與高熵值（Entropy）偵測攔截，並用路徑白名單避開測試假資料（Test Fixtures）；第二關則是**自動化驗證與秒級吊銷**——一旦偵測到真金鑰不小心被推上分支，背景管線先打雲端廠商的驗證 API 確認這把金鑰是不是活的，只要確認有效，馬上自動呼叫撤銷或輪換 API 把它廢掉，把外洩暴露時間從「等工程師隔天早上看到信去處理的十幾個小時」直接壓縮到幾分鐘以內。

#### 3. 軟體組成分析（SCA）與可達性分析（Reachability Analysis）

傳統的相依套件掃描（只看 `package-lock.json` 或 `Cargo.lock` 裡面有沒有中標的版本號）是另一個讓工程師崩潰的假警報製造機。一個中型 Node.js 服務隨便都有五百個間接依賴套件，今天某個只在本地跑單元測試或編譯前端文件時才會用到的開發套件（`devDependencies`）爆了一個 `CVSS 9.1` 的 CVE，傳統掃描器就跳出來逼全組停下工作緊急升級。

現代 AppSec 解決這個痛點的殺手鐧，就是**可達性分析**（Reachability Analysis）。它不再只看版本清單，而是幫你的應用程式跟第三方套件建出完整的**靜態呼叫圖**（Call Graph）與**符號引用圖**，按三步過濾：

第一步，先看這個有問題的套件**到底有沒有被打包進最終的正式環境容器映像檔裡**（先把純 `devDependencies` 分開，同時順手確認 CI 建置環境本身會不會拿外部不可信輸入餵給這個開發套件）。

第二步，從線上服務的外部進入點（Entrypoints）順著函式呼叫圖一路往下追，看程式執行時**有沒有任何一條路徑，真的會呼叫到該 CVE 出事的那個具體函式或方法**。如果我們雖然引入了那個套件，但只用了它的日期格式化函式，根本沒呼叫到它出洞的 XML 解析函式，那就是「函式級不可達」（Unreachable）。

第三步，結合我們在第 33 章學過的 **CVSS v4.0 + EPSS（`≥ 0.1`）+ CISA KEV** 做精準分流：只要套件漏洞命中 `EPSS ≥ 0.1` 或進了 CISA KEV，一律觸發**立即處置（立即分診）**；一旦呼叫圖確認它在正式環境（或會碰外部輸入的建置環境）**真的可達**，就嚴格照嚴重度執行 **`24 小時`（嚴重）** 或 **`7 天`（高危）** 的強制修復 SLA；反過來，如果立即分診確認它連正式映像檔都沒進、建置期也完全碰不到外部輸入，就把這份「不可達證據」存檔留底，轉入每月的例行套件升級排程，絕不浪費工程師寶貴的救火精力。

---

### 實例推導（Worked Example）：50 人團隊 SAST 誤報率 30% 與客製化 `< 3%` 規則之 ROI 量化

口頭說「降誤報很重要」不夠有說服力，當你要向工程副總（VP of Engineering）爭取兩週的工程人力去建置 Paved Road 與客製化 Semgrep 規則時，最有效的武器是直接算出一張**工程工時與投資報酬率（ROI）對照表**。

我們直接拿一個 **`50` 位工程師、每天合併 `100` 個 PR** 的中型研發團隊，把「直接開預設 SAST（誤報率 `30%`）」跟「建置 Paved Road + 客製化規則（誤報率壓到 `< 3%`，以下取 `2%` 實算）」的成本攤開來算清楚：

```text
[基準團隊參數]
- 工程團隊規模：50 位工程師（每天總可用開發工時 = 50 × 8 = 400 工程師小時/天）
- 每日 PR 合併量：100 PRs/天（平均每人每天發 2 個 PR），每月按 20 個工作天計算
- 單件阻斷警報的人工查證成本：15 分鐘 = 0.25 工程師小時/件
  （包含：被打斷切出原本思緒、翻跨檔案資料流、確認是不是假警報、寫豁免註解重跑 CI）

-------------------------------------------------------------------------
情境 A：直接把通用 SAST 預設規則集掛進 PR 阻斷層（假警報佔比 30%）
-------------------------------------------------------------------------
假設每天在 PR 階段共觸發 100 件阻斷警報，其中 30% 是假警報：
1. 每日假警報數 = 100 件 × 30% = 30 件假警報/天
2. 每日白白燒掉的查證工時 = 30 件 × 0.25 小時 = 7.5 工程師小時/天
3. 每月白白燒掉的查證工時 = 7.5 小時/天 × 20 天 = 150 工程師小時/月
4. 產能損耗與組織崩壞後果：
   - 每天燒掉 7.5 小時，佔全團隊總工時的 7.5 / 400 = 1.875%，
     相當於團隊裡隨時有約 0.94 名（快要 1 整名）全職資深工程師，每天從早到晚什麼功能都不寫，專門在幫掃描器擦屁股。
   - 更致命的是這 30 次打斷都發生在「工程師正準備合併 PR」的節骨眼上；不出三個禮拜，團隊就會對資安紅燈徹底失去耐心，逼迫把 SAST 降級成不阻斷的 Audit-only（只看事後報表），整道防線名存實亡。

-------------------------------------------------------------------------
情境 B：建置 Paved Road 安全封裝 + 客製化高精準規則（假警報佔比 < 3%，取 2% 計算）
-------------------------------------------------------------------------
把愛亂猜的通用啟發式規則移出 PR 阻斷層（改放到半夜非同步掃描並搭配自動化過濾），
PR 阻斷層只留「抓誰繞過 Paved Road」的高精準 AST 規則。在同樣每日 100 件 PR 檢查警報的基準下，假警報降為 2%：
1. 每日假警報數 = 100 件 × 2% = 2 件假警報/天
2. 每日假警報查證工時 = 2 件 × 0.25 小時 = 0.5 工程師小時/天
3. 每月假警報查證工時 = 0.5 小時/天 × 20 天 = 10 工程師小時/月

-------------------------------------------------------------------------
投入產出比（ROI）與回本天數（Break-even）實算
-------------------------------------------------------------------------
- PR 階段每天省下的無效分診工時（毛節省）= 7.5 - 0.5 = 7.0 工程師小時/天
  （把每個月 4 小時的規則維護成本攤提到 20 個工作天，即每天 0.2 小時，則每日淨節省 = 6.8 工程師小時/天）
- 每月省下的無效分診工時：毛節省 = 150 - 10 = 140 工程師小時/月
  （扣除每月 4 小時規則維護後，每月淨節省 = 136 工程師小時/月）
- 前期一次性研發投入（寫好 SafeHttpClient + TenantDbClient + 10 條客製化 Semgrep 規則 + 接進 CI）：
  共投入 80 工程師小時（約 2 位工程師合作 1 個禮拜）。
- 後續規則微調維護成本：每月 4 工程師小時。
- 幾天就能回本（Break-even）：
  * 按毛節省算：80 小時 ÷ 7.0 小時/天 ≈ 11.43 個工作天
  * 按扣掉維護的淨節省算：80 小時 ÷ 6.8 小時/天 ≈ 11.76 個工作天（第 12 個完整工作日就徹底回本，花不到 3 週！）
- 半年（6 個月 = 120 個工作天）下來在 PR 階段賺回來的淨工時：
  總毛節省 (120 × 7.0) - 前期投入 (80) - 6 個月維護 (6 × 4)
  = 840 - 80 - 24 = 736 工程師小時
  （按每人月 160 小時換算，半年就幫研發團隊省下約 4.6 個人月的假警報查證消耗；註：若夜間背景掃描仍保留部分啟發式規則，則另外計算 AppSec 團隊的背景分診工時）。
```

把這張算式攤在工程主管面前，沒有人會反對花 `80` 小時去鋪 Paved Road——因為第 `12` 個工作天就回本了，半年還能幫團隊多賺出 `736` 個小時（約 `4.6` 個人月）的真實研發產能，而且換來的是一道大家願意遵守、不會隨便被關掉的自動化防線。

---

### 漏洞管理 SLA 治理與跨團隊協作權衡

就算有了 Paved Road 跟精準的 CI 閘門，還是會有歷史遺留的舊系統漏洞、或是第三方開源套件突然爆出新的 0-day。這時候該怎麼定修補期限，才不會跟產品團隊吵成一團？

延續第 33 章與全書的基準門檻，NexusPay 的漏洞修復 SLA 完全看「可驗證的真實曝險」（至於 ISO 27001 或 SOC2 那些合規稽核條文不是本書重點，這裡只談實戰風險治理）：

| 風險分級 | 判定條件（CVSS v4.0 + EPSS / KEV + 可達性分析） | 強制修復 SLA | 執行與升級處置機制 |
|---|---|---|---|
| **嚴重**（Critical） | CVSS v4.0 `≥ 9.0`（或經確認可直接打穿帳本不變量、跨租戶隔離與核心憑證）且在線上環境真實可達；只要搭配 `EPSS ≥ 0.1` 或列入 CISA KEV 一律立即啟動處置 | **`24 小時`** | 自動開立最高優先級事件單並呼叫值班人員；超過 `24 小時` 還沒完成止血緩解，直接凍結該服務除資安修補以外的日常部署 |
| **高危**（High） | CVSS v4.0 `7.0–8.9` 且具真實可達攻擊路徑（尚未達嚴重級核心帳本破壞）；若搭配 `EPSS ≥ 0.1` 或列入 CISA KEV，立即啟動分診與止血，並在期限內完成根因修補 | **`7 天`** | 強制排入當週 Sprint 修補；若因重大架構相依無法在 `7 天` 內修完，必須走限時豁免程序 |
| **中低危／確認不可達** | CVSS v4.0 `< 7.0`（若搭配 `EPSS ≥ 0.1` 或列入 KEV 同樣須立即分診核實影響，確認達高危／嚴重者依上列等級升級 SLA，確認僅屬中低危者於評估後排程），或雖初始基礎分高但經立即分診確認在生產與建置環境皆不可達並已留存證據 | **排入常規技術債**（30–90 天） | 不打斷日常開發交付，優先透過升級 Paved Road 共用元件或每月例行套件更新一次清掉 |

在跨團隊協作時，最常發生摩擦的就是「**例外豁免**」（Exceptions / Waivers）。如果資安團隊死板板地說「不准豁免，不管什麼原因 7 天沒修完就封鎖部署」，業務團隊被逼急了只會想辦法把掃描器繞過去；但反過來，如果隨便簽一張「永久豁免單」，那些高危漏洞就會在系統裡躺到天荒地老。

最務實的工程解法是推行「**到期自動失效的限時豁免**」（Time-boxed Waiver）：如果某個高危漏洞真的因為牽涉底層架構改版、沒辦法在 `7 天` 內徹底根治，業務團隊可以申請一張最長 `14 天` 或 `30 天` 的限時豁免單，但前提是**必須先掛上補償性止血控制**（比如先在 Nginx / API Gateway 擋掉該異常參數或加上嚴格限流）。而且這張豁免單是有寫死 `expires_at` 日期的程式碼設定——時間一到，CI 閘門與警報就會自動重新跳紅燈，逼著大家把真正的根因修補還清。

另外，衡量一個 AppSec 團隊成不成功，千萬別只看「今年抓了幾個洞」（這是落後指標），更要盯緊**領先指標**（Leading Indicators）：也就是「**全公司有百分之多少的出站 HTTP 呼叫已經換成 `SafeHttpClient`？有百分之多少的微服務已經接上 `TenantDbClient`？**」當 Paved Road 的覆蓋率從 `40%` 推升到 `95%`（一口氣拉高 `55` 個百分點），受安全預設保護的版圖大幅擴張，同類漏洞的回歸復發率自然就會斷崖式下降。

---

## 故障模式與防禦

在把這套 SDLC 防線推進真實企業的過程中，有四個架構與流程上的暗礁最容易讓防線破功。

### 故障模式 1：抑制註解滿天飛，把安全閘門變成裝飾品（Suppression Sprawl）

當你在 CI 裡掛上 Semgrep 之後，很快就會發現有聰明的工程師為了趕在星期五下午下班前合併 PR，不把 `fetch` 換成 `safeFetch`，而是在上面隨手加一行 `// nosemgrep: nexuspay-no-raw-fetch`，或是自己亂貼一個 `@SecurityReviewed` 標籤就闖關成功了。

要堵住這個逃生門濫用，做法很簡單：把所有包含 `nosemgrep`、`@PublicEndpoint`、`@SecurityReviewed` 以及引入 `SystemDbClient` 的程式碼變更，全部寫進 GitHub 的 **`CODEOWNERS`** 保護清單裡。任何人只要在 PR 裡新增這幾個關鍵字，GitHub 就會強制要求必須有 `@appsec-team` 群組的成員按下 Approve 才能合併，而且註解後面硬性規定要附上核准的資安工單編號。

### 故障模式 2：自家程式碼很乖，卻被第三方 SDK 從背後開槍（Transitive Bypass）

你們團隊自己寫的每一行 TypeScript 都乖乖用了 `SafeHttpClient`，結果某天引入了一個第三方的圖片浮水印套件或 Webhook SDK，那個套件在它的 `node_modules` 裡面自己偷偷呼叫了 Node.js 原生的 `http.request`，照樣幫攻擊者把 SSRF 請求打進了 `169.254.169.254`。

這告訴我們：不能只靠應用層的 Paved Road 單打獨鬥，還必須在底層基礎設施補上**出站網路隔離**（Egress NetworkPolicy）。直接在 Kubernetes Pod 的網路層或雲端 VPC 路由上，預設封鎖所有業務容器連往雲端中繼資料位址 `169.254.169.254/32` 與非必要內網網段的 TCP 連線。應用層有 `SafeHttpClient` 把關、網路層有 Egress Policy 兜底，才叫真正的縱深防禦。

### 故障模式 3：測試環境為了圖方便，把安全機制全關了（Parity Drift）

有些團隊在正式環境開了完整的 `@Policy` 授權攔截器跟 PostgreSQL RLS，結果在跑本地開發跟 CI 整合測試時，嫌每次測試都要簽發 JWT 跟設 `tenant_id` 太麻煩，就在測試設定裡加了一個 `DISABLE_AUTH_AND_RLS=true`。這樣一來，你的 CI 測試跑得再綠，其實根本沒測到真正的權限邊界與 RLS 過濾邏輯，直到上線那天大爆炸。

防禦鐵律是：**整合測試環境的安全設定必須跟正式環境一模一樣**。與其讓工程師為了省事去關掉權限檢查，AppSec 團隊應該寫好一個超好用的測試輔助函式（例如 `createTestAuthHeader({ tenantId: 't_acme', role: 'merchant_admin' })`），讓大家在寫測試時只要呼叫一行就能拿到合法簽章的測試用 JWT，既好寫又能實打實地測到每一道安全防線。

### 故障模式 4：無限延期的「7 天 SLA」與永久技術債（Permanent Snoozing）

如果漏洞管理系統允許開發團隊在 `7 天` 高危 SLA 到期前一天，點個按鈕把到期日往後延一個 Sprint，那半年後你就會看到系統裡躺著兩百張「已經延了十次」的高危漏洞單。

要治好這種拖延症，可以借鏡 SRE 的錯誤預算（Error Budget），幫每個微服務團隊設立明確的「**安全債預算**」（Security Debt Budget）：只要某個服務累積超過門檻的逾期 `7 天` 高危漏洞，或是出現任何一張逾期的 `24 小時` 嚴重漏洞，發布管線就會自動亮起紅燈、暫停該服務的新功能上線，直到團隊把逾期的安全債清回安全水位線以內為止。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

現在我們直接動手幫 **NexusPay** 打造兩個真槍實彈的 Paved Road 核心模組（防 SSRF 與 DNS Rebinding 的 `SafeHttpClient`，以及強制綁定租戶 RLS 的 `TenantDbClient`），再寫兩條誤報率趨近於零的客製化 Semgrep 規則，在本地親自驗證它們怎麼攔下危險的原生呼叫、同時對合規程式碼做到 **0 誤報**。

### 步驟 1：建立 Paved Road 安全封裝模組（20 分鐘）

在本地建一個空目錄 `nexuspay-paved-road/`，在裡面寫好兩個核心安全模組：
1. `src/security/safe-http.ts`：實作 `safeFetch(rawUrl, options)`。它必須先檢查協定與標準埠號（`https:443` / `http:80`），接著用 `dns.lookup(host, { all: true })` 解出所有實際 IP，確認沒有任何一個 IP 落在私有或保留網段（包含 `127.0.0.0/8`、`10.0.0.0/8`、`169.254.0.0/16`、`172.16.0.0/12`、`192.168.0.0/16`、`100.64.0.0/10`、`::1`、`::ffff:0:0/96`、`fc00::/7`、`fe80::/10`），然後**用自訂的 `lookup` 回呼把通過檢查的 IP 鎖死在連線請求上**，並拒絕任何 `3xx` 自動轉址。
2. `src/security/tenant-db.ts`：實作 `TenantDbClient`，強制呼叫端傳入帶有非空 `tenantId` 的 `AuthContext`；在借出同一個資料庫連線後開啟交易（`BEGIN`），先跑參數化的 `SELECT set_config('app.current_tenant_id', $1, true)`，接著才跑業務 SQL 並 `COMMIT`。

### 步驟 2：撰寫低誤報的客製化 Semgrep 規則（10 分鐘）

建立 `.semgrep/paved-road.yaml`，寫入兩條專門抓「誰在 `src/services/` 目錄裡繞過 Paved Road」的精準規則：
- `nexuspay-no-raw-fetch`：只要在 `src/services/` 裡面看到直接呼叫 `fetch(...)`、`axios(...)` 或是匯入 `axios` / `node-fetch`，立刻報錯並提示改用 `safeFetch`。
- `nexuspay-no-raw-pool-query`：只要在 `src/services/` 裡面看到直接對物件呼叫 `.query(...)`（合規的 `TenantDbClient` 只會呼叫 `.queryScoped(...)`），立刻報錯並提示改用 `TenantDbClient`。

### 步驟 3：寫對照組服務並跑自動化驗證（15 分鐘）

1. 寫一支違規的 `src/services/webhook.ts`（裡面直接偷叫 `fetch(userUrl)`），再寫一支合規的 `src/services/report.ts`（乖乖使用 `safeFetch` 與 `TenantDbClient.queryScoped`）。
2. 跑單元測試，確認拿 `http://169.254.169.254/latest/meta-data/`、`http://[::ffff:127.0.0.1]/` 與非標準埠 `https://example.com:8080/hook` 去餵 `safeFetch` 時，都會當場拋出 `SsrfBlockedError`；確認傳空的 `tenantId` 給 `TenantDbClient` 會立刻被擋下來。
3. 執行 `semgrep --config .semgrep/paved-road.yaml --error src/services/`，確認它精準抓出 `webhook.ts` 的違規呼叫，而且對合規的 `report.ts` 保持 **0 誤報**。

---

### 參考解答

下面給出可以直接在本地（Node.js 22 + TypeScript `tsx` + Semgrep CLI）跑通的完整實作與驗證指令：

#### 1. 防 SSRF 與 DNS Rebinding 的 `src/security/safe-http.ts`

```typescript
import dns from 'node:dns/promises';
import net from 'node:net';
import http from 'node:http';
import https from 'node:https';

export class SsrfBlockedError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'SsrfBlockedError';
  }
}

export interface SafeFetchOptions {
  method?: 'GET' | 'POST';
  headers?: Record<string, string>;
  body?: string;
  timeoutMs?: number;
}

function ipv4ToInt(ip: string): number {
  return ip.split('.').reduce((acc, octet) => ((acc << 8) + Number(octet)) >>> 0, 0);
}

function isBlockedIPv4Int(num: number): boolean {
  const ranges: Array<[string, number]> = [
    ['0.0.0.0', 8],
    ['10.0.0.0', 8],
    ['100.64.0.0', 10],
    ['127.0.0.0', 8],
    ['169.254.0.0', 16],
    ['172.16.0.0', 12],
    ['192.168.0.0', 16],
  ];
  return ranges.some(([base, prefix]) => {
    const mask = prefix === 0 ? 0 : (~0 << (32 - prefix)) >>> 0;
    return (num & mask) === (ipv4ToInt(base) & mask);
  });
}

export function isBlockedIp(rawIp: string): boolean {
  const ip = rawIp.toLowerCase();
  if (net.isIPv4(ip)) return isBlockedIPv4Int(ipv4ToInt(ip));
  if (!net.isIPv6(ip)) return true;

  // 把 IPv6 正規化展開為 8 組 16-bit 整數，統一攔截 ::1、::、IPv4-mapped (::ffff:0:0/96)、ULA (fc00::/7) 與 Link-local (fe80::/10)
  let working = ip;
  if (working.includes('.')) {
    const lastColon = working.lastIndexOf(':');
    const v4Part = working.slice(lastColon + 1);
    if (!net.isIPv4(v4Part)) return true;
    const v4Int = ipv4ToInt(v4Part);
    const hi = ((v4Int >>> 16) & 0xffff).toString(16);
    const lo = (v4Int & 0xffff).toString(16);
    working = `${working.slice(0, lastColon)}:${hi}:${lo}`;
  }
  const [left, right] = working.split('::');
  const leftParts = left ? left.split(':') : [];
  const rightParts = right ? right.split(':') : [];
  const missing = 8 - (leftParts.length + rightParts.length);
  const full = [...leftParts, ...Array(Math.max(0, missing)).fill('0'), ...rightParts].map((h) => parseInt(h || '0', 16));
  if (full.length !== 8) return true;

  const isAllZeroPrefix = full.slice(0, 5).every((v) => v === 0);
  // 攔截 :: (未指定)、::1 (本機回環) 與 IPv4-compatible
  if (isAllZeroPrefix && full[5] === 0) {
    const v4Int = ((full[6] << 16) | full[7]) >>> 0;
    return v4Int <= 1 || isBlockedIPv4Int(v4Int);
  }
  // 攔截 ::ffff:0:0/96 (IPv4-mapped IPv6，包含點分十進位與 16 進位寫法如 ::ffff:7f00:1)
  if (isAllZeroPrefix && full[5] === 0xffff) {
    const v4Int = ((full[6] << 16) | full[7]) >>> 0;
    return isBlockedIPv4Int(v4Int);
  }
  // 攔截 fc00::/7 (Unique Local) 與 fe80::/10 (Link-local)
  if ((full[0] & 0xfe00) === 0xfc00 || (full[0] & 0xffc0) === 0xfe80) {
    return true;
  }
  return false;
}

export async function safeFetch(
  rawUrl: string,
  options: SafeFetchOptions = {}
): Promise<{ status: number; body: string }> {
  const parsed = new URL(rawUrl);
  if (parsed.protocol !== 'https:' && parsed.protocol !== 'http:') {
    throw new SsrfBlockedError(`Blocked protocol: ${parsed.protocol}`);
  }
  const expectedPort = parsed.protocol === 'https:' ? 443 : 80;
  const port = parsed.port ? Number(parsed.port) : expectedPort;
  if (port !== expectedPort) {
    throw new SsrfBlockedError(`Blocked non-standard port: ${port} for ${parsed.protocol}`);
  }

  // 若直接傳入 IP 字面量就當場檢查；若傳網域則先解析 DNS、檢查每一筆 A/AAAA 紀錄並鎖定連線 IP
  const host = parsed.hostname.replace(/^\[|\]$/g, '');
  let resolvedIp = host;
  let family: 4 | 6 = net.isIPv6(host) ? 6 : 4;

  if (!net.isIP(host)) {
    const records = await dns.lookup(host, { all: true });
    if (records.length === 0) throw new SsrfBlockedError('DNS lookup returned empty');
    for (const rec of records) {
      if (isBlockedIp(rec.address)) {
        throw new SsrfBlockedError(`Blocked resolved IP: ${rec.address}`);
      }
    }
    resolvedIp = records[0].address;
    family = records[0].family as 4 | 6;
  } else if (isBlockedIp(host)) {
    throw new SsrfBlockedError(`Blocked literal IP: ${host}`);
  }

  const transport = parsed.protocol === 'https:' ? https : http;
  return new Promise((resolve, reject) => {
    const req = transport.request(
      {
        hostname: host,
        port,
        path: `${parsed.pathname}${parsed.search}`,
        method: options.method ?? 'GET',
        headers: options.headers,
        // 自訂 lookup 直接回傳剛剛驗過的 resolvedIp，徹底封死連線階段的 DNS Rebinding
        lookup: (_hostname, opts, cb) => {
          if (typeof opts === 'object' && opts !== null && 'all' in opts && opts.all) {
            return cb(null, [{ address: resolvedIp, family }]);
          }
          return cb(null, resolvedIp, family);
        },
        timeout: options.timeoutMs ?? 5000,
      },
      (res) => {
        if (res.statusCode && res.statusCode >= 300 && res.statusCode < 400) {
          res.resume();
          reject(new SsrfBlockedError(`Redirects are disabled (status ${res.statusCode})`));
          return;
        }
        const chunks: Buffer[] = [];
        res.on('data', (c) => chunks.push(c));
        res.on('end', () => resolve({ status: res.statusCode ?? 0, body: Buffer.concat(chunks).toString('utf8') }));
      }
    );
    req.on('error', reject);
    req.on('timeout', () => req.destroy(new Error('Request timeout')));
    if (options.body) req.write(options.body);
    req.end();
  });
}

export const safeHttpGet = (rawUrl: string) => safeFetch(rawUrl, { method: 'GET' });
```

#### 2. 強制綁定租戶 RLS 的 `src/security/tenant-db.ts`

```typescript
export interface AuthContext {
  userId: string;
  tenantId: string;
}

export interface DbClientLike {
  query(sql: string, params?: unknown[]): Promise<{ rows: unknown[] }>;
  release(): void;
}

export interface DbPoolLike {
  connect(): Promise<DbClientLike>;
}

export class TenantDbClient {
  constructor(private readonly pool: DbPoolLike) {}

  async queryScoped(ctx: AuthContext, sql: string, params: unknown[] = []) {
    if (!ctx.tenantId || ctx.tenantId.trim() === '') {
      throw new Error('TenantContextViolation: missing tenantId');
    }
    // 借出同一條連線並開啟交易，讓 set_config(..., true) 在這個交易作用域內強制生效以觸發 PostgreSQL RLS
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      await client.query('SELECT set_config($1, $2, true)', ['app.current_tenant_id', ctx.tenantId]);
      const result = await client.query(sql, params);
      await client.query('COMMIT');
      return result;
    } catch (err) {
      await client.query('ROLLBACK').catch(() => {});
      throw err;
    } finally {
      client.release();
    }
  }
}
```

#### 3. 客製化 Semgrep 規則 `.semgrep/paved-road.yaml`

```yaml
rules:
  - id: nexuspay-no-raw-fetch
    patterns:
      - pattern-either:
          - pattern: fetch(...)
          - pattern: axios(...)
          - pattern: axios.$METHOD(...)
          - pattern: import ... from 'axios'
          - pattern: import ... from 'node-fetch'
    paths:
      include:
        - src/services/
    message: "禁止在業務服務直接匯入或呼叫原生 fetch/axios，請改用 src/security/safe-http.ts 提供的 safeFetch 以防禦 SSRF。"
    languages: [typescript, javascript]
    severity: ERROR

  - id: nexuspay-no-raw-pool-query
    pattern: $POOL.query(...)
    paths:
      include:
        - src/services/
    message: "禁止在業務服務直接呼叫底層連線池 query()，請改用 TenantDbClient.queryScoped() 確保強制租戶隔離。"
    languages: [typescript, javascript]
    severity: ERROR
```

#### 4. 執行自動化斷言與 Semgrep 閘門測試

建好對照用的 `src/services/webhook.ts`（裡面寫一行 `fetch(userUrl)`）跟 `src/services/report.ts`（裡面呼叫 `safeFetch` 與 `tenantDb.queryScoped`）之後，跑下面這兩段驗證指令：

```bash
# 1. 跑執行期單元測試：確認擋下雲端 metadata IP、IPv4-mapped IPv6、非標準埠 8080、空 tenantId，且交易內 SQL 順序正確
npx tsx -e "
import assert from 'node:assert/strict';
import { safeFetch, SsrfBlockedError } from './src/security/safe-http.ts';
import { TenantDbClient } from './src/security/tenant-db.ts';

await assert.rejects(() => safeFetch('http://169.254.169.254/latest/meta-data/'), SsrfBlockedError);
await assert.rejects(() => safeFetch('http://[::ffff:127.0.0.1]/'), SsrfBlockedError);
await assert.rejects(() => safeFetch('https://example.com:8080/hook'), SsrfBlockedError);

const executedSql: string[] = [];
const mockPool = {
  async connect() {
    return {
      async query(sql: string) { executedSql.push(sql); return { rows: [] }; },
      release() {},
    };
  },
};
const db = new TenantDbClient(mockPool);
await assert.rejects(() => db.queryScoped({ userId: 'u1', tenantId: '' }, 'SELECT 1'), /TenantContextViolation/);
await db.queryScoped({ userId: 'u1', tenantId: 't_acme' }, 'SELECT * FROM payouts');
assert.deepEqual(executedSql, ['BEGIN', 'SELECT set_config(\$1, \$2, true)', 'SELECT * FROM payouts', 'COMMIT']);
console.log('Paved Road runtime assertions passed.');
"

# 2. 跑 Semgrep CI 閘門：確認精準攔下 webhook.ts 並回傳非零 Exit Code，同時對合規的 report.ts 保持 0 誤報
semgrep --config .semgrep/paved-road.yaml --error src/services/
```

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別看下方解答，試著站在企業資安架構師的角度，回答下面 4 個常見的實戰挑戰：

1. **戳破粗糙的 URL 字串防禦**：某位資深後端工程師跟你爭論：「我們根本不需要用你們寫的那個什麼自訂 `lookup` 的 `SafeHttpClient`！我在呼叫 `fetch(inputUrl)` 之前，已經先用 `const u = new URL(inputUrl)` 檢查過 `u.hostname !== 'localhost'`，而且確認 `u.hostname` 開頭不是 `127.`、`10.` 或 `192.168.` 了，這樣怎麼可能還會有 SSRF？」請當場舉出三種能直接繞過他這段檢查、打進內網或雲端 Metadata 的手法。
2. **整頓被開發者嫌棄的高誤報 SAST 管線**：你剛接手一家 `80` 人工程團隊的 AppSec 負責人，發現現在 GitHub Actions 的 PR 檢查裡掛了一套開箱即用的 SAST 規則，誤報率高達 `25%`，每天在 `120` 件警報裡就有 `30` 件假警報，工程師每天花大把時間在群組抱怨、甚至到處亂貼 `// nosemgrep`。請說出你會怎麼分步驟改造這套管線，把 PR 阻斷層的誤報率壓到 `< 5%`、省回工程工時，同時又不漏掉真正的高風險漏洞？
3. **結合可達性分析與威脅情報的 SLA 裁決**：今天早上公司的 SCA 套件掃描器同時報出兩張警報單：
   - **警報 1**：`CVSS v4.0 = 9.3`，`EPSS = 0.45`，出在一個只用來在本地產生 API 靜態文件的 `devDependencies` 套件裡，正式環境的 Docker Image 完全沒有打包這個套件，而且 CI 建置文件時也只讀倉庫內部的固定程式碼註解。
   - **警報 2**：`CVSS v4.0 = 7.6`，`EPSS = 0.19`（外加網路上剛出現公開 PoC），出在線上公開收單服務用來解析商戶外部傳入 XML 報表的函式庫裡，靜態呼叫圖確認外部請求一進來就會直接走到該 CVE 出事的解析函式。
   請照本章與第 33 章的治理規則，決定這兩張單各自的處置流程與修復 SLA。
4. **為什麼 Default-Deny 勝過人工 Code Review**：在 NexusPay 新增一支「匯出商戶年度稅務報表」的 API 時，為什麼「全域預設拒絕攔截器 + 啟動期路由表斷言」比「規定每個 PR 都要由資深工程師在 Code Review 時檢查有沒有貼 `@AuthGuard`」可靠得多？

---

### 參考解答

1. **戳破粗糙的 URL 字串防禦（三種繞過手法）**：
   - **第一招：自訂網域指向內網或 DNS Rebinding**。只看 `u.hostname` 字串，根本不知道那個網域背後解析到哪個 IP。攻擊者只要買一個網域 `evil.example`，把它的 DNS A 紀錄直接設成 `127.0.0.1` 或 `10.24.8.15`，`u.hostname` 是 `'evil.example'`，一秒穿過他的字串檢查；就算他多做了一次事前 DNS 預檢，只要沒用自訂 `lookup` 鎖死連線 IP，攻擊者照樣能靠短 TTL 的 DNS Rebinding 在 `fetch()` 實際連線時切回內網 IP。
   - **第二招：漏掉的雲端 Metadata 網段與 IPv6 映射位址**。他的黑名單只擋了 `127.`、`10.` 跟 `192.168.`，那攻擊者直接打雲端中繼資料位址 `http://169.254.169.254/latest/meta-data/`、打 Docker 常見的 `172.16.0.0/12` 網段，或是用 IPv6 本機回環 `http://[::1]/` 與 IPv4-mapped IPv6 `http://[::ffff:127.0.0.1]/`（經 `new URL()` 解析後 `hostname` 是 `[::ffff:7f00:1]`），他的三個字串前綴檢查全部當場放行。
   - **第三招：HTTP 302 轉址跳板**。攻擊者先傳一個完全合法的公網網址 `https://attacker.example/start`，順利通過第一關 `new URL()` 檢查；等 `fetch()` 連上去之後，攻擊者的伺服器回傳 `302 Found` 並把 `Location` 指到 `http://169.254.169.254/`。因為原生 `fetch()` 預設會自動跟隨轉址，第二跳就直接打進內網了。
2. **整頓高誤報 SAST 管線的四步改造法**：
   - **第一步：立刻把誤報率 `25%` 的通用猜測型規則移出 PR 同步阻斷層**，先止住每天 `30` 件假警報消耗團隊 `7.5` 個工程師小時的失血，重新贏回開發者的信任（移到夜間非同步掃描時，也要順手關掉低價值的高噪音規則並加上確定性過濾，免得只是把同樣 `7.5` 小時的爛帳原封不動塞給 AppSec 團隊自己吞）。
   - **第二步：針對最痛的高危漏洞類別鋪好 Paved Road 共用元件**（如防 SSRF 的 `SafeHttpClient`、防 BOLA/SQLi 的 `TenantDbClient` 與預設拒絕的 `@Policy`）。
   - **第三步：在 PR 阻斷層改放高精準的客製化 AST 規則**（只抓誰敢在業務目錄裡繞過 Paved Road 去叫原生 `fetch` 或 `pool.query`），把 PR 階段的誤報率壓到 `< 3%–5%`，而且讓每次阻斷都附帶一行就能修好的明確指引。
   - **第四步：把 `nosemgrep` 與逃生門寫進 `CODEOWNERS`**，規定任何豁免註解都必須經過 AppSec 簽核並附上工單編號，防止大家私下繞過閘門。
3. **結合可達性分析與威脅情報的 SLA 裁決**：
   - **警報 1**：因為 `CVSS v4.0 = 9.3` 且 `EPSS = 0.45 ≥ 0.1`，第一時間會觸發全書基準的**立即處置（立即分診）**；但分診人員馬上透過可達性分析確認它只存在於本地 `devDependencies`、根本沒進正式環境容器，而且 CI 建置過程也不碰任何外部不可信輸入。因此只要把這份「無實質曝險（不可達）」的證據存檔留底，就可以走可達性例外程序轉入每月例行的套件更新排程，完全不必半夜叫人起來停機搶修。
   - **警報 2**：雖然基礎分 `7.6` 落在高危（High）區間，但因為它的 **`EPSS = 0.19 ≥ 0.1`**，同樣觸發**立即處置**，而且靜態呼叫圖已經確認它在正式環境的公開端點上**直接可達（Reachable）**！團隊必須立刻啟動止血並按高危漏洞標準在 **`7 天` 強制修復 SLA** 內完成升級或根治（如果分診時發現打穿這個 XML 解析器能直接改動帳本、突破租戶隔離或拿走主機憑證而升級為嚴重等級，那就必須直接套用 **`24 小時` 嚴重修復 SLA**）。
4. **為什麼 Default-Deny 勝過人工 Code Review**：
   - **人工審查靠的是人的注意力，一定會有疲勞漏看的時候**。當一個 PR 改了 40 個檔案、又有上線時間壓力時，Reviewer 很容易沒注意到某個新 Controller 方法上面少貼了一行 `@AuthGuard`。
   - **全域預設拒絕搭配啟動期路由斷言，則是百分之百確定性的機器不變量**。只要忘記宣告 `@Policy` 或 `@PublicEndpoint`，伺服器連啟動測試都跑不過、CI 直接亮紅燈，把「記不記得掛權限」從人腦記憶力問題變成了編譯與測試期的硬約束。

---

## 延伸閱讀

- **CISA — Secure by Design & Secure by Default**（https://www.cisa.gov/securebydesign）：深入探討為什麼軟體工程團隊應該把安全防護直接內建在預設框架與架構裡，而不是把防禦責任丟給個別開發者或終端用戶的記憶力。
- **Netflix / Google Paved Road Engineering 實踐**：可以搜尋 Netflix Security 團隊公開分享的《The Paved Road》演講與文章，看看超大型微服務團隊怎麼用「最好用的官方共用元件」取代「禁止清單」來規模化消滅漏洞。
- **OWASP Threat Modeling Manifesto & OWASP SAMM**（https://www.threatmodelingmanifesto.org/ / https://owaspsamm.org/）：威脅建模四問法的原始宣言，以及評估企業軟體安全成熟度的實務指標。
- **Semgrep Docs — Writing Custom Rules & Guardrails**（https://semgrep.dev/docs/writing-rules/overview）：手把手教你怎麼針對自家公司的安全封裝函式寫出低誤報的 AST 檢查規則，並接進 CI/CD 當作護欄。
- **CISA VEX (Vulnerability Exploitability eXchange) & SBOM 指引**（https://www.cisa.gov/sbom）：了解現代供應鏈安全怎麼用標準化的 VEX 文件，記錄並傳遞「某個相依套件 CVE 在我們系統裡到底可不可達、有沒有實質可利用性」。
