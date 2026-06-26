# 維護手冊（內部文件，非書籍內容）

《機制之下——後端與分散式系統如何運作、為何如此》（id `mech`）的維護基準。改任何時效性事實前先讀這份；改完在文末掃描日誌記一行。

## 本書性質與掃描重點

- **深讀版敘事技術書**，對象一般資深後端工程師。139 章＋2 附錄、8 個 Part（A–V 領域；見 outline）。姊妹書 `rsys`（速查版）並存——兩書同主題、不同形態，**不互相指向**。
- **四條改版紅線**（掃描必確認 0）：① 沒有任何個人/特定公司系統（NeoBards/LetsTalk/Bahwan）；② 沒有「你以為 vs 實際」居高臨下糾錯口吻（純機制天真假設的揭露可留）；③ 沒有指向任何其他書（含 `rsys`、作者他書）；④ 沒有練習段。外部第三方書/論文引用（《Refactoring》《Release It!》等）＝允許、加分。
- 內容多為「機制與取捨」（低腐蝕），但夾帶時效性事實（版本/授權/狀態/預設值），最易老化，集中在下面脆弱事實清單與 `landscape-2026-06.md`。
- **結構**：與 `rsys` 不同，本書**無固定六段骨架**。每章是有機敘事（開場張力→把問題講難→機制講透→取捨與故障織進敘事→收在「為何是這形狀」），唯一固定段是章尾 `## 延伸閱讀`（外部一手連結）。深度標竿＝〈共識〉章（consensus.md）。

## 跨章一致性基準

- **術語**：照 style-guide「術語對照表」（partition＝分區、shard＝分片、queue＝佇列、cache＝快取、thread＝執行緒…）。簡繁同形字（們/效/系/准/值/程）用 Python 逐字元比對、別用 shell grep 誤報。
- **交付語意基準**（多章引用，須一致）：SQS Standard＝at-least-once、SQS FIFO＝exactly-once（限流量上限內）、Redis Pub/Sub＝at-most-once、Redis Streams＝可重放、K8s CronJob＝非 exactly-once、Kafka EOS＝只在 Kafka 邊界內。
- **owning 章**（同一機制只在 owning 章深講一次，別章「（見〈章名〉）」帶過）：見 outline.md「owning 章」表。改機制描述只動 owning 章；引用處用章標題（短名）、不寫死檔名/章號。
- **worked example 數字是各章自帶的示意設例**（非跨章共享基準），不必跨章同步；但同章內算術要自洽。

## 脆弱事實清單（高風險老化，逐項以官方來源複查；重大修正需兩個獨立來源）

**A 級（最易腐，每次掃描必查）**
1. SQS 單則上限 1 MiB（2025-08-04 起）；async invoke payload 1 MB（2025-10-24 起，sync 仍 6 MB）——〈sqs〉〈lambda〉。
2. Redis 授權三階段（BSD→SSPL/RSAL 2024→Redis 8 加回 AGPLv3 2025）、Valkey（LF fork、BSD）；版本寫 8.x／9.x 不綁小版本——〈redis-internals〉。`io-threads` 預設仍 1（關閉）。
3. Kafka：KRaft 自 4.0（2025）為唯一模式、移除 ZooKeeper；**KIP-848 自 4.0 broker 端 GA 並預設，但 consumer 仍須設 `group.protocol=consumer`、尚非真正預設**；`linger.ms` 預設 4.0 改 5 ms——〈kafka〉〈delivery-semantics〉〈batching-coalescing〉。
4. SNS 單則上限仍 **256 KiB**（未隨 SQS 升到 1 MiB）——〈sns〉。
5. OAuth 2.1 在 2026-06 仍是 IETF draft（非 RFC）——〈oauth-oidc〉。
6. Lambda SnapStart 支援 runtime（Java/Python 3.12+/.NET 8+ GA；Node/Ruby/container 不支援）——〈lambda〉〈cold-start〉。
7. AWS API Gateway REST 帳號層預設 10,000 RPS steady／5,000 burst（部分新 Region 約 2,500/1,250）——〈api-gateway-role〉。
8. 工具現況：Clinic.js 已停止積極維護、k6（Grafana、AGPLv3）、Vegeta、Snyk 定價、Fluent Bit v5——〈quality-tooling〉。
9. BullMQ（Taskforce.sh 維護、非 Redis 所屬）、Bull 已停更——〈bullmq〉。
10. Let's Encrypt 90 天；公開 CA 效期上限 200 天（2026-03 起）——〈tls-mtls〉〈token-lifecycle〉相關。
11. **OWASP Top 10：Broken Access Control 自 2021 起連兩版（2021、2025）居第一**；「94%」是測試覆蓋率非缺陷率（平均發生率 3.81%）——〈authn-authz〉。
12. WebTransport baseline＝2026-03 Safari 26.4（Apple 2025 改年份制）——〈sse-webtransport〉。

**B 級（預設值/數量級，中風險）**
13. PostgreSQL `deadlock_timeout` 1s、MySQL `innodb_lock_wait_timeout` 50s；PG RR＝snapshot isolation（不防 write-skew）、MySQL RR＝next-key lock 防 phantom——〈locks-deadlock〉〈isolation-levels〉〈postgres-vs-mysql〉。
14. DynamoDB 單 partition 約 3,000 RCU/s、1,000 WCU/s、split-for-heat——〈sharding〉。TTL 刪除「數日內」——〈data-lifecycle〉。
15. Node active LTS（2026-06＝Node 24 Krypton）、UV_THREADPOOL_SIZE 預設 4——〈event-loop〉〈thread-pool〉。

**C 級（歸屬/年份，低腐蝕，驗一次即可）**
16. CAP＝Brewer／Gilbert-Lynch（2002）；PACELC＝Abadi（2010 blog／2012 IEEE）——〈guarantee-models〉。
17. Raft＝Ongaro-Ousterhout（2014）、Leader Completeness；Paxos＝Lamport（1998）；FLP＝Fischer-Lynch-Paterson（1985）；VR＝Oki & Liskov（1988）；BFT n≥3m+1＝Lamport-Shostak-Pease（1982）——〈consensus〉〈partial-failure〉。
18. BFF 命名＝SoundCloud 的 Phil Calçado（約 2013），Sam Newman 推廣——〈api-gateway-role〉。
19. 3PC＝Skeen（1981）；Dynamo＝DeCandia 等（SOSP 2007）；consistent hashing＝Karger 等——〈two-phase-commit〉〈replication-strategies〉〈consistent-hashing〉。

## lint 注意

`全量`（資料同步「全量同步/全量快照」、觀測「全量留存」對照增量/取樣語境）是**已裁定保留的 WARN 偽報**（沿用 `rsys`）——逐處複查確認是該語境即保留，勿盲改成「全面上線」。其餘大陸詞（概率/當且僅當/算法/灰度/流水線）一律改（見掃描日誌）。簡繁同形字用 Python 逐字元比對。

## 掃描協定（「掃描書的時效性」＝執行這套，工具路徑從本 book 根算）

1. **紅線 grep**（必 0）：`NeoBards|LetsTalk|Bahwan`、糾錯口吻（`老兵|記憶會過時`）、練習（`## 自我檢核|## 練習|## 動手做|紙上推演`）、**作者其他書名**（《保證與取捨》《名詞底下》《等待的數學》《正常意外》等——注意別誤抓外部第三方書）、編輯註記（`待回填|本任務`）、tool-call 殘留（`</?(content|invoke|parameter|antml)`）。
2. **lint**：`python3 ../../../tools/md-reader/lint_book.py book-src`（0 error；`全量` WARN 已裁定保留）。
3. **圖**：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（0 suspicious；ASCII box CJK=2）。
4. **事實**：對脆弱事實清單逐項 WebSearch（反駁框架）；A 級每次必查、B/C 級抽查。修正後更新對應章＋若動 landscape 基準同步 landscape-2026-06.md＋記掃描日誌。
5. **打包**：`build_shelf.py`（書架有變動先跑）→ `build_reader.py web/book.config.json`；render check 抽一張 CJK box 圖（headless Chrome）＋請作者在實際瀏覽器確認一張。

## 掃描日誌

- **2026-06-22（建書 P1–P5）**：由 `rsys`（速查版）的 ~150 主題衍生、重寫成 139 章深讀敘事書＋2 附錄。P2 Workflow 平行寫章（140 agent、~15M token）；P3 機械（lint 0 error＋12 `全量` 保留 WARN、check_diagrams 0、紅線 0；book-wide 修 概率/當且僅當/算法/灰度/流水線、webrtc 信令圖改無 rail 版）；P4 兩串審查＋收斂——Claude 逐章審 138/139（dual-write content-filter）、agy 跨家族 87/139（o–z 因 content-filter 回空、那半部只有 Claude 審）；consolidated fix workflow 套用 **68 must＋172 should＋151 nit、駁回/跳過 324**（verify-before-apply）。重點修正：BFF 命名歸 Phil Calçado（非 Sam Newman）、OWASP「94%」是測試覆蓋率非缺陷率＋BAC 2021/2025 連兩版第一、batching `cache penetration`→`cache breakdown/stampede`（與〈cache-failures〉一致）、Kafka KIP-848 consumer 端尚非預設、VR 補 Oki-Liskov 1988、SNS 256 KiB、DynamoDB partition 上限、AWS WAF rate-rule 時間語意。fix 後 lint 0 error/check_diagrams 0/紅線 0。**待辦（可選）**：對 agy 回空的 o–z ~52 章重跑 agy 補跨家族第二意見；round-2 全書複審；瀏覽器 render check。
