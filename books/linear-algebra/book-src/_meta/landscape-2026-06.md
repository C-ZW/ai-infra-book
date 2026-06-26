# 線性代數欣賞書 — 事實基準（landscape-2026-06）

> 本檔是全書的**事實基準（fact baseline）**：歷史歸屬、年代、術語起源、當代參考資源的查證結果。
> 日期戳：2026-06。
> **時效性：低（LOW）**。線性代數是接近永恆的數學，版本/價格/硬體幾乎不變。真正的風險不是「過時」，而是**歷史歸屬的迷思**——「某某發明某某」在線代裡常常是民間傳說。本檔對每條歸屬都標來源並以 ⚠️ 標記未確認或有爭議者。
>
> 用法：寫章節時凡引用人名、年代、術語起源、外部資源連結，一律以本檔為準。修正時更新本檔並在 maintenance 掃描日誌記一行；推翻既有基準需兩個獨立來源。
>
> 凡例：✅ 多來源一致、可放心引用｜⚠️ 有爭議／來源衝突／需謹慎措辭｜🔥 常被誤傳，書中可當「直覺的陷阱」素材。

---

## 1. 矩陣與行列式的歷史（matrix & determinant）

- ✅ **「matrix」一詞由 James Joseph Sylvester（1814–1897）於 1850 年提出**。出自論文 *On the Theory of Syzygies and Matrices*（投 Philosophical Transactions of the Royal Society）。他把 matrix 定義為「an oblong arrangement of terms（一個長方形的項排列）」，視為從中取方陣可生出各種行列式的「母體」；matrix 源自拉丁文「子宮／母體」。Sylvester 也創造／重新使用了 graph、discriminant、minor、nullity、canonical form 等大量術語。
  - 來源：https://mathshistory.st-andrews.ac.uk/HistTopics/Matrices_and_determinants/
  - 來源（Higham, *Cayley, Sylvester, and Early Matrix Theory*, 2008）：https://eprints.maths.manchester.ac.uk/954/1/cay_syl_07.pdf

- ✅ **Arthur Cayley 才是矩陣代數的奠基者**。1858 年 *A Memoir on the Theory of Matrices*（Phil. Trans. Roy. Soc., vol. 148, pp. 17–37；1857-12-10 收稿、1858-01-14 宣讀）。他引入單位矩陣、矩陣加法與乘法、逆矩陣、矩陣的冪，並指出乘法不可交換。**🔥 釐清：Sylvester 造詞（1850），Cayley 造理論（1858）——兩件事，常被混為一談。**
  - 來源：https://mathshistory.st-andrews.ac.uk/HistTopics/Matrices_and_determinants/
  - 來源（書目著錄）：https://www.lynge.com/en/mathematics/42295-a-memoir-on-the-theory-of-matrices-...

- ✅ **Cayley–Hamilton 定理**（每個方陣滿足自己的特徵方程式）出現在 Cayley 1858 那篇。Cayley 只對 2×2、3×3 給證明，宣稱驗證過 4×4，並寫下名句「I have not thought it necessary to undertake the labour of a formal proof of the theorem in the general case…」。
  - ⚠️ **命名的真相**：Hamilton 早在 1853 年就以四元數的線性函數逆運算證了一個特例（對應某類實／複矩陣），故定理掛兩人名字。**一般 n×n 的完整證明兩人都沒做**——後來由 Frobenius（1878）等人完成。書中若提「Cayley–Hamilton」要避免說成「Cayley/Hamilton 證明了一般情形」。
  - 來源：https://nhigham.com/2020/11/03/what-is-the-cayley-hamilton-theorem/
  - 來源：https://en.wikipedia.org/wiki/Cayley%E2%80%93Hamilton_theorem

- ✅ **行列式比矩陣老**——這是線代史最反直覺的事實之一，適合當開場。行列式比 matrix 一詞早約 167 年出現：
  - **關孝和（Seki Takakazu，1642–1708）1683 年**《解伏題之法》以表格形式發展矩陣方法、引入行列式（未用此名），算到 2×2 至 5×5。**目前公認是世界最早系統研究行列式者。**
  - **Leibniz**：在與 de l'Hôpital 的通信中，用行列式判斷線性方程組解的存在（係數矩陣行列式為 0 的條件）。⚠️ **年代來源衝突**：MacTutor 寫 **1693**（「關孝和之後十年」）；另一些二手來源寫 **1683**（與關同年）。最防禦性的說法：「關孝和 1683 年，Leibniz 約 1690 年代初獨立得到類似想法，且關的版本更一般。」不要把 Leibniz 釘成精確某年。
  - **Cramer 1750**：*Introduction à l'analyse des lignes courbes algébriques* 給出 n×n 系統的一般法則（Cramer 法則），但未證明。
  - **Bézout 1764、Vandermonde 1771**：行列式計算方法。
  - **Laplace 1772**：用「resultant」稱行列式，給出今日所稱的 Laplace 展開。
  - 來源：https://mathshistory.st-andrews.ac.uk/HistTopics/Matrices_and_determinants/
  - 來源（關孝和傳）：https://mathshistory.st-andrews.ac.uk/Biographies/Seki/
  - 來源：https://en.wikipedia.org/wiki/Seki_Takakazu

---

## 2. 高斯消去法（Gaussian elimination）

- ✅ **方法遠早於高斯**。中國《九章算術》第八章「方程」就在算籌（counting rods）上做消元，等價於今日的高斯消去／列運算（紅籌為正、黑籌為負）。
  - ⚠️ **《九章算術》的年代要小心措辭**：常見「179 CE」其實是兩件青銅標準量器上題銘的年份；學界認為**成書不晚於約 93 CE**，內容可追溯更早。最防禦性說法：「成書約西元一世紀（不晚於 93 CE），現存題銘可溯至 179 CE。」不要簡單寫「成書於 179 CE」。
  - ✅ 重點：**「方程」章的消元法比高斯（1777–1855）早了近兩千年。**
  - 來源：https://en.wikipedia.org/wiki/The_Nine_Chapters_on_the_Mathematical_Art
  - 來源：https://en.wikipedia.org/wiki/Fangcheng_(mathematics)

- ✅ **高斯做的是「形式化＋命名」，不是發明**。背景是 1801 年穀神星（Ceres）被發現又失蹤，高斯用最小平方法定出軌道；他在 *Theoria Motus*（1809）系統處理最小平方，消元法在其中作為計算工具。**🔥 「高斯發明了高斯消去法」是錯的**——他形式化了一個早已存在的方法，名字才掛上去。
  - ⚠️ 注意：最小平方法的首次發表是 Legendre（1805）；高斯宣稱自己 1795 年就在用。這是另一段著名的優先權爭議，書中提及最小平方時要小心。
  - 來源：https://www.cis.upenn.edu/~cis6100/Notices-06-11-Gausselim.pdf （Grcar, *Mathematicians of Gaussian Elimination*, AMS Notices）
  - 來源：https://thatsmaths.com/2021/06/24/gauss-predicts-the-orbit-of-ceres/

- ✅ **🔥 兩個 Jordan 的混淆（Gauss–Jordan 的「Jordan」）**：是**測地學家 Wilhelm Jordan（1842–1899，德國）**，不是法國數學家 Camille Jordan（1838–1922）。Wilhelm Jordan 為了在測量平差中最小化誤差，改良了消元法的穩定性，寫在其《測量學手冊》（*Handbuch der Vermessungskunde*）第三版（1888）。
  - 同年 B.-I. Clasen 獨立發表了類似東西。
  - **🔥 釐清三個 Jordan：** Camille Jordan → Jordan 標準形、Jordan 曲線定理（法國數學家）；Wilhelm Jordan → Gauss–Jordan 消去（德國測地學家）；Pascual Jordan → Jordan 代數（德國物理學家）。書中講 Gauss–Jordan 時務必標明是**測地學家 Wilhelm Jordan**。
  - 來源：https://en.wikipedia.org/wiki/Wilhelm_Jordan_(geodesist)
  - 來源：https://people.math.harvard.edu/~knill/teaching/math22a2018/exhibits/gaussjordan/index.html

---

## 3. 向量空間與抽象公理（vector space / axioms）

- ✅ **Hermann Grassmann，*Die Ausdehnungslehre*（延伸論），1844 年初版**。向量、線性組合、線性獨立／相依、維度、純量積的觀念都已在 1844 年版中出現。原著極難讀、不受當時數學界青睞，1862 年出較易讀的改寫版。
  - 來源：https://mathshistory.st-andrews.ac.uk/HistTopics/Abstract_linear_spaces/

- ✅ **Giuseppe Peano 1888 年給出向量空間的公理化定義**（史上第一個實線性空間的公理定義）。出自 *Calcolo geometrico secondo l'Ausdehnungslehre di H. Grassmann*（都靈出版）。Peano 自承奠基於 Grassmann；該書第 IX 章的公理「幾乎可以原封不動出現在 1988 年的教科書裡」。Peano 也在同書引入 ∩、∪、∈ 等集合記號。
  - 來源：https://mathshistory.st-andrews.ac.uk/HistTopics/Abstract_linear_spaces/

- ✅ **「vector」一詞由 William Rowan Hamilton 提出**。Hamilton 1843 年發明四元數（quaternions，一個 4 維向量空間的重要實例）；**1846 年**在四元數的脈絡中正式引入 scalar 與 **vector** 這兩個術語。vector 源自拉丁文 *vehere*（to carry，搬運／載運，與 vehicle 同源），原是天文幾何的技術詞。
  - **🔥 注意年代細分**：發明四元數＝1843；造「vector」一詞＝1846。兩者差三年，別合併。
  - 來源：https://mathshistory.st-andrews.ac.uk/Miller/mathword/v/
  - 來源：https://en.wikipedia.org/wiki/Quaternion

- ✅ **後續抽象化**：Stefan Banach 1920 年博士論文確立了完全公理化的（賦範完備）向量空間取向（Banach 空間）；Hermann Weyl 等人也參與了 20 世紀初的抽象化。
  - 來源：https://mathshistory.st-andrews.ac.uk/HistTopics/Abstract_linear_spaces/

---

## 4. 「eigen-」術語（eigenvalue / eigenvector）

- ✅ **「eigen」是德文，意為「自己的／固有的／特有的」（own / peculiar to / characteristic of）**。數學裡傳達「內稟、特徵」之意。**🔥 nuance：說「eigen 就是英文 self」太簡化**——較準的是「own / characteristic / proper（固有的、特徵的）」；中文「特徵」正是抓住這層意思。
  - 來源：https://old.maa.org/press/periodicals/convergence/math-origins-eigenvectors-and-eigenvalues
  - 來源：https://jeff560.tripod.com/e.html （Earliest Known Uses of … (E)）

- ✅ **David Hilbert 1904 年在積分方程著作中用 Eigenfunktion、Eigenwert**（*Grundzüge einer allgemeinen Theorie der linearen Integralgleichungen*），由其學派推廣「eigen-」用法成為標準。
  - 來源：https://jeff560.tripod.com/e.html
  - 來源：https://en.wikipedia.org/wiki/Spectral_theory

- ✅ **更早的同義詞**：Sylvester 1883 年論文 *On the Equation to the Secular Inequalities in the Planetary Theory* 用 **latent roots（latent point/latent value，潛根）**。歷史上還用過 characteristic value（特徵值）、secular value、proper value。到 1946 年（Jeffreys *Methods of Mathematical Physics*）eigenvalue 已與 characteristic value、latent root 視為同義。
  - 來源：https://old.maa.org/press/periodicals/convergence/math-origins-eigenvectors-and-eigenvalues
  - 來源：https://jeff560.tripod.com/e.html

---

## 5. 譜定理／對稱矩陣（spectral theorem）

- ✅ **Cauchy 1829 年首次一般地證明：實對稱矩陣的特徵值都是實數**，且實對稱矩陣可正交對角化（即對稱矩陣版的譜定理）。這是「主軸定理」（principal axis theorem，橢球主軸）的代數對應。
  - 18 世紀 Lagrange、Laplace 已在解線性微分方程組（力學問題）時碰到代數特徵值問題；Cauchy 1829 的論文啟動了到 1870 年代成形的矩陣譜理論。
  - 來源：https://www.sciencedirect.com/science/article/pii/0315086075900324 （Hawkins, *Cauchy and the Spectral Theory of Matrices*）
  - 來源：https://en.wikipedia.org/wiki/Principal_axis_theorem

- ✅ **「spectrum（譜）」一詞由 David Hilbert 引入**（無窮多變數二次型／Hilbert 空間理論的脈絡）。
  - 🔥 **絕佳的書中軼事**：Hilbert 取名「spectrum」純粹出於數學動機（橢球主軸定理的無窮維版本），**早於量子力學**；後來量子力學發現譜理論恰好能解釋原子的「光譜（spectrum）」，純屬巧合。Hilbert 自言：「我純為數學興趣發展無窮多變數理論，還叫它 spectral analysis，毫無預感它日後會用到物理的真實光譜上。」
  - ⚠️ 另說（Dieudonné 歸因）：Hilbert 採「spectrum」可能受 Wilhelm Wirtinger 1897 年一篇關於 Hill 微分方程的論文影響。軼事的核心（命名早於量子力學、純數學動機）穩固；確切靈感來源可加「據考」緩衝。
  - 來源：https://en.wikipedia.org/wiki/Spectral_theory
  - 來源：https://en.wikipedia.org/wiki/Spectrum_(functional_analysis)

---

## 6. 奇異值分解（SVD）的歷史

- ✅ **最早功勞歸 Eugenio Beltrami（1873）與 Camille Jordan（1874），各自獨立**：發現雙線性形式（以矩陣表示）的奇異值在正交代換下構成一組完整不變量。
- ✅ **James Joseph Sylvester（1889）**又獨立得到實方陣的 SVD（看似不知 Beltrami、Jordan 之工作），給了計算方法但寫得「晦澀」。
- ✅ **Erhard Schmidt 與 Hermann Weyl** 後來從積分方程的角度切入（與前三人從線性代數切入不同）。
- ✅ **Eckart–Young（1936）**把 SVD 推廣到長方矩陣，並證明**最佳低秩近似定理**：見下條。
  - 來源：https://www.cis.upenn.edu/~cis5150/cis515-15-sl12.pdf
  - 來源（SVD 早期史專文，scribd 收錄 Stewart）：https://www.scribd.com/document/495985801/On-the-early-history-of-SVD

- ✅ **Eckart–Young 定理（1936）**：對矩陣 A 的 SVD 截斷到前 k 項，得到的就是**在 Frobenius 範數下最佳的 rank-k 近似**；近似誤差等於被丟掉的奇異值（從第 k+1 個起）平方和開根號。
  - ⚠️ 推廣版（Eckart–Young–Mirsky）：對**任何么正不變範數**（Frobenius、譜範數、核範數…）截斷 SVD 都是最佳 rank-k 近似（Mirsky 1960）。書中講「SVD 給最佳壓縮」時，這是嚴格依據。
  - 原始出處：Eckart, C. & Young, G. (1936) *The Approximation of One Matrix by Another of Lower Rank*. Psychometrika, 1, 211–218.
  - 來源：https://www.scirp.org/reference/referencespapers?referenceid=1296328

---

## 7. Perron–Frobenius 定理（PageRank 背後的數學）

- ✅ **Oskar Perron（1907）**先處理**正矩陣（所有元素 > 0）**：存在唯一的、絕對值最大的實特徵值（Perron 根／主特徵值），對應的特徵向量可取為**所有分量嚴格為正**。
- ✅ **Georg Frobenius（1912）**把結果推廣到某類**非負矩陣**（不可約非負矩陣）。
- ✅ 這正是 PageRank「唯一正穩態特徵向量」存在性的數學保證（Google 矩陣是正的隨機矩陣 → 主特徵向量唯一且各分量為正）。
  - 來源：https://en.wikipedia.org/wiki/Perron%E2%80%93Frobenius_theorem

---

## 8. PageRank

- ✅ **Sergey Brin & Larry Page，史丹佛大學，1998 年論文 *The Anatomy of a Large-Scale Hypertextual Web Search Engine***，發表於 WWW7（第七屆全球資訊網大會，1998-04），刊於 *Computer Networks and ISDN Systems* 30(1–7), pp. 107–117。
  - ⚠️ 另有 1998/1999 的 Stanford 技術報告 *The PageRank Citation Ranking: Bringing Order to the Web*（Page, Brin, Motwani, Winograd）。書中提「PageRank 論文」最好區分「Anatomy 那篇（WWW7, 1998）」與「PageRank 技術報告」。
  - 來源：https://www2.math.upenn.edu/~kazdan/210/210F08/LectureNotes/Google/Brin-Page.html
- ✅ **PageRank ＝ Google 矩陣的主特徵向量（dominant eigenvector）／隨機漫步的穩態分布（stationary distribution）**。Google 矩陣的第二大特徵值滿足 **|λ₂| ≤ c**（阻尼係數），且 Haveliwala–Kamvar（2003）證明對真實 web 超連結圖通常**緊到等於 c**（≈0.85）——這界定了 power iteration 的收斂速率。⚠️ 勿寫成「λ₂ 恰等於 c」的裸述；正確版是「|λ₂|≤c，真實圖緊到等於阻尼」。
  - 來源：https://nlp.stanford.edu/pubs/secondeigenvalue.pdf （Haveliwala & Kamvar, *The Second Eigenvalue of the Google Matrix*, 2003）
- ✅ **阻尼係數（damping factor）通常設 0.85**：代表「隨機衝浪者」在每一頁有 0.85 機率沿連結走、約 0.15 機率跳到隨機頁。
  - 來源：https://www2.math.upenn.edu/~kazdan/210/210F08/LectureNotes/Google/Brin-Page.html
  - 來源（SIAM 科普）：https://www.siam.org/media/jzyklznu/mathmatters_google_pagerank.pdf

---

## 9. 主成分分析（PCA）

- ✅ **兩個獨立起源：**
  - **Karl Pearson（1901）**，*On Lines and Planes of Closest Fit to Systems of Points in Space*：從**純幾何**角度提出——找在最小平方意義下最貼合點雲的低維子空間。**Pearson 本人並未用「principal components」一詞。**
  - **Harold Hotelling（1933）**，*Analysis of a Complex of Statistical Variables into Principal Components*：給出**統計**表述（找變異數最大的正交線性組合），並**創造「principal components」這個名字**。
- ✅ PCA 與 SVD／共變異數矩陣特徵分解的關係：主成分＝資料共變異數矩陣的特徵向量＝（中心化）資料矩陣 SVD 的右奇異向量。
  - 來源：https://allmodelsarewrong.github.io/pca.html
  - 來源（PCA 史）：https://dl.acm.org/doi/10.1016/j.jmva.2021.104814

---

## 10. 線性代數基本定理／四大子空間（four fundamental subspaces）

- ✅ **「四大基本子空間（four fundamental subspaces）」是 Gilbert Strang 的教學框架**，不是一條古典的具名定理。四個子空間＝A 的行空間（column space）與零空間（null space），以及 Aᵀ 的行空間（＝列空間）與零空間（左零空間）。Strang 把它命名為「Fundamental Theorem of Linear Algebra」並在其教科書與 MIT 18.06 課程中大力推廣。
  - ⚠️ 措辭提醒：這是 **Strang 的 pedagogical framing／命名**。David Lay 等教科書也採用「四大子空間」呈現，但「Fundamental Theorem of Linear Algebra」這個招牌主要是 Strang 推廣的，並非數學界傳統定名。書中可說「Strang 稱之為…」。
  - 來源（Strang 本人專文）：https://www.engineering.iastate.edu/~julied/classes/CE570/Notes/strangpaper.pdf
  - 來源（MIT 18.06）：https://web.mit.edu/18.06/www/Essays/newpaper_ver3.pdf

---

## 常被誤傳（⚠️ 釘死正確版）

> 這一節是寫書的金礦——每條都可放進「直覺的陷阱／故障視角」。

| # | 常見誤傳（錯） | 釘死的正確版 | 來源 |
|---|---|---|---|
| 1 | 「高斯發明了高斯消去法」 | ❌。消元法早於高斯近兩千年（《九章算術》「方程」章）。高斯做的是**形式化＋命名**（最小平方、穀神星軌道，1809）。 | Grcar (AMS Notices) |
| 2 | 「Gauss–Jordan 的 Jordan ＝ Camille Jordan」 | ❌。是**測地學家 Wilhelm Jordan（1842–1899）**，不是法國數學家 Camille Jordan（Jordan 標準形那位），也不是物理學家 Pascual Jordan（Jordan 代數）。三個 Jordan。 | Wikipedia: Wilhelm Jordan (geodesist) |
| 3 | 「Cayley 發明了行列式」 | ❌。行列式**比 matrix 一詞老約 167 年**：關孝和 1683、Leibniz 1690 年代初、Cramer 1750、Laplace 1772。Cayley（1858）造的是**矩陣代數**。 | MacTutor |
| 4 | 「Sylvester 造了矩陣理論」 | ❌。Sylvester **造了 matrix 這個詞（1850）**；**理論是 Cayley（1858）**。造詞≠造理論。 | Higham 2008 |
| 5 | 「Cayley/Hamilton 證明了 Cayley–Hamilton 定理的一般情形」 | ❌。Hamilton（1853）證特例、Cayley（1858）只證 2×2、3×3。一般 n×n 由 Frobenius 等後人完成。 | Higham; Wikipedia |
| 6 | 「eigen 就是英文 self（自己）」 | ⚠️ 太簡化。eigen ＝ own / characteristic / proper（固有的、特徵的）。中文「特徵」正抓住這層。 | MAA Convergence |
| 7 | 「Hilbert 的 spectrum 命名來自量子力學的光譜」 | ❌。時序相反——Hilbert 純為數學取名「spectrum」，**早於量子力學**；量子力學恰好用上是巧合。 | Wikipedia: Spectral theory |
| 8 | 「2×2 行列式只是平行四邊形面積的近似」 | ❌。是**精確（exact）的有號面積**：\|ad − bc\| 正好等於面積，符號表定向。不是近似。 | TU Delft / LibreTexts |
| 9 | 「PCA 是 Pearson 一個人發明的」 | ⚠️ 不完整。**兩個獨立起源**：Pearson（1901，幾何）與 Hotelling（1933，統計＋命名 principal components）。 | allmodelsarewrong; JMVA |
| 10 | 「SVD 是某一個人發明的／是 20 世紀的東西」 | ❌。Beltrami（1873）、Jordan（1874）各自獨立最早；Sylvester（1889）再獨立得到。最佳低秩近似是 Eckart–Young（1936）。 | Stewart (early history of SVD) |
| 11 | 「四大子空間是古典具名定理」 | ⚠️。是 **Gilbert Strang 的教學框架／命名**（MIT 18.06），非數學界傳統定名。 | Strang 專文 |
| 12 | 「行＝row、列＝column」（用大陸習慣） | 🔥 **在台灣相反！** 台灣：**列＝row（橫列）、行＝column（直行）**。與大陸**完全相反**，是惡名昭彰的陷阱。見下表。 | 線代啟示錄 |

---

## 台灣數學用語基準（禁簡體）

> **全書一律用台灣繁中用語。** 程式／設定一律英文。下表的 EN 對照供查證，書內正文用台灣繁中。
> **最關鍵：行＝column（直行）、列＝row（橫列）——與中國大陸相反，務必釘死。**

| EN term | 台灣繁中 | 一句話 | note |
|---|---|---|---|
| **row** | **列**（橫列） | 矩陣的橫向一排 | 🔥 大陸用「行」表 row，**完全相反**。台灣沿襲古書直寫慣例。 |
| **column** | **行**（直行） | 矩陣的縱向一排 | 🔥 大陸用「列」表 column，**完全相反**。 |
| row vector | 列向量 | 一個橫排的向量（1×n） | 對應「列＝row」 |
| column vector | 行向量 | 一個直排的向量（n×1）；預設向量寫法 | 對應「行＝column」；配合矩陣乘法慣例 |
| matrix | 矩陣 | 數的長方形排列 | — |
| vector | 向量 | 有方向與大小的量／空間中的點 | — |
| determinant | 行列式 | 方陣的一個純量（有號體積） | 注意「行列式」字面含行與列，但**是純量不是矩陣** |
| eigenvalue | 特徵值 | 線性變換只縮放不轉向的倍率 | 🔥 台灣用「**特徵**」，**不用大陸的「本徵」**。zh-tw 維基條目即作「特徵值」 |
| eigenvector | 特徵向量 | 變換後方向不變、只被縮放的向量 | 同上，用「特徵」 |
| rank | 秩 | 矩陣中線性獨立的行（或列）數 | 兩岸同字 |
| null space / kernel | 零空間（核） | 被矩陣映到零向量的所有向量 | kernel 亦譯「核」 |
| linear independence | 線性獨立（線性無關） | 沒有任何向量是其他向量的線性組合 | 兩種說法皆台灣慣用 |
| linear dependence | 線性相依（線性相關） | 至少一向量可由其他線性組合表出 | — |
| basis | 基底（基） | 能張成整個空間的最小線性獨立集 | — |
| dimension | 維度（維數） | 基底的大小 | — |
| diagonalization | 對角化 | 把矩陣化成對角矩陣（相似變換） | — |
| SVD | 奇異值分解 | A = UΣVᵀ，任何矩陣都可分解 | zh-tw 維基作「奇異值分解」 |
| orthogonal | 正交 | 內積為零（互相垂直） | — |
| orthonormal | 單範正交（正交規範） | 正交且長度為 1 | 大陸作「標準正交」 |
| spectral theorem | 譜定理 | 對稱／正規矩陣可（么正）正交對角化 | — |
| column space | 行空間 | 行向量張成的空間（＝值域 range） | 「行＝column」 |
| row space | 列空間 | 列向量張成的空間 | 「列＝row」 |
| elementary matrix | 基本矩陣 | 一次基本列運算對應的矩陣 | 大陸作「初等矩陣」 |

來源（台灣 row/column 慣例與兩岸對照）：
- 線代啟示錄〈兩岸線性代數的翻譯名詞參照〉：https://ccjou.wordpress.com/2012/04/17/%E5%85%A9%E5%B2%B8%E7%B7%9A%E6%80%A7%E4%BB%A3%E6%95%B8%E7%9A%84%E7%BF%BB%E8%AD%AF%E5%90%8D%E8%A9%9E%E5%8F%83%E7%85%A7/
- 維基百科（zh-tw）〈行向量與列向量〉：https://zh.wikipedia.org/zh-tw/%E8%A1%8C%E5%90%91%E9%87%8F%E8%88%87%E5%88%97%E5%90%91%E9%87%8F
- 維基百科（zh-tw）〈特徵值和特徵向量〉（用「特徵」非「本徵」）：https://zh.wikipedia.org/zh-tw/%E7%89%B9%E5%BE%81%E5%80%BC%E5%92%8C%E7%89%B9%E5%BE%81%E5%90%91%E9%87%8F

---

## 數值／詞彙錨點（pin 死，跨章一致）

- **行＝column（直行）、列＝row（橫列）**——台灣慣例，與大陸相反。全書最高優先級的一致性錨點。
- **特徵值／特徵向量**（不是「本徵值」）——台灣用「特徵」。
- **PageRank 阻尼係數＝0.85**（隨機跳轉機率＝0.15）。
- **2×2 行列式＝有號面積（精確，非近似）**；n×n 行列式＝有號 n 維體積。
- **行列式比 matrix 一詞老約 167 年**（關孝和 1683 vs Sylvester 造詞 1850）。
- **SVD 截斷＝最佳低秩近似**（Eckart–Young 1936，Frobenius／任意么正不變範數）。

---

## 當代延伸閱讀資源（驗證過連結）

> 以下連結皆實際取回確認過。標「免費」者為公開可取。

- ✅ **3Blue1Brown《Essence of Linear Algebra》**（Grant Sanderson）。15 部影片的視覺化系列，**第一章「Vectors」於 2016-08-06 上傳**（預覽章 2016-08-05）。YouTube **免費**。頻道 3Blue1Brown 由 Grant Sanderson 經營（頻道始於 2015）。
  - 官方頁：https://www.3blue1brown.com/lessons/eola-preview/
  - YouTube 播放清單：https://www.youtube.com/playlist?list=PLZHQObOWTQDPD3MizzM2xVFitgF8hE_ab
  - 第一章：https://www.youtube.com/watch?v=fNk_zzaMoSs

- ✅ **Gilbert Strang，MIT 18.06 Linear Algebra**。MIT OpenCourseWare **免費**（含影片、講義）。
  - https://ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/
  - 「四大基本子空間」課（Lecture 10）：https://www.ocw.mit.edu/courses/18-06-linear-algebra-spring-2010/resources/lecture-10-the-four-fundamental-subspaces

- ✅ **Gilbert Strang，*Introduction to Linear Algebra*，第六版（6th ed.，2023，Wellesley-Cambridge Press，ISBN 9781733146678）**。第六版較早引入「獨立行、秩、行空間」概念，並新增最佳化與資料學習的章節。
  - 作者書頁：https://math.mit.edu/~gs/linearalgebra/ila6/indexila6.html
  - SIAM 版：https://epubs.siam.org/doi/book/10.1137/1.9781733146678
  - （⚠️ 書本身非免費；OCW 課程免費。）

- ✅ **Sheldon Axler，*Linear Algebra Done Right*，第四版（4th ed.，2024）**。determinant-free（把行列式放到全書最後）取向；**第四版為 Open Access，官方免費 PDF**。新增多線性代數一章（雙線性／二次型、張量積、以交錯多線性形式建構行列式）。
  - 官方免費頁：https://linear.axler.net/
  - Springer（Open Access, CC BY-NC 4.0）：https://link.springer.com/book/10.1007/978-3-031-41026-0

- ✅ **Philip N. Klein，*Coding the Matrix: Linear Algebra through Computer Science Applications*（Newtonian Press, 2013）**。Brown 大學，從程式／CS 應用切入線代。
  - https://en.wikipedia.org/wiki/Philip_N._Klein
  - 配套 Coursera 課（Internet Archive 鏡像）：https://archive.org/details/academictorrents_54cd86f3038dfd446b037891406ba4e0b1200d5a

- ✅ **David C. Lay 等，*Linear Algebra and Its Applications***。經典應用導向教科書，亦採用「四大子空間」呈現。
  - ⚠️ 版次：常見最新為第 5/6 版（Pearson）。本次未取回單一權威頁面釘死確切年份與版次，書中引用時請以實際取得的 Pearson 頁面為準，**勿憑記憶寫死版次年份**。

---

## 掃描協定備註

- 本檔時效性低；下次掃描重點仍是**歷史歸屬措辭**（特別是迷思表的 12 條），而非版本／價格。
- 兩處明確的**來源衝突**已標 ⚠️，引用時採最防禦性說法、勿寫死：
  1. **Leibniz 行列式年代**（1683 vs 1693）→ 寫「1690 年代初／關孝和之後約十年」。
  2. **《九章算術》成書年代**（93 CE vs 題銘 179 CE）→ 寫「約西元一世紀（不晚於 93 CE）」。
- David Lay 版次未釘死（⚠️），引用前需補查 Pearson 官方頁。
