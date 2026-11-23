# 第 10 章：可觀測性與維運——Trace、成本歸因、漂移監控與上線切換

> 「沒有 Trace 與成本歸因的 Agent 上線，等於沒有儀表板時以 12 req/s 盲飛。」

---

## 從你已知的出發

傳統微服務的可觀測性建立在「請求 → 資料庫／RPC → 回應」的確定性路徑上：HTTP 狀態碼 `200` 代表成功，p95 延遲反映系統健康。但在 `OrderOps` 這類企業級 Agent 系統中，這套假設會失效：

1. **HTTP `200` 不代表業務結案**：以退款工單為例，傳統微服務同樣可能回傳 `200` 卻未達成業務目的；在 Agent 中，模型可能回傳 `stop_reason: "end_turn"`，卻因為產生幻覺或漏掉關鍵工具呼叫而給出錯誤的退款建議。
2. **單次請求的成本與延遲高度變異**：同樣處理一張工單，在模型路由、快取與上下文精簡全套優化下，單筆成本可壓在 `≤ $0.012`；但若觸發多步迴圈或 Prompt Cache 失效，單筆成本會瞬間跳升至全 Sonnet 停用快取基準的 `$0.1015` 甚至更高。
3. **非同步與狀態機跨越多個 `Turn`**：一個 `OrderOps` 工單平均需要 `5` 個回合（`Turn`），每個回合包含一次 LLM 呼叫與零至多次工具執行，傳統單層 APM 無法把這些碎片串成同一條因果鏈。

因此，我們需要專為 Agent Loop 設計的四層維運架構：符合 OpenTelemetry GenAI 語意慣例的分散式追蹤、即時成本歸因與預算熔斷、核心維運指標監控，以及影子流量與金絲雀發布切換流程。

---

## 核心機制

### 1. Agent 專用遙測結構（OpenTelemetry GenAI 語意慣例）

為 `OrderOps` 建立追蹤時，必須將 Span 切分為四個層級，並透過 `trace_id` 與 `parent_span_id` 串聯（範例以教學用的自訂 Span 分類、序號 ID、記憶體存放與模擬時間示範結構）：

```text
agent.request (root: ticket_id, tenant_id, total_cost_usd)
├── agent.turn (turn_index=1)
│   ├── gen_ai.client (CLIENT: model, input_tokens, cache_read, finish_reasons, cost_usd)
│   └── agent.tool (tool_name, is_error, latency_ms)
└── agent.turn (turn_index=2)
    └── gen_ai.client (CLIENT: model, input_tokens, output_tokens, finish_reasons, cost_usd)
```

在線路上（Wire-level），每次呼叫 Anthropic Messages API 時，回應的 JSON 載荷與 HTTP Header 會提供可觀測性所需的原始事實。`usage` 物件精確拆分了計費類別，`stop_reason` 決定狀態機分支，而 `request-id` 與 `anthropic-ratelimit-requests-remaining`、`anthropic-ratelimit-tokens-remaining` 等 Header（須從 SDK 回應介面取得）則用於對齊上游限流與除錯：

```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "stop_reason": "tool_use",
  "usage": {
    "input_tokens": 1200,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 6800,
    "output_tokens": 350
  }
}
```

依 OpenTelemetry GenAI 語意慣例，LLM 呼叫應採 `CLIENT` Span Kind，並固定記錄 `gen_ai.provider.name`（`"anthropic"`）、`gen_ai.operation.name`（`"chat"`）與 `gen_ai.request.model`。實務上可將 `gen_ai.usage.input_tokens` 統一記為含快取讀寫的總輸入（實際欄位定義請依所採用之 OpenTelemetry GenAI 語意慣例版本與 Anthropic Messages API 文件為準；以示意數值為例：`1,200 + 0 + 6,800 = 8,000`，若對應 OrderOps 基準第 2 回合則為 `1,200 + 0 + 6,000 = 7,200`），而原始 Anthropic `usage.input_tokens`（`1,200`）僅含非快取輸入。其餘關鍵欄位如下：

- `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens`
- `gen_ai.usage.cache_creation.input_tokens` / `gen_ai.usage.cache_read.input_tokens`（搭配 `cache_control: {"type": "ephemeral"}` 斷點使用；`85%` 為特定工作負載目標，例如示意數值 `6,800 ÷ 8,000`，OrderOps 基準第 2 回合為 `6,000 ÷ 7,200 ≈ 83.3%`。若兩者同時為 `0`，可能是停用或移除快取、不可快取的內容、前綴未達門檻，或串流截斷造成 Usage 缺失，需分開診斷）
- `gen_ai.response.finish_reasons`（字串陣列，對應 Anthropic API 的 `stop_reason`，如 `end_turn`、`tool_use`、`max_tokens` 等，實際列舉值依官方 API 文件為準；串流起始為 `null`，遇到未知值應保留供診斷，且禁止執行截斷或未驗證的工具參數）
- `agent.cost_usd` 與 `agent.cache_hit_ratio`

以下是 TypeScript 的核心 Span 紀錄契約（完整可執行程式見 [index.ts](../examples/ts/ch10/index.ts) 與 [main.py](../examples/py/ch10/main.py)）：

```typescript
const totalInput = usage.input_tokens + usage.cache_creation_input_tokens + usage.cache_read_input_tokens;
const llmSpan = tracer.startSpan(
  traceId,
  "anthropic.messages.create",
  "gen_ai.client",
  {
    "gen_ai.provider.name": "anthropic",
    "gen_ai.operation.name": "chat",
    "gen_ai.request.model": usage.model,
    "gen_ai.usage.input_tokens": totalInput,
    "gen_ai.usage.output_tokens": usage.output_tokens,
    "gen_ai.usage.cache_creation.input_tokens": usage.cache_creation_input_tokens,
    "gen_ai.usage.cache_read.input_tokens": usage.cache_read_input_tokens,
    "gen_ai.response.finish_reasons": usage.stop_reason ? [usage.stop_reason] : [],
  },
  turnSpan.spanId,
);
```

在採樣策略上，高吞吐微服務常採用 1%–5% 頭部採樣（Head-based Sampling），但 Agent 系統不能這麼做：假設單筆失控迴圈或幻覺退款佔流量的 `0.5%`，頭部採樣可能漏掉絕大多數故障 Trace，且不能保證保留特定故障（例如 1% 隨機抽樣下，單筆故障有 99% 機率被漏掉）。生產環境應採用「**全量指標 + 尾部採樣**（Tail-based Sampling）」：

- **採樣前先產出全量指標**：所有全量計數器與延遲直方圖必須在採樣前計算，否則直接用留存 Trace 算比率或 p95 會產生嚴重的選樣偏差。
- **尾部採樣設計**：依 `trace_id` 將同一 Trace 的 Span 路由至同一 Collector 實例並規劃緩衝容量；凡符合 `status == ERROR`、根節點 `agent.total_cost_usd > 0.025`、`agent.cache_hit_ratio < 0.60` 或 `latency_ms > 18000` 者 100% 保留，其餘健康請求再依 10% 比例抽樣歸檔。注意固定 `60s` 緩衝可能在 `90s` 工單或跨 HITL 等待結束前就做出採樣決策，需妥善處理晚到 Span 與長工單關聯。

### 2. 核心維運指標與 SLO 基線

針對 `OrderOps` 日處理 `50,000` 筆工單（每月 `1,500,000` 筆，以 30 天計）、尖峰 `12` req/s（平均 `0.58` req/s，尖峰約 `20×`）的負載，維運儀表板必須持續追蹤六個核心指標，並明確定義分母、去重單位與時間窗：

| 指標名稱 | 計算方式（採樣前全量事件） | `OrderOps` 目標基線 | 異常判讀 |
|---|---|---|---|
| **Task Completion Rate** | 成功結案且通過後驗檢查的工單比例 | `≥ 96%` | 下降代表 Prompt 退化或工具契約破損 |
| **Tool Error Rate** | `is_error: true` 的工具嘗試佔總工具呼叫比例 | `≤ 1.5%` | 飆升代表下游 ERP／物流 API 異常或 Schema 漂移 |
| **Cache Hit Ratio** | 快取讀取 token 占比（`Σ cache_read ÷ Σ total_input`） | `≥ 85%`（特定工作負載目標） | 驟降至 `0%` 代表前綴快取失效、TTL 過期或路由改變 |
| **Cost per Ticket** | 根節點 `agent.total_cost_usd`（區分月平均與單筆告警） | 月均 `≤ $0.012`（月成本 `≤ $18,000`） | 單筆超過 `$0.025` 需檢查是否發生異常多步迴圈 |
| **p95 Latency** | 分流端與多步工具處置端的 95 百分位延遲 | 分流 `≤ 2.5s` / 多步 `≤ 18s` | 逼近 SLO 上限需檢查模型 TTFT 或工具逾時 |
| **HITL Escalation Rate** | 轉交人工審批（`pending_hitl`）的工單比例 | `5% – 12%` | 過低可能代表護欄失效，過高代表模型信心不足 |

上述指標需補齊工具嘗試、逾時、後驗結案與 HITL 狀態事件，並以 5 分鐘與 1 小時雙時間窗呈現，避免瞬時尖峰掩蓋長尾退化。

### 3. 成本歸因帳本與異常熔斷（Budget Circuit Breaker）

單靠事後帳單無法阻止失控的 Agent Loop。生產環境必須將熔斷邏輯拆分為**送出前檢查**（`checkBeforeSend`）與**送出後依實際 Usage 結算**（`recordUsage`），確保已發生的費用不會因提前回傳而漏記，並區分「已達上限（`>=`）」與「下一筆會超額（`>`）」：

1. **單筆工單上限**（Per-Ticket Cap）：例如設定 `maxTicketCostUsd = 0.15`（約為目標單筆成本 `$0.012` 的 `12.5×`）。送出前若已達上限即阻斷；送出後結算若超標，立即中止後續迴圈並轉交 `HITL`。
2. **每小時全域／租戶燃燒上限**（Hourly Burn Cap）：設定 `maxHourlyBurnUsd`（須依尖峰流量校準，見下文檢核題 3）。當視窗內的累計花費觸及上限時，熔斷器切換為 `OPEN` 狀態，拒絕非高優先級請求或降級至人工佇列。

在儲存架構上，即時熔斷與長期帳本必須分層處理：

- **即時熱路徑**（Redis）：使用鍵值 `budget:hourly:{tenant_id}:{yyyyMMddHH}`（整點固定窗，`TTL = 3600` 秒；若採滾動窗或程序起算窗須明確對齊）搭配 Lua 腳本執行原子性去重、扣款與上限檢查，目標延遲 `< 2ms`；熔斷旗標 `circuit:hourly:{tenant_id}` 設為 `TTL = 300` 秒，並預先定義 Redis Cluster 故障切換與旗標到期後的恢復行為。
- **非同步冷路徑**（PostgreSQL）：為避免 `(trace_id, turn_index)` 主鍵吞掉同回合的平行呼叫或真正再次計費的重試，應為**每次實際上游呼叫**記錄獨立的持久事件 ID（`event_id`，重送沿用該 ID），並保留 `ticket_id`、`turn_index` 與上游 `request_id` 供對帳。`(tenant_id, created_at)` 索引支援租戶與時間範圍查詢，`ticket_category` 則在該範圍內篩選或聚合；低價模型應選擇足夠的 `NUMERIC` 精度並延後四捨五入：

```sql
CREATE TABLE agent_cost_ledger (
  event_id TEXT PRIMARY KEY,
  ticket_id TEXT NOT NULL,
  trace_id TEXT NOT NULL,
  turn_index INT NOT NULL,
  upstream_request_id TEXT,
  tenant_id TEXT NOT NULL,
  ticket_category TEXT NOT NULL,
  model TEXT NOT NULL,
  cost_usd NUMERIC(12, 8) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ledger_tenant_time ON agent_cost_ledger (tenant_id, created_at DESC);
CREATE INDEX idx_ledger_ticket ON agent_cost_ledger (ticket_id, turn_index);
```

- **架構取捨**（Redis 即時 vs PostgreSQL 持久化）：改採 Redis 原子累加配合背景批次寫入，可避免同步寫入拖累 `p95` 延遲；當 Redis 節點意外重啟時，須先確保持久事件可重播，再重建熱路徑視窗計數。
- **逾時、SLO 與併發基線**：單次 LLM 呼叫 `30s`、單次 Tool `5s`、整筆工單 `90s`（`max_turns = 8`）是硬逾時設定；針對 `2.5s / 18s` SLO，還需獨立定義路徑期限（Deadline）、剩餘預算與取消傳遞。若 `12 req/s` 的工單到達率持續且系統達到穩態，平均約需 `12 × 5 = 60` 次 **LLM 呼叫／秒**（不能直接當作連線槽位）；瞬時尖峰與實際併發仍須另行估算，並用「到達率 × 各階段平均在途時間」納入工具扇出、重試與上游 RPM／ITPM／OTPM 限制。

### 4. Shadow Mode、Canary Rollout、漂移監控與模型版本 Pinning

升級模型（例如從 `claude-sonnet-5-5` 切換至新快照）或修改 System Prompt 時，嚴禁直接全量上線：

1. **安全邊界與 Shadow Mode**：所有工單內容、工具回傳與 MCP 回傳皆視為不受信任的資料。每次工具執行應由閘道驗證租戶、物件所有權、業務參數與審批；影子環境須在工具閘道封鎖副作用，採唯讀憑證及可控的 stub／replay，並遮罩 Trace 內的 PII、金流欄位與憑證。Shadow 可量測擬議動作與模型費用（`1,000` 筆在均勻到達下約需 `28.8` 分鐘），真實結案率與含寫入結果的總成本應由隔離重播或 Canary 驗證，並按退款等高風險類別檢查樣本量。
2. **Canary Rollout**：切出 `5%` 流量（約 `2,500` 筆／日）觀察至少 `24` 小時；若 `Tool Error Rate` 上升 `+0.5` 個百分點（從 `1.5%` 升至 `2.0%`）、任一條 `p95 Latency` 突破 SLO（`2.5s / 18s`）、`Cost per Ticket` 增幅超過 `15%` 或發生安全違規，立即自動切回舊版並妥善處置在途寫入。
3. **線上漂移監控與版本 Pinning**：生產環境應使用供應商明確文件化的固定快照識別碼；若僅使用模型 ID（如 `claude-sonnet-5-5`），須確認其版本更新政策並持續監控模型行為。建立按模型、Prompt、工具 Schema 版本與工單類別分層的線上基準，並處理後驗標籤晚到的評估延遲；每次升級前重跑第 7 章的 Eval 基準集，確認 `Pass^k`（見第 7 章）與延遲 SLO 達標。
4. **實際整合適用邊界**：本節範例使用模擬 Usage，未直接送出以下進階 API 參數，實際整合時須注意：`strict: true` 約束工具輸入 schema、`output_config.format` 約束模型輸出格式，但業務授權仍由應用程式執行；Thinking 費用採 API Usage 的輸出 token 計費；自管 MCP Streamable HTTP 與 Anthropic MCP Connector 屬於不同執行邊界，Connector 可由服務端呼叫公開 HTTP 的 MCP 工具，本地 `tool_use` 閘門無法攔截，因此 Shadow 須在 Connector 憑證或 MCP 服務端限制工具；Batch 應按每個成功結果的 Usage 歸因，以 `custom_id` 關聯工單並處理失敗、取消與過期結果。此外，本章範例的計價 helper 僅示範固定情境，生產帳本應保留原始 Usage、端點、模型與有效費率版本（涵蓋混合 TTL、Haiku `>100K` 級距、Batch、`inference_geo` 與伺服器端工具）。

---

## 故障模式與防禦

### 故障模式 1：Prompt Cache 靜默失效（Silent Cache Miss）

- **現象**：某次部署在 System Prompt 前段意外插入動態 `timestamp` 或隨機 `request_id`，導致每次請求的前綴雜湊改變。API 仍回傳 HTTP `200`，但 `usage.cache_read_input_tokens` 跌為 `0`，`cache_creation_input_tokens` 暴增（甚至每輪反覆產生寫入費）或全數按原價 `input_tokens` 計費。
- **診斷日誌與告警**：在 `gen_ai.client` 結構化日誌中記錄 `agent.prompt_prefix_sha256`（涵蓋實際送出的工具、系統指示與快取訊息，並排除原始敏感內容）、`cache_hit_ratio` 與 `cache_creation_input_tokens`。當 5 分鐘滾動視窗的 `Cache Hit Ratio` 低於 `60%`（目標為 `85%`），立即觸發 P1 告警並比對前後兩版前綴雜湊，於 5 分鐘內自動回滾或切換流量。

### 故障模式 2：上游限流（429/529）與工具異常重試引發的成本雪崩

- **現象**：下游 ERP 回傳 `503` 或 Anthropic API 回傳 `429`（夾帶 `retry-after` Header）與 `529 overloaded_error`。若未區分故障層級，模型會在 `Agent Loop` 中反覆嘗試修正參數並重新呼叫工具（`max_turns` 從 5 增至 8 或 10 本身只將呼叫次數增至 `1.6×` 或 `2×`，但加上重試與上下文膨脹，假設情境下單筆成本可能暴增至正常值的 `5×` 以上）。
- **診斷日誌與防禦**：日誌須區分 `upstream_http_status`（`429`/`529`/`503`）與 `tool_is_error`。結合 `BudgetCircuitBreaker` 與連續相同工具錯誤偵測（依操作鍵或參數指紋、錯誤類型與是否可重試界定，避免把同名工具的獨立查詢誤判為同一故障，連續 `2` 次即強制中斷並轉 `HITL`）；遇到 `429` 嚴格遵循 `retry-after`、`529` 在 Header 存在時採用否則走有上限的指數退避與 Jitter，並協調 SDK 與應用層重試納入共同 Deadline 與重試預算。當 1 分鐘內 `429` 比例超過 `5%` 時觸發 P2 限流告警。

### 故障模式 3：Streaming SSE 半途斷線與殘缺工具參數

- **現象**：使用串流模式時，連線在 `content_block_delta`（`input_json_delta`）階段因網路抖動中斷，未收到 `message_stop` 事件與最終 `usage` 物件。若系統未檢查結束事件就將殘缺 JSON 送入工具解析器，會引發解析例外並導致該回合費用無法歸因。
- **診斷日誌與防禦**：串流應從 `message_start` 保存可得的輸入 Usage，合併 `message_delta` 的累積值，收到 `message_stop` 才確認完整結束，並設定 `stream_idle_timeout_ms = 15000`。若未收到 `message_stop` 即斷線，將 `gen_ai.client` Span 標記為 `status: ERROR`、`agent.stream_truncated: true` 與 `last_event_type`，保存已知 Usage 並另行標記未知費用（字元數估算無法當財務下限，尤其遇到隱藏 thinking 或只收到部分輸出），禁止執行截斷的工具參數，並從上一個持久化 Checkpoint（見第 6 章）安全重試；當 5 分鐘內串流截斷率超過 `1%` 時觸發網路健康告警。

### 故障模式 4：成本帳本寫入競態與副作用冪等（Idempotency Collision）

- **現象**：當非同步 Worker 因超時觸發重試，或同一筆工單的兩個平行子任務同時回報完成時，若直接寫入帳本會造成內部成本重複歸因或預算重複扣減；若再次實際呼叫上游 API 則可能新增費用，而重送外部寫入更會造成重複退款。
- **診斷日誌與防禦**：所有寫入 `agent_cost_ledger` 的 SQL 語句必須使用 `ON CONFLICT (event_id) DO NOTHING`，且 Redis 扣款前先檢查冪等鍵 `ledger:dedup:{event_id}`（`SET NX EX 86400`），確保重試不會重複扣減每小時預算額度；退款等外部副作用須另用穩定的業務操作鍵，遇到逾時或回應遺失時，應先查核外部提交結果，再從 Checkpoint 恢復。

### Worked Example：計算 Prompt Cache 失效事故的 4 小時損失

假設 `OrderOps` 正常運作時，全套優化下的單筆工單平均成本為 `$0.012`。某次部署意外在 System Prompt 前段插入動態時間戳，導致快取在 **4 小時內維持 0% 命中**；若同時假設該期間所有請求均改用 Sonnet、完全停用快取（無快取寫入附加費）且 token 消耗回到基準值，單筆成本即為「全 Sonnet、停用快取」基準 `$0.1015`（依 ch01 首輪 `6,000` 起算的 5 輪序列：累計輸入 `42,000`、輸出 `1,750`）：

```text
[事故參數（均勻到達假設）]
- OrderOps 日工單量：50,000 筆/天（平均每小時 50,000 ÷ 24 = 2,083.33 筆/小時）
- 事故持續時間：4 小時
- 期間受影響工單數期望值：50,000 × 4 ÷ 24 = 8,333.33 筆
- 正常優化單筆成本：$0.012
- 快取失效後單筆成本（全 Sonnet 停用快取基準）：$0.1015

[成本計算]
1. 正常 4 小時預期成本：8,333.33 × $0.012  = $100.00（$25.00/hr）
2. 事故 4 小時實際成本：8,333.33 × $0.1015 = $845.83（$211.46/hr）
3. 4 小時淨多燒金額：  $845.83 - $100.00  = $745.83（事故總成本為正常 8.46×，淨增額為 7.46×）

[告警閾值設計]
- 若設定「5 分鐘滾動 Cache Hit Ratio < 60%」告警：
  5 分鐘觀測窗期望工單數為 173.61 筆，淨增額約 $15.54（若 5 分鐘即完成回滾，理論可省下 $730.30；
  實際損失仍須計入告警評估週期、回滾生效時間與在途工單）。
```

---

## 動手做

本節的完整可執行範例分別位於：
- TypeScript：[index.ts](../examples/ts/ch10/index.ts)
- Python：[main.py](../examples/py/ch10/main.py)

兩個範例皆實作了 `AgentTracer`、`BudgetCircuitBreaker`（含 `checkBeforeSend` 與 `recordUsage`）與 `runObservedTurn` / `run_observed_turn`，並模擬 `OrderOps` 工單在「正常快取命中（85%）」與「快取靜默失效（0%）」下的成本與 Span 輸出。

執行方式：

```bash
# Python
python3 books/enterprise-agents/examples/py/ch10/main.py

# TypeScript
npx tsx books/enterprise-agents/examples/ts/ch10/index.ts
```

預期輸出（兩語言一致）：

```text
=== OrderOps Telemetry Summary ===
Turn 1 (cached): cost=$0.00658, cache_hit=85.0%
Turn 2 (cache miss): cost=$0.01950, cache_hit=0.0%
Total spans recorded: 6
```

進階邊界驗證：建議修改 `main.py` 或 `index.ts` 中的測試參數，驗證兩種熔斷路徑與 Span 樹狀結構：
1. 將 `ticket_cost_so_far` 設為 `0.14` 並執行 Turn 2（`$0.01950`），確認 `recordUsage` 仍計入該筆已發生成本並回傳 `TICKET_BUDGET_EXCEEDED`（`$0.1595 > $0.15`），且 `agent.turn` 與根節點 Span 狀態標記為 `ERROR`。
2. 將 `max_hourly_burn_usd` 調降為 `0.02`，連續執行 Turn 1（`$0.00658`）與 Turn 2（`$0.01950`），確認總花費 `$0.02608` 超過 `$0.02` 時觸發 `HOURLY_BURN_EXCEEDED`，且第三次送出前呼叫 `checkBeforeSend` 會回傳 `CIRCUIT_OPEN_HOURLY_CAP`。
3. 印出 `tracer.get_trace(trace_id)`（TypeScript 為 `tracer.getTrace(traceId)`）的 6 筆 Span，確認 `agent.request` 為根節點、兩個 `agent.turn` 的 `parent_span_id` 指向根節點、Turn 1 的 `gen_ai.client` 與 `agent.tool` 指向 Turn 1，且 `agent.cost_usd` 加總與根節點的 `agent.total_cost_usd` 完全吻合。

---

## 自我檢核

1. （**入門｜10 分鐘**）在 `OrderOps` 的 OpenTelemetry Trace 中，為什麼不能只記錄 `agent.request` 層級的總延遲與 HTTP 狀態碼，而必須拆出 `gen_ai.client` 與 `agent.tool` Span？
2. （**進階｜15 分鐘**）當監控顯示 `Cache Hit Ratio` 從 `85%` 驟降至 `0%`，但 `Tool Error Rate` 與 `p95 Latency` 仍維持正常時，最可能的根因是什麼？請列出兩個排查步驟。
3. （**挑戰｜20 分鐘**）若 `OrderOps` 在尖峰流量 `12` req/s 下持續運作 10 分鐘，且單筆成本維持在 `$0.012`，請問 `BudgetCircuitBreaker` 的 `maxHourlyBurnUsd` 若設為 `$25.00` 會發生什麼問題？應如何調整？

### 參考解答

1. **拆出 `gen_ai.client` 與 `agent.tool` Span 的原因**：HTTP `200` 無法反映模型是否發生幻覺、輸出截斷（`max_tokens`）或工具參數錯誤；拆出 `gen_ai.client` 才能追蹤每個 `Turn` 的 `input_tokens`、`cache_read.input_tokens`、`finish_reasons` 與 `cost_usd`，而 `agent.tool` Span 則能定位究竟是模型推理慢（TTFT 升高）還是下游 ERP API 逾時導致違反 `2.5s / 18s` 的延遲 SLO。若不拆層，維運團隊在 p95 飆升時將無法區分該調整 Prompt、更換模型，還是擴容下游連線池。
2. **根因與排查步驟**：可能的原因之一是 System Prompt 或工具 Schema 前段被意外插入動態內容（如 `timestamp`、`trace_id` 或無固定順序的 JSON 鍵值），導致 Prompt Cache 前綴雜湊失效，但模型仍能正常完成推理與工具呼叫，因此錯誤率與延遲不受影響；但停用快取、未達快取門檻或其他快取設定變化也可能造成讀取量為零，單憑錯誤率與延遲正常不足以區分。排查步驟：(1) 檢查最近一次部署是否修改了 System Prompt 建構函式，並比對前後兩版的 `agent.prompt_prefix_sha256`；(2) 比對 `gen_ai.client` Span 中的 `cache_creation.input_tokens` 與 `cache_read.input_tokens`，確認是否出現每次請求都重新寫入或完全未命中快取的現象；若確認為前綴污染，應立即回滾部署並將動態欄位下移至 `messages` 尾端。
3. **尖峰流量下的預算熔斷調整**：`12` req/s 持續 10 分鐘（600 秒）共處理 `7,200` 筆工單，以單筆 `$0.012` 計算，燃燒速率為 `$0.144/s`，10 分鐘內會消耗 `$86.40`（若視窗初始耗用為零，約 `174s` 觸及 `$25`、`313s` 觸及 `$45`），導致正常尖峰流量在 3 分鐘內就被熔斷器誤殺。若該小時剩餘 50 分鐘回到日均速率（`$25/hr × 5/6 = $20.83`），題設下整小時約 `$107.23`；因此 `$120–$150/hr` 可作為該情境的候選熔斷閾值（若尖峰持續整小時則是 `$518.40/hr`），實際上線仍須依時間窗邊界、既有耗用、流量分布與併發結算情況校準，並搭配「5 分鐘 `Cache Hit Ratio < 60%`」與「單筆上限 `$0.15`」精準攔截，才能在不傷及正常尖峰流量的前提下阻斷成本雪崩。

---

## 延伸閱讀

- [OpenTelemetry Semantic Conventions for Generative AI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) — 本章 `gen_ai.client` Span 欄位命名與語意慣例的官方規範。
- Anthropic Prompt Caching 文件 — 了解 `cache_creation_input_tokens` 與 `cache_read_input_tokens` 的計費與 TTL（5m / 1h）行為。
