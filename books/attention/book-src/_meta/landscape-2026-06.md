---
last_verified: 2026-06-13
review_after_days: 120
status: research-agent-verified
source: web research 2026-06-13（8 群集 fan-out＋爭議項第二輪覆核，16 agents）
---

# 注意力機制史實與現況基準表（landscape-2026-06）

本檔是《注意力機制的原理》全書「歷史、人物、論文、歸屬、年份、2026 現況」的權威錨點。各章**數學自證**（公式、推導、脊椎數字不靠本檔）；本檔管**外部可驗證的事實**：年份、論文標題、arXiv 編號、作者、發表場合、採用情形、爭議與誤傳。

使用規約：
- 凡引用日期／歸屬／論文，作者請對照本檔，不要憑記憶。
- ⚠️ 標記 = 來源不一致、常被誤傳、爭議未定、或快速演變（尤其 2026 現況）。看到 ⚠️ 請照本檔給的保守版寫，並標時點 `（2026-06）`。
- 來源優先序：arXiv／原始論文／官方會議頁／官方部落格 > Wikipedia > 一般部落格。
- **時效性事實（frontier 章）一律標 `（2026-06）` 並區分「已驗證事實」與「趨勢/推測」。**

---

## 一、前傳：Transformer 之前的注意力（2013–2015）

### seq2seq 與固定向量瓶頸
- **Sutskever, Vinyals & Le 2014「Sequence to Sequence Learning with Neural Networks」**（arXiv 1409.3215，提交 2014-09，NIPS 2014）。三層 LSTM encoder 把整個輸入序列壓成一個**固定維度向量**，decoder 從它解碼；WMT'14 英法達 34.8 BLEU。這個固定向量就是後來注意力要打破的瓶頸。
- **Cho et al. 2014「Learning Phrase Representations using RNN Encoder–Decoder」**（EMNLP 2014，pp. 1724–1734）：encoder-decoder 架構、首次引入 **GRU**。作者含 Cho、Bahdanau、Bengio 等。
- 來源：https://arxiv.org/abs/1409.3215 ；https://aclanthology.org/D14-1179/

### Bahdanau 2014：第一個 NMT 注意力（加性）
- **Bahdanau, Cho & Bengio「Neural Machine Translation by Jointly Learning to Align and Translate」**（arXiv 1409.0473，提交 2014-09，ICLR 2015）。引入「對齊模型（alignment model）」讓 decoder 在生成每個目標詞時**動態加權**源句各隱態，直接解決固定向量瓶頸。加性/加法注意力（additive attention）評分：`score(s, h) = vᵀ tanh(W[s; h])`。
- **這是首篇在 NMT 脈絡正式命名「attention mechanism」的論文。**
- 來源：https://arxiv.org/pdf/1409.0473 ；https://aclanthology.org/D15-1166/

### Luong 2015：乘性/點積注意力
- **Luong, Pham & Manning 2015「Effective Approaches to Attention-based NMT」**（EMNLP 2015，pp. 1412–1421）。提出三種評分：dot-product、general（乘性）、location-based；區分 global vs local attention。**現代 scaled dot-product attention 的乘性形式直接源於此。**
- 來源：https://aclanthology.org/D15-1166/

### Graves 的可微分注意力雛形（更早的一條線）
- **Graves 2013「Generating Sequences With RNNs」**（arXiv 1308.0850）：手寫合成裡用高斯核混合的可微分「位址」機制（可視為注意力雛形）。
- **Graves, Wayne & Danihelka 2014「Neural Turing Machines」**（arXiv 1410.5401）：用可微分注意力讀寫外部記憶——「軟性內容定址記憶體」的直接前身（ch18 Hopfield 會回扣）。
- 來源：https://arxiv.org/abs/1308.0850 ；https://arxiv.org/abs/1410.5401

#### ⚠️ 「誰最早發明 attention」的歸屬
- 現代共識：**Bahdanau et al. 2014** 是「attention mechanism」一詞在 NMT 的正式確立者。Graves 2013 用了可微分注意力但未命名為 mechanism。
- ⚠️ Jürgen Schmidhuber 曾主張其 1991–1992 早期工作（"Fast Weight Programmers"）最早，但查檢其論文並未明確使用該術語。寫作時：歸屬給 Bahdanau 2014（NMT 注意力的確立），可一句話提 Graves 的更早雛形與 Schmidhuber 的爭議，**不選邊**。

---

## 二、Transformer（2017）：原始論文的精確事實

**Vaswani et al. 2017「Attention Is All You Need」**（arXiv 1706.03762，提交 2017-06-12，NeurIPS 2017）。8 位作者：Ashish Vaswani、Noam Shazeer、Niki Parmar、Jakob Uszkoreit、Llion Jones、Aidan N. Gomez、Łukasz Kaiser、Illia Polosukhin。**第一個完全靠 self-attention、不用 recurrence 或 convolution 的轉導（transduction）模型。**

可直接引用的精確事實（全部出自論文，來源 https://arxiv.org/abs/1706.03762 與 HTML 版 https://arxiv.org/html/1706.03762v7 ）：

- **縮放點積注意力**（§3.2.1）：`Attention(Q,K,V) = softmax(QKᵀ / √d_k) V`。
- **為何除以 √d_k**（§3.2.1 腳註）：假設 q、k 各分量獨立、均值 0、變異數 1，則 `q·k = Σ qᵢkᵢ` 的**變異數為 d_k**；d_k 大則內積分布變寬，把 softmax 推進梯度極小的飽和區，故除以 √d_k 把變異數拉回 ~1。（這正是 ch06 的核心，數學自證即可。）
- **多頭超參數**（§3.2.2）：h=8 顆頭，d_model=512，d_k=d_v=d_model/h=**64**。
- **層數**（§3.1）：encoder、decoder 各 N=6 層相同結構；所有 sublayer 與 embedding 輸出皆 d_model=512（為了殘差相加）。
- **FFN**（§3.3）：`FFN(x)=max(0, xW₁+b₁)W₂+b₂`，內層 d_ff=2048。
- **正弦位置編碼**（§3.5）：`PE(pos,2i)=sin(pos/10000^(2i/d_model))`、`PE(pos,2i+1)=cos(pos/10000^(2i/d_model))`；波長從 2π 到 10000·2π 成幾何級數。動機（原文）：對任意固定偏移 k，`PE(pos+k)` 是 `PE(pos)` 的線性函數（利於學相對位置），且**可外推到比訓練更長的序列**。
- **三種注意力**（§3.2.3）：① encoder self-attention（Q/K/V 同源自前一層 encoder）；② decoder **masked** self-attention（把非法（未來）連結在 softmax 前設 −∞ 以保自迴歸）；③ encoder-decoder **cross-attention**（Q 來自 decoder、K/V 來自 encoder 輸出）。
- **歸屬**（致謝）：論文明記 **Noam Shazeer 提出 scaled dot-product attention、multi-head attention 與 parameter-free 位置表示**。
- 結果：WMT'14 英德 big model BLEU **28.4**（新 SOTA、勝前人 >2 BLEU）；英法 **41.0**（訓練成本 <前 SOTA 的 1/4）。訓練：base 100k 步/12 小時、big 300k 步/3.5 天，8×NVIDIA P100；Adam β₁=0.9、β₂=0.98、ε=10⁻⁹、warmup 4000；base dropout 0.1、label smoothing 0.1。

---

## 三、位置編碼的演化（2017–2026）

- **Sinusoidal**（2017，見上）。
- **Learned absolute（可學習絕對位置嵌入）**：**BERT**（Devlin et al. arXiv 1810.04805，NAACL 2019）、**GPT-2**（2019）採用——每個位置一個可訓練向量。
- **Relative position**：**Shaw et al. 2018**（arXiv 1803.02155，NAACL 2018）為每個相對距離 r=j−i 學一個位置嵌入並做距離截斷；**T5**（Raffel et al. 2019）把相對位置簡化為**可學習純量偏置**＋對數分箱 bucket。
- **RoPE（旋轉位置嵌入，Rotary Position Embedding）**：**Su et al. 2021「RoFormer」**（arXiv 2104.09864）。把 q、k 依位置做**二維平面旋轉**（每對維度一個旋轉平面，角度隨位置與頻率變），內積後**相對位置自然浮現**（只看角度差）。**這是 ch10 接《圓的影子》（旋轉/複數/e^{iθ}）的關鍵接點。**
- **ALiBi**：**Press et al. 2021「Train Short, Test Long」**（arXiv 2108.12409）。不動 embedding，直接在 q·k 分數上加一個與距離成正比的**線性偏置**；利於長度外推。
- **長度外推**：Position Interpolation（**Chen et al. 2023**，arXiv 2306.15595，線性縮放位置索引）；NTK-aware（社群起源，⚠️ 無單一正式論文）；**YaRN**（**Peng et al. 2023**，arXiv 2309.00071，ICLR 2024，NTK-by-parts＋注意力溫度）。
- **採用情形（LLaMA 系列）**：LLaMA（arXiv 2302.13971）、Llama 2（2307.09288）均用 RoPE。
- **⚠️（2026-06）現況**：**RoPE 已是主流開源 LLM 的事實標準（de facto standard）**——Llama 2/3、Gemma/Gemma 2、Mistral、Qwen、DeepSeek-V3、GPT-NeoX 等皆採 RoPE 或其變體；ALiBi 採用率遠低。原因：相對、無查表、參數自由、相容 FlashAttention、配 NTK/YaRN 可外推到 256k+。（兩來源覆核 upheld；惟開源版本更新頻繁，標時點。）

---

## 四、效率：O(n²) 瓶頸與次二次方注意力（2019–2024）

標準 self-attention 的時間與空間複雜度皆 **O(n²)**（n=序列長度）——所有高效注意力的共同動機。**系統/部署深度指向《從後端到 AI Infra》（ch03 推論物理、ch05 KV cache、ch07 量化/FlashAttention 系統面）；本書只講「想法」。**

### 稀疏注意力（改「打分」的連結結構）
- **Sparse Transformer**（**Child et al. 2019**，arXiv 1904.10509）：固定稀疏模式（local＋strided），O(n√n)。作者含 Radford、Sutskever。
- **Longformer**（Beltagy et al. 2020）：局部窗口＋任務性全域注意力，線性複雜度，支援 4096 token。
- **BigBird**（Zaheer et al. 2020）：隨機＋滑動窗口＋全域三合一；理論證明保表達力。

### 線性注意力（改「正規化」——把 softmax 換成核技巧，用結合律）
- **Katharopoulos et al. 2020「Transformers are RNNs」**（ICML 2020）：把 attention 寫成核函數線性點積，利用矩陣乘法**結合律**把 O(n²) 降到 O(n)。線性注意力的理論基礎。
- **Performer**（Choromanski et al. 2020，arXiv 2009.14794）：FAVOR+ 隨機特徵近似 softmax 核。
- **Linformer**（Wang et al. 2020，arXiv 2006.04768）：把 K/V 在序列維度投影到低秩 k×d，O(n)。**低秩接《矩陣是動詞》SVD/低秩（ch19–20）。**

### 不近似也能省（精確注意力的工程想法）
- **FlashAttention**（**Dao et al. 2022**，arXiv 2205.14135）：**IO-aware 的精確注意力，不是近似**。分塊（tiling）＋**online softmax**，避免在 HBM 實體化整個 n×n 矩陣，減少 HBM 讀寫。作者 Tri Dao、Daniel Fu、Stefano Ermon、Atri Rudra、Christopher Ré。
- **FlashAttention-2**（2023，arXiv 2307.08691）：改進 warp/thread 分工，比 FA1 約 2×，A100 達 50–73% 理論峰值。
- **FlashAttention-3**（2024-07，arXiv 2407.08608，NeurIPS 2024 Spotlight）：用 Hopper 的非同步與 FP8，H100 BF16 達 840 TFLOPs/s、FP8 達 1.3 PFLOPs/s。
- **本書講 online softmax 的想法（與 ch06 縮放、ch17 加權平均同源），系統面（吃滿 SRAM/HBM）指向工作書。**

### 共享 K/V 頭（省 KV，改「打分」的頭結構）
- **MQA（Multi-Query Attention）**：**Shazeer 2019「Fast Transformer Decoding」**（arXiv 1911.02150）。所有頭共享同一份 K/V、各自 Q，省推論記憶體頻寬。
- **GQA（Grouped-Query Attention）**：**Ainslie et al. 2023**（arXiv 2305.13245，EMNLP 2023）。介於 MQA 與完整多頭之間（分組共享 K/V）；僅用 5% 預訓練算力可從多頭 checkpoint 微調成 GQA；**被 Llama 2/3 廣泛採用**。
- **MLA（Multi-Head Latent Attention）**：**DeepSeek** 開創（DeepSeek-V2 2024-05、V3 2024-12，arXiv 2412.19437）。把 KV 壓到低秩潛在向量，KV cache 每 token 僅 ~70 KB（對比 Llama-3.1-405B 約 516 KB）。⚠️（2026-06）已被 Kimi K2、GLM、Ling 等採用，成 KV 壓縮主流之一。

---

## 五、理論視角：注意力到底是什麼

- **核迴歸（kernel smoothing / Nadaraya-Watson）**：**Tsai et al. 2019「Transformer Dissection: ... via the Lens of Kernel」**（arXiv 1908.11775，EMNLP-IJCNLP 2019）。系統性地把 attention 寫成 **kernel smoother**——以相似度為核的加權平均。**接《馴服隨機》（加權平均=期望）與《馴服無限》。**
- **現代 Hopfield 網路**：**Ramsauer et al. 2020「Hopfield Networks is All You Need」**（arXiv 2008.02217，NeurIPS 2020）。連續狀態的現代 Hopfield 更新規則**等價於 Transformer 的 attention**；可指數級儲存模式、一步檢索——「軟性聯想記憶」（回扣 Graves NTM）。
- **集合運算與置換等變**：**Set Transformer（Lee et al. 2019，ICML 2019，arXiv 1810.00825）**。attention 是集合上的運算——對 query 集合置換等變、對 value 集合置換不變；**位置不是內建的、要外加**（回收 ch09）。與 GNN/message passing（如 Graph Attention Networks）相通。
- **表達力 / 秩坍縮**：**Dong et al. 2021「Attention is Not All You Need: Pure Attention Loses Rank Doubly Exponentially with Depth」**（arXiv 2103.03404，ICML 2021 oral）。**純** self-attention（無殘差、無 MLP）輸出會**雙指數**地坍縮到秩 1；殘差連接與 MLP 正是阻止坍縮的關鍵——解釋了 ch13「為何一層裡需要殘差與 FFN」。
- **softmax 作為 soft-argmax**：softmax 是 argmax 的平滑可微近似——輸出合法機率分布（非負、和為 1）、處處可微（能訓練）、放大分數差形成「軟選擇」。
- **softmax 替代品**：**Sigmoid attention**（**Apple 2024「Theory, Analysis, and Best Practices for Sigmoid Self-Attention」**，arXiv 2409.04431，ICLR 2025）——證明 sigmoid attention 的 Transformer 也是通用近似器，FLASHSIGMOID 在 H100 比 FA2 推論核快 17%；ReLU/Softplus 注意力等亦有研究。⚠️（2026-06）替代品領域演變快，但實證顯示 softmax 在全域競爭/檢索上仍領先，多數混合模型保留 softmax。

---

## 六、可解釋性：注意力權重是「解釋」嗎（爭議議題）

- **「不是解釋」**：**Jain & Wallace 2019「Attention is not Explanation」**（arXiv 1902.10186，NAACL 2019）——大量實驗指注意力權重無法提供可靠解釋。
- **「並非不是解釋」**：**Wiegreffe & Pinter 2019「Attention is not not Explanation」**（arXiv 1908.04626，EMNLP 2019）——反駁取決於「解釋」的定義，需更嚴謹實驗。
- **⚠️ 此論戰至今（2026-06）無共識**：兩派分歧本質是「解釋」定義之爭（忠實性 faithfulness vs 合理性 plausibility），不是事實對錯。2024–2025 研究續指注意力頭多義性、任務相依。寫作時：呈現雙方、明寫「未定論」，當作全書故障視角的高潮，**不選邊**。
- **語言學對應**：**Clark et al. 2019「What Does BERT Look At?」**（arXiv 1906.04341，BlackboxNLP 2019）——某些頭對應句法關係（直接賓語、限定詞、介詞賓語）與共指。**Voita et al. 2019**（arXiv 1905.09418，ACL 2019）——少數「重要頭」扛大部分工作、可剪掉 48 頭中的 38 頭只損 0.15 BLEU。

### 機制可解釋性（Anthropic 的 Transformer Circuits）
- **「A Mathematical Framework for Transformer Circuits」**（**Elhage et al. 2021**，Transformer Circuits Thread，2021-12-22）：把注意力頭分解成 **QK 電路**（決定看哪裡的注意模式）與 **OV 電路**（決定把什麼內容搬過去）。
- **「In-context Learning and Induction Heads」**（**Olsson et al. 2022**，arXiv 2209.11895，Transformer Circuits Thread）：辨識 **induction heads**（執行 `[A][B]…[A]→[B]` 的補全），其出現時機與 in-context learning 能力突增同時，是 in-context learning 的機制來源。**脊椎 it→animal 可畫成一個具體 QK/OV 電路。**
- **⚠️** Transformer Circuits Thread 非傳統同儕評審期刊，但在機制可解釋性領域影響極大；引用時標明性質。

---

## 七、前沿（2026-06）：注意力還必要嗎——SSM、Mamba 與混合架構

> **本節高度時效，全部標 `（2026-06）`，並區分「已驗證事實」與「趨勢/推測」。**

### 狀態空間模型（SSM）這條線
- **S4「Efficiently Modeling Long Sequences with Structured State Spaces」**（**Gu, Goel & Ré 2021**，arXiv 2111.00396，ICLR 2022 Outstanding Paper 榮譽提名）。建在 **HiPPO**（正交多項式投影）數學基礎上；Long Range Arena 全任務 SOTA，首解長度 16k 的 Path-X。
- **Mamba「Linear-Time Sequence Modeling with Selective State Spaces」**（**Gu & Dao 2023**，arXiv 2312.00752，COLM 2024）。選擇性 SSM，序列長度線性時間、約 5× Transformer 吞吐量。
- **Mamba-2 / SSD**：**「Transformers are SSMs ...」**（**Dao & Gu 2024**，arXiv 2405.21060，ICML 2024）。Structured State Space Duality（SSD）證明 SSM 是**因果線性注意力**的特例；Mamba-2 訓練快 2–8×（主要改訓練，非推論）。
- **Mamba-3**（Together.ai，arXiv 2603.15569，**提交 2026-03、ICLR 2026**）：複數值狀態更新、MIMO 變體；同困惑度下狀態減半、1.5B 規模下游平均 +1.8 pt、H100 長序列快 7×；為**推論**優化。

### 混合與生產現況
- **Jamba**（AI21，2024-03-28）：首個生產級**混合 SSM-Transformer**；約 1/8 層為注意力、其餘 Mamba；52B 總/12B 活躍（MoE）、256K context、Apache 2.0。Jamba 1.5（2024-08）：Large 為 398B 總/**94B 活躍**（⚠️ 早期「398B 活躍」是誤植，總參數才是 398B）。
- **MLA**（DeepSeek-V3，見第四節）：softmax 注意力＋低秩 KV 壓縮，2026 生產主流之一。
- **⚠️（2026-06）整體現況（趨勢、非終局）**：**softmax 注意力仍主導生產級 LLM**（GPT-5 系列、Claude、Gemini 等）；**新共識傾向「混合」**——以小比例（如 1-in-8 ~ 1-in-10）注意力層保留檢索能力、其餘用 Mamba/線性層（Qwen、Nemotron、IBM Bamba 等已出貨企業級混合）。**不存在大規模純 SSM 模型稱霸市場**。純 SSM vs 混合 vs 改進 softmax 的長期勝者**未定論**。（兩來源覆核 upheld，標時點。）
- 寫作分界：本書講「為什麼會有 SSM 這條路（O(n²) 與 KV 的代價）、SSM↔attention 的對偶之美、2026 的混合共識」；**生產部署/KV 工程指向《從後端到 AI Infra》**。

---

## 八、NLP 之外的應用

- **Vision Transformer（ViT）**：**Dosovitskiy et al. 2020「An Image is Worth 16x16 Words」**（arXiv 2010.11929，ICLR 2021）。把影像切成 16×16 patch 當 token，純 Transformer 做視覺。
- **CLIP**（OpenAI 2021，arXiv 2103.00020）：4 億圖文對對比預訓練，視覺-語言對齊。
- **Flamingo**（DeepMind 2022，arXiv 2204.14198）：用 cross-attention 處理交錯圖文。
- **Stable Diffusion / Latent Diffusion**（Rombach et al. 2021，arXiv 2112.10752）：用 **cross-attention** 把文字條件注入 U-Net 引導生成（原文：「by introducing cross-attention layers ... powerful and flexible generators for general conditioning inputs such as text」）。
- **AlphaFold2**（Jumper et al., Nature 2021-07-15）：Evoformer 內的 **triangle attention** 處理殘基對。

### ⚠️ 脊椎例子「the animal didn't cross the street because it was too tired」的出處
- **校正（第二輪覆核）**：此代名詞消解例子**不在**原始論文（arXiv 1706.03762）裡，**首見於 Google AI 官方部落格 2017-08「Transformer: A Novel Neural Network Architecture for Language Understanding」**，後經 **Jay Alammar「The Illustrated Transformer」** 廣為流傳。
- 寫作鐵則：**不可說它出自原論文**。要寫「出自 Google 2017 部落格、經 Illustrated Transformer 普及」。
- 來源：https://research.google/blog/transformer-a-novel-neural-network-architecture-for-language-understanding/ ；https://jalammar.github.io/illustrated-transformer/

---

## 九、數值與記號基準複核（脊椎與常用數）

- 脊椎硬數字（與 outline 基準表一致、全書不得矛盾，作者已用 Python 自算複核）：
  - q_it=(1,1,1,1)；k_animal=(2,1,1,0)、k_street=(0,1,1,0)、k_it=(1,−1,0,0)；d_k=4、√d_k=2。
  - 原始內積 QKᵀ = [animal 4, street 2, it 0]。
  - 縮放後 /√d_k = [2, 1, 0]。
  - softmax（縮放）= [animal **0.665**, street **0.245**, it **0.090**]（e²=7.389、e¹=2.718、e⁰=1，和 11.107）。
  - v_animal=(1,0)、v_street=(0,1)、v_it=(1,1) → 輸出 ≈ (0.755, 0.335)（偏向 animal 的 value 方向）。
  - 未縮放 softmax（raw [4,2,0]）= [0.867, 0.117, 0.016]（e⁴=54.598），明顯更「尖」——ch06 的對照。
- 原始 Transformer 常引數：d_model=512、h=8、d_k=d_v=64（√d_k=8）、d_ff=2048、N=6。
- e≈2.71828。所有數值寫章時自算複核，不抄記憶。

---

## 掃描日誌

- **2026-06-13**：建檔。8 群集 web fan-out（origins / transformer-2017 / positional / efficiency / theory / interpretability / frontier-2026 / beyond-nlp）＋爭議項第二輪獨立覆核，16 agents。重大校正：① 脊椎例子出處＝Google 2017 部落格非原論文（已覆核校正）；② Jamba 1.5 Large 為 398B 總/94B 活躍（覆核校正）。爭議標 ⚠️：attention 發明歸屬、attention≠解釋論戰、2026 純 SSM 未稱霸（皆 upheld 為「未定論/趨勢」）。
