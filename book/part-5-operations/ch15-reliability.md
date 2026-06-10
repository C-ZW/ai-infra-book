# ch15 — 可靠性工程：當 GPU 叢集開始壞

> **本章解決什麼問題**：ch02 給過你故障目錄的入門版、ch09 立了 NCCL hang 的牌子、ch11 留了 DCGM 自動隔離與 drain 數學的坑、ch12 欠你 retry budget 與「品質迴歸在 5xx 看不到」的完整答案——本章一次清償。內容是生產級 LLM 服務的完整故障目錄與防禦工事：健康檢查、graceful drain 的數學、發布工程、流量災難、incident runbook、混沌演練。指標定義在 ch14、autoscaling 與死亡螺旋在 ch13，本章假設你已經量得到，回答的是「壞了怎麼辦、怎麼讓壞得不那麼難看」。這是全書 Murphy 濃度最高的一章。

## 從你已知的出發

你做過 500K+ 使用者遊戲後端的高可用維運：on-call、graceful shutdown、RDS failover 演練、SQS consumer 的重試與冪等。這些肌肉記憶全部有效——但有三個物理常數變了，每一個都會讓照搬的 SOP 出事：

1. **硬體故障從「被雲端藏起來」變成「你的日常輸入」**。EC2 的 hypervisor 替你吞掉了壞磁碟與壞記憶體，你六年職涯大概沒看過一次真正的硬體故障。GPU 節點沒有這層溫柔：卡會從 PCIe 上消失、HBM 會翻位元、NVLink 會退化。ch02 引過 Meta 的數據：Llama 3 訓練（16,384 張 H100、54 天）有 419 次非預期中斷，約 78% 歸因硬體；Meta 另一份對自家研究叢集 11 個月、1.5 億 GPU 時的分析給出 **每千節點日約 2.3 次故障** 的量級（arXiv:2410.21680）。換算你未來管的 64 卡推論機隊（8 台 8 卡節點）：**硬體事件的期望值大約每月 0.5~1 次，軟體與引擎層事件更頻繁**。這不是異常，是輸入條件——架構必須假設「永遠有一個節點正在壞」。
2. **請求時長 ×100，所以一切「等它做完」的操作也 ×100**。你寫過 Node.js 的 graceful shutdown：停收新連線、等 in-flight、15~30 秒收工。同樣的模式在這裡完全成立，但一條 streaming 請求可以跑十分鐘——drain 預算從秒級變成十分鐘級，rolling deploy 從十分鐘變成數小時。本章中段用一個 worked example 把這筆帳算給你看。
3. **故障的可見性反轉了**。你習慣的世界裡「壞 = 錯誤率上升」，dashboard 看 5xx 就抓得到八成的事。這裡最貴的三類故障**全部不報錯**：NCCL hang 時 GPU util 卡在 100%（spin-wait 也是 util，ch09）；模型變笨時每個回應都是 HTTP 200；thermal throttling 讓卡無聲變慢、零錯誤。監控哲學要從「抓錯誤」轉成「抓背離」——util 高但 token 輸出歸零、回應全成功但輸出長度分布漂移、同機隊其他卡都比它快。這是你 FluentBit 指標管線經驗的進階版：訊號還在，但藏在比值與分布裡，不在錯誤碼裡。

把這三條想清楚，本章每個機制都是在防禦其中一條。

## 故障目錄：GPU 服務的疾病分類學

先上大表再深挖四個重點。表格按「硬體 → 平台 → 引擎 → 隱性」排列——越往下，偵測越難、平均存活時間越長、累積傷害越大：

| # | 故障 | 症狀長什麼樣 | 根因 | 偵測訊號 | 緩解 |
|---|---|---|---|---|---|
| 1 | CUDA OOM（啟動期） | pod 起不來，log 見 `CUDA out of memory` | `gpu-memory-utilization` 設太高、同卡有殘留 process、模型/context 帳算錯（ch03） | CrashLoopBackOff + 啟動 log | 部署前用 ch03 公式驗算；確認卡上無殭屍 process；留 5–10% headroom |
| 2 | CUDA OOM（執行期） | 跑了幾小時～幾天後突然 OOM；「要 2GB、明明有 3GB free」 | KV pool 之外的配置（activation、CUDA graph、NCCL buffer）碎片化；或記憶體緩慢洩漏 | HBM 用量的長期斜率（DCGM）；PyTorch allocator 統計 | `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`；斜率告警；排程性滾動重啟（見 drain 一節——這要付 deploy 稅） |
| 3 | ECC 不可修正（Xid 48，伴隨 63/64 row remapping） | 在跑的 process 被殺；同卡反覆發生 | HBM cell 退化 | dmesg Xid 流；DCGM ECC 計數器；retired pages 趨勢 | **自動 cordon + drain**；remap 資源用罄或一週內重發 → RMA |
| 4 | 掉卡（Xid 79，fallen off the bus） | `nvidia-smi` 報 unable to determine device handle，GPU 從 PCIe 消失 | 供電、riser、過熱、卡本體 | dmesg；node exporter | **自動 cordon**；重啟主機；重複發生 → 換機 |
| 5 | NVLink 錯誤（Xid 74） | TP 組整體變慢或 NCCL 偶發報錯；單卡指標正常 | 鏈路/bridge 硬體退化 | DCGM NVLink 錯誤計數器 | 計數突增 → cordon；見 NCCL runbook |
| 6 | GSP RPC timeout（Xid 119/120） | driver 操作卡死、`nvidia-smi` 掛起 | GPU 內部管理核心（GSP firmware）無回應 | dmesg | 重啟節點；反覆發生查 driver/firmware 版本，必要時依 NVIDIA 指引停用 GSP |
| 7 | 應用層錯誤（Xid 13/31） | kernel exception / page fault，process 死但卡是好的 | 引擎或 kernel 的軟體 bug、版本不相容 | dmesg + 引擎 crash log | **別 RMA**——先查引擎/driver 版本矩陣；可在原節點重啟 |
| 8 | NCCL hang / timeout | 整個 TP/EP 組 util 100%、token 輸出歸零、無 error log | 一個 rank 死亡或 desync，其餘 rank 在 collective 裡永遠等 | tokens/s 與 util 的背離；watchdog timeout log | 詳見下文：timeout 調小、深健康探針、整組重啟 |
| 9 | Driver/firmware 版本矩陣 | 升級後零星 Xid、效能退化、或根本起不來 | driver × CUDA × NCCL × 引擎的相容矩陣踩錯格 | 升級事件與故障率的相關性 | 版本組合當 artifact 管理；金絲雀節點先升；保留回退路徑 |
| 10 | Thermal / power throttling | **無聲變慢**：tok/s 下滑、零錯誤、無 Xid | 散熱不良、供電上限、機房熱點 | `nvidia-smi -q -d PERFORMANCE` throttle reasons；DCGM 時脈/溫度；同機隊橫向對比 | 時脈納入常規監控；持續 throttle → cordon 並查機房 |
| 11 | 節點 NVMe 被權重快取塞爆 | pod evicted、image pull 失敗、`DiskPressure` | 權重快取無淘汰機制（ch12） | node filesystem 使用率 | LRU 淘汰 + 容量配額 + 提前告警 |
| 12 | 引擎 scheduler 卡死 | running > 0 但 token 輸出歸零；非 NCCL（單卡也會） | 引擎 bug、事件迴圈死鎖 | 「有 running 卻無輸出」的背離指標；深健康探針 | 探針觸發 cordon + 重啟；蒐集 stack dump 回報 upstream |
| 13 | Sequence 洩漏 | running 數只升不降，KV 利用率單調上升，最終 preemption 風暴 | client 斷線未傳播成 abort（ch12）、或引擎釋放 bug | gateway 連線數 vs 引擎 running 數的背離 | 斷線傳播 abort；對 stream 設 max duration 硬上限 |
| 14 | Prefix cache hit rate 衰退 | TTFT 緩慢爬升、無錯誤、容量「莫名」變緊 | 路由變更、deploy 清空 cache、流量 mix 漂移（ch10） | hit rate 的趨勢告警（不是閾值告警） | 變更前後對比 hit rate；路由 scoring 回歸測試 |
| 15 | 慢 replica 拖累全池 | 全池 p99 變差，但平均正常 | 某 pod 所在卡 throttling、鄰居搶資源、或單 pod 退化 | **per-pod** 延遲分布的離散度（ch14） | 自動摘除離群 pod；EPP 把延遲納入 scoring |
| 16 | 品質迴歸 | 5xx 全綠、延遲正常、用戶投訴「變笨了」 | 量化切換、chat template/tokenizer 變更、sampling 預設漂移、壞 LoRA | eval gate 分數、輸出分布指標（見發布工程一節） | 權重/config/引擎一律過 canary + eval gate |

四個值得展開的重點：

### CUDA OOM：三種根因，三種處置

「OOM」這個詞在 vLLM 世界有個反直覺之處：**穩態的 KV cache 不會 OOM**。引擎啟動時就把 `gpu-memory-utilization` 指定的記憶體圈成 KV pool（ch05/ch06），請求多到裝不下時的行為是 preemption 與排隊，不是 OOM。所以真的看到 CUDA OOM，根因幾乎都在 pool 之外：（a）**啟動期帳算錯**——權重 + activation 峰值 + CUDA graph + NCCL buffer 超過實體容量，這是配置 bug，用 ch03 的公式重算；（b）**碎片化**——PyTorch caching allocator 的碎片讓「總量夠但連續塊不夠」，症狀是那句經典的「tried to allocate X but…」，`expandable_segments` 能緩解大半；（c）**緩慢洩漏**——HBM 或 host RSS 以每天幾百 MB 的斜率爬，幾天後撞牆。第三種最陰險，因為唯一可靠的緩解是定期重啟，而你看完 drain 一節就知道：**LLM 服務的「重啟一輪」是以小時計價的**——洩漏修不掉的話，這筆稅每週都要繳。

### Xid 家族：讀 dmesg 的紀律

Xid 是 GPU 世界的 errno（ch02），on-call 的紀律是一張三分法的表：**該換硬體的**（48 反覆、79、62/64 反覆、95）、**該先怪自己軟體的**（13、31、43——先查引擎版本與相容矩陣，別急著 RMA）、**該看趨勢不看單點的**（94 單位元 ECC 每月幾次是正常背景輻射；63 retired pages 的計數加速才是警訊）。自動化的對應原則：**只有第一類接自動 cordon**。把 13/31 也接上自動隔離，一個引擎 bug 就能讓你的自動化把整個叢集 cordon 光——本章最後的「防禦工事自身的故障」會回來鞭打這一點。

### NCCL hang：多卡世界最痛的故障

ch09 立過牌子，這裡交工事。為什麼它是最痛的：TP/EP 組裡**一個 rank 出事（OOM、crash、被 preempt、網卡抖動），其餘 rank 會在 collective 裡無限期等待**——NCCL 的同步語意沒有內建補償。症狀的三重欺騙：GPU util 100%（spin-wait）、無 error log（沒人報錯，大家都在等）、process 全部活著（liveness 探針全綠）。對「看指標找問題」的直覺是全反向的。

防禦工事三件套：

1. **把 timeout 從預設調到推論的時間尺度**。PyTorch 的 ProcessGroupNCCL watchdog 預設 collective timeout 是 **10 分鐘**（PyTorch 文件，2026-06）——這是給訓練的寬容度。推論的 decode collective 是毫秒級的事，任何一次 all-reduce 跑超過 30 秒就是死了，等剩下的 9.5 分鐘只是在燒卡與燒 SLO。把分散式 timeout 調到 30~120 秒；引擎是否把它暴露成旗標各家不一（SGLang 有 `--dist-timeout`；vLLM 以當下版本的環境變數與程式碼為準，部署前實測你的版本會不會在 timeout 後乾淨地 crash 而不是殭屍化）。
2. **偵測靠背離，不靠錯誤**：`tokens/s == 0` 且 `running > 0` 且 `GPU util > 90%` 持續 60 秒，就是 hang 的指紋——這條告警規則比任何 log 都早知道。再加深健康探針（下一節）兜底。
3. **故障域 = 整組**。TP4 的四個 pod 是一個生死與共的單位：殺一個、留三個，留下的三個還是僵的。處置永遠是整組摘流量、整組重啟（LWS 的組級故障語意就是為這個存在的，ch11）。驗屍工具：PyTorch 的 **Flight Recorder** 會在 timeout 時 dump 每個 rank 最後執行的 collective 與 stack trace，能直接看出「誰缺席」或「誰跟大家叫了不同的 collective」。順帶一個有用的 fleet 經驗：PyTorch 維護者公開說過，他們機隊裡絕大多數 watchdog timeout 的根因是 **desync（集合呼叫不匹配）而不是真的慢**——所以調大 timeout 幾乎從來不是解法。

### 隱性退化：最貴的一類

表中 14~16 共享同一個性質：**沒有事件，只有趨勢**。prefix hit rate 每週掉 2%、某 replica 比同儕慢 15%、輸出平均長度悄悄變短——每一項單看都不值得 page，累積三個月就是 30% 的容量蒸發或一次公關事故。防禦不是更多告警，是**三類例行對比**：時間軸對比（本週 vs 上週的關鍵比值）、同儕對比（per-pod 指標的離散度，抓離群者）、變更對比（每次 deploy 前後的指標 diff）。另外留一句 hedge：大規模機隊還有 silent data corruption（算錯但不報錯）的長尾風險，Meta 等公司有公開研究，但對推論服務的實務影響截至我能確認的資訊（2026-06）仍缺乏好的公開數據——eval gate 與輸出分布監控是目前唯一務實的網。

## 健康檢查：你怎麼知道它還活著

K8s 三種 probe 你閉著眼睛會配，但預設直覺在「載入要十分鐘、活著不代表能生成」的引擎上全是坑。

### startup / liveness / readiness 對長載入引擎

```yaml
# 示意：vLLM Deployment 的 probe 配置（語意為主，路徑與旗標以你的版本為準）
containers:
- name: vllm
  startupProbe:                 # 罩住冷啟動：權重載入＋compile 可達分鐘級（ch12）
    httpGet: { path: /health, port: 8000 }
    periodSeconds: 10
    failureThreshold: 120       # 10s × 120 = 容忍 20 分鐘啟動，照你實測的 p99 冷啟動設
  livenessProbe:                # 淺探針：只問「process 與事件迴圈活著嗎」
    httpGet: { path: /health, port: 8000 }
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 3
  readinessProbe:               # 接不接新流量：drain 就是把它翻成 false
    httpGet: { path: /health, port: 8000 }
    periodSeconds: 5
    failureThreshold: 2
terminationGracePeriodSeconds: 960   # 必須 ≥ drain 預算（下一節的數學）
```

三個必須答對的設計題：**startup probe 不設或設太短**，liveness 會在權重載入到一半時殺掉 pod，pod 重啟又從頭載入——你會得到一個永動的 CrashLoop，症狀是「pod 永遠 87% 就死」，根因是 probe 而不是程式。**liveness 必須淺**：它只該驗證「HTTP server 與引擎迴圈有心跳」，絕不可驗證「能生成 token」——理由見下。**readiness 是流量閥門**：它是 drain 與 brownout 的執行機構，語意是「我願不願意接新請求」，跟「我健不健康」是兩個問題。

### 深健康探針：生成一個 token 才算活著

淺探針抓不到本章最痛的三種死法：NCCL hang（process 活著）、scheduler 卡死（HTTP 還回 200）、隱性變慢。唯一可靠的「活著」定義是**端到端走完一次生成**：

```bash
# 深健康探針：真的生成 1 個 token，走完 tokenize→schedule→prefill→decode→detokenize 全路徑
curl -s -m 15 localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"prod-70b","messages":[{"role":"user","content":"ping"}],"max_tokens":1}'
```

但深探針有一個會炸全池的反模式：**把它接到 liveness 上**。推演一次 Murphy：流量尖峰 → 佇列變長 → 探針請求也在排隊 → 探針超時 → liveness 失敗 ×3 → K8s 重殺 pod → 容量更少 → 其他 pod 更擠 → 它們的探針也超時——**健康檢查親手執行了一場級聯故障**，而且是在你最忙的時候。深探針把「忙」誤判成「死」的代價是全池重啟。正確接法：深探針是**獨立的 prober**（每 30~60 秒一輪），結果進 metrics，觸發的是**告警與自動摘流量（cordon 該 pod）**，不是重啟；探針超時閾值要遠鬆於 SLO（SLO 的 3~5 倍），因為它的職責是分辨死活，不是量品質——量品質是 ch14 的 SLO 監控的事。

節點級的那一層（DCGM 持續健康檢查 → Xid/ECC 觸發 cordon + drain）ch11 已經給過迴路，本章補的是政策：**哪些訊號接自動、哪些留給人**——上面 Xid 三分法就是答案，再加一條全域保險：自動 cordon 要有速率上限（例如每小時最多 2 個節點），超過就停下來叫人，因為「自動化以為全叢集都壞了」的最常見原因是自動化自己壞了。

## Graceful drain 的數學：為什麼 deploy 以小時計

模式你熟到不用教：摘除 endpoint → 停收新請求 → 等 in-flight 跑完 → 才送 SIGTERM。LLM 的特殊性只有一條，但它改變一切：**in-flight 請求不可轉移**。你的無狀態 API 可以讓 LB 把連線換到別台；這裡一條 stream 的 KV cache 黏在這張卡的 HBM 裡（ch05），中途換 pod = 重算全部。所以 drain 沒有捷徑，只能等——問題變成：**等多久**？

### Worked example：drain 預算與 rollout 時長

設定：chat + 部分 agentic 流量的服務，24 個 vLLM pod，穩態每 pod 約 **48 條 in-flight** 請求。你照 ch14 的方法量到 E2E 請求時長分布：

| 分位 | p50 | p90 | p95 | p99 | p99.9 | 硬上限（gateway max stream duration） |
|---|---|---|---|---|---|---|
| 時長 | 6 s | 25 s | 45 s | 120 s | 420 s | **900 s** |

**第一步：單 pod 的 drain 時長是「48 個樣本的最大值」，不是中位數。** 這是大多數人算錯的地方。停收新請求後，pod 清空的時間 = 最慢那條 in-flight 的剩餘時長。保守地拿完整時長分布當剩餘時長的上界（悲觀但安全），假設近似獨立，則「t 秒內清空」的機率是 F(t)⁴⁸：

- 等到 p99（120 s）：0.99⁴⁸ ≈ **0.62**——38% 的 pod 還有人在跑。直覺上「等 p99 夠久了吧」，但 48 條請求的最大值天然集中在分布尾部：你要的不是 p99，是大約 p(1 − (1−q)/48) 這一階的分位數。
- 期望被砍的請求數 = 48 × (1 − F(t))，每 pod：等 30 秒砍 ~3.8 條、等 120 秒砍 ~0.48 條、等 420 秒砍 ~0.05 條、等 900 秒砍 0 條。

全量 rollout（24 個 pod）的期望傷亡：

| drain 截止 | 30 s（K8s 預設 grace period！） | 120 s（p99） | 420 s（p99.9） | 900 s（硬上限） |
|---|---|---|---|---|
| 整輪被砍的 stream 數 | **~92 條** | ~11.5 條 | ~1.2 條 | 0 |

第一個 punchline：**拿 K8s 預設的 30 秒 `terminationGracePeriodSeconds` 滾一輪，等於默默砍掉近百條正在輸出的對話**——而且 5xx 看不到（stream 已是 200，只會斷流，ch12）。第二個：**零傷亡的前提是 gateway 有 max stream duration 硬上限**。沒有上限，p100 在數學上是無界的，drain 預算也是——900 秒這個 cap 不是品質設計，是可運維性設計。

**第二步：rollout 時長。** GPU 稀缺，你租不到 25% 的 surge 容量，假設只有 2 張備卡 → maxSurge=2，12 個批次。surge 模式下每批可以平行做「起新 pod（warm path 冷啟動 ~3 分鐘，ch12）＋ bake 觀察 5 分鐘」與「舊 pod drain」，所以每批耗時 ≈ max(8 分鐘, drain 截止)：

| drain 截止 | 每批耗時 | 12 批 | + 首批 canary bake（eval gate，30–60 分） | 總計 |
|---|---|---|---|---|
| 120 s | 8 min | 96 min | +30~60 min | **~2~2.5 小時** |
| 420 s | 8 min（drain 7 分 < bake 8 分，**免費**） | 96 min | +30~60 min | **~2~2.5 小時** |
| 900 s | 15 min | 180 min | +30~60 min | **~3.5~4 小時** |

第三個 punchline 藏在中間那行：**從 p99 等到 p99.9 幾乎不增加 rollout 時間**（drain 被冷啟動＋bake 的 8 分鐘遮蔽了），卻把傷亡從 11.5 條降到 1.2 條——「捨不得等」是假節省。最後把結論收攏：一個 24 pod 的 LLM 服務，認真做 drain 與 canary 的 deploy 就是 **2~4 小時起跳**。這個數字會反過來改變你的上游決策：hotfix 流程要有「值不值得滾一輪」的門檻、記憶體洩漏的「重啟即解」每週繳一次 2 小時稅、incident 時 rollback 不能靠重新 rollout（下一節的熱回退）。

工程落地的兩個注意：`terminationGracePeriodSeconds` 必須 ≥ drain 截止 + 清理緩衝（上例 960 s）；drain 的「停收新請求」要做在路由層（EPP 摘 endpoint / readiness 翻 false），preStop hook 只負責等待——它不是魔法，只是把「摘流量」與「SIGTERM」解耦的時間差。引擎自身的 shutdown 語意截至 2026-06 還在標準化中（vLLM 有一篇 RFC 明確提案「SIGTERM 後停收新請求、in-flight 在可配置的時限內跑完、P/D 場景等 KV 傳輸完成」，尚未完全落地）——所以生產上的 drain 主力放在路由層，別賭引擎的訊號處理。

## 發布工程：canary 的對象不只程式碼

你的 canary 直覺：新版本接 5% 流量，盯錯誤率與延遲，正常就推進。框架照搬，但有兩個 LLM 特有的修正。

**第一，canary 的對象清單變長了。** 會改變服務行為的 artifact 至少有六種：引擎版本、模型權重、量化格式、sampling 預設值、chat template/tokenizer、LoRA adapter。每一種都該走同一條 canary 管線——歷史事故裡「沒人覺得這算 deploy」的變更（換了個量化 checkpoint、改了 chat template 的一行 Jinja）出事率不輸程式碼。配套是**熱回退**：權重是 70 GB 的 artifact，冷回退要重走分鐘～小時級的載入（ch12），所以 bake 期間舊版本池必須保持 warm——回退是秒級的路由切換，不是重新部署。

**第二，品質迴歸在 5xx 看不到。** 模型變笨不報錯：量化讓數學題錯誤率翻倍、template 錯位讓模型開始自言自語、tokenizer 版本差一個 special token 讓輸出夾雜亂碼——HTTP 層全是 200，延遲還可能更快。你在錯誤率 dashboard 上看到的 canary「全綠」，對品質是零證據。兩道網：

- **Eval gate（部署前的硬門檻）**：一組 golden set（幾百到一千條帶預期答案的 prompt，覆蓋你的核心場景＋歷史事故回歸題），對 canary 池跑一輪，分數低於基準線即自動擋下。可自動評分的任務（exact match、單元測試、結構化輸出 schema 驗證）優先；開放式回應用 LLM-as-judge 補位，但 judge 自己也是個會退化的模型——分數要看相對 diff 而不是絕對值。把它想成「模型的整合測試」，進 CI，跟 ch14 的效能迴歸 benchmark 並排跑。
- **Shadow traffic（部署中的分布監控）**：鏡像一部分真實流量到 canary（回應丟棄不回給用戶），離線對比新舊版本的**輸出分布指標**——平均輸出長度、refusal 率、重複率、`finish_reason` 分布、特定關鍵詞頻率。這些指標不需要 ground truth，卻對「模型行為變了」極其敏感。代價誠實列出：shadow 的每一條請求都是真 GPU 錢（鏡像 10% 流量 = 容量帳加 10%，ch16），所以用採樣而不是全量，並且 shadow 池可以用更小的副本數換更長的觀察窗。

## 流量災難：retry storm、brownout、佇列崩潰

### Retry storm 的 LLM 加強版

你在遊戲後端見過 retry storm。LLM 版本的放大係數高一個量級，因為三件事疊加：**重試的單位貴**（一次重試 = 重算整段 prefill，分鐘級、數萬 token 的計算）；**斷流即重試**（pod 死掉時上面 48 條 stream 同時斷，48 個 client SDK 同時重試，而且帶著完整的長 context）；**重試打中的是已經變慢的池子**（pod 少了一個，倖存者更擠 → 更多 timeout → 更多重試）。推演一次：8 pod 的池子死 1 個，瞬間 48 條重試湧向剩下 7 個——每條都是全量 prefill，等效於突然多了 7% 的最重型流量，落在一個剛損失 12.5% 容量的池子上。沒有防禦的話，這就是 ch13 死亡螺旋的點火器。

防禦工事，由近及遠：

1. **位置敏感的重試政策**（ch12 立的規則，這裡是執行細節）：首 token 前可重試、首 token 後預設不重試。配 **retry budget**——重試流量不得超過基準流量的 10%（按 token 計，不是按請求計，否則一條 128k context 的重試會吃掉 50 條短請求的額度）；budget 用罄就 fail fast。
2. **服務端不能信任 client**：你的 429 + `Retry-After` 是君子協定，第三方 SDK 不一定理你。額度要在 gateway 強制執行（per-tenant token bucket，ch16），超過的直接拒絕而不是排隊。
3. **斷流續傳是治本但少有人做**：原理上 server 端把已生成的 token 留存一個短 TTL，client 帶 resume token 重連時從斷點續發（SSE 的 `Last-Event-ID` 語意），重試成本從「重算全部」降到「重發已算的」。截至我能確認的資訊（2026-06），主流 open-source serving 棧沒有開箱即用的實作，這是平台層的自建題——值不值得做，取決於你的 stream 平均長度與斷流率的乘積。
4. **Priority shedding**：過載時丟棄要有順序——batch tier 先死、免費 tier 次之、付費互動流量最後（優先級從 gateway 的 tenant metadata 來，ch12/ch16）。「全體變慢」是最差的丟法，它讓所有人都超時、所有人都重試。

### Brownout：有秩序的降級

掉電（blackout）之前先調暗（brownout）：與其讓佇列崩潰，不如主動降低每請求成本換容量。LLM 服務的可調槓桿比一般後端豐富得多：

| 槓桿 | 容量收益 | 品質/體驗代價 | 備註 |
|---|---|---|---|
| 降 `max_tokens` 上限（如 4096→1024） | decode 佔用下降、佇列周轉加快 | 長輸出被截斷 | 對 reasoning 流量收益最大 |
| 降 max context / 拒收超長 prompt | KV 佔用大減（ch03 的線性帳） | 長文件場景退化成 422 | KV 壓力型過載的首選 |
| 關 speculative decoding | 釋放 draft + verify 的算力與記憶體 | 低載時 ITL 變慢 | 高 batch 時本來就收益遞減（ch07），過載時關掉接近免費 |
| 關 thinking mode / 砍 thinking budget | 輸出 token 數大減 | 複雜任務品質下降 | 對 reasoning 重的產品要產品側同意 |
| 切到小模型 / 更激進量化的備池 | 每請求成本砍半以上 | 品質明顯下降 | 需要預先存在的備池與路由開關 |
| Priority shedding（上節） | 立即、可控 | 對應 SLA 設計好就「無代價」 | 永遠是第一個拉的 |

兩條紀律比槓桿本身重要。**進出都要遲滯（hysteresis）**：進入條件（例如 KV 利用率 > 90% 持續 5 分鐘，或 SLO burn rate 超標，訊號定義見 ch13/ch14）與退出條件（回落到 70% 以下持續 10 分鐘）之間要有足夠的間隙，否則系統在邊界上抖動，用戶體驗到的是「時好時壞」——比穩定的差更糟。**brownout 必須是宣告式的狀態機，不是人手改 config**：凌晨三點拉閘的 on-call 不會記得早上把它關回去；狀態要進 metrics、變更要進 audit log、退出要自動。

### 佇列崩潰與殭屍請求

admission control 的位置（最前面的 gateway）與死亡螺旋的動力學分別在 ch12 與 ch13，這裡只補 incident 現場的一個關鍵事實：**當佇列等待時間超過 client timeout，佇列裡全是殭屍**——client 已放棄、重試已在路上，但引擎還在認真處理沒人要的請求，goodput 歸零而 GPU 滿載。這時「等它消化完」在數學上不成立（消化速度 < 殭屍生成速度），唯一的恢復操作是**大規模丟棄**：清空 waiting 佇列、必要時 abort 掉超齡的 running 請求。清要清得狠——半清等於沒清，殘留的殭屍會繼續佔住 batch slot 讓新請求也變殭屍。這是 on-call 手冊裡最反直覺、也最需要事先寫下來的一條：丟棄不是事故的失敗，是恢復的開始。

## 多區域：failover 的 RTO 現實

三個 LLM 特有的修正，修正你既有的 DR 直覺。**權重要預熱**：failover 不是把流量切過去就好，對端的每個節點得有權重（NVMe 快取或區域內物件儲存副本）——讓 50 個 pod 在 failover 當下同時去拉 S3，你會在最糟的時刻重演 ch12 的擴容風暴。**KV 不可遷移**：切換瞬間所有 in-flight stream 斷掉、所有 prefix cache 歸零，對端會迎來一波 TTFT 風暴（全是冷 prefill）——這是物理，不是 bug，告警要預先靜默、容量要為冷流量留 buffer。**RTO 由常備容量決定**：GPU 不是 EC2，failover 時臨時租 64 張 H100 的「彈性」不存在（有貨是運氣，沒貨是常態）。所以選項只有 active-active（雙倍 GPU 錢換分鐘級 RTO）或接受小時級 RTO 的事後擴容——pilot light 模式在 GPU 世界點不著。這筆錢怎麼算，ch16。

## Incident response：兩棵判斷樹

寫 runbook 的原則：判斷樹的每個分支是一條**可在 2 分鐘內查完的指標**，葉子是一個**動作**。GPU 服務的 mitigation 優先序要先背好：**rollback > shed/brownout > scale**——rollback 與 shedding 是秒～分鐘級，scale 是分鐘～小時級（冷啟動物理，ch12/ch13），半夜先拉快的閘。

### Runbook A：「TTFT p99 突然 ×3」

```text
TTFT p99 ×3（告警點火）
├─ Q1 範圍：單一/少數 pod 還是全池？（per-pod TTFT 分布，ch14 的面板）
│   ├─ 少數 pod → 慢 replica 路線：
│   │   ├─ DCGM throttle reasons / 溫度 / 時脈異常？ → thermal/power → cordon 該節點，開票
│   │   ├─ dmesg 有 Xid？ → 按故障目錄三分法處置
│   │   └─ 都沒有 → 先摘除該 pod 止血，再驗屍（別在病人身上 debug）
│   └─ 全池 → 系統性路線，往下走
├─ Q2 流量變了嗎？（RPS、prompt 長度分布、單一租戶占比）
│   └─ 是 → 容量問題：queue 深度、KV util 同步上升？
│        → shed 低優先 / brownout（先），擴容（後）；單租戶異常 → 限流該租戶（ch16）
├─ Q3 佇列在堆嗎？（num_waiting 趨勢）
│   ├─ 是，且流量沒變 → 供給端變慢：preemption 次數？長 prefill 干擾（ch06）？
│   └─ 否 → TTFT 高但沒排隊 → 幾乎可斷定是 Q4
├─ Q4 prefix cache hit rate 掉了嗎？（ch10）
│   └─ 是 → 路由變更？deploy 清了 cache？流量 mix 漂移？ → 回滾路由 config
└─ Q5 最近 4 小時有任何 deploy？（程式碼、權重、config、driver 都算）
    └─ 是 → 先 rollback（熱回退，秒級），再驗屍。「先回滾再理解」不丟人
```

### Runbook B：「某 node NCCL timeout」

```text
NCCL watchdog timeout（或 token 輸出歸零 + util 100% 的背離告警）
├─ 第 0 步 止血：這個 TP/EP 組是單一故障域 → 整組摘除流量（不是單一 pod）
│   並確認：被斷的 in-flight 請求的重試突刺有沒有觸發 retry budget（防二次災害）
├─ Q1 全組 rank 都卡在 collective？（stack dump / Flight Recorder）
│   ├─ 是，且有 rank 缺席 → 找屍體：
│   │   ├─ 該 rank pod OOMKilled / crash log？ → 軟體層 → 整組原地重啟
│   │   └─ 該節點 dmesg 有 Xid 79/48/119？ → 硬體層 → cordon 節點，整組在健康節點重建
│   ├─ 是，全員到齊但都不動 → desync（叫了不匹配的 collective）→ 引擎 bug：
│   │   蒐集 Flight Recorder dump → 整組重啟 → 回報 upstream（dump 是修 bug 的唯一證據）
│   └─ 否，有 rank 在跑只是慢 → 慢卡路線：DCGM 溫度/時脈 + NVLink/IB 錯誤計數（Xid 74）
├─ Q2 重啟後復發？
│   ├─ 同節點復發 → 硬體嫌疑加重：dcgmi diag 長測 → 不過就走 RMA 流程
│   └─ 換節點仍復發 → 軟體嫌疑：driver × NCCL × 引擎版本矩陣，查最近的升級事件
└─ 收尾：incident 記錄回寫 runbook；該組的請求傷亡數進 postmortem 的用戶影響欄
```

共同紀律：每次 incident 後 runbook 必須回寫（指標改名、面板搬家、工具換代都會讓判斷樹腐爛——半夜照著跑全是 404 的 runbook 比沒有更危險），而驗證 runbook 沒腐爛的唯一方法是演練——下一節。

## 混沌工程：對 GPU 服務的實驗清單

Chaos 的標準紀律（假設先行、爆炸半徑契約、自動中止條件）你都懂，這裡直接給 GPU 服務專屬的實驗清單。前五個在模擬叢集（M1，免費）就能跑，後面的需要 staging 真卡：

| 實驗 | 你在驗證的假設 | 注入方式 | 中止條件 / 注意 |
|---|---|---|---|
| 1. 殺掉 stream 進行中的 engine pod | client 收到可辨識的斷流訊號；gateway 不重試已出首 token 的請求；EPP 秒級摘除 | `kubectl delete pod --grace-period=0` | 錯誤率超過演練預算即停 |
| 2. Drain 一個節點 | drain 預算成立：實測清空時間 ≤ 預算、傷亡 ≤ 預期值 | `kubectl drain` | 拿實測值回填 worked example 的分布假設 |
| 3. 製造 retry storm | retry budget 擋得住：放大係數 ≤ 設計值、無螺旋 | k6 腳本配激進重試策略 | waiting 佇列深度超閾值即停 |
| 4. 拔掉 EPP / 路由層 | fail-open 或 fail-closed 的行為與你宣稱的一致（ch12） | scale EPP to 0 | — |
| 5. 凍結深健康探針的回應 | 探針失敗只觸發 cordon 與告警，**不**觸發 liveness 連鎖重啟 | 讓探針端點 sleep | 全池重啟 = 實驗失敗且立刻中止 |
| 6. 模擬 GPU 降頻 | 慢 replica 偵測在 N 分鐘內抓到離群 pod 並摘除 | `nvidia-smi -lgc` 鎖低時脈 | 結束後 `-rgc` 解鎖 |
| 7. TP rank 間注入網路延遲/丟包 | NCCL timeout 在設定值內點火；告警先於用戶投訴；整組一起重啟 | `tc netem`（跨節點 TP/EP 時） | 單組、限時 |
| 8. 塞爆節點 NVMe | DiskPressure 之前有告警；權重快取 LRU 正常淘汰 | `fallocate` 大檔 | — |
| 9. 權重 checksum 不符 | 部署管線拒絕啟動，而不是默默載入錯的權重 | 改 artifact 的一個 byte | 只在 staging |
| 10. 區域 failover 演練 | 權重已預熱、TTFT 風暴在預期內、RTO ≤ 承諾值 | 切斷主區流量 | 一年至少一次，否則 DR 是傳說 |

一個與一般後端不同的成本提醒：GPU staging 環境很貴，所以分層演練——**控制面與路由層的 chaos 在模擬叢集跑到飽**（kind + llm-d-inference-sim，零成本），只有牽涉真 GPU 物理的實驗（6、7）才上真卡，而且可以蹭在租卡做 benchmark（ch08/ch14）的同一批機時裡。

## 故障模式與防禦

本章通篇都是故障，所以這個招牌段落往上再走一層：**防禦工事自己會壞**。每一道你在本章建立的工事，它的失效模式與對策：

| 防禦工事 | 它自己怎麼壞 | 症狀 | 對策 |
|---|---|---|---|
| 深健康探針 | 過載時超時，把「忙」判成「死」；若誤接 liveness → 級聯重啟 | 尖峰時段 pod 集體重啟 | 探針只接 cordon/告警；閾值遠鬆於 SLO；探針自身的失敗率也要監控 |
| 自動 cordon | 誤報風暴：一個壞指標 cordon 掉半個叢集；或 Xid 13/31 誤入自動化 | 容量無故蒸發 | cordon 速率上限；軟體類 Xid 永遠留給人判斷 |
| Graceful drain | grace period < drain 預算；或 preStop 在等但路由層還在送新請求 | 每次 rollout 都有規律的斷流突刺 | 預算對齊（本章數學）；先摘 endpoint 再等待；用 chaos #2 定期驗證 |
| Eval gate | golden set 過擬合或外洩；judge 模型自己漂移 | gate 全綠但投訴上升 | 題庫定期輪換＋加入歷史事故回歸題；看相對 diff；與 shadow 分布指標互相印證 |
| Retry budget | 只設在自家 SDK，第三方 client 不甩你 | storm 照樣發生 | server 端強制（gateway token bucket）；429 必帶 Retry-After |
| Brownout | 沒有遲滯 → 邊界抖動；人工拉閘 → 忘記關 | 服務時好時壞；降級狀態跑了一週沒人發現 | 宣告式狀態機 + 自動退出 + brownout 狀態進告警面板 |
| Runbook | 寫完即腐爛：指標改名、工具換代 | 半夜照著跑，連結全 404 | incident 後回寫；每季 game day 演練 |
| Chaos 演練 | 在生產炸出真事故 | 你自己成為 postmortem 主角 | 爆炸半徑契約＋自動中止；控制面實驗一律先過模擬叢集 |

讀出這張表的共同模式：**每一道自動化防線都需要一個「防線失控時的剎車」**——速率上限、遲滯、人工門檻。自動化的層級越高，剎車越重要。這跟你在遊戲後端學到的「自動擴容要設上限，否則一個 bug 就是一張天價帳單」是同一條定律。

## 動手做

### 實驗 1 [M1]：kill pod 與 preStop 的 drain 演練

在 ch12 實驗 1 的模擬叢集（kind + GIE + llm-d-inference-sim）上：把 sim 的回應時長調到 30~60 秒模擬長 stream，先用 `kubectl delete pod --grace-period=0` 暴力殺一個正在服務的 pod，記錄 client 端看到什麼（斷流的形狀、gateway 的行為）；然後實作正確版本——readiness 翻 false + preStop 等待 in-flight 歸零 + 足夠的 grace period——再殺一次對比。**成功標準**：交出兩份 client 端的逐 token 時間戳記錄，暴力版有斷流、優雅版零傷亡；並且能說出你的 grace period 數字是怎麼從 sim 的時長分布算出來的（本章 worked example 的公式）。

### 實驗 2 [M1]：親手製造一場 retry storm

同一個模擬叢集，把 sim 的容量調小（低 max-num-seqs）。寫一個帶「激進重試」的 k6 腳本（timeout 5s、立刻重試、最多 5 次），逐步加壓直到佇列崩潰，觀察：佇列深度、有效完成率（goodput）、重試流量占比的時間序列。然後加上兩道防禦——gateway 端 429 + Retry-After、k6 端改成 retry budget + 指數退避 + jitter——重打一輪。**成功標準**：兩輪的「offered load vs goodput」曲線圖，第一輪能看到 goodput 在過載點之後**下降**（殭屍請求吃掉容量），第二輪 goodput 在過載點之後持平。能解釋兩條曲線差異的機制，這個現象你就真的懂了。

### 實驗 3 [紙上推演]：凌晨三點的 TTFT 告警

完整寫一棵你自己的「TTFT p99 ×3」判斷樹，規則：每個分支節點標注「查哪個指標、在哪個面板、預期耗時」；每片葉子是一個動作，標注「止血型（秒級）還是根治型（小時級）」；至少覆蓋本章 Runbook A 沒有展開的兩種情境（建議：「深夜 batch 租戶突然上量」與「上游權重快取層故障導致部分 pod 重啟後變冷」）。**成功標準**：拿給一位做過 on-call 的同事，請他用你的樹走一遍任一情境，他不需要問你任何補充問題就能走到葉子——問了，就是樹有洞。

## 這個領域往哪走

短期（1~2 年）最值得盯的三條線：**引擎 shutdown 語意的標準化**（vLLM 的 RFC 方向是把 drain、KV 傳輸收尾、可配置時限變成引擎的一等公民——落地後本章「drain 全靠路由層」的工法會簡化）；**容錯集合通訊**（讓 TP/EP 組在成員故障時收縮重組而不是整組陪葬的研究方向，若成熟會改寫「故障域 = 整組」的鐵律）；**GPU 健康的預測性維護**（用 ECC/溫度/時脈的時間序列預測壞卡，從「壞了才 cordon」走向「壞之前 drain」——大機隊的公開數據正在累積）。不變的部分更重要：故障目錄會換條目，但「抓背離而不是抓錯誤」「故障域思維」「防線要有剎車」這些原則，跟你從遊戲後端帶來的可靠性直覺一樣，十年不會過期。

## 自我檢核

1. dmesg 看到 Xid 48、Xid 31、Xid 79，三者的處置為什麼完全不同？哪些 Xid 可以接自動 cordon、哪些絕對不行、為什麼？
2. NCCL hang 為什麼是「三重欺騙」的故障？寫出一條不依賴 error log 的告警規則，並解釋為什麼處置單位必須是整個 TP/EP 組。
3. 深健康探針（真的生成 token）為什麼不能接 liveness probe？推演一次它在流量尖峰時引發級聯重啟的完整鏈條，以及正確的接法。
4. 給定請求時長分布與每 pod 48 條 in-flight，為什麼 drain 預算「等到 p99」遠遠不夠？寫出「t 秒內清空」的機率公式，並解釋 gateway 的 max stream duration 上限在這個數學裡扮演什麼角色。
5. 用 K8s 預設的 30 秒 grace period 對 24 pod 的 LLM 服務做 rolling update，會發生什麼？這個傷害為什麼在 5xx dashboard 上看不到？
6. 「品質迴歸在 5xx 看不到」——給出三個真實的觸發場景，並說明 eval gate 與 shadow traffic 各自防的是哪一段、各自的盲區是什麼。
7. LLM 的 retry storm 比一般 API 的版本危險在哪三點？retry budget 為什麼要按 token 計而不是按請求計？
8. 列出三個 brownout 槓桿與各自的代價，並解釋為什麼 brownout 必須是「帶遲滯的宣告式狀態機」而不是 on-call 手動改 config。

## 延伸閱讀

- [NVIDIA Xid Errors 官方文件與 Xid 目錄](https://docs.nvidia.com/deploy/xid-errors/) — 每個 Xid 的官方定義、成因與建議處置（Ampere 之後有完整 catalog 可下載），on-call 必備書籤。
- [NVIDIA GPU Debug Guidelines](https://docs.nvidia.com/deploy/gpu-debug-guidelines/) — 官方的 GPU 排障流程：什麼情況跑 dcgmi diag、什麼情況 RMA，本章 Xid 三分法的權威依據。
- [The Llama 3 Herd of Models（arXiv:2407.21783）第 3.3 節](https://arxiv.org/abs/2407.21783) — 16,384 張 H100、54 天、419 次中斷的一手數據，建立「故障是輸入條件」世界觀的最佳文獻。
- [Revisiting Reliability in Large-Scale ML Research Clusters（Meta, arXiv:2410.21680）](https://arxiv.org/abs/2410.21680) — 11 個月、1.5 億 GPU 時的機隊級故障率分析，本章「每千節點日 2.3 次故障」的出處，含 MTTF 隨規模的外推模型。
- [Flight Recorder: A New Lens for Understanding NCCL Watchdog Timeouts（PyTorch Blog）](https://pytorch.org/blog/flight-recorder-a-new-lens-for-understanding-nccl-watchdog-timeouts/) — NCCL timeout 驗屍工具的設計與用法，「desync 多於真慢」的 fleet 經驗也來自 PyTorch 維護者社群。
- [vLLM RFC: Clarifying vLLM Shutdown Semantics（Issue #24885）](https://github.com/vllm-project/vllm/issues/24885) — 引擎 graceful shutdown 標準化的進行式（2026-06 仍在演進），追蹤它就知道 drain 工法什麼時候可以下沉到引擎層。
- [Google SRE Book: Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/) — 級聯故障、load shedding 與「丟棄是恢復的開始」的經典論述，本章佇列崩潰一節的理論底。
- [Timeouts, Retries, and Backoff with Jitter（AWS Builders' Library）](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) — retry budget 與 jitter 的工程細節，把它的結論乘上 LLM 的成本係數就是本章的 retry storm 一節。
- [Modal: GPU Health 文件](https://modal.com/docs/guide/gpu-health) — 一家 GPU serverless 廠商怎麼把 Xid 監控與自動隔離做成產品功能，小而務實的生產實例。
