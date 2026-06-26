# 2PC 與分散式交易：原子提交與它的阻塞代價

一筆轉帳要從 A 帳戶扣 100、往 B 帳戶加 100。如果這兩個帳戶在同一個資料庫裡，你不必想太多：包進一個交易，`BEGIN ... COMMIT`，引擎用它的鎖、它的 WAL（見〈WAL：先寫日誌，再改資料〉）、它的 crash recovery，替你保證了「扣款和加款要嘛一起發生、要嘛一起不發生」。原子性是免費的，因為有一個**單一的引擎**坐在那裡仲裁，它知道整筆交易的全貌，它有一個權威的時刻決定「現在 commit 了」。

把這兩個帳戶搬到兩個不同的資料庫——一個記 A 的餘額、一個記 B 的餘額，各跑各的程序、各有各的磁碟、中間隔著網路——免費的午餐就沒了。沒有哪個引擎同時看得見兩邊。你能對 A 那台下 `COMMIT`、對 B 那台下 `COMMIT`，但這是兩個獨立的動作，中間有時間差，而世界會在那個時間差裡出事：你對 A 提交成功，正要對 B 提交，B 那台機器當機了。現在 A 扣了 100、B 沒加 100，憑空蒸發了一百塊。把順序反過來也一樣——先提交 B、再提交 A，A 失敗，就憑空多出一百塊。

這就是**分散式交易**要解的問題：當一筆邏輯上不可分割的操作橫跨多個獨立的資源（多個資料庫，或一個資料庫加一個訊息佇列），怎麼讓它們**一起生效或一起作廢**，不留下「一半成功」的殘局。聽起來只是把單機交易的 ACID 拉到多台機器上，但「沒有共同引擎」這件事，比想像中難纏得多。

## 天真的做法為什麼破

先看看不動腦會怎麼做，以及它為什麼站不住。

最直覺的版本是**循序提交**：對每個資源依序下 commit，`commit(A); commit(B); commit(C)`。它的破法上面已經演過了——任何一個 commit 失敗，前面已經 commit 的就回不去了。commit 在多數資料庫裡是個不可逆的動作，一旦引擎回你「成功」，那筆變更就持久化了、就對其他交易可見了，你沒有一個乾淨的退路把它撤回。所以循序提交的失敗模式是**部分提交**，而部分提交正是我們要消滅的東西。

退一步，把問題拆成兩個獨立的子問題會清楚很多。要達成「全有或全無」，你需要兩件事：

第一，每個參與者都得能**在真正落地之前先確認自己做得到**——磁碟夠不夠、約束有沒有違反、鎖搶不搶得到——並且在確認之後，**承諾它一定能完成**，哪怕中間它崩潰重啟。如果一個參與者說「我可以」之後又反悔，原子性就無從談起。

第二，得有一個**單一的、權威的決定點**：到底是全體 commit 還是全體 abort，這個決定只能有一個來源，而且一旦做出就**不能更改**。如果讓每個參與者各自決定，網路一抖、各看各的，立刻分岔。

兩階段提交（2PC，two-phase commit）就是把這兩件事拆成兩個階段，一個階段對一個子問題。它的形狀不是誰拍腦袋設計出來的，而是這兩個約束逼出來的唯一合理解。

## 兩個階段，一步步看

2PC 引入一個 **coordinator（協調者）** 角色，其餘是 **participant（參與者）**。coordinator 可以是其中一個資源、也可以是一個獨立的交易管理器（transaction manager）。整個協定走兩階段：

```
Phase 1 — prepare (voting)
  coordinator --- "can you commit?" --> participant A, B, C
  each participant:
    do all the work, write changes to its log (NOT committed yet),
    acquire and HOLD locks, fsync the prepare record to disk,
    then reply yes (prepared) or no (abort)

Phase 2 — commit / abort (decision)
  if ALL voted yes:
    coordinator logs "commit" decision (the point of no return),
    then --- "commit" --> A, B, C ; each commits, releases locks
  if ANY voted no (or timed out):
    coordinator decides abort,
    then --- "abort" --> A, B, C ; each rolls back, releases locks
```

第一階段叫 **prepare**，也叫投票。coordinator 問所有參與者：「你能提交嗎？」每個參與者收到後，把這筆交易該做的事全部做完——執行 SQL、檢查所有約束、搶到所有需要的鎖——但**停在最後一步之前不真的 commit**。它把變更寫進自己的持久日誌（一條 prepare record，fsync 到磁碟），然後回覆 yes 或 no。

這裡有個必須講透的轉折：**一旦一個參與者投了 yes，它就進入「不確定（in-doubt）」狀態，從此失去自主權。** 它對 coordinator 做出了一個沉重的承諾——「無論接下來發生什麼，只要你叫我 commit，我保證 commit 得了」。為了兌現這個承諾，它必須在投 yes 之前就把所有變更持久化、把所有鎖牢牢握住，而且**不能單方面反悔**：它不能自己決定 abort（萬一別人都投了 yes，全體本該 commit），也不能自己決定 commit（萬一有人投了 no，全體本該 abort）。它唯一能做的事，是**等 coordinator 的最終裁決**。這個「投了 yes 就交出決定權、原地等待」的設計，是 2PC 安全性的核心，也是它一切麻煩的源頭。

第二階段叫 **commit/abort**，是那個權威的決定點。coordinator 收齊所有票：只要有一個 no（或某個參與者逾時沒回），它就決定 abort，通知所有人回滾；只有全部都是 yes，它才決定 commit。決定一旦做出，coordinator 先把它寫進自己的持久日誌——**這條 commit record 落盤的那一刻，就是整筆分散式交易的「不可回頭點」**——然後才把決定廣播給所有參與者。參與者收到 commit 就真正提交、釋放鎖；收到 abort 就回滾、釋放鎖。

你大概已經看出這套機制為什麼能保證原子性了：沒有任何參與者能在「全體決定」之前自己 commit，所以不會有人偷跑；而那個全體決定只有 coordinator 一個來源、寫進日誌後不可變，所以不會分岔。「全有或全無」就這樣被釘死了——只要一切順利。

## 把延遲算出來

2PC 的代價不是抽象的。拿一個具體的例子手算到底：一筆交易跨 3 個參與者，coordinator 到每個參與者的單程網路延遲 2 ms，每個參與者把 prepare record 或 commit record fsync 到磁碟要 5 ms。正常路徑要走多久？

prepare 階段：coordinator 送出 prepare（2 ms 在途），參與者做完事、把 prepare record 落盤（5 ms），回 yes（2 ms 在途）。因為 coordinator 是平行送給三個參與者、平行等回覆，這一階段的牆鐘時間取決於最慢的那一條，約 `2 + 5 + 2 = 9 ms`。

commit 階段：coordinator 先把 commit 決定落盤（5 ms，這一步是序列的、無法和網路重疊），再送出 commit（2 ms 在途），參與者收到後各自 commit——這裡參與者是否還要再 fsync 一次取決於實作，但即使不再額外落盤，光是 coordinator 自己的這輪 fsync 加一趟往返，量級就和 prepare 相當，粗算約 `5 + 2 = 7`，保守抓到與 prepare 同量級的約 9 ms。

兩階段串起來，正常路徑的提交延遲約 **18 ms**——而且這 18 ms 從頭到尾，三個參與者**全程持有資源鎖**。對照單機交易那種一次落盤、幾毫秒了事的提交，2PC 把延遲拉長了好幾倍，鎖的持有時間也跟著拉長。鎖持有得越久，與它衝突、被它擋住的其他交易就越多，整個系統的並發度就被這條交易壓低。這是 2PC 在「一切順利」時就得付的稅：**兩輪網路往返、兩輪 fsync、全程鎖定**。

但 18 ms 還只是好日子的價碼。真正讓 2PC 在生產上聲名狼藉的，是它壞掉時的樣子。

## 它怎麼壞：阻塞，2PC 的原罪

把那個算例往前推一步。coordinator 已經收齊三張 yes 票，三個參與者全部進入 in-doubt、全部握著鎖等裁決。就在 coordinator **即將送出 commit、但還沒送**的那一瞬間——或者更糟，commit 才送給其中一個、還沒送完另外兩個——coordinator 當機了。

現在這三個參與者陷入一個沒有出路的處境。它們都投了 yes，所以**不能自己 abort**（萬一 coordinator 的決定是 commit，自行 abort 就破壞了原子性）。它們也**不能自己 commit**（萬一有別的參與者其實投了 no、coordinator 的決定是 abort，自行 commit 同樣破壞原子性）。它們唯一能做的，就是**繼續握著鎖、無限期地等**，等那個已經死掉的 coordinator 復活、從它的持久日誌裡讀出當初的決定、重新把裁決送過來。

這就是 **2PC 的阻塞（blocking）**。它不是某個實作沒寫好的 bug，而是協定本身的數學性質：在「投了 yes 就交出決定權」這個前提下，只要那個唯一的決定來源消失，等待它的人就只能卡死。被鎖住的那些資料行，在 coordinator 恢復之前，任何想碰它們的交易全部排隊堵塞。如果 coordinator 的恢復需要幾秒（重啟、重讀日誌），那就堵幾秒；如果 coordinator 的持久日誌也壞了、需要人介入，那就堵到有人來處理——可能是幾分鐘，可能更久。

這裡值得停下來釐清一個常見的混淆：**為什麼 coordinator 不能用逾時來打破僵局？** 你可能會想，參與者等不到裁決，乾脆設個逾時、超時就 abort，不就不會卡死了嗎？問題在於，**逾時無法區分「coordinator 死了」和「coordinator 還活著、只是訊息慢了」**——這正是分散式系統裡那個分不清「慢」與「死」的老難題（見〈為什麼分散式這麼難：partial failure 與失敗模型〉）。如果參與者一逾時就自作主張 abort，而 coordinator 其實還活著、已經決定了 commit、訊息只是塞在路上，那麼這個參與者就 abort 了一筆本該 commit 的交易，原子性當場破裂。所以 in-doubt 的參與者**不能**靠逾時自行了斷，它的安全性恰恰來自「死等」。阻塞，是 2PC 為了不犧牲原子性，付出的代價。

## 為什麼這道牆繞不過去

值得追問一句：阻塞是 2PC 沒設計好，還是更深層的東西？

2006 年，Gray 與 Lamport 在〈Consensus on Transaction Commit〉裡把這件事看穿了。他們證明：**原子提交本質上是一個共識問題**——讓所有參與者對「commit 還是 abort」這個值達成不可推翻的一致決定，這和讓一群節點對 replicated log 的下一格達成共識（見〈共識：讓一群會當機的機器同意一件事〉）是同一類問題。而他們進一步指出一件直擊要害的事：**經典的 2PC，其實是他們那個更一般的 Paxos Commit 協定的一個「退化特例」——退化成只有單一 coordinator 的版本。**

這句話一旦聽懂，整個 2PC 的脆弱就有了名字。共識協定（如 Raft、Paxos）之所以能容錯，是因為它的決定由**一群節點過半同意**做出，少數幾台死掉，過半的交集仍在，決定不會丟。而 2PC 把這個「決定」的責任，**全部壓在一個 coordinator 身上**。那條 commit record 只存在 coordinator 一台機器的日誌裡——它就是那個單點。Gray-Lamport 的 Paxos Commit 用 `2F+1` 個 coordinator、只要 `F+1` 個活著就能繼續推進，正是把這個單點換成一個能容錯的群體。換句話說，2PC 的阻塞不是一個可以靠「多寫幾行程式」修掉的瑕疵，而是「只有一個決定者」這個結構的必然後果。要不阻塞，你就得讓決定本身變得可容錯——而那已經是在跑共識了。

這給了我們一個看待後面所有變體的統一視角：**它們都在回答同一個問題——怎麼讓那個唯一的決定點不再是單點。**

## 想消滅阻塞的人們，與他們撞上的牆

第一個認真嘗試的是 3PC。

**3PC（三階段提交）**，由 Skeen 在 1981 年的〈Nonblocking Commit Protocols〉裡提出。它的想法很直接：2PC 之所以阻塞，是因為參與者在 in-doubt 狀態下「不知道別人的狀態」——它知道自己投了 yes，但不知道 coordinator 是否已經決定、別人是否已經 commit。3PC 在 prepare 和 commit 之間插一個 **pre-commit** 階段：coordinator 收齊 yes 之後，先廣播一輪「準備提交」，等大家都確認收到，才送真正的 commit。多了這一輪，參與者就能在 coordinator 失聯時，根據自己處於哪個階段來推斷全體的意向、安全地自行了斷，從而不阻塞。

聽起來解決了。但 3PC 有一個**致命的前提**：它的「不阻塞」只在**沒有網路分區、只有節點崩潰**的假設下成立。Skeen 的證明假設的是一個「高度可靠的網路」——一個永遠不會把存活的節點切割成互不通訊的兩群的網路。而真實的網路**會分區**。一旦發生分區，3PC 那套「根據自己的階段推斷全體意向」的邏輯就可能在被切開的兩側得出**相反**的結論——一側推斷該 commit、另一側推斷該 abort——原子性照樣破裂，而且這次連阻塞都不阻塞了，直接給你不一致。再加上它每筆交易要多付一整輪訊息往返、更慢，於是 3PC 幾乎從未在生產系統裡認真用過。它是個漂亮的理論結果，提醒我們「不阻塞」這四個字後面藏著多大的前提。

真正可行的路，是回到 Gray-Lamport 點破的那條：**把 coordinator 的決定本身用共識複製出去。** 這正是 Google **Spanner** 走的路。在 Spanner 裡，每一片資料（split）都複製成一個 Paxos group，組內有 leader 也有 follower。當一筆交易跨多個 split 時，每個 split 的 leader 當一個參與者，其中一個 split 的 leader 兼任 coordinator——但關鍵在於，**coordinator 把它的 prepare 決定、commit 決定都當成一條 log 記錄，透過自己那個 Paxos group 複製到多個副本上**。於是「commit record 只存在 coordinator 一台機器」這個單點就消失了：原本的 coordinator 若崩潰，它的 Paxos group 會選出新 leader 接手，新 leader 從複製出來的 log 裡讀得到那個決定，繼續把它推完。2PC 仍然是 2PC——prepare、decide 兩個階段一個都沒少——只是它跨在一層共識之上，那個曾經會阻塞的單點，被換成了一個能自我修復的群體。代價是顯而易見的：每一筆 prepare、每一個決定，都要付一輪 Paxos 共識的延遲，再疊在 2PC 本身的兩輪往返之上。你買到「不阻塞」，付出的是更高的延遲與遠更複雜的實作。

## 落到地面：XA 與 in-doubt 交易的運維稅

理論之外，2PC 在工業界有一套標準化的長相：**X/Open XA**。XA 是 2PC 的標準介面——它定義了交易管理器（TM）和資源管理器（RM，通常是資料庫）之間怎麼對話：`xa_prepare`、`xa_commit`、`xa_rollback`，以及一個容易被忽略卻很重要的 `xa_recover`。多數主流關聯式資料庫都實作了 XA 介面。

具體到 PostgreSQL，2PC 的指令是 `PREPARE TRANSACTION '<gid>'`（投 yes、進入 prepared 狀態，但不真的提交）、`COMMIT PREPARED '<gid>'`、`ROLLBACK PREPARED '<gid>'`。這裡有個第一次用會踩到的細節：PostgreSQL 預設**根本不開** prepared transaction——參數 `max_prepared_transactions` 預設是 0，你得手動把它設成非零（官方建議設成跟 `max_connections` 一樣）才能用。這個「預設關閉」不是疏忽，恰恰是因為 prepared transaction **危險**。

危險在哪？一個 `PREPARE TRANSACTION` 過的交易，**會一直持有它當初握住的所有鎖**，直到有人對它下 `COMMIT PREPARED` 或 `ROLLBACK PREPARED`。如果負責收尾的交易管理器崩潰了、或者根本忘了這筆交易，它就變成一個**孤兒（orphaned）prepared transaction**——一筆永遠停在 in-doubt、永遠握著鎖、永遠不會自己消失的交易。它的破壞力不只是擋住其他想碰那些行的交易：因為它在資料庫眼中是一筆「還沒結束的最老交易」，它會**卡住 VACUUM 回收舊版本**，讓死掉的 row 版本堆積，極端情況下逼近 transaction ID wraparound，最後可能逼整個資料庫停機自保。一筆被遺忘的 prepared transaction，能從一個小角落拖垮整台資料庫。

這就是 2PC 那條隱形的長期稅單：用了 XA/2PC 的系統，**運維人員必須懂得處理 in-doubt 交易**。他們得會用 `xa_recover`（或 PostgreSQL 的 `pg_prepared_xacts` 視圖）把卡住的交易撈出來，判斷每一筆該 commit 還是該 rollback，然後手動下 `COMMIT PREPARED` / `ROLLBACK PREPARED` 把它了結。

而「判斷該 commit 還是 rollback」這件事，本身就是個地雷。XA 規格裡有一個叫 **heuristic decision（啟發式決定）** 的機制：當 RM 等不到 TM 的最終裁決、又急著釋放被卡住的鎖時，它可以**繞過 TM、自行**決定 commit 或 rollback 一筆 in-doubt 的分支。這是一條應急的逃生門，但走它要冒一個明確的風險——如果某個 RM 啟發式地 commit 了它那一支，而 TM 最終的全體決定其實是 abort，那麼這個分支就和其他分支**永久地不一致**了，而且這個不一致是**靜默**的，資料庫不會替你報錯，得靠對帳（見〈對帳：怎麼確認兩邊一致、漂移怎麼修〉）才抓得出來。heuristic decision 是 2PC 在「鎖卡太久」和「可能不一致」之間，留給人類的一個沒有好答案的選擇題。

順帶澄清一個常被混為一談的點：2PC 解的是**跨資源的原子提交**，它和「訊息只送達一次」是兩回事。「全體 commit 成功」不等於「下游只收到一次通知」——交付語意是另一條獨立的線（見〈三種交付語意：at-most、at-least、exactly-once〉），別把跨資源原子性的勝利，誤當成解決了跨網路的重複投遞。

## 大多數人其實不需要 2PC

把帳算到這裡，2PC 的適用範圍就很清楚了。它買到的是真正的、強的、「同一瞬間全有或全無」的原子性；它收的費是：兩輪往返的延遲、全程的鎖持有、一個會阻塞的單點（除非你疊上共識）、以及一條沒人想處理的 in-doubt 運維稅。這個交易在什麼時候划算？

**當參與者少、都在同一個機房（網路快又穩、分區罕見）、交易頻率低、但每一筆都絕對不容許「一半成功」時**——比如一筆橫跨兩個內部資料庫的資金移轉，一天沒幾筆，但錯一筆就是真金白銀的帳目錯誤——2PC 的強原子性值得它的代價，而你也能接受它在 coordinator 故障時鎖住資源、等人來收的最壞情況。

反過來，**跨微服務、跨網際網路、高頻**的場景，2PC 幾乎總是錯的選擇。把那個會阻塞的單點、那條全程鎖定的同步路徑，放進一個每秒幾千筆、參與者散在不同團隊不同網路的系統裡，它的阻塞就不再是偶發的運維事件，而會在某次網路抖動時放大成系統性的雪崩——一筆卡住的交易堵住一批鎖，被堵的交易又堆積、又超時、又重試，整條鏈一起僵住。

所以絕大多數現代分散式系統，**刻意不追求全域原子性**，改用最終一致的替代品。最常見的兩條路：一是 **saga**——把一筆長交易拆成一串各自獨立提交的本地交易，每一步配一個「補償動作」，萬一中途失敗就反向跑補償、語意上撤銷已完成的步驟，用最終一致換掉全域鎖（saga 的補償語意與 choreography / orchestration 取捨，見〈跨服務的交付一致：outbox 與 saga〉）。二是 **outbox**——用一個本地交易，把業務變更和「待發事件」原子地寫進同一個資料庫，再非同步可靠地把事件投遞出去，從根本上避開「同時寫資料庫和訊息佇列」這種跨資源 dual-write（見〈跨服務的交付一致：outbox 與 saga〉與〈dual-write 問題與 event-carried state transfer〉）。這兩條路都放棄了「同一瞬間全有或全無」，換來的是中間態會短暫可見、但沒有阻塞、沒有單點、可水平擴展。

判準其實只有一句話：**你真的需要「同一瞬間、全有或全無」的強原子性，還是「最終都會一致、中間態短暫可見」就夠了？** 把這個問題誠實地問下去，你會發現絕大多數業務流程是後者——使用者下單後庫存稍晚一刻才扣、積分稍晚一刻才加，這些「最終一致」帶來的短暫不一致，遠比 2PC 的阻塞風險容易承受。真正需要前者的場景，少到你應該對「我這裡需要 2PC」這個念頭，先保持懷疑。

## 為什麼是這個形狀

退一步看，2PC 的整副樣貌，都是從一個無法迴避的事實裡長出來的：**跨多個獨立資源做原子提交，本質上是一個共識問題，而共識在「分不清慢與死」的網路上沒有免費的解。**

正因為要「全有或全無」，所以得有一個權威的決定點，不能各自為政——這逼出了 coordinator。正因為參與者必須先承諾「我一定做得到」才能被納入這個全體決定，所以它得先持久化、先鎖住、再投票——這逼出了 in-doubt 狀態。正因為 in-doubt 的參與者不能靠逾時自行了斷（逾時分不清 coordinator 是死是慢），所以它只能死等——這逼出了阻塞。而正因為那個權威決定壓在單一 coordinator 身上，這個單點一倒，等待它的人就無路可走——這就是 Gray-Lamport 說的「2PC 是單 coordinator 的退化共識」的全部含意。3PC 想用多一個階段繞過阻塞，卻被網路分區擋了回去；Spanner 想真正消滅單點，代價是把整個協定架在一層共識之上。沒有一條路是便宜的，因為它們都在償還同一筆債：在一個會延遲、會分區、會當機的世界裡，硬要一群互不相見的機器在同一個瞬間步調一致。

下次你看到一筆 XA 交易卡在 in-doubt、DBA 對著 `pg_prepared_xacts` 皺眉，或者一個架構評審裡有人提議「跨這三個服務上 2PC 保證一致」時，你會知道那張帳單上寫著什麼——以及，為什麼大多數時候，正確的答案是把「同一瞬間全有或全無」這個願望，換成一個能被最終一致兜住的、不會在半夜鎖死你資料庫的設計。

## 延伸閱讀

- Gray, Lamport, "Consensus on Transaction Commit", ACM TODS 31(1):133-160, 2006（證明 2PC 是單 coordinator 的退化共識、提出可容錯的 Paxos Commit）: https://dl.acm.org/doi/10.1145/1132863.1132867
- Skeen, "Nonblocking Commit Protocols", ACM SIGMOD 1981（3PC 的源頭，與「不阻塞」的前提）: https://dl.acm.org/doi/10.1145/582318.582339
- X/Open Distributed Transaction Processing: The XA Specification（2PC 的標準介面、heuristic decision 的定義）: https://pubs.opengroup.org/onlinepubs/009680699/toc.pdf
- PostgreSQL 官方文件 — PREPARE TRANSACTION（prepared transaction 的語意、孤兒交易與鎖的危險）: https://www.postgresql.org/docs/current/sql-prepare-transaction.html
- Corbett et al., "Spanner: Google's Globally-Distributed Database", OSDI 2012（2PC 跨在 Paxos group 之上以消除 coordinator 單點）: https://research.google/pubs/spanner-googles-globally-distributed-database/
- Garcia-Molina, Salem, "Sagas", ACM SIGMOD 1987（用補償交易與最終一致替代分散式原子提交的原始提案）: https://dl.acm.org/doi/10.1145/38713.38742
