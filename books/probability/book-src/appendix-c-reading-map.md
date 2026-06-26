# 附錄 C — 延伸閱讀總地圖

這份地圖把全書 23 章散落在各章末「延伸閱讀」的資源，連同 landscape 驗證過的經典論文，收成一張可以照著走的下山路線圖。你站在 ch23 的觀景台上，下面有三條岔路——**往嚴格**（把直覺補成證明）、**往應用**（把欣賞換成能算）、**往欣賞**（把驚嘆挖到底）。每條路線下的每一筆都附一句話：**為什麼值得讀、從哪一段切進去**。所有連結只收書中各章或 landscape 已標為查證過的；沒把握的明白標「（2026-06，未驗證）」。經典論文用「作者＋年份＋標題」記，不附可能失效的連結。

讀法建議：先看本附錄最後的「**如果只看三樣**」——那是給時間有限的你的最短路徑。三樣看完還想走遠，再回到三條路線裡挑。

---

## 路線一：往嚴格——把「應該對」補成「我證得出來」

本書全程紙筆推演、刻意不擺證明（測度論、強大數法則的證明、特徵函數版 CLT 都明寫略過）。如果你讀完癢起來，想看「工程師的嚴謹」升級成「數學家的嚴謹」長什麼樣，走這條。

- **Grinstead & Snell,《Introduction to Probability》（免費合法 PDF，American Mathematical Society 與 Dartmouth 釋出）**（2026-06，AMS 開放下載）——本書最該先碰的嚴格版。例子多、不裝高深，幾乎每一個本書的核心都有它的形式化對應：第 8 章用車比雪夫證弱大數法則（接本書 ch13）、第 11 章馬可夫鏈（接 ch21，自足不掉進測度論）、第 12 章隨機漫步與賭徒破產（接 ch20，公正與不公正兩種公式都推完）。想把哪一章補硬，就翻對應那章。

- **Blitzstein & Hwang,《Introduction to Probability》（2nd ed., CRC Press；免費電子版 probabilitybook.net，配哈佛 Stat 110 的 34 小時免費課程影片）**（2026-06，免費版與課程長期公開）——本書反覆引用的「能算版」教材。第 3、4 章把「隨機變數是函數」「指示變數與線性性」講到位（接 ch07、ch08）；它的 `|ρ|≤1` 柯西–施瓦茲證明、`Var(X+Y)` 交叉項展開（接 ch09、ch10）正是本書只給直覺、它給推導的地方。風格活潑、也講悖論與 PageRank，是「直覺→能算」轉換最順的一本。

- **Kolmogorov,《Grundbegriffe der Wahrscheinlichkeitsrechnung》（1933）——讀導讀而非原書**：找 Shafer & Vovk「The origins and legacy of Kolmogorov's Grundbegriffe」（arxiv.org/abs/1802.06071，2026-06 可查）。原書德文、偏測度論，不必硬啃；導讀讓你看見公理化當年到底解決了什麼焦慮（接 ch02 三公理、ch22 測度論門口）。這是「往嚴格」這條路的盡頭風景——機率被釘進測度論的那一刻。

- **Keith Conrad,「The Gaussian Integral」（kconrad.math.uconn.edu，2026-06，已查證）**——只有幾頁，把 ∫e^(−x²/2)dx=√(2π) 用好幾種方法算給你看。如果你對 ch15「為什麼鐘形下面積是 √(2π)、π 怎麼跑進機率」不滿足於直覺，這份是下一站（數學系大二程度，寫得乾淨）。更完整的「機率即面積」微積分底，見本附錄「鄰書銜接點」的《馴服無限》。

- **Hans Fischer,《A History of the Central Limit Theorem》（Springer, 2011）**——從棣美弗 1733 到 Lyapunov、Lindeberg 的完整學術史。偏學術，當參考不當入門；想知道「一份七頁小冊到嚴格定理為什麼走了快兩百年」就讀它（接 ch14）。

---

## 路線二：往應用——把欣賞換成「我會用、且不會被它騙」

本書給你直覺與故障視角，但沒教統計軟體、沒做題庫、沒展開因果框架。如果你要把這些直覺真的用在工作與資料上，走這條。

- **Blitzstein & Hwang,《Introduction to Probability》（同上，probabilitybook.net）**——「往嚴格」與「往應用」共用這一本：它既有推導也有大量可操作的招牌例子。對應用者最划算的是它的指示變數與線性性章節（ch08 的延伸），看完你會開始到處用線性性繞過硬計數。

- **David Spiegelhalter,《The Art of Statistics》（中譯《統計，讓數字說話》）**——當代最會講「資料怎麼來的，比資料多大更重要」的統計學家之一。讀他談 sampling frame 那段（接 ch16 抽樣）。這本是「把統計用在真實資料、又保持誠實」的最佳單冊入門。

- **Gerd Gigerenzer,《Calculated Risks》（中譯《如何不被數字騙》一類）**——把條件機率與 `P(A|B)≠P(B|A)` 的混淆講成日常決策災難（醫檢、法庭），用自然頻率法拆解（接 ch04、ch05）。原始論文是 **Gigerenzer & Hoffrage (1995),「How to Improve Bayesian Reasoning Without Instruction: Frequency Formats」, _Psychological Review_ 102(4):684–704**（照 landscape）——想看「把機率換成『1000 人中…』，貝氏直覺就回來」那組數字的出處讀它。

- **Judea Pearl & Dana Mackenzie,《The Book of Why》（中譯《因果革命》）**——本書「相關 ≠ 因果」只到「三條岔路＋隨機化直覺」為止（多變量與因果框架是全域不涵蓋的洞）。想正式地從資料推因果——confounder、do-演算、因果圖——這本是現代因果推論的科普入口（接 ch10、ch19）。

- **複現危機的一手文獻（往應用者必讀的「反面教材」，全部照 landscape）**：
  - **Ioannidis (2005),「Why Most Published Research Findings Are False」, _PLoS Medicine_ 2(8):e124**——元科學的奠基文獻，核心論證就是你已經會算的貝氏篩檢題（接 ch05、ch19）。
  - **Simmons, Nelson & Simonsohn (2011),「False-Positive Psychology」, _Psychological Science_ 22(11):1359–1366**——「研究者自由度／p-hacking」一詞的出處，把名目 5% 假陽性推到最壞約 60% 的那篇模擬；末尾「六條揭露要求」就是解藥（接 ch18、ch19）。
  - **Open Science Collaboration (2015),「Estimating the Reproducibility of Psychological Science」, _Science_**——原研究 97% 顯著、複現僅約 36% 的那張散點圖（接 ch18、ch19）。
  - **Wasserstein & Lazar (2016),「ASA Statement on p-Values」, _The American Statistician_ 70(2):129–133**——學界正式承認「招牌數字一直被讀錯」的歷史文件，讀第 2、5 條（接 ch18、ch19）。
  - **「Before p<0.05 to Beyond p<0.05」（_The American Statistician_ 2018, tandfonline，已查證）**——把 0.05 的身世講清楚，治好「0.05 是物理常數」這個病（接 ch18）。

- **信賴區間的誤讀（用之前先治病）**：**Hoekstra et al. (2014),「Robust misinterpretation of confidence intervals」, _Psychonomic Bulletin & Review_**——實測學生與研究者都系統性誤讀 CI 的經典研究。配 PMC「Continued misinterpretation of confidence intervals」（landscape 引）一起讀，把「為什麼這麼難改正」講透（接 ch17）。

---

## 路線三：往欣賞——把驚嘆挖到底

如果你只想再被拍一次大腿，看人類直覺如何在隨機面前崩壞、看一個概念誕生的歷史現場，走這條。這也是本書精神最近的一條路。

- **3Blue1Brown（Grant Sanderson），機率與統計系列（YouTube）**（2026-06，頻道持續更新，建議搜尋頻道確認連結）——跟本書同一種「先給直覺、再給數學」的精神，動態版。尤其「**But what is the Central Limit Theorem?**」（2023）把 ch14 的「抹平」直覺做給你看；「**Bayes theorem, the geometry of changing beliefs**」把 ch05 的「後驗＝真陽性佔全部陽性的比例」畫成面積；「**Why π is in the normal distribution**」接 ch15。免費、看完刻進腦子。

- **Daniel Kahneman,《快思慢想》（Thinking, Fast and Slow, 2011）**（2026-06，繁中譯本通行）——把本書「直覺的陷阱」整條線往認知科學深挖。Kahneman 與 Tversky 一輩子研究的就是人腦為什麼在機率前系統性崩壞（代表性捷思、基率忽視都出自他們，接 ch05、ch19）。讀完你會更看得起本書故障視角背後的科學。

- **Sharon Bertsch McGrayne,《The Theory That Would Not Die》（中譯《統計，改變了世界》系出此脈）**（2026-06，書目未逐一驗證）——講貝氏定理兩百年浮沉，從遺稿、二戰破密碼到現代復興，可讀性極高。想把「頻率派 vs 貝氏派世紀分裂」當故事讀完，從這本進（接 ch06）。

- **Jordan Ellenberg,《How Not to Be Wrong》（中譯《數學教你不犯錯》）**（2026-06，已查證歸屬，Ellenberg 引述 Wald／SRG）——瓦德飛機彈孔（倖存者偏誤）那一章是全書開場，比任何教科書都生動，讀第一章就值回票價（接 ch16）。

- **Darrell Huff,《How to Lie with Statistics》（1954）**——薄薄一本老書，「偏誤的樣本」那一章到今天一個字都不過時。當「統計版的反模式手冊」讀，每個看 dashboard 的人都該翻（接 ch16、ch19）。

- **Tyler Vigen,《Spurious Correlations》（網站 tylervigen.com 與同名書，2026-06，已查證）**——那些 ρ>0.99 卻荒謬絕倫的配對（緬因州離婚率 vs 人造奶油）。當笑話讀，看完你對「相關係數高」會永久免疫（接 ch10）。

- **悖論與謬誤的權威條目（精確陳述很重要，全部照 landscape）**：
  - **Steve Selvin (1975) 的原始信＋vos Savant (1990-09-09, _Parade_) 專欄論戰**——蒙提霍爾「換可使勝率加倍」引來約一萬封來信（含許多博士）說她錯，但她對。看一群受訓過的人集體翻車的震撼（接 ch06）。
  - **Stanford Encyclopedia of Philosophy,「The St. Petersburg Paradox」**（plato.stanford.edu，已查證）——讀「Bernoulli's solution」一節，確認它是效用問題、不是算錯（接 ch08）。
  - **Miller & Sanjurjo (2018),「Surprised by the Hot Hand Fallacy?」, _Econometrica_**（已查證）——熱手 2018 翻案：去掉選擇偏差後，三十年「熱手是謬誤」的定論被推翻。這個轉折本身就是獨立的驚嘆點（接 ch13）。
  - **Wikipedia,「Bertrand paradox (probability)」/「Boy or girl paradox」/「Birthday problem」/「Gambler's ruin」**（2026-06，可查）——三種隨機弦各得一答、兩孩問題的歧義、生日問題的逼近公式、賭徒破產與翻本法的必敗結構。圖解清楚，比文字快（接 ch02、ch03、ch20）。

- **科學史單篇佳作**：
  - **John D. Cook,「How the central limit theorem began」（johndcook.com, 2010，已查證）**——棣美弗 1733 怎麼從算硬幣意外撞出常態（接 ch14）。
  - **Brian Hayes,「First Links in the Markov Chain」, _American Scientist_ (2013)**（已查證）——馬可夫鬥嘴故事寫得像偵探小說，讀「the war on free will」與奧涅金兩節（接 ch21）。
  - **Brin & Page (1998),「The Anatomy of a Large-Scale Hypertextual Web Search Engine」**（照 landscape）——PageRank 原始論文，讀第 2.1 節隨機衝浪者與穩態（接 ch21）。

---

## 如果只看三樣

時間有限就看這三樣，分別補你最該補的一塊：

1. **Blitzstein & Hwang,《Introduction to Probability》（免費，probabilitybook.net ＋哈佛 Stat 110 影片）**——一本同時打通「往嚴格」與「往應用」：把本書全程的直覺升級成帶推導與習題的能算版，風格還活潑不死板。只挑一本教科書，就是它。

2. **3Blue1Brown「But what is the Central Limit Theorem?」（YouTube，2023）**——一支影片補滿「往欣賞」：把全書最大驚嘆（ch14 的「不管原分布長相、加總都收斂到同一條鐘」）做成動畫。免費、20 分鐘、看完那個直覺再也忘不掉。

3. **Wasserstein & Lazar (2016),「ASA Statement on p-Values」（_The American Statistician_ 70(2)）**——一份六頁的官方文件補滿「故障視角」：一個專業學會正式承認招牌數字被全世界讀錯。把 ch18、ch19 的故障視角從「本書作者的提醒」升級成「整個學界的共識」。

---

## 鄰書銜接點：書架上接著走的三本

本書是書架的一格，旁邊三本書接得上——它們不是延伸閱讀的「外人」，而是本書刻意留洞、由它們補完的鄰居。各標出「從本書哪一章接過去最順」。

### 《馴服無限》（微積分）——補完「機率即面積」與「怪獸函數」

本書全程把「機率＝曲線下面積」「機率＝密度的積分」當工具用，卻沒推導積分本身——那是微積分的主場。

- **從 ch15（常態之美與機率即面積）接過去最順**。本書用「機率即面積」查尾端、反查 CDF，但沒講高斯積分 ∫e^(−x²)dx=√π 為什麼會冒出 π。《馴服無限》把積分、曲線下面積、二維積分換極座標讓 π 從圓那裡進來這整套講透（積分基礎在它的 ch07「積分」與 ch08「微積分基本定理：面積＝斜率反過來」；「機率即面積」是它收尾把工具接回機率的脈絡，章號以該書當前版本為準）。ch12、ch14 用到面積時也都指向這裡。
- **ch22（布朗運動）接它的 ch13「怪獸函數：連續但處處尖刺」**——這條銜接最該先讀。魏爾斯特拉斯手刻的「處處連續、處處不可微」函數，正是布朗路徑病態的「確定性雙胞胎」：那本書手工打造的反例，本書用隨機性自動量產，是同一頭怪獸的兩張臉。

### 《佇列論》——補完 Poisson 過程、指數分布、Markov/CTMC 的運算

本書把 Poisson 分布、指數分布、馬可夫鏈當「靜態快照」欣賞，刻意不在時間軸上展開運算；那一整套到達過程與排隊計算，是《佇列論》的主場。

- **從 ch11（離散分布，卜瓦松）與 ch12（連續分布，指數）接過去最順**。本書的卜瓦松是稀有計數的靜態形狀、指數是無記憶的等待時間；《佇列論》ch04（指數分布：排隊世界的原子）、ch05（Poisson 過程：到達的標準模型）把它們接到到達間隔、佇列長度、Little's law 那一整套運算——靜態快照變成動態影片。
- **ch21（馬可夫鏈）接它的 ch06（Markov chain）、ch07（CTMC 與生滅過程），更進階的排隊網路在它的 ch16（Jackson networks）**。本書只給穩態的直覺；要動手算系統的吞吐與延遲、把馬可夫鏈當運算工具，去那裡。

### 《把系統寫成定理》（TLA+ 與形式化方法）——∀∃ 量詞與「我有多確定」的對抗結構

這條銜接最隱微也最迷人：信賴區間與 p 值的正確意義，骨子裡是一個**量詞結構**，跟 TLA+ 的 ∀∃ 是同一種思考。

- **從 ch17（估計與信賴區間）接過去最順**。「95% 信賴區間」的正確意義是頻率派的量詞陳述：**對所有真值**，用這套程序反覆抽樣，**存在 95% 的比例**會涵蓋真值（Neyman 1937，照 landscape）——它說的是「**製造區間這個程序**的長期涵蓋率」，不是「**這一條**區間」的機率。這個「∀真值・程序保證涵蓋率」的結構，跟 TLA+ 用 ∀∃ 量詞刻畫「所有執行路徑都滿足某性質」是同構的對抗式思考：你不是斷言某個個案，而是斷言一個程序對所有情況的保證。ch18 的 p 值（「假設 H₀，看資料有多極端」的反證法結構）同理——兩者都是「先固定一個全稱假設，再量化證據」，與形式化方法「先寫不變量、再驗所有狀態」是同一種腦袋。讀完本書 ch17、ch18，再去《把系統寫成定理》看 ∀∃ 怎麼把「正確性」變成可驗證的斷言，你會對「精確地說『我有多確定』」這件事有立體的體感。
