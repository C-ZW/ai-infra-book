## Verdict

**NEEDS_REVISION**

兩份範例都印出了預期的 `waiting_hitl → 3 → 5 → completed`，但核准函式只追加事件，尚未執行退款或喚醒 Worker。章內的 Replay 規則也不足以處理多工具回合和金流結果不明的情況。容量算式在理想配額模型下成立，但與前文指定的 90% 限流設定不一致。

**驗證範圍**：以貼出的章文與範例為審查對象，並執行工作區中的 Python 範例和 TypeScript 範例。TypeScript 使用 Node 的型別轉換執行，未跑 `tsc --noEmit` 或書中的 `npx tsx` 指令。兩份範例都使用 mock，Claude API 行為依官方文件核對。

## Critical / Factual / Math Issues

1. **退款去重應綁定業務操作。** `refund:{run_id}:{order_id}` 會讓同一筆退款意圖在重建 run 後獲得新鍵，也會讓同 run、同訂單的兩筆合法部分退款共用一把鍵。使用持久化的 `(tenant_id, refund_operation_id)`，綁定訂單、金額與幣別，對同鍵異參數回報衝突。送出前記錄授權後的操作意圖。金流逾時後，依供應商的冪等有效期和查單能力決定查詢、同鍵重送或人工對帳。本地 `UNIQUE` 只能約束本地寫入，無法封住外部已入帳、回執未落盤的窗口。自我檢核第 2 題也應補上這些成立條件。

2. **Replay 需要逐一核對工具呼叫。** 只看最後事件會漏掉同一 `llm_turn` 中尚未完成的其他工具。保存原始請求或其可重建版本、完整 assistant content、各 `tool_use_id` 與工具操作狀態，依序辨識已完成、尚未派送和結果不明的操作。所有待回覆的工具都有結果後，下一則 user message 應先放對應的 `tool_result` 區塊，再繼續模型回合。退款額度、權限和 HITL 狀態也要在派送時重新核對。 [Claude 工具呼叫與停止原因](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)

3. **Redis 租約與 HITL 喚醒都有競態。** `SET NX EX 30` 到期時，原 Worker 仍可能在執行。續約應涵蓋整段持有期間，並核對持有者 token 後才續約或刪鎖。持久狀態寫入應檢查版本或 fencing token，外部金流仍須有冪等保護。HITL 應將 `deadline_at` 存在 PostgreSQL，讓核准、駁回與升級以條件式狀態轉移競爭，並在同一交易寫入事件與喚醒 Outbox。Redis 到期通知可加快喚醒，持久化掃描負責補漏。`seq` 也需要原子配置或以預期版本寫入，避免併發者各自推算下一號。

4. **月分區與主鍵設計不相容。** PostgreSQL 原生分區表若以 `created_at` 分區，父表的唯一鍵或主鍵必須包含分區鍵。直接加上 `created_at` 會失去全表 `(run_id, seq)` 唯一性。若保留月分區，應另設每個 run 的版本／唯一性機制。歸檔也不能只按月卸載，因為仍在等待審批或執行的 run 可能橫跨數個分區。 [PostgreSQL 分區限制](https://www.postgresql.org/docs/current/ddl-partitioning.html)

5. **把授權放在工具執行端。** 模型輸出、工具與 MCP 回傳、訂單備註都可能帶有 prompt injection。退款端應依可信身分驗證租戶、訂單、角色、付款狀態、可退餘額與核准範圍。核准要綁定不可變的操作內容，且扣減可退餘額須防止併發超退。Checkpoint 保存完整訊息前，也要定義敏感欄位遮罩、讀取權限與保留期限。

### 數字與公式複核

| 項目 | 重算與審查結果 |
|---|---|
| 日／月工單與峰均比 | `50,000 × 30 = 1,500,000`。`50,000 ÷ 86,400 = 0.578704 工單/s`。`12 ÷ 0.578704 = 20.736×`，可寫約 `20.7×` 或約 `21×`，`20×` 是粗估。 |
| API 呼叫負載 | `12 × 5 = 60 calls/s`，相當於 `3,600 RPM`。平均為 `2.89352 calls/s`。尖峰換算假設五回合的呼叫量已充分重疊，且未計重試。 |
| Worked Example，按名目配額 | `2,400 ÷ 60 = 40 calls/s`。`(60 − 40) × 30 = 600` 個 **API 呼叫**。排空餘裕 `40 − 2.89352 = 37.10648 calls/s`，`600 ÷ 37.10648 = 16.17s`。原算式正確。 |
| Worked Example，按章內 90% 設定 | `40 × 0.9 = 36 calls/s`。30 秒累積 `(60 − 36) × 30 = 720` 個呼叫。若尖峰開始時桶滿且上游容許立即額外放行 `54` 次，估計剩 `666` 個，排空約 `20.12s`。無初始額度時約 `21.75s`。`600` 不能直接當工單佇列容量，也不足以推導 Gateway 連線池會耗盡。 |
| 自我檢核第 3 題 | `20 × 5 = 100 calls/s = 6,000 RPM`。名目 `3,600 RPM = 60 calls/s`，`(100 − 60) × 45 = 1,800` 正確。沿用 90% 則是 `54 calls/s`，未扣初始桶額度時積壓 `2,070`。在名目模型中，`1,500` 告警線於約 `37.5s` 抵達。 |
| Token 配額 | 採表列 `42,000 / 1,750`，持續 `12 工單/s` 相當於 `30.24M input tokens/min` 和 `1.26M output tokens/min` 的工作量，假設無快取、無重試且 `1,750` 涵蓋計費輸出。需與實際模型池的 RPM、ITPM、OTPM 一起核對，並說明多 Pod 如何共用配額。 [Claude 配額](https://platform.claude.com/docs/en/api/rate-limits) |
| 基準成本與 Batch | 按表列 token 數，`(42,000 × $2 + 1,750 × $10) ÷ 10⁶ = $0.1015`／筆，乘以日／月工單量得到 `$5,075`／日、`$152,250`／月。Batch 基礎 token 費率為 `$1 / $5`／MTok，同樣 token 量為 `$0.05075`／筆。`$18,000 ÷ 1,500,000 = $0.012`／筆，較基準省 `88.18%`。 [Claude 定價](https://platform.claude.com/docs/en/about-claude/pricing) |
| 基準表的 token 口徑 | `2,400 + 3,600 = 6,000`，`12 + 6 = 18`，`5 × 350 = 1,750`。`42,000` 可由 `5 × (6,000 + 1,200)` 得到，前提是每次請求固定只帶 `1,200` 額外輸入。若每回合新增的 `1,200` 會累積重送，則是 `5 × 6,000 + 1,200 × (1+2+3+4+5) = 48,000`，尚未計入另行重送的 assistant／工具內容。該口徑下，即使輸出仍是 `1,750`，成本也已是 `$0.1135`／筆。基準表須明示歷史如何計入。 |

## Code & API Issues

- **兩份範例把核准當成退款完成。** `approveHitl`／`approve_hitl` 可對不存在的 run 或重複審批追加 `hitl_resume` 與 `completed`，原本的退款結果仍是 `pending_hitl`。兩份 runner 也都只檢查 pause/resume，因此只有 `llm_turn` 時會重跑模型，自動核准後重送也會重跑。實測 TypeScript 自動核准的事件數從 `3` 增到 `6`，不存在的 run 也能被標成 `completed`。此外，工具回傳 `rejected` 仍進入一般 `completed` 分支，應明確定義 workflow 終態與退款結果。範例應真正走一次「持久化核准 → runner 續跑 → 拿到退款回執」，並用回執驗證完成。 [TypeScript runner](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/ts/ch06/index.ts:131) · [Python runner](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/py/ch06/main.py:100)

- **Mock 的金額驗證與租戶邊界有漏洞。** 兩份共享 mock 都在訂單租戶驗證前查冪等快取，同鍵可回傳既有交易資料，且沒有綁定原始參數。runner 還允許以浮點數傳入退款金額，應以最小貨幣單位或精確十進位處理，並拒絕非正數、NaN 和無效幣別。章內 Python 節錄也省略了區域 `call_llm` 定義，直接貼用會缺少該名稱。TS 節錄的退避計算與完整檔等價。

- **重試預算與熔斷器行為不一致。** 章文「重試 4 次」是最多 5 次嘗試，jitter 上界依次為 `0.5、1、2、4s`，合計 `7.5s`，`30s` 只封頂指數項。範例 `maxAttempts=4` 是 1 次初始呼叫加 3 次重試，jitter 上界為 `50、100、200ms`，合計 `350ms`，注入的 `0.02s` 是 `20ms`。第一次 mock 呼叫失敗、第二次成功，因此預設路徑根本不會熔斷。兩版 breaker 都包住整批重試且計入所有例外，沒有 `60s` 視窗或 HALF_OPEN 單探測保證。TS 還可能讓舊的在途成功關閉新開的 breaker。應統一計數單位、用單調時鐘與探測權限控制，並用剩餘 deadline 同時限制睡眠和單次呼叫。兩次 `60s` 已耗盡同步 `120s` 預算，完全用滿 5 次呼叫則可達 `307.5s`，且 `Retry-After` 可再拉長。若應用程式掌管重試，設 TS `maxRetries: 0`、Python `max_retries=0`，避免 SDK 預設兩次重試與外層相乘。 [Claude API 錯誤與重試](https://platform.claude.com/docs/en/api/errors) · [TypeScript SDK](https://github.com/anthropics/anthropic-sdk-typescript/blob/main/src/client.ts)

- **`429` 與 SSE 要按實際語意分類。** `429` 也可能是流量爬升限制或支出上限，支出上限型 `429` 可沒有 `Retry-After`。共用 `Retry-After` 下限也可能讓多個 Worker 同時醒來，應再經限流器放行。SSE 用 `message_stop` 確認正常結束，用 `message_delta` 的 `stop_reason` 決定下一步。完整回應仍可能是 `max_tokens`、`refusal`、`pause_turn`、`stop_sequence` 或 `model_context_window_exceeded`。HTTP 200 之後也可能出現 SSE `error`。只有已完成且符合派送條件的本地工具呼叫才能執行。將 transport idle 與模型進度 timeout 分開，避免把只有 `ping` 或暫無 `content_block_delta` 的活連線判成斷線。Streaming 若已把內容送給使用者，重試還需定義替換或去重行為。 [錯誤](https://platform.claude.com/docs/en/api/errors) · [SSE](https://platform.claude.com/docs/en/build-with-claude/streaming) · [停止原因](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)

- **Batch 的 `custom_id` 會被 API 拒絕。** `{run_id}:{seq}` 含不合法的 `:`，加上序號也可能突破 64 字元。使用符合 `^[a-zA-Z0-9_-]{1,64}$` 的短 ID，持久化它與 batch、run、turn 的對照。處理 `canceling`／`canceled`、亂序結果與 24 小時到期。`errored` 應先分類，永久驗證錯誤修正後才重送。下載與提交重試要用持久化狀態去重，尤其是 POST 成功但本地未收到 batch ID 的窗口。`succeeded` 仍需檢查訊息的 `stop_reason`。Batch 以每個子請求的 Messages 呼叫為單位，多步本地工具迴圈仍須逐輪協調。 [Batch 建立規格](https://platform.claude.com/docs/en/api/http/messages/batches/create) · [Batch 處理指南](https://platform.claude.com/docs/en/build-with-claude/batch-processing) · [Batch refusal](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)

- **快取前綴穩定只能提高命中機會。** 明確標示 `tools → system → messages` 中截至 `cache_control` 斷點的有效前綴，避免把 JSON 序列化的位元一致當作命中判準。即使前綴一致，仍受 TTL、模型最低可快取長度、處理時序等條件影響。計費與排錯應同時記錄 `input_tokens`、`cache_creation_input_tokens`、`cache_read_input_tokens`、`output_tokens`。表列 `1.25× / 2×` 寫入倍率與 `0.05× / 0.10×` 讀取倍率符合所列模型。 [Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Claude 定價](https://platform.claude.com/docs/en/about-claude/pricing)

- **補出 Structured Outputs、thinking 和 MCP 的適用邊界。** 本章未送出 `strict: true`、`output_config.format` 或 `thinking`，也沒有 MCP Client／Connector 程式碼可驗證。若要連回相關章節，應說明 `strict: true` 約束工具名稱與輸入 schema，`output_config.format` 約束模型 JSON 輸出，業務授權仍由工具端負責。Sonnet 5.5 預設 adaptive，`between_tools` 可停用前置 thinking，`disabled` 和舊式 `enabled` 會被拒絕。Replay 應保留同一工具回合要求回傳的 thinking 區塊與簽章。自行透過 MCP Streamable HTTP 派送與 Anthropic MCP Connector 代呼叫的失敗窗口不同，Connector 可能在 Messages 串流中斷前已執行遠端工具，盲目重送整個 turn 可能重複副作用。 [Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) · [Sonnet 5.5 遷移指南](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) · [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [MCP 傳輸規格](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)

## Clarity / Minor Suggestions

- 將量測基準和示範設定標清楚。`5s × 3 = 15s` 是單個唯讀工具含兩次重試的 timeout 預算，尚未計退避。寫入 `10s`、同步總上限 `120s`、背景預算 `3,600s = 1h` 與 HITL 的一小時截止時間各有用途。說明它們如何配合分流 `p95 ≤ 2.5s` 和多步處置 `p95 ≤ 18s`，以及何時轉非同步。`$300 > $250` 且低於 mock 訂單的 `$340`，此測試資料正確。
- 為其餘設定標明作用域和依據。`60s` 失敗窗、`5` 次閾值、`30s` 冷卻、`20` 併發、`prefetch = 1`、`429 > 5%` 持續 `2m`、`12s` 的標頭範例與 `30` 天歸檔均屬章內設定。逐一說明按 pod、租戶、模型池或整個服務計算，並區分 BullMQ、Celery、Temporal 各自的併發與預取語意。
- 統一「退款、扣款、入帳」用語。相同訂單與金額可能對應多筆合法退款，重複退款告警應依業務操作 ID 與供應商交易 ID 對帳。修正範例指令的起始目錄，兩條 `cd` 若在同一個 shell 連續執行，第二條相對路徑會從 TypeScript 目錄解析。