---
last_verified: 2026-06-21
review_after_days: 120
purpose: 本書時效性事實基準。章節遇到版本/語意/狀態類事實以此檔為錨；查證後有修正先改這裡。
---

# 《機制之下》時效性事實基準（2026-06）

> 本檔沿用自姊妹書 `rsys`（《保證與取捨》），兩書共用同一份事實底；查證後有修正請同步兩邊（或註明僅本書）。

本檔逐項驗證書中倚賴的「會隨時間漂移」的技術事實。每節格式：**結論** → **來源** → 必要時加 ⚠️。
語意類（at-least-once、snapshot isolation 等）相對穩定；版本／價格／維護狀態／授權類最易腐，引用時務必標日期。

最關鍵的「老化事實」（履歷／作者很可能記成舊版的）集中在：Twilio Video 關閉論點已被官方撤回、Redis 改授權＋Valkey 分裂、Bull→BullMQ、Clinic.js 已停止積極維護、OAuth 2.1 仍是 draft、Prisma 7 已去 Rust、Fluent Bit 已到 v5。

---

## 1. Amazon SQS — 投遞語意與上限

**結論：** Standard queue 為 at-least-once delivery、可能 duplicates、best-effort ordering；FIFO queue 在 5 分鐘 deduplication window 內提供 exactly-once processing、strict ordering。Visibility timeout 預設 30s、最大 12h、最小 0s；DLQ 支援；message retention 預設 4 天、最小 60s、最大 14 天（1,209,600s）。FIFO 預設吞吐為每 partition 每秒 300 非批次／3,000 批次；high throughput mode 在主要 region 可達約 70,000 messages/s（批次，region-dependent）。

⚠️ **老化事實（需更正）：** SQS 單則訊息上限現為 **1 MiB（1,048,576 bytes）**，不是常被記得的 256 KB。**年份校正（2026-06-21，兩來源確認，原稿誤記 2022）**：256 KB 上限存在很久，AWS 於 **2025-08-04** 才把單則上限提升到 1 MiB（來源：AWS what's-new 公告＋多家同日第三方報導）。對讀者（2019–2024 在職）而言「256 KB」在當年是**正確**的，是世界 2025 才變——這是一個「記憶當年沒錯、世界後來變了」型的老化事實，不是「你一直記錯」。超過上限用 Extended Client Library 把 payload 放 S3、最大 **2 GB**。high throughput FIFO 的精確 TPS 隨 region 變動，引用時宜標「最高約 70,000 msg/s（批次，主要 region），region-dependent」而非單一全域數字。

**來源：**
- https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html
- https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html
- https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html

---

## 2. Amazon SNS — fan-out 與 FIFO

**結論：** SNS 的 fan-out（一個 topic 扇出多個訂閱端）為核心模式；**SNS→SQS fan-out 是標準推薦架構**。**SNS FIFO topics 確實存在**，提供 strict ordering 與 deduplication，可投遞到 SQS FIFO queue（保留 ordering / exactly-once），也可（2023-09 起）投遞到 SQS Standard queue（降級為 best-effort ordering / at-least-once 以省成本）。SNS FIFO 不能直接投遞給 email/SMS/HTTP(S)/mobile/Lambda，須先經 SQS。訂閱端不可用時 SNS 執行 delivery retry policy，並可搭 DLQ 保存最終未送達訊息。

**來源：**
- https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html
- https://aws.amazon.com/blogs/aws/introducing-amazon-sns-fifo-first-in-first-out-pub-sub-messaging/

---

## 3. Redis Pub/Sub vs Streams 語意

**結論：** Redis Pub/Sub 是 fire-and-forget、at-most-once、無持久化：訊息只送給「發佈當下正連線」的 subscriber，離線者永久錯過、無 replay、無 consumer tracking。Redis Streams 相反——訊息持久化為 append-only log，透過 consumer group（`XREADGROUP`）達 at-least-once，需 `XACK` 明確確認；未確認訊息留在 Pending Entries List，consumer crash 後可重讀或被他人接手。

**來源：**
- https://redis.io/docs/latest/develop/use-cases/streaming/
- https://redis.io/docs/latest/commands/xreadgroup/

---

## 3b. Redis 授權演進與 Valkey 分裂（load-bearing 老化事實）

**結論：** 授權演進：Redis 2024-03 從 BSD-3-Clause 改為雙授權 SSPLv1 / RSALv2；2025-05 在 **Redis 8** 加入 **AGPLv3**，成為三授權（tri-license：RSALv2 或 SSPLv1 或 AGPLv3，三選一），其中只有 AGPLv3 是 OSI 認可的開源授權。產品名自 8.0 起為「Redis Open Source」，RediSearch/RedisJSON 等模組已併入核心並同受三授權。**當前 Redis 已是 8.x**（最新穩定版約 8.8.0，2026-05-25；另有 8.6.x／8.4.x／8.2.x 維護分支），**不是 7.x**。

Valkey fork：由 Linux Foundation 主導、2024 自 **Redis 7.2.4** fork、採 BSD-3-Clause。當前狀態：9.0 GA 於 2025-10-21，**最新穩定版 9.1.0（2026-05-19）**；採每年一個大版本節奏。主要 Linux distro（Fedora、Debian、Ubuntu、Arch、openSUSE 等）與雲端（AWS ElastiCache、Google Memorystore for Valkey 9.0 GA）已普遍轉向 Valkey。

⚠️ **引用注意：** 書若仍寫「Redis 是 BSD / 仍在 7.x」即過時。distro 的「精確版本號」（Fedora 42／Ubuntu 26.04／Debian 13 等）與部分廠商效能宣稱（「快 8%／省 20%／已遷數百萬節點」）多來自部落格而非官方逐一證實，引用時宜以「主要 distro 與雲端已普遍轉向 Valkey」概括，避免綁死單一版本號。

**來源：**
- https://redis.io/legal/licenses/
- https://redis.io/blog/agplv3/
- https://github.com/redis/redis/releases
- https://github.com/valkey-io/valkey/releases
- https://valkey.io/blog/introducing-valkey-9/

---

## 4. Redis internals — 單執行緒、I/O threads、持久化、驅逐

**結論：** 指令**執行仍為單執行緒**（單一 main thread、原子性）。Redis 6.0+ 加入 threaded I/O（把網路 read/parse 與寫回 response 卸載到多執行緒），但**指令執行本身永遠不平行**。Redis 8 重寫了 I/O threading 實作、效能顯著提升（並用 AVX2/AVX-512 SIMD 加速 CRC64 等）。持久化：RDB（point-in-time 快照）vs AOF（append-only log，含 fsync 策略 always／everysec／no）。驅逐策略：`noeviction`（預設）、allkeys-lru、allkeys-lfu、volatile-lru、volatile-lfu、volatile-ttl、allkeys-random、volatile-random（八種核心）；**Redis 8.6 起再加 `volatile-lrm`／`allkeys-lrm`（Least Recently Modified，以改寫而非讀取為準），8.6+ 共十種**（來源 https://redis.io/docs/latest/develop/whats-new/8-6/）。

⚠️ **易錯 nuance：** 即使在 Redis 8，`io-threads` **預設仍為 1（等於關閉）**，須手動設為 4–8 才生效（`io-threads-do-reads` 預設 off）。書中若稱「Redis 8 預設開啟 I/O threading」是錯的——應寫「Redis 8 強化了 I/O threading 能力，但仍需手動啟用」。

**來源：**
- https://redis.io/blog/redis-8-ga/
- https://redis.io/blog/redis-8-0-m03-is-out-even-more-performance-new-features/

---

## 5. WebRTC — 標準狀態 / ICE-STUN-TURN / SDP / SFU-MCU-mesh / JVB

**結論：** WebRTC 1.0 自 2021-01-26 成為 W3C Recommendation，至今仍是現行標準；W3C 後續以 amended Recommendation 重新發布（最新版日期 2025-03-13），故標準持續有效、未被取代。ICE 是 NAT 穿透的整體框架（蒐集 candidate、配對連通性）；STUN 發現自己經 NAT 映射後的 public IP/port；TURN 在直連失敗時作 relay 中繼。SDP offer/answer 為協商媒體能力的標準機制。拓樸三分法：mesh = P2P N×N、不可擴展；MCU = server 混流成單一 stream、CPU 重；SFU = server 選擇性轉發/路由各 stream、擴展性最佳。**Jitsi Videobridge（JVB）確實是 SFU**（官方 repo 自稱「WebRTC compatible video router or SFU」）。

⚠️ **完整性提醒：** 若只寫「2021 W3C Recommendation」不算錯但不完整，可補「2025-03-13 amended Recommendation 仍為現行」。

**來源：**
- https://www.w3.org/press-releases/2021/webrtc-rec/
- https://www.w3.org/TR/webrtc/
- https://github.com/jitsi/jitsi-videobridge

---

## 6. Jitsi / Twilio Video / Agora（履歷前提需修正的最關鍵老化事實）

**結論（Jitsi）：** 8x8 於 2018-10 自 Atlassian 收購 Jitsi，2026 仍由 8x8 維護，採 Apache 2.0。JVB 為現役活躍維護——`master` 最新 commit 至 2026-06（如改用 Jackson、Java 21 支援）。

⚠️ **結論（Twilio Programmable Video）— 履歷假設已過時：** Twilio 最早在 **2023-12** 首次宣告 Programmable Video EOL（原訂約 2024-12 關閉）、2024-03 更新把 EOL 延到 **2026-12-05**，但於 **2024-10-21 公開撤回**，官方原文：「we've reversed our earlier decision to retire Twilio Video in 2026」「Twilio Video will remain a standalone product」。故 2026-06 現況是 Twilio Video **未關閉、仍是現役產品**。履歷／書中若寫「因 Twilio 即將關閉而選 Jitsi」**論點已不成立**，應改為純成本／自架掌控／開源授權角度（Jitsi 開源可自架、零授權費 vs Twilio/Agora 商用按量計費）。

**結論（Agora）：** 仍為活躍商用 WebRTC/RTE 平台，2026 持續更新（Web SDK v4.24.x，release notes 有 2026-02 更新）。作為商用替代方案定位成立。

⚠️ **陷阱：** jitsi-videobridge 的 GitHub Releases 頁面最後一個 tagged release 停在 2024-06，僅憑 release 頁會誤判已停更；實際活躍度須看 commits。任何用 release tag 判斷「是否停更」的敘述都會誤判。

**來源：**
- https://www.twilio.com/en-us/changelog/-twilio-video-will-remain-a-standalone-product
- https://github.com/jitsi/jitsi-videobridge/commits/master
- https://github.com/jitsi/jitsi-meet/blob/master/LICENSE
- https://docs.agora.io/en/video-calling/overview/release-notes

---

## 7. TURN/STUN — coturn 與 RFC 編號

**結論：** RFC 編號（以 IETF datatracker 為準）：STUN 原 **RFC 5389**，已被 **RFC 8489** obsolete；TURN 原 **RFC 5766**，已被 **RFC 8656** obsolete；ICE 原 **RFC 5245**，已被 **RFC 8445** obsolete。coturn 為事實上的開源 TURN/STUN server。TURN 在 STUN 失敗時改走 relay 的原因：**symmetric NAT** 的映射是依目的地而異（destination-specific），故對 STUN server 探到的 public mapping 對真正對端 peer 不適用、candidate 連不通，只能退而經 TURN server 中繼。

**來源：**
- https://www.rfc-editor.org/rfc/rfc8489.html
- https://datatracker.ietf.org/doc/rfc5766/
- https://www.rfc-editor.org/info/rfc8445/

---

## 8. coturn — 維護狀態與版本

**結論：** coturn（github.com/coturn/coturn）2026 仍活躍維護；最新版約 **4.13.1（2026-06-15）**，近期版本含安全修補與 Linux UDP fast path（recvmmsg、UDP-GSO）等。

⚠️ **易腐：** 版本號高頻變動，引用時建議標日期、視為易腐事實。

**來源：**
- https://github.com/coturn/coturn/releases

---

## 9. Fluent Bit — 版本、Lua filter、vs Fluentd、S3 輸出

**結論：** Fluent Bit 在 2026-06 已進入 **v5.0** 系列（最新約 v5.0.7，2026-06-05）；v4.2 系列仍維護（v4.2.5）但支援於 2026-06-30 結束。**Lua scripting filter（config 名 `lua`）確認仍受支援、無棄用標記**，並在 v4.0.4+ 加入 OpenTelemetry metadata-aware callback 等新功能。Fluent Bit 為 C 撰寫的輕量代理；Fluentd 為 Ruby 核心＋gem plugin 生態；**兩者皆為 CNCF graduated**。典型 pipeline：input → parser → filter → output；輸出至 Amazon S3 用 `out_s3` plugin。

⚠️ **老化事實：** 書中若寫「Fluent Bit v3.x／v4.x」需更新為「2026 已達 v5（v5.0.x），v4.2 維護至 2026-06-30」。Lua filter 確定未棄用。

**來源：**
- https://fluentbit.io/announcements/
- https://docs.fluentbit.io/manual/data-pipeline/filters/lua
- https://docs.fluentbit.io/manual/about/fluentd-and-fluent-bit

---

## 10. Node.js event loop / libuv

**結論：** 截至 2026-06，Node.js active LTS 是 **Node 24（codename "Krypton"，active LTS 自 2025-10-28）**；Node 22（"Jod"）已降為 maintenance LTS，Node 26 為 current（非 LTS）。libuv 事件迴圈 phase 順序：**timers → pending callbacks → idle/prepare → poll（I/O）→ check（setImmediate）→ close callbacks**；microtask（先 `process.nextTick` queue、再 Promise microtask queue）在每個 phase 之間／每個 macrotask 之後排空。thread pool：**UV_THREADPOOL_SIZE 預設 4**，用於 fs、dns（`getaddrinfo`/`dns.lookup`）、async crypto（pbkdf2/scrypt 等）、所有 async zlib——但**不用於 network I/O**（network I/O 走 OS async 原語 epoll/kqueue/IOCP，在 loop 自己的單一執行緒上完成）。setTimeout 最小延遲會被 clamp，且 timer 只在迴圈走到 timers phase 時才觸發，故不精確。

⚠️ **老化事實：** active LTS 已是 Node 24（Krypton），不是 Node 22（Jod）——2026-06 已換。書若寫 Node 18/20/22 為 active LTS 需更新。

**來源：**
- https://nodejs.org/en/about/previous-releases
- https://github.com/nodejs/Release/blob/main/CODENAMES.md
- https://docs.libuv.org/en/v1.x/design.html

---

## 11. Bull vs BullMQ

**結論：** Bull（OptimalBits）已在 legacy/maintenance 模式（只收 bug fix、不加新功能）；**BullMQ 是以 TypeScript 重寫的活躍後繼者**，由 **Taskforce.sh** 維護，最新版約 v5.71.0（2026-03）。2026 的明確建議：新專案用 BullMQ；履歷上若仍列「Bull」即是老化事實，宜註明已轉 BullMQ。兩者有破壞性 API 變更（Queue/Worker 拆分、QueueEvents 類別、整數 job ID 不再允許等）。

⚠️ **需修正的前提：** 找不到 Redis Ltd. 收購 Taskforce.sh / BullMQ 的證據——**不要寫「BullMQ 屬於／associated with Redis」**，應寫「由 Taskforce.sh 維護」。

**來源：**
- https://github.com/taskforcesh/bullmq
- https://github.com/OptimalBits/bull

---

## 12. Clinic.js（明確的老化警示）

**結論：⚠️ Clinic.js 已停止積極維護。** 由 NearForm 開發，官方 README 現直接寫「Clinic.js is not being actively maintained. Due to its strong ties to Node.js internals, it may not work or the results you get may not be accurate.」最後一個正式 release 是 **v13.0.0（2023-06-28）**，距今約 3 年；repo 未被 formally archived（仍 public）但實質 dormant/maintenance-only。其四工具仍是 **Doctor、Flame、Bubbleprof、Heap Profiler**。寫書務必把「未積極維護、可能與新版 Node 不相容」當關鍵警示，不要呈現為現役推薦工具。

**來源：**
- https://github.com/clinicjs/node-clinic
- https://github.com/clinicjs/node-clinic/releases

---

## 13. k6 與 Vegeta

**結論：** **Grafana k6**——Grafana Labs 於 2021 收購 k6，官方名稱即 Grafana k6；open source、Go 引擎、測試腳本以 JavaScript（現也支援 TypeScript）撰寫，授權為 **AGPLv3**（Grafana 系 2021 起由 Apache 2.0 改 AGPLv3）。積極維護中，最新主版本約 k6 2.0（2025-05）。**Vegeta**——tsenart 的 Go HTTP load testing tool（github.com/tsenart/vegeta），採 constant request rate（固定速率）模型，可作 CLI 或 Go library，仍維護中（最新約 v12.13.0，2025-10）。

⚠️ **易錯：** k6 授權是 AGPLv3（非 Apache/MIT）；名稱應寫「Grafana k6」。

**來源：**
- https://github.com/grafana/k6/blob/master/LICENSE.md
- https://grafana.com/blog/k6-2-0-release/
- https://github.com/tsenart/vegeta

---

## 14. OAuth 2.0 / OAuth 2.1 + JWT + Introspection

**結論：** OAuth 2.1（`draft-ietf-oauth-v2-1`）在 2026-06 **仍是 IETF Internet-Draft、尚未成為 RFC**；最新修訂 **draft-15（2026-03-02 發布，Standards Track，expires 2026-09-03）**。它整併 OAuth 2.0（RFC 6749）＋ BCP，四大變更：**PKCE 對所有用 authorization code flow 的 client 強制必要**、**移除 implicit grant**、**移除 Resource Owner Password Credentials（ROPC）grant**、**redirect URI 必須 exact string matching**。JWT（RFC 7519）走 short-lived access token（典型 15–60 分鐘）＋ long-lived refresh token；JWT 難以即時撤銷的根因是 **stateless / self-contained**，簽發到 expiry 前都有效，除非額外維護 denylist（而查 denylist 又抵銷本地自驗的好處，這正是要拆短命 access＋長命 refresh 的理由）。opaque/可撤銷 token 靠 **token introspection（RFC 7662）** 由 resource server 向 authorization server 即時查 active 狀態。

⚠️ **措辭提醒：** 坊間「OAuth 2.1 Is Here」標題易被誤讀為已成 RFC。datatracker 為準——**仍是 draft**。書中請寫「2.1 仍在 draft 階段（draft-15，2026-06）」而非「OAuth 2.1 標準／RFC」。

**來源：**
- https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/
- https://oauth.net/2.1/
- https://www.rfc-editor.org/rfc/rfc7662.html

---

## 15. PostgreSQL / MySQL(InnoDB) 隔離級別

**結論：** PostgreSQL **預設 Read Committed**，以 MVCC 實作。關鍵 nuance（官方文件證實）：PG 的 **Repeatable Read 實際上是 Snapshot Isolation**——防 non-repeatable read 與 phantom read，但 **Serialization Anomaly 在該級別仍 Possible，即不防 write skew**。要防 write skew 須升到 **Serializable，PG 用 SSI（Serializable Snapshot Isolation）**：以 predicate locking 追蹤 read/write dependencies，偵測危險結構時以「could not serialize access due to read/write dependencies」中止交易，**應用程式必須準備 retry**（SSI 比其他級別昂貴）。`deadlock_timeout` **預設 1s**（衝突後先等這段時間才跑 deadlock detection）。對照 MySQL/InnoDB：**預設 REPEATABLE READ**，其 RR 是 **locking ＋ MVCC 混合**——用 **next-key lock（record lock ＋ 前方 gap lock）** 阻止 phantom；這與 PG RR（純 snapshot、不上鎖、不防 write skew）本質不同。

⚠️ **並排呈現以防混淆：** PG「RR ≠ Serializable、不防 write skew」與 MySQL「RR 是預設且靠 next-key lock 防 phantom」是兩個容易被作者與讀者混為一談的對立事實。

**來源：**
- https://www.postgresql.org/docs/current/transaction-iso.html
- https://www.postgresql.org/docs/current/runtime-config-locks.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html
- https://dev.mysql.com/doc/refman/8.4/en/innodb-next-key-locking.html

---

## 16. KrakenD（vs Kong / AWS API Gateway）

**結論：** KrakenD 是以 **Go 寫的 stateless、declarative、高效能 API Gateway**，無 runtime database、靠啟動時讀 JSON 設定；招牌能力是 **native API aggregation**（合併多個 backend 回應、過濾/重塑欄位）。治理需精確：**並非整個 KrakenD 捐給基金會，而是其核心 framework 於 2021-05 捐成 Linux Foundation 主持的 `Lura Project`**；KrakenD Community／Enterprise 是 Lura engine 的兩個實作。2025-09 KrakenD（公司）被 Shop Circle 收購，仍維持團隊與路線，Lura framework 續留 Linux Foundation。對照：**Kong** 是 NGINX/OpenResty ＋ Lua plugin 架構、控制面有 DB（PostgreSQL/Cassandra）、plugin 生態為其強項（KrakenD 無 runtime plugin 系統）；**AWS API Gateway** 為全託管。

⚠️ **一致性陷阱：** 說「KrakenD 是 CNCF 專案」會錯——它是 **Linux Foundation**（且嚴格說是其 framework Lura，非 KrakenD 本身）；別寫成「KrakenD 仍是獨立開源公司」（2025 起已屬 Shop Circle）。CNCF 與 LF 不可混用。

**來源：**
- https://www.krakend.io/open-source/
- https://www.linuxfoundation.org/press/press-release/open-source-api-gateway-krakend-becomes-linux-foundation-project
- https://github.com/luraproject/lura

---

## 17. AWS Lambda

**結論：** 事件驅動執行模型、按 invocation 啟動 execution environment。帳號預設併發上限 **1,000（per region，可申請調高）**；reserved concurrency 可預留、provisioned concurrency 預先初始化環境降 cold start。Max timeout **900s（15 分鐘）**，預設 3s。Memory **128 MB–10,240 MB**；/tmp ephemeral storage 預設 512 MB、可調至 10,240 MB。**SnapStart 在 2026 已對 Java（11/17/21）、Python（3.12+）、.NET（8+）全部 GA**（Python/.NET 於 2024-11 GA），可去除約 70–90% init latency；Node.js、Ruby、OS-only、container image 不支援。Payload：**synchronous 6 MB**；**asynchronous 已從 256 KB 提升至 1 MB（2025-10-24 生效）**。

⚠️ **老化事實：** 書若寫「async payload 256 KB」**已過時**——2025-10-24 起為 **1 MB**（sync 仍 6 MB）。這是本批最易悄悄過時的數字之一。

**來源：**
- https://aws.amazon.com/about-aws/whats-new/2025/10/aws-lambda-payload-size-256-kb-1-mb-invocations/
- https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html
- https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html

---

## 18. AWS ALB vs API Gateway

**結論：** **ALB**（L7 load balancer）以 target groups 為核心、支援 host/path/header-based routing，但不做 per-request request/response transformation、原生 auth 有限（OIDC/Cognito listener auth 可、但非 per-request fine-grained）、無原生 throttling（需搭 WAF 做 rate limiting）；成本走 LCU 模型，高吞吐下較便宜、延遲較低。**API Gateway** 提供 throttling（REST API 帳號預設約 10,000 RPS burst / 5,000 RPS steady-state per region）、auth（JWT / Lambda authorizers / IAM）、request transformation、usage plans，整體較貴。**HTTP API vs REST API**：HTTP API 較新、約便宜 70%、延遲較低、支援 JWT authorizer，但缺 VTL mapping templates、usage plans、API keys、private endpoints 等；REST API 功能最完整。經驗法則：需 VTL transform / usage plans / API keys → REST API；只要便宜快速 proxy + 簡單 JWT auth → HTTP API；純 L7 routing 到容器/EC2 且不需 per-request auth/transform → ALB。

**來源：**
- https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html
- https://aws.amazon.com/api-gateway/faqs/

---

## 19. Kubernetes CronJob

**結論：** CronJob 為穩定資源（**batch/v1**，自 v1.21 GA），具 `schedule`（cron 格式）、`concurrencyPolicy`（**Allow / Forbid / Replace**，預設 Allow）、`startingDeadlineSeconds`（預設 nil；**設成 < 10 秒可能根本不被排程**，因 controller 每 10 秒才 reconcile 一次）、`timeZone`（自 v1.27 GA，吃 IANA 名）等欄位。Missed-schedule：controller 計算自上次排程以來錯過次數，**超過 100 次時記一個 `TooManyMissedTimes` Warning event、跳過中間那一堆漏跑、仍只為最近一次建 Job、並照常繼續排程**（設了 `startingDeadlineSeconds` 則改以該秒數窗口計算漏跑起點，使數字幾乎不會破 100）。官方文件明確聲明 CronJob **非 exactly-once**——「在某些情況下，一個 job 可能被建立兩次，或一次都不建立」，故 job 應為 idempotent。

⚠️ **老化事實（需更正，2026-06-22 兩來源確認）：** 「超過 100 次則**停止排程並記 error、永久停擺直到手動介入**」是 **v1.21 GA 之前的舊 v1 controller** 行為，那行舊日誌長 `Cannot determine if job needs to be started: too many missed start times (> 100)`。現行 v2 controller（`pkg/controller/cronjob/utils.go` 的 `mostRecentScheduleTime`）只把該情況標成 `manyMissed`、呼叫端記 `TooManyMissedTimes` Warning，**回傳值仍是最近一次排程時刻、照建不誤、不停擺**。許多 2026 部落格/平台商 KB 仍在重述舊說法，但**原始碼才是事實底**；kubernetes/website Issue #44525 亦指此段官方文件措辭過時。真正的傷害是「中間漏掉的窗全部丟失」＋「只盯 Pod 健康會看不到」，而非「再也不觸發」。本書 `cronjob.md` 已據此改寫（開場事故、100 次段落、收束）。

**來源：**
- https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/
- https://github.com/kubernetes/kubernetes/blob/master/pkg/controller/cronjob/utils.go
- https://github.com/kubernetes/website/issues/44525

---

## 20. Snyk

**結論：** Snyk 是 developer-security platform，核心為 **SCA（software composition analysis，開源相依套件漏洞掃描，即 Snyk Open Source）**，並涵蓋 SAST（Snyk Code）、Container、IaC、API & Web (DAST)。2026 仍為商業 freemium：Free 層（各產品有測試次數上限）、Team 約 $25 per developer/月、Enterprise 客製報價；深度整合 IDE / Git / CI/CD，提供自動修復 PR。

⚠️ **易腐：** 定價數字（$25/dev/月、free 配額）時效敏感，引用時標 2026-06 並以官網 pricing 頁為準。

**來源：**
- https://snyk.io/

---

## 21. Socket.io

**結論：** Socket.IO 主程式庫當前為 **v4.x**（最新約 4.8.3，2025-12），仍活躍維護。相對 raw WebSocket 的差異：transport fallback（WebSocket 優先，v4.7+ 加入 WebTransport，最後退回 HTTP long-polling）、自動重連（指數退避 + heartbeat）、rooms、acknowledgements、namespaces。多節點水平擴展/跨實例 fan-out 由 **`@socket.io/redis-adapter`**（當前約 v8.3.0）提供，依賴 Redis Pub/Sub 在多台 Socket.IO server 間廣播封包；新部署另可用 Redis 7.0 sharded Pub/Sub 的 sharded adapter，或處理斷線重續的 Redis Streams adapter。

⚠️ **小提醒：** redis-adapter 8.3.0 已發布約兩年，若書中強調「最新」宜寫「v8.x」而非綁死小版本。

**來源：**
- https://socket.io/docs/v4/redis-adapter/
- https://www.npmjs.com/package/@socket.io/redis-adapter

---

## 22. WebSocket

**結論：** WebSocket 由 **RFC 6455** 定義。Frame 結構含 opcodes（0x0 continuation、0x1 text、0x2 binary、0x8 close、0x9 ping、0xA pong），**client→server 的 frame 一律 masked**（32-bit masking key），server→client 則 MUST NOT mask；ping/pong 為 control frame，用於 heartbeat/keepalive（payload ≤ 125 bytes、不可分片）。橫向擴展問題：WebSocket 連線為 stateful/long-lived，多節點擴展需 **sticky session（session affinity）** ＋ pub/sub backplane 共享連線狀態／跨節點 fan-out。

⚠️ **界定：** sticky session ＋ backplane 屬部署架構慣例，RFC 6455 本身不規範擴展策略。

**來源：**
- https://www.rfc-editor.org/rfc/rfc6455

---

## 23. Eventual Consistency / CAP / PACELC（歸屬精確性）

**結論：** **CAP theorem 由 Eric Brewer 提出**（2000 PODC keynote 的 conjecture），**由 Seth Gilbert 與 Nancy Lynch 於 2002 形式化證明**（"Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services", ACM SIGACT News 2002）。**PACELC 由 Daniel Abadi 提出**——最早見於 2010 年部落格文章，於 **2012 年 IEEE Computer 論文**〈Consistency Tradeoffs in Modern Distributed Database System Design: CAP is Only Part of the Story〉(vol. 45, no. 2, pp. 37–42) 正式形式化。PACELC 擴展 CAP：**if Partition → 選 Availability 或 Consistency；Else（正常運作）→ 選 Latency 或 Consistency**。Eventual consistency：若無新更新，所有副本最終會收斂到同一值（換取高可用＋低延遲、犧牲即時強一致）。

⚠️ **精確措辭：** PACELC 歸屬 Abadi 宜寫「2010 年部落格初提、2012 年 IEEE Computer 論文形式化」；勿把 Brewer（conjecture）與 Gilbert-Lynch（證明）混為一人。

**來源：**
- https://dl.acm.org/citation.cfm?id=2360959
- https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf

---

## 24. Prisma ORM

**結論：** Prisma 是 Node.js/TypeScript ORM：`schema.prisma` 宣告 schema、type-safe client、內建 migrations。最重大近期變更：**Prisma 已棄用 Rust query engine，改走 TypeScript/WASM 的 query compiler**——**Prisma 7（2025-11-19 發布）起，no-Rust 的 TS query compiler 為預設**，官方稱查詢最高約 3x 快、bundle 縮約 90%（約 14MB→1.6MB）。**當前 major 版本為 v7。** 連線池：Prisma Client 自帶 connection pool，但在 **serverless 下每個 function 實例各自開連線、auto-scale 時極易耗盡 DB 連線上限**，故需外部 pooler（**PgBouncer** 或 **Prisma Accelerate**）；代價是 transaction-mode pooling 下 session 狀態（prepared statements / advisory locks / temp tables）不跨 transaction 保留。

⚠️ **老化事實：** 寫「Prisma 仍用 Rust query engine」已過時（那是 v6 及更早）。應以「v7（2026-06）已預設 Rust-free TS query compiler」表述；major 版本號最易 aging，建議標日期。

**來源：**
- https://www.prisma.io/blog/from-rust-to-typescript-a-new-chapter-for-prisma-orm
- https://www.prisma.io/docs/postgres/database/connection-pooling

---

## ⚠️ 未能確認 / 需人工複查

以下項目未能從一手官方來源逐字鎖定，或本質上會隨時間漂移，下次掃描（review_after_days 到期）時優先複查：

1. **SQS synchronous payload 6 MB** — 多來源一致但 AWS Lambda agent 未逐字 fetch quotas 頁；高可信，建議直接 fetch Lambda quotas 頁定錨。（註：6 MB 屬 Lambda sync invoke 限制，非 SQS 本身。）
2. **high throughput FIFO 的精確 TPS** — AWS 以「per API request TPS / per-partition 3,000 批次」表述、無單一全域數字；「約 70,000 msg/s（批次，主要 region）」為 region-dependent，引用須標 region。
3. **Valkey distro 精確版本號**（Fedora 42／Ubuntu 26.04／Debian 13 等）與廠商效能宣稱（快 8%／省 20%／AWS 已遷數百萬節點）— 多來自部落格而非官方逐一公告；建議概括陳述，勿綁死數字。
4. **BullMQ 與 Redis 的關係** — 未找到 Redis Ltd. 收購 Taskforce.sh / BullMQ 的證據；目前證據指向「由 Taskforce.sh 維護」。若書中需斷言歸屬，須另找官方併購公告，否則寫「Taskforce.sh 維護」。
5. **Snyk 定價**（$25/dev/月、free 配額）— 時效敏感，以官網 pricing 頁為準、標查證日期。
6. **OAuth 2.1 定案時程** — 仍是 draft-15，無確定 RFC 發布日；若書中要給讀者「預計何時定案」需另查 OAuth WG 的 last-call/IESG 時程，避免讀者把 draft 當凍結標準。
7. **各專案最新 patch 版本號**（Redis 8.8.0、Valkey 9.1.0、coturn 4.13.1、Fluent Bit 5.0.7、BullMQ 5.71.0、Socket.IO 4.8.3、Vegeta 12.13.0 等）— 高頻變動，引用時一律標日期、視為易腐；本檔記錄的是 2026-06-21 當下狀態。
