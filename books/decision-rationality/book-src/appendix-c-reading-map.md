# 附錄 C — 閱讀地圖

> **這份附錄做什麼**：把全書攤成一張地圖，再給你幾條依興趣的捷徑、一份指向書架鄰書的跨書連結與理性三角的完整分工、以及一份去重後的延伸閱讀總清單。你不必從 ch01 一路爬到 ch18——這裡告訴你：想懂某件事，該走哪幾章；讀完某章想往外走，該翻哪本姊妹書、哪篇原始論文。

---

## 全書地圖重述

下面這張圖你在每個 Part 首章（ch01／ch05／ch08／ch13／ch16）都見過（「◄ 你在這裡」逐 Part 往下移）。這裡完整攤開，當作全書的索引：

```text
全書地圖：理性許下一套漂亮的演算法（你該怎麼選），現實在簡單的賭局前把它一條條掀翻（人怎麼選）

  Part I  理性的地基 .............. 從「該怎麼選」的最小公設出發
     ch01 一個賭注與一次檢查（脊椎登場）
     ch02 期望值與它的陷阱（聖彼得堡）
     ch03 期望效用：為何效用不是金額（vNM 公理、凹＝風險趨避）
     ch04 風險不是不確定（Knight、Ellsberg 模糊趨避）
        |
        v
  Part II  信念與證據 ............. 把「不確定」變成可更新的數
     ch05 貝氏決策：信念 × 效用 → 行動（檢查線登場）
     ch06 先驗從哪來：信念可以有數學
     ch07 資訊的價值：要不要再驗一次
        |
        v
  Part III  描述的裂縫 ........... 人實際怎麼選：展望理論
     ch08 參考點：你算的是變化不是狀態
     ch09 損失趨避與機率權重
     ch10 框架效應：同一個決策兩種問法
     ch11 Allais 悖論：獨立公理斷在哪
     ch12 描述還是規範：展望理論到底證明了什麼
        |
        v
  Part IV  有限理性 ............. 把最佳化放回成本有限的腦
     ch13 有限理性與 satisficing（Simon）
     ch14 多屬性決策：當權衡不只一個維度
     ch15 序貫決策：決策樹與沉沒成本
        |
        v
  Part V  收束 ................. 五種演算法，同一個決策
     ch16 對手會反應時：交棒給賽局
     ch17 理性是什麼：規範與描述的和解
     ch18 同一個決策，五種演算法重看（收官）
```

這本書的脊椎，是同一個帶不確定性的決策（賭注線＋檢查線），被七層重看直到 ch18 對帳。ch18 那張五層總對帳表，就是全書的終點口試：

```text
五層對帳：同一個賭注 L=(+200,0.5;−100,0.5)，五種眼光，兩個層次

  層次       演算法         賭注 L 的答案     層次歸屬
  ───────────────────────────────────────────────────────
  ①期望值    E[L]=+50      ⇒ 接             規範（ch02）
  ②期望效用  EU=8.66<10   ⇒ 拒（風險趨避）  規範（ch03）
  ③貝氏EU    後驗×效用矩   ⇒ 最適行動       規範（ch05）
  ④展望理論  |v(−100)|>v(+200) ⇒ 拒（損失重） 描述（ch09）
  ⑤有限理性  satisficing   ⇒ 定性門檻，不同類  橋接（ch13）
             （「值不值得算到展望理論這麼細？」）
  ───────────────────────────────────────────────────────
  ⑤不是第五個競爭答案，而是「要不要把前四個都算」的元層決策。
```

同一道裂縫（規範 vs 描述），五種長相，從「期望值給你正確的平均」走到「展望理論說人實際上在用另一套數學」，再到「有限理性說你可能根本不必把每種演算法都跑完」。

---

## 依興趣的選讀路徑

不想 18 章順著爬？下面五條捷徑各帶你去一個明確的目的地。每條都自成一個故事，讀完那幾章就夠回答標題那個問題。

```text
路徑 A：只想懂「為什麼拒絕正期望值的賭注是理性的」
   ch01 → ch02 → ch03 → ch18（第②列）
   先立框架（ch01），再看期望值在聖彼得堡崩壞（ch02），
   再看效用把它補回來、凹效用讓拒絕賭注變成理性（ch03），
   最後在收官章的對帳表第②列確認這個答案。
   最短的「懂風險趨避」路線。

路徑 B：只想懂「貝氏決策：收到告警後該不該行動」
   ch01 → ch05 → ch07 → ch18（第③列）
   先立框架與檢查線懸念（ch01），再算後驗 16.7%＋接效用矩陣
   求最適行動（ch05），再問「要不要再蒐集一次資訊」（ch07），
   最後在 ch18 對帳第③列。貝氏三部曲，缺哪章都不完整。

路徑 C：想懂「展望理論到底在說什麼、和期望效用什麼關係」
   ch03 → ch08 → ch09 → ch11 → ch12
   先把規範（凹效用）的精確意義弄清楚（ch03），
   再一根一根立展望理論的支柱（ch08 參考點、ch09 損失趨避與機率權重、
   ch11 Allais 獨立公理），最後看 ch12 把兩套理論的關係說清楚。
   「描述 vs 規範，為何不互相否證」的完整論證。

路徑 D：想懂「有限理性與 satisficing，工程上的決策該怎麼收」
   ch13 → ch14 → ch15 → ch17 → ch18（第⑤列）
   先看「夠好就停」在元層次上為何可能就是最佳化（ch13），
   再看多屬性選型的陷阱（ch14），再看決策樹倒推與沉沒成本（ch15），
   然後看哲學收束「理性的兩個意思」（ch17），最後確認 ch18
   第⑤列把 satisficing 放在「不同類」的那一格。

路徑 E：想了解「本書和書架上其他書的邊界在哪」
   ch01（全書地圖）→ ch04（模糊趨避，邊界與《賽局》）
   → ch12（交棒給《思考的陷阱》）→ ch16（交棒給《賽局》）
   → ch17（理性三角完整分工）
   閱讀目的是搞清楚「哪些問題在本書、哪些要去哪本鄰書」。
```

---

## 跨書連結整理：理性三角與書架鄰居

本書在「推理六書」家族中承擔的角色是**規範基準**——「單人在不確定下該怎麼選」的完整數學。遇到不同問題就指向書架上相鄰的書，不重推那一側的內容。

### 理性三角的三個頂點

```text
理性三角：同一個決策失誤，三本書各負責一個視角

  失誤案例：P0 alert 響，on-call 因基率忽視誤判「九成有病」，
            採取了錯誤行動。
  ─────────────────────────────────────────────────────────────
  本書（決策）         規範：P(病|陽)=16.7%（不是 99%），
                       後驗×效用矩陣=最適行動；
                       人「該」怎麼算，哪個步驟錯了。
  ─────────────────────────────────────────────────────────────
  《思考的陷阱》（偏誤）  描述：為什麼人腦看不見先驗——
                           可得性捷思讓「檢測陽性」的生動性
                           壓過了「基率」這個抽象數字；
                           雙系統為何讓你察覺不到。
  ─────────────────────────────────────────────────────────────
  《如何不騙自己》（科學方法） 制度：設計什麼流程讓這種偏誤
                               在「系統層面」不會發生——
                               postmortem 模板的「後驗計算欄」、
                               alert 觸發時強制顯示盛行率。
  ─────────────────────────────────────────────────────────────
  三本不互相否證：規範告訴你標準，偏誤告訴你為何偏離，
                 科學方法告訴你制度怎麼補這道缺口。
```

本書的明確交棒點：
- **ch12**（展望理論收束）：偏離的數學描述本書收了；**偏離的心理機制指向《思考的陷阱》**。
- **ch16**（對手會反應）：**單人決策交棒給《賽局》**——納許均衡、混合策略、機制設計在那裡。
- **ch17**（理性是什麼）：**理性三角總收束**，三本書的分工最後講清楚。

### 各書邊界速查

```text
問題是什麼                                  去哪本書
─────────────────────────────────────────────────────────────────
「在不確定下，單人該怎麼選」                  本書（已收完）
   期望效用、貝氏決策、資訊的價值
   展望理論的數學、有限理性的決策後果
─────────────────────────────────────────────────────────────────
「機率是怎麼算的、貝氏定理的推導」            《馴服隨機》
   條件機率機制、自然頻率法的嚴格版           （本書 ch05–07 只用結果）
   大數法則為何讓期望值有意義
─────────────────────────────────────────────────────────────────
「人為什麼會偏離規範、心理機制是什麼」        《思考的陷阱》
   雙系統、捷思怎麼運作、錨定、框架的          （ch08、ch09、ch12、ch13 交棒）
   心理成因、為何察覺不到
─────────────────────────────────────────────────────────────────
「當對手也是理性主體、會針對我反應時」        《賽局：當理性互相碰撞》
   納許均衡、混合策略、機制設計、              （ch04、ch16 交棒）
   重複賽局、承諾、可信威脅
─────────────────────────────────────────────────────────────────
「信念更新作為科學確證、制度怎麼防自欺」      《如何不騙自己》
   貝氏確證、頻率派之爭的制度面               （ch05、ch06、ch17 互指）
   可重現性、預先承諾
─────────────────────────────────────────────────────────────────
「凹效用的微分直覺、Jensen 不等式的圖像」    《馴服無限》
   凹凸函數、邊際遞減的導數版               （ch03、ch08 點到指向）
─────────────────────────────────────────────────────────────────
```

### 三個招牌跨書連結（總綱 §2.3 定義的）

1. **決策↔賽局**：單人理性決策（本書）與多人策略互動（《賽局》）是同一枚硬幣兩面；分水嶺在「那個讓你不確定的東西，會不會針對你反應」。本書 ch04（模糊趨避）、ch10（框架與對手）、ch16（交棒）、ch18（收官）各明寫一次。

2. **決策↔偏誤**：展望理論的數學描述（本書 Part III）與偏誤的心理機制（《思考的陷阱》）是同一道裂縫的兩面。本書 ch12 是第一個明確交棒點，ch17 是總收束。

3. **信念更新的兩個視角**：本書（ch05–07）從「信念→行動」的決策演算法角度用貝氏；《如何不騙自己》從「信念→真理」的科學確證角度用貝氏。兩者互指，不重推對方的核心。

---

## 延伸閱讀總清單（去重彙整）

以下條目從各章「延伸閱讀」段去重、合併，按主題分組。連結在 2026-06 查證過；標 ⚠️ 者為估計值或時效性項，定期需回頭確認。

### 原典與史料

**Daniel Bernoulli, "Exposition of a New Theory on the Measurement of Risk"（1738，英譯 1954，*Econometrica* 22(1):23–36）**
效用概念與對數效用的歷史出生證明；讀它如何用「財富的效用」而非「財富本身」化解聖彼得堡悖論，是「效用不是金額」這套思想的源頭。（ch02/03）

**von Neumann & Morgenstern, *Theory of Games and Economic Behavior*（1944；期望效用公理化在 1947 二版附錄）**
規範那一側的原典。期望效用公理的形式內容在附錄 "The Axiomatic Treatment of Utility"（常被誤記成 1944，見 ch03 的直覺的陷阱）。感受「幾條公理逼出唯一演算法」的規範之美。（ch03/16）

**Frank Knight, *Risk, Uncertainty and Profit*（1921）**
風險／不確定區分的源頭（Online Library of Liberty 有全文）。讀第一篇第一章掌握那條界線；後面的利潤理論可略。（ch04）

**Daniel Ellsberg, "Risk, Ambiguity, and the Savage Axioms," *Quarterly Journal of Economics* 75(4):643–669（1961）**
三色甕出自這裡。讀前三節即可看懂全部論證，數學門檻不高、文筆極好。（ch04）

**Maurice Allais, "Le Comportement de l'homme rationnel devant le risque…," *Econometrica* 21(4):503–546（1953）**
Allais 悖論的原始論文（法文）。即使讀不動全文，看他怎麼設計兩題來「狙擊」美國學派的公理也值得。（ch11）

**Frank Ramsey, "Truth and Probability"（1926 撰，1931 身後出版，收錄於 *The Foundations of Mathematics*）**
主觀機率「用賭率測量信念」這個想法的出生地；把信念度 translated 成可觀察的下注行為。（ch06）

**Leonard Savage, *The Foundations of Statistics*（Wiley, 1954）**
主觀期望效用的完整框架；sure-thing principle 出自這裡；Ellsberg 正是對它的反例。（ch04/06）

**Herbert A. Simon, "A Behavioral Model of Rational Choice"（*Quarterly Journal of Economics*, 1955）**
satisficing 與 aspiration level 的原始論文，是 ch13 一切的源頭。（ch13）

**Herbert A. Simon, *Administrative Behavior*（1947）**
有限理性最早成形的地方，從組織內決策角度切入。（ch13）

### 展望理論

**Kahneman, D. & Tversky, A., "Prospect Theory: An Analysis of Decision under Risk," *Econometrica* 47(2):263–291（1979）**
（https://www.econometricsociety.org/publications/econometrica/1979/03/01/prospect-theory-analysis-decision-under-risk）
展望理論出生證明，也是史上被引用最多的 Econometrica 論文；讀它如何把自己定位成**描述**理論（"a critique of expected utility theory as a descriptive model"）。（ch08/09/11/12）

**Tversky, A. & Kahneman, D., "Advances in Prospect Theory: Cumulative Representation of Uncertainty," *Journal of Risk and Uncertainty* 5(4):297–323（1992）**
（https://link.springer.com/article/10.1007/BF00122574）
累積展望理論（CPT），α=β=0.88、λ=2.25、γ=0.61、δ=0.69 這些數字的出處；讀「the value function」與「the weighting function」兩節，但記得這是估計值不是常數。⚠️（ch09/12）

**⚠️ Walasek, Mullett & Stewart, "A meta-analysis of loss aversion in risky contexts," *Journal of Economic Psychology* 103（2024）**
（https://www.sciencedirect.com/science/article/pii/S0167487024000485）
對 λ≈2.25「偏高」的整合分析，給出 λ≈1.31（CI 1.10–1.53）；讀它來校準「展望參數不是常數」的直覺（2026-06；全書最需定期回頭確認的一條）。（ch09/12/18）

**Tversky, A. & Kahneman, D., "Loss Aversion in Riskless Choice: A Reference-Dependent Model," *Quarterly Journal of Economics* 106(4):1039–1061（1991）**
（http://bear.warrington.ufl.edu/brenner/mar7588/Papers/tversky-kahneman-qji1991.pdf）
參考點依賴的直白版；兩個在最終財富上完全相同的選項因參考點不同而偏好翻轉。（ch08）

**Tversky, A. & Kahneman, D., "The Framing of Decisions and the Psychology of Choice," *Science* 211:453–458（1981）**
框架效應與亞洲疾病問題的原始論文；短、清楚、數學門檻低。（ch10）

**Tversky, A. & Kahneman, D., "Rational Choice and the Framing of Decisions," *Journal of Business* 59(4)（1986）**
把描述不變性的規範地位講透的那篇；「沒有理論能同時規範充分又描述準確」這句全書級結論的出處。（ch10）

### 貝氏決策與資訊價值

**Ronald A. Howard, "Information Value Theory," *IEEE Transactions on Systems Science and Cybernetics* SSC-2(1):22–26（1966）**
（https://en.wikipedia.org/wiki/Expected_value_of_perfect_information）
EVPI 與「資訊價值＝機率 × 後果」的原始形式化；讀它看見這套理論如何刻意和 Shannon 資訊理論分家。（ch07）

**Howard Raiffa & Robert Schlaifer, *Applied Statistical Decision Theory*（1961）**
EVSI 與貝氏決策分析的奠基之作；「決策樹倒推 + 資訊價值」的完整工程化版本。（ch07/15）

**Howard Raiffa, *Decision Analysis: Introductory Lectures on Choices under Uncertainty*（1968）**
決策樹與倒推（rollback）的經典入門；「先探測再決定」如何系統化成樹。（ch15）

**Casscells, Schoenberger & Graboys, "Interpretation by Physicians of Clinical Laboratory Results," *New England Journal of Medicine*（1978）**
（https://www.nejm.org/doi/full/10.1056/nejm197811022991808）
基率忽視的招牌實驗——哈佛醫師最常答 95%（正確約 2%）；體會這是人類認知的系統性盲點。（ch05）

**Gigerenzer & Hoffrage, "How to Improve Bayesian Reasoning Without Instruction," *Psychological Review*（1995）**
自然頻率法為何讓正確率大幅提升的理論根據；你日後要跟非技術同事解釋偽陽性時的最佳武器。（ch05）

### 多屬性決策

**Ralph Keeney & Howard Raiffa, *Decisions with Multiple Objectives: Preferences and Value Tradeoffs*（Wiley, 1976；Cambridge 1993 再版）**
多屬性效用理論的奠基之作；看「偏好獨立／效用獨立」這些條件何時讓加權加總合法、何時必須改用乘法合成。（ch14）

**Peter Fishburn, *Utility Theory for Decision Making*（1970）**
加權加總法的「偏好獨立 ⇒ 可加分解」表現定理的嚴格版；行有餘力才翻。（ch14）

### 沉沒成本

**Hal Arkes & Catherine Blumer, "The Psychology of Sunk Cost," *Organizational Behavior and Human Decision Processes* 35（1985）：124–140**
沉沒成本謬誤的代表性實驗論文（劇院季票、滑雪票這些經典情境出自這裡）；看「人確實會被沉沒成本綁架」的乾淨實驗設計。（ch15）

### 賽局理論（邊界外的指引）

**Thomas Schelling, *The Strategy of Conflict*（1960）**
謝林點、承諾、可信威脅的原典；ch16 交棒後的第一站。（ch16）

**Stanford Encyclopedia of Philosophy, "Game Theory"**
（https://plato.stanford.edu/entries/game-theory/）
納許均衡、不動點、混合策略的嚴謹但可讀的入門；深入指向《賽局》全書。（ch16）

### 概覽與科普

**Stanford Encyclopedia of Philosophy, "Decision Theory"**
（https://plato.stanford.edu/entries/decision-theory/）
規範與描述決策理論的權威概覽；「三要素＋規範/描述」的學術版，也有序貫決策與有限理性的段落。（ch01/11/15）

**Stanford Encyclopedia of Philosophy, "The St. Petersburg Paradox"**
（https://plato.stanford.edu/entries/paradox-stpetersburg/）
本書 ch02 史實的主要依據；讀「History」看 Nicolaus 1713 致 Montmort、Daniel 1738、Cramér；讀「Bounded utility」看效用為何沒真正終結悖論。（ch02）

**Stanford Encyclopedia of Philosophy, "Dutch Book Arguments"**
（https://plato.stanford.edu/entries/dutch-book/）
把「信念自洽 ⇔ 滿足機率公理」說清楚；ch06 Dutch book 一節的主要依據。（ch06）

**Stanford Encyclopedia of Philosophy, "Interpretations of Probability"**
（https://plato.stanford.edu/entries/probability-interpret/）
想看頻率派 vs 主觀派 vs 其他詮釋的完整地圖；對照 ch06「機率這個詞在扛兩個不同工作」的說法。（ch06）

**Daniel Kahneman, *Thinking, Fast and Slow*（2011，中譯《快思慢想》）**
展望理論作者本人寫給一般讀者的集大成之作；本書收的是「偏離的數學描述」，這本收的是「偏離的心理機制與作者本人的反省」（他承認研究一輩子照樣中招）。ch08 進入展望理論前翻一翻它的第四部（Choices）會很有感。（ch01/17/18）

**MIT News, "Explained: Knightian uncertainty"（2010）**
一頁科普，講 Knight 的區分為什麼在 2008 金融危機後重新被重視；快速複習「為什麼這條線到今天還重要」。（ch04）

**Data Colada, "[11] 'Exactly': The Most Famous Framing Effect Is Robust To Precise Wording"**
方法學部落格，檢驗亞洲疾病問題在精確措辭後是否仍穩健（結論：是）；想知道這個經典實驗在再現性風暴後站不站得住就讀它（hedge：部落格非論文，但作者群是知名方法學者）。（ch10）

**Gerd Gigerenzer 等人，"fast-and-frugal heuristics" 研究系列**
把 Simon 的有限理性接到「簡單規則在對的環境裡為何能勝過複雜模型」的現代延伸；讀「捷思不是次優、是生態理性」的論證，與本書 satisficing 觀點同調。（ch13）

---

## 給讀完全書的你：一道出口題

你走到這裡，手上有五副眼鏡、兩個層次、一道裂縫。最後一個問題不是要你查書的：

**挑你最近做過的一個決定（可以是技術選型、可以是要不要 rollback、可以是一次資源分配），用這五副眼鏡各看一遍：**

1. 期望值怎麼說？
2. 如果有隱含的效用函數，它是凹的嗎？拒絕正期望值的賭注是風險趨避的展現，還是真的判斷失誤？
3. 你的先驗是什麼？看完資料（log、指標、測試結果）後後驗更新到哪裡？後驗 × 後果矩陣指向哪個行動？
4. 你的決定有沒有被框架（措辭、別人怎麼描述）或參考點（上一版的水準、上季的目標）推著走？
5. 你把分析做到哪一格停手？那個停手點，是 satisficing 還是偷懶？

如果能對另一個工程師把這五個問題的答案講清楚，你就通過了這本書的口試。不需要答案完美——需要的是知道自己在哪個框架裡算。
