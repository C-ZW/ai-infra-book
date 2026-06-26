# CLAUDE.md

專案性質：個人書《專家是怎麼煉成的：一萬小時的真相與刻意練習的科學》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣**——不服務轉職敘事；動手做以紙上推演＋口頭自答為主，**無 Python 段**。脊椎：**四問診斷表**（①踩在能力邊緣？②即時回饋？③針對哪個具體弱點？④可重複？）——每章把當章內容收回四問；累積時數是迴圈的**副產品不是原因**。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — 跨章一致性基準表（Macnamara 26/21/18/4/<1%、Ericsson 1993、10,000 小時鐵律、2019 複製 8,224 vs 9,844、chunking 50,000、近/遠遷移…改任一個必照表全書同步）、脆弱事實清單、掃描協定與日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、深度標準。
3. `book-src/_meta/outline.md` — 各章範圍邊界，跨章主題用「（chNN）」帶過。

歷史與歸屬事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源。**守住的高風險事實**：Macnamara 百分比逐一標領域（落差就是論點）；「一萬小時法則」是 Gladwell 造的、Ericsson 否認；天賦與練習是**交互非對立**；2019 複製方向（最佳組反而少時數）別寫反。

## 修改後，必跑（工具在 `../../../tools/md-reader/`，從本書根 `books/expertise/` 起算）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過）。路線圖的 `│` 因上下無 box 字元被 checker 豁免，對齊靠渲染肉眼檢查。
- 動到任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（0 errors）→ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包 → `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**。

## 慣例

- reader config `id` 是 `expert`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 四個 Part 首章 ch01/ch04/ch08/ch12 共用同一張全書路線圖，只移 `◄你在這裡`；改章名/章序必四處同步。
- 跨章引用 house style：裸寫「（chNN）」。
- 簡體詞 lint 用 Python 逐字元比對（shell grep 對同形字會誤報）。
- 逐章第二意見：`agy --model "Gemini 3.5 Flash (Medium)" -p ...`（事實/數學/繁中），verify-before-apply——agy 是單一意見、不可推翻 landscape。
- 程式無（純紙筆書）；設定檔、註解一律英文；書內容繁體中文。
