## Verdict

**NEEDS_REVISION**

護欄成本與自我檢核的算術正確，兩份本機範例也都跑出預期的決策、遮罩與 `$3.75` 日成本。發布前須修正三個重點：Haiku 5.5 的 `temperature: 0` 會使請求失敗，退款政策缺少資源層授權與冪等控制，雜湊鏈與 ZDR 的保證超出實際能力。

驗證範圍為 Python 直接執行、TypeScript 透過 Node 的型別轉換執行，並核對共用計費函式與 Anthropic 官方文件。TypeScript 環境缺少 `tsx`、`tsc` 與本機依賴，因此未執行章載 `npx tsx` 指令或完整型別檢查。兩份範例均為離線模擬，未送出 Claude API 請求。

## Critical / Factual / Math Issues

1. **退款授權必須綁定實際訂單與金流狀態。** `PolicyEngine` 只比較呼叫端傳來的 `targetTenantId`／`targetCustomerId`。工具執行器應以已驗證身分與 token scope 查詢實際 `orderId`，並在寫入時原子檢查訂單歸屬、付款狀態、幣別與剩餘可退額。每回合一次寫入仍容許跨回合重複寫入，也涵蓋不了多 worker、重試及付款端已成功但本地逾時。以業務操作 ID 建立持久冪等紀錄，將同一鍵傳給金流端，並對不確定結果先查詢或對帳。HITL 須先持久建立審批單，將核准綁定訂單、金額、幣別與版本，執行前重新授權。只有建單成功，才能告知客戶已轉人工。

2. **短效 token、唯讀降級和 PII 遮罩各有明確邊界。** Scoped token 應綁定已驗證的 actor、工單或執行 ID 與 audience，使用伺服器時間在 `now >= expiresAt` 時拒絕，並在派發點查有效狀態。Redis 刪鍵無法撤回已派發操作，已取出的 token 副本也需要明確的撤銷語義。唯讀工具同樣要做租戶、資源及欄位授權。分類器不可用時只開放明確核准的低敏工具，其餘轉人工。XML 跳脫保護資料區塊的結構，仍須將工單和工具結果視為不可信資料。進模型前以欄位白名單投影，出站前檢查資料及目的地。現有 regex 只涵蓋特定 email、16 位卡號和美式 SSN 表示法，請刪除「徹底切斷外洩」的保證。無網路的沙盒與外送 Webhook 應走不同路徑，後者由受控出站代理強制驗證目的地與 payload。

3. **雜湊鏈提供可驗證的完整性，前提是鏈頭有獨立可信的錨點。** `(tenant_id, seq)` 只保證序號唯一，無法阻止缺號、整段重算或刪除尾端。多 worker 同時 append 時，應在交易內序列化每租戶的鏈頭更新，並把 checkpoint 寫入獨立的簽章或不可覆寫儲存。驗證器要重算每筆 hash、確認序號及連結，並比對可信 checkpoint。統一 SQL、TS 和 Python 的欄位與序列化規格，另記錄授權決策、實際執行結果與審批狀態。刪除「任何竄改」與「毫秒級」的承諾。

4. **ZDR、資料訓練用途與推論地域是三項不同的治理屬性。** `inference_geo: "us"` 約束受支援部署的推論地域，`1.1×` 費率正確。應另外查核工作區的 ZDR 協議、端點與功能資格，以及 Redis、日誌、工具端與其他下游服務的資料所在地和保留期限。稽核應記錄可查證的設定及來源，硬編 `zeroDataRetention: true` 或引用一般 API 標頭無法證明 ZDR。Claude API 的 MCP Connector 與 Message Batches 均不符合 ZDR，Batch 結果自建立起可取用 29 天。 [Anthropic 定價](https://platform.claude.com/docs/en/about-claude/pricing) · [API 資料保留](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention) · [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

5. **重算結果如下。** 章內需要修正的是 ROI 歸因、尖峰限流的適用範圍，以及把估算寫成保證的敘述。

   | 項目 | 獨立重算與判定 |
   |---|---|
   | 入口護欄，500 input／50 output | `$0.000050 + $0.000025 = $0.000075`／筆，`$3.75`／日，`$112.50`／30 天。US 模式為 `$0.0000825`／筆、`$4.125`／日、`$123.75`／月。正文「不到 4 美元」只適用於標準費率。 |
   | 挑戰題，800 input／100 output | `$0.000080 + $0.000050 = $0.000130`／筆。乘 `1.1` 後為 `$0.000143`／筆、`$7.15`／日、`$214.50`／月。全數正確。 |
   | 損失與 ROI | `2 × $5,000 = $10,000`／月。若分類器能獨立避免全部損失，`($10,000 − $112.50) ÷ $112.50 = 87.89×` 淨 ROI。應改用「既有 Policy Engine 上再加分類器所減少的預期損失」當分子基礎。若 `$200` 政策已攔下同樣兩筆，這兩筆給分類器的增量可歸因效益為 `$0`。`95%` 攔截率與「風險降至零」均無證據。 |
   | 工作量與 SLO | `50,000 × 30 = 1,500,000` 筆／月，`50,000 ÷ 86,400 = 0.5787 req/s`，`12 ÷ 0.5787 = 20.74×`，基準的 `20×` 為約數。`12 req/s` 是全站尖峰基準。若另設每租戶 `12 req/s`，應明列為獨立配額，並定義全站容量、桶深、跨副本原子更新與 in-flight 上限。`800 ms` 是護欄 deadline，`2.5 s`／`18 s` 是端到端 p95，需分別量測。 |
   | 前綴與未優化成本 | `12 + 6 = 18` 個工具，`2,400 + 3,600 = 6,000` tokens。依 ch01 的口徑，首輪為 `6,000`、後四輪各累加 `1,200`，合計 `42,000` input，`5 × 350 = 1,750` output。若首輪另外新增 `1,200` 個計費 token，則合計為 `48,000`。以 `42,000` 口徑計得 `$0.084 + $0.0175 = $0.1015`／筆、`$5,075`／日、`$152,250`／月。`$18,000 ÷ 1,500,000 = $0.012`／筆，相對基準降幅 `88.18%`。 |
   | 費率與本章其他數字 | 基準三款模型牌價、Haiku `>100K` 級距、`1.25×`／`2×` 寫入、`0.05×`／`0.10×` 讀取、Batch 半價及 US `1.1×` 均吻合官方定價。`300 s = 5 min`，`5,000 ms = 5 s`。`$45 < $200 < $250 < $5,000`，情境金額一致。`128`／`64` tokens、`256 MiB`、風險門檻及告警閾值屬配置假設，應標為示例並交代驗證方式。 |

   定價依據見 [Anthropic 定價](https://platform.claude.com/docs/en/about-claude/pricing) 與 [Haiku 5.5 規格](https://platform.claude.com/docs/en/models/haiku-5-5/overview)。

## Code & API Issues

1. **修正 Layer 1 的請求與回應契約。** Haiku 5.5 的 `temperature: 0` 會回 `400`，請省略 sampling 參數。Haiku 5.5 預設啟用 adaptive thinking。若要測試短輸出的分類設定，可明確送 `thinking: {"type":"disabled"}`，並以 `output_config.format` 的 JSON Schema 約束回應。範例中的 `"allow" | "block" | "escalate"` 是型別表示法，請改用合法 JSON 實例及 schema `enum`，並統一 `risk_score`／`riskScore` 和 `category`／`reason` 的映射。只接受成功完成且解析、驗證皆通過的結果，對 `max_tokens`、`refusal`、空回應和解析失敗走明確降級。`500/50` 應寫成成本假設，實際結算採 API usage。將上限降至 `64` 前先驗證完整輸出率與尾延遲。 [Haiku 5.5 遷移指南](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) · [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) · [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

2. **明確區分 SDK timeout、HTTP 錯誤與總 deadline。** `stream: false` 可用，非串流可簡化解析，端到端延遲仍需量測。`timeout` 是 SDK／傳輸設定，TS 的 `timeout: 800` 用毫秒，Python 的 `timeout=0.8` 用秒。兩套 SDK 預設重試可能突破預算。若入口只允許一次嘗試，設定 TS `maxRetries: 0`、Python `max_retries=0`，再用外層 deadline 約束整個分類階段。分別記錄 `429`、`529` 與本地逾時。`retry-after` 適用於仍有時間預算的重試或背景調度。 [Anthropic SDK 指南](https://github.com/anthropics/skills/blob/main/skills/claude-api/SKILL.md)

3. **補齊工具呼叫與串流的狀態機。** `strict: true` 放在 client tool 定義上，驗證的是受支援 JSON Schema 子集內的工具名稱與參數形狀。金額、資源授權及狀態仍由後端驗證。對一般 client-tool turn，收到完整 `message_stop` 後還要確認 `stop_reason: "tool_use"` 與完整參數，才可派發。`max_tokens`、中斷或 SSE error 不可觸發寫入。保留 assistant 原 turn，緊接一則 `user` 訊息，把所有對應的 `tool_result` 放在 content 前方，逐一以 `tool_use_id` 配對，包括拒絕及執行失敗。`pause_turn` 則依 server-tool continuation 規則處理。 [Strict tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/strict-tool-use) · [Handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) · [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)

4. **把 cache breakpoint 寫到具體的區塊。** 對固定工具集，可在最後一個靜態 system content block 設 explicit `cache_control`，覆蓋按 `tools → system → messages` 排序的前綴。若刻意另外在最後一個 tool definition 設斷點，說明它支援的重用情境。動態工具裁切會改變工具前綴，`6,000` tokens 是完整工具集的基準，應按實際工具組合觀測命中。快取 miss、write 和 TTFT 的關係需以 metrics 驗證。範例計費行應標明是 global、無快取的估算，與稽核記錄中的 US 設定分清楚。 [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

5. **交代 MCP 和 Batch 會如何改變政策執行點。** 本章兩份程式均未使用這兩項 API。若以應用程式自管 MCP Streamable HTTP client，應用層可在派發前授權，MCP server 仍須逐請求驗證身分與 scope，session ID 不能充當憑證。若用 Claude API Connector，`mcp_servers` 和 `mcp_toolset` 走 beta API，Anthropic 可在回應交給應用前呼叫 MCP 工具，因此寫入政策必須由 MCP server 或其前置 gateway 強制執行。若以 Batch 離線評估護欄，輸入與輸出半價，結果依 `custom_id` 配對，並處理個別失敗與過期。入口 `800 ms` 判定仍須走即時路徑。 [MCP Streamable HTTP](https://ts.sdk.modelcontextprotocol.io/v2/api/%40modelcontextprotocol/node/streamableHttp.html) · [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

6. **兩語範例與章載契約有可觀察的落差。**
   - **退款驗證。** 章內 snippet 把缺少金額轉成 `0` 後允許執行。兩份完整程式拒絕缺值和非正數，但 `NaN` 仍能通過比較。統一以正整數最小貨幣單位做執行期驗證，同時驗證上限和幣別，並拒絕未註冊工具。現有未知工具預設為 `mutating`，若它出現在 allowlist，通用路徑仍可能回 `execute`。
   - **分類與降級。** 兩份程式都是 regex stub，只會產生 `allow`／`block`，`escalate` 若出現會落入正常政策路徑。改為明確處理三個分支，並把 SDK、Redis、串流及降級等未實作行為標成設計。`TKT-102` 是入口分類攔截，未驗證工具結果注入後的寫入防線。`TKT-103` 是同租戶跨客戶，請更正情境名稱或補真正跨租戶的測例。
   - **稽核與教學輸出。** TS 把時間戳納入 hash，每次執行的 hash 會變。Python 無時間戳，欄位命名及 JSON 序列化也不同。章載固定 hash 只吻合本次 Python 執行。兩者均未提供驗證器，且都暴露可變紀錄，TS 的 `readonly AuditEntry[]` 只限制陣列介面。範例應共用可重現的事件格式並提供 verifier，或改以可驗證的決策與遮罩結果作為預期輸出。故障模式還應區分 `pending_hitl` 與 `deny`，兩者可另以統一的「未執行」欄位彙總。

## Clarity / Minor Suggestions

- 將 `95%`、`0.90`、`0.50` 與告警閾值標為待校準的初值。用含正常客訴、直接注入和工具結果注入的評估集報告召回率、誤殺率、人工轉介量及 p95。`risk_score` 若未經校準，避免直接解讀為機率。
- 將示範中的 `policy=execute` 說明為「政策允許」，把實際退款成功留給金流結果事件。安全日誌使用結構化欄位與穩定 reason code，避免逐筆輸出整段工單正文。
- 自我檢核第 2 題可先問「這筆資料原本是否准許該客戶讀取」，再問「准許讀取的欄位能否輸出到這個目的地」。這能具體區分資源授權、欄位最小化與出站控制。