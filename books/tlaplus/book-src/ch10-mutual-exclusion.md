# ch10 — 互斥：Peterson 演算法全手推

> **本章解決什麼問題**：Part III 給了你語言（動作邏輯、時序邏輯、完整 spec）與機器原理（TLC 的 BFS）。從本章起的 Part IV，把這套工具按在四個經典分散式協議上。第一個是最小的：互斥（mutual exclusion）——兩個 process 怎麼在只有原子讀寫的世界裡，不靠任何現成的鎖，保證不同時進入臨界區。本章做全書第一次「整個協議的狀態空間手推」：把 Peterson 演算法的所有可達狀態一個不漏畫出來、逐邊驗證 `MutualExclusion`。這個手藝是 ch11–13 讀 2PC、Paxos、Raft 的基本功，也是 ch14 歸納證明的前菜。

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
│ Part III  TLA+ 與時序邏輯                                        │
│   ch06 動作邏輯 → ch07 時序邏輯 → ch08 完整 spec → ch09 TLC 原理 │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part IV   協議精讀                                               │  ← 你在這裡
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

你的職業生涯大概沒有一天離開過鎖。`SELECT ... FOR UPDATE` 是鎖；Redis 的 `SETNX` 加 TTL 是鎖；你排查過的那次 RDS 鎖競爭、那個兩條 transaction 互相等待的 deadlock，全是互斥問題的工程現場。但注意一件事：這些鎖都是**買來的**。DB 的 lock manager 幫你做好了互斥，Redis 靠單執行緒事件迴圈幫你做好了「單一 key 的操作不會交錯」。你站在別人蓋好的互斥之上工作。

那最底下那層互斥是誰蓋的、怎麼蓋的？把問題推到極限：硬體只給你「對單一變數的原子讀」和「原子寫」，沒有 compare-and-swap、沒有 test-and-set、沒有任何現成的鎖。兩個 process 要共用一段臨界區（critical section）——你能只用幾個共享變數，徒手蓋出一把保證正確的鎖嗎？

這個問題由 Dijkstra 在 1965 年的 CACM 論文正式提出並給出 n 個 process 的解；兩個 process 的第一個正確解出自荷蘭數學家 Th. J. Dekker（Dijkstra 在講義《Cooperating Sequential Processes》中歸功於他），但 Dekker 的演算法出名地難讀。十六年後，Gary Peterson 在 1981 年用一篇**兩頁**的論文給出一個簡潔到令人發笑的解——論文標題就叫〈Myths About the Mutual Exclusion Problem〉，要破除的迷思正是「這問題的解必然複雜」。

本章拿 Peterson 當第一個精讀協議，有三個理由。第一，它小：小到你能把**整個**可達狀態空間畫在一頁紙上，逐邊驗證——這是唯一一個我們能做到「窮舉不靠機器」的協議，正好用來建立 Part IV 的手感。第二，它精巧得恰到好處：差一個變數會死鎖、改一行會破互斥，每個零件的「為什麼」都問得出來。第三，它把 ch07 的抽象詞彙全部落地：safety 是哪條、liveness 是哪條、deadlock 與 starvation 差在哪、WF 在哪裡開始幹活——全部在 20 個狀態裡看得見摸得著。

對照你的世界：你評估一把分散式鎖，問的也是同樣兩件事——「會不會兩個 client 同時拿到鎖」（safety；`SETNX` 靠 Redis 對單 key 操作的原子性）、「鎖會不會永遠拿不到」（liveness；TTL 在賭持有者掛了之後鎖終會釋放）。Peterson 是這兩個問題最純粹的標本。

## 互斥問題：規則與計分板

先把問題說精確。兩個 process（依全書基準，編號 0 與 1）各自反覆執行：

```text
loop:
  非臨界區（ncs）   \* 想待多久待多久，包括永遠
  進入協議（entry protocol）
  臨界區（cs）
  離開協議（exit protocol）
```

遊戲規則：

1. **只有共享暫存器的原子讀與原子寫。**一步只能讀或寫一個變數；不能「讀了馬上改」當成一步。
2. **process 可以永遠待在 ncs。**不想進臨界區的人沒有義務配合任何人。
3. **不能假設速度。**兩個 process 的相對速度任意，調度任意——這正是 ch01 講的「調度不可控」。

計分板上有一條 safety 與一階梯 liveness：

| 性質 | 類型 | 白話 |
|---|---|---|
| `MutualExclusion` | safety | 任何時刻至多一個 process 在臨界區 |
| deadlock-freedom | liveness（弱） | 只要有人想進，**就有人**終會進去 |
| starvation-freedom | liveness（強） | **每個**想進的 process 自己終會進去 |

starvation-freedom 蘊涵 deadlock-freedom，反之不然——「整體有進展」跟「每個個體都有進展」是兩回事，你在搶不到連線池的服務身上看過這個差距。兩條 liveness 都是 ◇ 型的承諾，照 ch07 的教訓，之後談它們時必須交代 fairness。

**本章的原子性假設，先講清楚**：我們建模時假設**每個動作是一步原子的**——寫一個變數是一步，連「同時讀 flag 與 turn 做判斷」也包成一步（下文會給這個簡化的理由與代價）。真實多核硬體不保證這件事：弱記憶體模型下寫入可能延遲可見、讀寫可能重排，裸寫 Peterson 在現代 CPU 上會壞——記憶體一致性模型是全書不涵蓋的主題，工程上請用語言提供的同步原語，想深究見延伸閱讀。

## 天真方案：兩面旗子，然後一起卡死

不看答案，你會怎麼設計 entry protocol？最自然的直覺：各舉一面旗。`flag[i] = TRUE` 表示「我想進」；進去之前先看對方的旗。

```text
flag[i] := TRUE;              \* 舉旗：我要進
await flag[1-i] = FALSE;      \* 等對方旗子放下
臨界區;
flag[i] := FALSE;             \* 放旗
```

把它看成狀態機：每個 process 的 pc（執行到哪一行）只有三個位置——n（在 ncs）、w（已舉旗、卡在 await）、c（在臨界區）。flag 不用另外記：flag[i] = TRUE 若且唯若 pc 不在 n（舉旗與進入同一步、放旗與離開同一步）。動作三種：R(i) 舉旗（n → w）、E(i) 通過 await（w → c，guard：對方 flag 為 FALSE）、X(i) 離開（c → n）。

狀態寫成 ⟨pc₀, pc₁⟩。pc 組合共 3 × 3 = 9 個，逐一展開可達的部分（ch09 的 BFS，這次完全手動）：

```text
                         nn
                       /     \
                  R0/           \R1
                 v                 v
                wn                nw
              /     \R1       R0/     \
          E0/          \     /          \E1
         v                v                v
        cn               ww               nc
       /   \                             /   \
  X0/        \R1                     R0/        \X1
  v            v                     v            v
(nn)          cw                    wc          (nn)
               |                     |
               |X0                   |X1
               v                     v
             (nw)                  (wn)
```

（括號節點代表「回到上方已畫過的狀態」，是同一個節點不重複畫；全章狀態圖都用這個慣例。每個狀態還允許 stuttering 步，依 ch06 慣例不畫。）

可達狀態 8 個：9 個 pc 組合裡只有 cc 不可達——也就是說 **`MutualExclusion` 成立**。對帳：cc 的入口只有兩個——cw 走 E1，或 wc 走 E0——但 guard 要求對方的 flag 為 FALSE，而對方 pc 在 c 上、旗子正舉著，兩個入口都被擋死。兩面旗子確實守住了 safety。

但看 ww 這個節點：**沒有任何一條出邊**。R 不行（兩人都不在 n）、E0 不行（flag[1] = TRUE）、E1 不行（flag[0] = TRUE）、X 不行（沒人在 c）。兩個 process 都舉著旗、都在等對方放旗——這就是 deadlock，而且它不是機率事件，是**狀態圖上一個白紙黑字的節點**，從初始狀態走兩步就到：

nn →R0→ wn →R1→ ww。卡死。

最短反例 2 步。值得停一拍體會這個諷刺：這個方案的 `MutualExclusion` 驗起來**全綠**。如果你只檢查 safety，它看起來完美——沒有人會同時進臨界區，因為很快就**沒有人能進任何地方**。一個死掉的系統不會違反任何 safety 性質（ch07 講過：safety 說「壞事不發生」，而什麼都不發生是它最便宜的滿足方式）。這是本書反覆敲打的假安全感模式裡最經典的一款。

順帶一提另一個直覺方向「先看再舉」（先確認對方旗子沒舉，再舉自己的）：它不死鎖，但直接破互斥——兩個 process 可以同時通過檢查、再同時舉旗進場。這正是你在 ch01 看過的 check-then-act race，dedup 檢查與入帳之間被插隊的同款形狀。反例留給紙上推演題 2。

兩個天真方案，一個死於「都讓」，一個死於「都搶」。缺的是一個**打破對稱**的裁決機制。

## Peterson：多一個 turn，讓位給對方

Peterson 的解法是在兩面旗之外加一個共享變數 turn ∈ {0, 1}，並且在舉旗之後做一件反直覺的事：**把優先權讓給對方**。

```text
flag[i] := TRUE;                       \* 舉旗：我要進
turn := 1 - i;                         \* 讓位：你先
await flag[1-i] = FALSE \/ turn = i;   \* 等：對方不想進，或輪到我
臨界區;
flag[i] := FALSE;                      \* 放旗
```

進入條件讀作：「對方根本不想進（flag[1−i] = FALSE），或者對方比我後讓位（turn = i——turn 的值是被**最後一次寫入**蓋掉的，所以 turn = i 表示對方在我之後執行了讓位、把 turn 寫回了 i）。」兩個人同時想進時，誰最後寫 turn，誰等。客氣不是裝飾，是裁決演算法。

寫成 TLA+。每個 process 的 pc 有四個位置：`"ncs"`（還沒開始）、`"set"`（已舉旗，下一步寫 turn）、`"wait"`（已讓位，卡在 await）、`"cs"`（臨界區內）。ch08 看過 PlusCal 翻譯出的 pc 變數，這裡我們直接手寫同一個建模手法：

```tla
Procs == {0, 1}
Other(i) == 1 - i

VARIABLES pc, flag, turn
vars == <<pc, flag, turn>>

TypeOK == /\ pc \in [Procs -> {"ncs", "set", "wait", "cs"}]
          /\ flag \in [Procs -> BOOLEAN]
          /\ turn \in Procs

Init == /\ pc = [i \in Procs |-> "ncs"]
        /\ flag = [i \in Procs |-> FALSE]
        /\ turn = 0

Request(i) == /\ pc[i] = "ncs"
              /\ flag' = [flag EXCEPT ![i] = TRUE]
              /\ pc' = [pc EXCEPT ![i] = "set"]
              /\ UNCHANGED turn

SetTurn(i) == /\ pc[i] = "set"
              /\ turn' = Other(i)
              /\ pc' = [pc EXCEPT ![i] = "wait"]
              /\ UNCHANGED flag

Enter(i) == /\ pc[i] = "wait"
            /\ flag[Other(i)] = FALSE \/ turn = i
            /\ pc' = [pc EXCEPT ![i] = "cs"]
            /\ UNCHANGED <<flag, turn>>

Exit(i) == /\ pc[i] = "cs"
           /\ flag' = [flag EXCEPT ![i] = FALSE]
           /\ pc' = [pc EXCEPT ![i] = "ncs"]
           /\ UNCHANGED turn

Next == \E i \in Procs :
          Request(i) \/ SetTurn(i) \/ Enter(i) \/ Exit(i)

Spec == Init /\ [][Next]_vars

MutualExclusion == ~(pc[0] = "cs" /\ pc[1] = "cs")
```

逐段讀：

- **四個動作對應四行程式**。Request 舉旗、SetTurn 讓位、Enter 通過 await、Exit 放旗回家。每個動作三個變數三個著落（ch06 的紀律）。
- **Enter 的 guard 是整個演算法的靈魂**：flag[Other(i)] = FALSE ∨ turn = i。注意它是狀態述語，讀的是當下這一拍的兩個共享變數。
- **Init 裡 turn = 0 是任意選的**，與 Lamport 的版本一致。初值不影響任何性質——事實上待會的圖裡 nn1（同一條起跑線、turn = 1）本來就是可達狀態，兩種初值的可達閉包相同；釘死一個值是讓 BFS 有單一起點。
- `MutualExclusion` 照全書基準命名：兩個 pc 不得同時是 "cs"。

**建模的三個誠實聲明**（每次精讀 spec 都要做的功課——spec 跟現實之間隔著哪些選擇）：

1. **ncs 與 cs 抽象成單一 label。**臨界區裡做什麼我們不關心；ncs 可以永遠待著（規則 2），所以 Request 之後不會有任何 fairness 強迫它發生。
2. **await 的判斷是一步原子讀兩個變數。**真實程式是迴圈裡兩次分開的讀。這是本章為了把全圖控制在一頁內做的**約化**：拆成兩步會讓每個 process 多一個 pc 位置、狀態數進一步膨脹。約化的底氣有二：Lamport 自己網站上的 PlusCal 版 Peterson 用的就是同一粒度的單步 await（2026-06 查證，見延伸閱讀）；而把讀拆開之後互斥**仍然**成立——Peterson 的設計本來就只依賴單變數原子讀寫，這是它有名的強項（標準結果，本書不驗，見延伸閱讀）。
3. **舉旗（Request）與讓位（SetTurn）絕不合併成一步。**這兩個寫入之間的縫隙正是演算法的戲肉：兩個 process 可以都舉完旗、還沒讓位。如果你把它們合併，狀態空間更小、驗證更輕鬆——但你驗的就不是 Peterson，而是一個硬體根本做不到的強化版。原子粒度寬一格，反例就少一批，這是 spec 騙過你的標準手法之一（陷阱與防禦再算帳）。

## 全狀態空間手推：20 個狀態、34 條邊

現在做本章的招牌動作：把 Spec 的**全部**可達狀態畫出來，每條邊驗一次 `MutualExclusion`。不開 TLC——我們自己當 TLC（演算法照 ch09 的 BFS）。

### 第一步：把上界從 128 壓到 32

照 TypeOK 數狀態上界：pc 每人 4 個位置（4 × 4 = 16）、flag 每人 2 值（× 4）、turn 2 值（× 2）——上界 **128**。手畫 128 個格子不現實，先找便宜的縮減。

觀察：**flag[i] 完全由 pc[i] 決定**。

⟨1⟩1. 宣稱：所有可達狀態滿足 FlagSync ≜ ∀ i ∈ Procs : flag[i] ≡ (pc[i] ≠ "ncs")。
⟨1⟩2. Init：pc 全 "ncs"、flag 全 FALSE，兩邊同假。理由：Init 的定義。
⟨1⟩3. 每步保持：Request(i) 把 flag[i] 設 TRUE 同時把 pc[i] 帶離 "ncs"（同步翻真）；Exit(i) 把 flag[i] 設 FALSE 同時把 pc[i] 設回 "ncs"（同步翻假）；SetTurn 與 Enter 不動 flag，pc[i] 在 {"set","wait","cs"} 內移動、不跨越 "ncs" 邊界；對方的 flag 與 pc 都沒被動到。四種動作都保持。
⟨1⟩4. Q.E.D. 由 ch05 的不變量規則（起點成立＋每步保持）。

所以 flag 不帶資訊，狀態可以壓成三元組 ⟨pc₀, pc₁, turn⟩：16 種 pc 組合 × 2 種 turn ＝上界 **32**。注意這一步本身就是一次小型歸納證明——你剛剛用 ch05 的工具把狀態空間砍掉四分之三。

以下狀態縮寫成三個字元：pc 取首字母 **n**（ncs）、**s**（set）、**w**（wait）、**c**（cs），第三碼是 turn。例如 ws1 ≜ ⟨pc₀ = "wait", pc₁ = "set", turn = 1⟩。

### 第二步：BFS，逐層展開

從 Init（即 nn0）開始，每層把 frontier 的每個狀態、每個動作試一遍：

- **第 0 層**：{nn0}。累計 1。
- **第 1 層**：展開 nn0——只有兩個 Request enabled：R0 → sn0、R1 → ns0。新增 2，累計 3。
- **第 2 層**：sn0：T0 → wn1（讓位，turn 翻成 1）、R1 → ss0。ns0：R0 → ss0（已入列）、T1 → nw0。新增 wn1、ss0、nw0，累計 6。
- **第 3 層**：wn1：E0 → cn1（guard 走 flag[1] = FALSE 這個 disjunct——對手不想進，直接過）、R1 → ws1。ss0：T0 → ws1、T1 → sw0。nw0：R0 → sw0、E1 → nc0。新增 cn1、ws1、sw0、nc0，累計 10。
- **第 4 層**：cn1：X0 → nn1、R1 → cs1。**ws1：E0 被擋**（flag[1] = TRUE 且 turn = 1——兩個 disjunct 都假），唯一出路 T1 → ww0。**sw0：E1 被擋**（鏡像），唯一出路 T0 → ww1。nc0：X1 → nn0（第一條回頭邊）、R0 → sc0。新增 nn1、cs1、ww0、ww1、sc0，累計 15。
- **第 5 層**：nn1：R0 → sn1、R1 → ns1。cs1：X0 → ns1、T1 → cw0。**ww0：兩人都在等，裁決時刻**——E0 enabled（turn = 0），E1 被擋（flag[0] = TRUE 且 turn = 0），唯一出路 E0 → cw0。ww1 鏡像：唯一出路 E1 → wc1。sc0：T0 → wc1、X1 → sn0（回頭）。新增 sn1、ns1、cw0、wc1，累計 19。
- **第 6 層**：sn1：T0 → wn1（回頭）、R1 → ss1。ns1：R0 → ss1、T1 → nw0（回頭）。**cw0：0 在臨界區、1 在等——E1 被擋**（flag[0] = TRUE 且 turn = 0），唯一出路 X0 → nw0（回頭）。wc1 鏡像：唯一出路 X1 → wn1（回頭）。新增 ss1，累計 20。
- **第 7 層**：ss1：T0 → ws1、T1 → sw0，都已入列。**frontier 空，BFS 收斂。**

**可達狀態共 20 個。**這個數字是本章自己推的，等下用第二條路複核。

### 全圖

34 條邊全部畫出（括號節點＝跳回上方同名節點；stuttering 不畫）：

```text
                                   nn0
                                 /     \
                             R0/         \R1
                            v               v
                           sn0             ns0
                          /    \R1     R0/    \
                      T0/        \     /        \T1
                      v             v             v
                     wn1           ss0           nw0
                    /   \R1     T0/   \T1     R0/   \
                E0/        \   /         \   /         \E1
                v            v             v             v
               cn1          ws1           sw0           nc0
              /   \           \             \           /   \
          X0/       \R1        \T1          \T0       R0/      \X1
          v           v         v            v         v          v
         nn1         cs1       ww0          ww1       sc0       (nn0)
         /   \R1   X0/  \T1  E0/              \E1    /   \
     R0/       \   /       \  /                 \T0/       \X1
      v           v          v                   v           v
     sn1         ns1        cw0                 wc1        (sn0)
     /  \R1   R0/  \          \                    \
  T0/     \   /      \T1       \X0                   \X1
   v        v         v         v                      v
 (wn1)     ss1      (nw0)     (nw0)                  (wn1)
          /   \
      T0/       \T1
      v           v
    (ws1)       (sw0)
```

先看圖的骨架再看細節：最左一縱列（sn0 → wn1 → cn1 → nn1 → sn1 → 回 wn1）是 process 0 在對手不搶時的「獨走循環」，最右側鏡像是 process 1 的；中間那團（ss、ww、cw、wc）才是兩人交鋒的戰場。整張圖有一個漂亮的對稱：把兩個 process 互換、turn 翻面（σ(⟨a, b, k⟩) = ⟨b, a, 1−k⟩），圖映到自己——20 個狀態恰好配成 10 對鏡像（如 ws1 ↔ sw0、cw0 ↔ wc1），等下對帳會用它當第三重複核。

### 逐狀態 × 逐動作總表：34 條邊全驗

「逐邊驗 invariant」對狀態述語來說等於兩件事：(1) 每個狀態本身滿足 `MutualExclusion`；(2) 每條邊的終點都還在這 20 個狀態之內（圖是封閉的）。下表把 20 個狀態的**每個動作**都交代掉——enabled 的給出終點，被擋的給出是哪個 guard 擋的，一步不跳：

| # | 狀態 | 出邊（動作 → 終點） | 被擋的 await（原因） | cs 占用 |
|---|---|---|---|---|
| 1 | nn0 | R0 → sn0、R1 → ns0 | — | 無 |
| 2 | sn0 | T0 → wn1、R1 → ss0 | — | 無 |
| 3 | ns0 | R0 → ss0、T1 → nw0 | — | 無 |
| 4 | wn1 | E0 → cn1、R1 → ws1 | — | 無 |
| 5 | ss0 | T0 → ws1、T1 → sw0 | — | 無 |
| 6 | nw0 | R0 → sw0、E1 → nc0 | — | 無 |
| 7 | cn1 | X0 → nn1、R1 → cs1 | — | 僅 0 |
| 8 | ws1 | T1 → ww0 | E0 ✗：flag[1] = T 且 turn = 1 | 無 |
| 9 | sw0 | T0 → ww1 | E1 ✗：flag[0] = T 且 turn = 0 | 無 |
| 10 | nc0 | X1 → nn0、R0 → sc0 | — | 僅 1 |
| 11 | nn1 | R0 → sn1、R1 → ns1 | — | 無 |
| 12 | cs1 | X0 → ns1、T1 → cw0 | — | 僅 0 |
| 13 | ww0 | E0 → cw0 | E1 ✗：flag[0] = T 且 turn = 0 | 無 |
| 14 | ww1 | E1 → wc1 | E0 ✗：flag[1] = T 且 turn = 1 | 無 |
| 15 | sc0 | T0 → wc1、X1 → sn0 | — | 僅 1 |
| 16 | sn1 | T0 → wn1、R1 → ss1 | — | 無 |
| 17 | ns1 | R0 → ss1、T1 → nw0 | — | 無 |
| 18 | cw0 | X0 → nw0 | E1 ✗：flag[0] = T 且 turn = 0 | 僅 0 |
| 19 | wc1 | X1 → wn1 | E0 ✗：flag[1] = T 且 turn = 1 | 僅 1 |
| 20 | ss1 | T0 → ws1、T1 → sw0 | — | 無 |

每個狀態還有 Request／SetTurn／Exit 沒列的部分：guard 是 pc 等式，不在對應位置就不 enabled，從狀態縮寫一眼可判，表中不贅列；表裡單獨點名的是六個「await 被擋」——它們才需要看兩個變數。

**邊數對帳**：14 個狀態各 2 條出邊、6 個狀態各 1 條，合計 2 × 14 + 6 = **34**。換個方向數：R 邊＝「pc 為 n 的格子數」＝ 12（pc₀ = n 的狀態 6 個、pc₁ = n 的 6 個），T 邊同理 12，X 邊＝「pc 為 c 的格子數」＝ 6，E 邊＝ w 格子 10 個減被擋 6 個＝ 4。12 + 12 + 6 + 4 = **34** ✓。兩種數法一致。

**逐邊驗 `MutualExclusion`**：34 條邊的終點全部出現在表中 20 個狀態之列（BFS 已收斂，圖封閉）；而 20 個狀態的「cs 占用」欄沒有任何一格是「0 與 1 同時」——**沒有任何 ⟨c, c, ·⟩ 狀態。每條邊都把系統送進一個滿足 `MutualExclusion` 的狀態。驗訖。**

值得把鏡頭推近到防守動作真正發生的地方。臨界區的入口只有 4 條 E 邊（#4、#6、#13、#14），而擋下入侵的是 6 個「✗」：

- **ww0／ww1（#13、#14）是裁決點**：兩人都讓完位，turn 的終值＝後讓位者讓出去的值，先讓位的人進場，另一人被「flag 為真 ∧ turn 不利」雙重鎖死。
- **cw0／wc1（#18、#19）是守門點**：有人已在臨界區內，門口那位的 E 被同一組條件擋住——這兩格就是 `MutualExclusion` 的最前線。對照天真方案：那裡擋住 cw／wc 的只有 flag，付出的代價是 ww 變成死路；Peterson 用 turn 把 ww 的死路改成單行道，又沒放鬆 cw／wc 的防守。

### 兩路對帳：32 個候選裡為什麼恰好缺 12 個

BFS 給了 20。第二條路：從 32 個候選（16 種 pc 組合 × turn 兩值）反向清點誰**不在**圖裡，並且要求每個缺席者都講得出缺席的理由——數字對上、理由齊全，才算對帳閉合。

對照 BFS 結果，32 − 20 = 12 個缺席者是：wn0、ws0、cn0、cs0（及其鏡像 nw1、sw1、nc1、sc1），cw1、wc0、cc0、cc1。它們由兩條引理解釋：

**引理 L1（讓位有記錄）**：若 pc_i ∈ {wait, cs} 且 pc_{1−i} ∈ {ncs, set}，則 turn = 1−i。

⟨1⟩1. 取 i 最後一次執行的 SetTurn(i)。它存在（i 進入 wait 的唯一入口），寫下 turn = 1−i；此後 i 一直留在 {wait, cs}（離開得經過 Exit 回 ncs，再回來就得再執行一次 SetTurn，跟「最後一次」矛盾），所以此後 flag[i] 恆為 TRUE（FlagSync）。
⟨1⟩2. 反設現在 turn = i。turn 被改寫的唯一途徑是 SetTurn，而 SetTurn(i) 已是最後一次，故存在更晚的 SetTurn(1−i) 寫下 turn = i，且它是對 turn 的最後一次寫入。
⟨1⟩3. 那次 SetTurn(1−i) 把 pc_{1−i} 帶到 wait。從那一刻到現在：turn 恆為 i（⟨1⟩2：沒有更晚的寫入）、flag[i] 恆為 TRUE（⟨1⟩1）——Enter(1−i) 的 guard「flag[i] = FALSE ∨ turn = 1−i」兩個 disjunct 恆假，1−i 出不了 wait。
⟨1⟩4. 所以現在 pc_{1−i} = wait，與前提 pc_{1−i} ∈ {ncs, set} 矛盾。Q.E.D.

白話：**你讓過位、對方在那之後沒讓過位，turn 就還停在你讓出去的值。**L1 一口氣解釋 8 個缺席者：wn0、ws0、cn0、cs0 都是「0 已過讓位線（w/c）、1 還沒（n/s）」卻 turn = 0 的狀態，違反 L1；4 個鏡像同理。

**引理 L2（交鋒時 turn 屬於場內者）**：若 pc_i = cs 且 pc_{1−i} ∈ {wait, cs}，則 turn = i。

論證（工程師嚴謹度的散文版）：i 在臨界區內，看它最後一次 Enter(i) 與對手最後一次 SetTurn(1−i) 誰先誰後。若 SetTurn(1−i) 在後：它寫下 turn = i，之後沒有人再寫（i 要再寫得先離開 cs，對手要再寫得先通過 Enter 繞一圈——但它正卡在 wait），所以現在 turn = i，證畢。若 Enter(i) 在後：Enter 那一刻對手已在 {wait, cs}、flag[1−i] = TRUE，guard 只能靠 turn = i 這個 disjunct 通過；之後同樣無人再寫 turn，現在仍是 turn = i。兩種情況都得到 turn = i。∎

L2 解釋剩下 4 個：cw1、wc0 直接違反；cc0 與 cc1 則是把 L2 同時套在兩人身上得到 turn = 0 且 turn = 1——矛盾，所以 **⟨c, c, ·⟩ 根本不可能可達，這正是 `MutualExclusion` 的「為什麼」**，而不只是「窮舉後沒看到」。

對帳閉合：32 候選 − L1 殺 8 − L2 殺 4 = **20** ✓，與 BFS 一致。第三重複核：20 個狀態配成 10 對鏡像、34 條邊也兩兩成對（抽查：ws1 -T1→ ww0 的鏡像是 sw0 -T0→ ww1 ✓；cw0 -X0→ nw0 的鏡像是 wc1 -X1→ wn1 ✓），對稱無破口。

最後預告：FlagSync ∧ L1 ∧ L2 ∧ TypeOK 這一包，其實就是 Peterson 的 **inductive invariant**（ch14 的主角）的雛形——它蘊涵 `MutualExclusion`，而且每步保持。本章用 BFS「走」出了它；ch14 教你在狀態空間大到走不完（或無限）時，不靠窮舉、直接對任意參數**證**出同樣的結論。這是「20 個狀態的窮舉」與「定理」之間的橋。

## Deadlock、starvation 與 fairness

safety 結案了，換 liveness。先把兩個常被混用的詞釘死：

| | deadlock | starvation |
|---|---|---|
| 定義 | 系統卡死：到達某狀態後，再也沒有任何（非 stuttering 的）動作 enabled | 系統整體有進展，但某個 process 永遠等不到它要的 |
| 在圖上長什麼樣 | **節點性質**：一個沒有出邊的節點 | **無限路徑性質**：單看任何節點看不出來，要看整條 behavior |
| 屬於哪類 | 有限前綴就能反駁 ⇒ 可當 safety 檢（TLC 的 deadlock check，見 ch09） | 純 liveness，要配 fairness 才談得下去（ch07） |

天真方案的 ww 是 deadlock 的標本。掃一眼 Peterson 的總表：**20 個狀態每個都至少一條出邊——無 deadlock 節點**。這條等於免費驗掉了 deadlock-freedom 的 safety 面。

starvation 呢？先寫下主張與它需要的燃料：

```tla
Trying(i) == pc[i] \in {"set", "wait"}

StarvationFree == \A i \in Procs : Trying(i) ~> (pc[i] = "cs")

FairSpec == Spec /\ \A i \in Procs :
              /\ WF_vars(SetTurn(i))
              /\ WF_vars(Enter(i))
              /\ WF_vars(Exit(i))
```

三件事要說清楚。

**第一，沒有 fairness 時 StarvationFree 必假。**ch06 念過的咒語：□[Next]_vars 是允許清單，不是待辦清單。反例便宜到難堪——behavior 走到 ww0 之後永遠 stuttering：Spec 完全允許，Enter(0) 永遠 enabled 卻永遠不被執行。注意這不是演算法的錯，是調度器的懶惰；fairness 公理的職責正是把這種「明明能走卻永遠不走」的 behavior 排除出考慮範圍（ch07）。

**第二，Request 故意不加 fairness。**規則 2 說 process 有權永遠待在 ncs。如果你給 Request 加了 WF，spec 就主張「每個人都會一直想進臨界區」——這是對現實撒謊，而且會讓某些以「對手永遠不來」為前提的性質空洞地變化。fairness 不是越多越好，是「對誰承諾、就對誰負責」的精確選擇。

**第三，WF 就夠了，不需要 SF。**這點值得證一遍，因為它揭露 Peterson 第二個精巧之處。對 process 0（對 1 對稱）：

⟨1⟩1. 反設某條滿足 FairSpec 的 behavior 裡，0 從某時刻起 Trying(0) 恆真、永遠進不了 cs。
⟨1⟩2. 0 不會永遠停在 "set"：SetTurn(0) 的 guard 只看 pc[0]，持續 enabled，WF 逼它發生。所以從某時刻起 pc[0] = "wait" 恆真。
⟨1⟩3. 從那時起，turn 一旦變成 0 就永遠是 0：把 turn 寫成 1 的唯一動作是 SetTurn(0)，它需要 pc[0] = "set"——不再可能。
⟨1⟩4. 情況 A：某時刻 turn = 0。由 ⟨1⟩3 此後恆 0，Enter(0) 的 guard 靠 turn = 0 持續成立，WF(Enter(0)) 逼它發生，0 進 cs。與 ⟨1⟩1 矛盾。
⟨1⟩5. 情況 B：turn = 1 恆真。看 pc[1] 在哪：
  ⟨2⟩1. "set"：WF(SetTurn(1)) 逼它讓位，turn := 0——回到情況 A，矛盾。
  ⟨2⟩2. "wait"：turn = 1 使 Enter(1) 持續 enabled，WF 逼 1 進 cs，轉 ⟨2⟩3。
  ⟨2⟩3. "cs"：WF(Exit(1)) 逼 1 離開，flag[1] := FALSE，轉 ⟨2⟩4。
  ⟨2⟩4. "ncs"：若 1 永遠待著，flag[1] = FALSE 持續成立，Enter(0) 持續 enabled，WF 逼 0 進場——矛盾；若 1 再度 Request（允許但不強迫），它來到 "set"，回 ⟨2⟩1——矛盾。
  ⟨2⟩5. Q.E.D. 每條路都通向矛盾。
⟨1⟩6. Q.E.D. StarvationFree 在 FairSpec 下成立。

WF 何以足夠？回想 ch07 的分工：WF 對付「持續 enabled」，SF 對付「enabled 閃爍不定」。Peterson 給了等待者一個**單調性**保證（⟨1⟩3）：turn 對你不利的值只會被翻成有利、不會翻回去——你的 Enter 一旦因 turn 而 enabled 就不再熄滅，所以最便宜的 WF 就能收割。如果一個演算法裡兩個 process 會反覆打掉對方的 guard，liveness 就得乞求 SF 甚至更多——ch12 的 Paxos 會讓你見識活性處境惡劣得多的世界。

順手收割一個更強的結論：圖上能直接**看見**有界等待（bounded waiting）。從 ww1（兩人都在等、輪到 1）出發走非 stuttering 步，路徑被圖逼死：

ww1 →E1→ wc1 →X1→ wn1 →R1→ ws1 →T1→ ww0 →（E1 被擋，唯一出路）E0→ cw0

對手 1 插隊**恰好一次**之後，它自己的第二次讓位（T1）把 turn 還給 0，從此它被擋在門外、0 必然是下一個進場者。更一般地：圖上所有避開「pc₀ = c」的環，都是 pc₀ = n 的環（0 根本沒在排隊；例如 nn0 → ns0 → nw0 → nc0 → nn0）——0 一旦舉旗，圖上**不存在**讓 1 連刷兩次臨界區的路徑（試著從 sn0 或 wn1 讓 1 繞圈，會在 sw0／ww0 撞牆）。這就是 ch09 說的「liveness 檢查＝在狀態圖上找滿足 fairness 的壞循環」：我們手工掃完了所有循環，壞循環不存在，剩下的 starvation 反例只有懶調度器一族，全數被 WF 沒收。

## 陷阱與防禦

互斥這個題目小，但它暴露的建模陷阱張張都是通用款。照本書固定問法：它怎麼給你假安全感、你怎麼發現。

| 故障模式 | 它怎麼騙你 | 防禦 |
|---|---|---|
| 原子粒度作弊 | 把「舉旗＋讓位」合併成一步，或把 await 的兩讀合成一讀，狀態空間縮小、反例消失——你驗過的是一個硬體做不到的演算法，報告卻全綠 | 每個動作旁問一句「硬體／runtime 真能一步做完嗎」；做了約化就白紙黑字寫下來（本章聲明 2），並交代為什麼結論不因此失效 |
| 只驗 safety，不問進展 | 天真方案 `MutualExclusion` 全綠，因為它很快死鎖——什麼都不發生的系統不違反任何 safety | 每張 safety 綠燈旁邊放一個問題：「那它會前進嗎？」至少檢查圖上有無零出邊節點（deadlock check 是便宜的） |
| 把 deadlock-freedom 當 starvation-freedom | 「系統整體有吞吐」聽起來像沒問題，但個體可以餓死——連線池搶不到的那個服務就是反例 | 兩條性質分開寫、分開驗：「有人進得去」與「每個想進的人進得去」是不同的時序公式 |
| liveness 主張不寫 fairness | StarvationFree 在裸 Spec 下被「永遠 stuttering」秒殺，而 spec 不會警告你忘了加燃料（ch07 主軸重演） | 寫 liveness 必同時寫明 fairness 給**哪些動作**；並反向檢查：哪些動作（如 Request）**不該**加 |
| 讓位寫反：turn′ = i | 一字之差，互斥陣亡；更毒的是反例要 6 步、特定交錯才現形，隨手試幾條 trace 多半全綠 | 對關鍵行做變異測試：故意改壞 spec，確認你的驗證流程真的抓得到（紙上推演題 3 親手做一次） |
| 紙上的 Peterson 直接上真硬體 | 本章全部論證建立在「每步原子、寫入立即可見」；弱記憶體模型下讀寫會重排，論證前提整包作廢 | 模型假設寫在 spec 旁邊；工程上用語言／平台的同步原語，不要手刻演算法（一句話聲明＋延伸閱讀，本書不展開） |
| 「2 個 process 驗過＝n 個也對」 | 我們窮舉的是 {0, 1} 這個配置；Peterson 的 n-process 推廣是另一個演算法、需要另一次驗證 | 把「驗過的配置」寫進結論裡（ch09 的 small scope：窮舉的辯護與限度）；推廣請另開一局 |

## 紙上推演

### 題 1：站在一個狀態，把八個動作問一遍（[10 分鐘] ★）

(a) 用 spec 逐合取驗證 ws1 -T1→ ww0 這條邊（unprimed 用 ws1、primed 用 ww0，ch06 的手追法）。
(b) 站在 cw0，把 R0、T0、E0、X0、R1、T1、E1、X1 八個動作逐一判斷 enabled 與否；不 enabled 的，指出是哪個 guard 擋的。

### 推演解答

(a) T1 ＝ SetTurn(1) 的四個著落，對 ⟨w, s, 1⟩ → ⟨w, w, 0⟩：

- pc[1] = "set"？ws1 的第二碼是 s ✓
- turn′ = Other(1) = 0？ww0 的 turn 是 0 ✓
- pc′ = [pc EXCEPT ![1] = "wait"]？pc₀ 不動（w → w）、pc₁ 改成 w ✓
- UNCHANGED flag？把縮寫展開：ws1 的 flag 是 (TRUE, TRUE)（兩個 pc 都在非 ncs 側），ww0 也是 (TRUE, TRUE)，相等 ✓

四個合取全真，邊成立。終點 ww0 無人在 cs，`MutualExclusion` 保持 ✓。

(b) cw0 ＝ ⟨pc₀ = "cs", pc₁ = "wait", turn = 0⟩，flag 兩面都 TRUE（FlagSync）：

- R0 ✗（pc[0] ≠ "ncs"）、T0 ✗（pc[0] ≠ "set"）、E0 ✗（pc[0] ≠ "wait"）、**X0 ✓**（pc[0] = "cs"）→ nw0
- R1 ✗（pc[1] ≠ "ncs"）、T1 ✗（pc[1] ≠ "set"）、X1 ✗（pc[1] ≠ "cs"）
- **E1 ✗**：pc[1] = "wait" 過了第一關，但 guard 第二行——flag[0] = TRUE 且 turn = 0 ≠ 1——兩個 disjunct 都假

唯一出路 X0。這格就是互斥的最前線：1 已經到門口，擋住它的是「0 的旗還舉著」加「turn 不站在 1 這邊」。注意 E1 與其他七個的不同：別的 guard 只看自己的 pc，E 的 guard 還要讀共享變數——這就是為什麼總表只替 E 寫「被擋原因」。

### 題 2：先看再舉，親手抓出互斥破口（[15 分鐘] ★★）

天真方案 B：「先確認對方旗子沒舉，再舉自己的旗」。

```text
await flag[1-i] = FALSE;   \* 看：對方沒舉旗
flag[i] := TRUE;           \* 舉旗
臨界區;
flag[i] := FALSE;
```

pc 三個位置：n（將檢查）、p（檢查已通過、將舉旗）、c（臨界區）；動作 C(i)（n → p，guard：flag[1−i] = FALSE）、S(i)（p → c，舉旗）、X(i)（c → n，放旗）。注意這裡 flag[i] = TRUE 若且唯若 pc_i = c。請手推一條打破 `MutualExclusion` 的 behavior，並指出反例的最短步數。

### 推演解答

關鍵：檢查（C）與舉旗（S）之間有縫。讓兩人都先鑽過檢查：

| 步 | 動作 | 狀態 ⟨pc₀, pc₁⟩ | flag |
|---|---|---|---|
| 0 | — | ⟨n, n⟩ | (F, F) |
| 1 | C(0)：flag[1] = FALSE ✓ | ⟨p, n⟩ | (F, F) |
| 2 | C(1)：flag[0] = FALSE ✓——0 還沒舉旗！ | ⟨p, p⟩ | (F, F) |
| 3 | S(0) | ⟨c, p⟩ | (T, F) |
| 4 | S(1) | ⟨c, c⟩ | (T, T) |

第 4 步抵達 ⟨c, c⟩，`MutualExclusion` 陣亡，最短反例 **4 步**。這就是 check-then-act：檢查當下為真的事，到行動那一刻已經不是真的。你在 ch01 的結算 race（dedup 檢查與入帳之間被插隊）、在 `if not exists then insert` 的每一次 code review 裡，見過它一百次。對照方案 A 與 Peterson：A 把「舉旗」放在「檢查」之前，堵住這個縫但換來死鎖；Peterson 同樣先舉旗，再用 turn 拆掉死鎖——順序與裁決，缺一不可。

### 題 3：改一行，讓 Peterson 壞掉（[25 分鐘] ★★★）

同事重構時手滑，把 SetTurn 的讓位寫反了：

```tla
SetTurn(i) == /\ pc[i] = "set"
              /\ turn' = i          \* 原版是 Other(i)
              /\ pc' = [pc EXCEPT ![i] = "wait"]
              /\ UNCHANGED flag
```

「turn 設成自己，輪到我，很合理啊。」請手推一條打破 `MutualExclusion` 的 behavior（狀態縮寫沿用本章三碼記法），並回答：為什麼同樣的交錯在原版 Peterson 走不通？

### 推演解答

讓位寫反後，「最後表態的人」從等待者變成插隊者。讓 0 先完整走到臨界區，再讓 1 姍姍來遲：

nn0 →R0→ sn0 →T0（turn := 0）→ wn0 →E0（flag[1] = F ✓）→ cn0 →R1→ cs0 →T1（turn := 1）→ cw1 →E1（turn = 1 ✓）→ **cc1**

**6 步**抵達 ⟨c, c, 1⟩。第 5 步是兇案現場：1 讓位給**自己**，把 0 在場內這個事實直接蓋掉；第 6 步 E1 的 guard 靠 turn = 1 放行，兩人同處臨界區。

原版同樣的交錯走到第 5 步：T1 寫的是 turn := 0，狀態是 cw0——查總表 #18，E1 被「flag[0] = TRUE 且 turn = 0」擋死，1 只能等 0 離場。一模一樣的調度，一個字的差別。兩個教訓：第一，「讓位給對方」不是禮貌是 safety 機制——它保證後到者把優先權判給先到者，正是 L2 引理的內容；第二，這個反例要 6 步、要特定的「一快一慢」交錯，手測幾條 happy path 根本碰不到（ch01 的調度爆炸重演）。改壞一行、確認驗證流程抓得到，是檢驗「你的驗證是不是擺設」最便宜的辦法。

## 自我檢核

口頭回答，講得出來才算過：

1. 互斥問題的計分板上有哪三條性質？各屬 safety 還是 liveness？starvation-freedom 與 deadlock-freedom 誰強誰弱、差距的工程含義是什麼？
2. 天真兩 flag 方案的 deadlock 為什麼「不是機率問題」？說出那個狀態、到它的最短路徑，以及為什麼這個方案的 `MutualExclusion` 檢查反而全綠。
3. 重建 128 → 32 → 20 兩次縮減：各靠什麼？第一次縮減用到了 ch05 的哪個工具？
4. 不看書，講出 L1（讓位有記錄）的論證骨架：誰最後寫了 turn、為什麼之後沒人再寫、被卡住的是誰。再用 L2 解釋為什麼 ⟨c, c, ·⟩ 不可達。
5. deadlock 與 starvation 在狀態圖上分別「長什麼樣」？為什麼前者可以當 safety 檢、後者必須談 fairness？
6. StarvationFree 為什麼 WF 就夠、不需要 SF？關鍵的單調性是哪一條？哪個動作刻意**不**加 fairness、為什麼？
7. 本章的「每步原子」假設具體簡化了哪兩處？哪一處是安全的約化、哪一處在真硬體上會出事？
8. 從圖上指出「對手最多插隊一次」的證據：哪條路徑、在哪個狀態被堵死？

## 延伸閱讀

- **G. L. Peterson, "Myths About the Mutual Exclusion Problem", Information Processing Letters 12(3), 1981, pp. 115–116**——原始論文，兩頁。看一個傳世演算法可以多短，也看 1981 年的正確性論證跟你本章做的手推差在哪。
- **E. W. Dijkstra, "Solution of a Problem in Concurrent Programming Control", CACM 8(9), 1965**：`https://cacm.acm.org/research/solution-of-a-problem-in-concurrent-programming-control/`——互斥問題的開山之作，一頁紙，n 個 process。Dekker 的兩 process 解則記載於 Dijkstra 的講義《Cooperating Sequential Processes》（EWD 123）。
- **Lamport 網站上的 Peterson 短文**：`https://lamport.azurewebsites.net/tla/peterson.html`——用 PlusCal 寫 Peterson 並以 TLC 驗互斥與 starvation-freedom，await 粒度與本章相同（2026-06 查證）。讀它可以對照：機器跑出來的，跟你手推的同一張圖。
- **tlaplus/Examples 的 Peterson spec**：`https://github.com/tlaplus/Examples/tree/master/specifications/locks_auxiliary_vars`——Peterson 對抽象 Lock 規格的 refinement，含 auxiliary variables。現在讀吃力是正常的，ch15 之後回來收割。
- **M. Herlihy & N. Shavit, *The Art of Multiprocessor Programming*（書）**——第 2 章系統性地講互斥：Peterson、filter lock（n-process 推廣）、Lamport bakery，以及這些演算法在真實硬體（弱記憶體模型、cache）上的命運。本章「每步原子」假設之外的世界，從這裡開始。
- **tlaplus/Examples 的 DijkstraMutex**：`https://github.com/tlaplus/Examples/tree/master/specifications/dijkstra-mutex`——Dijkstra 1965 原始 n-process 演算法的 PlusCal 版。想體會「為什麼 Peterson 被視為簡潔的奇蹟」，讀它最快。
