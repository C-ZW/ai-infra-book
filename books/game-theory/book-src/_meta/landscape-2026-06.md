# 《當理性互相碰撞》— 事實基準表（landscape, 2026-06）

> 本檔是全書的**事實錨點**。每一章的歷史、人名、年份、報酬矩陣數值、定理條件都必須與此一致；要改任何基準值，先改這裡、再同步全書（依 outline 基準表 grep）、並在 maintenance.md 掃描日誌記一行（maintenance 在 P5 才產）。
> 規則：每條都帶「驗證值／一句註記／來源 URL」。無法以可信來源確認者標 ⚠️ 並說明原因。時效性敘述加註 (2026-06)。
> 信心分級：本書的事實多屬「數學恆真」（報酬矩陣、納許均衡計算、ESS 條件——不會過時）與「史實」（年份、歸屬、諾貝爾獎——已定案）。時效風險低；唯一需 hedge 的是「重複賽局實證／演化模擬的後續解讀」（Axelrod 結論被後人質疑的程度，見三、T5）與「行為賽局實驗的複現」（最後通牒賽局跨文化變異，見三、T7）。
> 本檔史實由 **2026-06-20 一輪帶網路研究**查證（12 組獨立檢索，全部命中一級／權威來源：NobelPrize.org、SEP、原始論文 DOI、Britannica、Nature/Annals 原文頁）。下標 ✅ 者表示已對權威來源核實。

---

## 一、歷史與人物（年份、歸屬、原話）

### 1. 賽局理論的奠基書：von Neumann & Morgenstern 1944 ✅
- **驗證值**：John von Neumann（馮紐曼）與 Oskar Morgenstern（摩根斯坦），《Theory of Games and Economic Behavior》（賽局理論與經濟行為），Princeton University Press，**1944 年**出版。第一版 xviii + 625 頁。此書創立賽局理論這個跨領域研究場域，並把它包裝成可用於經濟學的工具。
- **一句註記**：賽局理論的奠基文獻，但**不是**馮紐曼第一次寫賽局——那是 1928 的論文（見本節 2）。書中最大數學貢獻之一是 von Neumann–Morgenstern 期望效用公理（vNM utility，本套由《決策與理性》owner 寫透，本書只用「效用不是金額」結論、指向《決策》）。
- **來源**：https://en.wikipedia.org/wiki/Theory_of_Games_and_Economic_Behavior ；https://press.princeton.edu/books/paperback/9780691130613/theory-of-games-and-economic-behavior

### 2. 馮紐曼 1928：極小極大定理與零和賽局 ✅
- **驗證值**：von Neumann，「Zur Theorie der Gesellschaftsspiele」（論室內遊戲的理論／On the Theory of Parlor Games），《Mathematische Annalen》卷 **100**，頁 **295–320**，**1928 年**。首次證明兩人零和賽局的**極小極大定理（minimax theorem）**：在混合策略下，每個玩家都有一個策略，能保證自己拿到的報酬不低於某個值（賽局的「值」），而這恰好等於對手能把你壓到的上限——max-min = min-max。
- **一句註記**：年份組「1928 論文、1944 書」兩者都要對；**極小極大定理屬於 1928，不要歸給 1944 那本書**。定理只對**兩人零和**成立（這是常見誤傳邊界，見三、T4）。原始證明用 Brouwer 不動點的拓撲論證；本書給直覺、不證。
- **來源**：https://www.privatdozent.co/p/john-von-neumanns-minimax-theorem ；https://www.historyofinformation.com/detail.php?id=601

### 3. 囚徒困境的來歷：Flood & Dresher 實驗、Tucker 命名 ✅
- **驗證值**：
  - **賽局結構**由 Merrill Flood（佛勒德）與 Melvin Dresher（德雷舍）於 **1950 年初**在 RAND 公司（蘭德公司）的賽局理論研究中提出，並做了重複 100 次的實驗。
  - **「囚徒困境（Prisoner's Dilemma）」這個名字與「兩名囚犯被分開偵訊、各自決定要不要招供」的故事版本**由 **Albert W. Tucker（塔克）**所取——他為了向史丹佛的心理學家聽眾講解 Flood–Dresher 的點子，編了這個易懂的故事框架。
- **一句註記**：脊椎敘事的歷史出處。守住分工：Flood–Dresher 造賽局（1950）、Tucker 取名與編故事（同年稍後）。Tucker 也是 Nash 的博論指導教授（見本節 4），這個巧合可在書中一提。
- **來源**：https://plato.stanford.edu/entries/prisoner-dilemma/ ；https://en.wikipedia.org/wiki/Merrill_M._Flood

### 4. Nash 1950/1951：納許均衡與存在性 ✅
- **驗證值**：
  - John Forbes Nash Jr.（納許）**1950 年**（22 歲）向 Princeton 數學系提交博士論文「Non-Cooperative Games」；指導教授 Albert W. Tucker。
  - 同年（**1950**）以短篇「Equilibrium Points in N-Person Games」發表於《PNAS》（美國國家科學院院刊）——**存在性定理的公告版**。
  - 完整版「Non-Cooperative Games」**1951 年 9 月**刊於《Annals of Mathematics》卷 **54**，頁 **286–295**。
  - **存在性證明**：用 Kakutani 不動點定理（1941，推廣自 Brouwer 1911）證明——**每個有限賽局（有限玩家、有限策略）在混合策略下都至少存在一個納許均衡**。
- **一句註記**：年份組「1950 PNAS 公告＋博論、1951 Annals 完整版」。存在性是「混合策略下」的（純策略均衡可能不存在，例如剪刀石頭布——見二、混合策略）。Nash 1994 獲諾貝爾（見本節 9）。
- **來源**：https://www.britannica.com/biography/John-Nash ；https://www.scirp.org/reference/referencespapers?referenceid=2302554 ；https://en.wikipedia.org/wiki/Kakutani_fixed-point_theorem

### 5. 重複賽局與合作的演化：Axelrod 1980 電腦競賽、tit-for-tat ✅
- **驗證值**：
  - Robert Axelrod（艾瑟羅）**1980 年**在密西根大學辦了**兩場**重複囚徒困境電腦競賽：邀請有研究紀錄的學者提交程式，做循環賽（round-robin），每對程式對戰 **200 回合**。
  - **兩場的冠軍都是 tit-for-tat（一報還一報／以牙還牙）**：第一回合合作，之後每一回合複製對手上一回合的選擇。由 Anatol Rapoport（拉波波特，數學家兼心理學家，密西根大學）提交——它也是**所有提交程式中最短的**（只有 4 行 FORTRAN）。
  - Axelrod 把 tit-for-tat 成功歸因於四個性質：**善良（nice，絕不率先背叛）、可激怒（retaliatory，被背叛立刻還手）、寬容（forgiving，對手回頭合作就既往不咎）、清晰（clear，對手容易看懂規則）**。
  - 1984 年出版《The Evolution of Cooperation》（合作的演化）普及此結果，被引用數萬次。
- **一句註記**：脊椎重複賽局層的核心史實。守住：tit-for-tat **不是最強策略**、是**最穩健**的——它在任何單場對戰中都**不可能贏過對手**（最多打平），卻贏得整場錦標賽（見三、T5 的 hedge）。「未來的陰影（shadow of the future）」＝折扣因子夠大時合作才能維持（見本節 6 folk theorem）。
- **來源**：https://egtheory.wordpress.com/2015/03/02/ipd/ ；https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0134128

### 6. 無名氏定理（folk theorem）：耐心讓合作成為均衡 ✅
- **驗證值**：無名氏定理是重複賽局理論的一組結果：當同一個階段賽局（stage game）被**無限重複**、且玩家**夠有耐心**（折扣因子 δ 夠接近 1）時，幾乎任何「可行且個人理性」的報酬——包括囚徒困境的相互合作——都能被支撐為（子賽局完美）均衡，靠的是「可信的獎賞與懲罰」。里程碑：Friedman 1971（觸發策略 trigger strategy 支撐勾結）、Aumann & Shapley、Rubinstein 1970s 末、Fudenberg & Maskin 1986（帶折扣的一般化 folk theorem）。
- **一句註記**：「叫 folk theorem 是因為它在正式發表前就在學界口耳相傳、作者不可考」。本書用它把「未來陰影」量化：合作可維持 ⇔ δ 夠大。給直覺與條件、不給完整證明。**注意：folk theorem 說合作「可以」是均衡，不是「必然」——背叛（全程互背）也仍是一個均衡**（這是常見過度樂觀的邊界，見三、T6）。
- **來源**：http://faculty.haas.berkeley.edu/stadelis/Game%20Theory/econ160_week6.pdf ；https://scholar.harvard.edu/files/maskin/files/folk_theorem_in_repeated_games_with_discounting_or_incomplete_information.pdf

### 7. 演化穩定策略 ESS：Maynard Smith & Price 1973 ✅
- **驗證值**：John Maynard Smith（梅納德・史密斯）與 George R. Price（普萊斯），「The Logic of Animal Conflict」（動物衝突的邏輯），《Nature》卷 **246**，頁 **15–18**，**1973 年**。首次提出**演化穩定策略（evolutionarily stable strategy, ESS）**概念，把賽局理論引入演化生物學。
- **一句註記**：ESS＝「一個族群普遍採用後，無法被任何初始稀少的突變策略入侵」的策略。它**不需要理性**——「策略」是基因型／行為型，「最佳化」由天擇代勞（這是本書最反直覺的橋：均衡不需要會算的玩家）。鷹鴿賽局（Hawk–Dove，見二）是其招牌例。
- **來源**：https://www.nature.com/articles/246015a0 ；https://www.scirp.org/reference/referencespapers?referenceid=2726320

### 8. 謝林點（focal point）：Schelling 1960 ✅
- **驗證值**：Thomas C. Schelling（謝林），《The Strategy of Conflict》（衝突的策略），**1960 年**。提出**謝林點（Schelling point／focal point）**：協調賽局中有多個均衡時，人們在無法溝通的情況下，會傾向選擇某個因「顯著／自然」而脫穎而出的解。經典實驗：問學生「明天要在紐約跟一個陌生人碰面、沒約時間地點，你去哪？」多數答「中央車站大鐘下、中午 12 點」。
- **一句註記**：協調賽局的核心。守住：謝林點是**經驗觀察／心理顯著性**，不是賽局理論能從報酬矩陣推出的東西——這是賽局理論的「文化／脈絡」缺口（一個誠實的局限，見三、T8）。Schelling 與 Robert Aumann 共獲 **2005** 諾貝爾。
- **來源**：https://en.wikipedia.org/wiki/Focal_point_(game_theory) ；https://www.econlib.org/library/Enc/bios/Schelling.html

### 9. 賽局理論的諾貝爾經濟學獎譜系 ✅
- **驗證值**（Sveriges Riksbank Prize in Economic Sciences in Memory of Alfred Nobel，俗稱諾貝爾經濟學獎；嚴格不是諾貝爾本人遺囑設立，書中可一句註明）：
  - **1994**：John Harsanyi（哈薩尼）、John Nash（納許）、Reinhard Selten（澤爾騰）——「非合作賽局均衡理論的開創性分析」。Nash＝均衡基礎；Selten＝子賽局完美等動態精煉；Harsanyi＝不完全資訊賽局（貝氏賽局）。
  - **1996**：William Vickrey（維克里）——拍賣理論（1961 第二價格／維克里拍賣論文）與不對稱資訊（與 James Mirrlees 共獲）。
  - **2005**：Robert Aumann（奧曼）、Thomas Schelling（謝林）——「透過賽局理論分析增進對衝突與合作的理解」。
  - **2007**：Leonid Hurwicz（赫維茲）、Eric Maskin（馬斯金）、Roger Myerson（梅爾森）——「奠定機制設計理論（mechanism design theory）的基礎」。Hurwicz 受獎時 90 歲，是史上最年長的經濟學獎得主。Myerson 證了揭示原理（revelation principle）。
- **一句註記**：機制設計（拍賣／投票的「反向賽局」）史實落點。守住年份組：1994 Nash/Harsanyi/Selten、1996 Vickrey、2005 Aumann/Schelling、2007 Hurwicz/Maskin/Myerson。
- **來源**：https://www.nobelprize.org/prizes/economic-sciences/2007/9276-mechanism-design-theory/ ；https://www.nobelprize.org/prizes/economic-sciences/1994/press-release/ ；https://www.nobelprize.org/prizes/economic-sciences/1996/advanced-information/

### 10. 拍賣與機制設計的具體基準 ✅
- **驗證值**：
  - **維克里拍賣（Vickrey auction）**＝第二價格密封投標：出價最高者得標、但只付**第二高**的價格。Vickrey 1961 證明它讓「誠實出價＝你的真實估值」成為**優勢策略**（dominant strategy）——這是機制設計「設計報酬讓說真話變理性」的招牌。Vickrey 也指出英式拍賣與第二價格拍賣策略等價、荷式拍賣與第一價格拍賣策略等價。
  - **Arrow 不可能定理（Arrow's impossibility theorem）**：Kenneth Arrow（阿羅）1951《Social Choice and Individual Values》——沒有任何投票規則能同時滿足一組「看似合理」的條件（無限制定義域、帕累托、無關選項獨立性、非獨裁）。Arrow 1972 獲諾貝爾（與 Hicks）。
- **一句註記**：機制設計章的兩個招牌——維克里拍賣（好消息：能設計出誘導誠實的機制）與 Arrow 定理（壞消息：投票天生有不可能性）。Arrow 定理的「無關選項獨立性」常被講錯，書中精確陳述。
- **來源**：https://www.nobelprize.org/prizes/economic-sciences/1996/advanced-information/ ；https://plato.stanford.edu/entries/arrows-theorem/

---

## 二、關鍵數值與報酬矩陣（必須精確；此為跨章基準）✅

> 報酬矩陣是「數學恆真」——不依賴 landscape 也能驗算，但全書必須用**同一組數字**，否則脊椎「同一張矩陣被重看七次」會崩。以下是本書統一基準；任一章不得另創數字。

### 脊椎：囚徒困境標準報酬矩陣（全書同一張）
- **慣例**：報酬寫 (列玩家, 行玩家)，數字**越大越好**（用「年數的負值」或「獲益點數」皆可，本書統一用**獲益點數、越大越好**，避免「刑期越小越好」的方向混淆——見三、T1）。
- **本書基準矩陣**（T=5 誘惑 / R=3 獎賞 / P=1 懲罰 / S=0 受騙者）：

  ```text
  本書囚徒困境基準（數字＝獲益點數，越大越好）：
                       對方：合作(C)      對方：背叛(D)
      我方：合作(C)      (3, 3)  ← R,R     (0, 5)  ← S,T
      我方：背叛(D)      (5, 0)  ← T,S     (1, 1)  ← P,P

  必須滿足的不等式： T > R > P > S        （5 > 3 > 1 > 0）✓ 困境核心
  重複賽局額外條件： 2R > T + S           （6 > 5）✓ 否則輪流剝削優於互相合作
  ```
- **關鍵結論**：背叛（D）是**嚴格優勢策略**（不管對方做什麼，背叛報酬都比合作高：5>3 且 1>0）；唯一純策略納許均衡是 **(背叛, 背叛) = (1,1)**；但 (合作,合作)=(3,3) 對雙方都更好——個體理性 vs 集體理性的裂縫，全書中央張力。
- **同源**：T,R,P,S 標號是賽局理論標準（Temptation/Reward/Punishment/Sucker）。

### 混合策略基準
- **剪刀石頭布（rock-paper-scissors）**：對稱零和、**無純策略納許均衡**；唯一納許均衡是各 **1/3** 的混合策略；賽局的值＝0。
- **配對銅板（matching pennies）**：兩人各出正/反，配對者贏、不配對者贏（零和）；唯一納許均衡是雙方各 **1/2** 混合；值＝0。**混合策略的關鍵直覺**：你選的機率要讓**對手對他的兩個選擇無差異**（否則對手會偏向一邊、你就被利用）——這是反直覺點，本書要寫透。

### 零和與極小極大
- **極小極大定理（von Neumann 1928）**：兩人零和賽局，在混合策略下，max-min = min-max = 賽局的值 v。**只對兩人零和成立**（見三、T4）。

### 鷹鴿賽局（Hawk–Dove，ESS 章）
- **標準報酬矩陣**（資源價值 V、打架受傷成本 C；兩鷹相遇平分價值但一半機率受傷）：

  ```text
  鷹鴿賽局（行＝對手；報酬＝期望適存度增益）：
                  對手：鷹(H)          對手：鴿(D)
      我方：鷹(H)   (V−C)/2            V
      我方：鴿(D)   0                  V/2

  情況一 V > C：鷹是嚴格優勢策略、ESS＝全鷹。
  情況二 C > V（自然界常態）：無純策略 ESS；
         ESS＝混合策略，鷹的比例 p* = V/C。
  ```
- **本書數值範例**：取 **V=2、C=4**（C>V）→ ESS 鷹比例 p* = V/C = **2/4 = 1/2**（族群中一半時間當鷹、一半當鴿，或一半個體是鷹）。**鷹鴿賽局＝膽小鬼賽局（chicken）＝雪堆賽局**，賽局理論上同構（生物學家叫鷹鴿、經濟/政治學家叫 chicken）。
- **守住**：ESS 是「無法被入侵」，比納許均衡多一層演化動態的穩定要求；混合 ESS 可實現為「族群比例」或「個體機率」兩種詮釋。

### 協調賽局（謝林點 / 性別戰）
- **純協調賽局**：雙方只要選同一個就好（兩個對稱純策略納許均衡＋一個混合均衡）；謝林點靠**顯著性**選出，不靠報酬。
- **性別戰（battle of the sexes）**：兩個純策略納許均衡，但兩人偏好不同的那一個——協調＋衝突並存。

### 數值自我複核基準
- 囚徒困境唯一純策略 NE＝(D,D)；剪刀石頭布 NE＝(1/3,1/3,1/3)；配對銅板 NE＝(1/2,1/2)；鷹鴿（C>V）ESS 鷹比例＝V/C。**所有混合策略機率、優勢策略判斷、ESS 比例，寫章時自己重算一遍，不得抄記憶。**

---

## 三、常被誤傳／需守住的正確版（直覺的陷阱）

> 以下每條都是「大眾版 vs 正確版」，是「直覺的陷阱」段的素材。守住正確版。

### T1. 報酬方向：「刑期」越小越好 vs「點數」越大越好
- **正確版**：經典囚徒困境用「坐牢年數」講（0/1/5/10 年，越**小**越好），但這會讓「優勢策略＝選報酬大的」這條通用法則反向、容易算錯。**本書統一用「獲益點數、越大越好」（T>R>P>S＝5>3>1>0）**，全書一致。引用經典「年數」版時要明寫方向已反轉。

### T2. 納許均衡 ≠ 最好的結果（不是最佳化全體）
- **正確版**：納許均衡只保證「沒有人能**單方面**改變策略而得益」——它可以是對所有人都糟的結果（囚徒困境的 (背叛,背叛) 正是如此）。納許均衡是「穩定」不是「最優」；把它當成「賽局的最佳解」是最常見的誤解。集體最優（(合作,合作)）往往**不是**納許均衡。

### T3. 「囚徒困境證明合作不理性／自私必勝」是過度推論
- **正確版**：囚徒困境的「背叛佔優」只在**單回合、無未來互動、無外部執行**下成立。一旦**重複**（未來陰影）、能**溝通承諾**、有**聲譽**或**外部懲罰**，合作就能是均衡（folk theorem、Axelrod）。囚徒困境是「為什麼合作會崩」的模型，不是「合作不可能」的證明。守住這層，全書才不會變成犬儒宣言。

### T4. 極小極大定理只對「兩人零和」成立
- **正確版**：von Neumann 1928 的極小極大定理（賽局有唯一的「值」、max-min=min-max）**只**適用於**兩人零和**賽局。多人賽局、非零和賽局（如囚徒困境本身就是非零和！）一般沒有單一的「值」，要用納許均衡這個更一般（但更弱）的概念。把「賽局理論＝零和」是大眾最大的誤解——**現實裡最有趣的賽局（囚徒困境、協調賽局）都不是零和**。

### T5. tit-for-tat「最強」是誤傳；它最穩健，且結論被後人 hedge
- **正確版**：tit-for-tat 贏得 Axelrod 1980 兩場錦標賽，但它在**任何單場一對一對戰中都贏不了對手**（最多平手，因為它從不率先背叛、報復也只還一次）。它靠的是「不製造敵人、整體積分高」。**後續研究（Press & Dyson 2012 的 zero-determinant 策略、各種演化模擬）顯示沒有單一策略在所有環境都最優**——tit-for-tat 的勝出依賴對手池組成與環境（2026-06：學界共識是「穩健、非萬能」）。書中講 Axelrod 結論時要 hedge：它是「一個強力的存在性示範」，不是「演化必然導致 tit-for-tat」。
- **來源**：https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0134128

### T6. folk theorem：合作「可以」是均衡 ≠「必然」會合作
- **正確版**：folk theorem 說，玩家夠耐心時，相互合作**可以**被支撐為均衡——但它同時說**很多其他結果（包括全程互相背叛）也都是均衡**。folk theorem 是「均衡多到爆炸」的定理，不是「重複就會合作」的保證。它解釋了合作的**可能性**，沒解釋為什麼現實會選到合作那一個（這要靠謝林點、演化、聲譽等額外故事）。

### T7. 最後通牒賽局：「人會拒絕不公平」有文化變異，別當鐵律
- **正確版**：最後通牒賽局（Güth/Schmittberger/Schwarze 1982）中，回應者常拒絕過低的分配（如 <20–30%），違背「拿到總比沒有好」的理性預測——這顯示公平偏好是真的。但**跨文化實驗（如 Henrich 等人的小規模社會研究）顯示拒絕門檻與提議慷慨度差異很大**，不是普世常數（2026-06）。本書點到此例屬「策略情境下的非理性」，**數學與規範分析指向《決策與理性》、心理機制指向《邏輯謬誤與認知偏誤》**，本書只用它說明「報酬矩陣不只有金錢」。
- **來源**：https://imotions.com/blog/learning/research-fundamentals/the-ultimatum-game/

### T8. 謝林點不是賽局理論「算」出來的
- **正確版**：協調賽局有多個納許均衡時，賽局理論（純報酬矩陣）**無法**告訴你會選哪一個——謝林點靠的是**心理顯著性、文化共識、脈絡**這些矩陣外的東西。這是賽局理論一個誠實的局限，不是它的勝利。把「謝林點」講成「賽局理論預測人會碰面在大鐘下」是錯的——是 Schelling 觀察到人會、然後指出理論解釋不了。

### T9. ESS 不需要「理性」或「有意識的最佳化」
- **正確版**：演化穩定策略裡的「策略」是基因決定的行為型，「最佳化」由天擇執行——**沒有任何個體在算報酬**。把 ESS 講成「動物理性地選擇混合策略」是擬人化錯誤。賽局理論在這裡量化的是「哪種行為比例能抵抗突變入侵」，與意識、理性無關。這正是本書「均衡可以不需要會算的玩家」這個驚嘆點的核心。

### T10. 「諾貝爾經濟學獎」嚴格不是諾貝爾遺囑設立的獎
- **正確版**：賽局理論諸獎（1994/1996/2005/2007）都是「Sveriges Riksbank Prize in Economic Sciences in Memory of Alfred Nobel」（瑞典央行紀念諾貝爾經濟學獎），由瑞典央行 1968 年設立、1969 起頒，**不是**諾貝爾 1895 遺囑裡的五個獎之一。書中沿用「諾貝爾經濟學獎」俗稱，但首次出現時一句註明此區別（嚴謹度誠實）。

---

## 四、與本套鄰書的邊界（僅供跨書指引，不需網路查證）

- **《在不確定中下注：決策與理性》（decide）**：owner of 單人理性選擇——期望值、期望效用、vNM 公理（效用不是金額／凹函數＝風險趨避）、不確定 vs 風險、貝氏決策。本書凡用到「單人在不確定下該怎麼選」一律指向它（如混合策略的期望報酬計算的**效用**面、最後通牒賽局的規範基準）。本書只在**「對手會反應」**時接手。三招牌跨書連結之一（決策 ↔ 博弈是同一枚硬幣兩面）。
- **《馴服隨機：機率與統計》（probability）**：owner of 機率機制——期望值「怎麼算」、混合策略期望報酬的機率運算、ESS 的族群比例作為機率分布。本書用混合策略時，把「期望值怎麼算」指向它，只用結果、不重推。
- **《思考的陷阱：邏輯謬誤與認知偏誤》（bias）**：owner of 推理錯誤與認知偏誤的心理機制。策略情境下的非理性（最後通牒賽局的公平偏好、信任賽局）的**心理機制**指向它，本書只點到「報酬矩陣不只有金錢」。
- **《矩陣是動詞：線性代數》（linalg，書架既有）**：若混合策略幾何、演化動態的馬可夫鏈穩態觸及向量／特徵值，點到為止指向它、不展開。

跨書引用格式一律主題式：`（見《在不確定中下注》談期望效用／單人理性那章）`。不寫死檔名路徑、不寫死他書未定案的精確章號（章序未定者用主題帶過；已驗證對齊者如《馴服隨機》ch08 期望值可寫死）。

---

## 五、跨章一致性速查表

| 項目 | 基準值 | 備註 |
|---|---|---|
| 囚徒困境基準矩陣 | T,R,P,S = 5,3,1,0（點數越大越好） | T>R>P>S；2R>T+S |
| 囚徒困境純策略 NE | (背叛,背叛)=(1,1) | 唯一；背叛＝嚴格優勢策略 |
| 囚徒困境集體最優 | (合作,合作)=(3,3) | **非**納許均衡（中央張力） |
| 剪刀石頭布 NE | 各 1/3 混合；值=0 | 無純策略 NE |
| 配對銅板 NE | 各 1/2 混合；值=0 | 無純策略 NE |
| 鷹鴿賽局矩陣 | V=2、C=4（C>V）；ESS 鷹比例 p*=V/C=1/2 | =膽小鬼=雪堆，同構 |
| 極小極大定理適用範圍 | 僅兩人零和；max-min=min-max=v | von Neumann 1928 |
| 維克里拍賣 | 第二價格密封投標；誠實出價＝優勢策略 | Vickrey 1961 |
| folk theorem 條件 | 無限重複＋δ 夠大 → 合作可為均衡 | 合作可能、非必然 |

### 關鍵年份速查
| 事件 | 年份 |
|---|---|
| von Neumann 極小極大定理（Math. Annalen 100:295） | 1928 |
| von Neumann & Morgenstern《Theory of Games and Economic Behavior》 | 1944 |
| Flood–Dresher 囚徒困境實驗（RAND）／Tucker 命名 | 1950 |
| Nash 博論＋PNAS 公告 | 1950 |
| Nash「Non-Cooperative Games」（Annals 54:286） | 1951 |
| Arrow《Social Choice and Individual Values》不可能定理 | 1951 |
| Schelling《The Strategy of Conflict》謝林點 | 1960 |
| Vickrey 第二價格拍賣論文 | 1961 |
| Maynard Smith & Price ESS（Nature 246:15） | 1973 |
| Friedman 觸發策略（folk theorem 起點之一） | 1971 |
| Güth–Schmittberger–Schwarze 最後通牒賽局 | 1982 |
| Axelrod 重複囚徒困境電腦競賽（tit-for-tat 奪冠） | 1980 |
| Axelrod《The Evolution of Cooperation》 | 1984 |
| Fudenberg & Maskin 帶折扣 folk theorem | 1986 |
| Nash/Harsanyi/Selten 諾貝爾經濟學獎 | 1994 |
| Vickrey/Mirrlees 諾貝爾經濟學獎 | 1996 |
| Aumann/Schelling 諾貝爾經濟學獎 | 2005 |
| Hurwicz/Maskin/Myerson 機制設計諾貝爾經濟學獎 | 2007 |
| Press & Dyson zero-determinant 策略（tit-for-tat 非萬能） | 2012 |

---

## 待考／低信心項（⚠️）

1. **Axelrod 結論的後續解讀（T5，最需 hedge 的時效項）**（2026-06）：tit-for-tat 的勝出依賴對手池與環境；Press–Dyson 2012 zero-determinant 策略顯示沒有萬能策略。書中講 Axelrod 要框成「強力存在性示範、非演化定律」、別寫死「演化必然導向 tit-for-tat」。
2. **最後通牒賽局的跨文化變異（T7）**（2026-06）：拒絕門檻與慷慨度有文化差異、非普世常數；本書只點到、深入指向《決策》《偏誤》。
3. **鷹鴿賽局數值範例 V/C**：V=2、C=4 是本書教學選值（給 p*=1/2 的乾淨數字）、非「自然界實測常數」；書中標明是示範值。
4. **「諾貝爾經濟學獎」名稱（T10）**：嚴格是瑞典央行紀念獎、非諾貝爾遺囑五獎之一；沿用俗稱但首次註明。
5. **同形記號歧義**：本書 δ＝折扣因子（folk theorem）、p*＝ESS 混合比例或混合策略機率、V/C＝鷹鴿賽局價值/成本、T/R/P/S＝囚徒困境四報酬。跨章新增內容引入這些符號前先回查附錄 A。

---
*掃描日期：2026-06-20。本檔史實由一輪帶網路研究查證（12 組獨立檢索），優先採一級／權威來源（NobelPrize.org 官方頁、SEP、原始論文 DOI/Annals/Nature 原文、Britannica）。報酬矩陣與均衡數值屬數學恆真、不依賴 landscape 但全書統一。重大修正（推翻既有基準）需兩個獨立來源。*
