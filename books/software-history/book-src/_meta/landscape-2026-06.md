# 事實基準表（landscape）—《軟體發展史》

> **本檔性質**：內部事實基準（非書內容）。掃描日期 **2026-06-13**。
> **使用契約**：本檔是 21 章作者引用日期、人名、引文、「首次出現」主張的**唯一真相來源**。寫作時若與記憶衝突，以本檔為準；本檔沒有的事實，請先查證再補進來，不要憑記憶寫。
> **標記約定**：
> - 🟢 = 兩個以上獨立來源確認，可放心使用。
> - ⚠️ = 有爭議／傳說性／單一來源／統計可疑。**作者引用時必須照本檔的措辭與保留條件寫，不可斷言。**
> - 📌 = 「大眾記憶錯誤」熱點，作者最容易寫錯，務必照本檔。
>
> **散文用繁體中文（台灣用語）；人名、書名、論文名、引文、URL 保留原文。**

---

## A. 史前與儲存程式（ch02）

| 事實 | 年份 | 歸屬 | 常見誤解／注意 | 來源 |
|---|---|---|---|---|
| 🟢 Babbage 構思 Difference Engine | 1821（構想）；政府資助計畫 1823 起 | Charles Babbage | — | https://www.computerhistory.org/babbage/engines |
| 🟢 Analytical Engine 首次提出設計 | 1837 起描述；研究延續到他過世（1871） | Charles Babbage | 從未完整建成；是「設計」不是「機器」 | https://en.wikipedia.org/wiki/Analytical_engine |
| 📌⚠️ Ada Lovelace「Note G／Bernoulli 數演算法」 | 1843（隨 Menabrea 1842 法文講稿英譯所附 Notes A–G 出版） | Ada Lovelace（譯註者）；Babbage 自承 Bernoulli 數部分的代數推演是他先做以省她麻煩 | **「第一位程式設計師」是有爭議的後世標籤**。Note G 嚴格說更像「執行軌跡（trace）」而非現代意義的「程式」；「to program」一詞是數十年後才有，套用在她身上是 anachronism。作者應寫成「常被譽為／一般認為」而非斷言。 | https://en.wikipedia.org/wiki/Note_G ；https://twobithistory.org/2018/08/18/ada-lovelace-note-g.html ；https://arxiv.org/pdf/2402.00749（"Was Ada Lovelace Actually the First Programmer?" 的回應論文） |
| 📌 Turing「On Computable Numbers, with an Application to the Entscheidungsproblem」 | 投稿 1936-05-28；分兩部刊於 *Proc. London Math. Soc.* s2-42（1936 年底印行），**正式卷期標 1937**；1937-04 另有更正 | Alan Turing | 引用時寫「1936」最常見且可接受（投稿與主要發表都在 1936）；若要精確可註「卷期標 1937」。論文題目務必完整，不要寫成「Turing machine 論文」。 | https://www.historyofinformation.com/detail.php?id=619 ；https://londmathsoc.onlinelibrary.wiley.com/doi/abs/10.1112/plms/s2-42.1.230 |
| 🟢 Church–Turing thesis | 1930s | Alonzo Church（lambda calculus）＋ Alan Turing（machine），兩套等價模型 | thesis 是「論題／猜想」非定理；名稱是後人合稱 | https://plato.stanford.edu/entries/church/ |
| 🟢 ENIAC 首次運轉解題 | 1945-12-10（Los Alamos 題目）；1946-02-15 公開揭露 | J. Presper Eckert ＆ John Mauchly，Moore School, U. Penn | ENIAC **不是儲存程式機**；以插線板（plugboard）＋纜線＋3 個 portable function table、上千個 10 段開關「設定」程式 | https://www.aps.org/apsnews/2022/11/eniac-first-top-secret-program ；https://www.columbia.edu/cu/computinghistory/eniac.html |
| 📌 ENIAC Six（女性程式設計師） | 1945–46 | Kathleen McNulty (Mauchly Antonelli)、Frances "Betty" Snyder Holberton、Marlyn Wescoff Meltzer、Frances Bilas Spence、Ruth Lichterman Teitelbaum、Jean Jennings Bartik | 1946 公開時未被介紹，長年被忽略；六人名字務必照此 | https://eniacprogrammers.org/documentary-info/ ；https://spectrum.ieee.org/the-women-behind-eniac |
| 📌⚠️ 「First Draft of a Report on the EDVAC」 | 1945-06-30 由 Herman Goldstine 分發（101 頁、未完成稿） | 文件單獨署名 **John von Neumann**——這正是「von Neumann architecture」命名爭議的根源 | **信用爭議**：Eckert/Mauchly 主張儲存程式概念基本上是他們的（早於 von Neumann 介入約 8 個月已討論）；單獨署名讓功勞集中於 von Neumann，且形同「公開發表」，破壞了他們的專利布局。作者談 von Neumann 架構必須帶這個爭議。 | https://en.wikipedia.org/wiki/First_Draft_of_a_Report_on_the_EDVAC |
| 🟢 Manchester Baby（SSEM）跑出第一支程式 | 1948-06-21 | F. C. Williams、Tom Kilburn、Geoff Tootill（Manchester） | **世界第一台運轉的電子儲存程式電腦**（實驗性小機） | https://en.wikipedia.org/wiki/Manchester_Baby ；https://www.computinghistory.org.uk/det/6013/ |
| 🟢 EDSAC 運轉 | 1949-05-06 | Maurice Wilkes（Cambridge） | 第一台「實用的」完整儲存程式電腦（Baby 是實驗機） | https://en.wikipedia.org/wiki/EDSAC |

---

## B. 第一層抽象：組語與編譯器（ch03）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 EDSAC「Initial Orders」——史上第一個組譯器系統 | 1949-05 | David Wheeler（Wilkes 的研究生） | 介於 bootstrap loader 與 assembly routine 之間；讓指令用助記符而非寫二進位，僅 31 字。**「assembler」一詞、組語概念由此奠基。** Wheeler 也奠基了 subroutine 概念（Wheeler Jump）。 | https://en.wikipedia.org/wiki/EDSAC ；https://hopl.info/showlanguage.prx?exp=3411 |
| 🟢 Wilkes/Wheeler/Gill《The Preparation of Programs for an Electronic Digital Computer》 | 1951 | Wilkes, Wheeler, Gill | 第一本程式設計教科書，含 subroutine library | https://cacm.acm.org/opinion/in-praise-of-wilkes-wheeler-and-gill/ |
| 📌⚠️ Grace Hopper「A-0 system」 | 1951–52，原為 UNIVAC I | Grace Murray Hopper | **「第一個編譯器」需加保留**：A-0 以現代定義更像 loader/linker（把編號的副程式序列串接載入），不是把高階語言翻成機器碼的現代 compiler。作者寫「常被稱為第一個編譯器，但以現代定義更接近連結載入器」。 | https://en.wikipedia.org/wiki/A-0_System ；https://cacm.acm.org/blogcacm/did-grace-hopper-create-the-first-compiler/ |
| 📌⚠️ 「第一隻電腦 bug」蛾 | 1947-09-09，Harvard Mark II | 工程團隊（含 William "Bill" Burke 等）；Hopper 在場並推廣此說 | **傳說 vs 事實**：日誌寫 "First actual case of bug being found"，本身就是在玩「bug」既有的工程俚語梗——**不是** bug/debug 詞源的起點（這兩詞此前已存在）。日誌可能不是 Hopper 本人所記。那是蛾（Lepidoptera），嚴格說不是昆蟲學意義的 "bug"。作者勿寫「Hopper 發明 debug 一詞」。 | https://americanhistory.si.edu/collections/object/nmah_334663 ；https://daily.jstor.org/the-bug-in-the-computer-bug-story/ |
| 🟢 FLOW-MATIC（原名 B-0） | 1955–59 | Grace Hopper（UNIVAC） | 第一個「英語化」資料處理編譯語言；**直接影響 COBOL** | https://en.wikipedia.org/wiki/Grace_Hopper |

---

## C. 高階語言誕生（ch03–ch04）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 FORTRAN 計畫啟動 | 1954（語言規格約 1954 末完成；compiler 1955–56 寫成測試） | John Backus 領導，IBM（為 IBM 704） | 賣點是「automatic programming」；當時普遍懷疑自動產生的碼跑不過手寫機器碼（效能 vs 生產力之爭） | https://www.ibm.com/history/john-backus |
| 🟢 FORTRAN 出貨 | 1957-04（首批給 IBM 704 用戶） | 同上 | **第一個廣泛使用的高階語言**。Backus 等人寫「The history of FORTRAN I, II, and III」為一手史料 | https://www.historyofinformation.com/detail.php?id=755 |
| 🟢 ALGOL 60 Report | 1960（巴黎會議 1960-01） | 委員會；**Peter Naur 任編輯** | block structure；BNF 主要由 John Backus 提出、Naur 為 ALGOL 60 改良（故名 **Backus–Naur Form**） | https://en.wikipedia.org/wiki/ALGOL_60 |
| 📌 Hoare 名言「a language so far ahead of its time…」 | 引文約 1973；最常見出處是 **1980 圖靈獎演說「The Emperor's Old Clothes」**（刊 *CACM* 24(2), 1981） | C. A. R. Hoare 論 ALGOL 60 | **精確措辭**：「Here is a language so far ahead of its time that it was not only an improvement on its predecessors but also on nearly all its successors.」作者引用務必照此句、別自行縮寫。 | https://www.cs.ru.ac.za/compilerbook/Modula2Standardisation/hoare.htm ；https://dl.acm.org/doi/10.1145/1283920.1283936 |
| 🟢 LISP 構思 / 論文 | 構思 1958（MIT）；論文「Recursive Functions of Symbolic Expressions and Their Computation by Machine, Part I」刊 *CACM* 1960 | John McCarthy | 引入 S-expression、**garbage collection**（GC 概念由此論文首次描述）、code-as-data／homoiconicity；AI lab 脈絡 | http://jmc.stanford.edu/articles/lisp/lisp.pdf ；https://en.wikipedia.org/wiki/Lisp_(programming_language) |
| 🟢 eval 被手工編成機器碼 | 約 1958–60 | **Steve Russell**（研究生）發現 McCarthy 紙上的 eval 可直接寫成 IBM 704 機器碼，做出第一個 LISP interpreter，令 McCarthy 驚訝 | 故事為真，常被引用 | https://en.wikipedia.org/wiki/Lisp_(programming_language) |
| 🟢 COBOL | 規格 1959 公布；1960 正式 | CODASYL；Grace Hopper 經 FLOW-MATIC 深刻影響（非「唯一作者」） | 為商業設計、強調可讀性／英語化；長壽 | https://en.wikipedia.org/wiki/Grace_Hopper |
| ⚠️ COBOL 至今仍大量運行（統計） | Reuters 估計常被引：2015/2017 **約 2,200 億行** COBOL、跑全球 43% 銀行系統、95% ATM | Reuters（被無限轉述） | **所有 LOC／使用量數字都標 ⚠️**：來源單一且難獨立查證；更近期出現「800 億行以上」「每日 $3 兆交易」等更誇張、更不可靠版本。作者只能寫「據（單一來源）估計／一說」，絕不可斷言確切數字。 | https://spectrum.ieee.org/cobol-programming-shelf-life ；https://www.thestack.technology/cobol-in-daily-use/ |

---

## D. 軟體危機與結構化編程（ch05）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 NATO Software Engineering Conference | **1968 Garmisch（德）**、**1969 Rome（義）** | 主席 F. L. Bauer；報告編者 Peter Naur ＆ Brian Randell | 「software crisis」一詞與「software engineering」學科認同由此確立；以「software engineering」為會議名是刻意挑釁（多歸功 Bauer） | https://en.wikipedia.org/wiki/NATO_Software_Engineering_Conferences ；https://www.scrummanager.com/files/nato1968e.pdf |
| 📌 Dijkstra「Go To Statement Considered Harmful」 | *CACM* 1968-03 | E. W. Dijkstra | **標題「…Considered Harmful」是編輯 Niklaus Wirth 改的**，Dijkstra 原投稿題為「A Case Against the Goto Statement」；Wirth 為加速刊登改成 letter 並換了標題。作者談「Considered Harmful 句型」起源時務必點明這點。 | https://en.wikipedia.org/wiki/Considered_harmful ；https://www.david.tribble.com/text/goto.html |
| 🟢 Böhm–Jacopini 定理（structured program theorem） | 1966 | Corrado Böhm ＆ Giuseppe Jacopini | 任何程式可用 sequence／selection／iteration 三結構改寫；Dijkstra 自己引用過此論文 | https://en.wikipedia.org/wiki/Structured_program_theorem |
| 🟢 Dijkstra「Notes on Structured Programming」 | 1970（EWD249） | E. W. Dijkstra | — | https://en.wikiquote.org/wiki/Edsger_W._Dijkstra |
| 🟢 名言「Program testing can be used to show the presence of bugs, but never to show their absence!」 | 最早見 **1969 Rome NATO 報告**；亦見 1970 EWD249 第 3 節 | E. W. Dijkstra | **精確措辭如上**。常被簡寫成「Testing shows the presence, not the absence, of bugs」——這是後世通俗化版本，作者若要嚴謹應用原句並註出處。 | https://en.wikiquote.org/wiki/Edsger_W._Dijkstra |
| ⚠️ 名言「Simplicity is prerequisite for reliability」 | 出自 **EWD498「How do we tell truths that might hurt?」（1975）** | E. W. Dijkstra | 措辭單純、出處可定位，但屬格言；標 ⚠️ 是因網路常張冠李戴年份，作者引用請註 EWD498 / 1975。 | https://en.wikiquote.org/wiki/Edsger_W._Dijkstra |

---

## E. 模組化、資訊隱藏、Unix（ch06）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 Parnas「On the Criteria To Be Used in Decomposing Systems into Modules」 | *CACM* 1972-12 | David L. Parnas | **information hiding** 原典；模組以「它對外隱藏哪個設計決策」來切分 | https://dl.acm.org/doi/10.1145/361598.361623 |
| 🟢 「separation of concerns」一詞 | EWD447「On the Role of Scientific Thought」**1974** | **Dijkstra 首創此詞** | 作者要把「關注點分離」歸給 Dijkstra/1974 而非泛泛 | https://www.cs.utexas.edu/~EWD/transcriptions/EWD04xx/EWD447.html |
| 🟢 Unix 開發起點 | 1969 起；首份內部手冊 1971-11；對外發表 1973-10 | Ken Thompson、Dennis Ritchie（及 Brian Kernighan、Doug McIlroy、Joe Ossanna），Bell Labs | — | https://en.wikipedia.org/wiki/Unix |
| 🟢 C 語言 | 原始版約 1972（Ritchie）；1973 用 C 重寫大部分 Unix 核心 | Dennis Ritchie | — | https://amturing.acm.org/award_winners/thompson_4588371.cfm |
| 🟢 Pipes | 概念 1973 由 McIlroy 推動進 Unix | Doug McIlroy（點子）；Thompson 實作 | — | https://en.wikipedia.org/wiki/Unix |
| 📌⚠️ Unix 哲學「do one thing and do it well」 | McIlroy 等 **1978** 在 *Bell System Technical Journal*（Unix Time-Sharing System: Foreword）列出原則，原文是「**Make each program do one thing well.**」 | Doug McIlroy（原則）；E. N. Pinson、B. A. Tague 共同署名該 Foreword | **常見誤引**：流傳的「Write programs that do one thing and do it well. Write programs to work together. Write programs to handle text streams…」這個整齊三句版本，是 **Peter H. Salus 在《A Quarter-Century of Unix》(1994)** 歸納轉述的，**不是 McIlroy 1978 的逐字原文**。作者若要逐字引用，請用 1978 原句「Make each program do one thing well」，或註明 Salus 1994 為轉述出處。 | https://en.wikipedia.org/wiki/Unix_philosophy ；https://en.wikiquote.org/wiki/Doug_McIlroy |
| 🟢 K&R《The C Programming Language》 | 1978（第 1 版） | Brian Kernighan ＆ Dennis Ritchie | — | https://en.wikipedia.org/wiki/The_C_Programming_Language |

---

## F. 物件導向（ch07）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 Simula I / Simula 67 | Simula I 1960s 初；**Simula 67** 1967 | Ole-Johan Dahl ＆ Kristen Nygaard（Norwegian Computing Center, Oslo） | **首個帶 class／object／inheritance／virtual method 的語言**；OOP 概念源頭；二人獲 2001 圖靈獎 | https://en.wikipedia.org/wiki/Simula ；https://awards.acm.org/award_winners/nygaard_5916220 |
| 🟢 Smalltalk | Smalltalk-72、-76、**-80**；Xerox PARC，1970s | Alan Kay、Dan Ingalls、Adele Goldberg | Alan Kay 創「object-oriented」一詞 | https://en.wikipedia.org/wiki/Smalltalk |
| 📌⚠️ Kay「OOP 的大想法是 messaging」 | 約 **1998**（email／後續訪談廣傳） | Alan Kay | **精確措辭**：「I'm sorry that I long ago coined the term 'objects' for this topic because it gets many people to focus on the lesser idea. The big idea is 'messaging'.」標 ⚠️ 因確切原始出處（哪封信／哪場訪談）細節版本不一；作者引用照此句並寫「Kay 後來表示」。另 OOPSLA 1997 他說過「I made up the term object-oriented, and I can tell you I did not have C++ in mind.」 | http://lists.squeakfoundation.org/pipermail/squeak-dev/1998-October/017019.html（squeak-dev 1998 email，廣被引為原始出處）；https://www.purl.org/stefan_ram/pub/doc_kay_oop_en（常被引的整理）|
| 🟢 C++ | 「C with Classes」1979 起；1983 改名 **C++** | Bjarne Stroustrup（AT&T Bell Labs） | — | https://www.stroustrup.com/hopl2.pdf |
| 🟢 Java | 1995 釋出 Java 1.0 | James Gosling，Sun Microsystems | 口號 **「Write Once, Run Anywhere」（WORA）** | https://en.wikipedia.org/wiki/Java_(programming_language) |

> 註：上方 Kay 引文的「原始 email」URL 為社群普遍引用之來源，但**單一來源**性質明顯，故標 ⚠️；引文文字本身在多處轉述一致。

---

## G. 型別、正確性、形式方法（ch08）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 Hoare logic：「An Axiomatic Basis for Computer Programming」 | *CACM* 1969（vol.12, pp.576–580） | C. A. R. Hoare | 引入 P{Q}R 記法；建基於 Floyd(1967) | https://dl.acm.org/doi/10.1145/363235.363259 |
| 📌 Hoare「billion-dollar mistake」（null reference） | null 引入於 **ALGOL W, 1965**；「billion-dollar mistake」說法出自 **QCon London 2009** 演講（InfoQ 有錄影），**非**圖靈獎演說 | C. A. R. Hoare | **常見誤植**：很多文章把此說繫到他 1980 圖靈獎演說，**錯**——1980 演說是「The Emperor's Old Clothes」，「billion-dollar mistake」是 2009 QCon。作者務必分清這兩場。 | https://www.infoq.com/presentations/Null-References-The-Billion-Dollar-Mistake-Tony-Hoare/ |
| 🟢 ML 語言 ＆ Hindley–Milner 型別推論 | 1970s，Edinburgh LCF theorem prover | Robin Milner（ML）；型別系統由 J. Roger Hindley 先述、Milner 重新發現、Luis Damas 形式化證明（Algorithm W） | 第一個有多型型別推論的語言 | https://en.wikipedia.org/wiki/ML_(programming_language) ；https://en.wikipedia.org/wiki/Hindley%E2%80%93Milner_type_system |

---

## H. 函數式編程（ch09）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 Lambda calculus | 1930s；**1936** 發表純計算相關的 untyped λ-calculus | Alonzo Church | 1935 原系統被 Kleene–Rosser 悖論證明不一致，Church 1936 抽出可計算部分 | https://en.wikipedia.org/wiki/Lambda_calculus |
| 🟢 Miranda | 1985 釋出（設計 1983–86） | David Turner | 專有；**Haskell 的主要靈感** | https://en.wikipedia.org/wiki/Miranda_(programming_language) |
| 🟢 Haskell 1.0 | **1990**（FPCA '87 在 Portland 決議組委員會） | 委員會 | lazy、purely functional | https://en.wikipedia.org/wiki/Haskell ；https://simon.peytonjones.org/assets/pdfs/haskell-being-lazy-with-class.pdf |
| 🟢 Herb Sutter「The Free Lunch Is Over」 | **2005-03**，*Dr. Dobb's Journal* 30(3) | Herb Sutter | multicore／concurrency 轉折的標誌性文章；另有 2005-02 *C/C++ Users Journal* 簡版 | http://www.gotw.ca/publications/concurrency-ddj.htm ；https://en.wikipedia.org/wiki/Herb_Sutter |

---

## I. 人月神話（ch10）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 《The Mythical Man-Month》 | **1975**（週年增訂版 **1995**） | Fred Brooks | 經驗來自 IBM OS/360 管理；談 conceptual integrity、second-system effect | https://en.wikipedia.org/wiki/The_Mythical_Man-Month |
| 🟢 Brooks's Law | 1975（書中） | Fred Brooks | 「**Adding manpower to a late software project makes it later.**」 | 同上 |
| 📌 「No Silver Bullet — Essence and Accident in Software Engineering」 | **1986**（論文，1986 IFIP）；**1995 版才併入** MM-M 週年版 | Fred Brooks | **熱點**：很多人以為「No Silver Bullet」是 1975 原書內容——**錯，是 1986 的獨立論文**。談 essential vs accidental complexity。作者寫年份務必 1986。 | https://en.wikipedia.org/wiki/The_Mythical_Man-Month ；https://en.wikipedia.org/wiki/No_Silver_Bullet |
| 📌 Conway's Law | 論文「How Do Committees Invent?」**1968-04 刊於 Datamation**（1967 投稿、先被 Harvard Business Review 退稿） | Melvin Conway | 「any organization that designs a system … will produce a design whose structure is a copy of the organization's communication structure.」名稱「Conway's Law」由 George Mealy 1968-07 後冠上。作者常寫「1968」，可；若寫「1967」要註明那是構思/投稿年。 | https://en.wikipedia.org/wiki/Conway%27s_law ；https://www.melconway.com/Home/Conways_Law.html |

---

## J. 瀑布（ch11）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 📌 Royce「Managing the Development of Large Software Systems」 | **1970** | Winston W. Royce | **本書最重要的「人人都搞錯」事實**：Royce **沒有**創「waterfall」一詞，也**沒有**主張純線性瀑布；他把純線性圖當作「risky and invites failure」的反例呈現，主張要**迭代**（「do it twice」、回饋環）。作者談瀑布起源**必須**寫成「常被誤讀為瀑布之父，實際上 Royce 是批判純線性並倡議迭代」。 | https://en.wikipedia.org/wiki/Winston_W._Royce ；https://en.wikipedia.org/wiki/Waterfall_model |
| 📌 「Waterfall」一詞之始 | **1976** | 一般歸於 **Bell ＆ Thayer**，"Software requirements: Are they really a problem?"（Proc. 2nd ICSE, 1976）——文中說「Royce…introduced the concept of the 'waterfall'」 | 該詞晚於 Royce 論文 6 年才出現，且非 Royce 自稱 | https://en.wikipedia.org/wiki/Waterfall_model |
| 🟢 CMM / CMMI | CMM 1980s 末–1990s（SEI, Carnegie Mellon） | Watts Humphrey（SEI） | 過程成熟度模型 | https://en.wikipedia.org/wiki/Capability_Maturity_Model |

---

## K. 敏捷（ch12）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 Agile Manifesto | **2001-02-11~13**，Snowbird, Utah | **17 位**簽署人（見下） | 四大價值：**Individuals and interactions over processes and tools；Working software over comprehensive documentation；Customer collaboration over contract negotiation；Responding to change over following a plan** | https://agilemanifesto.org/history.html |
| 🟢 17 位簽署人 | 2001 | Kent Beck, Mike Beedle, Arie van Bennekum, Alistair Cockburn, Ward Cunningham, Martin Fowler, James Grenning, Jim Highsmith, Andrew Hunt, Ron Jeffries, Jon Kern, Brian Marick, Robert C. Martin, Steve Mellor, Ken Schwaber, Jeff Sutherland, Dave Thomas | 名單照此 | https://agilemanifesto.org/ |
| 🟢 Extreme Programming（XP） | C3（Chrysler Comprehensive Compensation）專案約 **1993** 啟動；**Kent Beck 1996 進場**、發展 XP 實踐；系統 1997 上線、專案 **2000-02 取消**；**《Extreme Programming Explained》1999-10**。⚠️ 原記「1995-01 起」過於精確且來源不一，已校為「約 1993 啟動、Beck 1996 進場」（2026-06-13 ch12 撰寫時 web 複核：Wikipedia + 二手一致） | Kent Beck（Ron Jeffries、Ward Cunningham 參與） | — | https://en.wikipedia.org/wiki/Extreme_programming ；https://en.wikipedia.org/wiki/Kent_Beck |
| 🟢 TDD | 1990s 末隨 XP（Beck 稱「重新發現」非發明） | Kent Beck | red-green-refactor | https://martinfowler.com/bliki/TestDrivenDevelopment.html |
| 🟢 Scrum | OOPSLA **1995** 正式發表；首個 Scrum 團隊 1993/1994 | Ken Schwaber ＆ Jeff Sutherland | 根源於 Takeuchi & Nonaka **1986**「The New New Product Development Game」（*HBR*） | https://en.wikipedia.org/wiki/Scrum_(project_management) ；https://hbr.org/1986/01/the-new-new-product-development-game |
| 🟢 Refactoring | 《Refactoring》**1999**（Martin Fowler）；Opdyke 博論 **1992** | Martin Fowler；William Opdyke（學術源頭） | — | https://martinfowler.com/books/refactoring.html |
| ⚠️ Continuous Integration | 「CI」一詞常歸 **Grady Booch**（1990s, *Object-Oriented Analysis and Design*）；由 Beck/XP 推廣 | Booch（造詞）／Beck（推廣） | 造詞歸屬常被簡化；標 ⚠️ 提醒作者寫「一般歸於 Booch、XP 發揚」 | https://en.wikipedia.org/wiki/Continuous_integration |

---

## L. 關聯式資料庫（ch13）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 Codd「A Relational Model of Data for Large Shared Data Banks」 | *CACM* **1970-06**（13:377–387） | E. F. Codd（IBM） | 關聯模型原典；relational algebra | https://dl.acm.org/doi/10.1145/362384.362685 |
| 🟢 IBM System R / SEQUEL→SQL | SEQUEL 論文 **1974**（SIGFIDET）；System R 1970s 中 | Donald Chamberlin ＆ Raymond Boyce | 因商標衝突 SEQUEL 改名 **SQL**；Boyce 1974 年英年早逝 | https://www.historyofinformation.com/detail.php?id=910 ；https://en.wikipedia.org/wiki/IBM_System_R |
| 🟢 Ingres | 1970s，UC Berkeley | Michael Stonebraker 等 | 與 System R 並行的關聯式原型 | https://en.wikipedia.org/wiki/Ingres_(database) |
| 🟢 ACID 一詞 | **1983** | Theo Härder ＆ Andreas Reuter 造 ACID 縮寫；建基於 **Jim Gray** 的交易概念（Gray 命名了 atomicity/consistency/durability，但未含 isolation） | — | https://en.wikipedia.org/wiki/ACID |
| 🟢 CAP theorem | conjecture：Brewer **2000** PODC（先 1999 提）；證明：Gilbert ＆ Lynch **2002** | Eric Brewer（猜想）；Seth Gilbert ＆ Nancy Lynch（證明） | 「conjecture→theorem」順序要寫對 | https://en.wikipedia.org/wiki/CAP_theorem |
| 🟢 Bigtable / Dynamo 論文 | Bigtable **2006**（OSDI）；Dynamo **2007**（SOSP） | Google / Amazon | NoSQL 運動的技術源頭 | https://en.wikipedia.org/wiki/Bigtable |
| ⚠️ 「NoSQL」一詞的近代復興 | 2009 meetup（San Francisco, Johan Oskarsson 主辦），名稱由 **Eric Evans** 提議 | Eric Evans（2009 meetup 命名）；Johan Oskarsson（主辦） | **注意**：1998 Carlo Strozzi 曾用「NoSQL」指另一個（仍是關聯式但無 SQL 介面）的東西，與 2009 的分散式 NoSQL 運動是**不同**所指。作者要區分這兩個「NoSQL」。 | https://en.wikipedia.org/wiki/NoSQL |

---

## M. 開源與版本控制（ch14）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 GNU Project 宣告 | **1983-09-27** | Richard Stallman | 「GNU's Not Unix」遞迴縮寫 | https://www.gnu.org/gnu/thegnuproject.en.html |
| 🟢 Free Software Foundation | **1985** | Richard Stallman | 「Free as in freedom（自由而非免費）」 | https://www.britannica.com/biography/Richard-Stallman |
| ⚠️ GPL | **GPLv1 1989**（不是 1985）；GPLv2 1991；GPLv3 2007 | Richard Stallman | 提醒：FSF 是 1985，GPL **第一版是 1989**，常被混為一年 | https://en.wikipedia.org/wiki/GNU_General_Public_License |
| 🟢 Linux kernel | **1991**（1992 改為自由軟體授權） | Linus Torvalds | 與 GNU 結合成完整自由 OS | https://www.gnu.org/gnu/thegnuproject.en.html |
| 🟢 「The Cathedral and the Bazaar」 | 首次發表 **1997-05**（Linux Kongress, Würzburg）；書 1999 | Eric S. Raymond | — | https://en.wikipedia.org/wiki/The_Cathedral_and_the_Bazaar |
| 🟢 「Open Source」一詞 | **1998-02**（VA Linux 策略會，配合 Netscape 開源） | **Christine Peterson** 造詞；OSI 由 Eric Raymond（首任主席）、Bruce Perens 等創立 | — | https://opensource.com/article/18/2/coining-term-open-source-software ；https://opensource.org/about/history-of-the-open-source-initiative |
| 🟢 Git | **2005-04**（因 BitKeeper 授權爭議；Andrew Tridgell 反向工程事件觸發） | Linus Torvalds | 同期 **Mercurial** 亦由 Matt Mackall 2005 啟動 | https://en.wikipedia.org/wiki/Git ；https://en.wikipedia.org/wiki/Mercurial |
| 🟢 CVS / SVN | CVS 1990；Subversion 2000 起、1.0 於 2004 | — | Git 之前的主流集中式 VCS | https://en.wikipedia.org/wiki/Apache_Subversion |

---

## N. 網路與 Web（ch15）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 ARPANET 上線 | **1969**（年底四個節點） | ARPA | — | https://www.internetsociety.org/internet/history-internet/brief-history-internet/ |
| 🟢 TCP/IP 論文 / 切換 | 論文「A Protocol for Packet Network Intercommunication」**1974-05**（*IEEE Trans. Comm.*）；ARPANET 由 NCP 切到 TCP/IP 的 flag day **1983-01-01** | Vint Cerf ＆ Bob Kahn | — | https://en.wikipedia.org/wiki/Flag_day_(computing) |
| 🟢 World Wide Web | 提案「Information Management: A Proposal」**1989-03**；基本概念（HTTP/HTML/URL）1990 底定義；對外公開 **1991-08-06**；**1993-04-30 CERN 宣布 WWW 底層技術進入公有領域（royalty-free，放棄收費）**——這是「開放標準無人可擁有」論點的史實核心（ch15 個案用） | Tim Berners-Lee（CERN） | — | https://home.cern/science/computing/birth-web/short-history-web ；https://home.cern/news/news/computing/web30-relive-day-web-went-public-domain |
| 🟢 Mosaic | **1993-01-23** 宣布 | Marc Andreessen ＆ Eric Bina（NCSA） | 首個整合文字＋圖的圖形瀏覽器 | https://en.wikipedia.org/wiki/History_of_the_World_Wide_Web |
| 🟢 瀏覽器大戰（第一次） | Navigator 1994；IE 1.0 1995-08；戰局約 1995–2001 | Netscape vs Microsoft IE | — | https://en.wikipedia.org/wiki/Browser_wars |
| 🟢 Web 2.0 | 名詞出於 **2004** O'Reilly–MediaLive 腦力激盪；O'Reilly「What Is Web 2.0」**2005** | Tim O'Reilly | 年份要分：構思 2004、定義文 2005 | https://www.oreilly.com/pub/a/web2/archive/what-is-web-20.html |
| 🟢 AJAX 一詞 | **2005-02**「Ajax: A New Approach to Web Applications」 | Jesse James Garrett（Adaptive Path） | — | https://en.wikipedia.org/wiki/Jesse_James_Garrett |
| 🟢 LAMP | 1990s 末成形（Linux/Apache/MySQL/PHP(或 Perl/Python)） | 名詞普及約 1998（*c't* 雜誌） | 一般背景知識 | https://en.wikipedia.org/wiki/LAMP_(software_bundle) |

---

## O. 雲與虛擬化（ch16）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 IBM CP/CMS（CP-40 / CP-67） | 1960s 中（CP-40）；CP-67 1967 起日常生產 | IBM Cambridge Scientific Center | 每使用者一台「模擬的獨立電腦」＝最早的全虛擬化 | https://en.wikipedia.org/wiki/Timeline_of_virtualization_development |
| 🟢 VMware | 成立 1998；VMware Workstation **1999** | VMware | 首個成功的 x86 虛擬化產品 | 同上 |
| 🟢 Xen | **2003**（SOSP 論文「Xen and the Art of Virtualization」） | Ian Pratt, Keir Fraser 等（Cambridge） | paravirtualization | 同上 |
| 🟢 AWS S3 / EC2 | **S3 2006-03**；**EC2 2006-08**（公測） | Amazon | IaaS 起點：伺服器從「擁有」變「按片租用」 | https://en.wikipedia.org/wiki/Timeline_of_virtualization_development |
| 🟢 IaaS/PaaS/SaaS 分類 | 約 2006–2011 成形（NIST 雲定義 SP 800-145, 2011 確立） | — | 作者談分類學可引 NIST 2011 | https://csrc.nist.gov/pubs/sp/800/145/final |
| 🟢 Infrastructure as Code 工具線 | CFEngine **1993**；Puppet **2005**；Chef **2009**；Terraform **2014**（HashiCorp） | Mark Burgess(CFEngine)、Luke Kanies(Puppet)、Adam Jacob(Chef)、HashiCorp(Terraform) | 年份照此 | https://en.wikipedia.org/wiki/Infrastructure_as_code |

---

## P. 微服務、容器、DevOps、SRE（ch17–18）

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 SOA | 概念 1990s 末、流行於 2000s 初中期 | 業界 | 後因 vendor-specific stack 高調失敗而退潮 | https://intellias.com/service-oriented-architecture-soa/ |
| 🟢 Microservices 一詞普及 | 詞約 2011–2012 圈內成形；定義文 **2014**「Microservices」 | James Lewis ＆ Martin Fowler（定義文）；Netflix/Adrian Cockcroft 早期實踐者 | 作者寫「2014 Lewis & Fowler 定義文」最穩 | https://martinfowler.com/articles/microservices.html ；https://www.scirp.org/reference/referencespapers?referenceid=3943543 |
| 🟢 Docker | **2013-03** PyCon lightning talk「The Future of Linux Containers」公開展示 | Solomon Hykes，dotCloud（內部工具開源而來） | — | https://en.wikipedia.org/wiki/Docker_(software) ；https://pyvideo.org/pycon-us-2013/the-future-of-linux-containers.html |
| 🟢 cgroups / LXC | cgroups 進 Linux kernel **2007**（Google 主推，原名 "process containers"）；LXC 2008 | Google（Paul Menage, Rohit Seth 等） | 容器底層血統 | https://en.wikipedia.org/wiki/Cgroups |
| 🟢 Kubernetes / CNCF | K8s Google **2014** 宣布並開源（血統承 Borg/Omega）；**CNCF 2015** 成立、K8s 為首個種子專案 | Google | — | https://en.wikipedia.org/wiki/Cloud_Native_Computing_Foundation |
| 🟢 DevOps 一詞 | **2009-10** 首屆 DevOpsDays（Ghent, 比利時） | Patrick Debois | — | https://www.everythingdevops.dev/blog/a-brief-history-of-devops-and-its-impact-on-software-development |
| 🟢 《The Phoenix Project》 | **2013** | Gene Kim, Kevin Behr, George Spafford | IT/DevOps 小說 | https://itrevolution.com/product/the-phoenix-project/ |
| 🟢 《Continuous Delivery》 | **2010** | Jez Humble ＆ David Farley | — | https://martinfowler.com/books/continuousDelivery.html |
| 🟢 Google SRE / 《Site Reliability Engineering》 | SRE 起於 **約 2003**（Google）；書 **2016**（O'Reilly） | Ben Treynor Sloss（創 SRE） | error budget、SLO/SLI 等概念由此書普及 | https://sre.google/sre-book/embracing-risk/ |
| 🟢 《Team Topologies》 | **2019** | Matthew Skelton ＆ Manuel Pais | platform engineering 運動奠基文本；cognitive load、stream-aligned/platform team | https://teamtopologies.com/book |

---

## Q. AI 輔助編程（ch20）— ⚠️ 時效敏感，所有前瞻主張務必標日期

> **基準日期：2026-06。** 本節的「現況」會快速過期；作者寫此章時**一定**要寫「截至 2026-06」並避免具體市佔/排名數字。

| 事實 | 年份 | 歸屬 | 注意 | 來源 |
|---|---|---|---|---|
| 🟢 程式碼補全（autocomplete／IntelliSense 一脈） | 1990s–2010s 漸進 | 多家 IDE | 背景脈絡 | （一般背景） |
| 🟢 GitHub Copilot | technical preview **2021-06**；GA **2022-06**（VS Code 2022-06-29） | GitHub/OpenAI；初版基於 **OpenAI Codex**（GPT-3 後裔） | 年份穩固，可放心引 | https://github.blog/news-insights/product-news/introducing-github-copilot-ai-pair-programmer/ ；https://en.wikipedia.org/wiki/GitHub_Copilot |
| ⚠️ 2023–2026「agentic coding」工具景觀 | 2023 起加速 | Cursor、Claude Code、Copilot agent mode、Codex CLI、Windsurf 等（截至 2026-06 確實存在） | **務必 hedge**：可說「截至 2026-06，市場已從『行內補全』轉向『跨檔自主 agent』，主要工具包括 Cursor、Claude Code、GitHub Copilot 的 agent 模式等」。**不要**寫具體 SWE-bench 分數、市佔、營收、模型版本排名——這些變動極快且來源多為行銷/二手彙整，無法獨立查證。 | https://www.faros.ai/blog/best-ai-coding-agents-2026（二手彙整，僅供「存在性」佐證，數字不可引） |

> ⚠️ 提醒：搜尋結果中出現的「市場 18 個月翻倍至 $128 億」「90% 開發者每日使用」「Opus 4.8 在 SWE-bench Verified 88.6%」等數字，**全部來自二手部落格/彙整、無一手出處**，**禁止**寫入書中作為事實。作者若非寫不可，只能寫「有報導稱／一說」並明示不確定。

---

## R. 反覆主題的名言／概念（ch19, ch21）— 措辭與歸屬

| 名言／概念 | 年份 | 歸屬 | 精確措辭／注意 | 來源 |
|---|---|---|---|---|
| 🟢 The Law of Leaky Abstractions | **2002-11-11** | Joel Spolsky | 「All non-trivial abstractions, to some degree, are leaky.」 | https://www.joelonsoftware.com/2002/11/11/the-law-of-leaky-abstractions/ |
| ⚠️ 「two hard things in CS: cache invalidation and naming things」 | 確切年代不明（一說 CMU 約 1970s） | **Phil Karlton**（一般歸屬；Martin Fowler 等採此） | 原始出處與確切時間**無一手記載**；作者寫「一般歸於 Phil Karlton」即可，勿給確切年份。 | https://www.karlton.org/2017/12/naming-things-hard/ ；https://quotesondesign.com/phil-karlton/ |
| 📌 「premature optimization is the root of all evil」 | **1974**「Structured Programming with go to Statements」（*ACM Computing Surveys* 6(4), p.268） | **Donald Knuth** | **完整脈絡務必帶**：「We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil. **Yet we should not pass up our opportunities in that critical 3%.**」常被斷章取義成「不要優化」。Knuth **1989** 在「The Errors of TeX」中稱此為「Hoare's Dictum」，故有 Knuth/Hoare 歸屬之辯——但 1974 原文並未引 Hoare。作者寫「Knuth 1974，後 Knuth 自己歸給 Hoare」。 | https://en.wikiquote.org/wiki/Donald_Knuth ；https://shreevatsa.wordpress.com/2008/05/16/premature-optimization-is-the-root-of-all-evil/ |
| 🟢 「Worse is Better」 | 概念 1989；文「Lisp: Good News, Bad News, How to Win Big」1990；「The Rise of Worse is Better」正式刊 *AI Expert* **1991-06** | Richard P. Gabriel | 年份分層如左 | https://en.wikipedia.org/wiki/Worse_is_better ；https://dreamsongs.com/WorseIsBetter.html |
| （見 ch10）Brooks's Law、No Silver Bullet、Conway's Law | — | — | 措辭與年份見 §I | — |

---

## S. 跨章基準年份表（Appendix A 主時間軸）

> 僅收錄上方已查證條目。**strand** 欄：抽象（語言/型別/抽象層）｜方法（流程/工程實務）｜both。

| 年份 | 里程碑 | strand |
|---|---|---|
| 1837 | Babbage Analytical Engine 設計提出 | 抽象 |
| 1843 | Lovelace Notes（含 Note G／Bernoulli）⚠️「第一位程式設計師」標籤有爭議 | 抽象 |
| 1936 | Turing「On Computable Numbers」；Church 發表 untyped λ-calculus | 抽象 |
| 1945 | First Draft of a Report on the EDVAC（儲存程式概念，⚠️署名爭議） | both |
| 1945–46 | ENIAC 運轉/公開；ENIAC Six | both |
| 1948 | Manchester Baby 跑首支儲存程式 | 抽象 |
| 1949 | EDSAC 運轉；Wheeler「Initial Orders」＝首個組譯器 | 抽象 |
| 1951–52 | Hopper A-0（⚠️「第一個編譯器」需保留） | 抽象 |
| 1957 | FORTRAN 出貨 | 抽象 |
| 1958–60 | LISP（McCarthy）；GC、homoiconicity | 抽象 |
| 1959–60 | COBOL（CODASYL；Hopper 經 FLOW-MATIC 影響） | 抽象 |
| 1960 | ALGOL 60 Report；BNF | 抽象 |
| 1966 | Böhm–Jacopini 結構化定理 | 抽象 |
| 1967 | Simula 67（OOP 源頭） | 抽象 |
| 1968 | NATO Garmisch（software crisis / software engineering）；Dijkstra「Go To…Harmful」；Conway's Law 刊 Datamation | both |
| 1969 | ARPANET；Hoare logic 論文；NATO Rome；Unix 起步 | both |
| 1970 | Codd 關聯模型；Royce 論文（📌被誤讀為瀑布之父） | both |
| 1972 | C 語言；Parnas information hiding | both |
| 1973 | Unix pipes（McIlroy） | 抽象 |
| 1974 | TCP/IP 論文（Cerf/Kahn）；SEQUEL（→SQL）；Knuth premature-optimization；Dijkstra separation of concerns | both |
| 1975 | 《The Mythical Man-Month》；Brooks's Law | 方法 |
| 1976 | 「Waterfall」一詞首現（Bell & Thayer） | 方法 |
| 1978 | K&R《C》；Unix 哲學原則（McIlroy 等，⚠️整齊三句版是 Salus 1994 轉述） | both |
| 1979 | C with Classes（→C++ 1983） | 抽象 |
| 1980s | Smalltalk-80；ML/Hindley–Milner | 抽象 |
| 1983 | GNU 宣告；TCP/IP flag day；ACID 一詞 | both |
| 1985 | FSF；Miranda | both |
| 1986 | 📌「No Silver Bullet」（Brooks，**非 1975**）；Takeuchi & Nonaka HBR（Scrum 根源） | 方法 |
| 1989 | WWW 提案（Berners-Lee）；GPLv1；Worse is Better（概念） | both |
| 1990 | Haskell 1.0 | 抽象 |
| 1991 | WWW 公開；Linux | both |
| 1993 | Mosaic 圖形瀏覽器；**CERN 宣布 WWW 進入公有領域（4/30）** | 抽象 |
| 1995 | Java 1.0（WORA）；Scrum 發表（OOPSLA）；IE 1.0 | both |
| 1997 | Cathedral and the Bazaar | 方法 |
| 1998 | 「Open Source」一詞；VMware 成立 | both |
| 1999 | XP Explained；Refactoring（Fowler）；VMware Workstation | both |
| 2000 | CAP conjecture（Brewer） | 抽象 |
| 2001 | Agile Manifesto（Snowbird, 17 簽署人） | 方法 |
| 2002 | CAP 證明（Gilbert/Lynch）；Law of Leaky Abstractions | both |
| 2003 | Xen；Google SRE 起 | both |
| 2004–05 | Web 2.0（O'Reilly）；AJAX（Garrett）；Free Lunch Is Over（Sutter 2005）；Puppet 2005；MapReduce 論文（Dean & Ghemawat, OSDI 2004） | both |
| 2006 | AWS S3/EC2；Google Bigtable 論文 | both |
| 2007 | Linux cgroups（Google）；Amazon Dynamo 論文 | both |
| 2009 | DevOpsDays（Debois）；NoSQL meetup；Chef | 方法 |
| 2010 | 《Continuous Delivery》（Humble/Farley） | 方法 |
| 2013 | Docker 公開；《The Phoenix Project》 | both |
| 2014 | Kubernetes；Microservices 定義文（Lewis/Fowler）；Terraform | both |
| 2015 | CNCF 成立 | 方法 |
| 2016 | 《Site Reliability Engineering》（Google/O'Reilly） | 方法 |
| 2019 | 《Team Topologies》 | 方法 |
| 2021 | GitHub Copilot technical preview | 抽象 |
| 2022 | GitHub Copilot GA | 抽象 |
| 2023–26 | ⚠️ agentic coding 工具興起（Cursor / Claude Code / Copilot agent 等，截至 2026-06） | 抽象 |

---

## 脆弱事實清單（作者必須照本檔、不可憑記憶）

下列是「大眾記憶最容易錯」的高危事實。作者引用這些時，**必須**回到本檔對應條目照措辭/年份寫，並帶上保留條件：

1. **Royce / waterfall 神話（§J）**：Royce 1970 並未提倡純瀑布、也沒造「waterfall」一詞；他是把純線性當反例、倡議迭代。「waterfall」一詞出自 Bell & Thayer **1976**。
2. **Lovelace「第一位程式設計師」（§A）**：是有爭議的後世標籤；Note G 更近「執行軌跡」；Babbage 自承 Bernoulli 數部分代數推演是他先做的。寫「常被譽為」。
3. **Hopper A-0「第一個編譯器」（§B）**：以現代定義更像 loader/linker，不是現代意義 compiler。
4. **「Considered Harmful」標題（§D）**：是編輯 **Niklaus Wirth** 加的；Dijkstra 原題「A Case Against the Goto Statement」。
5. **Kay「OOP=messaging」引文（§F）**：精確句為「…The big idea is 'messaging'.」⚠️ 原始出處單一（1998 email）。
6. **Brooks「No Silver Bullet」是 1986、不是 1975（§I）**：原書 1975，No Silver Bullet 是 1986 論文，1995 才併入週年版。
7. **Conway's Law 1968（§I）**：刊 Datamation 1968-04（1967 投稿、被 HBR 退稿）；名稱由 Mealy 後冠。
8. **Knuth「premature optimization」完整脈絡（§R）**：必帶「Yet we should not pass up our opportunities in that critical 3%」與「97% of the time」；勿斷章成「不要優化」。Knuth 1989 自稱「Hoare's Dictum」。
9. **所有 LOC／使用量／市佔統計一律 ⚠️**：COBOL「2,200 億行」（Reuters 2015/17，單一來源）、「$3 兆/日」、AI coding 市場/SWE-bench 數字等——只能寫「據（單一/二手來源）估計」，不可斷言。
10. **Hoare「billion-dollar mistake」場合（§G）**：是 **2009 QCon London**，**不是** 1980 圖靈獎演說（那場是「The Emperor's Old Clothes」）。
11. **「a language so far ahead of its time」（§C）**：是 Hoare 論 ALGOL 60，精確句見 §C。
12. **Unix「do one thing well」（§E）**：1978 原句是「Make each program do one thing well」；流傳的整齊三句版是 Salus 1994 轉述。

---

*掃描日誌：2026-06-13 初版，涵蓋 ch02–ch21 全部事實區。約 60 次 web 搜尋/查證。下次重掃重點：Q 區（AI coding 半年內必過期）、所有 ⚠️ 統計、Kay 引文一手出處若有更可靠來源則升級。*
