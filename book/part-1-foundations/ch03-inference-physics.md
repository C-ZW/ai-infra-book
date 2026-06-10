# ch03 — Transformer 推論的物理學：每個 token 都是一次記憶體掃描

> **本章解決什麼問題**：ch02 給了你 GPU 這台機器的規格表與 roofline 分析工具；本章告訴你跑在上面的工作負載——transformer 推論——到底在算什麼、記憶體怎麼隨對話長大、瓶頸落在 roofline 的哪一側。這章是全書的理論地基：KV cache 大小公式與「prefill compute-bound / decode memory-bound」這兩個結論，會被 ch05（KV 管理）、ch06（batching）、ch10（P/D 分離）、ch13（容量規劃）反覆引用。你不需要會訓練模型，但讀完這章，你要能對任何一個模型的 config.json 心算出它的記憶體帳單。

## 從你已知的出發

你做過 WebSocket 即時系統：每條連線在 Redis 裡掛著一份 per-connection session state，幾 KB，10K CCU 全加起來也就幾十 MB，放哪都行。LLM serving 也是有狀態服務，每條對話掛著一份叫 KV cache 的 state——但它每生成一個 token 就長大幾百 KB，一條 32k context 的對話會長到 10 GB 以上，而且它只能住在整台機器最貴的記憶體（GPU 的 HBM）裡。把「session state」的直覺乘上六個數量級，你就有了本章的核心張力。

你也做過 profiling-driven 的 RDS 優化：下刀之前先分清楚瓶頸是 CPU 還是 IO，因為兩種瓶頸的處方完全不同。本章對 transformer 推論做同一件事——用 ch02 的 arithmetic intensity 證明：推論的兩個階段（prefill 與 decode）一個是 compute-bound、一個是 memory-bound。這個診斷結論不是學術趣味，它直接決定了後面所有章節的系統設計：為什麼要 batching（ch06）、為什麼量化權重能加速 decode（ch07）、為什麼有人把兩個階段拆到不同的 GPU 池（ch10）。

最後一個錨點：attention 機制本質上是「每個新 token 對所有歷史 token 做一次相似度全掃描」。用你的語言說，這是一張沒有索引、也建不了索引的表，每來一筆新資料就 full scan 一次——O(n²) 就是從這裡來的。業界後來想替這張表「建索引」的各種嘗試（sparse attention、linear attention），我們留到章末與 ch17。

## Token：計價與容量的原子單位

模型不讀字，讀 token。Tokenizer 把文字切成一串整數 id，每個 id 對應詞彙表（vocabulary）裡的一個片段。主流做法是 BPE（Byte Pair Encoding）：從位元組層級出發，統計訓練語料中最常相鄰出現的片段並反覆合併，最後得到一張固定大小的詞彙表——Llama 3 系列是 128,256 個條目（查證自 config.json，2026-06）。

三個工程上重要的事實：

1. **token ≠ 字**。英文平均約 3~4 個字元一個 token；中文依 tokenizer 而異，常見是一個字 1~2 個 token。同一段話換一個模型，token 數可以差 30% 以上。
2. **計價用 token 是物理誠實的**。下面你會看到：每個 token 消耗的 FLOPs 與 KV cache bytes 都是固定的，token 是成本的自然原子單位——類比 DynamoDB 用 RU 計價，而不是用「查詢次數」。
3. **tokenize 發生在 CPU**，在請求進入 GPU 之前。這是整條推論鏈路裡少數便宜的步驟，但它定義了後面一切的「n」。

Murphy 提醒：如果你的 gateway 用字元數估配額、引擎用 token 數計費，中文流量會讓兩本帳對不上。量測一律以引擎回報的 `prompt_tokens` / `completion_tokens` 為準。

## 推論時的 transformer：一條 token 的流水線

訓練怎麼回事本書不管。推論時，一個 decoder-only transformer（目前所有主流 LLM 的形態）就是一條固定的流水線：

```
prompt 文字
   │ tokenizer（CPU）
   ▼
token ids [n]
   │ embedding lookup：[n] → [n, 8192]        （查表，把每個 id 換成一個向量）
   ▼
┌─ Layer 1 … 80（每層結構相同，串行通過）──────────────┐
│   RMSNorm → Attention（Q/K/V/O 四個矩陣乘）→ 殘差相加   │
│   RMSNorm → FFN（8192 → 28672 → 8192）     → 殘差相加   │
└────────────────────────────────────────────┘
   ▼
RMSNorm → lm_head：[n, 8192] × [8192, 128256] → logits [n, 128256]
   ▼ 只取最後一個位置的 logits
sampling（temperature / top-p …）→ 下一個 token id → 餵回流水線，迴圈
```

（圖中形狀以 Llama-3.3-70B 為例：hidden size 8192、80 層、詞彙表 128,256。）

幾個對後端工程師重要的觀察：

- **整個模型就是一疊矩陣乘法加上少量逐元素運算**。沒有分支、沒有迴圈依資料而變（MoE 的 routing 是例外，見後文）——這就是它適合 GPU 這種 throughput machine 的原因（ch02）。
- **生成是自迴歸（autoregressive）的**：每次前向傳播只產出「下一個」token，把它接回輸入序列尾端，再跑一次。生成 500 個 token 就是 500 次完整流水線。這個串行依賴是 LLM 推論一切延遲問題的根源——你無法平行生成第 100 個 token 和第 101 個 token。
- **logits 是對整張詞彙表的打分**：一個 128,256 維的向量，sampling 就是從這個分布裡挑一個 id。

### 一層裡面長什麼樣：用矩陣形狀讀懂模型

「讀懂模型架構」對 infra 工程師來說，就是讀懂每層有哪幾個權重矩陣、形狀是什麼。以 Llama-3.3-70B 為例（所有數字查證自官方 config.json，2026-06）：

| 矩陣 | 形狀 | 參數量 | 作用 |
|---|---|---|---|
| W_Q | 8192 × 8192 | 67.1M | 產生 query（64 個 head × 128 維） |
| W_K | 8192 × 1024 | 8.4M | 產生 key（**只有 8 個 head** × 128 維） |
| W_V | 8192 × 1024 | 8.4M | 產生 value（同上） |
| W_O | 8192 × 8192 | 67.1M | attention 輸出投影 |
| W_gate | 8192 × 28672 | 234.9M | FFN（SwiGLU 三矩陣之一） |
| W_up | 8192 × 28672 | 234.9M | FFN |
| W_down | 28672 × 8192 | 234.9M | FFN |
| 每層合計 | | **約 855.6M** | attention 佔 151M（18%）、FFN 佔 704.6M（82%） |

驗算：855.6M × 80 層 ≈ 68.5B，加上 embedding（128,256 × 8192 ≈ 1.05B）與 lm_head（同形狀、不共享，再 1.05B），合計約 70.55B——和官方公布的 70.6B 對上了。能做這個驗算，代表你真的讀懂了 config.json；面試時這是區分「背過名詞」和「懂結構」的試金石。

注意兩件事，後面都會回收：W_K/W_V 窄得反常（1024 而不是 8192），這是 GQA，是 KV cache 一節的主角；FFN 佔每層 82% 的參數，這是 MoE 一節「只稀疏化 FFN 就夠了」的原因。

## Attention：為什麼每個 token 都要回頭看所有歷史

FFN 對每個 token 獨立運算，token 之間互不相見。整個 transformer 裡**唯一**讓不同位置的資訊互相流動的機制就是 attention。它的運作（單一 head、推論視角）：

1. 當前 token 的 hidden state 乘 W_Q 得到 **query** q——「我在找什麼」。
2. 每個歷史 token 都各有一份 **key** k（「我是什麼」）和 **value** v（「我攜帶什麼資訊」），由各自的 hidden state 乘 W_K、W_V 得到。
3. q 與**所有**歷史 token 的 k 做內積、除以 √128、過 softmax，得到一組注意力權重——一次對全部歷史的相似度掃描。
4. 用這組權重對所有 v 加權求和，結果就是「這個 token 從上下文中收集到的資訊」。

Decoder-only 模型帶 causal mask：每個 token 只能看見自己之前的 token。這個約束看似是訓練細節，卻是推論系統的救命恩人——它保證**歷史 token 的 k、v 一旦算出來就永遠不變**（新 token 的加入不影響它們），這正是 KV cache 能存在的前提。

O(n²) 從哪來：序列裡第 i 個 token 要對前 i 個 token 各做一次內積，整段序列就是 1+2+…+n ≈ n²/2 次。沒有索引可建——softmax 之前你不知道哪些歷史 token 重要，所以必須全掃。32k 的 prompt，這項就是 5 億次「行對行」比較，乘上 64 個 head、80 層。長上下文一節會把這筆帳算成秒數。

## KV cache：用記憶體換計算

### 它在解什麼問題

天真的生成方式：每生成一個新 token，把「prompt + 已生成的全部 token」重新跑一遍整條流水線。第 t 步要對 t 個 token 重算 k、v——但我們剛說過，歷史 token 的 k、v 永遠不變。重算是純浪費，而且浪費隨序列長度線性惡化，整段生成合計 O(n²) 次多餘的前向計算。

解法就是你做過一百次的 memoization：把每層、每個 token 的 k、v 向量算一次、存起來。之後每個 decode 步只需要為**一個**新 token 算 q/k/v，再對快取裡的歷史 K、V 做掃描。這份快取就是 **KV cache**。

代價也和所有 cache 一樣：儲存空間，以及隨之而來的失效管理、容量規劃、碎片化問題——後者整整佔了 ch05 一章。先把帳算清楚。

### KV cache 大小公式（全書公式，背下來）

```
KV cache bytes = 2 × n_layers × n_kv_heads × head_dim × bytes_per_param × n_tokens
```

逐項解釋：`2` 是 K 和 V 各一份；`n_layers` 是每一層都要存自己的 KV（attention 在每層獨立發生）；`n_kv_heads × head_dim` 是每層每個 token 的 KV 向量寬度；`bytes_per_param` 是數值精度（BF16/FP16 = 2、FP8 = 1）；`n_tokens` 是這條序列目前的長度（prompt + 已生成）。

前四項相乘就是「**每 token 每條序列的 KV bytes**」——一個模型的固定體質，從 config.json 直接算出來。

### Worked example：Llama-3.3-70B 的 KV 帳單（全書反覆引用）

這是全書最重要的一次計算，一步步來。模型參數（查證自官方 config.json，2026-06）：`num_hidden_layers = 80`、`num_key_value_heads = 8`、`head_dim = 128`、KV 精度 BF16（2 bytes）。

**第一步：每 token 的 KV bytes。**

```
2 × 80 × 8 × 128 × 2 = 327,680 bytes ≈ 320 KiB ≈ 0.33 MB / token
```

**第二步：一條 32k context 的對話。**

```
32,768 tokens × 327,680 bytes = 10,737,418,240 bytes ≈ 10.7 GB
```

一條對話、10.7 GB 的 state。你過去一條 WebSocket session 的 state 是幾 KB——差了七個數量級，而且這 10.7 GB 必須住在 HBM 裡，因為每個 decode 步都要把它整個讀一遍。

**第三步：一張 H100 80GB 能同時服務幾條 32k 對話？**

先把卡上的記憶體分帳。推論引擎通常保留約九成的 HBM 自用（vLLM 的 `gpu-memory-utilization`，預設值隨版本在 0.90~0.92 間演進，見 ch08；本章一律用保守的 0.90 計算），即約 72 GB，這裡面要裝三樣東西：模型權重、activation 工作區（中間計算的暫存，量級 1~3 GB）、KV cache 池。

- 權重 BF16：70.6B × 2 bytes ≈ **141.2 GB**。比整張卡還大，根本裝不進去。單卡 BF16 跑 70B，到此為止。
- 權重 FP8（ch07 會講怎麼來的）：70.6B × 1 byte ≈ 71 GB（實務上 embedding 等少數層不量化，約 72~75 GB）。72 GB 的預算減掉權重再減掉 activation，留給 KV cache 的空間是**零，甚至是負的**。

所以這題的誠實答案是：**0 條**。一張 80GB 的卡塞一個 70B 模型，連一條 32k 對話都服務不了。這個「算出 0」不是例子設計失敗，它就是本章想讓你記住的第一個結論——是這筆帳，而不是任何軟體偏好，逼著 70B 級模型走向多卡。

**第四步：那 2×H100（tensor parallelism，切法見 ch09）呢？**

可用記憶體 2 × 72 = 144 GB；FP8 權重 71 GB 平攤兩卡；activation 與通訊緩衝抓 4 GB。KV 池 ≈ 144 − 71 − 4 ≈ **69 GB**。

```
69 GB ÷ 10.7 GB/條 ≈ 6 條 32k 對話
```

兩張月租上萬美元等級的卡（2026 年年中 neocloud 行情約 $2~3/hr/卡，見 ch16），同時服務 **6 個**長上下文使用者。如果流量是 4k context 的短對話（每條 1.34 GB），同樣的池子能放約 51 條。**並發容量幾乎完全由 KV cache 預算決定，而 KV cache 由使用者的 context 長度決定**——這就是全書主軸一「LLM serving 是 memory 的生意」的第一次具體現身，也是 ch13 容量規劃數學的起點。

> **全書引用的三個數字（Llama-3.3-70B，BF16 KV）**
> - 每 token KV：**327,680 bytes ≈ 0.33 MB**
> - 每條 32k 對話：**≈ 10.7 GB**
> - 2×H100（FP8 權重）的 KV 池 ≈ 69 GB → **約 6 條 32k 並發對話**；單卡 H100 → **0 條**

這筆帳有三個刻意的簡化，方向都偏保守，引用前要知道：
1. **單位**：本章全用十進制 GB 粗算，但實體 HBM 與 `nvidia-smi` 用的是二進制——H100「80GB」實際是約 80 GiB（`nvidia-smi` 報約 8.1 萬 MiB），折合十進制約 85 GB。整筆帳改用 GiB 重算會多擠出約一條（≈7 條）。粗算時混用無妨，**做正式容量規劃時必須統一單位**——GB/GiB 混用是真實世界容量失準的常見來源。
2. **碎片化**：KV 池以 block（常見 16 tokens）為單位配置，每條請求的最後一個 block 平均半空，實際可用容量再打約 95 折（機制見 ch05）。
3. **Activation 抓固定 4 GB** 是 decode 穩態的量級；長 prompt 的 prefill 峰值會更高，引擎會用排程把它壓回去（ch06）。

順帶一提：KV cache 池在引擎裡怎麼切塊、怎麼避免碎片化（PagedAttention），是 ch05 的主題；多條請求怎麼動態進出這個池子（continuous batching），是 ch06 的主題。本章只管「池子有多大、每條對話吃多少」。

### MHA / GQA / MQA / MLA：KV 瘦身的演化史

上面算出的 320 KiB/token 已經是「瘦身後」的數字。公式裡的 `n_kv_heads` 是模型架構設計者手上最大的 KV 槓桿：

- **MHA（Multi-Head Attention）**：原版設計，每個 query head 配一組專屬 K/V。64 個 head 就是 64 組 KV。
- **MQA（Multi-Query Attention）**：走到另一個極端，所有 query head 共享**一組** KV。省 64 倍，但品質損失在大模型上不可忽略。
- **GQA（Grouped-Query Attention）**：折衷方案，把 64 個 query head 分成 8 組，每組共享一組 KV。品質幾乎不掉、KV 省 8 倍，是 2023 年後 dense 模型的業界預設。
- **MLA（Multi-head Latent Attention）**：DeepSeek-V2 提出的路線。不是減少 KV head 數，而是把 KV **壓縮成一個低秩 latent 向量**存起來，用的時候再投影回去。DeepSeek-V3 每層每 token 只存 576 個元素（512 維壓縮 latent + 64 維位置資訊；查證自 config.json，2026-06），而且 K 和 V 共用這一份——公式裡的「2 ×」也消失了。代價是架構必須從預訓練就這樣設計，沒辦法事後改裝到現有模型上。

用同一把尺量（70B 級 dense 假設 80 層 × head_dim 128；MLA 用 DeepSeek-V3 真實數字 61 層 × 576 元素，BF16）：

| 架構 | KV heads | 每 token 每層 | 每 token 全模型 | 一條 32k 對話 | 代表模型（2026-06） |
|---|---|---|---|---|---|
| MHA | 64 | 32 KiB | 2.56 MB | **85.9 GB** | GPT-3 世代 |
| GQA | 8 | 4 KiB | 0.33 MB | **10.7 GB** | Llama 3.x、多數 Qwen dense |
| MQA | 1 | 0.5 KiB | 0.04 MB | **1.3 GB** | Falcon、PaLM |
| MLA | （latent 576 元素） | 1.125 KiB | 0.07 MB | **2.3 GB** | DeepSeek-V2/V3、Kimi K2 |

兩個值得停下來看的點。第一：如果 Llama-70B 還是 MHA，一條 32k 對話的 KV 是 85.9 GB——比一張空的 H100 還大，前面那道題連「0 條」都不用算。GQA 那個 8 倍，是 2024 年後長上下文服務在經濟上成立的前提。第二：DeepSeek-V3 是 671B 參數的模型，每 token 的 KV 卻只有 Llama-70B 的五分之一。**模型架構設計已經把 serving 成本當成一級設計目標**——MLA 不是數學炫技，是衝著 HBM 帳單來的。2026 年的新動向（DeepSeek-V4 的 DSA sparse attention、Qwen3.5 的線性注意力混合）把這條路推得更遠，見章末與 ch17。

還有一個容易忽略的工程事實：**KV cache 只依賴 token 序列本身**，與 temperature 等 sampling 參數無關。兩個 prompt 前綴相同、sampling 設定不同的請求，KV 完全可以共用——這是 ch05 prefix caching 的理論基礎。

## Prefill 與 decode：一個請求、兩種物理

一個推論請求的生命週期分成兩段，物理性質截然不同：

- **Prefill**：把整段 prompt（可能幾千到幾萬個 token）一次性通過流水線，建立全部 KV cache，並產出第一個 token。使用者體感對應 **TTFT**（time to first token）。
- **Decode**：之後一次一個 token 的自迴歸迴圈。體感對應 **ITL/TPOT**（token 間延遲）。

### 用 arithmetic intensity 證明瓶頸在哪

拿出 ch02 的 roofline。H100 SXM 的帳：BF16 Tensor Core 約 989 TFLOPS（dense）、HBM3 頻寬 3.35 TB/s，ridge point ≈ 989e12 ÷ 3.35e12 ≈ **295 FLOP/byte**。workload 的 arithmetic intensity 高於它是 compute-bound，低於它是 memory-bound。

**Decode（batch = 1）**：生成一個 token，要把每個權重矩陣各做一次「矩陣 × 向量」（GEMV）。一個 m×k 的 BF16 矩陣：讀 2mk bytes，做約 2mk FLOPs——**intensity ≈ 1 FLOP/byte**。整個模型加總：約 2 × 70.6B ≈ 141 GFLOPs 的計算，對上約 141 GB 的權重讀取（BF16），再加上整份 KV cache 的讀取（32k context 時 +10.7 GB）。1 對 295——decode 是**極端 memory-bound**，Tensor Core 的利用率約 0.3%。GPU 不是在算，是在等記憶體。ch02 已經用這個邏輯推過單流 decode 的理論上限：3,350 GB/s ÷ 152 GB ≈ **22 tokens/s**，與量測值同量級。

**Prefill（n 個 token）**：同一批權重只讀一次，卻對 n 個 token 各做一份計算——矩陣乘變成真正的 GEMM，**intensity ≈ n FLOP/byte**。n 超過 ridge point（約 300 個 token）就翻到 compute-bound 那一側；一段 2,048 token 的 prompt，intensity 約 2,048，是 ridge 的 7 倍。Prefill 吃滿 Tensor Core，瓶頸是算力。

同一個模型、同一張卡、同一個請求的兩個階段，一個卡在頻寬、一個卡在算力：

| | Prefill | Decode |
|---|---|---|
| 一次處理 | 整段 prompt（10²~10⁵ tokens） | 每序列 1 token |
| 運算形態 | GEMM（矩陣×矩陣） | GEMV（矩陣×向量） |
| Arithmetic intensity | ≈ n（容易 ≫ 295） | ≈ 1（≪ 295） |
| 瓶頸 | 算力（Tensor Cores） | HBM 頻寬 |
| 使用者體感 | TTFT | ITL / TPOT |
| 對策的方向 | 更強算力、prefix 重用（ch05）、sparse attention | 更大頻寬、權重量化（ch07）、batching |

這個不對稱嚴重到什麼程度？單機層面，引擎得用 chunked prefill 避免一段長 prompt 的 prefill 把所有人的 decode 卡出 ITL 尖峰（ch06）；叢集層面，2025–2026 的大規模架構乾脆把兩個階段拆到不同的 GPU 池、各自用適合的硬體（P/D 分離，ch10）。那兩章的所有設計，都只是本節這張表的工程推論。

## Batch：decode 吞吐的來源與它的天花板

Decode 的 intensity ≈ 1 是 batch = 1 的情況。如果同一個 decode 步同時為 B 條序列各生成一個 token 呢？權重還是只讀一次，計算變成 B 份——**intensity 隨 B 線性上升**。這就是 batching 在 LLM 推論裡的本質：**攤提權重讀取**。讀一次 141 GB，服務 1 個 token 是浪費，服務 64 個 token 就接近合理。

但 KV cache 不一樣：**每條序列有自己的 KV，誰也不能攤提誰的**。每個 decode 步的記憶體流量是「權重（固定）+ B × 每條序列的 KV」。把它寫成式子，B 條序列、每條 context 長度 c：

```
intensity(B) ≈ (B × 2P) / (W_bytes + B × KV_per_seq)   →（B → ∞）→  2P / KV_per_seq
```

漸近線不是無限大。對 Llama-3.3-70B、32k context：141 GFLOPs ÷ 10.7 GB ≈ **13 FLOP/byte**——不管 batch 開多大，永遠到不了 295 的 ridge point。**長上下文的 decode 是 batching 救不回來的 memory-bound**，因為主要流量已經從權重變成 KV 本身。這是「KV cache 主宰一切」的第二次現身：它不只吃容量，還吃頻寬。（順帶可以看出 GQA 的另一層價值：MHA 的漸近線會再低 8 倍，只有 1.6。）

### 一階模型：吞吐—延遲取捨曲線

用一個放得進單卡的模型把曲線算出來。Llama-3.1-8B（32 層、8 KV heads、head_dim 128 → 每 token KV = 131,072 bytes）、BF16 權重 16 GB、H100、每條序列 context 4k（KV/條 ≈ 0.54 GB）。memory-bound 階段，每個 decode 步的時間 ≈ 記憶體流量 ÷ 3,350 GB/s：

| Batch B | 每步讀取 (GB) | 每步時間 = ITL | 總吞吐 (tok/s) | 對比 B=1 |
|---|---|---|---|---|
| 1 | 16.5 | 4.9 ms | 202 | 1× |
| 8 | 20.3 | 6.1 ms | 1,320 | 6.5× |
| 32 | 33.2 | 9.9 ms | 3,230 | 16× |
| 64 | 50.4 | 15.0 ms | 4,260 | 21× |
| **~100** | **~70** | **~21 ms** | **~4,800** | **KV 池撞牆**（72−16−2 ≈ 54 GB ÷ 0.54 GB） |
| 128（裝不下） | 84.7 | 25.3 ms | 5,060 | 25× |

（一階模型：假設完美 memory-bound、忽略計算時間與排程開銷，數字是理論形狀不是實測；實測方法見 ch14。）

三個讀法。第一，**B 從 1 到 64，吞吐漲 21 倍、ITL 只惡化 3 倍**——這條不對稱的曲線就是推論引擎存在的理由，沒有 batching 的 GPU 推論在經濟上不成立。第二，曲線有兩道天花板：頻寬漸近線（此例 3,350 ÷ 0.54 ≈ 6,200 tok/s）與 **KV 容量牆**（B≈100 時 54 GB 的池子滿了）——這張卡在跑滿之前先被記憶體容量掐住，又一次 memory 的生意。第三，ITL 隨 B 單調上升：吞吐與單使用者延遲是真實的取捨，不是調參能繞過的，這條曲線的甜蜜點選擇就是 ch06 排程與 ch13 容量規劃的核心題。

至於「怎麼讓請求隨來隨進、隨完隨走地動態組 batch」（continuous batching），機制留給 ch06。

## Sampling：infra 工程師需要知道的最低限度

流水線尾端，logits（128,256 維分數）要變成一個具體的 token id：

- **Greedy**：直接取分數最高的。**Temperature**：logits 先除以 T 再 softmax——T<1 分布更尖（保守）、T>1 更平（發散）、T=0 等價 greedy。**Top-k**：只在分數前 k 名裡抽。**Top-p（nucleus）**：只在累積機率達 p 的最小集合裡抽。

模型品質層面的調參不是本書的事。Infra 視角只有三件事重要：

1. **可快取性**：前面說過，KV 只依賴 token 序列，sampling 參數不影響 KV——prefix cache 可以跨不同 temperature 的請求共享（ch05）。但「輸出快取」（同 prompt 直接回放舊答案）只在 greedy + 固定條件下才語義成立。
2. **重現性**：temperature = 0 **不保證** bit 級重現。浮點加法不可結合，GPU kernel 的歸約順序會隨 batch 組成改變，同一個 prompt 在不同併發環境下可能產出不同 token。這不是 bug，是物理。後果很實際：eval pipeline 跑兩次分數不同，會被誤報成「模型退化」。防禦：評測固定 seed 與執行條件；vLLM 0.22 起提供 batch-invariant 推論選項，以效能換決定性（2026-06）。
3. **成本佔比**：sampling 本身的計算極便宜，可以忽略；但 structured output（JSON schema/grammar 約束）要在每步對 logits 上 mask，實作不好會成為瓶頸，這是 ch08 講 SGLang 時的話題。

## MoE：記憶體買全部、算力用一部分

回看每層參數表：FFN 佔 82%。MoE（Mixture of Experts）的想法是把這塊最大的肥肉換成 N 份平行的「expert」FFN，外加一個小小的 **router**：每個 token 經過每層時，router 給所有 expert 打分，只把 token 送進分數最高的少數幾個。

用 DeepSeek-V3 的真實數字（查證自 config.json，2026-06）：61 層，每層 256 個 routed expert + 1 個 shared expert（每個 token 都過），每 token 選 top-8。於是：

- **Total parameters：671B** ——記憶體必須裝下全部。權重 FP8 也要約 671 GB，加 KV 與 overhead，至少一台 8×H200（141 GB × 8 = 1,128 GB）等級的機器才裝得下，單卡免談。
- **Active parameters：37B** ——每個 token 實際流經的參數。每 token 計算量約 2 × 37B = 74 GFLOPs，**比 Llama-70B dense（141 GFLOPs）還便宜一半**，能力卻是另一個級別。

這就是「MoE 改變 serving 經濟學」的意思：**你為 capacity 付記憶體的錢，只為 intelligence 付算力的錢**。代價是兩者的失衡比 dense 模型更極端——一台塞滿 671 GB 權重的機器，每個 token 只動用 5.5% 的參數。小流量自建跑 MoE 極不划算（買了一倉庫的記憶體服務涓涓細流）；大平台則靠兩件事回本：足夠大的 batch 讓各 expert 都吃飽，以及把 expert 攤到大量 GPU 上的 expert parallelism（wide-EP，一句話帶過，機制見 ch09）。另一個 Murphy 點：router 是按 token 路由的，B 條序列的一個 decode 步可能喚醒幾乎所有 expert——batch 攤提權重讀取的效果在 MoE 上打折，hot/cold expert 的負載不均也成為新的故障面（ch09）。

2026 年年中的開放權重旗艦幾乎全是 MoE（規格依 landscape 基準，2026-06）：

| 模型 | Total | Active | Active 佔比 | 備註 |
|---|---|---|---|---|
| DeepSeek-V3 | 671B | 37B | 5.5% | 256+1 experts、top-8、MLA |
| DeepSeek-V4-Pro（preview） | 1.6T | 49B | 3.1% | DSA sparse attention、1M context |
| Kimi K2.6 | 1T | 32B | 3.2% | MLA、原生 INT4 |
| Qwen3.5-397B | 397B | 17B | 4.3% | 線性注意力混合 |
| Llama 4 Maverick | ~400B | 17B | 4.3% | 128 experts |
| gpt-oss-120b | 117B | 5.1B | 4.4% | MXFP4，單張 H100 可跑 |

趨勢線很清楚：total 越做越大（1.6T）、active 壓得越來越低（3%）。模型廠在用架構告訴你：智慧的上限靠 total params，serving 的成本靠 active params 與 KV 設計——兩者已經解耦。

## 長上下文的帳單：兩條曲線一起漲

把本章兩個主角放到 context 長度這個軸上：

**KV cache 隨 context 線性成長**（Llama-3.3-70B，BF16）：

| Context | KV / 條對話 | 對照 |
|---|---|---|
| 4k | 1.34 GB | 還算親切 |
| 32k | 10.7 GB | 本章主例 |
| 128k | **42.9 GB** | 一條對話 > 半張 H100 |
| 128k（若為 MHA） | 343.6 GB | 四張卡只為一條對話的 state |
| 128k（DeepSeek-V3 MLA） | 9.2 GB | 671B 模型反而最省 |

**Prefill 計算隨 context 平方成長**。FLOPs ≈ 線性項 2Pn + attention 項 4n²·d·L。對 Llama-3.3-70B（d=8192、L=80）：

| Prompt 長度 | 線性項 | Attention 項 | 合計 | attention 佔比 | 估計 prefill 時間* |
|---|---|---|---|---|---|
| 32k | 4.6 PFLOPs | 2.8 PFLOPs | 7.4 PFLOPs | 38% | ~15 s（單卡當量） |
| 128k | 18.5 PFLOPs | 45.0 PFLOPs | **63.5 PFLOPs** | 71% | ~128 s（單卡當量） |

（*以 989 TFLOPS × 50% MFU 的單卡當量粗估，僅看量級；實務靠多卡平行與 FlashAttention 等 kernel 壓低，見 ch07/ch09。）

context 從 32k 到 128k 是 4 倍，prefill 計算量卻是 8.6 倍——因為 O(n²) 項從配角變主角。一個 128k 的請求若沒有任何 cache 重用，光 prefill 就是分鐘級的 GPU 獨佔，TTFT 直接爆表。把這兩條曲線放在一起，你就理解了 2025–2026 整個產業的行為：API 廠商給 cached input 打 1~9 折的折扣結構、Mooncake 把 KV cache 做成儲存系統、agentic 流量讓 prefix caching 從優化變成生存必需（ch05、ch10、ch17）——全是這張帳單逼出來的。

## 故障模式與防禦

理論章也有 Murphy。以下每一條都是「公式沒算對」在生產環境的長相：

| 故障 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| 只用「參數量 × 2 bytes」估記憶體，忘了 KV 與 activation | 引擎啟動就 OOM；或啟動成功但 KV 池小到只能跑個位數併發 | vLLM 啟動 log 的 KV cache size / `num_gpu_blocks`；nvidia-smi 的常駐占用 | 用本章公式把權重、KV、activation 三本帳分開算，再決定卡數 |
| 把 GQA 公式套在 MLA 模型上（或反之） | 容量規劃高估/低估 5~8 倍，上線後併發與預估完全對不上 | 實際 `num_gpu_blocks` 與你的試算差距巨大 | 規格以 config.json 為準（`num_key_value_heads`、`kv_lora_rank`），不要讀行銷文 |
| `max_model_len` 開到 128k 但 p99 流量只有 4k | 單一長請求就能吃掉大半 KV 池；preemption 與 recompute 變多、ITL 抖動（ch06） | KV cache utilization 飆高伴隨 preemption 計數上升（ch14 指標） | 依真實 context 分布設上限；長 context 流量獨立成池 |
| 長 prompt 的 prefill 餓死全卡的 decode | 某些時刻全體使用者 ITL 突然尖峰，與長請求到達時間吻合 | ITL p99 與 `prompt_tokens` 分布的相關性 | chunked prefill / 排程隔離（ch06）；極端者 P/D 分離（ch10） |
| Gateway 用字元數做配額、引擎用 token 計費 | 中文/程式碼流量配額暴衝，計費對帳差 30%+ | 對帳 `prompt_tokens` vs gateway 計數 | 全鏈路統一用引擎側 token 計數；gateway 內嵌同款 tokenizer |
| 把浮點不可重現當成模型故障 | eval 分數隨 batch 環境漂移；temperature=0 仍有輸出差異，誤報「模型退化」 | 固定輸入重放：單獨跑 vs 高併發跑結果不同 | 評測固定 seed 與併發條件；必要時用 batch-invariant 模式（2026-06 vLLM 提供）換取決定性 |
| Context 滿時的 silent truncation | 沒有錯誤碼，但模型「忘了」對話前半段，品質劣化無聲無息 | 監控 `prompt_tokens` 逼近 `max_model_len` 的請求比例 | 顯式處理超限（拒絕或摘要重組），別依賴框架預設行為 |
| 用 active params 替 MoE 估記憶體 | 「37B 而已，兩張卡夠了」→ 671 GB 權重根本載入不了 | 載入階段直接失敗 | Total params 算記憶體、active params 算算力，兩本帳永遠分開 |

## 動手做

### Lab 1 [M1]：用 llama.cpp 親手量出 prefill / decode 的不對稱

ch02 你已經裝過 llama.cpp。這次用它的 benchmark 工具直接量兩階段：

```bash
# 模型：任一 8B 級 4-bit GGUF（約 4.5~5 GB），例如 Llama-3.1-8B-Instruct Q4_K_M
llama-bench -m models/llama-3.1-8b-instruct-Q4_K_M.gguf \
  -p 512,2048,8192 \    # prefill 測試：三種 prompt 長度
  -n 128                # decode 測試：生成 128 tokens
```

輸出裡 `pp`（prompt processing）就是 prefill 速率、`tg`（text generation）就是 decode 速率。**成功標準**：(1) pp 與 tg 差 1~2 個數量級，且你能用 arithmetic intensity 解釋為什麼；(2) pp 的總耗時隨 prompt 長度超線性成長；(3) 進階：查你晶片的記憶體頻寬（M1 ≈ 68 GB/s、M1 Pro ≈ 200、M1 Max ≈ 400），用「頻寬 ÷ 模型檔案大小」算出 decode 理論上限，對照實測值——通常落在理論值的 60~85%，能解釋差距去哪了（KV 讀取、非權重流量、排程開銷）就算通關。

### Lab 2 [紙上推演]：對三個模型算 KV 公式

只給 config，不給答案（答案在本章都出現過，自己對）：

| | Llama-3.1-8B | Llama-3.3-70B | DeepSeek-V3（MLA） |
|---|---|---|---|
| layers | 32 | 80 | 61 |
| kv_heads × head_dim | 8 × 128 | 8 × 128 | （latent：512 + 64 元素，K/V 共用一份） |
| KV 精度 | BF16 | BF16 | BF16 |

求：(a) 每 token KV bytes；(b) 一條 128k 對話的 KV（GB）；(c) 若 KV 池有 69 GB，各能放幾條 32k 對話；(d) 思考題：DeepSeek-V3 的答案為什麼「不公平地好」，它付出了什麼代價？**成功標準**：三組數字與本章誤差 < 5%，且 (d) 能講出「從預訓練就得採用 MLA 架構」這層。

### Lab 3 [M1]：tokenizer 十分鐘體感

```bash
uv run --with transformers python - <<'EOF'
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained("Qwen/Qwen3-8B")   # 不需下載權重，只拉 tokenizer
for s in ["The quick brown fox jumps over the lazy dog.",
          "敏捷的棕色狐狸跳過了懶狗。",
          "SELECT * FROM users WHERE id = 12345;"]:
    ids = tok.encode(s)
    print(f"{len(s):3d} chars -> {len(ids):3d} tokens | {s[:20]}")
EOF
```

**成功標準**：算出三種文本各自的 chars/token 比；能用一句話說明為什麼同一個 quota 數字對英文與中文使用者「不公平」，以及這對 gateway 計量設計的含意。

## 這個領域往哪走

本章的公式建立在「每個 token 對所有歷史做 full attention、KV 隨 context 線性成長」之上。這個前提正在被三條路線鬆動（2026-06）：MLA 已從 DeepSeek 的獨門變成開放權重旗艦的常見選擇（Kimi K2 採用）；DeepSeek-V4 的 DSA（sparse attention）讓每個 token 只精選一部分歷史來看，等於真的在替那張「不可索引的表」建索引；Qwen3.5 的線性注意力混合架構則讓部分層的 state 不再隨 context 成長。如果這些路線成為主流，本章的 KV 公式要改寫——但「state 大小 × 頻寬 = decode 物理」這個分析框架不會變，變的只是代入的數字。深入的評估留給 ch17。

## 自我檢核

1. 寫出 KV cache 大小公式，並對任一個你查得到 config.json 的 GQA 模型，心算每 token 的 KV bytes。
2. 用 arithmetic intensity 證明：為什麼 decode 是 memory-bound、prefill 是 compute-bound？ridge point 怎麼算？
3. Llama-3.3-70B 為什麼單張 H100 服務不了任何一條 32k 對話？2×H100 又為什麼是約 6 條？整筆帳重算一遍。
4. GQA 相對 MHA 把 KV 縮小幾倍？這個倍數同時影響容量與頻寬兩本帳，分別怎麼影響？
5. 為什麼 batch 能把 decode 吞吐拉高 20 倍，卻無法把它變成 compute-bound？寫出 intensity 隨 B 的漸近線並解釋 KV 為什麼不可攤提。
6. MLA 是怎麼把 KV 壓小的？它和 GQA 的本質差異是什麼？為什麼不能事後改裝到現有模型？
7. MoE 的 total / active 參數分別決定什麼資源的用量？「用 active 估記憶體」會在哪一步翻車？
8. 一個 128k 的請求，prefill FLOPs 與 KV bytes 各是 32k 請求的幾倍？為什麼兩個倍數不一樣？

答不出第 3 題的話，這章要重讀——全書後面會假設你閉著眼睛都算得出來。

## 延伸閱讀

- Vaswani et al., *Attention Is All You Need*（2017）— https://arxiv.org/abs/1706.03762 。原典。不必全讀，看架構圖與 3.2 節的 scaled dot-product attention 就夠本章使用。
- kipply, *Transformer Inference Arithmetic*（2022）— https://kipp.ly/transformer-inference-arithmetic/ 。本章記憶體與延遲數學的最佳延伸，所有推導再走深一層。
- Ainslie et al., *GQA: Training Generalized Multi-Query Transformer Models from Multi-Head Checkpoints*（2023）— https://arxiv.org/abs/2305.13245 。那個「省 8 倍」的出處，含品質對照實驗。
- Shazeer, *Fast Transformer Decoding: One Write-Head is All You Need*（2019）— https://arxiv.org/abs/1911.02150 。MQA 原始論文，也是最早把「decode 是 memory-bound」講透的文獻之一。
- DeepSeek-AI, *DeepSeek-V2*（2024）— https://arxiv.org/abs/2405.04434 。MLA 的原始定義，附各 attention 變體的 KV 對照表。
- DeepSeek-AI, *DeepSeek-V3 Technical Report*（2024）— https://arxiv.org/abs/2412.19437 。本章 MoE 數字的一手來源，順便預習 ch09 的大規模部署。
- Kwon et al., *Efficient Memory Management for Large Language Model Serving with PagedAttention*（2023）— https://arxiv.org/abs/2309.06180 。先只讀 §2–3：對「KV 連續配置浪費多少」的量測；系統解法等 ch05。
- Karpathy, *Let's build the GPT Tokenizer*（2024）— https://www.youtube.com/watch?v=zduSFxRajkE 。BPE 從零實作，兩小時建立 tokenizer 的完整直覺。
