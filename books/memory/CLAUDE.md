# CLAUDE.md

專案性質：個人書《大腦怎麼編造過去：記憶作為重建的科學》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣**——不服務轉職敘事；動手做以紙上推演＋口頭自答為主，**無 Python 段**。脊椎：**「每次 read 觸發一次 write」**（提取記憶會把它帶回不穩定狀態並重新寫入）——每章至少一處回問「這裡是 read，還是 read 觸發了 write？」；同時守防線：**重建≠記憶全不可信**。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — 跨章一致性基準表（Loftus&Palmer 45/150・32/14/12、mall 24/25%・123/35%、DRM、HM 1953/27、Nader anisomycin、Neisser 106→44/約32個月、HSAM=Patihis 2013…改任一個必照表全書同步）、脆弱事實清單、掃描協定與日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架、深度標準。
3. `book-src/_meta/outline.md` — 各章範圍邊界，跨章主題用「（chNN）」帶過。

事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後修正：更新 landscape → 依基準表同步 → maintenance.md 日誌記一行。重大修正需兩個獨立來源。**守住的高風險事實**：Neisser–Harsch 間隔＝**約 32 個月**（不是「兩年半/2.5 年」當主數）；Nader 2000 用 **anisomycin** 不是 propranolol；HSAM 假記憶＝**Patihis 2013**、命名是 LePort 2012；HM 內嗅皮質近全切、後側海馬迴殘留；**James McGaugh 仍在世（1931–）**；術語用**活化**不用「激活」。

## 修改後，必跑（工具在 `../../../tools/md-reader/`，從本書根 `books/memory/` 起算）

- ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄，exit 0 才過）。路線圖 `│` 被豁免，對齊靠渲染肉眼檢查。
- 任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（0 errors）→ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重打包 → `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html`、`../../bookshelf.html` 是產生物，**不要手改**。

## 慣例

- reader config `id` 是 `mem`，全域唯一（`../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 四個 Part 首章 ch01/ch04/ch08/ch12 共用同一張全書路線圖，只移 `◄你在這裡`；改章名/章序必四處同步。
- 跨章引用 house style：裸寫「（chNN）」。
- 簡體詞 lint 用 Python 逐字元比對。
- 逐章第二意見：`agy --model "Gemini 3.5 Flash (Medium)" -p ...`，verify-before-apply（agy 單一意見不可推翻 landscape）。
- 程式無；設定檔/註解一律英文；書內容繁體中文。
