# 附錄 C — 延伸閱讀總地圖

這份地圖把全書二十章各自的「延伸閱讀」收攏成一張總圖，按 Part 組織。每一條都是各章正文裡實際出現過、或經 `_meta/landscape-2026-06.md` 驗證過的連結——沒有一條是這裡才憑空生出來的。排序原則：官方文件、RFC、原始論文優先；二手導讀與概念整理放後面。

讀法建議三條：

- **想複習某個系統**：直接跳到它所在的 Part，那幾條就是該章的一手彈藥。
- **想查一個會腐的事實**（版本、語意、授權、預設值）：先翻每條後面標的官方來源，再翻 `landscape-2026-06.md` 的對應節看 `last_verified` 日期。時效敏感的連結都標了「（2026-06）」——過了就當它可能變了。
- **想往本書邊界外走**：看本附錄最後的「跨書指引」，四本姊妹書各補本書一塊缺口。

連結若標「（未驗證）」，表示它在章內出現但不在 landscape 的逐項查證清單裡，引用前自己再確認一次。沒標的，要嘛是 landscape 驗證過、要嘛是穩定的 RFC／論文／官方文件。

---

## Part I — 開場與透鏡（ch01–02）

把履歷讀成系統地圖、立起五個故障問句這支透鏡。這部的連結多半是「親眼確認規格，別靠記憶」型的一手出處。

- **Redis Pub/Sub 官方文件** — <https://redis.io/docs/latest/develop/pubsub/>：讀「Delivery semantics」一段，親眼確認 fire-and-forget／at-most-once 是官方說法。全書即時通知體檢的交付軸都站在這句話上（ch01、ch02、ch07、ch17）。
- **Amazon SQS — at-least-once delivery（官方）** — <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues-at-least-once-delivery.html>：標準佇列「會重」是規格不是運氣，官方直接要你「設計成冪等」（ch01、ch04、ch10）。
- **Amazon SQS — Visibility timeout（官方）** — <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html>：「at-least-once、可能重複」的官方措辭，交付軸「規格保證不是運氣」的第一手依據（ch02）。
- **Kubernetes — CronJob（官方文件，2026-06）** — <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>：白紙黑字寫「非 exactly-once、job 應為 idempotent」，持久軸與並發軸在排程上交會的標準案例（ch02、ch04、ch09、ch13；landscape §19）。
- **Twilio — Twilio Video Will Remain a Standalone Product** — <https://www.twilio.com/en-us/changelog/-twilio-video-will-remain-a-standalone-product>：2024-10-21 撤回 EOL 的官方原文（"we've reversed our earlier decision"）。把「Twilio 要關了」這個老兵記憶就地更新（ch01、ch08、ch19；landscape §6）。
- **OAuth 2.1 草案（IETF datatracker）** — <https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/>：確認 2026-06 它**仍是 draft（draft-15）不是 RFC**，順帶看 JWT 難撤銷的脈絡（ch01、ch16；landscape §14）。
- **Node.js Releases（官方）** — <https://nodejs.org/en/about/previous-releases>：查當前 active LTS，治好「Node LTS 是 18/20」的過時記憶（ch01、ch12；landscape §10）。
- **Gilbert & Lynch, "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services"（ACM SIGACT News, 2002）** — <https://dl.acm.org/citation.cfm?id=564601>：CAP 的形式化證明原文。確認歸屬（Brewer 提猜想、這兩位給證明），並看「分區時 C 與 A 不可兼得」怎麼被嚴格證出來（ch02；landscape §23）。
- **Daniel Abadi, "Consistency Tradeoffs in Modern Distributed Database System Design"（PACELC, IEEE Computer 2012）** — <https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf>：PACELC 的形式化論文。讀「Else → Latency or Consistency」那半邊——CAP 沒談的「網路正常時你還在付什麼代價」（ch02、ch11；landscape §23）。

---

## Part II — NeoBards：高併發與分散式（ch03–06）

回到 RDS 降 40%、結算 pipeline、Node 剖析、FluentBit 觀測四個招牌系統。這部的連結密度最高，多是 MySQL／AWS／Node／Fluent Bit 的官方手冊。

**ch03 — RDS CPU 降 40%：鎖、交易與 profiling**

- **MySQL Reference Manual — InnoDB Locking（17.7.1）** — <https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html>：行鎖、意向鎖、gap lock、next-key lock、insert intention lock 的官方定義。讀「Gap Locks」與「Insert Intention Locks」兩小節。
- **MySQL Reference Manual — Next-Key Locking / Phantom Rows（17.7.4）** — <https://dev.mysql.com/doc/refman/8.4/en/innodb-next-key-locking.html>：為什麼 RR 用 next-key lock 防幻讀、為什麼插入也會被 gap 擋住，本章反直覺例子的原型（ch11 再用一次；landscape §15）。
- **MySQL Reference Manual — Deadlock Detection（17.7.5.2）** — <https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlock-detection.html>：wait-for graph、挑犧牲者、回滾、error 1213，以及高並發下偵測本身的成本。
- **AWS re:Post — Resolve high CPU use on RDS for MySQL or Aurora MySQL** — <https://repost.aws/knowledge-center/rds-instance-high-cpu>：用 Performance Insights／Enhanced Monitoring 把「CPU 被什麼燒」拆開的官方流程，對照你當年看 CloudWatch 的做法、補上 wait-event 維度。
- **AWS Aurora User Guide — synch/cond/innodb/row_lock_wait** — <https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/ams-waits.row-lock-wait.html>：Performance Insights 上「行鎖等待」wait event 的官方說明。
- **AWS re:Post — Resolve Error 1205（Lock wait timeout exceeded）** — <https://repost.aws/knowledge-center/rds-mysql-error-1205>：`innodb_lock_wait_timeout`（預設 50s）超時的成因與排查。

**ch04 — 結算 pipeline：交付語意與跨服務最終一致**

- **Amazon SQS — Preventing duplicate processing** — <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/avoding-processing-duplicates-in-multiple-producer-consumer-system.html>：AWS 自己怎麼建議在多生產者／多消費者下做去重，對照你的 `settlement_key` 設計。
- **Saga choreography pattern（AWS Prescriptive Guidance）** — <https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga-choreography.html>：補償交易與跨服務最終一致的權威範式，對照本章「重試／補償／對帳」的拆解。
- **Saga pattern（Microsoft Azure Architecture Center）** — <https://learn.microsoft.com/en-us/azure/architecture/patterns/saga>：把「為什麼不能用一個分散式交易包住四個服務」講得最清楚的一篇，含 orchestration vs choreography 取捨。

**ch05 — 負載測試與 Node 剖析**

- **Node.js 官方《Don't Block the Event Loop (or the Worker Pool)》** — <https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop>：本章核心的官方版，含「50MB JSON parse 要 1.3 秒」的具體數字、`JSON.parse` 為何 O(n) 危險。讀「Blocking the Event Loop」與「JSON DoS」兩節。
- **Node.js 官方《Flame Graphs》診斷指南** — <https://nodejs.org/learn/diagnostics/flame-graphs>：用 `--prof`／`--cpu-prof` 產火焰圖、怎麼讀寬度與 self time。不依賴第三方工具的官方路徑，最不會版本過時。
- **Clinic.js node-clinic README** — <https://github.com/clinicjs/node-clinic>：**親自去讀 README 開頭那句「is not being actively maintained」**（2026-06）。本章老兵記憶校正的一手來源（landscape §12）。
- **0x（davidmarkclements/0x）** — <https://github.com/davidmarkclements/0x>：單指令火焰圖工具，Clinic.js Flame 的底層；想用第三方工具又不想裝整套 Clinic.js 時的選擇，注意它與最新 Node 的相容性。
- **Grafana k6 — Open and closed models** — <https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/>：壓測陷阱的官方說明——兩種模型差在哪、為什麼開放模型才逼近真實流量。k6 授權為 AGPLv3，使用前留意（landscape §13）。
- **Vegeta（tsenart/vegeta）** — <https://github.com/tsenart/vegeta>：固定速率壓測工具，README 直接點明它「avoids nasty Coordinated Omission」。理解「為什麼固定速率比封閉式準」最短的路（landscape §13）。

**ch06 — FluentBit + Lua：從 log 擠出 metric**

- **Fluent Bit 官方手冊 — Lua filter** — <https://docs.fluentbit.io/manual/data-pipeline/filters/lua>：你那段 Lua filter 的權威介面。讀「callback prototypes」與回傳 code 的語意（-1 丟棄、0 原樣、1/2 取代），對應本章 worked example（landscape §9）。
- **Fluent Bit 官方手冊 — Amazon S3 output** — <https://docs.fluentbit.io/manual/data-pipeline/outputs/s3>：`out_s3` 的 multipart 上傳與「大小 OR 時間先到先送」如何決定資料新鮮度。讀「buffering」段。
- **Fluent Bit 官方手冊 — Buffering & backpressure** — <https://docs.fluentbit.io/manual/administration/buffering-and-storage> 與 <https://docs.fluentbit.io/manual/administration/backpressure>：`mem_buf_limit`、input 暫停、檔案系統 buffer——本章「丟還是擋」抉擇的權威來源（完整背壓工程見 ch14）。
- **Fluent Bit 官方手冊 — Fluentd and Fluent Bit** — <https://docs.fluentbit.io/manual/about/fluentd-and-fluent-bit>：C vs Ruby、內建外掛 vs gem 生態、兩者皆 CNCF graduated 的分工。
- **AWS — Creating metrics from log events using filters** — <https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html>：CloudWatch metric filter 能做與不能做（百分位限制、不回溯、每 log group 100 個 filter 上限），本章「為什麼不直接用 CloudWatch」的對照依據。

---

## Part III — LetsTalk：即時通訊（ch07–09）

回到 WebSocket + Redis Pub/Sub、WebRTC + Jitsi、setTimeout → cron job queue。這部的連結扎在 RFC（WebSocket、ICE/STUN/TURN）與各家官方文件上。

**ch07 — 即時通知：WebSocket + Redis Pub/Sub 扇出與多裝置同步**

- **RFC 6455 — The WebSocket Protocol** — <https://www.rfc-editor.org/rfc/rfc6455>：讀 §5（frame、masking、opcode）與 §5.5（ping/pong control frame）。client→server 為什麼一律 masked、心跳為何是 control frame，答案都在這；§1.1 明說協定不規範擴展——sticky session 是你的事（landscape §22）。
- **Redis Pub/Sub 官方文件** — <https://redis.io/docs/latest/develop/pubsub/>：把「at-most-once、無持久化、離線訂閱者永久錯過」這幾句官方原文背下來，這是你系統能力邊界的法律條文。順帶看 `SPUBLISH`/`SSUBSCRIBE`（sharded Pub/Sub，Redis 7+）（landscape §3）。
- **Redis Streams 用例文件** — <https://redis.io/docs/latest/develop/use-cases/streaming/>：consumer group 與 Pending Entries List——「離線補發要持久」那條路在 Redis 內的選項，與 Pub/Sub 的精確對照（深掘留 ch17；landscape §3）。
- **Socket.IO Redis adapter 文件** — <https://socket.io/docs/v4/redis-adapter/>：它怎麼用 Pub/Sub 在多節點間廣播封包——你當年手刻的東西它幫你封裝了，但底層 Pub/Sub 限制一字不變（landscape §21）。
- **Firebase — FCM on Android / message priority** — <https://firebase.blog/posts/2025/04/fcm-on-android/> 與 <https://firebase.google.com/docs/cloud-messaging/android-message-priority>：Doze 模式下高/普通優先級差別、雲端佇列（離線約 4 週）。你「自建放棄了什麼」的官方依據——OS 級喚醒與離線佇列是平台特權。
- **AppInChina — Does Firebase Work in China?** — <https://appinchina.co/does-firebase-work-in-china/>：印證 FCM 在中國被擋、標準推送 SDK 失效（2026-06 仍如此），解釋你為何非自建不可。（未驗證——非 landscape 逐項清單，引用前自查）

**ch08 — 語音與視訊：WebRTC、Jitsi 與 NAT 穿透**

- **RFC 8445 — ICE** — <https://datatracker.ietf.org/doc/html/rfc8445>：NAT 穿透整體框架的一手出處（obsoletes 5245）；看 candidate 蒐集與連通性檢查的概念段即可（landscape §7）。
- **RFC 8489 — STUN** — <https://www.rfc-editor.org/rfc/rfc8489.html>（obsoletes 5389）／**RFC 8656 — TURN** — <https://datatracker.ietf.org/doc/rfc8656/>（obsoletes 5766）：STUN/TURN 的權威定義；TURN 那篇讀「為什麼需要 relay」的動機段，正是 symmetric NAT 失靈的官方版本（landscape §7）。
- **Jitsi Videobridge（GitHub）** — <https://github.com/jitsi/jitsi-videobridge>：官方自述「WebRTC compatible video router or SFU」的一手出處；判斷它死活看 **commits** 不看 releases（landscape §5、§6 的陷阱）。
- **coturn（GitHub）** — <https://github.com/coturn/coturn>：你當年自架的那台 TURN/STUN server，一套同時當 STUN 與 TURN；版本號易腐，引用標日期（landscape §8）。
- **WebRTC connectivity（MDN）** — <https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Connectivity>：把 ICE、STUN、TURN、candidate 類型（host/srflx/relay）與 trickle ICE 講得最清楚的入門權威；讀「ICE candidates」與「STUN/TURN」兩段。（未驗證——非 landscape 逐項清單）
- **Getting started with peer connections（webrtc.org）** — <https://webrtc.org/getting-started/peer-connections>：官方的 offer/answer 信令流程（createOffer → setLocalDescription → 送 → setRemoteDescription → createAnswer）。（未驗證——非 landscape 逐項清單）

**ch09 — 排程訊息重構：setTimeout → cron job queue**

- **Node.js 官方 Timers 文件** — <https://nodejs.org/api/timers.html>：讀 `setTimeout` 那段，特別是「delay 大於 2147483647、小於 1、或 NaN 時被設成 1」——本章 24.8 天硬上限的一手出處（2026-06）。
- **Node.js 官方《The Node.js Event Loop》** — <https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick>：timers 相位那段，理解為什麼 `setTimeout` 是「不早於」而非「準時」（深掘到相位級在 ch12；landscape §10）。
- **libuv 官方 `uv_timer_t` 文件** — <https://docs.libuv.org/en/v1.x/timer.html>：`setTimeout` 底下真正在動的計時器 handle；想看「timer skew」與 `uv_update_time` 為什麼存在，讀這裡。
- **BullMQ 官方文件 — Delayed jobs** — <https://docs.bullmq.io/guide/jobs/delayed>：delayed job 的官方說明，配合 <https://docs.bullmq.io/guide/going-to-production> 讀「持久化要開 AOF」那段。注意這是 **BullMQ**（現役），不是 Bull（已 legacy）（landscape §11）。
- **BullMQ（taskforcesh/bullmq）vs Bull（OptimalBits/bull）** — <https://github.com/taskforcesh/bullmq> 與 <https://github.com/OptimalBits/bull>：兩個 repo 並讀，親眼確認「Bull 進維護、BullMQ 現役、皆 Taskforce.sh 維護、查無 Redis 收購」這組校正（landscape §11）。

---

## Part IV — 橫切的老問題（ch10–18）

把系統章反覆撞上的老問題逐一挖穿。這部連結含全書最多的 RFC 與原始論文（Two Generals、Metastable Failures、PACELC、PostgreSQL/MySQL 隔離級別官方文件）。

**ch10 — 交付語意與冪等**

- **Two Generals' Problem（Wikipedia）** — <https://en.wikipedia.org/wiki/Two_Generals%27_Problem>：第一個被證明 unsolvable 的電腦通訊問題。讀「Illustrating the problem」與「Proof」——本章 ack 不可區分性的源頭（注意它和 FLP 是兩個不同結果）。
- **Exactly-once processing in Amazon SQS** — <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html>：官方對 FIFO「exactly-once processing」的定義，搭配 [Using the message deduplication ID](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html) 讀 5 分鐘 dedup 窗口的精確語意（landscape §1）。
- **You Cannot Have Exactly-Once Delivery（Tyler Treat）** — <https://bravenewgeek.com/you-cannot-have-exactly-once-delivery/>：把「exactly-once 交付不可能、所謂 exactly-once 是 at-least-once + 冪等」講得最透的一篇，與本章兩將軍版互相印證。（未驗證——非 landscape 逐項清單）
- **Exactly-Once Semantics Are Possible: Here's How Apache Kafka Does It（Confluent）** — <https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/>：Kafka 怎麼用冪等 producer（PID + 序號）+ 交易做 EOS。讀它看清「possible」指的是 processing 不是 delivery。（未驗證——非 landscape 逐項清單）
- **Implementing Stripe-like Idempotency Keys in Postgres（brandur.org）** — <https://brandur.org/idempotency-keys>：用 Postgres 唯一約束 + 交易做冪等鍵的工程範本，含「副作用要納入保護」。（未驗證——非 landscape 逐項清單）
- **Idempotent requests（Stripe API Reference）** — <https://docs.stripe.com/api/idempotent_requests>：請求層冪等的業界標準，含「key 在 ≥24 小時後可被清掉」——「去重窗口有限」的真實工業例證。（未驗證——非 landscape 逐項清單）

**ch11 — 一致性、隔離級別與複製延遲**

- **PostgreSQL Documentation — Transaction Isolation（13.2）** — <https://www.postgresql.org/docs/current/transaction-iso.html>：務必讀「Repeatable Read Isolation Level」（白紙黑字說它是 Snapshot Isolation、Serialization Anomaly 仍 Possible）與「Serializable Isolation Level」（SSI、predicate locking、必須 retry）兩段（landscape §15）。
- **PostgreSQL Documentation — Lock Management** — <https://www.postgresql.org/docs/current/runtime-config-locks.html>：`deadlock_timeout` 預設 1s 與「為什麼先等再偵測」的取捨理由（landscape §15）。
- **MySQL 8.4 Reference Manual — Transaction Isolation Levels（17.7.2.1）** — <https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html>：InnoDB 預設 RR、各級別行為、與 next-key lock 的關係。對照 PG 看兩個 RR 的本質差異（landscape §15）。
- **Jepsen — MySQL 8.0.34** — <https://jepsen.io/analyses/mysql-8.0.34>：實測 MySQL 的 RR「更像 Snapshot Isolation」、會出現 write skew 等 G2 異常。本章「MySQL RR 也擋不住 write skew」的獨立佐證（對抗性測試，結論比廠商文件保守）。
- **Daniel Abadi — PACELC（IEEE Computer 2012）** — <https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf>：把 read replica 同步/非同步的選擇對回 PACELC 的 E 段，會豁然開朗（landscape §23）。
- **Martin Kleppmann —《Designing Data-Intensive Applications》第 5、7、9 章**（書，非連結）：複製、交易與隔離級別、一致性與共識的權威整合。本章每一條（一致性譜、write skew、複製延遲、線性一致）這本都有更深的版本。

**ch12 — event loop 與單執行緒並發**

- **libuv 官方《Design overview》** — <https://docs.libuv.org/en/v1.x/design.html>：相位順序（timers → pending → idle/prepare → poll → check → close）的一手權威。讀 "The I/O loop" 那節，把相位圖刻進腦子（landscape §10）。
- **Node.js 官方《The Node.js Event Loop》** — <https://nodejs.org/learn/asynchronous-work/event-loop-timers-and-nexttick>：各相位在 Node 語境下處理什麼、`setTimeout` 為什麼不精確、poll 相位怎麼「阻塞地等」。
- **Node.js 官方《Don't Block the Event Loop》** — <https://nodejs.org/learn/asynchronous-work/dont-block-the-event-loop>：`process.nextTick` 為什麼能餓死 I/O、`setImmediate` 為什麼是延後工作的安全選擇。讀「nextTick vs setImmediate」與「Blocking the Event Loop」兩段。
- **libuv 官方《Thread pool work scheduling》** — <https://docs.libuv.org/en/v1.x/threadpool.html>：`UV_THREADPOOL_SIZE` 預設 4、哪些操作（fs/dns.lookup/crypto/zlib）走 pool、網路 I/O **不**走 pool 的一手依據（landscape §10）。
- **Node.js previous-releases / Release codenames** — <https://nodejs.org/en/about/previous-releases> 與 <https://github.com/nodejs/Release>：確認 active LTS 是 Node 24「Krypton」（自 2025-10-28）、Node 22「Jod」已降為 maintenance。老兵記憶校正用（landscape §10）。

**ch13 — 時間、持久化與失敗**

- **Node.js 官方 `perf_hooks` / `performance.now()`** — <https://nodejs.org/api/perf_hooks.html> 與 **`process.hrtime.bigint()`** — <https://nodejs.org/api/process.html#processhrtimebigint>：兩個**不依賴系統時鐘**的單調高精度計時來源——「量 duration 用這個、不用 `Date.now()`」那條鐵律的一手出處（2026-06）。
- **Kubernetes CronJob 官方文件** — <https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/>：讀 `concurrencyPolicy`、`startingDeadlineSeconds`、"missed schedule (> 100)" 與「不保證 exactly-once」那幾段，與 ch04 倚賴同一份文件（landscape §19）。
- **NTP slew vs step 行為** — Red Hat《Avoiding clock drift on VMs》<https://www.redhat.com/en/blog/avoiding-clock-drift-vms> 及 NTP 官方 ntpd 文件 <https://www.ntp.org/documentation/4.2.8-series/ntpd/>：理解「偏差 < 128ms 用 slew 平滑校正（只往前）、超過則 step 跳變（可往回）」這條本章倚賴的事實。
- **BullMQ 官方《Going to production》** — <https://docs.bullmq.io/guide/going-to-production>：「持久化要開 AOF」那段，「持久化是主動的、fsync 有代價」在你 ch09 系統上的具體化身。
- **Redis 官方 persistence 文件** — <https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/>：RDB vs AOF、fsync 策略（always/everysec/no）與各自「斷電丟多少」的權衡。fsync 那節的一手依據，深掘在 ch17（landscape §4）。

**ch14 — 背壓、rate limiting 與過載防禦**

- **Backpressuring in Streams（Node.js 官方）** — <https://nodejs.org/learn/modules/backpressuring-in-streams>：`highWaterMark`、`write()` 回傳值、`'drain'`、`pipe()` 自動接背壓——本章背壓具體化的源頭。搭配 [Stream API 文件](https://nodejs.org/api/stream.html) 查 `highWaterMark` 預設值。
- **Exponential Backoff And Jitter（AWS Architecture Blog / Marc Brooker）** — <https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/>：退避+jitter 論證的一手出處，有「沒有 jitter 退避只是讓同步洪水每隔越來越久來一次」的模擬圖。搭配 [Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)。
- **Metastable Failures in Distributed Systems（Bronson et al., HotOS '21）** — <https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf>：把 retry storm/death spiral/cascading failure 統一成「壞狀態+觸發+自我維持迴圈」的原始論文。12 頁好讀，讀「root cause 是 sustaining loop 不是 trigger」。搭配 [Marc Brooker 的白話導讀](https://brooker.co.za/blog/2021/05/24/metastable.html)。
- **CircuitBreaker（Resilience4j 官方文件）** — <https://resilience4j.readme.io/docs/circuitbreaker>：closed/open/half-open 三態狀態機的一手定義與可調參數，順便看它怎麼取代已進維護模式的 Hystrix。
- **Token Bucket vs. Leaky Bucket Algorithm（GeeksforGeeks）** — <https://www.geeksforgeeks.org/system-design/token-bucket-vs-leaky-bucket-algorithm-system-design/>：兩演算法並排對照「突發容忍 vs 流量整形」，有圖。（未驗證——非 landscape 逐項清單）

**ch15 — 觀測性**

- **Google SRE Book — Monitoring Distributed Systems（四個黃金信號）** — <https://sre.google/sre-book/monitoring-distributed-systems/>：latency／traffic／errors／saturation 的原始出處。讀「The Four Golden Signals」與「量 p99 能給你飽和的極早期信號」——「看 p99」與「症狀告警」的權威根。
- **Google SRE Workbook — Alerting on SLOs** — <https://sre.google/workbook/alerting-on-slos/>：怎麼把 SLO 變成告警的正規方法。讀「burn rate」段，理解為什麼不該在「錯誤率 > 0」告警、該在「燒預算太快」告警。
- **OpenTelemetry — Signals** — <https://opentelemetry.io/docs/concepts/signals/>：三柱（＋profiling 第四柱）統一在 OTLP 一個協定下的概念。只讀概念頁理解 OTel 的定位，不需深入 API。
- **USE Method（Brendan Gregg）** — <https://www.brendangregg.com/usemethod.html>：Utilization／Saturation／Errors，資源層診斷的系統化方法——症狀告警響之後怎麼有結構地查根因。
- **Charity Majors — Observability is a Many-Splendored Definition** — <https://charity.wtf/2020/03/03/observability-is-a-many-splendored-thing/>：monitoring（已知的未知）vs observability（未知的未知）的經典定義，與「高基數是 observability 的核心」。（未驗證——非 landscape 逐項清單）

**ch16 — 身分與存取：JWT、OAuth2 與 RBAC**

- **The OAuth 2.1 Authorization Framework（draft-ietf-oauth-v2-1-15）** — <https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/>：「OAuth 2.1 仍是 draft、不是 RFC」的一手出處。讀它對 PKCE 強制、移除 implicit/ROPC、redirect URI 精確比對的條文，別讀二手「2.1 Is Here」標題（landscape §14）。
- **RFC 7519 — JSON Web Token (JWT)** — <https://www.rfc-editor.org/rfc/rfc7519.html>：讀 §3「JWT 是 JWS 或 JWE」——「預設只簽（JWS）不加密、payload 是 base64url 不是密文」的源頭（landscape §14）。
- **RFC 7662 — OAuth 2.0 Token Introspection** — <https://www.rfc-editor.org/info/rfc7662>：opaque/可撤 token 怎麼向 authorization server 即時查 `active` 狀態——「introspection 是 JWT 自驗的反面」的依據（landscape §14）。
- **OpenID Connect** — <https://oauth.net/openid-connect/>：補上本章一句話帶過的 OIDC——它如何在 OAuth2 上加身分層、發 ID token 回答「你是誰」。讀「OAuth 管授權、OIDC 管認證」這條責任邊界。
- **RS256 vs HS256: A deep dive into JWT signing algorithms（WorkOS）** — <https://workos.com/blog/rs256-vs-hs256-jwt-signing-algorithms>：把金鑰分發帳講得最清楚——HS256 共用祕鑰（攻擊面 = N）vs RS256 公私鑰分離（下游只持公鑰、搭 JWKS 輪替）。（未驗證——非 landscape 逐項清單）
- **RBAC vs. ABAC: What is the difference?（WorkOS）** — <https://workos.com/blog/rbac-vs-abac>：RBAC（好稽核）與 ABAC（細粒度但難回答「這人能碰什麼」）的分界與取捨。（未驗證——非 landscape 逐項清單）

**ch17 — 快取與 Redis 內部**

- **Redis Persistence 官方文件** — <https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/>：讀 RDB vs AOF 與 `appendfsync` 三策略那段。官方原文「with everysec you can only lose one second worth of writes」與「fork() may block the main process」是持久化判斷的法律條文（landscape §4）。
- **Redis Eviction / `maxmemory-policy` 官方文件** — <https://redis.io/docs/latest/develop/reference/eviction/>：八種 policy 與「預設 noeviction」那段。預設值是為資料庫設計的，不是為快取（landscape §4）。
- **Redis 8 GA 公告** — <https://redis.io/blog/redis-8-ga/>：I/O threading 重寫與「命令執行仍單執行緒」——確認「多執行緒只分擔網路、不分擔執行」這個本章核心事實（2026-06；landscape §4）。
- **Redis 改用 AGPLv3 公告** — <https://redis.io/blog/agplv3/> 與**授權頁** — <https://redis.io/legal/licenses/>：三授權的演進。「Redis 是 BSD」舊記憶的官方校正——SSPL/RSAL 非 OSI 開源、AGPLv3 是強 copyleft，選型前必讀（landscape §3b）。
- **Valkey 官方介紹** — <https://valkey.io/> 與 **Redis 的「What is Valkey」對照** — <https://redis.io/blog/what-is-valkey/>：fork 自 7.2.4、BSD、Linux Foundation 治理。理解為什麼你今天在雲端開「Redis 相容」服務，預設很可能是 Valkey（landscape §3b）。
- **Redis Commands — `SCAN` 一族** — <https://redis.io/docs/latest/commands/scan/>：`SCAN` 為什麼用游標分批、為什麼能不阻塞地取代 `KEYS`。把 `SCAN`/`SSCAN`/`HSCAN` 當預設、`KEYS` 當禁忌。

**ch18 — 雲端原語：SQS／SNS／Lambda／ALB／API Gateway／KrakenD**

- **Amazon SQS — Message quotas** — <https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html>：單則上限、visibility timeout、保留期等硬數字。搭配 [SQS increases maximum message payload size to 1 MiB](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib/)（2025-08-04）讀「256 KB → 1 MiB」這個老兵記憶校正——注意它是 **2025-08** 才變的（landscape §1）。
- **Amazon SNS — FIFO message delivery** — <https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html>：SNS FIFO 的排序與去重語意、能/不能直接投給哪些端點。搭配 [Introducing SNS FIFO](https://aws.amazon.com/blogs/aws/introducing-amazon-sns-fifo-first-in-first-out-pub-sub-messaging/)（landscape §2）。
- **AWS Lambda — payload size increase to 1 MB** — <https://aws.amazon.com/about-aws/whats-new/2025/10/aws-lambda-payload-size-256-kb-1-mb-invocations/>：非同步 payload 256 KB → 1 MB 的官方公告（2025-10-24）。確認「sync 仍 6 MB、async 升 1 MB」這個易過時的數字（landscape §17）。
- **AWS Lambda — Improving startup performance with SnapStart** — <https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html>：SnapStart 支援的 runtime（Java/Python/.NET）與**不支援 Node.js** 的一手出處——別把 SnapStart 當 Node 的解（landscape §17）。
- **API Gateway vs ALB** — [Amazon API Gateway FAQs](https://aws.amazon.com/api-gateway/faqs/) 的 throttling/auth 段，與 [Throttle requests to your REST APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)（token bucket 限流、~10,000 RPS 上限）——「per-request 治理 vs 純 L7 路由」分界的官方依據（landscape §18）。
- **KrakenD — Open Source** — <https://www.krakend.io/open-source/> 與 **Lura Project** — <https://github.com/luraproject/lura>：核心 framework「Lura」捐給 Linux Foundation（2021-05）的一手出處；搭配 [Linux Foundation 公告](https://www.linuxfoundation.org/press/press-release/open-source-api-gateway-krakend-becomes-linux-foundation-project) 讀「捐的是 framework、給的是 LF 不是 CNCF」（landscape §16）。

---

## Part V — 收官（ch19–20）

把名詞講成面試級敘事、收全書地圖、搭通往 AI Infra 的橋。這部沒有新連結，把前面四部的一手出處當「面試前重新查證清單」回收一遍——尤其那些會腐的事實。

- **面試前重新查證清單**：把每個敘事裡會腐的事實逐一查現況——Twilio Video 狀態（撤回 EOL、仍現役，landscape §6）、SQS 單則上限（已升到 1 MiB，§1）、Bull→BullMQ（§11）、Redis 授權與 Valkey（§3b）、Clinic.js 維護狀態（§12）、OAuth 2.1 仍是 draft（§14）、Lambda async payload 升 1 MB（§17）、Node active LTS 已是 24（§10）。這些就是 ch19 故障表那個「老化事實地雷」的拆彈清單。
- **本書 `_meta/landscape-2026-06.md`**：全書時效性事實基準，也是「帶走反射、現查事實」這個習慣的彈藥庫。三年後你對任何版本／狀態／授權／預設值起疑（你一定會），先翻它的對應節、看 `last_verified` 日期、過期就重新查證。這份檔案本身就是「老兵記憶會過時」這條暗線的具體防禦。
- **你自己的履歷（`Chewei_Chen_Resume.md`）**：最後一個延伸閱讀，是你開始的地方。回去重讀 ch01 你圈過的那三十幾個名詞——這次每一個，你都該看得見它底下的系統了。看不見的那幾個，就是這本書續集要挖的。

---

## 如果只讀三樣

時間有限就讀這三條。它們不是「最重要的知識」，是**最能改寫你既有記憶**的三條——讀完，你對全書三條暗線（交付不可靠、老兵記憶會過時、規格不是運氣）各有一個一手錨點。

1. **You Cannot Have Exactly-Once Delivery（Tyler Treat）** — <https://bravenewgeek.com/you-cannot-have-exactly-once-delivery/>：一篇講穿「exactly-once 交付不可能、你要的是 at-least-once + 冪等」。這是全書脊椎「交付軸」的世界觀，讀完你看 SQS、CronJob、delayed job、Lambda 的眼神都會變。（搭配 [Two Generals' Problem](https://en.wikipedia.org/wiki/Two_Generals%27_Problem) 看它的證明源頭。）
2. **Twilio — Twilio Video Will Remain a Standalone Product** — <https://www.twilio.com/en-us/changelog/-twilio-video-will-remain-a-standalone-product>：一頁官方撤回 EOL 的公告，是全書「老兵記憶會過時」暗線最戲劇的單一證據。它教你的不是 Twilio，是「凡是三年前學的版本／狀態，今天都要重查一次」這個反射。
3. **PostgreSQL Documentation — Transaction Isolation** — <https://www.postgresql.org/docs/current/transaction-iso.html>：官方白紙黑字說「Repeatable Read 其實是 Snapshot Isolation、不防 write skew」。一手規格如何顛覆你對隔離級別的直覺——讀它，你會養成「去查規格、別靠級別名字猜」的習慣，這正是本書最想留給你的反射。

---

## 跨書指引：四本姊妹書各補本書哪塊缺口

本書刻意只挖「機制與工程取捨」，四塊它不碰的東西，書架上各有一本專書接住。下面說清楚每本補的是什麼缺口、從本書哪一章接過去。

| 書 | id | 它補本書的哪塊缺口 | 從本書哪裡接過去 |
|---|---|---|---|
| **《等待的數學：排隊理論》** | queue | 本書只給過載/背壓/尾延遲的**工程直覺與取捨**；「ρ→1 為什麼爆炸、Little's Law、p99 為什麼那麼厚、retry storm 的雙穩態怎麼手算」這些**數學**全在那本。 | ch05（壓測為何低估尖峰）、ch14（背壓與 metastable 的數學）、ch15（尾延遲的形狀） |
| **《從後端到 AI Infra》** | aiib | 本書 ch20 只搭橋不展開的對岸：LLM serving、GPU、K8s GPU 排程、PagedAttention。你的五軸直覺對準它的每一格（KV cache routing ≈ session affinity、continuous batching ≈ 你的 batch 取捨、autoscaling GPU ≈ 你的過載防禦）。 | ch20（接上 AI Infra 的那座橋） |
| **《正常意外》** | fail | 本書的「故障模式與防禦」綁定你**自己**的系統；複雜系統崩壞的**跨領域通論**（緊耦合、複雜互動、為什麼大事故總是小故障疊起來、靜默故障的通用分類）在那本。 | ch05/ch08（雪崩與少數派故障）、ch14（過載級聯通論）、ch16（靜默故障為何最難抓） |
| **《把系統寫成定理：TLA+》** | tla | 本書一路用「最終一致 + 冪等」**繞過**的那層——分散式共識（Raft/Paxos、leader election、quorum）、分散式時鐘（Lamport/向量時鐘）、以及**證明**一個並發設計真的對。 | ch11（想證明一致性正確）、ch13（分散式時鐘與失敗偵測的形式化）、ch16（refresh 輪替的並發 race 證明） |

> 一句話收口：這四本不是「進階版本書」，是本書**畫出邊界、把球傳出去**的四個方向。本書負責把你履歷上每個名詞挖到「看得見底下的系統」；要再往下挖數學、AI Infra、故障通論、形式化證明，順著上表的接點走。
