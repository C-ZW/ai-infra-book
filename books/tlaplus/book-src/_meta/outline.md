# 全書大綱（內部文件，非書籍內容）

書名（工作名）：《把系統寫成定理：TLA+ 與形式化方法》
形態：18 章、六個 Part、3 個附錄。紙上推演書（不裝工具、不寫程式）。
每章必須遵守 `style-guide.md` 的骨架與深度標準；時效性事實以 `landscape-2026-06.md` 為錨。

## 全書敘事弧

從「你寫過的併發 bug」出發 → 把系統看成狀態機 → 磨利數學工具 → 學會 TLA+ 這門「描述狀態機的語言」→ 精讀四個經典協議（手推）→ 爬上證明層（歸納不變量、refinement、機器證明）→ 回到地面（業界案例、方法地圖）。

前一章的問題是後一章的動機：測試蓋不住（ch01）→ 那描述系統要用什麼心智模型（ch02）→ 描述要精確需要邏輯與集合（ch03–04）→「每個可達狀態都成立」怎麼證（ch05）→ 這套數學怎麼變成一門語言（ch06–08）→ 機器怎麼自動找反例（ch09）→ 在真協議上用（ch10–13）→ 有限模型不夠、要證明（ch14–16）→ 業界到底怎麼用、我下一步去哪（ch17–18）。

## 跨章基準（一致性掃描的依據；各章不得另創數字與命名）

**貫穿範例「結算系統」**（源自讀者真實經歷：SQS → idempotent consumers → 入帳）：

| 元素 | 基準 | 首次出現 |
|---|---|---|
| v0 參數 | 訊息 2 則（m1, m2）、consumer 先 1 個再加到 2 個、ledger 為 msgId → 是否已入帳 | ch02 |
| v1 升級 | 加 consumer crash、redelivery（at-least-once）、dedup 表 | ch08 |
| v1 實際定案（ch08 撰寫時演進，後續章節以此為準） | `ledger ∈ [Msgs → Nat]`（計次，v0 的 BOOLEAN 看不出 double-pay）；Settle 拆成 Credit＋Ack；新增 Crash(c)；`dedup ⊆ Msgs` 單調只進不出；`NoDoublePay ≜ ∀m: ledger[m] ≤ 1`；基準參數下可達狀態 41（ch09 三路複核） | ch08 |
| safety 性質名 | `NoDoublePay`（同一 msgId 至多入帳一次） | ch02 |
| liveness 性質名 | `AllPaid`（每則訊息終會入帳） | ch07 |

**協議精讀的固定配置**：

| 協議 | 配置 | 命名基準 |
|---|---|---|
| DieHard | 3 與 5 加侖壺、目標 4 加侖 | 變數 small / big（ch08） |
| Peterson | process {0, 1} | 性質 `MutualExclusion`（ch10） |
| 2PC | 1 TM ＋ 2 RM：{r1, r2} | 沿用 Lamport TwoPhase 命名：rmState ∈ {"working","prepared","committed","aborted"}；性質 `TCConsistent`（ch11） |
| Paxos | 3 acceptors {a1, a2, a3}、2 proposers、ballot 1 與 2 | 不變量稱 P2c（沿 Lamport 編號）（ch12） |
| Raft | 5 nodes、term 從 1 起 | 性質名沿 Raft 論文（Leader Completeness 等）（ch13） |

**全書符號**：依 style-guide「數學符號規範」；證明一律 ⟨1⟩1 層級格式（ch05 起）。

**全域不涵蓋**（任何章都不展開，最多一句話＋指向延伸閱讀）：記憶體一致性模型（TSO/弱序）、密碼學協議驗證、Dafny 等程式碼級驗證教學、機率模型檢查（PRISM）、CUDA/GPU、任何工具安裝步驟。

---

## Part I — 為什麼，以及用什麼眼睛看系統（ch01–02）

### ch01 — 測試的極限：為什麼需要形式化方法
- **目標**：讀完能說出「測試與證明在能力上的本質差別」，且能畫出形式化方法全景地圖、指出 TLA+ 的位置。
- **必涵蓋**：一個具體併發 bug 開場（結算 pipeline 風格的 race：dedup 檢查與入帳之間被插隊）；為什麼測試抓不到——調度不可控＋狀態空間指數；AWS CACM 2015 的證詞（DynamoDB 35 步 bug 等，數據照 landscape）；全景地圖：規格層 vs 程式碼層、model checking vs theorem proving、輕量 vs 重型；「寫 spec 的最大價值是先想清楚」論點；本書路線圖（全書 ASCII 地圖首次出場）。
- **不涵蓋**：TLA+ 語法（ch06）、邏輯符號（ch03）、案例細節（ch17）。
- **橋接**：你修過的 race condition、k6 壓測抓不到的 heisenbug、code review 裡「這裡會不會被插隊」的直覺。
- **Worked example**：2 個 thread 各 3 步操作共享 counter，手算交錯數 C(6,3)=20，列出其中壞的調度；推到 10 步 ×3 thread 看組合爆炸。
- **紙上推演**：數另一組交錯數並找出壞調度；給一個「測過 1000 次都對」的程式找出測試漏掉的調度。

### ch02 — 一切都是狀態機：state、behavior、invariant
- **目標**：建立全書心智模型：系統＝允許的行為集合；能把一個小系統的狀態空間完整畫出來。
- **必涵蓋**：state＝變數的一組賦值；step；behavior＝（可無限的）狀態序列；規格＝允許行為的集合；非決定性建模 crash 與重送（不是隨機，是「都可能」）；引入結算系統 v0（基準表參數）；invariant 直覺版：所有可達狀態都成立的述語、`NoDoublePay` 首次登場；safety vs liveness 直覺版（一句話對比，正式定義見 ch07）；抽象的選擇：建模什麼、忽略什麼。
- **不涵蓋**：TLA+ 語法（ch06）、時序符號（ch07）、邏輯記號嚴格化（ch03）。
- **橋接**：DB 的一筆 row 就是 state、transaction log 就是 behavior；redux/event sourcing 的「狀態＋事件」你早就在寫。
- **Worked example**：手畫結算系統 v0 在（2 msgs, 1 consumer）的完整狀態空間圖；加到 2 consumers 後手算狀態數成長，體感爆炸。
- **紙上推演**：判斷給定 behavior 是否合法；給一個候選 invariant 找出打破它的可達狀態；幫 v0 加「consumer 重啟」後重畫狀態圖。

## Part II — 數學地基（ch03–05）

### ch03 — 命題與謂詞邏輯：精確說話的語法
- **目標**：能把白話業務規則翻成邏輯式、做否定推移，並對 vacuous truth 有肌肉記憶。
- **必涵蓋**：命題與真值；∧ ∨ ¬ ⇒ ≡ 與真值表；**⇒ 的陷阱：前件為假則整句為真（vacuous truth）**——埋「invariant 假通過」伏筆（ch14 回收）；∀ ∃、bound/free、否定推移 ¬∀=∃¬；述語；把規則翻成邏輯式的方法論（先找量詞範圍）。
- **不涵蓋**：集合論（ch04）、歸納（ch05）、時序算子（ch07）、形式證明系統（自然演繹不教，本書用「工程師的嚴謹」）。
- **橋接**：⇒ ≈ guard clause；vacuous truth ≈ `[].every(...)` 回 true；∀∃ ≈ SQL 的 NOT EXISTS 改寫。
- **Worked example**：把「已發放的獎勵不會再發」翻成謂詞式，否定它得到「bug 的形狀」，展示找反例＝證明否定式可滿足。
- **紙上推演**：真值表驗證 2 條等價式；中⇄邏輯互翻 3 題；否定推移練習（含巢狀量詞）。

### ch04 — 集合、函數、關係：TLA+ 的原料
- **目標**：能用集合語言精確定義資料結構與系統狀態；理解「函數＝查表」的 TLA+ 世界觀。
- **必涵蓋**：集合操作、冪集；tuple 與 sequence；函數（domain、把函數當總是查得到的表）；record（＝定義域是欄位名的函數）；關係；multiset 概念（at-least-once 的訊息該用 set 還是 bag——誠實討論）；有限/無限；一句話：TLA+ 的數學底是 ZF 集合論、一切皆集合。
- **不涵蓋**：TLA+ 語法本體（ch06/08，可預告「這些在 TLA+ 都是一級公民」）；基數/序數理論。
- **橋接**：function ≈ Map/hash；record ≈ JSON object；sequence ≈ array；冪集 ≈ feature flags 全組合；關係 ≈ join table。
- **Worked example**：用集合語言定義結算系統 v0 的完整狀態型別（每個變數的值域），並算出狀態空間大小上界——與 ch02 的手畫圖對帳。
- **紙上推演**：集合運算手算；把一張 DB schema 翻成 record 與關係；「用 set 建模佇列會丟失什麼資訊」分析題。

### ch05 — 歸納法：證明「永遠」的唯一辦法
- **目標**：能手寫層級式歸納證明；理解 inductive invariant 的形狀（全書最重要的單一概念）。
- **必涵蓋**：數學歸納、強歸納、結構歸納；遞推到狀態機：Init 成立＋每步保持 ⇒ 永遠成立；**inductive invariant 首次正式登場**（白話＋狀態機語言，不用 TLA+ 語法）；⟨1⟩1 層級證明格式首次使用並成為全書標準；手證結算系統 v0 的 `NoDoublePay`；首次示範「invariant 為真但不 inductive、證不動」的現象（只點出，技藝在 ch14）。
- **不涵蓋**：TLA+ 語法；invariant 強化技藝深論（ch14）；TLAPS（ch16）。
- **橋接**：loop invariant；「每次 migration 後 schema 都一致」的遞推信心；CI 的 green build 鏈。
- **Worked example**：一個小狀態機 invariant 的完整證明，包含一次失敗 →發現需要強化→ 成功的全過程（誠實展示彎路）。
- **紙上推演**：自然數歸納 1 題；狀態機 invariant 證明 2 題（一題會卡、需要小強化）。

## Part III — TLA+ 與時序邏輯（ch06–09）

### ch06 — 動作邏輯：TLA 的核心設計
- **目標**：能讀懂 Init ∧ □[Next]_vars 的每一個字，並手追 behavior；理解 stuttering 為什麼是刻意設計。
- **必涵蓋**：TLA+ 語法第一課：VARIABLES、primed/unprimed、action＝前後狀態的述語；Init/Next/□[Next]_vars 的拆解；**stuttering 的動機**（允許「不動」的步——明寫這是 ch15 refinement 的伏筆）；UNCHANGED；ENABLED 概念；ASCII ⇄ Unicode 對照表首次出現；把結算系統 v0 寫成第一個 TLA+ spec（精簡版，逐行解說）。
- **不涵蓋**：□ ◇ 的一般時序理論與 fairness（ch07）；完整 spec 慣例、PlusCal（ch08）；TLC（ch09）。
- **橋接**：action ≈ transaction 的 before/after snapshot；x′ ≈ 「commit 後的值」；stuttering ≈ 監控系統兩次取樣之間「看起來沒事發生」。
- **Worked example**：逐行讀 10 行的 v0 spec，手追一條 4 步 behavior（含一步 stuttering），逐步驗證每步滿足 Next 或 UNCHANGED。
- **紙上推演**：白話規則→action 翻譯 2 題；判斷給定 behavior 是否滿足 □[Next]_vars（含 stuttering 陷阱）；找出一個 action 寫法 bug（漏了 UNCHANGED）。

### ch07 — 時序邏輯：safety、liveness 與 fairness
- **目標**：能用 □ ◇ ~> 寫性質、分類 safety/liveness，並解釋為什麼沒有 fairness 的 liveness 是空話。
- **必涵蓋**：□、◇、□◇、◇□、~>（leads-to）；safety/liveness 正式定義（直覺版 Alpern–Schneider：safety 可被有限前綴反駁、liveness 永遠可補救）；□[Next]_vars 只給 safety、要 liveness 得加 fairness；WF 與 SF 的定義、差異、各自的典型場景；`AllPaid` 首次正式寫出（含該配哪種 fairness）；**陷阱主軸：忘了 fairness，liveness 空洞成立或空洞失敗**。
- **不涵蓋**：liveness 的證明技術（ch14 淺談 leads-to，不深入）；模型檢查 liveness 的演算法（ch09）；TLA+ 完整 spec 結構（ch08）。
- **橋接**：liveness ≈ 「SQS 訊息終究會被消費」的營運假設；WF ≈ consumer 健康時必處理；SF ≈ 反覆 crash-restart 的 consumer 也終會處理；deadlock alert ≈ ◇ 的反例。
- **Worked example**：對結算系統列 4 條白話性質 → 分類 safety/liveness → 寫成時序公式 → 標出各需要的 fairness。
- **紙上推演**：公式⇄白話互翻；對給定無限 behavior 判斷 □◇p 與 ◇□p；找出「哪條 liveness 主張因缺 fairness 而不成立」。

### ch08 — 完整的 spec：從 DieHard 到結算系統 v1
- **目標**：能獨立讀懂一份沒看過的中小型 spec；看懂 PlusCal 並對照其 TLA+ 翻譯。
- **必涵蓋**：spec 解剖學：MODULE/EXTENDS/CONSTANTS/ASSUME/VARIABLES/TypeOK/Init/Next/Spec/THEOREM；DieHard 精讀（基準表配置；「把目標寫成 invariant 的否定、讓反例變成解」的招式）；TypeOK 的角色與為什麼它幾乎總是第一個 invariant；PlusCal 簡介（讀得懂即可、明寫本書不要求會寫）與翻譯後 TLA+ 的 pc 變數；結算系統升級 v1：consumer crash、redelivery、dedup 表（基準表）；建模的誠實：v1 哪些現實被抽象掉了。
- **不涵蓋**：TLC 原理（ch09）；協議案例（Part IV）；refinement（ch15，但可一句話預告 v1 與某個抽象 spec 的關係）。
- **橋接**：DieHard＝面試白板題的正式化；redelivery/dedup 是讀者每天的生活。
- **Worked example**：DieHard 全狀態空間手畫（含轉移邊），手找達到 4 加侖的最短路徑，對照「invariant 反例＝解」。
- **紙上推演**：讀一份沒看過的 10–20 行 spec 答理解題；幫 spec 補 TypeOK；找出 spec 與白話需求的一處不一致。

### ch09 — 模型檢查器的原理：TLC 能與不能
- **目標**：不跑工具也能準確說出 TLC 怎麼工作、反例 trace 怎麼讀、以及它證明不了什麼。
- **必涵蓋**：顯式狀態 BFS；fingerprint（≈hash）與碰撞的意義；反例＝state graph 上的最短路徑（所以 trace 短而精）；state explosion 手算；緩解手段一覽（constraint、symmetry、抽象——原理層）；liveness 檢查＝找滿足 fairness 的壞循環（SCC，直覺版）；**TLC 的極限：有限參數的窮舉≠定理**、small scope hypothesis 的辯護與限度；Apalache 一句話對照（符號式、細節 ch16）；TLC 風格反例 trace 的讀法訓練（之後協議章會大量出現，這裡建立讀 trace 的能力）。
- **不涵蓋**：TLC 操作/設定教學（本書不動鍵盤）；TLAPS/Apalache 細節（ch16）。
- **橋接**：BFS／圖遍歷你會；fingerprint ≈ hash；state explosion ≈ 容量規劃的組合直覺；反例 trace ≈ 一條最短重現步驟的 bug report。
- **Worked example**：結算系統 v1 在基準參數下：狀態空間上界手算 vs 可達狀態估算；手動模擬 BFS 前 3 層、標出新發現狀態。
- **紙上推演**：讀一份 TLC 風格反例 trace 指出 bug 在哪步；估兩組參數的狀態數並判斷哪個可行；「加一個變數讓狀態空間爆多少倍」估算題。

## Part IV — 經典協議精讀（ch10–13）

### ch10 — 互斥：Peterson 演算法全手推
- **目標**：完成全書第一次「整個協議的狀態空間手推」；能解釋 naive 方案壞在哪、Peterson 為什麼對。
- **必涵蓋**：互斥問題定義（safety：`MutualExclusion`；liveness：想進終會進）；naive 兩 flag 方案手推找反例；Peterson（基準表配置）精讀：spec 逐段解說；**全狀態空間手推驗證 invariant**（全書招牌 worked example：節點全畫、每條邊驗一次）；deadlock vs starvation 區分；fairness 在 liveness 主張的角色（回收 ch07）。
- **不涵蓋**：共識（ch12）；硬體記憶體模型／弱一致性（全域不涵蓋，一句話聲明假設「步是原子的」＋指延伸閱讀）；鎖的工程實作。
- **橋接**：DB row lock、Redis SETNX 分散式鎖：它們的 safety/liveness 各自靠什麼；你排查過的鎖競爭。
- **Worked example**：Peterson 可達狀態空間完整手推＋逐邊驗 `MutualExclusion`（規模控制在可頁面內完成；確切狀態數由寫章 agent 自行推導並自我複核，不得抄外部數字）。
- **紙上推演**：手推 naive 方案的反例 trace；驗證某條邊保持 invariant；改一行 Peterson 讓它壞、找出反例。

### ch11 — Two-Phase Commit：把你寫過的交易正式化
- **目標**：能精讀 Lamport 的 TCommit/TwoPhase（對照原文）；能手推 blocking scenario 並解釋為什麼 blocking 是本質而非 bug。
- **必涵蓋**：交易承諾問題定義；`TCConsistent`（不能一個 commit 一個 abort）；TCommit（規格）與 TwoPhase（協議）兩層——這本身就是 refinement 的活教材（預告 ch15）；crash 與訊息遺失的建模選擇；**TM 單點與 blocking 的本質**（prepared 的 RM 不能自行決定）；3PC 一段帶過（為什麼沒解決問題）；與 Paxos Commit 的關係（ch12 伏筆）。
- **不涵蓋**：Paxos 本體（ch12）；saga/補償模式深論（橋接帶過）；XA 工程細節。
- **橋接**：讀者的訂單結算與 in-doubt transaction 經驗；「prepared 卡住」＝你看過的懸掛交易。
- **Worked example**：1 TM＋2 RM（基準表）手推「TM 在收齊 prepared 後 crash」的完整 scenario，展示 r1 r2 永遠卡住；對照 `TCConsistent` 全程未破。
- **紙上推演**：證 `TCConsistent` 的一個關鍵歸納步驟；設計一個「看似修好 blocking」的變體並親手找出它的反例或新弱點。

### ch12 — Paxos：共識的不變量
- **目標**：用「不變量先於演算法」的順序理解 Paxos；能手推 quorum intersection 如何防止分歧。
- **必涵蓋**：共識問題（agreement/validity/termination）；FLP 不可能定理一句話版（非同步＋crash ⇒ 沒有確定性又必然終止的共識）→ 所以 safety 無條件、liveness 看天吃飯；Single-decree Paxos（Synod）：ballot、phase 1/2、quorum intersection；**P2c 不變量是整個演算法的「為什麼」**；Voting → Consensus → Paxos 的層次（refinement 預告，ch15 回收）；為什麼大家覺得 Paxos 難：論文順序 vs 不變量順序。
- **不涵蓋**：Multi-Paxos/工程化（ch13 對照時帶）；Raft（ch13）；refinement 正式機械（ch15）；FLP 證明本體（不證，延伸閱讀）。
- **橋接**：quorum＝majority 你懂；ballot ≈ optimistic lock 版本號；「兩個 proposer 互踩」≈ 重試風暴。
- **Worked example**：3 acceptors＋2 proposers（基準表）手推雙 proposer 競爭：先展示沒有 phase 1 約束會分歧，再展示 quorum intersection＋P2c 如何擋下。
- **紙上推演**：打破 quorum 假設（2/4 acceptors）構造分歧反例；在小例上驗 P2c；判斷一個變體協議是否仍滿足 agreement。

### ch13 — Raft：工程化的共識，對照精讀
- **目標**：能讀 Ongaro 的 raft.tla 選段；能用 safety 性質清單對照 Paxos 與 Raft 的設計取捨。
- **必涵蓋**：Raft 的設計目標（understandability 作為一級需求）；leader election、log replication 的機制概要；五條 safety 性質（Election Safety、Leader Append-Only、Log Matching、Leader Completeness、State Machine Safety）；raft.tla 精讀 2~3 段（對照 landscape 的原文 URL）；Raft vs Paxos：誰把複雜度搬去哪了；etcd/K8s 一段（深度在 ch17）。
- **不涵蓋**：membership change／snapshot 細節（一句話＋延伸閱讀）；實作層（線程模型等）；案例研究深度（ch17）。
- **橋接**：讀者用過 etcd（K8s）；term ≈ epoch/generation 的既有直覺；split vote ≈ 重試碰撞。
- **Worked example**：5 nodes（基準表）手推一次含 split vote 的選舉：兩輪 term、票數表、誰最終當選、Election Safety 全程驗證。
- **紙上推演**：給一組 node logs 判斷誰有資格當選（Log Matching/Completeness 應用）；構造一個違反 Leader Completeness 的「壞 Raft」變體並指出哪條規則擋住它。

## Part V — 證明（ch14–16）

### ch14 — 歸納不變量：證明 safety 的技藝
- **目標**：能對中小型 spec 手寫完整的 inductive invariant 證明；掌握「不 inductive 就強化」的迴圈。
- **必涵蓋**：為什麼 TLC 不夠（無限狀態、任意參數、組合爆炸）；方法論三件套：Init⇒Inv、Inv∧Next⇒Inv′、Inv⇒Safety；**核心難點：Safety 本身通常不 inductive**——反例導向的強化迴圈（從失敗的證明步驟讀出缺的資訊）；輔助述語＝把「歷史」編碼進狀態述語；完整手證（a）結算系統 v1 的 `NoDoublePay`（b）2PC 的 `TCConsistent`（全書證明高峰）；leads-to 證明淺談（liveness 證明長什麼樣、本書不深入）；vacuous truth 伏筆回收（ch03）：太強的前件讓歸納步空洞通過的假象。
- **不涵蓋**：refinement（ch15）；TLAPS 語法（ch16）；liveness 證明完整理論。
- **橋接**：強化迴圈 ≈ debug 迴圈（反例＝失敗測試）；輔助述語 ≈ 為了排查而加的 audit 欄位。
- **Worked example**：`TCConsistent` 的完整層級證明（⟨1⟩ 格式），含一次「歸納步卡住 → 從卡點讀出要強化什麼 → 重證」的全過程。
- **紙上推演**：三個候選 invariant 判斷哪個 inductive（並指出非 inductive 者的「壞前驅狀態」）；強化練習 1 題；驗一個歸納步 2 題。

### ch15 — Refinement：實作蘊涵規格
- **目標**：能解釋「實作 ⇒ 規格」為什麼是蘊涵、stuttering 如何讓它成立；能手寫小型 refinement mapping。
- **必涵蓋**：規格與實作是同一種東西（都是時序公式）→ 「實作正確」＝ Impl ⇒ Spec；refinement mapping：把實作狀態映到規格狀態、每個實作步映成規格步或 stuttering（**ch06 伏筆兌現：stuttering 是為了這一刻**）；INSTANCE／substitution 的讀法；TCommit/TwoPhase 回收（ch11 的兩層正式接上）；auxiliary variables 概念層（history/prophecy 是什麼、為什麼有時非加不可；不教構造細節）；結算系統收官：v1 refine 抽象的 exactly-once ledger 規格——「at-least-once＋dedup 實作了 exactly-once」這句日常黑話的定理化。
- **不涵蓋**：prophecy variables 完整理論（指向 Lamport–Abadi 論文）；TLAPS 寫法（ch16）；液態的「refinement 一定存在嗎」理論深水區（一句話＋延伸閱讀）。
- **橋接**：介面與實作的契約、Liskov 替換的直覺；「對外行為不變的重構」＝ refinement 保持。
- **Worked example**：手寫結算系統 v1 → exactly-once 規格的 refinement mapping，逐 action 驗證映射（含哪些實作步映成 stuttering）。
- **紙上推演**：給小實作與小規格找 mapping；指出一個 mapping 為什麼失敗、需要什麼 auxiliary variable；判斷兩個 spec 誰 refine 誰。

### ch16 — 機器證明：TLAPS、Apalache 與定理證明全景
- **目標**：能逐行讀懂一段真實 TLAPS 證明；能畫出「嚴謹度光譜」並為一個問題選擇合適的嚴謹度。
- **必涵蓋**：嚴謹度光譜：測試 → TLC（有限窮舉）→ Apalache（符號／SMT、歸納檢查）→ TLAPS（機器查證的證明）→ Lean/Rocq/Isabelle（深度數學）；TLAPS 證明語言精讀：層級結構（⟨1⟩⟨2⟩…正式回收全書手寫格式）、BY/DEF/SMT 後端、proof obligation 概念；精讀一段真實 TLAPS 證明（~20 行，來源照 landscape）；Apalache 原理（狀態轉移編成 SMT 約束；檢查歸納不變量的用法）；定理證明器全景各一段：Lean 4（mathlib、與 AI 的結合）、Rocq（CompCert）、Isabelle（seL4）——只講定位與代表作；決策框架：「工程師走多深才划算」。
- **不涵蓋**：任何安裝與操作；Lean/Rocq 語法教學；SMT 求解器內部（一句話）。
- **橋接**：proof obligation ≈ CI 的 required checks；「SMT 後端搞不定就拆步驟」≈ 把大 PR 拆小。
- **Worked example**：逐行解讀一段真實 TLAPS 證明，把每行對應回 ch14 手寫證明的哪個動作。
- **紙上推演**：把 ch14 的一段手寫證明改寫成 TLAPS 風格骨架（紙上）；判斷三個 proof obligations 哪個 SMT 容易／困難並說理由。

## Part VI — 實務與地圖（ch17–18）

### ch17 — 業界案例研究：誰在用、用在哪、值不值
- **目標**：能用真實案例回答「形式化方法在工業界到底是不是玩具」；能對自己的系統做 ROI 評估。
- **必涵蓋**：AWS（CACM 2015：哪些團隊、找到什麼 bug、原文措辭——細節嚴格照 landscape，不得憑記憶）；AWS 後續（P language、automated reasoning，照 landscape）；MongoDB「eXtreme Modelling in Practice」的誠實教訓（spec–code 同步是真痛點）；Azure Cosmos DB（Lamport 參與的說法以 landscape 查證為準）；CockroachDB parallel commits；模式歸納：值得形式化的問題長相（協議級、故障×併發交錯、錯誤代價高）；**spec 腐化**：spec 與 code 漂移的維運視角；成本誠實帳（學習曲線、誰來維護 spec）。
- **不涵蓋**：重講協議內容（指回 Part IV）；工具教學；未經 landscape 確認的案例（寧缺勿錯）。
- **橋接**：用讀者自己的結算 pipeline 當評估標的。
- **Worked example**：拿 ch17 的決策框架完整評估「讀者的結算 pipeline 值不值得寫 spec」——走完每個判準、給出有數字的結論。
- **紙上推演**：對三個假想系統（CRUD 後台、分散式鎖服務、計費對帳）做形式化 ROI 評估並排序。

### ch18 — 形式化方法地圖與下一步
- **目標**：把全書收進一張地圖；知道 TLA+ 之外有什麼、何時選誰；帶走「不寫 spec 也能用」的思維紅利。
- **必涵蓋**：全書地圖回收（ch01 的圖、現在每格都走過了）；工具光譜各一段（定位＋適用場景，不教語法）：Alloy（關係邏輯、small scope）、P（事件驅動、可執行測試）、Quint（TLA+ 語意的現代語法外衣）、Event-B（精化驅動）、SPIN/NuSMV 一句話；設計級 vs 程式碼級驗證（seL4、CompCert、Dafny 定位——不展開）；輕量形式化光譜：property-based testing、deterministic simulation testing（FoundationDB 路線）、design doc 裡寫 invariant 的習慣——**沒有工具也帶得走的紅利**；AI × 形式化方法（2025–26 動態，照 landscape、全部 hedge）；如果哪天想動手：從讀者現狀出發的路徑指引（明寫本書刻意不動手）。
- **不涵蓋**：每個工具的語法；安裝；對 AI 進展的預言式斷言。
- **橋接**：把 ch01 開場的那個 bug 拿回來：現在的你會怎麼處理。
- **Worked example**：同一個小問題（兩人轉帳）用 TLA+ 思維、Alloy 思維、PBT 思維各建模一次（紙上、各 ~15 行），對照三者抓什麼、漏什麼。
- **紙上推演**：為三個場景選方法並說理由；幫一份（虛構的）design doc 補上三條 invariant 描述。

## 附錄（在全部章節完成後編譯，從實際寫出的內容萃取）

### 附錄 A — 符號速查表
全書符號總表：Unicode、TLA+ ASCII、讀法、中文名、首次出現章。從各章實際用過的符號 grep 彙整，不得收錄書中沒出現的符號。

### 附錄 B — 術語表
EN–ZH–一句話定義–首次出現章。同樣從實際內容萃取。

### 附錄 C — 延伸閱讀總地圖
彙整各章延伸閱讀＋landscape 驗證過的資源（書、論文、spec 原文、課程），給出「如果只讀三樣」與「想動手時的第一步」的順序建議。只收 landscape 或各章已驗證的連結。

## 檔名規範

`chNN-slug.md`（例：`ch01-why-formal-methods.md`）、附錄 `appendix-a-symbols.md`、`appendix-b-glossary.md`、`appendix-c-reading-map.md`。
