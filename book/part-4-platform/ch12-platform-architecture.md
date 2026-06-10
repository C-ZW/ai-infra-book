# ch12 — 推論平台架構：從 gateway 到引擎的全鏈路

> **本章解決什麼問題**：ch08 教你把一個引擎跑起來，ch10 講了引擎池上面的智慧路由，ch11 打好了 K8s 的 GPU 地基。本章把它們組裝成一個完整的生產平台：請求從 client 進來，經過認證、計量、admission control、模型路由、endpoint 選擇，最後到 vLLM pod 吐出 token——每一段用什麼協定、會怎麼壞、為什麼傳統 L7 load balancer 在這裡不夠用。這是系統設計面試的核心題型（ch18 會拿本章的圖去面試），也是你 API gateway 與 WebSocket 經驗最直接變現的一章。Autoscaling 訊號（ch13）、可靠性細節（ch15）、計費（ch16）在各自章節深談。

## 從你已知的出發

你維護過 KrakenD：認證、rate limiting、路由規則、聚合——API gateway 這層你閉著眼睛能畫。你也做過 WebSocket fan-out：長連線的生命週期管理、斷線偵測、心跳、buffer 管理。LLM 推論平台的前半段就是這兩件事的組合，只是物理常數變了三個地方：

1. **請求成本的變異從 10 倍變成 10,000 倍**。你的遊戲 API，最慢的端點跟最快的差一兩個量級，所以 least-request LB 夠用——「一個請求 ≈ 一份負擔」的假設近似成立。LLM 請求徹底打破它：一個 10 token 的問答跟一個 100k token 的 RAG prompt，成本差四個量級，而且**從 URL 和 header 完全看不出來**——成本藏在 JSON body 的 prompt 裡，還有一半（會生成幾個 token）連 body 都看不出來。對 connection 數或 request 數做均衡，等於對著雜訊做均衡。
2. **Backend 不再是無狀態的**。ch05/ch10 講過：每個 replica 的 prefix cache 內容不同，同一個請求打到「快取命中的 pod」跟「冷 pod」，TTFT 差可達數十倍（llm-d 在 8 pods/16×H100 上量到 prefix-aware routing 對 round-robin 有 57 倍 TTFT 差距——專案自報數字，但量級方向業界公認）。路由器必須知道每個 backend 的狀態才能做對決策。你做過 session affinity，方向相同，但這裡黏錯的代價不是「重建 session」而是「重算整段 prefill」。
3. **回應從「一個 response」變成「一條持續數秒到數分鐘的 stream」**。你的 WebSocket 直覺幾乎全部適用——只是業界選的載體是 SSE（Server-Sent Events），一條披著普通 HTTP response 外衣的單向長流。它繼承了 HTTP 生態的一切好處，也繼承了 HTTP 生態裡每一個會咬斷長連線的中間件。

把這三條變化想清楚，本章的每個元件都是在回答其中一條。

## 參考架構全圖

先上圖，再逐個箭頭講協定與失敗模式。這張圖是本章的骨架，也是你面試時要能默畫的圖：

```text
                 ①HTTPS/SSE        ②HTTP (內部)                ④HTTP/SSE
 [Client/SDK] ─────────────> [API Gateway] ─────────────> [Inference Gateway] ─────────> [Engine Fleet]
                              ・認證/API key                 (Envoy data plane)           vLLM pods × N
                              ・token 計量(ch16)              ・per-model HTTPRoute        ┌────────────┐
                              ・rate limit                    ・轉發到 EPP 指定的 pod      │ base model │
                              ・admission control                  │        ▲             │ +LoRA × M  │
                                                              ③ext-proc│        │⑤metrics │ /metrics   │
                                                                (gRPC) │        │ scrape   └────────────┘
                                                                       ▼        │                │
                                                              [EPP Endpoint Picker]              │⑦
                                                               ・讀 InferencePool CRD ⑥          ▼
                                                               ・queue/KV/LoRA 指標        [權重儲存/快取層]
                                                               ・挑出目標 pod               S3/OCI ─> 節點 NVMe
                                                               (scoring 機制見 ch10)        ─> P2P 同儕 ─> HBM
```

| 箭頭 | 協定 | 關鍵語意 | 典型失敗模式 |
|---|---|---|---|
| ① Client → API GW | HTTPS + SSE（長流） | 逾時必須是 idle-based 而非總時長；斷線要往下游傳播 | 中間件 idle timeout 砍斷長 stream；proxy buffering 毀掉 TTFT；client 斷線未傳播 → 引擎繼續算沒人收的 token |
| ② API GW → IGW | HTTP（內部網路） | 認證已完成，帶上 tenant/priority metadata；**首 token 後不可盲目重試** | 重試一個已部分 stream 的請求 = 重算全部 + 重複計費；admission 佇列溢出未回 429 |
| ③ IGW ↔ EPP | gRPC（Envoy ext-proc） | 每個請求都過 EPP 一手；EPP 決策延遲直接加在 TTFT 上 | EPP 掛掉 → fail-open（退化成普通 LB，效能劣化）或 fail-closed（全量 5xx），必須明確選一個並測試過 |
| ④ IGW → vLLM pod | HTTP/1.1 或 HTTP/2 + SSE | 直連 EPP 指定的 pod（繞過 kube-proxy 的隨機性） | 打到正在 drain 的 pod（見 ch15）；pod OOM 死在 stream 中途——HTTP 200 早就發出去了，錯誤只能以斷流呈現 |
| ⑤ EPP ← pods | HTTP `/metrics` 拉取或 ZMQ/事件推送 | EPP 對 fleet 狀態的視圖永遠是滯後的 | 指標過期 → 路由決策基於幻覺；scrape 失敗 → 該 pod 從候選消失或以舊資料留任 |
| ⑥ EPP ← K8s API | watch InferencePool/Pod | reconcile 延遲秒級 | endpoint 清單滯後：新 pod 沒進池（容量浪費）、死 pod 還在池（部分請求黑洞） |
| ⑦ Pod ← 權重層 | S3 API / OCI pull / P2P / NVMe | cold start 的主要時間都花在這條邊（本章後半解剖） | S3 throttling（503 SlowDown）；HF Hub 限流或檔案被改版；節點 NVMe 被權重快取塞爆（ch15） |

兩個全圖層級的觀察：

- **認證計量在最前、狀態感知在中間、重狀態在最後**。API gateway 那層是你既有技能的直接平移（KrakenD 換成 Envoy/Kong/雲端 API GW 都一樣），唯一的新東西是計量單位從 request 變成 token（ch16）。真正的新物種是中間那層 inference gateway——它存在的理由就是開頭那三條物理變化。
- **admission control 必須在最前面**。引擎的 waiting 佇列是無界的、不會回 429（ch06 講過）；如果讓過載流量一路漏到引擎才堆積，TTFT 會無聲爆炸而 GPU 指標一切正常。你在遊戲後端做過 backpressure，原則照搬：**拒絕要趁早，排隊要有界，佇列深度要可見**。LLM 的特殊處在於「成本預估」——admission 想按成本放行，就得估 prompt token 數（粗估 chars/4，或在 gateway 跑一個快速 tokenizer），輸出端則只能用 `max_tokens` 上限保守估。死亡螺旋的完整動力學與防禦位置在 ch13。

## 為什麼 L7 LB 不夠：Gateway API Inference Extension

上面那層 inference gateway 並不是每家自己發明一套。2025–2026 年 Kubernetes 社群把它標準化成 **Gateway API Inference Extension**（GIE，也叫 Inference Gateway / IGW）：v1.0 於 2025 下半 GA，本書寫作時最新為 v1.5.0（2026-04）。它是 Gateway API 的延伸，不是新 gateway——任何支援 Gateway API + Envoy ext-proc 的實作（Envoy Gateway、kgateway、GKE Inference Gateway、NGINX Gateway Fabric…）都能升級成 inference gateway。兩個核心元件：

**InferencePool**：一個 CRD，代表「一組可以互相替代的推論 pod」——同一個 base model、同一套配置的 replicas。它取代 K8s `Service` 作為 HTTPRoute 的 backend：

```yaml
# 示意：一個模型一個 InferencePool，HTTPRoute 按模型名分流
apiVersion: inference.networking.k8s.io/v1
kind: InferencePool
metadata:
  name: llama-70b-pool
spec:
  selector:
    matchLabels: { app: vllm-llama-70b }
  targetPorts:
  - number: 8000
  endpointPickerRef:        # 把「挑哪個 pod」外包給 EPP
    name: llama-70b-epp
    port: { number: 9002 }
```

**EPP（Endpoint Picker）**：InferencePool 附帶的一個獨立服務，透過 Envoy 的 **ext-proc 協定**（gRPC streaming）介入每個請求：Envoy 把請求 header/body 交給 EPP，EPP 根據它持續追蹤的 per-pod 指標——**waiting queue 深度、KV cache 利用率、目前載入的 LoRA adapters**——挑出目標 pod，以 header 回給 Envoy，Envoy 直連該 pod。為什麼非要這樣繞一圈？逐條對應開頭的物理變化：

- **模型名在 body 裡**。OpenAI-compatible API 的路由鍵是 JSON body 的 `"model"` 欄位，URL 一律是 `/v1/chat/completions`。傳統 L7 路由按 path/header 分流，在這裡是瞎的。GIE 提供 Body-Based Routing（BBR）元件把 body 裡的模型名提取成 header，讓 HTTPRoute 能按模型分流到不同 InferencePool。
- **均衡的目標不是 request 數，是 token 成本與快取狀態**。EPP 的預設 scheduler 同時看負載（queue、KV 利用率）與 prefix cache 親和性——這正是 ch10 講的「有狀態負載均衡」的標準化落地，scoring 函數的設計取捨見 ch10，這裡只需要知道機制介面：**LB 的決策單位從 connection/request 升級成「帶狀態的成本預估」**。
- **飽和要在 pool 層面看**。v1.5 加入 pool-wide saturation gauge 與 flow control：整池飽和時在 gateway 層排隊或拒絕，而不是讓請求漏進引擎的無界佇列（2026-06）。

對你來說最划算的理解角度：**EPP 之於 Envoy，就像你寫過的自訂 LB 邏輯之於 KrakenD——只是這次社群把 hook 點標準化了**，所以 llm-d、KServe、GKE 可以共用同一套資料平面，各自只換 scheduler 插件。

Murphy 提醒：EPP 在每個請求的關鍵路徑上。它的延遲直接墊高 TTFT（健康狀態下應 <10ms）；它的可用性決定整條路。部署時必須回答三個問題——EPP 掛了 fail-open 還是 fail-closed？指標多久過期算不可信？EPP 自己的 HPA 怎麼配？這三題答不出來，不要上生產。

## 平台選項：llm-d、Dynamo、KServe、Ray Serve

2026 年的格局（ch10 提過供應端視角，這裡給平台選型視角）：四條路線並進，但共用同一組底層原語——vLLM/SGLang 引擎、GIE 路由、NIXL 傳輸、P/D 分離。差異在「組裝哲學」與甜蜜點：

| | llm-d | NVIDIA Dynamo | KServe（LLMInferenceService） | Ray Serve LLM |
|---|---|---|---|---|
| 版本（2026-06） | 0.6/0.7 | 1.2.0 | KServe 0.18，LLMISVC `v1alpha2`（仍 alpha） | Ray 2.55.x |
| 組裝哲學 | K8s 原生：直接用 GIE/IGW + vLLM + 標準 CRD，提供「well-lit paths」（文件化、benchmark 過的參考配置） | 自帶控制面：planner、KV router、KVBM、NIXL，跑在 K8s 上但核心邏輯在自己的元件裡 | 把 llm-d 包進 KServe 的 CRD 體驗：一個 `LLMInferenceService` 展開成 gateway+EPP+P/D workers（LWS） | Python 程式化組合：`ray.serve.llm` API，部署是程式碼不是 YAML |
| 路由層 | GIE EPP + inference scheduler 插件（prefix/load/SLO scorer） | 自家 KV router（radix tree 索引，見 ch10） | 繼承 llm-d 的 EPP | 自家 router + PDProxy 模式 |
| 引擎支援 | vLLM 為主（擴及 SGLang） | vLLM / SGLang / TensorRT-LLM 統一抽象 | vLLM（經 llm-d） | vLLM 為主 |
| 甜蜜點 | 平台團隊 K8s 功力深、要 upstream 標準、避免單一廠商；中大規模 vLLM fleet | NVIDIA 硬體上的大規模 P/D 分離；要廠商整合（AIConfigurator 效能預測、NGC 支援）；混引擎 | 既有 KServe/Kubeflow/OpenShift AI 資產；predictive 與 generative 模型要同一套治理 | 推論只是 Python pipeline 的一環（embedding→rerank→LLM→後處理）；團隊已用 Ray 做資料/訓練 |
| 主要代價 | 元件多（gateway/EPP/CRD 一個都不能少），除錯面積大；新專案、API 還在動 | 與 NVIDIA 生態深綁；自帶控制面與 K8s 原生工具鏈有摩擦 | 多一層抽象，出事時要穿透 KServe→llm-d→vLLM 三層；alpha API | K8s 多租戶/配額治理較弱（要 KubeRay 補）；Ray 叢集本身是一個要養的分散式系統 |
| 背後推手 | Red Hat、Google、IBM、CoreWeave 等 | NVIDIA | Kubeflow 社群、Red Hat | Anyscale |

幾個有觀點的判讀：

- **這四個不是四選一的對等競品**。KServe LLMISVC 直接建構在 llm-d 之上；llm-d 直接建構在 GIE 之上；Dynamo 的 NIXL 反過來是 vLLM 與 Ray Serve P/D 的共同地基。選型其實是在選「你想站在哪一層抽象、跟誰的 roadmap 對齊」。
- **「自組 vs 採用」的判斷準則**：單模型、個位數 GPU、無 P/D 分離需求——一個 Deployment + Service + 普通 gateway 就夠，平台框架是負資產（每個元件都是你凌晨三點要會修的東西）。需要多模型路由、prefix-aware LB、或 P/D 分離的那一天，才是引入框架的那一天；而且我會建議從 GIE 這層標準開始（它最小、最不綁定），再視規模長到 llm-d/Dynamo。
- 截至我能確認的資訊（2026-06），公開的生產背書：llm-d 有 AWS 官方的 disaggregated inference 方案與 Red Hat OpenShift AI 產品化；Dynamo 有 AKS 官方多節點部署案例；Ray Serve LLM 有 Anyscale 的商業化路徑。各家 benchmark 數字一律是專案自報，引用時記得標註。

## 多模型服務與權重分發

平台不是服務一個模型，是服務一個**模型組合**（20 個模型、各自 2–3 個版本是中型內部平台的常態）。生命週期上沒有新概念——registry → 部署 → 版本灰度 → 下線，跟你做過的服務發布同構（模型 canary 的特殊性在 ch15：品質迴歸在 5xx 看不到）。新的工程問題只有一個：**artifact 大了三個量級**。你的 Docker image 幾百 MB，一個 70B FP8 模型 70 GB。權重分發是平台層的一等公民問題：

- **HF Hub 直拉是 demo 行為，不是生產行為**。三個風險：頻寬與限流不可控（單線程數十 MB/s 級、尖峰時更糟）、可用性不在你的 SLO 裡、supply chain——`main` branch 的權重是可變的，今天拉的跟昨天拉的可能不是同一份。生產最低標準：pin revision、權重進自己的 S3/物件儲存、過 checksum。
- **S3/物件儲存是預設答案**，搭配兩個優化：載入器要併發（下一節展開），以及節點本地 NVMe 快取——同一個模型第二次在這個節點起，就不用再過網路。快取層自己會變成故障源：NVMe 被多個模型的權重塞爆是真實事故（ch15 的故障目錄有它），要有 LRU 淘汰與容量監控。
- **OCI artifact（KServe 叫 modelcar）**：把權重打成 OCI image 放 registry，沿用整套 image 工具鏈——不可變 digest、掃描、複用 registry 的快取與授權。代價是 image pull 路徑對「巨大單檔」不算友善，通常要配 lazy-pull 才划算。
- **P2P 分發**：擴容 50 個 pod 時，與其 50 個都去打 S3，不如讓已有權重的節點互相餵。Dragonfly（CNCF 畢業專案）在 HTTP 層做這件事——CNCF 的案例數字：200 節點叢集把 origin 流量從 26 TB 壓到約 130 GB（2026-04）。更激進的是 RDMA 級 P2P：SGLang 用 Mooncake TransferEngine 做權重更新，1T 參數的 Kimi-K2 從 53s 壓到 7.2s（專案自報）。P2P 的甜蜜點是「同一模型大量副本、頻繁擴容或權重熱更新」；小規模平台用不到。

## Cold start 解剖

把一個 vLLM pod 從「排程成功」到「能回首 token」的全程切開，每段的時間量級與優化手段：

| 階段 | 在做什麼 | 冷的量級 | 優化手段 → 優化後 |
|---|---|---|---|
| 1. Pod 排程 | 找到有空 GPU 的節點 | 秒級（**前提：有 warm 節點**；要開新節點是 3–10 分鐘級，那是 ch13 的 headroom 數學） | 維持 warm pool（ch13） |
| 2. Image pull | 拉 10–20 GB 的推論引擎 image（CUDA runtime + PyTorch + vLLM） | 2–5 分鐘（下載 + containerd 逐層解壓，解壓常是瓶頸） | 節點 image cache → ≈0；lazy-pull（GKE image streaming / SOCI / eStargz：先啟動、背景補檔）→ 秒到十秒級 |
| 3. 權重載入 | 儲存層 → CPU → HBM | 來源決定：數十秒到數十分鐘（worked example 詳算） | 併發載入器 + 快取分層 + P2P → 十秒級 |
| 4. Engine 初始化 | CUDA context、（TP 時）NCCL init、記憶體 profiling 與 KV pool 配置、`torch.compile`、CUDA graph capture（ch07） | 首次 2–4 分鐘（compile 占大頭） | compile cache 持久化（vLLM 支援快取編譯產物）、縮小 graph capture 範圍 → 45–90 秒 |
| 5. Warmup + readiness | 打幾個真請求確認能生成（深健康檢查，ch15） | 10–30 秒 | 維持，不建議省 |

注意這張表的結構：**前三段是「搬 bytes」，可以用錢和工程壓到接近零；第四段是「算」，目前有分鐘級的地板**。這個地板就是 scale-to-zero 討論的物理基礎（下下節）。

### Worked example：70B FP8 的 cold start 帳單

設定：70B 模型 FP8 權重 ≈ **70 GB**（每參數 1 byte）；引擎 image **15 GB**；單張 H200 141 GB 裝得下（若 TP2 部署，權重載入兩卡平行、時間近似減半，但加 10–20s NCCL init——量級不變）。節點 NIC 100 Gbps。三案的權重載入逐段算：

**Case A：從 S3 拉。** 載入器決定一切。先看證據：NVIDIA 用 Llama-3-8B（15 GB safetensors）實測，預設 safetensors loader 即使在 4 GiB/s 的 IO2 SSD 上也只吃到 ~0.32 GiB/s（單線程、序列處理 tensor），47 秒；Run:ai Model Streamer 用 32 路併發直接 S3 → CPU → GPU 流水化，4.88 秒吃滿 ~3 GiB/s（NVIDIA 技術部落格，較舊的 vLLM 0.5.x 時代數據，但「併發決定吞吐」的結論至今成立）。套到 70 GB：

- naive 路徑（`aws s3 cp` 落地再用預設 loader 載入）：下載 70 GB @ ~1 GB/s ≈ 70s，再從磁碟載入 @ ~0.3 GiB/s ≈ 220s → **約 5 分鐘**。若是 HF Hub 直拉 @ ~80 MB/s，光下載就 **~15 分鐘**。
- 優化路徑（vLLM `--load-format runai_streamer`，concurrency 調到吃滿頻寬）：70 GB @ ~3 GiB/s ≈ **~23 秒**。注意 3 GiB/s ≈ 26 Gbps——NIC 要 50 Gbps 以上才有餘裕，而且 S3 端要避開單 prefix throttling（503 SlowDown 是真實會發生的）。

**Case B：節點 NVMe 已有快取。** 不過網路。NVMe Gen4 標稱 5–7 GB/s，但 naive loader 一樣只吃到 ~0.3–0.5 GiB/s（瓶頸在 loader 不在碟）→ **2.5–4 分鐘**；併發 loader 實際可吃到 2–3 GiB/s → **~25–35 秒**。教訓：**買了快的儲存，瓶頸就移到讀它的程式**——跟你當年發現 RDS 不是瓶頸、是 N+1 query 的劇情同構。

**Case C：P2P 從同儕節點拉。** 叢集裡已有副本持有權重。Dragonfly 級的 HTTP P2P 受 NIC 限制，100 Gbps 下實際 ~5–8 GB/s → **~10–15 秒**，且 origin（S3）流量趨近零；RDMA 級（Mooncake TransferEngine）在 200–400 Gbps 網路上理論 2–3 秒、工程上 <10 秒。

把五個階段加總（image 與 compile cache 的狀態另列）：

| 情境 | 排程 | image | 權重 | engine init | warmup | **總計** |
|---|---:|---:|---:|---:|---:|---:|
| 全冷 + HF 直拉（什麼都沒做） | 5s | 180s | ~900s | 200s | 20s | **~22 分鐘** |
| 全冷 + S3 naive | 5s | 180s | 290s | 200s | 20s | **~11.5 分鐘** |
| S3 + streamer + lazy-pull image + compile cache | 5s | 30s | 25s | 75s | 15s | **~2.5 分鐘** |
| NVMe 快取 + streamer + image cache + compile cache | 5s | ~0 | 30s | 75s | 15s | **~2 分鐘** |
| P2P（RDMA）+ 全快取 | 5s | ~0 | <10s | 75s | 15s | **~1.8 分鐘** |

三個讀法：

1. **優化空間有一個量級（22 分鐘 → 2 分鐘），但地板停在分鐘級**——搬 bytes 壓到秒級之後，engine init 成為主導項。前沿的解法方向是把「初始化完成的 GPU 狀態」整個 snapshot/restore（CUDA checkpoint 一系），以及 vLLM 的 sleep mode（權重暫退到 CPU RAM、秒級喚醒）——但後者是「原地休眠」，解的是 in-place 閒置，不是 pod 級的冷啟動。截至 2026-06 這些都還不是大規模生產的標準配備。
2. **每一段優化都是用「另一種資源」換時間**：NVMe 快取用磁碟容量換、P2P 用網路與運維複雜度換、warm pool 用閒置 GPU $ 換（ch13/ch16 算這筆帳）。沒有免費的。
3. 呼應全書主軸一：cold start 的本質就是**把 70 GB 的記憶體內容從世界的某處搬進 HBM**——LLM serving 是 memory 的生意，連「開機」都是。

## LoRA 多租戶：一個 base 模型，N 個客製版本

**LoRA（Low-Rank Adaptation）**是一種 fine-tune 方法：凍結 base 模型，只訓練插在各層旁邊的低秩矩陣對。從 infra 視角你只需要記住它的形狀：**adapter 是 base 權重的千分之一量級**（70B 模型的 adapter 通常數十到數百 MB），且推論時可以在同一個 batch 裡讓不同請求走不同 adapter。

這改寫了 per-tenant 客製的經濟學。沒有 LoRA：每個租戶一份完整模型副本，10 個租戶 × 70 GB × 各自的 GPU 池——閒置與碎片吃死你。有 multi-LoRA serving：**一個 base 模型的 GPU 池，掛 N 個 adapter，所有租戶共享 batch 與 KV pool**，邊際成本從「一個 deployment」降到「幾百 MB 記憶體」。長尾租戶（流量小到單獨部署絕不划算的）因此變得可服務——這也是為什麼說 multi-LoRA 是比 scale-to-zero 更好的長尾解法。

vLLM 的支援現況（2026-06）：`--enable-lora` + `--max-loras`（單批最多同時幾個 adapter 活躍）+ `--max-lora-rank` + `--max-cpu-loras`（CPU RAM 裡的 LRU 快取池）；設 `VLLM_ALLOW_RUNTIME_LORA_UPDATING=true` 後可用 `/v1/load_lora_adapter`、`/v1/unload_lora_adapter` 端點熱載/卸載——模型生命週期管理因此可以不重啟 pod。請求端用 OpenAI API 的 `model` 欄位指定 adapter 名，對 client 而言每個租戶就是一個「模型」。

平台層的配套與 Murphy 清單：

- **路由要 LoRA-aware**：GIE 的 EPP 本來就追蹤每個 pod 目前活躍的 adapters——把請求路由到已載入該 adapter 的 pod，避免熱載延遲打在請求的 TTFT 上。
- **LRU thrash**：`max-loras` 滿了之後,新 adapter 進來要踢舊的；如果活躍租戶數持續大於池子大小，adapter 換入換出會變成穩定的延遲尖刺來源。症狀像極了你看過的 connection pool 飽和——監控 adapter cache 的 hit/miss。
- **效能稅**：LoRA 路徑比純 base 推論多一段計算，吞吐有可量測的損耗（量級隨 rank 與實作版本變動，部署前自己 benchmark，方法見 ch14）。
- **治理**：adapter 是租戶上傳的 artifact——版本 pin、來源驗證、品質 eval gate（一個壞 adapter 輸出垃圾，5xx 看不到，ch15 的品質迴歸問題在多租戶下放大 N 倍）。

## Scale-to-zero 的真實代價

把上面兩節的數字放在一起，scale-to-zero 的判斷就不需要立場、只需要算術：**流量到達是秒級的，冷啟動是分鐘級的（優化到極限 ~2 分鐘）**。第一個喚醒請求的 TTFT 至少兩分鐘——任何互動式 SLO（TTFT p95 < 數秒）直接出局，沒有討論空間。

它能用的條件，本質上是「有人願意等，或沒有人在等」：內部工具與 dev/staging 環境（等 2 分鐘可接受）、批次/非同步工作負載（本來就排隊）、真正零流量時段的長尾模型。決策上先問兩個問題：這個模型是不是某個 base 的 fine-tune？是 → 用 multi-LoRA 共享池，根本不需要 scale-to-zero。等待是否在產品語意內（如「排隊生成報告」）？否 → 留至少一個 warm replica，把錢省在別處（quantization、共享池、spot——ch16）。執行機制（Knative KPA、KEDA scale-to-zero、HPAScaleToZero）與喚醒期間的請求緩衝設計在 ch13。

## API 層設計：OpenAI-compatible 與 SSE 的工程細節

### OpenAI-compatible 是 de facto 標準的含意

所有主流引擎與平台都暴露 OpenAI 風格的 `/v1/chat/completions`。對平台架構師，這個標準化的含意有三層：client 生態免費（SDK、LangChain 類框架、各種工具直接能接）；路由鍵被固定在 body 的 `model` 欄位（前面 BBR 的存在理由）；以及**你的 API 設計自由度其實很小**——自訂欄位要走 extra body/header，錯誤語意要對齊 OpenAI 的格式，否則 client 生態的好處立刻消失。內部平台直接抄這個介面，把創意留給介面後面。

### SSE：把你的 WebSocket 經驗對照過來

Token streaming 的載體是 SSE，不是 WebSocket。一條 SSE 回應長這樣：

```text
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache

data: {"id":"chatcmpl-1","choices":[{"delta":{"content":"今"}}]}

data: {"id":"chatcmpl-1","choices":[{"delta":{"content":"天"}}]}

data: [DONE]
```

就是一個永不結束的 chunked HTTP response，每個事件是 `data: <json>\n\n`，OpenAI 慣例以 `data: [DONE]` 收尾。對照你的 WebSocket 經驗：

| 你在 WebSocket 做過的 | SSE 對應 | 差異與坑 |
|---|---|---|
| Upgrade 握手、自訂協定 | 沒有——就是 HTTP | 好處：所有 HTTP 中間件「理論上」直接通。壞處：所有 HTTP 中間件都可能 buffer 它 |
| 雙向通訊 | 單向（server→client） | 「中途取消」不能在流內發——靠 client 斷開連線（或另發 API）；所以**斷線偵測就是取消機制**，必須往下游傳播成引擎 abort（ch06） |
| 心跳 ping/pong | SSE comment（`: ping\n\n`） | 防的是 LB/proxy 的 idle timeout 在兩個 token 間隔過長（長 prefill、reasoning 模型思考中）時砍線 |
| 斷線重連 + 訊息序號續傳 | EventSource 有 `Last-Event-ID`，**但 LLM API 普遍不支援續流** | 重連 = 新請求 = 重新排隊 + 重算 + 重計費。斷流續傳是平台級的進階設計（ch15 的 retry storm 一節） |
| 自己管 buffer 與 backpressure | TCP backpressure | 慢 client 讀不動 → gateway buffer 堆積；引擎側不會因此放慢生成。gateway 對 per-connection buffer 要設上限 |

生產環境 SSE 的故障幾乎都是同一類：**鏈路上某個環節在 buffer**。Nginx 要 `proxy_buffering off`（或回應頭帶 `X-Accel-Buffering: no`）、不能對 event-stream 開 gzip（壓縮器會攢 buffer 再 flush）、雲端 LB 的 idle timeout 要大於最壞 token 間隔、應用層每個事件後要 flush。症狀的指紋很好認：**TTFT 不是變慢，而是 token 一大坨一大坨地到**——curl 看是順的（curl 不 buffer），瀏覽器/SDK 看是卡的。你調過 WebSocket 經過 ALB 的 idle timeout,這是同一場仗換了個戰場。

### 錯誤語意：200 之後世界就不同了

SSE 把錯誤切成兩個世界。**首 byte 之前**，HTTP 語意完整可用：401/403（認證）、404（模型不存在）、422/400（參數錯）、**429 + `Retry-After`**（限流與 admission 拒絕——一定要帶 Retry-After，否則 client SDK 的指數退避會自己發明 retry storm）、503（整池飽和）。這個區間的請求**還沒進引擎**，重試是安全的、便宜的。**首 byte 之後**，status code 已經是 200 並且潑出去了——中途的失敗（pod 死亡、engine OOM、上游斷線）只能表現為「流提前終止」或一個 error event。平台要做兩件事：在最後一個 chunk 帶 usage（token 計量，ch16 的計費依據）與 `finish_reason`,讓 client 能區分「正常結束」與「斷掉」；以及把「部分輸出後失敗」的請求標記出來進指標——這類失敗在 5xx dashboard 上是隱形的，卻是使用者體感最差的一種。重試政策因此必須是位置敏感的：**首 token 前可重試、首 token 後預設不重試**（重試 = 全部重算 = 雙倍帳單），完整的 retry budget 設計在 ch15。

## 故障模式與防禦

| 故障模式 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| 中間件 buffer 整條 SSE | token「一坨一坨」到、體感 TTFT 爆炸，但引擎指標正常 | 對比 curl 直連 pod vs 走完整鏈路的逐 token 到達時間 | 全鏈路盤點 buffering（nginx/LB/gzip/應用層 flush）；把「首 token 到達 client」納入 e2e 監控（ch14） |
| EPP 故障或決策過慢 | fail-open：TTFT 整體劣化（退回隨機路由、prefix 命中率掉）；fail-closed：全量 5xx | EPP 自身的延遲/錯誤率指標；prefix cache hit rate 突然下滑 | 明確選擇並演練 fail 模式；EPP 多副本；對 EPP 決策延遲設 SLO |
| EPP 視圖過期 | 部分 pod 過載、部分閒置；新 pod 不接流量 | per-pod queue 深度的離散度；scrape 失敗率 | 縮短指標更新間隔；endpoint 清單以 K8s watch 為準並監控 reconcile 延遲 |
| Client 斷線未傳播成 abort | running 數高但輸出 token 無人收；「忙碌但無效」（ch06） | gateway 連線數 vs 引擎 running 數的背離 | gateway 偵測斷線 → 呼叫引擎 abort;對 streaming 連線設 max duration 上限 |
| 擴容風暴打死權重儲存 | 大量 pod 同時冷啟，S3 503 SlowDown / HF 限流，冷啟時間雪崩式變長 | 權重下載耗時的 p99 與儲存端錯誤率 | 節點 NVMe 快取、P2P 分發、擴容批次化（一次起 N 個，不是全部） |
| 節點 NVMe 被權重快取塞爆 | pod evicted、image pull 失敗、`DiskPressure` | node filesystem 使用率、快取目錄大小 | 快取 LRU 淘汰、容量配額、把快取納入容量規劃（ch15 故障目錄） |
| LoRA adapter thrash | 特定租戶 TTFT 規律尖刺，與 adapter 載入事件相關 | adapter cache hit/miss、載入耗時直方圖 | 調大 `max-loras`/`max-cpu-loras`；EPP 做 LoRA-aware 路由；長尾租戶分池 |
| Admission 缺位，引擎佇列當緩衝 | TTFT 無聲爆炸,GPU/5xx 指標全綠 | 引擎 `num_requests_waiting` 持續上升（ch06） | admission control 放 gateway,有界佇列 + 429 + Retry-After；佇列深度告警（ch13 接手 autoscaling） |
| 模型 artifact 不可重現 | 同一個「模型」在不同 replica 行為不同；品質投訴無法 bisect | 權重 checksum/digest 不一致 | pin revision、自管儲存、OCI digest 化；部署記錄 artifact hash |

## 動手做

### 實驗 1 [M1]：在模擬叢集上體驗 InferencePool 路由

目標：不碰 GPU，把「gateway → EPP → 多個 backend」這條路真的跑起來。用 kind + 一個支援 GIE 的 gateway（kgateway 或 Envoy Gateway）+ llm-d-inference-sim 當假引擎。

```bash
# 1. 建叢集，裝 Gateway API + Inference Extension CRDs（版本以官方 quickstart 為準）
kind create cluster --name igw-lab
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api-inference-extension/releases/latest/download/manifests.yaml

# 2. 部署 3 個 llm-d-inference-sim pod 當 vLLM 池（帶 app: vllm-sim label）
#    （sim 支援設定 TTFT/ITL/max-num-seqs，旗標以 repo README 為準）
# 3. 建 InferencePool + EPP + HTTPRoute（官方 getting-started 有完整 YAML）
# 4. 打流量並觀察路由分布
for i in $(seq 1 50); do
  curl -s $GATEWAY_IP/v1/completions -H 'Content-Type: application/json' \
    -d '{"model":"fake-8b","prompt":"hello","max_tokens":32}' &
done
kubectl logs -l app=vllm-sim --prefix | grep -c POST   # 看各 pod 的分配
```

**成功標準**：（a）能畫出請求實際走過的路徑（gateway → EPP ext-proc → 指定 pod），並用 EPP log 證明；（b）把一個 sim pod 的模擬 queue 長度調高，觀察 EPP 把流量導開；（c）kill 掉 EPP，回答「你的 gateway 是 fail-open 還是 fail-closed」並用實驗證明。做完這個實驗，本章架構圖的左半邊就是你親手摸過的東西。

### 實驗 2 [M1]：SSE 鏈路的 buffering 偵錯演練

在實驗 1 的鏈路前面再加一層 nginx（預設開 proxy_buffering），用一個故意慢的 sim（ITL 200ms）對比 `curl -N` 直連 vs 走 nginx 的逐 token 到達時間，然後修好它（`proxy_buffering off` / `X-Accel-Buffering: no`）。**成功標準**：你能在修好前後各錄一段 token 到達時間戳，量化說明「buffer 不改變吞吐、只毀掉 streaming 體感」。

### 實驗 3 [紙上推演]：為「5 個團隊、20 個模型」設計內部平台

規格：3 個高流量產品模型（其中一個 70B）、12 個各團隊的 LoRA fine-tune（共享兩個 base）、5 個長尾實驗模型；互動式 SLO TTFT p95 < 2s；GPU 預算有限。交付一頁設計文件：（a）完整架構圖（照本章骨架，每個箭頭標協定）；（b）InferencePool 怎麼劃（提示：per-base-model，LoRA 走 multi-LoRA 池）；（c）每類模型的冷啟動策略（warm pool / NVMe 快取 / scale-to-zero / multi-LoRA，各自為什麼）；（d）三個你預期最先發生的故障與對應防禦。**成功標準**：把文件唸給一個資深後端同事聽，他能在 10 分鐘內複述你的設計與理由——這份文件就是 ch18 系統設計面試的草稿。

## 這個領域往哪走

短期（1–2 年）：GIE 已經贏下「標準介面」這一格——四大平台共用它，接下來的競爭在 EPP 之上的 scheduler 智慧（SLO-aware、預測式路由）與 flow control 的成熟度。Cold start 那條「engine init 分鐘級地板」是下一個被攻擊的目標：GPU 狀態 snapshot/restore、編譯產物的全叢集共享、引擎的 partial warm 都在路上——如果地板被打穿到秒級，ch13 的 autoscaling 數學與 scale-to-zero 的結論都要重算（這是我會持續盯的少數幾個「會改變架構結論」的技術點）。平台層的整併也會繼續：四條路線共用的原語越來越多，差異化收斂到控制面體驗與生態綁定——學原語（GIE、P/D、KV 分層），不要把職涯押在單一框架的 API 上。

## 自我檢核

1. 為什麼傳統 L7 load balancer（least-request/round-robin）對 LLM 流量會做出系統性的壞決策？至少給出三個結構性原因（成本變異、狀態、路由鍵位置）。
2. 畫出 client 到首 token 的完整鏈路，標出每段協定，並指出「admission control 必須放在哪、為什麼不能靠引擎佇列」。
3. InferencePool 和 K8s Service 的本質差異是什麼？EPP 用哪些訊號挑 pod？EPP 掛掉時 fail-open 與 fail-closed 各是什麼後果，你會怎麼選？
4. llm-d、Dynamo、KServe、Ray Serve 各自的甜蜜點是什麼？什麼情境下你會建議「都不要用，自組」？
5. 默寫 cold start 的五個階段與各自的時間量級。70B FP8 從 S3 拉，naive 與優化後的權重載入時間各約多少？為什麼優化到最後瓶頸會落在 engine init？
6. Multi-LoRA serving 改變了什麼經濟學？它跟 scale-to-zero 在「長尾模型」問題上是什麼關係？LoRA thrash 的症狀長什麼樣？
7. SSE 與 WebSocket 的三個關鍵差異？「token 一坨一坨到但吞吐正常」的診斷順序是什麼？
8. 為什麼 LLM API 的重試政策必須以「首 token」為分界？429 回應為什麼必須帶 Retry-After？

## 延伸閱讀

- [Gateway API Inference Extension 官方文件](https://gateway-api-inference-extension.sigs.k8s.io/) — InferencePool/EPP 的第一手規格與 getting-started，本章左半張圖的權威來源，版本演進快、以它為準。
- [Endpoint Picker Protocol 提案文件](https://github.com/kubernetes-sigs/gateway-api-inference-extension/tree/main/docs/proposals/004-endpoint-picker-protocol) — EPP 與 gateway 之間 ext-proc 契約的設計細節，想自己寫 scheduler 插件從這裡開始。
- [llm-d: Our first well-lit paths](https://llm-d.ai/blog/llm-d-v0.2-our-first-well-lit-paths) — 「well-lit path」哲學的原始陳述與 benchmark 設定，學習他們怎麼誠實地呈現效能數字。
- [KServe LLMInferenceService 概觀](https://kserve.github.io/website/docs/model-serving/generative-inference/llmisvc/llmisvc-overview) — 一個 CRD 怎麼展開成 gateway + scheduler + P/D workers 的完整範例，理解「平台抽象層」的代價與收益。
- [Ray Serve LLM 文件](https://docs.ray.io/en/latest/serve/llm/index.html) — Python 組合路線的代表，與 K8s 原生路線對照著讀,選型的判斷會立體很多。
- [Introducing NVIDIA Dynamo（NVIDIA Technical Blog）](https://developer.nvidia.com/blog/introducing-nvidia-dynamo-a-low-latency-distributed-inference-framework-for-scaling-reasoning-ai-models/) — Dynamo 的架構自述（planner/KV router/NIXL），讀時記得它同時是技術文件與行銷材料。
- [Reducing Cold Start Latency with Run:ai Model Streamer（NVIDIA Technical Blog）](https://developer.nvidia.com/blog/reducing-cold-start-latency-for-llm-inference-with-nvidia-runai-model-streamer/) — 本章 worked example 引用的載入器 benchmark 原始數據，方法論寫得完整，值得學它怎麼控制變因。
- [vLLM 官方文件：LoRA Adapters](https://docs.vllm.ai/en/stable/features/lora/) — multi-LoRA 參數與動態載卸 API 的第一手資料。
- [P2P acceleration for AI model distribution with Dragonfly（CNCF Blog, 2026-04）](https://www.cncf.io/blog/2026/04/06/peer-to-peer-acceleration-for-ai-model-distribution-with-dragonfly/) — 權重 P2P 分發的生產案例與流量數據。
- [GKE image streaming 介紹（Google Cloud Blog）](https://cloud.google.com/blog/products/containers-kubernetes/introducing-container-image-streaming-in-gke) — image lazy-pull 的代表性實作,cold start 階段 2 的優化原理。
