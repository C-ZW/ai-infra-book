# CLAUDE.md

專案性質：個人書《馴服無限：微積分的直覺與驚嘆》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣**（2026-06-12 訪談定案）——不是解題訓練、不是嚴格分析教科書、不服務轉職敘事；動手做以紙筆推演＋口頭自答為主，指定六章有可選 Python 小實驗（本機、免費、≤30 行）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md`（P5 後存在）— **跨章基準表**（同一題三算 ∫₀¹x²dx=1/3、割線斜率表、e 複利表、Euler 法數值…改任何基準必須照表全書同步）、脆弱事實清單、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、數學記號規範（**全書 Unicode 純文字、不依賴 LaTeX 渲染**；多行推導進 ```text 區塊）、深度標準（數值自我複核、嚴謹度誠實標示、禁「顯然」）。
3. `book-src/_meta/outline.md` — 各章範圍邊界與基準表，跨章主題用「（見 chNN）」帶過、不展開。

歷史與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源。數學內容不依賴 landscape，但常被誤傳的數學事實（−1/12、0.999…、Gibbs ≈9%、Weierstrass 條件）以 landscape 查證版為準。

## 修改後，必跑

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過）
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架
- `web/index.html` 與 `../../bookshelf.html`（專案根的書架）是產生物，**不要手改**

## 慣例

- reader config `id` 是 `calc`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 簡體詞 lint 用 Python 逐字元比對（shell grep 對同形字會誤報）。
- 改動任何數值表（逼近表、部分和、迭代表）或推導後，必須自己重算複核；建議用 agy 重審該章數學（`agy --model "Gemini 3.5 Flash (High)" -p "..."`，只驗數學、不准碰歷史事實）。
- 程式碼（Python 小實驗）、設定檔、註解一律英文；書內容繁體中文。
