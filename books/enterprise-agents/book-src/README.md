# 企業級 Agent 工程

**用 Claude API 打造可上線、可觀測、可控成本的代理系統**

本書面向具多年後端系統開發經驗的工程師，跳過入門概念與黑箱框架搬運，直接從底層機制、狀態機契約、分散式可靠性、量化評測、單位經濟學與安全治理，一步步把一個每天處理 **50,000 筆**工單、未優化月燒 **$152,250** 的營運代理系統（`OrderOps`），改造成月成本 **≤ $18,000**（降幅 ≥ 88%）、具備完整觀測與安全防禦的生產級系統。

## 閱讀方式與程式碼配置

- **章節內文**：只呈現承重的核心程式碼片段、真實 API Payload、具體配置基線與端到端數字實算。
- **完整可執行程式碼**：雙語言完整實作統一放在專案目錄 [`books/enterprise-agents/examples/`](../examples/README.md) 下：
  - TypeScript（`@anthropic-ai/sdk` + `zod`）：`examples/ts/ch01/` 至 `examples/ts/ch12/`
  - Python（`anthropic` + `pydantic`）：`examples/py/ch01/` 至 `examples/py/ch12/`

## 全書路線

- **Part I：核心引擎與契約（ch01–ch03）** — Agent Loop 狀態機、Strict Tool Use 與 Streamable HTTP MCP、Context Engineering 與 Extended Thinking。
- **Part II：狀態、記憶與多代理協作（ch04–ch06）** — 持久化 Checkpoint 與多租戶 Agentic RAG、多 Agent 隔離與協作、429/529 重試與 HITL 斷點續跑。
- **Part III：優化、調校與單位經濟學（ch07–ch09）** — 評測驅動開發（EDD）與 `Pass^k`、五大降本槓桿與延遲優化帳本、安全護欄與確定性 Policy Engine。
- **Part IV：可觀測性與企業實戰藍圖（ch10–ch12）** — OpenTelemetry GenAI 追蹤與成本歸因、三大企業實戰場景深度拆解、Production Readiness Review 與漸進式上線路線。
