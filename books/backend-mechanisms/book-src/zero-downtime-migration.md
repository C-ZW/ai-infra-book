# 零停機 schema 遷移：expand-contract 與 backfill

凌晨兩點，一個看起來無害的 migration 上線：把訂單表的 `status` 欄改名，從 `state` 改成 `status`，順手把型別從 `varchar` 收緊成 `enum`。SQL 只有一行：

```sql
ALTER TABLE orders RENAME COLUMN state TO status;
```

在你的筆電上、那張只有幾百列的測試表，它在零點幾毫秒內跑完。在生產環境那張三億列、每秒承接幾千筆寫入的表上，這一行做了兩件你沒料到的事：第一，它要拿一把 `ACCESS EXCLUSIVE` 鎖——這把鎖和**所有東西**互斥，包括最普通的 `SELECT`；第二，它得排在當前所有未結束的交易後面才拿得到鎖，而它一旦排進等待佇列，**後到的讀寫也全部卡在它後面**。於是一個本來只需毫秒的 metadata 變更，因為前面有一筆跑了三十秒的報表查詢，硬生生把整張訂單表凍結了三十秒。在這三十秒裡，沒有人能下單、沒有人能查單。

更糟的還在後面。就算鎖瞬間拿到、`RENAME` 真的只花幾毫秒，那一刻舊版本的應用程式還在線上、還在發 `INSERT INTO orders (..., state) VALUES (...)`——欄位已經不叫 `state` 了，這些寫入全部報錯。你用一行 SQL 製造了一次部署事故，而它在測試環境完全看不出來，因為測試環境沒有「同時還活著的舊程式」這個維度。

這一章談的，就是怎麼讓資料庫的結構演化——加欄、改型別、改約束、搬資料——在**一個高吞吐、不能停的系統上**安全發生。核心的難點從來不是「怎麼改 schema」，SQL 語法誰都會寫；難點是**改 schema 的那一瞬間，系統並沒有為你停下來**：舊程式還在跑、新程式正在滾動上線、讀寫從不間斷。零停機遷移的全部技藝，是在這個「沒有人停下來等你」的前提下，把一次危險的瞬間切換，拆成一連串各自安全的小步。

## 為什麼一行 DDL 這麼危險：鎖與相容性兩條獨立的引線

把上面的事故拆開，會看到兩條**互不相干**的引線，各自都能引爆，而且常被混為一談。

第一條是**鎖**。資料庫的結構變更幾乎都要改 system catalog（描述「表長什麼樣」的元資料），而改 catalog 通常需要一把排他鎖。在 PostgreSQL 裡，大部分 `ALTER TABLE` 動作拿的是 `ACCESS EXCLUSIVE`——這是最強的表鎖，和包括 `SELECT` 在內的任何操作都衝突。鎖本身持有多久不是重點，重點是兩件事：一是某些 DDL 不只改 catalog，還要**重寫整張表**（rewrite），那會把鎖持有到整張表掃完、可能是好幾分鐘；二是**等鎖的過程會擋住後面所有人**——PostgreSQL 的鎖等待是有序佇列，一個在等 `ACCESS EXCLUSIVE` 的 DDL 會讓它之後到達的讀寫全部排在它後面，即使那些讀寫彼此根本不衝突。所以一筆長交易 ＋ 一個想拿強鎖的 DDL，兩者相乘就是一場全表凍結。

第二條是**相容性**。部署不是一個瞬間，是一段「新舊版本並存」的窗口——滾動更新（rolling update）期間，叢集裡有些 pod 跑新程式、有些還跑舊程式，它們**打的是同一個資料庫**。schema 在這個窗口裡只能有一個樣子，而它必須同時讓新舊兩版程式都能正常讀寫。任何「舊程式看得懂、新程式看不懂」或反過來的 schema 狀態，都會在部署窗口裡讓一半的流量報錯。`RENAME COLUMN` 之所以致命，正是因為它在同一瞬間既動了鎖、又破壞了相容性——它把欄位從舊程式腳下抽走了。

這兩條引線要分開記，因為它們的解法不同。鎖的問題靠「選對 DDL 形式、避開 rewrite、避開長時間持鎖」解決；相容性的問題靠「永遠不做破壞性的單步變更，改成一連串向後相容的小步」解決。把兩者都解乾淨，才叫零停機。而把「一連串向後相容的小步」這件事系統化的方法，有個名字：**expand-contract**。

## 第一原理：schema 永遠要對「兩個版本的程式」都成立

天真的遷移在腦中的模型是這樣的：應用程式和資料庫一起、原子地、從舊狀態跳到新狀態。畫成圖是一條乾淨的線：舊 app + 舊 schema → 新 app + 新 schema。

但生產環境裡這條線不存在。真實的時間軸上，app 和 schema 是**分開部署、各自滾動**的，於是你必然會經過這些中間狀態：舊 app 配新 schema（schema 先上、app 還在滾）、新 app 配舊 schema（app 先上、migration 還沒跑或正在跑）。零停機的第一原理可以濃縮成一句話：

> **在任何時刻，當前的 schema 必須同時相容於「即將被淘汰的舊程式」和「正在上線的新程式」。**

這句話一旦接受，遷移的形狀就被決定了。你不能做任何「讓某一版程式立刻失效」的單步變更——不能直接改名、不能直接刪欄、不能直接收緊一個現有資料還不滿足的約束。你能做的，只有**先擴張、再收縮**：先把新結構**加上去**，讓 schema 變成新舊兩版都能用的「超集」狀態；等所有舊程式都退場了、資料也都搬好了，再把不再有人用的舊結構**拿掉**。

這就是 expand-contract（也叫 parallel change，Martin Fowler 給它的名字；資料庫場景下的系統化最早來自 Ambler 與 Sadalage 的《Refactoring Databases》）。它把一次破壞性變更拆成三段：

- **expand（擴張）**：加入新結構，與舊結構並存。這一步永遠是**向後相容**的——它只增加，不拿走任何舊程式依賴的東西。
- **migrate / transition（過渡）**：讓資料和讀寫流量從舊結構平滑搬到新結構。包含 backfill（把存量資料填進新結構）和 dual-write（讓寫入同時落到新舊兩邊）。這一步可能橫跨多次部署、持續數小時到數天。
- **contract（收縮）**：當再也沒有任何程式碼依賴舊結構時，才把它刪掉。

關鍵的洞見是：**每一步單獨拿出來，都是一個向後相容、可隨時回滾的小變更**。沒有任何一步會讓「現在線上的某一版程式」失效。危險的不是「改 schema」，而是「在一步裡同時加新的、拿走舊的」——expand-contract 的全部價值，就是把這個危險的同時性拆開。

## 把一次改名走完：expand-contract 的七步

抽象講完，落到最常見也最有代表性的場景：把 `orders.state` 改名為 `orders.status`。我們不用 `RENAME`，用 expand-contract 把它走一遍，每一步標清楚它做了什麼、為什麼安全。

**步驟 1（expand）：加一個新欄 `status`，可為 null，不設預設值。**

```sql
ALTER TABLE orders ADD COLUMN status text;
```

這一步在現代 PostgreSQL（11 以後）是廉價的：加一個**可為 null、無預設值**的欄，只改 catalog、不碰任何既有資料列，`ACCESS EXCLUSIVE` 鎖只持有幾毫秒。舊程式完全不受影響——它根本不知道 `status` 存在，照舊讀寫 `state`。新欄此刻是空的，沒有任何讀者。

這裡藏著第一個非顯然的邊界，下一節會專門講：**一旦給它帶上 `DEFAULT` 或 `NOT NULL`，這一步的代價會天差地別。**

**步驟 2（expand 程式）：部署一版程式，寫入時同時寫 `state` 和 `status`（dual-write）。**

新版程式每次寫訂單，兩個欄都填一樣的值。但**讀取還是讀舊欄 `state`**——因為此刻 `status` 對存量資料還是空的，讀它會讀到一堆 null。這一版程式對舊 schema 也相容（`status` 欄已經在步驟 1 加好了），所以它能安全地滾動上線，和還沒更新的舊 pod 並存：舊 pod 只寫 `state`，新 pod 寫 `state` + `status`，兩者都不報錯。

**步驟 3（migrate）：backfill——把存量資料的 `status` 補上。**

```sql
-- 分批跑，不是一條 UPDATE 掃全表
UPDATE orders SET status = state
WHERE status IS NULL AND id BETWEEN ? AND ?;
```

這是整個遷移裡最重、最需要小心的一步，下一節單獨展開。重點先記住：**絕不能一條 `UPDATE orders SET status = state` 掃全表**——那會在一筆巨大的交易裡鎖住幾億列、撐爆 WAL、把 MVCC 的舊版本回收（見〈MVCC〉）卡死。要分成幾萬列一批、一批一個小交易、批次之間留喘息。

**步驟 4：讀取切到新欄 `status`。**

backfill 完成、且步驟 2 的 dual-write 保證了「backfill 之後的所有新寫入也都進了 `status`」，此刻 `status` 欄對**每一列**都有正確的值了。現在部署一版程式，讀取改讀 `status`。寫入仍然 dual-write（還不能停，理由在步驟 5）。

**步驟 5：停止寫 `state`，只寫 `status`。**

等步驟 4 那版「讀 status」的程式**完全鋪滿**、確認沒有任何 pod 還在讀 `state` 之後，才部署這一版：寫入只寫 `status`，不再碰 `state`。為什麼要等 4 完全鋪滿才能做 5？因為只要還有**一個** pod 在讀 `state`，你就不能停止寫 `state`——否則那個 pod 會讀到一個從此不再更新的舊欄、拿到過期資料。dual-write 必須撐到「最後一個讀舊欄的讀者下線」為止。

**步驟 6 與 7（contract）：確認沒有任何程式碼引用 `state` 後，刪掉它。**

```sql
ALTER TABLE orders DROP COLUMN state;
```

`DROP COLUMN` 在 PostgreSQL 裡也只是改 catalog（它不立刻清掉每列的資料、只標記欄位已刪；普通 VACUUM 之後只把那塊死空間標記為可重用、讓新資料填回，並不會把檔案縮回 OS——要真正釋放磁碟得 `VACUUM FULL` 或一次 table rewrite），鎖很短。但它是**不可逆**的破壞性操作，所以放在最後，且要等到你百分之百確定沒有任何線上程式、沒有任何報表 SQL、沒有任何備份還原腳本還引用 `state`。穩健的做法甚至會在 `DROP` 之前先讓這個欄「靜置」一段時間——程式都不寫不讀了，但欄還留著，萬一發現漏網的引用，回滾只是「重新開始寫它」而不是「從備份救資料」。

數一下：一次「改個欄名」，從一行 SQL 變成了**七步、跨越四到五次部署**。這就是零停機的真實成本——你用大量的步驟和時間，換掉了那三十秒的全表凍結和那一窗口的部署報錯。值不值得，取決於那張表停三十秒會不會上新聞。

## 加一個欄，怎麼會是危險動作

步驟 1 我說「加可為 null、無預設值的欄」是廉價的，並且警告別加 `DEFAULT` 或 `NOT NULL`。這個細節值得停下來講透，因為它是「同一行 SQL 在不同條件下代價差幾個數量級」最經典的例子，也是很多人對 DDL 鎖的直覺出錯的地方。

先看 `DEFAULT`。在 **PostgreSQL 11 以前**，`ADD COLUMN ... DEFAULT 'x'` 會做一件可怕的事：它要把這個預設值**物理地寫進每一個既有資料列**，於是整張表被重寫一遍，`ACCESS EXCLUSIVE` 鎖持有到重寫完成——一張幾億列的表就是幾分鐘的全表凍結。PostgreSQL 11 改掉了這件事：它不再重寫，而是把這個「缺失的預設值」記在 catalog 裡（`pg_attribute` 的 `atthasmissing` 標記），讀取舊列時若發現該欄沒有實體值，就動態回填這個記下來的預設。於是加帶預設值的欄變成了一個**只改 metadata 的快動作**。

但這個優化有個尖銳的邊界：**它只對「非 volatile」的預設值成立**。`DEFAULT 'pending'`、`DEFAULT 0` 這種每列都一樣的常數，可以只記一份在 catalog 裡。但 `DEFAULT now()` 或 `DEFAULT gen_random_uuid()`——每一列該拿到**不同**的值——沒辦法只記一份，PostgreSQL 只能退回老路，逐列算、逐列寫，**整張表重寫**。所以同樣是「加一個帶預設值的欄」，`DEFAULT 0` 是毫秒級的安全動作，`DEFAULT now()` 是分鐘級的全表凍結。這兩者在 SQL 上長得幾乎一樣，代價卻差了好幾個數量級——這正是為什麼遷移不能只看語法、要看它在引擎裡實際做了什麼。

再看 `NOT NULL`。直接對一個既有欄下 `ALTER TABLE ... ADD COLUMN status text NOT NULL DEFAULT 'x'` 或事後 `ALTER COLUMN status SET NOT NULL`，PostgreSQL（17 以前）都要**全表掃描一遍**來證明「真的沒有任何一列是 null」，這個掃描在 `ACCESS EXCLUSIVE` 鎖下進行——又是全表凍結。

繞過它的招數很能體現 expand-contract 的精神：**把「立刻全表驗證」拆成「先掛一個不驗證存量的約束、再在弱鎖下慢慢驗證」**。

```sql
-- 1. 掛一個 CHECK，宣告 NOT VALID：只對未來的寫入生效，不掃存量，鎖只持有毫秒
ALTER TABLE orders ADD CONSTRAINT status_not_null CHECK (status IS NOT NULL) NOT VALID;

-- 2. 在 SHARE UPDATE EXCLUSIVE 弱鎖下驗證存量（這把鎖不擋讀寫，只擋並行 DDL）
ALTER TABLE orders VALIDATE CONSTRAINT status_not_null;

-- 3. PG 12+ 看到「已驗證的等價 CHECK」就跳過掃描，把欄轉成真正的 NOT NULL（不再掃表）
ALTER TABLE orders ALTER COLUMN status SET NOT NULL;

-- 4. 刪掉現在多餘的 CHECK
ALTER TABLE orders DROP CONSTRAINT status_not_null;
```

精妙之處在第 2 步的鎖。`NOT VALID` 約束從加上去那一刻起就**對所有新寫入生效**——任何新插入或更新的列若違反約束就被拒。正因為「未來不會再有違規的列進來」，驗證存量時就只需要檢查**既有的列**，不必擋住並行的讀寫，所以 `VALIDATE CONSTRAINT` 只拿 `SHARE UPDATE EXCLUSIVE`——這把鎖容許讀、容許寫，只擋其他 DDL。掃描還是要掃整張表（這免不了），但它在背景掃、不凍結業務流量。第 3 步靠的是 PostgreSQL 12 加入的優化：當引擎看到已有一個「已驗證、語意等價」的 CHECK 罩著這個欄，`SET NOT NULL` 就**省掉那次全表掃描**——因為要證明的事（沒有 null）已經被那個 CHECK 證過了。一個容易踩的順序坑：第 4 步的 `DROP CONSTRAINT` 必須在第 3 步**之後**——若先 drop 再 set，那個讓你省掃描的 CHECK 已經沒了，`SET NOT NULL` 又會退回去全表掃。

到了 **PostgreSQL 18**，這個來回更被官方收進一條原生語法：可以直接 `ADD CONSTRAINT ... NOT NULL column_name NOT VALID`，一步宣告「未來強制非空、但暫不驗證存量」，之後再 `VALIDATE` 補掉存量檢查。不論走 CHECK 繞道還是 PG 18 的原生寫法，骨架是同一個：**把一個原本要在強鎖下一次做完的危險驗證，拆成「立刻對未來生效的廉價宣告」加上「在弱鎖下慢慢補的存量驗證」。**

## backfill：把存量資料搬過去而不弄垮資料庫

expand 把新結構加好了，但對幾億列的存量資料，新欄還是空的。把它們填上，就是 backfill——遷移裡最耗時、也最容易出事的一步。出事的原因幾乎都是同一個：**有人寫了一條 `UPDATE orders SET status = state` 想一口氣搞定。**

這一條看似無害的 `UPDATE`，在一張三億列的表上會同時引爆好幾顆雷。第一，它是**一筆交易**，要鎖住它碰到的所有列——三億個行鎖，任何想改這些列的業務寫入全部排隊等它，等上幾十分鐘。第二，PostgreSQL 的 MVCC 是寫時產生新版本（見〈MVCC〉），這條 `UPDATE` 等於把三億列**每一列都複製一份新版本**，舊版本要等 VACUUM 回收——表瞬間膨脹到接近兩倍，WAL（見〈WAL：先寫日誌，再改資料〉）被這幾億列的變更撐爆，複製副本（見〈複製延遲與讀己之寫〉）被這一大坨 WAL 灌到延遲飆高。第三，這麼大的交易一旦中途失敗或被取消，整筆 rollback，你掃了二十分鐘等於白做。

正確的 backfill 是**分批、有節制、可中斷可續跑**的。它的形狀大概是：

```
loop:
  pick next batch of N rows where status IS NULL,
      bounded by primary key range (id > last_seen ORDER BY id LIMIT N)
  UPDATE those rows SET status = state         -- 一個小交易，只鎖 N 列
  COMMIT                                        -- 立刻放鎖、讓 VACUUM 能回收
  record last_seen = max(id) in this batch     -- 記住進度，中斷後可續
  sleep(throttle_ms)                            -- 給 DB 和副本喘息，看 lag 動態調
  until no rows with status IS NULL remain
```

幾個設計決定都不是隨意的，每一個都對應前面那條巨型 `UPDATE` 的一顆雷：

- **每批是獨立的小交易**。一批改個一千到幾萬列、立刻 commit，行鎖只持有這一小段、MVCC 舊版本能被及時回收、WAL 一小段一小段流出去。把「一筆三億列的交易」換成「三萬筆一萬列的交易」，峰值壓力被攤平了。
- **用主鍵範圍切批，不用 `OFFSET`**。`... ORDER BY id LIMIT 1000 OFFSET 5000000` 這種寫法每翻一頁都要從頭數過五百萬列，越往後越慢，是個 O(n²) 的陷阱（見〈分頁：offset 與 cursor/keyset、深分頁〉）。用 `WHERE id > last_seen ORDER BY id LIMIT N` 的 keyset 翻頁，每批都直接從索引定位，恆定快。
- **記錄進度，讓它可中斷續跑**。backfill 可能跑好幾個小時甚至跨天，中間 DB 要維護、要重啟、你要下班。把 `last_seen` 持久化下來，整個流程隨時可以停、可以從斷點接著跑，而不是「死了就從頭來」。
- **動態節流**。盯著副本延遲（replication lag）和 DB 負載：lag 一漲就把 `sleep` 拉長、把批次縮小；空閒時段再加速。backfill 是後台苦工，絕不能和業務流量搶資源搶到把線上拖垮。

把這些數字算到底，就能看出 backfill 為什麼是「以小時計」的後台工程，而不是一道指令。三億列、每批一萬列，就是三萬批；假設每批的 `UPDATE`＋`COMMIT` 約耗 20 ms、批次之間 `sleep` 50 ms 給副本喘息，那麼每批約 70 ms、三萬批 ≈ 2,100,000 ms ≈ **35 分鐘**——這還是副本一路跟得上的順風情況。一旦業務高峰把 replication lag 推高，節流邏輯就會把 `sleep` 從 50 ms 拉到幾百 ms、把批次從一萬縮到一兩千，每批的有效耗時翻幾倍、批數也跟著變多，總時長很容易從半小時膨脹到**好幾個鐘頭**。這正是為什麼進度要持久化、流程要可中斷續跑：它本來就會橫跨一個你不會盯著看的時間尺度。

這裡有個必須講透的正確性邊界——**backfill 和 dual-write 的競態**。設想 backfill 正在掃，掃到第 1000 列把它的 `status` 填好；就在這之後一瞬間，有一筆業務更新改了**第 500 列**的 `state`（那一列 backfill 已經掃過了）。如果這版程式還沒開始 dual-write，這筆更新就只改了 `state`、沒同步 `status`——於是第 500 列的 `status` 從此停留在 backfill 當時抄的舊值，悄悄地漂移、過時了。

這正是為什麼步驟順序**不能對調**：**dual-write（步驟 2）必須在 backfill（步驟 3）開始之前就全面生效**。先讓「所有新寫入都同時更新新欄」這個保證鋪滿，backfill 才只需要負責「鋪滿之前就已存在、之後不再變動的存量」。兩者像兩面夾擊地把整張表填滿：dual-write 罩住「從現在起發生變化的列」，backfill 罩住「過去就靜止在那裡的列」，交集處（backfill 掃過之後又被改的列）由 dual-write 兜住、不會漏。順序反過來，這個交集就成了一個會默默產生髒資料的洞——而且它不會報錯，你只會在某天對帳（見〈對帳：怎麼確認兩邊一致、漂移怎麼修〉）時發現一小撮對不上的列，再也查不出是哪一刻漏的。

## 不重寫整張表的索引：CREATE INDEX CONCURRENTLY

遷移不只加欄改約束，常常要加索引——而加索引是另一個「天真寫法會凍結全表」的經典坑。普通的 `CREATE INDEX` 要拿一把擋住所有**寫入**的鎖（`SHARE` 鎖，容許讀但擋寫），持有到整張表掃完、索引建好為止。對大表，這又是幾分鐘所有寫入排隊。

PostgreSQL 給的解法是 `CREATE INDEX CONCURRENTLY`，它建索引時只拿 `SHARE UPDATE EXCLUSIVE`——這把鎖容許讀也容許寫，代價是它做得更慢、更小心。它的內部機制值得看清楚，因為它示範了「怎麼在不停止寫入的情況下，對一個移動中的標的建立一致的快照」：

它**掃兩遍表**，分在不同交易裡做。第一遍：先在 catalog 裡放一個標記為「無效（`indisvalid = false`）」的索引條目，然後掃一遍表、把當下看到的所有列建進索引。但這一遍掃的過程中，表還在被寫入——掃描開始後新插入或更新的列，第一遍可能漏掉。於是有第二遍：再掃一次，把第一遍進行期間發生的所有變更補進索引。兩遍之間、以及第二遍開頭，它都得**等待**那些可能看到不一致狀態的舊交易結束，才能確定自己追上了。等第二遍確認索引和表完全一致，才把 catalog 裡那個條目翻成「有效」，索引正式可用。

這個「兩遍掃描 ＋ 中間等舊交易退場」的設計，買到的是「建索引期間不擋寫」，付出的代價有三：它**更慢**（要掃兩遍還要等）；它**不能在交易塊裡跑**（因為它自己就跨多個交易）；最關鍵的，它**可能留下半成品**——如果建到一半失敗（比如在建唯一索引時撞到重複值、或撞上死結），它會在 catalog 裡留下一個那個「無效」的索引條目。這個無效索引不會被查詢用到，卻會**繼續拖累每一筆寫入**（寫入仍要維護它），而且還佔著名字。所以 `CREATE INDEX CONCURRENTLY` 失敗後的標準動作是：先 `DROP INDEX`（最好也用 `CONCURRENTLY`）把那個無效索引清掉，再重試。遷移腳本若不檢查、不清理這個半成品，下一次重跑會撞名失敗，而那個無效索引就這麼一直拖著寫入效能，沒人發現。

## MySQL 的另一條路：online DDL 與影子表

到目前為止講的鎖細節大多是 PostgreSQL 的，但 schema 遷移的兩條引線——鎖與相容性——在 MySQL/InnoDB 上一樣存在，只是 MySQL 的應對機制長得不同，值得對照著看，因為它揭示了同一個問題的另一種解法形狀。

MySQL 8.0 起，InnoDB 對許多 `ALTER TABLE` 內建了 online DDL，用 `ALGORITHM` 子句標明這次變更的代價等級：

| ALGORITHM | 做了什麼 | 鎖與代價 |
|---|---|---|
| `INSTANT` | 只改 data dictionary 的 metadata | 不重建表、不長時間鎖，幾乎瞬間（8.0.12 起支援 ADD COLUMN、僅限加在最後一欄；8.0.29 起放寬到任意位置、並支援 INSTANT DROP COLUMN） |
| `INPLACE` | 在原表上就地重組（如多數加索引） | 不複製整張表，多半容許並行讀寫，但仍可能掃表 |
| `COPY` | 建一張新表、把資料全複製過去 | 最重：複製期間鎖住寫入，等同舊式的全表重建 |

MySQL 8.0.12 引入的 `INSTANT` ADD COLUMN，和 PostgreSQL 11 那個「把缺失預設記在 catalog」異曲同工——都是「不碰存量資料、只動 metadata」。但 `INSTANT` 有它自己的脾氣：每做一次 instant 的加/刪欄，InnoDB 就給這張表記一個新的「row version」，存量列維持舊版本格式、讀取時動態適配。這意味著反覆 instant 改欄會累積 row version，到上限後就得做一次真正的表重建才能繼續——便宜不是無限的。

那當一個 `ALTER` 落在 `COPY`、MySQL 內建 online DDL 罩不住時呢？MySQL 生態長出了兩個著名的外部工具，它們的共同思路是 **expand-contract 在工具層的自動化版本——建一張影子表（shadow / ghost table），把新 schema 套在影子表上，慢慢把資料從原表複製過去，期間用某種機制讓影子表跟上原表的即時變更，最後一個原子的改名把影子表換成正式表**：

- **pt-online-schema-change**（Percona）：在原表上裝**觸發器**。每筆對原表的 `INSERT/UPDATE/DELETE` 都被觸發器**同步**地複寫一份到影子表，同時背景把存量資料分批複製過去。觸發器的好處是即時、同步、強一致；代價是每一筆業務寫入都被觸發器加了重量，高寫入負載下這個 overhead 很可觀，且在最後改名切換時觸發器和 metadata lock 的協調是個敏感點。
- **gh-ost**（GitHub）：不用觸發器。它偽裝成一個複本，去**讀 binlog**（資料庫的變更日誌），從變更事件流裡得知原表的即時寫入，再把這些變更套到影子表上。好處是業務寫入的路徑上**零額外負擔**——同步工作被推到旁邊讀 binlog 的程序上；代價是影子表和原表之間是**最終一致**（落後 binlog 串流一小段），且這個方式對某些情境（外鍵、特定 binlog 設定）有限制。pt-osc 的 `--resume`（搭 `--history`／`--nodrop-*`）機制較成熟；gh-ost 傳統上程序死掉就得重來，較新版本以 `--checkpoint`／`--resume` 提供有條件的續跑（須首次就帶 `--checkpoint` 啟動、至少完成一次 checkpoint、binlog 座標與 checkpoint 表都還在）。這也是選型時的實際差異。

把這兩個工具放回本章的脊椎：它們做的事，**和我們手動走的七步 expand-contract 是同一件事**——加新結構（影子表）、過渡期同時維護新舊（觸發器或 binlog 追平）、最後原子切換、收掉舊的。差別只在於，這些工具把「同步新舊兩份資料」這件最易出錯的事自動化、封裝成一個指令。但封裝不等於免費：你還是得理解底下是觸發器同步還是 binlog 追平、是強一致還是最終一致、死了能不能續，才知道它在你的寫入負載下會不會出事。

## 不只是加欄：改型別與拆表，同一個形狀

改個欄名是最乾淨的範例，但 expand-contract 的形狀套到更難的變更上一樣成立，值得快速走兩個，確認這個方法不是只對玩具場景管用。

**改型別**——比如把 `user_id` 從 32 位的 `int` 改成 64 位的 `bigint`（很多系統遲早會撞上自增主鍵逼近 21 億上限這件事）。直接 `ALTER COLUMN ... TYPE bigint` 要重寫整張表（每列的該欄物理寬度都變了）＋全表凍結。expand-contract 的版本：加一個新欄 `user_id_big bigint`（expand）→ dual-write，新寫入兩個欄都填 → backfill 把存量的 `user_id` 複製進 `user_id_big` → 讀取切到新欄 → 停寫舊欄 → 最後把舊 `user_id` 刪掉、把新欄改名頂上。同一個七步骨架，只是「新結構」從一個語意欄變成一個換了型別的欄。

**拆表 / 搬欄**——把一張過胖的 `users` 表裡的 profile 相關欄位拆到獨立的 `user_profiles` 表。expand：建新表、dual-write（寫 `users` 時也寫 `user_profiles`）→ backfill 把存量的 profile 欄搬過去 → 讀取改從新表讀（過渡期可能要 join，或在應用層組裝）→ 停止寫舊表的那些欄 → contract 把舊欄刪掉。

兩個例子都顯示同一件事：**expand-contract 不是一招特定的 SQL 技巧，而是一個對付「破壞性結構變更」的通用變換**——只要一個變更會讓某一版程式立刻失效，就把它拆成「先加相容的新東西、過渡、再拿走舊東西」三段，讓任何單一時刻的 schema 都同時服侍得了新舊兩版程式。難的從來不是哪一步的 SQL，而是**過渡期那份「新舊兩份資料必須一致」的協調**——dual-write 的時序、backfill 的競態、切換的順序，這些才是真正吃掉工程精力、也真正決定會不會出事的地方。

## 為什麼是這個形狀

退一步看，零停機 schema 遷移的整套樣貌，都是從一個無法迴避的事實裡長出來的：**部署不是一個瞬間，而是一段新舊程式並存、讀寫從不停止的窗口；而資料庫在這段窗口裡，只能擺出一個 schema。**

正因為這個窗口存在，schema 在任何時刻都必須對兩版程式都成立——所以不能有破壞性的單步，所以要 expand-contract 的「先擴張、後收縮」。正因為存量資料不會自己跑進新結構，所以要 backfill；正因為 backfill 期間資料還在被改，所以要 dual-write 先鋪好、再 backfill，用兩面夾擊堵住中間的競態。正因為強鎖會凍結全表、rewrite 會放大這個凍結，所以要會分辨哪種 DDL 只動 metadata、哪種會掃全表，並用 `NOT VALID` ＋ 弱鎖驗證、`CONCURRENTLY` 建索引、分批 backfill 這些手法，把每一個本來要「一次在強鎖下做完」的危險動作，拆成「立刻對未來生效的廉價部分」加「在背景慢慢補的存量部分」。

這個「拆」字是貫穿全章的母題。一行 `RENAME` 之所以危險，是因為它把「加新的」和「拿走舊的」綁在同一個瞬間；一條全表 `UPDATE` 之所以危險，是因為它把幾億列的變更綁在同一筆交易；一個 `SET NOT NULL` 之所以危險，是因為它把「對未來強制」和「驗證存量」綁在同一把強鎖下。零停機遷移的全部技藝，就是反覆地把這些被綁在一起的瞬間**拆開、攤平、排好序**——讓系統永遠不必為了你而停下來。

下次你面對一個「只要改一行就好」的 migration，真正要問的不是那行 SQL 對不對，而是：**它有沒有偷偷把某個危險的同時性藏在那一行裡？** 如果有，你的工作就是把它拆成一連串各自無害的小步，每一步都讓此刻線上的每一版程式都活得好好的。

## 延伸閱讀

- Martin Fowler, "ParallelChange"（expand-contract 的概念原型）: https://martinfowler.com/bliki/ParallelChange.html
- Scott Ambler & Pramod Sadalage, *Refactoring Databases: Evolutionary Database Design*（資料庫重構與漸進式 schema 演化的奠基著作）: https://databaserefactoring.com/
- PostgreSQL 官方文件, ALTER TABLE（各動作的鎖等級、`NOT VALID` / `VALIDATE CONSTRAINT`、`SET NOT NULL`）: https://www.postgresql.org/docs/current/sql-altertable.html
- PostgreSQL 官方文件, CREATE INDEX（`CONCURRENTLY` 的兩遍掃描與失敗後的無效索引處理）: https://www.postgresql.org/docs/current/sql-createindex.html
- Brandur Leach, "A Missing Link in Postgres 11: Fast Column Creation with Defaults"（PG 11 為何能讓 `ADD COLUMN ... DEFAULT` 不重寫表，及 volatile 預設的例外）: https://brandur.org/postgres-default
- MySQL 8.0 Reference Manual, "Online DDL Operations"（`INSTANT` / `INPLACE` / `COPY` 各支援哪些操作與其鎖代價）: https://dev.mysql.com/doc/refman/8.0/en/innodb-online-ddl-operations.html
- gh-ost（GitHub 的 triggerless online schema migration，讀 binlog 追平的影子表機制）: https://github.com/github/gh-ost
- Percona Toolkit, pt-online-schema-change（觸發器式影子表同步）: https://docs.percona.com/percona-toolkit/pt-online-schema-change.html
