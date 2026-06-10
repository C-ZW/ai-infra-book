# CHEN, CHE-WEI (Chewei Chen)

**Senior Backend Engineer**

New Taipei City, Taiwan
Email: a19575091@gmail.com | GitHub: github.com/C-ZW | LinkedIn: linkedin.com/in/che-wei-chen-39a068164

---

## Professional Summary

Senior Backend Engineer with **6+ years** specializing in **greenfield system design** and **high-concurrency performance engineering**. At NeoBards (Dynasty Warriors Mobile, **500K+ users, 10K+ CCU**), delivered a **40% reduction in peak RDS CPU** through profiling-driven optimization and architected event-driven systems for in-game competitions. Currently at Bahwan CyberTek, introduced NestJS and team conventions while designing a multi-tier cache library adopted across projects. Looking for opportunities with **broader ownership of architecture and team direction**.

---

## Technical Skills

- **Languages & Frameworks:** TypeScript, Node.js (NestJS, Express)
- **API & Auth:** RESTful design, OpenAPI/Swagger, versioning, JWT, OAuth 2.0 (token lifecycle), RBAC
- **Databases & Caching:** MySQL, PostgreSQL (read replicas, partitioning, isolation levels, deadlock detection, index tuning), Redis (Pub/Sub), Prisma ORM
- **Real-Time Communication:** WebSocket, Socket.io, WebRTC (Jitsi, TURN/STUN)
- **Cloud & Infrastructure:** AWS (EKS, ECS, Lambda, SQS, SNS, RDS, S3, CloudFormation, ALB, API Gateway), KrakenD, Docker, Kubernetes (CronJobs), Bull
- **Performance & Observability:** Clinic.js, FluentBit (Lua), AWS CloudWatch (Metrics, Log Insights, Metric Filters), k6, Vegeta
- **Testing & Quality:** Jest (TDD), CI/CD, Snyk

---

## Work Experience

### Software Engineer | Bahwan CyberTek
*September 2024 – Present*

*Flat engineering structure; operating at Senior-level scope — introduced NestJS framework and established team development conventions.*

*A global digital transformation leader specializing in IP-based solutions for 1,000+ enterprise clients across oil & gas, telecom, and banking sectors.*

- **Led 3 greenfield projects** building B2B/B2C data integration middleware on AWS ECS (TypeScript, NestJS) for a global bicycle manufacturer, centralizing data flows between PostgreSQL and MySQL across multi-region distributors.
- Designed a **lightweight decorator framework** that brought the most valuable NestJS ergonomics (class-validator DTO binding, declarative parameter injection, centralized exception mapping) to raw AWS Lambda — **deliberately avoiding full NestJS to keep the learning curve low** for a team where few had Nest experience. Reused the DTOs to auto-generate OpenAPI specs via a **CI pipeline that fails builds on undocumented API changes**, keeping validation and docs in sync. **Now used across 30–50 handlers and the default for all new functions.**
- Designed and documented a **multi-tier cache library** with pluggable data sources (in-memory → S3 → local) and **graceful degradation** across layers, plus a schema validation utility built on top of it. Authored integration guides for team-wide adoption.
- Established a shared internal library **now used by all ~10 team projects**, standardizing common patterns and reducing boilerplate.

### Senior Backend Engineer | NeoBards Entertainment
*April 2022 – September 2024*

*Contracted via Keyteo through March 2024; rejoined as direct hire June – September 2024.*

*A premier AAA game development studio recognized for collaborating with Capcom, Square Enix, and Koei Tecmo on high-profile global titles.*

- Scaled and maintained backend services for Dynasty Warriors Mobile, ensuring high availability for **500K+ users and 10K+ CCU**.
- Authored load testing scenarios on client-managed infrastructure; used **Clinic.js** to diagnose memory leaks and CPU bottlenecks, translating findings into concrete optimization actions.
- **Reduced RDS CPU by 40% during peak traffic** via profiling-driven database optimization: restructured SQL ordering and decomposed transactions to minimize lock contention, reordered cross-transaction execution to reduce hotspots, and batched row-by-row updates.
- Architected an **event-driven settlement pipeline** (Kubernetes CronJobs → SQS → idempotent consumers) processing **100K–300K reward distributions across ~5,000 guilds per season**, with eventual consistency across guild, player, inventory, and mail services.
- Built a custom **observability pipeline** (FluentBit + Lua scripts) to extract, transform, and aggregate API response metrics from production logs, shipping structured data to S3 for response-time visibility used by the game's publisher, **Nexon**.

### Backend Engineer | LetsTalk Technology
*June 2019 – March 2022*

*A software firm dedicated to building Letstalk, a highly secure and privacy-focused instant messaging ecosystem for global markets.*

- **Independently proposed and built** a real-time notification system (WebSocket + Redis Pub/Sub) for message fan-out and multi-device synchronization, serving **500K+ registered users with ~3,200 concurrent connections and ~10M messages/month**. Addressed an infrastructure gap for users in markets where **Google services (FCM) were unavailable, notably China**.
- Integrated voice and video calling capabilities into the IM platform — evaluated commercial WebRTC SDKs (Twilio, Agora) and **selected Jitsi on cost grounds** for group calls. Built Socket.io-based signaling and configured TURN/STUN servers for NAT traversal.
- Rebuilt the scheduled messaging feature from a setTimeout-based implementation (**so unstable it was capped at 15-minute delays** as a workaround) to a **cron-driven job queue**, enabling arbitrary-duration scheduling and ensuring messages survive service restarts.

---

## Education

**National Chengchi University (NCCU)**
Graduate Institute of Computer Science — Selected Coursework (Advanced Algorithms, Machine Learning)

**Tamkang University, 2017**
Bachelor of Science in Computer Science and Information Engineering
