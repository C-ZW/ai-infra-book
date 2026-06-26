# A · 順序、重試與跨服務交付

訊息系統把「送到」這件事拆成許多保證：訊息該不該照順序到、送不到時怎麼重投、重投太多次怎麼隔離、跨多個服務怎麼讓一筆業務要嘛全成要嘛可補償、對外的回呼怎麼確認真的是對方送的。本檔收六條：訊息順序、重試／退避／jitter、DLQ 死信、outbox／saga、webhooks、序列化與 schema 演進。邊界上：交付語意三選一與冪等／去重的定義在本領域的交付篇深講（見 交付語意三選一，領域 A；見 冪等 idempotency，領域 A），本檔只引用不重述；retry storm 的放大機制在領域 E、timeout／budget 在領域 P；資料庫結構變更（加欄位、改型別）在 零停機 schema 遷移（領域 B），本檔的「序列化與 schema 演進」只管線上協定（wire）相容，兩者互引。

## 訊息順序 ordering（FIFO / partition key）

### 定義與原理

訊息順序保證的是：consumer 看到的訊息次序，與某個「應該的次序」一致。但「應該的次序」幾乎從不是「全域所有訊息的單一總序」——那要全系統序列化，吞吐立刻塌掉。實務上要的是**每個鍵（key）內的順序**：同一個帳戶的扣款照發生順序、同一個訂單的狀態轉移照轉移順序，而不同帳戶之間誰先誰後無所謂。

第一原理只有一條：**順序只能在「單一序列化點」上保證**。一個 partition、一條 log、一個 FIFO message group，本質都是一條被單執行緒化的尾巴，append 有先後、讀也有先後。一旦同一個鍵的訊息散落到多個 partition、或被多個 consumer 並行處理，順序就沒了。所以「保 partition 內順序」與「用 partition 換並行度」是同一枚硬幣的兩面：partition 越多越能並行，但跨 partition 無序。

### 解法空間

- **partition key（雜湊分流）**：對業務鍵（如 `account_id`）取雜湊決定 partition，同鍵恆入同一 partition，於是同鍵有序、跨鍵並行。Kafka、SQS FIFO 的 message group ID、Kinesis 的 partition key 都是這套。
- **單 partition / 單佇列**：整個 topic 只有一個 partition，全域有序——但吞吐被一條尾巴鎖死，只適合低速控制流。
- **consumer 端維持單執行緒 per key**：broker 不保證順序，但 consumer 按 key 路由到同一個工作執行緒序列化處理（如以 key 為鎖）。把順序責任搬到應用層。
- **sequence number + 重排**：訊息帶單調遞增序號，亂序到達時 consumer 緩衝、依序號重排後再交付。容忍亂序傳輸、代價是緩衝與 gap 等待。
- **版本／時間戳，放棄順序改用 LWW**：不保證順序，靠每筆帶版本，收到舊版本就丟（last-write-wins）。不是順序保證，是「無序也能收斂」的替代設計（見 衝突解決，領域 L）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| partition key 雜湊 | 同 key 內 FIFO；跨 key 無序 | 高吞吐、天然可分鍵的事件流 | key 傾斜（hot key）讓單 partition 過載；partition 數一旦上線難縮 |
| 單 partition / 單佇列 | 全域 FIFO | 低速控制平面、審計 log | 吞吐被單序列化點鎖死，無法水平擴展 |
| consumer 端 per-key 序列化 | 應用層保同 key 有序 | broker 不保證順序時補救 | 需自管 key→worker 路由與背壓；crash 後 in-flight 順序要復原 |
| sequence number + 重排 | 重排後依序交付 | 多路徑傳輸、容忍亂序 | 緩衝佔記憶體；缺號要等或補洞，等多久是個策略決定 |

Kafka 的細節值得記住：要在**有重試的前提下**仍保 partition 內順序，必須開啟 idempotent producer（`enable.idempotence=true`，broker 用 producer ID + per-partition 序號偵測並重排），此時 `max.in.flight.requests.per.connection` 最高可設到 5 仍保序；若關閉 idempotence 又把 in-flight 設大於 1，重試會讓批次亂序——第一批失敗重送、第二批已成功，第二批的記錄可能排到前面（2026-06，來源見延伸閱讀）。SQS FIFO 則用 message group ID 當序列化單位：同 group 嚴格有序，不同 group 可並行消費（見 SQS，領域 A）。

### 何時需要

要嚴格順序的，是**狀態機式的因果鏈**：餘額類（先存後扣 vs 先扣後存結果不同）、訂單狀態轉移（created→paid→shipped 不能倒）、CDC 套用（見 CDC，領域 L，套用順序錯了資料就花）。

不需要的，比想像多：彼此獨立的通知、可交換的聚合（計數、求和，加法可交換）、最終以版本收斂的同步（LWW）。對這些硬上全域順序，是拿吞吐換一個用不到的保證——典型的 over-engineering。判準很簡單：**問「這兩則訊息交換次序，結果會不會不同？」不會，就不需要它們之間有序。**

### 常見誤解與陷阱

- **以為「FIFO 佇列」＝全域有序**。FIFO 通常是「每個 group / 每個 partition 內有序」，跨 group 無序。把不同業務鍵塞進同一 group 只會白白損失並行度。
- **partition key 選錯造成熱點**。用 `country` 當 key，流量全壓在少數熱門國家的 partition；該用更細的鍵（如 user／order）才分得開。
- **多 consumer 並行就破壞順序**。即使 broker 保 partition 有序，consumer group 內一個 partition 同時只該由一個 consumer 處理；自己起多執行緒並行消費同一 partition，順序立刻沒了。
- **把「順序」和「exactly-once」混為一談**。有序不代表不重複；重投仍可能來同一則（見 交付語意三選一，領域 A）。順序解決「次序」，去重解決「重複」，是兩個正交問題。
- **重排緩衝的缺號永遠不來**。等一個永遠不會到的序號會卡死整條；要有 gap timeout 與「跳過並告警」策略。

### 延伸閱讀

- Apache Kafka, "Producer Configs"（`enable.idempotence`、`max.in.flight.requests.per.connection`、ordering）：https://kafka.apache.org/documentation/#producerconfigs
- KIP-185: Make exactly once in order delivery per partition the default producer setting：https://cwiki.apache.org/confluence/display/KAFKA/KIP-185
- Aiven, "Does Apache Kafka really preserve message ordering?"：https://aiven.io/blog/kafka-real-ordering
- AWS, "Amazon SQS FIFO queues"（message group ID 與排序）：https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues.html

## 重試、退避、jitter

### 定義與原理

重試是對抗**暫時性失敗**的基本手段：網路抖一下、對端剛好在 GC、限流回了 429——這些再試一次就好。但重試本身是把雙面刃：盲目立刻重試，會在對端最虛弱的時候追加負載，把「暫時性失敗」推成「持續性失敗」。退避（backoff）讓每次重試間隔拉長，jitter（隨機抖動）讓多個 client 的重試時刻錯開。

第一原理：**重試前要先回答兩個問題**——(1) 這個操作可不可以重試（冪等嗎？非冪等的重試可能重複扣款，見 冪等 idempotency，領域 A）；(2) 這個錯誤值不值得重試（4xx 多半是請求本身錯，重試還是錯；5xx／逾時／429 才是暫時性）。退避與 jitter 是「值得重試」之後的事，不是免死金牌。

### 解法空間

- **固定間隔（fixed delay）**：每次都等同樣秒數。簡單，但 N 個 client 同時失敗會同時重試，形成同步尖峰。
- **指數退避（exponential backoff）**：`delay = base × 2^attempt`，間隔翻倍成長。讓壓力隨重試次數快速衰減。
- **指數退避 + full jitter**：`delay = random(0, min(cap, base × 2^attempt))`。AWS 的建議做法——在整個退避窗內均勻取樣，把同步尖峰攤成穩定細流。
- **equal jitter**：保留一半固定退避、另一半隨機，避免取到太短的 sleep。
- **decorrelated jitter**：`delay = min(cap, random(base, prev × 3))`，下次上界跟著上次的實際值走，收斂與分散兼顧。
- **配套防線**：最大重試次數（retry budget）、總時間上限（deadline，見 timeout / deadline / budget，領域 P）、區分可重試錯誤碼、尊重 `Retry-After` 標頭。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| 固定間隔 | 實作最簡 | 單一 client、低並發 | 多 client 同步尖峰；對過載對端最毒 |
| 指數退避（無 jitter） | 壓力隨次數衰減 | 重試方很少、不會撞車 | 多 client 仍同步——大家同一個 `2^n` 時刻一起回來 |
| 指數退避 + full jitter | 衰減 + 攤平尖峰 | 大量 client、雲端 SDK 預設 | 偶爾取到很短 sleep；要配 cap 與最大次數 |
| equal jitter | 攤平但不會太短 | 不想要極短間隔時 | 分散度略低於 full jitter |
| decorrelated jitter | 攤平且自適應 | 長尾退避、想更快爬出谷底 | 上界會增長，要 cap 住避免爆炸 |

**Worked example（為什麼一定要 jitter）**：假設一個下游服務瞬斷，1,000 個 client 在同一毫秒收到逾時。用「指數退避無 jitter，base=1s」，所有人都在第 1 秒、第 2 秒、第 4 秒整齊重試——下游每到那個時刻就被 1,000 個請求同時砸，根本爬不起來。換成 full jitter、cap=20s，第一次重試的延遲在 0～1s 間均勻分布，平均約 500 個 client 落在前半秒、其餘攤到後半秒，下游看到的是「每毫秒約 1～2 個」的細流而非「某一刻 1,000 個」的尖峰。同樣的重試總量，存活與否取決於是否攤平。這個正回饋一旦失控就是 metastable failure（見 retry storm · metastable failure，領域 E）。

### 何時需要

需要：跨網路的 RPC／HTTP 呼叫、對佇列的投遞、對外部 API 的整合——任何「對端是別人、可能暫時不可用」的邊界。配 jitter 的必要性與**並發 client 數**成正比：client 越多，同步尖峰越致命。

不需要 / 要收斂的：本地純函數、明確的 4xx 客戶端錯誤（重試只是重複犯錯）、非冪等且沒有冪等鍵保護的寫入（重試＝重複副作用）。還有一種反模式是**多層各自重試**：gateway 重 3 次、service 重 3 次、client 重 3 次，乘起來是 27 倍放大——重試應該集中在某一層，並用全域 deadline 收口（見 timeout / deadline / budget，領域 P）。

### 常見誤解與陷阱

- **退避有了就不會雪崩**。退避只攤平單一 client 的時間軸；跨 client 的同步尖峰要靠 jitter 才打散。沒 jitter 的指數退避照樣 thundering herd。
- **無腦重試非冪等操作**。沒有冪等鍵保護就重試 POST，可能重複建單、重複扣款。先做冪等，再談重試。
- **沒有總上限**。只設「最多重 5 次」不夠；5 次指數退避可能累積到分鐘級，早超過上游的 deadline。要有牆鐘總預算。
- **忽略 `Retry-After` 與 429 語意**。對端已經明說「等 N 秒」，自己的退避演算法不該蓋過它。
- **重試放大藏在依賴鏈裡**。每一層都「貼心地」加了重試，整條鏈的放大倍率是各層相乘。架構上要規定哪一層負責重試。

### 延伸閱讀

- AWS Architecture Blog, "Exponential Backoff And Jitter"（full / equal / decorrelated jitter 對比實驗）：https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
- Amazon Builders' Library, "Timeouts, retries, and backoff with jitter"：https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/
- Google SRE Book, Ch. 22 "Addressing Cascading Failures"（retry amplification、jittered backoff）：https://sre.google/sre-book/addressing-cascading-failures/

## DLQ 死信與毒訊息

### 定義與原理

死信佇列（dead-letter queue, DLQ）是一條「處理失敗的訊息最終停放處」。當一則訊息反覆處理失敗、超過最大接收次數，broker 不再無限重投，而是把它移到 DLQ。核心要對付的是**毒訊息（poison message）**：一則內容讓 consumer 每次都崩潰／拒絕的訊息。沒有 DLQ 時，毒訊息會被無限重投，卡住整條佇列的 head——後面正常的訊息全部餓死。

第一原理：**重試是給暫時性失敗的，DLQ 是給持久性失敗的**。把這兩類分開，是讓「正常流量不被一則壞訊息拖垮」的關鍵。DLQ 不是垃圾桶，是**未決問題的收件匣**：每一筆進 DLQ 的訊息都代表一個需要人或自動化去看的事件。

### 解法空間

- **broker 原生 DLQ + maxReceiveCount**：訊息被接收並回到佇列超過 N 次，自動轉投 DLQ（SQS redrive policy、RabbitMQ dead-letter exchange）。
- **應用層分流**：consumer 自己判斷「這是不可恢復的失敗」，主動把訊息送到一條 error topic，不依賴接收次數。
- **parking lot / retry topic 階梯**（Kafka 常見）：失敗訊息進 retry-5s → retry-1m → retry-10m 多級延遲 topic，全失敗才入 DLQ，把退避做在 topic 拓樸上。
- **DLQ 回灌（redrive）**：修好 bug 或下游恢復後，把 DLQ 訊息批次重投回主佇列。
- **丟棄 + 告警**：對真的無價值的訊息（如格式徹底壞掉、無業務意義），記錄、告警、直接丟，不佔 DLQ。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| SQS redrive + maxReceiveCount | 超次數自動入 DLQ；隔離毒訊息 | 標準佇列消費 | maxReceiveCount 太小會把暫時性失敗誤判為毒訊息；DLQ 也有 retention（與來源同上限 14 天） |
| RabbitMQ DLX | 拒絕／逾期／溢出訊息路由到 DLX | 需細分死信原因（`x-death` 標頭記原因） | DLX 也可能再死信，配置不當會迴圈 |
| Kafka retry-topic 階梯 | 分級退避後才死信 | 想要可觀測的多級重試 | topic 數膨脹；跨 topic 後原 partition 順序不再保（見 訊息順序，領域 A） |
| 應用層 error topic | 由語意而非次數決定死信 | 能明確分辨可恢復／不可恢復 | 判斷邏輯散在程式碼裡，要測 |

**Worked example**：一條佇列日均 100 萬則訊息，其中 0.1% 因下游短暫 5xx 而失敗，另有 50 則是 schema 壞掉的毒訊息。若沒 DLQ、`maxReceiveCount` 等於無限，那 50 則毒訊息每則無限重投，consumer 不斷崩潰重啟，整條佇列吞吐歸零。設 `maxReceiveCount=5`：暫時性失敗的那 0.1%（約 1,000 則）多半在 5 次內隨下游恢復而成功；50 則毒訊息各被收 5 次後（共約 250 次無效處理）進 DLQ，主佇列恢復正常。代價是那 250 次處理與每則 5 倍延遲——這是把「一則壞訊息的傷害」上限化的成本。

### 何時需要

需要：任何「會遇到無法處理的單則訊息、且不能讓它拖垮整條」的消費路徑——支付事件、訂單處理、外部回呼落地。尤其當訊息來源不完全受控（第三方推送、跨團隊 topic）時，毒訊息幾乎必然出現。

不需要 / 過度：純內部、訊息格式完全受控、且「失敗就該整批停下來人工介入」的低量管線——這種直接讓它卡住反而是對的訊號。另一種是**把 DLQ 當功能用**（正常分支也往 DLQ 丟），那是濫用：DLQ 滿了沒人看，等於沒有。

### 常見誤解與陷阱

- **DLQ 設了就沒人看**。最常見的失效模式：訊息默默堆進 DLQ，沒有「DLQ depth > 0」的告警，問題積壓到 retention 到期被丟掉才發現。DLQ 必須配告警與儀表板。
- **`maxReceiveCount` 設太小**。設成 1～2，會把「下游抖一下」的暫時性失敗也踢進 DLQ，DLQ 充滿其實可重試的訊息。要和退避策略一起調。
- **回灌不檢查就重投**。bug 沒修就把 DLQ 整批 redrive 回主佇列，訊息再死一輪、再回 DLQ，形成迴圈。回灌前要確認根因已除。
- **DLQ 訊息缺上下文**。只存原始 payload、不存失敗原因／堆疊／重試次數，事後完全無從 debug。死信時要連同 metadata 一起保存。
- **以為 DLQ 保證不丟**。DLQ 本身也有 retention 與容量上限；積壓超過期限照樣消失。

### 延伸閱讀

- AWS, "Amazon SQS dead-letter queues"：https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
- RabbitMQ, "Dead Letter Exchanges"：https://www.rabbitmq.com/docs/dlx
- Confluent, "Error Handling Patterns for Apache Kafka"（retry topic 與 DLQ 階梯）：https://www.confluent.io/blog/error-handling-patterns-in-kafka/

## outbox / saga

### 定義與原理

這條解的是分散式系統最頑固的一致性問題之一：**一筆業務要同時改自己的資料庫、又對外發訊息（或呼叫別的服務），怎麼讓它們要嘛全發生、要嘛全不發生**。兩個子問題：

- **dual-write 問題**：「寫 DB」和「發 MQ」是兩個獨立系統，沒有跨它們的交易。先寫 DB 再發 MQ——發 MQ 前崩潰，DB 改了訊息沒出去；先發 MQ 再寫 DB——寫 DB 失敗，訊息已出去但狀態沒改。**outbox pattern** 解這個：把「要發的訊息」當成一筆資料，和業務變更**寫在同一個本地交易**裡（同一張 DB 的 outbox 表），交易原子性保證「狀態改了 ⇔ 訊息記了」。再由一個獨立的 relay（輪詢或 CDC，見 CDC，領域 L）把 outbox 的訊息真正投到 broker。投遞是 at-least-once，所以下游要冪等（見 冪等 idempotency，領域 A）。

- **跨多服務的業務交易**：一筆下單要扣庫存、扣餘額、建物流單，分屬三個服務、三個 DB，沒有全域 ACID 交易（2PC 太貴又脆，見 2PC 與分散式交易，領域 M）。**saga** 解這個：把長交易拆成一串本地交易，每步都有對應的**補償交易（compensating transaction）**；某步失敗就反向執行已完成步驟的補償，達到「語意上的回滾」（不是真回到原狀態，是用一筆反向操作抵銷）。saga 概念出自 Garcia-Molina 與 Salem 1987 年 SIGMOD 的論文〈Sagas〉，原本是為單機長交易設計，微服務時代被重新發掘（見延伸閱讀）。

### 解法空間

outbox 的投遞 relay：
- **輪詢 outbox 表**：relay 定期 `SELECT ... WHERE published=false`，投遞後標記。簡單、不依賴 DB 特性，代價是輪詢延遲與 DB 壓力。
- **CDC tailing**：用 Debezium 之類讀 DB 的 WAL（見 WAL，領域 O），把 outbox 表的 insert 變成事件流。低延遲、不增 DB 查詢，代價是要架 CDC（見 CDC，領域 L）。

saga 的協調風格：
- **choreography（編舞）**：無中央協調者，每個服務消費上游事件、做自己的事、再發自己的事件。去中心、低耦合，但全域流程「藏在事件之間」，難一眼看懂。
- **orchestration（編排）**：一個中央 orchestrator 明確下令「先扣庫存，成功後扣款，失敗則補償」。流程集中可見、好監控，但 orchestrator 是新的耦合點與單點。
- **durable execution**：用持久化工作流引擎（Temporal、Step Functions）把 saga 的狀態與重試／補償邏輯交給引擎管，是 orchestration 的工程化版本（durable execution 的機制屬領域 K）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| outbox（輪詢 relay） | 狀態變更與訊息原子（同 DB 交易）；at-least-once 投遞 | 單服務內「改 DB ＋ 發事件」要一致 | 輪詢延遲；outbox 表要清理；下游必須冪等 |
| outbox（CDC relay） | 同上，延遲更低 | 已有 CDC 基礎設施 | 多一套 CDC 要維運；訊息順序依 WAL 順序 |
| saga choreography | 最終一致；無中央單點 | 步驟少（2～4）、團隊各自擁有服務 | 流程不可見、難 debug；事件迴圈風險；補償順序要想清楚 |
| saga orchestration | 最終一致；流程集中可見 | 步驟多、需審計與監控 | orchestrator 是耦合點與單點；要自己保證 orchestrator 高可用 |

**Worked example**：下單 saga 三步——扣庫存、扣餘額、建物流單。庫存成功、餘額成功、建物流單時下游回 5xx 且重試耗盡。orchestrator 觸發補償：先「取消物流單」（這步根本沒成功，補償是 no-op 或冪等地確認不存在），再「退餘額」、再「還庫存」，補償**逆序**執行。注意補償本身也會失敗也要重試、也要冪等：若「退餘額」補償投遞兩次，不能退兩次款——所以補償操作要帶冪等鍵。整個過程不是 ACID 的瞬時回滾，而是一段**可觀測的、最終收斂的**反向流程；中間存在「庫存已扣、款已退、但物流未建」的暫態，這正是 saga 用最終一致換可用性的本質。

### 何時需要

需要 outbox：只要「改本地狀態」和「通知外界」必須同生同滅——幾乎所有事件驅動服務的發件端都該用。它幾乎是 dual-write 的標準答案。

需要 saga：跨服務的業務交易、且**不能用單一 DB 交易**（資料分屬不同服務／不同 DB）。choreography 適合步驟少、耦合鬆；步驟一多（補償組合爆炸、流程看不懂）就轉 orchestration 或 durable execution。

不需要：能放進**單一本地 ACID 交易**的，就別拆 saga——saga 的最終一致、補償複雜度、暫態不一致都是真實成本。「為了微服務而微服務」把本可一個交易搞定的事拆成三服務 saga，是典型 over-engineering。

### 常見誤解與陷阱

- **outbox 之後就 exactly-once**。outbox 保證「狀態變更不丟訊息」，但 relay 投遞仍是 at-least-once——relay 標記「已投」前崩潰會重投。下游一定要冪等（見 交付語意三選一，領域 A）。
- **忘了清 outbox 表**。outbox 只進不出，表無限膨脹拖垮 DB。要有「已投遞 N 天後刪除」的清理。
- **補償＝rollback**。補償是語意逆向操作，不是還原快照。寄出去的 email 收不回，只能補發「取消通知」。設計補償要從「業務上怎麼抵銷」想，不是「怎麼回到上一個狀態」。
- **choreography 變成隱形的義大利麵**。事件 A 觸發 B 觸發 C 觸發 A，繞成迴圈沒人看得出；步驟一多務必上 orchestration 把流程顯式化。
- **補償不冪等 / 不重試**。補償也是分散式呼叫，也會逾時重投；補償若沒冪等鍵，重複補償會超扣超退。
- **暫態不一致沒對外講清楚**。saga 中間存在「扣了庫存還沒扣款」的視窗，產品與對帳（見 對帳 reconciliation，領域 L）都要承認這個視窗存在。

### 延伸閱讀

- Hector Garcia-Molina, Kenneth Salem, "Sagas"（SIGMOD '87，原始論文）：https://dl.acm.org/doi/10.1145/38713.38742
- microservices.io, "Pattern: Transactional outbox"：https://microservices.io/patterns/data/transactional-outbox.html
- microservices.io, "Pattern: Saga"（choreography vs orchestration）：https://microservices.io/patterns/data/saga.html
- Chris Richardson, "Saga distributed transactions"（補償語意）：https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/saga/saga

## webhooks

### 定義與原理

webhook 是**伺服器對伺服器的回呼**：當提供方（payment、VCS、SaaS）發生某事件，它主動對你預先登記的 URL 發一個 HTTP POST，把事件推給你——是 server→client 推送的一種，但對端是「另一台伺服器」而非瀏覽器。它把「你輪詢問狀態」反轉成「事件發生時對方通知你」，省掉輪詢延遲與浪費。

但 webhook 跑在公開網路上，誰都能對你的端點發 POST，所以它的核心難點不是「怎麼收」，而是四件保證：**這真的是對方送的（簽章）／不能被重放（防 replay）／送不到要能重投（交付＋重試）／重投不能造成重複副作用（冪等）**。本質上 webhook 是「別人家的 at-least-once 投遞打到你家」，所以接收端要按 at-least-once 的所有要求來設計。

### 解法空間

- **簽章驗證（HMAC）**：提供方用共享 secret 對 payload 算 HMAC（多為 SHA-256），放在 header；接收端用同 secret 重算比對。Stripe 用 `Stripe-Signature: t=...,v1=...`、GitHub 用 `X-Hub-Signature-256: sha256=...`。驗證必須用**原始 raw bytes**，不能用重新序列化的物件（多一個空白、改 key 順序、Unicode 正規化都會破壞簽章）。
- **時間戳 + 容忍窗防 replay**：簽章內含 timestamp，接收端拒收「太舊」的事件。Stripe 預設容忍 5 分鐘（300 秒），高價值端點再縮短。
- **冪等收件**：每個事件帶唯一 event ID，接收端用它去重（見 去重 dedup，領域 A；冪等定義見 冪等 idempotency，領域 A），同一事件處理過就直接回 2xx 不重做。
- **快速回 2xx + 非同步處理**：handler 收到後先落地（寫 DB / 入佇列）立刻回 2xx，重活丟背景做。否則處理慢會讓對方判定逾時而重投。
- **重試與 DLQ（提供方側）**：提供方對非 2xx 回應做退避重試（見 重試、退避、jitter，領域 A），多次失敗後停送或落 DLQ；接收端要能容忍亂序與重複到達。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| HMAC-SHA256 簽章 | 來源真實性＋完整性 | 所有對外 webhook 端點 | 必須用 raw body；secret 輪替要支援雙 secret 並存窗口 |
| 時間戳容忍窗 | 防 replay | 簽章可能外洩的高價值端點 | 接收端時鐘要對齊（NTP）；窗太緊會誤殺正常延遲 |
| event ID 冪等去重 | 重投不重複副作用 | at-least-once 必備 | 去重 key 存哪、TTL 多久要定（見 去重 dedup，領域 A） |
| 快速回 2xx + 非同步 | 避免被判逾時重投 | 處理較重的 handler | 落地後才回 2xx，否則落地失敗卻已回 2xx＝丟事件 |
| 常數時間比對簽章 | 防時序側信道 | 所有簽章驗證 | 用 `hmac.compare_digest` 類，不要用 `==` |

**Worked example**：一個 webhook 端點日收 50,000 個支付事件，提供方對逾時／5xx 做 at-least-once 重投。若 handler 同步處理（寫 DB + 發確認信 + 更新快取）平均 800ms，遇到下游慢時超過對方 10 秒逾時——對方判定失敗，重投。假設 0.5% 觸發重投（250 個事件），其中半數其實第一次已成功只是回應慢，於是同一筆支付被處理兩次：若沒有 event ID 冪等，就是 125 封重複確認信、甚至重複入帳。正確做法：handler 收到先用 event ID 查去重表，沒見過才寫入、入佇列、立刻回 2xx（耗時降到約 20ms），確認信與快取更新在背景非同步做。重投來的 125 個重複事件命中去重表，直接回 2xx，零重複副作用。

### 何時需要

需要：整合第三方事件源（支付成功、PR 合併、訂閱狀態變更）且不想輪詢；或自己當提供方、要把事件推給客戶。webhook 是 server-to-server 事件整合的事實標準。

不需要 / 換方案：對方在防火牆後、沒有公開可達的 URL（改用對方輪詢或拉模式）；事件量極大且要嚴格有序／可重放（用訊息佇列或 event streaming 更合適，webhook 不保證順序也難重放）；瀏覽器端即時更新（那是 WebSocket／SSE 的活，見領域 C）。

### 常見誤解與陷阱

- **不驗簽章**。最危險的一條：端點公開，不驗簽就信任任何 POST，等於開放任何人偽造事件。簽章驗證是底線。
- **用解析後的 JSON 算簽章**。框架自動 parse 過 body 再 re-stringify，位元組已變、簽章必不符。必須拿 raw bytes，且常見坑是 body parser 中介層已消費掉原始流。
- **用 `==` 比對簽章**。字串相等比對有時序側信道；要用常數時間比對。
- **同步處理重活才回 2xx**。處理太久被對方判逾時而重投，雪上加霜；要先落地再回 2xx，重活非同步。
- **沒有冪等**。提供方是 at-least-once，重投必然發生（見 交付語意三選一，領域 A）；不靠 event ID 去重就會重複副作用。
- **secret 不能輪替**。secret 寫死、無雙 secret 並存窗口，輪替時要嘛漏驗要嘛全掛。設計時就要支援「舊新 secret 同時有效」的過渡。

### 延伸閱讀

- Stripe Docs, "Check webhook signatures"：https://docs.stripe.com/webhooks/signature
- GitHub Docs, "Validating webhook deliveries"（`X-Hub-Signature-256`）：https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
- webhooks.fyi（webhook 安全與最佳實踐目錄）：https://webhooks.fyi/
- OWASP, "Server Side Request Forgery Prevention Cheat Sheet"（webhook 端點易成 SSRF 標的時參考）：https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html

## 序列化與 schema 演進

### 定義與原理

兩個服務（或一個服務的新舊版本）要交換資料，得先約定「位元組怎麼排成有意義的欄位」——這是序列化格式。但系統會演進：今天加一個欄位、明天棄用一個欄位，而生產者與消費者**不會同時升級**（rolling deploy 期間新舊版本並存，見 blue-green / canary / rolling，領域 Q）。於是核心問題是 **schema 演進的相容性**：改了 schema，舊版的對端還能不能正確讀／寫？

兩個方向的相容是這條的脊椎：
- **向後相容（backward compatible）**：用**新 schema** 的消費者，能讀**舊 schema** 寫的資料。典型安全變更：加可選欄位、刪欄位。
- **向前相容（forward compatible）**：用**舊 schema** 的消費者，能讀**新 schema** 寫的資料（要能忽略不認得的欄位）。典型安全變更：加欄位、刪可選欄位。
- **完全相容（full）**：同時向前與向後——只能加／刪可選欄位。

本條只管**線上協定（wire）相容**：跨服務傳的訊息／RPC payload 怎麼平滑演進。資料庫**結構**變更（加欄位、改型別、拆表怎麼不停機）是另一回事，在 零停機 schema 遷移（領域 B）——兩者互引：協定相容讓「傳輸」不破、schema 遷移讓「儲存」不停機。

### 解法空間

格式（各自的相容機制）：
- **JSON（無 schema 或配 JSON Schema）**：欄位靠名字，天生較寬容——多的欄位忽略、缺的當沒有。代價是無強型別、體積大、無內建相容檢查。
- **Protobuf**：欄位靠**field number**（不是名字）。相容規則靠「永不重用 field number、刪欄位要 `reserved` 保留其號」。proto3 移除了 `required`，因為 required 讓相容變脆。
- **Avro**：寫入時帶 writer schema，讀取時用 reader schema，靠**schema resolution** 對齊：reader 有而 writer 沒有的欄位用 reader 的 default 補；writer 有而 reader 沒有的欄位忽略。強依賴「default 值」做相容。
- **schema registry（如 Confluent）**：集中存所有版本 schema，註冊新版本時**自動做相容性檢查**，不相容就拒絕註冊——把「相容」從口頭約定變成 CI gate。

相容策略（registry 的 compatibility type，2026-06）：BACKWARD（預設，只比最新版）、FORWARD、FULL，以及對應的 TRANSITIVE 變體（比**所有**歷史版本而非只比最新版）。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| JSON（無 schema） | 寬容、人類可讀；無相容保證 | 對外 public API、低頻整合 | 無型別檢查、體積大；相容靠紀律與測試，沒人替你擋 |
| JSON Schema | 加上結構驗證 | 想驗 JSON 又不想換格式 | 驗證是執行期的、不像 registry 在註冊時擋 |
| Protobuf | 強型別、緊湊；field number 不重用即相容 | gRPC、高吞吐內部服務（見 gRPC / Protobuf，領域 N） | 刪欄位必須 `reserved` 號與名；改型別多半破壞相容 |
| Avro | schema resolution + default 補欄位 | Kafka 事件、資料管線 | 強依賴 default；reader/writer schema 都要可得 |
| Confluent Schema Registry | 註冊時自動擋不相容變更 | 多團隊共用 topic、要強制相容 | 預設 BACKWARD 只比最新版；要防「跨多版本回放」得用 *_TRANSITIVE |

**Worked example（Protobuf 加欄位安全、改號災難）**：一個 `Order` 訊息，欄位 `string id = 1; int64 discount = 2; int64 amount = 5;`。新版要加 `string currency = 3;`——這是安全的向後＋向前變更：舊消費者收到帶 field 3 的訊息會忽略不認得的 field，新消費者讀舊訊息時 field 3 取預設空字串。但若有人「整理」schema，把已棄用的 `discount = 2` 刪掉、又把 `amount` 從 `= 5` 改成 `= 2` 重用了 2 號——災難：舊資料裡 2 號是 `discount`，新程式按 `amount` 解，wire format 沒有任何機制偵測這種錯位，於是把折扣金額讀成訂單金額，靜默地把資料解爛。正確做法是 `reserved 2; reserved "discount";`，永久封印 2 號不再重用。這就是為什麼「永不重用 field number」是 Protobuf 相容的鐵律。

### 何時需要

需要嚴格 schema 與 registry：多團隊共用的事件 topic、長期保存要回放的事件流（event sourcing，見領域 K）、高吞吐內部 RPC——這些「對端很多、升級不同步、錯了很貴」的場景，值得用 Protobuf/Avro + registry 把相容變成 CI 擋得住的東西。

夠用 JSON：對外 public API（消費者不可控，JSON 的寬容反而是優點，配版本化端點，見 REST 設計 · 版本化 · OpenAPI 契約，領域 H）、低頻低量整合、原型階段。對這些上 registry 是 over-engineering。

判準：**對端是否受你控制 + 升級是否同步 + 演進是否頻繁**。三個都「否」就往強 schema + registry 走，都「是」就 JSON 夠了。

### 常見誤解與陷阱

- **以為加欄位永遠安全**。對 Protobuf／忽略未知欄位的格式是；但若舊消費者把「未知欄位」當成錯誤拒絕（嚴格模式），加欄位就破壞向前相容。要先確認對端對未知欄位的處理。
- **重用 Protobuf field number**。如上例，wire format 偵測不到，靜默解爛資料。刪欄位必 `reserved`。
- **Avro 加欄位不給 default**。Avro 靠 default 做 schema resolution；加欄位沒 default，舊資料用新 reader 讀就會失敗。
- **registry 預設只比最新版**。Confluent 預設 BACKWARD 是非遞移的——只跟「最新註冊版」比，不跟所有歷史版比。若要回放很久以前的資料，得用 BACKWARD_TRANSITIVE 才會跨全部版本檢查（2026-06）。
- **把 wire 相容和 DB 遷移混為一談**。協定相容讓傳輸不破，但欄位真正落進 DB、改型別、拆表是 零停機 schema 遷移（領域 B）的事；只顧一邊另一邊會炸。
- **改欄位型別當小事**。`int32 → int64`、`string → bytes` 這類在多數格式都是破壞性變更；要當新欄位加、舊欄位 deprecate，而非原地改型別。

### 延伸閱讀

- Protocol Buffers, "Language Guide (proto 3)"（field number、`reserved`、相容規則）：https://protobuf.dev/programming-guides/proto3/
- Apache Avro Specification, "Schema Resolution"：https://avro.apache.org/docs/1.12.0/specification/#schema-resolution
- Confluent Docs, "Schema Evolution and Compatibility"（BACKWARD/FORWARD/FULL 與 TRANSITIVE）：https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html
- Martin Kleppmann, *Designing Data-Intensive Applications*, Ch. 4 "Encoding and Evolution"
