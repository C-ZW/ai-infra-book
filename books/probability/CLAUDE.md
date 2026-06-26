# CLAUDE.md

專案性質：個人書《馴服隨機：機率與統計的直覺與驚嘆》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**純直覺與欣賞、和工作無關、紙上推演**（2026-06-13 訪談定案）——讀完要有「人類竟想得出這個」的數學之美震撼、能用自己的話對工程師轉述。**新增內容不得引入任何程式碼（含 Python）**；Monte Carlo 只用文字「想像擲一萬次」描述、數值表一律手算示範。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章基準數值表**（脊椎硬幣、生日 0.5073、醫檢後驗 1.94%、二項→卜瓦松 0.3679、民調 ±3.1%、60/100 檢定 0.046/0.0569、68-95-99.7…改任何基準必須照表全書同步）、脆弱事實清單（六個兩年份陷阱、熱手 2018 翻案、信賴區間正確意義、π/α/p 同形記號）、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體與大陸詞、禁「均值」改用平均/期望值、**自然口語不要翻譯腔**）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、記號規範（純文字 Unicode、不依賴 LaTeX、多行推導進 ```text）、脊椎硬幣七層、跨書邊界。
3. `book-src/_meta/outline.md` — 各章範圍邊界與基準表，跨章主題用「（見 chNN）」帶過、不展開。

歷史與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。數學內容不依賴 landscape 但必須自我複核。

## 修改後，必跑

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過；目前 ch04/07/10/12 有少量 schematic 圖的軟性 unconnected-vertical 警告、非失敗）
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架
- `web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**；閱讀器「⌂ 書架」由 build_reader 自動連到最近的上層 bookshelf.html

## 慣例

- reader config `id` 是 `prob`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 簡體詞與半形標點 lint 用 Python 逐字元比對（shell grep 對同形字會誤報）；半形標點被 CJK 夾住要轉全形（數學式/程式/英文/小數保留半形）。
- 跨書邊界：Poisson/指數/Markov 的運算指向《佇列論》、機率即面積/怪獸函數指向《馴服無限》，本書只用自己的欣賞聲音講「為何美」、不重推公式。
- 數學審查分工：便宜模型（agy）math-only 逐章/逐 worked-example 重算、不准碰史實；帶網路的較貴模型審全書事實（見記憶 `agy-per-chapter-math-review`）。改動數值或推導後建議用 agy 重算（`agy --model "Gemini 3.5 Flash (High)" -p "..."`）。
- 程式碼（無）、設定檔、註解一律英文；書內容繁體中文。
