# 第七章：評測驅動開發（EDD）：建立可量化的 Eval 與調校迴圈

## 從你已知的出發

寫傳統後端服務時，你靠 CI 回歸測試套件與契約斷言（Regression Suite）守住品質底線。每次改動程式碼，單元測試檢查函式回傳值，整合測試驗證 API 狀態碼與資料庫寫入結果；只要斷言全數通過，就能放心合併 PR。

這個機制對傳統後端成立的邊界在於「可控制的確定性」：在受控測試條件下，精確斷言能有效驗證指定行為，而系統穩定性仍須依測試覆蓋、重複執行與實際運行資料評估。把這套習慣搬到企業 Agent 上，確定性前提隨即失效——同一個工單輸入跑兩次，模型可能第一次先查訂單再查庫存，第二次先查庫存再查訂單，甚至在邊界語意下給出不同措辭的回覆。對於自由文字回覆與存在多條合法工具路徑的場景，單一預期字串的整體精確比對斷言（`assert response == expected`）通常不足以評估多種合法措辭或路徑（至於 Enum、固定 ID、正規化欄位與 API 契約仍應保留精確比對），要不是天天誤報紅燈，就是被迫把斷言放寬到形同虛設。

更棘手的是**複合誤差**。傳統 API 在受控條件下，單一端點通過測試只證明已測條件下的指定行為符合斷言，系統穩定性仍須綜合其他證據評估；而 `OrderOps` 這類多步 Agent 每次處理工單平均走 5 個回合，只要其中一步選錯工具或漏掉一個參數，整張工單就可能核發錯誤退款。因此，Agent 的回歸測試不能只看「最後一句話像不像對的」，必須同時檢查**執行軌跡**（Trajectory）與**多次重複執行的穩定度**（Pass^k）。

本章把你熟悉的 CI 契約斷言升級為「評測驅動開發（Eval-Driven Development, EDD）」：先建立 100 題黃金評測集，再用三層評測器與錯誤分類（Error Taxonomy）示範如何把 `OrderOps` 的通過率從 78% 系統化調校到 95%。

---

## 核心機制

### 三層評測器（Three-Tier Graders）

單靠一種評測方法無法兼顧速度、成本與語意準確度。企業級 Eval 套件通常由三層評測器組成，由快到慢、由廉價到高成本層層過濾：

1. **確定性 Code Grader（程式碼斷言層）**
   用純程式碼檢查所有可量化的硬性契約：JSON Schema 是否合法、是否帶入 `idempotencyKey`、最終回覆是否包含訂單編號；對於退款安全，必須以後端可信身分（Tenant 與授權）與交易狀態為準，驗證同一租戶、訂單、幣別、剩餘可退額及有效人工核准，並在寫入交易內重驗以防併發退款。評測應分別記錄工具嘗試、後端拒絕與實際落帳副作用。在 wire-level 上，Code Grader 還會驗證 Messages API 回應的 `stop_reason`：對自管 Client Tools，`tool_use` 屬於正常中間回應，應檢查下一則 user message 開頭包含該回合所有對應的 `tool_result` 並逐一比對 `tool_use_id` 與 `is_error` 錯誤處理；預期自然完成時才檢查 `end_turn`，並將 `max_tokens`、`refusal` 與 `pause_turn` 獨立分類。這一層執行時間在毫秒級、零 API 成本，應涵蓋 100% 的測試案例。
2. **校準後的 LLM-as-a-Judge（模型裁判層）**
   針對無法寫成正規表達式的語意品質（例如「拒絕超額退款時，語氣是否專業且清楚說明原因」），交由獨立且**無任何工具權限**的裁判模型（如 Claude Haiku 5.5 或 Sonnet 5.5）依明確的 1–5 分量表（Rubric）打分，且裁判不得覆寫 Code Grader 的硬性契約結果。部署前應依當時各模型（如 Haiku 5.5 與 Sonnet 5.5）及所選思考模式的官方參數文件確認 `temperature`、`top_p`、`top_k` 的可用設定；若保留 adaptive thinking 可用 `output_config.effort` 調節並量測 `max_tokens: 256` 是否足夠，或依文件支援設為停用思考。透過 `output_config.format` 指定 `type: "json_schema"`，要求輸出必填的 `score`（含分數範圍驗證）與 `reason`，並對 `refusal` 與 `max_tokens` 做獨立處理；同時把固定 Rubric 放在系統內容區塊末端並加上 `cache_control: { "type": "ephemeral" }`（注意固定前綴須達該裁判模型官方公布的最低可快取門檻，依模型與層級而異，部署前應查證並以實際 cache creation 與 read 用量驗證）。**關鍵在於校準**：起始設定可先在 30–50 筆人工標註的錨點資料上驗證，確保與人類專家一致率達 90% 以上（須定義採逐分一致或通過門檻一致；1–5 有序評分建議採加權 `κ ≥ 0.80`），才能放進自動化管線。
3. **人工抽檢（Human Audit）**
   起始設定為每週從線上流量（優先納入高風險案例）與 CI 邊界案例中抽樣 20–50 筆人工覆核，用來發現前兩層漏掉的新型態錯誤，並把這些案例回補進黃金評測集。

### Trajectory Eval 與 Eval 執行基線

在 `OrderOps` 場景中，就算兩次執行的最終回覆都是「已為您處理退款」，背後發生的事情可能完全不同：一次是先呼叫 `get_order` 確認狀態再呼叫 `issue_refund`；另一次則是沒查訂單就直接嘗試退款，撞到後端錯誤才補查。

**Trajectory Eval**（軌跡評測）直接檢查代理人的工具呼叫序列（`toolTrace`），核心指標包含：

- **必要工具覆蓋**：是否呼叫了所有必要工具（例如退款前必查 `get_order`）。
- **禁止工具攔截**：面對誘騙輸入時，是否誤觸高風險寫入工具。
- **呼叫順序約束**：對每次退款操作，核對同訂單、同租戶的成功 `get_order` 前置結果出現在該次 `issue_refund` 之前。
- **步數上限（`maxSteps`）**：是否在合理回合數內收斂，避免無意義的空轉消耗 Token（模型回合數與工具呼叫數應分開計數）。

在生產級 CI 管線中，Eval Runner 本身需要明確的配置基線與持久化結構，才能支撐追蹤與回歸比對：

- **逾時與併發基線**：單回合 LLM 呼叫 timeout 設為 `15,000 ms`，單次工具執行 timeout 設為 `5,000 ms`，單筆試驗（Trial）涵蓋模型、工具、退避與裁判的端到端 wall-clock deadline 上限 `45,000 ms`；`maxSteps` 設為 `6`（對應 `OrderOps` 平均 5 回合加上 1 回合緩衝）。CI 執行器併發度上限設為 `concurrency = 10`（僅限制在途量，仍須按 RPM、輸入／輸出 TPM 與共用配額節流）。
- **SQL 持久化結構**：每次 CI Eval 寫入 `eval_runs`（`run_id`, `git_sha`, `suite_version`, `pass_hat_k`, `total_cost_usd`, `created_at`）與 `eval_trial_results`（`run_id`, `case_id`, `trial_idx`, `passed`, `error_category`, `tool_trace_json`, `input_tokens`, `output_tokens`, `latency_ms`, `created_at`），對 `eval_trial_results` 建立 `UNIQUE (run_id, case_id, trial_idx)` 防止重跑重複入帳，並建立複合索引 `(run_id, case_id)` 與 `(error_category, created_at)` 以加速錯誤趨勢查詢（持久化 Trace 前應先遮罩憑證、個資與金流資料）。
- **Redis 快取鍵與環境隔離**：對不可變的測試夾具（Fixture）或只讀模擬回應，按 suite 與 fixture 版本以 `eval:fixture:{suite_version}:{case_id}:v1` 儲存（`TTL = 86,400s` 僅控制 Redis 保存期限），並在每個 Trial 之間重置或隔離可變狀態以確保可重現。

### Pass@k 與 Pass^k 的數學意義

評估非確定性系統時，單次試驗雖具觀測價值，但無法估計同題重跑的穩定度。業界常用兩個指標區分「能力上限」與「生產穩定度」：

- **Pass@k**：重複執行 `k` 次，**至少有 1 次**通過的比例。適合衡量「模型有沒有能力解出這題」（例如程式碼生成輔助）。
- **Pass^k**（Pass-hat-k）：重複執行 `k` 次，**全部 `k` 次都通過**的比例。這是衡量指定重複條件下系統穩定度的指標；在生產環境單次執行時，仍應獨立追蹤單次成功率與嚴重錯誤率。

更現實的問題是多步任務的機率乘法效應。若各步在前序成功下的條件成功率都為 `p`（或各步彼此獨立），一個 5 步任務的單次執行成功率為 `p^5`；在各次試驗獨立的假設下（實務上共用 Fixture、模型版本或上游故障可能造成相關性，觀測時仍可直接按案例計算 `any`／`all`），連續 `k` 次執行都成功的機率會進一步衰減為 `(p^5)^k`。這也是為什麼單步 90% 準確率在企業多步 Agent 中遠遠不夠。

### Worked Example：Pass^k 衰減與 100 題黃金集 CI 成本核算

以下以 `OrderOps` 基準（Sonnet 5.5 牌價 `$2.00 / $10.00` per MTok，第 1 回合 6,000 input tokens、第 2–5 回合各新增 1,200 歷史 input tokens，未優化基準單筆 5 回合累計 `42,000` input tokens / `1,750` output tokens，單筆成本 `$0.1015`）實算 Pass^k 衰減與每次 CI 跑 100 題黃金集的 API 成本：

```text
1. 多步任務與 Pass^k 數學實算
------------------------------------------------------------
情境 A：單步準確率 p = 0.90
  - 5 步任務單次成功率  = 0.90^5  = 0.5905 (59.05%)
  - 10 步任務單次成功率 = 0.90^10 = 0.3487 (34.87%)
  - 5 步任務 k=5 全對率 Pass^5 = 0.90^25 = 0.0718 (7.18%)

情境 B：單步準確率調校至 p = 0.98
  - 5 步任務單次成功率  = 0.98^5  = 0.9039 (90.39%)
  - 10 步任務單次成功率 = 0.98^10 = 0.8171 (81.71%)
  - 5 步任務 k=5 全對率 Pass^5 = 0.98^25 = 0.6035 (60.35%)

結論：單步準確率從 90% 提升到 98%，5 步任務的 Pass^5 穩定度
      從 7.18% 提升至 60.35%（約 8.41 倍）。

2. 100 題黃金集 CI 回歸測試成本核算（Sonnet 5.5 執行 + Haiku 5.5 裁判）
------------------------------------------------------------
假設黃金集共 100 題（60 正常 / 25 邊界 / 15 誘騙），每次 CI 跑 k = 3 次：
總執行次數 = 100 * 3 = 300 次 Agent Trial（約 1,500 次模型請求，外加最多 300 次裁判請求；重試另計）

(a) 被測 Agent 成本（Sonnet 5.5，$2.00 / MTok input，$10.00 / MTok output）：
    單次基準消耗 = 42,000 input + 1,750 output = $0.1015
    300 次總成本 = 300 * $0.1015 = $30.45

(b) LLM-as-a-Judge 裁判成本（Haiku 5.5，$0.10 / MTok input，$0.50 / MTok output；全送估算）：
    每次裁判輸入 1,500 tokens、輸出 150 tokens
    單次裁判成本 = (1,500 * 0.10 + 150 * 0.50) / 1,000,000 = $0.000225
    300 次裁判總成本 = 300 * $0.000225 = $0.0675

每次完整 CI 執行總成本 = $30.45 + $0.0675 = $30.52 USD（精確值 $30.5175）
（若搭配 ch08 的 Prompt Caching 與模型分層，在維持品質等價與對應快取命中率下，可評估進一步降本，實際降幅待量測）
```

### Error Taxonomy 驅動的調校工作流（78% → 95% 示意）

拿到失敗報表後，最忌諱「憑感覺改 Prompt」。系統化調校必須先將失敗案例歸類為明確的 **Error Taxonomy**，再對症下藥（下表以 100 題黃金集、調校前 22 題失敗為示意）：

| 錯誤類別（Error Taxonomy） | 佔全體比例（失敗 22 題） | 根因診斷 | 對應修復手段 |
|---|---|---|---|
| `tool_order_violation` | 8 題（8%） | 模型偶爾跳過 `get_order` 直接退款 | 在 System Prompt 強制前置步驟，並在 `issue_refund` 描述註明「須先取得訂單狀態」 |
| `policy_violation` | 7 題（7%） | 面對誘騙輸入時，誤信使用者宣稱的「主管已核准」 | 強化政策邊界範例（Few-shot），並由後端交易前置條件擋下未授權或超額請求 |
| `schema_error` | 4 題（4%） | 金額或 `tenantId` 格式偶發錯誤 | 啟用工具定義層級 `strict: true`（部署前應查核當時官方文件對 strict 工具數量與 schema 複雜度的限制）與枚舉約束（見 ch02） |
| `excessive_steps` | 3 題（3%） | 查無庫存時反覆重試同一工具 | 設定工具錯誤訊息引導終止，並限制最大步數 |

依序修復上述四類主要問題後，`OrderOps` 在 100 題黃金集上的 `Pass^3` 通過率示意從 **78%** 提升至 **95%**（餘下 5 題為長尾邊界與新回歸案例，須納入下一輪 Dev／Holdout 追蹤）。

實務上選擇修復手段遵循「確定性優先」原則：凡是格式與型別問題，一律下沉到 Tool Schema 的 `strict: true` 與枚舉約束；凡是順序、步驟上限與退款安全前置條件，交由執行迴圈與後端交易驗證把關；只有語意判斷與邊界拒答策略才透過 System Prompt 與 Few-shot 範例調校；若同一類別在調校兩輪後仍無法收斂，才考慮升級推理模型。

> [!NOTE]
> 線上流量的影子部署（Shadow Mode）與模型長期漂移監控屬於生產維運範疇，將於第 10 章（見 ch10）詳細說明；本章聚焦於上線前與 CI 階段的離線 Eval 與調校迴圈。

---

## 故障模式與防禦

1. **過度擬合黃金集（Eval Overfitting）**
   - **現象**：為了衝高 100 題黃金集的通過率，在 System Prompt 塞入針對特定測資的硬編碼規則，導致上線後面對沒見過的客訴句型表現崩盤。
   - **防禦**：把黃金集拆分為「開發調校集（Dev Set, 70 題）」與「保留驗證集（Holdout Set, 30 題，每錯一題即變動 3.33 個百分點）」，調校期間只看 Dev Set，合併前才跑一次 Holdout Set 驗證泛化能力；在監控指標設定告警閾值，當 `dev_pass_hat_3 - holdout_pass_hat_3 > 5 個百分點`、Holdout 低於絕對門檻，或關鍵安全案例未通過時自動阻斷合併（避免兩組同時退化仍通過）。
2. **Eval 併發觸發 API 限流（`429` / `529`）與殘缺串流**
   - **現象**：CI 同時對 100 題 × `k=3` 發起 300 次 Trial，未受控的併發會觸發 HTTP `429`（Rate Limit，附帶 `retry-after` Header）或 `529 overloaded_error`（服務過載）；若使用 Streaming 模式，須收到完整終止事件後才可評分或執行工具，半途斷線會留下殘缺 JSON 導致誤判。此外，TS 與 Python SDK 預設各重試 2 次，若外層再重試 3 次，每個邏輯請求最多可能送出 12 次。
   - **防禦**：將 Eval Runner 併發度鎖在 `concurrency ≤ 10` 並搭配 RPM／TPM 節流，由單一層控制重試（指數退避加隨機 Jitter，起始 `1,000 ms`、上限 `32,000 ms`、最多重試 3 次，遵守 `Retry-After` 與剩餘 deadline），並在結構化 log 記錄 `http_status`、`retry_after_ms`、`request_id` 與 `case_id`。起始設定告警：當單次執行 `eval_api_429_rate > 2%` 時發出警告，將基礎設施失敗、無效試驗與模型失敗徹底隔離。
3. **LLM-as-a-Judge 立場偏誤、提示注入與靜默快取失效（Silent Cache Miss）**
   - **現象**：工單文字、工具回傳與待評答案都可能帶有注入內容，裁判模型也傾向給「字數較長、語氣看似禮貌」的回覆高分；此外，若裁判 Prompt 把動態案例放在固定 Rubric 前面，或固定前綴未達該模型最低可快取門檻，會導致 `usage.cache_read_input_tokens = 0`（同時可能沒有 `cache_creation_input_tokens`），造成延遲與費用雙重膨脹。
   - **防禦**：永遠讓 **Code Grader 先行**，凡是事實性與契約性欄位（金額、狀態、ID）一律由程式碼斷言把關，LLM Judge 不具工具權限且只負責評分「語氣與解釋清晰度」等純語意維度。同時將固定 Rubric 置於系統內容區塊末端（確保達該模型官方最低門檻以上），定義 `judge_cache_hit_ratio`（例如合格請求命中比例）並以 `< 0.85` 作為起始告警門檻（須分開冷啟動樣本）。
4. **CI 成本失控或執行過慢**
   - **現象**：每次 PR 小改動都跑全套 100 題 × `k=3` 次（若 10 個 worker 各耗盡 45 秒上限需 22.5 分鐘，每日夜間跑 30 次約 `$915.53／月`，高頻 PR 全跑則月燒數千美元）。
   - **防禦**：將 Eval 分級為 **PR Smoke Gate**（20 題核心案例 × `k=1`，10 worker × 45 秒理論上限 90 秒，目標 2 分鐘內完成）與 **Nightly Full Regression**（100 題完整集 × `k=3`，每日夜間執行），並設定單次 CI 預算硬上限 `$35.00 USD`（較基準 `$30.5175` 預留 `$4.4825` 緩衝，派工前須原子預留在途請求與重試成本）與 `ci_eval_cost_usd` 告警。

---

## 動手做

本節示範如何為 `OrderOps` 建立具備「軌跡檢查 + 程式碼契約 + 裁判評分（範例內建字數 Stub）」的自動化評測器，並計算 `Pass@3` 與 `Pass^3`。完整可執行程式碼位於 `examples/ts/ch07/index.ts` 與 `examples/py/ch07/main.py`。

### 核心程式碼片段：軌跡評測與 Pass^k 計算

以下 TypeScript 節錄片段展示 `computePassKMetrics` 如何計算 `Pass@k` 與 `Pass^k`，以及 `gradeTrajectory` 如何檢查步數上限與簡化的工具呼叫順序（以 `indexOf` 示範單次順序比對；完整版另含 `requiredTools`、`forbiddenTools` 檢查，實務上應逐筆檢查每次 `issue_refund`，確認其前有同租戶、同訂單且成功完成的 `get_order`）：

```typescript
export function computePassKMetrics(trialResults: boolean[]): {
  passAtK: number;
  passHatK: number;
  k: number;
} {
  const k = trialResults.length;
  if (k === 0) return { passAtK: 0, passHatK: 0, k: 0 };
  const passAtK = trialResults.some(Boolean) ? 1 : 0;
  const passHatK = trialResults.every(Boolean) ? 1 : 0;
  return { passAtK, passHatK, k };
}

export function gradeTrajectory(
  evalCase: EvalCase,
  trace: ToolCallTrace[],
): { ok: boolean; errorCategory: ErrorCategory; reason: string } {
  if (trace.length > evalCase.maxSteps) {
    return { ok: false, errorCategory: "excessive_steps", reason: `Steps ${trace.length} > ${evalCase.maxSteps}` };
  }
  const calledNames = trace.map((t) => t.name);
  const getOrderIdx = calledNames.indexOf("get_order");
  const refundIdx = calledNames.indexOf("issue_refund");
  if (refundIdx !== -1 && (getOrderIdx === -1 || getOrderIdx > refundIdx)) {
    return { ok: false, errorCategory: "tool_order_violation", reason: "issue_refund called before get_order" };
  }
  return { ok: true, errorCategory: "none", reason: "Trajectory valid" };
}
```

### 執行完整範例與邊界驗證

你可以直接執行 TypeScript 或 Python 版本（內建模擬執行器，無需 API Key 即可跑通）：

```bash
# TypeScript 版本
cd examples/ts && npx tsx ch07/index.ts

# Python 版本
python3 examples/py/ch07/main.py
```

若完整執行該評測器，預期輸出範例會顯示每個測試案例的 `Pass@3`、`Pass^3`、最後一個失敗分類，以及依實際用量計算的總評測成本（當 `EVAL-003` 三次試驗為兩次通過、一次失敗時，`Pass@3` 為 `1`、`Pass^3` 為 `0`；實際總成本與非零 exit code 須執行完整範例確認）：

```text
[EVAL-001] category=normal Pass@3=1 Pass^3=1 lastFailureCategory=none
[EVAL-002] category=edge Pass@3=1 Pass^3=1 lastFailureCategory=none
[EVAL-003] category=adversarial Pass@3=1 Pass^3=0 lastFailureCategory=policy_violation
CI Regression Summary: 2/3 passed Pass^3 | Total Eval Cost: $0.2097
```

觀察 `EVAL-003` 的輸出即可驗證 `Pass@k` 與 `Pass^k` 的關鍵差異：該誘騙案例在 3 次試驗中有 2 次成功擋下、第 3 次未實際呼叫退款工具卻在回覆中誤報已核准（`1/3` 失敗），因此 `Pass@3=1`（看似有能力做對），但 `Pass^3=0`（無法保證每次做對），CI 閘門據此回傳非零 exit code 阻斷合併。

---

## 自我檢核

1. **入門（10 分鐘）**：為什麼傳統 CI 單元測試的精確字串比對斷言不適用於 Agent 的自由文字回覆與多路徑工具呼叫？在三層評測器中，哪些檢查應該交給 Code Grader，哪些才交給 LLM-as-a-Judge？
2. **進階（15 分鐘）**：若一個 6 步任務的單步準確率為 `0.95`（假設各步條件獨立），請問單次執行成功率與 `k=3` 次重複執行的 `Pass^3` 各是多少？為什麼企業生產環境應該看 `Pass^k` 而非 `Pass@k`？
3. **挑戰（20 分鐘）**：請在 `examples/ts/ch07/index.ts` 或 `examples/py/ch07/main.py` 中新增一個 `EVAL-004` 案例，模擬 Agent 在查無庫存時連續重試 5 次導致觸發 `excessive_steps` 錯誤，並觀察 Error Taxonomy 分類聚合報表輸出與 CI 成本變化。

### 參考解答

1. **入門**：因為 LLM 具有非確定性，同一問題多次執行的措辭與合法工具順序可能不同，精確字串比對會造成大量誤報。所有可量化、事實性的契約（JSON Schema、`stop_reason`、`tool_use_id` 配對、退款上限、訂單 ID、`idempotencyKey`、工具呼叫順序）都應交給零成本且毫秒級的 Code Grader；只有無法用規則表達的語意品質（語氣專業度、解釋清晰度）才交給校準後且無工具權限的 LLM-as-a-Judge。
2. **進階**：單次執行成功率為 `0.95^6 ≈ 0.7351`（73.51%）；`k=3` 的 `Pass^3` 為 `0.95^18 ≈ 0.3972`（39.72%）。生產環境單次執行應直接追蹤單次成功率與嚴重錯誤率；`Pass^k` 則作為重複條件下系統穩定度與一致性的輔助指標，而非用 `Pass@k` 掩蓋不穩定。
3. **挑戰**：在 `goldenSuite` 新增 `maxSteps: 4` 的案例，並在模擬執行器的 `trace` 推入 5 筆 `check_inventory` 呼叫，`gradeTrajectory` 即會回傳 `errorCategory: "excessive_steps"` 並計入分類聚合統計；同時固定試驗數下總執行次數會從 9 次增至 12 次。若新增三次試驗的平均成本與原九次完全相同，估計總評測成本會從 `$0.2097` 增至 `$0.2796`（增加 33⅓%）；但因 `EVAL-004` 含五次 `check_inventory` 呼叫並超過步數上限，實際值取決於模擬器對該案例的 token 計數與計費方式，須按實際用量重算。工程上這提醒我們：必須為工具設定明確的終止錯誤訊息與 `maxSteps` 上限，避免無效重試同時拖垮通過率與 Token 預算。

---

## 延伸閱讀

- [Anthropic Engineering: Demystifying Evals for AI Agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — 深入探討能力評測與回歸評測的差異、Pass@k 與 Pass^k 的實務取捨。
- [Anthropic Docs: Evaluate Prompts and Models](https://docs.anthropic.com/en/docs/test-and-evaluate/develop-tests) — 官方關於建立黃金測試集與校準 LLM-as-a-Judge 的最佳實踐。
