# 附錄C — 工程速查表

> 全部可直接抄用。每個區塊標注來源章節——公式的推導、機制的解釋、調錯的完整脈絡都在正文，這裡只放「動手時要抄的那一行」。所有時效性內容（版本號、預設值、規格）標注 2026-06，過期請以官方文件為準；數字基準與正文一致：模型用 Llama-3.3-70B、卡用 H100 SXM。

## C.1 公式卡

### KV cache 大小（ch03，全書公式）

```
KV cache bytes = 2 × n_layers × n_kv_heads × head_dim × bytes_per_param × n_tokens
```

`2` = K 和 V 各一份；`bytes_per_param`：BF16/FP16 = 2、FP8 = 1。前四項相乘 = 每 token 每序列的 KV bytes（模型的固定體質，從 config.json 直接算）。MLA 模型（DeepSeek 系）不適用此公式，以 `kv_lora_rank` 為準（見 ch03）。

**代入 Llama-3.3-70B**（80 層、8 KV heads、head_dim 128、BF16）：

```
每 token：2 × 80 × 8 × 128 × 2 = 327,680 bytes ≈ 320 KiB ≈ 0.33 MB
一條 32k 對話：32,768 × 327,680 ≈ 10.7 GB
2×H100（FP8 權重）KV 池 ≈ 69 GB → 約 6 條 32k 並發對話；單卡 H100 → 0 條
```

### 模型權重記憶體（ch03/ch07）

```
權重 bytes = 參數量 × bytes_per_param（BF16/FP16 = 2、FP8 = 1、INT4 = 0.5）
```

**代入 70.6B**：BF16 ≈ 141.2 GB（單卡 80GB 裝不下）；FP8 ≈ 71 GB（單卡塞下但 KV 空間趨近零）；INT4 ≈ 35 GB。實務上 embedding 等少數層不量化，FP8 全模型約 72~75 GB。

### Roofline 拐點（ch02）

```
Arithmetic intensity (AI) = FLOPs ÷ 必須從 HBM 搬的 bytes（FLOP/byte）
拐點 (ridge point) = P_peak ÷ BW
AI < 拐點 → memory-bound（效能 = AI × BW）；AI > 拐點 → compute-bound
```

**代入**（dense 算力，2026-06）：H100 BF16 989 TFLOPS ÷ 3.35 TB/s ≈ **295**；H100 FP8 1,979 ÷ 3.35 ≈ **590**；H200 BF16 989 ÷ 4.8 ≈ **206**；B200 FP8 4,500 ÷ 8 ≈ **562**。
速判：decode（batch=1）AI ≈ 1 → 極端 memory-bound；prefill AI ≈ n（prompt 長度），n 超過 ~300 翻成 compute-bound。batch 拉高 decode 的 AI，但漸近線 = `2P ÷ KV_per_seq`——70B、32k context 時只有 ~13，**長上下文 decode 是 batching 救不回來的 memory-bound**（ch03）。

### Decode 理論上限（ch02/ch03）

```
單請求 decode 上限 (tok/s) ≈ HBM 頻寬 ÷ 每 token 必讀 bytes（權重 + 該序列 KV）
batch B 每步讀取 = 權重 + B × KV/條；ITL ≈ 每步讀取 ÷ 頻寬
```

**代入 H100**：FP8 權重 70.6 GB → 3.35 TB/s ÷ 70.6 GB ≈ **47 tok/s**；BF16 + 32k KV → 3,350 ÷ (141 + 10.7) ≈ **22 tok/s**。現實 MBU 60–80% → 實測單請求約 30–38 tok/s（FP8）。看到「單請求 70B FP8 在 H100 跑 100 tok/s」的宣稱，直接判假。

### $/Mtok（ch16）

```
理論 $/Mtok = GPU 單價 ($/GPU-hr) ÷ (goodput tok/s/GPU × 0.0036)
實付 $/Mtok = 理論 $/Mtok ÷ 機隊利用率
```

goodput 是 SLO 內的 token rate（ch14），不是峰值吞吐；超出 SLO 的 token 是廢品，廢品不攤成本。

**代入**（2026-06 快照）：H100 $2.50/hr、70B FP8 TP2、goodput 2,000 tok/s/GPU → 理論 = 2.50 ÷ 7.2 ≈ **$0.35**；機隊利用率 40% → 實付 ≈ **$0.87**（恰與 Together 的 Llama-3.3-70B 牌價 $0.88 打平——市場已有效率到「自建全成本 ≈ 託管牌價」）。成本槓桿排序：利用率（2–5×）> 快取命中（1.5–3×）> batch/量化（殘餘 1.5–3×）> 硬體代際。

### 容量規劃：Little's law 鏈（ch13，五步骨架）

```
① λ_peak = 並發對話數 ÷ 請求週期        （週期 = 生成時間 + think time）
   L (in-flight) = λ × W                 （Little's law；W = 一次生成耗時）
② μ = 單 replica 在 SLO 內的持續吞吐    （goodput 膝點，必須用自己的 token 分布 benchmark）
③ N_base = ⌈λ_peak ÷ μ⌉
④ N = ⌈λ_peak × burst係數 ÷ μ⌉ + 1     （burst 無歷史數據時取 1.3 起跳；+1 = 容錯）
⑤ 複核 KV 容量與預算 → 壓測驗證 → 上線後回填
headroom 下限：h ≥ 流量在 T_react（scale-up 延遲，GPU 世界 10 分鐘級）內可能成長的最大幅度
```

**代入 ch13 主例**（5,000 並發 chat、TTFT p95<1.5s、ITL p95<60ms、70B FP8 TP2）：λ_peak = 5,000÷60 ≈ 83 req/s；L = 83×12s ≈ 1,000 in-flight（≠5,000，差 5 倍）；μ = 8 req/s/replica → N_base = ⌈83/8⌉ = 11；burst 1.3 → 14；+1 → **15 replicas = 30×H100**；尖峰利用率 ρ ≈ 69%；月成本（diurnal autoscaling 後）≈ $33–38k（2026 年年中快照）。

### Drain timeout（ch15）

```
P(t 秒內清空一個 pod) = F(t)^C          （C = in-flight 數；F = 請求時長 CDF）
單 pod 期望被砍 streams = C × (1 − F(t))
drain 預算照 p99.9 以上設計，零傷亡需要 gateway 的 max stream duration 硬上限
terminationGracePeriodSeconds ≥ drain 截止 + 清理緩衝
```

**代入 ch15 主例**（24 pods、每 pod 48 in-flight、p99=120s、p99.9=420s、硬上限 900s）：等到 p99 只有 0.99⁴⁸ ≈ 62% 的 pod 清空；整輪傷亡——30s（K8s 預設！）砍 ~92 條、120s 砍 ~11.5 條、420s 砍 ~1.2 條、900s 零傷亡。`terminationGracePeriodSeconds: 960`。從 p99 等到 p99.9 幾乎不增加 rollout 時間（被冷啟動＋bake 遮蔽），認真做 drain + canary 的 deploy 是 2~4 小時起跳。

## C.2 vLLM 關鍵參數表（2026-06，vLLM 0.22.x；與 ch08 一致）

預設值隨版本演進，**以你手上版本的 `vllm serve --help` 為準**。

| 參數 | 它在解什麼問題 | 預設（2026-06） | 調錯的症狀 |
|---|---|---|---|
| `--max-model-len` | 單一請求的 context 上限，決定一個請求最多吃多少 KV | 自動取模型 config（往往大得離譜） | 太大：啟動報 KV 容量不足起不來，或 KV 牆提前；太小：長請求被 400 拒絕 |
| `--gpu-memory-utilization` | 引擎可用 GPU 記憶體比例，KV pool 由它倒扣 | 0.92（早期版本 0.9） | 太高：尖峰偶發 OOM、in-flight 全陪葬；太低：KV pool 縮水、preemption 變多 |
| `--max-num-seqs` | 同時 running 的請求數上限（batch B） | 1024（V1） | 太高：ITL 墊高、preemption storm；太低：GPU 餵不飽、佇列堆積 |
| `--max-num-batched-tokens` | 每步 token budget，控制 prefill 對 decode 的干擾 | 常見 8192（隨版本/硬體） | 太大：長 prompt 進來 ITL 尖刺；太小：TTFT 變差 |
| `--enable-prefix-caching` | 前綴 KV 重用 | V1 預設開（`--no-enable-prefix-caching` 關） | 誤關：agentic/多輪流量 TTFT 暴漲；對比實驗忘了關：高估裸 prefill |
| `--tensor-parallel-size` | 單模型切到幾張卡（單節點內） | 1 | PCIe 互連硬開 TP：all-reduce 吃掉收益；單卡裝得下還開：純付通訊稅 |
| `--kv-cache-dtype fp8` | KV cache 減半 | `auto`（跟隨模型 dtype） | 長推理鏈品質劣化，5xx 看不到——要 eval 才抓得到 |
| `--quantization` | 權重量化格式 | 自動從 checkpoint 偵測 | 卡不支援該格式（如 Ampere 跑 FP8）：啟動失敗或 fallback 慢路徑 |
| `--dtype` | 權重載入精度 | `auto` | 舊卡強用 BF16：報錯或退化 |
| `--speculative-config` | speculative decoding（JSON） | 關 | 高 batch 流量開啟：吞吐不升反降（驗證稅） |
| `--scheduling-policy` | `fcfs` 或 `priority` | `fcfs` | 開 priority 但上游沒配額：低優先權租戶餓死 |
| `--enforce-eager` | 關 CUDA graphs（debug 用） | 關（graphs 開啟） | debug 完忘記拿掉：ITL 多吃 launch overhead |
| `--block-size` | KV block 的 token 數（分頁粒度） | 16 上下 | 幾乎不需要動 |

調參順序（ch08）：① `--max-model-len` 照流量 p99 context 設，不是模型上限（啟動 OOM 十之八九是它）→ ② `--gpu-memory-utilization` 給足留餘裕 → ③ `max-num-seqs` / `max-num-batched-tokens` 找工作點 → ④ 一次只動一個參數，每動必量。

## C.3 PromQL 片段（指標名與 ch13/ch14 一致；vLLM V1，2026-06）

```promql
# TTFT p99（p50/p95 改第一個參數）
histogram_quantile(0.99,
  sum(rate(vllm:time_to_first_token_seconds_bucket[5m])) by (le))

# ITL p99（舊版指標名為 vllm:time_per_output_token_seconds，以部署版本的 /metrics 為準）
histogram_quantile(0.99,
  sum(rate(vllm:inter_token_latency_seconds_bucket[5m])) by (le))

# 佇列深度：擴縮觸發用 sum()（總排隊人數，配 per-replica threshold），不要用 avg()
sum(vllm:num_requests_waiting{job="vllm-chat-70b"})

# KV cache 利用率（開 prefix caching 後長期偏高是正常的，要搭配 preemption 一起判讀）
avg(vllm:kv_cache_usage_perc{job="vllm-chat-70b"})

# Preemption 速率（健康系統 = 0；counter 一律包 rate()，永不裸用）
rate(vllm:num_preemptions_total[5m])

# Prefix cache 命中率（緩慢下滑 = 經典隱性退化：路由親和壞掉或流量結構變了）
rate(vllm:prefix_cache_hits[5m]) / rate(vllm:prefix_cache_queries[5m])

# Goodput@SLO 近似：TTFT ≤ 1.5s 的請求比例
# 前提：bucket 設計時就把 SLO 閾值放進 le 邊界——先定 SLO、再設 bucket，順序不能反
sum(rate(vllm:time_to_first_token_seconds_bucket{le="1.5"}[5m]))
  / sum(rate(vllm:time_to_first_token_seconds_count[5m]))

# SLO burn rate（示意；目標 99% → error budget 1%；burn > 1 = 正在透支預算）
(1 - (
  sum(rate(vllm:time_to_first_token_seconds_bucket{le="1.5"}[1h]))
    / sum(rate(vllm:time_to_first_token_seconds_count[1h]))
)) / 0.01
```

判讀紀律（ch14）：平均值不准出現在任何告警條件；fleet 聚合 `avg()` 會被冷熱不均掩蓋（KV-aware routing 下不均是故意的）；TTFT bucket 用對數刻度跨四個量級（50ms–60s），p99 恆定貼著 bucket 上界時先懷疑 bucket 溢出，不是「穩定地壞」。

## C.4 DCGM 重點欄位與 nvidia-smi 讀法（ch14）

`DCGM_FI_DEV_*` 是傳統裝置層欄位；`DCGM_FI_PROF_*` 是 profiling 計數器（精度高、支援 MIG），該用後者。

| 欄位 | 語意 | 速判 |
|---|---|---|
| `DCGM_FI_DEV_GPU_UTIL` | 取樣窗內**至少一個 kernel 在跑**的時間比例（= nvidia-smi 的 GPU-Util） | 高負載下恆 90%+，資訊量趨近零，別用它做任何決策；不支援 MIG |
| `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | compute engine active 比例，GPU_UTIL 的高精度替代 | 滿載 > 0.85；低 + 佇列在長 = 引擎卡住非容量不足（ch15） |
| `DCGM_FI_PROF_SM_ACTIVE` | 至少一個 warp 駐留的 SM 比例 | 滿載 > 0.8；warp 等記憶體也算 active——高 ≠ 在算東西 |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | tensor core pipe active 比例 | **decode 重時 10–25% 是物理不是 bug**；別看到低就去「優化」 |
| `DCGM_FI_PROF_DRAM_ACTIVE` | HBM 介面 active 比例 | decode 重時 0.5–0.8 = 頻寬有被用起來，是「健康的忙」 |
| `DCGM_FI_DEV_FB_USED` | 已用顯示記憶體 | 恆高——vLLM 啟動就預占，**「GPU 記憶體用量高」永遠不是告警條件**，真訊號在 `vllm:kv_cache_usage_perc` |
| `DCGM_FI_DEV_POWER_USAGE` | 板卡功耗 | 「有效工作量」的意外好代理：同 fleet 某卡功耗持續偏低 = 慢卡/掉頻，會拖慢整池 |
| `DCGM_FI_DEV_GPU_TEMP` + throttle reasons | 溫度與降頻原因 | thermal throttle = 機房問題不是軟體問題 |
| `DCGM_FI_DEV_XID_ERRORS` | 最近一次 Xid 錯誤碼 | 非零直接查 ch15 故障目錄；致命 Xid 觸發自動 cordon（ch11） |

**nvidia-smi 讀法四要點**：

1. GPU-Util 的真實定義是「有沒有 kernel 在跑」不是「算力用了多少」——一個只占 1 個 SM 的 spin kernel 也顯示 100%。等同於「64 核裡任一核非 idle 就回報 CPU 100%」的 htop，你不會接受這種 CPU 指標。
2. Memory used 恆貼上限是 vLLM 的正常狀態（啟動即按 `gpu-memory-utilization` 預占），不是洩漏。
3. benchmark 前用 `nvidia-smi -lgc` 鎖 GPU clock，消除 boost 浮動（CI 迴歸的固定紀律，ch14）。
4. 讀規格表防雷：NVIDIA 行銷頁預設引「with sparsity」數字（dense 的兩倍），LLM 推論用不到，一律看 dense；頻寬數字先問單向還是雙向加總（NVLink 900 GB/s 是雙向加總）。

交叉診斷速查：佇列增長 + GR_ENGINE_ACTIVE 高 + DRAM_ACTIVE 高 = 真飽和（去 ch13 擴容）；佇列增長 + GR_ENGINE_ACTIVE 低 = 引擎卡住（去 ch15）；吞吐降 + preemption 升 + KV 100% = KV 壓力（別被「GPU 100%」騙去加算力）；TTFT 右移 + prefix hit 掉 + GPU 全綠 = cache/路由退化（加卡完全無效，去 ch05/ch10）。

## C.5 K8s YAML 骨架（與 ch11/ch13 一致；2026-06）

### GPU resource request（device plugin 模型）

```yaml
# 整數、不可超賣、不可分割；requests 必須 = limits（ch11）
containers:
- name: vllm
  image: vllm/vllm-openai
  resources:
    limits:
      nvidia.com/gpu: 1
```

### Time-slicing（只准出現在 dev namespace——兩個 vLLM 共享一張卡 = 必然 OOM）

```yaml
# device plugin 的 sharing config（示意）：把一張卡謊報成 4 個
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
data:
  any: |-
    version: v1
    sharing:
      timeSlicing:
        resources:
        - name: nvidia.com/gpu
          replicas: 4
```

### MIG（H100 80GB profile：`1g.10gb`×7 / `2g.20gb`×3 / `3g.40gb`×2 / `7g.80gb`×1）

```yaml
# ① 節點宣告切法（MIG Manager 看 label 行動；改 profile 需先清空節點上的 GPU Pod）
kubectl label node $NODE nvidia.com/mig.config=all-3g.40gb --overwrite
# ② mixed 策略下 Pod 請求特定切片（single 策略則仍叫 nvidia.com/gpu）
resources:
  limits:
    nvidia.com/mig-3g.40gb: 1
```

記住：MIG 連 HBM 頻寬也跟著 memory slice 等比切——`3g.40gb` 上的模型 decode 上限約整卡一半，划不划算要回 roofline 算（ch11）。

### DRA ResourceClaim（resource.k8s.io/v1，K8s 1.34+ GA；CEL 屬性名依 driver 而異，示意）

```yaml
apiVersion: resource.k8s.io/v1
kind: ResourceClaimTemplate
metadata:
  name: two-h100-same-domain
spec:
  spec:
    devices:
      requests:
      - name: gpus
        exactly:
          deviceClassName: gpu.nvidia.com
          allocationMode: ExactCount
          count: 2
          selectors:
          - cel:
              expression: >-
                device.attributes['gpu.nvidia.com'].productName.matches('H100') &&
                device.capacity['gpu.nvidia.com'].memory.compareTo(quantity('79Gi')) >= 0
---
apiVersion: v1
kind: Pod
metadata:
  name: tp2-worker
spec:
  resourceClaims:
  - name: gpus
    resourceClaimTemplateName: two-h100-same-domain
  containers:
  - name: vllm
    image: vllm/vllm-openai
    resources:
      claims:
      - name: gpus        # 不再是 nvidia.com/gpu: 2
```

### LWS（多節點推論的複製單位；LWS v0.8.0，2026-01）

```yaml
# 每個副本 = 2 節點 × 8 卡（示意）
apiVersion: leaderworkerset.x-k8s.io/v1
kind: LeaderWorkerSet
metadata:
  name: llama-405b
spec:
  replicas: 2              # 2 個模型實例
  leaderWorkerTemplate:
    size: 2                # 每實例 1 leader + 1 worker
    restartPolicy: RecreateGroupOnPodRestart   # 一人死全組重啟（NCCL 連坐）
    leaderTemplate:
      spec:
        containers:
        - name: vllm
          resources: { limits: { nvidia.com/gpu: 8 } }
    workerTemplate:
      spec:
        containers:
        - name: vllm
          resources: { limits: { nvidia.com/gpu: 8 } }
```

### KEDA ScaledObject（KEDA v2.20；佇列 + KV 雙觸發，取 max；ch13）

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: vllm-chat-70b
  namespace: inference
spec:
  scaleTargetRef:
    name: vllm-chat-70b
  minReplicaCount: 11             # 基線容量：headroom 數學的輸出，不是拍腦袋
  maxReplicaCount: 18             # 預算上限 ∧ 叢集實際租得到的卡
  pollingInterval: 15
  cooldownPeriod: 600
  fallback:                       # Murphy 條款：Prometheus 斷線時凍結在安全容量
    failureThreshold: 3
    replicas: 15
  advanced:
    horizontalPodAutoscalerConfig:
      behavior:
        scaleUp:
          stabilizationWindowSeconds: 0     # 擴容不猶豫
          policies: [{ type: Pods, value: 4, periodSeconds: 60 }]
        scaleDown:
          stabilizationWindowSeconds: 900   # 縮容等 15 分鐘——縮容是有狀態操作（drain + cache）
          policies: [{ type: Pods, value: 1, periodSeconds: 300 }]
  triggers:
  - type: prometheus              # 主訊號：fleet 總排隊數，期望每 replica 排隊 ≤ 8
    metadata:
      serverAddress: http://prometheus-operated.monitoring.svc:9090
      query: sum(vllm:num_requests_waiting{job="vllm-chat-70b"})
      threshold: "8"
  - type: prometheus              # 第二訊號：KV 利用率，攔截長 context 流量的記憶體軸
    metadata:
      serverAddress: http://prometheus-operated.monitoring.svc:9090
      query: avg(vllm:kv_cache_usage_perc{job="vllm-chat-70b"})
      threshold: "0.85"
```

預測式擴縮：疊一個 `type: cron` trigger 在工作日 08:30 拉日間水位——autoscaler 看到的永遠是過去，只有你知道未來（活動/推播前 pre-scale 沒有自動訊號能替代）。

## C.6 Benchmark 檢查清單：發表數字前的 12 個自問（ch14 方法論）

1. SLO 是在跑 benchmark **之前**定好的嗎？（事後挑閾值 = 替自己作弊）
2. open-loop 還是 closed-loop？它回答的問題跟我要回答的一致嗎？（容量規劃幾乎都是 open-loop 的問題；closed-loop 的 `VU ÷ E2E = req/s` 是 Little's law 恆等式，不是系統能力）
3. 有沒有 coordinated omission？（closed-loop 在伺服器最痛苦時自動收手，災難期欠採樣，percentile 被沖淡）
4. 有 warmup 並整段丟棄嗎？每個量測點跑滿 3–5 分鐘穩態了嗎？（冷 cache 的引擎是另一台機器）
5. token 分布來自生產流量嗎？固定長度（`--ignore-eos`）還是自然停止有註明嗎？（兩者可差 20%+）
6. prefix 結構符合真實命中率嗎？（零共享前綴測 80% 命中的系統，TTFT 悲觀 2–5 倍；單一 prompt 重打則樂觀到離譜——冷/熱兩組都測）
7. 到達過程是什麼？（均勻到達不存在；Poisson 是底線；`vllm bench serve` 的 `--request-rate` 預設 `inf` 是在測瞬間洪峰，不是穩態）
8. 每個量測點 achieved ≈ offered 嗎？（達成 < 注入 = 已飽和，該點只能標「飽和」，不能當「系統能跑這麼快」的證據）
9. client 端是不是瓶頸？（k6 自己的 CPU、VU 池大小；xk6-sse 阻塞 VU，數千 stream 換 inference-perf）
10. 報的是分位數還是平均？（ITL 要看 p99/p999——stall 是稀疏事件，p95 常無感；平均值會把 thundering herd 與 preemption 全部抹平）
11. 給的是整條 latency-throughput frontier 還是單點？膝點在哪？goodput@SLO 有跟 SLO 定義一起報嗎？（沒有 SLO 的 goodput 數字無法比較）
12. 可重現嗎？（GPU SKU、driver、鎖 clock `nvidia-smi -lgc`、seed、資料集、引擎版本與全部參數記錄在案；至少 3 輪取中位數；判定線 = 中位數偏移 > max(2σ, 3%)）

## C.7 硬體速查小表（2026-06，與 ch02 一致）

| 卡 | HBM 容量 | HBM 頻寬 | FP8 算力（dense） | 拐點（FP8） | 一句話定位 |
|---|---|---|---|---|---|
| H100 SXM | 80 GB HBM3 | 3.35 TB/s | 1,979 TFLOPS | ~590 FLOP/byte | 2026 租用市場的工作馬，生態最成熟、單價已被新卡壓低 |
| H200 | 141 GB HBM3e | 4.8 TB/s | 1,979 TFLOPS（算力同 H100） | ~412 FLOP/byte | 記憶體大幅升級——專為推論/長 context 而生 |
| B200 | 192 GB HBM3e | 8 TB/s | 4,500 TFLOPS | ~562 FLOP/byte | 2026 主力雲端機型；FP4 原生支援 |

參考級距（同表來源，ch02）：B300/GB300 288 GB HBM3e、8 TB/s、1,400W；AMD MI355X 288 GB、8 TB/s（規格對齊 Blackwell）；GB200 NVL72 = 72×B200 單一 NVLink 域（聚合 130 TB/s），rack 取代 server 成為設計單位。互連速查：NVLink 4（Hopper）900 GB/s、NVLink 5（Blackwell）1.8 TB/s——皆為雙向加總；標準 HGX H100 每卡 400G IB NIC = 50 GB/s 單向；PCIe Gen5 ~64 GB/s 單向（HBM 的 1/50，「少過橋、晚過橋」的根源）。

讀規格表紀律（再說一次，因為一定會踩）：行銷頁的算力預設含 sparsity，一律除以二看 dense；頻寬先問單向還是雙向。
