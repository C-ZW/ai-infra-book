# 附錄 C — 閱讀地圖

> **這份附錄做什麼**：把全書攤成一張地圖，再給你幾條依興趣的捷徑、一份指向書架鄰書的跨書連結整理、以及一份去重後的延伸閱讀總清單。你不必從 ch01 一路爬到 ch20——這裡告訴你：想懂某件事，該走哪幾章；讀完某章想往外走，該翻哪本姊妹書、哪篇原始論文。

## 全書地圖重述

下面這張圖你在每個 Part 首章（ch01／ch04／ch08／ch12／ch16）都見過一次（「◄ 你在這裡」逐 Part 往下移）。這裡把它完整攤開，當作整本書的索引：

```text
全書地圖：每個整數都由質數搭成，可是質數自己長在哪裡？——從原子，到謎，到馴服

  Part I  乘法的原子 .............. 不可分的建材，與唯一的搭法
     ch01 整除與質數：誰能整除誰
     ch02 算術基本定理：唯一的搭法（埋哥德爾伏筆）
     ch03 質數無窮：歐幾里得的五行證明
        |
        v
  Part II  質數長在哪裡（上）...... 它們有多稀、住在哪
     ch04 篩法：把合數劃掉
     ch05 質數有多稀疏
     ch06 質數計數函數 π(x)
     ch07 質數定理 PNT：亂中的鐵律（高潮一）
        |
        v
  Part III  另一個世界：模算術 .... 把無窮整數摺進一個時鐘
     ch08 同餘：時鐘算術
     ch09 最大公因數與貝祖
     ch10 費馬小定理
     ch11 歐拉定理與歐拉函數 φ
        |
        v
  Part IV  尚未馴服的謎 ........... 細節裡的魔鬼
     ch12 孿生質數與質數間隙
     ch13 黎曼假設一瞥：質數的音樂（高潮二）
     ch14 驗證不是證明
     ch15 沒有公式，卻有規律
        |
        v
  Part V  質數的用處與收束 ........ 把難變成鎖，把謎收成欣賞
     ch16 梅森質數與最大質數的競賽
     ch17 RSA 一瞥：把分解變成鎖
     ch18 烏拉姆螺旋：亂裡的線
     ch19 質數長在哪裡：謎的對帳
     ch20 亂與律共存（收官）
```

這本書的脊椎，是兩條交織的主線：**脊椎 A**——同一個分解 60=2²·3·5，在每個新 Part 重新認識；**脊椎 B**——「質數長在哪裡」這個謎，逐層被追問、逐層被部分回答。ch19 把謎的每一層對帳，ch20 則把整本書的中央張力收束：

```text
脊椎 B：「質數長在哪裡」謎的六層對帳（ch19 總對帳）

  問題                 答案                        已證 / 未解
  ──────────────────  ──────────────────────────  ─────────────
  Q1 有幾個？          無窮多（ch03）               已證
  Q2 有多密？          越往上越稀（ch04/05）        已知
  Q3 稀到什麼程度？    π(x)~x/ln x（PNT，ch07）     已證（1896）
  Q4 誤差有多大？      黎曼零點控制（ch13）          未解（RH，2026-06）
  Q5 最近能多近？      孿生質數猜想（ch12）          未解（2026-06）
  Q6 最大的是哪個？    M52（2024-10，ch16）         會更新的紀錄（2026-06）
```

同一道謎，六種層次，從「有多少」（整體統計）走到「最近／最大」（細節邊界）。整本書其實只在問一句話：**質數看似隨機散落，卻服從鐵一般的統計律——亂與律如何在同一批數裡共存。** 答案是：亂在個別位置、律在整體統計；人類馴服了平均（PNT），還沒馴服細節（RH、孿生）。

## 依興趣的選讀路徑

不想二十章順著爬？下面五條捷徑各帶你去一個明確的目的地。每條都自成一個故事，讀完那幾章就夠回答標題那個問題。

```text
路徑 A：只想懂「什麼是算術基本定理、為什麼質數是原子」
   ch01 → ch02 → ch20
   先備齊原料——整除、因數、質數定義，以及 60=2²·3·5 這個貫穿全書的
   小數（ch01）；再深入唯一分解的核心——「拆法為何唯一」需要歐幾里得
   引理 VII.30 撐住，1 不是質數的原因也在這（ch02）；最後在收官章
   對帳「質數作為乘法原子」的完整意義（ch20）。
   最短的「懂 FTA」路線，三章可讀完。

路徑 B：想懂「質數定理是什麼、亂與律如何共存」
   ch05 → ch06 → ch07 → ch20
   先感受稀疏的驚人程度——沙漠可以任意長（ch05）；再引入計數函數
   π(x) 及其階梯形狀（ch06）；高潮：PNT 把「平均密度 1/ln x」釘成
   一條 1896 年才證出的鐵律（ch07）；最後在收官章確認亂與律共存的
   最終形式（ch20）。這條是全書「中央張力」的骨幹。

路徑 C：想懂「費馬小定理與 RSA 如何用質數當鎖」
   ch08 → ch09 → ch10 → ch11 → ch17
   先把無窮整數摺進有限時鐘——同餘的世界觀（ch08）；取出模算術的引
   擎——輾轉相除求 GCD，貝祖等式算逆元（ch09）；費馬小定理的直覺與
   為什麼成立（ch10）；歐拉定理把費馬推廣到任意模數，算出 φ(n)（ch11）；
   最後把前四章的工具全組裝進 RSA，手算玩具金鑰加解密（ch17）。
   這條走完 Part III 的整個地基。

路徑 D：想懂「歐幾里得那個兩千年前的五行證明」
   ch01 → ch03 → ch05
   先定義「質數」（ch01）；讀歐幾里得 IX.20 的建構式論證——不是反
   證法、N 不必是質數、30031=59×509 反例（ch03）；再看「無窮」與
   「稀疏」如何並存、沙漠可任意長但質數永不用完（ch05）。
   三章讀完，你可以對另一個工程師講清楚歐幾里得的美在哪、以及 T1
   「建構式 vs 反證法」的區別。

路徑 E：想感受「細節裡的謎」（Part IV 全覽）
   ch12 → ch13 → ch14 → ch15
   從孿生質數與張益唐的有界間隙出發（ch12）；看黎曼假設如何把質數
   分布的誤差連到 ζ 的零點——「質數的音樂」（ch13）；再接「驗證到
   很大都沒反例，為什麼不算證明」的誠實課（ch14）；最後在「沒有公
   式卻有規律」裡把 Part IV 的張力收束（ch15）。
   這條適合「對未解數學之謎最感興趣」的你。
```

五條路徑彼此有重疊（ch20 是 A 和 B 的共同終點，ch14 接在 D 和 E 之後都有收穫），那是刻意的——它們交會的地方，就是全書反覆叩問的那條中央張力：**亂與律如何在同一批數裡共存。** 讀完任一條想再往深走，順著地圖把缺的 Part 補回來即可。

## 跨書連結整理

本書是「推理六書」之一，書架上有幾本相鄰的姊妹書。本書遇到它們的主場時點到為止、把深度指過去。下面按主題整理「哪一章的哪件事，該往哪本書補」。格式照全書慣例——**主題式帶過、不寫死他書的章號**。

```text
主題                              本書出現處            指向
────────────────────────────────  ──────────────────  ────────────────────
FTA（算術基本定理）唯一分解被      ch02 埋伏筆          《這句話無法被證明》
哥德爾拿去把邏輯證明壓成數字                           談哥德爾編碼那章

對數 ln、漸近 ~、積分 Li(x)、     ch06/07/13           《馴服無限：微積分》
ζ 函數的解析延拓、頻譜直覺

質數的機率式啟發（1/ln n）、      ch07/ch12            《馴服隨機：機率與統計》
個體不可測總體可測的大數法則

驗證 vs 證明、科學歸納 vs         ch14                 《如何不騙自己》
數學演繹的差別                                         談科學方法那本

貝祖等式的線性組合與格（lattice） ch09（一句帶）       《矩陣是動詞》
```

**FTA → 哥德爾**（三大招牌跨書連結之首）。本書 ch02 是「質數與整數結構」的 owner，在算術基本定理那章明確埋了伏筆：「這個唯一分解，日後哥德爾會拿來把整串邏輯證明壓成一個獨一無二的數字——見《這句話無法被證明》談哥德爾編碼那章，它會回頭明引本書 FTA。」這是全套推理六書最招牌的跨書連結，兩本對讀，一本給地基（質因數分解的唯一性），另一本用地基蓋了驚人的建築（哥德爾不完備定理）。

**解析數論工具**——PNT 的 ln 與漸近（什麼是 π(x) ~ x/ln x 的 ~）、Li(x)=∫₂^x dt/ln t 的積分、ζ 函數的解析延拓、「零點疊加等於頻譜」的頻譜直覺——全部由《馴服無限：微積分》擁有。本書只用結果與「平均密度 1/ln x」的口語直覺，ch07 PNT、ch13 黎曼假設都把解析深度指過去，不重推。（見《馴服無限》談對數、漸近與積分那本。）

**機率式啟發**——「把質數是否出現當作機率約 1/ln n 的試驗」（Cramér 隨機質數模型）、孿生質數的 Hardy–Littlewood 估計、個體完全確定卻有統計律的「個體不可測、整體可測」——由《馴服隨機：機率與統計》擁有。本書在 ch07 PNT 和 ch12 孿生質數都點到這個啟發，強調「這是啟發式直覺、不是嚴格機率論述」。（見《馴服隨機》談大數法則精神、個體 vs 總體那本。）

**驗證 vs 證明**——本書 ch14 深入「數值驗證 ≠ 數學證明」，對照《如何不騙自己》談科學方法的那本書：科學的真是「至今未被推翻」、數學的真是「對所有 n 演繹正確」——兩種截然不同的「真」。ch14 用 Pólya 猜想、Skewes 數、哥德巴赫驗證做案例，跨書指向那本書談科學方法的核心。

**線性結構**（弱連結）。當 ch09 的貝祖等式涉及「整數係數線性組合」時，若想延伸到格（lattice）的幾何，可一瞥《矩陣是動詞》談線性組合那部分。本書一律一句帶過、不展開。

## 延伸閱讀總清單（去重）

把全書二十章的 `## 延伸閱讀` 彙整成一份分類總表。同一來源在多章出現的只列一次（標明它服務哪些章），每條一句話講「為什麼值得讀、讀哪一段」。去重後共收錄 **42 條**外部來源。

### 一手原典（招牌定理本尊）

- **歐幾里得《幾何原本》第七卷、第九卷（David Joyce 線上互動英譯版）**（aleph0.clarku.edu/~djoyce/elements）—— 服務 ch01/ch02/ch03/ch09。整除（VII.1–2）、輾轉相除（VII.1–2）、FTA 核心引理（VII.30）、質數無窮（IX.20）的源頭原文——讀原文是感受「兩千三百年前的數學和你今天寫的迴圈是同一件事」的最直接方式。特別推薦 IX.20，可以看到歐幾里得真的用建構式、不是反證。

- **Riemann, "Über die Anzahl der Primzahlen unter einer gegebenen Größe"（黎曼 1859 論文）**（原稿影本與英譯在 claymath.org/collections/riemanns-1859-manuscript/）—— 服務 ch13。ζ 解析延拓、顯式公式、RH 猜想的源頭，僅約 6–9 頁，黎曼唯一一篇數論論文。讀引言看他怎麼「順帶」提出那個猜想——RH 在原文裡其實只是個附帶一提的猜測，不是主角。

- **Rivest, Shamir, Adleman, "A Method for Obtaining Digital Signatures and Public-Key Cryptosystems"（1977/1978 *Communications of the ACM*）**—— 服務 ch17。RSA 的原始論文，短而可讀；看他們如何把「分解難」從直覺變成可用的密碼系統，正是本章玩具金鑰的大人版。

- **Clifford Cocks, "A Note on Non-Secret Encryption"（GCHQ 內部報告 1973，1997 解密公開）**—— 服務 ch17。比 RSA 早四年、被英國情報機關鎖在抽屜二十四年的等價系統；讀「公鑰密碼被發明過兩次、第一次沒人能說」這段史。The Aperiodical（aperiodical.com）有 GCHQ 解密文件的整理報導。

- **Diffie & Hellman, "New Directions in Cryptography"（1976）**—— 服務 ch17。提出「陷門函數應該存在」的那篇——RSA 是它預言的東西第一個被造出來的實例。讀前幾頁就能理解「公鑰密碼」這個想法本身從哪來。

- **Maynard Smith & Price, "The Logic of Animal Conflict"（*Nature* 246, 1973）**—— 與本書無直接關係，是姊妹書（賽局理論）的 ESS 來源。這裡不重複列。（保留此格式說明：本表只收與本書實際內容有直接服務關係的來源。）

### 解析數論基礎與 PNT

- **Tom Apostol, "A Centennial History of the Prime Number Theorem"**（calteches.library.caltech.edu/3832/1/Apostol.pdf）—— 服務 ch07。從高斯／勒讓德的猜想，到柴比雪夫上下界、黎曼 1859 橋、1896 年 Hadamard 與 de la Vallée Poussin 的兩封捷報，可讀性高的百年史；把本章那張年表讀厚就讀這篇。

- **Wolfram MathWorld, "Prime Number Theorem"**（mathworld.wolfram.com/PrimeNumberTheorem.html）—— 服務 ch06/ch07。PNT 的精確陳述、x/ln x 與 Li(x) 的並列、歷史與各種等價形式的速查；本章 worked example 的基準值可在此核對。

- **Quanta Magazine, "Mathematicians Will Never Stop Proving the Prime Number Theorem"（2020-07）**（quantamagazine.org）—— 服務 ch07。為什麼一個 1896 就證完的定理，至今仍不斷被人用新方法重證（複變分析、初等、Tauberian…）；感受 PNT 在數學家心中的份量。

- **Tomás Oliveira e Silva, "Tables of values of π(x)"**（sweet.ua.pt/tos/primes.html）—— 服務 ch06。權威的 π(x) 數值表，本章基準值（π(10⁶)=78498 等）的查核來源。

### 質數基礎與無窮性

- **Keith Conrad, "The Infinitude of the Primes"**（kconrad.math.uconn.edu/blurbs/ugradnumthy/infinitudeofprimes.pdf）—— 服務 ch03。大學講義，專門澄清「建構式 vs 反證法」的混淆，並收錄多個質數無窮的不同證明（含歐拉倒數和發散的路子）；讀第一節即可看清本章的核心區別（T1）。

- **Keith Conrad, "The Fundamental Theorem of Arithmetic"**（kconrad.math.uconn.edu 的 expository notes）—— 服務 ch02。存在性與唯一性分開證、VII.30 引理怎麼撐住唯一性，寫得乾淨；想看比本章更完整的推導讀這份。

- **Wikipedia, "Divergence of the sum of the reciprocals of the primes"**（en.wikipedia.org）—— 服務 ch03。歐拉 1737 年用「1/2+1/3+1/5+1/7+… 發散」證質數無窮的那條路——這條路通往 ζ 函數與解析數論，本書 ch13 黎曼那章遇上同一個 ζ。

- **OEIS A006862（歐幾里得數）**（oeis.org/A006862）—— 服務 ch03。3,7,31,211,2311,30031,… 這串「乘積+1」的數列，哪些是質數、哪些是合數（30031=59×509 是第一個合數），親手驗證本章的試金石。

- **The Prime Pages（t5k.org）**—— 服務 ch01/ch04/ch05。質數研究的權威站；trial division 詞條（ch01 試除剪枝）、〈How many primes are there?〉（ch05 密度衰減）、〈The Gaps Between Primes〉（ch05/ch12 間隙）都在這裡。

### 篩法與稀疏

- **Wikipedia, "Sieve of Eratosthenes"**（en.wikipedia.org/wiki/Sieve_of_Eratosthenes）—— 服務 ch04。演算法、歷史（尼科馬庫斯記載、原始以奇數篩）、與後世變體（分段篩、Sundaram/Atkin 篩）的整理。

- **MacTutor, "Eratosthenes" 傳記**（mathshistory.st-andrews.ac.uk/Biographies/Eratosthenes/）—— 服務 ch04。埃拉托斯特尼的生平與「量地球周長」的故事；讀完你會對「篩法只是他的副業」這句話有感。

- **Quanta Magazine, "How Can Infinitely Many Primes Be Infinitely Far Apart?"（2022-07）**（quantamagazine.org）—— 服務 ch05。本章張力（質數無窮，間隙卻能任意大）的科普正解；讀它怎麼用文字講「稀疏 ≠ 枯竭」，對照你能不能對工程師講清楚這件事。

### 模算術與 GCD

- **Keith Conrad, "Modular Arithmetic"（講義 PDF）**（kconrad.math.uconn.edu/blurbs/ugradnumthy/modarith.pdf）—— 服務 ch08。同餘的定義、相容律、消去律（含互質條件）寫得乾淨且嚴格；想看「除法是叛徒」那段的完整證明，讀消去律一節。

- **Wikipedia, "Extended Euclidean algorithm"**（en.wikipedia.org/wiki/Extended_Euclidean_algorithm）—— 服務 ch09。把反向輾轉相除整理成隨迴圈一起更新的係數表，看完你會明白為什麼它能順手算出模逆元（ch11/ch17 的引擎）。

- **Wikipedia, "Bézout's identity"**（en.wikipedia.org/wiki/B%C3%A9zout%27s_identity）—— 服務 ch09。歷史段落講清楚整數版其實源自巴歇 1624、貝祖 1779 是多項式推廣，核對「名字記的帳」。

- **Wikipedia, "Kuṭṭaka"**（en.wikipedia.org/wiki/Ku%E1%B9%AD%E1%B9%ADaka）—— 服務 ch09。阿耶波多（約 499）解線性不定方程的「粉碎法」，是擴展輾轉相除的東方源頭；看古人怎麼把係數一路打碎。

- **高斯《算術研究》(*Disquisitiones Arithmeticae*, 1801) 第一章**（MacTutor 有導讀 mathshistory.st-andrews.ac.uk/Extras/Gauss_Disquisitiones/）—— 服務 ch08。同餘的源頭；讀第一段就能感受到高斯如何把「只看餘數」一刀立成代數。

### 費馬小定理、歐拉定理

- **Wikipedia, "Fermat's little theorem"**（en.wikipedia.org/wiki/Fermat%27s_little_theorem）—— 服務 ch10。定理兩種形式、費馬 1640 信與歐拉 1736 首證的史實、與歐拉定理的關係；本章史實的查核入口。

- **Wikipedia, "Proofs of Fermat's little theorem"**（en.wikipedia.org/wiki/Proofs_of_Fermat%27s_little_theorem）—— 服務 ch10。同一定理的多種證明並列（重排連乘、歸納、項鍊組合、群論版），本章用的是最初等的「重排連乘」；想看其他路子從這裡入手。

- **John D. Cook, "Searching for pseudoprimes"**（johndcook.com/blog/2021/08/10/searching-for-pseudoprimes/）—— 服務 ch10。費馬偽質數與卡邁克爾數為什麼能騙過費馬測試的直覺說明；理解本章「漂亮的漏洞」這一節讀這篇。

- **Wolfram MathWorld, "Euler's Totient Theorem" 與 "Totient Function"**（mathworld.wolfram.com）—— 服務 ch11。歐拉定理與 φ 的定義、性質、公式的權威速查；φ(60)=16、乘性、質數冪公式都可在此核對。

### 孿生質數與有界間隙

- **Quanta Magazine, "Together and Alone, Closing the Prime Gap"（2013-11）**（quantamagazine.org）—— 服務 ch12。張益唐故事與 Polymath8 群眾協作壓低上界的第一手敘事，可讀性極高；讀它對「7000 萬→246」這段的人物與時間線。

- **張益唐, "Bounded gaps between primes," *Annals of Mathematics* 179 (2014)**（arxiv.org 有 Polymath 的相關回顧 1409.8361）—— 服務 ch12。原始論文；不必細推，讀引言看他自己怎麼陳述「有界間隙」的精確意義。

- **Wolfram MathWorld, "Twin Prime Conjecture" 與 "Twin Primes Constant"**（mathworld.wolfram.com）—— 服務 ch12。孿生質數常數 C₂≈0.6601618 與 Hardy–Littlewood 估計式的速查，核對本章的密度啟發。

### 黎曼假設

- **Clay Mathematics Institute, "Riemann Hypothesis"**（claymath.org/millennium/riemann-hypothesis/）—— 服務 ch13/ch19。千禧年大獎問題的官方頁，RH 的正式陳述與懸賞；確認「RH 仍未解（2026-06）」的權威狀態，不要信網路上的「已證」宣稱。

- **Marcus du Sautoy, *The Music of the Primes*（2003）**—— 服務 ch13。「質數的音樂」這個隱喻的源頭與普及之作，把 ζ 零點與質數分布的關係講成一段歷史故事，幾乎不用公式；建立「零點＝諧波」整體圖像的最佳科普書。

- **plus.maths.org, "The Music of the Primes"（du Sautoy 科普短文）**—— 服務 ch13。比整本書短得多的免費版本，把顯式公式「主項＋波」的圖像講得很清楚；趕時間的話讀這篇。

### 驗證 vs 證明

- **Wikipedia, "Skewes' number"**（en.wikipedia.org/wiki/Skewes%27_number）—— 服務 ch14。Littlewood 1914 變號定理、Skewes 1933 上界、後續收窄到約 1.39×10^316 的時間線；讀它確認「反超無窮多次卻沒人直接算到第一個」這個鏡像版「驗證 ≠ 證明」。

- **Wikipedia / MathWorld, "Pólya conjecture"**（en.wikipedia.org / mathworld.wolfram.com）—— 服務 ch14。Pólya 1919、Haselgrove 1958 推翻、最小反例 n=906,150,257（Tanaka 1980）；核對「前九億都對才崩」這個本章最有殺傷力的數字。

- **Oliveira e Silva, Herzog, Pardi, "Empirical verification of the even Goldbach conjecture ... up to 4·10^18," *Mathematics of Computation* 83 (2014)**（作者頁 sweet.ua.pt/tos）—— 服務 ch14。哥德巴赫驗證到 4×10^18 的權威來源；感受「世界級的驗證工程」與「仍是未證」之間那道牆。

### 沒有公式，卻有規律

- **Wolfram MathWorld, "Prime-Generating Polynomial" 與 "Euler Prime"**（mathworld.wolfram.com）—— 服務 ch15。n²−n+41 與「歐拉幸運數」（2,3,5,11,17,41）的速查，核對本章的數值與「沒有多項式對所有 n 吐質數」的陳述。

- **Wikipedia, "Formula for primes"**—— 服務 ch15。Mills、Wilson 定理改寫、Matiyasevich 多項式——把各種「質數公式」一次攤開，每一條都示範「存在卻沒用」是怎麼回事。

- **Wikipedia, "Mills' constant"**—— 服務 ch15。Mills 1947 的證明、A≈1.30637… 要假設黎曼假設才算得出、「存在但不可計算」的公式長什麼樣。

### 梅森質數與最大質數紀錄

- **GIMPS 官方公告頁 "Mersenne Prime Discovery — 2^136279841−1 is Prime!"**（mersenne.org/primes/press/M136279841.html）—— 服務 ch16/ch19。M52 的第一手發現公告，Luke Durant、GPU、A100/H100 覆驗、41,024,320 位這些數字的權威出處；也看 GIMPS 怎麼自稱 "52nd known"。

- **mersenne.org 的 "The Math" 頁**（mersenne.org/various/math.php）—— 服務 ch16。GIMPS 使用的數學：Lucas–Lehmer、預篩、FFT 大數乘法的入門整理；想知道「梅森數為什麼好驗」就讀這頁。

- **Terence Tao, "The Lucas–Lehmer test for Mersenne primes"**（terrytao.wordpress.com，2008）—— 服務 ch16。陶哲軒寫的 Lucas–Lehmer 檢驗背後數論的清晰講解；想看「為什麼這個迴圈能判定質數」的證明讀它（本書不展開的那一塊）。

- **Wikipedia, "Euclid–Euler theorem"**—— 服務 ch16。完全數與梅森質數一一對應的定理陳述與歷史（歐幾里得 IX.36 的「if」、歐拉補的「only if」）；核對本章 6、28、496 的對應。

### RSA 與密碼學

- **Wikipedia, "RSA (cryptosystem)"**（en.wikipedia.org/wiki/RSA_(cryptosystem)）—— 服務 ch17。RSA 發展史（Cocks 1973 祕密、RSA 1977 公開）的速查，與本章史實對照。

- **RSA Factoring Challenge / 整數分解紀錄（Paul Zimmermann 維護）**（members.loria.fr/PZimmermann/records/factor.html）—— 服務 ch17。想對「分解到底多難」有具體重量感，看 RSA-250（829 位，2020-02，約 2700 核心年）這類紀錄——古典電腦分解的公開最大者（2026-06）。

### 烏拉姆螺旋

- **Wikipedia, "Ulam spiral"**（en.wikipedia.org/wiki/Ulam_spiral）—— 服務 ch18。來歷、對角線對應二次多項式（4n²+bn+c）、避開小質因數的解釋都在這；讀「History」與「Explanation」兩節。

- **Wolfram MathWorld, "Prime Spiral"**（mathworld.wolfram.com/PrimeSpiral.html）—— 服務 ch18。較數學的條目，含對角線與質數密集二次式的對照；想看更多變體（不同中心、不同起點）的讀這條。

- **Wikipedia, "Bunyakovsky conjecture"**—— 服務 ch18/ch15。本章「沒有任何二次多項式被證明能生成無窮多質數」的出處——連 n²+1 都還沒解（蘭道四大問題之一）；讀它理解螺旋的線「看得見卻證不了」的根本原因。

### 收官與總覽

- **Terence Tao, "Structure and Randomness in the Prime Numbers"**（可由 terrytao.wordpress.com 搜尋進入）—— 服務 ch20。本章「結構與隨機的二分」「質數的偽隨機性」直覺的權威來源；把「確定卻表現得像隨機」這件事講得最透。是想往深一層看「質數為什麼難」的最好下一站（2026-06 查證為其長期講題）。

- **Clay Mathematics Institute, 千禧年大獎問題頁面**（claymath.org/millennium）—— 服務 ch13/ch19/ch20。七個千禧年問題的官方介紹；ch19 的「已解 vs 未解」對帳表所有「未解」的官方依據都在這裡。

### 教科書與系統性資源

- **G. H. Hardy & E. M. Wright, *An Introduction to the Theory of Numbers*（牛津大學出版社）**—— 服務全書。英文世界最經典的數論入門，含 FTA、質數無窮、篩法、同餘、費馬、PNT 等所有本書主題的嚴格版；想從這本書的欣賞進到嚴格數論，從 Hardy–Wright 入手。

- **Tom Apostol, *Introduction to Analytic Number Theory*（Springer）**—— 服務 ch07/ch13。解析數論的標準教材，PNT 的完整證明（包含 ζ 在 Re(s)=1 上無零點的論證）與黎曼 ζ 函數章節在此；本書只用結果的那些，這本書給證明。

- **Wolfram MathWorld, "Prime Counting Function"**（mathworld.wolfram.com/PrimeCountingFunction.html）—— 服務 ch06。π(x) 的定義、階梯性質、各種逼近（x/ln x、Li(x)）並列；想看更多基準值與歷史脈絡從這裡入手。

---

讀到這裡，這趟旅程的地圖、捷徑、鄰書與外部資源都在你手上了。回到那個分解 60 = 2²·3·5——它在 ch01 登場、在 ch02 揭示唯一性、在 ch09 算 gcd、在 ch11 算 φ(60)=16、在 ch19 對帳全書、在 ch20 收束脊椎。質數定理告訴你：「個別質數測不準，整體計數卻有鐵律。」往書架外走，從上面這份清單挑下一步。

數論沒說「質數毫無規律」，也沒說「質數完全可預測」——它說的是：**即使個別位置完全確定，整體行為也服從統計律；即使 PNT 已証，細節（RH、孿生）仍是謎。** 這本書要你帶走的，就是這一句——以及在那個「亂與律共存」的邊界上站一站的震撼。
