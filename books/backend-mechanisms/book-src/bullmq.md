# BullMQ：Redis 上的延遲與工作佇列

一個 HTTP handler 收到「使用者按下產生報表」。報表要跑三十秒：拉資料、算彙總、繪圖、寫 PDF。你當然不能讓那條 HTTP 連線吊著三十秒等——使用者的瀏覽器會逾時，你的 web server 的連線池會被這種慢請求吃光。標準做法是把這份工作**丟到背景**：handler 只記下「有人要這份報表」，立刻回一個 `202 Accepted`，真正的重活交給另一群行程慢慢做。

問題在「丟到背景」這四個字底下藏了一整套機制。那份工作要存在某個地方，撐過 web server 重啟也不能掉；要有一群 worker 來搶它、但同一份工作不能被兩個 worker 同時做；worker 做到一半當掉，工作不能就此人間蒸發、得有別人接手；做失敗要能重試、但不能無限重試打爆下游；有些工作還得「五分鐘後再做」或「每天凌晨三點做一次」。把這些湊齊，你需要的就是一個**工作佇列（job queue）**。

你大可以去架一台 RabbitMQ 或開一條 SQS。但很多 Node.js 服務手邊已經有一台 Redis——拿來當 session store、當快取、當分散式鎖。於是一個很自然的念頭浮現：能不能就用這台 Redis 來當工作佇列的後端，省掉再養一個 broker 的運維成本？BullMQ 就是這個念頭的成熟答案。它不是一個獨立的 broker 行程，而是一個 Node.js 函式庫（也有 Python、Rust、Elixir、PHP 的對應實作），把 Redis 的幾個資料結構編織成一個帶延遲、重試、優先序、排程的工作佇列。理解 BullMQ，本質上是理解「**怎麼用一堆本身不是佇列的 Redis 原語，拼出一個可靠的佇列**」——以及這個拼法在哪裡會漏。

## 為什麼不能只用一個 Redis list

Redis 有 list，list 有 `LPUSH` 和 `BRPOP`。生產者 `LPUSH` 把工作推進去，消費者 `BRPOP` 阻塞著等、有工作就拿走。這看起來已經是個佇列了，何必要 BullMQ？

把這個天真版本放到 worker 會當機的真實世界裡跑一遍，它就破了。`BRPOP` 是一個破壞性操作：它把元素從 list 上**原子地移除並回傳給你**。那一瞬間，這份工作只存在於那個 worker 的記憶體裡——它不在 Redis 上的任何地方了。如果這個 worker 在「拿到工作」和「做完工作」之間當掉（行程被 OOM killer 殺、機器斷電、部署滾動更新把它關了），這份工作就**徹底消失**。沒有人知道它存在過，沒有人會接手，使用者那份報表永遠不會生出來，而且系統裡沒有任何痕跡告訴你它丟了。

這就是工作佇列和「訊息傳遞」最關鍵的差別。一份工作不是發完即忘的訊號，它是一個**有狀態、有生命週期的任務**：它從「等待」進到「處理中」，可能「完成」、可能「失敗」、可能「失敗後重試」、可能「排程在未來」。一個破壞性的 `BRPOP` 抹掉了「處理中」這個狀態——它讓「工作離開佇列」和「工作真的做完」這兩件事在同一個原子操作裡發生，於是中間那段崩潰窗口無處安放。

要補這個洞，你需要的不是「把工作搬走」，而是「把工作**移交**，但留下它正在被處理的證據」。Redis 老式的答案是 `BRPOPLPUSH`（或 `LMOVE`）：原子地把元素從 `wait` list 的一端彈出、推進另一條 `active` list。工作沒有消失，它在一條「處理中」的清單上掛著。worker 真正做完，才把它從 `active` 上拿掉。worker 當掉，工作還躺在 `active` 上，可以被偵測、被搶救。BullMQ 的整個設計，就是把這個「移交而非搬走」的思路，擴張成一套完整的狀態機。

## 工作的生命週期：幾個 Redis 結構分工

BullMQ 在 Redis 裡為一條佇列維護一組結構，每個結構代表工作生命週期的一個階段。粗略地說：

```
                add()                          worker picks up
   producer  --------->  [ wait ]  ----------------------------->  [ active ]
                            ^  (a Redis LIST)                      (job + lock)
                            |                                          |
              promote when  |                                         done / failed
              time is due   |                                       /         \
                            |                                     v             v
                       [ delayed ]                          [ completed ]   [ failed ]
                    (a Redis SORTED SET,                    (sorted sets, capped)
                     score = run-at timestamp)
```

- **wait**：一條 Redis list，所有準備好被處理的工作排在這。worker 從這裡領工作。
- **active**：工作被某個 worker 領走、正在處理的階段。關鍵是領取的那一刻，工作的詮釋資料（存在一個 Redis hash 裡）被打上一個**鎖（lock）**——一個帶 TTL 的 key，宣告「這份工作有主了」。
- **delayed**：給「現在還不能做」的工作住的地方。它不是 list 而是一個**有序集合（sorted set）**，每份工作的 score 就是它「該被執行的時間戳」。`add(data, { delay: 5000 })` 不會進 wait，而是進 delayed、score 設成「現在 + 5 秒」。
- **completed / failed**：終態，同樣用 sorted set 存（以便依完成時間排序、依設定保留最近 N 筆或最近一段時間，舊的自動修剪掉）。
- **prioritized**：若工作帶了優先序，它走的不是普通 wait list，而是另一個 sorted set，score 編碼了優先級，讓高優先工作先被領走。

把工作在這些結構之間搬動的每一步——從 wait 領一份到 active 並上鎖、把到期的 delayed 工作提升到 wait、把做完的從 active 移到 completed——都**不能是多個 Redis 指令的鬆散組合**，否則兩個 worker 會在指令的縫隙裡搶到同一份工作。BullMQ 用 **Lua 腳本**解決這件事：Redis 保證單一 Lua 腳本的執行是原子的、不會被別的指令插入（Redis 的指令執行本身是單執行緒的，見〈Redis 的內部〉）。於是「檢查 wait 有沒有工作、彈一份出來、寫進 active、設好 lock、更新狀態 hash」這一連串動作，被打包進一個 Lua 腳本一次跑完，要嘛全發生、要嘛全不發生。這是 BullMQ 一切原子性保證的地基：**不是靠 Redis 交易（MULTI/EXEC），而是靠 Lua 腳本，因為腳本裡可以有條件邏輯**（「如果 wait 是空的就回傳 nil」這種判斷，MULTI/EXEC 做不到）。

## 延遲投遞：sorted set 加一個喚醒的 marker

延遲是這套機制裡最漂亮的一塊，值得拆開看。

「五秒後再做」的天真實作是讓 worker 不斷輪詢：每隔一段時間掃一遍所有延遲工作，看誰到期了。但 BullMQ 把它變成一次 `ZRANGEBYSCORE`：因為 delayed 是 sorted set、score 是執行時間戳，「哪些工作到期了」就是「score ≤ 現在」的那一段，而 sorted set 的範圍查詢是 `O(log N)`。一個負責提升的迴圈定期問 Redis：「把所有 score 不大於此刻的工作給我」，把它們從 delayed 搬進 wait。早年這個提升迴圈是一個叫 `QueueScheduler` 的獨立物件，你得記得另外起一個它、忘了起整條延遲佇列就不動——這是 Bull 時代一個著名的坑。**BullMQ 自 2.0 起把 QueueScheduler 廢掉了**，提升延遲工作與偵測 stalled 工作的責任收進了 Worker 本身，你只要起 Worker 就好，少了一個會忘記接的線。

但「定期掃一遍」還有個延遲問題：如果提升迴圈每五秒醒一次，一份只延遲了 100 毫秒的工作，最糟可能要等將近五秒才被看到。**BullMQ v5 把 marker 機制重新設計**來消掉這個遲滯（v4 已有舊式 marker，但仍靠 `BRPOPLPUSH`；v5 把它整個拿掉、改成下面這套——這也是 v4 到 v5 之間唯一的破壞性變更）：worker 領工作時，不是粗暴地輪詢 wait list，而是用 `BZPOPMIN` **阻塞在一個專門的 marker sorted set 上**。每當有延遲工作被加入、或下一份延遲工作的到期時間改變，這個 marker 就被更新成「下一個該醒來的時間」。`BZPOPMIN` 會一直阻塞到那個時間點、或被新工作的加入提早喚醒——於是 worker 既不空轉輪詢、又能在工作該跑的那一刻精準醒來。這是個典型的「用 Redis 的阻塞原語把忙等變成事件驅動」的手法：把「該醒來的最近時刻」維護成一個可阻塞的最小堆頂端，讓 Redis 自己替你算「還要睡多久」。

## 鎖、租約與 stalled：worker 死了之後

現在來到整套機制裡最容易出事、也最該講透的地方：worker 在處理工作的途中死了，會發生什麼。

回到「移交而非搬走」。worker 領到一份工作時，BullMQ 在 Redis 裡為它設了一個帶 TTL 的鎖。這個鎖**不是永久的所有權，而是一份租約（lease）**——它說的是「這份工作歸我，但只租 `lockDuration` 這麼久」。預設 `lockDuration` 是 **30000 毫秒（30 秒）**。只要 worker 還活著、還在處理，它必須**定期續租**：BullMQ 的 worker 在背景每隔 `lockRenewTime`（預設是 `lockDuration` 的一半，也就是 15 秒）就把鎖的 TTL 往後延一次。一份跑了三分鐘的健康工作，期間鎖被續了十幾次，從不過期。

關鍵的轉折在這：如果 worker 當掉了，它就**停止續租**。鎖不再被延展，TTL 自然走完、過期消失。這份工作現在處在一個尷尬狀態——它還掛在 active 上，但它的鎖不見了，也就是說它「有主之名、無主之實」。BullMQ 用一個 **stalled checker**（同樣收進了 Worker，定期執行）來抓這種工作：它掃 active 上的工作，找出那些**鎖已經不在**的，判定為 **stalled（停滯）**，把它們搬回 wait，讓另一個活著的 worker 重新領走。

這裡藏著一個非顯然、但用任何 at-least-once 工作佇列都必須內化的真相：**stalled 偵測無法區分「worker 死了」和「worker 還活著、只是慢到沒能及時續租」。** 想像一個 worker 在處理一份 CPU 密集的工作，整個 Node.js 行程的 event loop 被一段同步運算卡死了三十秒——它沒當機，但它也沒機會跑背景的續租邏輯（續租也要 event loop 排得到才能執行，見〈event loop：單執行緒怎麼同時做很多事〉）。鎖過期了，stalled checker 認定它停滯、把工作丟回 wait、另一個 worker 領走開始處理。於是**同一份工作被執行了兩次**，而第一個 worker 其實還在埋頭算、馬上也要算完。這正是共識章那個「你分不出慢和死」（見〈共識：讓一群會當機的機器同意一件事〉）在工作佇列尺度上的翻版——你的偵測工具只有逾時，而逾時永遠無法證明對方死了。

這就是為什麼 BullMQ 給的是 **at-least-once 處理保證**，而非 exactly-once。stalled 重拉是重複執行的根源，它不是 bug，是這套機制為了「worker 死了工作不丟」必須付出的代價——你要嘛容忍「死了不丟、但偶爾做兩次」，要嘛容忍「絕不做兩次、但 worker 死了就丟」，沒有第三條路在這個層次免費供應。BullMQ 選了前者。因此，**任何有副作用的工作處理器都必須是冪等的**（冪等的定義與冪等鍵的生命週期見〈重複是常態：冪等與去重〉）——這是用它的前提，不是可選的最佳實踐。

BullMQ 還在這之上放了一道閘：一份工作被判 stalled 的次數有上限（`maxStalledCount`，預設 1）。超過上限，它不再被當成「值得再試一次的倒楣工作」，而被直接打進 failed——因為一份反覆讓 worker 停滯的工作，很可能本身就有問題（例如它就是會把 event loop 卡死），無限重拉只會反覆毒害你的 worker 池。

## 把重複算出來：一個 worked example

抽象的「at-least-once 會重複」不夠有體感，把它算成具體數字才看得到該防什麼。

假設一個 worker 池要處理 100 萬份工作，每份平均跑 2 秒。某次滾動部署、加上零星的 OOM，造成大約 **0.05%** 的工作在處理途中、worker 被殺。這些工作的鎖會在最多 30 秒後過期，被 stalled checker 抓到、搬回 wait、由活著的 worker 重新處理：

```
重複執行的工作數 = 1,000,000 × 0.0005 = 500 份
```

500 份會被執行第二次。如果這些工作是「寄一封通知信」「對信用卡扣一筆款」這類**有外部副作用**的事，而處理器沒有冪等保護，那就是 500 次重複寄信、500 次重複扣款。沒有人在程式裡寫了 bug，每一行邏輯都對——重複純粹來自「worker 會死、死了工作要被接手」這個不可迴避的機制。

再把鎖續租的窗口算進來看一個更細的危險。假設一份工作偶爾會跑超過 `lockDuration`（30 秒），但 worker 的續租是每 15 秒一次。正常情況下續租撐住了鎖。但若這份工作的處理器內部有一段**長達 30 秒以上的同步阻塞**（一個沒有 `await` 讓出的大迴圈），那 15 秒的續租根本排不進 event loop——鎖照樣過期，工作照樣被判 stalled、被另一個 worker 領走並行處理。這告訴你一件實務上很反直覺的事：**讓工作冪等還不夠，你還得讓處理器別把 event loop 餓死**，否則連續租這道保命機制都會失效。CPU 密集的工作真正該做的，是搬去 worker thread 或拆成可讓出的小步（見〈thread pool 與 worker threads：CPU 密集怎麼辦〉），而不是賭它能在 30 秒內算完。

## 重試、退避與「失敗」的兩種長相

工作會以兩種完全不同的方式「失敗」，這兩種在 BullMQ 裡走不同的路，值得分清。

第一種是處理器**主動拋出例外**——它跑了、它知道自己失敗了（下游回 500、資料格式不對）。這種失敗 BullMQ 看得見：它根據工作的 `attempts` 與 `backoff` 設定決定要不要重試。若還有剩餘嘗試次數，工作不會立刻回 wait，而是被放回 **delayed** 集合、score 設成「現在 + 退避時間」——也就是說，**重試是用延遲機制實作的**，一份等著退避後重試的工作，和一份本來就排程在未來的工作，住在同一個 sorted set 裡。退避策略可以是固定間隔，也可以是指數退避（每次失敗等待時間翻倍）。指數退避加上抖動（jitter）是避免「一群工作同時失敗、又同時重試、再一起打爆已經很虛弱的下游」的標準防線（重試、退避與 jitter 的完整機制見〈重試、退避與 jitter〉）。

第二種失敗是前一節講的 stalled——處理器**沒有機會拋例外**，因為它連同整個 worker 一起消失了。BullMQ 看不到任何例外，只看得到「鎖過期了」。這種失敗走 stalled checker 那條路被搬回 wait 重新處理，而不是走 `attempts`/`backoff` 那條路。兩種失敗的計數也分開：`attempts` 數的是「處理器拋例外的次數」，`maxStalledCount` 數的是「停滯的次數」。一份工作可能拋例外重試了幾次、又因某次 worker 崩潰停滯了一次——它們是兩本獨立的帳。

當一份工作把所有重試都用光、或停滯次數超標，它落入 failed。它不會默默消失：它留在 failed sorted set 裡，帶著最後一次的錯誤堆疊，等你檢視、手動 retry，或被監控告警撈出來。這個「失敗的工作留有屍體可驗」的性質，是工作佇列相對於「丟了就不知道」的天真實作最實際的價值之一——你永遠能回答「那 500 份報表後來怎麼了」。

## 它的耐久性，不會比底下那台 Redis 高

到這裡 BullMQ 看起來相當穩固：移交而非搬走、鎖續租、stalled 接手、重試退避、失敗留痕。但有一條天花板必須講明白，否則會在最壞的時候給你錯誤的安全感：**整個工作佇列的耐久性，等於底層那台 Redis 的耐久性，一分不多。**

工作不是存在某個專為耐久設計的儲存裡，它就是 Redis 裡的幾個 key。所以「worker 死了工作不丟」這個保證，前提是**Redis 自己記得住那些 key**。而 Redis 的持久化是有縫的：在預設的 `appendfsync everysec` 設定下，AOF 每秒才 fsync 一次，意味著 Redis 行程若在某次 fsync 之間崩潰，**最近這一秒內寫入的工作可能跟著消失**（RDB 快照與 AOF 的取捨見〈Redis 的內部〉）。把 fsync 關掉換吞吐，這個窗口還會更大。換句話說，BullMQ 給你的所有「不丟」承諾，都疊在「Redis 沒丟」這個前提上——一旦 Redis 因為崩潰、或主從切換時尚未複製到副本的那段資料丟失，BullMQ 再嚴謹的狀態機也救不回來。這不是 BullMQ 的缺陷，是它選擇 Redis 當後端的本質後果。

這條天花板直接劃出了它的適用邊界。如果你的工作是「寄行銷信」「產縮圖」「重送 webhook」——偶爾丟一份在統計上可接受、或本來就會被別處補上——那麼 Redis 那一秒的窗口完全不是問題，而你換到的是「手邊已有的 Redis 就能跑、不必再養一個 broker」的巨大便利。但如果你的工作是「這筆款一定要扣、一筆都不能漏」這種金融級的耐久要求，把它建在「最近一秒可能蒸發」的後端上就是把房子蓋在裂縫上——那種需求該走有更強耐久保證的託管佇列（像 SQS 那種把訊息落進多副本儲存的，見〈SQS：Standard 與 FIFO〉），或在工作佇列之外另設一道帳本對帳。

順帶一提規模這條軸：因為 Redis 的指令執行是單執行緒的，整條佇列的吞吐最終被單一 Redis 實例的處理能力與記憶體封頂。你可以靠多個 worker 行程平行**處理**工作來擴展消費端，但它們全都打同一台 Redis；要再往上推，得分多條佇列、多個 Redis，而不是無限往單台堆。這也是 Redis-backed 佇列的甜蜜點落在「中等吞吐、要豐富的工作語意（延遲、優先序、排程、重試）」而非「百萬 TPS 的事件洪流」的原因。

## 為什麼是這個形狀

退一步看，BullMQ 的整個樣貌，都是從一個約束底下長出來的：**Redis 本身不是工作佇列，它只給你 list、sorted set、hash 和原子的 Lua 腳本——你得用這些零件拼出佇列該有的一切。**

正因 list 的 `BRPOP` 是破壞性的、會在崩潰窗口裡吃掉工作，所以要「移交到 active 並上鎖」而非「搬走」。正因沒有人能可靠地知道一個沉默的 worker 是死是活，所以鎖必須是會過期的租約、必須靠續租證明還活著、必須有 stalled checker 在租約失效時接手——而這條接手機制的代價，就是 at-least-once 與「處理器必須冪等」這個不可商量的前提。正因「五秒後做」和「失敗後退避再做」本質上都是「未來某時刻才該進 wait」，所以它們共用同一個 sorted set、共用同一套 marker 喚醒。正因工作就是 Redis 的 key，所以這套機制再嚴謹，耐久性也釘死在 Redis 的持久化天花板上。

下次你在一個 Node.js 服務裡 `queue.add('send-report', data)`、然後在另一個行程的 worker 裡看著它被處理，你看到的不是魔法，而是一台你早就有的 Redis，被一層 Lua 腳本與租約邏輯，編織成了一個會記得、會接手、會重試、但偶爾會做兩次的工作佇列。它買到的是「不必多養一個 broker」的便利，付出的是「冪等是你的責任、耐久性只到 Redis 為止」的代價——這組取捨成立的時候，它就是手邊那台 Redis 能給你的、最省力的那條路。

## 延伸閱讀

- BullMQ 官方文件 — Architecture（工作狀態與生命週期）: https://docs.bullmq.io/guide/architecture
- BullMQ 官方文件 — Stalled jobs（鎖、續租與 stalled 偵測）: https://docs.bullmq.io/guide/jobs/stalled
- BullMQ 官方文件 — Delayed jobs（延遲投遞與 marker 機制）: https://docs.bullmq.io/guide/jobs/delayed
- BullMQ — "Better queue markers in BullMQ v5"（marker + BZPOPMIN 設計說明）: https://bullmq.io/news/231204/better-queue-markers/
- BullMQ GitHub（Taskforce.sh 維護的後繼者，含 Lua 腳本實作）: https://github.com/taskforcesh/bullmq
- Bull GitHub（OptimalBits，已進入 maintenance 模式的前身）: https://github.com/OptimalBits/bull
- Redis Streams 文件（Redis 上另一種 at-least-once 訊息原語的對照）: https://redis.io/docs/latest/develop/data-types/streams/
