# ch12 — 交叉注意力與三種注意力

> **本章解決什麼問題**：到 ch11 為止，我們的 query、key、value 一直來自**同一個序列**——每個 token 既是查詢者也是被查者（self-attention）。但 ch03 那個 Bahdanau 的翻譯場景明明是「目標句的詞去看來源句」，那是**跨兩個序列**的查找，我們一直沒正式回去補。本章把這個洞補上：原始 Transformer 其實同時用了**三種**注意力——encoder self、decoder masked-self、encoder-decoder cross——差別只在「誰當 query、誰當 key/value、能不能看未來」。看懂它你就掌握了 attention 全部的接線方式，也會看到脊椎那個 it 在這裡升級成翻譯場景：脊椎矩陣第一次從 3×3 方陣變成「目標×源」的矩形。三步骨架一個字都沒變——只是換了 query 和 key/value 的來源。

## 從你已知的出發

你天天在做兩種查找，只是平常不會把它們分開命名。

第一種：**self-JOIN**。同一張表，把每一列拿去跟同一張表的其他列比對——找出「同一筆訂單裡互相關聯的明細」「同一個 session 裡前後相關的事件」。query 和被查的資料來自**同一張表**。這正是 ch07 講的 self-attention：序列裡每個 token 對同一序列的所有 token 算相似度。

第二種：**跨表 JOIN**。你拿 A 表的某一列當查詢條件，去 B 表裡找匹配的列——`orders JOIN users ON orders.user_id = users.id`。查詢的人在 A 表，被查的資料在 B 表，**兩張不同的表**。這就是本章主角 **cross-attention**：query 來自一個序列，key/value 來自**另一個**序列。

```text
self-attention  ≈  self-JOIN   （同一張表，列對列）
cross-attention ≈  cross-JOIN  （A 表的列去查 B 表）
```

而 ch11 的 causal mask，是在 self-JOIN 上再加一條權限規則：**你只能 JOIN 到時間戳記比你早的列**（append-only log，讀不到未來）。

所以原始 Transformer 用的「三種注意力」，本質就是三種「誰查誰、能查到哪」的組合——像你給不同的查詢配不同的權限：

```text
                  query 來源     key/value 來源    能看未來嗎
─────────────────────────────────────────────────────────────
① encoder self     源序列自己      源序列自己         能（雙向，看全句）
② decoder self     目標序列自己    目標序列自己       不能（causal mask，只看左）
③ cross            目標序列        源序列            不適用（看遍整個源）
```

這張表就是本章的全部骨幹。三種注意力不是三個新機制——是同一個三步骨架（打分→正規化→加權混合），接到三種不同的輸入插座上。本章動的不是骨架的任何一步，而是**第一步打分的兩個輸入「query 從哪來、key/value 從哪來」的接線方式**。

## 先回到 ch03：Bahdanau 其實就是 cross-attention 的雛形

cross-attention 不是 Transformer 發明的新東西。你在 ch03 已經親手算過它，只是當時還沒給它這個名字。

ch03 的 Bahdanau 對齊（2014）做的是：decoder 在生成每個目標詞時，拿**當前的 decoder 狀態**去對 encoder 的**每一個源句隱態**算對齊分數，softmax 成權重，加權混合源句隱態，得到一個動態的 context 向量（2026-06 查證：這正是現代 cross-attention 的概念前身——decoder 的查詢去看 encoder 的隱態）。把它翻成 Q/K/V 的話：

```text
Bahdanau 2014（cross 的雛形）         Transformer cross-attention（2017）
─────────────────────────────        ─────────────────────────────────────
decoder 當前狀態  → 對齊分數的 query   decoder 該層輸出      → Q（學來的投影）
encoder 各隱態    → 被對齊的對象       encoder 輸出          → K（學來的投影）
encoder 各隱態    → 被加權混合的內容   encoder 輸出          → V（學來的投影）
加性評分 vᵀtanh(·) → 打分              縮放內積 QKᵀ/√d       → 打分
```

差別只有兩處，都是前面幾章補過的零件：① 打分從 Bahdanau 的加性小網路換成 ch04–06 的縮放內積；② Bahdanau 直接拿 RNN 隱態當 key/value，Transformer 多加了 W_Q/W_K/W_V 三個**學來的投影**（ch04）。**接線方式完全一樣**：目標端當 query，源端當 key/value。

所以你大可以把這一章當成「ch03 的正式版」。當年 Bahdanau 解決固定向量瓶頸（ch02）靠的就是 cross-attention 的雛形；Transformer 只是把它標準化、配上 self-attention 一起用。三步骨架在 ch03 第一次現身時，跑的其實就是一次 cross-attention——我們繞了一圈才正式給它命名。

## 三種注意力：逐一拆「誰查誰」

原始 Transformer（Vaswani 2017，§3.2.3，landscape §2 已錄）是一個 encoder-decoder 架構：左邊一疊 encoder 層讀源句（比如英文），右邊一疊 decoder 層生成目標句（比如中文）。在這個架構裡，注意力出現在**三個**位置，各司其職。

```text
   源句（英文）                          目標句（中文，逐字生成）
   ┌─────────────┐                       ┌──────────────────────┐
   │  ENCODER    │                       │      DECODER         │
   │             │                       │                      │
   │ ① self-attn │                       │ ② masked self-attn   │
   │  (雙向)     │── encoder 輸出 ──┐    │  (只看左邊，ch11)    │
   │             │      K, V        │    │                      │
   └─────────────┘                  └───►│ ③ cross-attn         │
                                     Q ──│  (Q 來自此處 ↑)      │
                                         │                      │
                                         └──────────────────────┘
```

### ① encoder self-attention（雙向，看全句）

encoder 在讀源句時，每個源 token 對**同一個源序列**的所有 token 做注意力——Q、K、V 同源（ch07 的 self-attention）。沒有 mask，是**雙向**的：英文 "animal" 這個位置可以同時看它左邊和右邊的詞，因為讀理解時整句都在手上、沒有「未來」這回事。這顆引擎的任務是把源句**理解透**：每個 token 吸收全句脈絡，產出一份「讀懂了的」表示。

### ② decoder masked self-attention（單向，只看左）

decoder 在生成目標句時，每個已生成的目標 token 也對**目標序列自己**做 self-attention——但加了 ch11 的 **causal mask**：生成第 i 個中文字時，只能看它左邊已經生成的 ≤i 個字，不能偷看還沒生成的未來（否則就作弊了，自迴歸生成的鐵律）。這顆引擎的任務是讓目標句**自己內部連貫**：已經寫出的詞要彼此呼應、語法通順。

### ③ encoder-decoder cross-attention（目標查源）

這是本章的主角，也是把兩個序列**接起來**的關鍵接點。在這一步：

```text
Q（查詢）   來自 decoder——「我這個目標位置，需要源句的什麼？」
K, V        來自 encoder 輸出——源句被讀懂後的那份表示
            「源句各位置標榜自己是什麼（K）／能交出什麼內容（V）」
```

每個 decoder 位置的 query，去對**整個源序列**的 key 打分、softmax、混合源序列的 value（landscape §2：「allows every position in the decoder to attend over all positions in the input」——目標端每個位置可看遍源端所有位置）。這就是翻譯時「目標詞回頭查源句哪幾個詞最相關」的那一步——和 ch03 Bahdanau 同一件事。

> 一個值得停一下的設計細節：cross-attention 這一步**沒有 causal mask**。為什麼？因為源句（要翻譯的英文）在生成開始前就**整句給定**了——它不是逐字生成的，沒有「未來」可偷看。目標端的 query 看遍**整個**源句是合法且必要的（你翻譯時當然要看完整句英文）。causal mask 只管「目標序列自己內部不能看未來」（②），不管「目標看源」（③）。這是 ch11「能不能看未來」那條規則在三種注意力裡的精確落點。

把三種注意力對回三步骨架，會看到一件讓人安心的事：**三步骨架一個字都沒變**。打分都是縮放內積、正規化都是 softmax、混合都是加權平均 value。變的只是第一步打分的**兩個輸入插在哪**：

```text
                打分的 query 插座    打分的 key/value 插座
─────────────────────────────────────────────────────────
① encoder self      源序列              源序列            （同源、雙向）
② decoder self      目標序列            目標序列          （同源、masked）
③ cross             目標序列            源序列            （異源）★本章
```

這就是為什麼說「三種注意力」其實是同一個機制的三種接法。你已經會算 ① 和 ②（ch07、ch11）；本章只需把 ③ 的「Q 與 K/V 來自不同序列」這件事弄清楚、親手算一次。

## 脊椎升級：從 3×3 方陣到「目標×源」矩形

現在把脊椎那個 it 升級成翻譯場景，並且**明寫一個關鍵轉換**：注意力矩陣不再是方陣。

到 ch11 為止，脊椎一直是 3 個 token 的序列 [animal, street, it] 對自己做 self-attention，注意力矩陣是 **3×3 方陣**（每個 token 當 query，對三個 key 打分，每一列、每一欄都是同一批 token）。cross-attention 一來，這個方陣的前提就破了：

```text
self-attention（ch07–11）            cross-attention（本章）
   query ↓  key →                       query ↓   key →
        animal street it                     源_animal  源_street
 animal  ┌──┬──┬──┐                  目標_它 ┌────────┬─────────┐
 street  ├──┼──┼──┤   3×3 方陣               └────────┴─────────┘
 it      └──┴──┴──┘   （同一批 token       (1×2 矩形：1 個目標 query × 2 個源 key)
                       既當列又當欄）
```

**為什麼變矩形？** 因為 query 來自目標序列、key 來自源序列，**兩個序列的長度可以完全不同**。一句 5 個詞的英文翻成 8 個字的中文，注意力矩陣就是 8×5——8 個目標位置（列）對 5 個源位置（欄）。它不再是方陣，所以你**不能再套 self-attention 那些「對角線是自己」的直覺**（ch04 講過 self-attention 裡每個 token 對自己的分數、ch11 的因果遮罩是對上三角設 −∞）——矩形矩陣根本沒有「對角線＝自己」這回事，因為列和欄是兩批不同的 token。這是脊椎在全書第一次離開方陣，務必記住這個形狀的改變。

具體把脊椎翻成翻譯場景：英文源句 "the animal didn't cross the street ..." 經 encoder 讀懂後，我們**只取兩個關鍵源 token 當 key/value**：animal 和 street（簡化，真實的源句有更多 token）。decoder 正在生成中文譯文，輪到生成那個對應 "it" 的代名詞——中文裡是「牠／它」（指代動物用「牠」）。這個目標位置產生一個 query，要去問源句：「我這個代名詞，該對齊源句的哪個詞？」

```text
源端（encoder 輸出，當 K/V）——只取兩個關鍵 token
  k_animal = (2, 1, 1, 0)      v_animal = (1, 0)
  k_street = (0, 1, 1, 0)      v_street = (0, 1)

目標端（decoder 當前位置「牠」，當 Q）
  q_它     = (1, 1, 1, 1)      ← 沿用脊椎 q_it 同一個查詢向量
```

我們刻意讓目標 query 用**和脊椎 q_it 完全相同**的向量 (1,1,1,1)，並且源端 key/value 直接借用脊椎裡 animal、street 那兩個（基準數字見 outline，全書同一組）。這樣你能清楚看到：**同一個查詢，在 cross 場景下因為「被查的對象變了」（少了 it 自己這個 key），結果會跟 ch07 self-attention 不一樣**——這正是下一節 worked example 要算的重點。

## Worked example：迷你翻譯的 cross-attention

跑完整的三步骨架，維度沿用全書單頭視角 d=4、√d=2。

**第一步：打分。** 目標 query「牠」對兩個源 key 做內積（只有兩個 key，因為源端只取了 animal、street）：

```text
q_它 · k_animal = (1)(2) + (1)(1) + (1)(1) + (1)(0) = 2+1+1+0 = 4
q_它 · k_street = (1)(0) + (1)(1) + (1)(1) + (1)(0) = 0+1+1+0 = 2
                                          原始 cross 分數 [animal 4, street 2]
```

注意：這兩個內積值 [4, 2] 和脊椎 self-attention 算出來的前兩項**一模一樣**——因為 query 和這兩個 key 都沒變。差別在**少了第三項** q_它·k_it（cross 場景下源端沒有 it 這個 key）。

**第二步：縮放 + 正規化。** 除以 √d = 2，再 softmax：

```text
[4, 2] / √d=2  →  [2, 1]          ← 縮放後分數

e² = 7.389
e¹ = 2.718
                和 = 7.389 + 2.718 = 10.107   ← 只有兩項！

softmax 權重：
  animal: 7.389 / 10.107 = 0.731
  street: 2.718 / 10.107 = 0.269
                                   cross 權重 [0.731, 0.269]（驗：和=1.000 ✓）
```

**這裡是本章最該停十分鐘的地方。** 把它和脊椎正典（ch06 宣告的 self-attention 縮放權重）並排：

```text
                  animal   street   it       softmax 的分母
─────────────────────────────────────────────────────────────
self  [2,1,0]     0.665    0.245    0.090    7.389+2.718+1=11.107（三項）
cross [2,1]       0.731    0.269     —        7.389+2.718  =10.107（兩項）
                  ↑        ↑        ↑
              都變大了             it 不在了
```

同一個 query、同樣的 animal/street 分數，cross 給 animal 的權重（0.731）卻比 self（0.665）**高**。為什麼？因為 softmax 的分母變了：self-attention 的分母含三項（11.107），cross 只含兩項（10.107，少了 it 貢獻的那個 e⁰=1）。**it 在 self 場景裡分走的 0.090 權重，在 cross 場景裡不存在了，於是被 animal 和 street 按比例瓜分回去**。

更精確地說：animal 對 street 的權重比，在兩個場景裡**完全相同**——都是 e²/e¹ = e ≈ 2.718（self：0.665/0.245≈2.72；cross：0.731/0.269≈2.72）。softmax 不改變參與者之間的相對比例，但**誰參與**會改變每個人分到的絕對份額。這就是「3×3 方陣」變「1×2 矩形」在數字上的直接後果——不是換了公式，是換了 softmax 求和的對象。

> **這裡了不起／反直覺在哪**：很多人以為「cross-attention 是個跟 self-attention 不同的新機制」。不是。它跑的是**字字相同的三步骨架**，連 query 向量、key 向量都可以一樣。唯一變的是「打分時 query 和 key 來自不同的序列、softmax 對不同的一群 key 求和」。看懂這點，你就不會被「self / masked-self / cross / encoder-decoder attention」這一堆名詞淹沒——它們是同一台引擎接到不同插座上。

**第三步：加權混合。** 用源端的 value（v_animal=(1,0)、v_street=(0,1)）：

```text
輸出 = 0.731·(1,0) + 0.269·(0,1)
     = (0.731, 0)  + (0, 0.269)
     = (0.731, 0.269)
                          cross-attn 輸出 ≈ (0.731, 0.269)
```

這個輸出向量偏向 v_animal 的方向（第一維 0.731 遠大於第二維 0.269），意思是：decoder 在生成中文代名詞時，從源句**主要拉取了 animal 的內容**——它「對齊」到了英文的 animal。這正是翻譯該有的行為：中文的「牠」對應英文裡的動物。ch01 那個懸念（it 該看 animal）在 cross 場景裡換了個樣子重新成立：**目標語言的代名詞，跨序列對齊回了源語言的正確指代對象**。

熱圖（單列，因為只有一個目標 query；█ 最濃、░ 最淡）：

```text
            源_animal   源_street
目標「牠」  ███████     ██▒          ← 主要對齊 animal，分一點給 street
```

對照 self-attention（ch07 的 3×3）那張「it 那一列在 animal 欄最濃」的熱圖，你會發現 cross 版本就是**抽掉了 it 那一欄、只剩源端兩欄的一條橫切**。形狀對得上，只是換了被查的對象。

## 一張小心心的對照：self 與 cross 並排

把整章濃縮成一次並排計算，幫你把「變的只是接線」這件事坐實：

```text
                self-attention（ch07）        cross-attention（本章）
─────────────────────────────────────────────────────────────────────
query           q_it（序列自己的 it 位置）     q_它（目標序列的代名詞）
key/value 來源  同一序列 [animal,street,it]    源序列 [animal,street]
打分            q·k 內積（縮放）              q·k 內積（縮放）── 一樣
參與 softmax    3 個 key                       2 個 key  ← 唯一的結構差別
縮放分數        [2, 1, 0]                      [2, 1]
權重            [0.665, 0.245, 0.090]          [0.731, 0.269]
輸出            (0.755, 0.335)                 (0.731, 0.269)
注意力矩陣形狀  3×3 方陣                       1×2 矩形（目標×源）
```

兩欄唯一的「機制差別」就是「key/value 來自哪個序列、有幾個」。其餘——內積、縮放、softmax、混合——逐字相同。這是本章想讓你帶走的一句話：**cross-attention 不是新公式，是新接線。**

## cross-attention 在多模態與生圖裡的角色（一瞥）

cross-attention 的威力不只在翻譯。它的本質是「**讓一個序列被另一個序列當作條件來查詢**」——只要你有「A 想根據 B 來決定怎麼做」的場景，cross-attention 就是那個接點。這在 2020 年後的多模態與生成模型裡成了標準零件（landscape §8，這裡一段帶過、深入指向延伸閱讀）：

- **文字控制生圖（Stable Diffusion / Latent Diffusion，Rombach 2021）**：在去噪 U-Net 的每個注意力塊插入 cross-attention，讓**影像的潛在特徵當 Q**、**文字提示的 token embedding 當 K/V**（2026-06 查證；原文：「by introducing cross-attention layers ... powerful and flexible generators for general conditioning inputs such as text」）。直覺：影像的每個空間區域「查詢」文字提示，問「我這塊該畫成什麼？」——這就是「a cat on a sofa」這串字怎麼鑽進像素裡的機制。query 是圖、key/value 是字，方向和翻譯時剛好可以反過來，但接線邏輯一模一樣。

- **視覺語言模型（Flamingo，DeepMind 2022）**：在凍結的語言模型層之間插入 **gated cross-attention** 層，讓**語言當 Q、視覺特徵當 K/V**（2026-06 查證），把圖片資訊注入文字生成。gated（門控）是為了初始化時不破壞原語言模型——一個工程細節，不展開。

- **對比學習對齊（CLIP，OpenAI 2021）**：嚴格說 CLIP 主要用各自的 self-attention encoder 再做對比，不是靠 cross-attention 融合；列在這裡是提醒你「多模態對齊」有不只一種做法，cross-attention 只是其中最直接的「把 B 當條件查詢」那一種。

共通的模式：**cross-attention ＝ 把外部條件（文字、圖片、任何另一個序列）當成一張可查的 key/value 表，讓主序列按相關度去拉取它需要的資訊**。翻譯是「目標句查源句」，生圖是「圖查文字」，VLM 是「文字查圖」——query 和 key/value 的身分換來換去，但三步骨架和「異源查找」這個核心，從頭到尾沒變。多模態與 diffusion 的機制深入不是本書範圍（一句＋延伸），但你現在知道它們的「注意力接點」長什麼樣了。

## 故障模式與直覺陷阱

| 直覺陷阱 / 故障 | 為什麼錯／在哪一步把你帶溝裡 | 怎麼自我察覺、正確版是什麼 |
|---|---|---|
| 「cross-attention 是跟 self 不同的新機制／新公式」 | 把名詞當成不同的東西。其實跑的是**字字相同的三步骨架**，只有打分的 query 與 key/value 來源不同。 | 默念對照表：內積、縮放、softmax、混合全一樣。問自己「公式哪一項變了？」——沒有，只是 Q 與 K/V 插在不同序列。 |
| 「cross-attention 的矩陣也是方陣，有對角線＝自己」 | 把 self 的方陣直覺硬套到 cross。cross 矩陣是「目標×源」**矩形**，列和欄是兩批不同 token，根本沒有「對角線＝自己」。 | 看形狀：源句 5 詞、目標 8 字 → 8×5。不是方陣，別找對角線，也別套 causal mask 的上三角直覺。 |
| 「cross-attention 也要 causal mask、不能看未來」 | 混淆了「目標看源」和「目標看自己」。源句整句給定、不是逐字生成，沒有未來可偷看，目標端看遍整個源是合法的。causal mask 只管 decoder **self**-attention（②）。 | 問自己「源句是逐字生成的嗎？」——不是，翻譯前整句英文就在手上。所以 cross 不遮，看遍全源。 |
| 「同一個 query，self 和 cross 的權重會一樣」 | 忽略了 softmax 的分母會因「參與的 key 變了」而改變。脊椎裡 it 一抽掉，animal 從 0.665 跳到 0.731。 | 記住：softmax 對「誰參與」敏感。少一個 key，它的權重會被其餘按比例瓜分。並排看 11.107 vs 10.107 的分母。 |
| 「cross-attention 是 Transformer 發明的」 | 忽略 ch03。Bahdanau 2014 的對齊就是 cross 的雛形（decoder query 看 encoder 隱態），Transformer 只是換上縮放內積與 W_Q/W_K/W_V。 | 回扣 ch03：你早就算過一次 cross-attention，只是當時叫「對齊」。Transformer 標準化了它。 |
| 「decoder-only 的 GPT 裡也有 cross-attention」 | 危險的過度推廣。今日主流的 decoder-only LLM（GPT 類）**沒有 encoder**，所以**沒有 encoder-decoder cross-attention**——它們只有 masked self-attention（②）。cross 主要活在 encoder-decoder 架構（T5、翻譯）與多模態注入裡。 | 問自己「這個模型有 encoder 嗎？」沒有 encoder 就沒有 ③。三種家族的差別留 ch13 細講，但這個陷阱現在就要避開。 |

最值得警惕的是**最後一個**。讀者很容易把「Transformer ＝ 三種注意力都有」當成普世真理，然後在 2026 年的 decoder-only 世界裡找不到 cross-attention 而困惑。事實是：原始 Transformer（2017，翻譯用）是 encoder-decoder，三種都有；但今日生成式 LLM 多是 decoder-only，**只有 masked self-attention**。cross-attention 在 LLM 主線裡退居幕後，卻在**多模態注入**（生圖、VLM）裡找到了新主場。哪種架構配哪些注意力，是 ch13 三種家族要正式攤開的。

## 紙上推演

### 推演題

**第 1 題 [12 分鐘]（★）** 把 self / masked-self / cross 三者做成對照表。三欄分別是：(a) query 來自哪個序列、(b) key/value 來自哪個序列、(c) 能不能看未來（要不要 causal mask）。填完後用一句話說：這三者**共用**的是什麼、**不同**的只有什麼？

**第 2 題 [15 分鐘]（★★）** 親手算一次 cross-attention，並和 self 對比。給目標 query q=(1,1,1,1)、源端兩個 key k_animal=(2,1,1,0)、k_street=(0,1,1,0)、value v_animal=(1,0)、v_street=(0,1)，d=4。(a) 算兩個內積分數；(b) 除以 √d 後 softmax（e²、e¹、求和、相除）；(c) 加權混合得輸出；(d) 把你算出的 animal 權重（0.731）和脊椎 self-attention 的 animal 權重（0.665）並排，解釋**為什麼 cross 版反而更高**（提示：看 softmax 的分母）。

**第 3 題 [10 分鐘]（★★）** 解釋 cross-attention 與 ch03 Bahdanau 的關係。不查書，用三到五句向另一個工程師說：Bahdanau 的對齊為什麼就是 cross-attention 的雛形？它和 Transformer 的 cross-attention 差在哪兩個零件（都是前面章節補的）？

**第 4 題 [8 分鐘]（★★）** 舉一個「cross-attention 注入條件」的應用並拆解它的 Q/K/V。以「用文字 a cat on a sofa 控制生圖」為例：(a) 誰當 query、誰當 key/value？(b) 用一句話說這一步在直覺上做什麼？(c) 這和翻譯時的 cross-attention 在「接線方向」上有什麼異同？

### 推演解答

**第 1 題。**

```text
              query 來源    key/value 來源   看未來？（causal mask）
─────────────────────────────────────────────────────────────────
self          源序列自己     源序列自己        能（雙向，encoder 用）
masked-self   目標序列自己   目標序列自己      不能（單向，decoder 用，ch11）
cross         目標序列       源序列           不適用（源整句給定，看遍全源）
```

**共用**的是三步骨架（打分＝縮放內積、正規化＝softmax、混合＝加權平均 value）——三者一字不差。**不同**的只有「打分時 query 與 key/value 插在哪個序列、softmax 對哪一群 key 求和、要不要遮未來」。一句話：同一台引擎，三種接線。常見錯路：把「不同」寫成「公式不同」——不對，公式相同，只有輸入來源與 mask 不同。

**第 2 題。**
(a) q·k_animal = 2+1+1+0 = **4**；q·k_street = 0+1+1+0 = **2**。原始分數 [4, 2]。
(b) 除 √d=2 → [2, 1]；e²=7.389、e¹=2.718，和 = 10.107；權重 = [7.389/10.107, 2.718/10.107] = **[0.731, 0.269]**（驗：和=1.000 ✓）。
(c) 輸出 = 0.731·(1,0)+0.269·(0,1) = **(0.731, 0.269)**，偏向 animal。
(d) cross 的 animal 權重 0.731 比 self 的 0.665 **高**，因為 softmax 的分母不同：self 含三項（e²+e¹+e⁰=11.107），cross 只含兩項（e²+e¹=10.107，少了 it 那個 e⁰=1）。self 場景裡 it 分走的 0.090 權重，在 cross 場景裡不存在，於是被 animal、street 按原比例（e²:e¹=e≈2.72）瓜分回去。核心：softmax 不改變參與者間的相對比例，但「誰參與」改變每個人的絕對份額。常見錯路：以為「同一個 query 就該得同一組權重」——錯，權重取決於它對**哪一群** key 做 softmax。

**第 3 題（要點）。** 一個說得通的版本：「Bahdanau 2014 在 decoder 生成每個目標詞時，拿 decoder 當前狀態當查詢，去對 encoder 的每個源句隱態算對齊分數、softmax、加權混合源隱態——這就是『目標端 query 看源端 key/value』，正是 cross-attention 的定義。它和 Transformer cross-attention 差在兩個零件：① 打分函數從加性小網路 vᵀtanh(·) 換成縮放內積 QKᵀ/√d（ch04–06）；② 多了 W_Q/W_K/W_V 三個學來的投影，而 Bahdanau 直接拿 RNN 隱態當 key/value。接線方式完全一樣。」——只要點到「目標查源」這個接線等同、並指出打分與投影是後加的，就算抓到核心。常見錯路：說「Bahdanau 是 self-attention 的雛形」——錯，Bahdanau 是**跨序列**的（decoder 看 encoder），是 cross 的雛形不是 self。

**第 4 題。**
(a) **影像的潛在特徵當 query**、**文字提示 "a cat on a sofa" 的 token embedding 當 key/value**（2026-06 查證，Stable Diffusion 的接法）。
(b) 影像的每個空間區域「查詢」文字提示，問「我這塊該根據哪些字來畫」——把文字條件按相關度拉進像素的生成過程。
(c) 異同：**相同**的是「異源 cross-attention＋三步骨架」這個核心；**不同**的是接線方向——翻譯是「目標文字 query 查源文字 key/value」（文字查文字），生圖是「影像 query 查文字 key/value」（圖查字）。query 和 key/value 的「身分」可以跨模態換來換去，但「主序列按相關度去拉取另一個條件序列的內容」這個本質不變。

## 自我檢核

口頭自答，講得出來才算過：

1. 用「誰當 query、誰當 key/value、能不能看未來」三個維度，把 encoder self / decoder masked-self / encoder-decoder cross 三種注意力各講一遍。三者**共用**什麼、**只有**什麼不同？
2. cross-attention 在三步骨架裡動了哪一步？（提示：不是動了任何一步的算法，而是動了第一步打分的兩個輸入「query 與 key/value 的來源」。）
3. 脊椎升級到翻譯場景後，注意力矩陣為什麼從 3×3 方陣變成「目標×源」矩形？為什麼這時候「找對角線＝自己」的直覺會失效？
4. 同一個 query q=(1,1,1,1)，為什麼 cross 給 animal 的權重（0.731）比 self（0.665）高？把「softmax 分母少了 it 那一項」這條因果講順。
5. 為什麼 cross-attention 這一步**不需要** causal mask，但 decoder 的 self-attention 需要？（提示：源句是不是逐字生成的？）
6. cross-attention 和 ch03 Bahdanau 的對齊是什麼關係？Transformer 的版本多加了哪兩個前面章節補過的零件？
7. 為什麼今日主流的 decoder-only LLM（GPT 類）**沒有** encoder-decoder cross-attention？那 cross-attention 現在主要活在哪裡？
8. 用「把外部條件當一張可查的 key/value 表」這句話，解釋文字控制生圖時 cross-attention 在做什麼（誰 query、誰 key/value）。

## 延伸閱讀

- **Vaswani et al. 2017「Attention Is All You Need」§3.2.3「Applications of Attention in our Model」**（arXiv 1706.03762，https://arxiv.org/abs/1706.03762 ）：本章三種注意力的原始出處。那一節用三段話分別交代 encoder self、decoder masked-self、encoder-decoder cross 各自「Q、K、V 從哪來」。直接讀那三段，對照本章的對照表，你會發現整章就是把它展開講。
- **Bahdanau, Cho & Bengio 2014「Neural Machine Translation by Jointly Learning to Align and Translate」**（arXiv 1409.0473，https://arxiv.org/abs/1409.0473 ）：cross-attention 的雛形（ch03 已細講）。本章回扣它——讀對齊模型那一節，看「decoder 狀態當 query、encoder 隱態當被對齊對象」這個接線，和 Transformer cross-attention 對照。
- **Rombach et al. 2021「High-Resolution Image Synthesis with Latent Diffusion Models」**（arXiv 2112.10752，https://arxiv.org/abs/2112.10752 ）：文字控制生圖怎麼用 cross-attention 注入條件。讀它講 cross-attention 那段（影像潛在特徵 Q、文字 embedding K/V），就懂了「a cat on a sofa」如何鑽進像素——cross-attention 在 NLP 之外最漂亮的應用之一。
- **DeepMind 2022「Flamingo: a Visual Language Model for Few-Shot Learning」**（arXiv 2204.14198，https://arxiv.org/abs/2204.14198 ）：gated cross-attention 把視覺注入凍結的語言模型。看它怎麼用「語言 Q、視覺 K/V」做多模態——和生圖的接線方向剛好相反，是體會「cross-attention 接線可以任意換身分」的好對照。
- **Jay Alammar「The Illustrated Transformer」的 encoder-decoder 段落**（https://jalammar.github.io/illustrated-transformer/ ）：把三種注意力與 encoder-decoder 資料流畫成動圖。看「The Decoder Side」那一段，cross-attention 怎麼接 encoder 輸出的 K/V，與本章的 ASCII 架構圖互為補充。
- **何時回來重讀**：當你在 ch13 看到 encoder-only（BERT）／decoder-only（GPT）／encoder-decoder（T5）三種模型家族時，回頭對照本章的三種注意力——你會發現「哪種模型有哪些注意力」正是由本章這三種接法的取捨決定的（BERT 只用 ①、GPT 只用 ②、T5 三種全用）。本章是 ch13 那張家族譜的零件清單。
