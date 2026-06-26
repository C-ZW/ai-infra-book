# 《蝴蝶的鐵律》— 事實基準表（landscape, 2026-06）

> 本檔是全書的**事實錨點**。每一章的歷史、人名、年份、數值都必須與此一致；要改任何基準值，先改這裡、再同步全書、並在 maintenance.md 掃描日誌記一行。
> 規則：每條都帶「驗證值／一句註記／來源 URL」。無法以可信來源確認者標 ⚠️ 並說明原因。時效性敘述加註 (2026-06)。
> 信心分級：本書的事實多屬「數學恆真」（不會過時）與「史實」（已定案），時效風險主要落在「天氣可預測度上限」這類仍在演進的研究結論（見二、C11）。
> 本檔的史實與數值已由**兩個獨立流程**查證（2026-06-19 與 2026-06-20 各一次帶網路研究），12 組載重宣稱 12/12 一致；以下標 ✅ 者表示通過雙重查證。

---

## 一、歷史與人物（年份、歸屬、原話）

### 1. 拉普拉斯惡魔（Laplace's demon）✅
- **驗證值**：出自拉普拉斯 1814 年《機率的哲學試論》（*Essai philosophique sur les probabilités*）導論。經典英譯大意：「一個智者（une intelligence），若知道在某一刻驅動自然的所有力與萬物的所有位置，且其智力足以分析這些資料……對它而言沒有什麼是不確定的，未來會如過去一樣呈現在眼前。」
- **一句註記**：這是「嚴格物理決定論」的經典定義；拉普拉斯本人**用的是「智者／智能（intelligence）」、沒有用「惡魔（demon）」**，「demon」是後世評論者加上的稱呼。全書「決定論 vs 可預測性」對照的歷史起點。
- **來源**：https://en.wikipedia.org/wiki/A_Philosophical_Essay_on_Probabilities ；https://www.informationphilosopher.com/freedom/laplaces_demon

### 2. 龐加萊與三體問題、奧斯卡二世獎 ✅
- **驗證值**：
  - 瑞典與挪威國王奧斯卡二世（Oscar II）設立的國際數學競賽，**公告 1885 年**、為慶其 60 歲生日（1889-01-21）**頒獎 1889 年**。
  - 龐加萊（Henri Poincaré）得獎論文預定刊於《Acta Mathematica》。
  - 校稿者 **Lars Edvard Phragmén** 1889 年提出編輯疑問，龐加萊回應時於 **1889 年 11 月底發電報「停止印刷」、12 月承認重大錯誤**（他原以為證明了太陽系穩定性，此證明失效）。
  - 論文已印好並開始寄發；Mittag-Leffler 設法**召回幾乎所有副本**。
  - 龐加萊改寫出**修正版**（約原稿兩倍長），刊於 **1890 年《Acta Mathematica》卷 13**；改正過程中發現今日所稱的**同宿點／同宿纏結（homoclinic points／tangle）**，即首次對動力系統混沌行為的數學描述。
  - 龐加萊須自付額外印製費，**超過他贏得的獎金**。
- **一句註記**：「獎被頒了、論文卻得召回重印」是混沌史最戲劇的轉折——錯誤本身導出了混沌的發現。年份組：公告 1885、頒獎 1889、修正版刊出 1890。
- **來源**：https://link.springer.com/article/10.1007/BF00374436 （Barrow-Green, *Arch. Hist. Exact Sci.* 1994）；https://www.mittag-leffler.se/about-us/history/prize-competition/

### 3. 三體問題：無一般封閉解／Bruns、Sundman、現代編舞解 ✅
- **驗證值**：
  - **無一般封閉式（代數）解**：Bruns 1887 證明三體問題除 10 個古典積分外，沒有其他可表為座標與其導數之代數函數的首次積分；龐加萊 1890 進一步推到解析積分層面。
  - **Sundman 級數**：Karl Fritiof Sundman 1912 給出對所有時間收斂的冪級數解（以 t^(1/3) 的冪展開）；**實用上無用**（收斂極慢，需天文數字般多的項才達天文觀測精度；且排除零角動量／三體碰撞初始條件）。
  - **八字形編舞解（figure-eight choreography）**：由 Cris Moore 1993 以數值方法首次找到；**嚴格存在性證明**由 Alain Chenciner 與 Richard Montgomery 2000 發表（*Annals of Mathematics* 152(3), 881–901），用作用量泛函極小化證明。
- **一句註記**：「三體無解」的精確版是「**沒有一般封閉式代數解**」；它有特殊解（Euler、Lagrange、八字形）、也可數值積分到任意有限時間。書中要守住此直覺陷阱（見三、T6）。
- **來源**：https://en.wikipedia.org/wiki/Karl_F._Sundman ；https://gminton.org/choreointro.html （Chenciner–Montgomery 2000、Annals 152:881–901）

### 4. 阿達瑪（Jacques Hadamard）1898 ✅
- **驗證值**：Hadamard 1898 研究**負曲率曲面上的測地線流**，證明測地線彼此不穩定、以指數方式發散；被視為**最早被嚴格證明為混沌的動力系統之一**，並引入符號動力學描述對初始條件的敏感依賴。
- **一句註記**：「對初始條件敏感依賴」在 Lorenz 之前 60 餘年就有嚴格數學先例——混沌不是 1960 年代才冒出來。
- **來源**：https://en.wikipedia.org/wiki/Hadamard%27s_dynamical_system

### 5. 愛德華・勞侖次（Edward Lorenz）✅
- **驗證值**：
  - **1961 重新發現（MIT）**：Lorenz 用 12 變數天氣數值模型；為續算重新輸入先前印表機印出的中間值。電腦記憶體存六位小數 **0.506127**，印表機為省版面只印三位 **0.506**（差約**千分之一，約 0.1%**）。誤差隨時間放大，使後續結果完全不同——他由此意識到長期天氣預報不可行。
  - **1963 論文**：「Deterministic Nonperiodic Flow」，*Journal of the Atmospheric Sciences* 卷 20，頁 130–141。混沌理論奠基論文。
  - **方程式與參數**：σ=10、ρ(=r)=28、β=8/3（dx/dt=σ(y−x); dy/dt=x(ρ−z)−y; dz/dt=xy−βz）。經典「蝴蝶形」吸子標準參數。
  - **「蝴蝶」命名**：1972-12-29 在美國科學促進會（AAAS）第 139 屆會議演講題目「Predictability: Does the Flap of a Butterfly's Wings in Brazil Set Off a Tornado in Texas?」；**題目實際由氣象學家 Philip Merilees 在 Lorenz 缺席時代擬**。
  - **更早用「海鷗」**：Lorenz 在 **1963 NYAS Transactions** 論文寫道，一位（未具名）氣象學家說，若理論正確，一隻**海鷗（sea gull）**拍一次翅膀就足以永遠改變天氣走向。
- **一句註記**：「0.506127 → 0.506、六位捨成三位、約千分之一」是招牌故事，三細節都要對。蝴蝶之名來自 Merilees、不是 Lorenz 自取；蝴蝶之前用海鷗（出處是 NYAS 那篇，不是 JAS 那篇）。
- **來源**：https://www.technologyreview.com/2011/02/22/196987/when-the-butterfly-effect-took-flight/ ；https://physics.csuchico.edu/ayars/427/handouts/AJP000425.pdf （AAAS 1972、Merilees 命名、海鷗出處）

### 6. 李天岩（Li）& 約克（Yorke）1975：「Period Three Implies Chaos」✅
- **驗證值**：Tien-Yien Li 與 James A. Yorke，「Period Three Implies Chaos」，*The American Mathematical Monthly* 卷 82 第 10 期（1975-12），頁 985–992。首次在數學文獻使用「chaos（混沌）」一詞。
- **一句註記**：數學意義「混沌」一詞的命名出處；「週期 3 蘊含混沌」是銜接 Sharkovskii 定理的橋。
- **來源**：https://www.tandfonline.com/doi/abs/10.1080/00029890.1975.11994008

### 7. 夏可夫斯基定理（Sharkovskii 1964, 烏克蘭）✅
- **驗證值**：Oleksandr Sharkovsky 1964 論文「Coexistence of cycles of a continuous map of the line into itself」（《烏克蘭數學期刊》）。給自然數一個排序：先奇數 3,5,7,…，再各奇數×2、×4…，最後是 2 的冪 …,8,4,2,1。週期 3 排最前 → 「週期 3 ⇒ 所有週期都存在」。
- **一句註記**：比 Li–Yorke（1975）早 11 年、且結論更強（涵蓋所有週期共存）；拼法 Sharkovskii／Sharkovsky 並存。
- **來源**：http://www.scholarpedia.org/article/Sharkovsky_ordering

### 8. 羅伯特・梅伊（Robert May）1976 *Nature* 綜述 ✅
- **驗證值**：Robert M. May，「Simple mathematical models with very complicated dynamics」，*Nature* 261, 459–467（1976）。把邏輯斯諦映射與倍週期通往混沌的途徑推廣到生態、經濟、社會並普及化。
- **一句註記**：邏輯斯諦映射「廣為人知」主要靠這篇；May 是生態學家／物理出身。
- **來源**：https://www.nature.com/articles/261459a0

### 9. 米契爾・費根堡（Mitchell Feigenbaum）：常數與普適性 ✅
- **驗證值**：
  - 1975 年（用 HP-65 計算器）發現相鄰倍週期分岔參數間距比趨近約 4.6692 的常數。
  - 任職地點：**Los Alamos National Laboratory**（新墨西哥州）。
  - **普適性**：對一大類單峰映射（如 logistic、x→sin x），同一個 δ 都出現——倍週期通往混沌具普適性。
  - 正式論文「Quantitative Universality for a Class of Nonlinear Transformations」1978 年發表（*J. Stat. Phys.* 19(1):25–52）。
- **一句註記**：年份組「1975 發現、1978 正式發表、Los Alamos」三者都要對；普適性是書中「不同方程式、同一常數」最高潮（鐵律）。
- **來源**：https://mathworld.wolfram.com/FeigenbaumConstant.html ；https://writings.stephenwolfram.com/2019/07/mitchell-feigenbaum-1944-2019-4-66920160910299067185320382/

### 10. 本華・曼德博（Benoît Mandelbrot）：fractal、海岸線論文 ✅
- **驗證值**：
  - 「fractal（碎形）」一詞由 Mandelbrot **1975 年**鑄造（源於拉丁 *fractus*，破碎），首見 1975 法文書《Les Objets Fractals》。
  - 《The Fractal Geometry of Nature》**1982 年**出版。
  - 海岸線論文「How Long Is the Coast of Britain? Statistical Self-Similarity and Fractional Dimension」，*Science* **卷 156, 第 3775 期（1967-05-05），頁 636–638**。
- **一句註記**：海岸線論文卷號是 **156**（不是部分網頁誤植的「56」「165」）；它把 Richardson 的經驗觀察提升為「碎形維度」。
- **來源**：https://users.math.yale.edu/mandelbrot/web_pdfs/howLongIsTheCoastOfBritain.pdf ；https://en.wikipedia.org/wiki/The_Fractal_Geometry_of_Nature

### 11. 史蒂芬・史梅爾（Stephen Smale）：馬蹄映射 ✅
- **驗證值**：Smale 約 **1960 年**訪巴西里約（IMPA 期間）時，在科帕卡巴納（Copacabana）海灘構思出馬蹄映射（壓扁→拉長→折成馬蹄）。後寫成 1998 文章「Finding a Horseshoe on the Beaches of Rio」。
- **一句註記**：「海灘上的馬蹄」是 Smale 自述軼事，可放心使用；年份用「約 1960」。
- **來源**：http://www.scholarpedia.org/article/Smale_horseshoe

### 12. Ruelle & Takens 1971：「strange attractor」✅
- **驗證值**：David Ruelle 與 Floris Takens，「On the Nature of Turbulence」，*Communications in Mathematical Physics* 卷 20（1971），頁 167–192。此文鑄造「strange attractor（奇異吸子）」一詞。
- **一句註記**：「奇異吸子」命名出處；與 Lorenz 吸子、碎維度互相呼應。
- **來源**：https://www.ihes.fr/~/ruelle/PUBLICATIONS/146strange.pdf

### 13. James Gleick《Chaos: Making a New Science》1987
- **驗證值**：James Gleick，《Chaos: Making a New Science》，Viking，1987 出版。暢銷科普，把混沌與「蝴蝶效應」帶入大眾；入圍普立茲與美國國家圖書獎決選。副標是「Making a New Science」。
- **來源**：https://en.wikipedia.org/wiki/Chaos:_Making_a_New_Science

### 14. OGY 控制（Ott–Grebogi–Yorke 1990）
- **驗證值**：Edward Ott、Celso Grebogi、James Yorke，「Controlling Chaos」，*Physical Review Letters* 64, 1196（1990）。用小而即時的參數擾動，把混沌軌道穩定到嵌在吸子裡的某條不穩定週期軌。
- **一句註記**：「混沌可被控制」的奠基；ch18 用其直覺、不展開控制理論數學。
- **來源**：https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.64.1196

---

## 二、關鍵數值（必須精確；此為跨章基準）✅

### 邏輯斯諦映射 logistic map：x_{n+1} = r·x_n·(1 − x_n)
- **非零不動點** x* = 1 − 1/r；1 < r < 3 穩定（f′(x*) = 2 − r，|2−r| < 1 ⇔ 1 < r < 3）。
- **倍週期分岔點（onset 值）**：
  - r₁ = 3（週期 1 → 2）
  - r₂ = 1 + √6 ≈ **3.4495**（2 → 4）
  - r₃ ≈ **3.5441**（4 → 8；常引 3.54409）
  - r₄ ≈ **3.5644**（8 → 16；常引 3.564407）
  - r∞ ≈ **3.569945672…**（倍週期累積點／混沌起點，Feigenbaum 點）
  - 來源：https://en.wikipedia.org/wiki/Logistic_map ；https://astro.pas.rochester.edu/~aquillen/phy256/lectures/bif_maps.pdf
- **Feigenbaum 常數**：
  - δ ≈ **4.66920160910299**（倍週期間距比）
  - α ≈ **2.502907875**（x 軸尺度縮放比；嚴格符號為負 −2.5029，本書印正的量值 2.5029 並全書一致——見待考 #3）
  - 來源：https://mathworld.wolfram.com/FeigenbaumConstant.html
- **週期 3 視窗起點**：r = 1 + √8 (= 1 + 2√2) ≈ **3.8284**（精確 3.82843）。**位在混沌帶內**、機制是切線（鞍結）分岔，**不是**倍週期級聯的第三步。
  - 來源：https://en.wikipedia.org/wiki/Logistic_map
- **r = 4 時**：與帳篷映射（tent map，滿幅）拓撲共軛（共軛函數 φ(x)=(2/π)·arcsin(√x)）；不變密度 ρ(x)=1/(π·√(x(1−x)))，x∈[0,1]；李雅普諾夫指數 λ = **ln 2 ≈ 0.6931**（以 e 為底）。
  - 來源：https://mathworld.wolfram.com/LogisticMapR=4.html

### 勞侖次系統 Lorenz system（σ=10, ρ=28, β=8/3）
- **三個李雅普諾夫指數** ≈ (**+0.906**, 0, **−14.572**)（以 e 為底，每單位時間；Sprott 數值）。最大者常引 **≈ 0.9056**。
- **Kaplan–Yorke（Lyapunov）維度** D_KY = 2 + λ₁/|λ₃| ≈ **2.062**；關聯維度 ≈ 2.05；常以「≈ 2.06」概括。
- **李雅普諾夫時間** = 1/λ；以 λ≈0.9056 計 ≈ 1.10 時間單位。
- **混沌判據**：最大李雅普諾夫指數 λ > 0 ⇔ 混沌。
- 來源：https://sprott.physics.wisc.edu/chaos/lorenzle.htm

### 碎形維度（自相似維度 = ln N / ln(1/s)）
- Koch 曲線：ln 4 / ln 3 ≈ **1.2619**
- Cantor 集（中三分之一）：ln 2 / ln 3 ≈ **0.6309**
- Sierpiński 三角：ln 3 / ln 2 ≈ **1.585**
- **⚠️ 別交換**：Cantor ≈ 0.6309（介於 0 與 1）、Sierpiński ≈ 1.585（介於 1 與 2）——部分網路摘要把兩者值對調，務必守住。
- Mandelbrot 集**邊界**的 Hausdorff 維度 = **2**（Shishikura **1991 宣布／預印本、1998 正式刊** *Annals of Mathematics* 147(2):225–267）。
- 英國海岸線碎形維度 ≈ **1.25**（經驗估計，隨量測尺度 1.25–1.31）。
- 來源：https://users.math.yale.edu/mandelbrot/web_pdfs/howLongIsTheCoastOfBritain.pdf ；https://annals.math.princeton.edu/1998/147-2

### C11 — 大氣可預測度（atmospheric predictability）（2026-06，仍在演進，需 hedge）
- **經典「約兩週」上限**：1960 年代基於「誤差倍增時間約 5 天」的模型估計得出約兩週上限。
- **勞侖次後期估計**：1980 年代用更真實模型得較短倍增時間，**約 3.5 天**。
- **現代估計**：實務上限常引 **約 10–14 天**；Zhang et al.（2019）估計把現行初始條件誤差降一個數量級，中緯度技巧可延至**約 15 天**。
- **⚠️ 機器學習近年（2024–2026）**：GraphCast、FuXi 等 ML 天氣模型在 10 天尺度已常超越 ECMWF HRES；2025/2026 有研究（arXiv:2504.20238，後收於 *AIES*）報告在最佳化初始條件下，有用技巧（ACC≈0.6）可延到**約 27.5 天、甚至超過 30 天**——**結果有前景但尚未成為作業共識**。
- **一句註記**：書中講「兩週上限」要標明這是**實務經驗值／量級**、非定理；倍增時間 3.5–5 天視初始狀態與模型而異。**務必標 (2026-06)、給範圍、別寫死成「兩週，就這樣」**——這是全書最可能在一年內過時的一句。ML 的 30 天結果以「新興、未定」框，不要當成新上限。
- 來源：https://www.mdpi.com/2673-8392/3/3/63/html （Shen 等，Lorenz 的可預測度觀）；https://arxiv.org/html/2504.20238 （ML 超 30 天可預測度，新興）

---

## 三、常被誤傳／需守住的正確版（直覺的陷阱）

> 以下每條都是「大眾版 vs 正確版」，是「直覺的陷阱」段的素材。守住正確版。

### T1. 「蝴蝶效應」≠「微小原因必然造成某個巨大的特定結果」
- **正確版**：蝴蝶效應指**對初始條件的敏感依賴**，使**長期預測不可能**；它**不**保證某次拍翅一定造成某個特定龍捲風。它是**隱喻**，講可預測度的極限，不是直接因果鏈。Roger Pielke Sr. 直言單一拍翅在數千公里外引發特定龍捲風「答案是斷然的不」。
- **更深一層（Tim Palmer「真正的蝴蝶效應」，*Nonlinearity* 2014）**：某些多尺度流體系統有**絕對的有限時間可預測度屏障**——即使把初始誤差縮到任意小，預測期限仍趨於一個有限值，比 1963 年低階混沌（初值夠準就能預測任意久）更激進。書中可分兩層講。
- 來源：https://www.nationalgeographic.com/science/article/real-butterfly-effect-chaos-theory

### T2. 蝴蝶「形狀」與蝴蝶「拍翅」是兩件事（雙關巧合）
- **正確版**：勞侖次吸子在相空間呈雙螺旋、形似蝴蝶雙翼——這是**幾何形狀**的巧合；而「蝴蝶拍翅」隱喻是 1972 Merilees 擬的**題目**。兩者剛好都叫「蝴蝶」是雙關，**不是同一回事**，不要混講成「因為吸子像蝴蝶所以叫蝴蝶效應」。
- 來源：https://www.britannica.com/biography/Edward-Lorenz

### T3. 混沌 ≠ 隨機（randomness）
- **正確版**：混沌系統是**完全決定論**的——同初值給出同軌跡、無任何隨機項；表面的「亂」來自對初值的敏感依賴與粗粒化觀察，是**認識論的**不可預測，非本體論的隨機。
- 來源：https://plato.stanford.edu/entries/chaos/ （「chaotic behavior is always deterministic」）

### T4. 決定論（determinism）≠ 可預測性（predictability）
- **正確版**：SEP 明言「混沌與決定論的混淆，多半來自把決定論等同於可預測性」。決定論是「唯一演化」的本體論性質；可預測性是「我們能否算出來」的認識論能力。混沌打破的是後者。
- 來源：https://plato.stanford.edu/entries/chaos/

### T5. 混沌**沒有**推翻決定論
- **正確版**：混沌擊敗的是**長期預測**，不是決定論本身。即便系統不可預測，它仍可完全遵守決定論定律。流行說法稱混沌使決定論失效是誤解。
- 來源：https://plato.stanford.edu/entries/chaos/

### T6. 三體問題「無解」的精確意思
- **正確版**：指**沒有一般的封閉式（代數）解**（Bruns 1887／龐加萊 1890）。它**有**特殊解（Euler、Lagrange、八字形編舞解），也**可以數值積分**到任意有限時間，Sundman 甚至給了（實用無用的）收斂級數。別寫成「三體完全無法求解」。

### T7. 勞侖次本人的審慎
- **正確版**：勞侖次對「一隻蝴蝶是否真的引發某個特定龍捲風」是**保留**的——海鷗那句他歸給「一位（未具名）氣象學家」（轉述），蝴蝶題目是 Merilees 擬的；他真正主張的是「初始狀態微小差異使長期預報失準」，而非「拍翅必致龍捲風」。引用時要保留這份審慎。

### T8. 倍週期序 vs period-3 窗口（記號／標號陷阱）
- **正確版**：倍週期級聯到週期 8 在 r₃≈3.5441；period-3 窗口在 r=1+√8≈3.8284，**深在混沌帶內、機制是切線（鞍結）分岔，不是倍週期第 3 步**。Wolfram MathWorld 的 r 下標標號與本書（多數教材的倍週期序）不同，是同一批數字的不同標號、非矛盾，但書中要主動點破以免讀者混淆。

---

## 四、與書架相鄰書的邊界（僅供跨書指引，不需網路查證）

- **《馴服隨機》（probability）**：交界於「隨機 vs 決定論」「表面隨機的決定論系統」「不變密度 ρ(x) 是混沌軌跡的長期統計分布（遍歷性）」「白噪音」。本書講「混沌不是隨機／不是雜訊」時把機率語言指向它。
- **《馴服無限》（calculus，含微分方程／傅立葉）**：交界於「勞侖次系統是一組 ODE」「相空間軌跡＝微分方程解」「導數判斷不動點穩定性」「極限過程」「頻譜」。連續時間動力系統的工具指向它。
- **《矩陣是動詞》（linear algebra，含特徵值）**：交界於「不動點／週期軌穩定性＝雅可比矩陣特徵值的模是否 < 1」「線性化分析」「Lyapunov 指數＝長期平均對數伸縮率」。
- **《等待的數學》（queueing）**：交界較弱；「長期穩態分布 vs 對初值敏感的暫態」可順帶一提、不展開。

---

## 數值基準複核（跨章一致性速查表）

| 項目 | 基準值 | 備註 |
|---|---|---|
| logistic 非零不動點 | x* = 1 − 1/r | 1<r<3 穩定（f′=2−r） |
| r₁（1→2） | 3 | |
| r₂（2→4） | 1+√6 ≈ 3.4495 | |
| r₃（4→8） | ≈ 3.5441（3.54409） | |
| r₄（8→16） | ≈ 3.5644（3.564407） | |
| r∞（混沌起點） | ≈ 3.569945672… | Feigenbaum 點 |
| Feigenbaum δ | ≈ 4.66920160910299 | 間距比 |
| Feigenbaum α | ≈ 2.502907875（印正值） | 尺度比（嚴格符號負） |
| 週期 3 視窗起點 | 1+√8 = 1+2√2 ≈ 3.8284 | ≠ 倍週期第 3 步（切線分岔） |
| logistic r=4 不變密度 | 1/(π√(x(1−x))) | x∈[0,1] |
| logistic r=4 李指數 | λ = ln2 ≈ 0.6931 | 以 e 為底 |
| Lorenz 參數 | σ=10, ρ=28, β=8/3 | |
| Lorenz 最大李指數 | ≈ +0.9056（譜 ≈ +0.906,0,−14.572） | 以 e 為底，每單位時間 |
| Lorenz Kaplan–Yorke 維度 | ≈ 2.062（概括 ≈2.06） | =2+λ₁/\|λ₃\| |
| Lyapunov 時間 | 1/λ | λ>0 ⇔ 混沌 |
| 天氣可預測度上限 | 約 10–14 天（兩週，量級／經驗值） | 倍增 3.5–5 天；ML 新興挑戰，2026-06 |
| Koch 曲線維度 | ln4/ln3 ≈ 1.2619 | |
| Cantor 集維度 | ln2/ln3 ≈ 0.6309 | 介於 0 與 1 |
| Sierpiński 三角維度 | ln3/ln2 ≈ 1.585 | 介於 1 與 2（別與 Cantor 對調） |
| Mandelbrot 集邊界維度 | 2（Hausdorff） | Shishikura 1991 證／1998 刊 |
| 英國海岸線維度 | ≈ 1.25（1.25–1.31） | 經驗估計 |
| 勞侖次捨入故事 | 0.506127 → 0.506（6→3 位，約千分之一） | |
| 數學常數 | e≈2.71828、ln2≈0.6931、√6≈2.4495、√8≈2.8284 | 全書統一 |

### 關鍵年份速查
| 事件 | 年份 |
|---|---|
| 拉普拉斯《機率的哲學試論》 | 1814 |
| Bruns 無代數積分定理 | 1887 |
| 奧斯卡二世獎公告 | 1885 |
| 奧斯卡二世獎頒獎（國王 60 歲） | 1889 |
| 龐加萊修正版刊於 Acta Math. 卷 13 | 1890 |
| Hadamard 負曲率測地線 | 1898 |
| Sundman 收斂級數解 | 1912 |
| Smale 馬蹄映射（Copacabana） | 約 1960 |
| Lorenz 捨入重新發現（MIT） | 1961 |
| Lorenz "Deterministic Nonperiodic Flow"（JAS 20:130） | 1963 |
| Sharkovskii 定理（烏克蘭數學期刊） | 1964 |
| Ruelle & Takens 鑄「strange attractor」 | 1971 |
| Lorenz AAAS「蝴蝶」演講（Merilees 擬題） | 1972（12-29） |
| Feigenbaum 發現常數（Los Alamos、HP-65） | 1975 |
| Mandelbrot 鑄「fractal」 | 1975 |
| Li & Yorke「Period Three Implies Chaos」（Amer. Math. Monthly 82） | 1975 |
| May *Nature* 261:459 綜述 | 1976 |
| Feigenbaum 正式論文（普適性，J. Stat. Phys. 19) | 1978 |
| Mandelbrot《The Fractal Geometry of Nature》 | 1982 |
| Gleick《Chaos》 | 1987 |
| OGY「Controlling Chaos」（PRL 64) | 1990 |
| Moore 八字形解（數值） | 1993 |
| Shishikura 邊界維度＝2 正式刊（Annals 147) | 1998 |
| Chenciner & Montgomery 八字形存在性證明（Annals 152) | 2000 |

---

## 待考／低信心項（⚠️）

1. **天氣可預測度上限（C11，最重要的時效項）**（2026-06）：兩週是實務經驗值／量級、非定理；倍增 3.5–5 天；現代 10–17 天；ML（GraphCast/FuXi、arXiv:2504.20238）正把上限往 27.5–30 天推但屬新興未定。**務必標 (2026-06)、給範圍、ML 結果以「新興」框、別寫死。**
2. **英國海岸線維度 ≈ 1.25（1.25–1.31）**：經驗估計，隨量測尺度而異、非精確常數；書中以「約 1.25」表述。
3. **Feigenbaum α 符號**：嚴格為負（−2.5029…），本書若印正量值 2.5029 屬常見慣例，但**全書要一致**；提到時可一句註明「尺度比的量值，符號依慣例」。
4. **Sundman 級數所需項數**：量級廣傳但隨所求精度而變、非精確常數；書中以「天文數字般多的項」表述、不寫死指數。
5. **Lorenz λ／維度數值**：以 Sprott 數值（λ₁≈0.9056、D_KY≈2.062）為準；不同積分步長／時長會有末位差異，書中用「≈0.9056」「≈2.06」。
6. **同形記號歧義**（附錄 A 有專節）：λ＝Lyapunov 指數 vs 矩陣特徵值；α＝Feigenbaum 常數 vs 其他；r＝控制參數；σ/ρ/β＝Lorenz 參數；D＝維度。跨章新增內容引入這些符號前先回查附錄 A。

---
*掃描日期：2026-06-20。本檔事實由兩個獨立帶網路研究流程查證（2026-06-19 chaos-c 建書 30+ 次檢索；2026-06-20 本書建書 12 組載重宣稱獨立複查），12/12 一致。優先採一級／權威來源（原始論文、Britannica、SEP、大學講義、Annals／CMP 原文、Sprott、MathWorld）。*
