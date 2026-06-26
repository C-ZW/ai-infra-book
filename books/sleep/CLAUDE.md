# CLAUDE.md

專案性質：個人書《大腦每晚的維護工作：睡眠的科學》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣**——不服務轉職敘事；動手做以紙上推演＋口頭自答為主，**無 Python 段**。脊椎：睡眠＝大腦每晚的**維護視窗**，做三件事——**清除／鞏固／校準**；**雙歷程模型（Process S × Process C）是排程器**。每章把現象歸位：是哪一件維護工作？由哪個歷程驅動？涉醫療時明說「**機制說明，非醫療建議**」。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — 跨章一致性基準表（Borbély 1982、N1/N2/N3/REM、90 分週期、膠淋巴 ~60%/2013-vs-2024、SHY、腺苷/咖啡因、2017 諾獎果蠅 per/tim、TTFL=Hardin 1990、褪黑激素 7/8 分、FNSS…改任一個必照表全書同步）、脆弱事實清單、掃描協定與日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架、深度標準。
3. `book-src/_meta/outline.md` — 各章範圍邊界，跨章主題用「（chNN）」帶過。

事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後修正：更新 landscape → 依基準表同步 → maintenance.md 日誌記一行。重大修正需兩個獨立來源。**守住的高風險事實**：膠淋巴 **2013 vs 2024 僵持、無共識**，絕不可斷言「睡眠洗腦」；Walker《Why We Sleep》戲劇數字一律不引為定論；**2017 諾獎是果蠅 per/tim**，TTFL=Hardin **1990**（非 1984），別把 CRY 安到果蠅；腺苷是 Process S **之一非唯一**；褪黑激素非安眠藥。

## 修改後，必跑（工具在 `../../../tools/md-reader/`，從本書根 `books/sleep/` 起算）

- ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄，exit 0 才過）。**ch02 hypnogram／ch03 S-C 曲線圖是 Python 重生成的對齊圖**，改它們後務必重跑 checker＋渲染肉眼檢查。路線圖 `│` 被豁免。
- 任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（0 errors）→ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重打包 → `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html`、`../../bookshelf.html` 是產生物，**不要手改**。

## 慣例

- reader config `id` 是 `sleep`，全域唯一（`../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 四個 Part 首章 ch01/ch04/ch08/ch12 共用同一張全書路線圖，只移 `◄你在這裡`；改章名/章序必四處同步。
- 跨章引用 house style：裸寫「（chNN）」。
- 簡體詞 lint 用 Python 逐字元比對。
- 逐章第二意見：`agy --model "Gemini 3.5 Flash (Medium)" -p ...`，verify-before-apply（agy 單一意見不可推翻 landscape）。
- 程式無；設定檔/註解一律英文；書內容繁體中文。
