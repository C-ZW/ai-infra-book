# ch16 — 成本工程與多租戶：把 GPU 變成一門生意

> **本章解決什麼問題**：前面十五章教你把 LLM 服務跑起來、跑得快、跑得穩；本章回答「跑得划不划算」——這是 staff 級工程師與資深工程師的分水嶺。你會建立 $/M token 的單位經濟模型、看懂 GPU 採購光譜（2026-06 價格快照）、完整算一遍 50B tokens/月的 build vs buy 決算，然後處理內部多租戶的三件髒活：計量計費（chargeback）、token 計價的限流、noisy neighbor 隔離。技術優化手段本身在 ch05-07，容量數學在 ch13——本章拿它們的結論當輸入，算錢。

## 從你已知的出發

你做過的三件事，在這一章會直接變現。

第一，你把 RDS CPU 尖峰降了 40%——那其實是一次成本工程：同樣的負載用更少的資源扛住，省下的是實例費。本章做的事一模一樣，只是資源從 vCPU 換成 GPU，而 GPU 貴兩個量級：一台 db.r5.2xlarge 一個月一千美金上下，一台 8×H100 節點一個月一萬五到四萬美金（2026-06 快照，取決於怎麼租）。在後端世界「利用率低一點沒關係」的鬆弛感，在 GPU 世界是直接燒錢。

第二，你寫過結算 pipeline：K8s CronJobs → SQS → idempotent consumers，每季結算十萬到三十萬筆獎勵。把「獎勵發放事件」換成「token 用量事件」，把「每季結算」換成「每月出帳」，你就已經會做 chargeback 的計量管線了——架構同構，連 idempotency 跟最終一致性的坑都在同樣的位置。

第三，你寫過 rate limiter。token bucket 這個演算法你閉著眼睛能寫——桶子、補水速率、突發容量。本章它會再出現一次，唯一的差別是：**桶裡裝的不再是「請求數」這種抽象單位，而是字面意義的 token**。一個請求可能從桶裡拿走 50 個 token，也可能拿走 200,000 個。這個變化讓「一個請求扣一點」的舊設計徹底失效，但演算法本身不用換。

還有一個對照值得先記下：你在 AWS 上看過 cost allocation tags 與 Cost Explorer——雲端 FinOps 那一套（showback、預算告警、預留實例 vs on-demand 的取捨）整包搬過來都成立，只是這裡的「預留實例」叫 reserved GPU capacity，「Savings Plans」叫一年期合約，而且因為 GPU 供需波動比 EC2 劇烈得多，押錯邊的代價也大得多。

## 單位經濟學：$/M token 是怎麼來的

LLM 推論的成本最終都收斂到一個數字：**每百萬 token 的成本（$/Mtok）**。它的推導只有一行：

```text
理論 $/Mtok = GPU 單價 ($/GPU-hr) ÷ 有效 token rate (Mtok/GPU-hr)
            = GPU 單價 ÷ (goodput tok/s × 3,600 ÷ 10^6)
            = GPU 單價 ÷ (goodput × 0.0036)

實付 $/Mtok = 理論 $/Mtok ÷ 機隊利用率
```

兩個變數要講清楚定義，否則這條公式會騙你：

- **goodput**（ch14）：滿足 SLO 前提下、單 GPU 每秒處理的 token 數，input 與 output 都算（兩者的單位成本差很多，後面會加權處理，先用總量建立直覺）。注意是 goodput 不是吞吐——超出 SLO 的 token 對產品是廢品，廢品不能攤成本。
- **機隊利用率**：實際處理的 token 量 ÷ 機隊滿載能處理的量。你為尖峰配置容量、為故障留 headroom、為發布留 buffer——這些都讓分母大於分子。

代入一組真實量級（2026-06 快照；goodput 假設為你照 ch13/ch14 方法 benchmark 出來的數字）：H100 租金 $2.50/hr，70B 級模型 FP8、TP2，量到混合流量 goodput 約 2,000 tok/s/GPU：

```text
理論 $/Mtok = 2.50 ÷ (2,000 × 0.0036) = 2.50 ÷ 7.2 ≈ $0.35
機隊利用率 40% → 實付 $/Mtok ≈ $0.87
```

把 $0.87 跟 serverless API 牌價放在一起看：Together AI 的 Llama-3.3-70B 牌價 $0.88/Mtok（2026-06 快照）。幾乎打平不是巧合——這個市場已經有效率到「自建的全成本 ≈ 託管牌價」，供應商的毛利就藏在「他們的利用率比你高」這件事裡。這是本章反覆出現的主題。

### 什麼最動成本：排序與量級

公式裡每個變數都能優化，但槓桿長度差很多。我的排序與量級如下（前提：你已經用 vLLM 這類現代引擎，continuous batching 是入場券不是優化）：

| 排序 | 槓桿 | 量級 | 機制 |
|---|---|---|---|
| 1 | **利用率** | **2–5×** | 公式裡唯一站在分母、又最常爛掉的數。dev 叢集常態低於 30%；尖谷比 2–3× 的線上流量，峰值配置下利用率天花板就是 40–50%。從 20% 拉到 70% = 成本直接砍 3.5 倍，不用動任何一行引擎程式碼。手段：填谷（batch 工作負載吃離峰，見下文）、配額治理（ch11 quota）、autoscaling（ch13）、減少碎片（ch11 bin-packing）。 |
| 2 | **快取命中** | **1.5–3×**（agentic 流量可到 5×） | prefix cache 命中讓 prefill 幾乎免費（ch05）。市場證據：各家 API 把 cached input 定價在原價的 10–25%（2026-06）——定價反映成本結構。agentic 流量 input 佔比常超過 90% 且 prefix 重複率極高，命中率從 0 到 90% 等於把最大那塊成本打一折。 |
| 3 | **batch 調優／量化** | **殘餘 1.5–3×** | 從 naive serving 到 continuous batching 是 10× 級，但那是 ch06 的入場券。在此之上：batch 參數調優 1.2–1.5×（ch06/ch08）、FP8 1.4–1.8×、INT4/FP4 再 1.3–1.8× 但帶品質風險（ch07）。 |
| 4 | **硬體代際** | **perf/$ 每代約 1.2–1.5×** | B200 租金約 H100 的 2.2 倍、吞吐約 2–3 倍（2026-06 快照）——租賃市場會把代際紅利的大半定價掉。買斷自有硬體才能吃到完整代際紅利，但那是另一個量級的承諾。 |

這個排序的含意很直白：**在排第 1、2 的槓桿還沒拉滿之前，去追第 3、4 是本末倒置**。我看過太多團隊在利用率 25% 的叢集上認真評估 FP4——先把那 3 倍撿起來。

## GPU 取得光譜（2026-06 價格快照）

> ⚠️ GPU 租價以月為單位波動。下表所有絕對數字都是 2026 年年中快照，書付印時必然過期；**級距與倍率關係**才是該記的東西。即時行情可查 getdeploying.com/gpus 這類聚合站。

| 層級 | 代表 | H100 級距（$/GPU-hr） | 適合 | 代價／陷阱 |
|---|---|---|---|---|
| Hyperscaler on-demand | AWS p5、Azure ND H100 v5 | **$6.9–12** | 已有企業合約／合規要求、要跟既有 VPC 整合 | 最貴的一層；配額審批慢 |
| Hyperscaler 承諾折扣 | 1–3 年 committed / Savings Plans | 牌價的 4–7 折 | 同上＋用量可預測 | 鎖定期；GPU 代際換代風險自負 |
| Neocloud on-demand | CoreWeave、Lambda、Nebius、Crusoe | **$2–3.3**（Lambda ~$2.99、RunPod ~$2.49） | 自建推論的主流起點 | 比 hyperscaler 便宜 35–50%+，但生態服務少（沒有 RDS 給你靠） |
| Neocloud reserved | 同上，6–36 個月合約 | **約 $1.5–2.5**（CoreWeave 宣稱保留合約可比 on-demand 低最多 60%；Lambda 歷史上 1 年約 8 折） | 量穩定後的主力 | 簽約即承諾；報價不公開、要談 |
| Marketplace / community | Vast.ai、RunPod community | **$1.4–2** | 實驗、可中斷工作 | 可靠性與資安自負；單卡居多、難組叢集 |
| Spot / preemptible | 各家 spot 池（B200 spot 曾見 ~$2.1） | on-demand 的 3–6 折 | **batch 工作負載**（見下節） | 隨時被回收。**online serving 不要碰**：權重載入分鐘級（ch12 cold start），回收 = 直接掉容量 |
| Serverless per-GPU-second | RunPod Serverless、Modal、Baseten | 按秒計費，單價高於時租 | 突發、低流量、scale-to-zero 場景 | 冷啟動稅（ch12）；穩定流量下比時租貴 |
| Serverless per-token（API 託管） | Together、Fireworks、DeepInfra；封閉模型則是 OpenAI/Anthropic/Google | 不租卡，直接買 token | 下一節整節討論 | 控制權全部讓渡 |

兩條結構性觀察：

1. **Spot 與推論的關係是「分工」不是「替代」**。online serving 的狀態太重（權重 + KV cache）、冷啟動太慢，spot 回收等於容量瞬間蒸發，再便宜都不值。但離線 batch 推論（eval、資料合成、embedding 回填）天生 checkpoint-able，spot 是它的主場。
2. **越往下層走，你接手的維運面積越大**。Hyperscaler 把網路、儲存、排障都包了；marketplace 上你連這張卡昨天被誰用來挖礦都不知道。SemiAnalysis 對 neocloud 經濟結構的拆解（見延伸閱讀）值得整篇讀完——你會理解為什麼同一張 H100 的租價可以差 5 倍。

## Worked example：50B tokens/月的 build vs buy 決算

這是本章的核心計算。設定：你的產品月吞吐 50B tokens（**40B input + 10B output**，4:1 是 chat+RAG 混合流量的典型比例），模型是 70B 級開放權重（沿用 ch03 的 Llama-3.3-70B），SLO 是 chat 等級（TTFT p95 < 1.5s）。比較三案：（a）API 託管、（b）neocloud 租 H100 on-demand 自建、（c）一年期保留容量自建。所有價格皆為 2026-06 快照。

**共用假設**（每一個都該換成你自己的數字）：

| 參數 | 值 | 來源 |
|---|---|---|
| 月秒數 | 2.628M s（730 hr） | — |
| 尖峰係數 | 2×（日夜週期） | 你的流量觀測 |
| 單 GPU goodput | 2,000 tok/s（70B FP8、TP2、含 prefill+decode 混合、SLO 內） | ch14 方法 benchmark |
| Headroom | 25%（含 N+1 與發布 buffer） | ch13 的結論直接當輸入 |
| 工程師全載成本 | $14k/月/FTE | 假設參數，依你的市場調整 |

### Step 1：流量畫像 → 峰值需求

```text
平均 token rate = 50×10^9 ÷ 2.628×10^6 s ≈ 19,000 tok/s
峰值 token rate = 19,000 × 2 = 38,000 tok/s
```

### Step 2：峰值需求 → 卡數

```text
裸需求 = 38,000 ÷ 2,000 = 19 張 H100
加 25% headroom = 23.75 → 取整為 24 張（12 組 TP2，恰好 3 台 8 卡節點）
機隊利用率 = 19,000 ÷ (24 × 2,000) = 40%
```

注意這個 40%：你什麼都沒做錯——尖峰係數 2× 加上 25% headroom，數學上限就是這樣。這就是「利用率排第一」的具體長相。

### Step 3：三案逐月成本

**Case A — API 託管（serverless per-token）**

- 一線供應商牌價：Llama-3.3-70B 在 Together/Fireworks 約 **$0.88–0.90/Mtok**（input/output 同價，2026-06）：
  `50,000 Mtok × $0.88 = $44,000/月`
- 低價層（DeepInfra 等）：input ~$0.23、output ~$0.40（2026-06）：
  `40,000 × $0.23 + 10,000 × $0.40 ≈ $13,200/月`
  代價：TTFT 變異大、rate limit 緊、部署可能是量化版、資料條款要逐字讀。截至我能確認的資訊（2026-06），低價層的定價可能低於合理的自建邊際成本——背後可能是超賣、量化部署或虧本搶市，把它當 baseline 要打折扣看待。
- 人力：只剩整合與監控，估 0.15 FTE ≈ $2,000。

**Case A 合計：$15k–46k/月**，取決於你選哪一層、談到什麼量價。

**Case B — neocloud on-demand 自建**

```text
GPU：24 × $2.50/hr × 730 hr        = $43,800
附加（儲存、監控、egress、CI 用卡）  ≈  $2,500
人力：1.5 FTE × $14k（on-call 輪值） = $21,000
─────────────────────────────────────────────
合計                                ≈ $67,300/月   → blended $1.35/Mtok
```

注意 GPU-only 的 $43,800 ÷ 50,000 Mtok = **$0.88/Mtok——跟 Together 牌價一模一樣**。市場效率的具體展示：on-demand 自建在純 GPU 成本上對牌價 API 毫無優勢，加上人力後直接輸。

**Case C — 一年期保留容量自建**

保留價假設 $1.90/GPU-hr（neocloud 一年合約級距 $1.5–2.5 的中位，2026-06）：

```text
GPU：24 × $1.90/hr × 730 hr         = $33,300
附加                                 ≈  $2,500
人力：1.5 FTE                        = $21,000
─────────────────────────────────────────────
合計                                ≈ $56,800/月   → blended $1.14/Mtok
```

外加一個帳面外的負債：**你簽了 12 個月**。流量腰斬時 API 帳單跟著腰斬，這 $33,300 不會。

### Step 4：crossover 在哪裡

三案的成本結構：API 是純斜率（成本 ∝ token 量、零底座）；自建是「底座（人力＋附加）＋斜率（GPU ∝ 容量 ∝ token 量）」。crossover 解這條方程式：

```text
API 單價 × T = 自建斜率 × T + 自建底座
T* = 底座 ÷ (API 單價 − 自建斜率)

代入 Case C：T* = $23,500 ÷ ($0.88 − $0.67) ≈ 112,000 Mtok ≈ 112B tokens/月
（自建斜率 $0.67/Mtok = $33,300 GPU 費 ÷ 50,000 Mtok，已內含 40% 利用率）
```

| 月吞吐 | A1 API 牌價 | A2 API 低價層 | B on-demand 自建 | C reserved 自建 |
|---|---|---|---|---|
| 10B | **$8.8k** | $2.6k | $34.5k | $31.8k |
| 50B（本例） | $44k | **$13.2k** | $67.3k | $56.8k |
| ~110B | $97k | $29k | $131k | **$107k ← crossover 區** |
| 200B | $176k | $52.8k | $211k | **$169k** |

（110B 以上人力估 2 FTE；表中 crossover 對「牌價 API vs reserved 自建」成立。）

讀法：

- **10B/月以下：API 完勝**，自建的底座（最小 HA 部署＋人力）就把你壓死。
- **50B/月（本例）：API 仍勝**。牌價贏 22%，低價層贏 4 倍。
- **約 110–150B/月：對牌價 API 的 crossover**。人力是階梯函數、API 大量採購又有議價空間，所以這是個區間不是一個點。
- **對低價層 API（$0.26 blended）：在 40% 利用率下永遠不 crossover**——斜率就輸了（$0.67 > $0.26）。

### Step 5：什麼會翻盤

敏感度分析才是這個計算的真正產出：

1. **利用率**。把離峰填上 batch 工作負載、流量越平，40% → 65%：自建斜率 $0.67 → $0.41。再加上 prefix cache 命中讓 goodput 2,000 → 3,000：斜率 → $0.27——這時你才摸到低價層 API 的水位。**自建唯一能在價格上獲勝的路徑，就是把排序第 1、2 的槓桿拉滿。**
2. **非價格因素，而且實務上往往是它們決定**：資料不能出境／合規（API 直接出局）、客製 fine-tune 模型（託管 LoRA 另外加價或根本不收）、TTFT 要自己控、cache 主權（agentic 產品的 KV cache 策略是核心競爭力時，見 ch17）。
3. **模型選擇本身**。這題用 dense 70B 算；換成 MoE（active params 小一個量級，ch03）整張表的絕對值全變。模型架構是最大的成本決策，只是它通常不歸 infra 團隊管。

把這五步收成一句話：**buy 是預設值，build 要自證**——用你自己的流量、自己 benchmark 的 goodput、自己談到的價格重算一遍，而不是用部落格上的別人的數字。

## Batch tier 與快取經濟學

### 為什麼大家「恰好」都是 50%

OpenAI Batch API、Anthropic Message Batches、Gemini Batch Mode——三家的折扣全是 50%、SLA 全是 24 小時內完成（2026-06）。整齊到這個程度一定有結構性原因，而你現在已經有工具看穿它：

回到利用率那條公式。線上服務為尖峰配置，離峰時 GPU 閒著但錢照付——**batch tier 賣的就是這些谷底容量**。對供應商而言，batch 請求沒有延遲 SLO，排程器可以把它們塞進任何縫隙（夜間谷底、replica 暖機期、線上流量的瞬時低谷），邊際成本趨近於「本來就在燒的電」。50% 折扣換 24 小時排程自由度，對雙方都是好交易。Google 自己的工程部落格講得很直白：同一個模型、同樣的品質，折扣純粹是非同步換來的排程效率。

自建版本同樣成立，而且是你拉高利用率的主力手段：**讓內部的 eval、資料合成、embedding 回填走低優先級佇列，吃線上服務的離峰容量**——用 ch06 的 priority scheduling（vLLM 的 `--scheduling-policy priority`）加上租戶級 preemption（下一節），讓 batch 流量在線上尖峰時自動讓路。那 40% 利用率裡的谷底，就是這樣填成 65% 的。

### 快取的定價即成本結構

各家 API 的 cached input 定價是一份公開的成本結構招供（2026-06 快照，規則年年改版、來源間有矛盾，引用前查當下官方價目）：

| 供應商 | cache read 價格 | 備註 |
|---|---|---|
| Anthropic | 基準價 10% | write 有溢價：5 分鐘 TTL 1.25×、1 小時 TTL 2× |
| OpenAI | 50–90% 折扣依模型 | 自動快取、無 write 費（⚠️ 新模型折扣各來源說法 25–90% 不一） |
| Google Gemini | 約 75–90% 折扣 | explicit caching 另收按小時的儲存費 |
| DeepSeek | 約 90%+ 折扣 | 磁碟式自動快取；⚠️ V4 世代有報導稱折扣更深（原價 1/50 以下），僅見第三方來源 |

讀出兩件事。第一，**read 打一折 ≈ prefix cache 命中時 prefill 的真實成本**（ch05 的機制：命中的 block 不重算，只剩 KV 載入與 attention 讀取）。第二，**Anthropic 的 write 溢價與 Gemini 的儲存費，是 KV cache 分層儲存（ch05 的 HBM→RAM→NVMe）的成本被直接轉嫁成商品**——KV cache 已經從引擎內部的優化變成一個有定價的儲存層級。

對成本工程的含意：agentic 流量（input 佔比 90%+、prefix 重複率極高，ch17）讓**快取命中率變成損益表上的一級指標**。同一個 agent 產品，命中率 90% 與 50% 的 token 帳單可以差 2–3 倍——不管你是付 API 帳單（cached read 折扣）還是自建（goodput 翻倍）。所以：把 prefix cache hit rate 放進成本 dashboard，跟 $/Mtok 並排；prompt 的組織方式（穩定前綴在前、可變內容在後）要當成本規範來治理，不是工程美學。

## 利用率會計：忙碌不等於有效

「我們的 GPU 利用率 95%」是成本會議上最危險的一句話，因為 `nvidia-smi` 的 utilization 只表示「這段時間有 kernel 在跑」（ch14 講過 SM activity vs utilization 的差異）。成本視角需要一個三層的利用率會計：

```text
第一層：機隊層 —— 有多少 GPU-hr 被分配出去了？（vs 閒置、碎片、排隊中）
第二層：分配層 —— 分配出去的 GPU-hr 有多少在做「有人要的工作」？
第三層：有效層 —— 做的工作裡有多少轉成了 SLO 內的 token（goodput）？
```

每一層都有典型的洩漏：

- **機隊層**：bin-packing 碎片（叢集帳面有 12 張空卡，但散在 6 個節點上，湊不出一台 8 卡機跑 TP8——ch11 講過機制，這裡它直接是錢）；dev/研究卡掛著 notebook 過週末；保留容量買了沒用滿。
- **分配層**：「忙碌但無效」的 GPU——preemption 後的 recompute（ch06，同一段 prefill 算兩遍）、speculative decoding 被拒絕的 draft token（ch07）、客戶端早已斷線但還在繼續 decode 的殭屍請求（下文濫用防禦）、被打爆而全部超時的請求（100% busy、0% goodput）。
- **有效層**：MFU/MBU 很高但 SLO 不滿足——對產品而言這些 FLOPs 是廢品。

dev 卡治理值得單獨一段，因為它是最容易撿的錢：對 dev/研究用途用 time-slicing 或 MIG 切小（ch11），配 idle 自動回收（連續 N 小時無 kernel 活動就釋放），加上 showback 讓每張卡的閒置時數出現在持有團隊的月報上。經驗上，沒有治理的 dev 池利用率低於 20% 是常態而不是意外。

## 內部多租戶：計量、限流、隔離

平台做起來之後，你的客戶變成公司內部的 N 個團隊。三個問題依序出現：誰用了多少（計量）、誰能用多快（限流）、誰會弄壞誰（隔離）。

### Chargeback / showback 設計

計量管線的形狀你已經做過——這就是你的結算 pipeline 換了 payload：

```text
[Gateway] --usage event--> [Queue (SQS/Kafka)] --> [idempotent aggregator] --> [月度 rollup / dashboard]
```

usage event 的最小 schema（gateway 在請求完成或中斷時發出，ch12 的計量位置）：

```json
{
  "request_id": "…",            // 冪等鍵——重送不重計，你熟
  "tenant_id": "team-search",
  "model": "llama-3.3-70b-fp8",
  "input_tokens": 18234,
  "cached_input_tokens": 15012, // 必須分開計！成本差 10 倍
  "output_tokens": 512,
  "priority": "interactive",     // interactive | standard | batch
  "ts": "2026-06-10T03:21:00Z"
}
```

關鍵設計決策三個：

1. **內部價卡怎麼定**。從機隊全成本反推：`費率 = 機隊月成本 ÷ （目標利用率下的月 token 量）`，再按市場結構加權拆成三個費率——uncached input : cached input : output ≈ **1 : 0.1 : 4**（用上一節的 API 定價當權重依據）。給 cached input 打一折不是慈善，是**把真實成本結構傳導給內部用戶**，讓他們有動機把 prompt 組織成 cache-friendly 的形狀——計費設計就是行為設計。
2. **headroom 與閒置誰買單**。三個選項：攤進費率（除以目標利用率而非實際利用率）、平台稅（固定比例）、或平台自吸收。陷阱是「100% 成本真實」的定價：某團隊下線後總用量掉，單價被迫上調，其他團隊看到漲價也想走——**內部定價的死亡螺旋**，FinOps 的經典事故。解法是費率定價時就用「目標利用率」當分母並按季檢討，犧牲一點真實性換穩定性。
3. **showback 先行**。先讓帳單可見（showback）跑兩季，數字被質疑、修正、被信任之後，再變成真的預算劃轉（chargeback）。直接上 chargeback 的下場是所有團隊的第一反應都是攻擊計量方法，而不是優化用量。

### Token-denominated rate limiting

現在把你寫過的 token bucket 拿出來改。限流單位從「請求/分」換成「token/分（TPM）」之後，出現一個舊設計沒有的問題：**請求進來的當下，你不知道它要花多少 token**。input 可以當場算（tokenizer 一跑就有），但 output 要等生成完才知道，而 `max_tokens` 動輒是實際輸出的 4–16 倍。

解法是你在金流系統見過的模式：**兩階段——先預留（reserve）、後結算（settle）**。

```python
# 示意：token 計價的 token bucket，Redis Lua 保證原子性
# （你用 FluentBit + Lua 處理過 production log，這裡的 Lua 更短）
RESERVE_LUA = """
local key  = KEYS[1]
local now, rate, burst, cost = tonumber(ARGV[1]), tonumber(ARGV[2]),
                               tonumber(ARGV[3]), tonumber(ARGV[4])
local tokens = tonumber(redis.call('HGET', key, 'tokens') or burst)
local ts     = tonumber(redis.call('HGET', key, 'ts') or now)
tokens = math.min(burst, tokens + (now - ts) * rate)      -- 補水
if tokens < cost then
  return {0, math.ceil((cost - tokens) / rate)}           -- 拒絕＋Retry-After 秒數
end
redis.call('HSET', key, 'tokens', tokens - cost, 'ts', now)
return {1, 0}
"""

async def admit(tenant: str, prompt_tokens: int, max_tokens: int):
    # 預留量：prompt 實數 + 輸出「預估值」——用該租戶歷史 p95 輸出，
    # 而不是 max_tokens（否則過度預留會把吞吐掐死在配額的 1/10）
    est_output = min(max_tokens, await p95_output(tenant))
    reserve = prompt_tokens + 4 * est_output           # output 權重 4×
    ok, retry_after = await redis.eval(RESERVE_LUA, keys=[f"tpm:{tenant}"],
        args=[now(), tenant_rate(tenant), tenant_burst(tenant), reserve])
    if not ok:
        raise RateLimited(retry_after)                 # 429 + Retry-After
    return reserve

async def settle(tenant: str, reserved: float, usage):
    # 串流結束（或中斷）時結算實際加權用量，多退少補
    actual = (usage.uncached_input + 0.1 * usage.cached_input
              + 4.0 * usage.output)
    await redis.eval(REFUND_LUA, keys=[f"tpm:{tenant}"],
                     args=[now(), actual - reserved])  # 可為負：允許短期負債
```

設計重點，每一條都是會在生產咬人的：

- **預留用 p95 不用 max_tokens**。用 max_tokens 預留，等於讓每個請求按最壞情況佔配額——實測會把租戶的有效吞吐掐到名目配額的幾分之一。代價是 settle 時可能補扣成負值（實際輸出超過 p95），所以桶要允許短期負債、在補水時自然還清。
- **計量單位是加權 token**，權重沿用價卡（1 : 0.1 : 4）。cached input 只扣 0.1——再一次，把成本結構傳導成行為誘因。
- **限流維度不只 TPM 一個**：TPM（成本上限）、RPM（防小請求洪峰）、並發數與 in-flight KV 預算（防下一節的 noisy neighbor）——三道閘各防一種攻擊面，缺一不可。
- **Redis 掛了怎麼辦**——這個決策要寫在設計文件裡而不是事故報告裡：對外的免費層 fail-closed（寧可 429），對內的付費租戶 fail-open＋告警（寧可超賣也不要把全公司的 AI 功能打掛）。
- 大租戶的桶是 hot key：按 tenant 分 shard 或本地預扣＋週期回寫，你在 Redis 上都做過。

### Noisy neighbor：一個 200k-context 租戶怎麼吃光整個池

具體算一次傷害有多大。沿用 ch03 的數字：Llama-3.3-70B（GQA）每 token KV ≈ 0.32 MB（FP16）。一個 200k context 的請求：

```text
200,000 tokens × 0.32 MB ≈ 64 GB 的 KV cache
```

你的 TP2 部署：2×H100 = 160 GB HBM，FP8 權重佔 70 GB，`gpu-memory-utilization 0.9` 之下 KV 池約 74 GB。**一個請求佔掉 86% 的池子**。後果連鎖反應：數十條 4–8k 的正常對話被 preempt（ch06）→ recompute 推高負載 → 全租戶 ITL 飆升；它的 200k prefill 即使有 chunked prefill 也要佔用 token budget 近一分鐘；順手還把熱 prefix 從 cache 裡擠出去，全池命中率下跌——三種傷害一次到位。而且這不是攻擊，只是某個團隊「想把整份文件塞進去試試」。

隔離手段按成本從低到高分層，前三層在 gateway 就能做完：

| 層 | 手段 | 防住什麼 | 代價 |
|---|---|---|---|
| 1 | Gateway 按租戶分級限制 `max context`／`max_tokens` | 未經申請的超長請求直接 422 | 幾行 config |
| 2 | Token 計價限流（上文） | 200k 請求一次吃掉大半 TPM 桶，自我節流 | 已建好 |
| 3 | 租戶級 in-flight KV 預算：Σ(每請求 context × 每 token KV) 超過配額即排隊 | 並發堆疊吃池 | gateway 記帳；引擎不原生支援 per-tenant KV 配額，只能在外面估 |
| 4 | **池子分離**：長上下文流量路由到專用 InferencePool（ch12），用大 HBM 卡（H200/B200）；chat 池的 `--max-model-len` 直接設小，讓怪獸請求物理上進不來 | 徹底隔離資源畫像衝突的流量 | 多一個池的容量與維運 |
| 5 | 租戶優先級 + preemption：interactive > standard > batch（vLLM priority scheduling + gateway 佇列） | 擠壓時犧牲順序可控 | 排程複雜度 |
| 6 | 大租戶獨立部署（搭配 multi-LoRA 的經濟學見 ch12）；小模型多租戶用 MIG 硬隔離（ch11） | 連 cache 污染都隔開 | 利用率下降——隔離與利用率天生互斥 |

注意第 6 層的代價：**隔離跟利用率是一對矛盾**。切得越碎，每個池的統計複用越差，你在第一節拉高的利用率又掉回去。預設用 1–5 層的軟隔離，硬隔離留給真正付得起的租戶。

### 濫用防禦

內部平台也需要，因為「濫用」多數不是惡意而是 bug：

- **Streaming abandon**：客戶端斷線（或 agent 超時放棄）但 gateway 沒把取消傳到引擎，GPU 繼續為沒人收的 stream decode 完整個 `max_tokens`。防禦：斷線必須觸發引擎 abort（vLLM 支援請求中止），並把「abort 率」做成指標——這是分配層利用率的隱形洩漏。
- **Denial of wallet**：agent 寫壞了，retry 迴圈每次都帶完整 200k context（ch15 的 retry storm，但這裡燒的是錢不是可用性）。防禦：租戶級預算硬上限（到頂直接 429 而不是寄信）、單日環比異常告警。
- **max_tokens 濫用與配額套利**：把 `max_tokens` 設到頂「以防萬一」、把長工作拆小繞 RPM——兩階段結算讓前者只多扣預留、後者撞 TPM，設計正確時這兩種套利自動無利可圖。

## TCO 全貌：GPU 之外的帳單

build vs buy 的計算裡 GPU 拿走了鎂光燈，但自建的完整帳單還有四行，量級如下（以租用為主的部署；自有機房另有電力與土建，本書不展開）：

| 項目 | 量級（相對 GPU 費用） | 說明 |
|---|---|---|
| 網路 | 租用通常內含；自組叢集時 IB/RoCE fabric 約佔硬體成本 10–15% | 多節點推論（ch09/ch10）才需要；跨 AZ egress 是隱形殺手 |
| 儲存 | 1–3% | 權重倉（每個模型每個版本幾十到幾百 GB）、節點 NVMe 權重快取（ch12）、KV offload 層（ch05）、日誌 |
| 可觀測性 | 1–5% | metrics/log/trace 的儲存與查詢（ch14 那套不是免費的） |
| **人力** | **本例中 ≈ GPU 費的 40–60%** | 最常被漏算的一行。1.5–2 個能扛 GPU on-call 的工程師，在 2026 年是稀缺品——這正是你讀這本書的原因，也是自建門檻的真正所在 |

worked example 裡 Case C 的 $56,800 中人力佔 $21,000——**37%**。任何不含人力的 build vs buy 分析都是在自欺。

## 故障模式與防禦

成本工程的「故障」往往不報 5xx，它報在月底帳單上。照例列表：

| 故障 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| Denial of wallet（agent retry 迴圈） | 帳單單日 ×10；某租戶 token 量暴增但成功率沒變 | 租戶級每小時用量環比告警 | 預算硬上限；retry budget（ch15）；異常自動降級到 429 |
| Streaming abandon 洩漏 | GPU 忙、goodput 掉；abort 率為 0（反而可疑） | 「client 斷線數 vs 引擎 abort 數」對帳 | 斷線→abort 的傳播鏈做整合測試；abort 率進 dashboard |
| 快取命中率崩落 | 成本悄悄 +50–200%，無任何錯誤 | prefix cache hit rate 進成本 dashboard 並設告警 | 模型/版本升級會清空 cache（ch05）——發布時預期並預熱；prompt 改版要過 cache 影響評估 |
| 限流器估算漂移 | 租戶抱怨 429 但帳面用量遠低於配額（過度預留）；或配額形同虛設（預估過低） | reserve vs settle 的差值分布 | p95 預估值定期重算；差值分布進監控 |
| Redis（限流狀態）故障 | fail-open：配額全失效；fail-closed：全平台 429 | 限流器自身的健康指標 | 每租戶層級預先決定 fail 方向；本地兜底桶 |
| 保留容量買錯邊 | 利用率長期 <30% 但合約照付；或反向——天天撞容量上限去買貴的 on-demand | 保留 vs on-demand 用量比、合約利用率月報 | 先 on-demand 跑出三個月真實曲線再簽約；保留量壓在「基載」而非尖峰 |
| 碎片化吃掉帳面容量 | 「有 12 張空卡但 8 卡 job 排不進去」 | 叢集可分配拓撲 vs 名目空卡數（ch11） | bin-packing 策略、定期 defrag/drain 重排 |
| 殭屍 dev 卡 | dev 池利用率 <20% 成為常態 | 每卡 idle 時數 showback | idle 自動回收；dev 用 time-slicing/MIG 切小（ch11） |
| 內部定價死亡螺旋 | 租戶退出→單價上調→更多租戶退出 | 費率變動史與租戶流失的相關性 | 用目標利用率定價、按季調整；平台稅吸收波動 |

共同主題：**成本故障的偵測手段全是「對帳」**——預留 vs 結算、斷線 vs abort、帳面容量 vs 可排程容量、保留 vs 實用。你在結算 pipeline 學到的對帳紀律，在這裡原封不動適用。

## 動手做

### 實驗 1 [紙上推演]：替你公司的一個 AI 功能做 build vs buy

拿你目前（或上一份）公司一個真實或假想的 AI 功能（客服摘要、搜尋改寫、code review bot 都行）：

1. 估流量畫像：月 token 量、input/output 比、尖峰係數（沒數據就給三檔情境：低/中/高）。
2. 選一個開放權重模型，照本章五步算三案（API 牌價自查當日價目；自建 goodput 用 ch13 的方法粗估或借本章假設值並標注）。
3. 算出 crossover 點，寫 200 字的建議書：buy 還是 build、什麼條件下翻盤。

**成功標準**：三案的月成本各有一張可審計的算式表；crossover 公式代入正確；建議書裡至少有一個非價格因素的論證。

### 實驗 2 [M1]：實作 token-denominated rate limiter

你寫過 rate limiter；這次計量單位換成 token，且要處理「輸出未知」：

```bash
# 1. 起依賴：Redis + 模擬引擎（不需要 GPU）
docker run -d -p 6379:6379 redis:7
# llm-d-inference-sim 模擬 vLLM 的 OpenAI-compatible API（旗標以 repo README 為準）
docker run -d -p 8000:8000 ghcr.io/llm-d/llm-d-inference-sim:latest --model fake-70b

# 2. 在 ch04 的 FastAPI proxy 前面加上本章的 reserve/settle 兩階段限流
#    （Redis Lua 原子扣減；settle 在 stream 結束與斷線時都要觸發）

# 3. 用 k6 模擬兩個租戶：
#    tenant-A：穩定的短請求（prompt ~500 tok）
#    tenant-B：突發的長請求（prompt ~50k tok，模擬 noisy neighbor）
```

**成功標準**：（1）tenant-B 的長請求會按 token 成本快速耗盡自己的 TPM 桶並收到帶 `Retry-After` 的 429，而 tenant-A 的 p95 延遲不受影響；（2）刻意在 stream 中途斷線，驗證 settle 仍被觸發且多退少補正確（對帳：Σreserve − Σrefund = Σactual）；（3）關掉 Redis，驗證你設計的 fail-open/fail-closed 行為如預期。

### 實驗 3 [紙上推演]：設計一張內部價卡

給定：24×H100 機隊、月全成本 $57k（借用 Case C）、目標利用率 60%、流量結構 uncached input : cached input : output = 25 : 55 : 20。

1. 推出三個費率（權重 1 : 0.1 : 4），驗算：費率 × 預期月用量 = 月全成本。
2. 回答：headroom 的成本你選擇攤進費率、收平台稅、還是平台吸收？寫下理由與死亡螺旋的防範。

**成功標準**：三費率可驗算回全成本；能對「為什麼 cached input 只收一折」給出成本結構與行為誘因兩層理由。

## 這個領域往哪走

三個方向值得盯（皆為 2026-06 視角，詳細展開見 ch17）：計價單位正從 $/token 往 **$/任務** 演化——reasoning 模型讓同一個問題的 token 量差 50 倍，token 計價對買方越來越難預算；**推論市場聚合層**（OpenRouter 類）把「買 token」變成有比價、有路由的市場，會持續壓縮純轉售型供應商的毛利；**電力**正在成為比 GPU 更硬的約束，power-aware 的成本工程（把 batch 負載排到電價低谷）可能在 2–3 年內從論文走進你的排程器。

## 自我檢核

1. 寫出 $/Mtok 的推導公式。四大成本槓桿（利用率、快取命中、batch/量化、硬體代際）為什麼是這個排序？各給量級。
2. 你的機隊「利用率 95%」，為什麼可能仍在大量燒錢？用三層利用率會計各舉一個洩漏。
3. 為什麼 OpenAI/Anthropic/Google 的 batch tier「恰好」都是 50% 折扣＋24 小時 SLA？自建時對應的手段是什麼？
4. 各家 API 把 cached input 定價在原價 10–25% 這件事，透露了什麼成本結構？對 agentic 產品的成本治理有什麼含意？
5. 一個 200k-context 請求對 Llama-3.3-70B（TP2、2×H100）的 KV 池佔比是多少？算出來，並給出至少三層隔離手段與各自代價。
6. Token-denominated rate limiter 為什麼需要兩階段 reserve/settle？預留用 max_tokens 會出什麼事？Redis 掛掉時 fail-open 還是 fail-closed，你怎麼決定？
7. 內部 chargeback 的「死亡螺旋」是怎麼發生的？定價時怎麼防？
8. 月吞吐 50B tokens 的產品，什麼條件下自建才划算？寫出 crossover 公式，並列出三個會推翻純價格結論的非價格因素。

## 延伸閱讀

- [SemiAnalysis — AI Neocloud Playbook and Anatomy](https://newsletter.semianalysis.com/p/ai-neocloud-playbook-and-anatomy)：neocloud 商業模式與 H100 叢集 TCO 的最完整公開拆解，理解「同一張卡租價差 5 倍」的供給側原因。
- [SemiAnalysis — The GPU Cloud ClusterMAX Rating System](https://semianalysis.com/2025/03/26/the-gpu-cloud-clustermax-rating-system-how-to-rent-gpus/)：怎麼評估與挑選 GPU 雲，租卡前必讀。
- [Artificial Analysis — Prompt Caching 價格對照](https://artificialanalysis.ai/models/caching)：跨供應商的 cache read/write 定價即時對照，本章「定價即成本結構」論證的資料來源。
- [Google — Gemini Batch API 文件](https://ai.google.dev/gemini-api/docs/batch-api)與[官方部落格](https://developers.googleblog.com/en/scale-your-ai-workloads-batch-mode-gemini-api/)：batch tier 50% 折扣的結構性原因，供應商自己的說法。
- [OpenAI — Batch API 指南](https://platform.openai.com/docs/guides/batch)：另一家的 batch tier 設計，注意與 Gemini 在配額與失敗處理上的差異。
- [a16z — State of AI: 100 Trillion Token Study](https://a16z.com/state-of-ai/)：OpenRouter 真實流量的結構分析，agentic 流量如何改變成本畫像的最佳實證來源。
- [FinOps Foundation — FinOps Framework](https://www.finops.org/framework/)：showback/chargeback 的組織實務；雲端成本治理的方法論可整套平移到 GPU 平台。
- [getdeploying.com/gpus](https://getdeploying.com/gpus)：GPU 租價即時聚合站，查當日行情用——本章所有絕對價格過期後，從這裡重算。
- [vLLM — V1 引擎與 priority scheduling 文件](https://docs.vllm.ai/en/stable/usage/v1_guide/)：租戶間優先級與 preemption 的引擎側落地。
