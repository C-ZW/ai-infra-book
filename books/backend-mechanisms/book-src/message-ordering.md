# 訊息順序：FIFO 與 partition key

一個帳戶的當前餘額是 100 元。系統送出兩則訊息：「存入 50」和「扣款 120，餘額不足則拒絕」。如果 consumer 先看到存入、再看到扣款，這筆扣款成功，餘額剩 30。如果順序顛倒——先看到扣款，此刻餘額只有 100、不足以扣 120，扣款被拒，接著存入 50，餘額變 150。同樣兩則訊息、同樣的處理邏輯，只因為到達次序不同，一個帳戶最後落在 30，另一個落在 150，而且第二種情況下那筆 120 的扣款永遠不會再回來。

這就是訊息順序這件事的全部張力：對某些訊息，**次序本身就是語意的一部分**。可是分散式訊息系統天生就想把訊息打散到多台機器、多條連線、多個 consumer 上平行處理——而平行，正是順序的天敵。這一章要回答的是：在一個想盡辦法並行的系統裡，要怎麼把「同一個帳戶的操作照發生順序到達」這件事釘死，又不至於把整個系統的吞吐鎖死成一條單行道。

## 為什麼「全域有序」是一個你不該許的願

最直覺的想法是：那就讓所有訊息都嚴格照發送順序到達，一個不差。這個保證叫**全序（total order）**——系統裡每一則訊息都有一個明確的、所有 consumer 都同意的先後位置。

問題是它幾乎不可能既要又要。要讓「全系統的每一則訊息」有單一公認的順序，你就需要一個所有訊息都流經的**單一序列化點**——一條誰都繞不過的尾巴，每則訊息在這條尾巴上排隊、領一個遞增的號碼。一旦有了這條尾巴，它就是整個系統的吞吐天花板：不管你後面堆了多少台機器，每秒能處理的訊息數，被這條尾巴一秒能蓋多少個號碼鎖死。你買了一座資料中心，卻只准大家排成一列進門。

更關鍵的是，這個保證**絕大多數時候根本用不上**。回到開場那兩則訊息——它們之所以不能亂序，是因為它們碰的是**同一個帳戶**。但帳戶 A 的存款和帳戶 B 的扣款之間，誰先誰後有差嗎？沒有。它們作用在不相干的狀態上，交換次序不改變任何結果。為了保住 A 內部的順序，而要求 A 和 B 之間、A 和全世界其他幾百萬個帳戶之間都排成一列，是拿幾乎全部的並行度，去換一個你只在極小範圍內真正需要的保證。

所以實務上要的從來不是全序，而是**分區序（partial order）**，更精確地說是**每個鍵（key）內的順序**：同一個帳戶的操作有序、同一個訂單的狀態轉移有序，而不同鍵之間放任它們並行、放任它們亂序。判斷一對訊息要不要有序，有一個乾淨的判準：**「把這兩則訊息的次序對調，結果會不會不一樣？」** 會，它們之間就需要順序；不會，強加順序就是白白付並行度的稅。

這個轉念是整章的地基。它把「保證順序」這個看似要全系統協調的大問題，縮小成一個本地的、可分而治之的小問題：**只要保證同一個鍵的訊息，最後都流經同一條尾巴。** 不同鍵可以有各自的尾巴，彼此平行。鍵越多，尾巴越多，並行度越高——只要每條尾巴內部仍是嚴格有序。

## 順序只能在一條尾巴上保證

把「尾巴」這個詞講白：**順序只能在一個單一序列化點上成立，那個點本質是一段被單執行緒化的 append-only 序列。** 一個 Kafka 的 partition、一條 log、一個 SQS FIFO 的 message group——它們是同一個東西的不同名字：一條只能從尾端追加、且追加有先後的隊伍。寫進去有先後，讀出來也照那個先後。順序不是某個演算法「算」出來的，而是這條尾巴的物理結構**天然就有**的。

於是保住每鍵順序的整個機制，可以濃縮成一句話：**把同一個 key 的訊息，路由到同一條尾巴去。** 怎麼路由？最常見的是對業務鍵取雜湊、再對尾巴的數量取模：

```
partition = hash(key) % partition_count
```

`account_id = "A"` 的所有訊息，`hash("A") % N` 算出來永遠是同一個數，於是永遠落在同一個 partition；`account_id = "B"` 落在另一個（多半不同的）partition。同帳戶的訊息因此被收束到同一條尾巴上、嚴格有序；不同帳戶的訊息散落在不同尾巴、各自平行。Kafka 的 partition key、SQS FIFO 的 message group ID、Kinesis 的 partition key，骨子裡都是這同一套：**用一個鍵把訊息分流到序列化點，鍵相同則尾巴相同。**

這裡藏著一枚硬幣的兩面，值得釘死：**partition 的數量，同時是你的並行度上限，也是你能切出的「獨立有序序列」的數量。** 想要更高吞吐？多開 partition，讓更多尾巴並行。但每多一條尾巴，跨尾巴之間就更無序。「保 partition 內順序」和「用 partition 換並行」不是兩個可以分別最佳化的旋鈕，**它們是同一個旋鈕的兩端**。你沒辦法既要全域有序又要無限並行——這正是上一節「全序的代價」在機制層的回聲。

## 一個 key 選錯，半個系統壓在一條尾巴上

既然路由全靠 `hash(key) % N`，那麼 key 選什麼，就決定了負載怎麼分佈——而這是最容易在設計階段埋雷、上線後才痛的地方。來算一筆具體的帳。

設想一個訂單事件流，你要保證「同一筆訂單的狀態轉移有序」（created → paid → shipped 不能倒）。系統開了 12 個 partition，平均每秒 60,000 則訂單事件。理想情況下，每個 partition 該扛 60,000 / 12 = 5,000 則/秒，均勻。

現在比較兩種 key 的選法。

**選法一：用 `country` 當 partition key。** 直覺上「按國家分區」聽起來很整齊。但流量從來不是按國家均分的——假設 70% 的訂單來自單一個主力市場。`hash("TW") % 12` 是一個固定的 partition，於是這 70%、也就是每秒 42,000 則事件，全部壓在**那一條尾巴**上。這一個 partition 要獨自扛 42,000 則/秒，而它身為一條被單執行緒化的尾巴、只能由 consumer group 裡的**一個** consumer 來消費（下一節會講為什麼）。其餘 11 個 partition 加起來分剩下的 18,000，每個閒到只有約 1,600。你開了 12 條尾巴，真正的瓶頸卻是其中最熱的那一條——這就是 **hot key（熱鍵）傾斜**。partition 數字看起來很充足，實際可用的並行度趴在地上。

**選法二：用 `order_id` 當 partition key。** order_id 的基數（cardinality）極高、且天然均勻——每筆訂單一個獨一無二的 id，`hash(order_id) % 12` 把 60,000 則/秒幾乎完美地灑進 12 個 partition，每個約 5,000，沒有任何一條尾巴特別熱。而我們真正需要的保證——「**同一筆訂單**的事件有序」——絲毫沒有打折：同一個 order_id 的事件雜湊到同一個 partition，照樣嚴格有序。

兩種選法保住的是同一個業務保證，吞吐卻天差地遠。差別只在一件事：**partition key 的基數夠不夠高、分佈夠不夠均勻。** 選 key 的鐵律因此浮現——挑那個「能把你需要的有序範圍切到最細」的鍵。你需要的是「每筆訂單內有序」，那就用 order_id，別用 country；用了 country，等於宣告「整個國家的訂單必須互相排隊」，那是一個你從沒打算許下、卻在選 key 時不小心許下的、貴得離譜的願。

## 為什麼「多開幾個 consumer」救不了一條熱尾巴

承上，熱 partition 最反直覺的地方在於：你**沒辦法靠加 consumer 把它沖散**。理由就埋在「順序只能在一條尾巴上保證」這條原則的另一面。

Kafka 的 consumer group 有一條鐵律：**一個 partition，在同一個 consumer group 裡，同一時刻只能被一個 consumer 消費。** 這不是效能取捨，是順序的**必要條件**——如果一條尾巴上的訊息被分給兩個 consumer 同時處理，這兩個 consumer 一快一慢、一個先 commit 一個後 commit，partition 內辛苦保住的順序，在 consumer 這一端立刻又被打亂了。所以 broker 端的「partition 內有序」要真正傳遞到應用層，就必須一路維持到「一個 partition 對一個 consumer」。

這條鐵律直接推出一個讓很多人意外的結論：**partition 的數量，就是這個 consumer group 並行度的硬上限。** 一個 topic 有 12 個 partition，你最多只能讓 12 個 consumer 同時幹活；起第 13 個 consumer，它分不到任何 partition，只能**乾坐著閒置**——除非某個現役 consumer 掛了，它才會被指派接手。多出來的 consumer 不是備援就是浪費，對吞吐毫無貢獻。

把這兩件事疊起來看，前一節那條熱 partition 的處境就徹底沒救了：它扛著 42,000 則/秒，但只准一個 consumer 處理；你再怎麼往 consumer group 裡塞機器，它們全去搶那 11 條冷尾巴，沒有任何一個能去分擔那條熱尾巴的負載。**唯一的解，是回到上游把 key 選對**，讓負載一開始就別全擠到一條尾巴上。下游加再多機器，都救不了一個上游分流就壞掉的設計——這是訊息順序這個主題裡最容易讓人栽跟頭的因果鏈。

順帶戳破一個常見的「聰明做法」：broker 明明保住了 partition 順序，有人為了快，在 consumer 那端自己起一個 thread pool、把單一 partition 拉到的訊息丟給多個工作執行緒平行處理。一旦這麼做，partition 內的順序在你自己手上就碎了——thread 之間誰先跑完不可控。如果非要在單一 consumer 內並行又保序，得退回到應用層自己按 key 再切一層：同一個 key 的訊息路由到同一個工作執行緒序列化處理，等於在 consumer 內部又造了一批更小的尾巴。順序的責任沒有消失，只是從 broker 搬到了你的程式碼裡，而且搬家途中極容易掉東西。

## 重試怎麼在你背後把順序打亂

到這裡，順序的故事看似完整：選對 key、一個 partition 一個 consumer，就有序了。但有一個更陰險的破壞者藏在你最意想不到的地方——**producer 端的重試**。

設想 producer 要往同一個 partition 連續送兩批訊息：batch 1（含「存入 50」）、batch 2（含「扣款 120」）。為了吞吐，producer 預設允許多批訊息「在途中（in-flight）」同時飛、不必等前一批的 ack 回來才送下一批。現在 batch 1 送出後，broker 那端短暫抖了一下、回了個可重試的錯誤；batch 2 卻順利寫入成功。producer 看到 batch 1 失敗，於是重送 batch 1——可是 batch 2 早就落地了。結果在 partition 這條尾巴上，實際的順序變成了 **batch 2 在前、batch 1 在後**：扣款排到了存款前面。你在上游千挑萬選 key、下游嚴守一個 partition 一個 consumer，順序卻在 producer 的重試裡，無聲無息地翻了個面。

這個坑的根源是「允許多批 in-flight」配上「失敗重送」。最笨的堵法是把 in-flight 限制成 1——一次只准一批在途中，前一批沒 ack 絕不送下一批，重送自然不會插隊。但這等於把 producer 的吞吐勒死，沒人想這樣。

Kafka 的解法漂亮得多，叫 **idempotent producer（冪等 producer，`enable.idempotence=true`，在現代版本已是預設）**。開啟後，broker 給每個 producer 發一個唯一的 **producer ID**，並讓每一批訊息對「每個 partition」帶上一個**單調遞增的 sequence number**。broker 為每個 (producer, partition) 記住「我已經收到的最後一個序號」，於是它能做兩件事：序號重複的批次（重送造成的）直接丟棄不重複寫入（這是冪等、見〈重複是常態〉）；更關鍵的是，broker 認得序號的先後，**只要序號有缺口（batch 2 比還沒補上的 batch 1 先到），broker 就拒收這個批次、回一個 `OutOfOrderSequence` 錯誤**。producer 收到拒收後，把這些被擋下的批次重新排到較新批次之前、依序重送，於是最後落到 log 上的次序仍然正確。換句話說，broker 負責「拿序號把關、認出缺口就擋」，真正「把次序擺正」的重排與重送動作發生在 producer 端——順序的修復不再是 producer 那邊「小心翼翼別讓它亂」靠運氣，而是 broker 把關、producer 照序號補位，兩端合力釘死。

這裡有一個極漂亮、卻幾乎沒人講清楚的細節：開了 idempotence 之後，`max.in.flight.requests.per.connection` **最高可以設到 5、而且仍然保序**。為什麼偏偏是 5？不是隨便挑的吉利數字——是因為 **broker 端對每個 producer 只保留最近 5 個批次的序號狀態來做去重與缺口偵測**（真正的重排重送則在 producer 端、如上一段）。in-flight 的批次數一旦超過 5，最舊的那批序號可能已經滑出 broker 的記憶窗口，broker 就再也無法可靠地判斷「這批是接著哪一批、是不是重複」，保序的保證隨之失效。所以這個 5 是 broker 記憶體裡那個滑動窗口的大小，是個有物理意義的硬邊界，不是約定俗成。順帶一提：要是你**關掉** idempotence、又手癢把 in-flight 設成大於 1，那就退回本節開頭那個悲劇——重試插隊、靜默亂序，而且沒有任何東西會替你擋。

## SQS FIFO：把序列化單位攤在你面前

換到 AWS SQS 的世界，同一套原理換了個皮。SQS 有兩種佇列：Standard 是 at-least-once、best-effort ordering——它根本不承諾順序，訊息可能重複、可能亂序。要順序，得用 **FIFO queue**，而 FIFO 把「序列化單位」這個概念直接攤成一個你必須填的欄位：**message group ID**。

message group ID 扮演的角色，和 Kafka 的 partition key 幾乎一模一樣，但它更誠實——它不藏在雜湊函數背後，而是逼你在每則訊息上**明寫**「這則屬於哪個有序群組」。同一個 group ID 的訊息，SQS 保證嚴格有序、且一次只投遞一則、處理完（刪除）前不投下一則；不同 group ID 之間，完全並行、不保證任何先後。你想保「同一帳戶有序」，就把 `account_id` 設成 message group ID；想要更高並行，就讓 group ID 的基數更高——和 partition key 選 key 的取捨，是同一道題。

Lambda 消費 SQS FIFO 時這層映射看得最清楚：任一時刻，**同一個 message group ID 只會被一個 Lambda 實例處理**（呼應 Kafka 那條「一個 partition 一個 consumer」鐵律），而不同 group ID 可以被多個 Lambda 實例同時處理。序列化的單位是 group，並行的單位也是 group——和 Kafka 對 partition 的處理如出一轍。差別只在 Kafka 的 partition 是你預先開好的固定數量的尾巴，SQS FIFO 的 group 則是按你填的 ID **動態長出來**的、近乎無限多條更細的尾巴。

## 一則卡住的訊息，能餓死它整個群組

SQS FIFO 有一個故障模式，是「嚴格有序」這個保證的必然副作用，卻最常在半夜把人叫醒——**群組內的隊頭阻塞（head-of-line blocking）**。

機制是這樣的：FIFO 為了保證 group 內嚴格有序，規定**同一個 group 裡，前一則訊息沒被成功處理並刪除之前，後面的訊息一律不投遞**。平常這正是你要的——它就是「有序」的實作方式。但設想 group 裡的第一則訊息是一則**毒訊息（poison message）**：內容讓 consumer 每次處理都拋例外、永遠刪不掉。它於是卡在 in-flight 狀態，可見性逾時一到就被重投、再失敗、再重投……而它後面**同一個 group** 的所有訊息，全部被堵在它身後，誰也出不來。一則壞訊息，餓死它整個群組。這不是 bug，是「嚴格有序」與「容忍個別失敗」這兩個目標在邏輯上無法兼得的硬碰撞：你要嚴格有序，就不能跳過卡住的那一則去處理後面的，否則順序就破了。

更刁鑽的是它的波及範圍。SQS 在挑「下一個可投遞的 group」時，只會掃描佇列**前 120,000 則**訊息。如果這 12 萬則裡有若干 group 都被各自的隊頭訊息卡住（in-flight 未刪），那麼排在這 12 萬則**之後**、本來毫不相干、可以正常處理的 group，也**一起被卡在掃描窗口外取不到**。於是一小撮卡住的群組，能讓整條佇列的有效吞吐塌方——明明大部分訊息都好端端的。

這正是死信佇列（DLQ）在順序系統裡不可或缺的原因（見〈死信與毒訊息：DLQ〉）：給每個訊息設一個最大接收次數，反覆失敗的毒訊息被自動挪去 DLQ，**把卡住的隊頭挪開**，它身後那個群組才能繼續流動。順序保證和「一則訊息可能永遠處理不了」這個現實，必須靠 DLQ 來調停——否則嚴格有序遲早會親手把自己餓死。

## 改一次設定，把過去的順序悄悄解體

最後一個故障模式特別惡毒，因為它在你「優化系統」時發生，而且不會報任何錯——**事後增加 partition 數量。**

回想路由公式 `partition = hash(key) % N`。某天流量漲了，你決定把 partition 從 12 擴到 24，想多買點並行度。問題是公式裡的 `N` 變了：對同一個 key，`hash(key) % 12` 和 `hash(key) % 24` 算出來幾乎一定是**不同**的 partition。於是從擴容那一刻起，`account_id = "A"` 的**新**訊息流向了一個新 partition，而它**舊**的訊息還躺在原本那個 partition 裡。同一個 key 的歷史被劈成了兩半，分屬兩條尾巴。

後果是隱形的：一個 consumer 處理舊 partition、另一個處理新 partition，A 的舊事件和新事件由不同的人、以不可控的相對速度處理——A 的全局順序，就此**不再成立**。對需要靠順序重建狀態的系統（event sourcing、CDC 套用、餘額累積），這意味著某些 key 的狀態會被**靜默地**算錯：沒有 exception、沒有 DLQ、沒有任何告警，只是某些帳戶的餘額在某個時間點之後對不上了，而你完全不知道是哪一次「無害的擴容」種下的。

這是為什麼老練的做法是**一開始就刻意超額分區（over-partition）**——按未來幾年的成長預估去開 partition 數，寧可現在每條尾巴閒一點，也不要日後被迫擴容、付出「歷史順序解體」這個查都查不到的代價。partition 數量是個一旦上線就近乎無法安全更改的決定，這層僵固性，正是「順序只能在固定的那條尾巴上保證」這條原則，延伸到運維時間軸上的影子。

## 一個最後的釐清：有序不等於不重複

收尾前要拆掉一個極常見的概念糾纏：**順序和「不重複」是兩個正交的問題，別把它們混成一坨。**

把同一個 key 的訊息送進同一條尾巴、保住它們的先後——這解決的是「次序」。但它**完全沒有**順手解決「同一則訊息會不會來兩次」。一個保 partition 內有序的系統，照樣可能因為 producer 重送、consumer 處理到一半崩潰重啟而把同一則訊息投遞兩次。有序的扣款訊息來了兩次，就是扣兩次款——順序幫不上任何忙。「不重複」要靠冪等與去重來解，是另一套機制（見〈重複是常態：冪等與去重〉）。一句話：**順序管的是「誰先誰後」，冪等管的是「來幾次算一次」。** 一個成熟的訊息消費端，這兩件事都得各自做對，誰也替代不了誰。

## 為什麼是這個形狀

退一步看，整章的樣貌都從一條第一原理長出來：**順序只能在一條被單執行緒化的尾巴上成立。**

正因如此，你不能許「全域有序」的願——那需要一條全系統共用的尾巴，而那條尾巴就是吞吐的死刑。正因如此，實務上要的是每鍵有序，靠 `hash(key) % N` 把同鍵訊息收束到同一條尾巴，於是 key 的基數與分佈直接決定了你的並行度和熱點。正因如此，一條尾巴只能配一個 consumer，partition 數成了並行的硬上限，加機器救不了選錯 key 的熱點。正因如此，producer 的重試會在尾巴上插隊，得靠 broker 拿序號主動排好、而那個「5」是 broker 記憶窗口的物理大小。正因如此，嚴格有序的 FIFO 會被一則毒訊息卡死整個群組，逼出 DLQ 來調停。也正因如此，partition 數一旦定了就改不得——改了，過去那條尾巴上的順序就地解體。

訊息順序不是一套你可以隨手打開的功能開關，而是「在一個拼命想並行的系統裡，硬要保住某些訊息的先後」這個訴求，被物理逼到牆角後唯一站得住的形狀。下次你在設計事件流時停下來問自己「這個 key 該選什麼」，你問的其實是一個藏得很深的問題：我到底需要哪些訊息之間有序，又願意為此放棄多少並行——而這兩件事，是同一枚硬幣的兩面。

## 延伸閱讀

- Apache Kafka, "Producer Configs"（`enable.idempotence`、`max.in.flight.requests.per.connection` 與 ordering 的官方說明）：https://kafka.apache.org/documentation/#producerconfigs
- KIP-679: Producer will enable the strongest delivery guarantee by default（Kafka 3.0 起把 idempotence＋acks=all 設為預設的設計討論；奠基於更早的 KIP-185）：https://cwiki.apache.org/confluence/display/KAFKA/KIP-679
- Aiven, "Does Apache Kafka really preserve message ordering?"（partition、key 與順序保證的邊界）：https://aiven.io/blog/kafka-real-ordering
- AWS, "Using the message group ID with Amazon SQS FIFO queues"：https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagegroupid-property.html
- AWS, "Avoid large message backlogs with the same message group ID"（FIFO 群組隊頭阻塞與 120,000 掃描窗口）：https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/avoid-backlog-with-the-same-message-group-id.html
- Confluent, "Choose and Change the Partition Count in Kafka"（增加 partition 數對 key→partition 映射的影響）：https://docs.confluent.io/kafka/operations-tools/partition-determination.html
