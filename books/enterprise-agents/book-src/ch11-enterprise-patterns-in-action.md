# 第 11 章：三大企業實戰場景深度拆解

## 從你已知的出發

前十章把企業級 Agent 系統的每個元件都拆開驗證過了：`Agent Loop` 狀態機（見 ch01）、`18` 個工具的唯讀與寫入權限切分（見 ch02、ch05）、`Prompt Caching` 與 Context 壓縮（見 ch03、ch08）、`HITL` 審批閘門（見 ch06）、`Eval` 與 `Pass^k` 回歸測試（見 ch07），以及可觀測性與安全護欄（見 ch09、ch10）。

單一元件通過測試，不代表組合起來就能在生產環境穩定運作。不同企業場景的瓶頸完全不同：客服與營運工單卡在「**高併發、低延遲與寫入冪等性**」；法務合約審核卡在「**長文本降低漏讀風險、條款原文強制引用與夜間批次降本**」；On-call 告警分診卡在「**多源遙測證據鏈與沙盒重現**」，一旦沒有證據鏈約束，模型就會用看似合理的推論掩蓋根因幻覺。

本章先收束主軸系統 `OrderOps` 的端對端生產架構，再橫向拆解「企業合約與法規合規審核助理」與「自動化 On-call 告警分診與程式碼審查 Agent」兩套截然不同的架構範本，最後以假設情境與基準數字對比三者的單位經濟學與 ROI，協助你在不同延遲、準確率與成本約束下做出正確的架構取捨。

---

## 核心機制

### 場景 A：`OrderOps` 跨系統營運與退款自動化

`OrderOps` 每天處理 `50,000` 筆工單（每月 `1,500,000` 筆，以 30 天計），平均流量 `0.58` req/s，尖峰流量達 `12` req/s（約 `20×`）。核心挑戰是把「高頻唯讀查詢」與「低頻高風險金流寫入」徹底隔離，在分流 `p95 ≤ 2.5s`、多步處置 `p95 ≤ 18s` 的延遲預算內，把月成本壓在 `≤ $18,000` USD（見 ch08；該章逐項帳本以縮減後的 `3,600`-token 前綴與 30% 離線 Batch 折扣計得 `$14,789.55/月`，移除 Batch 折扣後同用量為 `$17,399.47/月`、約 `$0.0116/筆`，其底數須依 `ch08` 逐項帳本驗證）。

```text
Ticket Ingress (50,000/day, peak 12 req/s)
  -> Haiku 5.5 Triage & Cacheable Prefix (6,000 tokens, p95 <= 2.5s)
  -> Read-Only ERP/WMS Query (12 Read-only tools, parallel, timeout 1,500ms)
  -> Risk & Policy Gate
       |-- amount <= $50 & idempotent -> Mutating Tool (6 tools, auto-execute)
       '-- amount > $50 or policy conflict -> HITL Queue (Opus 5.5 arbitration + human)
```

- **Wire 層快取與回合控制**：快取前綴順序固定為 `tools -> system -> messages`。在 `6,000`-token 前綴（System Prompt `2,400` tokens + `18` 個工具 Schema `3,600` tokens）中，必須把 `cache_control: { type: "ephemeral" }` 放在最後一個靜態 `system` block（而非僅放在最後一個工具），才能同時快取工具定義與靜態 System Prompt；分流與唯讀階段應省略寫入工具，並按模型與實際工具集合量測快取。回應端需等 `message_stop`（或 SDK 確認完整終態）後再依 `stop_reason` 分流：`tool_use` 進入工具執行、`end_turn` 結束迴圈、`max_tokens` 觸發截斷告警，並處理 `refusal`、`stop_sequence`、`pause_turn`、context 上限與未知狀態。收到多個 `tool_use` 時，在緊接的 `user` 訊息開頭回傳各自配對的 `tool_result`，並原樣保留所需的 assistant `thinking` blocks；若上游 ERP 逾時，回傳 `is_error: true` 與錯誤碼給模型決定降級或轉人工，絕不靜默吞掉錯誤。
- **具體配置基線（示例配置）**：`Agent Loop` 上限設為 `max_turns = 8`，單次 Messages API timeout 設為 `6,000 ms`，單一唯讀工具 timeout 設為 `1,500 ms`，整筆工單 wall-clock 截止時間設為 `18,000 ms`（對齊 `p95 ≤ 18s` SLO，含排隊與重試剩餘預算；`HITL` 人工等待時間另計）。注意 `12` 筆/s 尖峰若每單 5 次模型呼叫，持續尖峰即達約 `60` 次模型請求/s（另計工具扇出與重試）；`8 × 6,000 ms = 48s` 已超過 `18s`，因此每步必須傳遞剩餘 deadline、限制 SDK 與外層共用的重試上限（如 3 次 Full Jitter 重試等待上限合計 `3.5s`），並以同時在途工單數管理 Worker 併發池與背壓，而非單用 `20 req/s` 速率描述。
- **工具面與寫入冪等性**：`18` 個工具拆成 `12` 個唯讀（Read-only）查詢工具與 `6` 個寫入／金流（Mutating）工具（見 ch02、ch05）。工單內容屬不可信外部資料（須防範 Prompt Injection），租戶、權限、幣別、金額上限與唯讀查詢範圍均由應用程式與服務端強制驗證，唯讀工具亦須限制跨租戶查詢與敏感資料外洩。進入退款或改單前，僅靠 `UNIQUE(tenant_id, order_id, idempotency_key)` 只能去除同一 key 的重送，不同 key 仍可能重複退款，且 Redis `SET NX EX 30` 租約過期後仍可能有兩個 Worker 同時執行。正確做法是在 DB 交易內保留退款額度、以業務鍵（如 `(tenant_id, order_id, operation_type)`）認領同一筆退款操作並持久化其 `idempotency_key` 與 `status`（`pending` / `committed` / `failed`），再向金流端傳送同一個持久化 key。遇到逾時、程序崩潰或衝突時，先讀回既有狀態並向金流端對帳，再決定是否重送；自動退款（示例門檻 `≤ $50`）與 `HITL` 人工批准均須由後端重新檢查租戶、權限、幣別、金額與剩餘可退額度，並將批准綁定至該次操作。
- **分層模型與 `HITL` 取捨**：分流層用 `Claude Haiku 5.5`（`$0.10 / $0.50` USD / MTok，上下文 `≤ 100K`）壓低 `TTFT`；常規處置用預設工作層 `Claude Sonnet 5.5`（`$2.00 / $10.00` USD / MTok）；只有觸及 `amount > $50` 或跨系統帳務衝突時，才升級至 `Claude Opus 5.5`（`$4.00 / $20.00` USD / MTok）產生仲裁摘要並送入 `HITL` 佇列。相較於「全量 Sonnet、無快取」基準（`$152,250/月`、`$0.1015/筆`；若全量 Opus 5.5 同 token 量則為 `$304,500/月`、`$0.203/筆`），`ch08` 的 `3,600`-token 帳本在未套用 Batch 時（`$17,399.47/月`）相對基準約降 `88.57%`，套用 Batch 後（`$14,789.55/月`）則約降 `90.29%`（實際底數仍以 `ch08` 逐項帳本為準）；本章 `6,000`-token 即時設計的實際降幅須依完整生產帳本計算，另列逐模型流量、每階段回合、cache read/write/miss、重試、Opus 升級成本，以及 Haiku 分流是否為額外呼叫。

### 場景 B：企業合約與法規合規審核助理

合約審核與 `OrderOps` 相反：它不追求秒級回應，而是要求**降低漏讀風險**與**阻斷未附逐字引文的結論**。一份企業主服務協議（MSA）動輒數萬 tokens，直接整份塞進單次對話容易觸發 Context 衰減（見 ch03），也無法依條款粒度平行處理。

- **長合約切分與索引**：先以結構化剖析器依章節邊界切分為獨立條款（`ContractClause`，分段目標控制在 `1,500–2,500` tokens），建立 `clauseId -> 原文` 的記憶體或資料庫索引，並保留超長條款、表格與附錄的來源頁碼／區段位置，同時拒絕重複 `clauseId` 覆寫與標記缺頁、解析失敗。
- **`Adaptive Thinking` 與結構化輸出**：`Extended Thinking` 可透過 `thinking: { type: "enabled", budget_tokens: N }` 啟用，新模型亦可改用 adaptive 推理模式（具體模型支援度與參數限制須依官方 API 文件或實測確認），並以 `max_tokens` 預留推理與最終 JSON 空間。請求中必須附帶受信任的企業內規正文與版本，並以 `output_config.format: { type: "json_schema", schema: ... }` 約束輸出結構（原生 Citations 與 `output_config.format` 的相容性及錯誤碼須依官方文件或實測確認，本章採用自訂 `verbatimQuote` 欄位以確保結構化輸出與逐字驗證一致）。回傳的 `signature` 可用於保留或回送區塊，稽核應依政策版本、原文、決策與請求紀錄留存。
- **強制原文 `Citations`**：每筆風險發現（`ClauseRiskFinding`）必須附上至少一段非空、逐字引用的 `verbatimQuote`。後端驗證器直接比對 `c.verbatimQuote.trim().length > 0 && source.text.includes(c.verbatimQuote)`，只要為空或找不到逐字匹配就整筆退回。需注意逐字匹配仍無法單獨辨識「引文與結論無關」或「遺漏跨條款例外」，因此實務上仍須搭配條款清冊對帳與法務複核。
- **夜間 `Batch API` 批次掃描與取捨**：合約審核多屬非即時工作負載，可改用 `/v1/messages/batches` 端點排程掃描。`custom_id` 應採用批次內唯一、僅含英數字與 `-`/`_` 的正規化識別碼（如 `MSA-2026-089__C-14_2__0`；實際字元與長度限制須依官方 Batch API 文件確認），並持久化其與合約版本、條款和政策版本的映射。Batch 享 `50%` 折扣（`Claude Sonnet 5.5` 為 `$1.00 / $5.00` USD / MTok），排程器每 `60s`（示例配置）輪詢批次狀態，待 `processing_status === "ended"` 後下載結果檔（注意回傳順序不保證，且含 `succeeded`、`errored`、`canceled`、`expired`），依 `custom_id` 冪等寫回並驗證 `stop_reason` 與結構，以非同步排程換取半價成本（實際完成時限依官方 Batch 文件為準）。

以下為核心的引用驗證邏輯（完整可執行程式碼見 [examples/ts/ch11/index.ts](../examples/ts/ch11/index.ts) 與 [examples/py/ch11/main.py](../examples/py/ch11/main.py)；本機範例僅驗證引用與證據鏈規則，未實際呼叫 Claude SDK、Batch API、MCP 或沙盒）：

```typescript
export function validateCitations(
  findings: ClauseRiskFinding[],
  clauseIndex: Map<string, ContractClause>,
): { valid: ClauseRiskFinding[]; rejected: Array<{ clauseId: string; reason: string }> } {
  const valid: ClauseRiskFinding[] = [];
  const rejected: Array<{ clauseId: string; reason: string }> = [];

  for (const f of findings) {
    const source = clauseIndex.get(f.clauseId);
    if (!source) {
      rejected.push({ clauseId: f.clauseId, reason: "clause_not_found" });
      continue;
    }
    if (f.citations.length === 0) {
      rejected.push({ clauseId: f.clauseId, reason: "missing_verbatim_citation" });
      continue;
    }
    const allGrounded = f.citations.every(
      (c) =>
        c.clauseId === f.clauseId &&
        c.verbatimQuote.trim().length > 0 &&
        source.text.includes(c.verbatimQuote),
    );
    if (!allGrounded) {
      rejected.push({ clauseId: f.clauseId, reason: "citation_mismatch_or_fabricated" });
      continue;
    }
    valid.push(f);
  }
  return { valid, rejected };
}
```

### 場景 C：自動化 On-call 告警分診與程式碼審查 Agent

On-call 分診 Agent 面對的最大風險是「**根因幻覺**」：模型看到單一錯誤日誌就急著下結論，甚至產出修錯檔案的 PR。因此架構上必須強制把「觀測蒐證」與「受信任沙盒重現」綁成不可跳過的狀態轉移：

- **唯讀 `MCP` 遙測工具**：若由應用程式作為 MCP Client 透過 Streamable HTTP 連線內網唯讀 MCP 伺服器存取 `logs_query`、`metrics_range` 與 `trace_get`（見 ch02、ch09），可將 MCP `isError` 或傳輸逾時映射為 Claude client `tool_result` 的 `is_error: true`；若改採 Messages API MCP Connector 直連，則須設定 `mcp_servers` 與 `mcp_toolset`、OAuth 2.1／Bearer 驗證與工具 allowlist，且 Connector 僅支援遠端 Streamable HTTP 端點（不支援本地 `stdio`；ZDR 適用性與 beta header 要求須另依官方文件確認）。日誌、程式碼與 MCP 回傳皆屬不可信資料，工具紀錄 ID 須由服務端綁定環境、服務、incident 與查詢時間窗，嚴禁賦予 Agent 修改生產環境或跨租戶查詢權限。
- **隔離沙盒重現測試**：Agent 提出根因假設後，必須由受控 runner 啟動隔離容器（`--network=none`、無生產憑證、唯讀根檔案系統、限制入口與掛載，且 PR 發佈權限完全隔離於沙盒之外），執行測試（示例配置：單次測試 timeout `30s`、總迴圈 `max_turns = 10`、wall-clock 上限 `120s`）。runner 紀錄須綁定同一基準提交與修補版本，分別驗證「修補前出現預期失敗」與「修補後通過」。容器每次執行完畢立即銷毀，僅保留退出碼、標準輸出摘要與覆蓋率報告。
- **防根因幻覺的證據鏈規則**：系統強制檢查結構化輸出 `StructuredPrReview`，要求 `evidenceChain` 至少包含 **2 種以上不同遙測來源**（僅計入已驗證的 `logs`、`metrics`、`trace`，不計入 `sandbox_repro`），每筆紀錄皆須附帶 `source`、`timestamp` 與非空 `observedSnippet`，且必須具備受信任 runner 驗證通過的 `sandbox_repro` 紀錄與 `sandboxReproPassed === true`，否則自動攔截該份 PR Review。這項規則會增加額外分診耗時（兩次串行測試各自設有 `30s` 逾時上限，加上容器準備與排隊，實際耗時分布應以壓測或線上觀測估計），能攔截未符合指定證據要求的修補建議（但仍不能單靠規則保證根因或修補完全正確）。

---

## 故障模式與防禦

| 場景 | 典型故障模式 | 觀測指標／線索 | 工程防禦機制 |
|---|---|---|---|
| **場景 A (`OrderOps`)** | Webhook 重試或雙擊導致重複退款 | 同一 `orderId` 出現兩筆 `RefundResult` | DB 交易內認領業務操作並持久化 `idempotency_key`，對帳後再決定是否重送（見 ch06） |
| **場景 A (`OrderOps`)** | 尖峰 `12` req/s 觸發 `429` / `529` 雪崩 | `http_status` 出現 `429` 或 `529 overloaded_error` | 遵守 `retry-after` header，指數退避 + Full Jitter，與外層共用重試上限 |
| **場景 A (`OrderOps`)** | Prefix 變動導致 Cache Silent Miss | `cache_read_input_tokens = 0` 且成本暴增 | 斷點放在最後一個靜態 `system` block，按模型與前綴版本監控命中率 |
| **場景 B (合約審核)** | 模型改寫條款字眼或回傳空引文 | `citation_mismatch_or_fabricated` 比率升高 | 程式端拒絕空引文並執行 `source.text.includes(verbatimQuote)` 逐字比對 |
| **場景 C (On-call)** | 僅憑單一 Log 片段猜測根因並開出錯誤 PR | 遙測來源 `< 2` 或缺少受信任沙盒紀錄 | `verifyTriageEvidenceChain` 閘門強制雙遙測來源 + 受信任 runner 沙盒重現 |

1. **HTTP `429` 與 `529 overloaded_error` 尖峰雪崩（場景 A）**：`OrderOps` 在 `12` 筆/s 尖峰（持續尖峰約 `60` 次模型請求/s）時容易觸發 Rate Limit（`429`）或上游過載（`529 overloaded_error`）。防禦機制是優先讀取回應標頭 `retry-after`（單位秒），若無標頭則採用指數退避加 Full Jitter（示例配置：`base = 500ms`、`max = 8,000ms`、SDK 與外層共用最多重試 `3` 次，等待上限合計 `3.5s`）。Log 必須記錄 `http_status`、`retry_after_ms`、`attempt` 與 `request_id`；當 `429/529` 錯誤率連續 `5` 分鐘超過 `2%`（示例門檻，最低樣本 `100` req）時觸發 P2 告警，並將非緊急工單降級至佇列排隊。
2. **Streaming SSE 半途斷線與殘缺 JSON（場景 A / C）**：長輸出或網路抖動可能導致 `tool_use` 區塊在半途截斷；若只檢查 `stop_reason !== "max_tokens"`，在 `stop_reason` 仍為 `null` 時也會誤判通過。防禦機制是必須等到 `message_stop` 或 SDK 確認完整終態、處理 HTTP 200 後的 SSE `error`，並依允許的 `stop_reason`（含 `end_turn`、`tool_use`、`max_tokens`、`refusal`、`stop_sequence`、`pause_turn`）分流；只有完整且通過 Schema 與授權驗證的 client `tool_use` 才可派送。單小時 `stream_aborted` 比率超過 `0.5%`（示例門檻）即發出告警。
3. **Prompt Caching Silent Miss（場景 A）**：若誤把動態時間戳記或隨機 `request_id` 塞進 System Prompt，每次請求的前綴雜湊都會改變。在相同 Sonnet 五回合基準（`42,000` 輸入 tokens）下，完全無快取為 `$152,250/月`，每回合皆以 5 分鐘 TTL 重寫 `6,000` 前綴為 `$174,750/月`，前綴全命中約為 `$66,750/月`（忽略首次寫入）；分層路由後遇到 miss 應依實際模型使用量估算。防禦機制是將動態欄位全數移至最後一則 `user` 訊息，並在計費日誌以 `cache_read_input_tokens / (cache_read_input_tokens + cache_creation_input_tokens + input_tokens)`（處理零分母）計算快取讀取占比；注意五回合基準即使 `30,000` 前綴 tokens 全命中也僅占 `71.43%`，因此若要以 `85%`（示例門檻）偵測固定前綴失效，應按模型與前綴版本統計合格請求的命中率。
4. **引用偽造與單源遙測幻覺（場景 B / C）**：模型在長合約下可能對條款語意改寫，或在 On-call 分診時只看單一錯誤 Log 就推論根因。防禦機制是把 `validateCitations` 與 `verifyTriageEvidenceChain` 設為硬性閘門，在 Log 記錄 `rejected_reason` 與 `telemetry_sources_count`；當場景 B 單批 `citation_mismatch_or_fabricated` 超過 `5%`（示例門檻）時暫停自動產出報告並轉人工複核。
5. **雙擊競態與 `Batch API` 局部失敗（場景 A / B）**：`OrderOps` 遇到連點或併發重送時，應在 DB 交易內認領同一業務操作並持久化 `idempotency_key` 與狀態，向金流端傳送同一 key，逾時或衝突時先對帳或讀回終止狀態；在金流端提供適當冪等保證、操作識別與退款額度控制正確，且對帳與重試流程可靠的前提下，可防止同一業務操作重複執行（部分退款須使用能區分各次合法操作的業務鍵）。場景 B 的 `Batch API` 則可能出現單一 `custom_id` 失敗，排程器必須解析結果檔的 `result.type`（`succeeded` / `errored` / `canceled` / `expired`），區分暫時性與永久性錯誤，僅針對可重試的失敗 `custom_id` 補送重試，並支援讀取中斷時安全跳過已寫回條款。

### Worked Example：三大場景單位經濟學與架構橫向對比

以下帶入本書基準數字（`OrderOps` 日工單 `50,000` 筆、`Claude Sonnet 5.5` `$2.00 / $10.00`、`Claude Opus 5.5` `$4.00 / $20.00`、`Batch API` `50%` 折扣），在假設情境下對比三個場景的單次成本與月度規模（實際交付時限仍須以排隊、配額與處理時間驗證）：

```text
================================================================================
三大企業場景單位經濟學橫向對比（基準：2026-11 牌價，假設情境）
================================================================================
指標 / 場景        | 場景 A: OrderOps         | 場景 B: 合約審核             | 場景 C: On-call 分診
-------------------+--------------------------+------------------------------+-------------------------
日請求量           | 50,000 筆/天             | 200 份/天 (夜間批次)         | 120 次告警/天
平均 Context       | 6,000 前綴 + 1,200/回合  | 18,000 tokens/份 (整份加總)* | 24,000 tokens/次
選用模型組合       | Haiku + Sonnet (+Opus)   | Sonnet 5.5                   | Sonnet 5.5 + Opus 5.5**
Batch / Thinking   | Prompt Caching (無Batch) | Batch 50% + Adaptive Think   | Adaptive Think (即時)
-------------------+--------------------------+------------------------------+-------------------------
單次成本計算       | 優化後混合均價           | Input: 18K * $1.00/M         | 全 Sonnet 基準:
                   | <= $0.012 / 筆           | Output: 3.5K * $5.00/M       | Input: 24K * $2.00/M
                   | (ch08 未用Batch省88.57%)| = $0.018 + $0.0175           | Output: 4K * $10.00/M
                   | (見 ch08 推導與說明)     | = $0.0355 / 份               | = $0.0880 / 次
-------------------+--------------------------+------------------------------+-------------------------
月度 API 成本      | <= $18,000 / 月          | 200 * 30 * $0.0355           | 全 Sonnet: $316.80 / 月
(以 30 天計)       |                          | = $213.00 / 月               | 混用Opus: $316.80*(1+Opus比例)
-------------------+--------------------------+------------------------------+-------------------------
核心 ROI 槓桿      | 省下大量一線客服工時     | 假設法務初審 2h -> 10m       | 假設縮短 MTTR（須計入
(未附實測假設)     | (即時設計須依完整帳本計) | 夜間批次再省 50%             | 人工複核與沙盒等成本）
================================================================================
* 場景 B 的 18K/3.5K 為整份合約所有條款請求的計費加總（含重複政策、Schema、交叉引用與 thinking tokens）。
** 場景 C 若 120 次/日同 token 量並以部分 Opus 取代 Sonnet，月成本為 $316.80 * (1 + Opus 比例)（全 Opus 為 $633.60/月）；若 Opus 為追加呼叫，須另計其 token 成本。
```

---

## 動手做

本章完整可執行的 TypeScript 與 Python 程式碼位於：
- TypeScript：[examples/ts/ch11/index.ts](../examples/ts/ch11/index.ts)
- Python：[examples/py/ch11/main.py](../examples/py/ch11/main.py)

執行驗證步驟如下：

```bash
# TypeScript
cd books/enterprise-agents/examples/ts
npx tsx ch11/index.ts

# Python
cd books/enterprise-agents/examples/py
python3 ch11/main.py
```

執行後終端機應輸出以下驗證結果（以 TypeScript 為例，Python 輸出結構相同；兩者皆使用本地模擬資料，不需外部 API 金鑰即可重現）：

```text
=== Scenario B: Contract & Compliance Audit ===
Valid findings: 1
Rejected findings: [ { clauseId: 'C-14.2', reason: 'citation_mismatch_or_fabricated' } ]
Batch requests: 2, Sonnet standard=$2/$10, 50% Batch est=$0.0355

=== Scenario C: On-Call Triage & PR Review ===
Triage verification: { accepted: true }
```

建議接著做兩項邊界實驗：
1. **驗證引用偽造與空引文攔截**：在場景 B 的測試資料中，把 `C-19.1` 的 `verbatimQuote` 中的 `7 days` 改為 `7 Days`（或改為空字串 `""`），重新執行後應看到 `Valid findings: 0`，且 `C-19.1` 被歸類為 `citation_mismatch_or_fabricated`（註：`POLICY-CAP-200` 純為偽造引文測資）。
2. **驗證單源遙測與無沙盒阻斷**：在場景 C 的 `StructuredPrReview` 中，保留 `logs` 與 `sandbox_repro` 但刪除 `metrics`，重新執行後 `verifyTriageEvidenceChain` 應回傳 `{ accepted: false }`，確認 `sandbox_repro` 不會被誤計為遙測來源。

---

## 自我檢核

1. **（入門｜10 分鐘）** 在場景 B 的合約審核 Pipeline 中，為什麼不能只靠 System Prompt 要求模型「請務必逐字引用原文」，而必須在程式碼層執行 `validateCitations`？
2. **（進階｜15 分鐘）** 假設場景 B 的每日合約掃描量從 `200` 份成長到 `2,000` 份，且法務團隊要求改為「使用者上傳後 15 分鐘內必須看到結果」。這項需求變更會如何影響 `Batch API` 的使用？月度成本會變成多少？如何在不爆預算的前提下滿足法務需求？
3. **（挑戰｜20 分鐘）** 在場景 C 的 `verifyTriageEvidenceChain` 中，如果模型在 `observedSnippet` 裡填入一段「真實存在於 Log，但時間戳記是三天前、與本次 `INC-4092` 無關」的舊錯誤，現有檢查會放行嗎？請設計一個額外的欄位與驗證規則來防禦這類時間錯置幻覺。

### 參考解答

1. **Prompt 只是軟性約束，程式碼才是硬性邊界**：模型在長文本與高風險推理下仍可能把條款語意改寫（paraphrasing）、回傳空引文，或在 `Adaptive Thinking` 後產出看似合理但原文不存在的字串。`validateCitations` 以非空檢查與 `source.text.includes(verbatimQuote)` 作為確定性閘門，能阻斷未附逐字引文的風險結論進入法務報告；實務上可先將雙方字串做空白正規化（collapse whitespace）再比對，避免換行差異造成誤殺。
2. **失去 `Batch API` 50% 折扣，月成本翻倍**：`Batch API` 屬於非同步排程（完成時限與服務條款依官方文件為準）；在沒有足夠期限保證與實測之前，不應假定其可滿足 15 分鐘要求。若全數改為即時 Messages API，單份成本從 `$0.0355` 跳回標準價 `$0.0710`（Input `18K × $2.00/M = $0.036` + Output `3.5K × $10.00/M = $0.035`）。以每日 `2,000` 份、每月 30 天計算，月成本將從 `2,000 × 30 × $0.0355 = $2,130` 暴增為 `2,000 × 30 × $0.0710 = $4,260` USD。若所有合約皆須滿足 15 分鐘要求，必須為全部合約設計並驗證符合期限的即時處理與排隊流程；只有法務同意改採分級 SLA，才能僅針對「加急合約」走即時 API、其餘例行合約維持夜間 `Batch API`。
3. **若現有實作僅檢查欄位非空而未驗證受信任的 incident 與時間窗綁定，該舊紀錄可能放行；須檢視完整驗證流程才能判定**：防禦方式是在 `StructuredPrReview` 新增由系統注入的受信任 `incidentStartTime`（ISO-8601 時間戳記）欄位，並在 `verifyTriageEvidenceChain` 強制驗證每筆 `EvidenceRecord.timestamp` 必須落在 `[incidentStartTime - 15m, now + 30s]` 的單一明確時間窗內（以 `now + 30s` 作為微幅時鐘偏移的明確上界，同時防止未來時間偽造）；超出視窗即判定為無效證據並退回。

---

## 延伸閱讀

- [ch02 — Tool Use 契約與 MCP 權限切分](ch02-tool-use-and-mcp.md)：唯讀與寫入工具的架構邊界。
- [ch06 — 可靠性工程與持久化執行](ch06-reliability-and-durable-execution.md)：`Idempotency Key` 與人工介入佇列設計。
- [ch08 — 成本與延遲最佳化](ch08-cost-and-latency-optimization.md)：`OrderOps` 從 `$152,250` 壓降至 `≤ $18,000` 的完整成本推導。
- [ch12 — 從原型到上線：PRR 檢查表與演進路線](ch12-production-readiness-blueprint.md)：將本章三大場景推進正式生產環境的最終上線審查。
