# 附錄 C — 閱讀地圖

> **這份附錄做什麼**：把全書攤成一張地圖，再給你幾條依興趣的捷徑、一份指向書架鄰書的跨書連結、以及一份去重後的延伸閱讀總清單。你不必從頭讀到尾——這裡告訴你：想懂某件事，該走哪幾章；讀完某章想往外走，該翻哪本書、哪篇論文。

## 全書地圖重述

下面這張圖你在每個 Part 首章都見過一次（「◄ 你在這裡」逐 Part 往下移）。這裡把它完整攤開，當作整本書的索引：

```text
全書地圖：決定論許下的承諾，如何被一條遞迴式拆穿，又如何露出鐵一般的秩序

  Part I  決定論的承諾 ............ 一個被算盡的宇宙，與它的第一道裂縫
     ch01 拉普拉斯的承諾
     ch02 三體：第一個解不開的時鐘
     ch03 0.506 與一隻蝴蝶（勞侖次）
     ch04 三條被混為一談的線（決定／隨機／可測）
        |
        v
  Part II  一條遞迴式裡的宇宙 ..... 脊椎：xₙ₊₁ = r·xₙ·(1−xₙ)
     ch05 同一條遞迴式
     ch06 不動點與穩定
     ch07 倍週期分岔
     ch08 費根堡常數（鐵律登場）
     ch09 混沌登場與秩序的孤島
        |
        v
  Part III  混沌的肖像 ........... 亂，長什麼樣子
     ch10 相空間
     ch11 奇異吸子
     ch12 碎形
     ch13 碎維度
        |
        v
  Part IV  為什麼測不準 .......... 不可預測的機制與極限
     ch14 Lyapunov 指數
     ch15 可預測的地平線
     ch16 拉伸與摺疊
        |
        v
  Part V  與混沌共處 ............ 分辨、駕馭、收束
     ch17 混沌不是雜訊
     ch18 駕馭混沌
     ch19 同一條遞迴式，現在你懂它七層
```

這本書的脊椎，是同一條遞迴式 xₙ₊₁ = r·xₙ·(1−xₙ)。它在每個 Part 換一張臉：ch05 是一條乖乖收斂的回授迴圈，ch07 一分為二再為四，ch08 撞上鐵律 δ≈4.6692，ch09 跨進混沌帶又露出秩序孤島，ch14 把敏感量成 λ=ln2、每步誤差翻倍，ch16 拆開它「拉伸＋摺疊」的製造機制。同一個 it，七層意義，ch19 攤成一張對帳表逐格收束——那七層就是全書的終點口試。整本書其實只在問一句話：**敏感（蝴蝶）與鐵律（普適）如何在這同一條確定的式子裡共存。**

## 依興趣的選讀路徑

不想 19 章順著爬？下面四條捷徑各帶你去一個明確的目的地。每條都自成一個故事，讀完那幾章就夠回答標題那個問題。

```text
路徑 A：只想懂「蝴蝶效應」一句話到底在講什麼
   ch01 → ch03 → ch04 → ch19
   立起「決定 ⇒ 可預測」的承諾（ch01），看勞侖次的 0.506 把它砍斷（ch03），
   分清「決定／隨機／可測」三條被混為一談的軸（ch04），最後在收官章
   聽惡魔死在哪一刀的完整版（ch19）。最短的「懂蝴蝶」路線。

路徑 B：想看那個跨系統不變的鐵律常數
   ch05 → ch07 → ch08
   先認識脊椎遞迴式（ch05），看它倍週期一分為二再為四（ch07），
   然後撞上全書最大驚嘆點——分岔間距以固定比例 δ≈4.6692 收縮，
   換成別的單峰映射還是同一個 δ（ch08）。三章看完「鐵律」。

路徑 C：想看混沌長什麼樣子（純視覺）
   ch10 → ch11 → ch12 → ch13
   相空間這面鏡頭（ch10），勞侖次蝴蝶吸子（ch11），碎形與自相似（ch12），
   再把「有多碎」變成一個分數維度（ch13）。這條是「混沌的肖像」整個 Part，
   亂之中的幾何秩序一次看完。

路徑 D：想懂為什麼天氣測不準（而且不是電腦不夠快）
   ch03 → ch14 → ch15
   先有敏感依賴的直覺（ch03），把它量成一個數 Lyapunov 指數 λ（ch14），
   再落到真實大氣的可預測地平線、兩週上限、系集預報（ch15）。
   讀完你會懂「測準十倍只多買一段固定的預測時間」。
```

四條路徑彼此有重疊（ch03 同時是 A 和 D 的起點），那是刻意的——它們交會的地方，就是全書反覆叩問的那條中央張力。讀完任一條想再往深走，順著地圖把缺的 Part 補回來即可。

## 跨書連結整理

書架上有幾本相鄰的書，本書遇到它們的主場時點到為止、把深度指過去。下面按主題整理「哪一章的哪件事，該往哪本書補」。格式照全書慣例（用主題帶過、不寫死他書精確章內容）。

```text
主題                          本書出現處        指向
────────────────────────────  ──────────────  ──────────────────────
隨機 vs 決定論的對照、         ch04            《馴服隨機》
表面隨機的確定性系統（PRNG）

不變密度 ρ(x) 作為混沌軌跡的   ch16            《馴服隨機》
長期統計分布（遍歷性）

白噪音、隨機漫步、「真隨機」    ch16、ch17      《馴服隨機》
的機率語言（雜訊散成雲）

冪律與 log-log 斜率的縮放律     ch13            《馴服隨機》（冪律）
                                              ＋《馴服無限》（對數）
```

- **隨機 vs 決定論**：本書一再強調「混沌不是隨機」「混沌不是雜訊」——混沌完全確定、表面的亂來自敏感依賴與粗粒化觀察。那份「真隨機在統計上反而很乖、可測」的機率論主場在《馴服隨機》。涉及 ch04（PRNG 是決定論造假亂的工程鐵證）、ch16（假亂 vs 真隨機的分界）、ch17（雜訊沒有 xₙ₊₁=f(xₙ) 的規則所以散成雲）。（見《馴服隨機》ch01）

```text
主題                          本書出現處        指向
────────────────────────────  ──────────────  ──────────────────────
勞侖次系統是一組 ODE、         ch10、ch11      《馴服無限》（微分方程）
相空間軌跡＝微分方程的解

導數＝瞬時斜率、               ch06、ch14      《馴服無限》（導數）
不動點穩定性的連續版判據

對數的縮放性質、頻譜（傅立葉）  ch13、ch17      《馴服無限》
```

- **連續時間動力系統的工具**：勞侖次那三條式子是 ODE，相空間軌跡是它們的解曲線；「每點給唯一速度向量」這條唯一性定理（軌跡不自交的嚴格底層）也在那本書。本書只用它的幾何結論。涉及 ch06、ch10、ch11、ch17。（見《馴服無限》談微分方程的章）

```text
主題                          本書出現處        指向
────────────────────────────  ──────────────  ──────────────────────
多維不動點／週期軌穩定性＝      ch06            《矩陣是動詞》（特徵值）
雅可比矩陣特徵值的模 < 1

線性化分析、Lyapunov 指數      ch14            《矩陣是動詞》
作為長期平均的對數伸縮率
```

- **線性化與特徵值**：本書一維的 |f′(x*)|<1 判據，是多維「Jacobian 特徵值的模全部 <1」的特例；Lyapunov 指數則是長期平均的對數伸縮率。多維怎麼算去那本書。涉及 ch06、ch14。（見《矩陣是動詞》談特徵值的章）

- **《等待的數學》（弱連結）**：交界較弱。若你對「長期穩態分布 vs 對初值敏感的暫態」這組對照有興趣，可順帶翻它一眼——排隊系統關心的是收斂後的穩態統計，混沌關心的是永遠不收斂、對初值敏感的暫態行為，兩者剛好是同一張時間軸的兩端。本書不展開。（見《等待的數學》）

## 延伸閱讀總清單（去重）

把全書 19 章的 `## 延伸閱讀` 彙整成一份分類總表。同一來源在多章出現的只列一次（標明它服務哪些章），每條一句話講「為什麼值得讀、讀哪一段」。標 ⭐ 的是 landscape 驗證過的權威來源；標「（未驗證）」的是我沒把握連結現況、但內容方向可信的。

### 必讀的哲學與概念錨點

- ⭐ **史丹佛哲學百科〈Chaos〉**（plato.stanford.edu/entries/chaos/）—— 全書最該先讀的一篇外部資料，貫穿 ch01／ch04／ch14／ch19。讀「determinism vs predictability」與「chaotic behavior is always deterministic」兩段：本書「決定論 ≠ 可預測」「混沌不是隨機」的哲學骨架全在這裡。那句「對混沌與決定論的混淆，多半來自把決定論等同於可預測性」值得抄在筆記第一頁。
- ⭐ **史丹佛哲學百科〈Causal Determinism〉**（plato.stanford.edu/entries/determinism-causal/）—— 服務 ch04／ch19。把「決定論＝唯一演化的本體論性質、可預測＝認識論能力」這條分界線摳得最乾淨；在四象限或「不可預測 ⇏ 未被決定」那步卡住時回頭看它。

### 經典科普（敘事版的全書）

- ⭐ **James Gleick《Chaos: Making a New Science》（Viking, 1987）**—— 服務 ch01／ch02／ch03／ch08／ch19，本書的散文版伴讀。第 1 章是蝴蝶效應走進大眾文化的源頭、〈Universality〉一章寫費根堡與物理學界的拉鋸、最後幾章把散落的發現編成「一門新科學」。享受它的敘事，但細節以本書事實基準為準（Gleick 流傳廣、若干考據後來更準）。
- **拉普拉斯《機率的哲學試論》英譯 *A Philosophical Essay on Probabilities***（archive.org 公版全文）—— 服務 ch01。讀導論前幾頁就好：決定論最強代言人寫的其實是一本講「機率即我們無知之度量」的書，這個反差本身就預告了 ch04。
- ⭐ **維基百科〈Laplace's demon〉**（en.wikipedia.org/wiki/Laplace's_demon）—— 服務 ch01。看 1814 原文英譯全文，注意它明確指出「demon」是後人加的綽號、原文用「intelligence」。本書守住的史實可一鍵複查。

### 歷史與原始論文（混沌的奠基文獻）

- ⭐ **June Barrow-Green《Poincaré and the Three-Body Problem》（AMS／LMS, 1997）**—— 服務 ch02。奧斯卡二世獎、出錯、召回重印整段歷史的權威專書，作者親自研究過原始檔案；1994 年《Archive for History of Exact Sciences》卷 48 的論文是濃縮版。
- ⭐ **Chenciner & Montgomery〈A remarkable periodic solution of the three-body problem…〉（*Annals of Mathematics* 152(3), 2000, 881–901）**—— 服務 ch02。八字形編舞解的嚴格存在性證明；數學偏硬，光看引言與那條八字軌道圖就能感受「三百年老問題仍在生新東西」（摩爾 1993 的原始數值發現在 *Phys. Rev. Lett.* 70, 3675）。
- ⭐ **Edward Lorenz〈Deterministic Nonperiodic Flow〉（*J. Atmos. Sci.* 20, 1963, 130–141）**—— 服務 ch03／ch11。混沌理論的奠基論文本尊，意外好讀。讀摘要與引言看勞侖次怎麼用最克制的語言說出「決定性卻非週期」；他描述「無限複雜的曲面複合體」那幾段，是人類第一次用大白話描述碎形（早曼德博鑄 fractal 十二年）。
- ⭐ **Edward Lorenz〈The Predictability of Hydrodynamic Flow〉（*Trans. NY Acad. Sci.* 25(4), 1963, 409–432）**—— 服務 ch03。「海鷗」那句話的真正出處（不是上面那篇 JAS）。想親眼確認「海鷗、未具名氣象學家、勞侖次的審慎」三件事，讀它的結尾段。
- ⭐ **T. N. Palmer, A. Döring, G. Seregin〈The real butterfly effect〉（*Nonlinearity* 27(9), 2014, R123）**—— 服務 ch03。想知道「比 SDIC 更狠的蝴蝶效應」（有限時間的絕對可預測屏障）長什麼樣就讀這篇；它把 Lorenz 1969 那篇被忽略的多尺度流論文重新挖出來。
- ⭐ **Robert May〈Simple mathematical models with very complicated dynamics〉（*Nature* 261, 1976, 459–467）**—— 服務 ch05。讓邏輯斯諦映射廣為人知的綜述，標題就是本書中心思想。讀導論與「the simplest nonlinear difference equation」一節，看一位生態學家怎麼意識到人口模型藏著整個混沌。
- ⭐ **Li & Yorke〈Period Three Implies Chaos〉（*Amer. Math. Monthly* 82(10), 1975, 985–992）**—— 服務 ch09。ch09 高潮的原始論文，也是「chaos」一詞在數學文獻的出生地。十頁不到，即使略過證明，讀引言與定理敘述能親眼確認「週期 3 蘊含全部」的精確分量。
- ⭐ **Feigenbaum〈Quantitative Universality for a Class of Nonlinear Transformations〉（*J. Stat. Phys.* 19(1), 1978, 25–52）**—— 服務 ch08。費根堡普適性的原始論文，標題裡的「Universality」就是 ch08 主角。不必硬啃全文，讀導論感受「他在主張一件多大的事」。
- ⭐ **曼德博〈How Long Is the Coast of Britain?…〉（*Science* 156(3775), 1967, 636–638）**—— 服務 ch12。碎形的起源論文、海岸線悖論的第一手出處；短、可讀，看曼德博怎麼把 Richardson 的經驗觀察提升成「碎形維度」。注意卷號是 **156**（不是某些網頁誤植的 56 或 165）。（users.math.yale.edu/mandelbrot/web_pdfs/howLongIsTheCoastOfBritain.pdf）
- ⭐ **曼德博《The Fractal Geometry of Nature》（1982）**—— 服務 ch12／ch13。碎形的聖經、「fractal」一詞的正式宣告地（拉丁 fractus＝破碎）。不必通讀，翻前幾章建立「自然界到處是碎形」的世界觀。
- ⭐ **Ruelle & Takens〈On the Nature of Turbulence〉（*Comm. Math. Phys.* 20, 1971, 167–192）**—— 服務 ch11。「strange attractor」一詞的出生證明；讀它怎麼從紊流逼出「長期行為被吸到一個非整數維度集合上」，理解「奇異＝碎形幾何」這個命名的脈絡。（ihes.fr/~ruelle/PUBLICATIONS/146strange.pdf）
- ⭐ **Shishikura〈The Boundary of the Mandelbrot Set Has Hausdorff Dimension Two〉（*Annals of Mathematics* 147(2), 1998, 225–267）**—— 服務 ch12。「邊界維度＝2」的正式證明（1991 證、1998 刊）。硬核論文，不必啃內文；看它把「一條邊界碎到維度頂滿成 2」坐實，就夠了。
- ⭐ **Takens〈Detecting strange attractors in turbulence〉（Springer LNM 898, 1981, 366–381）**—— 服務 ch17。延遲座標嵌入定理的原始論文、「單一變數重建吸子」的源頭。想看嚴格的嵌入維度條件（m > 2D）就讀這篇；本書只給了直覺。
- ⭐ **Smale〈Finding a Horseshoe on the Beaches of Rio〉（*The Mathematical Intelligencer*, 1998）**—— 服務 ch16。馬蹄發明人自述海灘軼事與數學動機，讀第一節「What Is Chaos?」就值回票價，是 Copacabana 故事的原始出處。
- ⭐ **Ott, Grebogi & Yorke〈Controlling Chaos〉（*Phys. Rev. Lett.* 64, 1196, 1990）**—— 服務 ch18。混沌控制的奠基論文，短而硬。讀引言就能確認那個翻轉：混沌吸子布滿不穩定週期軌、小擾動就能穩住一條，「混沌的存在對控制反而是優勢」是作者自己寫的。
- ⭐ **Stephen Wolfram〈Mitchell Feigenbaum (1944–2019), 4.66920160910299…〉**（writings.stephenwolfram.com）—— 服務 ch08。費根堡訃聞兼故事：HP-65、Los Alamos、在 Aspen 遇到史梅爾、從追極限值轉而追收斂比值的關鍵轉折，既有人味又精確。

### 標準教科書與權威數值（想看嚴格版）

- ⭐ **Strogatz《Nonlinear Dynamics and Chaos》**—— 全書的硬底子，服務 ch06／ch07／ch08／ch09／ch10／ch11／ch14／ch19。各章對應：第 5–7 章相平面與極限環（含第 6.8 節 Poincaré–Bendixson 定理，「二維裝不下混沌」的嚴格出處）、第 9 章勞侖次方程、第 10 章一維映射（不動點、cobweb、翻轉分岔、period-3 窗口、間歇性、Lyapunov）、第 10.6–10.7 節普適性與重整化。讀完本書再回看它的章末總結，你會發現本書是它的工程口語版。
- ⭐ **Sprott〈Lyapunov Exponents and Dimension of the Lorenz Attractor〉**（sprott.physics.wisc.edu/chaos/lorenzle.htm）—— 服務 ch11／ch13／ch14。勞侖次系統 Lyapunov 譜（≈+0.906, 0, −14.572）與維度 2.06（Kaplan–Yorke 2.062）的數值出處與算法。本書所有 Lorenz 數值的權威依據（landscape 2026-06 採用）。
- ⭐ **Wolfram MathWorld〈Feigenbaum Constant〉**（mathworld.wolfram.com/FeigenbaumConstant.html）—— 服務 ch08。δ≈4.66920160910299、α≈2.5029 的權威數值與定義；要核對小數位、看 δ 與 α 各自鎖橫縱的正式定義，看這裡。
- ⭐ **維基百科〈Logistic map〉**（en.wikipedia.org/wiki/Logistic_map）—— 脊椎式子的標準參考，服務 ch05／ch07／ch09／ch14。列齊分岔點 r₁=3、r₂≈3.4495、r₃≈3.5441、r₄≈3.5644、r∞≈3.57 與 r=4 全混沌，附互動分岔圖與 Lyapunov 曲線。守住一點：頁面對 period-3 窗口的 r 下標標號可能與本書倍週期序不同（陷阱 T8），數字本身一致。
- **Falconer《Fractal Geometry: Mathematical Foundations and Applications》**—— 服務 ch13。想看碎維度「直覺版」背後的嚴格定義（盒計數、Hausdorff、嚴格自相似時兩者相等），讀第 2–3 章。本書刻意略過的測度定義在這裡。
- **Kantz & Schreiber《Nonlinear Time Series Analysis》（第 2 版, Cambridge）**—— 服務 ch17。從時間序列判別混沌的標準教科書，把「重建結構、估 λ」兩條線與替代資料法寫成可操作方法。讀「Phase space methods」與「Surrogate data」兩章。
- **Theiler et al.〈Testing for nonlinearity in time series: the method of surrogate data〉（*Physica D* 58, 1992, 77–94）**—— 服務 ch17。替代資料法的奠基論文；ch17 陷阱「短資料＋相關雜訊會無中生有低維結構」與它的防禦，這篇講得最透徹。
- **Quillen〈PHY256 Lecture notes on Bifurcations and Maps〉**（astro.pas.rochester.edu/~aquillen/phy256/lectures/bif_maps.pdf）—— 服務 ch07。大學講義，從 f∘f 的不動點推 2-cycle 穩定性、列各分岔點數值，補上 ch07「乘子化簡」沒展開的代數。
- ⭐ **Scholarpedia〈Sharkovsky ordering〉**（scholarpedia.org，Sharkovsky 本人參與撰寫）—— 服務 ch09。夏可夫斯基排序 3◁5◁7◁…◁8◁4◁2◁1 的權威說明，把「比 Li–Yorke 更強更全」講具體。
- **維基百科主題條目群**—— 散見各章，挑你卡住的概念查：〈Cobweb plot〉（ch06）、〈Period-doubling bifurcation〉（ch07，翻轉分岔與負號）、〈Coastline paradox〉〈Koch snowflake〉〈Cantor set〉（ch12）、〈Phase space〉〈Phase portrait〉〈Limit cycle〉〈Van der Pol oscillator〉（ch10）、〈Lyapunov time〉（ch14，e-folding 與太陽系 vs 天氣對照）、〈Tent map〉〈Dyadic transformation〉（ch16，左移一位＝暴露一個 bit＝λ=ln2）。

### 天氣可預測度與系集預報（ch15 主場，2026-06 時效敏感）

- ⭐ **Bo-Wen Shen et al.〈Lorenz's View on the Predictability Limit of the Atmosphere〉（*Encyclopedia* 3(3), 2023, 887–899, MDPI）**—— 服務 ch15。把「兩週上限」的真實身世講最清楚：它來自 Charney 1966 的 5 天倍增外推、而非 Lorenz 的定理。釐清「量級非定理」這個分寸的最佳來源。
- ⭐ **Fuqing Zhang et al.〈What Is the Predictability Limit of Midlatitude Weather?〉（*J. Atmos. Sci.* 76(4), 2019, 1077–1091）**—— 服務 ch15。「實務 ~10 天 vs 內在 ~15 天」「降一個數量級初始誤差換約 5 天」兩個關鍵數字的原始出處；想看對數報酬在真實大氣裡長什麼樣，讀結論段。
- ⭐ **〈Testing the Limit of Atmospheric Predictability with a Machine Learning Weather Model〉（arXiv:2504.20238，後收於 *AIES*；2026-06 仍為新興結果）**—— 服務 ch15。ML 把確定性技巧在最佳化初始條件下推到約 27.5–33 天的研究。讀它正是為了學會 hedge：作者自己強調這是最佳化初值的研究設定、不是作業共識，別把 30 天當成新上限。
- **ECMWF〈Introduction to chaos, predictability and ensemble forecasts〉**（線上教材，2026-06 可查）—— 服務 ch15。系集預報的權威入門：為什麼混沌讓單一預報「可能毫無意義」、為什麼從 51 個微擾起點出發、spread 怎麼讀。「追一團起點」的工程版操作手冊。
- **Tim Palmer《The Primacy of Doubt》（Oxford University Press, 2022）**—— 服務 ch15。把「不確定性是預報的主角、不是缺陷」寫成一整本書的科普，作者是系集預報奠基者之一；想把「誠實面對地平線」擴展成世界觀就讀它。

### 應用與爭議（ch18 主場，hedge 素材）

- ⭐ **Garfinkel, Spano, Ditto & Weiss〈Controlling Cardiac Chaos〉（*Science* 257, 1230, 1992）**—— 服務 ch18。把混沌控制用到活體（兔心室）的標誌性論文。讀它**同時**讀後續爭議文獻（surrogate data 檢定那條線），你會體會 ch18 的 hedge 重心：控制有效 ≠ 底層一定是混沌。
- **Crutchfield & Mitchell 等〈Dynamics, Computation, and the "Edge of Chaos": A Re-Examination〉（1993）**—— 服務 ch18。「混沌的邊緣」假說的關鍵打臉文獻：重做 Langton 的細胞自動機實驗、無法重現「計算最強點在臨界值」。讀它能把對 edge of chaos 的 hedge 從「聽說有爭議」變成「看到爭議在哪」。
- ⭐ **Pecora & Carroll〈Synchronization in Chaotic Systems〉（*Phys. Rev. Lett.* 64, 821, 1990）**—— 服務 ch18。混沌同步的奠基論文、保密通訊那條應用線的技術根。兩個對初值極度敏感的系統居然能被一條耦合訊號拉到同步——讀完再回看本書對混沌加密安全性的保留，會懂「能同步」離「安全」還很遠。

### 視覺直覺與輔助讀物（看圖建立感覺）

- **Geoff Boeing〈Chaos Theory and the Logistic Map〉／〈Visualizing Chaos and Randomness〉**（geoffboeing.com, 2015）—— 服務 ch07／ch17。用大量分岔圖、cobweb 圖把「不動點→2-cycle→混沌」一級級畫出來；後者用延遲座標散點對照白噪音雲，跟 ch17 招牌圖同一個點子。配 ASCII 示意一起看會立體起來。（2026-06 可存取）
- **3Blue1Brown／Numberphile 的 Mandelbrot 集影片**（YouTube）—— 服務 ch12。Mandelbrot 集邊界「放大永遠冒出新細節與自我複本」動態看比靜態圖震撼十倍；3Blue1Brown 那支還會把它跟 z→z²+c 迭代、跟 Julia 集的關係講清楚，補上 ch12「血緣」那段的視覺版。
- **Jean-Luc Thiffeault 等〈The mathematics of taffy pullers〉（arXiv:1608.00152）＋ Smithsonian Magazine 科普版**—— 服務 ch16。太妃糖機真的是用混沌動力系統（pseudo-Anosov 映射）的數學分析的；讀它你會徹底相信「拉太妃糖＝製造混沌」不是比喻。先讀 Smithsonian 圖文版再啃 arXiv。
- **John D. Cook〈Cobweb plots〉**（johndcook.com, 2020）—— 服務 ch05。短而清楚的部落格，把蛛網圖「垂直碰曲線、水平碰對角線」雙步驟講透，配圖示範收斂與發散的不同路徑。
- **Yale 大學〈Fractal Geometry〉課程網站，Similarity Dimension 一節**（gauss.math.yale.edu/fractals）—— 服務 ch13。自相似維度 D=lnN/ln(1/s) 的標準教學，逐個碎形示範 N 與 s 怎麼數。讀「Similarity Dimension」與「Box-Counting Dimension」兩節。（2026-06 可存取）
- **plus.maths.org〈Smale's chaotic horseshoe〉**（未驗證）—— 服務 ch16。馬蹄映射的免費線上科普建構；想看「拉伸-摺疊如何變成嚴格定理」（符號動力學）而不被論文嚇到，從這裡入門。
- **Scholarpedia〈Attractor reconstruction〉**（scholarpedia.org）—— 服務 ch17。延遲座標重建、嵌入維度與延遲 τ 怎麼選的標準整理，是 Takens 原文和教科書之間最好的橋。讀「Delay coordinates」與「Choosing the embedding parameters」兩節。
- **Nicolas Bacaër〈Verhulst and the logistic equation (1838)〉**（未驗證）—— 服務 ch05。維赫斯特連續版邏輯斯諦方程的歷史與原貌；它的**連續**版乖乖收斂成 S 曲線，本書用的**離散**遞迴版才長出混沌——同一個名字、兩種命運。
- **The Conversation〈Pi might look random but it's full of hidden patterns〉**（未驗證）—— 服務 ch04。把「看起來隨機 ≠ 是隨機」講得最白話的一篇；π 是決定論造假亂的另一個漂亮標本（跟 LCG 同類），讀它能加固你對「混沌 ≠ 隨機」的免疫力。

---

讀到這裡，這趟旅程的地圖、捷徑、鄰書與外部資源都在你手上了。回到那條三個符號的遞迴式——它在 ch19 攤成七層；往書架外走，從上面這份清單挑下一步。混沌沒推翻決定論，它只砍斷了「決定 ⇒ 可預測」這一道箭頭；而那道被砍斷的地方，恰恰露出一條鐵一般、跨系統不變的秩序。這本書要你帶走的，就是這一句。
