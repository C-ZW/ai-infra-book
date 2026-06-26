# CLAUDE.md

專案性質：深讀版後端／分散式系統技術書《機制之下——後端與分散式系統如何運作、為何如此》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。

定位：**給一般資深後端工程師的深讀敘事書**。把後端與分散式系統反覆出現的機制，一主題一章講透——它解什麼問題、底下怎麼運作、買到什麼保證、付什麼代價、在哪裡會壞、為何是這形狀。脊椎＝**保證（guarantee）與取捨（trade-off）**。139 章＋2 附錄／22 領域（A–V）／8 個 Part。深度標竿＝〈共識〉章（`consensus.md`）。

> **與 `rsys` 的關係**：姊妹書 `rsys`（《保證與取捨》，速查／概念地圖、每條固定六段＋對照表）並存。兩書同主題、不同形態（rsys＝地圖、mech＝深讀），**互不指向**。本書由 `rsys` 的 ~150 主題於 2026-06-22 衍生重寫成敘事章。

## 硬規則（寫任何 book-src/ 內容前必守，全在 style-guide）

- **完全不提任何個人/特定公司系統**（NeoBards/LetsTalk/Bahwan 一律不准）；對象是所有人、平視同儕。
- **禁居高臨下糾錯口吻**（「你以為 vs 實際」「老兵記憶會過時」）；純機制天真假設的揭露（如樣章「最危險的假設是…」）可留。
- **不指向任何其他書**（含 `rsys`、作者他書）；延伸閱讀只放外部一手連結（RFC/論文/官方文件）。**外部第三方書/論文引用＝允許、加分**。
- **無練習段**。
- 每章是有機敘事、**無固定六段骨架**；唯一固定段是章尾 `## 延伸閱讀`。不要把對照表當一章骨幹、不要寫成速查表。
- 深度標準：讀完一章要能**向另一個工程師把該機制的細節講清楚**；零填充。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/style-guide.md` — 寫作契約：每章的形狀（敘事節奏，非模板）、深度的操作型標準、沿用的硬規則、術語對照表、章內引用與去重。
2. `book-src/_meta/outline.md` — 139 章清單、12 處合併決定、**owning 章表**（同一機制只在 owning 章深講、別章「（見〈章名〉）」帶過）、全域不涵蓋。
3. `book-src/_meta/maintenance.md` — 跨章一致性基準、脆弱事實清單、掃描協定與掃描日誌。

時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準（沿用自 `rsys`、兩書共用）；查證有修正：更新 landscape → 同步引用章 → maintenance.md 掃描日誌記一行。**重大修正需兩個獨立來源**。

## 檔案結構

- 一章一檔，檔名英文 slug（不帶章號）；h1＝章標題。reader 側欄顯示 h1。
- 附錄：`appendix-a-glossary.md`（術語表）、`appendix-b-reading-map.md`（延伸閱讀地圖）——衍生物，來源章一改要同步。
- reader 分組順序（`web/book.config.json`）：開始（README）→ Part 0–7 → 附錄。`_meta` 不入 reader。

## 修改後，必跑（工具路徑從本檔所在的 book 根起算）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄；box 中間行含全形標點會讓右框漂一欄，用 Python 精算寬度自測，exit 0 才算過；單純並排比較優先用 Markdown 表）。
- 動到任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（0 error；`全量` WARN 已裁定保留為資料同步/取樣語境偽報）＋ 書架有變動先 `python3 ../../../tools/md-reader/build_shelf.py` → `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包。
- 打包前紅線 grep（見 maintenance.md 掃描協定）應 0 命中。
- `web/index.html` 與 `../../bookshelf.html` 是產生物，**不要手改**；reader「⌂ 書架」由 build_reader 自動連最近上層 bookshelf.html。

## 慣例

- reader config `id` 是 `mech`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 簡體詞 lint 用 Python 逐字元比對（`們/效/系/准/值/程` 等兩岸同形字會讓 shell grep 誤報）；`對象` 禁用、用 `物件`；佇列勿用陸式同義詞。
- 程式碼/設定/註解一律英文；繁中只用於書內容與 reader UI。可貼**不可執行**的示意 pseudo-code（標明示意）。
- 章內引用一律「（見〈章名〉）」，用章標題、不寫死檔名/章號（章會增刪）。
