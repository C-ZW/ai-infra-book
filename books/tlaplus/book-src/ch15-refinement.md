# ch15 — Refinement：實作蘊涵規格

> **本章解決什麼問題**：ch14 教你證「spec 滿足性質」；但全書還欠著另一種主張的證法——「這個系統**實作了**那個規格」。ch11 的 `THEOREM TPSpec => TC!TCSpec`、ch12 的 `THEOREM Spec => V!Spec`，你都只是看見，還沒拆開。本章把它做成機械：規格與實作是同一種東西（都是時序公式），「實作正確」是一條貨真價實的蘊涵；驗它的工具叫 refinement mapping——把實作狀態映到規格狀態、把每個實作步映成規格步**或 stuttering**。ch06 你簽下的 stuttering 條款，今天到期。收官之作：把「at-least-once＋dedup 實作了 exactly-once」這句你講過無數次的黑話，寫成定理。ch16 會讓機器來查這些證明義務。

## 從你已知的出發

你做過這樣的重構：結算 pipeline 的 dedup 原本是 MySQL 的唯一鍵，你把它換成 Redis SETNX 加 TTL 補償；或是把直連的入帳呼叫拆成佇列加 consumer。PR 描述裡你寫了那句行話：「**對外行為不變**」。reviewer 信了，上線也沒出事。但如果有人逼問——「對外行為」的精確定義是什麼？「不變」拿什麼證？——你大概只能指著回歸測試說：你看，全綠。

ch01 就把這條路堵死過：測試是抽樣，不是全稱。本章給你第二條路。「對外行為」可以是一條公式——一份只談你在乎的變數的抽象 spec；「不變」可以是一條定理——新舊實作都蘊涵它。介面與實作的契約、Liskov 替換的直覺（子型別可以無痛頂替父型別出現的位置），在 TLA 的世界裡全部塌縮成同一個記號：⇒。

另一句你常講的黑話這章也要清算。「SQS 是 at-least-once，但我們有 idempotency key，所以整體是 exactly-once。」這句話在 design review 裡人人點頭，可它的邏輯地位是什麼？口號？經驗法則？本章結束時它是：**SettlementV1 的每一條合法行為，都是理想 exactly-once 帳本允許的行為**——一條可以逐步驗證的蘊涵式。

最後是還債。ch06 講 stuttering 時明寫「這是 ch15 的伏筆」；ch11 的兩層、ch12 的三層樓，每層之間都吊著一條沒拆的 THEOREM。今天全部兌現。

## 規格與實作是同一種東西

先把世界觀說死。ch02 起我們就說：一份 spec ＝ 一個允許的行為集合；ch06 把它寫成公式 Init ∧ □[Next]_vars。注意這個定義裡**沒有出現「規格」與「實作」的區分**——TCommit 是一條時序公式，TwoPhase 也是；Consensus 是，Paxos 也是；它們是同一種數學物件，差別只在粗細：粗的變數少、允許的行為多；細的變數多、允許的行為少。

於是「I 實作了 S」有了唯一合理的定義：**I 的每一條行為，S 都允許**。行為集合的 ⊆，在邏輯上就是蘊涵——一條公式蘊涵另一條，若且唯若滿足前者的行為都滿足後者：

```text
所有可能的 behavior
┌───────────────────────────────────────┐
│  S 允許的行為                         │
│                                       │
│      ┌─────────────────────┐          │
│      │  I 的行為           │          │
│      └─────────────────────┘          │
│                                       │
└───────────────────────────────────────┘
```

I ⇒ S，「實作正確」＝一條蘊涵式。沒有專門的「符合性檢查器」、沒有另一套理論——就是你 ch03 學的那個 ⇒，搬到時序公式上。

這個定義能成立，全靠 ch06 那個當時看起來像漏洞的設計。實作幾乎總是比規格多變數、多步驟：TwoPhase 比 TCommit 多了 tmState、tmPrepared、msgs，它的大多數步——TM 收訊息、TM 廣播——根本不碰 rmState。如果 TCommit 的公式要求「每一步 rmState 都得照 TCNext 動」，蘊涵當場死亡。但 TCSpec 寫的是 □[TCNext]_rmState：每一步，**要嘛是 TCNext、要嘛 rmState 不動**。TM 的忙碌，在只看 rmState 的觀察者眼裡是靜止——被 stuttering 條款接住。ch06 的時鐘寓言（時分時鐘實作小時鐘）就是這件事的最小版本；ch11 那張對照表是它的中型版本；本章要給你通用的機械。

還有一個推論值得先記下：refinement 是**遞移**的。Paxos ⇒ Voting、Voting ⇒ Consensus，所以 Paxos ⇒ Consensus——三層樓靠兩條蘊涵焊死，每層只需要對它的直接上層負責。這就是分層開發在邏輯裡的長相：規格也是某人的實作，實作也是某人的規格。

## Refinement mapping：把行為層的主張化約成逐步檢查

I ⇒ S 是行為層的主張——量化在所有（可能無限長的）行為上，沒辦法逐條檢查。ch05 你遇過一模一樣的困境：「所有可達狀態都滿足 Inv」也量化在無限多條路徑上，解法是歸納——把它化約成「起點成立＋每步保持」兩個局部義務。refinement mapping 對 I ⇒ S 做的是同一件事。**inductive invariant 之於 □Inv，恰如 refinement mapping 之於 I ⇒ S**：都是把行為層的全稱主張，化約成一步之內查得完的義務。

設規格 S 的變數是 y、實作 I 的變數是 x（各自可以是好幾個）。一個 **refinement mapping** 是一組**狀態函數** ȳ ＝ f(x)：用實作的變數，算出每個規格變數「此刻應該是什麼值」。直覺：f 是一副眼鏡，戴上它看實作，看到的是規格的世界。三個義務：

- ⟨1⟩1 **起點**：I 的每個初始狀態，戴上眼鏡滿足 S 的 Init。
- ⟨1⟩2 **逐步**：I 的每一步（在可達狀態上，所以前件帶著 Inv），戴上眼鏡是 S 的一步、**或 S 的 stuttering**（ȳ 沒動）。
- ⟨1⟩3 **Inv 本身**：Spec_I ⇒ □Inv——⟨1⟩2 用到的可達性事實要另案證明（ch14 的手藝）。

三個義務都過，I ⇒ S 成立：沿著 I 的任何一條行為做歸納（ch05），映出來的狀態序列起點合法、每步合法，就是 S 的一條行為。

畫出來。拿 ch08 那條最危險的 trace（s₂ → s₃ 正是「入帳之後、確認之前 crash」）的中段，戴上稍後會正式定義的眼鏡 f：

```text
抽象層   T1 ─PayOnce(m1)─→ T2 ============== T2 ============== T2
         ▲                 ▲                 ▲                 ▲
         │f                │f                │f                │f
實作層   s1 ──Credit(c1)─→ s2 ──Crash(c1)──→ s3 ─Fetch(c2,m1)→ s4
```

（═ 表示抽象狀態原地不動，即 stuttering。）實作走了三步驚心動魄的災難劇，抽象層只看到一件事發生：m1 被入帳了一次。Crash、redelivery、重複領取——全是分針。**stuttering 不是規格的寬容，是抽象的代價結構：你選擇不看的東西，必須有地方放。**ch06 的本票，兌現在這張圖的每一根 ▲ 上。

一個此刻就要立的警告，後面會反覆回來敲：**蘊涵是數學，mapping 是主張。**f 把規格的 y 接到實作的哪個東西上，是你的建模決定；接錯了（或接到常數上），定理可以為真而毫無意義。「陷阱與防禦」算總帳。

## INSTANCE：代換就是全部的語意

TLA+ 裡寫下 refinement mapping 的語法是 INSTANCE。Specifying Systems 第 4 章有一節的標題把語意說死了：*Instantiation Is Substitution*——引入模組＝做代換，沒有更多了。

從 ch11 已引的原文開始逐字拆：

```tla
TC == INSTANCE TCommit

THEOREM TPSpec => TC!TCSpec
```

第一行做三件事。其一，把 TCommit 模組的**每一個定義**搬進來，名字前掛 `TC!`：TC!TCInit、TC!TCNext、TC!TCSpec、TC!TCConsistent……（前綴就是 TwoPhase 原文註解說的避免撞名）。其二，TCommit 有兩個參數——CONSTANT RM 與 VARIABLE rmState——每個參數都必須給代換。其三，**沒寫 WITH 的參數，隱式用當前模組的同名符號代換**：TwoPhase 自己有 RM 和 rmState，所以 TC!TCSpec 就是「把 TCommit 全文裡的 rmState 換成 TwoPhase 的 rmState」之後的 TCSpec——ch11 說的「用 TwoPhase 的 rmState 講出來的 TCSpec」，一字不差。

所以這裡的 refinement mapping 是最便宜的一種：**投影**。規格變數 rmState 的眼鏡函數就是實作的 rmState 本身（恆等），多出來的 tmState、tmPrepared、msgs 被遮掉。便宜，但義務一個不少——下一節逐案清算。

要代換成別的東西，用 WITH：

```tla
M == INSTANCE SomeSpec WITH y <- expr
```

expr 可以是任何狀態函數——不只變數，**算出來的東西也行**。這正是 ch12 結尾那兩行的玩法（原文照引）：

```tla
votes == [a \in Acceptor |->
           {<<m.bal, m.val>> : m \in {mm \in msgs: /\ mm.type = "2b"
                                                   /\ mm.acc = a }}]

V == INSTANCE Voting

THEOREM Spec => V!Spec
```

Voting 的參數變數是 votes 與 maxBal。maxBal 同名，隱式恆等；votes 在 Paxos 模組裡**不是變數，是定義**——從 msgs 裡撈出所有 2b 訊息重建的投票記錄——而隱式代換規則「用當前模組的同名符號」照樣適用：V!Spec 就是「votes 一詞處處讀作那個重建式」的 Voting spec。ch12 說它是「refinement mapping 的雛形」；現在你知道它不是雛形，**它就是 mapping 本體**：f 把 Paxos 狀態（msgs、maxBal…）映到 Voting 狀態（votes、maxBal）。同一招再往上一層：Voting 裡 `chosen` 是從 votes 定義出來的狀態函數，`C == INSTANCE Consensus` 把 Consensus 的變數 chosen 隱式代換成它，`THEOREM Spec => C!Spec`（2026-06 對照 Voting.tla 原文）。三層樓的每一道焊縫，都是一次代換。

逐動作的對映也順手立起來（對照 Voting.tla 的兩個動作 IncreaseMaxBal 與 VoteFor，2026-06）：Phase1a 與 Phase2a 只動 msgs，votes 與 maxBal 紋風不動——Voting 眼裡是 stuttering；Phase1b(a) 把 maxBal[a] 推高、不投票——映成 IncreaseMaxBal(a, m.bal)；Phase2b(a) 發出 2b、三欄齊更新——映成 VoteFor(a, m.bal, m.val)，而 VoteFor 那條全知 guard（∃ Q : ShowsSafeAt）憑什麼成立？憑可達性事實：2a 訊息存在 ⇒ 發出它時收齊過 quorum 的 1b ⇒ ShowsSafeAt 的證據還躺在 msgs 裡。**ch12 那句「Voting 的 VoteFor 是全知 guard、Paxos 的工作是把全知換成訊息」，refinement 把它從口號變成義務**：每個 Phase2b 步，你都欠一個「訊息證據足以重建全知 guard」的證明。這筆帳跟 ch11 的「對照表沒那麼便宜」是同一筆，記在 ⟨1⟩3。

兩個收尾細節。其一，**prime 怎麼過代換**：ȳ′ 讀作「把 f 的定義式裡每個變數加 prime」——f(x) 在步後狀態的值。其二，**定理跟著搬**：抽象模組裡證過的 THEOREM，代換後仍然是定理（所以 Consensus 層證一次 Cardinality(chosen) ≤ 1，三層樓全體受益）。唯一的著名例外：含 ENABLED 的公式（包括 WF/SF）在代換下不保真——fairness 想跟著 mapping 下樓，得另外論證。這是 liveness refinement 比 safety 難的技術原因之一，本書不深入，先知道地雷在哪。

## 把 ch11 的對照表升格為定理

ch11 給過一張表：TwoPhase 的每種步，在 TCommit 眼裡是什麼。當時的話是「這張表沒有看起來那麼便宜」。現在付錢。義務照上節的三件套，目標：TPSpec ⇒ TC!TCSpec。

先把 ⟨1⟩3 要用的可達性事實列清楚（就是 ch11 題 2(d) 那條鏈的三節；它們對七個動作的歸納證明是 ch14 的正戲，這裡直接取用）：

- **F1**：[type ↦ "Commit"] ∈ msgs ⇒ ∀ rm ∈ RM : rmState[rm] ∈ {"prepared", "committed"}
- **F2**：[type ↦ "Commit"] ∈ msgs ⇒ [type ↦ "Abort"] ∉ msgs
- **F3**：rmState[rm] = "committed" ⇒ [type ↦ "Commit"] ∈ msgs

證明骨架（Inv ≜ TPTypeOK ∧ F1 ∧ F2 ∧ F3）：

⟨1⟩1. **起點**：TPInit ⇒ TC!TCInit。TPInit 的第一個合取 rmState = [rm ∈ RM ↦ "working"] 逐字就是 TCInit。∎

⟨1⟩2. **逐步**：Inv ∧ [TPNext]_⟨rmState, tmState, tmPrepared, msgs⟩ ⇒ [TC!TCNext]_rmState。分案：

  ⟨2⟩1. **stuttering、TMRcvPrepared、TMCommit、TMAbort**：四者都含 UNCHANGED rmState（或 vars 全等）⇒ rmState′ = rmState ⇒ [TC!TCNext]_rmState 的第二個 disjunct。TM 忙它的，小時鐘不動。∎
  ⟨2⟩2. **RMPrepare(r)**：guard rmState[r] = "working" 與效果「r 那格改 "prepared"」逐字等於 TC!Prepare(r)。∎
  ⟨2⟩3. **RMChooseToAbort(r)**：效果是 r 改 "aborted"，候選對映是 TC!Decide(r) 的 abort 分支，需要 rmState[r] ∈ {"working", "prepared"}（guard 給了 "working" ✓）與 notCommitted。反證：若某 rm committed，由 F3 得 Commit ∈ msgs，由 F1 得全員 ∈ {"prepared", "committed"}——與 r 在 "working" 矛盾。故 notCommitted 成立。∎
  ⟨2⟩4. **RMRcvCommitMsg(r)**：guard 給 Commit ∈ msgs，由 F1 知 rmState[r] ∈ {"prepared", "committed"}，分兩案。**案 prepared**：對映 TC!Decide(r) 的 commit 分支，其 guard canCommit ＝「全員 ∈ {"prepared", "committed"}」——正是 F1。✓ **案 committed**：EXCEPT 把 "committed" 蓋寫成 "committed"，rmState′ = rmState——**stuttering**。這就是原文註解那句「同一訊息收第二次無害」在證明裡的著落：**冪等的重複接收，映成規格的原地踏步**。∎
  ⟨2⟩5. **RMRcvAbortMsg(r)**：guard 給 Abort ∈ msgs。先證 notCommitted：若某 rm committed，F3 給 Commit ∈ msgs，F2 給 Abort ∉ msgs——矛盾。再分案：r ∈ {"working", "prepared"} → Decide(r) 的 abort 分支（notCommitted 剛證完）✓；r = "aborted" → 蓋寫同值，stuttering ✓；r = "committed" 已被 notCommitted 排除。∎

⟨1⟩3. TPSpec ⇒ □Inv：見 ch14。⟨1⟩4. 三件套齊 ⇒ TPSpec ⇒ TC!TCSpec。∎

ch11 的擴充版（TMCrash）一行收掉：TMCrash 含 UNCHANGED rmState，落進 ⟨2⟩1——**TM 之死，在問題層眼裡也是 stuttering**，所以 TPCrashSpec ⇒ TC!TCSpec 同樣成立。blocking 傷的是 liveness，refinement（safety 層）毫髮無傷——跟 ch11 手推的結論完全咬合。

回頭看那張表：它一直都是這個證明的目錄，每一格是一個 ⟨2⟩ 案；「沒那麼便宜」的部分就是 F1–F3——**對映表值多少錢，invariant 說了算**。

## Worked example：結算系統收官

現在輪到你的系統。目標：寫一份抽象的 exactly-once 帳本 spec，然後證 SettlementV1（ch08 原文，變數 queue、working、ledger、dedup，動作 Fetch、Credit、Ack、Crash）⇒ 它。

### 第一幕：BOOLEAN 抽象層，與它的盲區

第一直覺：理想的帳本不就是 v0 那種布林表嗎？每則訊息一格，從「未入帳」翻到「已入帳」，至多翻一次：

```tla
\* 第一幕的候選抽象層（最後會被退貨）：ExactlyOnceB
VARIABLE ledger      \* 預期 ledger \in [Msgs -> BOOLEAN]

InitB == ledger = [m \in Msgs |-> FALSE]

PayOnceB(m) == /\ ledger[m] = FALSE
               /\ ledger' = [ledger EXCEPT ![m] = TRUE]
```

v1 的 ledger 是計數（[Msgs → Nat]），型別對不上，隱式代換用不得——這正是 WITH 出場的時刻，**型別轉換必須白紙黑字寫出來**：

```tla
EOB == INSTANCE ExactlyOnceB WITH ledger <- [m \in Msgs |-> ledger[m] >= 1]
```

眼鏡函數：抽象格子為 TRUE ⇔ 實作計數 ≥ 1。驗證義務出乎意料地順：起點（全 0 映成全 FALSE）✓；Fetch、Ack、Crash 不動 ledger → stuttering ✓；Credit 把某格從 k 加到 k+1——k = 0 時 FALSE→TRUE，映成 PayOnceB ✓；k ≥ 1 時 TRUE→TRUE，映成 stuttering ✓。每案都過，THEOREM Spec ⇒ EOB!Spec 成立。

慶祝之前，做 ch08 題 4 教你的那個動作：讓防線承壓。拿 BadCredit 變體（刪掉 `working[c] \notin dedup` 那行 guard 的 v1——ch08 親手示範過它會 double pay）重驗一遍：第一次入帳 0→1 映成 PayOnceB ✓；**第二次入帳 1→2 映成 TRUE→TRUE——stuttering ✓**。全部義務照過。**壞掉的系統，拿到了同一張定理。**

驗屍兩刀。第一刀：Nat→BOOLEAN 的壓扁把「第二次入帳」變成抽象層的不可見事件——ch08 早警告過布林帳本看不見 double pay，這裡它以更陰的形式回魂：**stuttering 既是 refinement 的潤滑劑，也是藏屍處——mapping 壓扁掉的資訊，正是定理看不見的故障**。第二刀更誠實：回看第一幕的驗證過程，**從頭到尾沒有用到 dedup**——k = 0 與 k ≥ 1 的分案對任何系統都成立。一個對 dedup 防線隻字未提的定理，憑什麼宣稱定理化了「dedup 實作 exactly-once」？綠燈，但防線從未承壓（ch08 的劇場道具，定理版）。退貨。

### 第二幕：把抽象層改誠實

病根是抽象層太瞎，藥方是讓它看得見計數。理想帳本自己用 Nat——但它的動作規則保證值永遠只有 0 和 1：

```tla
---------------------------- MODULE ExactlyOnce ----------------------------
EXTENDS Naturals

CONSTANT Msgs

ASSUME Msgs # {}

VARIABLE ledger

TypeOK == ledger \in [Msgs -> Nat]

Init == ledger = [m \in Msgs |-> 0]

PayOnce(m) == /\ ledger[m] = 0
              /\ ledger' = [ledger EXCEPT ![m] = 1]

Next == \E m \in Msgs : PayOnce(m)

Spec == Init /\ [][Next]_ledger

NoDoublePay == \A m \in Msgs : ledger[m] <= 1

THEOREM Spec => []NoDoublePay
==============================================================================
```

十來行，零機制：沒有佇列、沒有 consumer、沒有 crash。每格是一個單向閂——從 0 出發，唯一的動作把 0 扳成 1，扳過就永遠扳不動（guard 死了，只剩 stuttering）。認出來了嗎？**這是 Consensus.tla 的結算版**（ch12 的頂樓：chosen 從 {} 到 {v}，一步定終身）——「定案」與「入帳」是同一個數學形狀。抽象層的 NoDoublePay 直接 inductive：Init 全 0 ✓；PayOnce 只造 1 ✓；TypeOK 注意寫 Nat 而不是 0..1——值域 0..1 是動作**掙來的秩序**，不是型別宣告（ch08 的走私紅線，在抽象層同樣有效）。

mapping 呢？v1 的 ledger 與抽象的 ledger 同名、同型別——隱式代換，恆等眼鏡。在 SettlementV1 末尾加兩行：

```tla
EO == INSTANCE ExactlyOnce

THEOREM Spec => EO!Spec
```

（展開等價於 `INSTANCE ExactlyOnce WITH Msgs <- Msgs, ledger <- ledger`。）**為什麼這個定理不空洞**：恆等 mapping 把抽象帳本接到 v1 的 ledger 本人——也就是你資料庫裡那張下游真的會去讀的表。定理說的是這張表的事，不是某個影子的事。

驗證開始。⟨1⟩3 先行——Credit 案會用到一條可達性事實（dedup 與 ledger 同步）：

Sync ≜ ∀ m ∈ Msgs : ledger[m] = (IF m ∈ dedup THEN 1 ELSE 0)

⟨1⟩1. Init ⇒ Sync：dedup = {} 使 IF 全取 0，ledger 全 0。∎
⟨1⟩2. TypeOK ∧ Sync ∧ Next ⇒ Sync′，分五案：
  ⟨2⟩1. Fetch、Ack、Crash：三者都 UNCHANGED ⟨ledger, dedup⟩，Sync 原封。∎
  ⟨2⟩2. Credit(c)：令 m₀ ≜ working[c]。guard 給 m₀ ≠ "idle"，配 TypeOK 與 ASSUME 的 "idle" ∉ Msgs，得 m₀ ∈ Msgs（那條 ASSUME 又一次自食其力）。guard 給 m₀ ∉ dedup，由 Sync 得 ledger[m₀] = 0。步後：ledger′[m₀] = 0 + 1 = 1 且 m₀ ∈ dedup′ ✓；其餘 m 兩邊都沒動 ✓。∎
  ⟨2⟩3. stuttering：全等。∎
（TypeOK 自身的保持是 ch14 的標準起手式，不重複。Sync 蘊涵 NoDoublePay——ledger[m] 只取 0 或 1。這正是 ch14 為 v1 鍛造的那型「dedup 是 ledger 的影子」事實。）

主菜，逐 action 對映。義務：TypeOK ∧ Sync ∧ [Next]_vars ⇒ [EO!Next]_ledger。

⟨1⟩1. **起點**：v1 的 Init 給 ledger = [m ∈ Msgs ↦ 0]，逐字就是 EO!Init。∎
⟨1⟩2. **Fetch(c, m)**：UNCHANGED ⟨ledger, dedup⟩ ⇒ ledger′ = ledger ⇒ stuttering disjunct。領取訊息，帳本沒動——分針。∎
⟨1⟩3. **Credit(c)**：令 m₀ ≜ working[c] ∈ Msgs（同上）。對映目標：EO!PayOnce(m₀)。
  ⟨2⟩1. guard：EO!PayOnce(m₀) 要求 ledger[m₀] = 0。由 Credit 的 guard m₀ ∉ dedup 與 Sync，成立。**這一步是整個定理的承重點：dedup guard 經由 Sync 換來抽象 guard——防線在證明裡真正承壓了。**
  ⟨2⟩2. 效果：Credit 給 ledger′ = [ledger EXCEPT ![m₀] = @ + 1]，而 @ ＝ ledger[m₀] ＝ 0，故 ledger′ = [ledger EXCEPT ![m₀] = 1]——與 EO!PayOnce(m₀) 的效果逐字相等。
  ⟨2⟩3. 故這一步滿足 EO!PayOnce(m₀) ⇒ EO!Next。∎
⟨1⟩4. **Ack(c)**：UNCHANGED ⟨queue, ledger, dedup⟩ ⇒ stuttering。確認與丟棄重複——分針。∎
⟨1⟩5. **Crash(c)**：UNCHANGED ⟨ledger, dedup⟩ ⇒ stuttering。**連 crash 加 redelivery 都是分針**——理想帳本不知道世上有死亡這回事。∎
⟨1⟩6. **v1 自己的 stuttering**：vars 全等 ⇒ ledger′ = ledger ⇒ stuttering。∎
⟨1⟩7. 起點＋逐步＋□(TypeOK ∧ Sync)，沿行為歸納（ch05）：Spec ⇒ EO!Spec。∎

定理到手，馬上做兩個對照。**其一**，BadCredit 這次逃不掉：取 ch08 那個懸崖狀態（c2 手持 m1、ledger[m1] = 1、m1 ∈ dedup），BadCredit(c2) 走一步，ledger[m1]: 1 → 2。抽象層三個出口逐一驗：EO!PayOnce(m1)？guard 要 ledger[m1] = 0，是 1，死；效果要改成 1，是 2，死。EO!PayOnce(m2)？動錯格子，死。stuttering？ledger 變了，死。**三路全滅——這一步映不出去，蘊涵破裂**。第一幕看不見的屍體，第二幕躺在光天化日之下。**其二**，白拿的紅利：抽象層證過 EO!Spec ⇒ □EO!NoDoublePay，定理過代換保持，而恆等代換下 EO!NoDoublePay 逐字就是 v1 的 NoDoublePay——所以 Spec ⇒ □NoDoublePay **免費掉出來**。refinement 比單條 invariant 說得更多：它鎖死了 ledger 的全部動力學（不減、不跳、每格至多一次跨越），NoDoublePay 只是它的影子之一。

最後，誠實記帳。那句黑話的完整版是兩半：「**至多**一次」是 safety——本章定理；「**至少**一次（終將入帳）」是 liveness——v1 沒有 fairness，AllPaid 不成立（ch08 結尾記過這筆帳），抽象層的 □[Next]_ledger 同樣只是允許清單，從不承諾 PayOnce 真的發生。要補齊，得在兩層各加 fairness、再證 fairness 過 mapping 仍成立——撞上前面說的 ENABLED 代換地雷。所以本章定理的精確名字是：**at-least-once＋dedup 實作了 at-most-once-and-nothing-weird**；exactly 的另一半，掛在 ch07 的帳上。把黑話定理化的最大收穫，往往就是發現黑話原來說了兩件事。

## 找不到 mapping 的時候：auxiliary variables

三個義務裡藏著一個沒明說的限制：f 是**狀態**函數——它只能看實作的現在，看不到過去，更看不到未來。有些 refinement 是真的（行為集合確實 ⊆），mapping 卻不存在，原因恰好兩種。

**實作忘了過去（history variable 補）。**規格的狀態若記著實作已經丟掉的歷史，f 無米可炊。你其實見過近親：TwoPhase 的 msgs 只增不減，本身就像一個內建的 history variable——「誰曾經說過什麼」全部留底，所以 ch11 的 F1–F3 才有得寫。反例也在你家：v1 的 dedup 是集合、ledger 是計數，**誰先入帳的順序**沒有任何變數記得——想證 v1 refine 一份記「入帳序列」的規格，f 就得從不記順序的狀態變出順序，不可能（紙上推演題 3 讓你親手撞牆＋修牆）。修法：給實作加一個只寫不讀的變數（history variable），把缺的歷史記回來——工程版你早就會：為了對帳而加的 audit log 欄位，不影響業務邏輯，只為「事後能回答問題」存在。

**實作還沒決定未來（prophecy variable 補）。**這個方向違反直覺，值得走完最小例子。兩份 spec，外部都只有 out：

```tla
\* SpecL（晚決定）：第二步才現場擲骰子
InitL   == out = << >>
First   == out = << >>   /\ out' = <<"a">>
SecondB == out = <<"a">> /\ out' = <<"a", "b">>
SecondC == out = <<"a">> /\ out' = <<"a", "c">>
SpecL   == InitL /\ [][First \/ SecondB \/ SecondC]_out

\* SpecE（早決定）：第 0 步就在內部變數 d 押好注
InitE   == out = << >> /\ d \in {"b", "c"}
FirstE  == out = << >>   /\ out' = <<"a">>        /\ d' = d
SecondE == out = <<"a">> /\ out' = Append(out, d) /\ d' = d
SpecE   == InitE /\ [][FirstE \/ SecondE]_<<out, d>>
```

兩者的 out 行為集合一模一樣（⟨⟩ → ⟨a⟩ → ⟨a,b⟩ 或 ⟨a,c⟩，外加各處 stuttering），所以「SpecL 實作了把 d 藏起來的 SpecE」直覺上為真。但畫出狀態圖就看到死穴：

```text
SpecL：分岔點是同一個狀態        SpecE：分岔在第 0 步就發生了

 ⟨⟩ ──First──→ ⟨a⟩ ──SecondB──→ ⟨a,b⟩     (⟨⟩, b) ─→ (⟨a⟩, b) ─→ (⟨a,b⟩, b)
                 │
                 └────SecondC──→ ⟨a,c⟩     (⟨⟩, c) ─→ (⟨a⟩, c) ─→ (⟨a,c⟩, c)
```

mapping 必須給出 d̄ ＝ f(out)。SpecL 在 out = ⟨a⟩ 只有**一個**狀態，f 只能押一個值，不妨說 d̄ = "b"。現在看走 SecondC 的那條行為：⟨a⟩ → ⟨a,c⟩ 這一步映過去，SecondE 要求被 append 的字元等於步前的 d̄——是 "b"，實際是 "c"，死；FirstE 不合（out ≠ ⟨⟩），stuttering 不合（out 動了）。**f 被要求在分岔前就知道骰子的點數。**修法：給 SpecL 加 prophecy variable p——Init 時 p ∈ {"b", "c"}，SecondB 加 guard p = "b"、SecondC 加 guard p = "c"。p 把「未來的決定」搬進現在的狀態（⟨a⟩ 裂成兩個狀態），而對 out 而言行為集合分毫未變——每條原行為都有唯一一種 p 的填法：照它未來真做的事填。在 spec 的數學裡，預知未來是合法的建構。然後 d̄ ≜ p，義務全過。

兩個收尾。其一，「把 d 藏起來」嚴格說要用一個本書沒教的算子：時序存在量詞 ∃∃（ASCII `\EE`），∃∃ d : SpecE 的行為集合＝「存在某條 d 軌跡使 SpecE 成立」的 out 行為。本章其他例子（TCommit、Consensus、ExactlyOnce）的變數全是對外的，所以 THEOREM 都不需要它；但 auxiliary variables 的完整理論離不開 hiding，入口見延伸閱讀。其二，理論的天花板：Abadi 與 Lamport 在〈The Existence of Refinement Mappings〉證明了**完備性定理**——只要 refinement 在行為層為真，加上 history 與 prophecy variables 之後 mapping 必定存在（需三個技術條件：實作 machine closed、規格的不可見非決定性有限、規格內部連續；條件不滿足時 mapping 可以真的不存在——深水區到此為止，本書不證）。這篇 1988 年的論文拿了 LICS Test of Time Award；而「怎麼在 TLA+ 裡實際把這些變數加進 spec」有一份手把手的教材：Lamport 與 Merz 的〈Auxiliary Variables in TLA+〉，連 stuttering variable（第三種：給實作墊步數的）都教。皆見延伸閱讀。

## 重構的安全證書

把鏡頭拉回你的日常。「對外行為不變的重構」現在有了精確版本：**新舊實作 refine 同一份抽象 spec**。抽象 spec 是「對外行為」這四個字的數學名字；refinement 定理是你貼在 PR 上的安全證書。把 v1 的 dedup 從 MySQL 唯一鍵換成 Redis SETNX、把 SQS 換成 Kafka——只要新系統仍然 ⇒ ExactlyOnce，下游連一個字都不用改，而「不用改」這次有證據。反過來，找不到 mapping、又加不出合理的 aux variable，往往是在告訴你：這次改動**不是**重構，外部行為真的變了——這個訊號比回歸測試靈敏得多。

什麼時候值得付這筆錢？我的判準：(1) 系統有自然的「需求／機制」兩層，且需求層能用一兩個變數寫完（TCommit、Consensus、ExactlyOnce 都做到了）——寫不出小的抽象層，多半表示你還沒想清楚對外承諾是什麼；(2) 你正要做元件替換或協議升級，需要「外部行為」的可對齊定義；(3) 協議本身是階梯式設計（Paxos 三層）。不滿足這些，一層 spec 加 invariant（ch14）就夠——mapping 的成本是 invariant 那套再來一遍，別為了儀式感付雙倍。

## 陷阱與防禦

| 故障模式 | 它怎麼給你假安全感 | 怎麼自我察覺 |
|---|---|---|
| 空實作通過 | 永遠 stuttering 的系統 refine 一切（起點合法的）safety spec——「我們的新版通過了 refinement 檢查」可能只證明它什麼都沒做 | safety refinement 從不要求事情發生。問：哪條 liveness 性質排除了空實作？沒有就去 ch07 補 fairness |
| mapping 與現實脫鉤 | 把抽象變數映到常數或無關欄位（ledger ↦ 恆 FALSE），義務全過、定理全真、意義全無 | 檢查你在乎的對外變數：mapping 是恆等或誠實的觀測函數嗎？你最在乎的實作動作映成了規格動作、還是被 stuttering 吞了？ |
| 型別壓扁丟資訊 | Nat→BOOLEAN 之後，double pay 映成 TRUE→TRUE 的 stuttering——壞系統與好系統拿同一張定理（本章第一幕） | 對每個最怕的故障 trace 手算抽象投影：抽象層**看得見**它嗎？再檢查證明有沒有用到防線（沒用到 dedup 的定理保護不了 dedup） |
| 逐步義務忘了帶 Inv | 在不可達狀態上驗 mapping：要嘛假卡住（ledger = 5 映不出去，誤判 mapping 錯），要嘛假通過 | 義務寫成 Inv ∧ [Next]_x ⇒ …；卡住先問 ch14 的老問題：這個壞前驅可達嗎？ |
| 隱式代換型別錯位 | INSTANCE 同名隱式代換把 Nat 塞進期待 BOOLEAN 的模組——TLA+ 無型別，不在門口報錯，公式安靜地變假或 vacuous 地真 | 每個 INSTANCE 逐參數列代換表（含隱式的）；型別不同必用 WITH 明寫轉換函數 |
| 以為 liveness 自動繼承 | safety refinement 證完就宣稱 AllPaid 也有了——抽象層沒承諾過，或實作的 fairness 沒能過代換（ENABLED 不保真） | 逐條列「這個定理帶過去了什麼」；fairness 的搬運另案論證，搬不動就誠實標注 |

## 紙上推演

### 題 1：第一張眼鏡（[15 分鐘] ★）

抽象 spec OneShot 與實作 Pipeline：

```tla
\* OneShot：一件事，做一次
VARIABLE done
InitO == done = FALSE
Fire  == done = FALSE /\ done' = TRUE
SpecO == InitO /\ [][Fire]_done

\* Pipeline：三段式部署
VARIABLE pc
InitP  == pc = "build"
Build  == pc = "build"  /\ pc' = "test"
Test   == pc = "test"   /\ pc' = "deploy"
Deploy == pc = "deploy" /\ pc' = "ok"
SpecP  == InitP /\ [][Build \/ Test \/ Deploy]_pc
```

寫出 INSTANCE 句與 mapping，逐 action 驗證 SpecP ⇒ 實例化後的 SpecO。哪些步是分針？這題需要可達性 invariant 嗎、為什麼？

### 推演解答

mapping：done 映成「pc 到站了沒」。

```tla
OS == INSTANCE OneShot WITH done <- (pc = "ok")

THEOREM SpecP => OS!Spec
```

逐案：起點——pc = "build" ⇒ (pc = "ok") = FALSE ＝ InitO ✓。Build：pc 從 "build" 到 "test"，眼鏡值 FALSE→FALSE——stuttering ✓。Test：FALSE→FALSE，stuttering ✓。Deploy：guard pc = "deploy" 給步前眼鏡值 FALSE，步後 pc′ = "ok" 給 TRUE——FALSE→TRUE 逐字滿足 Fire ✓。Pipeline 自己的 stuttering：pc 不動 ⇒ 眼鏡值不動 ✓。分針是 Build 與 Test：抽象層只關心「成了沒」，中間站全是過場。**不需要** invariant：每案用到的事實（步前眼鏡值是 FALSE）都直接寫在該動作自己的 guard 裡（pc 的值決定一切），不需要任何「歷史掙來的」可達性事實——對照本章 Credit 案（guard 給的是 dedup，要換成 ledger 的事實得靠 Sync），你就摸到了「mapping 何時欠 invariant」的手感：**guard 談的變數跟眼鏡讀的變數不是同一個時，中間的橋就是 invariant**。

### 題 2：誰 refine 誰（[15 分鐘] ★★）

三份 spec 共用同一個變數 x：

- SpecA ≜ (x = 0) ∧ □[x′ = x + 1]_x
- SpecB ≜ (x = 0) ∧ □[x′ = x + 1 ∨ x′ = x + 2]_x
- SpecZ ≜ (x = 0) ∧ □[FALSE]_x

判斷六個方向的蘊涵各是否成立：A ⇒ B、B ⇒ A、Z ⇒ A、A ⇒ Z、Z ⇒ B、B ⇒ Z。每個不成立的給一條反例 behavior。先想清楚：[FALSE]_x 是什麼意思？

### 推演解答

[FALSE]_x ≜ FALSE ∨ (x′ = x) ＝ x′ = x：SpecZ 說「x 生為 0，永遠不動」——空實作。變數相同，不需要 INSTANCE 與 mapping，refinement 就是裸的蘊涵＝行為集合的 ⊆。

- **A ⇒ B 成立**：逐步檢查，[x′ = x+1]_x 的兩個 disjunct（+1 或不動）都被 [x′ = x+1 ∨ x′ = x+2]_x 允許。加一是「加一或加二」的特例——實作比規格更具體＝行為更少。
- **B ⇏ A**：behavior 0 → 2 → 2 → …（一步 +2，從此 stuttering）。+2 既不是 +1 也不是不動，A 的第一步就拒收。
- **Z ⇒ A 成立**：Z 只有一條行為（0 永遠不動），而 A 的 stuttering 條款照單全收。**空實作 refine 了計數器規格。**
- **A ⇏ Z**：behavior 0 → 1 → …，x 動了，Z 不允許。
- **Z ⇒ B 成立**：同 Z ⇒ A（或由 Z ⇒ A ⇒ B 遞移）。
- **B ⇏ Z**：同 A ⇏ Z 的反例即可。

教訓有二。其一，refinement 的偏序方向：越細、越具體＝允許的行為越少＝在 ⇒ 的左邊。其二，Z 的位置應該讓你發涼：它 refine 這裡每一份 spec——只要起點合法，「什麼都不做」永遠是合格的實作。這不是悖論，是 safety 的定義（壞事不發生——不做事就不出事），也是陷阱表第一條的數學本體：要逼系統做事，safety refinement 給不了，去找 liveness。

### 題 3：忘了順序的帳本（[25 分鐘] ★★★）

有人要求結算系統對外提供**入帳順序**的保證，於是寫了抽象 spec PayLog：

```tla
\* log 是入帳的「流水帳」：嚴格按發生順序記錄，不重複
VARIABLE log
Range(s) == {s[i] : i \in 1..Len(s)}
InitG == log = << >>
LogPay(m) == /\ m \in Msgs \ Range(log)
             /\ log' = Append(log, m)
SpecG == InitG /\ [][\E m \in Msgs : LogPay(m)]_log
```

要求 mapping **忠實**：每個 Credit 步必須映成一個 LogPay 步（不准映成 stuttering）。(a) 證明：不存在從 SettlementV1 現有變數出發的忠實 refinement mapping（提示：構造兩條收斂到同一個狀態的 behavior）。(b) 加什麼 auxiliary variable 能修好？寫出它與新 mapping，並指出驗證需要的新 invariant。(c) 如果拿掉「忠實」要求，有沒有義務全過、但毫無意義的 mapping？它對應陷阱表哪一條？

### 推演解答

(a) 基準配置（Msgs = {m1, m2}）下構造兩條 behavior：

- w₁：Fetch(c1, m1)、Credit(c1)、Ack(c1)、Fetch(c1, m2)、Credit(c1)、Ack(c1)
- w₂：同一劇本，把 m1 與 m2 對調（m2 先入帳）。

兩條的終點是**同一個狀態** s⋆ ＝ ⟨queue = {}, working 全 "idle", ledger = (1, 1), dedup = {m1, m2}⟩——逐變數對一遍，分毫不差。忠實性要求 w₁ 的兩個 Credit 步分別映成 LogPay(m1)、LogPay(m2)（按此順序，因為第一個 Credit 步前 loḡ 必須還沒收 m1），所以 loḡ(s⋆) ＝ ⟨m1, m2⟩；對 w₂ 同理要求 loḡ(s⋆) ＝ ⟨m2, m1⟩。但 loḡ 是**狀態的函數**，s⋆ 只有一個——矛盾。∎ 根因：v1 把「誰先入帳」這段歷史忘得一乾二淨——dedup 是集合、ledger 是計數，沒有任何變數記順序。規格記得實作忘了的過去：history variable 的標準病徵。

(b) 加 history variable h（入帳流水帳）：Init 加一條 h = ⟨⟩；Credit(c) 加一條 h′ = Append(h, working[c])；Fetch、Ack、Crash 各加 UNCHANGED h。h 只寫不讀（沒有任何 guard 看它），所以不改變原變數的行為——auxiliary 的本分。mapping：`PL == INSTANCE PayLog WITH log <- h`。驗證 Credit ↦ LogPay(m₀) 時，guard 需要 m₀ ∉ Range(h)——這不是白給的，要一條新 invariant：**Range(h) = dedup**（Init 兩邊皆空；Credit 同步各收一個 m₀；其餘不動——自己跑一遍五案歸納，一分鐘）。配上 Credit 原有的 guard m₀ ∉ dedup，橋就搭通了。工程對應赤裸裸：h 就是你為了對帳加的 audit log——「不影響業務邏輯、只為事後回答問題而存在的欄位」，ch14 的那句橋接在 refinement 這裡有了定理級的版本。

(c) 有：loḡ ≜ ⟨⟩（常數空序列）。一切實作步映成 stuttering，起點義務 ⟨⟩ ＝ ⟨⟩ ✓，逐步義務「沒動」✓——SpecG 是允許清單，從不要求 log 成長，定理空洞成立。這就是陷阱表「mapping 與現實脫鉤」那條的最小標本：**忠實性不在三個義務裡，它是你對定理意義的額外要求**——數學只負責蘊涵為真，「定理在說你的系統」這件事，永遠要人來把關。

## 自我檢核

口頭回答，講得出來才算過：

1. 「規格與實作是同一種東西」的精確含義是什麼？I ⇒ S 對應行為集合的什麼關係？為什麼同一份 TwoPhase 既是（TCommit 的）實作、又可以是（更細系統的）規格？
2. refinement mapping 的三個義務各是什麼？它跟 ch05／ch14 的歸納法在方法論上同構在哪裡（提示：行為層主張怎麼變成逐步檢查）？
3. 逐字解釋 `TC == INSTANCE TCommit`：隱式代換的規則是什麼？什麼時候必須用 WITH？抽象層證過的定理會跟著搬下來嗎——例外是哪類公式？
4. TwoPhase 的哪些步映成 TCommit 的 stuttering？「同一訊息收第二次無害」在 ⟨2⟩4 的哪一案落地？這一切靠 ch06 的哪個設計決定？
5. 第一幕的 BOOLEAN mapping 為什麼讓 BadCredit 也通過？「整個證明沒用到 dedup」這個觀察為什麼本身就是警報？
6. 第二幕 Credit ↦ PayOnce 的驗證在哪一步用了 Sync？對 BadCredit 的 1 → 2 那一步，抽象層的三個出口各怎麼死的？
7. history 與 prophecy variable 各修哪種「mapping 不存在」？各舉一個最小例子（一個在本章正文、一個在題 3）。
8. 為什麼永遠 stuttering 的空實作 refine 所有起點相容的 safety spec？要把它趕出去得加什麼、那是哪一章的工具？

## 延伸閱讀

- **Martín Abadi & Leslie Lamport, “The Existence of Refinement Mappings”**, *Theoretical Computer Science* 82(2), 1991, pp. 253–284（會議版 LICS 1988，2008 年獲 LICS Test of Time Award）：`https://lamport.azurewebsites.net/pubs/pubs.html#abadi-existence`。refinement mapping 與 prophecy variable 的出生地；讀引言與 §1–2，看「mapping 何時存在」的三個條件（machine closure、finite invisible nondeterminism、internal continuity）怎麼陳述（2026-06 查證）。
- **Leslie Lamport & Stephan Merz, “Auxiliary Variables in TLA+”**（2017）：`https://lamport.azurewebsites.net/pubs/auxiliary.pdf`（arXiv:1703.05121）。history／prophecy／stuttering 三種輔助變數在 TLA+ 裡的具體加法規則，配玩具例子與一個 snapshot 演算法的完整驗證——本章概念層的施工手冊（2026-06 查證）。
- **Leslie Lamport, “Hiding, Refinement, and Auxiliary Variables”**（2019）：`https://lamport.azurewebsites.net/tla/hiding-and-refinement.pdf`。∃∃（hiding）與 refinement 關係的短篇講義，比論文好入口（2026-06 連結見於 Lamport 網站，內文未逐頁核對）。
- **Specifying Systems** 第 4 章（含 “Instantiation Examined” 與 “Instantiation Is Substitution” 兩節），免費 PDF：`https://lamport.azurewebsites.net/tla/book.html`。INSTANCE／WITH 的官方語意，用 FIFO 把「內層 spec ＋ hiding ＋ 實例化」完整走一遍——本章 INSTANCE 一節的原典。
- **Voting.tla 原文**：`https://github.com/tlaplus/Examples/blob/master/specifications/Paxos/Voting.tla`。對照本章的 Paxos→Voting 對映表讀它的 IncreaseMaxBal 與 VoteFor，再看檔尾的 `C == INSTANCE Consensus`——三層樓中間那層的焊縫（2026-06 開頁驗證）。
- **TwoPhase.tla 原文**：`https://github.com/tlaplus/Examples/blob/master/specifications/transaction_commit/TwoPhase.tla`。讀完本章回去重看最後兩行，它們現在是你能逐義務複核的定理，不再只是兩行咒語。
