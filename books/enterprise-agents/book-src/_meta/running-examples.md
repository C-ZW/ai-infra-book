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
