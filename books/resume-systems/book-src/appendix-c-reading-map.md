# 附錄 C · 延伸閱讀總地圖

這是全書各條目「延伸閱讀」的彙整，把散落各處的外部來源依主題分群成一張地圖。想深入某個領域時，從這裡找權威起點：RFC 與規格、奠基論文、官方文件、權威工程文章。同一連結若在多處出現，只列在最相關的領域一次。

## A · 訊息交付與佇列

- [Apache Kafka — Message Delivery Semantics（官方）](https://kafka.apache.org/documentation/#semantics)：at-most/at-least/exactly-once 三種交付語意的權威定義出處。
- [You Cannot Have Exactly-Once Delivery（Brave New Geek）](https://bravenewgeek.com/you-cannot-have-exactly-once-delivery/)：為何網路上「交付」層面不可能真正 exactly-once 的清楚論證。
- [The Two Generals' Problem（Wikipedia）](https://en.wikipedia.org/wiki/Two_Generals%27_Problem)：交付不可靠的根本不可能性結果，exactly-once 真相的理論底座。
- [Exactly-Once Semantics Are Possible: Here's How Apache Kafka Does It（Confluent）](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-kafka-does-it/)：Kafka 如何用 idempotent producer + 交易把「處理」做成 exactly-once。
- [Designing robust and predictable APIs with idempotency（Stripe Engineering）](https://stripe.com/blog/idempotency)：冪等鍵在生產環境的設計，at-least-once 下避免重複處理的範本。
- [Implementing Stripe-like Idempotency Keys in Postgres（brandur.org）](https://brandur.org/idempotency-keys)：用 Postgres 落地冪等鍵的具體實作與狀態機。
- [RFC 9110 §9.2.2 Idempotent Methods（IETF）](https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods)：HTTP 方法冪等性的規格定義。
- [Stripe API — Idempotent requests（官方）](https://docs.stripe.com/api/idempotent_requests)：冪等鍵 header 與行為的 API 契約範例。
- [IETF draft — The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)：把冪等鍵標準化進 HTTP header 的草案。
- [Amazon SQS — Using the message deduplication ID（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html)：FIFO 佇列用 dedup ID 做去重的具體機制。
- [Apache Kafka — Idempotent Producer（KIP-98）](https://cwiki.apache.org/confluence/display/KAFKA/KIP-98+-+Exactly+Once+Delivery+and+Transactional+Messaging)：producer ID + 序號偵測重複的原始設計文件。
- [Bloom Filters by Example](https://llimllib.github.io/bloomfilter-tutorial/)：去重常用的機率資料結構，互動式理解誤判率取捨。
- [KIP-185: exactly once in order delivery per partition（官方）](https://cwiki.apache.org/confluence/display/KAFKA/KIP-185)：為何 idempotent producer 成為預設、以及它如何保 partition 內順序。
- [Aiven — Does Apache Kafka really preserve message ordering?](https://aiven.io/blog/kafka-real-ordering)：重試與 in-flight 設定如何破壞順序的實務剖析。
- [AWS — Amazon SQS FIFO queues（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues.html)：message group ID 作為排序單位的機制。
- [AWS Architecture Blog — Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)：full / equal / decorrelated jitter 的對比實驗，退避設計的經典。
- [Amazon Builders' Library — Timeouts, retries, and backoff with jitter](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)：重試放大與退避/jitter 的工程權衡。
- [AWS — Amazon SQS dead-letter queues（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)：DLQ 接住毒訊息的標準做法。
- [RabbitMQ — Dead Letter Exchanges（官方）](https://www.rabbitmq.com/docs/dlx)：RabbitMQ 的死信路由機制。
- [Confluent — Error Handling Patterns for Apache Kafka](https://www.confluent.io/blog/error-handling-patterns-in-kafka/)：retry topic 與 DLQ 的階梯式錯誤處理。
- [Hector Garcia-Molina, Kenneth Salem — Sagas（SIGMOD '87）](https://dl.acm.org/doi/10.1145/38713.38742)：saga 與補償交易的原始論文，跨服務一致性的源頭。
- [microservices.io — Pattern: Transactional outbox](https://microservices.io/patterns/data/transactional-outbox.html)：用 outbox 解 dual-write 問題的權威模式描述。
- [microservices.io — Pattern: Saga](https://microservices.io/patterns/data/saga.html)：choreography vs orchestration 兩種 saga 編排的取捨。
- [Microsoft — Saga distributed transactions](https://learn.microsoft.com/en-us/azure/architecture/reference-architectures/saga/saga)：補償語意的工程化參考架構。
- [Stripe Docs — Check webhook signatures](https://docs.stripe.com/webhooks/signature)：webhook 簽章驗證的具體做法。
- [GitHub Docs — Validating webhook deliveries](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)：用 `X-Hub-Signature-256` 驗證 webhook 來源。
- [webhooks.fyi](https://webhooks.fyi/)：webhook 安全與最佳實踐的目錄站。
- [OWASP — Server Side Request Forgery Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)：webhook 端點易成 SSRF 標的時的防護清單。
- [Protocol Buffers — Language Guide (proto 3)](https://protobuf.dev/programming-guides/proto3/)：field number、`reserved` 與向前後相容規則。
- [Apache Avro — Schema Resolution](https://avro.apache.org/docs/1.12.0/specification/#schema-resolution)：Avro 讀寫 schema 解析與演進規則。
- [Confluent — Schema Evolution and Compatibility](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)：BACKWARD/FORWARD/FULL 與 TRANSITIVE 相容模式定義。
- [Amazon SQS — message quotas（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html)：含 1 MiB 訊息上限等硬限制。
- [Amazon SQS — visibility timeout（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)：可見性逾時與重投語意。
- [Amazon SQS — payload size increases to 1 MiB（2025-08 公告）](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib/)：訊息上限調整的時效性來源。
- [SQS FIFO queues exactly-once processing（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html)：FIFO 的去重視窗與一次處理語意。
- [Amazon SQS — Standard vs FIFO queues（官方）](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-queue-types.html)：兩種佇列的保證差異總表。
- [Amazon SNS — message delivery for FIFO topics（官方）](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html)：SNS FIFO 的可投遞端點限制。
- [Amazon SNS FIFO topics → SQS Standard（2023-09 公告）](https://aws.amazon.com/about-aws/whats-new/2023/09/amazon-sns-fifo-topics-message-delivery-sqs-standard-queues/)：fan-out 端點組合的能力更新。
- [Introducing Amazon SNS FIFO（AWS Blog）](https://aws.amazon.com/blogs/aws/introducing-amazon-sns-fifo-first-in-first-out-pub-sub-messaging/)：SNS FIFO 的設計脈絡。
- [Confluent — Transactions and Exactly-Once Semantics（課程）](https://developer.confluent.io/courses/architecture/transactions/)：Kafka 交易與 EOS 的官方教學。
- [Exactly-once with Kafka transactions（Strimzi blog）](https://strimzi.io/blog/2023/05/03/kafka-transactions/)：在 Kubernetes 上跑 Kafka 交易的實作觀點。
- [RabbitMQ — Consumer Acknowledgements and Publisher Confirms（官方）](https://www.rabbitmq.com/docs/confirms)：ack 與 confirm 如何決定 RabbitMQ 的交付保證。
- [RabbitMQ Tutorials（官方）](https://www.rabbitmq.com/tutorials)：各 exchange 類型與路由模式的入門。
- [AMQP 0-9-1 Model Explained（官方）](https://www.rabbitmq.com/tutorials/amqp-concepts)：exchange/queue/binding 的協定模型。
- [BullMQ GitHub](https://github.com/taskforcesh/bullmq)：Redis-backed 延遲/任務佇列的現役維護版。
- [Bull GitHub（legacy）](https://github.com/OptimalBits/bull)：BullMQ 的前身，理解設計沿革。
- [BullMQ Documentation](https://docs.bullmq.io/)：任務佇列的官方文件與保證說明。
- [Redis — Pub/Sub（官方）](https://redis.io/docs/latest/develop/interact/pubsub/)：fire-and-forget 發布訂閱、無持久化的交付特性。
- [Redis — Streams intro（官方）](https://redis.io/docs/latest/develop/data-types/streams/)：持久化流與 consumer group 的對照面。
- [Redis — XREADGROUP（官方）](https://redis.io/docs/latest/commands/xreadgroup/)：Streams 的 consumer group 語意與 pending 列表。

## L · 資料同步與整合

- [PostgreSQL — Logical Replication（官方）](https://www.postgresql.org/docs/current/logical-replication.html)：邏輯複製作為增量同步的核心機制。
- [AWS DMS — full load + CDC（官方）](https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Task.CDC.html)：先全量再持續變更的遷移模式。
- [Debezium 官方文件](https://debezium.io/documentation/reference/stable/)：log-based CDC 的架構與各家連接器。
- [PostgreSQL — Logical Decoding 概念（官方）](https://www.postgresql.org/docs/current/logicaldecoding-explanation.html)：CDC 從 WAL 解出變更串流的底層原理。
- [Using logs to build a solid data infrastructure（Confluent / Kleppmann）](https://www.confluent.io/blog/using-logs-to-build-a-solid-data-infrastructure-or-why-dual-writes-are-a-bad-idea/)：為何 dual-write 是壞主意、log 作為單一變更來源。
- [Debezium — Outbox Event Router](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)：把 outbox 表變成事件流的具體轉換。
- [Conflict-free Replicated Data Types（Shapiro et al., 2011）](https://hal.inria.fr/inria-00609399/document)：CRDT 的原始形式化，無需協調即收斂的條件。
- [Dynamo: Amazon's Highly Available Key-value Store（DeCandia et al., 2007）](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)：版本向量、quorum、anti-entropy（Merkle tree）與 gossip 的奠基論文。
- [Dotted Version Vectors: Logical Clocks for Optimistic Replication](https://arxiv.org/abs/1011.5808)：版本向量的改良，避免 false conflict。
- [Apache Cassandra — Repair / anti-entropy（官方）](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/repair.html)：對帳/修副本差異的生產實作。
- [Merkle — A Digital Signature Based on a Conventional Encryption Function（1987）](https://link.springer.com/chapter/10.1007/3-540-48184-2_32)：雜湊樹的原始概念，對帳找差異的資料結構。
- [PostgreSQL — Logical Replication Restrictions（官方）](https://www.postgresql.org/docs/current/logical-replication-restrictions.html)：明列不複製 DDL 等異質同步陷阱。
- [AWS — Multi-Region application fundamentals（官方）](https://docs.aws.amazon.com/whitepapers/latest/aws-multi-region-fundamentals/aws-multi-region-fundamentals.html)：跨區複製的設計考量。

## B · 資料一致性、交易與複製

- [Martin Kleppmann — Designing Data-Intensive Applications](https://dataintensive.net/)：複製、分片、編碼演進、資料模型的權威整理，全書多處的母本。
- [Jepsen — Consistency Models](https://jepsen.io/consistency)：互動式一致性層級圖，光譜入門首選。
- [Aphyr — Strong consistency models](https://aphyr.com/posts/313-strong-consistency-models)：把一致性模型講清楚的經典長文。
- [Terry et al. — Session Guarantees for Weakly Consistent Replicated Data](https://www.cs.cornell.edu/courses/cs734/2000FA/cached%20papers/SessionGuaranteesPDIS_1.html)：讀己之寫/單調讀等會話保證的原始論文。
- [Shopify Engineering — Read Consistency with Database Replicas](https://shopify.engineering/read-consistency-database-replicas)：複製延遲下保讀己之寫的工程做法。
- [PostgreSQL — Hot Standby & replication（官方）](https://www.postgresql.org/docs/current/hot-standby.html)：讀副本與複製延遲的官方說明。
- [PostgreSQL — Transaction Isolation（官方）](https://www.postgresql.org/docs/current/transaction-iso.html)：隔離級別、異常與 SSI/retry 要求的權威來源。
- [Berenson et al. — A Critique of ANSI SQL Isolation Levels（1995）](https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/)：指出標準隔離異常定義歧義的經典。
- [Jepsen — PostgreSQL 12.3](https://jepsen.io/analyses/postgresql-12.3)：隔離異常的實測分析。
- [Jepsen — MySQL 8.0.34](https://jepsen.io/analyses/mysql-8.0.34)：MySQL RR 弱於 snapshot isolation 的實測。
- [PostgreSQL — Concurrency Control / MVCC（官方）](https://www.postgresql.org/docs/current/mvcc.html)：多版本並發控制的內部機制。
- [PostgreSQL — Routine Vacuuming（官方）](https://www.postgresql.org/docs/current/routine-vacuuming.html)：含 XID wraparound，MVCC 的維運代價。
- [MySQL — InnoDB Multi-Versioning（官方）](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html)：InnoDB 的 MVCC 實作。
- [MySQL — InnoDB Locking（官方）](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)：record/gap/next-key 鎖的機制。
- [MySQL — Deadlocks in InnoDB（官方）](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html)：死結偵測與 wait-for graph。
- [PostgreSQL — Explicit Locking（官方）](https://www.postgresql.org/docs/current/explicit-locking.html)：`SELECT FOR UPDATE` 等顯式鎖，跨 runtime 原子性也常引此。
- [MySQL — InnoDB Transaction Isolation Levels（官方）](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)：MySQL 各隔離級別的行為。
- [PostgreSQL wiki — Serializable Snapshot Isolation](https://wiki.postgresql.org/wiki/SSI)：SSI 與 next-key 路線的本質差異。
- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)：方法 safe/idempotent、條件請求 ETag/If-Match/412 的規格出處（REST 與樂觀並發共用）。
- [MDN — If-Match header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match)：用條件請求做樂觀並發控制的瀏覽器端說明。
- [AWS — DynamoDB Condition Expressions（官方）](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)：以 conditional write 實作 CAS 的範例。
- [PostgreSQL — B-Tree Indexes（官方）](https://www.postgresql.org/docs/current/btree.html)：B-tree 索引的結構與適用。
- [PostgreSQL — Using EXPLAIN（官方）](https://www.postgresql.org/docs/current/using-explain.html)：讀查詢計畫的權威指引。
- [Use The Index, Luke!](https://use-the-index-luke.com/)：B-tree 索引與查詢調校的權威入門站。
- [AWS — SaaS Tenant Isolation Strategies（官方）](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html)：pool/silo/bridge 多租戶隔離模型。
- [PostgreSQL — Row Security Policies（官方）](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)：用 RLS 做 row 級租戶隔離。
- [AWS Database Blog — Multi-tenant isolation with PostgreSQL RLS](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)：RLS 多租戶隔離的工程實作。
- [Consistent Hashing and Random Trees（Karger et al., 1997）](https://dl.acm.org/doi/10.1145/258533.258660)：一致性雜湊與分片路由的原始論文（ACM 版）。
- [Vitess — Sharding（官方）](https://vitess.io/docs/concepts/shard/)：MySQL 水平分片的工程化文件。
- [AWS — Saga pattern（官方）](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/saga.html)：補償交易在最終一致下的工程化說明。
- [Pat Helland — Life beyond Distributed Transactions](https://dl.acm.org/doi/10.1145/3012426.3025012)：為何用補償而非 2PC 的經典論述。
- [Werner Vogels — Eventually Consistent（ACM Queue）](https://queue.acm.org/detail.cfm?id=1466448)：最終一致性的權威科普。
- [Gilbert & Lynch — Brewer's Conjecture（2002）](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf)：CAP 定理的正式證明。
- [Abadi — Consistency Tradeoffs in Modern Distributed Database System Design](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)：PACELC 的原始論文，補上「無分區時延遲 vs 一致性」維度。
- [Brewer — CAP Twelve Years Later（InfoQ）](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)：CAP 提出者十二年後的修正與澄清。
- [Dan Pritchett — BASE: An Acid Alternative（ACM Queue）](https://queue.acm.org/detail.cfm?id=1394128)：BASE 與 ACID 的取捨原典。
- [PostgreSQL — ALTER TABLE（官方）](https://www.postgresql.org/docs/current/sql-altertable.html)：加/改/拆欄位的鎖與重寫行為，零停機遷移的依據。
- [Xata — Schema changes with expand-contract（pgroll）](https://xata.io/blog/pgroll-expand-contract)：expand-contract 不停機遷移的工具化做法。

> 書籍（無單一連結）：Martin Kleppmann《Designing Data-Intensive Applications》第 4–7 章對編碼演進、複製、分片、lost update/write skew 有系統性整理（見 dataintensive.net）。

## O · 儲存引擎與資料模型

- [Patrick O'Neil et al. — The Log-Structured Merge-Tree (1996)](https://www.cs.umb.edu/~poneil/lsmtree.pdf)：LSM-tree 的原始論文，寫放大/讀放大取捨的源頭。
- [Luo & Carey — LSM-based Storage Techniques: A Survey](https://arxiv.org/abs/1812.07527)：LSM 各種 compaction 與優化的現代綜述。
- [RocksDB Wiki — Overview](https://github.com/facebook/rocksdb/wiki/RocksDB-Overview)：主流 LSM 引擎的內部結構。
- [Cassandra — Unified Compaction Strategy](https://cassandra.apache.org/_/blog/Apache-Cassandra-5.0-Features-Unified-Compaction-Strategy.html)：compaction 策略對讀寫放大的影響。
- [C. Mohan et al. — ARIES (1992)](https://dl.acm.org/doi/10.1145/128765.128770)：WAL 與崩潰恢復的奠基論文。
- [PostgreSQL — Write-Ahead Logging (WAL)（官方）](https://www.postgresql.org/docs/current/wal-intro.html)：WAL 如何保證持久性與可恢復。
- [MySQL — InnoDB redo log（官方）](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html)：InnoDB 的預寫日誌實作。
- [Codd — A Relational Model of Data (1970)](https://dl.acm.org/doi/10.1145/362384.362685)：關係模型原典，SQL vs NoSQL 的對照基準。
- [MongoDB — Data Modeling Introduction（官方）](https://www.mongodb.com/docs/manual/data-modeling/)：文件模型的設計取捨。
- [Cassandra — Data Modeling（官方）](https://cassandra.apache.org/doc/latest/cassandra/developing/data-modeling/index.html)：寬欄模型「先問查詢再建表」的範式。
- [Manning, Raghavan & Schütze — Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/)：inverted index 機制的權威教材。
- [PostgreSQL — Full Text Search（官方）](https://www.postgresql.org/docs/current/textsearch.html)：在關聯式庫內做全文搜尋的機制。
- [Apache Lucene 官方文件](https://lucene.apache.org/core/)：inverted index 的工業實作。
- [GDPR Art. 17 — Right to erasure](https://gdpr-info.eu/art-17-gdpr/)：合規刪除的法源原文。
- [UK ICO — Right to erasure](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/)：被遺忘權的合規實作指引。
- [DynamoDB — Time to Live (TTL)（官方）](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)：TTL 過期刪除非即時的明確聲明。

## G · 快取與儲存

- [AWS — Database Caching Strategies Using Redis（白皮書）](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/welcome.html)：cache-aside / write-through 的對照。
- [Redis — Client-side caching（官方）](https://redis.io/docs/latest/develop/reference/client-side-caching/)：read-through、行程內快取與失效追蹤的機制。
- [Burton Bloom — Space/Time Trade-offs in Hash Coding (CACM 1970)](https://dl.acm.org/doi/10.1145/362686.362692)：Bloom filter 原始論文，擋快取穿透的工具。
- [Redis — Key eviction（官方）](https://redis.io/docs/latest/develop/reference/eviction/)：LRU/LFU/TTL 等驅逐策略與近似 LRU 機制。
- [Redis 8.6 — What's new（官方）](https://redis.io/docs/latest/develop/whats-new/8-6/)：`volatile-lrm`／`allkeys-lrm` 等新驅逐策略。
- [Redis — Persistence（官方）](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)：RDB / AOF / 混合與 fsync 策略的取捨。
- [Redis persistence demystified（antirez）](http://oldblog.antirez.com/post/redis-persistence-demystified.html)：作者本人對持久化取捨的深入解說。
- [RFC 5861 — HTTP Cache-Control Extensions for Stale Content](https://www.rfc-editor.org/rfc/rfc5861)：stale-while-revalidate / stale-if-error，多層快取優雅降級的規格。
- [Redis 官方文件](https://redis.io/docs/latest/)：資料結構、persistence、eviction、client-side caching 的總入口。
- [Redis 8 GA 公告](https://redis.io/blog/redis-8-ga/)：I/O threading 重寫與效能變化的時效性來源。
- [Redis 授權頁](https://redis.io/legal/licenses/)：RSALv2 / SSPLv1 / AGPLv3 三授權的官方說明。
- [Valkey 專案](https://valkey.io/)：Linux Foundation 的 BSD fork，授權變動後的替代選項。
- [Amazon S3 FAQs](https://aws.amazon.com/s3/faqs/)：物件大小、耐久度與一致性保證。
- [AWS — S3 Multipart upload limits（官方）](https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html)：分片大小與單 PUT 上限。
- [Amazon S3 max object size 50 TB（2025-12 公告）](https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/)：物件大小上限的時效性來源。

## C · 即時傳輸

- [RFC 6455 — The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455)：WebSocket 的 frame、ping-pong 與握手規格。
- [WHATWG HTML — Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)：SSE 的標準定義與自動重連語意。
- [MDN — Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)：SSE 的實作面說明。
- [MDN — Writing WebSocket servers](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers)：含連線生命週期與 frame 解析實作。
- [WebSocket.org — WebSocket Protocol guide](https://websocket.org/guides/websocket-protocol/)：協定機制的補充導讀。
- [W3C — WebTransport (Working Draft)](https://www.w3.org/TR/webtransport/)：SSE/long-poll 之外的新傳輸選項。
- [IETF — WebTransport over HTTP/3 (draft)](https://datatracker.ietf.org/doc/draft-ietf-webtrans-http3/)：WebTransport 底層協定草案。
- [MDN — WebTransport API](https://developer.mozilla.org/en-US/docs/Web/API/WebTransport_API)：WebTransport 的瀏覽器 API。
- [Socket.IO — Redis adapter](https://socket.io/docs/v4/redis-adapter/)：多節點 WebSocket 水平擴展的 backplane 具體實作。
- [Socket.IO — Redis Streams adapter](https://socket.io/docs/v4/redis-streams-adapter/)：以 Streams 做 backplane 的替代方案。
- [@socket.io/redis-adapter (npm)](https://www.npmjs.com/package/@socket.io/redis-adapter)：adapter 套件本體。
- [W3C — WebRTC: Real-Time Communication in Browsers](https://www.w3.org/TR/webrtc/)：媒體/傳輸/信令三塊的規格。
- [RFC 8445 — Interactive Connectivity Establishment (ICE)](https://www.rfc-editor.org/info/rfc8445/)：NAT 穿透的連線建立框架。
- [RFC 8489 — Session Traversal Utilities for NAT (STUN)](https://www.rfc-editor.org/rfc/rfc8489.html)：發現自身公網位址的協定。
- [RFC 8656 — Traversal Using Relays around NAT (TURN)](https://www.rfc-editor.org/rfc/rfc8656.html)：無法直連時的中繼協定。
- [coturn](https://github.com/coturn/coturn)：開源 TURN/STUN server。

## N · 網路與協定

- [RFC 9114 — HTTP/3](https://www.rfc-editor.org/rfc/rfc9114.html)：HTTP/3 over QUIC 的規格。
- [RFC 9000 — QUIC Transport](https://www.rfc-editor.org/rfc/rfc9000.html)：QUIC 傳輸層，消除 TCP 隊頭阻塞的底座。
- [RFC 9113 — HTTP/2](https://www.rfc-editor.org/rfc/rfc9113.html)：HTTP/2 多工與 header 壓縮。
- [Head-of-Line Blocking in QUIC and HTTP/3: The Details（Robin Marx）](https://calendar.perfplanet.com/2020/head-of-line-blocking-in-quic-and-http-3-the-details/)：把隊頭阻塞在各層的差異講透。
- [gRPC — Core concepts（官方）](https://grpc.io/docs/what-is-grpc/core-concepts/)：unary vs streaming、同步阻塞 vs 非同步 stub 的語意。
- [gRPC over HTTP/2 協定規格](https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md)：gRPC 如何映射到 HTTP/2 frame。
- [Protocol Buffers 官方文件](https://protobuf.dev/)：序列化格式與相容規則的入口。
- [PostgreSQL — Connection settings / max_connections（官方）](https://www.postgresql.org/docs/current/runtime-config-connection.html)：連線數上限與 pool 的關係。
- [HikariCP — About Pool Sizing](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)：連線池大小的經典分析（小池常更快）。
- [PgBouncer 官方文件](https://www.pgbouncer.org/)：外部連線池器的機制與模式。
- [Envoy — Load Balancing（官方）](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/overview)：演算法、outlier detection 與 panic threshold。
- [HAProxy — Load Balancing Algorithms](https://www.haproxy.com/glossary/what-are-load-balancing-algorithms)：各負載均衡演算法對照。
- [The Power of Two Choices in Randomized Load Balancing（Mitzenmacher, 1996）](https://www.eecs.harvard.edu/~michaelm/postscripts/tpds2001.pdf)：P2C 為何遠勝純隨機的理論。
- [RFC 8446 — TLS 1.3](https://www.rfc-editor.org/rfc/rfc8446.html)：TLS 1.3 握手與安全模型。
- [Cloudflare — A Detailed Look at RFC 8446 (TLS 1.3)](https://blog.cloudflare.com/rfc-8446-aka-tls-1-3/)：TLS 1.3 改了什麼的權威導讀。
- [Let's Encrypt — How It Works](https://letsencrypt.org/how-it-works/)：ACME 自動續簽憑證的機制。
- [Kubernetes — DNS for Services and Pods（官方）](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)：叢集內服務發現的 DNS 機制。
- [Consul — Service Discovery（官方）](https://developer.hashicorp.com/consul/docs/use-case/service-discovery)：服務發現的概念與實作。
- [RFC 2782 — DNS SRV 記錄](https://www.rfc-editor.org/rfc/rfc2782.html)：用 DNS 做服務發現的記錄型別。
- [Istio — Ambient Mode Reaches GA in v1.24](https://istio.io/latest/blog/2024/ambient-reaches-ga/)：service mesh 從 sidecar 走向 ambient 的時效性更新。
- [Envoy Proxy — Architecture Overview（官方）](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/intro/)：mesh 資料面代理的架構。
- [Istio — Dataplane modes (sidecar vs ambient)](https://istio.io/latest/docs/overview/dataplane-modes/)：兩種資料面模式的取捨。

## H · API 與閘道

- [Roy Fielding — Architectural Styles (REST, 2000)](https://ics.uci.edu/~fielding/pubs/dissertation/top.htm)：REST 風格的原始論文。
- [OpenAPI Specification 3.2.0](https://spec.openapis.org/oas/v3.2.0.html)：REST API 契約的規格標準。
- [RFC 8594 — The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594.html)：API 版本退役的標準化通知 header。
- [Pagination Done the PostgreSQL Way / no-offset（Markus Winand）](https://use-the-index-luke.com/no-offset)：keyset/seek 分頁為何勝過深 offset。
- [GraphQL Cursor Connections Specification](https://relay.dev/graphql/connections.htm)：cursor 分頁的事實標準。
- [GraphQL Specification](https://spec.graphql.org/)：GraphQL 的官方規格。
- [Microservices.io — API Gateway pattern](https://microservices.io/patterns/apigateway.html)：閘道與 BFF 模式的權威描述。
- [Sam Newman — Backends For Frontends](https://samnewman.io/patterns/architectural/bff/)：為不同前端裁切 API 的 BFF 模式。
- [AWS — Throttle requests to your REST APIs（官方）](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)：API Gateway 帳戶層限流的官方文件。
- [AWS — Choosing between REST APIs and HTTP APIs（官方）](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)：兩種 API Gateway 型態的取捨。
- [KrakenD — Open Source](https://www.krakend.io/open-source/)：無狀態聚合閘道的開源治理。
- [Linux Foundation — KrakenD Becomes Linux Foundation Project](https://www.linuxfoundation.org/press/press-release/open-source-api-gateway-krakend-becomes-linux-foundation-project)：治理變動的時效性來源。
- [Kong Gateway 官方文件](https://docs.konghq.com/gateway/)：外掛式 API 閘道的能力地圖。

## F · 身分與存取

- [RFC 6749 — The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749)：OAuth 2.0 授權框架的規格本體。
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)：在 OAuth 之上加認證層的 OIDC 規格。
- [NIST SP 800-162 — Guide to ABAC](https://csrc.nist.gov/pubs/sp/800/162/upd2/final)：屬性式存取控制（ABAC）的定義與考量。
- [RFC 7009 — OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009)：token 撤銷的標準端點。
- [RFC 7662 — OAuth 2.0 Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)：查 token 是否仍有效的內省端點。
- [RFC 8725 — JSON Web Token Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725)：JWT 常見坑與安全最佳實踐。
- [RFC 7515 — JSON Web Signature (JWS)](https://www.rfc-editor.org/rfc/rfc7515)：JWT 簽章層的規格。
- [RFC 7517 — JSON Web Key (JWK)](https://www.rfc-editor.org/rfc/rfc7517)：JWKS 公鑰集合的格式。
- [RFC 7518 — JSON Web Algorithms (JWA)](https://www.rfc-editor.org/rfc/rfc7518)：HS256/RS256 等簽章演算法定義。
- [RFC 7519 — JSON Web Token (JWT)](https://www.rfc-editor.org/rfc/rfc7519)：JWT 結構與 claims 的規格。
- [NIST CSRC — Role Based Access Control (RBAC) project](https://csrc.nist.gov/projects/role-based-access-control)：RBAC 的標準與模型。
- [Adding Attributes to Role-Based Access Control（Kuhn, Coyne, Weil, 2010）](https://csrc.nist.gov/files/pubs/journal/2010/06/adding-attributes-to-rolebased-access-control/final/docs/kuhn-coyne-weil-10.pdf)：RBAC 與 ABAC 融合的論文。
- [RFC 7636 — Proof Key for Code Exchange (PKCE)](https://www.rfc-editor.org/rfc/rfc7636)：public client 防授權碼攔截的擴充。
- [OAuth 2.1 — draft-ietf-oauth-v2-1（2026-06 仍為 draft）](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/)：把 OAuth 2.0 最佳實踐收斂成單一規格的草案。

## D · 並發與執行模型

- [Rob Pike — Concurrency is not Parallelism（Go blog）](https://go.dev/blog/waza-talk)：並發 ≠ 平行的經典講解。
- [Concurrency (computer science)（Wikipedia）](https://en.wikipedia.org/wiki/Concurrency_(computer_science))：並發概念的通用整理。
- [libuv — Design overview（官方）](https://docs.libuv.org/en/v1.x/design.html)：event loop 各 phase 的權威說明。
- [libuv — Thread pool（官方）](https://docs.libuv.org/en/v1.x/threadpool.html)：`UV_THREADPOOL_SIZE`（預設 4、最大 1024）與用途。
- [Node.js — The Node.js Event Loop（官方）](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)：單執行緒並發的相位與 nextTick。
- [Dan Kegel — The C10K problem](http://www.kegel.com/c10k.html)：I/O 模型總覽的經典文獻。
- [Linux epoll(7) man page](https://man7.org/linux/man-pages/man7/epoll.7.html)：非阻塞 I/O 事件通知的核心介面。
- [Efficient IO with io_uring（Jens Axboe）](https://kernel.dk/io_uring.pdf)：新一代非同步 I/O 的設計文件。
- [Node.js — worker_threads（官方）](https://nodejs.org/api/worker_threads.html)：CPU 密集工作如何不卡 event loop。
- [Node.js — cluster（官方）](https://nodejs.org/api/cluster.html)：多行程橫向利用多核。
- [Redis — Transactions（官方）](https://redis.io/docs/latest/develop/using-commands/transactions/)：WATCH/MULTI/EXEC 做跨呼叫原子性與 CAS。
- [C. A. R. Hoare — Communicating Sequential Processes（CACM 1978）](https://dl.acm.org/doi/10.1145/359576.359585)：CSP 原始論文，Go channel 的理論根。
- [Carl Hewitt et al. — A Universal Modular ACTOR Formalism（1973）](https://dl.acm.org/doi/10.5555/1624775.1624804)：actor model 的原始論文。
- [The Go Memory Model（官方）](https://go.dev/ref/mem)：GMP 排程、搶佔與記憶體可見性。

## E · 過載與流量控制

- [Reactive Streams 規格](https://www.reactive-streams.org/)：非阻塞背壓的標準介面 Publisher/Subscriber/Subscription。
- [AWS Builders' Library — Using load shedding to avoid overload](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)：goodput、佇列丟棄與優先級卸載的權衡。
- [Google SRE Book — Addressing Cascading Failures](https://sre.google/sre-book/addressing-cascading-failures/)：retry amplification、load shedding、graceful degradation 的章節。
- [Stripe — Scaling your API with rate limiters](https://stripe.com/blog/rate-limiters)：token bucket 在生產環境的分層限流。
- [Cloudflare — How we built rate limiting to millions of domains](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)：滑動窗近似計數的工程取捨。
- [Martin Fowler — CircuitBreaker](https://martinfowler.com/bliki/CircuitBreaker.html)：三態斷路器機制（源自 Nygard《Release It!》）。
- [Marc Brooker — Fixing retries with token buckets and circuit breakers](https://brooker.co.za/blog/2022/02/28/retries.html)：斷路器與 retry token bucket 如何配合。
- [Bronson et al. — Metastable Failures in Distributed Systems（HotOS 2021）](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf)：retry storm 走向 metastable 的形式化。
- [Marc Brooker — Metastability and Distributed Systems](https://brooker.co.za/blog/2021/05/24/metastable.html)：遲滯與正回饋迴圈的直覺。
- [M/M/1 queue（Wikipedia）](https://en.wikipedia.org/wiki/M/M/1_queue)：含 `E[N] = ρ/(1−ρ)`，理解 ρ→1 為何爆炸。
- [Little's Law（Wikipedia）](https://en.wikipedia.org/wiki/Little%27s_law)：`L = λW`，連結佇列長度與延遲的基本恆等式。

## P · 韌性與容錯

- [gRPC — Deadlines（官方）](https://grpc.io/docs/guides/deadlines/)：呼叫鏈傳播 deadline 的機制。
- [gRPC and Deadlines（gRPC blog）](https://grpc.io/blog/deadlines/)：deadline budget 為何要往下游傳。
- [Google SRE Book — Handling Overload](https://sre.google/sre-book/handling-overload/)：client-side throttling 與 retry budget。
- [Bulkhead pattern（Wikipedia）](https://en.wikipedia.org/wiki/Bulkhead_pattern)：艙壁隔離的概念。
- [Michael Nygard — Stability Patterns（《Release It!》講義 PDF）](https://cdn.oreillystatic.com/en/assets/1/event/79/Stability%20Patterns%20Presentation.pdf)：bulkhead、fallback、steady state 等韌性模式總覽。
- [Microsoft Azure — Bulkhead pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)：艙壁隔離的工程化說明。
- [Kubernetes — Configure Liveness, Readiness and Startup Probes（官方）](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)：三種探針的設定與語意。
- [Kubernetes — Liveness/Readiness/Startup Probes 概念（官方）](https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/)：探針的概念層說明。
- [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)：gRPC 服務健康檢查的標準協定。
- [Kubernetes — Pod Lifecycle（官方）](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)：graceful shutdown 的終止流程。
- [Google Cloud — Kubernetes best practices: terminating with grace](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-terminating-with-grace)：優雅關機的實務細節。
- [Fault tolerance — Graceful degradation（Wikipedia）](https://en.wikipedia.org/wiki/Fault_tolerance#Graceful_degradation)：降級作為容錯手段的概念。

## S · 效能與延遲

- [Understanding the Lambda execution environment lifecycle（AWS）](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)：冷啟動成因的官方說明。
- [Understanding and Remediating Cold Starts: An AWS Lambda Perspective](https://aws.amazon.com/blogs/compute/understanding-and-remediating-cold-starts-an-aws-lambda-perspective/)：冷啟動的量化與緩解。
- [Tiered Compilation in JVM（Baeldung）](https://www.baeldung.com/jvm-tiered-compilation)：JIT 暖機為何影響早期延遲。
- [How Tiered Compilation works in OpenJDK（Microsoft）](https://devblogs.microsoft.com/java/how-tiered-compilation-works-in-openjdk/)：分層編譯的內部機制。
- [The Tail at Scale — Dean & Barroso（CACM 2013, PDF）](https://www.barroso.org/publications/TheTailAtScale.pdf)：長尾延遲成因與對策的奠基論文。
- [The Tail at Scale — summary（the morning paper）](https://blog.acolyer.org/2015/01/15/the-tail-at-scale/)：上文的精煉導讀。
- [Solving the N+1 Problem with DataLoader（GraphQL.js docs）](https://www.graphql-js.org/docs/n1-dataloader/)：用 batching 消 N+1 查詢。
- [graphql/dataloader（GitHub）](https://github.com/graphql/dataloader)：per-tick batching 與 coalescing 的語意與實作。
- [golang.org/x/sync/singleflight](https://pkg.go.dev/golang.org/x/sync/singleflight)：request coalescing 合併重複呼叫的標準工具。
- [HikariCP — configuration knobs](https://github.com/brettwooldridge/HikariCP#configuration-knobs-baby)：連線池調校參數總覽。
- [PgBouncer — configuration / pooling modes](https://www.pgbouncer.org/config.html)：transaction/session/statement pooling 的取捨。

## M · 分散式系統核心

- [Fischer, Lynch, Paterson — Impossibility of Distributed Consensus with One Faulty Process（FLP, 1985）](https://dl.acm.org/doi/10.1145/3149.214121)：非同步系統共識的根本不可能性。
- [Lamport, Shostak, Pease — The Byzantine Generals Problem（1982）](https://dl.acm.org/doi/10.1145/357172.357176)：拜占庭故障與 n≥3m+1 下界。
- [Ongaro, Ousterhout — In Search of an Understandable Consensus Algorithm（Raft, 2014）](https://raft.github.io/raft.pdf)：Raft 共識的原始論文。
- [Raft 官方網站](https://raft.github.io/)：含視覺化與實作清單，觀察選舉與 log 複製。
- [Lamport — The Part-Time Parliament（Paxos, 1998）](https://lamport.azurewebsites.net/pubs/lamport-paxos.pdf)：Paxos 的原始論文。
- [Lamport — Paxos Made Simple（2001）](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf)：Paxos 的精簡重述。
- [Cassandra — Dynamo / consistency levels（官方）](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html)：quorum 在生產的可調呈現。
- [PostgreSQL — High Availability, Load Balancing, and Replication（官方）](https://www.postgresql.org/docs/current/high-availability.html)：單主同步/非同步複製的工程呈現。
- [Gray, Lamport — Consensus on Transaction Commit（2006）](https://lamport.azurewebsites.net/pubs/consensus-on-transaction-commit.pdf)：把原子提交與共識統一看待。
- [Skeen — Nonblocking Commit Protocols（SIGMOD 1981）](https://dl.acm.org/doi/10.1145/582318.582339)：3PC 的源頭。
- [X/Open XA 規格](https://pubs.opengroup.org/onlinepubs/009680699/toc.pdf)：分散式交易的標準介面。
- [Martin Kleppmann — How to do distributed locking](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)：Redlock 批評與 fencing token 的經典論述。
- [Redis — Distributed Locks / Redlock（官方）](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)：Redlock 演算法的描述。
- [ZooKeeper Recipes — Locks](https://zookeeper.apache.org/doc/current/recipes.html#sc_recipes_Locks)：用順序節點實作分散式鎖。
- [Lamport — Time, Clocks, and the Ordering of Events（CACM 1978）](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)：邏輯時鐘的原典。
- [Kulkarni, Demirbas et al. — Logical Physical Clocks（HLC, 2014）](https://cse.buffalo.edu/tech-reports/2014-04.pdf)：混合邏輯時鐘的論文。
- [Corbett et al. — Spanner: Google's Globally-Distributed Database（TrueTime, 2012）](https://research.google.com/archive/spanner-osdi2012.pdf)：用有界時鐘誤差換外部一致性。
- [Karger et al. — Consistent Hashing and Random Trees（STOC 1997）](https://www.akamai.com/site/en/documents/research-paper/consistent-hashing-and-random-trees-distributed-caching-protocols-for-relieving-hot-spots-on-the-world-wide-web-technical-publication.pdf)：consistent hashing 原典（Akamai 版 PDF）。
- [Thaler & Ravishankar — Using Name-Based Mappings（rendezvous/HRW）](https://www.eecs.umich.edu/techreports/cse/96/CSE-TR-316-96.pdf)：HRW 雜湊的論文。
- [Lamping & Veach — Jump Consistent Hash](https://arxiv.org/abs/1406.2294)：極省記憶體的一致性雜湊變體。
- [Demers et al. — Epidemic Algorithms for Replicated Database Maintenance（PODC 1987）](https://dl.acm.org/doi/10.1145/41840.41841)：anti-entropy / gossip 的原典。
- [Das, Gupta, Motivala — SWIM（2002）](https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf)：可擴展成員與故障偵測協定。
- [IANA Time Zone Database](https://www.iana.org/time-zones)：tz database 官方來源，含變更日誌。
- [RFC 3339 — Date and Time on the Internet](https://www.rfc-editor.org/rfc/rfc3339)：Internet 日期時間格式（含時區標註）。
- [TC39 Temporal proposal](https://tc39.es/proposal-temporal/docs/)：JavaScript DST-aware 的新日期時間 API。
- [Chandra & Toueg — Unreliable Failure Detectors for Reliable Distributed Systems（1996）](https://www.cs.utexas.edu/~lorenzo/corsi/cs380d/papers/p225-chandra.pdf)：失敗偵測的理論框架。
- [The φ Accrual Failure Detector（Hayashibara et al., 2004）](https://www.computer.org/csdl/proceedings-article/srds/2004/22390066/12OmNvT2phv)：以連續值取代二元判生死的偵測器。

## K · 系統設計與解耦

- [Martin Fowler — What do you mean by 'Event-Driven'?](https://martinfowler.com/articles/201701-event-driven.html)：event notification vs event-carried state transfer 等四種模式的權威拆解。
- [Martin Fowler — BoundedContext](https://martinfowler.com/bliki/BoundedContext.html)：DDD 的限界上下文，劃分耦合邊界。
- [Ben Stopford — Designing Event-Driven Systems（Confluent 免費電子書）](https://www.confluent.io/designing-event-driven-systems/)：以 log 為中心的事件驅動架構。
- [Martin Fowler — CQRS](https://martinfowler.com/bliki/CQRS.html)：讀寫分離的模式與適用邊界。
- [Martin Fowler — Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)：以不可變事件序列作為狀態來源。
- [Greg Young — CQRS Documents（PDF）](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)：CQRS 原創者的權威整理。
- [Temporal — Workflow Execution（官方）](https://docs.temporal.io/workflow-execution)：durable execution 的執行歷史、replay 與 determinism。
- [AWS Step Functions — Choosing workflow type（官方）](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html)：Standard vs Express 的交付語意與時長上限。

> 書籍（無單一連結）：Gregor Hohpe & Bobby Woolf《Enterprise Integration Patterns》（整合模式奠基）、Sam Newman《Building Microservices, 2nd ed.》（服務邊界與耦合）、Yourdon & Constantine《Structured Design》（耦合/內聚光譜原典）、Robert C. Martin《Clean Architecture》（依賴方向與穩定依賴原則）。

## J · 雲端與編排原語

- [AWS — Lambda SnapStart（官方）](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)：含支援 runtime 與限制，緩解冷啟動。
- [AWS — Lambda quotas（官方）](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)：timeout/memory/payload/併發上限。
- [AWS Lambda async payload 256 KB → 1 MB（2025-10 公告）](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-lambda-payload-size-256-kb-1-mb-invocations/)：payload 限制的時效性來源。
- [SnapStart for Python and .NET GA（AWS Blog）](https://aws.amazon.com/blogs/aws/aws-lambda-snapstart-for-python-and-net-functions-is-now-generally-available/)：SnapStart 支援語言的更新。
- [The Twelve-Factor App — VI. Processes](https://12factor.net/processes)：無狀態行程，serverless 的前提。
- [The Twelve-Factor App — IV. Backing services](https://12factor.net/backing-services)：把狀態外推到後端服務。
- [Kubernetes — CronJob（官方）](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)：含 concurrencyPolicy、100 次漏跑與非 exactly-once 聲明。
- [Kubernetes — Jobs（官方）](https://kubernetes.io/docs/concepts/workloads/controllers/job/)：CronJob 生出的 Job 的重試/完成語意。
- [Linux clock_gettime(2) — CLOCK_MONOTONIC vs CLOCK_REALTIME](https://man7.org/linux/man-pages/man2/clock_gettime.2.html)：單調鐘 vs 牆鐘，排程不能用牆鐘的原因。
- [Cron expression format（crontab(5)）](https://man7.org/linux/man-pages/man5/crontab.5.html)：cron 排程語法的權威定義。

## Q · 部署與發布

- [Kubernetes — Performing a Rolling Update（官方）](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)：滾動更新的教學。
- [Kubernetes — Deployment strategy / maxSurge / maxUnavailable（官方）](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy)：滾動參數如何控制更新節奏。
- [Martin Fowler — BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)：藍綠部署的模式與切換取捨。
- [Martin Fowler — CanaryRelease](https://martinfowler.com/bliki/CanaryRelease.html)：金絲雀發布逐步放量的模式。
- [namespaces(7) — Linux manual page](https://man7.org/linux/man-pages/man7/namespaces.7.html)：容器隔離的 namespace 機制。
- [cgroups(7) — Linux manual page](https://man7.org/linux/man-pages/man7/cgroups.7.html)：容器資源限制的 cgroup 機制。
- [Open Container Initiative — Runtime Specification](https://github.com/opencontainers/runtime-spec)：容器執行期的標準介面。
- [Docker — Seccomp security profiles（官方）](https://docs.docker.com/engine/security/seccomp/)：用 seccomp 限制容器系統呼叫。
- [Kubernetes — Pods（官方）](https://kubernetes.io/docs/concepts/workloads/pods/)：最小調度單位的概念。
- [Kubernetes — Service（官方）](https://kubernetes.io/docs/concepts/services-networking/service/)：服務抽象與流量路由。
- [Kubernetes — Horizontal Pod Autoscaling（官方）](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)：含自動擴縮演算法。
- [Terraform — What is Infrastructure as Code（官方）](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code)：宣告式 IaC 的核心概念。
- [OpenTofu](https://opentofu.org/)：MPL 授權的 Terraform fork，授權變動後的替代。
- [Terraform — Managing resource drift（官方）](https://developer.hashicorp.com/terraform/tutorials/state/resource-drift)：狀態漂移的偵測與調和。
- [Kubernetes — Declarative Management of Objects（官方）](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/)：宣告式 apply 的冪等性。
- [The Twelve-Factor App](https://12factor.net/)：雲原生應用的十二要素方法論。
- [Twelve-Factor App Methodology is now Open Source（2024-11 公告）](https://12factor.net/blog/open-source-announcement)：方法論開源與更新的時效性來源。
- [twelve-factor/twelve-factor（GitHub）](https://github.com/twelve-factor/twelve-factor)：更新版方法論的開發中倉庫。
- [The Twelve-Factor App — III. Config](https://12factor.net/config)：把 config 放進環境變數。
- [Kubernetes — Secrets（官方）](https://kubernetes.io/docs/concepts/configuration/secret/)：含「預設僅 base64、需另開 encryption at rest」的關鍵限制。
- [Kubernetes — Encrypting Confidential Data at Rest（官方）](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)：靜態加密的設定。
- [OWASP — Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)：機密管理的防護清單。

## I · 可觀測性與品質

- [OpenTelemetry — Observability primer](https://opentelemetry.io/docs/concepts/observability-primer/)：metric/log/trace 三本柱的概念入門。
- [OpenTelemetry — Signals](https://opentelemetry.io/docs/concepts/signals/)：三種訊號的定義與關係。
- [Google SRE Book — Monitoring Distributed Systems](https://sre.google/sre-book/monitoring-distributed-systems/)：四個黃金訊號與症狀 vs 原因告警的出處。
- [OpenTelemetry — Sampling](https://opentelemetry.io/docs/concepts/sampling/)：head vs tail 取樣對聚合與追蹤的影響。
- [Prometheus — Instrumentation best practices](https://prometheus.io/docs/practices/instrumentation/)：為何計數要用 counter 埋點。
- [Prometheus — Histograms and summaries](https://prometheus.io/docs/practices/histograms/)：分位數估計的前提，為何不能平均 p99。
- [Prometheus — Naming and labels](https://prometheus.io/docs/practices/naming/)：標籤基數爆炸的警告。
- [Prometheus — do not overuse labels](https://prometheus.io/docs/practices/instrumentation/#do-not-overuse-labels)：高基數標籤的反模式。
- [OpenTelemetry — Metrics data model](https://opentelemetry.io/docs/specs/otel/metrics/data-model/)：attributes 與 cardinality 的資料模型。
- [Google SRE Book — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)：SLI/SLO/error budget 的定義。
- [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/)：含 burn-rate alerting 的落地。
- [Google SRE Workbook — Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/)：multi-window burn-rate 告警設計。
- [Rob Ewaschuk — My Philosophy on Alerting](https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit)：症狀告警原則的原典。
- [W3C — Trace Context](https://www.w3.org/TR/trace-context/)：跨服務傳播 trace context 的標準。
- [OpenTelemetry — Traces / Context propagation](https://opentelemetry.io/docs/concepts/signals/traces/)：span 與 context 傳播的概念。
- [Sigelman et al. — Dapper（2010）](https://research.google/pubs/pub36356/)：分散式追蹤基礎設施的原典。
- [Gil Tene — How NOT to Measure Latency](https://www.infoq.com/presentations/latency-response-time/)：coordinated omission 的原始論述。
- [HdrHistogram](https://github.com/HdrHistogram/HdrHistogram)：高動態範圍直方圖，含 coordinated omission 校正。
- [wrk2](https://github.com/giltene/wrk2)：constant throughput、正確延遲量測的 wrk 變體。
- [Martin Fowler — Test Pyramid](https://martinfowler.com/articles/practical-test-pyramid.html)：測試金字塔的權威整理。
- [Martin Fowler — Contract Test](https://martinfowler.com/bliki/ContractTest.html)：consumer-driven contract testing 的概念。
- [Pact 官方文件](https://docs.pact.io/)：契約測試的工具實作。
- [Kent C. Dodds — The Testing Trophy](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)：對金字塔的另一種權衡觀點。
- [Fluent Bit 官方文件](https://docs.fluentbit.io/manual)：輕量日誌採集器的能力。
- [Fluent Bit vs Fluentd（官方對比）](https://docs.fluentbit.io/manual/about/fluentd-and-fluent-bit)：兩者定位與選型。
- [Clinic.js（GitHub）](https://github.com/clinicjs/node-clinic)：Node 診斷工具，含維護狀態聲明。
- [Grafana k6 官方文件](https://grafana.com/docs/k6/latest/)：腳本化負載測試工具。
- [Vegeta（GitHub）](https://github.com/tsenart/vegeta)：constant-rate（開放模型）負載測試工具。
- [Snyk 官方網站](https://snyk.io/)：相依掃描與漏洞偵測的產品與定價。

## V · 營運與事故文化

- [John Allspaw — Blameless PostMortems and a Just Culture（Etsy, 2012）](https://www.etsy.com/codeascraft/blameless-postmortems)：無咎事後檢討的原始論述。
- [Google SRE Book — Postmortem Culture](https://sre.google/sre-book/postmortem-culture/)：從失敗學習的文化機制。
- [PagerDuty Incident Response Documentation](https://response.pagerduty.com/)：事故應變流程的公開參考。
- [Google SRE Book — Embracing Risk](https://sre.google/sre-book/embracing-risk/)：用 error budget 把可靠性當可談判的資源。
- [Google SRE Workbook — Error Budget Policy](https://sre.google/workbook/error-budget-policy/)：error budget 當談判工具的政策範本。
- [DORA — software delivery performance metrics](https://dora.dev/guides/dora-metrics/)：四指標的官方定義。
- [DORA — A history of DORA's metrics](https://dora.dev/insights/dora-metrics-history/)：指標演進的脈絡。
- [Forsgren, Humble, Kim — Accelerate](https://itrevolution.com/product/accelerate/)：DORA 四指標背後的實證研究。
- [Google — Code Review Developer Guide](https://google.github.io/eng-practices/review/)：審什麼、怎麼給回饋的權威指引（與 AI 工作流的人類審查原則共用）。
- [Modern Code Review: A Case Study at Google（Sadowski et al., ICSE-SEIP 2018）](https://research.google/pubs/modern-code-review-a-case-study-at-google/)：大型組織 code review 的實證研究。
- [Trunk Based Development](https://trunkbaseddevelopment.com/)：主幹開發的權威站點。
- [Martin Fowler — Patterns for Managing Source Code Branches](https://martinfowler.com/articles/branching-patterns.html)：分支策略的系統性整理。
- [Vincent Driessen — A successful Git branching model（git-flow）](https://nvie.com/posts/a-successful-git-branching-model/)：git-flow 原文，含作者後來對持續交付的註記。

## T · 工程實踐與團隊推動

- [Martin Fowler — Strangler Fig Application](https://martinfowler.com/bliki/StranglerFigApplication.html)：漸進替換而非一次切換的思維底層。
- [Martin Fowler — Parallel Change](https://martinfowler.com/bliki/ParallelChange.html)：expand-contract 的記述與定名，用於流程與資料遷移。
- [Microsoft Azure — Strangler Fig pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig)：絞殺榕模式的工程化步驟說明。
- [Software Engineering at Google（abseil.io）](https://abseil.io/resources/swe-book/)：大型組織讓慣例落地、設計文件運作的文化與流程章節。
- [Spotify — Golden Paths to Solve Fragmentation](https://engineering.atspotify.com/2020/08/how-we-use-golden-paths-to-solve-fragmentation-in-our-software-ecosystem/)：golden path / 鋪路概念的原始出處。
- [Netflix Technology Blog](https://netflixtechblog.com/)：自由與責任文化下 paved road 引導而非強制的脈絡。
- [Backstage](https://backstage.io/)：Spotify 開源、捐給 CNCF 的開發者入口，golden path 的工具載體。
- [Oxide Computer — RFD Process](https://rfd.shared.oxide.computer/rfd/0001)：一套公開可參考的工程 RFC 流程實作。
- [RFC 7282 — On Consensus and Humming in the IETF](https://www.rfc-editor.org/rfc/rfc7282)：「徵求意見」傳統與「粗略共識」判準的源頭。
- [Google — Engineering Practices Documentation](https://google.github.io/eng-practices/)：code review 與自動化把關如何分工。
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)：可被 CI 自動強制的 commit message 慣例規格。
- [pre-commit framework](https://pre-commit.com/)：跨語言的提交前檢查框架。
- [Michael Nygard — Documenting Architecture Decisions（2011）](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)：ADR 的原始提案。
- [Martin Fowler — Architecture Decision Record](https://martinfowler.com/bliki/ArchitectureDecisionRecord.html)：ADR 的概念與適用。
- [adr.github.io](https://adr.github.io/)：ADR 社群索引與多種範本（Nygard、MADR…）。
- [Ward Cunningham — The WyCash Portfolio Management System（1992）](https://c2.com/doc/oopsla92.html)：技術債比喻的原始出處。
- [Martin Fowler — Technical Debt](https://martinfowler.com/bliki/TechnicalDebt.html)：技術債概念的整理。
- [Martin Fowler — Technical Debt Quadrant](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html)：技術債四象限分類（deliberate/inadvertent × prudent/reckless）。
- [Fred Brooks — No Silver Bullet](https://en.wikipedia.org/wiki/No_Silver_Bullet)：本質複雜度無法被工具消除，框定 AI 能與不能省的部分。
- [Hyrum Wright — Large-Scale Changes（SWE at Google ch.22）](https://abseil.io/resources/swe-book/html/ch22.html)：確定性大規模變更的分批與驗證實務。
- [Refactoring at Scale（Maude Lemaire, O'Reilly）](https://www.oreilly.com/library/view/refactoring-at-scale/9781492075523/)：大規模重構的分批、驗證、回退策略。

## U · 工程判斷與決策

- [Amazon 2015 Letter to Shareholders](https://s2.q4cdn.com/299287126/files/doc_financials/annual/2015-Letter-to-Shareholders.PDF)：one-way / two-way doors 決策框架的原文。
- [Martin Fowler — Sacrificial Architecture](https://martinfowler.com/bliki/SacrificialArchitecture.html)：刻意設計成可丟棄的系統。
- [xz Utils 後門 CVE-2024-3094（CISA 通報）](https://www.cisa.gov/news-events/alerts/2024/03/29/reported-supply-chain-compromise-affecting-xz-utils-data-compression-library-cve-2024-3094)：供應鏈攻擊解剖，自建 vs 採用的風險案例。
- [OWASP — Software Component Verification Standard](https://owasp.org/www-project-software-component-verification-standard/)：相依盡職調查的框架。
- [Martin Fowler — Yagni](https://martinfowler.com/bliki/Yagni.html)：YAGNI 的精準定義與適用邊界。
- [Knuth — Structured Programming with go to Statements（1974）](https://dl.acm.org/doi/10.1145/356635.356640)：「過早最佳化是萬惡之源」的原文脈絡。
- [Dan McKinley — Choose Boring Technology](https://mcfunley.com/choose-boring-technology)：「無聊技術」與創新額度的經典論述。
- [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar)：技術成熟度與採用建議的持續評估框架。
- [The Fallacies of Distributed Computing（Wikipedia 整理）](https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing)：為何對網路錯誤不處理會悄悄壞掉。
- [Joe Duffy — The Error Model](http://joeduffyblog.com/2016/02/07/the-error-model/)：recoverable error vs bug 的分類哲學長文。
- [Google DORA — 2024 research on AI in software development](https://dora.dev/research/2024/dora-report/)：AI 對交付效能與品質的實證影響。
- [Jeff Dean / Peter Norvig — Latency Numbers Every Programmer Should Know（互動版）](https://colin-scott.github.io/personal_website/research/interactive_latency.html)：量級估算的錨點數字，可看隨年份演進。
- [Simon Eskildsen — napkin-math](https://github.com/sirupsen/napkin-math)：持續更新的當代硬體吞吐/成本錨點。
