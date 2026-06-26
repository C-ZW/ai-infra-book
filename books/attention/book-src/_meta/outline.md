# 全書大綱（內部文件，非書籍內容）

書名：《注意力機制的原理》（副標：直覺、機制與理論）
形態：23 章、六個 Part、3 個附錄。原理與欣賞書（**不教訓練、不教部署、不刷論文**；紙上推演為主＋**指定處少量可讀 NumPy/虛擬碼**）。
每章必須遵守 `style-guide.md` 的骨架與深度標準；歷史與時效性事實以 `landscape-2026-06.md` 為錨。
全書脊椎：**同一個句子裡的代名詞「it」**，每個 Part 越懂越深（脊椎多層讀法見 style-guide）。
全書統一骨架：**三步骨架＝打分（score）→ 正規化（softmax）→ 加權混合（mix）**，每章回扣。

## 全書敘事弧

一個代名詞「it」該看哪裡？（ch01）→ 為什麼舊方法（把整句壓成固定向量）做不到（ch02）→ 第一次注意：讓 decoder 動態加權源句（Bahdanau 2014，ch03）→ **核心機制（三步骨架）**：把查找拆成 Query/Key/Value（ch04）、softmax 把分數變成「該看哪裡」（ch05）、為什麼要除以 √d（ch06）、每個 token 都查一次＝自注意力與 O(n²)（ch07）、為什麼要很多顆頭（ch08）→ **補上缺的零件**：位置不是內建的（ch09）、用旋轉編碼位置 RoPE（ch10，接《圓的影子》）、只能看過去的遮罩（ch11）、跨序列查找與三種注意力（ch12）、把 attention 裝回一整層、一整個模型（ch13）→ **為什麼是 O(n²)**：一張建不了索引的表（ch14）、給它建索引：稀疏與線性注意力（ch15）、不近似也能省：FlashAttention 與 KV 共享（ch16）→ **它到底是什麼（理論身世）**：即核迴歸（ch17）、即聯想記憶／Hopfield（ch18）、即集合運算（ch19）→ **看進黑盒與未來**：注意力權重是解釋嗎（ch20）、QK/OV 電路與 induction heads（ch21）、注意力之外——SSM/Mamba 與 2026 的混合架構（ch22）→ 總收官：同一個 it，八層讀法（ch23）。

歷史暗線（交織不另立章，全照 landscape）：seq2seq 固定向量瓶頸（Sutskever 2014）→ Bahdanau 對齊注意力（2014）與 Luong 乘性（2015）→ Graves NTM 的可微分記憶（2014，伏筆 ch18）→ Transformer 統一一切（Vaswani 2017）→ 位置編碼演化到 RoPE（Su 2021）→ 效率之戰（Sparse 2019、Linear 2020、FlashAttention 2022）→ 理論回看（核迴歸 Tsai 2019、Hopfield Ramsauer 2020、秩坍縮 Dong 2021）→ 可解釋性論戰（2019）與機制可解釋性（Anthropic 2021–2022）→ SSM/Mamba 與混合架構（2021–2026）。

## 全書 ASCII 路線圖（基準圖；Part 首章照抄，把「◄你在這裡」標到該 Part）

```text
Part I 注意力解決什麼問題    Part II 三步骨架：核心機制    Part III 補上缺的零件
ch01 該看哪裡（序章）        ch04 Query/Key/Value         ch09 位置編碼
ch02 固定向量的瓶頸      →   ch05 softmax：該看哪裡    →   ch10 RoPE 與相對位置
ch03 第一次注意 Bahdanau     ch06 為什麼除以 √d            ch11 遮罩：只能看過去
                            ch07 自注意力與 O(n²)         ch12 交叉注意力與三型
                            ch08 多頭注意力               ch13 一整層到一整個模型
                                                               │
                                                               ↓
Part VI 看進黑盒與未來      Part V 理論身世             Part IV 為什麼是 O(n²)
ch20 注意力是解釋嗎     ←   ch17 即核迴歸           ←   ch14 二次方瓶頸
ch21 QK/OV 與 induction     ch18 即聯想記憶 Hopfield     ch15 稀疏與線性注意力
ch22 注意力之外 SSM/Mamba    ch19 即集合運算             ch16 FlashAttention/KV 共享
ch23 總收官：同一個 it      ★ 三步骨架貫穿全書          ★＝打分→正規化→混合
```

## 跨章基準（一致性掃描的依據；各章不得另創數字與命名）

**貫穿範例「同一個 it」**——脊椎句子 *"the animal didn't cross the street because **it** was too tired"*，簡化序列 [animal, street, it]。

| 元素 | 基準 | 首次出現 |
|---|---|---|
| 脊椎句子出處 | Google AI 2017-08 部落格，非原論文；經 Illustrated Transformer 普及（照 landscape §8，**不可說出自原論文**） | ch01 |
| 脊椎向量 | q_it=(1,1,1,1)；k_animal=(2,1,1,0)、k_street=(0,1,1,0)、k_it=(1,−1,0,0)；v_animal=(1,0)、v_street=(0,1)、v_it=(1,1)。**ch04–07 用單頭視角，維度直接叫 d=4、√d=2；d_k=d_model/h 的多頭拆分留 ch08** | ch04 |
| 脊椎打分 | 原始內積 QKᵀ=[animal 4, street 2, it 0] | ch04 |
| ch05 首算（未縮放） | 為避免在 √d 之前用到縮放，ch05 用**未縮放**分數把三步骨架先跑完一次：softmax([4,2,0])=[animal 0.867, street 0.117, it 0.016]（e⁴=54.598,e²=7.389,e⁰=1,和 62.99）；輸出 0.867·(1,0)+0.117·(0,1)+0.016·(1,1)≈(0.883, 0.133) | ch05 |
| ch06 縮放（**全書正典**） | /√d=2 → [2,1,0] → softmax=[animal **0.665**, street **0.245**, it **0.090**]（e²=7.389,e¹=2.718,e⁰=1,和 11.107）；**ch07 起一律用這組縮放後權重**，並對照 ch05 未縮放的 [0.867,0.117,0.016] 看「尖→軟」 | ch06 |
| 脊椎輸出（縮放後正典） | 0.665·(1,0)+0.245·(0,1)+0.090·(1,1) ≈ (0.755, 0.335)，偏向 animal | ch06 |
| 置換不變 | 把 [animal,street,it] 重排，it 對各 token 的權重不變（無位置資訊）——非加位置不可 | ch09 |
| 原始 Transformer 超參 | d_model=512、h=8、d_k=d_v=64（√d_k=8）、d_ff=2048、N=6（encoder/decoder 各 6 層）（照 landscape §2） | ch08 |
| 原始 Transformer 結果 | WMT'14 英德 28.4 BLEU、英法 41.0 BLEU（big model） | ch03／ch13 |
| 多頭脊椎 | 把 4 維拆成 2 顆頭×2 維：head A 抓句法、head B 抓指代，concat | ch08 |
| 關鍵年份/論文 | Bahdanau 2014(1409.0473)、Vaswani 2017(1706.03762)、RoPE 2021(2104.09864)、FlashAttention 2022(2205.14135)、Hopfield 2020(2008.02217)、induction heads 2022(2209.11895)、Mamba 2023(2312.00752)（皆照 landscape） | 各章 |
| 數字精度 | e≈2.71828、e²≈7.389、e⁴≈54.598；脊椎權重全書統一不得矛盾 | — |

**全域不涵蓋**（任何章都不展開，最多一句＋指向延伸閱讀或鄰書）：訓練工程與反向傳播數學（梯度只在 ch06/ch17 點到、指向《馴服無限》）、PyTorch/JAX 框架與 `nn.Module` 樣板、KV cache 記憶體管理／PagedAttention／prefill-decode／量化／batching 的**部署深度**（指向《從後端到 AI Infra》ch03/05/06/07）、線性代數的**運算深度**（內積/投影/SVD 指向《矩陣是動詞》）、完整的 SSM 理論與 HiPPO 推導（ch22 只給直覺一句＋延伸）、強化學習/RLHF、tokenizer 細節（一句帶過、指向工作書 ch03）、具體模型排行榜與 benchmark 大全。

---

## Part I — 注意力解決什麼問題（ch01–03）

### ch01 — 該看哪裡：一個代名詞的難題（序章）
- **目標**：讀完能說出本書要解決的核心問題（讓模型自己算出「每個位置該看序列的哪裡」）、認得脊椎句子與 it 懸念、看懂三步骨架的預告圖、畫得出全書地圖；並補上最小 ML 鷹架（token→embedding 向量是什麼）。
- **必涵蓋**：脊椎句子登場與 it 指代懸念（人一眼知道是 animal、機器憑什麼？**例子出處照 landscape：Google 2017 部落格，不可說原論文**）；「注意力」的一句話定義——對所有位置做一次「依相關性加權的平均」；**三步骨架**首次亮相（打分→正規化→加權混合）只給直覺、不算；**最小 ML 鷹架**：模型不讀字讀向量，token 經 embedding 變成一個向量（一句帶過 tokenizer，指向《從後端到 AI Infra》ch03）、「權重是學來的」是什麼意思（先給直覺，ch04 再用）；全書路線圖（基準圖首次出場）＋七條驗收目標開宗明義。
- **不涵蓋**：QKV 與真正的計算（ch04）；softmax 細節（ch05）；任何訓練機制（全域不涵蓋）。
- **橋接**：你天天在做「該看哪裡」——load balancer 該把請求送哪台、router 看哪條規則、cache 該查哪個 key；差別是那些規則你手寫死，注意力讓模型**自己學出**「該看哪裡」。
- **Worked example**：用脊椎句子做純文字版——把 it 對 animal/street 的「相關性」用直覺打三個分數（先不給公式），混合出「it 比較像 animal」，預示三步骨架（數字版留 ch04–05）。
- **紙上推演**：把「該看哪裡」翻成你熟的三個工程場景（routing/cache/JOIN）；對脊椎句子，口頭說出 it 該看 animal 的理由；畫出全書地圖並標出你最想先懂哪一格。

### ch02 — 固定向量的瓶頸：RNN 與 seq2seq 為何卡住
- **目標**：能講出注意力誕生前的世界長什麼樣、seq2seq 的「固定長度 context vector」為什麼是瓶頸，理解注意力是來解決一個**具體的痛**。
- **必涵蓋**：序列轉序列（seq2seq）的 encoder-decoder 框架（Sutskever 2014、Cho 2014 照 landscape）；**固定向量瓶頸**——把整個輸入句壓成一個固定維度向量，長句資訊被擠爆（「把一本書摘要成一句話再翻譯」）；RNN 的循序依賴（無法平行、長程依賴衰減）一句帶過；Graves 2013/2014 的可微分注意力/記憶雛形（伏筆 ch18，一段帶過）。
- **不涵蓋**：RNN/LSTM 內部機制（一句帶過、非本書主題）；注意力的解法（ch03）；O(n²)（ch07/ch14）。
- **橋接**：固定向量瓶頸＝你把一個富物件硬塞進固定大小的 protobuf／固定長度欄位，長資料被截斷；RNN 的循序依賴＝沒法平行化的 pipeline，前一步沒算完下一步動不了（這正是注意力後來「全部位置一次算」的對照）。
- **Worked example**：用脊椎句子示範瓶頸——把整句壓成一個向量後，decoder 要還原 it 指代需要的資訊已被稀釋；對照「如果能回頭看原句每個詞」會多容易（預告 ch03 對齊）。
- **紙上推演**：估計「把長度 n 的句子壓成固定 d 維向量」在 n 很大時會丟什麼；舉一個你系統裡「固定大小緩衝塞可變大小資料」的翻車；口頭講為什麼循序依賴讓 RNN 難平行。

### ch03 — 第一次注意：Bahdanau 的對齊（加性與乘性）
- **目標**：能講出第一個 NMT 注意力（Bahdanau 2014）如何用「動態加權源句」打破瓶頸、加性與乘性評分的差別，並認出這就是三步骨架的第一版。
- **必涵蓋**：Bahdanau 2014「對齊模型」——decoder 生成每個目標詞時對源句各位置算權重、加權混合（照 landscape；**首篇命名 attention mechanism**）；加性評分 `vᵀtanh(W[s;h])`；Luong 2015 的乘性/dot-product 評分與 global vs local（照 landscape）；**把它對到三步骨架**：打分（對齊分數）→正規化（softmax）→混合（加權源向量）——本書主骨架第一次完整現身；⚠️ 發明歸屬照 landscape（Bahdanau 確立、Graves 更早雛形、Schmidhuber 爭議，不選邊）。
- **不涵蓋**：self-attention（ch07，本章是 decoder 看 encoder 的 cross 形態雛形）；scaled dot-product 與 √d（ch04/ch06）；多頭（ch08）。
- **橋接**：對齊＝翻譯時「目標詞回頭查源句哪幾個詞最相關」，就像你做資料映射時動態查對應表，而不是套死的固定 schema。
- **Worked example**：一個迷你翻譯對齊——3 詞源句、生成 1 個目標詞，給三個對齊分數，softmax 成權重，加權混合源向量；標出這三步＝三步骨架。
- **紙上推演**：把加性與乘性評分各算一次同一組向量、比較；解釋「對齊」為何比固定向量好；指出這個雛形與後面 self-attention 的差別（誰看誰）。

---

## Part II — 三步骨架：注意力的核心機制（ch04–08）

### ch04 — Query、Key、Value：把注意力看成軟性字典查找
- **目標**：能講清楚 Q/K/V 三個角色各自在做什麼、為什麼 query 和 key 要用**不同**的學來投影、內積為何是「打分」，並親手算出脊椎 it 的原始分數。
- **必涵蓋**：**軟性字典查找**核心隱喻——硬 hash map 是「key 精確命中就取那個 value」，注意力是「query 對每個 key 算相似度、按相似度**混合所有** value」；Q/K/V 是同一批向量經三個**學來的**投影矩陣 W_Q/W_K/W_V 得到（補 ML 鷹架：權重矩陣是訓練學出的）；為什麼 query≠key 用不同投影——「我在找的」與「我是的」是兩件事（非對稱）；**內積即相似度**（指向《矩陣是動詞》ch15）＝三步骨架的「打分」步；脊椎 it 算 raw 分數 [4,2,0]。本章與 ch05–07 用**單頭視角**，維度直接叫 d=4、√d=2，**避免在多頭之前混入 d_k=d_model/h 的拆分**（留 ch08）。
- **不涵蓋**：softmax 正規化（ch05）；√d 縮放（ch06）；self vs cross（ch07/ch12，本章用脊椎單一 query 講清角色）。
- **橋接**：Q/K/V ＝ Redis 的「查詢條件 / 索引鍵 / 存的值」，但查找是軟的；query≠key ＝ 你查 DB 時「WHERE 條件」和「被索引的欄位」經過不同轉換；混合所有 value ＝ 不是取一筆、是按相關度加權所有筆。
- **Worked example**：脊椎 it（基準）——給 q_it 與三個 k，手算三個內積得 [4,2,0]；對照若 W_Q=W_K（query=key）會發生什麼（每個 token 最像自己，退化）。**可選**附 5 行 numpy 算 `Q @ K.T`。
- **紙上推演**：手算一組新向量的 Q·K 分數；用「我找的≠我是的」解釋為何要兩個投影；把 attention 與 hash map 的差別寫成三點對照。

### ch05 — softmax：把分數變成「該看哪裡」的權重
- **目標**：能講出 softmax 在三步骨架的「正規化」步做什麼（把任意分數變成和為 1 的權重分布＝soft-argmax）、溫度如何控制銳利度，並用脊椎完整跑完一次三步骨架。
- **必涵蓋**：softmax 公式與性質（非負、和為 1、放大差距）；**soft-argmax**——硬 argmax 只挑最大值（不可微、只看一個），softmax 是它可微分的「軟」版（按比例看全部，能訓練）；輸出是一個**機率分布**（呼應《馴服隨機》）；**溫度**——除以 T，T→0 趨硬 argmax、T→∞ 趨均勻；脊椎（**用未縮放分數**，縮放留 ch06）：softmax([4,2,0])=[0.867,0.117,0.016]→加權混合 V→輸出≈(0.883,0.133)，**三步骨架第一次完整跑完**；attention 不是「找最相關的一個」是「混合全部、相關的權重大」（招牌反直覺）。
- **不涵蓋**：為什麼分數要先除 √d（ch06，本章先用未縮放分數把骨架跑完）；多頭（ch08）；softmax 替代品（ch19）。
- **橋接**：softmax＝把一排「相關性原始分」正規化成「注意力預算的百分比分配」（像把各服務的權重正規化成流量配比）；溫度＝你調 sampling 的 temperature 時動的同一個旋鈕。
- **Worked example**：脊椎（基準）——手算 softmax([4,2,0]) 全步驟（e⁴,e²,e⁰、求和、相除）得 [0.867,0.117,0.016]，再加權混合 V 得輸出≈(0.883,0.133)；換溫度 T=0.5 與 T=2 各重算一次看權重變尖/變平。
- **紙上推演**：手算 softmax([4,2,0])（注意它很尖、最大權重 0.867）；解釋「attention 混合全部而非取一筆」並反駁「注意力就是找最相關的詞」；用溫度說明「為什麼同一組分數可以又尖又平」（口頭預測：把分數整體縮小，會更尖還是更平？為 ch06 鋪）。

### ch06 — 為什麼除以 √d：一個防止注意力崩掉的小數字
- **目標**：能講清楚 scaled dot-product 為何要除以 √d_k（變異數論證）、不除會怎麼壞（softmax 飽和、梯度消失），並用脊椎數字看出縮放前後的差別。
- **必涵蓋**：**變異數論證**（照 landscape §2 原文）——q、k 各分量獨立、均值 0 變異 1 時，內積 q·k 的變異數 = d_k；d_k 大則分數分布變寬，把 softmax 推進**飽和區**（一個權重→1、其餘→0），梯度趨近 0、學不動；除以 √d_k 把變異數拉回 ~1；脊椎對照：未縮放 [4,2,0]→[0.867,0.117,0.016]（尖，回收 ch05）vs 縮放 [2,1,0]→[0.665,0.245,0.090]（軟，**本章宣告為 ch07 起全書正典脊椎權重**、輸出 (0.755,0.335)）；原始 Transformer d_k=64→√d_k=8（照 landscape）；**故障模式**：softmax 飽和＝梯度消失（接 ch13 為何還需殘差）。
- **不涵蓋**：完整反向傳播數學（指向《馴服無限》梯度）；其他正規化（LayerNorm 留 ch13）。
- **橋接**：除以 √d＝你做數值穩定時的縮放/正規化（避免 overflow、避免某一項主宰）；softmax 飽和＝你看過的「某權重吃掉全部、系統失去調節能力」。
- **Worked example**：脊椎（基準）——並排算 softmax([4,2,0]) 與 softmax([2,1,0])，看尖 vs 軟；假設 d_k=64、分數量級 ~8 倍，示範不除會把 softmax 壓到接近 one-hot（梯度近 0）。
- **紙上推演**：用變異數論證解釋「為什麼是 √d_k 不是 d_k」；手算一組大分數不縮放的 softmax 看它多接近 one-hot；口頭講「softmax 飽和為何讓模型學不動」。

### ch07 — 自注意力：每個 token 都是一次查找（O(n²) 的源頭）
- **目標**：能講出 self-attention 與 ch03 cross 形態的差別（Q/K/V 同源）、為什麼「每個 token 都對所有 token 查一次」必然是 O(n²)，並讀懂矩陣形式 QKᵀ。
- **必涵蓋**：self-attention——Q、K、V 都來自同一序列（每個 token 既是查詢者也是被查者）；整個注意力矩陣 QKᵀ 是 n×n（每格＝一對 token 的相似度）；**O(n²) 從這裡來**（n 個 query × n 個 key）——接《從後端到 AI Infra》ch03「一張沒有索引、每筆新資料對全表 full scan」的講法（本書講原理、那本講記憶體）；脊椎三 token 的完整 3×3 注意力矩陣與熱圖；雙向（每個 token 看全部）的威力——一次抓全句關係。
- **不涵蓋**：masking（ch11，本章先講雙向全看）；多頭（ch08）；O(n²) 的省法（Part IV）；KV cache（指向工作書）。
- **橋接**：self-attention＝把序列做一次「all-pairs 相似度比對」，就像你對 N 筆資料做 N×N 的兩兩比對（沒有索引時的 O(n²)）；雙向＝你能同時看上下文兩邊，不像 streaming 只能看過去。
- **Worked example**：脊椎（基準）——算完整 3×3 注意力矩陣（每個 token 當 query 對三個 key），畫 ASCII 熱圖（看出 it 那列在 animal 欄最濃）；數出對長度 n 要算 n² 個分數。
- **紙上推演**：手算一個 3 token 序列的完整注意力矩陣；解釋為何 self-attention 是 O(n²) 而 RNN 是 O(n)；把 self-attention 對到你熟的「N×N 兩兩比對」場景並估計 n=1000、n=10⁴ 的成本。

### ch08 — 多頭注意力：為什麼要很多顆頭
- **目標**：能講出多頭注意力在做什麼（在不同子空間平行做多次注意力再 concat）、為什麼一顆頭不夠，並用脊椎看出不同頭抓不同關係。
- **必涵蓋**：把 d_model 切成 h 顆頭、每顆頭各有 W_Q/W_K/W_V 投影到 d_k=d_model/h 維（原始 h=8、d_k=64，照 landscape）；每顆頭在**不同子空間**做完整三步骨架、輸出 concat 再過 W_O；為什麼多頭——一顆頭的 softmax 只能聚焦一種關係，多頭讓模型同時抓句法、指代、位置…等多種關係（接 ch21 不同頭的專門化、Voita 2019）；脊椎：head A 抓「誰是主詞」、head B 抓「it→animal 指代」，concat 後 it 同時得到兩種資訊。
- **不涵蓋**：頭的可解釋性深入（ch20/ch21）；MQA/GQA 的 KV 共享（ch16）；頭剪枝（ch20 點到）。
- **橋接**：多頭＝把一個查詢拆成多個專門化的子查詢平行跑（像對同一批資料用多個不同索引同時查），各看一個面向再合併；concat＝把多路結果接起來。
- **Worked example**：脊椎（基準）——把 4 維拆成 2 顆頭×2 維，給兩組小投影，head A 與 head B 各算自己的注意力權重（一個偏 animal、一個偏別處），concat 出最終向量。
- **紙上推演**：解釋「為什麼一顆頭的 softmax 限制了它只能聚焦一種模式」；手算把 d=4 拆成 2 頭後每頭的維度與參數量；舉例你會想要哪幾種「頭」來理解一個句子。

---

## Part III — 補上缺的零件：位置、遮罩、跨序列、一整層（ch09–13）

### ch09 — 位置編碼：集合沒有順序這個洞
- **目標**：能講出 self-attention 本質是**集合**運算（置換不變、看不見順序）、這為什麼是個必須補的洞，並讀懂正弦位置編碼。
- **必涵蓋**：**置換不變性**——attention 對輸入順序無感（重排 token 只重排輸出、權重不變），所以「animal street it」與「it street animal」對模型一樣（脊椎示範）；這是必須**外加位置資訊**的根本原因（呼應 ch19 集合運算的理論）；**正弦位置編碼**（Vaswani 2017 公式照 landscape）——不同頻率的 sin/cos，動機是「相對位置可由線性關係表示」「可外推」；可學習絕對位置（BERT/GPT-2）對照。
- **不涵蓋**：RoPE 與相對位置（ch10）；長度外推細節（ch10 點到）；為何置換不變的嚴格證明（ch19）。
- **橋接**：置換不變＝你的 set/bag 資料結構沒有順序；要表達順序就得**顯式加一個欄位**（序號/timestamp）——位置編碼就是給每個 token 蓋一個「位置戳記」。
- **Worked example**：脊椎（基準）——把 [animal,street,it] 重排成 [it,street,animal]，示範 it 對各 token 的注意力權重**完全不變**（證明看不見順序）；算正弦位置編碼前兩個位置、前幾維的數值。
- **紙上推演**：證明「不加位置時 attention 對輸入置換等變」；解釋正弦編碼「相對位置＝線性關係」的直覺；把「給無序集合加順序」對到你加 timestamp/序號的經驗。

### ch10 — 旋轉的位置：RoPE 與相對位置之美
- **目標**：能講出 RoPE 如何用「旋轉」編碼位置、為什麼旋轉後內積只剩相對位置，並把它接回《圓的影子》的旋轉與複數。
- **必涵蓋**：RoPE（Su 2021，照 landscape）——把 q、k 依**位置**旋轉一個角度（每對維度一個旋轉平面、角度隨頻率變）；關鍵之美：兩個旋轉後向量的內積**只依賴相對位置**（角度差），絕對位置自動消去——**直接接《圓的影子》ch05 旋轉矩陣 R(a)R(b)=R(a+b)、ch07–08 複數與 e^{iθ}**；對照正弦編碼（加在 embedding 上）vs RoPE（旋轉 q/k）；ALiBi（線性偏置，Press 2021）一節；**外推失效**（故障視角）——超出訓練長度時注意力分數失真／注意力熵爆，模型「看不懂」更長的位置，這正是 Position Interpolation / YaRN 要救的（理論直覺，章節作者查證 landscape §3）；長度外推（PI/YaRN）一瞥；⚠️（2026-06）RoPE 是主流開源 LLM 事實標準（照 landscape）。
- **不涵蓋**：旋轉矩陣與複數本身（指向《圓的影子》，本書只用結論）；YaRN 數學細節（一句＋延伸）；位置編碼對 KV cache 的系統影響（指向工作書）。
- **橋接**：旋轉編碼＝你用「相位」表達相對關係（像訊號處理裡的相位差）；相對位置自然浮現＝你只關心「差幾步」而非「絕對在第幾格」。
- **Worked example**：用 2 維手算——把一個 k 向量在位置 m 旋轉角度 mθ、把 q 在位置 n 旋轉 nθ，算內積看到它只依賴 (n−m)（引用《圓的影子》R(a)R(b)=R(a+b)）；脊椎：給 it 與 animal 加上位置旋轉，看相對距離如何進入分數。
- **紙上推演**：用旋轉矩陣性質證明「RoPE 內積只依賴相對位置」；解釋 RoPE 與正弦編碼「加在哪」的差別；口頭講「為什麼旋轉是編碼位置的漂亮辦法」（接 trig 書）。

### ch11 — 遮罩：只能看過去
- **目標**：能講出 causal mask 為什麼存在（保自迴歸）、怎麼實作（softmax 前設 −∞）、padding mask 的用途，並區分雙向 encoder 與單向 decoder。
- **必涵蓋**：**因果遮罩（causal mask）**——生成時第 i 個 token 只能看 ≤i 的 token（不能偷看未來），實作是把非法位置的分數在 softmax 前設 **−∞**（softmax 後變 0，照 landscape §2）；**注意力流向的單向不對稱**（脊椎：it 看得到左邊的 animal，但 animal 看不到右邊的 it——ch07 雙向的對稱在此被打破，明寫這個轉折）；自迴歸生成的循序性（每次預測下一個）；**padding mask**（把補齊用的空 token 遮掉）；雙向（encoder，看全句）vs 單向（decoder，只看左邊）——對應 ch13 三種模型；脊椎：生成 it 時它合法地看左邊的 animal/street。
- **不涵蓋**：KV cache（生成時快取已算的 K/V，指向《從後端到 AI Infra》ch05）；具體 sampling（指向工作書 ch03）；三種模型的完整譜系（ch13）。
- **橋接**：causal mask＝append-only log／event sourcing——你只能讀「已發生」的事件、讀不到未來；設 −∞＝把非法連結的權重歸零（像 ACL 把無權限的列濾掉）。
- **Worked example**：脊椎（基準）——對 3×3 注意力矩陣套上因果遮罩（上三角設 −∞），重算每列 softmax，看每個 token 只在自己與左邊分配權重；對照無遮罩（雙向）的差別。
- **紙上推演**：手算加 causal mask 後的注意力矩陣；解釋「設 −∞ 而不是設 0」為什麼對（softmax 前 vs 後）；把 causal mask 對到 append-only log 並說它如何保證「不偷看未來」。

### ch12 — 交叉注意力與三種注意力
- **目標**：能講清楚 self / masked-self / cross 三種注意力各自誰看誰、cross-attention 如何跨序列查找，並把脊椎升級成翻譯場景。
- **必涵蓋**：三種注意力（照 landscape §2）——① encoder self（Q/K/V 同源，雙向）；② decoder masked self（單向，ch11）；③ **encoder-decoder cross**（Q 來自 decoder、K/V 來自 encoder，讓目標端每個位置看遍源端）；cross-attention 回扣 ch03 Bahdanau（那其實就是 cross 的雛形）；脊椎翻譯版：中文目標 query 去看英文源 K/V；cross-attention 在多模態/擴散的角色一瞥（CLIP/Stable Diffusion 用 cross 注入條件，照 landscape §8，一段帶過）。
- **不涵蓋**：完整 encoder-decoder 架構（ch13）；多模態深入（一句＋延伸）；diffusion 機制（一句＋延伸）。
- **橋接**：cross-attention＝跨兩張表的 JOIN（目標表的列去查源表）；self-attention＝同一張表的 self-JOIN；三種注意力＝三種「誰查誰、能查到哪」的權限組合。
- **Worked example**：迷你翻譯——2 詞源句（encoder 輸出 K/V）、decoder 生成 1 個目標詞（Q），算 cross-attention 權重與輸出；對照 self-attention（同源）的差別。**脊椎在此從 3×3 變成矩形（目標×源）矩陣**——明寫這個轉換（兩序列長度可不同，不再能套原本的方陣），這是脊椎升級成雙序列的關鍵一步。
- **紙上推演**：把 self/masked-self/cross 三者用「誰當 Q、誰當 K/V、能不能看未來」做成對照表；解釋 cross-attention 與 ch03 Bahdanau 的關係；舉一個 cross-attention 注入條件的應用（如文字控制生圖）。

### ch13 — 一整層到一整個模型：注意力住在哪裡
- **目標**：能講出注意力在一層 transformer 裡的位置（配殘差、LayerNorm、FFN）、為什麼需要殘差與 FFN，並認得 encoder-only / decoder-only / encoder-decoder 三種模型家族。
- **必涵蓋**：一層 transformer block＝（多頭注意力＋殘差＋LayerNorm）→（FFN＋殘差＋LayerNorm）（照 landscape §2 結構）；**ML 鷹架**：殘差連接是什麼（直通捷徑）、LayerNorm 是什麼（穩定數值）、FFN 是什麼（逐位置的非線性）——點到為止；**為什麼需要殘差與 FFN**：純堆 attention 會**秩坍縮**（Dong 2021，輸出退化成秩 1）——伏筆 ch19，殘差與 FFN 正是解藥；堆疊 N 層（原始 N=6）；**三種家族**：encoder-only（BERT，雙向，理解）、decoder-only（GPT，單向，生成——**今日主流 LLM 形態**）、encoder-decoder（T5，翻譯/摘要）；訓練目標鷹架（next-token 預測＋交叉熵，一句帶過、指向《馴服隨機》《馴服無限》）。
- **不涵蓋**：反向傳播與訓練工程（全域不涵蓋）；秩坍縮的數學（ch19）；具體模型細節與排行榜（全域不涵蓋）；推論部署（指向工作書）。
- **橋接**：一層 block＝一個處理 stage（attention 做混合、FFN 做逐位置轉換、殘差＝旁路、LayerNorm＝穩壓）；堆疊 N 層＝你的多層 pipeline；三種家族＝三種「讀/寫/讀寫」的服務形態。
- **Worked example**：把 ch08 多頭脊椎輸出接上殘差（加回輸入）與一個迷你 FFN，走完一層 block；用一個小例子示範「純 attention 多層後輸出趨同（秩坍縮）」、加殘差後不再趨同。
- **紙上推演**：畫出一層 transformer block 的資料流（標出殘差/LayerNorm/FFN）；解釋「為什麼純堆 attention 不夠、需要殘差與 FFN」；把 BERT/GPT/T5 用「雙向?／看未來?／用途」做對照表。

---

## Part IV — 為什麼是 O(n²)：效率與它的代價（ch14–16）

### ch14 — 二次方瓶頸：一張建不了索引的表
- **目標**：能講清楚 O(n²) 的代價在長 context 下如何爆炸、為什麼 attention 是「一張建不了索引的表」，並理解後面所有高效注意力的共同動機。
- **必涵蓋**：O(n²) 的精確來源（ch07 的 n×n 矩陣）；長 context 下計算與記憶體的平方成長（n=1k→100 萬格、n=100k→100 億格）；**「沒有索引的全表掃描」**——hash/B-tree 索引靠「可排序/可雜湊的鍵」把查找降到 O(log n)/O(1)，但 attention 的「相似度」不是這種鍵，無法預先建索引、每對都要算（接《從後端到 AI Infra》ch03，本書講原理、那本講記憶體與 roofline）；這是 Part IV 與 ch22（SSM）的共同動機。
- **不涵蓋**：具體省法（ch15/ch16）；KV cache 記憶體工程（指向工作書 ch05）；SSM（ch22）。
- **橋接**：O(n²)＝你最怕的「沒加索引的 N+1 query / 兩兩比對」，資料一大就爆；「建不了索引」＝相似度查找不像等值查找能靠 hash/B-tree 加速。
- **Worked example**：算 n=512、4k、100k 時注意力矩陣的格數與相對成長；對照 RNN 的 O(n) 線性成長；估計「context 長 10 倍、注意力成本變幾倍」。
- **紙上推演**：解釋「為什麼相似度查找建不了傳統索引」；把 O(n²) 對到你遇過的全表掃描翻車；列出「想加速 O(n²)」的兩個直覺方向（少算一些對 vs 換個算法）——預告 ch15/16。

### ch15 — 給注意力建索引：稀疏與線性注意力
- **目標**：能講出稀疏注意力（少算一些對）與線性注意力（換掉 softmax 用結合律）兩條路各動了三步骨架的哪一步、它們是近似、各自的取捨。
- **必涵蓋**：**稀疏注意力**（改「打分」的連結結構）——只算部分 token 對（local 窗口＋少數全域），Sparse Transformer O(n√n)、Longformer/BigBird 線性（照 landscape §4）；**線性注意力**（改「正規化」）——把 softmax(qkᵀ) 換成核函數 φ(q)φ(k)ᵀ，靠**矩陣乘法結合律**把 (QKᵀ)V 重排成 Q(KᵀV)，O(n²)→O(n)（Transformers-are-RNNs、Performer、Linformer，照 landscape）；**低秩**直覺接《矩陣是動詞》SVD/低秩（ch19–20）；取捨：這些是**近似**，省了成本但常損精度（尤其 token 級精確回憶）——伏筆 ch22 為何混合架構保留少量 softmax。
- **不涵蓋**：每個變體的完整公式目錄（點名＋想法即可）；FlashAttention（ch16，那是精確不是近似）；SSM（ch22）。
- **橋接**：稀疏＝你只比對「鄰近/重點」的資料而非全部（局部性假設）；線性注意力的結合律＝你把 (A·B)·C 改成 A·(B·C) 來省一個大中間矩陣——同一招你在查詢優化裡用過。
- **Worked example**：用結合律手算——比較先算 QKᵀ（n×n）再乘 V，與先算 KᵀV（d×d）再被 Q 乘，數出兩者乘法量在 n≫d 時的差距（線性注意力為何省）。
- **紙上推演**：把稀疏 vs 線性各自「動了三步骨架哪一步」說清楚；用結合律證明線性注意力的 O(n)；解釋「為什麼近似注意力會在精確回憶上吃虧」。

### ch16 — 不近似也能省：FlashAttention 與 KV 共享
- **目標**：能講出 FlashAttention 為何是**精確**注意力卻更省（online softmax＋分塊、不實體化 n×n）、MQA/GQA/MLA 的 KV 共享想法，並認得這一章正是「原理書／工作書」的邊界線。
- **必涵蓋**：**最小硬體直覺（全書唯一一次碰記憶體牆，只為動機、不教部署）**——一句話交代：推論時 attention 常是 memory-bound（瓶頸在搬資料、不在算），GPU 的 SRAM 快但小、HBM 大但慢，KV 要被反覆讀；這正是 FlashAttention 與 KV 共享想救的痛。**僅止於動機**——怎麼在 H100 上吃滿頻寬、KV 記憶體怎麼配置，**指向《從後端到 AI Infra》ch03/ch05/ch07**。**FlashAttention 的想法**（Dao 2022，照 landscape §4）——不先算出整個 n×n 矩陣再做 softmax，而是**分塊**逐塊算、用 **online softmax**（邊掃邊更新running max 與 running sum）合併，數學上完全等於標準注意力（**精確、非近似**）；online softmax 的遞推接 ch05 softmax 與 ch06 數值穩定（減去 running max 防 overflow）；**KV 共享**：MQA（所有頭共享 K/V）、GQA（分組共享，Llama 2/3 採用）、MLA（DeepSeek 低秩壓縮）——省的是 KV 記憶體/頻寬（照 landscape）；**邊界線**：本章講到「想法」為止，「在 H100 上怎麼吃滿 SRAM/HBM、KV cache 怎麼配置」**指向《從後端到 AI Infra》ch05/ch07**。
- **不涵蓋**：GPU 記憶體階層的**工程細節**與 kernel 優化／roofline（只給一句動機、深度指向工作書 ch02/ch05/ch07）；FlashAttention 各版硬體數字（landscape 有、書中一句帶過）；量化（指向工作書）。
- **橋接**：online softmax＝你做 streaming aggregation（不把全部資料載進記憶體、邊讀邊更新統計量）；KV 共享＝多個 worker 共用一份快取而非各存一份（省記憶體）。
- **Worked example**：online softmax 手算——把脊椎分數 [2,1,0] 分兩塊（[2,1] 與 [0]）逐塊更新 running max/sum，合併出與一次算相同的 [0.665,0.245,0.090]，證明分塊不損精度。**可選**附 numpy 雛形。
- **紙上推演**：證明「分塊 online softmax 等於整批 softmax」（追蹤 running max/sum）；解釋 FlashAttention「精確不是近似」與 ch15 線性注意力的本質差別；把 MQA/GQA 用「共享什麼、省什麼、損什麼」對照，並標出哪裡該翻去工作書。

---

## Part V — 注意力到底是什麼：理論身世（ch17–19）

### ch17 — 注意力即核迴歸：Nadaraya-Watson 的回歸
- **目標**：能講出 attention 是一種核平滑（kernel smoothing）／核迴歸，softmax 權重＝以相似度為核的加權平均，並看出它與「期望／加權平均」同源。
- **必涵蓋**：Nadaraya-Watson 核迴歸——預測值＝鄰近樣本的加權平均、權重由核函數（相似度）決定；**attention 就是這個**（Tsai 2019「Transformer Dissection」照 landscape §5）：query＝查詢點、key＝樣本位置、value＝樣本值、softmax＝以 exp 內積為核的權重；加權混合＝**條件期望的估計**（接《馴服隨機》加權平均=期望、《馴服無限》）；不同核（線性/RBF/exp）對照、為何 exp/softmax 核好用；嚴謹度標示：這是深刻的**等價視角**（attention 寫得出核迴歸形式），不是巧合。
- **不涵蓋**：核方法完整理論（一句＋延伸）；高斯過程（一句＋延伸）；機率/積分基礎（指向《馴服隨機》《馴服無限》）。
- **橋接**：核迴歸＝你做「用鄰近資料點加權估計目標值」（像 KNN 的加權版、locally weighted）；attention 把這件事變成可學習、可微分、可平行的版本。
- **Worked example**：用脊椎 value 與權重示範——把輸出 (0.755,0.335) 重新解讀成「以相似度為權重對 value 做的加權平均（核迴歸預測）」；給一個 1 維核迴歸小資料手算對照。
- **紙上推演**：把 attention 的三步骨架逐項對到 Nadaraya-Watson 的零件；解釋「softmax 權重＝核」的意思；用「加權平均＝期望」連回《馴服隨機》。

### ch18 — 注意力即聯想記憶：現代 Hopfield 網路
- **目標**：能講出 attention 與現代 Hopfield 網路的等價、為什麼可視為「軟性內容定址的聯想記憶」，並把它接回 ch04 字典查找與 Graves NTM。
- **必涵蓋**：聯想記憶（associative memory）——給一個帶噪/部分線索，檢索出完整存儲模式；**現代 Hopfield 網路**（Ramsauer 2020「Hopfield Networks is All You Need」照 landscape §5）：連續狀態的更新規則**等價於 Transformer attention**；指數級儲存容量、一步檢索；把 K/V 看成「存的記憶」、query 看成「線索」——attention＝軟性內容定址檢索（回扣 ch04 軟性字典、ch02/Graves NTM 的可微分記憶）；溫度/β 控制檢索的「尖銳—模糊」（接 ch05–06）。
- **不涵蓋**：經典 Hopfield 網路的能量函數完整推導（一句＋延伸）；記憶容量定理證明（直覺帶過）；現代 Hopfield 的其他應用（一句＋延伸）。
- **橋接**：聯想記憶＝你用模糊/部分 key 去查一個「容錯的鍵值庫」並取回最像的內容（像模糊搜尋/向量檢索）；attention 就是這種可微分的軟檢索。
- **Worked example**：用脊椎——把三個 token 的 V 當「存的三筆記憶」，q_it 當線索，示範 attention 如何「檢索」出最像 animal 的記憶（高 β/低溫時趨近硬檢索）；對照 ch04 的字典查找隱喻。
- **紙上推演**：把 attention 的 Q/K/V 對到聯想記憶的「線索/位址/內容」；解釋「為什麼提高 β（降溫）讓檢索更像硬查找」；連回 ch04 字典與 ch02 Graves NTM。

### ch19 — 注意力即集合運算：置換等變與訊息傳遞
- **目標**：能講出 attention 是集合上的置換等變運算（回收 ch09 為何要加位置）、它與圖上訊息傳遞的關係、通用近似與秩坍縮，並理解「為何 softmax」與它的替代品。
- **必涵蓋**：**置換等變/不變**的嚴格版（Set Transformer，Lee 2019，照 landscape §5）——attention 把輸入當**集合**處理，這正是 ch09 必須外加位置的根源；與 **GNN／message passing** 的關係（attention＝在全連接圖上學邊權重的訊息傳遞）；**表達力一瞥**——通用近似（足夠頭與維度下可近似序列函數）與**圖靈完備性**（如 Pérez et al. 2019/2021「Attention is Turing-Complete」：加上精度與位置假設後 Transformer 可模擬圖靈機；章節作者查證、明寫前提）；**秩坍縮**（Dong 2021，照 landscape §5）——純 attention 雙指數坍縮到秩 1，回收 ch13「為何需殘差與 FFN」；**為何 softmax**（soft-argmax、合法分布、競爭）與替代品（sigmoid attention/linear/ReLU，Apple 2024 照 landscape，⚠️ 標時點）。
- **不涵蓋**：GNN 完整理論（一句＋延伸）；通用近似定理證明（直覺帶過）；softmax 替代品的 benchmark 大全（一句＋延伸、指向 ch22）。
- **橋接**：集合運算＝你處理無序集合（去重、聚合）時的對稱性要求；訊息傳遞＝節點向鄰居要資訊再聚合（你做的 gossip/聚合協定）；attention＝在「全連接圖」上學出邊權重的聚合。
- **Worked example**：用脊椎證明置換等變（重排輸入、輸出隨之重排、權重不變，回收 ch09）；用一個 3 節點小圖示範「attention＝學出的邊權重訊息傳遞」。
- **紙上推演**：證明 self-attention 的置換等變性；把 attention 與一輪 GNN 訊息傳遞對照；解釋「為什麼 softmax 的競爭性對全域檢索有利」並列一個替代品的取捨。

---

## Part VI — 看進黑盒與它的未來（ch20–23）

### ch20 — 注意力權重是解釋嗎：招牌嘴仗
- **目標**：能講清楚「attention 權重能不能當解釋」的論戰雙方、忠實性 vs 合理性的差別，並把它當全書故障視角的高潮（誠實地說「未定論」）。
- **必涵蓋**：直覺陷阱——很多人把注意力熱圖當「模型為什麼這樣判斷的解釋」；**論戰**（照 landscape §6，⚠️ 未定論）：Jain & Wallace 2019「不是解釋」vs Wiegreffe & Pinter 2019「並非不是解釋」——分歧本質是「解釋」的定義（**忠實性 faithfulness** 模型真的據此決策 vs **合理性 plausibility** 看起來合理）；頭的語言學對應（Clark 2019）與頭專門化/可剪枝（Voita 2019，48 頭剪 38 只損 0.15 BLEU）——有些頭確實有意義、但不等於整體可解釋；自我察覺的徵兆（什麼時候你其實在過度解讀熱圖）。
- **不涵蓋**：機制可解釋性（ch21，那是不同層次的解釋）；具體 faithfulness 評估方法（一句＋延伸）；選邊站（明寫未定論）。
- **橋接**：把熱圖當解釋＝你把「相關性 dashboard」當「因果根因」（ch《馴服隨機》相關≠因果的工程版）；忠實 vs 合理＝你的 log「看起來解釋了 bug」不代表它真是根因。
- **Worked example**：用脊椎熱圖——展示 it→animal 權重最高，討論「這能否證明模型是**因為**看 animal 才解析 it」（呈現雙方論點，不下定論）。
- **紙上推演**：把「attention 是解釋」的四種讀法列出、標出哪些混淆了忠實與合理；解釋 Voita 剪枝結果對「頭是否有意義」說明了什麼；口頭講為何這個問題至今未定論。

### ch21 — 機制可解釋性：QK/OV 電路與 induction heads
- **目標**：能講出 Anthropic 把注意力頭拆成 QK/OV 電路的框架、induction heads 為何是 in-context learning 的機制來源，並把脊椎 it→animal 畫成一個電路。
- **必涵蓋**：**QK/OV 電路**（Elhage 2021「A Mathematical Framework for Transformer Circuits」照 landscape §6）——把一顆頭拆成 **QK 電路**（決定「看哪裡」的注意模式）與 **OV 電路**（決定「把什麼搬過去」的內容）；**induction heads**（Olsson 2022 照 landscape §6）——執行 `[A][B]…[A]→[B]` 的補全（看到 A 就去找上次 A 後面是什麼、複製過來），其出現時機與 **in-context learning** 能力突增同時，是 ICL 的機制源；脊椎：把 it→animal 畫成一個具體的 QK（it 找 animal）/OV（把 animal 的資訊搬給 it）電路；⚠️ Transformer Circuits Thread 非傳統同儕評審（照 landscape）。
- **不涵蓋**：完整迴路代數與張量分解（直覺帶過、指向延伸）；superposition/疊加特徵（一句＋延伸）；可解釋性的所有後續工作（一句＋延伸）。
- **橋接**：QK/OV＝把一個處理器拆成「定址邏輯」與「資料搬運邏輯」（你讀過的 CPU 取址 vs 取數）；induction head＝一個學會「看上次這個 pattern 後面接什麼就照抄」的小程式（像你寫的模式比對/自動補全規則，但是學出來的）。
- **Worked example**：脊椎 it→animal 畫成 QK/OV 電路 ASCII 圖（QK：query「找指代對象」對到 animal；OV：把 animal 的內容寫進 it 位置）；用一個 `[A][B]…[A]→?` 小序列示範 induction head 的補全邏輯。
- **紙上推演**：把一顆頭拆成 QK 與 OV 兩個職責並各舉一例；解釋 induction head 與 in-context learning 的關係；用脊椎畫出 it→animal 的電路。

### ch22 — 注意力之外：SSM、Mamba 與 2026 的混合架構
- **目標**：能講出「為什麼會有挑戰 attention 的新架構」（O(n²) 與 KV 的代價）、SSM↔attention 的對偶之美，並誠實描述 2026-06 的現況（softmax 仍主導、混合是新共識、純 SSM 未稱霸）。
- **必涵蓋**：動機回收——O(n²)（ch14）與 KV cache 的代價（指向工作書）；**SSM 這條線**（照 landscape §7，全標時點）：S4（Gu 2021，HiPPO 數學基礎一句）、Mamba（Gu & Dao 2023，選擇性 SSM、線性時間）、**SSD 對偶**（Mamba-2/「Transformers are SSMs」2024——SSM 是因果線性注意力的特例，對偶之美接 ch15）、Mamba-3（2026，推論優化）；**脊椎在此處「斷」**——SSM 把歷史壓進固定大小狀態、沒有 N×N 注意力矩陣，畫不出 it→animal 的連線；把這個斷裂當鏡子，正照出 SSM 用固定狀態換掉「精確回憶」的代價（資訊漏斗：問題從「it 看哪個 token」變成「漏斗有沒有留住 animal」）——這是脊椎在全書唯一一次刻意失效；**混合架構**（Jamba 2024，約 1/8 層注意力）；**MLA**（DeepSeek，softmax＋低秩 KV）；**⚠️（2026-06）現況**——softmax 仍主導生產級 LLM（GPT-5/Claude/Gemini），新共識傾向「1-in-8~10 注意力層」的混合，**不存在純 SSM 稱霸**，長期勝者未定論；「attention is all you need」這句話 2026 還成立嗎（開放討論）。
- **不涵蓋**：SSM/HiPPO 完整數學（一句＋延伸）；具體模型 benchmark（一句＋指向 landscape）；生產部署與 KV 工程（指向工作書 ch05/ch07/ch17）。
- **橋接**：SSM＝把「記住過去」壓成一個固定大小的狀態（像你維護的 running aggregate / 滑動視窗摘要），O(n) 且 KV 不爆——但壓縮就會丟精確回憶；混合＝你在系統裡「常用路徑走快取、少數需要精確的走全查詢」的同款取捨。
- **Worked example**：用「固定狀態 vs 全序列查找」對照——SSM 用 O(1) 狀態遞推 vs attention 用 O(n) 回看，列出兩者在「精確回憶 vs 成本」的取捨表（標 2026-06）；對偶之美：一句話說明 SSM 如何寫成因果線性注意力（接 ch15）。
- **紙上推演**：解釋「為什麼 SSM 省了 O(n²) 卻在精確回憶上吃虧」；用對偶性把 SSM 連回 ch15 線性注意力；口頭講「2026 年 attention 還是不是 all you need」（要標時點、區分事實與推測）。

### ch23 — 總收官：同一個 it，八層讀法
- **目標**：把全書收進一條能口頭講完的故事線；用七條驗收目標當口試題完成總自我檢核；知道讀完往哪走。
- **必涵蓋**：全書地圖回收（ch01 的圖，現在每格都走過）；**脊椎 it 八層總對帳表**（軟性查找 ch04 → softmax 權重 ch05 → √d 縮放 ch06 → 自注意力矩陣 ch07 → 多頭分工 ch08 → 置換不變要加位置 ch09 → 因果遮罩只看左 ch11 → QK/OV 電路 ch21）；**三步骨架是唯一主角**的回顧——從 Bahdanau 到 RoPE 到 FlashAttention 到 SSM，全是「打分→正規化→混合」的精煉；七條驗收目標各出一題口頭題＋「模範答案要點清單」；故障視角總帳（attention 不是取最相關的一個、softmax 會飽和、位置要外加、熱圖≠解釋、近似會損回憶、純 SSM 未稱霸）；下一步地圖（往理論/往實作/往前沿——對應附錄 C）；明寫本書刻意留的洞（訓練、部署、SSM 數學）與為何留（指向鄰書）。
- **不涵蓋**：任何新概念、新證明；「補完所有遺漏」的誘惑。
- **橋接**：回到 ch01 的你——當時看 it 指代只有直覺，現在能用三步骨架算出來、還能講八層。
- **Worked example**：「注意力原理」10 分鐘口述版逐段大綱（講稿骨架，標每段關鍵詞）；脊椎 it 八層對帳表完整列出。
- **紙上推演**：七條口試題正式作答（口頭、對照要點自評）；給「attention 就是個查表加權平均、沒什麼」這句話寫一段更精準的回應（200 字內）；一年後重讀清單：哪三章值得重讀、各自觸發條件。

---

## 附錄（在全部章節完成後編譯，從實際寫出的內容萃取）

### 附錄 A — 記號與讀法速查表
全書記號總表：寫法、怎麼唸（口述驗收用）、白話意義、首次出現章。涵蓋 Q/K/V、QKᵀ、softmax、√d_k、d_model/d_k/h、αᵢ（注意力權重）、⊙、‖·‖、−∞（遮罩）等。從各章實際用過的記號 grep 彙整。

### 附錄 B — 術語表
EN–ZH–一句話定義–首次出現章。涵蓋 attention/self/cross/multi-head、Q/K/V、scaled dot-product、softmax、positional encoding/RoPE/ALiBi、mask、residual/LayerNorm/FFN、encoder/decoder、O(n²)/sparse/linear、FlashAttention/MQA/GQA/MLA、kernel regression/Hopfield/permutation-equivariance、QK-OV/induction head、SSM/Mamba。從實際內容萃取。

### 附錄 C — 延伸閱讀總地圖
彙整各章延伸閱讀＋landscape 驗證過的資源（論文、部落格、課程、視覺化），分三條路線（往理論/往實作/往前沿），給「如果只看三樣」建議。只收 landscape 或各章已驗證的連結。標出書架鄰書（《矩陣是動詞》《從後端到 AI Infra》《圓的影子》《馴服隨機》《馴服無限》）的銜接點。

## 檔名規範

`chNN-slug.md`：
ch01-where-to-look.md、ch02-fixed-vector-bottleneck.md、ch03-bahdanau-alignment.md、ch04-query-key-value.md、ch05-softmax.md、ch06-scaling-sqrt-d.md、ch07-self-attention.md、ch08-multi-head.md、ch09-positional-encoding.md、ch10-rope-relative.md、ch11-masking.md、ch12-cross-attention.md、ch13-layer-to-model.md、ch14-quadratic-bottleneck.md、ch15-sparse-linear.md、ch16-flashattention-kv-sharing.md、ch17-kernel-regression.md、ch18-hopfield-memory.md、ch19-set-operation.md、ch20-attention-as-explanation.md、ch21-circuits-induction-heads.md、ch22-beyond-attention-ssm.md、ch23-finale.md；
附錄 appendix-a-notation.md、appendix-b-glossary.md、appendix-c-reading-map.md。
