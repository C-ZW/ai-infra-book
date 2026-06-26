# CLAUDE.md

專案性質：個人書《不只一種無限：集合論與無限的直覺與驚嘆》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣**——不是符號操練、不是嚴格公理化教科書、不服務轉職敘事；動手做以紙筆推演＋口頭自答為主，**無 Python 段**（集合論的驚嘆在論證，不在數值）。脊椎：一一對應＝「一樣多」的定義；「同一條對角線」四次出場（ch04 對角論證／ch06 冪集定理／ch10 羅素悖論／ch16 不完備）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章記號/基準表**（CH 寫 `2^ℵ₀=ℵ₁`、GCH 寫 `2^ℵ_α=ℵ_{α+1}`、對角集 `D={x∈A : x∉f(x)}`、羅素 `R={x : x∉x}`、π(2,3)=18、𝔠 串等號、ℕ 三處約定…改任何一個必須照表全書同步）、脆弱事實清單、掃描協定與日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、記號規範（Unicode 純文字、**變數下標用底線 ℵ_α/V_α、數字下標用 Unicode ℵ₀**；多行推導進 ```text）、深度標準（硬證只限對角論證/Cantor 定理/CSB/羅素/Vitali，其餘明標不證；禁「顯然」「易證」）。
3. `book-src/_meta/outline.md` — 各章範圍邊界，跨章主題用「（chNN）」帶過、不展開。

歷史與歸屬事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。**守住的高風險事實**：1874 套疊區間≠1891 對角論證、獨立性≠證偽 CH、Banach–Tarski 非物理魔術、克羅內克逼瘋康托爾是迷思、ℶ 是 Peirce 1900 非康托爾。

## 修改後，必跑（工具在 `../../../../tools/md-reader/`）

- 動到 ASCII 圖：`python3 ../../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過）。**注意**：路線圖的 `│` 因上下無 box 字元被 checker 豁免，checker 不約束路線圖對齊——路線圖對齊只能靠**渲染肉眼檢查**。
- 動到任何內容：`python3 ../../../../tools/md-reader/lint_book.py book-src`（exit 0）→ `python3 ../../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包 → `python3 ../../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html` 與 `../../bookshelf.html`（專案根的書架）是產生物，**不要手改**。

## 慣例

- reader config `id` 是 `sets`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- **6 個 Part 首章（ch01/04/07/10/14/17）共用同一張全書路線圖**，只移 `◄你在這裡`；地圖含全部 ch01–19（Part IV 為 4 列 ch10–13）。改章名/章序必須六處同步——目前由 maintenance.md 掃描日誌記的 Python 腳本統一生成，別手抄六次。
- **跨章引用 house style：裸寫「（chNN）」**（全書壓倒性）；跨書「（見《馴服無限》chNN）」。
- 簡體詞 lint 用 Python 逐字元比對（shell grep 對同形字會誤報）。
- 改動任何證明骨架/構造（一一對應、對角線、序數算式、Vitali）後，必須自己走一遍驗證不重不漏；建議用 agy 或 gate_book --verify 跨家族重審該章數學。
- 程式無（純紙筆書）；設定檔、註解一律英文；書內容繁體中文。
