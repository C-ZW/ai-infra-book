# 第 5 章：多 Agent 協作架構：Orchestrator、Handoff 與隔離沙盒

## 從你已知的出發

做過微服務架構的後端工程師，對**分散式 Saga 編排與補償**（Orchestrated Saga）並不陌生：當單一服務要同時協調訂單、庫存、金流與物流時，把所有邏輯塞進同一支 Transaction Script 會讓狀態耦合、權限過大、失敗恢復困難；因此我們改由一個中央 Orchestrator 依序或平行派發子任務給各領域服務，只收集結構化的執行結果，再決定下一步或觸發補償。

多 Agent 協作（Multi-Agent Orchestration）的**成立邊界**就在這裡：當單一 `Agent Loop` 需要攜帶過多工具、處理跨領域調查，或同時握有唯讀與高風險寫入權限時，拆成「中央協調者 + 專責 Sub-agent」能隔離 Context 汙染、縮小工具面（Tool Surface），並把權限鎖在最小範圍內。

兩者的**失效邊界**同樣明確：傳統 Saga 透過命令、RPC 或事件協調各服務的本地交易與補償，步驟通常採明確契約，但不必然是確定性 RPC（一樣可能逾時、重複執行或依外部狀態產生不同結果）；Agent 之間的傳遞卻包含自然語言推理與機率性工具呼叫，這帶來兩個傳統微服務沒有的新問題——**上下文膨脹**（Context Bloat）與**交接失真**（Handoff Drift，例如摘要遺漏已退款金額，或將「物流狀態未知」改寫成「尚未出貨」）。如果把 Sub-agent 的完整對話與工具回傳原封不動塞回主 Agent，主 Agent 的 Context Window 會在幾回合內被垃圾資訊淹沒；反之，如果摘要過度簡化，主 Agent 又會因為缺少關鍵證據而誤判。本章直接從單 Agent 的擴展瓶頸切入，建立三大協作拓撲、Handoff 壓縮契約、平行扇出容錯與 SDK 選型邊界。

---

## 核心機制

### 單 Agent 的擴展瓶頸

在 `OrderOps` 基準設定中，系統共有 `18` 個工具（12 唯讀 Read-only + 6 寫入／金流 Mutating），單一 Agent 的基準前綴大小為 `6,000` tokens（System Prompt 2,400 + 18 工具 Schema 3,600）。當業務繼續擴張到 30–50 個工具時，單 Agent 會同時撞上三個擴展瓶頸（實際影響幅度依工具描述重疊度與任務分布而異）：

1. **工具誤選率上升**：模型在每個 `Turn` 都要從數十個相似的 JSON Schema 中挑出正確工具，描述重疊度一高，參數填錯或叫錯工具的機率會顯著上升。
2. **長調查汙染決策上下文**：查物流軌跡、比對倉庫庫存與翻閱帳務明細會產生大量中間 JSON 與除錯訊息。這些只屬於「調查階段」的雜訊留在主對話裡，會稀釋後續「退款仲裁」時的注意力（Context Rot，見 ch03）。
3. **權限無法最小化**：只要同一個 `Agent Loop` 裡同時掛著 `get_order` 與 `issue_refund`，Prompt Injection 或模型幻覺就有機會直接觸發金流寫入，違反最小權限原則（詳細權限治理見 ch09）。

### 三大協作拓撲與選型

企業級多 Agent 系統通常收斂為三種基本拓撲，彼此可依任務複雜度組合使用：

```text
1. Router + Specialists（分流＋專責）
   Ticket -> Haiku Router (0 tools)
               |-- shipping_investigator (6 tools)
               |-- inventory_investigator (6 tools)
               +-- refund_arbitrator (Opus, 6 tools)

2. Orchestrator-Workers（協調者＋平行工人）
   Orchestrator
     |--[fan-out]--> Worker A (carrier_status)
     |--[fan-out]--> Worker B (warehouse_stock)
     +--[fan-out]--> Worker C (billing_ledger)
     <--[compressed WorkerHandoff]--

3. Evaluator-Optimizer（生成＋審查迴圈）
   Generator Agent --[draft]--> Evaluator Agent
        ^                              |
        +------[reject + feedback]-----+
```

- **Router + Specialists**：適合工單意圖明確、各領域邊界清楚的場景。Router 本身不掛任何工具（`0` 個工具），只輸出結構化路由決策，延遲與成本極低。
- **Orchestrator-Workers**：適合單一工單需要同時查多個獨立系統（例如同時查物流與帳務）的場景。Orchestrator 動態決定要扇出（Fan-out）哪些唯讀 Worker，等結果收斂後再決定是否升級給高階模型。
- **Evaluator-Optimizer**：適合合規報告、法務回覆或高風險退款理由生成，由獨立的 Evaluator 檢查事實引用與政策合規性，不通過則退回重寫（最多設 `max_revisions = 2` 防無窮迴圈）。

### Wire-Level 呼叫與 Sub-agent Handoff 契約

多 Agent 協作的成敗，取決於**線上請求邊界**與 Sub-agent 回傳給父層的**交接契約**（Handoff Contract）。

在分流階段，Haiku Router 呼叫 `messages.create` 時必須省略 `tools`（或設 `tools: []`）與非必要取樣參數（依模型官方文件確認），`max_tokens` 鎖在 `256`（若啟用 adaptive thinking 需預留足夠預算或降低 `output_config.effort`），並透過 `output_config.format`（`{ type: "json_schema", schema: ... }`）約束結構化 JSON 輸出；若要啟用 Prompt Caching，靜態路由 System Prompt 必須達到該模型的最小快取門檻（須依官方文件逐模型確認，例如 `claude-opus-5-5` 為 `512` tokens、`claude-sonnet-5` 與先前的 Sonnet 4.5／4.6 為 `1,024` tokens，至於 Sonnet 5.5 則依其官方文件確認，低於門檻時 `cache_control: { type: "ephemeral" }` 會靜默不寫入），且絕對不能把動態 `ticketId` 放在 `cache_control` 斷點之前。Router 回傳後，應用程式必須明確處理 `refusal`、`max_tokens` 截斷、空內容與解析失敗，並由程式驗證 `lane`、任務白名單、去重、數量與 `confidence` 範圍；Router 的輸出僅授權查詢白名單內的唯讀任務，工具服務仍須以可信的租戶與身分執行服務端授權。

在調查階段，每個唯讀 Worker 獨立執行自己的 `Agent Loop`。當模型回傳 `stop_reason: "tool_use"` 時，回應 `content` 內含 `tool_use` 區塊（附帶 `id: "toolu_..."`、`name` 與 `input`）；下一則 `user` 訊息開頭必須放上所有對應的 `tool_result`（逐一配對 `tool_use_id`，失敗時設 `is_error: true`），並保留完整的 assistant `content`（包含適用的 `thinking` 區塊），直到 `stop_reason === "end_turn"` 或觸及 `max_turns = 4` 上限；若使用 Streaming，必須等完整訊息收斂且通過本地驗證後才派發工具，並對 SSE `error` 事件分類處理。每次 API 回應的 `usage` 欄位（`input_tokens`、`output_tokens`、`cache_read_input_tokens`、`cache_creation_input_tokens`）都會逐次記錄，依該次呼叫的模型與各類費率（一般輸入、輸出、快取讀取及對應 TTL 的快取寫入）分別換算為美元後累加寫入 `WorkerHandoff.costUsd`；逾時等無法確認的帳務則另行標示並對帳。

父層 Orchestrator **絕對不該接收 Sub-agent 的完整 `messages` 陣列或原始工具回傳**，而只應接收固定結構的壓縮物件。為了防範交接失真與 Prompt Injection，模型產生的 `summary` 必須與後端驗證的 `facts` 分開保留，`facts` 應具備版本化欄位、大小上限、證據來源與觀測時間，例外則映射為安全錯誤碼。以下是 `OrderOps` 採用的 `WorkerHandoff` 契約（完整實作見 `examples/ts/ch05/index.ts` 與 `examples/py/ch05/main.py`）：

```typescript
export interface WorkerHandoff {
  workerId: string;
  task: string;
  status: "ok" | "timeout" | "error";
  summary: string;                  // 1-2 句精簡結論，供 LLM 閱讀（不可信來源）
  facts: Record<string, unknown>;   // 後端驗證的結構化關鍵欄位（orderId, status, totalUsd）
  latencyMs: number;
  costUsd: number;
}
```

這個設計把「調查過程的 3,000–8,000 tokens 雜訊（示意值）」隔離在 Worker 自己的區域變數裡，只讓精簡的結構化 `WorkerHandoff`（約 120–180 tokens 示意值，依實際欄位長度而定）進入父層 Context。

### 生產配置基線與狀態儲存

為了讓平行扇出在 `OrderOps` 的多步處置延遲 SLO（p95 ≤ `18` 秒）內穩定收斂，生產環境必須鎖定以下參數與儲存結構：

- **逾時、期限與併發上限**：單一 Worker 執行上限 `WORKER_TIMEOUT_MS = 8_000`（包含最多 `max_turns = 4` 回合），單次工單整體單調時鐘（monotonic）Wall-clock 期限 `18_000ms`（依序分配給 Router、Worker、仲裁與持久化）。在尖峰 `12 tickets/s` 下，每筆扇出 3–4 個 Worker 代表 `36–48` 次 Worker 啟動／秒（若耗滿 4 回合則達 `144–192` 次呼叫／秒），因此除了單工單 `MAX_PARALLEL_WORKERS = 4` 之外，還必須配置跨工單的全域／租戶併發限制、RPM／token 配額與有限佇列背壓，並分別追蹤成功、逾時與人工轉介。
- **Redis 租約與退款冪等**：派發前以原子取鎖（`SET ... NX PX` 搭配租約持有者 token 與安全比對釋放）寫入 `orderops:ch05:orch:{ticketId}:lock`（TTL `30s`），並以持久狀態的版本檢查或 fencing token 拒絕逾時後仍嘗試提交的舊持有者。示範用的 `orderops:ch05:idem:{orderId}:{action}`（TTL `86400s`）僅供短時防重；生產環境退款必須使用包含 `tenant_id` 與穩定 `refund_intent_id` 的持久唯一鍵，綁定請求參數與金流供應商的冪等鍵（避免阻擋合法的第二筆部分退款，也防止 24 小時後重放），並定義「供應商已接受、回應遺失」時的查單與對帳流程。
- **PostgreSQL 交接稽核表**：每次 Worker 結束後寫入 `agent_handoffs (handoff_id UUID PRIMARY KEY, ticket_id TEXT NOT NULL, workflow_run_id UUID NOT NULL, attempt_no INT NOT NULL, worker_id TEXT NOT NULL, status TEXT NOT NULL, facts JSONB NOT NULL, latency_ms INT NOT NULL, cost_usd NUMERIC(10,6) NOT NULL, created_at TIMESTAMPTZ DEFAULT now())`，並在 `(ticket_id, created_at)` 建立複合索引供查詢使用；另以符合入帳語意的持久唯一約束（例如 `(workflow_run_id, attempt_no, worker_id)`）搭配交易處理，區分工作流與重試次數並防止重複入帳。
- **預算熔斷保護**：Orchestrator 在派發前會預留最大待完成支出並檢查累計 `totalCostUsd`（區分已知成本與逾時後尚未確認的帳務）；若單筆工單累計成本超過 `$0.050`（約為分層基準 `$0.005085` 的 10 倍），立即停止後續非必要扇出並轉入人工審核，防止異常迴圈燒毀配額。

### Worked Example：單一 Sonnet（18 工具）vs 分層路由與隔離（Haiku Router + 3 Specialists）

以 `OrderOps` 的基準數字計算單筆工單的**純前綴輸入成本**（僅計入 System Prompt 與工具 Schema 前綴，不含快取折扣與各層輸出；Claude Haiku 5.5 牌價為 `$0.10 / $0.50` USD / MTok，Claude Sonnet 5.5 牌價為 `$2.00 / $10.00` USD / MTok，Claude Opus 5.5 牌價為 `$4.00 / $20.00` USD / MTok）：

```text
[方案 A：單一 Sonnet 5.5 攜帶全部 18 個工具]
- 前綴大小：6,000 tokens（System Prompt 2,400 + 18 工具 Schema 3,600）
- 假設 5 回合對話、五回合累計前綴：
  前綴累計輸入 = 6,000 × 5 = 30,000 tokens
- 前綴輸入成本 = 30,000 × ($2.00 / 1,000,000) = $0.060000 / 筆
- 工具選擇風險：18 個工具同台競爭，多步驟工單誤觸寫入工具的風險較高。

[方案 B：Haiku Router (0 工具) + 專責 Specialist (各 6 工具)]
（容量假設：每筆平均 1 個唯讀 Worker、20% 工單額外觸發 Opus 仲裁）
1. Haiku Router（1 回合、0 工具、前綴 450 tokens）：
   前綴輸入成本 = 450 × ($0.10 / 1,000,000) = $0.000045 / 筆
   （註：若計入 90 tokens 輸出則另加 $0.000045，合計 $0.000090 / 筆）
2. 唯讀調查 Worker（Haiku 5.5、6 工具、前綴 2,800 tokens、2 回合）：
   前綴累計輸入 = 2,800 × 2 = 5,600 tokens
   前綴輸入成本 = 5,600 × ($0.10 / 1,000,000) = $0.000560 / 筆
3. 高風險退款仲裁（僅 20% 工單觸發 Opus 5.5、6 工具、前綴 2,800 tokens、2 回合）：
   觸發時前綴成本 = (2,800 × 2) × ($4.00 / 1,000,000) = $0.022400 / 筆
   攤提至全量工單（× 20%）= $0.004480 / 筆
- 方案 B 合計平均純前綴成本 = $0.000045 + $0.000560 + $0.004480 = $0.005085 / 筆
- 純前綴成本降幅 = ($0.060000 - $0.005085) / $0.060000 = 91.53%
```

透過拆分工具面與分層模型，純前綴輸入成本從每筆 `$0.060000` 降至 `$0.005085`（降幅 `91.53%`；若平均每筆扇出 2 個等量 Worker 則為 `$0.005645`，降幅 `90.59%`），同時把 18 個工具的選擇空間縮小為每個 Specialist 僅面對 6 個工具（完整月度財務總帳與快取疊加計算見 ch08）。

### 自建 Loop vs Claude Agent SDK 選型邊界

實作多 Agent 編排時，團隊常面臨「自己寫 `messages.create` 迴圈」還是「採用官方 Claude Agent SDK（TypeScript `@anthropic-ai/claude-agent-sdk` 或 Python `claude-agent-sdk`）」的選擇：

| 評估維度 | 自建 Orchestrator Loop | Claude Agent SDK |
|---|---|---|
| 控制粒度 | 完全掌控每次 `messages.create`、自訂 Retry/Circuit Breaker 與任意資料庫狀態機 | 內建 Sub-agent 派發、工具執行迴圈與標準 Hook 生命週期 |
| 隔離與沙盒 | 需自行實作檔案系統／行程隔離與 `max_turns` 保護 | 原生支援工作目錄隔離、權限控制（`allowedTools` / `disallowedTools`）與 Sub-agent 上下文切分（租戶／行程隔離仍須搭配實際沙盒） |
| 適用場景 | 需要深度整合既有微服務佇列、自訂 Saga Checkpoint（見 ch06）或極致壓榨延遲 | 開發內部工程助手、程式碼／文件自動化管線或標準多步驟研究代理 |

在 `OrderOps` 這類高併發交易系統中，我們通常選擇自建 Orchestrator Loop，原因在於必須把 `WorkerHandoff` 與外部 PostgreSQL／Redis 狀態機緊密綁定，並在 `429`／`529` 發生時精準控制退避與降級；反之，若團隊建置的是離線程式碼審查或知識庫研究代理，直接採用 Claude Agent SDK 的 `allowedTools`（Python 為 `allowed_tools`）預先核准清單與 `disallowedTools`（細節依官方 SDK 文件確認）搭配沙盒環境，能省下大量樣板碼。

---

## 故障模式與防禦

多 Agent 系統最常見的線上故障不是單一模型答錯，而是扇出雪崩與部分失敗處理不當。線上維運必須針對以下四種故障建立結構化 log（`trace_id`、`ticket_id`、`worker_id`、`http_status`、`retry_after_ms`、`stop_reason`、`cache_read_input_tokens`、`handoff_status`）與對應告警：

1. **平行扇出部分失敗與逾時**（Partial Failure & Timeout）：
   使用 `Promise.all`（TS）或未加保護的 `asyncio.gather`（Python）時，只要其中一個唯讀 Worker 逾時或拋出例外，整個請求就會直接失敗，浪費其他已完成 Worker 的 token 成本。
   **防禦**：一律使用 `Promise.allSettled`（TS）或 `asyncio.gather(..., return_exceptions=True)`（Python），並為每個 Worker 設定獨立的 `WORKER_TIMEOUT_MS = 8_000` 與 `max_turns = 4` 上限（同時傳播取消訊號與 deadline）。退款與唯讀結案必須由**應用程式**依路由強制檢查必要證據（例如退款必須同時具備有效的 `carrier_status` 與 `billing_ledger`，且核對租戶、訂單、幣別、付款狀態與證據時效）；缺件、衝突或過期一律降級為 `degraded_pending_hitl`（人工審批），金流寫入前再由可信服務複檢可退款餘額。告警閾值：`worker_timeout_rate > 2%`（以所有 Worker 派發為分母）或 `degraded_hitl_rate > 5%`（以所有工單為分母），採 5 分鐘滾動視窗且最低樣本數 ≥ `100`。
2. **上游限流與過載雪崩**（429 / 529 Cascade）：
   單筆工單同時扇出 3–4 個 Worker，尖峰時會讓 API 呼叫量瞬間放大 3–4 倍，觸發 HTTP `429`（附帶 `retry-after` header）或 `529 overloaded_error`。若所有 Worker 同時無腦重試，會引發重試風暴；此外 SDK 預設自身也會重試（預設次數依 SDK 版本文件確認），若外層再包重試而不關閉內建重試，內外層各「1 次初始呼叫 + 2 次重試」會膨脹成 `(1+2) × (1+2) = 最多 9 次` 嘗試。
   **防禦**：限制單工單併發上限 `MAX_PARALLEL_WORKERS = 4` 並搭配全域限流；明確設定 SDK `maxRetries = 0`（由外層統一控制），Worker 內部對 `429` 優先讀取 `retry-after` 秒數等待，對 `529` 採用指數退避加 Full Jitter（`sleep = random(0, min(cap, base × 2^n))`，`n` 從 `0` 起算，`base = 500ms`、`cap = 8_000ms`、`max_retries = 2`；第 1、2 次重試分別為 `0–500ms` 與 `0–1,000ms`，單次等待上界為 `1,000ms`，兩次累計等待上界為 `1,500ms`）；若 `Retry-After` 或下一次嘗試將超出剩餘 deadline，直接降級。告警閾值：`429_rate > 1%` 或 `529_rate > 0.5%`（以所有 API 請求為分母，5 分鐘滾動視窗且最低樣本數 ≥ `100`）。
3. **Streaming 半途斷線與靜默快取失效**（Partial SSE & Silent Cache Miss）：
   啟用 Streaming 時，SSE 連線可能在 `content_block_delta` 傳送一半時中斷而未收到 `message_stop`，導致 `tool_use.input` 留下殘缺 JSON；另一種隱性故障是可快取前綴低於該模型的最小門檻（須依官方文件逐模型確認）導致 `cache_creation_input_tokens = 0` 且 `cache_read_input_tokens = 0`，或是將動態 `ticketId` 誤放在 `cache_control` 斷點之前，導致每次請求都 miss 並重複寫入快取。
   **防禦**：SSE 解析器必須驗證 `message_stop` 事件與完整 JSON Schema 後才允許執行工具，否則視為可重試的傳輸錯誤；同時對符合快取條件的請求監控整體快取讀取覆蓋率 `cache_hit_rate = cache_read_input_tokens / (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)`，低於 `80%` 立即告警。
4. **無限遞迴委派與跨 Agent 寫入衝突**（Delegation Loop & Write Collision）：
   如果 Agent A 能呼叫 Agent B，而 Agent B 的工具清單裡又包含呼叫 Agent A，兩者會在邊界條件不明時互相踢皮球直到耗盡預算；或者兩個平行 Worker 同時對同一筆訂單執行補償寫入，造成重複退款。
   **防禦**：由派發器（Dispatcher）在拓撲上強制有向無環圖（DAG）結構，執行 `depth`（呼叫深度，預設上限 `max_depth = 2`）與整筆工單的派發總數上限。所有唯讀調查 Worker 嚴格禁止掛載 Mutating 工具；只有單一仲裁 Specialist 能執行寫入，且必須攜帶基於租戶與穩定退款意圖 ID 的 `IdempotencyKey`（底層佇列與 Saga 重放細節見 ch06）。

---

## 動手做

本節的完整可執行程式碼位於 `books/enterprise-agents/examples/ts/ch05/index.ts`（TypeScript）與 `books/enterprise-agents/examples/py/ch05/main.py`（Python）。兩者皆內建離線模擬模式（無須 `ANTHROPIC_API_KEY` 即可執行驗證）；設定環境變數 `ANTHROPIC_API_KEY` 後，Haiku Router 會切換為真實 Claude API 呼叫，而 Worker 與 Opus Specialist 仍維持本地模擬，方便在不消耗高額 Opus 配額的情況下驗證路由與成本／降級邏輯。

### 關鍵實作：平行扇出與部分失敗降級

在 TypeScript 版本（`examples/ts/ch05/index.ts`）中，`orchestrateTicket` 先由 Haiku Router 產生結構化路由，再用 `Promise.allSettled` 與 `withTimeout` 平行執行唯讀 Worker，最後僅將壓縮後的 `WorkerHandoff[]` 交給應用程式檢查必要證據並決定是否升級給高階 Specialist：

```typescript
const settled = await Promise.allSettled(
  decision.parallelReadOnlyTasks.map(async (task) => {
    const startedAt = Date.now();
    try {
      return await withTimeout(runReadOnlyWorker(ticket, task), WORKER_TIMEOUT_MS, task);
    } catch (err) {
      throw { err, latencyMs: Date.now() - startedAt };
    }
  }),
);

const handoffs: WorkerHandoff[] = settled.map((res, idx) => {
  const task = decision.parallelReadOnlyTasks[idx];
  if (res.status === "fulfilled") return res.value;
  const { err, latencyMs } = res.reason as { err: unknown; latencyMs: number };
  const isTimeout = err instanceof WorkerTimeoutError;
  const errorCode = isTimeout ? "WORKER_TIMEOUT" : "WORKER_EXECUTION_ERROR";
  // 詳細例外僅寫入受控日誌，不將原始錯誤字串交給父層
  return {
    workerId: `worker-${task}`,
    task,
    status: isTimeout ? "timeout" : "error",
    summary: `Worker failed with safe code ${errorCode}`,
    facts: { errorCode, costStatus: "unconfirmed" },
    latencyMs,
    costUsd: confirmedCostUsd, // 帶入失敗前已確認的累計費用；未確認的在途帳務由 costStatus: "unconfirmed" 另行對帳
  };
});
```

Python 版本（`examples/py/ch05/main.py`）採用相同架構，以 `asyncio.wait_for` 搭配 `asyncio.gather(*coros, return_exceptions=True)` 實作隔離扇出。

### 執行驗證與預期輸出

```bash
# TypeScript（於 books/enterprise-agents/examples/ts 目錄下）
npx tsx ch05/index.ts

# Python
python3 books/enterprise-agents/examples/py/ch05/main.py
```

執行後會依序處理一般物流延遲工單 `TKT-5001` 與高風險退款工單 `TKT-5002`，以下為 TypeScript 離線模擬模式的示意輸出節錄（依範例內模擬的 token 數量計算，採用 2 個 Worker 與 1 次 Opus 呼叫，與上節容量假設不同；若需獨立重算或驗證兩筆 `totalCostUsd`，須核對範例程式內各模型呼叫的輸入、輸出與快取用量及實際執行結果；Python 輸出結構相同但欄位採 `snake_case`）：

```text
[ch05] Running OrderOps Orchestrator (OFFLINE SIMULATION)
{
  "ticketId": "TKT-5001",
  "route": { "lane": "shipping_investigator", "parallelReadOnlyTasks": ["carrier_status", "warehouse_stock"] },
  "finalAction": "resolved_read_only",
  "totalCostUsd": 0.00051
}
{
  "ticketId": "TKT-5002",
  "route": { "lane": "refund_arbitrator", "parallelReadOnlyTasks": ["carrier_status", "billing_ledger"] },
  "finalAction": "refund_approved_by_opus_specialist",
  "totalCostUsd": 0.01811
}
```

### 邊界測試建議

1. **模擬單一 Worker 逾時**：在 `runReadOnlyWorker` 針對 `billing_ledger` 注入超過 `WORKER_TIMEOUT_MS`（`8_000ms`）的延遲，驗證 `TKT-5002` 的 `handoffs` 中該項目是否正確標記 `status: "timeout"`，且 `finalAction` 降級為 `degraded_pending_hitl` 而非未捕獲例外。
2. **驗證缺少帳務證據時不放行退款**：當 Router 遺漏 `billing_ledger` 或後端回傳 `not_found`（`status: "error"`）時，驗證 `refund_arbitrator` 仍會降級為 `degraded_pending_hitl`。

---

## 自我檢核

1. **（入門｜10 分鐘）** 在 `OrderOps` 的 Router + Specialists 架構中，為什麼我們刻意讓 Haiku Router 攜帶 `0` 個工具，而不是順便讓它掛載 2 個常用查詢工具？
2. **（進階｜15 分鐘）** 如果 `OrderOps` 的某個 `billing_ledger` Worker 在 `Promise.allSettled` 中回傳 `status: "timeout"`，而 `carrier_status` Worker 回傳 `status: "ok"`，請說明 Orchestrator 應該如何處理「一般物流查詢工單」與「高風險退款工單」的差異？
3. **（挑戰｜20 分鐘）** 假設你的團隊想在 Evaluator-Optimizer 迴圈中加入「最大重試 2 次」與「每次評估結果必須包含結構化違規欄位」的限制，請設計這組 Handoff 介面，並說明若 Evaluator 本身發生 529 Overloaded 時該如何降級而不讓工單卡死。

### 參考解答

1. **Router 零工具原則**：Router 的唯一職責是分類與派發。若掛載查詢工具，模型可能忍不住先呼叫工具再分類，導致延遲從單次呼叫（分流基準 SLO 為 p95 ≤ `2.5s`）暴增為多回合 `Agent Loop`，同時把工具 Schema 前綴（每個工具約 `200` tokens，2 個工具即 `400` tokens）乘上全量 `50,000` 筆／天的流量（每日多出 `20,000,000` 輸入 tokens，按 Haiku ≤100K 無快取牌價約多 `$2`／日），浪費不必要的輸入成本與配額。
2. **部分失敗的差異化降級**：對「一般物流查詢工單」，`carrier_status` 成功即足以回答出貨進度，Orchestrator 可直接採用既有事實回覆並註明帳務系統暫時無法查詢；但對「高風險退款工單」，缺少 `billing_ledger` 的付款／已退金額確認會導致超額退款風險，因此 Orchestrator 必須將 `finalAction` 降級為 `degraded_pending_hitl`，將已收集的 `WorkerHandoff[]` 連同失敗原因轉交人工審批而非自動放行。
3. **Evaluator-Optimizer 降級設計**：可定義 `EvaluationHandoff { passed: boolean; violations: string[]; revisionCount: number; evaluatorStatus: "ok" | "overloaded" }`。`max_revisions = 2` 代表「初稿 + 最多 2 次改寫」（最多 3 次語意評估，與每次評估最多 2 次傳輸重試分開計算）。每次退回 Generator 時遞增 `revisionCount` 並附上 `violations` 陣列；當 `revisionCount >= 2` 仍未通過，或 Evaluator 遭遇 `529 overloaded_error` 且經過指數退避加 Full Jitter（`max_retries = 2`）仍失敗時，應立即終止迴圈並標記 `escalated_to_human_review`，將「評估未完成」狀態、最後一版草稿與 `violations` 一併送入人工審核佇列，確保工單不會無限重試或靜默失敗。

---

## 延伸閱讀

- Anthropic Engineering：*Building effective agents*（官方對 Router、Orchestrator-Workers 與 Evaluator-Optimizer 三大協作模式的設計指引）
- Anthropic Docs：*Claude Agent SDK*（`@anthropic-ai/claude-agent-sdk` / `claude-agent-sdk` 的 Sub-agent 派發與權限隔離機制）
