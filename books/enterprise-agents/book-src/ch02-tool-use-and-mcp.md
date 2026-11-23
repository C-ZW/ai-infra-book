# 第 2 章：Tool Use 契約、Strict Schema 與 MCP 企業整合

## 從你已知的出發

寫微服務時，你用 OpenAPI 定義端點契約，在閘道器擋掉缺欄位或型別錯誤的請求，並在金流寫入端點加上 `Idempotency-Key` 標頭，防止網路超時重試造成重複扣款。

把這套工程直覺帶進 Agent 系統，**契約與冪等性依然成立，但「呼叫端」換成了機率性的 LLM**：

- **成立邊界**：`Tool Use` 的 `input_schema` 就像 OpenAPI Spec，定義了參數型別、必填欄位與枚舉值；寫入型工具（例如 `issue_refund`）同樣需要確定性的冪等鍵（Idempotency Key）與 `dry_run` 預檢，才能在 Agent 重試或迴圈重播時不重複動帳。
- **失效邊界**：微服務的呼叫端是寫死的程式碼，收到 HTTP `400 Bad Request` 只能依錯誤碼決定重試、查詢狀態或告警；Agent 的呼叫端是模型，它會讀懂工具回傳的錯誤訊息並依錯誤類別處置（可修正的參數錯誤回填給模型重試、結果未知的寫入先查持久操作狀態、不可恢復的權限或政策違規直接轉人工）。因此，可修正的工具失敗不該直接拋出例外中斷迴圈，而必須將結構化的錯誤原因作為 `tool_result` 回填給模型。

在 `OrderOps` 主軸系統中，我們共有 **18** 個工具（**12** 個唯讀 Read-only 工具 + **6** 個寫入／金流 Mutating 工具），這些工具的 Schema 合計佔用 **3,600** tokens（加上 System Prompt **2,400** tokens，構成 **6,000** tokens 的基準前綴）。本章教你如何設計抗幻覺的工具契約、用 `strict: true` 與 `output_config.format` 鎖死型別，並將企業內部工具封裝為可水平擴展的 Stateless Streamable HTTP MCP Server，在支付商冪等契約覆蓋所有重試與對帳情境、且系統正確實作操作狀態與餘額保留時，可防止所涵蓋情境的重複動帳（實際仍須依支付商契約與故障測試驗證）。

---

## 核心機制

### 1. 工具面切分與抗歧義 Schema 設計

企業級 Agent 的第一個設計決策，是將「唯讀查詢」與「狀態變更／金流寫入」明確切分。`OrderOps` 的 **18** 個工具分為兩類：

```text
OrderOps Tools (18)
├── Read-only (12): get_ticket, get_order, list_customer_orders,
│                   get_shipment_tracking, get_inventory_level,
│                   get_warehouse_sla, get_refund_policy, get_invoice,
│                   list_payment_transactions, get_carrier_status,
│                   search_kb_articles, get_audit_log
└── Mutating  (6) : issue_refund, create_replacement_order,
                    update_shipping_address, cancel_order,
                    apply_store_credit, escalate_to_hitl
```

設計工具的 `input_schema` 與授權邊界時，必須遵守四個原則：

1. **枚舉約束取代自由字串**：例如退款原因 `reason_code` 必須限定為 `["shipping_delay", "damaged_item", "inventory_shortage", "invoice_error"]`，不能只寫 `type: "string"`。
2. **禁止多餘欄位**：所有物件一律加上 `additionalProperties: false`，並在 `required` 列出所有必要欄位，防止模型自行發明 `note` 或 `override` 等未定義參數。
3. **兩階段寫入契約與後端強制預檢**：金流與狀態變更工具內建 `dry_run: boolean`，模型應先以 `dry_run: true` 驗證政策上限與帳戶餘額，確認 `would_approve: true` 後再以 `dry_run: false` 提交。但**模型可直接送出 `dry_run: false` 或在預檢後篡改金額與訂單**，因此提交時後端必須驗證綁定 `(tenant_id, actor, operation, order_id, amount_usd)`（含原始付款識別碼及其他授權與政策判斷必要參數）的短效預檢紀錄，並在提交當下重查政策與可退餘額，同時禁止模型自行調降金額以繞過人工審批門檻。
4. **不可信資料隔離與身分授權**：工單內容、知識庫、MCP 工具描述與回傳結果皆視為不可信資料。`tenant_id` 必須從已驗證的身分上下文取得（而非信任模型填入的字串），依工具與資源逐次授權，並由後端產生操作鍵；人工審批（HITL）必須由可信工作流執行，最終 `refund_id` 與狀態一律以帳本為準。

### 2. Wire-Level Payload、`strict: true` 與 `output_config.format`

傳統的 JSON Schema 只是「提示」模型遵守格式，模型在長對話或高負載時仍可能漏掉必填欄位或輸出非法型別。Claude API 提供兩個層級的結構化保證：

- **Tool Input 強制契約（`strict: true`）**：在工具定義中設定 `strict: true`（搭配 `additionalProperties: false` 與完整的 `required` 陣列），API 會在解碼階段以受限採樣（Constrained Decoding）強制成功完成的 `tool_use.input` 符合支援的 JSON Schema 子集。實際支援的 JSON Schema 子集與限制須依相應版本的官方文件核對，且官方文件未承諾首次編譯必低於特定毫秒數；此外，金額上下限（如 `amount_usd > 0` 與小數精度）仍須在應用層驗證。
- **最終輸出強制契約（`output_config.format`）**：當 Agent 完成所有工具呼叫、準備輸出結構化決策給下游微服務時，設定 `output_config: { format: ... }`（可透過 TypeScript 的 Zod 或 Python 的 Pydantic 包裝，確切 wire 欄位與 SDK helper 簽章須依官方文件核對）鎖定最終 JSON 回應結構。在 `OrderOps` 中，最終輸出強制包含 `ticket_id`、`decision`（枚舉）、`refund_id`（必填且可為 `null`）、`amount_usd`、`confidence_score` 與 `summary`，並先檢查 `stop_reason` 與內容區塊 `type` 再解析。
- **迴圈終止條件（`stop_reason` 分支）與 Thinking 保留**：生產級 Agent Loop 必須顯式處理所有已記載的 `stop_reason`：`"tool_use"` 代表保留完整 assistant 內容（含帶簽章的 `thinking` blocks），並在緊接的單一 `user` 訊息開頭為每個本機呼叫回傳恰好一筆 `tool_result`；`"end_turn"` 代表完成推理；`"max_tokens"` 代表輸出截斷，若發生在 `tool_use` 中途必須丟棄該回合或重試；其餘官方文件記載的終止原因（如安全拒答或上下文視窗限制等）及任何未知 `stop_reason` 一律明確處置或轉人工。若需調整或停用思考模式，應依所使用模型與 API 版本的官方文件確認支援的 `thinking` 設定及錯誤行為，並以實測比較延遲。

以下為第 2 回合的 Wire-Level `tool_use` 回應範例（已有 `6,000` tokens 基準前綴命中快取，`1,200` tokens 為未快取的新增輸入，依第 5 節算例總輸入為 `7,200` tokens；省略 `role`、`model` 等外層欄位）：

```jsonc
// Assistant 回應（stop_reason: "tool_use"）
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "stop_reason": "tool_use",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lq9",
      "name": "issue_refund",
      "input": {
        "tenant_id": "TENANT-ACME",
        "order_id": "ORD-9042",
        "amount_usd": 45.0,
        "reason_code": "shipping_delay",
        "idempotency_key": "refund:TENANT-ACME:ORD-9042:TKT-101",
        "dry_run": true
      }
    }
  ],
  "usage": {
    "input_tokens": 1200,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 6000,
    "output_tokens": 350
  }
}
```

此外，Prompt Caching 的前綴匹配順序為 `tools → system → messages`。若僅將 `cache_control: { "type": "ephemeral" }` 放在最後一個工具上，只會快取 `tools`；要同時涵蓋固定的 `system` prompt，必須將斷點放在**最後一個固定 `system` 內容區塊**，並確保工具陣列順序、定義與 `system` 前綴在每個回合完全一致（快取命中屬 best effort）。

以下為 `issue_refund` 工具的 `strict: true` 定義（完整可執行程式見 `examples/ts/ch02/index.ts` 與 `examples/py/ch02/main.py`）：

```typescript
// examples/ts/ch02/index.ts
{
  name: "issue_refund",
  description:
    "Issue a customer refund. Always run with dry_run=true first to validate policy caps, then execute with dry_run=false and a deterministic idempotency_key.",
  strict: true,
  input_schema: {
    type: "object",
    properties: {
      tenant_id: { type: "string" },
      order_id: { type: "string" },
      amount_usd: { type: "number", description: "Refund amount in USD (> 0)" },
      reason_code: {
        type: "string",
        enum: ["shipping_delay", "damaged_item", "inventory_shortage", "invoice_error"],
      },
      idempotency_key: {
        type: "string",
        description: "Deterministic key: refund:<tenant_id>:<order_id>:<ticket_id>",
      },
      dry_run: { type: "boolean" },
    },
    required: ["tenant_id", "order_id", "amount_usd", "reason_code", "idempotency_key", "dry_run"],
    additionalProperties: false,
  },
}
```

### 3. 生產級儲存契約與配置基線

工具執行層的可靠性取決於外部共享狀態與全鏈路超時邊界，不能依賴單機記憶體：

- **全鏈路超時與併發基線**：單次 Messages API 請求設 `timeout = 30,000 ms`、唯讀工具 `5,000 ms`、寫入工具 `10,000 ms`，但**整條呼叫鏈必須共同執行 `18,000 ms` wall-clock deadline**（作為多步處置 `p95 ≤ 18s` SLO 的呼叫鏈預算；超時或轉人工工單是否納入分母與計算口徑須另行定義，並以實際延遲與結果分布驗證）：每次模型或工具呼叫都應以「剩餘 deadline」限制 timeout（包含 `Retry-After` 與 SDK 內建重試），剩餘預算不足時立即停止重試或轉人工，且 `max_turns = 8`。若 `12 req/s` 為工單進件率，5 回合穩態下約對應 `60` 次模型請求/秒（未計重試），工具併發、RPM、token 限額與連線池（如 `maxSockets = 64`、`keepAliveTimeout = 60,000 ms`）須依實際負載分別估算驗證。
- **端到端冪等與 PostgreSQL 帳本契約**：唯一索引只能保護資料庫寫入；若支付商已完成退款而程序在寫回帳本前崩潰，重試仍可能重複動帳。因此必須先以 `(tenant_id, idempotency_key)` 原子建立持久操作紀錄並比對正規化業務酬載雜湊，再將同一操作鍵傳給支付商，明確定義 `pending`、`succeeded`、`failed` 與 `unknown` 狀態轉移及對帳流程；同時在交易內鎖定或原子預留同一筆支付的可退餘額，避免兩個不同操作鍵超額退款。
  ```sql
  CREATE TABLE refund_ledger (
    refund_id        TEXT PRIMARY KEY,
    tenant_id        TEXT NOT NULL,
    order_id         TEXT NOT NULL,
    idempotency_key  TEXT NOT NULL,
    payload_hash     TEXT NOT NULL,
    amount_usd       NUMERIC(10, 2) NOT NULL CHECK (amount_usd > 0),
    reason_code      TEXT NOT NULL,
    status           TEXT NOT NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, idempotency_key)
  );
  ```
- **Redis 分散式租約與熱快取**：高併發重試時，先以 `SET idemp:refund:<tenant_id>:<order_id>:<ticket_id> <owner_token> NX EX 30` 搶佔 30 秒處理租約（釋放時須驗證持有者）；執行成功後寫入結果快取 `EX 86400`（24 小時 TTL），減少資料庫鎖爭用。

### 4. MCP 傳輸層演進與 Stateless Streamable HTTP

**MCP**（Model Context Protocol）將工具的「定義、探索與執行」從 Agent 程式碼中抽離為標準協定。在企業生產環境中，傳輸層的選擇直接決定了擴展性：

- **Stdio（本地子行程）**：適合本機開發與 CLI 工具，但無法跨容器共享連線，也不適合多租戶高併發部署。
- **Streamable HTTP（Stateless 模式）**：企業生產環境的標準選擇，可在負載平衡器後無狀態水平擴展（不依賴 Sticky Session）。即使不使用 `Mcp-Session-Id`，仍須依指定版本的 MCP 規範處理初始化生命週期（如 `initialize`、`notifications/initialized` 與 `tools/list` / `tools/call`）及對應的 HTTP 回應狀態碼與標頭，並驗證 `Origin` 標頭與請求大小上限。所有認證與租戶上下文（`Authorization`、`X-Tenant-Id`、`X-Trace-Id`）都必須隨每個 HTTP 請求完整傳遞。

此外，Claude API 支援透過 `mcp_servers` Connector（搭配 `tools` 中的 `mcp_toolset` 設定）由服務端直接連線至可公開存取的遠端 Streamable HTTP MCP Server，並以受限授權憑證（OAuth 2.1 / Bearer）傳遞身分（是否需要特定 beta 標頭與對應區塊型別名稱須依官方文件核對）。當企業需要細粒度工具權限過濾、動態注入已驗證 `tenant_id` 或統一稽核日誌時，仍建議由應用層代理處理初始化、HTTP 生命週期、逾時控制與工具派發。

### 5. 真實數字 Worked Example：Strict Schema 消除重試的成本帳

以下以 `OrderOps` 基準（**18** 個工具 Schema 共 **3,600** tokens、System Prompt **2,400** tokens、基準 **5** 回合、第 1 回合總輸入為 **6,000** tokens、其後每回合新增保留對話與工具結果 **1,200** tokens、每回合計費輸出 **350** tokens 含 thinking、Claude Sonnet 5.5 牌價 Input `$2.00 / MTok`、Output `$10.00 / MTok`）計算 `strict: true` 帶來的成本節省：

```text
1. 前綴與基準單筆成本（無快取，5 回合）：
   - 基準前綴 = 2,400 (System) + 3,600 (18 Tools) = 6,000 tokens
   - 第 1~5 回合輸入：6,000 + 7,200 + 8,400 + 9,600 + 10,800 = 42,000 tokens
   - 第 1~5 回合輸出：350 × 5 = 1,750 tokens
   - 基準單筆成本 = (42,000 × $2.00 + 1,750 × $10.00) / 1,000,000
                  = $0.0840 + $0.0175 = $0.1015 / 筆

2. 未開啟 strict: true 時的非法參數重試開銷（情境假設：12% 工單多出 1 回合且錯因可由 strict 消除）：
   - 額外第 6 回合輸入 12,000 tokens、輸出 350 tokens
   - 單次額外回合成本 = (12,000 × $2.00 + 350 × $10.00) / 1,000,000 = $0.0275
   - 平均每筆工單期望節省 = $0.0275 × 0.12 = $0.0033 / 筆
   - 放大至每日 50,000 筆工單：50,000 × $0.0033 = $165.00 / 天（情境估算 $4,950 / 月）
   - 實際延遲改善仍須以實測的錯誤分類、重試位置與延遲分布驗證。
```

（若要進一步透過工具動態裁切降低 **3,600** tokens 的前綴開銷，請見第 8 章的單位經濟學優化。）

---

## 故障模式與防禦

1. **HTTP `429` / `529` 與 Streaming 半途斷線殘缺 JSON**
   - **現象**：尖峰流量（12 req/s）時觸發 `429 Too Many Requests` 或 `529 overloaded_error`，或 SSE 串流在 `input_json_delta` 傳輸到一半時斷線，留下未閉合的 `tool_use` 區塊。
   - **防禦**：讀取回應標頭 `retry-after`（若無則採指數退避加 Full Jitter：`base = 500 ms`、`cap = 4,000 ms`、`max_retries = 4`），並受剩餘 wall-clock deadline 約束。串流應在完整訊息確認後才派發寫入；若已派發寫入且結果未知，應查詢持久操作狀態，絕不可整回合重播造成重複動帳。
   - **觀測與告警**：記錄 `http_status`、`retry_after_ms`、`stop_reason`；當 5 分鐘內（至少 100 次請求）`429`/`529` 比例超過 `2%` 時觸發限流告警。

2. **業務錯誤直接拋出例外，或遺漏 `tool_use_id` 配對**
   - **現象**：退款金額超過上限時開發者直接 `throw new Error(...)` 中斷迴圈，或未針對每個 `tool_use.id` 回填 `tool_result`，導致下一輪 API 回傳 `400 invalid_request_error`。
   - **防禦**：攔截可預期的業務錯誤，在 `tool_result` 設定 `is_error: true` 並回傳結構化 JSON（如 `{"error": "refund_exceeds_policy_cap", "max_allowed_usd": 100}`），同時設定 `max_consecutive_tool_errors = 3` 熔斷器，連續失敗 3 次即轉交 `escalate_to_hitl`。組裝下一輪 `messages` 前，以程式斷言檢查每個 `tool_use.id` 都有對應的 `tool_result`。

3. **冪等鍵衝突（Idempotency Collision）與並發競態**
   - **現象**：模型在 Turn 2 與 Turn 3 並發發出兩個相同 `idempotency_key` 的 `issue_refund` 請求，或以相同的 `idempotency_key` 夾帶不同的 `amount_usd` 重試。
   - **防禦**：Redis 租約搭配 PostgreSQL `UNIQUE(tenant_id, idempotency_key)` 攔截並發寫入，並比對正規化 `payload_hash`。若鍵相同但參數不同，回傳 `is_error: true`（`409 idempotency_payload_mismatch`），記錄 `idempotency_conflict_count` 並觸發 P1 告警。

4. **Prompt Cache 靜默失效（Silent Cache Miss）**
   - **現象**：`usage.cache_read_input_tokens` 持續為 `0`，`cache_creation_input_tokens` 每回合都大於 `0`，導致成本暴增。
   - **防禦**：檢查是否在工具 `description` 或 `system` 區塊中動態注入了時間戳記或工單 ID，或重新排序了 18 個工具。五回合基準的固定前綴總量雖為 `30,000 / 42,000 = 71.43%`，但若第一回合為冷啟動寫入快取、後四回合均命中，快取讀取量為 `4 × 6,000 = 24,000` tokens（占總輸入 `57.14%`）；僅當第一回合已命中既有快取時，五回合快取讀取才達 `71.43%`。因此監控應以**符合快取條件的前綴／請求**為分母設定 `80%` 告警（15 分鐘視窗），並另外追蹤總輸入快取讀取占比與冷啟動率。

5. **診斷日誌與可觀測性欄位基線**
   - 每次工具呼叫與 API 回應都必須寫入結構化 JSON 日誌，至少包含：`trace_id`、`tenant_id`、`turn`、`tool_name`、`tool_use_id`、`is_error`、`http_status`、`retry_after_ms`、`cache_read_input_tokens`、`cache_creation_input_tokens`、`latency_ms`（避免記錄原始憑證及敏感酬載）。服務層以 5 分鐘視窗（至少 50 次工具呼叫）統計 `tool_error_rate > 5%` 或 `p95 > 4,000 ms` 觸發告警，並按工具、租戶與錯誤類別聚合。

---

## 動手做

本章對應的範例程式路徑如下（請依實際檔案內容與本機執行結果驗證）：
- TypeScript：`examples/ts/ch02/index.ts`（含 `ORDEROPS_TOOLS`、`TicketResolutionSchema`、`IdempotentRefundExecutor`、Agent Loop 與 Stateless Streamable HTTP MCP Server）
- Python：`examples/py/ch02/main.py`（含 `ORDEROPS_TOOLS`、Pydantic `TicketResolution`、`IdempotentRefundExecutor`、Agent Loop 與 `ThreadingHTTPServer` MCP 端點）

### 執行 Python 範例與驗證輸出

```bash
cd books/enterprise-agents/examples/py
pip install -r requirements.txt
python3 -B ch02/main.py
```

未設定 `ANTHROPIC_API_KEY` 時，程式會自動執行本地的 `dry_run` → `commit` → `replay` 冪等去重測試；若已設定 `ANTHROPIC_API_KEY`，則會進一步執行完整 Agent Loop 驗證 `strict: true` 工具呼叫與 `TicketResolution` 結構化輸出（若啟用 Prompt Caching，呼叫 `calculate_cost_usd` 時須傳入對應的 cache usage 欄位）。預期輸出如下：

```text
Dry-run: ('{"dry_run": true, "would_approve": true, "order_id": "ORD-9042", "amount_usd": 45.0, "idempotency_key": "refund:TENANT-ACME:ORD-9042:TKT-101"}', False)
Commit: ('{"refund_id": "REF-...", "tenant_id": "TENANT-ACME", "order_id": "ORD-9042", "amount_usd": 45.0, "reason_code": "shipping_delay", "idempotency_key": "refund:TENANT-ACME:ORD-9042:TKT-101", "status": "approved"}', False)
Replay: ('{"refund_id": "REF-...", "tenant_id": "TENANT-ACME", "order_id": "ORD-9042", "amount_usd": 45.0, "reason_code": "shipping_delay", "idempotency_key": "refund:TENANT-ACME:ORD-9042:TKT-101", "status": "approved", "deduplicated": true}', False)
ANTHROPIC_API_KEY not set; skipping live Claude API call.
```

### 執行 TypeScript 範例

```bash
cd books/enterprise-agents/examples/ts
npm install
npx tsx ch02/index.ts
```

### 邊界測試與 MCP 端點驗證

1. **驗證 `dry_run` 不動帳與超限拒絕**：確認 `Dry-run` 不含 `refund_id` 且回傳 `would_approve: true`；金額超過 `$100` 時回傳 `would_approve: false` 與 `status: "pending_hitl"`。
2. **驗證冪等去重、同鍵異參與跨租戶隔離**：確認 `Replay` 的 `refund_id` 與 `Commit` 一致且帶有 `"deduplicated": true`；以相同 `idempotency_key` 傳入不同金額應回傳 `IDEMPOTENCY_PAYLOAD_MISMATCH`；不同 `tenant_id` 使用相同 `idempotency_key` 不應重播他租戶紀錄。
3. **驗證 Stateless MCP HTTP 端點**：啟動 MCP Server 後，依序發送 `initialize` → `notifications/initialized` → `tools/list` → `tools/call`（唯讀 `get_order`）：
   ```bash
   python3 -B ch02/main.py --serve
   # 另開終端機執行：
   curl -s -X POST http://127.0.0.1:8787/mcp \
     -H "Content-Type: application/json" \
     -H "Accept: application/json, text/event-stream" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'
   curl -i -s -X POST http://127.0.0.1:8787/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"notifications/initialized"}'
   curl -s -X POST http://127.0.0.1:8787/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
   curl -s -X POST http://127.0.0.1:8787/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_order","arguments":{"tenant_id":"TENANT-ACME","order_id":"ORD-9042"}}}'
   ```
4. **驗證負數與 `NaN` 金額邊界**：將 `amount_usd` 改為 `-10` 或 `NaN` 呼叫 `issue_refund`，確認帳本層回傳 `is_error: true` 且不寫入任何退款紀錄。

---

## 自我檢核

1. （**入門｜10 分鐘**） 為什麼在 Agent 系統中，工具執行遇到業務邏輯錯誤（如「退款金額超過上限」）時，應該回傳 `is_error: true` 的 `tool_result`，而不是直接拋出例外中斷程式？
2. （**進階｜15 分鐘**） `strict: true` 能保證什麼？它**不能**保證什麼？請以 `OrderOps` 的 `issue_refund` 工具為例說明。
3. （**挑戰｜20 分鐘**） 假設你的 `OrderOps` MCP Server 部署在 Kubernetes 上（3 個 Pod），前端透過 Load Balancer 輪詢發送請求。如果模型在 Turn 2 呼叫 `issue_refund(dry_run=true)` 命中 Pod A，Turn 3 呼叫 `issue_refund(dry_run=false)` 命中 Pod B，系統該如何確保冪等性與一致性？

### 參考解答

1. **解答**：在微服務中，呼叫端是確定性程式碼，收到例外只能依錯誤碼重試或告警；但在 Agent Loop 中，呼叫端是具備推理能力的 LLM。將結構化的業務錯誤透過 `is_error: true` 回填為 `tool_result`，等同於提供觀測訊號給模型，讓模型在下一回合修正參數或改為升級人工審批（`escalate_to_hitl`）。同時，Messages API 強制要求每個 `tool_use.id` 都必須有對應的 `tool_result`，若因例外中斷而遺漏配對，下一輪請求會直接回傳 `400 invalid_request_error`。工程上應搭配 `max_consecutive_tool_errors = 3` 熔斷器，避免模型陷入死循環。
2. **解答**：`strict: true` 在 API 解碼層透過受限採樣，保證成功完成的 `tool_use.input` 符合支援的 JSON Schema 子集結構、型別、必填欄位與 `enum` 約束（在 12% 情境假設下可望省下每月約 `$4,950` 的無效重試成本）。但它**不能**保證語意與業務邏輯正確——例如它無法阻止模型填入一個「型別正確但不存在的 `order_id`」，也無法驗證 `amount_usd > 0` 或是否超過該租戶的政策上限，因此後端仍必須執行 `dry_run` 預檢、範圍檢查與權限驗證。
3. **解答**：MCP Server 本身必須保持 Stateless，不將 `dry_run` 結果或冪等紀錄存在 Pod 本地記憶體，否則跨 Pod 路由時會發生狀態遺失或重複動帳。所有 `(tenant_id, idempotency_key)` 的鎖定與狀態紀錄必須寫入外部共享儲存：先以 Redis 租約搶佔處理權，再於 PostgreSQL 原子建立持久操作紀錄並以 `UNIQUE(tenant_id, idempotency_key)` 兜底與比對 `payload_hash`，將同一操作鍵傳給支付商並將結果快取 `EX 86400`（24 小時）。這樣無論 Turn 3 路由到哪一個 Pod，都能查詢到一致的帳本狀態，並在參數一致時回傳 `deduplicated: true`，參數不一致時回傳 `409` 衝突錯誤。

---

## 延伸閱讀

- Anthropic 官方文件：*Tool use with Claude*（`strict: true` 受限採樣與 `tool_result` 錯誤處理規範）
- Anthropic 官方文件：*Structured outputs*（`output_config.format` 與 JSON Schema 支援子集限制）
- Model Context Protocol (MCP) 規範：*Streamable HTTP Transport*（Stateless 無狀態傳輸模式與 JSON-RPC 2.0 雙向訊息格式）
