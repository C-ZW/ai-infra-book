# 附錄 A：完整程式碼範例索引（TypeScript & Python）

本書所有章節的完整可執行程式碼皆位於 `books/enterprise-agents/examples/`，採 TypeScript（`@anthropic-ai/sdk` + `zod`）與 Python（`anthropic` + `pydantic`）雙語言同步實作，並共用 `shared/` 內的 `OrderOps` 領域型別、2026-11 Claude API 牌價計費器與模擬後端。

## 執行環境準備

```bash
# TypeScript (Node.js 20+)
cd books/enterprise-agents/examples/ts
npm install
export ANTHROPIC_API_KEY="sk-ant-..."
npx tsx ch01/index.ts

# Python (Python 3.10+)
cd books/enterprise-agents/examples/py
pip install -e .
export ANTHROPIC_API_KEY="sk-ant-..."
PYTHONPATH=. python3 ch01/main.py
```

## 分章程式碼對照表

| 章節 | 主題 | TypeScript 完整實作 | Python 完整實作 |
|---|---|---|---|
| 共用模組 | 領域型別、2026-11 計費器、OrderOps Mock | `examples/ts/shared/types.ts`, `orderops-mock.ts` | `examples/py/shared/types.py`, `orderops_mock.py` |
| **ch01** | Agent Loop 狀態機、`stop_reason` 與預算護欄 | `examples/ts/ch01/index.ts` | `examples/py/ch01/main.py` |
| **ch02** | Strict Tool Use、`output_config.format` 與 MCP Server | `examples/ts/ch02/index.ts` | `examples/py/ch02/main.py` |
| **ch03** | 前綴穩定 Prompt Builder、Extended Thinking 與 Compaction | `examples/ts/ch03/index.ts` | `examples/py/ch03/main.py` |
| **ch04** | 持久化 Session Store 與多租戶 Agentic RAG | `examples/ts/ch04/index.ts` | `examples/py/ch04/main.py` |
| **ch05** | Router-Specialists 與 Orchestrator-Workers 協作 | `examples/ts/ch05/index.ts` | `examples/py/ch05/main.py` |
| **ch06** | Event-sourced Checkpoint、429/529 退避與 HITL 續跑 | `examples/ts/ch06/index.ts` | `examples/py/ch06/main.py` |
| **ch07** | Trajectory Eval、Code Grader 與 LLM-as-a-Judge | `examples/ts/ch07/index.ts` | `examples/py/ch07/main.py` |
| **ch08** | Model Router、Prompt Caching、Batch API 與成本計費器 | `examples/ts/ch08/index.ts` | `examples/py/ch08/main.py` |
| **ch09** | 確定性 Policy Engine、PII 遮罩與 Haiku 輸入護欄 | `examples/ts/ch09/index.ts` | `examples/py/ch09/main.py` |
| **ch10** | OpenTelemetry GenAI Trace 與預算異常熔斷器 | `examples/ts/ch10/index.ts` | `examples/py/ch10/main.py` |
| **ch11** | 合約合規審核 Pipeline 與 On-call 分診 Agent | `examples/ts/ch11/index.ts` | `examples/py/ch11/main.py` |
| **ch12** | Production Readiness Review（PRR）自動啟動檢查器 | `examples/ts/ch12/index.ts` | `examples/py/ch12/main.py` |
