# ch05 Self-Review Summary

- **File**: `books/enterprise-agents/book-src/ch05-multi-agent-orchestration.md`
- **Skeleton**: All 6 required `##` headings present in exact order (`從你已知的出發`, `核心機制`, `故障模式與防禦`, `動手做`, `自我檢核` + `### 參考解答`, `延伸閱讀`).
- **Bridge**: `tier=中段`, `bridge=分散式 Saga 編排與補償（Orchestrated Saga）` with explicit `成立邊界` and `失效邊界`.
- **Base Numbers & Arithmetic**: All base numbers match `_meta/running-examples.md` verbatim (`18` tools, `6,000` prefix tokens, `50,000` tickets/day, `p95 ≤ 18s`, Haiku `$0.10/$0.50`, Sonnet `$2.00/$10.00`, Opus `$4.00/$20.00`). Worked example arithmetic re-verified: Scheme A `$0.0600`, Scheme B `$0.000090 + $0.000560 + $0.004480 = $0.005130` (`91.45%` reduction).
- **Language & Lint**: Zero Simplified Chinese, zero `vocab_error` hits, zero `vocab_regex_warn` translationese hits, no CommonMark bold boundary violations adjacent to CJK, no personal/employer leakage.
- **Code & Execution**: Both `examples/ts/ch05/index.ts` (`npx tsx ch05/index.ts`) and `examples/py/ch05/main.py` (`python3 ...`) ran cleanly in offline simulation mode and matched the chapter's snippets and expected outputs (`0.00051` and `0.01811`).
- **Edits Made**: None required.
