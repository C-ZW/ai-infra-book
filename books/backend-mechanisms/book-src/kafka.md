# Kafka：log、partition 與 consumer group

把同一份「訂單成立」事件丟給三個下游——出貨、發票、推播——這件事在傳統佇列裡有個尷尬：一則訊息被一個 consumer 拿走、刪掉，就沒了。你得在前面接一個扇出層，把同一則訊息複製成三份、塞進三條佇列，下游各拉各的。現在加個需求：發票服務上週算錯稅、要把過去七天的訂單**重算一遍**。傳統佇列這下徹底沒轍——那些訊息早在被消費的瞬間就從佇列裡消失了，你想重放也沒得放。

這兩個需求——「同一份資料給很多組互不干擾的消費者」和「事後能把歷史重新讀一遍」——逼出一個和佇列截然不同的設計。Kafka 給的答案是：**不要把訊息當成「投遞完就丟」的封包，而是把它當成「寫進一本永遠只追加、不修改的帳本」的一筆記錄。** consumer 來讀，不是把記錄拿走，而只是把自己的書籤往前挪一格。記錄留在帳本裡，直到保留期過了才被清掉。換掉這一個底層假設，前面兩個需求就都不再是問題，而代價是另一整套新的取捨。這一章就是把這本帳本的構造、它怎麼擴展、怎麼壞，從頭看清楚。

## 一條 log 就是一個檔案，能有多快

先把最底層的物件釘死：Kafka 的 **partition**，在磁碟上就是一串**只能往尾巴追加的檔案**（segment 檔的接龍）。producer 寫一筆訊息，Kafka 把它接在這串檔案的末端，給它一個單調遞增的整數編號——**offset**。partition 0 的第一筆是 offset 0、第二筆是 offset 1，永遠遞增、永不重用、永不回填。一個 topic 是一個邏輯上的訊息流，底下切成若干個這樣的 partition。

這個「只追加」的選擇不是美學，是它快的根源。傳統訊息 broker 要維護「哪些訊息已投遞、哪些待投、哪些要重送」的可變狀態，每則訊息的生命週期都要在某個資料結構裡被翻動。Kafka 把這些全砍了：寫入永遠是 append 到檔案尾端——對磁碟而言這是**循序寫**，連機械硬碟都能跑到接近頻寬上限，更別說 SSD。讀取也是循序的：consumer 從某個 offset 開始，順著檔案往後掃。循序 I/O 比隨機 I/O 快上一兩個數量級，而 Kafka 的整個資料路徑被刻意設計成只有循序 I/O。

更狠的是它連「把資料從磁碟搬給網路」這一步都不經手。一筆訊息從 partition 檔案送到 consumer，作業系統的 `sendfile` 系統呼叫能讓資料直接從檔案的 page cache 流進網路 socket，**完全不複製進 Kafka 這個 JVM 行程的記憶體、不在使用者空間繞一圈**（zero-copy）。Kafka broker 在熱路徑上幾乎不碰訊息內容——它只是個管帳的，記住每個 partition 寫到哪、每個 consumer 讀到哪，真正的位元組搬運交給核心。這就是為什麼一台普通機器的 Kafka 能扛每秒數十萬則訊息：它在熱路徑上做的事，少到幾乎只剩「append 一個檔案」和「叫核心把一段檔案吐進 socket」。

## offset 是消費者的，不是訊息的

這裡有個容易被舊佇列直覺帶歪的關鍵：**「消費」一則訊息，在 Kafka 裡不改變那則訊息的任何狀態。** RabbitMQ 或 SQS 裡，consumer ack 之後訊息就被刪了——訊息身上帶著「已處理」這個狀態。Kafka 不是。訊息躺在 partition 裡一動不動，被誰讀過、讀了幾次，它自己毫不知情。

真正在動的是 consumer 那一側的一個數字：**「我讀到 offset 幾了」**。這個數字叫 committed offset，是 consumer（或更精確地說，一個 consumer group）的私有財產。consumer 讀到 offset 99、處理完、把「我已消費到 100」這件事記下來；下次它重啟或被別人接手，就從 100 繼續。整個消費進度，被壓縮成**一個遞增的整數指標**。

這個設計直接解掉開場的兩個需求。要讓三個下游各自讀同一份資料——給它們三個**不同的 consumer group**，每個 group 維護自己那一份 offset，互不干涉。出貨讀到 offset 5000、發票讀到 4800、推播讀到 5000，三個書籤各夾各的頁，誰都不擋誰。要重放歷史——把發票那個 group 的 offset **往回設**到七天前那一格，它就會把這七天的訊息重新讀一遍。訊息從沒被刪，重放只是把書籤倒退。

那這個「我讀到哪」的整數存在哪？Kafka 把它存進一個**自己的內部 topic**，叫 `__consumer_offsets`——是的，consumer 的進度本身也是寫進一條 Kafka log。當一個 consumer 提交 offset，它其實是往這條內部 topic append 一筆「group G 在 topic T 的 partition P 讀到 offset N」的記錄。這條 topic 是 **compacted（壓實）**的：同一個 key（group + topic + partition）只保留最新一筆，舊的進度記錄被背景清掉，所以它不會無限長大。broker 還把這些 offset 快取在記憶體裡，查進度時不必每次掃 log。consumer 的狀態，最後也是一本 log——這種「萬物皆 log」的自我一致，是 Kafka 設計裡很美的一處。

## 順序的真相：只在一條 partition 裡

partition 不只是分檔存放的單位，它同時是**順序保證的邊界**和**並行的單位**——這兩件事綁在同一個東西上，是 Kafka 最需要想透的取捨。

順序這件事，Kafka 給的保證精確而有限：**同一個 partition 內，訊息嚴格按 offset 有序；跨 partition，不保證任何順序。** 為什麼只能這樣？因為跨 partition 的全域順序，等於要求所有 partition 在每一筆寫入上達成一個全域一致的先後——那正是共識等級的協調（見〈共識〉），貴到會把吞吐打回原形。Kafka 選擇放棄全域順序，換來「每個 partition 各寫各的、彼此不必協調」的水平擴展。

那你要怎麼確保「同一個帳戶的一連串狀態變更照序處理」？答案是 **partition key**。producer 送訊息時帶一個 key，Kafka 對 key 取雜湊、決定它落哪個 partition——預設是 `hash(key) % partition_count`（預設的 `hash` 是 murmur2，不是 Java 的 `hashCode`）。同一個 key 永遠落同一個 partition，於是同 key 的訊息天然有序。把「帳戶 ID」當 key，同一帳戶的所有變更就被釘進同一條 partition、嚴格有序；不同帳戶散在不同 partition、互相平行。順序的粒度，由你選的 key 決定。

這裡藏著一個非顯然的陷阱，值得停下來看。`hash(key) % partition_count` 這個式子裡有 `partition_count`——**一旦你改變 partition 數，同一個 key 算出來的 partition 就變了**。本來 `hash("acct-6") % 6 = 3`，你把 partition 從 6 加到 12，變成 `hash("acct-6") % 12 = 9`。從那一刻起，acct-6 的新訊息寫進 partition 9，而它的舊訊息還躺在 partition 3。兩條 partition 各自有序，但 consumer 不保證先讀完 3 再讀 9——**這個帳戶的全域順序，就在你擴 partition 的瞬間斷了**。這是「partition 數通常只能加、加了又會打亂既有 key 順序」的根源；要安全擴容而不亂序，往往得搭配不依賴 partition 數的自訂 partitioner，或乾脆接受「擴容點之後才有序」。`partition_count` 不是個能隨手調的旋鈕，它編進了你每一筆訊息的落點。

## consumer group：partition 是怎麼被分掉的

現在看並行。一個 topic 有 12 個 partition，你想用一群 consumer 平行地消化它——這群 consumer 組成一個 **consumer group**。Kafka 的分配規則簡單而硬：**同一個 group 內，一個 partition 在同一時刻只交給一個 consumer。** 它把 12 個 partition 分給組內的 consumer，每個 consumer 認領一撮 partition、獨佔地讀。

這條規則直接定出並行度的天花板：**一個 consumer group 的有效並行消費者數，不會超過 partition 數。** 12 個 partition，最多 12 個 consumer 同時幹活；你塞第 13 個 consumer 進去，它分不到任何 partition，只能閒著待命（它不是全無用處——某個現役 consumer 掛了，它能立刻補位）。反過來，3 個 consumer 配 12 個 partition，每人扛 4 個 partition。所以當你的下游處理跟不上、想加 consumer 提速，加到等於 partition 數就到頂了——再想快，得先加 partition。這就是為什麼 partition 數是個要在建 topic 時就想清楚的容量決定：它同時是順序粒度、也是並行上限。

把一個具體的數字算到底，這個天花板就很有體感。假設一條 topic 有 **12 個 partition**，尖峰流入 **每秒 60,000 則**訊息，每個 consumer 處理一則平均要 **2 毫秒**（單執行緒）。一個 consumer 每秒最多處理 `1000 / 2 = 500` 則。要吃下 60,000 則/秒，你需要 `60000 / 500 = 120` 個處理單位的算力——但一個 group 最多只有 12 個 consumer 能同時拿到 partition，每個 consumer 就算榨乾單核也只有 500 則/秒，12 個合計 `12 × 500 = 6,000` 則/秒。**差了整整十倍。** 結論不是「多開 consumer」（開到第 13 個就沒 partition 可分了），而是要嘛把 partition 數提到至少 120、要嘛讓每個 consumer 內部再開執行緒池平行處理（代價是同 partition 內的順序保證被你自己打破）。這個算術逼你在建 topic 的那一刻就正視：partition 數不夠，後面再多機器也救不回吞吐。

## rebalance：群組成員一變，partition 就要重分

consumer group 不是靜態的。有人新加入、有人崩潰、有人因為太久沒送心跳被判定離線——每一次成員變動，group 都得重新決定「哪個 partition 歸誰」。這個重分配的過程叫 **rebalance**，它是 consumer group 最關鍵、也最容易出事的環節。

舊的 rebalance 協定（stop-the-world）有個讓人頭痛的性質：**rebalance 一觸發，整個 group 的所有 consumer 全部先停下、交還手上所有 partition，等協定重新算好分配、再各自領回**。在這段「全體暫停」的窗口裡，沒有任何 partition 被消費——整條 topic 的處理凍結。group 越大、partition 越多，這個停頓越長。更糟的是它會連鎖：一次部署滾動重啟，consumer 一個個離開又回來，每一次進出都觸發一輪 stop-the-world，整個重啟期間消費走走停停。

這裡有個特別陰險的 edge case：rebalance 由「心跳逾時」觸發，而**處理太慢也會被誤判為死掉**。consumer 要定期送心跳證明自己活著（背景執行緒在做），但它還要定期回來呼叫 `poll()` 拉下一批——如果某一批訊息處理得太久、超過 `max.poll.interval.ms`（預設 5 分鐘）才回來 poll，group coordinator 會認定「這傢伙卡死了」，把它踢出 group、觸發 rebalance、把它的 partition 分給別人。然後那個其實還活著、只是慢的 consumer 處理完回來一 poll，發現自己已經被開除了。它剛才處理的那批、如果還沒提交 offset，會被接手的 consumer 再處理一遍——這就是「慢」被當成「死」，在訊息系統裡重演（見〈共識〉裡同一個「分不出慢與死」的根本難題）。批次抓太多、單則處理太重，是這類非預期重複的常見來源。

新一代的 rebalance 協定（KIP-848，自 Kafka 4.0 起在 broker 端 GA 並預設啟用，但 consumer 仍須主動設 `group.protocol=consumer` 才採用，預計要到未來版本才成為真正的預設）把這件事做了根本性的改善（2026-06）。它做了兩個關鍵的事：一是把「算分配」這個工作從 client 端搬到 **broker 端的 group coordinator**——consumer 不再需要彼此用一個全域同步屏障對齊，而是各自和 coordinator 持續心跳、coordinator 增量地告訴每個 consumer「你多認領這幾個、交還那幾個」。二是這個過程是**增量且協作的**：coordinator 只算出需要搬動的那一小撮 partition（delta），沒被影響的 consumer 完全不必停——它手上的 partition 不動，它就繼續讀，不再有「全體暫停」。對一個十幾個 consumer、上千 partition 的大 group，這把原本動輒上百秒的 rebalance 壓到個位數秒。

## 訊息是怎麼變得「不會掉」的：ISR、acks 與 high watermark

到目前為止 partition 都像是單一檔案，但一條 partition 在生產環境是**有多份副本**的：一個 leader、若干 follower，分散在不同 broker 上。所有讀寫都走 leader，follower 的工作是不斷地從 leader 拉取、把自己的 log 追到和 leader 一樣。一份訊息「算不算寫成功、會不會掉」，全看這套副本機制怎麼運作——這是 Kafka 持久性保證的核心。

關鍵概念是 **ISR（in-sync replicas，同步副本集）**：那些「跟上了 leader 進度」的副本（leader 自己永遠在 ISR 裡）。一個 follower 如果落後太多、或太久沒來拉，會被踢出 ISR；追上了再放回來。ISR 是個會動的集合，它代表「此刻有哪幾份副本是可信的、資料是齊的」。

producer 寫入時的 `acks` 設定，決定「leader 要等多確定，才回 producer 說成功」：

| acks | leader 何時回 ack | 你買到什麼 | 風險 |
|---|---|---|---|
| `acks=0` | 送出就算，不等 | 最高吞吐 | leader 沒收到也不知道，直接掉 |
| `acks=1` | 寫進 leader 自己的 log 就回 | 中等 | leader 寫了還沒被 follower 複製就崩潰 → 掉 |
| `acks=all` | 寫進 **ISR 裡所有副本** 才回 | 最強持久性 | 較慢；且要配 `min.insync.replicas` 才真的安全 |

`acks=all` 看起來很安全，但它自己一個還不夠，這是最容易漏掉的一環。設想一條 partition 有 3 份副本，但因為網路或 broker 抖動，兩個 follower 都落後被踢出 ISR——現在 ISR 裡**只剩 leader 一個**。此時一筆 `acks=all` 的寫入「等 ISR 全部確認」，而 ISR 全部就是 leader 自己，於是它寫進 leader 的 log 就回成功了。看起來你開了最強持久性，實際上這筆訊息只存在一份副本上——leader 一崩，它就跟著消失。`acks=all` 的「all」是「ISR 的 all」，不是「副本的 all」；ISR 縮到只剩一個時，`acks=all` 悄悄退化成 `acks=1`。

補這個洞的是 broker 端的 **`min.insync.replicas`**。把它設成 2，意思是「ISR 少於 2 個時，拒絕 `acks=all` 的寫入、直接回錯」。現在上面那個場景：ISR 縮到只剩 leader 一個，min.insync.replicas=2 不滿足，producer 的寫入被擋下來、收到明確的錯誤——系統寧可拒寫，也不假裝寫成功卻只存一份。**`acks=all` 與 `min.insync.replicas=2` 必須成對出現**，少了後者，前者給你的是一種會在最壞時刻破功的安全感。這對組合背後的鴿巢邏輯，和共識叢集「過半才算數」是同一個道理（見〈共識〉）：要容忍 1 台掉、又絕不丟已確認的寫，至少得有 2 份副本同時持有它。

那 consumer 這側呢？這裡有個保護讀者的機制叫 **high watermark（高水位）**：consumer **只能讀到已經被 ISR 裡所有副本都複製到的那個 offset 為止**，這個界線就是 high watermark。leader 雖然可能已經寫進了更新的訊息（它的 log end offset 比 high watermark 高），但那些「還沒被所有 ISR 確認」的訊息對 consumer 是隱形的。為什麼要這樣？因為如果讓 consumer 讀到一筆「只在 leader 上、還沒複製出去」的訊息，而 leader 隨即崩潰、新 leader 從某個 follower 接手——那個 follower 上根本沒這筆訊息——consumer 就讀到了一筆「後來不存在」的記錄。high watermark 的作用，就是保證 consumer 看到的每一筆，都已經穩到「leader 換人也不會消失」。它讓「讀得到」這件事，永遠落後於「寫進去」一個複製的身位，用一點延遲換「讀到的絕不會憑空蒸發」。

## 「算不算處理完」取決於你何時提交 offset

把寫入的持久性放一邊，consumer 這側還有一個語意上的關鍵抉擇，它決定了 Kafka 給你 at-least-once 還是 at-most-once——而這個抉擇藏在一個看似不起眼的時機問題裡：**你在「處理訊息」之前還是之後，提交 offset？**

順序是「處理之前提交」：consumer 拉到一批訊息，先把 offset 往前提交（標記「這批我讀了」），再去處理。如果處理到一半 consumer 崩潰——offset 已經提交了，重啟後它從下一批開始，**這批沒處理完的就永遠跳過了**。這是 **at-most-once**：訊息頂多被處理一次，但可能一次都沒有（會掉）。

反過來「處理之後提交」：consumer 先把整批處理完、確認都成功了，才提交 offset。如果處理完、還沒來得及提交就崩潰——重啟後 offset 還停在這批的開頭，它會把這批**重新讀一遍、重新處理一遍**。這是 **at-least-once**：訊息至少被處理一次，但可能不只一次（會重複）。

絕大多數人要的，是 at-least-once——掉訊息通常比重複處理更糟。（值得提醒：Kafka **開箱的** `enable.auto.commit=true` 是背景每隔幾秒按計時器提交，和你處理到哪無關，崩潰時反而偏向 at-most-once 的「漏讀」；要穩拿 at-least-once，得關掉自動提交、在處理完之後手動 commit。）但 at-least-once 的代價就是上面那個「崩潰後重讀」會造成重複，所以 **consumer 端的處理必須是冪等的**（同一筆訊息處理兩次和處理一次結果一樣），否則一次崩潰就是一次重複扣款、重複寄信。這個「at-least-once 的世界裡，重複是常態、要靠冪等兜底」的完整道理（冪等鍵怎麼設計、去重在哪一層做），是另一個主題的核心（見〈重複是常態〉）。這裡只要記住：**Kafka 給你 at-least-once 還是 at-most-once，不是它預設好的，而是你提交 offset 的時機選的。** 很多人以為「commit offset」是「處理完成」的同義詞，其實它只是「把書籤往前挪」，挪的時機由你定，語意也由你定。

## exactly-once 的真相：它只在 Kafka 的邊界內成立

那 Kafka 廣告的 **exactly-once semantics（EOS）**呢？這是最需要把話講精確的地方，因為「exactly-once」這個詞太誘人、太容易被當成「整條業務鏈端到端只執行一次」的萬靈藥——而它不是。

先看它怎麼做到的。EOS 是三個機制疊起來的，缺一不可（2026-06）：

第一層，**冪等 producer**（`enable.idempotence=true`，自 Kafka 3.0 起為預設）。broker 給每個 producer 一個 PID（producer ID），producer 送往每個 partition 的每則訊息帶一個遞增的 sequence number。broker 記得每個 PID 在每個 partition 寫到的最後一個 sequence——如果因為網路重試、同一筆訊息（同 PID、同 sequence）又來了一次，broker 認得出來、直接丟掉、回成功，不會在 log 裡寫第二筆。這解掉了「producer 重試造成重複寫入」這個最常見的重複源——但只在單一 producer session、單一 partition 的範圍內。

第二層，**交易（transactional producer）**。設一個 `transactional.id`，producer 就能把「寫多個 partition／topic」綁成一個原子單位——要嘛全部生效、要嘛全部不算。更關鍵的是它能把「**寫資料**」和「**提交 consumer offset**」綁進同一個交易，達成 read-process-write 的原子性：讀進來、處理、寫出去、推進 offset，這四步作為一個交易一起 commit 或一起 abort，中間崩潰不會留下「寫了一半、offset 卻提前了」的破碎狀態。`transactional.id` 還用來**圍堵殭屍 producer**——舊的 producer 實例如果沒乾淨關掉、還在偷寫，新實例用同一個 transactional.id 上線時會把舊的「fence 掉」，舊實例的寫入從此被拒絕，避免兩個自以為是的 producer 各寫各的。

第三層，**consumer 設 `isolation.level=read_committed`**。這樣 consumer 只讀到「已 commit 的交易」裡的訊息，自動跳過被 abort 的交易留下的訊息，也只讀到 LSO（last stable offset，最後一個沒有未決交易卡著的位置）以前的訊息。沒有這一層，consumer 會把「正在進行、可能會被 abort」的交易訊息也讀進來，前兩層的努力就漏了。

三層湊齊，Kafka 確實能給你 exactly-once。但**它的邊界是「Kafka 到 Kafka」**：這套保證只覆蓋「從 Kafka 讀、處理、寫回 Kafka」這條鏈路。一旦你的處理有**外部副作用**——寫一個 PostgreSQL、呼叫一個第三方 API、寄一封 email——那個外部系統**不在 Kafka 的交易裡**，EOS 一步都延伸不到它。交易能保證「offset 推進」和「寫回 Kafka 的結果」一起成敗，但它管不到你中途對外部資料庫做的那次 `INSERT`。如果交易最後 abort、要重來，那次 INSERT 不會被回滾，重來時就執行第二遍。把 Kafka EOS 當成「我開了它，整條業務就端到端 exactly-once」，是這個主題最常見、後果也最嚴重的誤判——對外部系統的那一步，你仍然只有 at-least-once，仍然得靠冪等寫入或 outbox 把它兜住。EOS 不是讓你不必想冪等，它只是替你消掉了「Kafka 內部那一段」的重複。

## 把重複的數量算出來

抽象地說「會有重複」沒有體感，把它換成數字就具體了。設想一條高吞吐 topic，每天流經 **1,000 萬則**訊息，跑預設的 at-least-once，下游因為偶發的 consumer 重啟、rebalance、處理逾時，造成大約 **0.1%** 的訊息被重讀。那就是 `10,000,000 × 0.001 = 10,000` 筆重複，**每天一萬筆**要靠下游的冪等去吸收。如果下游是「給訊息對應的訂單蓋一個已處理標記」這種冪等操作，這一萬筆重讀無害——第二次處理發現標記已在，直接跳過。但如果下游是「每收到一筆就 `balance -= amount` 扣一次款」這種非冪等操作，這一萬筆就是**一萬次重複扣款**，是一場財務事故。

現在假設你為了消滅這些重複，開了 Kafka 的 EOS。在「Kafka 讀進來、處理、寫回另一條 Kafka topic」這段鏈路上，這一萬筆確實被交易機制消掉了，下游讀 read_committed 看到的就是乾淨的一份。但只要這個處理同時還往**外部那個 PostgreSQL** 寫了扣款記錄，那一段不在交易裡——EOS 沒碰它。所以真正能止血的，從來不是「開 EOS 就好」，而是「**對外部系統的那次寫入帶一個冪等鍵**」：每筆訊息算出一個穩定的去重鍵（例如 `order_id + event_type`），扣款前先查這個鍵有沒有處理過，處理過就跳過。EOS 把 Kafka 內部那段的一萬筆重複降到零，冪等鍵把外部那段的一萬筆重複降到零——兩者管不同的鏈段，缺哪一段，那一萬筆就從那個缺口漏出來。這個算術的用處，是讓你看清「exactly-once」這四個字到底替你擋了什麼、沒擋什麼。

## 為什麼是這個形狀

退一步看，Kafka 的整個樣貌，都是從一個底層選擇長出來的：**把訊息當成「寫進不可變 log 的記錄」，而不是「投遞完就丟的封包」。**

正因為訊息留在 log 裡、消費只是挪書籤，同一份資料才能給很多組互不干擾的消費者讀，事後才能重放歷史——這正是它天然契合 event sourcing 那種「狀態即不可變事件序列」的存放需求（見〈Event sourcing 與 CQRS〉）。正因為寫入只是 append 一個檔案、搬運交給核心的 zero-copy，它才能在一台普通機器上扛每秒數十萬則。正因為要水平擴展、不肯付全域順序那筆共識帳，它才把流切成 partition、把順序保證縮到單一 partition 內、把並行上限綁在 partition 數上。正因為 partition 有副本、要在「leader 崩了也不丟」和「別讓 consumer 讀到會蒸發的訊息」之間站穩，才有了 ISR、acks=all＋min.insync.replicas、high watermark 這一整套。而 exactly-once 之所以只能管到 Kafka 的邊界，是因為交易這把鎖只鎖得住 Kafka 自己的 log，鎖不住你伸手去碰的那個外部世界。

這些不是一堆各自獨立的功能旋鈕，而是「不可變 log」這一個決定，被推到各個方向後必然長出的後果。下次你在調 partition 數、選 acks、設 offset 提交時機、或盯著一次 rebalance 發呆，你會知道每一個選項背後，都是這同一本只追加的帳本，在問你願意為哪一種保證、付哪一種代價。

## 延伸閱讀

- Apache Kafka 官方文件 — Design / Message Delivery Semantics（at-least-once／at-most-once／exactly-once 與 offset 提交時機）: https://kafka.apache.org/documentation/#semantics
- Apache Kafka 官方文件 — Replication（ISR、leader/follower、high watermark）: https://kafka.apache.org/documentation/#replication
- Confluent, "Exactly-Once Semantics Are Possible: Here's How Apache Kafka Does It"（冪等 producer ＋ 交易的原始設計說明）: https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/
- KIP-848: The Next Generation of the Consumer Rebalance Protocol（broker 端、增量協作式 rebalance）: https://cwiki.apache.org/confluence/display/KAFKA/KIP-848%3A+The+Next+Generation+of+the+Consumer+Rebalance+Protocol
- Apache Kafka 4.0 釋出說明（KRaft 成為唯一模式、ZooKeeper 移除、新 rebalance 協定）: https://www.confluent.io/blog/latest-apache-kafka-release/
- KIP-932: Queues for Kafka（share groups，4.2 起 GA 的佇列式消費模型）: https://cwiki.apache.org/confluence/display/KAFKA/KIP-932%3A+Queues+for+Kafka
- Jay Kreps, "The Log: What every software engineer should know about real-time data's unifying abstraction"（log 作為統一抽象的奠基文章）: https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying
