# ch01 — 從後端到 AI Infra：你站在哪、要去哪

> **本章解決什麼問題**：這是全書的地圖。你即將從一個熟悉的領域（高併發後端）走進一個術語密度極高的新領域（LLM inference infrastructure），最大的風險不是「學不會」，而是「學錯方向」——在錯誤的層花三個月，或用舊直覺做出錯誤的容量判斷。本章給你四樣東西：這個領域的技術棧分層圖與每層對應的章節、職位光譜的解碼方法、你既有技能的遷移矩陣（哪些直接能用、哪些必須從零學）、以及一個把直覺顛覆量化出來的計算——為什麼同樣一萬個並發使用者，基礎設施成本可以差出一個半數量級。後面每一章都會回到這張地圖上。

## 從你已知的出發

先講全書的核心論點，因為它決定了你該怎麼讀這本書：

**大規模 LLM serving 本質上是分散式系統問題，不是模型問題。**

訓練模型的人決定了模型長什麼樣；但讓模型在叢集上跑得穩、快、省的人，每天面對的是排程、路由、快取、容量規劃、可觀測性、故障處理——全是你做了六年的東西，只是物理常數變了。你不需要會訓練模型，就像你維運 Dynasty Warriors Mobile 的後端時，不需要會寫遊戲引擎。

回想你最熟悉的場景：一個玩家請求打進來——ALB 把它分到某台無狀態的 Node.js 容器，業務邏輯跑幾毫秒，讀寫一次 RDS 或 Redis，回應出去。整套系統的狀態都住在資料庫層，app tier 隨便殺隨便擴，10K CCU 用二十台 4 vCPU 的機器就扛住了。你的直覺建立在三個隱含假設上：**每個請求很便宜、應用層無狀態、橫向擴展以秒計**。

LLM serving 把這三個假設全部打碎：

- 一個 chat 請求要做的浮點運算，比一個遊戲 API 請求多出**五到六個數量級**（本章稍後算給你看）。
- 每條進行中的對話在 GPU 記憶體裡掛著 GB 級的狀態（KV cache，見 ch03），它不像 session 可以丟進 Redis——它黏在那張卡上，搬動的成本高到需要專門的傳輸工程（見 ch10）。
- 擴一個新的推論副本，要拉數十 GB 的模型權重、初始化引擎、做 warmup，冷啟動以**分鐘**計（見 ch12）——而流量尖峰還是以秒計來的。

但別急著覺得陌生。你會發現這個領域到處都是你見過的問題穿著新衣服：PagedAttention 就是 OS virtual memory paging 搬到 GPU 記憶體上（見 ch05）；KV-aware routing 是 session affinity + consistent hashing 的高賭注版本（見 ch10）；preemption storm 跟你在遊戲後端見過的 retry storm 是同一種動力學（見 ch15）；你用 FluentBit + Lua 自建 metrics pipeline 的那套思路，換成 DCGM exporter + engine `/metrics` 一樣成立（見 ch14）。你的武器庫大部分還能用，本章的工作就是逐件清點。

## 一個 chat 請求的完整旅程

用一個具體場景把整個 stack 攤開。使用者在某個 AI 產品裡送出一句話，按下 Enter 之後發生的事：

```
client ──HTTPS/SSE──▶ API Gateway ──▶ Inference Router ──▶ vLLM Pod (GPU)
                       認證/計量/限流     KV-aware 路由        tokenize → 排程
                       (ch12, ch16)      (ch10, ch12)         → prefill → decode
                                                              (ch03, ch05, ch06)
   ◀── token ◀── token ◀── token ─── SSE streaming 一路流回 ───┘
```

1. **進門**：client 對 `/v1/chat/completions` 發一個 POST，帶 `stream: true`。這個 API 形狀（OpenAI-compatible）是業界的 de facto 標準（見 ch12）。Gateway 做認證、限流、計量——但注意，限流的單位不是請求數而是 **token 數**，因為一個請求的成本變異可達千倍（10 個 token 的問題 vs 100k token 的文件分析），用 RPS 限流毫無意義（見 ch16）。
2. **路由**：router 要決定送到哪個 GPU 副本。這不是 round-robin 能解的——如果某個副本的記憶體裡還留著這條對話上一輪的 KV cache，送過去可以跳過大量重算，TTFT 差距可達數十倍（llm-d 專案方數據，見 ch10）。這是**有狀態的負載均衡**，你做過的 session affinity 的進化版。
3. **引擎內**：vLLM（見 ch08）把 prompt 切成 token，scheduler 把這個請求**插進正在進行的 batch**——不等任何人，每個 decode step 都重組一次 batch，這叫 continuous batching（見 ch06），是「推論引擎為什麼快」的核心答案。同時為它配置 KV cache 的記憶體分頁（見 ch05）。
4. **Prefill**：整段 prompt 的所有 token 平行算一遍，建立 KV cache。這一步是 compute-bound，吃滿 GPU 算力。算完吐出第一個 token——從請求進門到此刻的時間就是 **TTFT**（time to first token）。
5. **Decode**：之後每個 token 都要把**整份模型權重從 HBM 讀一遍**，逐 token 自回歸生成。這一步是 memory-bound——瓶頸不是算力，是記憶體頻寬（見 ch02、ch03）。token 之間的間隔叫 **ITL**（inter-token latency）。每個 token 經 SSE 一路流回 client——你寫過 WebSocket fan-out，這套長連線串流的工程問題你全都熟，只是方向變成伺服器往外吐。
6. **收尾**：請求完成，KV cache 的分頁被釋放——或者留著當 prefix cache，賭下一輪對話會回來（見 ch05）。整條路上的每個環節都在吐指標（TTFT/ITL/goodput/KV 利用率，見 ch14），都有自己的死法（見 ch15），都在燒錢（見 ch16）。

一句話總結這趟旅程：**prefill 是算力的生意，decode 是記憶體的生意，而整個平台是分散式系統的生意。**

## 技術棧分層：這個領域的地圖

把上面那趟旅程垂直展開，就是這個領域的完整分層。每一層都有自己的工具生態、自己的工程師職稱、和本書對應的章節：

| 層 | 在解什麼問題 | 代表工具（2026-06） | 本書章節 |
|---|---|---|---|
| **產品 API 層** | 認證、計量、限流、OpenAI-compatible 介面 | API gateway、Envoy AI Gateway、OpenRouter 類聚合層 | ch12、ch16 |
| **平台層** | 多模型、多租戶、autoscaling、配額、發布 | KServe、Ray Serve、llm-d、NVIDIA Dynamo | ch12、ch13 |
| **叢集排程層** | GPU 當資源排程、共享、拓撲、節點生命週期 | K8s + GPU Operator、DRA、Kueue、LeaderWorkerSet | ch11 |
| **多卡/多節點層** | 一張卡裝不下：平行化、P/D 分離、KV 路由 | NCCL、vLLM/SGLang 的 TP/EP、Mooncake、NIXL | ch09、ch10 |
| **單機引擎層** | 一張卡之內把吞吐榨乾：batching、KV 管理 | vLLM、SGLang、TensorRT-LLM、llama.cpp/Ollama | ch05–ch08 |
| **Kernel/runtime 層** | 單一運算在 GPU 上跑多快 | CUDA、FlashAttention、FlashInfer、CUDA Graphs | ch04、ch07 |
| **模型層** | 模型結構決定的物理：attention、KV 數學、MoE | transformer 架構本身、quantization 格式 | ch03、ch07 |
| **硬體層** | 算力、記憶體頻寬、互連、功耗 | H100/B200、HBM、NVLink、InfiniBand | ch02 |

三個讀圖要點：

- **你的既有優勢集中在上半部**（產品 API ~ 叢集排程層），那裡的工程問題與你的經驗高度同構。**你的知識空洞集中在下半部**（引擎層以下），那是本書 Part I、II 要替你補的地基。
- **價值密度不是均勻的**。2024–2026 年這個產業最猛的工程創新發生在「單機引擎層」與「多節點層」之間（continuous batching、PagedAttention、P/D 分離、KV-aware routing），而 2026 年的競爭焦點正在往「平台層」上移——四條路線（llm-d、Dynamo、KServe、Ray Serve）都在把同一組底層原語包裝成 Kubernetes 原生的平台（見 ch12）。對你這是好消息：戰場正在往你的主場移動。
- **每層都被同一個約束貫穿**：記憶體。權重要裝得下（容量）、每個 token 要把權重讀一遍（頻寬）、每條對話要掛著 KV state（容量×時間）。這條主軸下面馬上會正式宣告。

## 新的物理常數：你的直覺哪裡會背叛你

你的分散式系統直覺——排程、佇列、一致性、可觀測性——在新世界全部成立。會背叛你的是**數量級**。這張表值得貼在螢幕旁邊：

| 維度 | 你的後端世界 | GPU 推論世界 | 後果 |
|---|---|---|---|
| 單一請求的計算量 | ~ms 級 CPU 時間 | 一則 500 token 回覆 ≈ 70 TFLOPs（70B 模型） | 差 5–6 個數量級，容量直覺全部重算 |
| 請求成本變異 | 大致均勻（±一個數量級內） | 10 token vs 100k token，變異千倍 | RPS 限流與 LB 連線數均衡全部失效 |
| 應用層狀態 | stateless，session 丟 Redis | 每條對話 GB 級 KV state 黏在卡上 | 路由變成有狀態問題（見 ch10） |
| 延遲的單位 | 請求級，看 p99 ms | token 級：TTFT（秒級）+ ITL（十 ms 級）雙指標 | 一個數字描述不了延遲（見 ch14） |
| 橫向擴展速度 | 容器秒級拉起 | 權重載入 + warmup，冷啟動分鐘級 | autoscaling 要靠預測與 headroom（見 ch13） |
| 資源超賣 | CPU 可超賣、cgroup 任意切 | GPU 整數配置、不可超賣（device plugin 模型） | bin-packing 與共享變成一級問題（見 ch11） |
| 重試的代價 | 便宜，retry 是預設手段 | 重試 = 重算分鐘級的昂貴請求 | retry storm 的破壞力放大百倍（見 ch15） |
| 記憶體頻寬 | 幾乎不用想 | **第一性瓶頸**，decode 速度上限由它決定 | 全書主軸一（見 ch02、ch03） |
| 硬體故障 | 單機故障少見，換機便宜 | ECC error、NCCL hang 是日常，一卡掛全組僵 | 可靠性工程是顯學（見 ch15） |
| 單位成本 | $0.17/hr 的 c5.xlarge | $2–7/hr 的 H100（2026-06 快照，級距隨市場波動） | 利用率直接是錢（見 ch16） |

注意這張表的性質：左欄到右欄，**沒有任何一個概念消失**，只有常數改變。佇列還是佇列、快取還是快取、p99 還是 p99。這就是為什麼資深後端工程師轉這個領域有結構性優勢——要補的是物理，不是世界觀。

## Worked example：同樣一萬個並發使用者，為什麼差出兩個數量級

把直覺顛覆量化出來。以下是粗估，目的是建立數量級的手感；嚴謹版的 KV 數學在 ch03、容量規劃方法論在 ch13。所有價格為 2026 年年中快照。

### 你的世界：10K CCU 的遊戲後端

| 假設 | 數值 |
|---|---|
| 並發在線 | 10,000 CCU |
| 平均請求率 | 0.5 req/s/玩家（含心跳與動作）→ 5,000 RPS |
| 每請求 CPU 時間 | 1–5 ms（業務邏輯 + DB/Redis I/O 等待） |
| 機型 | c5.xlarge：4 vCPU / 8 GiB，$0.17/hr（us-east-1，2026-06） |

20 台 c5.xlarge = 80 vCPU。5,000 RPS ÷ 80 vCPU ≈ 每 vCPU 每秒 62 個請求，即每個請求有 **16 ms 的 CPU 預算**——對幾 ms 的業務邏輯綽綽有餘，瓶頸早就丟給 RDS 了（所以你當年才會去優化 RDS 而不是 app tier）。

**成本：20 × $0.17 = $3.4/hr ≈ $2,500/月。**

### 新世界：10K 並發 chat 使用者

| 假設 | 數值 | 依據 |
|---|---|---|
| 並發使用者 | 10,000 | 同上 |
| 同時在等生成的比例 | 10%（人大部分時間在讀與打字）→ **1,000 條活躍生成串流** | duty cycle 假設，偏保守 |
| 模型 | 70B dense（Llama-3.3-70B 級），FP8 權重 ≈ 70 GB | |
| 體感速度要求 | ITL ≤ 40 ms → 每串流 25 tok/s | 約等於人的閱讀速度 |
| 平均對話 context | 4,096 tokens | chat 流量的典型值 |
| 卡 | H100 SXM：80 GB HBM3、3.35 TB/s 頻寬、FP8 dense 約 2 PFLOPS | NVIDIA datasheet |

**第一步，算錯誤的帳（算力帳）。** 每生成一個 token，70B dense 模型要做約 2 × 70×10⁹ = **140 GFLOPs**。總需求 = 1,000 串流 × 25 tok/s × 140 GFLOPs = **3.5 PFLOP/s**。一張 H100 的 FP8 算力約 2 PFLOPS——所以兩張卡就夠了？

**錯。這正是 CPU 直覺害死人的地方。** decode 的瓶頸不是算力，是記憶體。

**第二步，算容量帳（KV cache）。** Llama-3.3-70B 用 GQA：80 層、8 個 KV head、head_dim 128。每個 token 的 KV cache（FP16）：

```
2 (K+V) × 80 層 × 8 KV heads × 128 dim × 2 bytes = 327,680 bytes ≈ 320 KB/token
```

一條 4k context 的對話 = 4,096 × 320 KB ≈ **1.3 GB**。1,000 條活躍對話 = **1.3 TB 的 KV state 必須住在 HBM 裡**。

單張 H100 放下 70 GB 權重後所剩無幾，所以用 4 卡一組做 tensor parallelism（TP4，見 ch09）：320 GB 總 HBM − 70 GB 權重 − 約 25 GB 的 activation/緩衝，剩約 225 GB 給 KV → 每組 TP4 容納約 **175 條活躍對話**。

```
1,000 條 ÷ 175 條/組 ≈ 6 組 TP4 = 24 張 H100   ← 光是 KV 容量需求
```

**第三步，用頻寬帳驗證延遲。** 每個 decode step，一組 TP4 要從 HBM 讀：70 GB 權重 + 該 batch 的 KV（175 × 1.3 GB ≈ 228 GB）≈ 300 GB。TP4 聚合頻寬 = 4 × 3.35 = 13.4 TB/s：

```
300 GB ÷ 13.4 TB/s ≈ 22 ms/step → ITL ≈ 22 ms ✓（在 40 ms 預算內）
```

順手算同一個 step 的算力時間：175 token × 140 GFLOPs ÷ (4 × 2 PFLOPS) ≈ **3 ms**。記憶體要 22 ms、算力只要 3 ms——GPU 的運算單元有八成以上的時間在**等記憶體**。這就是「decode 是 memory-bound」的數字版（嚴謹推導見 ch02 的 roofline 與 ch03）。

**第四步，加上現實。** 上面還沒算：prefill 的算力尖峰（新訊息進來要算 TTFT，會跟 decode 搶資源，見 ch06）、流量尖峰係數、滾動發布與故障的冗餘。實務上 24 張會配到 **28–32 張 H100**。

**成本：28 × $2.75/hr（neocloud 級距）≈ $77/hr ≈ $56,000/月**；若用 hyperscaler on-demand（$7–12/GPU/hr）則 $143,000/月起跳。

### 對帳

| | 遊戲後端 | LLM chat | 倍率 |
|---|---|---|---|
| 並發使用者 | 10,000 | 10,000 | 1× |
| 每請求計算量 | ~10⁸ ops | ~7×10¹³ FLOPs（500 token 回覆） | ~10⁵–10⁶× |
| 應用層常駐狀態 | ~0（在 DB/Redis） | ~1.3 TB KV in HBM | — |
| 月成本 | ~$2,500 | ~$56,000–143,000 | 22–57× |

三個帶走的結論：（1）**算力幾乎從來不是答案**，容量與頻寬才是——這就是為什麼這本書叫你先學記憶體再學別的；（2）那 1.3 TB 的 KV state 是整個架構的重心，後面一半的章節（ch05、ch10、ch13、ch16）本質上都在處理它；（3）成本差兩個數量級，意味著**你在後端世界學到的效能工程，每一分優化在這裡的金錢槓桿放大了兩個數量級**——這正是這個職位存在、且薪資溢價的根本原因。

## 全書三條主軸

上面的計算已經把三條主軸演示了一遍，現在正式宣告。全書每一章都至少呼應其中一條：

1. **LLM serving 本質上是 memory 的生意。** 幾乎所有設計決策——batching、quantization、P/D 分離、路由、容量規劃——最終都回到 memory bandwidth 與 memory capacity 的取捨。看到任何新技術，先問「它動了記憶體的哪一邊」。
2. **量測 → 診斷 → 優化 → 用數據證明。** 你把 RDS CPU 尖峰降 40% 用的方法論，原封不動搬到 GPU 世界，只是 Clinic.js 換成 nvidia-smi/DCGM/engine metrics、k6 的對象從 REST API 換成 SSE token stream。這個方法論是你最值錢的資產，本書所有 lab 都按這個閉環設計。
3. **把分散式系統直覺翻譯到新物理。** 排程、路由、一致性、backpressure、可觀測性的直覺全部成立，但物理常數變了：ms→μs、GB→TB、stateless→重狀態、秒級擴展→分鐘級冷啟動。翻譯靠的是上面那張物理常數表。

## 職位光譜：JD 上的同名異實

「AI Infra」不是一個職位，是一個光譜。同一個 title 在不同公司可以是完全不同的工作，讀 JD 要看關鍵字不要看職稱：

| 職稱 | 實際在做什麼 | JD 關鍵字訊號 | 對應本書 | 與你的距離 |
|---|---|---|---|---|
| **LLM Inference Engineer** | 引擎層效能：KV cache、batching、quantization、引擎調參與選型 | vLLM/SGLang/TensorRT-LLM、TTFT/throughput、quantization、speculative decoding | ch05–ch08 | 中——效能方法論直接遷移，引擎機制要從零補 |
| **ML Platform Engineer** | 把推論（與訓練）包成內部平台：多租戶、配額、部署、CI/CD for models | Kubernetes、Ray/KServe、Go、multi-tenancy、IaC | ch11–ch13、ch16 | **最近**——你的 K8s/平台/AWS 經驗幾乎直接對口 |
| **GPU Infra Engineer** | 叢集與硬體層：節點生命週期、driver/CUDA 版本矩陣、IB 網路、利用率治理 | NCCL、InfiniBand/RoCE、DCGM、SLURM 或 K8s、fleet management | ch02、ch09、ch11、ch15 | 中——K8s 維運遷移，硬體與網路層要補 |
| **MLOps Engineer** | 模型生命週期：registry、部署 pipeline、監控、實驗追蹤 | MLflow/W&B、model registry、pipeline 工具 | ch12、ch14 | 近，但注意：這個 title 涵義最浮動，很多實際是「DevOps for data scientists」，infra 深度有限 |
| **(AI) Performance Engineer** | profiling 與 kernel 級優化：nsight、roofline、kernel fusion、編譯器 | CUDA、Triton（語言）、nsight、kernel | ch02、ch07 | 最遠——方法論同構但工具鏈全新，不建議當第一站 |

讀 JD 的兩個紅綠燈：JD 裡出現 **vLLM、KV cache、TTFT、goodput、DCGM** 這類詞，代表團隊真的在運推論基礎設施（綠燈）；只有「AI/LLM experience」加一堆應用框架（LangChain 類），代表是應用層職位，與本書目標不同（不是不好，是不同賽道）。

**薪資與稀缺度的結構性原因**（理解結構比記數字有用，數字會過期）：這個交集要求三種各需多年養成的能力同時在線——分散式系統工程、效能工程、GPU/ML 領域知識。供給端：三棲的人極少，且生產級 GPU 叢集經驗無法在家完整自學（你租得起一張卡，租不起一千張的故障現場）。需求端：每家把 LLM 放進產品的公司，推論帳單都在爆炸（上面 worked example 的 $56K/月只是一個小產品），會「把帳單降 30%」的人直接對 P&L 說話。截至我能確認的資訊（2026-06），公開薪資調查（levels.fyi 等）顯示 AI infra 相關職位相對同級一般後端有數萬美元級的溢價，且多份招聘調查把 AI infra 技能列為全球最難招的類別——但具體數字隨市場波動，請以你求職當下的 levels.fyi 與實際 offer 為準。

光譜上你的最短路徑：**以 ML Platform Engineer 的既有優勢為跳板，補足 Inference Engineer 的引擎層深度**——這正是本書的章節順序設計，也是 plan.md 的模組順序。

## 技能遷移矩陣：你帶著什麼上路

逐條清點你履歷上的資產。「遷移度」的判準：高 = 方法論與直覺直接可用，換工具即可；中 = 概念同構但需要顯著的新知識；零 = 從零學。

| 你的履歷條目 | AI Infra 對應能力 | 遷移度 | 章節 |
|---|---|---|---|
| RDS CPU 尖峰降 40%（profiling-driven：SQL 重排、交易拆分、鎖競爭、批次化） | GPU 效能優化的完整方法論：量測（DCGM/nsight）→ 找瓶頸（roofline 判斷 compute/memory-bound）→ 優化（batching/quantization）→ 數據證明。**同一個故事換了名詞** | **高** | ch02、ch07、ch08、ch14 |
| K8s CronJobs → SQS → idempotent consumers 結算 pipeline（最終一致性） | K8s controller 的 reconcile loop：desired state vs actual state 的收斂迴圈，本質就是你寫過的 idempotent consumer | **高** | ch04、ch11 |
| WebSocket + Redis Pub/Sub fan-out（3,200 並發連線、千萬訊息/月） | SSE token streaming：長連線生命週期、斷線語意、backpressure、graceful drain 中的 in-flight streaming 請求 | **高** | ch12、ch15 |
| k6 / Vegeta 負載測試 | LLM benchmark：TTFT/ITL/goodput、open-loop vs closed-loop、coordinated omission——k6 使用者會秒懂 | **高** | ch14 |
| FluentBit + Lua 自建 observability pipeline | DCGM exporter + engine `/metrics` + Prometheus/Grafana 的指標 pipeline，設計哲學完全相同 | **高** | ch14 |
| 多層 cache library（in-memory → S3 → local、graceful degradation） | KV cache offloading 分層（HBM → CPU RAM → NVMe → 物件儲存），同構程度高得驚人 | **高** | ch05 |
| KrakenD / API Gateway、rate limiting、OAuth | Inference gateway：token-based 限流、admission control、OpenAI-compatible API 設計 | **高** | ch12、ch16 |
| EKS/ECS/Lambda、Docker、CloudFormation | GPU 叢集的 K8s：物件模型直接複用，但 GPU 資源模型（整數、不可超賣、DRA）要重學 | 中 | ch11 |
| MySQL/PostgreSQL 鎖、隔離級別、deadlock、partitioning | 引擎 scheduler 的資源競爭直覺：preemption、starvation、head-of-line blocking | 中 | ch06 |
| Bull / cron-driven job queue | 排程與佇列理論在 batch scheduling 的應用 | 中 | ch06、ch13 |

**零遷移清單**——誠實面對，這些必須從零學，也是本書 Part I 存在的理由：

1. **GPU 硬體**：SM、HBM、NVLink、roofline——你從沒需要管過記憶體頻寬（ch02）。
2. **Transformer 推論機制**：attention、KV cache 數學、prefill/decode、MoE——所有 ML 術語（ch03）。
3. **Python 與 Go 生態**：你是 TS 工程師；AI infra 的 glue code 是 Python 的天下、K8s 控制面是 Go 的天下（ch04）。
4. **PyTorch 讀碼能力**：tensor、shape、dtype——目標是讀懂 vLLM 原始碼，不是訓練模型（ch04）。
5. **CUDA 生態名詞**：CUDA/cuDNN/NCCL/Triton——多半在讀 stack trace 與版本相容矩陣時遇到（ch04）。
6. **數值精度與 quantization**：FP16/BF16/FP8/FP4，後端工程師從未需要關心的維度（ch07）。

注意比例：高遷移 7 條、中遷移 3 條、零遷移 6 項。你不是從零開始，你是帶著一支大致完整的軍隊，去打一張沒見過的地圖。

## 怎麼讀這本書

### 三條路線

**完整路線（建議，3–6 個月）**：ch01 → ch18 順讀。Part I（ch01–04）是地基，Part II（ch05–08）是引擎機制，Part III（ch09–10）是分散式，Part IV（ch11–13）是你的主場延伸，Part V（ch14–16）是維運與成本，Part VI（ch17–18）是前沿與職涯。每章的「動手做」不要跳過——本書的實驗總預算（租 GPU 部分）控制在 $60–110，相當於一次面試來回的車錢。

**求職速通路線（6–8 週）**：ch01 → ch03（KV 數學，所有面試的地基）→ ch02（roofline）→ ch04（只讀 Python 段）→ ch05、ch06（面試口頭題的核心：PagedAttention 與 continuous batching）→ ch08（部署實戰，做出作品集核心專案）→ ch11（你的主場，差異化優勢）→ ch13（容量規劃，系統設計面試的骨架）→ ch14 → ch18。第一輪略過 ch07/ch09/ch10/ch16/ch17，面試前再補。

**面試前複習路線（3 天）**：ch03 的 KV worked example（會被問，要能白板推導）→ ch06 的 batching 取捨 → ch08 的參數表 → ch12 的參考架構圖 → ch13 的容量規劃 worked example → ch15 的故障目錄 → ch18 的 45 分鐘系統設計完整示範 → 附錄 C 速查表。

### 與 plan.md 的對應

如果你同時在執行那份轉職計劃書，本書與它的模組對應如下：

| plan.md 模組 | 本書章節 | 旗艦專案對應 |
|---|---|---|
| 模組一：基礎與語言橋接 | ch03、ch04（+ 本章動手做的 Ollama 初體驗） | — |
| 模組二：編排/排程模擬層 ★ | ch11、ch12、ch14（模擬叢集系列 lab） | 旗艦專案①（KWOK + fake-gpu-operator + llm-d-inference-sim） |
| 模組三：效能建模與優化思維 | ch02、ch06、ch07、ch13 | 旗艦專案②（配置權衡研究） |
| 模組四：真 GPU 與真 vLLM ★ | ch05–ch08 | 旗艦專案③（vLLM 部署 + benchmark + 調參閉環，見 ch08 lab） |
| 模組五：分散式與生產級深度 | ch09、ch10、ch12、ch15、ch16 | 旗艦專案④（多模型/多節點平台） |
| 模組六：作品集與求職 | ch17、ch18 | 作品集整合與面試 |

plan.md 的「概念螺旋」設計與本書一致：KV cache 會在 ch03（數學）、ch05（管理）、ch10（路由）、ch13（容量訊號）、ch16（成本）以遞增的 altitude 反覆出現。每次回訪要能說出「這次深在哪」。

## 故障模式與防禦

本章的主題是轉職地圖，所以這裡的故障目錄是**轉職本身**會怎麼壞。每一條都是真實會發生的路徑：

| 故障模式 | 症狀 | 怎麼觀測到 | 防禦 |
|---|---|---|---|
| **從 CUDA kernel 開始學** | 三個月還在寫 matrix multiply，JD 上的東西一項沒碰 | 學習筆記全是數學，沒有一個能跑的服務 | 推論工程師 90% 的工作在 kernel 之上。kernel 是光譜最遠端（見職位表），等有明確需要再深入。plan.md 第八節同此判斷 |
| **只會跑 demo** | `ollama run` 跑通就覺得會了；面試被問「vLLM 為什麼快」答不出機制 | 說得出工具名，說不出它解什麼系統問題 | 每碰一個工具強制回答三問：解什麼問題、什麼時候會壞、怎麼觀測。本書每章的結構就是這三問 |
| **作品集做成 chatbot** | 花兩個月做了個 RAG 應用，被歸類為 AI application engineer | 專案 README 裡沒有任何 TTFT/吞吐/成本數字 | infra 作品的辨識特徵是**量化的系統指標**。套用你「降 RDS CPU 40%」的敘事模板：量測→診斷→優化→數據（見 ch18） |
| **背參數而不是學機制** | 熟記 vLLM 0.22 的參數表，下一版全作廢 | 版本升級後無法解釋行為差異 | vLLM 每 2–3 週發一版（2026-06）。正文學機制、註腳記版本；追 release notes 的迴圈見 ch18 |
| **用 CPU 直覺做容量判斷** | 「算力夠就夠了」→ 規劃出 2 張卡扛 1,000 並發的方案 | 本章 worked example 的第一步就是這個錯誤的示範 | 先過 ch02 roofline 與 ch03 KV 數學，再談容量。記住：先算記憶體，再算算力 |
| **雲 GPU 帳單失控** | 忘了關 instance，一夜燒掉一週預算 | 信用卡帳單 | 紀律：用完即關、設預算警報、能用模擬就不開卡（plan.md 的「模擬優先」原則；具體流程見 ch08） |
| **被新聞流淹沒** | 每天追模型發布，半年後發現一行 code 沒寫 | 收藏夾很滿，GitHub 很空 | 模型會過期，系統不變量不會（roofline、排程理論、容量數學）。每週固定 30 分鐘看 release notes，其餘時間寫東西（見 ch18） |

## 動手做

### Lab 1：你自己的技能遷移矩陣 **[紙上推演]**

別直接用本章的表——那是作者的履歷。自己做一遍，這個產出在 ch18 改履歷時直接複用。

1. 列出你履歷上 8–10 條最有份量的經驗（系統、優化、事故、工具）。
2. 對每一條回答三個問題：（a）這條經驗的**本質**是什麼系統問題？（剝掉工具名詞，例如「FluentBit pipeline」的本質是「從高噪音資料流萃取結構化指標」）；（b）GPU 推論世界裡哪裡有**同構**的問題？（翻本章的分層表找）；（c）工具換成什麼？
3. 標遷移度（高/中/零），把「零」的部分按本書章節排成學習順序。
4. **成功標準**：產出一頁表格，且每條「高遷移」都能講出一個具體的同構點。講不出具體對應、只能說「都是後端」的，誠實降級為「中」。

### Lab 2：第一次接觸——Ollama + SSE streaming 觀察 **[M1]**

目標：在自己的機器上跑起一個模型，親手量到 TTFT 與 ITL，摸到 prefill/decode 的體感差異。這是全書所有 benchmark 工作的第一塊磚。

```bash
# 1. 安裝與啟動（macOS）
brew install ollama
ollama serve &                 # 預設聽 :11434

# 2. 拉一個 3–4B 級模型（M1 16GB 跑得動；模型名以你執行當下的 ollama library 為準）
ollama pull llama3.2:3b

# 3. 先用 curl 看 SSE 的原始形狀（-N 關閉緩衝）
curl -N http://localhost:11434/v1/chat/completions \
  -H "content-type: application/json" \
  -d '{"model":"llama3.2:3b","stream":true,
       "messages":[{"role":"user","content":"用三句話解釋 KV cache"}]}'
```

觀察輸出：一行一個 `data: {...}` 的 SSE chunk，每個 chunk 帶一小段文字——這就是 token streaming 的線上形狀，你的 WebSocket 經驗的近親（差異：單向、HTTP 原生、proxy 友善，見 ch12）。

接著用你的主場語言量化它（示意碼，Node 20+，零相依）：

```js
// ttft.mjs — 量 TTFT 與 ITL
const t0 = performance.now();
const res = await fetch("http://localhost:11434/v1/chat/completions", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({
    model: "llama3.2:3b",
    stream: true,
    messages: [{ role: "user", content: "用三句話解釋 KV cache" }],
  }),
});
if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
let last = 0, ttft = null;
const gaps = [];
for await (const _chunk of res.body) {
  const now = performance.now();
  if (ttft === null) ttft = now - t0;
  else gaps.push(now - last);
  last = now;
}
gaps.sort((a, b) => a - b);
const p = (q) => gaps[Math.floor(q * (gaps.length - 1))]?.toFixed(1);
console.log(`TTFT ${ttft?.toFixed(0)} ms | chunks ${gaps.length + 1}`);
console.log(`ITL p50 ${p(0.5)} ms | p95 ${p(0.95)} ms | p99 ${p(0.99)} ms`);
```

（註：一個 HTTP chunk 不嚴格等於一個 token——本機環境下接近 1:1，但經過 proxy 或網路就不可靠了；嚴謹的量法見 ch14。）

實驗序列與**預期觀察**：

1. **跑第一次**：TTFT 可能高達數秒——因為 Ollama 在第一個請求時才把權重載入記憶體。恭喜，你遇到了人生第一次 **cold start**（分鐘級冷啟動的迷你版，見 ch12）。
2. **立刻跑第二次**：TTFT 掉到百 ms 級。權重已常駐，這次量到的才是真的 prefill 時間。
3. **換長 prompt**：把一段 2,000 字的文章貼進 `content` 再跑。觀察：**TTFT 顯著變長**（prefill 的工作量隨 prompt 長度線性以上成長），但 **ITL 幾乎不變**（decode 每步的工作量由模型大小決定，與 prompt 長度關係小——在這個量級下）。你剛親手量到了 prefill/decode 兩階段的分野，ch03 會解釋背後的數學。
4. **同時跑兩個**：開兩個終端機同時執行，觀察 ITL 變化——這是你對 batching 與資源競爭的第一次觀察（見 ch06）。

**成功標準**：能用自己量到的數字回答——TTFT 與 ITL 各是什麼、prompt 變長時哪個變慢、為什麼第一次請求特別慢。三題都能不看書回答，這個 lab 才算完成。

**故障排除**（Murphy 條款）：`connection refused` → `ollama serve` 沒起來或 port 被占；下載極慢或模型跑起來機器卡死 → 模型太大掉進 swap，換更小的模型；M1 8GB 機型建議用 1–2B 級模型。

## 自我檢核

答得出來才算過關。這些問題對齊真實面試的 screening 深度：

1. 不看書，畫出 LLM serving 的技術棧分層圖（至少六層），每層舉一個代表工具，並標出你目前最強與最弱的層。
2. 用兩分鐘向一位後端同事解釋：為什麼 10K CCU 的遊戲後端 20 台 c5.xlarge 就扛住，10K 並發 chat 卻要約 30 張 H100？（必須講到 KV cache 容量與 memory bandwidth，只講「模型很大」不及格。）
3. prefill 與 decode 各受限於什麼資源？TTFT 與 ITL 各對應哪個階段？
4. 為什麼 K8s 上 CPU 可以超賣而 GPU 不行？這對叢集利用率意味著什麼？（粗略即可，細節在 ch11。）
5. 為什麼 LLM 流量的負載均衡不能用 round-robin 或連線數？（提示：請求成本變異 + 有狀態。）
6. 「冷啟動分鐘級、流量尖峰秒級」這對矛盾，會迫使 autoscaling 設計做出什麼妥協？（方向對即可，細節在 ch13。）
7. 一句話複述全書三條主軸，並對每一條舉出本章 worked example 裡的一個對應數字或情節。
8. 五種職位光譜中，哪一種與你的履歷重疊最高？你的「零遷移清單」前三項是什麼？

## 延伸閱讀

- [Transformer Inference Arithmetic — kipply's blog](https://kipp.ly/transformer-inference-arithmetic/)：2022 年的文章但仍是入門推論效能直覺的最佳單篇，本章「算力帳 vs 記憶體帳」的思路源頭之一，ch02/ch03 的預習。
- [LLM Inference Performance Engineering: Best Practices — Databricks](https://www.databricks.com/blog/llm-inference-performance-engineering-best-practices)：用生產視角講 TTFT/TPOT、prefill/decode 與量化取捨，與本書方法論同調。
- [Efficient Memory Management for Large Language Model Serving with PagedAttention（vLLM 論文，arXiv:2309.06180）](https://arxiv.org/abs/2309.06180)：現代推論引擎的奠基論文；現在只需讀 abstract 與 introduction，ch05 會深入。
- [Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving（arXiv:2407.00079）](https://arxiv.org/abs/2407.00079)：Kimi 的生產架構論文，「LLM serving 是 memory 的生意」最有力的工業界證據，ch10 的主角之一。
- [a16z × OpenRouter — State of AI: 100 Trillion Token Study](https://a16z.com/state-of-ai/)：對 2025–2026 推論流量結構（agentic、reasoning）最好的公開實證，理解「需求面為什麼長這樣」。
- [llm-d 官方 blog](https://llm-d.ai/blog)：K8s 原生推論平台的第一手工程敘事，平台層往哪走的風向標（ch10/ch12 的主角之一）。
- [levels.fyi — ML/AI Software Engineer](https://www.levels.fyi/t/software-engineer/focus/ml-ai)：求職前校準薪資預期用；數字隨市場波動，看相對溢價結構即可。
- [Ollama OpenAI compatibility 文件](https://github.com/ollama/ollama/blob/main/docs/openai.md)：Lab 2 用到的 API 介面說明（未驗證最新路徑，以 repo 當下文件為準）。
