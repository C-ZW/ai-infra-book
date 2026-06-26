# 混沌理論／蝴蝶效應書 — 事實基準表（landscape, 2026-06）

> 本檔是全書的**事實錨點**。每一章的歷史、人名、年份、數值都必須與此一致；要改任何基準值，先改這裡、再同步全書、並在 maintenance.md 掃描日誌記一行。
> 規則：每條都帶「驗證值／一句註記／來源 URL」。無法以可信來源確認者標 ⚠️ 並說明原因。來源彼此衝突者兩邊都記並標旗。時效性敘述加註 (2026-06)。
> 信心分級：本書的事實多屬「數學恆真」（不會過時）與「史實」（已定案），時效風險主要落在「天氣可預測度上限」這類仍在演進的研究結論。

---

## 一、歷史與人物（年份、歸屬、原話）

### 1. 拉普拉斯惡魔（Laplace's demon）
- **驗證值**：出自拉普拉斯 1814 年《機率的哲學試論》（*Essai philosophique sur les probabilités*）導論。經典英譯：「一個智者，若能知道在某一刻驅動自然的所有力與組成自然的萬物的所有位置，且其智力足以分析這些資料……對它而言沒有什麼是不確定的，未來會如同過去一樣呈現在它眼前。」
- **一句註記**：這是「嚴格物理決定論」的經典定義；拉普拉斯本人**沒有**用「惡魔（demon）」這個詞，是後世評論者加上的稱呼。是全書「決定論 vs 可預測性」對照的歷史起點（與 ch 哲學章呼應）。
- **來源**：
  - https://en.wikipedia.org/wiki/A_Philosophical_Essay_on_Probabilities （出版年 1814、英譯、demon 為後人命名）
  - https://www.informationphilosopher.com/freedom/laplaces_demon.2.en.html （完整段落與「Laplace 未用 demon」之說明）

### 2. 龐加萊與三體問題、奧斯卡二世獎
- **驗證值**：
  - 瑞典與挪威國王奧斯卡二世（Oscar II）設立的國際數學競賽，為慶其 60 歲生日（1889-01-21）。
  - 龐加萊（Henri Poincaré）的得獎論文預定刊於《Acta Mathematica》。
  - 校稿者 **Lars Edvard Phragmén** 在 1889 年 7 月提出編輯疑問，龐加萊回應時於 1889 年 12 月發現**重大錯誤**（他原以為證明了太陽系穩定性，此證明失效）。
  - 論文已印好並由 Mittag-Leffler 開始寄發；Mittag-Leffler 設法**召回幾乎所有副本**。
  - 龐加萊改寫出**修正版**（約為原稿兩倍長），刊於 1890 年的《Acta Mathematica》卷 13；改正過程中他發現了今日所稱的**同宿點／同宿纏結（homoclinic points / tangle）**，即首次對動力系統混沌行為的數學描述。
  - 龐加萊須自付額外印製費，**超過他贏得的獎金**。
- **一句註記**：「獎被頒了、論文卻得召回重印」是混沌史最戲劇的轉折——錯誤本身導出了混沌的發現。注意常見年份組：競賽公告 1885 年、頒獎 1889 年（國王生日）、修正版刊出 1890 年。
- **來源**：
  - https://link.springer.com/article/10.1007/BF00374436 （Barrow-Green, "Oscar II's prize competition and the error in Poincaré's memoir on the three body problem", *Arch. Hist. Exact Sci.* 1994）
  - https://www.mittag-leffler.se/about-us/history/prize-competition/ （Mittag-Leffler 研究所官方：競賽史、召回經過）
- ⚠️ **競賽公告年「1885」**：本次檢索未取得明確標注 1885 的一級來源頁面（Barrow-Green 專書應有，但檢索摘要只確認頒獎 1889、刊出 1890）。1885 為文獻常見值，但建議書中以「1880 年代中設立、1889 頒獎、1890 修正版刊出」的安全敘述帶過，或落地前再以 Barrow-Green 專書核一次。

### 3. 三體問題：無一般封閉解 / Bruns、Sundman、現代編舞解
- **驗證值**：
  - **無一般封閉式（代數）解**：Bruns（Ernst Heinrich Bruns）1887 年證明三體問題除 10 個古典積分（質心位置 3、質心速度 3、角動量 3、能量 1）外，**沒有其他可表為座標與其導數之代數函數的首次積分**。龐加萊（1890）進一步把不存在性推到解析積分層面。
  - **Sundman 級數**：Karl Fritiof Sundman 1912 年給出對所有時間收斂的冪級數解（以 t^(1/3) 的冪展開）。**但實用上無用**——收斂極慢，常引述「需約 10^(8,000,000) 項才能達到天文觀測精度」。
  - **現代編舞解（choreographies）**：八字形（figure-eight）解由 Cris Moore（Santa Fe Institute）於 **1993 年以數值方法**首次找到；**嚴格存在性證明**由 Alain Chenciner 與 Richard Montgomery 於 **2000 年**發表（"A remarkable periodic solution of the three-body problem in the case of equal masses", *Annals of Mathematics*），用作用量泛函極小化證明，三等質量物體以 1/3 週期的時間平移走同一條平面曲線。
- **一句註記**：「三體無解」的精確版是「**沒有一般封閉式代數解**」；它有特殊解、也可數值積分（這是書中要守住的直覺陷阱，見三）。
- **來源**：
  - https://link.springer.com/content/pdf/10.1023/A:1008346516349.pdf （Bruns 定理證明與推廣，*Celestial Mechanics and Dynamical Astronomy*）
  - https://en.wikipedia.org/wiki/Karl_F._Sundman （Sundman 1912、t^(1/3) 冪級數、收斂緩慢）
  - https://arxiv.org/pdf/1508.02312 （三體問題綜述：10^(8,000,000) 項之估計、八字形解史）
  - https://news.ucsc.edu/2019/08/three-body-problem/ （Moore 1993 數值、Chenciner–Montgomery 2000 證明）
- ⚠️ **「10^(8,000,000) 項」**：這個量級廣為流傳，但精確指數視所要求精度而異；書中宜寫「需要天文數字般多的項（常引述約 10 的數百萬次方量級）」而非當成精確常數。

### 4. 阿達瑪（Jacques Hadamard）1898
- **驗證值**：Hadamard 1898 年研究**負曲率曲面上的測地線流（geodesic flow）**，證明所有測地線彼此不穩定、以指數方式發散；被視為**最早被嚴格證明為混沌的動力系統之一**，並引入了符號動力學（symbolic dynamics）來描述對初始條件的敏感依賴。
- **一句註記**：「對初始條件敏感依賴」在 Lorenz 之前 60 餘年就有嚴格數學先例，可作為書中「混沌不是 1960 年代才冒出來」的伏筆。
- **來源**：
  - https://en.wikipedia.org/wiki/Hadamard%27s_dynamical_system （1898、負曲率測地線、指數發散、可能是最早被證明的混沌系統）

### 5. 愛德華・勞侖次（Edward Lorenz）
- **驗證值**：
  - **1961 重新發現（MIT）**：Lorenz 用 12 變數的天氣數值模型；為了續算，他重新輸入先前印表機印出的中間值。電腦記憶體存的是六位小數 **0.506127**，但印表機為省版面只印三位 **0.506**（差約**千分之一，約 0.1%**）。誤差隨時間放大，使後續結果完全不同——他由此意識到長期天氣預報不可行。
  - **1963 論文**：「Deterministic Nonperiodic Flow」，刊於 *Journal of the Atmospheric Sciences*（《大氣科學期刊》）卷 20，頁 130–141。被視為混沌理論奠基論文。
  - **勞侖次系統方程式與參數**：σ=10、ρ(=r)=28、β=8/3（dx/dt=σ(y−x); dy/dt=x(ρ−z)−y; dz/dt=xy−βz）。這是經典「蝴蝶形」吸引子的標準參數。
  - **「蝴蝶」命名**：1972-12-29 在美國科學促進會（AAAS）第 139 屆會議的演講題目「Predictability: Does the Flap of a Butterfly's Wings in Brazil Set Off a Tornado in Texas?」；**題目實際由氣象學家 Philip Merilees 在 Lorenz 缺席時代擬**。
  - **更早用「海鷗」**：Lorenz 在 1963 年另一篇文章（NYAS 會議論文，見下註）寫道：「一位氣象學家說，若理論正確，一隻**海鷗（sea gull）**拍一次翅膀就足以永遠改變天氣的走向。」
- **一句註記**：「0.506127 → 0.506、六位捨成三位、約千分之一」是書中招牌故事，三個細節都要對。蝴蝶之名來自 Merilees，不是 Lorenz 自取；蝴蝶之前用的是海鷗。
- **來源**：
  - https://www.aps.org/publications/apsnews/200301/history.cfm （APS：1961 故事、六位存 / 三位印、千分之一）
  - https://plus.maths.org/content/butterfly-flap-felt-across-world （0.506 vs 0.506127、<0.1%）
  - https://www.scirp.org/reference/referencespapers?referenceid=1646432 （1963 JAS 卷 20 頁 130–141 引文）
  - https://www.britannica.com/science/butterfly-effect （1972 AAAS 題目、Merilees 命名、早期海鷗）
  - https://barrypopik.com/blog/does_the_flap_of_a_butterflys_wings_in_brazil_set_off_a_tornado_in_texas （Merilees 在 Lorenz 缺席時擬題之考據）
- ⚠️ **「海鷗」出自哪一篇 1963 論文**：海鷗那句話來自 Lorenz **1963 年在紐約科學院（NYAS）的會議論文**「The Predictability of Hydrodynamic Flow」（*Transactions of the New York Academy of Sciences* 卷 25(4), 頁 409–432，1963-01-22 宣讀），**不是**同年的「Deterministic Nonperiodic Flow」（JAS）。坊間多處把兩篇混為一談。書中若引海鷗，請註明是 NYAS Transactions 那篇、且是「一位氣象學家的話」（Lorenz 轉述，未具名）。來源：https://nyaspubs.onlinelibrary.wiley.com/doi/abs/10.1111/j.2164-0947.1963.tb01464.x

### 6. 李天岩（Li）& Yorke 1975：「Period Three Implies Chaos」
- **驗證值**：Tien-Yien Li 與 James A. Yorke，「Period Three Implies Chaos」，*The American Mathematical Monthly* 卷 82, 第 10 期（1975 年 12 月），頁 985–992。此文首次在數學文獻中使用「chaos（混沌）」一詞。
- **一句註記**：數學意義上「混沌」一詞的命名出處；「週期 3 蘊含混沌」是書中銜接 Sharkovskii 定理的橋。
- **來源**：
  - https://www.tandfonline.com/doi/abs/10.1080/00029890.1975.11994008 （期刊頁，卷 82 第 10 期）
  - https://www.nku.edu/~longa/classes/mat360/days/resources/docs/Chaos/Li-PeriodThreeImplies-1975.pdf （原文 PDF）

### 7. Sharkovskii 定理（Sharkovskii 1964, 烏克蘭）
- **驗證值**：Oleksandr Mykolayovych Sharkovsky，1964 年論文「Coexistence of cycles of a continuous transformation of a line into itself」，刊於《烏克蘭數學期刊》。定理給出自然數的一個排序，使得若區間上連續映射有週期 n 的點、且 n 在此序中排在 m 之前，則該映射也有週期 m 的點。**排序**：先是奇數（從 3 起遞增）3,5,7,…，接著各奇數乘 2（2·3, 2·5,…），再乘 4（4·3,…）…，最後是 2 的冪（…,8,4,2,1）。週期 3 排在最前，故「週期 3 ⇒ 所有週期」。
- **一句註記**：比 Li–Yorke（1975）早 11 年，且結論更強（涵蓋所有週期共存）；姓氏拼法 Sharkovskii / Sharkovsky 並存。
- **來源**：
  - https://en.wikipedia.org/wiki/Sharkovskii%27s_theorem （1964、烏克蘭數學期刊、排序定義）
  - http://www.scholarpedia.org/article/Sharkovsky_ordering （Scholarpedia：排序與週期共存）

### 8. Robert May 1976 *Nature* 綜述
- **驗證值**：Robert M. May，「Simple mathematical models with very complicated dynamics」，*Nature* 261, 459–467（1976）。把邏輯斯蒂映射（logistic map）與倍週期通往混沌的途徑推廣到生態、經濟、社會領域並普及化。
- **一句註記**：邏輯斯蒂映射「廣為人知」主要靠這篇綜述；May 是生態學家／物理出身的應用數學家。
- **來源**：
  - https://www.nature.com/articles/261459a0 （*Nature* 261:459，1976）

### 9. Mitchell Feigenbaum：常數與普適性（universality）
- **驗證值**：
  - Feigenbaum 1975 年（用 HP-65 計算器）發現相鄰倍週期分岔參數間距之比趨近約 4.6692 的常數。
  - 任職地點：**Los Alamos National Laboratory**（洛斯阿拉莫斯國家實驗室，新墨西哥州）；之前曾在 Cornell、Virginia Tech。
  - **普適性**：他發現對一大類單峰映射（如 logistic、x→sin x），同一個 δ 都出現——倍週期通往混沌具普適性。
  - 正式論文「Quantitative Universality for a Class of Nonlinear Transformations」於 **1978 年初**發表（*J. Stat. Phys.* 19:25）；他也常引 1976-08-26 的演講摘要（收於 Los Alamos 理論部 1975–1976 年報）以主張優先權。
- **一句註記**：年份組合「1975 發現、1978 正式發表、Los Alamos」三者都要對；普適性是書中「不同方程式、同一常數」高潮。
- **來源**：
  - https://handwiki.org/wiki/Biography:Mitchell_Feigenbaum （Los Alamos、Cornell/Virginia Tech、HP-65、1975、x→sin x、1978 論文）
  - https://writings.stephenwolfram.com/2019/07/mitchell-feigenbaum-1944-2019-4-66920160910299067185320382/ （Wolfram 訃聞長文：常數值與生平）

### 10. Benoît Mandelbrot：fractal、海岸線論文
- **驗證值**：
  - 「fractal（碎形／分形）」一詞由 Mandelbrot 於 **1975 年**鑄造（源於拉丁語 *fractus*，破碎），首見其 1975 年法文書《Les Objets Fractals》。
  - 《The Fractal Geometry of Nature》於 **1982 年**出版（為 1977 年英文版、再前為 1975 法文版的增訂譯本）。
  - 海岸線論文「How Long Is the Coast of Britain? Statistical Self-Similarity and Fractional Dimension」，*Science* **卷 156, 第 3775 期（1967-05-05），頁 636–638**。
- **一句註記**：海岸線論文的卷號是 **156**（不是部分網頁誤植的「165」）；它把 Richardson 的經驗觀察提升為「碎形維度」。
- **來源**：
  - https://www.science.org/doi/10.1126/science.156.3775.636 （*Science* 156(3775):636–638, 1967）
  - https://en.wikipedia.org/wiki/The_Fractal_Geometry_of_Nature （1982 書、1975 鑄詞、版本沿革）

### 11. Stephen Smale：馬蹄映射（horseshoe map）
- **驗證值**：Smale 約於 **1960 年**在巴西里約熱內盧（訪 IMPA 期間），在科帕卡巴納（Copacabana）海灘上構思出馬蹄映射。他原先猜想「沒有混沌這種東西」，是 Norman Levinson 指出 Cartwright–Littlewood 的舊結果與其猜想矛盾，促成此發現。馬蹄映射（壓扁→拉長→折成馬蹄）成為混沌的標誌性幾何模型。後來他寫成 1998 年文章「Finding a Horseshoe on the Beaches of Rio」（*The Mathematical Intelligencer*）。
- **一句註記**：「海灘上的馬蹄」是真有其事的軼事（Smale 自述），可放心使用；年份用「約 1960」。
- **來源**：
  - https://plus.maths.org/content/smales-horseshoe （Copacabana、1960、Levinson/Cartwright–Littlewood）
  - http://www.scholarpedia.org/article/Smale_horseshoe （馬蹄映射定義與意義）

### 12. James Gleick《Chaos: Making a New Science》1987
- **驗證值**：James Gleick，《Chaos: Making a New Science》，Viking，**1987-10-29** 出版。暢銷科普書，把混沌理論與「蝴蝶效應」帶入大眾；曾入圍普立茲獎與美國國家圖書獎決選。
- **一句註記**：書名常被略寫為《Chaos》；副標是「Making a New Science」（並非 "The Making of"，後者是某些再版/標題變體）。
- **來源**：
  - https://en.wikipedia.org/wiki/Chaos:_Making_a_New_Science （1987、Viking、入圍）

### 13. Ruelle & Takens 1971：「strange attractor（奇異吸引子）」
- **驗證值**：David Ruelle 與 Floris Takens，「On the Nature of Turbulence」，*Communications in Mathematical Physics* 卷 20（1971），頁 167–192（另有卷 23 的勘誤 343–344）。此文鑄造「strange attractor」一詞，並提出其與湍流的關聯（Ruelle–Takens–Newhouse 通往混沌途徑）。
- **一句註記**：「奇異吸引子」命名出處；與 Lorenz 吸引子、碎形維度互相呼應。
- **來源**：
  - https://www.math.ucdavis.edu/~saito/data/synchrosqueezing/takens_detect-strange-attractors-turbulence.pdf （Takens 文，引述 Ruelle–Takens 1971 鑄詞）
  - https://link.springer.com/chapter/10.1007/BFb0091924 （"strange attractor" 由 Ruelle & Takens 1971 引入）

---

## 二、關鍵數值（必須精確；此為跨章基準）

### 邏輯斯蒂映射 logistic map：x_{n+1} = r·x_n·(1 − x_n)
- **非零不動點** x* = 1 − 1/r；在 1 < r < 3 時穩定。
  - 推導：不動點導數 f'(x*) = 2 − r，|2 − r| < 1 ⇔ 1 < r < 3。
  - 來源：https://subversion.american.edu/aisaac/notes/logistic.pdf ；https://math.libretexts.org/Bookshelves/Applied_Mathematics/Mathematical_Biology_(Chasnov)/01%3A_Population_Dynamics/1.02%3A_The_Logistic_Equation
- **倍週期分岔點**（onset 值）：
  - r₁ = 3（週期 1 → 2）
  - r₂ = 1 + √6 ≈ **3.4495**（週期 2 → 4）
  - r₃ ≈ **3.5441**（週期 4 → 8；常引 3.54409）
  - r₄ ≈ **3.5644**（週期 8 → 16；常引 3.564407）
  - r∞ ≈ **3.569945672…**（倍週期累積點 / 混沌起點，即 Feigenbaum 點）
  - 來源：https://en.wikipedia.org/wiki/Period-doubling_bifurcation （1+√6、3.54409、3.56440、3.56995）；https://www.sciencedirect.com/topics/mathematics/logistic-map （r=3, 3.449489, 3.54409, 3.564407）
  - ⚠️ **MathWorld 標號陷阱**：Wolfram MathWorld 的 LogisticMap 條目把「r₃ = 1+2√2 ≈ 3.8284」標為「period-3 onset」、把「1+√6 ≈ 3.4495」標為「period-4」，其 r 下標與本表（及多數教材）的「倍週期序」不同。1 + 2√2 = 1 + √8 ≈ 3.8284 指的是**混沌區內的週期 3 視窗**，不是倍週期級聯的第三步。書中務必區分「倍週期到週期 8 在 ~3.5441」與「週期 3 視窗在 ~3.8284」。
- **Feigenbaum 常數**：
  - δ ≈ **4.66920160910299**（…067185320382…；倍週期間距比）
  - α ≈ **2.502907875**（…095…；x 軸尺度縮放比）
  - 來源：https://en.wikipedia.org/wiki/Feigenbaum_constants ；https://writings.stephenwolfram.com/2019/07/mitchell-feigenbaum-1944-2019-4-66920160910299067185320382/
- **週期 3 視窗起點**：r = 1 + √8 (= 1 + 2√2) ≈ **3.8284**（精確 3.82843）。
  - 來源：https://mathworld.wolfram.com/LogisticMap.html
- **r = 4 時**：
  - 與帳篷映射（tent map，μ=2/μ=1 滿幅）拓撲共軛；共軛函數 φ(x) = (2/π)·arcsin(√x)。
  - 不變密度（invariant density）ρ(x) = 1 / (π·√(x(1−x)))，x ∈ [0,1]。
  - 李雅普諾夫指數（Lyapunov exponent）λ = ln 2 ≈ **0.6931**（以 e 為底）。
  - 來源：https://mathworld.wolfram.com/LogisticMapR=4.html

### 勞侖次系統 Lorenz system（σ=10, ρ=28, β=8/3）
- **三個李雅普諾夫指數** ≈ (**+0.906**, 0, **−14.572**)（以 e 為底，每單位時間；Sprott 用步長 0.001、積分逾 10⁶ 時間單位算得）。最大者常引 **≈ 0.9056**。
- **Kaplan–Yorke（Lyapunov）維度** D_KY = 2 + λ₁/|λ₃| ≈ **2.062**（Sprott 稱可信至 4 位有效數字）。
- **關聯維度（correlation dimension）** D₂ ≈ **2.05**（2.055 ± 0.004）；容量維度 D₀ ≈ 2.00。常以「≈2.06」概括吸引子維度。
- 來源：https://sprott.physics.wisc.edu/chaos/lorenzle.htm
- **李雅普諾夫時間** = 1/λ（混沌系統誤差 e 倍放大的特徵時間）。以最大 λ≈0.9056、每單位時間計，Lyapunov time ≈ 1.1 時間單位。
- **混沌判據**：最大李雅普諾夫指數 λ > 0 ⇔ 混沌（對初始條件指數敏感）。

### 大氣可預測度（atmospheric predictability）（2026-06，仍在演進，需 hedge）
- **經典「約兩週」上限**：1960 年代基於「誤差倍增時間約 5 天」的模型估計得出約兩週上限（Charney、Leith、Mintz、Smagorinsky 等）。
- **Lorenz 後期估計**：1980 年代用更真實的全球模型，Lorenz 得到較短的倍增時間，**約 3.5 天**。
- **現代估計**：實務上限常引 **約 10–14 天**；Zhang et al. (2019) 估計若把現行初始條件誤差降一個數量級，中緯度技巧可延至**約 15 天**；理想「孿生」實驗中誤差在中緯度約 17 天、熱帶逾 20 天才飽和。
- **一句註記**：書中講「兩週上限」要標明這是**實務經驗值 / 量級**，非定理；倍增時間 3.5–5 天視初始狀態與模型而異。給範圍、附來源、別寫死。
- 來源：
  - https://news.ucar.edu/4505/turning-tables-chaos-atmosphere-more-predictable-we-assume （5 天倍增、兩週、Zhang 2019 的 15 天、孿生實驗 17/20 天）
  - https://www.researchgate.net/publication/370872305_Lorenz's_View_on_the_Predictability_Limit_of_the_Atmosphere （Shen 等：兩週上限與 5 天倍增之關聯、Lorenz 後期 3.5 天）
- ⚠️ 機器學習近年（2024–2025）有「超 30 天可預測度」的論文，但屬前沿、結論未定；書中至多以一句「近年機器學習方法正在重新評估此上限」帶過，不當基準。來源：https://arxiv.org/html/2504.20238

### 碎形維度（fractal dimensions；自相似維度 = log N / log r）
- Koch 曲線：ln 4 / ln 3 ≈ **1.2619**
- Cantor 集（中三分之一）：ln 2 / ln 3 ≈ **0.6309**
- Sierpiński 三角：ln 3 / ln 2 ≈ **1.585**
- Mandelbrot 集**邊界**的 Hausdorff 維度 = **2**（Shishikura 1991 宣布；正式刊於 *Annals of Mathematics* 卷 147（1998），頁 225–267）
- 英國海岸線（coastline of Britain）碎形維度 ≈ **1.25**（部分來源給到 1.31）
- 來源：
  - https://www.vanderbilt.edu/AnS/psychology/cogsci/chaos/workshop/Fractals.html （Koch / Cantor / Sierpiński 標準維度）
  - https://arxiv.org/abs/math/9201282 （Shishikura：Mandelbrot 集邊界 Hausdorff 維度 = 2）
  - https://en.wikipedia.org/wiki/Coastline_paradox （英國海岸線 ≈1.25）
- ⚠️ **海岸線 1.25 是經驗估計**，隨量測尺度與資料而異（1.25–1.31）；非精確常數。書中以「約 1.25」表述。
- ⚠️ **Shishikura 年份**：成果常標「1991」（預印本/宣布），正式期刊出版為 1998（*Annals* 147）。書中宜寫「Shishikura 1991 年證明（1998 年正式發表）」以免被挑。

---

## 三、常被誤傳／需守住的正確版（直覺的陷阱）

> 以下每一條都是「大眾版 vs 正確版」，是書中「直覺的陷阱」段落的素材。守住正確版。

### T1. 「蝴蝶效應」≠「微小原因必然造成某個巨大的特定結果」
- **正確版**：蝴蝶效應指**對初始條件的敏感依賴**，使**長期預測不可能**；它**不**保證某次拍翅一定造成某個特定龍捲風。Roger Pielke Sr. 直言「蝴蝶拍翅在數千公里外引發龍捲風——在任何情況下都不可能，答案是斷然的『不』」。它是**隱喻**，講的是可預測度的極限，不是直接因果鏈。
- **更深一層（Tim Palmer「真正的蝴蝶效應」）**：Lorenz 1969 年（*Tellus* 多尺度流論文）描述的是**絕對的有限時間可預測度屏障**——在某些多尺度流體系統中，**即使把初始誤差縮到任意小，預測期限仍趨於一個有限值**，比 1963 年低階混沌（初值夠準就能預測任意久）更激進。書中可分兩層講：低階混沌的 SDIC vs 真正的有限時間屏障。
- 來源：https://www.nationalgeographic.com/science/article/real-butterfly-effect-chaos-theory ；https://ui.adsabs.harvard.edu/abs/2014Nonli..27R.123P/abstract （Palmer, "The real butterfly effect", *Nonlinearity* 2014）

### T2. 蝴蝶「形狀」與蝴蝶「拍翅」是兩件事（雙關巧合）
- **正確版**：勞侖次吸引子在相空間呈雙螺旋、形似蝴蝶雙翼——這是**幾何形狀**的巧合；而「蝴蝶拍翅」隱喻是 1972 年 Merilees 擬的**題目**。兩者剛好都叫「蝴蝶」是雙關，**不是同一回事**，不要混講成「因為吸引子像蝴蝶所以叫蝴蝶效應」。
- 來源：https://www.britannica.com/biography/Edward-Lorenz （吸引子形似蝴蝶；1972 題目來自 Merilees）

### T3. 混沌 ≠ 隨機（randomness）
- **正確版**：混沌系統是**完全決定論**的——同樣初值給出同樣軌跡，無任何隨機項；表面的「亂」來自對初值的敏感依賴與相空間的粗粒化觀察，是**認識論的**不可預測，非本體論的隨機。
- 來源：https://plato.stanford.edu/entries/chaos/ （「chaotic behavior is always deterministic」）

### T4. 決定論（determinism）≠ 可預測性（predictability）
- **正確版**：SEP 明言「混沌與決定論的混淆，多半來自把決定論等同於可預測性」。決定論是「唯一演化」的本體論性質；可預測性是「我們能否算出來」的認識論能力。混沌打破的是後者。
- 來源：https://plato.stanford.edu/entries/chaos/

### T5. 混沌**沒有**推翻決定論
- **正確版**：混沌擊敗的是**長期預測**，不是決定論本身。即便系統不可預測，它仍可完全遵守決定論定律。SEP：流行說法稱混沌使決定論失效是誤解。
- 來源：https://plato.stanford.edu/entries/chaos/ ；https://plato.stanford.edu/entries/determinism-causal/

### T6. 三體問題「無解」的精確意思
- **正確版**：指**沒有一般的封閉式（代數）解**（Bruns/Poincaré）。它**有**特殊解（如 Euler、Lagrange 解、八字形編舞解），也**可以數值積分**到任意有限時間，Sundman 甚至給了（實用上無用的）收斂級數。別寫成「三體完全無法求解」。
- 來源：見上「一、3」各條。

### T7. Lorenz 本人的審慎
- **正確版**：Lorenz 對「一隻蝴蝶是否真的引發某個特定龍捲風」是**保留**的——海鷗那句他歸給「一位氣象學家」（轉述、未具名），蝴蝶題目是 Merilees 擬的；他真正主張的是「初始狀態微小差異使長期預報失準」，而非「拍翅必致龍捲風」。書中引用時要保留這份審慎。
- 來源：https://www.britannica.com/science/butterfly-effect ；https://www.nationalgeographic.com/science/article/real-butterfly-effect-chaos-theory

---

## 四、與書架相鄰書的邊界（僅供跨書指引，不需網路查證）

讀者書架上的相鄰書與本書混沌主題的交界：
- **《馴服隨機》（probability）**：交界於「隨機 vs 決定論」「表面隨機的決定論系統」「不變密度 ρ(x) 是混沌軌跡的長期統計分布（遍歷性）」。本書講「混沌不是隨機」時，把機率語言指向《馴服隨機》。
- **《馴服無限》（calculus，含微分方程與傅立葉）**：交界於「勞侖次系統是一組 ODE」「相空間軌跡 = 微分方程解」「導數判斷不動點穩定性」「倍週期、極限過程」。連續時間動力系統的工具指向《馴服無限》。
- **《矩陣是動詞》（linear algebra，含特徵值）**：交界於「不動點/週期軌道穩定性 = 雅可比矩陣（Jacobian）特徵值的模是否 < 1」「線性化分析」「李雅普諾夫指數可視為長期平均的對數伸縮率」。穩定性的線性代數工具指向《矩陣是動詞》。
- **《等待的數學》（queueing）**：交界較弱；若觸及「長期穩態分布 vs 對初值敏感的暫態」可順帶一提，但不展開。

---

## 數值基準複核（跨章一致性速查表）

| 項目 | 基準值 | 備註 |
|---|---|---|
| logistic 非零不動點 | x* = 1 − 1/r | 1<r<3 穩定（f'=2−r） |
| r₁（1→2） | 3 | |
| r₂（2→4） | 1+√6 ≈ 3.4495 | |
| r₃（4→8） | ≈ 3.5441（3.54409） | |
| r₄（8→16） | ≈ 3.5644（3.564407） | |
| r∞（混沌起點） | ≈ 3.569945672… | Feigenbaum 點 |
| Feigenbaum δ | ≈ 4.66920160910299 | 間距比 |
| Feigenbaum α | ≈ 2.502907875 | 尺度比 |
| 週期 3 視窗起點 | 1+√8 = 1+2√2 ≈ 3.8284 | ≠ 倍週期第 3 步 |
| logistic r=4 不變密度 | 1/(π√(x(1−x))) | x∈[0,1] |
| logistic r=4 李指數 | λ = ln2 ≈ 0.6931 | 以 e 為底 |
| Lorenz 參數 | σ=10, ρ=28, β=8/3 | |
| Lorenz 最大李指數 | ≈ +0.9056（指數三元 ≈ +0.906,0,−14.572） | 以 e 為底，每單位時間 |
| Lorenz Kaplan–Yorke 維度 | ≈ 2.062 | =2+λ₁/|λ₃| |
| Lorenz 關聯維度 | ≈ 2.05（≈2.06 概括） | |
| Lyapunov 時間 | 1/λ | λ>0 ⇔ 混沌 |
| 天氣可預測度上限 | 約 10–14 天（兩週，量級/經驗值） | 倍增時間 3.5–5 天，2026-06 |
| Koch 曲線維度 | ln4/ln3 ≈ 1.2619 | |
| Cantor 集維度 | ln2/ln3 ≈ 0.6309 | |
| Sierpiński 三角維度 | ln3/ln2 ≈ 1.585 | |
| Mandelbrot 集邊界維度 | 2（Hausdorff） | Shishikura 1991/1998 |
| 英國海岸線維度 | ≈ 1.25（1.25–1.31） | 經驗估計 |
| Lorenz 捨入故事 | 0.506127 → 0.506（6→3 位，約千分之一） | |

### 關鍵年份速查
| 事件 | 年份 |
|---|---|
| 拉普拉斯《機率的哲學試論》 | 1814 |
| Hadamard 負曲率測地線 | 1898 |
| Bruns 無代數積分定理 | 1887 |
| 奧斯卡二世獎頒獎（國王 60 歲） | 1889 |
| 龐加萊修正版刊於 Acta Math. 卷 13 | 1890 |
| Sundman 收斂級數解 | 1912 |
| Smale 馬蹄映射（Copacabana） | 約 1960 |
| Lorenz 捨入重新發現（MIT） | 1961 |
| Lorenz "Deterministic Nonperiodic Flow"（JAS 20:130） | 1963 |
| Sharkovskii 定理（烏克蘭數學期刊） | 1964 |
| Ruelle & Takens 鑄「strange attractor」 | 1971 |
| Lorenz AAAS「蝴蝶」演講（Merilees 擬題） | 1972（12-29） |
| Feigenbaum 發現常數（Los Alamos） | 1975 |
| Mandelbrot 鑄「fractal」 | 1975 |
| Li & Yorke「Period Three Implies Chaos」（Amer. Math. Monthly 82) | 1975 |
| May *Nature* 261:459 綜述 | 1976 |
| Feigenbaum 正式論文（普適性） | 1978 |
| Mandelbrot《The Fractal Geometry of Nature》 | 1982 |
| Gleick《Chaos》 | 1987 |
| Moore 八字形解（數值） | 1993 |
| Chenciner & Montgomery 八字形存在性證明（Annals） | 2000 |

---

## 待考／低信心項（⚠️）

1. **奧斯卡二世獎「公告 1885 年」**：本次檢索未取得明確標 1885 的一級來源頁；頒獎 1889、刊出 1890 已確認。落地前以 Barrow-Green 專書核 1885，或書中寫「1880 年代中設立」。
2. **Sundman 級數「10^(8,000,000) 項」**：量級廣傳但隨所求精度而變，非精確常數；書中以「天文數字般多的項」表述。
3. **海鷗出處**：海鷗那句在 1963 NYAS Transactions「The Predictability of Hydrodynamic Flow」（卷 25(4):409–432），**不是**同年 JAS 的「Deterministic Nonperiodic Flow」；坊間多處混淆。且是 Lorenz 轉述「一位（未具名）氣象學家」的話。
4. **天氣可預測度上限（兩週 / 倍增 3.5–5 天 / 現代 10–17 天）**（2026-06）：實務經驗值與研究結論，仍在演進；機器學習近年挑戰此上限但結論未定。務必給範圍、標時間、別寫死。
5. **英國海岸線維度 ≈1.25（1.25–1.31）**：經驗估計，隨量測尺度而異，非精確常數。
6. **Shishikura 年份 1991 vs 1998**：宣布/預印本 1991、正式刊於 *Annals* 147（1998）；書中寫「1991 年證明、1998 年正式發表」。
7. **MathWorld logistic r 下標 vs 倍週期序**：MathWorld 把 1+2√2≈3.8284 標為「period-3」、1+√6≈3.4495 標為「period-4」，與本表倍週期序不同——這是同一批數字的不同標號，非矛盾，但易引讀者誤會，書中須明確區分「倍週期級聯到週期 8 在 ~3.5441」與「混沌區的週期 3 視窗在 ~3.8284」。
8. **拉普拉斯原文法文逐字**：本檔採通行英譯轉述；若書中要放「逐字」原文，建議引一級法文版再核，避免譯本差異。

---
*掃描日期：2026-06-19。本檔由事實基準研究流程產出，共 30+ 次定向檢索，優先採一級／權威來源（原始論文、Britannica、SEP、大學講義、MacTutor 類、同行評審）。*
