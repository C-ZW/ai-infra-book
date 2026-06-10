# 事實基準快照：2026-06-10

> 本文件為 AI Infrastructure 技術書全體章節作者的「業界現況事實基準」。所有事實均於 2026-06-10 以網路查證編寫，每條附來源 URL。
> 標註 ⚠️ 的條目表示來源不足、來源間互相矛盾、或僅有二手來源，引用前請再次查證。
> 凡寫「最新版本」者，皆指 2026-06-10 時點；正文寫作時建議寫成「本書寫作時（2026 年年中）」並避免把版本號寫死在不必要的地方。

---

## 1. vLLM

- **最新版本 v0.22.1（2026-06-05）**；v0.22.0（2026-05-29，459 commits / 230 貢獻者）、v0.21.0（2026-05-15）。尚未推出 1.0。 — https://pypi.org/project/vllm/ 、https://github.com/vllm-project/vllm/releases
- **V1 引擎已是唯一引擎**：v0.11.0 完成 V0 程式碼全面移除（`AsyncLLMEngine`、`MQLLMEngine`、舊 attention backends 等全部刪除），V1 是 codebase 中唯一引擎。 — https://github.com/vllm-project/vllm/releases/tag/v0.11.0 、https://docs.vllm.ai/en/stable/usage/v1_guide/
- **Priority scheduling**：V1 scheduler 支援 FCFS 與 priority-based 兩種策略（priority 以 FCFS 為 tie-breaker），由 `--scheduling-policy` 設定。 — https://docs.vllm.ai/en/stable/usage/v1_guide/
- **Wide-EP / DP attention**：官方 blog（2025-12-17）展示 DeepSeek 以 wide expert parallelism 達 2.2k tok/s/H200；DP attention 可與 TP attention 組合（每個 DP engine 擁有 TP-size 個 worker）。 — https://vllm.ai/blog/2025-12-17-large-scale-serving 、https://docs.vllm.ai/en/latest/serving/data_parallel_deployment/ 、https://docs.vllm.ai/en/latest/serving/expert_parallel_deployment/
- **P/D 分離與 KV connector**：以 KV connector 抽象支援 prefill/decode 分離（NixlConnector 等）；v0.21 整合 KV offloading 與 hybrid memory allocator，v0.22 加入 multi-tier KV cache offloading framework（含 filesystem tier）。 — https://github.com/vllm-project/vllm/releases
- **Speculative decoding**：支援 EAGLE / EAGLE-3 與 MTP（v0.11 release notes 包含 GPT-OSS、MiniCPM3 的 EAGLE-3 支援）。 — https://github.com/vllm-project/vllm/releases/tag/v0.11.0
- ⚠️ v0.22 其他亮點（DeepSeek V4 支援強化、Model Runner V2 成為 Qwen3 dense 預設、實驗性 Rust frontend、batch-invariant inference + Cutlass FP8）取自 release notes 摘要，細節寫作前請對照原始 release page。 — https://github.com/vllm-project/vllm/releases

## 2. SGLang

- **最新版本 v0.5.12.post1（2026-05-26）**；v0.5.12（2026-05-16，DeepSeek-V4 完整推論路徑，支援 B300/B200/H200）；v0.5.11（2026-05-05，CUDA 13 + PyTorch 2.11 為預設、Speculative Decoding V2 預設開啟、PD 分離的 decode radix cache）；v0.5.10（2026-04-06，piecewise CUDA graph 預設、Elastic EP、Apple Silicon 原生 MLX backend）。 — https://github.com/sgl-project/sglang/releases
- **RadixAttention** 仍是核心賣點（KV cache 前綴重用）；新增 HiCache（UnifiedRadixTree 階層式快取）。 — https://github.com/sgl-project/sglang
- **採用狀況**（⚠️ 專案自述數字，宜註明出處為專案方）：宣稱在生產環境驅動超過 40 萬張 GPU、每日數兆 tokens，採用者含 xAI、NVIDIA、AMD、LinkedIn 等。 — https://github.com/sgl-project/sglang
- **與 vLLM 的競爭態勢**：兩者功能高度趨同（PD 分離、wide-EP、spec decode、Blackwell 支援）；NVIDIA 同時為兩者出官方 release notes / container，Dynamo 與 llm-d 等上層框架皆同時支援兩者。第三方評測互有勝負（⚠️ 例如「SGLang 在 H100 上 throughput 高 29%」之類的單點數字來自行銷性質部落格，不要直接引用）。 — https://docs.nvidia.com/deeplearning/frameworks/sglang-release-notes/index.html 、https://docs.nvidia.com/deeplearning/frameworks/vllm-release-notes/index.html

## 3. TensorRT-LLM 與 NVIDIA Dynamo

- **TensorRT-LLM 最新版本 1.2.x（PyPI 上為 tensorrt_llm 1.2.1）**，2025 年下半進入 1.x 系列後持續活躍開發。⚠️ 1.2.1 確切發布日期未能確認。 — https://pypi.org/project/tensorrt-llm/ 、https://github.com/NVIDIA/TensorRT-LLM/releases
- **Dynamo 最新穩定版 v1.2.0（2026-06-02）**，dev track v1.3.0-dev.1（2026-06-09）；另有 DeepSeek-V4、Nemotron-Ultra 等模型專用 dev branch。 — https://github.com/ai-dynamo/dynamo/releases
- **架構要點**：
  - **Planner**：負責部署最佳化、負載擴縮與 throughput modeling，整合 AIConfigurator 做效能預測。 — https://github.com/ai-dynamo/dynamo
  - **KV router**：KV-aware routing，worker 廣播 KV events，router 以 cost function 平衡 cache locality 與負載；KV indexer 採 branch-sharded concurrent radix tree。 — https://github.com/ai-dynamo/dynamo/releases 、https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/
  - **KVBM（KV Block Manager）**：framework-agnostic 的 KV cache 分層管理。 — https://docs.nvidia.com/dynamo/components/kvbm
  - **NIXL**：KV 傳輸抽象層，統一 UCX、GPUDirect Storage、S3 等 backend；TensorRT-LLM 近期版本相依 NIXL 0.8.0。 — https://docs.nvidia.com/dynamo/components/backends/tensor-rt-llm
- **支援後端**：vLLM、SGLang、TensorRT-LLM 統一抽象，並有 Prometheus metrics / OpenTelemetry tracing。 — https://github.com/ai-dynamo/dynamo
- 公有雲整合案例：AKS 上的多節點 Dynamo 部署（微軟官方部落格，2026-03-16）。 — https://blog.aks.azure.com/2026/03/16/dynamo-on-aks-part-3

## 4. llm-d

- **最新版本 v0.6.0（2026-04-03）**，搭配 inference scheduler v0.7.1（新增 no-hit-lru-scorer、active-request-scorer、speculative indexing 等 plugin）；硬體支援擴及 AMD ROCm、Intel Gaudi/HPU、CPU（AMX）。 — https://github.com/llm-d/llm-d/releases 、https://llm-d.ai/blog
- **「Well-lit paths」**：提供四條文件化、經測試與 benchmark 的生產路徑。Path 1 = intelligent inference scheduling（prefix-cache-aware routing 跨 vLLM replicas），官方數字：8 pods / 16x H100 下 TTFT 比 round-robin 快 57 倍、throughput 2 倍；Path 2 = P/D 分離，16x16 B200 拓撲達 50k output tok/s。 — https://llm-d.ai/blog/llm-d-v0.2-our-first-well-lit-paths 、https://llm-d.ai/blog/llm-d-v0.3-expanded-hardware-faster-perf-and-igw-ga
- **社群採用**：AWS 官方部落格推出「Disaggregated Inference on AWS powered by llm-d」；KServe 的 LLMInferenceService 直接建構在 llm-d 之上；Red Hat 力推 KServe + llm-d 整合。 — https://aws.amazon.com/blogs/machine-learning/introducing-disaggregated-inference-on-aws-powered-by-llm-d/ 、https://developers.redhat.com/articles/2026/04/21/kserve-llm-d-optimized-gen-ai-inference

## 5. Kubernetes

- **最新版本 v1.36「ハル (Haru)」（2026-04-22）**：70 項 enhancements（18 GA / 25 Beta / 25 Alpha）。User Namespaces GA、OCI VolumeSource GA、HPAScaleToZero 預設啟用、gitRepo volume 永久停用。 — https://kubernetes.io/blog/2026/04/22/kubernetes-v1-36-release/ 、https://www.infoq.com/news/2026/05/kubernetes-1-36-released/
- **DRA（Dynamic Resource Allocation）**：核心已於 **v1.34（2025-08/09）GA**；v1.36 持續擴充（更多 driver 與新功能，官方 blog 2026-05-07）。生態採用：Red Hat OpenShift 4.21 DRA GA（2026-03-25）、GKE 提供 DRA 裝置管理。 — https://kubernetes.io/blog/2025/09/01/kubernetes-v1-34-dra-updates/ 、https://kubernetes.io/blog/2026/05/07/kubernetes-v1-36-dra-136-updates/ 、https://developers.redhat.com/articles/2026/03/25/dynamic-resource-allocation-goes-ga-red-hat-openshift-421-smarter-gpu
- **Kubernetes AI Conformance program**：1.35 時代建立，DRA 支援是第一個 MUST 要求。 — https://kubernetes.io/blog/2026/05/07/kubernetes-v1-36-dra-136-updates/
- **Kueue**：upstream 最新 minor 為 **v0.17.0（2026-03）**——MultiKueue 階層式 cohort、LeaderWorkerSet 工作負載支援、MultiKueueOrchestratedPreemption（alpha）、RayService 跨叢集 dispatch；下游 Red Hat build of Kueue 1.3（2026-04-16）引入 v1beta2 API（v1beta1 已棄用）。 — https://github.com/kubernetes-sigs/kueue/releases/tag/v0.17.0 、https://developers.redhat.com/articles/2026/04/16/red-hat-build-kueue-1-3-batch-workload-kubernetes
- **LeaderWorkerSet（LWS）**：v0.8.0（2026-01），持續活躍；Kueue 已原生支援 LWS 的 gang admission。 — https://lws.sigs.k8s.io/docs/installation/ 、https://kueue.sigs.k8s.io/docs/tasks/run/leaderworkerset/
- **Ingress NGINX 於 2026-03-24 正式退役**（SIG Network / Security Response Committee 決定），遷移方向是 Gateway API。 — https://kubernetes.io/blog/2026/04/22/kubernetes-v1-36-release/

## 6. Gateway API Inference Extension（GIE / IGW）

- **已 GA**（v1.0 於 2025 年下半達成 GA；⚠️ v1.0 確切 GA 日期本次未能直接確認，引用前請查 releases 頁），**最新版本 v1.5.0（2026-04-19）**；v1.4.0（2026-03-20）、v1.3.1（2026-02-20）。 — https://github.com/kubernetes-sigs/gateway-api-inference-extension/releases 、https://gateway-api-inference-extension.sigs.k8s.io/
- **機制**：`InferencePool` CRD 代表一組推論 Pod（selector + targetPort + extensionRef）；**EPP（Endpoint Picker）** 透過 ext-proc 協定監看 model server 指標並做智慧路由。v1.5 新增 pool-wide saturation gauge、flow control、可插拔的 EPP payload parser framework；v1.4 為 InferencePool 加入 appProtocol（gRPC）。 — https://gateway-api-inference-extension.sigs.k8s.io/api-types/inferencepool/ 、https://github.com/kubernetes-sigs/gateway-api-inference-extension/tree/main/docs/proposals/004-endpoint-picker-protocol
- **誰在用**：GKE Inference Gateway、Envoy AI Gateway、NGINX Gateway Fabric、KServe（已 bump 至 GIE v1.2.0）、llm-d（以 IGW 為其路由層，v0.3 即宣布 IGW GA 整合）。 — https://docs.nginx.com/nginx-gateway-fabric/how-to/gateway-api-inference-extension/ 、https://aigateway.envoyproxy.io/docs/capabilities/inference/httproute-inferencepool/ 、https://github.com/kserve/kserve/pull/4886 、https://llm-d.ai/blog/llm-d-v0.3-expanded-hardware-faster-perf-and-igw-ga

## 7. KServe 與 Ray Serve

- **KServe 最新版本 v0.18.0**；**LLMInferenceService** 自 v0.16 引入，是針對 LLM 的新一代 CRD，建構在 llm-d 之上；API 已從 `serving.kserve.io/v1alpha1` 升至 **v1alpha2**（PR #4886，同時 bump GIE 至 v1.2.0）→ 仍是 alpha API，寫作時要 hedge。 — https://github.com/kserve/kserve/releases 、https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview 、https://github.com/kserve/kserve/pull/4886
- KServe + llm-d 官方聯合定位文（2026-03-05）：「Cloud-Native AI Inference at Scale」。 — https://kserve.github.io/website/blog/cloud-native-ai-inference-kserve-llm-d
- **Ray Serve LLM**：Ray 最新穩定版 2.55.x；`ray.serve.llm` 提供一級的 LLM serving API，含 **prefill/decode 分離 serving pattern**（PDProxy/PDPrefillServer/PDDecodeServer），KV 傳輸用 vLLM 的 NIXLConnector / LMCacheConnector；Anyscale 發表 wide-EP + disaggregated serving with vLLM。 — https://docs.ray.io/en/latest/serve/llm/index.html 、https://docs.ray.io/en/latest/serve/llm/architecture/serving-patterns/prefill-decode.html 、https://www.anyscale.com/blog/ray-serve-llm-anyscale-apis-wide-ep-disaggregated-serving-vllm

## 8. KV cache 生態與 context caching 定價

- **LMCache**：最新 v0.4.6（2026-05-29）；vLLM V1 KV connector 原生整合；backends 含 CPU RAM、本地 SSD、Redis/Valkey、Mooncake、S3 相容物件儲存、NIXL、GDS；支援 AMD MI300X；與 NVIDIA Dynamo 整合、與 CoreWeave 有生產合作。 — https://github.com/LMCache/LMCache
- **Mooncake**（Moonshot AI / Kimi 的 serving 平台，KVCache-centric P/D 分離架構，論文 arXiv:2407.00079）：
  - 公開生產數據：真實負載下讓 Kimi 多承接 **75% 請求**；**Kimi K2 部署在 128x H200**（PD 分離 + 大規模 EP）達 **prefill 224k tok/s、decode 288k tok/s**。 — https://github.com/kvcache-ai/Mooncake/ 、https://arxiv.org/abs/2407.00079
  - 2026 動態：vLLM 官方 feature Mooncake Store；SGLang 用 Mooncake TransferEngine 做 RDMA P2P 權重傳輸，1T 參數 Kimi-K2 權重更新 53s → 7.2s（7 倍）。 — https://github.com/kvcache-ai/Mooncake/
- **NIXL**：NVIDIA Inference Xfer Library，統一 UCX / GPUDirect Storage / S3 等傳輸 backend 的 API，是 Dynamo、vLLM（NixlConnector）、Ray Serve P/D 的共同地基；近期版本 0.8.0。 — https://docs.nvidia.com/dynamo/components/backends/tensor-rt-llm
- **各家 API context/prompt caching 定價**（cache read 相對標準 input 價）：
  - **Anthropic**：read = 基準價 10%（90% 折扣）；write 有溢價：5 分鐘 TTL = 1.25x、1 小時 TTL = 2x（例：Sonnet 基準 $3/M → read $0.30/M、5-min write $3.75/M、1-hr write $6/M）。 — https://artificialanalysis.ai/models/caching
  - **OpenAI**：自動快取、無 write 費、TTL 5–10 分鐘；折扣依模型不同——GPT-4o 為 50%。⚠️ 較新模型（GPT-5 系列）折扣更深（約 90%），但各來源說法不一（25%~90% 都有人寫），引用前務必查當下官方價目表。 — https://artificialanalysis.ai/models/caching
  - **Google Gemini**：implicit caching 自動生效；explicit caching 另收**儲存費（按小時計）**。⚠️ read 折扣各來源在 75% 與 90% 之間不一致（artificialanalysis 列 Gemini 2.5 Flash $0.30 → $0.03 即 90%），寫作時查官方價目。 — https://artificialanalysis.ai/models/caching
  - **DeepSeek**：磁碟式自動快取、業界最深折扣。V3.x 時代 cache hit 約為原價 1/10；⚠️ V4 世代有報導稱 V4-Flash cache hit = 原價 1/50、V4-Pro = 1/120（≈98–99% 折扣），但此數字僅見於第三方部落格，官方公告頁未直接確認。 — https://api-docs.deepseek.com/news/news260424 、https://devtk.ai/en/blog/deepseek-api-pricing-guide-2026/
  - 給作者的安全寫法：「Anthropic/DeepSeek 約 90%+ 折扣、OpenAI 50–90% 依模型、Gemini 75–90% 另計儲存費」。

## 9. 加速器硬體

### NVIDIA
- **B200（Blackwell）**：192 GB HBM3e、約 8 TB/s 頻寬；GB200 NVL72 = 72x B200 + 36x Grace，NVLink 5（每 GPU 1.8 TB/s 雙向）。已大規模出貨，是 2026 年主力雲端機型。 — https://www.nvidia.com/en-us/data-center/gb300-nvl72/ 、https://intuitionlabs.ai/articles/nvidia-data-center-gpu-specs
- **GB300 NVL72（Blackwell Ultra / B300）**：B300 為 288 GB HBM3e（12-hi）、8 TB/s、1,400W、15 PFLOPS dense FP4；2025 下半開始供貨，2026 年放量。 — https://www.nvidia.com/en-us/data-center/gb300-nvl72/
- **Rubin 世代**：Vera Rubin NVL72（72x Rubin GPU + 36x Vera CPU，NVLink 6）於 CES 2026 發表、GTC 2026 詳述；**Q1 2026 進入量產，H2 2026 由 AWS/GCP/Azure/OCI/CoreWeave 開始提供**。Rubin GPU：雙 reticle die、288 GB **HBM4**、約 13 TB/s（較 B300 提升 62.5%）。⚠️ 「336B 電晶體」「5x Blackwell」等數字來自二手媒體，引用前查 NVIDIA 官方規格。 — https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/ 、https://www.nextplatform.com/2025/03/19/nvidia-draws-gpu-system-roadmap-out-to-2028/

### AMD
- **MI355X**（CDNA 4、3nm）：288 GB HBM3E、8 TB/s、TBP 1,400W；2025 年已出貨。 — https://www.datacenterdynamics.com/en/news/amd-launches-instinct-mi350-gpus-unveils-double-wide-helios-ai-rack-scale-system/
- **MI400 系列 + Helios 機架**：AMD 於 2026-02-23 重申 **on track 2H 2026**。MI400：432 GB HBM4、19.6 TB/s、40 PF FP4 / 20 PF FP8；Helios（雙寬機架、OCP 設計）：72x MI450 + Zen 6 EPYC「Venice」+ Vulcano NIC，約 1.4 EF FP8 / 2.9 EF FP4、31 TB HBM4。 — https://www.nextplatform.com/compute/2026/02/23/amd-says-helios-racks-and-mi400-series-gpus-on-track-for-2h-2026/4092199 、https://www.techpowerup.com/337987/amd-previews-432-gb-hbm4-instinct-mi400-gpus-and-helios-rack-scale-ai-solution

### Google TPU
- **Ironwood（TPU v7 / TPU7x）已 GA（2025-11）**：對 v6e（Trillium）单晶片性能 >4x，驅動 Gemini 3 生產推論；Anthropic 計畫使用最高 100 萬顆 Ironwood。 — https://docs.cloud.google.com/tpu/docs/tpu7x 、https://cloud.google.com/blog/products/compute/ironwood-tpus-and-new-axion-based-vms-for-your-ai-workloads
- Google Cloud Next 2026（2026-04）發表第八代 TPU 分流設計：**TPU 8t（訓練）與 TPU 8i（推論，帶 384 MB 級大 SRAM）**，8t 對 Ironwood 訓練性價比宣稱 ~2.7–2.8x、8i 推論性價比 +80%（皆廠商數字）。（2026-06-10 二次網搜以 Google 官方部落格覆核，原「僅分析師來源」⚠️ 解除） — https://blog.google/ 、https://hyperframeresearch.com/2026/04/22/google-cloud-next-2026-google-cloud-bifurcates-the-ai-future-specialized-tpu-8t-and-8i-architectures-signal-the-end-of-general-purpose-silicon/

### AWS / 其他
- **Trainium3**：2025-12 發表，AWS 首款 3nm AI 晶片；每晶片 2.52 PF FP8、144 GB HBM3e、4.9 TB/s；UltraCluster 3.0 宣稱單一網域可達 100 萬顆。⚠️ 大規模集群數字為 AWS 行銷宣稱。 — https://awesomeagents.ai/hardware/aws-trainium3/
- **NVIDIA × Groq（~$20B，2025-12）：實為非獨家技術授權＋人才移轉協議，並非傳統股權收購**——創辦人 Jonathan Ross 率核心團隊加入 NVIDIA，Groq 保持獨立法人營運（GroqCloud 持續服務，新任 CEO Simon Edwards）。目的是把 LPU 低延遲推論納入 NVIDIA stack。（2026-06-10 二次網搜覆核**修正**：原「收購大部分股權/資產」說法不準確） — https://groq.com 、https://fortune.com/2026/01/05/nvidia-groq-deal-ai-chip-startups-in-play/
- **Cerebras**：2026-02 完成 $1B Series H（Tiger Global 領投、AMD 參投）；2026-04-17 重新遞交 S-1；**2026-05-14 已完成 Nasdaq 上市（CBRS）**——發行價 $185/股、募資約 $5.55B、上市時完全稀釋估值約 $56B（遠超 S-1 階段的 ~$23B 預估）（2026-06-10 二次網搜覆核更新）；2026-01 與 OpenAI 簽算力採購協議——750MW 起、可擴至 2GW、累計價值 $10B+（後續報導稱擴大至 $20B ⚠️ 擴大金額僅見二手中文媒體）。 — https://www.nextplatform.com/compute/2026/04/22/the-second-time-will-be-the-ipo-charm-for-cerebras/5218651 、https://www.sec.gov/Archives/edgar/data/0002021728/000162828026029503/exhibit1011-sx1a.htm

## 10. 主流開放權重模型（2026-06 時點）

- **DeepSeek-V4（官方 preview，2026-04-24）**：
  - **V4-Pro：1.6T total / 49B active**；**V4-Flash：284B total / 13B active**；兩者皆 **1M context**、支援 thinking / non-thinking 雙模式、相容 OpenAI ChatCompletions 與 Anthropic API。
  - 注意力架構：官方描述為「token-wise compression + **DSA（DeepSeek Sparse Attention）**」，是從純 MLA 路線的演進（DSA 首見於 2025-09 的 V3.2-Exp；NSA = Native Sparse Attention 為 2025-02 論文）。
  - — https://api-docs.deepseek.com/news/news260424
- **Qwen（阿里）**：
  - **Qwen3.5（2026-02-16）**：8 個模型、dense + MoE，旗艦 **Qwen3.5-397B-A17B**；架構為 Gated Delta Networks（線性注意力）+ sparse MoE；**原生 262K context、可延伸至約 1M**。 — https://qwen.ai/blog?id=qwen3.5
  - **Qwen3.6（最新）**：Qwen3.6-35B-A3B（2026-04-16，35B total / 3B active）、Qwen3.6-27B dense（2026-04-22）；262K context；主打 agentic coding 與 thinking preservation。⚠️ Qwen3.6 是否有更大旗艦版未能確認。 — https://github.com/QwenLM/Qwen3.6 、https://huggingface.co/Qwen/Qwen3.6-35B-A3B
- **Llama（Meta）**：最新開放權重仍是 **Llama 4（2025-04）**：Scout（~109B total / 17B active / 16 experts，宣稱 10M context）與 Maverick（~400B total / 17B active / 128 experts，1M context）；Behemoth 始終未發布。**2026-04-08 Meta 發布閉源模型 Muse Spark，Llama 開源路線實質終止**（詳見第 17 節）。 — https://ai.meta.com/blog/llama-4-multimodal-intelligence/ 、https://thenewstack.io/meta-abandons-llama-spark/
- **Kimi（Moonshot AI）**：K2（2025 年中，**1T total / 32B active**，MLA、384 routed experts + 1 shared、每 token 選 8 個 expert）→ K2 Thinking（2025-11）→ **K2.6（2026-04-20）**：仍為 1T/32B active、**原生 INT4**、Modified MIT 授權、新增 Agent Swarm 原語；SWE-bench Pro 58.6% 與 GPT-5.5 持平；API 價 $0.60/$2.50 per M tokens。⚠️ K2 首發月份各來源寫 2025-07 或 2025-08 不一。 — https://www.verdent.ai/guides/what-is-kimi-k2-6 、https://blog.kilo.ai/p/kimi-k26-has-arrived-an-open-weight
- **gpt-oss（OpenAI）**：gpt-oss-120b（117B total / **5.1B active**，單張 80GB H100 可跑）與 gpt-oss-20b，Apache 2.0，**原生 MXFP4 量化**，2025-08-05 發布。⚠️ 截至 2026-06 未查到後續新版（gpt-oss-2 之類不存在於本次查證範圍）。 — https://openai.com/index/introducing-gpt-oss/ 、https://huggingface.co/openai/gpt-oss-120b
- ⚠️ 其他出現在推論引擎支援清單但本次未逐一查證規格的模型：GLM-5.1（智譜）、Gemma 4（Google）、Nemotron Ultra（NVIDIA）等——寫作引用前需個別查證。 — https://github.com/sgl-project/sglang/releases
- 市場面：OpenRouter 流量中**中國系模型佔比已超過 45%**（2024 末 <2%）。 — https://openrouter.ai/state-of-ai

## 11. GPU 租用價格快照（2026-06，$/hr/GPU）

> ⚠️ 整節皆為快照性質：GPU 現貨價格波動極快（月級），書中只應寫「級距」與「倍率關係」，不要寫死絕對數字。

- **H100 80GB**：
  - Neocloud / marketplace：Vast.ai 市場價 ~$1.87 起；RunPod community $1.99 / on-demand $2.49；Lambda ~$2.99（SXM）/ $3.29（PCIe）；全市場區間約 **$1.4–$7**。 — https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison 、https://www.thundercompute.com/blog/nvidia-h100-pricing
  - Hyperscaler on-demand：AWS p5 約 **$6.9/GPU**（8 卡 ~$55/hr）；Azure ND H100 v5 約 **$12/GPU**（8 卡 ~$98/hr）；GCP A3 介於其間。專業 GPU 雲比 hyperscaler 便宜 35–50%+。 — https://www.cloudzero.com/blog/cloud-gpu-pricing-comparison/ 、https://spendark.com/blog/machine-learning-cloud-cost/
- **B200**：on-demand 主流區間 **$5.3–$6.0**（Lambda $5.29、Nebius $5.50、RunPod $5.89）；spot 低至 ~$2.1。 — https://www.spheron.network/blog/gpu-cloud-pricing-comparison-2026/
- **L4 / A10（推論入門級）**：⚠️ 本次未能取得 2026-06 的逐家精確報價；一般級距約 **$0.2–$0.8/hr**（L40S 在去中心化平台 $0.19–0.55；A10/L4 在主流平台多落在 $0.5–1.0）。建議查 https://getdeploying.com/gpus 取得即時值。 — https://getdeploying.com/gpus
- **A100 80GB** 參考點：~$1.1–2.0（已明顯被 H100 價格下殺擠壓）。 — https://www.synpixcloud.com/blog/cloud-gpu-pricing-comparison-2026

## 12. Quantization 現況

- **FP8**：已完全成熟，Hopper 以上世代的生產預設選項之一；vLLM/SGLang/TRT-LLM 全面支援（含 FP8 KV cache）；DeepSeek 等旗艦模型以 FP8 訓練。 — https://docs.vllm.ai/ 、https://github.com/sgl-project/sglang/releases
- **NVFP4**：Blackwell 專屬硬體格式（B200/B300 的 tensor core 原生支援；Hopper/Ampere 無原生 FP4）。TensorRT-LLM 0.17+ 原生支援，是目前最成熟的 FP4 路徑；vLLM 在 Blackwell 上支援 dense 與 MoE 的 FP4。NVIDIA 宣稱記憶體相對 FP16 省 3.5x、相對 FP8 省 1.8x、精度劣化 <1%（⚠️ 廠商數字，依模型而異）。 — https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference/ 、https://www.spheron.network/blog/fp4-quantization-blackwell-gpu-cost/
- **MXFP4**：OCP microscaling 開放格式；最具代表性的採用是 **gpt-oss 權重原生以 MXFP4 發布**；NVIDIA ModelOpt 在同一校準管線中支援 FP8/FP4/MXFP4/INT4；PyTorch TorchAO 已有 Blackwell 上的 MXFP8/NVFP4 kernels（diffusion 案例）。 — https://huggingface.co/openai/gpt-oss-120b 、https://pytorch.org/blog/faster-diffusion-on-blackwell-mxfp8-and-nvfp4-with-diffusers-and-torchao/
- 模型側趨勢：原生低精度訓練/發布漸成常態（gpt-oss MXFP4、Kimi K2.6 原生 INT4）。 — https://blog.kilo.ai/p/kimi-k26-has-arrived-an-open-weight

## 13. Python 生態

- **Python 3.14**（2025-10 發布，現行 3.14.5）：**free-threading（no-GIL）依 PEP 779 從 experimental 升為 officially supported**（phase II）；單執行緒 overhead 從 3.13 的 ~40% 降至 ~5–10%；另有實驗性 JIT 與 t-strings。GIL 預設仍開啟，free-threaded 是獨立 build；phase III（預設關 GIL）尚未到來。 — https://docs.python.org/3/howto/free-threading-python.html 、https://docs.python.org/3/whatsnew/3.14.html
- **uv（Astral）**：每月下載量已達 ~75M–126M（不同統計口徑），超越 Poetry；對 free-threaded 3.14+ 直譯器免 opt-in 支援。**2026-03-19 OpenAI 宣布收購 Astral**（uv/Ruff/ty 的公司），團隊併入 Codex；OpenAI 承諾繼續維護開源產品（交易尚待監管批准）。 — https://openai.com/index/openai-to-acquire-astral/ 、https://simonwillison.net/2026/mar/19/openai-acquiring-astral/ 、https://astral.sh/blog/python-3.14

## 14. Agentic workload 趨勢

- **MCP（Model Context Protocol）**：2024-11-25 由 Anthropic 發布，現已交由 Linux Foundation 旗下 Agentic AI Foundation 作中立託管；已成為 agent-tool 連接的事實標準，主要 gateway 廠商普遍整合。 — https://www.digitalapplied.com/blog/mcp-adoption-statistics-2026-model-context-protocol
- **Agentic 流量數據（最佳公開來源）**：a16z x OpenRouter「State of AI: 100 Trillion Token Study」（arXiv:2601.10088）——OpenRouter 每週處理 >20T tokens；**agentic inference 是成長最快的使用型態**（長序列多步驟取代單發 prompt）；reasoning 模型 token 佔比自 2025 初持續上升。 — https://a16z.com/state-of-ai/ 、https://arxiv.org/abs/2601.10088
- **對基礎設施的影響**：agentic 流量呈 bursty、高併發、長 session、極高 prefix 重複率——這正是 prefix caching / KV cache 分層 / P/D 分離成為 2025–2026 架構主旋律的需求面原因（可引用 llm-d、Mooncake、DeepSeek cache 定價作互證）。 — https://llm-d.ai/blog/kvcache-wins-you-can-see
- **Test-time compute**：reasoning 模型（thinking/non-thinking 雙模式已成開源旗艦標配：DeepSeek V4、Kimi K2 Thinking、Qwen3.x）把推論成本重心從單次回應轉向長思考鏈，加劇 decode 階段的容量壓力。 — https://api-docs.deepseek.com/news/news260424
- OpenRouter 於 2026-05-26 募得 $113M，定位為企業推論路由層。 — https://siliconangle.com/2026/05/26/openrouter-raises-113m-bring-order-enterprise-ai-inference-routing/

## 15. 監控與 benchmark 工具

- **DCGM-exporter**：仍是 K8s GPU 遙測的事實標準（GPU 使用率/功耗/記憶體 → Prometheus）；benchmark 工具（如 AIPerf）直接從其 /metrics endpoint 收 GPU 指標。⚠️ 最新版號未查證。 — https://lucaberton.com/blog/nvidia-aiperf-llm-inference-benchmarking-guide/
- **genai-perf**：NVIDIA 的 LLM 負載測試 CLI（TTFT、ITL、token throughput），程式碼位於 triton perf_analyzer repo；⚠️ NVIDIA 已推出後繼/更名工具 **AIPerf**（"formerly GenAI-Perf"），新舊並存期，寫作時建議以 AIPerf 為主、註明前身。 — https://github.com/triton-inference-server/perf_analyzer/blob/main/genai-perf/README.md 、https://lucaberton.com/blog/nvidia-aiperf-llm-inference-benchmarking-guide/
- **inference-perf**：kubernetes-sigs 專案（源自 **WG Serving** 的標準化倡議，非 CNCF sandbox 專案）；**v0.5.0（2026-05-01）**；特性：TTFT/TPOT/ITL/goodput、ShareGPT/合成/多模態資料、Poisson/constant/trace replay 負載、宣稱可打 10k+ QPS、engine-agnostic（任何 OpenAI 相容端點）。 — https://github.com/kubernetes-sigs/inference-perf
- **vLLM 內建 bench**：`vllm bench {serve,throughput,latency}` 已是官方 CLI 子命令（取代早年 benchmarks/ 目錄下的散裝腳本）。 — https://docs.vllm.ai/

## 16. 模擬工具

- **KWOK（Kubernetes WithOut Kubelet）**：kubernetes-sigs 專案，模擬數千節點不需真 kubelet；是 GPU 叢集模擬的標準地基。⚠️ 最新版號未查證，但生態（fake-gpu-operator 等）持續依賴它，維護狀態健康。 — https://github.com/kubernetes-sigs/kwok
- **run-ai/fake-gpu-operator**：**活躍維護中**——最新 v0.0.82（2026-06-06）、89 個 releases；模擬 NVIDIA GPU（含 **DRA 與 Compute Domain 模擬**）；repo 仍掛在 run-ai org（Run:ai 已於 2024-12 完成被 NVIDIA 收購，NVIDIA 官方文件直接引用此工具作 NVCF 開發測試用）。 — https://github.com/run-ai/fake-gpu-operator 、https://docs.nvidia.com/cloud-functions/current/latest/fake-gpu-operator.html
- **llm-d-inference-sim**：llm-d 子專案，輕量即時模擬 vLLM 行為（不需 GPU/真模型），用於測試路由/調度層；活躍。 — https://github.com/llm-d/llm-d-inference-sim
- **microsoft/vidur**：LLM 推論系統模擬器（TTFT/TPOT 預測、容量規劃）。⚠️ **維護狀態存疑**：GitHub 無正式 release、主分支 commit 數少，未能確認 2025 後是否仍積極維護；學界已有後繼比較研究（如 Frontier，arXiv 2605.21312）。引用時宜寫「研究性工具」。 — https://github.com/microsoft/vidur 、https://arxiv.org/html/2605.21312

## 17. 過去 12 個月重大事件（2025-06 ~ 2026-06）

- **Meta 放棄 Llama 開源路線**：2026-04-08 發布首個閉源模型 **Muse Spark**（Meta Superintelligence Labs，$14.3B 團隊重建、9 個月、全新架構、原生多模態 reasoning；宣稱以 <1/10 算力達 Llama 4 Maverick 水準）；Yann LeCun 已於 2025-11 離開 Meta。開放權重領導權正式移轉到中國實驗室（DeepSeek/Qwen/Moonshot/智譜）+ OpenAI gpt-oss。 — https://ai.meta.com/blog/introducing-muse-spark-msl/ 、https://thenewstack.io/meta-abandons-llama-spark/
- **NVIDIA × Groq ~$20B 協議（2025-12）**：技術授權＋人才移轉（非股權收購，Groq 仍獨立營運）；LPU 低延遲推論納入 NVIDIA 產品線；引發 AI 晶片新創整併潮討論。（2026-06-10 覆核修正） — https://groq.com 、https://fortune.com/2026/01/05/nvidia-groq-deal-ai-chip-startups-in-play/
- **OpenAI 大舉垂直整合**：2026-01 與 Cerebras 簽 $10B（據報擴至 $20B ⚠️）算力協議；2026-03-19 宣布**收購 Astral（uv/Ruff）**併入 Codex。 — https://openai.com/index/openai-to-acquire-astral/ 、https://www.nextplatform.com/compute/2026/04/22/the-second-time-will-be-the-ipo-charm-for-cerebras/5218651
- **Cerebras 完成 IPO**：2026-04-17 遞 S-1（當時估值預估 ~$23B）→ **2026-05-14 Nasdaq 上市（CBRS），上市估值約 $56B**（2026-06-10 覆核更新）。 — https://futurumgroup.com/insights/cerebras-s-1-teardown-is-the-23b-wafer-scale-ipo-the-end-of-gpu-homogeneity/
- **DeepSeek-V4 preview（2026-04-24）**：1.6T MoE + DSA 稀疏注意力 + 1M context + 極端 cache 折扣定價，再次壓低整個市場的推論價格錨點。 — https://api-docs.deepseek.com/news/news260424
- **Kubernetes 生態的 AI 轉向**：DRA GA（1.34）→ AI Conformance program（DRA 為首個 MUST）→ v1.36（2026-04-22）；**Ingress NGINX 於 2026-03-24 退役**，路由層全面轉向 Gateway API（含 Inference Extension）。 — https://kubernetes.io/blog/2026/04/22/kubernetes-v1-36-release/
- **推論層「Kubernetes 化」競合格局成形**：llm-d（Red Hat/Google/IBM 系）、NVIDIA Dynamo、KServe LLMInferenceService、Ray Serve LLM 四條路線並進，但共用同一組底層原語（vLLM/SGLang、NIXL、Gateway API Inference Extension、P/D 分離、KV-aware routing）——「KV cache 是推論的記憶體階層」成為共識性架構論述。 — https://llm-d.ai/blog 、https://github.com/ai-dynamo/dynamo
- **vLLM 完成 V0→V1 引擎世代交替**（v0.11 移除 V0）；SGLang 與 vLLM 雙雄格局穩固，NVIDIA 對兩者皆深度投入。 — https://github.com/vllm-project/vllm/releases/tag/v0.11.0
- **OpenRouter「100T token」實證研究**公開了 agentic/reasoning 流量結構，成為描述推論需求面的標準引用。 — https://a16z.com/state-of-ai/

---

## 寫作者注意事項

1. **變動最快、必須 hedge 的領域**（月級變動）：
   - 開放權重模型版本與規格（第 10 節）——DeepSeek V4 還在 preview、Qwen 兩個月一版；寫「本書寫作時最新為 X」而非「最新是 X」。
   - GPU 租價（第 11 節）——只寫級距與倍率（如「neocloud 約為 hyperscaler 的 1/2~1/3」），絕對數字一律加「2026 年年中快照」字樣。
   - 推論引擎版本號（vLLM 0.22.x、SGLang 0.5.x 每 2–3 週一版）——正文講機制、註腳講版本。
   - API caching 定價（第 8 節）——各家折扣規則 2025–2026 已多次改版，且本次查證即發現來源互相矛盾（OpenAI 50% vs 90%、Gemini 75% vs 90%）。
2. **季度級變動、需標日期的領域**：K8s 次要版本與 DRA 功能集、Gateway API Inference Extension（v1.x 每 1–2 月一版）、llm-d/KServe/Dynamo 版本、NVIDIA/AMD 硬體出貨節奏（Rubin H2 2026、MI400 H2 2026 都還是「預告」，付印前必須回查是否如期）。
3. **相對穩定、可放心著墨的內容**：架構概念（P/D 分離、KV-aware routing、prefix caching、wide-EP、MLA/DSA、test-time compute）、已 GA 的 API 形狀（DRA、InferencePool/EPP）、硬體規格已出貨部分（H100/B200/MI355X/Ironwood）。
4. **本次未能確認、寫作前必須自行查證的項目**：TensorRT-LLM 1.2.1 確切日期與 changelog、GIE v1.0 GA 確切日期、DeepSeek V4 cache 折扣倍率（1/50、1/120）、Kimi K2 首發月份、Qwen3.6 旗艦版是否存在、vidur 維護狀態、L4/A10 即時租價、OpenAI–Cerebras「擴大至 $20B」之說。（原列的 Google TPU 8t/8i 已於 2026-06-10 覆核確認，解除）
5. **政治敏感/敘事性強的題材**（Meta 棄開源、NVIDIA 收購 Groq、開源權重「中國化」）：事實本身已多方確認，但解讀分歧大，書中引用時把「事實」與「評論」分開，並優先引官方一手來源（ai.meta.com、openai.com、SEC 文件）。
6. 所有「廠商自報 benchmark」（llm-d 57x TTFT、SGLang 40 萬 GPU、NVFP4 <1% 精度損失、Mooncake 75%）引用時務必標明「according to the project/vendor」。
