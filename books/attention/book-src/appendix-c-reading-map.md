# 附錄 C — 延伸閱讀總地圖

這份附錄把全書 23 章「## 延伸閱讀」段落的連結，加上 landscape 驗證過的資源，去重後攤成一張地圖。它不是把每章的清單抄一遍，而是按「你讀完這本書之後想往哪走」分成三條路線：往**理論**（注意力到底是什麼）、往**實作**（怎麼上手、怎麼看見它）、往**前沿**（2026 的位置編碼、效率、架構之爭）。

讀法約定：每一條都標「為什麼讀、讀哪一段」。資源若是 landscape 錨定過的論文，作者／年份／arXiv 編號照本檔；若是各章已標「（2026-06 查證）」的部落格或教材，我沿用其驗證狀態；沒把握的就明寫「（未逐一驗證 URL）」。前沿那一節的時效性事實一律標時點，並區分「已驗證事實」與「趨勢／推測」——架構之爭到 2026-06 尚無定論，不要把任何一條讀成終局。

全書一再回扣的鄰書銜接點，集中放在最後一節，不在三條路線裡重複。

```text
                    讀完《注意力機制的原理》之後，三條岔路

  往理論（這東西到底是什麼）          往實作（怎麼上手 / 看見它）
  核迴歸 → Hopfield → 集合運算       Illustrated Transformer → Karpathy
  → 表達力 → 可解釋性                → D2L 動手 → 視覺化教材
            │                                    │
            └──────────────┬─────────────────────┘
                           │
                    往前沿（2026 還在動的部分）
              RoPE/YaRN → FlashAttention → SSM/Mamba
                    → 2026 混合架構（趨勢、未定）
```

---

## 路線一：往理論 — 注意力到底是什麼

這條路線回答「三步骨架（打分→正規化→加權混合）究竟是什麼東西」。本書 ch17–ch19 已經把它從三個視角拆開（統計、記憶、集合），這裡給每個視角的原始出處，再加上表達力與可解釋性兩支延伸。

- **Tsai et al. 2019「Transformer Dissection: A Unified Understanding of Transformer's Attention via the Lens of Kernel」**（arXiv 1908.11775，EMNLP-IJCNLP 2019）。ch17 的學術源頭。系統性地把注意力寫成 kernel smoother（核平滑器），並明說放寬了「核需對稱半正定」的要求。讀第 3 節的 kernel 重構，對照本書「加權混合＝條件期望」那條線。https://arxiv.org/abs/1908.11775
- **Dive into Deep Learning,「Attention Pooling: Nadaraya-Watson Kernel Regression」**。把「注意力＝核迴歸」講得最清楚、最動手的一篇教材，ch17 的 1 維房價例子就出自它的高斯核式子；想看「非參數→頻寬可學的參數化」怎麼自然過渡到注意力，讀這篇。https://classic.d2l.ai/chapter_attention-mechanisms/nadaraya-watson.html
- **Ramsauer et al. 2020「Hopfield Networks is All You Need」**（arXiv 2008.02217，NeurIPS 2020）。ch18 的源頭：連續狀態的現代 Hopfield 更新規則等價於 attention，β=1/√d_k。先讀摘要與 Figure 1，再看「Modern Hopfield Networks」那節的更新規則與收斂；容量定理可略過，抓「更新規則＝attention」這個主結論即可。https://arxiv.org/abs/2008.02217
- **ml-jku「Hopfield Networks is All You Need」部落格**。上面那篇論文的官方科普版，把更新規則、β 的作用、三種能量極小（全局平均／亞穩態／單筆）畫成圖（2026-06 查證）；比論文好入口，配 ch18「β 旋鈕」那節讀。ml-jku.github.io/hopfield-layers
- **Krotov & Hopfield 2016「Dense Associative Memory for Pattern Recognition」**（arXiv 1606.01164）。容量從 0.14N 跳成多項式級的轉折，是 Ramsauer 連續版的前一站；想看「坑挖得更尖→存得更多」的數學直覺，讀它的能量函數那節。https://arxiv.org/abs/1606.01164
- **Lee et al. 2019「Set Transformer」**（arXiv 1810.00825，ICML 2019）。ch19 的源頭：把「attention 處理集合」做成正式框架。讀 SAB（置換等變的 self-attention）與 PMA（置換不變的池化）的定義，看「等變零件＋不變池化」如何拼出處理集合的網路。https://arxiv.org/abs/1810.00825
- **Veličković et al. 2017「Graph Attention Networks」**（arXiv 1710.10903，ICLR 2018）。反方向的證據：把 self-attention 搬進圖神經網路，attention 變成「聚合鄰居時的邊權重」。讀引言它怎麼把 attention 定位成 GNN 的訊息傳遞權重——「attention＝學出來的邊權重」這句就坐實了。https://arxiv.org/abs/1710.10903
- **Dong et al. 2021「Attention is Not All You Need: Pure Attention Loses Rank Doubly Exponentially with Depth」**（arXiv 2103.03404，ICML 2021 oral）。表達力的關鍵負面結果，ch06／ch13／ch19 共同回扣。先看 Figure 1（純 attention 雙指數坍縮到秩 1）與摘要主結論，再看它怎麼證殘差與 MLP 阻止坍縮；這是「為何一層裡需要殘差與 FFN」的數學依據。標題故意反 Vaswani 那句，是這領域的標題梗之一。https://arxiv.org/abs/2103.03404
- **Pérez et al.「Attention is Turing-Complete」**（JMLR 2021，v22/20-302）。表達力上限：在任意精度＋無界長度的理想化下，Transformer 可模擬圖靈機。重點不是讀完證明，而是抓住這個結論與它的前提，對照 ch19「有限精度下其實是有限狀態機」的誠實版。（未逐一驗證 URL）
- **Apple 2024「Theory, Analysis, and Best Practices for Sigmoid Self-Attention」**（arXiv 2409.04431，ICLR 2025）。softmax 不是唯一解的代表作：證明 sigmoid attention 的 Transformer 仍是通用近似器，FlashSigmoid 在 H100 比 FA2 推論核快 17%。對照 ch19「sigmoid 放棄了競爭性」這個取捨。⚠️ 替代品領域演變快（2026-06），讀時標時點。https://arxiv.org/abs/2409.04431
- **Jain & Wallace 2019「Attention is not Explanation」**（NAACL 2019，arXiv 1902.10186）。可解釋性論戰的第一拳（ch20）。讀 §3–4 的反事實測試設計（梯度／leave-one-out 對齊、對抗權重），那是「怎麼嚴謹地測一個解釋」的範本，比結論本身更值得學。https://arxiv.org/abs/1902.10186
- **Wiegreffe & Pinter 2019「Attention is not not Explanation」**（EMNLP-IJCNLP 2019，arXiv 1908.04626）。反擊。讀它對「解釋」定義的拆解與「存在不等於排他」那段——這是 ch20「忠實（faithfulness）vs 合理（plausibility）」框架的源頭。⚠️ 此論戰至今（2026-06）無共識，兩派分歧本質是「解釋」定義之爭，不是事實對錯。https://arxiv.org/abs/1908.04626
- **Clark et al. 2019「What Does BERT Look At?」**（BlackboxNLP 2019，arXiv 1906.04341）。某些頭對應到語法關係（直接賓語、限定詞、介詞賓語）與共指的具體證據；也讀它對「砸在 [SEP] 上」的誠實討論——那是 attention sink 的近親。https://arxiv.org/abs/1906.04341
- **Voita et al. 2019「Analyzing Multi-Head Self-Attention」**（ACL 2019，arXiv 1905.09418）。ch08「頭會專門化、但有冗餘」與 ch20「冗餘≠無意義」共同的支柱。讀它怎麼定義「重要頭」與其語言學角色——48 頭剪掉 38 只損 0.15 BLEU 的出處就在這。https://arxiv.org/abs/1905.09418

---

## 路線二：往實作 — 怎麼上手、怎麼看見它

這條路線給「想把直覺變成能跑、能看見的東西」的讀物：原始論文、視覺化圖解、動手教材。本書是原理書，不教 PyTorch 樣板與訓練工程（那些指向《從後端到 AI Infra》），但這裡的視覺化與動手資源能把紙上推演接到螢幕上。

- **Vaswani et al. 2017「Attention Is All You Need」**（arXiv 1706.03762，NeurIPS 2017）。全書反覆引用的原始論文，也是脊椎機制的唯一權威來源。讀完全書再回讀 §3.2（縮放點積與多頭）會豁然開朗：每個符號你都已有白話直覺在旁邊。注意脊椎那個 it 的例句**不**出自本論文（見下方「實作前先記住」）。https://arxiv.org/abs/1706.03762
- **Jay Alammar「The Illustrated Transformer」**。全網最好的 Transformer 圖解入門，本書脊椎句子的視覺化普及來源。先看「self-attention 怎麼讓 it 連到 animal」建立直覺，再看「Self-Attention in Detail」對照 ch04 的 worked example，多頭那節對照 ch08，「Residuals／The Decoder Side」對照 ch12–ch13。讀完全書後當「視覺版的本書」逐章對照（2026-06 仍可存取）。https://jalammar.github.io/illustrated-transformer/
- **Jay Alammar「Visualizing A Neural Machine Translation Model」**。Bahdanau 對齊的互動視覺化，把「生每個目標詞時權重在源句上移動」畫成動畫（ch03）。看一次勝過讀十頁加性注意力。https://jalammar.github.io/visualizing-neural-machine-translation-mechanics-of-seq2seq-models-with-attention/
- **Google AI 部落格「Transformer: A Novel Neural Network Architecture for Language Understanding」**（2017-08）。脊椎那個「it 指代」視覺化例子的原始出處（**不是**原論文）。讀它對「Transformer 解決了什麼」的官方一段話，當作 ch02–ch03「注意力來解決什麼痛」的官方版引子。https://research.google/blog/transformer-a-novel-neural-network-architecture-for-language-understanding/
- **3Blue1Brown「But what is a GPT? / Attention in transformers」（影片）**。把「向量在空間裡被注意力推來推去」動畫化的視覺直覺，適合讀本書前後各看一次，與三步骨架互補（搜尋頻道名稱即可，連結常變動，未逐一驗證 URL）。
- **Sebastian Raschka「Causal Attention」FAQ**。把「為什麼 GPT 不能看未來 token」用最少廢話講清楚，附三角遮罩的圖；和 ch11 的雙向 vs 單向那節互補（2026-06 查證）。https://sebastianraschka.com/faq/docs/causal-attention.html
- **MachineLearningMastery「A Gentle Introduction to Attention Masking」**。把 causal mask 和 padding mask 兩種遮罩放在一起講、附程式，補齊 ch11 padding mask 那節的工程細節（2026-06 查證）。https://machinelearningmastery.com/a-gentle-introduction-to-attention-masking-in-transformer-models/
- **「Why Do We Use Negative Infinity for Masking in Attention?」（Medium, 2026-01）**。專門講「為什麼遮罩用 −∞ 不是 0」這一個點，並提到實作上用大負數（如 float16 的 −65504）避免 NaN——正好對應 ch11 故障表第三列（2026-06 查證）。https://medium.com/@sachinkalsi/why-do-we-use-negative-infinity-for-masking-in-attention-450c59274ac8
- **APXML「Computational Complexity of Self-Attention」**。把 O(n²·d) 的時間與 O(n²) 的空間拆解得很清楚（QKᵀ 是 n×d 乘 d×n、結果 n×n），ch07 複雜度論證的對照讀物。讀它確認「n×n 矩陣」就是平方複雜度的唯一來源。https://apxml.com/courses/foundations-transformers-architecture/chapter-6-advanced-architectural-variants-analysis/self-attention-complexity
- **Michael Brenndoerfer「Attention Complexity: Quadratic Scaling, Memory Limits & Efficient Alternatives」**。把 O(n²) 的時間與空間、長 context 下的記憶體牆拆得很白話的 2026 讀物，對照 ch14 那張 n vs n² 成長表。https://mbrenndoerfer.com/writing/attention-complexity-quadratic-scaling-memory-efficient-transformers
- **EleutherAI「Rotary Embeddings: A Relative Revolution」**。最好讀的 RoPE 直覺文，把「內積只剩相對位置」用複數 e^{i(m−n)θ} 講得乾淨，與 ch10 的旋轉矩陣版互為鏡頭（2026-06 查證）。blog.eleuther.ai/rotary-embeddings

---

## 路線三：往前沿 — 2026 還在動的部分

> 本節高度時效，事實一律標 `（2026-06）`，並區分「已驗證事實」與「趨勢／推測」。架構之爭尚無定論，不要把任何一條讀成終局。

### 位置編碼：RoPE 與長度外推

- **Su et al. 2021「RoFormer: Enhanced Transformer with Rotary Position Embedding」**（arXiv 2104.09864）。RoPE 原始論文（ch10 主角）。讀第 3 節的推導（2 維旋轉、推廣到 d 維、long-term decay），對照本書的證明看原文怎麼用複數寫。RoPE 已是 2026 主流開源 LLM 的事實標準（Llama 2/3、Gemma、Mistral、Qwen、DeepSeek-V3 等皆採其變體）（2026-06，已驗證但開源版本更新頻繁，標時點）。https://arxiv.org/abs/2104.09864
- **Press et al. 2021「Train Short, Test Long: Attention with Linear Biases」（ALiBi）**（arXiv 2108.12409，ICLR 2022）。不動 embedding，直接在 q·k 分數上加與距離成正比的線性偏置，利於長度外推。讀它怎麼用這個極簡想法換到好的外推——ch10 對照表那一格的出處。⚠️（2026-06）ALiBi 採用率遠低於 RoPE。https://arxiv.org/abs/2108.12409
- **Chen et al. 2023「Extending Context Window via Position Interpolation」**（arXiv 2306.15595）與 **Peng et al. 2023「YaRN」**（arXiv 2309.00071，ICLR 2024）。外推失效的兩個主流救法：線性壓縮位置索引（PI）、NTK-by-parts 分頻率＋調注意力溫度（YaRN）。對應 ch10 故障模式那節；配 RoPE 可外推到 256k+（2026-06）。https://arxiv.org/abs/2306.15595 https://arxiv.org/abs/2309.00071

### 效率：精確省搬運與共享 K/V

- **Dao et al. 2022「FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness」**（arXiv 2205.14135）。ch16 主角。標題裡的 **Exact** 與 **IO-Awareness** 就是重點：精確、不是近似，關鍵在減少 HBM 搬運。讀 §3 的分塊（tiling）與 online softmax 推導，對照 ch16 手算的脊椎兩塊例子。FA2（2023，約 2×）、FA3（2024-07，NeurIPS 2024，用 Hopper 非同步與 FP8）的版本數字屬系統面，指向《從後端到 AI Infra》（2026-06 查證）。https://arxiv.org/abs/2205.14135
- **Milakov & Gimelshein 2018「Online normalizer calculation for softmax」**（arXiv 1805.02867）。online softmax 的源頭論文（早於 FlashAttention），把「邊掃邊更新 running max/sum」的遞推講得最乾淨。FlashAttention 是把這想法搬到注意力＋GPU SRAM 上。讀它理解校正因子的數學（2026-06 查證）。https://arxiv.org/abs/1805.02867
- **Shazeer 2019「Fast Transformer Decoding: One Write-Head is All You Need」（MQA）**（arXiv 1911.02150）。所有頭共享一份 K/V、各自 Q，省推論記憶體頻寬。又是一個「X is all you need」梗（ch16）。https://arxiv.org/abs/1911.02150
- **Ainslie et al. 2023「GQA: Training Generalized Multi-Query Transformer」**（arXiv 2305.13245，EMNLP 2023）。分組共享 K/V，在 MQA 速度與 MHA 品質間取折衷；僅 5% 預訓練算力即可從多頭 checkpoint 微調成 GQA——這是它被 Llama 2/3 廣泛採用的原因（2026-06）。https://arxiv.org/abs/2305.13245
- **Tay et al. 2020「Efficient Transformers: A Survey」**（arXiv 2009.06732）。把「對付 O(n²)」的各路線（稀疏、低秩／線性、記憶體／IO）系統性分類的綜述（ch14／ch15）。讀它的分類框架看全景，但注意它是 2020 的快照，之後 FlashAttention 改變了局面。https://arxiv.org/abs/2009.06732
- **稀疏與線性注意力代表作**（ch15）：**Child et al. 2019「Sparse Transformers」**（arXiv 1904.10509，固定 local＋strided 模式，O(n√n)）、**Katharopoulos et al. 2020「Transformers are RNNs」**（ICML 2020，用結合律把 O(n²) 降到 O(n)、自迴歸時變成 RNN 遞推——接 SSM 的伏筆）、**Choromanski et al. 2020「Performer」**（arXiv 2009.14794，FAVOR+ 隨機特徵近似 softmax 核）、**Wang et al. 2020「Linformer」**（arXiv 2006.04768，K/V 投影到低秩，O(n)）。兩條路都是**近似**（用精確回憶換速度），與 FlashAttention 的「不近似也能省」恰成對照（2026-06 查證）。https://arxiv.org/abs/1904.10509

### 架構之爭：SSM、Mamba 與混合

- **Gu, Goel & Ré 2021「Efficiently Modeling Long Sequences with Structured State Spaces」（S4）**（arXiv 2111.00396，ICLR 2022）。SSM 這條線的奠基作，建在 HiPPO（正交多項式投影）數學上。想懂「為什麼固定狀態能記長程」讀它的動機與 Long Range Arena 結果，HiPPO 數學細節可先略過（ch22）。https://arxiv.org/abs/2111.00396
- **Gu & Dao 2023「Mamba: Linear-Time Sequence Modeling with Selective State Spaces」**（arXiv 2312.00752，COLM 2024）。選擇性 SSM，序列長度線性時間、約 5× Transformer 吞吐量。讀「選擇性」那節——B/C 變成輸入的函數，是 Mamba 對 S4 的關鍵一改，對照 ch22「重要 token 多記」的直覺。https://arxiv.org/abs/2312.00752
- **Dao & Gu 2024「Transformers are SSMs: Structured State Space Duality」（Mamba-2/SSD）**（arXiv 2405.21060，ICML 2024）。ch22「對偶之美」的源頭：用半可分矩陣把 SSM 與**線性注意力**接起來（注意接的是線性注意力，不是 softmax）。Mamba-2 主要改訓練（快 2–8×），非推論。https://arxiv.org/abs/2405.21060
- **Together.ai 2026「Mamba-3」**（arXiv 2603.15569，ICLR 2026）。最新一代 SSM：複數值狀態更新（呼應 ch10 的旋轉位置）、MIMO 變體，為推論優化（同困惑度下狀態減半、H100 長序列快 7×）。frontier 資料，讀時標 2026 時點（2026-06，已驗證事實）。https://arxiv.org/abs/2603.15569
- **NVIDIA「Nemotron-H: A Family of Accurate and Efficient Hybrid Mamba-Transformer Models」**（arXiv 2504.03624，2025）。生產級混合的代表，讀「換掉約 92% 注意力層」的設計取捨與吞吐量數字（ch22）。https://arxiv.org/abs/2504.03624
- **AI21 部落格「Attention was never enough: Tracing the rise of hybrid LLMs」**。混合架構的脈絡與動機綜述（Jamba 出身），把「為什麼是混合不是替代」講得最白；搭配 ch22 的 2026 現況節讀（未逐一驗證 URL）。ai21.com
- **⚠️ 2026-06 整體現況（趨勢、非終局）**：softmax 注意力仍主導生產級 LLM（GPT-5 系列、Claude、Gemini 等）；新共識傾向「混合」——以小比例（約 1-in-8 ～ 1-in-10）注意力層保留檢索能力、其餘用 Mamba／線性層（Qwen、Nemotron、IBM Bamba 等已出貨企業級混合）。**不存在大規模純 SSM 模型稱霸市場**。純 SSM vs 混合 vs 改進 softmax 的長期勝者**未定論**。本書講「為什麼會有這條路、SSM↔attention 的對偶之美、2026 的混合共識」；生產部署／KV 工程指向《從後端到 AI Infra》。

---

## 如果只看三樣

時間有限，照你想去的方向各挑一樣，三樣合起來剛好覆蓋「看見它、理解它、追上它」：

1. **看見它 — Jay Alammar「The Illustrated Transformer」**。讀完全書後當「視覺版的本書」逐章對照，每張圖你都指得出對應哪一章、哪一步。把紙上的三步骨架接到圖上，直覺立刻立體。
2. **理解它 — Tsai et al. 2019「Transformer Dissection（核迴歸視角）」**。它把「注意力＝以相似度為核的加權平均」這件事講到根上，是 ch17–ch19「理論身世」三章裡最好的單一入口；讀完你會確信三步骨架是被重新發現的，不是被發明的。
3. **追上它 — Dao & Gu 2024「Transformers are SSMs（SSD 對偶）」**。它把 SSM 與線性注意力縫在一起，是理解 2026 架構之爭的鑰匙；讀它就懂為什麼前沿不是「拋棄注意力」而是「混合」。讀時記得標 2026 時點，現況仍在動。

若連三樣都嫌多：**只讀 Vaswani et al. 2017 原論文的 §3.2**，配著本書當白話注解。讀完全書再回看，每個符號都有直覺在旁——這是全書脊椎機制的唯一權威來源（脊椎那句 it 例句除外，它出自 Google 2017 部落格）。

---

## 書架鄰書銜接點

本書把直覺給足了，運算與系統的深度，在書架上的鄰書等你。以下是全書反覆指向的五個接點，按「往哪個深度走」整理。

| 想往哪個深度走 | 去哪本書 | 接什麼、本書在哪章指過去 |
| --- | --- | --- |
| 線代運算深度 | 《矩陣是動詞》 | 內積即相似度（ch04 打分、ch17 兩種核一家）；矩陣乘法即批量內積與結合律（ch03、ch07、ch15 重排乘法順序）；投影與子空間（ch08 多頭切子空間）；SVD／低秩近似（ch15 Linformer、ch16 MLA、ch21 QK/OV 低秩） |
| 系統與部署 | 《從後端到 AI Infra》 | tokenizer／embedding 進場與「一張建不了索引的表」（ch04、ch14）；KV cache 與管理（ch11、ch13、ch16、ch22）；FlashAttention 系統面、量化、推論物理（ch16） |
| RoPE 的底層 | 《圓的影子》 | 旋轉矩陣 R(a)R(b)=R(a+b) 與複數 e^{iθ}（ch09 相對位置＝旋轉、ch10 RoPE、ch22 Mamba-3 複數值狀態）——全書最漂亮的跨書接點 |
| 機率語義 | 《馴服隨機》 | softmax 輸出是合法機率分布（ch05、ch06、ch20）；加權平均＝期望、條件期望＝迴歸要估的東西（ch17）；溫度與熵、β 是逆溫度、softmax 是 Boltzmann 分布（ch18）；相關≠因果（ch20） |
| 訓練的數學 | 《馴服無限》 | 為什麼可微分才能訓練、梯度下降為何需要斜率（ch05）；梯度消失的完整數學、softmax 的 Jacobian 與反向傳播（ch06、ch17） |

### 實作前先記住：脊椎例句的出處

全書脊椎句子「the animal didn't cross the street because it was too tired」的代名詞消解例子，**不在**原始論文（arXiv 1706.03762）裡。它首見於 **Google AI 官方部落格 2017-08**（〈Transformer: A Novel Neural Network Architecture for Language Understanding〉），後經 **Jay Alammar「The Illustrated Transformer」** 廣為流傳。引用時要寫「出自 Google 2017 部落格、經 Illustrated Transformer 普及」，**不可說它出自原論文**——這是全書反覆強調的一個小而要命的事實。
