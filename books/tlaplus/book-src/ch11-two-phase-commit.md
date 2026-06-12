# ch11 — Two-Phase Commit：把你寫過的交易正式化

> **本章解決什麼問題**：ch10 手推了第一個協議，但那是單機記憶體裡的互斥；本章走進你的主場——分散式交易。我們對照 Lamport 的兩份原文 spec 精讀：TCommit 寫「交易承諾要什麼」，TwoPhase 寫「兩階段提交怎麼做」，而「TwoPhase 實作了 TCommit」這個主張本身就寫在 spec 的最後一行——這是 refinement 的活教材（正式機械見 ch15）。本章的核心論點：2PC 在 TM 故障時把 prepared 的 RM 卡死，這不是實作 bug，是「不犧牲一致性」的本質代價——我們會手推完整的 blocking scenario 證明給你看。「那能不能不卡？」由 ch12 的共識接手。

## 從你已知的出發

你大概沒親手寫過 two-phase commit，但你一定跟它的鬼魂打過交道。

MySQL 跑 `XA RECOVER`，列出一排卡在 prepared 的交易，文件管它們叫 **in-doubt transaction**：本地工作做完了、資源鎖著、日誌寫了「我可以 commit」，然後就停在那裡，等一個永遠沒有回來的協調者告訴它最後一步往哪走。DBA 半夜被叫起來，對著這排殭屍交易決定手動 commit 還是 rollback——那一刻，人類就是備援的 transaction manager。你排查過的「懸掛交易」「鎖被一筆不明交易抱著不放」，十之八九就是這個形狀。

另一條線索藏在你的結算 pipeline 的設計裡。跨服務的「扣庫存＋入帳」，你們沒有用分散式交易，而是用 SQS at-least-once 加 idempotent consumer 慢慢把最終一致性磨出來。這個「繞開」本身就是一張選票：團隊用腳投票表態 2PC 的代價——同步等待、協調者單點、卡住時全員抱鎖——付不起。至於補償交易（saga）那套繞法是另一本帳，本章不展開；本章要做的是把 2PC 這筆帳本身算清楚：它買到什麼、付出什麼、哪部分的代價是任何協議都躲不掉的。

本章的精讀材料是 Lamport 的兩份原文 spec：`TCommit.tla` 與 `TwoPhase.tla`——它們正是 Lamport 影片課程第 5、6 講的主角，與 Gray–Lamport 的論文同一脈絡，現存於 tlaplus/Examples（本章引用 2026-06 抓取的 master 版本，原文照貼）。兩份合計不到 250 行，卻是一組教科書級的示範：**先寫問題、再寫協議**。TCommit 是需求文件——「什麼結局算對」；TwoPhase 是設計文件——「誰在何時憑什麼資訊動作」。你天天在寫的 API 契約與其背後實作，就是這兩層關係的工程版。

配置沿全書基準：**1 個 TM（transaction manager，交易管理者）＋ 2 個 RM（resource manager，資源管理者）{r1, r2}**。

## TCommit：先寫「什麼叫對」，再操心「怎麼做到」

交易承諾（transaction commit）問題長這樣：一筆交易橫跨多個 RM——每個分庫、每個服務的本地交易各算一個。每個 RM 先各自做完本地工作，然後全體要對「這筆交易算不算數」收斂到同一個答案：**要嘛全 commit、要嘛全 abort**；而且只有在每個 RM 都表態過「我這邊可以 commit」之後，才允許任何人 commit。

Lamport 的 TCommit 模組把這個問題寫成 spec。開頭只有一個常數、一個變數：

```tla
------------------------------- MODULE TCommit ------------------------------
CONSTANT RM       \* The set of participating resource managers
VARIABLE rmState  \* `rmState[rm]' is the state of resource manager rm.
-----------------------------------------------------------------------------
TCTypeOK == 
  (*************************************************************************)
  (* The type-correctness invariant                                        *)
  (*************************************************************************)
  rmState \in [RM -> {"working", "prepared", "committed", "aborted"}]

TCInit ==   rmState = [rm \in RM |-> "working"]
  (*************************************************************************)
  (* The initial predicate.                                                *)
  (*************************************************************************)
```

沒有 TM、沒有訊息、沒有網路。整個世界只有一個函數 rmState ∈ [RM → {"working", "prepared", "committed", "aborted"}]：每個 RM 處在四個狀態之一。TCTypeOK 是第一個 invariant（ch08 講過：型別正確幾乎總是第一條），TCInit 說所有 RM 從 "working" 出發。單一 RM 的局部視角是一張小狀態圖：

```text
 ┌─────────┐  Prepare(r)   ┌──────────┐  Decide(r)：commit 分支    ┌───────────┐
 │ working │ ────────────→ │ prepared │ ─────────────────────────→ │ committed │
 └─────────┘               └──────────┘   guard：canCommit          └───────────┘
      │                         │
      │  Decide(r)：abort 分支  │
      │  guard：notCommitted    │
      ▼                         ▼
 ┌──────────────────────────────────┐
 │              aborted             │
 └──────────────────────────────────┘
```

四個狀態裡，"committed" 與 "aborted" 是終態（沒有出邊）；"working" 可以前進到 "prepared" 或直接放棄；"prepared" 只能往兩個終態走。讓這張圖「分散式起來」的是兩個 guard，它們定義在動作之前：

```tla
canCommit == \A rm \in RM : rmState[rm] \in {"prepared", "committed"}
  (*************************************************************************)
  (* True iff all RMs are in the "prepared" or "committed" state.          *)
  (*************************************************************************)

notCommitted == \A rm \in RM : rmState[rm] # "committed" 
  (*************************************************************************)
  (* True iff neither no resource manager has decided to commit.           *)
  (*************************************************************************)
```

（原文這行註解有個小筆誤——"neither no"——照引不改，你讀的是真檔案，不是教科書的淨化版。）

注意兩個 guard 的不對稱，這是整個問題的形狀：

- **commit 要全票**：canCommit 是全稱量詞——每一個 RM 都得在 {"prepared", "committed"} 裡。一票未到，誰都不准 commit。
- **abort 只要沒人越線**：notCommitted 只要求「還沒有任何人 commit」。abort 不需要全員同意——任何一個 RM 在表態前都可以單方面把整筆交易拖下水。

動作只有兩個：

```tla
Prepare(rm) == /\ rmState[rm] = "working"
               /\ rmState' = [rmState EXCEPT ![rm] = "prepared"]

Decide(rm)  == \/ /\ rmState[rm] = "prepared"
                  /\ canCommit
                  /\ rmState' = [rmState EXCEPT ![rm] = "committed"]
               \/ /\ rmState[rm] \in {"working", "prepared"}
                  /\ notCommitted
                  /\ rmState' = [rmState EXCEPT ![rm] = "aborted"]

TCNext == \E rm \in RM : Prepare(rm) \/ Decide(rm)
  (*************************************************************************)
  (* The next-state action.                                                *)
  (*************************************************************************)
-----------------------------------------------------------------------------
TCSpec == TCInit /\ [][TCNext]_rmState
```

Decide 是兩個析取：commit 分支要求自己已 prepared 且 canCommit 全域成立；abort 分支允許從 "working" 或 "prepared" 出發，只要 notCommitted。讀到這裡你應該停下來，問一個工程師的問題：**canCommit 是讀遍所有 RM 狀態的全稱條件——現實裡哪個節點讀得到？**

答案是：沒有任何節點讀得到，而且這正是重點。TCommit 不是協議，是**問題規格**。它假設了一個上帝視角，一步到位地說「當全員 prepared，某個 RM 可以變 committed」。它故意不回答「RM 怎麼知道全員 prepared」——那是協議的事。spec 的本分是先把「什麼叫對」釘死，再讓協議去操心「誰知道什麼」。你寫 API 契約時也是這樣：契約說「回 200 表示扣款成功且僅扣一次」，不說「內部用哪個鎖」。

最後是本章的主角性質與 spec 的主張：

```tla
TCConsistent ==  
  (*************************************************************************)
  (* A state predicate asserting that two RMs have not arrived at          *)
  (* conflicting decisions.                                                *)
  (*************************************************************************)
  \A rm1, rm2 \in RM : ~ /\ rmState[rm1] = "aborted"
                         /\ rmState[rm2] = "committed"

THEOREM TCSpec => [](TCTypeOK /\ TCConsistent)
```

TCConsistent 用 Unicode 寫出來：∀ rm1, rm2 ∈ RM : ¬(rmState[rm1] = "aborted" ∧ rmState[rm2] = "committed")——**不准有人 abort 的同時另一個人 commit**。這是一條狀態述語（沒有 prime），THEOREM 主張它（連同 TCTypeOK）在所有可達狀態成立，是 invariant。

順手把 2 RM 配置的帳算一下。型別狀態共 4² = 16 個；我把轉移圖完整窮舉過，**可達的恰是 12 個**。缺席的 4 個很有意思：⟨aborted, committed⟩ 與 ⟨committed, aborted⟩ 正是 TCConsistent 的反例；⟨committed, working⟩ 與 ⟨working, committed⟩ 則違反「有人 commit ⇒ 全員至少 prepared 過」——被 canCommit 的全稱 guard 擋在門外。更妙的是：TCTypeOK ∧ TCConsistent 在 TCommit 上**直接就是 inductive 的**（ch05 的詞彙：每一步都保持，不需要強化）——因為 guard 把一致性所需的條件原封不動寫了進去。這一步的證明手感很好，留給紙上推演的題 1；你會在那裡看到 guard 怎麼一個字一個字地把壞結局堵死。

## TwoPhase：把上帝視角拆成訊息

TwoPhase 模組開頭的註解是一份誠實的簡化聲明，值得整段照讀：

```tla
(***************************************************************************)
(* This specification describes the Two-Phase Commit protocol, in which a  *)
(* transaction manager (TM) coordinates the resource managers (RMs) to     *)
(* implement the Transaction Commit specification of module $TCommit$.  In *)
(* this specification, RMs spontaneously issue $Prepared$ messages.  We    *)
(* ignore the $Prepare$ messages that the TM can send to the               *)
(* RMs.\vspace{.4em}                                                       *)
(*                                                                         *)
(* For simplicity, we also eliminate $Abort$ messages sent by an RM when   *)
(* it decides to abort.  Such a message would cause the TM to abort the    *)
(* transaction, an event represented here by the TM spontaneously deciding *)
(* to abort.\vspace{.4em}                                                  *)
(*                                                                         *)
(* This specification describes only the safety properties of the          *)
(* protocol--that is, what is allowed to happen.  What must happen would   *)
(* be described by liveness properties, which we do not specify.           *)
(***************************************************************************)
```

（註解裡的 `$...$` 與 `\vspace` 是 Lamport 排版工具的標記，照引。）三條簡化逐一翻譯：

1. **RM 自發送出 Prepared**，TM 不用先送「請準備」的請求——少一輪訊息，不影響本質。
2. **RM 決定 abort 時不送訊息**——現實中這會觸發 TM abort；spec 裡直接讓 TM「自發地」abort，把「RM 拒絕」「逾時」「TM 自己反悔」等所有 abort 理由折疊成同一個非決定性動作。ch02 的老原則：建模「都可能」，不建模「為什麼」。
3. **只寫 safety**——這份 spec 從頭到尾不承諾任何事「終將發生」。記住這句話，它是後面兩個關鍵討論（訊息建模、crash 建模）的鑰匙。

變數從一個變成四個：

```tla
VARIABLES
  rmState,       \* $rmState[rm]$ is the state of resource manager RM.
  tmState,       \* The state of the transaction manager.
  tmPrepared,    \* The set of RMs from which the TM has received $"Prepared"$
                 \* messages.
  msgs           
```

rmState 與 TCommit 的同名同型別——不是巧合，是為了最後那行 INSTANCE（稍後揭曉）。tmState 是 TM 自己的狀態；tmPrepared 是 TM 收過誰的 Prepared 訊息。注意 tmPrepared 與 rmState 的本質差異：**rmState 是事實，tmPrepared 是 TM 的知識**。TM 不能讀 rmState——它只能從訊息裡拼湊世界，而訊息永遠是過去式。分散式系統的全部難處被這兩個變數的距離概括了。

而 msgs 的註解是全檔最值得偷學的一段建模技巧：

```tla
    (***********************************************************************)
    (* In the protocol, processes communicate with one another by sending  *)
    (* messages.  Since we are specifying only safety, a process is not    *)
    (* required to receive a message, so there is no need to model message *)
    (* loss.  (There's no difference between a process not being able to   *)
    (* receive a message because the message was lost and a process simply *)
    (* ignoring the message.)  We therefore represent message passing with *)
    (* a variable $msgs$ whose value is the set of all messages that have  *)
    (* been sent.  Messages are never removed from $msgs$.  An action      *)
    (* that, in an implementation, would be enabled by the receipt of a    *)
    (* certain message is here enabled by the existence of that message in *)
    (* $msgs$.  (Receipt of the same message twice is therefore allowed;   *)
    (* but in this particular protocol, receiving a message for the second *)
    (* time has no effect.)                                                *)
    (***********************************************************************)
```

拆開看，這段話做了兩個漂亮的推理：

- **msgs 只增不減，卻不是在假設網路可靠**——恰恰相反。因為只寫 safety，沒有任何動作「必須」發生；「訊息遺失導致收不到」與「訊息躺在那裡但對方永遠不去收」產生的行為集合一模一樣。既然區分不出來，就不建模。遺失被 stuttering 吃掉了（ch06 的設計紅利在這裡兌現）。
- **重複接收是允許的，但無害**——「收到訊息」被建模成「msgs 裡存在這則訊息」的 guard，同一則訊息可以觸發兩次接收動作。對這個協議無害，因為接收動作是冪等的：把已經 committed 的 RM 再 commit 一次，狀態不變。這就是你的 idempotent consumer 直覺，在 spec 裡的長相。

代價也要誠實記帳：這個便宜佔得成，**全靠 safety-only 這個前提**。哪天你要寫 liveness（「每個 RM 終將決定」），「收不到＝不想收」的等價立刻失效——你得把遺失、重送、逾時搬回模型裡，msgs 也許就得換成 bag 或帶上投遞狀態（ch04 吵過的 set vs bag 在這裡復活）。

剩下的宣告：

```tla
Message ==
  [type : {"Prepared"}, rm : RM]  \cup  [type : {"Commit", "Abort"}]
   
TPTypeOK ==  
  /\ rmState \in [RM -> {"working", "prepared", "committed", "aborted"}]
  /\ tmState \in {"init", "committed", "aborted"}
  /\ tmPrepared \subseteq RM
  /\ msgs \subseteq Message

TPInit ==   
  /\ rmState = [rm \in RM |-> "working"]
  /\ tmState = "init"
  /\ tmPrepared   = {}
  /\ msgs = {}
```

（引用時略去原檔各定義上方的註解框，程式本體照原文逐字。）Message 是 record 的集合（ch04）：Prepared 訊息帶寄件人欄位 rm，Commit 與 Abort 是 TM 的廣播、不帶欄位、全集合只有一份——所以 2 RM 配置下 Message 恰有 4 個元素：P(r1)、P(r2)、Commit、Abort（本章後面用這組縮寫，P(r) ≜ [type ↦ "Prepared", rm ↦ r]）。

七個動作，先看 TM 的三個：

```tla
TMRcvPrepared(rm) ==
  /\ tmState = "init"
  /\ [type |-> "Prepared", rm |-> rm] \in msgs
  /\ tmPrepared' = tmPrepared \cup {rm}
  /\ UNCHANGED <<rmState, tmState, msgs>>

TMCommit ==
  /\ tmState = "init"
  /\ tmPrepared = RM
  /\ tmState' = "committed"
  /\ msgs' = msgs \cup {[type |-> "Commit"]}
  /\ UNCHANGED <<rmState, tmPrepared>>

TMAbort ==
  /\ tmState = "init"
  /\ tmState' = "aborted"
  /\ msgs' = msgs \cup {[type |-> "Abort"]}
  /\ UNCHANGED <<rmState, tmPrepared>>
```

- **TMRcvPrepared(rm)**：guard 是「訊息存在」，效果是把 rm 記進自己的小本子 tmPrepared。注意 rmState 動都沒動——TM 收訊息是 TM 的事。
- **TMCommit**：tmPrepared = RM——小本子集滿了——TM 才能決定 commit，並廣播 Commit 訊息。這就是 canCommit 的協議版實作：**用「收齊的訊息」代替「讀遍全域狀態」**。
- **TMAbort**：只要還在 "init"，TM 隨時可以 abort 並廣播。沒有任何前提——這個非決定性吸收了所有現實裡的 abort 理由。

再看 RM 的四個：

```tla
RMPrepare(rm) == 
  /\ rmState[rm] = "working"
  /\ rmState' = [rmState EXCEPT ![rm] = "prepared"]
  /\ msgs' = msgs \cup {[type |-> "Prepared", rm |-> rm]}
  /\ UNCHANGED <<tmState, tmPrepared>>
  
RMChooseToAbort(rm) ==
  /\ rmState[rm] = "working"
  /\ rmState' = [rmState EXCEPT ![rm] = "aborted"]
  /\ UNCHANGED <<tmState, tmPrepared, msgs>>

RMRcvCommitMsg(rm) ==
  /\ [type |-> "Commit"] \in msgs
  /\ rmState' = [rmState EXCEPT ![rm] = "committed"]
  /\ UNCHANGED <<tmState, tmPrepared, msgs>>

RMRcvAbortMsg(rm) ==
  /\ [type |-> "Abort"] \in msgs
  /\ rmState' = [rmState EXCEPT ![rm] = "aborted"]
  /\ UNCHANGED <<tmState, tmPrepared, msgs>>
```

四個動作裡藏著本章最重要的一行 guard：**RMChooseToAbort 要求 rmState[rm] = "working"**。一旦 prepared，RM 就喪失單方面 abort 的權利——之後它的命運只剩兩條路：RMRcvCommitMsg 或 RMRcvAbortMsg，兩條都握在 TM 廣播的訊息手裡。「prepared」這個詞的真正語意就是**交出自決權**：我已經把「可以 commit」說出口，從此聽憑發落。blocking 的種子就埋在這行 guard 裡——先記住它，worked example 會回來收割。

收尾三行：

```tla
TPNext ==
  \/ TMCommit \/ TMAbort
  \/ \E rm \in RM : 
       TMRcvPrepared(rm) \/ RMPrepare(rm) \/ RMChooseToAbort(rm)
         \/ RMRcvCommitMsg(rm) \/ RMRcvAbortMsg(rm)
-----------------------------------------------------------------------------
TPSpec == TPInit /\ [][TPNext]_<<rmState, tmState, tmPrepared, msgs>>

THEOREM TPSpec => []TPTypeOK
```

狀態空間的帳：上界是 4²（rmState）× 3（tmState）× 2²（tmPrepared）× 2⁴（msgs）= 3072；實際可達 **56 個**（這兩個數字我把 2 RM 的轉移圖完整窮舉後數出來的，上界與前兩層展開你可以在紙上自行複核）。而原檔末尾的註解給了一個更大配置的數字，照引：

```tla
(***************************************************************************)
(* The two theorems in this module have been checked with TLC for six      *)
(* RMs, a configuration with 50816 reachable states, in a little over a    *)
(* minute on a 1 GHz PC.                                                   *)
(***************************************************************************)
```

從 2 個 RM 的 56 到 6 個 RM 的 50,816——state explosion 的手感（ch09）。也注意 Lamport 的措辭：theorems **checked with TLC for six RMs**。有限配置的窮舉不是任意 RM 數的證明；真正的證明欠著，ch14 還。

## 兩層關係：實作定理就寫在 spec 裡

TwoPhase.tla 的最後一段，是本書反覆預告的 refinement 第一次以原文現身：

```tla
(***************************************************************************)
(* We now assert that the Two-Phase Commit protocol implements the         *)
(* Transaction Commit protocol of module $TCommit$.  The following         *)
(* statement defines $TC!TCSpec$ to be formula $TCSpec$ of module           *)
(* $TCommit$.  (The TLA$^+$ \textsc{instance} statement is used to rename  *)
(* the operators defined in module $TCommit$ avoids any name conflicts     *)
(* that might exist with operators in the current module.)                 *)
(***************************************************************************)
TC == INSTANCE TCommit 

THEOREM TPSpec => TC!TCSpec
```

兩行，一個世界觀。`TC == INSTANCE TCommit` 把 TCommit 模組整份搬進來，所有名字前掛 `TC!`；TCommit 的 CONSTANT RM 與 VARIABLE rmState 用本模組的同名者代換（同名時代換是隱式的；改名要用 WITH，正式語意見 ch15）。於是 `TC!TCSpec` 就是「用 TwoPhase 的 rmState 講出來的 TCSpec」。然後：

**THEOREM TPSpec ⇒ TC!TCSpec**——TwoPhase 的每一條合法 behavior，都是 TCommit 允許的 behavior。實作正確＝一條蘊涵式（ch06 埋的伏筆原句兌現）。

```text
┌────────────────────────────────────────────────────┐
│ TCommit（問題層）                                  │
│ 變數：只有 rmState                                 │
│ 說的是「什麼結局合法」                             │
└────────────────────────────────────────────────────┘
           ▲
           │  THEOREM TPSpec => TC!TCSpec
           │  TwoPhase 的每條行為，遮住 TM 與訊息
           │  之後，都是 TCommit 允許的行為
┌────────────────────────────────────────────────────┐
│ TwoPhase（協議層）                                 │
│ 變數：rmState、tmState、tmPrepared、msgs           │
│ 說的是「誰在何時憑什麼資訊動作」                   │
└────────────────────────────────────────────────────┘
```

這條蘊涵為什麼有機會成立？把鏡頭只對準 rmState，逐動作對照——TwoPhase 的每一步，在「只看 rmState 的觀察者」眼裡是什麼：

| TwoPhase 的一步 | 在 TCommit 眼裡 |
|---|---|
| RMPrepare(r) | Prepare(r) |
| RMChooseToAbort(r) | Decide(r) 的 abort 分支 |
| RMRcvCommitMsg(r)，r 原為 "prepared" | Decide(r) 的 commit 分支 |
| RMRcvCommitMsg(r)，r 已為 "committed" | stuttering（rmState 沒動） |
| RMRcvAbortMsg(r)，r 原為 "working" 或 "prepared" | Decide(r) 的 abort 分支 |
| RMRcvAbortMsg(r)，r 已為 "aborted" | stuttering |
| TMRcvPrepared(r)、TMCommit、TMAbort | stuttering |

TM 的三個動作只碰 tmState、tmPrepared、msgs——對只看 rmState 的觀察者，這些步什麼都沒發生。**ch06 的時鐘寓言在此完整重演**：TwoPhase 是時分時鐘，TCommit 是小時鐘；TM 與訊息是「分針」，stuttering 條款讓「實作比規格多動很多步」不構成違約。如果當初 TCSpec 寫成裸的 □TCNext（每步都得真的動 rmState），這條 THEOREM 一個字都成立不了。

但這張表沒有看起來那麼便宜。每一格都偷偷依賴「可達狀態的事實」：RMRcvCommitMsg 要對映到 Decide 的 commit 分支，得先確認那一刻 canCommit 成立——也就是「Commit 訊息在 msgs 裡時，全員必在 {"prepared", "committed"}」。這句話憑什麼？憑一串環環相扣的可達性事實：Commit ∈ msgs ⇒ tmState = "committed" ⇒ tmPrepared = RM ⇒ 人人送過 Prepared ⇒ 沒有人還在 "working"，也沒有人 aborted。這串鏈條正是 ch14 要逐節鍛造的強化不變量；把這張表升格為定理的機械（refinement mapping），是 ch15 的主題。本章先讓你看見：**兩層關係不是文學比喻，是寫在 spec 裡、可以被證明的數學主張。**

## Blocking：手推一場 TM 之死

現在來驗證本章標題裡的指控。先把一件事說清楚，免得你帶著錯誤的期待讀原文：

**Lamport 的 TwoPhase.tla 沒有建模 TM crash——原版裡找不到任何 crash 動作。**這不是疏漏，是 safety-only 的直接後果：spec 從不要求任何人動作，所以「TM 從此再也不動」本來就是合法行為——一條 TM 收齊 prepared 之後永遠 stuttering 下去的 behavior，原版 TPSpec 照單全收。換句話說，**blocking 場景在原版 spec 裡早就存在**，crash 與「永遠拖延」在行為集合上不可區分，正如訊息遺失與「永遠不收」不可區分。同一個建模哲學，用了兩次。

那為什麼本章還要加 crash 動作？因為「卡住」是 liveness 層的指控，要把它說得字字有據，你需要能說出：「**即使**給足 fairness，prepared 的 RM 也走不出去」。ch07 教過，fairness 只能拯救 enabled 的動作——WF 說「持續 enabled 就終將發生」。對永遠 stuttering 的 TM，加上 WF(TMCommit) 就能逼它動起來，blocking 像是被「治好」了——但這是假象，治好的只是「懶」，不是「死」。要表達「死」，必須讓 TM 的動作從某一刻起**永遠不再 enabled**，這樣任何 fairness 都無計可施。這就得在狀態裡動手腳。

於是，擴充版（**以下全部是本書外加，非 Lamport 原文**）：

```tla
\* ---- 本書擴充：TM crash（非 Lamport 原文）----

TMCrash == /\ tmState = "init"
           /\ tmState' = "crashed"
           /\ UNCHANGED <<rmState, tmPrepared, msgs>>

TPCrashNext == TPNext \/ TMCrash

TPCrashSpec == TPInit /\ [][TPCrashNext]_<<rmState, tmState, tmPrepared, msgs>>
```

清點改了什麼、沒改什麼：

- **變數一個都沒加、沒刪**。tmState 的值域多一個 "crashed"（TPTypeOK 的第二行要對應改成 `tmState \in {"init", "committed", "aborted", "crashed"}`），其餘三個變數的型別原封不動。
- **TMCrash 不碰 rmState、tmPrepared、msgs**。所以它在 TCommit 眼裡是 stuttering——上一節那張對照表加一列就好，兩層關係毫髮無傷；ch14 對 TCConsistent 的歸納證明裡，TMCrash 的 case 也是平凡的（不動 rmState 的步打不破只談 rmState 的述語）。
- **只允許從 "init" crash**。從 "committed"/"aborted" crash 對 safety 沒有新內容（決定已經躺在 msgs 裡，RM 照樣收得到），徒增狀態；最小擴充就夠演示。
- 建模的是 **crash-stop**：倒了就不再起來。真實 DB 的 TM 重啟後會讀災後日誌續傳——那是縮短 blocking 時間的工程手段，不在本章模型裡（它消除不了 blocking 視窗本身）。
- 還有一個誠實聲明：原文的 TMCommit 把「做決定」與「廣播 Commit」綁成原子的一步，所以教科書裡更細的「決定已寫進日誌、訊息還沒出門就倒了」的窗口，在這個抽象層**不存在**。我們的 crash 窗口是「收齊 prepared、尚未做決定」——對演示 blocking 的本質，足夠了。

擴充後 2 RM 的可達狀態從 56 長到 72（同樣窮舉複核過）。值得一提：原版 56 個可達狀態裡，**每個狀態都至少有一個 enabled 的動作**（哪怕只是把同一則訊息再收一次），逐狀態的「卡死檢查」會全綠；擴充版裡出現了 9 個「零後繼」狀態，其中 8 個含有被永遠卡住的 prepared RM（另 1 個是全員已 abort、單純無事可做）。現在，手推最痛的那一條。

### Worked example：收齊 prepared 之後，TM 倒下

縮寫沿用：P(r) ≜ [type ↦ "Prepared", rm ↦ r]，Commit 與 Abort 訊息記作 C、A。六個狀態、五步：

| 狀態 | rmState[r1] | rmState[r2] | tmState | tmPrepared | msgs |
|---|---|---|---|---|---|
| s₀ | working | working | init | {} | {} |
| s₁ | prepared | working | init | {} | {P(r1)} |
| s₂ | prepared | prepared | init | {} | {P(r1), P(r2)} |
| s₃ | prepared | prepared | init | {r1} | {P(r1), P(r2)} |
| s₄ | prepared | prepared | init | {r1, r2} | {P(r1), P(r2)} |
| s₅ | prepared | prepared | crashed | {r1, r2} | {P(r1), P(r2)} |

逐步驗證，unprimed 用步前狀態、primed 用步後狀態（手法同 ch06 的 worked example）：

**起點**：s₀ 滿足 TPInit？rmState 全 "working" ✓；tmState = "init" ✓；tmPrepared = {} ✓；msgs = {} ✓。過。

**步 1：⟨s₀, s₁⟩ 是 RMPrepare(r1)**。
- rmState[r1] = "working"？s₀ 裡是 ✓
- rmState′ = [rmState EXCEPT ![r1] = "prepared"]？s₁：r1 ↦ prepared，r2 ↦ working（沒動）✓
- msgs′ = msgs ∪ {P(r1)}？{} ∪ {P(r1)} = {P(r1)} ✓
- UNCHANGED ⟨tmState, tmPrepared⟩？"init" 與 {} 原封不動 ✓

**步 2：⟨s₁, s₂⟩ 是 RMPrepare(r2)**。
- rmState[r2] = "working"？s₁ 裡是 ✓
- rmState′：只有 r2 那格改成 "prepared" ✓
- msgs′ = {P(r1)} ∪ {P(r2)} = {P(r1), P(r2)} ✓
- UNCHANGED ⟨tmState, tmPrepared⟩ ✓

**步 3：⟨s₂, s₃⟩ 是 TMRcvPrepared(r1)**。
- tmState = "init"？✓
- P(r1) ∈ msgs？P(r1) ∈ {P(r1), P(r2)} ✓
- tmPrepared′ = tmPrepared ∪ {r1} = {} ∪ {r1} = {r1} ✓
- UNCHANGED ⟨rmState, tmState, msgs⟩？三者在 s₃ 與 s₂ 相同 ✓

**步 4：⟨s₃, s₄⟩ 是 TMRcvPrepared(r2)**。
- tmState = "init"？✓
- P(r2) ∈ msgs？✓
- tmPrepared′ = {r1} ∪ {r2} = {r1, r2} ✓
- UNCHANGED ⟨rmState, tmState, msgs⟩ ✓

在 s₄ 停一拍。tmPrepared = {r1, r2} = RM——TM 的小本子集滿了，**TMCommit 的兩個 guard 同時亮起**。歷史在這裡分岔：在某個平行世界，下一步是 TMCommit，皆大歡喜。在我們要看的世界：

**步 5：⟨s₄, s₅⟩ 是 TMCrash（擴充動作）**。
- tmState = "init"？✓
- tmState′ = "crashed"？✓
- UNCHANGED ⟨rmState, tmPrepared, msgs⟩？✓

現在站在 s₅，把**所有**動作的 guard 逐一過堂：

| 動作 | guard | 在 s₅ 為什麼不成立 |
|---|---|---|
| TMRcvPrepared(r) | tmState = "init" | tmState = "crashed" |
| TMCommit | tmState = "init" ∧ tmPrepared = RM | tmPrepared = RM 明明成立，但 tmState ≠ "init"——死在離終點一步 |
| TMAbort | tmState = "init" | tmState = "crashed" |
| TMCrash | tmState = "init" | 死人不能再死一次 |
| RMPrepare(r) | rmState[r] = "working" | r1、r2 都是 "prepared" |
| RMChooseToAbort(r) | rmState[r] = "working" | 同上——prepared 者無權回頭 |
| RMRcvCommitMsg(r) | [type ↦ "Commit"] ∈ msgs | Commit 從未送出 |
| RMRcvAbortMsg(r) | [type ↦ "Abort"] ∈ msgs | Abort 從未送出 |

八類動作，零個 enabled。s₅ 之後唯一合法的延續是無限 stuttering：**r1 與 r2 的 rmState 永遠停在 "prepared"**。鎖抱著、資源佔著、誰也不會來救。這就是 blocking（卡死）：協議在無人違規的情況下，永遠無法前進。

再驗最後一件事：**TCConsistent 全程成立嗎？**檢查 s₀ 到 s₅：六個狀態裡沒有任何 rmState 值是 "committed" 或 "aborted"，所以對任何一對 rm1、rm2，「rmState[rm1] = "aborted" ∧ rmState[rm2] = "committed"」兩個合取項都為假，否定為真——TCConsistent 在每個狀態都成立，而且成立得很「空」（ch03 的 vacuous truth：連壞事的原料都沒生出來）。

把這兩個結論並排，就是本章的核心句：

> **blocking 不是不一致。2PC 在 TM 死亡時犧牲的是進展（liveness），分毫未動的是一致性（safety）。**你的監控不會跳出 invariant violation——不會有帳對不上、不會有一邊 commit 一邊 abort——只會有 P99 緩緩爬升、鎖等待逐漸堆積、`XA RECOVER` 列表慢慢變長。最安靜的故障模式，往往最難排查。

### 為什麼 r2 不能自己決定

盯著 s₅ 你一定想問：r2 等了這麼久，自己 abort 掉、把鎖放了，不行嗎？RMChooseToAbort 那行 `rmState[rm] = "working"` 的 guard，放寬成 prepared 也能 abort，不就解套了？

不行，而且「不行」可以論證。考慮另一個世界 B：前四步 s₀ 到 s₄ 一模一樣，但第五步不是 TMCrash 而是 TMCommit（tmState ↦ "committed"、msgs 多了 C），第六步 RMRcvCommitMsg(r1)（r1 ↦ "committed"）。現在比較兩個世界裡 **r2 的局部視圖**：

- 我們的世界 s₅：rmState[r2] = "prepared"，r2 收到過的訊息：無。
- 世界 B 的第六個狀態：rmState[r2] = "prepared"，r2 收到過的訊息：無（C 在 msgs 裡，但 r2 還沒收）。

一模一樣。**任何只憑 r2 本地資訊的決策規則，在兩個世界必然做出同一件事。**如果這條規則讓 r2 在我們的世界 abort（解掉 blocking），它就也會讓 r2 在世界 B abort——而世界 B 裡 r1 已經 committed，於是 ⟨committed, aborted⟩，TCConsistent 陣亡。要 safety，r2 就只能等；要不等，就賠上 safety。兩個無法區分的世界、一條必須二選一的規則——這個論證形態你會在 ch12 再遇到一次，它的完全體叫 FLP 不可能定理（那裡只給一句話版，本書不證）。

這就是「blocking 是本質不是 bug」的準確含義：**prepared 狀態的資訊結構決定了 RM 不可能安全地自救**。工程上所有真實止血手段都是在這個鐵框內騰挪：XA 的 heuristic decision（人工拍板）是在 spec 之外引入第二個決策者，等於主動放棄 TCConsistent 的保證、事後對帳——所以各家 DB 才會有專門的錯誤狀態描述「兩邊拍得不一樣」的下場；TM 寫災後日誌、重啟續傳，是縮短視窗，不是消滅視窗。真正消滅它，得換協議——往下看。

## 為什麼修不好：3PC，以及 Paxos Commit 的伏筆

教科書的標準續集是 **three-phase commit（3PC）**，出自 Skeen 1981 年的論文（見延伸閱讀）。思路順著上面的論證走：blocking 的根源是「有人可能已經 commit，而我不知道」，那就在 prepared 與 committed 之間再插一個階段——TM 先廣播「全員已 prepared，準備 commit」（pre-commit），收齊回應後才讓人真正 commit。這樣一來，「已有人 commit」蘊涵「全員都到過 pre-commit」，prepared 但沒見過 pre-commit 的 RM 就能放心 abort；搭配逾時與互詢，在 crash-stop 加同步網路的假設下確實能做到非阻塞。

那為什麼 2026 年的你在生產環境裡幾乎看不到 3PC？因為它買回 liveness 用的貨幣是 **safety 的假設**。3PC 的非阻塞性押在「故障偵測準確」與「網路不分割」上：一旦發生 network partition，兩個分區各自湊出「對方都死了」的結論，一邊依規則推進 commit、另一邊依規則推進 abort——TCConsistent 直接破裂。2PC 把 partition 熬成卡死，3PC 把 partition 變成不一致；對資料系統，後者通常是更貴的災難。一句話總結：**3PC 沒有消滅那道二選一的牆，只是換了撞牆的姿勢**（主流資料庫與訊息系統至今未採用 3PC 作為承諾協議，2026-06）。

真正的出路要再等二十多年。Gray 與 Lamport 在〈Consensus on Transaction Commit〉（ACM TODS, 2006）給出的答案是：別修補 TM，**把「TM 的那個決定」本身交給容錯共識**——用 2F+1 個協調者跑 Paxos，F 個倒下仍能推進，這就是 Paxos Commit；而且論文指出，2PC 恰好是它退化到 F = 0 的特例（Lamport 自己的話：「Two-Phase Commit is the trivial version of Paxos Commit that tolerates zero faults」）。共識憑什麼能容錯、quorum 怎麼擋住分歧，是 ch12 的主題——你會發現同一個目錄裡躺著 PaxosCommit.tla，等著被精讀。

## 陷阱與防禦

| 故障模式 | 它怎麼給你假安全感 | 怎麼自我察覺 |
|---|---|---|
| 把 blocking 當 bug 想修 | 「加個逾時就好了」——變體看起來能動，demo 也順利，因為測試裡 TM 沒有恰好死在收齊 prepared 之後 | 先問：prepared 的 RM 比 crash 前多了什麼**資訊**？沒有新資訊就沒有新決定。任何本地逾時規則都過不了「兩個無法區分的世界」這一關（紙上推演題 3） |
| 逐狀態的卡死檢查全綠＝不會卡 | 原版 2 RM 的 56 個可達狀態個個都有 enabled 動作，deadlock check 一片綠；但「TM 永遠 stuttering」的 blocking 行為照樣合法 | blocking 是 liveness 層的指控，要用時序性質（◇「人人有決定」）加 fairness 去問（ch07），deadlock check 根本看不見它 |
| 把「msgs 只增不減」讀成「假設網路可靠」 | 於是你以為這份 spec 比現實樂觀，對它的結論打折 | 恰恰相反：safety-only 之下「收不到」與「不去收」等價，遺失被 stuttering 吃掉。要驗的是你自己：這份 spec 哪裡承諾過「終將」？（原文明說 only safety） |
| 把 tmPrepared 當成 RM 的即時狀態 | 「TM 知道 r1 prepared」聽起來像讀到了 rmState[r1] | tmPrepared 是訊息的影子——分散式裡「知道」永遠是過去式。寫 spec 時對每個 guard 問：這個節點**物理上**讀得到這個條件嗎？讀不到的，就得有訊息把它送過來 |
| 沒讀簡化聲明就拿 spec 對教科書 | 「教科書說 TM 會先送 Prepare 請求、RM abort 會通知 TM，這 spec 都沒有，是不是錯了」 | 精讀任何 spec 先讀註解裡的「我忽略了什麼」。對 spec 的批評，先檢查是不是人家開頭就聲明過的抽象（本檔開頭那 17 行就是清單） |
| 有限配置 TLC 全綠＝定理證完了 | 「2 RM 過了、6 RM 的 50,816 個狀態也過了，還能有錯？」 | 窮舉只覆蓋跑過的參數；THEOREM 主張的是任意 RM 集合。從「TLC 檢查過」到「證明了」之間隔著 ch14 的歸納不變量與 ch16 的機器證明——Lamport 在檔尾用詞是 checked，不是 proved |

## 紙上推演

### 題 1：TCConsistent 的關鍵歸納步（[20 分鐘] ★★）

在 TCommit 上證明歸納步的 Decide 部分：**設步前狀態滿足 TCTypeOK ∧ TCConsistent，且這一步 ⟨s, t⟩ 滿足 Decide(r)（對某個 r ∈ RM），證明 t 滿足 TCConsistent**。用 ⟨1⟩ 層級格式（ch05），對 Decide 的兩個析取分案。寫完後回答：哪一個 case 用到了步前的 TCConsistent？哪一個其實沒用到？

### 推演解答

⟨1⟩1. Decide(r) 是兩個析取，分案討論。
⟨1⟩2. **案一（commit 分支）**：guard 含 rmState[r] = "prepared" 與 canCommit，效果是 rmState′ = [rmState EXCEPT ![r] = "committed"]。
  ⟨2⟩1. canCommit ＝ ∀ rm ∈ RM : rmState[rm] ∈ {"prepared", "committed"}，所以步前**沒有任何 RM 處於 "aborted"**（由 TCTypeOK，四個值只能取一）。
  ⟨2⟩2. t 與 s 只差 r 那格變成 "committed"；這一步沒有任何 RM 變成 "aborted"。
  ⟨2⟩3. 所以 t 裡也沒有任何 RM 是 "aborted"。TCConsistent 的內層是 ¬(rmState[rm1] = "aborted" ∧ rmState[rm2] = "committed")；對任何 rm1，第一個合取項在 t 為假，整個否定為真。案一成立。
⟨1⟩3. **案二（abort 分支）**：guard 含 rmState[r] ∈ {"working", "prepared"} 與 notCommitted，效果是 r 變 "aborted"。
  ⟨2⟩1. notCommitted ＝ ∀ rm ∈ RM : rmState[rm] ≠ "committed"，所以步前沒有任何 RM 是 "committed"。
  ⟨2⟩2. t 與 s 只差 r 變 "aborted"；沒有任何 RM 變成 "committed"，所以 t 裡也沒有 "committed"。
  ⟨2⟩3. 內層否定式的第二個合取項在 t 對任何 rm2 為假，TCConsistent′ 成立。案二成立。
⟨1⟩4. Q.E.D. 兩案蓋滿 Decide(r) 的兩個析取。∎

回答附問：**兩個 case 都沒用到步前的 TCConsistent**——guard 自己就夠強：canCommit 直接排除 aborted 的存在，notCommitted 直接排除 committed 的存在。真正用到歸納假設的是 Prepare(r) 那個 case（這裡補完整個歸納步）：Prepare 只把 "working" 改成 "prepared"，既不新增 "aborted" 也不新增 "committed"，所以**步前沒有違規配對、步後也不會有**——「步前沒有」正是歸納假設。這個「guard 把不變量寫在臉上」的奢侈，是規格層的特權：TCommit 的 guard 讀得到全域。下一題你會看到，失去上帝視角的 TwoPhase 沒有這種好日子。

### 題 2：TwoPhase 上的壞前驅（[15 分鐘] ★★）

考慮 TwoPhase 的狀態 s_bad ≜ ⟨rmState = (r1 ↦ "committed", r2 ↦ "working"), tmState = "init", tmPrepared = {}, msgs = {}⟩。

(a) 驗證 s_bad 滿足 TPTypeOK 與 TCConsistent。
(b) 找出一個在 s_bad enabled 的動作，使一步之後 TCConsistent 被打破。
(c) 由兩條 THEOREM 串起來，TCConsistent 是 TwoPhase 的 invariant——這跟 (b) 矛盾嗎？
(d) 寫出一條「可達狀態的事實」，把 s_bad 排除在可達集之外。

### 推演解答

(a) 型別逐項：rmState 是 RM → 四值集合的函數 ✓；tmState = "init" ∈ {"init", "committed", "aborted"} ✓；tmPrepared = {} ⊆ RM ✓；msgs = {} ⊆ Message ✓。TCConsistent：有 "committed"（r1）但沒有任何 "aborted"，否定式對每一對成立 ✓。

(b) RMChooseToAbort(r2)：guard rmState[r2] = "working" ✓ enabled。走一步：rmState′ = (r1 ↦ "committed", r2 ↦ "aborted")。取 rm1 = r2、rm2 = r1，內層合取兩項全真——TCConsistent′ 陣亡。

(c) 不矛盾，而且這正是 ch05 點過名的現象：**TCConsistent 是 invariant（所有可達狀態都成立），但在 TwoPhase 上不是 inductive 的**。invariant 主張的範圍是可達狀態；歸納步檢查的卻是「所有滿足述語的狀態」——s_bad 滿足 TCConsistent 卻不可達，它就是歸納證明會卡住的「壞前驅」。想用歸納法證 TCConsistent，就得把述語強化到足以排除 s_bad 這類狀態。

(d) 缺的事實是一條鏈：rmState[r] = "committed" ⇒ [type ↦ "Commit"] ∈ msgs（RM 只能因收到 Commit 而 commit）⇒ tmState = "committed"（Commit 只由 TMCommit 送出）⇒ tmPrepared = RM（TMCommit 的 guard）⇒ 每個 RM 都送過 Prepared ⇒ 沒有 RM 還在 "working"。s_bad 在第一節就斷裂：r1 committed 但 msgs = {}。把這條鏈逐節寫成合取、補進不變量、再對七個動作逐一重跑歸納步——那是 ch14 的完整 worked example，全書證明的高峰之一。

### 題 3：「看似修好 blocking」的變體（[25 分鐘] ★★★）

同事提案：「prepared 的 RM 等太久就自行放棄」，加入動作

```tla
RMTimeoutAbort(rm) == /\ rmState[rm] = "prepared"
                      /\ rmState' = [rmState EXCEPT ![rm] = "aborted"]
                      /\ UNCHANGED <<tmState, tmPrepared, msgs>>
```

並把它加進 TPNext。(a) 找出一條打破 TCConsistent 的完整 trace（提示：7 步，不需要 TMCrash）。(b) 用「兩個世界」的語言說明為什麼**任何**只憑 RM 本地資訊的解卡規則都有同型反例。(c) 改良案「cooperative termination」——prepared 的 RM 互相詢問，誰見過決定就轉告誰——能不能消除 blocking？

### 推演解答

(a) 反例 trace（每步都可逐 guard 驗證，手法同 worked example）：

| 步 | 動作 | 步後關鍵狀態 |
|---|---|---|
| 1 | RMPrepare(r1) | rmState = (p, w)，msgs = {P(r1)} |
| 2 | RMPrepare(r2) | rmState = (p, p)，msgs = {P(r1), P(r2)} |
| 3 | TMRcvPrepared(r1) | tmPrepared = {r1} |
| 4 | TMRcvPrepared(r2) | tmPrepared = {r1, r2} |
| 5 | TMCommit | tmState = "committed"，msgs 多了 C |
| 6 | RMRcvCommitMsg(r1) | rmState = (c, p) |
| 7 | RMTimeoutAbort(r2) | rmState = (c, a) —— TCConsistent 卒 |

第 7 步的 guard 完全合法：rmState[r2] = "prepared" ✓。Commit 訊息躺在 msgs 裡，但「躺在那裡」不等於「r2 收到了」——r2 的逾時敲在 Commit 抵達之前，這正是現實裡 timeout 永遠的命門：**它區分不了「死了」跟「慢了」**。

(b) 任何解卡規則 D，若只讀 r2 的本地資訊（自身 rmState、自己收過的訊息），則在「TM 於 s₄ 後 crash」與「TM 已 commit、Commit 訊息尚未送達 r2」兩個世界裡，r2 的本地視圖逐位元相同，D 必然輸出同一個決定。D 若決定 abort，世界 B 給出 ⟨committed, aborted⟩，破 safety；D 若決定 commit，對稱地考慮「TM 已 abort、Abort 尚未送達」的世界（TMAbort 隨時可發生），同樣破 safety；D 若決定等待——那就是 blocking 本身。三條路，無一倖免。這不是 2PC 寫壞了，是 prepared 狀態的資訊結構天生如此。

(c) cooperative termination 不破 safety——「轉告已知的決定」傳播的是真話，TCConsistent 無虞；它也確實縮小 blocking 視窗：只要**任何一個** RM 見過 Commit 或 Abort，全體就能脫困。但對 worked example 的 s₅ 它無能為力：全員 prepared、TM 在廣播前死亡，問遍所有人，所有人都只知道「我 prepared 了」——資訊總量為零，規則 (b) 照樣適用。結論：視窗變窄、本質還在，而且多付一輪互詢訊息。3PC 沿這條思路再往前一步，把代價押到了 partition 下的 safety（見本章 3PC 一節）。真正出線的路是把決定本身複製成多數決——ch12。

## 自我檢核

口頭回答，講得出來才算過：

1. TCommit 與 TwoPhase 各自在描述什麼？為什麼 Lamport 把它們寫成兩個模組，而不是一份「完整的 2PC spec」？這個分層對應你工作裡的什麼東西？
2. canCommit 與 notCommitted 是誰的視角？為什麼說 TCommit 不是可執行的協議？TwoPhase 分別用什麼機制替代這兩個 guard？
3. msgs 為什麼可以只增不減？這個建模選擇依賴哪個前提？如果要給 TwoPhase 加 liveness 性質，訊息層得補回哪些東西？
4. 原版 TwoPhase.tla 沒有 crash 動作，為什麼 blocking 場景仍然「在」spec 裡？本章的 TMCrash 擴充到底買到了什麼（提示：ENABLED 與 fairness 的關係）？
5. 不看書，手講一遍 worked example：crash 的窗口開在哪兩個事件之間？crash 之後八類動作各為什麼 disabled？TCConsistent 為什麼全程成立？
6. RMChooseToAbort 的 guard 為什麼是 "working" 而不是 {"working", "prepared"}？放寬之後，哪條 7 步 trace 會打破 TCConsistent？
7. 「blocking 是本質不是 bug」的論證核心是哪兩個無法區分的世界？這個論證形態與 ch12 要遇到的哪個不可能結果同源？
8. `TC == INSTANCE TCommit` 與 `THEOREM TPSpec => TC!TCSpec` 兩行各在做什麼？TwoPhase 的哪些步在 TCommit 眼裡是 stuttering？這件事靠 ch06 的哪個設計決定才成立？

## 延伸閱讀

- **TCommit.tla 原文**：`https://github.com/tlaplus/Examples/blob/master/specifications/transaction_commit/TCommit.tla`。本章引用的問題層 spec 全文（66 行）。讀的重點：註解怎麼把每個定義的「為什麼」講完。
- **TwoPhase.tla 原文**：`https://github.com/tlaplus/Examples/blob/master/specifications/transaction_commit/TwoPhase.tla`。協議層 spec 全文；同目錄還有 PaxosCommit.tla——讀完 ch12 回來精讀它，會有「原來如此」的時刻。
- **Jim Gray & Leslie Lamport, “Consensus on Transaction Commit”**, *ACM Transactions on Database Systems*, Vol. 31, No. 1（2006），pp. 133–160：`https://dl.acm.org/doi/10.1145/1132863.1132867`（Microsoft Research 頁面有 PDF）。兩份 spec 的論文出處；讀第 3–4 節看 2PC 如何被定位成 Paxos Commit 的 F = 0 特例。
- **Dale Skeen, “Nonblocking Commit Protocols”**, *Proceedings of ACM SIGMOD 1981*：`https://dl.acm.org/doi/10.1145/582318.582339`。3PC 的原典，給出了非阻塞承諾協議的充要條件——讀它是為了看清那些條件在 partition 下如何失效。
- **TLA+ Video Course 第 5、6 講**（Lamport 親自錄製）：`https://lamport.azurewebsites.net/video/videos.html`。第 5 講 “Transaction Commit” 與第 6 講 “Two-Phase Commit” 正是本章兩份 spec 的作者導讀，各約 20 餘分鐘；搭配本章手推服用效果最佳。
