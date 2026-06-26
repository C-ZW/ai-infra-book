---
last_verified: 2026-06-13
review_after_days: 180
status: research-agent-draft
source: web research 2026-06-13
---

# 機率與統計史實基準表（landscape-2026-06）

本檔是《馴服隨機》全書「歷史、人物、歸屬、引文、悖論精確陳述」的權威錨點。各章數學自證；本檔管日期、人名、歸屬、引言、著名結果與悖論的「標準陳述」。

使用規約：
- 凡引用日期／歸屬，作者請對照本檔，不要憑記憶。
- ⚠️ 標記 = 來源不一致、常被誤傳、或我無法從可靠來源百分百確認的細節。看到 ⚠️ 請特別小心，照本檔給的「正確版」寫。
- 來源優先序：Stanford Encyclopedia of Philosophy、MacTutor、大學頁面、原始論文紀錄、Encyclopedia of Mathematics > 一般百科 > 部落格。
- 數值基準（生日問題、民調誤差、貝氏篩檢、68-95-99.7）均為本研究 agent 以 Python 自算，標「自算」者可直接抄。

---

## 一、機率的誕生（賭桌，16–17 世紀）

### Cardano《Liber de ludo aleae》（賭博遊戲之書）
- **寫作約 1564，1663 年身後出版**（Cardano 1576 年過世）。被視為機率數學最早的起點之一，比 Pascal–Fermat 通信早一個多世紀。
- Cardano 是第一個把隨機事件當成受數學律支配、並把機率視為 0 到 1 之間的值、以「有利結果／不利結果之比」定義勝算的人。
- 來源：Timeline of probability and statistics（Wikipedia）https://en.wikipedia.org/wiki/Timeline_of_probability_and_statistics ；Chalkdust「Roots: Gerolamo Cardano」https://chalkdustmagazine.com/biographies/roots-gerolamo-cardano/ ；Dover 英譯本書目（Gould 譯）。
- ⚠️ 「1564」是學界常引的寫作年，但 Cardano 一生多次增補手稿，確切年份有彈性；出版年 1663 較無爭議。

### Pascal–Fermat 通信 1654，「分賭注問題（problem of points）」
- **1654 年夏**，Blaise Pascal 與 Pierre de Fermat 數週往返通信，公認為機率論正式史的開端。核心是「分賭注問題」：賭局中途中止，賭金該如何公平分配。
- 兩人以不同方法（Fermat 用窮舉所有可能結果；Pascal 用更高效的遞迴計算）得到一致解。**真正的成就是引入「期望值（expectation）」概念。**
- 來源：APS News「July 1654: Pascal's Letters to Fermat on the Problem of Points」https://www.aps.org/apsnews/2009/07/pascal-letters-fermat-points ；Wikipedia「Problem of points」https://en.wikipedia.org/wiki/Problem_of_points

### Huygens《De ratiociniis in ludo aleae》（論賭博中的推理）
- **1657 年以拉丁文出版，是第一本印行的機率論專著**（first printed treatise on probability），直到 18 世紀前是該主題唯一的書。
- Huygens 1656 年在巴黎聽聞 Pascal 的工作後投入研究。書中以「期望（一隨機量的期望值）」而非「過程的機率」為基本概念：若 a、b 的機率比為 p:q，「機會的價值」為 (pa+qb)/(p+q)。
- 來源：Wiley「Huygens and De Ratiociniis in Ludo Aleae, 1657」https://onlinelibrary.wiley.com/doi/10.1002/0471725161.ch6 ；Dartmouth 英譯本 https://math.dartmouth.edu/~doyle/docs/huygens/huygens.pdf ；Internet Archive https://archive.org/details/DeRatiociniisInLudoAleae

---

## 二、古典時期與兩大定理的起源（18–19 世紀）

### Jacob（Jakob）Bernoulli《Ars Conjectandi》（推測術）
- **1713 年出版**，作者已於 **1705 年過世**，由其侄 Nicolaus I Bernoulli 整理付印（出版時距其過世 8 年）。
- 含機率論第一個極限定理：**弱大數法則（weak law of large numbers）**，被視為該學科的奠基之作。
- 來源：Wikipedia「Ars Conjectandi」https://en.wikipedia.org/wiki/Ars_Conjectandi ；Wiley/ISR「Tercentenary of Ars Conjectandi (1713)」https://onlinelibrary.wiley.com/doi/10.1111/insr.12050

#### ⚠️「黃金定理（golden theorem / theorema aureum）」的命名爭議
- 通說：Bernoulli 自稱大數法則為其「黃金定理」，後由 **Poisson** 改稱「Bernoulli 的大數法則（law of large numbers）」。
- **但有學界主張這是訛傳**：Karl Pearson 可能把拉丁文 "**autem**"（然而）誤讀為 "**aureum**"（黃金），因此「黃金定理」之名未必是 Bernoulli 本意。寫作時建議用「Bernoulli 自認分量極重的核心定理」這類較保守敘述，或明白標注此命名有爭議。
- 來源：「Stop calling Bernoulli's law of large numbers his 'Golden Theorem' (Please?)」https://www.researchgate.net/publication/384021500 ；thatsmaths「Bernoulli's Golden Theorem and the Law of Large Numbers」https://thatsmaths.com/2021/12/16/bernoullis-golden-theorem-and-the-law-of-large-numbers/

### de Moivre《The Doctrine of Chances》— 二項分布的常態近似（史上第一個中央極限定理）
- **1733 年**，de Moivre 在一份未公開印行的小冊《Approximatio ad summam terminorum binomii (a+b)^n in seriem expansi》中，首次給出二項分布的**常態近似**；英文版收入 **1738 年《The Doctrine of Chances》第 2 版**。
- 這字面上就是「擲硬幣」的中央極限定理：n 次伯努利試驗中成功比例標準化後，隨 n→∞ 趨近標準常態。**這是 CLT 的最早實例**（Bernoulli 情形稱 de Moivre–Laplace 定理）。
- de Moivre 起初聚焦對稱情形 p=1/2、大 n，避開不對稱二項的複雜性。
- 精確日期常見作 **1733 年 11 月 12 日**（私印小冊）；常態密度中的歸一常數 **√(2π)** 是 Stirling 補上的（de Moivre 原本只得到一個未定常數）。（2026-06，ch14 撰寫時經獨立 web 審查確認：York 大學 histstat、John D. Cook）
- **1733 日期與「二項→常態近似」性質，兩來源確認。**
- 來源：Wikipedia「De Moivre–Laplace theorem」https://en.wikipedia.org/wiki/De_Moivre%E2%80%93Laplace_theorem ；John D. Cook「How the central limit theorem began」https://www.johndcook.com/blog/2010/01/05/how-the-central-limit-theorem-began/

### Daniel Bernoulli — 聖彼得堡悖論（1738）與期望效用
- **1738 年**發表《Specimen Theoriae Novae de Mensura Sortis》（風險度量新理論闡述）於《Commentarii Academiae Scientiarum Imperialis Petropolitanae》第 5 卷，pp. 175–192。
- 論文 19 節，三主題：效用概念（1–9）、對數效用（10–16）、聖彼得堡悖論（17–19）。Daniel 拒絕「以期望值決策」，主張同一風險不同人評價不同 → **期望效用（expected utility）**。
- 問題本身由其堂兄 Nicolaus I Bernoulli 提出（1713 年致 Montmort 的信）。
- ⚠️ 重點：聖彼得堡悖論**不是數學算錯**——期望值確實發散到無窮；悖論在於「沒人願付無限賭注」，解法是效用（邊際效用遞減），屬決策／效用層面，不是機率計算的錯。
- 來源：Stanford Encyclopedia of Philosophy「The St. Petersburg Paradox」https://plato.stanford.edu/entries/paradox-stpetersburg/ ；Springer「On Specimen Theoriae Novae…」https://link.springer.com/article/10.1007/s10203-024-00471-z

### Laplace《Théorie analytique des probabilités》（機率的分析理論）
- **1812 年**出版，給出**第一個一般形式的中央極限定理**（de Moivre 結果被 Laplace 約 1776–1812 推廣到更廣的分布）。
- **1774 年**論文《Mémoire sur la probabilité des causes par les événemens》（論由事件推因之機率）：18 世紀後期最具影響力的統計論文之一，是**逆機率（inverse probability）**最早被廣讀的呈現，獨立於 Bayes 發展並推廣了貝氏方法；現代「貝氏定理」的廣為人知，主要靠 Laplace。
- 來源：Britannica「Analytic Theory of Probability」https://www.britannica.com/topic/Analytic-Theory-of-Probability ；Stigler「Laplace's 1774 Memoir on Inverse Probability」https://projecteuclid.org/journals/statistical-science/volume-1/issue-3/Laplaces-1774-Memoir-on-Inverse-Probability/10.1214/ss/1177013620.full

### Chebyshev / Bienaymé 不等式（弱大數法則的引擎）
- **Bienaymé 1853 年先陳述（無證明），Chebyshev 1867 年給出更一般的證明。**故正名為 **Bienaymé–Chebyshev 不等式**。Liouville 安排 Bienaymé 的文章緊接在 Chebyshev 之前刊出。
- 不等式給「有限變異數的隨機變數偏離其均值超過某常數」的機率上界（≤ 變異數/常數²），**正是用來證明弱大數法則的工具**。
- 來源：Wikipedia「Chebyshev's inequality」https://en.wikipedia.org/wiki/Chebyshev%27s_inequality ；Encyclopedia of Mathematics「Chebyshev inequality」https://encyclopediaofmath.org/wiki/Chebyshev_inequality_in_probability_theory ；Wikipedia「Irénée-Jules Bienaymé」https://en.wikipedia.org/wiki/Ir%C3%A9n%C3%A9e-Jules_Bienaym%C3%A9
- ⚠️ 注意 1867 是「Chebyshev 證明年」，常被籠統寫成「Chebyshev 不等式 1867」；公平起見應提 Bienaymé 1853 在先。

---

## 三、貝氏（Bayes）

### Thomas Bayes 的論文（身後出版，由 Richard Price 代為發表）
- 全名《An Essay towards solving a Problem in the Doctrine of Chances》，Bayes 已於 **1761 年過世**；論文由其友 **Richard Price** 增補後，於 Royal Society《Philosophical Transactions》宣讀／刊出。
- ⚠️ **日期有 1763 / 1764 之爭**：刊載於標注 **1763** 年的卷（Royal Society DOI 10.1098/rstl.1763.0053），實際印行流通常記為 **1764**。寫作時建議寫「1763 年（卷次標 1763、1764 年印行）」並擇一主述、註明另一。
- 來源：Wikipedia「An Essay Towards Solving a Problem in the Doctrine of Chances」https://en.wikipedia.org/wiki/An_Essay_Towards_Solving_a_Problem_in_the_Doctrine_of_Chances ；Royal Society 原文 https://royalsocietypublishing.org/rstl/article/doi/10.1098/rstl.1763.0053/119736/

#### ⚠️ Bayes 究竟證明了什麼 vs 現代「貝氏定理」——常見過度宣稱
- **過度宣稱**：「Bayes 證明了我們今天寫的那條貝氏定理 P(A|B)=P(B|A)P(A)/P(B)。」**不準確。**
- **正確版**：Bayes 的命題 3、4、5 之預備結果**蘊含**今名「貝氏定理」者，但他**並未強調或聚焦這個結果**。他真正要解的是更廣的推論問題：「已知某未知事件成功與失敗的次數，求其單次成功機率落在任兩個指定值之間的機會」——即一個**逆機率（inverse probability）**問題，並用了均勻先驗。現代教科書的「貝氏定理」形式與一般化，主要是 **Laplace** 的功勞。
- 來源：同上 Wikipedia 條目；Stanford Encyclopedia「Bayes' Theorem」https://plato.stanford.edu/entries/bayes-theorem/

### 頻率派 vs 貝氏派（簡史）
- 18 世紀末逆機率（Bayes/Laplace）一度主流；20 世紀初 Fisher、Neyman、Pearson 建立頻率派（p 值、信賴區間、假設檢定）並批判先驗的主觀性，貝氏一度退居；20 世紀後期隨計算力與 MCMC 復興。本書若觸及只需點到（細節見各章）。

### Gigerenzer：自然頻率（natural frequencies）改善貝氏推理
- **Gigerenzer & Hoffrage (1995)**：把統計資訊改用「自然頻率格式」（如「1000 人中…」）呈現，受試者的貝氏推理表現遠優於用百分比/機率呈現時。兩個解釋：(1) 自然頻率讓後驗計算更簡單；(2) 演化上人腦更擅長從頻率而非機率推論。
- 重要修正：「人類天生是糟糕的貝氏推理者」這個舊主張只在資訊用機率呈現時成立。
- 來源：Gigerenzer & Hoffrage 1995, Psychological Review 102(4):684–704（引用紀錄與後續）https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.01473/full ；APA「Teaching Bayesian Reasoning in Less Than Two Hours」https://www.apa.org/pubs/journals/releases/xge-1303380.pdf

---

## 四、常態分布、回歸、相關（19 世紀）

### Gauss（1809）vs Legendre（1805）— 最小平方法的優先權之爭
- **Legendre 1805 年率先發表**最小平方法（附於彗星軌道專著的附錄）。**Gauss 1809 年於《Theoria motus corporum coelestium》正式發表**，並聲稱自 **1795 年**起就在用，且把最小平方與常態分布（誤差分布）連結。
- Legendre 對 Gauss 的優先權主張不滿，1820 年公開反駁。**這是數學史上最著名的優先權之爭之一（僅次於牛頓 vs Leibniz 的微積分之爭）。**
- 來源：Actuaries Institute「Gauss, Least Squares, and the Missing Planet」https://www.actuaries.asn.au/research-analysis/gauss-least-squares-and-the-missing-planet ；Stigler「The method of Gauss in 1799」https://projecteuclid.org/journals/statistical-science/volume-13/issue-2/The-method-of-Gauss-in-1799/10.1214/ss/1028905931.pdf
- ⚠️ 正確寫法：**發表優先權屬 Legendre（1805）**；Gauss 把它與常態誤差律結合、並聲稱更早私下使用，但「私下使用」無發表佐證。別寫成「Gauss 發明最小平方法」。

### Quetelet —「平均人（l'homme moyen / average man）」
- **1835 年**《Sur l'homme et le développement de ses facultés》（社會物理學）提出 **homme moyen（平均人）** 概念：人類某性狀的測量值按常態分布聚集於該中心值。
- Quetelet 自己也說平均人是「虛構（être fictif）」。並把「社會物理學（social physics）」用於對人口資料的量化研究（犯罪率、結婚率等）。
- 來源：Britannica「Adolphe Quetelet」https://www.britannica.com/biography/Adolphe-Quetelet ；Oxford Academic 章節 https://academic.oup.com/book/38774/chapter/337582254

### Galton — 回歸均值、相關係數的共同奠基
- **Hereditary Genius 1869**；**「Regression towards mediocrity in hereditary stature」1886**（首條回歸線，斜率 < 1，子代向均值回歸）；**Natural Inheritance 1889**（總結其回歸與相關工作）。早期豌豆實驗約 1875。
- Galton 發明相關係數的雛形，稱「index of correlation」，**用字母 r（取自 reversion／regression）**。其數學嚴謹化由 **Karl Pearson**（1857–1936）完成，故今稱 **Pearson's r**。
- 來源：MacTutor「Galton」https://mathshistory.st-andrews.ac.uk/Biographies/Galton/ ；Stanton, JSE「Galton, Pearson, and the Peas」https://jse.amstat.org/v9n3/stanton.html ；Gorroochurn「On Galton's Change from Reversion to Regression」http://www.columbia.edu/~pg2113/index_files/Gorroochurn-On%20Galton's%20Change.pdf
- ⚠️ 原詞是 **「regression towards mediocrity（向平庸回歸）」**，今多作「regression toward the mean（向均值回歸）」。引用 Galton 原文時用 mediocrity。題目給的「1869–1889」是其相關/回歸工作的跨度區間，**單篇回歸論文是 1886**。

### 68–95–99.7 規則的精確值（自算，erf 計算）
| 範圍 | 精確值 | 2 位小數 |
|---|---|---|
| ±1σ | 68.2689% | **68.27%** |
| ±2σ | 95.4500% | **95.45%** |
| ±3σ | 99.7300% | **99.73%** |
- 自算（Python `math.erf(k/√2)`）。常被四捨五入成 68/95/99.7，但精確值如上。
- 參考：Wikipedia「68–95–99.7 rule」https://en.wikipedia.org/wiki/68%E2%80%9395%E2%80%9399.7_rule
- ⚠️ 別寫成「±2σ 恰 95%」；**95% 對應的是 ±1.96σ**，±2σ 是 95.45%。

---

## 五、統計推論的建立（20 世紀）

### Gosset「Student」t 分布（1908，Guinness 釀酒廠）
- **William Sealy Gosset 1908 年以筆名「Student」在《Biometrika》第 6 卷 pp. 1–25 發表《The Probable Error of a Mean》**。
- 背景：Gosset 在都柏林 Guinness 釀酒廠處理小樣本（常 ≤10）品管問題；Guinness 禁員工具名發表（怕洩漏其科學方法），故用筆名。1906/07 曾赴 Karl Pearson 實驗室一年。
- 來源：Wikipedia「Student's t-test」https://en.wikipedia.org/wiki/Student%27s_t-test ；Zabell「On Student's 1908 Article」https://personal.morris.umn.edu/~jongmink/Stat2611/s1.pdf ；原文 York 鏡像 https://www.york.ac.uk/depts/maths/histstat/student.pdf
- ⚠️ 卷期：**Biometrika 6, 1–25**（已用多源確認；坊間偶見誤植「vol 4」或「pp. 1–24」，以 6/1–25 為準）。

### Kolmogorov 公理（1933）
- **Andrei Kolmogorov 1933 年《Grundbegriffe der Wahrscheinlichkeitsrechnung》（機率論基礎）**，以集合論與測度論（建基於 Borel、Lebesgue）給出機率論的公理化基礎，把機率函數歸結為三條（含可數可加性可算四條）簡單公設，如同 Euclid 之於幾何。
- 來源：arXiv「The origins and legacy of Kolmogorov's Grundbegriffe」https://arxiv.org/pdf/1802.06071 ；Internet Archive 原書 https://archive.org/details/kolmogoroff-1933-grundbegriffe-der-wahrscheinlichkeitsrechnung

### Fisher — p 值、顯著性、虛無假設、女士品茶
- **《Statistical Methods for Research Workers》1925**；**《The Design of Experiments》1935**。後者引入隨機化、重複、區組，並以「**女士品茶（lady tasting tea）**」說明虛無假設。
- 女士品茶：8 杯（4 先奶後茶、4 先茶後奶），受試者挑出某法所製的 4 杯。用 **Fisher 精確檢定**，虛無假設下全 8 杯都對的機率為 **1/70**。
- 來源：Wikipedia「The Design of Experiments」https://en.wikipedia.org/wiki/The_Design_of_Experiments ；「Lady tasting tea」https://en.wikipedia.org/wiki/Lady_tasting_tea ；「Statistical Methods for Research Workers」https://en.wikipedia.org/wiki/Statistical_Methods_for_Research_Workers

#### ⚠️ p<0.05 不是 Fisher 的硬性界線
- Fisher 1925 確實寫過「P=0.05（1/20）對應 1.96≈2，取此為判斷顯著與否的方便界限」。
- **但他明白表示這是方便、可調的**：「若 1/20 odds 不夠高，我們可改畫在 1/50（2%）或 1/100（1%）。」他把 0.05 當**慣例與起點，不是不可逾越的硬規則**。把「p<0.05 = 真/假」二分當成 Fisher 的鐵律是誤解。
- 來源：Tandfonline「Before p<0.05 to Beyond p<0.05」https://www.tandfonline.com/doi/full/10.1080/00031305.2018.1537891 ；UW News「Documents that Changed the World: Fisher defines statistical significance, 1925」https://www.washington.edu/news/2016/12/21/

### Neyman–Pearson 假設檢定框架；Neyman 信賴區間（1937）
- **Neyman & Pearson 1928、1933** 建立檢定框架：把虛無與對立假設不對稱處理，引入 **Type I（型一，棄真）/ Type II（型二，存偽）誤差** 與**檢定力（power）**。「最佳檢定」= 在控制 Type I ≤ α 下最小化 Type II。
- 來源：Frontiers「Fisher, Neyman-Pearson or NHST?」https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.00223/full

#### ⚠️ 信賴區間（confidence interval）的精確頻率派意義 —— 全書最常被講錯的點
- **Neyman 1937** 定義：一個「信賴係數 X%」的程序，指在**反覆抽樣**下，所產生的區間有 X% 會涵蓋真值（對所有真值都成立）。
- **錯誤陳述（務必避免）**：「這個算出來的 95% 信賴區間，有 95% 機率包含真值。」**錯。**真值是未知**常數**不是隨機變數；某條已算出的特定區間，**要嘛涵蓋（機率 1）要嘛沒涵蓋（機率 0）**。95% 是指**製造區間這個程序**的長期涵蓋率，不是「這一條」的機率。
- Neyman 本人 1937 在美國農業部演講時即糾正 Milton Friedman 的誤解：「真均值不是隨機變數，是未知常數。」
- 來源：PMC「Continued misinterpretation of confidence intervals」https://pmc.ncbi.nlm.nih.gov/articles/PMC4742490/ ；Wikipedia「Neyman construction」https://en.wikipedia.org/wiki/Neyman_construction

---

## 六、複現危機與 p 值之亂（當代）

### Ioannidis 2005「Why Most Published Research Findings Are False」
- **John Ioannidis，2005 年 8 月，PLoS Medicine 2(8):e124。** 論證：多數已發表（醫學）研究結果無法複現。研究較不可能為真的條件：樣本小、效應小、檢定的關係多而預選少、設計/定義/分析彈性大、利益偏見大、競逐顯著性的團隊多。被視為「元科學（metascience）」的奠基文獻。
- 來源：PLOS Medicine 原文 https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.0020124 ；Wikipedia https://en.wikipedia.org/wiki/Why_Most_Published_Research_Findings_Are_False

### Simmons, Nelson, Simonsohn 2011「False-Positive Psychology」
- **Psychological Science 22(11):1359–1366。** 全名《False-Positive Psychology: Undisclosed Flexibility in Data Collection and Analysis Allows Presenting Anything as Significant》。示範「未揭露的研究者彈性（即 **p-hacking**）」可把名目 5% 的型一誤差率推高到最壞約 60%。**普及了「研究者自由度（researcher degrees of freedom）」一詞。**
- 來源：SAGE 原文 https://journals.sagepub.com/doi/10.1177/0956797611417632

### Open Science Collaboration 2015（Science）心理學可複現性
- **2015 年《Science》「Estimating the reproducibility of psychological science」。** 複現 100 篇研究：原研究 97% 有顯著結果（p<.05），**但複現僅 36% 達顯著**；複現的效應量約為原研究的一半。
- **頭條複現率 ≈ 36%（約 1/3）。**
- 來源：Science 原文 https://www.science.org/doi/10.1126/science.aac4716 ；OSF 專案 https://osf.io/ezcuj/overview

### ASA 2016 對 p 值的聲明（Wasserstein & Lazar）
- **The American Statistician 70(2):129–133（2016）。** 六原則中關鍵警告：
  1. p 值衡量資料與某指定模型的「不相容程度」；
  2. **p 值不是「假設為真的機率」，也不是「結果純屬隨機的機率」**；
  3. 科學/商業/政策結論**不應只看 p 值是否過某門檻**；
  4. 正確推論需完整報告與透明（避免選擇性報告）；
  5. p 值/顯著性不衡量效應大小或結果重要性；
  6. 單一 p 值對證據強度的衡量有限。
- 來源：Tandfonline 原文 https://www.tandfonline.com/doi/full/10.1080/00031305.2016.1154108 ；Berkeley PDF https://www.stat.berkeley.edu/~aldous/Real_World/ASA_statement.pdf

---

## 七、著名悖論與謬誤（精確陳述很重要）

### Monty Hall 問題
- **起源：Steve Selvin 1975 年致《The American Statistician》的信**（首次提出並解答，用 "Let's Make a Deal" 主持人 Monty Hall 命名）。
- **Marilyn vos Savant：1990 年 9 月（Parade「Ask Marilyn」專欄，1990-09-09）** 給出「該換」「換可使勝率加倍」的答案，引發約 1 萬封來信（含許多博士）指她錯——但她是對的。
- **標準假設下：換 → 2/3 勝；不換 → 1/3 勝。**
- **⚠️ 換能贏 2/3 的「標準假設」（缺一不可）：**
  1. 主持人**一定**會開一扇（玩家沒選的）門；
  2. 主持人**一定**開出**羊**門，絕不開車門；
  3. 主持人**知道**門後是什麼（非隨機開）；
  4. 當玩家一開始就選中車、主持人面對兩扇羊門時，**隨機等機率**選一扇開。
- 若主持人行為不符（例如他只在你選中車時才邀你換、或隨機開可能開到車），2/3 結論**不成立**。Monty Hall **取決於主持人行為假設**，這點務必寫清楚。
- 來源：Wikipedia「Monty Hall problem」https://en.wikipedia.org/wiki/Monty_Hall_problem （標準假設依 Krauss & Wang 2003）

### Simpson 悖論（Simpson's paradox）
- **命名**：Colin Blyth 1972 年定名「Simpson's paradox」，源自 **Edward Simpson 1951** 的技術論文；更早 **Udny Yule 1903**（與 Pearson 1899）已述類似效應。
- **UC Berkeley 1973 研究所招生**（Bickel, Hammel & O'Connell, **Science 187(4175), 1975, pp. 398–404**）：**合計**數據看似**對女性不利**（男性錄取率較高）；但**按系拆分後反轉**為「對女性有小幅但統計顯著的有利偏向」。原因：女性較多申請競爭激烈、錄取率低的系。
  - ⚠️ **效應方向**：總體 → 似偏向男性；分系 → 偏向女性。別寫反。
- **腎結石治療**（Charig et al. 1986）：合計看 **經皮腎造瘻取石（PCNL）83% > 開放手術 78%**；但按結石大小拆分後，**開放手術在大、小結石都較佳**（<2cm：93% vs 83%；≥2cm：73% vs 69%）——混淆變數是結石大小（重症多用開放手術）。
- 來源：Wikipedia「Simpson's paradox」https://en.wikipedia.org/wiki/Simpson%27s_paradox ；Charig 1986 / PMC 案例 https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9960320/

### 生日問題（birthday problem）
- **23 人 → 至少兩人同生日的機率 ≈ 0.5073（50.73%）。** 自算（忽略閏日、假設均勻）：
  - **P(無碰撞, 23 人) = 0.4927（4 位小數）**
  - **P(有碰撞, 23 人) = 0.5073（4 位小數）**
- 直覺低估的原因：23 人有 C(23,2)=253 對可比較，不是只比一個人對全體。
- 來源：Wikipedia「Birthday problem」https://en.wikipedia.org/wiki/Birthday_problem （數值為自算）

### Bertrand 悖論（1889，隨機弦）
- **Joseph Bertrand 1889《Calcul des probabilités》** 提出：圓內內接正三角形，問「隨機弦」長於三角形邊的機率。三種「同樣合理」的隨機化各得不同答案：
  - 隨機端點法 → **1/3**；隨機半徑點法 → **1/2**；隨機中點法 → **1/4**。
- 寓意：在無窮樣本空間上**無差別原則（principle of indifference）若不指定隨機化機制，會給出不唯一的機率**。
- 來源：Wikipedia「Bertrand paradox (probability)」https://en.wikipedia.org/wiki/Bertrand_paradox_(probability)

### 男孩女孩／兩孩悖論（Martin Gardner 1959）
- **Martin Gardner，1959 年 10 月《Scientific American》Mathematical Games**，題為「The Two Children Problem」。
- Gardner 初給答案 **1/2 與 1/3**；**後來承認第二題有歧義**：「至少一個是男孩，兩個都是男孩的機率」可為 **1/3 或 1/2**，取決於「你如何得知有一個男孩」的隨機程序。
  - 從「至少有一男孩的兩孩家庭」隨機取一家 → 1/3；從某家隨機選一孩、得知其為男孩 → 1/2。
- 寓意：**未指定隨機化程序 → 機率不唯一。** 寫作時務必標明此題的歧義。
- 來源：Wikipedia「Boy or girl paradox」https://en.wikipedia.org/wiki/Boy_or_girl_paradox

### 合取謬誤 / Linda 問題（Tversky & Kahneman 1983）
- **Tversky & Kahneman 1983，Psychological Review 90:293–315。** Linda（31 歲、直言、關心歧視與社會正義、參加反核）→ 約 **85%** 受試者認為「Linda 是銀行出納員**且**女權主義者」比「Linda 是銀行出納員」更可能。
- 這違反**合取規則 P(A∩B) ≤ P(A)**（A∩B 是 A 的子集）。肇因於**代表性捷思（representativeness heuristic）**：「女權銀行員」更「像」描述。相關概念：**基本比率忽略（base-rate neglect）**。
- 來源：Wikipedia「Conjunction fallacy」https://en.wikipedia.org/wiki/Conjunction_fallacy

### 賭徒謬誤（gambler's fallacy）vs 賭徒破產（gambler's ruin）
- **兩者不同，別混。**
  - **賭徒謬誤**：誤以為獨立事件會「自我修正」（連開紅後黑「該來了」）——是**認知謬誤**。
  - **賭徒破產問題**：兩玩家各持本金、重複對賭至一方歸零，求各自破產/獲勝機率——是**正經機率問題**，源出 Pascal–Fermat（最早見 1656 年 Pascal 致 Fermat 信），由 **Huygens 1657《De ratiociniis…》** 發表（其書末第 5 題即此）。
- 來源：Wikipedia「Gambler's ruin」https://en.wikipedia.org/wiki/Gambler%27s_ruin ；Song & Song「A Note on the History of the Gambler's Ruin Problem」https://koreascience.or.kr/article/JAKO201311637859390.page

### 熱手謬誤（hot-hand fallacy）——⚠️ 2018 年的反轉，全書必須捕捉
- **原始：Gilovich, Vallone & Tversky 1985**（Cognitive Psychology）——主張籃球「熱手」是錯覺，人類在隨機資料中看見不存在的型態，**結論「熱手是謬誤」**。
- **反轉：Miller & Sanjurjo 2018**（Econometrica）——指出 1985 分析有**系統性選擇偏差（selection bias）**：在有限序列中，「連中後再投中」的經驗頻率**即使在獨立假設下也會系統性偏低**。**去偏後，1985 的經典結論被推翻，反而出現「連續命中」的顯著證據——熱手可能是真的。**
- ⚠️ **這個轉折必須寫進書**。很多來源（含 Gilovich 本人）仍把 1985 的「熱手是謬誤」當定論在講；正確的當代理解是：**因選擇偏差校正，熱手效應可能真實存在**（至少 1985 的否證不成立）。
- 來源：Miller & Sanjurjo「Surprised by the Hot Hand Fallacy? A Truth in the Law of Small Numbers」https://marketing.wharton.upenn.edu/wp-content/uploads/2018/11/Paper-Joshua-Miller.pdf ；Wikipedia「Hot hand」https://en.wikipedia.org/wiki/Hot_hand

### Sports Illustrated 封面魔咒 / 二年級退步（sophomore slump）——回歸均值的範例
- 「**SI 封面魔咒**」：登上封面者隨後表現變差。真因是**回歸均值**——登封面前往往是**異常出色（含好運成分）**的表現，之後自然回落到常態水準，並非被詛咒。
- 「**二年級／菜鳥後退步（sophomore slump）**」同理：新秀爆發季含超量好運，次年回歸平均。
- 來源：Wikipedia「Sports Illustrated cover jinx」https://en.wikipedia.org/wiki/Sports_Illustrated_cover_jinx ；「Regression fallacy」https://en.wikipedia.org/wiki/Regression_fallacy

---

## 八、分布與過程

### Poisson 分布
- **Siméon Denis Poisson 1837《Recherches sur la probabilité des jugements en matière criminelle et en matière civile》**（論刑事與民事審判機率）中首次發表，用於陪審團判決。
- **「稀有事件定律（law of rare events / small numbers）」**：60 年後由 **Ladislaus Bortkiewicz 1898《Das Gesetz der kleinen Zahlen》** 發揚——研究 **普魯士軍隊 14 個軍團、20 年間共 122 名被馬踢死** 的士兵，示範低頻事件在大母體中服從 Poisson 分布（即使各別機率不同）。此為經典教學資料集。
- 來源：Springer「Poisson Distribution and Its Application」https://link.springer.com/rwe/10.1007/978-3-642-04898-2_448 ；Poisson 原著 Gallica https://gallica.bnf.fr/ark:/12148/bpt6k110193z

### 冪律 / Pareto 原則（80/20）；肥尾；Taleb《黑天鵝》
- **Vilfredo Pareto**：觀察到義大利約 **20% 的人擁有 80% 的土地/所得**（冪律分布，即 Pareto 分布）。
  - ⚠️ **日期與「80/20」命名的細節易錯**：Pareto 的所得分布觀察見於《Cours d'économie politique》（**1896–1897**），有些來源把該冪律記為 **1906/1909**（《Manuale》）。而 **「80/20 原則」「Pareto principle」這個名稱與商管化，是 Joseph M. Juran 在 1940 年代命名／推廣的**（以 Pareto 之名），**不是 Pareto 本人取的**。寫作時：把「冪律觀察」歸 Pareto（1890s），把「80/20 原則」一詞歸 Juran（1940s）。
- **肥尾（fat tails）/「黑天鵝」**：Nassim Nicholas Taleb《**The Black Swan**》**2007** 把高衝擊、難預測、事後被合理化的稀有事件帶入主流；黑天鵝即位於肥尾深處的極端事件。
- 來源：Wikipedia「Pareto principle」https://en.wikipedia.org/wiki/Pareto_principle ；Juran Institute https://www.juran.com/blog/a-guide-to-the-pareto-principle-80-20-rule-pareto-analysis/

### Markov 鏈
- **Andrey Markov 1906** 起研究「相依變數的鏈」，奠定新分支。**1913 年**分析 **Pushkin《Eugene Onegin（葉甫蓋尼·奧涅金）》前 20,000 個字母的母音/子音序列**，把每字母分母音/子音，示範相依事件鏈可嚴格建模（下一字母類別僅依賴前一或前兩字母）。1913-01-23 於聖彼得堡帝國科學院報告。
- ⚠️ 常見混淆：**理論工作始於 1906**；**Onegin 母音/子音實證分析是 1913**。別把兩者都寫成 1906 或都寫成 1913。
- 來源：Wikipedia「Andrey Markov」https://en.wikipedia.org/wiki/Andrey_Markov ；American Scientist「First Links in the Markov Chain」https://www.americanscientist.org/article/first-links-in-the-markov-chain

### PageRank 作為 Markov 鏈
- **Brin & Page 1998《The Anatomy of a Large-Scale Hypertextual Web Search Engine》**（WWW7 / Computer Networks）。PageRank = 「**隨機漫遊者（random surfer）**」模型：以機率隨連結點擊、以機率 (1−d) 隨機跳到任一頁（d=阻尼因子）；某頁被造訪的穩態機率即其 PageRank——本質是有限狀態 **Markov 鏈** 的平穩分布。
- 來源：原論文 http://infolab.stanford.edu/pub/papers/google.pdf ；ETHW Milestone https://ethw.org/Milestones:PageRank_and_the_Birth_of_Google,_1996-1998

### 布朗運動（Brownian motion）
- **Robert Brown 1827** 顯微鏡下觀察花粉顆粒（Clarkia pulchella）在水中的隨機抖動。
- **Louis Bachelier 1900** 博士論文《Théorie de la spéculation》（投機理論，Poincaré 指導）——**更早**就以布朗運動建模金融價格，但長期被忽視至 1950 年代。
- **Einstein 1905** 獨立提出理論解釋（用以估 Avogadro 數與分子大小）。
- **Norbert Wiener 1923** 給出嚴格數學處理（**Wiener 過程**），證明存在連續路徑版本。
- ⚠️ **布朗路徑「幾乎必然連續但處處不可微（almost surely continuous but nowhere differentiable）」確認**：以機率 1，路徑處處不可微（Paley–Wiener–Zygmund 1931 首證；Dvoretzky–Erdős–Kakutani 1961 現代論證）。也因此須用隨機微積分（Itô）。
- 來源：Wikipedia「Brownian motion」https://en.wikipedia.org/wiki/Brownian_motion ；U Chicago Lalley 講義 https://galton.uchicago.edu/~lalley/Courses/313/BrownianMotionCurrent.pdf

### Buffon 投針（Buffon's needle，估 π）
- **Georges-Louis Leclerc, Comte de Buffon**：**1733 年提出，1777 年發表解答**。把針投到等距平行線地板上，針跨線的機率與 π 直接相關，可用作蒙地卡羅估 π。
- 趣聞：**Lazzerini 1901** 投 3,400+ 次估得 π≈3.1415929（頭 6 位正確）——但此結果常被疑為「對答案調參」的可疑案例。
- 來源：Wikipedia「Buffon's needle problem」https://en.wikipedia.org/wiki/Buffon's_needle_problem

---

## 九、數值基準複核（給作者抄用；標「自算」者可直接用）

| 項目 | 結果 | 出處 |
|---|---|---|
| 生日問題：P(無碰撞, 23 人) | **0.4927**（4dp） | 自算（Python，均勻、忽略閏日） |
| 生日問題：P(有碰撞, 23 人) | **0.5073**（4dp） | 自算 |
| 民調誤差界：1.96 × √(0.25/1000) | **0.0310 ≈ ±3.1%**（√(0.25/1000)=0.015811…） | 自算 |
| 疾病篩檢貝氏：盛行率 0.1%、敏感度 99%、偽陽性率 5% → 後驗 P(病\|陽性) | **≈ 0.0194 ≈ 1.94%**（真陽性 0.00099 / 全陽性 0.05094） | 自算 |
| de Moivre 二項→常態 | 一句話：n 次伯努利試驗的標準化成功數，隨 n→∞ 收斂到標準常態（史上第一個 CLT，字面上就是擲硬幣）。 | 見 §二 |

- ⚠️ 疾病篩檢數字是「反直覺教學金句」：篩檢陽性者**真正得病只約 2%**（因盛行率極低、偽陽性主導），務必照此寫，別誤寫成 99%。
- ⚠️ 民調 ±3.1% 是「p=0.5、n=1000、95% 信賴」的最大誤差界；新聞常說「±3%」即此。

---

## 十、常被誤傳的事實（重點清單——作者最可能寫錯的）

1. **熱手反轉**：別停在 Gilovich-Vallone-Tversky 1985 的「熱手是謬誤」。Miller & Sanjurjo 2018 校正選擇偏差後**推翻**該否證，**熱手可能是真的**。（§七）
2. **信賴區間誤解**：95% CI **不是**「真值有 95% 機率落在這條區間」。真值是常數；某條區間要嘛涵蓋要嘛不涵蓋；95% 是**程序**的長期涵蓋率。（§五）
3. **「Bayes 證明了我們現在寫的貝氏定理」——過度宣稱**。Bayes 解的是逆機率問題、用均勻先驗；現代形式與一般化主要是 Laplace。（§三）
4. **Gauss vs Legendre 最小平方法優先權**：**發表優先權屬 Legendre（1805）**；Gauss（1809）把它與常態誤差律結合並聲稱更早私用（無發表佐證）。別寫「Gauss 發明最小平方法」。（§四）
5. **p<0.05 不是 Fisher 的硬性鐵律**：Fisher 自己說可改 1/50、1/100，是方便慣例不是真假二分線。（§五）
6. **Monty Hall 取決於主持人行為假設**：2/3 只在「主持人一定開、一定開羊門、知情、面對兩羊門時隨機」下成立。（§七）
7. **聖彼得堡悖論是效用問題不是數學錯**：期望值確實發散；解在邊際效用遞減。（§二）
8. **大數法則不是「偏差會被修正」**：LLN 講的是**平均值/比例**收斂（稀釋效應），**不是**讓 |正面−反面| 歸零。事實上 **|正面−反面| 的期望絕對差隨 n 增長，約 ∝ √n**；認為「該來平衡了」正是賭徒謬誤。（§二、§七）
9. **Simpson 悖論方向別寫反**：Berkeley 1973 總體似偏向男性、分系後偏向女性；腎結石總體 PCNL 較佳、分大小後開放手術較佳。（§七）
10. **Pareto vs Juran**：冪律觀察歸 Pareto（1890s）；「80/20 原則」一詞與商管化是 Juran（1940s）命名。（§八）
11. **±2σ ≠ 95%**：±2σ = 95.45%；95% 對應 **±1.96σ**。（§四）
12. **Bayes 論文日期 1763/1764、Bienaymé–Chebyshev 1853/1867、Markov 1906/1913**：均有「兩個年份」陷阱，見各節 ⚠️。

---

## 附：尚未 100% 釘死、建議引用前再查的細節
- Cardano《Liber de ludo aleae》寫作年「1564」（手稿多次增補，數字有彈性）。
- Bayes 論文 1763 vs 1764（卷次標年 vs 實際印行年）。
- Pareto 冪律的精確年份（1896–97 Cours vs 1906/09 Manuale）。
- 「golden theorem / theorema aureum」是否為 Bernoulli 本意（Pearson 誤讀 autem→aureum 之說）。
- Lazzerini 1901 投針 π 值的真實性（疑似事後配參數）。
