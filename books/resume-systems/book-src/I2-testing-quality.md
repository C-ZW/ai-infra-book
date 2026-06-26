# I · 測試與品質

本領域處理「如何在上線前與上線後**取得對系統行為的信心**」這個老問題：什麼樣的測試給什麼樣的保證，又付出什麼代價。本檔含三條：負載測試（量化系統在壓力下的延遲與吞吐真相）、測試策略（unit / integration / contract / e2e 的金字塔與 contract testing）、可觀測性與品質工具地圖（各類別工具選什麼、為什麼）。線上指標（metric / log / trace、SLI/SLO、cardinality、告警、分散式追蹤）屬可觀測性本身，在領域 I 的另一檔；本檔聚焦「測試取得信心」與「工具選型」這兩面。

## 負載測試

### 定義與原理

負載測試問的是：**系統在「真實流量形狀」下，延遲分佈與吞吐天花板是什麼**。它不是「跑很多次取平均」，而是要逼出 p99 / p999 這條長尾——因為使用者體驗由長尾決定，不由平均決定（成因見 tail latency 與長尾，領域 S）。

關鍵的第一原理是**流量模型**：你怎麼產生負載，決定你量到什麼。兩個對立模型——

- **封閉模型（closed model / closed loop）**：固定數量的虛擬使用者（VU），每個 VU 送一個請求、**等回應、再送下一個**。系統一慢，VU 自然降速、送得更少。它模擬「請求數受限於在線使用者數」的場景（如固定連線數的內部服務）。
- **開放模型（open model / arrival rate）**：以**固定到達率**（如每秒 1000 個請求）灌入，**不管前一個有沒有回來**。它模擬「使用者不會因為你變慢就減少點擊」的真實外部流量（公開 API、網站）。

兩者量到的延遲可以差一個數量級，根因是**coordinated omission（協同遺漏）**——這個詞由 Gil Tene 約 2013 年提出。封閉模型在系統卡住時，VU 也跟著停下不發新請求，於是那段「本來應該被很多人撞上的高延遲」只被少數請求記到，**長尾被系統性地低估**。

### 解法空間

要量到誠實的延遲分佈，處理 coordinated omission 有幾條路：

- **改用開放模型**：以 arrival rate 驅動，到時間就發、不等回應。系統卡住期間累積的請求一樣被記錄，長尾不被抹掉。
- **constant-rate 工具補償**：固定速率送請求（如 Vegeta 的 constant request rate；wrk2 也走這條），把「該發而沒發」的請求視為延遲一併計入。
- **回填式校正（latency correction）**：用 HdrHistogram 這類直方圖，在已知預期請求間隔時，把缺漏的延遲樣本以該間隔回填補上，事後修正封閉模型的低估。
- **混合 / ramping 場景**：先封閉模型暖機（避免冷啟動污染，見冷啟動與暖機，領域 S），再切開放模型壓長尾；或用階梯式提升負載找出吞吐崩潰點（ρ→1 的爆炸，見排隊直覺，領域 E）。
- **影子流量 / 重放**：把生產真實流量錄下重放到測試環境，流量形狀天然真實，但需處理冪等與副作用（見冪等，領域 A）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 封閉模型（固定 VU） | 模擬有界並發；不會把系統灌爆 | 內部服務、固定連線數、想量「N 個並發下多快」 | 有 coordinated omission，長尾被低估；VU 數不等於 RPS |
| 開放模型（arrival rate） | 長尾誠實；模擬外部不退讓流量 | 公開 API / 網站、要量 p99/p999 真相 | 系統一崩請求會無限堆積、測試端先 OOM，需設上限與背壓 |
| constant-rate（Vegeta/wrk2） | 固定速率、補償遺漏 | 要可重現的速率基準、CI 回歸 | 速率設太高會打爆測試端網路；rate=0 表示盡全力發 |
| HdrHistogram 校正 | 事後補長尾、保留高動態範圍 | 已有封閉模型數據要修正 | 需正確的「預期間隔」才補得準；補錯反而失真 |
| 流量重放 / 影子 | 流量形狀最真實 | 上線前驗證、容量規劃 | 副作用與冪等是大坑；需資料隔離 |

### 何時需要

需要嚴肅負載測試的訊號：**對外承諾了 SLO**（p99 < Xms，見 SLI/SLO，領域 I）、要做**容量規劃**（買多少機器、何時分片）、上線前驗證**新架構**能不能扛預期尖峰、或要找出**吞吐崩潰點**（ρ 逼近 1 的位置）。

不需要過度投入的場景：低流量內部工具、流量遠低於單機天花板（先用量級估算判斷，見量級估算與容量直覺，領域 U）、或還在快速迭代、架構未定——這時花大力氣建負載測試框架是 over-engineering，跑一次粗略開放模型壓測拿個數量級就夠。

worked example：一個 API 平均回應 50ms，你用封閉模型 100 個 VU 測。若系統每分鐘卡頓一次 5 秒，封閉模型那 5 秒只記到約 100 個請求超時（VU 停發），p99 看起來漂亮。但若真實到達率是 2000 RPS，那 5 秒本該湧入約 2000 × 5 = **10,000 個請求**全部撞上高延遲——開放模型會把這 1 萬個慢請求記進分佈，p99 從「看起來 60ms」變成「真相 3000ms+」。差距不是測量誤差，是模型選錯。

### 常見誤解與陷阱

- **「平均延遲很好」≠ 系統健康**：平均把長尾稀釋掉；使用者撞上的是 p99/p999。只看平均等於沒測。
- **把 VU 數當 RPS**：100 個 VU 不等於 100 RPS——RPS = VU / 每請求耗時。系統變慢時封閉模型的實際 RPS 會自己掉下來——名義上設定 2000 RPS、實際可能只發出 800，量到的是兩者不一致的假象。
- **測試端自己是瓶頸**：負載產生器的 CPU / 網路 / GC（或 event loop 卡頓，見 event loop，領域 D）會污染數據；先確認瓶頸在被測系統不在產生器。
- **忽略暖機**：第一波請求撞上冷快取、冷連線池、JIT 未熱（見冷啟動與暖機，領域 S），把暖機數據混進穩態結果會高估延遲。
- **在共用環境測**：鄰居噪音（noisy neighbor）讓結果不可重現；負載測試要隔離環境或標注是「帶噪音的生產近似」。

### 延伸閱讀

- Gil Tene, "How NOT to Measure Latency"（演講，coordinated omission 的原始論述）：https://www.infoq.com/presentations/latency-response-time/
- HdrHistogram（高動態範圍直方圖，含 coordinated omission 校正）：https://github.com/HdrHistogram/HdrHistogram
- wrk2（constant throughput、correct latency 的 wrk 變體）：https://github.com/giltene/wrk2

## 測試策略

### 定義與原理

測試策略要回答的不是「要不要測」，而是**把有限的測試預算分配到哪一層，才能用最低成本買到最高信心**。每一層測試在「真實度 vs 速度/穩定」的軸上佔不同位置：

- **unit（單元）**：測單一函式 / 類別的邏輯，依賴全部用 mock / stub 替掉。**快、穩、定位精準**，但完全不保證「各部件兜起來能跑」。
- **integration（整合）**：測幾個真實部件協作——程式碼配真實資料庫、真實快取、真實 queue（常用 testcontainers 起一個真 PostgreSQL）。保證**接線正確**（SQL 語法、序列化、交易語意），代價是慢、需環境。
- **contract（契約）**：測**服務 A 對服務 B 的 API 假設**是否與 B 的實際行為一致——不需把 A、B 同時跑起來。它填補 unit（各自 mock、可能 mock 錯）與 e2e（全跑、太貴）之間的縫。
- **e2e（端到端）**：把整條真實系統串起來跑使用者旅程。**真實度最高、信心最強**，但**最慢、最脆（flaky）、定位最差**（紅了不知道哪一環壞）。

經典的**測試金字塔**主張：底層 unit 多、中層 integration 適量、頂層 e2e 少。倒過來（e2e 一堆、unit 沒幾個）叫「冰淇淋甜筒反模式」，會慢到沒人想跑、脆到沒人信。

### 解法空間

- **測試金字塔**：大量 unit + 中量 integration + 少量關鍵路徑 e2e。預設策略。
- **測試獎盃（testing trophy）**：把重心壓在 **integration** 那層（Kent C. Dodds 提倡）——因為純 unit 對重 mock 的程式碼信心低，integration 的「信心/成本比」更好。適合 I/O 密集、邏輯薄的服務。
- **contract testing**：在服務邊界放契約。**consumer-driven contract（CDC）**——消費端先寫下「我會這樣呼叫你、期待這樣的回應」，產生契約（pact 檔），供應端在自己的 CI 對著契約驗證自己沒破壞它。Pact 是這條路的事實標準（2026-06）。另一變體是 **schema/spec 契約**（用 OpenAPI/Protobuf 當合約，見序列化與 schema 演進，領域 A）。
- **snapshot / approval testing**：把輸出整塊存成快照、之後比對差異。對複雜輸出（如序列化結果、render 結果）省事，但容易養出「亂更新快照」的壞習慣。
- **property-based testing**：不寫死案例，宣告「對所有合法輸入應成立的性質」，由框架自動生成大量輸入找反例。對純函式、解析器、編解碼特別有效。
- **mutation testing**：故意改壞程式碼（注入 mutant），看測試有沒有抓到——量測「測試本身的有效性」而非覆蓋率。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| unit | 單元邏輯正確；快、定位準 | 純邏輯、演算法、邊界條件 | mock 可能與真實行為不符，買到「假信心」 |
| integration | 接線正確（DB/queue/序列化） | I/O 密集、薄邏輯服務 | 慢、需環境；testcontainers 起容器有開銷 |
| contract（CDC/Pact） | 服務間 API 假設一致 | 微服務多、跨團隊邊界 | 需雙方都接入並維護 pact broker；契約漂移要治理 |
| e2e | 整條路徑可跑、信心最高 | 關鍵使用者旅程（登入→下單） | 最慢最脆；只挑少數黃金路徑，別當主力 |
| property-based | 覆蓋大量自動生成輸入 | 解析器、編解碼、純函式 | 寫「性質」比寫案例難；失敗的最小反例需 shrink |
| mutation | 量測測試本身有效性 | 想知道覆蓋率有沒有騙人 | 極慢；當定期體檢、不進每次 CI |

### 何時需要

contract testing 的決策點很清楚：**當「把所有服務一起跑 e2e」的成本/脆度高到不可接受、而 mock 又怕 mock 錯**時，contract 是甜蜜點——它讓消費端與供應端**各自獨立 CI**，卻仍能在供應端改 API 時把消費端的真實假設打紅。單體應用、或服務邊界少且穩定，不值得引入契約框架與 broker 的維運成本。

金字塔的形狀該因系統而異：重邏輯的計算核心，unit 為主；薄邏輯重 I/O 的 CRUD 服務，重心上移到 integration（測試獎盃）。**別教條地追覆蓋率數字**——80% 覆蓋率可能全是沒斷言的 happy path，不如 50% 覆蓋率但每條都驗了失敗分支。

worked example：三個微服務 A→B→C，每個各 5 個版本要兼容。純 e2e 要驗的組合是 5×5×5 = **125 種**，且每次跑要把三個都拉起來、平均 8 分鐘、flaky 率 5%（一條 25 步的旅程，每步 99.8% 穩，整體 0.998²⁵ ≈ 95% 才會綠）。改成 contract：A↔B、B↔C 兩個邊界各自驗，A 的 CI 只跑自己 + 對 pact 驗證、約 40 秒，B 改 API 時若破壞 A 的契約，B 的 CI 直接紅——把 125 種組合的組合爆炸，拆成兩個線性可驗的邊界。

### 常見誤解與陷阱

- **覆蓋率 = 信心**：行覆蓋率只說「這行被執行過」，不說「有斷言驗證它」。100% 覆蓋率配空斷言是純擺設。
- **e2e 堆太多**：冰淇淋甜筒反模式——慢、脆、紅了沒人查得動，最後團隊習慣性 retry 到綠，等於沒測。
- **mock 漂移**：unit 裡 mock 的回應與供應端真實回應悄悄分歧，unit 全綠但上線就爆——這正是 contract testing 要堵的洞。
- **flaky 測試當背景噪音**：放任偶發紅就 retry，會慢慢侵蝕對整套測試的信任，最後真 bug 也被當 flaky 略過。flaky 要當 bug 修，不是當天氣忍。
- **把 contract 當完整 e2e**：契約只驗「雙方對 API 形狀/語意的假設一致」，不驗端到端業務正確；兩者互補，不互相取代。
- **AI 生成測試的假信心**：AI 能快速補大量測試提高覆蓋率數字，但容易生出「測 getter/setter、斷言寫成永真」的湊數測試——覆蓋率漲、實際信心沒漲，review 要盯斷言而非行數。

### 延伸閱讀

- Martin Fowler, "Test Pyramid"：https://martinfowler.com/articles/practical-test-pyramid.html
- Martin Fowler, "Contract Test" / "Consumer-Driven Contracts"：https://martinfowler.com/bliki/ContractTest.html
- Pact 官方文件（consumer-driven contract testing）：https://docs.pact.io/
- Kent C. Dodds, "The Testing Trophy and Testing Classifications"：https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications

## 可觀測性與品質工具地圖

### 定義與原理

這條不講某個概念的機制，而是給一張**選型地圖**：在「日誌採集、執行期診斷、負載測試、相依掃描」這幾個品質/可觀測性類別裡，**該選哪類工具、為什麼、現況如何、有什麼替代**。第一原理是——**工具是用來換取某種保證的，而工具會老化**（停止維護、改授權、被後繼者取代），所以選型時除了「能做什麼」，更要看「**還活著嗎、授權能用嗎、有沒有更好的接班**」。

四個類別各自要的保證不同：日誌採集要**不漏不重、低資源佔用**；執行期診斷要**貼合 runtime、結果準確**；負載測試要**長尾誠實**（見負載測試）；相依掃描要**漏洞庫新、誤報低、能進 CI gate**。

### 解法空間

按類別列各自的代表工具與機制：

- **日誌採集 / 轉發**：
  - **Fluent Bit**——C 寫的輕量代理，pipeline 是 input → parser → filter → output，記憶體足跡小，適合當每節點 / sidecar 的 log forwarder。2026-06 已到 **v5.0** 系列（CNCF graduated）。
  - **Fluentd**——Ruby 核心 + 龐大 gem plugin 生態，外掛最齊、較重，適合中央聚合層。同為 CNCF graduated。
  - 常見組合：節點端用 Fluent Bit 收集轉發、中央用 Fluentd 做複雜路由（兩者同源、可混用）。
- **Node 執行期診斷**：
  - **Clinic.js**——NearForm 的 Node 效能診斷套件（Doctor / Flame / Bubbleprof / Heap Profiler 四工具）。⚠️ **2026-06 官方 README 明言「不再積極維護、因深綁 Node 內部、可能失效或結果不準」**，最後正式 release 為 v13.0.0（2023-06）。
  - 替代：Node 內建 `--prof`、`--cpu-prof`、`node --inspect` 配 Chrome DevTools、`0x`（flamegraph）、`autocannon`（本機快速壓測）、以及 OpenTelemetry / APM 的 profiling 能力。
- **負載測試**：
  - **Grafana k6**——Go 引擎、測試腳本以 JavaScript（也支援 TypeScript）撰寫，open source、授權 **AGPLv3**（Grafana 系自 2021 由 Apache 2.0 改 AGPLv3）。積極維護，最新主版 **k6 2.0（GrafanaCON 2026 發表）**。支援開放/封閉模型（scenarios / executors）。
  - **Vegeta**——tsenart 的 Go HTTP 壓測工具，採 **constant request rate**（固定速率）模型、天然對抗 coordinated omission（見負載測試）；可當 CLI 或 Go library，最新約 **v12.13.0**（2026-06）。
  - 機制差異：k6 是「寫腳本表達情境」的全功能框架；Vegeta 是「一行打固定速率」的尖刀，CI 回歸基準很順手。
- **相依 / 漏洞掃描**：
  - **Snyk**——developer-security 平台，核心是 **SCA（software composition analysis，開源相依漏洞掃描＝Snyk Open Source）**，另涵蓋 SAST（Snyk Code）、Container、IaC。深整合 IDE / Git / CI/CD，能開自動修復 PR。2026-06 為商業 freemium。
  - 替代：`npm audit`（內建、免費但庫較淺）、OWASP Dependency-Check、Trivy（容器+相依，開源）、GitHub Dependabot（相依更新 + 告警）。

### 各方案的保證與取捨

| 工具 | 類別/保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Fluent Bit（v5，2026-06） | 日誌轉發；輕量、低足跡 | 每節點/sidecar log forwarder | v4.2 維護至 2026-06-30，宜上 v5；外掛數少於 Fluentd |
| Fluentd | 日誌聚合；外掛生態最齊 | 中央路由/聚合層 | Ruby、較重；高吞吐節點端不如 Fluent Bit |
| Clinic.js | Node 診斷；四合一視覺化 | 既有專案的歷史分析 | ⚠️ 已停止積極維護、可能與新版 Node 不相容，勿當現役推薦（2026-06） |
| Grafana k6（2.0） | 負載測試；情境腳本、雙模型 | 要寫複雜情境/CI 壓測回歸 | 授權 AGPLv3（非 MIT/Apache），自架服務化需留意條款 |
| Vegeta（v12.13.0） | 負載測試；固定速率、抗遺漏 | 簡單高頻速率基準、CLI/library | 不適合複雜多步情境；速率設過高會打爆測試端 |
| Snyk | 相依掃描（SCA）；自動修復 PR | 跨語言 SCA + SAST + IaC 一站 | 商業 freemium，Free 層有測試次數上限、Team 約 $25/dev/月（2026-06，以官網為準） |

### 何時需要

- **日誌採集**：一旦有多節點 / 容器化、需把分散日誌集中化就需要；單機單體直接寫檔/stdout 即可（logs as streams，見 12-factor app，領域 Q）。選 Fluent Bit 還是 Fluentd 看「節點端輕量 vs 中央外掛齊」。
- **Node 診斷**：定位 event loop 卡頓、記憶體洩漏、CPU 熱點時需要——但 Clinic.js 既已 dormant，新專案優先用內建 profiler / OpenTelemetry，把 Clinic.js 當「能用就用、不可依賴」。
- **負載測試**：見負載測試的「何時需要」；簡單速率基準選 Vegeta、複雜情境選 k6。
- **相依掃描**：任何有開源相依、且相依會隨時間冒漏洞的專案都需要某種 SCA 進 CI（這是供應鏈風險的第一道防線，見自建 vs 採用 + 相依管理，領域 U）。要不要上 Snyk（付費、功能全）vs `npm audit`/Trivy（免費、較淺），看團隊預算與合規需求。

worked example：一個 Node 服務有 800 個傳遞相依（transitive dependencies），手動追 CVE 不可能。接上 SCA 掃描後，假設漏洞密度約每 200 個套件 1 個可修高危漏洞，一次掃描約報出 **4 個高危**並各開一個升版 PR；接進 CI gate 後，新引入帶已知高危漏洞的相依會在 PR 階段就被擋下，把「上線後才發現用到有漏洞的套件」變成「合併前就攔截」。代價是誤報需人工 triage、以及付費層的 per-developer 成本。

### 常見誤解與陷阱

- **把停更工具當現役**：Clinic.js 是典型——文件還在、看起來能跑，但官方已明說不維護、深綁 Node 內部可能在新版失準（2026-06）。選工具要查「最後 release 日期 + 維護聲明」，不能只看「搜得到、星很多」。
- **授權沒看清**：k6 是 **AGPLv3** 不是寬鬆授權——若你把它包進對外提供的服務、或內嵌進產品，AGPL 的網路條款可能觸發義務。選 OSS 工具先讀 LICENSE，不是讀 README。
- **SCA 報告 = 安全**：相依掃描只覆蓋**已知**漏洞（CVE 已揭露的），零日與自家程式碼的邏輯漏洞它看不到；且高誤報率若不 triage 會養出「狼來了」、整批被忽略。
- **負載測試工具選錯模型**：用封閉模型的工具量對外 API 的長尾會被 coordinated omission 騙（見負載測試）——這是工具選型直接影響數據真相的例子。
- **日誌採集器自己變瓶頸**：log forwarder 設定不當（無背壓、buffer 無界）會在日誌暴量時吃光記憶體或拖垮節點；轉發層也要有背壓與丟棄策略（見背壓，領域 E）。
- **版本號當永恆**：本條所有版本/授權/定價都標了（2026-06）——它們是會腐的事實，引用時務必回官方來源複查，別把今天的版本號寫成定律。

### 延伸閱讀

- Fluent Bit 官方文件：https://docs.fluentbit.io/manual
- Fluent Bit vs Fluentd（官方對比）：https://docs.fluentbit.io/manual/about/fluentd-and-fluent-bit
- Clinic.js（GitHub，含維護狀態聲明）：https://github.com/clinicjs/node-clinic
- Grafana k6 官方文件：https://grafana.com/docs/k6/latest/
- Vegeta（GitHub）：https://github.com/tsenart/vegeta
- Snyk 官方網站（產品與定價）：https://snyk.io/
