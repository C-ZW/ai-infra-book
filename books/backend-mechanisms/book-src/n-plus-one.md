# N+1 查詢：一個迴圈打爆資料庫

有一段碼，在你的開發機上跑得飛快。它撈出一頁訂單、為每筆訂單把客戶名印出來，整個端點 8 毫秒回應，測試全綠，code review 沒人皺眉。你把它上了線。

幾週後，這個端點開始出現在慢查詢告警裡。同一段碼、同一個查詢、一行都沒改，p99 從 8 毫秒漂到 600 毫秒，DB 的連線池在尖峰時被它一個端點吃乾。你去看 SQL log，畫面是這樣的——

```
SELECT * FROM orders WHERE user_id = 42 LIMIT 50;
SELECT * FROM customers WHERE id = 1001;
SELECT * FROM customers WHERE id = 1002;
SELECT * FROM customers WHERE id = 1003;
... (再 47 行幾乎一模一樣的查詢)
```

一個請求，發了 51 次查詢。第一次撈清單，剩下 50 次各補一個客戶。這就是 **N+1 查詢**：取一份有 N 個項目的清單花 1 次查詢，接著為**每一個項目各發一次**後續查詢去補它的關聯資料，總共 1 + N 次往返。它是後端最常見、也最隱形的效能漏洞之一——隱形到它能通過所有測試、撐過 code review、在開發機上完全無感，然後在上線後的某個流量高峰，安靜地把資料庫打爆。

這一章要把它講透：為什麼它在開發機上看不出來、它的成本到底花在哪、為什麼 ORM 幾乎是**預設**製造它、以及解掉它的那幾條路各自買到什麼、又欠下什麼新的債。

## 問題不在查詢慢，在查詢多

先把一個直覺擋掉：N+1 慢，**不是因為任何一條查詢慢**。那 50 條 `SELECT * FROM customers WHERE id = ?` 每一條都走主鍵索引，DB 內部執行可能只要幾十微秒，快得不能再快。如果你把其中任一條單獨拎出來 `EXPLAIN`，計畫漂亮、成本趨近於零。問題不在單條，在**條數**。

要看清成本花在哪，得把一次資料庫往返拆開。當應用程式對 DB 發一條查詢，真正消耗時間的遠不只「DB 執行 SQL」這一段。一次 round-trip 至少疊著這幾筆**與資料量無關的固定成本**：

- **網路往返（RTT）**：請求飛到 DB、結果飛回來。同機房同網段可能 0.2 毫秒，跨可用區就是 1～2 毫秒，跨區域幾十毫秒。
- **連線取得**：從連線池借一條連線、用完歸還；池滿時還要排隊等。
- **查詢規劃**：DB 把 SQL 文字 parse、產生執行計畫（除非命中 prepared statement 快取）。
- **結果序列化**：把結果集編碼成 wire protocol、應用端再解碼成物件。

這筆固定成本，每一次往返都要付一遍，**而且不管你查回來的是一整張表還是一個欄位，它幾乎一樣貴**。N+1 的致命之處，就是把這筆固定成本**乘以 N**。它不是讓每次操作變慢，而是讓你做了 N 次本來只需要做 1 次的事。

手算一遍就觸目驚心。回到開頭那個訂單列表：50 筆訂單、每筆補一個客戶名。假設單次 DB round-trip 的固定成本是 2 毫秒（一個跨可用區、有點負載的 DB 很普通的數字），純資料傳輸的部分小到可以忽略。N+1 寫法的往返成本是：

```
1 次查訂單  +  50 次各查一個客戶  =  51 次 round-trip
51 × 2 ms = 102 ms
```

現在換一種寫法：先查出 50 筆訂單、收集它們的 `customer_id`，再用**一條**查詢把這 50 個客戶一次撈回——

```sql
SELECT * FROM customers WHERE id IN (1001, 1002, ..., 1050);
```

成本變成：

```
1 次查訂單  +  1 次 IN-list 批次  =  2 次 round-trip
2 × 2 ms = 4 ms
```

**同樣的輸入、同樣的結果、同一份資料**，延遲從 102 毫秒降到 4 毫秒，差 25 倍。而這個倍數**會隨 N 一起長**：列表頁從顯示 50 筆變成顯示 500 筆，N+1 寫法是 `501 × 2 = 1002 ms`，IN-list 寫法還是 `2 × 2 = 4 ms`，差距拉開到 250 倍。這就是為什麼 N+1 是個會「自己惡化」的 bug——它的傷害與資料規模成正比，而資料規模只會往上長。

## 為什麼開發機永遠看不出來

如果 N+1 這麼貴，為什麼它能一路躲過開發、測試、review，直到上線才爆？因為它在開發機上的成本，恰好被三個一起趨近於零的因子掩蓋掉了。

把那條 `成本 ≈ (1 + N) × RTT` 攤開，N+1 在開發機上無感，是因為這條式子的**兩個乘數同時都很小**：

- **RTT 趨近 0**。開發時 DB 通常是 localhost 或同一台機器上的 Docker 容器，往返走的是迴環介面（loopback），RTT 是微秒等級。固定成本被壓到幾乎不存在，乘以多少個 N 都還是很小。上線後 DB 在另一台機器、另一個可用區，RTT 一下跳到 1～2 毫秒——同一段碼，每次往返貴了上千倍。
- **N 趨近 0**。開發時的測試資料庫裡，一個使用者可能只有 3 筆訂單；上線後的真實帳號有 500 筆。N=3 的時候 `4 次往返 × 微秒` 完全無感，N=500 的時候就是另一個世界。
- **DB 沒有負載**。開發機上的 DB 只服務你一個人，連線隨借隨有、buffer cache 全熱、CPU 全空。上線後它同時扛幾百個併發請求，每多一次往返都在和別人搶連線、搶 CPU、搶鎖。

三個因子相乘，讓 N+1 的成本在開發環境下小到測不出來。這也直接給出它**唯一可靠的偵測方式**：不要看延遲、要**數查詢次數**。延遲在開發機上騙你，但「一個端點發了幾條 SQL」這個數字不會——它在 localhost 和正式環境是一模一樣的 51。所以對付 N+1 的測試不是「斷言這個端點 < 50ms」（這在開發機永遠通過），而是「斷言這個端點對 DB 的查詢數 ≤ 某個門檻」。很多框架（Rails 的 `assert_queries_count`／`assert_no_queries`、各種 query counter middleware）就是為了把這條斷言寫進測試而存在。把 N+1 從「效能問題」重新定義成「**查詢次數問題**」，是看懂它的第一步。

## ORM 不是在幫你，它是預設製造 N+1 的那個

N+1 最毒的版本，不是工程師手寫迴圈發查詢——那種至少看得見。最毒的是 ORM 的**惰性載入（lazy loading）**，因為它把那個迴圈藏進了一個看起來完全無害的屬性存取後面。

看這段虛擬碼，它讀起來像在操作記憶體裡的物件，沒有任何一行寫著「查詢資料庫」：

```python
orders = Order.where(user_id=42).limit(50)   # 1 次查詢，撈出 50 筆訂單

for order in orders:
    print(order.customer.name)               # 每一圈，order.customer 偷偷發一次查詢
```

關鍵在 `order.customer` 這個存取。在惰性載入的 ORM 裡，`Order` 物件初始化時**並沒有**把關聯的 `customer` 一起載進來；它只記了一個 `customer_id`。直到你第一次去碰 `order.customer` 這個屬性，ORM 才在那一刻**靜默地**發出一條 `SELECT * FROM customers WHERE id = ?`。迴圈跑 50 圈，這個屬性存取就觸發 50 次查詢——而程式碼表面上只有一個看起來人畜無害的 `.name`。

這是 N+1 之所以隱形的根因：**發出查詢的動作，被偽裝成了存取一個記憶體屬性**。你的眼睛看到的是物件導覽，DB 那端發生的是一場查詢風暴。惰性載入幾乎是所有主流 ORM 的**預設行為**——Hibernate/JPA 的集合關聯（`@OneToMany`、`@ManyToMany`）預設 `LAZY`（單值的 `@ManyToOne`／`@OneToOne` 規格上預設 `EAGER`，但實務常被改成 `LAZY`）、ActiveRecord 不加 `includes` 就逐筆載入、Django 的 `ForeignKey` 不加 `select_related` 就在存取時查、SQLAlchemy 預設 `lazy='select'`。它們這麼設計有合理的理由：你不總是會用到每個關聯，預設全部 eager 載入會拉回大量用不到的資料。但這個合理的預設，副作用就是**只要你在迴圈裡碰關聯，就掉進 N+1**，而且語言不會給你任何警告。

GraphQL 把這個陷阱放大到了架構層級。GraphQL 的 resolver 是**逐欄位、逐元素**執行的：一個查詢拿回 10 篇 post，框架接著為這 10 篇 post **各自**呼叫一次 `author` resolver 去解析作者。如果每個 `author` resolver 都獨立查一次 DB，這個查詢就是 1（查 posts）+ 10（逐篇查 author）= 11 次往返——GraphQL.js 官方文件用的正是這個 10 篇 post → 11 次查詢的例子。更糟的是它**天生巢狀**：`post → author → author.company → company.employees`，每往下一層、每個父元素都在 fan-out，N+1 可以變成 N×M×K。在 GraphQL 裡 N+1 不是「不小心寫錯」，而是 resolver 模型的**預設形狀**，你必須主動架一層東西去攔它。

## 三條解法，與它們各自欠下的債

知道病灶在「次數」，解法的方向就清楚了：**把 N 次往返壓回常數次**。歷史上演化出三條主要的路，它們不是誰取代誰，而是在不同的關聯結構與架構下各自勝出。逐一看，重點是每一條買到什麼、又欠下什麼新的債。

### 路一：JOIN／eager loading——一次撈齊，但小心笛卡兒爆炸

最直接的念頭：既然問題是「分多次撈」，那就在第一次查詢時用 JOIN 把關聯**一起**撈回來。一條 SQL 取齊主表加關聯，往返數固定為 1。ORM 把這條路包成 `includes`（Rails 的 eager_load 分支）、`JOIN FETCH`（JPA）、`select_related`（Django，專給一對一/多對一）。

```sql
SELECT o.*, c.*
FROM orders o
JOIN customers c ON c.id = o.customer_id
WHERE o.user_id = 42 LIMIT 50;
```

對於**多對一**（多筆訂單指向同一個客戶）這完美——一條查詢、零放大。但 JOIN 有個會反咬你的邊界：**一對多關聯的笛卡兒乘積膨脹**。

設想你要撈 10 篇 post，每篇 post 有它的 comments（一對多）和 tags（又一對多）。如果你天真地把兩個一對多都 JOIN 進來，結果集的行數不是相加而是**相乘**：10 篇 post × 每篇 30 則 comment × 每篇 200 個 tag = **60,000 行**。每一行都把那篇 post 的所有欄位重複攜帶一次，comment 和 tag 的所有組合被笛卡兒展開。你為了省往返，卻讓 DB 算出、序列化、傳輸了六萬行高度重複的資料，再讓應用端在記憶體裡把它們去重組裝回 10 篇 post——**省下的往返成本，被膨脹的資料傳輸與組裝成本反噬**，往往得不償失。Hibernate 對這件事的態度直接到會**拋例外**：你一旦試圖在同一個查詢 `JOIN FETCH` 兩個 `List` 型的集合（嚴格說是兩個 Bag——沒有 `@OrderColumn` 的無序 `List`；改用 `Set` 或加 `@OrderColumn` 可避開），它丟出 `MultipleBagFetchException`——它寧可報錯，也不讓你寫出一個會笛卡兒爆炸的查詢。

JOIN 還有第二個更陰險的邊界，和**分頁**致命地衝突。當你對一個帶一對多 JOIN 的查詢下 `LIMIT 50`，`LIMIT` 限制的是 **JOIN 之後的行數**，不是 post 的篇數。撈 10 篇 post、每篇 5 則 comment，JOIN 後是 50 行，`LIMIT 50` 砍下去——你可能只拿到了前 3 篇完整 post 加第 4 篇的一半 comment。分頁的語意整個壞掉。這正是為什麼分頁要避開一對多 JOIN：Hibernate（含 6.x）碰到「分頁 + 一對多集合 `JOIN FETCH`」時，預設並不會替你退回兩段式，而是把整個結果集抓回記憶體、在**記憶體裡分頁**（並記下 `HHH000104: firstResult/maxResults specified with collection fetch; applying in memory!` 警告），資料一大就是效能地雷。正確做法是改用**先查一頁的主鍵、再用 IN-list hydrate 集合**的兩段式（即下一節的路二）——這也是 Rails `preload`／SQLAlchemy `selectinload`／Django `prefetch_related` 這類「本來就分兩段」的策略內建走的路，但在 Hibernate 這邊得你自己寫，不是它自動幫你做。

### 路二：IN-list 兩段式——避開膨脹，固定兩次往返

笛卡兒爆炸的教訓指向第二條路：**別 JOIN，分兩次查，但兩次都是批次的。** 先查清單拿到 N 個主鍵與外鍵，再用一條 `WHERE fk IN (...)` 把所有關聯一次撈回，最後在應用程式的記憶體裡把兩邊配對起來（in-memory join）。

```sql
-- 第一段：撈清單
SELECT * FROM orders WHERE user_id = 42 LIMIT 50;
-- 收集 50 個 customer_id，第二段一次撈回
SELECT * FROM customers WHERE id IN (1001, 1002, ..., 1050);
```

往返數**固定為 2**，無論 N 是 50 還是 5000，而且**完全沒有笛卡兒膨脹**——客戶資料只回傳一次，不被 post×comment×tag 展開。對一對多它一樣漂亮：撈 10 篇 post、收集 10 個 post id、`SELECT * FROM comments WHERE post_id IN (10 個 id)`，comment 只回它本來的數量、在記憶體裡按 `post_id` 分組掛回去。這就是 Rails `preload`、Django `prefetch_related`、Hibernate `@BatchSize`、SQLAlchemy `selectinload` 走的策略。

這裡藏著一個非常具體、很多人沒注意過的 ORM 行為差異，值得停下來看：**Rails 的 `includes` 並不固定走哪一條路，它會自己決定。** 預設情況下 `includes` 會用 `preload`（兩段式 IN-list）；但如果你的查詢在 `WHERE` 或 `ORDER BY` 裡**引用了被關聯表的欄位**（例如「找出客戶名以 A 開頭的訂單」），那條件沒辦法在兩段式裡表達——第一段查 orders 時還沒撈 customers——於是 `includes` 會**自動切換成 `eager_load`（LEFT OUTER JOIN）**，把兩表合在一條查詢裡好讓 WHERE 能過濾。同一個 `includes` 呼叫，會因為你有沒有跨關聯過濾而產生兩種完全不同的 SQL。理解這個自動切換，才解釋得了為什麼有時候 `includes` 給你乾淨的兩段式、有時候又冒出一個 JOIN——它不是隨機的，是 WHERE 子句逼的。

IN-list 自己也有一個邊界：**清單不能無限長**。`WHERE id IN (...)` 塞進上萬個值時，查詢的 parse 與規劃會變慢，有些資料庫對單條查詢的參數個數有硬上限（如某些驅動的綁定參數上限）。所以批次載入器在 N 很大時會**自動分批**——把 5000 個 id 切成 5 批、每批 1000，發 5 條 IN 查詢。從「1+N」優化到「1+ceil(N/批量)」，仍然是常數級的往返，只是常數稍大。

### 路三：DataLoader——在事件迴圈裡把散落的 load 縫成一批

前兩條路都要求你在**寫查詢時就知道**「我接下來要批次撈什麼」。但 GraphQL 的 resolver 是各自獨立、彼此不知情地執行的——`author` resolver 被框架呼叫 10 次，每次只拿到一個 `authorId`，它**沒有機會**看到另外 9 個。你沒有一個「迴圈」可以改寫成 IN-list，因為 fan-out 是框架在背後做的。這就是 DataLoader 這個模式要解的問題，它的巧妙之處在於**利用事件迴圈的節奏，把時間上湊在一起的多個獨立請求縫成一批**。

機制是這樣的。你不直接查 DB，而是呼叫 `userLoader.load(authorId)`，它立刻回給你一個 Promise，但**先不發查詢**——它把這個 key 丟進一個暫存陣列，記下來。接著事件迴圈這一輪（一個 tick）裡，10 個 `author` resolver 各自呼叫了 `load()`，10 個 key 全被收集進同一個陣列。等到當前這一輪同步程式碼跑完、事件迴圈準備進下一個 tick 時，DataLoader 把累積的這 10 個 key**一次性**交給你提供的 batch function：

```js
// batch function：收到一批 key，回傳一批值，順序必須與 key 對齊
async function batchGetUsers(userIds) {
  const rows = await db.query(
    'SELECT * FROM users WHERE id IN (?)', [userIds]
  );
  // 關鍵：回傳陣列的第 i 個，必須對應 keys 的第 i 個
  const byId = new Map(rows.map(r => [r.id, r]));
  return userIds.map(id => byId.get(id) ?? null);
}
```

一條 IN-list 查詢撈回全部 10 個 user，DataLoader 再把結果按原本的順序分發給那 10 個還在等待的 Promise。1+10 就這樣被壓成了 1+1，而且每個 resolver 都還以為自己是獨立查的——批次化對它們完全透明。

這裡有幾個非顯然的邊界，是「真的懂 DataLoader」和「聽過 DataLoader」的分水嶺：

**第一，「同一個 tick」是它的物理邊界，不是設定值。** DataLoader 靠 JavaScript 事件迴圈的單執行緒節奏來界定「哪些 load 算同一批」——它用一個排在 Promise microtask 之後的排程（`enqueuePostPromiseJob`）來決定何時 flush：在 Node 下實作為 `Promise.resolve().then(() => process.nextTick(fn))`，先讓當輪的 Promise microtask 全部跑完、再排程 flush（瀏覽器無 `process.nextTick` 時才退回 `setImmediate`／`setTimeout`）。只有在**當前這一輪同步執行**裡發生的 `load()` 才會被合進同一批；跨越 `await` 邊界、落到下一個 tick 的 `load()`，會進到下一批。這也是為什麼 DataLoader 是 Node 生態的東西——它的批次邊界**就是事件迴圈的 tick**。在多執行緒、沒有單一事件迴圈節奏的環境裡，這套「靠時間湊批」的機制要換成別的實作（如 Java 的 `java-dataloader` 用顯式的 dispatch）。

**第二，它的快取是請求作用域的（request-scoped），這不是效能優化，是正確性要求。** DataLoader 在同一批裡會對重複的 key 去重（10 個 resolver 都要 user 1001，只查一次），並把結果記住，同一個請求內再 `load(1001)` 直接給快取值。但這份快取**絕對不能跨請求共用**。它是請求生命週期內的記憶化（memoization），不是 Redis 那種共享快取——如果你把一個 DataLoader instance 做成全域單例、跨請求重用，A 使用者的請求會讀到 B 使用者請求留下的舊資料，甚至跨使用者洩漏資料。所以鐵律是：**每個請求建一個全新的 DataLoader instance**，請求結束就丟。把它當共享快取用，是一個會洩漏資料的安全漏洞，不只是 bug。

**第三，batch function 的回傳順序是契約。** 你的 batch function 收到 `[1001, 1003, 1002]`，回傳的陣列**必須**是 `[user1001, user1003, user1002]`——第 i 個位置對應第 i 個 key。但 `SELECT ... WHERE id IN (...)` 回來的行**順序是不保證的**，DB 可能按任何順序給你。如果你直接把查詢結果原樣回傳，DataLoader 會把張三的資料分發給李四的 Promise。所以 batch function 裡那一步「用 Map 把結果按 id 索引、再按原始 key 順序重排」不是可有可無的整理，是**正確性的核心**。漏了它，你不會看到錯誤訊息，只會看到資料默默地配錯人——這是 N+1 解法裡最難 debug 的一類 bug。

## 修了一層，別漏了下一層

GraphQL 的巢狀讓 N+1 有個特別容易留尾巴的失敗模式，值得單獨點出來。一個查詢可能是 `post → author → author.company`：你很自然地為 `author` 加了 DataLoader，把「逐篇查 author」壓成一批，鬆一口氣。但 `author.company` 這一層呢？如果它還是逐個 author 獨立查公司，你只是把 N+1 從第一層挪到了第二層——`1 + 1（authors）+ N（每個 author 查 company）`。

**每一層關聯都是一個獨立的 fan-out 點，都需要自己的批次化。** 只在最外層加 loader 而漏掉內層，是個很常見、又很難察覺的半成品修復——因為它讓查詢數從「災難」降到「還行」，告警不再響，於是沒人回頭看其實還有一層在逐筆查。回到那個偵測原則：盯**查詢次數**。如果一個 GraphQL 查詢的 DB 查詢數會隨著結果集裡某一層的元素數量線性成長，那一層就還有 N+1 沒解掉，不管你在別層加了多少 loader。

## 什麼時候根本不用修

把 N+1 講得這麼兇，最後要平衡一句：**不是每個 N+1 都值得修。** 修它有成本——eager loading 會拉回你未必用得到的資料，DataLoader 是一層要維護的間接，過早的批次化也是一種過度工程。

判準還是回到那條 `成本 ≈ (1 + N) × RTT` 的式子，看 N 這個變數的性質：

- **N 恆定且很小**：如果某個關聯永遠只取固定的 3 筆（例如「顯示這個訂單的前 3 筆狀態變更」），N=3 是寫死的、不會隨資料長大，那 `1+3` 次往返完全可以接受，為它架 DataLoader 是殺雞用牛刀。
- **這條路徑不是熱點**：一個一天被呼叫五次的後台報表端點，就算它 N+1 到 500 次查詢、跑了一秒，也排在你該優化的清單很後面。
- **但要警惕「現在小不代表以後小」**：N+1 的危險正在於 N 是會長大的變數。今天每個使用者 3 筆訂單，產品做大後是 3000 筆，那段「現在無感」的碼會在某個你早忘了它存在的時刻自己惡化成事故。

所以決策不是「看到 N+1 就修」，而是先**量**——用查詢計數測出這條路徑實際發了幾條 SQL、N 會不會隨業務長大、它在不在熱路徑上——超過門檻、或 N 是會成長的變數，才動手。在不會長大的小 N 上花複雜度去消滅 N+1，本身就是另一種形式的過度工程。

## 為什麼是這個形狀

退一步看，N+1 的整個故事，都是從一個樸素的物理事實裡長出來的：**每一次跨越行程邊界的往返，都有一筆與你搬多少資料無關的固定成本；把這筆固定成本乘以 N，就是 N+1。**

正因為成本在「次數」而不在「資料量」，所有的解法本質上都是同一件事——**把 N 次往返折疊成常數次**：JOIN 把它折成 1 次（代價是可能笛卡兒膨脹），IN-list 折成 2 次（代價是清單長度上限），DataLoader 折成 1+1 次（代價是綁在事件迴圈、且要嚴守請求作用域）。它們不是三個互斥的選項，而是針對不同關聯結構（多對一還是一對多）、不同架構（手寫查詢還是 GraphQL fan-out）的同一個答案的三種形狀。

正因為發查詢的動作能被 ORM 偽裝成存取一個記憶體屬性，N+1 才會隱形——所以對付它的紀律不是「讓查詢更快」，而是「**數清楚一個請求到底發了幾條查詢**」。延遲會在開發機上對你說謊，查詢次數不會。當你下次看到一個端點在生產環境莫名變慢、SQL log 裡刷過一整片長得幾乎一樣的 `WHERE id = ?`，你會立刻認出它：那不是哪條查詢慢了，那是一個迴圈，正在一次一次地敲打資料庫的門。

## 延伸閱讀

- [Solving the N+1 Problem with DataLoader — GraphQL.js 官方文件（posts/authors 的標準範例與 per-request loader）](https://www.graphql-js.org/docs/n1-dataloader/)
- [graphql/dataloader — GitHub README（per-tick batching、request-scoped caching、batch function 順序契約的權威說明）](https://github.com/graphql/dataloader)
- [Batching — GraphQL Java 官方文件（JVM 生態的 DataLoader 與顯式 dispatch）](https://graphql-java.com/documentation/batching/)
- [N+1 Problem in Hibernate and Spring Data JPA — Baeldung（JOIN FETCH、@BatchSize、EntityGraph 對照）](https://www.baeldung.com/spring-hibernate-n1-problem)
- [Preload vs Eager Load vs Joins vs Includes — BigBinary（Rails includes 如何在 preload 與 eager_load 之間自動切換）](https://www.bigbinary.com/blog/preload-vs-eager-load-vs-joins-vs-includes)
- [Database access optimization — Django 官方文件（select_related vs prefetch_related）](https://docs.djangoproject.com/en/stable/topics/db/optimization/)
