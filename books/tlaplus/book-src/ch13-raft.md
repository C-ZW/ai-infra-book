# ch13 — Raft：工程化的共識，對照精讀

> **本章解決什麼問題**：ch12 你用「不變量先於演算法」的順序啃下了 Paxos；本章讀它最成功的工程化對照組——Raft，一個把「好懂」當成一級設計需求的共識演算法。三項任務：用論文的五條 safety 性質當地圖，理解 leader election 與 log replication；精讀 Diego Ongaro 親手寫的 raft.tla（471 行，一份工業級 spec 的真實長相）；在 5 個節點上手推一場含 split vote 的選舉，全程驗 Election Safety。Part IV 的協議精讀到此收官，ch14 起我們帶著這些素材爬上證明層。

## 從你已知的出發

你跟 Raft 的距離比想像中近。你排程結算 pipeline 用的 K8s CronJob、每一次 `kubectl apply`，最後都落到 etcd——而 etcd 的複製核心就是 Raft。你維運的那個 3 節點 etcd 叢集「掛一台沒事、掛兩台只能哭」的行為，本章讀完你能從一行 TLA+ 定義直接推出來。

三個你已有的直覺，先對好頻道：

**term ≈ 世代編號（epoch / generation）**。ch12 說 ballot ≈ optimistic lock 的版本號；Raft 的 term 是同一個直覺，但綁得更死：整個叢集的時間被切成一段段 term，**每個 term 至多一個 leader**。任何訊息都蓋著 term 戳章，舊 term 的訊息一律被「你過時了」打回票。你在 DB 樂觀鎖衝突時回 409 的肌肉記憶，整套適用。

**split vote ≈ 重試碰撞**。兩個 client 同時逾時、同時重試、又同時撞在一起——你在 backoff 沒加 jitter 的系統上看過這齣戲。Raft 的選舉一模一樣：多個候選人同時發起、票數均分、沒人過半，只好下一輪再來。Raft 的解法也是你的解法：隨機化逾時（jitter）。本章 worked example 會把這齣戲一步一步演完。

**log replication ≈ 主從複製**。Raft 是強 leader 設計：所有寫入走 leader，leader 把自己的 log 單向推給 followers——你管理過的 MySQL primary 把 binlog 推給 replica 就是這個形狀。Raft 多做的事，是把「primary 掛了誰接班、接班的人憑什麼不丟資料」這兩個你靠維運手冊與運氣處理的問題，變成有定理保護的機制。

## 設計目標：把 understandability 當成需求

Raft 論文的標題就是宣言：*In Search of an Understandable Consensus Algorithm*（Ongaro & Ousterhout，USENIX ATC 2014；官網稱該文獲當年 Best Paper Award）。摘要的第一段話值得記住：Raft 產出與 (multi-)Paxos 等價的結果、效率相當，但結構不同——而結構不同的目的就是好懂，以及給實際系統一個更好的地基。

「好懂」怎麼變成設計手段？論文給了兩招：

1. **分解（decomposition）**：把共識拆成 leader election、log replication、safety 三個近乎獨立的子問題，各自理解、各自論證。
2. **縮小狀態空間（state space reduction）**：用更強的約束減少你必須考慮的情況——log 不准有洞、資料只從 leader 單向流向 follower、log 之間的不一致被限制成「落後」或「多出一段未提交的尾巴」兩種形狀。

第二招你應該覺得耳熟：這就是 ch09 講的 state explosion，從演算法設計端動手。Paxos 允許的交錯多、對稱性高，所以「為什麼對」難講；Raft 用強 leader 把大量交錯直接定義成不存在。複雜度沒有消失——這是本章後面對照討論的主軸——但它被搬到了更容易說清楚的地方。

## 機制速覽：term、選舉、複製

每個 server 任一時刻處於三種狀態之一。先把狀態機畫出來：

```text
┌──────────┐   逾時，term+1   ┌───────────┐   獲得過半選票   ┌────────┐
│ Follower │ ───────────────► │ Candidate │ ───────────────► │ Leader │
└──────────┘                  └───────────┘                  └────────┘
     ▲                                                            │
     │             看到更高的 term：一律退回 Follower             │
     └────────────────────────────────────────────────────────────┘
```

（Candidate 逾時還沒選出結果時，把 term 再加一、留在 Candidate 重選——這條自環圖上省略，worked example 會走到。）

**term**：單調遞增的整數，從 1 起算（本書基準；raft.tla 的初始值也正是 1，稍後精讀時看得到）。term 是 Raft 的邏輯時鐘：每個 server 記著自己的 `currentTerm`，訊息帶著發送者的 term，誰看到更高的 term 就立刻追上去並退回 Follower；誰收到更低 term 的請求就拒絕。

**選舉**：Follower 一段時間沒收到 leader 的心跳（AppendEntries 空包）就逾時，把 term 加一、轉成 Candidate、投自己一票、向所有人發 RequestVote。拿到**過半**選票就成為該 term 的 leader。投票有兩條鐵律：

- 一個 server 在一個 term 內至多投一票（先到先得）。
- 投票者只把票投給「log 至少跟我一樣新」的候選人。「一樣新」的比較法：先比最後一筆 entry 的 term，term 大者新；term 相同則 log 長者新（論文 §5.4.1）。

第二條是 Raft 把複雜度搬家的關鍵動作，精讀段會逐字讀它的 TLA+ 寫法。

**複製**：client 的請求進到 leader，leader 把它接在自己 log 尾端（蓋上 currentTerm 戳章），再用 AppendEntries 推給所有 followers。AppendEntries 帶著「新 entry 的前一格」的 index 與 term（`prevLogIndex` / `prevLogTerm`），follower 核對自己 log 的同一格：對得上才收，對不上就拒絕，leader 把 `nextIndex` 往回退再試。這個一致性檢查配合「leader 只追加、絕不改寫自己的 log」，歸納地維持了所有 log 的前綴一致。

**提交（commit）**：當某筆 entry 被複製到過半 server，**且該筆 entry 屬於 leader 的當前 term**，leader 才把 `commitIndex` 推進到它；committed 的 entry 才能 apply 到狀態機、回覆 client。後半句的 term 限制看起來像贅肉，其實是整個演算法最精微的一條防線——紙上推演的題 2 會讓你親手拆掉它，看著已提交的資料被覆寫。

## 五條 safety 性質：Raft 的地圖

論文 Figure 3 列出五條任何時刻都成立的性質，圖說寫得很滿：「Raft guarantees that each of these properties is true at all times.」措辭照原文（引號內為論文原文，後附白話）：

1. **Election Safety**：「at most one leader can be elected in a given term.」（§5.2）——一個 term 至多選出一個 leader。
2. **Leader Append-Only**：「a leader never overwrites or deletes entries in its log; it only appends new entries.」（§5.3）——leader 絕不改寫或刪除自己的 log，只追加。
3. **Log Matching**：「if two logs contain an entry with the same index and term, then the logs are identical in all entries up through the given index.」（§5.3）——兩份 log 若在同一 index 有同 term 的 entry，則到該 index 為止整段相同。
4. **Leader Completeness**：「if a log entry is committed in a given term, then that entry will be present in the logs of the leaders for all higher-numbered terms.」（§5.4）——某 term 內提交的 entry，必出現在所有更高 term 的 leader 的 log 裡。
5. **State Machine Safety**：「if a server has applied a log entry at a given index to its state machine, no other server will ever apply a different log entry for the same index.」（§5.4.3）——只要有一台 server 在某 index apply 了某筆 entry，就不會有任何 server 在同一 index apply 不同的 entry。

這五條不是並列的雜貨清單，是一條推導鏈。State Machine Safety 是端到端的承諾——論文自己說它是「the key safety property for Raft」，地位等同 2PC 的 `TCConsistent`（見 ch11）與 Paxos 的 agreement（見 ch12）。前四條是支撐它的鷹架：

- Election Safety 來自「一 term 一票＋quorum 相交」（worked example 末尾給層級證明的骨架）。
- Leader Append-Only 是設計約束：spec 裡 leader 改 log 的唯一動作就是 Append。
- Log Matching 由 AppendEntries 的一致性檢查歸納維持。
- Leader Completeness 由兩道閘門合力：投票限制（log 不夠新的人選不上）＋提交限制（只對當前 term 的 entry 計票 commit）。
- 有了 Leader Completeness 與 Log Matching，committed entry 在所有後續 leader 手上且位置唯一，apply 自然一致——State Machine Safety 得證（本書不展開完整證明，見延伸閱讀的論文 §5.4.3 與 Ongaro 博士論文附錄）。

讀協議時把這張地圖放手邊：每看到一條規則，先問「它在替哪條性質扛事」。

## raft.tla 開箱：一份工業級 spec 的結構

精讀對象：Ongaro 本人維護的 `raft.tla`（repo `https://github.com/ongardie/raft.tla`，CC-BY 4.0；README 自述比博士論文版本略有更新，2026-06 查證）。471 行，是你目前讀過最大的 spec——但解剖學跟 ch08 完全一樣：CONSTANTS、VARIABLES、Init、一堆具名 action、Next、`Spec == Init /\ [][Next]_vars`。先看三個結構性亮點。

**訊息是 bag，不是 set。**

```tla
\* A bag of records representing requests and responses sent from one server
\* to another. TLAPS doesn't support the Bags module, so this is a function
\* mapping Message to Nat.
VARIABLE messages
```

ch04 那場「at-least-once 的訊息該用 set 還是 bag」的辯論，Ongaro 用行動投了票：網路會重複投遞（spec 裡有 `DuplicateMessage` action）、會丟（`DropMessage`），同一則訊息在途中的份數有意義，所以用 multiset——實作成「訊息 ↦ 份數」的函數，註解還誠實交代了原因：TLAPS 不支援 Bags 模組。工業級 spec 處處是這種「理論選型×工具現實」的妥協痕跡。

**history variables：只為證明而活的變數。**

```tla
\* A history variable used in the proof. This would not be present in an
\* implementation.
\* Keeps track of successful elections, including the initial logs of the
\* leader and voters' logs. Set of functions containing various things about
\* successful elections (see BecomeLeader).
VARIABLE elections
```

`elections`、`allLogs`、`voterLog` 三個變數都掛著同一句註解：「This would not be present in an implementation.」它們不影響協議行為，只是把歷史抄寫下來，讓性質可以寫成狀態述語——ch06 你在 `NoDoublePay` 上學過「把行為層的願望改寫成狀態層的述語」，ch14 會把這招正名為「把歷史編碼進狀態」，ch15 講 refinement 時 auxiliary variables 還會再登場。在這裡你先看到它的工業用法。

**quorum 的定義只有一行，註解卻是整個 ch12 的回聲。**

```tla
\* The set of all quorums. This just calculates simple majorities, but the only
\* important property is that every quorum overlaps with every other.
Quorum == {i \in SUBSET(Server) : Cardinality(i) * 2 > Cardinality(Server)}
```

「唯一重要的性質是任兩個 quorum 相交」——Paxos 靠它，Raft 也靠它（見 ch12）。SUBSET 是冪集（ch04），基數兩倍大於全集就是「過半」。5 個節點時，quorum = 任何 ≥ 3 台的子集。你的 etcd 叢集掛 2 台寫不進去，就是這一行：剩 1 台湊不出任何 quorum。

另外三件值得一瞥的事：(1) `InitServerVars` 把 `currentTerm` 初始化為 `[i \in Server |-> 1]`——term 從 1 起算，與本書基準一致；(2) `Restart(i)` 的 UNCHANGED 清單就是持久化需求的形式化——crash 重啟後只留 `currentTerm`、`votedFor`、`log` 三樣，恰是論文要求落盤的三樣；(3) 這份 spec **沒有**建模 membership change 與 snapshot/log compaction（`Server` 是固定常數），也沒有任何時間與機率——randomized timeout 在 spec 裡不存在，`Timeout(i)` 任何時刻都可能發生。

ASCII 對照補一條：這份 spec 裡的否定寫 `\lnot`（ch06 對照表列的是 `~`，兩者等價，TLA+ 都收）。

## 精讀一：投票條件（HandleRequestVoteRequest）

```tla
\* Server i receives a RequestVote request from server j with
\* m.mterm <= currentTerm[i].
HandleRequestVoteRequest(i, j, m) ==
    LET logOk == \/ m.mlastLogTerm > LastTerm(log[i])
                 \/ /\ m.mlastLogTerm = LastTerm(log[i])
                    /\ m.mlastLogIndex >= Len(log[i])
        grant == /\ m.mterm = currentTerm[i]
                 /\ logOk
                 /\ votedFor[i] \in {Nil, j}
    IN /\ m.mterm <= currentTerm[i]
       /\ \/ grant  /\ votedFor' = [votedFor EXCEPT ![i] = j]
          \/ ~grant /\ UNCHANGED votedFor
       /\ Reply([mtype        |-> RequestVoteResponse,
                 mterm        |-> currentTerm[i],
                 mvoteGranted |-> grant,
                 \* mlog is used just for the `elections' history variable for
                 \* the proof. It would not exist in a real implementation.
                 mlog         |-> log[i],
                 msource      |-> i,
                 mdest        |-> j],
                 m)
       /\ UNCHANGED <<state, currentTerm, candidateVars, leaderVars, logVars>>
```

逐段拆。`i` 是收件者（投票者）、`j` 是候選人、`m` 是請求。

**`logOk`：選舉時的「夠新」檢查。**這就是論文 §5.4.1 的 up-to-date 比較，翻成邏輯式只有三行：候選人最後一筆的 term 嚴格較大（第一個 disjunct）；或 term 打平、且候選人的 log 不比我短（第二個 disjunct）。`LastTerm` 是個輔助定義，空 log 回 0：

```tla
LastTerm(xlog) == IF Len(xlog) = 0 THEN 0 ELSE xlog[Len(xlog)].term
```

把白話「至少跟我一樣新」翻成可計算的字典序比較 ⟨lastTerm, len⟩，這是 ch03 練的翻譯功。它在替 Leader Completeness 扛事：committed entry 在過半機器上，而當選需要過半票，兩個過半必相交——所以**任何當選者至少跟某台「持有所有 committed entry」的機器一樣新**。

**`grant`：三個合取缺一不可。**term 必須**正好相等**（注意不是 ≤，題 3 會考你為什麼）；log 夠新；而且我這個 term 的票還沒投給別人——`votedFor[i] \in {Nil, j}` 同時涵蓋「還沒投」與「就是投給你（重複請求，冪等重投）」兩種情況。一 term 一票的鐵律就藏在這個 ∈ 裡。

**`IN` 之後：guard 加三個著落。**`m.mterm <= currentTerm[i]` 是這個 handler 的適用範圍——那「m.mterm 較大」的訊息誰處理？答案在 `Receive` 的析取裡：`UpdateTerm` 這個 action 先把收件者的 term 追上去（並退回 Follower、清空 votedFor），而且**不消費訊息**——原文註解寫明「messages is unchanged so m can be processed further」——下一步同一則訊息再進到本 handler，此時 term 已對齊。一次「收到高 term 訊息」被拆成兩個原子步，這是 spec 作者刻意把原子區域切小（atomic region 越小，涵蓋的實作越多；代價是狀態變多，ch09 的老朋友）。最後 `Reply` 一個動作完成「取出請求、放入回應」，回應裡帶著 `mvoteGranted` 與我的 currentTerm。

## 精讀二：log 一致性檢查（HandleAppendEntriesRequest）

這個 action 全長 63 行，是 spec 裡最大的一塊。骨架是一個 `logOk` 加三岔路（拒絕／candidate 退位／接受），接受裡再分三種情況。先讀 `logOk`：

```tla
HandleAppendEntriesRequest(i, j, m) ==
    LET logOk == \/ m.mprevLogIndex = 0
                 \/ /\ m.mprevLogIndex > 0
                    /\ m.mprevLogIndex <= Len(log[i])
                    /\ m.mprevLogTerm = log[i][m.mprevLogIndex].term
    IN /\ m.mterm <= currentTerm[i]
```

跟投票的 `logOk` 同名不同職：**這裡檢查的是「新 entry 的接點」**。leader 說「我要把 entry 接在你 log 的第 `mprevLogIndex` 格之後」，follower 核對：要嘛接點是 0（從頭開始，空前綴恆成立——注意這是 ch03 的良性 vacuous truth），要嘛我的 log 真的有那一格、而且那一格的 term 跟你說的一致。**同 index 同 term ⇒ 同 entry ⇒（歸納地）同前綴**——這個檢查每通過一次，Log Matching 的歸納步就被推進一格。ch05 的歸納法在這裡不是證明技巧，是協議本身的運轉方式。

接受分支裡最有戲的是衝突處理：

```tla
                   \/ \* conflict: remove 1 entry
                       /\ m.mentries /= << >>
                       /\ Len(log[i]) >= index
                       /\ log[i][index].term /= m.mentries[1].term
                       /\ LET new == [index2 \in 1..(Len(log[i]) - 1) |->
                                          log[i][index2]]
                          IN log' = [log EXCEPT ![i] = new]
                       /\ UNCHANGED <<serverVars, commitIndex, messages>>
                   \/ \* no conflict: append entry
                       /\ m.mentries /= << >>
                       /\ Len(log[i]) = m.mprevLogIndex
                       /\ log' = [log EXCEPT ![i] =
                                      Append(log[i], m.mentries[1])]
                       /\ UNCHANGED <<serverVars, commitIndex, messages>>
```

接點對上了，但我的 log 在接點之後還有舊東西、而且 term 對不上？這是「未提交的尾巴」——上個 term 留下的孤兒 entry。spec 的處理方式很有意思：**一步只刪最後一筆**（把 log 縮短一格的函數重建），不是一刀把整段尾巴砍掉。同一份訊息會被反覆處理（它還在 bag 裡），一步刪一筆，直到衝突清光、走到 append 分支。又是「最小原子步」哲學：實作可以一次截斷整段，spec 用更細的步涵蓋它（什麼叫「涵蓋」，ch15 的 refinement 給正式答案）。也注意被刪的只可能是 follower log 的尾巴、且 term 與現任 leader 衝突——committed entry 為什麼永遠刪不到？這正是 Leader Completeness 在罩著（推演題 2 拆給你看）。

## 精讀三：BecomeLeader

```tla
\* Candidate i transitions to leader.
BecomeLeader(i) ==
    /\ state[i] = Candidate
    /\ votesGranted[i] \in Quorum
    /\ state'      = [state EXCEPT ![i] = Leader]
    /\ nextIndex'  = [nextIndex EXCEPT ![i] =
                         [j \in Server |-> Len(log[i]) + 1]]
    /\ matchIndex' = [matchIndex EXCEPT ![i] =
                         [j \in Server |-> 0]]
    /\ elections'  = elections \cup
                         {[eterm     |-> currentTerm[i],
                           eleader   |-> i,
                           elog      |-> log[i],
                           evotes    |-> votesGranted[i],
                           evoterLog |-> voterLog[i]]}
    /\ UNCHANGED <<messages, currentTerm, votedFor, candidateVars, logVars>>
```

兩個 guard：我是 Candidate、我的得票集合屬於 Quorum——Election Safety 的執行點就這一行。當選後的兩個重置充滿樂觀與悲觀的分工：`nextIndex` 全體設成 `Len(log[i]) + 1`（樂觀假設大家跟我同步，從我的 log 尾端開始送，不合再退）；`matchIndex` 全體歸零（悲觀記帳：在 follower 親口確認前，不認定任何複製進度——commit 計票只信 matchIndex）。最後往 `elections` 這個 history variable 抄一筆完整的選舉記錄。注意 UNCHANGED 裡有 `messages`：**當選不廣播**。宣告勝選的方式是之後的 AppendEntries（心跳），這也是為什麼舊 leader 可能短暫不知道自己已被取代——下一節的陷阱表會回來談。

## Worked example：5 節點手推一場 split vote 選舉

基準配置：Server = {n1, n2, n3, n4, n5}，全體 log 為空。Quorum 需要 ≥ 3 票。初始狀態（對照 `InitServerVars`）：

| node | state | currentTerm | votedFor |
|---|---|---|---|
| n1–n5 | Follower | 1 | Nil |

先把會用到的兩個 action 原文擺上桌。`Timeout`：

```tla
\* Server i times out and starts a new election.
Timeout(i) == /\ state[i] \in {Follower, Candidate}
              /\ state' = [state EXCEPT ![i] = Candidate]
              /\ currentTerm' = [currentTerm EXCEPT ![i] = currentTerm[i] + 1]
              \* Most implementations would probably just set the local vote
              \* atomically, but messaging localhost for it is weaker.
              /\ votedFor' = [votedFor EXCEPT ![i] = Nil]
              /\ votesResponded' = [votesResponded EXCEPT ![i] = {}]
              /\ votesGranted'   = [votesGranted EXCEPT ![i] = {}]
              /\ voterLog'       = [voterLog EXCEPT ![i] = [j \in {} |-> <<>>]]
              /\ UNCHANGED <<messages, leaderVars, logVars>>
```

（註解又是「最小原子步」哲學：實作通常原子地投自己一票，spec 讓候選人對自己發訊息投票——「messaging localhost for it is weaker」，更弱的假設、更多的行為、更廣的涵蓋。）以及 `UpdateTerm`：

```tla
\* Any RPC with a newer term causes the recipient to advance its term first.
UpdateTerm(i, j, m) ==
    /\ m.mterm > currentTerm[i]
    /\ currentTerm'    = [currentTerm EXCEPT ![i] = m.mterm]
    /\ state'          = [state       EXCEPT ![i] = Follower]
    /\ votedFor'       = [votedFor    EXCEPT ![i] = Nil]
       \* messages is unchanged so m can be processed further.
    /\ UNCHANGED <<messages, candidateVars, leaderVars, logVars>>
```

### 第一輪：term 2，三人撞線

**步 1–3**：n1、n2、n5 相繼逾時（spec 不問理由：`Timeout` 永遠 enabled，這三步是合法 behavior 的一種選擇——現實裡是三台機器的選舉計時器幾乎同時到期，jitter 失靈的那一天）。各自執行 `Timeout`：轉 Candidate、term 升到 2、votedFor 清成 Nil、票箱清空。

| node | state | currentTerm | votedFor | votesGranted |
|---|---|---|---|---|
| n1 | Candidate | 2 | Nil | {} |
| n2 | Candidate | 2 | Nil | {} |
| n3 | Follower | 1 | Nil | — |
| n4 | Follower | 1 | Nil | — |
| n5 | Candidate | 2 | Nil | {} |

**步 4**：三位候選人各自對所有 server（含自己）執行 `RequestVote`，訊息進 bag。每則請求帶 mterm = 2、mlastLogTerm = 0、mlastLogIndex = 0（log 全空）。

**步 5–7（自投）**：n1 處理自己的請求：`HandleRequestVoteRequest(n1, n1, m)`——m.mterm = 2 = currentTerm ✓；logOk：0 = LastTerm(空) 且 0 ≥ Len(空) ✓（第二個 disjunct）；votedFor = Nil ∈ {Nil, n1} ✓ ⇒ grant，votedFor[n1] ≔ n1，回覆進 bag。接著 `HandleRequestVoteResponse(n1, n1, …)`：m.mterm = 2 = currentTerm ✓、mvoteGranted ⇒ votesGranted[n1] = {n1}。n2、n5 同理。

**步 8（n3 的票）**：n1 → n3 的請求先到。n3 的 currentTerm = 1 < 2，`HandleRequestVoteRequest` 的 guard `m.mterm <= currentTerm[i]` 不成立——先走 `UpdateTerm(n3, n1, m)`：term ≔ 2、維持 Follower、votedFor ≔ Nil，**訊息留在 bag**。下一步同一則訊息再進 handler：grant ✓，votedFor[n3] ≔ n1。回應送達後 votesGranted[n1] = {n1, n3}。

**步 9（n4 的票）**：對稱地，n2 → n4 的請求先到，兩步（UpdateTerm＋grant）後 votedFor[n4] ≔ n2，votesGranted[n2] = {n2, n4}。

**步 10（其餘請求全數碰壁）**：n2 → n3：m.mterm = 2 = currentTerm[n3] ✓、logOk ✓，但 votedFor[n3] = n1 ∉ {Nil, n2} ⇒ grant = FALSE，回 mvoteGranted = FALSE（票已投出，恕不退換）。n5 → n3、n1 → n4、n5 → n4 同型。候選人互投也一樣：n1 → n2 的請求遇上 votedFor[n2] = n2 ⇒ 拒。所有拒絕回應只讓 votesResponded 長大，votesGranted 不動。

**term 2 票數表（終局）**：

| 候選人 | 票來源 | 票數 | 過半（≥ 3）？ |
|---|---|---|---|
| n1 | {n1, n3} | 2 | ✗ |
| n2 | {n2, n4} | 2 | ✗ |
| n5 | {n5} | 1 | ✗ |

2 + 2 + 1 = 5，五張票發完，沒人過半。為什麼**這個 term 永遠選不出來**？五台機器的 votedFor 在 term 2 都已非 Nil；grant 要求 votedFor ∈ {Nil, j}，所以重送請求只可能重複拿到同一張票（冪等），票數凍結在 2/2/1。`BecomeLeader` 對三位候選人都不 enabled——`votesGranted[i] \in Quorum` 永遠為假。這就是 split vote：沒人輸，但也沒人贏。

**驗 Election Safety（term 2）**：當選 leader 數 = 0 ≤ 1 ✓。成立得有點空虛——這是誠實的空虛，性質只說「至多一個」，沒說「至少一個」。「終究會選出 leader」是 liveness，這份 spec 的 `Spec == Init /\ [][Next]_vars` 連 fairness 都沒寫，根本沒做這個承諾（ch07 的允許清單 vs 待辦清單）。現實中靠 randomized timeout 讓三人再度撞線的機率指數衰減，但機率與時間都不在 spec 的語彙裡；而 FLP（見 ch12）保證這種「壞運氣無限延續」的 behavior 在非同步模型下無法根除。

### 第二輪：term 3，n3 收割

**步 11**：n3 逾時（guard：Follower ∈ {Follower, Candidate} ✓）：Candidate、term ≔ 3、votedFor ≔ Nil，廣播 RequestVote（mterm = 3）。

**步 12**：n3 自投：votesGranted[n3] = {n3}，votedFor[n3] ≔ n3。

**步 13**：n1（Candidate，term 2）收到 n3 的請求：3 > 2 ⇒ `UpdateTerm`——**現任候選人就地退位**：Follower、term ≔ 3、votedFor ≔ Nil。同訊息再處理：grant ✓（log 同空，logOk；票未投）⇒ votedFor[n1] ≔ n3。回應到手：votesGranted[n3] = {n3, n1}。

**步 14**：n2 同理：votesGranted[n3] = {n3, n1, n2}。

**步 15**：`BecomeLeader(n3)`：state[n3] = Candidate ✓；votesGranted[n3] = {n3, n1, n2}，基數 3，3 × 2 = 6 > 5 ⇒ ∈ Quorum ✓。n3 成為 term 3 的 leader：nextIndex[n3] 全體 ≔ Len(空) + 1 = 1，matchIndex 全體 ≔ 0，elections 記下 ⟨eterm = 3, eleader = n3, …⟩。n4、n5 的票還沒進來？不需要——quorum 到手即當選；那些遲到的請求與回應之後送達時，n4、n5 會經由 UpdateTerm 跟上 term 3（n5 這位 term 2 的候選人同樣退位）；UpdateTerm 不消費訊息（步 8 走過的兩步路徑），所以兩人接著仍可能把這張遲到的票投給 n3——投或不投都是合法分支（非決定性，見 ch02），無關勝負。多餘的回應被 `DropStaleResponse` 清掉。

**最終狀態表**：

| node | state | currentTerm | votedFor |
|---|---|---|---|
| n1 | Follower | 3 | n3 |
| n2 | Follower | 3 | n3 |
| n3 | **Leader** | 3 | n3 |
| n4 | Follower | 2 → 3（訊息到達後） | n2 → n3 或 Nil |
| n5 | Candidate → Follower（同上） | 2 → 3 | n5 → n3 或 Nil |

**驗 Election Safety（全程）**：term 1 無人當選；term 2 無人當選；term 3 恰好 n3。「會不會 term 3 還冒出第二個 leader？」把論證寫成層級證明的骨架（工程師嚴謹度，完整機器驗證見延伸閱讀）：

- ⟨1⟩1. 固定 term T 內，每台 server 至多把票給一個候選人。**證**：votedFor 變成非 Nil 只發生在 grant 分支，而 grant 要求 votedFor ∈ {Nil, j}——只能從 Nil 設為 j，或維持同一個 j；會把 votedFor 清回 Nil 的兩個 action（Timeout、UpdateTerm）都同時把 currentTerm 抬高，term 不動則票不回收。
- ⟨1⟩2. 在 term T 當選需要一個 quorum 的票，且票全是 term T 的。**證**：BecomeLeader 要求 votesGranted ∈ Quorum；votesGranted 只被 HandleRequestVoteResponse 增長，其 guard 要求 m.mterm = currentTerm[i]。
- ⟨1⟩3. 假設 term T 有兩個 leader i ≠ j，由 ⟨1⟩2 各有 quorum Qᵢ、Qⱼ；Quorum 定義保證 Qᵢ ∩ Qⱼ ≠ ∅，取 v ∈ Qᵢ ∩ Qⱼ，則 v 在 term T 投了 i 也投了 j，與 ⟨1⟩1 矛盾。∎

## Raft vs Paxos：誰把複雜度搬去哪了

ch12 與本章各讀完一個共識協議，現在把它們並排。先說結論：**複雜度守恆**。共識該想清楚的事一件都沒少，Raft 做的是搬家——從「執行期」搬到「選舉期」，從「不變量難懂」搬到「規則清單較長」。

| 維度 | Paxos（見 ch12） | Raft |
|---|---|---|
| 角色結構 | 對稱：任何 proposer 隨時可發起，acceptor 規則一視同仁 | 強 leader：一切寫入經 leader，資料單向流動 |
| 「選哪個值」決定於 | 每次提案：phase 1 從 quorum 的回報裡挑出最高 ballot 的值 | 選舉時一次定案：up-to-date 投票限制保證當選者已持有全部 committed entries |
| log 結構 | 每個 slot 獨立跑共識，允許有洞 | 單一連續 log，禁止有洞 |
| 換 leader 的代價 | 隨時可換；新 proposer 要對未定的 slot 逐一補 phase 1 | 選舉本身就是交接：當選者不必回頭問任何人，直接覆寫分歧 |
| safety 的承載者 | acceptor 的承諾規則＋P2c 不變量 | 五條性質：投票限制與 commit 限制是兩道主閘門 |
| 理解難點 | 「為什麼這樣就對了」——不變量精巧，機制極簡 | 「規則為什麼這麼多」——每條都直白，合起來才見全貌 |

對照的核心是第二列。Paxos 把「我該提什麼值」的成本攤在**每一次提案**：phase 1 是一輪讀-改-寫，從 quorum 學到「可能已被選定的值」再接力（P2c 在背後撐腰，見 ch12）。Raft 把同一筆成本**一次付清在選舉**：投票者用 ⟨lastTerm, len⟩ 把「資訊不全的人」直接擋在門外，於是 leader 在位期間不必再問任何人「我可以寫嗎」——日常路徑變成無腦的單向複製，這就是工程上覺得 Raft 好寫的真正原因。代價也明碼標價：所有請求擠過一個 leader（吞吐瓶頸與熱點）；機制彼此咬合得緊（election、replication、commit 規則環環相扣，動一條要重新論證全部——題 2 讓你體會）；而 Paxos 的對稱性給了變體更多揮灑空間（Lamport 的 spec 甚至把這個自由度寫成 Voting → Consensus → Paxos 的精化層次，ch15 回收）。

從 TLA+ 的視角看也很有意思：Lamport 的 Paxos.tla 是分層的數學物件，抽象到沒有訊息遺失這回事（不需要——抽象層根本沒建模網路故障的細節）；raft.tla 是一張攤平的工程圖，471 行裡訊息重複、丟失、crash 重啟、持久化清單通通在場。一個是定理的形狀，一個是系統的形狀——這不是優劣，是兩位作者對「spec 該長什麼樣」的立場差異，你在 ch17 會看到業界兩種都用。

## 你手上的 Raft：etcd 與 K8s

最後接回你的日常。etcd 用 Raft 做複製，K8s 把所有 API 物件存在 etcd——你每天 `kubectl apply` 的 YAML、CronJob 的排程狀態、那些 controller 搶的分散式鎖（Lease 物件），底下都是本章的機制在跑：寫入走 leader、AppendEntries 推向 followers、過半確認後 commit。你維運直覺裡的「3 節點掛 1 台沒事」現在有了一行定義（Quorum）、「掛 2 台不能寫」有了證明義務（湊不出 quorum，AdvanceCommitIndex 永遠不 enabled）。業界怎麼用形式化方法對待這類系統、值不值得，是 ch17 的主題。

至於本章刻意略過的兩塊：**membership change**（joint consensus 與 single-server 變更——讓「換叢集成員」這件事本身也走共識）與 **snapshot/log compaction**（log 不能無限長，得截斷成快照），raft.tla 這版都沒建模，機制細節見延伸閱讀的 Ongaro 博士論文。

## 陷阱與防禦

| 故障模式 | 它怎麼騙你 | 防禦 |
|---|---|---|
| 把 Election Safety 讀成「任一時刻至多一個 leader」 | 性質是 **per term** 的。舊 term 的 leader 可能還不知道自己已被取代（BecomeLeader 不廣播），系統裡同時有兩台自認 leader 的機器——這完全合法 | 逐字讀性質：「in a given term」。stale leader 的寫入會被 followers 的 term 檢查拒收、它一收到高 term 訊息就退位；安全靠的是 term 戳章，不是「leader 唯一」的幻覺 |
| 「過半複製＝committed」 | 舊 term 的 entry 被新 leader 補到過半，看起來該 commit 了——commit 它，你就造出「已提交卻被覆寫」的反例（論文 Figure 8） | AdvanceCommitIndex 只對 `term = currentTerm` 的 entry 計票；舊 entry 只能搭新 entry 的便車間接提交。親手推一次（題 2），這條規則才會長在身上 |
| 把 history variables 當協議的一部分 | 看到 elections、allLogs、voterLog 以為實作要維護它們——白白背上無限增長的狀態 | 認註解：「would not be present in an implementation」。它們只為證明存在，不影響任何 guard 或轉移（ch14、ch15 詳論這類輔助變數） |
| 用太小的模型下太大的結論 | 3 節點驗過 = 5 節點也對？2+2+1 的三方 split vote 在 3 節點上根本擺不出來；某些 quorum 邊界情況只在 ≥ 5 節點現身 | small scope hypothesis 是賭注不是定理（ch09）：明寫你驗過的參數範圍；換參數前先想「哪些情境是這個規模擺不出來的」 |
| 以為 spec 保證「選舉終會成功」 | randomized timeout 寫在論文與每份實作裡，於是你以為 liveness 在 spec 裡——spec 沒有時間、沒有機率、沒有 fairness，split vote 無限重演是合法 behavior | 分層歸位：這份 spec 只扛 safety；liveness 論證屬於「fairness ＋ 時序假設」的世界（ch07），且受 FLP 天花板壓著（見 ch12） |
| 拿這份 spec 推 reconfiguration 的結論 | 「spec 驗過了所以 etcd 的成員變更也安全」——可是 Server 是固定常數，spec 根本沒建模 membership change | 先問「spec 的邊界在哪」再引用它的保證；超出邊界的主張一律重新建模（建模的誠實，ch08） |

## 紙上推演

### 題 1：誰有資格當選？（[20 分鐘] ★★）

5 個節點目前都在 term 6，log 如下（表中數字是各 index 上 entry 的 term）：

| node＼index | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| n1 | 1 | 1 | 4 | — |
| n2 | 1 | 1 | 4 | 4 |
| n3 | 1 | 1 | — | — |
| n4 | 1 | 1 | 4 | 4 |
| n5 | 1 | 1 | 2 | — |

(a) 對每個節點：若它現在發起 term 7 的選舉，**最理想情況下**（訊息順序任它挑）能拿到哪些票？誰有可能當選？逐一用投票版 logOk 驗。
(b) 已知 index 3 的 term-4 entry 已在 term 4 提交。哪些節點若當選會違反 Leader Completeness？投票限制有沒有把它們全部擋下？
(c) n2 與 n4 的 index 4 呢——若 n1 當選後用自己的 log 修剪它們，算不算丟失資料？

### 推演解答

(a) 投票者 v grant 候選人 c 的 logOk 條件：c.lastTerm > v.lastTerm，或（相等且 c.len ≥ v.len）。各節點的 ⟨lastTerm, len⟩：n1 = ⟨4, 3⟩、n2 = ⟨4, 4⟩、n3 = ⟨1, 2⟩、n4 = ⟨4, 4⟩、n5 = ⟨2, 3⟩。

| 候選人 | 能拿到的票（含自己） | 上限 | 過半？ |
|---|---|---|---|
| n1 ⟨4,3⟩ | n1；n3（4>1）；n5（4>2）。n2、n4 拒：term 打平但 3 ≥ 4 不成立 | 3 | ✓ 可當選 |
| n2 ⟨4,4⟩ | 全部：n1（打平且 4≥3）、n3、n4（打平且 4≥4）、n5 | 5 | ✓ 可當選 |
| n3 ⟨1,2⟩ | 只有自己：對所有人 1 > lastTerm 皆假、打平也不成立 | 1 | ✗ |
| n4 ⟨4,4⟩ | 同 n2 | 5 | ✓ 可當選 |
| n5 ⟨2,3⟩ | n5；n3（2>1）。其餘拒 | 2 | ✗ |

(b) committed 的 index 1–3 必須在未來所有 leader 手上。n3 缺 index 3、n5 的 index 3 是不同的 entry（term 2）——它們當選都違反 Leader Completeness。對照 (a)：恰好就是這兩位選不上。這不是巧合，是設計：committed entry 在過半機器上（這裡是 n1、n2、n4），任何 quorum 必與這過半相交，交集裡的機器用 logOk 把「不夠新」的候選人擋掉。性質與機制在這題裡互為鏡像。

(c) 不算。index 4 只在 n2、n4 上（2/5，未過半），而且 term 6 期間沒有任何機制能提交 term 4 的舊 entry（commit 限制）——它**不是** committed entry，只是上個時代未完成的草稿。n1 當選 term 7 後，AppendEntries 的一致性檢查會在 index 4 發現衝突（或直接以 n1 的 log 長度為準修剪），n2、n4 的尾巴被刪——Leader Completeness 與 State Machine Safety 毫髮無傷，因為承諾只覆蓋 committed。注意一個容易刺痛直覺的事實：**n1 比 n2 短卻能當選**——「夠新」不等於「最長」，丟掉沒提交的東西不算丟資料。client 端視角：那筆 entry 沒收到過 ack，本來就該重試（你的 at-least-once 直覺，ch02／ch08）。

### 題 2：拆掉一條規則，造一個壞 Raft（[30 分鐘] ★★★）

把 AdvanceCommitIndex 裡的 term 檢查刪掉——也就是把

```tla
           newCommitIndex ==
              IF /\ agreeIndexes /= {}
                 /\ log[i][Max(agreeIndexes)].term = currentTerm[i]
```

的第二個合取拿掉，允許 leader 對**任何** term 的 entry 計票提交。請在 5 節點上構造一條 behavior，讓一筆「已提交」的 entry 之後被覆寫（違反 Leader Completeness，進而威脅 State Machine Safety）。然後指出：真 Raft 的這條 term 檢查如何讓你的反例走不通。逐步列狀態，標清楚每一步誰在哪個 term、log 長什麼樣。

### 推演解答

這是論文 Figure 8 的場景，換上本書的節點名。記 A = ⟨term 2 的 entry⟩、B = ⟨term 3 的 entry⟩。

**第 1 幕（term 2）**：n1 當選 term 2 的 leader（全空 log，票 {n1, n2, n3}）。client 寫入 A：n1 的 log = [A]。AppendEntries 只成功送達 n2（n2 log = [A]）；給其他人的訊息被 DropMessage 吃掉。A 在 2/5 台上，未提交。n1 失聯（網路分割，它自己不知道）。

**第 2 幕（term 3）**：n5 逾時當選 term 3（票 {n3, n4, n5}——三台 log 皆空或不比 n5 新：n3、n4 空 log，logOk 打平成立）。client 寫入 B：n5 的 log = [B]。**還沒送出任何 AppendEntries**，n5 也失聯。

**第 3 幕（term 4）**：n1 回歸，逾時兩次（Timeout 沒有前置條件，連按兩次合法）把 term 推到 4，發起選舉：n2（⟨2,1⟩ 對 ⟨2,1⟩ 打平且 1 ≥ 1 ✓）、n3（空 ✓）、n4（空 ✓）都 grant——票 {n1, n2, n3}，n1 當選 term 4。它開始修復 followers：把 A 補給 n3（n3 log = [A]）。現在 A 在 {n1, n2, n3} = 3/5 台上。

**第 4 幕（壞規則發動）**：壞 AdvanceCommitIndex 看到 Agree(1) = {n1, n2, n3} ∈ Quorum，不檢查 term，commitIndex[n1] ≔ 1。**A 提交了**：n1 apply A、回覆 client「成功」。隨後 n1 再度失聯——注意它從頭到尾沒寫下任何 term 4 的 entry。

**第 5 幕（term 5，覆寫）**：n5 回歸，逾時把 term 推到 5，發起選舉：它的 ⟨lastTerm, len⟩ = ⟨3, 1⟩。n3：3 > 2 ✓ grant；n4：3 > 0 ✓ grant；加自己——票 {n3, n4, n5}，當選。n5 修復 followers：AppendEntries（prevLogIndex = 0，entry B）發向全體；n2、n3 的 index 1 是 A（term 2 ≠ 3）⇒ 衝突分支刪掉 A、再 append B。連 n1 回歸後也會被同樣修剪。終局：所有 log = [B]。**A——一筆已 ack 給 client 的 committed entry——從宇宙中消失。**Leader Completeness 死於第 5 幕（A 在 term 4 提交，term 5 的 leader 卻沒有它）；State Machine Safety 接著死（n1 已在 index 1 apply 了 A，其餘機器將在同一 index apply B）。

**真 Raft 怎麼擋**：第 4 幕走不通。A 的 term 是 2 ≠ currentTerm 4，湊滿三台也不提交。n1 必須先收一筆 term 4 的新 entry C、把它複製到過半（設 {n1, n2, n3}）——此時 Max(agreeIndexes) 落在 C，term 檢查通過，commitIndex 一口氣蓋過 index 1，**A 搭 C 的便車間接提交**。而一旦那三台的 lastTerm = 4，第 5 幕的 n5（⟨3, 1⟩）再也選不上：任何 quorum 都與 {n1, n2, n3} 相交，交集那台用 logOk 拒投，n5 至多拿 {n4, n5} 兩票。投票限制與 commit 限制是同一條防線的兩段——拆掉任何一段，另一段獨木難支。這也回答了「規則為什麼長這樣」：每一條看似多餘的合取，背後都有一條等著發生的反例。

### 題 3：spec 閱讀題——term 不對齊的訊息去了哪？（[15 分鐘] ★★）

(a) HandleRequestVoteRequest 的 guard 是 `m.mterm <= currentTerm[i]`。m.mterm **大於** currentTerm[i] 的請求，spec 在哪裡、怎麼處理？為什麼 UpdateTerm 的 UNCHANGED 清單裡有 messages 這件事至關重要？
(b) m.mterm **小於** currentTerm[i] 的請求會拿到票嗎？handler 回覆什麼？這個回覆對發送者有什麼用？

### 推演解答

(a) 在 `Receive(m)` 的析取裡，`UpdateTerm(i, j, m)` 是第一個 disjunct：guard 是 `m.mterm > currentTerm[i]`，效果是把 i 的 term 追平、退回 Follower、清空 votedFor。關鍵在原文註解「messages is unchanged so m can be processed further」——UpdateTerm **不消費訊息**。若它把 m 吃掉，這則請求就永遠失去被投票的機會，候選人少收一張本該到手的票（safety 不破，但行為集合錯了——你建模的不再是 Raft）。留著 m，下一步同一則訊息再進 HandleRequestVoteRequest，此時 term 已相等，正常走 grant 判斷。一次「收到高 term 請求」= 兩個原子步，這是 worked example 步 8 你親手走過的路徑。

(b) 不會。grant 的第一個合取要求 `m.mterm = currentTerm[i]`，stale 請求（m.mterm < currentTerm[i]）使 grant = FALSE——但 action 照樣執行，回覆 ⟨mvoteGranted = FALSE, mterm = currentTerm[i]⟩。這個回覆是糾錯信：發送者收到帶著更高 term 的回應，自己觸發 UpdateTerm 退回 Follower、追上時代。一個在舊 term 裡奮戰的殭屍候選人，就是被這種「拒絕＋附上新 term」的回覆喚醒的。順帶一提：對 stale 的**回應**（不是請求），spec 用 DropStaleResponse 直接丟棄——請求值得回覆糾錯，過期的回應則毫無資訊價值，這個不對稱本身就是設計。

## 自我檢核

口頭回答，講得出來才算過：

1. 五條 safety 性質各用一句白話說出來。哪一條是端到端的承諾？其他四條各自在哪個機制裡被執行？
2. Election Safety 為什麼成立？兩個要素（一 term 一票、quorum 相交）各由 spec 的哪一行扛著？它跟「任一時刻至多一個 leader」差在哪、為什麼後者不成立也沒關係？
3. raft.tla 有兩個 logOk——投票版與 AppendEntries 版。各檢查什麼？為什麼是兩個不同的條件、各替哪條性質服務？
4. 為什麼 leader 只能對 current term 的 entry 計票提交？描述放寬後反例的形狀（誰在哪個 term 提交了什麼、誰把它覆寫了）。
5. 「Raft 把複雜度從提案時搬到選舉時」——展開講：Paxos 的 phase 1 在每次提案做什麼？Raft 用什麼把這件事一次付清？代價是什麼？
6. raft.tla 裡哪三個變數是 history variables？它們為什麼不影響協議行為、又為什麼存在？
7. 這份 spec 對「選舉終會成功」做了什麼承諾？randomized timeout 在哪裡——spec、論文、還是實作？split vote 無限重演的 behavior 合法嗎？
8. 你的 3 節點 etcd 掛 1 台還能寫、掛 2 台不能——用 raft.tla 的 Quorum 定義與 AdvanceCommitIndex 的 guard 解釋給同事聽。

## 延伸閱讀

- **In Search of an Understandable Consensus Algorithm (Extended Version)**（Diego Ongaro & John Ousterhout）：`https://raft.github.io/raft.pdf`。本章五條性質的出處（Figure 3）；§5.4.1 的投票限制與 Figure 8（題 2 的原版）是必讀段落；§6–7 是 membership change 與 snapshot 的概要。會議版發表於 USENIX ATC 2014，官網稱其獲 Best Paper Award。
- **raft.tla 原始 spec**（Diego Ongaro）：`https://github.com/ongardie/raft.tla`。本章所有引文的出處，CC-BY 4.0；README 自述比博士論文版略有更新，並提醒想跑 TLC 的人參考 PR #4 的修改（2026-06 查證）。通讀一次全文（471 行）是檢驗本章學習成果的最好方式。
- **Consensus: Bridging Theory and Practice**（Diego Ongaro 博士論文，Stanford, 2014）：`https://github.com/ongardie/dissertation`。membership change（第 4 章）與 log compaction 各有專章；第 8 章與附錄是 safety 證明——README 並提到 Verdi 團隊後來在 Coq 裡完成了核心安全性的機器證明，可作為 ch16「嚴謹度光譜」的真實樣本。
- **raft.github.io**：Raft 官網。內建 5 節點選舉與複製的互動視覺化（把本章 worked example 動起來），另收錄各語言實作清單與歷年演講；頁面也連到逐步動畫教學 The Secret Lives of Data。
- **ch12 ⇄ ch13 對讀**：把 Lamport 的 Paxos.tla（見 ch12 的精讀與 `tlaplus/Examples` 路徑）與本章的 raft.tla 並排翻一次——一個是分層的數學物件、一個是攤平的工程圖。兩種 spec 風格的取捨，ch15（refinement）與 ch17（業界實務）各給一半答案。
