# CLAUDE.md

專案性質：個人書《把系統寫成定理：TLA+ 與形式化方法》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**紙上推演、不裝工具、深入到證明層**（2026-06-11 訪談定案）——新增內容不得引入「安裝／操作工具」的段落。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章一致性基準表**（v0/v1 結算系統命名與狀態數、各協議配置、證明 invariant 定案；改任何基準必須照表全書同步）、脆弱事實清單、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架（從你已知的出發／陷阱與防禦／紙上推演＋推演解答／自我檢核／延伸閱讀）、數學符號規範（內文 Unicode、spec 引文 ASCII）、深度標準。
3. `book-src/_meta/outline.md` — 各章範圍邊界，跨章主題用「（見 chNN）」帶過、不展開。

時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源。

## 修改後，必跑

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過）
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架
- `web/index.html` 與 `../../bookshelf.html`（專案根的書架）是產生物，**不要手改**；閱讀器的「⌂ 書架」按鈕由 build_reader 自動連到最近的上層 bookshelf.html

## 慣例

- reader config `id` 是 `tla`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 簡體詞 lint 用 Python 逐字元比對（「效」「系」「准」等同形字會讓 shell grep 誤報）。
- 數學審查歷史：全書 20 檔經獨立模型逐章重算（2026-06-12，見 maintenance.md 掃描日誌）；改動證明或狀態數後建議用 agy 重審該章（`agy --model "Gemini 3.5 Flash (High)" -p "..."`，只驗數學、不准碰事實）。
