# ch13 — Autoscaling 與容量工程：對的訊號、headroom 數學、把並發換算成卡數

> **本章解決什麼問題**：ch12 把平台架構組裝起來了，但留下兩個錢與 SLO 的問題：這個 fleet 應該有幾個 replica？流量變化時誰來增減它？CPU-based HPA 的肌肉記憶在這裡會直接傷害你——訊號全錯、時間尺度全錯。本章先拆解為什麼舊訊號失效、什麼是對的訊號階層，再給執行機制（KEDA/KPA）、headroom 數學與死亡螺旋防禦，最後用全書最重要的 worked example 之一走完一次完整容量規劃：從單卡 benchmark 推到卡數與月成本。指標的採集實作在 ch14，故障處理細節在 ch15，成本工程的完整版在 ch16。

## 從你已知的出發

你在遊戲後端做過這件事的上一個版本：開服前估 CCU、壓測單台 c5.xlarge 能扛多少 RPS、除一下加 buffer、掛上 CPU 60% 的 target tracking autoscaling，活動前夜手動先拉一倍容量。這套方法論的骨架——**流量模型 → 單機基準 → 除法 → headroom → 驗證**——在 LLM serving 一個字都不用改。要改的是三個物理常數：

1. **請求成本的同質性假設崩潰了**。你的遊戲 API，每個請求的 CPU 成本大致同量級，所以「RPS ≈ 負載」近似成立，CPU% 是負載的忠實代理。LLM 請求之間成本差四個數量級（10 token 問答 vs 100k token 文件分析），RPS 與負載之間只剩雜訊般的相關性。
2. **Scale-out 從分鐘級變成十分鐘級**。c5.xlarge 從觸發到進 ALB 大約 2–3 分鐘；一個 vLLM pod 從排程到能服務流量要載入幾十 GB 權重、做 CUDA graph capture 與 warmup（解剖見 ch12），有現成 GPU 節點時 3–8 分鐘，要新開節點時 10–20 分鐘起跳——而且 GPU 可能根本沒貨。流量尖峰還是秒級的。這個不對稱是本章一半內容的根源。
3. **資源不可超賣**。CPU 世界你可以 requests 寫低一點賭統計多工；GPU 是整數資源、KV cache 是硬容量（ch11）。超過容量的那一刻不是「大家慢一點」，是 preemption 與重算（ch06）——退化是懸崖式的。

但你有一個直覺在這裡完全保值，而且是本章的主角：**佇列先於資源指標惡化**。你在遊戲後端見過這個模式——大型活動開搶的瞬間，最先告警的不是 CPU，是 gateway 的等待佇列與 p95;CPU 還在 60% 的時候玩家已經在排隊了。你在 SQS pipeline 上也靠 queue depth 而不是 consumer CPU 來判斷要不要加 worker。LLM serving 把這個直覺從「經驗法則」升級成「唯一正確答案」：引擎內部就是一個 scheduler 加一條 waiting 佇列（ch06），佇列深度就是負載本身。

## 為什麼 CPU 與 RPS 訊號全錯

把三個常見的錯誤訊號逐一處決，並解釋屍檢結果。

### CPU%：量錯了器官

vLLM pod 的 CPU 在做 tokenization、HTTP/SSE 處理、排程邏輯——全是配角。GPU 打到天花板時 CPU 可能只有 20%；反過來，一波長 prompt 的 tokenization 也能把 CPU 推高而 GPU 還很空。對 CPU 做 HPA，等於用司機的心跳數決定要不要加開公車。

### RPS：變異數毀掉一切

對 RPS 擴縮隱含的假設是「每個請求成本近似相等」。LLM 流量的單請求成本分布跨 4 個數量級，而且成本藏在 body 裡、一半（輸出長度）連 body 都看不出來（ch12 講過同一件事對 load balancing 的傷害）。同樣 50 RPS，可能是輕鬆寫意，也可能是死亡螺旋的入口。用 RPS 做容量決策，相當於你的遊戲後端把「一次撈排行榜」和「一次全服結算」當同一種請求計數。

### GPU utilization：最危險的一個，因為它看起來最對

`nvidia-smi` 的 GPU-Util（DCGM 的 `DCGM_FI_DEV_GPU_UTIL`）語意是「取樣窗內**至少有一個 kernel 在跑**的時間比例」。一個 batch size = 1 的 decode 迴圈——GPU 在做它理論吞吐 1% 的有效工作——也會顯示 90%+ 的 utilization，因為 kernel 確實一直在跑，只是每次都在等 HBM 把權重搬進來（memory-bound，ch02/ch03）。它量的是「有沒有在動」，不是「做了多少有效工作」。SM activity 與 utilization 的完整辨析在 ch14；本章你只需要記住結論：**GPU util 接近 100% 是常態而非告警，它對 autoscaling 沒有資訊量**。

三個訊號的共同死因：它們都是**資源視角**的指標，而 LLM serving 的退化最先出現在**佇列視角**——請求開始排隊、TTFT 開始爬，此時所有資源指標都還「正常」。等資源指標異常時，使用者已經在受苦了。這正是你在遊戲後端親眼見過的模式，只是這裡懸崖更陡：latency-throughput 曲線在膝點(knee)之前近乎平坦，過了膝點佇列等待呈超線性爆炸（排隊理論的曲棍球桿，你懂的），而 LLM 還多一道 KV 容量天花板，撞上去直接觸發 preemption（後述死亡螺旋）。

## 正確的訊號階層

從領先到落後排列。指標名稱以 vLLM V1 的 `/metrics` 為例（2026-06；完整指標分類學見 ch14）：

| 階層 | 訊號 | vLLM 指標 | 類型 | 它告訴你什麼 | 判讀陷阱 |
|---|---|---|---|---|---|
| 1（最領先） | **佇列深度** | `vllm:num_requests_waiting` | gauge | 需求已超過當下消化能力；佇列形成於 SLO 惡化之前 | 為 0 不代表健康——gateway 的 admission control 可能正在上游丟棄流量（ch12）；要看 fleet 的 max 而非 avg（後述） |
| 2 | **KV cache 利用率** | `vllm:kv_cache_usage_perc` | gauge | 記憶體軸的飽和度；逼近 1.0 = preemption 風險（ch05/ch06） | 開了 prefix caching 後長期偏高是**正常的**（快取塊可回收不會主動釋放），必須搭配 preemption 計數一起判讀 |
| 3 | **Batch 占用** | `vllm:num_requests_running` ÷ `max-num-seqs` | gauge | 併發槽位的飽和度；貼著上限表示新請求只能排隊 | 上限是你自己設的（ch06/ch08），先確認它設得有道理 |
| 4 | **排隊時間** | `vllm:request_queue_time_seconds` | histogram | TTFT 惡化的歸因證據（排隊 vs 算得慢） | 落後於佇列深度，適合歸因不適合觸發 |
| 5（最落後） | **SLO burn** | `vllm:time_to_first_token_seconds`、`vllm:inter_token_latency_seconds` | histogram | 使用者體驗的 ground truth；burn rate 告警設計見 ch14 | 它惡化時你已經遲到了——當 gate（驗證擴縮有效）而非 trigger |
| 輔助 | **Preemption 速率** | `vllm:num_preemptions_total` | counter | KV 超賣的直接證據；死亡螺旋的領先指標 | 健康系統應接近 0；rate > 0 持續數分鐘就要介入 |

設計原則：**用領先指標觸發擴容，用落後指標驗證擴容有效**。佇列深度是主觸發（語意最乾淨：「有 N 個使用者在排隊」），KV 利用率是第二觸發（攔截長 context 流量造成的記憶體軸飽和——佇列可能還短但 KV 快炸了），TTFT/ITL 的 SLO burn rate 是告警與覆核，不直接驅動 HPA——拿落後指標觸發擴縮,等於看著後照鏡開車。

聚合方式有一個容易踩的坑：對 fleet 取 `avg()` 會被冷熱不均掩蓋。在 KV-aware routing 之下（ch10），replica 之間負載**故意**不均（cache 命中優先），一個 replica 排隊爆了、平均值仍可能很好看。擴縮觸發用 `sum()`（總排隊人數，配合 per-replica threshold）或 `max()`，per-replica 的不均問題交給路由層解決。

## 執行機制：HPA、KEDA、Knative KPA

訊號選對之後，執行機制反而是三者中最商品化的一環。

### HPA + custom/external metrics

原生 HPA 只認 CPU/memory，要吃 Prometheus 指標得透過 prometheus-adapter 把指標翻譯成 custom metrics API。能用，但 adapter 的 ConfigMap DSL 難寫難查錯、全叢集只能裝一個 adapter、規則是中心化管理——平台團隊的負擔。除非你已有現成 adapter 基礎設施，否則 2026 年的務實答案是 KEDA。

### KEDA：LLM autoscaling 的預設答案

KEDA（本書寫作時 v2.20，2026-05）本質是「external metrics 的發行版」：70+ 種 scaler、每個 ScaledObject 自帶查詢邏輯（去中心化）、支援 scale-to-zero、有 fallback 機制。底下還是生成一個 HPA，所以你的 HPA 知識全部保值。一份可以直接改用的 ScaledObject（示意，label 依你的部署調整）：

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: vllm-chat-70b
  namespace: inference
spec:
  scaleTargetRef:
    name: vllm-chat-70b          # 引擎 Deployment（一個 replica = 一個 TP2 引擎，見 worked example）
  minReplicaCount: 11             # 基線容量：headroom 數學的輸出，不是拍腦袋
  maxReplicaCount: 18             # 預算上限 ∧ 叢集實際租得到的卡
  pollingInterval: 15             # 秒
  cooldownPeriod: 600
  fallback:                       # Murphy 條款：Prometheus 斷線時凍結在安全容量
    failureThreshold: 3
    replicas: 15
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleUp:
          stabilizationWindowSeconds: 0     # 擴容不猶豫
          policies:
            - type: Pods
              value: 4
              periodSeconds: 60
        scaleDown:
          stabilizationWindowSeconds: 900   # 縮容等 15 分鐘再說
          policies:
            - type: Pods
              value: 1                      # 一次只縮一個，配合 drain（ch15）
              periodSeconds: 300
  triggers:
    # 主訊號：fleet 總排隊數，期望每 replica 排隊 ≤ 8
    - type: prometheus
      metadata:
        serverAddress: http://prometheus-operated.monitoring.svc:9090
        query: sum(vllm:num_requests_waiting{job="vllm-chat-70b"})
        threshold: "8"
    # 第二訊號：KV 利用率，攔截長 context 流量的記憶體軸飽和
    - type: prometheus
      metadata:
        serverAddress: http://prometheus-operated.monitoring.svc:9090
        query: avg(vllm:kv_cache_usage_perc{job="vllm-chat-70b"})
        threshold: "0.85"
```

幾個值得內化的設計點：

- **多 trigger 取 max**：KEDA 對每個 trigger 各算一個目標 replica 數，取最大值。佇列管吞吐軸、KV 管記憶體軸，哪個先飽和哪個說了算。
- **擴縮不對稱是刻意的**：擴容零等待、一分鐘最多 +4；縮容等 15 分鐘、五分鐘最多 -1。理由有三：尖峰常是鋸齒狀,對稱的策略會 flapping;縮容要 drain 長達分鐘級的 streaming 請求（ch15）；殺掉一個 replica 同時銷毀它的 prefix cache——暖 replica 的快取是資產，縮容是有狀態操作（ch10）。縮容應該慢到無聊。
- **`fallback` 不是選配**：指標管線本身會壞。沒有 fallback 的 ScaledObject 在 Prometheus 故障時行為是「維持現狀」，聽起來安全，直到故障撞上流量尖峰。把 fallback 設在「足以扛預測尖峰」的容量。
- **threshold 的語意**：Prometheus scaler 預設是 AverageValue——`sum(waiting)=88`、threshold 8 → 目標 11 個 replica。所以 query 用 `sum()` 配 per-replica 預算最直覺。

預測式擴縮在 KEDA 裡用 cron scaler 疊加實現：再加一個 `type: cron` 的 trigger，工作日 08:30 先把 minReplica 拉到日間水位——和你在遊戲活動前夜手動拉容量是同一件事，只是寫成宣告式。活動、行銷推送、產品發布前的 pre-scale 沒有任何自動訊號能替代：**autoscaler 看到的永遠是過去，只有你知道未來**。

### Knative KPA 與 scale-to-zero

Knative 的 KPA（KServe 的 Serverless 模式底層）只認兩種訊號：**併發數與 RPS**，原生支援 scale-to-zero，並有 panic mode（短窗口流量暴衝時跳過平滑直接擴）。兩個結論：

- 它讀不懂佇列深度與 KV 利用率，而「併發數」對 LLM 又有 RPS 同款的成本變異問題——所以 KPA 不是 LLM 主力服務的好答案。KServe 自己也提供 KEDA 路徑來做指標驅動的擴縮（2026-06）。
- 它真正的價值是 scale-to-zero 的長尾場景：內部平台上 20 個模型有 15 個一天被呼叫三次，閒置 GPU 比冷啟動難堪。但要誠實面對代價：ch12 算過冷啟動是分鐘級，scale-to-zero 等於把這個分鐘級延遲塞給閒置後的第一個使用者。決策準則：**面向使用者的同步服務不要 scale-to-zero；內部工具、批次、長尾模型可以**。中間地帶用 `minReplicaCount: 1` 加激進縮容。

| 機制 | 適用 | 不適用 | 一句話 |
|---|---|---|---|
| KEDA | LLM 服務的預設；任何 Prometheus 訊號 | — | external metrics 做對了的樣子 |
| HPA + adapter | 已有 adapter 基礎設施的組織 | 新建系統 | 能用，維運稅高 |
| Knative KPA | 長尾模型 scale-to-zero | 主力服務、需要佇列/KV 訊號 | 為無狀態 serverless 設計，LLM 只借它的零 |

## Scale-up 延遲是根本約束

把「按下擴容按鈕」到「新容量開始吃流量」的時間軸攤開（典型值，2026-06）：

| 階段 | 有暖節點 | 要新節點 |
|---|---|---|
| 指標 scrape + 評估 + HPA 決策 | 30–60s | 30–60s |
| Pod 排程 | 秒級 | — |
| 節點開機/進叢集（cluster autoscaler，ch11） | — | 5–20 min（且可能無貨） |
| Image pull + 權重載入 + warmup（解剖見 ch12） | 2–8 min | 2–10 min |
| **合計** | **3–9 min** | **8–30 min** |

流量尖峰是秒級到分鐘級的。結論很殘酷：**autoscaler 處理的是趨勢，不是尖峰。尖峰只能靠 headroom 吸收。**

### Headroom 數學

定義反應視窗 T_react = 從負載開始上升到新容量實際可服務的總時間（上表）。在 T_react 內到達的增量流量，只能由既有的空餘容量吸收。所以：

```
headroom 比例 h ≥ 你的流量在 T_react 內可能成長的最大幅度

需要的容量    N = N_base × (1 + h) + N_fail
等價的利用率目標 ρ_target = N_base / N
```

代入數字：T_react = 10 分鐘；翻你的流量歷史（你有 FluentBit pipeline,這正是它的用途），過去 90 天內任何 10 分鐘窗口的最大流量增幅是 30%；再加 N+1 容錯（一個 replica 故障或在 rollout 中）。那麼 h = 0.3，若 N_base = 11 則 N = ceil(11 × 1.3) + 1 = 15。預測尖峰時的利用率目標 ρ ≈ 11/15 ≈ 73%。

這就是 GPU fleet 跑不到 90% 利用率的結構性原因之一——剩下的 27% 不是浪費，是你買的保險。想壓縮它只有三條路：縮短 T_react（warm pool）、壓平流量（admission control + 排隊 + batch tier 分流，ch16）、或接受偶爾燒 SLO（跟產品談清楚）。

### Warm pool：用錢換 T_react

分層的暖度光譜，每深一層都更貴也更快：

1. **暖節點**：cluster autoscaler 的 overprovisioning（低優先級 placeholder pod 占著 GPU 節點，真工作負載來了搶占它，ch11）——省掉 5–20 分鐘的開節點時間，代價是閒置節點費。
2. **暖映像/暖權重**：節點 NVMe 預載 image 與權重（ch12 的優化手段）——把載入從 8 分鐘壓到 2 分鐘內。便宜，永遠值得做。
3. **暖引擎**：完整載入、CUDA graph 已 capture、不進 LB 的 standby replica——T_react 壓到秒級，代價是整卡閒置。只有 SLO 極嚴的場景值得。

### 預測式擴縮

LLM 流量有強烈的 diurnal pattern（上班時間 vs 凌晨可差 3–5 倍），這是最容易吃到的免費午餐：cron-based 排程（KEDA cron trigger）按時段調 min replica，凌晨的卡退回去（或讓給內部 batch 工作負載吃，ch16）。比 diurnal 更重要的是**事件驅動的 pre-scale**：你在遊戲業學到的「活動上線前先拉容量、寧可浪費兩小時也不要開場崩潰」在這裡原封不動適用——產品要推播、要上新功能、行銷要投放，容量要先到位。把「行銷日曆進入容量規劃流程」變成制度,比任何演算法都有效。

## 多維 scaling：加 replica 只是其中一個旋鈕

「容量不夠」有不止一種解法，每種的調整成本與時間尺度差很多。資深工程師的價值在於知道該轉哪個旋鈕：

| 維度 | 解什麼問題 | 時間尺度 | 代價 |
|---|---|---|---|
| 加/減 replica | 吞吐不足、佇列堆積 | 分鐘級（暖）～小時級（冷） | 線性 $；本章主軸 |
| 改 TP 度（ch09） | 單請求延遲不達標、或模型裝不下 | 小時級：全 fleet 重新部署 + 重新 benchmark | 通訊 overhead 改變整條效能曲線，舊容量數據作廢 |
| 改 MIG profile（ch11） | 小模型的利用率、多租戶隔離 | 小時級：節點 drain + 重切 | 排程複雜度、碎片化 |
| 換卡型（H100→B200…） | 經濟學的根本改變（$/有效 token） | 天～週：採購、排隊、遷移 | 一切 benchmark 重做；ch16 的決策 |
| 動模型（量化、換 size、開 spec decode，ch07） | 容量買不到或買不起 | 天級 + 品質評估 | 品質風險,需要 eval gate（ch15） |

Autoscaling 只自動化第一列。後四列是容量**工程**——按月做的審視,不是按分鐘做的反應。常見的職業級錯誤是用第一列硬扛本該用後四列解的問題：ITL 不達標就加 replica 是沒用的，單 replica 的 decode 速度跟 replica 數無關（ch03/ch09）——加 replica 解排隊，不解「算得慢」。

## 死亡螺旋：KV 壓力的正回饋迴圈

LLM serving 特有的 cascade failure，本章必須讓你能在凌晨三點一眼認出它：

```text
        流量上升 / 長 context 請求增多
                    │
                    ▼
     KV cache 利用率逼近 100%（ch05）
                    │
                    ▼
   scheduler 開始 preemption：踢掉執行中請求（ch06）
                    │
                    ▼
   被踢請求回到佇列，KV 被釋放——但它的 prefill 要全部重算
                    │
                    ▼
   有效負載上升（同樣的請求,要做更多次 prefill）
   goodput 下降、TTFT 飆升
                    │
                    ▼
   client 逾時 → 重試（retry storm，ch15）→ 流量進一步上升
                    │
                    └────────► 回到第一步，增益 > 1
```

你見過它的兩個近親：retry storm,以及 RDS 連線池耗盡時「逾時→重連→更多連線壓力」的螺旋。結構相同：**過載的系統為了處理過載而做更多工作**。LLM 版本的特殊處在於增益特別大——一次 preemption 浪費的是數千 token 的 prefill 算力，而重試進來的請求又是全額成本。

**可觀測的前兆**（按時間順序）：`vllm:kv_cache_usage_perc` 貼上 0.95+ → `vllm:num_preemptions_total` 的 rate 從 0 變成持續正值 → `num_requests_waiting` 開始堆積、TTFT p95 飆升——而此時 GPU utilization 是滿的、pod 全部 healthy。「GPU 100% 忙碌但 goodput 歸零」是這個故障的指紋。

**防禦工事的位置**（由外而內）：

1. **Admission control 在 gateway，不在引擎**（ch12 的結論在這裡兌現）：引擎的 waiting 佇列無界且不回 429。過載時必須在最前面拒絕——回 429 + `Retry-After`，讓 client 的退避邏輯有東西可遵循。Mooncake 論文把這叫 early rejection,是其 overload-oriented scheduling 的核心：在「開始算之前」拒絕,遠勝於「算到一半被踢」。
2. **Circuit breaker 以 preemption rate 為斷路條件**：`rate(vllm:num_preemptions_total[1m]) > 0` 持續 N 分鐘 → gateway 收緊 admission（降低放行併發），直到 preemption 歸零。這是買時間的機制——記住 scale-up 要 8–30 分鐘，螺旋成形只要幾十秒，**autoscaling 在死亡螺旋面前永遠遲到**，斷路器才是第一響應者。
3. **保守的引擎配置**：`max-num-seqs` 與 `gpu-memory-utilization` 留出餘量（ch06/ch08），讓 p95 的 context 長度組合也塞得下；KV 利用率的告警線設在 0.85 而非 0.95。
4. **分級卸載**：過載時先丟（或降級）低優先級流量——priority scheduling（vLLM V1 支援 priority policy）與租戶分級（ch16）。brownout 手段（縮 max context、關 spec decode 換容量）見 ch15。

## Worked example：5,000 並發對話的完整容量規劃

全書最重要的計算題之一。題目：

> 你的公司要上線一個 chat 產品。產品端給的需求：尖峰 **5,000 個並發對話**;SLO：**TTFT p95 < 1.5s、ITL p95 < 60ms**（打字感流暢）。模型選定 70B-class dense（即 ch03 反覆計算的 Llama-3.3-70B 級別），FP8 權重 + FP8 KV cache。問：需要幾張 H100？月成本多少？

方法論先行（這五步就是你面試時要背出來的骨架）：

> **① 把產品語言翻譯成流量模型（λ、token 分布、尖峰行為）→ ② 定義 replica 單位，benchmark 出 SLO 內的單 replica 持續吞吐 μ（goodput 膝點）→ ③ N_base = ⌈λ_peak / μ⌉ → ④ 加 headroom：burst 係數 + N+1 → ⑤ 複核（KV 容量、預算）、壓測驗證、上線後用真實數據回填。**

### Step 1 — 流量模型：5,000 並發對話 ≠ 5,000 個 in-flight 請求

這是最常見的錯誤翻譯。對話有 think time——使用者在讀回覆、在打字。你的 CCU 直覺直接適用：10K CCU 的遊戲也不是每秒 10K 個請求。建立模型：

| 參數 | 值 | 來源 |
|---|---|---|
| 輸入 token（含多輪歷史） | median 1,200 / **mean 1,500** / p95 4,000 | 同類產品數據或 beta 期實測 |
| 輸出 token | median 200 / **mean 250** / p95 600 | 同上 |
| 一次生成耗時 | ≈ TTFT 1s + 250 × 45ms ≈ **12s** | 由 SLO 與輸出長度推出 |
| 使用者讀 + 打字 | ≈ 48s | 產品端估計，需實測修正 |
| ⇒ 每對話請求週期 | **60s／請求** | |

於是尖峰到達率 **λ_peak = 5,000 ÷ 60 ≈ 83 req/s**。換算 token 需求：輸出 83 × 250 ≈ **20,800 tok/s**；prefill 原始需求 83 × 1,500 ≈ 125k tok/s——但多輪對話每次重送歷史,prefix cache 命中率高（ch05），有效 prefill 約打 4 折。這些 token 數不直接用來除卡數（那會漏掉排程與干擾的損耗），它們的用途是**設計 benchmark 的 workload**。

再用 Little's law 複核 in-flight 數：L = λ × W = 83 × 12s ≈ **1,000 個同時在生成的請求**。5,000 並發對話的真實瞬時負載是 1,000 in-flight——差 5 倍，這個係數值幾十萬美元。

### Step 2 — 定義 replica 單位，benchmark 出 μ

Replica 單位選 **2×H100 80GB、TP2**（70B FP8 權重約 70GB,單卡塞下後 KV 空間太侷促,TP2 是這個量級的標準解，ch09）。先紙上複核記憶體（ch03 公式）：

```
每 GPU 預算：80 GB × 0.92 (gpu-memory-utilization) = 73.6 GB
權重：70 GB ÷ 2 (TP2)                       = 35.0 GB/GPU
activation + CUDA graphs + NCCL buffers      ≈  4.6 GB/GPU
⇒ KV cache 空間 ≈ 34 GB/GPU × 2             = 68 GB/replica

Llama-3.3-70B 每 token KV（FP16）= 0.33 MB（ch03）→ FP8 KV = 0.16 MB
⇒ KV 容量 ≈ 68 GB ÷ 0.16 MB ≈ 425k tokens
```

再用 roofline 複核 ITL 下限（ch02）：每個 decode step 每卡讀 35GB 權重 ÷ 3.35TB/s ≈ 10.5ms，加上 TP all-reduce 與 chunked prefill 干擾,生產 batch 下 ITL p95 落在 40–60ms 是物理上合理的——SLO 可達,但不寬鬆。**如果這一步算出來物理上限就不達標，後面都不用跑了**——紙上複核的價值就在這裡。

然後上真 benchmark（`vllm bench serve` 或 inference-perf，方法論細節與 coordinated omission 的坑見 ch14），關鍵紀律：**用 Step 1 的 token 分布造 workload、開 prefix caching 模擬多輪重送、open-loop 注入、每檔速率至少跑 20 分鐘穩態**。掃 request rate 找 SLO 膝點（下表為示意數字,量級依據上面的物理複核，你的實測會不同——方法照搬即可）：

| 注入速率 | 穩態 in-flight | TTFT p95 | ITL p95 | KV 使用率 | SLO 判定 |
|---|---|---|---|---|---|
| 4 req/s | ~48 | 0.6s | 35ms | ~25% | ✓ |
| 6 req/s | ~72 | 0.8s | 44ms | ~33% | ✓ |
| **8 req/s** | **~96** | **1.2s** | **55ms** | **~42%** | **✓ ← 膝點** |
| 10 req/s | ~130+ | 3.5s | 82ms | ~55% | ✗ 佇列形成,TTFT 爆 |

**μ = 8 req/s／replica**（goodput 語意：SLO 內的最大持續速率，ch06/ch14）。注意這個 workload 是 compute/干擾先飽和（KV 才 42%）;若是長 context 的 RAG workload，KV 軸會先撞牆,膝點的成因不同——這就是為什麼 benchmark 必須用你自己的 token 分布,抄別人的數字等於抄別人的答案卷。

順手複核 Little's law：8 req/s × 12s = 96 in-flight，與實測吻合,模型自洽。

### Step 3 — 基線卡數

```
N_base = ⌈λ_peak / μ⌉ = ⌈83 / 8⌉ = ⌈10.4⌉ = 11 個 replica = 22 張 H100
```

### Step 4 — Headroom

- **Burst 係數**：尖峰時段內部的分鐘級抖動 + scale-up 視窗（T_react ≈ 10 min）內的最大成長。沒有歷史數據時，消費級產品取 1.3 起跳：83 × 1.3 = 108 req/s → ⌈108/8⌉ = 14 個 replica。
- **容錯**：N+1（一個 replica 在故障或 rollout 中）→ **15 個 replica = 30 張 H100**。

預測尖峰時利用率 ρ = 10.4/15 ≈ **69%**——這就是 SLO + 變異數 + 容錯的總價。配套的 KEDA 配置即前文那份 YAML：`minReplicaCount: 11`（日間尖峰時段，由 cron trigger 維持;夜間可降到 4–6）、`maxReplicaCount: 18`（預算閘門）、佇列 + KV 雙觸發。

### Step 5 — 複核與月成本

KV 複核：尖峰每 replica 96 in-flight × 平均存活 context ~1,700 tokens ≈ 163k tokens ≈ 26GB，是 425k 容量的 ~40%;p95 長度組合下也不會逼近天花板 ✓（prefix cache 會把剩餘空間填滿——KV 使用率讀數會偏高,正常）。

月成本（2026 年年中快照級距,只看量級;完整成本工程見 ch16）：

```
H100 neocloud on-demand ≈ $2.5/GPU·hr（級距 $2–3.5）

上限（30 卡 × 24/7）：30 × $2.5 × 730 hr ≈ $54,800/月
實際（diurnal autoscaling,平均 fleet ≈ 尖峰的 60%）：≈ $33,000–38,000/月
```

合理性 sanity check：日均負載約尖峰 35% → 每月輸出 token ≈ 19B → 全包成本 ≈ **$1.8–2.0 / M output tokens**,與 70B-class 模型的 API 牌價同量級——自建在這個量級尚未明顯划算,要靠 reserved 折扣與利用率工程才會（break-even 分析見 ch16）。

### Step 6 — 驗證與回填

上線前：以 1.3× λ_peak（108 req/s）對 15-replica fleet 做 30 分鐘以上穩態壓測（k6 或 inference-perf）,通過標準：SLO 全綠、preemption = 0、佇列不增長;再做一次「壓測中 kill 一個 replica」驗證 N+1 真的成立。上線後：把假設（think time 60s、token 分布、prefix 命中率）換成真實數據重算一輪——**容量規劃是迴圈,不是儀式**。

### 模擬工具的角色

掃配置空間（TP 度 × batch 上限 × 卡型 × 排程策略）時,真 GPU benchmark 每一格都要錢。模擬器（如 Microsoft 的 Vidur,MLSys 2024）用 profiling 數據預測不同配置的 TTFT/TPOT，把搜索成本降幾個量級。誠實的 hedge：截至我能確認的資訊（2026-06），Vidur 上一次 PyPI release 是 2025-08，維護動能存疑，宜當研究級工具——用它縮小候選集,最終配置仍以真 benchmark 拍板。輕量級的替代是用 llm-d-inference-sim 在模擬叢集上驗證「排程與擴縮邏輯」（見動手做），它不預測效能數字,但能驗證你的 autoscaling 行為。

## 故障模式與防禦

| 故障 | 症狀 | 根因 | 防禦 |
|---|---|---|---|
| **Flapping（擴縮震盪）** | replica 數鋸齒狀;每次縮容後幾分鐘又擴 | 對稱的擴縮策略 + 佇列訊號天然抖動 | 不對稱 behavior（擴快縮慢）、縮容 stabilization ≥ 15 min、threshold 與告警線拉開距離 |
| **平均值掩蓋熱點** | fleet avg 正常,但部分使用者 TTFT 爆 | 對 `avg()` 觸發 + KV-aware routing 的刻意不均（ch10） | 觸發用 `sum()`/`max()`;per-replica 佇列做告警不做觸發 |
| **指標管線斷裂** | 流量上升但 replica 數紋絲不動 | Prometheus/scrape 故障,HPA 拿不到指標就維持現狀 | KEDA `fallback` 設安全容量;對「指標缺席」本身告警（ch14） |
| **擴容擴了個寂寞** | HPA 已到 desired,pending pod 卡 10+ 分鐘 | 叢集沒有空 GPU、雲端無貨（stockout） | overprovisioning placeholder（ch11）、多 AZ/多雲容量策略（ch16）、maxReplica 要對齊「真的租得到」的數量 |
| **Scale-to-zero 陷阱** | 閒置後第一個請求逾時 | 冷啟動分鐘級（ch12） | 同步服務 min ≥ 1;長尾模型才歸零,且 client 端設計等待 UX |
| **負載中 readiness 假死** | 尖峰時 pod 被踢出 LB → 剩餘 pod 更過載 → 連鎖 | readiness probe 在高負載下逾時 | probe 必須輕量(不做真推論)、timeout 寬鬆;深健康檢查另設頻道（ch15） |
| **死亡螺旋** | preemption rate > 0、TTFT 爆、GPU 100% 忙、goodput 歸零 | KV 壓力 → preemption → 重算 → 更高負載（本章前述） | gateway admission control、preemption 斷路器、KV 告警線 0.85、priority shedding |
| **縮容殺掉暖 replica** | 縮容後 TTFT 全面變差,雖然容量「夠」 | prefix cache 隨 pod 銷毀;縮容挑了快取最熱的 victim | 縮容慢 + 一次一個;路由層感知 drain（ch10/ch15） |

共同主題：autoscaler 是一個以「指標→決策→執行」為迴路的控制系統，三段每一段都會壞——指標會說謊或缺席、決策會震盪、執行會卡在沒貨。把每一段的失效模式都設好預設行為，才算設計完成。

## 動手做

### Lab 1 — 佇列驅動的 autoscaling 全迴路 **[M1]**

在 ch11 搭好的 `gpu-sim` 模擬叢集上，把本章的訊號→KEDA→擴縮迴路真的跑起來（對應 plan.md 旗艦專案①的進階）。零 GPU 費用。

1. 裝 KEDA（helm）與 kube-prometheus-stack;部署 llm-d-inference-sim 的 Deployment（它模擬 vLLM 的 OpenAI API 與 vLLM 相容的 `/metrics`,可設定 TTFT/ITL 延遲參數）,initial replicas = 2,讓 Prometheus 抓它的指標。
2. 套用本章的 ScaledObject（把 query 的 label 換成你的 job 名,threshold 先設 5）。
3. 用 k6 寫 ramp 場景：60s 內從 5 VU 拉到 80 VU,維持 10 分鐘。觀察三條曲線：`num_requests_waiting`、replica 數、k6 的 p95。
4. **成功標準**：能在 Grafana 上指出「佇列開始堆積」與「新 replica 就緒」之間的時間差（這就是你的 T_react）;然後把 minReplicaCount 從 2 改成 4 重跑,展示 headroom 對 p95 的改善。
5. 進階:給 sim 加上 startup 延遲(模擬權重載入),重跑 ramp,觀察 T_react 變長之後 headroom 需求怎麼變——把本章的 headroom 公式用自己的數據驗證一次。

### Lab 2 — 換一種 workload 重做容量規劃 **[紙上推演]**

把 worked example 的方法套到新題目：「內部 RAG 助理，800 個分析師並發使用，輸入 mean 8,000 / p95 20,000 tokens,輸出 mean 300,TTFT p95 < 4s、ITL p95 < 80ms」。要求：走完五步、明確指出這個 workload 的膝點會由哪個軸決定（提示：先算 KV——它跟 chat 案例不同）、並回答「這個場景該不該考慮 P/D 分離（ch10）」。成功標準：卡數、headroom、月成本三個數字 + 每步的依據。

### Lab 3 — 配置空間搜索 **[紙上推演]**

用 Vidur（若環境裝得起來;研究級工具,2026-06 維護狀態存疑）或手算,對 Lab 2 的 workload 比較三種配置：TP2×H100、TP4×L40S、TP2×H200,各自的記憶體帳、理論 ITL 下限（roofline）、估計卡數與成本排序。成功標準：一張對照表 + 一段「我會選哪個、什麼新資訊會讓我改變主意」。

## 這個領域往哪走

- **Autoscaling 正在往 gateway 裡長**。Gateway API Inference Extension v1.5（2026-04）加入了 pool 層級的 saturation gauge 與 flow control——飽和度感知從「事後擴縮」前移到「路由當下」。擴縮、路由、admission control 三件事正在融合成同一個控制平面（ch12 的架構會繼續演化）。
- **SLO 驅動的 planner 取代 threshold 調參**。NVIDIA Dynamo 的 Planner 配合 AIConfigurator 做吞吐建模：給定 SLO 與流量,直接算出 P/D 配比與 replica 數,而不是讓人肉調 threshold。方向是把本章的 worked example 變成系統的內建能力——但方法論不會過期,因為你得看懂它算出來的東西對不對。
- **Agentic 流量讓尖峰更機器化**（ch17）：burst 由程式發起、相關性強、沒有 think time,Step 1 的流量模型假設全要重估。容量數學不變,輸入分布劇變。

## 自我檢核

1. 為什麼 GPU utilization 接近 100% 對 autoscaling 沒有資訊量？一個 batch=1 的 decode 迴圈為什麼會顯示高 util？
2. 寫出 vLLM 的四個 autoscaling 相關指標名,按「領先→落後」排序,並說明各自的判讀陷阱（至少含 prefix caching 對 KV 使用率讀數的影響）。
3. KEDA 多個 trigger 同時存在時的合成語意是什麼？為什麼縮容的 stabilization window 要遠長於擴容?給出三個理由。
4. 5,000 並發對話為什麼不等於 5,000 個 in-flight 請求？用 Little's law 寫出換算,並說明 think time 假設錯 2 倍時卡數差多少。
5. 默寫容量規劃五步驟。為什麼 benchmark 必須用自己的 token 分布而不能引用別人的數字？
6. 完整描述死亡螺旋的因果鏈、三個按時間順序出現的前兆指標,以及為什麼 autoscaling 救不了它、第一響應者該是什麼。
7. 從 T_react 推導 headroom 比例的公式是什麼？warm pool 的三個層級各用什麼代價換掉哪段時間？
8. 「ITL p95 不達標」為什麼通常不能靠加 replica 解決?該轉哪些旋鈕？

## 延伸閱讀

- [vLLM Metrics 設計文件](https://docs.vllm.ai/en/latest/design/metrics/) — V1 指標的權威清單與設計理由,本章訊號階層的事實來源。
- [vLLM production-stack: Autoscaling with KEDA](https://docs.vllm.ai/projects/production-stack/en/latest/use_cases/autoscaling-keda.html) — 官方的佇列驅動 KEDA 教學,Lab 1 的真 GPU 版。
- [KEDA Prometheus scaler 文件](https://keda.sh/docs/2.19/scalers/prometheus/) 與 [ScaledObject 規格](https://keda.sh/docs/2.19/reference/scaledobject-spec/) — threshold 語意、fallback、behavior 的精確定義都在這裡。
- [Knative Autoscaling 文件](https://knative.dev/docs/serving/autoscaling/) — KPA 的 concurrency/RPS 模型與 scale-to-zero 配置。
- [Red Hat: KServe autoscaling for vLLM with KEDA](https://developers.redhat.com/articles/2025/09/23/how-set-kserve-autoscaling-vllm-keda) — KServe 生態下指標驅動擴縮的落地寫法。
- [DistServe 論文（arXiv:2401.09670）](https://arxiv.org/abs/2401.09670) — goodput（SLO 內吞吐）作為容量單位的源頭之一,Step 2 的理論依據。
- [Mooncake 論文（arXiv:2407.00079）](https://arxiv.org/abs/2407.00079) — overload-oriented scheduling 與 early rejection:生產系統怎麼把 admission control 當一級設計。
- [Vidur 論文（arXiv:2405.05465）](https://arxiv.org/abs/2405.05465) 與 [repo](https://github.com/microsoft/vidur) — LLM 推論模擬器的代表作;維護動能存疑（2026-06）,當研究工具讀。
- [AKS: Autoscale KAITO inference workloads with KEDA](https://blog.aks.azure.com/2026/02/03/autoscale-inference-workloads-with-kaito) — 雲端託管視角的同一套模式（2026-02）。
