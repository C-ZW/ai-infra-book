# ch14 — 歸納不變量：證明 safety 的技藝

> **本章解決什麼問題**：ch09 的 TLC 與 ch11 的手推都停在同一道牆前——有限參數下的窮舉再徹底，也只是 checked，不是 proved，而 THEOREM 主張的是任意參數、任意規模。本章把 ch05 的不變量規則升級成能對真協議承重的技藝：三個義務、一個強化迴圈、一套讀卡點的方法；然後打兩場硬仗——SettlementV1 的 `NoDoublePay` 與擴充版 TwoPhase 的 `TCConsistent`（全書證明高峰），兌現 ch08 與 ch11 各欠的那張支票。ch15 的 refinement 與 ch16 的機器證明都假設你走過這一章。

你現在站在全書地圖的這裡：

```text
┌────────────────────────────────────────────────────────────────────┐
│ Part I   為什麼需要形式化                                          │
│   ch01 測試的極限 · ch02 狀態機                                    │
├────────────────────────────────────────────────────────────────────┤
│ Part II  數學地基                                                  │
│   ch03 邏輯 · ch04 集合 · ch05 歸納                                │
├────────────────────────────────────────────────────────────────────┤
│ Part III TLA+ 與時序邏輯                                           │
│   ch06 動作邏輯 · ch07 時序邏輯 · ch08 完整 spec · ch09 TLC 原理   │
├────────────────────────────────────────────────────────────────────┤
│ Part IV  協議精讀                                                  │
│   ch10 互斥 · ch11 2PC · ch12 Paxos · ch13 Raft                    │
├────────────────────────────────────────────────────────────────────┤
│ Part V   證明                                          ← 你在這裡  │
│   ch14 歸納不變量 · ch15 Refinement · ch16 機器證明                │
├────────────────────────────────────────────────────────────────────┤
│ Part VI  實務                                                      │
│   ch17 業界案例 · ch18 方法地圖                                    │
└────────────────────────────────────────────────────────────────────┘
```

Part V 三章是這本書的登頂段。Part IV 你精讀了四個協議、手推了它們的狀態空間；從本章起，問題從「這組參數下對不對」變成「**為什麼永遠對**」。三章的分工：本章教你手寫 safety 的證明（歸納不變量），ch15 教你證「實作蘊涵規格」（refinement），ch16 讓機器替你查證每一步（TLAPS）。裝備你都有了——⟨1⟩ 層級格式（ch05）、動作邏輯（ch06）、兩份熟到能背的 spec（ch08、ch11）——本章只是把它們擰成一股繩。

## 從你已知的出發

你最熟練的工作迴圈其實不是寫程式，是修 bug：失敗的測試亮紅燈 → 讀 stack trace，找出第一個不對勁的狀態 → 推測根因、下修正 → 重跑。本章的主迴圈一模一樣，連節奏都一樣：歸納步證不過（紅燈）→ 把卡點具體化成一個「壞前驅」狀態（stack trace）→ 判斷它可不可達（真 bug 還是誤報）→ 強化述語或舉出反例（修正）→ 重證（重跑）。差別只有一個：debug 迴圈收斂時你得到一個不再紅的測試；強化迴圈收斂時你得到一個對所有規模、所有調度一次買斷的定理。

第二條經驗也直接搬得進來。當年排查重複入帳，你在表上加過 `credited_at`、加過 idempotency key——業務邏輯不需要這些欄位，**排查**需要：它們讓「現在的狀態」回答得了「歷史上發生過什麼」。本章管這招叫**輔助述語**：dedup 表是「這則訊息曾經入過帳」的狀態化身；TwoPhase 那個只增不減的 msgs（ch11）是「誰曾經說過什麼」的全量留底。ch05 留過一個觀察：狀態機只有眼前這一格的記憶，性質需要歷史撐腰時，就得把歷史編碼進狀態——本章兌現它。

第三條：你 review 一個 PR 從不重播 git log，你看 diff，心裡的問題是「**假設 main 是好的**，這個 diff 會不會弄壞它」。歸納步就是這句話的數學版：假設步前狀態滿足 Ind，驗證任何一步之後仍滿足。而本章的核心難題，也正是 code review 的核心難題——「main 是好的」到底是哪幾句話？寫得太弱，diff 審不下去；寫得太強，main 自己都不滿足。整章都在練怎麼把這幾句話寫對。

## 為什麼 TLC 不夠：checked ≠ proved

TwoPhase.tla 檔尾那段註解（ch11 照引過）的措辭值得再讀一次：兩條定理「**checked** with TLC for six RMs」。Lamport 沒有寫 proved，因為它就不是。TLC 式窮舉（原理見 ch09）撞牆的位置有三個：

1. **參數是寫死的。**TLC 一次只能代入一組 CONSTANTS；`THEOREM TPSpec ⇒ □TCConsistent` 主張的卻是**任意** RM 集合。2 個 RM 的 56 個可達狀態全綠、6 個 RM 的 50,816 個全綠，對「第 7 個 RM 會不會出事」在邏輯上一個字都沒說。small scope hypothesis（ch09）是個勝率很高的賭注，但賭注不是定理。
2. **狀態空間可能根本無限。**ch05 的 ping-pong 機 p, q ∈ ℕ，窮舉免談。更陰的是 v1：ledger ∈ [Msgs → Nat]，**型別空間無限**，可達空間有限——但「可達空間有限」這件事本身是 dedup 守出來的秩序（ch08 原話），是一條待證的定理。用「先窮舉看看」去確認「可不可以窮舉」，邏輯上是繞圈。
3. **就算有限，也是指數。**56 到 50,816 只隔了四個 RM（ch11）。窮舉的成本曲線你在 ch09 算過，不再重算。

歸納證明為什麼能一次買斷？ch05 講過的那句話是全部的答案：**案例分析按動作分、不按參數分**。動作就那幾個，訊息三十萬則也是那幾個 case。

不過先別把 TLC 掃進垃圾桶——它在證明工作流裡換了個工位繼續上班。Lamport 有一份兩頁的技巧筆記（2018，見延伸閱讀）：把 spec 的 Init **換成你的候選 Ind**，讓 TLC 從「所有滿足 Ind 的狀態」出發走一步，看會不會走出 Ind——這恰恰是歸納步的機械化快篩，卡點（壞前驅）由機器替你找。代價是得先把無限值域砍成有限（例如 Nat 砍成 0..2），又一次付「有限化」的稅。Apalache 則把同樣的兩個義務編成 SMT 查詢，連砍值域都省了（`--init=IndInv --inv=IndInv --length=1` 的兩段式檢查，2026-06；原理見 ch16）。分工從此清楚：**機器找反例，人讀反例、寫條款、簽下任意規模的定理。**

## 三個義務與一個迴圈

把 ch05 的不變量規則穿上 TLA 的衣服。要證狀態述語 S 是 `Spec ≜ Init ∧ □[Next]_vars` 的 invariant，標準路線是找一個述語 Ind，完成三個義務：

1. **起點**：Init ⇒ Ind——所有初始狀態滿足 Ind。
2. **封閉**：Ind ∧ [Next]_vars ⇒ Ind′——從任何滿足 Ind 的狀態走任何一步，仍滿足 Ind。
3. **蘊涵**：Ind ⇒ S。

義務一、二合起來（ch05 的歸納）給出 Spec ⇒ □Ind；義務三收尾得 Spec ⇒ □S。滿足前兩個義務的 Ind 就叫 **inductive invariant**。這三條跟 Lamport 自己教學筆記裡列的三個條件一字同形（出處見延伸閱讀），不是巧合——這就是這門手藝的全部公理。

義務二有個小字條款先講清楚：它面對的是 [Next]_vars，比 Next 多一個 stuttering 析取。但 stuttering 步免費——vars′ = vars 時，Ind′ 跟 Ind 是同一句話（狀態述語的真值只由變數值決定）。所以接下來所有證明都只列真動作，這行豁免引用一次、全章有效。

困難全部集中在一件事上。Lamport 在同一份筆記裡的話，翻譯過來是：「如果 S 恰好自己就 inductive，讓 Ind 等於 S 就好，義務三免費——**但對我們在乎的那些 invariant，這種情況很少見**。」為什麼很少見，ch05 那張圈圈圖你應該還記得：S 為真只說可達狀態都落在 S 圈內，但 S 圈裡住著幽靈——不可達、卻滿足 S 的狀態——而歸納步分不出誰可達，會在幽靈身上一步跨出圈外。卡死。

卡死之後的流程，ch05 立過口訣：**證、卡、讀卡點、判可達、強化或舉反例**。本章把第三步「讀卡點」展開成可以照做的三問：

1. 卡住的那條義務，**缺哪句話**才推得過去？（把缺口寫成述語，精確到變數。）
2. 這句話在真實執行裡**為什麼為真**？（答案通常是某個動作的 guard、某種單調性、某條守恆。）
3. 把那個理由寫成狀態述語，疊進 Ind，**回到第一步重證**——包括新條款自己的八方義務。

最後一句是強化的價格表：**每加一條條款，每個動作都多一份義務**。n 個動作、k 條條款，封閉義務就是一張 n × k 的矩陣，一格都不能漏。條款不是越多越安全，是越多越貴——所以定稿前還有最後一道工序：審計每條條款被誰用到，沒人用的刪掉（刪完要重驗）。這些話現在聽起來抽象，兩場硬仗打完就是肌肉記憶。

## 找 Ind 的啟發法：工具箱先擺桌上

Lamport 的誠實警告（同一份 2018 筆記）：找 inductive invariant，沒做過很多次的人覺得難；做過很多次，要一次寫對還是難。所以這裡不賣銀彈，只擺四件工具，兩場證明會輪流用到它們：

| 啟發法 | 一句話 | 本書的先例 |
|---|---|---|
| 從 TypeOK 出發 | TypeOK 幾乎總是 Ind 的第一個合取項：沒有它，連「加一還是數字」「那格還在值域裡」都說不出口；而它通常自己就 inductive，是免費的地基 | ch08（TypeOK 的四層理由） |
| 從卡點學 | 不要憑空想條款——讓失敗的歸納步告訴你缺什麼。卡點是資訊，不是挫折 | ch05 的 ping-pong；本章全程 |
| 找守恆量 | 「什麼東西不會憑空增減」往往一句話圈死大片幽靈：訊息的存量、票的總數、錢的進出 | ch05 的 copies(m)；ch08 題 2 的 free + held = N |
| 把歷史編碼進狀態 | 性質需要「曾經發生過」時，去找狀態裡的史官：dedup 表、只增不減的 msgs、單調的 tmState。沒有史官就請一個（加輔助變數——那是 ch15 的 auxiliary variables 的近親） | dedup（ch08）；msgs（ch11） |

工具備齊，開戰。

## 完整證明（一）：SettlementV1 的 NoDoublePay

對象是 ch08 的 SettlementV1，名字與型別原樣搬來：變數 queue ⊆ Msgs、working ∈ [Consumers → Msgs ∪ {"idle"}]、ledger ∈ [Msgs → Nat]、dedup ⊆ Msgs；動作 Fetch(c, m)、Credit(c)、Ack(c)、Crash(c)；目標：

NoDoublePay ≜ ∀ m ∈ Msgs : ledger[m] ≤ 1

ch08 立了兩張字據：`THEOREM Spec => []TypeOK` 與 `THEOREM Spec => []NoDoublePay`。現在來兌現。

### 第一輪：直接拿 NoDoublePay 上，讓它卡

候選 Ind ≜ TypeOK ∧ NoDoublePay。四個動作裡只有 Credit 動 ledger，直奔它。設步前成立，Credit(c) 的 guard 給 working[c] ≠ "idle" 且 working[c] ∉ dedup；令 m₀ ≜ working[c]，步後 ledger′[m₀] 是 ledger[m₀] + 1。要驗 ledger′[m₀] ≤ 1，等於要步前 ledger[m₀] = 0。歸納假設只給 ledger[m₀] ≤ 1——**容許 1**。卡。

照流程，把卡點具體化成壞前驅（ch05 叫它壞前狀態，同物異名）：

s_x ≜ ⟨queue = {m2}, working = (c1 ↦ m1, c2 ↦ "idle"), ledger = (m1 ↦ 1, m2 ↦ 0), dedup = {}⟩

驗收：s_x 滿足 TypeOK（逐項在值域內）與 NoDoublePay（1 ≤ 1、0 ≤ 1）；Credit(c1) 的兩個 guard 都亮（c1 手上有 m1，m1 ∉ dedup）；走一步，ledger[m1] = 2。貨真價實的壞前驅。

判可達。先招認一個誘惑：ch05 證 v0 時你練出來的肌肉是守恆——copies(m) ≤ 1。它在 v1 仍然為真（值得你自己驗一次），但先別急著抄舊答案，**回去讀卡點**。卡住的義務是「步前 ledger[m₀] = 0」，這句話裡只有 ledger 和（經由 guard 出場的）dedup——queue 與 working 根本沒戲份。守恆也解釋不了 s_x 為什麼不可達：s_x 裡每則訊息的存量完全合法（m1 一份在 c1 手上，m2 一份在佇列）。s_x 的病不在存量，在**帳目**：ledger 說 m1 入過帳，dedup 卻不記得。而 v1 的設計恰恰保證這不可能——Credit 在同一步裡入帳＋寫 dedup（ch08 全 spec 最承重的假設），且 dedup 只進不出。把這個理由寫成述語：

DedupCovers ≜ ∀ m ∈ Msgs : m ∉ dedup ⇒ ledger[m] = 0

逆否讀法更順口：**入過帳的訊息必在 dedup 裡**——dedup 是 ledger 的影子收據。強化後的候選：

IndV1 ≜ TypeOK ∧ NoDoublePay ∧ DedupCovers

### 第二輪：完整證明

**定理**：SettlementV1 滿足 Spec ⇒ □TypeOK 與 Spec ⇒ □NoDoublePay（對任意非空的 Msgs 與 Consumers）。

⟨1⟩1. 起點：Init ⇒ IndV1。
  TypeOK：queue = Msgs ⊆ Msgs；working 把每個 c 映到 "idle"，落在 [Consumers → Msgs ∪ {"idle"}]；ledger 全 0 ∈ Nat；dedup = {} ⊆ Msgs。
  NoDoublePay：每格 0 ≤ 1。
  DedupCovers：後件 ledger[m] = 0 直接為真——這條在起點不是空洞通過，是貨真價實地成立。
⟨1⟩2. 封閉：設步前滿足 IndV1。Next 是 ∃ c ∈ Consumers（Fetch 再 ∃ m ∈ Msgs）套四類動作的析取——任取見證 c 與 m，逐動作討論；stuttering 步由本章開頭的豁免條款處理。
  ⟨2⟩1. 情況 Fetch(c, m)（guard：working[c] = "idle"、m ∈ queue）。本步動 queue、working；ledger、dedup 未動。
    ⟨3⟩1. TypeOK′：queue′ = queue ∖ {m} ⊆ Msgs；working′ 只把 c 那格改成 m，而 m ∈ queue ⊆ Msgs（步前 TypeOK），仍在值域；ledger、dedup 照舊。
    ⟨3⟩2. NoDoublePay′ ∧ DedupCovers′：兩條只談 ledger 與 dedup，本步未動，照搬歸納假設。
    ⟨3⟩3. Q.E.D.
  ⟨2⟩2. 情況 Credit(c)（guard：working[c] ≠ "idle"、working[c] ∉ dedup）。令 m₀ ≜ working[c]。本步動 ledger、dedup；queue、working 未動。
    ⟨3⟩1. m₀ ∈ Msgs。理由：TypeOK 給 working[c] ∈ Msgs ∪ {"idle"}，guard 排除 "idle"。
    ⟨3⟩2. 步前 ledger[m₀] = 0。理由：guard 給 m₀ ∉ dedup，DedupCovers 在 m₀ 上的實例。——第一輪卡死的位置就是這裡；強化條款進了歸納假設，債有人還了。
    ⟨3⟩3. ledger′[m₀] = 1 ≤ 1。理由：EXCEPT 把 m₀ 那格改成舊值加一，由 ⟨3⟩2 是 0 + 1。
    ⟨3⟩4. DedupCovers′ 對 m₀：m₀ ∈ dedup′ = dedup ∪ {m₀}，前件為假。
    ⟨3⟩5. 對每個 m̃ ≠ m₀：ledger′[m̃] = ledger[m̃]（EXCEPT 只動一格）；若 m̃ ∉ dedup′ 則 m̃ ∉ dedup（集合只變大），由歸納假設 ledger[m̃] = 0；ledger[m̃] ≤ 1 照搬。
    ⟨3⟩6. TypeOK′：ledger′[m₀] = 1 ∈ Nat；dedup′ = dedup ∪ {m₀} ⊆ Msgs（⟨3⟩1）；queue、working 未動。
    ⟨3⟩7. Q.E.D.
  ⟨2⟩3. 情況 Ack(c)（guard：working[c] ≠ "idle"、working[c] ∈ dedup）。只動 working：c 那格變回 "idle"，仍在值域，TypeOK′ 成立；ledger、dedup 未動，另兩條照搬。Q.E.D.
  ⟨2⟩4. 情況 Crash(c)（guard：working[c] ≠ "idle"）。動 queue 與 working：queue′ = queue ∪ {working[c]} ⊆ Msgs（working[c] ∈ Msgs，同 ⟨2⟩2 的 ⟨3⟩1），working′ 把 c 變回 "idle"；TypeOK′ 成立。ledger、dedup 未動，另兩條照搬。Q.E.D.
  ⟨2⟩5. Q.E.D. 四類動作蓋住所有真步。
⟨1⟩3. 蘊涵：IndV1 ⇒ NoDoublePay。第二個合取項就是它；IndV1 ⇒ TypeOK 同理。
⟨1⟩4. Q.E.D. 由 ch05 的不變量規則。∎

### 這份證明在說什麼

**Crash 與 redelivery 是免費的 case。**整個 v1 的戲劇性——crash 在入帳與確認之間插刀、訊息帶著舊身世回佇列（ch08 的六步危險路徑）——在證明裡只值兩行「ledger、dedup 未動，照搬」。這不是證明偷懶，是防線位置的精確刻畫：**`NoDoublePay` 的承重牆只有兩塊磚——dedup 只進不出，加上 Credit 拿它當門票**。ch08 預告過的那句話現在是定理級的：把「活著的 consumer 處理太慢、visibility timeout 重投遞」加回模型（同一訊息兩個 consumer 同持，copies = 2），Fetch 與 Crash 的 case 要改寫，但 ⟨2⟩2 的核心三步——guard 給 ∉ dedup、DedupCovers 給 = 0、加一得 1——一字不動。

**規模無關。**證明裡的量詞全是 ∀ m、∀ c，沒有任何一步用到「兩則訊息、兩個 consumer」。每季三十萬筆、兩百個 consumer，同一份證明。這就是 THEOREM 字據的真正兌現——TLC 給不了的那種。

**強化不必到位，夠用就停。**你可能注意到 DedupCovers 只寫了單向。雙向版本（m ∈ dedup ⟺ ledger[m] = 1）也是 inductive、把可達集合圈得更緊，但多出來的方向整份證明一次都用不到，而它照樣要在四個動作上繳維護稅。紙上推演題 1 讓你親手驗那一半，體會「inductive 但無用」是什麼觸感。

**證明的前提要抄錄在結論旁。**這份定理站在兩個 spec 假設上：Credit 的原子性（dedup 檢查＋寫入＋入帳同一筆交易）、dedup 永不清理。你的實作哪天改成「先 SELECT 再 INSERT」或給 dedup 上了 TTL，定理對你的系統即刻失效——ch08 的抽象帳，每次引用定理都該重讀一遍。

## 完整證明（二）：TwoPhase 的 TCConsistent

全書高峰。對象是 ch11 的擴充版 TwoPhase：原版七個動作加 TMCrash，TPCrashNext ≜ TPNext ∨ TMCrash，TPCrashSpec 照 ch11 的定義；TPTypeOK 的 tmState 值域補上 "crashed"：

```tla
TPTypeOK ==
  /\ rmState \in [RM -> {"working", "prepared", "committed", "aborted"}]
  /\ tmState \in {"init", "committed", "aborted", "crashed"}
  /\ tmPrepared \subseteq RM
  /\ msgs \subseteq Message
```

縮寫沿 ch11：P(r) ≜ [type ↦ "Prepared", rm ↦ r]，C ≜ [type ↦ "Commit"]，A ≜ [type ↦ "Abort"]。目標：

TCConsistent ≜ ∀ r1, r2 ∈ RM : ¬(rmState[r1] = "aborted" ∧ rmState[r2] = "committed")

先聲明賭注：證的是擴充版 TPCrashSpec ⇒ □TCConsistent。原版 TPSpec 的行為集合是擴充版的子集合（Next 少一個析取，允許的行為只少不多），所以定理對原版**免費成立**——ch11 檔尾那句「真正的證明欠著，ch14 還」，連本帶利一次結清。

### 第〇輪：拿 TCConsistent 直接上

候選 TPTypeOK ∧ TCConsistent。八個動作裡動 rmState 的有四個。RMPrepare 無害：working 變 prepared，既不製造 "committed" 也不製造 "aborted"，步前沒有違規配對、步後也不會有（ch11 題 1 解答的同款論證）。剩下三個全卡：

- **RMChooseToAbort(r)**：步後 r 變 "aborted"。若步前某個 r̃ 是 "committed"——歸納假設管不住：TCConsistent 只禁止「同時出現」，步前根本沒有 aborted。壞前驅正是 ch11 紙上推演題 2 的那位老朋友：s_bad ≜ ⟨rmState = (r1 ↦ "committed", r2 ↦ "working"), tmState = "init", tmPrepared = {}, msgs = {}⟩。它滿足 TPTypeOK 與 TCConsistent，RMChooseToAbort(r2) 一步打穿。
- **RMRcvCommitMsg(r)**：步後 r 變 "committed"，步前若有人 "aborted"，同型穿孔。
- **RMRcvAbortMsg(r)**：對稱。

s_bad 可達嗎？不可達——ch11 題 2 的 (d) 已經把理由寫成一條鏈。現在把那條鏈攤開，每一節標上它將要成為的條款編號（編號照本章定稿，方便對照）：

```text
rmState[r̃] = "committed"
   │ I1：committed 要有依據——RM 只因收到 Commit 而 commit
   ▼
C ∈ msgs
   │ I2：Commit 只有一個寄件人——TMCommit
   ▼
tmState = "committed"
   │ B：TMCommit 的 guard——小本子集滿才放行
   ▼
tmPrepared = RM
   │ I4：小本子不說謊——收過誰的信才記誰
   ▼
∀ r̃ ∈ RM : P(r̃) ∈ msgs
   │ I5：說出口的 prepared 收不回——發過信的人回不去 "working"
   ▼
沒有任何 RM 還在 "working"
```

注意鏈條的每一節都是一條**狀態述語形的蘊涵**，而其中 B 原本不是述語——它是 TMCommit 的 guard，一個「當時」的事實。歸納證明只看眼前一格，「當時」要靠狀態記住，所以 B 得升格成條款：B ≜ tmState = "committed" ⇒ tmPrepared = RM。msgs 與 tmState 在這裡就是史官：訊息只增不減、tmState 一旦離開 "init" 就不回頭，歷史因此可以從現在讀出來——這正是「把歷史編碼進狀態」這件工具的實戰長相。

### 第一輪：鏈條版，收一案、又卡兩案

候選：TPTypeOK ∧ TCConsistent ∧ I1 ∧ I2 ∧ B ∧ I4 ∧ I5。重證 RMChooseToAbort(r)：設步前有人 "committed"，沿鏈走——I1 給 C ∈ msgs，I2 給 tmState = "committed"，B 給 tmPrepared = RM，於是 r ∈ tmPrepared，I4 給 P(r) ∈ msgs，I5 給 rmState[r] ≠ "working"——與 guard 的 "working" 矛盾。所以步前無人 committed，步後自然沒有違規配對。**收案。**

但 RMRcvCommitMsg 還卡著。新的壞前驅：

s_bad2 ≜ ⟨rmState = (r1 ↦ "aborted", r2 ↦ "prepared"), tmState = "committed", tmPrepared = {r1, r2}, msgs = {P(r1), P(r2), C}⟩

逐條款驗它合格：TCConsistent（aborted 配 prepared，無違規）✓；I1（無人 committed，空洞）✓；I2（C 在場、tmState 確是 "committed"）✓；B（tmPrepared = RM）✓；I4（兩封 P 都在）✓；I5（aborted 與 prepared 都不是 working）✓。然後 RMRcvCommitMsg(r2) 的 guard C ∈ msgs 亮著，走一步——(aborted, committed)，目標陣亡。對稱地，RMRcvAbortMsg 也有同型卡點（committed 的人在場、A 也在場）。

判可達：s_bad2 不可達。理由口述出來是——TM 都 commit 了，r1 怎麼可能是 aborted？自發 abort 需要 "working"（I5 說發過信的人回不去）；被通知 abort 需要 A 在場，而 A 的唯一寄件人 TMAbort 與 TMCommit 互斥——TM 只有一次離開 "init" 的機會。讀出缺的句子：**Commit 在場的世界容不下 aborted**。最划算的條款寫法，是把 TCommit 的 canCommit 整句搬進來：

I7 ≜ C ∈ msgs ⇒ ∀ r ∈ RM : rmState[r] ∈ {"prepared", "committed"}

眼熟嗎？這正是 ch11 兩層對照表底下欠的那句話——「Commit 訊息在 msgs 裡時，全員必在 {"prepared", "committed"}」。當時說這串鏈條「正是 ch14 要逐節鍛造的強化不變量」，現在它有了條款編號。

I7 不是白拿的，它自己要過八個動作的歸納步，其中 TMCommit 那格逼出兩條新債：要在「TM 即將 commit」的時刻排除 aborted，需要知道 aborted 的人是怎麼 abort 的（I6 ≜ rmState[r] = "aborted" ⇒ A ∈ msgs ∨ P(r) ∉ msgs——abort 的兩種身世：被通知，或從沒準備過），以及 A 在場意味著什麼（I3 ≜ A ∈ msgs ⇒ tmState = "aborted"）。至於 RMRcvAbortMsg 的卡點讀出的那句「C 與 A 不可能同時在場」——它**不必當條款**：有了 I2 與 I3，C ∧ A 同時在場會逼 tmState 同時等於兩個值，矛盾自動奉上。有些事實當推論比當條款便宜，因為條款要繳八個動作的維護稅，推論不用。

### 定稿與審計

第二輪收齊後做條款審計，刪掉兩個白吃飯的：**B 用不到了**——I7 把 RM 端三個案子的推理全部短路（C 在場 ⇒ 全員就位，一步斃命），B 原本服務的那條長鏈只剩 TMCommit 的歸納步還需要，而那裡用的是 guard 本人，不是條款。**TCConsistent 自己也退役了**——它成了 I1 ∧ I7 的推論（馬上會證），目標性質從合取項裡畢業，這是強化迴圈收斂時常見的好結局。定稿：

```tla
IndTP == /\ TPTypeOK
         /\ \A r \in RM :
              rmState[r] = "committed" => [type |-> "Commit"] \in msgs
         /\ [type |-> "Commit"] \in msgs => tmState = "committed"
         /\ [type |-> "Abort"]  \in msgs => tmState = "aborted"
         /\ \A r \in RM :
              r \in tmPrepared => [type |-> "Prepared", rm |-> r] \in msgs
         /\ \A r \in RM :
              [type |-> "Prepared", rm |-> r] \in msgs => rmState[r] # "working"
         /\ \A r \in RM :
              rmState[r] = "aborted" => \/ [type |-> "Abort"] \in msgs
                                        \/ [type |-> "Prepared", rm |-> r] \notin msgs
         /\ [type |-> "Commit"] \in msgs =>
              \A r \in RM : rmState[r] \in {"prepared", "committed"}
```

七條條款的角色卡（依出場順序 T、I1…I7）：

| 條款 | 白話 | 主要在哪些歸納步當主力 |
|---|---|---|
| T（TPTypeOK） | 值域地基 | 處處墊底 |
| I1 | committed 要有依據：有人 commit ⇒ C 在場 | 蘊涵步；TMAbort |
| I2 | C 的寄件人只能是已 commit 的 TM | RMRcvAbortMsg；TMAbort、TMCrash |
| I3 | A 的寄件人只能是已 abort 的 TM | TMCommit（排除 aborted）；RMRcvAbortMsg |
| I4 | 小本子不說謊：記了誰就收過誰的信 | TMCommit |
| I5 | 發過 Prepared 的人回不去 "working" | TMCommit；RMChooseToAbort |
| I6 | aborted 的兩種身世：被通知，或從沒準備過 | TMCommit |
| I7 | C 在場 ⇒ 全員就位（canCommit 的條款化） | RM 端全部四個動作；蘊涵步 |

### 完整證明

**定理**：TPCrashSpec ⇒ □TCConsistent（任意有限非空 RM 集合）。

先立三條速記，給接下來 8 × 8 = 64 份義務裡的多數一行帳：

- **速記一（未動照搬）**：某條款引用的變數本步全未變，其真值不可能變，照搬歸納假設。
- **速記二（msgs 單調）**：每個動作至多往 msgs 加一封信、從不刪。所以「x ∈ msgs」形的**後件**不會因走步而由真變假；「x ∈ msgs」形的**前件**只在「本步加的恰是 x」時才可能由假轉真，「x ∉ msgs」形的析取只在同一情況下才可能由真變假。
- **速記三（單格修改）**：動 rmState 的動作只改 r 那一格；∀ r̃ 形條款對 r̃ ≠ r 照搬，只需驗 r̃ = r 那格。

封閉義務的總帳——動作 × 條款矩陣（◯ ＝ 一行帳：憑速記、guard 或效果直接結案，正文至多點名一句；● ＝ 需要動用歸納假設或多步推理，正文有編號步驟）：

| 動作＼條款 | T | I1 | I2 | I3 | I4 | I5 | I6 | I7 |
|---|---|---|---|---|---|---|---|---|
| RMPrepare(r) | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ● |
| RMChooseToAbort(r) | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ● | ● |
| RMRcvCommitMsg(r) | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ● |
| RMRcvAbortMsg(r) | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ● |
| TMRcvPrepared(r) | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ | ◯ |
| TMCommit | ◯ | ◯ | ◯ | ● | ◯ | ◯ | ◯ | ● |
| TMAbort | ◯ | ● | ● | ◯ | ◯ | ◯ | ◯ | ● |
| TMCrash | ◯ | ◯ | ● | ● | ◯ | ◯ | ◯ | ◯ |

六十四格、十二格戲肉，而且半數擠在 I7 那一欄——封閉證明的劇本永遠是這樣：最強的條款打工最多。開證。

⟨1⟩1. 起點：TPInit ⇒ IndTP。
  T：rmState 全 "working"、tmState = "init"、tmPrepared = {}、msgs = {} 逐項在值域內。
  其餘七條的前件逐一驗假：msgs = {} 殺死 I2、I3、I5、I7 的前件；tmPrepared = {} 殺死 I4 的；rmState 全 "working" 殺死 I1（無人 committed）與 I6（無人 aborted）的。七條全靠空洞成立。
  這種空洞合法——義務一只問初始世界，而初始世界乾淨。警鈴要留給另一種空洞：前件在**所有可達世界**都假（見下一節）。這裡不是：worked 過的 trace 裡（ch11 的 s₀…s₅）每條前件都真實亮起過。
⟨1⟩2. 封閉：設步前滿足 IndTP，TPCrashNext 拆掉 ∃ rm 量詞後分八類動作。
  ⟨2⟩1. 情況 RMPrepare(r)（guard：rmState[r] = "working"；效果：r ↦ "prepared"、msgs 加 P(r)）。
    ⟨3⟩1. I7′：若 C ∈ msgs，I7 給 rmState[r] ∈ {"prepared", "committed"}，與 guard 的 "working" 矛盾，故 C ∉ msgs；本步加的是 P(r) ≠ C，故 C ∉ msgs′，I7′ 空洞成立。（弦外之音：Commit 已在場的世界裡，RMPrepare 根本不該 enabled——條款在替協議看門。）
    ⟨3⟩2. 對 r 自己：I1′ 前件假（prepared 不是 committed）；I5′ 後件直接真（prepared ≠ working）；I6′ 前件假。
    ⟨3⟩3. 其餘：I2′、I3′（加的不是 C／A，前件不變，tmState 未動）；I4′（速記二，後件單調）；I1′、I5′、I6′ 對 r̃ ≠ r（速記三；I6 的 P(r̃) ∉ msgs 析取由速記二保住——加的是 P(r) 不是 P(r̃)）；T′ 直接。
    ⟨3⟩4. Q.E.D.
  ⟨2⟩2. 情況 RMChooseToAbort(r)（guard："working"；效果：r ↦ "aborted"）。
    ⟨3⟩1. P(r) ∉ msgs。理由：I5 的逆否——若 P(r) ∈ msgs 則 rmState[r] ≠ "working"，與 guard 矛盾。
    ⟨3⟩2. I6′ 對 r：第二個析取成立——P(r) ∉ msgs′ = msgs，由 ⟨3⟩1（msgs 本步未動）。
    ⟨3⟩3. I7′：同 ⟨2⟩1 ⟨3⟩1——C ∈ msgs 與 guard 的 "working" 不相容，故 C ∉ msgs = msgs′，空洞成立。
    ⟨3⟩4. 對 r 自己：I1′ 前件假（aborted 不是 committed）；I5′ 後件真（aborted ≠ working）。其餘照三條速記。T′ 直接。
    ⟨3⟩5. Q.E.D.（第〇輪在這個動作上卡死；定稿後 TCConsistent 甚至不必出場——「有人 committed 而我還能自發 abort」的世界被 I7 整個排除了。）
  ⟨2⟩3. 情況 RMRcvCommitMsg(r)（guard：C ∈ msgs；效果：r ↦ "committed"）。
    ⟨3⟩1. I7′：前件 C ∈ msgs′ 為真。步前 I7（前件由 guard 為真）給全員 ∈ {"prepared", "committed"}；本步只把 r 改成 "committed"，仍在 {"prepared", "committed"} 內。成立。
    ⟨3⟩2. 對 r 自己：I1′ 後件真（guard 給 C ∈ msgs，而 msgs 本步未動）；I5′ 後件真；I6′ 前件假（committed 不是 aborted）。
    ⟨3⟩3. 其餘照三條速記；T′ 直接。Q.E.D.（順帶：⟨3⟩1 說明步前 rmState[r] 已在 {"prepared", "committed"}——對已 committed 的 RM 重複投遞 Commit 是冪等的；ch11 引的原文註解「第二次收到同一訊息無效」在這裡有了證明級版本。）
  ⟨2⟩4. 情況 RMRcvAbortMsg(r)（guard：A ∈ msgs；效果：r ↦ "aborted"）。
    ⟨3⟩1. C ∉ msgs。理由：若 C ∈ msgs，I2 給 tmState = "committed"；guard 的 A ∈ msgs 配 I3 給 tmState = "aborted"——一個變數兩個值，矛盾。（「C 與 A 不可能同時在場」：不是條款，是 I2 ∧ I3 的推論。）
    ⟨3⟩2. I7′：由 ⟨3⟩1，C ∉ msgs′ = msgs，前件假，空洞成立。
    ⟨3⟩3. 對 r 自己：I6′ 第一析取真（A ∈ msgs′，guard）；I1′ 前件假；I5′ 後件真。
    ⟨3⟩4. 其餘照三條速記；T′ 直接。Q.E.D.
  ⟨2⟩5. 情況 TMRcvPrepared(r)（guard：tmState = "init"、P(r) ∈ msgs；效果：tmPrepared 加 r）。
    引用 tmPrepared 的條款只有 I4：對 r，後件 P(r) ∈ msgs 由 guard 為真；對 r̃ ≠ r 照搬（速記三的 tmPrepared 版）。其餘七條的變數本步全未動（速記一）。Q.E.D.
  ⟨2⟩6. 情況 TMCommit（guard：tmState = "init"、tmPrepared = RM；效果：tmState ↦ "committed"、msgs 加 C）。高峰的那一格。
    ⟨3⟩1. I2′：前件 C ∈ msgs′ 真，後件 tmState′ = "committed" 真。
    ⟨3⟩2. A ∉ msgs′。理由：若 A ∈ msgs，I3 給 tmState = "aborted"，與 guard 的 "init" 矛盾；本步加的是 C。於是 I3′ 前件假，空洞成立。
    ⟨3⟩3. I7′：前件真，需全員 ∈ {"prepared", "committed"}（rmState 本步未動）。任取 r̃ ∈ RM：
      ⟨4⟩1. r̃ ∈ tmPrepared。理由：guard tmPrepared = RM。
      ⟨4⟩2. P(r̃) ∈ msgs。理由：I4 套在 ⟨4⟩1。
      ⟨4⟩3. rmState[r̃] ≠ "working"。理由：I5 套在 ⟨4⟩2。
      ⟨4⟩4. rmState[r̃] ≠ "aborted"。理由：反設 aborted，I6 給 A ∈ msgs ∨ P(r̃) ∉ msgs；右析取與 ⟨4⟩2 矛盾，左析取與 ⟨3⟩2 的推導（A ∉ msgs）矛盾。
      ⟨4⟩5. Q.E.D. T 給四值，排掉兩個，剩 {"prepared", "committed"}。
    ⟨3⟩4. 其餘：I1′ 後件恆真（C ∈ msgs′）；I4′ 速記二；I5′、I6′（加的是 C，P 訊息與 A 訊息的有無不變，rmState 未動）；T′ 直接。
    ⟨3⟩5. Q.E.D.
    把 ⟨3⟩3 讀慢一點：ch11 末尾那串鏈條沒有消失，它整條搬進了這一步——guard 是橋，I4、I5、I6、I3 是四節車廂。協議在 guard 裡寫下的每個字，終究會在某個歸納步裡變成你的彈藥；反過來說，**guard 上省掉的每個字，都會在某個歸納步上變成你的卡點**。
  ⟨2⟩7. 情況 TMAbort（guard：tmState = "init"；效果：tmState ↦ "aborted"、msgs 加 A）。
    ⟨3⟩1. I3′：前後件直接真。I6′：第一析取 A ∈ msgs′ 恆真，整條直接成立。
    ⟨3⟩2. C ∉ msgs′。理由：若 C ∈ msgs，I2 給 tmState = "committed"，與 guard 的 "init" 矛盾；本步加的是 A。於是 I2′ 與 I7′ 前件假，空洞成立。
    ⟨3⟩3. I1′：由 ⟨3⟩2 與 I1 的逆否，步前無人 "committed"；rmState 未動，前件依然假。
    ⟨3⟩4. 其餘照速記（I4 後件單調；I5 前件不變）；T′ 直接。Q.E.D.
  ⟨2⟩8. 情況 TMCrash（guard：tmState = "init"；效果：tmState ↦ "crashed"，其餘全未動）。
    ⟨3⟩1. 引用 tmState 的條款只有 I2、I3（與 T）。兩條同型處理：前件成立會分別逼出 tmState = "committed"／"aborted"，皆與 guard 的 "init" 矛盾——故 C ∉ msgs 且 A ∉ msgs，而 msgs 未動，兩條在步後空洞成立。T′："crashed" 在擴充值域內。
    ⟨3⟩2. 其餘五條（I1、I4、I5、I6、I7）引用的變數本步一個都沒動，速記一照搬。
    ⟨3⟩3. Q.E.D.
    ch11 開的支票在此兌現：TMCrash 的 case 確實平凡——但精確的理由比「它不動 rmState」多一層：IndTP 裡有兩條談 tmState 的條款，殺死它們前件的是 crash 自己的 guard「只有還活在 "init" 的 TM 才能倒」。把 crash 放寬成任何狀態都能倒，這兩條就真的會破——紙上推演題 3 帶你修那個模型。
  ⟨2⟩9. Q.E.D. 八類動作蓋住 TPCrashNext 的所有真步。
⟨1⟩3. 蘊涵：IndTP ⇒ TCConsistent。反設某狀態滿足 IndTP 且 rmState[r1] = "aborted"、rmState[r2] = "committed"。I1 套 r2 給 C ∈ msgs；I7 給 rmState[r1] ∈ {"prepared", "committed"}，與 "aborted" 矛盾。∎
⟨1⟩4. Q.E.D. 由不變量規則，TPCrashSpec ⇒ □IndTP；配 ⟨1⟩3 得 TPCrashSpec ⇒ □TCConsistent；原版 TPSpec 的行為是子集合，一併成立。∎

### 高峰回望

**買到的東西。**2 個 RM 的 72 個可達狀態、6 個 RM 的五萬個、一千個 RM 的天文數字——一次買斷。Lamport 寫的 checked，從這一頁起，在我們的模型上是 proved。

**s_bad 死在哪一條。**回頭驗收：ch11 的 s_bad（committed 配 working、msgs 空）被 I1 在第一節就擋下——r1 committed 卻沒有 C。ch11 題 2 (d) 的預言「s_bad 在第一節就斷裂」，現在是定稿條款的一次點名。

**I7 是 ch15 的預付款。**ch11 的兩層對照表裡，「RMRcvCommitMsg 對映到 Decide 的 commit 分支」欠的正是 canCommit 在那一刻成立——也就是 I7。ch15 把對照表升格成 refinement mapping 時，IndTP 就是你帶進場的彈藥庫：refinement 的逐步驗證幾乎總是「在 inductive invariant 的保護下」進行的。

**七條沒有一條是靈感。**I1、I2、B（後來退役）來自第一個卡點，I7 來自第二個，I3、I6 是 I7 自己的歸納步逼出來的，I4、I5 是鏈條的零件。技藝的全部內容是紀律：卡了就讀，讀了就寫，寫了就重證，定稿前審計。

## vacuous truth 的清算：空洞通過的歸納步

ch03 簽過一張支票：「歸納假設是整個歸納步的前件；如果它強到沒有任何狀態能滿足，歸納步會『證明成功』——空洞地。」現在兌現，用一份完整的假證明。

同事也要證 v1 的 `NoDoublePay`，嫌強化麻煩，交出這份候選：

StrongInd ≜ NoDoublePay ∧ dedup = Msgs

他的證明：「義務二，逐動作——Fetch、Ack、Crash 不動 ledger 也不動 dedup，照搬；Credit 的 guard 要求 working[c] ∉ dedup，但 TypeOK 給 working[c] ∈ Msgs = dedup，**前件不可滿足，此案空洞通過**。義務三，第一個合取項就是目標。義務一，初始帳本乾淨，顯然滿足。Q.E.D.」

每個歸納 case 都綠燈，蘊涵也綠燈，報告看起來無懈可擊。但你已經在 ch05 被訓練過：看到「顯然」就拔保險。義務一逐字驗——Init ⇒ StrongInd 要求 dedup = {} 等於 Msgs，而 ASSUME 說 Msgs 非空。**義務一不成立，整份證明作廢。**

值得解剖的是這個錯為什麼這麼香。強化是有方向的誘惑：條款越強，歸納假設火力越大，歸納步越好過——極限就是強到把危險動作的 guard 直接堵死（Credit 在 StrongInd 的世界裡永遠不 enabled），歸納步全綠，**因為它什麼都沒檢查**。一份號稱保證「不重複入帳」的證明，從頭到尾沒有審過任何一次入帳——這跟 ch03 那個三個月沒亮過的退款 invariant、ch08 那座 N = 0 的空城，是同一隻鬼的第三次現身。

三個義務是串聯的保險絲，這個例子展示了它們怎麼互相兜底：**歸納步借來的火力，起點要還**。強化是借貸，義務一是討債的。自我察覺的動作清單：

1. **三義務逐項打勾，起點不是儀式。**你的 Ind 越強，Init ⇒ Ind 越可疑——它是「強過頭」唯一的出口檢查。
2. **witness 紀律（ch03 的老警報器）。**對每個空洞通過的 case 問：有沒有**可達**狀態真的踏進這個 case？Credit 是唯一動 ledger 的動作，它的 case 空洞＝你的證明沒看過一次入帳。對照合法的空洞：IndTP 的起點七條全空洞，但每條前件在 worked trace 裡都真實亮起過——空洞發生在初始是日常，發生在「整個可達世界」是事故。
3. **量一下 Ind 圈出的世界還能做什麼。**滿足 StrongInd 的狀態裡系統只剩 Fetch、Ack、Crash 在倒水——一個幾乎凍結的世界。把系統「證死」了，證的就是一座空城。

## leads-to 淺談：liveness 證明長什麼樣

本章到此全是 safety。liveness 的證明是另一座山，本書不爬（先說死），但站在埡口看一眼山形，值得五分鐘。

你其實已經見過一個雛形：ch07 證 FairSpec ⇒ AllPaid 時用的遞減量尺 M ≜ 2·|queue| ＋ 忙碌數——每個真步讓 M 嚴格遞減、M 非負、M = 0 時全入帳。把那個論證放進正式的形狀，地基是 Lamport 的 WF1 規則（出自他 1994 年的 TLA 論文；此處按其形狀轉述、符號換成本書慣例）：要證 □[Next]_vars ∧ WF_vars(A) ⇒ (P ⤳ Q)，交三份作業——

1. P ∧ [Next]_vars ⇒ (P′ ∨ Q′)——不做 A 的任何一步，要嘛留在 P、要嘛直接到 Q；
2. P ∧ ⟨Next ∧ A⟩_vars ⇒ Q′——真的做了 A，就到 Q；
3. P ⇒ ENABLED ⟨A⟩_vars——在 P 的世界裡，A 永遠可做。

然後 fairness 收尾：A 不可以永遠可做卻永遠不做（ch07），所以困在 P 的行為終究被踢進 Q。注意前兩份作業都是**動作層的蘊涵**——跟歸納步同一種義務、同一種驗法；而且實際使用時 P 幾乎總是合取著你的 inductive invariant（不然連 ENABLED 都論證不動）。**safety 證明是 liveness 證明的地基**，這句話是字面意思。

整條 liveness 證明的形狀於是浮現：用 WF1／SF1 鍛造一節一節的 P ⤳ Q，再用 ⤳ 的遞移性串鏈、用析取分案合流，長行為靠量尺壓陣——「M = k ⤳ M < k」對每個 k 成立，well-founded 的 ℕ 不允許無限遞減，所以 M ⤳ 0。歸納不變量是在**狀態上**做歸納，leads-to 鏈是在**量尺上**做歸納——同一把刀，換個磨法。SF 對應的規則（SF1）前提更繞，lattice 規則管無限分岔的鏈——到此打住；想看全套，Specifying Systems 第 8 章（ch07 延伸閱讀已列）是標準讀本。

## 陷阱與防禦

ch05 的陷阱表全部繼續適用；下面是證明規模放大之後新長出來的坑。

| 故障模式 | 它怎麼給你假安全感 | 怎麼自我察覺 |
|---|---|---|
| 把目標當 Ind 直接證，卡住就懷疑性質是假的 | 卡死的挫折感像極了「性質不成立」 | 先校準預期：有意義的 safety 幾乎從不 inductive（Lamport：seldom the case）。卡住是迴圈的第一步，不是終點；判可達之前不准下結論 |
| 歸納步偷用沒寫進條款的可達性事實 | 條款多了，「這種狀態實際上不會發生」混在十幾行推理裡不顯眼，還常披著「顯然」的皮 | 歸納步的彈藥清單只有四樣：歸納假設的條款、guard、效果、ASSUME。每一步指認彈藥來源；指認不出來的，要嘛是漏的條款（去強化），要嘛是循環論證 |
| 64 格矩陣漏格 | 「這動作跟這條款無關」憑感覺跳過——漏的那格往往正是 bug 門；漏一格，整份證明無效 | 動作 × 條款矩陣逐格清帳；「未動」也是一格、也要一行理由（速記一不是免檢，是檢完的章） |
| 強化過頭，歸納步空洞通過 | 歸納步全綠最快的方法是讓它檢查不到東西；StrongInd 的 Credit case 就是現場 | 義務一逐字驗；每個空洞 case 找可達 witness；問「滿足 Ind 的世界還能做什麼」 |
| 條款堆積、互相糾纏、目標漂移 | 七八條條款疊完，證出來的東西跟當初的 S 失聯；或者死條款白繳維護稅 | 定稿審計：每條條款標注「被哪些格用到」，沒人用的刪掉重驗（B 的下場）；義務三白紙黑字重寫一遍 |
| 小模型 TLC 掃過 Ind 就當證完 | 「Init ≔ Ind 跑一步沒紅」在 2 RM、0..2 上成立 ≠ 任意參數成立 | 角色分清：TLC 是歸納步的快篩（找壞前驅神速），定理還是要手上或機器上（ch16）走完三義務；反過來，動手證之前先讓 TLC 篩一輪，是聰明而不是作弊 |
| 對模型成立 ≠ 對系統成立 | IndV1 全程站在「Credit 原子」與「dedup 永存」上；定理越漂亮，越容易忘記它的地基 | 把證明實際引用的 spec 假設抄成清單貼在定理旁（ch08 的抽象帳）；實作變更時拿清單對照，失配即失效 |

## 紙上推演

**題 1 [20 分鐘] ★★ — 三個候選，三種命運。**對 SettlementV1（含 TypeOK 為前提），判斷下列三個候選各是什麼身分：(i) 是 invariant 嗎？(ii) 是 inductive 嗎？(iii) 對證明 `NoDoublePay` 有用嗎？非 inductive 的要給出具體壞前驅；不是 invariant 的要指出可達反例。

- (a) Inv_a ≜ ∀ m ∈ Msgs : ledger[m] ≤ 1
- (b) Inv_b ≜ ∀ m ∈ Msgs : m ∈ dedup ⇒ ledger[m] ≥ 1
- (c) Inv_c ≜ ∀ m ∈ Msgs : m ∈ queue ⇒ ledger[m] = 0

### 推演解答

(a) **是 invariant（本章主定理），不 inductive。**壞前驅即正文的 s_x：⟨queue = {m2}, working = (c1 ↦ m1, c2 ↦ "idle"), ledger = (m1 ↦ 1, m2 ↦ 0), dedup = {}⟩——滿足 Inv_a，Credit(c1) 一步打穿。不可達（DedupCovers 排除它），所以走強化分支——正文走完了。

(b) **是 invariant，而且 inductive，但沒用。**封閉逐動作：只有 Credit 相干——對 m₀：dedup′ 收編 m₀ 而 ledger′[m₀] = ledger[m₀] + 1 ≥ 1（TypeOK 給 ledger[m₀] ∈ Nat）；對 m̃ ≠ m₀：dedup 對 m̃ 的隸屬與 ledger[m̃] 都未變。Fetch、Ack、Crash 不動兩個變數。起點：dedup = {}，空洞成立。三義務的死穴在第三條：Inv_b 對 ledger 只給**下界**，蘊涵不出 ≤ 1。這就是正文說的「雙向耦合多出來的那一半」：自己站得住，對目標毫無貢獻——**inductive 不等於有用，義務三把關**。

(c) **根本不是 invariant。**直接歸納會在 Crash 卡住（c 手持已入帳的 m，crash 把 m 送回佇列），壞前驅是 ch08 危險路徑的 s₂——而這次它**可達**：ch08 那張表給了完整的三步 trace（s₀ →Fetch→ s₁ →Credit→ s₂），接上 Crash(c1) 就是反例，s₃ 本身就是 Inv_c 的可達反例（m1 ∈ queue 且 ledger[m1] = 1）。強化迴圈的「可達」分支長這樣：不要強化，舉反例，宣告性質為假。三個候選湊齊三種命運：真而不 inductive、inductive 而無用、假。判定永遠按這個順序問。

**題 2 [15 分鐘] ★★ — 守恆強化。**派工機：常數 N ∈ ℕ（ASSUME N ≥ 1）；變數 pending（待派）、active（進行中）、closed（已結案），皆屬 ℕ。Init：pending = N ∧ active = 0 ∧ closed = 0。動作 Assign：前提 pending > 0，效果 pending 減一、active 加一。動作 Finish：前提 active > 0，效果 active 減一、closed 加一。目標：closed ≤ N。
（a）直接歸納，找出卡點、寫出壞前驅、判可達。（b）強化並完成三義務的層級證明。

### 推演解答

（a）Assign 不動 closed，無事。Finish 卡：步前 closed ≤ N 容許 closed = N，配上 active ≥ 1，步後 closed′ = N + 1。壞前驅 ⟨pending = 0, active = 1, closed = N⟩（滿足 closed ≤ N，Finish enabled）。可達嗎？不可達——工單不會憑空增生：每張工單恆在三個桶子之一。這句話是守恆。

（b）Sum ≜ pending + active + closed = N；IndJob ≜ TypeOK ∧ Sum（TypeOK：三變數 ∈ ℕ）。

⟨1⟩1. 起點：N + 0 + 0 = N；三值皆 ∈ ℕ。
⟨1⟩2. 封閉：分兩動作。
  ⟨2⟩1. Assign：pending 減一、active 加一，和不變；guard pending > 0 保證 pending′ ∈ ℕ；closed 未動。
  ⟨2⟩2. Finish：active 減一、closed 加一，和不變；guard active > 0 保證 active′ ∈ ℕ。
  ⟨2⟩3. Q.E.D. 動作只有兩個。
⟨1⟩3. 蘊涵：closed = N − pending − active ≤ N。理由：pending, active ∈ ℕ 故非負。
⟨1⟩4. Q.E.D. ∎

這是守恆量啟發法的第三次出場：ch05 的 copies(m)、ch08 題 2 的 free + held = N、這裡的三桶總和。同一招用到第三次，該進肌肉了：**看到「東西在桶子之間搬」的系統，第一個候選條款永遠是桶子總和。**另外注意 ⟨1⟩3 用了 TypeOK 的非負——「守恆＋型別」才蘊涵得出上界，單獨一條都不夠。

**題 3 [30 分鐘] ★★★ — 在 IndTP 上動刀，驗兩個歸納步。**
（a）把 ch11 題 3 的變體動作加進擴充版 TwoPhase：RMTimeoutAbort(r) ≜ rmState[r] = "prepared" ∧ rmState′ = [rmState EXCEPT ![r] = "aborted"] ∧ UNCHANGED ⟨tmState, tmPrepared, msgs⟩。對 IndTP 跑這個新動作的歸納步：哪些條款的哪些格會卡？卡點的壞前驅可達嗎？結論是什麼？
（b）回到沒有 RMTimeoutAbort 的擴充版，把 TMCrash 的 guard 從 tmState = "init" 放寬成 TRUE（任何時候都能倒）。IndTP 的哪些條款在 TMCrash 的歸納步上破？給出最小修補，並指出修補波及哪些其他格。

### 推演解答

（a）逐條款過 RMTimeoutAbort(r)：T′ ✓；I1′ 對 r 前件假；I2′、I3′、I4′ 變數未動。卡在兩格。**I6′ 對 r**：步後 aborted，要 A ∈ msgs ∨ P(r) ∉ msgs——但 guard 只說 r 是 "prepared"，兩個析取都沒著落（正常準備過的 r 有 P(r) ∈ msgs 而 A 不在場）。**I7′**：若 C ∈ msgs，步前 I7 給 r ∈ {"prepared", "committed"}——prepared 滿足 guard，動作 enabled，步後 r 是 "aborted"，I7′ 直接破。把 I7 的卡點具體化：⟨rmState = (r1 ↦ "committed", r2 ↦ "prepared"), tmState = "committed", tmPrepared = RM, msgs = {P(r1), P(r2), C}⟩——逐條款驗它滿足 IndTP（I1 ✓、I2 ✓、I3 空洞、I4 ✓、I5 ✓、I6 空洞、I7 ✓）。可達嗎？**可達**——它正是 ch11 題 3 那條七步 trace 走到第 6 步的狀態。可達分支沒有回頭路：不必修補、不能修補，RMTimeoutAbort(r2) 接上去就是 TCConsistent 的反例，性質在這個變體上是假的。注意收穫：**證明的卡點直接指出設計的承重牆**——RMChooseToAbort 那行 "working" guard（ch11 說 blocking 的種子埋在那裡）拆掉的瞬間，I7 應聲而碎。證明不只是驗收工具，是定位工具。

（b）放寬後 TMCrash 可以從 "committed"／"aborted" 倒下，tmState′ = "crashed"。**I2′ 破**：C ∈ msgs 且步前 tmState = "committed"（I2 容許），步後 tmState ≠ "committed"。**I3′ 對稱地破**。其餘六條不引用 tmState，照舊。最小修補：弱化兩條——I2w ≜ C ∈ msgs ⇒ tmState ∈ {"committed", "crashed"}；I3w ≜ A ∈ msgs ⇒ tmState ∈ {"aborted", "crashed"}（放寬 crash 後它們才是真話）。然後**重審所有用過 I2、I3 的格**（審計紀律）：⟨2⟩6 ⟨3⟩2 與 ⟨2⟩7 ⟨3⟩2 的論證形如「前件 ⇒ tmState ≠ "init" 與 guard 矛盾」——弱化版照樣給出 ≠ "init"，存活；⟨2⟩8 換一種活法——guard 沒了，但弱化後件被「直接保持」：從 "committed"／"aborted" 倒下落在 "crashed"，仍在弱化值域內。唯一斷裂的是 ⟨2⟩4 ⟨3⟩1 的 C ∧ A 互斥：I2w ∧ I3w 容許兩者並存於 tmState = "crashed"。把當初「當推論不當條款」的那句話請回來當條款：I8 ≜ ¬(C ∈ msgs ∧ A ∈ msgs)。驗它 inductive：TMCommit 加 C，需 A ∉ msgs——I3w 配 guard "init" 給出；TMAbort 對稱；其餘動作不加 C 也不加 A；放寬版 TMCrash 不動 msgs。⟨2⟩4 與 ⟨2⟩6 改用 I8 收口，全盤重新閉合。教訓有二：模型動一寸，invariant 動一尺，而且**動完要全矩陣重審**；「推論 vs 條款」的選擇不是一次性的——模型弱化時，便宜的推論會漲價成必要的條款。

## 自我檢核

口頭回答，講得出來才算過：

1. 三個義務各是什麼？義務二嚴格說面對的是 [Next]_vars——為什麼 stuttering 步免費，所以證明只列真動作？
2. 「invariant 為真」與「inductive」差在哪？用 s_bad 講一遍：它滿足什麼、打破什麼、為什麼歸納步必須照顧這個不可達的狀態？
3. 強化迴圈的五個動作是什麼？「讀卡點」的三問是什麼？卡點可達與不可達各走哪條路——本章哪個例子走了可達分支？
4. IndV1 的耦合條款怎麼讀（正讀與逆否）？整份證明為什麼不需要「訊息至多一份」的守恆？這對你的 pipeline 防線設計說了哪句話？
5. IndTP 七條，每條一句白話角色。TMCommit 的 I7 步驟用到哪四條條款加哪個 guard？ch11 那條強化鏈在定稿證明裡搬到了哪裡？
6. TMCrash 的 case 為什麼平凡？精確理由是什麼（不只是「不動 rmState」）？guard 放寬成 TRUE 之後哪兩條條款先破、怎麼修？
7. 空洞的歸納步是怎麼製造出來的？三義務裡哪一條是它的最後防線？「合法的初始空洞」與「致命的恆假前件」怎麼分？
8. TLC 與 Apalache 在證明工作流裡的新工位是什麼？「Init ≔ Ind 跑一步」驗的是哪個義務、不驗哪個？它的綠燈為什麼仍然不是定理？

## 延伸閱讀

- **Leslie Lamport, “Using TLC to Check Inductive Invariance”（2018-08-23）**：<https://lamport.azurewebsites.net/tla/inductive-invariant.pdf> — 兩頁紙把本章三個義務一字不差地寫出來（含那句「我們在乎的 invariant 很少自己 inductive」），然後教你把 Init 換成候選 Ind、讓 TLC 當歸納步快篩。讀完正文再讀它，你會認出每一句。（2026-06 開頁核對）
- **Leslie Lamport, “Proving Safety Properties”（2019-05-18）**：<https://lamport.azurewebsites.net/tla/proving-safety.pdf> — 從找 inductive invariant、寫 ⟨1⟩ 層級證明、到把每一步餵給 TLAPS 的完整工作流，以互斥協議為例。本章手寫的東西，它的第 4–6 節給出工具化對應——是 ch16 之前最好的橋。（2026-06 開頁核對目錄）
- **Leslie Lamport, “Teaching Concurrency”（2009）**：<https://lamport.azurewebsites.net/pubs/teaching-concurrency.pdf> — ch05 引過；文末那個小演算法的 invariant 習題，是練本章強化迴圈最便宜的啞鈴——先自己卡一次，再看他的解。
- **Lorin Hochstein, “Inductive invariants”（Surfing Complexity, 2018-12）**：<https://surfingcomplexity.blog/2018/12/27/inductive-invariants/> — 用最小的例子把「為真但不 inductive」講透的短文，並親手解了上面那道習題；當本章的第二視角複習。
- **Leslie Lamport, *A Science of Concurrent Programs***：<https://lamport.azurewebsites.net/tla/science-book.html> — Lamport 晚期的集大成之作（Cambridge University Press 2026 年出版，官網提供免費 PDF；2026-06 開頁核對）。歸納不變量與 refinement 在完整理論裡的位置都在這裡；建議讀完 ch15、ch16 再回來啃。
- **Apalache 手冊〈Running the Tool〉**：<https://apalache-mc.org/docs/apalache/running.html> — 用 `--init=IndInv --inv=IndInv --length=1` 兩段式查詢機械化本章兩個義務的官方說明（2026-06；原理見 ch16）。
