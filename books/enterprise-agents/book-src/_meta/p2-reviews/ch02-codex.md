## Verdict

**NEEDS_REVISION**

成本算式在明確的假設下成立，但章節把 Schema 保證延伸成退款安全與延遲保證。兩份範例也都缺少文章承諾的工具迴圈與結構化輸出。Python 本地驗證通過 `dry_run → commit → replay` 和負數拒絕測試，同時重現了跨租戶錯誤重播、`NaN` 入帳及同毫秒退款 ID 碰撞。本地測試使用現有的 Python SDK 0.75.0。TypeScript 採靜態審閱，未執行型別檢查或即時 Claude API 驗證。

## Critical / Factual / Math Issues

1. **唯一索引只能保護資料庫中的寫入，退款仍需端到端冪等。** 如果支付商已完成退款，程序卻在寫回帳本前崩潰，Redis 鎖到期後仍可能再送一次退款。先以 `(tenant_id, operation_key)` 原子建立持久操作紀錄，比對正規化的業務酬載雜湊，再將同一操作鍵傳給支付商。明確定義 `pending`、成功、失敗與結果未知的轉移及對帳流程。Redis 鎖和 24 小時結果快取可減少爭用。若使用租約，釋放時須驗證持有者。兩個不同操作鍵也可能同時超過同一筆支付的可退餘額，需在交易內鎖定或原子預留餘額。

2. **`dry_run` 與租戶授權必須由伺服器執行。** 模型可直接送出 `dry_run: false`，也可在預檢後改金額、訂單或租戶。若預檢是必要條件，提交須驗證綁定租戶、操作者、操作與金額的短效批准紀錄，並重新檢查退款政策和餘額。從已驗證的身分取得租戶，依工具及資源逐次授權，由後端產生操作鍵。把工單、知識庫、MCP 工具描述與結果視為不可信資料，限制工具可見範圍與結果欄位，並讓人工審批由可信工作流執行。最終 `refund_id` 和成功狀態應來自帳本。模型也不應自行調降退款金額來繞過審批門檻。

3. **成本算術正確，但回合定義與節省結論須修正。**

   | 核對項目 | 獨立重算 |
   |---|---|
   | 工具與前綴 | `12 + 6 = 18`。`2,400 + 3,600 = 6,000` tokens |
   | 流量與 SLO | `50,000 × 30 = 1,500,000` 筆/月。`50,000 ÷ 86,400 = 0.5787` 筆/秒。若 `12 req/s` 指工單進件，尖峰為平均 `20.736×`。案例使用多步處置 `18s`，分流的 `2.5s` 屬另一條路徑 |
   | 五回合基準 | `6,000 + 7,200 + 8,400 + 9,600 + 10,800 = 42,000` 輸入。`350 × 5 = 1,750` 輸出。`$0.084 + $0.0175 = $0.1015`/筆，即 `$5,075`/天、`$152,250`/月 |
   | 第六回合與節省 | `10,800 + 1,200 = 12,000`。`$0.024 + $0.0035 = $0.0275`/次。`× 12% = $0.0033`/筆，即 `$165`/天、`$4,950`/月。含這項重試的無快取基準為 `$0.1048`/筆、`$5,240`/天、`$157,200`/月 |
   | 其他基準表費率 | Sonnet 5.5 五分鐘／一小時快取寫入為 `$2.50 / $4.00`，讀取為 `$0.10`，Batch 基礎輸入／輸出為 `$1 / $5`，皆以 MTok 計。Opus 5.5 讀取為 `$0.20`，Haiku 5.5 讀取依級距為 `$0.01 / $0.05`。若適用 `1.1×` 美國推論費率，無快取基準為 `$0.11165`/筆、`$167,475`/月。`$18,000`/月等於 `$0.012`/筆，較 `$152,250` 低 `88.18%` |
   | 其他量值 | `30,000 / 5,000 / 10,000 / 18,000 / 60,000 ms` 分別為 `30 / 5 / 10 / 18 / 60s`。`86,400s = 24h`。若首個退避以 `i=0` 計，四次 Full Jitter 上限為 `0.5 / 1 / 2 / 4s`，合計上限 `7.5s`、期望 `3.75s`，尚須加上請求時間。其餘回合上限、連線數、租約及告警閾值屬配置假設 |

   `42,000` 的前提是首輪總輸入已定為 `6,000`，且其後每輪累加 `1,200`，包含實際保留的對話、工具呼叫及結果。若首輪也有 `1,200` 新輸入，五回合會是 `48,000` tokens、`$0.1135`/筆。請交代首輪工單內容與 API 額外開銷如何計入。`350` 也應定義為計費輸出，含 thinking。`12%` 是每筆恰好多一次、且錯因完全可由 strict 消除的假設。將 `$4,950` 標為情境估算，移除「守住 p95」的結論，並用實測的錯誤分類、重試位置及延遲分布驗證。Batch 折扣適用非同步、獨立的 Messages 請求，無法在同一批次內接續等待本機工具結果的回合。快取可疊加，命中屬 best effort。 [Sonnet 5.5 規格](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) · [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) · [Data residency](https://platform.claude.com/docs/en/manage-claude/data-residency)

4. **快取斷點與告警公式互相矛盾。** 前綴順序為 `tools → system → messages`。最後一個工具上的斷點只能涵蓋工具前綴。要涵蓋固定的 system prompt，將斷點放在最後一個固定 `system` 內容區塊，並維持完整前綴一致。範例 `usage` 的總輸入為 `1,200 + 0 + 6,000 = 7,200`，該輪已讀取快取的 token 占 `83.33%`。依章內五回合分布，即使每輪都命中 `6,000`，全輸入讀取占比也只有 `30,000 ÷ 42,000 = 71.43%`，會持續觸發 `80%` 告警。應以符合快取條件的請求或指定前綴為分母，並另外追蹤總輸入快取讀取占比及冷啟動。 [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

5. **18 秒需由整條呼叫鏈共同執行。** 每次模型或工具呼叫都應以剩餘 deadline 限制 timeout，剩餘預算不足時停止重試或轉人工。`Retry-After` 也受 deadline 約束，SDK 的內建重試須納入同一預算。串流可在完整訊息確認後才派發寫入。若已派發且結果未知，應查詢持久操作狀態，避免整回合重播造成再次動帳。釐清 `12 req/s` 的計量點。若它是工單進件率，五回合對應穩態下約 `60` 次模型請求/秒，再加重試。工具併發、RPM、token 限額與排隊應分別估算，`64` 條 socket 容量也需配合實際用戶端與負載驗證。

## Code & API Issues

1. **兩份「完整範例」都缺少核心路徑。** `messages.create()` 只送一次，未設定 `output_config`、未執行模型要求的工具、未回填結果，也未解析最終輸出。兩邊皆只註冊兩個工具，還把無法執行的 `get_order` 公告給 Claude 與 MCP 客戶端。補上唯讀 handler、允許清單派發、回合上限與結構化輸出驗證。TypeScript 可用 `messages.parse()` 搭配 `output_config.format: zodOutputFormat(...)`，Python 可用 `messages.parse(output_format=TicketResolution)`。原始 wire 格式為 `{"type":"json_schema","schema":...}`。統一文章的 `resolution_type`、`decision`、`confidence_score` 與實際欄位，讓 Python 的 `refund_id` 與 TS 一樣必填且可為 `null`，並統一退款結果的大小寫命名。 [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

2. **說明完整的 Claude 回合契約。** `strict: true` 約束成功完成的工具輸入，且只涵蓋支援的 JSON Schema 子集。文件指出遞迴 Schema 不受支援，也未承諾首次編譯 `<50 ms`。金額上下限仍須在應用層檢查。最終輸出須先檢查停止原因和內容，再解析。補上 `stop_sequence`、`model_context_window_exceeded` 與伺服器工具的 `pause_turn`，並明定未知原因的處置。遇到 `tool_use`，保留完整 assistant 內容，在緊接的單一 user 訊息開頭回傳每個本機呼叫恰好一筆 `tool_result`。Sonnet 5.5 預設啟用 adaptive thinking，需原樣保留帶簽章的 thinking blocks，按 block `type` 取文字。若要降低前置推理，使用 `thinking: {"type":"between_tools"}`。`disabled` 在此模型會回傳 400。 [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) · [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) · [Sonnet 5.5 migration guide](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide)

3. **退款範例要在執行入口驗證參數。** TS 的型別斷言和 Python 的型別註記都不會驗證直連 MCP 的 JSON。兩者需驗證必填欄位、型別、枚舉、有限金額與小數精度，金額使用整數分或 Decimal。兩者目前只按來客可控制的鍵重播，且在 `dry_run` 判斷前查找既有提交。Python 多執行緒下的查找與寫入也缺少原子性。以可信租戶與操作鍵比對酬載，明確區分預檢、待審批、已提交與重播。超限分支目前回傳形似退款 ID 的占位值，應回傳明確的 `would_approve: false` 及待審狀態。改用唯一操作 ID。若保留記憶體實作，將保證明確限定為單程序示範。 [TypeScript executor](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/ts/ch02/index.ts:115) · [Python executor](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/py/ch02/main.py:109)

4. **兩個 HTTP handler 目前只展示部分 JSON-RPC 路由。** 無 session ID 仍須遵循 MCP 初始化生命週期。版本應協商，接受 `notifications/initialized` 時回空本文 `202`，不提供獨立 SSE 串流時對 MCP GET 回 `405`。補上 `Origin` 驗證、HTTP 與 JSON-RPC 參數驗證、大小及讀取期限限制。Python 的解析和 `**args` 例外會中斷請求，TS 則把執行例外誤報成 `-32700 Parse error`。建議使用官方 MCP SDK，並把驗證指令改成 `--serve`、`initialize → notifications/initialized → tools/list → tools/call` 的完整流程，POST 帶 `Accept: application/json, text/event-stream`。TS 本機示範應明確綁定 loopback。 [MCP 2025-03-26 transport](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) · [MCP lifecycle](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle)

5. **Connector 和應用層 MCP 代理需要各自的設定與權限邊界。** Connector 請求需指定支援的 beta 版本、`mcp_servers` 和對應的 `mcp_toolset`，並讓端點可從 Claude API 服務端連線。用工具組設定收斂允許清單，以受限授權憑證將使用者或租戶身分傳給服務端。Connector 使用 `mcp_tool_use`／`mcp_tool_result`，由供應商執行。應用層代理則負責初始化、HTTP 生命週期、逾時與工具派發。「只需 POST `tools/call`」及「毫秒級」均應改寫。 [Claude MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [MCP lifecycle](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle)

## Clarity / Minor Suggestions

- 動手做補上依賴安裝與 `--serve` 指令、唯讀呼叫，以及同鍵異參數、越權租戶和提交結果未知的驗收案例。TS 入口檢查可用 `pathToFileURL` 處理含空白的路徑。Python 的成本輸出目前只傳入未快取輸入與輸出，日後加入快取時須傳入各 usage 欄位。從範例交付物移除 `.pyc`。
- 為 `2% / 5 min`、`5% / 5 min`、工具 `p95 > 4s` 與連續三次失敗定義分母、最小樣本和處置範圍。單張工單只有少量工具呼叫，適合用明確失敗計數決定轉人工。服務告警可按工具、租戶和錯誤類別聚合。日誌保留稽核所需的識別與狀態，避免記錄原始憑證及敏感酬載。
- 將「靜態微服務客戶端無法修復」改成可操作的錯誤分類，交代哪些錯誤可以修正參數、哪些要查操作狀態、哪些應直接轉人工。把含 `//` 註解的 `json` 程式碼區塊改為合法 JSON 或標記 `jsonc`，並註明 wire 回應省略的欄位。