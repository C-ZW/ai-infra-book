# 寫作風格指南（內部文件，非書籍內容）

本文件是全書的寫作契約。每一章都必須遵守，否則全書會失去一致性。

## 讀者是誰

唯一讀者：Chewei，6 年以上資深後端工程師（TypeScript/Node.js、NestJS）。經歷：

- 遊戲後端（Dynasty Warriors Mobile）：500K+ 使用者、10K+ CCU，高可用維運
- 效能工程實績：profiling-driven 優化讓 RDS CPU 尖峰降 40%（SQL 重排、交易拆分、鎖競爭、批次化）
- Event-driven 結算 pipeline：K8s CronJobs → SQS → idempotent consumers，每季 10 萬~30 萬筆獎勵發放、最終一致性
- 自建可觀測性 pipeline：FluentBit + Lua，從 production logs 萃取 API 指標到 S3
- 即時系統：WebSocket + Redis Pub/Sub 訊息 fan-out、多裝置同步、WebRTC signaling
- 雲端：AWS（EKS、ECS、Lambda、SQS、SNS、RDS、S3）、Docker、K8s（CronJobs）、KrakenD
- 負載測試：k6、Vegeta；資料庫：MySQL/PostgreSQL（read replica、partitioning、isolation level、deadlock、index tuning）、Redis

目標：轉職 AI Infrastructure / LLM Inference Engineer。設備：M1 MacBook Pro ＋ 按小時租用的雲端 GPU（RunPod/Lambda/Vast.ai）。

**不需要解釋**（讀者已精通）：HTTP/REST、load balancing、queue、cache 的概念、DB 索引/交易/鎖、K8s 基礎物件（Deployment/Service/HPA/CronJob）、Docker、CI/CD、idempotency、eventual consistency、backpressure、rate limiting、p50/p95/p99、SLO 的概念本身。

**要從零教**（讀者完全沒碰過）：GPU 硬體與 CUDA 生態、PyTorch、transformer 內部機制、所有 ML/LLM 術語、Python 與 Go 的生態細節。

## 語言規範

- 繁體中文，台灣慣用語。技術名詞一律保留英文原文，不硬翻（KV cache、continuous batching、prefill、tensor parallelism…第一次出現時用一句中文解釋它是什麼）。
- 台灣用語基準：記憶體（不是内存）、快取（不是缓存）、佇列、叢集、排程、吞吐量、延遲、執行緒、資料、網路、程式碼、函式、伺服器、容器、映像檔、部署、影片（不是视频）、最佳化／優化皆可。
- 禁止簡體中文詞彙與用法。
- 第二人稱「你」直接對讀者說話。

## 每章骨架（必須遵守，標題名稱照抄）

1. 章首：`# chNN — 章名：副標`，接著一個 blockquote：
   `> **本章解決什麼問題**：…（這章在整個系統裡的位置、為什麼重要、跟前後章的關係，3-5 行）`
2. `## 從你已知的出發` — 橋接段：把本章核心概念錨定在讀者的後端經驗上（例：PagedAttention 之於 GPU 記憶體 ≈ OS virtual memory paging；KV-aware routing ≈ session affinity + consistent hashing；preemption storm ≈ retry storm）。橋接要具體到讀者的實際經歷（遊戲後端、RDS 優化、SQS pipeline、k6），不要泛泛而談。
3. 核心內容（多個 `##` section，深入機制）
4. `## 故障模式與防禦` — 本書招牌段落：這個主題在生產環境會怎麼壞、壞了長什麼樣（症狀/指標）、怎麼觀測到、怎麼防。用表格或條列。
5. `## 動手做` — 實驗，每個實驗標注 **[M1]**（MacBook 可做）/ **[租 GPU]**（標估計成本）/ **[紙上推演]**（計算題）。給出具體步驟或指令骨架與「成功標準」。
6. （可選）`## 這個領域往哪走` — 該主題 1-3 年內的走向，簡短。
7. `## 自我檢核` — 5~8 個問題，答得出來才算過關。問題對齊真實面試會問的深度。
8. `## 延伸閱讀` — 真實連結（官方文件、論文、工程部落格），每條一句話說明為什麼值得讀。

## 深度標準

- **每章至少一個 worked example**：帶真實數字、一步步算的計算（記憶體、頻寬、吞吐、成本…）。
- 真實的 config / code snippet（以可運行為目標；若是示意要註明「示意」）。
- 每個工具都要回答「它在解什麼系統問題」，禁止只羅列工具名稱。
- 每個技術選擇都給決策框架：什麼時候用、什麼時候不用、代價是什麼。
- Murphy 原則：每個機制都要回答「它什麼時候會壞、壞了長什麼樣、怎麼觀測到」。
- 寧深勿廣，不灌水。每章 5,000~10,000 中文字，依主題深度調整。

## 事實正確性

- 2026 年的版本號、價格、專案狀態以 `_meta/landscape-2026.md` 為事實基準；本章特定的細節自行用 WebSearch/WebFetch 查證。
- 所有時效性數據（版本、規格、價格、專案狀態）標註時點，格式：`（2026-06）`。
- 無法查證的事實要 hedge：「截至我能確認的資訊（2026-06）…」。
- 延伸閱讀只放真實存在的連結；沒把握的標註「（未驗證）」。

## 格式

- Markdown。主要層級用 `##`，次層 `###`。
- 圖：簡單結構用 ASCII diagram，流程/架構可用 Mermaid。
- 程式碼區塊標語言。表格用於對照與決策框架。
- 跨章引用格式：`（見 ch07）`，不要寫死檔名路徑。

## 語氣

工程師對工程師。冷靜、直接、有觀點（可以寫「我認為」「業界共識是 X，但我持保留態度，因為…」）。不行銷、不喊口號、不堆形容詞。允許冷幽默，但內容密度優先。
