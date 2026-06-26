# 附錄 B · 延伸閱讀地圖

這是全書各章「延伸閱讀」的彙整，把散落各章的外部來源收攏成一張地圖。想往下深掘某個主題時，從這裡找權威起點：RFC 與規格、奠基論文、官方文件、權威工程文章。**只收外部來源，不指向任何書。** 同一連結若在多章出現，只列在最相關的章一次。各章順序與正文相同，依 Part 與主題分群。

## Part 0 · 兩副透鏡——判斷與推動

### 推動採用：誘因、轉換成本與信任

- [Spotify Engineering, *How We Use Golden Paths to Solve Fragmentation in Our Software Ecosystem*](https://engineering.atspotify.com/2020/08/how-we-use-golden-paths-to-solve-fragmentation-in-our-software-ecosystem)：golden path 的原始脈絡，含「rumour-driven development」的問題描述
- [The Paved Road at Netflix](https://netflixtechblog.com/how-we-build-code-at-netflix-c5d9bd727f15)："freedom and responsibility" 文化下「引導而非強制」的採用哲學
- [Everett M. Rogers, *Diffusion of Innovations*](https://en.wikipedia.org/wiki/Diffusion_of_innovations)：採用者五分類與 S 形擴散曲線的奠基之作，1962
- [Geoffrey A. Moore, *Crossing the Chasm*](https://en.wikipedia.org/wiki/Crossing_the_Chasm)：早期採用者與早期多數之間那道信任鴻溝
- [Martin Fowler, *bliki: Strangler Fig*](https://martinfowler.com/bliki/StranglerFigApplication.html)：漸進替換而非一次切換的思維底層
- [*Conventional Commits 1.0.0*](https://www.conventionalcommits.org/en/v1.0.0/)：一個可被 commit-lint／CI 自動強制的 commit message 慣例規格

### 把決定寫下來：RFC、設計文件與 ADR

- [Michael Nygard, "Documenting Architecture Decisions"](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)：ADR 的原始出處與五欄模板，2011-11-15
- [Joel Parker Henderson, *architecture-decision-record*](https://github.com/joelparkerhenderson/architecture-decision-record)：ADR 模板與多種變體的彙整 repo
- [IETF, RFC 7282, "On Consensus and Humming in the IETF"](https://www.rfc-editor.org/rfc/rfc7282)：粗略共識與「不靠表決」的判準，2014-06
- [Oxide Computer, "RFD 1: Requests for Discussion"](https://rfd.shared.oxide.computer/rfd/0001)：一套公開、可參考的工程 RFC 流程實作，含 prediscussion/discussion/published/committed 狀態機
- [David D. Clark, "A Cloudy Crystal Ball — Visions of the Future"](https://groups.csail.mit.edu/ana/People/DDC/future_ietf_92.pdf)："rough consensus and running code" 信條的原始演講，IETF 24, 1992

### 鋪路：讓對的做法最省力

- [Dianne Marsh (Netflix), *The Paved Road at Netflix: At the junction of freedom and responsibility*, OSCON 2017](https://www.slideshare.net/diannemarsh/the-paved-road-at-netflix)：paved road 在「自由與責任」文化下如何引導而非強制
- [Backstage](https://backstage.io/docs/overview/what-is-backstage/)：Spotify 開源、現為 CNCF incubating 專案的內部開發者入口；Software Templates/Scaffolder 是 golden path 的工具載體
- [ESLint, *Bulk Suppressions*](https://eslint.org/blog/2025/04/introducing-bulk-suppressions/)：v9.24.0 內建的 baseline 機制，讓新規則只對新程式碼生效
- [ESLint, *Suppressions* 官方文件](https://eslint.org/docs/latest/use/suppressions)：`--suppress-all` / `--suppress-rule` 用法與 `eslint-suppressions.json` 格式
- [pre-commit framework 官方文件](https://pre-commit.com/)：跨語言的提交前檢查框架；本機 hook 為便利、非保證

### 漸進式遷移與淘汰：strangler 與 expand-contract

- [Martin Fowler, *bliki: Parallel Change*](https://martinfowler.com/bliki/ParallelChange.html)：expand / migrate / contract 三段式的記述與定名，2014
- [Martin Fowler, *bliki: Branch By Abstraction*](https://martinfowler.com/bliki/BranchByAbstraction.html)：在程式碼內部漸進替換核心元件的做法
- [Microsoft Azure Architecture Center, *Strangler Fig pattern*](https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig)：工程化、附四相位 facade 路由與 anti-corruption layer 的模式說明
- [Microsoft Azure Architecture Center, *Anti-corruption Layer pattern*](https://learn.microsoft.com/en-us/azure/architecture/patterns/anti-corruption-layer)：並存期新舊系統對話時，隔離舊語意滲透的轉譯層
- [Paul Hammant, *Legacy Application Strangulation: Case Studies*](https://paulhammant.com/2013/07/14/legacy-application-strangulation-case-studies/)：真實系統絞殺遷移的案例彙整

### 技術債：量化、排序、何時還

- [Ward Cunningham, *The WyCash Portfolio Management System*](https://c2.com/doc/oopsla92.html)：1992 OOPSLA experience report，技術債比喻的原始出處與原話
- [Martin Fowler, *Technical Debt*](https://martinfowler.com/bliki/TechnicalDebt.html)：bliki，比喻的現代重述
- [Martin Fowler, *Technical Debt Quadrant*](https://martinfowler.com/bliki/TechnicalDebtQuadrant.html)：蓄意/無心 × 輕率/審慎四象限
- [Jean-Louis Letouzey, *The SQALE Method for Evaluating Technical Debt*](https://ieeexplore.ieee.org/document/6225997)：2010，debt ratio 量化方法的原始論文
- [Sonar, *Understanding measures and metrics*](https://docs.sonarsource.com/sonarqube-server/user-guide/code-metrics/metrics-definition)：SonarQube 的 SQALE debt ratio 公式、預設 30 min/line、A–E 評級門檻
- [Scaled Agile Framework, *WSJF (Weighted Shortest Job First)*](https://framework.scaledagile.com/wsjf)：成本延遲 ÷ 工作量的排序方法，源自 Don Reinertsen

### 與 AI 協作：委派、驗收與信任邊界

- [Fred Brooks, *No Silver Bullet: Essence and Accident in Software Engineering*](https://worrydream.com/refs/Brooks_1986_-_No_Silver_Bullet.pdf)：IFIP 1986；IEEE Computer 1987——「本質複雜度無法被工具消除」的經典論證，框定了 AI 能省與不能省的邊界
- [Google Engineering Practices, *Code Review Developer Guide*](https://google.github.io/eng-practices/review/)：與工具無關的人類審查原則：審查者建立獨立心智模型、作者非審查者
- [Martin Fowler, *Refactoring with Codemods to Automate API Changes*](https://martinfowler.com/articles/codemods-api-refactoring.html)：codemod／AST 改寫如何提供「規則對則結果對」的確定性保證
- [Sonar, *State of Code Report 2026 — the AI "Verification Gap"*](https://www.sonarsource.com/company/press-releases/sonar-data-reveals-critical-verification-gap-in-ai-coding/)：96% 不完全信任 AI 產出、僅 48% 每次驗證的調查數據；"verification debt" 概念

### 兩扇門：可逆與不可逆決策

- [Martin Fowler, *Sacrificial Architecture*](https://martinfowler.com/bliki/SacrificialArchitecture.html)：刻意設計成可丟棄、便於替換的系統
- [Uber Engineering, *Introducing Piranha: An Open Source Tool to Automatically Delete Stale Code*](https://www.uber.com/en-US/blog/piranha/)：自動清除過期 feature flag 的工具與規模數字
- [uber/piranha](https://github.com/uber/piranha)：Piranha 原始碼

### 簡單性與過度工程：YAGNI 的兩面

- [Donald E. Knuth, *Structured Programming with go to Statements*, ACM Computing Surveys 6(4):261–301, 1974](https://dl.acm.org/doi/10.1145/356635.356640)：「過早最佳化是萬惡之源」的完整脈絡，含「關鍵 3%」那半句，p. 268
- [Sandi Metz, *The Wrong Abstraction*](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)：「重複遠比錯的抽象便宜」與「最快的前進是後退」
- [Rule of three (computer programming)](https://en.wikipedia.org/wiki/Rule_of_three_(computer_programming))：三的法則的由來，Don Roberts 與 Fowler 的 Refactoring
- [Gall's Law / *Systemantics*, John Gall, 1975](https://en.wikipedia.org/wiki/Systemantics)：複雜系統必從能運作的簡單系統演化而來
- [Ron Jeffries, *YAGNI, yes. Skimping, no. Technical Debt? Not even.*](https://ronjeffries.com/articles/019-01ff/iter-yagni-skimp/)：YAGNI 的常見誤用，以及它與偷工減料的差別

### 自建還是採用：相依的長期成本

- [npm left-pad incident](https://en.wikipedia.org/wiki/Npm_left-pad_incident)：一個十一行套件如何癱瘓半個 JavaScript 生態
- ["Shai-Hulud" npm 自我複製蠕蟲](https://www.cisa.gov/news-events/alerts/2025/09/23/widespread-supply-chain-compromise-impacting-npm-ecosystem)：CISA 2025-09 通報；首例自動傳播的 npm 供應鏈攻擊
- [Heartbleed](https://en.wikipedia.org/wiki/Heartbleed)：被半個網際網路依賴、卻幾乎無人資助維護的 OpenSSL
- [Core Infrastructure Initiative](https://en.wikipedia.org/wiki/Core_Infrastructure_Initiative)：Heartbleed 之後，資助「大家都用、沒人在養」的關鍵開源
- [GNU AGPLv3 授權全文](https://www.gnu.org/licenses/agpl-3.0.html)：第 13 條：網路使用如何觸發 copyleft
- [OWASP Software Component Verification Standard](https://owasp.org/www-project-software-component-verification-standard/)：相依盡職調查的框架

### 技術選型：評估、PoC 與退場成本

- [Dan McKinley, *Choose Boring Technology*](https://mcfunley.com/choose-boring-technology)：創新額度與「故障模式被充分理解」的經典論述
- [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar)：Adopt / Trial / Assess / Hold 四環的技術成熟度評估框架
- [ThoughtWorks Technology Radar FAQ](https://www.thoughtworks.com/en-us/radar/faq)：四環各自的確切含義與 blip 移動規則
- [Jan Sauermann et al., *Résumé-Driven Development: A Definition and Empirical Characterization*, ICSE-SEIS 2021](https://dl.acm.org/doi/10.1109/ICSE-SEIS52602.2021.00011)：履歷驅動開發的學術定義與實證

### 錯誤處理哲學：fail-fast、傳播、重試還是降級

- [L. Peter Deutsch / James Gosling 等, *The Fallacies of Distributed Computing*](https://en.wikipedia.org/wiki/Fallacies_of_distributed_computing)：為什麼把網路錯誤當成不會發生會悄悄壞掉；Sun Microsystems 起源、Deutsch 1994 整理、Gosling 1997 補第八條，Wikipedia 整理版
- [Jim Shore, "Fail Fast", IEEE Software, 2004](https://martinfowler.com/ieeeSoftware/failFast.pdf)：fail-fast 作為明確工程主張的原始短文
- [Joe Duffy, *The Error Model*](http://joeduffyblog.com/2016/02/07/the-error-model/)：recoverable error 與 bug 的分類哲學長文，Midori 語言的錯誤模型設計
- [RFC 9110, *HTTP Semantics*, §9.2.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)：idempotent 方法的定義，與「通訊失敗時哪些請求可自動重試」

### 信封背面：量級估算與容量直覺

- [Jeff Dean / Peter Norvig, *Latency Numbers Every Programmer Should Know*](https://colin-scott.github.io/personal_website/research/interactive_latency.html)：互動版，可看數字隨年份演進
- [jboner, *Latency Numbers Every Programmer Should Know*](https://gist.github.com/jboner/2841832)：最廣為流傳的原始 gist
- [Simon Eskildsen, *napkin-math*](https://github.com/sirupsen/napkin-math)：持續更新的當代硬體吞吐／成本錨點數字，含「實際可得 vs 裝置上限」的誠實對照
- [KIOXIA CM9 Series PCIe 5.0 NVMe SSD 規格](https://americas.kioxia.com/en-us/business/ssd/enterprise-ssd/cm9-r.html)：企業級隨機讀 IOPS 數字來源
- [DDR5 SDRAM](https://en.wikipedia.org/wiki/DDR5_SDRAM)：每通道頻寬與資料率，Wikipedia 整理

### AI 怎麼移動判斷的天平

- [DORA, *Accelerate State of DevOps Report 2024*](https://dora.dev/research/2024/dora-report/)：AI 採用與交付吞吐 −1.5%、穩定性 −7.2% 的原始研究
- [Google Cloud, *Announcing the 2025 DORA Report: State of AI-assisted Software Development*](https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report)：2025 年版：吞吐關係由負轉正、穩定性仍負、「AI 是放大器」
- [Spracklen et al., *We Have a Package for You! A Comprehensive Analysis of Package Hallucinations by Code Generating LLMs*, USENIX Security 2025](https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen)：19.7% 套件為幻覺、商用 5.2% / 開源 21.7%
- [CISA, *Reported Supply Chain Compromise Affecting XZ Utils*](https://www.cisa.gov/news-events/alerts/2024/03/29/reported-supply-chain-compromise-affecting-xz-utils-data-compression-library-cve-2024-3094)：CVE-2024-3094；供應鏈攻擊如何潛伏進廣泛間接依賴的元件
- [Martin Fowler, *Yagni*](https://martinfowler.com/bliki/Yagni.html)：YAGNI 的精準定義與適用邊界
- [Amazon, *2015 Letter to Shareholders*](https://s2.q4cdn.com/299287126/files/doc_financials/annual/2015-Letter-to-Shareholders.PDF)：one-way / two-way doors 的原始出處

## Part 1 · 訊息與交付

### 三種交付語意：at-most、at-least、exactly-once

- [Tyler Treat, "You Cannot Have Exactly-Once Delivery"](https://bravenewgeek.com/you-cannot-have-exactly-once-delivery/)：為何 exactly-once delivery 不可能的清楚論證
- [The Two Generals' Problem](https://en.wikipedia.org/wiki/Two_Generals%27_Problem)：Wikipedia，含不可能性的原始推論
- [Apache Kafka — Message Delivery Semantics](https://kafka.apache.org/documentation/#semantics)：官方文件，三種語意的定義
- ["Exactly-Once Semantics Are Possible: Here's How Apache Kafka Does It"](https://www.confluent.io/blog/exactly-once-semantics-are-possible-heres-how-apache-kafka-does-it/)：Confluent，冪等生產者＋交易的機制與邊界
- [Amazon SQS — Exactly-once processing](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html)：官方文件，FIFO 5 分鐘去重視窗
- [Amazon SQS — Using the message deduplication ID](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagededuplicationid-property.html)：官方文件，content-based dedup 對 body 取雜湊、不含 attributes
- [RFC 9110 §9.2.2 Idempotent Methods](https://www.rfc-editor.org/rfc/rfc9110.html#name-idempotent-methods)：IETF，冪等方法與安全重試

### 重複是常態：冪等與去重

- [Stripe, "Designing robust and predictable APIs with idempotency"](https://stripe.com/blog/idempotency)：冪等鍵設計的經典工程文
- [Stripe API Reference — Idempotent requests](https://docs.stripe.com/api/idempotent_requests)：存成功與失敗、參數校驗、24 小時保留的官方說明
- [IETF draft — The Idempotency-Key HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/)：draft-07，2026-06 仍為 Internet-Draft
- [brandur.org, "Implementing Stripe-like Idempotency Keys in Postgres"](https://brandur.org/idempotency-keys)：在 Postgres 上落地冪等鍵的完整實作
- [Apache Kafka — Idempotent Producer](https://cwiki.apache.org/confluence/display/KAFKA/Idempotent+Producer)：PID + 序號去重的設計

### 訊息順序：FIFO 與 partition key

- [KIP-185: Make exactly once in order delivery per partition the default producer setting](https://cwiki.apache.org/confluence/display/KAFKA/KIP-185)：為何把 idempotent in-order delivery 設為預設的設計討論
- [Aiven, "Does Apache Kafka really preserve message ordering?"](https://aiven.io/blog/kafka-real-ordering)：partition、key 與順序保證的邊界
- [AWS, "Using the message group ID with Amazon SQS FIFO queues"](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/using-messagegroupid-property.html)
- [AWS, "Avoid large message backlogs with the same message group ID"](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/avoid-backlog-with-the-same-message-group-id.html)：FIFO 群組隊頭阻塞與 120,000 掃描窗口
- [Confluent, "Choose and Change the Partition Count in Kafka"](https://docs.confluent.io/kafka/operations-tools/partition-determination.html)：增加 partition 數對 key→partition 映射的影響

### 重試、退避與 jitter

- [Marc Brooker, "Exponential Backoff And Jitter", AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)：full / equal / decorrelated jitter 的公式與模擬對比
- [Marc Brooker, "Timeouts, retries, and backoff with jitter", Amazon Builders' Library](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/)：含 5 層 ×3 次＝243 倍放大、單點重試原則
- [gRPC Proposal A6, "client-side Retries"](https://github.com/grpc/proposal/blob/master/A6-client-retries.md)：retryPolicy、retryableStatusCodes、retry throttling、hedging 與 retry 互斥
- [Bronson et al., "Metastable Failures in Distributed Systems", HotOS 2021](https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf)：重試風暴作為亞穩態故障的形式化

### 死信與毒訊息：DLQ

- [AWS, "Using dead-letter queues in Amazon SQS"](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html)：redrive policy、`maxReceiveCount`、retention 時間戳行為
- [AWS, "Introducing Amazon SQS dead-letter queue redrive to source queues"](https://aws.amazon.com/blogs/compute/introducing-amazon-simple-queue-service-dead-letter-queue-redrive-to-source-queues/)：回灌、redrive velocity
- [AWS Lambda, "Reporting batch item failures"](https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-errorhandling.html)：partial batch response、`ReportBatchItemFailures`
- [RabbitMQ, "Dead Letter Exchanges"](https://www.rabbitmq.com/docs/dlx)：四種死信原因、`x-death` 履歷、迴圈偵測、at-most-once 預設
- [RabbitMQ, "At-Least-Once Dead Lettering"](https://www.rabbitmq.com/blog/2022/03/29/at-least-once-dead-lettering)：quorum queue 的 at-least-once 死信保證
- [Confluent, "Spring for Apache Kafka: Can your Kafka consumers handle a poison pill?"](https://www.confluent.io/blog/spring-kafka-can-your-kafka-consumers-handle-a-poison-pill/)：`ErrorHandlingDeserializer` 與 dead-letter topic 模式

### 跨服務的交付一致：outbox 與 saga

- [microservices.io, "Pattern: Polling publisher" 與 "Pattern: Transaction log tailing"](https://microservices.io/patterns/data/polling-publisher.html)：relay 的兩種實作
- [microservices.io, "Pattern: Saga"](https://microservices.io/patterns/data/saga.html)：choreography vs orchestration
- [Confluent, "The Dual-Write Problem"](https://www.confluent.io/blog/dual-write-problem/)：dual-write 的成因與 outbox/CDC 解法
- [Microsoft Azure Architecture Center, "Saga distributed transactions pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/saga)：補償語意與 orchestration/choreography 取捨

### Webhooks：伺服器對伺服器的回呼

- [Stripe Docs, "Verify webhook signatures"](https://docs.stripe.com/webhooks/signature)：`Stripe-Signature` 的 `t`/`v1`、signed_payload 構造、5 分鐘容忍窗、constant-time 比對
- [Stripe Docs, "Receive Stripe events in your webhook endpoint"](https://docs.stripe.com/webhooks)：重試最長三天、只認 2xx、先回應再做重活
- [GitHub Docs, "Validating webhook deliveries"](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries)：`X-Hub-Signature-256`、HMAC-SHA256、勿用 `==`
- [Standard Webhooks Specification](https://github.com/standard-webhooks/standard-webhooks/blob/main/spec/standard-webhooks.md)：`webhook-id`/`webhook-timestamp`/`webhook-signature`、`{id}.{timestamp}.{body}` 簽章構造
- [webhooks.fyi](https://webhooks.fyi/)：webhook 安全與設計的最佳實踐目錄：簽章、防重放、無資料通知等
- [OWASP, "Server Side Request Forgery Prevention Cheat Sheet"](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)：webhook 端點與出站 URL 易成 SSRF 標的時的防護清單

### 序列化與 schema 演進

- [Protocol Buffers, "Language Guide (proto 3)"](https://protobuf.dev/programming-guides/proto3/)：field number、`reserved`、`required` 的移除與相容規則
- [Protocol Buffers, "Proto Best Practices"](https://protobuf.dev/best-practices/dos-donts/)：為何永不重用 field number、未知欄位的保留
- [Apache Avro Specification, "Schema Resolution"](https://avro.apache.org/docs/1.12.0/specification/#schema-resolution)：writer/reader schema 對齊、default 的角色
- [Confluent Docs, "Schema Evolution and Compatibility"](https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html)：BACKWARD/FORWARD/FULL 與 TRANSITIVE、預設模式

### SQS：Standard 與 FIFO

- [Amazon SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html)：官方 quotas，含 1 MiB 上限、in-flight 上限、retention 範圍
- [Amazon SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html)：官方，in-flight 與借期機制
- [FIFO queue delivery logic](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-understanding-logic.html)：官方，message group 投遞與隊頭阻塞、120,000 lookahead
- [High throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/high-throughput-fifo.html)：官方，per-partition TPS 與 high throughput mode

### SNS：fan-out 與 SNS→SQS

- [Amazon SNS message delivery for FIFO topics](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-delivery.html)：官方，含「FIFO topic 只能投 SQS」的端點限制
- [Amazon SNS message delivery retries](https://docs.aws.amazon.com/sns/latest/dg/sns-message-delivery-retries.html)：官方，四階段重試政策與各端點的精確次數
- [Amazon SNS raw message delivery](https://docs.aws.amazon.com/sns/latest/dg/sns-large-payload-raw-message-delivery.html)：官方，信封剝除與 10 個 attribute 上限
- [Amazon SNS subscription filter policies](https://docs.aws.amazon.com/sns/latest/dg/sns-subscription-filter-policies.html)：官方，attribute vs body 過濾
- [Amazon SNS endpoints and quotas](https://docs.aws.amazon.com/general/latest/gr/sns.html)：官方，256 KiB 訊息上限與各 region publish TPS
- [Amazon SNS FIFO topics now support delivery to SQS Standard queues](https://aws.amazon.com/about-aws/whats-new/2023/09/amazon-sns-fifo-topics-message-delivery-sqs-standard-queues/)：2023-09 公告，落點降級語意
- [Introducing Amazon SNS FIFO – First-In-First-Out Pub/Sub Messaging](https://aws.amazon.com/blogs/aws/introducing-amazon-sns-fifo-first-in-first-out-pub-sub-messaging/)：AWS Blog
- [Subscribing an Amazon SQS queue to an Amazon SNS topic](https://docs.aws.amazon.com/sns/latest/dg/subscribe-sqs-queue-to-sns-topic.html)：官方，SQS 存取政策與授權步驟

### Kafka：log、partition 與 consumer group

- [Apache Kafka 官方文件 — Replication](https://kafka.apache.org/documentation/#replication)：ISR、leader/follower、high watermark
- [KIP-848: The Next Generation of the Consumer Rebalance Protocol](https://cwiki.apache.org/confluence/display/KAFKA/KIP-848%3A+The+Next+Generation+of+the+Consumer+Rebalance+Protocol)：broker 端、增量協作式 rebalance
- [Apache Kafka 4.0 釋出說明](https://www.confluent.io/blog/latest-apache-kafka-release/)：KRaft 成為唯一模式、ZooKeeper 移除、新 rebalance 協定
- [KIP-932: Queues for Kafka](https://cwiki.apache.org/confluence/display/KAFKA/KIP-932%3A+Queues+for+Kafka)：share groups，4.2 起 GA 的佇列式消費模型
- [Jay Kreps, "The Log: What every software engineer should know about real-time data's unifying abstraction"](https://engineering.linkedin.com/distributed-systems/log-what-every-software-engineer-should-know-about-real-time-datas-unifying)：log 作為統一抽象的奠基文章

### RabbitMQ：exchange、routing 與 confirms

- [Quorum Queues](https://www.rabbitmq.com/docs/quorum-queues)：RabbitMQ 官方，Raft 複製、delivery-limit、confirm 與 quorum 的關係
- [AMQP 0-9-1 Model Explained](https://www.rabbitmq.com/tutorials/amqp-concepts)：RabbitMQ 官方，exchange / binding / queue 的概念模型
- [RabbitMQ Tutorials](https://www.rabbitmq.com/tutorials)：官方教學，逐型 exchange 與 routing 的範例
- [Reliability Guide](https://www.rabbitmq.com/docs/reliability)：RabbitMQ 官方，端到端不丟訊息要湊齊哪些條件
- [Publishers](https://www.rabbitmq.com/docs/publishers)：RabbitMQ 官方，mandatory 旗標、basic.return、unroutable 訊息處理
- [AMQP 0-9-1 specification](https://www.rabbitmq.com/resources/specs/amqp0-9-1.pdf)：協定原文，basic.publish / ack / nack / reject 的線上語意

### BullMQ：Redis 上的延遲與工作佇列

- [BullMQ 官方文件 — Architecture](https://docs.bullmq.io/guide/architecture)：工作狀態與生命週期
- [BullMQ 官方文件 — Stalled jobs](https://docs.bullmq.io/guide/jobs/stalled)：鎖、續租與 stalled 偵測
- [BullMQ 官方文件 — Delayed jobs](https://docs.bullmq.io/guide/jobs/delayed)：延遲投遞與 marker 機制
- [BullMQ — "Better queue markers in BullMQ v5"](https://bullmq.io/news/231204/better-queue-markers/)：marker + BZPOPMIN 設計說明
- [BullMQ GitHub](https://github.com/taskforcesh/bullmq)：Taskforce.sh 維護的後繼者，含 Lua 腳本實作
- [Bull GitHub](https://github.com/OptimalBits/bull)：OptimalBits，已進入 maintenance 模式的前身
- [Redis Streams 文件](https://redis.io/docs/latest/develop/data-types/streams/)：Redis 上另一種 at-least-once 訊息原語的對照

### Redis Pub/Sub 與 Streams：交付語意的取捨

- [Redis 官方〈Redis Pub/Sub〉](https://redis.io/docs/latest/develop/pubsub/)：at-most-once 語意、sharded Pub/Sub、client output buffer 行為
- [Redis 官方〈XREADGROUP command〉](https://redis.io/docs/latest/commands/xreadgroup/)：consumer group 讀取與 PEL 語意
- [Redis 官方〈XACK command〉](https://redis.io/docs/latest/commands/xack/)：確認與 PEL 移除
- [Redis 官方〈XAUTOCLAIM command〉](https://redis.io/docs/latest/commands/xautoclaim/)：pending 訊息接管、投遞計數、毒訊息偵測
- [Redis 官方〈Keyspace notifications〉](https://redis.io/docs/latest/develop/pubsub/keyspace-notifications/)：明示底層為 Pub/Sub、fire-and-forget、不可靠
- [Redis 官方〈Client handling〉](https://redis.io/docs/latest/develop/reference/clients/)：`client-output-buffer-limit` 與慢客戶端被斷線的機制

## Part 2 · 資料、一致性與儲存

### 一致性光譜：線性、因果、讀己之寫、最終一致

- [Herlihy, Wing, "Linearizability: A Correctness Condition for Concurrent Objects", ACM TOPLAS 12(3):463-492, 1990](https://cs.brown.edu/people/mph/HerlihyW90/p463-herlihy.pdf)：線性一致的奠基定義
- [Terry et al., "Session Guarantees for Weakly Consistent Replicated Data", PDIS 1994](https://www.cs.cornell.edu/courses/cs734/2000FA/cached%20papers/SessionGuaranteesPDIS_1.html)：讀己之寫等四個會話保證的原始論文
- [Lloyd, Freedman, Kaminsky, Andersen, "Don't Settle for Eventual: Scalable Causal Consistency for Wide-Area Storage with COPS", SOSP 2011](https://www.cs.cmu.edu/~dga/papers/cops-sosp2011.pdf)：causal+ 與「別將就最終一致」
- [Mahajan, Alvisi, Dahlin, "Consistency, Availability, and Convergence", UT Austin TR-11-22, 2011](https://www.cs.cornell.edu/lorenzo/papers/cac-tr.pdf)：因果一致是分區下可用的最強模型的證明
- [Peter Bailis, "Linearizability versus Serializability"](https://www.bailis.org/blog/linearizability-versus-serializability/)：兩個常被混為一談的概念的乾淨區分
- [Jepsen — Consistency Models](https://jepsen.io/consistency)：互動式的模型層級圖，最佳的全景入門
- [Aphyr (Kyle Kingsbury), "Strong consistency models"](https://aphyr.com/posts/313-strong-consistency-models)：從線性一致一路往下的圖解導覽
- [Werner Vogels, "Eventually Consistent", ACM Queue, 2008](https://queue.acm.org/detail.cfm?id=1466448)：最終一致性的權威科普

### 隔離級別與異常：dirty、phantom 到 write-skew

- [PostgreSQL 官方文件，Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html)：四級別在 PG 的實際語意、RR=snapshot isolation、SSI 與 `40001` 重試要求
- [Berenson, Bernstein, Gray, Melton, O'Neil, O'Neil, "A Critique of ANSI SQL Isolation Levels", SIGMOD 1995](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-95-51.pdf)：指出標準四異常的歧義、正式命名 snapshot isolation、定義 write skew A5B、證明 SI 與 RR 不可比較
- [MySQL 官方文件，InnoDB Transaction Isolation Levels](https://dev.mysql.com/doc/refman/8.4/en/innodb-transaction-isolation-levels.html)：InnoDB 預設 RR、next-key/gap lock 防幻讀、Serializable 隱式 `FOR SHARE`
- [Jepsen, MySQL 8.0.34](https://jepsen.io/analyses/mysql-8.0.34)：實測 InnoDB Repeatable Read 弱於 snapshot isolation，出現 G2-item／G-single／lost update
- [Fekete, Liarokapis, O'Neil, O'Neil, Shasha, "Making Snapshot Isolation Serializable", ACM TODS 2005](https://dl.acm.org/doi/10.1145/1071610.1071615)：SSI 的理論基礎：在 SI 上偵測危險讀寫依賴環
- [PostgreSQL wiki, Serializable Snapshot Isolation](https://wiki.postgresql.org/wiki/SSI)：SSI 在 PG 的工程實作與調校

### MVCC：讓讀不擋寫

- [PostgreSQL 官方文件，Concurrency Control](https://www.postgresql.org/docs/current/mvcc-intro.html)：Introduction / MVCC 總述，含「reading never blocks writing」
- [PostgreSQL 官方文件，Routine Vacuuming](https://www.postgresql.org/docs/current/routine-vacuuming.html)：含 XID wraparound 與 freeze
- [PostgreSQL 官方文件，Heap-Only Tuples (HOT)](https://www.postgresql.org/docs/current/storage-hot.html)
- [MySQL 官方文件，InnoDB Multi-Versioning](https://dev.mysql.com/doc/refman/8.4/en/innodb-multi-versioning.html)：DB_TRX_ID / DB_ROLL_PTR / undo log
- [MySQL 官方文件，Consistent Nonlocking Reads](https://dev.mysql.com/doc/refman/8.4/en/innodb-consistent-read.html)：read view 與 RR / RC 的快照時機
- ["Serializable Snapshot Isolation in PostgreSQL"](https://arxiv.org/pdf/1208.4179)：Ports & Grittner, VLDB 2012；MVCC 之上如何加序列化

### 鎖與死結：行鎖、gap、next-key 與 wait-for graph

- [MySQL 8.4 Reference Manual, InnoDB Locking](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking.html)：record / gap / next-key / insert intention lock 的精確定義與 supremum pseudo-record
- [MySQL 8.4 Reference Manual, Deadlocks in InnoDB](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlocks.html)
- [MySQL 8.4 Reference Manual, Deadlock Detection](https://dev.mysql.com/doc/refman/8.4/en/innodb-deadlock-detection.html)：受害者選擇＝回滾列數最少的交易、wait-for graph 上限
- [PostgreSQL Documentation, Lock Management](https://www.postgresql.org/docs/current/runtime-config-locks.html)：`deadlock_timeout` 預設 1s＝開始檢查死結前的等待時間
- [PostgreSQL Documentation, Explicit Locking](https://www.postgresql.org/docs/current/explicit-locking.html)：行鎖模式：`FOR UPDATE` / `FOR NO KEY UPDATE` / `FOR SHARE`
- [Jim Gray et al., "Granularity of Locks and Degrees of Consistency in a Shared Data Base"](https://dl.acm.org/doi/10.5555/1282480.1282513)：1976，鎖粒度與多粒度鎖的奠基論文

### 樂觀與悲觀並發控制：CAS、版本與 ETag

- [RFC 6585, "Additional HTTP Status Codes", §3 428 Precondition Required](https://www.rfc-editor.org/rfc/rfc6585.html)：要求寫入必須帶條件以防 lost update
- [MDN, If-Match request header](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/If-Match)
- [Redis Transactions](https://redis.io/docs/latest/develop/using-commands/transactions/)：WATCH/MULTI/EXEC 的樂觀鎖語意
- [AWS DynamoDB Developer Guide, Condition Expressions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Expressions.ConditionExpressions.html)：條件寫與 optimistic locking
- [etcd v3 API](https://etcd.io/docs/v3.6/learning/api/)：Txn 比較 mod_revision 做 compare-and-swap
- ["Compare-and-swap", Wikipedia](https://en.wikipedia.org/wiki/Compare-and-swap)：CAS 原語與 ABA 問題

### 複製延遲與讀己之寫

- [PostgreSQL — `synchronous_commit` 與同步複製](https://www.postgresql.org/docs/current/runtime-config-replication.html)：官方文件，含 remote_write／remote_apply 各等第的語意
- [MySQL — `WAIT_FOR_EXECUTED_GTID_SET` 等 GTID 函式](https://dev.mysql.com/doc/refman/8.4/en/gtid-functions.html)：官方文件，讀己之寫的內建原語
- [PostgreSQL — Hot Standby](https://www.postgresql.org/docs/current/hot-standby.html)：官方文件，讀副本的設定與行為

### 分片：水平切分與路由

- [Redis — Cluster specification](https://redis.io/docs/latest/operate/oss_and_stack/reference/cluster-spec/)：16384 槽、CRC16、hash tag、槽搬移的權威規格
- [Vitess — Resharding](https://vitess.io/docs/22.0/user-guides/configuration-advanced/resharding/)：線上改變分片數的工程化流程
- [Vitess — Sharding](https://vitess.io/docs/23.0/reference/features/sharding/)：vindex 與 keyspace ID 的概念
- [AWS — Best practices for designing and using partition keys effectively in DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html)：熱點、split for heat、單調 sort key 的陷阱

### 一致性與交易的保證模型：ACID、BASE、CAP、PACELC

- [Gilbert & Lynch, "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services", ACM SIGACT News, 2002](https://groups.csail.mit.edu/tds/papers/Gilbert/Brewer2.pdf)：CAP 的形式化證明
- [Brewer, "CAP Twelve Years Later: How the 'Rules' Have Changed", IEEE Computer 45(2), 2012](https://www.infoq.com/articles/cap-twelve-years-later-how-the-rules-have-changed/)：提出者本人對「三選二」誤讀的澄清
- [Abadi, "Consistency Tradeoffs in Modern Distributed Database System Design: CAP is Only Part of the Story", IEEE Computer 45(2):37-42, 2012](https://www.cs.umd.edu/~abadi/papers/abadi-pacelc.pdf)：PACELC 原始論文
- [Pritchett, "BASE: An Acid Alternative", ACM Queue 6(3), 2008](https://queue.acm.org/detail.cfm?id=1394128)：BASE 哲學的原始出處

### 索引與查詢計畫：B-tree、覆蓋索引與 planner

- [PostgreSQL 官方文件，Index Types / B-Tree Indexes](https://www.postgresql.org/docs/current/btree.html)：B-tree 支援的查找類型與運算子類
- [PostgreSQL 官方文件，Multicolumn Indexes](https://www.postgresql.org/docs/current/indexes-multicolumn.html)：含最左前綴與 skip scan
- [PostgreSQL 官方文件，Index-Only Scans and Covering Indexes](https://www.postgresql.org/docs/current/indexes-index-only-scans.html)：INCLUDE 與 visibility map 的角色
- [PostgreSQL 官方文件，Statistics Used by the Planner](https://www.postgresql.org/docs/current/planner-stats.html)：`pg_statistic`、`default_statistics_target`、選擇性估計
- [PostgreSQL 官方文件，Using EXPLAIN](https://www.postgresql.org/docs/current/using-explain.html)：讀懂查詢計畫
- [MySQL 官方文件，Clustered and Secondary Indexes](https://dev.mysql.com/doc/refman/8.4/en/innodb-index-types.html)：InnoDB 的 secondary index 帶主鍵欄與 bookmark lookup
- [Markus Winand, *Use The Index, Luke!*](https://use-the-index-luke.com/)：B-tree 索引與查詢調校的權威入門

### 多租戶隔離：row、schema、db-per-tenant

- [AWS Whitepaper, "SaaS Tenant Isolation Strategies"](https://docs.aws.amazon.com/whitepapers/latest/saas-tenant-isolation-strategies/saas-tenant-isolation-strategies.html)：silo / pool / bridge 三模型與各層隔離手段的權威整理
- [PostgreSQL 官方文件, "Row Security Policies"](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)：RLS policy、`ENABLE` vs `FORCE`、owner/BYPASSRLS 繞過規則
- [AWS Database Blog, "Multi-tenant data isolation with PostgreSQL Row Level Security"](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)：用 RLS 做租戶隔離的完整實作與 session 變數模式
- ["Postgres Row-Level Security Footguns", Bytebase](https://www.bytebase.com/blog/postgres-row-level-security-footguns/)：RLS 在連線池下 `SET` vs `SET LOCAL`、owner 繞過等實務陷阱

### 零停機 schema 遷移：expand-contract 與 backfill

- [Scott Ambler & Pramod Sadalage, *Refactoring Databases: Evolutionary Database Design*](https://databaserefactoring.com/)：資料庫重構與漸進式 schema 演化的奠基著作
- [PostgreSQL 官方文件, ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html)：各動作的鎖等級、`NOT VALID` / `VALIDATE CONSTRAINT`、`SET NOT NULL`
- [PostgreSQL 官方文件, CREATE INDEX](https://www.postgresql.org/docs/current/sql-createindex.html)：`CONCURRENTLY` 的兩遍掃描與失敗後的無效索引處理
- [Brandur Leach, "A Missing Link in Postgres 11: Fast Column Creation with Defaults"](https://brandur.org/postgres-default)：PG 11 為何能讓 `ADD COLUMN ... DEFAULT` 不重寫表，及 volatile 預設的例外
- [MySQL 8.0 Reference Manual, "Online DDL Operations"](https://dev.mysql.com/doc/refman/8.0/en/innodb-online-ddl-operations.html)：`INSTANT` / `INPLACE` / `COPY` 各支援哪些操作與其鎖代價
- [gh-ost](https://github.com/github/gh-ost)：GitHub 的 triggerless online schema migration，讀 binlog 追平的影子表機制
- [Percona Toolkit, pt-online-schema-change](https://docs.percona.com/percona-toolkit/pt-online-schema-change.html)：觸發器式影子表同步

### PostgreSQL 與 MySQL：兩種隔離哲學

- [PostgreSQL 原始碼樹，README-SSI](https://github.com/postgres/postgres/blob/master/src/backend/storage/lmgr/README-SSI)：SIREAD lock、危險結構、pivot 的工程說明
- [Ports, Grittner, "Serializable Snapshot Isolation in PostgreSQL", VLDB 2012](https://arxiv.org/abs/1208.4179)：SSI 在 PostgreSQL 的設計論文
- [Berenson 等人，"A Critique of ANSI SQL Isolation Levels", SIGMOD 1995](https://www.microsoft.com/en-us/research/publication/a-critique-of-ansi-sql-isolation-levels/)：指出標準異常定義的歧義、提出 snapshot isolation

### LSM-tree 與 B-tree：寫放大換讀放大

- [Bayer & McCreight, "Organization and Maintenance of Large Ordered Indexes", *Acta Informatica* 1(3):173-189, 1972](https://doi.org/10.1007/BF00288683)：B-tree 的原始論文
- [O'Neil, Cheng, Gawlick, O'Neil, "The Log-Structured Merge-Tree (LSM-Tree)", *Acta Informatica* 33(4):351-385, 1996](https://www.cs.umb.edu/~poneil/lsmtree.pdf)：LSM-tree 原始論文
- [Luo & Carey, "LSM-based Storage Techniques: A Survey", *VLDB Journal* 2020](https://arxiv.org/abs/1812.07527)：寫／讀／空間放大三方取捨的系統性整理
- [RocksDB Wiki — Leveled Compaction](https://github.com/facebook/rocksdb/wiki/Leveled-Compaction)：leveled 的寫放大與層級放大係數的官方說明
- [Apache Cassandra — Unified Compaction Strategy](https://cassandra.apache.org/_/blog/Apache-Cassandra-5.0-Features-Unified-Compaction-Strategy.html)：leveled↔tiered 連續可調的設計

### WAL：先寫日誌，再改資料

- [C. Mohan et al., "ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging", ACM TODS 17(1), 1992](https://dl.acm.org/doi/10.1145/128765.128770)：WAL 崩潰恢復的奠基論文，analysis/redo/undo 三階段與 repeating history 的原典
- [PostgreSQL 官方文件 — Write-Ahead Logging (WAL)](https://www.postgresql.org/docs/current/wal-intro.html)
- [PostgreSQL 官方文件 — Reliability and the Write-Ahead Log](https://www.postgresql.org/docs/current/wal-reliability.html)：full_page_writes、torn page、fsync 與磁碟說謊
- [PostgreSQL Wiki — Fsync Errors](https://wiki.postgresql.org/wiki/Fsync_Errors)：fsyncgate 的來龍去脈與 PG 12 的 PANIC 修法
- ["PostgreSQL's fsync() surprise", LWN.net, 2018](https://lwn.net/Articles/752063/)：fsyncgate 對整個資料庫圈的影響
- [MySQL 官方文件 — InnoDB redo log](https://dev.mysql.com/doc/refman/8.4/en/innodb-redo-log.html)：physiological logging、LSN、innodb_flush_log_at_trx_commit
- [RocksDB Wiki — Write Ahead Log (WAL)](https://github.com/facebook/rocksdb/wiki/Write-Ahead-Log-(WAL))：LSM 引擎的 WAL：manual_wal_flush 與 WriteOptions::sync 的取捨

### SQL 與 NoSQL：資料模型各擅其場

- [E. F. Codd, "A Relational Model of Data for Large Shared Data Banks", Comm. ACM 13(6):377–387, 1970](https://dl.acm.org/doi/10.1145/362384.362685)：關係模型原典，「先存好、查法之後想」的源頭
- [MongoDB 官方文件 — Transactions](https://www.mongodb.com/docs/manual/core/transactions/)：多文件 ACID 交易的成立條件與生產考量
- [MongoDB 官方文件 — Data Modeling Introduction](https://www.mongodb.com/docs/manual/data-modeling/)：嵌入 vs 引用的判斷
- [Apache Cassandra 官方文件 — Data Modeling](https://cassandra.apache.org/doc/latest/cassandra/developing/data-modeling/index.html)：反正規化、一表一查的原理
- [PostgreSQL 官方文件 — JSON Types](https://www.postgresql.org/docs/current/datatype-json.html)：`JSONB` 與 GIN 索引，關係/文件收斂的代表

### 倒排索引：全文搜尋的資料結構

- [PostgreSQL 官方文件 — Full Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [PostgreSQL 官方文件 — GIN Indexes](https://www.postgresql.org/docs/current/gin.html)：key, posting list) 的內部結構
- [Apache Lucene — 官方文件](https://lucene.apache.org/core/)：FST 詞典、postings 格式、skip data
- [Lucene `BlockTreeTermsReader`](https://lucene.apache.org/core/9_0_0/core/org/apache/lucene/codecs/blocktree/BlockTreeTermsReader.html)：FST 前綴 trie 詞典實作
- [SQLite FTS5 官方文件](https://www.sqlite.org/fts5.html)：嵌入式倒排索引、doclist 與 position list
- [M. F. Porter, "An algorithm for suffix stripping", 1980](https://tartarus.org/martin/PorterStemmer/def.txt)：Porter stemming 演算法原文

### 資料的生命週期：retention、TTL、軟刪除與合規刪除

- [GDPR Art. 17 — Right to erasure（'right to be forgotten'）原文與觸發條件、第 3 項例外](https://gdpr-info.eu/art-17-gdpr/)
- [GDPR Art. 83 — General conditions for imposing administrative fines](https://gdpr-info.eu/art-83-gdpr/)：€20M／全球營業額 4% 的罰則上限
- [UK ICO — Right to erasure](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/individual-rights/right-to-erasure/)：合規實作指引、備份「beyond use」處理
- [AWS DynamoDB 官方文件 — Using Time to Live (TTL)](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/howitworks-ttl.html)：「within a few days」、過期項目仍出現在查詢、刪除流入 Streams
- [Apache Cassandra 官方文件 — Tombstones](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/compaction/tombstones.html)：gc_grace_seconds、zombie 復活、刪除即寫入
- [PostgreSQL 官方文件 — Table Partitioning](https://www.postgresql.org/docs/current/ddl-partitioning.html)：DROP／DETACH PARTITION 與時間 retention
- [PostgreSQL 官方文件 — Partial Indexes](https://www.postgresql.org/docs/current/indexes-partial.html)：軟刪除的部分唯一索引解法基礎
- [Redis 官方文件 — Key expiration](https://redis.io/docs/latest/develop/use/keyspace/#how-redis-expires-keys)：惰性＋主動取樣回收機制

### 快取策略：cache-aside、write-through、write-behind

- [Microsoft, "Cache-Aside Pattern", Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside)：讀寫流程、先更 DB 再作廢快取的順序、一致性 caveat
- [AWS 白皮書, "Database Caching Strategies Using Redis"](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html)：cache-aside / read-through / write-through / write-behind 各模式對照
- [Oracle Coherence, "Read-Through, Write-Through, Write-Behind Caching and Refresh-Ahead"](https://docs.oracle.com/cd/E13924_01/coh.340/e13819/readthrough.htm)：write-behind 的 coalescing 與 batching 機制
- [Redis, "Client-side caching"](https://redis.io/docs/latest/develop/reference/client-side-caching/)：in-process 快取與 invalidation 失效追蹤
- [Ehcache, "Thundering Herd"](https://www.ehcache.org/documentation/2.8/recipes/thunderingherd.html)：read-through 下用 BlockingCache 做 single-flight 防驚群

### 快取的失效災難：雪崩、穿透、擊穿

- [Burton H. Bloom, "Space/Time Trade-offs in Hash Coding with Allowable Errors", CACM 13(7):422–426, 1970](https://dl.acm.org/doi/10.1145/362686.362692)：Bloom filter 原始論文，無偽陰性、有偽陽性的由來
- [Vattani, Chierichetti, Lowenstein, "Optimal Probabilistic Cache Stampede Prevention", PVLDB 8(8):886–897, 2015](https://www.vldb.org/pvldb/vol8/p886-vattani.pdf)：機率性提前過期的最佳化證明，XFetch 的理論來源
- [RFC 5861, "HTTP Cache-Control Extensions for Stale Content"](https://www.rfc-editor.org/rfc/rfc5861)：stale-while-revalidate 與 stale-if-error
- [Redis 官方〈Key eviction〉](https://redis.io/docs/latest/develop/reference/eviction/)：含 TTL、過期與隨機抖動的討論
- [antirez, "Cache stampede prevention"](https://redis.antirez.com/fundamental/cache-stampede-prevention.html)：mutex 鎖與 X-Fetch 機率提前重算的實作筆記
- [AWS 白皮書〈Database Caching Strategies Using Redis〉](https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/welcome.html)：cache-aside 讀寫路徑與快取一致性

### 驅逐：LRU、LFU、TTL 與 LRM

- [Redis 8.6〈What's new〉](https://redis.io/docs/latest/develop/whats-new/8-6/)：`volatile-lrm` / `allkeys-lrm`，Least Recently Modified
- [Memcached〈Modern LRU〉](https://memcached.org/blog/modern-lru/)：segmented LRU：HOT/WARM/COLD 與背景執行緒，對抗多執行緒下的 LRU 鎖爭用
- [Memcached 官方文件](https://github.com/memcached/memcached/wiki/UserInternals)：slab allocation 與 slab-specific 驅逐
- [Robert Morris, "Counting Large Numbers of Events in Small Registers", CACM 21(10):840-842, 1978](https://dl.acm.org/doi/10.1145/359619.359627)：Morris 機率計數器原始論文，LFU 8-bit 計數器的理論基礎

### Redis 的內部：單執行緒、I/O threads、持久化與多重角色

- [Redis 官方〈Redis persistence〉](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)：RDB / AOF / 混合 / fsync 策略 / fork 與 COW
- [Redis 官方〈Redis replication〉](https://redis.io/docs/latest/operate/oss_and_stack/management/replication/)：非同步複製、`WAIT` 的半同步語意與其限制
- [Redis 8.0-M03 公告](https://redis.io/blog/redis-8-0-m03-is-out-even-more-performance-new-features/)：重寫後的 I/O threading 模型：main thread 指派 client、I/O thread 讀寫與解析
- [Redis 8 GA 公告](https://redis.io/blog/redis-8-ga/)：I/O threading 重寫、SIMD 加速、效能數字
- [antirez, "Redis persistence demystified"](http://oldblog.antirez.com/post/redis-persistence-demystified.html)：作者談 RDB/AOF 與 fsync 取捨的原始思路
- [antirez, "WAIT: synchronous replication for Redis"](https://antirez.com/news/66)：`WAIT` 設計動機與「為何仍非 CP」
- [Redis 授權頁](https://redis.io/legal/licenses/)：RSALv2 / SSPLv1 / AGPLv3 三授權
- [Valkey 專案官網](https://valkey.io/)：Linux Foundation 主導的 BSD fork

### 物件儲存：S3 與大 payload 的交接

- [Amazon S3 FAQs](https://aws.amazon.com/s3/faqs/)：耐久度 11 個 9、強讀後寫一致性、物件大小
- [AWS 文件〈Amazon S3 multipart upload limits〉](https://docs.aws.amazon.com/AmazonS3/latest/userguide/qfacts.html)：5 MiB–5 GiB 分片、10,000 片上限、48.8 TiB 拼裝上限
- [AWS what's-new〈Amazon S3 increases the maximum object size to 50 TB〉](https://aws.amazon.com/about-aws/whats-new/2025/12/amazon-s3-maximum-object-size-50-tb/)：2025-12
- [AWS what's-new〈Amazon SQS increases maximum message payload size to 1 MiB〉](https://aws.amazon.com/about-aws/whats-new/2025/08/amazon-sqs-max-payload-size-1mib/)：2025-08
- [AWS 文件〈Managing large Amazon SQS messages using the Extended Client Library and Amazon S3〉](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-managing-large-messages.html)：claim-check、最大 2 GiB payload
- [AWS 文件〈Download and upload objects with presigned URLs〉](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)：過期語意、12h／7 天上限
- [Amazon S3 Service Level Agreement](https://aws.amazon.com/s3/sla/)：可用度 SLA 99.9%，與耐久度的區別

### 資料同步的全景：full/incremental、push/pull、batch/streaming

- [PostgreSQL 官方文件，Logical Replication Architecture](https://www.postgresql.org/docs/current/logical-replication-architecture.html)：初始快照 → 同步 → 串流的接縫機制
- [PostgreSQL 官方文件，`pg_dump`](https://www.postgresql.org/docs/current/app-pgdump.html)：平行匯出如何靠 exported snapshot 取得跨連線一致快照
- [Debezium Blog, "Incremental Snapshots in Debezium"](https://debezium.io/blog/2021/10/07/incremental-snapshots/)：DBLog 水位法在 Debezium 的落地

### CDC：從資料庫變更長出事件流

- [Andreakis, Papapanagiotou, "DBLog: A Watermark Based Change-Data-Capture Framework"](https://arxiv.org/abs/2010.12597)：Netflix，增量快照水位機制的原始論文
- [Debezium 官方文件](https://debezium.io/documentation/reference/stable/)：CDC 架構、PostgreSQL/MySQL connector、快照與串流模型
- [PostgreSQL 官方文件 — Logical Decoding Concepts](https://www.postgresql.org/docs/current/logicaldecoding-explanation.html)：replication slot、輸出外掛、提交順序語意
- [PostgreSQL 官方文件 — Logical Decoding Output Plugins](https://www.postgresql.org/docs/current/logicaldecoding-output-plugin.html)：只在提交時解碼、回滾交易不解碼
- [Gunnar Morling, "Mastering Postgres Replication Slots: Preventing WAL Bloat and Other Production Issues"](https://www.morling.dev/blog/mastering-postgres-replication-slots/)：slot 撐爆磁碟的成因與防線
- [MySQL 官方文件 — Replication Formats](https://dev.mysql.com/doc/refman/8.0/en/replication-formats.html)：ROW vs STATEMENT，CDC 為何需要 row 格式
- [Martin Kleppmann, "Using logs to build a solid data infrastructure (or: why dual writes are a bad idea)"](https://www.confluent.io/blog/using-logs-to-build-a-solid-data-infrastructure-or-why-dual-writes-are-a-bad-idea/)：log 作為變更真相來源的論述

### dual-write 問題與 event-carried state transfer

- [Chris Richardson, "Pattern: Transactional outbox", microservices.io](https://microservices.io/patterns/data/transactional-outbox.html)：outbox 模式的標準描述
- [Martin Fowler, "What do you mean by 'Event-Driven'?", 2017](https://martinfowler.com/articles/201701-event-driven.html)：event notification 與 event-carried state transfer 兩種風格的原始區分
- [AWS Prescriptive Guidance, "Transactional outbox pattern"](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html)：雲端視角的 outbox 與 dual-write 問題拆解
- [Debezium, "Outbox Event Router"](https://debezium.io/documentation/reference/stable/transformations/outbox-event-router.html)：用 CDC 讀 outbox 表投遞事件的具體實作與表結構慣例
- [Apache Kafka, "KIP-939: Support Participation in 2PC"](https://cwiki.apache.org/confluence/display/KAFKA/KIP-939%3A+Support+Participation+in+2PC)：讓 broker 參與外部協調 2PC 的提案與現況

### 衝突解決：LWW、版本向量與 CRDT

- [M. Shapiro, N. Preguiça, C. Baquero, M. Zawirski, "Conflict-free Replicated Data Types", SSS 2011](https://www.lip6.fr/Marc.Shapiro/papers/2011/CRDTs_SSS-2011.pdf)：CRDT 與 Strong Eventual Consistency 的原始形式化
- [M. Shapiro et al., "A comprehensive study of Convergent and Commutative Replicated Data Types", INRIA RR-7506, 2011](https://hal.inria.fr/inria-00555588/document)：state-based 與 op-based 的完整型別目錄與證明
- [DeCandia et al., "Dynamo: Amazon's Highly Available Key-value Store", SOSP 2007](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)：版本向量在生產系統的實作
- [Preguiça et al., "Dotted Version Vectors: Logical Clocks for Optimistic Replication"](https://arxiv.org/abs/1011.5808)：DVV，壓制 sibling 爆炸與 false conflict
- [Lamport, "Time, Clocks, and the Ordering of Events in a Distributed System", CACM 1978](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)：happens-before 與並發的原始定義
- [Riak KV 官方文件 — Conflict Resolution](https://docs.riak.com/riak/kv/latest/developing/usage/conflict-resolution/index.html)：siblings、causal context、DVV 的實務行為
- [Apache Cassandra — Dynamo](https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html)：官方說明其 last-write-wins 模型，並明言不採 Dynamo 論文的向量時鐘

### 對帳：怎麼確認兩邊一致、漂移怎麼修

- [Apache Cassandra 官方文件 — Repair / anti-entropy](https://cassandra.apache.org/doc/latest/cassandra/managing/operating/repair.html)：深度 15 緊湊 Merkle tree 的工程實作
- [Merkle, R. C., "A Digital Signature Based on a Conventional Encryption Function", CRYPTO 1987](https://link.springer.com/chapter/10.1007/3-540-48184-2_32)：雜湊樹的原始概念
- [Percona Toolkit — pt-table-checksum 官方文件](https://docs.percona.com/percona-toolkit/pt-table-checksum.html)：chunked checksum 隨複製串流重放、對齊比對時間點的實作
- [Percona Toolkit — pt-table-sync 官方文件](https://docs.percona.com/percona-toolkit/pt-table-sync.html)：依 checksum 結果定位並修復 replica drift
- [PostgreSQL 官方文件 — Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html)：一致性快照與複製位點，對齊對帳時間點的基礎

### 跨區與異質庫同步

- [PostgreSQL 官方文件 — Logical Replication Restrictions](https://www.postgresql.org/docs/current/logical-replication-restrictions.html)：明列「不複製 DDL／schema」「additive 變更建議先在訂閱端做」等限制
- [PostgreSQL 官方文件 — Date/Time Types](https://www.postgresql.org/docs/current/datatype-datetime.html)：`timestamptz` 存 UTC、依 session 時區換算的語意
- [MySQL 官方文件 — The DATE, DATETIME, and TIMESTAMP Types](https://dev.mysql.com/doc/refman/8.4/en/datetime.html)：`DATETIME` 不帶時區、`TIMESTAMP` 才做 UTC 換算的差異
- [Amazon DynamoDB 官方文件 — Global tables: multi-active, multi-Region replication](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/GlobalTables.html)：LWW 衝突解決、MREC 與 MRSC 一致性模式
- [AWS 官方文件 — AWS Multi-Region Fundamentals](https://docs.aws.amazon.com/whitepapers/latest/aws-multi-region-fundamentals/aws-multi-region-fundamentals.html)：跨區架構的延遲、複製與容災權衡
- [AWS Database Migration Service 文件 — full load + CDC 模式](https://docs.aws.amazon.com/dms/latest/userguide/CHAP_Task.CDC.html)：異質遷移的整批初始載入接續增量同步

## Part 3 · 連線、網路與 API

### HTTP/1.1、HTTP/2、HTTP/3：keep-alive、多工與 QUIC

- [RFC 9112 — HTTP/1.1](https://www.rfc-editor.org/rfc/rfc9112.html)：訊息語法與連線管理的當前規範
- [RFC 9113 — HTTP/2](https://www.rfc-editor.org/rfc/rfc9113.html)：多工、HPACK、server push 棄用
- [RFC 9114 — HTTP/3](https://www.rfc-editor.org/rfc/rfc9114.html)：HTTP over QUIC 的映射
- [RFC 9000 — QUIC: A UDP-Based Multiplexed and Secure Transport](https://www.rfc-editor.org/rfc/rfc9000.html)
- [RFC 9204 — QPACK: Field Compression for HTTP/3](https://www.rfc-editor.org/rfc/rfc9204.html)：為亂序交付重設計的 header 壓縮
- [Robin Marx, "Head-of-Line Blocking in QUIC and HTTP/3: The Details"](https://calendar.perfplanet.com/2020/head-of-line-blocking-in-quic-and-http-3-the-details/)：把三層隊頭阻塞講得最透的一篇
- [Cloudflare, "Even faster connection establishment with QUIC 0-RTT resumption"](https://blog.cloudflare.com/even-faster-connection-establishment-with-quic-0-rtt-resumption/)：0-RTT 復用與重放風險

### gRPC 與 Protobuf：用 IDL 定義服務

- [gRPC over HTTP/2 協定規格](https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md)：length-prefixed message、trailer、grpc-status 的線上格式
- [gRPC, "Deadlines"](https://grpc.io/docs/guides/deadlines/)：deadline 為絕對時間點、跨跳傳播換算為剩餘 timeout、對時鐘偏移免疫
- [gRPC, "Status codes and their use in gRPC"](https://grpc.io/docs/guides/status-codes/)：grpc-status 碼表
- [gRPC Blog, "The state of gRPC in the browser"](https://grpc.io/blog/state-of-grpc-web/)：為何瀏覽器需 gRPC-Web 與 proxy、trailer 限制
- [gRPC Blog, "gRPC on HTTP/2: Engineering a robust, high-performance protocol"](https://grpc.io/blog/grpc-on-http2/)：channel/subchannel、單一連線多工
- [Protocol Buffers 官方文件](https://protobuf.dev/)：Protobuf 作為序列化格式本身

### 連線池：為什麼不每次都重開連線

- [HikariCP — About Pool Sizing(小池為何比大池快的經典分析,含 Oracle 的 2048→96 連線壓測)](https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing)
- [PostgreSQL — Connection Settings(`max_connections` 預設與每連線成本)](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [PgBouncer — Features(session / transaction / statement 三種 pooling 模式與其狀態取捨)](https://www.pgbouncer.org/features.html)
- [RFC 8446 — TLS 1.3(1-RTT 交握,連線建立成本的另一半)](https://www.rfc-editor.org/rfc/rfc8446.html)
- [PgBouncer — Connecting application drivers and prepared statements(交易級 pooling 下預備語句失效的細節)](https://www.pgbouncer.org/config.html)

### 負載均衡：L4 與 L7、演算法與健康檢查

- [Eisenbud et al., "Maglev: A Fast and Reliable Software Network Load Balancer", NSDI 2016](https://www.usenix.org/conference/nsdi16/technical-sessions/presentation/eisenbud)：L4 LB 怎麼用一致性雜湊在無狀態下保持連線親和
- [Mitzenmacher, "The Power of Two Choices in Randomized Load Balancing", IEEE TPDS 12(10), 2001](https://www.eecs.harvard.edu/~michaelm/postscripts/tpds2001.pdf)：P2C 的 Θ(log log n) 結果
- [Envoy — Load Balancing Overview](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/overview)：演算法、ring hash、Maglev、P2C 的實作對照
- [Envoy — Panic Threshold](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/panic_threshold)：健康後端跌破門檻時為何把流量攤回全部後端
- [gRPC Blog — gRPC Load Balancing](https://grpc.io/blog/grpc-load-balancing/)：為何 HTTP/2 長連線讓 L4 失效、proxy 與 client-side 兩條路
- [HAProxy — Load Balancing Algorithms](https://www.haproxy.com/glossary/what-are-load-balancing-algorithms)：round robin / leastconn / 一致性雜湊的工程語意

### TLS 與 mTLS：握手與憑證管理

- [Cloudflare — A Detailed Look at RFC 8446 (a.k.a. TLS 1.3)](https://blog.cloudflare.com/rfc-8446-aka-tls-1-3/)
- [The Illustrated TLS 1.3 Connection: Every Byte Explained](https://tls13.xargs.org/)：逐位元組拆解一次真實握手
- [CA/Browser Forum — Ballot SC-081v3: Reducing Validity and Data Reuse Periods](https://cabforum.org/2025/04/11/ballot-sc081v3-introduce-schedule-of-reducing-validity-and-data-reuse-periods/)：效期遞減時間表
- [Let's Encrypt — How It Works](https://letsencrypt.org/how-it-works/)：ACME 自動簽發與續簽
- [Let's Encrypt — Decreasing Certificate Lifetimes to 45 Days](https://letsencrypt.org/2025/12/02/from-90-to-45)
- [RFC 5280 — Internet X.509 Public Key Infrastructure Certificate and CRL Profile](https://www.rfc-editor.org/rfc/rfc5280.html)：憑證與憑證鏈的格式與驗證規則

### DNS 與服務發現

- [RFC 2782 — A DNS RR for specifying the location of services (DNS SRV)](https://www.rfc-editor.org/rfc/rfc2782.txt)
- [RFC 2308 — Negative Caching of DNS Queries (DNS NCACHE)](https://www.rfc-editor.org/rfc/rfc2308.html)
- [Kubernetes — DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Kubernetes pods /etc/resolv.conf ndots:5 option and why it may affect your application performance(Marco Pracucci)](https://pracucci.com/kubernetes-dns-resolution-ndots-options-and-why-it-may-affect-application-performances.html)
- [Consul — Configure Consul DNS behavior(含 TTL 與健康檢查)](https://developer.hashicorp.com/consul/docs/discover/dns/configure)
- [AWS — Set the JVM TTL for DNS name lookups(JVM 永久快取與調整)](https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/jvm-ttl-dns.html)

### Service mesh：把網路關注點下沉到 sidecar

- [Istio — Fast, Secure, and Simple: Ambient Mode Reaches GA in v1.24](https://istio.io/latest/blog/2024/ambient-reaches-ga/)：ambient 模式 GA 公告，含設計動機
- [Istio — Dataplane modes](https://istio.io/latest/docs/overview/dataplane-modes/)：sidecar vs ambient 的權衡與架構
- [Envoy Proxy — Architecture Overview](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/intro/)：資料面代理的設計
- [Envoy — xDS REST and gRPC protocol](https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol)：LDS/RDS/CDS/EDS 的協定規格
- [SPIFFE — Overview](https://spiffe.io/docs/latest/spiffe-about/overview/)：工作負載身分與 SVID 標準
- [Linkerd — Under the hood of Linkerd's Rust proxy, linkerd2-proxy](https://linkerd.io/2020/07/23/under-the-hood-of-linkerds-state-of-the-art-rust-proxy-linkerd2-proxy/)：特化微代理 vs 通用代理的取捨

### server→client 推送的全景：推還是拉

- [WHATWG HTML Standard — Server-sent events](https://html.spec.whatwg.org/multipage/server-sent-events.html)：SSE 格式、`Last-Event-ID` 與重連語意的規範來源
- [MDN — Using server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)
- [RFC 6455 — The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455)
- [RFC 7540 — HTTP/2](https://httpwg.org/specs/rfc7540.html)：多工與 `SETTINGS_MAX_CONCURRENT_STREAMS`
- [W3C — WebTransport](https://www.w3.org/TR/webtransport/)：Working Draft
- [RFC 8030 — Generic Event Delivery Using HTTP Push](https://www.rfc-editor.org/rfc/rfc8030)：Web Push 協定
- [W3C — Push API](https://www.w3.org/TR/push-api/)

### WebSocket：frame、ping-pong 與水平擴展

- [RFC 7692 — Compression Extensions for WebSocket](https://www.rfc-editor.org/rfc/rfc7692)：permessage-deflate 與 context takeover 的記憶體取捨
- [MDN — Writing WebSocket servers](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers)：frame 解析與遮罩的實作層細節
- [WebSocket.org — WebSocket Protocol guide](https://websocket.org/guides/websocket-protocol/)：握手與 frame 的圖解導覽
- [WebSocket.org — Heartbeat: Ping/Pong, Keep-Alive & Zombie Detection](https://websocket.org/guides/heartbeat/)：心跳與殭屍連線偵測
- [WebSocket.org — Close Codes reference](https://websocket.org/reference/close-codes/)：1000/1001/1006/1009 等狀態碼語意
- [WebSocket.org — WebSockets at Scale](https://websocket.org/guides/websockets-at-scale/)：sticky session 與 pub/sub 背板的擴展架構

### SSE、long-poll 與 WebTransport

- [MDN — WebTransport API](https://developer.mozilla.org/en-US/docs/Web/API/WebTransport_API)
- [IETF — WebTransport over HTTP/3](https://datatracker.ietf.org/doc/draft-ietf-webtrans-http3/)：draft-ietf-webtrans-http3，2026-06 仍為 Internet-Draft

### Socket.io：fallback、rooms 與 redis-adapter

- [Socket.IO — How it works](https://socket.io/docs/v4/how-it-works/)：分層、transport、handshake 全景
- [Socket.IO — The Engine.IO protocol](https://socket.io/docs/v4/engine-io-protocol/)：heartbeat、transport upgrade 的封包級規格
- [Socket.IO — Redis adapter](https://socket.io/docs/v4/redis-adapter/)：Pub/Sub 背板與 sharded adapter
- [Socket.IO — Redis Streams adapter](https://socket.io/docs/v4/redis-streams-adapter/)：持久化背板、斷線重續
- [Socket.IO — Connection state recovery](https://socket.io/docs/v4/connection-state-recovery)：offset 重播與其限制
- [@socket.io/redis-adapter](https://www.npmjs.com/package/@socket.io/redis-adapter)：npm，版本與相依

### WebRTC：媒體、傳輸與信令

- [W3C — WebRTC: Real-Time Communication in Browsers](https://www.w3.org/TR/webrtc/)：Recommendation，2025-03-13 更新版
- [RFC 8445 — Interactive Connectivity Establishment (ICE)](https://www.rfc-editor.org/info/rfc8445/)
- [RFC 8489 — Session Traversal Utilities for NAT (STUN)](https://www.rfc-editor.org/rfc/rfc8489.html)
- [RFC 8656 — Traversal Using Relays around NAT (TURN)](https://www.rfc-editor.org/rfc/rfc8656.html)
- [RFC 8829 — JavaScript Session Establishment Protocol (JSEP)](https://www.rfc-editor.org/rfc/rfc8829.html)：offer/answer 的瀏覽器語意，後由 RFC 9429 更新
- [RFC 8827 — WebRTC Security Architecture](https://datatracker.ietf.org/doc/html/rfc8827)：強制 DTLS-SRTP、禁裸 RTP
- [coturn — 開源 TURN/STUN server](https://github.com/coturn/coturn)
- [Jitsi Videobridge — 開源 SFU 實作](https://github.com/jitsi/jitsi-videobridge)

### REST 設計、版本化與 OpenAPI 契約

- [RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html)：機器可讀錯誤格式，取代 RFC 7807
- [RFC 8594, The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594.html)：下線時間的機器可讀預告
- [The Deprecation HTTP Header Field](https://datatracker.ietf.org/doc/draft-ietf-httpapi-deprecation-header/)：IETF draft，棄用階段的標頭
- [OpenAPI Specification 3.2.0](https://spec.openapis.org/oas/v3.2.0.html)
- [The HTTP QUERY Method](https://datatracker.ietf.org/doc/draft-ietf-httpbis-safe-method-w-body/)：IETF，safe 且冪等、可帶 body 的查詢方法

### 分頁：offset 與 cursor/keyset、深分頁

- [Markus Winand, "We need tool support for keyset pagination"／Use-The-Index-Luke 的 *No Offset*](https://use-the-index-luke.com/no-offset)：seek method 的權威說明與索引原理
- [GraphQL Cursor Connections Specification](https://relay.dev/graphql/connections.htm)：opaque cursor 與 `pageInfo` 的事實標準
- [Elastic, "Paginate search results"](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/paginate-search-results)：`from`/`size` 上限、`search_after` 與 PIT
- [PostgreSQL Documentation, "Row and Array Comparisons"](https://www.postgresql.org/docs/current/functions-comparisons.html)：row value 比較的字典序語意
- [MySQL Reference Manual, "Row Constructor Expression Optimization"](https://dev.mysql.com/doc/refman/8.4/en/row-constructor-optimization.html)：row constructor 與索引使用
- [RFC 8288, *Web Linking*](https://www.rfc-editor.org/rfc/rfc8288.html)：用 `Link` header 的 `rel="next"`/`"prev"` 表達分頁連結

### REST、GraphQL 與 gRPC：三種 API 範式

- [Roy Fielding, "Architectural Styles and the Design of Network-based Software Architectures"](https://ics.uci.edu/~fielding/pubs/dissertation/top.htm)：2000，REST 的原始論文，含六大架構約束與「統一介面」
- [RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html)：方法的 safe / idempotent 定義，REST 倚賴的快取與方法語意
- [GraphQL Specification](https://spec.graphql.org/)：官方規格；最新為 September 2025 edition，前一個完整版為 October 2021
- [GraphQL over HTTP](https://graphql.github.io/graphql-over-http/draft/)：draft 規格：GET 查詢、`application/graphql-response+json` 與真實狀態碼、persisted documents
- [gRPC, "Core concepts, architecture and lifecycle"](https://grpc.io/docs/what-is-grpc/core-concepts/)：四種方法型態：unary / server-streaming / client-streaming / bidirectional
- [Protocol Buffers, "Encoding"](https://protobuf.dev/programming-guides/encoding/)：varint、tag = `(field_number << 3) | wire_type`、欄位號 1–15 佔一個位元組
- [gRPC-Web 協定說明](https://github.com/grpc/grpc-web)：瀏覽器無法用 HTTP/2 trailers，需 proxy 翻譯

### API gateway 的角色：authz、限流、轉換與聚合

- [Microservices.io, "Pattern: API Gateway / Backends for Frontends"](https://microservices.io/patterns/apigateway.html)
- [Sam Newman, "Pattern: Backends For Frontends"](https://samnewman.io/patterns/architectural/bff/)
- [AWS, "Throttle requests to your REST APIs for better throughput in API Gateway"](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html)：帳號層 token bucket 限流官方文件
- [AWS, "Rate-based rule high-level settings in AWS WAF"](https://docs.aws.amazon.com/waf/latest/developerguide/waf-rule-statement-type-rate-based-high-level-settings.html)：限流評估窗口與「近期請求加權、非精確」語意
- [AWS, "Control access to HTTP APIs with JWT authorizers in API Gateway"](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)
- [NGINX, "Deploying NGINX as an API Gateway"](https://www.f5.com/company/blog/nginx/deploying-nginx-plus-as-an-api-gateway-part-1)：閘道四類職責的工程拆解

### API 閘道對照：ALB、API Gateway、KrakenD、Kong

- [AWS, "Choosing between REST APIs and HTTP APIs"](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html)：兩種 API Gateway 的功能與取捨
- [AWS, "Authenticate users using an Application Load Balancer"](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html)：ALB 的 OIDC/Cognito 認證、X-AMZN-OIDC-* header、11KB claim 上限
- [KrakenD, "Open Source"](https://www.krakend.io/open-source/)：Lura Project 與 Linux Foundation 治理
- [Linux Foundation, "Open Source API Gateway KrakenD Becomes Linux Foundation Project"](https://www.linuxfoundation.org/press/press-release/open-source-api-gateway-krakend-becomes-linux-foundation-project)：2021 捐贈 framework 為 Lura
- [Kong, "Why We're Deprecating Cassandra Support"](https://konghq.com/blog/product-releases/cassandra-support-deprecated)：3.4 起 PostgreSQL 為唯一支援資料庫
- [Kong Gateway 官方文件](https://docs.konghq.com/gateway/)：NGINX/OpenResty/Lua plugin 架構、DB-less 模式

### 認證與授權：AuthN、AuthZ 與 OIDC 的位置

- [The OAuth 2.0 Authorization Framework — RFC 6749](https://www.rfc-editor.org/rfc/rfc6749)
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html)：ID Token、`nonce`、`aud` 驗證與認證流程的權威定義
- [OWASP Top 10:2021 — A01 Broken Access Control](https://owasp.org/Top10/2021/A01_2021-Broken_Access_Control/)：含 IDOR 與「認證做了、授權漏了」這類缺陷的分類與成因
- [OWASP — Insecure Direct Object Reference (IDOR)](https://owasp.org/www-community/attacks/insecure_direct_object_reference)
- [RFC 9700 — Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700)：含 access token 受眾綁定、混淆代理類攻擊的防護

### token 的生命週期與撤銷

- [OAuth 2.0 Token Revocation — RFC 7009](https://www.rfc-editor.org/rfc/rfc7009.html)：定義 revocation 端點；MUST 支援撤 refresh token、SHOULD 支援撤 access token 的措辭來源
- [OAuth 2.0 Token Introspection — RFC 7662](https://www.rfc-editor.org/rfc/rfc7662.html)：opaque token 即時驗活的標準
- [JSON Web Token Best Current Practices — RFC 8725](https://www.rfc-editor.org/rfc/rfc8725.html)：JWT 安全實務，含撤銷與短 TTL 的處理建議
- [Best Current Practice for OAuth 2.0 Security — RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)：BCP 240，2025-01；refresh token rotation 與 reuse detection 的權威出處
- [OpenID Connect RP-Initiated Logout 1.0](https://openid.net/specs/openid-connect-rpinitiated-1_0.html)：跨應用登出的標準機制
- [OpenID Connect Back-Channel Logout 1.0](https://openid.net/specs/openid-connect-backchannel-1_0.html)：identity provider 反向通知各應用終止 session

### JWT 與簽章：結構、HS256/RS256 與 JWKS

- [Jones, Bradley, Sakimura, "JSON Web Token (JWT)", RFC 7519, 2015](https://www.rfc-editor.org/rfc/rfc7519)：JWT 結構與註冊 claim 的權威定義
- [Jones, Bradley, Sakimura, "JSON Web Signature (JWS)", RFC 7515, 2015](https://www.rfc-editor.org/rfc/rfc7515)：簽章輸入 `BASE64URL(header).BASE64URL(payload)` 與 compact serialization
- [Jones, "JSON Web Algorithms (JWA)", RFC 7518, 2015](https://www.rfc-editor.org/rfc/rfc7518)：HS256/RS256/ES256 的精確定義與實作要求
- [Jones, "JSON Web Key (JWK)", RFC 7517, 2015](https://www.rfc-editor.org/rfc/rfc7517)：JWK 與 JWK Set、`kid` 與公鑰散佈格式
- [Sheffer, Hardt, Jones, "JSON Web Token Best Current Practices", RFC 8725, 2020](https://www.rfc-editor.org/rfc/rfc8725)：`alg:none`、演算法混淆等攻擊與對策清單
- [PortSwigger Web Security Academy, "JWT algorithm confusion attacks"](https://portswigger.net/web-security/jwt/algorithm-confusion)：RS256→HS256 混淆攻擊的可操作拆解

### RBAC 與 ABAC：兩種授權模型

- [Ferraiolo, Kuhn, Sandhu, et al., "Role-Based Access Control" — ANSI/INCITS 359](https://csrc.nist.gov/projects/role-based-access-control)：NIST RBAC 模型與標準，含 Core / Hierarchical / Constrained 與職責分離
- [Hu et al., "Guide to Attribute Based Access Control (ABAC) Definition and Considerations" — NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/upd2/final)：ABAC 權威定義
- [Kuhn, Coyne, Weil, "Adding Attributes to Role-Based Access Control", IEEE Computer 43(6), 2010](https://csrc.nist.gov/files/pubs/journal/2010/06/adding-attributes-to-rolebased-access-control/final/docs/kuhn-coyne-weil-10.pdf)：RBAC + 屬性混合模型的官方論證
- ["eXtensible Access Control Markup Language (XACML) Version 3.0" — OASIS Standard](https://docs.oasis-open.org/xacml/3.0/xacml-3.0-core-spec-os-en.html)：PEP/PDP/PIP/PAP 架構的經典規格
- [Pang et al., "Zanzibar: Google's Consistent, Global Authorization System", USENIX ATC 2019](https://www.usenix.org/conference/atc19/presentation/pang)：ReBAC 與關係元組的代表作
- [Open Policy Agent](https://www.openpolicyagent.org/)：CNCF 畢業專案，Rego policy 語言與通用決策引擎
- [Cedar — open-source authorization language and engine](https://docs.cedarpolicy.com/)：可同時表達 RBAC/ABAC、可形式化分析

### OAuth2、OIDC 與 OAuth 2.1：grant 類型與現況

- [The OAuth 2.1 Authorization Framework — draft-ietf-oauth-v2-1](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/)：IETF datatracker，2026-06 仍為 draft-15
- [Proof Key for Code Exchange by OAuth Public Clients — RFC 7636](https://www.rfc-editor.org/rfc/rfc7636)
- [OAuth 2.0 Token Introspection — RFC 7662](https://www.rfc-editor.org/rfc/rfc7662)
- [OAuth 2.1 official overview](https://oauth.net/2.1/)：oauth.net

## Part 4 · 並發、過載與韌性

### 並發不是平行：兩個常被混用的詞

- [Rob Pike, "Concurrency is not Parallelism" 投影片](https://go.dev/talks/2012/waza.slide)：go.dev/talks
- [Gene Amdahl, "Validity of the single processor approach to achieving large scale computing capabilities", AFIPS 1967](https://dl.acm.org/doi/10.1145/1465482.1465560)：Amdahl's Law 原始論文
- [Go 1.14 Release Notes](https://go.dev/doc/go1.14#runtime)：非同步搶佔，asynchronous preemption
- [libuv thread pool 官方文件](https://docs.libuv.org/en/v1.x/threadpool.html)：UV_THREADPOOL_SIZE 預設 4、最大 1024、用於 fs 與 DNS
- ["Concurrency (computer science)" — Wikipedia](https://en.wikipedia.org/wiki/Concurrency_(computer_science))：並發的一般概念與正交性

### event loop：單執行緒怎麼同時做很多事

- [libuv 官方設計文件](https://docs.libuv.org/en/v1.x/design.html)：event loop 各 phase、poll timeout 如何算出、為何 poll 會阻塞
- [Node.js 官方「The Node.js Event Loop」指南](https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick)：phase 順序、`process.nextTick` 與 microtask、`setImmediate` vs `setTimeout`
- [Node.js `dns` 模組文件](https://nodejs.org/api/dns.html)：`dns.lookup` 走 getaddrinfo/threadpool 與 `dns.resolve` 走 c-ares 的差別

### 阻塞與非阻塞 I/O

- [Dan Kegel, "The C10K problem"](http://www.kegel.com/c10k.html)：高並發 I/O 模型的經典總覽
- [Linux `epoll(7)` man page](https://man7.org/linux/man-pages/man7/epoll.7.html)：interest list、ready list 與 edge/level-triggered 語意
- [Linux `read(2)` man page](https://man7.org/linux/man-pages/man2/read.2.html)：`O_NONBLOCK` 下的 `EAGAIN`/`EWOULDBLOCK` 語意
- [Gaurav Banga, Jeffrey C. Mogul et al., "A Scalable and Explicit Event Delivery Mechanism for UNIX"](https://www.usenix.org/legacy/events/usenix99/full_papers/banga/banga.pdf)：USENIX ATC 1999，epoll 風格機制的學術源頭之一
- [Jens Axboe, "Efficient IO with io_uring"](https://kernel.dk/io_uring.pdf)：io_uring 的提交/完成環設計文件
- ["io_uring" — Wikipedia](https://en.wikipedia.org/wiki/Io_uring)：含 2023 年起的安全爭議與各家停用/限制現況

### thread pool 與 worker threads：CPU 密集怎麼辦

- [Node.js 官方 `worker_threads` 文件](https://nodejs.org/api/worker_threads.html)：Stable；transfer list、SharedArrayBuffer 與 structured clone 的傳值語意
- [Node.js 官方 `cluster` 文件](https://nodejs.org/api/cluster.html)：多行程擴展網路請求、與 worker threads 的分工
- [MDN, `Atomics.wait()`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Atomics/wait)：只能在 worker 上同步阻塞、配合 `SharedArrayBuffer` 協調執行緒
- [V8 team, "Atomics.wait, Atomics.notify, Atomics.waitAsync"](https://v8.dev/features/atomics)：共享記憶體下的執行緒同步原語
- [Piscina — Node.js worker thread pool 實作](https://github.com/piscinajs/piscina)：池化、排隊、逾時、zero-copy transfer

### race condition 與原子性：跨 DB、cache、runtime

- [Redis, "SET" command reference](https://redis.io/docs/latest/commands/set/)：8.4 起的 `IFEQ`/`IFNE` compare-and-set 選項
- [Redis, "Scripting with Lua"](https://redis.io/docs/latest/develop/programmability/eval-intro/)：EVAL 的原子性與「腳本必須快」的緣由
- [CockroachLabs, "What write skew looks like"](https://www.cockroachlabs.com/blog/what-write-skew-looks-like/)：write skew 的具體情境拆解

### 並發模型比較：thread、event-loop、actor、coroutine、CSP

- [C. A. R. Hoare, "Communicating Sequential Processes", CACM 21(8):666–677, 1978](https://dl.acm.org/doi/10.1145/359576.359585)：CSP 原始論文
- [Carl Hewitt, Peter Bishop, Richard Steiger, "A Universal Modular ACTOR Formalism for Artificial Intelligence", IJCAI 1973](https://dl.acm.org/doi/10.5555/1624775.1624804)：actor model 原始論文
- [Rob Pike, "Concurrency is not Parallelism"](https://go.dev/blog/waza-talk)：Go 官方部落格 talk，並發與平行之別的經典闡述
- [The Go Memory Model](https://go.dev/ref/mem)：共享記憶體、channel 與同步的官方語意
- ["Container-aware GOMAXPROCS"](https://go.dev/blog/container-aware-gomaxprocs)：Go 官方，Go 1.25 起 cgroup 感知的預設
- [JEP 444: Virtual Threads](https://openjdk.org/jeps/444)：Java 21 正式版 virtual threads 的規格
- [Joe Armstrong, "Making reliable distributed systems in the presence of software errors", PhD thesis, 2003](https://erlang.org/download/armstrong_thesis_2003.pdf)：Erlang 的 let-it-crash 與監督樹哲學
- [Akka BSL License FAQ](https://akka.io/bsl-license-faq)：Akka 2022 改 BSL 授權的官方說明

### 背壓：當下游跟不上

- [Reactive Streams 規格](https://www.reactive-streams.org/)：`Publisher`/`Subscriber`/`Subscription`/`Processor` 與 `request(n)` 的非阻塞背壓語意
- [Node.js 官方〈Backpressuring in Streams〉(`write()` 回傳值、`highWaterMark`、`drain` 事件與 `pipe` 的自動背壓)](https://nodejs.org/en/learn/modules/backpressuring-in-streams)
- [gRPC 官方〈Flow Control〉(基於 HTTP/2 視窗的串流背壓、`isReady`/`onReadyHandler`)](https://grpc.io/docs/guides/flow-control/)
- [RFC 9113, "HTTP/2"(§5.2 Flow Control:stream 與 connection 級視窗、`WINDOW_UPDATE`、初始視窗 65,535)](https://httpwg.org/specs/rfc9113.html#FlowControl)
- [RFC 9293, "Transmission Control Protocol"(§3.8.6 "Managing the Window"：接收視窗 rwnd 與 zero-window 流量控制)](https://www.rfc-editor.org/rfc/rfc9293.html)
- [AWS Builders' Library, "Using load shedding to avoid overload"(背壓與主動丟棄工作之間的取捨)](https://aws.amazon.com/builders-library/using-load-shedding-to-avoid-overload/)

### rate limiting：token bucket、leaky bucket 與分散式限流

- [RFC 6585, "Additional HTTP Status Codes"](https://datatracker.ietf.org/doc/html/rfc6585)：定義 429 Too Many Requests
- [RFC 9110, "HTTP Semantics" §10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#name-retry-after)：Retry-After 標頭語意
- [Generic Cell Rate Algorithm（GCRA 的 TAT／emission interval／tolerance 定義與來源）, Wikipedia](https://en.wikipedia.org/wiki/Generic_cell_rate_algorithm)
- [Stripe Engineering, "Scaling your API with rate limiters"](https://stripe.com/blog/rate-limiters)：token bucket 在生產環境的分層限流
- [Cloudflare, "How we built rate limiting capable of scaling to millions of domains"](https://blog.cloudflare.com/counting-things-a-lot-of-different-things/)：滑動窗計數近似的公式與實測誤差
- [Brandur Leach, "Rate limiting, cells, and GCRA"](https://brandur.org/rate-limiting)：GCRA 的工程直覺與 Redis 實作
- [Redis Docs, "Rate limiting"](https://redis.io/docs/latest/develop/use-cases/rate-limiter/)：用 Lua 腳本做原子限流的官方範例

### load shedding：主動丟掉一部分流量

- [Nichols, Jacobson, "Controlled Delay Active Queue Management", RFC 8289, 2018](https://www.rfc-editor.org/rfc/rfc8289.html)：CoDel：以停留時間而非佇列長度做主動丟棄
- [Envoy 官方文件, "Adaptive Concurrency Filter"](https://www.envoyproxy.io/docs/envoy/latest/configuration/http/http_filters/adaptive_concurrency_filter)：梯度控制器、minRTT/sampleRTT 與動態併發上限
- [Netflix Technology Blog, "Performance Under Load: Adaptive Concurrency Limits"](https://netflixtechblog.medium.com/performance-under-load-3e6fa9a60581)：從 TCP 壅塞控制與 Little's Law 推導自適應併發上限

### circuit breaker：三態與半開試探

- [Martin Fowler, "CircuitBreaker"](https://martinfowler.com/bliki/CircuitBreaker.html)：三態機制、自我恢復與半開試探的標準描述，溯源至 Nygard《Release It!》
- [Resilience4j CircuitBreaker 官方文件](https://resilience4j.readme.io/docs/circuitbreaker)：六態模型、count/time-based 滑動窗、slow-call 偵測與各預設值
- [Polly, "Circuit breaker resilience strategy"](https://www.pollydocs.org/strategies/circuit-breaker.html)：.NET 的 failure-ratio 斷路器、半開單筆試探、BrokenCircuitException
- [Envoy, "Outlier detection"](https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/outlier)：service mesh 層的 per-host 被動健康檢查與 eject，對照行程內斷路器
- [Marc Brooker, "Fixing retries with token buckets and circuit breakers"](https://brooker.co.za/blog/2022/02/28/retries.html)：斷路器與 retry token bucket 如何咬合避免放大故障

### retry storm 與 metastable failure

- [Huang, Charapko, et al., "Metastable Failures in the Wild", USENIX OSDI 2022](https://www.usenix.org/conference/osdi22/presentation/huang-lexiang)：load-spiking vs capacity-decreasing 觸發分類、真實案例與時長
- [Marc Brooker, "Metastability and Distributed Systems"](https://brooker.co.za/blog/2021/05/24/metastable.html)：遲滯與正回饋迴圈的直覺

### 排隊的直覺：為什麼利用率逼近 1 會爆炸

- [M/M/1 queue](https://en.wikipedia.org/wiki/M/M/1_queue)：Wikipedia，含 `E[N] = ρ/(1−ρ)`、`E[T] = 1/(μ−λ)` 與穩定性條件的完整推導
- [Kingman's formula](https://en.wikipedia.org/wiki/Kingman%27s_formula)：Wikipedia，G/G/1 的 VUT 重流量近似與變異係數的角色
- [J. F. C. Kingman, "The Single Server Queue in Heavy Traffic", Math. Proc. Camb. Phil. Soc. 57(4):902-904, 1961](https://www.cambridge.org/core/journals/mathematical-proceedings-of-the-cambridge-philosophical-society/article/abs/single-server-queue-in-heavy-traffic/81C55BC00A68FE6D5385638AA0B0AF37)：變異性主導重流量延遲的原始論文
- [John D. Cook, "Queueing theory and economies of scale"](https://www.johndcook.com/blog/2022/01/15/queueing-and-scale/)：為什麼一個 M/M/c 大池勝過多個 M/M/1 小池的直覺與算術
- [M/M/c queue](https://en.wikipedia.org/wiki/M/M/c_queue)：Wikipedia，多伺服器共享佇列與資源池化的公式

### timeout、deadline 與 budget：把等待變成有界

- [gRPC blog, "gRPC and Deadlines"](https://grpc.io/blog/deadlines/)：為什麼 deadline 優於 timeout、傳遞的工程動機

### bulkhead：艙壁隔離

- [Michael Nygard, “Stability Patterns and Antipatterns”（簡報）](https://cdn.oreillystatic.com/en/assets/1/event/79/Stability%20Patterns%20Presentation.pdf)：bulkhead／circuit breaker／fail fast 等穩定性模式與反模式的權威講義投影片
- [Microsoft Azure Architecture Center, "Bulkhead pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead)
- [Resilience4j 官方文件, "Bulkhead"](https://resilience4j.readme.io/docs/bulkhead)：`SemaphoreBulkhead` vs `ThreadPoolBulkhead` 的設定與語意
- [Netflix/Hystrix Wiki, "How it Works"](https://github.com/Netflix/Hystrix/wiki/How-it-Works)：`THREAD` 與 `SEMAPHORE` 兩種 isolation strategy 的原始設計
- [Wikipedia, "Bulkhead pattern"](https://en.wikipedia.org/wiki/Bulkhead_pattern)
- [Wikipedia, "Little's law"](https://en.wikipedia.org/wiki/Little%27s_law)：穩態併發 = 到達率 × 處理時間

### health check：liveness 與 readiness

- [Kubernetes, "Liveness, Readiness, and Startup Probes"](https://kubernetes.io/docs/concepts/workloads/pods/probes/)：三種探針的語意與差異
- [Kubernetes, "Configure Liveness, Readiness and Startup Probes"](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)：參數與設定細節，含預設值
- [Kubernetes Blog, "Kubernetes 1.24: gRPC container probes in beta"](https://kubernetes.io/blog/2022/05/13/grpc-probes-now-in-beta/)：原生 gRPC 探針的演進，後於 v1.27 GA
- [gRPC Health Checking Protocol](https://github.com/grpc/grpc/blob/master/doc/health-checking.md)：gRPC 健康檢查的標準規格

### graceful shutdown：怎麼好好地關掉一個行程

- [Kubernetes, "Pod Lifecycle"](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/)：Termination of Pods，preStop 與寬限期的官方時序
- [Kubernetes, "Explore Termination Behavior for Pods And Their Endpoints"](https://kubernetes.io/docs/tutorials/services/pods-and-endpoint-termination-flow/)：端點移除與行程關閉並行的官方教學
- [Google Cloud Blog, "Kubernetes best practices: terminating with grace"](https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-terminating-with-grace)
- [CNCF, "Decoding the pod termination lifecycle in Kubernetes: a comprehensive guide"](https://www.cncf.io/blog/2024/12/19/decoding-the-pod-termination-lifecycle-in-kubernetes-a-comprehensive-guide/)
- [Docker Docs, "docker container stop"](https://docs.docker.com/reference/cli/docker/container/stop/)：預設 10 秒寬限期與 `--time`
- [Deni Bertović, "Containers and Signal Handling: Why You Need to Care About PID 1"](https://www.denibertovic.com/posts/containers-and-signal-handling-why-you-need-to-care-about-pid-1/)
- [Hynek Schlawack, "Why Your Dockerized Application Isn't Receiving Signals"](https://hynek.me/articles/docker-signals/)：shell form 不轉發訊號
- [RabbitMQ, "Consumer Acknowledgements and Publisher Confirms"](https://www.rabbitmq.com/docs/confirms)：未 ack 投遞在連線關閉時自動 requeue

### fallback 與降級：壞掉時退到哪

- [Netflix, "Hystrix" — README](https://github.com/Netflix/Hystrix)：官方宣告進入維護模式、概念仍有效
- [AuthZed, "Understanding Failed Open and Fail Closed in Software Engineering"](https://authzed.com/blog/fail-open)：授權路徑 fail-open vs fail-closed 的取捨

### 冷啟動與暖機：第一個請求為什麼那麼慢

- [AWS, "Understanding the Lambda execution environment lifecycle"](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html)：Init/Invoke/Shutdown 三相位、10 秒 Init 上限、凍結與重用
- [AWS Compute Blog, "Understanding and remediating cold starts: An AWS Lambda perspective"](https://aws.amazon.com/blogs/compute/understanding-and-remediating-cold-starts-an-aws-lambda-perspective/)
- [AWS, "Improving startup performance with Lambda SnapStart"](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)：支援的 runtime、快照與恢復鉤子
- [Microsoft for Java Developers, "How tiered compilation works in OpenJDK"](https://devblogs.microsoft.com/java/how-tiered-compilation-works-in-openjdk/)：C1/C2 與分層門檻
- [Baeldung, "Tiered Compilation in JVM"](https://www.baeldung.com/jvm-tiered-compilation)：Tier3/Tier4CompileThreshold 預設值
- [V8 Blog, "Maglev — V8's Fastest Optimizing JIT"](https://v8.dev/blog/maglev)：Ignition→Sparkplug→Maglev→TurboFan 四層
- [GraalVM, "Native Image" 官方文件](https://www.graalvm.org/latest/reference-manual/native-image/)：AOT 編譯、閉世界假設、PGO

### 長尾延遲：p99 從哪裡來

- [Dean, Barroso, "The Tail at Scale", Communications of the ACM 56(2):74–80, 2013](https://www.barroso.org/publications/TheTailAtScale.pdf)：長尾延遲的奠基論文，含扇出放大、hedged/tied requests、BigTable 實測
- ["The Tail at Scale" — CACM 線上全文](https://cacm.acm.org/research/the-tail-at-scale/)
- ["The Tail at Scale" 導讀](https://blog.acolyer.org/2015/01/15/the-tail-at-scale/)：the morning paper
- [Gil Tene, "How NOT to Measure Latency"](https://www.youtube.com/watch?v=lJ8ydIuPFeU)：為什麼平均與 coordinated omission 會系統性低估尾巴

### N+1 查詢：一個迴圈打爆資料庫

- [Solving the N+1 Problem with DataLoader — GraphQL.js 官方文件](https://www.graphql-js.org/docs/n1-dataloader/)：posts/authors 的標準範例與 per-request loader
- [Batching — GraphQL Java 官方文件](https://graphql-java.com/documentation/batching/)：JVM 生態的 DataLoader 與顯式 dispatch
- [N+1 Problem in Hibernate and Spring Data JPA — Baeldung](https://www.baeldung.com/spring-hibernate-n1-problem)：JOIN FETCH、@BatchSize、EntityGraph 對照
- [Preload vs Eager Load vs Joins vs Includes — BigBinary](https://www.bigbinary.com/blog/preload-vs-eager-load-vs-joins-vs-includes)：Rails includes 如何在 preload 與 eager_load 之間自動切換
- [Database access optimization — Django 官方文件](https://docs.djangoproject.com/en/stable/topics/db/optimization/)：select_related vs prefetch_related

### 批次、coalescing 與 debounce

- [graphql/dataloader](https://github.com/graphql/dataloader)：README：per-tick batching、batch function 的等長同序契約、request-scoped 快取
- [DataLoader API 文件](https://www.npmjs.com/package/dataloader)：`maxBatchSize`、`batchScheduleFn`、cache 選項
- [Go `golang.org/x/sync/singleflight`](https://pkg.go.dev/golang.org/x/sync/singleflight)：`Do` / `DoChan` / `Forget` 與 `shared` 語意
- [Apache Kafka Producer Configs](https://kafka.apache.org/documentation/#producerconfigs)：`batch.size`、`linger.ms` 的 size-or-time 語意與預設值
- [Lodash `_.debounce`](https://lodash.com/docs/#debounce)：`leading` / `trailing` / `maxWait`，throttle 即帶 maxWait 的 debounce
- [John Nagle, RFC 896, "Congestion Control in IP/TCP Internetworks", 1984](https://www.rfc-editor.org/rfc/rfc896)：Nagle 演算法原始定義
- [Marc Brooker, "It's always TCP_NODELAY. Every damn time."](https://brooker.co.za/blog/2024/05/09/nagle.html)：Nagle × delayed-ACK 互鎖的實務剖析

### 連線池調校

- [HikariCP Configuration](https://github.com/brettwooldridge/HikariCP#configuration-knobs-baby)：connectionTimeout / maxLifetime / idleTimeout 等旋鈕的預設值與約束
- [Prisma — Connection pool](https://www.prisma.io/docs/orm/prisma-client/setup-and-configuration/databases-connections/connection-pool)：serverless 下每函式各自開池與外部 pooler 的必要性、預設池大小演進

## Part 5 · 分散式系統核心

### 為什麼分散式這麼難：partial failure 與失敗模型

- [Fischer, Lynch, Paterson, "Impossibility of Distributed Consensus with One Faulty Process", JACM 32(2):374–382, 1985](https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf)：FLP 不可能性：非同步網路下，只要一個節點可能崩潰，就沒有確定性協定能同時保證 agreement/validity/termination
- [Akkoyunlu, Ekanadham, Huber, "Some Constraints and Tradeoffs in the Design of Network Communications", SOSP 1975](https://dl.acm.org/doi/10.1145/800213.806523)：兩將軍問題不可能性的原始出處
- [Lamport, Shostak, Pease, "The Byzantine Generals Problem", ACM TOPLAS 4(3):382–401, 1982](https://lamport.azurewebsites.net/pubs/byz.pdf)：n ≥ 3m + 1 下界的原始證明
- ["October 21 post-incident analysis", The GitHub Blog, 2018](https://github.blog/2018-10-30-oct21-post-incident-analysis/)：一次 43 秒網路分區如何透過自動故障切換釀成資料分岔與 24 小時降級的事故剖析

### 共識：讓一群會當機的機器同意一件事

- [Fischer, Lynch, Paterson, "Impossibility of Distributed Consensus with One Faulty Process", JACM 32(2):374-382, 1985](https://dl.acm.org/doi/10.1145/3149.214121)：FLP 不可能性的原始證明
- [Ongaro, Ousterhout, "In Search of an Understandable Consensus Algorithm", USENIX ATC 2014](https://raft.github.io/raft.pdf)：Raft 論文
- [Ongaro, "Consensus: Bridging Theory and Practice", Stanford PhD dissertation, 2014](https://github.com/ongardie/dissertation)：成員變更、log 壓縮、線性一致讀的完整工程細節
- [Raft 官方網站](https://raft.github.io/)：含互動視覺化、實作清單
- [Lamport, "The Part-Time Parliament", ACM TOCS 16(2):133-169, 1998](https://lamport.azurewebsites.net/pubs/lamport-paxos.pdf)：Paxos 原始論文
- [Lamport, "Paxos Made Simple", 2001](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf)：較好讀的 Paxos 重述
- [Howard, Mortier, "Paxos vs Raft: Have we reached consensus on distributed consensus?", PaPoC 2020](https://arxiv.org/abs/2004.05074)：兩者本質比較

### leader election：選出唯一的寫入點

- [ZooKeeper Recipes and Solutions](https://zookeeper.apache.org/doc/current/recipes.html)：ephemeral sequential znode 的 leader election recipe 與如何用「只看前一個」避開 herd effect
- [etcd concurrency/election API 文件](https://pkg.go.dev/go.etcd.io/etcd/client/v3/concurrency)：外包選舉、session 租約與預設 60s TTL
- [KIP-996: Pre-Vote](https://cwiki.apache.org/confluence/display/KAFKA/KIP-996%3A+Pre-Vote)：Kafka KRaft 在遞增 term 前先過半確認，避免無謂選舉

### 分散式鎖：Redlock、fencing token 與「鎖其實是租約」

- [Martin Kleppmann, "How to do distributed locking", 2016](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html)：Redlock 批評與 fencing token 的經典論述，effiency vs correctness 的分界源頭
- [Salvatore Sanfilippo (antirez), "Is Redlock safe?", 2016](https://antirez.com/news/101)：Redlock 作者對上文的逐點回應
- [Redis 官方分散式鎖文件](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/)：Redlock 演算法描述、`SET NX PX`、N=5 多數決、解鎖比對與 fencing token 建議
- [ZooKeeper Recipes — Locks](https://zookeeper.apache.org/doc/current/recipes.html#sc_recipes_Locks)：ephemeral sequential znode 鎖、watch 前一個節點以避開 herd effect
- [etcd: Why etcd](https://etcd.io/docs/latest/learning/why/)：全域單調遞增 revision 的語意，可直接當 fencing token

### quorum：R + W > N 的鴿巢原理

- [Gilbert, Lynch, "Brewer's Conjecture and the Feasibility of Consistent, Available, Partition-Tolerant Web Services", ACM SIGACT News 2002](https://dl.acm.org/doi/10.1145/564585.564601)：一致性、可用性、分區容忍三者不可兼得的形式化證明
- [Martin Kleppmann, "Please stop calling databases CP or AP"](https://martin.kleppmann.com/2015/05/11/please-stop-calling-databases-cp-or-ap.html)：為什麼嚴格 quorum 仍非線性一致、以及它的邊界
- [Kyle Kingsbury (aphyr), "The trouble with timestamps"](https://aphyr.com/posts/299-the-trouble-with-timestamps)：LWW 與牆鐘時間戳在並行寫下靜默丟更新

### 邏輯時鐘與排序：Lamport、向量時鐘、HLC 與 TrueTime

- [Kulkarni, Demirbas, Madeppa, Avva, Leone, "Logical Physical Clocks and Consistent Snapshots in Globally Distributed Databases", OPODIS 2014](https://cse.buffalo.edu/tech-reports/2014-04.pdf)：HLC 原始論文
- [Corbett et al., "Spanner: Google's Globally-Distributed Database", OSDI 2012](https://research.google.com/archive/spanner-osdi2012.pdf)：TrueTime 與 commit-wait
- [Google Cloud, "TrueTime and external consistency"](https://cloud.google.com/spanner/docs/true-time-external-consistency)：Spanner 官方對外部一致性的說明
- [CockroachDB, "Life of a Distributed Transaction / Clock synchronization"](https://www.cockroachlabs.com/docs/stable/architecture/transaction-layer)：HLC、max-offset 與 uncertainty interval 的工程實作
- [Tyagi et al., "Implementation of Cluster-wide Logical Clock and Causal Consistency in MongoDB", SIGMOD 2019](https://dl.acm.org/doi/10.1145/3299869.3314049)：HLC 在 MongoDB 的 cluster time 與 signed cluster time

### 複製策略：單主、多主、無主

- [PostgreSQL 官方文件：High Availability, Load Balancing, and Replication](https://www.postgresql.org/docs/current/high-availability.html)：單主同步／非同步、多主衝突解決的工程呈現
- [MySQL 8.4 官方文件：Semisynchronous Replication](https://dev.mysql.com/doc/refman/8.4/en/replication-semisync.html)：`rpl_semi_sync_source_wait_point` 的 `AFTER_SYNC`／`AFTER_COMMIT` 差別
- ["CockroachDB: The Resilient Geo-Distributed SQL Database", SIGMOD 2020](https://dl.acm.org/doi/10.1145/3318464.3386134)：per-range 共識複製、leaseholder 與 Raft leader 的關係
- [Werner Vogels, "Eventually Consistent"](https://www.allthingsdistributed.com/2008/12/eventually_consistent.html)：無主／最終一致背後的取捨哲學

### 2PC 與分散式交易：原子提交與它的阻塞代價

- [Gray, Lamport, "Consensus on Transaction Commit", ACM TODS 31(1):133-160, 2006](https://dl.acm.org/doi/10.1145/1132863.1132867)：證明 2PC 是單 coordinator 的退化共識、提出可容錯的 Paxos Commit
- [Skeen, "Nonblocking Commit Protocols", ACM SIGMOD 1981](https://dl.acm.org/doi/10.1145/582318.582339)：3PC 的源頭，與「不阻塞」的前提
- [X/Open Distributed Transaction Processing: The XA Specification](https://pubs.opengroup.org/onlinepubs/009680699/toc.pdf)：2PC 的標準介面、heuristic decision 的定義
- [PostgreSQL 官方文件 — PREPARE TRANSACTION](https://www.postgresql.org/docs/current/sql-prepare-transaction.html)：prepared transaction 的語意、孤兒交易與鎖的危險
- [Corbett et al., "Spanner: Google's Globally-Distributed Database", OSDI 2012](https://research.google/pubs/spanner-googles-globally-distributed-database/)：2PC 跨在 Paxos group 之上以消除 coordinator 單點

### consistent hashing：節點進出時少搬一點資料

- [Karger, Lehman, Leighton, Levine, Lewin, Panigrahy, "Consistent Hashing and Random Trees: Distributed Caching Protocols for Relieving Hot Spots on the World Wide Web", STOC 1997](https://dl.acm.org/doi/10.1145/258533.258660)：consistent hashing 原始論文
- [Thaler, Ravishankar, "Using Name-Based Mappings to Increase Hit Rates", IEEE/ACM Transactions on Networking, 1998](https://www.eecs.umich.edu/techreports/cse/96/CSE-TR-316-96.pdf)：rendezvous / HRW hashing
- [Lamping, Veach, "A Fast, Minimal Memory, Consistent Hash Algorithm", 2014](https://arxiv.org/abs/1406.2294)：jump consistent hash
- [Stanford CS168, Lecture 1 — "Introduction and Consistent Hashing"](https://web.stanford.edu/class/cs168/l/l1.pdf)：搬動量與 vnode 的數學推導

### gossip 與 anti-entropy

- [Demers et al., "Epidemic Algorithms for Replicated Database Maintenance", PODC 1987](https://dl.acm.org/doi/10.1145/41840.41841)：anti-entropy 與 rumor mongering 的奠基論文
- [Karp et al., "Randomized Rumor Spreading", FOCS 2000](https://zoo.cs.yale.edu/classes/cs426/2013/bib/karp00randomized.pdf)：push-pull 的 log₃ N 收斂界
- [HashiCorp, "Making Gossip More Robust with Lifeguard"](https://www.hashicorp.com/blog/making-gossip-more-robust-with-lifeguard)：SWIM 在生產規模下的誤判問題與修正
- [Apache Cassandra Architecture — Gossip](https://cassandra.apache.org/doc/latest/cassandra/architecture/gossip.html)：三段 SYN/ACK/ACK2 交換與 generation/heartbeat 版本

### 時間與日期：UTC、epoch、timezone 與 DST 的應用層坑

- [RFC 3339, "Date and Time on the Internet: Timestamps"](https://www.rfc-editor.org/rfc/rfc3339)：Klyne & Newman, 2002；Internet 上日期時間格式的基準，含 `Z` 與偏移標註
- [RFC 9557, "Date and Time on the Internet: Timestamps with Additional Information"](https://www.rfc-editor.org/info/rfc9557/)：IXDTF，2024；以 `[Area/Location]` 後綴在時間戳裡標註 IANA 時區名，向後相容地擴充 RFC 3339
- [TC39 Temporal proposal](https://tc39.es/proposal-temporal/docs/)：JavaScript 新日期時間 API，`Instant` / `ZonedDateTime` 等型別 DST-aware，2026 進入 Stage 4、納入 ECMAScript 2026
- ["Falsehoods programmers believe about time"](https://infiniteundo.com/post/25326999628/falsehoods-programmers-believe-about-time)：時間處理常見錯誤假設清單
- [Google, "Leap Smear"](https://developers.google.com/time/smear)：閏秒抹平的做法說明
- [BIPM, CGPM Resolution 4 (2022)](https://www.bipm.org/en/cgpm-2022/resolution-4)：停止插入閏秒的國際決議原文

## Part 6 · 架構、雲端與發布

### 解耦：時間、空間、同步性、資料、實作五種耦合

- [Gregor Hohpe, "The Many Facets of Coupling"](https://www.enterpriseintegrationpatterns.com/ramblings/coupling_facets.html)：耦合的八個正交維度，本章五維分類的權威來源
- [Gregor Hohpe, "Event-driven = Loosely coupled? Not so fast!"](https://www.enterpriseintegrationpatterns.com/ramblings/eventdriven_coupling.html)：為什麼非同步訊息不會自動帶來鬆耦合、資料格式耦合仍在
- [W. Stevens, G. Myers, L. Constantine, "Structured Design", IBM Systems Journal 13(2):115–139, 1974](https://ieeexplore.ieee.org/document/5388187)：coupling 與 cohesion 最早的期刊發表
- [Martin Fowler, "BoundedContext"](https://martinfowler.com/bliki/BoundedContext.html)：依業務語言而非技術分層切邊界

### 同步與非同步通訊

- [Jeffrey Dean, Luiz André Barroso, "The Tail at Scale", Communications of the ACM 56(2):74-80, 2013](https://dl.acm.org/doi/10.1145/2408776.2408794)：尾延遲如何在扇出/串接下放大主宰整體表現
- [MDN, "Connection management in HTTP/1.x"](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Connection_management_in_HTTP_1.x)：keep-alive、pipelining 與 head-of-line blocking

### 事件驅動架構：event notification 與 event-carried state transfer

- [Amazon SNS 官方文件，"Publishing large messages with Amazon SNS and Amazon S3"](https://docs.aws.amazon.com/sns/latest/dg/large-message-payloads.html)：256 KB 上限與 S3 claim-check 解法
- [Apache Kafka 官方文件，"Log Compaction"](https://kafka.apache.org/documentation/#compaction)：compacted topic 如何保留每個 key 的最新狀態、支撐狀態重建

### Event sourcing 與 CQRS：狀態是不可變事件序列

- [Martin Fowler, "Event Sourcing"](https://martinfowler.com/eaaDev/EventSourcing.html)：奠基文章，含 replay 與外部系統互動、snapshot、external query 的經典討論
- [Martin Fowler, "CQRS"](https://martinfowler.com/bliki/CQRS.html)：含「對大多數系統是有風險的複雜度」的著名警示
- [Greg Young, "CQRS Documents"](https://cqrs.files.wordpress.com/2010/11/cqrs_documents.pdf)：命名者本人的權威整理，PDF
- [Bertrand Meyer, *Object-Oriented Software Construction*](https://en.wikipedia.org/wiki/Command%E2%80%93query_separation)：1988，CQS 命令查詢分離原則的原典
- [Microsoft, "Event Sourcing pattern"](https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing)：Azure Architecture Center，含投影、snapshot、一致性取捨的工程整理
- [Confluent, "Log Compaction"](https://docs.confluent.io/kafka/design/log_compaction.html)：Kafka 官方文件，理解為何 compaction 與 event sourcing 的完整歷史需求相衝突
- [KurrentDB](https://docs.kurrent.io/)：原 EventStoreDB）官方文件（專用 event store 的 stream、optimistic concurrency、projection 機制

### durable execution：Temporal、Step Functions 與長流程

- [Hector Garcia-Molina, Kenneth Salem, "Sagas", SIGMOD '87, pp. 249–259](https://dl.acm.org/doi/10.1145/38713.38742)：長流程與補償交易的原典
- [Temporal 官方文件, "Workflow Execution"](https://docs.temporal.io/workflow-execution)：事件歷史、replay、determinism 的權威說明
- [Temporal 官方文件, "Workflow Execution limits"](https://docs.temporal.io/workflow-execution/limits)：51,200 事件 / 50 MB 上限與 Continue-As-New
- [AWS Step Functions 官方文件, "Choosing workflow type"](https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html)：Standard vs Express：exactly-once / at-least-once / at-most-once、時長上限、計費模型
- [AWS Step Functions 官方文件, "What is Step Functions?"](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)：ASL 狀態機、託管編排的整體定位

### 無狀態與有狀態：為什麼 serverless 要無狀態

- [The Twelve-Factor App — VI. Processes](https://12factor.net/processes)：把 app 當無狀態 process 跑、記憶體只能是單次交易內的快取、sticky session 是違反
- [The Twelve-Factor App — IV. Backing Services](https://12factor.net/backing-services)：把資料庫／快取／佇列當可替換的附加資源
- [AWS Lambda — Implementing statelessness in functions](https://docs.aws.amazon.com/lambda/latest/dg/concepts-application-design.html)：官方無狀態實作指引、避免全域承載單次請求資料
- [Kubernetes — StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)：為何有狀態工作負載需要穩定身分與持久卷，對照 Deployment 的可互換 Pod

### Lambda：冷啟動、SnapStart、payload 與併發

- [Handling uniqueness with Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-uniqueness.html)：官方，快照複製唯一性內容的問題與 `beforeCheckpoint` / `afterRestore` hook
- [Understanding Lambda function scaling](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html)：官方，併發公式、RPS 上限 = 併發×10、擴縮速率 1,000/10s
- [AWS Lambda increases maximum payload size from 256 KB to 1 MB for asynchronous invocations](https://aws.amazon.com/about-aws/whats-new/2025/10/aws-lambda-payload-size-256-kb-1-mb-invocations/)：2025-10-24 公告
- [More room to build: serverless services now support payloads up to 1 MB](https://aws.amazon.com/blogs/compute/more-room-to-build-serverless-services-now-support-payloads-up-to-1-mb/)：AWS Compute Blog，含逐 64 KB 計費細節與上游服務各自上限
- [Coordinated Restore at Checkpoint (CRaC)](https://openjdk.org/projects/crac/)：SnapStart runtime hook 背後的開源專案

### K8s CronJob：schedule、concurrencyPolicy 與「不是 exactly-once」

- [Kubernetes 官方文件，CronJob](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)：含 `concurrencyPolicy`、`startingDeadlineSeconds`、100 次漏跑上限、`timeZone`、「非 exactly-once」聲明
- [Kubernetes 官方文件，Jobs](https://kubernetes.io/docs/concepts/workloads/controllers/job/)：CronJob 生出的 Job 的 `backoffLimit`、完成與重試語意
- [robfig/cron，Go cron 解析器](https://pkg.go.dev/github.com/robfig/cron/v3)：K8s CronJob `schedule` 欄位的解析來源，含 `@every`、巨集與欄位語意
- [`clock_gettime(2)` man page，`CLOCK_MONOTONIC` vs `CLOCK_REALTIME` 的語意差異](https://man7.org/linux/man-pages/man2/clock_gettime.2.html)
- [crontab(5) man page，cron 表達式格式](https://man7.org/linux/man-pages/man5/crontab.5.html)
- [IANA Time Zone Database](https://www.iana.org/time-zones)：`.spec.timeZone` 接受的時區名來源

### 失敗偵測：逾時是唯一手段、慢與死分不開

- [Chandra, Toueg, "Unreliable Failure Detectors for Reliable Distributed Systems", JACM 43(2):225-267, 1996](https://dl.acm.org/doi/10.1145/226643.226647)：completeness/accuracy 的分類，與「最終準確」偵測器如何讓非同步系統解出共識
- [Hayashibara, Defago, Yared, Katayama, "The φ Accrual Failure Detector", SRDS 2004](https://ieeexplore.ieee.org/document/1353004)：連續懷疑值 φ 的原始論文
- [Das, Gupta, Motivala, "SWIM: Scalable Weakly-consistent Infection-style Process Group Membership Protocol", DSN 2002](https://www.cs.cornell.edu/projects/Quicksilver/public_pdfs/SWIM.pdf)：ping / ping-req 代探與 suspicion 機制
- [Dadgar, Phillips, Currey, "Lifeguard: Local Health Awareness for More Accurate Failure Detection", 2017](https://arxiv.org/abs/1707.00788)：讓節點意識到「可能是我自己慢」而降誤判
- [AWS Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)：function 逾時上限 900 秒

### blue-green、canary 與 rolling

- [Kubernetes — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy)：官方，含 rolling update 的 strategy / maxSurge / maxUnavailable 語意
- [Kubernetes — Performing a Rolling Update](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)：官方互動教學
- [Martin Fowler — BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)
- [Martin Fowler — CanaryRelease](https://martinfowler.com/bliki/CanaryRelease.html)
- [Argo Rollouts — Progressive Delivery for Kubernetes](https://argoproj.github.io/rollouts/)：canary／blue-green 的 metric-driven 自動分析與回滾
- [AWS — Edit target group attributes](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html)：deregistration delay／connection draining，預設 300 秒

### Docker：容器隔離的原理

- [namespaces(7) — Linux manual page](https://man7.org/linux/man-pages/man7/namespaces.7.html)：八種 namespace 的權威總覽
- [cgroups(7) — Linux manual page](https://man7.org/linux/man-pages/man7/cgroups.7.html)
- [Control Group v2 — The Linux Kernel documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html)：cgroup v2 統一階層與 memory.max / OOM 行為
- [Open Container Initiative — Runtime Specification](https://github.com/opencontainers/runtime-spec)：OCI runtime spec，runc 遵循的標準
- [Docker — Seccomp security profiles](https://docs.docker.com/engine/security/seccomp/)：官方，含「預設封掉約 44 個 syscall」
- [Docker — Isolate containers with a user namespace](https://docs.docker.com/engine/security/userns-remap/)：容器 root 到 host UID 的映射
- [Docker — OverlayFS storage driver](https://docs.docker.com/engine/storage/drivers/overlayfs-driver/)：lowerdir / upperdir / copy-up / whiteout 的官方說明

### Kubernetes：Pod、Service、HPA 與調度

- [Kubernetes — Pods](https://kubernetes.io/docs/concepts/workloads/pods/)：官方概念，Pod 的生命週期與 ephemeral 本質
- [Kubernetes — Service](https://kubernetes.io/docs/concepts/services-networking/service/)：官方概念，ClusterIP 與虛擬 IP 機制
- [Kubernetes — EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)：官方，取代 Endpoints 的端點追蹤機制
- [Kubernetes — Virtual IPs and Service Proxies](https://kubernetes.io/docs/reference/networking/virtual-ips/)：官方，kube-proxy 的 iptables/IPVS/nftables 模式
- [Kubernetes — Horizontal Pod Autoscaling](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/)：官方，含 desiredReplicas 公式、tolerance、缺指標的保守處理
- [Kubernetes — Kubernetes Scheduler](https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/)：官方，filtering 與 scoring 兩階段
- [Kubernetes — Resource Management for Pods and Containers](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/)：官方，requests/limits 與 CPU throttle vs OOM

### IaC：宣告式、漂移與冪等 apply

- [Terraform — Manage resource drift](https://developer.hashicorp.com/terraform/tutorials/state/resource-drift)：官方教學，含 `-refresh-only` 與三方比對
- [Terraform — lifecycle meta-argument](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)：官方，`create_before_destroy` / `prevent_destroy` / `ignore_changes`
- [Terraform — S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)：官方，含 `use_lockfile` 原生鎖與 DynamoDB 鎖的棄用
- [OpenTofu — Announcing the fork of Terraform](https://opentofu.org/blog/opentofu-announces-fork-of-terraform/)：2023，授權分裂的緣由
- [Kubernetes — Server-Side Apply](https://kubernetes.io/docs/reference/using-api/server-side-apply/)：官方，`managedFields` 與欄位級衝突偵測
- [Kubernetes — Declarative Management of Kubernetes Objects](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/)：官方，宣告式 apply 的收斂語意

### 12-factor：哪些在容器/serverless 時代仍成立

- [The Twelve-Factor App](https://12factor.net/)：原始方法論，12factor.net
- [IX. Disposability — Maximize robustness with fast startup and graceful shutdown](https://12factor.net/disposability)：factor IX 原文
- [Twelve-Factor App Methodology is now Open Source](https://12factor.net/blog/open-source-announcement)：2024-11 開源公告
- [twelve-factor/twelve-factor](https://github.com/twelve-factor/twelve-factor)：GitHub 社群 repo，更新版在 `next` 分支開發中
- [Heroku Moved Twelve-Factor Apps to Open Source. What's Next?](https://thenewstack.io/heroku-moved-twelve-factor-apps-to-open-source-whats-next/)：The New Stack，更新方向的綜述
- [Kubernetes — Termination of Pods](https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/#pod-termination)：SIGTERM、寬限期與 graceful shutdown 的平台側機制

### config 與機密管理

- [The Twelve-Factor App — III. Config](https://12factor.net/config)：config 與程式碼分離的 litmus test
- [Kubernetes — Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)：官方，明載預設僅 base64、需另開 encryption at rest
- [Kubernetes — Encrypting Confidential Data at Rest](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)：EncryptionConfiguration 與 KMS provider
- [Kubernetes — Good practices for Kubernetes Secrets](https://kubernetes.io/docs/concepts/security/secrets-good-practices/)：RBAC、最小權限、外部機密整合
- [AWS Secrets Manager — Lambda rotation functions](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotate-secrets_lambda-functions.html)：createSecret/setSecret/testSecret/finishSecret 四步與 AWSCURRENT/AWSPENDING/AWSPREVIOUS 標籤
- [AWS Secrets Manager — Lambda function rotation strategies](https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotation-strategy.html)：單一使用者 vs 交替使用者，頻率砍半的原因
- [HashiCorp Vault — Lease, Renew, and Revoke](https://developer.hashicorp.com/vault/docs/concepts/lease)：動態機密的租約、TTL 與撤銷模型
- [OWASP — Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)：機密管理的整體實務基準

## Part 7 · 觀測與營運文化

### 三本柱：metric、log 與 trace

- [Tom Wilkie, "The RED Method: How to Instrument Your Services"](https://grafana.com/blog/the-red-method-how-to-instrument-your-services/)：Rate/Errors/Duration 的原始提法
- [OpenTelemetry — Observability Primer](https://opentelemetry.io/docs/concepts/observability-primer/)：三本柱與 observability 的基礎概念
- [OpenTelemetry — Signals](https://opentelemetry.io/docs/concepts/signals/)：traces / metrics / logs 的規格定位
- [Prometheus — Metric types](https://prometheus.io/docs/concepts/metric_types/)：counter / gauge / histogram / summary
- [Sigelman et al., "Dapper, a Large-Scale Distributed Systems Tracing Infrastructure", Google, 2010](https://research.google/pubs/pub36356/)：分散式追蹤的原典

### 從 log 算 metric 的陷阱：取樣、遺漏與視窗

- [Prometheus — Instrumentation best practices](https://prometheus.io/docs/practices/instrumentation/)：為什麼計數要用 counter 在源頭埋點，而非事後從 log 重建
- [Prometheus — Histograms and summaries](https://prometheus.io/docs/practices/histograms/)：分位數估計靠 bucket 線性插值，精度取決於 bucket 邊界
- [Fluent Bit — Backpressure](https://docs.fluentbit.io/manual/administration/backpressure)：`mem_buf_limit` 到頂時暫停輸入、filesystem buffering 的取捨
- [Fluent Bit — Buffering and storage](https://docs.fluentbit.io/manual/administration/buffering-and-storage)：`storage.total_limit_size` 滿時丟棄最舊 chunk
- [The Dataflow Model](https://research.google/pubs/pub43864/)：Akidau et al., VLDB 2015；event time vs processing time、watermark 與遲到資料的奠基論文

### cardinality 爆炸：一個 label 如何拖垮監控

- [Prometheus — Instrumentation best practices](https://prometheus.io/docs/practices/instrumentation/#do-not-overuse-labels)："do not overuse labels"，含 cardinality 盡量壓在 10 以下、過 100 重新設計的準則
- [Prometheus — Metric and label naming](https://prometheus.io/docs/practices/naming/)：label 基數警告
- [Prometheus — Configuration](https://prometheus.io/docs/prometheus/latest/configuration/configuration/)：`sample_limit`、`metric_relabel_configs` 的語意
- [Prometheus — Storage / TSDB](https://prometheus.io/docs/prometheus/latest/storage/)：head block、壓實與保留，理解記憶體為何錨定 active series
- [Prometheus — Native histograms](https://prometheus.io/docs/specs/native_histograms/)：用單一 series 表示分布、壓低 histogram 自帶的基數放大
- [OpenTelemetry — Metrics SDK](https://opentelemetry.io/docs/specs/otel/metrics/sdk/)：cardinality limit 預設 2000 與 `otel.metric.overflow` 合成資料點
- [OpenMetrics 1.0 specification](https://prometheus.io/docs/specs/om/open_metrics_spec/)：exemplars：把 metric bucket 連到 trace 的格式
- [Cloudflare — How Cloudflare runs Prometheus at scale](https://blog.cloudflare.com/how-cloudflare-runs-prometheus-at-scale/)：per-series 記憶體與 churn 的實戰量測

### SLI、SLO 與 error budget：p99 與 p999

- [Prometheus — `histogram_quantile()` 的精確語意](https://prometheus.io/docs/prometheus/latest/querying/functions/#histogram_quantile)：最高桶／+Inf 的回傳行為

### 告警設計：症狀 vs 原因、告警疲勞

- [Rob Ewaschuk, "My Philosophy on Alerting"](https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit)：症狀 vs 原因告警的原典，後成為 Google SRE 書監控章的骨幹
- [Prometheus — Alerting best practices](https://prometheus.io/docs/practices/alerting/)：對症狀告警、把原因留作診斷的實務指引
- [Grafana Labs — "How to implement multi-window, multi-burn-rate alerts"](https://grafana.com/blog/how-to-implement-multi-window-multi-burn-rate-alerts-with-grafana-cloud/)：落地一份多視窗燃燒率告警的工程細節

### 負載測試：開放與封閉模型、coordinated omission

- [Gil Tene, "How NOT to Measure Latency"](https://www.infoq.com/presentations/latency-response-time/)：QCon London 2013，coordinated omission 的原始論述與命名
- [wrk2 — A constant throughput, correct latency recording variant of wrk](https://github.com/giltene/wrk2)：README 詳述 CO 校正機制與 `--u_latency` 對照
- [HdrHistogram](https://github.com/HdrHistogram/HdrHistogram)：高動態範圍直方圖，`recordValueWithExpectedInterval` 的至記錄校正與 `copyCorrectedForCoordinatedOmission` 的事後校正
- [Grafana k6 — Open and closed models](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/open-vs-closed/)：開放／封閉模型的官方說明與圖解
- [Grafana k6 — Constant arrival rate executor](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/constant-arrival-rate/)：開放模型 executor 的設定與語意
- [Vegeta — HTTP load testing tool with a constant request rate model](https://github.com/tsenart/vegeta)

### 分散式追蹤：trace context 傳播、span 與取樣

- [W3C — Trace Context](https://www.w3.org/TR/trace-context/)：Recommendation，traceparent / tracestate 格式
- [W3C — Trace Context Level 2](https://www.w3.org/TR/trace-context-2/)：Candidate Recommendation Draft，random trace-id flag
- [Sigelman et al. — "Dapper, a Large-Scale Distributed Systems Tracing Infrastructure"](https://research.google/pubs/dapper-a-large-scale-distributed-systems-tracing-infrastructure/)：Google 2010，分散式追蹤原典
- [OpenTelemetry — Traces](https://opentelemetry.io/docs/concepts/signals/traces/)：span、context propagation 概念
- [OpenTelemetry — Sampling](https://opentelemetry.io/docs/concepts/sampling/)：head-based vs tail-based
- [OpenTelemetry Collector — Tail Sampling Processor](https://pkg.go.dev/github.com/open-telemetry/opentelemetry-collector-contrib/processor/tailsamplingprocessor)：尾部取樣的政策與架構約束

### 測試策略：unit、integration、contract、e2e

- [Martin Fowler, "The Practical Test Pyramid"](https://martinfowler.com/articles/practical-test-pyramid.html)：金字塔的權威闡述，含各層定義與比重
- [Kent C. Dodds, "The Testing Trophy and Testing Classifications"](https://kentcdodds.com/blog/the-testing-trophy-and-testing-classifications)：獎盃模型與 static/unit/integration/e2e 四分類
- [Martin Fowler, "ContractTest" / "Consumer-Driven Contracts"](https://martinfowler.com/bliki/ContractTest.html)：契約測試與 CDC 概念
- [Pact 官方文件](https://docs.pact.io/)：consumer-driven contract testing 的事實標準工具
- [Pact "Can I Deploy"](https://docs.pact.io/pact_broker/can_i_deploy)：matrix 與 can-i-deploy 的部署安全判定機制
- [PactFlow, "Bi-Directional Contract Testing"](https://pactflow.io/bi-directional-contract-testing/)：BDCT 與 CDC 的分工差異
- [Testcontainers 官方網站](https://testcontainers.com/)：用真實容器做 integration test

### 可觀測性與品質工具地圖

- [Fluent Bit vs Fluentd](https://docs.fluentbit.io/manual/about/fluentd-and-fluent-bit)：官方對比，含 input → parser → filter → output 管線與輕量 agent vs 中央聚合的分工
- [Clinic.js](https://github.com/clinicjs/node-clinic)：GitHub，README 含「不再積極維護、可能失準」的維護聲明
- [Node.js 官方 profiling 指南](https://nodejs.org/learn/getting-started/profiling)：內建 `--prof` / `--cpu-prof` / inspector
- [OpenTelemetry Profiles 進入 public Alpha](https://opentelemetry.io/blog/2026/profiles-alpha/)：2026，profiling 與 trace 關聯的開放標準方向
- [Grafana k6 官方文件](https://grafana.com/docs/k6/latest/)：scenarios / executors，開放與封閉模型
- [OSV-Scanner](https://github.com/google/osv-scanner)：Google 的開源相依漏洞掃描器，對照商業 SCA

### 事故應變與無咎事後檢討

- [John Allspaw, "Blameless PostMortems and a Just Culture", Etsy Code as Craft, 2012](https://www.etsy.com/codeascraft/blameless-postmortems)：把 Just Culture 落地到工程團隊的奠基之作
- [PagerDuty Incident Response Documentation](https://response.pagerduty.com/)：事故分級、Incident Commander 與各角色的公開實作指南
- [PagerDuty, "Severity Levels"](https://response.pagerduty.com/before/severity_levels/)：SEV1–SEV3 的具體判準範例
- [Wikipedia, "Incident Command System"](https://en.wikipedia.org/wiki/Incident_Command_System)：ICS 自加州野火發展為通用應變體系的歷史與角色結構

### DORA 四指標

- [DORA, "DORA's software delivery metrics"](https://dora.dev/guides/dora-metrics/)：四／五指標的官方定義與分組
- [DORA, "A history of DORA's software delivery metrics"](https://dora.dev/insights/dora-metrics-history/)：2023 更名、2024 加入第五指標與重新分組的官方時間線
- [Google Cloud, "Use Four Keys metrics to measure your DevOps performance"](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)：用工程資料自動計算四指標的做法
- [Marilyn Strathern, "'Improving ratings': audit in the British University system", *European Review* 5(3):305-321, 1997](https://doi.org/10.1002/(SICI)1234-981X(199707)5:3%3C305::AID-EURO184%3E3.0.CO;2-4)：Goodhart 定律最流傳的「當量測變成目標」表述出處

### 程式碼審查：審什麼、它在保護什麼

- [Sadowski, Söderberg, Church, Sipko, Bacchelli, "Modern Code Review: A Case Study at Google", ICSE-SEIP 2018](https://sback.it/publications/icse2018seip.pdf)：九百萬筆審查紀錄；審查的主要動機是教育與可維護性，缺陷偵測非主軸
- [SmartBear / Cisco, "Best Kept Secrets of Peer Code Review"](https://static1.smartbear.co/support/media/resources/cc/book/code-review-cisco-case-study.pdf)：2,500 次審查、320 萬行 code 的研究；200–400 行、<300–400 行/小時、60–90 分鐘的有效區間
- [Bacchelli, Bird, "Expectations, Outcomes, and Challenges of Modern Code Review", ICSE 2013](https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/)：審查的實際產出與期待落差；缺陷偵測之外的價值
- [Rigby, Bird, "Convergent Contemporary Software Peer Review Practices", FSE 2013](https://dl.acm.org/doi/10.1145/2491411.2491444)：跨多個開源與商業專案的審查實證，輕量審查為何收斂成主流

### 分支與發布策略：trunk-based vs git-flow

- [Trunk Based Development](https://trunkbaseddevelopment.com/)：Paul Hammant 等維護的權威站點，含 short-lived branch 與 feature flag 的完整實踐
- [Martin Fowler, "Patterns for Managing Source Code Branches"](https://martinfowler.com/articles/branching-patterns.html)：把分支模式攤成一條光譜、逐一分析整合頻率的取捨
- [Vincent Driessen, "A successful Git branching model"](https://nvie.com/posts/a-successful-git-branching-model/)：git-flow 原文，含作者 2020 年加註的持續交付適用邊界
- [Martin Fowler / Pete Hodgson, "Feature Toggles (aka Feature Flags)"](https://martinfowler.com/articles/feature-toggles.html)：feature flag 的分類、生命週期與技術債
- [DORA, "Capabilities: Trunk-based development"](https://dora.dev/capabilities/trunk-based-development/)：研究面的證據與「三條或更少活躍分支」的發現
- [DORA, "Capabilities: Continuous integration"](https://dora.dev/capabilities/continuous-integration/)：trunk-based 與 CI 為何須一起導入
