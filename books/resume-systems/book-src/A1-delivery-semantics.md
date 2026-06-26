# A · 交付語意與重複處理

本領域回答一件事：當訊息穿過會丟封包、會逾時、會重投的網路，**一筆事件到底被處理幾次**——零次、至少一次、還是剛好一次？這個檔含五條互相咬合的條目：先給「交付語意三選一」的全景，再展開 at-least-once 帶來的重複問題、拆穿 exactly-once 的真相，最後把兩個壓制重複的核心機制——**冪等（idempotency）**與**去重（dedup）**——講到機制級。這五條是後面所有訊息工具（SQS／Kafka／RabbitMQ…，領域 A 工具篇）與跨服務交付（outbox／saga，領域 A 順序篇）的共同地基；訊息順序、重試退避、DLQ、跨服務一致性等主題在本領域其他檔深講（見領域 A 順序篇與工具篇），本檔需要時才引用、不重複機制。

## 交付語意三選一

### 定義與原理

交付語意（delivery semantics）描述的是：在「生產者 → broker → 消費者」這條鏈上，**同一筆訊息最終影響系統狀態的次數**。三種選項：

- **at-most-once（至多一次）**：每筆訊息最多被處理一次，可能 0 次。實作上就是「不重試、不要求 ack」——送出去就忘（fire-and-forget）。丟了就丟了，但絕不重複。
- **at-least-once（至少一次）**：每筆訊息保證被處理至少一次，可能多次。實作上就是「處理完才 ack，沒收到 ack 就重投」。不會掉，但會重複。
- **exactly-once（剛好一次）**：每筆訊息對系統狀態的影響剛好一次。這是大家想要的，但它在「交付」這一層是不可能的（見「exactly-once 的真相」）——能達成的是 at-least-once 加上消費端去重後**看起來像** exactly-once。

第一原理是一個無法迴避的取捨：**在不可靠網路上，你只能選擇「寧可丟、不重複」或「寧可重、不丟失」，不能兩者都要。** 根因是 ack 也會在網路上遺失——生產者送出訊息、broker 處理完回 ack，若 ack 在回程丟了，生產者無法區分「broker 沒收到」與「broker 收到了但 ack 弄丟」。它若重送就可能重複（at-least-once），若不重送就可能遺失（at-most-once）。沒有第三條路。

### 解法空間

三種語意各對應一組明確的工程選擇：

- **要 at-most-once**：關掉重試、用 fire-and-forget transport。例如 Redis Pub/Sub——訊息只送給發佈當下在線的訂閱者，離線者永久錯過、無 replay（見 Redis Pub/Sub vs Streams，領域 A 工具篇）。UDP-style 的 metrics 上報（StatsD）也屬此類：掉幾筆取樣點不影響趨勢。
- **要 at-least-once**：處理成功才 ack、逾時未 ack 就重投。這是絕大多數持久化佇列的**預設**——SQS、Kafka 的基本消費、RabbitMQ 的 manual ack 都落在這裡。代價是消費端必須自己處理重複（見「at-least-once 與重複處理」）。
- **要「看起來像 exactly-once」**：at-least-once 的傳輸 + 消費端冪等或去重。沒有別條路；任何宣稱 exactly-once 的系統，拆開看都是這個組合（見「exactly-once 的真相」）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| at-most-once（fire-and-forget） | 絕不重複，可能丟 | metrics、log 取樣、即時但可丟的推播 | 丟訊息靜默無感，難察覺；不可用於金流／狀態變更 |
| at-least-once（ack-on-success + retry） | 絕不丟，可能重複 | 大多數業務佇列的預設 | 消費端**必須**冪等或去重，否則一筆操作做兩次 |
| at-least-once + 消費端去重 | 對外觀察=每筆影響一次 | 金流、扣庫存、發信、任何有副作用的處理 | 去重狀態需持久化＋有 TTL；跨副作用（如「呼叫外部 API」）的去重最難 |
| broker 內建 FIFO/EOS | broker 邊界內 effectively-once（SQS FIFO 靠 5 分鐘去重視窗、Kafka EOS 靠交易，兩者機制不同） | 重複間隔落在去重視窗內（SQS）／同叢集 read-process-write（Kafka） | 只在該 broker 邊界內成立，跨系統就失效 |

### 何時需要

判準是**重複處理的代價**，不是「越強越好」：

- **代價＝損失金錢或破壞不變量** → 要 exactly-once 觀感（at-least-once + 去重）。扣款、發券、扣庫存、寄帳單。
- **代價＝可容忍、可後補對帳** → at-least-once 裸用即可。寄通知信（多收一封比漏收一封好）、快取失效、重算衍生資料。
- **丟失比重複更可接受、且量大求快** → at-most-once。高頻 metrics、可取樣的 telemetry。

升一級語意通常要付出延遲與吞吐：例如 Kafka 開啟交易性 EOS，社群實測約增加數毫秒延遲、降約 10–20% 吞吐（2026-06）。所以反向問句更有用：**「這條訊息重複處理一次，誰會痛？」** 沒人痛就別上 exactly-once。

**Worked example**：一條推播管線每天 10 萬則訊息，broker 重投率 0.1%。at-least-once 下約 `100,000 × 0.1% = 100` 筆會被投遞兩次。若這是「發優惠券」，就是 100 張多發的券（真金白銀）→ 必須去重；若這是「你有一則新通知」的提醒，100 則重複提醒幾乎無感 → 裸 at-least-once 即可。同一個重投率，要不要加去重，由副作用代價決定。

### 常見誤解與陷阱

- **「我用了 exactly-once 的佇列，所以不用管重複」**——broker 的 exactly-once 只在它自己的邊界內成立。一旦消費者「收到訊息 → 呼叫外部支付 API → 然後才 ack」，那個外部呼叫就在 broker 的保證之外，照樣可能因消費者在 ack 前崩潰而重做。
- **把「順序」和「不重複」綁在一起想**——它們是正交的。FIFO 給你順序，但順序不等於去重；at-least-once 可以有序也可以重複。
- **以為 at-most-once 是「比較弱所以比較簡單」**——它在金流場景是災難（靜默丟款），「簡單」是因為它把難題（丟失）丟給了你沒注意的地方。
- **把語意說成 broker 的屬性**——它其實是**端到端**的屬性。broker 給 at-least-once，但若你的消費者 ack 之後才開始處理（ack-then-process），你實際拿到的是 at-most-once。語意由「ack 的時機」決定，不只由 broker 決定。

### 延伸閱讀

- You Cannot Have Exactly-Once Delivery（Brave New Geek）：https://bravenewgeek.com/you-cannot-have-exactly-once-delivery/
- Apache Kafka — Message Delivery Semantics（官方文件）：https://kafka.apache.org/documentation/#semantics
- Amazon SQS — Standard vs FIFO queues（官方文件）：https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-queue-types.html

## at-least-once 與重複處理

### 定義與原理

選了 at-least-once（多數系統的預設），就買下了一個義務：**消費端必須在「同一筆訊息出現兩次以上」時，仍只產生一次有效影響。** 重複從哪來？三個典型來源：

1. **broker 重投**：消費者處理完、ack 在回程丟失，broker 逾時後重投同一筆。
2. **生產者重試**：生產者送出、broker 的 ack 丟失，生產者重送，broker 真的收了兩筆。
3. **消費者重啟/rebalance**：處理到一半崩潰、訊息回到佇列、被另一個 worker 接手重做前半段。

很多人一聽到重複，反射動作是「做冪等」。但冪等只是解法空間裡的一個——**而且不是每種操作都改得成冪等**。完整的解法空間比冪等大。

### 解法空間

壓制 at-least-once 重複的辦法（由「改操作本身」到「在外圍擋」）：

- **冪等操作（idempotent operation）**：把操作設計成「做 N 次＝做 1 次」。`SET status='paid'` 天生冪等；`balance = balance - 10` 天生不冪等（見「冪等 idempotency」）。
- **唯一約束擋重（unique constraint）**：在資料庫對自然鍵或冪等鍵加 `UNIQUE`，重複插入直接撞約束失敗 → 當作「已處理」吞掉。讓資料庫替你做去重，最便宜可靠。
- **去重表/去重視窗（dedup store）**：另存一張「已處理過的訊息 id」表，處理前先查、處理後寫入，過期清掉（見「去重 dedup」）。
- **可重放設計（replay-safe）**：把處理寫成「依當前狀態算出目標狀態」而非「在當前狀態上累加」。重放整段也只收斂到同一結果——這是 event sourcing／狀態機 reduce 的核心性質（見 Event sourcing 與 CQRS，領域 K）。
- **副作用搬進同一筆交易**：把「業務狀態變更」與「標記已處理」放進**同一個資料庫交易**一起 commit；要不一起成功、要不一起回滾，杜絕「業務做了但沒標記、於是重做」的縫隙（跨服務版的此手法＝outbox，見 outbox／saga，領域 A 順序篇）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 冪等操作 | 同一輸入重放=同一結果 | 操作本身可寫成「設定目標態」 | 累加型／呼叫外部 API 型操作改不成冪等 |
| 唯一約束擋重 | 重複寫入被 DB 拒絕 | 有自然唯一鍵（order_id…） | 撞約束的錯要當「成功」處理、別當失敗重試 |
| 去重表 + TTL | 視窗內同 id 只處理一次 | 無自然鍵、需顯式冪等鍵 | 「查→處理→寫」三步須原子，否則仍有縫；TTL 太短會放過遲到重複 |
| 可重放（狀態收斂） | 整段重放收斂到同態 | event sourcing、reduce 型管線 | 副作用（發信、扣款）不會因「結果相同」就只發一次 |
| 副作用 + 標記同交易 | 業務與「已處理」同生同滅 | 副作用落在同一個 DB | 跨 DB／跨服務就退化成 dual-write 問題（見領域 L） |

### 何時需要

只要傳輸是 at-least-once（多數情況），消費端就**一定**要選上面至少一招。選哪招的判準：

- **有自然唯一鍵** → 優先唯一約束，最省事最可靠。
- **操作能寫成設定目標態** → 優先冪等操作，連去重表都省了。
- **操作是累加或呼叫外部副作用、又無自然鍵** → 去重表 + 顯式冪等鍵。
- **副作用落在同一個 DB** → 把它和「已處理標記」綁進同交易。

### 常見誤解與陷阱

- **「冪等＝去重」混為一談**——冪等是**操作的數學性質**（f(f(x))=f(x)），去重是**外圍擋掉重複的機制**。你可以用去重表讓一個不冪等的操作對外表現得像冪等，但它本身仍不冪等。
- **「查了去重表沒有，就放心處理」卻沒上鎖**——「查→沒有→處理」之間若有第二個 worker 也在查，兩個都查到「沒有」、兩個都處理。去重的「查與寫」必須原子（唯一約束或 `INSERT ... ON CONFLICT` 一步到位），否則去重本身有 race（見去重 dedup 的並發陷阱）。
- **把「回應失敗」一律當「沒做」而重試**——外部 API 回 500 或逾時，可能是「真的沒做」也可能是「做了但回應丟了」。盲目重試非冪等操作＝可能做兩次。這正是冪等鍵要由呼叫端帶、讓被呼叫端去重的理由。

**Worked example**：一張 `payments` 表，業務鍵是 `order_id`。即使支付事件被投遞三次，只要 `UNIQUE(order_id)` 存在，第二、三次 `INSERT` 都撞約束失敗；消費者把「unique violation」解讀為「這筆已處理過」並 ack 掉，最終 `payments` 裡只有一列。零去重表、零鎖，靠資料庫的唯一約束就擋掉了 at-least-once 的全部重複。

### 延伸閱讀

- Designing robust and predictable APIs with idempotency（Stripe Engineering）：https://stripe.com/blog/idempotency
- Implementing Stripe-like Idempotency Keys in Postgres（brandur.org）：https://brandur.org/idempotency-keys
- Apache Kafka — Message Delivery Semantics（官方文件）：https://kafka.apache.org/documentation/#semantics

## exactly-once 的真相

### 定義與原理

「exactly-once」是分散式系統裡最被誤用的詞。要拆清楚，先把它劈成兩半：

- **exactly-once delivery（剛好投遞一次）**：在不可靠網路上**不可能**。這是兩將軍問題（Two Generals Problem）的直接推論——任一方都無法確知對方是否收到自己最後一則訊息，要確認就得確認的確認，無窮回歸。沒有任何協定能在有限訊息內讓雙方達成「都確定對方收到了」的共同知識。
- **exactly-once processing（剛好處理一次的效果）**：**可能**，但它不是某種神奇的單次投遞，而是 **at-least-once 投遞 + 消費端去重/冪等** 的合成結果。訊息可能投來三次，但對系統狀態的**淨影響**恰好一次。

所以真相一句話：**沒有 exactly-once delivery，只有「at-least-once delivery + effectively-once processing」。** 任何號稱 exactly-once 的產品，拆開都是這個組合，差別只在「去重做在哪一層、你能不能信」。

### 解法空間

達成 effectively-once processing 的辦法（即「在 at-least-once 之上補去重」的各種落點）：

- **broker 內建去重**：broker 在它的邊界內替你去重。SQS FIFO 在 5 分鐘去重視窗內、對同一 `MessageDeduplicationId` 只投一次（2026-06）；Kafka 的冪等生產者給每個 producer 一個 PID、對每個 partition 維護遞增序號，重送的訊息因序號重複被 broker 直接丟棄。
- **broker 交易 + 消費端隔離**：Kafka 交易把「讀-處理-寫」綁成原子單元，配 `read_committed` 消費者只讀已提交的訊息，達成 stream 處理鏈內的 EOS（2026-06）。但這只在 Kafka 自家 topic 之間成立。
- **消費端自管去重**：broker 給 at-least-once，去重邏輯由你在消費端用冪等鍵/去重表/唯一約束做（見「冪等」「去重」）。最通用、跨任何 broker，但要自己保證原子性。
- **副作用接收端去重**：去重做在最終的副作用端（如支付閘道用你帶的冪等鍵去重），整條鏈即使每段都重投，最終那一次扣款仍只發生一次。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| SQS FIFO 去重視窗 | 5 分鐘內同 dedup id 只投一次 | 同佇列、重複間隔 < 5 分 | 超過 5 分視窗的重複擋不住；只在 SQS 邊界內 |
| Kafka 冪等生產者 | 同 producer 對同 partition 不寫重複 | 生產者重試導致的重複 | 跨 producer session／跨 partition 不保證，需開交易 |
| Kafka 交易 + read_committed | topic 間 read-process-write 原子 | Kafka Streams 處理鏈 | 出了 Kafka（呼叫外部 API、寫外部 DB）即失效 |
| 消費端去重表/冪等鍵 | 端到端 effectively-once | 跨任意 broker、含外部副作用 | 自管原子性與 TTL；最通用但最費工 |

### 何時需要

- **重複會損失金錢/破壞不變量** → 需要 effectively-once，且**必須一路做到副作用端**。光靠 broker 的內建 exactly-once 不夠，因為副作用通常在 broker 之外。
- **全鏈都在單一 broker 內（如純 Kafka Streams 拓樸）** → 可直接吃 broker 的交易型 EOS，省下自管去重。
- **重複可容忍** → 別碰 exactly-once，留在 at-least-once，把省下的延遲與吞吐拿去做別的。

### 常見誤解與陷阱

- **把 broker 行銷的「exactly-once」當成「我什麼都不用做」**——它幾乎總是限定在「broker 自己的邊界內」。你的消費者一旦對外做副作用，保證就斷在邊界上。
- **以為 exactly-once delivery 真的存在**——不存在，這是定理級的不可能。看到產品文件寫 exactly-once，要追問「是 delivery 還是 processing、邊界畫在哪」。
- **混淆「冪等生產者」與「跨重啟去重」**——Kafka 的冪等生產者在**單一 producer session 內**對單一 partition 去重；producer 重啟換了 PID，或寫到多個 partition 當一個邏輯單元，就得升級到交易，光靠冪等生產者不夠。
- **用 effectively-once 當藉口跳過對帳**——再嚴謹的去重也有視窗、有故障窗口。金流場景仍需獨立的對帳機制兜底（見 reconciliation，領域 L）。

**Worked example**：一筆扣款訊息被 SQS 投了兩次。若兩次間隔 30 秒、且生產時帶了相同 `MessageDeduplicationId`，SQS FIFO 在 5 分鐘視窗內擋掉第二次——broker 層 effectively-once 成立。但若這兩次間隔 6 分鐘（例如毒訊息進 DLQ、人工 6 分鐘後重放），就超出視窗、第二次會真的投達；此時唯一防線是消費端用 `order_id` 的唯一約束擋第二次扣款。這說明 broker 去重只是第一層，跨越其視窗/邊界的重複，仍要消費端自己擋。

### 延伸閱讀

- The Two Generals' Problem（Wikipedia 條目，附原始推論）：https://en.wikipedia.org/wiki/Two_Generals%27_Problem
- Exactly-Once Semantics Are Possible: Here's How Apache Kafka Does It（Confluent）：https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-kafka-does-it/
- Apache Kafka — Message Delivery Semantics（官方文件）：https://kafka.apache.org/documentation/#semantics

## 冪等 idempotency

### 定義與原理

冪等（idempotency）的數學定義很短：對操作 f，`f(f(x)) = f(x)`——做一次和做很多次，結果（系統狀態）相同。HTTP 規格早就把這寫進方法語意：`GET`／`PUT`／`DELETE` 被定義為冪等，`POST` 不是。冪等不是「不報錯」，而是「重複執行不改變淨效果」。

天生冪等 vs 天生不冪等：

- **冪等**：`SET status = 'shipped'`、`PUT /users/42 {name:'Alice'}`、`DELETE /orders/7`——它們設定的是**目標狀態**，重放只是把狀態再設到同一個值。
- **不冪等**：`balance = balance - 10`、`counter++`、無唯一鍵的 `INSERT INTO logs ...`、`POST /charges`（每次都建一筆新的）——它們是**相對當前狀態的累加或新建**，做兩次就是兩倍。（`INSERT` 的冪等性其實取決於有無唯一鍵：裸 `INSERT` 不冪等，帶 `UNIQUE`／`ON CONFLICT` 後重複插入會被擋、對外表現為冪等，與下文「唯一約束擋重」呼應。）

不冪等的操作要在 at-least-once 下安全，通用解是**冪等鍵（idempotency key）**：呼叫端為「同一個邏輯操作」產生一個唯一鍵，被呼叫端用這個鍵記住「這個操作我做過了、結果是什麼」，重送同鍵就回放上次的結果、不再重做。這把「不冪等的操作」包裝成「對外冪等的端點」。

### 解法空間

讓一個操作對外冪等的辦法：

- **重寫成設定目標態**：能改就改。把 `balance -= 10` 改成「依事件序列算出應有餘額再 `SET`」（需狀態機/event sourcing 配合，見領域 K）。
- **冪等鍵 + 結果快取**：呼叫端帶 `Idempotency-Key`，server 第一次處理後把「狀態碼 + 回應 body」存起來綁這把鍵；重送同鍵直接回放存好的回應，連業務邏輯都不重跑。這是 Stripe 等支付 API 的標準做法。
- **唯一約束當冪等閘**：用業務鍵或冪等鍵在 DB 加 `UNIQUE`，重複請求撞約束 → 視為已處理（見「at-least-once 與重複處理」）。
- **conditional write / CAS**：帶版本號或 ETag 的條件更新，只在「狀態還是先前讀到的那個」時才寫，重放因版本已變而落空（見樂觀並發控制，領域 B）。

**冪等鍵生命週期**（這條是本書冪等的 owning 落點，講清楚四個階段）：

```
# 示意，非可執行
1. CREATE  client 產生 key（建議 V4 UUID 或足夠亂度的隨機字串），
           綁定「一個邏輯操作」，放進 Idempotency-Key header。
2. CLAIM   server 第一次見到 key：原子地 INSERT 一筆「處理中」記錄
           （唯一約束擋並發重入），開始處理。
3. STORE   處理完成：把 (status_code, response_body) 連同 key 落地。
           關鍵——成功與失敗都要存，這樣重送會拿到一致結果。
4. EXPIRE  key 過 TTL 後清除（Stripe 為 24 小時，2026-06）。
           TTL 內重送回放結果；TTL 外視為新請求。
```

**client vs server 的責任分工**：呼叫端（client）負責**產生並在重試時沿用同一把鍵**——關鍵是「同一個邏輯操作的所有重試用同一把鍵，不同操作用不同鍵」。被呼叫端（server）負責**用這把鍵去重、儲存結果、設定 TTL、並校驗參數一致**（同鍵但 body 不同要報錯，避免誤用）。client 換鍵或 server 不去重，任一方失職，冪等就破。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 重寫成設定目標態 | 操作天生冪等、零額外狀態 | 狀態可由輸入算出 | 累加型、外部副作用型改不動 |
| 冪等鍵 + 結果快取 | 同鍵重送回放同結果（含錯誤） | 支付、建單等有副作用的 POST | 須存成功與失敗；TTL 要涵蓋重試窗；參數變要報錯 |
| 唯一約束當閘 | 重複落地被 DB 拒 | 有唯一業務鍵 | 撞約束須當「已處理」、別當失敗 |
| conditional write / CAS | 只在版本符時才生效 | 樂觀並發、版本化資源 | 重放會「失敗」，呼叫端要能解讀為「已被處理」 |

### 何時需要

- **操作有副作用且傳輸是 at-least-once** → 一定要冪等，否則重複＝重複扣款/重複發貨。
- **對外提供寫 API（尤其 POST）** → 提供 `Idempotency-Key` 是專業 API 的基本盤，讓呼叫端能安全重試。
- **純讀、或操作天生冪等（PUT 設定值）** → 不必額外做冪等鍵，本來就安全。
- **內部一次性、絕不重試的批次** → 過度設計，別硬加冪等層。

### 常見誤解與陷阱

- **「我的端點是 PUT 所以一定冪等」**——HTTP 方法的冪等是**規格約定**，不是你實作自動滿足的。若你的 `PUT` 內部偷做了 `audit_count++` 之類累加，它就不冪等了。方法名是承諾，實作要兌現。
- **冪等鍵只存「成功」結果**——若第一次處理失敗（如 500），沒存結果，重送會重跑業務邏輯，可能這次成功但與「上次到底做了沒」狀態不一致。Stripe 的做法是**成功與失敗都存**，重送一律回放第一次的結果。
- **TTL 設太短**——重複可能在 TTL 之外才到（DLQ 重放、慢重投）。TTL 必須涵蓋你系統最壞的重試/重投窗口，否則去重視窗一過，冪等就形同虛設。
- **「CLAIM 不原子」**——兩個帶同鍵的請求同時到、都查到「沒處理過」、都開始處理。CLAIM 那步必須靠唯一約束或原子 `INSERT` 一步擋掉並發重入，否則冪等鍵自己有 race。
- **把冪等鍵和業務鍵混用**——冪等鍵是「這次請求」的去重鍵，業務鍵（order_id）是「這個實體」的身分。同一筆訂單的「建立」和「取消」是兩個操作、該用兩把冪等鍵，別共用。

**Worked example**：支付 API 收到帶 `Idempotency-Key: 7f3a...` 的建單請求，第一次處理成功、回 `201` 並把「狀態碼 201 + 回應 body」綁這把鍵存 24 小時。客戶端因連線逾時（其實 server 已成功、只是回應丟了）用**同一把鍵**重送——server 查到鍵存在，直接回放那筆 `201` 與原 body，**業務邏輯一行都沒重跑**，所以只建了一張單、只扣一次款。若客戶端這次換了把新鍵重送，server 會當成全新請求 → 建出第二張單。「重試沿用同鍵」是整個機制能成立的前提。

### 延伸閱讀

- RFC 9110 §9.2.2 Idempotent Methods（HTTP 語意，IETF）：https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods
- Stripe API — Idempotent requests（官方文件）：https://docs.stripe.com/api/idempotent_requests
- IETF draft — The Idempotency-Key HTTP Header Field：https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/

## 去重 dedup

### 定義與原理

去重（dedup）是「在 at-least-once 之上，外圍擋掉重複訊息」的機制。它和冪等的分工：冪等改的是**操作本身的性質**，去重不碰操作、而是在操作前**判斷「這筆我見過嗎」**，見過就跳過。去重讓一個不冪等的操作對外表現得像只執行一次。

任何去重方案都要回答三個問題，這三個問題構成去重的三個軸：

- **key（去重鍵）**：用什麼判斷兩筆是「同一筆」？訊息 id、業務自然鍵（order_id）、或內容雜湊（content-based，對 body 取 SHA-256）。鍵選錯——太粗會誤殺不同訊息，太細會放過真重複。
- **window（去重視窗）**：記住「見過」這件事記多久？永久（成本爆炸）、固定 TTL（如 SQS FIFO 的 5 分鐘）、或滑動視窗。視窗決定了「能擋住間隔多久的重複」。
- **store（去重儲存）**：「見過的鍵」存哪？記憶體（快但重啟即失憶、跨節點不共享）、Redis（共享、可設 TTL）、或關聯式 DB 的唯一約束（持久、原子）。store 決定了去重的可靠性與並發正確性。

### 解法空間

按三軸的不同組合，去重落成幾種典型做法：

- **DB 唯一約束去重**（key=業務鍵，window=永久，store=DB）：對自然鍵加 `UNIQUE`，重複插入撞約束。最可靠、原子、不需額外清理，但鍵必須持久存在。
- **去重表 + TTL**（key=訊息 id/冪等鍵，window=TTL，store=DB/Redis）：另開一張「已見鍵」表，處理前 `INSERT ... ON CONFLICT DO NOTHING`，過期自動清。通用，但要管 TTL 與清理。
- **broker 內建去重**（key=dedup id，window=固定，store=broker 內部）：SQS FIFO 5 分鐘視窗、Kafka 冪等生產者的 PID+序號。零自管，但只在 broker 邊界與視窗內。
- **機率型去重**（key=雜湊，window=滑動，store=Bloom filter）：用 Bloom filter 記「可能見過」，省記憶體但有偽陽（可能誤判「沒見過的」為「見過」而漏處理）。只適合「漏掉個別重複可容忍」的場景。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| DB 唯一約束 | 持久、原子、永久去重 | 有自然唯一鍵 | 撞約束須當「已處理」；鍵須持久 |
| 去重表 + TTL（Redis/DB） | 視窗內同鍵只處理一次 | 無自然鍵、需顯式鍵 | 「查+寫」須原子；TTL 須涵蓋最壞重投窗 |
| SQS FIFO 內建（2026-06） | 5 分鐘視窗內去重 | 同佇列、近距重複 | 跨 5 分鐘、跨佇列失效 |
| Bloom filter | 省記憶體的近似去重 | 海量、可容忍偶爾漏 | 偽陽會讓真實訊息被誤當重複而漏掉 |

### 何時需要

- **操作改不成冪等、又無法靠唯一約束** → 用去重表 + 顯式冪等鍵。
- **有自然唯一鍵** → 直接唯一約束，是最省事的去重，連去重表都免。
- **重複幾乎只在短時間內成簇出現（生產者重試造成）** → broker 內建的短視窗去重就夠，別自建。
- **狀態算得出來、整段可重放收斂** → 用可重放設計（見「at-least-once 與重複處理」），可能根本不需要去重表。

### 常見誤解與陷阱

- **「查→處理→寫去重表」三步非原子**——這是去重最經典的 race：兩個 worker 同時查、都查到「沒見過」、都處理。正解是把「查與寫」壓成一步原子操作——`INSERT ... ON CONFLICT DO NOTHING` 或 `SET key NX`（Redis）的回傳值直接告訴你「是不是第一個插進去的」，是才處理，否則跳過。別先 `SELECT` 再 `INSERT`。
- **TTL 短於重投窗**——去重視窗 5 分鐘，但 broker 的最大重投延遲、DLQ 人工重放可能跨數小時。視窗一過，那筆「其實見過」的訊息被當新的處理。TTL 必須 ≥ 系統最壞重投/重放間隔。
- **去重存在記憶體裡**——程式重啟、節點崩潰，「見過」的記錄全沒了，重啟後第一波重複全部漏網；多節點下各節點記憶體不共享，A 節點去重的鍵 B 節點不認得。需共享、持久的 store。
- **content-based 去重鍵的範圍踩雷**——SQS content-based dedup 對 message body 取 SHA-256、但**不含 message attributes**（2026-06）。若兩筆 body 相同、只有 attribute 不同（如不同的 trace id），會被誤判為重複而擋掉第二筆。內容雜湊去重要確認雜湊涵蓋了所有「區分兩筆訊息」的欄位。
- **以為 broker 去重就免了消費端去重**——broker 去重只在它的視窗與邊界內。跨視窗、跨 broker、或消費者在 ack 前崩潰造成的重做，仍要消費端自己擋。

**Worked example**：一條訊息因生產者重試被送進去重表三次，去重鍵＝訊息的冪等鍵。消費者用 `INSERT INTO processed_ids(key) VALUES (:k) ON CONFLICT DO NOTHING RETURNING key`：第一次回傳該 key（插入成功）→ 繼續處理；第二、三次 `RETURNING` 為空（衝突、沒插入）→ 直接 ack 跳過。即使三筆併發抵達，資料庫的唯一約束保證只有一筆能插入成功，去重的原子性由 DB 兜底，消費端不需自己上鎖。`processed_ids` 設 TTL（如 7 天）定期清，涵蓋最壞重投窗即可。

### 延伸閱讀

- Amazon SQS — Using the message deduplication ID（官方文件）：https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html
- Apache Kafka — Idempotent Producer（KIP-98 設計文件）：https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging
- Bloom Filters by Example（資料結構機制）：https://llimllib.github.io/bloomfilter-tutorial/
