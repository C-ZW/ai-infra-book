# CLAUDE.md

專案性質：個人 AI Infrastructure 轉職書（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book/` 下的 Markdown。讀者與作者是同一人（背景見 `Chewei_Chen_Resume.md`）；`plan.md` 是配套的練功路線，書與它互相對應但各自獨立。

## 修改 book/ 內容前，必讀（依序）

1. `book/_meta/maintenance.md` — **跨章一致性基準表**（改任何基準數字必須照表全書同步，如 Llama-3.3-70B 320 KiB/token）、已知脆弱事實清單、掃描協定與掃描日誌。
2. `book/_meta/style-guide.md` — 寫作契約：繁體中文台灣用語（禁簡體詞）、章節骨架（從你已知的出發／故障模式與防禦／動手做／自我檢核／延伸閱讀）、深度標準。
3. `book/_meta/outline.md` — 各章範圍邊界，跨章主題用「（見 chNN）」帶過、不展開。

時效性事實（版本、價格、硬體狀態）以 `book/_meta/landscape-2026.md` 為基準；查證後有修正時：更新 landscape、依一致性基準表同步所有引用章節、在 maintenance.md 掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。

## 修改後，必跑

- 動到任何章節文字：`python3 ../tools/md-reader/gate_book.py book`（Tier-1 lint，exit 0 才算過；發佈前加 `--verify` 跑 Tier-2 跨模型驗算，三家模型獨立重算載重數字）。經 write-book skill 產的書，P3/P4 兩階段閘門為**硬性要求**。
- 動到 ASCII 圖：`python3 ../tools/md-reader/check_diagrams.py book`（CJK=2 欄對齊規則，exit 0 才算過）
- 動到任何 book/ 內容：`python3 ../tools/md-reader/build_reader.py web/book.config.json` 重新打包；書架有變動先跑 `python3 ../tools/md-reader/build_shelf.py`（閱讀器的「⌂ 書架」按鈕會自動連到最近的上層 bookshelf.html，所以書架要先存在）
- `web/index.html`、`web/plan.html`、`bookshelf.html`（專案根）是產生物，**不要手改**；書架位置由 `../profile/books.json` 的 `shelf_output` 欄位決定

工具已抽至 `../tools/md-reader/`（通用打包器，說明見該處 README；程式一律英文）。本 repo 只保留 reader 設定檔（`web/*.config.json`）與輸出。**每本書設定檔的 `id` 必須全域唯一**（localStorage 命名空間，重複會讓閱讀進度互相覆蓋）。

個人上下文中樞在 `../profile/`（建書與個人化任務先讀其 README）；書籍登記簿 `../profile/books.json`；寫新書用 `write-book` skill（v3，2026-07-03 重設計：引擎設定在 repo 根 `write-book.config.json`；phase 規格／書型 pack／prompt 模板／陷阱庫在 skill 的 `references/`、P2/P4 workflow scripts 在 `scripts/`；重設計計劃見 `write-book-redesign-plan.md`）。**所有書集中放在本專案 `books/<slug>/` 下**（2026-06-12 決定；如 `books/tlaplus/`，各有自己的 CLAUDE.md），只有本書（AI Infra 轉職書）因歷史因素留在 repo 根的 `book/`。

## 慣例

- 使用者閱讀偏好：light mode（閱讀器預設紙感米白）。
- 閱讀器字型對齊假設 Apple 平台（Menlo＋PingFang）：CJK=2 欄由 build_reader 的 **wrapCJK** 在渲染時把 `pre` 內中文包進 `.cjkw` span（PingFang、120.41%）達成。**不要改回 @font-face size-adjust**——WebKit/Safari 對 `local()` 字型忽略 size-adjust，會讓中文行右邊框塌掉（2026-06-12 教訓）。細節與限制見 maintenance.md。
- 「掃描書的時效性」＝執行 maintenance.md 的掃描協定。
