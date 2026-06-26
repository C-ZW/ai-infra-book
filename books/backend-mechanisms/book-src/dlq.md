# 死信與毒訊息：DLQ

凌晨三點，一條本來每分鐘吞吐幾千則訊息的佇列，吞吐突然歸零。儀表板上 consumer 還活著、CPU 正常、佇列深度卻一路往上爬。登進去看 consumer 的 log，是一行同樣的錯誤，每幾百毫秒重複一次，捲動得像瀑布——`JSON parse error at offset 0`。某個上游不知怎麼，把一則內容徹底壞掉的訊息塞了進來。consumer 拿到它、嘗試解析、丟例外、崩潰；訊息沒被確認，於是 broker 把它**重新投遞**回佇列頭；consumer 重啟、又拿到同一則、又崩潰。一則訊息，把整條管線鎖死了。

這就是**毒訊息（poison message）**：一則內容讓 consumer 每次處理都失敗的訊息。它的破壞力不在於它自己壞——壞掉的單一筆資料是小事——而在於**它擋在佇列的頭，後面所有正常的訊息全部餓死**。一則 0.001% 機率出現的爛資料，造成 100% 的停擺。死信佇列（dead-letter queue, DLQ）這套機制，存在的全部理由，就是把這顆毒丸從主管線裡**挑出來、隔離掉**，讓後面的隊伍能繼續前進。

## 為什麼「無限重投」是個陷阱

要看懂 DLQ 為什麼非存在不可，得先看清楚它要修補的那個天真設計：**訊息系統預設就是 at-least-once，而 at-least-once 的字面意思，是「沒成功就一直重投」。**

這個預設本身是對的。訊息送到 consumer、consumer 處理、處理成功才回 ack（acknowledgement）刪掉訊息——這條 ack 機制是訊息系統可靠性的根。如果 consumer 還沒回 ack 就崩了，broker 沒收到確認，唯一安全的假設是「這則訊息可能沒被處理」，於是它重投。這正是訊息系統承諾「不丟訊息」的方式：寧可重複，也不漏送（去重的責任因此落到 consumer 身上，這是另一套機制，見〈重複是常態〉）。

問題出在這個機制**分不出兩種完全不同的失敗**。

第一種是**暫時性失敗（transient failure）**：下游資料庫剛好在做 failover、被呼叫的 API 回了 429、網路抖了一下。這種失敗，重投是**對的解法**——再試一次，下次多半就成了。

第二種是**持久性失敗（persistent failure）**：訊息本身的內容讓處理永遠不可能成功。schema 壞掉解不出來、引用了一個早已被刪除的外鍵、欄位值違反了不可能違反的約束。這種失敗，重投是**最糟的解法**——它永遠不會成功，而你每重投一次，就再浪費一次 CPU、再撞一次崩潰、再把後面的隊伍多堵一會兒。

天真的 ack/重投機制只認得「沒回 ack」這一個訊號，把這兩種失敗一視同仁地塞進同一個無限重投的迴圈。對暫時性失敗，這迴圈會自己解開；對持久性失敗，這迴圈**永遠不會解開**——這就是毒訊息卡死管線的根本原因。

所以 DLQ 的第一原理只有一句話：**重試是給暫時性失敗的，DLQ 是給持久性失敗的。** 整套機制做的事，就是給「一則訊息已經失敗夠多次了」劃一條線——越過這條線，broker 不再把它投回主佇列，而是把它搬到旁邊一條專門的佇列（就是 DLQ）停放，讓主管線恢復暢通。劃這條線的判據，幾乎都是同一個：**這則訊息已經被收下並失敗了 N 次。**

## 那條線畫在哪：接收次數，不是處理次數

機制的核心，是 broker 替每一則訊息記一個計數器，數它「被投遞出去幾次」。以 SQS 為例，這個計數叫 `ApproximateReceiveCount`；佇列上設一個門檻 `maxReceiveCount`（透過 redrive policy 設定，預設值是 **10**，2026-06）。規則很簡單：

```
on each ReceiveMessage:
    receiveCount += 1
    deliver message to consumer
    if consumer deletes (acks) within visibility timeout:
        message gone, done
    else (visibility timeout expires without delete):
        message becomes visible again
        if receiveCount > maxReceiveCount:
            move message to DLQ   # 越線，搬走
        else:
            redeliver             # 還在容忍範圍，重投
```

這裡藏著一個幾乎所有人第一次都會踩到的陷阱：**這個計數器數的是「被收下幾次」，不是「崩潰幾次」。**

兩者的差別很要命。想像一則訊息**本身完全正常**，只是處理它需要 40 秒，而你的 visibility timeout（訊息被收下後、暫時對其他 consumer 隱形的時間）設成 30 秒。會發生什麼？consumer 收下訊息（`receiveCount` 變 1）、認真處理；30 秒一到，visibility timeout 過期，broker 以為「這個 consumer 大概死了」，**把還在處理中的訊息重新放出來**；另一個 consumer（或同一個）又收下它（`receiveCount` 變 2）……。這則訊息根本沒崩潰過、處理邏輯也沒有 bug，純粹因為**太慢**，計數器一路往上爬，最後越過 `maxReceiveCount`，被當成毒訊息丟進 DLQ。

於是你會在 DLQ 裡看到一則「看起來完全正常」的訊息，百思不得其解——它不是毒，它只是慢。這就是為什麼 `maxReceiveCount` 不能孤立地調：它和 visibility timeout、和你處理一則訊息的真實耗時**綁在一起**。visibility timeout 必須留足處理時間的餘裕（慢的 handler 要主動延長 visibility，或縮短處理路徑），否則 DLQ 會被一堆「慢但無辜」的訊息污染，而真正的毒訊息反而被淹沒在裡面。**DLQ 的判據是「接收次數」這個代理指標，而代理指標永遠有它測不準的角落。**

## 一則訊息進 DLQ，要付多少代價：手算一次

DLQ 不是免費的隔離。每一則最終進 DLQ 的訊息，都先在主佇列裡被反覆收下、反覆失敗了 `maxReceiveCount` 次——這些失敗的處理是真實的成本。把它算到底，才知道 `maxReceiveCount` 該設多大。

設一條佇列，日均 100 萬則訊息。其中：

- **0.1%（1,000 則）是暫時性失敗**——下游某段時間在抖，這些訊息頭一兩次收下時失敗，但隨下游恢復，多半在 2～3 次接收內就成功了。
- **50 則是真正的毒訊息**——schema 壞掉，無論收幾次都解不出來。

現在比較兩種設定。

**若 `maxReceiveCount` 設成 1（一失敗就丟 DLQ）**：那 1,000 則暫時性失敗的訊息，第一次撞上下游抖動就被踢進 DLQ——但它們其實只要再試一次就會成功。你把 1,000 則「可恢復」的訊息錯當毒訊息隔離了，DLQ 被它們塞滿，真正的 50 則毒訊息淹沒在一千則雜訊裡。這是「線畫得太前面」的代價：**把暫時性失敗誤判成持久性失敗。**

**若 `maxReceiveCount` 設成 5**：那 1,000 則暫時性失敗的，絕大多數在 5 次接收內隨下游恢復而成功，幾乎不進 DLQ。50 則毒訊息呢？每則被收下並失敗 5 次後才越線——共 `50 × 5 = 250` 次注定失敗的處理，然後它們乾淨地落進 DLQ。代價是這 250 次無效處理的 CPU，以及每則毒訊息從進佇列到進 DLQ 之間約 5 倍的延遲。換來的是主佇列在這整段期間**從未被堵死**。

這 250 次無效處理，就是「把一則毒訊息的傷害**上限化**」的價碼。沒有 DLQ（等於 `maxReceiveCount` 無限大）時，這 50 則毒訊息的傷害是**無上限**的：每則無限重投，consumer 不斷崩潰重啟，整條佇列吞吐歸零，後面 99.99 萬則正常訊息全部陪葬。DLQ 用「最多浪費 N 次處理」這個有界的小代價，換掉了「整條管線無限期停擺」這個無界的大災難。`maxReceiveCount` 這個數字，本質上就是你在「給暫時性失敗多少次翻盤機會」和「讓毒訊息多快被隔離」之間下的注。

## 進了 DLQ，訊息能放多久：一個會悄悄殺掉證據的時鐘

訊息進了 DLQ，故事還沒完——因為 **DLQ 自己也是一條佇列，也有 retention（保留期限）**。很多人把 DLQ 當成永久保險箱，這個假設會在最不該的時候背叛你。

SQS 的這個角落特別狡猾，值得講透。SQS 訊息的過期，是依**它最初進入佇列那一刻的時間戳**算的，retention 上限 14 天。關鍵在於：**當一則 Standard queue 的訊息被搬到 DLQ 時，這個原始時間戳「不會重設」。**（2026-06，AWS 官方文件；FIFO queue 的行為相反——搬進 DLQ 時時間戳會重設。）

把這個細節展開看它多致命。假設主佇列和 DLQ 的 retention 都設成預設的 4 天。一則訊息在主佇列裡掙扎了——被收下、失敗、重投、再失敗——整整 1 天，才終於越過 `maxReceiveCount` 進了 DLQ。它在 DLQ 裡還能活多久？不是 4 天，而是 `4 − 1 = 3` 天。因為那個倒數計時的時鐘，從訊息最初進主佇列那一刻就開始走了，搬家不會把它歸零。

更糟的版本：如果主佇列 retention 設 14 天、DLQ 也設 14 天，而一則訊息在主佇列裡（因為某種重投迴圈）耗了 13 天才進 DLQ，那它在 DLQ 裡只剩 1 天就會被**靜默刪除**——沒有錯誤、沒有告警，那則承載著「為什麼會失敗」的證據，就這麼蒸發了。等你某天早上想去 DLQ 撈出毒訊息追根因，發現它早就過期消失，連屍體都不剩。

這就是為什麼有一條看似囉嗦卻救命的最佳實踐：**DLQ 的 retention 一定要設得比來源佇列長**（SQS 直接設成上限 14 天最穩）。DLQ 的價值在於它是「待處理問題的收件匣」——而一個收件匣若會自動把還沒讀的信燒掉，它就不是收件匣。**DLQ 不保證不丟訊息**這件事，是它最反直覺、也最常被忽略的性質。

## broker 怎麼搬：三家三種脾氣

「把失敗訊息搬到旁邊」這個動作，每個 broker 的做法不同，而這些差異不是實作細節——它們決定了你的 DLQ 在邊界上會怎麼壞。

**SQS** 是最直白的一種：DLQ 就是另一條普通佇列，你在來源佇列的 redrive policy 上指定它的 ARN 和 `maxReceiveCount`，越線的訊息被 broker 自動搬過去。簡單，但它只認得「接收次數」這一個維度——它不知道你**為什麼**失敗，DLQ 裡的訊息身上沒有「失敗原因」這個資訊，那得靠你自己在處理時記 log。

**RabbitMQ** 走的是 dead-letter exchange（DLX）路線，語意豐富得多。一則訊息會被死信化（dead-lettered），有四個明確的原因（2026-06，RabbitMQ 官方文件）：

- `rejected`——consumer 明確地 `basic.reject` / `basic.nack` 且不要求 requeue；
- `expired`——訊息的 per-message TTL 到期；
- `maxlen`——佇列長度超過上限，訊息被擠掉；
- `delivery_limit`——（quorum queue）重投次數超過 `delivery-limit`。

而且 RabbitMQ 會在死信訊息的 header 裡塞一個 `x-death` 陣列，記下它每一次被死信化的完整歷史：是從哪條佇列、因什麼原因、第幾次、頭一次和最後一次的時間戳。這份履歷讓事後 debug 有跡可循——你一眼能看出這則訊息是「被 consumer 主動拒絕」還是「TTL 過期」死的，這是 SQS 給不了的。

但 RabbitMQ 這裡藏著一個足以讓人半夜驚醒的預設行為：**傳統的 dead-lettering 是 at-most-once 的。** broker 把死信訊息重新發佈到 DLX 時，**內部沒有開 publisher confirm**——也就是說，如果那一瞬間目標 DLQ 剛好不可用，或 broker 在搬運過程中崩潰，這則死信訊息會**直接遺失**。你以為訊息進了 DLQ 安全了，其實它在搬家的路上掉進了縫裡。要堵住這個洞，得用 **quorum queue 的 at-least-once dead-lettering**——它在重新發佈時開了 publisher confirm，確認目標收到才放手。但這個保證有個容易漏掉的成立條件：除了把 `dead-letter-strategy` 設成 `at-least-once`，還**必須**把 `overflow` 設成 `reject-publish`；若維持預設的 `drop-head`，整套機制會**悄悄退回 at-most-once**（因為 drop-head 允許從源佇列丟頭部訊息，本身就違反 at-least-once 語意）——正是這章最想防的那種「你以為設好了、其實沒生效」的靜默失效。「失敗的訊息至少不會在進 DLQ 的路上再丟一次」這個保證，**不是預設送的，要主動去掙、而且要掙對**。

RabbitMQ 還順手解了另一個問題：死信迴圈。如果 DLQ 的訊息又被死信化、又繞回原佇列，會不會無限轉圈？RabbitMQ 的規則是：**偵測到「同一則訊息第二次到達同一條佇列、且整個循環裡沒有任何一次是 `rejected`」，就把它丟棄**——用「迴圈裡有沒有人真的拒絕過」來區分「合法的多跳路由」和「死循環」。

**Kafka** 則乾脆**沒有 broker 原生的 DLQ**。這不是缺漏，是它的資料模型決定的：Kafka 的 topic 是一份不可變的 append-only log，consumer 自己拿著一個 offset 游標往前讀，**broker 根本不知道某一則訊息「被處理成功了沒有」**——它沒有 per-message ack 的概念，也就沒有「重投次數」可數，自然無從替你判斷哪則該進 DLQ。於是在 Kafka 世界裡，DLQ 是個**純粹的 consumer 端模式**：consumer 自己 catch 住處理失敗，把那則訊息**重新 produce 到另一條 topic**（習慣上叫 dead-letter topic）。一個典型的毒訊息場景是 producer 換了序列化格式卻沒換 topic，下游所有 consumer 的 deserializer 全部解不出來——`ErrorHandlingDeserializer` 之類的工具會把解不出的那則記成 null、把例外塞進 header，讓 consumer 能優雅地把它轉送到 dead-letter topic 而不是卡死整個 partition。

| broker | DLQ 怎麼來 | 判據 | 帶不帶失敗原因 | 搬運保證 |
|---|---|---|---|---|
| SQS | broker 原生（redrive policy） | `receiveCount > maxReceiveCount` | 否（自己記 log） | broker 伺服器端代搬（best-effort，無 exactly-once 保證） |
| RabbitMQ | broker 原生（dead-letter exchange） | reject / expired / maxlen / delivery_limit | 有（`x-death` 履歷） | 預設 at-most-once；quorum queue 才 at-least-once |
| Kafka | 沒有原生，consumer 自己 produce 到另一 topic | 由 consumer 程式碼自行定義 | 看你自己塞什麼進去 | 看你自己怎麼寫（要處理 produce 失敗） |

這張表的重點不是記住誰是誰，而是看出一條共同的縫：**「把訊息可靠地搬進 DLQ」這個動作本身，也是一次投遞，也會失敗。** SQS 把這一步搬到伺服器端代你做（所以它不會在你的程式碼裡靜默掉訊息）——但別把「broker 代搬」誤讀成「原子／exactly-once 搬運」：AWS 並未對這步 publish 明確的不重複保證，Standard queue 整體仍是 best-effort。RabbitMQ 預設則連這層 best-effort 都不保證（at-most-once），要你升級 quorum queue 去掙；Kafka 則整個丟給你自己寫——而你自己 produce 到 dead-letter topic 那一步若沒處理好 produce 失敗，毒訊息就在你試圖隔離它的瞬間蒸發了。

## 一個更陰險的版本：批次裡的一顆毒丸

到目前為止講的都是「一次處理一則」。但很多高吞吐管線是**批次消費**的——一次拉一批 10 則、20 則訊息進來一起處理。批次把毒訊息問題推到一個更難看的角落，這個 edge case 值得單獨拆開。

以 Lambda 消費 SQS 為例。Lambda 的 event source mapping 一次拉一個 batch（Standard queue 預設 10 則、設了 batching window 後最大可到 10,000 則；FIFO queue 上限 10 則，2026-06）交給你的函式。問題是：**這一整批的成敗，預設是綁在一起的。** 如果這個 batch 裡有 19 則正常、1 則是毒訊息，而你的函式在處理到那則毒訊息時拋了例外——預設行為是**整個 batch 算失敗**。於是那 19 則**已經成功處理過**的訊息，連同那 1 則毒訊息，**全部一起變回可見、一起被重投**。

接下來更難看：這 20 則又被一起拉一次，那 19 則正常訊息**被重複處理了第二遍**（如果你的 handler 不冪等，就是重複的副作用），那 1 則毒訊息又讓整批失敗、又一起重投……如此反覆 `maxReceiveCount` 次之後，**整個 batch——包括那 19 則無辜的正常訊息——一起被搬進 DLQ**。一顆毒丸，污染了一整批好訊息，把它們全拖下水。你的 DLQ 裡躺著 20 則訊息，其中 19 則其實早就處理成功過了。

修補的方式叫 **partial batch response**（在 event source mapping 上開 `ReportBatchItemFailures`）：函式不再用「拋例外＝整批失敗」來表態，而是回傳一份**明確的失敗清單**——「這個 batch 裡，只有第 7 則的 message ID 失敗了，其餘 19 則請當成功、別重投」。於是只有那 1 則毒訊息的 `receiveCount` 會往上爬、最後進 DLQ，19 則正常訊息一次過關、不被重複處理。

這個小細節揭露了 DLQ 機制一個更深的前提：**隔離的粒度必須對得上失敗的粒度。** 失敗是「一則」訊息的事，隔離就必須能精確到「一則」。一旦你的消費單位（batch）比你的失敗單位（單則訊息）粗，毒訊息的污染半徑就會放大到整個批次——你以為 DLQ 在做精準隔離，它其實在做連坐。（FIFO 場景下這個張力更尖銳：為了保住順序，一則卡住就不能跳過後面的，partial batch 的處理規則因此更嚴格——遇到第一個失敗就得停下，把它和它之後所有未處理的訊息一起回報為失敗。順序與隔離在這裡直接打架，見〈訊息順序：FIFO 與 partition key〉。）

## DLQ 不是垃圾桶，是收件匣

機制講到這裡都還只是「怎麼把訊息搬進 DLQ」。但 DLQ 真正的失效模式，幾乎都不在搬進去的那一刻，而在**搬進去之後**。

最常見、也最致命的一種失效，平淡到不像故障：**DLQ 設了，但沒人看。** 訊息默默地、一則一則地堆進 DLQ，沒有任何「DLQ depth > 0」的告警，沒有人盯著它的儀表板。問題在裡面靜靜積壓，直到某天——可能是 retention 到期、訊息被靜默刪光之後，可能是某個客戶投訴「我的訂單三週前就付款了怎麼還沒處理」之後——才有人想起來去看一眼 DLQ，發現裡面躺著三千則沒人管的失敗訊息，而最早那批已經因為過期而永遠消失了。一個沒有告警、沒有人看的 DLQ，和沒有 DLQ 幾乎沒兩樣：毒訊息確實沒堵死主管線了，但它承載的那個「有東西壞了」的訊號，也一起被你靜音了。

所以一條健康的 DLQ，永遠是**配著告警和儀表板**的——「DLQ 深度大於 0」本身就該是一個值得有人醒來看一眼的事件。因為每一則進 DLQ 的訊息，定義上都是一個「系統嘗試處理、但失敗了」的未決問題。DLQ 是這些問題的**收件匣**，不是它們的**垃圾桶**。

問題看了、根因修了之後，還有最後一步：**回灌（redrive）**——把 DLQ 裡的訊息重新投回主佇列再處理一次。SQS 在 2021 年底加了原生的 DLQ redrive，2023 年補上了 SDK／CLI 自動化和 FIFO 支援，還能調**回灌速率**（system-optimized 全速，或自訂每秒上限，免得一口氣把幾萬則訊息倒回主佇列、瞬間壓垮才剛恢復的下游）。但回灌有一個必須先過的關卡，過不了就是一場災難：**回灌前，根因必須已經修好。**

道理很硬：DLQ 裡的訊息，定義上就是「處理會失敗」的訊息。如果 bug 還沒修、下游還沒恢復，你就把它們整批 redrive 回主佇列——它們會**再失敗一輪、再被收 `maxReceiveCount` 次、再回到 DLQ**。你什麼都沒解決，只是讓同一批訊息多繞了一圈、多燒了一輪 CPU，運氣不好還在這一圈裡把它們的 retention 時鐘又往前推了一截，離靜默刪除更近一步。回灌不是「重試」的同義詞——重試是賭「下游剛好抖了一下」，回灌是賭「我已經把根本的 bug 修好了」。賭錯的代價，是一個自己餵自己的死循環。

## 為什麼是這個形狀

退一步看，DLQ 的整個樣貌，都是從一個無法迴避的事實裡長出來的：**訊息系統用「沒成功就重投」來保證不丟訊息，而這個機制天生分不出「值得再試」和「再試也沒用」。**

正因為分不出，所以需要一條線——用「失敗了幾次」這個可數的代理指標，替「這是不是毒訊息」這個無法直接判定的問題，畫一個務實的近似。正因為這條線是近似，所以它總在邊界騙人——慢的訊息被誤當成毒的，暫時性失敗被誤當成持久性的，`maxReceiveCount` 永遠是在兩種誤判之間下注。正因為被隔離的是「失敗的證據」，所以 DLQ 必須被當成收件匣慎重對待——它要有比來源更長的 retention 護住證據、要有告警喊醒人去看、要有回灌的路徑在根因修好後讓訊息重見天日。

DLQ 不是一個讓壞訊息「消失」的地方。它是一個承認「持久性失敗會發生、而且不該由整條管線陪葬」的設計——把那一小撮注定失敗的訊息，從快速流動的主幹道上**抽出來、停到路肩**，讓車流繼續跑，同時亮起一盞「這裡有東西需要人來看」的燈。下次你看到一條佇列旁邊掛著一條幾乎總是空的 DLQ，你會知道那條空佇列不是擺設——它是一份隨時待命的保險，賭的是「總有一天，會有一則訊息壞到沒有任何重試能救得了」。而那一天，它會是擋在你的主管線和那則毒訊息之間，唯一的那道牆。

## 延伸閱讀

- AWS, "Using dead-letter queues in Amazon SQS"（redrive policy、`maxReceiveCount`、retention 時間戳行為）: https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html
- AWS, "Introducing Amazon SQS dead-letter queue redrive to source queues"（回灌、redrive velocity）: https://aws.amazon.com/blogs/compute/introducing-amazon-simple-queue-service-dead-letter-queue-redrive-to-source-queues/
- AWS Lambda, "Reporting batch item failures"（partial batch response、`ReportBatchItemFailures`）: https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html
- RabbitMQ, "Dead Letter Exchanges"（四種死信原因、`x-death` 履歷、迴圈偵測、at-most-once 預設）: https://www.rabbitmq.com/docs/dlx
- RabbitMQ, "At-Least-Once Dead Lettering"（quorum queue 的 at-least-once 死信保證）: https://www.rabbitmq.com/blog/2022/03/29/at-least-once-dead-lettering
- Confluent, "Spring for Apache Kafka: Can your Kafka consumers handle a poison pill?"（`ErrorHandlingDeserializer` 與 dead-letter topic 模式）: https://www.confluent.io/blog/spring-kafka-can-your-kafka-consumers-handle-a-poison-pill/
