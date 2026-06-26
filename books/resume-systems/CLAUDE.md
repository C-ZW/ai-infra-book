# CLAUDE.md

專案性質：通用概念參考書《保證與取捨——後端與分散式系統的概念地圖》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。

定位：**給一般資深後端工程師**的概念地圖。對後端與分散式系統反覆出現的老問題，回答「它保證什麼／解什麼問題 → 解法空間 → 各方案的保證與取捨 → 何時需要 → 常見誤解與陷阱」。脊椎＝**保證（guarantee）與取捨（trade-off）**。約 150 條目 / 22 領域（A–V）/ 8 個 Part。

> **歷史**：本書由舊個人書《名詞底下》（向內挖作者履歷系統、含「我以為 vs 實際」糾錯口吻）於 2026-06-21 **就地重寫**成通用向外概念書。舊 `chNN-*.md` 已移至 `_archive-personal-book/`（不打包、不掃描）。

## 硬規則（寫任何 book-src/ 內容前必守，全在 style-guide）

- **完全不提任何個人/特定公司系統**（NeoBards/LetsTalk/Bahwan 一律不准出現）；對象是所有人、平視同儕。
- **禁糾錯口吻**（不寫「你以為 vs 實際」「老兵記憶會過時」）。
- **不指向任何其他書**；延伸閱讀只放外部真實連結（RFC/論文/官方文件）。
- **無練習段**。
- AI 維度只寫**原理層**（委派/驗收/信任邊界/新故障模式），不寫任何 AI 工具版本或品牌。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、**兩種條目各六段 `###` 骨架**（問題型：定義與原理/解法空間/各方案的保證與取捨/何時需要/常見誤解與陷阱/延伸閱讀；工具型：是什麼與內部機制/在哪些系統扮演什麼角色/保證與限制/跟替代品的取捨/常見誤解與陷阱/延伸閱讀）、深度標準、平行產出一致性規範（術語對照表、長度、引用格式）。
2. `book-src/_meta/outline.md` — 完整 TOC、各領域邊界、**跨領域去重 owning 表**（同一主題的機制只在 owning 條目深講一次，另一處用「（見 X，領域 Y）」帶過）、全域不涵蓋。
3. `book-src/_meta/maintenance.md` — 跨條目一致性基準、脆弱事實清單、掃描協定與掃描日誌。

時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依 owning 表同步引用條目 → maintenance.md 掃描日誌記一行。**重大修正（推翻既有基準）需兩個獨立來源**。

## 檔案結構

- 一個領域一個檔，命名 `<字母>-<英文 slug>.md`；大領域切多檔（A→A1/A2/A3、B→B1/B2、M→M1/M2、I→I1/I2、T→T1/T2），切多檔的領域 h1 用子題區分。
- 每檔 h1 `# <字母> · <子題>`＋前言；每概念一個 `##`；六段 `###`。
- 附錄：`appendix-a-guarantee-cheatsheet.md`（保證速查）、`appendix-b-glossary.md`（術語表）、`appendix-c-reading-map.md`（外部延伸閱讀地圖）——**衍生物**，來源條目一改要同步。
- reader 分組順序（`web/book.config.json`）：Part 0→7；**L 歸 Part 2**、**Part 3 順序 N→C→H→F**。

## 修改後，必跑（工具路徑從本檔所在的 book 根起算）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄；box 中間行含全形標點會讓右框漂一欄，用 Python 精算寬度自測，exit 0 才算過）
- 動到任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（0 error；新檔不符 `ch*.md` 故被當 content、只跑簡體字/大陸詞檢查——每條的六段骨架不在 lint 範圍，靠 review 把關）＋ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架
- 打包前 grep 防呆：`待回填|掃描日誌|本任務`（編輯註記洩漏）＋ `</?(content|invoke|parameter|function|antml)`（tool-call 殘留）應 0 命中
- `web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**；閱讀器「⌂ 書架」按鈕由 build_reader 自動連到最近上層 bookshelf.html

## 慣例

- reader config `id` 是 `rsys`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 簡體詞 lint 用 Python 逐字元比對（`們/效/系/准/值` 等兩岸同形字會讓 shell grep 誤報）；`對象` 禁用、用 `物件`；佇列勿用陸式同義詞。
- 程式碼/設定/註解一律英文；繁中只用於書內容與閱讀器 UI。可貼**不可執行**的示意 pseudo-code（標明示意）。
- 跨條目引用一律「（見 <概念名>，領域 X）」，不寫死檔名/章號（領域會增刪）。
