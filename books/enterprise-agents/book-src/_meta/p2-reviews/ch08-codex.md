## Verdict

**NEEDS_REVISION**

第 5 階段的 **$14,789.55/月** 可以重現，但它是特定假設下的 Claude token 成本。依兩份範例的路由規則重算 Batch 折扣，全量採用美國境內推論時可達 **$18,826.27/月**，超過目標。發布前應修正帳本假設、補齊 SLO 的驗證方式，以及落實串流中斷與寫入工具的安全邊界。

Python 本地範例已執行。TypeScript 以 Node 載入並執行同一模組，確認回傳 `$14,790`、`$0.00986`、`90.3%`。環境缺少 `tsx` 和 `tsc`，因此未驗證原文的 TS 啟動命令或完整型別檢查。兩份範例均未呼叫 Claude API。

## Critical / Factual / Math Issues

1. **Batch 折扣應按成本加權。** `1 − 30% × 50% = 0.85` 的前提是這 30% 工單恰好占折扣前成本的 30%。兩份範例只把低優先發票工單送入 Batch，且全部走 Haiku。若它們占全體工單 30%，沿用第 5 階段其他假設，月成本應為 `1,500,000 × (0.01159965 − 0.30 × 0.50 × 0.00126525) = $17,114.79`，全量 `us` 為 **$18,826.27**。依模型、工作流和執行模式分列工單量、token 及命中率。Batch 折扣可與快取和地理倍率疊加，但 Batch 快取命中須另估。 [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing) · [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

2. **逐回合推導 token 量，並把第 5 階段標為待驗證的情境。** 基準的 `42,000 = 5 × 6,000 + 1,200 × (1+2+3+4+5)` 成立，前提是每回合新增的 1,200 tokens 逐次保留，且已包含會重送的歷史內容。第 3 階段的 `18,000 = 5 × 3,600` 成立，但每回合新增 700 tokens，若全留會累計 `10,500`；若每次請求只留最近三份，則為 `8,400`，仍需要交代 `7,000` 的來源與摘要成本。第 5 階段若沿用 `3,600 × 3.5`，得到 `12,600` 個前綴 tokens。`13,500` 需要額外的前綴來源或不同的工作負載分布。`1,050 ÷ 3.5 = 300` billed output tokens／回合，也需要包含工具參數和 thinking 的實測。結構化輸出可降低格式重試，但章節仍需量測它能省多少回合、是否維持任務成功率，以及升級、重試、摘要與額外 Haiku 護欄的成本。 [Thinking cost and billing](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)

3. **瀑布算術大致正確，需統一精度並說清楚達標條件。** 以下沿用原稿輸入與 `0.85` 假設，按中間值不捨入、金額採十進位四捨五入重算。

   | 階段 | USD／筆 | USD／月 | 累積降幅 |
   |---|---:|---:|---:|
   | 0 基準 | 0.1015 | 152,250.00 | 0% |
   | 1 路由 | 0.04872 | 73,080.00 | 52.0% |
   | 2 快取 | 0.024897 | 37,345.50 | 75.5% |
   | 3 工具分組與裁剪 | 0.0181062 | 27,159.30 | 82.2% |
   | 4 Batch | 0.01539027 | 23,085.41 | 84.8% |
   | 5 結構化輸出，加 Batch | 0.0098597025 | 14,789.55 | 90.3% |

   - 階段 1 各模型為 `$0.005075 / $0.101500 / $0.203000`。階段 2 有效倍率 `0.215 / 0.170 / 0.170`、Haiku 和 Sonnet 等效輸入 `18,450 / 17,100`，以及各模型成本 `$0.002720 / $0.051700 / $0.103400` 均正確。階段 3 補列 Opus `$0.075240`。階段 4 精確值為 `$23,085.405`，原稿 `$23,085.40` 可由 ties-to-even 得到。階段 5 各模型折扣前為 `$0.00126525 / $0.024090 / $0.048180`。
   - `50,000 × 30 = 1,500,000`，基準 `$5,075/日` 正確。`50,000 ÷ 86,400 = 0.5787 req/s`，所以 `12 req/s` 是約 `20.74×`，可寫「約 21 倍」。`18 = 12 + 6`、`6,000 = 2,400 + 3,600`、`3,600 = 2,400 + 1,200` 均成立。六個工具共 `1,200` tokens 則假設每個工具平均 `200` tokens，應以實際 schema 驗證。`$18,000/月 = $0.012/筆` 對應 **88.18%** 降幅。降幅恰為 88% 時仍要 `$18,270/月`。
   - 沿用原稿 `0.85` 假設，全量 `us` 為 `$16,268.51`，餘裕 `$1,731.49`。固定同樣 90% 命中率，**同時**改成 `1h` 與 `us` 為 `$17,631.74`。只改 `1h` 為 `$16,028.85`。`inference_geo: "us"` 控制推論位置，合約若涵蓋儲存、保留及外部工具處理位置，須各自查核。 [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing) · [Data residency](https://platform.claude.com/docs/en/manage-claude/data-residency)

4. **修正快取回本與命中條件。** 5m 首次寫入後，**一次**命中即比兩次無快取便宜，`1.25 + 0.05 = 1.30 < 2`，Haiku 的 `1.35 < 2` 也成立。20 分鐘間隔的三次範例算對，`22,500 → 12,600` 確實省 44%。兩次請求時 1h 也已優於兩次 5m 冷寫入，但相鄰請求必須重用相同前綴，且間隔要落在可命中的期限內。三款 5.5 在 Claude API 的門檻都是 **512 tokens**。90% 應定義為可快取前綴的 **token 讀取占比**，另列冷寫入及未快取量。日流量只推出全量平均 `34.72` 筆／分鐘。若均分四組，每組約 `8.68` 筆／分鐘，還會依模型與部署範圍分散。請移除單憑工單量即可保證 `>90%` 的說法，並計入冷啟動時首個回應開始前的併發請求。 [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

5. **timeout、併發與 SLO 需要各自的容量依據。** `TTFT + (N−1) × TPOT` 是以首個 token 定義 TTFT 時的單次生成近似式。端到端還有排隊、工具、護欄及多回合。`600+600 → 約 600ms` 只適用於相互獨立且可立即並行的 I/O。五次 LLM 上限就有 50 秒，必須以剩餘 deadline 限制每步，並為分流另定低於 2.5 秒的預算。`16+2=18` 只是拆預算。請用峰值負載量測 TTFT、首個可安全顯示內容與端到端 p95。租戶的 `25% × 16 = 4` 算對，但 Token Bucket 控制速率，單 Worker Semaphore 控制本機在途量。若 16 是全域在途工單上限，`12 req/s` 只容許平均約 `1.33s` 的占用時間。分開限制全域／租戶在途量、模型 RPM／ITPM／OTPM 和工具併發，佇列也要有容量與逾時。

6. **串流、金流與 Prompt Injection 的邊界必須明確。** 平行護欄在首段內容或工具動作前要有放行點。若兩者並行，放行延遲取決於較慢的一邊。工單、預取資料、摘要和工具結果皆視為不受信任資料，schema 驗證之外還須在工具端檢查租戶、訂單歸屬、權限及業務條件。只有獨立唯讀工具適合直接並行。對寫入／退款，使用持久化業務冪等鍵、狀態與對帳，並處理 timeout 後結果未知。`SET NX EX 300` 只是租約，範例 key 還缺租戶與執行身分。它無法防止逾時後重複寫入或供應商重複計費。Redis 預取的 `300s` 也應定義鮮度、失效與命中後的授權檢查。

## Code & API Issues

- **完整範例只驗證路由和兩個成本端點。** TS 的 Router 與節錄一致，Python 路由條件也一致，但 Python 缺工具分組與快取 payload builder。兩份 `simulate*Waterfall` 都只算基準與第 5 階段，且把 `5m` 寫死，沒有 `inference_geo` 參數。請補齊章節承諾可驗證的功能，或明確縮小範例的驗證範圍。TS 的 `file://${process.argv[1]}` 比對遇到空白或需 URL 編碼的路徑會失敗，應用 Node 的 `pathToFileURL` 正規化後比較。

- **Wire 範例需要有效 schema 與實際 SDK 型別。** `{"...":"..."}` 是佔位內容。TS 的 `input_schema: unknown` 無法直接滿足 SDK 工具參數型別。`selectToolsForCategory` 依輸入順序過濾，無法兌現字典序保證。應固定排序、版本化工具集合，並驗證各組最終 token 數。`cache_control` 的 `ephemeral`、`5m`／`1h` 和最多四個斷點皆正確。補充比對順序 `tools → system → messages`、斷點往前約 20 個 block 的查找，以及工具組改變也會影響後面的 system 前綴。 [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

- **結構化輸出與 thinking 要有可對照的請求契約。** 工具參數約束是工具定義上的 `strict: true`。最終 JSON 用 `output_config.format`，包含 `type: "json_schema"` 與 `schema`。兩者用途不同，截斷或拒答仍需走各自的處理分支。5.5 的 adaptive thinking 要納入成本與延遲測試，可透過 `output_config.effort` 調整。以回應的 billed `output_tokens` 計價，並保留工具續回合需要的原始 thinking blocks。 [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs) · [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking-steering-and-cost)

- **補齊停止原因與串流狀態。** 處理 `stop_sequence`、`refusal`、`pause_turn`、`model_context_window_exceeded`，以及使用相關功能時的 `compaction`。`tool_use` 要等完整參數後再驗證與執行，並用匹配的 `tool_use_id` 回填 `tool_result`。SSE 應合併 `message_start` 與累計的 `message_delta.usage`，並用 `message_stop` 或 SDK 完成訊號確認正常結束。HTTP 200 後仍可能收到串流 `error`。斷線時的可見 delta 只能當估算，帳本應保存 request ID、attempt ID、完成狀態和估算標記，再另行對帳。 [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) · [Streaming Messages](https://platform.claude.com/docs/en/build-with-claude/streaming)

- **Batch 是逐筆 Messages 推論，24 小時是到期界線。** `ended` 後按 `custom_id` 處理順序不定的 `succeeded`、`errored`、`canceled`、`expired`。`custom_id` 是批次內關聯識別，應另存批次 ID、租戶、業務操作 ID 和嘗試狀態。永久驗證錯誤須修正後才重送。多步 client-tool 工作流還須由外部編排工具執行與下一次 Messages 呼叫，不能把一個 batch item 當完整 Agent Loop。30% 離線流量也應明訂獨立的完成目標。 [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

- **對齊應用層與 SDK 重試，補足帳本資料。** TS `maxRetries` 與 Python `max_retries` 預設均為兩次。若應用層負責重試，停用 SDK 重試或合併計入同一 deadline。TS timeout 用毫秒，Python 用秒。明訂「最多 3 次」指嘗試或重試；若是三次重試，Full Jitter 的等待上限依序為 `0.5/1/2s`，合計最多 `3.5s`，另加請求耗時。計費 helper 還應以**單次請求**的總 prompt tokens 判定 Haiku `>100K` 階梯，支援 5m／1h 分開寫入量、Batch、geo 及費率版本，並拒絕未知模型的靜默 Sonnet 計價。PostgreSQL 需區分可計費 attempt 與邏輯 turn，為帳本寫回加唯一鍵，並提高 `NUMERIC(10,6)` 的小數精度，避免逐筆捨入累積。 [TypeScript SDK](https://github.com/anthropics/anthropic-sdk-typescript) · [Python SDK](https://github.com/anthropics/anthropic-sdk-python) · [Anthropic Pricing](https://platform.claude.com/docs/en/about-claude/pricing)

- **MCP 在本章沒有可驗證的實作。** 若工具分組涵蓋 MCP，須區分應用程式作為 MCP client 使用 Streamable HTTP，與 Claude Messages API 代呼叫遠端工具的 Connector。後者使用 `mcp_servers`、對應的 `mcp_toolset` 及相容 beta header，有遠端存取和資料保留限制。兩條路徑都要明定工具授權、租戶憑證及資料出境邊界。 [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector)

## Clarity / Minor Suggestions

- 統一「五大槓桿」與瀑布的對應。帳本把工具分組與回傳裁剪合併，另新增結構化輸出。自我檢核第 2 題可直接列出 Sonnet 的邊際成本，少 700 個輸出 tokens 省 `$0.007`，同量未快取輸入省 `$0.0014`，命中輸入省 `$0.00007`。TPOT 是每 token 耗時，裁減 tokens 直接減少的是總生成時間。
- 將 `300–600ms`、告警門檻、60 秒輪詢與 `16/4` 標成示例配置，補上量測期間與分母。第 3 題可用分組前後的實際 token 帳本比較節省幅度，並維持寫入工具的最小權限。
- 將絕對 `file:///Users/...` 範例連結改為儲存庫相對路徑，並在預期輸出分別列出 Python 的美分精度與 TypeScript 的整美元精度。