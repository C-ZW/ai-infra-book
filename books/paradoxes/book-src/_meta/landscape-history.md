# 悖論事實基準表（Verified Fact Baseline for Paradox Book）

> 內部參考文件。經五組獨立對抗式查證（WebSearch/WebFetch，2026-07 執行），交叉比對 Wikipedia、Stanford Encyclopedia of Philosophy (SEP)、MacTutor、原始論文 PDF、法院判決書。**⚠️ 標記＝無法獨立確認或來源互相矛盾之處，寫作時務必照該處措辭留餘地，不要把圓整的數字／日期當定論寫死。** 章節作者請把本表當地面真值（ground truth）。

---

## Part I — 條件機率家族（蒙提霍爾譜系）

### 1. 蒙提霍爾問題（Monty Hall Problem）

- **首次正式陳述**：Steve Selvin，《The American Statistician》vol. 29（1975 年 2 月、8 月兩封讀者信）；第二封是「Monty Hall problem」名稱首度見於印刷品。
- **推廣者／爭議引爆點**：Marilyn vos Savant，《Parade》「Ask Marilyn」，**1990 年 9 月 9 日**（⚠️ 有次級來源誤記 9 月 2 日，以 9 月 9 日為準）。
- **標準答案**：換門 → **2/3**；不換 → 1/3。**前提**：主持人知情、必開一扇未被選且是山羊的門、且必提供交換。前提變則答案不必然鎖在 2/3。
- **可重演爭議**：vos Savant 自稱收到約 **10,000 封**信、近 1,000 封博士簽名、約 92% 說她錯。⚠️ **這些數字是她本人自述、未經第三方稽核**，寫成「她的說法」。名句 "You blew it, and you blew it big!" 出自 Robert Sachs 教授（後道歉）。《紐時》頭版：John Tierney, 1991-07-21。Erdős 據載看模擬才信服 ⚠️（單一傳記來源 Hoffman 1998）。
- **前身**：Bertrand 盒子（1889）；Monty Hall／三囚犯／Bertrand 盒子三者數學同構。
- 來源：en.wikipedia.org/wiki/Monty_Hall_problem ; en.wikipedia.org/wiki/Marilyn_vos_Savant

### 2. 三囚犯問題（Three Prisoners Problem）
- **originator**：Martin Gardner，《Scientific American》"Mathematical Games"，**1959 年 10 月**（早 Selvin 16 年）。
- **答案**：P(A 獲赦) 維持 **1/3**；P(C 獲赦) 升至 **2/3**。因 P(獄卒說 B∣A 赦)=1/2、∣C 赦)=1、∣B 赦)=0 → A:C=1:2。
- 與蒙提霍爾、Bertrand 盒子同構。
- 來源：en.wikipedia.org/wiki/Three_prisoners_problem

### 3. 貝特朗盒子悖論（Bertrand's Box Paradox）
- **originator**：Joseph Bertrand，《Calcul des probabilités》(Paris, **1889**)。
- **答案**：三盒（金金／銀銀／金銀），見金後同盒另一面也是金 = **2/3**。以 6 枚硬幣個別等機率想：3 枚金中 2 枚屬金金盒。
- ⚠️ **與「貝特朗弦悖論」（#22）是兩個不同問題**，同出 1889 同書同作者，最易混寫，務必分開。
- 來源：en.wikipedia.org/wiki/Bertrand%27s_box_paradox

### 4. 男孩女孩問題（Boy or Girl Paradox）
- **originator**：Martin Gardner，《Scientific American》，**1959 年 10 月**。原兩問：「較大是女孩→都女孩」答 1/2；「至少一個男孩→都男孩」原答 1/3。
- ⚠️ **核心爭議（勿當定論）**：Gardner 後來自承第 2 問**有歧義**，答案取決於「至少一個是男孩」這資訊**如何取得**（從所有 ≥1 男孩家庭隨機挑 → 1/3；挑一戶再隨機揭露一個是男孩 → 1/2）。Bar-Hillel & Falk (Cognition 1982) 主張未指定抽樣程序時此題**本質欠定（ill-posed）**。
- **星期二男孩**：Gary Foshee，2010 G4G9 提出，廣傳答案 **13/27**，但**只在特定可爭論抽樣假設下成立** ⚠️（無一手逐字稿）。寫成「標準假設下的標準答案」，標明詮釋依賴。
- 來源：en.wikipedia.org/wiki/Boy_or_girl_paradox ; Bar-Hillel & Falk 1982

### 5. 偽陽性悖論／基率謬誤（False-Positive / Base-Rate Fallacy）
- ⚠️ **無單一 originator**：現象由 Meehl & Rosen (1955) 記述，Kahneman & Tversky 自 1973 起實驗研究（代表性捷思）。「base rate fallacy」確切鑄詞者查無。
- **標準教學算例**：盛行率 1%、敏感度 99%、特異度 99% → 10,000 人中真陽 99、假陽 99 → P(病∣陽)=**50%** ⚠️（教學裝置，無具名論文出處）。
- **本書採用之算例**：盛行率 **1/1000**、敏感度＝特異度 **99%** → P(病∣陽)=(0.001·0.99)/(0.001·0.99+0.999·0.01)≈**9.02%**（此為本書基準 B3–B5；戲劇性更強：99% 準的檢測、陽性也只 9%）。
- **有敘事力的具名案例**：David Eddy (1982) 調查 100 位醫師，乳癌盛行率 1%、敏感度 80%、假陽 9.6% → 正確 P(癌∣陽)≈**7.8%**，多數醫師估 70–80%。⚠️「95/100」數字未直接核對原始書章。
- 來源：en.wikipedia.org/wiki/Base_rate_fallacy ; Bar-Hillel 1980

### 6. 檢察官謬誤（Prosecutor's Fallacy）
- **命名／形式化**：Thompson & Schumann,《Law and Human Behavior》11(3), **1987**。錯誤本身遠早於此。
- **Sally Clark 案**：1999-11-09 判謀殺兩嬰兒罪。小兒科醫師 Roy Meadow 作證兩嬰皆死於 SIDS 機率 **1/7,300 萬**（由單次 1/8,543 平方而得）。**兩個錯**：(a) 平方假設兩死**獨立**（同家庭共享基因/環境，錯）；(b) 把 P(證據∣無辜) 當 P(無辜∣證據)（真正的「檢察官謬誤」，RSS 指出）。**2003 年撤銷定罪** ⚠️（口頭撤銷/獲釋 2003-01-29 vs 書面判決 R v Clark [2003] EWCA Crim 1020 於 2003-04-11，指不同事件，須指明）。RSS 聲明 2001-10-23。⚠️ 引 1/8,500 或 1/8,543 要釘住一個。
- 來源：en.wikipedia.org/wiki/Sally_Clark ; R v Clark [2003] EWCA Crim 1020

---

## Part II — 期望值與賭博

### 7. 生日問題（Birthday Problem）
- ⚠️ **originator 有爭議**：首度**發表**分析 = Richard von Mises, 1939（伊斯坦堡）；常歸 Davenport (~1927) 但從未發表、無存世文件（民俗級，勿當事實）。
- **標準數字**：**23 人 → P(共生日)≈0.507297（50.73%，本書 B7）**；57 人 ≈ 99%；70 人 ≈ 99.9%。算式 P(無共)=365!/[(365−n)!·365ⁿ]，n=23 首度跌破 0.5。
- 生日攻擊：Gideon Yuval, 1979（技術），⚠️「birthday attack」名稱是否此文鑄造不明。
- 來源：en.wikipedia.org/wiki/Birthday_problem

### 8. 賭徒輸光問題（Gambler's Ruin）
- ⚠️ **須與「分賭金問題」區分**：分賭金（problem of points）= Pascal–Fermat 通信 **1654**（機率論誕生，Pascal 回信 1654-10-27）。**賭徒輸光（吸收隨機漫步，不同問題）**溯及 **1656** 一封信 ⚠️（確切日/傳遞路徑不確定）。
- **首度出版**：Christiaan Huygens, 1657,《De Ratiociniis in Ludo Aleae》（史上第一本機率論專著），賭徒輸光是其「第五問」。⚠️ Huygens 是否解出第五問是史學爭論。通式由 de Moivre 1712 給出。「gambler's ruin」一詞遠晚於 1657。
- **標準結果（公平 p=q=1/2）**：起始 i、總彩池 N → 破產機率 **q_i = 1 − i/N = (N−i)/N**（本書 B8）。
- 來源：en.wikipedia.org/wiki/Gambler%27s_ruin ; Huygens 譯本 probabilityandfinance.com

### 9. 賭徒謬誤／熱手謬誤（Gambler's & Hot-Hand Fallacy）
- **賭徒謬誤—蒙地卡羅 1913**：輪盤連開黑 **26 次**，多數記 **1913-08-18**，機率≈1/6,840 萬。⚠️ **所有來源溯及同一現代次級鏈（終至 BBC 2015）**，無 1913 一手佐證；寫作留餘地（"as the story is usually told…"）。
- **熱手—Gilovich, Vallone & Tversky 1985**（《Cognitive Psychology》17(3)）：分析 NBA 未見「命中提高下一球命中率」證據，結論熱手是認知錯覺。
- ⚠️ **Miller & Sanjurjo 2018 修正（務必寫準）**（《Econometrica》86(6)）：GVT 用的統計量含**有限樣本選擇偏誤**（短序列以「連中後條件於再中」計數，即使真獨立期望也向下偏）。修正並重分析 GVT 原資料後估計顯示**有意義的正相關**。**正確措辭**：「1985 的證偽本身有統計瑕疵，修正分析暗示效應可能真的存在」，**不要**寫「熱手已證實為真」。
- 來源：en.wikipedia.org/wiki/Gambler%27s_fallacy ; Miller & Sanjurjo 2018 (Econometrica)

### 10. 聖彼得堡悖論（St. Petersburg Paradox）
- **首度提出**：**Nicolaus I Bernoulli**（1687–1759），**1713-09-09** 致 Montmort 信 ⚠️（家族有三位 Nicolaus，寫信者是 Nicolaus I）。
- **首度正式發表之解**：**Daniel Bernoulli, 1738**,《Commentarii Academiae … Petropolitanae》Tomus V——發表於聖彼得堡帝國科學院院刊，**此即悖論名稱之由來**（非賭局地點）。⚠️ 拉丁草稿早至 1731。Daniel 解＝**對數效用**（邊際效用遞減）。
- **算式**：擲到第 k 次正面賠 2^k、機率 (1/2)^k → 期望 = Σ 2^k·(1/2)^k = Σ 1 = **∞**（本書 B10）。
- **跨書一致性**：與《在不確定中下注》(decide) 一致。
- 來源：plato.stanford.edu/entries/paradox-stpetersburg/

### 12. 帕隆多悖論（Parrondo's Paradox）
- **originator**：Juan M. R. Parrondo，**1996** 設計（未出版演講 "How to cheat a bad mathematician"）。首度印刷命名：Harmer & Abbott,《Nature》402:864 (1999-12)；完整處理《Statistical Science》14(2) (1999)。
- **結構**：賽局 A：偏硬幣 p₁=½−ε（輸）。賽局 B：資本相依——資本可被 M（常 3）整除時用壞硬幣 p₂=1/10−ε，否則好硬幣 p₃=¾−ε（整體亦輸）。**交替 A、B（如 AABB 或隨機選）淨贏**。⚠️ **並非每種交替都贏**——嚴格 ABAB 仍可能輸。
- 來源：en.wikipedia.org/wiki/Parrondo%27s_paradox ; Harmer & Abbott 1999

---

## Part III — 決策理論與機率哲學（多屬未定論）

### 11. 兩個信封悖論（Two-Envelope Paradox）
- ⚠️ **無單一 originator**：前身 = Maurice Kraitchik《Mathematical Recreations》(1942/43，領帶/錢包版)；Littlewood 1953 紙牌版（歸功 Schrödinger ⚠️ 僅 Littlewood 轉述）；Gardner 1982 推廣；Nalebuff 1988–89／Broome 1995 決策理論形式化。
- **正確解**：樸素論證 E(另一封)=½(2A)+½(A/2)=1.25A **不一致地對待 A**（同時當定額與隨機變數）。**有限、可正規化先驗下，正確條件化後換信封期望增益 = 0（已定、無爭議）**。⚠️ **只有不當／無界先驗版本才「未解」（SEP）；勿把有限教科書版與無限版混為一談**。
- 來源：en.wikipedia.org/wiki/Two_envelopes_problem ; SEP infinity/decision-problems

### 21. 睡美人問題（Sleeping Beauty Problem）
- **originator**：⚠️ 首度提出（弱歸屬）Arnold Zuboff「1980 年代中期」未出版 ⚠️（僅次級來源）；名稱據稱 Stalnaker，1999 rec.puzzles 熱議 ⚠️；**帶入主流標準 2 天版 = Adam Elga,《Analysis》60(2), 2000**（主張 **1/3**）。
- **兩派**：Thirder（Elga 2000）P(正)=1/3（三個不可辨醒來情境）；Halfer（David Lewis,《Analysis》61(3), 2001）P(正)=1/2（醒來未獲新證據）。
- ⚠️ **未解**，形式知識論活躍問題；**勿把任一方寫成已定「正確」**。SEP 無獨立條目，收於 "Epistemic Paradoxes"。
- 來源：princeton.edu/~adame/papers/sleeping/sleeping.pdf ; SEP epistemic-paradoxes

### 25. 紐康難題（Newcomb's Problem）
- **originator**：William A. Newcomb（物理學家），約 **1960** 構思 ⚠️（無一手文件、從未發表）。**首度哲學陳述／推廣**：Robert Nozick, "Newcomb's Problem and Two Principles of Choice"，⚠️ **日期歧義 1969 vs 1970**（哲學慣引 1969，書目編 1970；寫成引用歧義）。Gardner 推廣：《Scientific American》**1973 年 7 月**。
- **設定**：預測者已放好 A 盒（透明 $1,000）、B 盒（不透明：預測「只拿 B」則 $100 萬，預測「拿兩盒」則 $0）。**CDT → two-box**（選擇無法因果影響已做預測）；**EDT → one-box**（選擇是 B 盒內容的證據）。⚠️ **決策論活躍爭議、無共識**。
- 來源：Nozick 原文 PDF ; SEP decision-causal

### 15. 意外絞刑／突擊考試悖論（Unexpected Hanging / Surprise Exam）
- ⚠️ **民俗起源**：1940 年代初口傳；常歸瑞典數學家 Lennart Ekbom（1943/44 瑞典電台）⚠️（無一手佐證）。SEP 指逆向消去推理早在 1756 德國民間故事已現。
- **首度印刷**：D. J. O'Connor,《Mind》57(227), 1948。關鍵回應：Quine,《Mind》62(245), 1953（缺陷在學生不能真的**知道**宣告為真）。
- ⚠️ **真正未解**——80 年活躍爭議，無公認標準解。「首度提出（口傳）」vs「首度印刷（O'Connor 1948）」vs「已解（從未）」三者勿混。
- 來源：SEP epistemic-paradoxes ; en.wikipedia.org/wiki/Unexpected_hanging_paradox

---

## Part IV — 知識、共同知識與歸納

### 13. 紅藍眼睛島民／共同知識（Blue-Eyed Islanders / Common Knowledge）
- ⚠️ **謎題歸屬薄弱**：「藍眼島民」特定包裝**無確認學術 originator**（Tao 2008、xkcd 2015 皆無歸屬）；**勿歸給 Littlewood**——確認的是 Littlewood 1953 含一個結構相同的謎題（火車廂三髒臉女士），且他自稱「當時已廣為人知」。
- **共同知識—正式概念**：Morris Friedell (1969，據 SEP 為**首度數學分析**，早於下二者卻少被引)；David Lewis《Convention》(1969，首度完整**哲學**分析，無限層級)；**Robert Aumann,《Annals of Statistics》4(6), 1976**（首度嚴格賽局論形式化，同意定理）。Aumann 2005 諾貝爾 ⚠️（表彰整體貢獻，勿寫「因 1976 那篇」）。
- **邏輯結構**：n 位藍眼各見他人不見自己；「有人藍眼」是**互知**非**共知**；外來者公開陳述把互知轉共知；n 位藍眼在**第 n 天**同時離島（本書 B11：藍眼 **100** 人、第 **100** 天）。
- ⚠️ Friedell 1969 優先權被低報；若引「Lewis 1969 首創」宜補。
- 來源：SEP common-knowledge ; terrytao.wordpress.com blue-eyed-islanders

### 14. 泥巴小孩／髒臉問題（Muddy Children / Dirty Faces）
- ⚠️ **古老民俗，最早源不確定**：最早確認 = Kraitchik 1942/43（三髒臉哲學家）；Littlewood 1953；Gamow & Stern《Puzzle-Math》1958（不忠妻子版）。「泥巴小孩」之名與正式同步宣告處理由 Fagin/Halpern/Moses/Vardi《Reasoning About Knowledge》(MIT, 1995) **系統化（非發明）**。
- **與藍眼島民同構**：同一 n 輪歸納、同需公開宣告把互知轉共知。解：唯一髒孩第 1 輪答「是」；m 個髒孩在第 m 輪同時答「是」。
- ⚠️ Van Ditmarsch, arXiv:2606.13703 (2026-06) 較臆測宣稱（Dirac's Riddle、Church 傳聞）作者自標不確定，當線索非定論。「最早印刷」誠實講不能比「至少 1942」更精確。
- 來源：arxiv.org/abs/2606.13703 ; Reasoning About Knowledge (MIT)

---

## Part V — 分散式系統與統計反直覺

### 16. 兩位將軍問題（Two Generals' Problem）
- ⚠️ **originator（不可能性證明，1975）**：E. A. Akkoyunlu, K. Ekanadham, **R. V. Huber**，"Some Constraints and Trade-offs…"，Proc. 5th ACM SOSP (1975)。**⚠️ 第三作者姓 Huber，不是 Huang**（ACM DL/dblp 一致）。1975 用「幫派（gangsters）」框架、證不可能。
- **命名（1978）**：Jim Gray, "Notes on Data Base Operating Systems" (LNCS 60, 1978) 改鑄為「將軍」並命名。**1975 首度證明（幫派版），1978 命名（Gray）**——Wikipedia 自標常見誤歸。
- **結果**：可丟訊息的通道上，任何協定都無法讓雙方無條件確定同時行動（最後一則訊息永遠無法被確定確認）。
- 來源：dl.acm.org/doi/10.1145/800213.806523

### 17. 辛普森悖論（Simpson's Paradox）
- ⚠️ **命名史最常寫亂**：正式首度陳述 = Edward H. Simpson,《JRSS-B》13(2), 1951（**Simpson 本人未用「paradox」一詞**）；更早前身 Pearson (1899)／Yule (1903)（別名 Yule–Simpson effect）；**鑄「Simpson's paradox」= Colin Blyth,《JASA》67(338), 1972**（晚 Simpson 21 年）。**命名紀念的人既非最早發現、也非自己命名**。
- **UC Berkeley 案例**：Bickel, Hammel, O'Connell,《Science》187(4175), 1975。整體錄取率男 **44%**、女 **35%**（男 **8,442**、女 4,321 申請，合計 12,763）；按系所細分後女性略有利。（更正 2026-07-01：原誤記男 12,763，但 12,763 是男女合計、男性單獨為 8,442——經 R UCBAdmissions 與 Science 摘要核實。）⚠️ 教科書常過度簡化；原論文僅約 85/101 系所詳析，用「乾淨例子」宜留餘地。
- 來源：SEP paradox-simpson ; Science 1975 ; Blyth 1972

### 18. 非傳遞骰子（Non-Transitive Dice）
- **originator**：Bradley Efron（1970 年前數年，⚠️ 確切年不可考）；首度公開 = Gardner,《Scientific American》1970 年 12 月。
- **四顆 Efron 骰（已確認）**：A: 4,4,4,4,0,0；B: 3,3,3,3,3,3；C: 6,6,2,2,2,2；D: 5,5,5,1,1,1。
- ⚠️ **性質須寫準**：每顆以機率恰 **2/3** 打敗**環中下一顆**（A→B→C→D→A）；**但並非所有配對皆 2/3——C 打敗 A 的機率是 5/9**。**若寫「每一配對都 2/3」須修正**。
- **Grime dice** 是**不同、較晚**的 5 顆一組構造（beats 排序隨在場骰數變），非 Efron 重包裝。
- 來源：en.wikipedia.org/wiki/Nontransitive_dice

### 19. 孔多塞悖論（Condorcet Paradox）
- **originator**：Marquis de Condorcet,《Essai …》(Paris, **1785**)。
- **結果**：即使每位選民偏好可遞移，對 3+ 選項的成對多數投票可產生**循環社會偏好**（A>B>C>A），無孔多塞贏家。
- **Arrow 不可能定理**：《Social Choice and Individual Values》(1951)；**1972 諾貝爾**（與 Hicks 分享）。3+ 選項時無社會福利函數能同時滿足：無限制定義域、（弱）Pareto、無關選項獨立性（IIA）、非獨裁。
- 來源：SEP social-choice ; en.wikipedia.org/wiki/Social_Choice_and_Individual_Values

### 20. 布雷斯悖論（Braess's Paradox）
- **originator**：Dietrich Braess, "Über ein Paradoxon aus der Verkehrsplanung",《Unternehmensforschung》12, **1968**（德文）。
- **結果**：自私（Nash/Wardrop）路由網路中，加一條邊（即使零成本）可**增加**均衡總旅行時間，雖系統最優路由不會因加容量變差。
- ⚠️ **真實案例流行科普常誇大**：Stuttgart 1969（軼事、無硬統計）、NYC 42 街 1990（單一 NYT 文、未量測）、首爾清溪川 2003（**很可能是誘發需求/Downs–Thomson，非真 Braess**，須標爭議）；**唯一嚴謹同儕審查案例 = Youn, Gastner & Jeong,《PRL》101, 128701 (2008)**（模型預測，非觀測歷史事件）。
- 來源：Braess 1968 PDF (ruhr-uni-bochum) ; en.wikipedia.org/wiki/Braess%27s_paradox

---

## Part VI — 連續機率、數論與集合論

### 22. 貝特朗弦悖論（Bertrand Paradox — chord）
- **originator**：Joseph Bertrand, 1889（與盒子悖論同書）。**與盒子悖論（#3）明確不同**。稱「paradox」據載歸 Poincaré ⚠️。
- **三種「隨機」給三答案**：隨機端點 → **1/3**；隨機半徑 → **1/2**；圓盤內隨機中點 → **1/4**。皆在各自程序下不「錯」——「無差異原則」在連續空間未良好定義的經典示範。
- **Jaynes 解**：《Foundations of Physics》3(4), 1973——加尺度/平移不變性（最大熵/變換群）得唯一解 P=1/2；**是加不變性假設後的一個解**，未消解「均勻隨機」本身的哲學歧義。⚠️ SEP 無獨立條目。
- 來源：en.wikipedia.org/wiki/Bertrand_paradox_(probability) ; Jaynes 1973

### 23. 班佛定律（Benford's Law）
- **首度提出**：**Simon Newcomb**,《American Journal of Mathematics》4(1), 1881（對數表前頁磨損更甚）。**獨立再發現/推廣**：**Frank Benford**,《Proc. APS》78(4), 1938（跨 ~20 資料集實證）。
- **公式**：P(d)=log₁₀(1+1/d)。**P(1)=log₁₀2≈30.10%（本書 B12）**，遞減至 P(9)≈4.6%。（1→30.1、2→17.6、3→12.5、4→9.7、5→7.9、6→6.7、7→5.8、8→5.1、9→4.6%。）
- **法務會計**：Nigrini 推廣。⚠️ **法庭採認須寫準**：United States v. Channon 的 Benford 裁定只在**地院 Daubert 層級**（2015-10-28，裁定可採）；**廣傳引「881 F.3d 806 (10th Cir. 2018)」為採認先例是錯的**——該上訴意見完全未討論 Benford。Benford 只標示「值得進一步調查的異常」，非詐欺證明；受限值域/選票資料不適用。
- 來源：Newcomb 1881 PDF ; Benford 1938 PDF

### 24. 巴拿赫–塔斯基悖論（Banach–Tarski Paradox）
- **originator**：Stefan Banach & Alfred Tarski,《Fundamenta Mathematicae》6, 1924（建於 Hausdorff 1914 之上）。
- **陳述**：ℝ³ 實心球可分為**有限個**碎片，僅經剛體運動（旋轉+平移）重組為**兩個與原球等大**的球（維度 ≥ 3 皆成立）。
- ⚠️ **最少碎片數 = 5**（Robinson 1947，證 5 足且 <5 不足）；「von Neumann 9／Sierpiński 8」說無一手佐證，標未證實。
- ⚠️ **對選擇公理的依賴須寫準**：ZF 單獨或 ZF+DC 皆不可證（確需超出標準分析的選擇原則）；但**不需完整 AC**——Pawlikowski (1991) 證 ZF+Hahn–Banach 即可導出（嚴格弱於 AC）。**寫「需超出 DC 的某種選擇」，勿寫「完整 AC 為最小需求」或「B-T ⟺ AC」**。
- **純集合論、非物理**：碎片是**不可測集**（無良定義體積）；與物質/能量守恆無關；「可實際切球得兩球」是範疇錯誤。
- 來源：eudml.org/doc/214280 ; en.wikipedia.org/wiki/Banach%E2%80%93Tarski_paradox

---

## 整體注意事項（寫作最易寫錯的 8 點）

1. **蒙提霍爾**：「10,000 封信／1,000 位博士」是 vos Savant 自述、非稽核事實；日期 **1990-09-09**；Erdős 軼事單一傳記來源。都標「據載／她說」。
2. **兩位將軍第三作者是 Huber，不是 Huang**；1975 用「幫派」框架證不可能，「將軍」名與框架是 Gray 1978——證明與命名是兩件事、兩年份、兩批人。
3. **辛普森命名史**：Simpson (1951) 既非最早發現（Yule 1903/Pearson 1899 在前）、也非自己命名（Blyth 1972 才以他為名）；Simpson 本人未用「paradox」。最常被寫亂。
4. **熱手別過度反轉**：寫「1985 的證偽本身有有限樣本偏誤，修正後暗示熱手可能真的存在」，**不要**「熱手已證實為真」。賭徒謬誤「蒙地卡羅 1913」只溯及單一 BBC 來源，須留餘地。
5. **男孩女孩/星期二男孩是欠定問題**（Bar-Hillel & Falk 1982）：1/3、1/2、13/27 都依賴未言明的抽樣程序；寫成「特定詮釋下的標準答案」+ 公開的方法論爭議。
6. **四個「未解」哲學悖論別寫成有標準答案**：睡美人（thirder/halfer 未定）、兩個信封（僅無限先驗版未解、有限版已解，勿混）、意外絞刑（80 年活躍爭議）、紐康（CDT/EDT 未定）。
7. **多個 originator 是薄弱民俗歸屬、最早源自己都不認**：藍眼島民（非確歸 Littlewood，且他說「當時已廣知」）、泥巴小孩（至少 1942 Kraitchik，更早不可考）、意外絞刑（Ekbom/瑞典電台無一手）、兩個信封（Schrödinger 僅 Littlewood 轉述）、睡美人（Zuboff「1980 年代中期」僅次級）。寫「民俗，首度印刷源為 X，很可能更早」。
8. **兩個精確技術點常寫錯**：(a) **非傳遞骰子非每對都 2/3**——C 對 A 是 **5/9**，只有四個環相鄰對是 2/3；(b) **Banach–Tarski 不需完整 AC**（Hahn–Banach 即足、DC 不足），最少 **5** 片（Robinson），純集合論非物理。另：**貝特朗盒子（#3, 硬幣）與貝特朗弦（#22, 圓）是兩個不同問題**，同書同作者最易互相混寫；**SEP 無睡美人、貝特朗弦的獨立條目**。

---

**查證方法附註**：本表由五組平行對抗式研究彙整，各組獨立以 WebSearch/WebFetch 交叉比對一手論文、SEP、MacTutor、法院判決書。凡標 ⚠️ 者為無法獨立確認或來源分歧；重大更正（Huber 非 Huang、Benford 881 F.3d 806 誤引、非傳遞骰子 5/9、B-T 不需完整 AC）已直接抓一手來源核實。章節作者印刷前對自有館藏權限二次核對期刊卷期／DOI。
