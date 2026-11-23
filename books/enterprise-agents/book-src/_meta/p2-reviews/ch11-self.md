# Self-Review: ch11 (`ch11-enterprise-patterns-in-action.md`)

- **Skeleton**: All 6 required `##` headings present in exact order (`從你已知的出發`, `核心機制`, `故障模式與防禦`, `動手做`, `自我檢核` + `### 參考解答`, `延伸閱讀`).
- **Bridge compliance**: `tier=後段, bridge=none` — verified zero external analogies or metaphors.
- **Base numbers & arithmetic**: All `OrderOps` baselines (`50,000`/day, `12` req/s, `p95 ≤ 2.5s / 18s`, `≤ $18,000`/mo, `$152,250`/mo, `6,000`-token prefix, `18` tools, Haiku/Sonnet/Opus 5.5 pricing, `Batch API` 50% discount) match `_meta/running-examples.md` verbatim. Re-computed Scenario B (`$0.0355`/contract, `$213.00`/mo), Scenario C (`$0.0880`/incident, `$316.80`/mo), and Self-Check Q2 (`$0.0710`/contract, `$4,260`/mo) — all exact.
- **Prose & CommonMark**: Zero Simplified Chinese, zero forbidden vocab, zero translationese patterns, and all `**...**` spans keep CJK quotes/parentheses outside.
- **Code & examples**: Executed `npx tsx ch11/index.ts` and `python3 ch11/main.py`; both exited 0 and matched the chapter's expected output.
- **Personal leakage**: None.
- **Edits made**: None required.
