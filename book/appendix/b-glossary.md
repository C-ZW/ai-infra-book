# 附錄B — 術語表：LLM Serving 領域 EN→繁中對照

> **使用說明**：收錄全書出現的 LLM serving 領域術語，每條一行定義＋主要出現章節。按字母排序，數字/符號開頭放最前；同一個詞多章出現時，「主要見」標機制講解最深的那章。一般後端詞彙（HTTP、cache、queue 這類你已精通的）不收。時效性描述以本書寫作時（2026-06）為準。

## 數字與符號

- **$/Mtok ($ per Million tokens)** — LLM 推論的單位經濟學指標：每處理或產出一百萬個 token 的成本，由 GPU 時租價除以有效 token rate 推得。主要見 ch16。

## A

- **Acceptance Rate（接受率）** — speculative decoding 中 draft token 通過 target 模型驗證的比例，直接決定加速倍率；過低時投機反而比不投機更慢。主要見 ch07。
- **Active Parameters（激活參數量）** — MoE 模型每個 token 前向計算實際用到的參數量（如 1T total / 32B active）；active 決定算力成本、total 決定記憶體成本，是 MoE 改變 serving 經濟學的關鍵。主要見 ch03。
- **Admission Control（准入控制）** — 在系統最前端（gateway）依當前容量決定是否接受新請求的機制，是防止佇列崩潰與死亡螺旋的第一道防線。主要見 ch12、ch15。
- **Agentic Workload** — 由 AI agent 自主發起的多輪工具呼叫流量：長 session、極高 prefix 重複率、機器速率的突發請求，正在取代 chat 成為主流負載形態。主要見 ch17。
- **AIPerf** — NVIDIA 的 LLM 負載測試工具（前身 GenAI-Perf），量測 TTFT、ITL、token throughput 等推論指標。主要見 ch14。
- **All-Gather** — 集合通訊原語：每個參與者收集所有其他參與者的資料分片，結束時人人持有完整資料。主要見 ch09。
- **All-Reduce** — 集合通訊原語：對所有參與者的資料做歸約（如加總）後分發回每個參與者；tensor parallelism 每層 forward 需要兩次。主要見 ch09。
- **All-to-All** — 集合通訊原語：每個參與者送不同分片給每個其他參與者；是 expert parallelism 把 token 路由到 expert 所在 GPU 的核心通訊。主要見 ch09。
- **Arithmetic Intensity（運算強度）** — 每從記憶體搬一個 byte 所執行的浮點運算數（FLOP/byte），與 roofline model 搭配判斷 workload 是 compute-bound 還是 memory-bound。主要見 ch02。
- **Attention（注意力機制）** — transformer 的核心機制：每個 token 以 Query 對所有歷史 token 的 Key 計算相關性、再加權彙總 Value——「看所有歷史」正是 O(n²) 計算與 KV cache 的來源。主要見 ch03。
- **AWQ (Activation-aware Weight Quantization)** — weight-only INT4 量化方法：依 activation 分布找出重要權重通道並保護其精度。主要見 ch07。

## B

- **Batch Tier（批次方案）** — API 供應商的離線推論等級：以約五折價格換取非即時回應，用離峰閒置容量消化延遲不敏感的工作。主要見 ch16。
- **Bin-Packing** — 把 Pod 盡量塞滿同一節點的排程策略，用於減少 GPU 碎片化；代價是單節點故障的爆炸半徑變大。主要見 ch11。
- **Blackwell** — NVIDIA 2024–2026 的主力資料中心 GPU 世代（B200/B300），特徵是 HBM3e（B200 約 8 TB/s）與原生 FP4 tensor core。主要見 ch02。
- **Block Table** — PagedAttention 中每個 sequence 的邏輯 block 到實體 KV block 的映射表，角色等同 OS 的 page table。主要見 ch05。
- **BPE (Byte Pair Encoding)** — 主流 tokenizer 演算法：從高頻字節對反覆合併建立詞表，這是「token ≠ 字」的原因。主要見 ch03。
- **Brownout（降級運行）** — 過載時主動降級換容量的運維模式：縮小 max context、關閉 speculative decoding 等，犧牲部分功能保住整體可用性。主要見 ch15。

## C

- **Calibration（校準）** — 量化前用一小批代表性資料估計權重與 activation 的數值分布、決定縮放因子的步驟；校準資料不具代表性是量化品質劣化的常見根因。主要見 ch07。
- **Chargeback / Showback** — 內部多租戶把 GPU 成本按 per-token 用量歸因到各團隊的記帳機制；showback 只揭露數字、chargeback 實際入帳。主要見 ch16。
- **Chunked Prefill** — 把長 prompt 的 prefill 切成小塊、混進 decode batch 逐步執行的排程技術，避免長 prompt 卡住所有人的 decode 造成 ITL spike。主要見 ch06。
- **Cold Start（冷啟動）** — 推論服務從 Pod 排程到能服務首個請求的全過程（image pull → 權重載入 → 引擎初始化 → CUDA graph capture → warmup），時間以分鐘計，是 autoscaling 的根本約束。主要見 ch12。
- **Context Caching** — 各家 API 把 prefix caching 商品化的計費功能：cache 命中的 input token 享約 50–90% 不等的折扣（2026-06），是快取命中經濟價值的直接證據。主要見 ch05、ch16。
- **Context Length（上下文長度）** — 模型一次能處理的最大 token 數；KV cache 容量與 prefill 計算量都隨之成長，2026 年旗艦開源模型已達 1M。主要見 ch03。
- **Continuous Batching** — 以 decode step 為粒度動態重組 batch 的排程機制：新請求隨時加入、完成的隨時離開，是現代推論引擎吞吐的核心來源。主要見 ch06。
- **Coordinated Omission** — 負載測試的經典謬誤：closed-loop 測試在系統變慢時自動放慢送出速率，使量到的延遲嚴重偏向樂觀。主要見 ch14。
- **Copy-on-Write** — PagedAttention 讓多個 sequence 共享 KV block、寫入時才複製的機制，支撐平行取樣與 beam search。主要見 ch05。
- **cuBLAS** — NVIDIA 的 GPU 線性代數函式庫（矩陣乘法），幾乎所有推論引擎矩陣運算的底層。主要見 ch04。
- **CUDA (Compute Unified Device Architecture)** — NVIDIA 的 GPU 通用計算平台與程式模型，整個 NVIDIA 軟體生態（driver、toolkit、函式庫）的地基。主要見 ch04。
- **CUDA Graphs** — 把一串 GPU kernel 啟動序列錄製成圖、之後一次提交重放的機制，消除 decode 每步的 kernel launch overhead。主要見 ch07。
- **cuDNN** — NVIDIA 的深度學習 primitive 函式庫（attention、normalization 等常用運算的最佳化實作）。主要見 ch04。
- **CUTLASS** — NVIDIA 的開源 CUDA C++ template 函式庫，用於組裝自訂高效能矩陣乘法 kernel。主要見 ch04。

## D

- **Data Parallelism (DP)** — 把完整模型複製到多組 GPU、各自服務不同請求的平行化方式；最樸素也最常用的 scale-out。主要見 ch09。
- **DCGM (Data Center GPU Manager)** — NVIDIA 的資料中心 GPU 監控與健康管理套件；DCGM-exporter 把指標轉成 Prometheus 格式，是 K8s GPU 遙測的事實標準。主要見 ch14。
- **Decode** — 推論的第二階段：逐 token 自迴歸生成，每步都要讀完整模型權重與 KV cache，因此是 memory-bound。主要見 ch03。
- **Device Plugin** — K8s 讓節點回報 GPU 等擴展資源的傳統機制；資源以整數計、不可分割不可超賣，正被 DRA 取代。主要見 ch11。
- **DeviceClass** — DRA 資源模型中由管理員定義的裝置類別，使用者透過 ResourceClaim 引用它請求裝置。主要見 ch11。
- **DistServe** — 提出 prefill/decode 分離的代表性學術工作之一（2024），證明分離可同時改善 TTFT 與 TPOT 的 SLO 達成率。主要見 ch10。
- **Diurnal Pattern（日夜週期）** — 流量隨日夜規律起伏的形態，是預測式擴縮最可靠的依據。主要見 ch13。
- **DP Attention** — MoE serving 的組合技：attention 層以 data parallelism 各自處理不同請求（避免 MLA 類模型在 TP 下重複存放 KV cache），expert 層以 EP 橫跨全部 GPU。主要見 ch09。
- **DRA (Dynamic Resource Allocation)** — K8s 新一代裝置資源模型（v1.34 GA）：以 ResourceClaim/DeviceClass/structured parameters 描述與分配 GPU，解決 device plugin 整數資源表達力不足的問題。主要見 ch11。
- **Draft Model** — speculative decoding 中負責快速猜測多個候選 token 的小模型，猜測結果由 target 模型一次平行驗證。主要見 ch07。
- **Drain (Graceful Drain)** — 節點或 Pod 下線前停收新請求、等待 in-flight 請求完成的流程；LLM streaming 請求可長達分鐘級，drain timeout 必須按 p99.9 請求時長設計。主要見 ch15。
- **DSA (DeepSeek Sparse Attention)** — DeepSeek V3.2 起採用的稀疏注意力機制：每個 token 只關注被挑選的部分歷史，壓低長上下文的計算與 KV 成本。主要見 ch17。
- **Dynamo (NVIDIA Dynamo)** — NVIDIA 的開源分散式推論框架：提供 planner、KV-aware router、KVBM 與 NIXL 傳輸層，統一支援 vLLM/SGLang/TensorRT-LLM 後端。主要見 ch10、ch12。

## E

- **EAGLE / EAGLE-3** — 主流 speculative decoding 方案：用 target 模型自身 hidden state 訓練的輕量 draft head 連續猜測多個 token，接受率高於獨立 draft model。主要見 ch07。
- **ECC (Error-Correcting Code)** — GPU 記憶體的錯誤偵測與修正機制；single-bit 錯誤可修正，double-bit 錯誤會讓工作負載中止，是最常見的 GPU 硬體故障訊號之一。主要見 ch02、ch15。
- **Embedding** — 把 token id 映射成連續向量的查表層，transformer 的輸入層。主要見 ch03。
- **Endpoint Picker (EPP)** — Gateway API Inference Extension 的核心元件：透過 ext-proc 協定取得各 engine Pod 的即時指標（佇列深度、KV 利用率、prefix cache 狀態），替每個請求挑選最佳後端。主要見 ch12。
- **Eval Gate（評測關卡）** — 發布流程中以任務型評測分數作為放行條件的關卡；模型「變笨」不會出現在 5xx 裡，必須靠 eval 攔截品質迴歸。主要見 ch15。
- **Expert Parallelism (EP)** — MoE 專屬的平行化：把 experts 分散到多張 GPU，token 經 all-to-all 通訊路由到其 expert 所在的卡。主要見 ch09。
- **Extended Resource** — K8s 中以整數計數的自訂資源型別（如 `nvidia.com/gpu`），不可分割、不可超賣——GPU 資源模型一切限制的根源。主要見 ch11。

## F

- **fake-gpu-operator** — 模擬 NVIDIA GPU Operator 行為的開源測試工具，讓沒有 GPU 的叢集（kind + KWOK）也能演練 GPU 排程與監控。主要見 ch11。
- **Fallen off the Bus** — GPU 從 PCIe bus 上「消失」的硬體故障（Xid 79），driver 完全失去裝置，通常需要重啟節點甚至送修。主要見 ch15。
- **FCFS (First-Come, First-Served)** — 先到先服務的排程策略，vLLM scheduler 的預設；簡單公平但有 head-of-line blocking 風險。主要見 ch06。
- **FFN (Feed-Forward Network)** — transformer 每層中接在 attention 後的矩陣乘法區塊（升維→降維），佔 dense 模型的多數參數；MoE 替換的就是這部分。主要見 ch03。
- **FlashAttention** — IO-aware 的 attention kernel：以 tiling 在 SRAM 內完成 softmax 歸約、大幅減少 HBM 往返，把 attention 的記憶體開銷從 O(n²) 降到 O(n)。主要見 ch07。
- **FlashInfer** — 專為 LLM serving 設計的開源 attention kernel 函式庫，原生支援 paged KV cache 等 serving 特化場景。主要見 ch07。
- **FP8** — 8-bit 浮點格式（E4M3/E5M2），Hopper 世代起有原生 tensor core 支援；2026 年生產推論的主流精度之一，權重與 KV cache 都可用。主要見 ch07。
- **Free-Threading** — Python 的無 GIL 建置模式：3.13 實驗性引入、3.14 起正式支援，多執行緒 CPU-bound 工作不再被全域鎖序列化。主要見 ch04。

## G

- **Gang Scheduling** — 「全有或全無」的排程語意：多 Pod 工作要嘛全部同時排上、要嘛都不排，避免多節點推論部分就緒造成死鎖與 GPU 空轉。主要見 ch11。
- **Gateway API Inference Extension (GIE / IGW)** — K8s Gateway API 的推論擴展（已 GA）：定義 InferencePool 與 Endpoint Picker，讓 L7 路由能感知模型負載與 KV cache 狀態——因為 LLM 請求成本變異數百倍，傳統 LB 演算法失效。主要見 ch12。
- **GGUF** — llama.cpp 生態的模型檔案格式（內含權重、量化資訊與 metadata），本地與邊緣推論的事實標準。主要見 ch07、ch08。
- **GIL (Global Interpreter Lock)** — CPython 的全域直譯器鎖：同一時刻僅一條執行緒執行 Python bytecode，正被 free-threading 逐步淘汰。主要見 ch04。
- **Goodput** — 滿足 SLO 的有效吞吐量：只計入 TTFT/ITL 都達標的請求所貢獻的 token rate，是比 raw throughput 誠實的容量指標。主要見 ch06、ch14。
- **GPTQ** — weight-only INT4 量化方法：逐層利用二階資訊最小化量化誤差。主要見 ch07。
- **GPU Fragmentation（GPU 碎片化）** — 叢集總卡數足夠、但分散在各節點湊不出單一工作所需整組 GPU 的浪費形態；直接反映成錢。主要見 ch11、ch16。
- **GPU Operator (NVIDIA GPU Operator)** — 以 operator 模式把 driver、container toolkit、device plugin、DCGM-exporter、MIG manager、NFD 等 GPU 軟體棧整套部署進 K8s 的元件。主要見 ch11。
- **GPUDirect Storage (GDS)** — 讓 NVMe/儲存資料以 DMA 直達 GPU 記憶體、繞過 CPU bounce buffer 的技術，加速權重載入與 KV offloading。主要見 ch10、ch12。
- **GQA (Grouped-Query Attention)** — 多個 query head 共用一組 KV head 的 attention 變體，把 KV cache 縮小數倍而品質損失輕微；Llama 3 等主流模型標配。主要見 ch03。
- **Grace** — NVIDIA 的 Arm 架構資料中心 CPU，與 GPU 以 NVLink-C2C 互連組成 GB200/GB300 等超級晶片。主要見 ch02。

## H

- **HBM (High Bandwidth Memory)** — GPU 的堆疊式高頻寬主記憶體（H100 為 HBM3 3.35 TB/s、B200 為 HBM3e 約 8 TB/s）；其頻寬是 decode 吞吐的物理上限，本書「memory 的生意」主軸的物理基礎。主要見 ch02。
- **Head-of-Line Blocking** — 佇列前端的長工作堵住後面所有短工作的現象；LLM 中「長 prefill 卡住所有人的 decode」是典型案例。主要見 ch06。
- **Headroom（容量餘裕）** — 容量規劃中刻意保留的緩衝，用來吸收流量尖峰與分鐘級的 scale-up 延遲；headroom 大小由冷啟動時間與尖峰係數共同決定。主要見 ch13。
- **HiCache** — SGLang 的階層式 KV cache：以 UnifiedRadixTree 把 radix tree 延伸到 CPU RAM 與儲存層。主要見 ch08。
- **Hopper** — NVIDIA 2022–2024 的主力 GPU 世代（H100/H200），首次原生支援 FP8 tensor core。主要見 ch02。

## I

- **inference-perf** — kubernetes-sigs 的標準化 LLM benchmark 工具：TTFT/TPOT/goodput 量測、Poisson/trace replay 負載產生、engine-agnostic（任何 OpenAI 相容端點）。主要見 ch14。
- **InferencePool** — Gateway API Inference Extension 的 CRD：宣告一組推論 Pod 為可智慧路由的資源池，由 Endpoint Picker 決定每個請求的落點。主要見 ch12。
- **InfiniBand (IB)** — 跨節點 RDMA 高速網路，多節點訓練與推論的主流互連；低成本替代品是 RoCE。主要見 ch02、ch09。
- **ITL (Inter-Token Latency)** — 相鄰兩個輸出 token 之間的時間間隔，決定 streaming 的流暢度；與 TPOT 常混用，但 ITL 強調逐 token 間隔的分布（看 p99）。主要見 ch14。

## K

- **KEDA (Kubernetes Event-Driven Autoscaling)** — 以外部事件或指標（佇列深度、Prometheus query）驅動 HPA 的擴縮框架，LLM autoscaling 最常用的執行機制。主要見 ch13。
- **Kernel Fusion** — 把多個相鄰 GPU kernel 合併成一個、省去中間結果寫回 HBM 再讀回的最佳化手法。主要見 ch07。
- **KPA (Knative Pod Autoscaler)** — Knative 的 Pod 擴縮器：以並發數/RPS 為訊號、支援 scale-to-zero；用於 LLM 時要直面分鐘級冷啟動。主要見 ch13。
- **KServe** — K8s 上的模型服務平台；其 LLMInferenceService CRD（仍為 alpha，2026-06）建構在 llm-d 之上，代表傳統 model serving 向 LLM 原生架構的演進。主要見 ch12。
- **Kueue** — K8s 的工作佇列與配額排程器：提供 quota、cohort 借用、gang admission，管理 GPU 等稀缺資源的公平分配與搶占。主要見 ch11。
- **KV Cache** — 把每層 attention 算出的 Key/Value 向量存起來避免重算的快取；大小 = 2 × layers × kv_heads × head_dim × bytes × tokens，隨 context 線性成長，是 LLM serving 最重要的記憶體開銷。主要見 ch03、ch05。
- **KV Cache Utilization** — 已用 KV block 占引擎 KV 總容量的比例：判斷飽和、預測 preemption、驅動 autoscaling 的關鍵健康訊號。主要見 ch13、ch14。
- **KV Connector** — vLLM 的 KV cache 傳輸與外接抽象層（NixlConnector、LMCacheConnector 等），P/D 分離與分層快取的標準接口。主要見 ch10。
- **KV Offloading（KV 分層卸載）** — 把 KV cache 在 GPU HBM → CPU RAM → NVMe/遠端儲存之間分層存放的機制，用慢一級的儲存換 HBM 容量。主要見 ch05。
- **KV-Aware Routing** — 路由器依各 replica 的 KV cache 內容（prefix 命中可能性）與即時負載挑選後端的策略；本質是有狀態的負載均衡，cache 命中價值遠高於一般 session affinity。主要見 ch10。
- **KVBM (KV Block Manager)** — Dynamo 的 framework-agnostic KV cache 分層管理元件。主要見 ch10。
- **KWOK (Kubernetes WithOut Kubelet)** — 模擬數千個無 kubelet 假節點的 kubernetes-sigs 工具，GPU 叢集排程實驗的標準地基。主要見 ch11。

## L

- **Latency-Throughput Frontier** — 對同一系統掃描不同負載率畫出的延遲—吞吐曲線；比任何單點數字誠實的 benchmark 呈現方式。主要見 ch14。
- **LeaderWorkerSet (LWS)** — K8s 的多 Pod 群組部署原語：一個 leader 帶 N 個 worker 作為單一單位排程、擴縮與重啟，是多節點推論（TP/PP 跨機）的標準部署形態。主要見 ch11。
- **Linear Attention（線性注意力）** — 把 attention 改寫為線性複雜度的架構家族（Gated Delta Networks、Mamba 混合架構等）：以固定大小的狀態取代線性成長的 KV cache，可能顛覆現有 KV 數學。主要見 ch17。
- **llama.cpp** — 純 C/C++ 的輕量推論引擎，主攻 CPU 與消費級硬體；GGUF 格式與本地量化生態的核心。主要見 ch08。
- **llm-d** — K8s 原生的分散式推論框架（Red Hat/Google/IBM 系）：以 Gateway API Inference Extension 為路由層，提供 prefix-cache-aware scheduling 與 P/D 分離等「well-lit paths」。主要見 ch10、ch12。
- **llm-d-inference-sim** — llm-d 子專案：無需 GPU 即可模擬 vLLM 的 API 與指標行為，用於測試路由、擴縮與監控層；本書 [M1] 實驗的主力工具。主要見 ch11、ch14。
- **LMCache** — 開源 KV cache 分層儲存引擎：把 KV 外溢到 CPU RAM、SSD、Redis、S3 等後端，與 vLLM 原生整合。主要見 ch05。
- **Load Shedding（卸載流量）** — 過載時主動丟棄部分請求以保護核心容量的手段；LLM 場景常按優先級丟（priority shedding），先犧牲批次與低付費層流量。主要見 ch13、ch15。
- **Logits** — 模型最後一層輸出的未正規化分數向量（維度 = 詞表大小），經 softmax 與 sampling 決定下一個 token。主要見 ch03。
- **LoRA (Low-Rank Adaptation)** — 以低秩矩陣微調模型的方法；serving 時一個 base 模型可同時掛載多個 LoRA adapter（multi-LoRA serving），是低成本多租戶客製的基礎。主要見 ch12。
- **LPU (Language Processing Unit)** — Groq 的推論專用處理器：權重放 SRAM 而非 HBM，以容量換極低延遲（NVIDIA 已於 2025-12 以約 $20B 取得其技術授權與核心團隊，Groq 公司仍獨立營運）。主要見 ch02、ch17。

## M

- **Mamba** — 以 state space model 取代 attention 的模型架構：狀態大小固定、不隨 context 成長；實務上多以與 attention 混合（hybrid）的形態落地。主要見 ch17。
- **MBU (Memory Bandwidth Utilization)** — 實際用到的記憶體頻寬占硬體峰值的比例，decode 階段效率的關鍵指標。主要見 ch14、ch16。
- **MCP (Model Context Protocol)** — agent 與工具連接的開放協定（Anthropic 發起，現由 Linux Foundation 旗下基金會託管），agentic 流量標準化的主要推手。主要見 ch17。
- **MFU (Model FLOPs Utilization)** — 實際達成的 FLOPs 占硬體峰值算力的比例；「GPU 忙碌但無效」的照妖鏡。主要見 ch14、ch16。
- **MI355X (AMD Instinct MI355X)** — AMD 的旗艦資料中心 GPU（CDNA 4，288 GB HBM3E、8 TB/s），NVIDIA 之外最主要的選項；MI400/Helios 機架預計 2026 H2。主要見 ch02。
- **MIG (Multi-Instance GPU)** — 把一張 GPU 硬體分割成多個有獨立記憶體與算力配額的實例（H100 最多 7 個），隔離性最強的 GPU 共享技術，適合多租戶小模型。主要見 ch11。
- **MLA (Multi-head Latent Attention)** — DeepSeek 的 attention 變體：把 KV 壓縮成低維 latent 向量存放，KV cache 比 GQA 再小一個量級。主要見 ch03。
- **MLX** — Apple 的機器學習框架，針對 Apple Silicon 統一記憶體最佳化，M 系列晶片本地推論的主要選項之一。主要見 ch08。
- **MoE (Mixture of Experts)** — 把 FFN 換成多個 expert、每個 token 只激活少數幾個的架構：記憶體要裝下全部參數、算力只用 active 部分，從根本改變 serving 的經濟學與平行化策略。主要見 ch03。
- **Mooncake** — Moonshot AI（Kimi）的 KVCache-centric 推論平台：以分離式 KV cache 池為核心的 P/D 分離架構，最早公開生產數據的系統之一；其 Transfer Engine 與 Store 已開源。主要見 ch10。
- **MPS (Multi-Process Service)** — NVIDIA 讓多個 process 同時共享一張 GPU 的機制：可劃分算力但故障隔離弱，隔離性介於 time-slicing 與 MIG 之間。主要見 ch11。
- **MQA (Multi-Query Attention)** — 所有 query head 共用單一組 KV head 的極端變體：KV cache 最小，但品質損失比 GQA 明顯。主要見 ch03。
- **MTBF (Mean Time Between Failures)** — 平均故障間隔；單卡 MTBF 再長，數千卡叢集的整體故障率仍會讓硬體故障成為日常而非例外。主要見 ch15。
- **MTP (Multi-Token Prediction)** — 模型原生內建多 token 預測頭的 speculative decoding 形態，DeepSeek-V3 起採用，免去外掛 draft model。主要見 ch07。
- **MXFP4** — OCP microscaling 標準的開放 4-bit 浮點格式（block 共享 scale）；gpt-oss 權重即以 MXFP4 原生發布。主要見 ch07。

## N

- **NCCL (NVIDIA Collective Communications Library)** — NVIDIA 的集合通訊函式庫（all-reduce/all-gather/all-to-all），多卡推論的通訊地基；NCCL hang（一卡出事、全組僵住且不報錯）是多卡世界最痛的故障。主要見 ch09、ch15。
- **Neocloud** — 專營 GPU 租賃的新型雲端業者（CoreWeave、Lambda、RunPod、Vast.ai 等），同卡型價格約為 hyperscaler 的 1/2–1/3（2026-06 快照）。主要見 ch16。
- **NIXL (NVIDIA Inference Xfer Library)** — KV cache 傳輸抽象層：統一 UCX、GPUDirect Storage、S3 等 backend 的 API，是 Dynamo、vLLM、Ray Serve 做 P/D 分離的共同地基。主要見 ch10。
- **Node Feature Discovery (NFD)** — 自動偵測節點硬體特性（GPU 型號、互連拓撲等）並打上 label 的 K8s 元件，拓撲感知排程的前提。主要見 ch11。
- **Noisy Neighbor** — 多租戶下單一租戶（例如一個 200k-context 使用者）耗盡共享資源（KV cache、batch slot）拖累其他租戶的現象。主要見 ch16。
- **NVFP4** — NVIDIA 的 4-bit 浮點格式，Blackwell（B200/B300）tensor core 原生支援；Hopper 及更早世代無原生 FP4。主要見 ch07。
- **NVL72 (GB200/GB300 NVL72)** — 把 72 顆 GPU 與 36 顆 Grace CPU 用 NVSwitch 連成單一 NVLink domain 的機架級系統；rack 取代 server 成為設計與採購單位。主要見 ch02。
- **NVLink** — NVIDIA GPU 之間的高速直連互連（第 5 代每 GPU 1.8 TB/s 雙向），頻寬比 PCIe 高一個量級——這是 TP 通常不出 NVLink domain 的原因。主要見 ch02、ch09。
- **NVSwitch** — 把多顆 GPU 全互連成單一 NVLink domain 的交換晶片。主要見 ch02。

## O

- **Ollama** — 包裝 llama.cpp 的本地模型工具：一行指令下載並 serve 模型，本書 M1 實驗的入門起點。主要見 ch01、ch08。
- **Open-Loop / Closed-Loop** — 負載測試的兩種模式：open-loop 按固定到達率送請求（不等回應）、closed-loop 等回應才送下一個；LLM benchmark 必須用 open-loop 才能避免 coordinated omission。主要見 ch14。
- **OpenAI-Compatible API** — 與 OpenAI Chat Completions 介面相容的 API 形狀；推論引擎、閘道與聚合層的 de facto 標準。主要見 ch12。
- **OpenRouter** — 聚合多家模型供應商的推論路由市場；其公開流量研究是 agentic/reasoning 流量趨勢最常被引用的數據源。主要見 ch17。
- **Orca** — 提出 iteration-level scheduling（continuous batching 前身）的開創性系統論文（OSDI '22）。主要見 ch06。

## P

- **P/D Disaggregation（Prefill/Decode 分離）** — 把 compute-bound 的 prefill 與 memory-bound 的 decode 分到不同 GPU 池執行、以 KV cache 傳輸串接的架構；2025–2026 大規模推論的主旋律，小規模部署則是複雜度稅。主要見 ch10。
- **PagedAttention** — vLLM 的核心創新：把 KV cache 切成固定大小 block、以 block table 做邏輯到實體映射——等同 OS 的 virtual memory paging，幾乎消除 KV 記憶體碎片。主要見 ch05。
- **Perplexity（困惑度）** — 語言模型對文本的預測不確定性指標；量化品質評估的傳統手段，但對下游任務劣化不敏感，不可單獨依賴。主要見 ch07。
- **Pipeline Parallelism (PP)** — 把模型按層切成多個 stage 串成流水線的平行化：跨節點友善、吞吐導向，但有 bubble（流水線空轉）問題。主要見 ch09。
- **Poisson Arrival Process** — benchmark 模擬真實隨機到達的請求產生方式：請求間隔呈指數分布，比固定間隔更能暴露突發下的尾延遲。主要見 ch14。
- **Preemption（搶占）** — KV cache 不足時排程器強制中止部分執行中請求讓位的機制（處理方式為 recompute 或 swap）；preemption 風暴是死亡螺旋的引信。主要見 ch06。
- **Prefill** — 推論第一階段：平行處理整個 prompt 並建立 KV cache，計算量 O(n²)、compute-bound；其耗時是 TTFT 的主要成分。主要見 ch03。
- **Prefix Caching** — 跨請求重用相同前綴（system prompt、多輪歷史）KV cache 的機制（vLLM 用 hash-based block、SGLang 用 radix tree）；agentic 流量下命中率可達九成，直接轉換成 TTFT 與成本。主要見 ch05。
- **PreStop Hook** — K8s Pod 終止前執行的鉤子；LLM serving 用它觸發「停收新請求＋等待 in-flight streaming 完成」的 graceful drain 流程。主要見 ch15。
- **Priority Scheduling** — 按請求優先級排序的引擎排程策略（vLLM 以 `--scheduling-policy priority` 啟用，FCFS 為 tie-breaker），讓互動流量優先於批次流量。主要見 ch06。

## Q

- **Quantization（量化）** — 用更低位元數表示權重或 activation 以節省記憶體與頻寬的技術（FP8、INT4、FP4 等）；收益是吞吐與卡數，代價是品質風險與工程驗證成本。主要見 ch07。

## R

- **RadixAttention** — SGLang 的 prefix caching 機制：以 radix tree 組織 KV cache，自動共享任意長度的共同前綴。主要見 ch05、ch08。
- **Ray Serve** — Ray 生態的模型服務框架；`ray.serve.llm` 提供 LLM 一級 API 與 P/D 分離 pattern，強項是 Python 端的組合彈性。主要見 ch12。
- **RDMA (Remote Direct Memory Access)** — 繞過遠端 CPU 直接讀寫其記憶體的網路技術（InfiniBand/RoCE 實作），KV 傳輸與 NCCL 跨節點通訊的基礎。主要見 ch09、ch10。
- **Reasoning Model（推理模型）** — 輸出最終答案前先生成思考鏈的模型（thinking/non-thinking 雙模式已是 2026 開源旗艦標配）；把推論成本重心移向 decode 階段。主要見 ch17。
- **Recompute** — preemption 的處理方式之一：直接丟棄被踢請求的 KV cache，重新排隊後從頭重算 prefill。主要見 ch06。
- **ResourceClaim** — DRA 中使用者宣告「我需要什麼樣的裝置」的 K8s 物件，由 DRA driver 配對具體裝置來滿足。主要見 ch11。
- **Retry Budget** — 限制重試流量占總流量比例的機制；LLM 請求昂貴且長，無節制重試會把局部過載直接推成全面雪崩。主要見 ch15。
- **RoCE (RDMA over Converged Ethernet)** — 在乙太網上跑 RDMA 的協定，InfiniBand 的低成本替代。主要見 ch02。
- **Roofline Model** — 以記憶體頻寬與峰值算力兩條「屋頂」判斷 workload 瓶頸的分析模型：arithmetic intensity 低於拐點即 memory-bound——本書最重要的分析工具。主要見 ch02。
- **Rubin** — NVIDIA 的下一代 GPU 平台（Vera Rubin NVL72，288 GB HBM4、約 13 TB/s），2026 H2 起於主要雲端供應（2026-06 時點為預告）。主要見 ch02、ch17。

## S

- **Sampling（取樣）** — 從 logits 機率分布選出下一個 token 的過程（greedy/temperature/top-p/top-k）；參數選擇影響輸出重現性與可快取性。主要見 ch03。
- **Scale-to-Zero** — 無流量時縮到零副本的能力；LLM 服務要為此承受分鐘級冷啟動，只適合延遲不敏感的服務等級。主要見 ch12、ch13。
- **Sequence Parallelism (SP)** — 沿序列維度把超長 context 的 prefill 切分到多卡的平行化方式。主要見 ch09。
- **SGLang** — 與 vLLM 並列的開源推論引擎雙雄之一：核心賣點是 RadixAttention 與結構化輸出，xAI 等在生產大規模採用（專案自述）。主要見 ch08。
- **Shadow Traffic** — 把生產流量複製一份打到新版本、但不把回應回傳給使用者的驗證手段；攔截 5xx 看不到的品質迴歸。主要見 ch15。
- **SIMT (Single Instruction, Multiple Threads)** — GPU 的執行模型：一條指令同時驅動一個 warp（32 條執行緒）執行。主要見 ch02。
- **SLO Burn Rate** — 錯誤預算被消耗的速率；比單點閾值更穩健的告警與擴縮訊號。主要見 ch13、ch14。
- **SLO-Aware Scheduling** — 把各請求的 TTFT/ITL 目標納入引擎排程決策的策略，例如讓延遲預算寬鬆的批次請求讓位給互動請求。主要見 ch06。
- **SM (Streaming Multiprocessor)** — GPU 的基本計算單元（H100 有 132 個），各自帶 tensor core、暫存器與 warp scheduler；注意「SM 占用率高」不等於有效工作。主要見 ch02。
- **Speculative Decoding（投機解碼）** — 用便宜機制（draft model、EAGLE、n-gram）先猜多個 token、由目標模型一次平行驗證的加速技術；低 batch 時有效，高 batch 時收益遞減甚至為負。主要見 ch07。
- **Splitwise** — 與 DistServe 同期提出 P/D 分離的學術工作（Microsoft），P/D 架構的源頭之一。主要見 ch10。
- **Starvation（飢餓）** — 低優先級或長請求在排程中持續搶不到資源的狀態；priority scheduling 必須搭配 aging 等手段防範。主要見 ch06。
- **Swap** — preemption 的處理方式之一：把被踢請求的 KV cache 搬到 CPU RAM 暫存，恢復時再搬回 GPU。主要見 ch06。

## T

- **Temperature** — sampling 時對 logits 的縮放係數：越低輸出越確定，0 等同 greedy；直接影響重現性。主要見 ch03。
- **Tensor Core** — GPU 內專做矩陣乘加的硬體單元；各世代支援的數值格式不同（Hopper 起 FP8、Blackwell 起 FP4），是 LLM 算力的真正來源。主要見 ch02。
- **Tensor Parallelism (TP)** — 把每層權重矩陣切到多卡、各算部分結果再 all-reduce 合併的平行化：降低單卡記憶體與延遲，但每層兩次通訊使它通常不跨出 NVLink domain。主要見 ch09。
- **TensorRT-LLM** — NVIDIA 的編譯式推論引擎：以 ahead-of-time 最佳化換取峰值效能，代價是彈性與迭代速度低於 vLLM/SGLang。主要見 ch08。
- **Test-Time Compute** — 在推論時投入更多算力（長思考鏈、多分支探索）換取輸出品質的範式；使輸出 token 量爆炸，重塑容量規劃與計價模型。主要見 ch17。
- **Thermal Throttling** — GPU 過熱時自動降頻保護硬體的機制；症狀是效能無聲衰退而非報錯，必須靠溫度與時脈指標觀測。主要見 ch02、ch15。
- **Thinking Budget** — 限制 reasoning 模型思考 token 用量的控制機制，成本與品質之間的調節閥。主要見 ch17。
- **Time-Slicing** — 多個容器分時輪流共用同一張 GPU 的共享方式：無記憶體隔離、無算力保證，僅適合開發環境。主要見 ch11。
- **Token** — 模型處理文本的基本單位（BPE 切出的子詞）；LLM 世界計價、限流與容量規劃的計量單位。主要見 ch03。
- **Token Bucket** — 限流演算法：以固定速率補充、按請求消耗的桶；在 LLM rate limiting 中「token」是字面意義——按模型 token 計量。主要見 ch16。
- **Token Budget** — chunked prefill 排程中每個 decode step 允許處理的 token 總量上限，控制 prefill 對 ITL 的干擾程度。主要見 ch06。
- **TPOT (Time Per Output Token)** — 平均每個輸出 token 的生成時間（總生成時間除以輸出 token 數，通常不含首 token）；與 ITL 同族但取平均視角。主要見 ch14。
- **TPU (Tensor Processing Unit)** — Google 自研的 AI 加速器；2026 年主力為 Ironwood（TPU v7），驅動 Gemini 生產推論。主要見 ch02。
- **Trainium** — AWS 自研的 AI 訓練/推論晶片；Trainium3（2025-12 發表）是 AWS 首款 3nm AI 晶片。主要見 ch02。
- **Triton (OpenAI Triton)** — 用 Python 語法撰寫 GPU kernel 的語言與編譯器；注意與 NVIDIA Triton Inference Server 同名不同物。主要見 ch04。
- **TTFT (Time To First Token)** — 從送出請求到收到第一個 token 的延遲，由排隊時間與 prefill 構成；互動體驗最核心的延遲指標。主要見 ch01、ch14。

## U

- **UCX (Unified Communication X)** — 高效能通訊框架，NIXL 的傳輸 backend 之一。主要見 ch10。

## V

- **Vidur** — Microsoft 的 LLM 推論系統模擬器（研究性工具，維護狀態不明）：預測 TTFT/TPOT、輔助容量規劃與配置搜索。主要見 ch13。
- **vLLM** — 2026 年最主流的開源推論引擎：PagedAttention 與 continuous batching 的發源地；本書寫作時為 v0.22.x、V1 是唯一引擎，選型的 de facto 預設值。主要見 ch08。
- **Volcano** — 批次工作負載導向的 K8s 排程器，提供 gang scheduling 與佇列管理；與 Kueue 同領域的另一選項。主要見 ch11。

## W

- **W8A8** — 權重與 activation 都量化到 8-bit 的方案（如 FP8 W8A8）：矩陣乘法直接在低精度 tensor core 上執行，比 weight-only 量化多省算力。主要見 ch07。
- **Warm Pool** — 預先啟動、權重已載入的待命副本池：用空置成本換 scale-up 速度，對沖分鐘級冷啟動。主要見 ch13。
- **Warp** — GPU 排程的基本單位：32 條執行緒以 SIMT 方式同步執行同一指令。主要見 ch02。
- **Well-Lit Paths** — llm-d 的設計哲學：只提供少數幾條文件化、經 benchmark 驗證的生產部署路徑，而非開放無限組合。主要見 ch10、ch12。
- **Wide-EP (Wide Expert Parallelism)** — 把 MoE experts 攤到數十至數百張卡的大規模 EP 部署（DeepSeek 式）；prefill 群與 decode 群可採不同 EP 度。主要見 ch09。

## X

- **Xid** — NVIDIA driver 的 GPU 錯誤代碼體系（如 Xid 48 = ECC double-bit、Xid 79 = fallen off the bus），GPU 硬體故障診斷的第一手訊號。主要見 ch02、ch15。
- **xPyD** — P/D 分離部署中「x 個 prefill 實例對 y 個 decode 實例」的配比記號；配比由流量形態（輸入/輸出 token 比例）決定。主要見 ch10。
