# ch06 — 動作邏輯：TLA 的核心設計

> **本章解決什麼問題**：ch02 把系統看成狀態機，Part II 磨利了邏輯、集合與歸納，但到目前為止你都是用白話加圖在描述「一步」。本章引入 TLA 的核心發明——動作（action）：用含 prime 記號的述語，精確寫出「一步前後的關係」，再把整個系統壓縮成一條公式 Init ∧ □[Next]_vars。讀完本章，你能逐字讀懂這條公式、手追一條 behavior、並理解「允許不動」（stuttering）為什麼是刻意設計而不是缺陷。這是 Part III 的第一章：ch07 補上時序邏輯與 fairness，ch08 組裝完整的 spec，ch09 講機器怎麼自動檢查。

你現在的位置：

```text
┌──────────────────────────────────────────────────────────────────┐
│ Part I    為什麼                                                 │
│   ch01 測試的極限 → ch02 狀態機                                  │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part II   數學地基                                               │
│   ch03 邏輯 → ch04 集合 → ch05 歸納                              │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part III  TLA+ 與時序邏輯                                        │  ← 你在這裡
│   ch06 動作邏輯 → ch07 時序邏輯 → ch08 完整 spec → ch09 TLC 原理 │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part IV   協議精讀                                               │
│   ch10 互斥 → ch11 2PC → ch12 Paxos → ch13 Raft                  │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part V    證明                                                   │
│   ch14 歸納不變量 → ch15 Refinement → ch16 機器證明              │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part VI   實務                                                   │
│   ch17 業界案例 → ch18 方法地圖                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 從你已知的出發

你每天都在跟「一步前後的關係」打交道，只是沒有用這個名字。

寫 PostgreSQL trigger 的時候，你拿到兩個東西：`OLD` 與 `NEW`——同一筆 row 在這次修改前後的快照。你寫的條件像「`NEW.balance` 必須等於 `OLD.balance` 減掉這次的扣款」，這不是在描述某個瞬間的狀態，而是在描述**一次轉移**：前後兩個狀態之間必須滿足的關係。DB 交易也是同一回事：commit 把系統從「修改前的世界」原子地帶到「修改後的世界」，isolation level 吵的全部是「別人能不能看到中間狀態」，而你心中拿來推理的單位，一直都是 before/after 這一對快照。

Code review 的時候你也在做一樣的事。看到一段入帳邏輯，你會在心裡說：「這一步執行完之後，ledger 必須已經標記、訊息必須已經離開佇列。」這句話有兩個時間點——「執行前」與「執行完之後」——以及一條把它們綁在一起的規則。

TLA（Temporal Logic of Actions）的核心設計，就是把這個你早就在用的心智模型搬進邏輯：

- 沒有 prime 的變數 `x`，指這一步**之前**的值——就是你的 `OLD`。
- 帶 prime 的變數 x′，指這一步**之後**的值——就是你的 `NEW`。
- 一個 **action** 就是一條同時談 OLD 與 NEW 的述語，描述「什麼樣的一步是合法的」。

ch02 我們說系統＝允許的行為集合，behavior＝狀態序列；ch03 你練了把白話翻成邏輯式。本章把兩者接起來：用邏輯式寫出「合法的一步」，再用一條公式圈出「所有合法的 behavior」。

還有一個你天天經歷、但大概沒想過要放進數學的現象：監控系統每 15 秒抓一次 metrics，兩次取樣之間，dashboard 上「什麼都沒發生」。系統也許真的閒著，也許在你看不到的粒度上做了一萬件事——對只看這幾個指標的你來說，這兩種情況**無法區分，也不需要區分**。TLA 把這件事做成了語言的地基，名字叫 stuttering。本章後半會講為什麼這是整個理論最重要的一個設計決定。

## 動作：把「一步」寫成述語

先複習 ch02 的詞彙：一個**狀態（state）**是變數到值的一組賦值；一條 **behavior** 是狀態的（可以無限長的）序列；一**步（step）**是序列中相鄰的一對狀態 ⟨s, t⟩。

TLA+ 用 `VARIABLES` 宣告變數。對結算系統 v0（ch02 引入：訊息 m1、m2，consumer 從 1 個加到 2 個，ledger 記每個 msgId 是否已入帳），變數是：

```tla
VARIABLES queue, working, ledger
```

接著是本章的主角。**action 是一條布林運算式，裡面可以同時出現 unprimed 變數（取「這一步之前」的值）與 primed 變數（取「這一步之後」的值）**。語意上，action 是「狀態對」的述語：給一對狀態 ⟨s, t⟩，unprimed 變數用 s 的值代入、primed 變數用 t 的值代入，算出真假。算出真，我們說這一步 ⟨s, t⟩ **滿足**這個 action。

這是你的第一段 TLA+ 語法，先把對照表立起來。本書全程的慣例：**內文與紙上推演用 Unicode 數學符號；引用 spec 原文時保留 ASCII，放在標 `tla` 的 code block 裡**。之後所有章節都沿用，全表收在附錄 A。

| 內文（Unicode） | spec 原文（ASCII） | 讀法 |
|---|---|---|
| ∧ | `/\` | 且（and） |
| ∨ | `\/` | 或（or） |
| ¬ | `~` | 非（not） |
| ⇒ | `=>` | 蘊涵（見 ch03） |
| ≡ | `<=>` | 等價 |
| □ | `[]` | always（本章只用直覺版，理論見 ch07） |
| ◇ | `<>` | eventually（見 ch07） |
| x′ | `x'` | x 在下一狀態的值 |
| ≜ | `==` | 定義為 |
| ∀ / ∃ | `\A` / `\E` | 對所有／存在（見 ch03） |
| ∈ / ∉ | `\in` / `\notin` | 屬於／不屬於（見 ch04） |
| ≠ | `#` 或 `/=` | 不等於 |
| ⟨x, y⟩ | `<<x, y>>` | tuple（見 ch04） |
| ↦ | `\|->` | 函數的「映到」（見 ch04） |
| ⤳ | `~>` | leads-to（見 ch07） |

來看最小的例子。「counter 加一」這一步，寫成 action 是：

```tla
Incr == counter' = counter + 1
```

內文寫法：Incr ≜ counter′ = counter + 1。一對狀態 ⟨s, t⟩ 滿足 Incr，若且唯若 t 裡 counter 的值等於 s 裡 counter 的值加一。

這裡有一個必須在第一天就矯正的直覺：**counter′ = counter + 1 是方程式，不是賦值**。它跟程式裡的 `counter = counter + 1` 長得像，骨子裡完全不同：

- 它沒有執行順序。一個 action 是一堆合取（∧）的組合，把合取的順序打亂，意思一個字都不變——它們是同時成立的約束，不是依序執行的指令。
- 它不一定「決定」下一個值。你可以寫 counter′ > counter（下一個值隨便，只要變大）；可以寫 counter′ ∈ {1, 2, 3}（三選一）。一個 action 對同一個起點可以允許**多個**不同的終點——這就是 ch02 講的非決定性，在語言裡的長相。
- 它可以無解。x′ = x + 1 ∧ x′ = x − 1 是一條永遠為假的 action：沒有任何一步滿足它。語法完全合法，邏輯上等於 FALSE。這不是趣聞，是一整類 bug 的形狀，「陷阱與防禦」會回來算帳。

∃ 在 action 裡扮演「系統自己挑」的角色。「某個還在佇列裡的訊息被取走」寫成 ∃ m ∈ queue : …，哪一個 m？都可能。把非決定性寫成存在量詞，是 TLA+ 最常見的句型。

## Init、Next、□[Next]_vars：一條公式讀完一個系統

有了 action，描述整個系統只需要三樣東西：

1. **Init**：一條普通的狀態述語（沒有 prime），圈出合法的起始狀態。
2. **Next**：一條 action，通常是好幾個具名 action 的析取（∨）——「系統的下一步，是這幾種步的其中一種」。
3. 把兩者綁成一條時序公式：

Spec ≜ Init ∧ □[Next]_vars

這條公式是整個 TLA+ 的縮影，值得逐字拆。設 σ = s₀, s₁, s₂, … 是一條 behavior：

- **Init**：s₀ 必須滿足 Init。起點要對。
- **□**：「在每一步都……」。□ 是時序算子 always，它的一般理論（作用在任意時序公式上、跟 ◇ 的對偶性）留給 ch07；本章你只需要這個讀法：□F 表示 F 對 behavior 的每個位置都成立。
- **[Next]_vars**：這是 TLA 特有的記號，定義是

  [Next]_vars ≜ Next ∨ (vars′ = vars)

  其中 vars ≜ ⟨queue, working, ledger⟩ 是把所有變數打包成一個 tuple。所以 [Next]_vars 讀作：「這一步要嘛滿足 Next，**要嘛這組變數一動不動**」。後面那個免責條款就是 stuttering 步。
- 合起來：σ 滿足 Spec，若且唯若 s₀ 滿足 Init，而且每一對相鄰狀態 ⟨sᵢ, sᵢ₊₁⟩ 要嘛滿足 Next、要嘛 vars 不變。

注意下標 vars 不是裝飾。它回答「不動是指**誰**不動」——是這個 spec 關心的那組變數。TLA 的語法甚至刻意不讓你寫裸的 □Next：action 要進 □，必須包成 [Next]_vars 這種對 stuttering 免疫的形式。這是語言在強迫你接受一個設計哲學，下一節講為什麼。

兩個配套記號：

**UNCHANGED**。UNCHANGED v 就是 v′ = v 的縮寫；UNCHANGED ⟨x, y⟩ 等於 x′ = x ∧ y′ = y。它存在的理由是紀律：**一個 action 必須對每個變數都交代**——要嘛說它怎麼變，要嘛明說它不變。沒交代的變數不是「預設不變」，而是**不受約束**：語意上它下一步可以變成任何值。這條規則違反直覺（程式裡沒寫到的變數當然不變），所以是新手第一大坑，「陷阱與防禦」第 2 條。

**ENABLED**。ENABLED A 是一條**狀態**述語：在狀態 s 為真，若且唯若存在某個狀態 t 使 ⟨s, t⟩ 滿足 A。白話：「站在 s，A 這種步走得出去」。直覺上就是你熟的 guard——條件滿足、這個分支可以走。兩件事先說清楚：第一，ENABLED A 已經沒有 prime 了，primed 變數被「存在某個 t」吃掉了，所以它是談單一狀態的述語；第二，**enabled 不等於會發生**。好幾個 action 同時 enabled 時，系統挑哪個？都可能；一直只挑別人、把某個 enabled 的 action 餓死，也完全合法。想說「enabled 夠久就必須發生」，那叫 fairness，是 ch07 的主題，本章不展開。ENABLED 在這裡先掛號，因為 fairness 的定義（WF、SF）整個建立在它上面。

## 為什麼允許不動：stuttering 是刻意設計

[Next]_vars 裡那個 vars′ = vars 的免責條款，初看像是漏洞：我寫 spec 是要系統做事，為什麼要允許「什麼都不做」永遠合法？

Lamport 的經典例子是時鐘（出自 Specifying Systems 第 2 章，本章延伸閱讀有免費 PDF）。考慮一個只顯示**小時**的時鐘 spec：變數 hr，每一步 hr 前進一格、12 之後回到 1。再考慮一個顯示**時與分**的時鐘：變數 hr 與 min，每一步 min 前進一格，min 走滿 60 才推動 hr 一次。

問題來了：時分時鐘算不算「實作了」小時時鐘的 spec？直覺上當然算——把分鐘遮起來，它就是一個如假包換的小時鐘。但如果小時 spec 寫成「每一步 hr 都必須前進」，那時分時鐘**不滿足**它：時分時鐘每 60 步裡有 59 步 hr 紋風不動。一個顯然正確的實作，被 spec 判了死刑——錯的不是實作，是 spec 把「每一步」說得太滿。

加上 stuttering 條款後，問題消失：小時 spec 說的是「每一步，要嘛 hr 照規則前進，要嘛 hr 不動」。時分時鐘那 59 步「只動分針」的步，對只看 hr 的觀察者來說就是 hr 不動的步——合法。於是「時分時鐘 ⇒ 小時時鐘」這條蘊涵成立了。

把這個模式抽出來，就是整個 TLA 的世界觀：

- **規格與實作是同一種東西**——都是「允許的行為集合」，都寫成同一種公式。
- **「實作正確」＝實作的每條 behavior 都被規格允許**＝一條蘊涵式 Impl ⇒ Spec。
- 實作幾乎總是比規格**細**：它有規格沒有的變數（分針、cache、重試計數器），它的很多步只動這些新變數。要讓蘊涵成立，規格必須把這些步看成「我的變數沒動」——也就是 stuttering。

所以：**允許不動，不是寬鬆，是讓「實作蘊涵規格」在數學上可能成立的先決條件。** 這裡只給直覺；把 Impl ⇒ Spec 真正當定理來驗（refinement mapping、INSTANCE 的讀法），是 ch15 的主題。**這是 ch15 的伏筆，本章先把地基打好：你今天接受的 stuttering 條款，就是為了那一章存在的。**

順帶補一個技術細節，之後讀文獻會用到：在 TLA 的語意裡，一個狀態其實是「**所有**變數」的賦值，不只是你 spec 裡宣告的那幾個。stuttering 步是「**我的** vars 沒動」，宇宙裡別的變數（別人 spec 的變數、實作層的新變數）可以照動。這就是為什麼下標 _vars 不可省略——它宣告「我」是誰。

monitoring 的比喻在這裡接上：你的 spec 就是那個每 15 秒看一次固定幾個指標的觀察者。兩次取樣之間系統做了什麼，只要沒反映在這幾個指標上，對 spec 而言就是 stuttering。一個對「取樣之間沒事」過敏的觀察者，沒辦法跟任何真實系統相處。

最後是代價，必須誠實說：stuttering 條款意味著**從任何一點開始永遠不動**的 behavior 也滿足 □[Next]_vars。一條從 s₀ 起就原地踏步到天荒地老的 behavior，是 Spec 的合法行為。所以 Init ∧ □[Next]_vars 這種公式**只說得了 safety**（壞事不發生），說不了 liveness（好事終將發生）：它從不承諾任何訊息「終究會」入帳。要承諾，得加 fairness 條件——ch07 的事。本章你只要記住這個邊界：**□[Next]_vars 是一張「允許清單」，不是一張「待辦清單」。**

## 第一個 spec：結算系統 v0

材料齊了，把 ch02 的結算系統 v0 寫成你的第一個 TLA+ spec。回憶設定：兩則訊息 m1、m2 在佇列裡等著入帳；consumer 從佇列取訊息、處理、入帳；ledger 記錄每個 msgId 是否已入帳。ch02 手畫狀態空間時先用 1 個 consumer、再加到 2 個體會爆炸；這裡直接寫 2 個 consumer 的版本（把 `Consumers` 改成只剩 `"c1"` 就還原 ch02 的小圖）。取訊息與入帳拆成兩個 action，對應你在 SQS 世界的日常：receive 是一步，處理完 delete 是另一步——race 就藏在「兩步之間」，這也是 ch08 升級 v1（crash、redelivery、dedup）時的施工點。

完整 spec 如下（約 20 行；MODULE、EXTENDS 等完整檔案結構是 ch08 的事，這裡先專心看邏輯本體）：

```tla
Msgs == {"m1", "m2"}
Consumers == {"c1", "c2"}

VARIABLES queue, working, ledger
vars == <<queue, working, ledger>>

Init == /\ queue = Msgs
        /\ working = [c \in Consumers |-> "idle"]
        /\ ledger = [m \in Msgs |-> FALSE]

Fetch(c, m) == /\ working[c] = "idle"
               /\ m \in queue
               /\ queue' = queue \ {m}
               /\ working' = [working EXCEPT ![c] = m]
               /\ UNCHANGED ledger

Settle(c) == /\ working[c] # "idle"
             /\ ledger' = [ledger EXCEPT ![working[c]] = TRUE]
             /\ working' = [working EXCEPT ![c] = "idle"]
             /\ UNCHANGED queue

Next == \E c \in Consumers : Settle(c) \/ \E m \in Msgs : Fetch(c, m)

Spec == Init /\ [][Next]_vars

NoDoublePay == \A m \in Msgs :
                 ledger[m] => /\ m \notin queue
                              /\ \A c \in Consumers : working[c] # m
```

逐行解說：

- **`Msgs` / `Consumers`**：用 ≜（ASCII `==`）定義兩個常數集合。v0 把參數寫死成基準配置；ch08 會教 CONSTANTS 讓它們變成可調參數。
- **`VARIABLES queue, working, ledger` 與 `vars`**：三個狀態變數——queue 是還沒被取走的訊息**集合**（v0 沒有重送，用 set 不會丟資訊；什麼時候該用 bag，ch04 已經吵過）；working 是函數 Consumers → 值，記每個 consumer 手上的東西，"idle" 是「兩手空空」的哨兵值；ledger 是函數 Msgs → BOOLEAN，對應 ch02 的「msgId → 是否已入帳」。vars 把三個變數打包成 tuple，給 [Next]_vars 和 UNCHANGED 用。
- **`Init`**：合取三條：佇列裝滿兩則訊息；`[c \in Consumers |-> "idle"]` 是 ch04 教的函數寫法——定義域是 Consumers、每個 c 都映到 "idle"；ledger 全部 FALSE。注意 Init 裡沒有任何 prime：它是狀態述語，圈起點。
- **`Fetch(c, m)`**：「consumer c 從佇列取走訊息 m」。前兩個合取沒有 prime，是 guard：c 必須閒著、m 必須還在佇列。後三個合取交代**每一個**變數的下一步：queue′ 是舊 queue 拿掉 m（集合差，見 ch04）；working′ 用 EXCEPT 語法——`[working EXCEPT ![c] = m]` 讀作「跟 working 一模一樣的函數，只有在 c 這一格改成 m」，這是 TLA+ 更新函數的標準句型；ledger 明說不動。對照你的直覺：這就是 SQS receive——訊息離開可見佇列、進到某個 consumer 手上，帳本沒動。
- **`Settle(c)`**：「consumer c 把手上的訊息入帳」。guard：c 手上有東西（≠ "idle"）。然後 ledger 在 working[c]（**舊值**——unprimed！）那一格改成 TRUE；working 把 c 那格放回 "idle"；queue 不動。一次入帳＋釋放 consumer，原子地發生。
- **`Next`**：系統的任何一步，就是**某個** consumer 做 Settle，或**某個** consumer 對**某則**訊息做 Fetch。兩層 ∃ 把所有非決定性（誰動、拿哪則）攤開。
- **`Spec`**：Init ∧ □[Next]_vars。十一個字元，整個系統。
- **`NoDoublePay`**：性質名沿 ch02。注意它的形狀：這是一條**狀態**述語（沒有 prime），不是 action。

NoDoublePay 值得多停一步，因為這裡有一個方法論的彎。白話的「同一 msgId 至多入帳一次」是在數**整條 behavior 裡 Settle 對 m 發生幾次**——那是行為層的敘述。但 invariant（ch02、ch05）是**狀態**述語：它只能看著單一狀態說話，看不到歷史。怎麼把「至多一次」塞進一張快照？答案是換個說法：**「已入帳的訊息，必須已經徹底離開系統」**——不在佇列裡、也不在任何 consumer 手上。只要每個可達狀態都滿足這句話，「第二次入帳」就無從發生：對 m 再做一次 Settle，前提是有 consumer 手持 m；要手持 m 得先 Fetch；要 Fetch 得 m 在佇列——三條路全被堵死。把行為層的願望改寫成狀態層的述語，是寫 invariant 的核心技藝，ch14 會把它磨到能撐起證明（那裡它有個正式名字：把歷史編碼進狀態）。

這份 spec 怎麼被機器檢查、「v0 的所有可達狀態都滿足 NoDoublePay」怎麼被證明，分別是 ch09 與 ch14 的事。本章先練手藝：手追。

## 手追一條 behavior：worked example

紙上推演的基本功：給一條 behavior，逐步驗證它滿足 Spec。我們追一條 4 步的 behavior，**刻意含一步 stuttering**。狀態寫成 tuple，函數值縮寫 T/F：

| 狀態 | queue | working | ledger |
|---|---|---|---|
| s₀ | {m1, m2} | (c1 ↦ idle, c2 ↦ idle) | (m1 ↦ F, m2 ↦ F) |
| s₁ | {m2} | (c1 ↦ m1, c2 ↦ idle) | (m1 ↦ F, m2 ↦ F) |
| s₂ | {m2} | (c1 ↦ m1, c2 ↦ idle) | (m1 ↦ F, m2 ↦ F) |
| s₃ | {m2} | (c1 ↦ idle, c2 ↦ idle) | (m1 ↦ T, m2 ↦ F) |
| s₄ | {} | (c1 ↦ idle, c2 ↦ m2) | (m1 ↦ T, m2 ↦ F) |

**起點**：s₀ 滿足 Init 嗎？queue = Msgs ✓；working 兩格都是 "idle" ✓；ledger 兩格都 FALSE ✓。過。

**步 1：⟨s₀, s₁⟩**。候選：Fetch(c1, m1)。逐合取驗，unprimed 用 s₀、primed 用 s₁：

- working[c1] = "idle"？s₀ 裡是 idle ✓
- m1 ∈ queue？m1 ∈ {m1, m2} ✓
- queue′ = queue ∖ {m1}？s₁ 的 queue 是 {m2}，等於 {m1, m2} ∖ {m1} ✓
- working′ = [working EXCEPT ![c1] = m1]？s₁ 裡 c1 ↦ m1、c2 ↦ idle（沒動）✓
- UNCHANGED ledger？s₁ 的 ledger 與 s₀ 相同 ✓

五個合取全真 ⇒ 這一步滿足 Fetch(c1, m1) ⇒ 滿足 Next ⇒ 滿足 [Next]_vars。

**步 2：⟨s₁, s₂⟩**。s₂ 跟 s₁ 一字不差。它能是哪個 action 嗎？驗給你看：Fetch 要求 queue′ 比 queue 少一個元素——queue 沒變，不滿足；Settle 要求 working 的某一格回到 "idle"（這裡還得把 ledger 的 m1 格翻成 T）——working 與 ledger 都沒變，不滿足。**沒有任何 action 解釋得了這一步。**但 vars′ = vars 成立（三個變數原封不動），所以 [Next]_vars 的第二個 disjunct——stuttering 條款——接住了它 ✓。這就是那個免責條款「上工」的樣子：不靠它，這條 behavior 在第 2 步就死了。至於這一步「實際上」是什麼？也許是 c1 正在處理、還沒到入帳那一刻；也許是 GC pause；也許整個機房真的靜止了 15 秒。spec 不知道、也不在乎——這正是重點。

**步 3：⟨s₂, s₃⟩**。候選：Settle(c1)。

- working[c1] ≠ "idle"？s₂ 裡 working[c1] = m1 ✓
- ledger′ = [ledger EXCEPT ![working[c1]] = TRUE]？working[c1] 取**舊值** m1，所以要求 ledger 的 m1 格翻成 T、m2 格不動——s₃ 正是 (m1 ↦ T, m2 ↦ F) ✓
- working′ = [working EXCEPT ![c1] = "idle"]？s₃ 裡 c1 回到 idle ✓
- UNCHANGED queue？兩邊都是 {m2} ✓

滿足 Settle(c1) ⇒ 滿足 [Next]_vars。

**步 4：⟨s₃, s₄⟩**。候選：Fetch(c2, m2)。working[c2] = "idle" ✓；m2 ∈ {m2} ✓；queue′ = {m2} ∖ {m2} = {} ✓；working′ 只改 c2 格成 m2 ✓；ledger 不動 ✓。過。

四步全過、起點合法 ⇒ 這條 behavior（接著無限 stuttering 下去）滿足 Spec。順手做兩個加值檢查：

**ENABLED 的手感**：站在 s₁，哪些 action enabled？Fetch(c2, m2)：c2 閒、m2 在佇列 ⇒ enabled。Fetch(c2, m1)：m1 ∉ queue ⇒ **不** enabled——SQS 直覺完全對應：被 c1 取走的訊息，c2 看不見，所以 v0 天生不會雙取。Settle(c2)：c2 手上沒東西 ⇒ 不 enabled。Settle(c1)：enabled。注意步 2 裡 Fetch(c2, m2) 與 Settle(c1) 都 enabled，但**都沒發生**——enabled ≠ 發生，behavior 選了 stuttering，完全合法。

**NoDoublePay 抽查**：s₃ 是第一個有訊息入帳的狀態。ledger[m1] = T ⇒ 要求 m1 ∉ queue（✓，queue = {m2}）且沒有 consumer 手持 m1（✓，兩個都 idle 或持 m2）。成立。s₄ 同理。其餘狀態 ledger 全 F，蘊涵的前件為假——ch03 的 vacuous truth 在這裡是良性的：沒入帳，就沒義務。

## 陷阱與防禦

動作邏輯的坑，幾乎都來自「它長得像程式，但不是程式」。每一條都按本書的固定問法：它怎麼給你假安全感、你怎麼發現。

| 故障模式 | 它怎麼騙你 | 防禦 |
|---|---|---|
| 把 x′ = e 當賦值 | 你以為合取有執行順序、以為「後面那行」能讀到「前面那行」改完的值；於是寫出引用 working′[c] 卻期待舊值之類的鬼東西 | 把 action 唸成「前後快照的關係」；測試法：任意打亂合取順序，意思必須一字不變 |
| 漏交代變數（忘了 UNCHANGED） | 沒被約束的變數＝下一步**什麼值都行**。spec 默默允許 ledger 憑空翻面，invariant 莫名其妙破掉，而你盯著 action 看不出哪裡寫錯——因為錯的是「沒寫」 | 寫完每個 action 點名每個變數：「你的下一步被誰決定？」三個變數三個著落，缺一個就是洞（TLC 也會在這裡直接報錯，見 ch09） |
| action 恆假（guard 矛盾或方程無解） | 永遠不 enabled 的 action 等於從 Next 裡消失；系統照跑、所有 invariant 照樣全綠——因為那條路根本沒人走過。綠燈是 vacuous 的（ch03 的 vacuous truth，ch14 還會回收一次） | 對每個 action 手工構造一個讓它 enabled 的具體可達狀態；構造不出來，要嘛 spec 有鬼、要嘛你對系統的理解有鬼 |
| 把 □[Next]_vars 讀成「系統會前進」 | 你寫完 spec 覺得「訊息會被入帳」已經在裡面了——其實裡面只有「入帳時不會做錯」。永遠 stuttering 的 behavior 完全合法，AllPaid 之類的承諾一個字都沒說 | 默念：□[Next]_vars 是允許清單，不是待辦清單。「終將發生」是 liveness，要 fairness 才有（見 ch07） |
| 把 ENABLED 當「會發生」 | 「這個 action 在那個狀態明明 enabled，所以接下來就是它」——不，非決定性之下它可以被永遠跳過 | enabled 只回答「可不可以」；「會不會」是 fairness 的事（見 ch07）。手追 behavior 時練習：每一步先列出所有 enabled 的 action，再看實際走了哪個 |
| 在 invariant 裡寫 prime | 想寫「入帳之後不會再入帳」，手一滑在 NoDoublePay 裡寫出 ledger′ —— invariant 是狀態述語，看不到「下一步」 | 寫性質前先分類：談單一狀態→狀態述語；談一步→action；談整條 behavior→時序公式（ch07）。層次錯了，後面全錯 |

## 紙上推演

### 題 1：白話規則 → action（[15 分鐘] ★）

替 v0 補兩個 action（先不要管要不要加進 Next）：

(a) **Requeue(c)**：「consumer c 手上有訊息時，可能因 visibility timeout 到期，把訊息放回佇列、自己回到 idle；帳本不動。」

(b) **Backfill(m)**：「維運人員對還在佇列裡、尚未入帳的訊息 m 直接補入帳：標記 ledger、把 m 移出佇列；不經過任何 consumer。」

寫完後自問：每個變數的下一步都有著落嗎？

### 推演解答

(a)

```tla
Requeue(c) == /\ working[c] # "idle"
              /\ queue' = queue \cup {working[c]}
              /\ working' = [working EXCEPT ![c] = "idle"]
              /\ UNCHANGED ledger
```

三個變數三個著落：queue 收回訊息、working 釋放、ledger 明說不動。最常見的錯路是把第二行寫成 queue′ = queue ∪ {working′[c]}——用了 **primed** 的 working，那是新值 "idle"，你會把字串 "idle" 塞進佇列。合取沒有順序，「先放回再清空」的程式直覺在這裡不存在；所有 unprimed 都是同一張舊快照。順帶一個 ch07 的預告：若把 Requeue 加進 Next，會出現「m1 被取走又放回、取走又放回……」的無限循環 behavior——完全合法、永不入帳。safety 毫髮無傷，liveness 整個沒了。記住這個不舒服的感覺，ch07 拿 fairness 來治它。

(b)

```tla
Backfill(m) == /\ m \in queue
               /\ ledger[m] = FALSE
               /\ ledger' = [ledger EXCEPT ![m] = TRUE]
               /\ queue' = queue \ {m}
               /\ UNCHANGED working
```

兩個 guard、三個著落。其實在 v0 裡 `ledger[m] = FALSE` 是多餘的 guard——NoDoublePay 成立的話，在佇列裡的訊息必然未入帳；但把它寫出來無傷，既是文件也是防禦（如果未來哪個改動讓「在佇列又已入帳」變得可達，Backfill 不會雪上加霜）。另一個值得咀嚼的點：worked example 的步 2 解答裡我們說過「一步同時改 queue 和 ledger 不滿足任何 action」——對**原版** Next 而言不合法的轉移，宣告成新 action 加進 Next 後就合法了。spec 是允許清單：清單上沒有的事不會發生，清單是你寫的。

### 題 2：這條 behavior 合法嗎？（[20 分鐘] ★★）

對原版 v0 spec（Next 只有 Fetch 與 Settle），逐一判斷下面三條 behavior 是否滿足 Init ∧ □[Next]_vars。不合法的，指出**第一個**出問題的步，並說明它為什麼不滿足任何一個 disjunct。（狀態欄位依序為 queue、working、ledger；working 與 ledger 只列縮寫。）

(a) 四個狀態：
s₀ = ⟨{m1, m2}, (c1 ↦ idle, c2 ↦ idle), (m1 ↦ F, m2 ↦ F)⟩；
s₁ = ⟨{m1}, (c1 ↦ m2, c2 ↦ idle), (m1 ↦ F, m2 ↦ F)⟩；
s₂ = s₁；
s₃ = ⟨{m1}, (c1 ↦ idle, c2 ↦ idle), (m1 ↦ F, m2 ↦ T)⟩。

(b) 兩個狀態：s₀ 同上；s₁ = ⟨{m1}, (c1 ↦ idle, c2 ↦ idle), (m1 ↦ F, m2 ↦ T)⟩。

(c) 三個狀態：s₀ 同上；s₁ = ⟨{m2}, (c1 ↦ m1, c2 ↦ idle), (m1 ↦ F, m2 ↦ F)⟩；s₂ = ⟨{m2}, (c1 ↦ idle, c2 ↦ idle), (m1 ↦ F, m2 ↦ F)⟩。

### 推演解答

(a) **合法**。步 1 是 Fetch(c1, m2)（逐合取驗法同 worked example）；步 2 是 stuttering（沒有 action 能解釋，但 vars 全等，第二個 disjunct 接住）；步 3 是 Settle(c1)：working[c1] 舊值 m2，ledger 的 m2 格翻 T、queue 不動 ✓。陷阱在步 2：「什麼都沒發生」不是違規，是 [Next]_vars 白紙黑字允許的。

(b) **不合法**，問題在步 1。這一步 queue 少了 m2 **且** ledger 的 m2 格翻了 T，working 全程 idle。驗三個出口：Fetch 要求 working 有一格從 idle 變成某個訊息——沒有；Settle 要求事前有 consumer 手持訊息——沒有；stuttering 要求 vars 全等——變了兩個。三個 disjunct 全滅 ⇒ 不是合法的步。注意：這個轉移**正是**題 1(b) 的 Backfill——在沒有宣告 Backfill 的 spec 裡，它就是違規。同一個轉移，合法與否取決於你的允許清單。

(c) **不合法**，問題在步 2。working[c1] 從 m1 變回 idle，但 ledger 沒翻面（不滿足 Settle）、queue 沒收回 m1（不滿足 Requeue——況且原版 spec 根本沒有 Requeue）、vars 又不是全等。這就是「訊息蒸發」：consumer 拿著訊息憑空兩手一攤。眼熟嗎？這是 **crash**。v0 不允許它，不是因為現實中 consumer 不會掛——會，你太知道了——而是 v0 **選擇不建模** crash（ch02 的抽象選擇）。ch08 的 v1 會正式宣告 Crash 與 redelivery，到時這個轉移就會出現在允許清單上，而 NoDoublePay 的考驗才真正開始。

### 題 3：找出這個 action 的 bug（[10 分鐘] ★★）

同事提交了 Requeue 的另一個版本：

```tla
BadRequeue(c) == /\ working[c] # "idle"
                 /\ queue' = queue \cup {working[c]}
                 /\ working' = [working EXCEPT ![c] = "idle"]
```

指出 bug、說明語意後果，並回答：把 BadRequeue 加進 Next 之後，NoDoublePay 還守得住嗎？

### 推演解答

bug：**ledger 沒有著落**——少了 UNCHANGED ledger。後果不是「ledger 預設不變」，而是 ledger′ 完全不受約束：滿足 BadRequeue 的步裡，ledger 可以變成**任何**布林函數。包括：m2 沒人碰過卻翻成 T（憑空記帳）；更陰的是 m1 已入帳的 T 翻回 F（帳被抹掉，之後可以再入一次帳——真正的 double pay 開了門）。NoDoublePay 守不住：取「c1 手持 m1、m2 還在佇列」的可達狀態，走一步 BadRequeue(c1) 並讓 ledger′ 的 m2 格為 T——新狀態裡 ledger[m2] = T 而 m2 ∈ queue，NoDoublePay 直接陣亡。防禦就是陷阱表第 2 條的紀律：寫完 action，逐變數點名。三個變數、三個著落，少一個都不行。

## 自我檢核

口頭回答，講得出來才算過：

1. 狀態述語、action、時序公式三層各談什麼？各舉 v0 裡的一個例子（提示：NoDoublePay、Fetch、Spec 各屬一層）。
2. 逐字念出 Init ∧ □[Next]_vars：每個記號什麼意思？下標 vars 在回答什麼問題、為什麼不可省略？
3. counter′ = counter + 1 與程式裡的 `counter = counter + 1` 差在哪？至少講出兩點（順序、非決定性／可無解）。
4. 一條從 s₀ 起永遠 stuttering 的 behavior 滿足 v0 的 Spec 嗎？這暗示 Spec 沒承諾什麼、要去哪一章補？
5. 用時鐘的例子解釋：為什麼禁止 stuttering 的 spec 會誤殺正確的實作？這跟 ch15 的 refinement 是什麼關係？
6. ENABLED Settle("c1") 是狀態述語還是 action？prime 到哪去了？enabled 為什麼不等於會發生？
7. 「同一 msgId 至多入帳一次」是行為層的敘述，NoDoublePay 卻是一條狀態述語——它用了什麼改寫策略？為什麼這條狀態述語成立就堵死了第二次入帳？
8. 一個 action 漏寫 UNCHANGED，語意上發生什麼事？為什麼這比「寫錯」更難發現？

## 延伸閱讀

- **Specifying Systems**（Leslie Lamport, Addison-Wesley, 2002）——官方頁面提供免費 PDF：`https://lamport.azurewebsites.net/tla/book.html`。第 2 章就是本章時鐘例子的原始出處（HourClock spec），第一部分（第 1–7 章，約 83 頁）涵蓋本書整個 Part III 的原典版本。讀原文最大的收穫是 Lamport 對每個設計決定的辯護。
- **learntla.com 的「TLA+」一章**（Hillel Wayne）：`https://learntla.com/core/tla.html`。用 hour clock 從零走一遍純 TLA+ 的 Init／Next／Spec 與 EXCEPT 語法，跟本章互為印證；整個網站免費且持續維護（2026-06 查證）。
- **The Temporal Logic of Actions**（Lamport, ACM TOPLAS 1994）：`https://lamport.azurewebsites.net/pubs/pubs.html#lamport-actions`。TLA 的原始論文。想看「為什麼把 action 放進邏輯、stuttering 為何不可妥協」的第一手論證，讀前兩節就值回票價。
- **TLA+ Video Course**（Lamport 親自錄製）：`https://lamport.azurewebsites.net/video/videos.html`。共 10 講，前幾講對應本章與 ch07–08 的內容。課程開場自述「These videos are not light entertainment. They require careful viewing and actual thinking.」——名不虛傳，搭配紙筆服用。
