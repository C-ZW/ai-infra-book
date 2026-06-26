# 《思考的陷阱》— 事實基準表（landscape, 2026-06）

> 本檔是全書的**事實錨點**。每一章的歷史、人名、年份、實驗設定、效果量、**複製狀態**都必須與此一致；要改任何基準值，先改這裡、再同步全書、並在 maintenance.md 掃描日誌記一行。
> 規則：每條都帶「驗證值／一句註記／來源 URL」。無法以可信來源確認者標 ⚠️ 並說明原因。時效性敘述加註 (2026-06)。
> **本書的時效風險異常高**：與數論/混沌那種「數學恆真」不同，本書大量引用**心理學實驗的效果量與複製狀態**，而再現性危機仍在演進。鐵律：(1) 引用任何經典實驗必標其複製狀態；(2) 嚴格區分「未能複製」≠「確定造假/確定不存在」，多數是「效果遠小於原始/受脈絡強烈調節」；(3) 凡「某效果已被推翻/質疑」必標 (2026-06)、必 hedge。**禁止把「未複製成功」當鐵打事實**（這條本身就是本書與《科學方法》呼應的核心教材）。
> 本檔由帶網路研究流程查證（2026-06-20，16 次 web 檢索涵蓋全部脆弱事實）。邏輯恆真項（四推論有效性、合取律方向）不靠本檔但寫章時自我複核。

---

## 一、捷思與雙系統（綱領、年份、設定）

### 1.1 雙系統 System 1 / System 2（脊椎框架）
- **驗證值**：康納曼（Daniel Kahneman）2011《Thinking, Fast and Slow》普及了 System 1（快、自動、省力、無意識控制感）/ System 2（慢、費力、需專注的心智活動）的對比。**但這對術語並非康納曼首創**——史塔諾維奇（Keith Stanovich）與韋斯特（Richard West）2000 年先以 System 1 / System 2 命名；雙歷程框架本身更早。
- **一句註記**：脊椎透鏡。**誠實邊界**：這是「有用的隱喻」、不是腦裡有兩個小人、也不對應固定腦區或解剖實體——學界（含 Evans & Stanovich 2013）已轉向「Type 1 / Type 2 歷程」措辭以避免「兩個系統」的實體化誤解。書中用「系統一/二」當教學透鏡，但「直覺的陷阱」要點破實體化謬誤（見 T1）。
- **來源**：https://www.marketingsociety.com/think-piece/system-1-and-system-2-thinking ；https://en.wikipedia.org/wiki/Dual_process_theory

### 1.2 可得性捷思（availability heuristic）
- **驗證值**：Tversky & Kahneman 1973，「Availability: A Heuristic for Judging Frequency and Probability」，*Cognitive Psychology* 5:207–232。定義：靠「相關實例多容易想到」估計頻率或機率。原始示範之一：判斷英文裡 R 開頭 vs R 在第三位的字詞何者多（多數人因 R 開頭較好提取而高估）。
- **一句註記**：「對的捷思」——常見的確實好想起來；翻車在生動、近期、情緒化的被系統性高估（空難 vs 車禍直覺）。
- **來源**：https://www.sciencedirect.com/science/article/abs/pii/0010028573900339

### 1.3 代表性捷思（representativeness heuristic）
- **驗證值**：Tversky & Kahneman 1972/1973/1974 提出。定義：靠「某情境與某原型有多相似」估計機率，系統性忽略基率與樣本大小。是基率忽視（ch10）與合取謬誤（ch11）的共同引擎。
- **一句註記**：「對的捷思」——判斷「像不像」時有效；翻車在「判斷機率」時（像不像 ≠ 多可能）。
- **來源**：https://www.science.org/doi/10.1126/science.185.4157.1124

### 1.4 錨定（anchoring）
- **驗證值**：Tversky & Kahneman 1974。經典實驗：在受試前轉動一個被動過手腳、只會停在 **10 或 65** 的輪盤，再問「非洲國家佔聯合國的比例」高於或低於該數、並給出估計。**錨 10 組中位估計 25%、錨 65 組中位估計 45%**——一個明顯無意義的數字把答案拖動約 20 個百分點。
- **一句註記**：錨定**穩健、屢次複製、五十多年仍最常出現**——本書用它當「站得住的偏誤」與後面要打折的偏誤（ego depletion 等）對照，示範誠實分級。機制：不充分調整（insufficient adjustment）。
- **來源**：https://www.science.org/doi/10.1126/science.185.4157.1124 ；https://www.simplypsychology.org/what-is-the-anchoring-bias.html

### 1.5 判斷與捷思總綱
- **驗證值**：Tversky & Kahneman 1974，「Judgment under Uncertainty: Heuristics and Biases」，*Science* 185(4157):1124–1131。三捷思（可得性、代表性、錨定與調整）的綱領性論文。
- **來源**：https://www.science.org/doi/10.1126/science.185.4157.1124

---

## 二、邏輯與推理（形式謬誤、瓦森、哥德爾濫用）

### 2.1 瓦森四卡片選擇任務（Wason selection task）
- **驗證值**：瓦森（Peter Cathcart Wason）**1966** 提出的四卡片問題（測條件規則 P→Q）。抽象版**正解率 < 10%**（約 90–96% 答錯）。四種條件推論：肯定前件（MP）、否定後件（MT）有效；肯定後件（AC）、否定前件（DA）無效。受試傾向選「能證實」的卡（確認偏誤的形式版），不選能否證的「7」卡。
- **一句註記**：人類連純形式推理都系統性偏向「找證實」；具體/社會脈絡版（如「喝酒要滿 18 歲」）正解率大幅提升——脈絡能救形式推理。
- **來源**：https://en.wikipedia.org/wiki/Wason_selection_task

### 2.2 確認偏誤詞源：瓦森 1960 的 2-4-6 任務
- **驗證值**：瓦森 1960，*Quarterly Journal of Experimental Psychology*，2-4-6 規則發現任務。受試只測「符合自己假設」的正例，不主動測能否證的反例。真實規則只是「任三個遞增數」，但多數人卡在「偶數、+2」的自證迴圈。**「確認偏誤」研究路線由此開端，早於 Tversky–Kahneman 捷思綱領**。
- **一句註記**：確認偏誤的鼻祖實驗；連到 ch13 動機版。
- **來源**：https://www.tandfonline.com/doi/abs/10.1080/17470218.2014.914547 ；https://explorable.com/confirmation-bias

### 2.3 哥德爾濫用（Gödel misuse，叢集跨書連結用）
- **驗證值**：法蘭森（Torkel Franzén）2005《Gödel's Theorem: An Incomplete Guide to Its Use and Abuse》系統性整理對不完備定理的誤用；Sokal & Bricmont 1998《Fashionable Nonsense》（*Intellectual Impostures*）收錄後現代學界的濫用案例。**關鍵**：被亂套的對象（社會、心靈、後現代論述）**根本不是形式系統**——沒有形式語言、公理集、形式推論規則、可計算枚舉的定理集，因此定理不適用。
- **一句註記**：ch08 當「不當類比/訴諸權威」謬誤案例；**定理精確陳述指向《這句話無法被證明》（godel）**，本書只給「為何是濫用」。
- **來源**：https://philarchive.org/archive/ZACTFG ；https://en.wikipedia.org/wiki/G%C3%B6del%27s_incompleteness_theorems#Misconceptions

> **邏輯恆真項（不靠本檔、寫章自我複核）**：P→Q 下，肯定前件（P,∴Q）與否定後件（¬Q,∴¬P）有效；肯定後件（Q,∴P）與否定前件（¬P,∴¬Q）無效（反例：P→Q 真不代表 Q→P 真）。合取律 P(A∩B) ≤ P(A) 恆真。

---

## 三、機率直覺崩壞（基率、合取、賭徒、熱手翻案）

### 3.1 基率忽視與自然頻率法
- **驗證值**：基率忽視（base-rate neglect）＝忽略事前盛行率、只看檢驗準度/相似度（代表性捷思）。吉仁澤（Gerd Gigerenzer）等示範：把機率題改寫成**自然頻率**（「每 10 萬人中…」）能大幅提升正確率——同一題兩種表述、難度天差地別。
- **一句註記**：**機制與貝氏算法指向《馴服隨機》ch05**；本書只重述「為何直覺如此判、自然頻率為何解救」。檢察官謬誤＝混淆 P(證據|無罪) 與 P(無罪|證據)。
- **來源**：機率機制見《馴服隨機》landscape（醫檢基率基準）；自然頻率法 https://en.wikipedia.org/wiki/Base_rate_fallacy

### 3.2 Linda 合取謬誤（conjunction fallacy）
- **驗證值**：Tversky & Kahneman **1983**（*Psychological Review* 90:293–315）。Linda 描述為 31 歲、單身、直言、聰明、主修哲學、關心歧視與社會正義、參與反核遊行。問「Linda 較可能是 (a) 銀行員 還是 (b) 女性主義銀行員」。**約 85% 受試選 (b)**，違反 P(女性主義∩銀行員) ≤ P(銀行員)。機制：代表性捷思（(b) 更像 Linda 的原型）。
- **一句註記**：**受表述強烈調節**（見 T6）——以明確「機率」措辭、加輕微激勵、改用頻率版時，違反率明顯下降。書中用 85% 要標「這是原始研究、後續發現受措辭影響」。
- **來源**：https://www.sciencedirect.com/science/article/abs/pii/S0899825609001742 （後續實驗證據與激勵效應）；https://www.psychologytoday.com/us/blog/the-superhuman-mind/201611/linda-the-bank-teller-case-revisited

### 3.3 賭徒謬誤（gambler's fallacy）
- **驗證值**：認為獨立事件「連紅就該黑」「該輪到反面了」。機制：小數法則（誤以為小樣本也該像母體）＋誤把大數法則當「短期自我修正」。獨立事件無記憶，P(下一個正面)仍 1/2。
- **一句註記**：**大數法則是「稀釋」不是「修正」，機制指向《馴服隨機》ch13**。與熱手謬誤方向相反（賭徒：連紅後押黑；熱手：連中後押再中），但都源於對隨機序列的錯誤直覺。
- **來源**：https://en.wikipedia.org/wiki/Gambler%27s_fallacy

### 3.4 ⚠️ 熱手「謬誤」2018 翻案（重要誠實項）
- **驗證值**：Gilovich/Vallone/Tversky 1985 原宣稱「熱手是謬誤」（籃球連中不代表下一球更易進）。**Miller & Sanjurjo 2018**（〈Surprised by the Hot Hand Fallacy? A Truth in the Law of Small Numbers〉，*Econometrica* 86(6):2019–2047，前身 SSRN 2015）證明常用度量存在 **streak-selection bias（連續選擇偏差）**——在有限序列裡「挑出緊接連勝後的那幾球」這個動作本身會引入向下偏差。**修正此偏差後，原始研究的結論反轉：熱手效應可能真實存在。**
- **一句註記**：「連學界都被一個統計假象騙了二十多年」的活教材（ch12）。書中要守住：**賭徒謬誤仍是真謬誤；但「熱手是謬誤」這個 1985 結論已被 2018 翻案打折**——兩者別混講。
- **來源**：https://www.econometricsociety.org/publications/econometrica/2018/11/01/surprised-hot-hand-fallacy-truth-law-small-numbers ；https://arxiv.org/pdf/1902.01265

---

## 四、框架效應與展望理論

### 4.1 框架效應（亞洲疾病問題）
- **驗證值**：Tversky & Kahneman **1981**（*Science* 211:453–458）。情境：美國準備應對一場預期殺死 600 人的疫病。**存活框**：方案 A 確定救 200 人；方案 B 有 1/3 機率救全部 600、2/3 機率一個都救不到——**72% 選 A（風險趨避）**。**死亡框**（數學等價）：方案 C 確定死 400；方案 D 有 1/3 機率無人死、2/3 機率 600 人全死——多數翻轉成**風險偏好**選 D。
- **一句註記**：同一組結果、只換「救/死」描述，多數選擇翻轉。**穩健**——DataColada #11 確認此效果對精確措辭穩健。機制：正框視為收益（風險趨避）、負框視為損失（風險偏好）。
- **來源**：https://datacolada.org/11 ；https://www.cambridge.org/core/journals/judgment-and-decision-making/article/moderators-of-framing-effects-in-variations-of-the-asian-disease-problem

### 4.2 展望理論與損失趨避（規範/數學指向《決策》）
- **驗證值**：Kahneman & Tversky **1979**（〈Prospect Theory: An Analysis of Decision under Risk〉，*Econometrica* 47(2):263–291）。損失趨避：失去 X 的痛約為得到 X 的爽的 ~2 倍（係數常引 λ≈2，**精確值依研究而異、需 hedge**）；機率權重函數高估小機率、低估中大機率。
- **一句註記**：本書 ch14 只講**描述面心理機制**；**價值函數/機率權重函數/損失趨避係數的數學、Allais/Ellsberg、EU 規範基準指向《在不確定中下注》（decide）**。康納曼 2002 諾貝爾經濟學獎（特沃斯基 1996 過世、諾獎不追授）。
- **來源**：https://www.jstor.org/stable/1914185 ；損失趨避係數 https://en.wikipedia.org/wiki/Loss_aversion

---

## 五、再現性危機：經典偏誤的複製狀態（本書最敏感的時效區，全標 2026-06、全 hedge）

> **鐵律**：以下每條都嚴格區分「未能複製/效果遠小於原始」與「確定不存在/造假」。書中引用任一偏誤實驗必附其複製狀態標籤。狀態可能隨新研究演進——標 (2026-06)。

### 5.1 再現性計畫基準（Open Science Collaboration 2015）
- **驗證值**：Open Science Collaboration, 2015,「Estimating the reproducibility of psychological science」, *Science* 349(6251):aac4716。複製 **100 篇**心理研究：原始 **97% 顯著** → 複製僅 **約 36%** 達顯著、且複製效果量約為原始一半。
- **一句註記**：再現性危機的標誌性數據。書中用「約 36%」要標明這是「100 篇樣本的複製率」、不是「97% 的心理學是假的」（過度解讀陷阱）。
- **來源**：https://www.science.org/doi/10.1126/science.aac4716

### 5.2 ⚠️ ego depletion（自我耗損）
- **驗證值**：Baumeister 等 1998 提出（自制力像會耗盡的資源）。**Hagger 等 2016** 多實驗室預先註冊複製（23 lab、N=2141）：效果量 **d=0.04, 95% CI [−0.07, 0.15]——包含 0**。Dang 等 2021 用更強的耗損操弄報告了一個**小而顯著**的效果；2025 多實驗室再探（Dang et al.）顯示**操弄強度與控制任務設計關鍵**，整體**爭議未定**（2026-06）。
- **一句註記**：典型「原始大效果 → 大型複製含 0 → 後續在特定條件下找到小效果」的故事。**別寫「ego depletion 已被證偽」；寫「大型複製未能複製原始效果，是否在特定條件存在仍有爭議（2026-06）」。**
- **來源**：https://journals.sagepub.com/doi/10.1177/1745691616652873 （Hagger 2016 RRR）；https://journals.sagepub.com/doi/10.1177/18344909251386084 （Dang 2025 多實驗室）

### 5.3 ⚠️ power posing（高權姿勢）
- **驗證值**：Carney/Cuddy/Yap **2010**（N=42）宣稱擴張姿勢提升睪固酮、降皮質醇、增冒險。**Ranehill 等 2015**（5 倍樣本）**未能複製任何生理或行為效果**，僅「主觀感到有力（felt power）」重現。**2016 年原始第一作者 Carney 在 UC Berkeley 網站公開聲明「我不再相信『高權姿勢效應』為真……反證無可辯駁」。**
- **一句註記**：「原始作者親自撤回」的罕見誠實案例（ch17 招牌）。守住：**身體姿勢→主觀有力感較穩；→荷爾蒙/行為效果未能複製**。別籠統說「power posing 全是假的」。
- **來源**：https://en.wikipedia.org/wiki/Power_posing ；Carney 2016 聲明（Berkeley，經 Slate/Wikipedia 轉述）https://slate.com/technology/2016/01/amy-cuddys-power-pose-research-is-the-latest-example-of-scientific-overreach.html

### 5.4 ⚠️ 社會促發（social priming，老人步速）
- **驗證值**：Bargh 等 **1996** 宣稱用「老人」相關詞（Florida、wrinkle…）促發後，受試走出實驗室更慢。**Doyen 等 2012 未能複製**，並指原效果疑為**實驗者期望效應**（主試者無意間透過細微線索引導受試行為）。社會促發**整類**在再現性危機受重創（2026-06）。
- **一句註記**：Bargh 對失敗複製曾以部落格文〈Nothing in their heads〉激烈回應——「替自己論文辯護到惱羞」的史料（語氣素材，照實寫、別誇大）。守住：**這是「社會行為促發」的失敗，不等於否定所有 priming（如語意促發在認知心理學仍穩）。**
- **來源**：https://www.nationalgeographic.com/science/article/failed-replication-bargh-psychology-study-doyen ；https://rips-irsp.com/articles/10.5334/irsp.1036

### 5.5 ⚠️ 面部回饋（facial feedback，咬筆微笑）
- **驗證值**：Strack/Martin/Stepper **1988** 用牙齒咬筆（誘發微笑）vs 嘴唇含筆，前者把卡通評得更好笑（原始差 **≈0.82** 於 10 點量表）。**Wagenmakers 等 2016 RRR**（17 個獨立直接複製、共同協定）**meta 差僅 ≈0.03、無顯著**。**Coles 等 2019 meta** 納入「是否知道被錄影」當調節變項：面部回饋效果**小、變異大、受脈絡（如有無觀眾/錄影）調節**。
- **一句註記**：典型「原始中等效果 → 大型 RRR 趨零 → meta 顯示小而受脈絡調節」。別寫「面部回饋已被推翻」；寫「咬筆版未能複製，整體效果小且受脈絡調節（2026-06）」。
- **來源**：https://journals.sagepub.com/doi/full/10.1177/1745691616674458 （Wagenmakers 2016 RRR）；https://www.apa.org/pubs/journals/features/bul-bul0000194.pdf （Coles 2019 meta）

### 5.6 ⚠️ backfire effect（逆火效應）
- **驗證值**：早期宣稱「糾正錯誤資訊反而強化錯誤信念」。**Wood & Porter 2019**（5 個實驗、52 個議題/糾正、共 10,100 人）**未能對任何單一議題誘發 backfire**——即使議題與受試政治立場一致，糾正多半把信念**拉向**事實。現共識：backfire **罕見**，僅在攻擊極核心世界觀信念時偶現。
- **一句註記**：ch13/ch17 用——破除「跟人講道理只會更糟」的流行迷思。守住：**「糾正有效」是好消息；backfire 被大幅高估、但非絕對不存在。**
- **來源**：https://journals.plos.org/plosone/article/file?id=10.1371/journal.pone.0281140&type=printable ；https://www.tandfonline.com/（Wood & Porter 2019, *Political Behavior*）轉述見 https://link.springer.com/article/10.1186/s41235-023-00492-z

### 5.7 ⚠️ Dunning–Kruger（鄧寧–克魯格效應）
- **驗證值**：Kruger & Dunning **1999** 原宣稱「能力最差者最高估自己、最強者略低估」。**Nuhfer 等 2016/2017 與 Gignac & Zajenkowski 2020** 指出**經典那張曲線大半是統計假象**——(1) **自相關**（把測驗分數同時放進兩軸：x=實際分數、y=實際−自評，兩軸共用同一變數必然造出該斜線）＋(2) **回歸均值**。改用連續變項法後效果**大幅縮水**。
- **一句註記**：ch19 招牌。**極端版（最差者狂妄/最強者嚴重低估）被推翻；但「人普遍不擅長自我評估」這個較弱結論未被否定。** 別把「整個效應是假的」當定論——寫「經典曲線大半是統計假象（自相關＋回歸均值），但弱版的自評不準未被否定（2026-06）」。
- **來源**：https://www.researchgate.net/publication/340361120 （Gignac & Zajenkowski 2020, *Intelligence*）；https://economicsfromthetopdown.com/2022/04/08/the-dunning-kruger-effect-is-autocorrelation/

### 5.8 偏誤盲點（bias blind spot）
- **驗證值**：Pronin, Lin & Ross **2002**（*Personality and Social Psychology Bulletin*）：人傾向評自己比一般人**更少**受各種偏誤影響、對他人偏誤偵測力遠高於對自己。
- **一句註記**：ch19 核心——「你察覺不到自己正在犯」的實證；連到內省錯覺（introspection illusion，Pronin 後續工作）。此項相對未受再現性危機重創，但仍以「研究報告」措辭、別當鐵律。
- **來源**：https://journals.sagepub.com/doi/10.1177/0146167202286008

---

## 六、常被誤傳／需守住的正確版（直覺的陷阱素材，T 系列）

> 每條都是「大眾版 vs 正確版」，是「直覺的陷阱」段的素材。守住正確版。

### T1. 雙系統 ≠ 腦裡有兩個小人/兩塊腦區
- **正確版**：System 1 / 2 是**教學隱喻**，描述「快自動」與「慢費力」兩類歷程，不是兩個解剖實體、不對應固定腦區。學界（Evans & Stanovich 2013）改用「Type 1 / Type 2 歷程」以免實體化。康納曼本人在書中也明說這是擬人化的方便說法。**別寫成「大腦有兩個系統各管一塊」。**

### T2. ego depletion「已被證偽」是過度解讀
- **正確版**：大型多實驗室複製（Hagger 2016, d≈0.04 含 0）未能複製原始大效果；但後續（Dang 2021）在更強操弄下找到小顯著效果，**是否在特定條件存在仍有爭議（2026-06）**。寫「未能複製原始效果」，別寫「證明不存在」。

### T3. power posing 不是「全部是假的」
- **正確版**：荷爾蒙與行為效果未能複製、原始作者 Carney 2016 撤回；但「擺姿勢→主觀感到更有力（felt power）」相對較穩。守住分層：**生理/行為效果倒了、主觀感受效果還在。**

### T4. 社會促發失敗 ≠ 所有 priming 都假
- **正確版**：Bargh 1996 老人步速等「社會行為促發」未能複製、整類受重創；但認知心理學的**語意促發**（如看到「醫生」後更快認出「護士」）仍是穩固現象。別把兩者混為一談。

### T5. 面部回饋 ≠ 「微笑讓你快樂」被完全推翻
- **正確版**：Strack 1988 咬筆版在 17 實驗室 RRR 趨零；但 Coles 2019 meta 顯示面部回饋有**小而受脈絡調節**的效果（如是否被觀察）。寫「咬筆版未複製、整體效果小且受脈絡調節」。

### T6. Linda 合取謬誤受表述強烈調節
- **正確版**：原始約 85% 違反率是在特定措辭下；改用明確「機率」字眼、加輕微金錢激勵、或用自然頻率版重述時，違反率明顯下降。**這效果真實但不是「人類在任何表述下都這樣」的鐵律**——這個調節性本身就是個教材（措辭如何召喚不同捷思）。

### T7. 賭徒謬誤 vs 熱手「謬誤」別混講
- **正確版**：**賭徒謬誤仍是真謬誤**（獨立事件不自我修正）。但「**熱手是謬誤**」這個 1985 結論已被 Miller & Sanjurjo 2018 的 streak-selection bias 翻案——修正後熱手可能真實。兩者是不同的事：一個（賭徒）站穩，一個（熱手是謬誤）被打折。

### T8. backfire effect 被大幅高估
- **正確版**：「糾正錯誤資訊反而強化錯誤信念」其實**罕見**（Wood & Porter 2019, 52 議題 10,100 人未誘發單一 backfire），糾正多半有效。別用 backfire 替「跟人講道理沒用」背書。

### T9. Dunning–Kruger 經典曲線大半是統計假象
- **正確版**：那張「最差者最狂妄」的曲線大半源於**自相關＋回歸均值**（Nuhfer 2016/17、Gignac & Zajenkowski 2020）。極端版被推翻；但「人普遍不擅自我評估」這個弱版未被否定。別把「整個效應是假的」當定論、也別繼續用極端版當鐵打事實。

### T10. 訴諸謬誤（fallacy fallacy）
- **正確版**：「對方犯了謬誤」**不等於**「對方的結論為假」。論證爛 ≠ 結論錯（ch06 健全性 vs 有效性）。指出謬誤只證明「這個論證沒成功支持結論」，不證明結論本身。

### T11. 「相關不蘊含因果」也別矯枉過正
- **正確版**：相關確實不蘊含因果，但相關**是**因果的必要證據之一；「這只是相關所以無意義」也是一種懶惰駁斥。正確態度是去找：第三變因、反向因果、巧合——而非一句「相關≠因果」就收工（ch09，方法論指向《科學方法》）。

---

## 七、與叢集/書架相鄰書的邊界（僅供跨書指引，不需網路查證）

- **《馴服隨機》（probability）**：owner 機率機制。基率/貝氏（ch10）、合取律證明（ch11）、大數法則「稀釋非修正」（ch12）、回歸均值統計機制（ch16/ch19）一律指向它，本書只用結果與直覺。
- **《在不確定中下注》（decide，叢集）**：owner 單人規範理性。框架效應/損失趨避（ch14）的**規範基準（EU）與展望理論數學**指向它——偏誤偏離的「正確答案」在那本。
- **《如何不騙自己：科學方法》（scimethod，叢集）**：owner 制度防線。確認偏誤的「制度怎麼防」（ch13）、再現性危機的 p-hacking/預先註冊/複製率方法論（ch17）、相關 vs 因果方法論（ch09）指向它——本書收**心理機制與事實狀態**。
- **《這句話無法被證明》（godel，叢集）**：owner 哥德爾定理精確陳述。哥德爾濫用（ch08）的「定理到底說什麼」指向它，本書只給「為何是濫用」。
- **《當理性互相碰撞》（game，叢集）**：owner 多人策略。社會偏誤裡的策略情境非理性公平偏好（ch14/ch15）點到、指向它。

---

## 八、關鍵年份速查

| 事件 | 年份 |
|---|---|
| 瓦森 2-4-6 任務（確認偏誤詞源，QJEP） | 1960 |
| 瓦森四卡片選擇任務 | 1966 |
| Tversky & Kahneman〈Availability〉Cognitive Psychology 5:207 | 1973 |
| Tversky & Kahneman〈Judgment under Uncertainty〉Science 185:1124 | 1974 |
| Gilovich/Vallone/Tversky 熱手（原始） | 1985 |
| Kahneman & Tversky 展望理論 Econometrica 47:263 | 1979 |
| Tversky & Kahneman 框架效應/亞洲疾病 Science 211:453 | 1981 |
| Tversky & Kahneman Linda 合取謬誤 Psych. Review 90:293 | 1983 |
| Strack/Martin/Stepper 面部回饋（咬筆） | 1988 |
| Bargh 社會促發（老人步速） | 1996 |
| Sokal & Bricmont《Fashionable Nonsense》 | 1998 |
| Kruger & Dunning 效應 | 1999 |
| 史塔諾維奇 & 韋斯特先用 System 1/2 | 2000 |
| Pronin/Lin/Ross 偏誤盲點 | 2002 |
| Franzén《Gödel's Theorem: Use and Abuse》 | 2005 |
| Carney/Cuddy/Yap power posing | 2010 |
| 康納曼《Thinking, Fast and Slow》 | 2011 |
| Doyen 社會促發未複製 | 2012 |
| Open Science Collaboration 再現性計畫（複製率 36%） | 2015 |
| Ranehill power posing 未複製 | 2015 |
| Hagger 多實驗室 ego depletion RRR（d 含 0） | 2016 |
| Carney 公開撤回 power posing | 2016 |
| Wagenmakers 面部回饋 RRR（趨零） | 2016 |
| Miller & Sanjurjo 熱手翻案（Econometrica） | 2018 |
| Coles 面部回饋 meta（小且受脈絡調節） | 2019 |
| Wood & Porter backfire 未誘發（52 議題） | 2019 |
| Gignac & Zajenkowski Dunning–Kruger 統計假象批判 | 2020 |
| Dang ego depletion 小顯著效果（爭議未定） | 2021 |

---

## 九、待考／低信心項（⚠️，最敏感的時效區）

1. **所有再現性狀態（§5、T2–T9）（2026-06，最重要）**：心理學再現性危機仍在演進，個別偏誤的複製狀態可能隨新研究改變。**鐵律**：引用必標 (2026-06)、必 hedge、必區分「未能複製/縮水/受脈絡調節」與「確定不存在/造假」。寫新內容引用任一偏誤實驗前回查本檔 §5。
2. **損失趨避係數 λ**：常引 ≈2，但精確值依研究/領域而異，且本身有再現性討論。書中以「約兩倍」表述、數學指向《決策》。
3. **Linda 85% 違反率**：是原始特定措辭下的數字，受表述/激勵/頻率版調節（T6）。引用必標「原始研究、後續發現受措辭影響」。
4. **錨定 25%/45%**：原始輪盤實驗的中位數；錨定效應整體穩健，但確切數字是該次實驗值。
5. **OSC 2015 複製率 36%**：是「100 篇樣本」的複製率，**不等於**「64% 的心理學是假的」；不同學科/期刊複製率不同。引用要標樣本與範圍。
6. **Asch/Milgram/旁觀者效應（ch15）**：寫 ch15 前須補查證——Asch 從眾的效果量在後續/跨文化有變動；Kitty Genovese「38 個冷漠目擊者」是被誇大的都市傳說版（後經 2007 Manning et al. 修正），書中用**修正版**、別用原始報紙版。寫 ch15 時補 2–3 次 web 查證並回填本檔。
7. **同形記號歧義**（附錄 A 有專節）：→（條件「若…則」vs 推導箭頭）、P(·)（機率 vs 命題變數 P）、λ（損失趨避係數 vs 其他）。跨章引入前先回查附錄 A。

---
*掃描日期：2026-06-20。本檔由帶網路研究流程查證（16 次 web 檢索，涵蓋雙系統詞源、三捷思、瓦森、Linda、賭徒/熱手翻案、框架/展望、OSC 2015、ego depletion、power posing、社會促發、面部回饋、backfire、Dunning–Kruger、偏誤盲點、哥德爾濫用）。優先採一級/權威來源（原始論文、Science/Econometrica/PLOS、Wikipedia 條目交叉、DataColada、SEP）。本書時效風險集中於 §5 再現性狀態，須隨新研究滾動更新並於 maintenance.md 記日誌。ch15 社會偏誤的史實（Asch/Genovese）留待 P2 寫該章時補查並回填。*
