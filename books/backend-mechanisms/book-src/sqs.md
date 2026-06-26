# SQS：Standard 與 FIFO

一個 worker 從佇列拉到一則訊息——「給訂單 #4471 寄出貨通知」——開始處理。它呼叫郵件服務、等了兩秒、信送出去了，正準備回頭把這則訊息標記為「處理完畢」，這時這台機器被部署滾動更新殺掉了。訊息沒被刪。三十秒後，另一台 worker 拉到了同一則訊息，又寄了一次。同一個客戶，收到兩封一模一樣的出貨通知。

這一幕不是 bug，是 Amazon SQS 的**設計**。要看懂 SQS——看懂它為什麼幾乎一定會重複投遞、為什麼還是無數系統的預設選擇、以及它的兩種佇列各自買到什麼、賠掉什麼——得先看懂它在最底層做了一個什麼決定：**它把「刪除訊息」這個動作，交到了消費者手上**。這個看似不起眼的設計選擇，是後面所有保證與所有坑的源頭。

## 一個沒有 push 的佇列

先把這東西的形狀講清楚。SQS 是全託管的分散式訊息佇列：producer 呼叫 `SendMessage` 把訊息寫進去，consumer 呼叫 `ReceiveMessage` 把訊息拉出來。注意是「拉」——SQS **沒有 push 模型**，它不會主動把訊息推給你的 server，是你的 worker 自己去問「有沒有東西給我做」。這個 pull 的形狀有它的好處：消費端天然有背壓（見〈背壓〉），你拉得多快、處理得多快，完全由你決定，下游永遠不會被上游灌爆。

但 pull 帶來一個立刻要面對的問題：**訊息什麼時候該從佇列裡消失？**

最天真的做法是「一拉走就刪」。consumer 一呼叫 `ReceiveMessage`，SQS 就把訊息從佇列移除。乾淨俐落——但這正是開場那台機器若採用此法會發生的災難的**相反面**：worker 拉到訊息、刪掉、然後在寄信前崩潰，訊息就此蒸發，這個客戶**永遠收不到通知**，而且沒有任何痕跡。這叫 at-most-once：最多送一次，但可能一次都不送。對「寄出貨通知」這種事，悄悄漏掉一筆，比重複寄一封糟糕得多。

另一個極端是「等 consumer 明確說處理好了，才刪」。這就對了——但它逼出一個新問題：**從 consumer 拉走訊息、到它說「我處理完了」之間，這段時間裡，這則訊息算什麼狀態？** 如果它還留在佇列裡可見，那麼第二台 worker 會立刻也拉到它，兩台同時處理同一則訊息。如果它消失了，那 consumer 萬一中途崩潰，訊息就再也回不來了。

SQS 對這個兩難的答案，是一個叫 **visibility timeout（可見性逾時）** 的機制。整個 SQS 的交付語意，都長在這個機制上。

## visibility timeout：被借走的訊息

當一個 consumer 呼叫 `ReceiveMessage` 拉到一則訊息，SQS **不刪它**，而是把它變成「in-flight（傳輸中）」狀態——這則訊息暫時對**其他**consumer 隱形，隱形的時長就是 visibility timeout，預設 **30 秒**，可設成 0 秒到 12 小時之間（2026-06）。

把它想成圖書館借書，但有一個關鍵的不同：你借走的不是書本身，是書的一份影本，原書還在架上、只是被蓋了一塊「已借出」的布。在借期內，別人看不到它。接下來有兩條路：

- 你在借期內處理完，呼叫 `DeleteMessage`——這才是真正把訊息從佇列移除。書還掉、原書下架、結束。
- 你**沒有**在借期內刪它——可能是處理太慢，可能是你崩潰了。借期一到，那塊「已借出」的布自動掀開，訊息**重新變得可見**，下一個來問的 consumer 就會拿到它。

```
t=0    consumer A 呼叫 ReceiveMessage，拿到 msg
       msg 進入 in-flight，對其他 consumer 隱形（visibility timeout = 30s）
t=2    consumer A 處理完，呼叫 DeleteMessage → msg 真正消失
       （正常路徑結束）

—— 但如果 consumer A 在 t=2 之前崩潰、沒呼叫 DeleteMessage ——

t=30   visibility timeout 到期，msg 自動重新可見
t=31   consumer B 呼叫 ReceiveMessage，拿到「同一則」msg → 重複處理
```

這張圖就是 SQS 全部祕密的一半。**刪除是主動的、是消費者的責任；沒成功刪，就會重投。** 這直接導出 SQS Standard 佇列的核心保證：**at-least-once delivery（至少投遞一次）**。每則訊息保證至少被投到一次（不會像 at-most-once 那樣靜默丟失），但**可能被投不只一次**——只要有任何一次「拉走了、但沒在借期內刪掉」，就會重投。開場那兩封出貨通知，就是這麼來的：第一台 worker 信寄了、訊息卻沒刪成（它在刪之前就死了），於是借期一到，第二台接手、又寄一次。

理解了這個，你也就理解了一條鐵律：**用 SQS（Standard）的 consumer，處理邏輯一定要冪等。** 因為重複不是異常、是常態，handler 必須能安全地把同一則訊息處理第二次而不造成第二次副作用（冪等鍵怎麼設計、去重視窗怎麼維護，是另一個主題，見〈重複是常態〉）。SQS 自己不替你去重，它只負責「至少送到」，「不重複生效」是你的事。

## 借期設多長：一個容易設錯的旋鈕

visibility timeout 看起來只是一個數字，但它設錯會以兩種相反的方式咬你，值得停下來想清楚。

設**太短**是最常見、也最隱蔽的坑。假設你的訊息平均要處理 45 秒，但 visibility timeout 還是預設的 30 秒。會發生什麼？consumer A 拉到訊息、認真處理到第 30 秒——這時借期到了，訊息重新可見，consumer B 拉到它、開始處理**同一則**。現在你有兩台機器在平行做同一件事。如果這件事是「扣一次款」，你就 double-charge 了。最陰險的是，consumer A 並不知道自己的「借期」已經過期——它做完 45 秒的活、開開心心呼叫 `DeleteMessage`，SQS 接受了（刪一個已經被別人重新拿走的訊息不會報錯），於是 A 自以為一切正常。表面風平浪靜，底下訊息已經被做了兩次。

設**太長**的代價比較溫和但也真實：如果 consumer 真的崩潰了，訊息得等滿整個借期才會重新可見、才能被別人接手。借期設 12 小時，一台 worker 死了，它手上那則訊息就要積壓 12 小時才會被重試——對時效敏感的工作，這是不可接受的延遲。

務實的做法有兩種。一是把 visibility timeout 設成「處理時間的合理上界」——比如 p99 處理時間再加一段緩衝。二是對「處理時間變動很大、無法預估」的長任務，用 `ChangeMessageVisibility` **在處理途中續租**：worker 處理到一半，發現還要久，就主動延長這則訊息的借期，像續借圖書一樣。這比一開始就把借期設得很長更精細——正常的訊息很快歸還，只有真正在處理中的訊息才持續佔用借期。

順帶一提：in-flight 的訊息數量本身有上限——Standard 與 FIFO 佇列都是 **120,000 則**（FIFO 在 2024-11 才從原本的 20,000 提上來）。超過這個數，再 `ReceiveMessage` 會收到 `OverLimit` 錯誤。這個數字平常碰不到，但如果你的 consumer 大面積卡住（處理不完、又沒刪、借期又長），in-flight 會堆積，堆到上限就連新訊息都拉不出來了——一個慢消費者最終會把整條佇列鎖死。

## Standard：用「會重複、會亂序」換近乎無限的吞吐

到這裡，Standard 佇列的全貌就清楚了。它給你三件事：

第一，**近乎無限的吞吐**。Standard 佇列對 `SendMessage`／`ReceiveMessage`／`DeleteMessage` 的每秒呼叫數幾乎沒有上限（AWS 官方用詞就是「nearly unlimited」），它在背後自動水平擴展、把你的訊息散佈到大量的分散式儲存節點上。你不必預估流量、不必預先佈建容量。

第二，**at-least-once delivery**——剛剛講透的那個，刪除是主動的、沒刪就重投。

第三，**best-effort ordering**。注意這個措辭：SQS Standard **不保證順序**。它會「盡量」按你送進去的順序投遞，但因為訊息被打散在許多節點上平行處理，先送進去的訊息**可能後出來**。

而這三件事是同一個設計決定的三個面向，這是看懂 Standard 的關鍵。為什麼能近乎無限吞吐？正是因為它**放棄了全域順序**——它不需要維護「哪則訊息該排在哪則前面」這種跨節點的協調，每個節點各幹各的，所以能無限平行。順序和吞吐在這裡是直接對立的：你要全域有序，就得有某種集中協調來排隊，那就有了瓶頸；你放棄有序，就解開了協調，吞吐才能無上限。Standard 選了後者。同理，「可能重複」也部分源於這種無協調的平行性——當儲存被打散、`ReceiveMessage` 從多個副本拉取，偶爾把同一則訊息投兩次比建立一個全域去重機制要便宜得多。

所以 Standard 不是「一個有 bug、偶爾會亂序會重複的佇列」，而是「一個**刻意**用亂序與重複換取無限吞吐的佇列」。它適合的場景非常明確：工作之間彼此獨立、誰先誰後無所謂、且 consumer 本來就該冪等的非同步任務——寄信、轉檔、產縮圖、發 webhook。這類工作佔了訊息佇列用途的絕大多數，這也是 Standard 是預設選擇的原因。

## 當順序真的不能亂：FIFO 是另一筆交易

但有些工作，順序就是不能亂。同一個帳戶的「開戶 → 入金 → 提款」三筆指令，如果亂序成「提款 → 開戶 → 入金」，第一筆就會對一個還不存在的帳戶提款。對這種場景，best-effort 不夠，你需要**嚴格有序**。SQS 的答案是 **FIFO 佇列**，它是和 Standard 完全不同的一筆交易。

FIFO 給你兩個 Standard 沒有的保證：

**strict ordering（嚴格先進先出）**——但有一個關鍵的限定詞，這個限定詞是理解 FIFO 全部行為的鑰匙：順序保證是**在同一個 message group 內**成立的，不是整條佇列。

**exactly-once processing（恰好處理一次）**——同樣有限定：是在一個 **5 分鐘的 deduplication window（去重視窗）** 內，靠 deduplication ID（去重識別碼）達成。

先講 message group，因為它是 FIFO 最常被誤解、也最決定性能的東西。

## message group：FIFO 的有序與並行單位

每一則送進 FIFO 佇列的訊息，都**必須**帶一個 `MessageGroupId`（沒帶的話 `SendMessage` 直接失敗）。SQS 用這個 ID 把訊息分成一個個「有序群組」。規則是這樣：

- **同一個 message group 內**，訊息嚴格按送入順序投遞，而且——這點至關重要——**同一時刻，一個 message group 只會有一則訊息在被處理**。你拉走了 group A 的第一則訊息，在你刪掉它之前，SQS **不會再把 group A 的任何訊息**給任何人。group A 在你手上時，對整個世界是「鎖住」的。
- **不同 message group 之間**，完全並行、互不相干。group A 的訊息卡住，不影響 group B 照常流動。

這個設計很巧妙：它讓你用 message group ID 來**畫定「哪些訊息必須有序」的邊界**。把同一個帳戶的所有指令都標上 `MessageGroupId = "account-4471"`，這個帳戶的指令就嚴格有序、一筆一筆來；不同帳戶用不同的 group ID，彼此並行，互不拖累。message group 既是**順序的單位**，也是**並行的單位**——你有多少個活躍的 message group，就有多少個可以平行處理的「車道」。

但這個設計有一個立刻浮現、且咬人很痛的後果。

## 隊頭阻塞：FIFO 最該知道的那個坑

既然「同一個 message group 同時只有一則訊息在處理、處理不完別人拿不到下一則」，那麼想想：如果 group A 的第一則訊息**處理失敗、又一直沒被刪掉**，會發生什麼？

group A 整個**堵死**。那則失敗的訊息會反覆地：被拉走、處理失敗、沒刪、借期到期、重新可見、又被拉走……而排在它後面的 group A 訊息，**全部動彈不得**，因為 FIFO 的承諾就是「前一則沒處理掉，後一則不准出來」。這叫**隊頭阻塞（head-of-line blocking）**——一則毒訊息（poison message）卡在隊頭，後面整個群組陪葬。

這和 Standard 形成尖銳的對比。在 Standard 裡，一則處理不了的訊息只是它自己反覆重試，旁邊的訊息照流；在 FIFO 裡，它會把整個 message group 拖住。所以 FIFO 佇列**幾乎一定要配 DLQ（死信佇列）**：設一個 `maxReceiveCount`，讓那則毒訊息被重試到一定次數後自動移進死信佇列、把隊頭讓出來，後面的訊息才能繼續（DLQ 的機制見〈死信與毒訊息：DLQ〉）。沒配 DLQ 的 FIFO 佇列，遇到一則處理不了的訊息，就是一個會無限期卡住整個群組的定時炸彈。

隊頭阻塞還有一個更隱蔽的變體，連 AWS 文件都得專門說明。FIFO 佇列在決定「現在該給 consumer 哪些訊息」時，只會往佇列的**前 120,000 則**裡看，找出沒被鎖住的 message group。如果這前 12 萬則訊息所屬的 group **全都**因為各自有 in-flight 訊息而被鎖住了，那麼即使佇列裡第 120,001 則之後有別的、完全空閒的 group 的訊息，**也拉不出來**。換句話說，少數幾個卡住的 group，可能在「視野」上擋住後面所有原本可以平行處理的 group。這是把 message group 設計得太粗（活躍 group 太少、每個 group 太長）時會踩到的擴展性陷阱——group 的數量和分佈，直接決定了 FIFO 佇列實際能跑多平行。

## exactly-once processing 的真相：它只是把去重內建了

現在講 FIFO 的第二個賣點——exactly-once processing——以及為什麼這個詞每個字都要小心讀。

機制是這樣：每則送進 FIFO 佇列的訊息可以帶一個 **deduplication ID**。在 5 分鐘的去重視窗內，如果 SQS 已經接受過一則帶有相同 deduplication ID 的訊息，那麼後續任何帶相同 ID 的訊息會被「接受但不投遞」——SQS 收下你的請求、回你成功，但不會真的把這則重複的訊息放進佇列。deduplication ID 可以你自己給（比如用業務上的唯一鍵），也可以開啟 content-based deduplication，讓 SQS 用訊息**內容**的 SHA-256 雜湊自動產生。

這解決了一個非常具體的問題：**producer 端的重送重複**。設想 producer 呼叫 `SendMessage`，網路抖了一下、回應沒收到，producer 不知道訊息到底進去了沒，於是重送。如果沒有去重，這則訊息就進了佇列兩次。有了 deduplication ID，producer 大可放心重送——只要在 5 分鐘窗內、帶同一個 ID，SQS 會認出「這則我收過了」，第二次默默吞掉。所以這個機制讓 **producer 的重試變得安全**（這正是 at-least-once 系統裡 producer 該有的行為：沒收到 ack 就重送）。

但「exactly-once **processing**」這個詞裡，最關鍵的是它**不是** exactly-once **delivery**。它沒有、也不可能保證一則訊息在物理上「只被投遞一次、只被處理一次」。為什麼？因為 consumer 端的重複，跟 producer 端的去重是兩回事。回想 visibility timeout：consumer 拉走一則訊息、處理了 40 秒、然後在刪之前崩潰——這則訊息會在借期到後重新可見、被重新投遞。FIFO 的去重視窗管不到這個，因為這不是「同一個 deduplication ID 被送了兩次」，而是「同一則訊息因為沒刪成而被重投」。consumer 崩潰造成的重複處理，FIFO 一樣會發生。

而且去重視窗只有 **5 分鐘**。如果你的兩次重送間隔超過 5 分鐘——比如一則訊息處理失敗、半小時後一個重試批次又送了一次同樣的——去重視窗早就忘了第一次，第二次會被當成全新訊息放進去。

所以 FIFO 的 exactly-once processing 該被理解成：**它幫你內建了一層「producer 端、5 分鐘窗內」的去重，省掉你自己維護一張去重表的麻煩。** 它是一個方便、好用的局部保證，不是「端到端只執行一次」的魔法。任何有真實副作用的 consumer，**仍然必須冪等**——FIFO 縮小了你需要自己處理的重複窗口，但沒有消滅它（端到端去重與冪等的完整討論見〈重複是常態〉）。

## FIFO 的吞吐天花板：有序的代價

天下沒有白吃的午餐，FIFO 為「有序」付的代價，直接寫在它的吞吐數字上，而且這個代價大到會反過來決定你的架構。

Standard 是近乎無限吞吐；FIFO **不是**。FIFO 的吞吐是有明確上限的，而且這個上限不是按「訊息」算、是按 **API 請求**算。預設情況下，整條 FIFO 佇列共用每秒 **300** 個非批次操作、或 **3,000** 個批次操作（一個批次最多打包 10 則訊息）的額度。

這裡藏著一個讓很多人意外的限制：**預設的 300/3,000 是整條佇列共用的，不是每個 message group 各自 300**。你開一千個 message group，它們仍然分食同一份 300 TPS 的餅。要讓 message group 真正各自獨立擴展，必須開啟 **high throughput mode**（把 `FifoThroughputLimit` 設成 `perMessageGroupId`，並把去重範圍設成 message group 級）。開啟後，額度改為按 partition 計算——每個 partition 各自 300（非批次）／3,000（批次），SQS 在背後把你的 message group 散佈到多個 partition 上。它是用 message group ID 的 hash 來決定每個 group 落在哪個 partition，所以 group 的數量夠多、分佈夠均勻，才填得滿多個 partition——這也是 high throughput 下仍要避免「少數熱門 group 吃掉大半流量」的原因。在主要 region（如 us-east-1、us-west-2、eu-west-1），high throughput FIFO 可以達到約 **70,000 訊息/秒**（批次模式下更高，且這個數字隨 region 變動，引用時該標明 region，2026-06）。

把這條算術走一遍，「為什麼有序這麼貴」就具體了。假設你需要每秒處理 30,000 則有順序要求的訊息。在 Standard，這完全不是問題——近乎無限吞吐，30,000 TPS 隨便跑，但你拿不到順序。在 FIFO 預設模式，整條佇列頂多 3,000 則/秒（批次），離 30,000 差了一個數量級，根本不夠。你**必須**開 high throughput mode，並且——這是關鍵——你的訊息**必須分佈在夠多的 message group 上**，SQS 才能把它們散到多個 partition 去平行。如果你的 30,000 則訊息全用了同一個 `MessageGroupId`（比如圖省事，全標成 `"default"`），那麼不管你開不開 high throughput mode，它們全擠在一個有序群組裡、只能一則一則來，你的有效吞吐會被死死壓在單一群組的速度上，30,000 TPS 是天方夜譚。

這就推導出 FIFO 設計的核心張力：**順序的粒度，和吞吐的上限，是同一個旋鈕的兩端。** message group 切得越細（越多獨立群組），可平行的 partition 越多、吞吐越高，但你能保證有序的範圍就越小（只在每個小群組內有序）。message group 切得越粗（越少群組、每群越大），有序的範圍越大，但平行度越低、吞吐越被壓縮。你選 message group ID 的方式，本質上就是在這條線上選一個點：你到底需要**多大範圍**的有序？通常答案是「同一個實體（帳戶、訂單、使用者）內有序就夠了」——於是用實體 ID 當 message group ID，既拿到了業務上需要的有序，又讓不同實體之間能盡量平行。把有序的範圍畫得比業務真正需要的更大，就是在白白犧牲吞吐。

## 大訊息與一個悄悄變了的數字

有一個 SQS 的數字，很多既有系統的假設仍停在舊值上，值得單獨點出來，因為它會直接決定架構。

SQS 單則訊息的 payload 上限，**現在是 1 MiB（1,048,576 bytes）**（2026-06）。但這個數字長期以來是 **256 KiB**——AWS 在 **2025-08-04** 才把上限從 256 KiB 提升到 1 MiB（Standard 與 FIFO 都適用，所有商用 region 生效）。也就是說，在 2025 年 8 月之前，「SQS 最大 256 KB」是**完全正確**的——是世界後來變了，不是誰一直記錯。如果你的程式碼裡還在 250 KB 處硬切分訊息、或假設超過 256 KB 就一定要走 S3，那段邏輯現在可能是多餘的；反過來，有些舊版 SDK 或前置驗證可能還沒更新到 1 MiB，曾出現「伺服器端接受 1 MiB、但 client SDK 仍按 256 KiB 報錯」的情況——升限後該以官方 quotas 文件為錨、並實測你手上 SDK 的版本。

那超過 1 MiB 怎麼辦？SQS 的官方解法是 **Extended Client Library**：把真正的大 payload 存進 S3，SQS 訊息裡只放一個指向 S3 物件的指標。這條路最大可以到 **2 GB**（受限於 S3 物件，而非 SQS）。這個「大 payload 走 S3、佇列只傳指標」的模式（claim-check pattern）不只是 SQS 的權宜之計，是訊息系統處理大物件的通用做法（物件儲存與大 payload 的交接見〈物件儲存：S3 與大 payload 的交接〉）。

順帶記一個計費的反直覺：SQS 不是按「訊息則數」計費，是按**每 64 KB 一個請求單位**計。一則 700 KiB 的訊息會被算成 `ceil(700 / 64) = 11` 個請求，不是一個；一則滿 1 MiB 的訊息算 16 個。所以把幾則小訊息合併成一則大訊息，並不會等比例省錢——計費單位是 64 KB，不是訊息本身。

## Standard 還是 FIFO：問題不在「要不要順序」

把兩種佇列並排，取捨就一目了然：

| | Standard | FIFO |
|---|---|---|
| 投遞語意 | at-least-once（會重複） | exactly-once processing（5 分鐘窗內去重） |
| 順序 | best-effort（可能亂序） | 同一 message group 內嚴格有序 |
| 吞吐 | 近乎無限 | 預設 300/3,000 TPS（整佇列）；high throughput 約 70,000 msg/s |
| consumer 需冪等 | 一定要 | 仍然要（崩潰重投、5 分鐘窗外重送） |
| 隊頭阻塞 | 無（訊息互相獨立） | 有（毒訊息卡住整個 group，需配 DLQ） |

但真正該問的問題，不是「我要不要順序」，而是更精確的兩個：**我的重複能不能靠冪等吸收？** 以及 **我需要有序的範圍有多大？**

如果你的 consumer 本來就冪等（或可以做成冪等），那 Standard 的「會重複」就被你的 handler 吸收掉了，你白拿了近乎無限的吞吐，沒理由去付 FIFO 的吞吐代價。絕大多數非同步任務屬於這一類——這是 Standard 該是預設的真正理由。只有當「順序錯了會直接導致業務邏輯出錯」（如帳戶狀態機、需要嚴格按序套用的指令流），且這個有序的範圍可以被收斂進一個個不太大的 message group 時，FIFO 才值得。而且就算選了 FIFO，你也沒能省掉冪等——FIFO 縮小了重複窗口，但 consumer 崩潰造成的重投、跨 5 分鐘的重送，都還在。

還有一個常被忽略的判斷點：FIFO 的有序保證**只在 SQS 這一段成立**。訊息一旦離開佇列、被你的 consumer 拉走，如果你的 consumer 是個有多個 worker、平行處理的池子，而你又沒有在自己的處理邏輯裡維持順序，那麼 SQS 辛苦保證的有序，可能在你的應用層就被打亂了。SQS 只能保證「按序投遞給你」，沒法保證「你按序處理完」——尤其在處理失敗、訊息重投、跑到後面去的時候。端到端的有序，是 SQS 的有序投遞**加上**你自己的有序處理，缺一不可。

## 它不是一個壞掉的 Kafka

最後值得釐清一個範式上的誤解，因為它常讓人用錯工具。SQS 是**佇列**，不是**日誌**。一則訊息被一個 consumer 拉走、刪掉，就**永遠消失了**——SQS 沒有「保留歷史」「重放（replay）」「讓一個新加入的消費者從頭讀一遍」這些概念。訊息的生命就是「進來、被拉走、被刪掉、消失」，message retention（預設 4 天，可設 60 秒到 14 天）只是「沒人來拿的話最多放多久」的上限，不是給你回頭重讀的歷史。

這和 append-only log 那種「訊息消費後仍留著、保留期內可任意重讀、多組消費者各讀各的」的範式（見〈Kafka：log、partition 與 consumer group〉）是兩種根本不同的東西。也因為 SQS 是「一則訊息只給一個 consumer」的點對點佇列，要把同一則訊息**扇出**給多個獨立的下游（出貨、發票、通知各收一份），SQS 自己做不到——你得在它前面接一個 pub/sub 把訊息複製成多份、分別落進多條佇列（這個 fan-out 模式見〈SNS：fan-out 與 SNS→SQS〉）。

## 為什麼是這個形狀

退一步看，SQS 的兩種佇列，其實是同一個核心決定——**「刪除訊息是消費者的責任，沒刪就重投」**——延伸出的兩條岔路。

正因為刪除是主動的、可能失敗，所以 SQS 天生是 at-least-once：它寧可重複，也不願意悄悄丟失，因為對絕大多數工作而言，重複可以靠冪等收拾，丟失卻是無聲的災難。這個選擇讓 Standard 得以放棄全域協調、換來近乎無限的吞吐——亂序與重複不是它的缺陷，是它換取無限擴展所付的、且通常划算的代價。

而當你**真的**需要有序時，FIFO 出現，但它誠實地把代價標在價目表上：要有序，就得有協調；有協調，吞吐就有上限；要在這個上限裡跑得快，就得把「有序的範圍」切得夠細——切到剛好覆蓋業務真正需要的邊界、不多一分。FIFO 的 message group、它的隊頭阻塞、它按 partition 算的吞吐天花板，全都是「在一個分散式系統裡維持順序」這件事的固有成本，被攤開來讓你看見、讓你選。

所以 SQS 沒有「最好」的那種佇列。它有的是一個把取捨講得很清楚的選單：你願意承擔重複、換無限吞吐（Standard），還是願意犧牲吞吐、換一個可以畫定範圍的有序（FIFO）。而無論你選哪個，那條最底層的規則——刪除是你的責任、重複是常態、冪等是你的事——都不會變。看懂了 visibility timeout 那一塊「已借出」的布，你就看懂了 SQS 的全部。

## 延伸閱讀

- [Amazon SQS message quotas（官方 quotas，含 1 MiB 上限、in-flight 上限、retention 範圍）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html)
- [Amazon SQS visibility timeout（官方，in-flight 與借期機制）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)
- [FIFO queue delivery logic（官方，message group 投遞與隊頭阻塞、120,000 lookahead）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-understanding-logic.html)
- [Exactly-once processing in Amazon SQS（官方，5 分鐘去重視窗與 deduplication ID）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html)
- [High throughput for FIFO queues（官方，per-partition TPS 與 high throughput mode）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html)
- [Amazon SQS increases maximum message payload size to 1 MiB（2025-08 公告）](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib/)
