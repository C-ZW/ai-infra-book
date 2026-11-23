# 第 1 章：從 Workflow 到 Agent：執行迴圈、狀態機與可控邊界

企業導入 LLM 時，最常見的架構誤判是「把確定性流程硬寫成 Agent」，或反過來「把開放式決策硬塞進寫死的 DAG」。本章從後端工程師熟悉的系統模型切入，建立 `Agent Loop` 的狀態機骨架，並以主軸系統 `OrderOps` 跑通第一版具備強制終止契約的執行迴圈。

## 從你已知的出發

做過後端服務的工程師，對**有限狀態機與事件迴圈**（FSM + Event Loop）都不陌生：一個請求進來，系統根據當前狀態與外部事件決定下一個狀態，直到進入終止態（`COMPLETED`、`FAILED` 或 `TIMEOUT`）。

`Agent Loop`（模型推理 → 工具執行 → 觀測回填的狀態轉移迴圈）本質上就是一個**由外部程式驅動的 FSM + Event Loop**。兩者的核心對應如下：

- **LLM 本身無狀態**：每次呼叫 Claude Messages API，模型都不記得上一輪發生過什麼；所有對話歷史（`messages` 陣列）都由你的後端狀態機負責保存與重送。
- **狀態轉移函數**（Transition Function）：傳統 FSM 的轉移規則寫死在 `switch/case` 裡；在 `Agent Loop` 中，LLM 根據當前 `messages` 產出 `stop_reason` 與內容區塊，決定下一步要呼叫哪個工具或直接結束。
- **Event Loop 驅動**：外部 `while` 迴圈扮演事件迴圈，每次呼叫 API 取得一個 `Turn`（回合）的輸出，若為工具呼叫就執行對應後端函式並將結果寫回 `messages`，再進入下一輪。

**橋接成立邊界與失效邊界：**

- **成立邊界**：迴圈的控制權、終止條件（`max_turns`、預算上限、wall-clock timeout）與副作用執行權，全部留在你的後端程式碼中，與傳統 FSM 完全一致。
- **失效邊界**：傳統 FSM 的狀態轉移是**確定性**（Deterministic）且可窮舉的；LLM 的轉移帶有**機率性**，同樣的輸入在不同時間可能選出不同工具順序，甚至在邊界條件下陷入重複呼叫同一個工具的無窮迴圈。因此不能只靠模型「自覺停止」，必須由外部狀態機強制執行護欄。

## 核心機制

### Workflow 與 Agent 的決策光譜

不是每個企業需求都需要開放式 `Agent Loop`。延遲、成本與可預測性都要求我們先判斷該用確定性 Workflow 還是 Agent：

1. **Augmented LLM**：單次呼叫 LLM，搭配檢索或單一工具查詢，無迴圈（若需由模型讀回 client-tool 結果再作答，通常會多一次 Messages 請求）。適合簡單分類或摘要。
2. **Prompt Chaining**（串鏈）：固定步驟 `A → B → C`，每步之間由程式碼做格式檢查或閘門（Gate）。適合合約審閱、固定報表產出。
3. **Routing**（路由分流）：先用輕量模型或規則分類，再導向不同專用處理鏈。例如 `OrderOps` 將簡單查詢導向低成本模型，複雜客訴導向多步處置。
4. **Parallelization**（平行化）：同時派發多個獨立子任務（如同時查訂單與查庫存）或多次投票，再由程式碼彙整。
5. **Orchestrator-Workers**（編排者與工作者）：由主模型動態拆解子任務並派發給專責 Worker，適合任務結構無法事先寫死的場景。
6. **Evaluator-Optimizer**（評估與優化迴圈）：一個模型產出、另一個模型或規則檢查器評分，不通過就退回重寫，直到達標或達重試上限。

**選型準則**：判斷的核心在於**下一步的決策權屬於程式碼還是模型**。確定性 Workflow 也能依觀測結果走條件分支；只有當「下一步該查什麼資料、呼叫幾個工具」必須交由模型依前一步觀測動態決定時，才啟用 `Agent Loop`。

### `stop_reason` 驅動的狀態轉移與 Wire-Level 契約

在 Claude Messages API 中，每次 `Turn` 結束都會回傳 `stop_reason` 欄位。外部狀態機不應解析模型回傳的自然語言來猜測是否結束，而應直接對 `stop_reason` 做窮舉分派（下圖為本章本地工具迴圈的核心子集；完整 API 的其他 `stop_reason` 值如 `stop_sequence`、`pause_turn` 與 `model_context_window_exceeded` 等，以官方 Handling Stop Reasons 文件列舉為準）：

```text
[START]
   │
   ▼
messages.create() ──▶ 檢查預算與 wall-clock timeout
   │
   ├── stop_reason == "end_turn"    ──▶ [COMPLETED]（提取 text 回覆）
   ├── stop_reason == "tool_use"    ──▶ 執行本地工具 ──▶ 回填 tool_result ──▶ 下一輪
   ├── stop_reason == "max_tokens"  ──▶ [ERROR / TRUNCATED]（單輪輸出截斷）
   └── stop_reason == "refusal"     ──▶ [REFUSED]（安全策略拒答，立即終止）
```

在真實的 Wire-Level HTTP 回應（以下為關鍵欄位節錄）中，當 `stop_reason` 為 `"tool_use"` 時，`content` 陣列會包含一個或多個 `tool_use` 區塊，每個區塊帶有唯一的 `id`（例如 `toolu_01A09q90qw90lq917835lq9`）、工具名稱 `name` 與結構化 `input` 物件：

```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "type": "message",
  "role": "assistant",
  "stop_reason": "tool_use",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lq9",
      "name": "get_order",
      "input": { "order_id": "ORD-88412", "tenant_id": "tn_apac_01" }
    }
  ],
  "usage": {
    "input_tokens": 6000,
    "output_tokens": 350,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0
  }
}
```

你的後端必須原樣保留上一輪的 `assistant` 內容區塊（含 thinking signature），並在緊接的 `user` 訊息中回傳對應的 `tool_result` 區塊，且 `tool_use_id` 必須與 `id` 精確配對；若同則 `user` 訊息另附文字提示，`tool_result` 必須排在文字區塊之前。若模型在同一輪同時發出多個 `tool_use`（例如同時呼叫 `get_order` 與 `check_inventory`），所有對應的 `tool_result` 必須放在同一則 `user` 訊息內依序回填，缺一不可（具體錯誤碼與驗證細節依官方 Tool Use 文件為準）。若工具執行失敗（例如訂單不存在或參數格式錯誤），不應直接拋出未捕捉例外中斷整個迴圈，而應正規化為穩定錯誤碼並回傳 `is_error: true`（例如 `{"error": "order_not_found", "retryable": false}`），讓模型在下一輪有機會修正參數或改走其他路徑（工具契約與 MCP 細節見第 2 章）。

此外，單輪內對互相獨立且可充分並行的唯讀工具適合平行執行（`Promise.all` 或 `asyncio.gather`），理想延遲近似最慢呼叫的耗時（實際仍須加上排程與彙整開銷並考慮資源限制）；但若同一輪同時包含唯讀與寫入型工具，必須先執行唯讀檢查並在寫入端原子驗證前置條件；限制單輪寫入數量可縮小故障範圍，但仍須配合寫入端原子驗證、冪等性及逾時後對帳或補償機制，跨系統一致性不能由寫入數量限制單獨保證。

### 生產級配置基線與狀態儲存邊界

裸跑一個 `while` 迴圈很容易，但要上線承受 `OrderOps` 尖峰 `12` req/s 的負載，必須先釘死以下配置基線：

- **迴圈與預算護欄**：`maxTurns = 8`、`maxTotalInputTokens = 50,000`（累計輸入上限，高於 5 回合基準 `42,000` tokens）、`maxCostUsd = 0.25`、`wallClockTimeoutMs = 18,000`（對齊多步處置 p95 SLO）、`turnTimeoutMs = 5,000`。需注意回合結束後的累計檢查屬於軟性斷路器，可阻止後續回合與成本擴大；若需嚴格硬預算，發送前必須估算完整請求輸入並預留 `max_tokens` 對應的輸出費用。
- **HTTP 連線池**：若尖峰 `12` req/s 下每筆工單都走 `5` 回合，穩態原始負載約 `60` calls/s；若平均停留時間約 `1.5` 秒，依 Little’s Law 推算平均在途（In-flight）連線數約 `90` 條。實務上應將 HTTP Client 連線池上限（如 Node.js `Agent` 的 `maxSockets` 或 Python `httpx.Limits` 的 `max_connections`）設為 `128` 作為壓測起點，並將分流比例、重試、每程序連線池與上游 RPM／TPM 一併納入驗證。此外，5 輪若各耗滿 `5,000 ms` 即達 `25 s`，因此整體 `wallClockTimeoutMs` 與端到端 p95 需分別驗證。
- **Redis 租戶範圍鎖與執行狀態鍵**：以 `orderops:run:{tenant_id}:{ticket_id}` 作為租戶隔離鍵，並將**可續租的短暫 lease**（含 owner token 與原子釋放，防止舊持有者誤刪新持有者的鎖；寫入端仍須驗證版本或 fencing token，才能防止過期 worker 覆寫外部狀態）與執行狀態分離，防止同一工單被重試佇列重複啟動兩個 `Agent Loop`。
- **PostgreSQL 執行軌跡表**：建立 `agent_runs`（主鍵 `run_id`，索引 `(tenant_id, ticket_id)`）與 `agent_turns`（複合主鍵 `(run_id, turn_index)`），記錄每輪的 `stop_reason`、`input_tokens`、`output_tokens`、`cost_usd` 與 `request_id`，供事後稽核與成本歸因（斷點續跑細節見第 6 章）。

### `OrderOps` 基準情境與無快取膨脹帳本

貫穿本書的主軸系統 `OrderOps` 是一個企業級訂單營運代理系統，承接以下基準負載：

- **日工單量**：`50,000` 筆／天（`1,500,000` 筆／月，以 30 天計）
- **尖峰流量**：`12` req/s（平均 `0.58` req/s，尖峰 `20×`；精確比值約 `20.7×`）
- **延遲 SLO**：分流 p95 ≤ `2.5` 秒；多步工具處置 p95 ≤ `18` 秒
- **基準回合與輸出**：每筆工單平均 `5` 回合，每回合新增輸入 `1,200` tokens，每回合**計費輸出** `350` tokens（含 thinking tokens）
- **模型計價基準**：Claude Sonnet 5.5 牌價為 `$2.00 / $10.00` USD / MTok（Input / Output）；Claude Haiku 5.5（≤100K）為 `$0.10 / $0.50` USD / MTok

由於 LLM 無狀態，每一輪都必須重送固定前綴（System Prompt `2,400` tokens + `18` 個工具 Schema `3,600` tokens，共 `6,000` tokens）與先前累積的對話歷史。以下為 `OrderOps` 單筆工單在**全用 Sonnet 5.5、無快取**下的簡化帳本算式（若首輪工單另占 `U` tokens 且每輪重送，5 回合累計輸入為 `42,000 + 5U` tokens）：

```text
假設：固定前綴（System Prompt 2,400 + 18 工具 Schema 3,600）= 6,000 tokens
      每回合新增輸入（tool_result + 上輪輸出）= 1,200 tokens
      每回合平均計費輸出 = 350 tokens，共 5 回合

Turn 1 Input:  6,000 tokens
Turn 2 Input:  6,000 + 1,200 =  7,200 tokens
Turn 3 Input:  7,200 + 1,200 =  8,400 tokens
Turn 4 Input:  8,400 + 1,200 =  9,600 tokens
Turn 5 Input:  9,600 + 1,200 = 10,800 tokens
--------------------------------------------------
5 回合累計輸入 = 6,000 + 7,200 + 8,400 + 9,600 + 10,800 = 42,000 tokens
5 回合累計輸出 = 350 × 5 = 1,750 tokens

單筆輸入成本 = (42,000 ÷ 1,000,000) × $2.00  = $0.0840
單筆輸出成本 = ( 1,750 ÷ 1,000,000) × $10.00 = $0.0175
--------------------------------------------------
未優化單筆成本 = $0.0840 + $0.0175 = $0.1015
每日成本（50,000 筆）  = $0.1015 × 50,000    = $5,075
每月成本（1,500,000 筆）= $0.1015 × 1,500,000 = $152,250
```

這筆 `$152,250`／月的帳單清楚說明了為什麼第 1 章就要把迴圈與預算護欄建好：第 8 章將示範如何透過模型分層與 Prompt Caching 把月成本壓到 `≤ $18,000`。

## 故障模式與防禦

未設防的 `Agent Loop` 上線後，最常見的四種故障模式、診斷線索與防禦機制如下（下列數值為初始政策門檻，上線後應依分母與最小樣本量校準）：

1. **無窮工具迴圈與參數振盪**（Infinite Tool Loop）
   - **現象**：模型反覆用相同參數呼叫同一個工具（例如查不到訂單卻一直重試 `get_order`），直到帳單暴增或撐爆上下文。
   - **診斷與告警**：結構化 log 記錄 `ticket_id`、`turn`、`tool_name` 與 `tool_input_hash`。當單日 `budget_exceeded` 終止比例超過 `1%` 或單筆 `turns >= 7` 連續出現時觸發告警。
   - **防禦**：在迴圈外層強制設定 `maxTurns = 8`、`maxTotalInputTokens = 50,000` 與 `maxCostUsd = 0.25`，任一條件觸發立即終止並回傳 `budget_exceeded`。進階防護可加上連續相同 `(tool_name, tool_input_hash)` 偵測，連續 2 次即強制中斷或注入提示。
2. **單輪與總體超時級聯**（Timeout Cascade）
   - **現象**：上游 API 回應緩慢或本地工具卡住，導致工單處理時間突破 `OrderOps` 多步處置 p95 ≤ `18` 秒的 SLO，進而拖垮工作佇列的 Worker 執行緒。
   - **診斷與告警**：log 記錄 `elapsed_ms`、`turn_latency_ms` 與 `tool_latency_ms`。當多步處置 p95 延遲連續 5 分鐘超過 `16,000 ms` 時觸發預警。
   - **防禦**：設定雙層 Timeout——總 wall-clock 上限 `18,000 ms`（對齊 SLO），單次 LLM 呼叫 `5,000 ms`（隨剩餘時間動態縮減：`Math.min(5000, 18000 - elapsedMs)`），並對每個外部工具呼叫加上獨立的 `AbortSignal` 超時。
3. **HTTP `429` / `529` 與 Streaming 半途斷線**
   - **現象**：尖峰 `12` req/s 時觸發 Rate Limit（HTTP `429`，回應標頭附帶 `retry-after`）或平台過載（如 HTTP `529 overloaded_error`，具體錯誤碼以官方 Errors 文件為準）；若啟用 Streaming，網路抖動可能導致 SSE 串流半途斷線，留下殘缺的工具參數 JSON。
   - **診斷與告警**：log 記錄 `http_status`、`request_id`（來自回應標頭 `request-id`）與 `retry_after_ms`。當 `429` 或 `529` 比例在 2 分鐘內超過 `2%` 時觸發告警。
   - **防禦**：SDK 內建指數退避與 Jitter 重試，但重試總時間仍受外層 `wallClockTimeoutMs` 約束；對 Streaming 斷線不應把殘缺 JSON 送進工具執行，而應捨棄該未完成 Turn 並視剩餘預算決定是否重試。
4. **`max_tokens` 截斷與寫入型工具冪等性碰撞**
   - **現象**：模型輸出過長觸發 `stop_reason == "max_tokens"`（若啟用 extended 或 adaptive thinking，`max_tokens` 須同時涵蓋思考與可見輸出，實際預設行為依模型版本與官方文件為準），導致結構化輸出或工具參數不完整；此外，若寫入型工具（如 `issue_refund`）沒有冪等鍵，模型在超時重試時可能重複退款。
   - **診斷與告警**：log 記錄 `stop_reason` 與 `idempotency_key`。任何 `stop_reason == "max_tokens"` 事件都應計入錯誤指標並抽樣檢查；若單日**異參數衝突**（同鍵不同內容，需與正常冪等重放分開計數）衝突率超過 `0.5%`，代表上層重試策略或狀態鎖失效。
   - **防禦**：將 `max_tokens` 設為明確上限（如 `1024`），在狀態機中把 `max_tokens` 視為異常分支直接終止，不當成正常結果回傳。所有寫入型工具的 `tenant_id`、金額（以最小貨幣單位驗證為有限正值）與租戶範圍冪等鍵（如 `refund:{tenant_id}:{ticket_id}:{order_id}`）**必須由後端從已驗證的工單上下文綁定與產生，絕不信任模型傳入的值**；資料庫對該鍵建立唯一約束並記錄請求指紋，針對「金流已接受但應用逾時」的案例保留待對帳狀態與查詢恢復流程。

## 動手做

完整可執行的 TypeScript 與 Python 程式碼位於：

- TypeScript：[index.ts](../examples/ts/ch01/index.ts)（共用型別與 Mock 位於 `examples/ts/shared/`）
- Python：[main.py](../examples/py/ch01/main.py)（共用型別與 Mock 位於 `examples/py/shared/`）

以下節錄 TypeScript 版本的狀態機核心迴圈與預算護欄（完整定義請見上述檔案）：

```ts
while (turns < budget.maxTurns) {
  const elapsedMs = Date.now() - startedAt;
  if (elapsedMs >= budget.wallClockTimeoutMs) {
    return { status: "timeout", stopReason: "wall_clock_timeout", /* ... */ };
  }

  turns += 1;
  const remainingMs = Math.min(budget.turnTimeoutMs, budget.wallClockTimeoutMs - elapsedMs);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), remainingMs);

  let response: Anthropic.Message;
  try {
    response = await client.messages.create(
      { model, max_tokens: 1024, system: SYSTEM_PROMPT, tools: TOOLS, messages },
      { signal: controller.signal },
    );
  } catch (err) {
    if (controller.signal.aborted || err instanceof Anthropic.APIConnectionTimeoutError) {
      const hitWallClock = Date.now() >= deadline;
      return {
        status: "timeout",
        stopReason: hitWallClock ? "wall_clock_timeout" : "llm_turn_timeout",
        /* ... */
      };
    }
    return { status: "error", stopReason: "api_error", /* ... */ };
  } finally {
    clearTimeout(timer);
  }

  totalInputTokens += response.usage.input_tokens;
  totalOutputTokens += response.usage.output_tokens;
  totalCostUsd += calculateCostUsd(model, response.usage);

  if (totalInputTokens > budget.maxTotalInputTokens || totalCostUsd > budget.maxCostUsd) {
    return { status: "budget_exceeded", stopReason: "budget_exceeded", /* ... */ };
  }

  messages.push({ role: "assistant", content: response.content });

  if (response.stop_reason === "end_turn") {
    return { status: "completed", stopReason: "end_turn", /* ... */ };
  }
  if (response.stop_reason === "tool_use") {
    if (turns >= budget.maxTurns) {
      return { status: "budget_exceeded", stopReason: "max_turns", /* ... */ };
    }
    if (Date.now() - startedAt >= budget.wallClockTimeoutMs) {
      return { status: "timeout", stopReason: "wall_clock_timeout", /* ... */ };
    }
    const toolResults = toolBlocks.map((b) => executeTool(backend, ticket, b));
    messages.push({ role: "user", content: toolResults });
    continue;
  }
  if (response.stop_reason === "refusal") {
    return { status: "refused", stopReason: "refusal", /* ... */ };
  }
  return { status: "error", stopReason: response.stop_reason ?? "unknown", /* ... */ };
}
```

設定 `ANTHROPIC_API_KEY` 後，可在範例目錄執行以下指令驗證單工單處理流程（持久化斷點續跑將於第 6 章實作）：

```bash
# TypeScript
cd books/enterprise-agents/examples/ts && npx tsx ch01/index.ts

# Python
cd books/enterprise-agents/examples/py && python3 ch01/main.py
```

正常執行結束後，終端機會輸出包含 `status: "completed"`、`turns`、`totalInputTokens`、`totalOutputTokens` 與 `totalCostUsd` 的 JSON 摘要（Python 版欄位為 `snake_case`）。預設 `sampleTicket` 會觸發查單與庫存檢查；`OrderOpsMockBackend` 亦預載了退款冪等表，可透過修改測試工單或以固定假回應驗證三個邊界情境：
1. 將 `maxTurns` 改為 `1`，確認迴圈在第一輪 `tool_use` 派發前即攔截並回傳 `budget_exceeded`（`stopReason: "max_turns"`），且不會在最後一輪執行寫入工具。
2. 傳入不存在的 `order_id`，觀察 `executeTool` 回傳 `is_error: true` 後，模型如何在下一輪向使用者回報查無此訂單，而不是讓程式拋出未捕捉例外崩潰。
3. 以受控的延遲或假回應搭配極短的 `wallClockTimeoutMs`（例如 `1` ms），驗證逾時分支能觸發 `AbortController`（Python 版為 `httpx.Timeout` / `timeout` 參數）並回傳 `status: "timeout"` 與 `stopReason: "wall_clock_timeout"`（實務上計時器排程與取消並非精確即時，且程式需區分單輪逾時與整體 wall-clock 逾時）。

## 自我檢核

1. **【入門｜10 分鐘】** 為什麼 `OrderOps` 的第 5 回合單次輸入是 `10,800` tokens，而不是 `1,200` tokens？若將一個 3 步驟的固定報表產出任務改寫成開放式 `Agent Loop`，會帶來什麼不必要的風險？
2. **【進階｜15 分鐘】** 在 `runOrderOpsAgent` 中，如果把 `wallClockTimeoutMs` 檢查放在 `while` 迴圈結尾而不是開頭，會發生什麼問題？若工具執行本身卡住超過 `18,000 ms`，目前的範例還缺哪一層防護？
3. **【挑戰｜20 分鐘】** 假設 `OrderOps` 有 `60%` 的簡單工單只需 `2` 回合即可完成，且改用 Claude Haiku 5.5（`$0.10 / $0.50` USD / MTok，前綴仍為 `6,000` tokens，每回合新增 `1,200` tokens、輸出 `350` tokens）。請計算這 `60%` 工單的單筆成本與每日總成本（每天 `50,000 × 60% = 30,000` 筆）。

### 參考解答

1. **解答**：因為 LLM API 無狀態，每一輪都必須重送完整前綴（`6,000` tokens）與先前所有回合的對話歷史，因此輸入隨回合線性膨脹：`6,000 → 7,200 → 8,400 → 9,600 → 10,800`。固定 3 步驟任務若改寫成 `Agent Loop`，會引入多餘的模型推理延遲、非確定性步驟順序、額外 token 費用與重複呼叫風險，應改用 Prompt Chaining 並在每步之間加上確定性格式閘門（見「Workflow 與 Agent 的決策光譜」）。
2. **解答**：結尾檢查雖可在正常走到該檢查點後攔截下一輪，但若迴圈中有 `continue`、例外分支或工具派發前未再次檢查，仍可能多發起無效呼叫，且無法即時中止已卡住的呼叫；因此首次呼叫前、迴圈開頭與每次派發工具前都應檢查剩餘 deadline，並為 API 與工具呼叫設置可執行的超時機制。此外，目前範例僅對 `client.messages.create` 套用 `AbortController`，若本地 `executeTool`（例如呼叫外部 HTTP 或 DB）卡住，仍可能突破 `18,000 ms` SLO；生產環境必須為每個工具呼叫也加上獨立的 `AbortSignal` 超時。同時要留意，`Promise.race` 僅讓等待方提早返回，並不會自動取消或回滾已經送出的外部寫入請求，因此寫入型工具（如 `issue_refund`）必須搭配冪等鍵與超時後對帳機制，才能避免「客戶端判定超時、但金流端實際已退款」的狀態分裂問題。
3. **解答**：
   - 2 回合累計輸入 = `6,000 + 7,200 = 13,200` tokens；累計輸出 = `350 × 2 = 700` tokens。
   - 單筆成本（Haiku 5.5）= `(13,200 ÷ 1,000,000) × $0.10 + (700 ÷ 1,000,000) × $0.50 = $0.00132 + $0.00035 = $0.00167`。
   - 每日總成本（`30,000` 筆）= `$0.00167 × 30,000 = $50.10`（`$1,503/月`，相較於未優化 Sonnet 5.5 單筆 `$0.1015`，該分群單筆降幅達 `98.35%`）。若剩餘 `40%` 複雜工單仍按 5 輪 Sonnet 基準，月總成本為 `$62,403`；要達成整體 `≤ $18,000/月`（平均 `$0.012/筆`，總降幅 `88.18%`），複雜工單平均成本須壓至 `≤ $0.027495/筆`（其對全部工單的加權成本貢獻須 `≤ $0.010998/總工單筆`），這部分待第 8 章透過 Prompt Caching 與 Batch API 實證驗證（Batch API 的處理時限依官方文件為準，且相依的 client-tool turns 須等前一輪結果）。

## 延伸閱讀

- Anthropic 官方工程指南：[Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)（Workflow vs Agent 決策光譜與六種基礎模式）。
- Claude Messages API 規格：[Handling Stop Reasons](https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons)（Tool Use 與 `stop_reason` 狀態機設計）。
- 本書後續章節：第 2 章（Tool Use 契約與 MCP）、第 6 章（持久化斷點續跑）、第 8 章（成本與延遲優化帳本）。
