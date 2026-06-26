# PostgreSQL 與 MySQL：兩種隔離哲學

你把一個應用從 MySQL 搬到 PostgreSQL，連線字串換掉、SQL 方言上的幾處差異補好，測試都綠了，上線。隔離級別你沒動——兩邊本來就都跑在預設，而你記得兩邊的預設都叫某個再熟悉不過的名字。幾週後，一個值班排班的功能開始出現詭異的資料：偶爾整個班次沒人值班，雖然程式裡明明寫著「至少留一人」。它在舊系統跑了三年沒事。

問題不在你的程式碼，也不在哪個版本有 bug。問題在於：**MySQL 的預設隔離級別和 PostgreSQL 的預設隔離級別，雖然在某種意義上對得起來，但它們在底下用完全相反的機制實作並發控制，於是對「同一段並發程式碼到底安不安全」給出不同的答案。** 更糟的是，這兩個資料庫各有一個隔離級別**叫同一個名字**——Repeatable Read——而這兩個同名的級別，保證的東西並不一樣。

這一章要講的不是「PostgreSQL 比較好還是 MySQL 比較好」這種沒有答案的問題。要講的是一件更底層、也更有用的事：當兩個工程師都說「我跑在 Repeatable Read」，他們可能在說兩件不同的事——因為這兩個資料庫面對「並發交易會打架」這個古老問題時，做了哲學上相反的選擇。一個選擇**樂觀**：先讓大家跑，事後偵測到誰踩到誰，把其中一個交易槍斃掉、要它重來。一個選擇**悲觀**：先把該鎖的範圍鎖住，寧可讓你等，也不讓衝突發生。理解這個分岔，你就理解了為什麼上面那個排班功能會在搬家後壞掉。

## 先把戰場畫清楚：隔離級別到底在管什麼

退一步，所有隔離級別要解的是同一個問題：多個交易同時碰同一份資料，引擎要決定**容許它們看到彼此到什麼程度**。完全不容許——每個交易都像獨佔整個資料庫——就是 serializable，最強、最貴。容許得越多，並發越好、但會漏出各種讀寫交錯的怪現象。

這些怪現象有名字，由弱到強排：**dirty read**（讀到別人還沒 commit 的值）、**non-repeatable read**（同一列讀兩次值變了）、**phantom read**（同一個範圍查詢兩次，回傳的列集合變了——有人在範圍裡插了或刪了列）。SQL 標準就是用「禁止哪幾種現象」來定義四個級別。這裡有個關鍵的、本章從頭到尾都繞著它打轉的事實：**SQL 標準只定義了名字和「禁止哪些現象」，沒有規定引擎要用什麼機制去達成。** 名字是一份壞契約——同一個名字，不同的引擎可以用天差地別的內部機制去兌現，兌現的「程度」也可能不同。

而且標準的四現象還漏了一個著名的洞：**write skew（寫偏序）**。兩個交易各自讀一個重疊的資料集、各自據此寫**不同的列**——單獨看每個交易都合法，合起來卻打破了一個跨列的不變量。排班就是教科書級的例子：值班表上現在有兩個人，規則是「任何時候至少留一人」。醫生 Alice 和醫生 Bob 同時想請假。

- Alice 的交易讀到「現在有 2 人值班」，2 ≥ 1，於是把自己設為休假。合法。
- Bob 的交易**同時**讀到「現在有 2 人值班」（他看不到 Alice 那筆還沒 commit、或在自己快照之外的更新），2 ≥ 1，於是把自己設為休假。也合法。
- 兩個交易各自只改了**自己那一列**，沒有任何一列被兩個交易同時寫。兩邊都通過檢查、都 commit。

結果：零人值班。沒有任何單筆 `UPDATE` 是錯的，是它們**合起來**錯了。write skew 的致命之處正在於——**沒有任何一列被兩個交易同時寫**，所以靠「寫同一列就排隊」的行鎖根本攔不到它。它落在標準四現象的範圍之外，於是「禁止 phantom」那個級別也不保證擋得住它。

這個排班場景會是本章的脊椎。我們要讓它在 PostgreSQL 和 MySQL 各自的預設與最高級別下各跑一遍，看兩種哲學在同一個現場給出什麼不同的結局。

## PostgreSQL：純 MVCC，與一個誠實到惱人的事實

PostgreSQL 走的是純 MVCC（多版本並發控制）路線。寫不就地覆蓋舊值，而是產生新版本；讀去找「對我這個快照可見」的那個版本，於是讀不擋寫、寫不擋讀。舊版本留在 heap 裡，靠背景的 VACUUM 回收（MVCC 的引擎細節是另一個主題，見〈MVCC：讓讀不擋寫〉）。

它的預設隔離級別是 **Read Committed**：每一條語句都重新取一次快照，看到的是「這條語句開始那一刻已經 commit 的資料」。這是最務實的預設——絕大多數 OLTP 不需要更強。

但這章的戲在它的 **Repeatable Read**。PostgreSQL 的 RR 給整個交易一個固定的快照：交易第一條語句取一次快照，之後整個交易都透過這個快照看世界，看不到任何在交易開始後 commit 的東西。這帶來一個直接的後果——它**比 SQL 標準的 RR 還強**：標準的 RR 容許 phantom，但 PostgreSQL 的 RR 連 phantom 都不會出現（你的範圍查詢看的是固定快照，別人插的新列你根本看不見）。

說穿了，PostgreSQL 的 Repeatable Read **就是 snapshot isolation**。官方文件對這件事誠實到近乎刺眼——它明確寫著，在這個級別下「Serialization Anomaly 仍然 Possible」。換句話說，PostgreSQL 親口告訴你：**我的 Repeatable Read 不防 write skew。** 把排班場景放進 PostgreSQL 的 RR：Alice 和 Bob 的交易各自看自己那份固定快照，都看到 2 人、都通過檢查、都改自己那列、都 commit。零人值班。引擎不會攔你——它從沒承諾要攔。

這不是 bug，是 snapshot isolation 的定義本身就有的洞。理解這一點，你已經比「以為 RR 就是安全的可重複讀」往前走了一大步。

## SSI：讓 serializable 不必上一堆讀鎖

要在 PostgreSQL 上真正堵住 write skew，得升到 **Serializable**。而 PostgreSQL 的 Serializable 用的機制叫 **SSI（Serializable Snapshot Isolation，可序列化快照隔離）**——這是本章前半最值得在腦中重放的一塊。

傳統要做到真 serializable 的辦法是 2PL（兩階段鎖）：連讀都要上讀鎖，並持有到交易結束。讀鎖一上，並發就崩——讀者擋住寫者。SSI 的洞見是：**不要上讀鎖去「預防」衝突，而是讓交易照常跑在 snapshot isolation 上、暗中追蹤誰讀了誰寫了什麼，事後判斷這組交易合起來有沒有可能不可序列化；有，就中止其中一個。** 這是樂觀的精神：先放行，出事再回滾。

它怎麼追蹤？關鍵概念是 **rw-dependency（讀寫依賴，又叫 rw-antidependency）**：交易 T1 讀了某筆資料，而 T2 寫了同一筆（並且 T1 的快照看不到 T2 那個寫）——這代表「如果照可序列化的順序排，T1 必須排在 T2 前面」（T1 看到的是 T2 改之前的世界）。SSI 用 **predicate locking（謂詞鎖）** 來捕捉這種依賴：交易讀資料時，引擎在讀到的範圍上放一種特殊的、非阻塞的 **SIREAD lock**——它不擋任何人，純粹是個記號，用來在事後判斷「如果某人寫了這塊，會不會和我這個讀構成 rw-dependency」。

真正的判斷標準漂亮得令人意外。理論結果是：snapshot isolation 下每一種異常，在交易依賴圖裡都對應一個環，而**這種環一定包含一個「危險結構」——一個交易身上同時有一條進來的 rw-dependency 邊、和一條出去的 rw-dependency 邊**（兩條相鄰的 rw-antidependency 邊，那個中間的交易叫 pivot）。SSI 不去找完整的環（那很貴），它只盯這個局部結構：**只要看到某個交易同時是某條 rw-dependency 的「被讀方」又是另一條的「讀方」，就拉警報、中止其中一個交易**，回報那句你遲早會在 log 裡見到的 `ERROR: could not serialize access due to read/write dependencies among transactions`。

把排班場景放進來：Alice 的交易讀了「值班人數」（在那塊資料上放了 SIREAD lock），然後寫了自己那列；Bob 的交易也讀了「值班人數」（同樣放 SIREAD lock），也寫了自己那列。Alice 的寫，落在 Bob 讀過、放了 SIREAD lock 的範圍裡——一條 rw-dependency 從 Bob 指向 Alice；Bob 的寫，落在 Alice 讀過的範圍裡——一條 rw-dependency 從 Alice 指向 Bob。兩條相鄰的 rw-antidependency，危險結構成立。引擎在 commit 時偵測到，中止其中一個，回報 `could not serialize`。被中止的那個交易**從頭重跑**——重跑時它會看到對方已經請了假、現在只剩 1 人、規則不允許，於是正確地被擋下。write skew 被堵住了，而且全程沒有任何讀鎖擋住任何人。

這裡藏著一個非顯然、但你一定要知道的後果：**SSI 把「資料錯」這個問題，換成了「交易被中止、要重試」這個問題。** PostgreSQL 的 Serializable 不是一個你打開就高枕無憂的開關——它隨時可能在 commit 時把你的交易槍斃，丟回一個序列化失敗。**沒有寫 retry 迴圈，serializable 等於把這個錯誤原封不動丟給使用者看。** 用 SSI 的應用，必須把「收到 `could not serialize` 就整個交易重跑」當成正常流程的一部分，不是例外處理。

再帶兩個 SSI 的邊角，因為它們會在生產裡咬你：

第一，**SSI 會誤殺（false positive）**。它盯的是「危險結構」，但不是每個危險結構最後都真的會構成不可序列化——SSI 寧可錯殺、絕不放過，所以它有時會中止一個其實沒問題的交易。這是它換來「讀不上鎖」的代價，你只能靠 retry 吸收。

第二，**sequential scan 會放大中止率**。predicate locking 的精細度受限於引擎能在多細的粒度上放 SIREAD lock——走索引時可以只鎖到掃過的那段範圍，但一旦查詢退化成全表掃描（seq scan），引擎只能在**整張表**這個層級放謂詞鎖。於是任何對這張表的寫，都和你這個全表讀構成依賴，序列化失敗率飆升。這把一個你平常只當效能問題的東西（沒走索引），變成了一個**正確性吞吐**問題：在 SSI 下，缺索引不只讓查詢慢，還讓你的交易更常被中止重跑。

## MySQL 的相反賭注：用鎖把幻讀擋在門外

換到 MySQL（這裡指它的主力引擎 InnoDB）。它也用 MVCC——讀走一致快照、靠 undo log 還原舊版本（與 PostgreSQL 把舊版本留在 heap 不同，但那是儲存引擎的事）。但在「怎麼實作隔離」這件事上，InnoDB 走了和 PostgreSQL 相反的路：**MVCC 與鎖的混合**。

第一個會讓搬家工程師絆倒的差異：**InnoDB 的預設隔離級別是 Repeatable Read，不是 Read Committed。** 光是預設就和 PostgreSQL 不同了——同一個應用，不改任何 `SET TRANSACTION`，在 MySQL 上跑的是 RR，在 PostgreSQL 上跑的是 RC。

第二個、也是更深的差異：InnoDB 的 RR **不靠純快照擋 phantom，它靠鎖。** 這就是 **next-key lock**——它是兩種鎖的組合：**record lock**（鎖住一筆索引記錄本身）＋ **gap lock**（鎖住索引上兩筆記錄之間的「間隙」）。gap lock 是個奇特的東西：它不擋讀、也不擋對既有列的改，它**只擋一件事——別人往這個間隙裡插入新列**。把「鎖住掃過的列」和「鎖住列前的間隙」合起來，就是 next-key lock：當你在 RR 下做一個範圍掃描的鎖定讀（`SELECT ... FOR UPDATE`、或 `UPDATE`/`DELETE` 帶範圍條件），InnoDB 對「範圍內的列＋範圍內所有間隙」都上 next-key lock。於是在你交易進行中，**沒有人能往這個範圍插入新列**——phantom 被擋住了，不是因為你看的是固定快照，而是因為你**把可能長出幻影的那片空間鎖死了**。

這是一個哲學上的選擇：PostgreSQL 用「我看不見你插的新列」（快照）擋 phantom，MySQL 用「我不准你插」（鎖）擋 phantom。一個是讓幻影對你不可見，一個是讓幻影根本生不出來。

有個重要的細節值得釘住，免得你高估了 next-key lock 的覆蓋面：**只有鎖定讀和寫才上 next-key lock；InnoDB RR 下的普通 `SELECT`（非鎖定一致讀）走的還是 MVCC 快照，完全不上鎖。** 也就是說，next-key lock 保護的是「你明確要鎖的範圍」，普通的讀仍然只是看快照。這個區分會直接通向下面那個壞消息。

## 兩個 Repeatable Read 並不相等

現在把兩邊的 RR 並排，你會看到那個讓排班功能出事的真相。

PostgreSQL 的 RR ＝ snapshot isolation：強到連 phantom 都不出現，但**官方明說不防 write skew**。

MySQL 的 RR 呢？直覺會說「它用鎖，應該至少和 snapshot isolation 一樣強」——但實測指向相反的結論。Jepsen 在 2023 年對 MySQL 8.0.34 的分析裡發現，**InnoDB 的 Repeatable Read 連 snapshot isolation 都達不到**——它在並發負載下會出現 G-single（read skew）、lost update，甚至 write skew，這些異常本不該在一個真正的 snapshot isolation 下出現。原因正是上一節那個細節：InnoDB RR 的保護來自鎖，而**普通的非鎖定讀不上鎖**，於是「先用普通 `SELECT` 讀一個值、再據此寫」這種讀-改-寫模式，兩個交易的讀可以都用各自的快照、互不感知，寫下去就丟失更新或寫偏序了。它的「可重複讀」這個名字，承諾的比它實際給的多。

於是排班場景在兩邊的 RR 下會發生什麼？**兩邊都擋不住 write skew。** PostgreSQL 是因為它的 RR 就是 SI、SI 的定義本來就漏 write skew；MySQL 是因為它的 RR 連 SI 都不到、那些普通讀根本沒上鎖。同一個 bug，兩個不同的根因——而你只看名字「Repeatable Read」是看不出這層差別的。這就是為什麼那個排班功能搬家後會壞：它在舊系統能跑，往往是運氣（並發度低、剛好沒撞上），名字相同更讓人以為隔離行為會平移過去。它不會。

要在 MySQL 上真正擋住排班那種 write skew，你有兩條路。一是把那個讀**從普通 `SELECT` 改成鎖定讀**——`SELECT count(*) FROM shifts WHERE on_call = true FOR UPDATE`，主動把相關的列鎖起來，讓兩個請假交易必須排隊，後到的那個讀到「只剩 1 人」而被擋。二是升到 Serializable。

## MySQL 的 Serializable：把普通讀偷偷變成鎖定讀

MySQL 的 Serializable 和 PostgreSQL 的 SSI 是兩個世界。它沒有依賴追蹤、沒有 SIREAD lock、沒有事後中止那一套。它的做法樸素得多：**在 Serializable 下，InnoDB 把每一個普通 `SELECT` 隱式升級成 `SELECT ... FOR SHARE`**（8.0 之前寫作 `LOCK IN SHARE MODE`）——也就是給你讀過的每一列都加上共享鎖。共享鎖允許別人讀、但擋住別人改。這是 2PL 風格的悲觀做法：連讀都上鎖，而且持有到交易結束。回到排班——兩個請假交易各自的 `SELECT` 現在都對「值班的人」加了共享鎖，於是當一個交易要把某人改成休假（需要排他鎖）時，會被另一個交易的共享鎖擋住，串行化發生，write skew 被擋。代價就是 2PL 一貫的代價：讀者擋住寫者，並發掉下來、死結風險升上去。而且這個排班場景下，「死結風險」不是抽象的：兩個交易都先各自拿到了共享鎖，接著都想把自己那列升級成排他鎖去寫——兩個共享鎖互相擋住對方的升級，正是教科書級的鎖升級死結。InnoDB 的 wait-for graph 偵測到環，中止其中一個。所以悲觀派在高衝突下其實也得 retry，只是觸發的名目從「序列化失敗」換成了「死結」——retry 並沒有真的消失。

這裡有一個極容易被忽略、卻在實務裡常讓人困惑的 nuance：**這個「普通 SELECT 變成 FOR SHARE」只在 autocommit 關閉時發生。** 如果 autocommit 是開的，一個單獨的 `SELECT` 自成一個交易、而且是唯讀的——InnoDB 知道它不會再有後續動作，於是把它當成一致性非鎖定讀（普通快照讀）跑、不上任何共享鎖，也不擋別人。所以「我在 Serializable 下，讀一定會上鎖」這句話，在 autocommit 開著的單句查詢上**不成立**。要讓 Serializable 的讀鎖真的生效，得在一個顯式交易裡（autocommit off / 開了 `BEGIN`）。

把兩邊的 Serializable 對照看，哲學的分岔到這裡最清楚：

| 維度 | PostgreSQL Serializable | MySQL InnoDB Serializable |
|---|---|---|
| 機制 | SSI：依賴追蹤＋偵測危險結構＋中止重試 | 2PL 風格：普通讀隱式升級為 `FOR SHARE` 共享鎖 |
| 風格 | 樂觀：先放行，事後槍斃衝突者 | 悲觀：先上鎖，把衝突者擋在門外 |
| 讀會不會擋別人 | 不會（SIREAD 是非阻塞記號） | 會（共享鎖擋寫），但 autocommit 開的單句讀例外 |
| 應用要付什麼 | 必須能 retry（隨時被 `could not serialize` 中止） | 較低並發、死結風險；高衝突下仍須 retry，只是觸發名目是「死結中止」而非「序列化失敗」 |
| 高衝突時的痛點 | 中止率飆升、retry 風暴 | 鎖等待、並發崩、死結 |

一句話收住整章的脊椎：**PostgreSQL 用「偵測衝突後中止重試」達成可序列化（樂觀風格的 SSI）；MySQL 用「加鎖預先擋住」防住異常（悲觀風格的 next-key 與共享鎖）。** 一個賭衝突少、發生才處理；一個先上鎖、寧可擋住。這不是誰抄誰、也不是誰比較先進，是兩條都自洽、各有勝場的路。

## 兩個名字像、語意相反的 timeout 旋鈕

最後一個會在跨庫時悄悄咬你的差異，藏在死結處理上。兩邊都用 **wait-for graph**（等待圖）偵測死結——交易是節點，「T1 等 T2 的鎖」畫一條邊，圖裡出現環就是死結，引擎選一個受害者中止。這部分兩邊一致（鎖與死結的機制細節見〈鎖與死結：行鎖、gap、next-key 與 wait-for graph〉）。

但兩邊各有一個帶 timeout 的旋鈕，名字像、語意完全不同，混用會讓你調錯東西：

- PostgreSQL 的 `deadlock_timeout`，**預設 1 秒**。它的意思是「一個交易等鎖等了這麼久之後，引擎**才開始去查**有沒有死結」。它調的是**偵測延遲**——查死結是有成本的操作，所以引擎不想每次等鎖都立刻查，先等個 1 秒、賭這只是普通的鎖等待、會自己解開；等過了還沒解，才動用 wait-for graph 去找環。它**不是**「等多久就放棄」。
- MySQL 的 `innodb_lock_wait_timeout`，**預設 50 秒**。它的意思是「一個交易等鎖等了這麼久，就**放棄**這次等待、回報錯誤」。它調的是**放棄門檻**。

兩個都是「等鎖相關的 timeout」，但一個管「何時開始查死結」、一個管「何時放棄等鎖」，語意和量級（1 秒 vs 50 秒）都不同。把它們當同一個東西調，你會在錯誤的問題上轉旋鈕。

## 為什麼是這個形狀

退到最遠處看，這整章的分歧，都從那個一開始就埋下的事實裡長出來：**SQL 標準只定義了隔離級別的「名字」和「要禁止哪些現象」，從不規定用什麼機制達成。** 名字是一份留白巨大的契約，於是兩個資料庫在這片留白裡，做了哲學上相反的填法。

PostgreSQL 選了純 MVCC，把「真 serializable」這件難事用 SSI 解——它賭的是衝突不多，所以讓大家樂觀地跑、事後偵測危險結構再中止重試，換來「讀永遠不擋寫」這個寶貴的並發性質，代價是逼應用學會 retry。MySQL 選了 MVCC 加鎖，用 next-key lock 把幻影擋在門外、用共享鎖把 serializable 撐起來——它賭的是「先擋住比事後處理單純」，把多數衝突在發生前就排成隊，代價是鎖帶來的並發損失與死結（而高衝突下 retry 並沒消失，只是名目從序列化失敗換成死結中止，如前所述）。

於是那兩個都叫 Repeatable Read 的級別，根本不是同一個東西：PostgreSQL 的是強到不出 phantom、但誠實承認不防 write skew 的 snapshot isolation；MySQL 的是靠鎖、實測下連 snapshot isolation 都不到的混合體。它們名字一樣，是 SQL 標準這份壞契約的遺產，不是它們行為一樣的證據。

所以那個搬家後零人值班的排班功能，不是哪一邊壞了。它是在告訴你一件事：**換資料庫從來不只是換連線字串。** 預設級別變了（RR↔RC）、同名級別的真實語意變了、達成 serializable 的機制變了、連死結的旋鈕語意都變了。並發正確性不會跟著連線字串自動平移——你得回到「我這段邏輯依賴的是哪個保證、這個引擎用什麼機制兌現它、在什麼條件下兌現不了」，一條一條重新對過。讀懂了這兩種哲學，你下次看到 `could not serialize` 或一片莫名的 gap lock 死結時，就會知道那不是資料庫在找你麻煩——那是它在用自己選定的方式，替你擋住那個會讓班次空掉的並發。

## 延伸閱讀

- PostgreSQL 官方文件，Transaction Isolation（明文「Repeatable Read 下 Serialization Anomaly 仍 Possible」、SSI 與 retry 要求、`could not serialize access due to read/write dependencies among transactions` 訊息）：https://www.postgresql.org/docs/current/transaction-iso.html
- PostgreSQL 原始碼樹，README-SSI（SIREAD lock、危險結構、pivot 的工程說明）：https://github.com/postgres/postgres/blob/master/src/backend/storage/lmgr/README-SSI
- Ports, Grittner, "Serializable Snapshot Isolation in PostgreSQL", VLDB 2012（SSI 在 PostgreSQL 的設計論文）：https://arxiv.org/abs/1208.4179
- MySQL 官方文件，InnoDB Transaction Isolation Levels（RR 為預設、Serializable 把普通讀升級為 `FOR SHARE` 與 autocommit 例外）：https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html
- MySQL 官方文件，InnoDB Locking（record lock / gap lock / next-key lock 的定義）：https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html
- Jepsen，MySQL 8.0.34（實測 InnoDB Repeatable Read 弱於 snapshot isolation，出現 G-single、lost update、write skew）：https://jepsen.io/analyses/mysql-8.0.34
- Berenson 等人，"A Critique of ANSI SQL Isolation Levels", SIGMOD 1995（指出標準異常定義的歧義、提出 snapshot isolation）：https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/
