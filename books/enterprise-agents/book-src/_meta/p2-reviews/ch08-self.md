# Self-Review: ch08 (`ch08-cost-and-latency-optimization.md`)

- **Skeleton**: Verified exact 6 `##` headings in order (`從你已知的出發`, `核心機制`, `故障模式與防禦`, `動手做`, `自我檢核` + `### 參考解答`, `延伸閱讀`).
- **Bridge compliance**: Verified `tier=中段`, bridge=雲端 FinOps 單位成本與 CDN 快取命中率, with both `成立邊界` and `失效邊界`.
- **Base numbers & arithmetic**: Verified all base numbers match `_meta/running-examples.md` verbatim. Re-computed Stage 0–5 waterfall (`$152,250.00` → `$14,789.55`/月, `$0.00986`/筆, `90.3%` 降幅), `inference_geo="us"` (`$16,268.51`/月), and `參考解答` #1 TTL comparison (`22,500` vs `12,600`, `44%` savings); all exact.
- **Language & lint**: Zero Simplified Chinese, zero `vocab_error`, zero `vocab_regex_warn`, zero personal/employer/résumé leakage.
- **CommonMark bold boundary**: Fixed 3 `**（...）**` occurrences in `## 自我檢核` (lines 172–174) to `（**...**）` atomically via `.tmp` + `mv`.
- **Code consistency**: Ran `python3 books/enterprise-agents/examples/py/ch08/main.py` and `npx tsx books/enterprise-agents/examples/ts/ch08/index.ts`; both exited 0 and matched the chapter's expected output.
