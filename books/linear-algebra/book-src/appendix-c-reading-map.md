# 附錄 C — 延伸閱讀總地圖

> **這份地圖在做什麼**：把全書 22 章各自「## 延伸閱讀」推薦過的資源，去重、分類、排成三條路——**往抽象走、往數值走、往應用走**。每條只放一句話，告訴你它為什麼值得讀、該看哪一段、它接的是本書哪一章。最後給「如果只看三樣」的精選，和書架上四本鄰書的銜接點。
>
> **收錄原則**：只放 `landscape-2026-06` 或各章已實際引用、且確認存在的連結。沒把握的標「（未驗證）」並請你自己查一眼再點。所有連結 2026-06 驗證；線代是接近永恆的數學，連結壞掉的機率低，但網站搬家總會發生——若某條打不開，用標題去搜尋多半找得到。

---

## 怎麼用這張地圖

讀完這本書，你站在一個分岔口。本書刻意只走一條路：**幾何優先、把矩陣當動詞**。它故意留了幾個洞——抽象向量空間的完整公理、若爾當形、張量、數值演算法的實作、無窮維／函數空間——因為填滿它們會變成另一本書。這份地圖就是那幾個洞的出口。

三條路不是互斥的，是三種「再深一層」的方向：

```text
              你讀完的這本書
        （矩陣是動詞、幾何優先）
                   │
      ┌────────────┼────────────┐
      ↓            ↓            ↓
  往抽象走      往數值走      往應用走
  公理、證明    它怎麼壞、    拿線代去做
  一般 n 維    為何不穩      真實的事
  Axler        Strang 數值   3B1B、PCA、
  向量空間     條件數、QR    PageRank、ML
```

- **往抽象走**：你想看本書「直覺帶過、嚴格證明指向延伸」那些地方的完整版——譜定理、SVD 存在性、維度良定義、向量空間公理。這條路的旗手是 Axler。
- **往數值走**：你想知道「它在電腦上會怎麼壞」——為什麼 det≠0 還是解不準（條件數）、為什麼不要算逆矩陣、classical Gram–Schmidt 為何不穩。這條路服務本書的「直覺的陷阱／故障視角」。
- **往應用走**：你想看線代被拿去做真實的事——影像壓縮、PageRank、PCA、機器學習。這條路最對工程師胃口。

每條路下面，資源大致按「先看哪個」排序。

---

## 路線一：往抽象走——看本書沒展開的嚴格版

本書一路用「方格網還是方格網」「特徵向量是不轉的方向」這種幾何語言講。但每個直覺背後都有一個嚴格命題與證明，本書刻意把它們指向延伸。這條路就是那些證明的家。

- **Sheldon Axler，《Linear Algebra Done Right》第四版**（2024，Open Access 官方免費 PDF）。**這條路的首選，也是全書被各章引用最多次的一本**。它的招牌是 *determinant-free*——刻意把行列式放到全書最後，主張很多定理不靠行列式更乾淨，視角和本書幾乎相反（本書 ch09 行列式是主角之一），正好當對照組。本書沒展開的東西這裡都有嚴格版：維度良定義與替換引理（接 ch03）、可逆＝單射又滿射（接 ch08）、秩—零化度定理（他叫 Fundamental Theorem of Linear Maps，接 ch10）、複數場上每個算子都有特徵值（接 ch12）、若爾當形的不靠行列式建構（接 ch13）、內積空間公理與 Cauchy–Schwarz（接 ch15）、正交投影的最小化性質（接 ch16）、Gram–Schmidt 存在性（接 ch17）、一般 n 維的譜定理與 SVD（接 ch18–19）。第四版新增的**多線性代數一章**（雙線性／二次型、張量積）就是本書「張量」那個洞的補丁。讀完本書想看「同一套東西用嚴格公理重講一遍」長什麼樣，從這裡開始。<https://linear.axler.net/>

- **MAA Convergence，"Math Origins: Eigenvectors and Eigenvalues"**（免費）。**詞源與概念史**，接 ch11–12。Cauchy 的 *racine caractéristique*、Hilbert 1904 的 *Eigenwert*、為什麼 eigen＝own/characteristic 而非單純的 self、latent root 等同義詞怎麼演變——「特徵這個詞怎麼來的」想講完整，出處在這。<https://old.maa.org/press/periodicals/convergence/math-origins-eigenvectors-and-eigenvalues>

- **MacTutor 數學史，矩陣與行列式條目**（聖安德魯斯大學，免費）。**線代史的總入口**，接 ch01、ch06、ch09。Sylvester 1850 造「matrix」這個詞、Cayley 1858 造矩陣代數、行列式比矩陣老約 167 年（關孝和 1683、Cramer 1750）——本書歷史暗線的多數歸屬都可在這查證。配套的 Camille Jordan 傳（接 ch13，釐清三個 Jordan）與《九章算術》條目（接 ch07，看高斯消去早於高斯兩千年）同站。<https://mathshistory.st-andrews.ac.uk/HistTopics/Matrices_and_determinants/>

- **歷史原文（給好奇心特別重的）**：
  - **Arthur Cayley，*A Memoir on the Theory of Matrices*（1858）**（Internet Archive 掃描，免費）。矩陣代數的出生證明，也是「乘法不可交換」第一次被白紙黑字寫進理論的地方（接 ch06）。讀不懂十九世紀記法沒關係，看一眼你天天用的乘法是 1858 年才被定義出來的，就值了。<https://archive.org/details/philtrans05474612>
  - **Eckart, C. & Young, G.（1936），《The Approximation of One Matrix by Another of Lower Rank》，Psychometrika 1, 211–218**。最佳低秩近似定理的原始出處（接 ch20）——一篇 1936 年的論文，今天每個 PCA、每個推薦系統都在用它。原文偏技術，建議從後人整理（如 Strang 教科書的 SVD 章）入手。
  - **G. W. Stewart，"On the Early History of the Singular Value Decomposition"，SIAM Review（1993）**。接 ch19。把「SVD 是被獨立發明好幾次的東西、不是某一個人的專利」（Beltrami 1873、Jordan 1874、Sylvester 1889）講準確的學術出處。<https://www.scribd.com/document/495985801/On-the-early-history-of-SVD>
  - **Hawkins，"Cauchy and the Spectral Theory of Matrices"，Historia Mathematica（1975）**。接 ch18。柯西 1829 首次證實對稱矩陣特徵值為實、主軸定理、譜理論到 1870 年代成形——譜定理歷史的學術出處。<https://www.sciencedirect.com/science/article/pii/0315086075900324>

---

## 路線二：往數值走——它在電腦上會怎麼壞

本書的「直覺的陷阱／故障視角」一路警告你：det≠0 不代表解得準、用逆矩陣解方程是數值上的罪、不是什麼都能對角化、classical Gram–Schmidt 在浮點下會塌。這條路把那些警告補成完整的數值圖像。**這幾篇都是短文或講義，最適合「想把一條工程教訓鎖死、然後轉述給另一個工程師」。**

- **John D. Cook，〈Don't invert that matrix〉**（部落格短文，免費）。**這條路的開胃菜，一頁講清「為什麼解方程不要算逆、要做分解」**。接 ch08「用逆矩陣解方程是數值上的罪」與 ch17「QR 解最小平方而非算逆」。最簡明的工程共識背書，短到可以直接貼給同事。<https://www.johndcook.com/blog/2010/01/19/dont-invert-that-matrix/>

- **Gregory Gundersen，〈Why Shouldn't I Invert That Matrix?〉**（部落格文章，免費）。**同一條教訓的加長版**，接 ch08。把「別寫 `inv(A)@b`、要寫 `solve(A, b)`」的數值理由（計算複雜度、數值穩定性）攤開，**附實驗**。想看數字而不只是結論，讀這篇。<https://gregorygundersen.com/blog/2020/12/09/matrix-inversion/>

- **Nick Higham，數值線代短文系列**（部落格，免費）。**數值線代權威的一頁系列**，接 ch08 與 ch19：
  - 〈What Is the Condition Number of a Matrix?〉——把條件數的定義與「損失幾位有效數字」講得最乾淨（接 ch08 病態矩陣）。
  - 〈What Is the Hilbert Matrix?〉——用希爾伯特矩陣示範「乾淨可逆卻病態到爆」的標本（接 ch08）。
  - 〈What Is the Singular Value Decomposition?〉——一頁把 SVD、奇異值＝√(AᵀA 特徵值)、條件數＝σ_max/σ_min、低秩近似的關係講清楚（接 ch19，把 ch08→ch19 那條條件數線補成精確定義）。
  
  入口任選一篇，站內互相連結：<https://nhigham.com/2020/06/30/what-is-the-hilbert-matrix/>

- **Åke Björck，《Gram–Schmidt Orthogonalization: 100 Years and More》**（綜述 PDF，免費）。接 ch17。把 Gram（1883）、Schmidt（1907）的歷史，以及 **classical 與 modified Gram–Schmidt 在浮點下的穩定性差異**（正交性損失正比 κ(A) vs κ(A)²）講得最完整——本書「classical 不穩、用 modified」那段陷阱的權威出處。<https://www.cis.upenn.edu/~cis6100/Gram-Schmidt-Bjorck.pdf>

- **Gilbert Strang，MIT 18.06 的數值與工程面**（MIT OpenCourseWare，免費）。**這條路也可以走 Strang**：他不是把線代教成純抽象，而是計算與幾何並重，數值面給得足——逆矩陣與消去法（接 ch08，看他怎麼不靠逆就解方程）、投影矩陣 P=A(AᵀA)⁻¹Aᵀ 與正規方程（接 ch16）、Gram–Schmidt 與 A=QR 一條龍（接 ch17）、正定的多種等價判據攤開對照（接 ch18）。比本書深、例子多。<https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/>
  - 配套教科書 **Gilbert Strang，《Introduction to Linear Algebra》第六版**（Wellesley-Cambridge，2023，ISBN 9781733146678）。第六版新增最佳化與資料學習的章節，是往數值與應用兩條路的橋。（書本身非免費；OCW 課程免費。）<https://math.mit.edu/~gs/linearalgebra/ila6/indexila6.html>

> **數值線代手冊本書刻意不收**：BLAS、LAPACK、求解器實作、Householder/Givens 的演算法細節，是一整個獨立領域。上面這幾篇是「為什麼要在乎數值穩定」的入口，不是實作手冊。真要往那走，Strang 第六版與 Higham 的書（*Accuracy and Stability of Numerical Algorithms*）是下一站。

---

## 路線三：往應用走——拿線代去做真實的事

這條路最對工程師胃口：線代被拿去壓縮影像、排名網頁、降維資料、訓練模型。本書 ch19–21 已經把 SVD、PCA、PageRank 講過一遍幾何，這條路是「同一個東西，看它在真實系統裡怎麼用」。

- **3Blue1Brown，《Essence of Linear Algebra》**（Grant Sanderson，YouTube／官網，免費）。**嚴格說它是「視覺地基」而非單純應用，但放這裡因為它是全書最該配著看的一套，且每一集都把抽象變成可見的東西**。15 部影片的視覺化系列，第一集「Vectors」2016-08 上傳。各章對應關係：第 1 集 Vectors（ch02）、第 2 集 span/basis（ch03）、第 3 集 linear transformations（ch01、ch05，Grant 自稱「大概是理解線代最重要的一個概念」）、第 4 集 matrix multiplication as composition（ch06）、第 6 集 determinant（ch09）、第 7 集 inverse/column space/null space（ch07、ch08、ch10）、第 9 集 dot products and duality（ch15、ch16，內積＝投影那個圖像）、第 13 集 change of basis（ch04、ch13）、第 14 集 eigenvectors and eigenvalues（ch11、ch12、ch13、ch14、ch20、ch21，含 eigenbasis 與 90° 旋轉沒有實特徵向量）。讀完本書帶著「會講」的眼睛回去看一遍，每一集都會點頭。播放清單：<https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab>　官網主題頁：<https://www.3blue1brown.com/topics/linear-algebra>

- **Philip N. Klein，《Coding the Matrix: Linear Algebra through Computer Science Applications》**（Newtonian Press, 2013）。**這條路最對工程師胃口的一本**。Brown 大學，從程式與 CS 應用切入線代——影像、搜尋、糾錯碼。如果你想動手寫程式驗證本書的每個概念（而不只是在紙上推演），這是配套。<https://en.wikipedia.org/wiki/Philip_N._Klein>

- **Kurt Bryan & Tanya Leise，《The $25,000,000,000 Eigenvector: The Linear Algebra Behind Google》，SIAM Review 48(3)（2006）**。接 ch21。**標題就是 PageRank 那一章的驚嘆點**——把 PageRank 完全當成一個特徵向量問題從線代角度講透（隨機矩陣、Perron–Frobenius、阻尼 0.85、power iteration），深度恰好接本書、又補了嚴格細節。想把 ch21 每一步釘死，這是最佳單篇。<https://epubs.siam.org/doi/10.1137/050623280>

- **Sergey Brin & Larry Page，《The Anatomy of a Large-Scale Hypertextual Web Search Engine》（WWW7, 1998）**。接 ch21。PageRank 的原始論文，第 2.1 節定義 PageRank 與隨機衝浪者模型、給出阻尼係數。「十億帝國的地基」原文，篇幅不長、工程味很重。landscape 驗證過的 upenn 講義鏡像：<https://www2.math.upenn.edu/~kazdan/210/210F08/LectureNotes/Google/Brin-Page.html>　（ch21 另引用了 Stanford infolab 鏡像 <http://infolab.stanford.edu/~backrub/google.html>，內容相同但 2026-06 取回逾時、**未驗證**，建議用上面 upenn 鏡像。）

- **David C. Lay 等，《Linear Algebra and Its Applications》**（Pearson）。**經典的應用導向教科書**，亦採用 Strang 的「四大子空間」呈現，例子多、偏工程。**⚠️ 版次未釘死**：常見最新為第 5/6 版，但本書查證時未取回單一權威頁面確認確切年份與版次；引用或購買前請以實際取得的 Pearson 頁面為準，**不要憑記憶寫死版次年份**。

- **機器學習銜接（本書到此為止、指向下一站）**：本書 ch20 把 PCA 講成「主軸＝共變異矩陣的特徵向量」，但只到線性主軸為止。**非線性降維**（資料躺在彎曲的低維流形上、線性主軸抓不到）——autoencoder、t-SNE、UMAP——是把「降維」推廣到非線性的方向，屬於機器學習而非線代。最小平方（ch16）是線性迴歸的線代骨架；SVD（ch19）是推薦系統潛在因子與矩陣補全的核心。這些是「線代之後」的題目，沒有單一指定連結；Strang 第六版新增的「資料學習」章是溫和的接口，往下走則進入 ML 教材的領地。

---

## 如果只看三樣

時間有限就看這三樣，它們剛好涵蓋三條路、互不重疊：

1. **3Blue1Brown《Essence of Linear Algebra》全系列**（免費，約 3 小時）。**把幾何直覺釘死的最快路徑**。本書的幾何語言（格線保持平行等距、特徵向量是留在自己 span 上的軸）與它同源——讀完本書帶著「會講」的眼睛重看一遍，是性價比最高的複習。三條路之前的「再看一遍」。

2. **Gilbert Strang MIT 18.06**（OCW 免費，完整一學期課程）。**把計算與工程面補滿的完整課程**。本書幾何優先、他幾何與計算並重；四大子空間、正定判據、最小平方與 QR 的數值處理，比本書深、例子多。往數值與應用兩條路的主幹。

3. **Sheldon Axler《Linear Algebra Done Right》第四版**（Open Access 免費 PDF）。**把嚴格證明補滿的標準參考**。determinant-free、乾淨的一般 n 維證明——本書刻意沒展開的譜定理、SVD 存在性、向量空間公理，那裡有嚴格版。往抽象走的主幹，也是本書「張量」那個洞的補丁。

> 三樣的分工：**3B1B 給你眼睛、Strang 給你手、Axler 給你嘴**（能把證明講清楚）。三個都是免費的——線代是少數「最好的入門資源恰好都公開」的數學領域，沒有藉口不看。

---

## 書架鄰書的銜接點

你現在戴上了線代的眼鏡。書架上有幾本相鄰的書，本書遇到重疊主題時，刻意只講「線代這一側」，把另一側指向它們。現在你有了線代的底，這幾本會讀得更深。

| 鄰書 | 共同主題 | 本書講哪一面（哪章） | 那本書講哪一面 |
|---|---|---|---|
| 《圓的影子》 | 複數即旋轉 | 旋轉的複特徵值 e^{±iθ}、為何沒有實不變方向（ch12） | **為什麼**乘 e^{iθ} 是旋轉、複數乘法為何是旋轉加縮放（其 ch07–08） |
| 《圓的影子》 | 正交基與函數 | 內積、正交、投影（ch15–17） | 無窮維版：sin/cos 是正交基底、Fourier 級數＝換到正弦基底的座標 |
| 《馴服隨機》 | 共變異與 PCA | 為什麼主軸是特徵向量、第一主成分解釋 75% 變異（ch20） | 共變異在統計上量什麼、相關係數如何正規化（其 ch10） |
| 《馴服隨機》 | 馬可夫與 PageRank | 穩態＝λ=1 的特徵向量、power iteration 為何收斂（ch21） | 馬可夫為何忘記起點、遍歷性與穩態存在條件（其 ch21） |
| 《馴服無限》 | 線性即局部近似 | 「線性是我們唯一算得動的那塊」（ch01／ch22） | 導數即最佳線性近似、微分把曲線在無窮小尺度拉直成線性 |
| 《佇列論》 | 馬可夫運算 | 離散隨機矩陣、穩態特徵向量（ch21） | 連續時間馬可夫鏈與排隊網路的運算、穩態計算 |

幾句話把銜接點說清楚：

- **《圓的影子》（三角函數）**——本書「函數也是向量」那個洞的出海口。ch12 講「旋轉的特徵值是 e^{±iθ}」，《圓的影子》ch07–08 講「為什麼 e^{iθ} 是旋轉」，兩本書從兩側講同一枚硬幣。再往深一層，你在 ch15–17 學的投影與正交基底，到了無窮維就是傅立葉分析——sin/cos 是正交基底、Fourier 級數是「換到正弦基底的座標」。本書到正交基底的門口，那本書帶你走進去。

- **《馴服隨機》（機率統計）**——書架上跟本書配合最緊的一對。共變異與相關（其 ch10）是 ch20 PCA 的統計那一側；馬可夫鏈（其 ch21）是 ch21 PageRank 的世界觀那一側。本書講「為什麼主軸是特徵向量、穩態為什麼是 λ=1 的特徵向量」（線代機制），那本講「共變異在量什麼、馬可夫為什麼忘記起點」（機率世界觀）。兩本一起讀，PCA 與 PageRank 會從「會算」變成「兩面都懂」。

- **《馴服無限》（微積分）**——本書 ch01／ch22 反覆說的「線性是我們唯一算得動的那塊」，在那本書裡是字面意義：整個微積分就是「把彎的東西局部換成線性」的技藝——導數即最佳線性近似，微分把曲線在無窮小尺度拉直成線性。讀那本書時你會發現，它每一頁都在偷偷用線代。

- **《佇列論》**——ch21 的隨機矩陣往應用延伸的方向。離散時間的馬可夫鏈與穩態特徵向量（本書）推廣到連續時間的轉移與排隊網路運算（那本書），是同一套穩態思維在排隊系統上的展開。

---

一句話帶走這份地圖：**三條路、三樣免費資源（3B1B 給眼睛、Strang 給手、Axler 給嘴），加上書架上四本從別的角度講同一些東西的鄰書——你已經不是當初把矩陣當數字表格的那個人了，剩下的只是挑一個方向往下走。**
