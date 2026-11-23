## Verdict

**NEEDS_REVISION**

以提供的 Base-Numbers Table 為基準，重算第 12 章的成本、流量與損益，並檢查 repo 內的兩份完整範例。Python 原指令與 TypeScript 經 Node 24 載入的執行結果皆為 exit `0`，也都讓 **$18,150／月**的候選設定通過成本閘道。TypeScript 已驗證執行行為，`tsc --noEmit` 尚未驗證。兩份範例皆為本地設定驗證器，沒有發出 Claude API 請求。

## Critical / Factual / Math Issues

1. **統一 $18,000 的預算口徑與 US 推論成本。** 基準表的 `$0.012／筆 × 1,500,000 筆 = $18,000／月`。範例的 `$0.011 × 1.1 = $0.0121／筆`，即 `$18,150／月`、`$605／天`，同時超過兩項上限。若 $18,000 是含 US 推論加價的硬上限，基礎成本須降到約 **$0.010909／筆**。`inference_geo: "us"` 控制模型推論地理位置，費率倍率適用於支援平台與模型的 input、output、cache write、cache read。儲存、日誌、應用服務及 MCP 工具的落地範圍須各自驗證。 [Anthropic 定價](https://platform.claude.com/docs/en/about-claude/pricing) · [資料駐留](https://platform.claude.com/docs/en/manage-claude/data-residency)

2. **修正四階段帳本與損益平衡。** 以下沿用章中的每筆 `$0.011`、L2 節省 `$1.20`、L3 節省 `$1.60`。前三階段採全球推論價，第四階段採 US 價。階段二若維持影子流量，假設 Canary 請求取代對應的影子請求，每筆只呼叫一次。

   | 階段 | 重算結果 |
   |---|---|
   | Day 1–14，100% Shadow | 50,000 筆／天，節省 0 小時。API 月化 $16,500，14 天實際 $7,700 |
   | Day 15–35，5% L2 | 2,500 筆／天、75,000 筆／月。每筆省 3 分鐘，即 0.05 小時，月化節省 $90,000。僅呼叫 5% 時，API $825、淨節省 $89,175。維持全量呼叫時，API $16,500、淨節省 $73,500 |
   | Day 36–60，30% L2 | 15,000 筆／天、450,000 筆／月。月化節省 $540,000，API $4,950，淨節省 $535,050 |
   | Day 61–90，70% L2／30% L3 | L2 為 1,050,000 筆、節省 $1,260,000。L3 為 450,000 筆，應用精確的 `4/60` 小時，節省 **$720,000**。合計 **$1,980,000**，扣除 US API $18,150 後為 **$1,961,850／月** |

   第四階段的加權節省為 `0.7 × $1.20 + 0.3 × $1.60 = $1.32／筆`。假設全系統每天仍支出 `$605`，且取得節省的工單維持 70/30 組合，連續值門檻為 `605 ÷ 1.32 = 458.33`，從 **459 筆／天**起為正，約 0.918%。若要求整數工單維持精確 70/30，最小為 **460 筆**。原文的 `$550.80` 是 `459 × $1.20`，搭配的是全球推論的 `$550／天`。459 恰好也出現在 US 混合案例，但推導不同。若 API 只對實際處理的工單收費，應以每筆貢獻及固定成本另算門檻。

   進階題的 **1,800,000 筆／月、$19,800 基礎成本、$21,780 US 成本、$726／天**皆正確。以 L2 計，**605 筆恰好打平，606 筆才為正**，約 1.01%。若交付的是 90 天累計值，按四段 **14／21／25／30 天**及僅呼叫 5% 的 Canary 方案，API 共 **$30,552.50**，估算人力價值 **$2,493,000**，差額 **$2,462,447.50**。本章以美元呈現的是估算淨效益。若稱為 ROI，須定義分母，並交代人力時數能否轉成實際支出減少，以及營運、人工覆核、退款損失等成本。

3. **基準成本成立，快取失效的成本推論需要改寫。** `50,000 × 30 = 1,500,000`，平均 `50,000 ÷ 86,400 ≈ 0.579` 工單／秒，尖峰 12 約為平均的 **20.74 倍**。工具數 `12 + 6 = 18`，固定前綴 `2,400 + 3,600 = 6,000`。依 ch01 的口徑，首輪輸入為 6,000，後四輪各增加 1,200，含前輪輸出與工具回傳，因此總輸入是 `5 × 6,000 + (0+1+2+3+4) × 1,200 = 42,000`，輸出為 `5 × 350 = 1,750`。Sonnet 成本為 `$0.084 + $0.0175 = $0.1015／筆`，即 `$5,075／天`、`$152,250／月`。$18,000 對應 **88.18%** 降幅。純人工的 `4/60 × $24 = $1.60／筆`、`$2,400,000／月`也正確。

   官方定價支持基準表的模型牌價、快取寫入 **1.25×／2×**、讀取 **0.05×／0.10×**及 Batch **50%** 折扣。`cache_read_input_tokens` 歸零時，模型路由、回合數、Batch 比例與快取寫入費仍會影響帳單，無法直接推得 `$152,250`。用實際模型與各類 `usage` 重估，並定義 `0.70` 告警的分母，例如合格前綴的讀取 tokens ÷（讀取＋寫入 tokens），另監控合格請求的快取覆蓋率。ch12 的 `$0.011` 也應明列為 rollout 假設，交代它與 ch08 Stage 5 約 `$0.009860` 的口徑差異。 [Anthropic 定價](https://platform.claude.com/docs/en/about-claude/pricing) · [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

4. **把退款權限落在工具服務端，並定義未知提交結果。** 將工單內容、模型輸出、工具回傳及 MCP 內容視為不可信資料。每次寫入都由服務端依租戶、操作者、訂單、幣別、金額與剩餘可退額重新授權。L1 不授予寫入憑證，L2 核准綁定特定請求內容與版本，L3 執行單筆及累計上限，超額或資料不一致時轉 L2。用業務操作 ID 保證重試與跨 worker 去重，並以交易或原子條件更新防止並行超退。付款端逾時後先查核原操作結果，再決定是否重試或交人工處理。Shadow 也應在工具層禁止外部寫入與通知。

5. **把 SLO、限流、預算與退場定義成可驗證的運行契約。** `5s < 12s < 60s` 的數值順序正確，但 8 次 LLM 呼叫單獨已可用掉 `96s`，尚未計入工具、重試及排隊。分流的 2.5s、多步的 18s 是端到端 p95 目標，應分別定義統計起訖，說明 L2 人工等待是否另計，並用剩餘 deadline 限制每次呼叫。12 工單／秒若每單 5 次模型呼叫，容量估算已是 **60 模型請求／秒**，還要考慮每模型 token 限額、工具 fan-out、重試及影子流量。每日若按 30 天均分，`$18,000 ÷ 30 = $600`，150% 為 `$900`。若 $600 是硬上限，$900 熔斷不能是唯一控制，需在請求前預留預算並對帳。另定義 5% 錯誤率的分母、3 分鐘觀測窗，以及從觸發到 30 秒內停止新寫入的界線。已提交或結果未知的在途退款仍須對帳，人工佇列也需有承載上限。

## Code & API Issues

- **兩份成本閘道驗的是設定值，且實際容許 US 成本到 $19,800。** `18,000 × 1.1 = 19,800`，所以第二個比較沒有提供獨立的預算約束。`dailyTicketVolume`／`daily_ticket_volume` 未參與運算。請分開輸入硬上限與預估基礎單價，以流量、單價、計費天數與倍率推得預估支出，再比對含加價的上限。修正後，現有 US 候選設定應在此閘道失敗。
- **兩份 timeout 判斷都能放過明顯無效的設定。** 程式缺少 `llmTimeout < wallClockTimeout`，以 `llmTimeout × maxTurns <= 2 × wallClockTimeout` 代替。工具 5 秒、LLM 12 秒、總期限 6 秒、1 回合仍可通過。範例的 `96,000 <= 120,000` 也解釋了為何顯示通過。驗證正值、整數回合、完整期限關係，並說清楚 8 是示例、12 是否為政策上限。在 runtime 傳遞絕對 deadline、取消未完成工作，並限制 SDK 內建重試與應用層重試的總次數。
- **加上 runtime schema，並補齊 TS／Python 行為差異。** TS 的共用價格表宣告為 `Record<string, ModelPricing>`，所以 `keyof typeof ...` 無法限制到列出的模型 ID，且 TS 缺少 Python 的 `model_registry` 閘道。兩版的型別標註都無法驗證外部設定。未知的 `autonomyLevel` 可跳過 L2／L3 檢查，未知 geo 會走全球費率，負 SLO 或負預算也可通過。請驗證 enum、嚴格布林、有限正數、整數及 `[0,1]` 比率，並驗證 L3 上限確實落在核准政策內。章中 TS 節錄與完整實作的三個閘道相符，因此修正也要同步到節錄。 [TypeScript 範例](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/ts/ch12/index.ts:45) · [Python 範例](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/py/ch12/main.py:46)
- **把示範驗證器接到部署的真實設定與驗收證據。** 兩個入口都只跑寫死的候選物件。`2.1s／15.4s`、`0.94／0.88`、`180 天`在數值上符合設定閘道，無法證明延遲、評測或留存真的達標。CI 應載入實際部署設定，並對應帶版本的負載測試、Eval 報告、工具權限清單、預算熔斷及退場演練證據。L3 的離線 `Pass^3 ≥ 0.95` 與連續 14 天零嚴重誤判應分別驗收。明訂線上如何重跑同一案例三次、最低樣本數、嚴重度及標註方式。自我檢核答案也應補回流程圖中的 14 天 `Pass^3` 門檻。
- **釐清 Messages API、Agent SDK 與本地設定欄位。** 裸 Messages API 的回合上限由應用程式執行，`max_turns` 是 Agent SDK 的 Python 選項，TypeScript 對應 `maxTurns`。本章使用的 5.5 模型應依型號採 adaptive thinking 與 `output_config.effort`，並以實測用量把 thinking 納入輸出預算。`strict: true` 放在自訂工具定義，約束工具名稱與輸入結構。`output_config.format` 約束最終 JSON。授權、金額與業務狀態仍由服務端驗證。`cache_control` 可用於自動快取或明確斷點，需驗證實際序列化前綴及模型門檻。這些欄位目前都沒有出現在範例的 API 請求中，適合在 PRR 增列整合驗收。 [Agent SDK](https://code.claude.com/docs/en/agent-sdk/typescript) · [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) · [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) · [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- **明訂停止原因與串流失敗的處置。** `tool_use` 只在收到完整且驗證通過的工具區塊後執行，`tool_result.tool_use_id` 須對應。`pause_turn` 依文件續跑 server-tool 回合。`max_tokens`、`refusal`、模型上下文超限、串流中斷及 HTTP 200 後的串流錯誤都須有明確分支。收到部分 JSON 時不得觸發寫入。遇 `429` 遵守 `Retry-After` 與剩餘 deadline，`529` 採限次退避，工具的 `is_error` 依錯誤分類決定是否重試。 [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)
- **把 MCP 傳輸、Connector 與 Batch 的責任分清楚。** Streamable HTTP 是 MCP 傳輸。Anthropic Connector 是 Messages beta，使用 `mcp-client-2025-11-20`、`mcp_servers` 與 `tools` 內的 `mcp_toolset`，連到可公開存取的 HTTP 端點，目前僅支援工具呼叫。若由 Connector 呼叫寫入工具，授權與審批必須在遠端服務端強制執行。Batch 是非同步路徑，適合離線稽核，線上 p95 路徑應獨立。驗收應涵蓋逐項結果、`custom_id` 對應、失敗重送與去重。Connector 與 Batch 的保留條件也需納入資料審查。 [MCP 傳輸規格](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) · [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [Message Batches](https://platform.claude.com/docs/en/api/beta/messages/batches/create) · [API 資料保留](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)

## Clarity / Minor Suggestions

- 將「除錯成本呈指數上升」「第三方框架高度抽象」改成可驗收的選型條件，例如能否取得實際請求、逐回合 usage、重試次數與快取命中，以及能否接管取消和審批。觀測預設記錄 request ID、模型、停止原因與分類用量。若需留存內容，明訂遮罩、存取與留存政策。
- 流程圖從 L1 開始，90 天計畫從 Shadow 直接進 L2。補一句 L1 驗收在何時完成。把 `$50`、14 天、90 天、180 天、70% 及 5%／3 分鐘標示為本案例的設定或政策，並交代對應的驗收依據。
- 將機器專屬的 `file:///Users/...` 改為 repo 相對連結。延伸閱讀的 Anthropic 連結應指向實際引用的定價、快取、地理位置或錯誤文件。Google 目前的連結對應 Launch Coordination，若要引用 PRR 可另鏈到 SRE Book 的對應章節。 [Google SRE Launch Coordination](https://sre.google/sre-book/launch-coordination/) · [Google SRE Production Readiness Review](https://sre.google/sre-book/evolving-sre-engagement-model/)