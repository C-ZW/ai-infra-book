# 全書章節規格（內部文件）

每章作者：先讀 `style-guide.md`（寫作契約）與 `landscape-2026.md`（事實基準），再讀本檔你負責的章節段。**嚴守章節邊界**：別章的主題用一句話＋`（見 chNN）`帶過，不展開。

## 全書三條主軸（每章都要呼應至少一條）

1. **LLM serving 本質上是 memory 的生意**：幾乎所有設計決策最終都回到 memory bandwidth 與 memory capacity 的取捨。
2. **量測 → 診斷 → 優化 → 用數據證明**：讀者既有的效能工程方法論，原封不動搬到 GPU 世界。
3. **把分散式系統直覺翻譯到新物理**：排程、路由、一致性、可觀測性的直覺都成立，但物理常數變了（ms→μs、GB→TB/s、stateless→重狀態）。

## 目錄總表

| 章 | 檔案 | 一句話範圍 |
|---|---|---|
| ch01 | part-1-foundations/ch01-from-backend-to-ai-infra.md | 全書地圖：技術棧分層、職位光譜、技能遷移矩陣、怎麼讀這本書 |
| ch02 | part-1-foundations/ch02-gpu-architecture.md | GPU 硬體：SM/HBM/roofline、互連、機房現實、硬體版圖 |
| ch03 | part-1-foundations/ch03-inference-physics.md | Transformer 推論物理：attention、KV cache 數學、prefill/decode、MoE 結構 |
| ch04 | part-1-foundations/ch04-language-bridge.md | 語言橋接：Python（給 TS 工程師）、PyTorch 讀碼、Go 讀 K8s controller、CUDA 概念 |
| ch05 | part-2-inference-engine/ch05-kv-cache.md | KV cache 系統：PagedAttention、prefix caching、KV 量化、offloading 分層 |
| ch06 | part-2-inference-engine/ch06-batching-scheduling.md | 單機排程：continuous batching、chunked prefill、preemption、SLO-aware 排程 |
| ch07 | part-2-inference-engine/ch07-model-optimization.md | 模型加速：quantization、speculative decoding、attention kernels、CUDA graphs |
| ch08 | part-2-inference-engine/ch08-engines-in-practice.md | 引擎實戰：vLLM 架構與參數、SGLang、TensorRT-LLM、選型、單卡部署 |
| ch09 | part-3-distributed/ch09-parallelism.md | 平行化：TP/PP/DP/EP/SP、NCCL、拓撲、wide-EP MoE serving |
| ch10 | part-3-distributed/ch10-disaggregation-routing.md | P/D 分離與路由：Dynamo/llm-d/Mooncake、KV 傳輸、KV-aware routing |
| ch11 | part-4-platform/ch11-kubernetes-for-gpus.md | K8s 上的 GPU：device plugin→DRA、MIG/MPS/time-slicing、Kueue、拓撲排程、節點生命週期 |
| ch12 | part-4-platform/ch12-platform-architecture.md | 推論平台架構：gateway→router→engine 全鏈路、Gateway API Inference Extension、KServe/Ray Serve/llm-d/Dynamo、LoRA 多租戶、cold start |
| ch13 | part-4-platform/ch13-autoscaling-capacity.md | Autoscaling 與容量工程：訊號選擇、KEDA、預測式擴縮、容量規劃數學、硬體選型 |
| ch14 | part-5-operations/ch14-observability-benchmarking.md | 可觀測性與 benchmark：指標分類學、goodput、DCGM、tracing、benchmark 方法論 |
| ch15 | part-5-operations/ch15-reliability.md | 可靠性工程：故障目錄、健康檢查、graceful drain、canary、retry storm、incident |
| ch16 | part-5-operations/ch16-cost-multitenancy.md | 成本工程與多租戶：$/Mtok 經濟學、採購策略、chargeback、公平性與濫用 |
| ch17 | part-6-frontier/ch17-frontier-2026-2028.md | 前沿：agentic 流量、reasoning 經濟學、新架構、硬體路線圖、什麼值得押注 |
| ch18 | part-6-frontier/ch18-career.md | 職涯：作品集對應、系統設計面試完整示範、開源策略、定位 |
| 附錄A | appendix/a-labs-index.md | 全書實驗總表：三條軌道（M1 / 單卡 / 多卡）、成本矩陣 |
| 附錄B | appendix/b-glossary.md | 術語表 EN→繁中 |
| 附錄C | appendix/c-cheatsheets.md | 速查表：公式、vLLM 參數、PromQL、DCGM、K8s YAML |

---

## ch01 — 從後端到 AI Infra：你站在哪、要去哪

**額外輸入**：Read 專案根目錄的 `Chewei_Chen_Resume.md` 與 `plan.md`。

**目標**：讀完後讀者腦中有完整地圖——這個領域的技術棧分層、職位光譜、自己的技能哪些直接遷移、哪些要補、這本書每一章在地圖上的位置。

**必涵蓋**：
- 核心論點開場：大規模 LLM serving 是分散式系統問題，不是模型問題。用一個具體場景（一個 chat 請求從進到出的完整旅程）展開整個 stack。
- 技術棧分層圖（model → kernel → engine 單機 → 多卡 → 叢集 → 平台 → 產品 API），標出每層的代表工具與本書對應章節。
- 職位光譜拆解：Inference Engineer / ML Platform / GPU Infra / MLOps / Performance Engineer 各自做什麼、JD 關鍵字怎麼讀、薪資與稀缺度的結構性原因。
- 技能遷移矩陣：逐項把履歷上的經驗對應到 AI infra 的什麼能力（RDS 優化→GPU profiling 方法論同構；SQS idempotent consumer→K8s controller reconcile；WebSocket fan-out→SSE token streaming；k6→LLM benchmark；FluentBit pipeline→DCGM/engine metrics pipeline）。同樣誠實列出「零遷移、必須從零學」的清單。
- 新物理常數對照表：後端世界 vs GPU 世界（請求耗時 ms→token 級 μs；stateless 容易→KV state 黏重；scale-out 秒級→冷啟動分鐘級；CPU 可超賣→GPU 不可超賣…）。
- 本書閱讀路線：完整路線 vs 求職速通路線 vs 面試前複習路線；與 plan.md 模組的對應表。
- 三條全書主軸的宣告（見本檔開頭）。

**不涵蓋**：任何單一技術的機制細節（全部指向後章）。

**Worked example**：用粗略數字走一遍「為什麼 10K CCU 的遊戲後端用 20 台 c5.xlarge 就扛住，但 10K 並發 chat 使用者需要數十張 H100」——把直覺顛覆量化出來。

**Lab**：[紙上推演] 讀者拿自己履歷做一次技能遷移矩陣；[M1] 跑 Ollama 起一個小模型，用 curl 觀察 SSE streaming 與 TTFT，當作第一次接觸。

---

## ch02 — GPU：一種你沒用過的計算機

**目標**：建立 GPU 的系統工程師心智模型（不是 CUDA 程式設計教學），能讀懂規格表、能做 roofline 推理、能講出資料中心層級的硬體版圖。

**必涵蓋**：
- GPU vs CPU 心智模型：為什麼是 throughput machine；SM、warp、SIMT 用「超大規模 worker pool」類比講清楚。
- 記憶體階層與數字感：register/SMEM/L2/HBM 的容量與頻寬量級；H100/B200 的 HBM 頻寬具體數字（2026-06 查證）。
- Roofline model 與 arithmetic intensity：教會讀者用一條公式判斷 workload 是 compute-bound 還是 memory-bound。這是全書最重要的分析工具之一。
- Tensor cores 與數值格式（FP16/BF16/FP8/FP4）的硬體支援差異（哪一代卡支援什麼）。
- 互連：PCIe gen5、NVLink/NVSwitch（代際頻寬數字）、InfiniBand vs RoCE、NVL72 rack-scale 架構是什麼、為什麼重要。
- 資料中心現實：功耗（700W→1000W+/卡）、散熱（氣冷→液冷）、電力成為 scaling 瓶頸的趨勢。
- 硬體版圖總表（2026-06）：NVIDIA（H100/H200/B200/GB200/GB300）、AMD MI300X/MI355X、TPU、AWS Trainium/Inferentia、推論專用晶片（Groq/Cerebras）一覽，各自定位。
- GPU 故障模式入門：ECC error、Xid、fallen off the bus、thermal throttling、大規模叢集的 MTBF 現實（為 ch15 鋪墊）。

**不涵蓋**：CUDA 程式設計（ch04 概念帶過）、kernel 優化（ch07）、K8s 上的 GPU 管理（ch11）。

**Worked example**：用 roofline 算給讀者看：Llama-70B 在 H100 上 decode 一個 token 需要讀多少 bytes 的權重、HBM 頻寬下的理論 token rate 上限，證明 decode 是 memory-bound。

**Lab**：[紙上推演] 給三張卡的規格表算 roofline 拐點；[M1] 用 Apple Silicon 的統一記憶體當對照組，跑 llama.cpp 觀察 memory bandwidth 對 token rate 的影響。

---

## ch03 — Transformer 推論的物理學

**目標**：不需要會訓練模型，但要能精確說出推論時每一步在算什麼、記憶體怎麼長、瓶頸在哪。這章是全書的理論地基。

**必涵蓋**：
- Tokenization：BPE 概念、token ≠ 字、為什麼計價用 token。
- 推論時的 transformer：embedding → N 層（attention + FFN）→ logits → sampling。每層在做什麼，用工程師語言（矩陣乘法的形狀）講。
- Attention 機制：Q/K/V 是什麼、為什麼需要看所有歷史 token、O(n²) 從哪來。
- KV cache：它在解什麼問題（避免重算）、**KV cache 大小公式**（2 × layers × kv_heads × head_dim × bytes × tokens）、MHA vs GQA vs MQA vs MLA 對 KV 大小的影響。
- Prefill vs decode 兩階段：compute-bound vs memory-bound 的數學證明（arithmetic intensity 接 ch02 roofline）、為什麼這個分野決定了後面所有章節的設計。
- Batch 對 decode 的效果：為什麼 batch 能攤提權重讀取、吞吐與延遲的根本取捨曲線。
- Sampling：temperature/top-p/top-k 一頁帶過（infra 視角：sampling 參數影響可快取性與重現性）。
- MoE 結構：expert、router、active vs total params（用 DeepSeek-V3 等真實模型數字）、MoE 為什麼改變 serving 經濟學（記憶體要裝全部、算力只用一部分）。
- 長上下文的代價：prefill O(n²)、KV 線性成長，數字化展示 128k context 的記憶體帳單。

**不涵蓋**：PagedAttention 等 KV 管理系統（ch05）、continuous batching 細節（ch06）、平行化（ch09）。

**Worked example**：完整算一遍 Llama-3.3-70B（GQA）每 token 的 KV cache bytes → 一條 32k context 對話吃多少 GB → 一張 H100 80GB 扣掉權重後能同時服務幾條對話。這個計算全書會反覆引用。

**Lab**：[M1] 用 llama.cpp 的 verbose 輸出觀察 prefill/decode 的速度差異與 context 長度的影響；[紙上推演] 對三個模型（dense 8B、dense 70B、MoE）算 KV 公式。

---

## ch04 — 語言與工具橋接：Python、PyTorch、Go、CUDA

**目標**：用最短路徑讓 TS 工程師能寫 Python 服務、讀懂 PyTorch 推論碼、讀懂 Go 寫的 K8s controller、看懂 CUDA 生態的名詞。這章是工具章，務實、密度高。

**必涵蓋**：
- Python for TS engineers：對照表教學（npm/pnpm→uv、package.json→pyproject.toml、tsconfig→mypy/pyright、Promise→asyncio、Express/NestJS→FastAPI、class-validator→pydantic）。重點講坑：GIL 與 free-threading 現況（2026-06 查證 Python 3.13/3.14 狀態）、async 生態的分裂、型別只是註記不是執行期保證。
- 一個完整範例：用 FastAPI + pydantic + httpx 寫一個 OpenAI-compatible 的 proxy 服務（streaming SSE），這是 AI infra 最常寫的 glue code 形態。
- PyTorch 讀碼能力：tensor、shape、dtype、device、`torch.no_grad()`、把 ch03 的 attention 用 30 行 PyTorch 對照展示。目標是「能讀懂 vLLM 原始碼在寫什麼」而非會訓練。
- Profiling Python：py-spy、cProfile，對應讀者的 Clinic.js 經驗。
- Go for K8s：為什麼 infra 層是 Go 的天下；goroutine/channel vs Node event loop；讀懂一個最小 controller 的 reconcile loop（橋接：reconcile ≈ 讀者寫過的 idempotent consumer——desired state vs actual state）。不教完整 Go，教「讀懂與小改」。
- CUDA 生態名詞表：CUDA/cuDNN/cuBLAS/NCCL/CUTLASS/Triton（語言）各是什麼層級、AI infra 工程師什麼時候會碰到哪個（答案：多半在讀 stack trace 與版本相容矩陣時）。注意消歧義：Triton 語言 vs NVIDIA Triton Inference Server。

**不涵蓋**：NCCL 集合通訊機制（ch09）、K8s GPU 排程（ch11）。

**Worked example**：把同一個「帶重試與逾時的併發 HTTP 呼叫」用 TS 和 Python asyncio 各寫一遍，逐行對照差異與坑。

**Lab**：[M1] 完成那個 FastAPI streaming proxy 並接上 Ollama，用 k6 打它；[M1] 用 py-spy 找出故意埋的效能 bug。

---

## ch05 — KV Cache 管理：推論引擎的記憶體子系統

**目標**：深入 KV cache 的系統設計——這是現代推論引擎最核心的工程創新所在，也是 2026 年產業競爭的焦點之一。

**必涵蓋**：
- 問題定義：naive 連續配置的浪費（內部碎片、預留浪費），引用 vLLM 論文的數字。
- PagedAttention：block table、虛擬→實體 block 映射，全程用 OS virtual memory paging 類比（讀者熟）。copy-on-write 與 fork（beam search/平行取樣）。
- vLLM V1 的 KV cache manager 現況（2026-06 查證）。
- Prefix caching：hash-based block 重用（vLLM）vs RadixAttention/radix tree（SGLang）；什麼 workload 受益（system prompt、多輪對話、agentic 迴圈）；cache hit 的經濟價值（各家 API 的 cached input 折扣當證據）。
- KV cache 量化（FP8 KV）：省一半記憶體的代價與品質風險。
- 分層 offloading：GPU HBM → CPU RAM → NVMe/遠端儲存的階層；LMCache、Mooncake（KVCache-centric 設計、Kimi 的生產數據）；NIXL 等傳輸層一句話帶過（細節見 ch10）。
- KV cache 的失效與一致性：模型版本更新時 cache 全失效、sampling 參數與 cache 的關係、多副本間 cache 不共享的路由含意（指向 ch10）。
- 容量視角：KV cache 利用率作為系統最重要的健康指標之一（為 ch13 autoscaling 訊號鋪墊）。

**不涵蓋**：KV-aware routing 與跨節點傳輸細節（ch10）、batching 排程（ch06）。

**Worked example**：對一個 agentic workload（system prompt 2k + 工具描述 3k + 10 輪對話）算 prefix cache 命中下的 prefill 成本 vs 未命中，換算成 TTFT 與 $ 差異。

**Lab**：[M1] 用 llm-d-inference-sim 或 vLLM CPU mode 觀察 prefix caching 指標；[租 GPU] 在 vLLM 開關 `--enable-prefix-caching` 對同一 workload 的 TTFT 對比（估 $3-5）。

---

## ch06 — Batching 與單機排程：吞吐的來源

**目標**：完整理解 continuous batching 與引擎內排程器——這是「推論引擎為什麼快」的核心答案，也是讀者排程直覺最能發揮的地方。

**必涵蓋**：
- 歷史脈絡：static batching → dynamic batching → continuous batching（Orca 論文的 iteration-level scheduling），每一步解了什麼問題。
- Continuous batching 機制：每個 decode step 重組 batch、新請求隨時加入、完成的隨時離開；與 KV cache 配置的互動。
- Chunked prefill：prefill 與 decode 互相干擾的問題（長 prompt 卡住所有人的 decode → ITL spike）、把 prefill 切塊混進 decode batch 的解法、token budget 概念。
- Preemption：KV 不夠時誰被踢、recompute vs swap 的取捨、preemption 對尾延遲的影響。
- 排程策略：FCFS、priority、SLO-aware；公平性問題（長短請求混跑的 head-of-line blocking，類比讀者熟的 queue 理論）；starvation。
- 關鍵參數的系統意義：`max-num-seqs`、`max-num-batched-tokens`、`gpu-memory-utilization` 怎麼共同決定延遲/吞吐曲線。
- Goodput 概念引入：滿足 SLO 的吞吐才是有效吞吐（細節量測見 ch14）。

**不涵蓋**：跨節點排程（ch10/ch11）、autoscaling（ch13）、vLLM 完整參數表（ch08）。

**Worked example**：給定 H100 + 8B 模型 + 固定流量分布，手算（或用簡化模型）batch size 從 1→8→32→128 時吞吐與 ITL 的變化曲線，標出甜蜜點與 KV 容量撞牆點。

**Lab**：[M1] 用 llm-d-inference-sim 設不同 batch 與延遲參數，用 k6 觀察吞吐/延遲曲線；[租 GPU] vLLM 上調 `max-num-seqs` 三檔對比 throughput/ITL（估 $3-5）。

---

## ch07 — 模型壓縮與加速：quantization、speculative decoding、kernels

**目標**：掌握「同一張卡榨出更多」的三大武器的原理、收益、代價與適用判斷。

**必涵蓋**：
- Quantization 原理：精度 vs 動態範圍、outlier 問題、calibration；weight-only（GPTQ/AWQ INT4）vs weight+activation（FP8 W8A8）；硬體支援對照（FP8 需 Hopper+、FP4/NVFP4 需 Blackwell）（2026-06 查證格式現況）。GGUF 與 llama.cpp 生態的量化是另一條線。
- 品質評估：perplexity 不夠，要用任務型 eval；「免費午餐」的邊界在哪（哪些任務先壞：數學、長推理、低資源語言）。
- 量化的決策框架：吞吐提升 × 品質風險 × 工程成本的取捨表。
- Speculative decoding：draft-verify 機制、acceptance rate 數學、n-gram/draft model/EAGLE-3/MTP（DeepSeek 的 multi-token prediction）等方案光譜（2026-06 查證）；**反直覺重點**：高 batch 時收益遞減甚至為負（驗證吃掉的算力），什麼流量形態才划算。
- Kernels：FlashAttention（IO-aware 的意義，用「減少 HBM 往返」講）、FlashInfer；kernel fusion 的概念。
- CUDA Graphs：decode 每步 launch overhead 的問題與 graph capture 的解法；torch.compile 在推論的角色。
- 全章收尾：優化疊加順序建議（先量測、再 quantization、再 spec decode，每步驗證品質與速度）。

**不涵蓋**：KV cache 量化細節（ch05）、引擎參數操作（ch08）。

**Worked example**：70B 模型 FP16 vs FP8 vs INT4：權重記憶體、需要的卡數、理論 decode 上限（接 ch02 roofline）、品質風險等級，一張完整對照表。

**Lab**：[M1] llama.cpp 跑同模型 Q4/Q8 對比速度與輸出品質；[租 GPU] vLLM 上 FP8 vs FP16 同 workload benchmark（估 $5-8）。

---

## ch08 — 推論引擎實戰：vLLM、SGLang、TensorRT-LLM 與選型

**目標**：把 ch05-07 的機制落到真實引擎上：懂 vLLM 架構、會調參數、能做引擎選型、能獨立完成單卡部署與 benchmark。本章是 Part II 的實戰總結。

**必涵蓋**：
- vLLM 架構解剖（2026-06 的 V1 架構）：AsyncLLM / EngineCore / scheduler / KV cache manager / model runner 的分工，process 模型，請求的一生（從 HTTP 進到 token 出）。
- 關鍵參數完整表：每個參數解什麼問題、調錯的症狀（`--max-model-len`、`--gpu-memory-utilization`、`--max-num-seqs`、`--max-num-batched-tokens`、`--enable-prefix-caching`、`--tensor-parallel-size`、quantization、speculative config…）。
- OpenAI-compatible API、/metrics endpoint 重點指標預覽（細節 ch14）。
- SGLang：RadixAttention、結構化輸出強項、與 vLLM 的真實差異（2026-06 的版本狀態與社群動態）。
- TensorRT-LLM：compile 式引擎的取捨（峰值效能 vs 彈性）、什麼場景值得。
- 本地/邊緣線：llama.cpp、Ollama、MLX 的定位。
- 選型決策樹：模型、硬體、流量形態、團隊能力 → 引擎choice；「預設選 vLLM，除非…」的務實建議與例外清單。
- 完整部署 walkthrough：租一張卡（RunPod/Lambda）→ 起 vLLM → 跑 benchmark → 讀指標，含成本控制紀律（用完即關、設預算警報）。

**不涵蓋**：多節點（ch09/ch10）、平台層部署（ch12）、benchmark 方法論深度（ch14）。

**Worked example**：同一張 L4 上 8B 模型，三組參數配置（保守/平衡/激進）的實測對比表，解釋每個差異的機制成因。

**Lab**：[租 GPU] 本章核心：完整走一遍部署＋benchmark＋調參閉環（估 $5-10）。這直接對應 plan.md 的旗艦專案③。

---

## ch09 — 平行化策略：當一張卡裝不下

**目標**：掌握 TP/PP/DP/EP/SP 的機制、通訊代價、適用場景，能對給定模型＋硬體做平行策略決策。

**必涵蓋**：
- 為什麼要切：記憶體裝不下 vs 延遲要求 vs 吞吐要求，三種動機切法不同。
- Tensor parallelism：attention heads 與 FFN 怎麼切、每層兩次 all-reduce 的通訊量、為什麼 TP 通常不出節點（NVLink vs 跨節點頻寬的數量級差）。
- Pipeline parallelism：stage 切分、bubble 問題、micro-batching；推論時 PP 的角色（吞吐型、跨節點友善）。
- Data parallelism：最樸素也最常用的 scale-out；DP attention + EP MoE 的組合。
- Expert parallelism：MoE 專屬、all-to-all 通訊、wide-EP（DeepSeek 式大規模部署：prefill 群與 decode 群不同 EP 度）（2026-06 查證 vLLM/SGLang 的 wide-EP 支援現況）。
- Sequence/context parallelism：超長上下文的 prefill 切法，一節帶過。
- NCCL 與集合通訊：all-reduce/all-gather/all-to-all 各自的通訊量公式與直覺；拓撲感知（NVLink domain 內 vs InfiniBand 跨節點）；為什麼 NCCL hang 是多卡世界最痛的故障（細節 ch15）。
- 決策框架：模型大小 × 卡型 × SLO → 推薦策略表（8B/70B/405B dense、大 MoE 各一行）。

**不涵蓋**：P/D 分離（ch10）、訓練的平行化（本書不管訓練）。

**Worked example**：70B FP8 在 2×H100 TP2 vs 4×L40S TP4 的記憶體帳、通訊量帳、預估 token rate 與成本對比。

**Lab**：[紙上推演] 對 405B 與 DeepSeek-V3 級 MoE 各設計一套平行配置並算記憶體；[租 GPU] 2 卡 TP2 起 vLLM，對比單卡（估 $8-15）。

---

## ch10 — 解構推論服務：P/D 分離與 KV 路由

**目標**：理解 2025-2026 大規模推論架構的主旋律——prefill/decode 分離與 KV-aware routing，能判斷什麼規模才值得上這套複雜度。

**必涵蓋**：
- 動機：prefill 與 decode 的資源畫像衝突（接 ch03/ch06），chunked prefill 只是緩解不是根治；干擾的量化證據。
- 學術源頭一段帶過（DistServe/Splitwise），重點放生產系統：Mooncake（Kimi，KVCache-centric，公開的生產數據）、NVIDIA Dynamo（架構與 planner）、llm-d（well-lit paths）、vLLM 的 KV connector 生態（2026-06 查證各專案狀態）。
- KV 傳輸工程：NIXL、RDMA/InfiniBand、NVLink、傳輸延遲的數學——什麼時候「傳 KV」比「重算 prefill」划算（給公式與數字）。
- xPyD 配比問題：prefill 池與 decode 池的容量比怎麼定、流量形態怎麼影響配比、動態調整。
- KV-aware / prefix-aware routing：問題本質是「有狀態的負載均衡」（橋接：session affinity、consistent hashing，但 cache 命中價值遠高於一般 session）；llm-d inference scheduler、SGLang router、Dynamo KV router 的做法比較；scoring 函數設計（cache 命中 vs 負載均衡的拉扯）。
- 異質硬體部署：prefill 用算力強的卡、decode 用頻寬大的卡的思路。
- 誠實的反面：什麼規模以下不要碰 P/D 分離（複雜度稅、傳輸開銷、運維面積），給判斷準則。

**不涵蓋**：K8s 排程機制（ch11）、平台產品比較的完整版（ch12）。

**Worked example**：算一遍 KV 傳輸帳：32k context 的 KV（用 ch03 公式）走 NVLink / IB / 100GbE 各要幾 ms，對比重算 prefill 的時間，找出 crossover point。

**Lab**：[M1] 用 llm-d-inference-sim 模擬 P/D 分離的 TTFT/ITL 特性；[紙上推演] 給三種流量形態（短問答/長文件 RAG/agentic）設計 xPyD 配比並辯護。

---

## ch11 — Kubernetes 上的 GPU：排程、共享與節點生命週期

**目標**：這是讀者既有 K8s 功力的主場延伸：完整掌握 GPU 在 K8s 上的資源模型、共享技術、排程器生態與節點維運。

**必涵蓋**：
- GPU 資源模型的根本限制：extended resources 是整數、不可超賣、不可分割——為什麼（device plugin 機制決定的），這與 CPU/memory 的 requests/limits 哲學差在哪。
- NVIDIA GPU Operator 全家桶解剖：driver、container toolkit、device plugin、DCGM exporter、MIG manager、Node Feature Discovery 各自做什麼、壞了各是什麼症狀。
- 共享技術三件套對照表：time-slicing（無隔離、適合 dev）、MPS（部分隔離）、MIG（硬體分割、profile 表、適合多租戶小模型）——隔離性/粒度/開銷/適用場景。
- **DRA（Dynamic Resource Allocation）**：ResourceClaim/DeviceClass/structured parameters 的模型、它解了 device plugin 的什麼痛（2026-06 查證 GA 狀態與生態採用度）、未來幾年的排程資源模型會長怎樣。
- 排程器生態：default scheduler 的不足、Kueue（quota、borrowing、gang）、Volcano、拓撲感知排程（NVLink/IB locality 為什麼影響效能，接 ch09）。
- Bin-packing vs spread：GPU 碎片化問題（叢集有卡但湊不出一台 8 卡機）、這直接是錢（接 ch16）。
- 多節點推論的部署原語：LeaderWorkerSet（LWS）是什麼、為什麼 StatefulSet 不夠、gang scheduling 需求。
- 節點生命週期：GPU 健康檢測（DCGM → 自動 cordon/drain）、driver/CUDA 版本相容矩陣的維運地獄、node pool 升級策略。
- 多租戶基礎：namespace + ResourceQuota、priority class 與 preemption 的 GPU 特殊性。

**不涵蓋**：推論平台軟體（ch12）、autoscaling（ch13）、成本（ch16）。

**Worked example**：設計一個 64 卡叢集的 namespace/quota/priority 方案：兩個產品團隊＋一個研究團隊，含借用規則與搶占順序，YAML 骨架。

**Lab**：[M1] 本章是模擬主場：kind + KWOK + fake-gpu-operator 建假 GPU 叢集，部署假工作負載，觀察排程行為（對應 plan.md 旗艦專案①）；實驗 MIG label 與 bin-packing 策略。

---

## ch12 — 推論平台架構：從 gateway 到引擎的全鏈路

**目標**：能畫出並辯護一個生產級推論平台的完整架構——這是系統設計面試的核心題，也是讀者架構能力的展示舞台。

**必涵蓋**：
- 參考架構全圖：client → API gateway（認證/計量/限流）→ inference gateway/router（模型路由、KV-aware）→ engine fleet（vLLM pods）→ 權重儲存/快取層，每個箭頭標協定與失敗模式。
- **Gateway API Inference Extension**：InferencePool、endpoint picker（EPP）的機制、為什麼 L7 LB 對 LLM 流量不夠（請求成本變異數百倍、需要 body-based 與 state-aware 路由）（2026-06 查證狀態）。
- 平台選項深度比較：llm-d（K8s 原生、well-lit paths）、NVIDIA Dynamo、KServe（LLMInferenceService 的演進）、Ray Serve（Python 組合彈性）；各自的甜蜜點、誰在生產用（2026-06 查證）；自組 vs 採用的判斷。
- 多模型服務：模型生命週期（registry → 部署 → 版本 → 下線）、權重分發工程（HF Hub 直拉的風險、S3/OCI artifact、P2P/streaming 載入）、**cold start 解剖**（image pull → 權重載入 → engine 初始化 → CUDA graph capture → warmup，每段的時間量級與優化手段）。
- LoRA 多租戶：multi-LoRA serving 機制（一個 base 模型掛 N 個 adapter）、per-tenant fine-tune 的經濟學、vLLM 的 LoRA 支援現況。
- Scale-to-zero 的真實代價：冷啟動分鐘級 vs 流量秒級，什麼服務等級才能用。
- API 層設計:OpenAI-compatible 作為 de facto 標準的含意、SSE streaming 的工程細節（讀者的 WebSocket 經驗對照）、錯誤語意（429/503、retry-after）、admission control 與佇列（橋接讀者的 backpressure 經驗）。

**不涵蓋**：autoscaling 訊號與容量（ch13）、可靠性細節（ch15）、計費（ch16）。

**Worked example**：cold start 帳單：70B FP8 模型從 pod 排程到首 token 的每階段耗時估算（image 15GB、權重 70GB 從 S3 / 從本地 NVMe cache / 從 P2P），給三種優化方案的對比。

**Lab**：[M1] 在模擬叢集上裝 llm-d 或 KServe + llm-d-inference-sim，體驗 InferencePool 路由；[紙上推演] 為「內部 AI 平台、5 個團隊、20 個模型」畫完整架構圖並寫設計文件。

---

## ch13 — Autoscaling 與容量工程

**目標**：能為 LLM 服務設計正確的 autoscaling，能做 SLO 驅動的容量規劃與硬體選型——把讀者「為高併發做容量」的經驗翻譯過來。

**必涵蓋**：
- 為什麼 CPU/RPS 訊號全錯：請求成本變異（10 token vs 100k token）、GPU util 指標的誤導性（SM 占用 ≠ 有效工作）、佇列先於資源指標惡化（讀者在遊戲後端見過這個模式）。
- 正確的訊號階層：佇列深度、KV cache 利用率、batch slot 占用、TTFT/SLO burn rate；vLLM 暴露哪些（接 ch14）。
- 執行機制：HPA + custom/external metrics、KEDA（scaledobject 範例）、Knative KPA 與 scale-to-zero（接 ch12 的冷啟動代價）。
- **Scale-up 延遲是根本約束**：冷啟動分鐘級 vs 流量尖峰秒級 → headroom 數學（要留多少 buffer）、warm pool、預測式擴縮（diurnal pattern、活動預告——橋接讀者的遊戲活動經驗）。
- 縮容的優雅性：drain 中的長 streaming 請求怎麼辦（指向 ch15 細節）。
- 多維 scaling 決策：加 replica vs 改 TP 度 vs 換 MIG profile vs 換卡型，各維度的調整成本與時間尺度。
- **容量規劃完整方法論**：benchmark 出單卡在 SLO 內的 sustainable token rate（goodput）→ 流量模型（並發、token 分布、尖峰係數）→ 卡數公式 → 留 headroom → 验证。模擬工具（Vidur 等）的角色。
- 死亡螺旋防禦：KV 壓力 → preemption → recompute → 更高負載的正回饋迴圈，circuit breaker 與 load shedding 的位置（admission control 在 gateway，接 ch12）。

**不涵蓋**：指標實作（ch14）、故障處理（ch15）、$ 細節（ch16）。

**Worked example**：完整容量規劃題：「chat 產品，尖峰 5,000 並發對話、輸入輸出 token 分布給定、TTFT p95 < 1.5s、ITL p95 < 60ms」→ 從 benchmark 數據推出需要幾張 H100、怎麼配 headroom、月成本估算。全書最重要的 worked example 之一。

**Lab**：[M1] 模擬叢集 + KEDA + llm-d-inference-sim：用佇列深度驅動 autoscaling，k6 打流量觀察行為（對應 plan.md 旗艦專案①的進階）；[紙上推演] 用 Vidur 跑一次配置搜索。

---

## ch14 — 可觀測性與 Benchmark：你不能優化你量不到的東西

**目標**：建立 LLM 服務的完整指標體系與誠實的 benchmark 方法論——讀者的可觀測性與負載測試經驗在此直接複用。

**必涵蓋**：
- 指標分類學（分層）：產品層（availability、goodput）；請求層（TTFT、TPOT/ITL、E2E、排隊時間，各取 p50/p95/p99）；引擎層（batch size、KV utilization、preemption 次數、prefix cache hit rate、排程延遲）；GPU 層（DCGM：SM activity vs utilization 的差異與誤導、memory bandwidth util、功耗、溫度）；叢集層（pending pods、佇列深度）。每個指標：定義、怎麼採、什麼值算健康、什麼形態算異常。
- 為什麼平均值說謊：token 級延遲要看分布；TTFT 與 ITL 的 histogram 設計。
- 實作棧：vLLM /metrics 重點清單、DCGM-exporter、Prometheus 抓取設定、Grafana dashboard 設計原則（一面板回答一個運維問題）；告警設計：page vs ticket 的分界。
- Tracing：OTel 跨 gateway→router→engine 的 span 設計、token 計數進 span attributes、長 streaming 的 trace 怎麼處理。
- 日誌的隱私現實：prompt 是 PII，sampling 與 redaction 策略。
- **Benchmark 方法論**（本章後半核心）：workload 真實性（token 分布、prefix 結構、到達過程——Poisson vs burst）；open-loop vs closed-loop 與 coordinated omission（讀者用 k6 會秒懂）；warmup 與穩態；latency-throughput frontier 曲線怎麼跑怎麼讀；goodput@SLO 作為單一比較數字。
- 工具實測：vLLM bench、genai-perf、inference-perf（2026-06 查證各工具狀態）、用 k6 自寫 SSE-aware 腳本（給骨架碼，讀者的主場）。
- 效能迴歸防禦：benchmark 進 CI、與 baseline 比對的統計紀律。

**不涵蓋**：故障告警的 runbook（ch15）、成本指標（ch16）。

**Worked example**：把一次「看起來吞吐很高」的 benchmark 拆穿：closed-loop、無 warmup、忽略 p99 的測試 vs 修正後的結果對比，數字示範方法論差異有多大。

**Lab**：[M1] 為 llm-d-inference-sim 建全套 Prometheus + Grafana dashboard（對應 plan.md 模組二的監控）；[M1] 寫 k6 SSE benchmark 腳本；[租 GPU] 對真 vLLM 跑一條 latency-throughput frontier（估 $5-8）。

---

## ch15 — 可靠性工程：當 GPU 叢集開始壞

**目標**：生產級 LLM 服務的故障目錄與防禦工事。這章是全書 Murphy 濃度最高的一章，也是資深 SRE 視角的展示。

**必涵蓋**：
- **故障目錄**（表格：症狀/根因/偵測訊號/緩解）：CUDA OOM（碎片化、KV 超配、洩漏）；Xid 錯誤家族（ECC double-bit、fallen off the bus、NVLink error）；NCCL hang/timeout（多卡最痛：一卡掛全組僵住，偵測為什麼難）；driver/firmware 問題；thermal/power throttling；host 層（NVMe 被權重快取塞爆）；引擎層（scheduler 卡死、sequence 洩漏、記憶體緩慢洩漏）；隱性退化（prefix hit rate 慢慢掉、某 replica 變慢拖累全池）。
- 健康檢查設計：liveness vs readiness vs startup probe 對長載入引擎的特殊處理；「深健康」探針（真的生成幾個 token 才算活著）的取捨；DCGM 驅動的節點級健康與自動 cordon。
- **Graceful drain 的數學**：streaming 請求可長達分鐘級 → drain timeout 要照 p99.9 請求時長設計；preStop hook + 停收新請求 + 等 in-flight 的完整模式（橋接讀者做過的 graceful shutdown，但時間尺度 ×100）。
- 發布工程：canary 的對象不只程式碼——模型權重、引擎版本、config 都要 canary；**品質迴歸在 5xx 看不到**（模型變笨不報錯）→ eval-based gate 與 shadow traffic 的必要性。
- 流量災難：retry storm 的 LLM 加強版（重試的是分鐘級昂貴請求；流式中斷重試 = 重算全部）——retry budget、冪等性、斷流續傳的設計；priority shedding（先丟低優先級）；brownout 模式（降 max context、關 spec decode 換容量）。
- 容量事故：佇列崩潰的動力學、admission control 為什麼必須在最前面。
- 多區域：權重預熱、KV cache 不可遷移的含意、failover 的 RTO 現實。
- Incident response：兩個 runbook 範例（「TTFT p99 突然 ×3」、「某 node NCCL timeout」）的判斷樹。
- 混沌工程：對 GPU 服務做 chaos 的具體實驗清單。

**不涵蓋**：監控指標定義（ch14）、autoscaling（ch13）。

**Worked example**：drain timeout 計算：給定請求時長分布，算「不掉任何 in-flight 請求的 drain 預算」與 rollout 一輪要多久，展示為什麼 LLM 服務的 deploy 以小時計。

**Lab**：[M1] 在模擬叢集上演練：kill pod 觀察 in-flight 處理、設計 preStop；故意製造 retry storm 觀察佇列；[紙上推演] 為「凌晨三點 TTFT 告警」寫完整判斷樹。

---

## ch16 — 成本工程與多租戶：把 GPU 變成一門生意

**目標**：建立 $/M token 的成本模型、GPU 採購與利用率策略、內部多租戶的公平與計費——staff 級工程師的視角。

**必涵蓋**：
- **單位經濟學**：$/M token 推導公式（GPU $/hr ÷ 有效 token rate）；什麼最動成本（排序：利用率 > 快取命中 > batch/量化 > 硬體代際），各給量級。
- GPU 取得光譜（2026-06 價格快照）：hyperscaler on-demand / 承諾折扣、neocloud（CoreWeave/Lambda/RunPod/Vast 等級距）、reserved vs spot 的推論適用性（spot 配 batch 工作負載）。
- Serverless inference / API 託管 vs 自建的 crossover 分析：什麼條件自建才划算（量、延遲、隱私、客製模型），給公式與 break-even 計算。
- Batch tier 的存在理由：離線工作負載吃 off-peak 容量、各家 50% 折扣的結構性原因。
- 快取經濟學：prefix cache 命中的成本結構（各家 API cached input 定價當證據）、agentic 流量讓快取變成本中心的核心。
- 利用率會計：MFU/MBU vs goodput、「忙碌但無效」的 GPU、叢集層級的碎片浪費（接 ch11 bin-packing）、dev 卡閒置的治理。
- 內部多租戶:chargeback/showback 設計（per-token 歸因，類比雲端 FinOps）、token-denominated rate limiting（token bucket 演算法在這裡是字面意義）、priority class 與租戶間 preemption、noisy neighbor（一個 200k-context 租戶吃光 KV）的隔離手段、濫用防禦。
- TCO 全貌：GPU 之外的網路（IB 不便宜）、儲存、電力、人力。

**不涵蓋**：技術性優化手段本身（ch05-07）、容量數學（ch13）。

**Worked example**：完整 build vs buy 決算：某產品月吞吐 50B tokens，比較（a）API 託管（b）neocloud 租 H100 自建（c）保留容量自建的三案月成本，含人力與 headroom，標出 crossover 點。

**Lab**：[紙上推演] 為你目前公司的某個假想 AI 功能做一次 build vs buy 分析；[M1] 在模擬叢集實作 token-based rate limiter（讀者寫過 rate limiter，這次計量單位換成 token）。

---

## ch17 — 前沿（2026–2028）：流量在變、模型在變、硬體在變

**目標**：分析未來 2-3 年業界會把資源砸向哪裡，給讀者「押注什麼能力」的判斷框架。本章觀點性最強，必須大量引用 2026-06 查證的證據。

**必涵蓋**：
- **流量形態革命（本章核心論點）**：agentic workload 正在取代 chat 成為主流負載——多輪工具呼叫、超高 prefix 重複、長 session、平行分支探索、機器發起的請求洪峰；MCP 等協定標準化的影響；這對 ch05/ch10/ch13 的每個設計意味著什麼（KV cache 從優化變成產品核心、session 黏性、快取分層儲存）。
- Reasoning / test-time compute 經濟學：思考 token 的成本結構、$/任務取代 $/token 的計價演化、thinking budget 控制、對容量規劃的衝擊（輸出 token 爆炸）。
- KV cache 成為儲存層級：Mooncake store、LMCache、各家 API 的 context caching 商品化——「KV 是新的 Redis」這個論點的證據與反證。
- 模型架構的移動目標：sparse attention（DeepSeek 的路線）、linear/hybrid attention（Mamba 混合架構的代表模型）、對「KV cache 數學」的顛覆程度評估（如果 KV 不再線性成長，ch03 的公式怎麼變）；多模態推論的工程差異（encoder pipeline、image/video token）。
- 硬體路線圖（2026-06 視角）：NVIDIA Rubin 世代、AMD MI400/Helios、custom silicon（TPU、Trainium）、推論專用架構（Groq/Cerebras 的 SRAM 路線）；HBM 供應與功耗牆；rack-scale（NVL72 之後）成為設計單位。
- 電力成為一級約束：GW 級資料中心、power-aware scheduling 可能成為 infra 工程師的新工作面。
- 標準化與市場結構：OpenAI API 相容作為 de facto、Gateway API Inference Extension、推論市場（OpenRouter 類聚合層）、neocloud 整併趨勢。
- **能力耐久性矩陣**（收尾）：哪些知識會過期（具體工具參數）、哪些十年不變（roofline、排程理論、可觀測性、容量數學）——呼應全書主軸與讀者的轉職策略。

**不涵蓋**：已在前章深講的機制（引用即可）。

**Worked example**：用公開數據估算一個 agentic coding assistant 的流量畫像（每 session 的 tool call 數、prefix 重複率、token 比例），對比 chat 流量,推導對 KV 容量與路由設計的需求差異。

**Lab**：[紙上推演] 挑一個 2026 的熱門辯論（如「P/D 分離會不會被硬體進步淘汰」），正反兩面各寫 200 字論證。

---

## ch18 — 把能力變成職涯：作品集、面試、開源

**額外輸入**：Read 專案根目錄的 `Chewei_Chen_Resume.md` 與 `plan.md`。

**目標**：把全書知識轉成可展示、可面試、可被錄取的形態。直接服務讀者的轉職目標。

**必涵蓋**：
- 本書 ↔ plan.md 對應表：四個旗艦專案各自用到哪些章、每個專案的「深度升級建議」（怎麼把專案做到面試官眼睛一亮）。
- 作品敘事模板：把「降 RDS CPU 40%」的敘事結構套到 GPU 專案上的具體示範（量測→診斷→優化→數據,換上 TTFT/goodput/$ 的數字）。
- **系統設計面試完整示範**（本章核心）：「設計一個多租戶 LLM 推論平台，5k 並發、TTFT p95<1.5s」的 45 分鐘完整作答——需求澄清→SLO 與容量數學（ch13）→架構圖（ch12）→深掘兩處（KV 管理 ch05、autoscaling ch13）→故障與運維（ch15）→成本（ch16）。逐段標註「面試官在這裡想聽什麼」。
- 面試題庫：把各章「自我檢核」的精華 30 題彙整,按面試輪次分類（screening/深度/系統設計/行為）。
- 開源策略：vLLM/llm-d/KServe/SGLang 各自的貢獻面積與門檻評估（2026-06 查證 good-first-issue 文化）、從文件與測試切入的路徑、一個 PR 的完整生命週期預期。
- 履歷改寫方向：後端經驗 → AI infra 語言的逐條翻譯示範（拿讀者履歷的真實條目示範 2-3 條）。
- JD 解碼器：同名職缺的不同實質（inference engineer 在 model lab vs 在產品公司 vs 在 neocloud 的差異）、紅旗與綠旗、該問面試官的問題清單。
- 持續更新系統：該追的源頭清單（vLLM blog/SIG、llm-d、主要會議）、每週 30 分鐘的維護迴圈設計。

**不涵蓋**：技術機制（全部引用前章）。

**Worked example**：那場 45 分鐘系統設計面試的完整逐字稿級示範。

**Lab**：[紙上推演] 用本章模板改寫自己履歷的三條 bullet；錄音自講一次系統設計題並對照檢核表。

---

## 附錄A — 動手實驗總表（appendix/a-labs-index.md）

把全書各章的「動手做」彙整成三條漸進軌道，每個實驗一列：章節、目標、硬體、估計成本、估計時間、成功標準。
- Track 1【M1 免費】：模擬叢集系列（kind/KWOK/fake-gpu-operator/llm-d-inference-sim/Prometheus/KEDA）＋本地模型系列（Ollama/llama.cpp/MLX）— 對應 plan.md 模組一、二。
- Track 2【單卡租用，總預算 $30-50】：vLLM 部署、調參、benchmark、量化對比 — 對應 plan.md 模組三、四。
- Track 3【多卡/進階，總預算 $30-60】：TP、P/D 模擬、平台組裝 — 對應 plan.md 模組五。
寫法：先 Grep 各章的 `## 動手做` 段落彙整，確保與章內一致；篇幅 2000-3000 字。

## 附錄B — 術語表（appendix/b-glossary.md）

全書出現的術語 EN→繁中對照＋一行定義＋主要出現章節。至少 120 條，按字母排序。聚焦 LLM serving 領域（不收一般後端詞彙）。

## 附錄C — 速查表（appendix/c-cheatsheets.md）

工程速查，全部可直接抄用：
- 公式卡：KV cache 大小、模型權重記憶體、roofline 拐點、decode 理論上限、$/Mtok、容量規劃、drain timeout。
- vLLM 關鍵參數表（參數/預設/解什麼/調錯症狀）（2026-06）。
- PromQL 片段：TTFT/ITL 分位數、KV 利用率、goodput、SLO burn rate。
- DCGM 重點欄位與 nvidia-smi 讀法。
- K8s YAML 骨架：GPU resource、MIG、time-slicing config、DRA ResourceClaim、LWS、KEDA ScaledObject。
- Benchmark 檢查清單（發表數字前的 12 個自問）。
