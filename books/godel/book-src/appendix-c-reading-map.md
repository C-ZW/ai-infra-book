# 附錄 C — 閱讀地圖

> **這份附錄做什麼**：把全書攤成一張地圖，再給你幾條依興趣的捷徑、一份指向書架鄰書的跨書連結、以及一份去重後的延伸閱讀總清單。你不必從 ch01 一路爬到 ch16——這裡告訴你：想懂某件事，該走哪幾章；讀完某章想往外走，該翻哪本姊妹書、哪篇原始論文。

---

## 全書地圖重述

下面這張圖你在每個 Part 首章（ch01、ch04、ch07、ch09、ch14）都見過一次（「◄ 你在這裡」逐 Part 往下移）。這裡把它完整攤開，當作整本書的索引：

```text
全書地圖：希爾伯特想造一台算盡數學的機器，哥德爾如何用一句指涉自己的話拆穿它

  Part I  機械之夢 .............. 形式系統是什麼、希爾伯特想要什麼、真與可證憑什麼分家
     ch01 機械的證明（形式系統＝符號遊戲）
     ch02 希爾伯特的夢（完全機械化、可判定）
     ch03 真，不等於可證
        |
        v
  Part II  自我指涉的引擎 ....... 把自爆的悖論改造成不完備的武器
     ch04 說謊者與它的修正（這句話是假的 → 這句話不可證）
     ch05 把句子變成數字（哥德爾編碼，借《乘法的原子》FTA）
     ch06 對角化：造出說「我不可證」的句子 G
        |
        v
  Part III  兩聲驚雷 ............ 脊椎句 G 引爆
     ch07 第一不完備定理（G 真但不可證）
     ch08 第二不完備定理（系統證不了自己一致）
        |
        v
  Part IV  孿生與邊界 .......... 同一極限的另一張臉，以及它到底在說什麼
     ch09 停機問題（圖靈的孿生子）
     ch10 不可判定的群島（決定問題、邱奇、可計算性的版圖）
     ch11 沒有終點（補洞長新洞）
     ch12 G 到底真在哪（標準模型與「真」的精確意義）
     ch13 逃得掉的系統（完備又可判定的反例）
        |
        v
  Part V  與極限共處 .......... 濫用解剖、根岑的回應、收官
     ch14 哥德爾說了什麼、沒說什麼（濫用大解剖）
     ch15 根岑的回應（超限歸納把一致性外包）
     ch16 同一句 G，現在你層層讀懂它（收官）
```

這本書的脊椎，是同一句自我指涉的話 G（「G 在本系統 F 內無法被證明」）。它每進一個 Part 換一張臉、被搭高一層，ch16 把五層身份全攤成一張總對帳表——那就是全書的終點口試：

```text
脊椎句 G 的五種身份（ch16 對帳表簡版）

  身份① 白話版 ......... 「G 在本系統 F 內無法被證明。」              ch04 成形
  身份② 形式等價版 ..... F ⊢ G ↔ ¬Prov_F(⌜G⌝)                    ch06 造出
  身份③ 算術句 ......... ¬∃y. Proof_F(y, ⌜G⌝)（純算術命題）        ch05 鋪路
  身份④ ℕ 中為真 ....... ℕ ⊨ G（在標準模型中確定為真）             ch07 引爆/ch12 釘死
  身份⑤ F 中不可證 ..... F ⊬ G（且 F ⊬ ¬G，後者需 ω-一致或羅瑟）  ch07 引爆
```

身份④ 說「真」，身份⑤ 說「證不到」——兩者在同一句話上分了家，那就是不完備的全部核心。

---

## 選讀路徑

不同的興趣起點，不同的最短路徑。

### 路徑一：只想懂第一不完備定理

最短路徑（必讀，約 6 章）：

```text
ch01 → ch03 → ch04 → ch05 → ch06 → ch07
（形式系統）→（真≠可證）→（說謊者換字）→（哥德爾編碼）→（對角化）→（引爆）
```

跳過 ch02（希爾伯特計畫）和 ch08–ch16 也能理解第一定理的骨架；但 ch02 能讓你感受到為什麼這一刀這麼痛，建議帶上。

### 路徑二：想懂兩條定理（含第二定理「系統自證一致」那把刀）

在路徑一之上加：

```text
→ ch08（第二定理）
```

ch08 的前置是 ch07 + ch05 裡對 HBL 的直覺；建議按順序讀到 ch08 再停。

### 路徑三：想懂停機問題與不完備的孿生關係

在路徑一之上加：

```text
→ ch09（停機問題）→ ch10（可計算性版圖，選讀）
```

ch09 讀完，你會看到「P 會停嗎」和「G 可證嗎」如何用同一招對角化歸謬拆穿——那是本書最驚豔的同構之一。

### 路徑四：想讀懂「G 真」究竟什麼意思

在路徑一之上加：

```text
→ ch12（標準模型與真的精確意義）
```

如果讀完 ch07 還覺得「G 說它不可證，但它怎麼能說自己真？」——答案在 ch12。

### 路徑五：想解剖流行的哥德爾引用

最短路徑（需要前置）：

```text
ch01 → ch03 → ch07 → ch14
（地基）→（真≠可證）→（第一定理）→（濫用解剖）
```

ch14 用三條件當尺，量出流行引用合法在哪、越界在哪一步；需要先懂第一定理才能拿住那把尺。

### 路徑六：想懂根岑如何「外包一致性」

需要先讀路徑二（懂第二定理），再加：

```text
→ ch15（根岑的回應）
```

ch15 是全書罕見的「正面故事」——希爾伯特的夢死了，但故事不是純粹失敗；根岑精確量化了「要多少外部資源才能擔保 PA 一致」。

### 路徑七：走完全書的收官口試

按 Part 順序走完 ch01–ch16，最後在 ch16 把脊椎句 G 的五層身份全對帳一遍——那是「我真的懂了這本書」的收尾。

---

## 跨書連結整理

這本書把對應的深層機制指向書架上相鄰的書，而不是自己重推一遍。下面是所有跨書連結的匯整：

### 《乘法的原子：數論與質數》（本套鄰書，招牌連結）

- **連結點**：ch05（哥德爾編碼）明寫「這裡借的是《乘法的原子》的算術基本定理」——質因數分解唯一（FTA）是哥德爾數可逆的引擎；沒有 FTA，編碼就算不出唯一解碼，整個機制就塌了。
- **也在**：ch06（對角化的「解碼」步驟站在 FTA 上）、ch09（D 能拿到自己的編碼 ⌜D⌝）、ch13（Presburger 因無乘法連質數都定義不了，所以握不住這把鑰匙）。
- **指向**：質數本身的性質、無窮性、分布——那本的核心領土，本書全部指向它、不重推。

### 《思考的陷阱：邏輯謬誤與認知偏誤》（本套鄰書）

- **連結點**：ch14（濫用大解剖）負責「定理的精確邊界在哪、越界在哪一步」；但「為什麼人愛把技術詞當日常詞偷渡」的**心理機制**——把「不完備」當「不完美」、把「不可判定」當「見仁見智」背後的認知偏誤——那是《思考的陷阱》的核心領土，指向它。
- **也在**：ch02（希爾伯特計畫的過度樂觀一面）、ch07（G 為真卻「感覺」不知道對錯——直覺的陷阱第一種）。

### 《如何不騙自己：科學方法》（本套鄰書）

- **連結點**：ch03（真 vs 可證）的對照版：「科學的真 vs 已驗證」——數學的「⊨」和科學的「被實驗支持」是兩種不同的「確定」，本書在 ch03 點這個對照、把科學那一面指向它。
- **也在**：ch14 濫用裡「哥德爾推翻科學」的那條越界，ch15 把一致性「外包給更可信的原則」的哲學餘味。

### 《把系統寫成定理》TLA+（書架既有）

- **連結點**：ch01（形式系統＝機械符號遊戲）的工程化對照：TLA+ 的 model checker 也是不理解語意、只機械搜狀態；「規格 ＋ 機械檢查器」的精神與本書的符號遊戲同調。
- **也在**：ch09（半可判定）、ch13（刻意設計得不夠強以換取可判定——TLA+ 刻意限制表達力讓 model checker 跑得動）。
- **注意**：本書不依賴它；讀過更有感，沒讀也能理解。

### 《馴服無限：微積分》（書架既有）

- **連結點**：ch06（對角化）的 Cantor 對角線直覺、ch12（非標準模型）的「無窮大自然數」——這些牽涉可數與不可數的機制，本書點到為止，那本才展開。
- **也在**：ch15（ε₀、超限歸納、序數的無限嵌套——良序與可數無限的直覺）。

### 「理性三角」分工（本套推理六書的跨書分工）

本書（godel）在推理六書裡的定位是「形式系統的可證性極限」；相鄰書各管一個角落：

```text
《這句話無法被證明》（本書）
  ── 形式系統的極限：可證 vs 真、兩條不完備定理、停機問題

《乘法的原子》（primes）
  ── 數論的引擎：質因數分解唯一（本書 ch05 的借力點）

《思考的陷阱》（bias）
  ── 為什麼人會把技術詞當日常詞偷渡（本書 ch14 的心理學那面）

《如何不騙自己》（scimethod）
  ── 科學的「確定」vs 數學的「確定」（本書 ch03 的科學對照面）

《在不確定中下注》（decide，另一本推理鄰書）
  ── 個人在不確定下的理性選擇（與本書「可判定」互不重疊）
```

這幾本書是同一套推理直覺的不同切面，相互指引，但各自獨立。

---

## 延伸閱讀總清單（去重彙整，依主題分組）

以下是全書十六章延伸閱讀去重後的彙整；每條說明**值得讀哪裡、為什麼**。優先採有查證的連結；未查證者標（未驗證）。

### 一、入門科普（讀完本書之後、想從另一個角度再走一遍）

**Douglas Hofstadter,《Gödel, Escher, Bach: An Eternal Golden Braid》（GEB, 1979）**
全書 MIU 系統（ch01）、quine 與對角化（ch06）的直覺骨架許多借自 GEB。它把「自我指涉是引擎」這條主線玩到極致——讀它當作「同一個震撼、另一種講法」的回味。注意：它偏哲學聯想，定理精確邊界仍以 SEP 與 Franzén 為準。

**Ernest Nagel & James Newman,《Gödel's Proof》（修訂版，Hofstadter 作序）**
比本書再硬一級的證明細節，但仍是科普範圍；把 ch05–ch08 那條鏈（編碼→對角化→第一定理）用一百多頁從頭講透。想要骨架之外的細部，讀這本。

### 二、權威免費參考（隨時查、不必整本讀）

**Stanford Encyclopedia of Philosophy（SEP），"Gödel's Incompleteness Theorems"**
https://plato.stanford.edu/entries/goedel-incompleteness/
本書整整十六章最常引用的單一參考。真 vs 可證、三條件、ω-一致、羅瑟改進、HBL 條件、G 為真的標準模型意義——每個精確點都在這裡有嚴格版。可根據章節需求只讀對應小節。

**Stanford Encyclopedia of Philosophy，"Hilbert's Program"**
https://plato.stanford.edu/entries/hilbert-program/
ch02 四根柱子的骨架來源；也收根岑之後希爾伯特計畫以什麼形式存活（ch15 的學界定位）。讀「The Program」、「The Impact of Gödel's Theorems」、「Relativized Hilbert's Program」三節。

**Stanford Encyclopedia of Philosophy，"The Church-Turing Thesis"**
https://plato.stanford.edu/entries/church-turing/
ch10 最該守準的參考：論題 vs 定理的分界、三個計算模型等價性的說明。

**Stanford Encyclopedia of Philosophy，"The Logic of Provability"**
https://plato.stanford.edu/entries/logic-provability/
ch08 進階：把 Prov_F 當成模態運算子（□）研究的證明邏輯（GL）；HBL 條件在這裡長成模態公理，Löb 定理是明星。

**SEP，"Tarski's Truth Definitions"**
https://plato.stanford.edu/entries/tarski-truth/
ch03/ch04/ch12 的「真不可定義」根源；讀「真不可定義」與「可證可表達」的不對稱那一段。

### 三、「濫用解毒」的標準參考（ch14 的武器庫）

**Torkel Franzén,《Gödel's Theorem: An Incomplete Guide to Its Use and Abuse》（2005, A K Peters）**
本書 ch14 濫用解剖的權威聖經。神學、反機械論、後現代三大濫用區都在這裡被拆穿；想把 ch14 那把尺磨得更利，從這本開始。收官後第一本該讀的書。

**Alan Sokal & Jean Bricmont,《Fashionable Nonsense / Intellectual Impostures》（1997/1998）**
「術語挪用」的經典批判，ch14 (d3) 後現代濫用的主要出處。看他們如何拆解把「不確定性」「相對性」「不完備」修辭性盜用的後現代文本。

**Internet Encyclopedia of Philosophy，"The Lucas-Penrose Argument about Gödel's Theorem"**
https://iep.utm.edu/lp-argue/
Lucas–Penrose 論證與其反駁的權威整理。讀「human consistency 假設」那節——本書指出的「缺的那個前提」在這裡被哲學界正式提出。（2026-06：仍無共識結局。）

### 四、定理細節（比本書硬一級，指向技術讀者）

**Wikipedia，"Proof sketch for Gödel's first incompleteness theorem"**
https://en.wikipedia.org/wiki/Proof_sketch_for_G%C3%B6del%27s_first_incompleteness_theorem
把 ch07 主菜「F ⊢ G ⇒ 矛盾」寫成逐步形式版；想看更形式化的展開從這裡進。

**Wikipedia，"Rosser's trick"**
https://en.wikipedia.org/wiki/Rosser%27s_trick
羅瑟句如何把 ω-一致減弱為只需一致的精確機制；ch07 的配菜細節。

**Wikipedia，"Diagonal lemma"**
https://en.wikipedia.org/wiki/Diagonal_lemma
ch06 的對角化引理：歸屬（Gödel 1931 特例、Carnap 1934 一般化）、別名、與塔斯基不可定義性和 Löb 定理的關係。

**SEP，"Gödel's Incompleteness Theorems — Supplement: Gödel Numbering"**
https://plato.stanford.edu/entries/goedel-incompleteness/sup1.html
ch05 哥德爾編碼的標準參考；讀三層編碼（符號→公式→證明）與「語法謂詞變算術謂詞」的精確處理。

**SEP，"Gödel's Incompleteness Theorems — Supplement: The Diagonalization Lemma"**
https://plato.stanford.edu/entries/goedel-incompleteness/sup2.html
ch06 對角化引理的嚴格陳述與證明骨架。

### 五、可計算性與停機問題（ch09–ch10 的深化）

**Wikipedia，"Turing's proof"**
https://en.wikipedia.org/wiki/Turing%27s_proof
圖靈原始論文證的是「circle-free 不可判定」、機器 H 算不出自己的數字；「停機問題」這個名字是後世所加。ch09 的出處細節。

**Charles Petzold,《The Annotated Turing》**
逐句注解圖靈 1936 論文的世界級導讀；圖靈機、circle-free、對角化、決定問題如何串起來的細部還原。想從圖靈原文層面補完 ch09 的骨架，讀這本。

**Wikipedia，"Entscheidungsproblem"**
https://en.wikipedia.org/wiki/Entscheidungsproblem
決定問題的精確陳述、Hilbert–Ackermann 1928 的提出、與 Church/Turing 1936 的否決時間線；ch10 的史實骨架。

**Wikipedia，"Rice's theorem"**
https://en.wikipedia.org/wiki/Rice%27s_theorem
「程式的任何非平凡語意性質都不可判定」——你對「完美靜態分析器不存在」的工程直覺的精確邊界；讀它看「語意性質 vs 語法性質」的區分（後者仍可能可判定）。

**Wikipedia，"Post correspondence problem"**
https://en.wikipedia.org/wiki/Post_correspondence_problem
不可判定群島裡「形狀最簡單、最常當歸約跳板」的一座島；ch10 的群島地圖素材。

**Wikipedia，"Hilbert's tenth problem"**
https://en.wikipedia.org/wiki/Hilbert%27s_tenth_problem
MRDP 定理（Matiyasevich 1970）把不可判定性釘進數論腹地——「丟番圖方程有整數解嗎」無通用判定法。ch10 群島裡最有數論感的一座島。

### 六、逃得掉的系統（ch13 的反例）

**Wikipedia，"Presburger arithmetic"**
https://en.wikipedia.org/wiki/Presburger_arithmetic
本章主角的標準條目。讀「沒有乘法 ⇒ 完備、可判定」與「為什麼這不違反哥德爾」兩段。

**Fischer & Rabin，"Super-Exponential Complexity of Presburger Arithmetic"（1974）**
https://link.springer.com/chapter/10.1007/978-3-7091-9459-1_5
「可判定不等於跑得動」的原始證據：雙重指數下界 2^(2^(cn))——原則上有判定程序，實務上不可用。

**Wolfram MathWorld，"Tarski's Theorem"**
https://mathworld.wolfram.com/TarskisTheorem.html
實閉體可判定、初等幾何可判定的簡潔說明。

### 七、根岑與序數分析（ch15 的深化）

**Wikipedia，"Gentzen's consistency proof"**
https://en.wikipedia.org/wiki/Gentzen%27s_consistency_proof
根岑 1936 一致性證明的史實細節，特別是「PRA ＋ ε₀ 超限歸納不含 PA，PA 也不含它，互不包含」這個關鍵點——不違反第二定理的原因。

**Gerhard Gentzen，"Die Widerspruchsfreiheit der reinen Zahlentheorie"**
Mathematische Annalen 112 (1936), 493–565
https://link.springer.com/article/10.1007/BF01565428
根岑的原始論文（德文）。不必逐行讀，知道它在哪、卷頁為何，遇到需要引用原文時回來。

**John Carlos Baez，"Large Countable Ordinals (Part 1–2)"**
https://johncarlosbaez.wordpress.com/2016/06/29/large-countable-ordinals-part-1/
對 ω、ω^ω、ε₀ 建立真正視覺直覺的最好讀科普；數學家寫的，讀到 ε₀ 那段就夠 ch15 用。

**Wikipedia，"Paris–Harrington theorem"**
https://en.wikipedia.org/wiki/Paris%E2%80%93Harrington_theorem
1977 年第一個「自然的 PA-獨立命題」——一個真實的組合數學命題，PA 卻證不出；ch11「系統塔的洞裡有真正數學」的具體例子。

**Alan Turing，"Systems of Logic Based on Ordinals"（1939）**
https://en.wikipedia.org/wiki/Systems_of_Logic_Based_on_Ordinals
圖靈博士論文——「正面強攻無限補洞」的早期嘗試，為什麼連圖靈都讓洞從序數編號裡冒回來；ch11「補洞長新洞」的另一個視角（技術細節極硬，看概覽即可）。

### 八、原始論文（歷史感優先，技術細節硬）

**Kurt Gödel（1931），"Über formal unentscheidbare Sätze der Principia Mathematica und verwandter Systeme I"**
Monatshefte für Mathematik und Physik, 卷 38, 頁 173–198
https://link.springer.com/article/10.1007/BF01700692
原始論文（德文，有英譯）。想直接感受「這件事是在 1931 年真實發生的，而且就是這樣寫的」，從這裡進；技術細節以 SEP 補充節為輔助。

**Alan M. Turing（1936），"On Computable Numbers, with an Application to the Entscheidungsproblem"**
Proceedings of the London Mathematical Society, Series 2, 卷 42, 頁 230–265
https://londmathsoc.onlinelibrary.wiley.com/doi/abs/10.1112/plms/s2-42.1.230
圖靈 1936 論文，引入圖靈機與停機問題（雖然「停機問題」之名是後世所加）；成文 1936、卷標 1937、另有 1937 勘誤。
