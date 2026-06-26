# J · 雲端與編排原語

雲端的運算原語（serverless function、排程器、編排器）把「何時跑、跑幾次、跑在哪台機器」這些調度決策從你手裡接走，換來彈性與免運維——但同時也把一組分散式系統的硬保證問題搬到你面前：執行環境隨時可丟、排程不是 exactly-once、節點的死活只能用逾時去猜。本檔涵蓋五條：Lambda（serverless function 的執行模型與特有調校）、無狀態 vs 有狀態（為什麼這層運算必須把狀態外置）、K8s CronJob（排程觸發的交付語意）、時間與排程（排程觸發的時間語意：用哪種鐘量逾時、漏跑怎麼補）、失敗偵測（在這層只能用逾時判生死）。邊界：冷啟動的通用機制在領域 S，本檔只點 Lambda 特有的 SnapStart；時間/時鐘的完整機制（邏輯時鐘、UTC/DST 應用層坑）在領域 M，本檔只講排程觸發語意；health check 的探針機制在領域 P，本檔只講「逾時是唯一手段」這個分散式視角。

## Lambda

### 是什麼與內部機制

AWS Lambda 是事件驅動的 serverless 運算：你交一段函式碼與一個 handler，平台在事件到來時啟動一個 **execution environment**（一個受隔離的 microVM）來跑它，跑完保留一段時間以便重用，閒置夠久就回收。一個 execution environment 在任一瞬間只服務**一個** invocation——這是理解 Lambda 併發模型的關鍵：要同時處理 N 個請求，平台就得有 N 個 environment 同時存在。

一次冷啟動（cold start）= 找/造一個新 microVM → 下載你的程式碼 → 啟動 runtime → 跑你的 init 程式碼（handler 外的頂層程式）→ 才進 handler。重用既有 environment 時這些全跳過，是為 warm start。冷啟動的通用成因與暖機策略屬通用機制（見冷啟動與暖機，領域 S）；這裡只談 Lambda 特有的減速手段。

**SnapStart** 是 Lambda 特有機制：它在你發布版本時先把 init 跑完，對初始化完成的 microVM 記憶體拍一個加密快照（Firecracker microVM snapshot），之後的冷啟動直接從快照還原，跳過「啟動 runtime + 跑 init」這段，官方稱可去除約 70–90% 的 init latency。代價是 snapshot 是在發布時拍的、之後每個 invocation 共用同一份還原起點，所以 init 期間建立的東西（產生的亂數種子、開好的 DB 連線、快取的時間戳）在還原後可能「不新鮮」——須用 runtime hook（`beforeCheckpoint` / `afterRestore`）在還原後重建。

### 在哪些系統扮演什麼角色

- **事件處理 worker**：S3 物件到達、SQS/SNS 訊息、DynamoDB Streams、EventBridge 事件觸發一段處理邏輯。Lambda 在這裡是「免管理機器的 consumer」。
- **API 後端**：API Gateway 或 ALB 把 HTTP 請求轉成同步 invoke，Lambda 當無狀態 request handler（見 API gateway 的角色，領域 H）。
- **排程任務**：EventBridge Scheduler 定時觸發，當 cron 用（與 K8s CronJob 同類角色，語意差異見 K8s CronJob 與時間與排程）。
- **膠水 / 編排步驟**：Step Functions 的一個 task state 呼叫 Lambda 當單一步驟（持久化工作流見領域 K）。

### 保證與限制

帶數字的硬限制（2026-06，以官方 quotas 為準）：

| 維度 | 值 | 注意事項 |
|---|---|---|
| Timeout | 預設 3s、最大 **900s（15 分鐘）** | 超過即被砍，長流程須拆步或改用 durable workflow |
| Memory | 128 MB–10,240 MB | CPU 隨 memory 線性配比，調記憶體＝同時調 CPU |
| 帳號預設併發 | **1,000（per region，可申請調高）** | 是「同時存在的 environment 數」上限，非 RPS |
| Sync payload | **6 MB**（request＋response 各自上限） | 超過要把大 payload 放 S3 傳引用（見 S3 / 物件儲存，領域 G） |
| Async payload | **1 MB**（2025-10-24 起，原為 256 KB） | 這是 2025 才放大的數字，舊資料常仍寫 256 KB |
| /tmp 暫存 | 預設 512 MB、可調至 10,240 MB | ephemeral，跨 invocation 不保證保留 |

**Worked example（併發推算）**：每個請求平均跑 200 ms、要支撐穩定 2,000 req/s。同時在跑的 environment 數約 = 到達率 × 平均處理時間 = 2,000 × 0.2 = **400 個併發**——在預設 1,000 上限內。但若處理時間因下游變慢漲到 800 ms，需求變 2,000 × 0.8 = **1,600 個**，直接撞上預設 1,000 上限，後續請求收到 throttle（429）。這就是 Lambda 併發的陷阱：併發需求 = 流量 × 延遲，下游一慢、所需併發成倍漲，限流不是被流量打爆而是被延遲打爆。

SnapStart 支援的 runtime（2026-06，已查證）：

| Runtime | SnapStart | 備註 |
|---|---|---|
| Java | 支援（11 / 17 / 21） | Java 託管 runtime 無額外費用 |
| Python | 支援（3.12+） | 2024-11 GA |
| .NET | 支援（8+） | 2024-11 GA |
| Node.js | **不支援**（2026-06） | nodejs 各版皆不支援；container image、OS-only runtime 亦不支援 |
| Ruby | 不支援 | 同上 |

SnapStart 另不支援 provisioned concurrency、EFS、>512 MB 的 ephemeral storage。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| AWS Lambda | 免運維、毫秒計費、自動擴縮到 0 | 突發/稀疏流量、事件處理、膠水 | 冷啟動延遲、15 分鐘上限、本地無持久狀態 |
| 容器（ECS/EKS 常駐） | 長連線、無冷啟動、可有狀態 sidecar | 穩定高流量、長流程、需 WebSocket | 要自管擴縮與機器，閒置仍計費 |
| Cloud Run / Knative | 介於兩者：容器化 + 縮到 0 | 想要容器彈性又要自動縮放 | 仍有冷啟動，並發模型與 Lambda 不同 |
| Provisioned concurrency | 預先初始化環境、近零冷啟動 | 延遲敏感、可預測尖峰 | 預留即計費，與 SnapStart 互斥 |

判準：**流量稀疏或尖峰陡 → Lambda**（縮到 0 省錢）；**流量穩定且高 → 常駐容器**（攤平後容器更便宜、無冷啟動）。延遲敏感的尖峰用 provisioned concurrency 或（Java/Python/.NET）SnapStart 補冷啟動。

### 常見誤解與陷阱

- **「Lambda 是無狀態的所以我不用管狀態」**：函式碼語意上無狀態，但 execution environment 會被**重用**——頂層（init 外）的全域變數、`/tmp` 內容會跨 invocation 殘留。把使用者資料快取在全域變數，下一個請求（不同使用者）可能讀到上一個的——這是真實的資料外洩路徑。全域只放無狀態的東西（DB client、設定）。
- **「SnapStart 全 runtime 都能用」**：Node.js / Ruby 不支援（2026-06）。Node 冷啟動本就相對低，這是官方不優先支援的理由，但若你押注 SnapStart 來救 Node 冷啟動會落空。
- **「async payload 還是 256 KB」**：2025-10-24 起已是 1 MB。仍照 256 KB 設計的截斷邏輯會在 256 KB–1 MB 區間放行原本預期會被擋的訊息。
- **冷啟動連線風暴**：每個新 environment 各自開 DB 連線，併發 400 就是 400 條連線，瞬間擴張可打爆 DB 連線上限——serverless 連 DB 應走外部連線池（見連線池，領域 N）。
- **併發上限是 environment 數不是 RPS**：1,000 併發在 200 ms 處理下約等於 5,000 req/s，但在 2s 處理下只剩 500 req/s。換算永遠要乘上延遲。

### 延伸閱讀

- [Improving startup performance with Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)（官方，含支援 runtime 與限制）
- [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)（官方，timeout/memory/payload/併發上限）
- [AWS Lambda payload size 256 KB → 1 MB for async invocations](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-lambda-payload-size-256-kb-1-mb-invocations/)（2025-10 公告）
- [SnapStart for Python and .NET is now GA](https://aws.amazon.com/blogs/aws/aws-lambda-snapstart-for-python-and-net-functions-is-now-generally-available/)

## 無狀態 vs 有狀態

### 定義與原理

一個運算單元是**無狀態**的，意思是：它在兩次請求之間不持有任何「下一次請求正確處理所必需」的記憶體狀態。任意一個實例都能處理任意一個請求，把實例殺掉再換一個，行為不變。**有狀態**則相反：實例的記憶體裡握著外面取不到的東西（連線進度、累計計數、會話資料、本地排序緩衝），殺掉這個實例就丟了。

第一原理是一句殘酷的事實：**process 的記憶體是 process 的私產，process 一死即蒸發。** serverless / 自動擴縮的世界裡，execution environment 與 container 是「牲口不是寵物」——隨時可能被回收、搬遷、因擴縮而增減。所以一條鐵律浮現：**持久化是一個主動動作，不是預設行為。** 你寫進記憶體的東西不會自己活下來；要它活過重啟，你得**主動**把它寫到一個重啟後仍在的地方（DB、Redis、物件儲存、訊息佇列）。沒主動寫出去的，重啟就是失憶，平台不會替你保管。

serverless 要求無狀態，正是因為平台保留「隨時換掉你的實例」的權利——它用這個權利換來彈性擴縮、滾動更新、故障自癒。你交出「狀態留在記憶體」的便利，換來「實例可被任意替換」的彈性，這是一筆明確的交易。

### 解法空間

把狀態外置（externalize）的辦法：

- **會話/使用者狀態 → 外部 store**：session 放 Redis 或 DB，不放 process 記憶體；請求自帶 token（JWT，見領域 F）讓任一實例都能驗。
- **進行中的工作狀態 → 持久佇列 / durable workflow**：長流程的中間狀態交給 Step Functions / Temporal（見持久化工作流與 durable execution，領域 K），實例死了流程能從上次的持久點續跑。
- **本地快取 → 接受它是易失的**：把記憶體快取定位成「可重建的加速層」，重啟就重建，不當權威來源（cache-aside，見快取策略，領域 G）。
- **連線/檔案 → 每次重建或走外部池**：DB 連線交給外部 pooler，臨時檔放 `/tmp` 但不假設它跨 invocation 存在。
- **累計型狀態（計數、聚合）→ 原子化到外部**：用 Redis `INCR` 或 DB 的原子更新，而非「讀進記憶體 +1 再寫回」（那是 race，見 race condition，領域 D）。
- **真的需要黏住 → sticky session（次選）**：WebSocket 等長連線靠 session affinity 把同一 client 綁到同一實例（見連線狀態與水平擴展，領域 C），但這是把無狀態的好處部分讓出去換來的，擴縮時仍會斷。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 狀態外置到 DB/Redis | 任一實例可服務任一請求，可隨意擴縮 | 絕大多數無狀態服務的預設 | 每請求多一次外部往返；外部 store 變成新的單點，要它自己的 HA |
| Durable workflow | 長流程中間狀態持久、可從斷點恢復 | 多步驟、跨服務、長時程的編排 | 引入額外平台與心智模型；非所有流程都值得 |
| 本地快取（易失） | 命中時快、重啟自動重建 | 讀多寫少、可容忍 miss 的加速 | 不可當權威來源；多實例間快取不一致 |
| Sticky session | 同 client 落同實例、保留連線態 | WebSocket、無法外置的長連線狀態 | 負載不均、擴縮/重啟時連線斷、實例死即丟該 client 狀態 |

判準：**能外置就外置**（換來自由擴縮）；只有外置成本過高（如即時媒體的記憶體緩衝）才退而用 sticky，並接受它的脆弱。

### 何時需要

- **必須無狀態**：任何要自動擴縮 / 滾動更新 / 跑在 serverless 的請求處理層——沒有選擇，平台會替你殺實例。
- **可以有狀態（且接受代價）**：單實例的批次工具、開發期原型、明確不需擴縮的內部工具。一旦要橫向擴展或上 serverless，有狀態就成了擴縮的天花板。
- **over-engineering 警訊**：把本來單機就夠、永遠不會擴縮的小工具硬塞進「全狀態外置」架構，徒增 Redis/DB 往返延遲與運維面。無狀態是擴縮的手段，不是無條件的美德。

### 常見誤解與陷阱

- **「我沒存全域變數所以是無狀態」**：連線池、模組級快取、`/tmp` 的累積檔案、甚至 logging buffer 都是狀態。無狀態的檢驗標準是「殺掉換一個，行為不變嗎」，不是「我有沒有寫 `global`」。
- **把記憶體當持久層**：「先寫進 map，背景再 flush 到 DB」——實例在 flush 前死掉，那段資料憑空消失且沒人知道。持久化必須在「回應成功」之前完成，或明確走 outbox（見 outbox / saga，領域 A）。
- **以為 serverless 自動幫你保存狀態**：平台只保證「會給你一個能跑的實例」，不保證「是同一個」「上次的記憶體還在」。
- **sticky session 當高可用用**：sticky 只決定「路由去哪」，不複製狀態。被綁的實例一死，那批 client 的記憶體狀態照樣全丟——sticky 不是備援。
- **跨 invocation 殘留誤當作快取**：Lambda environment 重用會讓全域變數殘留，初學者誤以為這是「平台幫我快取」，實則不可靠（環境隨時被回收）且有把上一請求資料洩漏給下一請求的風險。

### 延伸閱讀

- [The Twelve-Factor App — VI. Processes（Execute the app as stateless processes）](https://12factor.net/processes)
- [The Twelve-Factor App — IV. Backing services](https://12factor.net/backing-services)

## K8s CronJob

### 是什麼與內部機制

Kubernetes CronJob 是一個依 cron 時間表反覆建立 **Job** 的控制器資源（穩定 API：`batch/v1`，自 v1.21 GA）。它本身不跑你的程式——它的工作是「到點了就建一個 Job」，Job 再建 Pod、Pod 才跑你的容器。所以 CronJob 是「排程器」這一層，真正的執行語意（重試幾次、算不算成功）落在它生出的 Job 上。

CronJob controller 的運作迴圈大致是：週期性醒來 → 算「從上次排程到現在，照 `schedule` 應該觸發幾次」→ 對每個該觸發的時間點，依 `concurrencyPolicy` 決定建不建 Job。關鍵欄位：

- `schedule`：標準 cron 字串（如 `*/5 * * * *` 每 5 分鐘），可指定 `timeZone`。
- `concurrencyPolicy`：上一個 Job 還沒跑完、下一個排程到了時怎麼辦——`Allow`（預設，並行跑）、`Forbid`（跳過這次、不重疊）、`Replace`（殺掉舊的、跑新的）。
- `startingDeadlineSeconds`：排程時間到了但 controller 太晚才處理（如 controller 當機重啟），超過這個秒數就放棄這次觸發。
- `successfulJobsHistoryLimit` / `failedJobsHistoryLimit`：保留幾個歷史 Job 物件（預設 3 / 1）。

**Missed-schedule 行為（官方）**：controller 算「自上次排程以來錯過幾次」，若**超過 100 次**就停止排程並記 error（`too many missed start time (> 100)`）——典型成因是 controller / 叢集當機很久、或 `startingDeadlineSeconds` 沒設。若設了 `startingDeadlineSeconds`，則只在該秒數的窗口內數錯過次數，避開這個 100 次的死結。

### 在哪些系統扮演什麼角色

- **定期批次**：對帳、報表、清理過期資料、TTL 掃描。
- **週期維護**：cache 預熱、憑證輪替觸發、健康巡檢。
- **外部 cron 的叢集內替代**：取代散落在各機器 crontab 的腳本，集中受 K8s 調度與可觀測性管理。
- **觸發長流程的起點**：CronJob 只負責「按時點火」，點火後的長流程交給 durable workflow 或佇列（見領域 K / A）。

### 保證與限制

**最重要的限制：CronJob 不是 exactly-once。** 官方文件明說「在某些情況下，一個 job 可能被建立兩次，或一次都不建立」。原因是排程觸發跨越了 controller 的故障邊界：controller 重啟、時鐘抖動、API server 暫時不可達，都可能讓某次觸發漏掉或重複。因此**你的 Job 必須冪等**（見冪等，領域 A）——同一邏輯時間點跑兩次不能造成雙重副作用。

`concurrencyPolicy` 提供的也只是**盡力**保證，不是分散式互斥鎖。`Forbid` 不保證「絕對不重疊」（兩個 controller 視角下的競態仍可能讓兩個 Job 短暫並存）；要真正的單一執行者保證，需在 Job 內部再加一把分散式鎖 + fencing token（見分散式鎖，領域 M）。

**Worked example（漏跑的代價）**：一個 `*/5 * * * *`（每 5 分鐘）的 CronJob，叢集 control plane 升級導致 controller 停了 4 小時。4 小時 = 240 分鐘 = **48 次**排程被錯過。重啟後 48 < 100，controller 會為**最近一個**漏掉的時間點補建『一個』Job（K8s 刻意只補最新一次、不會把那 48 次批量回填）。但若停了 **9 小時** = 540 分鐘 = 108 次 > 100，controller 直接放棄、記 error 並**不再排程**——一個沒設 `startingDeadlineSeconds` 的每分鐘 CronJob，叢集斷 1 小時 41 分（101 分鐘）就會永久卡住，直到人工介入。這是真實的生產陷阱：高頻 CronJob + 沒設 deadline + 一次長停機 = 排程默默死掉。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| K8s CronJob | 至少觸發（非 exactly-once）、叢集內統一調度 | 已在 K8s 上的週期批次 | 100 次漏跑死結、`Forbid` 非真互斥、Job 須冪等 |
| 傳統 crontab | 單機簡單、無依賴 | 單台機器的本地腳本 | 機器死即不跑、無 HA、無集中觀測 |
| EventBridge Scheduler / 雲 cron | 託管、高可用觸發 | serverless / 雲原生排程 | 仍非 exactly-once，下游須冪等 |
| Durable workflow 的 schedule | 排程 + 持久化狀態 + 自動重試恢復 | 長流程、需斷點恢復的排程任務 | 重，單純定時跑腳本用不到 |

判準：**已在 K8s 上、任務是冪等的短批次 → CronJob**；**任務本身是有狀態長流程 → 用 CronJob 只點火、流程交 durable workflow**；**需要嚴格不重疊 → CronJob 外加應用層分散式鎖**。

### 常見誤解與陷阱

- **「concurrencyPolicy: Forbid 等於分散式鎖」**：它只防同一 CronJob 的相鄰排程重疊，不防你別處手動觸發、不跨叢集、競態下仍可能短暫並存。要互斥保證得自己加鎖。
- **「CronJob 會 exactly-once 執行」**：不會。漏跑與重複都在官方承認的可能範圍內，Job 必須冪等。
- **沒設 `startingDeadlineSeconds` 的高頻任務**：一次長停機累積過 100 次漏跑，CronJob 會永久停擺且只在 controller log 留一行 error，監控若沒抓這條，會以為任務還在跑。
- **把 `schedule` 的時區當預設本地**：不指定 `timeZone` 時的解讀依叢集設定，跨時區團隊容易誤判觸發時刻（DST 邊界更亂，見時間與日期處理，領域 M）。
- **依賴 Job 一定成功**：CronJob 只管「建 Job」，Job 失敗的重試由 Job 的 `backoffLimit` 管，CronJob 不會因 Job 失敗而「補一次」——別把「建了 Job」當成「任務成功了」。

### 延伸閱讀

- [Kubernetes — CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)（官方，含 concurrencyPolicy、100 次漏跑、非 exactly-once 聲明）
- [Kubernetes — Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)（CronJob 生出的 Job 的重試/完成語意）

## 時間與排程

### 定義與原理

排程系統要回答兩個獨立的時間問題，混用任一個都會出事：**「現在幾點？要不要觸發？」**（牆鐘 wall clock 問題）和**「過了多久？逾時了沒？」**（間隔 interval 問題）。前者要的是與真實世界對齊的時刻，後者要的是穩定遞增的計時。

- **牆鐘（wall clock，`CLOCK_REALTIME`）**：與 UTC 對齊的「真實時刻」。它會被 NTP 校正、被管理員手動改、會因校時而**往前跳或往後退**。它能回答「現在是不是 03:00、該不該跑這個 cron」。
- **單調鐘（monotonic clock，`CLOCK_MONOTONIC`）**：從某個任意固定起點起**只增不減、不被 NTP 跳動影響**的計數（NTP 只能讓它緩慢 slew、不會讓它跳）。它能回答「我等了多久、逾時了沒」。

鐵律：**判斷「到點觸發」用牆鐘，判斷「過了多久 / 逾時」用單調鐘。** 用牆鐘量間隔的經典 bug：你記下開始時間 `t0 = now()`，NTP 在中途把牆鐘往回撥 2 秒，你算 `now() - t0` 得到**負的**經過時間——逾時邏輯瞬間錯亂（可能永不逾時，或立刻誤判逾時）。時間/時鐘的完整機制（邏輯時鐘、向量時鐘、UTC/DST 應用層坑）是領域 M 的範圍；本條只談排程觸發的這層語意。

排程的另一面是**觸發保證**：排程器和被觸發的工作之間隔著故障邊界，於是有兩個必答問題——**漏跑**（該觸發的時刻沒觸發，怎麼補？）與**補跑**（事後補觸發，會不會跟原本疊起來、會不會一口氣補一大批）。

### 解法空間

- **計時（逾時/退避）一律用單調鐘**：語言通常有對應 API（如 `process.hrtime`、`steady_clock`、`time.monotonic()`），別用 `Date.now()` / `gettimeofday` 量間隔。
- **觸發判斷用牆鐘 + 明確時區**：cron 表達式錨在某時區（指定 `timeZone`），不靠機器本地時區的隱含預設。
- **漏跑偵測**：記錄「上次成功觸發的邏輯時間」，重啟時比對應觸發時間，算出漏了幾次。
- **補跑策略二選一**：
  - **catch-up（補做）**：把漏掉的每個時間點都補跑一次（適合「每個時間點都有獨立工作」如每小時對帳）。
  - **skip-to-latest（只做最新）**：漏了 N 次只跑最新一次（適合「冪等的全部重刷」如重算快取，補做 N 次是浪費）。
- **設窗口上限**：給補跑加 deadline（如 K8s 的 `startingDeadlineSeconds`），避免長停機後一次補建一大批把系統打爆。
- **去重邏輯時間鍵**：每次觸發帶一個「邏輯排程時間」當冪等鍵，重複觸發同一時間點被去重（見冪等 / 去重，領域 A）。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| 單調鐘量間隔 | 逾時/退避計算不受校時影響 | 所有 timeout、retry backoff、計時 | 不能拿去顯示「現在幾點」，它無對應真實時刻 |
| 牆鐘判觸發 | 與真實時刻對齊、人看得懂 | cron 觸發、「每天 03:00 跑」 | 受 NTP/DST 影響，跨時區須明確指定 |
| catch-up 補跑 | 不漏掉任一時間點的工作 | 每時間點工作獨立（對帳、計費窗） | 長停機後可能一次補一大批，要配窗口上限 |
| skip-to-latest | 避免補跑風暴 | 冪等的全部重刷（重算/重建） | 中間時間點的「那一刻狀態」會永久缺失 |
| 邏輯時間鍵去重 | 重複觸發不造成雙重副作用 | 任何非 exactly-once 的排程 | 需要一個持久的去重 store 與 TTL |

### 何時需要

- **必須區分兩種鐘**：任何同時做「定時觸發」又做「逾時控制」的系統——幾乎所有排程器/worker 都是。
- **必須想清補跑策略**：任務在「漏跑代價高」（計費、對帳缺一窗就少算錢）或「補跑代價高」（一次補 100 次把下游打爆）的場景。
- **可以簡化**：純展示用、漏一兩次無感、人工隨時可手動重觸發的內部小任務——不必上完整的漏跑偵測 + 去重，但「量間隔用單調鐘」這條仍該守（成本幾乎為零、踩雷代價高）。

### 常見誤解與陷阱

- **用牆鐘量逾時**：`const t0 = Date.now(); ... if (Date.now() - t0 > TIMEOUT)`（示意，不可執行）——NTP 往回撥時 `Date.now() - t0` 可能變負或暴增，逾時判斷錯亂。改用單調鐘。
- **假設 cron「不會漏、不會重」**：排程器跨故障邊界，漏跑與重複是常態（CronJob 官方就明說非 exactly-once，見 K8s CronJob）。沒有去重 + 冪等，補跑就是雙重副作用。
- **補跑風暴**：長停機後 catch-up 一口氣補建幾十上百個 Job，瞬間把下游打爆——補跑必須有窗口上限或改 skip-to-latest。
- **時區與 DST**：把 cron 錨在會 DST 的本地時區，春季跳鐘那天「02:30」這個時刻不存在、秋季回撥那天出現兩次——觸發時刻會詭異（機制細節見時間與日期處理，領域 M）。生產排程多以 UTC 錨定。
- **把「該幾點」和「過多久」當同一個時間源**：兩個問題、兩種鐘，混用就是埋雷。

### 延伸閱讀

- [Linux `clock_gettime(2)` — CLOCK_MONOTONIC vs CLOCK_REALTIME](https://man7.org/linux/man-pages/man2/clock_gettime.2.html)
- [Cron expression format（crontab(5)）](https://man7.org/linux/man-pages/man5/crontab.5.html)

## 失敗偵測

### 定義與原理

在分散式系統裡，你想知道「對面那個節點/任務還活著嗎」，但你能依靠的只有一件事：**你發出去的東西，在限定時間內有沒有得到回應。** 沒有別的訊號。對方沒回應，可能是它死了、可能是它還活著只是慢、可能是網路把訊息或回應吞了——而**你無法從外部區分這三者**。這是失敗偵測的第一原理，也是它最殘酷的地方：**逾時（timeout）是唯一可用的失敗偵測手段，而逾時無法區分「慢」與「死」。**

這直接推出一個著名結論的工程版本：在一個訊息可能任意延遲的非同步網路裡，你不可能造出一個「絕不誤判」的完美失敗偵測器。任何逾時值都是一個賭注——設太短，把只是慢的健康節點誤判為死（false positive），可能引發不必要的 failover、重試、甚至把工作重複執行；設太長，真的死了卻遲遲不發現（高偵測延遲），故障期間請求持續打進黑洞。你只能在「誤判率」與「偵測延遲」之間選一個點，沒有兩全。

health check 探針的具體機制（liveness vs readiness 的差異與設計）是領域 P 的範圍；本條只講「逾時是唯一手段、慢與死不可分」這個分散式視角下的根本約束。

### 解法空間

既然單次逾時無法區分慢與死，工程上的辦法是**加更多訊號、把「賭注」做得更聰明**：

- **逾時 + 重試（有限次）**：一次逾時可能是暫時慢，重試幾次再判死。但重試本身會放大負載（見 retry storm，領域 E），且若對方其實活著只是慢，重試 = 重複執行，必須冪等。
- **心跳 / keepalive**：對方週期性主動發「我還在」，連續漏 N 拍才判死。把「一次逾時」軟化成「連續多次無訊號」，降誤判。
- **phi accrual failure detector**：不輸出「死/活」二元，而輸出一個「懷疑值」（φ）隨無回應時間連續上升，讓上層自己決定門檻——同一偵測器服務不同敏感度需求。
- **間接探測 / gossip**：A 判不準 B，就問 C「你連得到 B 嗎」，多方視角降單點誤判（見 gossip / anti-entropy，領域 M）。
- **fencing token**：承認「誤判無法消除」，改為讓誤判**無害**——被判死的節點若其實沒死、事後醒來想寫資料，用單調遞增的 fencing token 讓它的舊請求被拒（見分散式鎖，領域 M）。這是面對失敗偵測不完美的正解：不是追求零誤判，是讓誤判不造成資料損壞。
- **deadline 而非 timeout**：傳遞「絕對截止時刻」而非「相對逾時」，跨多跳呼叫時逾時預算才不會被重置累加（見 timeout / deadline / budget，領域 P）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 單次逾時 | 簡單、立即判定 | 單跳呼叫、誤判可容忍 | 慢=死不可分，誤判率與偵測延遲難兩全 |
| 逾時 + 有限重試 | 降低暫時性慢的誤判 | 冪等操作、瞬時抖動多的環境 | 放大負載；對活著只是慢的節點＝重複執行 |
| 心跳 / 連續 N 拍 | 把瞬時抖動過濾掉，降誤判 | 叢集成員存活偵測 | 偵測延遲 = N × 心跳間隔，更慢；網路分區下整片誤判 |
| phi accrual | 連續懷疑值、可分級反應 | 對誤判成本不同的多種消費者 | 較複雜，需調參與歷史視窗 |
| fencing token | 讓誤判不造成損壞（而非消除誤判） | 任何「被判死的節點復活仍可能寫」的場景 | 需要寫入端配合檢查 token；不能單獨用 |

判準：**誤判代價低（重連即可）→ 簡單逾時 + 重試**；**誤判代價高（會 failover、會雙寫）→ 心跳降誤判 + fencing token 讓殘餘誤判無害**。

### 何時需要

- **必須認真做**：任何有 failover、leader 切換、把「死掉的」工作重派給別人的系統——誤判直接導致雙主、重複執行、資料衝突。
- **必須配冪等/fencing**：只要失敗偵測會觸發「重做」或「換人做」，下游就必須冪等或有 fencing，因為被判死的節點可能其實沒死。
- **可以從簡**：請求/回應的單跳同步呼叫，逾時後直接回錯給上游、由上游決定——這時一個合理逾時 + 上游重試就夠，不需要完整偵測器。

**Worked example（逾時值的賭注）**：一個服務正常回應 p99 = 200 ms、p999 = 900 ms。把 client 逾時設 **250 ms**（略高於 p99）：所有跑超過 250 ms 的請求都會被當成失敗——這大約是 p99 以上那一小撮、約 **1%** 的請求，它們其實還活著、只是慢，卻被誤判而重試。若這些重試又疊到其他慢請求上，會把更多請求推過 250 ms，形成正回饋。反過來把逾時放寬到 **900 ms（≈ p999）**：誤判降到約 **0.1%**（只剩最尾巴那千分之一），但真的死掉的節點要等滿約 1s 才被發現，故障期間每個打進去的請求都白等近 1s。250 ms vs 900 ms，就是「誤判率 vs 偵測延遲」這枚硬幣的兩面——沒有同時把兩者都壓到零的設定。

### 常見誤解與陷阱

- **「沒回應就是死了」**：沒回應 = 死、或慢、或網路丟包，三者外部不可分。當成「一定死了」去 failover，就會在對方其實活著時造成雙主/重複執行。
- **逾時設太短引發 retry storm**：誤判 → 重試 → 加負載 → 更多請求變慢 → 更多誤判，正回饋雪崩（見 retry storm · metastable failure，領域 E）。
- **以為加心跳就「準了」**：心跳只是把單次逾時換成「連續 N 拍無訊號」，降誤判但拉長偵測延遲，且網路分區時分區另一側會被整片誤判為死——準不了，只是換了賭注的位置。
- **追求零誤判**：在非同步網路裡這做不到。正確心態是「假設誤判一定會發生，讓它無害」——這就是 fencing token 存在的理由。
- **逾時跨多跳不傳 deadline**：每一跳各自重設一個相對逾時，總時間預算被悄悄放大，外層以為設了 1s、實際下游可能跑了好幾秒（見 timeout / deadline / budget，領域 P）。

### 延伸閱讀

- [Unreliable Failure Detectors for Reliable Distributed Systems（Chandra & Toueg, 1996）](https://www.cs.utexas.edu/~lorenzo/corsi/cs380d/papers/p225-chandra.pdf)
- [The φ Accrual Failure Detector（Hayashibara et al., 2004）](https://www.computer.org/csdl/proceedings-article/srds/2004/22390066/12OmNvT2phv)
