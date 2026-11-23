## Verdict

`NEEDS_REVISION`

基準表的價格與章內成本算術大致正確。必修問題是預設 token 上限與五輪基準互相矛盾、兩份範例無法履行超時契約，以及退款工具把租戶、金額和冪等鍵交給模型決定。審查以貼出的章稿與原始碼為準，並讀取 repo 內的共用 Mock、成本函式與依賴宣告。使用本機 Python SDK 0.75.0 搭配假回應重現缺單、超時及最後一輪行為。repo 宣告 Python SDK `>=2.11.0`，該版本的實際 API 往返與 TypeScript 型別編譯均未驗證。

## Critical / Factual / Math Issues

1. **五輪基準在第 4 輪就會被預設護欄截斷。** 各輪累計輸入為 `6,000 → 13,200 → 21,600 → 31,200 → 42,000`。`25,000` 上限會在第 4 輪已送出並計費後觸發，此時成本為 `31,200 × $2/MTok + 1,400 × $10/MTok = $0.0764`。請決定 `25,000` 是累計用量上限還是單次上下文上限，並讓設定、欄位名稱與五輪驗收一致。若要宣稱硬預算，發送前需以完整請求估算輸入、預留 `max_tokens` 對應的輸出費用，並把重試納入預算政策。現在的事後檢查只能阻止後續工作。

2. **成本帳本的算術成立，首輪與輸出的定義需補齊。** `2,400 + 3,600 = 6,000`，五輪單次輸入 `6,000 / 7,200 / 8,400 / 9,600 / 10,800` 合計 `42,000`，輸出 `5 × 350 = 1,750`。Sonnet 成本為 `$0.0840 + $0.0175 = $0.1015`，乘以 `50,000` 與 `50,000 × 30 = 1,500,000` 分別為 `$5,075/日`、`$152,250/月`。但首輪已包含工單內容，工具定義也可能引入額外開銷。保留基準表時，請把 `6,000` 明示為簡化帳本的首輪假設，並說明若另有固定首輪工單開銷 `U`，五輪合計需再加 `5U`。`350` 應定義為每輪**計費輸出**的假設，含 thinking。第 5 輪單次 `10,800` 的自我檢核仍成立。 [Tool use 定價](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) · [Sonnet 5.5 遷移指南](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide)

3. **分流算式正確，月成本目標仍需完整模型。** `50,000 × 60% = 30,000`，兩輪為 `13,200` 輸入和 `700` 輸出，Haiku 成本 `$0.00132 + $0.00035 = $0.00167/筆`，即 `$50.10/日`、`$1,503/月`。相較五輪全 Sonnet 基準，降幅 `98.35%`，同時包含輪數減少與模型降價。若剩餘 `40%` 仍按五輪 Sonnet 基準，總額為 `$62,403/月`。要達 `$18,000`，複雜工單的加權成本須降至 `($18,000 − $1,503) ÷ 600,000 = $0.027495/筆`。整體目標為 `$0.012/筆`、降幅 `88.18%`。請把「還需結合 Batch API 才能達標」改為待第 8 章驗證的方案，並交代可批次化的流量占比。Batch 結果可能耗時達 24 小時，且相依的 client-tool turns 須等前一輪結果才能提交。 [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

4. **12 req/s 的容量模型只能當初估。** 日均 `50,000 ÷ 86,400 = 0.5787 req/s`，尖峰是 `20.736×`，可寫「約 21×」。若尖峰每張工單都走五輪，穩態原始負載才是 `12 × 5 = 60 calls/s`。`60 × 1.5 = 90` 的算術正確，但 Little’s Law 使用平均停留時間，不能以單次 p95 推出平均在途量或 socket 上限。請說明 `128` 是壓測起點，並納入路由比例、重試、每程序的連線池與上游 RPM／輸入及輸出 TPM。`maxSockets` 也應替換為各實際 transport 的設定方式。`18,000 ms = 18 s`、`5,000 ms = 5 s`、`86,400 s = 24 h` 均正確。五輪若各耗滿單輪上限就是 `25 s`，還未計工具及排隊，因此整體 deadline 與端到端 p95 要分別驗證。

5. **租戶與金流授權必須由後端掌握。** 兩例都接受模型提供的 `tenant_id`、`order_id`、退款金額和冪等鍵。Mock 又在驗證訂單與租戶前依裸 key 讀取舊結果。請從可信的已驗證工單上下文綁定租戶與資源權限，把工單、檢索內容及工具回傳一律當成不可信資料，在執行器獨立驗證動作、金額、幣別、可退餘額及核准狀態。`strict: true` 只保證受支援 schema 的形狀。兩份 Mock 的上限比較也會讓負數或 `NaN` 落入 `approved`，應先驗證有限、正值的金額，金流使用最小貨幣單位。 [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

6. **Redis 鎖、資料庫唯一鍵和外部金流各有不同的失敗窗口。** `orderops:run:{ticket_id}` 缺租戶範圍，24 小時的鎖與狀態共用 TTL 也使崩潰接管和過期寫入難以定義。請分開租戶範圍的執行狀態與可續租 lease，明定 owner token、原子釋放及 stale worker 防護。退款採後端產生的租戶範圍操作 ID，持久化請求指紋與結果，並在金流端傳遞同一冪等鍵。區分同內容重放與同鍵異參數衝突。對「金流已接受、應用逾時或尚未寫入結果」的情況，要有待對帳狀態及查詢恢復流程。唯讀先跑也無法消除 TOCTOU，寫入端仍須原子驗證前置條件。同輪多筆寫入若可能部分成功，應逐筆持久化結果，或由後端限制每輪可執行的寫入數。

## Code & API Issues

- **超時與 API 例外都未映射成承諾的結果。** TS 的 `finally` 只清 timer，abort 會拋到 `main`。Python 的 `timeout=turn_timeout` 是 HTTP 階段 timeout，SDK 重試可進一步拉長整體時間。本機假回應也確認 `APITimeoutError` 直接外拋。兩例應明確處理 API timeout、429／529、連線錯誤及取消，以單調時鐘與同一個 deadline 涵蓋重試等待、整輪和工具執行。收到回應後、派發工具前仍應檢查剩餘時間。手動測試需分別驗證 `turn_timeout` 與 `wall_clock_timeout`。串流模式只在收到完整成功的訊息後派發工具。 [TypeScript SDK](https://github.com/anthropics/anthropic-sdk-typescript#retries) · [Python SDK](https://github.com/anthropics/anthropic-sdk-python#timeouts)

- **最後一輪可執行退款後才報耗盡。** `maxTurns=1` 收到 `tool_use` 時，兩例都先呼叫工具，最後才回傳 `status=budget_exceeded`、`stopReason=max_turns`。若最後一輪必須保留給模型收尾，應在派發前禁止工具執行。若業務允許最後一輪提交副作用，結果契約須明示已完成哪些動作，讓呼叫端安全恢復。

- **缺單、並行和範例輸出與文字不一致。** 兩份 Mock 都用 `{"error": ...}` 回傳缺單，執行器僅在例外或未知工具時設 `is_error: true`。應將領域失敗正規化成穩定錯誤碼，並區別可重試的技術失敗。TS `map` 和 Python list comprehension 都依回傳順序同步執行，沒有實作「唯讀併行、驗證後寫入」，也不會因前一個唯讀結果失敗而阻止憑同輪參數發出的退款。TS 摘錄對 refusal 回傳 `error`，完整程式回傳 `refused`。Python JSON 使用 `snake_case`。樣本只要求查單與庫存，而且 CLI 只印摘要，因此無法保證或直接看到三工具軌跡。用固定回應測試這些分支，並同步修正摘錄和操作說明。

- **`stop_reason` 圖應明示適用範圍。** 現有四個分支適合作為本章本地工具迴圈的核心子集。完整 API 還有 `stop_sequence`、`pause_turn`、`model_context_window_exceeded`，需分別依自訂停止序列、伺服器工具續跑、截斷處理。串流初始值可為 `null`，HTTP 錯誤走例外路徑，`end_turn` 也應依產品契約檢查是否有可用回覆。現行「原樣保留 assistant blocks，再以緊接的 user message 回送所有本地 `tool_result`，由 ID 配對」方向正確。若加入文字，`tool_result` 須排在前面。Wire JSON 建議標為節錄。 [Stop reasons and fallback](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)

- **補上 Sonnet 5.5 的 thinking 行為與版本邊界。** `claude-sonnet-5-5` 是有效 ID。省略 `thinking` 仍預設 adaptive，`max_tokens: 1024` 含思考與可見輸出，因此需用代表性工單驗證截斷率。完整保留 assistant blocks 的做法正確，含 thinking signature。若示範最低思考設定，Sonnet 5.5 用 `thinking.type: "between_tools"` 並遵守 effort 相容性，`disabled` 會回 400。一般工具使用、`strict: true`、`output_config.format`、`cache_control` 是不同契約。本章可以保留最小本地工具範例，並明示哪些功能留待後章。工具參數的 `String`、`Number`、`str`、`float` 強制轉型應改為實際驗證。 [Sonnet 5.5 遷移指南](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) · [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

- **成本 helper 的適用範圍要與可傳入的模型一致。** 目前固定 Sonnet、無快取的路徑計費正確。公開 `model` 參數卻容許未知模型靜默沿用 Sonnet 價格，且兩份 helper 漏算 Haiku `>100K` 的全請求較高費率。若接上快取，兩例的 token 護欄都要加總一般輸入、寫入和讀取，Python 成本呼叫也須傳入兩類快取用量。混用 TTL 時需依各寫入桶計價。目前無快取的章例可以明確限制支援模型與費率情境，並在 README 或執行步驟補上依賴安裝及已驗證的 SDK 版本。 [Claude API 定價](https://platform.claude.com/docs/en/about-claude/pricing) · [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

- **MCP 與 Batch 的後章前導應保留執行邊界。** Messages MCP Connector 使用 beta `mcp-client-2025-11-20`、`mcp_servers` 和 `tools` 內的 MCP toolset，由服務端連到遠端 MCP 工具，支援 Streamable HTTP 與舊 SSE。Streamable HTTP 本身是 MCP 傳輸協定，POST 回應可為 JSON 或 SSE，和 Claude 回傳 SSE 是兩段不同連線。Batch 以 `custom_id` 配對可能亂序的結果。50% 折扣適用模型輸入與輸出 token，Connector 的 MCP 工具呼叫費率仍與一般 Messages 相同。 [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [MCP transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) · [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

## Clarity / Minor Suggestions

- **可保留的定價與基準。** `12 + 6 = 18`。第一方 API 的 Sonnet `$2/$10`、Opus `$4/$20`、Haiku `$0.10/$0.50` 與 `>100K` 時 `$0.50/$2.50` 均吻合。快取寫入 `1.25×/2×` 對應 `5m/1h`，Sonnet／Opus 讀取 `0.05×`，Haiku `0.10×`。Sonnet Batch `$1/$5` 是標準費率乘 `0.5`。支援模型在適用平台啟用 `inference_geo: "us"` 的 `1.1×` 涵蓋四類 token 費率。 [Claude API 定價](https://platform.claude.com/docs/en/about-claude/pricing)
- 「工作流或 Agent」的判準應聚焦於**下一步決策權在程式還是模型**。確定性 workflow 也可以依觀測結果走分支。「單次 LLM 搭配工具」可限定為先由應用程式取資料再呼叫模型，或註明 client-tool call 若需要模型讀回結果，通常會多一次 Messages 請求。 [Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)
- 自我檢核第 2 題可更精確。迴圈尾端檢查能抓到在該輪內已發生的超時，缺的是第一個呼叫與每次派發前的 deadline 檢查。`Promise.race` 只讓等待方提早返回，底層操作仍須支援取消或對帳。
- `1%`、`turns >= 7`、連續兩次相同工具、`16,000 ms` 持續五分鐘、兩分鐘內 `2%`、`0.5%` 都是政策門檻，應標為初始值並定義分母、最小樣本量及告警持續條件。`16 s` 距 `18 s` 剩 `2 s`，其餘門檻沒有基準數據可推導。正常冪等重放應與異參數衝突分開計數。
- 完整範例清單移除 `__pycache__` 二進位檔，將作者機器的絕對 `file://` 連結換成 repo 相對連結。將「重複扣款」改成退款案例對應的「重複退款」，並為延伸閱讀補上官方直連。