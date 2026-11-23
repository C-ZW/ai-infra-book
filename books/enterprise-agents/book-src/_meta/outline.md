# 全書大綱（Outline）— 企業級 Agent 工程

**書名**：企業級 Agent 工程：用 Claude API 打造可上線、可觀測、可控成本的代理系統
**Slug / ID**：`enterprise-agents` / `eagent`
**書型**：`instructional`（教學實戰型，`zh-TW`，`specialist` 語域）
**完整程式碼路徑**：`books/enterprise-agents/examples/`（`ts/` TypeScript + `py/` Python 雙語言完整實作；章節內文僅放核心片段與檔路徑指標）

---

## 一、貫穿全書的主軸（Spine）

**OrderOps — 企業級營運與異常處理代理平台（Enterprise Operations Agent Platform）**

一個中型跨國電商與供應鏈平台的內部營運代理服務，每天處理 **50,000 筆**客戶與供應商異常工單（出貨延遲、庫存同步差異、退換貨審核、發票對帳、SLA 違約通知）。
全書 12 章從零把 `OrderOps` 從一個容易失控、每月燒掉 **$152,250** 的裸迴圈原型，一步步重構成具備嚴格工具契約、持久化狀態、多代理協作、Eval 回歸閘門、安全護欄、OpenTelemetry 觀測性，且月成本壓低至 **$18,000 以下**的生產級系統。
除主軸 `OrderOps` 外，第 11 章額外深入拆解兩個真實企業場景：**企業合約與法規合規審核助理**、**自動化 On-call 告警分診與程式碼審查 Agent**。

---

## 二、跨章一致性基準表（Base-Numbers Table — Single Source of Truth）

> 本表為全書唯一數字基準；`_meta/running-examples.md` 與 `_meta/maintenance.md` 皆由本表逐字複製，禁止在各章單獨修改數字。

| 基準項目 | 數值 | 單位 | 所屬概念 | 引用章節 |
|---|---|---|---|---|
| OrderOps 日工單量 | 50,000 | 筆／天（1,500,000 筆／月，以 30 天計） | 主軸工作負載 | ch01, ch06, ch08, ch10, ch11 |
| OrderOps 尖峰流量 | 12 | req/s（平均 0.58 req/s，尖峰 20×） | 吞吐與限流設計 | ch01, ch06, ch08, ch10 |
| OrderOps 延遲 SLO | 2.5 / 18 | 秒（分流 p95 ≤ 2.5s；多步工具處置 p95 ≤ 18s） | 延遲預算 | ch01, ch08, ch10, ch12 |
| OrderOps 工具總數 | 18 | 個工具（12 唯讀 Read-only + 6 寫入／金流 Mutating） | 工具面與權限切分 | ch02, ch05, ch08, ch09, ch11 |
| OrderOps 基準前綴大小 | 6,000 | tokens（System Prompt 2,400 + 18 工具 Schema 3,600） | Context 與快取基準 | ch02, ch03, ch08 |
| OrderOps 基準回合與輸出 | 5 / 1,200 / 350 | 回合 / 每回合新增輸入 tokens / 每回合輸出 tokens | 單筆基準消耗 | ch01, ch03, ch08 |
| OrderOps 未優化單筆消耗 | 42,000 / 1,750 | 累計輸入 tokens / 累計輸出 tokens（5 回合加總） | 成本基準 | ch01, ch08 |
| OrderOps 未優化基準成本 | $0.1015 / $5,075 / $152,250 | 單筆 / 每日 / 每月（全用 Sonnet 5.5、無快取） | 單位經濟學基準 | ch01, ch08, ch10, ch12 |
| Claude Haiku 5.5 牌價（≤100K） | $0.10 / $0.50 | USD / MTok（Input / Output；>100K 為 $0.50 / $2.50） | 模型分層計價 | ch01, ch05, ch08, ch09 |
| Claude Sonnet 5.5 牌價 | $2.00 / $10.00 | USD / MTok（Input / Output） | 預設工作層計價 | ch01, ch03, ch08, ch11 |
| Claude Opus 5.5 牌價 | $4.00 / $20.00 | USD / MTok（Input / Output） | 高風險仲裁層計價 | ch03, ch05, ch08, ch11 |
| Prompt Caching 寫入倍率 | 1.25× / 2.0× | 基礎輸入單價（5m TTL / 1h TTL） | 快取寫入成本 | ch03, ch08 |
| Prompt Caching 讀取倍率 | 0.05× / 0.10× | 基礎輸入單價（Sonnet/Opus 5.5 為 0.05×；Haiku 5.5 為 0.10×） | 快取命中折扣 | ch03, ch08 |
| Batch API 折扣 | 50% | Input 與 Output 同步半價（Sonnet 5.5 為 $1.00 / $5.00） | 非同步批次降本 | ch06, ch08, ch11 |
| 資料駐留附加倍率 | 1.1× | 啟用 `inference_geo: "us"` 全類別 token 費率倍率 | 法遵成本權衡 | ch08, ch09, ch12 |
| OrderOps 目標優化月成本 | ≤ $18,000 | USD / 月（降幅 ≥ 88%，單筆 ≤ $0.012） | 優化工程目標 | ch08, ch10, ch12 |

---

## 三、橋接登記表與遞減排程（Bridge Registry & Fade-out Schedule）

- **規則**：每章 ≤ 1 個外部橋接；全域每個來源 ≤ 1 次（遠低於上限 3 次）；僅限技術機制對照並明確標註「失效邊界」。
- **前段（ch01–ch04）**：每章 1 個資深後端機制對照。
- **中段（ch05–ch08）**：精簡系統機制對照，並優先引用前章已定義的 Agent 概念。
- **後段（ch09–ch12）**：**全部 `none`**，純以本書原生 Agent 工程詞彙撰寫。

| 章節 | 階段 | 指定橋接來源（或 `none`） |
|---|---|---|
| ch01 | 前段 | 有限狀態機與事件迴圈（FSM + Event Loop） |
| ch02 | 前段 | 微服務 RPC 契約與冪等鍵（OpenAPI + Idempotency Key） |
| ch03 | 前段 | CPU 快取局部性與虛擬記憶體分頁（Cache Prefix + Paging） |
| ch04 | 前段 | 資料庫預寫日誌與列級權限（WAL Checkpoint + Row-Level Security） |
| ch05 | 中段 | 分散式 Saga 編排與補償（Orchestrated Saga） |
| ch06 | 中段 | 熔斷器與 Transactional Outbox 模式 |
| ch07 | 中段 | CI 回歸測試套件與契約斷言（Regression Suite） |
| ch08 | 中段 | 雲端 FinOps 單位成本與 CDN 快取命中率 |
| ch09 | 後段 | `none`（原生詞彙） |
| ch10 | 後段 | `none`（原生詞彙） |
| ch11 | 後段 | `none`（原生詞彙） |
| ch12 | 後段 | `none`（原生詞彙） |

---

## 四、各章規格（Per-Chapter Specs）

### Part I：核心引擎與契約

#### ch01 (`ch01-agent-architecture.md`) — 從 Workflow 到 Agent：執行迴圈、狀態機與可控邊界
- **教學目標**：能判斷一個企業需求應寫成確定性 Workflow 還是 Agent，並能用 Claude Messages API 從零實作具備強制終止契約的最小 `OrderOps` Agent Loop。
- **Spine 觸點**：建立 `OrderOps` 基準情境（50,000 筆/天、5 回合、未優化月燒 $152,250），跑通第一版單工單處理迴圈。
- **Must-cover**：Workflow vs Agent 決策光譜（Augmented LLM、Chaining、Routing、Parallelization、Orchestrator-Workers、Evaluator-Optimizer）；LLM 無狀態本質與外部狀態機；`stop_reason`（`end_turn`、`tool_use`、`max_tokens`、`refusal`）驅動迴圈；硬性護欄（`max_turns`、token budget、wall-clock timeout）。
- **Must-NOT-cover**：Prompt Caching 細算（見 ch08）、MCP 協定細節（見 ch02）、持久化斷點續跑（見 ch06）。
- **Worked Example**：算清 `OrderOps` 5 回合無快取對話歷史膨脹（6,000 → 7,200 → 8,400 → 9,600 → 10,800 = 42,000 input tokens）與單筆 $0.1015 / 月 $152,250 成本帳。
- **完整程式碼**：`examples/ts/ch01/`、`examples/py/ch01/`（帶 budget guard 與 `stop_reason` 狀態機的 `OrderOps` 最小 Agent Loop）。

#### ch02 (`ch02-tool-use-and-mcp.md`) — Tool Use 契約、Strict Schema 與 MCP 企業整合
- **教學目標**：能設計抗幻覺、可自癒的工具介面，使用 `strict: true` 與 `output_config.format` 強制型別契約，並將企業工具封裝為 Stateless Streamable HTTP MCP Server。
- **Spine 觸點**：實作 `OrderOps` 的 18 個工具切分（12 唯讀 + 6 寫入），示範退款工具的 Idempotency Key 與兩階段確認契約。
- **Must-cover**：Tool Schema 設計原則（防參數歧義、枚舉約束、錯誤訊息作為給模型的觀測而非例外中斷）；`strict: true` Tool Use 與 `output_config.format`（Zod / Pydantic）；寫入型工具的冪等鍵與乾跑（dry-run）；MCP 傳輸層演進（Stdio vs Streamable HTTP）、Stateless HTTP 水平擴展與 Claude API `mcp_servers` Connector。
- **Must-NOT-cover**：Prompt Injection 權限攻擊防禦全貌（見 ch09）、工具動態裁切降本細算（見 ch08）。
- **Worked Example**：18 個工具 Schema 佔用 3,600 tokens 的前綴開銷計算，以及嚴格 Schema 下非法參數重試率從 12% 降至 0% 所省下的額外回合成本。
- **完整程式碼**：`examples/ts/ch02/`、`examples/py/ch02/`（Strict Tool Use + Zod/Pydantic `output_config.format` + Streamable HTTP MCP Server 範例）。

#### ch03 (`ch03-context-and-prompt-engineering.md`) — Context Engineering：從 Prompt 調校到上下文預算管理
- **教學目標**：能用系統工程思維設計 Context 結構，避免 Context Rot、最大化 Prompt Cache 前綴命中，並正確配置 Extended Thinking 與長對話 Compaction。
- **Spine 觸點**：將 `OrderOps` 的 6,000-token 前綴重組為「靜態前綴 + 動態工單載荷」，並實作工具大回傳裁剪與第 4 回合後摘要壓縮。
- **Must-cover**：Context Window 組成與 Context Rot（中間遺失與干擾物稀釋）；前綴穩定排序（`tools` → `system` → `messages`）與 `cache_control` 斷點擺放；XML 結構化分區與 Few-shot 邊界案例；Extended Thinking（`budget_tokens`、`max_tokens > budget_tokens`、多回合保留 `thinking` block 與 signature）；工具結果截斷、Compaction 與 Scratchpad 模式。
- **Must-NOT-cover**：Prompt Caching 完整 5m vs 1h FinOps 財務建模（見 ch08）、向量檢索演算法細節（見 ch04）。
- **Worked Example**：開啟 Extended Thinking（`budget_tokens: 4,000`）對單筆高難度工單成本與 `max_tokens` 配額的影響實算，以及工具回傳從 8,000 tokens 裁剪為 600 tokens 對後續 3 回合累計輸入的乘法節省。
- **完整程式碼**：`examples/ts/ch03/`、`examples/py/ch03/`（前綴分層 Prompt Builder + Extended Thinking 多回合保留 + Compaction 壓縮器）。

---

### Part II：狀態、記憶與多代理協作

#### ch04 (`ch04-state-memory-and-retrieval.md`) — 持久化狀態、多層記憶與企業知識檢索（Agentic RAG）
- **教學目標**：能將 Agent 對話狀態持久化至 PostgreSQL/Redis 支援跨請求續跑，並建構具多租戶 ACL 隔離與引用溯源的 Agentic RAG。
- **Spine 觸點**：讓 `OrderOps` 能跨小時恢復等待供應商回覆的工單狀態，並在查詢退貨政策與供應商合約時附帶精準條文 Citations。
- **Must-cover**：三層記憶模型（Working Context、Session State Store、Long-term Episodic/Semantic Memory）；對話歷史與工具結果的 Schema 化持久化；傳統靜態 RAG 的盲點 vs Agentic RAG（Hybrid Search BM25 + Vector + Rerank，由 Agent 自主決定檢索查詢與重試）；多租戶 ACL 前置過濾（Pre-filtering，絕不在 LLM 輸出後才過濾）；Citation 驗證。
- **Must-NOT-cover**：跨節點分散式重試與 Outbox（見 ch06）、資安 Prompt Injection 攻防細節（見 ch09）。
- **Worked Example**：比較靜態 RAG 每次塞入 Top-10 文件（+6,500 tokens/筆）與 Agentic RAG 按需檢索（僅 35% 工單觸發、Top-3 精準段落 +1,800 tokens）在 50,000 筆/天下的 token 與成本差額。
- **完整程式碼**：`examples/ts/ch04/`、`examples/py/ch04/`（PostgreSQL/SQLite Session Store + 多租戶 Hybrid Search 檢索工具與 Citation 檢查）。

#### ch05 (`ch05-multi-agent-orchestration.md`) — 多 Agent 協作架構：Orchestrator、Handoff 與隔離沙盒
- **教學目標**：能辨別何時該拆分多 Agent，設計 Context 隔離的 Orchestrator-Workers 與 Router-Specialists 拓撲，並評估自建 Loop 與 Claude Agent SDK 的取捨。
- **Spine 觸點**：把 `OrderOps` 拆分為「Haiku 分流 Router + 唯讀調查 Worker + 高風險退款仲裁 Opus Specialist」，隔離工具面與上下文。
- **Must-cover**：單 Agent 的擴展瓶頸（工具過多導致選錯、長調查汙染決策上下文、權限無法最小化）；三大協作拓撲（Router + Specialists、Orchestrator-Workers、Evaluator-Optimizer）；Sub-agent 上下文壓縮回傳契約；平行扇出（Fan-out）與部分失敗處理；自建 Loop vs Claude Agent SDK（`@anthropic-ai/claude-agent-sdk` / `claude-agent-sdk`）選型邊界。
- **Must-NOT-cover**：模型路由的完整月度財務總帳（見 ch08）、底層佇列與 Saga 重放細節（見 ch06）。
- **Worked Example**：單一 Sonnet 攜帶全部 18 個工具（6,000 token 前綴）vs Router（Haiku，0 工具）+ 3 個 Specialist（各 6 工具，前綴 2,800 tokens）的上下文與工具誤觸率對照實算。
- **完整程式碼**：`examples/ts/ch05/`、`examples/py/ch05/`（Orchestrator-Workers 平行調度器與 Handoff 狀態傳遞實作）。

#### ch06 (`ch06-reliability-and-durable-execution.md`) — 企業級可靠性：重試、熔斷、Checkpoint 與長任務執行
- **教學目標**：能讓 Agent 在 LLM API 限流、Streaming 斷線、外部 ERP 逾時與人工審批暫停下，依然保證不重複扣款、不遺失進度。
- **Spine 觸點**：為 `OrderOps` 的退款與批次對帳流程實作 Event-sourced Checkpoint、429/529 指數退避與 HITL 暫停／喚醒狀態機。
- **Must-cover**：LLM 與工具雙層故障分類（429 Rate Limit、529 Overloaded、Streaming 半途斷裂、Tool 逾時與部分寫入）；Token Bucket 與 Retry-After 感知的退避重試；Checkpoint / Replay 執行日誌設計；非同步 Worker Queue 與 Batch API 狀態追蹤；Human-in-the-Loop（HITL）審批暫停、超時升級與喚醒續跑。
- **Must-NOT-cover**：OpenTelemetry 監控儀表板與告警（見 ch10）、安全權限引擎細節（見 ch09）。
- **Worked Example**：`OrderOps` 尖峰 12 req/s、每筆平均 5 次 API 呼叫（= 60 RPM 尖峰轉換為 3,600 API calls/min）下的 Rate Limit（RPM / ITPM / OTPM）容量與退避佇列深度估算。
- **完整程式碼**：`examples/ts/ch06/`、`examples/py/ch06/`（Checkpoint Durable Runner + Exponential Backoff with Jitter + HITL Pause/Resume 狀態機）。

---

### Part III：優化、調校與單位經濟學

#### ch07 (`ch07-evals-and-systematic-tuning.md`) — 評測驅動開發（EDD）：建立可量化的 Eval 與調校迴圈
- **教學目標**：能建立涵蓋結果與工具軌跡的自動化 Eval 套件，運用 Pass^k 衡量企業可靠性，並以錯誤分類（Error Taxonomy）系統化調校 Prompt、工具描述與模型參數。
- **Spine 觸點**：為 `OrderOps` 建立 100 題黃金評測集（涵蓋正常工單、邊界異常、誘騙輸入），示範一次從 78% → 95% 通過率的系統化調校實錄。
- **Must-cover**：三層評測器（確定性 Code Grader、校準後的 LLM-as-a-Judge、人工抽檢）；Trajectory Eval（工具呼叫順序、參數正確性、冗餘步數）；Pass@k vs Pass^k 數學意義（為什麼 90% 單次成功率在 5 步任務只剩 59%）；Error Taxonomy 驅動的調校工作流（Prompt 改寫 vs 工具 Schema 重構 vs 模型升級）；把 Eval 整合進 CI/CD 防止回歸。
- **Must-NOT-cover**：線上流量影子部署與模型漂移監控（見 ch10）。
- **Worked Example**：Pass^k 數學實算（單步準確率 p = 0.90 vs 0.98 在 5 步與 10 步下的整條任務成功率；k=5 次重複執行全對率 Pass^5），以及 100 題黃金集每次 CI 跑 Eval 的 Claude API 成本核算。
- **完整程式碼**：`examples/ts/ch07/`、`examples/py/ch07/`（Trajectory + Code Grader + LLM-as-a-Judge 評測執行器與報表產出）。

#### ch08 (`ch08-cost-and-latency-optimization.md`) — 成本與延遲優化：從 $152,250/月壓到 $18,000/月的工程帳本
- **教學目標**：能精算 Agent 系統的單位經濟學，依序套用五大降本槓桿與四大延遲優化手法，並量化每項優化對品質與 SLO 的影響。
- **Spine 觸點**：把 `OrderOps` 從 ch01 基準 **$152,250 / 月** 逐步優化至 **≤ $18,000 / 月**（降幅 ≥ 88%），同時將分流 p95 壓在 2.5s 內、多步處置 p95 壓在 18s 內。
- **Must-cover**：五大降本槓桿與精算：(1) Model Routing（60% 簡單工單 Haiku 5.5 + 35% 標準工單 Sonnet 5.5 + 5% 高風險 Opus 5.5）；(2) Prompt Caching（5m vs 1h TTL 損益平衡、0.05×/0.10× 讀取折扣與 512/1024 最小門檻陷阱）；(3) Context Compaction 與工具回傳裁剪；(4) Batch API 50% 折扣（將 30% 非即時對帳／稽核工單轉離線批次）；(5) 工具分組精簡前綴。延遲優化：TTFT vs TPOT 拆解、Streaming 漸進回傳、平行 Tool Calls、預取（Prefetch）與 Speculative 並行護欄。
- **Must-NOT-cover**：雲端法遵 `inference_geo` 的法務合規條文（見 ch09，本章僅算 1.1× 成本影響）。
- **Worked Example**：完整的 `OrderOps` 5 階段降本瀑布帳本（逐步列出 input/output/cache-write/cache-read tokens、單筆成本、月成本與累積降幅，全部算式閉合且經獨立驗算）。
- **完整程式碼**：`examples/ts/ch08/`、`examples/py/ch08/`（Model Router + Prompt Caching 前綴管理 + Batch API 提交流程 + 單筆即時成本計費器）。

#### ch09 (`ch09-security-guardrails-and-governance.md`) — 安全、護欄與企業治理：對抗 Prompt Injection 與越權
- **教學目標**：能針對 Agent 特有攻擊面建立縱深防禦，將權限檢查與高風險寫入控制從「靠 Prompt 勸說」移至確定性 Policy Engine。
- **Spine 觸點**：加固 `OrderOps` 對抗惡意客訴工單中的間接 Prompt Injection（企圖誘騙 Agent 執行超額退款或洩漏其他客戶資料），建立退款上限 Policy Engine 與完整 Audit Trail。
- **Must-cover**：Agent 威脅模型（Direct/Indirect Prompt Injection、Tool Argument Tampering、Data Exfiltration、Confused Deputy）；縱深防禦分層（Haiku 輕量輸入分類器、資料與指令隔離、最小權限 Scoped Token、確定性 Policy Engine 攔截寫入與金額門檻、輸出 PII 遮罩）；程式碼執行與外部呼叫的沙盒隔離；不可竄改 Audit Trail、資料駐留（`inference_geo: "us"` 1.1× 成本與延遲權衡）與零訓練保留政策驗證。
- **Must-NOT-cover**：通用 Web OWASP 基礎（假設讀者已知）、Eval 評測框架建置（見 ch07）。
- **Worked Example**：在 50,000 筆/天流量下，前置 Haiku 5.5 護欄分類器（每筆 500 input / 50 output tokens）的每日附加成本與延遲開銷，對比一次未攔截超額退款事故的預期損失（Expected Loss）。
- **完整程式碼**：`examples/ts/ch09/`、`examples/py/ch09/`（確定性 Policy Engine + PII Redactor + Haiku Input Guardrail 中介層）。

---

### Part IV：可觀測性與企業實戰藍圖

#### ch10 (`ch10-observability-and-operations.md`) — 可觀測性與維運：Trace、成本歸因、漂移監控與上線切換
- **教學目標**：能為 Agent 系統建立端到端分散式追蹤、按租戶／工單類型歸因成本，並設計安全的影子流量、金絲雀發布與模型升級切換流程。
- **Spine 觸點**：為 `OrderOps` 加上 OpenTelemetry Trace（Request → Turn → LLM/Tool Span）、即時每筆成本追蹤與異常迴圈告警。
- **Must-cover**：Agent 專用遙測結構（OpenTelemetry GenAI 語意慣例：記錄 `model`、`input_tokens`、`cache_read_tokens`、`stop_reason`、tool latency、cost_usd）；核心維運指標（Task Completion Rate、Tool Error Rate、Cache Hit Ratio、Cost per Ticket、p95 Latency、HITL Escalation Rate）；成本異常熔斷（單筆／每小時預算上限）；Shadow Mode、Canary Rollout 與模型版本 Pinning／升級回歸流程。
- **Must-NOT-cover**：Prometheus/Grafana 基礎安裝教學（假設讀者已知）。
- **Worked Example**：偵測 Prompt Cache 失效事故——當某次部署意外在 System Prompt 前段插入動態 `timestamp` 導致 Cache Hit Ratio 從 85% 暴跌至 0%，計算 4 小時內 `OrderOps` 多燒的美元金額與告警觸發閾值設計。
- **完整程式碼**：`examples/ts/ch10/`、`examples/py/ch10/`（OpenTelemetry Tracer 封裝 + Token/Cost Attribution 攔截器 + Budget Circuit Breaker）。

#### ch11 (`ch11-enterprise-patterns-in-action.md`) — 三大企業實戰場景深度拆解
- **教學目標**：能將前 10 章的架構組件組裝並遷移到三類截然不同的企業生產場景，掌握各場景的專屬瓶頸與架構取捨。
- **Spine 觸點**：先收束 `OrderOps` 端對端完整生產架構，再橫向對照另兩個真實企業場景（合約合規審核、On-call 分診與 PR 審查）。
- **Must-cover**：
  1. **場景 A：OrderOps 跨系統營運與退款自動化**（多 ERP 唯讀查詢 + 冪等寫入 + HITL 門檻 + 成本壓至 ≤ $18,000/月）。
  2. **場景 B：企業合約與法規合規審核助理**（長合約切分與索引、Extended Thinking 條款風險比對、強制原文 Citations、夜間 Batch API 批次掃描 50% 降本）。
  3. **場景 C：自動化 On-call 告警分診與程式碼審查 Agent**（唯讀 Log/Metrics/Trace MCP 工具 + 隔離沙盒重現測試 + 結構化 PR Review 輸出 + 防根因幻覺的證據鏈規則）。
- **Must-NOT-cover**：重複解釋前章單一機制定義（一律以 `（見 chNN）` 指向）。
- **Worked Example**：三大場景的單位經濟學與架構橫向對比表（日請求量、平均 Context、選用模型組合、是否用 Batch/Thinking、單次成本與 ROI 計算）。
- **完整程式碼**：`examples/ts/ch11/`、`examples/py/ch11/`（場景 B 合約審核 Pipeline 與場景 C 告警分診 Agent 的可執行骨幹）。

#### ch12 (`ch12-production-readiness-blueprint.md`) — 從原型到上線：架構決策清單、組織落地與演進路線
- **教學目標**：能主導一個企業級 Agent 專案從 POC 走到正式上線，完成 PRR 審查、技術棧選型（裸 API vs Agent SDK vs 框架）與分階段自動化演進。
- **Spine 觸點**：對 `OrderOps` 執行完整的上線前 Production Readiness Review（PRR），制定 L1 → L2 → L3 漸進式上線與退場回滾計畫。
- **Must-cover**：Buy vs Build 決策矩陣（裸 Claude API + 自建狀態機 vs Claude Agent SDK vs 第三方編排框架，分析抽象洩漏與除錯成本）；企業級 PRR 檢查表（可靠性、Eval 基準、安全護欄、成本上限、觀測告警、合規審計）；漸進式自主權路線（L1 Copilot 輔助 → L2 HITL 人工核准 → L3 有界全自動）；五種常見企業 Agent 專案上線失敗模式復盤。
- **Must-NOT-cover**：重複詳解各子系統實作細節（一律回指 ch01–ch11）。
- **Worked Example**：`OrderOps` 上線 90 天分階段流量切換計畫（Shadow 14 天 → 5% Canary L2 → 30% L2 → 100% L2/L3 混合），計算各階段人工覆核工時節省與 API 成本的淨 ROI 損益平衡點。
- **完整程式碼**：`examples/ts/ch12/`、`examples/py/ch12/`（Production Readiness 自動化啟動檢查腳本與 Config Validator）。
