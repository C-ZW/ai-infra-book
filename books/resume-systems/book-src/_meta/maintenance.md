# 維護手冊（內部文件，非書籍內容）

《保證與取捨——後端與分散式系統的概念地圖》的維護基準。改任何時效性事實前，先讀這份；改完在文末掃描日誌記一行。

## 本書性質與掃描重點

- 通用概念參考書，**對象是一般資深工程師**（非特定作者）。掃描時優先確認：**沒有任何個人/特定公司系統洩漏**、**沒有「我以為 vs 實際」糾錯口吻**、**沒有指向其他書**、**沒有練習段**（這四項是改版紅線，見 style-guide「明確禁止」）。
- 內容多為「機制與取捨」（低腐蝕），但夾帶一批**時效性事實**（版本/授權/產品狀態/預設值），這是最易老化的部分，集中列在下面脆弱事實清單。
- 結構鐵律：每個 `##` 概念底下恰好六個 `###`（問題型：定義與原理/解法空間/各方案的保證與取捨/何時需要/常見誤解與陷阱/延伸閱讀；工具型：是什麼與內部機制/在哪些系統扮演什麼角色/保證與限制/跟替代品的取捨/常見誤解與陷阱/延伸閱讀）。標題逐字、不加括號註解。

## 跨檔一致性基準

- **術語**：照 style-guide「主要術語對照表」（partition＝分區、shard＝分片、queue＝佇列、cache＝快取…）。簡繁同形字（們/效/系/准/值）用 Python 逐字元比對、別用 shell grep 誤報。
- **交付語意基準**（多檔引用，須一致）：SQS Standard＝at-least-once、SQS FIFO＝exactly-once（限流量上限內）、Redis Pub/Sub＝at-most-once（無持久化）、Redis Streams＝可重放、K8s CronJob＝非 exactly-once。改任一處要全書一致。
- **owning 條目表**（同一主題機制只在 owning 條目深講一次，別處用「（見 X，領域 Y）」帶過）：見 outline.md「跨領域去重」表。改機制描述時只動 owning 條目，引用處不必同步機制、但若 owning 條目改名要更新引用。
- **worked-example 數字是各條目自帶的示意設例**（標「假設/約/示意」），**非跨檔共享基準**，不必跨檔同步；但同一條目內的算術要自洽（掃描時用算術健全性檢查）。

## 脆弱事實清單（高風險老化，逐項標了所在領域）

時效性事實（標 `（2026-06）`），逐項以官方來源複查；重大修正（推翻基準）需**兩個獨立來源**。

**A 級——版本/授權/產品狀態（最易腐，每次掃描必查）**
1. SQS 單則 payload 上限 **1 MiB（自 2025-08-04）**——A3、A2（DLQ 保留期 14 天上限亦在此）。
2. Bull 已停更、現役 **BullMQ**，維護方 Taskforce.sh（非 Redis 官方）——A3。
3. Redis 授權三階段：BSD → SSPL/RSAL（2024）→ Redis 8 加回 AGPLv3（2025）；**Valkey** 為 Linux Foundation fork——G。版本號（Redis 8.x、Valkey 9.x）寫「8.x／9.x」不綁小版本。
4. Redis 驅逐政策數量與名稱（含 volatile-lrm / allkeys-lrm，約 10 種 maxmemory-policy）——G。
5. **OAuth 2.1 在 2026-06 仍是 IETF draft**（非 RFC）——F。
6. AWS Lambda **SnapStart 支援的 runtime**（Java 支援；Node.js 現況須查）——J、S（冷啟動）。
7. AWS API Gateway REST API 帳戶層預設 **10,000 RPS steady-state / 5,000 burst**——H。
8. 觀測/品質工具現況：Clinic.js 維護狀態、k6（Grafana，2.0）、Vegeta 版本、Snyk 定價（$25/dev/月＋credit model 變動）——I2。
9. 12-factor 現況（官方/Google 正在為容器・AI 時代改版，別當凍結標準）——Q。
10. Temporal 現況（由 Cadence 原班人馬創立、持續活躍；版本/fork 年份不綁死）——K。
11. Let's Encrypt 憑證效期 **90 天**——N。
12. DynamoDB TTL 刪除延遲（約 48 小時內，敘述保守）——O。

**B 級——預設值/數量級（中風險）**
13. PostgreSQL `deadlock_timeout` 1s、MySQL `innodb_lock_wait_timeout` 50s——B1。
14. PostgreSQL REPEATABLE READ＝snapshot isolation（不防 write-skew）、MySQL RR 比 SI 弱（Jepsen）——B1。
15. PostgreSQL 18 skip scan 對最左前綴的鬆綁條件——B1。
16. runc 預設 seccomp 封掉的 syscall 數（約 44，敘述用「約」）、Node V8 old-space heap 預設上限（約 2 GB，依版本/平台）——Q。
17. TrueTime ε（典型約數毫秒、commit-wait 約 2ε）——M2。

**C 級——歸屬與年份（低腐蝕，驗一次即可）**
18. CAP＝Brewer 提出／Gilbert-Lynch 證明；PACELC＝Abadi——B2。
19. Raft＝Ongaro-Ousterhout（2014）；Paxos＝Lamport；FLP＝Fischer-Lynch-Paterson（1985）；2PC 阻塞性＝Skeen——M1。
20. Actor model＝Hewitt（1973）——D；consistent hashing＝Karger 等、jump hash＝Lamping-Veach——M2。
21. RFC：HTTP semantics 9110、WebSocket 6455、HTTP/3 9114、QUIC 9000——A1/C/N。Idempotency-Key 仍是 IETF draft——A1。

## 延伸閱讀連結

各條目「延伸閱讀」放外部真實連結。部分連結（論文 PDF 鏡像、blog 永久連結）寫入時未逐一 WebFetch 驗活，標為穩定權威網域；下次大掃描時抽樣 fetch 確認可達，失效者改用 DOI 或官方鏡像。**不得指向作者的其他書。**

## 掃描協定（「掃描書的時效性」＝執行這套）

1. **紅線 grep**（必 0）：個人系統/糾錯/練習/他書（`NeoBards|LetsTalk|Bahwan`、糾錯口吻、`## 自我檢核`、書名號 `《》`）＋編輯註記（`待回填|本任務`）＋tool-call 殘留（`</?(content|invoke|parameter|antml)`）。
2. **結構驗證**：每個 `##` 恰六個 canonical `###`（strip code fence → 比對六標題集合）。
3. **lint**：`python3 ../../../tools/md-reader/lint_book.py book-src`（0 error；全量這字在資料同步語境是已裁定保留的 WARN 偽報）。
4. **圖**：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（0 suspicious）。
5. **事實**：對脆弱事實清單逐項 WebSearch（反駁框架，找它是否已過時）；A 級每次必查、B/C 級抽查。修正後：更新對應條目 → 若動到 landscape 基準同步 landscape-2026-06.md → 文末記掃描日誌一行。
6. **打包**：`build_reader.py web/book.config.json` → `build_shelf.py`；render check 抽一張 CJK box 圖。

## 掃描日誌

- **2026-06-21**：本書由舊個人書《名詞底下》就地重寫為通用概念書《保證與取捨》。27 領域檔（~150 條目）以平行 agent 產出；P3 結構/lint/圖全綠（per-entry 六段 0 偏離、lint 0 error＋2 個已裁定保留的「全量」WARN、check_diagrams 0 suspicious）；舊 chNN 移至 `_archive-personal-book/`。P4 跨 27 檔反駁框架事實查證（490 條事實確認）：套用 18 項事實修正＋6 項算術修正。重點——InnoDB 預設自 MySQL 5.5（非 8.0，唯一 high）、KrakenD 被 Shop Circle 收購為 2025-09（非 08）、DORA 第四指標更名於 2023（非 2024）、3PC 出處 Skeen 1981、IANA tz 去釘版（如 2026b）、Vegeta v12.13.0、RocksDB 11.0.x、Debezium/BullMQ 版本去釘、Avro 1.12、Go 1.25 GOMAXPROCS 轉 cgroup-aware、RFC 8656 與 Kleppmann/SRE-Book Ch.6 連結修正；算術——M2 Redlock（⌊N/2⌋+1）與 consistent-hashing 公式、M1 捨入、J 誤判率（250 ms≈1%／900 ms≈0.1%）、H 聚合往返數、E GiB 捨入。
- **2026-06-21（逐章三重審）**：Claude 逐章 holistic 審（27 agent，concept/math/fact/structure/voice/clarity）＋ agy 逐章跨家族審（Gemini Flash High，逐項展示核對）＋ 15 條 web 爭點獨立複查。套用 **32 項修正**。重點事實——SQS FIFO 70k 是**非批次**數字、FIFO 預設 300/3,000 是**整佇列共用**非 per-group（per-group 需開 high-throughput mode）；K8s CronJob 漏跑只補**一個** Job、不批量回填；TCP+TLS 1.3 新連線＝**2-RTT**（非 1）；JS Temporal 預定納入 **ES2027**（非 2026）；DORA 第四指標更名於 **2023**、且 2024 重組分組；公開 CA 效期上限 **200 天**（2026-03 起，LE 自採 90）；Node 12+ V8 **container-aware**（old-space≈cgroup 上限一半）；Debezium **3.5.x**；DynamoDB TTL「數日內」非 48 小時；Redis io-threads **預設不卸載讀路徑**；OIDC ID Token 非「一律」非對稱（持 client_secret 可 HS256）；coordinated omission 由 Gil Tene **約 2013** 提出。概念——D 多核切塊≠SIMD、A2 Protobuf 範例改號自洽、MySQL SERIALIZABLE 用 FOR SHARE＋限 autocommit off。算術——G single-flight（20ms 窗內約 100 非 4,999）、G LRU 掃描需容量<鍵數、M1 99.28%、N L4 失衡 800 QPS。**verify-before-apply 擋下 2 個審稿偽陽**：Redis 8.6 LRM/10 策略與 Fluent Bit v4.2 EOL **書本正確、未改**。agy 對 L（及首輪 A3/I2）content-filter 回空（工具限制、已由 Claude＋web 複查覆蓋）。C 另補：推送訊息算術（1,000 筆/2s＝500/s、「請求數」改「推送訊息數」）與 MASK 措辭（cache poisoning）。**verify-before-apply 第 3 次擋下偽陽**：agy 誤指「Safari 26.4 是穿越版本、WebTransport 應在 Safari 17.4（2024）」——web 查證 Apple 2025 改年份制（Safari 26＝2025-09）、且 WebTransport 確實到 **2026-03 Safari 26.4** 才支援（達 baseline），**書本正確、未改**。脆弱事實清單應加：WebTransport baseline＝2026-03 Safari 26.4（易腐）。
