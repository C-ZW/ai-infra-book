# Landscape 2026-06 — 排隊理論書的事實基準

本檔是各章寫作 agent 的事實基準：易變動或常被記錯的事實，每條附來源 URL。
除標注 ⚠️（未驗證）者外，所有條目於 2026-06-12 經 WebSearch/WebFetch 實際查證
（免費 PDF 均實際抓取確認標題或 HTTP 200 + Content-Type）。

## 教科書與免費資源

- **Mor Harchol-Balter,《Performance Modeling and Design of Computer Systems: Queueing Theory in Action》**，Cambridge University Press，2013 年 2 月。本書主要參考教科書。**無免費 PDF**（作者明言建議買紙本，Kindle 版會弄壞數學式）；第 1 章免費試讀、errata 在書頁上。
  來源：https://www.cs.cmu.edu/~harchol/PerformanceModeling/book.html （2026-06 驗證）
- **Mor Harchol-Balter,《Introduction to Probability for Computing》**，Cambridge University Press，2024。**全書 PDF 免費**，已驗證可下載（HTTP 200，8.4 MB，伺服器端 2026-03 更新）：
  https://www.cs.cmu.edu/~harchol/Probability/chapters/HarcholBalterWholeBook.pdf
  書頁（含逐章 PDF 與投影片）：http://www.cs.cmu.edu/~harchol/Probability/book.html （2026-06 驗證）
- **Ivo Adan & Jacques Resing,《Queueing Systems》講義**（TU Eindhoven, Department of Mathematics and Computing Science），版本日期 1995 初版多次修訂、現行 PDF 標注 **2015-03-26**。免費 PDF，已抓取並確認標題與作者：
  https://www.win.tue.nl/~iadan/queueing.pdf （301 轉向 https://iadan.win.tue.nl/queueing.pdf ，2026-06 驗證）
- **Leonard Kleinrock,《Queueing Systems》** Vol. 1: Theory（Wiley, 1975，417 頁）；Vol. 2: Computer Applications（Wiley, 1976）。經典兩卷本，無官方免費 PDF。
  來源：https://onlinelibrary.wiley.com/doi/abs/10.1002/net.3230060210 、https://www.wiley.com/en-us/Queueing+Systems,+Volume+2:+Computer+Applications-p-9780471491118
- **Shortle, Thompson, Gross, Harris,《Fundamentals of Queueing Theory》第 5 版**，Wiley，2018（ISBN 9781118943526）。注意：第 5 版作者順序是 Shortle/Thompson/Gross/Harris；舊版習慣引作 "Gross & Harris"，引用時對齊版次。
  來源：https://www.wiley.com/en-us/Fundamentals+of+Queueing+Theory,+5th+Edition-p-9781118943526
- **Bertsekas & Gallager,《Data Networks》第 2 版**（Prentice Hall, 1992）。MIT 官方頁面提供**全書逐章免費下載**（非商業用途；含 Chapter 3 "Queueing"——本書 G/G/1、網路相關章可引）＋解答手冊。
  來源：https://web.mit.edu/dimitrib/www/datanets.html （2026-06 驗證）
- **Robert Gallager,《Stochastic Processes: Theory for Applications》**，Cambridge University Press，2013（ISBN 9781107039759）。配套課程 **MIT OCW 6.262 Discrete Stochastic Processes（Spring 2011, Gallager 親授）**有完整錄影、講義（開放教科書草稿）、習題解答：
  https://ocw.mit.edu/courses/6-262-discrete-stochastic-processes-spring-2011/ （2026-06 驗證）
  書籍頁：https://www.cambridge.org/9781107039759
- **CMU 15-857 Analytical Performance Modeling & Design of Computer Systems**（Harchol-Balter；奇數年秋季開課，1999 至今，最近一次 Fall 2025）。主題涵蓋 operational laws、Markov chains、Poisson process、queueing、simulation——與本書章節結構高度對應。
  入口：https://www.cs.cmu.edu/~harchol/ ；課綱 PDF：https://www.cs.cmu.edu/~harchol/Perfclass/webpage.pdf （2026-06 驗證 HTTP 200）

## 經典論文（年份、出處、歸屬複核）

逐章引用時照此表，不要憑記憶寫年份。

- **A.K. Erlang**：生卒 **1878-01-01（Lønborg, Denmark）– 1929-02-03（Copenhagen）**。
  1909 "The Theory of Probabilities and Telephone Conversations"，*Nyt Tidsskrift for Matematik B*, Vol. 20, pp. 33–39——證明隨機電話呼叫服從 Poisson 分布、部分解決延遲問題。
  1917 "Solution of Some Problems in the Theory of Probabilities of Significance in Automatic Telephone Exchanges"，*Elektroteknikeren*, Vol. 13——loss formula（Erlang B）與等待時間（Erlang C）出處。
  來源：https://mathshistory.st-andrews.ac.uk/Biographies/Erlang/ 、https://plus.maths.org/content/agner-krarup-erlang-1878-1929
- **D.G. Kendall 1953** "Stochastic Processes Occurring in the Theory of Queues and their Analysis by the Method of the Imbedded Markov Chain"，*Annals of Mathematical Statistics* 24(3): 338–354。A/S/c 記號（Kendall notation）的起源論文。
  https://projecteuclid.org/euclid.aoms/1177728975
- **J.D.C. Little 1961** "A Proof for the Queuing Formula: L = λW"，*Operations Research* 9(3): 383–387。
  https://pubsonline.informs.org/doi/10.1287/opre.9.3.383
  **S. Stidham 1974** "Technical Note—A Last Word on L = λW"，*Operations Research* 22(2): 417–421（僅假設極限平均存在且有限的嚴格證明）。
  https://pubsonline.informs.org/doi/epdf/10.1287/opre.22.2.417
- **D.V. Lindley 1952** "The Theory of Queues with a Single Server"，*Mathematical Proceedings of the Cambridge Philosophical Society* 48(2): 277–289。Lindley recursion（W_{n+1} = max(0, W_n + S_n − A_n)）出處。
  https://www.cambridge.org/core/journals/mathematical-proceedings-of-the-cambridge-philosophical-society/article/abs/theory-of-queues-with-a-single-server/53E80E039A02BCCC909E5C1D3BBC1AD1
- **J.F.C. Kingman**——兩篇都存在、常被混引：
  **1961** "The Single Server Queue in Heavy Traffic"，*Math. Proc. Cambridge Philos. Soc.* 57(4): 902–904（DOI 10.1017/s0305004100036094）；
  **1962** "On Queues in Heavy Traffic"，*J. Royal Statistical Society Series B* 24(2): 383–392。
  G/G/1 等待時間近似（Kingman approximation）章引 1961，並可注 1962 為一般化。
  https://www.cambridge.org/core/journals/mathematical-proceedings-of-the-cambridge-philosophical-society/article/abs/single-server-queue-in-heavy-traffic/81C55BC00A68FE6D5385638AA0B0AF37 、https://academic.oup.com/jrsssb/article/24/2/383/7035157
- **P.J. Burke 1956** "The Output of a Queuing System"，*Operations Research* 4(6): 699–704。Burke's theorem（M/M/c 穩態輸出仍為 Poisson）。
  https://pubsonline.informs.org/doi/10.1287/opre.4.6.699
- **J.R. Jackson**：**1957** "Networks of Waiting Lines"，*Operations Research* 5(4): 518–521（open network product form）；**1963** "Jobshop-Like Queueing Systems"，*Management Science* 10(1): 131–142（state-dependent rates 推廣）。
  https://ideas.repec.org/a/inm/oropre/v5y1957i4p518-521.html 、https://pubsonline.informs.org/doi/abs/10.1287/mnsc.10.1.131
- **W.J. Gordon & G.F. Newell 1967** "Closed Queuing Systems with Exponential Servers"，*Operations Research* 15(2): 254–265。封閉網路 product form。
  https://ideas.repec.org/a/inm/oropre/v15y1967i2p254-265.html
- **F. Pollaczek 1930** "Über eine Aufgabe der Wahrscheinlichkeitstheorie"，*Mathematische Zeitschrift* 32: 64–100 與 729–750（兩部分）。
  https://link.springer.com/article/10.1007/BF01194620
  **A.Ya. Khinchine 1932** "Mathematical Theory of a Stationary Queue"，*Matematicheskii Sbornik* 39(4): 73–84 ⚠️（卷期頁碼來自 Wikipedia 引用鏈，未直查俄文原刊）。英文拼法：Pollaczek（固定）；Khinchine 亦作 Khinchin／Khintchine，公式名通行 **Pollaczek–Khinchine formula**。
  https://en.wikipedia.org/wiki/Pollaczek%E2%80%93Khinchine_formula
- **R.W. Wolff 1982** "Poisson Arrivals See Time Averages"，*Operations Research* 30(2): 223–231。PASTA 縮寫即出自此文標題；核心假設是 lack of anticipation。
  https://pubsonline.informs.org/doi/abs/10.1287/opre.30.2.223
- **L. Schrage 1968** "Letter to the Editor—A Proof of the Optimality of the Shortest Remaining Processing Time Discipline"，*Operations Research* 16(3): 687–690。注意體裁是 Letter to the Editor，不是 full paper。
  https://pubsonline.informs.org/doi/10.1287/opre.16.3.687
- **M. Reiser & S.S. Lavenberg 1980** "Mean-Value Analysis of Closed Multichain Queuing Networks"，*Journal of the ACM* 27(2): 313–322。MVA 出處。
  https://dl.acm.org/doi/10.1145/322186.322195
- **S. Halfin & W. Whitt 1981** "Heavy-Traffic Limits for Queues with Many Exponential Servers"，*Operations Research* 29(3): 567–588。QED（Halfin–Whitt）regime 的極限定理出處；square-root staffing 的歸屬細節見「常被誤傳的事實」。
  https://ideas.repec.org/a/inm/oropre/v29y1981i3p567-588.html
- **BCMP 1975**：F. Baskett, K.M. Chandy, R.R. Muntz, F.G. Palacios, "Open, Closed, and Mixed Networks of Queues with Different Classes of Customers"，*Journal of the ACM* 22(2): 248–260。四位作者、JACM——兩者都常被記錯。
  https://dl.acm.org/doi/10.1145/321879.321887

## 系統與工程文獻（應用章引用）

- **Dean & Barroso, "The Tail at Scale"**，*Communications of the ACM* 56(2): 74–80，**2013 年 2 月**。tail latency 章的定錨文獻。
  DOI 頁：https://dl.acm.org/doi/10.1145/2408776.2408794 ；開放入口：https://research.google/pubs/the-tail-at-scale/
- **"Metastable Failures in Distributed Systems"**，Nathan Bronson, Abutalib Aghayev, Aleksey Charapko, Timothy Zhu，**HotOS 2021**（pp. 221–227）。開放 PDF 已驗證（HTTP 200, application/pdf）：
  https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf
- **"Metastable Failures in the Wild"**，Lexiang Huang, Matthew Magnusson, Abishek Bangalore Muralikrishna, Salman Estyak, Rebecca Isaacs, Abutalib Aghayev, Timothy Zhu, Aleksey Charapko（8 位作者，自 USENIX 頁面 metadata 逐一核對），**OSDI 2022**。開放 PDF：
  https://www.usenix.org/system/files/osdi22-huang-lexiang.pdf （頁面 https://www.usenix.org/conference/osdi22/presentation/huang-lexiang ）
- **Marc Brooker 部落格**（三篇皆從其 blog 索引頁逐一核對 URL 與日期，2026-06）：
  - "Metastability and Distributed Systems"（2021-05-24）——metastable failure 的排隊直覺入門，retry storm 章引。
    https://brooker.co.za/blog/2021/05/24/metastable.html
  - "Fixing retries with token buckets and circuit breakers"（2022-02-28）——retry 放大係數與 token-bucket 限流，retry storm 章引。
    https://brooker.co.za/blog/2022/02/28/retries.html
  - "Surprising Economics of Load-Balanced Systems"（2020-08-06）——M/M/c vs 多個 M/M/1 的池化效益，正好配 Erlang C 章。
    https://brooker.co.za/blog/2020/08/06/erlang.html
- **Gil Tene, "How NOT to Measure Latency"**（Strange Loop 2015 場次為通行版本）。coordinated omission 的出處談話；標題與頻道經 YouTube oEmbed 驗證。
  https://www.youtube.com/watch?v=lJ8ydIuPFeU
- **Orca**：Gyeong-In Yu, Joo Seong Jeong, Geon-Woo Kim, Soojeong Kim, Byung-Gon Chun, "Orca: A Distributed Serving System for Transformer-Based Generative Models"，**OSDI 2022**（5 位作者自 USENIX metadata 核對）。continuous batching（論文用語 iteration-level scheduling）出處。
  https://www.usenix.org/system/files/osdi22-yu.pdf
- **vLLM**：Woosuk Kwon, Zhuohan Li 等, "Efficient Memory Management for Large Language Model Serving with PagedAttention"，**SOSP 2023**。arXiv：https://arxiv.org/abs/2309.06180
- 2025–2026 現狀（一句話即可，本書只當配菜；深入內容歸 AI Infra 主書）：continuous batching＋PagedAttention 已是 LLM serving 排程的業界基線，vLLM 持續活躍維護（最新 release **v0.22.1，2026-06-05**，GitHub Releases API 驗證，2026-06）。
  https://github.com/vllm-project/vllm/releases

## 工具現狀（2026-06）

- **simpy 4.1.2**（PyPI，2026-05-24 釋出；Development Status 5 - Production/Stable，支援 Python 3.8–3.14）。"Event discrete, process based simulation for Python."
  https://pypi.org/project/simpy/ （PyPI JSON API 驗證，2026-06）
- **ciw 3.2.7**（PyPI，2025-12-05 釋出）。"A discrete event simulation library for open queueing networks."
  https://pypi.org/project/ciw/ （PyPI JSON API 驗證，2026-06）
- 本書實驗以標準庫為主（`random`、`statistics`、`heapq`），numpy/matplotlib 可選；simpy/ciw 只在延伸閱讀提及，不寫教學。

## 常被誤傳的事實

- **「Erlang 發明排隊理論」**——精確說法：Erlang 1909 證明隨機電話呼叫服從 Poisson 分布並部分解決延遲問題，1917 給出 loss／waiting 公式；「排隊理論」作為一般化學科是 1950 年代由 Kendall（1953 記號與 imbedded Markov chain）、Lindley（1952）等人建制化的。
  https://mathshistory.st-andrews.ac.uk/Biographies/Erlang/
- **Little's Law 在 1961 之前是 folk theorem**——L = λW 在 Little 證明前已被廣泛當作常識使用，但缺一般性證明；Little 本人在 50 週年回顧（Little, "Little's Law as Viewed on Its 50th Anniversary"，*Operations Research* 59(3): 536–549, 2011）詳述這段歷史。
  https://people.cs.umass.edu/~emery/classes/cmpsci691st/readings/OS/Littles-Law-50-Years-Later.pdf
- **PASTA 命名由來**——縮寫直接來自 Wolff 1982 論文標題 "Poisson Arrivals See Time Averages"；性質本身在更早文獻已被個案使用，Wolff 給出一般證明（lack of anticipation 假設）。
  https://pubsonline.informs.org/doi/abs/10.1287/opre.30.2.223
- **Square-root staffing 歸屬**——不能整包歸給 Halfin–Whitt。正確分層：經驗法則（rule of thumb）久已存在於電話工程實務，常被上溯到 Erlang 1924 年的工作 ⚠️（「1924」這個年份未在本次查證來源中直接確認，引用時寫「可上溯至 Erlang」即可）；**Halfin & Whitt 1981** 給出 many-server 極限定理（QED regime）；**Borst, Mandelbaum & Reiman, "Dimensioning Large Call Centers"（*Operations Research* 52(1): 17–34, 2004）**給出該法則的嚴格漸近證成。
  https://ideas.repec.org/a/inm/oropre/v52y2004i1p17-34.html
- **P-K 公式兩人各自貢獻**——Pollaczek 1930 以複變／分析方法先得到結果（Math. Z. 32）；Khinchine 1932 以機率論語言重新推導，公式因此掛雙名。兩人沒有合作。拼字：Pollaczek–Khinchine（Khinchin、Khintchine 亦通行）。
  https://en.wikipedia.org/wiki/Pollaczek%E2%80%93Khinchine_formula
- **Kingman 公式的年份**——常被籠統寫成「Kingman 1962」或「1960s」；單伺服器 heavy-traffic 短文是 **1961**（PCPS 57(4): 902–904），**1962** 是 JRSS-B 的一般化長文。見上方經典論文節。
- **Gordon–Newell 不是「Jackson 的封閉版小改」**——封閉網路的 normalization constant 讓計算本質變難（後續才有 Buzen 的卷積法與 Reiser–Lavenberg 1980 的 MVA），寫作時不要把 1967→1980 之間的計算難題一筆帶過。
- **Schrage 1968 的 SRPT 最佳性**是「任意到達序列下最小化系統內工作數」的 sample-path 結果，發表體裁是 Letter to the Editor；「SRPT 會餓死大工作」在 M/G/1 下並不成立於想像的程度（公平性討論見 Harchol-Balter 2013 教科書），排程章需區分這兩層。

## 掃描日誌

- 2026-06-12 初版（建書 P1）
