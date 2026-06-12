# 附錄 C — 延伸閱讀總地圖

> 全書十六章的延伸閱讀，在這裡彙整成一張地圖：先給「如果只看三樣」，再分三條路線——往嚴格走、往應用走、往欣賞走——對應 ch16 的下一步地圖。只收 `_meta/landscape-2026-06.md` 或各章延伸閱讀已查證過的資源（連結現況以 2026-06 為基準），不收未驗證的新東西。各章原始清單的完整去處，見文末索引表。

## 如果只看三樣

1. **Steven Strogatz《無限的力量》**（Infinite Powers，黃駿譯，旗標，2020）——與本書同一個敵人（無限）、同一種打法（直覺優先），讀完本書再讀它，你會以同行而非讀者的身分驗收他的敘事，是成本最低的全書總複習（見 ch01–ch16，幾乎每章點名）。
2. **3Blue1Brown《Essence of Calculus》**：https://www.3blue1brown.com/lessons/essence-of-calculus/ （YouTube 播放清單：https://www.youtube.com/playlist?list=PLZHQObOWTQDMsr9K-rj53DwVRMYO3t5Yr ）——把你剛建好的直覺全部變成會動的圖，而且現在的你看得出每一集在哪裡停住、省略了哪個證明——「看得出省略」正是本書交付的能力（見 ch16 的收官建議）。
3. **William Dunham《The Calculus Gallery: Masterpieces from Newton to Lebesgue》**（Princeton UP）：https://press.princeton.edu/books/paperback/9780691182858/the-calculus-gallery ——工程師的下一步不是刷題、是看原典級證明怎麼蓋起來；難度恰好比本書高一階，從 Newton 一路走到 Lebesgue，是三條路線中「往嚴格走」最自然的第一步（見 ch08、ch09、ch11、ch14）。

## 往嚴格走（實分析方向）

本書刻意停在直覺與結構理解；想把每個「本書不證」補上，走這條。

- **Spivak《Calculus》第 4 版**（Publish or Perish，2008）——證明導向微積分的標竿、「對嚴格性的初次正面相遇」；先讀極限與連續那幾章，看 ε-δ 在行家手裡可以多優雅（見 ch14）。
- **Apostol《Calculus》兩卷**（Wiley，2nd ed. 1967/1969）——理論與技巧並重、「先積分後微分」的 Caltech 傳統教本；想照歷史的真實順序（累積先於變化率）系統重學，選它（見 ch07–ch08 的順序對帳）。
- **Judith Grabiner〈Who Gave You the Epsilon? Cauchy and the Origins of Rigorous Calculus〉**：https://www.jstor.org/stable/2975545 ——「觀念奠基在柯西、符號定稿在魏爾斯特拉斯」這條主線的史學依據，嚴格化故事的單篇最佳入口（見 ch03、ch14）。
- **Dedekind《Essays on the Theory of Numbers》**（Beman 英譯，Project Gutenberg 第 21016 號，免費）：https://www.gutenberg.org/ebooks/21016 ——第一篇就是 1872 年切割原典，不到三十頁，數學史上少見的「原作比教科書好讀」（見 ch14）。
- **H. Jerome Keisler《Elementary Calculus: An Infinitesimal Approach》**（CC 授權免費線上版）：https://people.math.wisc.edu/~hkeisler/calc.html ——用 Robinson 的無窮小從頭教一遍大一微積分；翻第 2 章，看 dy/dx 當真正的除法用是什麼感覺（見 ch14）。
- **G. H. Hardy〈Weierstrass's non-differentiable function〉**（Trans. AMS, 1916）：https://www.ams.org/journals/tran/1916-017-03/S0002-9947-1916-1501044-1/S0002-9947-1916-1501044-1.pdf ——放寬怪獸條件至 ab ≥ 1 的原始論文，前兩頁的歷史回顧與條件陳述就值回票價（見 ch13）。
- **Johan Thim《Continuous Nowhere Differentiable Functions》**（Luleå 碩士論文, 2003）：https://ltu.diva-portal.org/smash/get/diva2:1022983/FULLTEXT01 ——怪獸圖鑑：Bolzano、Takagi、van der Waerden……每隻都附完整證明（見 ch13）。
- **Mörters & Peres《Brownian Motion》**：https://www.mi.uni-koeln.de/~moerters/book/book.pdf ——定理 1.27 就是「路徑以機率 1 處處不可微」的正牌證明，讀第一章即可（見 ch13）。
- **Needham《Visual Complex Analysis》25 週年版**（OUP，2023）：https://global.oup.com/academic/product/visual-complex-analysis-9780192868923 ——本書刻意留下的複變之洞（e^{iθ} 只到形式操作）的補完方向：501 張圖把複變講成幾何，嚴格但極度視覺，與本書氣質相容（見 ch09）。

## 往應用走（微分方程與 ML 數學方向）

想把「會欣賞」升級成「會操作」——正課、微分方程、ML 數學與數值工藝，走這條。

- **MIT OCW 18.01 Single Variable Calculus**：https://ocw.mit.edu/courses/18-01-single-variable-calculus-fall-2006/ （較新版本：https://ocw.mit.edu/courses/18-01-calculus-i-single-variable-calculus-fall-2020/ ）——標準正課版的單變數微積分（含 2007 年 Jerison 錄影）；本書刻意不教的解題技巧與更多例題在這裡補（見 ch04、ch06、ch07）。
- **MIT OCW 18.03 Differential Equations**（Spring 2010）：https://ocw.mit.edu/courses/18-03-differential-equations-spring-2010/ ——正式學微分方程解法與理論的標準課；先看前幾講的方向場與一階方程，可直接接上 ch10（見 ch10）。
- **Paul's Online Math Notes**：https://tutorial.math.lamar.edu/ ——Algebra 到 Calculus I–III、微分方程的免費筆記，查技巧用的工具書；Lagrange 乘數那頁（https://tutorial.math.lamar.edu/classes/calciii/lagrangemultipliers.aspx ）是 ch06 一句話帶過的約束最佳化路標（見 ch06）。
- **3Blue1Brown〈Gradient descent〉與〈Backpropagation calculus〉**：https://www.3blue1brown.com/lessons/gradient-descent 、https://www.3blue1brown.com/lessons/backpropagation-calculus/ ——從 ch06 的一維坡走進億維地形，再看連鎖規則怎麼變成 backprop 的記帳系統（見 ch06、ch15）。
- **Parr & Howard〈The Matrix Calculus You Need For Deep Learning〉**：https://explained.ai/matrix-calculus/ ——ch15 一句話帶過的矩陣微積分完整地圖；它假設的起點恰好是你現在的程度（單變數連鎖規則）（見 ch15）。
- **Rumelhart, Hinton & Williams〈Learning representations by back-propagating errors〉**（Nature 323, 1986）：https://www.nature.com/articles/323533a0 ——使 backprop 普及的原始論文，數學核心就是連鎖規則（見 ch15）。
- **Gaffer On Games〈Integration Basics〉**：https://gafferongames.com/post/integration_basics/ ——遊戲物理視角的 Euler／semi-implicit Euler／RK4 比較，把「tick loop 就是 Euler 法」與能量漂移寫成工程實戰指南（見 ch10）。
- **APMonitor〈Proportional Integral Derivative (PID)〉**：https://apmonitor.com/pdc/index.php/Main/ProportionalIntegralDerivative ——P、I、D 三項各自脾氣的教學頁，想親手調 Kp、Ki、Kd 從這裡開始（見 ch15）。
- **fdlibm 的 k_sin.c 原始碼**：https://www.netlib.org/fdlibm/k_sin.c ——三十行程式加註解，親眼看 sin 的多項式實作與誤差界，「泰勒級數真的跑在你機器裡」的鐵證（見 ch09）。

## 往欣賞走（數學史與科普方向）

想把這趟旅程的故事線讀厚——人物、原典與翻案，走這條。

- **Steven Strogatz《無限的力量》**（旗標，2020）——已列「如果只看三樣」第一位；阿基米德、導數誕生、FTC、微分方程到傅立葉，每段都有對應章節的敘事版（見 ch01–ch16）。
- **David Bressoud《Calculus Reordered: A History of the Big Ideas》**（Princeton UP，2019）：https://press.princeton.edu/books/hardcover/9780691181318/calculus-reordered ——以累積、變化比、級數、容差四大主軸重排微積分史；讀完你會明白，本書的章節順序也只是諸多可能中的一種（見 ch11、ch16）。
- **Archimedes Palimpsest 官方網站**：https://www.archimedespalimpsest.org/ ——《方法》重寫本從祈禱書到多光譜成像的全程紀錄，先讀 History 頁，看人類怎麼差點弄丟它（見 ch02）。
- **SEP 與 IEP 的〈Zeno's Paradoxes〉**：https://plato.stanford.edu/entries/paradox-zeno/ 、https://iep.utm.edu/zenos-paradoxes/ ——悖論標準轉述與現代解的完整地圖；IEP 較口語，其「The Standard Solution」一節就是本書 ch03–ch04 走的路（見 ch01）。
- **亞里斯多德《物理學》卷六英譯**（MIT Classics）：https://classics.mit.edu/Aristotle/physics.6.vi.html ——三支箭的原始轉述都在 Part 9，一頁讀完，親眼看一次原文（見 ch01）。
- **MacTutor 數學史檔案**——本書人物與概念身世的史料依據，每篇都短：Eudoxus 傳記（https://mathshistory.st-andrews.ac.uk/Biographies/Eudoxus/ ）、《方法》選段譯文（https://mathshistory.st-andrews.ac.uk/Extras/Archimedes_The_Method/ ）、Madhava 傳記（https://mathshistory.st-andrews.ac.uk/Biographies/Madhava/ ）、〈The number e〉（https://mathshistory.st-andrews.ac.uk/HistTopics/e/ ）（見 ch02、ch05、ch09）。
- **Euler 原典兩處**：Euleriana 的 Basel 史料與證明綜覽（https://scholarlycommons.pacific.edu/cgi/viewcontent.cgi?article=1032&context=euleriana ）、Euler Archive 的 E247《De seriebus divergentibus》（https://scholarlycommons.pacific.edu/euler-works/247/ ）——看十八世紀最強的腦袋怎麼大膽形式操作、又怎麼自建護欄（見 ch09、ch12）。
- **Stephen Wolfram〈Who Was Ramanujan?〉**：https://writings.stephenwolfram.com/2016/04/who-was-ramanujan/ ——兩封信的前後脈絡與手稿影像；「瘋人院」那句話的原始出處（第二封信，1913-02-27）（見 ch12）。
- **Quanta Magazine〈The Jagged, Monstrous Function That Broke Calculus〉**（2025-01）：https://www.quantamagazine.org/the-jagged-monstrous-function-that-broke-calculus-20250123/ ——怪獸史的科普敘事版，讀完 ch13 躺著複習用（見 ch13）。

## 各章延伸閱讀索引

各章清單的一行濃縮版；完整評注回各章末尾看。

| 章 | 該章延伸閱讀的去處 |
|---|---|
| ch01 | SEP／IEP 芝諾條目；亞里斯多德《物理學》卷六（MIT Classics）；《無限的力量》；3B1B 系列 |
| ch02 | Palimpsest 官網；Wikipedia〈Quadrature of the Parabola〉〈Measurement of a Circle〉；Holy Cross 阿基米德講義（https://mathcs.holycross.edu/~little/Archimedes.pdf ）；MacTutor Eudoxus 與《方法》選段；《無限的力量》 |
| ch03 | 3B1B 系列；Wikipedia〈0.999…〉（https://en.wikipedia.org/wiki/0.999... ）；《無限的力量》；Grabiner ε 史源 |
| ch04 | 3B1B〈The paradox of the derivative〉（https://www.3blue1brown.com/lessons/derivatives ）；MAA《The Analyst》珍藏頁（https://old.maa.org/press/periodicals/convergence/mathematical-treasure-george-berkeleys-the-analyst ）；《Commercium Epistolicum》條目（https://www.historyofinformation.com/detail.php?id=1726 ）；《無限的力量》；MIT OCW 18.01 |
| ch05 | 3B1B 系列；MacTutor〈The number e〉；《無限的力量》；Wikipedia〈e (mathematical constant)〉（https://en.wikipedia.org/wiki/E_(mathematical_constant) ） |
| ch06 | 3B1B〈Gradient descent〉與系列；MIT OCW 18.01；Paul's Notes 的 Lagrange 乘數頁；《無限的力量》；Wikipedia〈Gradient descent〉（https://en.wikipedia.org/wiki/Gradient_descent ） |
| ch07 | 3B1B〈Integration〉（https://www.3blue1brown.com/lessons/integration ）；Wikipedia〈Riemann integral〉〈Integral symbol〉；MacTutor「integral」詞源（https://mathshistory.st-andrews.ac.uk/Miller/mathword/i/ ）；MIT OCW 18.01；《無限的力量》 |
| ch08 | 3B1B〈Integration〉；Nauenberg 論 Barrow 與 Leibniz（https://arxiv.org/abs/1111.6145 ）；MAA 牛頓 FTC 原證（https://old.maa.org/press/periodicals/convergence/teaching-the-fundamental-theorem-of-calculus-a-historical-reflection-newtons-proof-of-the-ftc ）；Britannica〈Discovery of the theorem〉；Prometheus query functions 文件（https://prometheus.io/docs/prometheus/latest/querying/functions/ ）；《無限的力量》；《The Calculus Gallery》 |
| ch09 | 3B1B〈Taylor series〉（https://www.3blue1brown.com/lessons/taylor-series ）；Euleriana Basel 綜覽；fdlibm k_sin.c；《The Calculus Gallery》；MacTutor Madhava |
| ch10 | 3B1B〈Differential equations〉（https://www.3blue1brown.com/lessons/differential-equations ）；MIT OCW 18.03；Wikipedia〈Discovery of Neptune〉（https://en.wikipedia.org/wiki/Discovery_of_Neptune ）；Gaffer On Games；《無限的力量》 |
| ch11 | 3B1B〈Fourier series〉（https://www.3blue1brown.com/lessons/fourier-series ）；Wikipedia〈Gibbs phenomenon〉（https://en.wikipedia.org/wiki/Gibbs_phenomenon ）；《The Calculus Gallery》；《Calculus Reordered》；《無限的力量》 |
| ch12 | Wikipedia〈History of Grandi's series〉〈Riemann series theorem〉〈1 + 2 + 3 + 4 + ⋯〉〈Kahan summation algorithm〉；Euler Archive E247；Wolfram〈Who Was Ramanujan?〉 |
| ch13 | Wikipedia〈Weierstrass function〉（https://en.wikipedia.org/wiki/Weierstrass_function ）；Hardy 1916（AMS PDF）；Quanta 怪獸專文；Thim 怪獸圖鑑；Mörters & Peres《Brownian Motion》；Shen 論 Hausdorff 維度（https://arxiv.org/abs/1505.03986 ） |
| ch14 | Spivak《Calculus》；《The Calculus Gallery》；Dedekind 原典（Gutenberg 21016）；Keisler 無窮小教本；Grabiner ε 史源 |
| ch15 | 3B1B〈Backpropagation calculus〉；Parr & Howard 矩陣微積分；Rumelhart–Hinton–Williams 1986；Kubernetes HPA 文件（https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/ ）；APMonitor PID；Prometheus histograms 文件（https://prometheus.io/docs/practices/histograms/ ）；Wikipedia〈Numerical differentiation〉（https://en.wikipedia.org/wiki/Numerical_differentiation ） |
| ch16 | 本附錄三條路線；《無限的力量》；《Calculus Reordered》；3B1B 系列重看 |
