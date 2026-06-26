# 附錄 C — 延伸閱讀總地圖

> 這份地圖把全書 21 章各自的 `## 延伸閱讀` 收成一張表，去重後分成三條路線：**往深處讀**（該親自讀一次的一手原典）、**往應用走**（把這部歷史接上你的 AI Infra 轉職目標）、**往廣處讀**（給想輕鬆讀軟體／計算史的書與整理）。只收書中各章實際推薦過、且經 landscape 驗證或可獨立查證為真實存在的資源；沒把握的標「（未驗證）」。連結照各章已寫的版本，沒有自行編造新連結。後面標的「（出自 chNN）」是該資源在書中第一次出現的位置，跨多章引用的列出全部。

---

## 往深處讀：經典原典

這些是「導遊講完、你該親自走進現場」的一手文獻。讀完這本書之後，它們是你最讀得進去、回報也最高的。每條附「為什麼值得讀、讀哪一段」。

- **Fred Brooks，《No Silver Bullet — Essence and Accident in Software Engineering》（1986）** — 全書那把手術刀（本質複雜度 vs 偶然複雜度）的原典，不長、論證乾淨。**讀法**：帶著一個問題讀——他 1986 年說「過去的進步砍的都是偶然複雜度」，對照你 2026 年手上的 AI agent，這句話過時了還是更準了？注意它是 1986 的獨立論文，**不是** 1975《人月神話》的內容（1995 週年版才併入）。網路上有全文 PDF/HTML 轉錄。（出自 ch10／ch19／ch20／ch21）

- **Fred Brooks，《The Mythical Man-Month》（1975；二十週年增訂版 1995）** — 方法 strand 的智慧書。若只讀兩章：同名的〈The Mythical Man-Month〉（Brooks's Law 與 O(n²) 溝通的原始論證）與〈Aristocracy, Democracy, and System Design〉（概念完整性、架構與實作分離）。1995 版多收的〈"The Mythical Man-Month" after 20 Years〉是難得的作者自我修正。（出自 ch10）

- **David Parnas，《On the Criteria To Be Used in Decomposing Systems into Modules》（CACM, 1972）** — 資訊隱藏的原典，只有十幾頁，**一定要讀原文**。重點看他把 KWIC 索引用「照流程切」與「照資訊隱藏切」各切一次，再列那串「likely to change」的決策——你 2026 年切微服務的所有道理，1972 年都寫完了。原文：https://dl.acm.org/doi/10.1145/361598.361623 （全文鏡像 http://sunnyday.mit.edu/16.355/parnas-criteria.html）。（出自 ch06／ch21）

- **Melvin Conway，〈How Do Committees Invent?〉（Datamation, 1968-04）** — Conway's Law 的原文，melconway.com 上作者本人放了全文。重點看那句定律的原始措辭——關鍵詞是「溝通結構」，比流行的「組織圖＝系統圖」精細得多。讀完看你自己的服務拓樸圖，你會看到組織結構印在上面。（出自 ch10／ch17／ch21）

- **E. W. Dijkstra，〈Go To Statement Considered Harmful〉（CACM, 1968-03）** — 結構化編程的核心一手文獻，只有兩頁，必讀。重點看「our intellectual powers are rather geared to master static relations」那段；讀完你會發現它離「GOTO 邪惡」的口號有多遠。可對照投稿原題版 EWD215（A Case against the GO TO Statement），看標題如何被編輯改動。（出自 ch05）

- **E. W. Dijkstra，〈Notes on Structured Programming〉（EWD249, 1970）** — 結構化編程綱領的較完整版本，也是「測試只能證明 bug 存在、不能證明不存在」那句的出處之一。Dijkstra Archive（cs.utexas.edu/~EWD）有全部 EWD 手稿掃描。（出自 ch05）

- **John McCarthy，〈Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I〉（CACM, 1960）** — Lisp 的原典，garbage collection 第一次被描述就在這裡（只佔一頁多）。看它怎麼用 eval 證明語言能描述自己——「程式即資料」的最初現場；也是你今天 `arr.map(fn)` 的血緣源頭。原文 PDF：http://jmc.stanford.edu/articles/lisp/lisp.pdf 。（出自 ch04／ch09）

- **C. A. R. Hoare，〈An Axiomatic Basis for Computer Programming〉（CACM, 1969）** — Hoare logic 的原典，只有幾頁。即使不讀完那些推論規則，讀引言——感受 1969 年有人認真想「像證明數學定理一樣證明程式正確」的野心，是理解「型別／形式方法」這條光譜「強的那一端」的鑰匙。https://dl.acm.org/doi/10.1145/363235.363259 。（出自 ch08）

- **C. A. R. Hoare，〈The Emperor's Old Clothes〉（1980 圖靈獎演說，刊 CACM 24(2), 1981）** — 「a language so far ahead of its time…」這句論 ALGOL 60 的名言的原始出處。整篇是大師對「簡單 vs 複雜」的反省，與本書「複雜度守恆」主題直接共鳴。（出自 ch04）

- **Tony Hoare，〈Null References: The Billion Dollar Mistake〉（QCon London 2009，InfoQ 有完整錄影）** — **務必看本人親口講**。看他怎麼描述 1965 那個「太容易實作」的決定；順帶親耳確認這是 2009 QCon，**不是** 1980 圖靈獎演說（那場是上一條的〈The Emperor's Old Clothes〉，兩場常被搞混）。https://www.infoq.com/presentations/Null-References-The-Billion-Dollar-Mistake-Tony-Hoare/ 。（出自 ch08）

- **Winston Royce，〈Managing the Development of Large Software Systems〉（Proc. IEEE WESCON, 1970）** — 全書最該親自讀的論文之一，約 11 頁。**讀法**：讀到那張線性流程圖時先別停，往下讀他怎麼說它「risky and invites failure」、再讀五項修正特別是「Do it twice」那節——你會親眼看見一篇主張迭代的論文怎麼被截走一半、被讀成它的反面。網路上有多份 PDF（如 praxisframework.org）。（出自 ch11／ch12）

- **E. F. Codd，〈A Relational Model of Data for Large Shared Data Banks〉（CACM, 1970-06）** — 關聯模型的原典。讀它對「data independence」的定義，以及他點名要消滅的三種相依（ordering／indexing／access path）——整篇的目標不是「表」，是「解綁」。https://dl.acm.org/doi/10.1145/362384.362685 。（出自 ch13）

- **Charles Bachman，〈The Programmer as Navigator〉（1973 圖靈獎演說，CACM 1973-11）** — 讀 Codd 的對手怎麼**驕傲地**描述那個被 Codd 推翻的世界觀。和 Codd 1970 對讀，你會親眼看到一場範式轉移的兩邊。（出自 ch13）

- **Donald Knuth，〈Structured Programming with go to Statements〉（ACM Computing Surveys, 1974）** — 「premature optimization is the root of all evil」的原始出處。讀 p.268 那段的**完整**上下文（含「97% of the time」與「critical 3%」），你會發現你以為你懂的那句話意思跟流行版相反；它本身也是結構化編程辯論的一手史料。（出自 ch05／ch19）

- **Joel Spolsky，《The Law of Leaky Abstractions》（2002-11-11）** — 「所有非平凡抽象都會洩漏」這條全書收官定律的源頭，原文很短，半小時讀完。留意結尾那句「abstractions save us time working, but they don't save us time learning」——那是這條定律最實際的推論。https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/ 。（出自 ch01／ch13／ch16／ch19）

- **Richard P. Gabriel，《The Rise of Worse is Better》（概念 1989／刊 1991）** — 對比「MIT 派（the right thing）」與「New Jersey 派（worse is better）」，理解為什麼「先簡單地活下來」常常打敗「做到完美」。免費全文：https://www.dreamsongs.com/WorseIsBetter.html 。（出自 ch19）

- **Alan Kay 的 1998 squeak-dev 郵件** — 「The big idea is 'messaging'」那句的原始載體，也是他用 Internet 比喻講 OOP 願景的地方。**一定要讀原文那幾段**，它短，但會徹底改變你對「OOP 是什麼」的預設理解；對照你做微服務的直覺讀。http://lists.squeakfoundation.org/pipermail/squeak-dev/1998-October/017019.html 。（出自 ch07）

- **Ole-Johan Dahl，〈The Birth of Object Orientation: the Simula Languages〉（2001）** — class 與 object 的源頭，由發明者本人回顧。看他怎麼從「模擬港口的船」這種具體需求長出 class，你會懂為什麼 OOP 的出身決定了它後來「用物件對應現實世界東西」的直覺與陷阱。（出自 ch07）

- **Manifesto for Agile Software Development（agilemanifesto.org, 2001）** — 四個價值＋十二條原則，全文不到一頁，必讀。重點看那句保留條件「while there is value in the items on the right, we value the items on the left more」，與十二原則第二條「Welcome changing requirements」——整章核心賭注就在這兩句。history.html 頁有 Snowbird 現場的第一手回憶。（出自 ch12）

- **Herb Sutter，〈The Free Lunch Is Over〉（Dr. Dobb's Journal, 2005-03）** — 函數式四十年後翻身的觸發點。看他怎麼論證「時脈撞牆、未來是並行」——讀完你會懂為什麼一篇 2005 年談 CPU 的文章，會讓 1958 年就有的「不可變」答案突然變值錢。http://www.gotw.ca/publications/concurrency-ddj.htm 。（出自 ch09）

- **John Backus et al.，《The FORTRAN Automatic Coding System》（1957）／John Backus，《The History of FORTRAN I, II, and III》（HOPL, 1978）** — 史上第一次把「自動編程」當賣點的一手文件，與當事人事後寫的史料。1957 原文看標題與引言的承諾句型（和今天 AI 工具官網文案有多像）；1978 史料看團隊怎麼想、怎麼賭、怎麼為了讓產出碼夠快下最佳化的苦工。Software Preservation Group / softwarepreservation.computerhistory.org 有掃描全文。（出自 ch03／ch20）

- **Tim Berners-Lee，〈Information Management: A Proposal〉（CERN, 1989）** — Web 的起點提案，CERN 有原件掃描。看它要解的痛多麼具體、多麼不像「要發明改變世界的東西」——提醒你重大躍遷往往始於一個樸素的本地問題。（出自 ch15）

- **Vint Cerf & Bob Kahn，〈A Protocol for Packet Network Intercommunication〉（IEEE Trans. Comm., 1974）** — TCP/IP 的原典。不必啃數學，看它怎麼論證「讓底層網路保持笨、把互連智慧放到端點」這個 end-to-end 決策——你「在應用層處理可靠性」的整套直覺，根就在這篇。（出自 ch15）

- **Richard Stallman，《The GNU Manifesto》（1985）／《The GNU Project》** — 自由軟體運動的創世文件與較完整回顧。Manifesto 看他怎麼把「分享程式碼」講成倫理立場；GNU Project 看 free 的兩種意思、copyleft 的動機，也是分清 FSF（1985）與 GPLv1（1989）兩個年份最清楚的地方。線上：gnu.org/gnu/manifesto、gnu.org/gnu/thegnuproject。（出自 ch14）

---

## 往應用走：接上你的 AI Infra 之路

這部歷史的最新一章，是你正要去寫的那一章。下面這些把軟體史接到「讓大模型跑得穩、快、省」這個目標——LLM serving 的每一面牆（memory-bound、分散式推論、SLO、節點編排）都是前面這些書講過的牆換了尺度重來。每條附「它接上你哪一段路」。

- **《Site Reliability Engineering: How Google Runs Production Systems》（Google／O'Reilly, 2016，全書免費線上版在 sre.google/sre-book）** — SRE 的聖經，也是你那本 AI Infra 書談「推論延遲 SLO、成本最佳化」的方法地基。**只要讀兩章就值回票價**：〈Embracing Risk〉把「100% 是錯的目標」與 error budget 的邏輯講到底；〈Service Level Objectives〉把 SLI/SLO 怎麼定講清楚。（出自 ch18）

- **Jez Humble & David Farley，《Continuous Delivery》（2010）** — 把「部署從大事件變成按鈕級非事件」這條流水線講透的綱領書，是你天天在用的 CI/CD 的源頭文本。讀「deployment pipeline」那幾章就好。（出自 ch12／ch18）

- **Matthew Skelton & Manuel Pais，《Team Topologies》（2019，teamtopologies.com）** — 平台工程運動的奠基書。讀「cognitive load」與「platform team」兩個概念就好：理解為什麼微服務的「團隊自治」會逼出認知負荷過載、為什麼答案是把複雜度收進一個自助平台——這正是「把 GPU 排程／serving 複雜度收進內部平台」的理論骨架。（出自 ch18）

- **James Lewis & Martin Fowler，〈Microservices〉（martinfowler.com, 2014-03）** — 微服務最權威的定調文。重點看「Organized around Business Capabilities」（用 Conway's Law 論證為什麼按業務能力切）與「Smart endpoints and dumb pipes」兩段——你會發現它通篇都在講組織，不只是技術。https://martinfowler.com/articles/microservices.html 。（出自 ch17）

- **Werner Vogels（訪談 Jim Gray），〈A Conversation with Werner Vogels〉（ACM Queue, 2006）** — 「You build it, you run it」的出處。看 Amazon 怎麼把服務所有權整個交給建造它的團隊——「團隊自治」與「products not projects」的一手源頭，也預告了開發與維運那道牆怎麼被拆掉。（出自 ch17）

- **John Allspaw & Paul Hammond，〈10+ Deploys Per Day: Dev and Ops Cooperation at Flickr〉（Velocity 2009）** — DevOps 的「示範現場」一手史料。2009 年就示範了開發與維運共用版本控制、共用 metric、一鍵部署、feature flag，與那句世界觀翻轉的話：維運的工作不是「保持穩定」，是「讓業務能安全地改變」。（出自 ch18）

- **Benjamin Black，〈EC2 Origins〉（2009，blog.b3k.us/2009/01/25/ec2-origins.html）** — EC2 共同發起人之一的第一手回憶：2003 年那份給 Bezos 的文件、把虛擬伺服器當服務賣的點子怎麼來的。讀它看「雲」如何從一家公司的內部痛點長出來，而非某個宏大藍圖——你租 GPU 算力跑推論，租的是這條線的延伸。（出自 ch16）

- **NIST SP 800-145,〈The NIST Definition of Cloud Computing〉（2011，csrc.nist.gov）** — 只有短短幾頁，是 IaaS/PaaS/SaaS 與雲特性（on-demand、measured service…）的權威定義。當你需要一個不被行銷詞汙染的分類學基準時讀它。（出自 ch16）

- **HashiCorp Terraform 文件的〈What is Infrastructure as Code〉段落（developer.hashicorp.com）** — 當代 IaC 思維最清楚的官方陳述（宣告式、plan/apply、狀態管理）。把「基礎設施即程式碼」對應回你天天寫的 CloudFormation/CDK，再延伸到你會用來宣告 serving 叢集的那套。（出自 ch16）

- **Brendan Burns, Joe Beda, Kelsey Hightower，《Kubernetes: Up and Running》** — 從「天天用 K8s」走向「理解 K8s 為何長這樣」。看它講宣告式 API 與 reconciliation loop 的部分就好——抓住「期望狀態 vs 實際狀態的持續收斂」這個跟 SQL、Terraform 同源的世界觀（你之後排度 GPU 工作負載會一直用到）。（出自 ch17）

- **Jeffrey Dean & Sanjay Ghemawat，〈MapReduce: Simplified Data Processing on Large Clusters〉（OSDI, 2004）** — 看 Google 怎麼明說 MapReduce 的名字與概念取自 Lisp 的 `map`／`reduce`，以及「純函數天生可平行」如何被放大到上千台機器——你 `arr.map()` 的資料中心版本，也是你日後做大規模批次推論／資料前處理的思維原型。https://research.google.com/archive/mapreduce-osdi04.pdf 。（出自 ch09）

- **你書架上的《把系統寫成定理：TLA+ 與形式化方法》** — 本書談 Hoare logic、CAP、最終一致性都點到為止；那本書把「分散式系統的正確性怎麼用 invariant 證明」這條路走到底，正對你那種分散式、並行、最終一致性的 serving 場景。當你想真正搞懂「為什麼分區下不能同時要 C 和 A」，去那裡。（出自 ch08／ch13）

- **你書架上的 AI Infra 書** — 這部歷史的「最新一章」由它接手：模型內部、LLM serving、GPU 排程、推論延遲 SLO、KV cache、成本最佳化。把這本軟體史書當它的「為什麼會走到今天」前傳——你會發現 LLM serving 的每一面牆，都是前面講過的牆換了尺度重來。（出自 ch18／ch21）

---

## 往廣處讀：科普與歷史

想把這本書的「工程師讀法」對照其他讀法（人物史、機構史、社會史、考據態度），擴大視野。下面是給想輕鬆讀軟體／計算史的書、導讀與整理。每條附一句「它補上哪一塊」。

- **Charles Petzold，《The Annotated Turing》** — 逐行註解圖靈 1936〈On Computable Numbers〉。原文數學很硬不必硬啃，這本帶你體會「程式即資料」最早的理論形態。（出自 ch02）

- **Computer History Museum 線上展〈The Stored Program〉與〈ENIAC Programmers Project〉（eniacprogrammers.org）＋ IEEE Spectrum〈The Women Behind ENIAC〉** — 圖文並茂講 Baby／EDSAC／EDVAC 這條線，並把 ENIAC Six 的故事補齊。適合先建立畫面再讀文字。（出自 ch02）

- **twobithistory.org〈What Did Ada Lovelace's Program Actually Do?〉（2018）** — 逐步拆解 Note G 到底算了什麼、為什麼說它更像 trace，是把「第一位程式設計師」爭議講得最清楚、最不情緒化的一篇。（出自 ch02）

- **Eric S. Raymond，〈The Origins and History of Unix, 1969–1995〉（《The Art of Unix Programming》第 2 章）** — 把 Unix 的誕生、C 重寫、擴散講成連貫故事，對「可移植性為什麼是決定性勝利」寫得最清楚。http://www.catb.org/~esr/writings/taoup/html/ch02s01.html 。（出自 ch06）

- **Eric S. Raymond，《The Cathedral and the Bazaar》（1997）** — 把 Linux 現象理論化的那篇。讀「大教堂 vs 市集」的對比與 Linus's Law，讀完記得自己補上 Heartbleed 這個反例的但書。catb.org/~esr/writings/cathedral-bazaar。（出自 ch14）

- **Paul Graham，〈The Roots of Lisp〉** — 用現代讀者讀得懂的方式重講 McCarthy 1960 論文的核心（eval 的七個原始運算子）。如果 Lisp 原典太硬，從這篇進去。（出自 ch04）

- **Paul Hudak et al.，〈A History of Haskell: Being Lazy with Class〉（2007）** — Haskell 委員會自己寫的歷史，講清楚 1987 FPCA 為什麼決定組委員會、Miranda 的影響、為什麼選擇「純粹到底」。https://www.microsoft.com/en-us/research/wp-content/uploads/2016/07/history.pdf 。（出自 ch09）

- **The morning paper（Adrian Colyer）對 Parnas 1972 的導讀** — 若 Parnas 原文的 1972 行文讀起來吃力，先看這篇現代工程師視角的拆解，再回頭讀原文。https://blog.acolyer.org/2016/09/05/on-the-criteria-to-be-used-in-decomposing-systems-into-modules/ 。（出自 ch06）

- **David Wheeler，〈The Waterfall Model〉（dwheeler.com/essays/waterfall.html）** — 對瀑布神話最冷靜可靠的二手整理之一。Wheeler 點明 Royce 稱自己的純線性版本為「simpler method」並明確 recommended against 它，並追溯瀑布如何被後來的標準固化進政府採購。讀完 Royce 原文後拿來對照、確認自己沒讀偏。（出自 ch11）

- **Bjarne Stroustrup，〈A History of C++〉（HOPL II, 1993）** — C++ 作者親述「為什麼是 class with classes、為什麼 zero-overhead」，是「OOP 進主流要付什麼妥協」最清楚的一手材料。https://www.stroustrup.com/hopl2.pdf 。（出自 ch07）

- **Steve Yegge，〈Execution in the Kingdom of Nouns〉（2006）** — 對「Java 把一切硬塞進 class（名詞王國）」的著名吐槽。當作對照組讀，感受「class 中心 OOP 被推到極致」的荒謬，再回頭對照 Kay 的訊息願景。（觀點文，非史料。）（出自 ch07）

- **Takeuchi & Nonaka，〈The New New Product Development Game〉（Harvard Business Review, 1986）** — Scrum 的思想根。看「接力賽 vs 橄欖球」那組對比，你會發現敏捷對「跨職能團隊一起推進」的主張，1986 年就被兩位商管學者在汽車與相機工廠裡觀察到了。（出自 ch12）

- **Martin Fowler，《Refactoring》（1999；第 2 版 2018 改用 JavaScript 範例）** — 重構的系統化論述。讀「為什麼重構」那幾章就好，理解「在不改變外部行為下持續改善內部結構」為什麼是敏捷的必需品。martinfowler.com 上有大量免費 bliki 短文可先嚐。（出自 ch12）

- **Dave Thomas，〈Agile is Dead (Long Live Agility)〉（2014）＋ Martin Fowler 談「Agile Industrial Complex」（Agile Australia 2018 keynote）** — 宣言原作者親口診斷「Agile」一詞如何被掏空、被企業收編，是「敏捷帳單」最有分量的一手佐證。（出自 ch12）

- **The Phoenix Project（Gene Kim, Kevin Behr, George Spafford, 2013）** — DevOps 的傳教小說。想理解「為什麼那道牆是組織與文化問題、不是工具問題」，讀小說比讀論文有效；配套《The DevOps Handbook》（2016）是它的實務版。（出自 ch18）

- **Gerwin Klein 等，seL4: Formal Verification of an OS Kernel（CACM 摘要版）** — 想知道「形式驗證真的拿來驗一個能跑的系統」長什麼樣，看這篇。重點不是技術細節，是感受「為了證明一個微核心無 bug 要付出的人力規模」——你會立刻明白為什麼它進不了你的後端。https://cacm.acm.org/research/sel4-formal-verification-of-an-operating-system-kernel/ 。（出自 ch08）

- **Benjamin C. Pierce，《Types and Programming Languages》（TAPL）—— 只讀 Preface／第 1 章** — 型別系統的權威教科書，但**不必讀內文**（型別理論硬核，本書不展開）。只讀引言那幾頁，看他怎麼把型別系統定位成「最普及的輕量形式方法」。System F、dependent types 想深入，這本是入口。https://www.cis.upenn.edu/~bcpierce/tapl/ 。（出自 ch08）

- **Scott Chacon & Ben Straub，《Pro Git》（線上免費，git-scm.com/book）** — 本書刻意沒展開的「Git 內部物件模型」在這裡有最清楚的講解。讀第 10 章〈Git Internals〉，你會看到內容定址、blob/tree/commit、DAG 在程式碼層面長什麼樣。（出自 ch14）

- **Christine Peterson，〈How I coined the term 'open source'〉（opensource.com, 2018）** — 「open source」這個詞 1998 年怎麼被造出來、為什麼要刻意去道德化的第一手回憶，理解「自由軟體 vs 開源」分歧的好入口。（出自 ch14）

- **Tim O'Reilly，〈What Is Web 2.0〉（oreilly.com, 2005）＋ Jesse James Garrett，〈Ajax: A New Approach to Web Applications〉（2005-02）** — 「瀏覽器從文件檢視器變成應用平台」這波轉變的命名文與 AJAX 一詞的出處。看「在瀏覽器裡跑應用」在 2005 年還是個需要被命名、被論證的新觀念。（出自 ch15）

- **MinnPost〈The rise and fall of the Gopher protocol〉（2016）等 Gopher 興衰整理** — 把「開放標準擊敗圍牆花園」個案的另一半補齊：一個差點贏、卻被一個授權決定親手葬送的競爭者。（歷史整理、非一手檔案，年份與流量數字屬估計。）（出自 ch15）

- **Eric Brewer，〈CAP Twelve Years Later: How the "Rules" Have Changed〉（2012, IEEE Computer）** — CAP 提出者本人十二年後的澄清：「三選二」其實是過度簡化，分區只在真的發生時才逼你選。讀它能讓你不把 CAP 講成口號。（出自 ch13）

- **James Martin，《Application Development Without Programmers》（1981）** — 4GL 運動的綱領，光看書名就值得記住：這是「不需要程式設計師」這個夢最赤裸的一次命名。對照低程式碼／無程式碼今天的文案，你會看見同一個承諾隔四十年的兩次發聲。（原書較難找，讀其維基條目與 4GL 條目即可掌握脈絡。）（出自 ch20）

- **維基百科〈Computer-aided software engineering〉條目 ＋ 1993 年 GAO 對 CASE 工具的評估** — 把 CASE 工具的興衰當教學案例：怎麼被吹上天（1990 年近 200 種產品、IBM 的 AD/Cycle）、又怎麼安靜地死掉（GAO「幾乎沒有證據顯示能改善生產力」）。讀它能讓你對 2026 的喧囂多一分免疫力。（出自 ch20）

- **Martin Fowler，《TwoHardThings》（bliki）** — 關於「cache 失效與命名」這句話，Fowler 親自考據歸屬、坦承找不到一手出處的短文。讀它示範「廣為流傳 ≠ 經得起查證」的引用自律——這本身就是本書一直在教你的事。https://martinfowler.com/bliki/TwoHardThings.html 。（出自 ch01／ch19）

---

## 如果只看三樣

從上面三條路線各挑一個最高槓桿的：

1. **Fred Brooks，《No Silver Bullet》（1986，往深處讀）** — 全書四條主線的交會點，也是你拿來測下一個技術宣稱（包括 AI coding）最常用的那把刀。三篇最該讀的原典裡若只挑一篇，挑它。

2. **《Site Reliability Engineering》的〈Embracing Risk〉＋〈Service Level Objectives〉兩章（2016，往應用走）** — 你 AI Infra 之路的方法地基：error budget 與 SLO 把「可靠度」從信仰變成可談判的工程量，這正是 LLM serving 要你建的東西。兩章、免費、立刻能用。

3. **Joel Spolsky，《The Law of Leaky Abstractions》（2002，往廣處／回望）** — 半小時讀完，但會永久改變你看每一層抽象的方式。讀完你會在每一次 ORM 的 N+1、每一次 Lambda 冷啟動、每一張爆掉的雲帳單裡，認出同一條定律——這是「複雜度守恆」最日常的證據。

---

> **協調者複核備註（編譯時觀察，非書內容）**
>
> 各章延伸閱讀的連結與資源逐條對照 landscape 與獨立查證後，**未發現偽造或明顯不存在的連結**；下列幾條僅標示「需留意」而非「可疑」，供複核時參考：
> - **ch16〈EC2 Origins〉**：landscape 無此條，但已獨立查證 blog.b3k.us/2009/01/25/ec2-origins.html 真實存在（Benjamin Black 本人部落格）。⚠️ 待協調者複核是否要把此一手來源升格進 landscape。
> - **ch20《Application Development Without Programmers》（James Martin, 1981）**：landscape 無此條，已獨立查證該書真實存在（Prentice Hall, 1981, ISBN 0130389439）。各章亦自承「原書較難找」。⚠️ 待協調者確認是否補進 landscape。
> - 部分二手導讀（The New Stack 的 FORTRAN 文、gigamonkeys 的 Brooks's Law 分析、pragtob/Tobias Mayer 的 Royce 逐段導讀、abortretry.fail 的 Gopher 長文）各章以「搜標題可得」帶過、未給固定 URL；它們存在但網址未釘死，本附錄從略或只保留有穩定連結者，避免收錄會腐爛的連結。⚠️ 此為編譯取捨，待協調者確認是否需要補回。
> - landscape 已標 ⚠️ 的資源（Kay 1998 email 單一來源、COBOL LOC 統計）本附錄沿用各章既有 hedge，未另作斷言。
