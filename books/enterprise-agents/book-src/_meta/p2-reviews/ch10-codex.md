## Verdict

**NEEDS_REVISION**

Python 與 TypeScript 範例均重現章稿的兩筆成本、快取比例與 5 個 Span。TypeScript 使用本機 `tsx` loader 執行，獨立的 `tsc` 型別檢查未完成。兩個範例使用模擬的 Usage，未發送 Claude API 請求。發布前應先修正三件事：已發生費用會被熔斷器漏記、事故模型混用了快取失效與整套降本策略失效、遙測欄位與採樣方式會讓儀表板產生偏差。

## Critical / Factual / Math Issues

1. **基準成本成立，但要把首輪假設寫清楚。** 依 ch01 的 `6,000 → 7,200 → 8,400 → 9,600 → 10,800`，累計輸入為 `42,000`，輸出為 `5 × 350 = 1,750`，Sonnet 成本為 `$0.084 + $0.0175 = $0.1015`／筆、`$5,075`／日、`$152,250`／30 天。這個序列從首輪 `6,000` 起算，只有四次 `1,200` 的增量。若首輪也要在 `6,000` 靜態前綴上加 `1,200`，則是 `48,000` 輸入、`$0.1135`／筆。月目標 `1,500,000 × $0.012 = $18,000`，降幅 `88.18%`。`50,000 ÷ 86,400 = 0.5787 req/s`，尖峰為 `20.736×`，章稿的 `20×` 可標為近似值。`12 + 6 = 18`、`2,400 + 3,600 = 6,000`，兩條延遲 SLO 也與基準表一致。三種模型牌價、快取倍率、Batch 半價和美國推論 `1.1×` 與官方文件相符。[ch01 基準](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/book-src/ch01-agent-architecture.md:107) · [Claude 價格](https://platform.claude.com/docs/en/about-claude/pricing)

2. **快取失效的成本因果要重寫。** `85%` 是範例的 `6,800 ÷ 8,000`，需要至少 `6,800` tokens 的可重用前綴。若每輪只命中 `6,000` 的靜態前綴，`8,000` 輸入時是 `75%`，五輪全命中時是 `30,000 ÷ 42,000 = 71.43%`。以同一個全 Sonnet 五輪工作負載計算，單是輸出就要 `$0.0175`，已超過 `$0.012`。保留快取斷點的前綴污染還可能反覆產生寫入費。若 `6,000` tokens 每輪都以 5 分鐘 TTL 重寫，成本會是 `$0.1165`／筆。建議把 `$0.1015` 標為「全 Sonnet、停用快取的情境」，另外用固定模型路由、回合數與輸入輸出量做 cache-only 對照。`85%` 應列為特定工作負載目標。讀寫皆零也可能是停用或移除快取、不可快取的內容，或截斷造成 Usage 缺失，需分開診斷。[Claude Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

3. **四小時事故有中途取整與倍率標示錯誤。** 建議保留未取整的平均流量，並採下表同一口徑。若保留原稿的 `8,332` 筆，淨增額應從未四捨五入金額算出 `$745.714 → $745.71`。`8.46×` 指事故總成本，淨增額是正常成本的 `7.46×`。原稿的 `2,083 × $0.1015 ≈ $211.42` 與 `174 × $0.0895 ≈ $15.57` 各自算得正確，但使用了預先取整的流量。

   | 均勻到達假設 | 重算結果 |
   |---|---:|
   | 四小時工單期望值 `50,000 × 4 ÷ 24` | `8,333.33` 筆 |
   | 正常成本／事故成本／淨增額 | `$100.00`／`$845.83`／`$745.83` |
   | 正常每小時／事故每小時 | `$25.00`／`$211.46` |
   | 五分鐘工單期望值／淨增額 | `173.61` 筆／`$15.54` |
   | 五分鐘即完成回滾時的理論節省 | `$730.30` |

   五分鐘是觀測窗。實際損失還要計入告警評估週期、回滾生效時間與在途工單。`5×` 重試成本、`0.5%` 罕見故障率及 `<2 ms` Redis 延遲應標為情境假設或提供量測依據。`max_turns` 從 5 增至 8 或 10，本身只將呼叫次數增至 `1.6×` 或 `2×`。

4. **燃燒上限與併發有量綱錯誤。** `$0.15 ÷ $0.012 = 12.5×`、`12 × 600 = 7,200` 筆、`7,200 × $0.012 = $86.40` 都正確。假設視窗初始耗用為零，尖峰以 `$0.144/s` 燃燒，約 `174s` 觸及 `$25`、`313s` 觸及 `$45`。若同一小時剩餘 50 分鐘回到日均速率，整小時約 `$107.23`。因此 `$120–$150` 可作為「一次 10 分鐘尖峰」的示例，需註明既有耗用與緩衝假設。若尖峰持續整小時，則是 `$518.40/hr`。同樣地，`12 req/s × 5 = 60` 的單位是 **LLM 呼叫／秒**，不能直接當作連線槽位。用到達率乘以各階段平均在途時間估算併發，再納入工具扇出、重試與 RPM／ITPM／OTPM 限制。`30s` LLM、`5s` 工具、`90s` 工單是硬逾時設定，還需獨立定義 `2.5s / 18s` SLO 的路徑期限、剩餘預算與取消傳遞。

5. **成本入帳與副作用必須分別做冪等。** `yyyyMMddHH` 是整點固定窗，範例則從程序建立起算一小時。兩者都和正文的滾動一小時不同。Redis 的去重、全域／租戶扣款與閘門決策須有一致的原子邊界，並定義 Redis Cluster、故障切換及旗標到期後的行為。PostgreSQL 現有主鍵會拒絕重複 `INSERT`，但 `(trace_id, turn_index)` 仍可能吞掉同回合的平行呼叫或真正再次計費的重試。應為每次實際上游呼叫記錄獨立的持久事件 ID，重送沿用該 ID，並保留工單、回合與上游 request ID 供對帳。先確保持久事件可重播，再談 Redis 重啟後的重建。退款等副作用另用穩定的業務操作鍵。遇到逾時或回應遺失時，應先查核外部提交結果，再從 checkpoint 恢復。`NUMERIC(10,6)` 也可能把低價模型的細粒度費用捨去，應按費率選擇足夠精度並延後四捨五入。

6. **六項維運指標需要完整事件來源。** 依錯誤、成本、快取與延遲做尾部採樣後，再用留存 Trace 算比率或 p95，會產生選樣偏差。應在採樣前產出全量計數器及延遲直方圖，以 `Σ cache_read / Σ total_input` 計算 token 加權比例，並補上工具嘗試、逾時、後驗結案和 HITL 狀態事件。定義每項指標的分母、去重單位與時間窗，尤其是工單總成本的月平均和單筆告警要分開。尾採樣還需定義同一 Trace 的 Collector 路由、容量、晚到 Span，以及長工單或跨 HITL 等待的關聯方式。固定等 `60s` 可能在 `90s` 工單結束前做出決策。工單成本門檻應明確引用根節點的 `agent.total_cost_usd`。[OpenTelemetry Tail Sampling Processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor)

7. **Shadow 必須在工具閘道封鎖副作用，發布須區分漂移與版本比較。** 工單內容、工具回傳與 MCP 回傳都要視為不受信任的資料。每次工具執行應由閘道驗證租戶、物件所有權、業務參數與審批，影子環境採唯讀憑證及可控的 stub／replay，並遮罩 Trace 內的 PII、金流欄位和憑證。Shadow 可量測擬議動作與模型費用，真實結案率及含寫入結果的總成本應由隔離重播或 Canary 驗證。均勻到達時，`1,000` 筆約需 `28.8` 分鐘，`5% × 50,000 = 2,500` 筆／日，兩者都需要按退款等高風險類別檢查樣本量。若工具錯誤門檻是 `+0.5` 個百分點，從 `1.5%` 起算即 `2.0%`。自動回滾應同時檢查兩條 SLO、樣本量及安全違規，並交代在途寫入的處置。章名承諾了漂移監控，正文還缺少按模型、Prompt、工具 Schema 版本與工單類別分層的線上基準，以及後驗標籤晚到時的評估方式。

## Code & API Issues

1. **兩份 `checkAndRecord` 都漏掉已發生的費用。** `runObservedTurn` 接到 Usage 並算出成本後，超過單筆上限、超過每小時上限或熔斷已開啟的分支都會提前回傳，跳過 hourly 累加。應拆為送出前的檢查／額度預留，以及送出後依 Usage 結算。章稿的兩個邊界值算得正確：`$0.14 + $0.01950 = $0.15950`，`$0.00658 + $0.01950 = $0.02608`。但範例主程式丟棄阻擋原因、根 Span 一律 `OK`，第二項也缺少第三次送出前檢查來證明 `CIRCUIT_OPEN_HOURLY_CAP`。讓範例直接驗證兩條路徑的入帳、根節點結果和後續拒絕。同時區分已達上限 `>=` 與下一筆會超額 `>`。[TypeScript 範例](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/ts/ch10/index.ts:69) · [Python 範例](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/py/ch10/main.py:69)

2. **同步修正章稿、程式片段與兩語言的 OTel 契約。** 固定一個 GenAI 語意慣例版本。採 `gen_ai.provider.name = "anthropic"`、`gen_ai.operation.name`、`CLIENT` span kind、`gen_ai.usage.cache_creation.input_tokens`／`gen_ai.usage.cache_read.input_tokens`，並將 `gen_ai.response.finish_reasons` 寫成字串陣列。依規格，`gen_ai.usage.input_tokens` 應包含快取讀寫，所以範例是 `8,000`，原始 Anthropic 非快取欄位才是 `1,200`。TS 與 Python 的屬性型別也要能承載陣列。把自訂 Span 分類、序號 ID、記憶體存放和模擬時間清楚標為教學實作。示例中收到 `tool_use` 後直接跑下一輪，若要宣稱示範完整 Trace 樹，須加入模擬工具執行 Span 和對應回合事件。Python 的租戶／類別屬性也應與 TS 對齊。[OpenTelemetry Client Inference](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/client-inference.md) · [GenAI 屬性登錄](https://opentelemetry.io/docs/specs/semconv/registry/attributes/gen-ai/)

3. **補齊 Messages 狀態、SSE 與 SDK 重試邊界。** TS 的 `UsagePayload.stop_reason` 漏掉正文已列的 `refusal`，也未處理如 `stop_sequence`、`pause_turn`、`model_context_window_exceeded` 及串流起始的 `null`。Python 接受任意字串，但沒有對應的狀態分支。應保留未知值供診斷，並禁止執行截斷或尚未驗證的工具參數。串流從 `message_start` 保存可得的輸入 Usage，合併 `message_delta` 的累積值，收到 `message_stop` 才確認完整結束。中斷時保存已知 Usage，另標記未知費用。字元數估算無法當財務下限，尤其遇到隱藏 thinking 或只收到部分輸出。`429` 傳回 `retry-after` 時應遵循，`529` 則在 header 存在時採用，否則走有上限的退避與 jitter。協調 SDK 和應用層的重試，並將傳輸嘗試納入共同 deadline 與重試預算。API 回應 header 要從 SDK 的回應介面取得，限流則同時看請求、輸入及輸出 token 維度。[Claude Stop Reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) · [Claude Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming) · [Claude Rate Limits](https://platform.claude.com/docs/en/api/rate-limits)

4. **成本 helper 適合固定情境，仍缺生產計價維度。** 本例兩輪分別為 `1,200 × $2/MTok + 6,800 × $0.10/MTok + 350 × $10/MTok = $0.00658`，以及 `8,000 × $2/MTok + 350 × $10/MTok = $0.01950`。根節點 `$0.02608` 與 `1 + 2 + 2 = 5` 個 Span 都正確。兩個 helper 都會把未知模型默默按 Sonnet 計價，也缺混合 TTL 的寫入拆分、Haiku `>100K` 級距、Batch、`inference_geo` 和可另外計費的伺服器端工具。若要升級成帳本範例，應保留原始 Usage、端點、模型及有效費率版本，讓未知費率待對帳。TS 是呼叫端指定 `5m`，Python 使用同值的預設參數，建議明確對齊。[TypeScript 計價 helper](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/ts/shared/types.ts:75) · [Python 計價 helper](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/py/shared/types.py:34) · [Claude 價格](https://platform.claude.com/docs/en/about-claude/pricing)

5. **補一段實際整合的適用邊界。** 本章沒有送出 `strict: true`、`output_config.format`、`thinking`、MCP Connector 或 Batch 請求。若以它們解釋維運行為，應明示 `strict: true` 在工具定義上約束輸入 schema，`output_config.format` 約束模型輸出格式，業務授權仍由應用程式執行。Thinking 費用採 API Usage 的輸出 token，Sonnet 5.5 的參數應依模型遷移文件。自管 MCP Streamable HTTP 與 Anthropic Connector 是兩種執行邊界，Connector 可由服務端呼叫公開 HTTP 的 MCP 工具，不能假設本地 `tool_use` 閘門會攔到，因此 Shadow 需在 Connector 憑證或 MCP 服務端限制工具。Batch 應按每個成功結果的 Usage 歸因，以 `custom_id` 關聯工單，並處理失敗、取消與過期結果。`claude-sonnet-5-5` 作為固定快照的說法正確。[Claude Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) · [Sonnet 5.5 遷移指南](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5) · [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [Batch Processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing) · [Model IDs and Versioning](https://platform.claude.com/docs/en/about-claude/models/model-ids-and-versions)

## Clarity / Minor Suggestions

- 開頭可直接用退款案例說明 HTTP 成功、模型回合結束與業務結案的差異。傳統微服務同樣可能回傳 `200` 卻未達成業務目的。
- 將 `Cache Hit Ratio` 標為「快取讀取 token 占比」，另說明冷啟動、TTL、路由及前綴長度。前綴指紋應涵蓋實際送出的工具、系統指示與快取訊息，並排除原始敏感內容。
- 相同 `tool_name` 連續失敗兩次只是初始策略。建議用操作鍵或參數指紋、錯誤類型及是否可重試來界定，避免把同名工具的獨立查詢算成同一故障。
- PostgreSQL 的 `(tenant_id, created_at)` 索引支援租戶及時間範圍查詢，`ticket_category` 仍須在該範圍內篩選或聚合。把這一點寫明即可。
- 範例連結改用相對路徑，避免離線讀者遇到作者機器上的 `file://`。把 `Pass^k` 的定義與 ch07 連在一起。