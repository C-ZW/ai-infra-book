# 第 6 章 企業級可靠性：重試、熔斷、Checkpoint 與長任務執行

單機跑通一個 Agent Loop 只需要幾十行程式碼，但把這套迴圈放進企業生產環境，面對的卻是完全不同的物理現實：上游 LLM API 會在尖峰時段回傳 `429` 與 `529`、Streaming 回應會在吐出半截 JSON 時斷線、外部 ERP 或金流工具會逾時，而高額退款還必須暫停等待人工審批（Human-in-the-Loop，以下簡稱 **HITL**）。

本章為 `OrderOps` 建立企業級可靠性基礎設施：從雙層故障分類、感知 `Retry-After` 的指數退避與熔斷器，到 Event-sourced Checkpoint、Batch API 狀態追蹤與 HITL 暫停／喚醒狀態機，在持久化儲存、供應商冪等與查單等條件成立時，降低重複退款與進度遺失的風險；當結果不明且無法安全確認時，暫停自動重送並轉由人工對帳。

## 從你已知的出發

後端工程師對**熔斷器**（Circuit Breaker）與 **Transactional Outbox 模式**並不陌生：當下游付款閘道連續失敗達閾值，熔斷器切到 `OPEN` 狀態快速失敗，避免執行緒池被雪崩拖垮；而為了讓「寫入訂單狀態」與「發送退款事件」具備原子性，我們把事件寫進同一個資料庫交易的 Outbox 表，再由背景 Worker 非同步派送，配合 Idempotency Key 防止重複執行。

把這兩個機制映射到 Agent 系統，**成立邊界**在於「失敗隔離」與「副作用去重」完全相通：Agent 呼叫 LLM API 的行為等同於呼叫高延遲、配額受限的外部微服務，適用熔斷與退避；而 Agent 決定呼叫寫入型工具（例如 `issue_refund`）時，把決策寫入 Checkpoint 日誌再執行工具，正如同 Outbox 先落盤再派送。

**失效邊界**則出在「重試成本與狀態長度」：傳統微服務重試一次只需幾毫秒與幾百 bytes，但 Agent 每次重試整個 Turn 都可能重算數萬 tokens，且 Streaming 半途斷線時，模型已經吐出一半的推理內容與不完整的 `tool_use` JSON 參數，無法直接當作冪等結果重播，必須在 Checkpoint 邊界明確區分「LLM 推理中斷」與「工具已送出但未收到回執」。

## 核心機制

### 雙層故障分類：LLM 層與工具層

企業級 Agent 的錯誤處理必須把「LLM API 層」與「外部工具層」切開，因為兩者的失敗語意、HTTP 回應結構與重試代價截然不同：

1. **LLM API 層**：
   - `429 rate_limit_error`：觸及 RPM（Requests Per Minute）、ITPM（Input Tokens Per Minute）、OTPM（Output Tokens Per Minute）配額上限，或是流量爬升限制／支出上限。配額型回應標頭通常附帶 `retry-after`（秒數）以及剩餘配額與重設時間相關標頭（例如 `anthropic-ratelimit-*` 系列標頭，確切標頭名稱與格式依官方文件為準）；支出上限型 `429` 則可能沒有 `retry-after`，不應無止盡重試。
   - `529 overloaded_error`：供應商推理叢集暫時過載（例如回應主體帶 `overloaded_error` 類型，確切錯誤主體格式依官方文件為準）。此類錯誤屬於瞬態故障，可重試但需要較長冷卻視窗，且不應計入業務邏輯失敗。
   - **Streaming 半途斷線與停止原因**：SSE 連線須以 `event: message_stop` 確認正常結束，並依 `message_delta` 中的 `stop_reason` 決定下一步（完整回應仍可能是截斷、拒答或暫停等非正常結束原因，確切 `stop_reason` 列舉值依官方文件為準；HTTP `200` 之後也可能出現 SSE `error`）。若連線在 `message_stop` 前中斷，造成 `input_json_delta` 累積的 `tool_use.input` 出現殘缺 JSON，絕不能送進工具層，應丟棄該次殘缺輸出；確認未發生外部副作用後才重試整個 Turn（若使用 MCP Connector 等遠端代呼叫模式而可能已執行工具，應先查詢遠端狀態並依冪等保障決定是否重送或人工對帳）。
   - **非重試錯誤**：`400 invalid_request_error`、`401 authentication_error`、`403 permission_error` 與 `413 request_too_large` 屬於契約或權限錯誤，重試只會浪費配額，必須立即終止並標記為 `failed`。

2. **外部工具層**：
   - **唯讀工具逾時**（如 `get_order`、`check_inventory`）：無副作用，單次工具 timeout 設為 `5s`。若逾時或連線重置，可直接重試 `2` 次（總預算 `5s × 3 = 15s`，未計退避）；若仍失敗，在 `tool_result` 區塊設定 `is_error: true` 並回傳精簡錯誤訊息，讓模型決定改查替代欄位或回覆使用者。
   - **寫入／金流工具逾時或授權邊界**（如 `issue_refund`）：單次工具 timeout 設為 `10s`。由於模型輸出、工具／MCP 回傳與訂單備註都可能夾帶 prompt injection，**業務授權必須放在工具執行端**：依可信身分驗證租戶、訂單、角色、付款狀態、可退餘額與核准範圍，並以條件更新防止併發超退。去重鍵必須綁定持久化業務操作 `(tenant_id, refund_operation_id)`（綁定訂單、最小貨幣單位金額與幣別，對同鍵異參數回報衝突）。送出前記錄授權後的操作意圖；逾時後依供應商的冪等有效期與查單能力決定查詢、同鍵重送或人工對帳。

### Token Bucket 與 Retry-After 感知的退避重試

單純的固定間隔重試會在尖峰時段引發「重試風暴」。生產環境應在客戶端（按模型池與租戶配額作用域）維護本地 Token Bucket 限流器（補充速率設為租戶配額的 `90%`，例如 `2,400 RPM` 配額對應 `36 calls/s`，突發容量 `burst = 54`），並以 **Exponential Backoff with Full Jitter** 結合伺服器回傳的 `retry-after` 標頭；共用 `retry-after` 下限醒來後仍須經限流器放行，避免多 Worker 同時湧入：

```text
delay_ms = max(retry_after_ms, random(0, min(max_delay_ms, base_delay_ms * 2^(attempt - 1))))
```

建議生產工程基線配置如下（若由應用程式掌管重試，應設 TypeScript `maxRetries: 0`、Python `max_retries=0`，避免與 SDK 預設重試相乘）：
- **單次 LLM 請求與 SSE timeout**：單次 HTTP timeout 設為 `60s`；Streaming 需將 transport idle（含 `ping` 保活）與模型進度 timeout 分開，避免把只有 `ping` 或暫無 `content_block_delta` 的活連線誤判斷線。
- **退避與同步／背景預算**：`base_delay_ms = 500ms`、`max_delay_ms = 30,000ms`（前 `4` 次退避上限依序為 `0.5s、1s、2s、4s`，合計 `7.5s`）。同步 API 請求總 wall-clock 上限 `120s` 須同時約束單次呼叫與睡眠的剩餘 deadline（兩次 `60s` 呼叫即會耗盡同步預算，分流目標為 `p95 ≤ 2.5s`、多步處置 `p95 ≤ 18s`，超時即轉非同步）；非同步背景 Worker 總預算設為 `3,600s`。
- **熔斷器參數**（按模型池／Pod 維護）：滑動視窗 `60s` 內連續發生 `failure_threshold = 5` 次 `529` 或 `5xx` 錯誤即切為 `OPEN`，冷卻 `cooldown = 30s` 後進入 `HALF_OPEN`，僅放行 `1` 個探測請求（並以 epoch／token 防止舊的在途請求關閉新開的 breaker）；成功則復歸 `CLOSED`，失敗則重設 `30s` 冷卻。
- **Prompt Caching 與結構化輸出邊界**：重試時應保持 `tools → system → messages` 中截至 `cache_control: {"type": "ephemeral"}` 斷點的有效前綴一致，但命中仍受 TTL、模型最低可快取長度與處理時序影響；計費與排錯應同時記錄 `input_tokens`、`cache_creation_input_tokens`、`cache_read_input_tokens` 與 `output_tokens`。若啟用 `strict: true` 或 `output_config.format` 約束 JSON 結構，業務授權仍由工具端負責；Extended Thinking 可透過 `thinking: { type: "enabled", budget_tokens: N }` 或較新模型支援的 adaptive reasoning 模式啟用（具體預設與支援參數依模型版本與官方文件確認），Replay 時須保留同一工具回合要求回傳的 thinking 區塊與簽章。

### Event-sourced Checkpoint 與 Replay 執行日誌

為了讓長任務在 Pod 重啟、Deployment 滾動更新或 HITL 暫停後能從斷點續跑，Agent Loop 的每一步狀態轉移都必須以 append-only 事件寫入持久化儲存（PostgreSQL 為主儲存，Redis 負責分散式鎖與超時提醒），並在寫入前遮罩敏感欄位、控管讀取權限與保留期限：

- `llm_turn`：記錄原始請求（或可重建版本）、完整 `assistant` 訊息（含 thinking 區塊與簽章）、各 `tool_use_id`、`usage` 與 `stop_reason`。
- `tool_call`：記錄 `tool_use_id`、工具名稱、輸入參數、`idempotency_key`（基於 `refund_operation_id`）、`is_error` 與回傳結果。
- `hitl_pause`：記錄暫停原因、綁定的不可變操作內容與超時時間 `deadline_at`（`deadline_sec = 3600`）。
- `hitl_resume`：記錄審批人識別碼、核准或駁回決定與備註。
- `completed` / `failed`：終態標記。

建議持久化 Checkpoint 表結構（PostgreSQL）如下；`seq` 須以原子方式配置或搭配預期版本號寫入：

```sql
CREATE TABLE agent_checkpoints (
  run_id      VARCHAR(64) NOT NULL,
  seq         INT NOT NULL,
  step_type   VARCHAR(32) NOT NULL,
  payload     JSONB NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (run_id, seq)
);
CREATE INDEX idx_checkpoints_created ON agent_checkpoints (created_at);
```

- **分散式執行鎖與 Fencing**：Worker 接手 `run_id` 前先搶佔 Redis 鎖 `run:lock:{run_id}`（`SET NX EX 30`），並在整個持有期間由背景心跳定期續約；續約與刪鎖前必須核對持有者 token（如 Lua compare-and-delete），持久狀態寫入也應檢查版本號或 fencing token，防止鎖過期後舊 Worker 覆寫狀態。
- **Replay 逐一核對規則**：依 `seq ASC` 讀取事件並組裝 `messages[]`。Replay 不能只看最後一筆事件，必須逐一比對最新 `llm_turn` 中的每個 `tool_use_id` 與對應 `tool_call` 事件，依序辨識已完成、尚未派送與結果不明的操作；派送前須重新核對退款額度、權限與 HITL 狀態。待所有工具皆有結果後，下一則 `user` message 應先放入對應的 `tool_result` 區塊再繼續模型回合。自行透過 MCP Streamable HTTP 派送與 Anthropic MCP Connector 代呼叫的失敗窗口不同，Connector 可能在串流中斷前已執行遠端工具，重送整個 turn 前須先核對遠端狀態。
- **冷熱分層與歸檔**：PostgreSQL 原生分區表若以 `created_at` 按月分區，父表主鍵必須包含分區鍵，直接加上 `created_at` 會失去全表 `(run_id, seq)` 唯一性；若保留月分區，應另設 `agent_runs` 表維護每個 run 的 `current_seq` 與唯一性。歸檔至物件儲存（Parquet 格式）時，不可只按月卸載分區，必須確認該 run 已進入 `completed` 或 `failed` 終態且超過 `30` 天、橫跨分區的相關紀錄皆已結案。

### 非同步 Worker Queue 與 Batch API 狀態追蹤

對於不要求即時回應的批次對帳或夜間報表任務，應將工單丟入非同步 Worker Queue（如 BullMQ、Celery 或 Temporal），每個 Worker Pod 限制併發數 `concurrency = 20`、`prefetch = 1`（各系統語意不同：BullMQ 依 `concurrency` 拉取、Celery 設 `worker_prefetch_multiplier=1`、Temporal 控制 `maxConcurrentActivityTaskExecutions`），避免單一節點記憶體被大量長 Context 撐爆。

針對高吞吐、低急迫性的工作負載，應切換至 **Batch API**（`POST /v1/messages/batches`）。Batch API 提供 **50%** 折扣（Sonnet 5.5 為 `$1.00 / $5.00` per MTok），適用於非同步批次工作負載（實際完成時間與 SLA 須依對應版本的官方文件為準）。Worker 必須把 `custom_id` 編碼為符合官方規格的短 ID（並持久化它與 `batch_id`、`run_id`、`seq` 的對照），定期輪詢批次狀態，並在結果就緒後下載 `.jsonl` 結果檔依對照表寫回；`custom_id` 格式、`processing_status` 狀態轉移與子請求到期規則須以對應版本的官方文件為準。Batch 以單次 Messages 呼叫為單位，多步本地工具迴圈仍須逐輪協調；成功回應仍需檢查 `stop_reason`，失敗子請求應先分類（永久驗證錯誤修正後再送），過期子請求則僅針對該子請求重新打包送出，並以持久化狀態去重提交與下載。

### HITL 審批暫停、超時升級與喚醒續跑

在 `OrderOps` 中，當退款金額超過自動核准上限（`$250`）時，工具回傳 `status: "pending_hitl"`。此時 Agent Loop 必須立刻停止推進，寫入 `hitl_pause` 事件並釋放 Worker 執行緒，同時將 `deadline_at` 寫入 PostgreSQL（搭配 Redis `hitl:deadline:{run_id}` TTL `3600s` 作為快速通知，持久化掃描負責補漏）：

```text
running ──(amount > $250)──> waiting_hitl
   │                              │
   │                    ┌─────────┴─────────┐
   │             (人工核准/駁回)      (超過 SLA 如 3600s)
   │                    ▼                   ▼
   │                 resumed            escalated
   │                    │
   └────────────────────┴──> completed / failed
```

核准、駁回與升級必須在 PostgreSQL 中以條件式狀態轉移競爭（例如 `WHERE status = 'waiting_hitl'`），並在同一交易寫入事件與喚醒 Outbox。人工核准後，系統寫入 `hitl_resume` 事件並喚醒 Worker 續跑，帶著核准憑證執行退款並寫入 `tool_call` 與 `completed`；若審批人駁回，則將駁回原因封裝為 `tool_result`（`is_error: true`）回填給模型生成安撫回覆並終止流程。

### Worked Example：OrderOps 尖峰容量與退避佇列深度估算

以下以 `OrderOps` 基準數據估算容量與退避佇列：

```text
1. 基礎負載（對應 running-examples.md）：
   - OrderOps 日工單量：50,000 筆／天（1,500,000 筆／月，以 30 天計）
   - OrderOps 尖峰流量：12 req/s（平均 0.5787 req/s，尖峰約 20.7×）
   - 單筆平均 API 呼叫：5 次（5 回合）

2. 尖峰 API 請求率（RPM）：
   - 每秒 API 呼叫數 = 12 req/s × 5 calls/req = 60 calls/s（假設五回合充分重疊，未計重試）
   - 每分鐘 API 呼叫數（尖峰 RPM） = 60 calls/s × 60 s = 3,600 RPM

3. 配額缺口與退避佇列深度估算（以 API 呼叫數為單位）：
   - 假設租戶購買的 API 配額上限為 2,400 RPM（即 40 calls/s）
   - 按名目配額 40 calls/s：尖峰淨超額 20 calls/s，持續 30 秒累積 600 個 API 呼叫；
     尖峰後平均流量 2.89 calls/s，排空餘裕 37.11 calls/s，約 16.2 秒排空。
   - 按章內 90% 限流設定（36 calls/s）：持續 30 秒累積 (60 - 36) × 30 = 720 個 API 呼叫
     （若尖峰開始時桶滿且立即放行 burst = 54，則剩 666 個，約 20.1 秒排空；無初始額度約 21.8 秒）。

4. 結論：
   - 退避佇列應以 API 呼叫數（而非工單數）估算緩衝深度，並將超額請求轉入非同步 Worker Queue，
     避免在同步路徑硬扛 429 拖垮可用性。
```

## 故障模式與防禦

生產環境的可靠性取決於能否在第一時間從日誌與 HTTP 狀態碼辨識故障類型，並觸發對應防禦：

| 故障模式 | 觀測線索（HTTP / Log） | 關鍵日誌欄位與告警閾值 | 生產級防禦基線 |
|---|---|---|---|
| **配額雪崩** | 大量 `429 rate_limit_error`，標頭含 `retry-after: 12`（示範值） | `http_status=429`、`retry_after_sec`；服務 `429` 比例 `> 5%` 持續 `2m` 告警 | 啟用本地 Token Bucket + Full Jitter；`retry-after` 優先於本地計算延遲，醒來後仍經限流器放行 |
| **上游叢集過載** | `529 overloaded_error` 連續出現 | `breaker_state=OPEN`、`attempt`；單模型池熔斷 `OPEN > 30s` 告警 | 熔斷器設定 `failure_threshold = 5`、`cooldown = 30s`，`OPEN` 期間直接轉入延遲佇列 |
| **Streaming 殘缺 JSON** | `SyntaxError: Unexpected end of JSON input`，無 `message_stop` | `sse_stop_reason=null`、`partial_json_bytes`；任何 `> 0` 即記 WARN | 僅在收到 `message_stop` 且 JSON Schema 驗證通過後才寫入 `llm_turn`；否則丟棄殘缺輸出，確認無外部副作用後再重試（遠端代呼叫須先查單或依冪等鍵對帳） |
| **Silent Cache Miss** | 重試 Turn 時 `cache_read_input_tokens = 0` | `cache_creation_input_tokens > 0` 且 `attempt > 1` 觸發告警 | 鎖定 `tools → system → messages` 有效前綴，重試前驗證 prefix hash 一致性 |
| **重啟重複退款** | 同一 `refund_operation_id` 出現兩筆退款單 | `run_id`、`refund_operation_id`；重複退款事件 `> 0` 立即 P1 告警 | 工具層強制檢查 `(tenant_id, refund_operation_id)`，綁定訂單、金額與幣別 |
| **HITL 永遠卡死** | `run_status = waiting_hitl` 超過 SLA 無更新 | `hitl_age_sec > 3600` 觸發升級告警 | PostgreSQL 存 `deadline_at` 並由排程掃描補漏，Redis `hitl:deadline:{run_id}` 加速通知 |

實務排錯時，工程師應特別注意兩項細節：第一，`529` 屬於過載類瞬態故障，而 `429` 須先區分是暫時性配額限流還是支出上限（後者不應無止盡重試）：配額型 `429` 應優先檢查 `anthropic-ratelimit-tokens-reset` 與本地 Token Bucket 補充速率是否與實際購買的 Tier 配額一致，而 `529` 則不應盲目降低併發，應直接依賴熔斷器將非即時工單轉入延遲佇列；第二，重複退款告警應依業務操作 ID 與供應商交易 ID 對帳，同一筆訂單因部分退貨本來就可能有多筆合法退款。

## 動手做

本章完整可執行程式碼位於 `examples/ts/ch06/index.ts`（TypeScript）與 `examples/py/ch06/main.py`（Python），兩者皆整合 `OrderOpsMockBackend` 展示 **Checkpoint + Exponential Backoff with Jitter + Circuit Breaker + HITL Pause/Resume**（範例為秒級執行使用教學縮放參數：`maxAttempts = 4`、`50ms` 起跳與 `20ms` retry-after）。以下節錄核心退避與工作流狀態機邏輯。

### TypeScript 核心片段（`examples/ts/ch06/index.ts`）

```ts
export async function withBackoffAndJitter<T>(
  fn: () => Promise<T>,
  options: { maxAttempts?: number; baseDelayMs?: number; maxDelayMs?: number } = {},
): Promise<T> {
  const maxAttempts = options.maxAttempts ?? 4;
  const baseDelayMs = options.baseDelayMs ?? 50;
  const maxDelayMs = options.maxDelayMs ?? 1000;

  let lastError: unknown;
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (err) {
      lastError = err;
      if (!(err instanceof RetryableApiError) || attempt === maxAttempts) {
        throw err;
      }
      const expCap = Math.min(maxDelayMs, baseDelayMs * 2 ** (attempt - 1));
      const fullJitterMs = Math.floor(Math.random() * expCap);
      const retryAfterMs = err.retryAfterSec ? err.retryAfterSec * 1000 : 0;
      await new Promise((resolve) => setTimeout(resolve, Math.max(fullJitterMs, retryAfterMs)));
    }
  }
  throw lastError;
}
```

### Python 核心片段（`examples/py/ch06/main.py`）

```python
def run_refund_workflow(
    self, *, run_id: str, refund_operation_id: str, order_id: str, tenant_id: str, amount_usd: float, reason: str
) -> dict[str, Any]:
    if not math.isfinite(amount_usd) or amount_usd <= 0:
        raise ValueError("amount_usd must be a positive finite number")
    idempotency_key = f"{tenant_id}:{refund_operation_id}"
    existing = self.store.get_events(run_id)
    paused = any(e.step_type == "hitl_pause" for e in existing)
    resumed = any(e.step_type == "hitl_resume" for e in existing)

    if not paused:
        attempts = 0

        def call_llm() -> dict[str, Any]:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RetryableApiError("Rate limit exceeded", 429, retry_after_sec=0.02)
            return {"action": "issue_refund", "amount_usd": amount_usd}

        decision = self.breaker.execute(lambda: with_backoff_and_jitter(call_llm))
        self.store.append(run_id, "llm_turn", {"decision": decision, "attempts": attempts})
```

### 執行驗證與預期輸出

從專案根目錄執行以下指令驗證 TypeScript 與 Python 版本的 Checkpoint 與 HITL 續跑流程：

```bash
(cd books/enterprise-agents/examples/ts && npx tsx ch06/index.ts)
(cd books/enterprise-agents/examples/py && python3 ch06/main.py)
```

兩個版本的預期終端輸出皆為：

```text
First pass status: waiting_hitl
Checkpoints recorded: 3
After HITL approval, total checkpoints: 6
Final step: completed
```

驗證重點與設計預期：依章節範例設計，第一次執行因退款金額 `$300` 超過 `$250` 自動核准上限（且低於 mock 訂單總額 `$340`），會寫入 `llm_turn`、`tool_call` 與 `hitl_pause` 共 `3` 筆事件並回傳 `waiting_hitl`；人工核准寫入 `hitl_resume` 後，由 Runner 續跑取得核准後的退款回執並寫入 `tool_call` 與 `completed`，最終預期累積 `6` 筆事件且不重複呼叫 LLM（實際執行結果須依完整程式碼實測驗證）。

## 自我檢核

1. **入門，10 分鐘**：為什麼在處理 `429 rate_limit_error` 時，不能只用固定間隔（例如每次等 `2` 秒）重試，而必須結合 Full Jitter 與 `retry-after` 標頭？
2. **進階，15 分鐘**：假設 `OrderOps` 的某一筆工單在執行 `issue_refund` 後、寫入 `tool_call` Checkpoint 前，Worker Pod 突然被 OOMKill。請說明系統重啟後如何透過 `(tenant_id, refund_operation_id)` 與 Replay 機制避免重複退款，並指出本地 `UNIQUE` 約束無法涵蓋的邊界。
3. **挑戰，20 分鐘**：若 `OrderOps` 在大促期間尖峰流量升至 `20 req/s`（每筆 `5` 次 API 呼叫），而租戶配額為 `3,600 RPM`，請計算持續 `45` 秒尖峰會累積多少待退避請求（分別以名目配額與 `90%` 限流估算），並設計對應的佇列背壓（Backpressure）策略與 Batch API 分流取捨。

### 參考解答

1. 固定間隔重試會讓同一批失敗的請求在相同時間點再次同時湧入上游，形成「驚群效應」（Thundering Herd），導致連續觸發 `429`。Full Jitter 在 `[0, expCap]` 區間隨機抽樣以降低重試同步與碰撞機率，但有限區間內仍可能發生碰撞；當多數請求收到相同的 `retry-after` 且取 `max(fullJitter, retryAfter)` 時，小於該下限的抽樣會集中在同一時間點醒來，因此仍需透過本地限流器或在冷卻下限之後進一步分散放行。
2. Worker 重啟後依 `seq ASC` 讀取 Checkpoint，比對 `llm_turn` 與 `tool_call` 發現回執尚未落盤（不重跑 LLM），先將該操作標記為結果不明。送出前系統已記錄授權後的 `(tenant_id, refund_operation_id)` 操作意圖並綁定訂單、金額與幣別；應依供應商的查單能力與冪等有效期查詢狀態或同鍵重送，若無法安全確認則暫停自動派送並轉由人工對帳（本地資料庫 `UNIQUE` 約束無法單獨封住「外部已入帳但回執未落盤」的窗口）。
3. `20 req/s × 5 = 100 calls/s`（`6,000 RPM`），名目配額為 `3,600 RPM`（`60 calls/s`），淨超額率為 `40 calls/s`，持續 `45` 秒累積 `40 × 45 = 1,800` 個 API 呼叫（約 `37.5s` 抵達 `1,500` 告警線）；若沿用 `90%` 限流（`54 calls/s`），未扣初始桶額度時積壓 `(100 - 54) × 45 = 2,070` 個。背壓策略應包含：(1) 在 API Gateway 層對低優先級工單回傳 `202 Accepted` 並轉入非同步佇列或 Batch API（享 **50%** 折扣，Sonnet 5.5 降至 `$1.00 / $5.00` per MTok，代價是轉為非同步批次處理，實際完成時間依官方文件為準）；(2) 保留即時配額給 `critical` / `high` 工單；(3) 佇列深度超過 `1,500` 時觸發限流告警與降級。

## 延伸閱讀

- Anthropic API Rate Limits 與 `retry-after` 標頭規格（官方文件，建議搭配 SDK `max_retries` 參數對照）。
- Marc Brooker，《Exponential Backoff And Jitter》（AWS Architecture Blog）—— Full Jitter 與 Decorrelated Jitter 的數學比較。
- Martin Kleppmann，《Designing Data-Intensive Applications》第 11 章 —— Event-sourced 日誌與冪等性寫入的分散式系統基礎。
