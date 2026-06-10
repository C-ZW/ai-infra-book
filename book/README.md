# 從後端到 AI Infra：LLM 推論基礎設施工程

> 寫給一位資深後端工程師的 AI Infrastructure 專業養成書。
> 核心論點：**大規模 LLM serving 是分散式系統問題，不是模型問題**——你過去六年的高併發、效能工程、可觀測性功力，是這個領域最稀缺的底子；這本書負責補上新的物理。
>
> 事實基準時點：**2026-06**（時效性內容均標註；維護方式見 `_meta/maintenance.md`）。

## 全書三條主軸

1. **LLM serving 本質上是 memory 的生意** — 幾乎所有設計決策最終都回到 memory bandwidth 與 memory capacity 的取捨。
2. **量測 → 診斷 → 優化 → 用數據證明** — 你既有的效能工程方法論，原封不動搬到 GPU 世界。
3. **把分散式系統直覺翻譯到新物理** — 排程、路由、一致性、可觀測性的直覺都成立，但物理常數變了。

## 目錄

### Part I — 心智模型與基礎
| 章 | 標題 | 一句話 |
|---|---|---|
| [ch01](part-1-foundations/ch01-from-backend-to-ai-infra.md) | 從後端到 AI Infra | 全書地圖：技術棧分層、職位光譜、你的技能遷移矩陣 |
| [ch02](part-1-foundations/ch02-gpu-architecture.md) | GPU：一種你沒用過的計算機 | SM/HBM/roofline、互連、機房現實、硬體版圖 |
| [ch03](part-1-foundations/ch03-inference-physics.md) | Transformer 推論的物理學 | attention、KV cache 數學、prefill/decode——全書的理論地基 |
| [ch04](part-1-foundations/ch04-language-bridge.md) | 語言與工具橋接 | Python（給 TS 工程師）、PyTorch 讀碼、Go 讀 controller、CUDA 生態 |

### Part II — 推論引擎
| 章 | 標題 | 一句話 |
|---|---|---|
| [ch05](part-2-inference-engine/ch05-kv-cache.md) | KV Cache 管理 | PagedAttention、prefix caching、KV 量化、offloading 分層 |
| [ch06](part-2-inference-engine/ch06-batching-scheduling.md) | Batching 與單機排程 | continuous batching、chunked prefill、preemption、吞吐的來源 |
| [ch07](part-2-inference-engine/ch07-model-optimization.md) | 模型壓縮與加速 | quantization、speculative decoding、kernels、CUDA graphs |
| [ch08](part-2-inference-engine/ch08-engines-in-practice.md) | 推論引擎實戰 | vLLM 架構與參數、SGLang、TensorRT-LLM、選型、單卡部署閉環 |

### Part III — 分散式推論
| 章 | 標題 | 一句話 |
|---|---|---|
| [ch09](part-3-distributed/ch09-parallelism.md) | 平行化策略 | TP/PP/DP/EP/SP、NCCL 通訊帳、拓撲、wide-EP |
| [ch10](part-3-distributed/ch10-disaggregation-routing.md) | P/D 分離與 KV 路由 | Mooncake/Dynamo/llm-d、KV 傳輸數學、KV-aware routing |

### Part IV — 平台工程（你的主場）
| 章 | 標題 | 一句話 |
|---|---|---|
| [ch11](part-4-platform/ch11-kubernetes-for-gpus.md) | Kubernetes 上的 GPU | device plugin→DRA、MIG/MPS/time-slicing、Kueue、節點生命週期 |
| [ch12](part-4-platform/ch12-platform-architecture.md) | 推論平台架構 | gateway→router→engine 全鏈路、平台選型、LoRA 多租戶、cold start |
| [ch13](part-4-platform/ch13-autoscaling-capacity.md) | Autoscaling 與容量工程 | 訊號選擇、headroom 數學、SLO 驅動的容量規劃與硬體選型 |

### Part V — 生產維運
| 章 | 標題 | 一句話 |
|---|---|---|
| [ch14](part-5-operations/ch14-observability-benchmarking.md) | 可觀測性與 Benchmark | 五層指標分類學、goodput@SLO、誠實的 benchmark 方法論 |
| [ch15](part-5-operations/ch15-reliability.md) | 可靠性工程 | 16 條故障目錄、drain 數學、eval gate、runbook 判斷樹 |
| [ch16](part-5-operations/ch16-cost-multitenancy.md) | 成本工程與多租戶 | $/Mtok 經濟學、build vs buy、token 計量限流、chargeback |

### Part VI — 前沿與職涯
| 章 | 標題 | 一句話 |
|---|---|---|
| [ch17](part-6-frontier/ch17-frontier-2026-2028.md) | 前沿 2026–2028 | agentic 流量革命、reasoning 經濟學、新架構與硬體、能力耐久性矩陣 |
| [ch18](part-6-frontier/ch18-career.md) | 把能力變成職涯 | 作品集對應、45 分鐘系統設計面試完整示範、開源策略、履歷改寫 |

### 附錄
- [附錄 A — 動手實驗總表](appendix/a-labs-index.md)：52 個實驗、三條軌道（M1 免費 / 單卡 $21–36 / 多卡 $8–15＋模擬），含建議順序與成本紀律
- [附錄 B — 術語表](appendix/b-glossary.md)：193 條 EN→繁中
- [附錄 C — 速查表](appendix/c-cheatsheets.md)：公式卡、vLLM 參數、PromQL、DCGM、K8s YAML、benchmark 檢查清單

## 怎麼讀

**完整路線**（建議，約 8–12 週搭配實作）：按章節順序。Part I 是地基（尤其 ch03，全書反覆引用它的數字）；每章讀完做「動手做」、用「自我檢核」驗收後再前進——講不清楚就是還沒懂。

**求職速通路線**：ch01 → ch03 → ch05 → ch06 → ch08 → ch11 → ch13 → ch14 → ch18，搭配附錄 A 的 Track 1＋Track 2。這條線覆蓋面試硬性要求的最小集合。

**面試前複習路線**：ch18 的 45 分鐘示範與 30 題題庫 → 各章「自我檢核」→ 附錄 C 公式卡。

**與 `../plan.md` 的關係**：plan.md 是練功路線（能力模組＋考核），本書是知識本體（機制＋深度＋判斷）。對應關係在 ch01 與 ch18 有完整表格；附錄 A 的每個實驗都標了 plan.md 模組歸屬。兩者搭配：照 plan.md 的模組推進，用本書對應章節補深度。

## 誠實聲明

- 本書由 AI 協作撰寫（2026-06），所有可查證事實均經網路查證並標註時點，但**版本號、價格、硬體預告屬月級變動**——動手前以官方文件為準。已知需要回查的項目集中在 `_meta/maintenance.md`。
- 各章的 worked example 是「方法可移植、數字要自己重測」——benchmark 示意數字均已標明假設。
