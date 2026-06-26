# ch18 — 雲端原語：SQS／SNS／Lambda／ALB／API Gateway／KrakenD

> **本章解決什麼問題**：這是 Part IV「橫切的老問題」的最後一站，也是整個 Part 的收口。前面九章把交付（ch10）、一致（ch11）、並發（ch12）、時間（ch13）、背壓（ch14）、觀測（ch15）、身分（ch16）、快取（ch17）這些老問題從你的系統裡抽出來挖穿了。這一章回到一個很具體的地方：你履歷上那一排 **AWS／閘道名詞**——SQS、SNS、Lambda、ALB、API Gateway、KrakenD。你在 ECS／Lambda 上把它們當積木拼過，但你大概從沒並排問過一個問題：**它們各自在五軸上預設了什麼答案？** 本章的主張只有一句——**它們不是可互換的積木**，每一個原語都替你回答了某幾個故障問句、又把另外幾個甩回給你。把它們攤在五軸體檢表上，你會看見哪個保證不丟、哪個一定會重、哪個重啟就失憶。最後一張並排表，是全書脊椎在雲端原語上的兌現。

## 從你已知的出發

你在 NeoBards 和 LetsTalk 用過這整排雲端原語，而且不是淺嘗。結算 pipeline（ch04）那條 **CronJob → SQS → 冪等 consumer**，SQS 是中間那條命脈；通知與整合層你碰過 **SNS** 的扇出；你在 ECS 上跑服務、用 **ALB** 做 L7 路由，也接過 **API Gateway**；履歷上還列了 **KrakenD**——你拿它當 API Gateway 做過聚合。你甚至列了 **Lambda**，雖然你的主力是長駐的 Node 服務。

你當年用它們的方式，多半是「需要一個佇列 → 拉個 SQS」「要扇出 → SNS」「要個對外入口 → ALB 或 API Gateway」。這是工作級的熟練：知道哪個服務做哪件事、設定怎麼填、權限怎麼開。沒問題，你線上跑過、扛過流量。

但我想問你一個你當年大概**沒並排想過**的問題。你把這些東西當成一盒積木，需要哪塊就拿哪塊——彷彿它們是同一種材質、只是形狀不同。它們不是。**每一個原語都是別人替你在五個故障問句上做好的一組決定**：SQS 替你決定了「訊息會重、但不會掉」；Lambda 替你決定了「每次呼叫都是一張白紙，上一次的記憶體不存在」；ALB 替你決定了「我只管把連線送到健康的後端，request 裡寫什麼我不看」。你選一個原語，就是吞下它替你做好的那組決定——連同它甩回給你的那幾軸。

還有一串「老兵記憶」在這章會被逐一校正，而且這次特別反直覺：**有些事實不是你記錯了，是它最近才變的**。你 2019–2024 用 SQS 時，單則訊息上限**就是** 256 KB——你記得沒錯。但它在 **2025-08** 才被提到 1 MiB。Lambda 的非同步 payload 上限也在 **2025-10** 從 256 KB 升到 1 MB。KrakenD 背後的公司在 **2025-09** 被收購了。你的記憶在它那個年代是對的——這才是「老兵記憶」最危險的地方：**它不會報錯，它只是默默地停在某個版本，而世界往前走了**。

這一章把這六個原語從「會用」挖到「各自保證什麼、各自會怎麼騙你」，然後用全書的五軸透鏡，把它們並排放上同一張體檢表。

## SQS：at-least-once 是它的本性，不是它的 bug

SQS 是這整排原語裡你最熟、也最容易記錯細節的一個。ch04 和 ch10 已經把它的核心語意挖過了——這裡做收口，把細節補齊、把陷阱列全。

### Standard vs FIFO：交付與排序的兩套語意

SQS 有兩種佇列，它們在**交付**和**排序**這兩軸上是兩套完全不同的答案（landscape §1）：

| 維度 | Standard（標準佇列） | FIFO（先進先出佇列） |
|---|---|---|
| 交付保證 | **at-least-once**（至少一次，可能重複） | **exactly-once *processing***（靠去重窗，效果上剛好一次） |
| 排序 | **best-effort**（盡力，不保證） | **strict ordering**（嚴格，per message group） |
| 去重機制 | 無（重複要你自己擋） | `MessageDeduplicationId` ＋ **5 分鐘**去重窗 |
| 吞吐 | 幾乎無上限（高） | 預設 per partition 每秒 **300 非批次／3,000 批次**；high throughput mode 主要 region 可達約 70,000 msg/s（批次，region-dependent） |

這張表的核心你在 ch10 已經懂了：FIFO 的「exactly-once」是 **exactly-once *processing***，不是交付——它是 SQS 用 `MessageDeduplicationId` 在 broker 端替你做的一層冪等，5 分鐘窗外就失效。它**不是**「更高級的傳輸技術、真的線上只傳一次」（那邏輯上不可能，ch10 用兩將軍退化版證過）。

要補的是**選型判準**。很多人一聽「Standard 會重複」就反射性想用 FIFO，這通常是錯的。判準是這樣：

- **你需要嚴格排序嗎？** 結算誰先誰後無所謂 → 不需要 → Standard。聊天訊息要按序到達、金融交易要按序入帳 → 需要 → FIFO。
- **你需要 broker 替你去重、還是自己做冪等更划算？** 如果你下游已經有業務層冪等（你的 `settlement_key`，ch04），FIFO 的去重窗是**重複的保險、且只覆蓋 5 分鐘**——付吞吐代價買一個你已經有、而且做得比它更久的東西，不划算。

> **決策框架**：FIFO 不是「Standard 的升級版」，是「為了排序與去重，付吞吐代價」的另一個取捨。**預設用 Standard ＋ 業務層冪等**；只有當「順序本身是正確性的一部分」時才換 FIFO。你結算 pipeline 選 Standard 是對的——你不需要排序，你的冪等做在業務層活一整季，比 FIFO 的 5 分鐘窗強得多。

### visibility timeout、DLQ、長輪詢：三個你該設對的旋鈕

這三個是 SQS 的操作面，但每一個背後都連著一軸故障：

**visibility timeout（可見性逾時，預設 30s、最大 12h、最小 0s，2026-06）。** ch04 挖過它的機制：consumer 撈走訊息後，訊息不消失，只是**暫時不可見**這段時間；處理完呼叫 `DeleteMessage` 才真正刪掉。沒刪（當機、太慢、`DeleteMessage` 沒送達）→ 到期重投。這就是 at-least-once 的根：**SQS 分不清你「死了」還是「只是慢」**，所以它永遠偏向重投。設定建議約處理時間的 6 倍——太短會在「真的還在處理」時誤判重投（製造重複），太長會讓「真的當機」的訊息卡很久才被重試。

**DLQ（死信佇列，dead-letter queue）。** 一則訊息被接收超過 `maxReceiveCount` 次還沒被成功刪除，SQS 把它移到你指定的 DLQ。它的用途是**隔離毒丸**——那些永久失敗的訊息（玩家帳號已刪、payload 壞掉）不會無限重試卡住佇列，而是被請到一邊。但 DLQ 最大的陷阱是 ch04 點過的「DLQ 黑洞」：訊息進了 DLQ 卻**沒人看**。DLQ 不是垃圾桶，是「需要人看的收件匣」——**DLQ 深度 > 0 本身就該告警**（這是觀測軸）。

**長輪詢（long polling，`WaitTimeSeconds` 最大 20s）。** 短輪詢（預設 0）的 `ReceiveMessage` 就算佇列空也立刻回，consumer 只好瘋狂空轉重試——浪費 API 呼叫（要錢）、浪費 CPU。長輪詢讓請求**等到有訊息或等滿 20 秒才回**，大幅減少空輪詢。這是個幾乎沒有壞處、卻常被忘記開的設定。

### 老兵記憶校正：單則上限是 1 MiB，但這是 2025 才變的

這是這章最值得停下來的一個事實，因為它示範了「老兵記憶」最刁鑽的一種形態。

你大概記得「SQS 單則訊息上限是 256 KB」。**你沒記錯**——在你 2019–2024 用它的整個期間，上限確實是 256 KB（更精確說 256 KiB），而且這個限制存在了很多年。但在 **2025-08-04**，AWS 宣布把上限提到 **1 MiB（1,048,576 bytes）**，標準佇列與 FIFO 佇列皆適用（2026-06，兩個獨立來源：AWS 官方 what's-new 公告 ＋ 多家第三方同日報導）。

一個常見的誤記是把這次提升放在 2022 年——其實 AWS 官方公告明載是 **2025-08-04**，且公告自述「256 KB 的舊上限已存在很長一段時間」。年份很重要，因為它決定了這到底是「你一直記錯」還是「你記得對、世界後來變了」——答案是後者。

這個年份校正讓「我以為 vs 實際」變得更精確、也更有意思：

> **我以為 vs 實際**：你以為「SQS 上限 256 KB」是你記錯了的過時事實。**其實你那個年代它就是 256 KB——是世界後來變了**，2025-08 才升到 1 MiB。這正是老兵記憶最危險的形態：它不是「一開始就錯」，是「曾經對、後來被偷偷改掉」。實戰後果：(1) 你當年「超過 256 KB 就得把 payload 丟 S3、佇列裡只放指標」的設計慣性，今天上限放寬到 1 MiB 後**不一定還需要**——但很多 8x8/256 KB 之間的 payload 現在可以直接進佇列了。(2) 就算到 1 MiB，**大訊息仍是反模式**：佇列要存的是「指標與意圖」，不是「資料本體」；真要傳 1 MiB～2 GB 的大物件，用 Extended Client Library 把 payload 放 S3、佇列只放 S3 引用（最大 2 GB）。**上限變大不等於你該塞滿它。**

## SNS：扇出是它的本職，推與拉是它和 SQS 的分工

SNS 常被和 SQS 放在一起講，但它們是兩種**不同方向**的東西。把這個方向想清楚，你就不會再糾結「這個場景該用 SNS 還是 SQS」。

### 推（push）vs 拉（pull）：一句話分工

- **SNS 是推（push）**：發佈者把訊息送進一個 **topic**，SNS 主動把它**推**給所有訂閱者（多個 SQS 佇列、Lambda、HTTP endpoint、email、SMS…）。訂閱者是被動接收的。
- **SQS 是拉（pull）**：訊息躺在佇列裡，consumer **主動來撈**（`ReceiveMessage`）。佇列是被動等人來拿的。

這個方向決定了它們各自擅長什麼。SNS 擅長**一對多扇出**（一則事件要通知很多個下游）；SQS 擅長**緩衝與解耦**（讓 consumer 按自己的步調慢慢消化，天然有背壓——consumer 慢，訊息就堆在佇列裡等，不會壓垮 consumer，見 ch14）。

### 招牌模式：SNS → 多個 SQS 的 fan-out

把兩者的長處接起來，就是 AWS 最標準的推薦架構（landscape §2）——**SNS topic 扇出到多個 SQS 佇列**：

```
                    ┌─────────────┐
   事件發佈 ───────►│  SNS topic  │
                    └──────┬──────┘
                           │  （推、扇出）
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ SQS 佇列 │   │ SQS 佇列 │   │ SQS 佇列 │
      │  （拉）  │   │  （拉）  │   │  （拉）  │
      └────┬─────┘   └────┬─────┘   └────┬─────┘
           ▼              ▼              ▼
       consumer A     consumer B     consumer C
       各自的步調      各自的步調      各自的步調
```

這個組合的妙處在於它**同時拿到兩者的長處**：SNS 負責「一則事件扇出給三個下游」（推、一對多），每個 SQS 負責「讓對應的 consumer 按自己步調消化、且訊息持久不掉、慢了就堆著」（拉、緩衝、背壓）。如果你只用 SNS 直推到三個 Lambda，那三個 Lambda 之中只要一個慢或掛，那一支的訊息就可能掉（SNS 直推有重試策略與 DLQ，但語意不如 SQS 緩衝穩）。中間墊一層 SQS，等於給每個下游各配一個持久的緩衝區。

### SNS FIFO 存在，但別誤用

一個容易被忽略的事實：**SNS 也有 FIFO topic**（landscape §2）。它提供嚴格排序與去重，可投遞到 SQS FIFO 佇列（保留排序／exactly-once processing），也可（2023-09 起）投到 SQS Standard 佇列（降級為 best-effort／at-least-once 以省成本）。但要注意限制：**SNS FIFO 不能直接投給 email／SMS／HTTP(S)／mobile push／Lambda**，必須先經 SQS。所以 SNS FIFO 的典型用法就是「FIFO topic → FIFO 佇列」的有序扇出，不是萬用的。

> **決策框架**：要「一則事件通知多個下游」→ SNS（推、扇出）。要「讓 consumer 按自己步調消化、有緩衝、不怕慢」→ SQS（拉、背壓）。兩個都要 → SNS → 多 SQS 的 fan-out。**別用 SNS 當佇列**（它不為你緩衝、訂閱者當下不在就靠重試策略兜，語意比 SQS 弱）；也別用 SQS 做扇出（一則訊息被一個 consumer 撈走就不在了，要扇給三個下游得自己複製三份）。

## Lambda：無狀態是前提，冷啟動是現實

你履歷上有 Lambda，但你的主力是長駐 Node 服務。這個對照恰好是理解 Lambda 的最好切入點：**Lambda 把你那台長駐伺服器的「記憶」拿掉了**，換來「不跑不收錢、自動擴展」。理解 Lambda 的關鍵，全在這個交換裡。

### 執行模型：每次呼叫都是一張白紙

Lambda 是事件驅動的：一個事件來（HTTP、SQS 訊息、SNS、排程…），Lambda 啟動一個 **execution environment**（執行環境）來跑你的函式，跑完環境可能被凍結、重用、或回收。關鍵語意：

- **「無狀態」是前提，不是建議**。你不能假設「上一次呼叫在記憶體裡存的東西，這一次還在」。execution environment 會被重用（所以 handler 外的全域變數**有時**還在——這是 warm start），但你**不能依賴**它還在（下一次可能是全新環境——cold start）。把任何**必須跨呼叫存活的狀態**放進 Lambda 的記憶體或本地磁碟，就是在埋一顆「有時對、有時錯」的雷。狀態必須外部化到 DynamoDB／RDS／S3／ElastiCache。
- **本書脊椎的回響**：這正是「持久軸」的極端形態。你那條 setTimeout（ch09）撐不住是因為「計時器活在單一行程記憶體裡、重啟即失憶」；Lambda 把這個性質**變成了規格**——它**設計上**就會頻繁地「重啟」（回收環境）。在 Lambda 上，「重啟失憶」不是故障，是常態。

### 冷啟動：你拿掉長駐，代價在這裡

**冷啟動（cold start）** 是 Lambda 最有名的現實。當沒有可重用的 warm 環境時，Lambda 要：下載你的程式碼 → 啟動 runtime → 初始化（跑 handler 外的程式碼、建連線池…）→ 才開始處理事件。這段初始化延遲就是冷啟動，對延遲敏感的同步 API 特別有感。

降冷啟動的手段（2026-06）：

- **provisioned concurrency**：預先初始化好一批環境，永遠 warm——代價是這些環境**閒著也收錢**（你又把「長駐的成本」買回來了一部分）。
- **SnapStart**：把初始化後的環境**快照**起來，後續從快照還原，可去除約 70–90% 的 init latency。**關鍵限制（2026-06，已查證）**：SnapStart **支援 Java（11+）、Python（3.12+）、.NET（8+）**，三者皆已 GA（Python／.NET 於 2024-11 GA）；**Node.js 不支援**、Ruby／OS-only／container image 也不支援。

> **老兵記憶校正**：如果你印象裡 SnapStart「只有 Java」，那是 2022 剛推出時的狀態。2024-11 起 Python 和 .NET 也 GA 了。但**Node.js 至今（2026-06）仍不支援**——所以如果你的 Lambda 是 Node，SnapStart 幫不上你，降冷啟動只能靠 provisioned concurrency 或把初始化做輕。

### 上限與 payload：又一個剛變過的數字

Lambda 的硬上限（2026-06，已查證）：

- **預設併發 1,000**（per region，可申請調高）。reserved concurrency 可為某函式預留、provisioned concurrency 預先初始化降冷啟動。
- **timeout 最大 900s（15 分鐘）**，預設 3s。
- **記憶體 128 MB–10,240 MB**；`/tmp` 暫存預設 512 MB、可調到 10,240 MB。
- **payload**：同步呼叫（synchronous）**6 MB**；非同步呼叫（asynchronous）**1 MB**。

> **老兵記憶校正（async payload）**：非同步 payload 上限在 **2025-10-24** 從 **256 KB** 提到了 **1 MB**（2026-06，已查證，AWS 官方 what's-new）。同步仍是 6 MB。如果你記得「Lambda async 事件最大 256 KB」——又是一個「曾經對、2025-10 後變了」的老兵記憶。注意這跟前面 SQS 1 MiB 是**兩個獨立的、都發生在 2025 下半年的**放寬，別搞混（SQS 是訊息上限、Lambda 是 invoke payload 上限）。

> **決策框架**：什麼時候 Lambda 是對的工具？**突發、短時、無狀態、可水平攤平**的工作——事件處理、定時任務、輕量 API。什麼時候不是？**需要常駐長連線**（WebSocket server，連線狀態綁機器，ch07 的 sticky session 在 Lambda 上很彆扭）、**需要跨呼叫的本地狀態**（你會被無狀態前提反咬）、**長時間運算**（900s 上限）、**對冷啟動零容忍且是 Node**（SnapStart 救不了你）。你 LetsTalk 的 WebSocket 通知系統用長駐 Node 服務而不是 Lambda，是對的——長連線的 Lambda 是逆風飛行。

## ALB vs API Gateway：負載均衡不是 API 管理

這是你最容易「憑直覺擺錯」的一組。ALB 和 API Gateway 都能當「對外入口」，但它們是**兩種不同層次**的東西——一個是 L7 負載均衡器，一個是 API 管理層。把它們的本職分清楚，選型就不糾結了。

### ALB：L7 負載均衡，它不看你 request 裡寫什麼

**ALB（Application Load Balancer）** 是 L7（應用層）負載均衡器（landscape §18）。它的本職是：根據 host／path／header 把進來的連線**路由**到健康的後端（target group——ECS 容器、EC2、Lambda）。它做的事：

- host/path/header-based routing（`/api/*` 去這組、`/admin/*` 去那組）。
- 健康檢查、把流量從掛掉的後端移開。
- 原生 OIDC/Cognito listener 層級認證（但**不是** per-request 細粒度授權）。

它**不做**的事，正是區分它和 API Gateway 的關鍵：**沒有 per-request 的 request/response 轉換**、**沒有原生限流**（要搭 WAF 做 rate limiting）、**沒有 usage plan／API key**。ALB 的世界觀是「我把連線送到健康的後端，request body 裡寫什麼是後端的事，我不看」。

它的優勢：**成本（LCU 模型，高吞吐下便宜）、延遲（低）、吞吐（幾乎無上限）**。

### API Gateway：API 管理，per-request 的治理層

**API Gateway** 是完整的 API 管理層（landscape §18）。它在 ALB 之上多做的事，全是「**per-request 的治理**」：

- **限流（throttling）**：REST API 帳號預設約 **10,000 RPS steady-state（穩態速率）／burst bucket 5,000 requests（突發桶容量，token bucket 最大並發）**（per region）——別把兩者記反了，10,000 是每秒速率、5,000 是桶能一次吞的並發量。可設 usage plan 做 per-client 限流。
- **認證授權**：JWT authorizer、Lambda authorizer、IAM——可在閘道層驗 token，把授權從後端程式碼裡拿出來。
- **request/response 轉換**：REST API 的 VTL mapping template 可改寫請求／回應。
- **usage plan ／ API key**：給不同客戶不同配額。

代價：**整體較貴、延遲較高、吞吐有上限**（那個 10,000 RPS）。

### HTTP API vs REST API：API Gateway 自己也分兩種

API Gateway 內部還分兩種，這也常被搞混（landscape §18）：

| 維度 | HTTP API | REST API |
|---|---|---|
| 定位 | 較新、輕量 | 功能最完整 |
| 成本 | 約**便宜 70%** | 較貴 |
| 延遲 | 較低 | 較高 |
| 認證 | 支援 JWT authorizer | JWT／Lambda／IAM 全有 |
| 缺什麼 | 無 VTL mapping、無 usage plan、無 API key、無 private endpoint | —（最完整） |

經驗法則：需要 VTL 轉換／usage plan／API key → REST API；只要便宜快速的 proxy ＋ 簡單 JWT 認證 → HTTP API。

> **決策框架**：純 L7 路由到容器／EC2、**不需要 per-request 認證或轉換** → **ALB**（便宜、快、吞吐高）。需要**限流、API key、usage plan、per-request 認證或轉換** → **API Gateway**（REST 要 VTL/usage plan、HTTP 要便宜快速）。最常見的擺錯是「為了一個對外 API 反射性拉 API Gateway」——如果你只是把流量導到 ECS、認證已在服務內做、不需要 usage plan，ALB 又便宜又快，API Gateway 的治理功能你一個都沒用到、卻付了它的延遲與費用。**先問「我需不需要 per-request 治理」，再決定要不要那一層 API 管理。**

## KrakenD：無狀態 API Gateway，招牌是聚合

KrakenD 在你履歷上，是因為你拿它當 API Gateway 做過 API 聚合。它和上面的 AWS 原語不同——它是一個**你自己部署的開源閘道**，不是託管服務。理解它的關鍵在兩件事：**無狀態**和**聚合**。

### 它是什麼：Go 寫的、無狀態、宣告式

KrakenD（landscape §16）是用 **Go** 寫的 **stateless（無狀態）、declarative（宣告式）、高效能 API Gateway**。「無狀態」在這裡很具體：它**沒有 runtime database**——啟動時讀一份 JSON 設定檔，把所有路由、聚合、轉換規則編譯進記憶體，然後就照著跑。沒有控制面資料庫、沒有運行時可變狀態。這讓它**水平擴展極簡單**（每個實例都一樣、無共享狀態、加機器就行），也讓它快。

它的**招牌能力是 native API aggregation（原生 API 聚合）**：一個進來的請求，KrakenD 可以**並行**打多個後端、把回應**合併**成一個、過濾／重塑欄位後回給 client。這正是你當年用它做的事——前端要一個畫面的資料，背後是三個 microservice，KrakenD 在閘道層幫你聚合成一次回應，前端不用打三次。

### 治理精確：別說錯它屬於誰

這裡有一串**極容易說錯**的治理細節，面試講錯會被抓（landscape §16，2026-06 已查證）：

- **捐給基金會的不是整個 KrakenD，是它的核心 framework「Lura Project」**，於 **2021-05** 捐給 **Linux Foundation** 主持。KrakenD Community／Enterprise 是 Lura engine 的兩個實作。
- **是 Linux Foundation，不是 CNCF**。這兩個常被混用——說「KrakenD 是 CNCF 專案」是錯的。
- **2025-09，KrakenD（公司）被 Shop Circle 收購**，團隊與路線圖維持，Lura framework 續留 Linux Foundation、核心仍開源。所以說「KrakenD 仍是獨立開源公司」也不對了——2025 起它屬於 Shop Circle。

> **老兵記憶校正**：如果你印象裡「KrakenD 是一家獨立開源公司」，那是 2025-09 之前的事。被 Shop Circle 收購後團隊和開源承諾都還在，但所有權變了。而且請記準：**捐出去的是 framework「Lura」、給的是 Linux Foundation（不是 CNCF）**——這三個點（哪個被捐、捐給誰、公司被誰收）任何一個說錯，懂的人一聽就知道你只是聽過名字。

### 對照 Kong：兩種不同哲學的閘道

把 KrakenD 和 **Kong** 並排，能看清它的取捨（landscape §16）：

| 維度 | KrakenD | Kong |
|---|---|---|
| 底層 | Go，自有引擎 | NGINX/OpenResty ＋ Lua |
| 狀態 | **無狀態**（讀 JSON 設定、無 runtime DB） | 控制面有 DB（PostgreSQL/Cassandra），亦有 DB-less 模式 |
| 招牌 | **native API aggregation**（聚合） | **plugin 生態**（豐富的 runtime plugin） |
| 擴展模型 | 宣告式設定，**無 runtime plugin 系統** | runtime plugin（Lua/其他），生態為其強項 |

它們是兩種哲學：KrakenD 賭「無狀態 ＋ 宣告式 ＋ 聚合」——簡單、快、易擴展，但你想加它沒內建的行為時沒有 plugin 系統那麼靈活；Kong 賭「plugin 生態 ＋ 控制面」——什麼都能裝外掛，但帶著一個有狀態的控制面、運維更重。

> **決策框架**：要**把多個後端聚合成一次回應**、要**極簡無狀態水平擴展**、不需要一大堆現成 plugin → KrakenD。要**豐富的現成 plugin 生態**（認證、限流、轉換各種外掛即裝即用）、能接受一個有狀態控制面 → Kong。要**全託管、不想自己運維閘道** → AWS API Gateway。你當年選 KrakenD 做聚合是對的——聚合正是它的本職，而你不需要 Kong 那一櫃子 plugin。

## 故障模式與防禦

這六個原語各自會怎麼壞、壞了長什麼樣、怎麼防。至少一個綁定你真實的系統。

| 故障 | 壞了長什麼樣（可觀測徵兆） | 怎麼防 |
|---|---|---|
| **SQS 訊息重複被處理**（visibility timeout 到期重投 ＋ consumer 非冪等，**你的結算 pipeline**） | 玩家貨幣翻倍、收到兩份獎勵；對帳查出 settlement 筆數與發放量對不上 | 業務層冪等鍵（`settlement_key` 唯一約束，ch04/ch10）；visibility timeout 設約處理時間 6 倍；不靠 FIFO 取代業務冪等 |
| **SQS DLQ 黑洞**（毒丸訊息進了 DLQ 但沒人看） | 一批永久失敗的工作靜靜躺在 DLQ，下游靜默少做、無人發現 | **DLQ 深度 > 0 即告警**；把 DLQ 當「需要人看的收件匣」不是垃圾桶 |
| **把 SNS 當佇列用**（直推下游、無緩衝） | 下游一慢或一掛，那一支的訊息靠重試策略兜、語意比 SQS 弱、可能掉 | 要緩衝與背壓就在 SNS 和下游之間墊 SQS（fan-out 標準架構）；要持久消化用 SQS 不用 SNS 直推 |
| **Lambda 被當有狀態服務用**（依賴 handler 外全域狀態跨呼叫存活） | 「有時對有時錯」——warm start 時對、cold start 時資料不見；偶發、難重現的 bug | 把所有跨呼叫狀態外部化（DynamoDB/RDS/S3/ElastiCache）；handler 外只放「可重建的初始化」（連線池），不放「業務狀態」 |
| **Lambda 冷啟動拖垮尾延遲**（Node runtime、無 provisioned concurrency） | p99/p999 尾延遲尖刺，且和流量無關、像隨機；SnapStart 對 Node 無效 | Node 上靠 provisioned concurrency ＋ 把初始化做輕；對延遲敏感且高頻的同步 API 重新評估該不該用 Lambda |
| **Lambda 併發打到上限**（預設 1,000、上游突發） | 函式被 throttle、事件被丟回重試或進 DLQ；上游看到大量 429/throttle | 申請調高併發上限；用 reserved concurrency 給關鍵函式預留；上游加退避＋jitter（ch14）避免 retry storm |
| **該用 ALB 卻用了 API Gateway**（純路由卻拉了治理層） | 多付延遲與費用、撞上 10,000 RPS 上限、治理功能一個沒用到 | 先問「需不需要 per-request 治理」；純 L7 路由到容器用 ALB；要限流/usage plan/轉換才上 API Gateway |
| **KrakenD 聚合的後端有一個慢**（聚合等最慢的那個） | 聚合回應整體變慢、被最慢的後端拖住；尾延遲被「木桶最短板」決定 | 對每個聚合後端設獨立 timeout；非關鍵後端允許「部分回應」（缺一塊也回）；觀測每個後端的 per-backend 延遲 |

注意這張表的脈絡：**幾乎每一個故障都是「你選了某個原語、卻沒吞下它甩回給你的那一軸」**。SQS 把交付軸的「會重」甩給你（你得做冪等）；Lambda 把持久軸的「重啟失憶」變成規格（你得外部化狀態）；ALB 把治理甩回後端（你以為它會幫你限流，它不會）。**選原語就是吞它的取捨**——這正是下一節並排體檢表要攤開的事。通用的「複合系統為什麼會以意想不到的方式崩壞」分類見《正常意外》（fail）。

## 紙上推演

### 推演一：把 SQS／SNS／Lambda 並排做五軸體檢 **[25 分鐘]** ★★★

這是本章的 worked example，也是全書脊椎在雲端原語上的兌現。把 **SQS Standard 佇列**、**SNS topic**、**Lambda 函式**三個原語並排，對每一個做一次五軸體檢（交付／持久／分區／並發／觀測）。

**問**：對每個原語、每一軸，回答兩件事——(1) 它替你保證了什麼？(2) 它把什麼甩回給你（你得自己處理什麼）？特別要答出：**誰保證不丟、誰可能重、誰重啟失憶**。最後用一句話總結這三個原語各自「最該配什麼防禦」。

### 推演二：手追「Lambda 處理 SQS 訊息但逾時、SQS visibility 到期重投」的重複場景 **[20 分鐘]** ★★

你用 **SQS → Lambda**（event source mapping）處理結算訊息。一筆獎勵訊息進了 SQS，Lambda 被觸發來處理它。Lambda 的 timeout 設 30 秒，SQS 的 visibility timeout 也設 30 秒（這是個**陷阱設定**）。這次 Lambda 處理到第 28 秒時，下游一個服務慢，Lambda 在第 30 秒**逾時被殺**——它已經寫了 guild、player，但還沒寫完 inventory、mail，也還沒成功處理完讓 SQS 刪除訊息。

**問**：(a) 第 30 秒同時發生了兩件事，是哪兩件？(b) 這則訊息接下來會怎樣？(c) 如果 Lambda 處理**不冪等**，玩家最後拿到什麼？(d) 這裡 visibility timeout = Lambda timeout 為什麼是個陷阱設定？正確該怎麼設？(e) 這個場景收口到 ch10 的哪條安全帶？

### 推演三：三個需求各選哪個原語並說理由 **[15 分鐘]** ★★

為下面三個需求各選一個原語（或組合）並說「被放棄的選項輸在哪」：

- **(甲)** 一則「使用者升級了方案」事件，要同時通知計費服務、通知系統、資料倉儲三個下游，每個下游按自己步調消化、且不能掉。
- **(乙)** 一個對外 REST API，要按客戶分級限流（免費版每秒 10 次、付費版每秒 100 次）、在閘道層驗 JWT、不想在每個後端各寫一遍。
- **(丙)** 一個前端畫面要的資料來自三個 microservice，希望前端打一次就拿到合併好的結果。

### 推演解答

**推演一解答。**

並排五軸體檢（核心：誰保證不丟、誰可能重、誰重啟失憶）：

| 軸 | SQS Standard 佇列 | SNS topic | Lambda 函式 |
|---|---|---|---|
| **交付** | 保證**不丟**（持久重投）、但**會重**（at-least-once）；甩回「做冪等」給你 | **盡力推**給訂閱者、有重試策略＋DLQ，但語意比 SQS 弱、訂閱端不在時靠重試兜；甩回「要不要墊 SQS 緩衝」給你 | 同步呼叫成敗即時回傳；**非同步**呼叫失敗會重試（at-least-once）＋可配 DLQ；甩回「函式要冪等」給你 |
| **持久** | **訊息持久在佇列**（最大保留 14 天）；consumer 重啟不丟工作 | topic 本身不存訊息（推完就走）；持久性靠下游（墊 SQS 才有）；甩回「持久化在哪」給你 | **重啟即失憶**——execution environment 隨時被回收，記憶體/本地磁碟狀態不保證存活；甩回「狀態外部化」給你 |
| **分區** | 跨可用區冗餘、佇列本身高可用；訊息順序 best-effort（Standard） | 跨區高可用；多訂閱者各自看到的時序可能不同 | 無狀態 → 沒有自己的一致性問題，但它讀寫的外部存儲有（那是 ch11 的事） |
| **並發** | 多 consumer 並發撈同一佇列是常態；visibility timeout 防同則被兩人同時處理（但超時反製造重複） | 扇出本身就是並發推送；各訂閱者獨立 | **預設併發 1,000**（per region）；超過被 throttle；甩回「預留/調高/退避」給你 |
| **觀測** | 佇列深度、in-flight 數、DLQ 深度、訊息齡都是 metric；甩回「設告警」給你 | 投遞成功/失敗數、DLQ；甩回「訂閱端有沒有真的收到」的端到端觀測給你 | invocation 數、error 數、duration、throttle 數、冷啟動；甩回「業務正確性觀測」給你 |

一句話總結各自最該配的防禦：**SQS → 業務層冪等 ＋ DLQ 告警**；**SNS → 墊 SQS 緩衝（要持久消化時）**；**Lambda → 狀態外部化 ＋ 函式冪等 ＋ 併發預留**。三句話都指向同一個底層：**at-least-once ＋ 冪等是預設安全帶**（ch10）。

**推演二解答。**

(a) 第 30 秒同時發生兩件事：**(1) Lambda 自己的 timeout 到期，函式被強制終止**（它寫了 guild、player，但 inventory、mail 沒寫完，也沒成功回報 SQS 刪除）；**(2) SQS 的 visibility timeout 同時到期**，這則訊息**重新變可見**。

(b) 訊息接下來會被**重新投遞**——SQS event source mapping 會再觸發一次 Lambda（或同一批的下一次輪詢）來處理同一則訊息，從頭跑：寫 guild、寫 player……

(c) **不冪等**：第二次處理從頭來，guild 再結算、player **再加一次錢**、inventory 加道具、mail 寄信。第一次已經寫成功的 guild、player 被**重做**——玩家**雙領**了貨幣（以及第二次補上的道具與信）。

(d) **visibility timeout = Lambda timeout 是陷阱**，因為它**沒有給「Lambda 剛好在 timeout 邊緣完成、但回報刪除還在路上」留任何餘裕**——兩個 timeout 同時到期，SQS 在 Lambda 還沒來得及確認成功時就把訊息放出去重投，幾乎**保證**製造一次重複。正確設法：**SQS visibility timeout 應明顯大於 Lambda function timeout**（AWS 建議至少 6 倍 function timeout），給「Lambda 跑完 ＋ event source mapping 確認刪除」留出安全餘裕，讓「正常跑完」的訊息不會因為時序貼太近而被誤判重投。

(e) 收口到 ch10 的 **「at-least-once 交付 ＋ 冪等」安全帶**：SQS→Lambda 這條路徑**結構上**就是 at-least-once（逾時重投、非同步重試都會重），所以函式**必須冪等**——這跟 ch04 結算 consumer 必須冪等是同一個底層問題，只是把「長駐 consumer」換成了「Lambda」。換了執行載體，老問題一字不差地跟過來。

**推演三解答。**

- **(甲)** → **SNS → 三個 SQS 的 fan-out**。SNS 負責一對多扇出（推），三個 SQS 各給一個下游做持久緩衝（拉、按自己步調、不掉）。被放棄的：**純 SNS 直推三個 Lambda**——輸在沒有持久緩衝，下游一慢一掛那支的訊息語意弱、可能掉；**用一個 SQS**——輸在一則訊息被一個 consumer 撈走就不在了，扇不到三個下游（要自己複製三份，等於重造 SNS）。
- **(乙)** → **API Gateway（REST API ＋ usage plan）**。要 per-client 分級限流（usage plan/API key）＋ 閘道層 JWT 授權，這正是 API Gateway 的本職。被放棄的：**ALB**——輸在沒有原生限流（要搭 WAF）、沒有 usage plan、沒有 per-request 細粒度授權；**HTTP API**——輸在缺 usage plan／API key（分級限流做不了，landscape §18）。
- **(丙)** → **KrakenD（API aggregation）**。前端打一次、KrakenD 並行打三個後端合併回應，這是它的招牌。被放棄的：**讓前端打三次**——輸在前端複雜、三次往返延遲、三個失敗各自處理；**API Gateway**——它的轉換是 per-request 改寫，不是「並行多後端聚合成一個回應」，硬做很彆扭；**Kong**——能做但要裝 plugin、帶有狀態控制面，比 KrakenD 內建聚合重。

## 自我檢核

口頭自答，講得出來才算過關：

1. SQS Standard 和 FIFO 在**交付**和**排序**兩軸各是什麼答案？為什麼「FIFO 是 exactly-once」要加上「*processing*」這個字才精確？什麼時候才該選 FIFO（判準那一句）？
2. visibility timeout 的機制怎麼**直接製造**重複？為什麼 SQS → Lambda 場景裡「visibility timeout = Lambda timeout」是陷阱，該怎麼設？
3. SNS 和 SQS 的分工用「推 vs 拉」一句話講出來；為什麼「SNS → 多 SQS」能同時拿到兩者的長處？為什麼別拿 SNS 當佇列用？
4. 為什麼 Lambda 的「無狀態」是**前提**不是建議？把狀態放進 Lambda 記憶體會出什麼「有時對有時錯」的 bug？這對應全書哪一軸的極端形態？
5. SnapStart 支援哪些 runtime、**不**支援哪些？如果你的 Lambda 是 Node，降冷啟動還剩哪些手段？
6. ALB 和 API Gateway 的本職差在哪一句話？「該用 ALB 卻用了 API Gateway」會付出哪些代價？HTTP API 比 REST API 少了哪些東西、所以哪種需求不能用它？
7. KrakenD 的招牌能力是什麼？把它的治理講精確——**捐出去的是什麼、捐給誰、2025 公司被誰收**（三個點都別說錯）？它和 Kong 的哲學差別？
8. 把本章六個原語的共同主題講出來：「選一個原語＝吞下它替你做好的五軸決定、連同它甩回給你的那幾軸」——舉三個例子（哪個甩回交付、哪個甩回持久、哪個甩回治理）？

## 延伸閱讀

- **Amazon SQS — Message quotas**（[AWS docs](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html)）：單則上限、visibility timeout、保留期等硬數字的一手出處。搭配 [Amazon SQS increases maximum message payload size to 1 MiB](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib/)（2025-08-04）讀「256 KB → 1 MiB」這個老兵記憶校正的官方根據——注意它是 **2025-08** 才變的。
- **Amazon SNS — FIFO message delivery**（[AWS docs](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html)）：SNS FIFO 的排序與去重語意、能/不能直接投給哪些端點。搭配 [Introducing SNS FIFO](https://aws.amazon.com/blogs/aws/introducing-amazon-sns-fifo-first-in-first-out-pub-sub-messaging/) 理解「FIFO topic → FIFO 佇列」的有序扇出。
- **AWS Lambda — payload size increase to 1 MB**（[AWS what's new](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-lambda-payload-size-256-kb-1-mb-invocations/)）：非同步 payload 256 KB → 1 MB 的官方公告（2025-10-24，2026-06 查證）。讀它確認「sync 仍 6 MB、async 升 1 MB」這個易過時的數字。
- **AWS Lambda — Improving startup performance with SnapStart**（[AWS docs](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)）：SnapStart 支援的 runtime（Java/Python/.NET）與**不支援 Node.js** 的一手出處——對照本章冷啟動那段，別把 SnapStart 當 Node 的解。
- **API Gateway vs ALB**：讀 [Amazon API Gateway FAQs](https://aws.amazon.com/api-gateway/faqs/) 的 throttling/auth 段，與 [Throttle requests to your REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)（token bucket 限流、10,000 RPS 上限）——本章「per-request 治理 vs 純 L7 路由」分界的官方依據。
- **KrakenD — Open Source**（[krakend.io](https://www.krakend.io/open-source/)）與 **Lura Project**（[github.com/luraproject/lura](https://github.com/luraproject/lura)）：核心 framework「Lura」捐給 Linux Foundation（2021-05）的一手出處；搭配 [Linux Foundation 公告](https://www.linuxfoundation.org/press/press-release/open-source-api-gateway-krakend-becomes-linux-foundation-project) 讀「捐的是 framework、給的是 LF 不是 CNCF」這個治理精確點（landscape §16；2025-09 公司被 Shop Circle 收購）。
- 想把本章的交付語意接回源頭——**ch10（交付語意與冪等）**把「exactly-once 是幻覺、at-least-once + 冪等是安全帶」挖到形式化；SQS 在結算 pipeline 的實戰見 **ch04**；背壓與 retry storm 見 **ch14**；Lambda 冷啟動的「重啟失憶」對應 setTimeout 那課見 **ch09**。想把過載的**數學**（為什麼 ρ→1 會爆炸）挖穿，見《等待的數學：排隊理論》（queue）。

---

### 本章體檢：雲端原語 × 五軸並排表

這是全書脊椎在雲端原語上的兌現——把六個原語並排，一眼看完「誰保證不丟、誰可能重、誰重啟失憶、誰把哪一軸甩回給你」。

| 原語 | 交付 | 持久 | 分區 | 並發 | 觀測 |
|---|---|---|---|---|---|
| **SQS Standard** | 不丟、**會重**（at-least-once）→ 甩回冪等 | 訊息持久（≤14 天）、重啟不丟工作 | 跨區高可用、排序 best-effort | 多 consumer 並發常態、visibility 超時反製造重複 | 佇列深度/in-flight/DLQ/訊息齡皆 metric |
| **SQS FIFO** | exactly-once *processing*（5 分鐘去重窗）、嚴格排序 | 同 Standard | 嚴格排序（per group）、有吞吐上限 | 排序 → 同 group 串行 | 同 Standard ＋ dedup 指標 |
| **SNS** | 盡力推＋重試策略＋DLQ、語意弱於 SQS | topic 不存訊息 → 持久靠下游 | 跨區高可用、多訂閱者時序可不同 | 扇出即並發推送、各訂閱獨立 | 投遞成功/失敗數 → 端到端要自己接 |
| **Lambda** | sync 即時回、async 重試＋DLQ（at-least-once）→ 甩回冪等 | **重啟即失憶**（環境隨時回收）→ 甩回狀態外部化 | 無狀態、一致性問題在它讀寫的外部存儲 | 預設併發 **1,000**、超過 throttle → 甩回預留/退避 | invocation/error/duration/throttle/冷啟動 |
| **ALB** | L7 路由、不看 request body | 無狀態、自身不存資料 | 健康檢查移開故障後端、幾乎無吞吐上限 | 連線層負載均衡 | 路由/健康/延遲 metric、**無 per-request 治理觀測** |
| **API Gateway** | per-request 入口、有限流（REST ~10K RPS） | 無狀態託管 | 託管高可用、吞吐有上限 | token bucket 限流、usage plan per-client | 內建 access log/metric、per-client 配額可觀測 |

> 這張表是全書「五個故障問句」透鏡的雲端版收口：**沒有一個原語在五軸上全綠**——每一個都替你回答了某幾軸、又把另外幾軸甩回給你。看懂這張表，你就懂了本章唯一的主張：**它們不是可互換的積木，選一個原語就是吞下它的整組五軸取捨。** 全系統 × 五軸的總表見附錄 B。
