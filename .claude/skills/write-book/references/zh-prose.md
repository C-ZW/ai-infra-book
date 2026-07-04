# zh-TW 措辭契約（prose contract for Traditional-Chinese books）

Applies to every zh-TW book, all forms. The chapter-writer template makes
writers read this file; P1 merges `forms/zh-prose.lint.json` into the book's
lint config so the worst patterns surface as WARN. These are style rules —
the linter warns, a human (or reviewer agent) decides; never mass-replace on
a hit (pitfalls rule 4).

## 原則：白話直述，動詞優先

寫給人讀的中文，不是譯稿。判斷標準：一句話唸出聲，像不像一個懂行的人
在對同行說話。像論文摘要或翻譯腔，就重寫。

## 禁止的翻譯腔模式（lint 以 WARN 偵測）

| 模式 | 改法 | 例 |
|---|---|---|
| 「進行／加以」＋動作名詞 | 直接用動詞 | 進行分析 → 分析 |
| 「透過…的方式」 | 用／靠／以 | 透過快取的方式加速 → 用快取加速 |
| 「在…的情況下」 | 當／若／…時 | 在高負載的情況下 → 高負載時 |
| 「對於…而言」 | 對… | 對於讀者而言 → 對讀者 |
| 「存在著」 | 有 | 存在著三種寫法 → 有三種寫法 |
| 「是…的」空殼斷言連用 | 拆掉空殼 | 這是很重要的 → 這很重要 |
| 「作為（一個）…」開頭 | 換主語直述 | 作為一個佇列，它… → 這個佇列… |

## 節奏與句構

- 一段一個論點；說理長句之後接一個短句落點。
- 名詞化堆疊（「…的…的…的」三連以上）拆句。
- 被動「被」只在受事者是焦點時用；平常用主動。
- 每個代名詞（它／這／其）要能立刻指認對象，指認不了就寫出名詞。

## 個人材料規則（校準用，不入內文）

Profile 目錄裡的文件（背景、履歷、目標、偏好）只用來校準「讀者已知什麼、
要學什麼、用什麼口吻」。**讀者的個人經歷、任職公司、做過的專案，一律不
寫進書的內文** ——除非使用者明確要求。需要具體場景時，用一般化的場景
（「一個推播管線」「一家中型電商的結帳服務」），不用讀者自己的系統。
（既有教訓：概念書要向外不向內。）
