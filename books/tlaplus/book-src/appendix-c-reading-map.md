# 附錄 C — 延伸閱讀總地圖

> **本附錄是什麼**：ch01–ch18 各章「延伸閱讀」的全部條目，去重後按類別重排，再加上事實基準（2026-06 landscape）已驗證的少數生態入口。收錄規則：**只收各章已列出、或 landscape 已驗證的資源**，本附錄不新增任何未經查證的連結；原章與 landscape 的驗證註記（「2026-06 開頁核對」「未逐字核對」「未開原文」等）一律保留。每條格式：名稱—連結—一句話（沿用原章的推薦語）—出現章。

## C.1 書

- **Specifying Systems**（Leslie Lamport，Addison-Wesley，2002）：`https://lamport.azurewebsites.net/tla/book.html`（官方頁免費 PDF；頁面驗證於 2026-06）— 全書的最終參考書，讀原文最大的收穫是 Lamport 對每個設計決定的辯護。各章指路：第 1 章〈A Little Simple Math〉複習本書 ch03–04 的全部數學；第 2 章是時鐘例子（HourClock）的原始出處；第一部分（第 1–7 章，約 83 頁）是本書整個 Part III 的原典；第 8 章〈Liveness and Fairness〉是 WF/SF 的教科書版；第 14 章〈The TLC Model Checker〉是 TLC 的官方原典；第 4 章是 INSTANCE／substitution 的官方語意。（出現章：ch01、ch02、ch03、ch04、ch06、ch07、ch08、ch09、ch15）
- **Practical TLA+**（Hillel Wayne，Apress，2018）：未附連結（landscape 經 learntla.com 證實作者身分；出版社與年份為常識性事實、未另行查證）— learntla 作者的紙本入門書，走「動手跑工具」路線，與本書的紙上推演路線互補。（出現章：無，僅 landscape §3）
- **A Science of Concurrent Programs**（Leslie Lamport，Cambridge University Press，2026）：`https://lamport.azurewebsites.net/tla/science-book.html`（官網提供免費 PDF；2026-06 開頁核對）— Lamport 晚期的集大成之作；歸納不變量與 refinement 在完整理論裡的位置都在這裡，建議讀完 ch15、ch16 再回來啃。（出現章：ch14）
- **The Art of Multiprocessor Programming**（M. Herlihy & N. Shavit）：未附連結 — 第 2 章系統性地講互斥：Peterson、filter lock（n-process 推廣）、Lamport bakery，以及這些演算法在真實硬體（弱記憶體模型、cache）上的命運；本書「每步原子」假設之外的世界，從這裡開始。（出現章：ch10）
- **Software Abstractions**（Daniel Jackson）：未附連結（書本身未另行查證版次）— Alloy 思維的原典；線上入口見 C.6 的 Alloy 官網。（出現章：ch18）
- **Book of Proof 第 3 版**（Richard Hammack）：`https://richardhammack.github.io/BookOfProof/`（官方免費 PDF）— 第 2 章〈Logic〉用最少的形式機械把真值表、量詞、否定推移講完，習題量大；想把 ch03 練成厚實的肌肉，做它的習題最划算。（出現章：ch03）
- **Mathematics for Computer Science**（Lehman、Leighton 與 Meyer）：`https://people.csail.mit.edu/meyer/mcs.pdf`（MIT 開放教材，免費 PDF）—〈Logical Formulas〉一章從數位電路與程式驗證的動機講命題與謂詞邏輯，工程味最重的一本；讀 ch05 歸納法時它也是好補充。（出現章：ch03）

## C.2 論文

### 理論奠基

- **Dijkstra，“On the reliability of programs”（EWD303）**：`https://www.cs.utexas.edu/~EWD/transcriptions/EWD03xx/EWD303.html`（UT Austin 檔案館轉錄）— 「測試只能證明 bug 存在」名言的原始脈絡——他不是在罵測試，是在論證「正確性需要不同種類的論證」。（出現章：ch01）
- **Lamport，“Computation and State Machines”（2008）**：`https://lamport.azurewebsites.net/pubs/state-machine.pdf` — Lamport 親自論證「計算就該用狀態機描述、而描述狀態機用數學就夠了」的立場文，本書世界觀的源頭；讀前半部就值回票價。（連結驗證於 2026-06）（出現章：ch02）
- **Lamport，“The Temporal Logic of Actions”（ACM TOPLAS 1994）**：`https://lamport.azurewebsites.net/pubs/pubs.html#lamport-actions` — TLA 的原始論文；想看「為什麼把 action 放進邏輯、stuttering 為何不可妥協」的第一手論證，讀前兩節就值回票價。（出現章：ch06）
- **Alpern & Schneider，“Defining Liveness”（*Information Processing Letters* 21(4)，1985）**：未附連結（期刊原文在付費牆內）— liveness 正式定義與「任何性質＝safety ∧ liveness」分解定理的原始出處；正文不到五頁，拓撲味比本書直覺版重，先讀 Lamport 的 safety-liveness 講義轉述也夠用（見 C.4）。（出現章：ch07）
- **Lamport，“How to Write a 21st Century Proof”（2011）**：`https://lamport.azurewebsites.net/pubs/proof.pdf` — 層級證明格式的原典；本書的 ⟨1⟩⟨2⟩ 編號就是它的手寫版，ch16 的 TLAPS 是它的機器版。讀前半即可。（出現章：ch05）
- **Lamport，“Teaching Concurrency”（2009）**：`https://lamport.azurewebsites.net/pubs/teaching-concurrency.pdf` — 兩頁的小論文：不變量是理解併發系統的鑰匙，而多數工程師沒被教過這樣思考；文末的小演算法是練 ch14 強化迴圈最便宜的啞鈴。（出現章：ch05、ch14）
- **Yu、Manolios、Lamport，“Model Checking TLA+ Specifications”（CHARME 1999）**：`https://lamport.azurewebsites.net/pubs/yuanyu-model-checking.pdf` — TLC 的出生論文：為什麼要為無型別的集合論語言做顯式狀態檢查器、fingerprint 的設計取捨。（連結定位於 2026-06，內文意旨經摘要核對）（出現章：ch09）
- **Fischer、Lynch、Paterson，“Impossibility of Distributed Consensus with One Faulty Process”（*JACM* 32(2)，1985）**：`https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf`（2026-06 可得）— FLP 本尊；本書不證，讀第 1 節與主定理的敘述，把每個限定詞讀準就值回票價。（出現章：ch12）
- **Abadi & Lamport，“The Existence of Refinement Mappings”（*TCS* 82(2)，1991；會議版 LICS 1988）**：`https://lamport.azurewebsites.net/pubs/pubs.html#abadi-existence` — refinement mapping 與 prophecy variable 的出生地；讀引言與 §1–2，看「mapping 何時存在」的三個條件怎麼陳述。（2026-06 查證）（出現章：ch15）
- **Lamport & Merz，“Auxiliary Variables in TLA+”（2017）**：`https://lamport.azurewebsites.net/pubs/auxiliary.pdf`（arXiv:1703.05121）— history／prophecy／stuttering 三種輔助變數在 TLA+ 裡的具體加法規則——ch15 概念層的施工手冊。（2026-06 查證）（出現章：ch15）
- **Cousineau、Doligez、Lamport、Merz 等，“TLA+ Proofs”（FM 2012）**：`https://lamport.azurewebsites.net/pubs/tlaps.pdf` — TLAPS 證明語言的設計論文：為什麼是層級、為什麼宣告式、義務怎麼生成。讀 §2–3 就夠。（2026-06 連結可達）（出現章：ch16）

### 協議原典

- **Dijkstra，“Solution of a Problem in Concurrent Programming Control”（*CACM* 8(9)，1965）**：`https://cacm.acm.org/research/solution-of-a-problem-in-concurrent-programming-control/` — 互斥問題的開山之作，一頁紙，n 個 process。（出現章：ch10）
- **Peterson，“Myths About the Mutual Exclusion Problem”（*Information Processing Letters* 12(3)，1981）**：未附連結 — 原始論文，兩頁；看一個傳世演算法可以多短，也看 1981 年的正確性論證跟你在 ch10 做的手推差在哪。（出現章：ch10）
- **Gray & Lamport，“Consensus on Transaction Commit”（*ACM TODS* 31(1)，2006）**：`https://dl.acm.org/doi/10.1145/1132863.1132867`（Microsoft Research 頁面有 PDF）— TCommit 與 TwoPhase 兩份 spec 的論文出處；讀第 3–4 節看 2PC 如何被定位成 Paxos Commit 的 F = 0 特例。（出現章：ch11）
- **Skeen，“Nonblocking Commit Protocols”（ACM SIGMOD 1981）**：`https://dl.acm.org/doi/10.1145/582318.582339` — 3PC 的原典，給出非阻塞承諾協議的充要條件——讀它是為了看清那些條件在 partition 下如何失效。（出現章：ch11）
- **Lamport，“Paxos Made Simple”（2001）**：`https://lamport.azurewebsites.net/pubs/paxos-simple.pdf`（2026-06 驗證可下載）— ch12 的 P1／P2／P2c 引文與 phase 1/2 推導全部出自 §2.2，十四頁讀完整個不變量鏈。（出現章：ch12）
- **Lamport，“The Part-Time Parliament”（*ACM TOCS* 1998）**：`https://lamport.azurewebsites.net/pubs/pubs.html#lamport-paxos`（Lamport 出版品頁錨點）— 寓言包裝的原始論文，當文化史讀——「Paxos 難」的名聲有一半是文體造成的。（出現章：ch12）
- **Ongaro & Ousterhout，“In Search of an Understandable Consensus Algorithm (Extended Version)”**：`https://raft.github.io/raft.pdf` — Raft 五條 safety 性質的出處（Figure 3）；§5.4.1 的投票限制與 Figure 8 是必讀段落。（出現章：ch13）
- **Ongaro，*Consensus: Bridging Theory and Practice*（Stanford 博士論文，2014）**：`https://github.com/ongardie/dissertation` — membership change 與 log compaction 各有專章；第 8 章與附錄是 safety 證明，README 提到 Verdi 團隊後來在 Coq 裡完成核心安全性的機器證明——ch16「嚴謹度光譜」的真實樣本。（出現章：ch13）

### 業界案例論文與報告

- **Newcombe 等六人，“How Amazon Web Services Uses Formal Methods”（*CACM* 58(4)，2015）**：DOI `https://doi.org/10.1145/2699417`（正式版有付費牆）— 本書所有 AWS 數字與引文的原典；先讀 Table 1 與 DynamoDB「35 步」一節。（2026-06 已對照 PDF 原文逐字核對）（出現章：ch01、ch17）
- **“Use of Formal Methods at Amazon Web Services”（2014 技術報告）**：`https://lamport.azurewebsites.net/tla/formal-methods-amazon.pdf`（Lamport 網站存檔；landscape 標注未開頁）— CACM 版的免費前身，內容高度重疊；引用數字時以 CACM 版為準。（出現章：ch01）
- **Lamport，“Who Builds a House Without Drawing Blueprints?”（*CACM* 58(4)，2015）**：DOI `https://doi.org/10.1145/2736348` — 「寫 spec 的最大價值是先想清楚」論點的原典，四頁，一杯咖啡的長度。（出現章：ch01）
- **“Systems Correctness Practices at Amazon Web Services”（*CACM* 68(6)，2025-06；ACM Queue 版 22(6)）**：`https://queue.acm.org/detail.cfm?id=3712057` — 2015 的十年後續篇，AWS 正確性工具箱的全景。（2026-06 查證時點全文受取用限制，ch17 僅依摘要與二手轉述引用其框架）（出現章：ch17）
- **“Using Lightweight Formal Methods to Validate a Key-Value Storage Node in Amazon S3”（SOSP 2021）**：DOI `https://dl.acm.org/doi/10.1145/3477132.3483540` — ShardStore 的輕量方法論文（Rust 參考模型＋property-based testing）——讀它最重要的理由是搞清楚它**不是** TLA+ 案例。（2026-06 未開原文，存在性經多來源確認）（出現章：ch17）
- **Davis、Hirschhorn、Schvimer，“eXtreme Modelling in Practice”（*PVLDB* 13(9)，2020）**：`http://vldb.org/pvldb/vol13/p1346-davis.pdf` — 工業界少見的誠實：§4 的 MBTC 驗屍報告與 §5 的 MBTCG 成功學，spec–code 同步是真痛點。（2026-06 對照論文原文）（出現章：ch17）
- **Hackett、Rowe、Kuppe，“Understanding Inconsistency in Azure Cosmos DB with TLA+”（ICSE-SEIP 2023）**：arXiv `2210.13661` — 使用者視角 spec 如何照出官方 spec 的縫隙；搭配官方 repo（見 C.3）對讀。（2026-06 對照 arXiv 摘要）（出現章：ch17）

## C.3 spec 原文

GitHub `tlaplus/Examples` repo 為活躍維護（有 CI 驗證工作流程；landscape 2026-06 開頁驗證），以下 Examples 內的路徑全部經 GitHub API 確認存在。

- **DieHard.tla（＋DieHarder.tla）**：`https://github.com/tlaplus/Examples/blob/master/specifications/DieHard/DieHard.tla` — ch08 精讀的原文，註解比程式碼多三倍，Lamport 式教學的標本；DieHarder.tla 把壺的數量與容量推廣成 CONSTANTS。（連結驗證於 2026-06）（出現章：ch08）
- **DieHard_proof.tla**：`https://github.com/tlaplus/Examples/blob/master/specifications/DieHard/DieHard_proof.tla` — ch16 精讀的原檔，全文 81 行；BigToSmall 那個對稱案是現成的自我測驗。（2026-06 開頁下載，引文逐字一致）（出現章：ch16）
- **TCommit.tla**：`https://github.com/tlaplus/Examples/blob/master/specifications/transaction_commit/TCommit.tla` — 交易承諾問題層 spec 全文（66 行）；讀的重點是註解怎麼把每個定義的「為什麼」講完。（出現章：ch11）
- **TwoPhase.tla（＋同目錄 PaxosCommit.tla）**：`https://github.com/tlaplus/Examples/blob/master/specifications/transaction_commit/TwoPhase.tla` — 2PC 協議層 spec 全文；讀完 ch15 回去重看最後兩行，它們是你能逐義務複核的定理，不再只是兩行咒語。（出現章：ch11、ch15）
- **Paxos 三層：Consensus.tla → Voting.tla → Paxos.tla**：`https://github.com/tlaplus/Examples/blob/master/specifications/Paxos/Paxos.tla`（同目錄三份，2026-06 驗證存在）— 把 Voting.tla 的 ShowsSafety 定理對照 ch12 的 ⟨1⟩ 論證讀；Voting.tla 檔尾的 `C == INSTANCE Consensus` 是三層樓中間那層的焊縫（ch15）；Consensus.tla 的 Invariance 是最小的不變量證明範本、LivenessTheorem 是 WF1 規則的機器版（ch16）。（出現章：ch12、ch15、ch16）
- **raft.tla**（Diego Ongaro 本人 repo）：`https://github.com/ongardie/raft.tla` — ch13 所有引文的出處，CC-BY 4.0；README 自述比博士論文版略有更新，想跑 TLC 要參考 PR #4 的修改（2026-06 查證）。通讀一次全文（471 行）是檢驗 ch13 學習成果的最好方式。（出現章：ch13）
- **Lamport 網站上的 Peterson 短文**：`https://lamport.azurewebsites.net/tla/peterson.html` — 用 PlusCal 寫 Peterson 並以 TLC 驗互斥與 starvation-freedom，await 粒度與 ch10 相同（2026-06 查證）；機器跑出來的，跟你手推的同一張圖。（出現章：ch10）
- **locks_auxiliary_vars（tlaplus/Examples）**：`https://github.com/tlaplus/Examples/tree/master/specifications/locks_auxiliary_vars` — Peterson 對抽象 Lock 規格的 refinement，含 auxiliary variables；現在讀吃力是正常的，ch15 之後回來收割。（出現章：ch10）
- **DijkstraMutex（tlaplus/Examples）**：`https://github.com/tlaplus/Examples/tree/master/specifications/dijkstra-mutex` — Dijkstra 1965 原始 n-process 演算法的 PlusCal 版；想體會「為什麼 Peterson 被視為簡潔的奇蹟」，讀它最快。（出現章：ch10）
- **標準模組 Bags.tla**：`https://github.com/tlaplus/tlaplus/blob/master/tlatools/org.lamport.tlatools/src/tla2sany/StandardModules/Bags.tla` — bag 被編碼成「元素 ↦ 正整數份數」的函數，印證 ch04 的 multiset 討論；讀檔頭註解與三個定義即可。（連結驗證於 2026-06）（出現章：ch04）
- **azure-cosmos-tla**（官方 repo）：`https://github.com/Azure/azure-cosmos-tla` — Cosmos DB 五種一致性等級的 TLA+ 規格＋三個由簡到繁的情境模型；搭配上面的 ICSE-SEIP 2023 論文對讀。（2026-06 開頁查證）（出現章：ch17）

## C.4 課程、教材與 Lamport 講義

- **TLA+ Video Course**（Lamport 親自錄製）：`https://lamport.azurewebsites.net/video/videos.html` — 共 10 講（部分分上下集），開場自述「These videos are not light entertainment. They require careful viewing and actual thinking.」——名不虛傳，搭配紙筆服用。各章指路：Lecture 1–2 對應 ch02、Lecture 4 “Die Hard” 是 ch08 精讀的影片版、第 5–6 講是 ch11 兩份 spec 的作者導讀。（連結與講次驗證於 2026-06；landscape 開頁驗證）（出現章：ch02、ch06、ch08、ch11、ch18）
- **learntla.com**（Hillel Wayne）：`https://learntla.com` — 免費線上教材，偏實作操作路線，與本書互為對照組；哪天想動手跑 TLC，從這裡開始最快（landscape 2026-06 開頁驗證，站點持續維護）。各章指過的小節：〈Operators and Values〉（ch03、ch04）、〈Structured Data〉（ch04）、〈Writing an Invariant〉（ch02、ch05）、〈TLA+〉（ch06）、〈Temporal Properties〉（ch07）、〈PlusCal〉（ch08）、Topics 部的〈Optimizing Model Checking〉（ch09）。（出現章：ch01–ch09、ch18）
- **A PlusCal User's Manual**：P-syntax 版 `https://lamport.azurewebsites.net/tla/p-manual.pdf`、C-syntax 版 `https://lamport.azurewebsites.net/tla/c-manual.pdf` — 讀前幾節就夠「看得懂」；兩份手冊對照翻兩頁，你就知道兩種語法真的只是換皮。（連結驗證於 2026-06）（出現章：ch08）
- **Lamport，“Safety, Liveness, and Fairness”（2019-05-26 講義）**：`https://lamport.azurewebsites.net/tla/safety-liveness.pdf` — ch07 的 safety/liveness 定義與 WF/SF 等價讀法的直接出處，短短 8 頁；把第 4 節 WF 的五種等價說法讀到「顯然等價」是最好的自測。（2026-06 開頁核對）（出現章：ch07）
- **Lamport，“Using TLC to Check Inductive Invariance”（2018-08-23）**：`https://lamport.azurewebsites.net/tla/inductive-invariant.pdf` — 兩頁紙把 ch14 的三個義務一字不差地寫出來，然後教你讓 TLC 當歸納步快篩。（2026-06 開頁核對）（出現章：ch14）
- **Lamport，“Proving Safety Properties”（2019-05-18）**：`https://lamport.azurewebsites.net/tla/proving-safety.pdf` — 從找 inductive invariant、寫 ⟨1⟩ 層級證明、到把每一步餵給 TLAPS 的完整工作流；手寫與機器之間最好的一座橋。（2026-06 開頁核對目錄）（出現章：ch14、ch16）
- **Lamport，“Hiding, Refinement, and Auxiliary Variables”（2019）**：`https://lamport.azurewebsites.net/tla/hiding-and-refinement.pdf` — ∃∃（hiding）與 refinement 關係的短篇講義，比論文好入口。（2026-06 連結見於 Lamport 網站，內文未逐頁核對）（出現章：ch15）
- **TLA+ Wiki〈codebase: liveness〉**：`https://docs.tlapl.us/codebase:liveness` — 開發者視角的 liveness 檢查實作：behavior graph、Tarjan SCC、隨圖成長分批執行；ch09 SCC 直覺版的工程對照。（搜尋定位於 2026-06，未逐段核對）（出現章：ch09）
- **Apalache 手冊〈Running the Tool〉**：`https://apalache-mc.org/docs/apalache/running.html` — 用 `--init=IndInv --inv=IndInv --length=1` 兩段式查詢機械化 ch14 兩個義務的官方說明；配合 ch16 的原理段重讀。（2026-06 開頁核對指令與措辭）（出現章：ch14、ch16）

## C.5 工程部落格與案例頁

- **Lorin Hochstein，“Inductive invariants”（Surfing Complexity，2018-12）**：`https://surfingcomplexity.blog/2018/12/27/inductive-invariants/` — 用最小的例子把「為真但不 inductive」講透的短文，還親手解了 Teaching Concurrency 的習題；當 ch05／ch14 的第二視角複習。（出現章：ch05、ch14）
- **Hillel Wayne，“Weak and Strong Fairness”**：`https://www.hillelwayne.com/post/fairness/` — 用一個 succeed/fail/retry 的 worker 把「WF 救不了反覆失敗、SF 可以」演了一遍，與 ch07 的 Requeue 攻防互為印證。（2026-06 開頁核對）（出現章：ch07）
- **Jack Vanlightly，“An introduction to symmetry in TLA+”（2024-12）**：`https://jack-vanlightly.com/blog/2024/12/5/an-introduction-to-symmetry-in-tla` — 用視覺化把軌道坍縮講透，含「對稱與 liveness 不合」的警告與隱性不對稱的踩坑案例。（開頁驗證於 2026-06）（出現章：ch09）
- **raft.github.io**（Raft 官網）：未附獨立連結（與上方 raft.pdf 同站）— 內建 5 節點選舉與複製的互動視覺化（把 ch13 的 worked example 動起來），另收錄各語言實作清單與歷年演講。（出現章：ch13）
- **Nathan VanBenschoten，“Parallel Commits”（CockroachDB blog，2019-11-07）**：`https://www.cockroachlabs.com/blog/parallel-commits/` — 讀協議設計，更要讀文末 TLA+ 驗證一節——AckImpliesCommit 與 ImplicitCommitLeadsToExplicitCommit 兩條性質的命名就是一堂「怎麼把保證說清楚」的課。（2026-06 開頁查證；landscape 開頁驗證）（出現章：ch17）
- **P language 官方案例頁**：`https://p-org.github.io/P/casestudies/` — S3 strong consistency 遷移如何用 P 驗證的第一手簡述。（2026-06 開頁查證）（出現章：ch17）
- **“Using Kani to Validate Security Boundaries in AWS Firecracker”（Kani 官方部落格，2023）**：`https://model-checking.github.io/kani-verifier-blog/2023/08/31/using-kani-to-validate-security-boundaries-in-aws-firecracker.html` — rate limiter 與 virtio 驗證的細節與 bug 清單，程式碼級驗證長什麼樣的最佳速寫。（2026-06 開頁查證）（出現章：ch17）
- **FoundationDB，“Simulation and Testing”**：`https://apple.github.io/foundationdb/testing.html` — deterministic simulation testing 的原典文件，「unlikely that we would have been able to build FoundationDB without this technology」的出處。（2026-06 開頁驗證）（出現章：ch18）
- **Antithesis 的 DST 綜述**：`https://antithesis.com/docs/resources/deterministic_simulation_testing/` — 把 FoundationDB 路線一般化的入門讀物。（連結於 2026-06 經搜尋確認，內文未逐字核對）（出現章：ch18）
- **“Can LLMs model real-world systems in TLA+?”（ACM SIGOPS Blog，2026-05）**：`https://www.sigops.org/2026/can-llms-model-real-world-systems-in-tla/` — ch18 AI 一節 etcd Raft 實測的出處：生成的 spec 能過語法、能跑 TLC，深層語意驗證仍是缺口。（2026-06 查證連結與要旨）（出現章：ch18）

## C.6 工具與社群入口

- **Lamport 的 TLA+ Home Page**：`https://lamport.azurewebsites.net/tla/tla.html` — Lamport 個人網站的 TLA+ 入口；頁面明示官方資源已移交 TLA+ Foundation。（landscape 2026-06 開頁驗證）
- **TLA+ Foundation**：`https://foundation.tlapl.us/` — 官方（基金會）入口。（landscape：連結經 Lamport 首頁證實）
- **TLAPS 官網與 tlapm repo**：`https://proofs.tlapl.us/` 與 `https://github.com/tlaplus/tlapm` — 文件、教學與原始碼；後端組成與預設策略的權威出處。本書不裝工具，但哪天你想動手，入口在這裡。（2026-06 開頁）（出現章：ch16）
- **Quint 官網**：`https://quint.sh`（2026-06 開頁驗證；原 quint-lang.org 已轉址）— 首頁十分鐘看完語法長相，判斷它是不是你團隊的入口。（出現章：ch18）
- **Alloy 官網**：`https://alloytools.org`（2026-06 開頁驗證）— Overview 與文件入口。（出現章：ch18）
- **P 官網**：`https://p-org.github.io/P/`（2026-06 開頁驗證）— 「state machine based programming language」的自述與案例清單；AWS 的採用脈絡見 ch17。（出現章：ch18）

## C.7 如果只讀三樣

你已經讀完十八章，資深後端的直覺也都接上了。如果接下來只有三份東西的時間，我會這樣選：

1. **《Specifying Systems》第一部分（第 1–7 章，約 83 頁）**。理由：它是你剛學完的整個 Part II–III 的原典，而且是免費 PDF。本書替你鋪了白話與橋接，現在回去讀 Lamport 本人的版本，每個設計決定（為什麼無型別、為什麼 stuttering、為什麼 □[Next]_vars）都有作者親自辯護——這一遍會把「學會了」升級成「知道為什麼非這樣不可」。
2. **“How Amazon Web Services Uses Formal Methods”（CACM 2015）**。理由：十頁出頭，是你回答「這套東西在工業界到底是不是玩具」與替團隊寫採用建議時的原典彈藥；本書引用的每個數字（35 步、804 行、七個團隊）都出自這裡且已逐字核對，你引用時可以放心精確。
3. **“eXtreme Modelling in Practice”（PVLDB 2020）**。理由：讀完本書最危險的狀態是高估形式化的下一步——以為 spec 寫完就一勞永逸。這篇是工業界少見的誠實失敗報告（spec–code 同步的真實代價，一成一敗），先把 Murphy 的帳攤開，你的期望值會校準在正確的位置。

遺珠：想往理論深處走，補《A Science of Concurrent Programs》（ch14）；想重走一遍共識的不變量鏈，補 “Paxos Made Simple”（ch12）。

## C.8 想動手時的第一步

本書刻意不碰鍵盤——紙上推演逼你把每一步想穿。完整的路徑指引在 ch18〈如果哪天想動手〉，這裡只給資源對應，照順序：

1. **learntla.com 的 The Core**（C.4）——什麼都不用裝就能開始讀；免費、行文最像工程師對工程師，從零帶到能跑 TLC。
2. **TLA+ Video Course**（C.4）——10 講，Lamport 親授；比 learntla 慢但深，配著本書的章節順序看，每講都會遇到老朋友。
3. **編輯器：VSCode 的 TLA+ extension**（識別碼 `alygin.vscode-tlaplus`）——2026-06 時點的社群主流入口；老牌 Eclipse Toolbox 已進入維護模式（此為社群觀察、措辭保守，見 ch18）。第一步是編輯器，不是安裝包。
4. **第一份 spec 不要寫新的**——把 ch08 的 SettlementV1 打進去，基準參數跑 TLC，親眼看你手推過的那條反例被機器印出來（劇本見 ch18）；想對照官方範例，DieHard.tla 與 `tlaplus/Examples`（C.3）是現成題庫。
5. **之後分流**——想爬證明層：TLAPS 官網（C.6）＋ “Proving Safety Properties”（C.4）；想拉團隊一起：Quint 與 P 的官網（C.6）。
