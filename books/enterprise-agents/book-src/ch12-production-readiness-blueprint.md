# 第 12 章：從原型到上線：架構決策清單、組織落地與演進路線

## 從你已知的出發

前十一章已經把企業級 Agent 的所有核心零件逐一拆解完畢：從 `Agent Loop` 狀態機（ch01）、Tool Use 契約與 `MCP`（ch02）、Context Engineering 與 Prompt Caching（ch03）、持久化狀態與 Agentic RAG（ch04）、多 Agent 協作（ch05）、可靠性工程與 `HITL`（ch06）、Eval 評測與 `Pass^k`（ch07）、單位經濟學與延遲 SLO（ch08）、安全護欄與權限治理（ch09）、可觀測性與 OpenTelemetry 追蹤（ch10），到批次處理與演進調校（ch11）。

然而，把原型推上線時，團隊卡住的往往不是單一模組寫不出來，而是三個系統級決策沒有落地：第一，該用裸 Claude API 自建狀態機、採用 Claude Agent SDK，還是引入第三方編排框架？第二，上線前如何用客觀的 Production Readiness Review（PRR）門檻驗收，而不是憑感覺放行？第三，如何設計從人工輔助到有界自動化的流量切換路線，讓技術團隊與業務主管都能在可量化的風險內推進？

本章以本書建立的原生 Agent 工程詞彙，為 `OrderOps` 完成上線前的最後一哩路：架構選型矩陣、企業級 PRR 檢查表、90 天漸進式自主權演進與估算淨效益計算，以及五種常見的上線失敗模式復盤。

## 核心機制

### Buy vs Build 決策矩陣：抽象洩漏與除錯成本

在 `OrderOps` 這類企業級系統中，技術棧選型的核心矛盾在於「開發速度」與「故障時的控制權」之間的取捨。當 `Agent Loop` 在生產環境發生 `429` 限流、`529 overloaded_error`、Streaming 斷線或 `cache_read_input_tokens` 歸零時，工程師必須能直接取得實際送出的請求、`messages` 陣列、逐回合 `usage`、重試次數、`stop_reason` 與 `tool_result` 配對，並能接管取消與審批流程，否則故障定位與恢復時間將大幅拉長。

| 評估維度 | 裸 Claude API + 自建狀態機 | Claude Agent SDK | 第三方編排框架 |
|---|---|---|---|
| **控制粒度** | 完整掌控 `messages`、`cache_control` 斷點、`thinking` block 與重試退避 | 封裝標準 `Agent Loop` 與 Tool 迴圈，保留核心鉤子（Hooks）與權限回呼 | 常隱藏 Prompt 組裝、上下文壓縮與內部重試邏輯 |
| **抽象洩漏風險** | 最低；所有 HTTP Header 與 Token 用量直接暴露 | 低；與 Claude 原生能力（如 Prompt Caching、Extended Thinking）同步 | 高；框架自帶的記憶體管理或摘要策略常破壞快取前綴 |
| **除錯與觀測成本** | 需自建 OpenTelemetry Span，但根因定位最直接 | 內建標準事件流，易於串接既有追蹤系統 | 故障時需先剝除框架外殼才能還原真實 API Payload |
| **適用場景** | 高併發、嚴格成本／延遲 SLO（如 `OrderOps`）、需客製化 `HITL` 狀態機 | 中等複雜度、標準工具呼叫與檔案／程式操作任務 | 快速 POC 驗證、跨多模型供應商的實驗性專案 |

對 `OrderOps` 而言，日工單量達 50,000 筆／天（1,500,000 筆／月，尖峰 12 req/s 若每單 5 次模型呼叫，持續穩態下平均約 60 次模型請求／秒；瞬間尖峰仍須依各回合時間分布與併發情況估算），且必須將月成本從未優化基準的 $152,250 壓低至 ≤ $18,000（降幅 ≥ 88%，單筆 ≤ $0.012），同時滿足分流 p95 ≤ 2.5 秒、多步工具處置 p95 ≤ 18 秒的延遲 SLO。這類系統一旦被第三方框架的隱藏回合或動態 System Prompt 破壞 Prompt Caching 命中率，成本會立刻失控。因此，生產環境建議採用「裸 Claude API + 自建狀態機」，或僅在非核心子流程使用「Claude Agent SDK」（註：Messages API 需由應用程式自行執行回合上限，而 `max_turns`／`maxTurns` 為 Agent SDK 選項；線上應依模型採 adaptive thinking 與 `output_config.effort`，並以 `strict: true` 與 `output_config.format` 約束結構）。

### 企業級 Production Readiness Review（PRR）檢查表

上線前的 PRR 不是人工勾選的書面表單，而是一套必須與 CI/CD 及啟動腳本綁定的硬性門檻（以下數值如 `$50`、14 天、90 天、180 天、70% 與 5%／3 分鐘皆為本案例的政策設定，實際導入應對應壓測與 Eval 驗收證據）。以下六個維度缺一不可：

1. **可靠性與超時階層（參見 ch06）**：必須嚴格遵守 `0 < toolTimeoutMs < llmTimeoutMs < wallClockTimeoutMs`。例如 `OrderOps` 設定單次工具超時 5,000 ms、單次 LLM 呼叫超時 12,000 ms、`max_turns` 上限 8 回合（政策上限 12）、總 Wall-Clock 上限 60,000 ms，並將剩餘 deadline 向下傳遞以限制每次呼叫與 SDK／應用層重試總次數；所有寫入／金流工具強制要求 `Idempotency Key`，付款端逾時後須先查核原操作結果再決定重試或轉人工。
2. **Eval 基準線（參見 ch07）**：離線回歸測試集必須達到 `Pass@1` ≥ 0.92 且 `Pass^3` ≥ 0.85（若進入 L3 全自動退款，則要求離線 `Pass^3` ≥ 0.95，並明訂線上重跑同一案例三次的抽樣與嚴重度標註方式）。任何 Prompt 或工具 Schema 變更未通過門檻一律阻斷部署。
3. **安全護欄與權限治理（參見 ch09）**：18 個工具必須明確切分為 12 個唯讀與 6 個寫入／金流工具；工單內容、模型輸出與 MCP 回傳皆視為不可信資料，每次寫入須在工具服務端依租戶、操作者、訂單、幣別與剩餘可退額重新授權（L1 不授予寫入憑證、L2 核准綁定特定請求內容與版本、L3 執行單筆及累計上限）。若受法遵規範限制資料落地美國，須在設定中鎖定 `inference_geo: "us"`（1.1× 費率倍率適用於 input、output、cache write 與 cache read，儲存與日誌落地須另行驗證）並納入預算模型。
4. **成本上限與熔斷（參見 ch08）**：設定每日（`$18,000 ÷ 30 = $600`）與每月（`≤ $18,000`）硬性預算上限，並在請求前預留預算、預測消耗將觸及 `$600` 前阻擋新增支出，同時定期對帳；另設單日消耗達 150%（`$900`）的後備告警與自動降級（純人工或 L1 模式），僅用於處理計量延遲或極端超額情境，不能作為維持 `$600` 硬上限的主要防線。
5. **可觀測性與告警（參見 ch10）**：OpenTelemetry 追蹤必須覆蓋每個 `Turn`、工具耗時、request ID、`stop_reason` 與 `usage` 欄位（含 `cache_read_input_tokens`），預設不留存敏感原文或明訂遮罩與存取政策，且稽核日誌保留天數 ≥ 90 天（本案例設為 180 天）。
6. **合規與回滾預案**：必須具備一鍵切換至純規則引擎或人工佇列的 Feature Flag，確保 30 秒內停止新寫入並完成流量退場，同時對在途或結果未知的退款執行對帳。

### 漸進式自主權路線：L1 → L2 → L3

企業級 Agent 不應在上線第一天就取得寫入資料庫或執行退款的完全自主權。正確的演進路線分為三個階段（L1 驗收於上線前 Shadow 期間同步完成）：

```text
L1 (Copilot 輔助)
  └─ Agent 只讀不寫，產出草稿與建議，100% 由人工點擊執行
       │  (驗證準確率與延遲 SLO 達標後推進)
       ▼
L2 (HITL 人工核准)
  └─ Agent 執行唯讀查詢並組裝寫入請求，關鍵金流/異動由人工一鍵核准
       │  (連續 14 天 Pass^3 >= 0.95 且零嚴重誤判後推進)
       ▼
L3 (有界全自動)
  └─ 低風險、小額（如 <= $50）工單全自動結案；高風險與超額工單仍退回 L2
```

### Worked Example：`OrderOps` 90 天分階段流量切換與估算淨效益

假設 `OrderOps` 日工單量為 50,000 筆／天（1,500,000 筆／月），人工處理每筆工單平均耗時 4 分鐘（`4/60` 小時），客服人力時薪成本為 $24／小時，則純人工處理單筆成本為 `$1.60`（月成本 `$2,400,000`）。本案例採 rollout 假設單筆基礎 API 成本為 `$0.011`（全球推論月滿載 API 成本為 `$16,500`，啟用 `inference_geo: "us"` 的 1.1× 倍率後為 `$18,150`，即 `$605/天`）。若 `$18,000` 為含 US 加價的硬上限，則階段四須將基礎單價壓低至 `≤ $0.010909/筆`（例如 `$0.0108/筆` 對應 `$17,820/月`），否則 `validateProductionConfig` 會因 `estMonthlyUsd = 18,150 > 18,000` 阻斷部署（若要通過成本檢查，須調高月預算上限，或維持 `$18,000` 硬上限並將基礎單價降至 `≤ $0.010909／筆`或減少計費量）。以下帳本沿用 `$0.011/筆` 計算估算淨效益（註：真確 ROI 仍須定義分母並計入人工覆核、營運與退款損失等成本）：

```text
[階段一：Day 1–14 Shadow 模式（0% 實際寫入，工具層禁止外部寫入與通知）]
- 流量比例：100% 旁路鏡像（50,000 筆/天），僅記錄決策不對外回覆
- 人工覆核節省：0 小時（純測試期）
- 月化 API 成本：$16,500（14 天實際 $7,700）
- 淨效益：負值（純投資期，用於驗證延遲 p95 <= 2.5s / 18s 與 Pass^3 >= 0.85）

[階段二：Day 15–35 Canary L2（5% 流量進入 HITL）]
- 每日進入 L2 工單：50,000 × 5% = 2,500 筆/天（75,000 筆/月）
- L2 人工核准耗時：從 4 分鐘降至 1 分鐘（每筆節省 3 分鐘 = 0.05 小時 = $1.20）
- 每月節省人工成本：75,000 × 0.05 小時 × $24/小時 = $90,000/月
- 僅呼叫 5% 流量 API 成本：$825/月（若維持全量影子呼叫則為 $16,500/月）
- 估算淨效益（以 5% 實際呼叫計）：$90,000 - $825 = +$89,175/月

[階段三：Day 36–60 擴大 L2（30% 流量）]
- 每日 L2 工單：50,000 × 30% = 15,000 筆/天（450,000 筆/月）
- 每月節省人工成本：450,000 × 0.05 小時 × $24/小時 = $540,000/月
- 對應 API 成本（30% 流量）：450,000 × $0.011 = $4,950/月
- 估算淨效益：$540,000 - $4,950 = +$535,050/月

[階段四：Day 61–90 100% L2/L3 混合（70% L2 + 30% L3 有界全自動，啟用 us 1.1x）]
- L2 工單（70%）：1,050,000 筆/月 × 0.05 小時 × $24 = $1,260,000/月節省
- L3 工單（30%）：450,000 筆/月 × (4/60) 小時 × $24 = $720,000/月節省
- 總節省人工成本：$1,980,000/月
- 滿載 API 成本（含 us 1.1x 資料駐留）：$16,500 × 1.1 = $18,150/月（$605/天；此情境須先調高 $18,000 預算上限或將基礎單價降至 ≤ $0.010909 方能通過部署檢查）
- 估算淨效益：$1,980,000 - $18,150 = +$1,961,850/月
- 損益平衡點：70/30 組合加權節省為 0.7×$1.20 + 0.3×$1.60 = $1.32/筆；
  若將滿載 $605/天視為固定支出，至少需處理 ≥ 459 筆/天（605 ÷ 1.32 = 458.33，約佔總量 0.92%）方能打平；若依變動成本計算（每筆含 1.1× 約 $0.0121），單筆淨節省為 $1.32 − $0.0121 = $1.3079，每處理一筆即為正效益。
```

## 故障模式與防禦

企業 Agent 專案從 POC 走到上線，最常見的五種失敗模式如下：

1. **無界迴圈與超時雪崩**：未設定 `max_turns` 或 `wallClockTimeoutMs`，導致模型在工具回傳 `is_error: true` 時無限重試，耗盡連線池並觸發 `429` 限流。**防禦**：在 PRR 啟動檢查中強制驗證 `0 < toolTimeoutMs < llmTimeoutMs < wallClockTimeoutMs` 與 `max_turns <= 12`，將剩餘 deadline 傳遞給每次呼叫，超時立即取消未完成工作並降級。
2. **快取靜默失效（Cache Silent Miss）**：上線後因動態插入時間戳或隨機請求 ID 至 System Prompt 前段，導致 `cache_read_input_tokens` 歸零，成本將大幅攀升（若其餘模型與 token 假設亦接近未優化條件，甚至可能趨近 `$152,250` 基準）。**防禦**：在可觀測性儀表板設定 `cache_hit_ratio < 0.70`（定義為統計視窗內快取讀取佔已記錄快取讀寫 token 的比例：`cache_read_input_tokens ÷ (cache_read_input_tokens + cache_creation_input_tokens)`）的 P1 告警，並針對分母為 0 或預期可快取請求卻無快取讀寫的情形另設異常檢查（若要衡量全部合格前綴的實際命中率，仍須另行估算或記錄未進入快取讀寫的合格前綴 token），同時在 CI 中鎖定前綴結構。
3. **權限膨脹與無保護寫入**：為了追求自動化率，未經 `Pass^3` 驗收便直接開放寫入／金流工具，導致異常輸入觸發錯誤退款。**防禦**：嚴格執行 L1 → L2 → L3 門檻，所有寫入授權皆在工具服務端重驗，L2 強制 `hitlRequiredForMutating = true`，L3 強制設定單筆與累計金額上限，並僅在收到完整且驗證通過的 `tool_use` 區塊後執行。
4. **架構抽象洩漏**：過度依賴第三方編排框架的預設記憶體與重試機制，當線上出現 `529 overloaded_error`、`pause_turn`、`max_tokens`、`refusal` 或 Streaming 半途斷線時，無法定位是框架重試還是模型輸出異常。**防禦**：核心業務路徑採用裸 SDK 與自建狀態機，保留完整原始 `usage` 與 `stop_reason` 日誌，遇 `429` 遵守 `Retry-After` 與剩餘 deadline。
5. **缺乏退場機制**：上線後遇到上游 API 長時間異常或模型品質退化，系統沒有快速切回人工或規則引擎的開關，只能硬扛故障。**防禦**：在入口閘道器實作 Feature Flag 與錯誤率熔斷器，錯誤率（失敗請求 ÷ 總請求）連續 3 分鐘超過 5% 即於 30 秒內停止新寫入並切換至純人工佇列（人工佇列亦須設承載上限）。

## 動手做

我們將 PRR 檢查表實作為可執行的自動化啟動檢查腳本（Config Validator），在服務啟動或 CI/CD 階段載入部署設定並自動阻斷不合格的配置。

- 完整 TypeScript 實作：[examples/ts/ch12/index.ts](../examples/ts/ch12/index.ts)
- 完整 Python 實作：[examples/py/ch12/main.py](../examples/py/ch12/main.py)

以下節錄 TypeScript 版 `validateProductionConfig` 的部分核心閘道邏輯，驗證延遲 SLO、成本上限（含 `inference_geo: "us"` 的 1.1× 倍率）與部分自主權等級的相依條件（完整驗證仍須確認 `passPow3` 為有效有限數值且達標，並由設定檢查或其他控制機制驗收連續 14 天、零嚴重誤判、累計退款上限與 L1 無寫入憑證等條件）：

```ts
// 節錄自 examples/ts/ch12/index.ts
const sloOk =
  isPos(cfg.latencySlo.triageP95Sec) &&
  isPos(cfg.latencySlo.multiStepP95Sec) &&
  cfg.latencySlo.triageP95Sec <= 2.5 &&
  cfg.latencySlo.multiStepP95Sec <= 18;

const geoValid = cfg.inferenceGeo === "global" || cfg.inferenceGeo === "us";
const geoMult = cfg.inferenceGeo === "us" ? 1.1 : 1.0;
const estMonthlyUsd =
  cfg.budget.dailyTicketVolume * 30 * cfg.budget.estimatedBaseCostPerTicketUsd * geoMult;
const costOk =
  geoValid &&
  isPos(cfg.budget.monthlyBudgetCapUsd) &&
  isPos(cfg.budget.dailyTicketVolume) &&
  isPos(cfg.budget.estimatedBaseCostPerTicketUsd) &&
  estMonthlyUsd <= cfg.budget.monthlyBudgetCapUsd;

const levelValid = cfg.autonomyLevel === "L1" || cfg.autonomyLevel === "L2" || cfg.autonomyLevel === "L3";
let autonomyOk = levelValid && typeof cfg.safety.hitlRequiredForMutating === "boolean";
if (cfg.autonomyLevel === "L2" && !cfg.safety.hitlRequiredForMutating) {
  autonomyOk = false;
}
if (
  cfg.autonomyLevel === "L3" &&
  (!isPos(cfg.safety.maxAutoRefundUsd) || cfg.safety.maxAutoRefundUsd > 50 || cfg.evalGate.passPow3 < 0.95)
) {
  autonomyOk = false;
}
```

執行驗證腳本，確認所有閘道皆回傳 `[PASS]` 且 Exit Code 為 `0`：

```bash
python3 books/enterprise-agents/examples/py/ch12/main.py
cd books/enterprise-agents/examples/ts && npx tsx ch12/index.ts
```

## 自我檢核

1. **（入門｜10 分鐘）** 在 Buy vs Build 決策矩陣中，為什麼 `OrderOps` 這類高併發且對成本敏感的系統，不建議在核心路徑使用高度抽象的第三方編排框架？
2. **（進階｜15 分鐘）** 若 `OrderOps` 計畫將某類低風險退款工單從 L2 升級為 L3 有界全自動，根據本章的 PRR 與演進規範，必須滿足哪三個必要條件？
3. **（挑戰｜20 分鐘）** 假設 `OrderOps` 因合規要求必須啟用 `inference_geo: "us"`（1.1× 倍率），且客戶要求將日工單量提升至 60,000 筆／天。若單筆優化後基礎 API 成本維持 $0.011，請計算新的月度滿載 API 成本，並說明在什麼條件下仍能維持正向估算淨效益。

### 參考解答

1. **解答**：第三方編排框架常隱藏 Prompt 組裝、動態摘要與內部重試邏輯，容易破壞 Prompt Caching 的穩定前綴，導致 `cache_read_input_tokens` 命中率下降、成本失控；此外，當發生 `429`、`529` 或 Streaming 斷線時，抽象層會遮蔽底層 `messages` 與 `stop_reason`，大幅增加線上除錯時間。
2. **解答**：第一，離線 Eval 的 `Pass^3` 必須達到 ≥ 0.95（高於通用上線基準 0.85）；第二，必須設定明確的單筆自動執行金額上限（`0 < maxAutoRefundUsd <= 50`），超額工單仍強制退回 L2 人工核准；第三，在 L2 階段需連續 14 天穩定運行且 `Pass^3 >= 0.95`、零嚴重誤判（30 秒 Feature Flag 退場機制則屬通用 PRR 要求）。
3. **解答**：
   - **新月度滿載 API 成本**：`60,000 筆/天 × 30 天 = 1,800,000 筆/月`。基礎成本為 `1,800,000 × $0.011 = $19,800/月`，乘以 `1.1×` 資料駐留倍率後為 `$21,780/月`。
   - **維持正向估算淨效益條件**：雖然 `$21,780` 超過原訂 $18,000 的月成本上限，但只要 L2/L3 每日能節省的人力處理成本超過每日 API 成本（`$21,780 ÷ 30 = $726/天`），系統整體仍為正向估算淨效益。以 L2 每筆節省 $1.20（3 分鐘 × $24/小時）計算，若將全量 API 呼叫成本 `$726/天` 視為固定支出，則每日處理 605 筆 L2 工單（約佔總量 1.01%）恰好打平、606 筆起淨效益為正（若 API 呼叫量隨實際處理筆數變動，則應依實際呼叫筆數計算變動成本）；但工程團隊仍須同步向財務申請調高預算上限，或進一步優化快取命中率與模型分層比例。

## 延伸閱讀

- [Anthropic Claude API Pricing & Prompt Caching](https://platform.claude.com/docs/en/about-claude/pricing) — 官方針對模型牌價、Prompt Caching 倍率與 `inference_geo` 資料駐留費率的完整說明。
- [Google SRE Book: Production Readiness Review](https://sre.google/sre-book/evolving-sre-engagement-model/) — 傳統分散式系統 PRR 審查流程與 [Launch Coordination Checklist](https://sre.google/sre-book/launch-coordination/) 的原始工程規範。
- 本書前序章節回顧：可靠性工程與熔斷（ch06）、Eval 與 `Pass^k`（ch07）、單位經濟學（ch08）、安全治理（ch09）與可觀測性（ch10）。
