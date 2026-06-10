# ch18 — 把能力變成職涯：作品集、面試、開源

> **本章解決什麼問題**：前十七章把知識裝進你腦袋，本章把它變成 offer。知識不會自動轉換成職涯——市場只看得到三樣東西：可驗證的作品、面試房間裡四十五分鐘的表現、以及公開的足跡（文章與開源貢獻）。本章給你四套工具：plan.md 四個旗艦專案的深度升級路線、一場完整示範的系統設計面試（本章的 worked example）、各開源專案的貢獻策略，以及讓知識不過期的維護迴圈。所有技術機制都只引用前章章號，不再展開。

## 從你已知的出發

你已經成功做過一次「把工程成果變成職涯資產」這件事。「降 RDS CPU 40%」這條履歷之所以有效，不是因為 40% 這個數字大，而是因為它的敘事結構完整：有量測（Clinic.js、load test）、有診斷（鎖競爭、交易熱點）、有優化動作（SQL 重排、交易拆分、批次化）、有驗證後的數據。面試官聽完知道你不是運氣好，是有方法論——同一套方法丟到任何系統上都會再產出一次 40%。

轉職 AI infra 的求職工程，就是把這個結構**再執行一次，換掉名詞**。CPU% 換成 TTFT 與 goodput（見 ch14），Clinic.js 換成 DCGM 與 engine metrics，k6 打的對象從 REST API 換成 SSE token stream。這正是全書主軸二：量測 → 診斷 → 優化 → 用數據證明，原封不動搬家。

另一個你熟的視角：求職本身是一個有 SLO 的 serving 系統。履歷是 admission control（90% 的請求在這裡被拒絕，而且是 silent drop，沒有錯誤碼）；面試是深健康檢查（探的不是你「活著」，是你能不能在壓力下生成正確的 token）；作品集是你的 `/metrics` endpoint——面試官想抓你的歷史數據，你得先有 exporter。本章就按這條 pipeline 逐段加固。

## 本書 ↔ plan.md：四個旗艦專案的對應與深度升級

plan.md 的四個旗艦專案是你作品集的骨架。下表先對應「每個專案用到哪些章」，再給每個專案一條「深度升級建議」——也就是把專案從「能動」推到「面試官眼睛一亮」要補的那一層。判準很簡單：**教學式作品（照 README 跑通）面試官看過一百次；有自己的量測、取捨與反直覺發現的作品，他們一年看不到幾個。**

| # | 旗艦專案 | 對應章節 | 證明的能力 |
|---|---|---|---|
| ① | 模擬推論叢集（kind + KWOK + fake-gpu-operator + llm-d-inference-sim） | ch11（主場）、ch12、ch13、ch14 | K8s GPU 排程、路由、autoscaling、可觀測性 |
| ② | 配置權衡研究（容量規劃與成本建模） | ch02、ch03、ch06、ch09、ch13、ch16 | 容量數學、SLO 驅動的硬體選型、$ 思維 |
| ③ | vLLM 推論效能優化（租 GPU） | ch05、ch06、ch07、ch08、ch14 | 真實 benchmark、profiling、優化閉環 |
| ④ | 多模型／多節點服務平台 | ch09、ch10、ch12、ch15、ch16 | 分散式推論、生產級可靠性、多租戶 |

**專案① 的深度升級**：基本版是「拉起模擬叢集、部署假負載」。升級版要做三件事：（a）用 KEDA 接佇列深度驅動 autoscaling，並用 Grafana 截圖證明「改參數前後，佇列深度與 TTFT 曲線怎麼變」（ch13 的訊號選擇直接落地）；（b）故意做壞一次——把 autoscaling 訊號換成 CPU%，展示它如何完全不動作，這個「對照組」是整個專案最有面試價值的部分；（c）一鍵 `setup.sh` 加上 README 前三行就放數字。面試官一問「為什麼不用 GPU utilization 當訊號」，你直接打開自己的 dashboard 回答（ch13、ch14）。

**專案② 的深度升級**：plan.md 原案用 Vidur，但截至我能確認的資訊（2026-06），Vidur 的維護狀態存疑（無正式 release、commit 稀疏），把整個專案押在它上面有風險。升級路線：以自己的解析模型為主——用 ch03 的 KV 公式、ch02 的 roofline、ch13 的容量方法論建一張試算表或一支小工具，輸入「模型、卡型、SLO、流量分布」輸出「卡數與月成本」；Vidur 作為交叉驗證之一，再用專案③ 的實測數據回頭校準你的模型。「我的解析模型預測 X，實測 Y，誤差 Z% 來自…」這句話的面試殺傷力，遠大於「我會用某個模擬器」。

**專案③ 的深度升級**：基本版是「部署 vLLM、跑 benchmark」。升級版：（a）跑出完整的 latency-throughput frontier 曲線而不是單點數字（ch14）；（b）benchmark 方法論要經得起拷問——open-loop、有 warmup、報告 p99 而非平均（ch14 的 coordinated omission 是你 k6 經驗的主場）；（c）做一組量化對比（FP8 vs FP16）時，同時報告品質影響而不只報速度（ch07）——「我量了速度也量了品質代價」是區分工程師與跑分仔的分界線；（d）整個 harness 開源、可重現，這份 repo 同時是你開源貢獻的敲門磚（見下文）。

**專案④ 的深度升級**：基本版是「多模型部署起來」。升級版聚焦兩個生產級演示：（a）canary + graceful drain——用模擬叢集演示滾動更新時 in-flight streaming 請求一條不掉，並寫出 drain timeout 的計算依據（ch15 的數學）；（b）多租戶 token-based rate limiting——你寫過 rate limiter，這次計量單位換成 token（ch16），加一個 noisy neighbor 實驗（一個租戶塞長 context 請求，展示隔離前後其他租戶的 p95 變化）。這兩個演示直接對應系統設計面試的最後十五分鐘（見下文示範）。

四個專案的共同升級原則，就是 plan.md 第二條策略「每個專案往上一層做」：每個 repo 都要能回答三個問題——**它什麼時候會壞？我量到了什麼？我為什麼選 A 不選 B？**

## 作品敘事模板：把「降 RDS CPU 40%」搬到 GPU 上

你的成功敘事結構拆開是五段：**場景（規模）→ 量測（工具）→ 診斷（根因）→ 行動（具體優化）→ 數據（前後對比）**。原版：

> 在 500K+ 使用者、10K+ CCU 的遊戲後端，用 Clinic.js 與負載測試定位 DB 瓶頸（量測），發現鎖競爭與跨交易熱點（診斷），重排 SQL、拆分交易、批次化逐行更新（行動），峰值 RDS CPU 降 40%（數據）。

同一結構套到專案③，每段換上 GPU 世界的名詞（數字是示意，用你的實測值替換）：

> 在單張 L4 上服務 8B 模型（場景），用 vLLM `/metrics` ＋ DCGM ＋ 自寫的 k6 SSE 腳本建立 baseline：固定流量下 TTFT p95 2.8s、goodput 41%（量測，ch14）；診斷發現 KV cache 利用率長期 95%+ 觸發 preemption、recompute 進一步推高負載——典型的死亡螺旋前兆（診斷，ch05、ch06、ch13）；調低 `max-num-seqs` 換取 KV headroom、開 prefix caching、改用 FP8 KV cache（行動，ch05–ch08）；同 SLO 下 goodput 從 41% 提到 78%，等效於同樣流量少租 47% 的 GPU 時數，每月省 $X（數據，ch16）。

注意最後一句的形態變化：在後端世界你用 CPU% 收尾，在 GPU 世界**永遠用 goodput 和 $ 收尾**——因為這個職位存在的根本原因是推論帳單（見 ch01），會把優化翻譯成錢的人對 P&L 說話。

模板的反面檢查：如果你的專案敘事寫不出「診斷」那一段（只有「我調了參數變快了」），代表專案還停在「能動」層，回去補量測。

## 履歷改寫：三條真實條目的翻譯示範

履歷的目標讀者有兩個：ATS／招募者（掃關鍵字）與 hiring manager（找方法論證據）。改寫原則：**不發明經歷，只翻譯語言**——把每條後端成果的「可遷移內核」顯式化，並接上 AI infra 的詞彙表。以下拿你履歷的三條真實條目示範（履歷是英文，改寫保持英文，註解用中文）。

**第一條：RDS 優化。** 原文：

> Reduced RDS CPU by 40% during peak traffic via profiling-driven database optimization: restructured SQL ordering and decomposed transactions to minimize lock contention, reordered cross-transaction execution to reduce hotspots, and batched row-by-row updates.

改寫：

> Cut peak database CPU 40% for a 10K+ CCU game backend through a measure-diagnose-optimize loop (profiling, lock-contention analysis, transaction decomposition, batching) — the same methodology I now apply to GPU inference: benchmarked and tuned vLLM serving to raise goodput 41%→78% under a fixed TTFT SLO (see portfolio).

改了什麼：把「方法論」從動作清單中拎出來命名（measure-diagnose-optimize loop），然後**用一個分號把舊成果和新作品焊在一起**，讓讀 JD 的人在同一行看到 RDS 和 vLLM/goodput/TTFT/SLO 四個關鍵字。後半句的數字來自你的專案③，沒做完之前不要寫。

**第二條：多層 cache library。** 原文：

> Designed and documented a multi-tier cache library with pluggable data sources (in-memory → S3 → local) and graceful degradation across layers.

改寫：

> Designed a multi-tier caching library (in-memory → S3 → local) with pluggable backends and graceful degradation — structurally the same hierarchy problem as LLM KV-cache offloading (HBM → CPU RAM → NVMe → object storage), which I've since built hands-on experience with (vLLM prefix caching / tiered KV offloading benchmarks).

改了什麼：這條的同構性高到近乎作弊（見 ch05 的 offloading 分層），直接點破它。面試官看到這行會想問「那你說說 KV offloading」——這正是你準備好的主場。**設陷阱給面試官跳，是履歷的高階玩法。**

**第三條：WebSocket 即時系統。** 原文：

> Independently proposed and built a real-time notification system (WebSocket + Redis Pub/Sub) for message fan-out and multi-device synchronization, serving 500K+ registered users with ~3,200 concurrent connections.

改寫：

> Built a real-time message fan-out system (WebSocket + Redis Pub/Sub, 3,200 concurrent long-lived connections) — directly transferable to LLM token streaming: connection lifecycle, backpressure, and graceful drain of in-flight streams are the same engineering problems as SSE-based inference serving.

改了什麼：把「長連線生命週期」這個可遷移內核顯式化，並接上 SSE、in-flight stream、graceful drain 這些 ch12/ch15 的詞——它們正是推論平台 JD 的高頻關鍵字。

三條的共同模式：**前半句保留原始數字與規模（可信度錨點），後半句翻譯成目標領域語言（相關性訊號）**。整份履歷不需要每條都翻，挑三四條遷移度最高的（見 ch01 的技能遷移矩陣）就夠；翻太多反而稀釋。

## 系統設計面試完整示範：45 分鐘逐段走

題目：「**設計一個多租戶 LLM 推論平台：尖峰 5,000 並發對話、TTFT p95 < 1.5s。**」這是這個領域系統設計面試的標準題型，也是你在 ch12 動手做裡寫過設計文件的那道題的面試版。以下按時間軸走完 45 分鐘，每段標註面試官在聽什麼。數字沿用全書的基準（Llama-3.3-70B 級 GQA 模型、H100，價格為 2026 年年中快照）。

### 第 0–5 分鐘：需求澄清

你開口的第一句話不是畫圖，是提問：

> 「我先確認幾個會直接改變設計的參數。第一，5,000 並發是指同時掛著的對話 session，還是同時在生成的請求？第二，流量形態是人打字的 chat，還是有 agentic／批次流量混入？第三，模型是固定一個 70B 級的，還是多模型？租戶之間要硬隔離還是公平共享就好？最後，TTFT p95 1.5s 之外，有沒有 ITL 或吞吐的要求？」

假設面試官回答：5,000 是並發 session、以 chat 為主、單一 70B 開放權重模型加上幾個租戶的 LoRA 變體、公平共享即可、補充 ITL p95 < 60ms。你立刻把澄清變成設計輸入：

> 「那我用三個工作假設：chat 流量的 duty cycle 約 10%——人大部分時間在讀和打字，所以 5,000 session 對應約 **500 條同時活躍的生成串流**；平均 context 4k tokens、單輪輸出約 400 tokens；多輪對話佔大宗，這代表 prefix caching 的命中率會是整個容量模型的槓桿，我後面會算給你看。」

> **面試官在這裡想聽什麼**：你會不會區分「session 並發」與「串流並發」（差 10 倍，直接決定卡數）；你有沒有意識到流量形態（chat vs agentic）改變整個快取與路由設計（見 ch17）。直接開始畫框圖的候選人，在這 5 分鐘就被分到下一個級距去了。

### 第 5–15 分鐘：SLO 與容量數學

這 10 分鐘是整場面試的勝負手。你在白板上算，邊算邊講：

**Decode 容量（記憶體帳，ch03 的公式）**：

```
70B GQA：每 token KV ≈ 320 KB（FP16）
一條 4k context 對話 ≈ 4,096 × 320 KB ≈ 1.3 GB
模型權重 FP8 ≈ 70 GB → 單卡放不下 KV，用 TP4（ch09）
每組 TP4：320 GB HBM − 70 GB 權重 − ~25 GB 緩衝 ≈ 225 GB 給 KV
        → 上限 ~175 條活躍對話/組
500 條 ÷ 125 條/組（取 ~70% KV 利用率、留 preemption headroom，ch06/ch13）
        → 4 組 TP4 = 16 張 H100
```

**ITL 驗證（頻寬帳，ch02 的 roofline 直覺）**：

```
每個 decode step 讀：70 GB 權重 + 125 × 1.3 GB KV ≈ 232 GB
TP4 聚合頻寬 ≈ 13.4 TB/s → ~17 ms/step ✓（< 60 ms 預算）
```

**Prefill 容量（這裡放你的亮點）**：

> 「請求到達率：500 條串流、每輪 400 tokens、25 tok/s → 一輪 16 秒，約 **31 輪/秒**。如果每輪都全量 prefill 4k context，需求是 127k prefill tok/s——粗估要再加十幾張卡，而且 prefill 會干擾 decode 的 ITL（ch06）。但 chat 是多輪對話：前幾輪的 KV 已經在快取裡，每輪真正新增的只有幾百個 token。假設 prefix cache 命中率 80%（多輪流量下保守，ch05），有效 prefill 需求降到約 30–35k tok/s，用 chunked prefill 的 token budget 混進 4 組 decode batch 就吃得下。**prefix cache hit rate 是這個設計裡槓桿最大的單一數字**——它決定我要 16 張卡還是 40 張卡，所以後面的路由設計會圍繞保護它來做。」

**結論**：4 組 TP4 承載穩態，加 1 組做尖峰 headroom 與滾動更新冗餘（N+1，ch13/ch15）→ **20 張 H100**。TTFT 分解驗證：cache 命中時增量 prefill 約 20–50ms、未命中全量約 200–300ms，p95 1.5s 的預算大頭留給排隊——這就是 admission control 要守住的東西。

> **面試官在這裡想聽什麼**：（1）你先算記憶體再算算力——證明你懂「LLM serving 是 memory 的生意」（主軸一）；（2）每個數字有來源、有交叉驗證（容量帳算完用頻寬帳驗 ITL）；（3）你主動暴露了 prefill/decode 干擾與快取槓桿這兩個非顯而易見的點。答不出容量數學的候選人講再漂亮的架構圖都是空中樓閣，這是 ch13 整章存在的理由。

### 第 15–25 分鐘：架構圖

現在才畫圖（ch12 的參考架構）：

```
client ──HTTPS/SSE──► API Gateway ──► Inference Router ──► Engine Fleet
權重儲存（S3 + 節點 NVMe cache）──cold start 載入──► Engine Fleet
Engine Fleet ──/metrics + DCGM──► Observability
```

- **API Gateway**：認證、計量、token-based 限流、admission control（ch12/ch16）
- **Inference Router**：Gateway API Inference Extension——InferencePool + EPP prefix-aware 路由（ch10/ch12）
- **Engine Fleet**：5 組 TP4 vLLM，4 active + 1 headroom（ch08/ch09）
- **Observability**：/metrics + DCGM（ch14）；權重儲存的 cold start 路徑見 ch12

逐個箭頭講清楚為什麼：

- **Gateway 層**：OpenAI-compatible API（de facto 標準）；限流單位是 token 不是 RPS——請求成本變異上千倍，RPS 限流毫無意義（ch16）；admission control 放在最前面，佇列崩潰的動力學決定了它不能放在引擎旁邊（ch13/ch15）。
- **Router 層**：「L7 round-robin 對 LLM 流量不夠——這是有狀態的負載均衡，KV cache 命中與否讓同一個請求的成本差一個數量級。我會用 Gateway API Inference Extension 的 InferencePool + endpoint picker 做 prefix-aware 路由（ch10/ch12），scoring 在 cache 命中與負載均衡之間拉扯，純命中優先會把熱租戶打爆單一副本。」
- **LoRA 多租戶**：幾個租戶的 LoRA 變體用 multi-LoRA serving 掛在同一個 base 模型池上，而不是每租戶一個獨立部署（ch12）——這是這題「多租戶」的記憶體經濟學正解。
- **平台選型**：「自組 vs 採用：這個規模我會基於 llm-d 或 KServe 的 LLMInferenceService 起步而不是裸寫 operator——它們把 InferencePool、P/D、KV 路由都做成 well-lit path 了（ch12，2026-06 的生態狀態）。」

> **面試官在這裡想聽什麼**：每個框不是名詞而是決策——「為什麼這裡不能用普通 LB」「為什麼限流在 gateway 而不是引擎」。另外聽你的選型誠實度：知道站在 llm-d/KServe 上而不是炫技自建，是 staff 訊號不是偷懶（ch12 的自組 vs 採用判斷）。

### 第 25–35 分鐘：深掘兩處

面試官會挑一兩處往下鑽，你也可以主動選。建議選一個「引擎深度」加一個「平台深度」，展示縱深：

**深掘一：KV cache 管理（ch05）。** 「剛才說 prefix cache 是最大槓桿，展開講保護它的三層設計：（1）引擎內 PagedAttention 的 block 重用——同 system prompt 的租戶共享前綴 block；（2）路由層 prefix-aware——同一對話的後續輪次必須回到同一副本，否則命中率歸零，這是 session affinity 的高賭注版本；（3）容量壓力下的 eviction 順序與多層 offloading（HBM→CPU RAM→NVMe）——掉到下層的代價要和重算 prefill 比價（ch05/ch10 的 crossover 數學）。觀測上我會把 prefix cache hit rate 和 KV utilization 放在 dashboard 第一排（ch14），hit rate 緩慢下滑是路由壞掉的早期訊號（ch15）。」

**深掘二：autoscaling（ch13）。** 「訊號不用 GPU utilization——SM 占用不等於有效工作，而且它是落後指標。我用的階層：佇列深度（最靈敏）、KV cache 利用率、SLO burn rate，KEDA 接 external metrics 執行。但真正的約束是 scale-up 延遲：拉一個新的 TP4 副本要拉 70GB 權重加引擎初始化，冷啟動以分鐘計，而 chat 尖峰以秒計來——所以靠的是 headroom 數學加 diurnal pattern 的預測式擴縮（我在遊戲後端為活動尖峰做過一樣的事），而不是反應式擴縮。Scale-to-zero 對這個 SLO 直接出局（ch12/ch13）。」

> **面試官在這裡想聽什麼**：深度的「梯度」——你能從平台層一路講到 block table，而且每層都知道觀測指標。第二個深掘裡「冷啟動分鐘級 vs 流量秒級」這句話是這個領域 autoscaling 的第一性約束，講不出它的人會設計出永遠慢一拍的系統。

### 第 35–40 分鐘：故障與運維

主動講，不要等問（ch15 整章的濃縮）：

> 「三個我最擔心的故障。第一，**KV 壓力死亡螺旋**：負載逼近容量 → preemption → recompute 推高負載的正回饋，防禦是 admission control 前置加 KV utilization 告警在 85% 而不是 99%。第二，**graceful drain**：streaming 請求可以長達分鐘級，drain timeout 要照 p99.9 請求時長設計，preStop 停收新請求、等 in-flight 排空——所以這個平台的滾動更新一輪以小時計，部署窗口要排進容量規劃。第三，**品質迴歸在 5xx 看不到**：模型權重、引擎版本、量化配置的 canary 不能只看錯誤率，要有 eval-based gate——模型變笨不會報錯。Runbook 我會先寫兩本：TTFT p99 突然 ×3、單 node NCCL timeout。」

> **面試官在這裡想聽什麼**：你有沒有運維過真東西的氣味。「deploy 以小時計」「模型變笨不報錯」這類細節騙不了人——它們不在任何教程的 happy path 裡。你的 10K CCU 維運經驗在這一段是真實優勢，把它講出來。

### 第 40–45 分鐘：成本收尾

> 「算一下這套設計的單位經濟學（ch16）：20 × H100，neocloud 級距約 $2.75/hr/卡（2026 年年中快照）→ $55/hr ≈ **$40k/月**。尖峰吞吐 500 串流 × 25 tok/s = 12.5k output tok/s ≈ 45M tok/hr，即尖峰時 **$1.2/M output tokens**；按日均利用率 50% 算，實際約 $2.4/M。誠實說：這個量級用第三方 API 託管開放權重模型可能更便宜——自建的辯護理由是多租戶 LoRA、資料隱私與流量成長曲線，如果這三個都不成立，正確答案是先不要自建（ch16 的 build vs buy crossover）。如果要降成本，槓桿排序：把利用率提上去 > 提高 cache 命中 > FP8/量化 > 換硬體代際。」

> **面試官在這裡想聽什麼**：兩件事。第一，你把整場面試的數字串成了 $/Mtok——證明容量數學不是表演，是會計。第二，那句「這個規模可能不該自建」——敢對題目本身提出經濟學質疑，並給出成立條件，是資深與 staff 的分水嶺。沒有面試官會因為你誠實扣分；他們天天在開的會就是這個會。

### 賽後檢核表

錄音自講一遍後對照：六段都覆蓋了嗎？容量數學算對了嗎（KV/token → 串流數/組 → 卡數）？每個架構決策都有「為什麼不用替代方案」嗎？有沒有主動講故障？最後有沒有落到 $？任何一段超過 12 分鐘就是配速失敗——面試和 drain timeout 一樣，預算要照最壞情況設計。

## 面試題庫：30 題按輪次

各章「自我檢核」的精華彙整。每題後標出處章節；答不出來就回去重讀那章——這份清單同時是你的面試前複習地圖。

**Screening／電話初篩（答案要能在 90 秒內講完）**

1. 為什麼 decode 是 memory-bound？用數字證明一次（ch02、ch03）
2. KV cache 在解什麼問題？一條 32k context 對話在 70B GQA 模型上吃多少記憶體？（ch03）
3. Continuous batching 和 dynamic batching 差在哪？它為什麼是「推論引擎快」的核心答案？（ch06）
4. TTFT 和 ITL 各由什麼決定？為什麼一個數字描述不了 LLM 延遲？（ch03、ch14）
5. PagedAttention 在解什麼問題？跟 OS virtual memory 的類比成立在哪裡？（ch05）
6. FP8／INT4 量化的收益與風險各是什麼？什麼任務先壞？（ch07）
7. 為什麼 K8s 預設不能把一張 GPU 分給兩個 Pod？業界怎麼繞、各有什麼代價？（ch11）
8. Prefix caching 對什麼 workload 槓桿最大？為什麼 agentic 流量讓它從優化變成產品核心？（ch05、ch17）

**深度技術輪（會被連環追問三層）**

9. Chunked prefill 解什麼問題？token budget 怎麼定？代價是什麼？（ch06）
10. Preemption 什麼時候發生？recompute vs swap 怎麼選？它如何引發死亡螺旋？（ch06、ch13）
11. TP 為什麼通常不出節點？把每層的通訊量算給我看（ch09）
12. P/D 分離的動機是什麼？什麼規模以下不要碰？（ch10）
13. KV-aware routing 的 scoring 怎麼設計？cache 命中與負載均衡怎麼拉扯？（ch10）
14. Speculative decoding 為什麼在高 batch 下收益遞減甚至為負？（ch07）
15. MoE 為什麼改變 serving 經濟學？wide-EP 部署在解什麼問題？（ch03、ch09）
16. DRA 解了 device plugin 的什麼痛？（ch11）
17. Cold start 從 pod 排程到首 token，每段的時間量級與優化手段？（ch12）
18. GPU utilization 為什麼是誤導性指標？你用什麼代替？（ch13、ch14）

**系統設計輪**

19. 設計多租戶 LLM 推論平台（本章示範題，反覆練到肌肉記憶）
20. 為 LLM 服務設計 autoscaling：訊號、headroom 數學、scale-to-zero 的判斷（ch13）
21. 為 agentic 流量設計快取與路由層（ch05、ch10、ch17）
22. 設計一套不騙自己的 benchmark 方法論（ch14）
23. 設計模型權重的 canary 發布——品質迴歸在 5xx 看不到，怎麼辦？（ch15）
24. 你的產品每月 50B tokens，build vs buy 怎麼決策？算給我看（ch16）

**行為輪**

25. 講一個你用數據證明的效能優化（你的 RDS 故事，套本章敘事模板，60 秒版與 5 分鐘版各準備一個）
26. 講一次 production incident：你怎麼定位、怎麼止血、事後改了什麼
27. 為什麼轉 AI infra？（用 plan.md 的定位句：不是想轉 AI 的後端工程師，而是把同一套效能工程方法複製到 GPU 推論上的人）
28. 你怎麼進入一個全新領域？（你手上就有證據：模擬叢集、租卡實驗、本書的學習路徑）
29. 講一次你和團隊的技術決策衝突與收場
30. 「你有什麼想問我們的？」（這題是送分題也是送命題——用下面 JD 解碼器的問題清單）

## 開源貢獻策略：面積、門檻與第一個 PR

開源貢獻在這個領域的求職權重高於一般後端——因為整個推論棧就建在這幾個專案上，你的 PR 紀錄是 hiring manager 可以直接 review 的工作樣本。但策略要對：**目標不是「貢獻過 vLLM」這個名頭，是一段可以在面試裡講的、有來有回的工程協作敘事。**

| 專案 | 主語言 | 貢獻面積 | 門檻 | 對你的契合度（2026-06 評估） |
|---|---|---|---|---|
| **vLLM** | Python（核心）/ CUDA（kernel） | 巨大：單一 release 200+ 貢獻者；docs、model support、benchmark、CI、kernel 全光譜 | 中高：專案極熱門，good-first-issue 競爭激烈（我查證時 open 的僅十餘個）；kernel 區門檻最高 | 中：benchmark／docs／metrics 區與你重疊；先從重現 bug 與補測試切入 |
| **llm-d** | **Go**（scheduler/路由）+ Python | 中等但成長快：inference scheduler 的 scorer plugin 架構是顯式的擴充點；SIG 制、雙週 contributor standup | 低中：社群年輕、維護者可及性高，曝光/競爭比最好 | **高**：K8s + Go + 排程直覺正是你的主場（ch04 的 Go 橋接在此兌現） |
| **llm-d-inference-sim** | Go | 小而精：模擬器功能、指標仿真 | **最低**：不需要 GPU，跑在你的 M1 上；你在專案①④天天用它 | **最高**：用的時候踩到的坑就是 issue，修了就是 PR——最自然的切入路徑 |
| **SGLang** | Python | 大：迭代極快（2–3 週一版）導致文件與 cookbook 長期落後——這就是貢獻面 | 中：sgl-cookbook 有顯式的社群貢獻路線圖與 good-first-issue | 中：適合 docs/benchmark 切入；核心排程區節奏快、競爭烈 |
| **KServe** | Go（controller）+ Python | 中：CNCF incubating（2025 起）、治理正式；LLMInferenceService 還是 alpha API，文件與測試缺口明顯 | 中：CNCF 流程（DCO、雙週 working group）較重但透明 | 高：controller/reconcile 是你 ch04/ch11 練過的形態；alpha API 周邊是肥沃帶 |

（各專案的社群入口：vLLM 有 developer Slack 與雙週 office hours；llm-d 有 Slack、SIG 與雙週 standup；KServe 走 CNCF Slack 與雙週 working group meeting。截至 2026-06 查證，連結見延伸閱讀。）

**從文件與測試切入的路徑，具體展開**：（1）先當使用者——你的旗艦專案就是使用現場，把踩到的文件錯誤、過期參數、缺失的錯誤訊息記下來；（2）挑一個去 issue 區搜，沒人報就開 issue，**先在 issue 裡溝通再動手**——直接丟 PR 給沒共識的改動是新貢獻者最常見的浪費；（3）第一個 PR 刻意選小：一頁文件、一個測試、一個錯誤訊息改善，目標是走完流程而不是技驚四座；（4）PR 裡展示你的量測習慣——「我在 X 環境重現、改後行為是 Y」比「我覺得這樣比較好」過審快得多。

**一個 PR 的完整生命週期預期**（以 vLLM 為例，其 contributing guide 明文的節奏）：提交後分配 reviewer，約每 2–3 天會有狀態更新，7 天沒人理可以禮貌 ping；加上 CI（大專案的 GPU CI 常需 maintainer 觸發）與來回修改，**第一個 PR 從動手到 merge 預期 2–6 週**。心理建設：PR 被晾著不是針對你，maintainer 的 review 佇列跟你設計的系統一樣會塞——你懂佇列。

優先序建議：**llm-d-inference-sim 起手（零硬體成本、Go、低競爭）→ llm-d scheduler 的 scorer/文件 → vLLM 的 benchmark/docs 區**。一個 merged PR ＋ 一段有來有回的 review 經歷，就達到 plan.md 模組五的考核標準；三個以上不同面積的貢獻，在履歷上就是獨立的一條 bullet。

## JD 解碼器：同名職缺的三種實質

ch01 的職位光譜按「職稱」拆，這裡按「公司類型」拆——同一個 "Inference Engineer" 在三種公司是三份不同的工作：

| | Model lab（前沿實驗室） | 產品公司（LLM 進產品） | Neocloud／GPU 雲 |
|---|---|---|---|
| 實質工作 | 引擎與 kernel 級效能：attention 變體、編譯、自家模型的極限壓榨 | 平台與 serving：用 vLLM/llm-d 組平台、SLO、成本、多租戶 | 機隊維運：叢集供裝、IB 網路、利用率經濟學、賣 GPU 給別人 |
| JD 關鍵字 | CUDA、kernels、torch.compile、MFU | vLLM、K8s、SLO、$/token、observability | InfiniBand、DCGM、fleet、provisioning、SLURM/K8s |
| 對應本書 | ch02–ch07 | ch08、ch11–ch16 | ch02、ch09、ch11、ch15 |
| 你的距離 | 最遠（kernel 鏈從零） | **最近（這本書就是為它寫的）** | 中（維運遷移、網路硬體要補） |

**紅旗清單**：JD 只有 LangChain 類應用框架卻掛 infra 職稱（應用層職位穿 infra 外套）；「負責訓練＋推論＋資料＋平台」全包（沒有 infra 團隊，你會是唯一的人）；宣稱生產規模卻不提任何 SLO／on-call／指標詞彙（大概率還沒有生產流量）；要求清單裡 CUDA kernel 與 Terraform 並列且都「必須精通」（JD 是許願池，團隊自己也不知道要找誰）。

**綠旗清單**：寫得出具體引擎與指標（vLLM、TTFT、goodput、DCGM）；提到 GPU 機隊規模或推論帳單量級；有獨立的 infra/platform 團隊；面試流程裡有真的系統設計輪而不只 LeetCode。

**該問面試官的問題**（每一題都同時在收集資訊和展示深度）：

1. 「你們的 GPU 機隊多大、怎麼取得的（on-demand／reserved／自建）？」——規模決定你做的是 ch08 還是 ch10 的工作。
2. 「推論的 SLO 是誰定的、誰背？現在的 TTFT p95 和 goodput 大概在哪？」——有沒有數字文化，一問便知。
3. 「模型或引擎版本更新怎麼發布？有 eval gate 嗎？」——測他們的 ch15 成熟度。
4. 「Prefix cache 命中率現在多少？誰在看這個數字？」——這題會讓懂的面試官眼睛一亮，不懂的支吾——兩種反應都是你要的資訊。
5. 「on-call 輪值怎麼排？最近一次推論相關的 incident 是什麼？」——工作品質的真相都在 incident 裡。
6. 「未來一年是自建更多還是往 API/託管收斂？」——測這個職位本身的耐久性（ch16 的 build vs buy 會反過來吃掉職位）。

## 持續更新系統：每週 30 分鐘的維護迴圈

這個領域的工具層以月為單位漂移（vLLM 每 2–3 週一版），但你不需要追逐每個版本——你需要一個固定頻寬的維護迴圈，對應 plan.md 的 L3 迴圈。**追的層級**：機制與架構走向（耐久）優先於參數與版本號（速朽，見 ch17 的能力耐久性矩陣）。

**該追的源頭清單（2026-06 時點）**：

| 源頭 | 頻率 | 為什麼追 |
|---|---|---|
| vLLM release notes ＋ blog（vllm.ai/blog） | 每版掃標題 | 引擎層事實上的風向標；office hours（雙週，有 YouTube 錄影）適合聽設計討論 |
| llm-d blog ＋ release notes | 月 | K8s 原生推論平台的走向；well-lit paths 文章本身就是架構教材 |
| SGLang releases（GitHub） | 月 | 與 vLLM 的功能趨同/分歧是判斷「什麼是共識」的訊號 |
| Kubernetes blog（DRA／WG Serving 相關）＋ KServe/CNCF blog | 季 | 資源模型與平台原語的演進（ch11/ch12 的地基） |
| NVIDIA developer blog（Dynamo、NIXL、硬體） | 季 | 硬體路線圖與官方棧的方向 |
| a16z × OpenRouter「State of AI」類流量研究 | 年 | 需求面（agentic/reasoning 流量結構）的最佳公開數據（ch17） |
| 會議錄影：KubeCon（Cloud Native AI 軌）、GTC、Ray Summit、PyTorch Conference、vLLM meetup | 半年挑著看 | 生產案例濃度最高的來源；演講者名單也是求職的公司名單 |

**迴圈設計（每週 30 分鐘，行事曆上鎖死）**：10 分鐘掃 vLLM／llm-d 的 release 標題，只記「出現了什麼新機制詞」；10 分鐘精讀一篇上表的文章；10 分鐘更新自己的 cheatsheet 或實驗筆記（附錄C 是你的起點）。每月加碼一次：把專案①的模擬叢集重跑一遍，看哪個工具的 API 漂移了——壞掉的 lab 就是最誠實的 changelog。每季對照一次 landscape 級事實（價格、版本、專案狀態），標記自己知識的「最後查證時點」——你在本書裡到處看到的（2026-06）標記，就是這個習慣的示範。

## 故障模式與防禦

求職系統的故障目錄，格式照舊：

| 故障模式 | 症狀 | 根因 | 防禦 |
|---|---|---|---|
| 作品集「能動就停」 | 面試第二層追問就垮（「為什麼有效？」答不出） | 專案缺診斷層，只有操作層 | 每個專案補齊「會怎麼壞／量到什麼／為什麼選 A」三問（plan.md 原則二） |
| 數字失憶 | 「我優化過但忘了具體數字」 | 沒有實驗日誌 | README 前三行就是數字；實驗當天寫 log，數字進履歷前可重現 |
| 教程式作品集 | 面試官禮貌地換話題 | 跟著別人 README 跑一遍沒有自己的發現 | 每個專案至少一個對照組或反直覺結果（如：CPU 訊號 autoscaling 的失敗演示） |
| 系統設計背稿 | 第一個 follow-up 就偏離劇本後崩潰 | 背架構圖不會算數字 | 本章示範的每個箭頭都要能展開成計算；換三組參數自己重算 |
| 開源 PR 石沉大海 | PR 開了兩個月沒人理，挫折棄坑 | 沒先溝通、選錯面積、撞上 maintainer 佇列 | 先 issue 後 PR；挑活躍區（看最近 merge 紀錄）；7 天後禮貌 ping；同時開兩條線不單點依賴 |
| 履歷被 ATS silent drop | 投遞無回音 | 關鍵字錯頻：滿頁 NestJS 沒有 K8s/vLLM/SLO | 用本章翻譯模板對齊 JD 語言；但絕不謊報——關鍵字會在面試被逐一驗貨 |
| 知識過期 | 面試引用了已被移除的機制（如 vLLM V0 時代的參數） | 學習快照沒有維護迴圈 | 每週 30 分鐘迴圈；講機制不講版本號，版本相關陳述加時點 |
| 無限備戰 | 「再學完 X 就投」循環半年 | 把求職當 waterfall 不當迭代 | 邊投邊學：面試是最高密度的量測，每場面試的失分點就是下週的學習 backlog |

## 動手做

1. **[紙上推演] 履歷翻譯**：用本章模板改寫你履歷的三條 bullet。成功標準：每條保留原始數字錨點、出現至少兩個目標領域關鍵字、且每個關鍵字你都能被追問三層不破。
2. **[紙上推演＋錄音] 模擬面試**：計時 45 分鐘自講本章的系統設計題（換一組參數：例如 2k 並發、ITL p95 < 40ms、agentic 流量為主），錄音後對照賽後檢核表逐段打分。成功標準：六段全覆蓋、容量數學重算正確、無任何一段超過 12 分鐘。做完再做一次 ch12 動手做的那份設計文件對照——它就是這題的書面版。
3. **[M1] 第一個開源迴圈**：在 llm-d-inference-sim 或你常用專案的 docs 區找一個真實的小問題，走完 issue → 溝通 → PR → review 的完整生命週期。成功標準：不是 merge（那不完全由你控制），而是收到至少一輪 maintainer 的實質回饋並完成修改。

## 自我檢核

1. 不看書，把 5k 並發題的容量數學從一張白紙算到卡數與 $/Mtok，數字與本章誤差在 2 倍以內？
2. 你的四個旗艦專案，每個都能在 90 秒內講出「問題→量測→診斷→優化→數字」，且 README 前三行有數字？
3. 面試官問「為什麼不用 GPU utilization 當 autoscaling 訊號」，你能給出三層理由並說出替代訊號階層？
4. 你能說出 vLLM 與 llm-d 各自的貢獻切入面積、以及你下一個 PR 的具體候選？
5. 給你一份 JD，5 分鐘內判斷它屬於三種公司類型的哪種、列出兩面紅旗或綠旗、並選好三個要問面試官的問題？
6. 「講一個你用數據證明的優化」——你的 60 秒版本一氣呵成嗎？最後一句落在方法論而不是數字本身嗎？
7. 你的每週 30 分鐘維護迴圈在行事曆上了嗎？說出上週 vLLM 或 llm-d release notes 裡的一個新機制詞。

## 延伸閱讀

- vLLM Contributing Guide（https://docs.vllm.ai/en/latest/contributing/）— PR 生命週期、review 節奏（2–3 天更新、7 天可 ping）的官方說法，投第一個 PR 前必讀。
- vLLM Slack（https://slack.vllm.ai）與 vLLM Events（https://vllm.ai/events）— developer Slack 是貢獻協調的主場；meetup 與 office hours 是聽核心開發者討論設計的最低成本管道。
- llm-d 專案與社群（https://github.com/llm-d/llm-d 、https://llm-d.ai/blog）— CONTRIBUTING、SIG 與雙週 contributor standup 的入口；blog 的 well-lit paths 系列本身是平台架構教材。
- KServe Community（https://github.com/kserve/community）— CNCF 式治理與雙週 working group 的運作方式，Go controller 貢獻者的起點。
- SGLang（https://github.com/sgl-project/sglang）— release notes 是觀察引擎層競爭格局的另一隻眼；其 cookbook 子專案有面向新貢獻者的任務路線圖。
- a16z × OpenRouter「State of AI: 100 Trillion Token Study」（https://a16z.com/state-of-ai/）— 推論需求面的最佳公開數據，面試聊產業趨勢時的可靠彈藥（ch17 詳用）。
- kubernetes-sigs/inference-perf（https://github.com/kubernetes-sigs/inference-perf）— 標準化 benchmark 工具；給你的專案③④ 一個社群認可的量測基準，本身也是貢獻面積。
- levels.fyi（https://www.levels.fyi）— 薪資數字會過期，談 offer 前查當下值；用結構（ch01 的稀缺度分析）理解數字，不要反過來。
