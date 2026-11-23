## Verdict

**NEEDS_REVISION**

兩份範例的線上路徑都會因 Sonnet 5.5 不支援手動 `budget_tokens` 而收到 HTTP 400。章內算式在各自假設下成立，但第 1 回合的輸入量與全書 42,000-token 基準互相矛盾。快取命中、自我檢核與 Compaction 也有會讓讀者實作出錯的問題。

驗證以貼出的版本為準，並查閱工作區的共用計價函式。Python 離線實跑得到 `32,000 → 2,191` 字元及 `$0.060900`。TypeScript 執行環境缺少 `@anthropic-ai/sdk`，因此只完成靜態檢查，SDK 型別檢查及兩語言的線上呼叫均未驗證。

## Critical / Factual / Math Issues

1. **統一第 1 回合的輸入定義。** 全書 outline 的五回合帳本是 `6,000 + 7,200 + 8,400 + 9,600 + 10,800 = 42,000`，等於 `5 × 6,000 + 1,200 × (0+1+2+3+4)`。ch03 情境 A 明列第 1 回合另有 `1,200` tokens，依同一套累積規則就會得到 `5 × 6,000 + 1,200 × (1+2+3+4+5) = 48,000`。兩者皆有 `5 × 350 = 1,750` output tokens，但分別是 **`$0.1015／筆、$5,075／日、$152,250／月`** 和 **`$0.1135／筆、$5,675／日、$170,250／月`**。建議保留表內基準，明列 `1,200` 是第 2–5 回合的歷史增量，並將情境 A 標為首輪另有載荷的獨立情境。也要定義 `1,200` 是否已含重送的可見 assistant 輸出與工具結果，避免重複加計。 [全書 outline](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/book-src/_meta/outline.md:78)

2. **更正快取失效範圍與監控公式。** `tools → system → messages` 是服務端的前綴評估順序，與 JSON 欄位的序列化順序無關。在 `system` 開頭插入時間戳會使 `system` 斷點失配，但已寫入且仍有效的 `tools` 斷點可讀取 **3,600 tokens**，其餘 **2,400 tokens** 可重新寫入。請同步修正故障模式和自我檢核第 1 題。`usage.input_tokens` 只代表未讀取亦未寫入快取的輸入，故 token 命中占比應為 `read / (input + write + read)`，並在監控區間先加總各欄位。全前綴命中且另有 `1,200` 未快取 tokens 時，原公式會得到 `6,000 / 1,200 = 500%`，正確值為 `83.33%`。將 **70%** 標為示例告警門檻，並按前綴版本區分冷啟動、TTL 到期及持續失配。並發請求也可能一起 miss，因為第一個回應開始後才有可讀取的快取項目。 [Anthropic Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

3. **把裁剪的「後續重送節省」與「端到端節省」分開。** 裁剪發生在寫入 `tool_result` 前，第一次把結果送入模型時就已省下 tokens。情境 B 和挑戰題的答案只計後續重送，算術均正確。若首次送入也按同一未快取費率計費，總額如下。兩題也應明示原始大回傳是獨立情境，不能直接從全書的 `1,200`-token 回合增量基準扣除。若中途 Compaction 已移除該結果，後續少送幾次就少算幾次。

   | 情境 | 章內口徑 | 加計首次送入 |
   |---|---:|---:|
   | B，`8,000 − 600 = 7,400`，後續 3 次 | `22,200` tokens，`$0.044400／筆` | `29,600` tokens，`$0.059200／筆` |
   | 挑戰題，`5,000 − 500 = 4,500`，後續 4 次 | `18,000` tokens，`$0.036／筆`，`$54,000／月` | `22,500` tokens，`$0.045／筆`，`$67,500／月` |

4. **其餘數字重算。** 情境 A 的 `4,000 + 350 = 4,350` output tokens，`$0.015000 + $0.002400 + $0.043500 = $0.060900`，其中 thinking 為 `$0.040000`。數字可保留，但 `4,000` 要改為假設觀測到的計費量。其餘基準相符：`12 + 6 = 18` 個工具，`2,400 + 3,600 = 6,000` 前綴 tokens，`50,000 × 30 = 1,500,000` 筆／月，`50,000 / 86,400 ≈ 0.579 req/s`，`12 / 0.579 ≈ 20.74×`，可粗估為 `20×`。`$18,000 / 1,500,000 = $0.012／筆`，相對 `$152,250` 降幅為 `88.18%`。Sonnet／Opus／Haiku 牌價及表內快取倍率與官方價目相符，Sonnet Batch 半價為 `$1／$5 per MTok`，第一方 Claude API 的 US-only token 費率為 `1.1×`。`2.5s／18s` 是端到端 p95 目標，章內的 `15,000` tokens 無法單獨推導 TTFT、p95 或截斷結果。 [Anthropic 價目表](https://platform.claude.com/docs/en/about-claude/pricing)

5. **在應用層落實退款與租戶邊界。** 兩份程式直接插入工單文字，輸入可破壞 XML 結構。先做 XML escaping 或使用可靠序列化，並把工單、ERP 自由文字和摘要視為不可信資料。從已驗證的請求身分取得租戶，工具執行器按租戶查驗訂單權限。退款前依權威帳本重查餘額、幣別、資格與核准紀錄，並在寫入時以交易或版本條件防止並發超額退款。持久化以業務操作識別碼為基礎的冪等鍵，讓逾時後可查詢執行結果再決定是否重試。模型產生的 `refund_eligible: true` 只能作為待驗證線索。

## Code & API Issues

1. **修正 Thinking 設定、算例和第 2 題。** Sonnet 5.5 預設使用 adaptive thinking。兩份程式及 Python 節錄應使用 `thinking: { type: "adaptive" }`，以 `output_config.effort` 調整深度，以 `max_tokens` 限制單次總輸出。若低延遲路徑要停用工具呼叫前的思考，可用 `between_tools`，搭配 `high` 或更低的 effort。手動 `max_tokens > budget_tokens` 的規則只適用於支援手動模式的模型。計費用 API 的 `usage.output_tokens`，摘要或省略後的 thinking 文字長度無法用來還原費用。 [Sonnet 5.5 規格](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) · [Anthropic Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)

2. **讓範例真正跑完工具回合。** 兩個 `main` 只送一次請求並印出 `stop_reason`。歷史只有兩則，Compaction 必定直接返回。至少以 mock 示範 `tool_use → tool_result → 第二次 Messages 呼叫`，完整保留 assistant blocks，包含 `thinking`、`redacted_thinking` 與簽章。將所有對應的 `tool_result` 放在緊接的 user 訊息開頭，以 `tool_use_id` 配對。多工具並行時替各呼叫設期限，失敗結果以原 ID 回傳 `is_error`。`max_tokens` 表示達到輸出上限，`model_context_window_exceeded` 表示用盡上下文容量。遇到截斷或拒絕時，應有明確處置，尤其要禁止派送未完成的工具參數。 [Anthropic 停止原因](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) · [官方工具迴圈範例](https://platform.claude.com/cookbook/extended-thinking-extended-thinking-with-tool-use)

3. **依完整工具交換及 token 預算做 Compaction。** `keepRecentTurns * 2` 以訊息數代替回合邊界，可能留下孤立的 `tool_result` 或移除它所屬的 assistant turn。目前五則以內跳過，六則只把一則中間訊息替換成一則摘要。區塊型內容只保留 `[N content blocks]`，會丟失正文、證據和工具結果。應只壓縮已完成的交換，原樣保留仍在進行的交換，並用來源、時間與版本明確的應用程式狀態重建摘要。將「第 4 回合」定為示例觸發條件，實作以 token 預算和輸出預留量判斷。 [Anthropic Context Windows](https://platform.claude.com/docs/en/build-with-claude/context-windows)

4. **截斷器沒有落實 600-token 上限，且小上限會反向膨脹。** 現有樣本是 `10 × 3,200 = 32,000` 字元，保留 `1,680 + 480` 字元，加上 31 字元標記，得到 `2,191` 字元，省略 `29,840`。兩語言在 `maxChars = 1–4` 時尾長取整為零，`slice(-0)`／`[-0:]` 會把完整原文放回。TypeScript 以 UTF-16 計數，也可能切斷代理對。請驗證上限並把截斷標記計入，優先投影必要欄位、分頁並維持有效 JSON，再用代表性繁中與 ERP 資料量測 token。將 `2,400 ≈ 600` 和 `32,000 ≈ 8,000` 標為粗估。 [Anthropic Token Counting](https://platform.claude.com/docs/en/build-with-claude/token-counting)

5. **用實際 `usage` 驗證快取。** 範例只給一個短工具和一段短政策，未驗證任何斷點達到 Sonnet 5.5 的 **512-token** 最低門檻。離線成本使用硬編的 6,000-token 寫入 fixture，應清楚標為帳本演示。要驗證 API 快取，請用達標的前綴連續送兩次請求，檢查 `cache_creation_input_tokens` 和 `cache_read_input_tokens`。章內可簡述最多四個斷點、20 個 blocks 的回看範圍，以及 `ttl: "1h"` 的設定。若示範混用 TTL，共用計價函式須按 `usage.cache_creation` 的 TTL 明細計算。 [Sonnet 5.5 規格](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) · [Anthropic Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

6. **釐清本章的 API 涵蓋面。** `strict: true`、`output_config.format`、MCP Connector 和 Batch 在本章及兩份程式中均未使用。就本章可補一句交代：`strict: true` 控制工具呼叫的名稱與參數形狀，`output_config.format` 控制最終 JSON 輸出形狀。MCP Streamable HTTP 是傳輸協定，Claude Connector 則透過 Messages beta 的 `mcp_servers` 與 `mcp_toolset` 連接遠端工具。Batch 是非同步路徑，逐項以 `custom_id` 對帳，依各項結果決定重試。`custom_id` 是關聯識別碼，業務去重仍由應用程式處理。 [Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) · [MCP Transport 規格](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) · [Claude MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [Message Batches](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

## Clarity / Minor Suggestions

- 將 CPU cache 類比限於重用穩定內容。移除「同位址就絕對等價」，並把「四個區塊依序組成」改為三類請求內容加上生成輸出預算。KV cache 使用量、上下文容量和帳單是三種不同的量。
- 補上範例政策真正使用的 few-shot，或在文字中清楚標出建議做法。把「72 小時」寫成示例業務規則，說明以物流最後更新時間為準。兩份 fixture 只有工單建立日期及承諾送達日期，無法判定追蹤碼停更已逾 72 小時。
- 說明「第 3／4 回合」、「最近 2 回合」、`8,000／15,000` tokens 和練習的 `10／15／20` 分鐘各是示例設定、情境輸入或估時。將「必然漏看退款上限」改成可用評測驗證的風險。
- TypeScript 節錄的 `<ticket_context>...</ticket_context>` 是佔位內容，應明示有所省略。兩份程式都定義了建立時間但沒送入模型。移除未使用的 mock 初始化及 Python 的匯入時資料查找，並列出可以重現離線驗證與 TypeScript typecheck 的相依版本和命令。