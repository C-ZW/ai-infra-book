# ch08 — 完整的 spec：從 DieHard 到結算系統 v1

> **本章解決什麼問題**：ch06 給了你動作與 Init ∧ □[Next]_vars，ch07 補上時序性質與 fairness——但你目前看到的都是去掉包裝的邏輯本體。本章補上包裝：一份完整的 .tla 檔由哪些固定部位組成、各部位回答什麼問題，讓你拿到任何一份沒看過的中小型 spec 都知道從哪讀起。然後做兩件事：精讀 Lamport 的 DieHard，學會「把目標寫成 invariant 的否定、讓反例變成解」這記招式；再把結算系統升級到 v1——讓 crash 與 redelivery 真正進場、用 dedup 表守住 `NoDoublePay`。v1 是後面三章的地基：ch09 算它的狀態空間、ch14 證它、ch15 拿它做 refinement。

## 從你已知的出發

打開一個陌生的 repo，你不會從第一行讀到最後一行。你有一套固定的尋路順序：先看 `package.json` 知道它叫什麼、依賴什麼；看環境變數與設定檔知道有哪些可調參數；看 entities 或 schema 知道狀態長什麼樣；看 handlers 知道系統會做哪些事；最後看測試與文件，知道作者「主張」這個系統保證什麼。順序爛熟於心，所以再陌生的專案你都有地圖。

一份完整的 TLA+ spec 也有這樣的固定部位，而且少得多——十個左右，一頁就放得下。本章第一件事就是把這張地圖立起來：MODULE 是名字、EXTENDS 是依賴、CONSTANTS ＋ ASSUME 是設定檔與設定檢查、VARIABLES ＋ TypeOK 是 schema、Init/Next/Spec 是行為本體、THEOREM 是作者的主張清單。之後你讀任何 spec——包括 Part IV 那四個經典協議——都用同一套尋路順序。

第二件事是精讀一份麻雀雖小五臟俱全的真 spec：DieHard。它把一道你大概在白板面試見過的題目——用 3 加侖與 5 加侖兩個沒有刻度的水壺量出恰好 4 加侖——寫成狀態機，然後耍了一記漂亮的招式：把「量出 4 加侖」這個**目標**寫成一條 invariant 的**否定**，讓模型檢查器去「打破」它；打破的那條反例 trace，就是解題步驟。你做過幾乎一樣的事：想確認某個壞狀態到底能不能發生，你不是盯著程式碼想，而是想辦法**逼它重現**——重現的步驟一旦到手，問題就從玄學變成工單。

第三件事回到你的主場。v0 的結算系統活在童話裡：consumer 不會掛、入帳與確認黏成原子的一步。你的真實世界不是這樣——SQS 是 at-least-once，consumer 會在任何一行程式碼之間被 OOM kill，而你之所以睡得著，是因為入帳交易裡有那張 idempotency key 表。本章把這三樣現實——crash、redelivery、dedup 表——正式寫進 spec。v1 大概三十行，但它就是你維護過的那條 pipeline 的骨架。

## spec 解剖學：一份 .tla 檔的固定部位

把一份典型的完整 spec 從上往下拆開：

| 部位 | 回答什麼問題 | 後端對應物 |
|---|---|---|
| `---- MODULE Name ----` | 這份 spec 叫什麼（模組名必須與檔名一致） | repo 名 |
| `EXTENDS` | 用到哪些標準模組的算子 | import 依賴 |
| `CONSTANTS` | 哪些參數先declare、不寫死 | 環境變數／設定檔 |
| `ASSUME` | 參數必須滿足什麼，違反就拒絕開工 | 設定檔的 schema validation |
| `VARIABLES` | 狀態由哪些變數組成 | DB schema 的表名 |
| `TypeOK` | 每個變數的值域 | 欄位型別＋約束 |
| `Init` | 合法的起點 | seed／初始 migration |
| 各具名 action 與 `Next` | 系統允許哪些步 | handlers |
| `Spec ≜ Init ∧ □[Next]_vars` | 整個系統的一條公式 | 入口點 |
| `THEOREM` | 作者主張這個 spec 滿足什麼 | 文件裡的保證、SLA 條款 |

幾個部位值得多說兩句。

**EXTENDS**。TLA+ 的世界觀是一切皆集合（見 ch04），徹底到連自然數的算術都不是語言內建——`+`、`−`、`..` 這些算子住在標準模組 `Naturals` 裡，要用就得 `EXTENDS Naturals`。忘了寫，spec 裡的 `big + small` 直接是未定義符號。

**CONSTANTS 與 ASSUME**。ch06 的 v0 把 `Msgs` 與 `Consumers` 寫死成兩個具體集合，那是教學上的偷懶。正規做法是宣告成 CONSTANTS——spec 對「任何」訊息集合與 consumer 集合成立，具體代入哪組值是檢查模型時才決定的事（ch09 會看到 TLC 怎麼吃這些參數；本書紙上代入即可）。而參數一旦開放，就得立規矩：ASSUME 寫下常數必須滿足的條件，學 learntla 的說法，它在模型開跑之前就先檢查。這是你寫了無數次的「啟動時驗 config」：與其讓一個空的 consumer 集合讓所有性質空洞地成立（ch03 的 vacuous truth），不如在門口擋下。

**模組裝飾**。模組內偶爾出現一整行 `-----`，那是純視覺的分隔線，沒有語意；檔案最後一行 `====`，之後的內容一律被忽略——有些人拿那個區域當筆記本。

**THEOREM**。這是最容易被誤會的部位：`THEOREM Spec => []Inv` 只是把作者的**主張**記錄在案，寫下它不會讓任何事情變成真的。TLC 可以在有限參數下檢查它（ch09）、TLAPS 可以逼你交出證明（ch16），但 THEOREM 這行字本身只是立了一張字據。讀 spec 時它的價值是導航：作者自己最在乎的性質是哪幾條，一目瞭然。

## TypeOK：為什麼它幾乎總是第一個 invariant

TLA+ 是**無型別**的語言。`VARIABLES queue, working, ledger` 只宣告了名字；沒有任何地方強迫 queue 是集合、ledger 是函數。型別不是宣告出來的，是你**主張**出來的——主張的慣用形式，就是一條叫 TypeOK 的狀態述語（慣例名，不是關鍵字）：每個變數的值落在預期的集合裡。

它幾乎總是 spec 的第一個 invariant，理由有四層：

1. **它是 schema 文件。** 讀陌生 spec 的第一站永遠是 TypeOK——先知道每個變數裝什麼形狀的值，再去讀動作，就像先看 schema 再讀查詢。DieHard 的原文註解把這件事說得很直白：型別不變量「不是規格的一部分，但放進來幾乎總是好主意，因為它幫讀者理解 spec」。
2. **它是最便宜的煙霧偵測器。** ch06 題 1 解答裡那條錯路——手滑用了 primed 變數、把字串 `"idle"` 塞進佇列——逐行盯動作不一定看得出來，但 TypeOK 的 `queue ⊆ Msgs` 一步現形。DieHard 原文接著說：讓 TLC 檢查它，抓到的錯誤正是「有型別的語言裡由 type checking 抓的那類」。
3. **後面的推理全靠它墊底。** ch14 的歸納不變量幾乎總是 TypeOK ∧ 其他條款的形狀——歸納步要推「ledger[m] + 1 還是數字」「queue ∖ {m} 還是 Msgs 的子集」，沒有 TypeOK 連這些最低限度的話都說不出口。
4. **它自己也是要驗的。** TypeOK 是 invariant，不是公理：它必須被檢查（ch09）或被證明（ch14），而且通常它本身就 inductive——這讓它成為練習 ch05 三個義務的最佳起手式。

一個現在就要立的紀律，後面 v1 會再回來敲打：**TypeOK 只准寫「值的形狀」，不准寫「動作規則掙來的秩序」**。把 ledger 的值域寫成 0..1，等於把 `NoDoublePay` 走私進型別——這條線怎麼分、踩過界會發生什麼，陷阱表見。

## DieHard 精讀：把救命題交給檢查器

材料來自 GitHub 的 tlaplus/Examples repo（原文連結見延伸閱讀；以下引用皆為 ASCII 原文，2026-06 對照）。spec 開頭的註解先把問題與企圖講完：電影《終極警探 3》（原文稱 Die Hard 3）裡，主角必須用一個 5 加侖壺、一個 3 加侖壺和一個水龍頭量出恰好 4 加侖的水。原文的下一句是整份 spec 的靈魂：「Our goal: to get TLC to solve the problem for us.」——目標不是驗證，是**讓檢查器替我們解題**。

從頭讀起。模組頭、依賴、變數：

```tla
------------------------------ MODULE DieHard -------------------------------
EXTENDS Naturals

VARIABLES big,   \* The number of gallons of water in the 5 gallon jug.
          small  \* The number of gallons of water in the 3 gallon jug.
```

`\*` 是行註解。兩個變數：big 是 5 加侖壺裡的水量、small 是 3 加侖壺的。接著就是 TypeOK——你的尋路順序第一站：

```tla
TypeOK == /\ small \in 0..3
          /\ big   \in 0..5
```

值域一出來，型別空間就可以心算：4 × 6 ＝ 24 種賦值組合。待會手畫狀態空間時拿它對帳。初始狀態：兩壺皆空。

```tla
Init == /\ big = 0
        /\ small = 0
```

動作分三類：從水龍頭灌滿一壺、把一壺倒光、一壺倒進另一壺。前兩類共四個動作：

```tla
FillSmallJug  == /\ small' = 3
                 /\ big' = big

FillBigJug    == /\ big' = 5
                 /\ small' = small

EmptySmallJug == /\ small' = 0
                 /\ big' = big

EmptyBigJug   == /\ big' = 0
                 /\ small' = small
```

注意兩件事。其一，**這些動作沒有 guard**——任何狀態下都 enabled。灌滿一個已滿的壺？合法，只是什麼都沒變：那一步的前後狀態相同，既滿足 FillSmallJug、也同時是 stuttering 步（[Next]_vars 的兩個 disjunct 本來就不互斥，ch06 的細節在這裡有了實例）。在狀態圖上這類步是自環，BFS 會自動忽略它們。其二，每個動作對兩個變數都交代了——這份 spec 不用 UNCHANGED，直接寫 `big' = big`，效果相同。

倒水的動作是全 spec 最漂亮的三行。先定義輔助算子 Min，然後：

```tla
Min(m,n) == IF m < n THEN m ELSE n

SmallToBig == /\ big'   = Min(big + small, 5)
              /\ small' = small - (big' - big)

BigToSmall == /\ small' = Min(big + small, 3)
              /\ big'   = big - (small' - small)
```

原文註解交代了建模決策：壺**沒有刻度**，所以倒水只有兩種有意義的結局——把目標壺倒滿，或把來源壺倒空。SmallToBig 的第一行說「big 的新值＝兩壺總量與 5 取小」；第二行說「small 把實際倒出去的量（big′ − big）扣掉」。看清楚第二行：**它在等式右邊引用了 big′**——另一個變數的新值。這在程式裡是先後順序問題，在這裡不是：合取沒有順序，兩條等式是同時成立的約束，求解的是「滿足這組方程的前後狀態對」（ch06「方程式不是賦值」的最佳實例）。順手驗一下守恆：兩條等式相加，small′ + big′ = small + big——水不會憑空增減，模型自己保證。

收尾三件套：

```tla
Next ==  \/ FillSmallJug
         \/ FillBigJug
         \/ EmptySmallJug
         \/ EmptyBigJug
         \/ SmallToBig
         \/ BigToSmall

Spec == Init /\ [][Next]_<<big, small>>
```

六個動作的析取、一條你已經會逐字念的公式（見 ch06）。然後是那記招式。spec 在分隔線之後定義：

```tla
NotSolved == big # 4
```

「未解」：big 不等於 4。原文註解把玩法說破：把 NotSolved 當作 invariant 交給 TLC 檢查。如果它真的是 invariant——所有可達狀態 big 都不是 4——那這道題**無解**。如果不是，TLC 會「失敗」，並印出一條以 big = 4 的狀態收尾的反例 trace——而那條 trace 就是解題步驟。原文最後一句話是 ch09 的預告：「Because TLC uses a breadth-first search, it will find the shortest solution.」BFS 找到的反例是最短的，所以你拿到的不只是解，是**最短解**。

把這招提煉出來：**反例是中性的機器產物，好壞由 invariant 的立場決定。**寫 `NoDoublePay` 時你站在 invariant 那邊，反例＝事故報告；寫 NotSolved 時你故意站在反面，反例＝攻略。同一台機器，兩種用法。你在生產環境其實兩種都做過：前者是「證明這個壞狀態到不了」，後者是「給我一條重現路徑」。

還有一個方向上的細節，誤會的人很多：這招回答的是**可能性**（存在一條路走到 big = 4），不是**必然性**（所有行為終將走到）。□[Next]_vars 是允許清單，從不承諾英雄真的會照著走——他們大可以把兩個壺灌滿倒掉灌滿倒掉直到炸彈倒數歸零。「終將解出」是 liveness，要 fairness 才有（見 ch07）。幸好電影只需要存在一條路，而且他們找到了。

## 全狀態空間手畫＋手找最短解（worked example）

機器怎麼解是 ch09 的事；本章先用手把 TLC 的工作完整做一遍。狀態記作 (small, big)，從 (0, 0) 出發做廣度優先窮舉：每層把所有新狀態的六個動作逐一算出落點，落點若是沒見過的狀態就編進下一層。

**第 0 層**：(0,0)。六個動作算一輪：FillSmallJug → (3,0) 新；FillBigJug → (0,5) 新；EmptySmallJug、EmptyBigJug、SmallToBig、BigToSmall 全是自環（兩壺皆空，倒無可倒）。

**第 1 層**：(3,0)、(0,5)。
- (3,0)：FillBigJug → (3,5) 新；SmallToBig → big′ = Min(3, 5) = 3、small′ = 3 − 3 = 0，即 (0,3) 新；EmptySmallJug → (0,0) 舊；其餘自環。
- (0,5)：FillSmallJug → (3,5) 已列；BigToSmall → small′ = Min(5, 3) = 3、big′ = 5 − 3 = 2，即 (3,2) 新；EmptyBigJug → (0,0) 舊；其餘自環。

**第 2 層**：(3,5)、(0,3)、(3,2)。
- (3,5)：四個非自環動作的落點 (0,5)、(3,0) 全是舊面孔，沒有新貨。
- (0,3)：FillSmallJug → (3,3) 新；BigToSmall → small′ = Min(3, 3) = 3、big′ = 0，即 (3,0) 舊；FillBigJug → (0,5) 舊；EmptyBigJug → (0,0) 舊。
- (3,2)：EmptySmallJug → (0,2) 新；SmallToBig → big′ = Min(5, 5) = 5、small′ = 3 − 3 = 0，即 (0,5) 舊；FillBigJug → (3,5) 舊；EmptyBigJug → (3,0) 舊。

**第 3 層**：(3,3)、(0,2)。
- (3,3)：SmallToBig → big′ = Min(6, 5) = 5、small′ = 3 − 2 = 1，即 (1,5) 新；其餘落點皆舊。
- (0,2)：BigToSmall → small′ = Min(2, 3) = 2、big′ = 0，即 (2,0) 新；FillSmallJug → (3,2) 舊；其餘舊。

**第 4 層**：(1,5)、(2,0)。
- (1,5)：EmptyBigJug → (1,0) 新；BigToSmall → small′ = Min(6, 3) = 3、big′ = 5 − 2 = 3，即 (3,3) 舊；其餘舊。
- (2,0)：FillBigJug → (2,5) 新；SmallToBig → (0,2) 舊；其餘舊。

**第 5 層**：(1,0)、(2,5)。
- (1,0)：SmallToBig → big′ = Min(1, 5) = 1、small′ = 0，即 (0,1) 新；其餘舊。
- (2,5)：**BigToSmall → small′ = Min(7, 3) = 3、big′ = 5 − (3 − 2) = 4，即 (3,4) 新——big = 4，目標出現在第 6 層。**EmptyBigJug → (2,0) 舊；其餘舊。

TLC 做到這裡就會停：NotSolved 被打破，印 trace。我們為了畫完整張地圖，繼續：

**第 6 層**：(0,1)、(3,4)。(0,1) 給出 FillSmallJug → (3,1) 新；(3,4) 給出 EmptySmallJug → (0,4) 新（以及 SmallToBig → (2,5) 舊）。

**第 7 層**：(3,1)、(0,4)。兩者的所有落點——(3,5)、(0,1)、(3,0)、(0,4)、(3,4)、(0,5)、(0,0)、(3,1)——全是舊面孔。**沒有第 8 層，窮舉收斂。**

可達狀態共 **16 個**。畫成地圖（Lk ＝ BFS 第 k 層首次發現）：

```text
          big=0   big=1   big=2   big=3   big=4   big=5
         +-------+-------+-------+-------+-------+-------+
 small=0 |  L0 * |  L6   |  L3   |  L2   |  L7 ! |  L1   |
 small=1 |  L5   |   x   |   x   |   x   |   x   |  L4   |
 small=2 |  L4   |   x   |   x   |   x   |   x   |  L5   |
 small=3 |  L1   |  L7   |  L2   |  L3   |  L6 ! |  L2   |
         +-------+-------+-------+-------+-------+-------+
```

（* ＝初始狀態；! ＝ big = 4 的目標狀態；x ＝型別空間內、不可達。）

封閉性檢查照 ch02 的紀律做：對 16 個狀態逐一列出六個動作的落點，確認全部落回清單內（「＝」表示自環）：

| (small, big) | 層 | FillS | FillB | EmptyS | EmptyB | SmallToBig | BigToSmall |
|---|---|---|---|---|---|---|---|
| (0,0) | L0 | (3,0) | (0,5) | ＝ | ＝ | ＝ | ＝ |
| (3,0) | L1 | ＝ | (3,5) | (0,0) | ＝ | (0,3) | ＝ |
| (0,5) | L1 | (3,5) | ＝ | ＝ | (0,0) | ＝ | (3,2) |
| (3,5) | L2 | ＝ | ＝ | (0,5) | (3,0) | ＝ | ＝ |
| (0,3) | L2 | (3,3) | (0,5) | ＝ | (0,0) | ＝ | (3,0) |
| (3,2) | L2 | ＝ | (3,5) | (0,2) | (3,0) | (0,5) | ＝ |
| (3,3) | L3 | ＝ | (3,5) | (0,3) | (3,0) | (1,5) | ＝ |
| (0,2) | L3 | (3,2) | (0,5) | ＝ | (0,0) | ＝ | (2,0) |
| (1,5) | L4 | (3,5) | ＝ | (0,5) | (1,0) | ＝ | (3,3) |
| (2,0) | L4 | (3,0) | (2,5) | (0,0) | ＝ | (0,2) | ＝ |
| (1,0) | L5 | (3,0) | (1,5) | (0,0) | ＝ | (0,1) | ＝ |
| (2,5) | L5 | (3,5) | ＝ | (0,5) | (2,0) | ＝ | **(3,4)** |
| (0,1) | L6 | (3,1) | (0,5) | ＝ | (0,0) | ＝ | (1,0) |
| (3,4) | L6 | ＝ | (3,5) | (0,4) | (3,0) | (2,5) | ＝ |
| (3,1) | L7 | ＝ | (3,5) | (0,1) | (3,0) | (0,4) | ＝ |
| (0,4) | L7 | (3,4) | (0,5) | ＝ | (0,0) | ＝ | (3,1) |

96 個落點全數命中清單，封閉 ✓。16 就是全部。

**型別空間 24、可達 16，缺的 8 格為什麼恰好是那 8 格？**看 x 的分布：{1, 2} × {1, 2, 3, 4}——兩壺都「不空也不滿」的組合，一個都到不了。理由可以從動作直接讀出來：六個動作每一個結束時**至少有一壺處在校準點**（空或滿）——灌滿與倒光自不必說，倒水則「不是把目標倒滿、就是把來源倒空」。沒有刻度的壺，只有靠空與滿這兩個校準點丈量世界；「small ∈ {0, 3} ∨ big ∈ {0, 5}」就是這台狀態機掙來的秩序，一條你現在有能力證的 inductive invariant（見 ch05 的三個義務；這裡不展開）。

**手找最短解。**big = 4 的可達狀態有兩個：(3,4) 在第 6 層、(0,4) 在第 7 層——所以最短解是 6 步，終點 (3,4)。路徑從發現過程倒著讀回去：(3,4) 由 (2,5) 的 BigToSmall 而來、(2,5) 由 (2,0) 的 FillBigJug 而來……一路回溯到 (0,0)。逐步驗算：

| 步 | 動作 | 驗算 | 落點 (small, big) |
|---|---|---|---|
| 0 | — | Init：兩壺皆空 | (0, 0) |
| 1 | FillBigJug | big′ = 5，small 不動 | (0, 5) |
| 2 | BigToSmall | small′ = Min(5, 3) = 3；big′ = 5 − (3 − 0) = 2 | (3, 2) |
| 3 | EmptySmallJug | small′ = 0，big 不動 | (0, 2) |
| 4 | BigToSmall | small′ = Min(2, 3) = 2；big′ = 2 − (2 − 0) = 0 | (2, 0) |
| 5 | FillBigJug | big′ = 5，small 不動 | (2, 5) |
| 6 | BigToSmall | small′ = Min(7, 3) = 3；big′ = 5 − (3 − 2) = **4** | (3, 4) |

第 6 步之後 NotSolved 為假——這條 trace 就是 TLC 會交給你的「錯誤」，也是電影主角的活命步驟。

加碼一個 BFS 才給得起的結論：**這條最短解是唯一的。**從邊表逐層回推前驅——指向 (3,4) 的只有 (2,5)（L5）與 (0,4)（L7），最短路只能經 (2,5)；指向 (2,5) 的只有 (2,0)（L4）與 (3,4)；指向 (2,0) 的只有 (0,2)（L3）與 (2,5)；指向 (0,2) 的只有 (3,2)（L2）與 (2,0)；指向 (3,2) 的只有 (0,5)（L1）與 (0,2)；而 (0,5) 在第 0 層的前驅只有 (0,0)。每一層的選擇都是被迫的：六步解不只最短，還是唯一的六步解。

## PlusCal：你只需要讀得懂

讀真實世界的 spec，你遲早會撞見另一種長相：`.tla` 檔的註解區塊裡躺著一段像 Pascal 或 C 的程式，下面跟著一段機器生成的 TLA+。那是 **PlusCal**——一種寫在註解裡的演算法語言，由翻譯器轉成 TLA+ 之後才能餵給工具。先把本書的立場說死：**你不需要會寫 PlusCal，只需要看到它不慌**。理由是本書 Part IV 要精讀的經典 spec（TwoPhase、Paxos、raft.tla）都以原生 TLA+ 寫成，力氣花在刀口上。但工業界用它用得很兇——AWS 那篇 CACM 2015 論文的 Table 1 裡，S3 容錯網路演算法的 spec 是 804 行 PlusCal，作者之一 Fan Zhang 的自述是她寫 PlusCal 比寫 TLA+ 更有生產力（2015 時點，見 ch17）——所以「讀得懂」有實際價值。

PlusCal 有兩種等價語法：P-syntax（類 Pascal，`begin…end`）與 C-syntax（大括號），Lamport 為兩種各寫了一本使用手冊（連結見延伸閱讀，2026-06 查證有效）。同一個語言、兩層皮，讀哪種都一樣。下面用 P-syntax 給你唯一需要的對照例——一個單 consumer 的迷你結算迴圈：

```tla
(* --algorithm settle_one
variables queue = {"m1", "m2"},
          done  = {},
          cur   = "idle";
begin
Loop:
  while queue # {} do
    Fetch:
      with m \in queue do
        queue := queue \ {m};
        cur := m;
      end with;
    Credit:
      done := done \union {cur};
      cur := "idle";
  end while;
end algorithm *)
```

整段住在 `(* … *)` 註解裡；`:=` 是賦值、`while` 是迴圈、`with m \in queue` 是「從佇列裡挑一個」——讀起來就是程式。關鍵是那三個帶冒號的標籤 `Loop:`、`Fetch:`、`Credit:`。**標籤是原子性的立法**：同一個標籤底下的所有語句在一步之內同時發生，步與步的切換只發生在標籤邊界。learntla 的說法一針見血：「Labels represent everything that can happen in a single step of the system.」

翻譯器把它轉成的 TLA+ 大致如下（節錄重排；實際輸出的排版與輔助定義依版本而異）：

```tla
VARIABLES queue, done, cur, pc

vars == <<queue, done, cur, pc>>

Init == /\ queue = {"m1", "m2"}
        /\ done = {}
        /\ cur = "idle"
        /\ pc = "Loop"

Loop == /\ pc = "Loop"
        /\ IF queue # {} THEN pc' = "Fetch" ELSE pc' = "Done"
        /\ UNCHANGED <<queue, done, cur>>

Fetch == /\ pc = "Fetch"
         /\ \E m \in queue : /\ queue' = queue \ {m}
                             /\ cur' = m
         /\ pc' = "Credit"
         /\ done' = done

Credit == /\ pc = "Credit"
          /\ done' = done \union {cur}
          /\ cur' = "idle"
          /\ pc' = "Loop"
          /\ queue' = queue

Next == Loop \/ Fetch \/ Credit
          \/ (pc = "Done" /\ UNCHANGED vars)

Spec == Init /\ [][Next]_vars
```

讀懂這份翻譯需要三個觀察，之後在野外遇到任何 PlusCal 生成物都通用：

1. **pc 變數**。ch02 說過：程式計數器沒有特殊地位，要的話自己宣告成變數——這就是了。pc 記錄「執行到哪個標籤」，值域是標籤名加上終態 `"Done"`。控制流被物化成資料，於是「程式」徹底變回狀態機。
2. **一個標籤＝一個 action**。每個動作的第一個合取是 `pc = "標籤名"`（guard），最後一個合取把 pc′ 設成下一個標籤——順序執行被編譯成狀態轉移。`with` 變成了 ∃：非決定性的選擇，跟你在 ch06 看到的同一句型。
3. **末尾的免責 disjunct**。`pc = "Done" ∧ UNCHANGED vars` 允許終止後原地踏步——翻譯器的慣例，讓「做完了」不被誤判成卡死。

現在回頭看標籤的份量。Fetch 與 Credit 是兩個標籤，所以「取走訊息」與「記帳」之間**存在一條步的縫**——如果有第二個 process，它可以插隊；如果有 crash，它可以發生在縫裡。把兩段合併進同一個標籤，縫就消失，世界回到 v0 的童話。**標籤切太粗，race 就在 spec 裡不存在**——這是 PlusCal 最大的陷阱：原子性的立法藏在標籤位置這種不起眼的地方，而你 review 的眼睛習慣性略過它。下一節在原生 TLA+ 裡做的事——把 Settle 拆成兩個動作——本質上就是「把一個標籤拆成兩個」。

## 結算系統 v1：讓故障進場

債務清單先攤開。ch02 說 v0「不會 crash、不會重送」是童話，並承諾 v1 還債；ch05 證完 `NoDoublePay` 之後點名了兩個欠著的原子性假設；ch06 寫 v0 spec 時把 Fetch 與 Settle 之間標成「ch08 的施工點」。現在施工。

**v0 在哪裡說謊。**你的 consumer 真實程式碼是兩步：先在一筆 DB 交易裡入帳（連同寫入 idempotency key），交易 commit 之後才呼叫 DeleteMessage 把訊息從佇列刪掉。v0 的 `Settle(c)` 把這兩步黏成原子的一步——於是「入帳成功之後、刪訊息之前 crash」這個 double-pay 的經典開局，在 v0 裡**連寫都寫不出來**。模型表達不出的失敗，性質的成立就有一半是盲區（ch02 的老話）。

**所以 v1 的第一刀：把 Settle 拆成 Credit 與 Ack。**設計理由有三條，每條都站得住：

1. **現實對應**：Credit ＝ 那筆 DB 交易（入帳＋寫 dedup key，原子 commit）；Ack ＝ DeleteMessage。你的程式碼本來就是這兩步，v0 才是說謊的那個。
2. **方法論**：要讓危險的 crash 存在於模型，crash 必須有縫可鑽——縫只能用「拆成兩個動作」造出來。拆完之後，dedup 表才有真正的工作可做；不拆，它就是擺設。
3. **ch15 的伏筆**：在抽象的 exactly-once 規格眼裡，v1 的兩步只有一步「算數」、另一步會映成 stuttering——ch06 你接受的 stuttering 條款，就是在等這種時刻（一句話預告，正戲在 ch15）。

**第二刀：讓 crash 進場。**`Crash(c)`：手上有訊息的 consumer 隨時可能死掉，它手上的訊息回到佇列（佇列服務沒等到 ack，visibility timeout 到期後重新投遞——v1 把「crash、超時、重投遞」壓成一步，這筆抽象帳下一節算）。閒著的 consumer 也會 crash，但對這三個變數毫無影響——那種步是 stuttering，spec 不必列（允許清單只列觀察得到的事，ch06）。

**第三刀：dedup 表。**新變數 `dedup`：已入帳訊息的 id 集合——你那張 idempotency key 表的數學形狀。防線位置是個真實的設計決策：guard 放在 **Credit**，不放在 Fetch。理由跟你生產環境一模一樣：佇列照常投遞重複訊息（那不歸你管），冪等檢查活在 consumer 的入帳交易裡；而且若擋在 Fetch，已入帳的重複訊息將永遠無人領取、佇列永不清空——現實中你也必須先 receive 才能 delete。於是 Ack 自然長出第二種劇本：手上的訊息已在 dedup 裡（不論是自己剛入的帳、還是別人入過的），直接確認丟棄。**正常完成與重複丟棄共用同一個 Ack**——你的 idempotent consumer 正是這樣寫的。

最後一個必須誠實交代的變更：**ledger 的型別從布林演進成計數**。ch05 已經把問題挑明：布林帳本上「再入帳一次」只是把 TRUE 蓋寫成 TRUE，狀態上看不出差別——在 v0 那是個可以接受的簡化，在 v1 卻會讓 double-pay 變成**不可觀察**的事件，整章白忙。所以 v1 的 ledger[m] 記「m 被入帳的次數」，`NoDoublePay` 終於可以用它的本意陳述：每則訊息至多入帳一次。變數名、動作名、哨兵值全部沿用 v0（queue、working、ledger、Fetch、`"idle"`），這不是潔癖：ch09、ch14、ch15 都要在這份 spec 上施工，命名漂移會讓三章的對帳全部斷裂。

完整模組如下——這也是你在本書看到的第一份「解剖學十個部位齊全」的 spec：

```tla
---------------------------- MODULE SettlementV1 ----------------------------
EXTENDS Naturals

CONSTANTS Msgs, Consumers

ASSUME /\ Msgs # {}
       /\ Consumers # {}
       /\ "idle" \notin Msgs

VARIABLES queue, working, ledger, dedup

vars == <<queue, working, ledger, dedup>>

TypeOK == /\ queue \subseteq Msgs
          /\ working \in [Consumers -> Msgs \cup {"idle"}]
          /\ ledger \in [Msgs -> Nat]
          /\ dedup \subseteq Msgs

Init == /\ queue = Msgs
        /\ working = [c \in Consumers |-> "idle"]
        /\ ledger = [m \in Msgs |-> 0]
        /\ dedup = {}

Fetch(c, m) == /\ working[c] = "idle"
               /\ m \in queue
               /\ queue' = queue \ {m}
               /\ working' = [working EXCEPT ![c] = m]
               /\ UNCHANGED <<ledger, dedup>>

Credit(c) == /\ working[c] # "idle"
             /\ working[c] \notin dedup
             /\ ledger' = [ledger EXCEPT ![working[c]] = @ + 1]
             /\ dedup' = dedup \cup {working[c]}
             /\ UNCHANGED <<queue, working>>

Ack(c) == /\ working[c] # "idle"
          /\ working[c] \in dedup
          /\ working' = [working EXCEPT ![c] = "idle"]
          /\ UNCHANGED <<queue, ledger, dedup>>

Crash(c) == /\ working[c] # "idle"
            /\ queue' = queue \cup {working[c]}
            /\ working' = [working EXCEPT ![c] = "idle"]
            /\ UNCHANGED <<ledger, dedup>>

Next == \E c \in Consumers : \/ \E m \in Msgs : Fetch(c, m)
                             \/ Credit(c)
                             \/ Ack(c)
                             \/ Crash(c)

Spec == Init /\ [][Next]_vars

NoDoublePay == \A m \in Msgs : ledger[m] <= 1

THEOREM Spec => []TypeOK
THEOREM Spec => []NoDoublePay
==============================================================================
```

逐部位讀，新東西優先：

- **CONSTANTS ＋ ASSUME**：參數開放了；三條 ASSUME 各有名目——兩個非空條件擋掉 vacuous 的世界，`"idle" ∉ Msgs` 擋的是**哨兵撞名**：若有訊息恰好叫 `"idle"`，`working[c] # "idle"` 這類 guard 全面歧義，整份 spec 安靜地壞掉。基準配置（ch02 起沿用）是代入 Msgs = {"m1", "m2"}、Consumers = {"c1", "c2"}。
- **TypeOK**：注意 `ledger ∈ [Msgs -> Nat]`——值域是整個 Nat，不是 0..1。型別空間因此是無限的，但可達空間有限；「有限」不是型別的功勞，是 dedup 守出來的秩序（ch09 拿這句話當主場）。為什麼不直接寫 0..1？陷阱表算帳。
- **Fetch**：與 ch06 的 v0 一字不差（多一行 UNCHANGED dedup）。
- **Credit**：兩個 guard——手上有訊息、且該訊息不在 dedup 裡；效果是 ledger 對應格加一、dedup 收編該訊息，**同一步完成**。`@` 是 EXCEPT 句型裡「舊值」的縮寫：`[ledger EXCEPT ![working[c]] = @ + 1]` 讀作「ledger 只有 working[c] 那格改成舊值加一」。dedup 寫入與入帳的原子性對應你的「同一筆 DB 交易」——這個假設極度承重，下一節單獨算帳。
- **Ack**：guard 是手上的訊息**已在** dedup 裡。對照 Credit 的 guard，兩者恰好互補：手持訊息的 consumer，要嘛還沒入帳（走 Credit）、要嘛已入帳（走 Ack），不會卡死。也注意 Ack 擋掉了「沒入帳就確認」——那是把 at-least-once 做成 at-most-once 的掉件事故，v1 把它立法為不可能（consumer 程式碼是我們寫的，這條法我們立得起；對比 Crash 的 guard 就不行，見下）。
- **Crash**：guard 只有 `working[c] # "idle"`——**它不准引用 ledger 或 dedup**。crash 的「執行者」是死神加佇列服務，它們看不到你的 DB；guard 只能用執行者觀察得到的資訊，這是寫故障動作的鐵律（違反它會發生什麼，紙上推演題 4 領教）。
- **THEOREM ×2**：作者主張。TLC 在基準參數下可以檢查（ch09）；真正的證明欠到 ch14——先說結論免得你懸著：`NoDoublePay` 成立，關鍵是 dedup 只進不出、而 Credit 的 guard 拿它當門票。

每則訊息的一生，畫成圖（Q ＝在佇列；H0 ＝被某 consumer 手持、尚未入帳；H1 ＝被手持、已入帳；OUT ＝已確認、徹底離開系統）：

```text
        Fetch(c, m)        Credit(c)         Ack(c)
   Q ---------------> H0 -------------> H1 ------------> OUT
   ^                  |                 |
   |     Crash(c)     |                 |
   +------------------+                 |
   ^              Crash(c)              |
   +------------------------------------+
```

左邊的 Crash 迴圈無害：沒入帳的訊息回佇列重來，頂多多繞幾圈。**右邊那條邊是整章的主角**：已入帳的訊息回到佇列。走過這條邊之後再次被 Fetch，會直接落在 H1（dedup 認得它），唯一的出路是 Ack 丟棄。把這條危險路徑完整追一遍（基準配置，只追 m1；working 縮寫成 (c1 的值, c2 的值)，ledger 縮寫成 (m1 的值, m2 的值)）：

| 狀態 | 動作 | queue | working | ledger | dedup |
|---|---|---|---|---|---|
| s₀ | — | {m1, m2} | (idle, idle) | (0, 0) | {} |
| s₁ | Fetch(c1, m1) | {m2} | (m1, idle) | (0, 0) | {} |
| s₂ | Credit(c1) | {m2} | (m1, idle) | (1, 0) | {m1} |
| s₃ | **Crash(c1)** | {m1, m2} | (idle, idle) | (1, 0) | {m1} |
| s₄ | Fetch(c2, m1) | {m2} | (idle, m1) | (1, 0) | {m1} |
| s₅ | Ack(c2) | {m2} | (idle, idle) | (1, 0) | {m1} |

s₂ → s₃ 就是任務書上的那行字：**crash 發生在入帳之後、確認之前**——m1 帶著「已入帳」的事實回到佇列。s₄ 站在懸崖邊：c2 手持 m1，若它能 Credit，ledger[m1] 就變 2。驗 guard：working[c2] = m1 ∈ dedup —— **Credit(c2) 不 enabled**，唯一能走的是 Ack(c2)。dedup 表在這一步擋下了 double pay；s₅ 之後 m1 徹底離開系統，m2 的人生照常進行。

反事實對照，一刀見血：把 Credit 的第二個 guard `working[c] \notin dedup` 刪掉（叫它 BadCredit 的 v1 變體），上表走到 s₄ 後 Credit(c2) enabled，走一步——ledger[m1] = 2，`NoDoublePay` 陣亡。這條路徑就是一條如假包換的反例 trace（讀法訓練在 ch09——TLC 實際印出的那條未必是它）。同一條路徑，在 DieHard 那邊反例是攻略、在這邊反例是事故報告——你現在兩種立場都站過了。

順帶記下兩個此刻就看得出來的事實，留給後面章節收割。其一：v0 版的 `NoDoublePay` 寫法（已入帳 ⇒ 不在佇列、不在任何手上）在 v1 是**假的**——s₃ 就是反例（ledger[m1] = 1 且 m1 ∈ queue）。這不是性質壞了，是系統真的變了：v1 的世界裡「已入帳的訊息暫時還在系統裡晃」是合法日常，我們守的從來就不是「它消失」，而是「它不再被入帳」。性質的寫法必須跟著系統的誠實度演進。其二：v1 沒有任何 fairness 條款，所以「每則訊息終將入帳」（`AllPaid`，見 ch07）不成立——Fetch–Crash 鬼打牆到天荒地老是合法行為。v1 刻意只承諾 safety；liveness 的帳本書在 ch07 已經教你怎麼記。

## v1 抽象掉了哪些現實

照 ch02 立的規矩，每筆省略白紙黑字記帳：

| 被抽象掉的現實 | 模型裡的長相 | 後果與還債 |
|---|---|---|
| crash → 超時 → 重投遞是三件隔著時間的事 | Crash 一步完成「死亡＋訊息回佇列」 | 問不了任何 timeout 調校問題；本書不建模時間，不還 |
| crash 後 consumer 有 down time | crash 完立刻能接新訊息（K8s 自動重啟的極限簡化） | consumer 池固定不縮，狀態空間因此小很多；不還 |
| 活著的 consumer 處理太慢、visibility timeout 到期重投遞 | 不存在——訊息要回佇列只有 crash 一途，且任何時刻每則訊息在系統裡至多一份 | 「兩個 consumer 同時手持同一訊息」的劇本不在 v1 裡。緩解：`NoDoublePay` 的防線只靠 dedup 的單調性與 Credit 的 guard，不依賴「至多一份」——把慢消費者加回來，防線設計不必動（ch14 的證明骨架也是）。要建模它得把佇列換成 bag（ch04 吵過的帳） |
| dedup 檢查、寫 key、入帳是一筆 DB 交易 | Credit 一步原子完成三件事 | **全 spec 最承重的假設**。現實裡若先查再寫、不在同一交易，ch01 的 race 原樣回歸。這個假設對應你程式裡的唯一鍵＋交易，模型只是把你的設計決定寫成數學；哪天你的實作改用「先 SELECT 再 INSERT」，這份 spec 對你的系統就**失效** |
| dedup 表會被 TTL／歸檔清理 | dedup 只進不出 | 現實的事故形狀：TTL 短於最大重投遞窗口，老訊息復活時 key 已被清掉。模型裡 Msgs 有限、表永存免費；生產環境這是一條真實的值班教訓 |
| 佇列服務本身會丟訊息、會自行複製訊息 | 佇列忠實保管，重投遞只由 Crash 觸發 | 佇列服務的正確性是別人的定理；我們 ASSUME 它。要驗它，得寫它自己的 spec |
| 金額、訊息內容、順序、毒訊息／DLQ | 不存在 | 同 ch02 的帳，不再贅述 |

讀這張表的正確姿勢不是「模型好假」，而是 ch02 教的那句：模型是針對特定問題的證詞。v1 的問題是「at-least-once 之下 dedup 擋不擋得住 double pay」——對這個問題，上表每一筆省略都不傷證詞效力，**除了**第四筆：Credit 的原子性不是簡化，是**前提**。你的系統若不滿足它，v1 證得再漂亮都與你無關。這就是 Murphy 原則的形式化版在 spec 層的長相：寫 spec 逼你把「我的安全感建立在哪個假設上」一個字一個字寫出來。

## 陷阱與防禦

| 故障模式 | 它怎麼騙你 | 防禦 |
|---|---|---|
| TypeOK 走私定理 | 把 ledger 的值域寫成 0..1——`NoDoublePay` 被塞進「型別」，TLC 檢查 TypeOK 等於檢查性質，你以為它天生成立、從此沒人證它 | TypeOK 只寫宣告層面的值形狀；凡是要靠動作規則才守得住的範圍，都是 invariant 不是型別。自測法：這條範圍是「值的定義」還是「掙來的秩序」？後者搬出去 |
| 常數沒立 ASSUME | Consumers 代入空集合：沒有任何動作 enabled，全部 safety 性質 vacuous 全綠；或訊息恰好叫 "idle"，guard 全面歧義 | 每個 CONSTANTS 配一條 ASSUME；問「最惡劣的合法代入是什麼」。空集合與哨兵撞名是兩個必問 |
| 反招的極性搞反 | 用 DieHard 招式時，invariant 被打破是**好**消息；你習慣性看到綠燈就放心——其實綠燈＝無解（或你的 Next 漏了動作，把目標弄成不可達） | 用反招時在 spec 註解明寫立場；對每個綠燈問一句：這是「證明了安全」，還是「證明了我到不了」？ |
| 故障動作的 guard 偷看不該看的資訊 | Crash 的 guard 引用 ledger 或 dedup（「入帳後就不會 crash」）——模型替現實讀心，危險路徑被貼心地堵死，dedup 防線從未受考驗就全綠 | 鐵律：guard 只能用該動作執行者觀察得到的資訊。佇列服務看不到你的 DB；死神誰都看得到。逐個故障動作審一遍 guard 的「視力」 |
| PlusCal 標籤切太粗 | 現實中可被打斷的兩段操作住在同一個標籤，race 在 spec 裡不存在——v0 的原子 Settle 就是這個病的原生 TLA+ 版 | 對每個標籤（每個 action）問：現實裡這中間能不能插人、能不能 crash？能，就拆。原子性是立法，不是預設 |
| 把「反例＝解」推成「spec 保證會解出」 | BFS 找到一條到 big = 4 的路，你說「系統會達成目標」——□[Next]_vars 從不承諾任何路被走 | 區分 ∃ behavior（可能性，反例給的）與 ∀ behavior（必然性，invariant／liveness 主張的）。「終將」二字出現就去找 fairness（見 ch07） |

## 紙上推演

### 題 1：BFS 地圖的剩餘價值（[10 分鐘] ★）

用 worked example 的層級表與邊表回答：

(a) 想在**大壺**裡量出恰好 1 加侖，最少幾步？寫出該寫給檢查器的「目標反轉」invariant 與一條最短路徑。

(b) 「兩壺合計恰好 4 加侖」的可達狀態有哪些？最少幾步達成？

### 推演解答

(a) invariant 寫 big ≠ 1（ASCII：`big # 1`）。big = 1 的可達狀態只有 (0,1)（L6）與 (3,1)（L7），所以最少 **6 步**。回溯第 6 層的發現路徑：(0,0) →FillSmallJug→ (3,0) →SmallToBig→ (0,3) →FillSmallJug→ (3,3) →SmallToBig→ (1,5) →EmptyBigJug→ (1,0) →SmallToBig→ (0,1)。注意這條解全程沒用到 BigToSmall——跟量 4 加侖那條解恰好是「鏡像策略」（一條反覆用小壺餵大壺、一條反覆用大壺餵小壺）。

(b) small + big = 4 在型別空間有四個格子：(0,4)、(1,3)、(2,2)、(3,1)。查地圖：(1,3) 與 (2,2) 落在不可達區（兩壺皆不空不滿），可達的只有 **(0,4)（L7）與 (3,1)（L7）**——最少 **7 步**。invariant 寫 `small + big # 4`。這題的弦外之音：同一句白話「量出 4 加侖」可以指 big = 4（6 步）也可以指合計 4（7 步）——目標寫成形式述語的那一刻，歧義就死了。這就是「寫 spec 的最大價值是先想清楚」的微縮版（見 ch01）。

### 題 2：讀一份沒看過的 spec（[15 分鐘] ★★）

不查任何資料，讀懂下面這份完整 spec 並回答四個問題：

```tla
------------------------------- MODULE Slots --------------------------------
EXTENDS Naturals

CONSTANTS N

ASSUME N \in Nat \ {0}

VARIABLES free, held

vars == <<free, held>>

TypeOK == /\ free \in 0..N
          /\ held \in 0..N

Init == /\ free = N
        /\ held = 0

Acquire == /\ free > 0
           /\ free' = free - 1
           /\ held' = held + 1

Release == /\ held > 0
           /\ held' = held - 1
           /\ free' = free + 1

Next == Acquire \/ Release

Spec == Init /\ [][Next]_vars
==============================================================================
```

(a) 它在建模你生產環境裡的什麼東西？(b) 把 ASSUME 拿掉、代入 N = 0 會發生什麼？哪裡最陰？(c) free + held = N 是 invariant 嗎？是 inductive 嗎（口頭走 ch05 的三個義務）？(d) 這份 Spec 保證「想 Acquire 的人終究拿得到」嗎？

### 推演解答

(a) 一個容量 N 的資源池——DB connection pool、semaphore、限流的 token bucket（不補充的版本）都是它。free 是池裡剩的、held 是被借走的。

(b) N = 0 時 Init 給 free = held = 0，Acquire 與 Release 的 guard 雙雙永遠為假——系統只剩 stuttering。最陰的不是報錯，是**不報錯**：所有 safety 性質對這個只會原地踏步的系統全部成立，全綠。你以為驗過了池子的行為，其實驗了一座空城（ch03 的 vacuous truth、ch02 的性質空洞成立，同一隻鬼）。這就是 ASSUME 的工作：把「合法但無意義」的參數擋在門外。

(c) 是，而且是 inductive。三個義務：起點——N + 0 = N ✓；封閉——Acquire 一減一加、Release 一加一減，和都不動 ✓（兩個 case 蓋住 Next）；蘊涵——目標就是自己 ✓。順帶看出 TypeOK 的上界其實是這條守恆撐住的：free ≤ N 不是型別天生，是 free + held = N ∧ held ≥ 0 的推論——但寫在 TypeOK 裡的 `free ∈ 0..N` 沒有走私，因為 0..N 確實是 free 的合理值域宣告，秩序與型別在這題剛好重疊（對照陷阱表第 1 條，分界感覺一下）。

(d) 不保證。□[Next]_vars 是允許清單：free > 0 時 Acquire enabled，但 behavior 可以永遠只走 Release 或原地踏步。「等得到」是 liveness，要 fairness（見 ch07）。讀任何 spec 的最後一問永遠是：它承諾的是「不出事」還是「會發生」——這份只有前者。

### 題 3：幫 PlusCal 翻譯補 TypeOK（[15 分鐘] ★★）

本章 PlusCal 一節的翻譯產物（settle_one）沒有 TypeOK。補一條，四個變數都要交代；然後回答：「cur ≠ "idle" 時 pc 必不是 "Loop"」這句話該不該寫進 TypeOK？

### 推演解答

```tla
TypeOK == /\ queue \subseteq {"m1", "m2"}
          /\ done \subseteq {"m1", "m2"}
          /\ cur \in {"m1", "m2", "idle"}
          /\ pc \in {"Loop", "Fetch", "Credit", "Done"}
```

要點三個。其一，pc 的值域＝標籤集 ∪ {"Done"}——拿到任何 PlusCal 翻譯，pc 的型別照這個公式抄。其二，cur 的值域要記得收哨兵 "idle"——漏了它，TypeOK 在 Init 就破，這種「第 0 步就紅」的錯反而是好事，秒級定位。其三，`queue ⊆ S` 與 `queue ∈ SUBSET S` 是同一句話的兩種寫法（ch04 的冪集），讀 spec 兩種都會遇到。

至於「cur ≠ "idle" 時 pc 必不是 "Loop"」：這句話為真（cur 只在 Fetch 後非 idle、在 Credit 末尾歸位），但它是**動作規則掙來的秩序**，不是值的形狀——寫進 TypeOK 就是陷阱表第 1 條的走私。它該去的地方是一條獨立的 invariant（而且 ch14 你會發現：證 done 相關性質時，正是這類「pc 與資料的綁定」要被強化進歸納不變量——PlusCal 翻譯物的證明幾乎總是繞著 pc 轉）。

### 題 4：spec 與白話需求的不一致（[25 分鐘] ★★★）

白話需求四條：

1. consumer 隨時可能 crash；
2. crash 的 consumer 手上的訊息會被佇列服務重新投遞；
3. 同一 msgId 至多入帳一次；
4. 已重複投遞的訊息由 consumer 端冪等處理。

同事據此交出一份 v1 的變體，與本章 v1 唯一的差異是 Crash 多了一個 guard：

```tla
Crash(c) == /\ working[c] # "idle"
            /\ working[c] \notin dedup
            /\ queue' = queue \cup {working[c]}
            /\ working' = [working EXCEPT ![c] = "idle"]
            /\ UNCHANGED <<ledger, dedup>>
```

他的說法：「入帳都做完了，這時候 crash 也沒什麼好建模的，加個 guard 讓模型小一點。」TLC 在基準參數下檢查 `NoDoublePay`：全綠。指出 spec 與需求的不一致、說明那個綠燈為什麼幾乎不值錢，並給出修正與自我察覺的方法。

### 推演解答

**不一致在需求 1**：「隨時可能 crash」被改成了「只在還沒入帳時 crash」。這個 guard 引用了 dedup——但 crash 的執行者（死神、OOM killer、preemption）看不到你的 DB，憑什麼挑時機？陷阱表第 4 條的鐵律被踩穿：guard 用了執行者觀察不到的資訊，模型在替現實讀心。

**綠燈為什麼不值錢**：加了這個 guard，「入帳之後、確認之前」的 crash 不可能發生，已入帳的訊息**永遠**不會回到佇列。推下去：m ∈ queue ∧ m ∈ dedup 不可達，於是 Credit 的 dedup guard 從未真正擋下任何一步、Ack 的「重複丟棄」劇本從未上演——整條 dedup 防線在這個模型裡是**從未承壓的劇場道具**。`NoDoublePay` 確實全綠，但成立的理由是「危險被定義掉了」，不是「防線擋住了危險」。這正是 ch02 那句話的工程版：性質成立，有時只因為你的模型說不出那種失敗。哪天有人把 dedup 表的寫入弄壞，這份 spec 一聲不吭。

**修正**：刪掉 `working[c] \notin dedup` 那行，回到本章的 Crash。代價是狀態空間變大——這是誠實的價格，照付。

**自我察覺**：兩個習慣。一，對每個防禦機制（這裡是 Credit 的 dedup guard）手構一條讓它「真的擋下一步」的 trace——構不出來，防線就是道具（本章 s₀…s₅ 那條 trace 就是 dedup 的承壓證明）。二，review 故障動作時逐字審 guard：每多一個 conjunct 就問「這個資訊，故障發生的那一方拿得到嗎」。故障動作的 guard 越乾淨，模型越誠實——你巴不得 crash 無條件 enabled，因為現實裡它就是。

## 自我檢核

口頭回答，講得出來才算過：

1. spec 解剖學的十個部位各回答什麼問題？拿到一份陌生的 .tla，你的前三站是哪裡、為什麼？
2. TypeOK 為什麼幾乎總是第一個 invariant？它與 ASSUME 的分工是什麼（提示：一個管變數、一個管常數）？「ledger ∈ [Msgs → 0..1]」為什麼是走私？
3. DieHard 的招式是什麼？為什麼 BFS 的反例自動是最短解？這招回答「可能性」還是「必然性」——差別在哪個量詞上？
4. v0 的 Settle 為什麼必須拆成 Credit 與 Ack？crash 必須能插在哪兩步之間，double-pay 的風險才真實存在？
5. v1 的 `NoDoublePay` 為什麼從「已入帳 ⇒ 徹底離開系統」改寫成 ledger[m] ≤ 1？v0 的舊寫法在 v1 的哪個可達狀態上陣亡？
6. dedup 的 guard 為什麼放在 Credit 而不是 Fetch？Ack 的兩種劇本（正常完成、重複丟棄）為什麼能共用同一個動作？
7. PlusCal 的標籤立的是什麼法？pc 變數是誰生出來的、值域怎麼讀？「標籤切太粗」對應 v0 的哪個謊言？
8. `THEOREM Spec => []NoDoublePay` 這行字「說」了什麼、「沒說」什麼？要讓它從主張變成事實，你有哪兩條路、各在哪一章？

## 延伸閱讀

- **DieHard.tla 原文**：`https://github.com/tlaplus/Examples/blob/master/specifications/DieHard/DieHard.tla`——本章所有引文的出處，註解比程式碼多三倍，Lamport 式教學的標本；同目錄的 DieHarder.tla 把壺的數量與容量推廣成 CONSTANTS，讀完本章正好接得住（連結驗證於 2026-06）。
- **TLA+ Video Course, Lecture 4 “Die Hard”**：`https://lamport.azurewebsites.net/video/videos.html`——本章精讀的影片版，Lamport 親自把這份 spec 餵給 TLC、看反例變成解；課程自述「We save the lives of two Hollywood action heroes.」（連結與講次驗證於 2026-06）。
- **Specifying Systems**（Lamport, 2002），免費 PDF：`https://lamport.azurewebsites.net/tla/book.html`——第一部分（第 1–7 章）是 spec 結構慣例的原典；本章解剖學那張表的每一格，那裡都有 Lamport 自己的辯護。
- **A PlusCal User's Manual**：P-syntax 版 `https://lamport.azurewebsites.net/tla/p-manual.pdf`、C-syntax 版 `https://lamport.azurewebsites.net/tla/c-manual.pdf`——讀前幾節就夠「看得懂」；兩份手冊對照翻兩頁，你就知道兩種語法真的只是換皮（連結驗證於 2026-06）。
- **learntla.com 的 PlusCal 一章**（Hillel Wayne）：`https://learntla.com/core/pluscal.html`——標籤＝原子性這件事講得最清楚的教材；它走的是「先 PlusCal 後 TLA+」的路線，與本書相反，正好當對照組（連結驗證於 2026-06）。
