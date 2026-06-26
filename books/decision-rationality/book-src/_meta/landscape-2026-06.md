# 《在不確定中下注》— 事實基準表（landscape, 2026-06）

> 本檔是全書的**事實錨點**。每一章的歷史、人名、年份、引文、實驗數值都必須與此一致；要改任何基準值，先改這裡、再同步全書、並在 maintenance.md 掃描日誌記一行（maintenance 在 P5 才建）。
> 規則：每條都帶「驗證值／一句註記／來源 URL」。無法以可信來源確認者標 ⚠️ 並說明原因。時效性／再現性敘述加註 (2026-06)。
> 信心分級：本書事實多屬「史實」（已定案，論文年份、諾貝爾、出處）與「數學恆真」（期望值、貝氏、效用代入，不會過時）。**時效／再現性風險集中在「展望理論的實驗參數估計」**（見一、9 與三、T6）——這是全書最該 hedge 的一類，引用實驗數字時務必標明「常被引用的一組估計、有再現性討論、非常數、(2026-06)」。
> 本檔史實與參數已由一次帶網路研究流程查證（2026-06-20 建書，15 組 web 查證）；優先採一級／權威來源（原始論文、Econometrica/QJE/JRU 出版頁、SEP、諾貝爾官網、Springer/JSTOR）。

---

## 一、歷史與人物（年份、歸屬、原話）

### 1. 聖彼得堡悖論與 Daniel Bernoulli（1738）✅
- **驗證值**：Daniel Bernoulli（1700–1782）1738 年於《Commentarii Academiae Scientiarum Imperialis Petropolitanae》卷 V（頁 175–192）發表「Specimen Theoriae Novae de Mensura Sortis」（《測量風險的新理論闡述》）。文中提出**效用**概念、**對數效用**、並用以解聖彼得堡悖論。Bernoulli 主張財富的效用約等於財富的對數（邊際效用遞減），故大而極不可能的獎金對期望效用的貢獻有限，理性的人只願付有限賭金。
- **一句註記**：「效用不是金額、邊際效用遞減」的歷史起點，本書 ch02→ch03 的橋。聖彼得堡悖論**不是數學錯誤**，是「期望值 ≠ 該付的價」的訊號（見 T1）。
- **來源**：https://plato.stanford.edu/entries/paradox-stpetersburg/ ；https://link.springer.com/article/10.1007/s10203-024-00471-z

### 2. 聖彼得堡悖論的真正首倡者：Nicolaus Bernoulli（1713）✅
- **驗證值**：聖彼得堡賭局**最早由 Nicolaus I Bernoulli（1687–1759）於 1713-09-09 寫給 Pierre Rémond de Montmort 的信中提出**（一個用骰子的早期版本）。Daniel Bernoulli 1738 年才提出對數效用的解，並因發表於聖彼得堡科學院期刊而得名「St. Petersburg」。
- **一句註記**：常被誤傳為「Daniel Bernoulli 提出悖論」（見 T3）。正確版：Nicolaus 提出問題、Daniel 提出解、名字來自發表地。
- **來源**：https://plato.stanford.edu/entries/paradox-stpetersburg/

### 3. von Neumann–Morgenstern 期望效用（1944／**公理在 1947 二版**）✅
- **驗證值**：John von Neumann 與 Oskar Morgenstern，《Theory of Games and Economic Behavior》，Princeton University Press，**第一版 1944**。但**從公理推導期望效用的形式內容出現在 1947 年第二版的附錄**（"The Axiomatic Treatment of Utility"）。vNM 公理通常列為四條：完備性（completeness）、遞移性（transitivity）、連續性（continuity）、獨立性（independence）。
- **一句註記**：年份陷阱——書是 1944，**期望效用公理化是 1947 二版附錄**（見 T2）。表現定理：滿足四公理 ⇒ 偏好可由某期望效用最大化表示。
- **來源**：https://en.wikipedia.org/wiki/Theory_of_Games_and_Economic_Behavior ；https://academic.oup.com/book/11279/chapter/159842381

### 4. Leonard Savage：主觀期望效用與 sure-thing principle（1954）✅
- **驗證值**：Leonard Jimmie Savage，《The Foundations of Statistics》，Wiley，1954。建立**主觀期望效用**（subjective expected utility）：從選擇行為同時導出**主觀機率**與效用函數。核心公理之一為**確實事件原理（sure-thing principle, P2）**。承襲 Ramsey、de Finetti、vNM。
- **一句註記**：把「不確定」（不只客觀機率）納入期望效用的嘗試；Allais（1953）與 Ellsberg（1961）正是對它（尤其 sure-thing principle）的反例。
- **來源**：https://en.wikipedia.org/wiki/Savage%27s_subjective_expected_utility_model

### 5. Frank Knight：風險 vs 不確定（1921）✅
- **驗證值**：Frank H. Knight，《Risk, Uncertainty and Profit》，1921。區分**風險（risk）＝機率可測（可保險、可下注）** 與 **不確定（uncertainty）＝機率不可測（"true uncertainty", not susceptible to measurement）**。Knight 認為利潤來自承擔不可測的不確定。
- **一句註記**：本書 ch04 的地基。常被當同義詞混用（見 T5）。「Knightian uncertainty」即此。
- **來源**：https://en.wikipedia.org/wiki/Knightian_uncertainty ；https://news.mit.edu/2010/explained-knightian-0602

### 6. Maurice Allais：Allais 悖論（1953）✅
- **驗證值**：Maurice Allais 1953 年論文「Le Comportement de l'homme rationnel devant le risque: critique des postulats et axiomes de l'école américaine」，*Econometrica* 21(4):503–546。設計兩組對賭，顯示受過機率訓練的人系統性違反期望效用的**獨立公理**。Allais 1988 年獲諾貝爾經濟學獎。
- **一句註記**：「確定性效應」（certainty effect）一詞後由 Kahneman–Tversky 1979 普及。本書 ch11。經典金額版：題1 確定 100 萬 vs（10% 得 500 萬, 89% 得 100 萬, 1% 得 0）；題2（11% 得 100 萬, 89% 得 0）vs（10% 得 500 萬, 90% 得 0）。
- **來源**：https://en.wikipedia.org/wiki/Allais_paradox

### 7. Daniel Ellsberg：Ellsberg 悖論（1961）✅
- **驗證值**：Daniel Ellsberg，「Risk, Ambiguity, and the Savage Axioms」，*Quarterly Journal of Economics* 75(4):643–669（1961）。**三色甕**：90 球，30 紅，60 為黑或黃（比例未知）。多數人同時偏好「賭紅」勝過「賭黑」、又偏好「賭(黑或黃)」勝過「賭(紅或黃)」——無法用任何單一對「黑佔比」的信念同時成立，違反 Savage 的 sure-thing principle。Ellsberg 稱此為**模糊趨避（ambiguity aversion）**。
- **一句註記**：模糊趨避是**對公理的拒絕、不是算錯**（見 T5）。同一個 Daniel Ellsberg 即後來的五角大廈文件揭密者（軼事可一句帶，hedge）。
- **來源**：https://en.wikipedia.org/wiki/Ellsberg_paradox

### 8. Herbert Simon：有限理性與 satisficing（諾貝爾 1978）✅
- **驗證值**：Herbert A. Simon 1978 年獲諾貝爾經濟學獎，表彰「對經濟組織內決策過程的開創性研究」。提出**有限理性（bounded rationality）**（理性受認知與資訊成本所界）與 **satisficing**（satisfy＋suffice 的合成詞，找「夠好」而非「最佳」）。
- **一句註記**：本書 ch13。satisficing＝設一 aspiration level、達標即停；在「把搜尋成本算進去」的元層次上可視為最佳化（見 T10）。
- **來源**：https://www.nobelprize.org/uploads/2018/06/simon-lecture.pdf ；https://en.wikipedia.org/wiki/Herbert_A._Simon

### 9. Kahneman & Tversky：展望理論（1979）與累積展望理論（1992）✅／⚠️參數
- **驗證值**：
  - **原始展望理論**：Daniel Kahneman & Amos Tversky，「Prospect Theory: An Analysis of Decision under Risk」，*Econometrica* 47(2):263–291（1979-03）。提出參考點、損失趨避、機率權重、確定性效應、隔離效應。
  - **累積展望理論（CPT）**：Amos Tversky & Daniel Kahneman，「Advances in Prospect Theory: Cumulative Representation of Uncertainty」，*Journal of Risk and Uncertainty* 5(4):297–323（1992-10）。決策權重改用**累積**機率，並給出參數估計。
  - **TK1992 中位參數估計**：價值函數曲率 α = β = **0.88**；損失趨避 λ = **2.25**；機率權重 γ（得）= **0.61**、δ（失）= **0.69**。價值函數 v(x)=x^α (x≥0)、v(x)=−λ(−x)^β (x<0)；權重 w(p)=p^γ/(p^γ+(1−p)^γ)^(1/γ)。
- **⚠️ 再現性與時效（2026-06）**：λ=2.25 等是**一組常被引用的中位估計、不是常數**。近期 meta-analysis（Brown et al. 2024, *Journal of Economic Psychology*）以隨機效應給出 **λ≈1.31（95% CI 1.10–1.53）**，並指 TK1992 的 2.25「可能偏高」；其他研究依領域給範圍 **1.8–2.7**。損失趨避**現象本身**跨文化、跨領域穩健，但**具體係數值變異大**。本書引用任何展望參數**必須 hedge**：標明來源 TK1992、標 (2026-06)、給範圍、明說「非物理常數、有再現性討論」。
- **來源**：https://www.econometricsociety.org/publications/econometrica/1979/03/01/prospect-theory-analysis-decision-under-risk ；https://link.springer.com/article/10.1007/BF00122574 ；https://www.sciencedirect.com/science/article/pii/S0167487024000485 （meta-analysis λ≈1.31）

### 10. Kahneman 諾貝爾（2002）；Tversky 1996 過世 ✅
- **驗證值**：Daniel Kahneman 2002 年與 Vernon L. Smith **共享**諾貝爾經濟學獎（Kahneman 表彰「把心理學洞見整合進經濟學，尤其是不確定下的判斷與決策」）。Amos Tversky **1996 年過世**；諾貝爾不追授，故 Tversky 未能共享（一般認為若在世會共享）。
- **一句註記**：年份/歸屬陷阱——2002 諾貝爾**不含 Tversky**（已歿），與 Kahneman 同年得獎的是實驗經濟學的 Vernon Smith、**不是 Tversky**（見 T7）。
- **來源**：https://www.nobelprize.org/prizes/economic-sciences/2002/kahneman/facts/ ；https://en.wikipedia.org/wiki/Daniel_Kahneman

### 11. 資訊的價值：Howard 1966／Raiffa–Schlaifer 1961 ✅
- **驗證值**：
  - 「資訊的價值」（value of information）框架由 **Ronald A. Howard 1966「Information Value Theory」（*IEEE Transactions on Systems Science and Cybernetics* SSC-2(1):22–26）** 形式化；**EVPI**（完全資訊期望價值）＝決策者為「在行動前得知某不確定量的真值」願付的最高金額。
  - **EVSI**（樣本資訊期望價值）由 **Howard Raiffa & Robert Schlaifer，《Applied Statistical Decision Theory》1961** 推廣——一次不完美觀測在決策前帶來的期望效用增益。
  - 關鍵性質：資訊價值在期望意義上 **≥ 0**（多知道不會更糟）；**不會改變最適行動的資訊，其決策價值精確等於 0**。
- **一句註記**：本書 ch07 的地基與「資訊不改變決策 ⇒ 價值＝0」的高潮洞見。
- **來源**：https://en.wikipedia.org/wiki/Expected_value_of_perfect_information ；https://en.wikipedia.org/wiki/Expected_value_of_sample_information

### 12. 多屬性效用：Keeney–Raiffa（1976）✅
- **驗證值**：Ralph Keeney & Howard Raiffa，《Decisions with Multiple Objectives: Preferences and Value Tradeoffs》，Wiley，1976。建立**多屬性效用理論（MAUT）**：加權加總值函數 v(t)=Σ wⱼ·vⱼ(xⱼ)，在**偏好獨立**等條件下成立；否則需乘法／多線性合成。區分「效用函數」（風險下）與「值函數」（確定下強度比較）。
- **一句註記**：本書 ch14；加權加總法的危險在於「偏好獨立」常被違反、權重常被結論回填（見 T11）。
- **來源**：https://link.springer.com/doi/10.1007/978-1-4419-1153-7_644

### 13. Ramsey／de Finetti：Dutch book 與主觀機率 ✅
- **驗證值**：Frank Ramsey（1926「Truth and Probability」，1931 出版）與 Bruno de Finetti（1937）各自提出：若一個人的信念（賭率）不滿足機率公理（不自洽），可被組合成一組賭局讓他**穩賠**（Dutch book／荷蘭賭論證）——故理性信念必須自洽（像機率）。
- **一句註記**：本書 ch06「主觀機率不是隨便喊、受 Dutch book 約束」的依據。給直覺、不展開。
- **來源**：https://plato.stanford.edu/entries/dutch-book/

---

## 二、關鍵數值（必須精確；此為跨章基準，多屬數學恆真）

### 脊椎賭注（the bet）：L =（+200, 0.5; −100, 0.5），單位 NT$
- **期望值** E[L] = 0.5·(+200) + 0.5·(−100) = **+50**。
- **基準凹效用** u(x)=√(x+100)（財富基準 W=100，全書統一；ln 版只在 ch03 對照聖彼得堡一次）。
  - u(不賭) = √(0+100) = **10**。
  - EU(L) = 0.5·√(200+100) + 0.5·√(−100+100) = 0.5·√300 + 0.5·√0 = 0.5·17.3205 + 0 = **8.6603**。
  - EU(L)=8.66 < u(不賭)=10 ⇒ **拒絕正期望值賭注＝風險趨避**（裂縫顯現，全書採此基準 W=100）。
  - 確定等值 CE：u(CE)=8.6603 ⇒ CE = 8.6603² − 100 = 75.0 − 100 = **−25.0**。
  - 風險溢酬 = E[L] − CE = 50 − (−25) = **75**。
- ⚠️ **基準 W 的選定**：若用 W=1000，EU(L)=0.5·√1200+0.5·√900=32.32 > √1000=31.62 會「接受」，裂縫消失。故全書定案 **W=100** 使「拒絕正期望值」的裂縫顯現。各章不得另用 W。
- **校驗常數**：√300=17.3205、√3=1.7321、√1000=31.6228、√1200=34.6410、√900=30。

### 聖彼得堡賭局
- 規則：擲公正硬幣到首次正面；若在第 n 次首次正面，付 2ⁿ。
- 期望值 E = Σ(n=1→∞) (1/2ⁿ)·2ⁿ = Σ(n=1→∞) 1 = **∞**（每項貢獻恰為 1，發散）。
- 對數效用下（u=ln）期望效用**有限**（Daniel Bernoulli 1738）→ 理性人只願付有限。
- 截斷版（最多付到第 N 次首次正面）期望值 = **N**（有限；無限來自尾部）。

### 脊椎醫療檢查（the test）：盛行率 1%、敏感度 99%、偽陽率 5%
- 後驗 P(病|陽性) = P(陽|病)·P(病) / [P(陽|病)·P(病) + P(陽|健康)·P(健康)]
  = (0.99·0.01) / (0.99·0.01 + 0.05·0.99) = 0.0099 / (0.0099 + 0.0495) = 0.0099 / 0.0594 = **0.16667 ≈ 16.7%**。
- **自然頻率交叉驗算**（1 萬人）：100 病 → 99 真陽；9900 健康 → 495 偽陽；共 594 陽性，其中 99 真病 → 99/594 = **16.67%**。✅ 兩法一致。
- ⚠️ **與《馴服隨機》ch05 的基率不同**：該書用盛行率 0.1%（後驗≈1.94%）；本書刻意用 **1%**（後驗 16.7%）讓後驗落在「值得決策」的區間。各章引用本書檢查時用 **1% / 16.7%**，並明寫此差異、把機率機制指向《馴服隨機》ch05。
- **檢查效用矩陣**（示意，全書一致）：u(治療,病)=−10、u(不治療,病)=−100、u(治療,健康)=−20、u(不治療,健康)=0。
  - EU(治療|陽性) = 0.1667·(−10) + 0.8333·(−20) = −1.667 − 16.667 = **−18.33**。
  - EU(不治療|陽性) = 0.1667·(−100) + 0.8333·0 = **−16.67**。
  - ⇒ 在此矩陣與後驗下 **不治療**期望效用較高（−16.67 > −18.33）；把 u(不治療,病) 由 −100 改為 −500 則翻轉（自行於章內重算）。

### 展望理論（TK1992 中位估計；引用必 hedge，見一、9 與 T6）
- 價值函數 v(x) = x^α (x≥0)；v(x) = −λ·(−x)^β (x<0)；**α = β = 0.88、λ = 2.25**。
- 機率權重 w(p) = p^γ / (p^γ + (1−p)^γ)^(1/γ)；**γ = 0.61（得）、δ = 0.69（失）**；小機率被高估、中大機率被低估（倒 S 型）。
- 脊椎賭注展望重算（參考點 0，先用 w(p)=p 簡化）：v(+200)=200^0.88、v(−100)=−2.25·100^0.88。
  - 200^0.88 = exp(0.88·ln200) = exp(0.88·5.2983) = exp(4.6625) ≈ **105.9**。
  - 100^0.88 = exp(0.88·ln100) = exp(0.88·4.6052) = exp(4.0526) ≈ **57.5**；×2.25 ≈ **129.5**。
  - 加權值 ≈ 0.5·105.9 − 0.5·129.5 = 52.95 − 64.75 = **−11.8 < 0** ⇒ **拒絕**（與凹效用殊途同歸，機制是損失更重而非邊際遞減）。⚠️ 這些 v 值依賴 α=0.88、λ=2.25，**換 λ=1.31 重算**：100^0.88·1.31≈75.3，0.5·105.9−0.5·75.3=+15.3>0 ⇒ **會接受**——示範參數不確定足以翻轉結論，章內務必點出。
- **校驗**：ln200=5.2983、ln100=4.6052、exp(4.6625)≈105.9、exp(4.0526)≈57.5（手算保留 1 位小數，章內可微調但須自我複核）。

### Allais 對賭（經典金額版，單位「萬」）
- 題1：A =（確定 100）；B =（10% 得 500, 89% 得 100, 1% 得 0）。
- 題2：C =（11% 得 100, 89% 得 0）；D =（10% 得 500, 90% 得 0）。
- 多數人選 **A 又選 D** ⇒ 消去兩題共同的「89%」後，A 與 D 對剩下 11% 的偏好相反 ⇒ 違反獨立公理。

### 數學常數
- ln2 ≈ 0.6931、e ≈ 2.71828；√3 ≈ 1.7321、√300 ≈ 17.3205、√1000 ≈ 31.6228。全書統一。

---

## 三、常被誤傳／需守住的正確版（直覺的陷阱）

> 以下每條都是「大眾版 vs 正確版」，是「直覺的陷阱」段的素材。守住正確版。

### T1. 聖彼得堡「期望值無限 ⇒ 理性人該付任意多」是**錯的**
- **正確版**：期望值無限**不是數學錯誤**，它正確地說「平均報酬發散」；但期望值**不是該付的價**。Daniel Bernoulli 用**邊際效用遞減（對數效用）**指出理性人的期望**效用**有限、故只願付有限。聖彼得堡是「期望值≠效用」的訊號，不是悖論性的算術矛盾。

### T2. vNM 期望效用公理的出處年份
- **正確版**：《Theory of Games and Economic Behavior》第一版是 **1944**；但**從公理推導期望效用的形式內容在 1947 年第二版的附錄**。科普常寫「1944 年提出期望效用公理」，更精確是「1944 出書、1947 二版附錄給公理化」。

### T3. 聖彼得堡悖論的首倡者
- **正確版**：問題**最早由 Nicolaus Bernoulli 1713 年**（致 Montmort 的信）提出；Daniel Bernoulli 1738 提出對數效用的**解**，名稱「St. Petersburg」來自**發表地（聖彼得堡科學院期刊）**。別寫成「Daniel Bernoulli 提出悖論」。

### T4. 風險趨避不是「膽小／不理性」
- **正確版**：在**凹效用**下，拒絕一個正期望值的賭是**理性的**（期望效用 < 不賭的效用）。風險趨避是效用函數形狀（凹＝邊際遞減）的數學後果，不是性格缺陷或非理性。

### T5. 風險（risk）≠ 不確定（uncertainty）；模糊趨避不是「算錯」
- **正確版**：Knight 1921 區分**機率可測的風險**與**機率不可測的不確定/模糊**。Ellsberg 三色甕中受試者的模糊趨避，是**對 sure-thing 公理的拒絕**（任何單一信念都無法同時合理化兩個偏好），**不是算術錯誤**。別把兩詞當同義詞、別把 Ellsberg 受試者說成「算錯機率」。

### T6. 展望理論的參數（λ≈2.25 等）不是常數（最重要的再現性項）（2026-06）
- **正確版**：α=β=0.88、λ=2.25、γ=0.61、δ=0.69 是 **Tversky–Kahneman 1992 的一組中位估計**，**不是物理常數**。meta-analysis（Brown et al. 2024）給 **λ≈1.31（CI 1.10–1.53）**，指 2.25「可能偏高」；依領域範圍 1.8–2.7。**損失趨避現象本身跨文化穩健，但係數值變異大。** 引用任何展望參數務必：標來源 TK1992、標 (2026-06)、給範圍、明說「非常數、有再現性討論」。

### T7. 展望理論**沒有**證明「人不理性／期望效用沒用」；2002 諾貝爾**不含 Tversky**
- **正確版**：展望理論是更好的**描述**模型，期望效用仍是合理的**規範**理論——兩套數學描述兩件不同的事（人怎麼選 vs 該怎麼選），不互相否證。另：Tversky **1996 過世**，2002 諾貝爾由 Kahneman 與 **Vernon Smith**（不是 Tversky）共享；諾貝爾不追授。

### T8. 參考點依賴／損失趨避不是「人很笨」的指控
- **正確版**：它們是**穩定、可預測方向**的描述性事實（不是隨機錯誤）。把它當「缺陷」會錯過重點——重點是偏離有結構、可建模、可預期，這正是它了不起的地方。

### T9. Allais「我的選擇都很合理、哪有矛盾」
- **正確版**：矛盾不在單題內，而在**跨兩題對共同 89% 的不同對待**——消去共同結果後，選 A 與選 D 對剩下 11% 的偏好相反。受試者覺得「都合理」正是確定性效應在作怪，不代表沒違反獨立公理。

### T10. satisficing 不是「偷懶／次優」
- **正確版**：把**搜尋成本**算進去後，「夠好就停」可能就是真正的最佳化（找最大要付的搜尋代價未必值得）。有限理性是**把成本納入的理性**，不是放棄理性。

### T11. 加權評分表不是「客觀計算」
- **正確版**：加權加總值函數 v=Σwⱼvⱼ 的權重是**價值判斷**，常被「先有結論再回填」；且它假設**偏好獨立**（一維權衡不受他維水準影響），此假設常被違反。權重微小改動就翻轉結論是**警訊**（結論不穩健），不是巧合。

### T12. 沉沒成本在規範上該被忽略
- **正確版**：已付且不可回收的成本，在「往前看」的決策中**不該**進入計算（只看未來的增量成本與報酬）。人會受沉沒成本影響（協和號效應）是描述性事實、不是規範依據。

### T13. 把會反應的對手當固定機率
- **正確版**：對「自然的不確定」（不會針對你）可用單人期望值；對「會策略性回應的對手」必須用賽局——把對手當固定機率會系統性低估對手。決策↔賽局的分界是質變（均衡概念）不是量變（更難的期望值）。

---

## 四、與書架相鄰書的邊界（僅供跨書指引，依總綱 §2，不需網路查證）

- **《馴服隨機》（probability）**：機率公理、條件機率、**貝氏定理的機率機制**、期望值的機率定義、變異數、分布。本書 ch05–07 只用結果、不重推；醫療檢查與其 ch05 同題（但本書用盛行率 1%、後驗 16.7%；該書 0.1%、1.94%）。
- **《思考的陷阱》（fallacies-biases）**：偏誤的**心理機制**（雙系統、捷思怎麼運作、為何察覺不到、演化由來）。本書講展望理論的**數學描述**與規範後果、把心理成因指向它（理性三角）。
- **《賽局：當理性互相碰撞》（game-theory）**：多人策略互動（納許均衡、混合策略、機制設計）。本書是單人決策；「對手會反應」處交棒給它（ch04/10/16/18）。
- **《如何不騙自己》（scientific-method）**：信念更新的**貝氏確證**面與制度防線。與本書貝氏決策互指（理性三角，ch05/06/17）。
- **《馴服無限》（calculus）**：凹效用的凹凸、邊際遞減的微分直覺、期望值的積分版。本書 ch03/08 觸及時點到指向。

---

## 關鍵年份速查
| 事件 | 年份 |
|---|---|
| Nicolaus Bernoulli 提出聖彼得堡賭局（致 Montmort 信） | 1713 |
| Daniel Bernoulli「Specimen Theoriae Novae」對數效用解 | 1738 |
| Frank Knight《Risk, Uncertainty and Profit》 | 1921 |
| Ramsey「Truth and Probability」（撰，1931 出版） | 1926 |
| de Finetti 主觀機率／Dutch book | 1937 |
| von Neumann–Morgenstern《Theory of Games》一版 | 1944 |
| 期望效用公理化（vNM 二版附錄） | 1947 |
| Maurice Allais 悖論（Econometrica 21） | 1953 |
| Leonard Savage《The Foundations of Statistics》 | 1954 |
| Daniel Ellsberg 悖論（QJE 75） | 1961 |
| Raiffa–Schlaifer《Applied Statistical Decision Theory》（EVSI） | 1961 |
| Howard「Information Value Theory」（EVPI） | 1966 |
| Keeney–Raiffa《Decisions with Multiple Objectives》（MAUT） | 1976 |
| Kahneman–Tversky 展望理論（Econometrica 47） | 1979 |
| Herbert Simon 諾貝爾（有限理性） | 1978 |
| Allais 諾貝爾 | 1988 |
| Tversky–Kahneman 累積展望理論（JRU 5） | 1992 |
| Amos Tversky 過世 | 1996 |
| Kahneman 諾貝爾（與 Vernon Smith 共享） | 2002 |
| 損失趨避 meta-analysis（λ≈1.31，Brown et al.） | 2024 |

---

## 待考／低信心項（⚠️）
1. **展望理論參數的再現性（T6，最重要的時效項）**（2026-06）：α=β=0.88、λ=2.25、γ=0.61、δ=0.69 是 TK1992 中位估計、非常數；meta-analysis 給 λ≈1.31、範圍 1.8–2.7。引用必 hedge＋標時點。**本書最可能在數年內需要更新的一節。**
2. **效用函數財富基準 W=100**：為使脊椎賭注「拒絕正期望值」的裂縫顯現而選定（W=1000 會接受）。這是教學設計選擇、非經驗常數；各章須統一用 W=100。
3. **檢查盛行率 1%（後驗 16.7%）**：刻意異於《馴服隨機》ch05 的 0.1%（1.94%），為讓後驗落在「值得決策」區間。引用本書檢查時須用 1%/16.7% 並明寫差異。
4. **展望理論 v 值手算（105.9、57.5 等）**：依 α=0.88 的指數手算、保留 1 位小數；不同捨入會有末位差異，章內須自我複核並標「示意值」。
5. **Allais／Ellsberg 軼事**（Savage 自己選錯後改回、Ellsberg 即五角大廈文件揭密者）：可放但標「轉述／軼事」，hedge。
6. **同形記號歧義**（附錄 A 有專節）：λ＝損失趨避係數；α β＝展望價值曲率；γ δ＝機率權重參數；π(p)＝決策權重（本書圓周率不出現）；P(θ|D)＝後驗。跨章新增內容引入這些符號前先回查附錄 A。

---
*掃描日期：2026-06-20。本檔史實與參數由一次帶網路研究流程查證（15 組 web 檢索：展望理論 1979/1992、聖彼得堡 1738/Nicolaus 1713、Allais 1953、Ellsberg 1961、vNM 1944/1947、Savage 1954、Knight 1921、Simon 1978 諾貝爾、Kahneman 2002 諾貝爾/Tversky 1996 歿、Howard 1966/EVSI、Keeney–Raiffa 1976、損失趨避 meta-analysis）。展望參數的再現性以 2024 meta-analysis 為 hedge 依據。優先採一級／權威來源（Econometrica/QJE/JRU 出版頁、SEP、諾貝爾官網、Springer、Wikipedia 主條目交叉核對）。*
