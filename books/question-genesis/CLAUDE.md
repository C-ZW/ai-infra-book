# CLAUDE.md — 《問題誕生之前：從理所當然到值得追問》

面向對世界好奇的一般讀者的「問題誕生學」敘事非虛構書（繁體中文・台灣，`form = narrative`，`reader_register = general`）。不假設專業背景，透過科學、數學、哲學、發明史上的真實探索現場，帶讀者體會：**人們原本把什麼當成理所當然、哪個微小細節刺破了常識、模糊的困惑又如何被鍛造成值得追問的問題**。

全書脊椎：**「問題顯影四階」**（理所當然的背景 → 刺眼的微小細節 → 從迷霧到對焦 → 日常的回聲）。12 章 ＋ 附錄 A/B，分 4 個 Part。閱讀器 `id`：`qgen`（localStorage 命名空間，全域唯一）。

**本書不寫入任何作者個人經歷、不做職涯敘事、不假設讀者特定職業背景。**

## 修改 `book-src/` 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — 基準數字表（`B1`–`B10`，跨章一致鐵律，與 `outline.md`／`running-examples.md` 三方逐字相同）、**脆弱事實索引**、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：四階問題顯影敘事弧線、全形標點、禁止說教與禁止教科書編號標題、深度標準（每章 `≥ 4500` depth units）。
3. `book-src/_meta/outline.md` — 各章 spec、範圍邊界、基準數字表（唯一真相）。
4. `book-src/_meta/landscape-2026-10.md` 與 `book-src/_meta/source-evidence/` — 歷史歸屬與實驗數據事實基準（⚠️ 標記後世浪漫化傳說處，如伽利略斜塔與比薩吊燈）。

## 修改後，必跑

- 動到章節文字與圖框：`python3 tools/md-reader/gate_book.py books/question-genesis/book-src --lang zh-TW --config books/question-genesis/book-src/_meta/lint.config.json`（exit 0）＋ `python3 tools/md-reader/check_diagrams.py books/question-genesis/book-src`（CJK 全形＝2 欄，exit 0）。
- 動到任何內容：`python3 tools/md-reader/build_reader.py books/question-genesis/web/book.config.json` 重新打包。書架有變動先跑 `python3 tools/md-reader/build_shelf.py`。
- 改基準數字：只改 `outline.md` 的基準表 → 重新同步 `running-examples.md` 與 `maintenance.md`（三方逐字相同）→ 傳播進章節 → 重跑一致性檢查。
- 動到載重推導或史實：重跑 Tier-2 `verify_book.py` 查核並更新 `book-src/_meta/verify-log.md`。

## 慣例

- `web/index.html` 是產生物，**不要手改**；書架位置由根目錄 `books.json` 的 `shelf_output` 決定。
- 標點一律全形中文標點；數學符號、比例與科學單位保持半形。
- ASCII 推演框必須包裹於 ```` ```text ```` 程式碼區塊內，並通過 `check_diagrams.py` 欄寬對齊檢查。
