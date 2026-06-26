# ch13 — 一整層到一整個模型：注意力住在哪裡

> **本章解決什麼問題**：前面九章我們把注意力這台引擎拆到了零件等級——Q/K/V（ch04）、softmax（ch05）、√d 縮放（ch06）、自注意力矩陣（ch07）、多頭（ch08）、位置（ch09–10）、遮罩（ch11）、跨序列（ch12）。但你從沒看過它「裝回去」的樣子。真實的 transformer 不是一顆裸露的注意力——注意力是一層 block 裡的**一個零件**，旁邊還配著殘差連接、LayerNorm、和一個逐位置的前饋網路（FFN）；這樣的 block 再堆疊 N 層，才成為一個完整模型。本章補上這個「組裝」的視角：注意力**住在哪裡**、為什麼旁邊非得有殘差和 FFN（少了會發生一件很糟的事，叫秩坍縮），以及這些 block 怎麼接成今日三種模型家族——BERT、GPT、T5。三步骨架本身一個字都沒動；本章講的是**它周圍的鷹架**，以及這些鷹架為什麼存在。讀完你能對另一個工程師畫出一層 transformer 的資料流，並說清「為什麼純堆注意力不夠」。

## 從你已知的出發

你寫過的任何一個像樣的處理管線，從來不是一個裸函式。你不會把一個 `transform()` 直接串一百層接成系統——你會在每個 stage 旁邊配上**旁路、穩壓、和一個本地的加工步驟**。

具體一點，想想你部署過的一個請求處理 stage：

- **旁路（bypass / passthrough）**：你常留一條「原始輸入直接帶過去」的路徑，這個 stage 只**在原始資料上疊加**它算出的修正，而不是整個重寫。理由很現實——萬一這個 stage 算壞了，至少原始資訊還在，下游不會拿到一坨被某一層搞砸的垃圾。這正是**殘差連接（residual connection）** 的工程直覺：`輸出 = 輸入 + 這一層算出的東西`。
- **穩壓（normalization）**：多 stage 串起來最怕數值規模一層層放大或縮小，到後面要嘛爆掉要嘛消失。你會在 stage 之間插一個正規化步驟，把數值拉回一個固定的尺度再往下送。這是 **LayerNorm** 的角色。
- **本地加工（per-item processing）**：有些轉換不需要看別人、只在每一筆資料自己身上做——一個 `map(item => f(item))`，每筆獨立、同一個 `f`。這是 **FFN（前饋網路）** 在 transformer 裡的角色：注意力負責「跨位置混合資訊」，FFN 負責「在每個位置自己身上做一次非線性加工」。

一層 transformer block，就是把這三樣鷹架圍著**注意力**這個核心零件組裝起來：

```text
                      ┌──── 殘差旁路（原輸入帶過去）────┐
   輸入 ──┬──────────►│                                 ▼
          │           │   多頭注意力（跨位置混合）──►（＋）──► LayerNorm ──┐
          └───────────┘                                                    │
                                                                           ▼
                      ┌──── 殘差旁路 ────┐
                      │                  ▼
                      │   FFN（逐位置加工）──►（＋）──► LayerNorm ──► 這一層的輸出
                      └──────────────────┘
```

注意：本章**完全沒有動三步骨架**。打分、softmax、加權混合，全都在「多頭注意力」那個方塊**裡面**，跟前面九章一模一樣。本章講的是那個方塊**外面**圍了什麼、為什麼非圍不可。如果說 ch04–ch12 在打磨引擎，本章是在裝引擎室——油路、散熱、減震，少一樣車都跑不久。

> 全書地圖回顧（你在 Part III 的最後一格）：

```text
Part I 注意力解決什麼問題    Part II 三步骨架：核心機制    Part III 補上缺的零件
ch01 該看哪裡（序章）        ch04 Query/Key/Value         ch09 位置編碼
ch02 固定向量的瓶頸      →   ch05 softmax：該看哪裡    →   ch10 RoPE 與相對位置
ch03 第一次注意 Bahdanau     ch06 為什麼除以 √d            ch11 遮罩：只能看過去
                            ch07 自注意力與 O(n²)         ch12 交叉注意力與三型
                            ch08 多頭注意力               ch13 一整層到一整個模型 ◄你在這裡
                                                               │
                                                               ↓
Part VI 看進黑盒與未來      Part V 理論身世             Part IV 為什麼是 O(n²)
ch20 注意力是解釋嗎     ←   ch17 即核迴歸           ←   ch14 二次方瓶頸
ch21 QK/OV 與 induction     ch18 即聯想記憶 Hopfield     ch15 稀疏與線性注意力
ch22 注意力之外 SSM/Mamba    ch16 FlashAttention/KV 共享
ch23 總收官：同一個 it      ★ 三步骨架貫穿全書          ★＝打分→正規化→混合
```

## 一層 transformer block：兩個 sublayer 的標準三明治

原始 Transformer（Vaswani 2017，§3.1，landscape §2）把一層定義得非常規整：**一層 encoder block ＝ 兩個 sublayer**，每個 sublayer 都包在同一個「殘差 ＋ LayerNorm」的三明治裡。

```text
sublayer 1：多頭自注意力（multi-head self-attention）
sublayer 2：逐位置前饋網路（position-wise FFN）
```

兩個 sublayer 用的是**完全相同的包裝公式**。原文寫得很乾脆（landscape §2 覆核，2026-06）：每個 sublayer 的輸出是

```text
LayerNorm( x + Sublayer(x) )
        └──┬──┘   └───┬────┘
        殘差：原輸入   這個 sublayer 算出的東西
```

把它拆開看，每個 sublayer 做三件事，順序很重要：

1. **算**：`Sublayer(x)`——sublayer 1 是多頭注意力（前面九章那一整套），sublayer 2 是 FFN。
2. **加回去（殘差）**：`x + Sublayer(x)`——把原輸入直接加回算出來的東西。
3. **穩壓（LayerNorm）**：把相加的結果正規化，再送給下一個 sublayer。

> **這是原始 Transformer 的順序，叫 Post-LN（LayerNorm 在殘差相加之後）**（2026-06 查證）。2020 年後多數大型 LLM 改用 **Pre-LN**（`x + Sublayer(LayerNorm(x))`，把 LayerNorm 挪到 sublayer 前面），因為它在堆很深時訓練更穩、不太需要小心翼翼地暖身學習率（On Layer Normalization in the Transformer Architecture，Xiong 2020 查證）。哪種放法對訓練穩定性影響很大，但**那是訓練工程的事，本書不展開**（指向《從後端到 AI Infra》與深度學習專書）。對「注意力住在哪裡」這個原理問題，Post-LN 和 Pre-LN 的差別只是「LayerNorm 放殘差前還是後」——三明治的兩片麵包換了位置，夾的料（注意力＋殘差）沒變。本章用原始的 Post-LN 講，因為它是 landscape 的事實基準。

所以一層完整的 block，是這兩個三明治串起來：

```text
  輸入 x
    │
    ├──────────────┐               sublayer 1
    │              ▼
    │      多頭自注意力 Attn(x)
    │              │
    ▼              ▼
   （＋）◄──── 殘差相加 x + Attn(x)
    │
    ▼
  LayerNorm ──► z
    │
    ├──────────────┐               sublayer 2
    │              ▼
    │          FFN(z)
    │              │
    ▼              ▼
   （＋）◄──── 殘差相加 z + FFN(z)
    │
    ▼
  LayerNorm ──► 這一層的輸出
```

兩個 sublayer 分工明確，這是看懂一層 block 的關鍵直覺：

- **注意力 sublayer ＝ 跨位置的混合（mixing across positions）**。它讓每個 token 去看別的 token、把資訊拉過來（三步骨架）。它是「橫向」的——it 從 animal 那裡拿東西。
- **FFN sublayer ＝ 逐位置的加工（per-position processing）**。它**不看別人**，只在每個位置自己身上跑同一個小網路。它是「縱向」的——拿到混合好的資訊後，在原地做一次非線性轉換。

一句話記住：**注意力負責「交流」，FFN 負責「消化」。** 一層 block 先讓 token 們交流一次（注意力），再讓每個 token 各自消化一次（FFN）。少了任何一個，後面會看到，這層就殘廢了。

## 三個鷹架零件，逐一說清「它在解決什麼」

本書的鐵律是「禁止無動機的定義」。所以下面三個零件，每個都先回答「不裝它會怎樣」，再說它是什麼。三個都點到為止——這是 ML 鷹架，不是本書主題，深入指向深度學習專書。

### 殘差連接：給梯度和資訊各留一條直通捷徑

**不裝它會怎樣**：你把 sublayer 一層層硬串起來，每一層都對輸入做一次徹底的非線性重寫。堆個幾十層後，最底層那點原始資訊早就被反覆改寫到面目全非；而且訓練時梯度要穿過幾十層的非線性才能傳回去，一路衰減，底層幾乎學不到東西（梯度消失，回扣 ch06 softmax 飽和那個故障）。

**它是什麼**：殘差連接就是那條旁路——`輸出 = 輸入 + sublayer(輸入)`。sublayer 不再負責「重寫」輸入，而是負責**算出一個要疊加上去的修正量（residual，殘差）**。這有兩個好處：

- **資訊直通**：原輸入永遠有一條不被改寫的路徑通到最後（這正是為什麼原始 Transformer 規定所有 sublayer 和 embedding 都是同一個維度 d_model=512——不同維度沒法直接相加，landscape §2）。
- **梯度直通**：`x + sublayer(x)` 對 x 求導，那個 `+x` 貢獻一個常數 1 的梯度路徑，梯度可以「抄近路」直接傳回底層，不必穿過每一層的非線性。

工程類比你已經有了：殘差就是你那條「原始輸入帶過去」的旁路。這一層只在原值上**疊加**它的判斷，而不是推倒重來。萬一這層學歪了（輸出接近 0），殘差讓它至少退化成「原樣通過」，不會把資訊砸爛。

### LayerNorm：把每個 token 的數值拉回固定尺度

**不裝它會怎樣**：殘差是「一直往上加」（`x + sublayer(x) + …`），堆很多層後數值的規模會越滾越大或在某些維度上失控，softmax、內積這些對尺度敏感的運算（ch06 整章在講尺度！）就會行為怪異，訓練不穩。

**它是什麼**：LayerNorm 對**每一個 token 的向量自己**做正規化——把這個向量的各維減掉它自己的平均值、除以自己的標準差，拉成「平均值 0、變異數 1」，再用兩個可學的參數（縮放 γ、平移 β）調回模型想要的尺度。關鍵字是「Layer」：它是在**單一 token 的特徵維度上**做正規化（每個 token 獨立），不跨 token、不跨 batch——這跟你可能聽過的 BatchNorm 不同，後者跨樣本統計，在序列長度可變的 NLP 裡很麻煩，所以 transformer 用 LayerNorm。

工程類比：穩壓器。多 stage 串接時，你在中間插一個「把信號拉回標準範圍」的步驟，免得某一級的輸出規模把下一級頂爆。

### FFN：每個位置各自做一次非線性加工

**不裝它會怎樣**：這是最深刻的一個。**注意力本身幾乎是線性的**——加權混合就是 value 的加權平均（ch05），那是個線性運算；softmax 雖然非線性，但它只決定「權重」，混合那一步是線性的。如果一層裡只有注意力，那這一層對 value 做的本質上是「線性組合 ＋ 線性投影」。多層純線性疊起來，數學上等價於一個線性變換——表達力嚴重受限，而且會引發下一節的秩坍縮。**模型需要在每個位置注入真正的非線性**，這就是 FFN 的活。

**它是什麼**：FFN 是一個套在**每個位置上、獨立且相同**的小型兩層網路（position-wise，逐位置；landscape §2，2026-06 覆核原文）：

```text
FFN(x) = max(0, x·W₁ + b₁)·W₂ + b₂
            └──────┬──────┘
              ReLU 非線性（負的歸零）
```

原始 Transformer 的 FFN 把 d_model=512 先**擴張**到 d_ff=2048（4 倍），過一個 ReLU（負值歸零，提供非線性），再**收縮**回 512（landscape §2；查證 2026-06：d_ff 通常設為 d_model 的約 4 倍，俗稱 expand-and-contract，先膨脹再壓回）。為什麼擴張再收縮？膨脹到高維給網路更大的「工作空間」去做非線性切割，再壓回原維度好接下一層。同一個 FFN（同一組 W₁/W₂）作用在序列的**每一個位置**上——it 過一次、animal 過一次、street 過一次，各算各的，互不相干。

> **這裡值得停十分鐘**：注意力和 FFN 的分工是 transformer 最優雅的設計之一。注意力是**唯一**會跨位置搬資訊的零件——它決定「誰看誰、拉什麼過來」。FFN 則完全**不跨位置**，它只在每個 token 拉到資訊後，原地做一次重型的非線性加工。一個橫向（社交），一個縱向（思考）。整個 transformer 就是「交流一次、思考一次」交替疊 N 層。很多人以為 transformer 的能力全在注意力——其實參數量的大頭往往在 FFN（d_ff 是 d_model 的 4 倍，FFN 的兩個矩陣比注意力的投影矩陣大）。注意力決定看哪裡，FFN 決定看到之後怎麼想。

## 為什麼純堆注意力不夠：秩坍縮

現在來算清楚「少了殘差和 FFN 會發生的那件糟事」。這是本章的理論高潮，也是 ch13 在全書地圖上的一個重要伏筆（ch19 會把它形式化）。

直覺先行：注意力的第三步是**加權平均**（ch05）。平均這個動作，本性就是**把東西拉近**——你把一群數平均，結果一定落在它們中間，比原來更集中。如果你一層層**只做平均、不做別的**，每個 token 都在不斷地「變成大家的平均」，那麼所有 token 會越來越像，最後**全部收斂到同一個向量**。一旦所有 token 變成同一個向量，這個序列的表示就只剩一個方向——數學上叫**秩坍縮（rank collapse）**：表示矩陣的秩掉到 1，整個序列攤平成一條線，模型再也分不出哪個 token 是哪個。

這不是危言聳聽，是被嚴格證明的。**Dong, Cordonnier & Loukas 2021「Attention is Not All You Need: Pure Attention Loses Rank Doubly Exponentially with Depth」**（ICML 2021 oral，arXiv 2103.03404，landscape §5，2026-06 查證）證明：**純** self-attention（沒有殘差、沒有 MLP/FFN）的輸出會以**雙指數**的速度坍縮到秩 1。雙指數有多快？快到幾層就崩——這幾乎是「立刻」的意思。論文的解藥也很明確：**殘差連接和 FFN 正是阻止這個坍縮的兩個關鍵**（原文：skip connections and MLPs stop the output from degeneration）。

### Worked example：用脊椎親手看坍縮，再看殘差怎麼救

用脊椎的三個 value 當三個 token 的初始表示（沿用全書數字，v_animal=(1,0)、v_street=(0,1)、v_it=(1,1)），跑一個被刻意推到極端的「純平均注意力」——假設這一層的注意力權重恰好是均勻的（每個 token 對三個 token 各給 1/3，這是 Dong 描述的「token uniformity」極端情形）。

**純注意力（無殘差），第一層的混合**：每個 token 的新表示 ＝ 三個 value 的均勻平均。

```text
三個 value 的均勻平均 = (1/3)·(1,0) + (1/3)·(0,1) + (1/3)·(1,1)
                      = ( (1+0+1)/3 ,  (0+1+1)/3 )
                      = ( 2/3 , 2/3 )
                      ≈ (0.667, 0.667)
```

算一次就崩了：

```text
            初始              純注意力一層後
  animal   (1, 0)     ──►    (0.667, 0.667)
  street   (0, 1)     ──►    (0.667, 0.667)   ← 三個 token
  it       (1, 1)     ──►    (0.667, 0.667)     變成一模一樣！
                             表示矩陣的三列全相同 → 秩 = 1（坍縮）
```

三個原本不同的 token，被均勻平均後**全部變成 (0.667, 0.667) 這同一個向量**。再疊一層，平均三個相同的向量還是它自己，永遠停在這裡。序列的表示徹底攤平——這就是秩坍縮的極端版（我用 Python 核對：均勻平均後三列相同、矩陣秩為 1）。

**加上殘差**：現在把同一個平均結果，**加回各自的原輸入**（殘差就是 `x + sublayer(x)`）：

```text
            原輸入 x      ＋ 注意力混合 (0.667,0.667)  =  殘差後
  animal   (1, 0)       + (0.667, 0.667)            =  (1.667, 0.667)
  street   (0, 1)       + (0.667, 0.667)            =  (0.667, 1.667)
  it       (1, 1)       + (0.667, 0.667)            =  (1.667, 1.667)
                                          三列各不相同 → 秩維持 = 2（沒坍縮）
```

殘差一加，三個 token 又**各不相同**了——因為每個都保留了自己原始的那一份（animal 還記得自己是 (1,0)、street 還記得自己是 (0,1)）。混合帶來的「拉近」效果被「保留自我」的殘差抵住了。表示矩陣的秩維持在 2，序列沒有攤平。FFN 接著還會在每個位置上做非線性加工，進一步把它們推開。這就是 Dong 2021 那句話的具體機制：**殘差讓 token 不會忘記自己是誰，FFN 給每個位置注入非線性，兩者合力擋住坍縮。**

> **這裡了不起／反直覺在哪**：你大概以為「注意力是 transformer 的全部，殘差和 FFN 是無關緊要的鷹架」。完全相反——**純注意力會在幾層內自我毀滅**，把序列攤平成一條線。讓 transformer 能堆到幾十層還不崩的，恰恰是那兩個「不起眼的鷹架」。論文標題故意叫「Attention is Not All You Need」（注意力不是你需要的全部），是對原始那篇「Attention Is All You Need」的精準回敬——一個漂亮的學術冷笑話，背後是嚴格的證明。注意力是主角，但主角單獨上台會當場垮掉。

## 堆 N 層：從一層到一整個模型

一層 block 講清楚了，剩下的「組裝」其實很簡單到有點反高潮：**把同樣結構的 block 疊 N 層，前一層的輸出當後一層的輸入。** 原始 Transformer 是 encoder、decoder 各 N=6 層（landscape §2）。今日的大模型動輒幾十到上百層，但每一層的結構就是上面那個三明治，沒有變。

為什麼要堆很多層？直覺：一層只能做「交流一次、消化一次」。語言的結構是有層次的——詞→片語→子句→句意。淺層的注意力傾向抓局部、表面的關係（相鄰詞、句法），深層的注意力在淺層處理過的表示之上，抓更抽象、更長程的關係（指代、語意、篇章）。堆疊讓模型**逐層精煉**：底層 it 先搞清楚句法位置，中層才在這基礎上解指代（it→animal），高層整合出句意。這跟你的多層 pipeline 同理——每一 stage 在前一 stage 的產出上做更高層的加工。

```text
  輸入 embedding（＋位置編碼，ch09–10）
        │
        ▼
   ┌─ block 1 ─┐   注意力＋殘差＋LN → FFN＋殘差＋LN
        │
        ▼
   ┌─ block 2 ─┐   （同樣結構）
        │
        ⋮          堆 N 層（原始 N=6）
        │
        ▼
   ┌─ block N ─┐
        │
        ▼
   輸出表示 → （接任務頭，見下節）
```

注意一件事：堆疊讓 ch07 講的 O(n²) 變成「**每層**都付一次 n×n 的代價」。N 層就是 N 倍的 O(n²)——這是 Part IV（ch14–16）要正面解決的成本問題。本章先把結構講清，成本帳留給後面。

### ML 鷹架一句帶過：模型怎麼學、學什麼

到這裡你已經看過完整結構，但還沒談「它怎麼變好用的」。一句話補上鷹架（**不展開，這是訓練工程，本書邊界外**）：模型最常見的訓練目標是 **next-token 預測**——給定前面的 token，預測下一個 token 是什麼，用**交叉熵（cross-entropy）** 衡量預測的機率分布和真實答案差多遠（呼應《馴服隨機》：那是個機率分布；《馴服無限》：梯度往下走，最小化這個誤差）。所有的權重矩陣（W_Q/W_K/W_V/W_O、FFN 的 W₁/W₂、LayerNorm 的 γ/β）都是這樣**學出來的**——這正是 ch04 第一次說「權重是學來的」那句話的兌現。怎麼學（反向傳播、最佳化器）是訓練工程，指向深度學習專書，本書到此為止。

## 三種模型家族：BERT、GPT、T5

最後一塊拼圖。同樣的 block 堆疊，**接線方式不同**（ch12 的三種注意力是零件，這裡是把零件組成整機），長出三種模型家族。差別全在 ch11–ch12 那兩個問題：**能不能看未來？有沒有 encoder？**

### encoder-only：BERT（雙向，理解）

只用 encoder 那疊 block，注意力是**雙向**的 self-attention（沒有 causal mask，每個 token 看全句，ch07/ch11）。代表是 **BERT**（Devlin 2019，landscape §3）。雙向意味著它讀理解時整句都在手上，特別適合**理解類**任務——分類、抽取、填空。它的訓練目標是「克漏字」（masked language modeling，遮住一些詞讓模型猜，這也是它能雙向的原因：要猜中間的詞當然要看左右兩邊，2026-06 查證）。BERT 不擅長生成——它不是設計來逐字往下寫的。

### decoder-only：GPT（單向，生成）——今日主流 LLM 形態

只用 decoder 那疊 block，注意力是 **masked（單向）** self-attention（causal mask，每個 token 只看左邊，ch11）。代表是 **GPT** 系列。單向是為了**自迴歸生成**：逐字往下寫，每寫一個字只能依賴已經寫出的（不能偷看未來，ch11 的鐵律）。

> **這是 2026 年絕大多數生成式 LLM 的形態**（GPT 系列、Claude、Gemini、Llama 等主線都是 decoder-only）。注意一個 ch12 強調過、這裡要再釘一次的事實：decoder-only 模型**沒有 encoder，所以沒有 encoder-decoder cross-attention**——它整個模型裡只有一種注意力，masked self-attention。ch12 那個「三種注意力」的完整陣容只在 encoder-decoder 架構裡才湊齊。

### encoder-decoder：T5（讀寫分離，翻譯/摘要）

encoder 和 decoder 都用，三種注意力全上場（ch12）：encoder 雙向 self、decoder masked self、中間用 cross-attention 把 decoder 的 query 接到 encoder 的 key/value。代表是 **T5**（Raffel 2019）。這是**原始 Transformer 的原生形態**（2017 那篇就是為翻譯設計的 encoder-decoder），適合**有明確輸入序列要轉成輸出序列**的任務——翻譯、摘要。T5 的特色是把所有任務都包裝成「文字進、文字出」（text-to-text，2026-06 查證）。

三種家族的對照——這張表就是 ch11–ch12 那兩個問題的答案矩陣：

```text
家族           有 encoder?  注意力種類              看未來?    典型用途
──────────────────────────────────────────────────────────────────────────
encoder-only   只有 encoder  雙向 self              看全句     理解（分類/抽取）
（BERT）                                                       克漏字訓練
decoder-only   只有 decoder  masked self            只看左     生成（逐字往下寫）
（GPT）                      （唯一一種注意力）                next-token 訓練
                                                              ★今日主流 LLM
encoder-decoder 兩者都有     雙向 self ＋ masked     源：看全   序列→序列
（T5）                      self ＋ cross           目標：看左  翻譯/摘要
```

三種家族對到你熟的服務形態：encoder-only 是**唯讀**服務（讀進來、理解、輸出判斷，不續寫）；decoder-only 是**串流寫入**服務（逐字 append，只能依賴已寫的，append-only log 那條線，ch11）；encoder-decoder 是**讀寫分離**服務（一個專門讀源、一個專門寫目標，中間用 cross-attention 接通，像 reader/writer 分離的架構）。注意力住在哪、能看哪，就決定了這台機器是讀、是寫、還是讀寫。

> 收個有趣的歷史轉折（誠實標時點 2026-06）：原始 Transformer 是 encoder-decoder（為翻譯），最早最紅的也是 encoder-only 的 BERT（2018–2019 統治理解類榜單）。但 2020 年後，隨著生成式應用爆發，**decoder-only 成了大模型的事實主流**——同一套注意力零件，最後勝出的接法是「只留 decoder、只看過去、逐字生成」這個最簡單的形態。這不是因為它表達力最強，而是因為它最適合「給前文、續寫下一個 token」這個能涵蓋幾乎所有任務的通用目標。為什麼是它勝出，是個值得另寫一本書的問題；本章只要你記住：**三種家族是同一套 block 的三種接線，今日主線走 decoder-only。**

## Worked example：脊椎的 it 走完一整層 block

把前面所有零件接起來，讓脊椎那個 it 第一次走完**完整的一層**。我們接續 ch08 多頭那一站的產出。維度沿用脊椎玩具 d=4。

**第 0 步：這一層的輸入。** it 這個位置進入這層 block 時，帶著一個 4 維表示。我們用 ch04 那個產生 q_it 的輸入向量 x_it=(1,1,1,1)（脊椎基準）當這層的輸入。

**第 1 步：注意力 sublayer 算。** it 對全序列做多頭注意力。ch08 算過，兩顆頭 concat、過 W_O=I 後，it 位置拿到的注意力輸出是 **(0.822, 0.266, 0.926, 0.380)**（ch08 worked example 的結果，我已重新核對吻合）。這就是 `Sublayer(x)`——it 從別的 token（主要是 animal）混回來的東西。

**第 2 步：殘差——加回輸入。**

```text
x + Attention(x) = (1, 1, 1, 1) + (0.822, 0.266, 0.926, 0.380)
                 = (1.822, 1.266, 1.926, 1.380)
                   └──── it 既記得自己原本是誰，又疊上了從別人那拉來的資訊 ────┘
```

注意這一加的意義：it 沒有被注意力的輸出**取代**，而是在自己原來的 (1,1,1,1) 上**疊加**了混合結果。這就是殘差防坍縮的那一手——it 不會忘記自己是 it。

**第 3 步：LayerNorm——拉回固定尺度。** 對 (1.822, 1.266, 1.926, 1.380) 這個向量做 LayerNorm（取 γ=1、β=0，即標準正規化）：

```text
平均值 m = (1.822 + 1.266 + 1.926 + 1.380) / 4 = 6.394 / 4 = 1.5985
各維減平均值：(0.224, −0.333, 0.327, −0.219)
標準差 σ = √(各維離差平方的平均) = √( (0.224²+0.333²+0.327²+0.219²)/4 ) ≈ 0.281

LayerNorm 輸出 = (各維離差) / σ
              = (0.796, −1.184, 1.166, −0.778)
                核對：四維和 ≈ 0 ✓、變異數 ≈ 1 ✓（我用 Python 驗過）
```

得到 z = (0.796, −1.184, 1.166, −0.778)，這是 sublayer 1（注意力）的最終輸出，平均值 0、變異數 1，尺度乾淨，送進 sublayer 2。

**第 4 步：FFN sublayer。** z 過 FFN——`max(0, z·W₁+b₁)·W₂+b₂`，這是 it 這個位置**自己**的一次非線性加工（不看別的 token）。真實的 W₁/W₂ 是訓練學出來的、我們沒有，所以這一步只示意結構不給具體權重（給了也是瞎編，違反本書誠實原則）：FFN 把 z 擴張到高維、ReLU 砍掉負的、再壓回 4 維，產出一個修正量。

**第 5 步：第二個殘差 ＋ LayerNorm。** `LayerNorm( z + FFN(z) )` ——同樣把 FFN 的修正疊回 z，再正規化。輸出就是**這一層 block 對 it 的最終產物**，交給下一層 block 當輸入。

走完一層，你看到的是：**it 在一層裡，先跟全句交流了一次（注意力，主要拉了 animal 的資訊回來），保住自我（殘差），調好尺度（LayerNorm），再自己消化了一次（FFN），保住自我、調好尺度。** 堆 N 層，就是把這個「交流—消化」循環做 N 遍，it 對 animal 的理解逐層精煉。脊椎那個懸念（it 該看 animal）的解答，就是在這樣一層層的 block 裡被算出來、且不被秩坍縮抹平的。

如果你想看演算法骨架，一層 Post-LN block 就是這幾行（每顆頭的 `multi_head` 是 ch08 那個函式，原封不動）：

```python
def transformer_block(x, attn_params, ffn_params):
    # sublayer 1: multi-head self-attention + residual + LayerNorm
    a = multi_head(x, x, x, *attn_params)   # ch08: cross-position mixing
    x = layer_norm(x + a)                    # residual, then normalize (Post-LN)
    # sublayer 2: position-wise FFN + residual + LayerNorm
    f = ffn(x, *ffn_params)                  # per-position non-linear processing
    x = layer_norm(x + f)                    # residual, then normalize
    return x
```

兩個 sublayer，同樣的「算 → 加回去 → 正規化」三明治。注意力和 FFN 是裡頭那個 `Sublayer`，殘差是那個 `x +`，LayerNorm 是那個包裹。整層的精神全在這六行裡：**混合一次、消化一次，每次都記得自己是誰。**

## 故障模式與直覺陷阱

| 直覺陷阱 / 故障 | 為什麼錯／在哪一步把你帶溝裡 | 怎麼自我察覺、正確版是什麼 |
|---|---|---|
| 「注意力就是 transformer 的全部，殘差/FFN 是次要鷹架」 | 危險的本末倒置。Dong 2021 證明**純注意力會雙指數坍縮到秩 1**——幾層就把序列攤平成一條線。殘差與 FFN 不是裝飾，是讓深層 transformer 不自我毀滅的關鍵。 | 記住論文標題的對話：「Attention Is All You Need」vs「Attention is **Not** All You Need」。自己用脊椎三個 value 算一次均勻平均，看它們怎麼全變成 (0.667,0.667)。 |
| 「FFN 也跨位置混合資訊」 | 把兩個 sublayer 的分工搞混。FFN 是**逐位置（position-wise）** 的——它對每個 token 獨立跑同一個小網路，**完全不看別的 token**。跨位置混合是注意力的**唯一**職責。 | 默念分工：注意力＝橫向（交流），FFN＝縱向（消化）。問自己「這一步有沒有看別的位置？」——FFN 沒有。 |
| 「殘差就是把輸出和輸入拼接（concat）」 | 殘差是**相加（add）** 不是拼接。`x + sublayer(x)`，維度不變（這正是為何所有 sublayer 都得是 d_model）。拼接會讓維度增長，而且少了「梯度直通」那條常數梯度路徑。 | 看公式裡是 `+` 還是接起來。殘差永遠是逐元素相加、維度守恆。（concat 是 ch08 多頭在做的事，別搞混。） |
| 「LayerNorm 跨 token 或跨 batch 做正規化」 | 那是 BatchNorm。LayerNorm 是在**單一 token 的特徵維度**上正規化（每個 token 自己減自己的平均值除自己的標準差），不跨 token、不跨 batch——所以序列長度可變也不怕。 | 關鍵字「Layer」＝對一個 token 的那一層特徵做。問自己「統計量是從誰算的？」——從這一個 token 的各維算的。 |
| 「decoder-only 的 GPT 裡也有 cross-attention」 | ch12 已警告過、這裡再釘一次。decoder-only **沒有 encoder**，所以**沒有 cross-attention**，只有一種 masked self-attention。cross 只活在 encoder-decoder（T5）裡。 | 問自己「這個模型有 encoder 嗎？」沒有就沒有 cross。三種家族對照表裡，只有 T5 那行有 cross。 |
| 「BERT 也能像 GPT 那樣逐字生成」 | 把理解模型當生成模型。BERT 是雙向 encoder-only，訓練目標是克漏字，它沒有「只看左邊逐字往下寫」的機制，不適合自迴歸生成。 | 看注意力是雙向還是 masked。雙向（看全句）→ 理解；masked（只看左）→ 生成。家族決定能幹什麼。 |
| 「Pre-LN 和 Post-LN 是兩種不同的注意力機制」 | 兩者的注意力**一模一樣**，差別只是 LayerNorm 放在殘差相加之前還是之後——是訓練穩定性的工程選擇，不是機制差異。 | 原始 Transformer 是 Post-LN（`LN(x+sub(x))`），多數現代 LLM 是 Pre-LN（`x+sub(LN(x))`）。三明治換了麵包順序，夾的料沒變。深入指向訓練工程書。 |

**和後面章節的鉤子**：本章的秩坍縮（純注意力坍縮到秩 1）是一個會反覆回來的伏筆。ch19 會把它**形式化**——從「集合運算／置換等變」的角度嚴格說明為何純注意力有「token uniformity」的歸納偏置，以及殘差與 FFN 在數學上如何阻止它。本章只需要你帶走直覺：**注意力是平均、平均會拉近、一直平均會坍縮、殘差和 FFN 把它救回來。** 另外，三種模型家族（尤其 decoder-only 主導）這個事實，會在 ch22 討論「2026 年 attention 是否還是唯一解」時再被拿出來檢視——挑戰者（SSM/Mamba）想動的，正是 decoder-only 那條 masked self-attention 的 O(n²) 成本。

## 紙上推演

### 推演題

**第 1 題 [12 分鐘]（★）** 畫出一層 transformer block 的資料流。要標出：(a) 兩個 sublayer 分別是什麼；(b) 每個 sublayer 外面包的「殘差 ＋ LayerNorm」三明治（原始 Post-LN 的公式 `LayerNorm(x + Sublayer(x))`）；(c) 用一句話說每個 sublayer 的分工——哪個跨位置、哪個逐位置。畫完後口頭回答：殘差是「相加」還是「拼接」？為什麼這決定了所有 sublayer 必須同維度？

**第 2 題 [15 分鐘]（★★）** 親手演示秩坍縮與殘差的解救。用脊椎三個 value 當三個 token 的初始表示：v_animal=(1,0)、v_street=(0,1)、v_it=(1,1)。假設一層純注意力的權重是均勻的（每個 token 對三個 token 各 1/3）。(a) 算「純注意力（無殘差）」一層後三個 token 各變成什麼向量？三列相同嗎？秩是多少？(b) 改成「注意力 ＋ 殘差」（把均勻平均的結果加回各自原輸入），算三個 token 各變成什麼？三列還相同嗎？秩是多少？(c) 用一句話說：殘差到底擋住了什麼？（提示：它讓每個 token 保住了什麼？）

**第 3 題 [10 分鐘]（★★）** 解釋「為什麼純堆注意力不夠、需要殘差與 FFN」，講給另一個工程師聽（不查書，三到五句）。要點到：(a) 注意力的混合本質上是個什麼運算（線性？非線性？）；(b) 一直做這種運算會導致什麼（Dong 2021 的結論）；(c) 殘差和 FFN 各自怎麼幫忙（一個保住自我、一個注入非線性）。

**第 4 題 [10 分鐘]（★★）** 把 BERT / GPT / T5 三種家族做成對照表，三欄是：(a) 有沒有 encoder；(b) 用哪種（哪幾種）注意力；(c) 注意力看不看未來、典型用途。填完後回答兩個問題：① 為什麼 decoder-only 的 GPT 裡找不到 cross-attention？② 哪一種是 2026 年生成式 LLM 的主流形態，為什麼是它（一句話）？

### 推演解答

**第 1 題。**

```text
  輸入 x ──┬─────────────────────────────┐
           │                             ▼
           │  (a) sublayer 1：多頭自注意力 ──►(＋)──► LayerNorm ──► z
           └─────────────────────────────┘  (b) 殘差＋LN：LayerNorm(x + Attn(x))
                                                   (c) 跨位置：讓 token 互相交流
           ┌─ z ─────────────────────────┐
           │                             ▼
           │  (a) sublayer 2：FFN ────────►(＋)──► LayerNorm ──► 輸出
           └─────────────────────────────┘  (b) 殘差＋LN：LayerNorm(z + FFN(z))
                                                   (c) 逐位置：每個 token 自己消化
```

殘差是**相加（add）**，不是拼接。因為 `x + Sublayer(x)` 要逐元素相加，兩者維度必須一樣——所以原始 Transformer 規定所有 sublayer 與 embedding 輸出都是同一個 d_model=512，否則加不起來。常見錯路：以為殘差像 ch08 多頭那樣 concat——不對，多頭 concat 會讓維度變大，殘差永遠維度守恆。

**第 2 題。**
(a) 純注意力（無殘差）：每個 token 變成三個 value 的均勻平均 ＝ (1/3)(1,0)+(1/3)(0,1)+(1/3)(1,1) ＝ (2/3, 2/3) ≈ **(0.667, 0.667)**。三個 token **全變成這同一個向量**，三列相同 → **秩 = 1**（坍縮）。
(b) 注意力 ＋ 殘差：把 (0.667,0.667) 加回各自原輸入：
- animal：(1,0)+(0.667,0.667) = **(1.667, 0.667)**
- street：(0,1)+(0.667,0.667) = **(0.667, 1.667)**
- it：(1,1)+(0.667,0.667) = **(1.667, 1.667)**

三列**各不相同** → **秩 = 2**（沒坍縮）。
(c) 殘差擋住了「token 全變成大家的平均」這件事——它讓每個 token **保住了自己原本的那一份表示**（animal 記得自己是 (1,0)），混合的拉近效果被「保留自我」抵住，所以序列不會攤平成一條線。常見錯路：以為坍縮要堆很多層才發生——Dong 2021 證明是**雙指數**速度，這個極端均勻例子裡一層就崩了。

**第 3 題（要點）。** 一個說得通的版本：「注意力的第三步是加權平均 value，那本質上是個**線性**運算——softmax 只決定權重，混合是線性的。一層層只做這種『平均』，每個 token 不斷變成大家的平均，會越來越像，最後**全部收斂成同一個向量**（秩坍縮，Dong 2021 證明是雙指數速度坍縮到秩 1）。殘差（`x + 注意力輸出`）讓每個 token 保住自己原本的表示、不會忘記自己是誰；FFN 在每個位置注入真正的**非線性**加工。兩者合力，讓深層 transformer 堆幾十層也不會把序列攤平。」——只要點到「平均→拉近→坍縮」與「殘差保自我、FFN 給非線性」就算抓到核心。常見錯路：只說「為了訓練穩定」——那是 LayerNorm 的活，殘差/FFN 解的是**表達力坍縮**，是不同的問題。

**第 4 題。**

```text
家族            有 encoder?   注意力種類             看未來?   典型用途
──────────────────────────────────────────────────────────────────────────
BERT            只有 encoder   雙向 self             看全句    理解：分類/抽取
（encoder-only）                                              （克漏字訓練）
GPT             只有 decoder   masked self（唯一）   只看左    生成：逐字往下寫
（decoder-only）                                             （★今日主流 LLM）
T5              兩者都有       雙向 self ＋ masked    源:看全   序列→序列
（encoder-dec.）              self ＋ cross          目標:看左  翻譯/摘要
```

① GPT 是 decoder-only，**沒有 encoder**，而 cross-attention 的定義就是「Q 來自 decoder、K/V 來自 encoder」（ch12）——沒有 encoder 就沒有可被查詢的源序列 key/value，所以沒有 cross-attention。GPT 整個模型只有一種注意力：masked self-attention。
② **decoder-only（GPT 類）是 2026 年生成式 LLM 的主流**（2026-06）。一句話原因：它最適合「給前文、續寫下一個 token」這個 next-token 預測目標，而幾乎所有任務都能被改寫成這個通用形式，所以這個最簡單的接法反而最通用。常見錯路：說「因為 decoder-only 表達力最強」——不準確，勝出更多是因為通用性與訓練/部署的簡潔，而非單純表達力。

## 自我檢核

口頭自答，講得出來才算過：

1. 一層 transformer block 由哪兩個 sublayer 組成？每個外面包的「三明治」是什麼公式（原始 Post-LN）？兩個 sublayer 的分工——哪個跨位置、哪個逐位置？
2. 殘差連接解決什麼問題？它是「相加」還是「拼接」？為什麼這決定了所有 sublayer 必須同維度？（提示：資訊直通＋梯度直通。）
3. LayerNorm 在正規化什麼？它和 BatchNorm 的關鍵差別是什麼？（提示：對單一 token 的特徵維度做，不跨 token/batch。）
4. FFN 在做什麼、為什麼非有它不可？（提示：注意力的混合本質是線性的，模型需要在每個位置注入非線性；expand-and-contract。）
5. 「純堆注意力會秩坍縮」是什麼意思？用脊椎三個 value 親手算的均勻平均結果是什麼？殘差怎麼把它救回來？（連到 Dong 2021、雙指數坍縮到秩 1。）
6. 為什麼要堆 N 層而不是用一個超大的單層？堆疊讓 O(n²) 變成什麼成本？（提示：逐層精煉；每層付一次 n×n，N 層 N 倍。）
7. BERT / GPT / T5 三種家族，用「有沒有 encoder、哪種注意力、看不看未來」各講一遍。為什麼 decoder-only 裡沒有 cross-attention？
8. 哪一種家族是 2026 年生成式 LLM 的主流形態？為什麼勝出的是這個最簡單的接法？（一句話。）

## 延伸閱讀

- **Vaswani et al. 2017「Attention Is All You Need」§3.1–§3.3**（arXiv 1706.03762，https://arxiv.org/abs/1706.03762 ）：一層 block 的原始定義。讀 §3.1（兩個 sublayer 與 `LayerNorm(x + Sublayer(x))` 的 Post-LN 公式、N=6、所有 sublayer d_model=512）、§3.3（position-wise FFN，d_ff=2048、ReLU）。對照本章你自己走的那一層脊椎。
- **Dong, Cordonnier & Loukas 2021「Attention is Not All You Need: Pure Attention Loses Rank Doubly Exponentially with Depth」**（ICML 2021，arXiv 2103.03404，https://arxiv.org/abs/2103.03404 ）：本章秩坍縮的證據來源，也是「為何需要殘差與 FFN」的嚴格答案。讀它的 path decomposition 直覺與「skip connections and MLPs stop the output from degeneration」那個結論；不必啃完整證明，抓住「純注意力雙指數坍縮到秩 1」即可。ch19 會深入。
- **Xiong et al. 2020「On Layer Normalization in the Transformer Architecture」**（arXiv 2002.04745，https://arxiv.org/abs/2002.04745 ）：Pre-LN vs Post-LN 為何影響訓練穩定性。本章只用結論（現代 LLM 多走 Pre-LN，訓練更穩）；想知道為什麼 Pre-LN 不太需要學習率暖身，讀這篇——但記住這是訓練工程，本書邊界外。
- **Jay Alammar「The Illustrated Transformer」的「Residuals」與「The Decoder Side」段落**（https://jalammar.github.io/illustrated-transformer/ ）：把一層 block 的殘差、LayerNorm、FFN、以及 encoder-decoder 整機畫成圖。看「Residuals」那節的 add & normalize 動畫，與本章 ASCII 三明治互為補充。
- **《從後端到 AI Infra》（與工作相關的書）**：本章刻意不展開的「N 層各付一次 O(n²) 的成本帳、KV cache、推論部署」全在那本。本章講結構，那本講「這個結構在 H100 上跑起來要花多少記憶體與時間」——讀完本章對結構有概念後，那本接手講成本與系統。
- **何時回來重讀**：當你在 ch19 看到「self-attention 的置換等變與 token uniformity」的嚴格版時，回頭看本章的秩坍縮 worked example——你會發現本章用脊椎手算的「三個 value 均勻平均變成同一個向量」，正是 ch19 要形式化的那個歸納偏置的最小可見證據；以及 ch22 討論 SSM/Mamba 時，回頭看本章的三種家族——挑戰者瞄準的正是 decoder-only 那條 masked self-attention 的成本。
