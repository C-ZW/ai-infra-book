# 附錄 B — 人物與術語表

> 從各章實際寫出的內容萃取的速查表，只收書中真正出現、且講過貢獻或意義的人與詞。本書的驗收靠口述——所以這裡每一筆都寫成「一句話講出他/它在解什麼複雜度」的形式：你若能把這張表的任一列用自己的話對另一個工程師講清楚，那一章就算過了。首次出現章以全書 grep 對到的最早章為準（序章 ch01 會先預告幾個全書工具，真正攤開的「主場章」在一句話裡用「（見 chNN）」標出）。

## 人物

| 原文名 | 中譯（書中用法） | 一句話貢獻 | 首次出現章 |
|---|---|---|---|
| Charles Babbage | Babbage | 構思分析機（Analytical Engine, 1837 起），第一個把「通用可程式化機器」當成設計來畫的人——但機器從未完整建成，留下的是設計不是機器。 | ch02 |
| Ada Lovelace | Lovelace | 為分析機寫下含 Bernoulli 數演算法的 Note G（1843）；「第一位程式設計師」是有爭議的後世標籤（Note G 嚴格說更像執行軌跡），本書照 landscape 寫「常被譽為」而非斷言。 | ch02 |
| Alan Turing | 圖靈 | 1936《On Computable Numbers》用圖靈機（一個思想實驗、不是機器）劃出「可計算」的邊界，奠定計算的理論地基。 | ch02 |
| John von Neumann | 馮紐曼 | 1945 EDVAC 報告單獨署名，使「程式與資料同住一個記憶體」的儲存程式概念以他冠名（馮紐曼架構）——但功勞歸屬對 Eckert/Mauchly 有爭議，本書照 landscape 帶出。 | ch02 |
| J. Presper Eckert | Eckert | 與 Mauchly 共同設計 ENIAC（1945–46）；儲存程式概念的早期討論者，是馮紐曼署名爭議裡被蓋過功勞的一方。 | ch02 |
| John Mauchly | Mauchly | ENIAC 的另一位主設計者；與 Eckert 同為儲存程式信用爭議的當事人。 | ch02 |
| Herman Goldstine | Goldstine | 1945 把馮紐曼署名的 EDVAC 報告分發出去的人，這份「形同公開發表」的動作正是命名爭議的引爆點。 | ch02 |
| Maurice Wilkes | Wilkes | 主持 EDSAC（1949），第一台實用的完整儲存程式電腦；其 Initial Orders 把儲存程式從理論變成日常可操作的機器。 | ch02 |
| David Wheeler | Wheeler | EDSAC 的 Initial Orders（1949）作者——史上第一個組譯器系統，讓人用助記符而非二進位寫指令，並奠基副程式（Wheeler Jump）概念。 | ch03 |
| Grace Hopper | Hopper（多用原文） | A-0（1951–52）與 FLOW-MATIC——把「英語化、自動串接副程式」推上路，深刻影響 COBOL；「第一個編譯器」之說以現代定義更像連結載入器，本書照 landscape 校準。 | ch02 |
| John Backus | Backus | 領導 IBM 做出 FORTRAN（1957），第一個廣泛使用的高階語言，賭贏了「機器產生的碼能不能跟手寫一樣快」這場效能↔生產力之爭；後又提出 BNF。 | ch03 |
| John McCarthy | McCarthy | 1958–60 設計 LISP，引入 S-expression、程式即資料（homoiconicity）與 garbage collection——把「記得釋放記憶體」這個複雜度永久搬給 runtime。 | ch04 |
| Steve Russell | Russell | 發現 McCarthy 紙上的 eval 可直接寫成機器碼，做出第一個 LISP 直譯器，令 McCarthy 自己都吃驚——「理論被人手工變成可跑的程式」的經典一幕。 | ch04 |
| Peter Naur | Naur | ALGOL 60 報告的編輯；把 Backus 的記法改良成 Backus–Naur Form（BNF），讓「描述語言語法」本身有了形式工具。 | ch04 |
| C. A. R. Hoare | Hoare（東尼·霍爾） | Hoare logic（1969）用前後條件「證明」程式正確；又自承把 null 引進 ALGOL W（1965）是「十億美元錯誤」——一個圖方便的決定如何變成全球性的複雜度負擔（見 ch08）。 | ch04 |
| Edsger W. Dijkstra | Dijkstra | 反 GOTO（1968，標題是編輯下的）、結構化編程、separation of concerns（1974）；名言「測試只能證明 bug 存在、不能證明不存在」——方法 strand 的紀律源頭（見 ch05）。 | ch01 |
| Niklaus Wirth | Wirth | 身為《CACM》編輯把 Dijkstra 原題改成「Go To Statement Considered Harmful」，意外開創了「…Considered Harmful」這個句型。 | ch05 |
| Corrado Böhm | Böhm | 與 Jacopini 證明結構化定理（1966）：任何程式可只用順序／選擇／迭代三種結構改寫——給了「為什麼不需要 GOTO」的數學底氣。 | ch05 |
| Giuseppe Jacopini | Jacopini | Böhm–Jacopini 結構化定理的共同作者。 | ch05 |
| F. L. Bauer | Bauer | 1968 NATO Garmisch 會議主席；「software engineering」作為會議名是刻意的挑釁式命名，多歸功於他。 | ch05 |
| Brian Randell | Randell | 與 Naur 共同編纂 1968/69 NATO 會議報告，使「software crisis」與這門學科的自覺定形於文獻。 | ch05 |
| David L. Parnas | Parnas | 1972 information hiding 原典：模組該按「藏住哪個會變的設計決策」切，不是照處理流程切——切大程式的判準至今仍被違反。 | ch06 |
| Ken Thompson | Thompson | 與 Ritchie 開創 Unix（1969 起）；把「小工具＋可移植」的工程文化做成一整套作業系統。 | ch06 |
| Dennis Ritchie | Ritchie | C 語言（約 1972）的作者，用高階語言重寫 Unix 核心——可移植性這個賭注讓 Unix 擴散全世界。 | ch06 |
| Doug McIlroy | McIlroy | 推動 pipe 進 Unix（1973）並提出「Make each program do one thing well」——把組合哲學變成你今天 pipeline／微服務的祖宗。 | ch06 |
| Brian Kernighan | Kernighan | 與 Ritchie 合著 K&R《The C Programming Language》（1978），把 C 與 Unix 風格傳遍一整代工程師。 | ch06 |
| Ole-Johan Dahl | Dahl | 與 Nygaard 設計 Simula 67，首個帶 class／object／inheritance／virtual method 的語言——OOP 的概念源頭。 | ch07 |
| Kristen Nygaard | Nygaard | Simula 67 的共同設計者，OOP 血脈的另一位開山者。 | ch07 |
| Alan Kay | Alan Kay | 在 Xerox PARC 造出「object-oriented」一詞；後來強調 OOP 的大想法是 messaging（訊息傳遞）而非 class——一個好點子規模化落地時如何被改形的活標本。 | ch07 |
| Dan Ingalls | Ingalls | Smalltalk 的主要實作者之一，把 Kay 的願景做成能跑的系統。 | ch07 |
| Adele Goldberg | Goldberg | Smalltalk 的共同打造與推廣者（Xerox PARC）。 | ch07 |
| Bjarne Stroustrup | Stroustrup | 「C with Classes」→C++（1983 命名），把 OOP 帶進主流效能語言。 | ch07 |
| James Gosling | Gosling | Java（1995）的主要設計者，以 JVM 兌現「Write Once, Run Anywhere」——把平台差異的複雜度搬進 runtime。 | ch07 |
| Robin Milner | Milner | 1970s 在愛丁堡設計 ML 與 Hindley–Milner 型別推論——「型別檢查器是最普及的形式方法」，讓靜態型別不再囉嗦。 | ch08 |
| J. Roger Hindley | Hindley | 先描述了後來叫 Hindley–Milner 的型別系統，是這個「誰先發明」三方公案的一方。 | ch08 |
| Luis Damas | Damas | 形式化證明 Hindley–Milner 型別推論（Algorithm W），補上三方歸屬的最後一塊。 | ch08 |
| Alonzo Church | Church | 1936 發表 untyped lambda calculus，與圖靈機並列為「可計算」的另一個等價理論根——也是函數式編程的數學祖宗。 | ch09 |
| David Turner | David Turner | 設計 Miranda（1985），惰性純函數語言，是 Haskell 的主要靈感。 | ch09 |
| Herb Sutter | Herb Sutter | 〈The Free Lunch Is Over〉（2005）標誌時脈撞牆、多核心成為必修——讓四十年前 Lisp 就給的「不可變」答案突然變值錢。 | ch09 |
| Fred Brooks | Brooks | 《人月神話》（1975）與《No Silver Bullet》（1986）：Brooks's Law、概念完整性、本質 vs 偶然複雜度——本書反覆動用的手術刀（見 ch10）。 | ch01 |
| Melvin Conway | Conway | Conway's Law（1968 刊 Datamation）：系統結構照抄組織的溝通結構——切錯微服務邊界往往是組織問題偽裝成技術問題（見 ch10、ch17）。 | ch01 |
| Winston W. Royce | Royce | 1970 論文常被當「瀑布之父」，實際上他把純線性圖當作有缺陷的反例、主張迭代——本書最重要的「人人都讀反了」案例（見 ch11）。 | ch02 |
| Watts Humphrey | Humphrey | 在 SEI 推動 CMM／CMMI，把「過程成熟度」變成可稽核的重量級流程模型。 | ch11 |
| Kent Beck | Kent Beck | Extreme Programming（XP）與 TDD（red-green-refactor）的推手；把敏捷「擁抱變化」變成可操作的技術紀律。 | ch12 |
| Ken Schwaber | Schwaber | 與 Sutherland 正式發表 Scrum（OOPSLA 1995），把短迭代框架化。 | ch12 |
| Jeff Sutherland | Sutherland | Scrum 的共同創立者。 | ch12 |
| William Opdyke | Opdyke | 重構（refactoring）的學術源頭（1992 博論），先於 Fowler 把它系統化。 | ch12 |
| Grady Booch | Booch | 一般歸於他造了「Continuous Integration」一詞（後由 XP 發揚）。 | ch12 |
| Martin Fowler | Martin Fowler | 《Refactoring》（1999）、微服務定調文（與 Lewis, 2014）等的作者；本書多處引他的考據（含 Phil Karlton 名言的歸屬整理）。 | ch01 |
| E. F. Codd | Codd | 1970 關聯模型原典：用宣告式查詢與資料獨立性，把「怎麼存取資料」的複雜度整包搬給資料庫引擎（見 ch13）。 | ch01 |
| Donald Chamberlin | Chamberlin | 與 Boyce 設計 SEQUEL（1974，後改名 SQL），把關聯代數變成人能讀寫的查詢語言。 | ch13 |
| Raymond Boyce | Boyce | SEQUEL/SQL 的共同設計者（1974 年英年早逝）。 | ch13 |
| Jim Gray | Jim Gray | 1970s 末刻畫交易性質、命名 atomicity/consistency/durability（尚無 isolation），是 ACID 的概念奠基者。 | ch13 |
| Theo Härder | Härder | 與 Reuter 在 1983 造出 ACID 縮寫，把 Gray 的概念補上 isolation 湊成四件套。 | ch13 |
| Andreas Reuter | Reuter | ACID 縮寫的共同提出者（1983）。 | ch13 |
| Eric Brewer | Brewer | CAP 猜想（2000 PODC）：規模逼你在一致性與可用性之間選邊——鐘擺從「引擎包辦一切」擺回「應用自己扛一致性」。 | ch13 |
| Seth Gilbert | Gilbert | 與 Lynch 在 2002 把 CAP 從猜想證明成定理。 | ch13 |
| Nancy Lynch | Lynch | CAP 定理的共同證明者（2002）。 | ch13 |
| Eric Evans | Eric Evans | 在 2009 meetup 提議用「NoSQL」一詞稱呼當時的分散式資料庫運動（與 1998 Strozzi 那個 NoSQL 不同所指）。 | ch13 |
| Richard Stallman | Stallman | GNU（1983）、FSF（1985）、copyleft：用授權當法律駭客，把「free as in freedom（自由而非免費）」這個所有權主張寫進軟體。 | ch14 |
| Linus Torvalds | Torvalds | Linux 核心（1991）證明開源協作能成；又在 2005 極短時間內寫出 Git，用內容定址與 DAG 重組「上千人併行改一個 codebase」的協作複雜度。 | ch14 |
| Eric S. Raymond | Raymond | 《The Cathedral and the Bazaar》（1997）把 Linux 現象理論化——回答「這種看似混亂的市集式開發為什麼行得通」（見 ch14）。 | ch06 |
| Christine Peterson | Peterson | 1998 造出「open source」一詞，配合 Netscape 開源的策略命名。 | ch14 |
| Bruce Perens | Perens | 與 Raymond 等共同創立 OSI，把開源從理念變成有定義、有招牌的運動。 | ch14 |
| Andrew Tridgell | Tridgell | 反向工程 BitKeeper 的事件觸發了授權爭議，間接逼出 Git 的誕生。 | ch14 |
| Vint Cerf | Cerf | 與 Kahn 的 1974 論文奠定 TCP/IP：讓底層網路保持笨、把互連的智慧放到端點——你「在應用層處理可靠性」的直覺根在這裡。 | ch15 |
| Bob Kahn | Kahn | TCP/IP 的共同作者（1974）。 | ch15 |
| Tim Berners-Lee | Berners-Lee | 在 CERN 提出 WWW（1989 提案／1991 公開），用無專利的 HTTP/HTML/URL 三件套，讓開放標準擊敗圍牆花園、長成史上最大應用平台。 | ch15 |
| Tim O'Reilly | O'Reilly | 推廣「Web 2.0」（2004 構思／2005 定義文），標記瀏覽器從文件檢視器變成應用平台。 | ch15 |
| Jesse James Garrett | Garrett | 2005 造「AJAX」一詞，給「網頁不重整就更新」這個體驗一個名字。 | ch15 |
| Jeff Bezos | Bezos | 主導 Amazon 把內部基礎設施對外開放成 API（AWS, 2006），把「擁有並維運機房」的巨大複雜度變成一行 API 呼叫。 | ch16 |
| Solomon Hykes | Hykes | 2013 PyCon 五分鐘 lightning talk 展示 Docker，把「在我機器上能跑」的環境複雜度封進不可變 image（回收 ch02 程式即資料）。 | ch17 |
| James Lewis | Lewis | 與 Fowler 的 2014 定調文〈Microservices〉，把一個已在發生的實踐命名定調（注意：是命名不是發明）。 | ch17 |
| Adrian Cockcroft | Cockcroft | Netflix 早期微服務實踐的代表人物，為撐住串流爆量很早走上細粒度服務。 | ch17 |
| Patrick Debois | Debois | 2009 首屆 DevOpsDays（Ghent）的發起者，給「彌合開發與維運之牆」這件事一個名字：DevOps。 | ch18 |
| Jez Humble | Humble | 與 Farley 合著《Continuous Delivery》（2010），把自動化部署流水線系統化。 | ch18 |
| David Farley | Farley | 《Continuous Delivery》共同作者（2010）。 | ch18 |
| Gene Kim | Gene Kim | 《The Phoenix Project》（2013）作者之一，用小說把 DevOps 的價值講進產業常識。 | ch18 |
| Ben Treynor Sloss | Treynor | 約 2003 在 Google 創立 SRE：「叫軟體工程師去做維運會得到的東西」；error budget／SLO 由 2016 SRE book 普及。 | ch18 |
| Matthew Skelton | Skelton | 與 Pais 合著《Team Topologies》（2019），平台工程運動的奠基文本（cognitive load、stream-aligned/platform team）。 | ch18 |
| Manuel Pais | Pais | 《Team Topologies》共同作者（2019）。 | ch18 |
| Donald Knuth | Knuth | 「過早最佳化是萬惡之源」（1974）——但完整脈絡是「97% 的時候別過早最佳化，但要抓住關鍵 3%」，常被斷章取義成「不要優化」（見 ch19）。 | ch01 |
| Phil Karlton | Karlton | 一般歸於他的名言「CS 兩大難事：cache invalidation 與命名」——本書用它示範「連人人會背的話，認真考據都站不太穩」的態度。 | ch01 |
| Joel Spolsky | Spolsky | 〈The Law of Leaky Abstractions〉（2002）：「所有非平凡的抽象在某種程度上都會洩漏」——複雜度守恆的必然結果（見 ch19）。 | ch01 |
| Richard P. Gabriel | Gabriel | 「Worse is Better」（1989–91）：把「夠用、簡單、先出貨」為何常勝過「正確、完整、優雅」寫成一條反覆應驗的觀察。 | ch19 |

## 術語

| English | 中文 | 一句話定義（它在解什麼複雜度） | 首次出現章 |
|---|---|---|---|
| conservation of complexity | 複雜度守恆 | 全書核心主張：抽象不消滅複雜度，只把它搬家（搬給編譯器、runtime、雲、別人的團隊），帳單在抽象洩漏時回來找你。 | ch01 |
| two strands（abstraction / method） | 兩條 strand（抽象／方法） | 「我們用什麼蓋（抽象）」與「我們怎麼蓋（方法）」是同一場對抗複雜度戰爭的兩面，全程互相觸發。 | ch01 |
| pendulum | 鐘擺 | 效能↔生產力、集中↔分散、單體↔分散式、手工↔自動——同一組張力反覆擺盪，每次回擺帶著上次的教訓。 | ch01 |
| essential complexity | 本質複雜度 | 問題本身固有、任何工具都砍不掉的困難（搞清楚到底要建什麼、跨系統一致性）——Brooks 的手術刀，ch10 正式定義。 | ch10 |
| accidental complexity | 偶然複雜度 | 不是問題本身、而是我們的工具與做法附帶製造的負擔（樣板、語言囉嗦）——工具能砍的只有這一塊。 | ch10 |
| leaky abstraction | 抽象洩漏 | 抽象在邊緣總會漏出它本想藏住的底層細節（N+1、冷啟動、TCP 重傳）——這不是 bug，是抽象的稅（見 ch19）。 | ch01 |
| stored-program | 儲存程式 | 把程式與資料放進同一個記憶體，讓程式變成「可被程式操作的資料」——編譯器、直譯器、容器 image 後來的一切都站在這個前提上（見 ch02）。 | ch01 |
| Turing machine | 圖靈機 | 一個思想實驗（不是機器），用來劃出「什麼可被計算」的理論邊界。 | ch02 |
| assembler | 組譯器 | 用助記符取代手寫二進位／手算位址，第一次「不直接對機器說話」——把記位址這個負擔外包出去。 | ch03 |
| automatic programming | 自動編程 | 從 FORTRAN（1957）到 AI agent（2026）反覆出現的夢：讓寫程式更接近說人話；每代都兌現了一部分抽象、又都高估了能消滅本質複雜度（見 ch20）。 | ch03 |
| garbage collection | 垃圾回收 | 自動回收不再使用的記憶體，把「記得 free」這個複雜度永久搬給 runtime（帳單：GC pause）。 | ch01 |
| homoiconicity（code as data） | 程式即資料 | 程式用與資料相同的結構表示，於是程式能操作程式（eval、codegen、巨集）——LISP 帶來的世界觀。 | ch04 |
| BNF（Backus–Naur Form） | 巴科斯–諾爾範式 | 一套形式記法，把「描述程式語言的語法」這件事本身變得可精確定義。 | ch04 |
| structured programming | 結構化編程 | 只用順序／選擇／迭代取代滿天飛的 GOTO，讓靜態程式文本與動態執行過程的差距縮到人腦追得上——方法 strand 第一次登場（見 ch05）。 | ch01 |
| software crisis | 軟體危機 | 1968 NATO 會議喊出：大型系統大到一個人腦裝不下、超支延遲不可靠，逼出「software engineering」這門學科的自覺。 | ch05 |
| information hiding | 資訊隱藏 | 模組該按「它對外藏住哪個會變的設計決策」來切，而不是照處理步驟切——讓需求變動時要改的範圍最小。 | ch06 |
| separation of concerns | 關注點分離 | Dijkstra（1974）造詞：把不同面向的問題分開各自處理，別讓它們在腦子裡糾纏。 | ch06 |
| Unix philosophy | Unix 哲學 | 寫只做一件事並做好的小程式、讓它們用 pipe 協作——你今天 pipeline／微服務的哲學祖宗。 | ch06 |
| object-oriented | 物件導向 | 把資料與行為綁在一起（封裝＋多型），收攏「資料和操作散落各處」的複雜度——封裝是資訊隱藏的另一條實作路線（見 ch07）。 | ch07 |
| messaging | 訊息傳遞 | Kay 說 OOP 的大想法不是 class 而是 messaging：自治單元之間傳訊（像細胞）——actor model／微服務比 class 繼承更接近這個原意。 | ch07 |
| inheritance | 繼承 | 沿類別樹共享行為；落地時被當招牌，卻製造「行為藏在哪一層」的垂直離散，後來才有「組合優於繼承」的反省。 | ch07 |
| Hoare logic | 霍爾邏輯 | 用前後條件（P{Q}R）「證明」程式正確的理想——靜態型別與形式驗證同一種衝動的最嚴格那一端。 | ch04 |
| null reference | 空引用 | Hoare 1965 為圖方便加入、四十年後自稱「十億美元錯誤」——一個圖方便的設計決策變成全球性的複雜度負擔。 | ch08 |
| type inference | 型別推論 | 編譯器從你怎麼用一個值自己推出型別，省掉手寫型別宣告——讓靜態型別的保護不必付「囉嗦」的代價。 | ch08 |
| Hindley–Milner | Hindley–Milner（型別系統） | 第一個有多型型別推論的實用系統——TypeScript/Rust/現代 C++ 型別推論的共同祖宗。 | ch08 |
| formal methods | 形式方法 | 在執行前用數學「證明」排除一整類錯誤；因成本高留在航太/晶片/協定，但型別檢查器是它最普及的輕量版。 | ch08 |
| lambda calculus | Lambda 演算 | Church 1936 的計算理論根，與圖靈機等價——函數式編程的數學祖宗。 | ch09 |
| pure function | 純函數 | 同輸入必得同輸出、無副作用——可重試、可平行、可推理（你的冪等消費者逼近的就是它）。 | ch09 |
| immutability | 不可變 | 資料一旦建立不再改動，天生對並行友善（沒有共享可變狀態就沒有 race condition）——多核心時代讓這個老答案變值錢。 | ch09 |
| The Free Lunch Is Over | 免費的午餐結束了 | Sutter 2005：時脈不再自動變快、平行化變必修——「老答案（不可變）等到問題出現才被需要」的範例。 | ch09 |
| Brooks's Law | Brooks 定律 | 「加人到一個遲到的軟體專案會讓它更遲到」——溝通路徑 O(n²)＋新人 ramp-up，是數學不是管理失誤。 | ch10 |
| conceptual integrity | 概念完整性 | 一致的設計願景比堆功能更重要；沒有它，codebase 會分裂——複雜度的人性面。 | ch10 |
| No Silver Bullet | 沒有銀彈 | Brooks 1986：工具只能砍偶然複雜度、砍不掉本質複雜度——所以「沒有銀彈」是面對每次革命承諾的合理預設懷疑。 | ch01 |
| Conway's Law | Conway 定律 | 系統結構照抄組織的溝通結構——微服務本質是把組織結構固化成系統結構（見 ch10、ch17）。 | ch10 |
| data independence | 資料獨立性 | 你說要什麼（宣告式），引擎決定怎麼拿——所以你能換 index 而不改應用程式碼，把存取路徑的複雜度搬給查詢最佳化器。 | ch13 |
| declarative | 宣告式 | 描述「要什麼結果」而非「怎麼一步步做」，把執行細節的複雜度交給引擎（SQL、K8s 調度同一個衝動）。 | ch13 |
| relational model | 關聯模型 | Codd 1970：用關聯代數與資料獨立性把「怎麼存取資料」整包搬給引擎——抽象的一次大勝利。 | ch13 |
| ACID | ACID | 把交易的複雜度標準化成原子性／一致性／隔離性／持久性四件套——你天天在跟它的帳單打交道。 | ch13 |
| CAP theorem | CAP 定理 | 分散式系統在一致性與可用性之間必須取捨——規模逼你放棄強一致、自己在應用層扛一致性。 | ch13 |
| NoSQL | NoSQL | 2009 起的分散式資料庫運動，為規模而放棄關聯/強一致——鐘擺從「引擎包辦」擺回「應用自理」。 | ch13 |
| free software | 自由軟體 | Stallman 的理念：free as in freedom（自由而非免費）——把軟體的所有權主張寫進授權。 | ch14 |
| copyleft | copyleft | 用著作權法反向操作（GPL），強制衍生作品也必須自由——把「保持開放」變成可執行的法律條款。 | ch14 |
| open source | 開源 | 1998 造詞，務實版的自由軟體（強調協作效益而非道德）——與 Stallman 的理想派分歧不只是用詞。 | ch14 |
| distributed version control | 分散式版本控制 | Git（2005）把整個版本歷史搬到每個人本機，用便宜分支與 merge 重組「上千人併行改一個 codebase」的協作複雜度。 | ch14 |
| TCP/IP | TCP/IP | 讓底層各種網路保持笨、把互連與可靠性的智慧放到端點——你「在應用層處理可靠性」的根。 | ch15 |
| World Wide Web | 全球資訊網 | 無專利的 HTTP/HTML/URL 三件套，讓開放標準擊敗圍牆花園、長成史上最大應用平台。 | ch15 |
| open standard | 開放標準 | 無人可獨佔、任何人可實作的規格——Web 贏過封閉線上服務的決定性原因（複雜度/控制權如何分配）。 | ch15 |
| virtualization | 虛擬化 | 一台機器假裝成多台，把硬體與工作負載解耦——雲「按片租用」的技術前提。 | ch16 |
| cloud / IaaS-PaaS-SaaS | 雲／三層服務 | 把「買機器、進機房、接網路」的複雜度整包外包、按用量計費；分層各把「你不用管什麼」往上推一層。 | ch16 |
| Infrastructure as Code | 基礎設施即程式碼 | 把基礎設施從手動點擊變成版本控制下的程式碼（可重現、可審查、可回溯）——維運也納入軟體工程（見 ch16）。 | ch01 |
| microservices | 微服務 | 按業務能力切、獨立部署、團隊自治，解「大團隊在單體上互相踩腳」的複雜度；代價是把複雜度從程式內搬到網路上（見 ch17）。 | ch01 |
| container | 容器 | 把執行環境連同程式打包成不可變 image，一次搬走「在我機器上能跑」的環境差異複雜度（回收 ch02 程式即資料；見 ch17）。 | ch01 |
| Kubernetes | Kubernetes | 分散式系統的作業系統，用宣告式調度管理容器（回收 ch13 宣告式）——治微服務的編排複雜度。 | ch16 |
| DevOps | DevOps | 彌合「開發丟給維運」那道牆，把開發與維運融合、自動化部署（敏捷往維運的延伸；見 ch18）。 | ch01 |
| SRE | SRE | 用寫軟體的方法做維運（自動化、消除重複勞動），把可靠度從信仰變成可量化工程（見 ch18）。 | ch01 |
| error budget | 錯誤預算 | 「允許的不可靠額度」——把開發（要快）與維運（要穩）的永恆衝突，從立場之爭變成一個共享的數字。 | ch18 |
| SLO / SLI | 服務等級目標／指標 | 把「多可靠才夠」變成可談判的數字，讓可靠度的本質複雜度能被工程紀律馴服。 | ch18 |
| platform engineering | 平台工程 | 對「每個團隊都要懂全套微服務維運」的複雜度爆炸的回應，把維運複雜度再搬到一個內部平台抽象後面（鐘擺：又一次集中化）。 | ch18 |
| Law of Leaky Abstractions | 抽象洩漏定律 | Joel Spolsky 2002：「所有非平凡的抽象在某種程度上都會洩漏」——複雜度守恆的必然推論（見 ch19）。 | ch19 |
| premature optimization | 過早最佳化 | Knuth 1974 名言的完整脈絡：97% 的時候別過早最佳化、但要抓住關鍵 3%——常被斷章成「不要優化」。 | ch01 |
| Worse is Better | 「夠用即是好」 | Gabriel 1989–91：簡單、夠用、先出貨，常勝過正確、完整、優雅——一條反覆應驗的工程觀察。 | ch19 |
| agentic coding | 代理式編程 | 截至 2026-06，AI 寫程式從「行內補全」轉向「跨檔自主 agent」；用 Brooks 手術刀看，它砍的多是偶然複雜度、本質複雜度砍不掉（見 ch20）。 | ch20 |
