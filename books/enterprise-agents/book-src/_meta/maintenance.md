# 維護與一致性手冊（Maintenance）— 企業級 Agent 工程

## 1. 跨章一致性基準表（Base-Numbers Table — Byte-Identical to `outline.md`）

> 修改任何基準數值時，**必須先改 `_meta/outline.md`**，再同步重新生成 `_meta/running-examples.md` 與本表，並更新所有引用章節。

| 基準項目 | 數值 | 單位 | 所屬概念 | 引用章節 |
|---|---|---|---|---|
| OrderOps 日工單量 | 50,000 | 筆／天（1,500,000 筆／月，以 30 天計） | 主軸工作負載 | ch01, ch06, ch08, ch10, ch11 |
| OrderOps 尖峰流量 | 12 | req/s（平均 0.58 req/s，尖峰 20×） | 吞吐與限流設計 | ch01, ch06, ch08, ch10 |
| OrderOps 延遲 SLO | 2.5 / 18 | 秒（分流 p95 ≤ 2.5s；多步工具處置 p95 ≤ 18s） | 延遲預算 | ch01, ch08, ch10, ch12 |
| OrderOps 工具總數 | 18 | 個工具（12 唯讀 Read-only + 6 寫入／金流 Mutating） | 工具面與權限切分 | ch02, ch05, ch08, ch09, ch11 |
| OrderOps 基準前綴大小 | 6,000 | tokens（System Prompt 2,400 + 18 工具 Schema 3,600） | Context 與快取基準 | ch02, ch03, ch08 |
| OrderOps 基準回合與輸出 | 5 / 1,200 / 350 | 回合 / 每回合新增輸入 tokens / 每回合輸出 tokens | 單筆基準消耗 | ch01, ch03, ch08 |
| OrderOps 未優化單筆消耗 | 42,000 / 1,750 | 累計輸入 tokens / 累計輸出 tokens（5 回合加總） | 成本基準 | ch01, ch08 |
| OrderOps 未優化基準成本 | $0.1015 / $5,075 / $152,250 | 單筆 / 每日 / 每月（全用 Sonnet 5.5、無快取） | 單位經濟學基準 | ch01, ch08, ch10, ch12 |
| Claude Haiku 5.5 牌價（≤100K） | $0.10 / $0.50 | USD / MTok（Input / Output；>100K 為 $0.50 / $2.50） | 模型分層計價 | ch01, ch05, ch08, ch09 |
| Claude Sonnet 5.5 牌價 | $2.00 / $10.00 | USD / MTok（Input / Output） | 預設工作層計價 | ch01, ch03, ch08, ch11 |
| Claude Opus 5.5 牌價 | $4.00 / $20.00 | USD / MTok（Input / Output） | 高風險仲裁層計價 | ch03, ch05, ch08, ch11 |
| Prompt Caching 寫入倍率 | 1.25× / 2.0× | 基礎輸入單價（5m TTL / 1h TTL） | 快取寫入成本 | ch03, ch08 |
| Prompt Caching 讀取倍率 | 0.05× / 0.10× | 基礎輸入單價（Sonnet/Opus 5.5 為 0.05×；Haiku 5.5 為 0.10×） | 快取命中折扣 | ch03, ch08 |
| Batch API 折扣 | 50% | Input 與 Output 同步半價（Sonnet 5.5 為 $1.00 / $5.00） | 非同步批次降本 | ch06, ch08, ch11 |
| 資料駐留附加倍率 | 1.1× | 啟用 `inference_geo: "us"` 全類別 token 費率倍率 | 法遵成本權衡 | ch08, ch09, ch12 |
| OrderOps 目標優化月成本 | ≤ $18,000 | USD / 月（降幅 ≥ 88%，單筆 ≤ $0.012） | 優化工程目標 | ch08, ch10, ch12 |

## 2. 已知脆弱事實清單（Fragile-Facts Index — from `landscape-2026-11.md`）

| 項目 | 2026-11 基準值 | 受影響章節 | 備註 |
|---|---|---|---|
| Claude 5.5 模型 ID 與牌價 | Haiku 5.5 `$0.10/$0.50`、Sonnet 5.5 `$2.00/$10.00`、Opus 5.5 `$4.00/$20.00` | ch01, ch03, ch05, ch08, ch09, ch11 | `⚠️` 每次新模型發布或調價須同步重算 `OrderOps` 帳本 |
| Prompt Caching 最小前綴門檻與讀取倍率 | 512 / 1,024 / 4,096 tokens；讀取 0.05× / 0.10× | ch03, ch08 | `⚠️` 依各模型官方文件定期複核 |
| 官方 SDK 最新穩定版 | `@anthropic-ai/sdk` v1.10.0；`anthropic` v2.11.0；Claude Agent SDK | ch01, ch02, ch05, ch12, examples/ | `⚠️` 升級主版本時須重驗 `examples/ts` 與 `examples/py` |
| MCP Streamable HTTP & Connector 規格 | Streamable HTTP 取代 HTTP+SSE；Stateless HTTP；`mcp_servers` Connector | ch02, ch11 | `⚠️` 追蹤 `modelcontextprotocol.io` 與 Anthropic beta 標頭演進 |
| Context Window 與 `inference_geo` 倍率 | 最高 1M tokens；`inference_geo: "us"` 1.1× | ch03, ch08, ch09, ch12 | `⚠️` 費率與區域支援可能調整 |

## 3. 時效性掃描協定（Scan Protocol）

執行時效性掃描（「掃描書的時效性」）時依序執行：
1. 針對第 2 節每一筆 `⚠️` 脆弱事實，以官方文件與套件庫（`claude.com`、npm、PyPI、`modelcontextprotocol.io`）重新查證；重大變動須兩個獨立來源確認。
2. 若任何基準數字變動：先更新 `_meta/outline.md` 基準表 → 逐字同步 `_meta/running-examples.md` 與本檔第 1 節 → 同步更新所有引用章節與 `examples/ts/shared/types.ts`、`examples/py/shared/types.py`。
3. 重跑 Tier-1 檢查：
   ```bash
   python3 tools/md-reader/gate_book.py books/enterprise-agents/book-src --lang zh-TW --config books/enterprise-agents/book-src/_meta/lint.config.json
   python3 tools/md-reader/check_diagrams.py books/enterprise-agents/book-src
   ```
4. 若改動載重算式或架構機制，重跑 `verify_book.py --writer-family google --no-cache --chapters <touched>`；重新打包書架與閱讀器。
5. 於下方掃描日誌新增一行紀錄。

## 4. 橋接登記鎖（Bridge Registry Lock）

| 章節 | 階段 | 鎖定橋接來源 |
|---|---|---|
| ch01 | 前段 | 有限狀態機與事件迴圈（FSM + Event Loop） |
| ch02 | 前段 | 微服務 RPC 契約與冪等鍵（OpenAPI + Idempotency Key） |
| ch03 | 前段 | CPU 快取局部性與虛擬記憶體分頁（Cache Prefix + Paging） |
| ch04 | 前段 | 資料庫預寫日誌與列級權限（WAL Checkpoint + Row-Level Security） |
| ch05 | 中段 | 分散式 Saga 編排與補償（Orchestrated Saga） |
| ch06 | 中段 | 熔斷器與 Transactional Outbox 模式 |
| ch07 | 中段 | CI 回歸測試套件與契約斷言（Regression Suite） |
| ch08 | 中段 | 雲端 FinOps 單位成本與 CDN 快取命中率 |
| ch09–ch12 | 後段 | `none`（原生詞彙） |

## 5. 掃描與建置日誌（Scan Log）

- `2026-11-22` | `full`（初版建置）| ch01–ch12（12 章＋附錄 A＋TS/Python 雙語言完整範例）| P2（`gemini-4-hydrogen-low` + self-review + `codex gpt-6.2-sol low` review）、P3（0 errors / 0 warnings / 0 diagram findings / 14 Python 檔編譯通過）、P4（2 輪跨模型裁決 + 5 筆單家 OpenAI `incorrect` 終修、Bridging 12/12 通過、餘下 `imprecise` 經使用者確認豁免）、P4.5（Teach-test 12/12 通過）、P5 打包與無頭瀏覽器驗證完成。
