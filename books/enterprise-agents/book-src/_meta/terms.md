# 全書術語對照表（P2.5 Terms Registry）

| 術語 | 首次定義章節 | 簡要定義 |
|---|---|---|
| `Agent Loop` | ch01 | 以 LLM 為無狀態轉移函數、由外部狀態機驅動 `stop_reason` 與工具執行的閉環 |
| `Turn`（回合） | ch01 | Agent Loop 內一次完整的 Messages API 呼叫與其對應工具執行 |
| `OrderOps` | ch01 | 貫穿全書的企業級營運代理主軸系統（50,000 筆/天、18 工具、未優化月燒 $152,250） |
| `Strict Tool Use`（`strict: true`） | ch02 | 解碼期以文法約束強制工具名稱與參數符合 JSON Schema |
| `Structured Outputs`（`output_config.format`） | ch02 | 以 JSON Schema 約束模型最終文字輸出結構 |
| `Idempotency Key`（冪等鍵） | ch02 | 具寫入／金流副作用的工具防重放與防重複扣款的唯一鍵 |
| `Streamable HTTP MCP` | ch02 | 取代舊版 HTTP+SSE 的遠端 MCP 單端點傳輸標準，支援 Stateless 水平擴展 |
| `Context Rot` | ch03 | 上下文拉長後注意力稀釋與中段資訊召回衰退現象 |
| `Prompt Caching`（`cache_control`） | ch03 / ch08 | 依 `tools → system → messages` 嚴格前綴命中快取（5m / 1h TTL） |
| `Extended Thinking` | ch03 | 配置 `budget_tokens` 的內部推理區塊，多回合工具呼叫需原樣保留 `thinking` + `signature` |
| `Context Compaction` | ch03 | 將長對話或大工具回傳裁剪、摘要或卸載至外部 Scratchpad 以控管輸入膨脹 |
| `Agentic RAG` | ch04 | 由 Agent 自主決定檢索時機、查詢改寫與重試的 Hybrid Search（BM25 + Vector + Rerank） |
| `Pre-filtering ACL` | ch04 | 多租戶權限過濾下推至檢索查詢層，絕不在 LLM 輸出後才過濾 |
| `Orchestrator-Workers` / `Router-Specialists` | ch05 | 隔離工具面與上下文的多 Agent 協作拓撲 |
| `Event-sourced Checkpoint` | ch06 | Append-only 狀態轉移事件日誌，支援 Pod 重啟與 HITL 暫停後的斷點續跑 |
| `HITL`（Human-in-the-Loop） | ch06 | 高風險操作（如超額退款）暫停執行、等待人工審批後喚醒續跑的機制 |
| `Trajectory Eval` | ch07 | 針對工具選取、參數正確性與步數效率的過程軌跡評測 |
| `Pass@k` / `Pass^k` | ch07 | `k` 次嘗試至少成功 1 次 vs 連續 `k` 次全部成功（企業可靠性指標） |
| `Model Routing` | ch08 | 依工單複雜度動態分流至 Haiku 5.5 / Sonnet 5.5 / Opus 5.5 |
| `TTFT` / `TPOT` | ch08 | Time To First Token / Time Per Output Token |
| `Batch API` | ch08 | 非同步批次推理介面，Input/Output 一律 50% 折扣 |
| `Policy Engine` | ch09 | 位於工具執行層前的確定性授權與金額上限檢查閘門，不依賴 Prompt 自律 |
| `Indirect Prompt Injection` | ch09 | 藏於工單內文、網頁或工具回傳中的惡意指令注入攻擊 |
| `OpenTelemetry GenAI Span` | ch10 | 覆蓋 Request → Turn → LLM/Tool 的標準化分散式追蹤與成本歸因結構 |
| `Shadow Mode` / `Canary Rollout` | ch10 | 線上雙跑比對不寫入外部系統／按比例切流與預算熔斷的發布策略 |
| `PRR`（Production Readiness Review） | ch12 | 上線前涵蓋可靠性、Eval、安全、成本、觀測與回滾預案的強制審查 |
