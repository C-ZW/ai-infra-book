## Verdict

**NEEDS_REVISION**

場景 B 的 Batch payload 有兩處會被 Claude API 拒絕。場景 A 的退款流程無法保證外部金流只執行一次，場景 B、C 的驗證器也會放行缺乏支持的結論。成本表的主要乘法正確，但場景 A 引用的推導包含 Batch 折扣，場景 C 則以 Sonnet 單價計算混用 Opus 的架構。

已執行 Python 本機範例，並以 Node 的模組解析 hook 執行 TypeScript 範例。兩者的固定測資皆輸出一筆有效引用與一筆拒絕，並放行分診結果。工作區未安裝 `tsx`、`tsc`，所以正式 TS 執行指令與型別檢查尚未驗證。Claude API 相容性依官方文件查核，未發送實際請求。

## Critical / Factual / Math Issues

1. **A｜退款冪等性必須涵蓋金流端。** `UNIQUE(tenant_id, order_id, idempotency_key)` 只去除同一 key 的重送。兩個不同 key 仍可能為同一訂單建立退款，Redis 的 30 秒租約過期後也可能有兩個 Worker 同時執行。應在 DB 交易內保留退款額度、認領同一業務操作並持久化其狀態，向金流端傳送同一個持久化 key。遇到逾時、程序崩潰或狀態不明時，先對帳，再依金流端狀態決定是否重送。衝突時讀回 `pending`、`committed` 或終止狀態。自動退款與人工批准都應由後端重新檢查租戶、權限、幣別、金額及剩餘可退額度，並把批准綁定到該次操作。

2. **A｜即時架構缺少可重算的成本帳。** [ch08](/Users/theway.chen/Desktop/personal/ai-infra-book/books/enterprise-agents/book-src/ch08-cost-and-latency-optimization.md:74) 的最終帳採用縮減後的 `3,600`-token 前綴，並以 30% 離線流量乘上 `0.85`。移除 Batch 折扣後，按同一份最終使用量回推為 `$14,789.55 ÷ 0.85 = $17,399.47/月`，約 `$0.011600/筆`。這仍沿用 ch08 的前綴、回合與流量假設。本章的 `6,000`-token 即時設計須另列逐模型流量、每階段回合、cache read/write/miss、重試與 Opus 升級成本，交代 Haiku 分流是否為額外呼叫。`≥88%` 的比較基準應明確寫成全量 Sonnet、無快取。全量 Opus 若沿用同一 token 量，基準是 `$0.203/筆`、`$304,500/月`。

3. **A｜修正 Silent Miss 的公式與成本敘述。** 若指全部計費輸入中的快取讀取占比，分母應為 `cache_read_input_tokens + cache_creation_input_tokens + input_tokens`，並處理零分母。若要以 `85%` 偵測固定前綴失效，宜按模型與前綴版本統計合格請求的命中率。按五回合基準，即使 `30,000` 個前綴 tokens 全部命中，其占全部 `42,000` 個輸入 tokens 也只有 **71.43%**。在相同 Sonnet 工作量下，完全無快取為 `$152,250/月`，每回合都以 5 分鐘 TTL 重寫 `6,000` 前綴則為 **`$174,750/月`**，前綴全命中約為 **`$66,750/月`**（忽略首次寫入）。分層路由後遇到 miss，應依實際模型使用量估算。 [Anthropic Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)

4. **A｜延遲、吞吐與重試預算混為一談。** `20 req/s` 是速率；Worker 池應以同時在途工單數描述。尖峰 `12` 工單/s 若每單五次模型呼叫，持續尖峰下即有約 `60` 次模型請求/s，還要另計工具扇出與重試。八回合的模型等待上限相加為 `48s`，已超過 `18s`，三次 Full Jitter 重試若從 `500ms` 開始，等待上限合計 `3.5s`，還未計呼叫耗時或 `Retry-After`。應明訂全程截止時間、每步剩餘預算、排隊與背壓、SDK 與外層共用的重試上限，以及逾時、排隊、HITL 是否納入 SLO。 [Claude API 錯誤與重試](https://platform.claude.com/docs/en/api/errors)

5. **B｜「零漏讀」與「100% 阻斷未經原文支持的結論」超出驗證能力。** 空字串會通過 TS `includes("")` 與 Python `"" in text`。真實引文也可能與政策結論無關，或省略例外及交叉引用。應拒絕空引文，查驗文件版本與原文範圍，保留逐條處理狀態，並以條款清冊對帳。缺頁、解析失敗、條款缺漏、跨條款例外及有爭議的結論都要顯式標記並進入複核。`1,500–2,500` tokens 應寫成分段目標，並交代超長條款、表格及附錄如何保留來源位置。

6. **C｜證據與測試結果必須由受信任的執行元件提供。** 兩版程式都讓 `logs + sandbox_repro` 達到兩種來源門檻，並接受模型可自行填入的 `sandboxReproPassed`、時間戳與摘要。只計入已驗證的 `logs`、`metrics`、`trace`。以工具紀錄 ID 綁定環境、服務、incident 與查詢時間窗，並以 runner 紀錄綁定同一基準提交與修補版本，分別驗證修補前出現預期失敗、修補後通過。參考解答的 `[incidentStartTime − 15m, now]` 已排除所有未來時間，後面的 `now + 30s` 因此無效。應使用一個明確的上界與受信任的事件起始時間。

7. **A／B／C｜補上 Prompt Injection 與權限邊界。** 工單、合約、日誌、程式碼與 MCP 回傳都是外部資料。租戶、授權、查詢範圍、退款政策及證據來源由應用程式和服務端決定。唯讀工具仍須限制跨租戶查詢與敏感資料外洩。沙盒應由受控 runner 啟動，限制可執行入口、資源與掛載，避免將主機 socket、憑證或可寫主機目錄帶入。PR 發佈權限應隔離於沙盒之外。

8. **B／C｜算式成立的條件要寫進表內。** 場景 B 的 `18K/3.5K` 必須是**整份合約所有請求的計費加總**，含各條款重複帶入的政策、schema、交叉引用上下文，以及計費 thinking tokens。場景 C 的 `$316.80/月` 是全 Sonnet 情境。若 120 次/日都使用同樣 token 量、並將其中一部分完整換成 Opus，月成本為 `$316.80 × (1 + Opus 比例)`，全 Opus 為 `$633.60`。若 Opus 是追加呼叫，應另加它的實際 token 成本。兩個即時或夜間場景都須用實際排隊、配額與處理時間驗證交付時限。 [Anthropic 定價](https://platform.claude.com/docs/en/about-claude/pricing)

| 重算項目 | 結果 |
|---|---|
| A 流量與規模 | `50,000 × 30 = 1,500,000/月`。`50,000 ÷ 86,400 = 0.578704 req/s`，`12 ÷ 0.578704 = 20.736×`。`約 20×` 可作粗估。 |
| A 工具、前綴與五回合 | `12 + 6 = 18`，`2,400 + 3,600 = 6,000`。沿用 ch01 的首回合簡化，`Σ(6,000 + 1,200i), i=0…4 = 42,000`，`5 × 350 = 1,750`。若首回合也新增完整 `1,200`，則是 `48,000` 輸入 tokens。應註明首筆工單內容在帳本中的處理方式。 |
| A 未優化基準與上限 | `(42,000×2 + 1,750×10)/1M = $0.1015`，即 `$5,075/日`、`$152,250/月`。`$18,000 ÷ 1,500,000 = $0.012/筆`，相對降幅 **88.1773%**。`2.5s`／`18s` 與基準 SLO 相符。 |
| 牌價與倍率 | 官方牌價與基準表相符。Haiku `≤100K` 為 `$0.10/$0.50`，`>100K` 為 `$0.50/$2.50`。Sonnet `$2/$10`，Opus `$4/$20`。五分鐘／一小時寫入 `1.25×/2×`，Sonnet／Opus 讀取 `0.05×`，Haiku `0.10×`。Batch 半價後 Sonnet 為 `$1/$5`。`inference_geo: "us"` 的 `1.1×` 涵蓋所有 token 類別；若未加附費的成本剛好是 `$18,000`，加成後為 `$19,800`。 |
| B 合約與自我檢核 | Batch `$0.018 + $0.0175 = $0.0355/份`，`6,000` 份/月為 `$213`。即時 `$0.036 + $0.035 = $0.071/份`。`2,000 × 30 = 60,000` 份，Batch `$2,130/月`，即時 `$4,260/月`。如所有上傳都適用 15 分鐘要求，分級仍須符合該要求，或先修改服務承諾。 |
| C 分診與 ROI | `120 × 30 = 3,600` 次。全 Sonnet `$0.048 + $0.040 = $0.088/次`，即 `$316.80/月`。法務 `2h → 10m` 等於每份節省 `110m`、工時降幅 `91.67%`，目前是未附實測的假設。MTTR 沒有數值可驗算。 |

## Code & API Issues

1. **B｜兩個可獨立重現的請求格式錯誤。** Sonnet／Opus 5.5 使用 `thinking: {type: "enabled", budget_tokens: 2048}` 會收到 HTTP 400。改用 `thinking: {type: "adaptive"}` 或採用預設，以 `output_config.effort` 控制深度，並為 `max_tokens` 預留推理和最終 JSON 空間。簽章可用於保留或回送區塊，稽核應依政策版本、原文、決策與請求紀錄。`custom_id` 必須符合 `^[a-zA-Z0-9_-]{1,64}$`。正文的冒號與 TS 實際產出的 `MSA-2026-089__C-14.2` 中的句點都違規。使用批次內唯一、長度固定的合法 ID，持久化它與合約版本、條款和政策版本的映射。 [Anthropic Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) · [Create a Message Batch](https://platform.claude.com/docs/en/api/messages/batches/create)

2. **B｜請求沒有提供政策，也沒有定義結構化輸出。** TS 只送出 `against enterprise policy` 與條文，缺少受信任的政策正文、版本及 `output_config.format: {type: "json_schema", schema: …}`。兩版型別也未在執行時解析模型回傳。對 client tools，在各工具定義上用 `strict: true` 約束工具名稱與參數；對最終 JSON，用 `output_config.format`。兩者都需要業務驗證及拒絕、截斷處理。本章的 `verbatimQuote` 應明稱自訂引文字段。若同時啟用 Claude 原生 Citations 與 `output_config.format`，API 會回 400。 [Anthropic Structured Outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs)

3. **A｜快取斷點放錯位置，工具隔離也要反映在請求上。** 快取順序是 `tools → system → messages`。在最後一個工具加 `cache_control` 只涵蓋工具前綴。要納入靜態 System Prompt，把斷點放在最後一個靜態 system block。按模型與實際工具集合量測快取，分流及唯讀階段應省略寫入工具。收到多個 client `tool_use` 時，在緊接的 user 訊息開頭回傳各自配對的 `tool_result`，原樣保留所需 assistant thinking blocks。 [Anthropic Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) · [Anthropic Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking)

4. **A／C｜SSE 必須確認整則訊息完成後才派送工具。** `stop_reason !== "max_tokens"` 在 `stop_reason` 仍為 `null` 時也成立，部分資料也可能剛好能解析。應等到 `message_stop` 或 SDK 確認完整終態，處理 HTTP 200 後的 SSE `error`，再依允許的 `stop_reason` 分流。補上 `refusal`、`stop_sequence`、`pause_turn`、context 上限與未知狀態的處理。只有完整、通過 schema 與授權驗證的 client `tool_use` 才進入工具派送。 [Claude 串流事件](https://platform.claude.com/docs/en/build-with-claude/streaming) · [Sonnet 5.5 遷移指南](https://platform.claude.com/docs/en/models/sonnet-5-5/migration-guide)

5. **C｜說清楚 MCP 是應用程式代接，還是 Claude Connector 直連。** 應用程式以 MCP client 接 Streamable HTTP 時，可將 MCP `isError` 或傳輸逾時映射成 Claude client `tool_result.is_error`。若走 Messages API Connector，應寫明其 beta 版本、`mcp_servers` 與配對的 `mcp_toolset`、OAuth 與工具 allowlist，並處理 API 回傳的 `mcp_tool_use`／`mcp_tool_result`。Connector 需要可公開連線的 HTTP 端點，支援 Streamable HTTP 與 SSE，不適用 ZDR。內網遙測需據此選擇接法及資料暴露範圍。 [Claude MCP Connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector) · [MCP Streamable HTTP 規格](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/streamable-http.mdx)

6. **B｜24 小時是到期界線，批次結束仍須逐筆驗收。** `/v1/messages/batches` 和 `processing_status === "ended"` 正確。結果還有 `canceled`，且回傳順序不保證。應以 `custom_id` 對帳並冪等寫回，區分暫時性錯誤、永久的 payload 錯誤、取消及到期。`succeeded` 仍要檢查 message 的停止原因和資料結構。若讀取中斷，續跑時應可安全跳過已寫回條款。 [Anthropic Batch Processing](https://platform.claude.com/docs/en/build-with-claude/batch-processing)

7. **範例與正文驗收契約需要同步。** 正文把缺少來源與缺少引文合併為 `missing_source_or_citation`，兩個檔案則拆成 `clause_not_found` 和 `missing_verbatim_citation`。Python 沒有 Batch builder，也沒有印出 request count，分診結果是 `(True, 'ok')`。兩版的 `indexContractClauses`／`index_contract_clauses` 只映射已分段資料，重複 clause ID 會在建立索引時覆蓋，tokens 估算也分別使用向上取整與截尾。固定測資未走過 Claude SDK、Batch 結果處理、MCP 或沙盒。應明示範例涵蓋範圍，讓兩種語言的 payload 與驗證契約一致，並加入空引文、重複 ID、`logs + sandbox_repro`、缺少真實 runner 紀錄的負例。

## Clarity / Minor Suggestions

- 將 `$50`、`1,500ms`、`6s`、`8/10` 回合、`30s/120s`、`60s` 輪詢及 `85%`／`2%`／`0.5%`／`5%` 標成示例配置，交代適用範圍、分母、觀察窗、最低樣本量與超標動作。`45–90s` 若是同一工單中串行執行的兩次測試，兩次各限 `30s`，純測試執行最多 `60s`。若含容器準備、排隊或更多次執行，請列出組成。
- 將「真實數字」與 ROI 表中的估計值改成有明確假設的情境。法務初審和 MTTR 若要報成效，請補測量口徑、樣本，以及人工複核和沙盒等成本。單憑合約長度也無法推出「無法平行化」。
- 動手做的標點測試請指定可重現的替換，例如將 `7 days` 改為 `7 Days`。單源測試應保留 `logs + sandbox_repro`，才能抓到目前的計數漏洞。`POLICY-CAP-200` 可註明純為偽造引文測資，避免讀者誤以為程式會判定責任上限條款。
- 修正 ch06、ch08 的失效連結，實際檔名是 `ch06-reliability-and-durable-execution.md` 與 `ch08-cost-and-latency-optimization.md`。範例改用 repo 相對連結，方便其他讀者從自己的 checkout 開啟。