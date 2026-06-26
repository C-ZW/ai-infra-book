# Event sourcing 與 CQRS：狀態是不可變事件序列

先看一個再普通不過的資料表。一個帳戶，有一欄 `balance`，現在是 500。某天客服接到投訴：「我明明存了一筆 100，怎麼餘額沒變？」你打開資料庫，看到 `balance = 500`。然後呢？你能告訴客服這 500 是怎麼來的嗎？它中間有沒有過 600 又被扣回 500？那筆爭議中的 100 到底有沒有進帳、是在哪一步被某個 bug 吃掉的？

你回答不了。因為這張表只存「現在」。每一次 `UPDATE balance = balance + amount`，都把上一個值原地碾過去——前一刻的真相被新的真相覆蓋，不留痕跡。資料庫忠實地記著「此刻餘額是多少」，卻對「它怎麼走到這裡」一無所知。你能做的，頂多是去翻另外一張你**剛好有先見之明**去維護的稽核表（audit log），祈禱它記得夠全、夠準、沒漏掉哪次寫入。

這就是 event sourcing 想翻轉的那件事。它的主張聽起來幾乎是哲學性的：**當前狀態不是你該存的東西，當前狀態是你該「算出來」的東西。** 你真正存下來、當作唯一真相的，是導致這個狀態的那一連串**不可變的事件**——`Deposited(100)`、`Withdrew(30)`、`Deposited(430)`……餘額 500 不是一個被寫進某一欄的值，而是把這些事件**從頭依序套用一遍**得到的結果。歷史不再是你額外維護的副產品，歷史**就是**資料本身。

這個翻轉解掉了開頭那個問題——而且是順帶解掉的。但它也不是免費的午餐，它把「存當前狀態」這件最廉價的事換成了一個會 replay、會膨脹、會在 schema 演進時咬你的系統。要決定值不值得，你得先把這個機制看到能在腦中重放的程度。

## 把 UPDATE 拆成 append

傳統 CRUD 的世界裡，狀態的演化是「就地修改」。一筆轉帳進來，你做的是 `UPDATE accounts SET balance = balance + 100 WHERE id = ?`。這一行 SQL 同時做了兩件事：它**決定**了新的真相（餘額多了 100），也**銷毀**了舊的真相（之前的餘額再也查不到）。決定與銷毀綁在同一個動作裡，這正是歷史會丟失的根源。

event sourcing 把這兩件事拆開。它說：你只能 **append**，不准 **update**，也不准 **delete**。一筆轉帳進來，你寫的是一筆**新的事實**：

```
events table (append-only, 同一個 stream 內嚴格有序)：

  stream_id   version   type            payload
  acct-42     1         Deposited       {"amount": 100}
  acct-42     2         Withdrew        {"amount": 30}
  acct-42     3         Deposited       {"amount": 430}
```

注意這裡每一筆事件的命名都是**過去式**：`Deposited`，不是 `Deposit`；是「已經存了」，不是「請去存」。這個語法上的小講究背後有一個硬約束——事件記錄的是**已經發生、無法反悔的事實**。一個事實不會「過時」，也不會「需要修正」。如果後來發現存錯了金額，你不會回去把那筆 `Deposited(100)` 改成 `Deposited(10)`（那等於竄改歷史），你會 append 一筆**新的**更正事件 `Corrected(...)` 或 `Reversed(...)`。歷史只增不改。會計的世界幾百年來就是這樣運作的——你不會擦掉分類帳上的一行，你會記一筆紅字沖銷——event sourcing 不過是把這個古老的紀律搬進了資料庫。

那「現在餘額多少」怎麼回答？把這個 stream 的事件**從頭 fold 一遍**：

```
state = 0
for event in events(stream="acct-42") order by version:
    state = apply(state, event)
# apply(0, Deposited 100)  -> 100
# apply(100, Withdrew 30)  -> 70
# apply(70, Deposited 430) -> 500
# 結果：500
```

`apply` 是一個純函數：給它「之前的狀態」和「一筆事件」，它回傳「之後的狀態」。把整串事件 fold 過去，就重建出當前狀態。這裡藏著 event sourcing 一個極漂亮的性質——**當前狀態是一個衍生物（derived），不是真相（source of truth）**。你可以隨時把算出來的餘額整個丟掉，再從事件流 replay 一次，得到一模一樣的結果。真相只有一份，就是那串永不變動的事件；其餘的一切都是它的投影。

## 同一串事件能投影出很多種樣子

既然當前狀態只是事件流的一個衍生投影，一個自然的問題冒出來：為什麼只投影成「一個餘額」？

同一串 `Deposited` / `Withdrew` 事件，你可以投影成餘額（給 ATM 看），也可以投影成「每月交易筆數」（給風控看），可以投影成「最近 10 筆交易」（給 App 首頁看），還可以投影成「每日結餘的時間序列」（給對帳和報表看）。**一份事實，多種讀法。** 而且這些讀模型（read model）彼此獨立——風控的需求改了，你重建風控那份投影就好，碰都不必碰餘額那份；明天業務端要一個全新的視角，你拿同一串老事件 replay 一遍就能憑空生出它，連歷史資料都是現成的。

這就自然滑進了 CQRS。CQRS（Command Query Responsibility Segregation，命令查詢職責分離）這個名字由 Greg Young 在 2010 年前後提出與推廣，它的源頭是 Bertrand Meyer 1988 年在《Object-Oriented Software Construction》裡講的 CQS（Command Query Separation，命令查詢分離）原則——一個更微觀的主張：**一個方法要嘛改變狀態（command）、要嘛回報狀態（query），不該兩者都做**（問一個問題不該改變答案）。CQRS 把這個原則從「方法層級」拉高到「整個模型層級」：

- **寫模型（command side）**：負責「改變狀態」。在 event-sourced 系統裡，它接收命令（`DepositMoney`）、驗證業務規則（帳戶沒被凍結嗎？）、然後 append 對應的事件。它為**一致性與正確性**最佳化——它要能原子地檢查不變式、拒絕非法操作。
- **讀模型（query side）**：負責「回報狀態」。它訂閱事件流，把事件投影成一個個為查詢量身打造的、通常反正規化的視圖。它為**讀取效能**最佳化——餘額視圖可能就是一張 key-value 表，一次點查 O(1) 拿到，根本不必每次都 fold。

```
                  ┌──── command side（寫）─────┐
  DepositMoney -> │ validate -> append event   │ -> event store (truth)
                  └────────────────────────────┘         │
                                                          │ (事件流出)
                  ┌──── query side（讀）───────┐          │
  GET balance  <- │ projection: balance view   │ <───────┘
  GET history  <- │ projection: tx-list view   │
                  └────────────────────────────┘
```

這裡要釘死一個常被搞混的點：**CQRS 和 event sourcing 是兩個獨立的東西，只是常常一起出現。** 你完全可以做 CQRS 而不做 event sourcing——寫端照樣存當前狀態的正規化表，只是另外維護一份為查詢最佳化的讀模型，兩者用 CDC（見〈CDC〉）或事件同步。反過來，你幾乎**不可能**做 event sourcing 而不做某種 CQRS——因為一個 append-only 的事件流根本不適合直接拿來查詢（你總不能每次查餘額都 fold 五千筆事件），你被迫得另外建一個讀模型。所以：CQRS 可以單獨用，event sourcing 則幾乎一定拖著 CQRS 一起來。把這兩者當成同一個東西、以為「要用 CQRS 就得把整個狀態翻成事件流」，是過度複雜化最常見的起點。

## replay 一筆都不能少，但五千筆太慢——snapshot 的位置

把當前狀態算出來這件事，聽起來很乾淨，直到 stream 變長。

來算一筆實帳。一個活躍帳戶，三年下來累積了 **5,000 筆**交易事件。每次有人查餘額，純做法是把這 5,000 筆從頭 fold 一遍。假設 `apply` 一筆事件要 **0.02 毫秒**（讀出、反序列化、套用），那麼一次「查餘額」要 5,000 × 0.02 = **100 毫秒**。對一個一秒被查幾千次的端點，這是災難——你把一個本該是 O(1) 點查的操作，變成了 O(事件數) 的全量重算，而且事件數只會**單調成長**：帳戶越老、交易越多，查餘額越慢。這是 event sourcing 最直接的代價——**讀「當前狀態」從 O(1) 退化成 O(歷史長度)。**

解法是 **snapshot（快照）**：每隔一段事件，就把「fold 到這個版本為止的狀態」存下來。比如每 **500 筆**事件存一次 snapshot：

```
event #500   -> snapshot: balance=720,  version=500
event #1000  -> snapshot: balance=310,  version=1000
   ...
event #5000  -> snapshot: balance=500,  version=5000
```

現在查餘額，不從第 1 筆開始 fold，而是**載入最近的 snapshot，再 replay 它之後的那幾筆**。最壞情況下，最近一次 snapshot 在 version 4500，當前是 5000，你只需 fold 後面**至多 500 筆**（一個 snapshot 間距），約 500 × 0.02 = **10 毫秒**。讀取成本從「跟著歷史無限長」降回「跟著 snapshot 間距有界」——這是用空間（存 snapshot）和一點寫入成本（定期算 snapshot）換讀取延遲。

這裡有一個**非顯然、卻致命**的邊界，必須講清楚：**snapshot 是衍生物，不是真相。** 它和讀模型一樣，是事件流的一個快取，可以隨時刪掉、從事件重建。一旦你動了念頭「既然 snapshot 就是當前狀態，那我直接去 `UPDATE` snapshot 不就好了，省得 append 事件」——你就**親手摧毀了 event sourcing 的全部價值**。那一刻起，你的真相不再是事件流，而是一個被就地修改的 snapshot，歷史又開始丟失了。snapshot 必須**只能**從 replay 產生、永遠不被當成權威來源去寫。記住這條判準：在 event-sourced 系統裡，任何「就地 UPDATE」的衝動出現時，幾乎都是設計走歪的信號。

順帶一個對帳的好處，這也是 event sourcing 賣點裡最實在的一個。在「只存餘額」的傳統系統裡，要回答「兩年前某天這帳戶餘額是多少」幾乎做不到——你只有當前的 500，過去的值早被覆蓋。但在 event-sourced 系統裡，這個問題是**免費**的：把事件 replay 到那一天的最後一筆為止，fold 出來的就是當天的餘額。**時光回溯、完整審計軌跡，不是你額外蓋的功能，是這個資料模型的天然副作用。** event sourcing 的核心交換，一句話講完：**用「讀當前狀態變貴」換「歷史與審計變免費」。** 值不值，全看你的領域到底需不需要那段歷史。

## 兩個寫入同時撞上同一個帳戶

append-only 聽起來與並發無關——大家都只是往後加，不會互相覆蓋，哪來的衝突？但 event sourcing 的並發問題藏在一個更隱蔽的地方：**業務不變式（invariant）的檢查，和事件的 append，不是同一個原子動作。**

具體看。規則是「餘額不能變負」。帳戶餘額現在 50。兩個提款請求幾乎同時到達，各要提 40：

```
請求 A: 讀事件、fold 出 balance=50、檢查 40 <= 50 ✓、決定 append Withdrew(40)
請求 B: 讀事件、fold 出 balance=50、檢查 40 <= 50 ✓、決定 append Withdrew(40)
兩者都通過檢查，都 append 成功
-> 事件流：... Withdrew(40), Withdrew(40)
-> fold 出來 balance = -30  ❌ 不變式被破壞
```

兩個請求都基於「餘額 50」這個**過時的快照**做了決定，各自覺得自己合法，append 上去之後一 fold 才發現帳戶透支了。這是經典的讀-改-寫競態，只是穿了 event sourcing 的外衣。

擋它的標準手法是 **optimistic concurrency（樂觀並發）配 expected version**。append 事件時，client 不只說「我要加 `Withdrew(40)`」，還要說「我這個決定，是基於 stream 走到 **version N** 那一刻做的」。event store 在 append 時檢查：這個 stream 現在的 version 真的還是 N 嗎？

```
請求 A: 基於 version 3 決定，append with expected_version=3
        -> store 此刻 version 確實是 3 -> 接受，stream 前進到 version 4
請求 B: 基於 version 3 決定，append with expected_version=3
        -> store 此刻 version 已是 4（A 剛搶先）-> 衝突！拒絕
        -> B 收到 concurrency conflict，必須重讀（現在 balance=10）、
           重新檢查（40 <= 10 ✗）、這次正確地拒絕提款
```

這個「expected_version 不符就拒絕」的機制，本質上是把 stream 的 version 號當成一個 compare-and-swap 的條件（這套樂觀並發的完整推導見〈樂觀與悲觀並發控制〉，事件 append 的去重與冪等則見〈重複是常態〉）。它保證的是：**對同一個 stream，任何時刻只有一個基於最新版本的寫入能成功**，落敗的那個被迫回頭面對新的現實、重新決定。值得注意的是衝突不一定是真衝突——B 失敗後重讀，有時會發現新來的事件其實和它要做的事不相干（A 改的是另一個欄位），這時 B 可以基於新版本重試而非直接報錯；但「餘額」這種共享不變式，重試時就會正確地撞牆。

這裡也順帶劃清一個邊界：optimistic concurrency 保護的是**單一 stream（單一聚合）內部**的不變式。如果你的不變式**跨多個帳戶**（「A 轉給 B，兩邊餘額一起變、要嘛都成功要嘛都不」），那 event store 的 per-stream 版本檢查救不了你——跨聚合的原子性是另一個層級的問題，得靠 saga 補償或把它們塞進同一個 stream 重新建模。event sourcing 不會自動給你跨聚合交易，這是設計聚合邊界時就要想清楚的事。

## replay 會把副作用也重播一遍——除非你攔住它

到目前為止，replay 聽起來是個安全、可隨意重來的操作：把事件 fold 一遍，得到狀態，純函數，無副作用。但這裡藏著 event sourcing 最容易出事、也最反直覺的一個陷阱，Martin Fowler 在他那篇 event sourcing 的奠基文章裡特別點名它。

問題是這樣的：你的事件處理邏輯，**真的純嗎**？假設處理 `OrderPlaced` 事件時，你的程式碼不只更新內部狀態，還順手「寄一封確認信給客戶」「呼叫金流去扣款」。第一次處理時，這完全正確。但 event sourcing 的核心承諾是「你可以隨時 replay 整串事件來重建狀態」——那麼當你某天為了重建一個壞掉的讀模型，把三年來的 `OrderPlaced` 全部 replay 一遍時，會發生什麼？

**每一個客戶會再收到一封三年前那筆訂單的確認信。每一筆款會被再扣一次。** 外部系統分不出「這是真實處理」還是「這是 replay 重建」——對它們而言，一個 `sendEmail()` 呼叫就是一個 `sendEmail()` 呼叫。replay 把本該是純粹內部重算的操作，變成了向真實世界發射的散彈。

這逼出一條 event sourcing 的鐵律：**replay 期間，所有對外的副作用必須被抑制。** fold 出狀態（純內部計算）是 replay 該做的；觸發外部動作（寄信、扣款、發訊息）不是。實作上，外部系統的呼叫要被包進一個能分辨「live 模式」和「replay 模式」的 gateway——live 時真的呼叫，replay 時跳過。換句話說，你必須把「重建狀態」和「對世界產生影響」這兩件事在程式碼層面**徹底分開**，否則每次 replay 都是一場災難。

這個陷阱還有一個更隱蔽的孿生版本：**replay 時去查外部系統的「當前值」。** 如果處理某個舊事件時，你的邏輯會去問「這個商品現在的價格是多少」，那麼三年後 replay 這筆事件，查到的是**今天**的價格，不是當年那筆訂單成立時的價格——replay 出來的歷史就失真了。Fowler 給的解法很乾脆：把當時查到的外部回應**也記進事件裡**。事件要**自足**——它應該包含「當時發生了什麼」所需的一切值，而不是存一個「指向會變動的外部資料的引用」。一筆 `OrderPlaced` 事件該記下成交當下的價格 `price: 99`，而不是只記 `productId`、replay 時再去查現價。事件是凝固在時間裡的事實，任何會隨時間漂移的引用，都會讓你的歷史在 replay 時悄悄改寫自己。

## 那些永遠不會消失的舊事件

傳統資料表改 schema，是一次性的：跑個 migration，把 `ALTER TABLE` 一執行，舊的列就地變成新格式，過去的格式從此不存在。event sourcing 沒有這種奢侈——因為**舊事件永遠在那裡，而且永遠不能改。**

想像你三年前定義的 `Deposited` 事件長這樣：`{"amount": 100}`。後來業務要支援多幣別，新的事件變成 `{"amount": 100, "currency": "TWD"}`。問題來了：那串三年前的老事件，裡面**沒有** `currency` 欄位，而它們是不可變的事實、你不准回去改。當你 replay 到那些老事件時，你的 `apply` 函數讀到一個缺 `currency` 的 payload，怎麼辦？

你不能去改老事件（竄改歷史、且它們可能已經被別的讀模型、別的下游消費過了）。標準解法叫 **upcasting**：在**讀取**老事件、餵給 `apply` 之前，先經過一個轉換函數，把舊格式「升級」成當前格式——讀到沒有 `currency` 的老事件，就在記憶體裡補上一個預設值 `currency: "TWD"`，再交給 `apply`。事件在磁碟上原封不動，只是被讀進來的瞬間穿了一件新衣服。

```
on read:  raw_event(v1, no currency) -> upcaster -> event(v2, currency=TWD) -> apply
on disk:  raw_event(v1) 永遠不變
```

這聽起來優雅，但有一個會慢慢長出來的代價：**upcaster 只增不減。** v1→v2 加了一個，v2→v3 又加一個，五年後你可能有一疊 upcaster，每次載入老 stream 都要依序穿過整條升級鏈。這是 event-sourced 系統長期維護裡最磨人的地方——你的事件格式演進史，會以 upcaster 鏈的形式永遠掛在系統裡，誰也不敢刪，因為總有某個塵封三年的老帳戶，stream 裡還躺著最古早那版事件。

這就是為什麼「事件 schema 設計」在 event sourcing 裡份量遠超傳統 schema 設計。傳統表的 schema 是「當前的形狀」，改了就改了；事件的 schema 是「歷史上所有曾經存在過的形狀的總和」，你做的每一個事件結構決定，都會跟著你到系統的盡頭。設計事件時要刻意求穩、求自足、求向後相容（這套「向後相容地演進序列化格式」的紀律見〈序列化與 schema 演進〉），因為你寫下的不是一個可以明天反悔的表結構，而是一份**永久檔案**。

## 事件怎麼從寫端流到讀端

寫模型 append 了事件，讀模型要更新——這兩者之間隔著一條必須**可靠**的管線。如果這條管線丟了一筆事件，讀模型就和真相永久偏離；如果它漏處理了一筆，餘額視圖就錯了。這條管線怎麼搭，決定了整個 CQRS 系統的一致性品質。

最樸素也最危險的做法是「append 事件之後，順手去更新讀模型」——也就是在同一段程式碼裡，先寫事件、再寫讀模型。這正是 dual-write 問題：兩個寫入沒有共同的交易邊界，第一個成功、第二個失敗（行程在中間崩了），你就有了一筆永遠不會反映到讀模型的事件。可靠的做法是把事件當成唯一的真相先落地，再讓讀模型**訂閱**這個已落地的事件流去自己更新——常見手段是 outbox（事件與業務狀態在同一個交易裡寫出，再由一個 relay 可靠地搬給下游，見〈跨服務的交付一致〉），或從 event store 的 log 直接訂閱，或用 CDC 從事件表的變更日誌擷取（見〈CDC〉）。關鍵是：讀模型的更新必須由「事件已經是事實」這件事**驅動**，而不是和寫事件擠在同一個不可靠的雙寫裡。

而這條管線是非同步的，於是 CQRS 系統繼承了一個無法迴避的性質——**讀模型是最終一致的**（見〈一致性光譜〉）。使用者剛存了 100，命令成功了，但他立刻刷新 App 看到的餘額**可能還是舊的**——因為那筆 `Deposited` 事件還在從寫端流向讀端的路上，餘額投影還沒追上。這就是「讀己之寫」（read-your-writes）破掉的瞬間（見〈複製延遲與讀己之寫〉）。你有兩條路應對：要嘛接受它、在 UI 上樂觀地先顯示「處理中」；要嘛對這種關鍵讀取繞過讀模型、直接從寫端 fold 出當前狀態回給使用者。但你**不能假裝**讀寫是即時一致的——那個延遲視窗是 CQRS 的結構性特徵，不是你能調掉的 bug。

## Kafka 的 log 看起來像 event store，但有個陷阱

Kafka 的 partition 本質上就是一個 append-only、嚴格有序的 log（見〈Kafka〉），這個形狀和 event store 像到讓很多人直接拿 Kafka 當事件儲存。在很多場景這確實合理——log 天然有序、可重放、扛得住高吞吐。但這裡有一個會吃掉你歷史的設定陷阱，必須講清楚。

Kafka 的 topic 有一個 retention（保留）策略。預設的「依時間刪除」會在事件超過保留期後**把它們刪掉**——對一個普通的訊息佇列這很合理（老訊息沒人要了），但對 event store 這是**災難**：你的真相被定時清掉了，再也 replay 不出完整歷史。要拿 Kafka 當 event store，你得把 retention 設成無限（或極長），讓 log 永遠不刪。

更隱蔽的是另一個選項：**log compaction（日誌壓縮）**。compaction 的行為是「對每個 key，只保留最後一筆值」——它會把同一個 key 的所有舊事件**丟掉**，只留最新的那筆。這對「我只在乎每個實體的當前狀態」的場景很省空間，但它和 event sourcing 的核心**直接衝突**：event sourcing 要的就是**每一筆中間事件**，`Deposited(100)`、`Withdrew(30)` 一筆都不能少，因為當前狀態是把它們全部 fold 出來的。一旦開了 compaction，中間事件被壓掉，你就只剩下「最後一筆」，fold 不出正確的餘額，審計軌跡也斷了。**compaction 保留的是「最終狀態」，event sourcing 需要的是「完整過程」——這兩件事南轅北轍。** 拿 Kafka 當 event store 時，這個 topic 必須是非 compacted、長（或無限）retention 的；專用的 event store（如今天已從 EventStoreDB 改名為 KurrentDB 的那一類，2026-06）之所以存在，部分原因正是它們把「事件永不丟、有序、可依 stream 讀回、原生 optimistic concurrency」這些 event sourcing 的硬需求做成了預設，而不是要你在一個通用 log 上小心翼翼地避開那些會刪資料的開關。

## 大多數系統不該碰它

把上面的代價列一遍——讀當前狀態退化成 replay、要維護 snapshot、要抑制 replay 副作用、事件要自足、upcaster 鏈只增不減、讀模型最終一致、不能就地修改任何東西——你會發現 event sourcing 不是一個「比較進階」的 CRUD，它是一套**完全不同的、更難的**資料管理紀律。它買到的東西很特定：完整不可變的審計軌跡、時光回溯、一份事實餵多種視圖。它要的代價很實在：上面那一整包複雜度，外加一條陡峭的學習曲線。

所以判準應該很保守。Fowler 對 CQRS 的措辭罕見地謹慎——「對大多數系統，CQRS 增加的是有風險的複雜度」，他建議只在系統的**特定區塊**（透過 bounded context 劃出的一小塊）用它，而非全系統套用，而真正適合的場景「是極少數」。event sourcing 更是如此。問自己兩個問題就夠：

第一，**「我真的需要每一次變更的完整、不可變、可追溯的歷史嗎？」** 金融帳務、醫療紀錄、法遵要求「每筆變更都要留痕、不可竄改」的領域——是，這時 event sourcing 不只值得，它幾乎是這類需求的天然形狀，你想擦掉的歷史正是它監管要你保留的。但一個內容管理後台、一個設定面板、一個普通的 CRUD 業務——你存的東西改了就改了、沒人會問「上週二下午三點這個值是多少」——那段歷史對你毫無價值，而你卻要為它付全部的複雜度。

第二，**「我的讀寫負載與型態，是否嚴重不對稱到單一模型很痛？」** 讀爆量、查詢花樣百出、寫入相對簡單——是，那 CQRS（**未必要配 event sourcing**）能讓讀寫各自最佳化、各自擴展。但讀寫對稱、量也不大的系統，硬拆成兩個模型只是憑空多養一套同步管線和一個最終一致的視窗。

兩個問題都答「否」，就別碰。對絕大多數系統，「存當前狀態，外加一張稽核表」這個樸素組合，已經涵蓋了你真正需要的歷史，而且便宜得多。event sourcing 是這個領域裡**最常被濫用**的模式之一——它在簡報上很美（不可變！可回溯！完整審計！），但那些形容詞背後是你每天都要扛的維護成本。

## 為什麼是這個形狀

退一步看，event sourcing 的整個樣貌，都是從拒絕一件事長出來的：**它拒絕「就地覆蓋」。**

正因為不准 update、只准 append，歷史才得以完整保存——這是它全部好處（審計、回溯、多視圖）的唯一來源。也正因為當前狀態不再被直接存著、而要從事件算出來，讀取才退化成 replay、才需要 snapshot 來救——這是它全部代價的唯一來源。它的每一個性質，無論是禮物還是負擔，都可以一路追溯回「狀態是不可變事件序列」這一個根本選擇。CQRS 跟著來，是因為一個只能 append 的事件流先天不適合查詢，逼你把「改」和「讀」拆成兩個各自為政的模型。replay 必須抑制副作用、事件必須自足、upcaster 只增不減——這些看似零碎的鐵律，全是「歷史不可變」這個前提在不同角落投下的影子。

所以 event sourcing 不是一個任意的架構流行語，它是「**如果你決定把歷史本身當作真相、而非把當前狀態當作真相**」這個選擇，被一路推到底之後，唯一站得住的形狀。下次你在一個系統裡看到 append-only 的事件表、看到背景在跑 projection、看到有人為了重建讀模型而小心翼翼地把外部呼叫關掉——你會知道那不是有人在炫技，那是這個選擇在兌現它的承諾：開頭那個帳戶的 500，永遠回答得出它是怎麼來的。

## 延伸閱讀

- Martin Fowler, "Event Sourcing"（奠基文章，含 replay 與外部系統互動、snapshot、external query 的經典討論）：https://martinfowler.com/eaaDev/EventSourcing.html
- Martin Fowler, "CQRS"（含「對大多數系統是有風險的複雜度」的著名警示）：https://martinfowler.com/bliki/CQRS.html
- Greg Young, "CQRS Documents"（命名者本人的權威整理，PDF）：https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf
- Bertrand Meyer, *Object-Oriented Software Construction*（1988，CQS 命令查詢分離原則的原典）：https://en.wikipedia.org/wiki/Command%E2%80%93query_separation
- Microsoft, "Event Sourcing pattern"（Azure Architecture Center，含投影、snapshot、一致性取捨的工程整理）：https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing
- Confluent, "Log Compaction"（Kafka 官方文件，理解為何 compaction 與 event sourcing 的完整歷史需求相衝突）：https://docs.confluent.io/kafka/design/log_compaction.html
- KurrentDB（原 EventStoreDB）官方文件（專用 event store 的 stream、optimistic concurrency、projection 機制）：https://docs.kurrent.io/
