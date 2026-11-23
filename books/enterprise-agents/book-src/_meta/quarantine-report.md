# P4 Tier-2 Quarantine Report (After 2 Adjudication Rounds)

- **Date**: 2026-11-21
- **Overall Tier-2 Verdict**: `WARN` (`0 FAIL`, `0 INCONCLUSIVE`, `degraded: false`)
- **Writer Family**: `google` (`gemini-4-hydrogen-low`); Conclusive Non-Writer Panelists: `openai` + `anthropic` (`claude` CLI)
- **P4 Bridging Review**: `12/12 passed/exempt`
- **P4.5 Teach-Test**: `12/12 passed`

## Remaining Single-Family `incorrect` Findings (5 total — OpenAI only; Anthropic did not flag `incorrect`)

### `ch01-agent-architecture.md` [openai:incorrect]
- **Claim**: if (controller.signal.aborted || err instanceof Anthropic.APIConnectionTimeoutError) { return { status: "timeout", stopReason: "wall_clock_timeout", /* ... */ }; }
- **Reasoning**: 程式將計時器設為單輪上限與總剩餘時間的較小值。若單輪上限為 5 秒、總剩餘時間為 18 秒，計時器在約 5 秒觸發時，總 wall-clock 期限尚未到，程式卻標記為 wall_clock_timeout。APIConnectionTimeoutError 也不能單憑其類型證明總期限已到。
- **Suggested**: 應依實際總期限是否到達區分 wall_clock_timeout 與單輪或 API 逾時，並保留可辨識的逾時原因。

### `ch05-multi-agent-orchestration.md` [openai:incorrect]
- **Claim**: 每次 API 回應的 usage……分別換算為美元後累加寫入 WorkerHandoff.costUsd；逾時等無法確認的帳務則另行標示並對帳。
- **Reasoning**: 展示的失敗分支對所有逾時或例外一律回傳 costUsd: 0。若 Worker 在失敗前已有成功回應並產生可確認費用，這些已知費用不會由該分支帶入，與累加已知成本的要求不一致。costStatus: unconfirmed 能標示未知部分，不能補回已知的漏計金額。
- **Suggested**: 將每次已確認呼叫的累積費用保存在失敗時仍可讀取的狀態，失敗交接時填入該已知金額，並另外標示及對帳未確認費用。

### `ch06-reliability-and-durable-execution.md` [openai:incorrect]
- **Claim**: Streaming 殘缺 JSON 的生產級防禦為「僅在收到 message_stop 且 JSON Schema 驗證通過後才寫入 llm_turn；否則丟棄重試」。
- **Reasoning**: 章內已指出 MCP Connector 等遠端代呼叫模式可能在串流中斷前執行工具。收到不完整串流時，丟棄殘缺輸出可以避免直接執行不完整參數，但不代表外部副作用尚未發生；直接重試整個回合可能重複派送寫入操作。
- **Suggested**: 丟棄不可用的殘缺輸出；確認沒有外部副作用後才重試。若遠端工具可能已執行，應先查詢狀態，依冪等保障決定是否同鍵重送，無法安全確認時轉人工對帳。

### `ch06-reliability-and-durable-execution.md` [openai:incorrect]
- **Claim**: 「429 與 529 雖同屬瞬態錯誤」。
- **Reasoning**: 章內前文區分了暫時性的配額或流量限制，並指出支出上限型 429 可能沒有 retry-after、不應無止盡重試。因此不能把所有 429 都概括為會自行恢復的瞬態錯誤。
- **Suggested**: 529 可按章內設定視為過載類瞬態故障；429 應先辨識原因，暫時性限流可依限制與預算重試，支出上限等情況則須先排除根因。

### `ch10-observability-and-operations.md` [openai:incorrect]
- **Claim**: PostgreSQL 帳本應保留 ticket_id、turn_index 與上游 request_id 供對帳。
- **Reasoning**: 文字要求保留 ticket_id，但緊接著的 CREATE TABLE 只有 trace_id、turn_index、upstream_request_id 等欄位，沒有 ticket_id。若 trace_id 與工單並非一對一，也不能僅憑現有欄位可靠地按工單對帳。
- **Suggested**: 在帳本加入 ticket_id 欄位，例如 ticket_id TEXT NOT NULL；或明確提供可可靠連回工單的關聯方式。

## Per-Chapter Summary

| Chapter | Verdict | Non-Google `incorrect` | Non-Google `imprecise` |
|---|---|---:|---:|
| `ch01-agent-architecture.md` | `WARN` | 1 | 3 |
| `ch02-tool-use-and-mcp.md` | `WARN` | 0 | 4 |
| `ch03-context-and-prompt-engineering.md` | `WARN` | 0 | 6 |
| `ch04-state-memory-and-retrieval.md` | `WARN` | 0 | 4 |
| `ch05-multi-agent-orchestration.md` | `WARN` | 1 | 7 |
| `ch06-reliability-and-durable-execution.md` | `WARN` | 2 | 4 |
| `ch07-evals-and-systematic-tuning.md` | `WARN` | 0 | 6 |
| `ch08-cost-and-latency-optimization.md` | `WARN` | 0 | 6 |
| `ch09-security-guardrails-and-governance.md` | `WARN` | 0 | 7 |
| `ch10-observability-and-operations.md` | `WARN` | 1 | 5 |
| `ch11-enterprise-patterns-in-action.md` | `WARN` | 0 | 7 |
| `ch12-production-readiness-blueprint.md` | `WARN` | 0 | 6 |
