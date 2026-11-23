# Verification & Adjudication Log (P4)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 首輪基準輸入（System Prompt + 18 工具 Schema + 首輪工單）= 6,000 tokens。
verifier value: 固定前綴為 6,000 tokens；若首輪工單另占 U tokens，首輪輸入為 6,000 + U，五輪累計輸入為 42,000 + 5U。  flagging family: openai (incorrect)
arbiter: agrees=true — 基準資料將 6,000 tokens 全部分配給 System Prompt 的 2,400 tokens 與工具 Schema 的 3,600 tokens，因此沒有剩餘空間計入非零的首輪工單內容。若首輪工單另占 U tokens，且後續每輪都重送，五輪累計輸入應為 42,000 + 5U tokens；章內雖有提及此調整，卻仍把工單內容納入 6,000 tokens 的定義。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 把 wallClockTimeoutMs 檢查放在 while 迴圈結尾，會導致即使上一輪剛結束時已超時，仍會多發起一次無效的 API 呼叫才中斷。
verifier value: 結尾檢查可攔截正常走到該檢查點後的下一輪，但仍應在首次呼叫前及派發工具前檢查剩餘時間，並為 API 與工具呼叫設置可執行的超時機制。  flagging family: openai (incorrect)
arbiter: agrees=true — 若檢查確實位於每次迴圈的結尾，上一輪工作完成後會先檢查時間；若此時已超時，便可在進入下一輪及發出下一次 API 呼叫前中斷。實際行為仍取決於檢查相對於 continue、工具派發和其他分支的位置；只在結尾檢查也無法即時中止卡住的呼叫。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: Sonnet 5.5 預設啟用 adaptive thinking。
verifier value: Sonnet 5.5 是否預設啟用 adaptive thinking，須以該模型的相關文件或可驗證的實際行為確認。  flagging family: openai (imprecise)
arbiter: agrees=true — 所附證據指出較新模型可使用 adaptive reasoning modes，但未說明 Sonnet 5.5 是否預設啟用，也未提供支持此預設行為的材料。因此無法僅憑提供的證據確認這項主張。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 可續租的短暫 lease 含 owner token 與原子釋放，可防範 stale worker 覆寫。
verifier value: owner token 與原子釋放可保護鎖的釋放；防範 stale worker 寫入還需要寫入端執行版本檢查、fencing 或等效的原子條件驗證。  flagging family: openai (imprecise)
arbiter: agrees=true — owner token 搭配原子釋放可避免舊持有者誤刪新持有者的鎖；但舊 worker 在 lease 過期後仍可能繼續執行，單靠這些措施不能阻止它寫入外部狀態。要防止過期持有者覆寫，還需讓受保護的寫入端驗證有效的版本或 fencing token 等條件。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 尖峰流量：12 req/s（日均 0.5787 req/s，尖峰約 21×）
verifier value: 約 20.7×（基準表記為 20×；建議改寫為「約 20.7×」或統一沿用基準的 20×）  flagging family: anthropic (imprecise)
arbiter: agrees=true — 日均流量 50,000 / 86,400 = 0.5787 req/s，所以 12 / 0.5787 ≈ 20.7 倍。章節寫「約 21×」，算術上比較接近實際值。但基準表寫的是「平均 0.58 req/s，尖峰 20×」，章節寫法與基準不一致，全書應統一用語。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: Sonnet 5.5 預設啟用 adaptive thinking，max_tokens: 1024 同時涵蓋思考與可見輸出
verifier value: 限定說法：若啟用 extended/adaptive thinking，max_tokens 須涵蓋思考與最終輸出；Sonnet 5.5 是否預設啟用需查官方文件  flagging family: anthropic (imprecise)
arbiter: agrees=true — 提供的史料只說 extended thinking 以 budget_tokens 啟用，「或新模型有 adaptive 模式」，並要求 max_tokens 大於 budget_tokens。史料沒有說 Sonnet 5.5 預設啟用 adaptive thinking，所以這一點無法從提供的證據判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 多個 tool_use 的 tool_result 若未在同一則 user 訊息中完整回填，API 會回傳 400 invalid_request_error
verifier value: 需另行對照 Tool Use 官方文件確認錯誤行為  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 沒有記載 tool_result 的配對規則，也沒有記載對應的錯誤碼，閉卷無法確認。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 五回合基準（30,000 / 42,000 = 71.43%）在全輸入占比上本就低於 80%。
verifier value: 冷啟動且後四回合全命中時，快取讀取占總輸入 24,000 / 42,000 = 57.14%；五回合皆讀取既有快取時為 71.43%。  flagging family: openai (incorrect)
arbiter: agrees=true — 五回合各含 6,000 tokens 固定前綴，合計 30,000 tokens，佔總輸入 42,000 tokens 的 71.43%；但這是前綴占比，不是快取讀取占比。若第一回合建立快取、後四回合均命中，快取讀取量為 4 × 6,000 = 24,000 tokens。若第一回合已命中先前建立的快取，才可能達到 30,000 tokens 的讀取量。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 提交時後端必須驗證綁定 (tenant_id, actor, operation, amount_usd) 的短效預檢紀錄，防止模型在預檢後篡改金額與訂單。
verifier value: 預檢紀錄應綁定經驗證的租戶、操作者、操作類型、訂單或原始付款識別碼、金額及其他會影響授權或政策判斷的必要參數；提交時比對並重新驗證政策與可退餘額。  flagging family: openai (incorrect)
arbiter: agrees=true — 所列綁定欄位包含金額，卻沒有訂單、原始付款或其他能唯一識別退款目標的欄位。兩筆訂單若租戶、操作者、操作類型與金額相同，僅比較這些欄位無法識別提交時更換訂單。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 需注意 strict: true 不支援遞迴 Schema、patternProperties 或 minLength。
verifier value: strict: true 對支援的 JSON Schema 子集提供結構約束；遞迴 Schema、patternProperties 與 minLength 的支援情況須依相應版本的官方文件核對。  flagging family: openai (imprecise)
arbiter: agrees=true — 所附證據只支持 strict tool use 會強制工具名稱與輸入符合支援的 schema，未列出這三項限制，因此無法從提供的材料確認各項限制是否成立。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 若需降低工具間前置推理延遲，可使用 thinking: {"type": "between_tools"}（Sonnet 5.5 設為 disabled 會回傳 400）。
verifier value: 應依所使用模型與 API 版本的官方文件確認支援的 thinking 設定及錯誤行為，並以實測比較延遲。  flagging family: openai (imprecise)
arbiter: agrees=true — 所附證據提到 enabled 與較新模型的 adaptive reasoning，並未記載 between_tools 模式、其延遲效果，或 Sonnet 5.5 對 disabled 的回應，因此無法獨立確認這些具體主張。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: Streamable HTTP（Stateless 模式）必須依序完成 initialize、notifications/initialized，再執行 tools/list 或 tools/call；通知回傳空本文 202。
verifier value: Streamable HTTP 可用於遠端 MCP；無狀態模式的生命週期與 HTTP 回應細節須對照指定版本的 MCP 規範。  flagging family: openai (imprecise)
arbiter: agrees=true — 所附證據支持 Streamable HTTP 與無狀態水平擴展的概述，但沒有提供初始化順序、通知回應狀態碼或其在無狀態模式下的具體要求，無法據此判定這些細節。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 完整可執行程式碼已建置於 examples/ts/ch02/index.ts 與 examples/py/ch02/main.py。
verifier value: 須檢視完整程式碼並在適當環境執行，才能確認其存在、內容及可執行性。  flagging family: openai (imprecise)
arbiter: agrees=true — 材料只提供檔案路徑、片段與預期輸出，沒有提供兩份完整程式碼或執行結果，無法確認檔案存在、可執行，或實作了所列元件與驗證流程。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: strict: true 不支援遞迴 Schema、patternProperties 或 minLength
verifier value: 改為限定說法：strict 只支援 JSON Schema 子集，實際支援的關鍵字請以官方文件為準  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只寫到 strict: true 會在解碼階段強制工具名稱與輸入符合 Schema，沒有列出不支援的關鍵字。這項限制清單無法從提供的材料判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: Sonnet 5.5 預設 adaptive thinking；可使用 thinking: {"type": "between_tools"}；Sonnet 5.5 設為 disabled 會回傳 400
verifier value: 保留「多回合工具迴圈須原樣回傳帶簽章的 thinking blocks」；between_tools 與 disabled 回 400 的說法需要外部官方文件佐證  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只記載 thinking: { type: "enabled", budget_tokens: N }，以及「較新模型有 adaptive 模式」。它沒有說 Sonnet 5.5 預設啟用 adaptive，沒有 between_tools 型別，也沒有 disabled 會回 400 的規則。這些細節都缺乏證據。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: stop_reason 包含 "refusal"、"pause_turn"、"model_context_window_exceeded"
verifier value: 需要查官方文件；可改為「處理所有已記載的 stop_reason，未知值一律轉人工」  flagging family: anthropic (imprecise)
arbiter: agrees=true — 提供的 source-evidence 沒有列出 stop_reason 的枚舉值，這幾個值的存在與語意無法從材料判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 錯誤範例的政策上限為 max_allowed_usd: 50，邊界測試卻寫金額超過 $100 才回傳 would_approve: false / pending_hitl
verifier value: 統一門檻數值，或明確說明 $50 與 $100 分別代表的政策層級  flagging family: anthropic (imprecise)
arbiter: agrees=true — 同一章對退款上限給了兩個不同數值，而範例 $45 退款在兩者之下都會通過，因此看不出哪個才是實際門檻。這兩個值可能分屬不同層級（自動核准上限與 HITL 門檻），但章內沒有說明。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: 前綴需達模型最低門檻（Sonnet 5.5 為 512 tokens）。
verifier value: Sonnet 5.5 的最低可快取前綴門檻須以該模型的官方文件另行確認。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 將 512 tokens 指給較新的旗艦模型並以 Opus 5.5 為例；其 1,024 tokens 項列舉 Sonnet 5 及較早版本，但沒有明確列出 Sonnet 5.5。因此，現有材料既不足以確認章節的 512，也不足以推定 Sonnet 5.5 必為 1,024。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: 只要前綴字元完全一致，就能命中快取。
verifier value: 前綴一致且符合最低門檻，並已有尚未到期的對應快取項目時，才可能命中；冷啟動與並發建立期間仍可能未命中。  flagging family: openai (incorrect)
arbiter: agrees=true — 前綴相同是比對條件，但不保證已存在可用的快取項目。章節本身也指出冷啟動、TTL 到期，以及首次回應開始前的並發請求可能造成未命中；低於模型最低門檻的前綴亦可能不建立快取。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: claude-sonnet-5-5 預設使用自適應思考，並透過 output_config.effort 調整深度。
verifier value: 須另行核對 Sonnet 5.5 的模型文件，確認預設思考模式與 effort 的適用方式。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 支持較新模型可能具備自適應推理模式，但沒有確認 Sonnet 5.5 的預設模式，也沒有說明該模型的 effort 設定。因此無法從提供的材料判定這些特定細節。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: 使用 XML 標籤能降低模型把工單內文誤認為系統指令的風險。
verifier value: 可用 XML 標籤和可靠序列化標示不可信資料；實際防護效果應透過提示注入評測驗證，並配合應用層權限控制。  flagging family: openai (imprecise)
arbiter: agrees=true — XML 標籤與 escaping 能在表示形式上區分資料區塊，但提供的材料沒有比較實驗或其他證據，足以判定其降低誤認風險的效果或幅度。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: 前綴需達模型最低門檻（Sonnet 5.5 為 512 tokens）
verifier value: Sonnet 5.5 的最低可快取門檻在提供的證據中未載明（可能是 512 或 1,024 tokens，需查官方文件確認）；OrderOps 的 3,600 與 6,000 tokens 前綴不論哪個門檻都超過。  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只說 512 tokens 適用於較新的 Claude 5 / 5.5 旗艦模型，括號中的例子是 claude-opus-5-5；標準 Sonnet 系列（claude-sonnet-5、Sonnet 4.5/4.6）是 1,024 tokens。證據沒有直接寫出 Sonnet 5.5 的門檻，還註明部署前要逐模型核對。所以「Sonnet 5.5 為 512」缺乏證
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: 最多支援 4 個斷點、向前回看 20 個 blocks
verifier value: unknown（需查官方 Prompt Caching 文件）  flagging family: anthropic (imprecise)
arbiter: agrees=true — 基準資料和 source-evidence 都沒有提到斷點數量上限或回看 block 數，無法從提供的證據判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: claude-sonnet-5-5 預設使用自適應思考（thinking: { type: "adaptive" }，並透過 output_config.effort 調整深度）
verifier value: 較新模型可能支援自適應推理模式；Sonnet 5.5 是否預設 adaptive、是否有 output_config.effort 參數，提供的證據中都未知  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只寫到「或較新模型上的自適應推理模式」，沒有說 Sonnet 5.5 預設採用 adaptive，也沒有提到 output_config.effort 參數。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: Context Rot：模型在長上下文中段的資訊檢索準確率會明顯下滑
verifier value: 應限定為「可能下滑，需以評測驗證」，並補上來源  flagging family: anthropic (imprecise)
arbiter: agrees=true — 提供的基準資料與 source-evidence 都不包含這項實證；章節也沒有給出量化數據或來源。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 系統必須對政策型回答執行確定性 Citation 驗證，明確攔截漏引、格式錯誤與無法解析的引用。
verifier value: 此函式只能檢查至少存在一個可辨識引用，且所有可辨識引用均在檢索結果清單中；須另行驗證完整輸出格式、逐項主張的引用及引用與主張的對應關係。  flagging family: openai (incorrect)
arbiter: agrees=true — 程式只擷取符合正規表示式的引用，再檢查擷取結果是否在允許清單。若回答同時含有合法的 [POL-RET-APAC#4.2] 和格式錯誤的 [POL-FAKE#abc]，後者不會被擷取；只要前者在允許清單，函式便回傳 valid: true。它也沒有逐一檢查政策主張是否有引用，或引用內容是否支持主張。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 模型會看到工具已經執行完畢並取得結果，不會重新發起同一筆工具呼叫。
verifier value: 保留工具結果有助於模型續跑；不得依賴模型自行避免重複呼叫。寫入操作須由應用層以穩定業務操作 ID、操作紀錄與下游冪等或對帳機制防止重複生效。  flagging family: openai (incorrect)
arbiter: agrees=true — 保存並重送工具結果能讓模型看到先前結果，但歷史上下文不能保證隨機推理的模型不再提出相同業務操作。CAS 可防止特定狀態的併發推進，但不能單獨阻止後續回合再次提出退款；還需由執行層核對操作紀錄並依賴下游冪等性或對帳。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 到期排程器與正常喚醒競爭同一狀態轉移，將狀態轉為 expired 並發送超時通知給值班主管，避免超時通知與退款同時成立。
verifier value: CAS 可限制同一版本的到期與喚醒競爭只有一方成功；通知與退款的互斥仍須透過完整狀態機、操作紀錄及可靠派送和冪等機制確保。  flagging family: openai (imprecise)
arbiter: agrees=true — 在兩者以相同狀態及版本進行條件更新時，CAS 可以使其中一個狀態轉移勝出；但狀態轉移、通知傳送與外部退款並非僅憑該條件更新就能原子化。材料沒有完整定義退款授權時點、通知派送及失敗重試與後續狀態的約束，因此不足以推出通知與退款在所有情況下互斥。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 資料庫 WAL 假設重放（Replay）是確定性的，但 LLM 推理具備隨機性。
verifier value: WAL 恢復依賴已記錄的資料庫變更與恢復規則；重新執行 LLM 推理及外部工具則需要另行處理非確定性與副作用。  flagging family: openai (imprecise)
arbiter: agrees=true — 章節未定義此處的重放是資料庫重做已記錄的變更，還是重新執行原始應用程式與外部工具。由資料庫可利用日誌恢復，不能推出重新執行任意應用邏輯或外部操作必然得到相同結果。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: Anthropic 原生 Citations 不可與 output_config.format 同時使用，否則回傳 400。
verifier value: 所提供證據不足以判定兩者是否互斥及其錯誤碼；需核對相應版本的官方文件或實測。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 支持 output_config.format 與 strict tool use 的概述，但沒有記錄原生 Citations 與該格式設定的相容性或錯誤碼，無法據此獨立確認此細節。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 上線時只需將 SQLiteSessionStore 替換為 PostgreSQL 連線池並開啟 RLS 策略，即可無縫銜接多節點部署。
verifier value: 遷移至多節點部署還須實作並驗證租戶身分傳遞、交易與併發控制、外部操作冪等、事件去重及故障恢復等機制。  flagging family: openai (incorrect)
arbiter: agrees=true — 章內自身還要求交易內設定已驗證的租戶身分、使用受 RLS 約束的連線角色、以狀態與版本進行原子 CAS，以及處理工具操作紀錄、冪等、Webhook 去重與逾時競爭。僅替換連線池和開啟 RLS，無法推導這些跨節點契約均已成立；材料亦未提供範例實作內容以證明其餘部分已具備。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: RRF（Cormack et al., 2009，k = 60）只看 1-based 名次不看絕對分數。
verifier value: 依章內公式，RRF 分數只取決於各路名次；作者與年份須另查原始文獻。  flagging family: openai (imprecise)
arbiter: agrees=true — 章內給出的公式確實只使用兩路結果的名次，未出現時貢獻為零；但所附資料未提供論文內容或出版資訊，不能據此核實作者與年份的歷史歸屬。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 範例輸出：Retrieved chunks input cost 0.003600；Single Agentic RAG turn cost incl. 350 output tokens 0.007100
verifier value: 建議改標為「檢索片段輸入 + 350 輸出 tokens 成本 $0.0071（不含前綴、其他輸入與歷史）」  flagging family: anthropic (imprecise)
arbiter: agrees=true — 1,800 × $2/MTok = $0.0036；350 × $10/MTok = $0.0035，合計 $0.0071，數字算得對。但「Single Agentic RAG turn cost」只算了檢索片段輸入和輸出，沒有包含 6,000 tokens 前綴（快取讀取時為 6,000 × $0.10/MTok = $0.0006）、每回合 1,200 tokens 新增輸入，也沒有包含歷史重
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: RRF（Cormack et al., 2009，k = 60）；延伸閱讀稱其為「無參數排名融合演算法」
verifier value: 改為「只需單一平滑常數 k（常用 60）、無須分數正規化的排名融合方法」，文獻出處須另行查核  flagging family: anthropic (imprecise)
arbiter: agrees=true — 提供的 source-evidence 沒有這項文獻出處與年份，閉卷無法查證，所以標為 imprecise。另外，章內明寫了常數 k = 60，又說 RRF「無參數」，前後不一致。比較準確的說法是：RRF 不需要訓練或分數正規化，但有一個平滑常數 k。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: Anthropic 原生 Citations 不可與 output_config.format 同時使用，否則回傳 400；stop_reason 包含 model_context_window_exceeded
verifier value: 須依官方 API 文件查證後再保留，或加註「依撰寫時文件」  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只記錄了 output_config.format 與 strict: true，沒有提到 Citations 與結構化輸出不相容、會回傳 400，也沒有列出 model_context_window_exceeded 這個 stop_reason。依提供的證據無法判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: pgvector 近似索引（HNSW/IVFFlat）預設可能先掃描候選再套用 WHERE 過濾，導致有效結果少於 K
verifier value: 須對照 pgvector 官方文件確認，包括 iterative scan 選項的版本需求  flagging family: anthropic (imprecise)
arbiter: agrees=true — 這項主張在技術上合理，但提供的基準資料與 source-evidence 都沒有涵蓋 pgvector 的行為，閉卷無法確認。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: Haiku 5.5 的最小快取門檻為 512 tokens；低於門檻時快取會靜默不寫入。
verifier value: Haiku 5.5 的最小快取門檻須依該模型的官方文件另行確認；450 tokens 是否可快取，在所給材料中無法判定。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 將 512 tokens 列為 Opus 5.5 的門檻，也列出部分其他模型的門檻，但沒有提供 Haiku 5.5 的門檻。因此無法由所給證據推得 Haiku 5.5 是 512 tokens，也不能據此判斷章內 450-token Router 前綴是否低於該模型門檻。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: 對 529 採用指數退避加 Full Jitter，base = 500ms、cap = 8,000ms、max_retries = 2，此參數下等待上界為 1,000ms。
verifier value: 明訂退避公式；若第 1、2 次重試分別採 0–500ms、0–1,000ms，則單次上界為 1,000ms，兩次合計上界為 1,500ms。  flagging family: openai (imprecise)
arbiter: agrees=true — 章節未定義重試次數的指數從 0 還是 1 起算，也未說明上界指單次等待或所有等待加總。若兩次重試的 Full Jitter 範圍分別為 0–500ms 與 0–1,000ms，則單次等待上界為 1,000ms，累計等待上界則為 1,500ms。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: 例外應映射為安全錯誤碼；範例將 Worker 失敗轉成交接物件。
verifier value: 將例外分類成固定的安全錯誤碼與通用摘要，詳細錯誤僅寫入受控日誌。  flagging family: openai (incorrect)
arbiter: agrees=true — 範例的 summary 使用 `Worker failed: ${String(res.reason)}`，把原始例外轉成字串交給父層，並未映射為安全錯誤碼；原始例外也可能含有不適合交接的內部資訊。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: Worker 失敗時，範例交接物件設置 latencyMs: WORKER_TIMEOUT_MS、costUsd: 0。
verifier value: 使用實際量測的延遲與已知累計費用；對未確認的費用另標示未知或待對帳。  flagging family: openai (incorrect)
arbiter: agrees=true — 一般例外可能在逾時之前發生，因此固定填入 8,000ms 不一定是實際延遲；Worker 也可能在失敗或逾時前已產生 API 費用，填零會把未知或已發生成本誤報為零。這與章內區分已知成本及尚未確認帳務的要求不一致。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: 傳統 Saga 的每個步驟都是確定性 RPC，輸入與輸出 schema 嚴格固定。
verifier value: 傳統 Saga 可使用命令、RPC 或事件協調本地交易與補償；步驟通常採明確契約，但不必然是確定性 RPC。  flagging family: openai (incorrect)
arbiter: agrees=true — Saga 是將跨服務工作分解為一連串本地交易及補償的協作模式；章內前提並未要求步驟必須使用 RPC，也不能由使用 RPC 推出結果必定確定。Saga 步驟可透過事件或訊息觸發，並可能依外部狀態產生不同結果。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: Haiku 5.5 的最小快取門檻為 512 tokens
verifier value: Haiku 5.5 的門檻在提供的證據中未記載（unknown），部署前應查官方文件逐模型確認  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只寫 512 tokens 適用於「newer Claude 5 / 5.5 flagship models (claude-opus-5-5)」，Sonnet 為 1,024，舊版 Haiku 4.5 為 4,096，並且要求逐一模型查證。Haiku 5.5 的門檻在提供的證據中沒有記載，章節把 512 套用到 Haiku 5.5 缺乏依據。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: SDK 內建重試加上外層重試，「2 次 × 2 次會膨脹成最多 9 次嘗試」
verifier value: 內外層各「1 次初始 + 2 次重試」= 3 × 3 = 最多 9 次嘗試（SDK 預設值需另行查證）  flagging family: anthropic (imprecise)
arbiter: agrees=true — 若內外層各重試 2 次，每層各有 3 次嘗試，(1+2) × (1+2) = 9，結論成立。但原文寫「2 次 × 2 次」，讀起來像 4，容易誤解。此外，SDK 預設重試次數不在提供的證據中。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: Full Jitter（base = 500ms、cap = 8,000ms、max_retries = 2），此參數下等待上界為 1,000ms
verifier value: 單次等待上界 1,000ms（n 從 0 起算），累計等待上界 1,500ms；應明示公式  flagging family: anthropic (imprecise)
arbiter: agrees=true — 以 sleep = random(0, min(cap, base × 2^n)) 計算，n 從 0 起算時，兩次等待的上界分別為 500ms 與 1,000ms。所以 1,000ms 只是單次等待的最大值，累計等待上界是 1,500ms。若 n 從 1 起算，則為 1,000ms 與 2,000ms，累計 3,000ms。章節沒有說明指數起點，也沒區分單次與累計。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: Haiku 5.5 呼叫應省略 temperature；Agent SDK 可搭配 permissionMode: "dontAsk"
verifier value: 需以官方 API / Agent SDK 文件查證；提供的證據只支持 allowedTools / disallowedTools  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只提到 Agent SDK 的 allowedTools / disallowedTools 權限控制，沒有關於 Haiku 5.5 取樣參數限制的記載，也沒有 permissionMode 或 "dontAsk" 這個值。無法用提供的材料判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: 離線模擬輸出 totalCostUsd：TKT-5001 為 0.00051、TKT-5002 為 0.01811；WorkerHandoff 約 120–180 tokens
verifier value: 無法從提供材料驗證（unknown），需實際執行範例或列出模擬用 token 數  flagging family: anthropic (imprecise)
arbiter: agrees=true — 這些數值取決於範例程式碼的模擬 token 數與輸出量，材料中沒有提供，無法重算。章節也自承情境與容量假設不同（2 個 Worker、1 次 Opus）。120–180 tokens 同樣沒有計算依據。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: 確保系統在任何節點重啟或外部異常下，都不重複退款、不遺失進度。
verifier value: 在持久化與供應商冪等或查單等條件成立時降低重複退款與進度遺失的風險；結果不明且無法安全確認時，暫停自動重送並進行人工對帳。  flagging family: openai (incorrect)
arbiter: agrees=true — 章內本身指出，外部金流可能已入帳而本地回執尚未落盤；本地唯一約束無法涵蓋這個窗口。若供應商的冪等有效期已過，且無法可靠查詢交易狀態，系統不能僅靠所列機制保證安全重送或自動完成對帳。持久化、備援與資料遺失情境亦未完整定義，因而不能推出對任何外部異常均不遺失進度。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: Full Jitter 把重試時間均勻打散在 [0, expCap] 區間內，在數百個並發 Worker 同時退避時能有效消除尖峰碰撞。
verifier value: Full Jitter 可降低重試同步與碰撞，但不能保證消除；共同 retry-after 可能造成醒來時間集中，仍需限流或在下限之後進一步分散放行。  flagging family: openai (incorrect)
arbiter: agrees=true — 隨機退避可以降低請求同時重試的機率，但有限時間區間內多個請求仍可能碰撞。此外章內實際延遲取 max(fullJitter, retryAfter)：若多個請求收到相同 retry-after，所有小於該值的抽樣都會集中在同一時間醒來，並非均勻分布；後續限流可再抑制同時放行。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: Batch API 的 processing_status 依序為 in_progress → ended／canceling／canceled；expired 子請求在 24 小時到期。
verifier value: Batch API 為非同步且依所附證據享 50% 折扣；狀態名稱、轉移與到期規則須以對應版本的官方文件另行查證。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 支持 Batch API 非同步處理及輸入、輸出各半價，但沒有列出批次狀態列舉、狀態轉移或到期時間，因此無法據此核定這些具體 API 細節。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: Sonnet 5.5 預設 adaptive thinking（between_tools 可停用前置 thinking，disabled 與舊式 enabled 會被拒絕）。
verifier value: Replay 須保留同一工具回合要求回傳的 thinking 區塊與簽章；Sonnet 5.5 的預設及支援設定須另查該模型的官方文件。  flagging family: openai (imprecise)
arbiter: agrees=true — 所附證據只說明較新模型可能有 adaptive reasoning，並描述舊式 enabled 的一般用法與工具回合中的 thinking 保留要求；沒有提供 Sonnet 5.5 的預設模式、between_tools 語意或兩種設定會被拒絕的證據。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: 兩個版本的範例首次執行記錄 3 筆 Checkpoint，核准續跑後累積 6 筆，且不重複呼叫 LLM。
verifier value: 這是章節列出的預期結果；是否實際成立須核讀完整程式或執行驗證。  flagging family: openai (imprecise)
arbiter: agrees=true — 章節給出預期輸出及部分程式片段，但未提供完整的 TypeScript、Python 實作與實際執行結果。依所附片段無法獨立重建完整事件序列，也無法確認兩個版本續跑時都不重複呼叫 LLM。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: Sonnet 5.5 預設 adaptive thinking（between_tools 可停用前置 thinking，disabled 與舊式 enabled 會被拒絕）
verifier value: 需要查官方文件確認；在確認前，建議改成「新模型可能支援 adaptive reasoning，具體參數以官方文件為準」  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只寫了 thinking 透過 `thinking: { type: "enabled", budget_tokens: N }` 啟用，或在較新模型上使用 adaptive 模式。它沒有說 Sonnet 5.5 預設採用 adaptive，沒有提到 `between_tools` 選項，也沒有說 `enabled`／`disabled` 會被拒絕；「enabled
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: Batch custom_id 須符合 ^[a-zA-Z0-9_-]{1,64}$；expired 為 24 小時到期；processing_status 狀態為 in_progress／ended／canceling／canceled
verifier value: 需要外部官方文件查證  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只提到 Batch API 打五折和非同步處理，沒有 custom_id 格式、24 小時到期或狀態列舉的內容。這些細節無法從提供的材料判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: 429／529 回應標頭與主體（retry-after、anthropic-ratelimit-* 標頭、overloaded_error 主體格式）及 stop_reason 列舉值
verifier value: 需要外部官方文件查證  flagging family: anthropic (imprecise)
arbiter: agrees=true — 提供的基準資料和 source-evidence 都沒有涵蓋 rate limit 標頭名稱、錯誤主體格式或 stop_reason 列舉，無法依材料判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 相同輸入必然產生相同輸出與副作用，單次執行通過即代表系統穩定。
verifier value: 對可控制且具確定性的測試條件，精確斷言能有效驗證指定行為；系統穩定性仍須依測試覆蓋、重複執行與實際運行資料評估。  flagging family: openai (incorrect)
arbiter: agrees=true — 傳統後端可能受並發、時間、隨機性、外部服務與資料庫狀態影響。即使某次測試的輸入和環境固定，單次通過也只能證明該次觀測結果符合斷言，不能證明所有輸入與執行條件下都穩定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 對 Haiku 5.5 與 Sonnet 5.5，固定前綴須達模型最低可快取門檻 512 tokens。
verifier value: 應分別確認 Haiku 5.5 與 Sonnet 5.5 的最低快取門檻，並以實際 cache creation 和 read 用量驗證。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的史料證據只明列 Opus 5.5 為 512 tokens，並列出標準 Sonnet 系列的部分其他型號為 1,024 tokens；並未給出 Haiku 5.5 或 Sonnet 5.5 各自的明確門檻。因此無法根據材料推定兩者都是 512 tokens。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 對每次退款操作，核對同訂單、同租戶的成功 get_order 前置結果出現在該次 issue_refund 之前。
verifier value: 逐筆檢查 issue_refund，確認其前有對同一租戶及訂單成功完成的 get_order，並依需求驗證查詢結果是否仍然有效。  flagging family: openai (incorrect)
arbiter: agrees=true — 章內程式片段只用 indexOf 比較第一個 get_order 與第一個 issue_refund 的位置。它沒有檢查查詢是否成功、租戶或訂單是否相同，也沒有逐筆核對後續退款；因此不能實現前述軌跡規則。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 新增案例後，總評測成本會從 $0.2097 等比例增加至 $0.2796。
verifier value: 若新增三次試驗的平均成本與原九次完全相同，估計總成本為 $0.2796；否則須按新增試驗的實際用量重算。  flagging family: openai (imprecise)
arbiter: agrees=true — 12／9＝4／3，而 $0.2097×4／3＝$0.2796，算術正確。但新增案例含五次工具呼叫，材料未提供其實際 token、裁判及工具計費方式，不能僅憑試驗次數增加就確定成本等比例增加。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 須確認不超過官方 20 個 strict 工具上限與 schema 複雜度。
verifier value: 部署前應查核當時官方文件對 strict 工具數量與 schema 複雜度的限制。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的史料證據支持 strict: true 可約束工具名稱與輸入符合 schema，但未提供 20 個工具的上限或其適用條件，無法據此核實這項具體限制。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: Haiku 5.5 或 Sonnet 5.5 裁判的固定前綴須達模型最低可快取門檻 512 tokens
verifier value: 固定前綴須達該裁判模型官方公布的最低門檻（Sonnet 層依證據可能為 1,024 tokens；Haiku 5.5 為 unknown，須查文件），不宜一律寫 512  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只說 512 tokens 適用於較新的 Claude 5／5.5 旗艦模型（例：claude-opus-5-5），標準 Sonnet 層列為 1,024 tokens，而 Haiku 5.5 沒有列出門檻，也註明須逐模型查證。把 512 套用到 Haiku 5.5／Sonnet 5.5 缺乏證據；若實際門檻是 1,024，前綴介於 512 到 1,023 時快取會
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: strict: true 須確認不超過官方 20 個 strict 工具上限
verifier value: 上限數值 unknown，須查官方文件  flagging family: anthropic (imprecise)
arbiter: agrees=true — 提供的 source-evidence 只描述 strict: true 會在解碼時強制工具名稱與輸入符合 schema，沒有提到「20 個 strict 工具上限」。這個數字無法從證據判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 範例輸出 9 次試驗總評測成本 $0.2097；新增 EVAL-004 後試驗增至 12 次，成本等比例增至 $0.2796（增加 33⅓%）
verifier value: 成本至少約 $0.2796（以每次試驗成本相同為前提）；實際值取決於模擬器對 EVAL-004 的 token 計數，目前 unknown  flagging family: anthropic (imprecise)
arbiter: agrees=true — 12/9×$0.2097 = $0.2796，算術正確。但 $0.2097/9 ≈ $0.0233/次，跟基準 $0.1015/次對不上，模擬器的 token 設定沒有提供，無法驗證。另外，EVAL-004 會走 5 次 check_inventory、超過步數，單次試驗的 token 消耗多半高於平均，「等比例」只是近似。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 企業生產環境每次只執行一次工單，因此必須用 Pass^k 而非 Pass@k 衡量
verifier value: 生產單次執行應追蹤單次成功率與嚴重錯誤率；Pass^k 作為穩定度與一致性指標輔助，而不是唯一依據  flagging family: anthropic (imprecise)
arbiter: agrees=true — 說 Pass@k 不適合生產是對的，但理由與章內自身說法有落差。生產環境只跑一次時，直接對應的指標是單次成功率（約等於 Pass^1）。Pass^k 衡量的是重複條件下的一致性，章節前文也寫明單次成功率與嚴重錯誤率應另外獨立追蹤。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: Claude 5.5 三款模型在 Claude API 的 Prompt Caching 最小前綴門檻皆為 512 tokens。
verifier value: Opus 5.5 的已提供門檻為 512 tokens；Sonnet 5.5 與 Haiku 5.5 的門檻須依各模型文件另行確認，並分別驗證。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 僅明確列出 Opus 5.5 為 512 tokens，未提供 Sonnet 5.5 與 Haiku 5.5 的確切門檻；其他列出的 Sonnet 與 Haiku 門檻則屬不同型號。因此無法由所給證據推出三款均為 512，也無法據此判定啟動時只檢查超過 512 tokens 即足夠。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 每 20 分鐘才進線 1 次時……改用 1h TTL 時，第 1 次付 2.0× 寫入，第 2、3 次各付 0.05× 讀取……省下 44% 前綴成本。因此離峰間隔大於 5 分鐘但小於 1 小時的長尾租戶應選 1h TTL。
verifier value: 三次請求符合所列命中假設時，1h 節省 44%；實際 TTL 應依相同前綴的回合數、請求間隔、命中率及冷寫入次數比較。  flagging family: openai (imprecise)
arbiter: agrees=true — 在三次請求均使用相同前綴、後兩次均命中，且 5m 情境三次均為冷寫入的假設下，5m 為 3 × 6,000 × 1.25 = 22,500 等效 tokens；1h 為 6,000 × (2 + 0.05 + 0.05) = 12,600，節省 44%，算術正確。但僅有兩次請求時，1h 的 2.05 倍仍高於 5m 兩次冷寫的 2.5 倍所對應的比較需依實際快取使用情況判斷；更一般地，間隔本身不能
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 在 simulateOrderOpsWaterfall 中分別傳入 ttl = "1h" 與 inference_geo = "us"（1.1×），確認輸出月成本仍低於 $18,000 上限（$16,268.51／$16,269）。
verifier value: 若兩個參數同時傳入，預期月成本約 $17,631.74，取整美元為 $17,632；若分開測試，1h 約 $16,028.85，us 約 $16,268.51。  flagging family: openai (incorrect)
arbiter: agrees=true — 章內 Stage 5 已分別列出：僅啟用 us 駐留為 $16,268.51；僅改 1h TTL 為 $16,028.85；兩者並用為 $17,631.74。將兩個參數同時傳入時，應比較兩者並用的數值，不能使用僅啟用 us 駐留的數值。由 $16,028.85 乘 1.1 約得 $17,631.74，與帳本一致。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 裁減 700 個輸出 tokens 等於直接減少 700 × TPOT 的總生成時間。
verifier value: 在 TTFT、TPOT 及其他條件近似不變時，裁減 700 個輸出 tokens 可近似減少 700 × TPOT 的生成時間，實際效益須量測。  flagging family: openai (imprecise)
arbiter: agrees=true — 章內生成時間公式是 TTFT + (N − 1) × TPOT 的近似式。只有在比較前後 TTFT 與每 token 耗時可視為相同，且其他延遲不變時，輸出減少 700 tokens 才近似節省 700 × TPOT；實際生成速度與其他延遲可能改變。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: Stage 0：「5×6,000 + 1,200×(1+2+3+4+5) = 42,000」
verifier value: 5×6,000 + 1,200×(0+1+2+3+4) = 42,000（若照原算式則為 48,000）  flagging family: anthropic (incorrect)
arbiter: agrees=true — 照字面計算：5×6,000 = 30,000；1,200×(1+2+3+4+5) = 1,200×15 = 18,000；兩者相加是 48,000，不是 42,000。要得到基準的 42,000，新增輸入的累加項必須是 1,200×(0+1+2+3+4) = 12,000，也就是第 k 回合帶入前 k−1 回合累積的新增輸入。42,000 這個數字本身與基準相符，錯的是算式。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 尖峰 12 req/s 約為平均 0.5787 req/s 的「約 21 倍」
verifier value: 約 20.7 倍（基準標示為 20×，應統一說法）  flagging family: anthropic (imprecise)
arbiter: agrees=true — 50,000/86,400 = 0.5787 req/s，12/0.5787 = 20.7 倍，四捨五入確實接近 21。但基準資料寫的是「平均 0.58 req/s，尖峰 20×」，兩處說法不一致。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 「Claude 5.5 三款模型在 Claude API 的 Prompt Caching 最小前綴門檻皆為 512 tokens」
verifier value: 僅 Opus 5.5 經證據確認為 512；Sonnet 5.5 與 Haiku 5.5 的門檻 unknown，應逐一查證，啟動驗證也應依各模型門檻設定  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只寫明 claude-opus-5-5 的門檻是 512。它列出的 1,024 適用「standard Sonnet tiers（claude-sonnet-5／先前的 Sonnet 4.5/4.6）」，4,096 適用舊版 Haiku 4.5，並註明部署前須逐一查核各模型門檻。Sonnet 5.5 與 Haiku 5.5 的門檻在提供的證據中查不到，因此「三款皆為
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 「每個斷點往前查找約 20 個 block」，以及 Batch「24 小時內完成，逾時標記為 expired」
verifier value: 須以官方 Prompt Caching 與 Batch 文件查證  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只說明前綴依 tools → system → messages 的順序精確比對，以及 Batch 有 50% 折扣。20 個 block 的回溯範圍、24 小時時限與 expired 狀態都不在提供的證據中，閉卷無法確認。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: 每天不到 4 美元的估算開銷就能在入口處過濾多數已知惡意輸入。
verifier value: 在所列用量與費率假設下成本為 $3.75／天；能攔截多少惡意輸入須由評估集量測。  flagging family: openai (imprecise)
arbiter: agrees=true — 費用可依假設重算，但提供的材料沒有分類器在代表性惡意輸入上的攔截率，也沒有支持「多數」的評估結果；成本低不能推導出攔截效果。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: 即使主模型被 Indirect Prompt Injection 徹底攻陷，只要 Policy Engine 與後端執行器拒絕執行，攻擊就無法造成實際損失。
verifier value: 若政策與執行器在派發前正確拒絕該項操作，可阻止該操作經由受控路徑執行；其他損失仍須依各自攻擊路徑防禦。  flagging family: openai (imprecise)
arbiter: agrees=true — 拒絕某項未授權工具操作，只能推導該操作未透過此執行路徑完成；不能排除其他讀取、輸出、可用性或資訊外洩造成的損失。章內也指出退款上限擋不住借唯讀工具外洩資料。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: 將前一筆雜湊納入當前紀錄，並比對獨立儲存的可信 checkpoint，即可偵測資料庫層級的竄改或刪除。
verifier value: 可信 checkpoint 可保護其涵蓋的鏈段；要偵測 checkpoint 之後的尾端刪除，還需獨立保存並比對足夠新且可信的預期鏈頭或序號。  flagging family: openai (imprecise)
arbiter: agrees=true — 重算雜湊、檢查序號與比對可信 checkpoint，可偵測影響已錨定鏈段的變更，以及可觀察到的不連續；但若最新 checkpoint 之後的完整尾段遭刪除，且沒有獨立記錄最新預期鏈頭或序號，單靠較舊 checkpoint 無法證明該尾段曾存在。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: Claude Haiku 5.5 不支援 temperature: 0，送出會回傳 400；預設啟用 adaptive thinking，並可傳入 thinking: {"type": "disabled"}。
verifier value: 應依該模型當前官方文件或受控 API 測試確認支援的取樣與 thinking 設定，以及不支援時的實際錯誤。  flagging family: openai (imprecise)
arbiter: agrees=true — 所附 source-evidence 有概述 extended thinking，但沒有列出 Haiku 5.5 的取樣限制、預設 thinking 模式或該停用設定的相容性，因此無法由提供材料驗證這些具體 API 行為。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: Claude API 的 MCP Connector 與 Message Batches 均不符合 ZDR，Batch 結果自建立起可取用 29 天。
verifier value: 應依適用部署、端點、功能與協議的官方資料確認 ZDR 資格及 Batch 結果保留期限。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 沒有列出這兩項功能的 ZDR 資格或 Batch 結果保留期限，故無法據此判定具體限制與天數。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: Claude Haiku 5.5 不支援 temperature: 0（送出會回傳 400），且預設啟用 adaptive thinking，可用 thinking: {"type": "disabled"} 關閉
verifier value: 應限定為「依部署時的官方模型文件確認 sampling 與 thinking 預設行為」，或補上來源  flagging family: anthropic (imprecise)
arbiter: agrees=true — 基準資料與 source-evidence 只提到 Extended Thinking 可用 budget_tokens 或新模型的 adaptive 模式啟用。兩者都沒有記載 Haiku 5.5 拒絕 temperature: 0、會回傳 400，或預設開啟 adaptive thinking。這些細節閉卷無法判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: Claude API 的 MCP Connector 與 Message Batches 均不符合 ZDR，Batch 結果自建立起可取用 29 天
verifier value: 應改為「需查核 MCP Connector 與 Batch 的 ZDR 資格及結果保留期限」，並附上官方來源  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 沒有提到 ZDR 資格，也沒有提到 Batch 結果的保留天數。「29 天」與「不符合 ZDR」都無法從已提供的證據判定，需要外部官方文件查證。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: 「頭部採樣會直接漏掉故障現場。」
verifier value: 頭部採樣可能漏掉絕大多數故障 Trace，且不能保證保留特定故障；尾部採樣可依已觀察到的錯誤等條件提高保留率。  flagging family: openai (incorrect)
arbiter: agrees=true — 若頭部採樣以每筆請求獨立隨機抽樣，單一故障 Trace 被保留的機率等於採樣率，並非必然遺漏。例如採樣率為 1% 時，該 Trace 被漏掉的機率為 99%。在 50,000 筆工單中，若 0.5% 為故障，期望有 250 筆故障；以 1% 隨機抽樣，期望保留 2.5 筆故障 Trace，但仍可能一筆也未保留。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: 「最常見的根因是 System Prompt 或工具 Schema 前段被意外插入動態內容。」
verifier value: 前綴被動態內容改變是可能原因之一，應結合前綴雜湊、快取寫入與讀取量及快取設定診斷；材料不足以判定哪個原因最常見。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的證據支持前綴內容變動會使後續快取斷點失效，但未提供事故統計，不能據此判定這是最常見的原因。停用快取、未達快取門檻或其他快取設定變化也可能造成讀取量為零；工具錯誤率與延遲正常不足以區分這些原因。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: 「生產環境一律鎖定明確的模型版本字串（如 `claude-sonnet-5-5`）。」
verifier value: 應使用供應商明確文件化的固定快照識別碼；若只有模型 ID，須確認其版本更新政策，並持續監控模型行為。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 將 `claude-sonnet-5-5` 列為 canonical model ID，但未說明此字串是否指向不可變快照，或供應商是否可能更新其背後實作。因此，僅憑這份材料不能確定使用該字串已完成快照層級的版本鎖定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: OTel GenAI 語意慣例中 gen_ai.usage.input_tokens 應包含快取讀寫 token；Anthropic Header 名稱（request-id、anthropic-ratelimit-*）與 stop_reason 列舉（含 refusal、pause_turn、model_context_window_exceeded）
verifier value: 需對照 OpenTelemetry GenAI semconv 現行版本與 Anthropic Messages API 文件查證後再定稿  flagging family: anthropic (imprecise)
arbiter: agrees=true — 所附 source-evidence 只涵蓋價格、快取、工具與 MCP，沒有 OpenTelemetry semconv 規範、Anthropic 回應 Header，也沒有完整的 stop_reason 列舉，閉卷無法從所提供證據判定正誤。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: Span 範例中單回合 input 1,200 + cache_read 6,800 = 8,000，用來說明 OrderOps 回合
verifier value: 標註為示意數值；或改用與基準一致的回合，例如第 2 回合 7,200 = 快取 6,000 + 新增 1,200（命中率約 83.3%）  flagging family: anthropic (imprecise)
arbiter: agrees=true — 算式本身正確，但依基準序列，各回合輸入為 6,000、7,200、8,400、9,600、10,800，沒有一個回合是 8,000。而且基準前綴是 6,000 tokens，不是 6,800。這組數字只是示意，與 ch01 序列並不一致，讀者可能誤以為是基準回合。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 此分層架構可換取 88% 以上的成本降幅。
verifier value: 3,600-token 帳本相對基準約降 88.57%；6,000-token 即時架構的降幅須依完整生產帳本計算。  flagging family: openai (imprecise)
arbiter: agrees=true — 以章節引用的 $17,399.47/月與無快取基準 $152,250/月相比，降幅約為 88.57%；但該數字屬縮減至 3,600 tokens 的另一份帳本。本章即時設計使用 6,000-token 前綴，且未列出逐模型流量、快取、重試及升級呼叫等完整帳本，無法據此證明本章架構本身達到同一降幅。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 在 Sonnet／Opus 5.5 中，舊版 thinking: { type: "enabled", budget_tokens: 2048 } 會觸發 HTTP 400。
verifier value: 依提供的證據可知存在 enabled 與 adaptive 設定；是否對指定模型回傳 400，仍需模型專屬文件或實測證據。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 說明 enabled 設定或較新模型的 adaptive 模式，並未提供 Sonnet／Opus 5.5 禁用前者及回傳 HTTP 400 的證據，不能由此推得章節的絕對說法。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 若同時啟用 Claude 原生 Citations 與 output_config.format，API 會回 400。
verifier value: 相容性及可能的錯誤碼須以相關 API 文件或實測確認。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 支持結構化輸出使用 output_config.format，但未記載其與原生 Citations 的相容性或錯誤碼，因此無法從材料判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 這項規則會讓每次分診多花 45–90s（兩次串行 30s 測試最多 60s，加上容器準備與排隊），但能阻斷未經實證的錯誤修補建議。
verifier value: 額外耗時應以實測分布估計；證據鏈可攔截未符合指定證據要求的建議，但不能保證根因或修補正確。  flagging family: openai (incorrect)
arbiter: agrees=true — 每次測試的 30 秒是逾時上限，不是實際耗時；容器準備與排隊也未給定上下界，因此無法推出每次增加 45–90 秒。雙來源與重現測試只能檢查指定證據是否存在並通過規則，不能保證測試足以證明根因或排除所有錯誤修補。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 法務團隊要求使用者上傳後 15 分鐘內必須看到結果……僅針對「加急合約」走即時 API，其餘例行合約維持夜間 Batch API。
verifier value: 若所有合約都適用 15 分鐘要求，須為所有合約設計並驗證符合期限的處理流程；只有法務同意變更或分級 SLA，才能將例行合約留待夜間處理。  flagging family: openai (incorrect)
arbiter: agrees=true — 題目要求上傳後 15 分鐘內看到結果，未對例行合約設例外。將例行合約留待夜間處理無法滿足此要求；即時 API 本身也不保證整體流程達成 15 分鐘。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 現有檢查會放行，因為它只檢查字串非空，未檢查時間窗口。
verifier value: 若現有實作僅檢查欄位非空而未驗證受信任的 incident 與時間窗綁定，該舊紀錄可能放行；須檢視完整驗證流程才能判定。  flagging family: openai (imprecise)
arbiter: agrees=true — 章節沒有提供 verifyTriageEvidenceChain 的完整程式碼；同時正文要求遙測紀錄由服務端綁定 incident 與查詢時間窗，並只計入已驗證來源。若這些綁定確實在閘門前或閘門內執行，三天前且與事件無關的紀錄可能已被拒絕，因此不能確定必然放行。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: ch08 最終帳本（3,600-token 前綴，30% 離線流量享 Batch 折扣）為 $14,789.55/月；移除 Batch 折扣後為 $17,399.47/月，約 $0.0116/筆
verifier value: 比例關係正確；$17,399.47 的底數須以 ch08 逐項帳本驗證  flagging family: anthropic (imprecise)
arbiter: agrees=true — 內部算式自洽：17,399.47×(1 − 0.3×0.5) = 17,399.47×0.85 ≈ 14,789.55；17,399.47/1,500,000 ≈ $0.0116；降幅約 88.57%，符合 ≥88% 與 ≤$18,000 的目標。不過 $17,399.47 這個底數，以及 3,600-token 前綴的設定，都要依賴 ch08 的帳本（基準前綴是 6,000），本章與基準都沒有提
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 在 Sonnet／Opus 5.5 中，舊版 thinking: { type: "enabled", budget_tokens: 2048 } 會觸發 HTTP 400，應改用 adaptive
verifier value: 依現有證據，應改寫為「新模型可改用 adaptive 推理模式」；要宣稱會回 400，須另行查證官方文件  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 寫的是 Extended Thinking 透過 thinking: { type: "enabled", budget_tokens: N } 啟用，新模型「或」可用 adaptive 模式，完全沒提到 budget_tokens 在 5.5 會回 400。這與章節說法有落差，現有證據不支持。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 同時啟用原生 Citations 與 output_config.format 會回 400；Batch 的 custom_id 須符合 ^[a-zA-Z0-9_-]{1,64}$；Batch 有 24 小時 SLA
verifier value: unknown；須以官方 Batch 與 Structured Outputs 文件查證  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只記載 Batch 的 50% 折扣與 output_config.format 的用途，沒有 Citations 衝突、custom_id 格式或 24 小時時限的資料，無法判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: Messages API MCP Connector 需要可公開連線的 Streamable HTTP + SSE 端點，且不適用 ZDR，並須明確設定 beta 版本
verifier value: 依現有證據：Connector 需要遠端 Streamable HTTP 端點（不支援 stdio）；SSE、ZDR 與 beta header 要求須另行查證  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只指出 Connector 接受遠端 Streamable HTTP（OAuth 2.1／Bearer），透過 mcp_servers 與 mcp_toolset 設定，不支援 local stdio。該證據也說 Streamable HTTP 已取代舊版 HTTP+SSE。「需要 SSE」「不適用 ZDR」「須設 beta 版本」都沒有證據支持。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 「每日處理超過 459 筆工單（605 ÷ 1.32 = 458.33，約佔總量 0.92%）即可打平每日 $605 API 成本。」
verifier value: 若固定支出確為 $605／天，至少需 459 筆／天；若 API 成本隨處理量按每筆 $0.011 × 1.1 = $0.0121 計算，則每筆平均淨節省為 $1.32 − $0.0121 = $1.3079，不能據此推得 459 筆的損益平衡門檻。  flagging family: openai (incorrect)
arbiter: agrees=true — $605 是 50,000 筆全量呼叫所產生的變動成本，不能同時假設只處理約 459 筆並沿用全量成本。若假設 $605 是不隨處理量變動的固定支出，458.33 筆須向上取整為 459 筆，而非超過 459 筆，才能使節省額至少打平。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 「只要 L2/L3 每日能節省的人力處理成本超過每日 API 成本（$21,780 ÷ 30 = $726/天）……每日僅需處理超過 605 筆工單……即可達成損益平衡。」
verifier value: 全量 API 呼叫成本固定為 $726／天的假設下，605 筆 L2 恰好打平，606 筆起為正；若 API 呼叫量隨處理量變動，應依實際呼叫筆數計算成本。  flagging family: openai (imprecise)
arbiter: agrees=true — $726 是每天 60,000 筆均呼叫 API 的成本，而 605 筆是把這筆全量成本當作固定支出，再以每筆 L2 節省 $1.20 計算所得。若只有 605 筆呼叫 API，成本也會下降；若全量 60,000 筆都呼叫，則至少需要 606 筆產生 L2 節省才能使該估算淨效益為正。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 「尖峰 12 req/s 若每單 5 次模型呼叫即達 60 模型請求／秒」。
verifier value: 持續穩態下平均約 60 次模型請求／秒；瞬間尖峰須依各回合時間分布與併發情況估算。  flagging family: openai (imprecise)
arbiter: agrees=true — 12 筆工單／秒乘每單 5 次，得到的是該工單流量持續且模型呼叫分布達穩態時的平均模型請求率；各回合可能分散在不同時間，也可能集中，單憑每單呼叫次數無法確定瞬間尖峰。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 「設定 cache_hit_ratio < 0.70（定義為合格前綴 cache_read_input_tokens ÷ (cache_read_input_tokens + cache_creation_input_tokens)）的 P1 告警」，用以防禦快取靜默失效。
verifier value: 除監控有定義的讀取比例外，應對分母為 0、預期可快取請求卻沒有讀取或建立 token 的情形另設檢查；比率的統計範圍也須明訂。  flagging family: openai (imprecise)
arbiter: agrees=true — 依提供的證據，低於最低可快取前綴門檻時可能不建立快取，且 cache_creation_input_tokens 為 0；若同時沒有快取讀取，公式分母為 0，無法算出低於 0.70 的比率。其他未建立或未讀取快取的情形也有同樣限制。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 「單日異常消耗達 150%（$900）時自動降級」與每日「$600」硬性預算上限並存。
verifier value: 應在預留或預測消耗將觸及 $600 前阻擋新增支出；$900 只能明確定義為計量延遲或超額後的後備告警，不能保證 $600 硬上限。  flagging family: openai (imprecise)
arbiter: agrees=true — 若 $600 是不可超過的硬上限，且請求前預留及對帳能準確執行，消耗不應達到 $900；因此 $900 不能作為維持該硬上限的主要觸發點。章節雖另要求預留與對帳，仍未說明 $900 告警所處理的超額或計量延遲情境。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 「cache_read_input_tokens 歸零，成本可能朝未優化的 $152,250 基準急遽攀升。」
verifier value: 快取失效可能提高成本；只有其他成本假設也接近未優化基準時，才可用 $152,250／月作為相應估算。  flagging family: openai (imprecise)
arbiter: agrees=true — 基準 $152,250 假設全量使用 Sonnet、每筆輸入 42,000 tokens、輸出 1,750 tokens 且無快取。快取讀取歸零只符合其中一項條件；實際成本仍取決於模型分流、token 用量、快取寫入及其他折扣。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 與 ch08 Stage 5 的 $0.009860 估算口徑不同
verifier value: unknown（需對照 ch08 原文）  flagging family: anthropic (imprecise)
arbiter: agrees=true — 提供的材料沒有 ch08 Stage 5 的內容，無法核對 $0.009860 這個數值及其口徑。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 階段四啟用 us 1.1× 後滿載 API 成本 $18,150/月（$605/天），作為可上線的配置
verifier value: 若上限為含 US 加價的 $18,000，階段四的基礎單價須 ≤ $0.010909（例如 $0.0108 對應 $17,820/月），否則須先調高預算上限  flagging family: anthropic (imprecise)
arbiter: agrees=true — PRR 第 4 點把每日上限定為 $600、每月上限定為 ≤ $18,000，但階段四的 $18,150（$605/天）超過這兩個上限。章內的 validateProductionConfig 會算出 estMonthlyUsd = 18,150 > 18,000，令 costOk 為 false 並阻斷部署。章節雖然指出基礎單價應降至 ≤ $0.010909，帳本卻仍沿用 $0.011，因此前後
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 損益平衡點：加權節省 $1.32/筆；每日處理超過 459 筆工單（605 ÷ 1.32 = 458.33，約佔總量 0.92%）即可打平每日 $605 API 成本
verifier value: ≥ 459 筆（約 0.92%）的前提是 $605 為固定成本；以變動成本計，單筆淨節省約 $1.32 − $0.0121 ≈ $1.308，恆為正  flagging family: anthropic (imprecise)
arbiter: agrees=true — 算術正確：0.7 × 1.20 + 0.3 × 1.60 = 1.32；605 ÷ 1.32 = 458.33；459 ÷ 50,000 = 0.918%。但有兩個問題。其一，打平條件是 ≥ 459 筆，「超過 459 筆」的寫法不精確。其二，$605/天是 50,000 筆全量處理的 API 成本，若每日只處理 459 筆，API 成本不會是 $605。每筆的 API 成本約為 $0.0121（
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 自我檢核 2 解答：L3 需離線 Pass^3 ≥ 0.95（高於 L2 的 0.85 門檻）、0 < maxAutoRefundUsd ≤ 50、L2 連續 14 天 Pass^3 ≥ 0.95 且零嚴重誤判，並具 30 秒 Feature Flag
verifier value: 三條件：離線 Pass^3 ≥ 0.95；0 < maxAutoRefundUsd ≤ 50 且超額退回 L2；L2 連續 14 天 Pass^3 ≥ 0.95 且零嚴重誤判（Feature Flag 屬通用 PRR 要求）  flagging family: anthropic (imprecise)
arbiter: agrees=true — 門檻數值與章內 PRR、演進圖及程式碼一致。但題目要求「三個必要條件」，解答的第三點另外併入了 Feature Flag，實際上列了四項。另外，0.85 是通用的上線基準，並非專屬於 L2 的門檻，稱「L2 的 0.85 門檻」不夠精確。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 要達成整體 ≤ $18,000/月，複雜工單加權成本須壓至 ≤ $0.027495/筆。
verifier value: 複雜工單平均成本須 ≤ $0.027495／筆；其對全部工單的加權成本貢獻須 ≤ $0.010998／總工單筆。  flagging family: openai (imprecise)
arbiter: agrees=true — 月均每筆上限為 $18,000 / 1,500,000 = $0.012。令複雜工單每筆成本為 C，則 0.6 × $0.00167 + 0.4C ≤ $0.012，得 C ≤ $0.027495。數值正確，但這是複雜工單本身的平均單筆成本上限；其占全部工單的加權貢獻是 0.4C，不能同時稱為加權成本和每筆上限。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 若同一輪同時包含唯讀與寫入型工具，必須先執行唯讀檢查、在寫入端原子驗證前置條件無誤後再執行寫入，或由後端限制單輪可執行的寫入數量，避免部分失敗造成狀態不一致。
verifier value: 限制單輪寫入數量可縮小故障範圍，但須配合寫入端原子驗證、冪等性及逾時後對帳或補償機制；跨系統一致性不能由寫入數量限制單獨保證。  flagging family: openai (incorrect)
arbiter: agrees=true — 限制寫入數量本身不能保證一致性：即使一輪只執行一次寫入，寫入仍可能成功而回應逾時，或與其他系統的狀態不一致。先讀後寫也只有在寫入端原子驗證相關前置條件時，才能避免讀取與寫入之間的狀態變更造成相應競態；跨系統部分失敗還需要恢復機制。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 將 wallClockTimeoutMs 設為 1，確認 AbortController 能立即中止請求並回傳 status: timeout 與 stopReason: wall_clock_timeout。
verifier value: 應以受控的延遲或假回應驗證逾時分支，並區分單輪逾時與整體 wall-clock 逾時；取消與回傳時間均有排程及實作上的限制。  flagging family: openai (imprecise)
arbiter: agrees=true — 程式只在進入迴圈時先檢查已耗時間，再以剩餘時間設定計時器。計時器排程及請求取消均非精確即時，且若請求在中止前完成，程式也可能走其他分支；因此設定 1 毫秒不能單憑程式保證立即中止及固定結果。此外，單輪 5 秒計時器觸發時，同一 catch 分支也會回報 wall_clock_timeout，無法區分單輪逾時與整體期限逾時。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 單輪內的多個唯讀工具適合平行執行，能把多工具總延遲從加總降為最大值。
verifier value: 對互相獨立且可充分並行的唯讀呼叫，理想延遲近似最慢呼叫的耗時，實際仍須加上開銷並考慮資源限制。  flagging family: openai (imprecise)
arbiter: agrees=true — 若工具呼叫互相獨立、可充分並行，且忽略排程、連線與彙整開銷，等待全部結果的時間近似各呼叫耗時的最大值。若有依賴、資源競爭或並行度限制，實際延遲可能高於最大值，甚至接近串行加總。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: Batch API 結果最長可達 24 小時
verifier value: 限定為「依官方 Batch API 文件的處理時限為準」，或補上可查證的出處  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只記載 Batch API 的 input/output 各打 50% 折扣、適用非同步工作負載，沒有任何處理時限的資料。這段材料無法支持「24 小時」這個數字。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch01-agent-architecture.md — fixed
claim: 完整 API 的 stop_reason 尚包含 stop_sequence、pause_turn 與 model_context_window_exceeded；平台過載回傳 HTTP 529 overloaded_error
verifier value: 保留，但需註明以官方文件列舉為準並另行查證  flagging family: anthropic (imprecise)
arbiter: agrees=true — 提供的基準資料與 source-evidence 都沒有列出這些 stop_reason 值或 529 錯誤碼，閉卷無法查證，需要對照官方 Handling Stop Reasons 與 Errors 文件。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 整條呼叫鏈必須共同執行 18,000 ms wall-clock deadline（對齊多步處置 p95 ≤ 18s SLO）。
verifier value: 18 秒可作為呼叫鏈預算；應另定義完成、超時及轉人工的 SLO 計算方式，並以實際延遲與結果驗證。  flagging family: openai (imprecise)
arbiter: agrees=true — 18 秒 deadline 可限制呼叫鏈等待與重試時間，但 p95 SLO 衡量的是定義中的完成延遲分布。若超時工單被轉人工或視為失敗，仍須明確定義其是否納入分母及如何計算，不能僅憑設置 deadline 推得 SLO 達成。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 以下為 Wire-Level tool_use 回應範例：usage 中 input_tokens 為 1200，cache_read_input_tokens 為 6000。
verifier value: 應標明此為已有 6,000 tokens 快取命中的後續回合，並說明 1,200 tokens 為未快取輸入；依成本算例，其總輸入為 7,200 tokens。  flagging family: openai (imprecise)
arbiter: agrees=true — 若 1,200 是未快取的新增輸入，則此範例總輸入為 1,200 + 6,000 = 7,200 tokens，對應成本算例中的第二回合，而非該算例的第 1 回合。範例本身未標明回合，也未說明 usage 欄位的計數關係，因此不足以判定其與算例是否一致。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 依序發送 initialize → notifications/initialized → tools/list → tools/call。
verifier value: 在 notifications/initialized 與 tools/call 之間補上一個 JSON-RPC tools/list 請求，並檢查其回應。  flagging family: openai (incorrect)
arbiter: agrees=true — 所附 curl 命令依序只發送 initialize、notifications/initialized 與 tools/call，沒有發送 tools/list，因此實際命令不能完成文字指定的驗證序列。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 本章的完整可執行程式碼已建置於 examples/ts/ch02/index.ts 與 examples/py/ch02/main.py。
verifier value: 應以提供的原始碼及實際執行與測試結果驗證；目前只能視為待查的程式碼位置與預期行為。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的材料只有路徑、程式片段與預期輸出，沒有兩個檔案的完整內容或實際執行結果，無法獨立確認檔案存在、功能完整或可執行。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 將操作鍵傳給支付商並結合共享帳本，可確保在高併發與跨節點重試下維持帳務零重複。
verifier value: 在支付商冪等契約覆蓋所有重試與對帳情境，且系統正確實作操作狀態及餘額保留時，可防止所涵蓋情境的重複退款；須依支付商契約與故障測試驗證。  flagging family: openai (imprecise)
arbiter: agrees=true — 持久操作紀錄、酬載比對與支付商冪等鍵能降低重複退款風險，但零重複還依賴支付商實際支援的冪等範圍與保留期限、未知結果的查詢及對帳，以及重試時是否沿用相同鍵。提供的材料未證明這些外部條件均成立。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: strict: true 會在解碼階段強制 tool_use.input 符合 schema；遞迴 Schema、patternProperties、minLength 等是否支援須依官方文件核對
verifier value: 核心機制正確；所舉不支援關鍵字的例子須外部查證官方文件  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 支持 strict: true 會在解碼時強制工具名稱與輸入酬載符合 schema。但它沒有列出支援或不支援的關鍵字，所以舉這幾個關鍵字作為可能不支援的例子，無法從所附證據判定。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: output_config.format 底層 wire 格式為 {"type": "json_schema", "schema": ...}；Python 搭配 messages.parse(output_format=...)；TypeScript 搭配 zodOutputFormat
verifier value: output_config.format 接受 JSON Schema（可用 Zod / Pydantic 包裝）；確切 wire 欄位與 helper 名稱須查官方文件  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 只記載 output_config.format 接受 JSON Schema，並可透過 TS 的 Zod 或 Python 的 Pydantic 包裝。具體 wire 包裝物件、helper 名稱與方法簽章都不在所附證據內。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: Claude API 透過 mcp_servers Connector（搭配對應 beta 標頭與 mcp_toolset 設定）連線至遠端 Streamable HTTP MCP Server，使用 mcp_tool_use / mcp_tool_result 區塊
verifier value: mcp_servers + mcp_toolset、僅限遠端 Streamable HTTP（OAuth 2.1 / Bearer）有證據支持；beta 標頭與區塊型別名稱須外部查證  flagging family: anthropic (imprecise)
arbiter: agrees=true — source-evidence 支持 mcp_servers、mcp_toolset、僅限遠端 HTTP 以及 OAuth 2.1 / Bearer 認證。但「需要 beta 標頭」以及 mcp_tool_use / mcp_tool_result 區塊名稱，所附證據都沒有記載。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch02-tool-use-and-mcp.md — fixed
claim: 退避設定 base = 500 ms、cap = 16,000 ms、max_retries = 4（指數退避加 Full Jitter）
verifier value: 要嘛刪掉 cap，要嘛註明以 max_retries = 4 計算時 cap 實際不會生效（最大單次延遲約 4,000 ms）  flagging family: anthropic (imprecise)
arbiter: agrees=true — 以 base × 2^(n−1) 計算，4 次重試的上限依序為 500、1,000、2,000、4,000 ms，永遠到不了 16,000 ms 的 cap，所以這個參數形同無效。若改用 base × 2^n，上限為 1,000～8,000 ms，同樣到不了 cap。累計最大等待約 7.5～15 s，在 18 s deadline 下仍可行，但參數組合彼此不一致。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: OrderOps 的 3,600 與 6,000 tokens 前綴不論哪個門檻都已超過。
verifier value: 兩個前綴均超過所舉的 512 與 1,024 tokens 門檻；各模型實際門檻，包括 Sonnet 5.5，仍須另行確認。  flagging family: openai (imprecise)
arbiter: agrees=true — 3,600 與 6,000 均超過章內舉例的 512 與 1,024 tokens 門檻；但提供的證據另列部分舊模型門檻為 4,096 tokens，3,600 未達該門檻。證據也未列出 Sonnet 5.5 的確切最低門檻，因此不能據此確認其 3,600-token 斷點必定可快取。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: thinking 產生的 tokens 計入 API 回傳的 usage.output_tokens，因此只應在高難度或高風險工單開啟，不應全量預設開啟。
verifier value: 應確認所用模型的 thinking 計費與 usage 欄位口徑，並依任務品質、風險、延遲及成本評測決定啟用範圍。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的證據列出輸出價格與 thinking 的使用方式，但未直接記載 usage.output_tokens 的計數口徑。即使按章內假設將 thinking 視為計費輸出，成本較高也不能單獨證明必須僅限高難度或高風險工單；決策還取決於品質改善、錯誤損失與任務評測。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch03-context-and-prompt-engineering.md — fixed
claim: 在 tool_use 迴圈中，必須原封不動保留 thinking／redacted_thinking block（包含其中的 signature 欄位），並將所有對應的 tool_result 放在緊接的 user 訊息開頭。
verifier value: 工具迴圈中應依所用 API 的規格保留先前 assistant thinking blocks 及其簽章；redacted_thinking 與 tool_result 的具體格式及排序須另行查證。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的證據支持在多回合工具迴圈中保留先前 assistant thinking blocks 及其簽章，但未具體說明 redacted_thinking 的欄位結構，也未提供 tool_result 必須位於緊接 user 訊息開頭的規則，無法獨立核實這些細節。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: Prompt Caching 靜默失效導致成本暴增（cache_creation_input_tokens = 0 且 cache_read_input_tokens = 0）；動態段落破壞前綴雜湊或工具陣列順序未固定，導致快取鍵值每回合都 miss。
verifier value: 前綴變動可能造成讀取 miss 並產生新的快取寫入；兩項計數皆為零時，應另查斷點、門檻及快取是否實際啟用。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的證據指出，低於最小可快取門檻會使建立快取的計數為零；但前綴改變造成未命中，與沒有建立快取是不同情況。若新前綴符合門檻且成功建立快取，miss 仍可能伴隨 cache_creation_input_tokens 大於零。因此不能把所有這類失效都描述為兩個計數皆為零。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 將每回合的 messages、已執行的 tool_use 與 tool_result 配對以及 waiting_for 狀態持久化到 PostgreSQL，就能在任何無狀態 Worker 節點上安全喚醒續跑。
verifier value: 持久化狀態可讓無狀態 Worker 恢復上下文；安全續跑還須結合併發控制、可恢復操作紀錄、外部副作用的冪等或對帳，以及授權檢查。  flagging family: openai (imprecise)
arbiter: agrees=true — 保存對話與等待狀態可提供恢復所需資訊，但單靠這些資料無法排除多個 Worker 同時喚醒，也無法處理外部退款已成功、結果尚未寫入時的崩潰。章節後文另要求狀態與版本 CAS、操作紀錄、下游冪等或對帳及權限重查，顯示原句的條件不足以單獨保證安全。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 喚醒與到期排程皆須以 agent_sessions.version 與 status = 'waiting_external' 執行條件 CAS 搶佔；搶佔失敗立即放棄。
verifier value: 除狀態與版本外，正常喚醒應檢查 expires_at > NOW()；到期轉移應檢查 expires_at ≤ NOW()，並在成功時改變狀態或遞增版本。  flagging family: openai (imprecise)
arbiter: agrees=true — 相同狀態與版本的條件更新，若成功時同時變更狀態或遞增版本，能使競爭同一版本的更新至多一方成功；但僅憑版本與狀態不能判定是否已到期。若喚醒在到期之後先搶佔，仍可能違反到期規則。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: Claude Messages API 嚴格要求每個 client-side tool_use 的對應 tool_result 出現在緊接其後的 user 訊息，且 tool_result 必須排在文字區塊之前。
verifier value: 此具體訊息順序與配對規則須以相應版本的官方 Messages API 工具使用文件核對。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 支持工具使用及多回合中保留 thinking 區塊，但沒有記錄此訊息配對與區塊順序的具體規則，無法僅依材料獨立確認完整的 wire-level 契約。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch04-state-memory-and-retrieval.md — fixed
claim: 檢索回來的動態段落必須放在 tool_result 內，絕不能插入 tools 或 system 之間。
verifier value: 為維持穩定快取前綴，動態段落應放在穩定 tools 與 system 前綴之後的適當訊息中；工具檢索結果通常放在對應 tool_result。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的證據顯示快取以前綴精確匹配，較早區塊變動會使後續斷點失效；因此把動態內容放在穩定前綴之後有助於保留前綴命中。這不能推出動態段落只能放在 tool_result：章節後文也容許放在最新 user 訊息中。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: 在 `(ticket_id, created_at)` 建立複合索引，區分工作流與重試次數，避免重試重複入帳。
verifier value: 複合索引用於查詢；應另以符合入帳語意的持久唯一鍵或唯一約束，以及交易處理，防止重複入帳。  flagging family: openai (incorrect)
arbiter: agrees=true — 此索引只包含工單與建立時間，可支援相關查詢；它既不包含 workflow_run_id 或 attempt_no，也沒有宣告唯一約束，因此無法單靠此索引區分各工作流與重試，更不能防止重複入帳。資料表雖有這兩個欄位，仍需明確定義何者代表同一次應入帳的執行，並以持久唯一鍵及交易邏輯防重。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: 每次 API 回應的 `usage` 欄位（`input_tokens`、`output_tokens`、`cache_read_input_tokens`、`cache_creation_input_tokens`）都會即時累加，寫入 `WorkerHandoff.costUsd`。
verifier value: 逐次記錄各類用量，依模型與適用費率分別換算後累加美元成本；無法確認的帳務應另行標示並對帳。  flagging family: openai (imprecise)
arbiter: agrees=true — 四種 token 用量不能直接相加成美元，必須依模型、一般輸入、輸出、快取讀取及各種快取寫入 TTL 的適用費率分別計價。提供的材料沒有顯示完整程式，也未說明如何區分不同 TTL 的寫入用量，因此無法判定實作是否正確累計費用。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: Sonnet 層級的最小快取門檻為 1,024 tokens。
verifier value: 提供的證據支持所列 Sonnet 5、4.5／4.6 的 1,024-token 門檻；Sonnet 5.5 應另依其型號文件確認。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 將 1,024 tokens 列於 Sonnet 5 和先前的 Sonnet 4.5／4.6，沒有明列本章使用的 Sonnet 5.5。據此不能把該門檻直接推廣至所有 Sonnet 型號。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch05-multi-agent-orchestration.md — fixed
claim: 執行後會依序處理 TKT-5001 與 TKT-5002，示意輸出成本分別為 $0.00051 與 $0.01811。
verifier value: 需提供各模型呼叫的輸入、輸出及快取用量，並核對實際程式或執行結果，才能驗證兩筆金額。  flagging family: openai (imprecise)
arbiter: agrees=true — 章節未提供範例實際使用的完整 token 數與程式內容；僅憑兩筆示意輸出和基準牌價，無法獨立重算成本或驗證程式執行結果。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: 若連線在 message_stop 前中斷，造成 tool_use.input 出現殘缺 JSON，必須丟棄該次未完成的 Turn 並重試整個 Turn。
verifier value: 丟棄殘缺輸出；確認未發生外部副作用後才重試。若遠端工具可能已執行，先查詢狀態，並依冪等保障決定是否重送或人工對帳。  flagging family: openai (imprecise)
arbiter: agrees=true — 殘缺的工具參數不能當成完整工具呼叫執行；但章節稍後指出，使用 MCP Connector 時，遠端工具可能已在串流中斷前執行。因此直接重送整個 Turn 可能重複副作用，是否能安全重試取決於派送方式及遠端執行狀態。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: Worker 重啟後依 seq ASC 讀取 Checkpoint，比對 llm_turn 與 tool_call 發現工具尚未落盤，於是補派送該工具。
verifier value: 先將操作標記為結果不明，依供應商查單能力與冪等有效期查詢或同鍵重送；無法安全確認時暫停自動派送並人工對帳。  flagging family: openai (imprecise)
arbiter: agrees=true — 缺少 tool_call 結果只證明回執尚未記錄，不能證明工具未曾派送或退款未入帳。原題恰好設定為執行工具後、寫入 Checkpoint 前崩潰；參考解答後文雖提到查單與冪等限制，這句仍把結果不明直接等同於應補派送。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: Batch API 提供 50% 折扣，Sonnet 5.5 為每百萬輸入 tokens 1 美元、輸出 tokens 5 美元；回應通常數十分鐘至數小時內完成。
verifier value: 依提供的價格基準，Batch 輸入與輸出分別為每百萬 tokens 1 美元及 5 美元；通常完成時間須另據可核驗的資料限定。  flagging family: openai (imprecise)
arbiter: agrees=true — 依提供的基準與 source-evidence，Sonnet 原價為輸入 2 美元、輸出 10 美元，兩者半價確為 1 美元及 5 美元。但所附證據只支持非同步批次及折扣，沒有提供足以判定通常完成時間分布的資料。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch06-reliability-and-durable-execution.md — fixed
claim: 兩個版本執行範例後，第一次記錄 3 筆 Checkpoint，核准後累積 6 筆，最終狀態為 completed，且不重複呼叫 LLM。
verifier value: 依所述事件設計預期為 3 筆及 6 筆；實際輸出與是否重複呼叫 LLM 須檢視完整程式並執行驗證。  flagging family: openai (imprecise)
arbiter: agrees=true — 依章節列出的預期事件，可算出第一次 3 筆，接著增加 hitl_resume、tool_call、completed 3 筆，合計 6 筆。但提供的程式碼片段不含完整流程及兩個版本的實際執行結果，無法獨立確認輸出或 LLM 呼叫次數。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 對於自由文字回覆與存在多條合法工具路徑的場景，傳統的精確字串比對斷言會全面失效。
verifier value: 單一預期字串的整體精確比對通常不足以評估多種合法措辭或路徑；可確定的欄位與契約仍適合精確檢查。  flagging family: openai (imprecise)
arbiter: agrees=true — 只要輸出有多種可接受措辭，拿單一預期字串做整體比對確實可能把正確答案判為失敗；但這不能推出精確比對在所有此類場景都失效。可用明確列舉的合法結果、正規化後的欄位，或其他確定性條件檢查可判定的部分。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 傳統 API 只要單一端點通過測試就代表穩定。
verifier value: 單一端點通過測試只證明已測條件下的指定行為符合斷言，系統穩定性仍須綜合其他證據評估。  flagging family: openai (incorrect)
arbiter: agrees=true — 單一端點通過測試只能支持它在該次測試條件下符合所測斷言，不能推得未覆蓋情境、重複執行、依賴服務或生產環境都穩定；章首也已承認穩定性須依覆蓋、重複執行與運行資料評估。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: 對 Haiku 5.5 與 Sonnet 5.5，應省略 temperature、top_p、top_k。
verifier value: 部署前應依當時各模型及所選思考模式的官方參數文件確認可用設定；所附證據不足以確立一律省略。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的 source-evidence 記載了結構化輸出與 extended thinking，但未記載這兩個模型對 temperature、top_p 或 top_k 的支援限制。僅依所附材料無法判定三個參數都必須省略，也無法判定限制是否依思考模式而異。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch07-evals-and-systematic-tuning.md — fixed
claim: EVAL-003 未通過時，程式會以非零 exit code 1 結束，並輸出總評測成本 $0.2097。
verifier value: 若 EVAL-003 的三次結果確為兩次通過、一次失敗，則其 Pass@3 為 1、Pass^3 為 0；實際成本與退出碼須核讀或執行完整範例才能確認。  flagging family: openai (imprecise)
arbiter: agrees=true — 所附程式片段只能顯示布林試驗結果如何計算 Pass@k 與 Pass^k，以及簡化軌跡檢查；它沒有提供完整模擬器、用量計費或程序退出邏輯。因此無法從材料獨立驗證範例實際輸出、總成本或退出碼。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 用可驗算的工程帳本，把月成本壓進 ≤ $18,000，同時守住分流 p95 ≤ 2.5 秒與多步工具處置 p95 ≤ 18 秒的延遲 SLO。
verifier value: 在所列假設下估算模型 token 費用約 $14,789.55／月；是否達成完整成本目標與兩項延遲 SLO，須納入額外成本並以實際工作負載驗證。  flagging family: openai (imprecise)
arbiter: agrees=true — 帳本證明的是特定假設下的模型 token 費用情境，並未證明實際工作負載可達成。Stage 5 的回合數、token 數與快取占比均待實測；摘要、升級、重試及平行護欄等額外成本也未在該情境中明確計入。此外，設定 16 秒總期限本身不能證明分流與多步處置的 p95 均達標，還需要包含排隊、失敗及峰值流量的端到端量測。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 將 current_time 或動態 ticketId 放進 System Prompt 開頭，或每次動態組裝工具陣列順序，會導致每次請求前綴都不同。API 仍回傳 200 OK，但 usage.cache_read_input_tokens 永遠為 0。
verifier value: System 中的動態值會使該變動點及其後的前綴失效，但較前面的工具前綴仍可能命中；工具順序若改變，則會影響變動點及其後的快取。  flagging family: openai (incorrect)
arbiter: agrees=true — 提供的證據指出比對順序為 tools → system → messages，較早區塊變動會使其後的斷點失效。若只有 system 開頭的動態值改變，而 tools 不變且工具末端已有可命中的快取斷點，工具前綴仍可能命中；因此不能推論整個請求的 cache_read_input_tokens 永遠為 0。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch08-cost-and-latency-optimization.md — fixed
claim: 若間隔超過 1 小時，則應改回 5m TTL，避免白白多付 2.0× 寫入費卻無法命中。
verifier value: 間隔超過 1 小時代表不能依賴該兩次請求之間的 1h 快取命中；仍須比較工單內各回合與其他共用前綴請求的間隔及命中情形。  flagging family: openai (imprecise)
arbiter: agrees=true — 若每次工單只有一次請求，且跨工單間隔超過 1 小時，兩種 TTL 都無跨工單命中，5m 冷寫入的 1.25× 確實低於 1h 的 2.0×。但本章設定每筆工單有多回合，同一工單內仍可能命中；例如寫入後兩次讀取，1h 成本為 2.0 + 2 × 0.05 = 2.1×，5m 若三次皆冷寫入則為 3.75×。僅憑跨工單間隔無法決定 TTL。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: 若主模型在後續回合才因工具回傳結果觸發注入，則由 Layer 2 與 Layer 4 接手攔截。
verifier value: Layer 2 可降低資料被誤認為指令的風險；Layer 4 可阻止其政策涵蓋的未授權工具操作。工具結果注入及其後果仍須搭配唯讀授權、欄位投影、輸出與出站控制，並以評估量測防護效果。  flagging family: openai (incorrect)
arbiter: agrees=true — Layer 2 以標籤和系統提示區分資料與指令，但模型仍可能遵循不可信內容；Layer 4 則依確定性政策檢查工具呼叫，不能判定或攔截所有注入造成的行為。例如，模型可能透過已授權的唯讀工具取得資料後，在回答中洩漏內容。章節其他地方也指出，唯讀外洩與輸出內容需要各自防禦。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: 切勿將動態工單或時間戳記放進前綴，否則會導致快取靜默失效（cache_read_input_tokens 歸零且 cache_creation_input_tokens 暴增）。
verifier value: 將動態內容放在需要重用的快取斷點之後；若它出現在某斷點所涵蓋的前綴內，其變動可能使該斷點及後續斷點無法命中，但較早的有效斷點仍可能命中。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的證據指出，較早區塊變動會使其後的快取斷點無效；但若動態內容位於較早的有效快取斷點之後，該斷點之前的穩定前綴仍可能命中。因此不能一概推論讀取量必然歸零、寫入量必然暴增；結果還取決於斷點位置、前綴是否相同及快取狀態。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: 高風險分數（> 0.90）才直接 block，模糊地帶（0.50–0.90）標記為 escalate 轉交人工。
verifier value: 明確定義完整分數範圍、各邊界、無效或缺失值的降級處理，以及 risk_score 與 decision 衝突時的優先規則；閾值須經代表性評估集校準。  flagging family: openai (imprecise)
arbiter: agrees=true — 這兩段規則涵蓋 0.50 以上的分數，但未說明低於 0.50 時如何決策，也未定義分數缺失、超出範圍或與模型回傳的 decision 不一致時的處理方式。由於章節將 risk_score 描述為未校準分數，不能僅從數值推定其意義。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch09-security-guardrails-and-governance.md — fixed
claim: 實際執行後，終端機應輸出所列的三筆紀錄、雜湊前綴與 Audit chain verified: True。
verifier value: 需檢視指定程式及其雜湊計算方式，並實際執行後才能確認輸出；目前只能將其視為章節宣稱的預期結果。  flagging family: openai (imprecise)
arbiter: agrees=true — 提供的材料只有預期輸出，沒有兩份範例程式的內容、雜湊輸入序列化方式或實際執行結果，因此無法獨立重算所列雜湊前綴，也無法判定兩種語言版本是否都會產生該輸出。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: 導致全 Sonnet 工作負載的快取失效並在 4 小時內維持 0% 命中，單筆成本退回「全 Sonnet、停用快取」基準 $0.1015。
verifier value: 若另外假設所有請求均使用 Sonnet、完全停用快取，且 token 消耗回到基準值，則單筆成本為 $0.1015；僅知道快取命中率為 0% 時無法確定事故成本。  flagging family: openai (imprecise)
arbiter: agrees=true — 題目先給正常狀態為「全套優化」，再假設事故狀態為全 Sonnet、停用快取。即使 0% 快取讀取成立，也不能單憑這個條件推得模型路由改為全 Sonnet或其他優化全部消失；若仍產生快取寫入，也可能有寫入附加費。$0.1015 因此是額外設定的事故情境成本，不能歸因於快取失效本身。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: 尖峰 12 req/s × 平均 5 回合 = 60 的單位是 LLM 呼叫／秒。
verifier value: 若 12 筆／秒的到達率持續且系統達到穩態，平均約需 60 次 LLM 呼叫／秒；瞬時尖峰與併發量仍須另行估算。  flagging family: openai (imprecise)
arbiter: agrees=true — 每秒到達 12 筆工單、每筆平均 5 次呼叫，長期平均需求可換算為每秒 60 次呼叫；但多回合呼叫分布在工單生命週期內，瞬時呼叫率受各回合延遲、流量變化、重試與併發影響，不能單憑工單到達率斷定尖峰瞬間必為 60 次／秒。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: 若該小時剩餘 50 分鐘回到日均速率，整小時約 $107.23；因此可將單次 10 分鐘尖峰的每小時熔斷閾值設在 $120–$150/hr。
verifier value: 題設下整小時約 $107.23；$120–$150 可作為該情境的候選閾值，仍須依時間窗、既有耗用、流量分布與併發情況校準。  flagging family: openai (imprecise)
arbiter: agrees=true — 10 分鐘尖峰消耗為 12 × 600 × $0.012 = $86.40；其餘 50 分鐘按每天 $600 的均勻速率消耗 $25 × 50 ÷ 60 = $20.83，合計 $107.23。算術成立，但 $120–$150 只適用於該固定小時窗中已包含這段尖峰、其餘時間如假設般運作的情境；既有耗用、尖峰跨窗、更多尖峰或併發結算都會改變所需閾值。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch10-observability-and-operations.md — fixed
claim: 當非同步 Worker 因超時觸發重試，或同一筆工單的兩個平行子任務同時回報完成時，若直接寫入帳本或重送外部寫入，會造成重複計費或重複退款。
verifier value: 帳本重複寫入可能造成重複歸因或扣減預算；再次實際呼叫上游可能新增費用；重送外部寫入可能造成重複退款。  flagging family: openai (imprecise)
arbiter: agrees=true — 同一費用事件重複寫入帳本會造成內部成本重複歸因或預算重複扣減，並不會單憑帳本寫入使供應商再次收費。另一次實際上游呼叫可能產生新的費用；重送退款等外部寫入則可能造成重複副作用。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: ch08 的 3,600-token 帳本相對基準約降 88.57%。
verifier value: 應明示：未套用 Batch 時，相對基準約降 88.57%；套用 Batch 後，依章節所列月成本約降 90.29%。兩個底數仍須核對 ch08 帳本。  flagging family: openai (imprecise)
arbiter: agrees=true — 章節同時列出同一帳本套用 Batch 後的 $14,789.55/月，以及移除 Batch 後的 $17,399.47/月。以 $152,250 為基準，前者降幅為約 90.29%，後者才是約 88.57%。原句沒有指出所用情境；此外，未提供 ch08 的逐項帳本，無法獨立驗證兩個月成本底數。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: Batch API 無法保證 15 分鐘內回傳。
verifier value: 應依官方 Batch 完成時限與服務條款確認；在沒有足夠期限保證與實測之前，不應假定 Batch 可滿足 15 分鐘要求。  flagging family: openai (imprecise)
arbiter: agrees=true — 所附證據支持 Batch 為非同步且輸入與輸出半價，但沒有提供完成時限或服務保證，不能僅憑非同步性質推導出其官方 15 分鐘保證條款。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch11-enterprise-patterns-in-action.md — fixed
claim: 在 DB 交易內認領同一業務操作並持久化 idempotency_key，對帳後再決定是否重送，可確保單筆訂單只扣款一次。
verifier value: 在金流端提供適當冪等保證、操作識別與退款額度控制正確，且對帳和重試流程可靠的前提下，可防止同一業務操作重複執行；部分退款須使用能區分各次合法操作的業務鍵。  flagging family: openai (imprecise)
arbiter: agrees=true — 資料庫認領可協調本系統中的併發，持久化 key 與對帳也能降低重送風險；但跨系統最終效果仍取決於金流端是否支援並正確執行冪等、其 key 的有效範圍及對帳可靠性。章節亦討論退款，而「單筆訂單只扣款一次」未區分扣款、退款及允許多次部分退款的業務情境。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 若 $18,000 為含 US 加價的硬上限，則階段四須將基礎單價壓低至 ≤ $0.010909/筆……否則 validateProductionConfig 會因 estMonthlyUsd = 18,150 > 18,000 阻斷部署，須先調高預算上限。
verifier value: 將基礎單價降至不超過約 $0.01090909／筆，或調高月預算上限；若必須維持 $18,000 硬上限，則須降價或減少計費量。  flagging family: openai (incorrect)
arbiter: agrees=true — 滿載月量為 50,000 × 30 = 1,500,000 筆，故含加價的基礎單價上限為 18,000 ÷ 1,500,000 ÷ 1.1 ≈ $0.01090909。原價 $0.011 確實會使月估算成本達 $18,150 並超出上限，但降低基礎單價也是通過成本檢查的方法，因此不一定須調高預算上限。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 在可觀測性儀表板設定 cache_hit_ratio < 0.70，定義為合格前綴在統計視窗內的 cache_read_input_tokens ÷ (cache_read_input_tokens + cache_creation_input_tokens)，並針對分母為 0 或預期可快取請求卻無快取讀寫的情形另設異常檢查。
verifier value: 將此值限定稱為快取讀取占已記錄快取讀寫 token 的比例；若要衡量全部合格前綴的命中率，另需估算或記錄未進入快取讀寫的合格前綴 token。  flagging family: openai (imprecise)
arbiter: agrees=true — 這個比率只涵蓋已記為快取讀取或建立的 token。即使另行偵測完全沒有讀寫的請求，部分請求中的合格前綴若有一部分既未讀取也未建立快取，仍可能被排除於分母，使比率無法代表所有預期可快取前綴的命中比例。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)

## [2026-11-21] ch12-production-readiness-blueprint.md — fixed
claim: 以下為 validateProductionConfig 的核心閘道邏輯，驗證延遲 SLO、成本上限與自主權等級的相依條件。
verifier value: 此節錄僅顯示部分相依條件；完整驗證應確認 Pass^3 為有效有限數值且達標，並在可機器驗證的範圍內檢查其餘 L1／L3 條件，或明確指出哪些條件須由其他控制驗收。  flagging family: openai (imprecise)
arbiter: agrees=true — 節錄中的 L3 條件只在 cfg.evalGate.passPow3 < 0.95 時拒絕；若數值為 NaN，這個比較會得到 false，因而無法由該條件拒絕無效評測值。節錄也未檢查章內要求的連續 14 天、零嚴重誤判、累計退款上限或 L1 無寫入憑證。由於完整實作未提供，不能判定這些檢查是否存在於其他程式碼中。
tiebreak: n/a
action: fixed in chapter (Round 1 adjudication)
