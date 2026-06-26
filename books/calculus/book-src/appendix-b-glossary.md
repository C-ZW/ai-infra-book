# 附錄 B — 術語表

> 全書出現過的技術名詞，EN–ZH 對照＋一句話定義。定義用的是**這本書的講法**（直覺優先），不是教科書的標準措辭——你要的是能複述的版本，不是能背誦的版本。依英文字母排序；「首次出現章」以實際內文為準。跨章概念的完整討論回該章看。

| English | 中文 | 一句話定義（本書講法） | 首次出現章 |
|---|---|---|---|
| absolute convergence | 絕對收斂 | 取絕對值後仍收斂；這種級數才能隨便重排不出事 | ch12 |
| accumulation function | 累積函數 | A(x)＝從 0 積到 x 的面積，把「面積」變成 x 的函數——FTC 的關鍵視角轉換 | ch08 |
| actual infinity | 實際無限 | 把無限當成一個已完成的整體（希臘人迴避的東西） | ch01 |
| alternating harmonic series | 交錯調和級數 | 1 − 1/2 + 1/3 − …＝ln 2；條件收斂的招牌例子 | ch12 |
| alternating series | 交錯級數 | 正負號交替出現的級數 | ch09 |
| analytic continuation | 解析延拓 | 把函數延伸到原本發散的地方、賦予新值（ζ(−1)=−1/12 的來路） | ch12 |
| Archimedean property | 阿基米德性質 | 沒有「無限小但非零」的實數；任何正數乘夠多次都能超過另一個 | ch03 |
| associativity | 結合律 | 加法可隨意加括號——在發散級數上**失效** | ch12 |
| Brownian motion | 布朗運動 | 塵埃、股價的隨機路徑；幾乎處處連續卻處處不可微（自然界的怪獸） | ch13 |
| catastrophic cancellation | 災難性消去 | 兩個相近浮點數相減，有效位數崩光——數值微分 h 太小就栽在這 | ch04 |
| chain rule | 連鎖規則 | 複合函數的導數＝各層變化率相乘；backprop 的數學核心 | ch05 |
| completeness | 完備性 | 實數沒有洞；「夾擠到的那個點」一定真的存在——極限與積分的地基 | ch14 |
| commutativity | 交換律 | 加法可調換順序——無限與浮點世界裡都要小心 | ch12 |
| conditional convergence | 條件收斂 | 收斂但取絕對值後發散；重排可改變和（黎曼重排定理） | ch12 |
| continuous | 連續 | 沒有跳躍、可以一筆畫完；用極限定義（不必可微） | ch03 |
| converge | 收斂 | 部分和（或數列）有極限、停得下來 | ch01 |
| cumulative distribution function (CDF) | 累積分布函數 | 機率密度的累積——本身就是一個積分；P99 是它的反查 | ch15 |
| Dedekind cut | 戴德金切割 | 用有理數的一刀切法定義無理數，把數線上的洞補滿 | ch14 |
| derivative | 導數 | 瞬間變化率＝差商的極限＝切線斜率 | ch04 |
| difference quotient | 差商 | (f(x+h)−f(x))/h，割線斜率；取 h→0 極限成導數 | ch04 |
| differential equation | 微分方程 | 用變化率描述系統的方程式——「定律寫的是變化率、不是軌跡」 | ch10 |
| diverge | 發散 | 沒有極限；和往無限跑或來回擺盪 | ch01 |
| epsilon-delta definition | ε-δ 定義 | 把「逼近」寫成可驗收條款的法典：對手出 ε、你給 δ | ch14 |
| Euler's method | 歐拉法 | 解不出方程就沿斜率一步步走（你的 tick loop 就是它） | ch10 |
| exponential backoff | 指數退避 | 重試間隔指數遞減；總時間是收斂的幾何級數（工程橋接） | ch01 |
| factorial | 階乘 | n!＝n×(n−1)×…×1；泰勒係數的分母 | ch09 |
| formal manipulation | 形式操作 | 先照規則算、嚴格性事後補票——十八世紀的招牌風格 | ch09 |
| Fourier series | 傅立葉級數 | 把任何週期訊號拆成 sin/cos 的無限疊加 | ch11 |
| Fast Fourier Transform (FFT) | 快速傅立葉變換 | 讓傅立葉拆解快到能跑在手機裡的演算法（JPEG、音訊） | ch11 |
| Fundamental Theorem of Calculus (FTC) | 微積分基本定理 | 面積與斜率互為反操作——微分與積分是同一件事的正反面（全書高潮） | ch08 |
| geometric series | 幾何級數 | 公比固定的級數；\|r\|<1 時收斂到 1/(1−r) | ch01 |
| Gibbs phenomenon | 吉布斯現象 | 傅立葉逼近在跳躍點旁約 9% 的過衝，項數再多也壓不掉 | ch11 |
| gradient descent | 梯度下降 | 沒有公式解時「往坡下走」找極小；步長＝你調過的學習率 | ch06 |
| harmonic series | 調和級數 | Σ1/n；項趨於 0 卻發散的第一面牆（Oresme 分組論證） | ch09 |
| hyperreal numbers | 超實數 | 把無窮小嚴格化的數系（羅賓遜非標準分析） | ch14 |
| improper integral | 廣義積分 | 積分界限或被積函數無界時，用極限定義——又一個「極限偽裝成運算」 | ch12 |
| indeterminate form | 未定式 | 像 0/0 這種本身無意義、要靠極限才有答案的式子 | ch04 |
| inner product | 內積 | 兩函數「相乘再積分」的相似度；不同頻率內積為零＝正交 | ch11 |
| integral | 積分 | 切薄、近似、加總、取極限；累積量，面積只是一張臉 | ch07 |
| limit | 極限 | 逼近的目的地，不是過程的最後一步（沒有最後一項） | ch01 |
| local linearity | 局部線性 | 光滑曲線放大到夠近就是直線——微分的世界觀（怪獸函數打破它） | ch05 |
| method of exhaustion | 窮盡法 | 內外夾擠＋反證法算精確值；阿基米德的絕技，但沒有通法 | ch02 |
| natural logarithm | 自然對數 | ln，以 e 為底；e^x 的反面 | ch05 |
| non-standard analysis | 非標準分析 | 羅賓遜 1960 年代讓無窮小嚴格復活，平反萊布尼茲的直覺 | ch14 |
| orthogonality | 正交 | 不同頻率「互不干擾」，所以傅立葉係數可以各自結帳 | ch11 |
| partial sum | 部分和 | 級數前 n 項之和；它的極限才是級數的「和」 | ch01 |
| potential infinity | 潛在無限 | 把無限當成「永遠可以再加一步」的過程（亞里斯多德的迴避法） | ch01 |
| power series | 冪級數 | 以 x 的次方為項的無限級數（泰勒級數是一種） | ch09 |
| probability density function (pdf) | 機率密度函數 | 曲線下面積＝機率；機率其實是在算積分 | ch15 |
| radius of convergence | 收斂半徑 | 冪級數能收斂的範圍；超出去就失效（離展開點愈遠愈吃緊） | ch09 |
| range reduction | 範圍縮減 | 先把角度折回小區間再用多項式算 sin（libm 的真實做法） | ch09 |
| rational numbers | 有理數 | 可寫成分數的數；稠密卻有洞（√2 不在其中） | ch14 |
| real number | 實數 | 補完所有洞、完備的數線；ℝ | ch14 |
| reductio ad absurdum | 反證法 | 假設相反、推出矛盾；窮盡法收尾的關鍵（因為當年沒有「取極限」） | ch02 |
| Riemann rearrangement theorem | 黎曼重排定理 | 條件收斂級數重排後可收斂到任意指定值——無限不守交換律 | ch12 |
| Riemann sum | 黎曼和 | 切 n 條矩形近似面積，n→∞ 取極限；積分的硬算定義 | ch07 |
| secant line | 割線 | 穿過曲線兩點的直線；兩點靠攏的極限是切線 | ch04 |
| separation of variables | 分離變數 | 把同類變數搬到等號同側再積分的解法（本書僅示範一次） | ch10 |
| sequence | 數列 | 一串有順序的數 a₁, a₂, …；可談它的極限 | ch03 |
| series | 級數 | 數列各項相加；和定義成部分和的極限 | ch03 |
| slope field | 方向場 | 在平面每點畫上該處斜率的小箭頭，畫出解的「流向」 | ch10 |
| square wave | 方波 | 在 +1 與 −1 間跳變的不連續波；傅立葉的試金石 | ch11 |
| standard normal distribution | 標準常態分布 | 鐘形曲線；曲線下面積＝機率，68-95-99.7 法則 | ch15 |
| tangent line | 切線 | 曲線在一點「貼著走」的直線；斜率＝導數 | ch04 |
| Taylor series | 泰勒級數 | 把函數展開成無限多項多項式，每多一項多抄一階導數 | ch09 |
| telescoping | 對消／伸縮 | 級數相鄰項相消、只剩頭尾（算部分和的招式） | ch09 |
| transfer principle | 轉移原理 | 非標準分析裡，實數的性質可平移到超實數的橋 | ch14 |
| trapezoidal rule | 梯形法 | 用梯形而非矩形近似積分，誤差以 1/n² 縮小（比矩形快一階） | ch07 |
| Weierstrass function | 魏爾斯特拉斯函數 | W(x)＝Σ aⁿcos(bⁿπx)；處處連續、處處不可微的怪獸 | ch13 |
| well-defined | 良定義 | 一個寫法真的指到一個確定對象（0.999… 的代數論證偷偷假設了它） | ch03 |
| Wiener process | 維納過程 | 布朗運動的嚴格數學模型；路徑以機率 1 處處不可微 | ch13 |
