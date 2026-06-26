# B · 隔離與並發控制

本領域回答的問題只有一句：**多個交易同時碰同一份資料，你想要它們彼此隔離到什麼程度，又願意為此付多少並發代價。** 本檔含七個條目——從異常分類（隔離級別）、到實作隔離的兩大引擎（MVCC、鎖）、到兩種並發控制哲學（樂觀／悲觀）、再到兩個資料庫操作面的鄰題（索引與查詢計畫、多租戶隔離），最後以一條 PostgreSQL vs MySQL 工具對照收尾。邊界：一致性的「分散式／跨副本」面（線性化、CAP、複製延遲）在領域 B 的另一檔與領域 M；本檔只談**單一資料庫節點內**的交易隔離與並發。

---

## 隔離級別與異常（dirty / non-repeatable / phantom / write-skew）

### 定義與原理

隔離（isolation）是 ACID 的 I：交易並發執行時，每個交易應該「像是」獨佔資料庫。完全的隔離＝serializable（可序列化）＝結果等同於某個串列執行順序。但完全隔離很貴，所以 SQL 標準退而求其次，用「**容許哪些異常**」來定義較弱的級別。隔離級別不是用「鎖什麼」定義的，而是用**它禁止哪些讀寫交錯現象**定義的——這是理解它的第一原理。

四個經典異常，由弱到強排：

- **dirty read（髒讀）**：讀到另一個**尚未 commit** 交易寫的值；對方一旦 rollback，你讀到的是從未存在的資料。
- **non-repeatable read（不可重複讀）**：同一交易內讀同一**列**兩次，值不同（中間別人改了並 commit）。
- **phantom read（幻讀）**：同一交易內用同一**範圍查詢**（`WHERE age > 30`）兩次，回傳的**列集合**變了（別人插入／刪除了符合條件的列）。non-repeatable 是「列被改」，phantom 是「列集合變動」。
- **write skew（寫偏序）**：兩個交易各自讀一個重疊的資料集、各自據此寫**不同的列**，單獨看都合法，合起來破壞了一個跨列不變量。經典例子：兩個醫生各自看到「現在有兩人值班」，於是各自把自己設為休假——結果零人值班。write skew **不在** SQL 標準的四異常之列，是 snapshot isolation 留下的著名漏洞。

SQL 標準的四級別正是按「禁止哪些異常」定義：

| 級別 | dirty read | non-repeatable | phantom | write skew |
|---|---|---|---|---|
| Read Uncommitted | 可能 | 可能 | 可能 | 可能 |
| Read Committed | 禁止 | 可能 | 可能 | 可能 |
| Repeatable Read（標準語意） | 禁止 | 禁止 | 可能 | 可能 |
| Serializable | 禁止 | 禁止 | 禁止 | 禁止 |

注意：這是**標準**的語意。實際 DB 各有偏差——PostgreSQL 的 Repeatable Read 比標準強（連 phantom 都防），MySQL 的 Repeatable Read 在某些測試下比 snapshot isolation 還弱（見「PostgreSQL vs MySQL」）。

### 解法空間

要實作這些級別，引擎手上只有兩類武器，再加上兩個版本化策略：

- **悲觀鎖（pessimistic locking）**：讀前／寫前先上鎖，衝突的交易等待。Read Committed 用短命的讀鎖（讀完即放）；Serializable 的純鎖實作（2PL，two-phase locking）讀鎖持有到 commit。
- **MVCC（多版本並發控制）**：寫不覆蓋舊值，而是產生新版本；讀走「快照」看一致的舊版本，讀不擋寫、寫不擋讀（見「MVCC」）。Read Committed＝每條語句一個新快照；Repeatable Read／snapshot isolation＝整個交易一個快照。
- **next-key locking**：在索引上對「列＋列前的間隙」上鎖，專門用來在 Repeatable Read 級別擋 phantom（MySQL InnoDB 的做法）。
- **SSI（Serializable Snapshot Isolation）**：在 snapshot isolation 上加「讀寫依賴追蹤」，偵測到危險環就中止一個交易，用以達成真正的 serializable 又不必上讀鎖（PostgreSQL 的做法）。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Read Committed | 不讀到未 commit 的值 | 絕大多數 OLTP 預設 | 同交易內兩次讀可能不同；不保護任何跨語句不變量 |
| Snapshot Isolation（多數 DB 的 RR） | 整個交易看一致快照、防 non-repeatable／phantom | 報表、需要交易內穩定視圖 | **不防 write skew**；長交易撐快照會脹版本 |
| 2PL Serializable（純鎖） | 真 serializable | 強一致需求、寫衝突低 | 讀也上鎖，並發低、易死結 |
| SSI Serializable | 真 serializable、讀不上鎖 | 寫衝突中等、可接受重試 | 偵測到衝突會中止交易，**應用必須有 retry 邏輯** |

### 何時需要

判準是「**這條業務有沒有跨列／跨範圍的不變量，且兩個交易可能同時打它**」。

- 只是讀單列、寫單列、彼此不相關：Read Committed 夠了，升級隔離只是白付並發成本。
- 交易內要對同一份資料多次計算（先 `SELECT` 算總額、再 `UPDATE`）：至少 snapshot isolation，否則中途值會變。
- 有「總和不得超過上限」「至少留一人值班」這種**跨列不變量**：snapshot isolation 不夠（會 write skew），要 Serializable，或在應用層用顯式鎖（`SELECT ... FOR UPDATE` 把相關列鎖住）把它降級成單純的寫衝突。

worked example：一張帳戶表，規則「兩個共用帳戶的總餘額 ≥ 0」。A 餘額 100、B 餘額 100。交易 T1 讀到「A+B=200」、決定從 A 領 150（剩 A=-50，但 A+B=50≥0，合法）；T2 同時讀到「A+B=200」、從 B 領 150（B=-50，A+B=50，也合法）。在 snapshot isolation 下兩者各自的快照都看到 200、都通過檢查、都 commit——最終 A=-50、B=-50、總和 -100，不變量被打破。這是 write skew 的標準現場：**沒有任何一列被兩個交易同時寫，所以版本檢查抓不到**。Serializable（SSI）會偵測到兩交易讀寫集的危險交叉、中止其中一個。

### 常見誤解與陷阱

- **「Repeatable Read 就是 SQL 標準那個」**——錯。標準的 RR 容許 phantom，但 PostgreSQL 的 RR 連 phantom 都不會出現（因為它其實是 snapshot isolation）。級別名稱是個壞契約：同名在不同 DB 行為不同。
- **「升到最高隔離就一勞永逸」**——Serializable 不是免費的隔離開關，它把問題從「資料錯」換成「交易被中止、要 retry」。沒寫 retry 迴圈，使用者就看到隨機報錯。
- **「write skew 很罕見」**——任何「先查一個聚合條件、再據此寫入」的邏輯都有風險：庫存扣減、預約衝突、唯一性檢查（先 `SELECT` 查不存在、再 `INSERT`）全是。
- **把隔離級別當效能旋鈕亂調**——調低級別省並發成本，但你買進來的是上面那些異常；該標清楚「降到 Read Committed，代價是放棄交易內可重複讀」。

### 延伸閱讀

- PostgreSQL 官方文件，Transaction Isolation：https://www.postgresql.org/docs/current/transaction-iso.html
- Berenson 等人，"A Critique of ANSI SQL Isolation Levels"（1995，指出標準異常定義的歧義）：https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/
- Jepsen，PostgreSQL 12.3 分析（隔離異常的實測）：https://jepsen.io/analyses/postgresql-12.3

---

## MVCC

### 定義與原理

MVCC（Multi-Version Concurrency Control，多版本並發控制）的核心想法一句話：**寫不就地覆蓋，而是寫一個新版本；讀去找「對我可見」的那個版本。** 這樣讀者和寫者不必互相等待——讀走快照看舊版本，寫產生新版本，兩條路徑解耦。它是現代 OLTP 資料庫（PostgreSQL、MySQL InnoDB、Oracle、SQL Server 的 RCSI）實作隔離的主力引擎。

每個版本帶兩個關鍵元資料：**創建它的交易 ID（xmin）** 與**刪除／取代它的交易 ID（xmax）**。讀的時候，引擎拿你的快照（一組「哪些交易在我開始時已 commit」的資訊）去判斷每個版本可見不可見：版本的 xmin 必須是「我看得到的已 commit 交易」，且 xmax 必須是「我看不到的或未發生的」。可見性判斷把「隔離級別」具體化為「快照取得的時機」：Read Committed＝每條語句重取快照、Repeatable Read＝交易開始取一次。

### 解法空間

MVCC 不是單一做法，舊版本放哪、怎麼清，有兩條主要路線：

- **就地存新版本＋表內留舊版本（append-in-heap）**：PostgreSQL。`UPDATE` 寫一條新 tuple，舊 tuple 標記過期但留在 heap 裡，靠背景的 **VACUUM** 回收。優點是 commit／rollback 便宜（不用搬資料），缺點是膨脹（bloat）與 VACUUM 壓力。
- **undo log 還原舊版本（rollback segment）**：MySQL InnoDB、Oracle。最新版本就地寫在資料頁，舊版本靠 **undo log** 反推回去。讀舊版本要沿 undo 鏈回溯，優點是主表不膨脹，缺點是長交易讓 undo 鏈變長、purge 跟不上時讀很慢（"history list length" 暴增）。
- **可見性判斷**：靠快照／交易 ID 比對（上面說的 xmin/xmax 或 read view）。
- **舊版本回收**：背景程序（VACUUM／purge），不是即時的——這是 MVCC 所有麻煩的根源。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| heap 內多版本 + VACUUM（PostgreSQL） | 讀不擋寫、commit/rollback 便宜 | 寫密集、rollback 常見 | 表膨脹；長交易卡住 VACUUM → bloat 與 XID wraparound 風險 |
| undo log + purge（InnoDB/Oracle） | 主表緊湊、最新版本就地讀快 | 讀最新版本為主 | 讀舊版本要沿 undo 回溯變慢；長交易撐住 undo → history list 暴增 |
| 純鎖（無 MVCC，2PL） | 不需版本與回收 | 教科書／極簡引擎 | 讀寫互擋，並發差——現代 OLTP 幾乎不用 |

### 何時需要

MVCC 不是你「選用」的，而是你用的資料庫已經替你選了。你真正要做的判斷是**怎麼配合它別把它搞爆**：

- 讀寫並發高、且讀多：MVCC 是天賜——讀者完全不擋寫者。
- 有長時間執行的交易（大報表、ETL、忘了 commit 的連線）：這是 MVCC 的頭號殺手。一個跑了一小時的交易，會讓引擎**不敢回收**這一小時內所有被更新列的舊版本（因為這個老交易可能還要看），全庫膨脹。

worked example：一張 100 萬列、每列 200 bytes 的表（約 200 MB）。某連線開了交易忘了 commit，一直掛著。期間應用對全表做了一輪 `UPDATE`（每列改一次）。在 PostgreSQL 下，舊版本因為那個老交易還在而無法被 VACUUM 回收——表從 200 MB 膨脹到約 400 MB，且這個膨脹直到老交易結束才會被回收。在 InnoDB 下對應的是 undo history list length 持續上升，purge 執行緒追不上。教訓很實際：**最便宜的 MVCC 調校是「別讓交易開著不關」**。

### 常見誤解與陷阱

- **「MVCC＝沒有鎖」**——只對「讀」成立。寫同一列仍然要排隊：第二個 `UPDATE` 會等第一個 commit／rollback（行鎖，見「鎖與死結」）。MVCC 消除的是**讀寫互擋**，不是寫寫互擋。
- **「`SELECT` 不影響任何東西」**——一個只讀的長交易，照樣會撐住快照、阻止舊版本回收。唯讀不等於無害。
- **把 bloat 當「需要更大硬碟」**——通常是長交易或 VACUUM 跟不上，加硬碟只是延後爆炸。要查 `pg_stat_activity` 最老的交易、InnoDB 的 history list length。
- **以為 rollback 很貴**——在 append 式 MVCC（PostgreSQL）裡 rollback 反而便宜（不用撤銷，直接把這些版本標廢）；貴的是 undo 式引擎的大交易 rollback（要逐筆反推）。引擎不同，直覺要反過來。

### 延伸閱讀

- PostgreSQL 官方文件，Concurrency Control / MVCC：https://www.postgresql.org/docs/current/mvcc.html
- PostgreSQL 官方文件，Routine Vacuuming（含 XID wraparound）：https://www.postgresql.org/docs/current/routine-vacuuming.html
- MySQL 官方文件，InnoDB Multi-Versioning：https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html

---

## 鎖與死結（行鎖/gap/next-key、wait-for graph）

### 定義與原理

當 MVCC 不夠（寫寫衝突、要擋 phantom、要顯式序列化），引擎落回**鎖**。鎖是並發控制最直接的武器：在資源上掛一個標記，要動它的交易得先拿到相容的鎖，拿不到就等。鎖的麻煩不在「擋住」本身，而在**互相等成環**——A 等 B 手上的鎖、B 又等 A 手上的鎖，誰也不放，這就是死結（deadlock）。

引擎用 **wait-for graph（等待圖）** 形式化死結：節點是交易，「T1 等 T2」就畫一條 T1→T2 的邊。**圖裡出現環＝死結。** 偵測器週期性找環，找到就選一個「受害者」中止（通常選回滾代價小的），讓其餘的繼續。

```
  wait-for graph（死結＝有環）

      lock A           lock B
   ┌─────────┐      ┌─────────┐
   │   T1    │ ───▶ │   T2    │   T1 想要 B（T2 持有）
   │ holds A │      │ holds B │
   └─────────┘ ◀─── └─────────┘   T2 想要 A（T1 持有）
        環 T1 → T2 → T1：偵測器中止其一
```

鎖的**粒度**從粗到細：表鎖 → 頁鎖 → 行鎖（row lock）。OLTP 主要靠行鎖。InnoDB 還有兩種特別的鎖用來擋 phantom：

- **record lock（記錄鎖）**：鎖住一筆索引記錄本身。
- **gap lock（間隙鎖）**：鎖住兩筆索引記錄**之間的空隙**，purely inhibitive——它不擋讀、只擋「往這個間隙插入新列」，這正是擋 phantom 的手段。
- **next-key lock**：record lock ＋ 它前面那段 gap lock 的組合。InnoDB 在 Repeatable Read 下對範圍掃描預設用 next-key lock，於是「範圍內的列＋範圍內的所有間隙」都被鎖住，別人插不進來 → 沒有 phantom。

### 解法空間

對付死結，有四條路，本質是「預防 vs 偵測」之分：

- **偵測後中止（detection）**：放任死結發生，靠 wait-for graph 找環、犧牲一個交易（PostgreSQL、InnoDB 的預設）。
- **逾時放棄（timeout）**：不畫圖，等鎖超過 `innodb_lock_wait_timeout`／`lock_timeout` 就放棄。簡單但會誤殺（慢交易被當死結）也會漏判（真死結等滿逾時才解）。
- **固定加鎖順序（ordering）**：應用層約定「永遠先鎖 id 小的列」，從根本消除環。最有效的預防，但要全應用配合。
- **降低鎖需求**：縮短交易、用樂觀並發控制（見下一條）、把多列操作拆小，從源頭減少持鎖時間與範圍。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| wait-for graph 偵測 | 保證死結被解、選代價小的犧牲 | DB 引擎內建（PG/InnoDB） | 偵測有延遲（PG 預設等 `deadlock_timeout`=1s 才查）；應用仍須能 retry 受害者 |
| 鎖逾時 | 實作簡單、無圖計算 | 簡單系統、分散式鎖 | 誤殺慢交易＋真死結反應慢，逾時值難調 |
| 固定加鎖順序 | 根除死結（無環可成） | 多資源批次更新 | 要全應用紀律；動態決定鎖哪些列時難套用 |
| 縮短交易/樂觀控制 | 減少持鎖時間與衝突面 | 衝突率低的高並發 | 衝突率高時樂觀控制的重試成本反而更高（見「樂觀 vs 悲觀」） |

### 何時需要

- 寫同一列的併發本來就由行鎖串起來、不用你管——你要管的是**別讓持鎖交易拖太久**（中間穿插網路呼叫、等使用者輸入都是大忌）。
- 多筆列要在一個交易裡一起更新（轉帳：扣 A 加 B）：這是死結高發區，套**固定加鎖順序**（永遠按主鍵排序加鎖）。
- 範圍更新／範圍刪除在 Repeatable Read 下會吃 gap/next-key lock，鎖的範圍比你以為的大很多——這是 InnoDB 的隱藏死結來源（見陷阱）。

worked example：轉帳服務，兩筆交易同時做相反方向轉帳。T1：`UPDATE acct SET bal=bal-100 WHERE id=1`（鎖住列 1），再 `... WHERE id=2`。T2：先 `... WHERE id=2`（鎖住列 2），再 `... WHERE id=1`。現在 T1 持列 1 等列 2、T2 持列 2 等列 1——wait-for graph 成環，引擎中止其一。修法：兩個交易都**先鎖 id 較小者**（`ORDER BY id` 或顯式 `SELECT ... FOR UPDATE` 按序），環就無法形成。一行排序約定換掉一整類死結。

### 常見誤解與陷阱

- **「死結是 bug，正確的程式不該有」**——死結是高並發下的正常現象，不是邏輯錯誤。正解是**讓受害交易能安全 retry**（這要求操作冪等或交易性，見「冪等」，領域 A），不是假裝它不會發生。
- **「我只更新一列，不會死結」**——會。如果該 `UPDATE` 走了次級索引，InnoDB 可能在主鍵與索引上各加鎖、與另一交易反序相遇成環。也別忘了**外鍵檢查會默默對父表加鎖**。
- **gap lock 的範圍被低估**——`DELETE FROM t WHERE status='pending'` 在 RR 下可能鎖住一大段索引間隙，擋住別人對該範圍的插入，把不相干的併發插入串成死結。`WHERE` 條件命不中索引時更糟（退化成更粗的鎖）。
- **把 `deadlock_timeout` 當死結逾時**——PostgreSQL 的 `deadlock_timeout`（預設 1s）是「等多久才**開始查**有沒有死結」，不是「等多久放棄鎖」。它調的是偵測延遲，不是放棄門檻（2026-06）。

### 延伸閱讀

- MySQL 官方文件，InnoDB Locking（record/gap/next-key）：https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html
- MySQL 官方文件，Deadlocks in InnoDB：https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html
- PostgreSQL 官方文件，Explicit Locking：https://www.postgresql.org/docs/current/explicit-locking.html

---

## 樂觀 vs 悲觀並發控制（CAS、version/ETag、conditional request）

### 定義與原理

並發控制有兩種哲學，差別在「**衝突發生前先防，還是發生後再驗**」。

- **悲觀（pessimistic）**：假設衝突常發生。動資料前先上鎖（`SELECT ... FOR UPDATE`），別人得等。衝突在「進場前」就被擋住，代價是持鎖期間的等待與死結風險。
- **樂觀（optimistic, OCC）**：假設衝突罕見。讀的時候不上鎖，只記住「我讀到的版本」；寫的時候用一個**原子的條件更新**——「只有當版本還是我讀到的那個時才寫」。版本變了表示有人插隊，這次寫就失敗，由呼叫端決定重試還是放棄。

樂觀控制的技術核心是一個**比較並交換**的原子操作：

- **CAS（compare-and-swap）**：硬體／引擎層的「值還等於 expected 才換成 new」原子指令，是所有樂觀控制的底座。
- **version 欄位 / row version**：表上加一個 `version`（或 `updated_at`、`xmin`）欄，更新時 `UPDATE ... SET v=v+1 WHERE id=? AND v=?`；affected rows = 0 即衝突。
- **ETag + conditional request**：把上述模式搬到 HTTP。伺服器回應帶 `ETag`（資源版本指紋），客戶端寫回時帶 `If-Match: <etag>`；版本不符伺服器回 **412 Precondition Failed**，這是 RFC 9110 定義的標準樂觀並發控制（2026-06）。

樂觀控制與**冪等**是兩件事，常被混淆：冪等保證「同一操作重放不重複生效」（見「冪等」，領域 A）；樂觀控制保證「過期的寫不會覆蓋新值（lost update）」。重試一個失敗的樂觀寫時，你會用到冪等來確保重試本身安全，但樂觀控制本身解的是 lost update，不是去重。

### 解法空間

- **悲觀行鎖**：`SELECT ... FOR UPDATE` / `FOR SHARE`，引擎層串行化。
- **version 欄位 OCC**：應用層維護版本欄，條件更新。
- **DB 原生時間戳 / 系統欄位**：用 `xmin`（PG）或 `ROWVERSION`（SQL Server）當版本，免自己維護欄位。
- **HTTP 條件請求**：`If-Match` / `If-Unmodified-Since` + ETag，把並發控制推到 API 邊界。
- **CAS 在分散式 KV**：Redis `WATCH`/`MULTI`（或 Lua）、DynamoDB conditional write、etcd compare-and-swap——同一套樂觀模式的分散式版本。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 悲觀 `SELECT ... FOR UPDATE` | 進場即互斥、無 lost update | 高衝突、重試成本高（複雜長交易） | 持鎖期間阻塞、死結風險、不能跨請求持鎖 |
| version 欄位 OCC | 無 lost update、讀期間零鎖 | 低衝突、讀多寫少 | 高衝突時重試風暴；要處理 affected rows=0 的分支 |
| ETag + `If-Match`（HTTP） | 跨無狀態請求防 lost update | REST API、跨網路的編輯 | 客戶端必須回傳並尊重 ETag；弱比較 vs 強比較語意要對齊 |
| 分散式 CAS（Redis/DynamoDB） | 單鍵原子條件寫 | 跨節點計數、狀態機轉移 | 只保單鍵原子；跨多鍵要交易或別的協調 |

### 何時需要

決策只看一個數字：**衝突率（同一筆資料被併發寫的機率）**。

- **低衝突**（多數使用者編輯自己的資料、很少撞上同一列）：樂觀。讀期間零鎖、零等待，偶爾撞上就重試一次，整體吞吐最高。
- **高衝突**（熱點列：秒殺庫存、全域計數器、被多人搶改的同一份文件）：樂觀會陷入重試風暴（讀-改-寫-失敗-重來，反覆消耗），此時悲觀鎖反而便宜——排隊雖慢但不空轉。
- **跨請求 / 無狀態邊界**（你不可能在 HTTP 請求 A 持鎖等請求 B）：只能樂觀，用 ETag。

worked example：一個庫存欄位 `stock=10`，預期一天賣幾筆、衝突低。用 version OCC：客戶讀到 `stock=10, version=7`，下單時送 `UPDATE items SET stock=stock-1, version=8 WHERE id=? AND version=7`。若這期間沒人改，affected rows=1，成功。若另一筆併發訂單先把 version 推到 8，本次 `WHERE version=7` 命中 0 列，affected rows=0 → 應用收到「版本過期」、重讀、重試。對照同一場景如果是秒殺（5000 人搶 10 件）：樂觀控制下 4990 次都會撞 version 失敗、瘋狂重試，CPU 燒在空轉上——這時改悲觀 `FOR UPDATE` 排隊，或乾脆用 Redis 原子 `DECR` 把搶量擋在 DB 之外，才是對的。同一個欄位，衝突率不同，答案相反。

### 常見誤解與陷阱

- **「樂觀控制比較快」**——只在低衝突時。它把「等待」換成「重試」，高衝突下重試成本可以遠超過鎖等待。沒有絕對更快，只有「對的衝突率配對的策略」。
- **忘了檢查 affected rows**——version OCC 的全部安全性都在「`UPDATE` 影響 0 列＝衝突」這個分支上。很多 bug 是 `UPDATE` 默默改了 0 列、程式卻當成功繼續，lost update 照樣發生。
- **ETag 客戶端不回傳**——伺服器發了 ETag，客戶端寫回時不帶 `If-Match`，等於沒做樂觀控制。要嘛伺服器對缺 `If-Match` 的寫一律拒絕（要求 `If-Match: *` 或具體值），要嘛明確接受「無條件覆蓋」的語意——別含糊。
- **拿樂觀控制當去重**——它防的是 lost update，不是重複處理。同一筆冪等鍵被重送兩次的去重，是另一回事（見「冪等」，領域 A）。
- **跨多列的不變量靠單欄 CAS 守不住**——version 欄只保護「這一列」的原子更新；跨列的不變量（write skew 那類）要靠交易隔離或顯式鎖，CAS 救不了。

### 延伸閱讀

- RFC 9110，HTTP Semantics（§13 Conditional Requests、ETag/If-Match/412）：https://www.rfc-editor.org/rfc/rfc9110.html
- MDN，If-Match header：https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match
- AWS 文件，DynamoDB Condition Expressions（conditional write）：https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html

---

## 索引與查詢計畫（B-tree、覆蓋/複合索引、查詢計畫）

### 定義與原理

索引是一份**額外維護的、排好序的資料結構**，讓引擎不必掃全表就能定位列。它換的是空間與寫入成本（每筆寫要同步更新索引），買的是讀的速度。它和並發放在同一領域，是因為**索引決定鎖的範圍**：InnoDB 的 gap/next-key lock 鎖在索引上，查詢命不命中索引，直接決定它鎖多大一片、會不會和別人死結（見「鎖與死結」）。

主力結構是 **B-tree**（嚴格說多是 B+tree）：一棵平衡的、排序的多叉樹，葉節點存索引鍵與指向列的指標。它的關鍵性質是樹高極矮——分支因子大，幾百萬列也只需 3–4 層，所以一次查詢只讀少數幾個頁。B-tree 同時支援等值查找、範圍查找、前綴查找、與有序輸出（`ORDER BY` 可免排序），這是它當預設索引的原因。

**查詢計畫（query plan）** 是引擎的查詢優化器產出的執行方案：要不要用索引、用哪個、是 index scan 還是 seq scan、怎麼 join。它基於**統計資訊**（表有多少列、欄位值的分佈）估算各方案成本、選最便宜的。`EXPLAIN` 看計畫，`EXPLAIN ANALYZE` 實際跑一遍給真實時間與列數。

### 解法空間

不是「加索引」一個動作，而是一組選擇：

- **單欄 B-tree**：最基本，對單一過濾欄。
- **複合索引（composite / multi-column）**：對 `(a, b, c)` 排序，遵守**最左前綴規則**——能服務 `WHERE a`、`WHERE a AND b`、`WHERE a AND b AND c`，但**不能**只靠 `WHERE b` 或 `WHERE c`。欄位順序就是設計（等值欄放前、範圍欄放後）。
- **覆蓋索引（covering index）**：查詢需要的欄全在索引裡，引擎直接從索引取值、**不回表**（index-only scan）。PostgreSQL 用 `INCLUDE` 把非鍵欄掛進索引而不影響排序。
- **部分索引（partial index）**：只索引符合條件的列（`WHERE status='active'`），省空間、提命中。
- **其他結構**：hash（純等值）、GIN/GiST（全文、陣列、地理，機制見領域 O 的 inverted index）、BRIN（巨大且物理有序的表）。
- **skip scan**：PostgreSQL 18 起，複合索引在只約束後段欄位（前段欄位基數低）時也能用上索引，部分鬆綁最左前綴的限制（2026-06）。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 單欄 B-tree | 等值/範圍/排序皆快 | 通用過濾與排序 | 每個寫操作要維護它；高基數欄才划算 |
| 複合索引 `(a,b,c)` | 服務含最左前綴的查詢、可一索引頂多查詢 | 多條件常一起出現 | 受最左前綴限制；欄序錯了等於沒用對 |
| 覆蓋索引（INCLUDE） | 免回表，I/O 大降 | 熱查詢的固定欄位集 | 索引變大、寫更貴；查詢欄一變就失效 |
| 部分索引 | 體積小、命中高 | 查詢恆帶固定條件（如只查 active） | 條件外的查詢用不到它 |

### 何時需要

- 查詢用某欄過濾且該欄**選擇性高**（不同值多、每個值對應的列少）：值得加 B-tree。低選擇性欄（如布林 `is_deleted`，半數列都符合）加了優化器也常不用，因為走索引再回表比掃全表還貴。
- 一組欄位**總是一起**出現在 `WHERE`：用複合索引，按「等值欄在前、範圍欄在後、最常用的在最左」排。
- 某條熱查詢只取少數幾欄、跑超頻繁：上覆蓋索引換掉回表 I/O。
- 別的方向：**寫密集、讀少**的表，索引是負擔不是資產——每筆 `INSERT` 都要改全部索引。

worked example：一張 1000 萬列的訂單表，查 `WHERE user_id=? AND status='paid' ORDER BY created_at DESC LIMIT 20`。無索引：seq scan 掃 1000 萬列、排序、取 20，每次查讀數十萬個頁。建複合索引 `(user_id, status, created_at DESC)`：優化器用 user_id+status 定位、created_at 已排好序，直接從索引頭取 20 列就停——讀的頁數從數十萬降到 B-tree 樹高（約 4 頁）＋20 列所在的少數葉頁，三到四個數量級的差距。若再把 `LIMIT 20` 要顯示的欄（如 `amount`）用 `INCLUDE` 掛進去做成覆蓋索引，連回表那 20 次隨機 I/O 都省掉。用 `EXPLAIN ANALYZE` 應看到 `Index Scan`／`Index Only Scan` 取代 `Seq Scan`，且 `Rows Removed by Filter` 接近 0。

### 常見誤解與陷阱

- **「欄上有索引，查詢就會用」**——不一定。函數包住欄（`WHERE lower(email)=?` 對 `email` 索引）、隱式型別轉換（字串欄用數字比）、`LIKE '%x'` 前綴萬用、低選擇性條件，都會讓優化器放棄索引。看 `EXPLAIN` 才算數，別憑「我建了」就以為命中。
- **複合索引欄序搞反**——`(status, user_id)` 服務不了「只給 user_id」的查詢，因為 user_id 不是最左前綴。索引設計的一半是**欄序設計**。
- **索引越多越好**——每個索引都加重寫成本、吃空間、誤導優化器。沒被任何查詢用到的索引是純負債，要定期用 `pg_stat_user_indexes` 之類找出零命中的砍掉。
- **覆蓋索引的「免回表」有前提**——PostgreSQL 的 index-only scan 還要 visibility map 是新的（VACUUM 跟得上），否則仍得回 heap 查可見性，「免回表」打折。MVCC 的回收節奏（見「MVCC」）會回頭影響索引效益。
- **把查詢計畫當穩定的**——它依賴統計資訊。資料分佈大變而沒重算統計（`ANALYZE`），優化器會用過時估計選錯計畫；同一條 SQL 昨天走索引今天走全掃，常是統計過期或參數嗅探（parameter sniffing）作怪。

### 延伸閱讀

- PostgreSQL 官方文件，B-Tree Indexes：https://www.postgresql.org/docs/current/btree.html
- PostgreSQL 官方文件，Using EXPLAIN：https://www.postgresql.org/docs/current/using-explain.html
- Use The Index, Luke!（B-tree 索引與查詢調校的權威入門）：https://use-the-index-luke.com/

---

## 多租戶隔離（row / schema / db-per-tenant）

### 定義與原理

多租戶（multi-tenancy）＝同一套系統服務多個彼此獨立的客戶（tenant），共用程式碼與基礎設施。核心問題：**租戶 A 的資料絕不能被租戶 B 看到或改到，而你又想盡量共用資源省成本。** 這條問句的脊椎是「**隔離強度 vs 資源效率**」——越強的隔離越貴、越好遷移／合規，越共享越省、但爆炸半徑越大。

三種主要模型（業界也叫 pool / bridge / silo）：

- **row-level（共池 pool）**：所有租戶資料同表，靠一個 `tenant_id` 欄區分，每個查詢都要帶 `WHERE tenant_id=?`。最省，隔離最弱——少一個 `WHERE` 就漏資料。
- **schema-per-tenant（橋接 bridge）**：同一個資料庫實例，每個租戶一個 schema（一組同名表）。邏輯隔離、可做租戶級客製。
- **db-per-tenant（穀倉 silo）**：每個租戶一個獨立資料庫（甚至獨立實例）。隔離最強、最好遷移與合規，最貴最難管。

### 解法空間

- **row-level + 應用層過濾**：每條 query 注入 `tenant_id`。最脆，全靠紀律。
- **row-level + 資料庫強制（RLS）**：PostgreSQL Row-Level Security——在 DB 層綁 policy（`USING (tenant_id = current_setting('app.tenant'))`），即使應用忘了帶條件，引擎也擋住。把「別漏 WHERE」從人腦移到引擎。
- **schema-per-tenant**：連線時 `SET search_path`（PG）或 `USE db`（MySQL）切到租戶 schema。migration 要對每個 schema 各跑一次。
- **db-per-tenant**：路由層（連線字串／服務發現）把請求導到對的庫。
- **混合（hybrid）**：小租戶共池、大客戶獨庫——常見的成熟做法，按租戶大小分層。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| row-level（共 `tenant_id`） | 資源利用率最高、onboarding 最快 | 海量小租戶、SaaS 早期 | 隔離最弱；漏一個 `WHERE` 即跨租戶洩漏；noisy neighbor；難按租戶刪資料/合規 |
| row-level + RLS | 引擎層強制過濾、補上「漏 WHERE」 | 同上但要更硬的隔離 | policy 設計與 `current_setting` 注入要對；繞過 RLS 的角色（owner/superuser）是後門 |
| schema-per-tenant | 邏輯隔離、可租戶客製、好按租戶備份 | 中量級租戶、需差異化 | migration ×N 個 schema；上千 schema 撐爆系統目錄、效能掉 |
| db-per-tenant | 隔離最強、爆炸半徑＝單租戶、易遷移/合規/獨立調校 | 大客戶、強監管、資料落地要求 | 成本最高、連線數膨脹、營運與監控 ×N 個庫 |

### 何時需要

按「租戶數量 × 隔離要求 × 客戶大小」三軸選：

- 租戶**多而小**、隔離要求一般（典型 B2C-ish SaaS）：row-level，最好加 RLS 兜底。
- 租戶**中量**、需要租戶級客製或獨立備份：schema-per-tenant。
- 客戶**少而大**、強合規（金融／醫療）、資料主權／落地要求、要能獨立調效能：db-per-tenant。
- 多半最後是**混合**：絕大多數小租戶共池，少數付費大客戶獨庫——別讓一個模型硬撐所有規模。

worked example：一個 SaaS 有 5000 個小租戶＋20 個大企業客戶。全用 db-per-tenant＝5020 個資料庫，連線池、migration、監控全部 ×5020，營運成本爆炸且小租戶閒置浪費。全用 row-level＝大客戶的查詢和小租戶擠同一批表，一個大客戶的全表掃描拖慢所有人（noisy neighbor），且大客戶常要求「我的資料要能單獨匯出／刪除／落在指定區域」，共池下做這些要在十億列裡按 `tenant_id` 篩，痛苦。務實解：5000 小租戶共池（row-level + RLS），20 大客戶各自 db-per-tenant。一次 migration 要跑 1 次（共池）＋20 次（獨庫），而不是 5020 次。同一個產品，按租戶大小分層放，才同時拿到效率與隔離。

### 常見誤解與陷阱

- **「加了 `tenant_id` 欄就安全」**——row-level 的全部安全性掛在「每條 query 都正確帶 `WHERE tenant_id=?`」上。一個 ORM 的 lazy load、一條手寫報表 SQL、一個忘了過濾的 join，就跨租戶洩漏。要嘛上 RLS 讓引擎兜底，要嘛在 data access 層強制注入、禁止裸 query。
- **schema-per-tenant 在「幾千租戶」時撞牆**——每個 schema 的表都進系統目錄（catalog），上千租戶＝幾萬張表，`pg_class` 膨脹、規劃器變慢、`pg_dump` 變慢、連線啟動變慢。它適合「幾十到幾百個租戶」，不適合「無上限增長」。
- **db-per-tenant 的連線數陷阱**——每個庫各自要連線池，1000 個庫 × 每庫 10 連線＝1 萬連線，遠超單一 PG 實例的 `max_connections`（預設百級）。要靠 pooler（PgBouncer）和多實例分散，不是「再開一個庫」這麼便宜。
- **把多租戶當「之後再說」的事**——`tenant_id` 沒從第一天進每張表、每個索引（複合索引要 `tenant_id` 當最左欄，否則查詢掃全租戶），事後補是大手術。多租戶模型是**地基決策**，難可逆（見領域 U 的可逆 vs 不可逆決策）。

### 延伸閱讀

- AWS 文件，SaaS Tenant Isolation Strategies（pool/silo/bridge 與隔離模型）：https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html
- PostgreSQL 官方文件，Row Security Policies（RLS）：https://www.postgresql.org/docs/current/ddl-rowsecurity.html
- AWS Database Blog，Multi-tenant data isolation with PostgreSQL Row Level Security：https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/

---

## PostgreSQL vs MySQL（隔離預設、SSI vs next-key 的本質差）

### 是什麼與內部機制

PostgreSQL 與 MySQL（InnoDB 引擎）是兩大開源關聯式資料庫。兩者都用 MVCC 做並發，但**實作隔離的內部機制走了相反的路線**，這在「Repeatable Read 到底保證什麼」「怎麼擋 phantom」「怎麼達成真 serializable」三件事上分得最開（截至 2026-06，PostgreSQL 18、MySQL 8.4 LTS 為當前主線）。

- **PostgreSQL**：純 MVCC 路線。舊版本存在 heap、靠 VACUUM 回收。隔離預設 **Read Committed**。它的 **Repeatable Read 實際上是 snapshot isolation**——交易看一致快照，連 phantom 都不會出現（比 SQL 標準的 RR 強），但**不防 write skew**。要防 write skew 得升到 **Serializable**，PostgreSQL 用 **SSI（Serializable Snapshot Isolation）**：不靠讀鎖，而是用 predicate locking 追蹤交易間的讀寫依賴，偵測到「危險結構」（會導致不可序列化的讀寫環）時，中止其中一個交易並回報 `could not serialize access`，由應用 retry。

- **MySQL / InnoDB**：MVCC ＋ 鎖的混合路線。隔離預設 **Repeatable Read**。它的 RR 靠 **next-key lock**（record lock ＋ gap lock）在範圍掃描時鎖住「列＋列前間隙」來擋 phantom——是**用鎖**擋幻讀，而非純快照。它的 Serializable 基本上是把普通 `SELECT` 隱式升級成 `SELECT ... FOR SHARE`（8.0 前的舊寫法是 `LOCK IN SHARE MODE`；2PL 風格的共享讀鎖，且僅在 autocommit 關閉時發生——autocommit 開啟的單句 SELECT 仍走非鎖一致讀），不是 SSI。

本質差一句話：**PostgreSQL 用「偵測衝突後中止重試」達成可序列化（樂觀風格的 SSI）；MySQL 用「加範圍鎖預先擋住」防幻讀（悲觀風格的 next-key）。** 一個賭衝突少、發生才處理；一個先上鎖、寧可擋住。

### 在哪些系統扮演什麼角色

- **PostgreSQL**：複雜查詢、需要強一致與真 serializable、重 JSONB／地理／全文／擴充（PostGIS、pgvector）的場景常選它。SSI 讓「需要 serializable 但不想自己上一堆顯式鎖」變可行，代價是要寫 retry。
- **MySQL/InnoDB**：簡單高並發 OLTP、讀多寫少、生態（複製、託管服務、運維工具）成熟度與既有部署量大的場景。預設 RR ＋ next-key 對「讀範圍要穩定」的交易直覺友善（不用自己想快照），但 gap lock 帶來的隱性鎖範圍是死結來源。

### 保證與限制

| 維度 | PostgreSQL（18） | MySQL / InnoDB（8.4） |
|---|---|---|
| 預設隔離級別 | Read Committed | Repeatable Read |
| RR 的真實語意 | snapshot isolation（連 phantom 都防、**不防 write skew**） | 比 snapshot isolation 弱：Jepsen 測出 RR 仍有 G-single（read skew）、lost update、write skew |
| 擋 phantom 的手段 | 快照（RR 即不出現幻讀） | next-key lock（鎖列＋間隙） |
| 真 serializable 的實作 | SSI（依賴追蹤＋中止重試） | 2PL 風格讀鎖（普通讀升級為共享鎖） |
| 死結偵測 | wait-for graph，`deadlock_timeout` 預設 1s 後才查 | wait-for graph，`innodb_lock_wait_timeout` 預設 50s（逾時放棄） |
| 多版本回收 | heap + VACUUM（bloat 風險） | undo log + purge（history list 風險） |

關鍵限制／提醒（2026-06）：

- PostgreSQL 的 SSI **要求應用能 retry**——交易隨時可能因 `could not serialize` 被中止；沒寫 retry，serializable 等於把錯誤丟給使用者。
- MySQL InnoDB 的 RR **不等於 snapshot isolation**：Jepsen 對 MySQL 8.0.34 的測試發現它的 RR 連 snapshot isolation 都不滿足（出現 G-single、lost update、write skew）。把 InnoDB RR 當「安全的可重複讀」會踩坑；需要時用顯式 `SELECT ... FOR UPDATE` 補。MariaDB 為此在 11.8 起加了預設開啟的 `innodb_snapshot_isolation`，但 Jepsen 指出該修補在併發負載下仍可重現異常。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| PostgreSQL（SSI serializable） | 真 serializable、讀不上鎖、防 write skew | 跨列不變量強、寫衝突中等、能寫 retry | 中止重試成本；長交易脹 bloat；高衝突下中止率高 |
| MySQL InnoDB（RR + next-key） | 範圍讀穩定、擋 phantom、無中止 | 高並發 OLTP、讀多、生態成熟度優先 | RR 弱於 SI、要防 write skew 須顯式鎖；gap lock 隱性死結 |
| 升 Serializable 解一切 | 最強隔離 | 一致性壓倒吞吐 | PG 是 SSI 重試成本、MySQL 是讀鎖並發崩——都不是免費 |

選型上：跨列不變量多、要 DB 幫你扛序列化正確性、團隊能處理 retry → PostgreSQL Serializable。以高並發單列 OLTP 為主、生態與運維熟悉度優先、能接受自己用顯式鎖補強 → MySQL。不要因為「名字都叫 Repeatable Read」就假設兩邊行為一樣——這是本條最大的陷阱。

### 常見誤解與陷阱

- **「兩邊的 Repeatable Read 一樣」**——最致命的誤解。PG 的 RR＝snapshot isolation（強、不防 write skew）；MySQL 的 RR 在實測下比 snapshot isolation 還弱。同名不同義，遷移時隔離行為會悄悄變。
- **「PostgreSQL Serializable 慢所以別用」**——SSI 的成本主要是**中止重試**，在低衝突下接近 snapshot isolation。先量你的衝突率再下結論，別憑「serializable 一定貴」就放棄正確性。
- **「MySQL RR 能擋 write skew」**——InnoDB 的 next-key 擋的是 phantom（插入），不是 write skew（各寫不同列）。要防 write skew 得自己 `SELECT ... FOR UPDATE` 把相關列鎖起來，或升 Serializable。
- **把 PG `deadlock_timeout` 和 MySQL `innodb_lock_wait_timeout` 當同一個東西**——前者（PG，預設 1s）是「等多久**開始查**死結」；後者（MySQL，預設 50s）是「等鎖多久就**放棄**」。語意與量級都不同，調校時別混。
- **以為換 DB 只是換連線字串**——隔離預設不同（RC vs RR）、RR 語意不同、serializable 機制不同、鎖逾時行為不同。跨 PG/MySQL 的應用，並發正確性不會自動平移。

### 延伸閱讀

- PostgreSQL 官方文件，Transaction Isolation（含 SSI 與 retry 要求）：https://www.postgresql.org/docs/current/transaction-iso.html
- MySQL 官方文件，InnoDB Transaction Isolation Levels：https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html
- Jepsen，MySQL 8.0.34（RR 弱於 snapshot isolation 的實測）：https://jepsen.io/analyses/mysql-8.0.34
- PostgreSQL wiki，Serializable Snapshot Isolation：https://wiki.postgresql.org/wiki/SSI
