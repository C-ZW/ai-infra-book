# 第 3 章：Context Engineering：從 Prompt 調校到上下文預算管理

在生產環境裡，多數工程師把 Prompt 當成「調整語氣與措辭的文案」，但對企業級 Agent 而言，Context Window 就是執行期的**工作記憶體**（Working Memory）。當 `OrderOps` 每天處理 50,000 筆工單、每筆平均經歷 5 個回合時，塞進 Context 的每一個多餘 token 都會在後續回合被重複計費，同時稀釋模型對關鍵規則的注意力。

本章把焦點從單次 Prompt 寫作，轉移到系統層級的 **Context Engineering**：如何像規劃記憶體分頁與快取前綴一樣，編排靜態前綴與動態載荷、配置 Extended Thinking 預算，並在長對話中用截斷與 Compaction 守住延遲與成本邊界。

---

## 從你已知的出發

資深後端工程師設計高效能服務時，會利用「**CPU 快取局部性**（Cache Locality）」與「**虛擬記憶體分頁**（Virtual Memory Paging）」來壓低延遲與記憶體壓力。這兩個機制與 LLM 的 Context 管理有直接的結構對照：

- **CPU 快取前綴對照 Prompt Caching**：CPU 依賴空間局部性來重用穩定資料；LLM 推論引擎的 KV Cache 也是如此：API 請求必須依照 `tools` → `system` → `messages` 的固定前綴順序送出，當請求前綴字元完全一致、符合模型最低門檻，且已有尚未到期的對應快取項目時，就能命中快取，以基礎輸入單價的 **0.05×**（Sonnet 5.5 / Opus 5.5）或 **0.10×**（Haiku 5.5）讀取（冷啟動、TTL 到期與首次回應開始前的並發建立期間仍可能未命中）。需注意 KV Cache 使用量、上下文容量與計費口徑是三種不同的量。
- **虛擬記憶體分頁對照 Context Compaction**：當行程的 working set 超出實體記憶體，作業系統會把冷資料換出（swap out），只把熱頁留在 RAM。Agent 進入較長對話（例如示例第 4 回合以後），早期工具回傳與中間推理過程會快速膨脹，我們必須透過「工具結果截斷」與「對話歷史 Compaction」，把舊回合壓縮成精簡摘要，只保留最近回合（例如最近 2 個完整回合）在 Context 中。

這個技術對照的**成立邊界**在於「重用穩定內容與熱／冷資料分層」：靜態規則放最前、動態工單放最後、過期觀測壓縮換出。**失效邊界**則在於：LLM 的 KV Cache 對任何一個空白字元或時間戳記的改動都會使該斷點及其後段失效（Cache Miss）；此外，作業系統的分頁換入換出是無損的，而 Context Compaction 是有損壓縮，一旦把關鍵訂單編號或金額壓掉，模型就無法憑空還原。

---

## 核心機制

### Context Window 組成與 Context Rot

一次完整的 Claude Messages API 請求，上下文由三個請求內容區塊加上生成輸出預算組成：

```text
[1. tools]        -> 18 個工具 Schema（OrderOps 基準：3,600 tokens）
[2. system]       -> 角色定義、合規規則、Few-shot（OrderOps 基準：2,400 tokens）
[3. messages]     -> 多回合對話、tool_use、tool_result、thinking blocks
[4. output]       -> 本回合生成的 thinking + text / tool_use（受 max_tokens 約束）
```

把這四塊全部塞滿並不代表效果最好。實務上常討論 **Context Rot**（上下文腐化）風險：隨著無關資訊或冗長日誌累積，模型在長上下文中段（Middle）的資訊檢索準確率可能下滑，且無關的干擾物可能稀釋對系統規則的注意力（實際影響幅度須透過自身任務的評測驗證）。對 `OrderOps` 而言，把一份 8,000 tokens 的完整 ERP 原始 JSON 塞進 `tool_result`，不僅浪費輸入預算，還會提高模型漏看工單真實退款上限的風險（可透過評測驗證）。

### 前綴穩定排序與 `cache_control` 斷點

Claude API 的 Prompt Caching 採前綴比對（Prefix Matching），評估順序固定為 **`tools` → `system` → `messages`**（與 JSON 欄位序列化順序無關），且前綴需達模型最低門檻（依模型版本與官方文件確認，例如較新旗艦模型 `claude-opus-5-5` 為 512 tokens，標準 Sonnet 系列如 `claude-sonnet-5` 為 1,024 tokens，部分較舊模型則為 4,096 tokens；`OrderOps` 的 3,600 與 6,000 tokens 前綴均已超過上述 512 與 1,024 tokens 門檻，但各模型實際最低門檻，包括 Sonnet 5.5，仍須依官方文件另行確認）。為了最大化快取命中率，必須把靜態內容集中在前段，動態內容推到最尾端：

1. **`tools` 尾端斷點**：在最後一個工具定義加上 `cache_control: { type: "ephemeral" }`，把 `OrderOps` 的 3,600 tokens 工具面鎖進快取。
2. **`system` 尾端斷點**：把 2,400 tokens 的靜態營運規範與 Few-shot 放在 `system`，並在最後一個 text block 加上 `cache_control: { type: "ephemeral" }`。
3. **動態載荷後置**：工單編號、客戶訊息、當前時間等每次請求都會變動的資料，一律放在 `messages` 的 `user` 訊息中，絕對不要插進 `system` 前段。

> [!NOTE]
> 本章僅處理前綴結構與斷點擺放；關於 5 分鐘（1.25× 寫入）與 1 小時（2.0× 寫入，`ttl: "1h"`）的完整 FinOps 損益平衡精算，見 ch08。若需進一步約束輸出形狀，可在工具定義使用 `strict: true` 控制工具名稱與參數，或在請求使用 `output_config.format` 控制最終 JSON 輸出（遠端 MCP Connector 與 Batch API 見後續章節）。

以下是 TypeScript 的前綴分層建構核心片段（完整可執行檔見 `books/enterprise-agents/examples/ts/ch03/index.ts`，Python 對照實作見 `books/enterprise-agents/examples/py/ch03/main.py`）：

```typescript
// 節錄自 examples/ts/ch03/index.ts（動態欄位已省略並須經 XML escaping）
export function buildLayeredPrompt(
  ticket: OrderOpsTicket,
  tools: Anthropic.Tool[],
  staticPolicyText: string,
): LayeredPrompt {
  const cachedTools = tools.map((tool, idx) =>
    idx === tools.length - 1
      ? { ...tool, cache_control: { type: "ephemeral" as const } }
      : tool,
  );

  const system: Anthropic.TextBlockParam[] = [
    {
      type: "text",
      text: staticPolicyText,
      cache_control: { type: "ephemeral" },
    },
  ];

  return {
    tools: cachedTools,
    system,
    messages: [{ role: "user", content: `<ticket_context>...</ticket_context>` }],
  };
}
```

### XML 結構化分區與 Few-shot 邊界案例

在企業級 Prompt 中，可使用 XML 標籤（如 `<role>`、`<rules>`、`<examples>`、`<ticket_context>`）與可靠序列化標示指令與不可信資料的邊界；實際防護效果仍應透過提示注入評測驗證，並配合應用層權限控制。寫入 `<ticket_context>` 前必須先做 XML escaping（或可靠序列化），並把工單、ERP 自由文字與壓縮摘要一律視為不可信資料。

與其寫十條抽象形容詞（「請保持專業且謹慎」），不如在 `<examples>` 中放 2 到 3 個**邊界案例**（Edge Cases）。例如針對 `OrderOps` 的示例業務規則：明確示範「當物流追蹤碼依最後更新時間已超過 72 小時無更新且訂單狀態為 `delayed` 時，先查庫存再決定是否補償」，以及「當工單要求退款金額大於訂單總額時，必須拒絕並回報異常」。這能直接校準模型的輸出格式與決策邊界。

### Extended Thinking 配置與多回合保留

面對高難度異常工單（例如跨倉調撥衝突或複雜發票對帳），可以啟用 **Extended Thinking**，讓模型在輸出最終回覆或 `tool_use` 之前，先在內部完成多步驟推理：

- **模式與配額**：較新模型支援自適應推理模式，亦可使用 `thinking: { type: "enabled", budget_tokens: N }`（具體預設模式與可調參數依模型版本與官方文件確認）。設定 `budget_tokens` 時，`max_tokens` 必須嚴格大於 `budget_tokens`，以保留最終答案或工具呼叫的輸出配額。
- **計費與延遲**：`thinking` 產生的 tokens 會增加輸出成本與延遲（Sonnet 5.5 輸出單價為 `$10.00 / MTok`，Opus 5.5 為 `$20.00 / MTok`；實際 `thinking` 計費與 `usage` 欄位計數口徑應依所用模型與官方文件確認），因此應依任務品質改善、錯誤風險、延遲與成本評測決定啟用範圍，而非無條件全量預設開啟。
- **多回合保留 `thinking` block**：在 `tool_use` 迴圈中，把上一回合 `assistant` 的回應寫回 `messages` 時，**必須原封不動保留先前的 `thinking` block（包含其中的 `signature`）**，並依所用 API 規格處理 `tool_result`（以 `tool_use_id` 配對）及其他加密推理區塊的格式與排序。

```python
# 節錄自 examples/py/ch03/main.py
response = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=8000,
    thinking={"type": "adaptive"},
    tools=prompt["tools"],
    system=prompt["system"],
    messages=prompt["messages"],
)
# 多回合必須原樣保留 response.content（含 thinking block 與 signature）
updated_messages = [*prompt["messages"], {"role": "assistant", "content": response.content}]
```

### 工具結果截斷、Compaction 與 Scratchpad

當對話進入多回合（例如示例第 3 回合以後），Context 膨脹的主要元兇往往不是使用者的幾句話，而是工具回傳的龐大資料。生產系統必須同時採用三道壓縮防線：

1. **工具結果截斷**（Truncation）：在寫入 `tool_result` 之前，對超過閾值（例如粗估 600 tokens / 約 2,400 字元）的回傳採頭尾保留、中段省略的截斷（並確保小上限時不會反向膨脹），優先投影必要欄位與分頁，避免單次粗估 8,000-token 的 ERP 日誌在後續回合被反覆計費。
2. **歷史 Compaction**：以 token 預算與輸出預留量為準（例如第 4 回合作為示例觸發條件），只壓縮已完成的工具交換為結構化 `<compacted_history>` 摘要，不可切斷 `tool_use` 與其對應的 `tool_result`，並原樣保留最近回合。
3. **Scratchpad 與應用層邊界**：可要求模型把已確認的事實寫入狀態區塊，但模型產出的 `refund_eligible: true` 只能視為待驗證線索。租戶身分必須來自已驗證的請求憑證，工具執行器須按租戶查驗訂單權限，並在退款前依權威帳本重查餘額、幣別、資格與冪等鍵。

---

## Worked Example：Extended Thinking 與工具裁剪的真實成本帳本

以下以 `OrderOps` 基準（Sonnet 5.5：Input `$2.00 / MTok`、Output `$10.00 / MTok`；基準前綴 `6,000` tokens；第 2–5 回合每回合新增歷史輸入 `1,200` tokens（已含重送的可見 assistant 輸出與工具結果）、每回合輸出 `350` tokens；5 回合未優化基準累計 `42,000` input / `1,750` output，單筆 `$0.1015`）獨立實算兩個情境：

```text
情境 A（獨立首輪載荷情境）：單筆高難度工單開啟 Extended Thinking（max_tokens = 8,000）
假設第 1 回合寫入 6,000-token 前綴（5m TTL 寫入倍率 1.25×），首輪另有動態輸入 1,200 tokens，
且觀測到計費輸出為 4,000 thinking tokens + 350 回覆 tokens（合計 4,350 output tokens）：
- 前綴快取寫入成本 = (6,000 × $2.00 × 1.25) ÷ 1,000,000 = $0.015000
- 新增輸入成本     = (1,200 × $2.00) ÷ 1,000,000        = $0.002400
- 輸出成本（含思考）= (4,350 × $10.00) ÷ 1,000,000       = $0.043500
- 單回合總計       = $0.060900（光 thinking 4,000 tokens 就佔了 $0.040000）

情境 B（獨立大回傳情境）：第 2 回合工具回傳從 8,000 tokens 裁剪為 600 tokens，對後續 3 回合的乘法節省
- 單次省下的輸入量 = 8,000 - 600 = 7,400 tokens
- 後續第 3、4、5 回合共 3 次重送都會帶入該工具結果（未命中快取的新增對話區，且假設中途未經 Compaction 移除）：
  後續重送累計省下 = 7,400 × 3 = 22,200 input tokens（若加計第 2 回合首次送入則端到端為 29,600 tokens）
- 以 Sonnet 5.5 基礎輸入單價 $2.00 / MTok 計算：
  後續重送節省 = (22,200 × $2.00) ÷ 1,000,000 = $0.044400（含首次送入為 $0.059200）
```

這組數字清楚說明兩個工程決策：第一，Extended Thinking 的輸出單價極高，必須只針對高風險或複雜工單按需開啟；第二，工具回傳的截斷具有**乘法效應**，越早截斷，後續回合省下的輸入成本與延遲越多。

---

## 故障模式與防禦

1. **前綴汙染導致 Cache Silent Miss**
   - **現象**：API 正常回傳 `200 OK`，但監控發現 `usage.cache_creation_input_tokens` 持續偏高、而 `usage.cache_read_input_tokens` 遠低於預期（或為 `0`）。
   - **根因**：有人在 `system` prompt 最前端插入了 `current_timestamp`、`request_id` 等動態變數。由於前綴評估順序為 `tools` → `system` → `messages`，`tools` 斷點（3,600 tokens）仍可命中讀取，但 `system`（2,400 tokens）與後續斷點會失配重寫；此外並發請求在第一個回應開始前也可能同時 miss。
   - **防禦**：嚴格執行 `tools` → `system` → `messages` 分層；CI 加入前綴雜湊檢查；上線後在監控區間加總各欄位，追蹤 `cache_read_input_tokens / (input_tokens + cache_creation_input_tokens + cache_read_input_tokens)`，按前綴版本區分冷啟動、TTL 到期與持續失配，低於示例告警門檻（如 70%）即告警。

2. **遺失 `thinking` block 或 `signature` 導致多回合失敗**
   - **現象**：在 `tool_use` 迴圈第 2 回合送出請求時，API 回傳 `400 invalid_request_error` 提示 thinking block 格式錯誤或簽章無效。
   - **根因**：開發者在組裝歷史訊息時，只擷取了 `text` 與 `tool_use` block，把 `thinking` block 過濾掉，或自行修改了 `signature`。
   - **防禦**：使用 `appendAssistantTurn` 等統一 helper，將 `response.content` 陣列完整寫回 `messages`，Compaction 時也僅壓縮已完成的更早回合，不拆解當前回合的 `thinking` 區塊；遇到 `max_tokens` 或 `model_context_window_exceeded` 截斷時，禁止派送未完成的工具參數。

3. **未截斷的工具回傳引發 Context 溢位或延遲飆升**
   - **現象**：某筆工單呼叫 ERP 查詢後回傳大型日誌（例如 15,000 tokens），使端到端延遲面臨突破 p95 SLO（分流 2.5s / 多步處置 18s）或觸發截斷的風險。
   - **根因**：直接把外部 API 的原始 JSON 全量塞進 `tool_result`。
   - **防禦**：在工具執行層強制套用 `truncateToolResult`（上限粗估 600 tokens / 2,400 字元），並對清單類工具預設加上 `limit` 與欄位白名單。

---

## 動手做

本節對應的完整可執行程式碼位於：
- TypeScript：`books/enterprise-agents/examples/ts/ch03/index.ts`
- Python：`books/enterprise-agents/examples/py/ch03/main.py`

兩份程式皆實作了 `buildLayeredPrompt`、`truncateToolResult` 與 `compactHistory`，並支援在未設定 `ANTHROPIC_API_KEY` 時自動切換為離線驗證模式，示範工具結果截斷、多回合歷史 Compaction 與 Extended Thinking 成本帳本。

執行 Python 版本驗證：

```bash
python3 books/enterprise-agents/examples/py/ch03/main.py
```

若已設定 `ANTHROPIC_API_KEY` 與 TypeScript 相依套件（`@anthropic-ai/sdk`、`tsx`），可執行 TypeScript 版本或跑型別檢查：

```bash
npx --prefix books/enterprise-agents/examples/ts tsx books/enterprise-agents/examples/ts/ch03/index.ts
```

---

## 自我檢核

1. **（入門｜預估 10 分鐘）** 為什麼在 Claude API 中，把當前時間 `2026-11-21T10:00:00Z` 放在 `system` prompt 的第一行，會讓 `OrderOps` 的 `system` 前綴快取失效？此時 `tools`（3,600 tokens）與 `system`（2,400 tokens）分別會發生什麼事？應該改放在哪裡？
2. **（進階｜預估 15 分鐘）** 在多回合 `tool_use` 迴圈中，為什麼在支援手動 `budget_tokens` 的模式下 `max_tokens` 不能小於或等於 `budget_tokens`？而在使用自適應推理模式時，應如何依官方文件確認深度控制與輸出上限？把上一回合的 `assistant` 回應寫回 `messages` 時，必須遵守什麼規則？
3. **（挑戰｜預估 20 分鐘）** 假設在獨立大回傳情境下，`OrderOps` 某個工具平均回傳 5,000 tokens，且每筆工單平均還有 4 個後續回合（假設未經 Compaction 移除）。若你實作截斷器將其壓縮為 500 tokens，在 Sonnet 5.5（Input `$2.00 / MTok`）下，僅計後續重送每筆工單可省下多少輸入 tokens 與美元成本？若每日有 50,000 筆工單觸發此工具，每月（30 天）共省下多少美元？（若加計首次送入，端到端總節省又為何？）

### 參考解答

1. **解答**：Prompt Caching 採用嚴格前綴比對（`tools` → `system` → `messages`）。時間戳記放在 `system` 第一行時，已寫入且仍有效的 `tools` 斷點（3,600 tokens）仍可命中讀取，但從 `system` 斷點起（2,400 tokens）會因位元組改變而失配並重新寫入快取。正確做法是將靜態政策留在 `system`，把時間戳記等動態欄位放進 `messages` 最後的 `user` 訊息（例如 `<ticket_context>`）中。
2. **解答**：在手動 `budget_tokens` 模式下，`max_tokens` 是單回合所有輸出（包含 `thinking` tokens 與最終可見的 `text` / `tool_use` tokens）的總上限，因此必須嚴格大於 `budget_tokens`，否則沒有配額輸出最終答案。若使用較新模型的自適應推理模式，應依該模型版本的官方文件確認對應的深度控制與 `max_tokens` 設定。寫回 `messages` 時，必須原封不動保留 `response.content` 中的 `thinking` block 與其 `signature`（其他加密區塊與格式細節依所用 API 官方規格確認）。
3. **解答**：
   - 單次省下輸入：`5,000 - 500 = 4,500` tokens。
   - 僅計後續 4 個回合重送：`4,500 × 4 = 18,000` input tokens / 筆，單筆省下 `(18,000 × $2.00) ÷ 1,000,000 = $0.036` / 筆；每月（1,500,000 筆）省下 `$54,000` / 月。
   - 若加計首次送入（共 5 次）：`4,500 × 5 = 22,500` tokens / 筆，單筆 `$0.045` / 筆，每月 `$67,500` / 月。

---

## 延伸閱讀

- [Anthropic Prompt Caching 官方文件](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)：深入檢視 `cache_control` 斷點數量上限與 TTL 規則。
- [Anthropic Extended Thinking 指南](https://platform.claude.com/docs/en/build-with-claude/thinking)：了解手動 `budget_tokens`、自適應推理模式與 `thinking` block 簽章驗證機制。
- 本書第 8 章（`ch08-cost-and-latency-optimization.md`）：完整 5m vs 1h TTL 損益平衡與 `OrderOps` 月成本壓縮帳本。
