# 附錄 C — 延伸閱讀總地圖

這份地圖把全書 19 章末尾散落的「延伸閱讀」，連同 landscape 查證過的資源，收成一張可以照著走的下山路線圖。你站在 ch19 的觀景台上，回頭看那條從牧羊人配對一路走到哥德爾自我指涉的脊椎；往前看，有三條岔路——**往邏輯與可計算走**（對角線家族的後代：停機問題、不完備、型別論）、**往基礎與公理走**（把直覺補成嚴格：公理集合論、AC、CH、forcing、模型論）、**往欣賞與哲學走**（把驚嘆挖到底：數學史、康托爾傳記、無限的哲學、科普影片）。

每條路線下的每一筆都附一句話：**為什麼值得讀、讀哪一段、對應本書哪章**。所有連結只收書中各章或 landscape 已標為查證過的（多數標「2026-06 確認在線」）；連結狀態會隨時間變動，最終以「能不能搜到那個標題」為準。沒附死連結的經典，用「作者＋年份＋標題」記，搜尋即可。

讀法建議：時間有限的話，先跳到本附錄最後的「**如果只看三樣**」——那是跨三條路線各挑一個的最短路徑。三樣看完還想走遠，再回到路線裡挑。

---

## 路線一：往邏輯與可計算走——對角線家族的後代

這條路是本書脊椎的自然延伸。對角論證（ch04）、冪集定理對角集（ch06）、羅素悖論（ch10）、哥德爾不完備（ch16）、停機問題（ch16）是**同一條對角線**的五次化身；走這條路，你會看到它在計算理論裡繼續開枝散葉。對一個工程師來說，這也是最有「字面同一件事」回報的一條（見 ch18）。

- **康托爾 1891 原論文〈Über eine elementare Frage der Mannigfaltigkeitslehre〉（論流形論中的一個初等問題）。** 對角論證的源頭，出乎意料地短。康托爾原本就是對任意「兩個元素的特徵函數族」陳述，比「實數不可數」更一般——等於他自己埋好了冪集定理。入口讀 Wikipedia「Cantor's diagonal argument」條目（2026-06 確認在線）的原文脈絡與英譯導讀即可。對應 ch04（定版那條對角線）、ch06（一般化）。

- **史丹佛哲學百科「Gödel's Incompleteness Theorems」**（plato.stanford.edu/entries/goedel-incompleteness/，2026-06 確認在線）。最權威也最克制的入口，把「G 說自己不可證」這種非正式說法、和精確的對角化引理講清楚，並逐條破除誤讀（真理不可知／數學不一致／凡事不可證／拿去證上帝）。你想確認自己沒把定理講過頭時，回來對這篇。對應 ch16——這是全書最容易翻車的單一主題，先讀它再跟人講。

- **〈Did Turing prove the undecidability of the halting problem?〉**（arXiv:2407.00680，2026-06 確認在線）。專門考據「停機問題」這個名字不在圖靈 1936 原文、是後人（戴維斯 1958）命名的措辭史。你之後跟人講這個故事時，這篇讓你不會把名字繫錯到圖靈頭上。對應 ch16（停機問題＝對角線的計算版）。

- **Charles Petzold,《The Annotated Turing》。** 圖靈 1936 原論文〈On Computable Numbers〉的逐行導讀。想把「對角論證→停機問題→不可計算函數」這條脊椎，從康托爾這側親手走到圖靈那側、看圖靈本人怎麼用對角線造出「可定義但不可計算」的序列，這是最好的一本（2026-06，內容為穩定史料；圖書館／電子書皆易得）。對應 ch16、ch18。

- **Wikipedia,〈Rice's theorem〉**（en.wikipedia.org/wiki/Rice%27s_theorem，2026-06 確認在線）。萊斯定理的精確陳述（非平凡語義性質不可判定）與證明，看它怎麼把任意非平凡語義性質的判定**化約**到停機問題——「沒有萬能靜態分析器」最該讀的一頁。對應 ch18（對角線的工程日常）。

- **Wikipedia,〈Incompressible string〉／Kolmogorov complexity**（en.wikipedia.org/wiki/Incompressible_string，2026-06 確認在線）。不可壓縮字串與「幾乎所有字串不可壓縮」的鴿籠論證，跟本書「程式可數、函數不可數」是同一個鴿籠精神，也是「不存在完美無損壓縮」的數學底。對應 ch18。

- **SEP,「Intuitionistic Type Theory」**（plato.stanford.edu/entries/type-theory-intuitionistic/，2026-06 確認在線）。構造主義在現代的復活地：Curry–Howard 對應、型別論、Coq／Lean／Agda 的哲學地基。想知道「證明即程式」這句話的字面意思，這是橋。對應 ch17、ch18（版本與生態狀態屬時效細節，以「廣為使用、進入主流」概括即可）。

---

## 路線二：往基礎與公理走——把直覺補成嚴格

本書全程紙筆推演、刻意不擺完整證明（CSB 只給骨架、forcing 只給 taste、ℝ 的構造與測度論明寫略過）。如果你讀完癢起來，想看「工程師的直覺」升級成「數學家的嚴謹」長什麼樣，走這條。第一站是兩本經典教科書，再往公理化集合論的爭議與獨立性深處走。

- **Paul Halmos,《Naive Set Theory》（1960）。** 書名叫「Naive」其實講的正是 ZFC，但用最少的形式包袱、把公理當工具一條條引入立刻拿來用。薄、狠、無廢話——「一一對應定義一樣多」「公理＝限制概括」這些本書的種子，這裡有最精簡的數學語言版。本書是它的「直覺與驚嘆」版，兩者對照讀很划算。對應 ch01（cardinality 開頭）、ch11（第 1–11 節對應 ZFC）。

- **Thomas Jech,《The Axiom of Choice》（Dover 重印）。** 想看 AC 的完整技術版（含獨立性證明、各種弱版的層級）。本書不證的細節都在這；當參考書、不必通讀。對應 ch12。

- **史丹佛哲學百科,「Zermelo's Axiomatization of Set Theory」**（plato.stanford.edu/entries/zermelo-set-theory/，2026-06 確認在線）。分離公理 1908 年的原始動機、策梅洛 1904 用 AC 證良序定理引爆爭議的第一手脈絡。對應 ch09（良序定理伏筆）、ch11（分離公理為修羅素而生）、ch12（AC 的歷史現場）。

- **史丹佛哲學百科,「The Axiom of Choice」**（plato.stanford.edu/entries/axiom-choice/，2026-06 確認在線）。AC 最權威的哲學與數學綜述。讀「The Axiom」與「Maximal Principles」把三張臉（選擇函數／良序／佐恩）的等價看得更細；構造性爭議在「The Axiom of Choice and Logic」。對應 ch12。

- **Encyclopedia of Mathematics,〈Schroeder–Bernstein theorem〉**（encyclopediaofmath.org/wiki/Schroeder%E2%80%93Bernstein_theorem，2026-06 確認在線）。CSB 歸屬史的權威整理，看清「康托爾述用 AC／戴德金 1887 未發表／伯恩斯坦 1897／施洛德 1898 有瑕」這個名字掛三人卻帳算不平的定理。完整證明（追蹤軌道、鏈分三型）可配 Wikipedia「Schröder–Bernstein theorem」的「Proof」一節。對應 ch07。

- **史丹佛哲學百科,「The Continuum Hypothesis」**（plato.stanford.edu/entries/continuum-hypothesis/，2026-06 確認在線）。CH 與其獨立性最權威的綜述：哥德爾（L）與科恩（forcing）各證了什麼、以及「靠新公理決定 CH」的現代爭論。對應 ch14（問題的形狀）、ch15（獨立性與現代態度）。

- **Akihiro Kanamori,〈How Gödel Transformed Set Theory〉**（Notices of the AMS, 2006；math.bu.edu/people/aki/12.pdf，2026-06 確認在線）。哥德爾用 L 證 `Con(ZF) ⇒ Con(ZFC+GCH)` 的第一手脈絡。要弄清「相對一致性、不是證 CH 為真」這條高風險線，讀這篇最穩。對應 ch15。

- **Timothy Chow,〈A Beginner's Guide to Forcing〉**（arXiv:0905.2539，2026-06 確認在線）。替「想再多懂一點 forcing、但還不想啃完整技術」的人寫的橋。本書只給 taste，這篇把「為什麼能加新實數又不矛盾」講到你能再深一層，且刻意對非專家友善。對應 ch15。

- **Scott Aaronson,〈The Complete Idiot's Guide to the Independence of the Continuum Hypothesis〉**（scottaaronson.blog/?p=4974，2026-06 確認在線）。一個電腦科學家寫給工程師口味讀者的獨立性導讀，語氣和本書最近。看它怎麼把哥德爾＋科恩串成一個故事。對應 ch15。

- **R. Gardner（ETSU 講義）,〈Nonmeasurable sets and the Banach-Tarski Paradox〉**（faculty.etsu.edu/gardnerr/5210/banach-tarski.pdf，2026-06 確認在線）。把「不可測集 → 維塔利 → 巴拿赫–塔斯基」一條線講得最乾淨的教學講義。本書明說不證的群論（自由群 F₂ 分解）與維塔利論證完整版都在這。對應 ch13。

---

## 路線三：往欣賞與哲學走——把驚嘆挖到底

如果你讀這本書最被打動的不是「我證得出來」，而是「人類竟然想得出這個」，那打動你的是思想史與哲學。這條路把無限放回它誕生的歷史現場與爭論裡，也是本書精神最近的一條。

- **J. W. Dauben,《Georg Cantor: His Mathematics and Philosophy of the Infinite》。** 康托爾的權威傳記。它把康托爾的數學、哲學、與那場被嚴重渲染的精神疾病傳說的真相都考據清楚——本書對康托爾生平的克制寫法（雙相情感障礙是內因、學術壓力是誘因非病因），正是以 Dauben 這一系考據為錨。對應 ch04、ch17、ch19（全書的康托爾敘事）。

- **Hilbert,〈Über das Unendliche〉（論無限，1925 演講／1926 刊出）。** 「沒有人能把我們逐出康托爾為我們創造的樂園」的原始出處，也是形式主義對無限最有力的辯護書。讀它如何把「無限存不存在」這個形上學問題、改寫成「形式系統一致不一致」這個技術問題——這一步是 20 世紀數學哲學的關鍵轉折。（2026-06，依 landscape §20。）對應 ch17、ch19。

- **Galileo,《Two New Sciences》（1638），「第一天」談無限與連續的段落。** 伽利略悖論的原始出處，看他怎麼在「平方數一一對應」和「整體大於部分」之間，選擇了放棄比較——一個人離真相只差一句話卻沒說出口。讀那段對話（Salviati 與 Simplicio）比讀任何轉述都有力。英譯多有公版（如 Dover 版）。對應 ch01。

- **George Gamow,《One Two Three… Infinity》（1947）。** 讓希爾伯特旅館舉世皆知的那本科普書（中譯常作《從一到無窮大》）。第 1 章談無限與可數，文字活潑、是這個比喻的原始普及來源——讀它順便對照本書把歸屬講清楚的版本（希爾伯特 1924 口頭講、伽莫夫筆下普及）。對應 ch02。

- **Hofstadter,《Gödel, Escher, Bach》。** 把哥德爾的自我參照、對角化、quine、遞迴串成一整本書的科普經典。它正是用「自我指涉」這條線把邏輯、藝術、音樂縫起來，跟本書「同一條對角線」的脊椎是親戚。當你想把不完備的震撼往更廣處延伸時讀它（厚，但值得）。對應 ch16。

- **史丹佛哲學百科,「Intuitionism in the Philosophy of Mathematics」**（plato.stanford.edu/entries/intuitionism/，2026-06 確認在線）。直覺主義最權威的當代綜述：布勞威爾為什麼拒絕排中律、選擇序列如何重建連續統、代價在哪。想真正理解「存在＝可構造」這條線，從這裡讀。對應 ch17。

- **Veritasium／Numberphile 的對角論證與無限影片。** YouTube 上多支以視覺方式走對角線（搜「Cantor diagonal argument」即可，2026-06）。優點是把「翻轉對角線」的動畫做得很直觀，適合在你自己重講之前先看一遍別人怎麼講；缺點是幾乎都不處理 0.4999…＝0.5000… 雙重表示的坑，看的時候自己補上本書 ch04 的「只在 {3,7} 裡選」規則。對應 ch04。

- **史丹佛哲學百科,「Russell's Paradox」**（plato.stanford.edu/entries/russell-paradox/，2026-06 確認在線）。羅素悖論最權威的入口。讀「The Paradox」與「Frege」兩節，把本書的兩段論和弗雷格的反應對照一次；它也講了策梅洛的獨立發現。對應 ch06（埋下的對角集 D）、ch10（正面拆開）。

---

## 鄰書銜接點：書架上接著走的一本

本書是書架的一格，旁邊那本《馴服無限》（微積分）接得上——它不是延伸閱讀的「外人」，而是本書刻意留洞、由它補完的鄰居，也是同一種勝利的另一個方向。

- **《馴服無限》全書。** 這本書馴服的是「無限大／多少」，把「一樣多」操作化成一一對應；那本書馴服的是「無限小／逼近」，把無限操作化成極限——**同一招學了兩遍**。具體銜接：康托爾為什麼走進集合論（三角級數唯一性與點集）在它的 ch11／ch14；ℝ 的構造（Dedekind 切割／Cauchy 序列、0.999…＝1）在它的 ch03／ch14，本書 ch03–ch05 用到 ℝ 的性質時一句話帶過、正主在那裡；它處理的分析學 ∞（極限、過程）與本書的 ℵ₀（大小、對象）是兩個無限符號，讀完兩本你會徹底分清。對應 ch01–ch05、ch19。

---

## 如果只看三樣

時間只夠看三樣，就跨三條路線各挑一個——一個把脊椎走到計算的盡頭，一個把直覺釘成嚴格，一個把驚嘆放回歷史：

1. **（路線一）史丹佛哲學百科「Gödel's Incompleteness Theorems」。** 全書高潮二（ch16）最該守住、也最容易講過頭的一篇。讀完它，你對「不完備到底說什麼、不說什麼」的把握，會勝過市面 99% 的轉述——而這正是飯桌上最常被講錯的數學定理。

2. **（路線二）Paul Halmos,《Naive Set Theory》。** 最友善的「升級到嚴格」單冊入口。薄薄一本，把本書十九章的直覺用最精簡的數學語言重講一遍——對照讀，你會看見自己的直覺其實一直站在正確的形式骨架上。

3. **（路線三）J. W. Dauben,《Georg Cantor》。** 如果這本書最打動你的是「人類竟然想得出這個」，這本權威傳記把那個人、那場爭論、那個被渲染的瘋癲傳說的真相都還原給你。讀完它，你會用更克制也更尊重的方式，把康托爾的故事講給下一個人聽。
