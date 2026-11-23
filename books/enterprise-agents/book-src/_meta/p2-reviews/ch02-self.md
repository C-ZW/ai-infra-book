# Self-Review: ch02 (`ch02-tool-use-and-mcp.md`)

## Audit Results
- **Skeleton Headings**: All 6 required headings (`從你已知的出發`, `核心機制`, `故障模式與防禦`, `動手做`, `自我檢核` + `### 參考解答`, `延伸閱讀`) are present in exact order.
- **Bridge Compliance**: Tier = 前段, Bridge = 微服務 RPC 契約與冪等鍵（OpenAPI + Idempotency Key）, with explicit 成立邊界 and 失效邊界.
- **Base Numbers & Arithmetic**: All base numbers match `_meta/running-examples.md` verbatim (`18` tools = `12` read-only + `6` mutating, `6,000` prefix = `2,400` + `3,600`, `5` turns, `1,200` new input/turn, `350` output/turn, `42,000` / `1,750` tokens, `$0.1015` / ticket, `50,000` tickets/day, Sonnet 5.5 `$2.00` / `$10.00` per MTok). Worked example arithmetic (`$0.0275` extra turn, `$0.0033`/ticket at 12%, `$165.00`/day, `$4,950`/month) verified from scratch.
- **Language & Lint**: Zero Simplified Chinese, zero `vocab_error` terms, zero `vocab_regex_warn` translationese matches.
- **No Leakage**: Zero personal history, employer, or résumé references.

## Fixes Applied
1. **Code Consistency (`動手做`)**:
   - Replaced `IdempotentRefundLedger` with `IdempotentRefundExecutor` (3 occurrences) to match `examples/ts/ch02/index.ts` and `examples/py/ch02/main.py`.
   - Updated MCP `curl` endpoint from `http://127.0.0.1:8080/mcp` to `http://127.0.0.1:8787/mcp` to match the listening port `8787` in both `index.ts` and `main.py`.
2. **CommonMark Bold Boundary (`自我檢核`)**:
   - Fixed `**（入門｜10 分鐘）**`, `**（進階｜15 分鐘）**`, and `**（挑戰｜20 分鐘）**` to `（**入門｜10 分鐘**）`, `（**進階｜15 分鐘**）`, and `（**挑戰｜20 分鐘**）`.
