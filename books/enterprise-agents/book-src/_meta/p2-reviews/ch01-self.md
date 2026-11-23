# ch01 Self-Review Summary

- **Skeleton & Structure**: Verified all 6 required `##` headings in exact order (`從你已知的出發`, `核心機制`, `故障模式與防禦`, `動手做`, `自我檢核` + `### 參考解答`, `延伸閱讀`).
- **Bridge Compliance**: `tier=前段`, `bridge=有限狀態機與事件迴圈（FSM + Event Loop）` — present in `從你已知的出發` with explicit `成立邊界` and `失效邊界`, using technical-mechanism-to-technical-mechanism comparison only.
- **Base Numbers & Arithmetic**: All base numbers match `_meta/running-examples.md` verbatim (`50,000` tickets/day, `1,500,000`/month, `12` req/s peak, `2.5s` / `18s` SLO, `6,000` prefix tokens, `5` turns, `1,200` new input tokens/turn, `350` output tokens/turn, Sonnet 5.5 `$2.00 / $10.00`, Haiku 5.5 `$0.10 / $0.50`, `≤ $18,000` target). Re-computed all worked examples (5-turn uncached `$0.1015` / `$5,075` / `$152,250`, connection pool `90` in-flight / `128` `maxSockets`, and Self-Check Q3 Haiku 2-turn `$0.00167` / `$50.10` / `98.35%` reduction) — all exact.
- **Prose & Lint**: Zero Simplified Chinese, zero forbidden vocab, zero `vocab_regex_warn` hits, and zero CommonMark bold boundary violations.
- **Code Consistency**: `ch01-agent-architecture.md` TypeScript excerpt and CLI instructions are consistent with `examples/ts/ch01/index.ts` and `examples/py/ch01/main.py`.
- **Privacy**: Zero personal history, employer, or résumé leakage.
- **Edits Made**: None required; chapter and examples passed all checks as-is.
