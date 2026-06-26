# 附錄 A — 軟體史總時間軸

> 這張表把全書二十一章散落各處的里程碑收進一條編年線，每一條標出它屬於哪一條 strand（抽象／方法／both）、以及主要在哪一章被講透——它是全書「跨章年份一致性」的最終對帳表，年份與歸屬一律照 `_meta/landscape-2026-06.md` 的主時間軸。

## 主時間軸

下表只收**書中（任一章）實際講過**的事件；年份照 landscape 主時間軸，landscape 用區間或標 ⚠️ 的，這裡照樣 hedge。「strand」欄沿用全書定調：**抽象**＝用什麼蓋（語言／型別／抽象層）、**方法**＝怎麼蓋（流程／工程實務）、**both**＝同時是語言事件與方法事件。「章」欄填該事件**主要**在哪一章被攤開（多章回收的，標主場章；跨章回收見該章內文）。

| 年份 | 里程碑 | strand | 章 |
|---|---|---|---|
| 1837 | Babbage 提出 Analytical Engine 設計（從未完整建成；是「設計」不是「機器」） | 抽象 | ch02 |
| 1843 | Lovelace 隨 Menabrea 講稿英譯所附 Notes A–G（含 Note G／Bernoulli 數）⚠️「第一位程式設計師」是有爭議的後世標籤，Note G 嚴格說更像執行軌跡 | 抽象 | ch02 |
| 1936 | Turing〈On Computable Numbers〉；Church 抽出 untyped λ-calculus（計算的另一個理論根，FP 的源頭） | 抽象 | ch02／ch09 |
| 1945 | 《First Draft of a Report on the EDVAC》——儲存程式工程藍圖 ⚠️ 單獨署名 von Neumann，與 Eckert/Mauchly 的功勞爭議照書 | both | ch02 |
| 1945–46 | ENIAC 運轉（1945-12-10 首題、1946-02-15 公開）；非儲存程式機，以插線板設定；ENIAC Six 女程式設計師 | both | ch02 |
| 1948 | Manchester Baby（SSEM）跑出第一支儲存程式（世界第一台運轉的電子儲存程式電腦，實驗機） | 抽象 | ch02 |
| 1949 | EDSAC 運轉（第一台「實用的」完整儲存程式電腦）；Wheeler「Initial Orders」＝史上第一個組譯器系統 | 抽象 | ch02（機器）／ch03（組譯器） |
| 1951–52 | Hopper A-0 ⚠️「第一個編譯器」需保留——以現代定義更接近 loader/linker，非把高階語言翻成機器碼的現代 compiler | 抽象 | ch03 |
| 1957 | FORTRAN 出貨——第一個廣泛使用的高階語言；「automatic programming」的賭注（效能↔生產力鐘擺第一次擺動） | 抽象 | ch03 |
| 1958–60 | LISP（McCarthy）——程式即資料（homoiconicity）、遞迴、garbage collection 的誕生；eval 被 Steve Russell 手工編成機器碼 | 抽象 | ch04（語言哲學）／ch09（FP 源頭） |
| 1959–60 | COBOL（CODASYL；Hopper 經 FLOW-MATIC 深刻影響，非唯一作者）——為商業可讀性設計、長壽 | 抽象 | ch04 |
| 1960 | ALGOL 60 Report；block structure；BNF（Backus–Naur Form）；後世語言的共同祖先 | 抽象 | ch04 |
| 1965 | Hoare 在 ALGOL W 引入 null reference——後來他稱為「billion-dollar mistake」（道歉場合是 2009 QCon，非 1980 圖靈獎演說） | 抽象 | ch08 |
| 1966 | Böhm–Jacopini 結構化定理——sequence／selection／iteration 三結構足夠 | 抽象 | ch05 |
| 1967 | Simula 67（Dahl & Nygaard）——首個帶 class／object／inheritance 的語言，OOP 概念源頭 | 抽象 | ch07 |
| 1968 | NATO Garmisch 會議喊出 software crisis、「software engineering」刻意挑釁命名；Dijkstra〈Go To Statement Considered Harmful〉（標題是編輯 Wirth 下的）；Conway〈How Do Committees Invent?〉刊於 Datamation（1967 投稿被 HBR 退稿；「Conway's Law」之名後人冠上） | both | ch05（NATO／GoTo）／ch10（Conway） |
| 1969 | ARPANET 上線（年底四節點）；Hoare logic〈An Axiomatic Basis for Computer Programming〉；NATO Rome 會議；Unix 開發起步（Thompson, Bell Labs） | both | ch15（ARPANET）／ch08（Hoare logic）／ch05（NATO）／ch06（Unix） |
| 1970 | Codd〈A Relational Model of Data〉——關聯模型原典、資料獨立性；Royce〈Managing the Development of Large Software Systems〉📌 常被誤讀為瀑布之父，實際上他把純線性當反例、倡議迭代 | both | ch13（Codd）／ch11（Royce） |
| 1970s | Smalltalk-72/-76/-80（Kay/Ingalls/Goldberg, Xerox PARC）——Kay 造「object-oriented」一詞；ML 與 Hindley–Milner 型別推論（Milner, Edinburgh）——第一個有多型型別推論的實用系統 | 抽象 | ch07（Smalltalk）／ch08（ML/HM） |
| 1972 | C 語言（Ritchie）；Parnas〈On the Criteria To Be Used in Decomposing Systems into Modules〉——information hiding 原典 | both | ch06 |
| 1973 | Unix pipes（McIlroy 推動進 Unix）——小工具用 pipe 組合的哲學 | 抽象 | ch06 |
| 1974 | TCP/IP 論文（Cerf & Kahn）；SEQUEL（→SQL，Chamberlin & Boyce）；Knuth「premature optimization is the root of all evil」完整脈絡（97%／關鍵 3%）；Dijkstra 在 EWD447 造「separation of concerns」一詞 | both | ch15（TCP/IP）／ch13（SQL）／ch19（Knuth）／ch06（SoC） |
| 1975 | 《The Mythical Man-Month》（Brooks，經驗來自 OS/360）；Brooks's Law（加人到遲到的專案讓它更遲到）；概念完整性 | 方法 | ch10 |
| 1976 | 「Waterfall」一詞首現（一般歸 Bell & Thayer）——晚於 Royce 論文 6 年、非 Royce 自稱 | 方法 | ch11 |
| 1978 | K&R《The C Programming Language》；Unix 哲學原則（McIlroy 等，1978 原句「Make each program do one thing well」；⚠️ 流傳的整齊三句版是 Salus 1994 轉述） | both | ch06 |
| 1979 | 「C with Classes」起步（1983 改名 C++）（Stroustrup, Bell Labs） | 抽象 | ch07 |
| 1983 | GNU 宣告（Stallman）；TCP/IP flag day（NCP 切到 TCP/IP）；ACID 一詞（Härder & Reuter；概念奠基 Jim Gray，原未含 isolation） | both | ch14（GNU）／ch15（flag day）／ch13（ACID） |
| 1985 | Free Software Foundation（Stallman，「free as in freedom」）；Miranda（Turner）——惰性純函數、Haskell 主要靈感 | both | ch14（FSF）／ch09（Miranda） |
| 1986 | 📌《No Silver Bullet》（Brooks，**1986 論文**，非 1975 原書；本質 vs 偶然複雜度——全書的分析手術刀） | 方法 | ch10 |
| 1989 | WWW 提案〈Information Management: A Proposal〉（Berners-Lee, CERN）；「Worse is Better」概念（Gabriel，正式刊 1991） | both | ch15（WWW 提案）／ch19（Worse is Better） |
| 1990 | Haskell 1.0（委員會；1987 FPCA 決議組委員會、1990-04 發表第一份 Report）——惰性、純函數式的終點 | 抽象 | ch09 |
| 1991 | WWW 對外公開（1991-08）；Linux kernel（Torvalds，1992 改自由軟體授權） | both | ch15（WWW）／ch14（Linux） |
| 1993 | Mosaic 圖形瀏覽器（Andreessen & Bina, NCSA）；**CERN 宣告 WWW 進入公有領域（1993-04-30，無人可擁有）**；CFEngine（IaC 工具線起點） | both | ch15（Mosaic／CERN）／ch16（CFEngine） |
| 1995 | Java 1.0（Gosling, Sun；「Write Once, Run Anywhere」）；Scrum 正式發表（OOPSLA；根在 Takeuchi & Nonaka 1986） | both | ch07（Java）／ch12（Scrum） |
| 1997 | 〈The Cathedral and the Bazaar〉（Raymond）——大教堂式 vs 市集式開發 | 方法 | ch14 |
| 1998 | 「Open Source」一詞（Peterson 造詞，OSI 成立）；VMware 成立 | both | ch14（Open Source）／ch16（VMware） |
| 1999 | 《Extreme Programming Explained》（Beck）；《Refactoring》（Fowler）；VMware Workstation | both | ch12（XP/重構）／ch16（VMware Workstation） |
| 2000 | CAP conjecture（Brewer, PODC）——規模逼迫放棄強一致 | 抽象 | ch13 |
| 2001 | Agile Manifesto（Snowbird, 17 簽署人）——四大價值、對重量級流程的反叛 | 方法 | ch12 |
| 2002 | CAP 證明（Gilbert & Lynch）；〈The Law of Leaky Abstractions〉（Joel Spolsky）——「所有非平凡抽象都會洩漏」 | both | ch13（CAP 證明）／ch19（抽象洩漏） |
| 2003 | Xen（paravirtualization）；Google SRE 起（約 2003，Treynor Sloss 創立） | both | ch16（Xen）／ch18（SRE 起源） |
| 2004 | MapReduce 論文（Dean & Ghemawat, OSDI；名字與概念取自 Lisp 的 map/reduce，純函數天生可平行）；Web 2.0 命名（O'Reilly–MediaLive 腦力激盪） | both | ch09（MapReduce）／ch15（Web 2.0） |
| 2005 | 〈The Free Lunch Is Over〉（Sutter, *Dr. Dobb's*）——多核轉折、不可變值錢；AJAX 一詞（Garrett）；Web 2.0 定義文〈What Is Web 2.0〉（O'Reilly）；Puppet（IaC）；Git（Torvalds，BitKeeper 授權爭議觸發，極短時間成形） | both | ch09（Free Lunch）／ch15（AJAX/Web 2.0）／ch16（Puppet）／ch14（Git） |
| 2006 | AWS S3（2006-03）／EC2（2006-08）——IaaS 起點，伺服器從「擁有」變「按片租用」；Google Bigtable 論文（NoSQL 技術源頭） | both | ch16（AWS）／ch13（Bigtable） |
| 2007 | Linux cgroups 進 kernel（Google 主推，容器底層血統）；Amazon Dynamo 論文 | both | ch17（cgroups）／ch13（Dynamo） |
| 2009 | 首屆 DevOpsDays（Debois, Ghent）——DevOps 一詞；NoSQL meetup（命名 Eric Evans）；Chef（IaC） | 方法 | ch18（DevOps）／ch13（NoSQL）／ch16（Chef） |
| 2010 | 《Continuous Delivery》（Humble & Farley）——自動化部署流水線 | 方法 | ch18 |
| 2013 | Docker 公開（Hykes, PyCon lightning talk）——把環境差異封進不可變 image（回收 code as data）；《The Phoenix Project》 | both | ch17（Docker）／ch18（Phoenix Project） |
| 2014 | Kubernetes（Google 宣布並開源，血脈承 Borg）；Microservices 定義文（Lewis & Fowler）；Terraform（HashiCorp） | both | ch17（K8s／微服務）／ch16（Terraform） |
| 2015 | CNCF 成立（K8s 為首個種子專案） | 方法 | ch17 |
| 2016 | 《Site Reliability Engineering》（Google／O'Reilly）——SLO/SLI/error budget 由此普及 | 方法 | ch18 |
| 2019 | 《Team Topologies》（Skelton & Pais）——平台工程運動奠基文本、cognitive load | 方法 | ch18 |
| 2021 | GitHub Copilot technical preview（基於 OpenAI Codex） | 抽象 | ch20 |
| 2022 | GitHub Copilot GA | 抽象 | ch20 |
| 2023–26 | ⚠️ agentic coding 工具興起（Cursor／Claude Code／Copilot agent 等，截至 2026-06）——「自動編程」夢的最新一輪，判斷可能被推翻 | 抽象 | ch20 |

## 怎麼用這張表

這張表不是給你背年份的——書一開頭就說了，軟體史不是「某年某人發明某物」的編年帳。它的用法是當**驗收清單**：把手指蓋住「里程碑」欄以外的部分，對每一跳問自己兩個問題——

1. **這一跳搬走了什麼複雜度？** 它撞的是哪一面牆（人腦裝不下、機器太難說話、大團隊互相踩腳、規模逼著放棄一致性……），用的是抽象還是方法翻越的？
2. **帳單是什麼？** 它把複雜度搬去哪了（搬進編譯器、搬上網路、搬給雲、搬給別人的團隊），這筆帳在什麼情況下會洩漏、回來找你？

講得出這兩件事的那一行，你才算真的懂了它——而不只是記得它發生在哪一年。能對整條時間軸從 1837 講到 2026、每一跳都說清楚「搬走什麼、帳單是什麼」，你就完成了全書的核心驗收：軟體七十年史是一部**複雜度反覆搬家、從未消滅**的歷史（總帳回收見 ch19，最終陳述見 ch21）。

另外提醒：標 ⚠️ 的幾行（Lovelace「第一位程式設計師」、EDVAC 署名爭議、Hopper「第一個編譯器」、Salus 轉述的 Unix 哲學三句版、2023–26 的當下判斷）是「大家最容易記錯／還沒蓋棺」的地方——這些保留條件本身，正是本書要你帶走的東西之一：對流行說法保持歷史縱深的清醒。
