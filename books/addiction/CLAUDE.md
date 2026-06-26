# CLAUDE.md

專案性質：個人書《大腦被劫持：成癮的機制》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣**——不服務轉職敘事；動手做以紙上推演＋口頭自答為主，**無 Python 段**。脊椎：成癮＝獎賞學習被劫持；**dopamine 是「想要（wanting）」不是「喜歡（liking）」**，成癮中兩者分離——**「兩條曲線分岔」**（wanting↑敏化、liking↓allostasis）。每章問：這裡講想要還是喜歡？哪段迴路被劫持？涉醫療/戒斷時明說「**機制說明，非醫療/戒斷建議**」。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — 跨章一致性基準表（wanting/liking、疾病vs學習不裁決、Trevor Robbins=習慣化、Lee Robins=越戰、Rat Park 1978–81・**約 19 倍**、脆弱性 15%/遺傳率 40–60%、buprenorphine=丁基原啡因、Leshner 1997 Policy Forum…改任一個必照表全書同步）、脆弱事實清單、掃描協定與日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架、深度標準。
3. `book-src/_meta/outline.md` — 各章範圍邊界，跨章主題用「（chNN）」帶過。

事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後修正：更新 landscape → 依基準表同步 → maintenance.md 日誌記一行。重大修正需兩個獨立來源。**守住的高風險事實（鐵律）**：**Lee Robins（越戰）≠ Trevor Robbins（習慣化）** 是不同人、絕不可混；疾病 vs 學習模型**兩造並陳、不裁決**、不可用脊椎替疾病模型背書；Rat Park 複製不穩**必 hedge**、不可寫「成癮全是環境」（嗎啡倍數＝某些條件下約 19 倍，landscape 原誤 7 倍已於 2026-06 修）；buprenorphine=**丁基原啡因**（非布托啡諾）；可卡因→**古柯鹼**；dlPFC 是靈長類分區（齧齒類用 PL/IL）。

## 修改後，必跑（工具在 `../../../tools/md-reader/`，從本書根 `books/addiction/` 起算）

- ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄，exit 0 才過）。**ch08 旋鈕對照表是 Python 重生成的對齊圖**，改它後務必重跑 checker。路線圖 `│` 被豁免。
- 任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（0 errors）→ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重打包 → `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html`、`../../bookshelf.html` 是產生物，**不要手改**。

## 慣例

- reader config `id` 是 `addct`，全域唯一（`../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 四個 Part 首章 ch01/ch05/ch09/ch13 共用同一張全書路線圖，只移 `◄你在這裡`；改章名/章序必四處同步。
- 跨章引用 house style：裸寫「（chNN）」。
- 簡體詞 lint 用 Python 逐字元比對。
- 逐章第二意見：`agy --model "Gemini 3.5 Flash (Medium)" -p ...`，verify-before-apply（agy 單一意見不可推翻 landscape）。
- 程式無；設定檔/註解一律英文；書內容繁體中文。
