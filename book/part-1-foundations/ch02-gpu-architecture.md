# ch02 — GPU：一種你沒用過的計算機

> **本章解決什麼問題**：你接下來整本書要打交道的機器，物理特性跟你熟的 EC2 完全不同。這章建立 GPU 的系統工程師心智模型——不是教你寫 CUDA（那是 ch04 的事），而是讓你能讀懂規格表、用 roofline 一條公式判斷 workload 卡在算力還是記憶體、講得出 2026 年資料中心層級的硬體版圖。ch03 會用這章的 roofline 證明「decode 是 memory-bound」這個全書反覆引用的結論；ch09 的平行化決策、ch13 的容量規劃、ch16 的成本模型，地基全在這裡。

## 從你已知的出發

你做過一件事，方法論跟這章完全同構：把 RDS CPU 尖峰降 40% 之前，你第一步不是改 SQL，而是先用 profiling 確認瓶頸到底在 CPU、在 IO、還是在鎖競爭——瓶頸判斷錯了，後面所有優化都是白工。Roofline model 就是把這個判斷變成一條可以**事先用紙筆算出來**的公式：不用先部署、先壓測，看著規格表就能算出「這個 workload 在這張卡上，天花板是算力還是記憶體頻寬」。這是本章要交給你的最重要工具。

另外三個錨點：

- **GPU 的執行模型 ≈ 一個超大規模 worker pool**。你管過 10K CCU 的遊戲後端：幾十台機器、每台幾百個並發連線，靠的不是單一 worker 快，而是夠多 worker 同時在飛、誰被 IO 卡住就先處理別人。GPU 把這個模式燒進矽片：一張 H100 上常駐**二十幾萬條硬體執行緒**，誰在等記憶體就瞬間切走，用海量並發把延遲「藏」起來。
- **GPU 記憶體階層 ≈ 你的 local cache → Redis → RDS 分層**。每往下一層，容量漲三個數量級、速度掉一個數量級，而你的工作跟以前一樣：讓熱資料留在快的那層。差別是這裡的「慢層」HBM 都有 3.35 TB/s——是你用過最快的 RAM 的幾十倍——而它仍然是瓶頸。
- **互連拓撲 ≈ 同 AZ vs 跨 AZ vs 跨 region**。你知道跨 AZ 的延遲與費用會改變架構決策；GPU 世界同理，節點內 NVLink 與節點間 InfiniBand 差了一個數量級，這條斷層線直接決定模型怎麼切（ch09 的全部內容建立在這上面）。

最後一個心理準備：GPU 是**裸露的實體資產**。EC2 給你的抽象層（hypervisor 把壞硬體藏起來、可超賣、秒級替換）在這裡大部分不存在。卡會掉、記憶體會翻位元、散熱不良會讓它無聲變慢。本章最後一節先給你故障目錄的入門版，ch15 再展開完整的可靠性工程。

## GPU vs CPU：latency machine 與 throughput machine

CPU 是 **latency machine**：它的設計目標是讓「單一指令流」越快越好。一顆現代伺服器 CPU 把大部分電晶體花在讓你看不見的地方——分支預測、亂序執行、多層大快取——全是為了讓單執行緒少等待。所以幾十個核心、每個都很聰明。

GPU 是 **throughput machine**：它賭的是你的問題可以被切成數十萬個一模一樣的小工作（矩陣乘法正是如此）。它把電晶體全部押在「更多算術單元」上，砍掉分支預測與亂序執行，用一個簡單粗暴的策略對付記憶體延遲：**等待的時候去做別人的工作**。

具體的硬體分層（以 H100 SXM 為例，2026-06 查證）：

- **SM（Streaming Multiprocessor）**：GPU 的基本執行單元，H100 有 132 個。粗略類比：一個 SM ≈ 一個自帶排程器、自帶 scratch 記憶體的小型多核處理器。
- **Warp**：32 條執行緒一組，**鎖步執行同一條指令**（SIMT，Single Instruction Multiple Threads）。warp 是排程的最小單位——你可以想成「一個 worker 一次處理一批 32 筆的 batch job，批內每筆走同樣的程式路徑」。
- **Latency hiding**：每個 SM 上可以同時「常駐」最多 64 個 warp（2,048 條執行緒），132 個 SM 合計約 27 萬條常駐執行緒。某個 warp 發出記憶體請求要等幾百個 cycle？SM 的 warp scheduler **下一個 cycle 就切去跑別的 warp**，切換成本是零——因為每個 warp 的暫存器都常駐在 SM 上，不像 OS context switch 要存還現場。

這就是你的 event loop 直覺的硬體版：Node.js 用單執行緒 + 非同步 IO 把等待藏進並發；GPU 用上萬個硬體執行緒做同一件事，只是排程器是矽做的、切換是零成本的。推論一個系統含意：**GPU 要餵飽才快**。並發不足（batch 太小、kernel 太碎）時，SM 大部分時間找不到可跑的 warp，幾百 TFLOPS 的算力直接閒置——這是 ch06 batching 與 ch07 CUDA Graphs 要解的問題的物理根源。

量級感：H100 的 BF16 tensor core 算力是 989 TFLOPS（dense）；你以前用的 c5 系列一顆 vCPU 是 GFLOPS 等級——中間差了五個數量級。但這個算力有個前提條件，下一節就會看到：資料要供得上。

## 記憶體階層：先建立數字感

LLM serving 本質上是 memory 的生意（全書主軸一），所以這張表比算力數字重要得多。以 H100 SXM 為例（2026-06）：

| 層級 | 容量 | 頻寬量級 | 誰負責管理 |
|---|---|---|---|
| Registers | 每 SM 256 KB（全卡 ≈ 33 MB） | 約百 TB/s 級（聚合） | 編譯器 |
| Shared memory / L1 | 每 SM 256 KB（SMEM 最高可配 228 KB） | 數十 TB/s 級（聚合） | kernel 作者（ch07） |
| L2 cache | 50 MB（全卡共享） | 約 10 TB/s 級 | 硬體 |
| **HBM3（顯示記憶體）** | **80 GB** | **3.35 TB/s** | 推論引擎與你 |
| 主機 DRAM | TB 級 | 受 PCIe Gen5 限制：~64 GB/s 單向 | OS |
| NVMe / 網路儲存 | 數 TB 起 | 數~十數 GB/s | OS |

（晶片內各層頻寬是微基準測量值，不同來源略有出入，這裡只取量級；HBM 頻寬是官方規格。）

三個必須內化的觀察：

1. **每往上一層，頻寬漲約一個數量級，容量掉約三個數量級。** 你在 local cache / Redis / RDS 之間做過的所有取捨，這裡原樣成立，只是時間尺度從 ms 縮到 ns。
2. **模型權重只裝得進 HBM 這一層。** 70 GB 的權重對 50 MB 的 L2 來說大到沒有快取意義——每次用到都得從 HBM 重讀。所以「HBM 頻寬」幾乎就是 LLM decode 的代名詞（下一節證明）。
3. **PCIe 是斷崖。** HBM 內部 3.35 TB/s，但跨過 PCIe 到主機 RAM 瞬間掉到約 64 GB/s 單向——差 50 倍。這就是為什麼 KV cache offloading（ch05）、權重載入（ch12）的設計都圍繞著「怎麼少過、晚過這道橋」。

一個常見誤解先拆掉：HBM（High Bandwidth Memory）不是普通 GDDR 顯示記憶體，它是用 3D 堆疊直接封裝在 GPU 旁邊的 DRAM，靠超寬匯流排（H100 是 5120-bit）換頻寬。它貴、產能緊張，而且**容量與頻寬是 GPU 定價的真正主成分**——你會在硬體版圖表看到，2024–2026 每一代新卡的頭條規格都是 HBM，不是 TFLOPS。

## Roofline model：一條公式判斷瓶頸

現在把本章最重要的分析工具裝上。問題形式是：「給定一張卡和一個 workload，效能天花板由算力決定，還是由記憶體頻寬決定？」

定義 **arithmetic intensity（AI，運算強度）**：

```
AI = 這個 workload 做的 FLOPs ÷ 它必須從 HBM 搬的 bytes    （單位：FLOP/byte）
```

（FLOP = 一次浮點運算；一次乘加 FMA 算 2 FLOPs。）

一張卡有兩個天花板：算力屋頂 `P_peak`（TFLOPS）與頻寬屋頂 `BW`（TB/s）。可達到的效能是：

```
可達效能 = min( P_peak ,  AI × BW )
```

兩條屋頂的交點叫 **ridge point（拐點）**：

```
拐點 = P_peak ÷ BW    （FLOP/byte）
```

- workload 的 AI **小於**拐點 → **memory-bound**：算力再強也吃不飽，效能 = AI × BW，唯一解法是搬更少 bytes 或買更大頻寬。
- AI **大於**拐點 → **compute-bound**：頻寬有餘裕，效能貼著算力屋頂，解法是更多/更快的算術單元或更低精度。

把 2026 年常見卡的拐點算出來（dense 算力，2026-06 查證）：

| 卡 | 算力（dense） | HBM 頻寬 | 拐點 |
|---|---|---|---|
| H100 SXM | BF16 989 TFLOPS | 3.35 TB/s | ~295 FLOP/byte |
| H100 SXM | FP8 1,979 TFLOPS | 3.35 TB/s | ~590 FLOP/byte |
| H200 | BF16 989 TFLOPS | 4.8 TB/s | ~206 FLOP/byte |
| B200 | FP8 4,500 TFLOPS | 8 TB/s | ~562 FLOP/byte |

讀規格表的兩個防雷技巧：（1）NVIDIA 行銷頁預設引用「with sparsity」的數字（剛好是 dense 的兩倍，例如 H100 BF16 寫 1,979），LLM 推論用不到結構化稀疏，**一律看 dense**；（2）凡是頻寬數字都先問「單向還是雙向加總」——NVLink 的 900 GB/s 是雙向加總，IB 的 400 Gb/s 是單向，直接相除會錯一倍。

### Worked example：證明 Llama-70B 在 H100 上 decode 是 memory-bound

這是全書會反覆回來的計算，一步步走。

**第 0 步：設定。** Llama-3.3-70B，實際參數量約 70.6B，是 dense 模型（每個 token 用到全部參數）。H100 SXM：80 GB HBM3、3.35 TB/s、FP8 dense 1,979 TFLOPS。

**第 1 步：權重裝不裝得下？**

```
FP16/BF16：70.6B × 2 bytes = 141.2 GB  → 80 GB 裝不下，需要 2 張卡（TP2，見 ch09）
FP8：     70.6B × 1 byte  =  70.6 GB  → 單卡裝得下，但只剩不到 10 GB 給 KV cache 與 activation
```

（FP8 單卡在生產上太緊——KV cache 空間決定你能同時服務幾條對話（見 ch03）——但作為計算案例最乾淨，先用它。）

**第 2 步：decode 一個 token 要搬多少 bytes？** Decode 階段每生成一個 token，都要把**整個模型的權重從 HBM 讀進 SM 一次**。為什麼快取救不了：L2 只有 50 MB，對 70.6 GB 的權重而言命中率趨近於零，每一層算完、下一層的權重一定來自 HBM。所以 batch=1 時：

```
bytes ≈ 70.6 GB（權重，FP8）＋ KV cache 讀取（暫時忽略，ch03 補上，它只會讓結論更 memory-bound）
```

**第 3 步：decode 一個 token 要算多少 FLOPs？** 經驗法則：dense transformer 每個參數每個 token 貢獻一次乘加 = 2 FLOPs：

```
FLOPs ≈ 2 × 70.6B = 141.2 GFLOP
```

**第 4 步：arithmetic intensity。**

```
AI = 141.2 GFLOP ÷ 70.6 GB = 2 FLOP/byte
```

**第 5 步：跟拐點比。** H100 FP8 拐點 ≈ 590 FLOP/byte。

```
2 ≪ 590 → 重度 memory-bound，差了約 300 倍
```

換句話說：batch=1 decode 時，H100 的 tensor core 利用率上限是 2/590 ≈ **0.3%**。你花的是 1,979 TFLOPS 的錢，用到的算力連 1% 都不到——瓶頸從頭到尾是那條 3.35 TB/s 的記憶體匯流排。

**第 6 步：理論 token rate 上限。** 既然是 memory-bound，效能由「搬完一輪權重要多久」決定：

```
單請求 decode 上限 = 3.35 TB/s ÷ 70.6 GB ≈ 47 tokens/s
```

**第 7 步：現實折扣。** 實際系統的 memory bandwidth utilization（MBU）通常落在 60–80%（kernel 不完美、KV 讀取、排程開銷），所以實測單請求 decode 大約 30–38 tok/s。公開的 H100 70B 單請求 benchmark 數字落在這個區間，與推算一致——這條公式可以當 sanity check 用：**看到有人宣稱單請求 70B FP8 在 H100 上跑 100 tok/s，你現在有能力直接斷定那是假的（或不是這個配置）。**

**第 8 步：FP16 + TP2 對照。** 141.2 GB 權重切到 2 張卡上，聚合頻寬 6.7 TB/s：

```
6.7 TB/s ÷ 141.2 GB ≈ 47 tokens/s（忽略卡間通訊開銷，實際更低）
```

跟 FP8 單卡**一樣**。加卡沒有改變單請求的天花板（頻寬×2、bytes 也×2），但 FP8 用一半的卡達到同樣速度——**量化是 memory-bound 世界的頭等優化**（ch07 展開）。

**第 9 步：batch 為什麼是免費的午餐（直到不是）。** batch=B 時，權重照樣只讀一輪，卻服務了 B 個 token：

```
AI ≈ 2B FLOP/byte → 吞吐近似 B × 47 tok/s，直到 AI 撞上拐點
```

理論上 B≈295 時撞 compute 屋頂；實際上 KV cache 的容量與讀取量會先撞牆（ch03/ch05/ch06 的主題）。但方向已經清楚了：**decode 幾乎永遠活在 roofline 的左半邊**，所有推論引擎的設計——continuous batching、PagedAttention、KV 量化——都是在這個物理事實下討生活。

反過來，prefill 階段一次處理整條 prompt 的 n 個 token，權重讀一輪攤提給 n 個 token，AI ≈ 2n FLOP/byte，n 上千時穩穩 compute-bound。一個請求的兩個階段分別貼著 roofline 的兩條屋頂——這個分裂是 ch06 chunked prefill 與 ch10 P/D 分離的全部動機。完整數學在 ch03。

## Tensor cores 與數值格式：精度是一個可以調的旋鈕

Tensor core 是 SM 裡的專用矩陣乘法單元：一般 CUDA core 一個 cycle 做一次標量 FMA，tensor core 一個 cycle 吃掉一小塊矩陣乘加。LLM 推論 95% 以上的 FLOPs 都發生在 tensor core 上。

關鍵的系統特性：**精度每砍半，tensor core 吞吐量翻倍，權重 bytes 減半**。對 memory-bound 的 decode 來說這是雙重收益——屋頂變高、要搬的東西變少——所以數值格式不是 ML 研究員的玄學，是你做容量與成本規劃的一級變數。

硬體支援是有代際門檻的（2026-06）：

| 格式 | bits | 一句話定位 | 原生硬體支援 |
|---|---|---|---|
| FP32 / TF32 | 32 / 19 | 傳統科學計算；TF32 是 tensor core 上的折衷 | 全部 / Ampere+ |
| FP16 | 16 | 最早的推論主流 | Volta+ |
| BF16 | 16 | 動態範圍同 FP32，訓練與推論通用預設 | Ampere+ |
| FP8（E4M3/E5M2） | 8 | Hopper 世代推論主力，生產上已完全成熟 | Hopper、Ada+ |
| FP4（NVFP4）/ FP6 | 4 / 6 | Blackwell 專屬硬體格式 | **Blackwell only** |
| MXFP4 | 4 | OCP 開放 microscaling 格式（gpt-oss 權重原生採用） | Blackwell（硬體加速） |
| INT8 / INT4 | 8 / 4 | weight-only 量化路線（GPTQ/AWQ） | Turing+ / 軟體解包 |

實務含意三條：

- **你選的卡決定你能用的格式。** 在 H100 上想跑 FP4？沒有原生硬體，要嘛軟體模擬（慢），要嘛換 Blackwell。反過來，2026 年模型開始**原生以低精度發布**（gpt-oss 用 MXFP4、Kimi K2.6 原生 INT4，2026-06），買卡時的格式支援直接決定你能不能吃到這些模型的紅利。
- **FP8 是 2026 年 Hopper 機隊的生產預設**：vLLM/SGLang/TensorRT-LLM 全面支援，DeepSeek 等旗艦模型直接以 FP8 訓練（2026-06）。
- 低精度的品質代價、calibration、哪些任務先壞——是 ch07 的主題，這裡只記住：格式選擇是「吞吐 × 品質 × 硬體相容」的三方取捨，不是越低越好。

## 互連：三層網路，一個數量級的斷層

一座 GPU 叢集裡其實有三張網：

```
一台 8×H100 節點的三張網
├── scale-up：GPU0…GPU7 全接上 NVSwitch（節點內 all-to-all）
│       NVLink 4：每卡 900 GB/s 雙向（450 GB/s 每方向）
├── 節點內骨幹：PCIe Gen5 x16，~64 GB/s 每方向（GPU 到 CPU / NIC）
├── scale-out：每卡一張 400G NIC ──► RDMA 網（IB NDR：50 GB/s 每方向）
└── frontend：一般乙太網（儲存、管理、使用者流量）
```

**Scale-up：NVLink / NVSwitch。** NVLink 是 GPU 對 GPU 的專用點對點互連；NVSwitch 是交換晶片，讓節點內 8 張卡兩兩之間都有全頻寬。代際數字（2026-06 查證）：

| 世代 | 架構 | 每卡頻寬（雙向加總） |
|---|---|---|
| NVLink 3 | Ampere（A100） | 600 GB/s |
| NVLink 4 | Hopper（H100/H200） | 900 GB/s |
| NVLink 5 | Blackwell（B200/B300） | 1.8 TB/s |
| NVLink 6 | Rubin（2026 H2 起） | 預告再翻倍（付印前查證） |

**Scale-out：InfiniBand vs RoCE。** 跨節點走 RDMA 網路。IB 世代：HDR 200 Gb/s → NDR 400 Gb/s → XDR 800 Gb/s（Quantum-X800 世代）；標準 HGX H100 每卡配一張 400G NIC，即每 GPU 50 GB/s 單向。RoCE（RDMA over Converged Ethernet）用乙太網跑 RDMA：便宜、供應商中立、你的網路團隊熟，但要把尾延遲調到 IB 水準（PFC/ECN 調校）是真功夫；NVIDIA 自家的 Spectrum-X 與業界的 Ultra Ethernet 聯盟都在押「乙太網追平 IB」這條線。粗略決策：自建中小叢集、已有強乙太網運維 → RoCE 可省可觀成本；租用時你沒得選，看雲商給什麼。

**斷層線就是架構線。** 節點內 NVLink 450 GB/s 每方向 vs 跨節點 IB 50 GB/s 每方向——**9 倍**；對比 PCIe 64 GB/s 也有 7 倍。這個數量級差距就是 ch09 那條鐵律的物理來源：tensor parallelism 的高頻 all-reduce 流量幾乎只能活在 NVLink 域內，跨節點只跑低頻寬需求的平行模式（PP/DP/EP）。

**NVL72：把 NVLink 域撐到一整個機櫃。** GB200 NVL72 是 2026 年的標誌性設計：72 張 B200 + 36 顆 Grace CPU 裝進一個機櫃，用 NVSwitch tray 與銅纜背板把 **72 張卡接成單一 NVLink 域**（聚合 130 TB/s）。意義：以前「高速互連域 = 8 卡」是硬上限，現在是 72 卡——萬億參數 MoE 模型的 expert parallelism 可以整櫃展開（ch09、ch17），rack 取代 server 成為採購與設計的基本單位。代價在下一節。

## 資料中心現實：功耗、散熱、電力牆

每卡功耗的軌跡（2026-06）：V100 300W → A100 400W → H100 700W → B200 約 1,000–1,200W（依機型）→ B300 / AMD MI355X 1,400W。五年漲了 4 倍，還在漲。

連鎖反應：

- **機櫃密度爆炸**：傳統企業機房一櫃 5–15 kW；一台 8×H100 伺服器就吃 10–12 kW；GB200 NVL72 一櫃約 120 kW（公開部署資料約 120–132 kW，2026-06）。
- **氣冷到頭了**：氣冷實務上限約 40–50 kW/櫃，NVL72 世代直接要求 direct-to-chip 液冷。這不是機房團隊的家務事——液冷改造的資本支出與交期，是 2026 年「有卡但上不了架」的常見原因之一。
- **電力成為一級約束**：一張 H100 跑滿一年 ≈ 6.1 MWh（含散熱更多）。新建資料中心以 GW 計，電網接入排隊以年計。業界共識是：2026 之後限制 AI 算力擴張的第一瓶頸不是晶片產能而是電力（ch17 展開，包括 power-aware scheduling 可能成為 infra 工程師的新工作面）。

對你這個層級的直接含意有一條，常被忽略：**功耗上限會回頭吃效能**。資料中心做 power capping、或散熱不良時，GPU 會自動降頻——症狀是 tok/s 無聲下滑、沒有任何錯誤。你在租用市場（尤其 Vast.ai 這類聚合個人機房的平台）拿到的「同型號卡」，實際效能可能因散熱環境差 10–20%。Benchmark 時記得把 `nvidia-smi` 的時脈與 throttle 原因一起記下來（ch14）。

## 硬體版圖總表（2026-06）

| 晶片 / 系統 | 記憶體 | 頻寬 | 一句話定位 |
|---|---|---|---|
| NVIDIA H100（80GB） | 80 GB HBM3 | 3.35 TB/s | 2026 租用市場的工作馬，生態最成熟、單價已被新卡壓低 |
| NVIDIA H200 | 141 GB HBM3e | 4.8 TB/s | 算力同 H100、記憶體大幅升級——專為推論/長 context 而生 |
| NVIDIA B200（Blackwell） | 192 GB HBM3e | 8 TB/s | 2026 主力雲端機型；FP4 原生支援 |
| NVIDIA GB200 NVL72 | 72×B200 整櫃 | NVLink 域聚合 130 TB/s | rack-scale 設計單位；大 MoE serving 的目標平台 |
| NVIDIA B300 / GB300 NVL72 | 288 GB HBM3e | 8 TB/s | Blackwell Ultra，1,400W、15 PFLOPS dense FP4；2026 放量 |
| AMD MI300X | 192 GB HBM3 | 5.3 TB/s | 「單卡大記憶體」先行者；ROCm 生態仍是採用門檻 |
| AMD MI355X | 288 GB HBM3e | 8 TB/s | 規格對齊 Blackwell；vLLM/SGLang/LMCache 已支援 ROCm |
| Google TPU v7（Ironwood） | 192 GB HBM3e | 7.4 TB/s（Google 公布） | 僅 GCP；驅動 Gemini 3 生產推論；Anthropic 計畫用到百萬顆 |
| AWS Trainium3 | 144 GB HBM3e | 4.9 TB/s | AWS 垂直整合的性價比路線，2.52 PF FP8/晶片 |
| Groq LPU | 晶片內 SRAM（百 MB 級） | SRAM 等級 | 極端低延遲路線；NVIDIA 以 ~$20B 取得技術授權＋核心團隊（2025-12，非股權收購，Groq 仍獨立營運） |
| Cerebras WSE-3 | 晶圓級 SRAM（44 GB，廠商數字） | 廠商宣稱 PB/s 級 | wafer-scale；2026-05 完成 Nasdaq IPO（上市估值約 $56B），與 OpenAI 有 $10B+ 算力協議 |

幾條讀表的線索：

- **頭條規格全是記憶體，不是 TFLOPS。** H100→H200 算力一模一樣，只升級 HBM，就足以成為一代「推論神卡」——回到 roofline：decode 的天花板是頻寬，H200 等於把拐點左移、屋頂抬高 43%。整個產業的競價維度已經說明了「LLM serving 是 memory 的生意」。
- **NVIDIA 的護城河是三層的**：CUDA 軟體生態（ch04）、NVLink/NVSwitch 互連、供應鏈優先權。AMD 在紙面規格上已經追平甚至超越，真正的差距在軟體成熟度與運維工具鏈——不過 2026 年 vLLM/SGLang/llm-d 對 ROCm 的支援已是官方路線（2026-06），「AMD 不能用於 LLM 推論」已經是過時資訊。
- **Hyperscaler 自研晶片（TPU/Trainium）**的本質是垂直整合省掉 NVIDIA 的毛利，鎖定在自家雲；你會在 JD 裡看到它們，但租用市場的主流仍是 NVIDIA。
- **SRAM 路線（Groq/Cerebras）**：把整個模型放進晶片內 SRAM，徹底繞開 HBM 瓶頸，換取極端低延遲；代價是容量經濟學困難（SRAM 貴且小，大模型要攤到大量晶片上）。NVIDIA 花 ~$20B 把 Groq 的技術授權與核心團隊納入麾下（2025-12）這件事本身，就是「低延遲推論專用架構有真實市場」的最強背書。
- 租價量級（2026-06 快照，只記倍率）：H100 在 neocloud 約 $2–3/hr,hyperscaler on-demand 約其 2–4 倍；B200 約 $5–6/hr。絕對數字月級波動，採購策略見 ch16。
- 下一代已預告（付印前需回查）：NVIDIA Rubin（288 GB HBM4、約 13 TB/s,H2 2026 上雲）、AMD MI400（432 GB HBM4、19.6 TB/s,H2 2026）。

## 故障模式與防禦

GPU 故障是 ch15 的主場，但你需要先有「這東西會怎麼壞」的基本目錄。先記一個入口：**Xid**——NVIDIA driver 寫進 kernel log（`dmesg`）的 GPU 錯誤碼，是 GPU 世界的 errno。

| 故障 | 典型 Xid / 訊號 | 症狀長什麼樣 | 怎麼觀測 | 防禦 |
|---|---|---|---|---|
| ECC 單位元錯誤（已修正） | Xid 94（contained）；SBE 計數上升 | 無感，資料已被 ECC 修正 | DCGM 的 ECC 計數器趨勢 | 監控趨勢即可；計數加速上升是壞卡前兆 |
| ECC 雙位元錯誤（不可修正） | **Xid 48**，伴隨 63/64（row remapping） | 在跑的 process 被殺；反覆發生 | `dmesg`、DCGM、`nvidia-smi -q` 的 retired pages | 自動 cordon + drain 節點（ch11/ch15）；remap 資源用罄→RMA |
| 掉卡（fallen off the bus） | **Xid 79** | GPU 從 PCIe 上消失，`nvidia-smi` 報 unable to determine device handle | dmesg、node exporter | 重啟主機；重複發生→硬體/電源/散熱問題，換機 |
| 應用程式記憶體違規 | Xid 13 / 31 | kernel crash，但卡是好的 | dmesg | **別急著 RMA**——這通常是軟體 bug，不是硬體壞；先查引擎版本與 driver 相容性 |
| NVLink 錯誤 | Xid 74 | TP 組整體變慢或 NCCL 報錯，單卡看不出問題 | DCGM NVLink 計數器 | 多卡推論最痛的一類，偵測與處置見 ch15 |
| Thermal / power throttling | 無 Xid！時脈下降 | **無聲變慢**:tok/s 下滑、零錯誤 | `nvidia-smi -q -d PERFORMANCE` 的 throttle reasons、DCGM 溫度/時脈 | 把時脈與 throttle 原因納入常規監控；對照同機隊其他卡 |

兩個工程判斷要先建立：

1. **「有 Xid」≠「卡壞了」，「沒 Xid」≠「卡沒事」。** Xid 13/31 多半是你的軟體問題；而 throttling 這種最常見的效能殺手根本不產生錯誤。分類學比恐慌重要。
2. **規模會把小機率變成日常。** Meta 訓練 Llama 3 405B 時公開的數據：16,384 張 H100、54 天、**419 次非預期中斷**——平均每 3 小時一次，其中約 30% 是 GPU 故障、17% 是 HBM3 故障。粗換算單卡年化故障率約 9–10%。推論叢集比訓練幸運（沒有全域同步，單卡故障的爆炸半徑小），但 64 卡的推論機隊照這個比率，**每個月都會遇到幾次硬體事件**——這不是異常，是常態，你的架構必須把它當輸入條件（ch15）。

你的可觀測性直覺直接遷移：你以前用 FluentBit 從 production log 萃取 API 指標，這裡的對應物是 **DCGM-exporter**（GPU 指標進 Prometheus 的事實標準，2026-06）+ dmesg 裡的 Xid 流。ch14 給完整指標體系。

## 動手做

### Lab 2-1 [紙上推演] 三張卡的 roofline 拐點與 70B decode 上限

給定規格（dense 算力，2026-06）：

| 卡 | BF16 dense | FP8 dense | HBM 頻寬 | HBM 容量 |
|---|---|---|---|---|
| H100 SXM | 989 TFLOPS | 1,979 TFLOPS | 3.35 TB/s | 80 GB |
| H200 | 989 TFLOPS | 1,979 TFLOPS | 4.8 TB/s | 141 GB |
| B200 | 2,250 TFLOPS | 4,500 TFLOPS | 8 TB/s | 192 GB |

任務：

1. 算出三張卡在 BF16 與 FP8 下的 roofline 拐點。
2. 對 70B 模型 FP8 權重（70.6 GB），算每張卡 batch=1 的理論 decode 上限（tok/s），並標注哪張卡「裝不下、需要幾張」。
3. 回答：H200 對 decode 的提升幅度是多少？對 prefill 呢？為什麼不一樣？
4. 進階：估算每張卡要多大的 batch,decode 才會從 memory-bound 翻成 compute-bound（忽略 KV cache）。

**成功標準**：拐點算出 295 / 206 / 281（BF16）與 590 / 412 / 562（FP8）的量級；能說出「H200 算力沒變，所以 prefill（compute-bound）幾乎不變，decode（memory-bound）提升 ≈ 頻寬比 4.8/3.35 ≈ 43%」。

### Lab 2-2 [M1] 用 Apple Silicon 驗證「decode 上限 = 頻寬 ÷ 模型大小」

你的 MacBook 是絕佳對照組：Apple Silicon 的統一記憶體頻寬是公開規格（M1 Pro 200 GB/s、M1 Max 400 GB/s），而 llama.cpp 的 decode 同樣是 memory-bound——同一條公式應該能預測你機器的 token rate。

```bash
# 1. 安裝 llama.cpp（含 llama-bench）
brew install llama.cpp

# 2. 下載同一個 8B 模型的兩種量化（Hugging Face 上的 GGUF,檔名依實際 repo 調整）
#    Q4_K_M 約 4.9 GB、Q8_0 約 8.5 GB
huggingface-cli download bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
  Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf --local-dir ./models
huggingface-cli download bartowski/Meta-Llama-3.1-8B-Instruct-GGUF \
  Meta-Llama-3.1-8B-Instruct-Q8_0.gguf --local-dir ./models

# 3. 分別 benchmark 純 decode（tg = text generation,不含 prefill）
llama-bench -m ./models/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf -p 0 -n 128
llama-bench -m ./models/Meta-Llama-3.1-8B-Instruct-Q8_0.gguf  -p 0 -n 128
```

然後做三件事：

1. **預測**：理論上限 = 你機器的記憶體頻寬 ÷ 模型檔案大小。M1 Pro + Q4_K_M:200 ÷ 4.9 ≈ 41 tok/s。
2. **驗證比值**:Q4 與 Q8 的 tok/s 比值，應接近檔案大小的反比（≈ 8.5/4.9 ≈ 1.7 倍）——如果是 compute-bound，比值不會跟著檔案大小走。
3. **反推 MBU**：實測 tok/s × 模型大小 = 你機器的有效頻寬，除以規格頻寬得到 MBU。

**成功標準**:Q4/Q8 的 tok/s 比值與大小反比誤差 < 20%；反推的有效頻寬落在規格的 50–80%。做到這裡，你就親手驗證了本章 worked example 的物理——同一條公式，從你桌上的 Mac 到機房裡的 H100 都成立。

（附帶觀察：跑 benchmark 時開著活動監視器看 GPU 與記憶體壓力——統一記憶體架構下沒有 PCIe 這道橋，這正是 Mac 能用很普通的算力跑出不錯 token rate 的原因。）

## 這個領域往哪走

短期（1–2 年）的三條確定趨勢：**HBM 軍備競賽繼續**（Rubin 13 TB/s、MI400 19.6 TB/s 都已預告 2026 H2，頻寬代際增速明顯快於算力——產業用腳投票承認了 memory-bound 的現實）；**rack 成為設計單位**（NVL72 之後，採購、排程、故障域的思考單位都從 server 上移到 rack,ch11/ch17）；**電力與散熱從機房議題升級為架構議題**。對你的職涯含意：roofline 這類分析工具十年不會過期，具體卡的型號兩年就換一輪——把力氣花在前者（ch17 有完整的能力耐久性矩陣）。

## 自我檢核

答得出來再往 ch03 走：

1. GPU 為什麼選擇「數十萬條慢執行緒」而不是「幾十條快執行緒」？latency hiding 的機制是什麼，跟 Node.js event loop 的相似點與本質差異在哪？
2. 默寫 roofline 拐點公式，用 H100 FP8 的數字算出拐點，並解釋拐點左右兩側分別該用什麼手段優化。
3. 一步步算：70B 模型 FP8 在單張 H100 上 batch=1 decode 的理論上限是多少 tok/s？實測通常打幾折、為什麼？
4. 為什麼 tensor parallelism 幾乎不跨節點？給出 NVLink 4 與 IB NDR 的每方向頻寬數字佐證。
5. H200 與 H100 算力完全相同，為什麼前者是「推論神卡」？它對 prefill 與 decode 的提升分別是多少？
6. 同事說「nvidia-smi 顯示 GPU utilization 100%，所以這張卡已經被榨乾了」——這個推論哪裡有問題？（提示：本章的 0.3%）
7. dmesg 裡看到 Xid 79 跟 Xid 13，處置方式為什麼完全不同？
8. 你的 64 卡推論機隊，按公開的故障率數據，大約多久會遇到一次硬體事件？這個數字應該如何改變你的部署架構思維？

## 延伸閱讀

- [NVIDIA Hopper Architecture In-Depth](https://developer.nvidia.com/blog/nvidia-hopper-architecture-in-depth/) — H100 架構官方深度解析，SM/tensor core/HBM 數字的一手來源。
- [Making Deep Learning Go Brrrr From First Principles（Horace He）](https://horace.io/brrr_intro.html) — 用 compute/memory/overhead 三分法講效能瓶頸，是 roofline 思維最好讀的工程版，全網被引用最多的入門文之一。
- [Roofline: An Insightful Visual Performance Model（Williams et al., CACM 2009）](https://dl.acm.org/doi/10.1145/1498765.1498785) — roofline 原始論文，證明這個工具早於 LLM 二十年、還會再用二十年。
- [NVIDIA Xid Errors 官方目錄](https://docs.nvidia.com/deploy/xid-errors/) — 每個 Xid 的官方定義與建議處置，值得加入書籤，on-call 時會回來查。
- [The Llama 3 Herd of Models（arXiv:2407.21783）](https://arxiv.org/abs/2407.21783) — 第 3.3 節的基礎設施與可靠性數據(419 次中斷的一手來源），大規模 GPU 機隊 MTBF 現實的最佳公開文獻。
- [Nvidia's H100: Funny L2, and Tons of Bandwidth（Chips and Cheese）](https://chipsandcheese.com/p/nvidias-h100-funny-l2-and-tons-of-bandwidth) — 用微基準實測 H100 記憶體階層各層的真實延遲與頻寬，建立數字感的好材料。
- [Stas Bekman, Machine Learning Engineering Open Book](https://github.com/stas00/ml-engineering) — accelerator 與 debug 章節是大規模 GPU 維運的實戰筆記，Xid 排障部分尤其實用。
- [NVIDIA GB300 NVL72 產品頁](https://www.nvidia.com/en-us/data-center/gb300-nvl72/) — rack-scale 系統的官方規格，感受「機櫃即計算機」的設計語言(2026-06)。
