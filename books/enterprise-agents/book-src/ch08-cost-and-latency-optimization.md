# 成本與延遲優化：從 $152,250/月壓到 $18,000/月的工程帳本

`OrderOps` 上線後的第一張帳單往往會讓工程團隊震驚：日工單量 `50,000` 筆／天（`1,500,000` 筆／月，以 30 天計），若全部交給預設工作層 Claude Sonnet 5.5 處理且不開快取，每筆工單歷經 5 回合、累計消耗 `42,000` 輸入 tokens 與 `1,750` 輸出 tokens，單筆成本高達 `$0.1015`，每月帳單就是 `$152,250`。這章拆解五大降本槓桿與四大延遲優化手法，並用可驗算的工程帳本，在所列假設下將模型 token 費用估算壓至約 `$14,789.55/月`；至於能否達成完整的 `≤ $18,000` 月成本目標（單筆 `≤ $0.012`、降幅 `≥ 88.18%`；若僅達 88% 仍為 `$18,270/月`）與分流 `p95 ≤ 2.5` 秒、多步工具處置 `p95 ≤ 18` 秒兩項延遲 SLO，仍須納入摘要、升級、重試與平行護欄等額外成本，並以實際工作負載與端到端量測驗證。

## 從你已知的出發

做過「**雲端 FinOps 單位成本與 CDN 快取命中率**」的後端工程師，對請求合併、邊緣快取命中、冷熱分層並不陌生。Agent 系統的成本與延遲治理，在架構上與這兩者高度相似：

- **成立邊界**：Prompt Caching 就像把靜態資源推上 CDN——System Prompt 與工具 Schema 屬於「不變前綴」，只要前綴 byte-for-byte 一致，重複讀取就能從基礎輸入單價降到 `0.05×`（Sonnet/Opus 5.5）或 `0.10×`（Haiku 5.5）；Model Routing 則像 FinOps 的運算分層，把 60% 簡單分流交給低價節點（Haiku 5.5），只把 5% 高風險仲裁留給高階節點（Opus 5.5）。
- **失效邊界**：CDN 快取的是「最終回應」，而 Prompt Caching 快取的是「KV Cache 前綴狀態」。只要前綴裡任何一個字元（例如動態時間戳或隨機排序的工具清單）變動，快取就會從變動點之後整段失效；此外，LLM 輸出的邊際成本遠高於輸入（Sonnet 5.5 輸出 `$10.00 / MTok` 是輸入 `$2.00 / MTok` 的 5 倍），這在傳統 CDN 流量計費裡並不存在。

## 核心機制

### 1. 五大降本槓桿與 Wire-Level 契約

要將 `OrderOps` 月成本從 `$152,250` 壓到 `≤ $18,000`，單靠一招不夠，必須依序疊加五個工程槓桿（下節瀑布帳本將「工具分組精簡」與「回傳裁剪」合併為 Stage 3，並將「結構化輸出」獨立為 Stage 5）：

1. **Model Routing（模型分層路由）**：依據工單優先級與類別分流——60% 簡單工單（如一般物流查詢）走 Claude Haiku 5.5（`$0.10 / $0.50` per MTok，≤100K；`>100K` 為 `$0.50 / $2.50`），35% 標準工單走 Claude Sonnet 5.5（`$2.00 / $10.00`），僅 5% 高風險或 SLA 違約工單升級至 Claude Opus 5.5（`$4.00 / $20.00`）。路由決策必須在進入 `Agent Loop` 前完成，避免中途切換模型導致前綴快取全部作廢；若分流後才發現工單複雜度超出預期，只允許單向升級至高階模型並重設該筆工單的快取前綴，且需將升級與重設成本納入實測。
2. **Prompt Caching（前綴快取與 TTL 權衡）**：`OrderOps` 基準前綴為 `6,000` tokens（System Prompt `2,400` + 18 工具 Schema `3,600`），加上多回合對話歷史。在 Messages API 請求中，於 `system` 陣列最後一塊與 `tools` 陣列最後一個工具加上 `cache_control: { "type": "ephemeral", "ttl": "5m" }`（或 `"1h"`）。寫入快取需付 `1.25×`（5 分鐘 TTL）或 `2.0×`（1 小時 TTL），讀取僅需 `0.05×`（Sonnet/Opus 5.5）或 `0.10×`（Haiku 5.5）。5m TTL 在首次寫入後，只要在 5 分鐘內命中 `≥ 1` 次（即總計 `≥ 2` 次請求）就比兩次無快取便宜（`1.25 + 0.05 = 1.30 < 2`，Haiku 為 `1.35 < 2`）；1h TTL 適合離峰流量低於每 5 分鐘 1 次的長尾租戶，雖寫入需 `2.0×`，但能跨 1 小時保溫，避免每次請求都重新支付寫入溢價。快取比對順序為 `tools → system → messages`，因此工具分組變動也會連帶使後方的 `system` 前綴失效。
3. **Context Compaction 與工具回傳裁剪**：外部 API 回傳的訂單 JSON 常夾帶數千 tokens 的冗餘欄位（例如完整物流歷史陣列與內部稽核標籤）。在寫入對話歷史前，先以確定性投影（Projection）只保留必要欄位（如 `order_id`、`status`、`carrier`、`eta`），並對超過 3 回合的歷史觀測做摘要壓縮（需另行量測摘要本身的 token 成本），可將每回合新增輸入壓低，使 5 回合未快取輸入收斂至 `7,000` tokens。
4. **Batch API 50% 折扣與非同步對帳**：將非即時的對帳、發票稽核與批次補單轉入 `/v1/messages/batches`（非同步批次處理，實際完成時限與狀態碼依官方 Batch API 文件為準），Input 與 Output 同步半價（Sonnet 5.5 降至 `$1.00 / $5.00`），且可與 Prompt Caching 及地理倍率疊加（但 Batch 的快取命中率須獨立估算）。實作上以 `custom_id` 綁定批次內關聯識別，並於本地帳本另存 `batch_id`、`tenant_id`、`business_op_id` 與嘗試狀態；以示例輪詢間隔 `60s` 追蹤直到 `processing_status` 轉為 `ended`，再依 `custom_id` 處理順序不定的批次結果（如成功、失敗或取消等狀態，依官方文件為準）。永久驗證錯誤須先修正請求再重送；多步 client-tool 工作流仍須由外部編排工具執行與下一輪 Messages 呼叫，不能把單一 batch item 當成完整 `Agent Loop`。
5. **工具分組精簡與結構化輸出**：將 `18` 個工具（12 唯讀 Read-only + 6 寫入／金流 Mutating）依工單類別收斂為固定分組（平均 6 個工具，假設每個工具 Schema 約 `200` tokens，應以實際 Schema 驗證），前綴從 `6,000` 降至 `3,600` tokens。同時在工具定義加上 `strict: true` 約束參數，並在最終回應使用 `output_config.format`（`type: "json_schema"` 與 `schema`）減少格式重試；若啟用 Claude 5.5 的 adaptive thinking，可透過 `output_config.effort` 調整思考深度，並以實際 billed `output_tokens` 計價及保留工具續回合所需的原始 thinking blocks。

在 Wire-Level 層面，每次 Messages API 呼叫的快取斷點與計費欄位如下：

```json
{
  "model": "claude-sonnet-5-5",
  "max_tokens": 1024,
  "system": [
    {
      "type": "text",
      "text": "<static_orderops_policy_2400_tokens>",
      "cache_control": { "type": "ephemeral", "ttl": "5m" }
    }
  ],
  "tools": [
    {
      "name": "get_order",
      "description": "Fetch order summary by order_id.",
      "input_schema": {
        "type": "object",
        "properties": { "order_id": { "type": "string" } },
        "required": ["order_id"]
      }
    },
    {
      "name": "track_shipment",
      "description": "Fetch latest carrier tracking status.",
      "input_schema": {
        "type": "object",
        "properties": { "order_id": { "type": "string" } },
        "required": ["order_id"]
      },
      "cache_control": { "type": "ephemeral", "ttl": "5m" }
    }
  ],
  "messages": [{ "role": "user", "content": "Ticket T-8001: order ORD-9001 delayed." }]
}
```

API 回應的 `usage` 物件會明確區分三類輸入：`input_tokens`（未命中快取的新增輸入，含最後一則 `user` 訊息與工具回傳）、`cache_creation_input_tokens`（本次寫入快取的 tokens，乘以 `1.25×` 或 `2.0×`）與 `cache_read_input_tokens`（本次命中快取的 tokens，乘以 `0.05×` 或 `0.10×`）。單筆 Turn 的真實成本必須將這三者分別乘上對應倍率後加總，再加上 `output_tokens` 費用。此外，後端必須依據 `stop_reason` 決定迴圈分支：收到 `tool_use` 時等待完整參數並驗證後執行工具，再以匹配的 `tool_use_id` 回填 `tool_result`；收到 `end_turn` 時結束迴圈並寫入帳本；若收到 `max_tokens`、`stop_sequence`、`refusal`、`pause_turn`、`model_context_window_exceeded` 或 `compaction`，應各自走對應的截斷、拒答、續傳或壓縮處理分支，避免殘缺或拒答內容流入下游。

### 2. OrderOps 五階段降本瀑布帳本（Worked Example）

以下帳本以 `running-examples.md` 基準數字計算（`1,500,000` 筆／月，5m TTL 假設可快取前綴的 token 讀取占比為 90%、冷寫入 10%，實效讀取倍率為 `0.9 × read_mult + 0.1 × 1.25`，即 Haiku `0.215`、Sonnet/Opus `0.170`；中間值不捨入，金額採十進位四捨五入）：

```text
OrderOps 5 階段降本瀑布帳本（1,500,000 筆/月）
========================================================================
Stage 0: 基準線（全 Sonnet 5.5、無快取、5 回合：5×6,000 + 1,200×(0+1+2+3+4) = 42,000）
  - 單筆消耗: 42,000 input + 1,750 output
  - 單筆成本: 42,000*$2.00/1M + 1,750*$10.00/1M = $0.101500
  - 月成本  : $152,250.00（基準 0%）

Stage 1: Model Routing（60% Haiku + 35% Sonnet + 5% Opus）
  - Haiku 單筆 : 42,000*$0.10/1M + 1,750*$0.50/1M  = $0.005075
  - Sonnet 單筆: $0.101500 | Opus 單筆: $0.203000
  - 加權單筆   : 0.60*0.005075 + 0.35*0.1015 + 0.05*0.2030 = $0.048720
  - 月成本     : $73,080.00（累積降幅 52.0%）

Stage 2: Prompt Caching（30,000 cached + 12,000 uncached, 90% 讀取占比）
  - Haiku 等效 input : 30,000*0.215 + 12,000 = 18,450 -> 單筆 $0.002720
  - Sonnet 等效 input: 30,000*0.170 + 12,000 = 17,100 -> 單筆 $0.051700
  - Opus 單筆        : $0.103400
  - 加權單筆         : $0.024897
  - 月成本           : $37,345.50（累積降幅 75.5%）

Stage 3: 工具分組精簡（5×3,600 = 18,000 cached）+ 回傳裁剪（7,000 uncached）
  - Haiku : $0.001962 | Sonnet: $0.037620 | Opus: $0.075240
  - 加權單筆: $0.0181062 -> 月成本: $27,159.30（累積降幅 82.2%）

Stage 4: Batch API 50% 折扣（假設佔成本加權 30% 之工作負載轉入 Batch，整體倍率 0.85）
  - 加權單筆: $0.01539027 -> 月成本: $23,085.41（累積降幅 84.8%）

Stage 5（待實測驗證情境）: 結構化輸出精簡（平均回合 5 -> 3.5，輸出 1,750 -> 1,050）
  - 輸入: 13,500 cached（3.5×3,600=12,600 + 900 對話前綴）+ 4,500 uncached；輸出: 1,050
  - 折扣前單筆: Haiku $0.00126525 | Sonnet $0.024090 | Opus $0.048180
  - 疊加 0.85 倍率後單筆: $0.0098597025（<= $0.012 目標）
  - 月成本                    : $14,789.55（<= $18,000 目標，累積降幅 90.3%）
  - 敏感度提示: 若僅 30% 單量且全屬 Haiku 低優先發票工單走 Batch，月成本為 $17,114.79
    （全量 us 駐留則為 $18,826.27，將超出 $18,000 目標）；若沿用 0.85 倍率且全量啟用
    inference_geo="us"（1.1×）為 $16,268.51/月，單改 1h TTL 為 $16,028.85/月，
    兩者並用為 $17,631.74/月。
```

### 3. 延遲拆解、計費帳本 Schema 與四大優化手法

單次生成的串流近似時間為 `TTFT + (N − 1) × TPOT`（`TTFT` 為首字延遲、`TPOT` 為每輸出 token 耗時）；端到端回應還包含佇列等待、工具執行、護欄檢查與多回合往返。要守住分流 `p95 ≤ 2.5` 秒（須另定低於 `2.5s` 的分流預算）與多步處置 `p95 ≤ 18` 秒，單靠固定 `10s` LLM timeout 與 5 回合上限（最壞 `50s`）並不夠，必須以**剩餘 deadline** 限制每一步驟，將單一工具 timeout 設為 `3s`、總 wall-clock 上限設為 `16s`（保留 `2s` 緩衝給網路與序列化），並以峰值負載量測 TTFT、首個可安全顯示內容與端到端 p95。同時落實以下四項手法與基礎設施配置：

- **Streaming 漸進回傳**：開啟 `stream: true`，讓前端在 `TTFT`（示例為 300–600ms）後開始渲染。SSE 應合併 `message_start` 與累計的 `message_delta.usage`，並以 `message_stop` 或 SDK 完成訊號確認正常結束（HTTP 200 後仍可能收到串流 `error`）。斷線時僅能依已收 delta 估算並標記 `is_estimated = true`，帳本須保存 `request_id`、`attempt_id` 與完成狀態，再另行對帳。
- **平行 Tool Calls**：僅針對相互獨立的唯讀工具（如訂單主檔與物流追蹤）在單一 Turn 內發出多個 `tool_use` block，後端以 `Promise.all` / `asyncio.gather` 併發執行（單一工具 timeout `3s`，示例信號量併發上限 `16`），將 2 次獨立且可立即並行的 I/O（600ms + 600ms）壓縮為 `max(600ms) = 600ms`。
- **預取（Prefetch）與 Redis 快取鍵**：工單進入佇列時，依 `orderId` 先行非同步拉取訂單基本資料並寫入 Redis，鍵名為 `orderops:prefetch:{tenant_id}:{order_id}`，TTL 設為 `300s`，並定義資料鮮度、失效機制與快取命中後的租戶／訂單歸屬授權檢查。
- **Speculative 並行護欄**：在主模型開始推理的同時，平行送出輕量 Haiku 5.5 護欄檢查；必須在首段內容對外串流或執行工具動作前設置放行點，放行延遲取決於較慢的一邊（`max(main, guardrail)`）。所有工單內容、預取資料、摘要與工具回傳皆視為不受信任資料，除 Schema 驗證外，工具端仍須強制檢查租戶、訂單歸屬、權限與業務條件。
- **單位成本帳本 Schema（PostgreSQL）**：每筆可計費 attempt 完成後非同步寫入 `ticket_cost_ledger`，區分 `attempt_id` 與邏輯 `turn_index`，以唯一鍵確保冪等寫回，並提高小數精度避免逐筆捨入累積：

```sql
CREATE TABLE ticket_cost_ledger (
  id BIGSERIAL PRIMARY KEY,
  ticket_id TEXT NOT NULL,
  tenant_id TEXT NOT NULL,
  turn_index INT NOT NULL,
  attempt_id TEXT NOT NULL,
  request_id TEXT,
  is_estimated BOOLEAN NOT NULL DEFAULT FALSE,
  model TEXT NOT NULL,
  input_tokens INT NOT NULL,
  cache_creation_tokens INT NOT NULL DEFAULT 0,
  cache_read_tokens INT NOT NULL DEFAULT 0,
  output_tokens INT NOT NULL,
  cost_usd NUMERIC(12, 8) NOT NULL,
  latency_ms INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (ticket_id, turn_index, attempt_id)
);
CREATE INDEX idx_ledger_tenant_time ON ticket_cost_ledger (tenant_id, created_at DESC);
```

### 4. 併發限流、資料駐留與成本護欄

在 `12 req/s` 尖峰流量下，若不限制併發數，多租戶同時湧入會瞬間耗盡組織層級的 RPM、ITPM 與 OTPM 配額，引發連鎖 `429` 限流。工程上應分開限制全域／租戶在途量、模型 RPM／ITPM／OTPM 與工具併發，並為佇列設定容量上限與逾時：例如以 Redis Token Bucket 控制租戶速率（示例單租戶佔比上限 `25%`，即 `4` 個），並以 Worker Semaphore 控制本機在途量（示例 `16`；若 `16` 為全域在途上限，在 `12 req/s` 下僅容許平均約 `1.33s` 的占用時間）。

此外，若企業合約要求資料駐留於美國境內，必須在每次請求中明確傳入 `inference_geo: "us"`，此設定會對所有類別的 token 統一加上 `1.1×` 附加費率，且僅控制推論位置——合約若涵蓋資料儲存、保留與外部工具處理位置，仍須各自查核。路由層應將 `inference_geo` 設為租戶級屬性，僅對受法遵約束的租戶開啟，而非全域預設啟用。

## 故障模式與防禦

1. **Cache Silent Miss（快取靜默失效）**：將 `current_time` 或動態 `ticketId` 放進 System Prompt 開頭，會使該變動點及其後的前綴失效（但較前面的工具前綴若不變且末端已有可命中的快取斷點，仍可能命中）；若每次動態組裝工具陣列順序，則會使變動點及其後的快取（包含 `tools` 後方的 `system` 與 `messages`）一併失效。這類情況下 API 仍回傳 `200 OK`，但 `cache_read_input_tokens` 顯著下降甚至歸零、`cache_creation_input_tokens` 暴增，成本不降反升（寫入 `1.25×`）。**防禦**：固定將靜態 System Prompt 與依字典序排序後的工具定義放在前綴頂端並加上 `cache_control`，所有動態欄位一律放在最後一則 `user` 訊息。於結構化 log 記錄 `prefix_hash`、`cache_read_input_tokens` 與 `cache_creation_input_tokens`，當 5 分鐘滑動視窗的 `cache_hit_ratio < 0.70` 時觸發告警。
2. **低於快取最小門檻陷阱（Below Minimum Prefix Threshold）**：在 Claude API 的 Prompt Caching 中，已確認 `claude-opus-5-5` 的最小前綴門檻為 `512` tokens，而 Sonnet 5.5 與 Haiku 5.5 的確切門檻須依各模型官方文件分別查證。若工具分組裁切後的前綴低於對應模型門檻，API 不會報錯，但會靜默略過快取（`cache_creation_input_tokens = 0` 且 `cache_read_input_tokens = 0`）。**防禦**：在服務啟動時依各模型門檻分別驗證每個工具分組的基準前綴 token 數，並於監控面板追蹤 `cache_creation_input_tokens + cache_read_input_tokens == 0` 的異常比例（示例告警閾值 `> 5%`，5 分鐘視窗，以總請求數為分母）。
3. **429 / 529 尖峰限流與重試風暴**：`OrderOps` 尖峰流量達 `12 req/s`（基準平均 `0.58 req/s`，約 `20.7 倍`／基準標示為 `20×`）。TS SDK `maxRetries`（timeout 為毫秒）與 Python SDK `max_retries`（timeout 為秒）預設均為 `2` 次；若應用層負責重試，應停用 SDK 重試或合併計入同一剩餘 deadline。**防禦**：解析 `429` 回應的 `retry-after` Header，對 `529 overloaded_error` 採指數退避加隨機 Full Jitter（初始 `500ms`，倍率 `2×`，最多 3 次重試，等待上限依序為 `0.5 / 1 / 2s`、合計最多 `3.5s` 另加請求耗時），並嚴守總 wall-clock 上限 `16s`。當 `http_429_rate > 2%` 或 `http_529_rate > 0.5%`（1 分鐘視窗）時自動將低優先級工單降級至 Batch 佇列。
4. **Streaming 半途斷線與寫入冪等性衝突**：SSE 串流在送出 `message_stop` 前斷線，若客戶端直接重試會導致重複扣款或工具重複執行。`SET NX EX 300` 僅為短暫租約，無法防止逾時後重複寫入或供應商重複計費。**防禦**：對寫入與退款操作使用持久化業務冪等鍵（例如包含 `tenant_id`、`ticket_id` 與 `action_id`）、狀態機與對帳機制，並明確處理 timeout 後結果未知的狀態；斷線時依已收 delta 估算成本並標記待對帳，當 `sse_incomplete_rate > 0.5%`（5 分鐘視窗）時觸發告警。

## 動手做

完整可執行範例位於 [examples/ts/ch08/index.ts](examples/ts/ch08/index.ts) 與 [examples/py/ch08/main.py](examples/py/ch08/main.py)（兩份範例在本地驗證路由邏輯、工具分組與 Stage 5 瀑布計算，不直接呼叫 Claude API；若工具分組涵蓋 MCP，須區分應用程式作為 MCP client 使用 Streamable HTTP，與 Claude Messages API 透過 `mcp_servers`／`mcp_toolset` 代呼叫遠端工具的 Connector，並明定工具授權、租戶憑證與資料出境邊界）。以下節錄核心的 Model Router：

```typescript
export function routeTicket(ticket: OrderOpsTicket): RoutingDecision {
  if (ticket.priority === "critical" || ticket.category === "sla_breach") {
    return { model: "claude-opus-5-5", reason: "high_risk_escalation", batchEligible: false };
  }
  if (ticket.category === "invoice_discrepancy" && ticket.priority === "low") {
    return { model: "claude-haiku-5-5", reason: "offline_reconciliation", batchEligible: true };
  }
  if (ticket.priority === "low" || ticket.category === "shipping_delay") {
    return { model: "claude-haiku-5-5", reason: "standard_triage", batchEligible: false };
  }
  return { model: "claude-sonnet-5-5", reason: "standard_workflow", batchEligible: false };
}
```

執行以下命令即可驗證本地瀑布帳本計算結果：

```bash
python3 books/enterprise-agents/examples/py/ch08/main.py
npx tsx books/enterprise-agents/examples/ts/ch08/index.ts
```

預期輸出（Python 顯示至美分 `$14,789.55`，TypeScript 四捨五入至整美元 `$14,790`，單筆皆為 `$0.00986`、降幅 `90.3%`）：

```text
Routing: RoutingDecision(model='claude-haiku-5-5', reason='standard_triage', batch_eligible=False)
Waterfall: {'baseline_monthly_usd': 152250.0, 'optimized_monthly_usd': 14789.55, 'optimized_per_ticket_usd': 0.00986, 'reduction_pct': 90.3}
```

進階驗證建議：
1. 在 `simulateOrderOpsWaterfall` / `simulate_orderops_waterfall` 中分別或同時傳入 `ttl = "1h"` 與 `inference_geo = "us"`（`1.1×`），確認輸出月成本仍低於 `$18,000` 上限（單改 `1h` 約 `$16,028.85`、單開 `us` 約 `$16,268.51`、兩者並用約 `$17,631.74`／`$17,632`）。生產環境的計費 helper 還應依**單次請求**的總 prompt tokens 判定 Haiku `>100K` 階梯、支援 5m／1h 分開寫入量、Batch、geo 及費率版本，並拒絕未知模型的靜默 Sonnet 計價。
2. 驗證 `selectToolsForCategory` / `select_tools_for_category` 對五種工單類別回傳的工具清單皆依名稱字典序確定性排序，確保前綴 hash 穩定；同時檢查 `buildCachedPrefixBlocks` / `build_cached_prefix_blocks` 僅在 `system` 區塊與最後一個工具定義上標記 `cache_control`，符合單次請求最多 4 個快取斷點的上限。
3. 模擬 `priority = "low"` 且 `category = "invoice_discrepancy"` 的工單，確認 `batchEligible` 為 `true` 且路由至 `claude-haiku-5-5`；同時驗證 `priority = "critical"` 的工單強制升級至 `claude-opus-5-5` 且 `batchEligible` 為 `false`，避免高風險工單被誤送入非同步批次佇列。

## 自我檢核

1. （**難度：入門，預估時間：10 分鐘**） 若某租戶在離峰時段每 20 分鐘才進線 1 筆工單，使用 Sonnet 5.5（前綴 `6,000` tokens）時，應該選擇 `5m` TTL 還是 `1h` TTL？請列出算式比較。
2. （**難度：進階，預估時間：15 分鐘**） 在 `OrderOps` 中，為什麼「把輸出 tokens 從 `1,750` 壓到 `1,050`」對總成本與總生成時間的邊際效益，往往比單純縮減 `700` 個輸入 tokens 更高？
3. （**難度：挑戰，預估時間：20 分鐘**） 當工具數量從 `18` 個動態裁切為 `6` 個時，雖然單次輸入變小，卻可能導致不同工單類別之間的前綴不同而降低 Prompt Caching 命中率。你會如何設計快取鍵與分組策略來平衡這兩個指標？

### 參考解答

1. **TTL 選擇**：在「三次請求皆使用相同前綴、後兩次均命中，且 `5m` 情境三次皆為冷寫入」的假設下，每 20 分鐘進線 1 次時，`5m` TTL 每次都會過期，等於每次都付 `1.25×` 寫入費（單次 `6,000 × 1.25 = 7,500` 等效 tokens，3 次共 `22,500`）。改用 `1h` TTL 時，第 1 次付 `2.0×` 寫入（`12,000`），第 2、3 次各付 `0.05×` 讀取（各 `300`），3 次共 `12,600` 等效 tokens，省下 `44%` 前綴成本。但若僅有 2 次請求（`2.05×` 對 `2.5×`），或進一步納入單筆 5 回合與跨工單命中率，實際 TTL 選型應依相同前綴的回合數、請求間隔、命中率與冷寫入次數綜合比較，而非僅憑請求間隔判定；即便跨工單間隔超過 1 小時，也僅代表不能依賴該兩次請求之間的 1h 快取命中，仍須比較工單內各回合與其他共用前綴請求的間隔及命中情形，才能決定採用 `1h` 或 `5m` TTL。
2. **輸出壓縮效益**：以 Sonnet 5.5 為例，減少 `700` 個輸出 tokens 可省 `$0.007`（`$10.00 / MTok`），同量未快取輸入僅省 `$0.0014`（`$2.00 / MTok`），若輸入已命中快取（`0.05×` 即 `$0.10 / MTok`）更只省 `$0.00007`（輸出單價為快取輸入的 `100` 倍）。同時 `TPOT` 是每 token 耗時，在 `TTFT`、`TPOT` 及其他延遲條件近似不變的前提下，裁減 `700` 個輸出 tokens 可近似減少 `700 × TPOT` 的生成時間（實際效益仍須依實測確認）。實務上應以 JSON Schema 限制欄位名稱長度、移除冗餘解釋文字，並設定 `max_tokens` 上限防止模型過度發散。
3. **分組與快取平衡**：將 `18` 個工具收斂為 3–4 個高頻固定組合（例如 `read+shipping`、`read+refund`、`read+invoice`），而非為每張工單動態生成任意子集；並對每個組合內的工具依名稱字典序固定排序，同時維持寫入工具的最小權限。以 `50,000` 筆／天（全量平均 `34.72` 筆／分鐘、均分四組約 `8.68` 筆／分鐘）的流量為例，仍須依模型、部署範圍與冷啟動期間首個回應完成前的併發請求實測命中率，並以分組前後的實際 token 帳本比較節省幅度；若某長尾組合每 5 分鐘請求低於 2 次，則應暫時併入最接近的標準組合。

## 延伸閱讀

- [Anthropic Prompt Caching 官方文件](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- [Anthropic Message Batches API 指南](https://platform.claude.com/docs/en/build-with-claude/batch-processing)
- 本書 `ch09`：資料駐留 `inference_geo: "us"` 的合規條文與安全護欄實作
- 本書 `ch10`：將本章單位經濟學帳本串接至生產級可觀測性儀表板與成本告警規則
