# ch14 — 可觀測性與 Benchmark：你不能優化你量不到的東西

> **本章解決什麼問題**：前面所有章節的決策——調哪個參數（ch08）、要不要 P/D 分離（ch10）、留多少 headroom（ch13）——最後都要靠數據回答。本章建立兩件事：一套分層的指標體系（從產品 SLO 一路往下鑽到 DCGM 的硬體計數器），以及一套誠實的 benchmark 方法論（open-loop、warmup、latency-throughput frontier、goodput@SLO）。這是你 FluentBit pipeline 與 k6 經驗最直接複用的一章；ch15 的告警 runbook、ch16 的成本指標都建立在本章的指標地基上，但不在這裡展開。

## 從你已知的出發

你做過兩件事，跟本章是同構的。

第一件：你用 FluentBit + Lua 從 production logs 萃取 API 指標送進 S3——本質是「應用不直接給你想要的指標，所以你在旁路建一條萃取管線」。LLM serving 的好消息是引擎（vLLM）原生暴露 Prometheus `/metrics`，硬體有 DCGM-exporter，你不用再寫 Lua 去 parse log；壞消息是指標的「層」變多了：你以前一層 API 指標就能回答大部分問題，現在同一個症狀（「變慢了」）的根因可能在五層中的任何一層——產品、請求、引擎、GPU、叢集——而且**各層指標會互相說謊**（GPU「100% 利用率」可能什麼有效工作都沒做，後面講透）。

第二件：你用 k6 和 Vegeta 做負載測試。這個經驗九成可以平移，但有一個你可能已經隱約知道、在 LLM 世界會被放大一百倍的陷阱：**closed-loop 測試的 coordinated omission**。你的遊戲 API 一個請求 50ms，k6 用 `constant-vus` 測出來的偏差還能忍；LLM 一個請求 5 秒到 5 分鐘，closed-loop 的自我節流會讓你的 benchmark 結果跟生產現實差出 30% 以上——本章的 worked example 會用數字把這件事拆穿。

方法論還是你那套：量測 → 診斷 → 優化 → 用數據證明。你拿它降過 RDS CPU 40%；這章把儀器換成 GPU 世界的。

## 五層指標分類學

先給全景，再逐層拆。每層回答一個不同的問題：

```text
┌─ 產品層 ──「使用者拿到價值了嗎?」── availability、goodput@SLO
├─ 請求層 ──「單一請求的體驗如何?」── TTFT、ITL/TPOT、E2E、排隊時間
├─ 引擎層 ──「引擎把資源用好了嗎?」── batch 占用、KV util、preemption、cache hit
├─ GPU 層 ──「硬體在做什麼?」────── DCGM:SM/tensor/DRAM activity、功耗、Xid
└─ 叢集層 ──「容量與排程健康嗎?」── pending pods、pool 飽和度、佇列深度
```

診斷永遠從上往下鑽：產品層告警 → 請求層定位哪段延遲壞了 → 引擎層找機制原因 → GPU 層確認物理現實 → 叢集層看是不是容量問題。反過來（看到 GPU 指標異常就開修）容易修一個不影響使用者的「問題」。

### 產品層

| 指標 | 定義 | 怎麼採 | 健康值 | 異常形態 |
|---|---|---|---|---|
| Availability | 成功請求比例；**串流場景下「成功」= 完整收完 stream**，不是 HTTP 200 | 不能只看 status code——SSE 開流後才死的請求，200 早就發出去了。要在 gateway/client SDK 層記 `finish_reason`（正常 stop vs 斷流）；vLLM 端對照 `vllm:request_success_total` 的 label | ≥ 99.9%（依產品 SLO） | 200 比例正常但斷流率上升 = 引擎在 stream 中途 OOM/被 preempt 殺掉（見 ch15），傳統 LB 健康檢查完全看不到 |
| Goodput@SLO | 單位時間內**滿足 SLO 的**請求（或 token）數。定義見本章後半 | 由請求層的 TTFT/ITL histogram 推導（PromQL 在下面） | 接近總吞吐（gap < 5%） | 總吞吐平穩但 goodput 下滑 = 系統「忙而無效」，最危險的退化形態，平均值儀表板上完全隱形 |

模型品質（答得好不好）也是產品層指標，但屬於 eval 與 canary gate 的範疇（見 ch15）；成本指標 $/Mtok 在 ch16。

### 請求層

四個延遲指標的關係先釘死，面試與報告都會用到：

```text
E2E = 排隊時間 + prefill 時間(≈TTFT − 排隊) + decode 時間
TTFT  = 請求送出 → 第一個 token        （使用者感知的「開始回應」）
ITL   = 相鄰兩個 token 的間隔          （每個 token 一個樣本）
TPOT  = (E2E − TTFT) / (輸出 token 數 − 1)（單一請求的 ITL 平均）
```

| 指標 | 定義 | 怎麼採 | 健康值（互動式 chat 的常見目標） | 異常形態 |
|---|---|---|---|---|
| TTFT | 含排隊 + prefill；server 端與 client 端要分開量，差值是 gateway/網路的「平台稅」 | server 端：`vllm:time_to_first_token_seconds`（histogram）；client 端：benchmark 工具或 SDK 埋點 | p95 < 1.5s（接 ch13 的 SLO 設定） | p99 先壞、p50 不動 = 排隊或 preemption；整條分布右移 = prefix cache hit 掉了（鑽引擎層）或 prompt 變長了 |
| ITL | token 間隔的逐 token 分布 | `vllm:inter_token_latency_seconds`（舊版叫 `time_per_output_token_seconds`，指標名隨版本演進，以你部署版本的 `/metrics` 輸出為準，2026-06） | p95 < 60ms（快過人類閱讀即可） | p99/p999 出現尖刺 = decode 被長 prefill 卡住（chunked prefill 預算太大，見 ch06）或被 preempt；**TPOT 平均會把這些 stall 抹平**，所以 ITL 分布不可省 |
| E2E | 請求進到最後一個 token | `vllm:e2e_request_latency_seconds` | 取決於輸出長度，無通用值 | 用來算 drain 預算（ch15）與 Little's law 驗證，不適合直接設 SLO |
| 排隊時間 | 引擎收到 → scheduler 排入 batch | `vllm:request_queue_time_seconds` | ~0（p99 < 100ms） | 持續 > 0 且增長 = 飽和的最早訊號，比任何 GPU 指標都早（你在遊戲後端見過同一個模式：佇列先於資源惡化） |

**ITL vs TPOT 值得多一句**：TPOT 是 per-request 平均，適合容量計算；ITL 是 per-token 樣本，適合抓體驗劣化。一個請求 256 個 token 裡有一次 2 秒的 stall（被 preempt 後 recompute），TPOT 只從 40ms 變成 48ms，看起來沒事；ITL p99 會直接打到 2s。使用者感受到的是那次卡頓，不是平均。

### 引擎層

這層是 vLLM `/metrics` 的主場（指標名以 2026-06 的 vLLM 文件為準）：

| 指標 | 定義 | 怎麼採 | 健康值 | 異常形態 |
|---|---|---|---|---|
| `vllm:num_requests_running` | 本輪 decode batch 裡的請求數 | gauge，直接抓 | 接近但不貼死 `max-num-seqs` | 貼死上限 + waiting > 0 = batch slot 是瓶頸；遠低於上限但 GPU 忙 = 單請求太肥（長 context 吃 KV） |
| `vllm:num_requests_waiting` | 引擎內部等待佇列深度 | gauge | ~0 | 持續增長 = 飽和；**這個佇列是無界的、不會自己回 429**（ch06），admission control 必須在 gateway 層（ch12） |
| `vllm:kv_cache_usage_perc` | KV cache block 使用比例（0–1） | gauge | 尖峰 0.6–0.85（經驗值） | 持續 > 0.9 = preemption 風險區；打到 1.0 後 preemption 啟動 → 尾延遲與吞吐同時惡化（死亡螺旋入口，防禦見 ch13） |
| Preemption 次數 | KV 不足時被踢出 batch 重排的請求數（`vllm:num_preemptions_total`，counter） | `rate()` 後看 | 0 | 任何持續非零值都該開 ticket；rate 突增 + KV util 100% = 立刻處理 |
| Prefix cache 命中率 | `rate(vllm:prefix_cache_hits[5m]) / rate(vllm:prefix_cache_queries[5m])` | 兩個 counter 相除 | 取決於流量形態：agentic 流量 60–90%+，無共享前綴的冷流量可能 < 10%（ch05） | **緩慢下滑**是經典隱性退化：deploy 重啟清空 cache、路由器親和性壞掉（ch10）、或流量結構變了。它直接放大 prefill 成本，下游症狀是 TTFT 整體右移 |
| Spec decode 接受率 | `vllm:spec_decode_num_accepted_tokens / vllm:spec_decode_num_draft_tokens` | counter 相除 | 視方案，EAGLE 類 60–80%（ch07） | 接受率掉 = 流量分布偏離 draft model 的訓練分布，spec decode 可能已經是負優化 |

### GPU 層（DCGM）

DCGM-exporter 的部署在 ch11（GPU Operator 全家桶）講過；這裡講欄位語意。先記住一個分界：**`DCGM_FI_DEV_*` 是傳統裝置層欄位，`DCGM_FI_PROF_*` 是 profiling 計數器**——精度高、支援 MIG，是你該用的。

| 欄位 | 定義 | 健康值（decode 為主的 serving） | 異常形態 |
|---|---|---|---|
| `DCGM_FI_DEV_GPU_UTIL` | 「取樣窗內**至少有一個 kernel 在跑**的時間比例」——就是 `nvidia-smi` 的 GPU-Util | 高負載下幾乎恆 90%+，**資訊量趨近於零**（下一節拆解） | 別用它做任何決策；不支援 MIG |
| `DCGM_FI_PROF_GR_ENGINE_ACTIVE` | compute engine active 的時間比例，GPU_UTIL 的高精度替代品 | 滿載 > 0.85 | 低 + 引擎佇列在長 = 引擎卡住而非容量不足（scheduler 卡死、NCCL hang，見 ch15） |
| `DCGM_FI_PROF_SM_ACTIVE` | 至少一個 warp 駐留的 SM 比例（對所有 SM 平均） | 滿載 > 0.8 | 注意：warp 在等記憶體也算 active——高 ≠ 在算東西 |
| `DCGM_FI_PROF_SM_OCCUPANCY` | 駐留 warp 數 / 理論上限 | decode 時中低是常態 | 用於 kernel 層分析（ch07），不是運維告警對象 |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | tensor core pipe active cycle 比例 | **decode 重時 10–25% 是物理，不是 bug**；prefill 突發時衝高 | 全天低且你的流量明明 prefill 很重 = 檢查 batch 與 chunked prefill 設定 |
| `DCGM_FI_PROF_DRAM_ACTIVE` | HBM 介面 active cycle 比例 | decode 重時 0.5–0.8，**高代表頻寬有被用起來**（ch02：decode 是 memory-bound，這是「健康的忙」） | 與 TENSOR_ACTIVE 同時低 + 引擎說自己很忙 = 各層指標矛盾，先懷疑量測 |
| `DCGM_FI_DEV_FB_USED` | framebuffer 已用記憶體 | 恆高——vLLM 啟動就按 `gpu-memory-utilization` 預占（ch08），**「GPU 記憶體用量高」永遠不是告警條件**，真訊號在引擎層 KV util | 比預期低 = 引擎沒起來或參數錯 |
| `DCGM_FI_DEV_POWER_USAGE` | 板卡功耗 | 滿載接近 TDP | 功耗是「有效工作量」的意外好代理：同 fleet 某卡功耗持續偏低 = 慢卡/掉頻/throttling，整池會被它拖慢（ch15 的隱性退化） |
| `DCGM_FI_DEV_GPU_TEMP`、throttle reasons | 溫度與降頻原因 | 視機型 | thermal throttle = 機房問題不是軟體問題 |
| `DCGM_FI_DEV_XID_ERRORS` | 最近一次 Xid 錯誤碼 | 0 | 非零直接進 ch15 的故障目錄查表；某些 Xid 該觸發自動 cordon（ch11） |

上面的「健康值」都是經驗量級起點，不是規範——你的模型、卡型、流量形態會移動這些數字；正確做法是用本章後半的 benchmark 替自己的系統建立 baseline。

### 叢集層

簡短帶過，機制都在前面的章節：pending GPU pods 與排程失敗原因（`kube-state-metrics`，ch11）、Kueue 的 pending workloads（ch11）、gateway/EPP 層的 pool 飽和度與 flow control 計數（GIE v1.5 的 pool-wide saturation gauge，ch12）、跨 replica 的負載與 cache 命中率方差（路由品質的直接證據，ch10）。叢集層指標回答的問題只有一個：「是不是該動容量了」——那是 ch13 的主題。

## SM utilization 的誤導性：把這件事一次講透

這是 GPU 監控最大的坑，值得專門一節。`nvidia-smi` 右上角那個 "GPU-Util"（= `DCGM_FI_DEV_GPU_UTIL`）的真實定義是：

> 在過去的取樣窗口內，**至少有一個 kernel 在 GPU 上執行**的時間比例。

注意它量的是「時間」，不是「算力」。H100 SXM 有 132 個 SM；一個只占用 1 個 SM 的 while-true spin kernel，會讓 GPU-Util 顯示 **100%**——機器實際上 99.2% 的算力在發呆。用你熟的世界類比：這等於一個 htop，只要 64 核裡有任何一核非 idle 就回報「CPU 100%」。你絕不會接受這種 CPU 指標，但整個業界的 GPU dashboard 預設擺的就是這個。

誤導有三層，一層比一層隱蔽：

1. **「有 kernel 在跑」≠「SM 都在跑」**。LLM serving 的 decode 迴圈幾乎每微秒都有 kernel 在 GPU 上，所以 GPU-Util 恆貼 100%——不管你的 batch 是 2 還是 200。它對「這張卡還有多少餘量」這個你最想問的問題，回答永遠是同一個數。修正：看 `DCGM_FI_PROF_SM_ACTIVE`（多少 SM 真的有 warp 駐留）。
2. **「SM 在跑」≠「在算東西」**。SM_ACTIVE 把「warp 駐留但 stall 在等 HBM」也算 active。ch02/ch03 證明過 decode 是 memory-bound：權重從 HBM 搬進來的時間遠大於計算時間。所以 decode 滿載的卡，SM_ACTIVE 高、`PIPE_TENSOR_ACTIVE` 只有一兩成——**這不是浪費，這就是 decode 的物理**。看到 tensor core 利用率低就去「優化」它，方向就錯了；該問的是 DRAM_ACTIVE 高不高（頻寬有沒有吃滿）。
3. **「在算東西」≠「在算有價值的東西」**。preemption 後的 recompute、本該命中 prefix cache 卻 miss 掉的重複 prefill、spec decode 被拒絕的 draft token——每一焦耳都真實燒掉了，DCGM 每個指標都顯示「忙」，但沒有任何一個 token 因此更早到達使用者。硬體指標在請求語意面前是全盲的。

所以分層的意義在此：**DCGM 告訴你硬體有沒有在動，引擎指標告訴你動得有沒有效率，產品指標告訴你效率有沒有變成使用者價值**。三層各自健康不代表整體健康，三層交叉才有診斷力：

| 症狀組合 | 診斷 |
|---|---|
| 佇列增長 + GR_ENGINE_ACTIVE 高 + DRAM_ACTIVE 高 | 真飽和：物理到頂了，去 ch13 擴容 |
| 佇列增長 + GR_ENGINE_ACTIVE 低 | 引擎卡住，不是容量問題：去 ch15 查故障 |
| 吞吐降 + preemption rate 升 + KV util 100% | KV 壓力：調 `max-num-seqs` 或加卡，別被「GPU 100%」騙去以為是算力不夠 |
| TTFT 右移 + prefix hit rate 掉 + GPU 指標全綠 | cache/路由退化：去 ch05/ch10，加卡完全無效 |

這跟你修 RDS 的經驗同構：CPU 100% 從來不告訴你是鎖競爭還是真工作，你當年靠 Performance Insights 的 wait event 分層才找到 SQL 重排的方向。DCGM 之於引擎指標，就是 CPU% 之於 wait events。

## 為什麼平均值說謊：histogram 設計

LLM 的延遲分布天生長尾且多峰：命中 prefix cache 的 TTFT 跟未命中差一個量級（ch05）、被 preempt 的請求跟沒被 preempt 的是兩個世界。對這種分布報平均值，等於把兩座山的海拔平均成一個不存在的丘陵。實務紀律：

- **TTFT 的 histogram bucket 要用對數刻度、跨四個量級**：50ms 到 60s。預設 bucket 如果頂在 10s，一次容量事故裡所有樣本掉進 `+Inf` bucket，`histogram_quantile` 會把 p99「夾」在最後一個 bucket 邊界上——dashboard 顯示 p99 = 10s 恆定，實際是 45s 還在惡化。這是 Prometheus histogram 最陰的失效模式：**指標看起來壞得「很穩定」的時候，先懷疑 bucket 溢出**。
- **ITL 要看 p99/p999 而不只 p95**：stall 事件（preemption、長 prefill 插隊）是稀疏的，p95 常常完全無感。
- 常用 PromQL（更多片段見附錄C）：

```promql
# TTFT p99
histogram_quantile(0.99,
  sum(rate(vllm:time_to_first_token_seconds_bucket[5m])) by (le))

# SLO 達成率:TTFT ≤ 1.5s 的請求比例(le 邊界要在 bucket 設計時就對齊 SLO!)
sum(rate(vllm:time_to_first_token_seconds_bucket{le="1.5"}[5m]))
  / sum(rate(vllm:time_to_first_token_seconds_count[5m]))
```

第二條就是 goodput@SLO 的 Prometheus 近似——前提是你設計 bucket 時就把 SLO 閾值放進 `le` 邊界。先定 SLO、再設 bucket，順序不能反。

## 實作棧：scrape、dashboard、告警

**Scrape**：vLLM pod 加 annotation 或 ServiceMonitor，15s interval 夠用（decode 是秒級動態，再密只是浪費 TSDB）。兩個紀律：(1) **label cardinality**——`model_name` 可以，per-user/per-request label 絕對不行，你在 CloudWatch 看過自訂指標維度爆炸的帳單，Prometheus 爆的則是記憶體；(2) counter 在 pod 重啟時歸零，所有 counter 一律包 `rate()`/`increase()`，永不裸用。

**Grafana dashboard 設計原則：一個面板回答一個運維問題。** 不是把所有指標倒上去，而是按診斷路徑排版：

| 面板（問題） | 指標 |
|---|---|
| 使用者現在痛嗎？ | TTFT p50/p95/p99、ITL p99、斷流率 |
| 在排隊嗎？ | `num_requests_waiting`、`request_queue_time` p99、gateway 429 率 |
| KV 有壓力嗎？ | `kv_cache_usage_perc`、preemption rate |
| Cache 還健康嗎？ | prefix hit rate（按 replica 拆開——方差大 = 路由問題） |
| 硬體在做什麼？ | GR_ENGINE_ACTIVE、DRAM_ACTIVE、功耗（按卡拆開找慢卡） |
| 容量還剩多少？ | running vs `max-num-seqs`、goodput vs 總吞吐 |

**告警的 page vs ticket 分界**（只列分界原則，處置 runbook 見 ch15）：page 的條件是「使用者正在痛或五分鐘內會痛」——SLO burn rate 超標、waiting 佇列持續增長、斷流率突增、preemption storm、Xid 致命錯誤；ticket 的條件是「趨勢不對但沒人在痛」——prefix hit rate 緩降、KV util 週趨勢上行、單 replica 功耗偏低、histogram 出現 `+Inf` 樣本。**平均值不准出現在任何告警條件裡。**

## Tracing 與日誌

**Tracing**：OTel 的 span 鏈路是 gateway → EPP 決策 → engine。設計重點：

- Span attributes 進 token 計數與路由決策：`gen_ai.usage.input_tokens`、`gen_ai.usage.output_tokens`（OTel GenAI semantic conventions，2026-06 仍在演進中，欄位名以當下 semconv 為準）、EPP 挑了哪個 pod、為什麼（cache 親和 vs 負載分）。
- **長 streaming 的 span 不要等 stream 結束才有資訊**：一條 span 活兩分鐘，期間 trace 上什麼都看不到。把 `first_token`、`queued`、`scheduled` 記成 span events，TTFT 直接從 event 時間差讀出來。
- 取樣策略：頭部取樣 1–10% 打底，錯誤與 SLO 違反的請求要 tail-based 全採——你要的是「慢請求的完整解剖」，不是均勻樣本。

**日誌的隱私現實**：prompt 是 PII，這在你以前的 API log 裡少見（你 log 的是 user id 和操作，不是使用者打的每一個字）。紀律：預設不 log prompt/completion 本文；除錯需要時用獨立的、短 TTL、強存取控制的儲存；要做 cache 分析就 log prefix 的 hash 而非原文；萃取管線在邊緣就 redact（你的 FluentBit + Lua 經驗直接上場——同一個 pipeline 形狀，filter 從「萃取指標」變成「先打碼再萃取」）。

## Benchmark 方法論

下半章換帽子：從「觀測生產」變成「製造可信的數字」。一個 benchmark 報告只有在三件事都誠實時才可信：**workload 真實、負載模型正確、統計處理乾淨**。逐一拆。

### Workload 真實性

LLM benchmark 的輸入空間比 HTTP API 大得多，三個維度都會大幅改變結果：

1. **Token 分布**：輸入/輸出長度不是平均數而是分布（生產流量通常重尾）。固定長度（`--ignore-eos` 強制生成到 max_tokens）讓容量計算乾淨、可重現；自然停止則更貼近真實 decode 行為。兩者數字可差 20%+，報告必須註明用哪種。
2. **Prefix 結構**：共享 system prompt、多輪對話、agentic 迴圈的前綴重複率決定 prefill 的真實成本（ch05）。用零共享前綴的合成資料測一個生產上 80% 命中率的系統，TTFT 會悲觀 2–5 倍；反之用單一 prompt 重複打，會樂觀到離譜。要嘛重放生產 trace，要嘛冷/熱兩組都測。
3. **到達過程**：均勻到達是不存在的流量。Poisson 是底線，真實 agentic 流量比 Poisson 更 bursty（一個 agent 平行 fan-out 數十個請求，見 ch17）。工具上：inference-perf 支援 Poisson/constant/trace replay，`vllm bench serve` 用 `--request-rate` 加 burstiness 參數控制（2026-06）。

### Open-loop vs closed-loop 與 coordinated omission

用你的 k6 語言講最快：

| | Closed-loop | Open-loop |
|---|---|---|
| k6 executor | `constant-vus`、`per-vu-iterations` | `constant-arrival-rate`、`ramping-arrival-rate` |
| Vegeta | （不適用——Vegeta 天生 open-loop） | `-rate` 旗標就是它 |
| 模型 | N 個 VU，各自「發請求→等回應→再發」 | 以固定速率發請求，**不管前面的回應回來了沒** |
| 並發 | 固定（= VU 數） | 浮動（= λ × W，Little's law） |
| 它模擬的世界 | 固定 worker 池（batch pipeline、有界並發的內部 agent fleet） | 互聯網使用者——**彼此獨立、不會因為伺服器慢就停止到來** |

Coordinated omission（Gil Tene 命名）是 closed-loop 的結構性謊言：伺服器一卡 10 秒，closed-loop 的每個 VU 就乖乖等 10 秒——這段期間它**少發了**本來會到達的請求。結果有兩重：(1) 樣本集裡「災難期間的請求」嚴重欠採樣，percentile 被沖淡；(2) 進攻方恰好在防守方最痛苦時收手——客戶端跟伺服器「協調」好了，故名。你的真實使用者不會協調：伺服器越慢，排隊的人越多。

LLM 把這個老問題放大兩個量級，因為**服務時間從 50ms 變成 5–300 秒**。Closed-loop 64 VUs 意味著引擎看到的並發被精準地夾在 64——佇列永遠是空的，KV 永遠不會被擠爆，preemption 永遠不會發生。你測的不是「這個系統在 35 req/s 下的行為」，是「這個系統在永不超過 64 並發的溫室裡的行為」。而生產環境的 35 req/s 是 open-loop 的：尖峰一來，並發直接衝過 KV 容量的牆。

誠實的補充：closed-loop 不是錯，是另一個問題的答案。「我的 agent pipeline 固定開 32 個 worker，能跑多快」就該用 closed-loop 測。罪不在 closed-loop，在**用 closed-loop 的結果回答 open-loop 的問題**——而容量規劃（ch13）問的幾乎都是 open-loop 的問題。

### Warmup 與穩態

冷啟動的引擎跟穩態的引擎是兩台機器：prefix cache 是空的、編譯快取沒熱、Python 層的配置器還在長大。紀律是：**先打 2–3 分鐘流量，整段丟棄，等指標穩定（prefix hit rate、KV util 走平）再開始計數**；每個量測點至少持續 3–5 分鐘，讓引擎佇列達到該負載下的穩態。順帶一個工具陷阱：`vllm bench serve` 的 `--request-rate` 預設是 `inf`——所有請求在 t=0 一次全部送出，那是在測「瞬間洪峰下的 batch 吞吐」，不是任何穩態（2026-06）。

### Latency-throughput frontier：怎麼跑、怎麼讀

單點數字（「9,000 tok/s！」）沒有意義，因為吞吐和延遲是一條曲線上的取捨（ch06 的 batch 數學決定的）。frontier 就是把這條曲線實測出來：

**怎麼跑**：
1. 固定 workload（資料集、token 分布、prefix 結構、seed）與引擎配置，全程不動。
2. Warmup，丟棄。
3. 以 open-loop 掃 offered rate：例如 2、4、8、16、24、30、35、40 req/s，每檔 5 分鐘。
4. 每檔記錄：實際達成吞吐、TTFT p50/p95/p99、ITL p95/p99、佇列深度、KV util、preemption 數。
5. 每檔做有效性檢查：**達成吞吐 ≈ offered rate** 才是有效點；達成 < offered 代表已過飽和點，該點只能標註「飽和」，不能當作「系統能跑這麼快」的證據。同時確認 client 不是瓶頸（k6 自己的 CPU、VU 池夠不夠大——下面的腳本註解會講）。
6. 畫圖：x 軸吞吐、y 軸各延遲分位數。

**怎麼讀**：曲線必然分三段——平坦區（負載低，延遲由服務時間主導，加負載近乎免費）、膝點（佇列開始形成，p99 先翹）、懸崖（飽和，延遲垂直起飛而吞吐不再增加）。三個讀法：(1) **比較兩個配置看整條曲線**，不看單點——A 配置峰值吞吐高 10% 但膝點早 30%，對線上服務是更差的配置；(2) 膝點位置就是 ch13 容量規劃的輸入；(3) p50 和 p99 的分岔點比膝點更早出現，是最靈敏的飽和前兆。

### Goodput@SLO：單一比較數字

frontier 是一條曲線，但決策常常需要一個數字。Goodput 的定義（源自 DistServe 論文對 serving 評測的修正）：

> **Goodput@SLO = 在滿足 SLO（例：TTFT p99 ≤ 1.5s 且 ITL p99 ≤ 60ms）的前提下，系統能持續達成的最大吞吐。**

操作上就是在 frontier 的每個量測點檢查 SLO 達成率，取「達成率 ≥ 目標（如 99%）」的最高一檔。它把「吞吐很高但人人都在等」的配置自動判死刑，是引擎調參（ch08）、架構比較（ch10）、容量規劃（ch13）共用的比較基準。兩個紀律：SLO 必須在跑 benchmark **之前**定好，否則你會不自覺挑出對自己有利的閾值；報告 goodput 必須同時報 SLO 定義，沒有 SLO 的 goodput 數字無法比較。還有一個容易踩的坑：**分位數本身是 SLO 的一部分**——本章的示範刻意用較嚴的 p99，而 ch13 的容量規劃題用的是 p95；同樣的閾值換個分位數就是另一個 SLO，跨章（或跨團隊）對照數字之前，先核對分位數。

### 工具選型（2026-06）

| 工具 | 它解什麼問題 | 什麼時候用 |
|---|---|---|
| `vllm bench serve` | 引擎自帶、零安裝，調參迴圈內的快速 A/B | 單機調 vLLM 參數時；注意 `--request-rate inf` 預設 |
| **AIPerf**（NVIDIA，genai-perf 的後繼，前者已停止新功能開發） | 全功能 client 端壓測：TTFT/ITL/吞吐/分位數，OpenAI-compatible 通吃 | 正式的跨引擎/跨配置評測報告 |
| **inference-perf**（kubernetes-sigs，WG Serving 出品，v0.5.0，2026-05） | 標準化、宣告式 config、goodput 原生支援、trace replay、高 QPS | K8s 環境的可重現基準、CI 迴歸（本人偏好：它的 config-as-code 形態最適合進版控） |
| **k6 + xk6-sse** | 你已有的整套 scenario/threshold/CI 整合，加上 SSE 能力 | 想複用既有 k6 資產、要測「gateway 到引擎全鏈路」而非裸引擎、要自訂計量邏輯時 |

### k6 SSE-aware 腳本骨架

xk6-sse 是社群擴充；現行 k6 可直接 `import sse from "k6/x/sse"` 自動解析，無需手動 xk6 build（以 k6 v1.2 世代驗證，2026-06）。骨架（可運行為目標，prompt 池與 threshold 自行補）：

```javascript
import sse from "k6/x/sse";
import { Trend, Counter, Rate } from "k6/metrics";

const ttft = new Trend("ttft_ms", true);
const itl = new Trend("itl_ms", true);
const e2e = new Trend("e2e_ms", true);
const outTokens = new Counter("output_tokens");
const streamOK = new Rate("stream_complete"); // 斷流率,不是 HTTP 狀態碼!

export const options = {
  scenarios: {
    open_loop: {
      executor: "constant-arrival-rate",   // open-loop:到達率與回應快慢無關
      rate: 8, timeUnit: "1s",
      duration: "5m",
      // 關鍵:xk6-sse 會阻塞 VU 直到 stream 結束,所以「VU 數=最大並發」。
      // 按 Little's law 配:需要的 VU ≈ rate × p99 請求時長。
      // 8 req/s × p99 30s = 240,再加安全係數。VU 不夠時 k6 會丟 dropped_iterations
      // ——那一刻你就退化回 closed-loop,數字作廢。盯著這個計數器。
      preAllocatedVUs: 400, maxVUs: 600,
    },
  },
  thresholds: {
    dropped_iterations: ["count==0"],      // open-loop 有效性的硬檢查
    ttft_ms: ["p(99)<1500"],
    itl_ms: ["p(99)<60"],
  },
};

export default function () {
  const payload = JSON.stringify({
    model: "meta-llama/Llama-3.1-8B-Instruct",
    messages: [{ role: "user", content: pickPrompt() }], // 從分布抽樣,別用同一條!
    max_tokens: 256,
    stream: true,
    stream_options: { include_usage: true }, // 拿真實 token 數
  });

  const t0 = Date.now();
  let started = false, tPrev = 0, completed = false;

  sse.open(`${__ENV.BASE_URL}/v1/chat/completions`, {
    method: "POST",
    headers: { "Content-Type": "application/json",
               Authorization: `Bearer ${__ENV.API_KEY}` },
    body: payload,
  }, (client) => {
    client.on("event", (ev) => {
      if (ev.data === "[DONE]") { completed = true; client.close(); return; }
      const now = Date.now();
      if (!started) { started = true; ttft.add(now - t0); }
      else { itl.add(now - tPrev); }   // 注意:這是 chunk 間隔的近似
      tPrev = now;
      const msg = JSON.parse(ev.data);
      if (msg.usage) outTokens.add(msg.usage.completion_tokens);
    });
    client.on("error", () => { /* 留給 streamOK 統計,別吞掉 */ });
  });

  streamOK.add(completed);
  if (completed) e2e.add(Date.now() - t0);
}
```

兩個誠實的註記：(1) **一個 SSE chunk 不保證等於一個 token**——引擎可能把多個 token 併進一個 chunk，所以 client 端 ITL 是近似值，真實 token 數要用 `usage` 欄位；精確的 ITL 分布以 server 端 `vllm:inter_token_latency_seconds` 為準，client 端數字拿來量「使用者實際感受」（含網路與中間件，這正是它的價值，見 ch12 的 proxy buffering 問題）。(2) xk6-sse 阻塞 VU 的特性使它不適合做超高並發（數千 stream）的壓測端——到那個量級換 inference-perf，或多台 k6 分散式。

### 效能迴歸防禦：benchmark 進 CI

你寫過 API 的迴歸測試；效能迴歸的難點在**雜訊**。紀律清單：

- 固定一切可固定的：同 GPU SKU、同 driver、鎖定 GPU clock（`nvidia-smi -lgc`，消除 boost 浮動）、固定資料集與 seed、固定引擎參數。
- 每次至少 3 輪取中位數；維護 baseline 的歷史方差，判定線設在「中位數偏移 > max(2σ, 3%)」之類的雙條件，而不是裸的百分比——單卡上 1–3% 的 run-to-run 雜訊是常態，拿 2% 偏移開 P1 是在訓練團隊忽略告警。
- 比較對象是 goodput@SLO 與 frontier 上的 2–3 個固定負載點，不是峰值吞吐。
- 結果存成結構化 artifact（JSON）進版控，迴歸發生時你要能 bisect 到 commit。

## Worked example：拆穿一個「看起來吞吐很高」的 benchmark

> 場景與數字為合成示意，量級對齊單卡 8B 模型的公開基準；重點是方法論差異的「形狀」，不是絕對值。

同事交來一份 benchmark 報告，結論很漂亮：

> 「Llama-3.1-8B（BF16）on 1×H100，k6 64 VUs 打 3 分鐘：**輸出吞吐 9,100 tok/s，平均 E2E 1.8s，平均 TTFT 350ms**。換算 35.5 req/s，扛住尖峰 5,000 並發只要 N 張卡，結案。」

workload：輸入 ~512 / 輸出 ~256 tokens。先做物理 sanity check（ch02/ch03 的方法）：decode 在 batch ~64 時，每 step 至少讀 16GB 權重，3.35TB/s HBM 下理論上限約 209 step/s × 64 ≈ 13k tok/s——9,100 在理論天花板的 70%，數字本身不假。**假的是它跟生產的關係。**三宗罪：

**罪一：closed-loop（64 VUs）**。35.5 req/s 不是輸入，是輸出——`64 VUs ÷ 1.8s = 35.5 req/s` 是 Little's law 的恆等式，系統再爛這個算式都會給出「系統剛好跟得上」的假象。並發被精準夾在 64：引擎佇列恆空、KV 從未承壓、preemption 為零。它測的是溫室，並且當引擎偶有卡頓時，VU 集體等待、到達率自動下降——coordinated omission，災難期欠採樣，percentile 被沖淡。

**罪二：無 warmup**。3 分鐘的 run 連穩態都沒進入：前 30 秒包含 prefix cache 全冷、64 個 VU 在 t=0 同時開火的 thundering herd。這些慢樣本都在資料裡——但因為只報平均值，被 256 個 token 的長 decode 稀釋到隱形。

**罪三：只報平均**。把他的原始資料拿來重算分位數：TTFT p99 = 1.6s，是平均值的 4.6 倍；ITL p99 = 95ms。如果產品 SLO 是 TTFT p99 ≤ 1.5s、ITL p99 ≤ 60ms，**這份報告自己的資料就已經不及格**，只是平均值替它遮住了。

修正後重跑：warmup 3 分鐘丟棄；prompt 從生產 token 分布抽樣（含 1.5k token 的共享 system prompt，模擬真實 prefix 命中）；open-loop Poisson 掃 rate，每檔 5 分鐘：

| Offered (req/s) | 達成 (req/s) | 輸出吞吐 (tok/s) | TTFT p50 / p99 | ITL p99 | KV util | waiting 佇列 |
|---|---|---|---|---|---|---|
| 8 | 8.0 | 2,050 | 120ms / 480ms | 38ms | 35% | 0 |
| 16 | 16.0 | 4,100 | 180ms / 850ms | 45ms | 55% | 0 |
| **24** | **24.0** | **6,150** | **310ms / 1.4s** | **56ms** | **74%** | 0–2 |
| 30 | 30.0 | 7,680 | 650ms / 3.8s | 72ms | 89% | 5–20，間歇 preemption |
| 35 | 33.6 | 8,600 | 2.9s / 19s | 88ms | 99% | 持續增長（飽和） |
| 40 | 34.1 | 8,730 | 8s+ / 45s+ | 95ms | 100% | 爆炸，preemption storm |

讀法：

- 系統的真實飽和點在 ~34 req/s——original 報告的 35.5 req/s 「結論」位於懸崖**之後**，那裡 TTFT p99 是 19 秒。closed-loop 之所以還能交出 1.8s 平均 E2E，正是因為它從不允許佇列形成。
- **Goodput@SLO（TTFT p99 ≤ 1.5s ∧ ITL p99 ≤ 60ms）= 24 req/s ≈ 6,150 tok/s**——比報告的 9,100 tok/s 低 32%。
- 容量規劃（ch13）該用的單卡數字是 24 req/s 再扣 headroom，不是 35。照原報告買卡，上線第一個尖峰就會把使用者推進 19 秒 TTFT 的世界，而且 dashboard 上的「GPU 利用率」全程 100%，顯得一切正常。

同一台機器、同一個模型，方法論的差異就是 32% 的容量誤判加一次線上事故。這就是為什麼 benchmark 方法論值得半章。

## 故障模式與防禦

本章的招牌段落這次照向自己：**觀測與量測系統本身**會怎麼壞。

| 故障 | 症狀 | 怎麼觀測到 | 防禦 |
|---|---|---|---|
| Histogram bucket 溢出 | 事故中 p99「穩定地」貼在某個整數上不動 | `+Inf` bucket 佔比 > 0 | bucket 上界 ≥ 最壞想像 × 3；對 `+Inf` 佔比設 ticket 告警 |
| Label cardinality 爆炸 | Prometheus OOM / 查詢逾時，恰好在你最需要它的事故當下 | TSDB head series 數量趨勢 | code review 把關 label；禁 per-user/per-request label |
| Counter 重啟歸零 | deploy 後 rate() 出現負尖刺或斷層 | 對照 pod restart 事件 | 一律 `rate()`，dashboard 不放裸 counter |
| DCGM-exporter 死掉 | GPU 面板變平線——**沒有資料常被誤讀成沒有問題** | `absent()` 告警 | 對每個 scrape target 設 absent 告警；缺資料 = 黃色，不是綠色 |
| 監控只看平均 | 一切正常，但客訴在升 | goodput vs 總吞吐的 gap | 告警與報告全面分位數化（本章通篇） |
| Benchmark client 自己是瓶頸 | 「延遲」隨並發線性惡化，但引擎指標顯示很閒 | k6 端 CPU、`dropped_iterations`；server/client 兩端 TTFT 差距拉大 | 監控壓測機本身；VU 池按 Little's law 配；必要時分散式 client |
| Closed-loop 冒充 open-loop | 數字漂亮且穩定得可疑；佇列與 preemption 恆零 | 報告裡找不到 offered vs achieved 對照 | 方法論 review：沒寫到達過程的 benchmark 一律打回 |
| 冷熱 cache 混比 | 兩次 run 差 40%，互相指責 | 對照 prefix hit rate 曲線 | 報告必附 hit rate;冷/熱分開測分開報 |
| Chunk 當 token 數 | client 吞吐比 server 端低一截 | 對照 `usage` 欄位與 chunk 計數 | token 計數一律以 usage / server 指標為準 |
| 中間件污染量測 | client TTFT 比 server TTFT 高出秒級 | 兩端同時量、取差 | 修 proxy buffering（ch12）；量測點標清楚在鏈路哪一層 |

通用原則：**觀測系統要用對待生產系統的標準對待**——它有自己的容量極限、自己的故障模式、自己的盲區，而它失效的時刻往往正是你最需要它的時刻（事故中 cardinality 爆炸、佇列堆積時 scrape 逾時）。

## 動手做

**Lab 1 [M1]：給模擬引擎建全套監控**
1. 跑 `llm-d-inference-sim`（暴露 vLLM 相容的 `/metrics`）+ Prometheus + Grafana（docker compose 三件組）。
2. 按本章「一個面板一個問題」的表建 6 個面板：TTFT p50/p95/p99、ITL p99、waiting 佇列、KV util、prefix hit rate、吞吐 vs goodput。
3. 用下面 Lab 2 的 k6 腳本打流量，調 sim 的延遲/容量參數製造「飽和」與「cache 退化」兩種事故。
4. **成功標準**：兩種事故都能在 dashboard 上 30 秒內定位到正確的層（飽和 → 佇列面板先動；cache 退化 → hit rate 先動、TTFT 後動），並能口頭說出診斷路徑。

**Lab 2 [M1]：k6 SSE benchmark 腳本**
1. 以本章骨架為底，目標打 Ollama（ch01 裝過）或 Lab 1 的 sim。
2. 實作 prompt 池抽樣、`dropped_iterations` threshold、冷/熱 cache 兩種模式。
3. 對同一目標各跑一次 closed-loop（`constant-vus`）與 open-loop（`constant-arrival-rate`），到達率對齊。
4. **成功標準**：能展示兩種模式下 p99 的差異並解釋成因；驗證 chunk 數 ≠ `usage.completion_tokens`。

**Lab 3 [租 GPU]：對真 vLLM 跑一條 frontier（估 $5–8）**
1. 租 1×H100 或 A100（2–3 小時），起 vLLM + Llama-3.1-8B-Instruct（ch08 的部署流程）。
2. Warmup 3 分鐘丟棄；用 inference-perf 或 Lab 2 腳本掃 6–8 檔 offered rate，每檔 5 分鐘；同步抓 `/metrics`。
3. 畫出 frontier（x = 吞吐，y = TTFT/ITL p99），標出膝點與飽和點；以 TTFT p99 ≤ 1.5s ∧ ITL p99 ≤ 60ms 算出 goodput@SLO。
4. **成功標準**：一張 frontier 圖 + 一個 goodput 數字 + 每個量測點的 offered vs achieved 對照表；能指出哪幾檔是無效點（飽和）。這張圖直接成為你作品集的素材（ch18）。
5. 用完即關，確認帳單。

## 自我檢核

1. `nvidia-smi` 顯示 GPU-Util 100%。說出至少三種彼此完全不同的真實狀況，以及你會各用哪個指標區分它們。
2. 寫出 TTFT、ITL、TPOT、E2E 的定義與關係式。為什麼 TPOT 平均正常時，ITL p99 仍可能在告警？哪種引擎行為會造成這個分岔？
3. 什麼是 coordinated omission？k6 的哪些 executor 會中招？為什麼 LLM 的長服務時間讓它比傳統 API 測試嚴重得多？
4. 描述跑一條 latency-throughput frontier 的完整步驟，包含每個量測點的兩個有效性檢查。
5. Goodput@SLO 的定義是什麼？為什麼它比峰值吞吐更適合做容量規劃輸入？它的兩個使用紀律是什麼？
6. `vllm:kv_cache_usage_perc` 是 95%——這健康嗎？你會再看哪兩個指標來決定要不要行動？
7. 為什麼 streaming API 的 availability 不能只用 HTTP status code 計算？正確的計法要在哪一層埋點？
8. CI 裡 benchmark 數字比 baseline 慢了 4%，你怎麼判斷這是迴歸還是雜訊？說出至少三個你會先檢查的「環境固定」項目。

## 延伸閱讀

- [vLLM Metrics 設計文件](https://docs.vllm.ai/en/latest/design/metrics/) — v1 引擎完整指標清單與設計取捨，本章引擎層指標的一手來源。
- [NVIDIA DCGM-Exporter 文件](https://docs.nvidia.com/datacenter/dcgm/latest/gpu-telemetry/dcgm-exporter.html) — 欄位定義與 K8s 部署；搭配 ch11 的 GPU Operator 脈絡讀。
- Gil Tene, ["How NOT to Measure Latency"](https://www.infoq.com/presentations/latency-response-time/) — coordinated omission 的原始佈道，所有做負載測試的人的必修課。
- [DistServe 論文（arXiv:2401.09670）](https://arxiv.org/abs/2401.09670) — goodput 作為 serving 評測目標的正式定義出處（它同時是 ch10 P/D 分離的學術源頭之一）。
- [inference-perf（kubernetes-sigs）](https://github.com/kubernetes-sigs/inference-perf) — WG Serving 的標準化 benchmark 工具，config-as-code 形態最適合進 CI。
- [AIPerf（ai-dynamo）](https://github.com/ai-dynamo/aiperf) — NVIDIA 的全功能 LLM 壓測 CLI，genai-perf 的後繼者。
- [xk6-sse](https://github.com/phymbert/xk6-sse) — k6 的 SSE 擴充，本章腳本骨架的依賴；README 直接以 LLM benchmark 為示範場景。
- [k6 文件：Open vs Closed 模型](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/) — 官方對兩種負載模型的解釋，對照本章的 LLM 放大版。
- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — LLM tracing 的屬性命名標準（2026-06 仍在演進中）。
