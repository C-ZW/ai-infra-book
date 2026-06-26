# Landscape — 三角函數書事實基準（2026-06）
> 內部文件，非書籍內容。歷史／歸屬／名稱／常誤傳數學事實的查證基準。各章必須以此為錨；本檔沒有的，撰章時自行查證並 hedge。重大修正需兩個獨立來源。
> 與姊妹書《馴服無限》（微積分）重疊處（Euler、Fourier、方波 1.10347）必須一致。

---

- **基準日期**：2026-06（全部條目於 2026-06-13 以網路查證或本檔自行複核）。
- **使用規則**：各章引用本檔列出的事實時，**以本檔表述為準**，不得引用記憶中的「常見說法」。標注 ⚠️ 的條目未能完全確認，章節引用時必須帶保留語氣或註明「傳說／待考」。重大修正（推翻本檔既有表述）需兩個獨立來源，並於 maintenance 掃描日誌記一行。
- **與姊妹書（calculus）一致性錨點**：Euler 公式系統表述 1748《Introductio》、Cotes 1714 對數先聲；Fourier 1807 提交、1822 出版；Gibbs overshoot 以「整個跳躍幅度的 8.95%」表述（非半跳躍 17.9%）；方波三項部分和於 x=π/2 = 52/(15π) ≈ **1.10347**。

---

## 1. 三角學的起源與名稱

### 1.1 弦表（chord tables）：Hipparchus → Ptolemy
- **事實**：已知最早的弦表由希臘天文學家 **Hipparchus（喜帕恰斯，約西元前 190–120）約於西元前 150–140 年**製作；該表已佚失（原為 12 卷論著，被後來更完整的《Almagest》取代）。據稱以每 7.5° 為間距列出弦長。**Ptolemy（托勒密，約西元 2 世紀）** 在《Almagest》（天文學大成）第一卷第 11 章給出更完整的弦表，角度自 0.5° 到 180°、間距 0.5°，半徑取 60（六十進位）。托勒密的弦表大量奠基於 Hipparchus 的觀測與成果。
- **要點**：早期三角學的基本量不是 sine，而是**圓上一段弧所對的「弦」（chord）**——chord(θ) 與現代 sine 的關係是 chord(θ) = 2·sin(θ/2)。這正是本書「三角是旋轉／圓的語言」論點的史實根：起點就是圓，不是直角三角形。
- **來源**：https://mathshistory.st-andrews.ac.uk/Biographies/Hipparchus/ ；https://en.wikipedia.org/wiki/Ptolemy%27s_table_of_chords
- **判定**：確認。Hipparchus 年份坊間有「約前 150」「約前 140」兩說，書中寫「約西元前 150 年」並註「±」最穩。

### 1.2 從弦到正弦（chord → sine）：印度的轉換
- **事實**：以「半弦」（half-chord，對應現代 sine）取代整條弦，是印度數學的關鍵轉換。**Aryabhata（阿耶波多，476–550）** 在《Aryabhatiya》（成書 499 CE）中列出史上第一張正弦表（嚴格說是 R·sin 值表），以 3.75°（225 分）為間距、半徑 R = 3438，並用差分遞迴法計算後續值（已具有限差分的雛形）。
- **來源**：https://en.wikipedia.org/wiki/%C4%80ryabha%E1%B9%ADa%27s_sine_table
- **判定**：確認。「史上第一張正弦表」為標準歸屬。

### 1.3 「sine」一字的語源鏈（jyā → jiba → jaib → sinus）
- **事實**：這條著名語源鏈經查證如下——
  1. 梵文 **jyā / jīvā**，本義「弓弦（bowstring）」，被印度數學家用來指半弦（即 sine）。
  2. 阿拉伯人音譯為 **jiba**；依阿拉伯文省略母音的習慣，僅寫子音 **jb**（jyb）。
  3. 後來的讀者把無母音的 jb 讀成 **jaib（jayb）**——這是一個有意義的阿拉伯文真詞，意為「灣／衣襟的褶／胸懷（bay / fold / bosom）」。
  4. 12 世紀拉丁譯者（Gherardo of Cremona／另說 Robert of Chester）將 jaib 意譯為拉丁文 **sinus**（意同「灣／褶／胸懷」）——現代 sine 即源於此。
- **細緻化（引用時注意）**：這條鏈「常被garbled（講岔）」。最穩的版本是：**jiba 是純音譯、本身在阿拉伯文無義；jaib 是後人因無母音而誤讀出的真詞；sinus 是對 jaib 的拉丁意譯。** 不要說「阿拉伯人把 sine 叫做『胸懷』」——是歐洲／後世的誤讀，再被忠實意譯成拉丁文。誤讀者究竟是阿拉伯人本身或歐洲譯者，史料說法不一（兩說並存），書中宜寫「在傳抄中被讀成 jaib」而不指名誰錯。
- **來源**：https://www.etymonline.com/word/sine ；https://en.wikipedia.org/wiki/Jy%C4%81,_koti-jy%C4%81_and_utkrama-jy%C4%81 ；https://www.themathdoctors.org/trig-terminology-what-do-those-words-mean/
- **判定**：確認（附「誤讀者不指名」的 hedge）。

### 1.4 tangent 與 secant 的語源（圓上的線段）
- **事實**：**tangent** 源自拉丁文 **tangere「觸碰」**（tangens 為其現在分詞）——對應**切線**，與圓只相切於一點。**secant** 源自拉丁文 **secare「切割」**（secans 為其現在分詞）——對應**割線**，穿過圓割出兩點。在單位圓圖上，tan θ、sec θ 確實就是切線、割線上的對應線段長度（cosecant、cotangent 同理為「餘」版本）。
- **要點**：這呼應全書論點——六個三角函數原本都是**圓上的幾何線段**，而非「三角形的邊比」。
- **來源**：https://www.themathdoctors.org/trig-terminology-what-do-those-words-mean/
- **判定**：確認。

### 1.5 「trigonometry」一詞的鑄造：Pitiscus, 1595
- **事實**：「trigonometry」一字由德國數學家／天文學家／神學家 **Bartholomäus Pitiscus（1561–1613）** 鑄造，首見於其著作書名《Trigonometria: sive de solutione triangulorum tractatus brevis et perspicuus》，**1595 年於海德堡（Heidelberg）首版**。該詞由希臘文 trigōnon（三角形）＋ metron（度量）組成。英譯（1614）與法譯（1619）使該詞傳入英、法語。
- **來源**：https://mathshistory.st-andrews.ac.uk/Biographies/Pitiscus/ ；https://en.wikipedia.org/wiki/Bartholomaeus_Pitiscus
- **判定**：確認。注意：Pitiscus 卒年兩說（7/2 或 8/24 1613），書中不需引用卒日。

### 1.6 印度貢獻：Madhava 的冪級數（約 1400）
- **事實**：**Madhava of Sangamagrama（桑加馬格拉馬的馬德哈瓦，約 1340–1425）**，Kerala 學派創始人，已知（或歸於其學派）的成果包含 sin 與 cos 的冪級數展開：sin x = x − x³/3! + x⁵/5! − …、cos x = 1 − x²/2! + x⁴/4! − …，以及 π/4 = 1 − 1/3 + 1/5 − …（今稱 **Madhava–Leibniz / Madhava–Gregory 級數**），早於歐洲（Gregory、Newton、Leibniz）約兩百年。
- **保留態度（與姊妹書一致）**：Madhava 本人著作多已佚失，成果經後世 Kerala 學者（Nilakantha《Tantrasangraha》、Jyesthadeva《Yukti-Bhasa》約 1550）轉述。歸屬須註明「經後世學派文本轉述」。主流視之為**獨立先驅**，無傳入歐洲之證據。
- **來源**：https://en.wikipedia.org/wiki/Madhava%27s_sine_table ；https://mathshistory.st-andrews.ac.uk/Biographies/Madhava/
- **判定**：確認（附「經學派文本轉述」的歸屬 hedge）。

### 1.7 伊斯蘭黃金時代：al-Battani、Abu al-Wafa、六函數與球面三角
- **事實**：伊斯蘭數學家把六個三角函數（sin、cos、tan 及其倒數 sec、csc、cot）首次系統化整理。**Abu al-Wafa al-Buzjani（阿布·瓦法，940–998）** 引入了 **secant 與 cosecant**、專門研究 tangent，並系統化六條三角線之間的關係；編製 15 分間距的 sine、tangent 表；在**球面三角**有重要創新。**al-Battani（巴塔尼，約 858–929）** 是三角學最有影響力的人物之一，其《Kitāb az-Zīj》影響了後人。
- **來源**：https://en.wikipedia.org/wiki/Abu_al-Wafa%27_al-Buzjani ；https://en.wikipedia.org/wiki/Al-Battani
- **判定**：確認。⚠️ 個別「誰最先引入哪一個函數」的精確優先權在不同來源略有出入，書中宜以「伊斯蘭數學家系統化六函數、Abu al-Wafa 引入 sec/csc」概括，不在單一人名上釘太死。

---

## 2. 弧度（radian）：概念 vs 名稱

- **事實**：**「radian」這個「名稱」由工程師 James Thomson（Lord Kelvin 之兄）鑄造**，首次見於印刷品是 **1873 年 6 月 5 日**他在貝爾法斯特 Queen's College 出的考卷上。他早在 1871 年已使用此詞。（旁證：1869 年 Thomas Muir 在 rad / radial / radian 之間猶疑，1874 年與 James Thomson 商議後採用 radian。）
- **概念更早**：弧度「概念」（以弧長與半徑之比作為角的自然度量）通常歸於 **Roger Cotes（柯茨，1714 年左右）**——他「除了名字之外把弧度的一切都描述了」，並認識到它作為角度單位的自然性。
- **要點**：本書的「旋轉語言」論點需要弧度（讓 e^{iθ} 與 sin x 的導數乾淨），這裡正可講「概念與命名相隔約 160 年」的故事。
- **來源**：https://en.wikipedia.org/wiki/James_Thomson_(engineer) ；https://en.wikipedia.org/wiki/Roger_Cotes ；https://www.scientificlib.com/en/Mathematics/LX/Radian.html
- **判定**：確認。

---

## 3. 複數、旋轉與 Euler

### 3.1 de Moivre 定理（棣美弗）
- **事實**：(cos θ + i sin θ)ⁿ = cos nθ + i sin nθ，歸於 **Abraham de Moivre（棣美弗，1667–1754）**。de Moivre 在 **1707** 年的論文中已使用相關結果、**1722** 年再度表述；其現代閉式形式常透過 **Euler** 的記法定型（de Moivre 本人未寫成今日的緊湊形式）。
- **來源**：https://en.wikipedia.org/wiki/De_Moivre%27s_formula
- **判定**：確認（附「現代形式經 Euler 定型」的細緻化）。⚠️ de Moivre 1707/1722 的「精確內容歸屬」在科普來源中常被簡化，書中宜寫「de Moivre 在 1700 年代初期得到此結果，現代寫法經 Euler 定型」。

### 3.2 Cotes 的對數先聲（1714）
- **事實**：**Roger Cotes 於 1714 年**給出等價於 Euler 公式的**對數形式**：ix = ln(cos x + i sin x)（即 log(cos x + i sin x) = ix）。這比 Euler 的指數形式早，但 Cotes 未寫成指數式、也未充分展開其意義。
- **與姊妹書一致**：calculus 書 landscape 第 14 條已記「等價對數形式更早見於 Roger Cotes（1714）」。
- **來源**：https://en.wikipedia.org/wiki/Roger_Cotes ；https://en.wikipedia.org/wiki/Euler%27s_formula
- **判定**：確認。

### 3.3 Euler 公式與 Euler 恆等式
- **事實**：**e^{ix} = cos x + i sin x** 的系統性表述出自 **Euler（歐拉）《Introductio in analysin infinitorum》（1748，兩卷）** 第 8 章；Euler 亦在 1740 年左右的文章中觸及。代入 x = π 得 **Euler 恆等式 e^{iπ} + 1 = 0**（連結 e、i、π、1、0 五個常數）。
- **與姊妹書一致**：calculus 書記「Euler 公式系統性表述出自《Introductio》（1748）；Euler 的貢獻是指數形式與系統運用」——本書沿用。
- **要點**：這是全書的樞紐——「e^{iθ} 就是『以單位速率在單位圓上旋轉』」是 ch（複數→旋轉）的核心隱喻。
- **來源**：https://en.wikipedia.org/wiki/Euler%27s_formula ；https://mathshistory.st-andrews.ac.uk/（Euler 傳記）
- **判定**：確認。

### 3.4 複數平面（Wessel / Argand / Gauss）
- **事實**：複數的幾何表示（複數平面）由三人各自獨立提出——
  - **Caspar Wessel（韋塞爾，挪威-丹麥測量師）：1799 年**發表論文首次給出複數的幾何詮釋（1797 年向丹麥科學院宣讀）；但其論文長期被埋沒，直到 1895 年才被重新注意。
  - **Jean-Robert Argand（阿爾岡，1768–1822）：1806 年**私下出版《Essai…》，提出同一想法（故複數平面又稱 **Argand 圖**）；1813 年於《Annales de Mathématiques》重刊。
  - **Carl Friedrich Gauss（高斯）：1831 年**獨立引入並使之主流化。
- **細緻化**：Argand 常被誤稱「瑞士數學家」，他其實是住巴黎、經營書店的自學者；「Argand 圖」之名其實 Wessel 更早做出。
- **來源**：https://mathshistory.st-andrews.ac.uk/Biographies/Wessel/ ；https://mathshistory.st-andrews.ac.uk/Biographies/Argand/ ；https://en.wikipedia.org/wiki/Complex_plane
- **判定**：確認。

---

## 4. 波、傅立葉、Lissajous

### 4.1 Fourier
- **事實**：**Fourier 於 1807 年 12 月 21 日**向法蘭西科學院提交熱傳導備忘錄《Mémoire sur la propagation de la chaleur…》；**Lagrange 反對**（主因是三角級數的處理方式），論文未獲出版。1811 年得獎稿仍被批不夠嚴格。**1822 年**（Lagrange 已歿）出版《Théorie analytique de la chaleur》（熱的解析理論）。
- **與姊妹書一致**：calculus 書 landscape 第 16 條表述相同，本書沿用 1807／1822 兩個年份。
- **來源**：https://en.wikipedia.org/wiki/Joseph_Fourier
- **判定**：確認。

### 4.2 Lissajous 圖形
- **事實**：Lissajous 圖形（兩個互相垂直的正弦運動疊合而成的曲線）最早由 **Nathaniel Bowditch（鮑迪奇，美國）於 1815 年**研究（故又稱 **Bowditch 曲線**）；其後由 **Jules Antoine Lissajous（利薩茹，1822–1880）於 1857 年**更詳細地研究（以光學鏡面演示）。
- **要點**：絕佳的「兩個週期運動疊加 → 圖形」教具，呼應週期性主題。
- **來源**：https://en.wikipedia.org/wiki/Lissajous_curve ；https://mathshistory.st-andrews.ac.uk/Biographies/Lissajous/
- **判定**：確認。

### 4.3 Gibbs 現象（過衝精確常數）
- **事實**：在跳躍不連續處，傅立葉部分和會**過衝（overshoot）**。精確常數：以方波半跳躍（即從 0 到峰值）計，部分和峰值收斂到 **(2/π)·Si(π) = 1.17897974447…**（Si 為正弦積分）；超出量相對於**整個跳躍幅度**為 **0.089489872236… ≈ 8.95%**。相關的 Wilbraham–Gibbs 常數 ∫₀^π (sin t)/t dt = **1.851937051982…**。本檔自行複核（數值積分）：Si(π) ≈ 1.851938、(2/π)Si(π) ≈ 1.178980、相對半跳躍超出 ≈ 0.17898 → 相對整個跳躍 ≈ 0.089490 ✓。
- **與姊妹書一致（重要）**：calculus 書一律以「**跳躍幅度的 8.95%**」表述（若誤以半跳躍為分母會變 17.9%，坊間兩種寫法混用）。**本書必須採同一表述：8.95% of the jump。**
- **來源**：https://en.wikipedia.org/wiki/Gibbs_phenomenon
- **判定**：確認。

---

## 5. 雙曲函數

### 5.1 sinh / cosh 的歷史
- **事實**：雙曲函數由 **Vincenzo Riccati（文森佐·里卡蒂，1707–1775）** 於 **1757 年左右**正式引入（著作《Opusculorum…》1757–1762，部分與 Saladini 合作），他以 Sh./Ch. 表雙曲正弦／餘弦、Sc./Cc. 表圓函數，並導出加法公式、導數及與指數函數的關係。**Johann Heinrich Lambert（蘭伯特）於 1768/1770 年**進一步推廣；今日通用的記法 **sinh、cosh** 出自 Lambert。
- **細緻化**：常被簡化為「Lambert 發明雙曲函數」，其實 Riccati 更早；Lambert 的貢獻是記法與推廣。
- **來源**：https://mathshistory.st-andrews.ac.uk/Biographies/Riccati_Vincenzo/ ；https://en.wikipedia.org/wiki/Vincenzo_Riccati
- **判定**：確認。

### 5.2 懸鏈線（catenary）是 cosh，不是拋物線
- **事實**：自由懸掛的鏈條曲線（catenary，懸鏈線）的形狀是 **cosh（雙曲餘弦）**，**不是拋物線**。**Galileo（伽利略）曾錯誤猜測是拋物線**。**Jacob Bernoulli（雅各布·伯努利）於 1690 年**公開徵解；**Johann Bernoulli、Leibniz、Huygens 三人各自獨立解出，三份解皆於 1691 年**（《Acta Eruditorum》）發表。Huygens 於 1690 年命名 catenaria（源自拉丁文 catena「鏈」）。
- **要點**：懸鏈線是「雙曲函數有真實物理身世」的好例子，與圓函數（旋轉）對照。
- **來源**：https://www.bshm.ac.uk/scientific-challenges-and-encryption-discoveries-17th-century-rational-mechanics ；https://en.wikipedia.org/wiki/Catenary
- **判定**：確認。⚠️ 「Galileo 主張拋物線」一說廣為流傳但帶 hedge：部分學者指出 Galileo 的原文較含糊（他知道那不完全是拋物線、只是近似），書中宜寫「Galileo 曾以為（或近似為）拋物線」而非斬釘截鐵。

---

## 6. 工程裡的三角

### 6.1 CORDIC 演算法
- **事實**：**CORDIC（COordinate Rotation DIgital Computer）由 Jack E. Volder 於 1956 年構思**（在 Convair 航電部門），目的是用更快更準的即時數位方案取代 **B-58 Hustler 轟炸機**導航計算機中的類比解算器。演算法只用加法與移位（不需乘法器），透過一系列固定角度的「旋轉」逼近三角函數。Volder 於 **1959 年**在 Western Joint Computer Conference 論文集首次公開發表。
- **細緻化（年份）**：構思／內部報告是 **1956**，公開發表是 **1959**。題目可寫「1959 年公開」，但若強調「為 B-58 而生」則背景在 1956。書中兩個年份都提最穩。
- **要點**：CORDIC 把 sin/cos 計算還原成「一連串小旋轉」，是「三角＝旋轉」論點在工程上的完美印證。
- **來源**：https://en.wikipedia.org/wiki/CORDIC ；https://en.wikipedia.org/wiki/Jack_E._Volder
- **判定**：確認。

### 6.2 atan2
- **事實**：`atan2(y, x)` 是雙參數反正切，相對單參數 atan 能解析出完整四象限的角度（並正確處理 x=0）。它**起源於 Fortran 程式語言**的數學內建函式，後為 C 等語言沿用，成為事實標準。引數順序慣例為 **atan2(y, x)**（y 在前）。
- **來源**：https://en.wikipedia.org/wiki/Atan2
- **判定**：⚠️ 「起源於 Fortran」是廣為接受的說法（atan2 確實是 Fortran 早期數學函式庫的一員），但本檔未逐一查到「哪一版 Fortran 最早」的一手出處；書中宜寫「最早隨 Fortran 進入程式語言標準函式庫」並 hedge 確切版本。

---

## 7. 常被誤傳或需釘死的數學事實（基準數值，全書必須一致）

> 以下數值本檔已用 Python（math 模組）自行複核（2026-06-13），各章引用以此為準。

### 7.1 特殊角精確值
- sin 30° = 1/2，cos 30° = √3/2，tan 30° = 1/√3 = √3/3
- sin 45° = cos 45° = √2/2（= 1/√2），tan 45° = 1
- sin 60° = √3/2，cos 60° = 1/2，tan 60° = √3
- sin 0° = 0、sin 90° = 1、cos 0° = 1、cos 90° = 0
- **判定**：確認（恆等式，非經驗值）。

### 7.2 常數小數
- √2 ≈ **1.41421**（1.41421356…）
- √3 ≈ **1.73205**（1.73205081…）
- √2/2 ≈ **0.70711**，√3/2 ≈ **0.86603**
- π ≈ **3.14159**（3.14159265…）
- e ≈ **2.71828**（2.71828183…）
- **判定**：確認（本檔複核）。

### 7.3 小角度值（弧度，x = 0.1）
- sin(0.1) ≈ **0.0998334**
- cos(0.1) ≈ **0.9950042**
- tan(0.1) ≈ **0.1003347**
- **判定**：確認（本檔複核）。可用於「小角近似 sin x ≈ x、cos x ≈ 1 − x²/2」的對照。

### 7.4 極限（鋪墊導數）
- lim_{h→0} sin(h)/h = **1**
- lim_{h→0} (1 − cos h)/h = **0**
- lim_{h→0} (1 − cos h)/h² = **1/2**
- **判定**：確認（標準極限）。

### 7.5 單位根（roots of unity）
- 立方根：1、**−1/2 + (√3/2)i**、**−1/2 − (√3/2)i**，三者**和為 0**（本檔複核：sum = 0）。
- 一般：n ≥ 2 時，n 個 n 次單位根之和為 **0**（幾何級數 / 正多邊形頂點向量和）。
- **判定**：確認。

### 7.6 方波傅立葉級數（跨書錨點）
- 方波（振幅 1，即在 +1 與 −1 之間，奇函數展開）= **(4/π)(sin x + sin 3x/3 + sin 5x/5 + …)**。
- 在 x = π/2 的**三項部分和** = (4/π)(1 − 1/3 + 1/5) = (4/π)(13/15) = **52/(15π) ≈ 1.10347**（本檔複核：1.10347427… ✓，三種寫法 (4/π)(1−1/3+1/5)、(4/π)(13/15)、52/(15π) 數值一致）。
- ⚠️ **跨書錨點（重要）**：姊妹書《馴服無限》（微積分）將此值釘在 **1.10347**（該書於 2026-06-12 修正過早先的錯誤值 1.0383）。**本書必須採同一值 1.10347；任何章節若算出別的數，先懷疑自己算錯，再對照本條。**
- **判定**：確認（本檔複核 52/(15π) = 1.1034742721…）。

### 7.7 相位合成（A sin x + B cos x）
- **A·sin x + B·cos x = √(A²+B²)·sin(x + φ)，其中 φ = atan2(B, A)。**
- **判定**：確認（本檔複核：以 A=3, B=4 隨機取點驗證，R=5、φ=atan2(4,3)≈0.9273，恆等式成立 ✓）。**相位慣例釘死為 φ = atan2(B, A)**（B 對應 cos 係數、A 對應 sin 係數，順序勿顛倒）；另一常見等價寫法是寫成 R·cos(x − ψ)，但本書統一採 sin 形式以保持一致。

### 7.8 畢氏／雙曲恆等式
- **sin²θ + cos²θ = 1**（圓的方程 x²+y²=1 在單位圓上的直接後果）。
- **cosh²t − sinh²t = 1**（雙曲線 x²−y²=1）。
- **判定**：確認（定義級恆等式）。對照：圓函數參數化單位圓、雙曲函數參數化單位雙曲線——是全書「圓 vs 雙曲」對照的代數骨架。

---

## 8. 延伸閱讀候選（已驗證連結真實存在）

### 影片（3Blue1Brown）
- **「But what is a Fourier series? From heat flow to circle drawings」**（DE 系列；2019-06-30；25 分；正是「epicycle / 用旋轉的圓畫圖」那支）—— 官網 https://www.3blue1brown.com/lessons/fourier-series/ ；YouTube https://www.youtube.com/watch?v=r6sGWTCMz2k 。**確認存在。**
- **「Complex number fundamentals | Lockdown math ep. 3」**（2020-04-24）—— https://www.3blue1brown.com/lessons/ldm-complex-numbers/ ；YouTube https://www.youtube.com/watch?v=5PcpBw5Hbwo 。**確認存在。**
- **「Trigonometry fundamentals | Lockdown math ep. 2」**（複數那集的前一集，含「世界最有名的三角恆等式」推導）—— Lockdown Math 系列頁 https://www.3blue1brown.com/topics/lockdown-math 。**確認系列存在。**
- ⚠️ **「Essence of trigonometry」並不存在**：3Blue1Brown 的「Essence of …」系列只有 Calculus 與 Linear Algebra；三角的內容散落在 Lockdown Math（ep. 2/3）與 Fourier 影片中。引用時不要寫「Essence of trigonometry」。

### 書
- **Tristan Needham《Visual Complex Analysis》**（OUP；有 2023 年 25 週年紀念版）—— https://global.oup.com/academic/product/visual-complex-analysis-9780192868923 。**確認存在。**（全書以「複數＝旋轉與縮放」的視覺進路，與本書論點高度同調。）
- **Eli Maor《Trigonometric Delights》**（Princeton；Princeton Science Library 版 ISBN 9780691202198）—— https://www.amazon.com/Trigonometric-Delights-Princeton-Science-Library/dp/0691202192 。**確認存在。**
- **Eli Maor《e: The Story of a Number》**（Princeton）—— 作者頁／書目確認其著作含本書。**確認存在。**⚠️ 直接官方產品頁未逐一抓取，引用 ISBN 前可再快查一次。

### 網站文章（Better Explained）
- **「Intuitive Understanding Of Euler's Formula」** —— https://betterexplained.com/articles/intuitive-understanding-of-eulers-formula/ 。**確認存在。**（「e^{iθ}＝在圓上旋轉」的直覺講法，與本書 ch（複數→旋轉）對齊。）
- **「Easy Trig Identities With Euler's Formula」** —— https://betterexplained.com/articles/easy-trig-identities-with-eulers-formula/ 。**確認存在。**
- **Better Explained 三角主題索引頁** —— https://betterexplained.com/articles/series/math-trigonometry/ 。**確認存在。**

### Steven Strogatz
- ⚠️ Strogatz 著有《Infinite Powers》《The Joy of x》及 NYT 數學專欄，**書本身存在**，但本檔**未直接查到「專講三角／週期」的單篇文章 URL**。引用時宜寫「Strogatz 的科普寫作（如《The Joy of x》、NYT 專欄）對週期與振盪有平易近人的討論」並 hedge，或撰章時再補查具體篇目。

---

## 待確認 / 低信心清單（⚠️ 撰章時必須 hedge）

1. **sine 語源「誰誤讀出 jaib」**（1.3）：阿拉伯人本身或歐洲譯者，史料兩說並存——寫「在傳抄中被讀成 jaib」、不指名誰錯。
2. **伊斯蘭六函數的個別優先權**（1.7）：「誰最先引入哪一個函數」各來源略有出入——以「系統化六函數、Abu al-Wafa 引入 sec/csc」概括，勿在單一人名釘死。
3. **de Moivre 1707/1722 的精確內容歸屬**（3.1）：科普來源常簡化——寫「1700 年代初期得到、現代形式經 Euler 定型」。
4. **Galileo「主張懸鏈線是拋物線」**（5.2）：流傳廣但原文較含糊（他知道只是近似）——寫「曾以為（或近似為）拋物線」。
5. **atan2「起源於 Fortran」**（6.2）：廣為接受但本檔未查到「哪一版 Fortran 最早」一手出處——hedge 確切版本。
6. **CORDIC 年份**（6.1）：構思 1956、公開 1959，兩年份並存——勿只寫單一年份而忽略另一個語境。
7. **3Blue1Brown「Essence of trigonometry」不存在**（§8）：勿引用此不存在的標題；三角內容在 Lockdown Math ep. 2/3 與 Fourier 影片。
8. **Eli Maor《e: The Story of a Number》官方產品頁 / ISBN**（§8）：書確定存在，但官方頁未逐一抓取，引用精確 ISBN 前再快查一次。
9. **Steven Strogatz 三角／週期專篇 URL**（§8）：書與專欄存在，但無單篇確切連結——撰章時再補查或泛指。
