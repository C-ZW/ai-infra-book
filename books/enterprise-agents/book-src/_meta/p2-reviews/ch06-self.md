# ch06 Self-Review Summary

- **Skeleton**: Verified all 6 required `##` headings in exact order (`從你已知的出發`, `核心機制`, `故障模式與防禦`, `動手做`, `自我檢核` + `### 參考解答`, `延伸閱讀`).
- **Bridge**: Verified `tier=中段`, `bridge=熔斷器與 Transactional Outbox 模式` with explicit `成立邊界` and `失效邊界`.
- **Numbers & Arithmetic**: Verified all base numbers match `_meta/running-examples.md` verbatim (`50,000` 筆／天, `1,500,000` 筆／月, `12 req/s` / `0.58 req/s`, `5` 回合, Batch API `50%` 折扣 `$1.00 / $5.00`). Re-computed all steps in Worked Example (`60 calls/s`, `3,600 RPM`, `20 calls/s` excess, `600` queued requests, `37.1 calls/s` drain headroom, `16.2s` drain time) and Q3 (`100 calls/s`, `6,000 RPM`, `40 calls/s` excess, `1,800` queued requests).
- **Prose & Lint**: Zero Simplified Chinese, zero forbidden terms, zero CommonMark bold boundary violations. Replaced `進行容量與退避佇列估算` with `估算容量與退避佇列` on L99.
- **Code & Examples**: Executed both `examples/ts/ch06/index.ts` and `examples/py/ch06/main.py`; both exited 0 with expected output (`waiting_hitl`, `3` checkpoints -> `5` checkpoints, `completed`).
