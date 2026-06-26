# CLAUDE.md

專案性質：個人書《複雜度守恆：軟體發展史的工程師讀法》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**興趣導向的「欣賞與直覺」軟體史，從資深後端工程師視角讀**（2026-06-13 訪談定案）——不是編年大事記、不是技術教科書、不服務轉職敘事；**純敘事＋紙上思辨（口頭自答＋思辨題），無可執行 lab**。核心主張：軟體史是反覆「對抗複雜度」的歷史，抽象只把複雜度搬家（複雜度守恆，是眼鏡非物理定律）；兩條 strand（抽象／方法）交織；鐘擺反覆擺動。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章一致性基準表**（核心命名、關鍵年份、12 項脆弱事實清單、ch19/ch21 總帳表與附錄的結構同步提醒、掃描協定與掃描日誌）。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞、技術詞留英文）、章節骨架（從你已知的出發／複雜度搬去哪了／紙上推演＋推演解答／自我檢核／延伸閱讀）、深度標準（史實照 landscape 不憑記憶、名言查證、傳說標明、每章一個被講透的個案）。
3. `book-src/_meta/outline.md` — 21 章×7 Part 的範圍邊界與基準表，跨章主題用「（見 chNN）」帶過、不展開。

歷史與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → ch19/ch21 總帳表 → 附錄 A/B/C → maintenance.md 掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。**所有 LOC／市佔／金額／AI coding 數字一律標估計、禁斷言。**

## 修改後，必跑（從本目錄 `books/software-history/` 執行）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過；**傳目錄非單檔**——傳單檔會回報 0 diagrams 假通過）。
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html` 與專案根 `bookshelf.html` 是產生物，**不要手改**；閱讀器「⌂ 書架」按鈕由 build_reader 自動連到最近的上層 bookshelf.html。

## 慣例

- reader config `id` 是 `swhist`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 簡體詞 lint 用 Python 逐字元比對（shell grep 對繁簡同形字如 息/硬/境/存/挑 會誤報）。
- 紙上推演層級慣例：題目 `### 推演題N`、解答 `#### 推演解答`（全書統一）。
- 7 個 Part 首章（ch01/04/07/10/13/16/19）＋ch21 各含一張全書 ASCII 路線圖（基準圖在 outline.md），改基準圖須同步 8 處。
- 結構同步雷區：改任一章的 `## 複雜度搬去哪了` 帳單，必回頭同步 ch19（17 列總表）與 ch21（19 列總表），以及附錄 A 章欄／附錄 B 首次出現章（見 maintenance.md 第四節）。
- 「掃描書的時效性」＝執行 maintenance.md 的掃描協定；最須重掃 landscape §Q（AI 輔助編程，半年內過期）。
- 程式碼／設定檔／註解一律英文；書內容繁體中文。
