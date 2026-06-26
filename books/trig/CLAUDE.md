# CLAUDE.md

專案性質：個人書《圓的影子：三角函數作為旋轉與週期的語言》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣、和工作無關**（2026-06-13 訪談定案）——不解三角形題、不背恆等式（恆等式一律從來源推）、不裝高深；主軸是「三角函數不是三角形的學問，是旋轉與週期的語言；sin/cos 是繞圓的影子」。**每章至少一張程式生成圖**（這是本書與其他書最大的不同）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章基準表**（脊椎「和角公式四種證法」、特殊角表只在 ch03、方波 1.10347 跨書錨點、ch14 圖 rasterized 等；改任一基準必須照表全書同步）、脆弱事實清單、圖片機制、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答＋動手生圖／自我檢核／延伸閱讀）、Unicode 純文字數學（**不依賴 LaTeX**；多行推導進 ```text）、**圖片機制與固定腳本樣板**、深度標準。
3. `book-src/_meta/outline.md` — 各章範圍邊界與基準表，跨章主題用「（見 chNN）」帶過、不展開。

歷史與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源。常被誤傳的數學事實（方波 1.10347、Gibbs ≈8.95%、特殊角值、單位根和為 0）以 landscape 查證版為準。

## 與姊妹書的分工（可引用、不依賴）

書架上有《馴服無限：微積分的直覺與驚嘆》。Euler：那本從 e^x 級數推、本書 ch08 從旋轉推（同一定理兩個鏡頭）；sin′=cos：那本 ch05 只給草圖、本書 ch11 用旋轉補證；傅立葉：那本 ch11 管收斂嚴格化、本書 ch13 管「為什麼正弦是對的基底」到門口為止。方波 π/2 三項和兩書必須都是 **1.10347**。

## 修改後，必跑（注意本書比其他書多一步：先生圖）

- 動到 ASCII 圖（路線圖等）：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過）。
- **動到任何 figure 腳本或新增圖**：先 `python3 ../../../tools/md-reader/build_figures.py book-src/figures`（跑出所有 `figures/out/*.svg`）。缺圖會讓下一步 build_reader 直接報錯中止。
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包（config 的 `inline_images:true` 會把 `figures/out/` 的圖 base64 內嵌，保持單檔離線），書架有變動再 `python3 ../../../tools/md-reader/build_shelf.py`。
- `web/index.html` 與 `../../bookshelf.html`（專案根的書架）是產生物，**不要手改**；閱讀器的「⌂ 書架」按鈕由 build_reader 自動連到最近的上層 bookshelf.html。

## 慣例

- reader config `id` 是 `trig`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- **圖內所有文字一律英文/數學記號**（matplotlib 對中文是豆腐框）；圖的繁中 caption 寫在 markdown 的 `![caption](...)` alt 文字裡。figure 腳本＝該章 `### 動手生圖` 的 Python 小實驗，內嵌版與 `.py` 必須逐字一致。圖腳本用 `__file__` 推導輸出路徑（與 cwd 無關，樣板見 style-guide）。
- 簡體詞 lint 用 Python 逐字元比對；已知繁簡同形誤報：然/弧/旋/存/象/麼、以及「划算」的划。
- 改動任何數值（特殊角、近似表、複數運算、相量幅角、方波部分和）或推導後必須自己重算複核；建議用 agy 重審該章數學（`agy --model "Gemini 3.5 Flash (High)" -p "只驗數學、不准碰歷史/用詞..."`）。agy 是便宜模型、偽陽性多，採納前必須自己複核（見 maintenance.md 2026-06-13 掃描日誌的裁決紀錄）。
- 程式碼（figure 腳本）、設定檔、註解一律英文；書內容繁體中文。
