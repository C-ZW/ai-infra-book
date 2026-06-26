# SNS：fan-out 與 SNS→SQS

一個訂單成立了。在這之後，要發生的事情其實有一長串：扣庫存、開發票、寄確認信、通知物流、更新推薦模型、寫一筆稽核紀錄。寫下單那段程式的人，最直覺的做法是把這些下游一個一個呼叫過去——`reserveInventory()`、`issueInvoice()`、`sendEmail()`、`notifyShipping()`……。這段程式一開始很乾淨，半年後它變成一坨四百行、夾雜五個 try/catch、每加一個新需求就要動下單流程的怪物。更糟的是：發票服務那天延遲了 800 毫秒，於是「下單成功」這個本該瞬間完成的動作，被一個跟它八竿子打不著的下游拖慢了。

問題的根源是耦合。下單這件事，和「下單之後誰想知道」這件事，被綁死在同一段同步呼叫裡。下單者被迫知道有哪些下游、它們的位址、它們的健康狀況，還要替它們的慢和死負責。每多一個訂閱者，下單流程就更重一分。我們真正想要的，是一個「一件事發生了，廣播出去，誰想聽誰自己接」的機制——發布者只管喊一聲，完全不必認識聽眾。

Amazon SNS（Simple Notification Service）就是把這一聲喊做成託管服務的東西。它是 pub/sub：發布者 `Publish` 一則訊息到一個 **topic**，SNS 負責把這同一則訊息**推**（push）給所有訂閱該 topic 的端點。一發、多收，這就是 **fan-out（扇出）**。下單者從此只認識一個 topic，不認識任何下游；下游從一個變成五個，下單那段程式一個字都不用改。

## 推，而不是拉：SNS 和佇列是相反的方向

要真正理解 SNS，得先把它和佇列擺在一起看，因為它們在兩個維度上正好相反。

佇列（如 SQS）是**拉**模型，而且訊息**歸屬單一消費者**：consumer 主動去 `ReceiveMessage`，一則訊息被某個 consumer 拿走、處理、刪掉，就從佇列裡消失了，別人再也拿不到。佇列天生是「把一份工作分給一群 worker，誰有空誰做」——競爭式消費。

SNS 是**推**模型，而且訊息**複製給每一個訂閱者**：你不去拉，是 SNS 主動把訊息送上門；而且同一則訊息，每個訂閱者各拿到一份完整的拷貝。topic 有三個訂閱者，一次 `Publish` 就變成三次投遞，三個訂閱者各自收到一份、互不相干。

這兩個差別合起來決定了它們各自擅長什麼。要「一份工作只能有一個人做」——用佇列。要「一件事所有相關方都該知道」——用 topic。把 SNS 當工作分發（期待一則訊息只被處理一次）是用錯了，因為它會把訊息複製給每個訂閱者；把 SQS 當廣播（期待每個下游都收到）也是用錯了，因為一則訊息被一個 consumer 拿走就沒了。這不是設定問題，是兩種工具骨子裡的語意差。

但 SNS 純粹的「推」帶來一個它自己解不了的弱點，而這個弱點正是後面那套經典架構存在的全部理由。

## SNS 沒有緩衝，這是它最容易被誤解的地方

一個很自然、但錯得很危險的假設是：「SNS 是訊息服務，所以它應該會幫我把訊息存著、等下游有空再給。」不會。**SNS 本身沒有緩衝。** 它是一個推送的轉發器，不是一個儲存體。一則訊息 `Publish` 進來，SNS 立刻嘗試把它推給所有訂閱者，推完它的責任就結束了。

那如果某個訂閱者此刻掛了、或慢到接不下呢？SNS 確實不會立刻放棄——它對 SQS 和 Lambda 這類「AWS 託管端點」有一套相當有耐心的重試政策（後面會手算它到底有多耐心）。但重試政策終究會耗盡，耗盡之後，這則訊息要嘛進你掛上去的死信佇列（DLQ，機制見〈死信與毒訊息：DLQ〉），要嘛就**被丟掉**。重試期間，SNS 不會替你把「之後又湧進來的新訊息」整整齊齊排好隊——它沒有佇列，沒有積壓的概念，沒有讓你慢慢消化的緩衝區。

對比一下佇列：訊息進了 SQS，就安安靜靜躺在那裡，consumer 崩潰、重啟、放假三天，訊息都還在（在 retention 期內），等你回來慢慢拉。**緩衝**和**背壓吸收**是佇列的天職，恰恰是 SNS 沒有的東西。

於是你看到一個張力：SNS 給你「扇出」（一發多收、發布者不認識下游），但拿不到「緩衝」（下游慢/掛時的吸收與重放）；SQS 給你「緩衝」，但拿不到「扇出」（一則訊息只一個消費者）。兩個都想要，怎麼辦？

## SNS→SQS：把扇出和緩衝接起來

答案是把它們串起來，而且順序只能是這一個：**SNS 在前、SQS 在後。**

一個事件發到 SNS topic，topic 扇出到多個 SQS 佇列，每個下游服務各自從自己那條佇列拉。回到開場那個訂單：

```
                         +--> [SQS: inventory] --> inventory worker
                         |
[order service] --Publish--> [SNS topic: order-created] --> SQS: invoice  --> invoice worker
                         |
                         +--> [SQS: shipping]  --> shipping worker
                         |
                         +--> [SQS: email]     --> email worker
```

這個組合同時拿到兩邊的好處，而且每一條好處都對應到剛才那個張力裡少掉的一塊：

- **扇出**來自 SNS：訂單服務只 `Publish` 一次，四個下游各拿一份。要新增一個「更新推薦模型」的下游？開一條新佇列、訂閱上去，訂單服務一個字都不用改。發布者徹底不認識訂閱者。
- **緩衝**來自每一條 SQS：訊息一旦投進佇列就**落定**了，安靜躺著等對應的 worker 來拉。email worker 部署中、掛了二十分鐘？這二十分鐘的訊息全在它那條 email 佇列裡堆著，一則不丟，等它回來慢慢消化。而且——這是關鍵——**email 佇列的積壓完全不影響其他三條**。inventory、invoice、shipping 照常流動。故障被佇列**隔離**在它自己那一條裡，不會回頭拖累發布者，也不會橫向波及兄弟下游。
- **獨立的重試與 DLQ**：每條佇列各有自己的 visibility timeout、`maxReceiveCount`、死信佇列（這些 SQS 機制見〈SQS〉）。invoice 處理失敗的重試節奏，和 email 完全分開。

這就是為什麼 AWS 把 SNS→SQS 當成官方推薦的標準解耦架構，也是為什麼你會在無數系統圖裡看到這個「一個 topic 後面掛一排佇列」的形狀。它不是隨便接的——它是把「扇出」和「緩衝」這兩個本來在不同工具裡的能力，用一條邊精準地縫在一起。順序不能反：SQS 在前、SNS 在後是沒有意義的，因為一則訊息被 SQS 的某個 consumer 拿走就消失了，根本到不了 SNS 去扇出。要扇出，扇出點必須在訊息「還是一份、還沒被任何人消費」的時候，也就是在佇列**之前**。

## 訊息到了 SQS，長什麼樣子：那層 JSON 信封

這裡有一個會在第一次串 SNS→SQS 時絆倒很多人的細節，值得停下來看清楚。發布 `{"order_id": "ORD-12345"}`，consumer 從佇列拉出來的，並不是這個 JSON 本身。**預設情況下，SNS 會把你的訊息包進一層它自己的 JSON 信封再投進 SQS：**

```json
{
  "Type": "Notification",
  "MessageId": "22b80b92-fdea-4c2c-8f9d-bdfb0c7bf324",
  "TopicArn": "arn:aws:sns:us-east-1:123456789012:order-created",
  "Message": "{\"order_id\": \"ORD-12345\"}",
  "Timestamp": "2026-06-21T10:30:00.000Z",
  "MessageAttributes": { ... }
}
```

你真正的 payload 變成那個 `Message` 欄位裡的一個**字串**（注意它是被跳脫過的 JSON 字串，不是巢狀物件）。consumer 從 SQS 拉出來，得先解析外層信封、再從 `Message` 欄位把字串拿出來、再解析一次，才摸得到 `order_id`。如果你的下游程式直接 `JSON.parse` 然後找 `order_id`，它會找不到——因為最外層那一圈是 SNS 的 metadata。

要拿掉這層信封，把訂閱的 **RawMessageDelivery** 屬性設成 `true`：開啟後，SNS 把它自己的 metadata 整個剝掉，原封不動把你的 payload 投進 SQS，consumer 解析一次就拿到 `order_id`。這個設定是**每個訂閱各自獨立**的——同一個 topic，A 佇列可以開 raw、B 佇列可以不開，互不影響。

但 raw 不是免費的午餐，它有一個容易踩到的邊界：**開了 RawMessageDelivery 之後，一則訊息最多只能帶 10 個 message attribute**；要帶超過 10 個屬性，就得關掉 raw、忍受那層信封。原因不難理解——message attribute 本來是被 SNS 放進那層 JSON 信封裡傳的，剝掉信封改用 SQS 原生的 attribute 通道後，就受 SQS attribute 數量上限的約束了。所以「信封還是 raw」這個看似無關緊要的開關，背後牽動的是「你的 metadata 走哪條路」。

## 一個沉默的陷阱：SQS 變胖了，SNS 沒有

這是整章裡最值得記死、也最容易在某次升級後悄悄咬你一口的事實。

SQS 的單則訊息上限，在 2025-08 從 256 KiB 提升到了 **1 MiB**（見〈SQS〉）。很多人下意識會以為「SNS 是同一家、同一條訊息路徑，應該也跟著漲了」。**沒有。截至 2026-06，SNS 的單則訊息上限仍是 256 KiB（262,144 bytes）。** 兩者在這件事上分了岔。

把這個分岔放回 SNS→SQS 的架構裡，後果就浮現了：你這條鏈是 SNS 在前、SQS 在後，那麼**整條鏈的 payload 上限由最窄的那一段決定，也就是 SNS 的 256 KiB**。就算後面的 SQS 佇列現在能吃 1 MiB，你也塞不進一則 300 KiB 的訊息——因為它根本過不了 SNS 那一關，`Publish` 會直接被拒。一個只測過「SQS 直連、能收 1 MiB」的人，把同一份 payload 改走 SNS→SQS 扇出，會在 256 KiB 那道牆上撞得莫名其妙。

正解和 SQS 那邊是同一套：超過上限的大 payload，用 Extended Client Library 把實際內容放進 S3，SNS 訊息裡只帶一個指向 S3 物件的指標，下游再去 S3 取（這條路最大可到 2 GB）。換句話說，訊息匯流排傳的是「東西在哪」，不是「東西本身」。把大 payload 走物件儲存交接，本來就是訊息系統的常規做法（見〈物件儲存：S3 與大 payload 的交接〉），而 SNS 這個比 SQS 更小的 256 KiB 上限，只是讓你**更早**就得面對這個交接點。

## fan-out 的代價：扇出幾倍，下游與帳單就放大幾倍

扇出聽起來很美——一發多收，多優雅。但它有一個必須算清楚的成本，而且這個成本是**乘法**，不是加法。我們把它手算到底。

假設一個 SNS topic 扇出到 **4 條** SQS 佇列，這個月發布 **100 萬則**訊息。在 SNS 端，這是 100 萬次 `Publish`。但在投遞端，SNS 要把每一則訊息推給 4 個訂閱者，於是產生：

```
1,000,000 publish  ×  4 subscriptions  =  4,000,000 次對 SQS 的投遞
```

也就是 400 萬則訊息進入 SQS 體系——每條佇列各 100 萬則，各自再被 worker `ReceiveMessage`、`DeleteMessage`。你的 SQS 請求量、worker 數量、下游資料庫的寫入壓力，全部是按**扇出倍數 4** 放大的。如果哪天業務又加了兩個下游、扇出變成 6，同樣 100 萬則 publish 就變成 600 萬則投遞——下單那段程式毫無感覺，但你的 SQS 帳單和下游負載靜悄悄漲了 50%。

這個乘法效應有兩個容易被忽略的角落。第一，它讓「隨手多訂閱一個 topic」變成一個有成本的決定：訂閱很便宜（改個設定），但每一個訂閱都把全部流量乘一遍。第二，它和 SNS 的計費粒度疊加——SNS 和 SQS 一樣，發布是按每 64 KB 算一個請求單位的，一則 200 KiB 的訊息算 `ceil(200/64) = 4` 個請求，再乘上扇出倍數，數字會比你直覺的大得多。

那有沒有辦法「扇出，但不要每條佇列都收到全部」？有，這正是 fan-out 真正聰明的地方，下一節講。

## 不是每個訂閱者都想要每一則：訊息過濾

純粹的扇出是「廣播」——每個訂閱者收到 topic 的**每一則**訊息，然後自己在 consumer 裡判斷「這則跟我有沒有關係」，沒關係的就丟掉。這很浪費：你付了投遞的錢、worker 拉了訊息、解析了、判斷了，最後只是丟掉。

SNS 的**訊息過濾（message filtering）**把這個判斷往前挪到 SNS 端。你在每個訂閱上掛一份 **filter policy**（一段 JSON），SNS 在投遞前先拿訊息去比對這份 policy，**不符的訊息根本不會被投進那條佇列**。於是同一個 topic，可以讓不同訂閱者只收到它關心的子集：

- email 佇列的 policy：只要 `event_type` 是 `order_created` 或 `order_cancelled`；
- 物流佇列的 policy：只要 `region` 是 `APAC`；
- 稽核佇列：不設 policy，照單全收。

過濾可以針對**訊息屬性**（message attributes，預設），也可以針對**訊息內容本身**（message body，把訂閱的 `FilterPolicyScope` 設成 `MessageBody`）。後者讓你不必為了過濾而把判斷欄位特地搬到 attribute 去，直接拿 payload 裡的欄位比對。

過濾不只是省錢，它在語意上也更乾淨：「誰該收到什麼」這個路由規則，從散落在各個 consumer 程式裡的 `if (event_type !== ...) return;`，被收斂成一份宣告式的、住在訂閱設定裡的 policy。下游程式可以假設「我收到的都是我該處理的」，少一層防禦性判斷。

這裡有一個營運上的時間差陷阱要記得：**改了 filter policy，最長要 15 分鐘才完全生效。** 它不是即時的。如果你在一次部署裡同時改 policy、又期待新規則立刻擋住某類訊息，中間這段窗口裡舊規則還在放行，下游可能收到那些本以為已經擋掉的訊息。把 filter policy 當「即時開關」用，會在這 15 分鐘裡被騙。

## SNS 到底多有耐心：把重試政策算出來

前面說「SNS 沒緩衝，但對 SQS/Lambda 這類端點有相當有耐心的重試」。到底多有耐心？這個數字是可以查到、可以算的，而且算出來會讓你對「SNS 什麼時候才真的放棄一則訊息」有具體的感覺。

對 **AWS 託管端點**（SQS、Lambda 等），SNS 的預設投遞政策分四個階段：

```
immediate retry (no delay):  3   次，無間隔
pre-backoff:                 2   次，間隔 1 秒
backoff:                     10  次，指數退避，從 1 秒到 20 秒
post-backoff:                100,000 次，間隔 20 秒
------------------------------------------------------------
total:   100,015 次嘗試，橫跨約 23 天
```

把最後那個階段的時間粗算一下就懂這個「23 天」從哪來：post-backoff 是 100,000 次、每次間隔 20 秒，光這一段就是 `100,000 × 20 = 2,000,000` 秒 ≈ **23.1 天**。前面三個階段加起來不過幾分鐘，整條政策的長度幾乎全由這最後一段撐起。

這個數字告訴你兩件事。第一，對 SQS 端點，SNS 其實**極其**有耐心——一個下游佇列就算掛了好幾天，SNS 都還在每 20 秒敲一次門。但第二，也是更重要的：注意 SNS 重試的對象是「把訊息**投進 SQS** 這個動作」，不是「你的 worker 把訊息**處理成功**」。一旦訊息成功落進 SQS 佇列，SNS 的責任就結束了、重試政策就功成身退；之後 worker 處理失敗的重試，是 SQS 那邊 visibility timeout + `maxReceiveCount` 的事（見〈SQS〉），跟 SNS 的這 23 天完全是兩套機制。

這也再次印證了 SNS→SQS 為什麼是對的架構。如果你讓下游**直接訂閱 SNS**（比方一個 email 或 SMS 訂閱，它的政策短得多：總共約 50 次嘗試、橫跨約 6 小時，然後就放棄；HTTP(S) 端點更短，整條政策被硬上限在 1 小時內），那你能依靠的就只有 SNS 那套你改不了多少的重試政策加 DLQ。中間插一條 SQS，等於把「投遞成功」這個 SNS 容易達成的目標和「處理成功」這個你真正在乎的目標**解耦**開來：SNS 只要把訊息塞進佇列就算成功（這幾乎總會在第一次嘗試就達成），訊息接著安穩躺在佇列裡，你的 worker 用自己的節奏、自己的重試規則、自己的 DLQ 去消化它。重試與背壓的控制權，從 SNS 手裡交回到你手裡。

## 當順序也要保證：SNS FIFO topic 和它的硬規矩

到此為止講的都是 **Standard topic**：高吞吐、at-least-once（訊息至少投一次，可能重複）、best-effort ordering（盡量但不保證順序）。對絕大多數 fan-out 場景——通知、稽核、觸發下游作業——這完全夠用，因為下游本來就該冪等（見〈重複是常態〉），亂序也無傷。

但有些事件流，順序本身就是語意的一部分：同一個帳戶的「開戶 → 入金 → 出金」如果亂序處理，會算出負餘額。為這類場景，SNS 提供 **FIFO topic**，它買到兩個保證：同一個 message group 內的 **strict ordering**（嚴格先進先出），以及 5 分鐘窗內的 **deduplication（去重）**。去重 ID 可以你自己給，也可以開 content-based deduplication，讓 SNS 用**訊息內容的 SHA-256 雜湊**自動當去重 ID（注意：雜湊只算 message body，不含 message attributes——兩則 body 一樣、只有 attribute 不同的訊息，會被當成重複）。

但 FIFO topic 帶著一條會打亂你架構直覺的硬規矩，必須記牢：**SNS FIFO topic 不能直接投遞給 email、SMS、HTTP(S)、行動推播、Lambda——它只能投遞到 SQS 佇列。** 想要「有序事件 + 扇出 + 通知」，你不能讓 FIFO topic 直接掛一個 email 訂閱，中間一定要過 SQS。

更微妙的是，**端到端的順序保證能不能成立，取決於落點佇列的型別**，這裡有兩條路：

| FIFO topic 投到 | 端到端保證 | 換到的東西 |
|---|---|---|
| SQS **FIFO** 佇列 | strict ordering ＋ exactly-once processing（有序、不重複） | 完整保留順序與去重，但受 FIFO 吞吐上限 |
| SQS **Standard** 佇列（2023-09 起支援） | 降級為 best-effort ordering ＋ at-least-once | 丟掉嚴格順序與去重，換較低成本與較高吞吐 |

第二條路是一個常被忽略的「保證會在最後一段漏掉」的陷阱。你在 topic 端費心開了 FIFO、保證了順序，結果落點接了一條 Standard 佇列——那麼從這條佇列拉出來的訊息，順序和去重保證**就在這最後一段被丟掉了**。保證鏈是整條一起成立或不成立的：FIFO topic → FIFO queue 全段有序；FIFO topic → Standard queue，等於只在前半段有序、後半段放手。這個選擇本身是合理的設計（AWS 2023-09 特意開放它，就是讓你能為「不在乎順序的那些訂閱者」省成本、共用佇列），但你得**清楚自己在哪一段放掉了什麼**，而不是以為「topic 開了 FIFO，全鏈就有序」。而且這個「要不要保留全鏈順序」的決定，得在建佇列那一刻就做掉——SQS FIFO 佇列名稱必須以 `.fifo` 結尾、且型別在建立時就固定、事後不能從 Standard 改成 FIFO，所以「想接 FIFO 佇列」這一步漏在建資源時就會卡住，無法事後補救。

順帶一提，FIFO topic 還獨有一個 Standard topic 沒有的能力：**訊息存檔與重放（archive + replay）**。Standard topic 是純轉發、不留歷史，訊息推完即忘，晚加入的訂閱者讀不到過去；FIFO topic 可以設 archive policy 把訊息留存一段時間，讓新訂閱者或需要重跑的訂閱者把歷史 replay 一遍。這是 SNS 唯一帶「歷史」概念的角落——也提醒你，如果「重放歷史給新消費者」是核心需求，那條路通常更適合走 Kafka 那種日誌語意（見〈Kafka：log、partition 與 consumer group〉），而不是把 SNS 的這個附加能力撐成主力。

## 一個容易卡住整個架構的小東西：那條 SQS 的存取政策

最後講一個機制上很小、但在實務上絆住無數人第一次串接的細節，因為它揭露了 SNS→SQS 底下「誰有權對誰做什麼」的真相。

很多人以為「在 SNS 訂閱裡填上 SQS 佇列的 ARN」就完成了串接。沒有。少了關鍵一步：**那條 SQS 佇列得在自己的存取政策裡，明確允許 SNS 來投訊息**。因為訊息實際上是 SNS 服務代表那個 topic，去呼叫 SQS 的 `SendMessage`——如果 SQS 那邊沒有一條政策放行，這個呼叫會被拒，訊息靜悄悄送不進去，而 SNS 那套耐心的重試還在徒勞地敲門。

那條政策長這樣（示意）：

```json
{
  "Effect": "Allow",
  "Principal": { "Service": "sns.amazonaws.com" },
  "Action": "sqs:SendMessage",
  "Resource": "arn:aws:sqs:us-east-1:123456789012:invoice-queue",
  "Condition": {
    "ArnEquals": { "aws:SourceArn": "arn:aws:sns:us-east-1:123456789012:order-created" }
  }
}
```

讀懂這四行，等於讀懂了這條邊的信任模型：`Principal` 是 `sns.amazonaws.com`——允許的是 SNS 這個**服務**，不是某個使用者；`Action` 是 `sqs:SendMessage`——只給投訊息這一個權限，不給讀、不給刪；`Condition` 用 `aws:SourceArn` 把放行範圍**鎖死在那一個特定的 topic** 上，這一條至關重要——沒有它，等於任何 SNS topic 都能往你這條佇列灌訊息（這正是「confused deputy」那類權限混淆問題的防線）。當你用主控台或 CloudFormation 一鍵建立訂閱時，這條政策通常會被自動加上，於是你沒感覺到它的存在；但一旦是跨帳號、用程式碼分開建資源，或手動拼裝，這一步漏掉，整個 fan-out 就在最不起眼的地方靜默失敗。

值得記住的是這個失敗的**形狀**：它不會報錯給發布者。下單服務 `Publish` 成功、拿到 200，一切看起來都對；訊息卻從沒到過那條沒授權的佇列，下游靜靜地什麼都沒收到。這種「上游成功、訊息蒸發」的失敗最難查——它沒有例外、沒有堆疊、沒有紅字，只有一條本該流動卻空著的佇列。

## 為何是這個形狀

退一步看，SNS 的整個樣貌，都是從「把『一件事發生了』和『誰想知道』徹底拆開」這一個訴求長出來的。

正因為要讓發布者完全不認識訂閱者，它選了「推」而不是「拉」、選了「複製給每個訂閱者」而不是「歸屬單一消費者」——這直接決定了它是廣播工具、不是工作分發工具。正因為它把自己定位成純粹的轉發器、不沾儲存，它沒有緩衝，於是「下游慢/掛時的吸收」這塊缺口，必須靠在它後面接一條 SQS 來補——這就長出了 SNS→SQS 這個幾乎成為條件反射的標準架構，把「扇出」和「緩衝」這兩個分屬不同工具的能力縫在一起。正因為扇出是複製，它的成本是乘法，於是又長出訊息過濾，讓你在投遞前就把不相關的訂閱者剃掉。正因為純轉發不留歷史，要順序、要去重、要重放就得搬出 FIFO topic，而 FIFO 又帶著「只能投 SQS」「落點型別決定保證」這些約束，因為強保證從來都要在別處付代價。

所以下次你在系統圖上看到一個 SNS topic 後面掛著一排 SQS 佇列，你看到的不是隨手的接法，而是一連串取捨被擺到正確位置的結果：發布者只喊一聲、誰想聽自己接、每條下游有自己的緩衝與重試、互不拖累。一則「訂單成立」的訊息發出去，就像往水面丟一顆石子——漣漪自己擴散到每一個關心它的角落，而丟石子的那隻手，從頭到尾不必認識任何一圈漣漪。

## 延伸閱讀

- [Amazon SNS message delivery for FIFO topics（官方，含「FIFO topic 只能投 SQS」的端點限制）](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html)
- [Amazon SNS message delivery retries（官方，四階段重試政策與各端點的精確次數）](https://docs.aws.amazon.com/sns/latest/dg/sns-message-delivery-retries.html)
- [Amazon SNS raw message delivery（官方，信封剝除與 10 個 attribute 上限）](https://docs.aws.amazon.com/sns/latest/dg/sns-large-payload-raw-message-delivery.html)
- [Amazon SNS subscription filter policies（官方，attribute vs body 過濾）](https://docs.aws.amazon.com/sns/latest/dg/sns-subscription-filter-policies.html)
- [Amazon SNS endpoints and quotas（官方，256 KiB 訊息上限與各 region publish TPS）](https://docs.aws.amazon.com/general/latest/gr/sns.html)
- [Amazon SNS FIFO topics now support delivery to SQS Standard queues（2023-09 公告，落點降級語意）](https://aws.amazon.com/about-aws/whats-new/2023/09/amazon-sns-fifo-topics-message-delivery-sqs-standard-queues/)
- [Introducing Amazon SNS FIFO – First-In-First-Out Pub/Sub Messaging（AWS Blog）](https://aws.amazon.com/blogs/aws/introducing-amazon-sns-fifo-first-in-first-out-pub-sub-messaging/)
- [Subscribing an Amazon SQS queue to an Amazon SNS topic（官方，SQS 存取政策與授權步驟）](https://docs.aws.amazon.com/sns/latest/dg/subscribe-sqs-queue-to-sns-topic.html)
