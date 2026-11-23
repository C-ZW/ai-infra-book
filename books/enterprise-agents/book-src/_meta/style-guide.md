# 寫作契約（Style Guide）— 企業級 Agent 工程

## 1. 目標讀者與口吻（Calibration Only）

- **讀者設定**：具 5–10 年經驗的資深後端工程師（`specialist` 語域）。
- **假設已知（不從零解釋）**：TypeScript / Node.js、Python 基礎語法、REST/RPC、關聯式資料庫（PostgreSQL/MySQL）、Redis、訊息佇列、分散式系統冪等性與重試、Docker/Kubernetes、CI/CD、基本自動化測試，以及日常操作 AI Coding Agent（如 Claude Code、Codex、Gemini CLI、自訂 Skills/Workflow）的實務手感。
- **從零建立（程式與工程深度）**：以程式碼（預設 Claude API：`@anthropic-ai/sdk` 與 Python `anthropic` SDK）從零建構可上線的企業級 AI Agent 系統——涵蓋執行迴圈狀態機、Tool Use 契約與 MCP、Context Engineering、持久化狀態與 Agentic RAG、多 Agent 協作、可靠性工程、Eval 評測與系統化調校、單位經濟學與成本／延遲優化、安全護欄與權限治理、可觀測性與上線維運。
- **口吻要求**：直接切入系統架構、底層機制、邊界條件（Edge Cases）、失敗模式與實作細節。零商業吹捧、零入門廢話。
- **個人材料禁令**：讀者個人背景僅供深度校準。**書中絕不出現任何特定個人經歷、任職公司、真實客戶或個人 Side Project**；所有企業場景皆為泛化設計（以主軸系統 `OrderOps` 與三個泛化企業案例呈現）。

## 2. 語言與措辭契約（zh-TW）

- 繁體中文（台灣工程用語），禁止簡體字與中國大陸術語（`軟件`→`軟體`、`內存`→`記憶體`、`默認`→`預設`、`大模型`→`LLM`、`智能體`→`Agent`、`提示詞`→`Prompt`）。
- 技術專有名詞保留英文（如 Tool Use、Prompt Caching、Context Rot、Idempotency Key、Rate Limit、Eval、Pass^k），不硬翻。
- 遵守 `references/zh-prose.md`：白話直述、動詞優先；避免「進行＋動作名詞」「透過…的方式」「在…的情況下」「對於…而言」「存在著」「作為一個…」等翻譯腔。
- **CommonMark 粗體邊界規則**（pitfalls #13）：全形引號與括號一律放在 `**...**` 之外（寫 `是「**詞**」`、`**詞**（註）`，絕不寫 `是**「詞」**`）。
- 程式碼註解、變數名、設定檔、log 訊息一律使用英文。

## 3. 書型契約（Instructional Form）

每章必須嚴格依序包含以下六個二級標題（`##`），與 `_meta/lint.config.json` 鎖定的 `skeleton_slots` 完全一致：

1. `## 從你已知的出發`
2. `## 核心機制`
3. `## 故障模式與防禦`
4. `## 動手做`
5. `## 自我檢核`
6. `## 延伸閱讀`

### 深度與實作要求

- **長度不設上限，但零灌水**：以「讓資深後端工程師徹底看懂機制並能動手做出企業級系統」為唯一標準。
- **真實數字 Worked Example（每章 ≥ 1 個）**：使用 fenced code block（或結構化算式區塊）帶入真實數字端到端計算（token 數、美元成本、延遲毫秒、配額吞吐、錯誤率或 Pass^k），禁止只丟抽象公式。所有跨章引用的基準數字必須與 `_meta/running-examples.md` 逐字一致。
- **程式碼片段 vs 完整程式碼**：
  - 章節內文只放**精簡、承重的核心程式碼片段**（標明關鍵機制、契約型別、API 呼叫或防禦邏輯），並清楚標註完整可執行檔案路徑（例如 `examples/ts/ch01/...` 與 `examples/py/ch01/...`）。
  - 完整可執行的 TypeScript（`@anthropic-ai/sdk` + `zod`）與 Python（`anthropic` + `pydantic`）程式碼統一放在 `books/enterprise-agents/examples/` 對應章節目錄。
- **練習與解答（`## 自我檢核`）**：
  - 每題標註**難度**（`入門` / `進階` / `挑戰`）與**預估時間**（如 `15 分鐘`）。
  - 緊接於題目之後必須有 `### 參考解答`（或 `### 解答`）子節，給出完整推導與工程取捨，不給敷衍一句話。
- **決策框架優先於工具清單**：提到任何 SDK、框架或協定，必先拆解其底層機制與取捨邊界。
- **實戰工程細節強制要求（Production Details）**：每章必須包含可直接落地的生產級細節，禁止只停留在概念描述：
  - **真實 API Payload 與欄位邊界**：展示關鍵請求／回應的真實欄位（如 `tool_use` / `tool_result` 配對 ID、`is_error: true`、`cache_control` 斷點位置、`usage.cache_read_input_tokens`、`thinking` block 與 `signature`、`stop_reason` 狀態分支）。
  - **具體數值與配置基線**：不寫「設定合理的 timeout／重試次數」，必須給出具體工程值與依據（例如單次 LLM timeout、Tool timeout、總 wall-clock 上限、`max_turns`、退避倍率與 Jitter、連線池／併發上限、SQL 表結構與索引鍵、Redis Key 命名與 TTL）。
  - **真實上線故障與排錯線索**：點名具體 HTTP 狀態碼與 Header（`429` + `retry-after`、`529 overloaded_error`、Streaming 半途斷線殘缺 JSON、Cache silent miss 導致 `cache_creation_input_tokens = 0`）、實際 log 欄位與告警閾值。

## 4. 橋接契約（Bridging Contract）

- 僅允許**技術機制對技術機制**的客觀對照（禁止日常比喻與第二人稱閒聊口吻）。
- 每章最多 1 個外部橋接，必須同時寫出「成立邊界」與「失效邊界」。
- 嚴格遵守 `outline.md` 的 Bridge Registry 與遞減排程：
  - 前段（ch01–ch04）：每章 1 個後端系統機制對照（全域每個來源 ≤ 1 次）。
  - 中段（ch05–ch08）：精簡後端架構對照並優先交叉引用前章已定義概念。
  - 後段（ch09–ch12）：**零外部比喻（`none`）**，全以本書已建立的原生 Agent 工程詞彙撰寫。

## 5. 符號與術語規範

| 規範寫法 | 意義 | 首次定義章節 |
|---|---|---|
| `Agent Loop` | 模型推理 → 工具執行 → 觀測回填的狀態轉移迴圈 | ch01 |
| `Turn`（回合） | Agent Loop 內一次完整的 Messages API 呼叫與其對應工具執行 | ch01 |
| `MTok` | 百萬 tokens（1,000,000 tokens），所有 API 計價單位 | ch01 |
| `TTFT` / `TPOT` | Time To First Token / Time Per Output Token | ch08 |
| `Pass@k` / `Pass^k` | k 次嘗試至少成功 1 次 / 連續 k 次全部成功 | ch07 |
| `HITL` | Human-in-the-Loop（人工審批／介入節點） | ch06 |
| `MCP` | Model Context Protocol | ch02 |
| `OrderOps` | 貫穿全書的企業級營運代理系統主軸範例 | ch01 |

- 數學表示採 Unicode 純文字（不啟用 KaTeX），如 `×`、`÷`、`≤`、`≥`、`≈`、`∑`、`^`。
- ASCII 架構圖遵守 CJK = 2 欄寬度對齊，複雜方框圖由 Python 腳本生成並通過 `check_diagrams.py`。
