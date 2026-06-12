# ch16 — 機器證明：TLAPS、Apalache 與定理證明全景

> **本章解決什麼問題**：ch14 你手寫了 8 × 8 的義務矩陣、ch15 又添上 refinement 的逐步義務——但查證者始終是你自己，而 ch14 的陷阱表說得明白：漏一格，整份證明無效。本章把「查證」這份工作交給機器：TLAPS 把你的 ⟨1⟩ 層級證明拆成一條條 proof obligation 丟給後端 prover 逐條查驗；Apalache 把歸納檢查編成 SMT 查詢；再往右是 Lean、Rocq、Isabelle 的深度數學。Part V 在此收官：全書的嚴謹度光譜補上最後一格，並回答一個務實的問題——工程師走多深才划算。

## 從你已知的出發

你最信任的品質機制大概不是任何一個人，而是 CI 的 required checks。一個 PR 要進 main，得讓每一條 check 變綠：lint、型別檢查、單元測試、整合測試。沒有任何一條 check「理解」你的 PR 在做什麼——每條只負責一小件事，但**全部通過**這件事本身就是承諾。而且機器不會累、不會給面子：你少跑一條，它就紅一條。

TLAPS 的工作模式就是這個形狀。你交出一份 ⟨1⟩ 層級證明（你從 ch05 寫到現在的那種），proof manager 把它拆成一條條獨立的 **proof obligation**（證明義務）——每條義務是一小句「在這些事實之下，這個斷言成立」——然後逐條丟給後端 prover 查驗。全綠，定理成立；紅一條，整份不算。ch14 那張 64 格矩陣你靠紀律逐格清帳，靠「速記不是免檢，是檢完的章」撐住品質；機器版的好處很直白：**漏格在語法上不可能**——QED 步沒湊齊案例，義務直接生不出來或直接紅。

第二條經驗也搬得進來。你不會把三千行的 PR 丟給 reviewer——會被退、會漏看、會拖一週。你拆成小 PR，每個小到 reviewer 一眼看得完。TLAPS 的後端 prover 就是那位 reviewer：一條義務塞太多推理，後端在時限內啃不動，回你一個 timeout。處方跟拆 PR 一字不差：把那一步往下展開一層，⟨3⟩ 拆成幾個 ⟨4⟩，每條義務變小，後端就吃得下了。「SMT 搞不定就拆步驟」是本章的工作迴圈，而你已經用它管理程式碼審查很多年——只是名字叫「把大 PR 拆小」。

第三條是你該帶進本章的戒心。CI 全綠不代表功能是對的——測試本身寫錯，綠燈就是假的。機器證明同理：TLAPS 查證的是「**這份證明確實證出了這條定理**」，至於定理寫的是不是你以為的那句話、spec 對不對得上現實，機器一個字都沒擔保。這條裂縫貫穿全章，「陷阱與防禦」算總帳。

## 嚴謹度光譜：每一層買什麼、付什麼

把全書用過的驗證手段排成一條光譜。這張圖是本章的骨架，也是 ch17、ch18 回頭引用的座標系：

```text
┌────────────────────────────────────────────────────────┐
│ 測試                                    （你的日常）   │
│ 買到：抽樣的證據——跑過的案例沒出錯                     │
│ 付出：案例要人想；調度與交錯靠運氣                     │
└───────────────────────────┬────────────────────────────┘
                            │  保證變強
                            ▼  成本變貴
┌────────────────────────────────────────────────────────┐
│ TLC：顯式窮舉                              （ch09）    │
│ 買到：這組有限參數下的全部狀態，一個不漏               │
│ 付出：狀態爆炸；參數寫死——checked，不是 proved         │
└───────────────────────────┬────────────────────────────┘
                            │  保證變強
                            ▼  成本變貴
┌────────────────────────────────────────────────────────┐
│ Apalache：符號／SMT                                    │
│ 買到：固定步數的反例搜尋＋歸納檢查，值域不必砍         │
│ 付出：型別註記；步數有上界；參數維度仍寫死             │
└───────────────────────────┬────────────────────────────┘
                            │  保證變強
                            ▼  成本變貴
┌────────────────────────────────────────────────────────┐
│ TLAPS：機器查證的證明                                  │
│ 買到：任意參數、任意規模的定理——proved                 │
│ 付出：證明仍由人寫，機器只負責查；以天、週計           │
└───────────────────────────┬────────────────────────────┘
                            │  保證變強
                            ▼  成本變貴
┌────────────────────────────────────────────────────────┐
│ Lean／Rocq／Isabelle：深度數學                         │
│ 買到：從邏輯地基蓋到屋頂的確定性（seL4、CompCert）     │
│ 付出：以人年計——那是另一個職業                         │
└────────────────────────────────────────────────────────┘
```

三句讀圖說明。**其一，這是工具箱，不是排行榜。**左端不可恥、右端不高尚——每往下一格，你買到更強的保證，也簽下更貴的帳單；「該停在哪格」是工程判斷，本章末尾給決策框架。**其二，你的手寫證明住在第四格。**ch14 的 IndTP 證明在數學上就是 TLAPS 等級的物件——任意參數、逐步可查——差別只在查證者是你自己，而人會累、會漏、會對自己的「顯然」心軟。**其三，相鄰層是同事不是對手。**ch14 已經演過一次：TLC 與 Apalache 當歸納步的快篩、人簽定理；本章會看到 TLAPS 紅燈時你反過來請 TLC 幫忙分診。光譜上的實戰永遠是混編的。

## TLAPS：你已經會寫它的證明了

先把 ch05 簽的那張本票兌現。當年立層級格式時說過：「到 ch16 讀真 TLAPS 證明時無縫接軌。」現在正式宣布：**本書的手寫格式就是 TLAPS 的證明語言**——⟨1⟩1 在 ASCII 裡寫成 `<1>1.`，Q.E.D. 步寫成 `QED`，「理由：…」寫成 `BY ...`。你不是要學一門新語言，是要看熟一套你寫了十一章的格式換上機器讀得懂的衣服。

機器這邊的分工（依官方文件與 repo 的描述，2026-06）：proof manager `tlapm` 負責讀懂層級結構、把證明拆成義務、調度後端、彙整紅綠；後端 prover 負責真正的推理，成員包括 SMT solver（預設 Z3，也支援其他）、一階邏輯的 tableau prover Zenon、客製化的 Isabelle/TLA+，以及吃命題時序邏輯的 LS4。專案如今由 TLA+ 社群維護在 `tlaplus/tlapm`。

### Proof obligation：證明的最小可查單位

tlapm 走訪你的證明樹，對每個**葉步驟**（不再往下展開的步）產出一條義務：

> 在「此步可用的事實與定義」之下，證明「此步的斷言」。

義務彼此獨立——可以平行送後端、可以快取（已證過的義務會被記住，改了 spec 只重查受影響的那些，跟增量編譯同款邏輯）。這個設計把 ch05 的觀察做成了架構：層級證明讓每個跳步「肉眼可見地少一層」，而在 TLAPS 裡，每一層就是一道閘門——你想跳步，義務就會胖到後端吃不下，紅燈逼你補層。**「顯然」在這套系統裡不是修辭問題，是會超時的工程問題。**

關鍵語意三件套，對照你的手寫習慣：

| TLAPS 寫法 | 語意 | 你手寫時的對應動作（ch05／ch14） |
|---|---|---|
| `BY e1, e2 DEF d1, d2` | 用事實 e1、e2（前面的步驟名、引理、CASE 假設…），並展開定義 d1、d2，證本步 | 「理由：⟨3⟩2 與 guard；展開 Credit 的定義」——彈藥逐項指認 |
| `OBVIOUS` | 不引額外事實，光靠當前上下文就該成立 | 「理由：直接由型別／上下文」——最薄的一行理由 |
| `<2>. SUFFICES ASSUME P PROVE Q` | 把本層目標改寫成「假設 P、證 Q」 | 「設步前狀態滿足 Ind，分動作討論」 |
| `<2>1. CASE A` | 在「析取肢 A 為真」的假設下證目標；步名 `<2>1` 引用的就是這個假設 | ⟨2⟩ 層的「情況 Fetch(c, m)」 |
| `<2>. USE DEF TypeOK` | 此後所有義務自動展開 TypeOK | 「這行豁免引用一次、全章有效」的速記宣告 |
| `<2>. QED BY <2>1, ..., <2>7 DEF Next` | 本層目標由列出的步湊齊；展開 Next 以確認案例蓋滿 | 「Q.E.D. 七類動作蓋住所有真步」 |

注意一個容易錯過的預設：**TLAPS 不自動展開定義**。你不寫 `DEF Credit`，後端看到的 Credit 就是一個不透明符號，義務多半證不動。這不是不便，是紀律的語法強制版——ch14 說歸納步的彈藥清單只有四樣、每一步要指認來源；TLAPS 把「指認」變成必填欄位，忘了指認的下場從「審稿人皺眉」升級成「義務翻紅」。

### 後端與工作迴圈

一條義務送出後，預設策略是依序嘗試：**先 SMT，不行換 Zenon，再不行上 Isabelle**（依官方文件的預設順序，2026-06；各自的時限本書不抄死）。三位的胃口不同：SMT 擅長算術與基本的集合、函數推理，怕的是量詞層層疊的式子；Zenon 是一階邏輯出身，量詞與集合推理在行，但完全不懂算術；Isabelle 當壓陣，偶爾撿起前兩位都漏接的球，特別是需要歸納模式的目標。時序推理的葉步驟（馬上會看到 `PTL`）則交給 LS4。你也可以在 `BY` 後面點名指定後端——但對讀者而言，知道「有分工、有預設順序」就夠了。

於是日常工作迴圈長這樣，跟 ch14 的強化迴圈互為表裡：

1. 先寫**粗**的：每個 ⟨2⟩ 步直接 `BY` 一坨事實加 `DEF` 一串定義，賭後端吃得下。
2. 紅了，先分診——紅燈有兩種病：**斷言是假的**，或**義務太胖**。這是與手寫卡點唯一的本質差異：手寫時卡住幾乎總是「缺條款」，機器紅燈多了一種「後端讀不懂」的假陽性。
3. 分診的工具是光譜的左鄰：把出事的那條義務交給 TLC 或 Apalache 找反例（ch14 教過的快篩）。找到反例＝真的假，回去走強化迴圈；找不到＝多半太胖，進下一步。
4. **拆步驟**：把胖義務往下展開一層，每個子步驟附上自己的小 `BY`。拆到後端全綠為止——跟把大 PR 拆小到 reviewer 看得完，同一個動作。

## 熱身：Consensus.tla 的九行證明

ch12 在延伸閱讀裡埋過一句：「Consensus.tla 裡那段 TLAPS 證明是 ch16 的預習材料。」現在兌現。Consensus.tla 你熟到能背——chosen 從空集合到單元素集合的一步定終身（ch12 的頂樓）——它檔尾的 Invariance 定理是世界上最小的真 TLAPS 證明之一（tlaplus/Examples 原文，2026-06 逐字對照）：

```tla
THEOREM Invariance == Spec => []Inv
<1>1. Init => Inv
  BY FS_EmptySet DEF Init, Inv, TypeOK
<1>2. Inv /\ [Next]_chosen => Inv'
  <2>1. Inv /\ Next => Inv'
    BY FS_Singleton DEF Inv, TypeOK, Next
  <2>2. Inv /\ UNCHANGED chosen => Inv'
    BY DEF Inv, TypeOK
  <2>. QED  BY <2>1, <2>2
<1>3. QED   BY <1>1, <1>2, PTL DEF Spec
```

逐步認親。⟨1⟩1 是**起點義務**：Init ⇒ Inv，理由欄裡 `DEF Init, Inv, TypeOK` 是展開定義，`FS_EmptySet` 是引理——FiniteSetTheorems 模組的庫存定理（空集合是有限集、基數為 0），用來餵 Cardinality(chosen) ≤ 1 這個斷言。站在別人證好的定理上，就像你 import 一個函式庫。⟨1⟩2 是**封閉義務**，內部拆兩案：⟨2⟩1 真步（FS_Singleton：單元素集合有限、基數 1），⟨2⟩2 stuttering。注意這個 ⟨2⟩2——ch14 開頭你立過「stuttering 步免費，全章豁免」的條款，手寫時引用一次就好；**機器不送這個人情**，[Next]_chosen 的兩個析取肢一肢一案，少一案 QED 就湊不齊。⟨1⟩3 的 `PTL` 是全段的點睛：從「起點」與「封閉」兩個動作層事實推出 □Inv 這個時序結論——這一步推理你在 ch05 親手證過，它叫**不變量規則**。在 TLAPS 裡，你的 ⟨1⟩3「由不變量規則」變成一次 PTL 後端呼叫：機器替你執行了那條你證明過的規則。

同檔再往下還有一段 LivenessTheorem，順手看一眼（原文節錄，2026-06）：

```tla
<1>1. [][Next]_chosen /\ WF_chosen(Next) => [](Init => Success)
  <2>1. Init' \/ (chosen # {})'
    BY DEF Init
  <2>2. Init /\ <<Next>>_chosen => (chosen # {})'
    BY DEF Init, Next
  <2>3. Init => ENABLED <<Next>>_chosen
    BY ValuesNonempty, ExpandENABLED DEF Init, Next
  <2>. QED  BY <2>1, <2>2, <2>3, PTL DEF Success
```

認出來了嗎？⟨2⟩1、⟨2⟩2、⟨2⟩3 正是 ch14「leads-to 淺談」裡 WF1 規則的三份作業：不做 A 也走不出 P ∪ Q、做了 A 必到 Q、在 P 裡 A 永遠可做。`ExpandENABLED` 是把 ENABLED 展開成存在量詞的指令（ch15 警告過 ENABLED 是代換的地雷區，機器處理它也得用專門工具）。liveness 的山本書不爬（ch14 立的界碑不動），但你現在知道：山上也通機器的路，而且路標跟你學過的一模一樣。

## 精讀 DieHard_proof.tla：手寫動作的機器對應

主菜。tlaplus/Examples 的 DieHard 目錄裡，spec 旁邊躺著一份 `DieHard_proof.tla`（2026-06 開頁下載、逐字對照）——對 ch08 精讀過的那兩個水壺，機器查證 `Spec => []TypeOK`。選它當精讀對象的理由：spec 你手推過全狀態空間（ch08 的六層 BFS），TypeOK 你知道為什麼幾乎總是第一個 invariant（ch08 的四層理由），所以全部注意力可以放在**證明語言**本身。

檔頭的註解先交代立場（原文）：

```tla
(* TLAPS proof of  Spec => []TypeOK.                                       *)
(* (NotSolved is meant to be violated -- it's the puzzle's "find a         *)
(*  solution" search invariant -- so we don't try to prove it.)            *)
```

NotSolved 本來就是要被打破的——它是「把目標寫成 invariant 的否定」那記招式的道具（ch08），所以沒人會去證它。同一份 spec，TLC 拿 NotSolved 找解、TLAPS 拿 TypeOK 簽定理：**反例是中性的機器產物，定理也是——立場都由人定**。

### 第一塊：引理

```tla
LEMMA MinNat ==
  ASSUME NEW m \in Nat, NEW n \in Nat
  PROVE  Min(m, n) \in Nat /\ Min(m, n) <= m /\ Min(m, n) <= n
  BY DEF Min
```

`ASSUME NEW m \in Nat ... PROVE ...` 讀作「任取 m, n ∈ ℕ，證明…」——數學裡的 ∀ 引入，你每份手寫證明開頭的「任取 m ∈ Msgs」。LEMMA 是抽出來重用的小定理：Min 的三條基本性質後面要用好幾次，抽成引理，正文就能像引用速記一樣 `BY MinNat`——ch14 開證前先立三條速記，同一個動作。理由欄 `BY DEF Min` 只展開 Min 的定義（一個 IF-THEN-ELSE），後端自己分案搞定。

### 第二塊：骨架

```tla
THEOREM TypeCorrect == Spec => []TypeOK
<1>1. Init => TypeOK
  BY DEF Init, TypeOK
<1>2. TypeOK /\ [Next]_<<big, small>> => TypeOK'
  <2>. SUFFICES ASSUME TypeOK, [Next]_<<big, small>>  PROVE TypeOK'
    OBVIOUS
  <2>. USE DEF TypeOK
  <2>1. CASE FillSmallJug
    BY <2>1 DEF FillSmallJug
  <2>2. CASE FillBigJug
    BY <2>2 DEF FillBigJug
```

骨架與你的手寫證明逐行同構：

- `<1>1`＝**起點義務**。big = 0、small = 0 逐項在值域內——ch14 ⟨1⟩1 的「逐項在值域內」，這裡一行 `BY DEF` 就讓 SMT 收工。
- `<1>2`＝**封閉義務**。第一個子步 `SUFFICES ASSUME ... PROVE TypeOK'` 就是你寫了三章的開場白「設步前滿足 TypeOK」；它自己的理由是 `OBVIOUS`——改寫目標成假設前件、證後件，邏輯上是 ⇒ 的定義，不需要彈藥。
- `<2>. USE DEF TypeOK`＝速記宣告：此後每條義務自動展開 TypeOK，不必每步重抄。注意這兩個 `<2>.` 都**沒有編號尾碼**——無名步，不能被引用，專門放「改寫目標」「注入事實」這類管家動作。
- `<2>1` 到 `<2>6`＝**逐動作分案**，每案一行：CASE 假設（該動作為真）加上動作定義，後端直接驗「新值在值域內」。FillSmallJug 把 small 設成 3、big 不動——3 ∈ 0..3，SMT 眨個眼。

收尾（原文）：

```tla
  <2>7. CASE UNCHANGED <<big, small>>
    BY <2>7
  <2>. QED  BY <2>1, <2>2, <2>3, <2>4, <2>5, <2>6, <2>7 DEF Next
<1>. QED  BY <1>1, <1>2, PTL DEF Spec
```

`<2>7` 又是那個機器不肯豁免的 stuttering 案——兩個變數都沒動，TypeOK′ 照搬，理由就是 CASE 假設本人。倒數第二行的 QED 是**裝配說明**：七案蓋滿 [Next]_vars 的所有析取肢，`DEF Next` 讓後端親自核對「真的蓋滿了」——你手寫的「七類動作蓋住所有真步」在這裡不是宣告，是一條被機器驗算的義務。最後一行 `PTL DEF Spec`：跟 Consensus 的 ⟨1⟩3 同款，不變量規則收官。

### 第三塊：SmallToBig——機器禁止「顯然」的現場

六個動作裡有四個一行就過，剩下兩個倒水動作是戲肉。SmallToBig 的定義你在 ch08 拆過：big′ ＝ Min(big + small, 5)，small′ ＝ small − (big′ − big)——第二條等式裡引用了 big′，「方程式不是賦值」的最佳實例。手寫驗它的 TypeOK 保持，你大概一句話：「倒完水兩壺都還在容量內，顯然。」機器的回答是 24 行（原文，逐字照引）：

```tla
  <2>5. CASE SmallToBig
    <3>1. big \in Nat /\ small \in Nat /\ big + small \in Nat
      OBVIOUS
    <3>2. big' = Min(big + small, 5) /\ small' = small - (big' - big)
      BY <2>5 DEF SmallToBig
    <3>3. big' \in 0..5
      <4>. Min(big + small, 5) \in Nat /\ Min(big + small, 5) <= 5
        BY <3>1, MinNat
      <4>. QED  BY <3>2
    <3>4. small' \in 0..3
      <4>1. big' \in Nat /\ big' >= big
        <5>1. big + small >= big
          BY <3>1
        <5>. Min(big + small, 5) >= big
          BY <5>1, <3>1 DEF Min
        <5>. QED  BY <3>2, <3>3
      <4>2. big' <= big + small
        <5>. Min(big + small, 5) <= big + small
          BY <3>1, MinNat
        <5>. QED  BY <3>2
      <4>3. small - (big' - big) \in 0..small
        BY <4>1, <4>2, <3>1, <3>3
      <4>. QED  BY <3>2, <4>3
    <3>. QED  BY <3>3, <3>4
```

逐行走，每步標出它對應 ch14 手寫證明的哪個動作：

- **⟨3⟩1（OBVIOUS）**：big、small、big + small 都是自然數。彈藥是上下文裡的 TypeOK（SUFFICES 假設了它、USE DEF 展開了它），0..5 ⊆ ℕ 的推理後端自理。對應手寫的**型別墊底**——ch14 每個 ⟨3⟩ 步開頭那句「TypeOK 給 working[c] ∈ …」。為什麼要先立這一步？因為 SMT 對「加法不會變小」這種事，只在確認運算元是自然數之後才敢點頭——型別是算術推理的入場券。
- **⟨3⟩2（BY <2>5 DEF SmallToBig）**：把動作的兩條效果等式請進上下文。`<2>5` 引用的是 CASE 假設（SmallToBig 為真），`DEF` 展開它的定義。對應手寫的**引用動作效果**：「Credit(c) 的效果：ledger′[m₀] 是 ledger[m₀] + 1」——先指認出處，再使用。
- **⟨3⟩3（big′ ∈ 0..5）**：拆兩小步。無名的 ⟨4⟩ 步引 MinNat 拿到「Min ∈ ℕ 且 ≤ 5」，QED 步用 ⟨3⟩2 把 Min(big + small, 5) 換名成 big′。對應手寫的**等式替換**——⟨2⟩2 裡「由 ⟨3⟩2 是 0 + 1」那種代入。
- **⟨3⟩4（small′ ∈ 0..3）**：全檔最深的一塔，鑽到 ⟨5⟩。手寫時最容易被「顯然」糊掉的位置，機器逼你把直覺拆成三個彼此獨立的事實：
  - **⟨4⟩1：big′ ≥ big**——倒水只會讓大壺變多。注意它居然還要 ⟨5⟩1 先證 big + small ≥ big（加法不變小，靠 ⟨3⟩1 的型別），再 `DEF Min` 分案取下界。MinNat 引理在這裡幫不上忙——它只給了上界方向的兩條，下界這條只能現場展開定義。**引理沒收錄的性質就是沒有**，跟 ch14「歸納假設只給 ≤ 1、不給 = 0」的卡點同一種誠實。
  - **⟨4⟩2：big′ ≤ big + small**——大壺再多也多不過兩壺總量。這次 MinNat 有貨，一行引理一行替換。
  - **⟨4⟩3：small − (big′ − big) ∈ 0..small**——純算術收割：扣掉的量非負（⟨4⟩1），所以不超過 small；扣掉的量不超過 small（⟨4⟩2 移項），所以不會扣成負水。SMT 的甜蜜點，四個事實餵進去一行過。
  - **⟨4⟩ QED**：⟨3⟩2 把表達式換名成 small′，而 0..small ⊆ 0..3 的最後一哩靠上下文裡的 TypeOK（small ≤ 3）。
- **⟨3⟩ QED（BY <3>3, <3>4）**：TypeOK′ 的兩個合取項到齊，**裝配說明**——你每一層收尾的那句「⟨3⟩4 與 ⟨3⟩5 合起來蓋住所有訊息」。

讀完的兩個帶走點。**第一，這就是 ch05 測謊器的機器版。**「倒水顯然不會溢出」被拆成 big′ ≥ big、big′ ≤ big + small 兩個方向的比較式，每個比較式又得先押上型別——你手寫時省掉的每句「顯然」，在這裡都有一行對應的義務。寫過 ch14 的 64 格矩陣再看這 24 行，你該有的感想不是「機器好囉嗦」，而是「我手寫時到底心軟放過了多少步」。**第二，深度是局部的。**六個動作四個一行過、兩個鑽到 ⟨5⟩——層級格式讓嚴謹度按需分配，簡單的案例不陪葬。這正是 ch05 說的「信任可以分層發放」，現在連機器的算力也照這個原則分配。

## Apalache：把歸納步編成 SMT 查詢

光譜第三格。ch09 講過 TLC 的工作方式：一個狀態一個狀態地搬——算出後繼、查 fingerprint、進佇列，直到搬完或爆炸。Apalache 走完全不同的路：**不搬狀態，解方程**。它把變數變成 SMT 求解器裡的符號、把 Init 與每一步 Next 變成約束、把「k 步之內性質被打破」也變成約束，然後把整包丟給 Z3 問：這組約束可滿足嗎？可滿足——解出來的賦值就是一條反例 trace；不可滿足——k 步之內無反例。這叫 **bounded model checking**：官方手冊說得直白（2026-06 開頁核對）：找到 bug 就回報反例，找不到就只承諾「到這個長度為止沒有」。誠實，但有界。

它的甜蜜點恰好補 TLC 的短板。TLC 的成本跟**狀態數**走：值域砍不小、可達集合太大，就是死。SMT 的成本跟**約束的難度**走：ledger ∈ [Msgs → Nat] 這種無限值域，符號變數直接吃下，不必先砍成 0..2——ch14 說 Apalache「連砍值域都省了」，原理就是這個。代價也明碼標價：TLA+ 是無型別的語言，要編進有型別的 SMT 世界，每個變數得先標型別註記、過型別檢查器這關；而且不是每個 TLA+ 運算子都編得動（遞迴定義等角落要繞路，2026-06 時點）。

對你最重要的用法是 ch14 預告過的**兩段式歸納檢查**——把三個義務裡最苦的兩個機械化（指令照官方手冊，2026-06）：

1. 起點義務：`--init=Init --inv=IndInv --length=0`——零步，問「所有初始狀態都滿足 IndInv 嗎」。
2. 封閉義務：`--init=IndInv --inv=IndInv --length=1`——把 IndInv 當出發點集合，走**一步**，問「走得出 IndInv 嗎」。出得去，解出來的那組賦值就是你的壞前驅，強化迴圈的「讀卡點」直接有料；出不去，封閉成立。
3. 蘊涵義務照樣有得查：`--init=IndInv --inv=Safety --length=0`——零步的純蘊涵。

對照 ch14 的手工流程，這是同一套三義務換了執行者；對照 TLC 的「Init ≔ Ind 跑一步」快篩，差別是不必先有限化值域。但要看清楚綠燈的邊界：**參數維度仍然是寫死的常數**。RM ＝ {r1, r2} 之下歸納步全綠，是「這組常數下 IndInv 是 inductive」；「任意 RM 集合」那張字據，光譜上只有下一格簽得出來。Apalache 是 ch14 迴圈裡最好的陪練——找壞前驅比你快幾個數量級——但簽名欄還是留給 TLAPS 或你的手。

維護現況一句（2026-06，開頁核對 README）：Apalache 由原核心開發者**獨立維護**，repo 在 apalache-mc 組織下，README 明言不受任何組織資助——網路舊資料常寫「Informal Systems 維護」，已過時。它同時是 Quint 的後端引擎（見 ch18）。

| | TLC（ch09） | Apalache |
|---|---|---|
| 引擎 | 顯式 BFS ＋ fingerprint | 轉移編成 SMT 約束，問 Z3 |
| 回答的問題 | 這組參數下的全部可達狀態 | k 步之內有沒有反例 |
| 無限值域 | 必須砍成有限 | 整數等值域符號處理，不必砍 |
| 歸納檢查 | Init ≔ Ind 走一步（先有限化） | 兩段式查詢，原值域直上 |
| 綠燈的意思 | 窮舉完畢，此參數組無反例 | k 步內無反例；歸納模式＝該組常數下義務成立 |

## 定理證明全景：光譜最右端住著誰

最後一格不是一個工具，是另一個世界。TLAPS 的證明語言刻意長得像數學系作業，後端自動化撐起大半苦工；最右端的互動式定理證明器（interactive theorem prover）則把「證明」本身變成一種程式設計——每一步都在型別檢查器的監督下構造，信任鏈從邏輯公理一路焊到結論。本書不教任何一個的語法，但你該知道三個名字的定位與代表作，因為它們定義了「最嚴謹」這個詞的現行匯率。

**Lean 4**——數學社群與 AI 的交會點。由 Lean FRO 維護，既是定理證明器也是一門程式語言。它最大的社群資產是 mathlib：協作建成的數學庫，從大學課程一路蓋到研究前沿，規模以數十萬條定理計（2026-06 時點的量級）。它也是「AI 做數學」這條戰線的主場：DeepMind 的 AlphaProof（2024）用強化學習在 Lean 裡搜尋證明、達到 IMO 銀牌等級；其後陸續有系統宣稱在 IMO 等級的題目上達到金牌等級、解答由 Lean 全程查證（截至 2026 年中的報導，本書未逐一驗證）。注意這個架構的形狀：**模型負責起草，Lean 負責把關**——不管生成器多會說話，進得了庫的只有過了型別檢查的證明。這跟 ch18 要談的「LLM 起草、符號工具查證」是同一個信任結構。

**Rocq**——程式驗證的老牌重鎮。原名 Coq，2025 年 3 月隨 9.0 版完成改名（讀舊文獻時兩個名字是同一個東西）。理論底座是「命題即型別、證明即程式」的對應，本書不展開。代表作 CompCert：經機器證明的 C 編譯器，定理是「編譯不改變程式語意」——程式碼級驗證的旗艦（ch01 的全景地圖、ch18 的分界線都拿它當錨）。離本書最近的親戚：ch13 延伸閱讀提過，Verdi 團隊在 Coq 裡完成了 Raft 核心安全性的機器證明——你在 ch13 手推的那五條性質，光譜最右格有人付了全價。

**Isabelle/HOL**——老牌互動式證明器，工程驗證的另一座燈塔。代表作 seL4：一個 microkernel 的 C 實作被證明在功能上符合其抽象規格，作業系統核心等級的全程式碼驗證，人力以人年計（ch18 拿它當成本的刻度原器）。對本章還有一層直接關係：TLAPS 的後端之一就是 Isabelle/TLA+——你前面精讀的證明裡，SMT 與 Zenon 啃不動的義務，最後就是送進 Isabelle 查的。光譜的第四格與第五格之間，有一條現成的管線。

三個名字的共同點，也是與你的距離：它們驗證的對象通常是**數學本身就是產品**的東西——編譯器、核心、密碼學原語、數學定理。後端工程師的日常問題很少長這樣。所以這一格對你的正確姿勢是「知道在哪、讀得懂結論」，不是「搬進去住」。

## 決策框架：走多深才划算

把光譜變成決策表。對每一行，誠實標出你買到什麼、付出什麼——這是給你（資深後端，帶一條結算 pipeline）的版本：

| 你的問題長相 | 建議停在哪格 | 為什麼 |
|---|---|---|
| CRUD 後台、單機業務邏輯 | 測試（＋property-based testing，見 ch18） | 沒有協議級併發；形式化的固定成本攤不到回報 |
| 併發協議、故障 × 交錯，有限配置的反例就能說服你改設計 | 寫 spec ＋ TLC | 性價比之王：AWS 的主力用法（ch17）；反例 trace 直接變設計評審材料 |
| TLC 被狀態爆炸卡死；或你在練 ch14 的強化迴圈、需要快篩 | ＋Apalache | 符號檢查不數狀態；兩段式歸納檢查是壞前驅產生器 |
| 協議是公司的核心資產，需要「任意參數」的定理；或 spec 要長期當權威文件 | ＋TLAPS | 唯一能機器簽發任意規模字據的層；預算以天、週計 |
| 編譯器、OS 核心、密碼學——數學即產品 | Lean／Rocq／Isabelle | 以人年計；對你是地圖知識，不是工作地點 |

三句誠實話收尾。**第一句**：對你的結算 pipeline，九成的價值在第二格就拿完了——「寫 spec 的最大價值是先想清楚」（ch01）加上 TLC 的反例，已經覆蓋 AWS 論文裡七個團隊的主要用法。**第二句**：學會**讀** TLAPS 證明的回報，比學會寫高得多——寫是另一份工作，讀讓你接得住社群裡現成的證明資產（Paxos、Raft、各種佇列協議），也讓你手寫證明的紀律有了校準器。本章教的是讀。**第三句**：機器證明不修「spec 對不對現實」的裂縫——IndV1 的定理再怎麼機器查證，你的 production 把 Credit 拆成兩步它就作廢（ch14 的前提清單），而 spec 與 code 的漂移是工業界真實的痛（ch17 的 MongoDB 案例）。光譜往右走買的是「推理無誤」，永遠買不到「模型如實」。

## 陷阱與防禦

| 故障模式 | 它怎麼給你假安全感 | 怎麼自我察覺 |
|---|---|---|
| 綠燈崇拜：把「證明通過」當「系統正確」 | 機器查的是「這份證明證出了這條定理」；定理寫弱了、變數寫錯了、ASSUME 塞了矛盾（矛盾前提下萬物可證——vacuous truth 的終極形態），照樣全綠 | 把定理唸成白話講給自己聽；檢查每條 ASSUME 是否可滿足；問 ch15 的老問題——定理說的是「我的系統」嗎 |
| 定理少寫一半，機器不會替你想 | 把定理寫成 Ind ∧ [Next]_vars ⇒ Ind′ 而不是 Spec ⇒ □Ind——起點義務根本沒進場，封閉全綠就慶祝 | 機器只查你交來的義務，不查你沒交的；對照 ch14 三義務清單逐項點名（紙上推演題 3 的劇本） |
| 把 Apalache 的 bounded 綠燈當定理 | 「k = 10 沒反例」說的是十步以內；第十一步的反例一個字都沒否認 | 報告永遠帶著 k；要「永遠」，走兩段式歸納檢查或上 TLAPS |
| 大顆 BY 的技術債 | 今天後端撐得起一條胖義務；spec 改一行、義務變胖一圈，紅在離修改最遠的地方 | 戲肉步驟主動拆層（DieHard 的 ⟨5⟩ 塔是示範）；把「義務小而多」當投資不當囉嗦 |
| 兩種紅燈不分診 | 義務失敗＝「假了」或「後端讀不懂」，急著拆步驟的人會把真反例拆到看不見 | 先丟 TLC／Apalache 對紅掉的義務找反例：有反例走強化迴圈，沒反例才拆步驟 |
| DEF 漏掛 | 定義沒展開，後端面對不透明符號，紅得莫名其妙；於是亂加事實直到「碰巧」綠 | 每步指認彈藥（ch14 的清單紀律）；紅燈先查「我給後端看得到它需要的定義嗎」 |
| 證明腐化 | spec 改了、證明沒跟上——跟 ch17 的 spec–code 漂移同型，只是發生在樓上 | 把證明當程式碼管理：spec 變更必重跑 tlapm；快取讓重跑只付增量的錢 |

## 紙上推演

### 題 1：把 ch14 的手寫證明穿上 TLAPS 的衣服（[25 分鐘] ★★）

拿 ch14 的 IndV1 證明（TypeOK ∧ NoDoublePay ∧ DedupCovers），在紙上改寫成 TLAPS 風格的骨架：定理宣告、起點義務、SUFFICES 開場、逐動作 CASE、每步的 BY 與 DEF 清單、各層 QED。不要求語法逐字合規（量詞怎麼拆成 CASE 的細節可以含糊），要求：層級結構完整、每個葉步驟的彈藥指認得出來、stuttering 案不漏。提示：Credit 案照 ch14 的 ⟨3⟩1–⟨3⟩7 搬，想清楚每個 ⟨3⟩ 步的 BY 該列誰。

### 推演解答

骨架（紙上版；真要餵 tlapm 還得打磨量詞與 vars 元組的寫法，但層級與彈藥就是這份）：

```tla
THEOREM Spec => []IndV1
<1>1. Init => IndV1
  BY DEF Init, IndV1, TypeOK, NoDoublePay, DedupCovers
<1>2. IndV1 /\ [Next]_vars => IndV1'
  <2>. SUFFICES ASSUME IndV1, [Next]_vars PROVE IndV1'
    OBVIOUS
  <2>. USE DEF IndV1, TypeOK, NoDoublePay, DedupCovers
  <2>1. ASSUME NEW c \in Consumers, NEW m \in Msgs, Fetch(c, m)
        PROVE  IndV1'
    BY <2>1 DEF Fetch, vars
  <2>2. ASSUME NEW c \in Consumers, Credit(c) PROVE IndV1'
    <3>1. working[c] \in Msgs
      BY <2>2 DEF Credit          \* guard 排除 "idle"，TypeOK 給值域
    <3>2. ledger[working[c]] = 0
      BY <2>2 DEF Credit          \* guard: notin dedup ＋ DedupCovers
    <3>3. ledger'[working[c]] = 1
      BY <3>2, <2>2 DEF Credit    \* EXCEPT 0 + 1
    <3>4. \A mt \in Msgs : mt # working[c] =>
            ledger'[mt] = ledger[mt] /\ (mt \notin dedup' => mt \notin dedup)
      BY <2>2 DEF Credit          \* EXCEPT 單格；dedup 只變大
    <3>. QED  BY <3>1, <3>2, <3>3, <3>4
  <2>3. ASSUME NEW c \in Consumers, Ack(c) PROVE IndV1'
    BY <2>3 DEF Ack
  <2>4. ASSUME NEW c \in Consumers, Crash(c) PROVE IndV1'
    BY <2>4 DEF Crash
  <2>5. CASE UNCHANGED vars
    BY <2>5 DEF vars
  <2>. QED  BY <2>1, <2>2, <2>3, <2>4, <2>5 DEF Next
<1>3. QED  BY <1>1, <1>2, PTL DEF Spec
```

對帳重點：（i）⟨2⟩5 的 stuttering 案必須在——ch14 的「豁免條款」是修辭，機器要的是案例。（ii）Credit 案的 ⟨3⟩2 是整份證明的承重點，它的 BY 清單裡 `<2>2`（guard）與 DedupCovers（經 USE 注入）缺一不可——這正是 ch14 第一輪卡死、強化後「債有人還了」的那一步，機器版的還債就是這行 BY。（iii）Fetch、Ack、Crash 一行收掉，理由跟手寫版相同：兩條承重條款只談 ledger 與 dedup，這三個動作不動它們——但「不動」也要 DEF 展開動作定義讓後端親眼看見。

### 題 2：三條義務，三種胃口（[15 分鐘] ★★）

下列三條 proof obligation 分別交給 TLAPS 的預設後端鏈，哪條最容易、哪條會逼你拆步驟、哪條三個自動後端可能全啞？說出理由（提示：回想各後端的胃口——SMT 怕量詞、Zenon 不懂算術、歸納模式要 Isabelle 或手動展開）。

- (a) 已知 ledger[m₀] = 0 與 TypeOK，證 ledger′ = [ledger EXCEPT ![m₀] = @ + 1] 之後 ledger′[m₀] ≤ 1。
- (b) 已知 IndTP 與 TMCommit 的 guard 和效果，證 ∀ r ∈ RM : rmState′[r] ∈ {"prepared", "committed"}（即 ch14 ⟨2⟩6 的 I7′ 步）。
- (c) 證對所有 n ∈ ℕ：0 + 1 + ⋯ + n = n(n+1)/2（ch05 的開場定理）。

### 推演解答

(a) **SMT 的甜蜜點，一行過。**函數單格更新加小算術（0 + 1 ≤ 1），沒有量詞嵌套——這正是 DieHard ⟨4⟩3 那型義務。
(b) **會逼你拆。**斷言本身帶 ∀，推理還要串四條條款（I4 → I5 → I6 → I3 的鏈，ch14 ⟨2⟩6 ⟨3⟩3 的四節車廂）——量詞加多步串接是 SMT 的弱項；Zenon 吃量詞但這裡混著集合與記錄的雜活。實務解法不是換後端，是把 ch14 手寫的 ⟨4⟩1–⟨4⟩5 直接搬成 TLAPS 子層：每節車廂一條小義務，節節皆綠。手寫時的好結構就是機器時代的好結構——這題是本章「接軌」的全部意義。
(c) **自動後端基本全啞，因為它需要歸納。**SMT 與 Zenon 都不會自己發明歸納假設；這類目標要嘛點名 Isabelle 後端碰運氣，要嘛在 TLA+ 裡引用自然數歸納規則手動展開層級（基底一義務、歸納步一義務）。「歸納這個動作本身」永遠是人的決定——ch05 教的那把刀，機器只替你磨，不替你揮。

### 題 3：把 ch14 的假證明餵給機器（[15 分鐘] ★★）

ch14 那位同事的 StrongInd ≜ NoDoublePay ∧ dedup = Msgs，配上他「義務二全空洞通過、義務三第一個合取項」的證明。（a）把這份證明寫成 TLAPS 骨架餵給 tlapm，哪條義務翻紅？紅燈訊息會指向哪個具體事實？（b）反過來：如果他狡猾地把定理只寫成 `THEOREM StrongInd /\ [Next]_vars => StrongInd'`，tlapm 會給全綠嗎？這個全綠值多少錢？

### 推演解答

（a）翻紅的是**起點義務** `Init => StrongInd`：Init 給 dedup = {}，StrongInd 要 dedup = Msgs，而 ASSUME 說 Msgs 非空——後端輕鬆找到矛盾，紅燈直指 dedup = Msgs 這個合取項。注意機器的判決跟 ch14 的人工驗屍完全一致（義務一不成立，整份作廢），但快得多、而且不會被「封閉全綠」的氣勢唬住：義務彼此獨立，一條紅就是紅。三義務是串聯保險絲——機器把每顆保險絲分開測。

（b）**會全綠，而且這個全綠一文不值。**那條定理本身是真的（空洞地真：StrongInd 的世界裡 Credit 永不 enabled，封閉確實成立）——機器忠實地證明了你交給它的句子。但 Spec ⇒ □NoDoublePay 從來沒被主張過：少了起點義務與 PTL 收尾，□ 根本沒出場。這是陷阱表第二條的現場：**機器不會替你想你沒交的義務**。自我防衛只有一招：每次慶祝全綠之前，回頭核對定理的形狀是不是 `Spec => []...`——字據上少一個 □，整張白簽。

## 自我檢核

口頭回答，講得出來才算過：

1. proof obligation 是什麼？tlapm 把一份層級證明變成什麼東西的集合？「CI required checks」這個類比在哪裡成立、在哪裡會誤導你？
2. BY、DEF、OBVIOUS、SUFFICES、CASE 各自的語意是什麼？TLAPS 預設不展開定義——這個設計跟 ch14 的「彈藥清單只有四樣、逐步指認」是什麼關係？
3. 後端的預設嘗試順序是什麼？三位的胃口各是什麼？「SMT 搞不定就拆步驟」的工作迴圈，分診那一步為什麼要先請 TLC／Apalache 出場？
4. DieHard 證明的 `<2>7. CASE UNCHANGED` 對應你手寫證明裡的哪句話？為什麼機器不接受「全章豁免」？
5. 兩份精讀證明的最後一行都是 `BY ... PTL DEF Spec`——PTL 後端在那一步執行的推理，你在哪一章親手證過？
6. Apalache 的兩段式歸納檢查各對應 ch14 三義務的哪條？它的綠燈與 TLAPS 的綠燈，各自承諾到哪裡為止？
7. Lean 4、Rocq、Isabelle 各用一句話定位，並各說一個代表作。三者中誰跟 TLAPS 有直接的管線關係？
8. 嚴謹度光譜五格，每格買到什麼、付出什麼？你自己的結算 pipeline 該停在哪格——用決策表的判準說出理由。

## 延伸閱讀

- **DieHard_proof.tla（tlaplus/Examples）**：<https://github.com/tlaplus/Examples/blob/master/specifications/DieHard/DieHard_proof.tla> — 本章精讀的原檔，全文 81 行（2026-06 開頁下載，引文逐字一致）。讀完本章再通讀一次全檔，BigToSmall 那個對稱案是現成的自我測驗。
- **Consensus.tla（tlaplus/Examples）**：<https://github.com/tlaplus/Examples/blob/master/specifications/Paxos/Consensus.tla> — ch12 鉤子的本尊（2026-06 開頁核對）。Invariance 是最小的不變量證明範本；LivenessTheorem 是 WF1 規則的機器版，對照 ch14 的三份作業讀。
- **Denis Cousineau, Damien Doligez, Leslie Lamport, Stephan Merz 等, “TLA+ Proofs”（FM 2012）**：<https://lamport.azurewebsites.net/pubs/tlaps.pdf> — 證明語言的設計論文（2026-06 連結可達）：為什麼是層級、為什麼宣告式（證明寫「什麼成立」而不是「按哪個鍵」）、義務怎麼生成。讀 §2–3 就夠。
- **TLAPS 官網與 tlapm repo**：<https://proofs.tlapl.us/> 與 <https://github.com/tlaplus/tlapm>（2026-06 開頁）— 文件、教學與原始碼；後端組成與預設策略的權威出處。本書不裝工具，但哪天你想動手，入口在這裡。
- **Apalache 手冊〈Running the Tool〉**：<https://apalache-mc.org/docs/apalache/running.html> — bounded model checking 與兩段式歸納檢查的官方說明（2026-06 開頁核對指令與措辭）；ch14 引用過，配合本章的原理段重讀。
- **Leslie Lamport, “Proving Safety Properties”（2019）**：<https://lamport.azurewebsites.net/tla/proving-safety.pdf> — ch14 已列；現在你有了 TLAPS 的讀法，它的第 4–6 節（從手寫不變量到逐步餵進 TLAPS）會從「預告」變成「操作手冊」。手寫與機器之間最好的一座橋。
