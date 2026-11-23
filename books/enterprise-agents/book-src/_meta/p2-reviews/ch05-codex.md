## Verdict

**NEEDS_REVISION**

兩份範例都能離線重現章內的 `$0.00051` 與 `$0.01811`，但所謂 `LIVE API` 只會呼叫 Router，範例仍會在缺少帳務證據時輸出退款已核准。財務比較也混入了 Router 輸出費，使宣稱的前綴成本降幅口徑不一致。

本次以貼出的章文及工作區範例為審查範圍。Python 以章內命令離線執行，TypeScript 以 Node 24 搭配模組路徑轉接離線執行。TypeScript 的 `tsx` 命令、完整型別檢查及真實 API 呼叫未驗證。

## Critical / Factual / Math Issues

1. **P0｜退款必須由應用程式依必要證據決定是否放行。** 兩份程式的 `billing_ledger` 都只查通用訂單物件，沒有實付、已退款或可退餘額。後端回傳 `not_found` 仍標 `ok`。Router 若省略帳務任務，甚至回傳空陣列，失敗清單也會是空的，程式隨即輸出 `refund_approved_by_opus_specialist`。應由程式依路由強制要求指定證據，檢查租戶、訂單、幣別、付款狀態及證據時效。缺件、衝突或過期一律轉人工。金流寫入前，由可信服務再次檢查可退款餘額及核准紀錄。一般物流也應在必要物流證據缺失時停止回報 `resolved_read_only`。

2. **P0｜Redis 租約與退款冪等需要明確的原子性及重放語意。** `30s` TTL 比 `18s` 期限長 `12s`，但程序暫停、網路分割或逾時後仍在執行的工作都可能跨過租約。用原子取鎖、租約持有者識別與安全釋放，並以持久狀態的版本檢查或 fencing 拒絕舊持有者提交。`86400s = 24h` 的 `orderId + action` 會阻擋合法的第二筆部分退款，也容許過期後重放。用包含租戶與穩定退款意圖 ID 的持久唯一鍵，綁定請求參數及金流供應商的冪等鍵，並定義「供應商已接受、回應遺失」時的查單與對帳流程。交接稽核表應能區分工作流、分支及嘗試次數，避免重試重複入帳。

3. **P0｜Handoff 壓縮需要可驗證的資料邊界。** `summary`、任意鍵的 `facts` 和例外文字都可能把不可信指令、跨租戶資料或敏感資訊帶給仲裁層。每種任務應有版本化欄位、大小上限、證據來源與觀測時間。分開保留模型摘要與後端驗證事實，並把例外映射成安全錯誤碼。Router 的輸出只授權查詢已核准的唯讀任務，工具服務仍須用可信租戶與身分做服務端授權。拓撲 DAG 和 `max_depth = 2` 也應由派發器執行，並另外限制整筆工單的派發總數。

4. **P1｜重算成本時統一前綴與輸出的範圍。** 下表以題給牌價計算。Haiku 用的是 ≤100K 級距，三款模型牌價、快取倍率、Batch 折扣與 US-only 附加倍率均與官方定價相符。[Anthropic 定價](https://platform.claude.com/docs/en/about-claude/pricing)

   | 項目 | 獨立重算與結論 |
   |---|---|
   | 工作負載與工具 | `50,000 × 30 = 1,500,000` 筆／月。`50,000 ÷ 86,400 = 0.5787 req/s`，`12 ÷ 0.5787 ≈ 20.74×`，可寫約 `21×`。`12 + 6 = 18`，`2,400 + 3,600 = 6,000`，Schema 平均 `3,600 ÷ 18 = 200` tokens／工具。 |
   | 方案 A | `6,000 × 5 = 30,000` 前綴 tokens，`30,000 × 2 / 10⁶ = $0.060000`／筆。正文應寫「五回合累計」。 |
   | 方案 B | Router 前綴 `$0.000045`，90 輸出 tokens 另計 `$0.000045`。一個唯讀 Worker 的前綴 `2,800 × 2 × 0.10 / 10⁶ = $0.000560`。Opus 每次觸發的前綴 `2,800 × 2 × 4 / 10⁶ = $0.022400`，按 20% 攤提為 `$0.004480`。 |
   | 同口徑降幅 | 純前綴成本為 `$0.005085`／筆，對 `$0.060000` 降 **91.525%**，約 **91.53%**。章內 `$0.005130` 與 `91.45%` 的算術成立，但只納入 Router 的輸出。須說明每筆平均一個唯讀 Worker、20% 額外觸發 Opus，以及這是容量假設。若平均兩個等量 Worker，純前綴為 `$0.005645`，降 **90.59%**。 |
   | 離線模擬 | Router `$0.000090`，每個 Worker `(1,200 × 0.10 + 180 × 0.50) / 10⁶ = $0.000210`，模擬 Opus `(2,800 × 4 + 320 × 20) / 10⁶ = $0.017600`。兩筆分別為 `$0.000510`、`$0.018110`。模擬用兩個 Worker，且 Opus 只估一次呼叫，應與方案 B 的假設分開標示。 |
   | 跨章總成本 | 表列 `42,000 / 1,750` 可重算成 `$0.1015`／筆、`$5,075`／日、`$152,250`／月。但若 5 輪各新增 `1,200` 輸入 tokens 並保留歷史，光前綴與歷輪新增輸入就有 `30,000 + 1,200 × (1+2+3+4+5) = 48,000`；若還保留前 4 輪輸出，另有 `3,500` 輸入 tokens，前提是未算進 `1,200`。請在基準表定義裁剪或重用口徑。`$18,000 ÷ 1,500,000 = $0.012`，較表列基準降 **88.18%**。前綴比較本身無法驗證這個月度目標。 |
   | 熔斷、自我檢核 | `$0.050 ÷ $0.005130 = 9.75×`，用純前綴口徑則約 `9.83×`，兩者都可稱約 10 倍。`2 × 200 × 50,000 = 20,000,000` 額外輸入 tokens／日，按 Haiku 低級距、無快取計為 `$2`／日。教材的 `<500ms` 無量測依據，且分流基準 SLO 是 p95 ≤ `2.5s`。 |

5. **P1｜每筆扇出上限不足以支撐尖峰 SLO。** 在 `12 tickets/s` 下，3–4 個 Worker 對應 `36–48` 次 Worker 啟動／秒；若每支都耗滿 4 次模型呼叫，穩態上界為 `144–192` 次 Worker 模型呼叫／秒，另計 Router、仲裁及重試。這是容量情境，實際瞬時 API RPS 取決於各輪時間分布。加入跨工單的全域及租戶並行限制、RPM／token 配額、有限佇列及背壓。用單一單調時鐘期限分配 Router、Worker、仲裁與持久化的剩餘時間。`18s` 硬期限與 p95 ≤ `18s` 應分別追蹤成功、逾時和人工轉介。成本熔斷須在派發前預留最大待完成支出，並區分已知成本與逾時後尚未確認的帳務。

## Code & API Issues

1. **Router 的 wire-level 規格與兩份程式不一致。** 刪除章文要求的 `temperature: 0`，Haiku 5.5 應省略取樣參數，也可省略整個 `tools` 欄位。兩份程式目前只靠提示詞要求 JSON，且直接解析第一個文字區塊。改用 `output_config.format: {type: "json_schema", schema: …}`，再由應用程式驗證 lane、任務白名單、去重、數量、信心範圍與路由必備任務。`strict: true` 放在客戶端工具定義，約束工具輸入。Router 要明確處理 `refusal`、`max_tokens`、空內容、解析失敗及 API 例外。Haiku 預設 adaptive thinking，可用較低 `output_config.effort`，或在支援的 effort 下停用 thinking；`256` 應按完整輸出及 thinking 預算驗證。 [Haiku 5.5 遷移指南](https://platform.claude.com/docs/en/models/haiku-5-5/migration-guide) [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

2. **快取門檻、miss 診斷與 usage 公式都要更正。** 若斷點處的可快取前綴確為 `450` tokens，低於 Haiku 5.5 所需的 `512`，加 `cache_control` 也不會寫入。對已達門檻的前綴，斷點前放唯一 `ticketId` 通常會造成 miss 並建立新快取，兩個 cache 計數同時為零有其他原因。`input_tokens` 只計未快取的輸入，整體快取讀取覆蓋率應用 `read / (input + creation + read)`。若監控靜態前綴的 `80%` 目標，分母應限定符合快取條件的請求或預期靜態前綴 tokens。Python 目前丟掉 cache usage，TS 有傳入。共用計價器也應標明只涵蓋示範條件，若用於生產須處理 Haiku 長輸入級距、混合 TTL、Batch 與資料駐留。 [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) [Haiku 5.5 規格](https://platform.claude.com/docs/en/models/haiku-5-5/overview)

3. **補齊工具迴圈，或把教學明確標為只有 Router 接 API 的模擬。** 目前 `WORKER_MAX_TURNS` 只出現在摘要中，沒有真實 Worker 模型迴圈、工具派發、usage 累計或 Opus 仲裁呼叫，`WorkerHandoff[]` 也未傳給任何 Specialist。實作時保留完整 assistant `content`，包括適用的 thinking 區塊。下一則 `user` 訊息開頭放上所有對應的 `tool_result`，逐一配對 `tool_use_id`，失敗附 `is_error: true`。分別處理 `end_turn`、`tool_use`、截斷、拒絕及達回合上限。若採用支援會暫停的伺服器工具，另處理 `pause_turn`。Streaming 等到完整訊息再由本地驗證並派發工具，對 SSE `error` 事件也要分類，因連線已建立時 HTTP 狀態可能仍是 200。 [工具呼叫](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls) [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) [Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)

4. **取消、重試與錯誤分類需對齊。** TS `withTimeout` 只拒絕外層 Promise，Worker 繼續執行。應傳播取消訊號及 deadline，並記錄逾時前累積 usage。Python `wait_for` 會等待協程取消完成，同步阻塞的後端呼叫也會卡住 event loop。兩份程式都應使用有期限的非阻塞 I/O。章內 TS 片段把所有 rejection 標為 timeout，檔案則靠字串比對；改成明確錯誤型別與終止原因。TS 的 `30ms` 延遲未觸發 `8,000ms` timeout，Python 沒有相同的注入。SDK 預設自身也會重試，若外層控制退避，應明確配置 SDK，避免兩層各 2 次重試變成最多 9 次嘗試。按 `i=0,1` 計算，Full Jitter 的等待上界為 `500 + 1,000 = 1,500ms`，`8,000ms` cap 在這組參數下不會觸及。`Retry-After` 或下一次呼叫超出剩餘期限時應直接降級。 [TypeScript SDK](https://github.com/anthropics/anthropic-sdk-typescript) [Python SDK](https://github.com/anthropics/anthropic-sdk-python)

5. **Agent SDK 的權限與沙盒描述會誤導部署。** `allowedTools` 本身是預先核准清單。應說明其與 `permissionMode: "dontAsk"`、`disallowedTools` 或權限規則的搭配。工作目錄與 Sub-agent context 各自有用途，租戶／行程／檔案系統隔離仍須配置實際沙盒或隔離執行環境。若並列 Python，使用 `allowed_tools`、`permission_mode`。 [Agent SDK permissions](https://code.claude.com/docs/en/agent-sdk/permissions) [Secure deployment](https://code.claude.com/docs/en/agent-sdk/secure-deployment)

6. **MCP 與 Batch 在本章沒有實作可驗證。** 若為跨章預告，應明確區分 MCP Streamable HTTP 傳輸、Claude API MCP Connector，以及 Messages 的 SSE 串流。Connector 支援遠端 Streamable HTTP／SSE 的工具呼叫，本地 STDIO 不能直接接入。Message Batches 的 50% input/output 折扣可用於離線評估或回填；批次最長可到 24 小時，無法用於本章 `18s` 互動式路徑。 [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) [Message Batches](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

## Clarity / Minor Suggestions

- 「30–50 個工具的物理極限」和「常見誤觸寫入」需要量測或改寫為依工具描述重疊度、任務分布而變的風險。`3,000–8,000` 與 `120–180` tokens 建議標為量測值或示意值。四個告警門檻 `2%`、`5%`、`1%`、`0.5%` 應交代分母、視窗和最低樣本數。
- Saga 的類比可保留，但 RPC 一樣可能逾時、重複執行或回傳不確定結果。把 Agent 特有的變異說具體，例如摘要遺漏已退款金額，或將「物流狀態未知」寫成「尚未出貨」。
- `max_revisions = 2` 可表示初稿加最多兩次改寫，最多三次語意評估。把它與每次評估最多兩次傳輸重試分開。若 Evaluator 沒有成功產出結果，人工審核應收到「評估未完成」及最後可用的草稿和違規紀錄。
- 將書中的離線輸出標為 TS 節錄，因 Python 使用 snake_case。退款範例宜顯示可辨識的模擬結果，並加入兩語共用的故障情境，驗證帳務分支缺失、逾時或回傳無效資料時確實進入人工審核。