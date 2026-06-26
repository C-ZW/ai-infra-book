# 附錄 D — 延伸閱讀總地圖

這張地圖把全書二十一章的延伸閱讀彙整成一份，去掉重複（Harchol-Balter、Adan–Resing、MIT 6.262、Marc Brooker 等貫穿多章的資源各只列一次，附上所有用到它的章），按六個 Part 組織。每筆都標明「是什麼＋什麼時候讀＋哪幾章用過」。連結以 `_meta/landscape-2026-06.md` 驗證過的為主；少數只在某章出現、由該章寫作時自行查證的連結，標「（章驗證）」，待一致性掃描複核。標「（2026-06）」者為時效性條目，版本或可用性會隨時間變動。讀完不知從哪下手，先看最後兩節：「如果只讀三樣」與「想更嚴格時的下一本」。

---

## 主幹資源（貫穿全書，先在這裡認識）

這幾筆橫跨多個 Part，是全書的骨幹，先建立印象，後面各 Part 不再重述其定位。

- **Mor Harchol-Balter,《Performance Modeling and Design of Computer Systems: Queueing Theory in Action》(Cambridge, 2013)** — 本書全程的主要參考教科書，電腦系統視角、工程友善、習題有火氣。無免費 PDF（作者明言別買 Kindle，數學式會壞），官網有第 1 章試讀與 errata。幾乎每章都指回它的對應章節。
  用於 ch01、ch02、ch03、ch04、ch06、ch07、ch08、ch09、ch11、ch12、ch13、ch15、ch16、ch17、ch18、ch19、ch21。
  https://www.cs.cmu.edu/~harchol/PerformanceModeling/book.html
- **Mor Harchol-Balter,《Introduction to Probability for Computing》(Cambridge, 2024)** — 全書 PDF 免費（2026-06 驗證可下載）。機率地基與重尾章的第一手敘述；想系統性重建機率工具就讀它。
  用於 ch03、ch04、ch05、ch15（ch15 另指逐章 PDF 的 Ch.10）。
  https://www.cs.cmu.edu/~harchol/Probability/chapters/HarcholBalterWholeBook.pdf
- **Ivo Adan & Jacques Resing,《Queueing Systems》講義（TU Eindhoven，2015-03-26 版）** — 全本免費 PDF，最精簡而嚴謹的對照教材；推完本書任一推導拿它對答案的首選。
  用於 ch01、ch03、ch04、ch05、ch07、ch08、ch09、ch12。
  https://www.win.tue.nl/~iadan/queueing.pdf
- **MIT OCW 6.262《Discrete Stochastic Processes》(Gallager, Spring 2011)** — 完整錄影＋開放講義＋習題解答；想把本書「快速複習即可」的機率與隨機過程地基補成研究所級嚴格的免費權威下一站。
  用於 ch03、ch04、ch05、ch06、ch07、ch11、ch21。
  https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/
- **Marc Brooker 部落格** — 工程師視角的排隊直覺，本書多處的「互動體感版」。三篇：
  - "Surprising Economics of Load-Balanced Systems"（2020-08-06）— 用 Erlang-C 算「池子越大延遲越好」。用於 ch01、ch09、ch19。 https://brooker.co.za/blog/2020/08/06/erlang.html
  - "Fixing retries with token buckets and circuit breakers"（2022-02-28）— token bucket 給 retry 設預算。用於 ch10、ch20。 https://brooker.co.za/blog/2022/02/28/retries.html
  - "Metastability and Distributed Systems"（2021-05-24）— metastable failure 的排隊直覺入門。用於 ch20。 https://brooker.co.za/blog/2021/05/24/metastable.html

---

## Part I — 地圖與定律（ch01–02）

- **MacTutor: Agner Krarup Erlang（1878–1929）傳記** — 1909、1917 兩篇里程碑論文的脈絡：這門數學誕生於真實工程壓力。用於 ch01、ch05、ch09。 https://mathshistory.st-andrews.ac.uk/Biographies/Erlang/
- **Jeffrey Dean & Luiz André Barroso, "The Tail at Scale", *CACM* 56(2), 2013** — 「平均與 tail 是兩回事」的工程定錨文獻；ch01 預告、ch18 鋪墊、ch20 兌現（hedged/tied requests）。用於 ch01、ch18、ch20。 https://research.google/pubs/the-tail-at-scale/
- **Little, J.D.C. (1961). "A Proof for the Queuing Formula: L = λW." *Operations Research* 9(3): 383–387** — Little's Law 原始證明（平穩假設版）。用於 ch02。 https://pubsonline.informs.org/doi/10.1287/opre.9.3.383
- **Stidham, S. (1974). "A Last Word on L = λW." *Operations Research* 22(2): 417–421** — 只剩兩個極限假設的最終版；體會「假設可以削到多薄」。用於 ch02。 https://pubsonline.informs.org/doi/epdf/10.1287/opre.22.2.417
- **Little, J.D.C. (2011). "Little's Law as Viewed on Its 50th Anniversary." *Operations Research* 59(3): 536–549** — folk theorem 的歷史與五十年應用清單，免費 PDF；§2 歷史段最值得讀。用於 ch02。 https://people.cs.umass.edu/~emery/classes/cmpsci691st/readings/OS/Littles-Law-50-Years-Later.pdf
- **Denning, P.J. & Buzen, J.P. (1978). "The Operational Analysis of Queueing Network Models." *ACM Computing Surveys* 10(3): 225–261** — 操作分析的建制化論文，ch02 世界觀的出處（章驗證）。用於 ch02。 https://dl.acm.org/doi/10.1145/356733.356735
- **Lazowska, Zahorjan, Graham & Sevcik (1984). *Quantitative System Performance*. Prentice-Hall** — 作者取回版權後全書免費；fundamental laws 與 bounds 兩章是 asymptotic bounds 的標準教科書處理，ch17 的 MVA 也用它（章驗證）。用於 ch02、ch17。 https://homes.cs.washington.edu/~lazowska/qsp/

---

## Part II — 機率地基（ch03–06）

- **Wikipedia "Memorylessness"** — 唯一性刻畫與函數方程 S(t+s)=S(t)S(s) 的精簡陳述，複習 ch04 證明骨架用（二手來源，章驗證）。用於 ch04。 https://en.wikipedia.org/wiki/Memorylessness
- **Wikipedia "Palm–Khintchine theorem"** — 「大量獨立稀疏流疊加趨向 Poisson」定理的精確敘述（章驗證）。用於 ch05。 https://en.wikipedia.org/wiki/Palm%E2%80%93Khintchine_theorem
- **Levin, Peres & Wilmer,《Markov Chains and Mixing Times》2nd ed.（AMS）** — 耦合論證完整版與 mixing time 的標準參考，作者頁全書免費 PDF（2026-06 驗證，章驗證）。用於 ch06。 https://pages.uoregon.edu/dlevin/MARKOV/mcmt2e.pdf
- **J.R. Norris,《Markov Chains》(Cambridge)** — 離散時間理論乾淨俐落、CTMC 嚴格版（Q matrix、jump chain、爆炸判準），ch06/ch07「指路」的正主；作者頁部分章節免費（2026-06 驗證，章驗證）。用於 ch06、ch07。 https://www.statslab.cam.ac.uk/~james/Markov/
- **Martin Fowler, "CircuitBreaker"（2014-03-06）** — breaker 模式的通行工程描述；對照 ch06 模型看出工程描述裡的陷阱（章驗證）。用於 ch06。 https://martinfowler.com/bliki/CircuitBreaker.html
- **Brian Hayes, "First Links in the Markov Chain"（American Scientist）** — Markov 1906 年為何發明這東西的科普長文，當甜點（章驗證）。用於 ch06。 https://www.americanscientist.org/article/first-links-in-the-markov-chain

---

## Part III — 生滅與經典模型（ch07–11）

- **Kleinrock,《Queueing Systems, Vol. 1: Theory》(Wiley, 1975)** — 第 3 章 "Birth-Death Queueing Systems in Equilibrium" 是生滅過程的經典處理；無官方免費 PDF。用於 ch07（亦見 ch21 的兩卷本路徑）。 https://www.wiley.com/en-us/Queueing+Systems,+Volume+I-p-9780471491101
- **Wikipedia "Birth–death process"** — recurrence/transience 判準（ch07 不展開的第二條級數）的速查（章驗證）。用於 ch07。 https://en.wikipedia.org/wiki/Birth%E2%80%93death_process
- **R.W. Wolff, "Poisson Arrivals See Time Averages", *Operations Research* 30(2): 223–231, 1982** — PASTA 的出生地；讀引言與定理敘述拿到 lack of anticipation 的精確形式。用於 ch08。 https://pubsonline.informs.org/doi/abs/10.1287/opre.30.2.223
- **D.G. Kendall, "Stochastic Processes Occurring in the Theory of Queues…", *Annals of Mathematical Statistics* 24(3): 338–354, 1953** — A/S/c 記號（Kendall notation）的出處論文。用於 ch08。 https://projecteuclid.org/euclid.aoms/1177728975
- **Kendall's notation（Wikipedia）** — 擴充欄位（/K/N/D）與各欄慣例速查（二手來源，章驗證）。用於 ch08。 https://en.wikipedia.org/wiki/Kendall%27s_notation
- **Adan & Resing 的 M/M/1 講義（5 頁 PDF）** — T~Exp(μ−λ) 的 Erlang 混合推導與 mean-value 路線的最精簡版（2026-06 驗證，章驗證）。用於 ch08。 https://iadan.win.tue.nl/blockq/h3.pdf
- **Halfin & Whitt, "Heavy-Traffic Limits for Queues with Many Exponential Servers", *Operations Research* 29(3), 1981** — QED 極限定理原文；β 與極限等待機率的精確函數關係從這裡進。用於 ch09。 https://ideas.repec.org/a/inm/oropre/v29y1981i3p567-588.html
- **Borst, Mandelbaum & Reiman, "Dimensioning Large Call Centers", *Operations Research* 52(1), 2004** — 把「β 怎麼選」寫成成本最佳化並嚴格證成 √ 法則。用於 ch09。 https://ideas.repec.org/a/inm/oropre/v52y2004i1p17-34.html
- **Shortle, Thompson, Gross & Harris,《Fundamentals of Queueing Theory》5th ed.（Wiley, 2018）** — ch10 全部模型（M/M/1/K、M/M/c/K、有限母體、balking/reneging）的標準教科書處理，公式表齊全當速查。用於 ch10。 https://www.wiley.com/en-us/Fundamentals+of+Queueing+Theory,+5th+Edition-p-9781118943526
- **Garnett, Mandelbaum & Reiman, "Designing a Call Center with Impatient Customers", *M&SOM* 4(3): 208–227, 2002** — Erlang-A（M/M/c+M）的定錨論文，ch10 不耐煩敘述的出處（章驗證）。用於 ch10。 https://pubsonline.informs.org/doi/10.1287/msom.4.3.208.7753
- **Haight, "Queueing with Balking"（*Biometrika* 44, 1957）／"Queueing with Reneging"（*Metrika* 2, 1959）** — 兩種不耐煩行為的命名出處，歷史趣味大於實用（章驗證）。用於 ch10。 https://academic.oup.com/biomet/article-abstract/44/3-4/360/238518
- **Wikipedia "Leaky bucket"** — 把 Turner 1986 的出處與「計量器 vs 佇列」兩種身分的混淆史整理得很清楚（少數值得推薦的條目，章驗證）。用於 ch10。 https://en.wikipedia.org/wiki/Leaky_bucket
- **nginx 官方文件 ngx_http_upstream_module** — `max_conns` 與 `queue` 指令就是 M/M/c/K 的工程化身（佇列滿或逾時回 502）（2026-06；章驗證）。用於 ch10。 https://nginx.org/en/docs/http/ngx_http_upstream_module.html
- **P.J. Burke, "The Output of a Queuing System", *Operations Research* 4(6): 699–704, 1956** — Burke 定理原始論文（輸出間隔直接分析）。用於 ch11。 https://pubsonline.informs.org/doi/10.1287/opre.4.6.699
- **E. Reich, "Waiting Times When Queues are in Tandem", *Annals of Mathematical Statistics* 28(3): 768–773, 1957** — Burke 定理的可逆性路線源頭，串聯兩站等待獨立性也出自此（章驗證）。用於 ch11。 https://projecteuclid.org/euclid.aoms/1177706889
- **F.P. Kelly,《Reversibility and Stochastic Networks》（Wiley 1979；Cambridge 2011 重印）** — 可逆性的聖經：第 1 章是 Burke 那批定理的嚴格版（含 Kolmogorov 判準），第 2–3 章鋪到 Jackson 網路與 quasi-reversibility。作者官方頁提供免費全文（2026-06 驗證）。用於 ch11、ch16、ch18。 https://www.statslab.cam.ac.uk/~fpk1/rsn.html
- **P.J. Burke, "Proof of a Conjecture on the Interarrival-Time Distribution in an M/M/1 Queue with Feedback", *IEEE Trans. Communications* 24: 575–576, 1976** — feedback 合流不是 Poisson 的定論（邊際間隔是兩指數混合），兩頁讀完（章驗證）。用於 ch11。 https://ieeexplore.ieee.org/document/1093335/

---

## Part IV — 超越指數（ch12–15）

- **Wikipedia "Pollaczek–Khinchine formula"** — 平均式與 transform 式的對照、Pollaczek 1930／Khinchine 1932 歸屬簡史（章驗證）。用於 ch12。 https://en.wikipedia.org/wiki/Pollaczek%E2%80%93Khinchine_formula
- **Wikipedia "M/G/1 queue"** — embedded chain 轉移結構與 busy period 的 Kendall functional equation，ch12 兩個「存在聲明」的下一步入口（章驗證）。用於 ch12。 https://en.wikipedia.org/wiki/M/G/1_queue
- **Pollaczek 1930, "Über eine Aufgabe der Wahrscheinlichkeitstheorie", *Mathematische Zeitschrift* 32** — 歷史原典（德文、複變方法），看一眼會感激 mean-value 路線的存在。用於 ch12。 https://link.springer.com/article/10.1007/BF01194620
- **Kleinrock 1965, "A Conservation Law for a Wide Class of Queueing Disciplines", *Naval Research Logistics Quarterly* 12(2): 181–192** — 守恆律原典，UCLA 開放 PDF（章驗證）。用於 ch13。 https://www.lk.cs.ucla.edu/data/files/Kleinrock/A%20Conservation%20Law%20for%20a%20Wide%20Class%20of%20Queueing%20Disciplines.pdf
- **Kingman 1962, "The Effect of Queue Discipline on Waiting Time Variance", *Math. Proc. Cambridge Philos. Soc.* 58(1): 163–164** — 「FCFS 變異數最小」的兩頁原典（章驗證）。用於 ch13。 https://www.cambridge.org/core/journals/mathematical-proceedings-of-the-cambridge-philosophical-society/article/abs/effect-of-queue-discipline-on-waiting-time-variance/D48362807F5674D679592E8BBA13C63C
- **Schrage 1968, "Letter to the Editor—A Proof of the Optimality of the Shortest Remaining Processing Time Discipline", *Operations Research* 16(3): 687–690** — SRPT 最優性完整證明（體裁是 Letter to the Editor）。用於 ch13。 https://pubsonline.informs.org/doi/10.1287/opre.16.3.687
- **Bansal & Harchol-Balter 2001, "Analysis of SRPT Scheduling: Investigating Unfairness", SIGMETRICS 2001** — 「餓死長工作」的逐條量化，ch13 引用的定理全在這（章驗證）。用於 ch13。 https://www.cs.cmu.edu/~harchol/Papers/Sigmetrics01.pdf
- **Sakata, Noguchi & Oizumi 1971, "An Analysis of the M/G/1 Queue Under Round-Robin Scheduling", *Operations Research* 19(2): 371–385** — PS 作為 RR 極限的原始分析、insensitivity 出處之一（章驗證）。用於 ch13。 https://pubsonline.informs.org/doi/10.1287/opre.19.2.371
- **Node.js 官方文件 "The Node.js Event Loop, Timers, and process.nextTick()"** — 拿 PS 眼鏡重讀 event loop phases 與「執行到耗盡」語意（2026-06；章驗證）。用於 ch13。 https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick
- **Kingman 1961, "The Single Server Queue in Heavy Traffic", *Math. Proc. Cambridge Philos. Soc.* 57(4): 902–904** — heavy-traffic 近似原典，三頁短文看一個不等式怎麼打開一個領域。用於 ch14。 https://www.cambridge.org/core/journals/mathematical-proceedings-of-the-cambridge-philosophical-society/article/abs/single-server-queue-in-heavy-traffic/81C55BC00A68FE6D5385638AA0B0AF37
- **Kingman 1962, "Some inequalities for the queue GI/G/1", *Biometrika* 49(3/4): 315–324** — ch14 上界的出處（章驗證）。用於 ch14。 https://academic.oup.com/biomet/article-abstract/49/3-4/315/223450
- **Lindley 1952, "The Theory of Queues with a Single Server", *Math. Proc. Cambridge Philos. Soc.* 48(2): 277–289** — Lindley recursion 與積分方程的出處，G/G/1 理論的起點。用於 ch14。 https://www.cambridge.org/core/journals/mathematical-proceedings-of-the-cambridge-philosophical-society/article/abs/theory-of-queues-with-a-single-server/53E80E039A02BCCC909E5C1D3BBC1AD1
- **Whitt 1983, "The Queueing Network Analyzer", *Bell System Technical Journal* 62(9): 2779–2815** — 把兩矩近似工程化成整套網路工具（QNA）；C² 如何在多站間傳播的代表作，免費 PDF（章驗證）。用於 ch14、ch18。 http://www.columbia.edu/~ww2040/QNA_1983.pdf
- **Krämer & Langenbach-Belz 1976, "Approximate Formulae for the Delay in the Queueing System GI/G/1"（ITC 8）** — C²ₐ<1 區的標準修正因子，ch14 D/M/1 偏高 18% 的解藥（章驗證）。用於 ch14。 https://www.semanticscholar.org/paper/Approximate-Formulae-for-the-Delay-in-the-Queueing-Kraemer-Langenbach-belz/311428c1ef0588162f2321d25452952001c1b3b1
- **Bertsekas & Gallager,《Data Networks》2nd ed., Ch. 3** — G/G/1 上界與通訊網路 Jackson／Kleinrock 獨立性近似的免費嚴謹版（MIT 官方逐章下載）。用於 ch14、ch16。 https://web.mit.edu/dimitrib/www/datanets.html
- **AllAboutLean, "The Kingman Formula – Variation, Utilization, and Lead Time"** — 製造業視角的 VUT 讀法（《Factory Physics》把它叫 VUT equation）（章驗證）。用於 ch14。 https://www.allaboutlean.com/kingman-formula/
- **Harchol-Balter《Introduction to Probability for Computing》Ch.10 "Heavy Tails"（逐章 PDF）** — ch15 證據段第一手敘述：UNIX 量測、網頁檔案 α≈1.1、雲端 α≈0.72，含 Bounded Pareto 習題（章驗證）。用於 ch15。 https://www.cs.cmu.edu/~harchol/Probability/chapters/chpt10.pdf
- **Crovella & Bestavros, "Self-Similarity in World Wide Web Traffic", *IEEE/ACM ToN* 5(6): 835–846, 1997** — 網頁檔案重尾證據原典，鏡像 PDF（章驗證）。用於 ch15。 https://ant.isi.edu/csci551/images/c/c2/Crovella97a.pdf
- **Harchol-Balter & Downey, "Exploiting Process Lifetime Distributions for Dynamic Load Balancing", *ACM TOCS* 15(3), 1997（SIGMETRICS '96 版免費）** — UNIX 行程壽命 P(>t)≈1/t 的量測與搶占式遷移含義（章驗證）。用於 ch15。 https://www.cs.cmu.edu/~harchol/Papers/Sigmetrics96.pdf
- **Borst, Boxma & Núñez-Queija, "Heavy Tails: The Effect of the Service Discipline", TOOLS 2002 (LNCS 2324)** — FCFS／PS／LCFS 在 regularly varying 服務下尾巴行為的綜述，ch15 兩條敘述層級尾巴結果的嚴格版入口（章驗證）。用於 ch15。 https://link.springer.com/chapter/10.1007/3-540-46029-2_1
- **Zwart & Boxma, "Sojourn time asymptotics in the M/G/1 processor sharing queue", *Queueing Systems* 35: 141–166, 2000** — PS 的 P(T>x)~P(S>(1−ρ)x) 出處（章驗證）。用於 ch15。 https://link.springer.com/article/10.1023/A:1019142010994

---

## Part V — 佇列網路（ch16–18）

- **J.R. Jackson, "Networks of Waiting Lines", *Operations Research* 5(4): 518–521, 1957** — 開放網路乘積形式原典，只有四頁（章驗證）。用於 ch16。 https://pubsonline.informs.org/doi/abs/10.1287/opre.5.4.518
- **J.R. Jackson, "Jobshop-Like Queueing Systems", *Management Science* 10(1): 131–142, 1963** — 狀態相依服務速率的推廣（M/M/c 站）。用於 ch16。 https://pubsonline.informs.org/doi/abs/10.1287/mnsc.10.1.131
- **B. Melamed, "Characterizations of Poisson traffic streams in Jackson queueing networks", *Adv. Appl. Prob.* 11(2): 422–438, 1979** — 「迴路上的流必非 Poisson」判準的出處，把 ch16 的驚奇釘成定理（章驗證）。用於 ch16。 https://www.cambridge.org/core/journals/advances-in-applied-probability/article/abs/characterizations-of-poisson-traffic-streams-in-jackson-queueing-networks/090226B97FAA5EC414481C4B41BC53BD
- **M. Reiser & S.S. Lavenberg, "Mean-Value Analysis of Closed Multichain Queuing Networks", *JACM* 27(2): 313–322, 1980** — MVA 的出生地，原文直接是多 class 版；讀第 2 節看三條方程的原始形態。用於 ch17。 https://dl.acm.org/doi/10.1145/322186.322195
- **W.J. Gordon & G.F. Newell, "Closed Queuing Systems with Exponential Servers", *Operations Research* 15(2): 254–265, 1967** — 封閉網路乘積形式的出處；對照 Jackson 1957 看 normalization constant 怎麼出現。用於 ch17。 https://ideas.repec.org/a/inm/oropre/v15y1967i2p254-265.html
- **J.P. Buzen, "Computational algorithms for closed queueing networks…", *CACM* 16(9): 527–531, 1973** — 把 normalization constant G 從不可算變成 O(N·k) 的卷積演算法，MVA 之前的全部可算性（章驗證）。用於 ch17。 https://dl.acm.org/doi/10.1145/362342.362345
- **K.C. Sevcik & I. Mitrani, "The Distribution of Queuing Network States at Input and Output Instants", *JACM* 28(2): 358–371, 1981** — arrival theorem 的完整證明（與 Lavenberg–Reiser 獨立得出）（章驗證）。用於 ch17。 https://dl.acm.org/doi/10.1145/322248.322257
- **F. Baskett, K.M. Chandy, R.R. Muntz, F.G. Palacios, "Open, Closed, and Mixed Networks of Queues…", *JACM* 22(2): 248–260, 1975** — BCMP 原典；定理敘述（§3）含四型站的精確條件。用於 ch18。 https://dl.acm.org/doi/10.1145/321879.321887
- **L. Flatto & S. Hahn, "Two Parallel Queues Created by Arrivals with Two Demands I", *SIAM J. Appl. Math.* 44(5), 1984** — fork-join n=2 精確解的出處；讀引言感受「為什麼只有 n=2」即可（章驗證）。用於 ch18。
- **R. Nelson & A.N. Tantawi, "Approximate Analysis of Fork/Join Synchronization in Parallel Queues", *IEEE Trans. Computers* 37(6), 1988** — 工程上最常用的 fork-join 近似（scaling approximation），n≤32 誤差 5% 內（章驗證）。用於 ch18。 https://research.ibm.com/publications/approximate-analysis-of-forkjoin-synchronization-in-parallel-queues
- **A. Thomasian, "Analysis of Fork/Join and Related Queueing Systems", *ACM Computing Surveys* 47(2), Article 17, 2014** — fork-join 文獻全景 survey，當目錄用（章驗證）。用於 ch18。 https://dl.acm.org/doi/10.1145/2628913

（Kelly《Reversibility and Stochastic Networks》也用於 ch16、ch18，已列於 Part III。Whitt QNA 1983 也用於 ch18，已列於 Part IV。Bertsekas–Gallager《Data Networks》也用於 ch16，已列於 Part IV。Lazowska 等《Quantitative System Performance》也用於 ch17，已列於 Part I。）

---

## Part VI — 模擬與回到系統（ch19–21）

- **Gil Tene, "How NOT to Measure Latency"（Strange Loop 2015）** — coordinated omission 的出處談話；現場演示修正 CO 前後 P99.99 差幾個數量級。用於 ch19、ch20。 https://www.youtube.com/watch?v=lJ8ydIuPFeU
- **P.D. Welch, "The Statistical Analysis of Simulation Results"（1983）** — 暖機期偵測 Welch 法的原始出處；找不到原文時 Rossetti 開放教科書有清楚的現代重述（2026-06 驗證，章驗證）。用於 ch19。 https://rossetti.github.io/RossettiArenaBook/statistical-analysis-techniques-for-warmup-detection.html
- **simpy 官方文件（PyPI）／ciw 官方文件（PyPI）** — 要寫比單站複雜的網路模擬、不想自己管事件 heap 時的成熟 Python 選擇；它們解決「排程事件」、不是「方法學」（2026-06，版本見正文：simpy 4.1.2、ciw 3.2.7）。用於 ch19。 https://pypi.org/project/simpy/ ；https://pypi.org/project/ciw/
- **Nathan Bronson et al., "Metastable Failures in Distributed Systems", *HotOS 2021*** — 雙穩態的定錨論文；把 trigger／sustaining effect 的區分內化。開放 PDF。用於 ch20。 https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf
- **Lexiang Huang et al., "Metastable Failures in the Wild", *OSDI 2022*** — 前一篇的實證續集，真實案例譜系與緩解手段。開放 PDF。用於 ch20。 https://www.usenix.org/system/files/osdi22-huang-lexiang.pdf
- **Gyeong-In Yu et al., "Orca: A Distributed Serving System for Transformer-Based Generative Models", *OSDI 2022*** — continuous batching（論文用語 iteration-level scheduling）的出處；ch20 只當點綴，機制深度在書架上的《從後端到 AI Infra》。用於 ch20。 https://www.usenix.org/system/files/osdi22-yu.pdf
- **Michael Mitzenmacher, "The Power of Two Choices in Randomized Load Balancing", *IEEE TPDS* 12(10), 2001** — ch21 po2c 半頁敘述的原始出處之一（佇列版雙指數衰減）；另一獨立來源是 Vvedenskaya–Dobrushin–Karpelevich 1996（章驗證）。用於 ch21。 https://cs.colby.edu/courses/F09/cs231-labs/labs/lab07/Mitzenmacher-2Choices-TPDS2001.pdf
- **Leonard Kleinrock,《Queueing Systems》Vol. 1: Theory（Wiley, 1975）／Vol. 2: Computer Applications（Wiley, 1976）** — 經典兩卷本，理論深水區（transform 方法、嚴格推導）＋電腦/網路應用；無官方免費 PDF。用於 ch21（Vol. 1 第 3 章亦見 ch07）。 https://onlinelibrary.wiley.com/doi/abs/10.1002/net.3230060210

（"The Tail at Scale" 也用於 ch20，已列於 Part I。Marc Brooker 三篇與 MIT 6.262、Harchol-Balter、Adan–Resing 的後續路徑已列於主幹資源。）

---

## 如果只讀三樣

給這位讀者（資深後端工程師，要嚴謹但要能落地）槓桿最高的三筆：

1. **Harchol-Balter《Performance Modeling and Design of Computer Systems》** — 全書的對應教科書，工程視角、習題有火氣；一本就把 operational laws 到 SRPT 排程到 BCMP 全覆蓋。值得買紙本當案頭書。
2. **Adan & Resing《Queueing Systems》講義（免費 PDF）** — 最精簡的嚴謹對照；每次推完一個公式拿它對答案，隨身可查、零成本。
3. **Marc Brooker, "Surprising Economics of Load-Balanced Systems"** — 一篇部落格把池化效益用 Erlang-C 算給你看；把書裡的數學直接接回「該配幾個 worker」的工程決策，是理論落地的最短路徑。

## 想更嚴格時的下一本

當你覺得 Harchol-Balter 的工程化敘述不夠嚴格、想看「原版的嚴謹」，順著這條路往上走（依 landscape 的階梯）：

1. **MIT OCW 6.262《Discrete Stochastic Processes》(Gallager)** — 先補地基：Markov 過程、renewal theory、heavy-traffic 的真正理論，免費錄影＋講義＋習題解答，研究所級但自學友善。對應教科書是 Gallager《Stochastic Processes: Theory for Applications》(Cambridge, 2013)。
2. **Kleinrock《Queueing Systems》Vol. 1: Theory（1975）** — 排隊理論本身的嚴謹原版：transform 方法、嚴格推導；Vol. 2 接到電腦/網路應用。無免費 PDF。
3. **F.P. Kelly《Reversibility and Stochastic Networks》** — 想把 Burke／Jackson／BCMP 那條網路主線推到底（可逆性、quasi-reversibility、insensitivity 的嚴格地基），作者頁有免費全文。
4. **Shortle, Thompson, Gross & Harris《Fundamentals of Queueing Theory》5th ed.（2018）** — 想要一本公式表最齊、模型涵蓋最廣的速查型教科書時的補充。

時效提醒（2026-06）：工具版本（simpy 4.1.2、ciw 3.2.7）與官方文件連結（nginx、Node.js、PyPI）會隨時間變動，引用前以當下版本為準；免費 PDF 的可用性（Kelly、Levin–Peres–Wilmer、Lazowska 等作者自架頁面）亦可能變動。
