# 附錄 C — 閱讀地圖

> 這份地圖是給讀完（或不打算線性讀完）全書的人用的：先把全書十九章的結構重述一遍，再給幾條依興趣的捷徑，整理本書與書架上相鄰幾本的交界，最後把散在各章末尾的延伸閱讀去重彙整成一份分類清單。連結現況以 2026-06 為基準；只收 `_meta/landscape-2026-06.md` 或各章已查證過的資源，沒把握的標「（未驗證）」。

## 全書地圖重述

```text
全書地圖：一條遞迴式，從秩序走到混沌，再走回來

  Part I  鐘錶宇宙的裂縫 ........ 決定論的夢，與第一道裂縫
     ch01 拉普拉斯的惡魔
     ch02 龐加萊的三體問題
     ch03 蝴蝶效應（勞侖次）
     ch04 決定論 不等於 可預測
        |
        v
  Part II  一條遞迴式裡的宇宙 ... 脊椎：xₙ₊₁ = r·xₙ·(1−xₙ)
     ch05 同一條遞迴式
     ch06 不動點與穩定
     ch07 倍週期分岔
     ch08 費根堡普適性
     ch09 混沌登場與秩序孤島
        |
        v
  Part III  混沌的肖像 ......... 混沌長什麼樣子
     ch10 相空間
     ch11 奇異吸子
     ch12 碎形與自相似
     ch13 碎維度
        |
        v
  Part IV  為什麼測不準 ........ 不可預測的機制與極限
     ch14 Lyapunov 指數
     ch15 可預測的地平線
     ch16 拉伸與摺疊
        |
        v
  Part V  與混沌共處 .......... 分辨、駕馭、收束
     ch17 混沌 不等於 雜訊
     ch18 駕馭混沌
     ch19 同一條遞迴式，現在你懂它七層
```

五個 Part 是一條有去有回的弧線：**Part I** 立起「決定論的夢」這個標靶，從拉普拉斯的惡魔到龐加萊三體、勞侖次蝴蝶，第一次看見裂縫，並在 ch04 把「決定論／隨機／可預測」三條被混為一談的軸拆開。**Part II** 是全書的脊椎——一條一行的邏輯斯諦映射 `xₙ₊₁ = r·xₙ·(1−xₙ)`，只轉動 r 這個旋鈕，就看到秩序→倍週期→普適常數 δ→混沌＋秩序孤島的完整劇情。**Part III** 換成連續時間與空間，問混沌「長什麼樣子」：相空間、奇異吸子、碎形、分數維度。**Part IV** 回答「為什麼測不準」的機制與極限：Lyapunov 指數把敏感變成一個數、可預測地平線把它落到天氣、拉伸與摺疊揭開製造混沌的工序。**Part V** 收束：怎麼把混沌和真雜訊分辨開、混沌怎麼被駕馭與利用，最後在 ch19 用同一條遞迴式對帳七層意義、回答「惡魔死在哪一刀」。

## 依興趣的選讀路徑

不想一章一章讀完的人，可以照興趣挑一條捷徑。每條都點名章號，缺前置概念時各章開頭的 blockquote 會告訴你該回哪裡補。

- **「只想搞懂蝴蝶效應到底在說什麼」** → ch01 → ch03 → ch04 → ch19。ch01 立起「決定論⇒可預測」這個被全書拆解的標靶，ch03 把敏感依賴（SDIC）與蝴蝶名稱史講透，ch04 把「決定論／隨機／可預測」三軸分清楚，ch19 收成一句話：混沌殺死的不是決定論，是「決定論⇒可預測」這個推論。讀完你能對另一個工程師講清楚震撼在哪。
- **「想看脊椎遞迴式的完整劇情」** → ch05 → ch06 → ch07 → ch08 → ch09 → ch14 → ch16。從一行回授迴圈出發（ch05），看不動點怎麼吸引或排斥（ch06）、旋鈕過 3 後一分為二再分為四（ch07）、不同映射撞同一個 δ≈4.669 的普適性（ch08）、越過 r∞ 進入混沌帶又冒出 period-3 秩序孤島（ch09）；然後 ch14 給它 λ=ln2 的數字、ch16 拆開「拉伸＋摺疊」的製造工序。這是全書最連貫的一條主線。
- **「衝著碎形與奇異吸子的視覺」** → ch10 → ch11 → ch12 → ch13。相空間先建立「狀態＝一點、演化＝一條軌跡、軌跡不自交」的鏡頭（ch10），勞侖次蝴蝶吸子兌現「有界＋永不重複＋不自交」三者共存（ch11），碎形給它幾何語言（ch12），分數維度把「有多碎」變成一個介於 1 與 2 之間的數（ch13）。本書的招牌程式生成圖大多在這四章。
- **「為什麼天氣測不準」** → ch03 → ch14 → ch15。ch03 用勞侖次 0.506 vs 0.506127 的列印軼事帶出敏感依賴，ch14 把它量化成 Lyapunov 指數與「對數報酬」，ch15 落到真實天氣的兩週可預測極限、系集預報、以及「為什麼這不是電腦不夠快能解決的」。

## 跨書連結整理

本書定位是「用欣賞的聲音講為何美、為何反直覺」，運算與理論深度指向書架上相鄰的幾本。下表整理主要交界；引用格式全書統一為「（見《某某書》chNN）」，不寫死檔名。

| 相鄰書 | 交界主題 | 本書涉及章節 |
|---|---|---|
| 《馴服隨機》（機率） | 真隨機 vs 決定論、機率分布與大數法則、隨機過程與白噪音、不變密度＝混沌軌跡的長期統計分布 | ch04、ch16、ch17 |
| 《馴服無限》（微積分） | 微分方程與 ODE（勞侖次系統）、相空間軌跡＝微分方程解、導數與斜率、指數與對數 | ch10、ch11、ch14、ch15 |
| 《矩陣是動詞》（線性代數） | 多維不動點穩定性＝Jacobian 特徵值的模是否 <1、線性化分析、伸縮方向與倍率 | ch06、ch13、ch14 |
| 《等待的數學》（佇列） | 回授系統的長期穩態 vs 對初值敏感的暫態（弱連結，順帶一提、不展開） | ch15、ch18 |

具體落點：混沌「不是隨機」的另一半——真隨機怎麼被大數法則收編成測得準的分布——在《馴服隨機》ch01／ch02；時間軸上的隨機與白噪音長什麼樣，見《馴服隨機》ch20。連續時間動力系統「給變化率、求軌跡」這件事本身怎麼做，見《馴服無限》談微分方程的章。一維 |f′(x*)|<1 的穩定判據推廣到多維的特徵值版本，見《矩陣是動詞》談特徵值的章。

## 延伸閱讀總清單

各章末尾的延伸閱讀去重後分成五類。每條一句話說明為什麼值得讀、讀哪一段；標 ch 者指該書內首次或主要引用的章。

### 經典科普與傳記

- **James Gleick《Chaos: Making a New Science》（Viking, 1987）** — 把混沌史寫成故事的暢銷經典，副標是「Making a New Science」。讀第一章〈The Butterfly Effect〉感受「氣象學家被自己的數值機器打臉」的戲劇性；它就是讓「蝴蝶效應」走進大眾文化的那本書。當敘事讀、細節以本書 landscape 為準。（ch01／ch02／ch03）
- **Stephen Wolfram,〈Mitchell Feigenbaum (1944–2019), 4.66920160910299067185320382…〉（2019 訃聞長文）** — https://writings.stephenwolfram.com/2019/07/mitchell-feigenbaum-1944-2019-4-66920160910299067185320382/ 把費根堡 1975 在 Aspen 受啟發、回 Los Alamos 用 HP-65 算分岔點、發現拋物線與正弦映射撞同一個 δ、論文兩度被退稿才在 1978 登上 *J. Stat. Phys.* 的故事講得最生動。讀「the discovery」一段。（ch08）
- **Peter Dizikes,〈When the Butterfly Effect Took Flight〉，*MIT Technology Review*（2011）** — https://www.technologyreview.com/2011/02/22/196987/when-the-butterfly-effect-took-flight/ 蝴蝶效應正確版的好科普：它是「對初始條件的敏感依賴」、講的是長期預測不可能，不是「小因必致特定大果」。（ch19）
- **National Geographic,〈The butterfly effect is a real phenomenon—but not how you think〉** — 用大眾語言把「蝴蝶效應 ≠ 小因必致特定大果」講清楚，含 Roger Pielke Sr.「斷然的不」那段。想向非工程師朋友轉述本書時拿來對照措辭。（ch03，2026-06 可查）

### 奠基論文（史實的一級來源）

- **Edward Lorenz,〈Deterministic Nonperiodic Flow〉，*Journal of the Atmospheric Sciences* 20 (1963): 130–141.** 混沌理論奠基論文本尊；SDIC 的原始定義在這裡。即使不細讀那三條 ODE，也值得讀摘要與引言，看 1963 年的勞侖次怎麼用最克制的語言說出「決定性卻非週期」。（ch03／ch11）
- **Edward Lorenz,〈The Predictability of Hydrodynamic Flow〉，*Transactions of the New York Academy of Sciences* 25(4) (1963): 409–432.** 「海鷗」那句話的真正出處（不是上面那篇 JAS）。想親眼確認「海鷗、未具名氣象學家、勞侖次的審慎」三件事，讀它的結尾段。（ch03）
- **Li, T.-Y. & Yorke, J. A.,〈Period Three Implies Chaos〉，*The American Mathematical Monthly* 82(10) (1975): 985–992.** 數學意義上「混沌」一詞的出處。論文短、可讀，看它怎麼用介值定理把「一個週期 3」撐出「所有週期」。原文 PDF：https://www.nku.edu/~longa/classes/mat360/days/resources/docs/Chaos/Li-PeriodThreeImplies-1975.pdf （ch09，2026-06 可讀）
- **Robert May,〈Simple mathematical models with very complicated dynamics〉，*Nature* 261 (1976): 459–467.** 讓邏輯斯諦映射紅遍科學界的綜述。讀它對「stable points → bifurcating cycles → apparently random fluctuations」的概述，正是本書 Part II 的劇本。https://www.nature.com/articles/261459a0 （ch04／ch05／ch07／ch18）
- **Mitchell Feigenbaum,〈Quantitative Universality for a Class of Nonlinear Transformations〉，*J. Stat. Phys.* 19:25 (1978).** 普適性的原始正式論文。本書只給直覺；想看普適性與重整化怎麼被嚴肅論證，從引言與結論讀起（中段泛函分析可略）。（ch08）
- **Mandelbrot,〈How Long Is the Coast of Britain? Statistical Self-Similarity and Fractional Dimension〉，*Science* 156 (1967): 636–638.** 海岸線悖論的原始論文，把理查森的經驗觀察提升為「碎形維度」。卷號是 **156**（常被誤植 165，認準 156）。https://www.science.org/doi/10.1126/science.156.3775.636 （ch12／ch13）
- **Ruelle & Takens,〈On the Nature of Turbulence〉，*Comm. Math. Phys.* 20 (1971): 167–192.** 「strange attractor（奇異吸子）」一詞的出生地。技術較重，但你至少該知道這個名字從哪來。（ch11）
- **Steve Smale,〈Finding a Horseshoe on the Beaches of Rio〉，*The Mathematical Intelligencer* 20 (1998): 39–44.** 馬蹄映射發明人的第一手回憶：Copacabana 海灘、Levinson 的信、原本以為「混沌不存在」、訂正錯誤反而撞出馬蹄。讀來像偵探故事，數學門檻低。（ch16）
- **Shishikura,〈The Hausdorff Dimension of the Boundary of the Mandelbrot Set and Julia Sets〉，*Annals of Mathematics* 147 (1998).** 證明 Mandelbrot 集**邊界**維度＝2（1991 公布、1998 正式發表）。硬核複動力系統，不必全讀；看 abstract 確認「是邊界的維度＝2」，守住本書最常被講錯的點。https://arxiv.org/abs/math/9201282 （ch12）
- **June Barrow-Green,〈Oscar II's Prize Competition and the Error in Poincaré's Memoir on the Three Body Problem〉，*Archive for History of Exact Sciences*（1994）。** 奧斯卡二世獎事故的權威考據：召回經過、錯誤性質、龐加萊自付印費超過獎金。本書 ch02 史實的一級來源；想看完整時間軸讀這篇。延伸的專書是 June Barrow-Green《Poincaré and the Three-Body Problem》（AMS, 1997），含「1885 設立」這類細節考據（本書對該年份保持保留，想自核者從這裡查起）。（ch02）
- **龐加萊《天體力學新方法》（*Les méthodes nouvelles de la mécanique céleste*, 1892–1899）。** 他在這套書裡寫下「同宿纏結複雜到我不敢嘗試畫出」的那段話。讀第三卷談漸近解與同宿軌的部分，感受發現者本人的眩暈。（ch02）
- **Ott, Grebogi & Yorke,〈Controlling Chaos〉，*Physical Review Letters* 64 (1990): 1196–1199.** OGY 控制法的原始論文，本書 ch18 的源頭。讀引言與方法概述，看他們怎麼把「敏感」當槓桿、怎麼用延遲座標就地估出局部動力學。全文 PDF 可於 yorke.umd.edu 取得。（ch18）
- **Ditto, Rauseo & Spano,〈Experimental Control of Chaos〉，*Physical Review Letters* 65 (1990): 3211.** OGY 第一個被廣泛引用的實驗驗證（磁彈性帶）。感受「實驗室成功」的真實尺度，以及離「產品」還很遠。（ch18）
- **Garfinkel, Spano, Ditto & Weiss,〈Controlling Cardiac Chaos〉，*Science* 257 (1992): 1230–1235.** 混沌控制最有名的生物應用。重點讀它對「敏感使系統既不可預測又極易控制」的措辭；同時記住 hedge：這不證明「正常心臟是混沌的」。（ch18）
- **Mitchell, Crutchfield & Hraber,〈Dynamics, Computation, and the "Edge of Chaos": A Re-Examination〉（1993）。** 對「混沌邊緣＝最有計算力」具體主張的批判性重做。想對任何「邊緣很強大」的宣稱保持戒心，讀這篇——它示範怎麼用重做實驗戳破一個太順的故事。melaniemitchell.me 有作者自存 PDF。（ch18）
- **T. N. Palmer, A. Döring, G. Seregin,〈The real butterfly effect〉，*Nonlinearity* 27(9) (2014): R123.** 「比 SDIC 更狠的蝴蝶效應」——有限時間的絕對可預測屏障。它把 Lorenz 1969 年 Tellus 那篇被忽略的多尺度流論文重新挖出來，主張那才是勞侖次心裡真正的蝴蝶效應。（ch03）
- **Packard, Crutchfield, Farmer & Shaw,〈Geometry from a Time Series〉，*Physical Review Letters* 45 (1980): 712–716.** 比 Takens 定理早一年的直覺起點，第一次提出「用一個變數的延遲座標重建相空間幾何」。短、好讀。（ch17）
- **Floris Takens,〈Detecting Strange Attractors in Turbulence〉（1981）。** 延遲嵌入定理的原始論文，本書 ch17 相空間重建的理論根。讀引言與定理陳述就好（證明硬核），抓「單一變數的延遲座標足以重建吸子」這個核心。收於 Springer *Lecture Notes in Mathematics* 898。（ch17）
- **Theiler et al.,〈Testing for Nonlinearity in Time Series: The Method of Surrogate Data〉，*Physica D* 58 (1992).** 替身資料法的奠基論文。本書「判別不是看一眼、是跟去掉確定性的對照組比」的科學紀律出自這裡，補的是「有限維度 ≠ 混沌」這個洞。（ch17）
- **Zhang, F. et al.,〈What Is the Predictability Limit of Midlatitude Weather?〉，*J. Atmos. Sci.* 76(4) (2019): 1077–1091.** 本書 ch15「現代估計」那些數字（實務 ~10 天、降一個數量級誤差 → ~15 天、孿生實驗 ~17 天）的原始出處。重點在「這道極限是系統內在的、即使模型與初值近乎完美仍存在」。https://journals.ametsoc.org/view/journals/atsc/76/4/jas-d-18-0269.1.xml （ch15，2026-06 可讀）

### 權威詞條與百科

- **Stanford Encyclopedia of Philosophy,〈Chaos〉（Robert Bishop）** — https://plato.stanford.edu/entries/chaos/ 本書哲學立場的定盤星。讀「determinism vs. predictability」與「chaotic behavior is always deterministic」兩處，它把「混沌是決定論的、不可預測是認識論的而非本體論的」「混沌不推翻決定論」講得最乾淨。（ch01／ch04／ch19，2026-06 為現行版本）
- **Stanford Encyclopedia of Philosophy,〈Causal Determinism〉** — https://plato.stanford.edu/entries/determinism-causal/ 決定論（本體論）與可預測性（認識論）的分野，以及對自由意志「點到為止」的謹慎尺度，本書 ch19 就以它為準。（ch19）
- **Encyclopaedia Britannica,〈butterfly effect〉** — https://www.britannica.com/science/butterfly-effect 快速核對 1972 AAAS 題目由 Merilees 擬、勞侖次原本用海鷗、吸子形似蝴蝶與蝴蝶拍翅是雙關巧合這幾件常被講錯的事。（landscape／ch03）
- **維基百科〈Laplace's demon〉** — https://en.wikipedia.org/wiki/Laplace%27s_demon 核對「拉普拉斯本人未用 demon、後人加上」，以及量子力學／熱力學後來怎麼從另一個方向反駁惡魔（與本書的混沌路徑互補）。（ch01）
- **維基百科〈Period-doubling bifurcation〉** — https://en.wikipedia.org/wiki/Period-doubling_bifurcation 對齊 r₂=1+√6、r₃≈3.54409、r∞≈3.56995 等分岔點數值。讀「logistic map」那一節。（ch07）
- **維基百科〈Feigenbaum constants〉** — https://en.wikipedia.org/wiki/Feigenbaum_constants δ≈4.66920160910299 與 α≈2.502907875 的精確值、各管哪個方向的縮放、普適類範圍，速查與交叉驗證用。（ch08）
- **維基百科〈Cobweb plot〉** — https://en.wikipedia.org/wiki/Cobweb_plot 蛛網圖的純幾何說明：階梯收縮 vs 張開、螺旋進 vs 螺旋出，配 ch06 的 ASCII 示意一起看。（ch06）
- **維基百科〈Phase space〉與〈Limit cycle〉** — https://en.wikipedia.org/wiki/Phase_space ；https://en.wikipedia.org/wiki/Limit_cycle 定義、單擺相圖、極限環 vs 閉環的差別，配 ch10 三連圖讓「孤立且吸引」更實。（ch10）
- **維基百科〈Coastline paradox〉與〈Koch snowflake〉** — https://en.wikipedia.org/wiki/Coastline_paradox 找更多量測數字、Koch 雪花「無窮周長有限面積」的算法、理查森的西班牙—葡萄牙邊界軼事。當導覽用，原始數字仍以一級來源為準。（ch12）
- **維基百科〈Dyadic transformation〉** — https://en.wikipedia.org/wiki/Dyadic_transformation 二進位移位（doubling／Bernoulli map）的乾淨整理：怎麼「逐位砍掉 x 的二進位展開」、|f′|=2 給出 λ=ln2、「m 步後只剩 s−m 個 bit 資訊」——ch16 worked example 的數值依據。（ch16）
- **Wolfram MathWorld,〈Logistic Map〉與〈Logistic Map: r = 4〉** — https://mathworld.wolfram.com/LogisticMap.html 有 2-cycle 封閉式推導與 r=4 的 λ=ln2、不變密度 1/(π√(x(1−x)))、與帳篷映射共軛 φ(x)=(2/π)arcsin√x。**讀時務必注意它的 r 下標慣例和本書（多數教材）不同**：它把 1+2√2≈3.8284 標 period-3、1+√6≈3.4495 標 period-4，對照 ch07／ch09 的鐵則一起看，反而能加深「倍週期序 vs 窗口」的區別。（ch07／ch09／ch14）
- **Scholarpedia,〈Sharkovsky ordering〉與〈Smale horseshoe〉** — http://www.scholarpedia.org/article/Sharkovsky_ordering ；http://www.scholarpedia.org/article/Smale_horseshoe 前者把完整偏序與「週期 3 在最前」講清楚、交代 1964 烏克蘭原文與 Li–Yorke 的關係；後者是馬蹄映射的正式定義與符號動力學。本書「誠實標示不展開」的嚴格版在這裡。（ch09／ch16）

### 教科書與深入教材

- **Steven Strogatz,《Nonlinear Dynamics and Chaos》** — 本書反覆指向的標準教科書，工程師級嚴謹（每步有理由、不陷進測度論）。對照章節：第 5–8 章相平面與極限環（ch10）、第 9 章 Lorenz 方程（ch11）、第 10 章一維映射含不動點／2-cycle／Lyapunov／§10.6–10.7 重整化（ch06／ch07／ch08／ch09／ch14／ch16）。想把本書任一章的直覺升級成能算的版本，先翻它。
- **Kenneth Falconer,《Fractal Geometry: Mathematical Foundations and Applications》** — 想補本書 ch13 誠實標示「不展開」的 Hausdorff 維度測度定義、以及盒計數維度與 Hausdorff 維度何時相等，讀第 2–3 章即可，不必啃全書。（ch13）
- **Kantz & Schreiber,《Nonlinear Time Series Analysis》（劍橋大學出版，第 2 版 2004）** — 把 ch17「給直覺、不展開」的實作（嵌入維度怎麼選、延遲 τ 怎麼定、關聯維度與 Lyapunov 怎麼從資料估、怎麼避免被雜訊騙）講全的標準教科書。想真的動手做時讀這本。（ch17）

### 線上講義、科普與機構教材

- **3Blue1Brown,〈Differential equations, a tourist's guide〉（YouTube）** — 用動畫把單擺的 (θ, ω) 相空間、向量場、軌跡流動講得極直觀；看一遍勝過讀十頁文字，ch10 的三張 ASCII 相圖在那裡會動起來。（ch10）
- **J. C. Sprott,〈Lyapunov Exponent and Dimension of the Lorenz Attractor〉** — https://sprott.physics.wisc.edu/chaos/lorenzle.htm 勞侖次吸子那組 Lyapunov 指數（≈+0.906, 0, −14.572）與碎維度（Kaplan–Yorke ≈2.062、關聯維度 ≈2.055）的權威出處與算法。本書 landscape 的 Lorenz 數值即以它為準。（ch11／ch13／ch14）
- **ECMWF,〈Introduction to chaos, predictability and ensemble forecasts〉（線上教材）** — https://www.ecmwf.int/en/learning/training/introduction-chaos-predictability-and-ensemble-forecasts 把「混沌 → 為什麼要系集 → 怎麼從擾動初值估不確定性」一條線講清楚的官方教材。特別看它怎麼解釋「為什麼預報要給機率、不給單一數字」。（ch15，2026-06 可查）
- **NCAR/UCAR News,〈Turning the tables on chaos: Is the atmosphere more predictable than we assume?〉** — https://news.ucar.edu/4505/turning-tables-chaos-atmosphere-more-predictable-we-assume 用大眾語言把「5 天倍增、兩週、Zhang 的 15 天、孿生實驗 17/20 天」串起來的好讀版本。（ch15，2026-06 可查）
- **Shen, B.-W. et al.,〈Lorenz's View on the Predictability Limit of the Atmosphere〉（綜述）** — 把「兩週上限」「倍增時間 5 天」「勞侖次後期估計 3.5 天」的來歷與演進交代得最清楚的回顧，說明為什麼這些是量級、會抖、別寫死。researchgate／NOAA repository 可查。（ch15，2026-06）
- **〈Atmospheric Predictability Beyond 30 Days with Machine Learning〉（arXiv 2504.20238，後刊於 *AIES*）** — https://arxiv.org/abs/2504.20238 ch15「ML 正在重新評估上限、結論未定」那句的出處。讀它要帶著 hedge：它證明的是「能延伸技巧的初值存在」，不是「業務上能即時拿到」——存在性與可操作性是兩回事，當前沿風向、不當基準。（ch15，2026-06）
- **Mittag-Leffler Institute 官方競賽史（mittag-leffler.se 的 prize-competition 頁）** — 從期刊主編這一側看奧斯卡二世獎的召回事件，補足 Barrow-Green 之外的視角。（ch02）
- **John D. Cook,〈Cobweb plots〉（2020）** — https://www.johndcook.com/blog/2020/01/19/cobweb-plots/ 蛛網圖的乾淨入門，圖配得好。看完 ch05 想多練幾個「垂直—水平」例子從這裡開始。（ch05）
- **〈The Logistic Map: a Simple Model with Rich Dynamics〉，ThatsMaths（2023）** — https://thatsmaths.com/2023/11/09/the-logistic-map-a-simple-model-with-rich-dynamics/ 從人口模型講到混沌的科普導覽，把 ch05–09 的全劇情用一篇串過，適合「先看全景再讀細節」的暖身。（ch05）
- **MacTutor,〈Pierre Verhulst (1804–1849)〉** — https://mathshistory.st-andrews.ac.uk/Biographies/Verhulst/ 連續版邏輯斯諦方程提出者的小傳；想知道這條式子在變成混沌招牌之前本來拿來幹嘛（1838 修正 Malthus 無限成長），讀這篇。（ch05）
- **plus.maths.org,〈How to compute the dimension of a fractal〉** — 用 Koch、Sierpiński 一步步示範 D = ln N / ln(1/s) 與盒計數的科普文章，圖文清楚。想找比 ch13 更多範例練手，把 N 與 s 多代幾個碎形熟悉公式。（ch13，線上免費）

### 原典（直接讀作者的話）

- **拉普拉斯《機率的哲學試論》（A Philosophical Essay on Probabilities, 1814）導論。** 惡魔那段就在最前面幾頁，英譯本網路上找得到（如 archive.org）。直接讀拉普拉斯怎麼用「intelligence」而非「demon」，親眼確認那層命名漂移；也會發現惡魔的設定本身就把「決定論」與「可預測」黏在一起（同時假設唯一演化＋無限算力＋完美初值）。（ch01／ch04）

---

讀完 ch19 想再往哪走，就回這份清單：哲學上的疑問走 SEP 兩條，史實考據走 Barrow-Green 與各篇奠基論文，想動手算走 Strogatz、Falconer、Kantz–Schreiber。本書到「為什麼美、為什麼反直覺」為止；要把欣賞升級成操作，運算深度指向書架上那三本相鄰書。
