# ch12 — Paxos：共識的不變量

> **本章解決什麼問題**：ch11 的 2PC 把「全體一致才 commit」做對了，但 TM 一倒、prepared 的 RM 就永遠卡住——單點不是實作偷懶，是協議結構。要拔掉單點，你需要一個能在「少數節點倒掉、訊息任意延遲」之下仍能做出**不可反悔的決定**的協議。這個問題叫共識（consensus），它的標準答案叫 Paxos。本章用「不變量先於演算法」的順序講它：先寫死要保什麼（一旦多數選定就不可改），再看 phase 1/2 的每條規則怎麼從不變量長出來——這正是 Lamport 自己的 spec 階層 Consensus.tla → Voting.tla → Paxos.tla 的設計。ch13 用 Raft 對照工程化路線，ch15 把本章預告的 refinement 做成機械。

## 從你已知的出發

先從你寫過幾百次的東西開始：樂觀鎖。

```text
UPDATE accounts SET balance = 900, version = 8
WHERE id = 42 AND version = 7
```

帶著版本號去寫；版本舊了，affected rows = 0，你升版本重試。這個模式裡藏著 Paxos 的兩個核心零件：**版本號決定誰說了算**（ballot 就是分散式版的 version），以及**寫之前先確認現況**（phase 1 就是那句 `WHERE version = 7` 的前置讀取＋一個更強的承諾）。差別在仲裁者：樂觀鎖背後有一台單一的 DB 替你裁決誰先誰後；Paxos 要面對的世界裡，「資料庫」本身是三台會當機的機器，沒有任何單點可以當裁判——裁判只能是**多數派（quorum）**。多數你也懂：etcd 三台掛一台照常服務，掛兩台就罷工，你在 K8s 維運裡早就體感過「過半才算數」。

第三個零件你也熟，而且是用痛換來的：兩個 client 對同一筆 row 樂觀鎖互踩，A 寫失敗重試、B 寫失敗重試、誰都過不了——重試風暴。Paxos 裡這叫 duelling proposers，而且本章會給你一個壞消息：這不是實作可以徹底修掉的毛病，是物理（FLP 不可能定理）。

最後接上 ch11 的尾巴。2PC 卡死的根源是：**「決定」這個事實存放在單一 TM 的腦子裡**，TM 倒了，prepared 的 RM 既不能 commit 也不能 abort。Paxos 的答案是把「決定」本身打散：沒有任何單一節點「知道」答案，答案是一個關於多數派的**狀態述語**——多數 acceptor 在同一輪投了同一個值，這個值就被選定了，誰都不必在場。Lamport 後來把 2PC 與 Paxos 正式接起來（同目錄的 PaxosCommit.tla：用 Paxos 替每個 RM 的決定做容錯），那條線本章不走，但你應該帶著 ch11 的問題意識讀本章：**Paxos 就是「沒有單點的決定機制」**。

## 共識問題，與它的規格

把問題說精確。一群行程要從各自提議的值裡選定（choose）一個，要求三條：

- **Agreement**：至多選定一個值——任何兩個得知結果的人，得到的是同一個值。
- **Validity**：選定的值必須是真的有人提議過的值（排除「不管誰提什麼、一律回傳 0」這種作弊解）。
- **Termination**：終究要選定一個值。

你的世界裡到處是它的化身：DB failover 選新 primary、K8s controller 的 leader election、分散式鎖服務決定誰持鎖——本質都是「一群會當機的機器要對一件事永久定案」。

「定案」用 TLA+ 寫出來是什麼樣子？Lamport 的 Consensus.tla（tlaplus/Examples，2026-06 對照原文）給了一份極簡的答案——注意它連「怎麼選」都不說：

```tla
VARIABLE chosen

Init == chosen = {}

Next == /\ chosen = {}
        /\ \E v \in Value : chosen' = {v}

Spec == Init /\ [][Next]_chosen

Inv == /\ TypeOK
       /\ Cardinality(chosen) \leq 1
```

被選定的值的集合從空集合開始，**唯一**允許的一步是從 {} 變成某個單元素集合 {v}——之後 Next 的 guard `chosen = {}` 永遠為假，只剩 stuttering。agreement 的全部內容就是 Inv 那行 Cardinality(chosen) ≤ 1。這是三層樓的頂樓：純粹的「什麼叫定案」，沒有 acceptor、沒有訊息、沒有演算法。

接著是壞消息。**FLP 不可能定理**（Fischer–Lynch–Paterson, 1985）的一句話版：**在非同步系統（訊息延遲沒有上界、不能依賴時鐘）裡，只要有一個行程可能 crash，就不存在既是確定性、又保證必然終止的共識演算法**。本書不證，見延伸閱讀。它逼你選邊：safety 與 termination 不可兼得地「無條件成立」。Paxos 的選擇毫不曖昧——**safety 無條件**（任何交錯、任何延遲、任何少數 crash，agreement 都不破），**liveness 看天吃飯**（網路夠穩、恰好只剩一個 proposer 在推進時，才會定案）。這跟 ch07 的結構完全對齊：Init ∧ □[Next]_vars 只給 safety；而這裡連加 fairness 都買不回 termination，FLP 留的逃生門是隨機性或時序假設（timeout），不是公平性公式。本章接下來九成的篇幅都在講 safety，這是誠實，不是偷懶。

## 不變量先於演算法：把規則長出來

多數人學 Paxos 的方式是先背規則：phase 1 發 prepare、acceptor 回最大編號的已接受提案、proposer 必須採用回應中編號最高的值……規則像憑空掉下來的戒律，背完不知道為什麼，更不敢動——改一個字會不會壞？不知道。本章反過來走：先把「要保什麼」寫死，再看每條規則是從哪個不變量長出來的。走完之後你應該能對任何一條規則回答：「刪掉它，哪個不變量會在哪一步破」——紙上推演就考這個。

以下的推導完全沿 Lamport 的 Paxos Made Simple（2001）§2.2，引文皆為原文（2026-06 對照 PDF）。

**第一步：定案＝同一輪的多數票。**要在會當機的機器上存放「不可反悔」的事實，唯一的辦法是讓它分散在多數派上：v 被選定 ≜ 存在一個多數集，其中每個 acceptor 都接受了 v。為什麼是多數？因為**任何兩個多數集必有交集**——這是把「兩個決定」綁在同一個證人身上、從而逼它們相等的唯一槓桿。記住這句話，整章的 safety 都吊在它上面。

**第二步：一輪不夠。**單輪投票會卡死：三個 proposer 各拿三分之一票，無人過半，而票已投完。又或者剛好過半的那一票所在的 acceptor 當機，結果永遠無人知曉。所以必須允許**多輪**——每輪一個編號，叫 ballot。但多輪立刻引爆新危險：**第 1 輪選了 x，第 2 輪選了 y**。於是要保的不變量現身了。Lamport 給它編號 P2：

> P2. If a proposal with value v is chosen, then every higher-numbered proposal that is chosen has value v.

（若值 v 的提案被選定，則每個被選定的更高編號提案的值也是 v。）ballot 全序，所以 P2 直接蘊涵 agreement。

**第三步：下放。**P2 談的是「被選定」——那是一個全域述語（多數派投了票），**沒有任何單一節點觀測得到**，所以沒有任何節點能直接「執行」P2。ch06 教過你這個方法論：把行為層的願望改寫成可以由本地規則維護的條件。Lamport 連續下放了三次。先下放到 acceptor 的「接受」動作（被選定的前提是被接受）：

> P2a. If a proposal with value v is chosen, then every higher-numbered proposal accepted by any acceptor has value v.

但 P2a 跟最初的一條基本要求打架。那條要求是 P1——

> P1. An acceptor must accept the first proposal that it receives.

（不接受第一個提案，就回到「無人過半」的卡死。）現在想像：v 已在多數派裡被選定，而某個從頭到尾沒收過任何訊息的 acceptor c 剛醒來，一個新 proposer 拿著更高編號、不同值的提案找上它——P1 命令 c 接受，P2a 禁止。接受端救不了，再上移一層，下放到**發出端**：

> P2b. If a proposal with value v is chosen, then every higher-numbered proposal issued by any proposer has value v.

提案要先被發出才可能被接受，所以 P2b ⇒ P2a ⇒ P2。但 proposer 同樣看不到「被選定」，P2b 還是不能直接執行。Lamport 的下一步是本章最值得學的一手：**他不是去「想」規則，而是去看 P2b 的證明需要什麼前提，再把前提抄下來當規則**。假設 ⟨m, v⟩ 已被選定，要證每個編號 n > m 的提案值都是 v——這是個對 n 的歸納證明（ch05），歸納步需要的前提，整理出來就是：

> P2c. For any v and n, if a proposal with value v and number n is issued, then there is a set S consisting of a majority of acceptors such that either (a) no acceptor in S has accepted any proposal numbered less than n, or (b) v is the value of the highest-numbered proposal among all proposals numbered less than n accepted by the acceptors in S.

逐字拆。發出編號 n、值 v 的提案之前，必須存在一個**多數集 S** 作為證據，滿足兩種情況之一：

- **(a) 白紙**：S 裡沒有任何 acceptor 接受過編號小於 n 的提案——歷史是空的，v 隨你選（validity 由「proposer 只提自己手上的值」保住）。
- **(b) 繼承**：S 裡編號小於 n 的所有已接受提案中，**編號最高的那張票的值就是 v**——歷史不空，你沒有選擇權，只能抄最高票。

這條就是整個演算法的「為什麼」。本書沿 Lamport 的編號，跨章一律稱它 **P2c**。

**第四步：時態問題，promise 登場。**P2c 的 (a) 有個陷阱：它說「沒有 acceptor 接受過」，但這是發出當下的快照——如果 S 裡某台 acceptor **之後**才接受一個編號小於 n 的提案呢？P2c 會被追溯破壞。Lamport 原文把這個困境與解法寫得極好：

> Learning about proposals already accepted is easy enough; predicting future acceptances is hard. Instead of trying to predict the future, the proposer controls it by extracting a promise that there won't be any such acceptances.

（查過去容易，測未來很難；所以不要預測未來，**控制**未來——要求 acceptor 承諾不再接受編號小於 n 的提案。）promise 把 (a) 的「現在沒有」升級成「永遠不會有」。於是 phase 1/2 不是發明出來的，是 P2c 的影子（原文演算法摘述）：

1. **Phase 1（prepare）**：proposer 選新編號 n，向 acceptor 們發 prepare 請求，要求回覆：「(a) A promise never again to accept a proposal numbered less than n」與「(b) The proposal with the highest number less than n that it has accepted, if any」。
2. **Phase 2（accept）**：收到**多數** acceptor 的回應後，proposer 發出編號 n、值 v 的 accept 請求——v 是回應中最高編號提案的值；若回應全是白紙，v 才可以自選。acceptor 收到 accept 請求就接受它，除非已經回應過編號更高的 prepare。

每一條規則都能指回 P2c 的某個字：

| 規則 | 它在守 P2c 的哪裡 |
|---|---|
| prepare 必須收齊**多數**回應才能進 phase 2 | S 是多數集——跟任何已選定的多數有交集 |
| acceptor 承諾不再接受編號更小的提案 | 把 (a)/(b) 從快照升級成對未來成立 |
| 1b 回應帶上「已接受的最高編號提案」 | (b) 需要的歷史證據 |
| 回應不空時，v 必須抄最高編號的值 | (b) 的「v is the value of the highest-numbered …」 |
| 回應全空時才能自選值 | (a) 的白紙情況 |
| acceptor 拒收編號小於承諾的 accept 請求 | 兌現 promise，否則 (a) 被追溯破壞 |

**第五步：把歸納證明補完。**P2c 為什麼真的足夠？給「工程師的嚴謹」版（完整機械版是 Voting.tla 的 ShowsSafety 定理與其 TLAPS 證明，本章不展開）：

**定理**：P2c 持續成立 ⇒ P2b。設 ⟨m, v⟩ 已被選定（多數集 C 在 ballot m 全數投給 v），證：每個被發出的 ⟨n, w⟩（n > m）都有 w = v。對 n 做強歸納（ch05）。

- ⟨1⟩1. 歸納假設：每個編號落在 m..(n−1) 之間、曾被發出的提案，值都是 v。（n = m+1 時該區間只有 m，而編號 m 的提案就是被選定的 ⟨m, v⟩，成立。）
- ⟨1⟩2. C 中每個 acceptor 都接受過編號落在 m..(n−1) 的提案——至少 ballot m 那張。又由 ⟨1⟩1，凡編號落在這個區間且被接受的提案（被接受的前提是曾被發出），值都是 v。
- ⟨1⟩3. ⟨n, w⟩ 被發出，由 P2c 存在多數集 S 滿足 (a) 或 (b)。多數必交：取 a ∈ S ∩ C。
- ⟨1⟩4. (a) 不可能：a ∈ C 接受過編號 m < n 的提案，S 不是白紙。
- ⟨1⟩5. 故 (b) 成立：w 等於「S 中編號小於 n 的已接受提案」裡最高編號那張的值。這個最高編號 ≥ m（a 的 ballot m 票就在池子裡）且 ≤ n−1，由 ⟨1⟩2 它的值是 v。所以 w = v。
- ⟨1⟩6. QED。由強歸納，所有 n > m 的提案值皆 v；更高 ballot 若有值被選定，必是 v——P2 成立，agreement 成立。

注意 ⟨1⟩4 到 ⟨1⟩5 的槓桿全是 quorum intersection：**S 必含一個 C 的證人，證人把歷史押進 (b)**。沒有交集，(b) 看不到歷史，P2c 形同虛設——紙上推演題 1 會讓你親手體驗。

## 三層樓：Consensus → Voting → Paxos

上一節的推導，Lamport 在 tlaplus/Examples 裡寫成了三份疊起來的 spec（同一目錄，2026-06 對照原文）：

```text
┌─────────────────────────────┐
│ Consensus.tla               │   定案長什麼樣：chosen 至多一個值
│ VARIABLE chosen             │
└──────────────▲──────────────┘
               │  refinement：Voting!Spec => C!Spec
┌──────────────┴──────────────┐
│ Voting.tla                  │   為什麼安全：ballot、quorum、SafeAt
│ VARIABLES votes, maxBal     │
└──────────────▲──────────────┘
               │  refinement：Paxos!Spec => V!Spec
┌──────────────┴──────────────┐
│ Paxos.tla                   │   怎麼跑起來：訊息傳遞
│ VARIABLES maxBal, maxVBal,  │
│           maxVal, msgs      │
└─────────────────────────────┘
```

頂樓你已經看過。中層 **Voting.tla** 是 P2c 的數學本體——有 ballot、投票與 quorum，但**還沒有任何訊息**。先看它怎麼定義「選定」：

```tla
VotedFor(a, b, v) == <<b, v>> \in votes[a]

ChosenAt(b, v) == \E Q \in Quorum :
                     \A a \in Q : VotedFor(a, b, v)

chosen == {v \in Value : \E b \in Ballot : ChosenAt(b, v)}
```

注意 chosen 在這層**不是變數，是定義出來的狀態函數**——「被選定」純粹是 votes 的影子，這正式坐實了前面那句「沒有任何節點知道答案，答案是一個狀態述語」。quorum 的假設只有兩行，第二行就是那根承重柱：

```tla
ASSUME QuorumAssumption == /\ \A Q \in Quorum : Q \subseteq Acceptor
                           /\ \A Q1, Q2 \in Quorum : Q1 \cap Q2 # {}
```

接著是 P2c 在這層的化身。先定義「b 輪以下再也選不出別的值」：

```tla
CannotVoteAt(a, b) == /\ maxBal[a] > b
                      /\ DidNotVoteAt(a, b)

NoneOtherChoosableAt(b, v) ==
   \E Q \in Quorum :
     \A a \in Q : VotedFor(a, b, v) \/ CannotVoteAt(a, b)

SafeAt(b, v) == \A c \in 0..(b-1) : NoneOtherChoosableAt(c, v)
```

SafeAt(b, v) 讀作：對每個更低的 ballot c，存在一個 quorum，其中每個成員要嘛已投 v、要嘛**永遠不可能**在 c 投票（已承諾更高的 maxBal 且沒在 c 投過）——所以 c 輪不可能選出 v 以外的值。SafeAt 是「在 b 輪投 v 是安全的」的精確語意，但它量化了**所有**更低的 ballot，不好直接檢查；於是有一個有限證據版：

```tla
ShowsSafeAt(Q, b, v) ==
  /\ \A a \in Q : maxBal[a] \geq b
  /\ \E c \in -1..(b-1) :
      /\ (c # -1) => \E a \in Q : VotedFor(a, c, v)
      /\ \A d \in (c+1)..(b-1), a \in Q : DidNotVoteAt(a, d)
```

把它跟 P2c 對起來：Q 就是 S；第一行是收齊的 promise；c = −1 的情況是 (a)（Q 裡沒人在 b 以下投過票）；c ≥ 0 的情況是 (b)（c 是 Q 裡 b 以下最高的投票輪，那一輪有人投了 v）。Voting 的投票動作把 ShowsSafeAt 直接寫進 guard：

```tla
VoteFor(a, b, v) ==
    /\ maxBal[a] \leq b
    /\ \A vt \in votes[a] : vt[1] # b
    /\ \A c \in Acceptor \ {a} :
         \A vt \in votes[c] : (vt[1] = b) => (vt[2] = v)
    /\ \E Q \in Quorum : ShowsSafeAt(Q, b, v)
    /\ votes' = [votes EXCEPT ![a] = @ \cup {<<b, v>>}]
    /\ maxBal' = [maxBal EXCEPT ![a] = b]
```

而「P2c 足夠」在這層是一條定理（本章 ⟨1⟩ 論證的機械版）：

```tla
THEOREM ShowsSafety ==
          TypeOK /\ VotesSafe /\ OneValuePerBallot =>
             \A Q \in Quorum, b \in Ballot, v \in Value :
               ShowsSafeAt(Q, b, v) => SafeAt(b, v)
```

Voting.tla 的結尾寫著 `C == INSTANCE Consensus` 與 `THEOREM Spec => C!Spec`：**Voting 的每條合法行為，都是 Consensus 允許的行為**——ch06 那句「實作正確＝Impl ⇒ Spec」的活例。同樣地，等一下你會在 Paxos.tla 的結尾看到 `V == INSTANCE Voting` 與 `THEOREM Spec => V!Spec`。三層樓靠兩條蘊涵焊在一起；INSTANCE 與 substitution 怎麼讀、這種定理怎麼證，是 ch15 的主題，本章你只需要看見階梯本身：**演算法（Paxos）是不變量（Voting）的實作，不變量是規格（Consensus）的守護者**。

注意 VoteFor 的 guard 裡有一條「全知」條件：它直接讀**其他 acceptor** 的 votes（第三個合取）和全域的 ShowsSafeAt。單機數學可以這樣寫，分散式系統不行——沒有人能瞬間讀到別人的狀態。把這些全知 guard 換成**訊息**，就是底層 Paxos.tla 的全部工作。

## 精讀 Paxos.tla

進到底層（節錄自 tlaplus/Examples 原文，2026-06；註解有刪節）。常數與 Voting 相同；四個變數：

```tla
VARIABLE maxBal,
         maxVBal, \* <<maxVBal[a], maxVal[a]>> is the vote with the largest
         maxVal,    \* ballot number cast by a; it equals <<-1, None>> if
                    \* a has not cast any vote.
         msgs     \* The set of all messages that have been sent.
```

每個 acceptor 三個欄位：**maxBal[a]** 是 promise 線（「編號小於這個的我一概不理」）；**maxVBal[a] 與 maxVal[a]** 是最後一票（在哪輪、投了什麼值；沒投過則為 −1 與 None）。注意 maxBal[a] ≥ maxVBal[a] 恆成立：承諾線只會被 prepare 與投票推高。

msgs 是**所有發過的訊息的集合，只增不減**。原檔的 NOTE 註解值得整段消化（節譯）：更精確的模型應該有「在途訊息」、遺失、重複與接收動作；但這份 spec 主要關心 safety，而 **safety 只說「什麼訊息可以被收到」，從不主張「有訊息真的被收到」——所以「訊息遺失」與「訊息永遠沒被收到」在這層無法區分，根本不必建模**。一句話的抽象選擇（ch02），省掉一半的狀態空間，而且是誠實的：要談 liveness 才需要把「必須送達」說清楚。順帶地，msgs 只增不減也天然涵蓋了亂序與重複送達——舊訊息永遠躺在那裡，隨時可能被「再收到一次」。

```tla
Init == /\ maxBal = [a \in Acceptor |-> -1]
        /\ maxVBal = [a \in Acceptor |-> -1]
        /\ maxVal = [a \in Acceptor |-> None]
        /\ msgs = {}

Send(m) == msgs' = msgs \cup {m}
```

四個 action。先看 phase 1 的一來一回：

```tla
Phase1a(b) == /\ Send([type |-> "1a", bal |-> b])
              /\ UNCHANGED <<maxBal, maxVBal, maxVal>>

Phase1b(a) == /\ \E m \in msgs :
                  /\ m.type = "1a"
                  /\ m.bal > maxBal[a]
                  /\ maxBal' = [maxBal EXCEPT ![a] = m.bal]
                  /\ Send([type |-> "1b", acc |-> a, bal |-> m.bal,
                            mbal |-> maxVBal[a], mval |-> maxVal[a]])
              /\ UNCHANGED <<maxVBal, maxVal>>
```

有一件事值得停一秒：**這份 spec 裡沒有 proposer 行程**。Phase1a(b) 的參數是 ballot，不是某個 proposer 的名字——「ballot b 的 leader」是隱含的，誰都可以替任何 b 發 1a。本章基準配置說的「2 個 proposers」p1、p2，在 spec 裡的對應就是「ballot 1 的 leader」與「ballot 2 的 leader」；工程上 ballot 編號空間會切給不同 proposer（例如 p1 用奇數、p2 用偶數），保證同一編號只有一個主人。Phase1b 是 promise 的執行處：guard `m.bal > maxBal[a]` 讓 maxBal 嚴格單調上升，1b 回訊帶上最後一票（mbal、mval）——P2c 的 (b) 所需的歷史證據。

接著是整個演算法的心臟。原檔註解直說：「This second conjunct … is the heart of the algorithm」：

```tla
Phase2a(b, v) ==
  /\ ~ \E m \in msgs : m.type = "2a" /\ m.bal = b
  /\ \E Q \in Quorum :
        LET Q1b == {m \in msgs : /\ m.type = "1b"
                                 /\ m.acc \in Q
                                 /\ m.bal = b}
            Q1bv == {m \in Q1b : m.mbal \geq 0}
        IN  /\ \A a \in Q : \E m \in Q1b : m.acc = a
            /\ \/ Q1bv = {}
               \/ \E m \in Q1bv :
                    /\ m.mval = v
                    /\ \A mm \in Q1bv : m.mbal \geq mm.mbal
  /\ Send([type |-> "2a", bal |-> b, val |-> v])
  /\ UNCHANGED <<maxBal, maxVBal, maxVal>>
```

逐塊讀：

- 第一個合取：ballot b 至多發**一張** 2a——同輪不能提兩個值（守 Voting 的 OneValuePerBallot；工程對應「leader 自己要記得提過什麼」，這裡用 msgs 單調性白嫖）。
- Q1b：來自 quorum Q、回應 ballot b 的 1b 訊息；`\A a \in Q : \E m \in Q1b : m.acc = a` 要求**收齊整個 Q**——P2c 的「a majority of acceptors」。
- Q1bv：其中真的帶票（mbal ≥ 0）的子集。`Q1bv = {}` 就是 P2c 的 (a)：白紙，v 自由。否則必須存在一張 mbal 最大的 1b，其 mval 等於 v——P2c 的 (b)：抄最高票。**這個 LET 區塊就是 P2c 翻成可執行檢查的樣子。**原檔註解明說：由此可推出存在 Q 使 ShowsSafeAt(Q, b, v)（Voting 層的橋）。

```tla
Phase2b(a) == \E m \in msgs : /\ m.type = "2a"
                              /\ m.bal \geq maxBal[a]
                              /\ maxBal' = [maxBal EXCEPT ![a] = m.bal]
                              /\ maxVBal' = [maxVBal EXCEPT ![a] = m.bal]
                              /\ maxVal' = [maxVal EXCEPT ![a] = m.val]
                              /\ Send([type |-> "2b", acc |-> a,
                                       bal |-> m.bal, val |-> m.val])
```

Phase2b 是投票：guard `m.bal \geq maxBal[a]` 兌現 promise（小於承諾線的 accept 請求被無聲拒絕），三個欄位一起更新，2b 訊息對外宣告這一票。learner 在這份 spec 裡被抽象掉了——「v 被選定」就是「存在 quorum，其成員都發過 ⟨b, v⟩ 的 2b」，誰要知道結果就去數 2b。最後組裝與 refinement：

```tla
Next == \/ \E b \in Ballot : \/ Phase1a(b)
                             \/ \E v \in Value : Phase2a(b, v)
        \/ \E a \in Acceptor : Phase1b(a) \/ Phase2b(a)

Spec == Init /\ [][Next]_vars

votes == [a \in Acceptor |->
           {<<m.bal, m.val>> : m \in {mm \in msgs: /\ mm.type = "2b"
                                                   /\ mm.acc = a }}]

V == INSTANCE Voting

THEOREM Spec => V!Spec
```

votes 從 2b 訊息**重建**出 Voting 層的投票記錄——這就是 refinement mapping 的雛形（把底層狀態映成上層狀態），ch15 正式拆解。

## Worked example：雙 proposer 競爭

基準配置：acceptors = {a1, a2, a3}，quorum＝任兩個以上（{a1,a2}、{a1,a3}、{a2,a3} 與全集——兩兩必交 ✓）；proposer p1 用 ballot 1 提值 x，proposer p2 用 ballot 2 提值 y。狀態記法：每個 acceptor 寫成 (maxBal, maxVBal, maxVal)；訊息縮寫 1a⟨b⟩、1b⟨a, b, mbal, mval⟩、2a⟨b, v⟩、2b⟨a, b, v⟩。

### 情境 A：拔掉 phase 1，看分歧怎麼發生

先做對照組。規則只改一條：**proposer 不做 phase 1，直接發 2a、值自己挑**；acceptor 端的 Phase2b 規則原封不動，「同輪多數票＝選定」也不變。

| 步 | 動作 | a1 | a2 | a3 | 新增訊息 |
|---|---|---|---|---|---|
| 0 | Init | (-1, -1, None) | (-1, -1, None) | (-1, -1, None) | — |
| 1 | p1 直接發 2a（沒問過任何人） | 不變 | 不變 | 不變 | 2a⟨1, x⟩ |
| 2 | Phase2b(a1)：1 ≥ −1 ✓ | (1, 1, x) | 不變 | 不變 | 2b⟨a1, 1, x⟩ |
| 3 | Phase2b(a2)：1 ≥ −1 ✓ | 不變 | (1, 1, x) | 不變 | 2b⟨a2, 1, x⟩ |

第 3 步之後，quorum {a1, a2} 在 ballot 1 全數投了 x：**ChosenAt(1, x) 成立，x 已被選定**。任何 learner 收齊這兩張 2b 都會誠實地宣布 x。繼續：

| 步 | 動作 | a1 | a2 | a3 | 新增訊息 |
|---|---|---|---|---|---|
| 4 | p2 直接發 2a（也沒問過任何人） | 不變 | 不變 | 不變 | 2a⟨2, y⟩ |
| 5 | Phase2b(a2)：2 ≥ 1 ✓ | 不變 | (2, 2, y) | 不變 | 2b⟨a2, 2, y⟩ |
| 6 | Phase2b(a3)：2 ≥ −1 ✓ | 不變 | 不變 | (2, 2, y) | 2b⟨a3, 2, y⟩ |

第 6 步之後，quorum {a2, a3} 在 ballot 2 全數投了 y：ChosenAt(2, y) 也成立。a2 在 ballot 1 投的那票不會消失——2b⟨a2, 1, x⟩ 已經發出去了，先前那個 learner 宣布的 x 收不回來。於是 chosen = {x, y}，Cardinality(chosen) = 2，Consensus 層的 Inv 陣亡：**兩個 learner 各自誠實，答案不同**。

驗屍。acceptor 沒有破任何規則：第 5 步 a2 收下 2a⟨2, y⟩ 完全合法——它的 guard 只擋「比承諾線舊」的請求，而**沒有人問過 a2，它沒承諾過任何東西**。兇手是第 4 步的「發出」：檢查 P2c，多數集 S 只有三個候選——{a1,a2}、{a1,a3}、{a2,a3}——每一個都含 a1 或 a2 至少一個，而 a1、a2 都已接受 ⟨1, x⟩，(a) 三路全滅；(b) 則要求 y 等於最高票的值 x，也不成立。**⟨2, y⟩ 在任何 S 之下都違反 P2c。**phase 1 的全部意義就是把這個檢查做成訊息協議：在「發出」之前，逼 proposer 先收集到一個能證明 (a) 或 (b) 的多數證據。

### 情境 B：完整 Paxos，看 P2c 怎麼擋下

同一個劇本，這次照規矩來。p1 先完整跑完 ballot 1：

| 步 | 動作 | a1 | a2 | a3 | 新增訊息 |
|---|---|---|---|---|---|
| 0 | Init | (-1, -1, None) | (-1, -1, None) | (-1, -1, None) | — |
| 1 | Phase1a(1)：p1 開 ballot 1 | 不變 | 不變 | 不變 | 1a⟨1⟩ |
| 2 | Phase1b(a1)：1 > −1 ✓ | (1, -1, None) | 不變 | 不變 | 1b⟨a1, 1, −1, None⟩ |
| 3 | Phase1b(a2)：1 > −1 ✓ | 不變 | (1, -1, None) | 不變 | 1b⟨a2, 1, −1, None⟩ |
| 4 | Phase2a(1, x)：見下 | 不變 | 不變 | 不變 | 2a⟨1, x⟩ |
| 5 | Phase2b(a1)：1 ≥ 1 ✓ | (1, 1, x) | 不變 | 不變 | 2b⟨a1, 1, x⟩ |
| 6 | Phase2b(a2)：1 ≥ 1 ✓ | 不變 | (1, 1, x) | 不變 | 2b⟨a2, 1, x⟩ |

第 4 步逐合取驗：msgs 沒有 ballot 1 的 2a ✓；取 Q = {a1, a2}，Q1b 兩張都在、蓋住 Q ✓；Q1bv = {}（兩張都是 mbal = −1 的白紙）⇒ 第一個 disjunct 成立，x 自由選 ✓。第 6 步之後 **ChosenAt(1, x)：x 已被選定**。這個事實從此不可逆——接下來的問題是，姍姍來遲的 p2 會不會搞砸它。

| 步 | 動作 | a1 | a2 | a3 | 新增訊息 |
|---|---|---|---|---|---|
| 7 | Phase1a(2)：p2 開 ballot 2 | 不變 | 不變 | 不變 | 1a⟨2⟩ |
| 8 | Phase1b(a2)：2 > 1 ✓ | 不變 | (2, 1, x) | 不變 | 1b⟨a2, 2, 1, x⟩ |
| 9 | Phase1b(a3)：2 > −1 ✓ | 不變 | 不變 | (2, -1, None) | 1b⟨a3, 2, −1, None⟩ |

注意第 8 步：a2 的 promise 線推高到 2，但它**順手把最後一票 ⟨1, x⟩ 押進了 1b**——歷史進入了 p2 的視野。現在 p2 想發 2a⟨2, y⟩，逐合取驗 Phase2a(2, y)：

- msgs 沒有 ballot 2 的 2a ✓。
- 取 Q = {a2, a3}：Q1b = {1b⟨a2, 2, 1, x⟩, 1b⟨a3, 2, −1, None⟩}，蓋住 Q ✓。
- Q1bv = {1b⟨a2, 2, 1, x⟩} ≠ {}，所以第一個 disjunct 死了；第二個 disjunct 要求存在 m ∈ Q1bv 使 m.mval = y 且 m.mbal 最大——唯一的候選那張票寫的是 x，不是 y。**兩個 disjunct 全滅：Phase2a(2, y) 在這個狀態不是 enabled。**

p2 的「意志」根本進不了狀態空間：想提 y，但這個 action 走不出去（ch06 的 ENABLED——spec 把不安全的選項直接修剪掉，而不是事後懲罰）。它**唯一** enabled 的 phase 2 是：

| 步 | 動作 | a1 | a2 | a3 | 新增訊息 |
|---|---|---|---|---|---|
| 10 | Phase2a(2, x)：Q1bv 最高票 ⟨1, x⟩ ⇒ 被迫抄 x | 不變 | 不變 | 不變 | 2a⟨2, x⟩ |
| 11 | Phase2b(a2)：2 ≥ 2 ✓；Phase2b(a3)：2 ≥ 2 ✓ | 不變 | (2, 2, x) | (2, 2, x) | 2b⟨a2, 2, x⟩、2b⟨a3, 2, x⟩ |

ballot 2 也「選定」了——選定的還是 x。ChosenAt(1, x) 與 ChosenAt(2, x) 並存，chosen = {x}，agreement 完好。**p2 沒有失敗，它只是被迫成為 x 的傳聲筒**：它的 ballot 推進了系統（promise 線整體墊高），但值的決定權在第 6 步就已經封死了。

換 quorum 也逃不掉：p2 若改收 {a1, a3} 的 1b，a1 會回 1b⟨a1, 2, 1, x⟩（它在 ballot 1 投過 x），照樣被迫抄 x；{a1, a2} 更是兩張票都寫 x。共同原因只有一個——**ballot 2 的任何 quorum 都與選定 x 的 quorum {a1, a2} 相交，交集裡的證人把歷史押進 1b**。這就是 quorum intersection ＋ P2c 的合奏：(b) 永遠看得到該看的歷史。

### 情境 B′：搶先的 phase 1——safety 的另一面

把交錯反過來，讓 p2 的 phase 1 跑在最前面，會看到 P2c 的 (a) 與 promise 怎麼合作：

1. 1a⟨2⟩；a2、a3 回 1b（promise 線推到 2，皆白紙）→ a2 = (2, −1, None)、a3 = (2, −1, None)。
2. p1 此時才發 1a⟨1⟩：只有 a1 能回（a2、a3 的 guard 要求 1 > 2，不成立）。ballot 1 的 1b 永遠湊不滿多數 ⇒ Phase2a(1, ·) 永遠不 enabled ⇒ **ballot 1 胎死腹中**。就算 p1 硬是把 2a⟨1, x⟩ 發出去（它湊不齊證據，發不出來；退一萬步說發出來了），a2、a3 的 Phase2b guard（1 ≥ 2 不成立）也會拒收——promise 把 (a) 的「現在沒有」撐成「永遠不會有」。
3. p2 的 Phase2a(2, y)：Q = {a2, a3}，Q1bv = {} ⇒ (a) 白紙 ⇒ 自由選 y；a2、a3 投 ⟨2, y⟩ ⇒ **y 被選定**。

沒有分歧：x 從頭到尾沒被選定，y 是唯一定案。教訓很重要：**Paxos 保證至多一個值被選定，不保證是「你的」值**——p1 輸了，但 agreement 與 validity 都無恙。

把 B′ 再推一步就是 liveness 的深淵。Paxos Made Simple 的 Progress 一節自己構造了這個場景（摘述）：p 完成編號 n1 的 phase 1；q 接著完成 n2 > n1 的 phase 1，於是 p 的 phase 2 被拒；p 不服，完成 n3 > n2 的 phase 1，換 q 的 phase 2 被拒……兩個 proposer 編號節節攀升，**永遠沒有任何提案被選定**。這條無限 behavior 完全滿足 Spec——□[Next]_vars 是允許清單，不是待辦清單（ch06）。Lamport 的處方是選出一個 distinguished proposer 作為唯一的提案者；而「可靠地選出它」本身又是……一個共識問題。原文坦白引用 FLP：可靠的選舉必須靠隨機性或實際時間（例如 timeout）；但無論選舉成敗，**safety 都不受影響**。這就是「safety 無條件、liveness 看天吃飯」的全文注解：工程上你用 timeout＋退避把 duel 機率壓到極低（你處理重試風暴的手法一模一樣），數學上你接受 termination 沒有無條件保證。

## 為什麼大家覺得 Paxos 難

規則就這四個 action，狀態就三個欄位加一袋訊息——憑什麼「難」名遠播？歷史一半、教學順序一半。

歷史那一半：Lamport 1998 年的原始論文 The Part-Time Parliament 用考古寓言包裝整個演算法（虛構的 Paxos 島、兼職議會、出土的銘文），審稿人與讀者多年消化不良。2001 年他寫了 Paxos Made Simple，整篇摘要只有一句話：

> The Paxos algorithm, when presented in plain English, is very simple.

教學順序那一半才是本章在意的。多數教材（包括許多課堂）從規則開始：先背 phase 1/2，再（也許）補證明。規則先行的代價是**每條規則都像任意的戒律**——為什麼回應裡要帶最高票？為什麼必須抄它的值？為什麼是多數而不是三分之二？背下來的人換一個場景就不會變通，更不敢改。而你這章走的是反向：P2 → P2a → P2b → P2c 每一步都是「上一條執行不了，所以下放」，phase 1/2 是 P2c 的影子，每條規則都能指回不變量的某個字。順序反過來，難度跌一半——剩下那一半是 quorum intersection 的歸納論證，⟨1⟩1 到 ⟨1⟩6 你也走過了。

最好的證據是 Lamport 自己的三層 spec：他**沒有**從演算法寫起。頂樓 Consensus 只說「選了至多一個值」；中層 Voting 把 ballot、quorum、SafeAt 的數學寫完——此時還沒有一封訊息；演算法在最底層才出現，而且每個 action 都對著上層的某個動作或 stuttering。「不變量先於演算法」不是本書的教學花招，是原作者的設計檔案結構。

最後一句話帶過工程化：single-decree Paxos 只定案**一個**值；真實系統要定案一串值（replicated log），做法是逐 slot 跑一個 Synod 實例、並讓穩定的 leader 把 phase 1 攤提掉——這叫 Multi-Paxos，而 Raft 乾脆把「強 leader」做成協議的一級公民。取捨對照與 raft.tla 精讀，見 ch13。

## 陷阱與防禦

| 故障模式 | 它怎麼給你假安全感 | 怎麼自我察覺 |
|---|---|---|
| 把「被選定」當成某節點知道的事件 | 「leader 收到多數 ack 就算定案了」——但 chosen 是全域狀態述語，定案的瞬間**沒有任何節點知道**；leader 可能在得知前就倒了，事實卻已不可逆 | 對每個「系統決定了 X」的句子追問：這是哪個狀態述語？誰的本地狀態能見證它？見證與事實的時間差就是 bug 的窩 |
| 把 ballot 當成「新的蓋掉舊的」 | 「我的編號比較大，我的值理應獲勝」——大編號不是覆寫權，是**繼承義務**：phase 1 強迫你抄多數派的最高票 | 回 P2c 的 (b)：自選值的權利只在 Q1bv = {} 時存在。手驗：情境 B 第 10 步，p2 連提自己值的資格都沒有 |
| promise 不持久化 | 測試全綠——直到某台 acceptor 重啟、maxBal 歸零，等於收回承諾；P2c 的 (a) 被追溯破壞，分歧重演（紙上推演題 3 就是這個故障的紙上版） | maxBal/maxVBal/maxVal 的單調性是 safety 的承重牆：spec 裡沒有「磁碟」，但實作必須在回 1b/2b **之前** fsync。review 清單：每個承諾欄位，落盤了嗎？ |
| 把 liveness 當成理所當然 | 「總會有人成功的」——duelling proposers 的無限互踩是 Spec 的合法 behavior，而且 FLP 說沒有確定性方法能根治 | 分開驗收：safety 找不變量，liveness 找「需要什麼環境假設」。任何聲稱「必然終止」的共識設計，先問它把 FLP 藏到哪了（timeout？隨機化？） |
| 動了 quorum 卻沒重驗交集 | 「讀寫各過半改成讀 1 寫 3」「偶數叢集」「動態縮編」——QuorumAssumption 是公理不是定理，任何兩個 quorum 必交是人配置出來的 | 改完 quorum 配置，手算最壞交集：∀ Q1, Q2：Q1 ∩ Q2 ≠ ∅ 還成立嗎？題 1 給你一個 2/4 的反面教材 |
| 誤讀 msgs 單調的抽象 | 「spec 都沒建模掉訊息，不嚴謹吧」——其實相反：safety 層「遺失」＝「永遠沒收到」，免費涵蓋；真正要小心的是反方向：實作裡重複、亂序送達的舊訊息，spec 裡全部合法 | 讀任何 spec 先問 ch02 的問題：它建模了什麼、刻意忽略什麼、忽略是否誠實。對 Paxos：safety 不靠送達，liveness 才靠 |

## 紙上推演

### 題 1：打破 quorum 假設（[20 分鐘] ★★）

四台 acceptors {a1, a2, a3, a4}，有人把 quorum 定義成「任意兩台」（理由：「讀寫都快」）。注意 {a1, a2} ∩ {a3, a4} = {}——QuorumAssumption 的第二行死了。請**完全遵守** Paxos.tla 的四個 action，構造一條 behavior 使兩個不同的值都被選定。逐步列出每台 acceptor 的 (maxBal, maxVBal, maxVal)。然後回答：四台機器的正確 quorum 該是什麼？這跟「etcd 建議奇數台」有什麼關係？

### 推演解答

每條規則都照走，照樣分歧：

1. Phase1a(1)：1a⟨1⟩。
2. Phase1b(a1)、Phase1b(a2)：a1 = a2 = (1, −1, None)，兩張白紙 1b。
3. Phase2a(1, x)：Q = {a1, a2} 是合法 quorum、1b 收齊、Q1bv = {} ⇒ 自由選 x。2a⟨1, x⟩。
4. Phase2b(a1)、Phase2b(a2)：a1 = a2 = (1, 1, x)。**ChosenAt(1, x)**——quorum {a1, a2} 全票。
5. Phase1a(2)：1a⟨2⟩。
6. Phase1b(a3)、Phase1b(a4)：a3 = a4 = (2, −1, None)。注意：**它們從沒見過 ballot 1 的任何訊息**，1b 是白紙——而這完全合法。
7. Phase2a(2, y)：Q = {a3, a4} 是合法 quorum、1b 收齊、Q1bv = {} ⇒ (a) 成立 ⇒ **自由選 y**。2a⟨2, y⟩。
8. Phase2b(a3)、Phase2b(a4)：a3 = a4 = (2, 2, y)。**ChosenAt(2, y)**。chosen = {x, y}，分歧。

兇手不是任何一條規則，是公理：P2c 寫「a majority of acceptors」不是修辭——**(b) 能看到歷史的唯一原因是 S 與既有的選定 quorum 相交**。{a3, a4} 跟 {a1, a2} 不相交，歷史對它就是不存在。四台的正確 quorum 是任意三台（任兩個三元集必交），容錯量 1——跟三台叢集一樣，但多付一台機器的錢、寫入還要多等一票。這就是 etcd 文件勸你用奇數台的數學根源：偶數台的多數派門檻上升，容錯量卻不變，純虧。

### 題 2：在小例上驗 P2c（[15 分鐘] ★★）

基準三台。某狀態下 msgs 恰好含三張 1b（沒有任何 ballot 2 的 2a）：

- 1b⟨a1, 2, −1, None⟩
- 1b⟨a2, 2, 1, y⟩
- 1b⟨a3, 2, −1, None⟩

（即：三台都回應過 1a⟨2⟩；a2 曾在 ballot 1 投過 y，另外兩台從未投票。）回答：(i) 取 Q = {a2, a3}，Phase2a(2, v) 對哪些 v 是 enabled？(ii) 取 Q = {a1, a3} 呢？(iii) 若 proposer 用 (ii) 的 Q 發出 2a⟨2, x⟩（x ≠ y），msgs 裡會同時存在 2a⟨1, y⟩（a2 那票的來源）與 2a⟨2, x⟩——兩個 ballot、兩個值。這安全嗎？用 Voting 的 SafeAt 語言說明。

### 推演解答

(i) Q1b 蓋住 {a2, a3} ✓；Q1bv = {1b⟨a2, 2, 1, y⟩} ≠ {}，最高票唯一，其 mval = y ⇒ **只有 v = y enabled**——P2c 的 (b)：a2 的歷史綁死了你。

(ii) Q1b 蓋住 {a1, a3} ✓；Q1bv = {} ⇒ 第一個 disjunct 成立 ⇒ **任何 v ∈ Value 都 enabled**——P2c 的 (a)：這個 quorum 是白紙。

(iii) 安全，而且這是本題真正的考點：**同一個狀態，不同 quorum 給出不同的束縛，而兩者都對**。檢查 y 還有沒有機會在 ballot 1 被選定：ChosenAt(1, y) 需要一個 quorum 在 ballot 1 全票投 y，而每個 quorum 都含 a1 或 a3 至少一個；a1、a3 的 maxBal 已是 2 且未在 ballot 1 投票——這正是 Voting 的 CannotVoteAt(a, 1)：promise 線高過 1，Phase2b 的 guard 永遠擋掉 ballot 1 的 accept 請求。所以 NoneOtherChoosableAt(1, x) 成立（{a1, a3} 作證），SafeAt(2, x) 成立：**ballot 1 的 y 已經永遠湊不滿多數，x 在 ballot 2 暢行無阻**。a2 那張 ⟨1, y⟩ 的票成了死票。順帶驗證 OneValuePerBallot 無恙：它只要求**同一** ballot 內值唯一，跨 ballot 不同值本來就是 Paxos 的日常——被選定的值唯一，靠的是 P2c，不是「值從不變化」。

### 題 3：改一個 guard，找出分歧（[25 分鐘] ★★★）

同事覺得 Phase2b 的 guard 太嚴：「跟 promise 比太保守了，跟**最後一票**比就夠了吧。」他把 `m.bal \geq maxBal[a]` 改成 `m.bal \geq maxVBal[a]`（其餘四行不動）。直覺上好像沒差——投過的票本來就擋住更舊的提案？請構造一條 behavior 打破 agreement（基準配置：三台、p1/ballot 1/值 x、p2/ballot 2/值 y），並指出 P2c 在哪一步、以哪種方式被破壞。

### 推演解答

這個改動把 promise 變成廢紙：acceptor 答應過「不收 ballot < 2」，但 guard 不再檢查 maxBal，承諾無人兌現。反例（每步都標 guard 計算）：

1. p1 跑 phase 1：1a⟨1⟩；a1、a2 回白紙 1b ⇒ a1 = a2 = (1, −1, None)。
2. p2 跑 phase 1：1a⟨2⟩；a2（2 > 1 ✓）、a3（2 > −1 ✓）回白紙 1b ⇒ a2 = (2, −1, None)、a3 = (2, −1, None)。
3. Phase2a(2, y)：Q = {a2, a3}，1b 收齊、Q1bv = {} ⇒ 自由選 y。2a⟨2, y⟩。**此刻 P2c 的 (a) 成立**——靠的是 a2、a3 的承諾「不再接受 ballot < 2」。
4. Phase2a(1, x)：Q = {a1, a2}——注意第 1 步的兩張 1b **還在 msgs 裡**（msgs 單調），收齊 ✓、Q1bv = {} ⇒ 自由選 x。2a⟨1, x⟩。p1 不知道 a2 已經改宗；原版 Paxos 裡這張遲到的 2a 無害，因為 a2 會拒收。
5. 變體 Phase2b(a1)：1 ≥ maxVBal[a1] = −1 ✓ ⇒ a1 投 ⟨1, x⟩。
6. 變體 Phase2b(a2)：1 ≥ maxVBal[a2] = −1 ✓（**原版會檢查 1 ≥ maxBal[a2] = 2，不成立，擋下**）⇒ a2 投 ⟨1, x⟩。**ChosenAt(1, x)**：{a1, a2} 在 ballot 1 全票 x。
7. Phase2b(a2)：2 ≥ maxVBal[a2] = 1 ✓ ⇒ 投 ⟨2, y⟩；Phase2b(a3)：2 ≥ −1 ✓ ⇒ 投 ⟨2, y⟩。**ChosenAt(2, y)**。chosen = {x, y}。

P2c 的破壞方式是**追溯**的：第 3 步發出 ⟨2, y⟩ 時 (a) 真實成立；第 6 步 a2 收下 ballot 1 的提案，讓「S 裡沒人接受過編號 < 2 的提案」**事後變假**。這正是 Lamport 那句「predicting future acceptances is hard」的全部份量：(a) 必須對未來成立，而唯一能對未來成立的方法是 promise＋兌現。maxBal 這條線不是最佳化，是 P2c 的 (a) 從快照升級成永久敘述的機制。工程鏡像：promise 沒落盤、重啟後 maxBal 歸零，行為跟這個變體一模一樣——「我答應過誰？沒印象。」

## 自我檢核

口頭回答，講得出來才算過：

1. 共識的 agreement／validity／termination 各說什麼？FLP 的一句話版是什麼？Paxos 對著 FLP 做了哪邊的取捨？
2. P2 → P2a → P2b → P2c 每一步把責任從誰下放給誰？驅動每次下放的共同困境是什麼（提示：誰觀測得到「被選定」）？
3. P2c 的 (a) 與 (b) 各對應 phase 1 回應的什麼情況？promise 在守哪一個？為什麼說 (a) 是對未來的敘述？
4. 為什麼任何兩個 quorum 必須相交？拿掉交集假設後分歧反例長什麼樣（口述題 1 的劇情）？
5. Paxos.tla 的 maxBal、maxVBal、maxVal 各扮演什麼角色？哪個是承諾線、哪兩個是最後一票？為什麼三者都必須單調不回退？
6. 「x 已被選定」在第幾類述語（狀態／action／時序，ch06）？為什麼定案的瞬間可以沒有任何節點知道？
7. Consensus → Voting → Paxos 三層各自抽象掉什麼？`THEOREM Spec => V!Spec` 這一行在主張什麼？（ch15 會把證明方法補上。）
8. duelling proposers 為什麼不違反 Spec？工程上的緩解手段是什麼？為什麼那個緩解就算失敗也不傷 safety？

## 延伸閱讀

- **Paxos Made Simple**（Leslie Lamport, 2001）：`https://lamport.azurewebsites.net/pubs/paxos-simple.pdf`（2026-06 驗證可下載）。本章 P1／P2／P2a／P2b／P2c 引文與 phase 1/2 推導全部出自 §2.2「Choosing a Value」，十四頁讀完整個不變量鏈；§2.4「Progress」是 duelling proposers 與 FLP 取捨的原始出處。
- **Consensus.tla／Voting.tla／Paxos.tla**（Lamport）：`https://github.com/tlaplus/Examples/blob/master/specifications/Paxos/Paxos.tla`（同目錄三份，2026-06 驗證存在）。把 Voting.tla 的 ShowsSafety 定理對照本章的 ⟨1⟩ 論證讀；Consensus.tla 裡那段 TLAPS 證明是 ch16 的預習材料。
- **Impossibility of Distributed Consensus with One Faulty Process**（M. Fischer, N. Lynch, M. Paterson, *JACM* 32(2), 1985）：`https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf`（2026-06 可得）。FLP 本尊。本書不證；讀第 1 節與主定理的敘述，把「非同步＋一個 crash ⇒ 不存在確定性又必然終止的共識」這句話的每個限定詞讀準就值回票價。
- **The Part-Time Parliament**（Lamport, *ACM TOCS* 1998）：`https://lamport.azurewebsites.net/pubs/pubs.html#lamport-paxos`（Lamport 出版品頁錨點）。寓言包裝的原始論文，當文化史讀——理解「Paxos 難」的名聲有一半是文體造成的，順便看 Lamport 在出版品頁上對這篇的自述。
