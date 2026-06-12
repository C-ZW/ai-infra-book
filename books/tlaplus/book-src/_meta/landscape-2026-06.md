---
baseline_date: 2026-06
verified_by: research-agent
---

# TLA+ / 形式化方法事實基準（2026-06）

本檔是全書的事實錨點。標記規則：

- ✅ ＝ 研究 agent 實際開頁（WebFetch / GitHub API / 論文 PDF 原文）驗證過，內容相符。
- ⚠️ ＝ 僅從搜尋結果摘要推斷、未開頁驗證；或來源互相矛盾（矛盾點會寫明）。

章節 agent 引用事實時：✅ 條目可直接寫進書；⚠️ 條目要嘛避開精確數字、要嘛在書中用模糊措辭（「約」「截至本書查證時點」）。

---

## 1. TLA+ 核心工具鏈現狀（2026-06 時點）

| 項目 | 現狀 | 來源 |
|---|---|---|
| TLA+ Foundation | 2023-04-21 由 Linux Foundation 宣布成立；創始會員 AWS、Oracle、Microsoft；官網 `https://foundation.tlapl.us/` | 成立日期與會員 ⚠️（多則新聞稿摘要一致，未開頁）；官網連結 ✅（Lamport 的 TLA+ 首頁明示「TLA+ is now in the hands of the TLA+ Foundation」並連到該站） |
| TLC / tla2tools 最新穩定版 | v1.7.4「The Xenophanes release」；v1.8.0「The Clarke release」長期掛 **pre-release**、由 CI 持續重新發布（GitHub API 顯示其 published_at 為 2026-05-26，即最近一次重發） | ✅ GitHub API（`https://api.github.com/repos/tlaplus/tlaplus/releases`）。**注意**：v1.7.4 的發布年份兩次抓取不一致（2023-08-05 vs 2024-08-05）⚠️，書中勿寫精確日期，寫「v1.7.4 為最新穩定版」即可 |
| Toolbox vs VSCode | TLA+ Toolbox（Eclipse 桌面 IDE）已進入維護模式；官方開發重心與社群主流是 **VSCode extension**（`alygin.vscode-tlaplus`），社群有 Toolbox→VSCode 遷移指南討論串 | ⚠️（未開頁，但 Google Groups 遷移討論串、VSCode Marketplace、Informal Systems 教學三個獨立來源的摘要一致） |
| TLAPS（TLA+ Proof System） | 由 proof manager `tlapm` 加後端 prover 組成；後端：SMT solvers（預設 Z3，亦支援 CVC4/CVC5、veriT）、Zenon（tableau 一階邏輯）、Isabelle/TLA+（客製 object logic）、LS4（命題時序邏輯）；預設依序嘗試 SMT(5s)→Zenon(10s)→Isa(30s)。repo 已移至 `https://github.com/tlaplus/tlapm`，最新為 1.6.0 rolling pre-release | 後端清單與順序 ⚠️（搜尋摘要引自官方文件，多來源一致）；版本號 ⚠️（未開頁）。書中可放心寫後端組成，避免寫死版本號 |
| Apalache | TLA+（與 Quint）的符號模型檢查器，將 TLA+ 轉成 SMT（Z3、CVC5）做 bounded model checking。**現為獨立維護**：repo 在 `https://github.com/apalache-mc/apalache`，維護者 Igor Konnov、Jure Kukovec、Thomas Pani；README 明言「Apalache is not funded by any organization」。最新 release v0.58.0（2026-05-29），維護活躍 | ✅（開頁驗證 README 與 release）。**注意**：網路上大量舊資料仍寫「由 Informal Systems 維護」，已過時，勿沿用 |
| PlusCal | 寫在 `.tla` 檔註解區塊內的演算法語言，經 translator 轉成 TLA+；有兩種等價語法：**P-syntax**（類 Pascal，`begin…end`）與 **C-syntax**（大括號）。Lamport 的 PlusCal 手冊兩種都涵蓋 | 兩種語法的存在為穩定事實（Lamport PlusCal 頁 `https://lamport.azurewebsites.net/tla/pluscal.html` ⚠️ 未開頁）。哪本教材用哪種語法未逐一查證，書中勿斷言 |

---

## 2. 周邊形式化方法生態（一句話定位）

| 工具 | 定位與現狀 | 來源 |
|---|---|---|
| Quint | Informal Systems 開發的現代規格語言，定位是「給工程師的 TLA+ 替代語法」，可由 Apalache 做後端檢查（Apalache README 同時列 TLA+ 與 Quint）| Apalache 支援 Quint ✅；Quint 本身現狀 ⚠️（未開頁） |
| Alloy 6 | 關聯邏輯（relational logic）規格語言＋Alloy Analyzer；第 6 版合併了 Electrum 的時序運算子 | ⚠️（常識性事實，未查證；書中提及時勿寫發布日期） |
| P language | 通訊狀態機（communicating state machines）建模語言，源自 Microsoft；2019 年起在 AWS 內部開發、為策略性開源專案（詳見第 4 節 AWS 後續） | 2019 起在 AWS 開發 ⚠️（CACM 2025 文章摘要） |
| Lean 4 | 定理證明器＋程式語言，Lean FRO 維護，數學形式化社群（Mathlib）為最大用戶 | ⚠️（常識性，未查證細節） |
| Rocq（Coq 改名） | Coq 已改名 **The Rocq Prover**：改名意向公布於 2023 年（搜尋摘要稱 2023-10-11 ⚠️），改名隨 **Rocq 9.0（2025-03-12 發布）** 完成；標準函式庫 namespace 由 `Coq` 改為 `Stdlib`；官網 `https://rocq-prover.org/` | 9.0 發布日期 ⚠️（rocq-prover.org changelog 連結在搜尋結果中明示日期，未開頁但來源即官網）；書中寫「2025 年 3 月隨 9.0 完成改名」安全 |
| Isabelle/HOL | 老牌互動式定理證明器，持續年度發布；TLAPS 以 Isabelle/TLA+ 為其中一個後端 | TLAPS 後端關係見第 1 節；其餘 ⚠️ |
| Event-B | refinement 為核心的形式方法，配套 Rodin 平台 | ⚠️（常識性，未查證近況） |

---

## 3. 教材與社群

| 項目 | 事實 | 來源 |
|---|---|---|
| Specifying Systems（Lamport, Addison-Wesley 2002） | 官方頁面提供免費 PDF 下載；頁面 `https://lamport.azurewebsites.net/tla/book.html` ✅；PDF 檔名 `book-21-07-04.pdf`（2021-07-04 版本），完整 URL 推斷為 `https://lamport.azurewebsites.net/tla/book-21-07-04.pdf` ⚠️（頁面開過、PDF 本身未抓） | 頁面 ✅ |
| learntla.com | Hillel Wayne 的免費線上 TLA+ 教材；三大部：The Core（線性入門）、Topics（進階獨立課題）、Examples；仍持續維護（有 What's New 頁與 roadmap）；作者自述為 TLA+ Foundation 成員、《Practical TLA+》作者 | ✅（開頁驗證） |
| Practical TLA+（Hillel Wayne） | Apress 出版，2018；learntla.com 頁面證實作者身分 | 作者 ✅；出版社/年份 ⚠️（常識性，未另查） |
| TLA+ Video Course | Lamport 親自錄製，`https://lamport.azurewebsites.net/video/videos.html`；**10 講**（部分分上下集，共 13 段影片）；課程開場自述「These videos are not light entertainment. They require careful viewing and actual thinking.」 | ✅（開頁驗證） |
| Lamport 的 TLA+ Home Page | `https://lamport.azurewebsites.net/tla/tla.html`；頁面明示官方資源已移交 TLA+ Foundation、此頁為其個人網站；頁面 2025-10-13 仍有更新（last modified） | ✅（開頁驗證） |
| Leslie Lamport 近況 | 2013 年 ACM Turing Award 得主（2014 年公布）⚠️ 常識性；個人網站 2025-10 仍在更新 ✅；**是否仍任職 Microsoft Research 未查證** ⚠️——書中寫「長年任職 Microsoft Research」即可，勿寫「現任」 | 混合 |
| TLA+ Community Event | 最近一次：**2026-04-12 於義大利 Torino**，與 ETAPS 2026 共同舉辦（官網 `https://conf.tlapl.us/2026-etaps/` ✅）。2025 年場次亦掛在 ETAPS 下（`/2025-etaps/` 路徑存在 ✅，地點未查 ⚠️） | ✅ / ⚠️ |

---

## 4. 業界案例（案例研究章的事實底）

### 4.1 AWS：CACM 2015 論文（已逐字核對 PDF 原文 ✅）

- 論文：**“How Amazon Web Services Uses Formal Methods”**, *Communications of the ACM*, Vol. 58 No. 4（2015 年 4 月）, DOI `10.1145/2699417`。
- 作者（原文順序）：Chris Newcombe, Tim Rath, Fan Zhang, Bogdan Munteanu, Marc Brooker, Michael Deardeuff。✅
- 開頭句（原文）：“SINCE 2011, ENGINEERS at Amazon Web Services (AWS) have used formal specification and model checking to help solve difficult design problems in critical systems.” ✅ → AWS 使用 TLA+ 起點是 **2011**。
- 前身：2014 年技術報告 “Use of Formal Methods at Amazon Web Services”，Lamport 網站存有 PDF（`https://lamport.azurewebsites.net/tla/formal-methods-amazon.pdf` ⚠️ 未開頁）。

**Table 1（“Applying TLA+ to some of Amazon's more complex systems”，行數不含註解）— 全表已對 PDF 原文核對 ✅：**

| 系統 | 元件 | 規格行數／語言 | 成果（論文原文意旨） |
|---|---|---|---|
| S3 | Fault-tolerant, low-level network algorithm | 804 行 PlusCal | Found two bugs, then others in proposed optimizations |
| S3 | Background redistribution of data | 645 行 PlusCal | Found one bug, then another in the first proposed fix |
| DynamoDB | Replication and group-membership system | 939 行 TLA+ | Found three bugs requiring traces of up to 35 steps |
| EBS | Volume management | 102 行 PlusCal | Found three bugs |
| Internal distributed lock manager | Lock-free data structure | 223 行 PlusCal | Improved confidence though failed to find a liveness bug, as liveness not checked |
| Internal distributed lock manager | Fault-tolerant replication-and-reconfiguration algorithm | 318 行 TLA+ | Found one bug and verified an aggressive optimization |

**防張冠李戴對照（章節 agent 必讀）：**

- 「35 步 bug」屬於 **DynamoDB**（replication and group-membership system），不是 S3。原文：“shortest error trace exhibiting the bug included 35 high-level steps. The improbability of such compound events is not a defense against such bugs; historically, AWS engineers have observed many combinations of events at least as complicated as those that could trigger this bug. The bug had passed unnoticed through extensive design reviews, code reviews, and testing…” ✅（T.R.＝Tim Rath，DynamoDB）
- 「804 行 PlusCal」屬於 **S3** 的容錯低階網路演算法。原文背景：S3 團隊原本「had been considering writing a Java program to brute-force explore possible executions: essentially a hard-wired form of model checking. They were able to avoid the effort by using TLA+ instead.」作者 F.Z.（Fan Zhang）兩週內寫了兩版 spec，且「she was more productive in PlusCal than TLA+」。✅
- 採用規模（原文）：“At the time of this writing, seven Amazon teams have used TLA+, all finding value in doing so… Executive management actively encourages teams to write TLA+ specs for new features and other significant design changes. In annual planning, managers now allocate engineering time to TLA+.” ✅ →「七個團隊」是 **2015 年論文時點**的數字，書中必須綁定時點。
- 學習曲線（原文意旨）：從新人到 principal 等級的工程師都能從零學 TLA+，「get useful results in two to three weeks」。✅

### 4.2 AWS 後續（2015 之後）

| 事實 | 細節 | 來源 |
|---|---|---|
| 續篇論文 | **“Systems Correctness Practices at Amazon Web Services”**，CACM Vol. 68 No. 6（2025-06）；另有 ACM Queue 版（Vol. 22 No. 6，2025 年初）。總覽 AWS 正式與半正式方法組合：TLA+、P、property-based testing、fuzzing、runtime monitoring 等 | ⚠️（搜尋摘要，未開頁；cacm.acm.org 對抓取回 403）。URL：`https://cacm.acm.org/practice/systems-correctness-practices-at-amazon-web-services/`、`https://queue.acm.org/detail.cfm?id=3712057` |
| P language | 2019 年起在 AWS 內部開發、維持為策略性開源專案；用「communicating state machines」建模，貼近微服務工程師的心智模型；**著名應用：S3 從 eventual 遷移到 strong read-after-write consistency 的設計驗證** | ⚠️（CACM 2025 摘要，多來源一致） |
| ShardStore（S3 儲存節點） | 論文 **“Using Lightweight Formal Methods to Validate a Key-Value Storage Node in Amazon S3”**（SOSP 2021）。**注意：ShardStore 用的是輕量級形式化方法（Rust 參考模型＋property-based testing），不是 P、也不是 TLA+**——這是最容易張冠李戴的點 | 論文存在與標題 ⚠️（dl.acm.org 連結出現於多個獨立搜尋結果）；DOI 頁 `https://dl.acm.org/doi/10.1145/3477132.3483540` |
| Kani | AWS 用 Rust 驗證工具 Kani 驗證 Firecracker 的安全邊界 | ⚠️（CACM 2025 摘要） |
| TLA+ 是否仍在用 | AWS 為 TLA+ Foundation 創始會員（2023）⚠️；CACM 2025 文章仍將 TLA+ 列入現行工具組合 ⚠️。書中可寫「TLA+ 仍是 AWS 工具箱一員，但 2019 後新增了 P 等更貼近工程師的工具」 | ⚠️ |

### 4.3 Microsoft Azure Cosmos DB

- 官方 spec repo：`https://github.com/Azure/azure-cosmos-tla` ✅（開頁驗證；另有 `tlaplus/azure-cosmos-tla` 鏡像 ⚠️）。內容：五種一致性等級（strong、bounded staleness、session、consistent prefix、eventual）的 TLA+ 規格＋三個由簡到繁的情境模型。✅
- **Lamport 參與的正確說法**：README 連到一段 **Lamport 受訪影片**，談 TLA+ 在 Cosmos DB 的應用；Cosmos DB 團隊自述「heavily relies on TLA+」。✅（README 開頁驗證）。**Lamport 不是 Cosmos DB 的設計者**——書中只能寫「Lamport 曾與 Cosmos DB 團隊合作／受訪談其 TLA+ 應用」，不能寫成他設計了協定。
- 反面教材（可增加章節深度）：Finn Hackett 等人 **“Understanding Inconsistency in Azure Cosmos DB with TLA+”**（ICSE-SEIP 2023；arXiv `2210.13661`）指出官方 spec 與實際行為存在落差。⚠️（搜尋摘要，未開頁；引用前建議再核對）

### 4.4 MongoDB

- 論文：**“eXtreme Modelling in Practice”**，A. Jesse Jiryu Davis、Max Hirschhorn、Judah Schvimer，*PVLDB* Vol. 13 No. 9（2020）。PDF：`http://vldb.org/pvldb/vol13/p1346-davis.pdf`；DOI 頁：`https://dl.acm.org/doi/10.14778/3397230.3397233`。⚠️（未開頁，但 dl.acm.org 與 vldb.org 兩來源一致）
- 內容：兩個案例——(1) MongoDB Server **replication protocol** 的 model-based trace-checking（MBTC，比對 TLA+ spec 與 C++ 實作的執行軌跡）；(2) MongoDB Realm Sync operational transformation 演算法的 model-based test-case generation（MBTCG）。⚠️
- 配套部落格（第一手作者）：emptysqua.re 的 “Two attempts to compare a TLA+ spec with a C++ implementation” 與 MongoDB 官方 “Conformance Checking at MongoDB”。⚠️
- 論文重要結論方向（書中引用前請開原文核對 ⚠️）：spec-implementation conformance 檢查成本高，兩案例結果一成一敗（trace-checking 一側遇到顯著困難）。

### 4.5 CockroachDB

- 部落格：**“Parallel Commits: An atomic commit protocol for globally distributed transactions”**，Nathan VanBenschoten，2019-11-07，`https://www.cockroachlabs.com/blog/parallel-commits/`。✅（開頁驗證）
- TLA+ 驗證了兩個性質：**AckImpliesCommit**（safety：coordinator 一旦向 client 回報 commit 成功，交易必已 committed）與 **ImplicitCommitLeadsToExplicitCommit**（liveness：進入 implicit commit 狀態的交易終將進入 explicit commit，即使 coordinator 故障）。spec 檔 `ParallelCommits.tla` 在 CockroachDB GitHub repo。✅
- 背景：該 spec 是在請 Hillel Wayne 帶的內部 workshop 中發展出來的。✅

### 4.6 未能確認、書中不可列的案例

Intel、Elasticsearch、Confluent 等傳聞案例**未在本次預算內以兩個獨立來源確認**，依規格不列入。章節 agent 不得在書中引用這些名字作為 TLA+ 案例，除非另行查證。

---

## 5. 經典 spec 原文位置（逐一驗證 ✅）

GitHub `tlaplus/Examples` repo：活躍維護（有 CI「Validate Specs & Models」工作流程），結構為 `specifications/<名稱>/`，每目錄含 `manifest.json`。✅（開頁驗證）

以下檔案路徑全部經 GitHub API 直接列目錄確認存在（master branch）✅：

| Spec | URL |
|---|---|
| DieHard.tla（含 DieHarder.tla 推廣版與 DieHard_proof.tla） | `https://github.com/tlaplus/Examples/blob/master/specifications/DieHard/DieHard.tla` |
| TCommit.tla（Lamport，transaction commit） | `https://github.com/tlaplus/Examples/blob/master/specifications/transaction_commit/TCommit.tla` |
| TwoPhase.tla（Lamport，two-phase commit；同目錄另有 PaxosCommit.tla） | `https://github.com/tlaplus/Examples/blob/master/specifications/transaction_commit/TwoPhase.tla` |
| Paxos.tla（Lamport 原版；同目錄含階層：Consensus.tla → Voting.tla → Paxos.tla） | `https://github.com/tlaplus/Examples/blob/master/specifications/Paxos/Paxos.tla` |
| raft.tla（Diego Ongaro 本人 repo；CC-BY 4.0；自述比博士論文版略有更新；要跑 TLC 建議參考 PR #4 的修改） | `https://github.com/ongardie/raft.tla` ✅（開頁驗證） |

Lamport 自有頁面：

- TLA+ Home Page（個人版）：`https://lamport.azurewebsites.net/tla/tla.html` ✅
- Specifying Systems 書頁（免費 PDF）：`https://lamport.azurewebsites.net/tla/book.html` ✅
- 官方（基金會）入口：`https://foundation.tlapl.us/` ✅（連結經 Lamport 首頁證實）

---

## 6. AI × 形式化方法（2025–2026 動態；全節為快照，書中僅末章淺談）

| 動態 | 時點 | 細節 | 來源 |
|---|---|------|---|
| LLM 生成 TLA+ spec 的能力評測 | 2025-09 起 | **SysMoBench**：評測 AI 對真實複雜系統做形式建模（arXiv `2509.23130`）。另有一篇 2026-03 投稿的評測：30 個 LLM、205 個 TLA+ spec，**最佳語意正確率僅 8.6%**，且模型規模與品質無關 | ⚠️（搜尋摘要；8.6% 這個數字引用前必須開原文核對出處論文名） |
| 真實系統建模實測 | 2026-05 | ACM SIGOPS 部落格 “Can LLMs model real-world systems in TLA+?”（Specula 團隊）：Claude 生成的 Etcd Raft TLA+ spec 能過語法檢查、能跑 TLC，但深層語意驗證仍是缺口 | ⚠️（`https://www.sigops.org/2026/can-llms-model-real-world-systems-in-tla/`，未開頁） |
| LLM 輔助證明 | 2025-12 | “Towards Language Model Guided TLA+ Proof Automation”（arXiv `2512.09758`）：LLM 引導證明義務的階層分解，驗證仍交給符號 prover | ⚠️ |
| 整體格局 | 2026-06 時點 | 共識方向：LLM 在「函式層級規格、pre/post-condition 生成」有進展；**完整系統級 spec 合成仍是開放問題**；「LLM 起草、符號工具把關」是主流架構 | ⚠️（綜合多來源，屬研究快照而非定論） |

**寫作提醒**：本節所有數字與結論都帶強時效性，書中引用一律加「截至 2026 年中」之類的時點限定詞。

---

## 維護備註

- 本檔由研究 agent 於 2026-06-11 產出；網路查詢約 26 次（WebSearch/WebFetch）＋GitHub API／論文 PDF 本機解析。
- 最可信的三塊（已開原始來源逐字核對）：AWS CACM 2015 全表與引文、`tlaplus/Examples` 各 spec 路徑、CockroachDB 部落格。
- 最需要後續補驗的三塊：CACM 2025 AWS 續篇（官網 403，僅摘要）、MongoDB 論文內文結論、AI×FM 節的所有數字。
