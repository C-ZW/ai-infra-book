# RabbitMQ：exchange、routing 與 confirms

你寫一個 producer，要把一筆「使用者上傳了一張圖、請去產縮圖」的工作交出去。如果你來自佇列的世界，第一直覺是「把訊息塞進一個叫 `thumbnails` 的佇列」。但你打開 RabbitMQ 的 client，找不到「對佇列發送」這個動作——你能呼叫的只有「對某個 exchange 發布」。佇列的名字一次都沒出現在 producer 的程式碼裡。

這不是 API 設計上的彆扭，而是 RabbitMQ 整個世界觀的入口：**producer 不知道、也不該知道訊息最後會落到哪個佇列。** 它只負責把訊息丟到一個交換所，附上一串描述「這是什麼訊息」的標籤；至於哪些佇列對這種訊息有興趣、要不要複製好幾份、要不要一份都不要，是 broker 那一側、由 binding 決定的事。producer 與 consumer 之間隔著一層 routing，兩邊都不必知道對方的存在。理解 RabbitMQ，就是先理解這層刻意插進來的間接層為什麼值得。

## 為什麼要在中間插一個 exchange

設想最直白的做法：producer 直接寫佇列。一開始只有一個下游——縮圖服務——讀 `thumbnails` 佇列，沒問題。然後產品要加一個功能：每張新圖也要送去做內容審核。現在你有兩個下游想看同一筆「新圖上傳」事件。

如果 producer 直寫佇列，你只剩兩條爛路。一是讓 producer 對兩個佇列各發一次——於是 producer 的程式碼裡硬編了「目前有哪些下游」這份知識，每加一個消費者就得改 producer、重新部署。二是讓縮圖 worker 處理完再轉發一份給審核佇列——於是兩個本該獨立的關注點被串成一條鏈，縮圖服務掛了、審核也跟著斷。兩條路的共同病根是：**發布端被迫知道消費端的拓樸**，而拓樸是會變的。

exchange 就是來斬斷這個耦合的。producer 永遠只做一件事：對 exchange 發布訊息，附一個 **routing key**（一個描述訊息的字串，像 `image.uploaded`）。訊息會不會被複製、複製到哪幾個佇列，由運維時建立的 **binding**（把某個佇列以某個 pattern 綁到某個 exchange）決定。要加審核服務？建一個 `moderation` 佇列，綁到同一個 exchange、配同樣的 pattern——producer 一行都不用改，它根本不知道世界上多了一個消費者。這層 routing 把「誰發」和「誰收」在時間和知識上徹底解開（這種空間與知識上的鬆綁，是一個更大的主題，見〈解耦〉）。

## 四種 exchange：routing 的四種脾氣

exchange 不是只有一種。AMQP 0-9-1 定義了四型，差別只在「拿到一則帶 routing key 的訊息後，用什麼規則決定送進哪些 binding」（2026-06）。把這四種規則想清楚，你就能在腦中重放任何一條訊息的去向。

- **direct**：routing key 要和 binding key **完全相等**才送。這是點對點的「按類型分流」——`severity=error` 的 log 進 error 佇列，`severity=info` 的進 info 佇列。
- **topic**：routing key 用點號切成一段一段（`order.eu.created`），binding key 可以帶萬用字元——`*` 配**剛好一段**、`#` 配**零或多段**。`order.#` 收所有 order 開頭的，`*.eu.*` 收所有歐洲區的中間事件。這是訂閱式路由最有表達力的一型。
- **fanout**：**完全無視 routing key**，無腦廣播到所有綁上來的佇列。要把一個事件扇出給每一個下游，這是最省事的一型。
- **headers**：不看 routing key，改看訊息的 header 欄位做比對（可設 `x-match=all` 全中或 `any` 任一中）。實務上用得最少，但當你的路由維度不只一個字串、而是好幾個屬性的組合時，它是唯一不必把所有維度硬塞進一個 routing key 的辦法。

值得在腦中釘住的一件事：**topic exchange 在 binding key 全是字面值（沒有萬用字元）時，行為和 direct 完全一樣。** 所以這四型不是四個孤立的東西，而是一條表達力光譜——fanout 是「全收」、direct 是「精確相等」、topic 是 direct 的超集（多了萬用字元）、headers 則換一個比對維度。多數系統其實只需要 direct 和 topic 兩型。

這裡藏著第一個非顯然的後果：**一則訊息可以被路由到多個佇列，也可以一個都不到。** fanout 顯然會複製多份；但即使是 direct，只要有兩個佇列用同一個 binding key 綁上來，訊息就會各送一份。反過來，如果一則訊息的 routing key 沒有對上任何 binding——拼錯了、或那個下游還沒部署——它**不會報錯，會被靜默丟棄**。這是新手最常踩、也最難察覺的坑，我們待會兒回來算這筆帳。

## 一則訊息走完一趟的全貌

把上面的零件接起來，一則訊息從生到滅的路徑是這樣的：

```
producer
   |  basic.publish(exchange, routing_key, body)
   v
+----------+   binding (key pattern)   +---------+   push    +----------+
| exchange | ------------------------> |  queue  | --------> | consumer |
+----------+   matched? copy in        +---------+  prefetch +----------+
   |                                                      |  basic.ack
   |  no binding matched                                  v
   v                                                  broker deletes msg
 dropped (silently, unless mandatory / AE)
```

注意 consumer 那一側是 broker **主動推**（push）給它的，不是 consumer 去拉——這和「消費者自己拉取」的佇列模型（見〈SQS：Standard 與 FIFO〉）剛好相反。broker 把訊息推給 consumer 後，這則訊息進入「已投遞、未確認」的懸而未決狀態，要等 consumer 回一個 `basic.ack`，broker 才把它標記為可刪、真正從佇列移除。這個「推了不等於沒事」的環節，是 RabbitMQ 可靠性的整個核心，也是接下來最值得講透的地方。

## ack：訊息什麼時候才算「處理完了」

把訊息推給 consumer，broker 面對一個它無法直接觀測的問題：consumer 到底把這則訊息處理完了沒？它可能正在處理、可能處理到一半崩潰、可能根本沒收到。broker 看不進 consumer 的行程裡，它只能靠一個約定：consumer **自己回報**。

這個回報就是 **consumer acknowledgement**。RabbitMQ 有兩種模式，差別大到決定了你的交付語意。

**自動 ack（automatic acknowledgement）**：訊息一旦被送出，broker 就**當場視為投遞成功**、立刻從佇列刪掉，不等 consumer 說任何話。官方文件對這個模式的措辭很直接——它「應被視為不安全、並非適合所有工作負載」。原因一眼可見：訊息已經離開佇列、正在網路上飛或剛進 consumer 的緩衝區，此時 consumer 崩潰，這則訊息**沒有任何副本可以重投**，它就這麼沒了。這是 **at-most-once**：快，但會掉。

**手動 ack（manual acknowledgement）**：broker 推出訊息後不刪，掛在「unacked」狀態等著。consumer 處理完、明確呼叫 `basic.ack`，broker 才刪。如果 consumer 在 ack 之前斷線（崩潰、連線掉、行程被殺），broker 偵測到那條 channel 沒了，就把所有它推出去、還沒被 ack 的訊息**重新放回佇列**，投給另一個 consumer。這個「沒收到 ack 就重投」的機制，正是 RabbitMQ 的 **at-least-once** 來源——也正是重複的來源：consumer 明明處理完了、ack 卻在回程上丟了，broker 不知情，於是重投，下游就會看到同一筆做了兩次。

所以光是「手動 ack」還不夠，consumer 端必須冪等才能兜住這個重複窗口（冪等的完整機制見〈重複是常態〉）。這裡要釘住的關鍵時序是：**重複不是因為 broker 投了兩次，而是因為 broker 無法區分「consumer 沒處理完」和「consumer 處理完了但 ack 弄丟了」**——這和分散式系統裡那個更深的「你分不出慢和死」是同一個病根（見〈為什麼分散式這麼難〉）。在資訊不完整下，broker 只能選擇「寧可重投、不要漏投」，重複就是這個選擇的必然代價。

手動 ack 還不只 `basic.ack` 一種回報。consumer 可以回 `basic.nack` 或 `basic.reject` 表示「這則我處理不了」，並用一個 `requeue` 旗標決定 broker 該把它放回佇列重試、還是丟棄（丟棄時若配了死信機制，就轉去死信佇列，見下文）。一個沒想清楚就會踩的陷阱是：對一則「內容本身就壞、永遠處理不了」的毒訊息（poison message）回 `nack` 並 `requeue=true`——broker 老實地把它放回佇列，consumer 再拿到、再 reject、再 requeue，形成一個**全速空轉的無窮迴圈**，把 CPU 燒乾、把其他正常訊息卡在後面。毒訊息要嘛 `requeue=false` 丟去死信，要嘛靠下面要講的 delivery-limit 自動攔下。

## prefetch：別讓 broker 一次塞爆一個 consumer

手動 ack 帶出一個調度問題。broker 推訊息給 consumer，如果不設限，它會把佇列裡的訊息一股腦全推給第一個連上來的 consumer——因為在 broker 眼中那個 consumer 還沒說「我滿了」。結果是一個 consumer 的記憶體堆了上萬則待處理訊息，其他 consumer 卻閒著沒事做，負載嚴重傾斜。

解法是 **prefetch**（`basic.qos` 設的 unacked 上限）：它規定**一個 consumer 最多能有幾則「已投遞、未 ack」的訊息**（RabbitMQ 預設按 per-consumer 計，這點刻意偏離 AMQP 規格的 per-channel 共享；設 `global=true` 才回到整條 channel 共用一個額度）。設 prefetch=10，broker 推到第 10 則未 ack 的就停手，直到 consumer ack 掉一則、騰出一個位子，才再推下一則。這實際上是一個流量閥——它讓「消費的速度」回頭限制「投遞的速度」，正是背壓在訊息層的具體長相（背壓的完整機制見〈背壓〉）。

prefetch 的取捨是一條清楚的曲線。設太低（比如 1），每處理完一則才拿下一則，consumer 大半時間在等下一則訊息越過網路飛來，吞吐被 RTT 拖死。設太高，又退回前面那個「訊息全堆在一個 consumer、負載傾斜、且那個 consumer 一崩潰要重投一大批」的局面。沒有萬用值：處理快、訊息小，prefetch 可以高（幾百）以攤平網路延遲；處理慢、訊息重，prefetch 該低（個位數）讓工作平均分給整群 worker。這是個要按「處理時間 vs 網路 RTT」的比例去調的旋鈕，不是設一次就忘的常數。

## confirms：發布端怎麼知道訊息真的進去了

到目前為止講的 ack，全是 broker 和 consumer 之間的事。但發布端有一個對稱的、同樣要命的問題：**producer 呼叫 `basic.publish` 之後,怎麼知道訊息真的安全進了 broker？**

預設情況下它不知道。AMQP 的 publish 是「射後不理」——`basic.publish` 把訊息交給 TCP 連線就回，沒有任何回報。如果這一瞬間 broker 崩了、或網路斷了、或訊息因為路由不到被靜默丟棄，producer **完全無感**，它以為訊息送出去了，其實掉在了「producer → broker」這一段。

補這個洞的機制叫 **publisher confirms**。在一條 channel 上開啟 confirm 模式後，broker 每收下並安置好一則訊息，就回一個 `basic.ack` 給 producer（注意這個 ack 是 broker→producer 方向，和前面 consumer→broker 的 ack 同名但完全是兩回事）。producer 收到 confirm，才能確定訊息沒掉在前半段。

這裡有一個 2026 的重要細節，決定了 confirm 到底保證了什麼。RabbitMQ 4.0 起，**quorum queue 成為預設的複製佇列型別**（取代了 4.0 移除的 classic mirrored queue）；quorum queue 底層跑的是 Raft 共識（見〈共識〉），佇列的內容被複製到一組成員上。對 quorum queue 而言，官方文件講得很精確：**publisher confirm 只會在「訊息已成功複製到 quorum 個成員、在該佇列脈絡下被視為安全」之後才發出。** 換句話說，一個 confirm 不只是「broker 收到了」，而是「過半副本都落定了」——它扛的是「只要多數節點不永久消失，這則已 confirm 的訊息就不會丟」這個強度的保證。

而這引出 confirms 第一個違反直覺的點：**confirm 不保證按發布順序回來。** 官方明說 confirm 是**非同步**發出的——broker 大多數時候會照發布序回 ack，但因為不同佇列的複製進度不同，confirm「可以用和訊息不同的順序到達」。所以你不能寫「我發了第 1、2、3 則，收到一個 confirm 就當作是第 1 則的」——你必須照 broker 給的 delivery tag（一個單調遞增的序號）去對帳，broker 還會用「ack 到 tag N」這種累積式確認一次認掉一批。把 confirm 當成「同步、有序、一發一回」來寫，是這個機制最常見的誤用。

## confirm 和 ack 是兩條彼此不知道的線

把兩個 ack 擺在一起，最關鍵的一句話是：**publisher confirms 和 consumer acknowledgements 是正交的，彼此完全不知道對方存在**（這是官方原文的措辭）。

- confirm 覆蓋的是**前半段**：producer → broker（→ quorum 副本）。它回答「訊息有沒有安全寫進 broker」。
- consumer ack 覆蓋的是**後半段**：broker → consumer。它回答「訊息有沒有被成功處理」。

一則訊息要端到端不丟，這兩段**都要做**，少一段就漏一段。最常見的誤解是把 publisher confirm 當成端到端保證——「我收到 confirm 了，所以這筆工作完成了」。錯得很危險：confirm 只證明訊息躺進了 broker，它對 consumer 有沒有處理、有沒有崩在處理到一半，一無所知。那則訊息此刻可能正安穩地躺在佇列裡等一個根本還沒上線的 consumer。confirm 是「寄出的信有沒有送到郵局」，consumer ack 是「收件人有沒有真的拆開讀完」——兩件事。

而且即使前後兩段都做了，中間還有一個常被忘記的環節：**訊息和佇列本身得是持久的**。佇列要宣告為 `durable`、訊息要標 `persistent`，broker 重啟後它們才還在。如果佇列不持久，broker 一重啟佇列就沒了，你那套「confirm + ack」一個都救不回一則從未被寫進穩定儲存的訊息——所幸 quorum queue 天生就是持久且複製的，這個坑主要存在於還在用非持久 classic queue 的舊配置裡。完整的 at-least-once 是四件事疊起來的：佇列 durable、訊息 persistent、consumer 手動 ack、producer 開 confirms——缺任何一環，就在對應的那一段開了一個丟訊息的窗口。

## confirm 的吞吐帳：為什麼不能一則一等

publisher confirms 的安全不是免費的，它的代價直接寫在吞吐上，可以手算出來。

設想 producer 和 broker 之間的網路單程往返（RTT）是 **1 毫秒**。最天真的可靠寫法是「同步等 confirm」：發一則、卡住等它的 confirm 回來、再發下一則。那麼每一則訊息的節奏就被一個完整的 RTT 鎖死——發出去 + confirm 回來 ≈ 1 ms。一秒鐘裡你最多塞得進：

```
1 則 / 1 ms = 1000 則/秒
```

無論你的 broker 多強、機器多閒，這條 channel 的吞吐上限就是 **1,000 則/秒**，因為它被 RTT 卡死了，CPU 全程在空等。對一個要灌幾萬則/秒的系統，這個數字是災難。

破法是**批次 confirm**：一口氣發 100 則，然後只等一次 confirm（靠累積式 ack 一次認掉這 100 則）。現在 100 則訊息共攤一個 RTT：

```
100 則 / 1 ms = 100,000 則/秒（受限轉為 broker 的處理能力，而非 RTT）
```

同樣的 1 ms RTT，吞吐拉高了約**兩個數量級**。瓶頸從「網路往返」挪到了「broker 一秒能消化幾則」——也就是真正的物理上限，而不是空等。

但這個吞吐是用一塊安全性換來的，代價很具體：批次裡萬一有訊息沒被 confirm（broker 對某幾則回了 `basic.nack`，表示它沒能安置），你只知道「**這批有問題**」，卻不能精確地一眼指出是哪幾則——你得照 delivery tag 去比對哪些 tag 沒被 ack、把那幾則重送。批次越大，吞吐越高，但一旦出事要回溯、重送的範圍也越大，且這段期間 producer 得自己把「已發未確認」的訊息暫存著、不能丟。安全與吞吐的取捨，就精確地落在「批次大小」這一個旋鈕上：實務上常取 50–100 則等一次 confirm，在「RTT 不要太傷吞吐」和「出事重送範圍不要太大」之間找平衡。

## 訊息會在哪些地方安靜地消失

RabbitMQ 的可靠性故事裡，最陰險的不是「會丟」，而是「丟得無聲無息」。把幾個會靜默吞掉訊息的點集中起來看，因為它們各自都長得人畜無害。

**路由不到，預設直接丟。** 前面埋的這筆帳現在算清楚：你 publish 一則 routing key 是 `order.created` 的訊息，但因為打字錯成 `oder.created`、或那個該收的佇列還沒被綁上來，**沒有任何 binding 匹配**。broker 不會報錯、不會退回、不會記一筆顯眼的 log——它**靜靜地把訊息丟棄**。producer 那邊若開了 confirms，甚至還會收到一個 `basic.ack`（訊息被 broker「成功處理」了——只是這裡的「處理」就是丟棄）。表面上一切正常、confirm 也回來了，訊息卻已蒸發。想堵這個洞有兩條路：publish 時帶 `mandatory` 旗標——這樣路由不到時 broker 會用 `basic.return` 把訊息**退回** producer，讓你當場知道；或給 exchange 配一個 **alternate exchange**——路由不到的訊息被導去一個「兜底」exchange（通常是 fanout 接一個 `unroutable` 佇列），事後撈出來查。兩條路都得你**主動**設，預設行為就是無聲丟棄。

**毒訊息與 delivery-limit。** 前面提過 `nack` + `requeue` 會把壞訊息打進無窮重試。RabbitMQ 4.0 起的 quorum queue 給了一道自動保險：**delivery-limit 預設 20**。同一則訊息被投遞、被 requeue、再投遞……次數一旦超過這個上限，broker 不再傻傻重投，而是把它**丟棄、或（若配了死信交換所）轉進死信佇列**。這把「毒訊息無限空轉」從一個會燒掉叢集的事故，降級成「一則訊息靜靜躺進 DLQ 等人來看」。要注意這是 quorum queue 的行為，且 20 是個你該按自己重試策略調整的預設，不是金科玉律。

**死信交換所（DLX）不等於 alternate exchange。** 這兩個機制名字都像「兜底」，但攔的是完全不同的時刻，混為一談會在錯的地方找不到訊息：

| 機制 | 攔截時機 | 觸發條件 |
|---|---|---|
| alternate exchange | 訊息在 **exchange** 路由階段就沒對上任何佇列 | 無 binding 匹配（還沒進任何佇列） |
| dead letter exchange (DLX) | 訊息**已經進了佇列**、之後才出局 | 被 `reject`/`nack`（不 requeue）、TTL 過期、或超過 delivery-limit／佇列長度上限 |

一句話記牢：**alternate exchange 接的是「進不了任何佇列」的訊息，DLX 接的是「進了佇列、但被退貨」的訊息。** 你的訊息明明 publish 了卻人間蒸發時，要先分清它是卡在路由階段（去看 alternate exchange / mandatory return）還是出局階段（去看 DLX），否則會在錯的桶子裡撈空。

## 它解什麼、又不解什麼

把 RabbitMQ 放回它的生態位看，形狀就清楚了。它的兩個招牌強項，都是從「中間那層 exchange」長出來的：一是 **routing 的表達力**——direct / topic / fanout / headers 讓你用宣告的方式描述複雜的分送邏輯，不必把它寫死在 producer 裡；二是**低延遲的任務分發**——一群 worker 用 competing consumers 模式各搶各的，配 prefetch 做負載均衡，配手動 ack 做可靠重試，這套組合對「把耗時工作丟出去、要靈活路由、量中等」的場景貼合得很好。

它的弱項同樣是結構性的，而且正是它和 log 型系統（見〈Kafka：log、partition 與 consumer group〉）最該被想清楚的分界：RabbitMQ 本質是**消費即走**的 broker——一則訊息被某個 consumer ack 掉，就從佇列消失了。它的世界裡**沒有「歷史」這個概念**：你不能讓一個新上線的 consumer「從三天前開始重讀」，因為三天前被 ack 的訊息早就不存在了；你也不能讓兩組互不相干的消費者各自完整地讀一遍同一批訊息（除非在 exchange 那層 fanout 成兩個佇列，但那是「複製當下的流」，不是「重放過去的 log」）。需要重放、需要多組消費者獨立地把同一份歷史讀很多遍——這是 log 的設計甜蜜點，把 RabbitMQ 硬掰成那個形狀是在跟它的本質作對。（RabbitMQ 後來加了 Stream 這種 append-only、可重讀的佇列型別來補這一塊，但那是另一套心智模型，不是 exchange/queue 的預設世界。）

## 為什麼是這個形狀

回到開頭那個「找不到怎麼對佇列發送」的困惑。RabbitMQ 的整個形狀，是把一個樸素的判斷貫徹到底的結果：**發布的人不該知道訂閱的人是誰。** 

正因如此，中間要有一層 exchange + binding，讓 routing 成為運維時可重新佈線、而非編譯進 producer 的東西——四種 exchange 不過是這層 routing 的四種表達力。正因為訊息要跨越「producer → broker → consumer」兩段不可靠的傳輸，每一段都需要自己的、互不知情的確認——前段 confirm、後段 ack，正交是它們的本質而非巧合。正因為「沒收到確認」永遠分不清是「沒做完」還是「確認丟了」，broker 只能選擇寧可重投，於是重複成為常態、冪等成為前提。也正因為它選擇了「消費即走」這個輕量的語意，它換來了低延遲與靈活路由，也就此放棄了重放歷史的能力。

每一個你覺得彆扭的設計——producer 看不到佇列、confirm 不照順序回、訊息會無聲消失、要手動湊齊四件事才不丟——拆開來看，都不是隨意的工程慣例，而是「在不可靠傳輸上做靈活分送」這個問題被推到底之後，一個個取捨留下的形狀。下次你盯著一個 routing key 拼錯而蒸發的訊息發呆時，你會知道那不是 bug——那是它在忠實地執行「路由不到就丟」的約定，而你只是還沒替那個約定裝上 mandatory 或 alternate exchange 這道你本該裝的網。

## 延伸閱讀

- Consumer Acknowledgements and Publisher Confirms（RabbitMQ 官方，confirm/ack 正交性與保證的權威說明）: https://www.rabbitmq.com/docs/confirms
- Quorum Queues（RabbitMQ 官方，Raft 複製、delivery-limit、confirm 與 quorum 的關係）: https://www.rabbitmq.com/docs/quorum-queues
- AMQP 0-9-1 Model Explained（RabbitMQ 官方，exchange / binding / queue 的概念模型）: https://www.rabbitmq.com/tutorials/amqp-concepts
- RabbitMQ Tutorials（官方教學，逐型 exchange 與 routing 的範例）: https://www.rabbitmq.com/tutorials
- Reliability Guide（RabbitMQ 官方，端到端不丟訊息要湊齊哪些條件）: https://www.rabbitmq.com/docs/reliability
- Publishers（RabbitMQ 官方，mandatory 旗標、basic.return、unroutable 訊息處理）: https://www.rabbitmq.com/docs/publishers
- AMQP 0-9-1 specification（協定原文，basic.publish / ack / nack / reject 的線上語意）: https://www.rabbitmq.com/resources/specs/amqp0-9-1.pdf
