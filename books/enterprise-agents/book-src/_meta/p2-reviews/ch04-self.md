# Self-Review: ch04 (`ch04-state-memory-and-retrieval.md`)

- **Skeleton & Headings**: Verified all 6 required `##` headings in exact order (`從你已知的出發`, `核心機制`, `故障模式與防禦`, `動手做`, `自我檢核` + `### 參考解答`, `延伸閱讀`).
- **Bridge Compliance**: Tier=前段, Bridge=WAL Checkpoint + Row-Level Security (RLS) in `從你已知的出發`, with explicit 成立邊界 and 失效邊界.
- **Base Numbers & Arithmetic**: Verified against `_meta/running-examples.md` (`50,000` tickets/day, `1,500,000` tickets/month, Sonnet 5.5 `$2.00 / MTok`, `6,000` tokens prefix, `18` tools, `0.05×` cache read). Recomputed worked example (`$650/day` vs `$63/day`, saving `$17,610/month` or `90.3%`) and Q1 answer (`5 × 1,000 tokens × $2.00/MTok = $0.01/ticket`, `$500/day`); all exact.
- **Prose & CommonMark**: Zero forbidden vocab, zero translationese hits, zero Simplified Chinese, and zero CommonMark bold boundary violations.
- **Code & Examples**: `verifyCitations` snippet matches `examples/ts/ch04/index.ts` verbatim. Executed both `examples/py/ch04/main.py` and `examples/ts/ch04/index.ts`; both passed and matched expected output.
- **Fixes Applied**: None required.
