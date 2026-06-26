# A · 訊息工具對照

這個檔回答的不是「該選哪個訊息保證」（那是交付語意條目的事），而是「**市面上具體的訊息工具，各自把哪些保證做進預設、又把哪些坑留給你**」。本檔含六個條目：SQS、SNS、Kafka、RabbitMQ、Bull／BullMQ，以及一個比較條目「Redis Pub/Sub vs Streams」。它們共用同一條脊椎：每個工具都是一組「保證 ＋ 適用條件 ＋ 坑」的打包，你選工具就是在選你願意承擔哪一組坑。與相鄰領域的邊界一句話：**交付語意（at-least-once／exactly-once）、冪等、去重、順序、DLQ 等「機制」在交付語意與重複處理的條目深講，本檔只講「某個工具怎麼實作或不實作這些機制」**；Redis 自身的單執行緒內幕、持久化、io-threads 在領域 G 的「Redis」深講，本檔只比交付語意差異。

## SQS（Standard vs FIFO、visibility timeout）

### 是什麼與內部機制

Amazon SQS 是全託管的分散式訊息佇列：producer 呼叫 `SendMessage` 把訊息寫進佇列，consumer 用 `ReceiveMessage` 拉取（pull 模型，沒有 push），處理完呼叫 `DeleteMessage` 把訊息刪掉。關鍵機制是 **visibility timeout**：當一個 consumer 收到一則訊息，這則訊息不會立刻被刪，而是進入「in-flight」狀態、在 visibility timeout 這段時間內對其他 consumer 隱形。如果 consumer 在這段時間內 `DeleteMessage`，訊息消失；如果沒有（崩潰、處理超時），timeout 一到訊息重新變可見，另一個 consumer 會再拿到它——這正是 SQS「至少一次」的根源：刪除是主動的，沒成功刪就會重投。

SQS 有兩種佇列。**Standard**：近乎無限吞吐、at-least-once delivery、best-effort ordering（盡量但不保證順序，可能重排）。**FIFO**：strict ordering（同一 message group 內嚴格先進先出）、在 5 分鐘的 deduplication window 內提供 exactly-once processing（靠 deduplication ID 去重）。visibility timeout 預設 **30 秒**，範圍 **0 秒到 12 小時**；message retention 預設 4 天、可設 60 秒到 14 天（2026-06）。

### 在哪些系統扮演什麼角色

SQS 最典型的角色是**服務間的非同步解耦緩衝**：上游把工作丟進佇列就回，下游 worker 自己的步調拉取，上下游不必同時在線（時間解耦）。常見搭配是把它放在 SNS 後面當 fan-out 的落點（見 SNS），或當 Lambda 的事件來源（event source mapping）。FIFO 佇列則用在「順序不能亂、重複會出事」的場景，例如同一個帳戶的一連串狀態變更必須照序處理——用 message group ID 把同一帳戶的訊息綁進同一個有序群組，不同帳戶之間仍可並行。

### 保證與限制

保證：Standard 是 at-least-once ＋ best-effort ordering；FIFO 是 exactly-once processing（5 分鐘窗內）＋ strict ordering。兩者都支援 DLQ（超過 `maxReceiveCount` 的訊息轉進死信佇列）。

硬限制（必須記牢，會直接影響架構）：

- **單則訊息 payload 上限為 1 MiB（1,048,576 bytes）（2026-06）**。這是 2025-08-04 才從 256 KiB 提升上來的——在那之前是 256 KiB，所以許多既有系統與函式庫的假設仍停在 256 KiB（見下方陷阱）。超過 1 MiB 要用 Extended Client Library 把 payload 放 S3、訊息只帶指標，這條路最大可到 2 GB。
- FIFO 預設吞吐為**整條佇列共用**每 API action 每秒 300 則（非批次）／3,000 則（批次）；要靠 message group 粒度平行擴展，必須開 high throughput mode（`FifoThroughputLimit=perMessageGroupId`），開啟後每 message group／partition 各自 300／3,000，主要 region（us-east-1／us-west-2／eu-west-1）**非批次**即可達約 70,000 訊息/秒、含批次更高（2026-06）。
- 計費以每 64 KB 為一個請求單位計：一則 1 MiB 訊息算 16 個請求，不是一個。

**Worked example（payload 上限）**：假設一個系統把使用者上傳的結構化資料整包塞進 SQS 訊息，平均 700 KiB、尖峰偶爾 1.3 MiB。在 1 MiB 上限下，那批 1.3 MiB 的訊息會被 `SendMessage` 直接拒絕（拋 message-too-long）。若每天有 10 萬則訊息、其中 0.5% 超過 1 MiB，就是每天 500 則靜默失敗（如果沒檢查回傳）。正解是對所有 > 1 MiB 的 payload 走 S3 offload，而不是賭尖峰不發生。同時注意計費：700 KiB 的訊息算 `ceil(700/64) = 11` 個請求單位，10 萬則就是 110 萬個請求單位，不是 10 萬。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| SQS Standard | at-least-once、best-effort ordering | 一般非同步解耦、可容忍重複/重排的工作佇列 | 一定會遇到重複與亂序，consumer 必須冪等 |
| SQS FIFO | exactly-once processing（5 分鐘窗）、strict ordering | 同群組內順序敏感、重複會出錯 | 預設整佇列 300／3,000 TPS；按 message group 擴展須開 high throughput mode |
| Kafka（見 Kafka） | at-least-once，可開 EOS；保留期內可重放 | 高吞吐事件流、需要重放/多訂閱者 | 自運維（或付託管）、partition＝順序與並行單位 |
| RabbitMQ（見 RabbitMQ） | at-least-once（手動 ack）；豐富 routing | 複雜路由、低延遲任務分發 | 訊息預設消費即走、無內建長期保留/重放 |

跟 Kafka 的本質差異：SQS 是「訊息被消費刪除即消失」的佇列語意（沒有 replay、沒有「新訂閱者讀歷史」），Kafka 是「append-only log、保留期內可任意重讀」的日誌語意。要重放或多組互不影響的消費者讀同一份資料，SQS 做不到、要靠前面接 SNS 扇出多個佇列。

### 常見誤解與陷阱

- **把 256 KiB 當上限寫死**：很多既有程式、第三方 SDK 或 mental model 仍假設 256 KiB（這在 2025-08 之前是對的）。升級後若你的程式碼還在 250 KiB 處硬切分訊息，是在做沒必要的工。反過來，有些舊版 SDK／驗證邏輯尚未更新到 1 MiB，曾出現「server 接受 1 MiB 但 client 端 SDK 仍按 256 KiB 報錯」的案例——升限後請以一手 quotas 文件為準、並實測你的 SDK 版本。
- **以為 FIFO ＝ 訊息層 exactly-once delivery**：FIFO 給的是 exactly-once **processing**（5 分鐘去重窗內），不是物理上保證只投一次。窗外的重送、或下游處理本身的重複，仍要靠冪等兜底（見冪等與去重條目，本領域）。
- **visibility timeout 設太短**：若處理時間 > visibility timeout，訊息會在你還在處理時重新可見、被另一個 consumer 並行拿走，造成重複處理甚至 double-spend。長任務要嘛把 timeout 設足，要嘛在處理中呼叫 `ChangeMessageVisibility` 續租。
- **把 SQS 當廣播**：SQS 是點對點，一則訊息被一個 consumer 拿走刪掉就沒了。要一份訊息給多個下游，前面要接 SNS（見 SNS）。

### 延伸閱讀

- [Amazon SQS message quotas（官方 quotas，含 1 MiB 上限）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html)
- [Amazon SQS visibility timeout（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
- [Amazon SQS increases maximum message payload size to 1 MiB（2025-08 公告）](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib/)
- [FIFO queues exactly-once processing（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html)

## SNS（fan-out、SNS→SQS）

### 是什麼與內部機制

Amazon SNS 是全託管的 pub/sub 服務：producer 把訊息 `Publish` 到一個 **topic**，SNS 把同一則訊息推（push）給所有訂閱該 topic 的端點——這就是 **fan-out**（一發、多收）。訂閱端可以是 SQS 佇列、Lambda、HTTP(S) endpoint、email、SMS、行動推播等。它與 SQS 的根本差別是方向：SQS 是 consumer 主動拉、且一則訊息只給一個 consumer；SNS 是 SNS 主動推、且一則訊息複製給所有訂閱者。

SNS 有 Standard topic 與 FIFO topic 兩種。Standard topic：高吞吐、best-effort ordering、at-least-once。**FIFO topic**：strict ordering（同一 message group 內）＋ deduplication（5 分鐘窗，可用訊息內容 SHA-256 自動產生去重 ID）。

### 在哪些系統扮演什麼角色

SNS 的招牌角色是 **SNS→SQS fan-out**：一個事件（例如「訂單成立」）發到 SNS topic，扇出到多個 SQS 佇列，各佇列後面掛不同的下游服務（出貨、發票、通知各拉各的、互不影響）。這個組合是 AWS 官方推薦的標準解耦架構，因為它同時拿到 SNS 的扇出與 SQS 的緩衝/重試/DLQ。SNS 也常單獨用於通知（推播、簡訊、email）這類「發完即忘、不需緩衝」的場景。

### 保證與限制

保證：Standard topic 是 at-least-once delivery、best-effort ordering；FIFO topic 是 strict ordering ＋ deduplication。訂閱端不可用時，SNS 執行 delivery retry policy，並可搭配 DLQ 保存最終投遞失敗的訊息。

限制（FIFO topic 的投遞規則要記牢，2026-06）：**SNS FIFO topic 不能直接投遞給 email/SMS/HTTP(S)/行動推播/Lambda，只能投遞到 SQS 佇列**。它可以投到：

- **SQS FIFO 佇列** → 保留 strict ordering ＋ exactly-once（端到端有序、不重複）；
- **SQS Standard 佇列**（2023-09 起支援）→ **降級為 best-effort ordering ＋ at-least-once**，換取較低成本。

也就是說，端到端的順序保證能不能成立，取決於落點佇列的型別——FIFO topic 配 Standard queue，等於在最後一段把順序與去重保證丟掉了。

**Worked example（fan-out 計費直覺）**：一個 SNS topic 扇出到 4 個 SQS 佇列。發布 100 萬則訊息，SNS 端是 100 萬次 publish，但會產生 100 萬 × 4 ＝ 400 萬次對 SQS 的投遞。如果其中一個下游（例如通知服務）暫時掛掉，受影響的只有它那條佇列裡的積壓——其他三條照常流動，這正是「各佇列獨立緩衝」的價值。但別忽略：扇出數越多，下游請求數與費用就線性放大。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| SNS（fan-out） | at-least-once 推送給所有訂閱者 | 一個事件要給多個獨立下游 | 推模型、無緩衝；下游慢/掛要靠後面的 SQS 兜 |
| SNS→SQS | 扇出 ＋ 每條下游各自緩衝/重試/DLQ | 解耦多下游、要獨立重試與背壓 | FIFO topic 配 Standard queue 會降級有序保證 |
| Kafka（見 Kafka） | consumer group 天然多訂閱、可重放 | 同一份事件流多組消費者、要重放 | 自運維成本高；非「託管即用」 |
| EventBridge | 規則路由、schema registry、跨帳號 | 需要內容過濾/路由規則的事件匯流 | 與 SNS 重疊但偏「事件總線」、語意更重 |

SNS 與 Kafka 都能做「一發多收」，但 SNS 是推、無歷史、新訂閱者讀不到過去的訊息；Kafka 是拉、有保留期、新 consumer group 可從頭重放。要「重放歷史給新加入的消費者」選 Kafka；要「託管、零運維、即發即扇」選 SNS。

### 常見誤解與陷阱

- **以為 SNS 有緩衝**：SNS 是推、不是佇列，它本身不替你存著等下游。下游處理不過來或暫時掛掉，緩衝來自它後面的 SQS——直接訂閱 Lambda/HTTP 而沒接 SQS，遇到下游故障只能靠 SNS 的 retry policy ＋ DLQ，控制力遠不如 SQS。
- **以為 SNS FIFO 能直接給任何端點有序投遞**：它只能投到 SQS。想要端到端有序，必須 FIFO topic → FIFO queue，且整段都不可換成 Standard。
- **把 fan-out 當免費**：扇出 N 個訂閱者就是 N 倍下游請求量與費用，且任何一個下游的放大都會被乘上去。
- **混淆 SNS 與 SQS 的訊息歸屬**：SQS 一則訊息只一個 consumer 拿；SNS 一則訊息每個訂閱者各拿一份。把 SQS 當廣播、或把 SNS 當工作分發，都是用錯工具。

### 延伸閱讀

- [Amazon SNS message delivery for FIFO topics（官方，含可投遞端點限制）](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html)
- [Amazon SNS FIFO topics now support delivery to SQS Standard queues（2023-09 公告）](https://aws.amazon.com/about-aws/whats-new/2023/09/amazon-sns-fifo-topics-message-delivery-sqs-standard-queues/)
- [Introducing Amazon SNS FIFO（AWS Blog）](https://aws.amazon.com/blogs/aws/introducing-amazon-sns-fifo-first-in-first-out-pub-sub-messaging/)

## Kafka（log/partition/consumer group/EOS）

### 是什麼與內部機制

Apache Kafka 不是傳統佇列，而是一個**分散式、可持久化、可重放的 append-only commit log**。核心抽象：

- **Topic**：一個邏輯訊息流，切成多個 **partition**。
- **Partition**：append-only、嚴格有序的訊息序列，每則訊息有單調遞增的 offset。partition 是**順序與並行的最小單位**——順序只在單一 partition 內保證，跨 partition 不保證。producer 用 partition key 決定訊息落哪個 partition（同 key → 同 partition → 有序）。
- **Consumer group**：一組 consumer 共同消費一個 topic，Kafka 把 partition 分配給組內各 consumer，**一個 partition 在同一時刻只給組內一個 consumer**。不同 consumer group 彼此獨立、各自從頭或從某 offset 讀同一份 log（這就是「多訂閱者」與「重放」的來源）。
- **Offset commit**：consumer 自己記錄讀到哪（commit offset）。「消費」不刪訊息——訊息留在 log 直到 retention 過期。讀進度只是一個 offset 指標。

因為訊息不隨消費刪除、而是按 retention（時間或大小）保留，Kafka 天然支援 replay 與多組互不干擾的消費者——這是它與 SQS/RabbitMQ「消費即走」語意的根本分野。

### 在哪些系統扮演什麼角色

Kafka 的典型角色：高吞吐**事件流匯流排**（所有服務的事件往這裡寫、各下游各自訂閱）、**event sourcing 的存放層**（狀態＝不可變事件序列，log 天然契合，見 K 領域的 Event sourcing）、**串流處理的來源/落點**、以及 **CDC 的傳輸層**（資料庫變更 → Kafka → 下游同步，見 L 領域）。當需求是「一份事件流、很多消費者、還要能重放歷史」，Kafka 幾乎是預設選擇。

### 保證與限制

預設保證是 **at-least-once**：producer 重試可能造成重複、consumer 在 commit offset 前崩潰會重讀。順序只在 partition 內保證。

**Kafka EOS（exactly-once semantics）成立的條件與限制（2026-06，務必精確）**：Kafka 能在「Kafka 內部」達到 exactly-once，但它是三個機制疊起來的，缺一不可：

1. **冪等 producer**（`enable.idempotence=true`，新版預設開）：broker 給每個 producer 一個 PID ＋ 每則訊息一個 sequence number，重試造成的重複在 broker 端被去掉。這只解決「單一 producer session、單一 partition」的重複。
2. **交易（transactional producer）**：跨多個 partition／topic 的寫入原子化（兩階段提交式），並把「寫資料 ＋ commit consumer offset」綁進同一個交易，達成 read-process-write 的原子性。要設 `transactional.id` 並用 `beginTransaction`/`commitTransaction`。
3. **consumer 設 `isolation.level=read_committed`**：consumer 只讀到已 commit 交易的訊息，跳過 aborted 交易的訊息；只讀到 offset 低於 LSO（last stable offset）的訊息。

**關鍵限制**：Kafka 的 EOS 是「**Kafka-to-Kafka**」的——它保證「從 Kafka 讀、處理、寫回 Kafka」這條鏈路 exactly-once。一旦你的處理有**外部副作用**（寫第三方資料庫、呼叫外部 API、發 email），那個外部系統不在 Kafka 交易裡，EOS **不延伸到它**——對外部系統仍要靠冪等寫入或 outbox 模式（見 outbox/saga 條目，本領域）來兜。把 Kafka EOS 當成「整條業務鏈端到端只執行一次」是最常見的誤判。

**Worked example（重複數量直覺）**：用預設 at-least-once、broker 重投率約 0.1%，每天流經 1,000 萬則訊息，下游約有 `10,000,000 × 0.001 = 10,000` 筆重複要靠冪等吸收。若改開 EOS（Kafka 內部鏈路），這 1 萬筆在 Kafka↔Kafka 段被消掉，但若下游同時還在寫一個外部 PostgreSQL，那段仍需自己的冪等鍵——EOS 沒幫你保證那一步。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Kafka | at-least-once（可開 Kafka 內 EOS）；保留期內可重放、多 consumer group | 高吞吐事件流、event sourcing、需重放/多訂閱 | 自運維重；EOS 不含外部副作用；partition＝順序與並行單位 |
| SQS（見 SQS） | at-least-once / FIFO exactly-once processing | 託管即用的解耦佇列 | 無 replay、無「多組讀同份」、無長期保留 |
| RabbitMQ（見 RabbitMQ） | at-least-once（手動 ack）、豐富 routing | 複雜路由、低延遲任務分發 | 非日誌語意、無原生長期保留/重放 |
| Pulsar | 類 Kafka log ＋ 內建分層儲存、多租戶 | 需要 segment/storage 分離、地理複製 | 生態與人才池小於 Kafka |

選擇判準：要「重放 ＋ 多組獨立消費 ＋ 超高吞吐」→ Kafka；只要「託管解耦佇列、不重放」→ SQS；要「靈活 routing、低延遲、訊息量中等」→ RabbitMQ。

### 常見誤解與陷阱

- **以為開了 EOS 就整條業務 exactly-once**：EOS 是 Kafka-to-Kafka。外部資料庫/API 的副作用不在交易裡，仍要冪等。這是本條最重要的一句。
- **以為 Kafka 全域有序**：順序只在 partition 內。要讓某類訊息有序，必須用同一個 partition key 把它們綁進同一個 partition——代價是該 key 的吞吐被單一 partition 上限。
- **partition 數設太低或太高**：partition 數是並行度上限（consumer group 內並行消費者數 ≤ partition 數）。設太低限制吞吐；設太高增加 metadata/rebalance 負擔，且 partition 數通常只能加不能減。
- **把 commit offset 當「處理完成」**：若在處理完成前就自動 commit offset，崩潰會造成訊息遺失（變成 at-most-once）；若處理完才 commit，崩潰造成重讀（at-least-once）。語意取決於 commit 時機，不是預設就對。

### 延伸閱讀

- [Kafka Documentation: Design / Message Delivery Semantics（官方）](https://kafka.apache.org/documentation/#semantics)
- [Confluent: Transactions and Exactly-Once Semantics（官方課程）](https://developer.confluent.io/courses/architecture/transactions/)
- [Exactly-once semantics with Kafka transactions（Strimzi blog）](https://strimzi.io/blog/2023/05/03/kafka-transactions/)

## RabbitMQ（exchange/routing/ack/confirms）

### 是什麼與內部機制

RabbitMQ 是基於 AMQP 的訊息 broker，核心模型把「發布」與「投遞」用一層 routing 解耦：producer 不直接寫佇列，而是把訊息發到 **exchange**，exchange 依照 **binding** 與 **routing key** 把訊息路由到一個或多個 **queue**，consumer 從 queue 取訊息。四種 exchange 決定路由邏輯（2026-06）：

- **direct**：routing key 完全相符才投（點對點/按類型）。
- **topic**：routing key 做萬用字元比對（`*` 一段、`#` 多段），用於主題訂閱。
- **fanout**：忽略 routing key，廣播到所有綁定的 queue（扇出）。
- **headers**：依訊息 header 而非 routing key 比對。

可靠性靠兩個**正交且互不相關**的機制（官方明確說兩者彼此無感知）：

- **consumer acknowledgements（ack）**：consumer 處理完呼叫 `basic.ack`，broker 才把訊息標記可刪。手動 ack 模式下，consumer 在 ack 前崩潰，訊息會 requeue 給別人——這是 RabbitMQ 的 at-least-once 來源。自動 ack（auto-ack）則一投遞就視為完成，崩潰即遺失（at-most-once，效能高但危險）。
- **publisher confirms**：broker 收到並安置好訊息後回 `basic.ack` 給 producer，讓 producer 知道訊息沒在「producer → broker」這段掉。它只覆蓋發布端與所連節點/queue leader 之間，與 consumer ack 無關。

### 在哪些系統扮演什麼角色

RabbitMQ 的典型角色是**任務分發與工作佇列**（把耗時工作丟給一群 worker，competing consumers 各搶各的）、**需要靈活路由的事件分送**（用 topic exchange 做主題訂閱、用 fanout 做廣播），以及**請求/回覆式的非同步整合**。它的強項是 routing 表達力與低延遲；弱項是它本質是「消費即走」的 broker，沒有 Kafka 那種長期保留與任意重放（雖然有 Streams 外掛補強，但不是預設心智模型）。

### 保證與限制

保證：手動 ack ＋ 持久化 queue ＋ 持久化訊息 ＋ publisher confirms，能達 at-least-once（producer 端確認沒掉、consumer 端確認處理完才刪）。

限制與條件：

- **at-least-once 不是免費的**：要同時做到「queue 宣告 durable」「訊息標 persistent」「consumer 手動 ack」「producer 開 publisher confirms」，少一環就有對應的遺失或重複窗口。auto-ack ＋ 非持久化＝高吞吐但隨時可能掉訊息。
- **沒有原生 exactly-once**：requeue 機制本身會造成重複，下游要冪等。
- **publisher confirms 的吞吐取捨**：逐則同步等 confirm 會嚴重拖慢吞吐；實務上批次發布、每 50–100 則等一次 confirm，在安全與吞吐間取平衡。

**Worked example（confirm 批次的吞吐差異）**：假設單則往返 confirm 的網路 RTT 是 1 ms。若逐則同步等 confirm，理論上限約 1,000 則/秒（被 RTT 卡死）。若改成批次：一次送 100 則、只等一次 confirm，同樣 1 ms RTT 下吞吐可拉高約兩個數量級（受限轉為 broker 處理能力而非 RTT）。代價是：一個 batch 內若有訊息沒被 confirm，你只知道「這批有問題」、要整批重送或逐則重查——安全性換吞吐的具體取捨就在這裡。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| RabbitMQ | at-least-once（手動 ack ＋ confirms ＋ 持久化）；豐富 routing | 任務分發、靈活路由、低延遲、量中等 | 消費即走、無原生重放；可靠性需手動湊齊四環 |
| Kafka（見 Kafka） | at-least-once，可開 EOS；可重放、多 consumer group | 高吞吐事件流、event sourcing | routing 表達力弱於 RabbitMQ（靠 partition key/topic 設計） |
| SQS（見 SQS） | at-least-once / FIFO exactly-once processing | 託管零運維解耦佇列 | routing 極簡（無 exchange 概念）、要扇出靠 SNS |
| Redis Streams（見 Redis Pub/Sub vs Streams） | at-least-once（consumer group ＋ XACK） | 輕量持久化流、已有 Redis | 持久化/可靠性弱於上述專用 broker |

判準：需要複雜 routing（topic/header 比對）、低延遲任務分發 → RabbitMQ；需要重放與超高吞吐 → Kafka；要託管免運維 → SQS；只是已有 Redis、想要輕量持久化流 → Redis Streams。

### 常見誤解與陷阱

- **把 publisher confirms 當成 end-to-end 保證**：confirm 只證明「producer → broker」沒掉，不證明 consumer 處理成功。端到端要 confirm（前段）＋ consumer 手動 ack（後段）兩者都做。
- **用 auto-ack 還以為可靠**：auto-ack 在訊息投遞瞬間就視為完成，consumer 崩潰＝訊息已從 queue 消失、無法 requeue。要可靠就得手動 ack。
- **忘了標 durable/persistent**：queue 沒宣告 durable、訊息沒標 persistent，broker 重啟就清空——「我有 ack 機制」救不了沒持久化的訊息。
- **把 RabbitMQ 當 Kafka 用（要重放）**：預設語意是消費即走、無歷史。需要重放或多組互不影響地讀同一份歷史，這不是 RabbitMQ 的設計甜蜜點。

### 延伸閱讀

- [Consumer Acknowledgements and Publisher Confirms（官方）](https://www.rabbitmq.com/docs/confirms)
- [RabbitMQ Tutorials（含各 exchange 類型）](https://www.rabbitmq.com/tutorials)
- [AMQP 0-9-1 Model Explained（官方）](https://www.rabbitmq.com/tutorials/amqp-concepts)

## Bull / BullMQ（Redis-backed delayed/job queue）

### 是什麼與內部機制

Bull／BullMQ 是 Node.js 的**以 Redis 為後端的 job queue**：不是獨立的 broker 進程，而是一個函式庫，用 Redis 的資料結構（list、sorted set、hash、加上以 Lua 腳本保證原子性的操作）把「工作」存進 Redis，由 worker 進程拉取執行。它和 SQS/Kafka 那種「訊息傳遞」不同，定位是 **background job processing**：你 `add` 一個 job（帶 payload、選項），worker `process` 它，框架管狀態流轉（waiting → active → completed/failed）、重試、延遲、優先序、可重複排程（repeatable/cron-like）、rate limiting、流程編排（flows）。

延遲投遞靠 Redis 的 sorted set：把「該執行時間」當 score，到時間才從 delayed 集合移到 waiting。原子性靠 Lua：例如「從 waiting 取一個 job 並移到 active 並設 lock」必須是不可分割的單一操作，否則兩個 worker 會搶到同一個 job。

**版本與維護狀態（2026-06，務必精確）**：原始的 **Bull（OptimalBits）已進入 legacy/maintenance 模式**（只收 bug fix、不加新功能）；**現役後繼者是 BullMQ**，以 TypeScript 重寫，由 **Taskforce.sh 維護**（持續活躍更新，2026-06 仍為 v5.x 系列）。**新專案應選 BullMQ**。注意：BullMQ 由 Taskforce.sh 維護，**不是 Redis 官方／Redis Ltd. 的產品**（沒有 Redis 收購 BullMQ 的證據）——Taskforce.sh 是 BullMQ 與 Bull 背後的團隊與商用 dashboard 提供者。BullMQ 相對 Bull 有破壞性 API 變更（Queue/Worker 拆分、獨立的 QueueEvents 類別、不再允許整數 job ID 等）。

### 在哪些系統扮演什麼角色

典型角色：Node.js 應用裡的**非同步背景工作**——寄信、產報表、影像/檔案處理、webhook 重送、排程性任務（用 repeatable jobs 取代外部 cron）。它的甜蜜點是「已經有 Redis、想要帶延遲/重試/優先序/排程的工作佇列、又不想多養一個 SQS/RabbitMQ」。它常被放在 web 請求路徑外：HTTP handler 只 `add` job 就回應，重活交給 worker 池。

### 保證與限制

保證：at-least-once 處理——job 被 worker 取走時上 lock，處理完才標 completed；worker 崩潰、lock 到期後 job 被視為 stalled、會被重新拉起處理（所以可能重複）。內建重試（含 backoff）、延遲、優先序、並發控制、rate limiting。

硬限制：

- **可靠性的天花板是 Redis 的持久化**。Redis 預設 AOF/RDB 設定下，崩潰可能丟失最近一小段未落盤的資料（見領域 G 的 Redis 持久化）——也就是說，job 佇列的耐久性等於你 Redis 的耐久性，不會更高。要求金融級不丟，Redis-backed queue 不是首選。
- **沒有 exactly-once**：stalled job 重拉就是重複來源，handler 必須冪等。
- **規模受單一 Redis（或 cluster）限制**，吞吐與資料量綁在 Redis 的記憶體與單執行緒執行模型上（見領域 G）。

**Worked example（stalled 重複數量）**：假設一個 worker 池處理 100 萬個 job，平均處理 2 秒，部署/OOM 造成約 0.05% 的 job 在處理中途 worker 被殺。這些 job 的 lock 到期後會被當 stalled 重新處理：`1,000,000 × 0.0005 = 500` 個 job 會被執行第二次。如果其中是「扣款」「寄信」這類有副作用的工作而 handler 不冪等，就是 500 次重複扣款/重複寄信——所以 Redis-backed queue 的 handler 必須帶冪等鍵（見冪等條目，本領域）。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| BullMQ（Redis-backed） | at-least-once；內建延遲/重試/優先序/排程 | Node.js 背景工作、已有 Redis、要延遲/cron-like | 耐久性 = Redis 耐久性；stalled 重複；單 Redis 規模限制 |
| Bull（legacy） | 同上但只收 bugfix | 既有專案維持現狀 | 新專案勿選；遷 BullMQ 有破壞性 API 變更 |
| SQS（見 SQS） | at-least-once / FIFO；託管耐久 | 跨語言、要託管耐久與大規模 | 無內建 job 狀態機/優先序/cron，要自己組 |
| Sidekiq（Ruby）/ Celery（Python） | at-least-once（多 backend） | 對應語言生態的背景工作 | 與 BullMQ 同類、語言綁定不同 |

判準：Node.js ＋ 已有 Redis ＋ 要延遲/重試/排程而非跨語言耐久傳遞 → BullMQ；要託管、跨語言、更高耐久 → SQS；其他語言生態 → Sidekiq/Celery 等對應物。

### 常見誤解與陷阱

- **履歷/文件仍寫「Bull」**：Bull 已是 legacy（只收 bug fix）。現役是 BullMQ，新專案用它（2026-06）。把 Bull 當「現在要採用的選擇」是過時資訊。
- **以為 BullMQ 屬於 Redis 官方**：它由 Taskforce.sh 維護，不是 Redis Ltd. 產品。它「用 Redis 當後端」不等於「是 Redis 的東西」。
- **把它的耐久性想得比 Redis 高**：job 佇列不會比底層 Redis 更可靠。Redis 沒設好持久化，崩潰就會丟 job——這不是 BullMQ 的 bug，是它後端的本質。
- **handler 不冪等**：at-least-once ＋ stalled 重拉 ＝ 一定會有重複執行。有副作用的 job handler 必須冪等，這是用任何 at-least-once 工作佇列的前提。

### 延伸閱讀

- [BullMQ GitHub（Taskforce.sh 維護）](https://github.com/taskforcesh/bullmq)
- [Bull GitHub（OptimalBits，legacy）](https://github.com/OptimalBits/bull)
- [BullMQ Documentation](https://docs.bullmq.io/)

## Redis Pub/Sub vs Streams

### 定義與原理

Redis 提供兩種「把訊息從發布者送到消費者」的機制，交付語意天差地別，選錯會在「訊息可不可以掉」這件事上踩坑。本條只比**交付語意**；Redis 自身的單執行緒執行、io-threads、持久化（RDB/AOF）等內部機制在領域 G 的「Redis」深講（見 Redis，領域 G）。

- **Pub/Sub**：`PUBLISH` / `SUBSCRIBE`，**fire-and-forget、at-most-once、無持久化**。訊息只送給「發布當下正連線且已訂閱」的 subscriber。離線的、或在訊息發出後才訂閱的，**永久錯過**——沒有 replay、沒有歷史、沒有消費進度追蹤。它是純廣播管道，訊息發完不留痕。
- **Streams**：`XADD` 寫入一個 **append-only log**（持久化於 Redis 資料結構，受 RDB/AOF 保護），每則訊息有單調遞增的 ID。消費可用 `XREAD`（無消費進度、自己記 ID），或用 **consumer group**（`XREADGROUP`）達 **at-least-once**：每則被讀走的訊息進入 **PEL（Pending Entries List）**，消費者處理完必須 `XACK` 明確確認；沒 ack 的訊息留在 PEL，消費者崩潰後可重讀、或用 `XCLAIM`/`XAUTOCLAIM` 被別的消費者接手。語意上 Streams 像「Redis 內的迷你 Kafka」。

第一原理差異：Pub/Sub 把訊息當「當下的事件信號」（沒人聽就沒了）；Streams 把訊息當「持久化的記錄」（保留、可重讀、要確認）。

### 解法空間

當需求是「Redis 內把訊息傳給消費者」，可走的路：

- **Pub/Sub（普通）**：一發、所有當下訂閱者收、不留。適合「即時但可丟」的廣播。
- **Sharded Pub/Sub**（Redis 7.0+）：把 channel 依 slot 分片，解決 cluster 模式下 Pub/Sub 訊息要在所有節點間擴散的擴展瓶頸——語意仍是 at-most-once，只是擴展性改善。
- **Streams ＋ `XREAD`**：持久化 log、自己管讀到哪、無 ack；適合「要歷史但消費者自己管進度」。
- **Streams ＋ consumer group（`XREADGROUP` ＋ `XACK`）**：at-least-once、多消費者分攤、PEL 追未確認、可重認領；適合「不能掉、要重試、要多 worker 分攤」。
- **Keyspace notifications**：Redis 把 key 變更事件透過 Pub/Sub 推出來——但底層是 Pub/Sub，因此一樣 at-most-once、會漏，不能當可靠事件源。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Pub/Sub | at-most-once、無持久化、無 replay | 即時廣播、可容忍丟失（線上狀態、即時通知扇出） | 離線/晚訂閱者永久漏訊；不可當可靠事件源 |
| Sharded Pub/Sub（7.0+） | at-most-once，但 cluster 下可擴展 | cluster 模式高扇出廣播 | 語意不變，仍會丟；只是解擴展瓶頸 |
| Streams ＋ XREAD | 持久化、可重讀，但無內建 ack/分攤 | 單消費者、要歷史、自管進度 | 沒 consumer group 就沒 at-least-once 的重認領機制 |
| Streams ＋ consumer group | at-least-once、PEL 追蹤、可重認領 | 不能掉、要重試、多 worker 分攤 | 需 XACK；不 ack 的留 PEL，要監控 PEL 積壓；可能重複（要冪等） |

核心取捨一句話：**Pub/Sub 用「會丟」換「零狀態、最低延遲、最簡單」；Streams（consumer group）用「要管 PEL、要 ack、可能重複」換「不丟、可重放、多消費者」**。

### 何時需要

- **選 Pub/Sub**：訊息是「現在這一刻的事件信號」，丟了無所謂或可從別處補（例如把快取失效信號廣播給所有節點、即時狀態更新、Socket.IO 跨節點 fan-out 的 backplane）。沒人在線聽 ＝ 那一刻沒人需要，這正是可接受的語意。
- **選 Streams（consumer group）**：訊息代表「必須被處理至少一次的工作或事件」，消費者可能離線、崩潰、要重試，或要多個 worker 分攤同一條流。需要 at-least-once、需要重放、需要追蹤誰處理到哪——這些都是 Pub/Sub 給不了的。
- **Over-engineering 警訊**：若訊息可丟、消費者永遠在線、又不需要歷史，硬上 Streams ＋ consumer group ＋ PEL 監控，是替「不會發生的丟失」付管理成本。反過來，把「不能掉的工作」放 Pub/Sub，是在賭消費者永不離線——這個賭遲早輸。

### 常見誤解與陷阱

- **以為 Pub/Sub 可靠**：它是 at-most-once。subscriber 一旦斷線重連，斷線期間的訊息**永久消失、無法補**。把訂單、扣款、不可丟的事件放 Pub/Sub 是經典誤用。
- **以為 Streams ＝ exactly-once**：Streams consumer group 是 at-least-once。`XACK` 之前消費者崩潰、訊息被 `XCLAIM` 重認領，會被處理第二次——消費端仍要冪等（見冪等條目，本領域）。
- **不監控 PEL**：消費者讀了卻一直不 `XACK`（卡死、bug），訊息堆在 PEL 不會自己消失、也不會被自動重投給別人，除非你主動 `XAUTOCLAIM`。PEL 積壓是 Streams 的隱形背壓，要監控。
- **用 Streams 卻不設 maxlen**：`XADD` 預設不自動修剪，log 會無上限增長吃光記憶體。要用 `XADD ... MAXLEN ~ N`（近似修剪）或定期 `XTRIM` 控制長度。
- **把 keyspace notifications 當可靠事件源**：它底層是 Pub/Sub，一樣會漏。要可靠捕捉資料變更應走 CDC 或 Streams（見 CDC，領域 L）。

**Worked example（漏訊量直覺）**：用 Pub/Sub 廣播即時更新，平均每秒 200 則。某個 subscriber 因部署滾動更新斷線 8 秒。Pub/Sub 下，這 8 × 200 ＝ 1,600 則在斷線期間發出的訊息對它**全部永久遺失**，重連後只收得到「重連之後」的新訊息。同樣場景若用 Streams ＋ consumer group，這 1,600 則仍在 log 裡，消費者重連後從上次 ack 的 ID 之後繼續讀、一則不漏——這就是兩者語意差異的直接後果。

### 延伸閱讀

- [Redis Pub/Sub（官方）](https://redis.io/docs/latest/develop/interact/pubsub/)
- [Redis Streams intro（官方）](https://redis.io/docs/latest/develop/data-types/streams/)
- [XREADGROUP command reference（官方，consumer group 語意）](https://redis.io/docs/latest/commands/xreadgroup/)
