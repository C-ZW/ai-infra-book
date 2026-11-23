## Verdict

**NEEDS_REVISION**

兩版模擬器都重現了 `2/3 passed Pass^3` 與 `$0.2097`。主要阻擋項是裁判請求使用指定模型不支援的 `temperature`、退款案例把「回報已核准」寫成「實際退款」，以及範例在安全案例失敗時仍以 exit code `0` 結束。`78% → 95%` 的調校結果也缺少能對帳的試驗紀錄。

驗證範圍為本機 Python 與 TypeScript 模擬執行、靜態程式碼審查及 Anthropic 官方文件。TypeScript 透過 Node 載入 `tsx` loader 執行，因沙箱阻擋 `tsx` CLI 建立 IPC。完整 `tsc` 型別檢查與 live Claude API 請求未執行。

## Critical / Factual / Math Issues

1. **`78% → 95%` 的錯誤分類無法對帳。** `8 + 7 + 4 + 3 = 22`，如果是全體 100 題中的互斥主因，應標成 8、7、4、3 題。如果分母是 22 題失敗案例，比例應為 36.36%、31.82%、18.18%、13.64%。若四類全部歸零且涵蓋所有失敗，結果應為 100%。請交代剩下五題是殘留失敗還是新回歸，並提供逐版案例數、suite 版本與 Dev／Holdout 結果。若無試驗紀錄，改標「示意」，刪除「實錄」「穩定」和「沒有任何猜測成分」。

2. **補上機率模型的假設，修正 `Pass^k` 的生產解讀。** `p^5` 需要各步在前序成功下的條件成功率都為 `p`，直接乘邊際準確率則需要獨立性。跨 trial 再取 `k` 次方也有相應假設，共用 fixture、模型版本或上游故障都可能造成相關性。觀測指標仍可直接按案例算 `any`／`all`。生產只執行一次時，單次成功率與嚴重錯誤率都應獨立呈現。`Pass^k` 衡量指定重複條件下的穩定度，「唯一能採信」應刪除。30 題 Holdout 每錯一題就變動 3.33 個百分點。`> 5%` 應寫成差距 **> 5 個百分點**，並同時定義 Holdout 絕對門檻及關鍵安全案例閘門，避免兩組同時退化仍通過。 [Anthropic Agent Evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)

3. **退款安全應以後端狀態和交易前置條件判定。** Prompt、工具描述和 `strict: true` 都只適合引導或約束格式。應由後端從可信身分取得 tenant 與授權，驗證同一租戶、訂單、幣別、剩餘可退額及有效人工核准，並在寫入交易內重驗以處理併發退款。重試沿用同一業務操作的冪等鍵，後端以租戶和操作範圍唯一約束並檢查請求內容一致，逾時後先查結算狀態。評測應分別記錄工具嘗試、後端拒絕和實際副作用。工單文字、工具回傳與待評答案都可能帶有注入內容。裁判應無工具權限，且不得覆寫硬性契約結果。

4. **CI 的成本、限流與時間上限需要可執行的定義。** 300 是 Agent trial 數。按五回合基準是約 **1,500 次模型請求，外加最多 300 次裁判請求**，重試另計。`concurrency ≤ 10` 只限制在途量，仍需按 RPM、輸入／輸出 TPM 和共用配額節流。10 個 worker 下，300 個各耗盡 45 秒的 trial 需 **22.5 分鐘**，20 題 Smoke 則需 **90 秒**，兩者都未計額外排程時間。六輪各用 15 秒就已達 90 秒。請把 45 秒做成涵蓋模型、工具、退避及裁判的明確 deadline，並標示「2 分鐘」是目標。`$35` 比基準僅多 **$4.4825**，硬預算要在派工前原子預留在途請求和重試的成本。請把 `70%+` 降本列為待量測，或附 cache 命中、路由比例及品質等價條件。30 次 nightly 約 **$915.53／月**，「數千美元」需附執行頻率。

5. **持久化與隔離設計有缺口。** `(error_category, created_at)` 無法照列出的欄位建在 `eval_trial_results`，因 `created_at` 只在 `eval_runs`。請補 trial 時間欄位或改成分表索引與聯結，並用 `(run_id, case_id, trial_idx)` 唯一約束防止重跑重複入帳。`86,400s = 24h` 只控制 Redis 保存期限。fixture 應不可變且按 suite／fixture 版本定址，可變狀態應在每個 trial 重置或隔離。持久化 trace 前也應遮罩憑證、個資與金流資料。

**數字核算**

| 項目 | 獨立重算 |
|---|---|
| 五回合基準 | 依 ch01／ch03 的記帳，第 1 回合為 6,000 tokens，第 2–5 回合各新增 1,200 個歷史輸入 tokens，合計 `6,000 + 7,200 + 8,400 + 9,600 + 10,800 = 42,000`。輸出 `5 × 350 = 1,750`。若照基準表字面每輪都新增 1,200，輸入會是 48,000。應同步修正表述。 |
| 單位經濟 | `0.084 + 0.0175 = $0.1015／筆`，乘 50,000 及 30 天得 `$5,075／日` 與 `$152,250／月`。50,000 筆／天等於 0.5787 req/s，尖峰 12 req/s 約為 20.736 倍。`$18,000 ÷ 1,500,000 = $0.012／筆`，較基準低 88.18%。 |
| 機率例題 | `0.90^5 / ^10 / ^25` 分別為 **59.05%／34.87%／7.18%**。`0.98` 對應 **90.39%／81.71%／60.35%**，全過率為原來 **8.406 倍**。請直接用 `p^25`，以四捨五入後的 `0.9039` 代入會得到 60.34%。自我檢核 `0.95^6 = 73.51%`、`0.95^18 = 39.72%` 正確。 |
| 全套 CI | `60 + 25 + 15 = 100`，`100 × 3 = 300`。Agent `300 × $0.1015 = $30.45`。按每 trial 一次 Haiku 裁判，`(1,500 × $0.10 + 150 × $0.50) ÷ 10^6 = $0.000225`，合計 `$0.0675`。總額 **$30.5175 → $30.52**。請把 300 次裁判標成全送估算，因正文主張硬性檢查先行。 |
| 模擬器與挑戰題 | `8,400 × $2/MTok + 650 × $10/MTok = $0.0233／trial`。9 次為 **$0.2097**，12 次為 **$0.2796**，增加 33⅓%。固定試驗成本下才會等比例增加。五筆呼叫確實超過上限四筆。 |

## Code & API Issues

1. **裁判請求參數。** Haiku 5.5 和 Sonnet 5.5 都應省略 `temperature`、`top_p`、`top_k`。若保留 adaptive thinking，用 `output_config.effort` 調節，並量測 `max_tokens: 256` 是否足夠。若裁判設計需要關閉 thinking，這兩個模型可明確設 `thinking: {"type":"disabled"}`。用 `output_config.format` 指定 `type: "json_schema"`，並驗證必填的 `score` 與 `reason` 及分數範圍。`refusal` 和 `max_tokens` 都要有獨立處理。`strict: true` 是工具定義層級欄位，只約束工具輸入 schema。18 個工具低於官方 20 個 strict 工具的上限，仍需驗證合併後的 schema 複雜度。 [Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview) · [Sonnet 5.5 遷移指南](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide) · [Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

2. **快取命中與重試要按 wire 行為處理。** 將 `cache_control` 設在固定 system 內容區塊的末端，使動態案例位於 breakpoint 後。指定模型的最低可快取前綴為 512 tokens。1,500 個總輸入 tokens 無法證明固定前綴達門檻。`cache_read_input_tokens = 0` 也可能同時沒有 `cache_creation_input_tokens`。請定義 `0.85` 是合格請求命中比例還是 token 命中比例，並分開冷啟動樣本。`429` 是限流、`529` 是服務過載。遵守 `Retry-After` 與剩餘 deadline，串流收到完整終止事件後才評分或執行工具。兩個 SDK 預設各重試兩次。若外層再重試三次，每個邏輯請求最多送出 **12 次**。請由單一層控制重試並區分基礎設施失敗、無效試驗與模型失敗。 [Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [API Errors](https://platform.claude.com/docs/en/api/errors) · [TS SDK](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/typescript) · [Python SDK](https://platform.claude.com/docs/en/cli-sdks-libraries/sdks/python)

3. **`stop_reason` 與工具配對要分路徑。** 對自管 client tools，`tool_use` 是正常的中間回應。應檢查下一則 user message 開頭包含該回合所有對應的 `tool_result`，逐一比對 ID 並驗證錯誤處理。`end_turn` 應用於預期自然完成的終局。另行分類 `max_tokens`、`refusal` 和適用時的 `pause_turn`。本章沒有實作 MCP 或 Batch。若補充交界說明，Claude MCP Connector 支援遠端 Streamable HTTP／SSE，回應使用 `mcp_tool_use`／`mcp_tool_result`。Message Batches 按獨立 Messages 請求非同步處理，適合裁判或單步評測。多輪 Agent 的後續請求仍依賴工具結果，需由外部協調。表列 Batch 50% 與 Sonnet `$1/$5` 正確。 [Tool Implementation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) · [MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [Message Batches](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

4. **兩版範例都沒有測到正文宣稱的退款失敗。** `EVAL-003` 第三次只將 `refundStatus` 設成 `approved`，沒有呼叫 `issue_refund`。前兩次反而有嘗試退款，因 `$2,500 > $1,850` 才被 mock 拒絕。三個案例的 `forbiddenTools` 都是空陣列。請把目前的失敗寫成「誤報退款核准」，或加入確實會測到政策攔截的案例，分別斷言報告、嘗試及落帳狀態。TS 註解的「10%」應更正為固定第三次失敗，本次該案例的失敗比例為 1/3。 [TS 模擬器](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/ts/ch07/index.ts:147) · [Python 模擬器](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/py/ch07/main.py:97)

5. **評測器和 CI 閘門尚未兌現教學契約。** 兩版 Code Grader 只檢查狀態和訂單 ID 子字串。Trace 缺少足以驗證工具結果、租戶、冪等性及實際提交的資料，`indexOf` 也只能證明第一個同名查詢出現在第一個退款前。應對每次退款核對同訂單、同租戶的成功前置結果，並分開計數模型回合與工具呼叫。兩版裁判只是字數 stub，仍會在硬檢查失敗後執行。若只有裁判失敗，兩版都標成 `none`，TS 甚至回報 `All graders passed`。請標明 stub、短路硬失敗、補上原因與分類，並讓 gate 透過非零 exit code 或 CI 可讀狀態阻斷。挑戰題還應補上分類聚合，目前程式只印每題最後一次失敗的類別。 [TS 評測器](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/ts/ch07/index.ts:125) · [Python 評測器](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/py/ch07/main.py:81)

## Clarity / Minor Suggestions

- 精確比對仍適合 enum、固定 ID、正規化欄位與 API 契約。把開場範圍縮到「自由文字與多條合法工具路徑」。單次試驗也有觀測價值，只是無法估計同題重跑的穩定度。
- 將 `30–50` 筆錨點、`90%` 一致率、`κ ≥ 0.80`、每週抽檢 `20–50` 筆、`429 > 2%` 及 `0.85` 命中門檻標成起始設定。對 1–5 的有序評分可用加權 κ，並交代一致率是逐分還是依通過門檻計算，以及如何抽樣高風險案例。
- 章內 `computePassKMetrics` 與完整 TS 實作一致。`gradeTrajectory` 片段省略必要及禁止工具檢查，應明標節錄。輸出中的 `3` 可從 `k` 產生，`lastError` 可改成 `lastFailureCategory`，讓讀者知道它保留的是最近一次失敗。