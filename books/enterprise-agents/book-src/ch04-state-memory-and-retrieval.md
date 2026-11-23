# 第 4 章 持久化狀態、多層記憶與企業知識檢索（Agentic RAG）

## 從你已知的出發

資深後端工程師設計分散式服務時，靠兩項資料庫基石保證系統可恢復與多租戶隔離：**預寫日誌與檢查點**（WAL Checkpoint）確保程序崩潰或重啟後，能從最後一個已提交的交易邊界或恢復點續跑；**列級權限**（Row-Level Security, RLS）則在查詢引擎層強制過濾 `tenant_id`，不讓應用層的疏忽外洩跨租戶資料。

把這組機制對照到企業級 Agent：
- **成立邊界**：`OrderOps` 處理「等待供應商回覆 ETA」的工單時，可能暫停數小時。將每回合的 `messages`、已執行的 `tool_use` 與 `tool_result` 配對以及 `waiting_for` 狀態持久化到 PostgreSQL，可讓無狀態 Worker 節點恢復上下文；但要做到安全喚醒續跑，還須結合併發控制（CAS）、可恢復的操作紀錄、外部副作用的冪等或對帳，以及權限重查。同樣地，企業知識庫檢索必須在向量與全文查詢前就套用 `tenant_id` 與 `acl_roles` 過濾（相當於 RLS）。
- **失效邊界**：資料庫 WAL 恢復依賴已記錄的資料變更與恢復規則，而重新執行 LLM 推理及外部工具則具備非確定性與副作用。一旦某個 `tool_result` 已經寫入持久化狀態，續跑時**絕不能**重新呼叫一次寫入型工具（否則會重複退款），只能把已保存的觀測結果直接餵回模型；此外，RLS 只管得到結構化資料列，若把未過濾的檢索段落塞進 Context Window，LLM 仍可能在生成階段把機密條文混合輸出。

## 核心機制

### 1. 三層記憶模型與儲存配置基線

企業級 Agent 不能把所有資訊都塞進單次請求的 `messages` 陣列，必須拆分為生命週期與存取延遲截然不同的三層記憶：

```text
[1] Working Context (單次 API 請求生命週期)
    └─ System Prompt + Tools + 近期對話 + 本回合檢索段落（受 Context Window 上限約束）
[2] Session State Store (數分鐘～數天，PostgreSQL + Redis)
    └─ 工單對話歷史、turn_count、waiting_for、待喚醒的 tool_use_id
[3] Long-term Memory (跨工單長期留存，Vector DB + Full-Text Index)
    └─ Episodic（歷史工單處置紀錄）與 Semantic（退貨政策、供應商合約）
```

在 `OrderOps` 中，設定基線如下：Redis 負責熱快取，Key 格式為 `orderops:session:{tenant_id}:{session_id}`，快取 TTL 設為 `86,400` 秒（24 小時），單 Worker 連線池上限 `50`、單次讀取 timeout `150 ms`。PostgreSQL 負責持久化落盤，單 Worker 連線池設為 `min=5, max=20`、寫入 timeout `2,000 ms`，單筆 `messages_json` 軟上限為 `512 KB`（超過即觸發早期回合摘要壓縮，避免序列化與網路傳輸拖垮延遲）。正式部署時須為資料表啟用 PostgreSQL RLS 政策並在交易內設定租戶身分（例如 `SET LOCAL app.tenant_id = ...`），且應用連線角色不可為表擁有者或具備 `BYPASSRLS` 權限。

寫入路徑必須以 PostgreSQL 為唯一事實來源（Source of Truth）：先寫 PostgreSQL，成功後再更新或失效 Redis；喚醒、授權與寫入決策一律以資料庫為準，快取回填須帶 `version` 保護，避免舊讀取在較新寫入後回填過期版本。請嚴格區分三種期限：Redis 快取 TTL（24 小時）、外部等待逾時 `expires_at`（例如 24 小時）與法遵資料留存期限（依企業稽核規範另定）。當工單進入 `waiting_external` 狀態時，Worker 釋放記憶體與連線，直到供應商 Webhook 回調才從資料庫載入 `AgentSessionState` 繼續下一回合；並另建獨立的操作與稽核紀錄表，確保 `messages_json` 壓縮摘要時仍能保留未完成工具配對、退款事實與稽核證據。若工單在 `waiting_external` 超過 `expires_at` 仍無外部回調，背景排程器會以條件更新（`WHERE status = 'waiting_external' AND version = $3`）與正常喚醒競爭同一狀態轉移，確保只有一方能成功推進狀態；至於超時通知與退款的互斥，仍須透過完整狀態機、操作紀錄、可靠派送及下游冪等機制確保。

### 2. 對話歷史的 Schema 化持久化與 Wire-Level 契約

直接把整個 `messages` 陣列序列化成單一純文字 Blob，會在模型升級或 Schema 變更時難以除錯。生產環境應為 `agent_sessions` 建立明確欄位，並加入 `version` 樂觀鎖防止併發喚醒覆寫：

```sql
CREATE TABLE agent_sessions (
  tenant_id     TEXT NOT NULL,
  session_id    TEXT NOT NULL,
  ticket_id     TEXT NOT NULL,
  status        TEXT NOT NULL, -- 'active' | 'waiting_external' | 'completed' | 'expired'
  turn_count    INTEGER NOT NULL DEFAULT 0,
  version       INTEGER NOT NULL DEFAULT 1,
  messages_json JSONB NOT NULL,
  waiting_for   TEXT,
  expires_at    TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (tenant_id, session_id)
);
CREATE INDEX idx_sessions_waiting ON agent_sessions (status, expires_at)
  WHERE status = 'waiting_external';
```

每次 `Turn` 結束（無論是 `tool_use` 還是進入 `waiting_external`），系統先以帶狀態條件的 CAS（`UPDATE ... SET version = version + 1 WHERE tenant_id = $1 AND session_id = $2 AND status = $3 AND version = $4 AND expires_at > NOW()`）檢查更新列數是否為 `1`，並在同一交易寫入可恢復的操作紀錄，再回傳外部事件（跨節點分散式重試與 Outbox 見 ch06）。

在 Wire-Level 上，訊息配對與區塊順序（例如 `assistant` 的 `tool_use` 與後續 `user` 訊息中 `tool_result` 的對應與排列）須依相應版本的官方 Messages API 工具使用文件核對；`createdAt` 等本地 metadata 必須留在 wire payload 之外，而工具回合所需的原始 `assistant` `thinking` / `redacted_thinking` 區塊與簽章則須完整保留。未完成的呼叫可先存為工作紀錄，組裝 API 歷史時才要求配對完整；若 `pending_external` 已作為 `tool_result` 寫入，後續 Webhook 應成為新的事件輸入（例如新的 `user` 訊息）。程式必須依據回應中的 `stop_reason` 分派流程、依 `usage` 計量與執行預算政策：

```json
{
  "id": "msg_01XFDUDYJgAACzvnptvVoYEL",
  "stop_reason": "tool_use",
  "content": [
    {
      "type": "tool_use",
      "id": "toolu_01A09q90qw90lq917835lq9",
      "name": "search_knowledge_base",
      "input": { "query": "carrier delay 72 hours APAC", "top_k": 3 }
    }
  ],
  "usage": {
    "input_tokens": 1840,
    "cache_read_input_tokens": 6000,
    "output_tokens": 92
  }
}
```

當 `stop_reason === "tool_use"` 時，Worker 執行工具並寫回 `tool_result`（若工具失敗則帶上 `"is_error": true` 與錯誤訊息讓模型降級處理）；`end_turn` 或 `stop_sequence` 代表本輪推理正常結束；若出現 `max_tokens` 或 `model_context_window_exceeded` 代表輸出或上下文截斷，`refusal` 代表安全拒答，皆不可當成正常回覆；若使用服務端工具並收到 `pause_turn`，則須依協定續跑。串流收到 `message_stop` 後仍須檢查 `stop_reason`、完整區塊、schema 與授權，並處理 HTTP `200` 之後才送出的 SSE `error` 事件。

### 3. 靜態 RAG 的盲點 vs Agentic RAG

傳統靜態 RAG 在使用者輸入進來後，固定執行一次向量檢索並把 Top-10 文件硬塞進 Prompt。這種作法在企業場景有兩個致命傷：第一，簡單工單（例如單純查詢物流單號）根本不需要政策文件，卻白白承擔數千 tokens 的上下文噪音與費用；第二，單次查詢詞彙若與合約條文用語不同（例如工單寫「海關卡關」，合約寫「不可抗力清關延遲」），靜態 RAG 沒有機會換詞重試。

**Agentic RAG** 把檢索包裝成一個唯讀工具（例如 `search_knowledge_base`）。由 Agent 自主決定何時需要查資料、拆解關鍵字、結合 **Hybrid Search**（BM25 全文檢索 + Vector 語意檢索 + RRF 倒數排名融合，常數 `k = 60`），並在首輪結果不足時自主改寫查詢詞重試。設定上，單次檢索工具 timeout 設為 `800 ms`，單回合最多允許 `max_search_retries = 2` 次改寫重試（串行檢索最多耗 `2.4 s`，尚須加上改寫、排隊與模型延遲，適用 `18 s` 多步處置 SLO，而非 `2.5 s` 分流 SLO）。

在 Prompt Caching 佈局上，Claude 依 `tools → system → messages` 順序建立快取前綴；為維持穩定前綴，檢索回來的動態段落應放在穩定 `tools` 與 `system` 前綴之後的適當訊息中（工具檢索結果通常放在對應 `tool_result`），絕不能插入 `tools` 或 `system` 之間。System Prompt（`2,400` tokens）與 18 個工具定義（`3,600` tokens）合計構成 `6,000` tokens 的穩定前綴；若只把 `cache_control: { "type": "ephemeral" }` 放在最後一個工具，僅能涵蓋約 `3,600` tokens 的工具區段，因此應將斷點設在最後一個穩定的 `system` 內容區塊，才能完整涵蓋 `6,000` tokens（5 分鐘 TTL 讀取僅需基礎輸入單價的 `0.05×`）。若數小時後才喚醒續跑，快取可能已過期而產生 `cache_creation_input_tokens > 0`，不可假設必然命中。

在排序融合上，BM25（建議初始參數 `k1 = 1.2, b = 0.75`）擅長精準匹配料號、條文編號與專有名詞，密集向量（Dense Vector Cosine Similarity）則擅長捕捉語意同義詞。兩者原始分數尺度不同，採用 RRF（`k = 60`）只看 1-based 名次不看絕對分數：`rrf_score = 1 / (60 + rank_bm25) + 1 / (60 + rank_vector)`；若候選文件未出現在某路檢索結果中，該路貢獻為 `0`，且可依 `(rrf_score DESC, chunk_id ASC)` 穩定處理同分，並依實際資料量測 Top-3 品質。

### 4. 多租戶 ACL 前置過濾與 Citation 驗證

企業知識庫常同時存放多個租戶的專屬合約與由受信任發布路徑管理的 `global` 規範。`tenant_id` 與 `acl_roles` 必須來自已驗證的呼叫身分，且 **ACL 過濾必須發生在檢索評分之前**（Pre-filtering），絕不能先做全域 Top-K 檢索再由程式碼或 LLM 過濾，否則高分機密文件會把該租戶真正有權限的文件擠出 Top-K，甚至在 Prompt 中造成跨租戶洩漏（資安攻擊防禦全貌見 ch09）。須注意部分向量近似索引（如 HNSW/IVFFlat）在結合 `WHERE` 過濾時可能出現有效結果少於 K 的情況（實際行為與 iterative scan 選項須依所用資料庫與 pgvector 版本官方文件確認），應依 ACL 選擇性搭配確切搜尋或分區索引並量測 `recall@K` 與 p95。同時，已授權的文件仍可能包含過時政策或 prompt injection，因此退款工具必須獨立驗證工單歸屬、金額、政策版本與 HITL 門檻，並在續跑時重新檢查已撤銷的權限。

此外，為防止模型捏造條文編號或漏引來源，系統必須對政策型回答要求結構化輸出（例如以 `output_config.format` 約束 JSON claim、來源 ID、條款與版本，並以 `strict: true` 約束工具參數；若需併用原生 Citations 與結構化輸出，須依撰寫時官方 API 文件確認相容性），再於應用層執行確定性 **Citation 驗證**：下例函式只檢查至少存在一個可辨識引用，且所有可辨識引用均在檢索結果清單中；完整輸出格式、逐項主張的引用覆蓋率與引用內容對應關係，仍須另行驗證：

```typescript
// 摘自 examples/ts/ch04/index.ts
export function verifyCitations(
  answerText: string,
  retrieved: SearchResult[],
  requireCitation = true,
): { valid: boolean; cited: string[]; fabricated: string[]; missingCitation: boolean } {
  const allowed = new Set(retrieved.map((r) => `${r.chunk.docId}#${r.chunk.clauseId}`));
  const matches = [...answerText.matchAll(/\[([A-Za-z0-9-]+#[0-9.]+)\]/g)].map((m) => m[1]);
  const fabricated = matches.filter((id) => !allowed.has(id));
  const missingCitation = requireCitation && matches.length === 0;
  return { valid: !missingCitation && fabricated.length === 0, cited: matches, fabricated, missingCitation };
}
```

### 5. Worked Example：靜態 RAG vs Agentic RAG 的真實成本帳

以 `OrderOps` 每日 **50,000** 筆工單（每月 **1,500,000** 筆，平均 `0.58 req/s`、尖峰 `12 req/s` 約 `20×`）、預設工作模型 **Claude Sonnet 5.5**（Input 牌價 **$2.00 / MTok**）計算兩種架構的**檢索片段單次輸入費**差異（情境假設：每筆觸發工單僅檢索一次，且檢索片段只在當次請求按未快取輸入計費；若計算端到端淨節省，尚須計入多輪 Messages 歷史重送、快取寫讀、查詢改寫、工具呼叫與輸出、embedding／搜尋服務成本及品質門檻）：

```text
條件基準：
- 日工單量：50,000 筆/天（30 天 = 1,500,000 筆/月）
- 模型：Claude Sonnet 5.5（Input = $2.00 / MTok）

方案 A：靜態 RAG（情境假設：每筆工單固定塞入 Top-10 文件 = +6,500 tokens）
- 每日額外輸入 = 50,000 × 6,500 = 325,000,000 tokens = 325.0 MTok/天
- 每日檢索輸入成本 = 325.0 × $2.00 = $650.00 / 天
- 每月檢索輸入成本 = $650.00 × 30 = $19,500.00 / 月

方案 B：Agentic RAG（情境假設：僅 35% 工單觸發檢索，Top-3 精準段落 = +1,800 tokens）
- 每日觸發筆數 = 50,000 × 35% = 17,500 筆/天
- 每日額外輸入 = 17,500 × 1,800 = 31,500,000 tokens = 31.5 MTok/天
- 每日檢索輸入成本 = 31.5 × $2.00 = $63.00 / 天
- 每月檢索輸入成本 = $63.00 × 30 = $1,890.00 / 月

檢索片段輸入費降幅（單次未快取口徑）：
- 每日節省 = $650.00 - $63.00 = $587.00 / 天
- 每月節省 = $19,500.00 - $1,890.00 = $17,610.00 / 月（檢索片段輸入費降幅 90.3%）
```

## 故障模式與防禦

1. **孤兒 `tool_use` 與崩潰後重複退款**（HTTP `400 invalid_request_error`）
   - **成因**：Worker 在收到模型回傳的 `tool_use` 後、執行外部工具前崩潰，或退款成功後、寫入 `tool_result` 前崩潰，導致 `messages_json` 缺少配對或下一個 Worker 重送退款。
   - **診斷與告警**：Log 記錄 `tenant_id`、`session_id`、`turn_count`、`http_status: 400`、`error_type: "invalid_request_error"`；當全服務 `400` 錯誤率在 5 分鐘內（最少 100 筆請求）超過 `0.5%` 時觸發 PagerDuty 告警。
   - **防禦**：只在工具執行完畢並產出 `tool_result` 後才更新 `messages_json`；寫入型工具（如退款）在呼叫前先以資料庫 CAS 寫入可恢復的操作紀錄並遞增 `version`，使用綁定業務操作、跨推理重試穩定的 idempotency key（例如 `{tenant_id}:{ticket_id}:refund:{operation_id}`），下游逾時則查詢既有結果或進入 `pending_reconciliation`。若為非同步外部等待，先寫入合成的 `tool_result`（`status: "pending_external"`），後續 Webhook 則作為新的 `user` 事件輸入。
2. **後置過濾造成授權文件被擠出 Top-K**（Post-filtering）
   - **成因**：向量資料庫先取全域 Top-5，應用層再依 `tenant_id` 剔除不屬於該租戶的文件，結果有效段落只剩 0 或 1 筆，Agent 誤判「查無政策」而拒絕合理退款。
   - **診斷與告警**：Log 記錄 `search_query`、`pre_filter_count` 與 `returned_chunks_count`；當全服務 `returned_chunks_count == 0` 比例在 5 分鐘內（最少 50 次檢索）超過 `15%` 時觸發檢索品質告警。
   - **防禦**：在向量索引與 BM25 查詢語句中強制帶入 `WHERE (tenant_id = $1 OR tenant_id = 'global') AND acl_roles && $2::text[]`，並依資料選擇性驗證 pgvector 過濾後的 `recall@K`。
3. **高併發喚醒下的樂觀鎖競爭與 Webhook 重複**
   - **成因**：供應商 Webhook 重試機制在 500 ms 內連續送出兩次相同回調，或到期排程與喚醒同時觸發，兩個 Worker 同時載入同一份 `waiting_external` 狀態並各自呼叫退款工具。
   - **診斷與告警**：Log 記錄 `session_id`、`expected_version`、`actual_version` 與 `idempotency_key`；單一 `session_id` 出現連續 `version_conflict` 超過 3 次即告警。
   - **防禦**：Webhook 須依已驗證來源與事件 ID 去重，且事件經持久化接收後才回傳 `200 OK`；喚醒與到期排程皆須以 `agent_sessions.version` 與 `status = 'waiting_external'` 執行條件 CAS 搶佔（正常喚醒另須檢查 `expires_at > NOW()`，到期轉移則檢查 `expires_at <= NOW()`，並在成功時變更狀態與遞增 `version`，檢查更新列數為 `1`），搶佔失敗立即放棄。
4. **上游限流、過載與串流斷線**（HTTP `429` / `529` / 殘缺 JSON）
   - **成因**：尖峰時段觸發 Anthropic API 限流（`429` 附帶 `retry-after` header）或系統過載（`529 overloaded_error`），或者 SSE 串流在輸出 `tool_use` 參數中途斷線，留下無法解析的殘缺 JSON。
   - **診斷與告警**：Log 記錄 `http_status`、`retry_after_ms`、`stream_truncated: true`；全服務 `529` 或串流截斷率連續 3 分鐘（最少 100 筆請求）超過 `2%` 時告警。
   - **防禦**：SDK 與 Worker 重試須共用總期限與次數預算，不超過 `18 s` 多步處置 SLO；針對 `429` 嚴格遵守 `retry-after`（若超過剩餘期限則立即失敗降級）；針對 `529` 採用指數退避加 Full Jitter（基底 `500 ms`、上限 `16,000 ms`、最多重試 `4` 次，上界合計至多 `7.5 s`）；串流階段只在收到完整 `message_stop` 事件且 `stop_reason`、JSON 與授權檢查通過後，才允許推進 `turn_count` 並落盤。
5. **Prompt Caching 失效導致成本暴增**（`cache_read_input_tokens = 0`）
   - **成因**：開發者在檢索結果出爐後，動態將段落插入 System Prompt 或工具定義之間，破壞了前綴雜湊，或因工具陣列順序未固定，導致讀取 miss 並可能產生新的快取寫入（`cache_creation_input_tokens > 0`）；若 `cache_creation_input_tokens` 與 `cache_read_input_tokens` 皆為 `0`，則應另查斷點位置、最小可快取門檻及快取是否實際啟用。
   - **診斷與告警**：Log 記錄每回合 `usage.cache_read_input_tokens` 與 `usage.cache_creation_input_tokens`；當連續 5 分鐘（最少 100 筆請求）快取命中率低於 `80%` 時觸發 FinOps 告警。
   - **防禦**：固定工具定義與 System Prompt 順序，將 `cache_control: { "type": "ephemeral" }` 斷點設在最後一個穩定的 `system` 內容區塊以涵蓋完整 `6,000` tokens 前綴，並將動態檢索段落嚴格限縮在 `tool_result` 或最新一筆 `user` 訊息中；若兩個欄位皆為 `0`，應優先排查斷點位置與最小 token 門檻。

## 動手做

本章完整可執行範例分別位於 [examples/ts/ch04/index.ts](examples/ts/ch04/index.ts) 與 [examples/py/ch04/main.py](examples/py/ch04/main.py)（本機模擬程式，未直接呼叫真實 Anthropic SDK、MCP 或 Batch API）。兩個範例都實作了：
1. `SessionStateStore`（Python 版使用內建 `sqlite3` 模擬 PostgreSQL `agent_sessions` 複合主鍵、`version` 樂觀鎖與 TTL 過期檢查）。
2. `MultiTenantKnowledgeBase` / `hybrid_search`（強制 `tenant_id` 與 `acl_roles` 前置過濾，並以 RRF 融合 BM25 與向量餘弦分數）。
3. `verifyCitations` / `verify_citations`（比對輸出中的 `[doc_id#clause_id]` 是否皆來自本次授權檢索結果，並攔截漏引）。

執行驗證步驟（TypeScript 需 Node.js 22+ 原生執行或安裝 `tsx`）：

```bash
# Python 版本
python3 books/enterprise-agents/examples/py/ch04/main.py

# TypeScript 版本（Node.js 22+）
node --experimental-strip-types books/enterprise-agents/examples/ts/ch04/index.ts
```

預期終端輸出（以 Python 版為例）：

```text
Resumed session: sess-88412 turn: 3 version: 2 conflict_caught: True
Authorized chunks: ['POL-RET-APAC#4.2', 'POL-SUP-SLA#2.1']
Good citation check: {'valid': True, 'cited': ['POL-RET-APAC#4.2'], 'fabricated': [], 'missing_citation': False}
Bad citation check: {'valid': False, 'cited': ['POL-VIP-EU#9.1'], 'fabricated': ['POL-VIP-EU#9.1'], 'missing_citation': False}
Uncited check: {'valid': False, 'cited': [], 'fabricated': [], 'missing_citation': True}
Retrieved chunks input cost (USD): 0.003600
Retrieved chunks (1,800) + 350 output tokens cost (excl. prefix/other input/history, USD): 0.007100
```

建議進一步測試更多邊界情境：將 `ttl_hours` 設為 `-1` 驗證過期、以 `tenant-eu-02` 搭配 `ops_agent` 驗證跨租戶隔離、故意漏引或混入 `[POL-FAKE#1.0]`，以及測試同文件多條款、空檢索結果、重複 Webhook 與退款成功後崩潰恢復。上線時除了將 `SQLiteSessionStore` 替換為 PostgreSQL 連線池並開啟 RLS 策略外，還須實作並驗證交易內租戶身分傳遞、狀態與版本 CAS、外部操作紀錄與冪等、Webhook 去重及故障恢復機制，才能安全銜接多節點部署。

## 自我檢核

1. **【入門｜10 分鐘】** 為什麼在 `OrderOps` 中不能把所有歷史工單的政策文件都放進 System Prompt，而必須區分 Working Context、Session State Store 與 Long-term Memory？
2. **【進階｜15 分鐘】** 假設 `OrderOps` 某租戶的知識庫有 10,000 筆文件，其中 9,990 筆屬於其他租戶。請說明若改用「先取全域 Top-5 再做應用層過濾（Post-filtering）」會發生什麼問題，並寫出正確的 SQL／檢索過濾條件。
3. **【挑戰｜20 分鐘】** 當 `OrderOps` 工單在等待供應商回覆（`waiting_external`）超過 24 小時後被喚醒，若直接重放整個 `Agent Loop`，如何確保先前已經呼叫過的唯讀查詢或寫入型工具不會被重複執行？

### 參考解答

1. **解答**：System Prompt 受限於 Context Window 上限與每回合線性增加的輸入成本（在 5 回合對話中，若均按未快取費率計價，前綴每多 1,000 tokens 就會乘以 5 倍消耗；以 Sonnet 5.5 `$2.00 / MTok` 計算，單筆多花 `$0.01`，每日 50,000 筆就是 `$500`），且過多無關文件會引發 Context Rot 稀釋注意力。拆分為三層後，Working Context 只保留當下推理所需的最小集合（單次請求結束即釋放），Session State Store 負責跨小時暫停與恢復（Redis 熱快取 + PostgreSQL 落盤），Long-term Memory 則透過 Agentic RAG 按需載入。
2. **解答**：全域 Top-5 極可能被其他租戶的高相似度文件佔滿，導致應用層過濾後剩下 0 筆結果，使 Agent 誤判「查無資料」而拒絕合理請求（實際 Top-5 失敗率仍須依資料分佈量測）；若改把未過濾段落送進 Prompt 再叫 LLM 忽略，則會造成跨租戶機密外洩。正確做法是在向量與全文檢索階段就執行 Pre-filtering，例如在 PostgreSQL/pgvector 中加上 `WHERE (tenant_id = $1 OR tenant_id = 'global') AND acl_roles && $2::text[]`，確保進入 RRF 排名融合的候選集 100% 合法，並可為 `(tenant_id, acl_roles)` 建立帶 `btree_gin` 的 GIN 複合索引，搭配查詢計畫與壓測驗證是否達標 `50 ms` 目標。
3. **解答**：持久化 `AgentSessionState` 時，必須把已完成的 `tool_use` 與對應 `tool_result` 成對寫入 `messages_json`，並以帶狀態條件的 `version` 樂觀鎖 CAS 確保只有一個喚醒 Worker 能推進狀態。喚醒續跑時，將這份完整的 `messages_json` 作為新一次 Messages API 請求的歷史上下文，模型會看到工具已經執行完畢並取得結果，有助於接續推理；但不得依賴模型自行避免重複呼叫，寫入型工具在呼叫前仍應先在同一交易寫入可恢復的操作紀錄，並使用綁定業務操作、跨推理重試穩定的 idempotency key（例如 `{tenant_id}:{ticket_id}:refund:{operation_id}`）搭配下游冪等或對帳機制，即使發生崩潰或跨節點重試也不會重複退款。

## 延伸閱讀

- PostgreSQL Row-Level Security（RLS）與 WAL 官方文件：多租戶資料列隔離與檢查點恢復的資料庫層實作參考。
- Reciprocal Rank Fusion（RRF）：Hybrid Search 結合 BM25 與密集向量、只需單一平滑常數 `k`（常用 `60`）且無須分數正規化的排名融合方法。
- 本書第 6 章（ch06）：進一步探討跨節點分散式重試、Transactional Outbox 與 HITL 長任務暫停／喚醒狀態機，以及多租戶配額隔離。
