# Self-Review: ch12 (`ch12-production-readiness-blueprint.md`)

- **Skeleton**: 6 required headings present in exact order (`從你已知的出發`, `核心機制`, `故障模式與防禦`, `動手做`, `自我檢核` + `### 參考解答`, `延伸閱讀`).
- **Bridge compliance**: `tier=後段`, `bridge=none` — zero external analogies; uses only native Agent engineering terms.
- **Base numbers & arithmetic**: All base numbers match `_meta/running-examples.md` verbatim (`50,000/day`, `1,500,000/mo`, `$152,250` unoptimized, `<= $18,000` target, `2.5s / 18s` SLO, `18` tools, `1.1x` US residency). Re-computed every step in the 90-day rollout worked example and Self-Check #3; all arithmetic is exact.
- **Prose & CommonMark**: Zero Simplified Chinese, zero forbidden vocabulary, zero translationese patterns, and zero CommonMark bold-boundary violations.
- **Code consistency**: Inline TS snippet matches `examples/ts/ch12/index.ts`; both `examples/py/ch12/main.py` and `examples/ts/ch12/index.ts` executed and exited `0` with all gates `[PASS]`.
- **Personal leakage**: None.
- **Edits made**: None required.
