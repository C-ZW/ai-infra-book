## Verdict

**NEEDS_REVISION**

成本表的算術正確，但 **90.3% 只代表指定假設下的檢索片段輸入費降幅**。上線前必須修正三個核心問題：退款在崩潰與喚醒競爭下可能重複執行、快取斷點只涵蓋工具、引文驗證無法證明退款政策支持模型的結論。

我以提供的章文與工作區範例審查。Python 實跑符合預期輸出。TypeScript 透過 Node.js 的模組解析掛鉤執行成功，並重現 `$0.007100`。環境缺少 `tsx` 與 `tsc`，因此原指令與完整型別檢查仍未驗證。兩個範例都未呼叫 Claude API。

## Critical / Factual / Math Issues

1. **§2、故障模式 1／3、自我檢核 3｜把資料庫提交與退款副作用分開建模。** 工具成功後、寫入 `tool_result` 前崩潰，下一個 Worker 仍可能重送退款。呼叫前先用帶狀態條件的 CAS 檢查 `version`、`waiting_external` 與期限，並在同一交易寫入可恢復的操作紀錄。CAS 必須遞增版本並檢查是否更新一列。退款使用對應業務操作、跨推理重試穩定的 idempotency key。現有 `turn_count:tool_use_id` 可以辨識已保存的那次呼叫，模型重新產生呼叫時 ID 可能改變。下游逾時時要查詢既有結果或進入待對帳狀態。Webhook 以已驗證的來源與事件 ID 去重，事件經持久化接收後才回 `200`。到期排程與喚醒也須競爭同一狀態轉移，避免超時通知與退款同時成立。

2. **§1–2、動手做｜快取與資料庫需要明確的一致性契約。** PostgreSQL 提交後更新 Redis 仍有失敗窗口，舊讀取也可能在新寫入後回填舊版本。喚醒、授權及寫入決策應以資料庫為準，快取失效或回填須有版本保護。分開定義 Redis 的 24 小時 TTL、外部等待的 `expires_at`、資料留存期限。正式部署還需要 RLS 政策與交易內的租戶身分設定，應用角色須避免表擁有者或 `BYPASSRLS` 的繞過行為。保留獨立的操作紀錄，摘要時才能保住未完成工具配對、退款事實與稽核證據。 [PostgreSQL RLS](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)

3. **§4、故障模式 2、自我檢核 2｜分開驗證 ACL、檢索召回率與執行授權。** `WHERE` 可約束 SQL 回傳的資料列，但 pgvector 的近似索引可能先掃候選再套用過濾，合法結果仍可能少於 K。依 ACL 選擇性量測確切搜尋、分區索引或 iterative scan 的 recall@K 與 p95。複合 GIN 的 `text` 欄位需要對應 operator class，例如 `btree_gin`，`50 ms` 須有查詢計畫與壓測支持。租戶與角色由已驗證身分取得，`global` 文件由受信任的發布路徑管理。已授權的文件仍可能包含錯誤政策或 prompt injection。退款工具須獨立驗證工單歸屬、金額、政策版本與 HITL 門檻，並在續跑時重新檢查已撤銷的權限。 [pgvector 過濾](https://github.com/pgvector/pgvector#filtering) · [PostgreSQL `btree_gin`](https://www.postgresql.org/docs/current/btree-gin.html)

4. **§5｜保留算式，修正成本名稱與比較口徑。** 明定「每筆觸發工單只檢索一次、片段只在一次請求按未快取輸入計費」。多輪 Messages 會重送歷史，單次檢索也可能多次計費。若稱為端到端淨節省，須計入兩案的後續片段重送、快取寫讀、查詢改寫、工具呼叫與輸出、embedding／搜尋服務成本，並交代兩案的品質門檻。範例的 `$0.007100` 包含完整的 350 output tokens，只有在這 350 tokens 全是增量時才可稱為 delta。純檢索片段增量是 `$0.003600`。 [Claude 成本最佳化](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence)

| 核算項目 | 獨立重算 |
|---|---|
| 工作量 | `50,000 × 30 = 1,500,000` 筆／月。平均 `50,000 ÷ 86,400 = 0.578704 req/s`，峰均比 `12 ÷ 0.578704 ≈ 20.736×`，表中的 `20×` 是概數。 |
| 基準前綴與成本 | `12 + 6 = 18` 工具，`2,400 + 3,600 = 6,000` tokens。依表格口徑 `5 × (6,000 + 1,200 × (1+2+3+4+5) ÷ 5) = 42,000` input，`5 × 350 = 1,750` output。按 `$2/$10` 得 `$0.1015`／筆、`$5,075`／日、`$152,250`／月。若 `1,200` 排除重送的歷史模型輸出，五回合另有 `350 × (0+1+2+3+4) = 3,500` input tokens，基準變成 `$0.1085`／筆。請明定計量口徑。 |
| 靜態 RAG | `50,000 × 6,500 = 325 MTok`／日 → `$650`／日 → `$19,500`／月。 |
| Agentic RAG | `50,000 × 35% = 17,500` 筆／日，`17,500 × 1,800 = 31.5 MTok`／日 → `$63`／日 → `$1,890`／月。平均每筆工單 630 額外 tokens。 |
| 差額與目標 | `$587`／日、`$17,610`／月，`17,610 ÷ 19,500 = 90.3077%`。`$18,000 ÷ 1,500,000 = $0.012`／筆，相對全系統基準降 `88.1773%`。兩個百分比的分母不同。 |
| 快取、範例與自我檢核 | Sonnet `5m/1h` 寫入為 `$2.50/$4`／MTok，讀取 `$0.10`／MTok，6,000-token 前綴分別為 `$0.015/$0.024/$0.0006`。Wire 範例為 `(1,840 × 2 + 6,000 × 0.10 + 92 × 10) ÷ 10⁶ = $0.0052`，假設無快取寫入。程式為 `(1,800 × 2 + 350 × 10) ÷ 10⁶ = $0.0071`。自我檢核 `1,000 × 5` 得 `$0.01`／筆、`$500`／日，前提是五次均按未快取費率。 [Sonnet 5.5 定價](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) |

## Code & API Issues

1. **§3、故障模式 5｜移動 `cache_control` 斷點。** Claude 以 `tools → system → messages` 建立前綴。在最後一個工具設斷點只涵蓋工具，依章內數字約 3,600 tokens。要涵蓋穩定的 6,000 tokens，應放在最後一個穩定的 `system` 內容區塊。變動的 System Prompt 只會使涵蓋該段的前綴失效。有效但未命中的斷點可產生 `cache_creation_input_tokens > 0`，兩個欄位都為零應另查斷點、門檻與設定。固定前綴也須符合 TTL 與快取可見時機，數小時後喚醒不可假設仍命中。 [Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

2. **§2、故障模式 1／4｜補齊 Messages 重播契約。** client-side `tool_use` 的全部結果須一起放進緊接的 `user` 訊息，`tool_result` 區塊排在文字前。可以把未完成呼叫保存成工作紀錄，組裝 API 歷史時才要求配對完整。若 `pending_external` 已作為工具結果，後續 Webhook 應成為新的事件輸入。保存原始 assistant blocks，包括工具回合所需的 `thinking`／`redacted_thinking` 與簽章，將 TS 的 `createdAt` 等本地 metadata 留在 wire payload 之外。`stop_reason` 用來分派，`usage` 用來計量與執行預算政策。補上 `stop_sequence`、`refusal`、`model_context_window_exceeded`，以及使用相應服務端工具時的 `pause_turn`。串流收到 `message_stop` 後仍需檢查終止原因、完整區塊、schema 與授權，並處理 HTTP 200 後的 SSE `error`。SDK 與 Worker 的重試須共用總期限及次數預算。 [Tool use](https://platform.claude.com/docs/en/agents-and-tools/tool-use/implement-tool-use) · [Stop reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons) · [Streaming](https://platform.claude.com/docs/en/build-with-claude/streaming)

3. **§4、兩份範例｜引用驗證會放行漏引、格式錯誤與結論錯配。** regex 只收集符合格式的標記，零引文或小寫等未匹配標記會得到 `valid: true`。引用合法條文也可同時錯報金額。對政策型回答要求結構化的 claim 與來源 ID、條款和版本，明確處理漏引與無法解析的引用，並檢查關鍵主張。Claude `output_config.format` 可約束回覆 JSON，工具上的 `strict: true` 可約束工具名稱與參數。兩者都須搭配應用層檢查。自訂引用欄位可放進 JSON schema。Anthropic 原生 Citations 與 `output_config.format` 同用會回 `400`。 [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

4. **兩份範例｜檢索實作與章文不符。** 兩路都以詞彙交集計分。BF 式詞彙分數 `overlap/√文件詞數` 與第二路 `overlap/√(查詢詞數×文件詞數)` 對同一非空查詢只差固定倍率，因此兩路排序完全相同。範例 APAC 與全域條款分別命中 `5/1` 詞，詞彙分數約 `1.76777/0.37796`，第二路約 `0.72169/0.15430`，RRF 恰為 `2/61 ≈ 0.032787`、`2/62 ≈ 0.032258`。應實作真正的 BM25 和 embedding cosine，或明確標成單一詞彙訊號的 RRF 示意。TS 以 `docId` 查名次，會讓同文件不同條款共用第一個名次。兩版應統一 chunk ID、Unicode 斷詞、重複詞及同分規則，限制 `topK` 為有上限的正整數。零分候選目前仍會取得正的 RRF 分數，應允許回傳無證據。 [RRF 原始論文](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf)

5. **兩份範例｜「續跑」只改了物件。** 兩版都未保存 `active`、`turnCount = 3` 或清除 `waiting_for`，再次 `load` 仍會讀到舊狀態。補寫回並展示重新載入，可驗證最基本的續跑。若要展示本章的併發契約，還須加入帶版本的條件更新與衝突案例。TS 的固定到期時間 `2026-11-22T10:01:00Z` 會讓 demo 到期後直接失敗，應注入時鐘或從執行時間推算。TS 的冒號拼接複合鍵可碰撞，應用巢狀 Map 或無歧義編碼。Python 的 SQLite `:memory:` 僅能示範程序內儲存，且每次 `save` 會重置期限，應區分建立等待期限與一般狀態更新。 [TypeScript 範例](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/ts/ch04/index.ts) · [Python 範例](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/examples/py/ch04/main.py)

6. **API 適用範圍｜本章範例是本機模擬。** 兩份完整程式皆未使用 Anthropic SDK、MCP 或 Batch。若在 §2 補介面說明，Sonnet 5.5 預設 adaptive thinking，最低設定為 `between_tools` 且限 `high` effort 或以下。MCP Streamable HTTP 是傳輸層，Claude Messages MCP Connector 則使用 `mcp_servers`、相應的 `mcp_toolset` 和平台支援的 beta header。Connector 的伺服器工具區塊應依其協定續跑。Batch 的 Sonnet 標準輸入／輸出半價為 `$1/$5` 每 MTok，適用非同步工作，互動 SLO 與額外工具計費應另算。 [Sonnet 5.5 遷移說明](https://platform.claude.com/docs/en/models/sonnet-5-5/whats-new-sonnet-5-5) · [MCP 傳輸規格](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) · [Claude MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [Batch processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

## Clarity / Minor Suggestions

- **把設定值、案例條件與量測結果分開。** `86,400 s = 24 h`、`2,000 ms = 2 s`、`800 ms = 0.8 s`、`16,000 ms = 16 s` 均正確。若 `800 ms` 是每次檢索、允許初次加兩次改寫，串行檢索最多耗 `2.4 s`，尚需加上改寫、排隊與模型延遲。`500 ms` 起算四次 Full Jitter 的上界為 `0.5/1/2/4 s`，合計至多 `7.5 s`，`16 s` cap 不會觸發。標明適用 `2.5 s` 或 `18 s` SLO，以及 `retry-after` 的剩餘期限處理。
- **為其餘數字標示性質。** 連線池 `50`、`5–20`、讀取 `150 ms`、`512 KB`、告警 `0.5%/5 分鐘`、`15%`、連續超過三次衝突、`2%/3 分鐘`、命中率 `80%/5 分鐘` 都是設定值。補每 Worker 或全服務的口徑、位元組或 token 的限制、告警分母與最小樣本數。`35%`、`6,500/1,800` tokens 是情境假設。`72 h`、`$250`、`18%` 是範例資料。工單由 turn 2 到 3 正確，自我檢核 `10,000−9,990=10` 筆同租戶候選，單靠這比例無法推定 Top‑5 的實際失敗率。
- **收斂排序與資料庫類比。** RRF 的 `k=60` 源自原論文的 pilot，請說明名次從 1 起算、不在某路候選時該路貢獻為零，以及同分規則。`k1=1.2`、`b=0.75` 可列為 BM25 初始參數，Top‑3 品質須量測。PostgreSQL checkpoint 是 WAL 恢復的起點之一，應用程式從持久化狀態與操作紀錄決定續跑。 [RRF 原始論文](https://cormack.uwaterloo.ca/cormack/cormacksigir09-rrf.pdf) · [PostgreSQL WAL](https://www.postgresql.org/docs/current/wal-intro.html)
- **讓讀者重現結果。** 將作者本機 `file://` 連結換成可攜式相對路徑，補上 TS 範例目錄與依賴安裝步驟。除了現有的負 TTL、跨租戶引用與假 ID 案例，也展示同文件多條款、空結果、重複 Webhook，以及退款已成功但結果尚未寫入便崩潰的情境。