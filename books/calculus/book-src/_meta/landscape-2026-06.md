# landscape-2026-06：本書時效性與歷史事實的唯一基準

- **用途**：本書（微積分思想史）所有「脆弱事實」——歷史年份、出處、原句、數值、外部資源連結——的唯一基準檔。
- **基準日期**：2026-06（全部條目於 2026-06-12 以網路查證或本檔自行複核）。
- **使用規則**：各章引用本檔列出的事實時，**以本檔表述為準**，不得引用記憶中的「常見說法」；若常見說法與本檔的「部分修正」衝突，一律採本檔版本。標注 ⚠️ 的條目未能完全確認，章節引用時必須帶保留語氣或註明「傳說」。重大修正（推翻本檔既有表述）需兩個獨立來源，並在 maintenance 掃描日誌記一行。

---

## A. 古代與前奏

### 1. 芝諾悖論的出處
- **事實**：芝諾（Zeno of Elea，西元前五世紀）原著不存。四個運動悖論（二分、阿基里斯與烏龜、飛矢不動、運動場）皆經亞里斯多德《物理學》（Physics）第六卷轉述而流傳，部分輔以 Simplicius 的注釋。飛矢不動的標準轉述位置是 Physics 239b30：「若凡占據與自身相等空間者皆靜止，而運動中之物在任一瞬間皆如此，則飛矢不動。」亞里斯多德並指出二分與阿基里斯本質上是同一論證（阿基里斯即追趕版的二分）。
- **來源**：https://plato.stanford.edu/entries/paradox-zeno/ ；https://iep.utm.edu/zenos-paradoxes/
- **判定**：確認。

### 2. Eudoxus 與窮盡法
- **事實**：窮盡法（method of exhaustion）歸於 Eudoxus of Cnidus（約西元前 408–355）。歸屬依據是阿基米德本人：他在《論球與圓柱》（On the Sphere and Cylinder）序文中把相關定理的證明（角錐、圓錐體積）歸功於 Eudoxus。更早的雛形想法來自 Antiphon，Eudoxus 將其變成嚴格方法；約一百年後由阿基米德發揮到極致。
- **來源**：https://mathshistory.st-andrews.ac.uk/Biographies/Eudoxus/ ；https://en.wikipedia.org/wiki/Method_of_exhaustion
- **判定**：確認。

### 3. 阿基米德《拋物線求積》：弓形面積 = 內接三角形的 4/3
- **事實**：《拋物線求積》（Quadrature of the Parabola）證明拋物線弓形面積是同底同高內接三角形的 4/3。論證核心：逐層內接三角形，每一層新增面積是前一層的 1/4，亦即依賴幾何級數 1 + 1/4 + 1/16 + … = 4/3。**細緻化（引用時注意）**：阿基米德並未「加總無窮級數」——他在命題 23 證明的是**有限和**恆等式（前 n 項加上一個尾項修正等於 4/3），再於命題 24 用窮盡法的雙重歸謬（面積既不能大於也不能小於 4/3）完成證明。書中可說「實質上等於求出該幾何級數的和」，但不要說他「直接求了無窮和」。
- **來源**：https://en.wikipedia.org/wiki/Quadrature_of_the_Parabola ；https://mathcs.holycross.edu/~little/Archimedes.pdf
- **判定**：確認（附細緻化：有限和＋雙重歸謬，非直接無窮求和）。

### 4. 阿基米德以 96 邊形夾擠 π
- **事實**：《圓的度量》（Measurement of a Circle）中，阿基米德從正六邊形出發，逐次倍增至內接與外切正 96 邊形，證得 3 + 10/71 < π < 3 + 1/7，即 223/71 < π < 22/7（約 3.1408 < π < 3.1429）。
- **來源**：https://itech.fgcu.edu/faculty/clindsey/mhf4404/archimedes/archimedes.html ；https://www.pbs.org/wgbh/nova/physics/approximating-pi.html
- **判定**：確認。

### 5. 《方法》與 Archimedes Palimpsest
- **事實**：丹麥學者 Johan Ludvig Heiberg 於 1906 年在君士坦丁堡（伊斯坦堡）的 Metochion 圖書館檢視一部祈禱書重寫本（palimpsest），發現底層是七篇阿基米德著作，包括《方法》（The Method）的唯一傳世希臘文本、Stomachion 與希臘文《論浮體》。該手抄本 1998 年 10 月 28 日在紐約 Christie's 拍賣，由匿名美國藏家購得，1999 年 1 月寄存於巴爾的摩 Walters Art Museum 進行修復、多光譜成像與學術研究。2008 年 10 月 29 日（拍賣十週年）全部影像與轉錄以 Creative Commons 授權公開。現行官方網站：**https://www.archimedespalimpsest.org/**（2026-06 仍在線，歷史頁 https://www.archimedespalimpsest.org/about/history/index.php ）。
- **來源**：https://www.archimedespalimpsest.org/about/history/index.php ；https://en.wikipedia.org/wiki/Archimedes_Palimpsest ；https://thewalters.org/news/lost-and-found-the-secrets-of-archimedes/
- **判定**：確認。

### 6. 調和級數發散的最早證明：Nicole Oresme
- **事實**：最早證明歸於十四世紀法國學者 Nicole Oresme（約 1350 年），方法是分組（1/3+1/4 ≥ 1/2、1/5+…+1/8 ≥ 1/2，依此類推），是 Cauchy 凝聚判別法的先聲。此結果其後湮沒，十七世紀由 Pietro Mengoli 與 Jacob Bernoulli 等人重新證明。
- **來源**：https://en.wikipedia.org/wiki/Harmonic_series_(mathematics) ；https://www.math.utah.edu/history/oresme.html
- **判定**：確認。

### 7. Kerala 學派／Madhava：早於歐洲約兩百年
- **事實**：Madhava of Sangamagrama（MacTutor 作 1350–1425，另說約 1340–1425）創立 Kerala 學派。歸於他（或其學派）的成果：π/4 = 1 − 1/3 + 1/5 − …（今稱 Madhava–Leibniz 級數，並附修正項加速收斂）、sin 與 cos 的冪級數展開，並算得 π 準確至 **11 位小數**（3.14159265359）。這些成果早於歐洲（Gregory、Newton、Leibniz）兩百年以上。**保留態度（學界主流）**：Madhava 本人的數學著作已佚失，成果經由後世 Kerala 學者轉述——最清楚的是 Jyesthadeva 的《Yukti-Bhasa》（約 1550）與 Nilakantha 的著作；曾被當作 Madhava 親著的《Mahajyanayana prakara》現多被認定為十六世紀後學之作。目前沒有 Kerala 成果傳入歐洲的證據，主流觀點視之為**獨立的先驅成就**，而非歐洲微積分的來源。**常見錯誤**：坊間常寫「π 準確至 13 位」，MacTutor 與多數學術來源為 11 位，本書採 11 位。
- **來源**：https://mathshistory.st-andrews.ac.uk/Biographies/Madhava/ ；https://www.britannica.com/science/Indian-mathematics/The-school-of-Madhava-in-Kerala ；https://en.wikipedia.org/wiki/Madhava_of_Sangamagrama
- **判定**：部分修正：π 採 11 位小數（非 13）；歸屬須註明「經後世學派文本轉述」。

### 8. 「微積分」中文譯名：李善蘭與偉烈亞力《代微積拾級》
- **事實**：1859 年，李善蘭（1811–1882）與英國傳教士偉烈亞力（Alexander Wylie）合譯美國 Elias Loomis 的《Elements of Analytical Geometry and of the Differential and Integral Calculus》（1850），中譯名《代微積拾級》，由上海墨海書館刊行——東亞第一本微積分教科書。書名意指「代（數幾何）、微（分）、積（分），拾級而上」。「微分」「積分」二詞即出自此譯本，李善蘭並創譯代數、常數、變數、函數、係數、級數、切線、法線、漸近線等沿用至今的術語。
- **來源**：https://highscope.ch.ntu.edu.tw/wordpress/?p=25200 ；https://zh.wikipedia.org/zh-tw/%E6%9D%8E%E5%96%84%E5%85%B0
- **判定**：確認。

---

## B. 牛頓、萊布尼茲與優先權之爭

### 9. 牛頓的瘟疫年與《Principia》
- **事實**：1665–66 年倫敦大瘟疫期間劍橋關閉，牛頓回到 Woolsthorpe 老家，在這段「奇蹟年」（anni mirabiles）發展出流數法（method of fluxions）的核心想法（1666 年 10 月寫成私人短論，即 October 1666 tract），同期完成光學實驗與重力思考的起點。系統性論文《De Methodis Serierum et Fluxionum》完成於 1671 年，但生前未出版（英譯本《Method of Fluxions》遲至 1736 年身後刊行）。《Philosophiæ Naturalis Principia Mathematica》出版於 1687 年。
- **來源**：https://en.wikipedia.org/wiki/Method_of_Fluxions ；https://en.wikipedia.org/wiki/Early_life_of_Isaac_Newton
- **判定**：確認（注意：流數法 1665–66 發展、1671 成稿、1736 才出版的時間差是優先權之爭的火種）。

### 10. 萊布尼茲的記號與第一篇論文
- **事實**：萊布尼茲於 **1675 年 10 月 29 日**的手稿《Analyseos tetragonisticae pars secunda》首次使用積分號 ∫（取自拉丁文 summa 的長 s）；同年 **11 月 11 日**的手稿首次寫出 ∫ 與 dx 連用的形式。第一篇公開發表的微分學論文是 1684 年刊於《Acta Eruditorum》的〈Nova Methodus pro Maximis et Minimis〉（d 記號首次印行）；∫ 記號首次印行則在 1686 年的〈De Geometria Recondita〉。
- **來源**：https://en.wikipedia.org/wiki/Leibniz%27s_notation ；https://en.wikipedia.org/wiki/Integral_symbol ；https://mathshistory.st-andrews.ac.uk/Miller/mathsym/calculus/
- **判定**：確認（補充印行年份：d 記號 1684、∫ 記號 1686 才見於出版品）。

### 11. FTC 的先驅：Gregory 與 Barrow
- **事實**：微積分基本定理（FTC）的幾何版先驅有二：**James Gregory**（1638–1675）在 1668 年《Geometriae pars universalis》發表第一個**公開出版**的初步幾何形式；**Isaac Barrow**（1630–1677）約 1670 年在《Lectiones Geometricae》給出更一般的幾何版證明。兩者皆以幾何語言包裝，掩蓋了計算上的威力；把 FTC 變成演算工具並建立完整體系的是牛頓與萊布尼茲。學界標準說法即「Gregory 先發表、Barrow 更一般、牛頓與萊布尼茲完成」。**細緻化**：常稱 Barrow 是「牛頓的老師」——精確說法是 Barrow 是劍橋首任 Lucasian 教授、牛頓的前任與提攜者；正式的師生授業關係證據薄弱，書中宜用「前輩／提攜者」。
- **來源**：https://en.wikipedia.org/wiki/Fundamental_theorem_of_calculus ；https://www.britannica.com/science/analysis-mathematics/Discovery-of-the-theorem ；https://arxiv.org/pdf/1111.6145
- **判定**：確認（附細緻化：「Barrow＝牛頓的老師」是通俗簡化）。

### 12. 優先權之爭與 Commercium Epistolicum
- **事實**：萊布尼茲向皇家學會申訴後，時任會長的牛頓親自挑選一個全由己方支持者組成的委員會（無任何歐陸數學家），1712 年作成調查報告，年底以《Commercium Epistolicum》刊行，結論指萊布尼茲剽竊——而**報告實質上由牛頓本人起草與主導**，萊布尼茲從未獲答辯機會。牛頓其後又匿名在《Philosophical Transactions》發表吹捧該報告的書評（〈An Account of the Commercium Epistolicum〉，1715）。此為科學史上著名的裁判兼球員案例。
- **來源**：https://www.historyofinformation.com/detail.php?id=1726 ；https://www.newtonproject.ox.ac.uk/view/texts/normalized/NATP00352 ；https://www.maths.tcd.ie/pub/HistMath/People/Newton/CommerciumAccount/
- **判定**：確認。

### 13. Berkeley《The Analyst》與「ghosts of departed quantities」
- **事實**：George Berkeley《The Analyst; or, a Discourse Addressed to an Infidel Mathematician》出版於 1734 年。名句出自**第 XXXV 節**，原文：「And what are these Fluxions? The Velocities of evanescent Increments? And what are these same evanescent Increments? They are neither finite Quantities nor Quantities infinitely small, nor yet nothing. May we not call them the Ghosts of departed Quantities?」——矛頭針對牛頓流數法中「消逝增量」（evanescent increments）的邏輯地位。此書刺激了後續使分析嚴格化的努力（Maclaurin 等）。
- **來源**：https://en.wikipedia.org/wiki/The_Analyst ；https://old.maa.org/press/periodicals/convergence/mathematical-treasure-george-berkeleys-the-analyst
- **判定**：確認（引用原句以本檔為準，出處標 §XXXV）。

---

## C. 十八～十九世紀：擴張與嚴格化

### 14. Euler：Basel 問題與 Euler 公式
- **事實**：Euler 解出 Basel 問題（Σ1/n² = π²/6）於 1734 年，1735 年 12 月 5 日在聖彼得堡科學院宣讀；論文〈De summis serierum reciprocarum〉（編號 E41）刊於院刊《Commentarii》第 7 卷（卷標 1734/35，實際印行 1740）——引用時寫「1734/1735」最穩。Euler 公式 e^{iθ} = cos θ + i sin θ 的系統性表述出自《Introductio in analysin infinitorum》（1748，兩卷）。**細緻化**：等價的對數形式更早見於 Roger Cotes（1714），Euler 的貢獻是指數形式與系統運用。
- **來源**：https://en.wikipedia.org/wiki/Basel_problem ；https://scholarlycommons.pacific.edu/cgi/viewcontent.cgi?article=1032&context=euleriana ；https://www.ams.org/journals/bull/2007-44-04/S0273-0979-07-01183-4/S0273-0979-07-01183-4.pdf
- **判定**：確認。

### 15. Grandi 級數與「上帝創世」
- **事實**：義大利數學家暨修士 Guido Grandi（1671–1742）在 1703 年《Quadratura circoli et hyperbolae》提出 1 − 1 + 1 − 1 + …：不同加括號方式可得 0 或 1，他以此論證「從無中創造（creatio ex nihilo）完全可信」——這是有文獻的真實論述，非後人杜撰。Grandi 本人認為該級數「真值」是 1/2。
- **來源**：https://en.wikipedia.org/wiki/Grandi%27s_series ；https://en.wikipedia.org/wiki/History_of_Grandi%27s_series
- **判定**：確認。

### 16. Fourier → Dirichlet → Cantor 的史線
- **事實**：Fourier 於 **1807 年 12 月 21 日**向法蘭西科學院（Institut de France）提交熱傳導備忘錄《Mémoire sur la propagation de la chaleur dans les corps solides》；Laplace、Monge 等人傾向刊行，但 **Lagrange 反對**（主因是三角級數的處理方式），論文未獲出版。1811 年科學院以熱傳導為題懸賞，Fourier 修訂稿得獎但被批不夠嚴格。1822 年（Lagrange 已歿）出版《Théorie analytique de la chaleur》。**Dirichlet 1829** 年在 Crelle 期刊（Journal für die reine und angewandte Mathematik 第 4 卷，頁 157–169）發表〈Sur la convergence des séries trigonométriques…〉，給出第一個嚴格的傅立葉級數收斂定理。其後 Heine 向 Cantor 提出三角級數表示的唯一性問題（Dirichlet、Riemann 等人未能解決），Cantor 於 1870 年證出唯一性、1870–72 年系列論文中為處理例外點集而引入點集概念——**「傅立葉級數的收斂與唯一性問題催生嚴格分析、並直接引出 Cantor 集合論」是有據可查的標準史線**。
- **來源**：https://en.wikipedia.org/wiki/Joseph_Fourier ；https://www.scirp.org/reference/referencespapers?referenceid=2329205 ；https://mathshistory.st-andrews.ac.uk/Biographies/Cantor/ ；https://www.pma.caltech.edu/documents/5627/uniqueness.pdf
- **判定**：確認。

### 17. Cauchy《Cours d'analyse》與 ε-δ
- **事實**：Cauchy《Cours d'analyse》（1821）以極限概念定義連續與收斂，把分析建立在極限之上；其證明中已出現 ε 型論證（Grabiner 的考據）。但**定義本身**是用「無窮小增量產生無窮小變化」的語言寫的，不是現代符號化的 ε-δ；今天教科書形式的 ε-δ 定義標準歸於 **Weierstrass**（1861 年柏林講義起）及其學派的系統化。更早 Bolzano（1817）已有嚴格定義但流傳極少。學界對「Cauchy 到底多現代」有持續辯論（Grabiner vs. Borovik–Katz 等），本書採折衷標準說法：**觀念奠基在 Cauchy，符號化與系統化在 Weierstrass 學派**。
- **來源**：http://amsi.org.au/ESA_Senior_Years/SeniorTopic3/3a/3a_4history_4.html ；https://arxiv.org/pdf/1108.2885 ；https://arxiv.org/pdf/1502.06942
- **判定**：確認（claim 原表述即為學界折衷說法，可直接使用）。

### 18. Weierstrass 怪獸函數
- **事實**：f(x) = Σ aⁿ cos(bⁿπx)。Weierstrass 於 **1872 年 7 月 18 日**在柏林的皇家普魯士科學院宣讀；本人當時未出版，**首次印行是 du Bois-Reymond 1875 年**刊於 Crelle 期刊第 79 卷（頁 21–37）的論文〈Versuch einer Classification der willkürlichen Functionen reeller Argumente…〉。原始條件：0 < a < 1、b 為正奇數、ab > 1 + 3π/2（滿足條件的最小 b 是 7）。**Hardy 1916**（Trans. AMS 17，〈Weierstrass's non-differentiable function〉）放寬為 0 < a < 1、ab ≥ 1，且 **b 不必是奇數或整數**。
- **來源**：https://en.wikipedia.org/wiki/Weierstrass_function ；https://www.ams.org/journals/tran/1916-017-03/S0002-9947-1916-1501044-1/S0002-9947-1916-1501044-1.pdf ；https://mathshistory.st-andrews.ac.uk/Biographies/Du_Bois-Reymond/
- **判定**：確認（全部條件數字照本檔）。

### 19. Riemann 重排定理的出處
- **事實**：條件收斂級數可重排至任意實數值（或發散）的定理，出自 Riemann 的教授資格論文（Habilitationsschrift）《Ueber die Darstellbarkeit einer Function durch eine trigonometrische Reihe》（**1854** 年提交哥廷根大學）；Riemann 1866 年病逝，論文由 Dedekind 安排於 **1867** 年身後出版。
- **來源**：https://en.wikipedia.org/wiki/Riemann_series_theorem ；https://www.sciencedirect.com/science/article/abs/pii/B9780444508713501194
- **判定**：確認。

### 20. Dedekind cuts
- **事實**：Dedekind《Stetigkeit und irrationale Zahlen》（連續性與無理數）出版於 **1872** 年，以「切割」（cut）從有理數構造實數，給出實數完備性（連續性）的算術化基礎。核心想法 Dedekind 自記成形於 1858 年 11 月 24 日（在蘇黎世教微積分時），擱置十四年後才出版。
- **來源**：https://www.britannica.com/biography/Richard-Dedekind ；https://www.sciencedirect.com/science/article/pii/B9780444508713501248
- **判定**：確認。

### 21. 海王星：用微積分算出來的行星
- **事實**：Le Verrier 以天王星軌道攝動反推未知行星，1846 年 8 月 31 日向法蘭西科學院提交預測位置，並去信柏林天文台的 Johann Galle；**1846 年 9 月 23 日當晚**，Galle 與 d'Arrest 在**距 Le Verrier 預測位置約 1° 之內**找到海王星，前後不到一小時。英國的 Adams 獨立做過類似計算，但其解多次變動，發現位置距其預測約 12°；現代科學史（尤其 1998 年皇家格林威治天文台檔案重見天日後）已下修 Adams 的「共同預測者」地位。「人類第一次用紙筆（攝動計算＝微積分）找到一顆行星」的敘事成立，精確度即「約 1°」。
- **來源**：https://en.wikipedia.org/wiki/Discovery_of_Neptune ；https://www.aps.org/apsnews/2020/08/neptunes-existence-confirmed ；https://www.nasa.gov/history/175-years-ago-astronomers-discover-neptune-the-eighth-planet/
- **判定**：確認（Adams 部分採保留表述）。

### 22. Poincaré 與三體問題
- **事實**：為瑞典國王 Oscar II 六十大壽（1889 年 1 月）設立的懸賞，Poincaré 以《Sur le problème des trois corps et les équations de la dynamique》獲獎。論文付印時，編輯 Phragmén 的提問讓 Poincaré 發現一個深層錯誤（誤以為不變曲線擬閉合、實則橫截相交），他自費回收重印——花費超過 2500 克朗的獎金。修正後約 270 頁的論文 **1890 年 12 月**刊於《Acta Mathematica》第 13 卷，其中對同宿交錯（homoclinic tangle）的描述是**動力系統混沌行為的第一次數學刻畫**。「微分方程寫得下、卻解不出（無一般封閉解，且對初值敏感）」的標準敘事由此而來。
- **來源**：https://en.wikipedia.org/wiki/Poincar%C3%A9_and_the_Three-Body_Problem ；https://www.actamathematica.org/library/prize-competition/ ；https://www.mittag-leffler.se/about-us/history/prize-competition/
- **判定**：確認。

---

## D. 二十世紀與現代

### 23. Robinson 非標準分析
- **事實**：Abraham Robinson 於 **1960** 年（普林斯頓研討會）提出非標準分析，1961 年發表同名論文，**1966** 年出版專著《Non-standard Analysis》——在超實數體系 ℝ* 上把無窮小建為嚴格的數學物件，距 Weierstrass 學派「驅逐」無窮小約一個世紀，常被稱為無窮小的嚴格平反。
- **來源**：https://en.wikipedia.org/wiki/Nonstandard_analysis ；https://www.encyclopedia.com/science/encyclopedias-almanacs-transcripts-and-maps/resurrection-infinitesimals-abraham-robinson-and-nonstandard-analysis
- **判定**：確認。

### 24. 1 + 2 + 3 + … 「=」 −1/12 的正確脈絡
- **事實**：級數 1+2+3+… 的部分和趨於無窮，**它發散，沒有傳統意義的和**。−1/12 是另一種「求和」意義下指派的值：ζ(s) 的解析延拓給出 ζ(−1) = −1/12，zeta 正規化與 Ramanujan 求和也指派同值（物理上用於弦論等）。**史實修正（常被講錯）**：「1+2+3+⋯ = −1/12 under my theory… you will at once point out to me the lunatic asylum as my goal」這段話出自 Ramanujan 給 Hardy 的**第二封信（1913 年 2 月 27 日）**，不是著名的第一封信（1913 年 1 月 16 日）；第一封信列出的是可詮釋為 ζ(−1)、ζ(−3) 的結果。書中引用須寫「=」是加引號的、並指明是解析延拓／正規化意義。
- **來源**：https://en.wikipedia.org/wiki/1_%2B_2_%2B_3_%2B_4_%2B_%E2%8B%AF ；https://writings.stephenwolfram.com/2016/04/who-was-ramanujan/
- **判定**：部分修正：名句出自第二封信（1913-02-27），非第一封。

### 25. 布朗運動路徑幾乎處處不可微
- **事實**：Wiener process（布朗運動的數學模型）的樣本路徑以機率 1 處處連續但**處處不可微**——首證為 Paley–Wiener–Zygmund 1933 年〈Notes on random functions〉（Math. Z. 37, 647–668）；現代教科書（Mörters–Peres《Brownian Motion》定理 1.27 等）皆收錄。亦即「自然界（的標準數學模型）真的長出怪獸函數」成立——注意措辭：不可微的是**數學模型的路徑**，物理布朗粒子在極小尺度另有物理。
- **來源**：https://www.mi.uni-koeln.de/~moerters/book/book.pdf ；https://galton.uchicago.edu/~lalley/Courses/313/BrownianMotionCurrent.pdf
- **判定**：確認。

### 26. PID 控制器
- **事實**：PID = proportional（比例，回應當下誤差）、integral（積分，累計過去誤差以消除穩態偏差）、derivative（微分，以誤差變化率預測未來、抑制震盪）。
- **來源**：https://www.crystalinstruments.com/blog/2020/8/23/pid-control-theory ；https://apmonitor.com/pdc/index.php/Main/ProportionalIntegralDerivative
- **判定**：確認。

### 27. 梯度下降與反向傳播
- **事實**：梯度下降（最速下降法）歸於 **Cauchy 1847** 年短文〈Méthode générale pour la résolution des systèmes d'équations simultanées〉（Comptes Rendus）。反向傳播在數學上就是多層複合函數的 chain rule 反向應用；**Rumelhart–Hinton–Williams 1986** 年 Nature 論文〈Learning representations by back-propagating errors〉（323: 533–536）**使之普及**——「普及」措辭正確且必要，因為反向模式自動微分更早已有（Linnainmaa 1970、Werbos 1974）。
- **來源**：https://en.wikipedia.org/wiki/Gradient_descent ；https://www.nature.com/articles/323533a0
- **判定**：確認（保留「普及」而非「發明」的措辭）。

### 28. 數值微分的步長困境
- **事實**：浮點運算下，前向差分 (f(x+h)−f(x))/h 的總誤差 ≈ 截斷誤差 O(h) ＋ 捨入誤差 O(ε/h)（ε 為 machine epsilon，雙精度 ≈ 2.2×10⁻¹⁶）；h 太小時相近數相減發生災難性消去。最小化 h/2·M + 2ε/h 得最適 h ~ **√ε 量級**（雙精度 ≈ 10⁻⁸）。中央差分截斷誤差 O(h²)，最適 h ~ **ε^{1/3} 量級**（≈ 6×10⁻⁶）。此為標準數值分析結論。**本檔自行複核**：對 e(h) = h/2 + 2ε/h 求導置零得 h* = 2√ε ✓；對 e(h) = ε/h + h²/6 得 h* = (3ε)^{1/3} ✓。
- **來源**：https://en.wikipedia.org/wiki/Numerical_differentiation ；https://docs.sciml.ai/FiniteDiff/dev/epsilons/
- **判定**：確認（含本檔自行複核）。

---

## E. 延伸閱讀資源（2026-06 連結現況）

### 29. 3Blue1Brown《Essence of Calculus》
- 官網系列頁：https://www.3blue1brown.com/lessons/essence-of-calculus/ （存在）；YouTube 播放清單：https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr （存在）。視覺直觀、以「讓你覺得自己能發明微積分」為目標。
- **判定**：確認。

### 30. MIT OCW 18.01 Single Variable Calculus
- 現行課程頁（含 2007 年 Jerison 錄影的經典版）：https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/ ；較新版本：https://ocw.mit.edu/courses/18-01-calculus-i-single-variable-calculus-fall-2020/ 。
- **判定**：確認。

### 31. Steven Strogatz《Infinite Powers》（2019）
- 原書：Houghton Mifflin Harcourt，2019-04-02。**有繁體中文譯本**：《無限的力量：這個世界表面上看似混亂且不講理，但其最深處卻是合乎邏輯，並且確實遵守著一條條的數學定律》，黃駿譯，旗標出版，2020-09，ISBN 9789863126348。
- 來源：https://www.books.com.tw/products/0010867735 ；https://www.tenlong.com.tw/products/9789863126348
- **判定**：確認（繁中譯名《無限的力量》）。

### 32. Spivak《Calculus》第 4 版；Apostol《Calculus》
- Spivak《Calculus》4th ed.（Publish or Perish，2008，ISBN 9780914098911；官方頁 https://mathpop.com/products/calculus-4th-edition ）——**定位**：證明導向微積分的標竿，「對嚴格性的初次正面相遇」。Apostol《Calculus》兩卷（Wiley，2nd ed. 1967/1969；https://en.wikipedia.org/wiki/Calculus_(Apostol_books) ）——**定位**：理論與技巧並重、先積分後微分的 Caltech 傳統教本。
- **判定**：確認。

### 33. Dunham《The Calculus Gallery》；Bressoud《Calculus Reordered》
- Dunham《The Calculus Gallery: Masterpieces from Newton to Lebesgue》（Princeton UP；平裝頁 https://press.princeton.edu/books/paperback/9780691182858/the-calculus-gallery ）——以原典級證明走一遍從 Newton 到 Lebesgue 的畫廊。Bressoud《Calculus Reordered: A History of the Big Ideas》（Princeton UP，2019；https://press.princeton.edu/books/hardcover/9780691181318/calculus-reordered ）——以累積、變化比、級數、容差四大主軸重排微積分史。
- **判定**：確認。

### 34. Paul's Online Math Notes
- https://tutorial.math.lamar.edu/ （Lamar University，Paul Dawkins；2026-06 仍在線）——Algebra 到 Calculus I–III、微分方程的免費筆記。
- **判定**：確認。

### 35. Needham《Visual Complex Analysis》25 週年版
- 25th Anniversary Edition，Oxford University Press，2023-02 出版，720 頁，新增 Roger Penrose 序與全部 501 張圖的完整說明文字；精裝 ISBN 9780192868916、平裝 9780192868923（https://global.oup.com/academic/product/visual-complex-analysis-9780192868923 ）。
- **判定**：確認。

---

## F. 基準數值複核（本檔自行複核，2026-06-12，Python 3 雙精度）

### 36. (1+1/n)ⁿ 逼近 e
- n=12：2.613035…（≈ 2.6130 ✓）；n=365：2.714567…（≈ 2.7146 ✓）；e = 2.718281828…（≈ 2.71828 ✓）。
- **判定**：確認（本檔自行複核）。

### 37. Euler 法 dy/dt = y, y(0)=1, 算到 t=1
- 步長 0.1：(1.1)^10 = 2.5937424601（≈ 2.5937 ✓）；步長 0.01：(1.01)^100 = 2.704813829…（≈ 2.7048 ✓）。
- **判定**：確認（本檔自行複核）。

### 38. 三個基準常數
- 交錯調和級數 1 − 1/2 + 1/3 − … = ln 2 = 0.693147…（≈ 0.6931 ✓）；Basel 和 π²/6 = 1.644934…（≈ 1.6449 ✓）；芝諾配置（阿基里斯 10 m/s、烏龜 1 m/s、讓先 100 m）追上點 = 100·10/(10−1) = 1000/9 = 111.111… m（≈ 111.11 m ✓）。
- **判定**：確認（本檔自行複核）。

### 39. 方波傅立葉級數與 Gibbs 現象
- 方波（±1）的傅立葉級數 = (4/π)(sin x + sin 3x/3 + sin 5x/5 + …) ✓。Gibbs overshoot：部分和峰值 → (2/π)·Si(π) = 1.178979…，超出量 0.178979…，**相對於整個跳躍幅度（2）為 8.949 %**——「約 9 %（精確值 8.95 %）」成立。**引用時注意分母**：若誤以半跳躍（1）為分母會變成 17.9 %，坊間兩種寫法混用，本書一律以「跳躍幅度的 8.95 %」表述。
- **判定**：確認（本檔自行複核：Simpson 法算 Si(π) = 1.851937）。

### 40. ∫₀¹ x² dx 與黎曼和
- 精確值 1/3 ✓；n=4 左黎曼和 = (0²+0.25²+0.5²+0.75²)/4 = 0.21875 ✓；右黎曼和 = (0.25²+0.5²+0.75²+1²)/4 = 0.46875 ✓。
- **判定**：確認（本檔自行複核）。

---

## 傳說與軼事註記（引用時必須標明性質）

- **牛頓的蘋果**：⚠️ 傳說等級的軼事。有十八世紀文獻（如 Stukeley 回憶錄轉述牛頓晚年自述）支持「見蘋果落下而思重力」，但「蘋果砸到頭」是後世渲染；本次掃描未逐一查證細節，書中引用一律寫「傳說」。
- **阿基米德「Eureka」裸奔、「別弄壞我的圓」**：⚠️ 傳說，出自後世（Vitruvius、Plutarch 等）轉述，不可當史實引用。
- **Grandi 的上帝創世論證**（見第 15 條）：**非傳說**，有原典文獻，可直接引用。
- **Ramanujan 瘋人院妙語**（見第 24 條）：**非傳說**，但出自第二封信。

## 本次掃描摘要（2026-06-12）
- 全部 40 條皆已查證或自行複核；無條目停留在「⚠️ 未能確認」（僅傳說註記中兩條軼事性質本身標 ⚠️）。
- 對常見說法的修正：Madhava π 採 11 位非 13 位（第 7 條）；阿基米德是有限和＋雙重歸謬非直接無窮求和（第 3 條）；−1/12 名句在第二封信（第 24 條）；「Barrow＝牛頓的老師」為簡化（第 11 條）；Gibbs 9 % 的分母是整個跳躍（第 39 條）；∫ 與 d 的手稿與印行年份要分開講（第 10 條）。
