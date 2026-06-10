# AI Infrastructure 轉職學習計劃書

> 從 Senior Backend（Node/TS）轉向 AI Infrastructure / Inference Engineer
> 設備：MacBook Pro (M1) ｜ 策略：模擬優先、租 GPU 補硬體
> 本計劃以「能力」為單位而非時間，依模組逐級攻克，每級以考核通過為前進條件。

---

## 一、目標與定位

**目標角色**：AI Infrastructure / LLM Inference Engineer——負責讓大型模型在叢集上跑得穩、快、省，處理排程、路由、autoscaling、推論效能優化。

**核心論點**：大規模服務 LLM 本質上是「分散式系統問題」，不是模型問題。六年的高併發、效能調校、event-driven 與可觀測性經驗，是這個角色最缺、也最難被 AI 自動化的底子。門檻高、供給稀缺，正好對齊「長期仍站得住」的目標。

**定位句（履歷與面試用）**：

> 「我不是想轉 AI 的後端工程師，而是用同一套效能工程方法（量測 → 診斷 → 優化 → 用數據證明），把過去在 RDS／高併發系統上的成果，複製到 GPU 推論服務上的人。」

---

## 二、核心策略（三條原則）

1. **模擬優先，硬體後補。** 編排與效能建模兩層可在 M1 上免費、無限練（業界官方工具就支援）；需要 NVIDIA GPU／CUDA 的部分用按小時租的雲端 GPU 補上，成本壓到最低。
2. **每個專案往「上一層」做。** 不停在「能動就好」。做服務要做到能量化它何時會壞、優化前後差多少。深度差一層，作品說服力差很多。
3. **敘事連續性。** 所有作品都套用既有的成功模板（「降 RDS CPU 40%」式的量測—診斷—優化—數據佐證），讓轉職故事連貫。

---

## 三、能力地圖

### 已具備（直接遷移，是護城河）

- Kubernetes（EKS、CronJobs）、AWS（ECS、Lambda、SQS、SNS、RDS、S3）
- Event-driven 架構、idempotent consumer、最終一致性
- 可觀測性：CloudWatch、自建 FluentBit pipeline
- 負載測試：k6、Vegeta（直接對應 infra 的 benchmark 工作）
- **效能工程本能**：profiling、找瓶頸、為延遲／吞吐重構系統 ← 最關鍵的可遷移資產

### 需要補（依優先序）

1. **語言橋接**：Python（主力）、Go（K8s controller／scheduler）
2. **推論內部機制**：forward pass、KV cache、PagedAttention、continuous batching、prefill/decode 分離、quantization（AWQ/GPTQ/FP8）、speculative decoding
3. **GPU 排程**：MIG、vGPU、time-slicing、topology-aware scheduling、GPU bin-packing
4. **服務層工具**：vLLM、NVIDIA Triton、KServe、Ray Serve、llm-d
5. **IaC 與監控**：Helm、Terraform、Prometheus／Grafana（監控已有底子）

### 業界職缺能力要求對照（先知道終點長怎樣）

**硬性要求（must-have，幾乎每個職缺都列）**

- 理解 LLM forward pass、KV caching、prefill/decode 分離、continuous batching
- vLLM 推論優化與部署
- Python（模型介面）＋ Go（K8s controller／scheduler 邏輯）
- 大規模／多租戶 Kubernetes
- Helm、Terraform 等 IaC
- 為延遲／吞吐 SLO 跑 benchmark，在意 TPOT、GPU 使用率

**加分項（nice-to-have，拉開薪資與層級差距）**

- MIG／vGPU 配置、GPU 虛擬化
- quantization（AWQ、GPTQ）、speculative decoding
- 多叢集網路（Cilium、Calico）
- 對開源 AI infra 專案（vLLM、KServe、Kubernetes）有貢獻
- Prometheus／Grafana、GitOps、可觀測性 stack

---

## 四、學習路線（分級能力模組）

> 每個模組包含三部分：**學習內容**（細節）、**需具備的能力**（過關標準）、**考核方式**（怎麼驗證自己真的會了）。考核分三種：口頭（能講清楚＝真懂）、實作（能做出來＝會用）、產出（留下作品＝可展示）。

---

### 模組一：基礎與語言橋接

**學習內容**

- Python 到「能寫服務」：型別註記、async/await、venv／套件管理、用 FastAPI 寫一個 async 服務、用 pydantic 做資料驗證。（以 TS 底子，重點是熟悉生態而非從零學程式）
- LLM 推論基礎：tokenization；prefill（吃 prompt、compute-bound）vs decode（逐 token、memory-bound）兩階段；autoregressive 為何一個字一個字吐；KV cache 在解什麼問題；batching 為何提升吞吐。
- 本機環境：Ollama／MLX／llama.cpp 安裝與跑模型；量化格式（GGUF、不同 bit 數）的差別。

**需具備的能力**

- 能用 Python 寫出一個 async API 服務。
- 能準確說出 LLM 推論的兩階段與各自瓶頸。

**考核方式**

- 口頭：能向非專業者解釋「為什麼 LLM 一個字一個字吐、瓶頸常在記憶體頻寬而非算力」。
- 實作：在 M1 上跑同一模型的兩種量化版本，量出延遲與記憶體差異並解釋原因。
- 產出：一頁概念筆記（KV cache／batching／quantization，用自己的話）。

---

### 模組二：編排／排程模擬層 ★ 重點

全程 M1、零 GPU 費用，練的正是分散式系統強項的延伸。

**學習內容**

- 本機 K8s：k3d／kind 建叢集、kubectl、Deployment／Service／PVC、HPA。
- KWOK：無 kubelet 模擬大量節點、stage 設定。
- run-ai/fake-gpu-operator：安裝、label 節點、生出「多張 H100」假節點、注入假 `nvidia-smi`、模擬 MIG。
- llm-d-inference-sim：當 OpenAI 相容後端，設定 TTFT、inter-token latency、jitter，模擬 prefill/decode 分離下的 KV-cache 傳輸延遲。
- GPU 排程概念：為何 GPU 預設不可超賣、不可請求「部分 GPU」；MIG 切分；time-slicing；device plugin 與 extended resources；topology-aware scheduling；GPU bin-packing。
- Helm 部署；Prometheus（exporter、PromQL）＋ Grafana dashboard。

**需具備的能力**

- 能無硬體搭出模擬 GPU 叢集，並在上面部署假推論服務。
- 能設定／調整一個排程或路由策略，並用監控觀測其效果。
- 能解釋 K8s 如何把 GPU 當資源排程，以及 MIG 與 time-slicing 的差別與適用場景。

**考核方式**

- 口頭：解釋「為什麼 K8s 預設不能把一張 GPU 分給兩個 Pod，業界用哪些方式繞過，各有什麼代價」。
- 實作：一鍵 `setup.sh` 拉起整套模擬叢集；改一個排程／autoscaling 參數，用 Grafana 展示佇列深度與延遲的前後變化。
- 產出：**旗艦專案①** repo（含 README）＋ 一篇技術文章（開始累積公開足跡）。

---

### 模組三：效能建模與優化思維

**學習內容**

- Vidur（microsoft/vidur）：安裝、跑模擬、用 Vidur-Search 自動找最省錢配置、看懂它對 operator 的建模方式。
- 核心指標：TTFT、TBT／ITL、throughput、goodput、P50/P95/P99 延遲、SLO。
- 平行策略：tensor parallel、pipeline parallel、data parallel 的差別與取捨。
- Batching：static vs continuous batching；max batch size 對延遲與吞吐的取捨。
- Quantization（AWQ／GPTQ／FP8）的原理與「品質 vs 速度／記憶體」取捨；speculative decoding 原理。

**需具備的能力**

- 能在不跑真推論的前提下，推估某個部署配置的延遲與吞吐。
- 能在給定延遲 SLO 下做容量規劃與硬體選型。

**考核方式**

- 口頭：解釋「continuous batching 為何提升吞吐、代價是什麼」「tensor parallel 與 pipeline parallel 各在什麼情況用」。
- 實作：用 Vidur 對一個模型跑出「配置 vs 吞吐 vs 成本」分析。
- 產出：**旗艦專案②** 配置權衡決策報告——能回答「要在 P95 延遲 < X 下服務 Y QPS，該選什麼卡、開多大 batch、用什麼平行策略」。

---

### 模組四：真 GPU 與真 vLLM ★ 作品集核心

到此才開始花 GPU 錢，金額可控（一張 L4／A10 每小時約 1–2 美金，用完即關）。

**學習內容**

- 租 GPU 流程（RunPod／Lambda／Vast.ai）與成本控制。
- vLLM 部署與關鍵參數：`max-num-seqs`、`gpu-memory-utilization`、`max-model-len`、`tensor-parallel-size`、quantization 選項。
- Benchmark：用 k6／locust／vLLM 內建 bench 打負載，量 TTFT／TPOT／throughput／GPU util。
- Profiling：nvidia-smi、nvitop，判斷瓶頸在 compute、memory bandwidth 還是 KV cache。
- 優化：調 batching、套 quantization、調整 KV cache 配置。

**需具備的能力**

- 能在真 GPU 上部署 vLLM 並做出可重現的 benchmark。
- 能做出量化的優化前後對比，並解釋每一步的取捨與量測方法。

**考核方式**

- 口頭：對你做的每一步優化，能回答「為什麼有效、代價是什麼、怎麼量出來的」。
- 實作：完整跑一遍「量測 → 診斷 → 優化 → 驗證」閉環。
- 產出：**旗艦專案③** 優化前後對比圖與報告（敘事模板與履歷的「降 RDS CPU 40%」一致）。

---

### 模組五：分散式與生產級深度

**學習內容**

- Ray Serve／KServe／llm-d：多節點推論、多模型共用叢集、KV-cache 感知路由、prefill/decode 分離部署、scale-to-zero。
- Go：讀懂 K8s controller／operator／device plugin 的結構，能改小東西。
- 生產級議題：canary rollout、graceful shutdown（不掉 in-flight 請求）、用佇列深度／KV cache 使用率（而非 CPU）做 autoscale、自訂 Prometheus 指標。
- 開源：閱讀 vLLM／KServe／Kubernetes 的 issue，提小 PR 或文件貢獻。

**需具備的能力**

- 能設計並部署一個含路由、監控、graceful shutdown 的多模型／多節點推論平台。
- 能讀懂並小幅修改 Go 寫的 K8s 控制邏輯。
- 有一個被社群接受（merged 或獲正向討論）的開源貢獻。

**考核方式**

- 口頭：在白板上設計「一套可擴展的 LLM 推論服務」並說明每個取捨。
- 實作：部署一個接近生產形態的平台，能展示 canary 與 graceful shutdown 不掉請求。
- 產出：**旗艦專案④** ＋ 至少一個開源貢獻連結。

---

### 模組六：作品集、公開足跡與求職

**學習內容／要做的事**

- 把四個旗艦專案整理成作品集（GitHub ＋ 兩篇深度技術文章）。
- 履歷與 LinkedIn 重新定位為 AI Infra 方向，量化每個專案成果。
- 系統設計面試準備，聚焦「設計一套 LLM 推論服務」這類題目。
- 軟實力：把技術決策講給非技術的人聽（資深／staff 級別的天花板關鍵）。

**需具備的能力**

- 能清楚展示作品與成果敘事。
- 能通過系統設計面試與行為面試。

**考核方式**

- 模擬面試：在 45 分鐘內白板設計一套可擴展的 LLM 推論服務並說明取捨。
- 履歷檢核：每個專案都有可量化的成果數字。
- 作品集檢核：每個 repo 都能一鍵跑起來、有清楚 README、附對應文章。

---

## 五、作品集總覽（面試要展示的）

| #   | 專案                                                 | 證明的能力                      | 用到真 GPU？ |
| --- | ---------------------------------------------------- | ------------------------------- | ------------ |
| ①   | 模擬推論叢集（KWOK + fake-gpu-operator + llm-d-sim） | K8s GPU 排程、路由、autoscaling | 否           |
| ②   | 配置權衡研究（Vidur）                                | 容量規劃、成本／效能取捨        | 否           |
| ③   | vLLM 推論效能優化                                    | 真實 benchmark、profiling、優化 | 是（租）     |
| ④   | 多模型／多節點服務平台                               | 分散式推論、生產級架構          | 部分         |

---

## 六、學習資源（起手清單）

**模擬工具**

- KWOK — `github.com/kubernetes-sigs/kwok`
- Fake GPU Operator — `github.com/run-ai/fake-gpu-operator`
- llm-d-inference-sim — `github.com/llm-d/llm-d-inference-sim`
- Vidur — `github.com/microsoft/vidur`

**推論服務**：vLLM（核心，務必熟）、NVIDIA Triton、KServe、Ray Serve、llm-d

**本機模型（M1）**：Ollama、MLX、llama.cpp

**租 GPU**：RunPod、Lambda、Vast.ai（按小時、用完即關）

**追蹤生態**：vLLM／KServe／llm-d 官方 blog 與 release notes（領域變很快，定期看）

---

## 七、整體能力檢核（求職就緒門檻）

> 當以下全部能做到，代表已達「可投遞 AI Infra 職缺」的門檻。這是最終總考核。

- [ ] 能無硬體模擬出 GPU 叢集，並解釋 K8s 如何排程 GPU。
- [ ] 能在真 GPU 上部署 vLLM，並做出有數據的優化前後對比。
- [ ] 能在給定延遲 SLO 下做硬體選型與容量規劃。
- [ ] 能在白板上設計一套可擴展的 LLM 推論服務，並講清楚每個取捨。
- [ ] 能用分散式系統的語言（排程、一致性、瓶頸、可觀測性）解釋 LLM 服務的每個設計決策。
- [ ] 具備硬性要求清單上的全部能力（見第三節「對照」）。
- [ ] 有四個作品 ＋ 公開技術文章 ＋ 至少一個開源貢獻。

---

## 八、風險與調整原則

- **領域變動快**：工具會換（vLLM 參數、新框架），但「分散式系統 ＋ 效能工程」的底層思維不會。學工具時永遠多問一句「它在解什麼系統問題」，知識才能跨越版本。
- **別過早鑽 CUDA kernel**：那是離既有背景最遠、最不該一開始投入的地方。模擬碰不到它沒關係，等真有需要再補。
- **保持上移**：長期而言價值會從「寫 code」移向「決定建什麼、怎麼權衡、帶方向」。每個專案都順手練「把決策講清楚」，比多學一個框架更決定上限。
- **以考核通過為前進條件**：不要因為「學完內容」就跳下一級，而要因為「通過考核」才前進——口頭講不清楚就代表還沒真懂。

---

## 九、概念螺旋地圖（同一概念跨模組的回訪）

> 這份計劃表面是六個模組的直線，實際上核心概念會在多個模組以**更高 altitude** 回來。
> 下表把「回訪」變可見、可排程——別把任何概念當「模組 X 學完就結束」。
> 讀法：● ＝首次引入（introduce）；◆ ＝深化（deepen）。括號項是教學實作補的、非原計劃明列。

| 概念 ＼ 模組 | 一 | 二 | 三 | 四 | 五 | 觸點 |
| --- | --- | --- | --- | --- | --- | --- |
| prefill/decode 分離 | ● 兩階段概念 | ◆ 模擬 KV 傳輸延遲 | ◆ TTFT/TBT 指標 | ◆ profiling 判瓶頸 | ◆ 分離部署 | 5 |
| KV cache | ● 在解什麼問題 | ◆ KV 傳輸延遲 | ◆ 容量規劃 | ◆ 調 KV 配置 | ◆ KV-cache 感知路由 | 5 |
| 量測→診斷→優化（主敘事） | ● roofline 利用率 | ◆ Grafana 佇列/延遲前後 | ◆ Vidur 配置 vs 成本 | ◆ 真 benchmark 優化前後 | | 4 |
| continuous batching | ● 為何提升吞吐 | | ◆ static vs continuous 取捨 | ◆ 調 batching | | 3 |
| quantization | ● GGUF/bit 數實測 | | ◆ AWQ/GPTQ/FP8 原理取捨 | ◆ 套用優化 | | 3 |
| GPU 排程／資源 | （● lab 容量限制 503） | ● MIG/time-slicing/bin-packing | ◆ 容量規劃 | | ◆ KV/佇列做 autoscale | 3–4 |
| 可觀測性（Prometheus/Grafana） | | ● 導入 | | ◆ GPU util | ◆ 自訂指標 | 3 |
| autoscaling | （● 容量訊號 available_slots） | ● HPA 參數 | | | ◆ 用 KV/佇列深度 | 2–3 |
| 把取捨講清楚（軟實力） | ● 口頭考核 | ◆ | ◆ | ◆ | ◆ 白板設計 | 6（貫穿全程） |

**怎麼用這張表**

- **深化（◆）不是重學**：每次回訪要比上次更深一層，且能說出「這次深在哪」。若某次回訪只是把上次的話再講一遍，代表那一格沒真的上移。
- **這就是 L0/L1 之外的真實學習量**：六個模組（L1）底下，藏著約 22 次概念回訪（L2 螺旋）＋每道考核失敗就重來（L0）。把計劃當「六關打完」會嚴重低估，且讓每個概念淺嘗即止。
- **維護迴圈（L3，不在表內）**：`vLLM` 參數（模組四）、`llm-d`/`KServe` API（模組五）、`Vidur`（模組三）會隨版本漂移；第六節「定期看 release notes」與第八節「領域變動快」就是這條永不關閉的迴圈。學工具時回到「它在解什麼系統問題」，知識才跨得過版本。

> 方法論細節（L0–L3 四層迴圈的定義與生成規則）見 repo root 的 `LEARNING-LOOP.md` 的 LOOP SCOPES 段。

---

_本計劃為能力框架，建議定期回顧並依實際進度與市場變化調整。_
