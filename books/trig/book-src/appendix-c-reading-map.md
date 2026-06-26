# 附錄 C — 延伸閱讀總地圖

這份地圖把全書十五章用過的延伸閱讀，依「你讀完這本書之後想往哪走」重新排成三條路線：**往複變與幾何**、**往訊號與傅立葉**、**往欣賞與數學史**。它不是參考書目堆疊，而是一張「下一步該看誰」的決策圖。

挑選原則照全書一貫的誠實標準：

- 以 `landscape-2026-06` 第 8 節**逐一驗證過確切網址**的資源為核心（影片、書、Better Explained 文章），這些標「（2026-06 確認存在）」。
- 章節實際引用、且連結可查的學術／工具頁（MacTutor、Wikipedia、課程講義等）一併收入，但這些**未在 landscape 逐一抓取確切網址**，統一標「（2026-06，未逐一驗證確切網址）」。引用前請自己再點一次。
- **3Blue1Brown 沒有「Essence of trigonometry」這個系列**——這是全書反覆提醒、最常被誤傳的幻影標題。它的三角內容散在 **Lockdown Math ep. 2（Trigonometry fundamentals）／ep. 3（Complex numbers）** 與那支 **Fourier series（畫圓）影片**裡。本地圖只引用這些真實存在的條目，絕不寫「Essence of trigonometry」。
- 姊妹書《馴服無限：微積分的直覺與驚嘆》在重疊主題（Euler 級數那側、Fourier 收斂那側）一律明說分工：本書管「為什麼正弦是對的基底／旋轉這側」，那本管「收斂與嚴格化」。互為鏡像，可引用、不依賴。

---

## 如果只看三樣

讀完本書、時間有限，這三樣最對得起「三角是旋轉與週期的語言」這條主軸：

1. **3Blue1Brown,「But what is a Fourier series? From heat flow to circle drawings」**（影片，約 25 分）——全書最後一格（ch13 epicycles）的動畫聖經。看「一堆首尾相接的旋轉箭頭畫出任意曲線」那段，本書「波＝旋轉的圓疊起來」會從文字變成肉眼直覺。官網 https://www.3blue1brown.com/lessons/fourier-series/ ；YouTube https://www.youtube.com/watch?v=r6sGWTCMz2k （2026-06 確認存在）
2. **Tristan Needham,《Visual Complex Analysis》**（書）——把「複數＝旋轉與縮放」推到整個複變分析，與本書 ch05→ch09 那條旋轉骨幹高度同調。先讀第 1 章 "Geometry and Complex Arithmetic"。https://global.oup.com/academic/product/visual-complex-analysis-9780192868923 （2026-06 確認存在）
3. **Eli Maor,《Trigonometric Delights》**（書）——把三角當「值得欣賞的東西」而非考試工具來寫的科普經典，史與數交織，氣質和本書最近。讀 sine 的身世與弦表那幾章。https://www.amazon.com/Trigonometric-Delights-Princeton-Science-Library/dp/0691202192 （2026-06 確認存在）

一句話：一支影片把「圓→波」演給你看、一本書把「複數＝旋轉」推到極致、一本書把這一切的歷史與品味補齊。

---

## 路線一 — 往複變與幾何

把本書 Part II（旋轉是母題）與 Part III（複數＝旋轉的代數）往下接：旋轉矩陣 → 複數乘法 → Euler → 單位根，再往複變函數論與更高維旋轉走。

- **Tristan Needham,《Visual Complex Analysis》**（OUP，有 2023 年 25 週年紀念版）——這條路線的主幹。整本書的開場進路就是「複數＝旋轉與縮放」，視覺密度遠超一般教科書。本書 ch05（旋轉矩陣）、ch07（複數乘法）、ch08（Euler）、ch09（單位根）、ch11（`d/dθ e^{iθ}=i·e^{iθ}` 是速度永遠垂直半徑）都在這本裡接得上；想把 ch08「`e^{iθ}` 是旋轉」推到複變並補上本書誠實標為「不證」的嚴格層幾何版，這是首選。https://global.oup.com/academic/product/visual-complex-analysis-9780192868923 （2026-06 確認存在）
- **3Blue1Brown,「Complex number fundamentals | Lockdown math ep. 3」**（2020-04-24）——把「複數乘法＝旋轉＋縮放」「`e^{iθ}` 繞圈」用動畫講到骨子裡，是 ch07/ch08/ch09 旋轉直覺的影像版。看「乘以 i 這支箭頭怎麼轉起來」。https://www.3blue1brown.com/lessons/ldm-complex-numbers/ （2026-06 確認存在）
- **3Blue1Brown,「Trigonometry fundamentals | Lockdown math ep. 2」**——含「世界最有名的三角恆等式」（和角公式）的視覺推導，對應本書 ch01/ch03/ch04 的單位圓與幾何進路。系列頁 https://www.3blue1brown.com/topics/lockdown-math 。（再次提醒：沒有「Essence of trigonometry」，三角內容就在 Lockdown Math 與 Fourier 影片裡。2026-06 確認系列存在）
- **3Blue1Brown, Essence of Linear Algebra**（「Linear transformations and matrices」、「Dot products and duality」兩集）——ch05 旋轉矩陣（矩陣＝基底向量的去向）與 ch06 點積即投影的動畫地基。https://www.3blue1brown.com/topics/linear-algebra （2026-06 確認系列存在）
- **Better Explained,「Intuitive Understanding Of Euler's Formula」**——把 `e^{iθ}` 講成「在圓上連續旋轉」，和本書 ch07→ch08 旋轉這側完全同調，是進 ch08 前的最佳暖身。https://betterexplained.com/articles/intuitive-understanding-of-eulers-formula/ （2026-06 確認存在）
- **Wikipedia,「Euler's formula」/「Roger Cotes」**——想把 Cotes 1714 對數先聲、Euler 1748《Introductio》第 8 章的歷史歸屬釘清楚的乾淨入口（ch08 歷史段來源）。https://en.wikipedia.org/wiki/Euler%27s_formula （2026-06，未逐一驗證確切網址）
- **Wikipedia,「Complex plane」**——複數平面的歷史（Wessel 1799 先做卻被埋沒、Argand 1806 私印、Gauss 1831 使之主流）與正式定義，ch07 歷史段在此。https://en.wikipedia.org/wiki/Complex_plane （2026-06，未逐一驗證確切網址）
- **Wikipedia,「De Moivre's formula」/「Root of unity」**——de Moivre 的歷史歸屬（現代緊湊形式經 Euler 定型）與單位根的代數性質（分圓多項式、原根），ch09 的延伸。https://en.wikipedia.org/wiki/De_Moivre%27s_formula （2026-06，未逐一驗證確切網址）
- **Wikipedia,「Rotation matrix」/「Orthogonal group」**——想把 SO(2)、正交矩陣、det=±1 的群結構，以及往 3D（SO(3)）與更高維推廣釘清楚的入口（ch05 延伸）。https://en.wikipedia.org/wiki/Rotation_matrix （2026-06，未逐一驗證確切網址）
- **Wikipedia,「Ptolemy's theorem」** 與 **Cut-the-Knot,「Sine, Cosine, and Ptolemy's Theorem」**——想親眼看「和角公式＝托勒密定理的重新整理」怎麼從圓內接四邊形推出來（ch04 歷史旁證）。https://en.wikipedia.org/wiki/Ptolemy%27s_theorem ；https://www.cut-the-knot.org/proofs/sine_cosine.shtml （2026-06，未逐一驗證確切網址）
- **Keith Conrad,「Etymology of Trigonometric Function Names」**（UConn 講義 PDF）——學術地追六個函數名的由來與「它們本來是圓上線段」的幾何構造（ch03 詞源延伸）。https://kconrad.math.uconn.edu/math1131f19/handouts/trigfunctionnames.pdf （2026-06，未逐一驗證確切網址）
- **往 3D 與四元數走**：3Blue1Brown 與 Ben Eater 合作的「Visualizing quaternions」互動式講解（quaternions.online）——把 ch05 的「複合旋轉」推到 3D、看清四元數為什麼能避開萬向鎖。四元數的代數根就在 ch07 的複數乘法。（2026-06，未逐一驗證確切網址，建議查證）
- **姊妹書《馴服無限》ch09**——Euler 公式的另一個鏡頭：從 `eˣ` 的泰勒級數代 iθ 推出來，補上本書 ch08 刻意不碰的收斂與級數重排嚴格層。**同一定理的兩個鏡頭**，對照著讀最有收穫。

---

## 路線二 — 往訊號與傅立葉

把本書 Part IV（週期與波）往下接：波的解剖（相量）→ sin′=cos → 疊加與拍頻 → 傅立葉的門口，再往收斂的嚴格層、訊號處理工程與 FFT 走。

- **3Blue1Brown,「But what is a Fourier series? From heat flow to circle drawings」**（DE 系列；2019-06-30；約 25 分）——這條路線的主幹影片，正是「epicycle／用旋轉的圓畫圖」那支。ch10（單獨一支相量）、ch12（多個波疊加）、ch13（無限多支相量的合奏）整段都站在它上面。官網 https://www.3blue1brown.com/lessons/fourier-series/ ；YouTube https://www.youtube.com/watch?v=r6sGWTCMz2k （2026-06 確認存在）
- **Better Explained,「Intuitive Understanding Of Euler's Formula」**——把 `e^{iθ}` 講成「在圓上旋轉」，正是 ch10 相量 `A·e^{i(ω·t+φ)}` 的地基。讀完回頭看 ch10「相量」那節會更通透。https://betterexplained.com/articles/intuitive-understanding-of-eulers-formula/ （2026-06 確認存在）
- **Better Explained,「Easy Trig Identities With Euler's Formula」**——用 Euler／de Moivre 一招現推多倍角與積化和差，把本書「不必背恆等式」的姿態（ch08/ch09/ch12）再坐實一次。https://betterexplained.com/articles/easy-trig-identities-with-eulers-formula/ （2026-06 確認存在）
- **Wikipedia,「Phasor」**——工程視角的相量完整詞條：旋轉向量、複數振幅、為什麼微分變成乘 i·ω、AC 電路怎麼把微分方程變代數。ch10「為什麼工程上用相量」的工程細節在此。https://en.wikipedia.org/wiki/Phasor （2026-06，未逐一驗證確切網址）
- **Wikipedia,「Beat (acoustics)」** 與 **「Lissajous curve」**——拍頻＝|f₁−f₂|、包絡頻率 (f₁−f₂)/2 的「差兩倍」陷阱，以及各種頻率比／相位差的封閉條件與 Bowditch/Lissajous 史實（ch12 延伸）。https://en.wikipedia.org/wiki/Beat_(acoustics) ；https://en.wikipedia.org/wiki/Lissajous_curve （2026-06，未逐一驗證確切網址）
- **Test & Measurement Tips,「Lissajous patterns: using a scope for display signals」**——從工程量測角度看怎麼用示波器 XY 模式讀頻率比與相位差，配 ch12「示波器」那段。https://www.testandmeasurementtips.com/using-scope-display-lissajous-patterns/ （2026-06，未逐一驗證確切網址）
- **Gilbert Strang, MIT「Fourier Series」講義章節**——把正交性、係數＝投影、方波例子用工程師語言寫得最乾淨的免費教材之一；ch13「探測器＝投影」如何嚴謹展開，從這裡入手。https://math.mit.edu/~gs/cse/websections/cse41.pdf （2026-06，未逐一驗證確切網址）
- **MIT OCW,「Highlights of Calculus」— Derivatives of sin x and cos x（Gilbert Strang）**——Strang 從差商與小角極限把 `sin′=cos` 講得極清楚，補足 ch11「極限路」的嚴格細節（看他怎麼處理 `sin h/h`）。https://ocw.mit.edu/courses/res-18-005-highlights-of-calculus-spring-2010/ （2026-06，未逐一驗證確切網址）
- **Wikipedia,「Gibbs phenomenon」**——過衝常數（**整個跳躍幅度的 8.95%**、Wilbraham–Gibbs 常數）與「為什麼變窄不變矮」的最快入口；數值與歷史（Wilbraham 1848、Gibbs 1899）都在（ch13 延伸）。https://en.wikipedia.org/wiki/Gibbs_phenomenon （2026-06，未逐一驗證確切網址）
- **往 FFT 走**：ch09 的單位根就是 FFT 取樣探測器（twiddle factors）落腳的地方。把「離散傅立葉＝在單位根上做投影、O(N log N) 利用單位根對稱性加速」接起來後，可往訊號處理教材（如 Oppenheim《Discrete-Time Signal Processing》）走。（2026-06，未逐一驗證版次）
- **姊妹書《馴服無限》ch11**——本書 ch13 把「收斂與『等於』的嚴格意義」整個交給它：逐點收斂 vs 均方收斂、Dirichlet 條件、Gibbs 為什麼是 8.95%（牽涉正弦積分 Si(π)），以及 19 世紀「三角級數算不算函數」逼出實分析嚴格化的歷史危機。**本書管「為什麼正弦是對的基底」，那本管「無窮和到底等於什麼」**——兩本對照著讀最完整。
- **姊妹書《馴服無限》ch05（草圖）與 ch10（彈簧）**——ch05 只給 `sin′=cos` 的幾何草圖、明說沒證，本書 ch11 是它的正式補完；ch10 從微分方程那側講 `x″=−x` 的解，與本書 ch11「繞圓投影」互為表裡。

---

## 路線三 — 往欣賞與數學史

不為了再學一門技術，只想把「三角是怎麼長出來的」這件事看得更深、更有味道。對應本書交織全書的歷史暗線（弦表 → 印度正弦表 → 伊斯蘭六函數 → 詞源 → 弧度命名 → 複數平面 → 傅立葉 → 雙曲與懸鏈線）。

- **Eli Maor,《Trigonometric Delights》**（Princeton Science Library 版，ISBN 9780691202198）——這條路線的主幹。把三角當「值得欣賞的東西」來寫的科普經典，史與數交織，氣質和本書最近。sine 的身世與弦表（補 ch01）、tangent/secant 作為線段與詞源（補 ch03）、正弦波作為週期運動（補 ch10）都在裡面。https://www.amazon.com/Trigonometric-Delights-Princeton-Science-Library/dp/0691202192 （2026-06 確認存在）
- **Eli Maor,《e: The Story of a Number》**（Princeton）——把 e 的故事（也就是雙曲與 Euler 的母題，ch08/ch15）講成一本書，承接「往欣賞」這條路的後半。（2026-06 書確認存在；引用精確 ISBN 前可再快查一次）
- **MacTutor History of Mathematics**（mathshistory.st-andrews.ac.uk）——本書歷史查證的主要學術來源。重點條目：
  - 「Trigonometric functions」與 Hipparchus、Ptolemy、Aryabhata、Madhava 傳記——弦表 → 正弦表 → 級數的演化（ch01 歷史）。
  - 「Earliest Known Uses of …（R）」的 "radian" 條——James Thomson 1873、Thomas Muir 命名之爭的原始出處（ch02 歷史）。
  - 「Vincenzo Riccati」傳記——雙曲函數 1757 由里卡蒂引入（用 Sh./Ch. 記號），sinh/cosh 記號出自蘭伯特的推廣；釐清「蘭伯特發明雙曲函數」這個常見簡化（ch15 歷史）。
  （2026-06 查證為本書歷史錨；未逐一驗證每條傳記確切網址）
- **The Math Doctors,「Trig Terminology: What Do Those Words Mean?」**——把 sine（jyā→jiba→jaib→sinus 的誤讀詞源鏈）、tangent（tangere「觸」）、secant（secare「切」）講得最白話（ch03 詞源即以此與 landscape 對照）。記住詞源鏈的細緻版：jaib 是傳抄中因無母音被讀出的真詞，sinus 是對它的拉丁意譯，**不指名誰誤讀**。https://www.themathdoctors.org/trig-terminology-what-do-those-words-mean/ （2026-06 確認存在）
- **The Math Doctors,「Ranges of Inverse Trig Functions」** 與 **Math LibreTexts,「The functions of arcsin, arccos, and arctan」**——「為什麼三個主值分支這樣選、選別的會壞在哪」與主值分支圖的標準參考（ch14 延伸）。https://www.themathdoctors.org/ranges-of-inverse-trig-functions/ ；https://math.libretexts.org/Bookshelves/Precalculus/Precalculus_(Tradler_and_Carley)/19:_Inverse_Trigonometric_Functions （2026-06 確認存在）
- **Wikipedia,「CORDIC」**——「硬體怎麼用一連串小旋轉算 sin/cos/atan2」，是「三角＝旋轉」主題在矽晶片層的印證（Volder 1956 構想／1959 公開，為 B-58 轟炸機而生）。看 rotation mode 與 vectoring mode 兩節（ch14 延伸）。https://en.wikipedia.org/wiki/CORDIC （2026-06，未逐一驗證確切網址）
- **Wikipedia,「Catenary」**（懸鏈線）——伽利略曾以為（或近似為）拋物線的錯猜、伯努利 1690 徵解、惠更斯／萊布尼茲／約翰·伯努利 1691 各自解出的公案：「為什麼是 cosh 不是拋物線」（ch15）。https://en.wikipedia.org/wiki/Catenary （2026-06，未逐一驗證確切網址）
- **Wikipedia,「Rapidity」**（快度）——artanh(v/c) 讓相對論速度可加、Lorentz 變換寫成 cosh/sinh 就和旋轉矩陣同形。想看「雙曲版的旋轉疊加」（ch15 一句話帶過的 rapidity）從這裡進。https://en.wikipedia.org/wiki/Rapidity （2026-06，未逐一驗證確切網址）
- **Steven Strogatz 的科普寫作**（如《The Joy of x》、NYT 數學專欄）——對週期、振盪與三角的平易近人討論，氣質和「往欣賞」這條路相合。（2026-06：書與專欄存在，但無「專講三角／週期」的單篇確切連結，引用時宜泛指或自行補查篇目）

---

## 三條路線的交會點

三條路其實匯回同一個圓：**複變與幾何**告訴你旋轉的代數（複數、Euler、單位根），**訊號與傅立葉**告訴你週期是旋轉的影子在時間上的展開（相量、波、epicycles），**欣賞與數學史**告訴你這套語言是人類花了兩千年、從一張弦表一路長出來的。本書 ch15 的收官把這三條都標進了「下一步地圖」——你現在拿到的這份附錄，就是那張地圖的展開版。

往哪走都行；但別找「Essence of trigonometry」——它不存在。要 3Blue1Brown 的三角，去 Lockdown Math ep. 2／ep. 3 和那支畫圓的 Fourier 影片。
