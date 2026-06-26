# CLAUDE.md

專案性質：個人書《正常意外：複雜系統如何崩壞，以及一個工程師該怕什麼》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**興趣導向的「工程災難解剖」敘事書，從資深後端工程師的「焦慮工程師」視角讀**（2026-06-13 建書定案）——不是災難百科、不是技術教科書、不獵奇；**純敘事＋紙上思辨，無可執行 lab**。核心主張：嚴重災難幾乎從不是單一根因，而是多層防禦的孔洞對齊（正常意外／瑞士起司／漂移到失效）；全書招牌＝一套可重用的失敗模式語言 F1–F14。形態：**23 章、七個 Part、3 附錄**。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章一致性基準、脆弱事實清單、結構同步雷區（路線圖 8 處、F1–F14 三處同步、附錄A是數字第二存放處）、案例取材原則、掃描協定與掃描日誌**。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞、技術詞留英文）、章節骨架（從你已知的出發／故障解剖／換成你的系統／紙上推演＋推演解答／自我檢核／延伸閱讀）、F1–F14 基準表、深度標準（史實照 landscape、迷思必校正、不獵奇、破單一根因）。
3. `book-src/_meta/outline.md` — 23 章×7 Part 的範圍邊界、敘事弧、跨章基準、各章主打 F 模式與被講透的個案。

硬事實（日期、死傷、金額、技術根因、調查結論、連結）以 `book-src/_meta/landscape-2026-06.md` 為事實基準（三輪查證、34 案）；查證後有修正：更新 landscape →依 maintenance.md 第三節同步引用章→同步 `appendix-a-timeline.md`（數字第二存放處）→ ch23/附錄B/style-guide 的 F 表（若動到歸屬）→ maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源。**所有死傷／金額／規模一律標估計或給範圍。**

## 修改後，必跑（從本目錄 `books/systems-failure/` 執行）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過；**傳目錄非單檔**）。**路線圖連接線只能用 `▼ ▲ ◄`，不可用 `↓ ↑ ←`**（裸箭頭會被判未連而 FAIL）。
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html` 與專案根 `bookshelf.html` 是產生物，**不要手改**；閱讀器「⌂ 書架」按鈕由 build_reader 自動連到最近的上層 bookshelf.html。

## 慣例

- reader config `id` 是 `fail`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- **全書路線圖**出現在 7 個 Part 首章（ch01/04/07/10/14/18/22）＋ outline 基準圖，改基準圖須同步 8 處（見 maintenance.md 第四節）。
- **失敗模式 F1–F14** 在 style-guide 基準表、附錄B、ch23 總表三處必須同步。
- **案例取材原則**：刻意排除 jserv《軟體失效案例》合集已收案例（Ariane 5、Therac、Knight、Patriot、Mars Climate Orbiter、AT&T、北美大停電、Pentium、Toyota…），**永不採為主案或內文範例**（見 maintenance.md 第二節）。
- 簡體詞 lint 用 Python 逐字元比對（shell grep 對繁簡同形字會誤報）。
- 內部註記 `⚠️ 待協調者複核` 不得留在成書 ch*.md／appendix*.md（會在閱讀器顯示）。
- 「掃描書的時效性」＝執行 maintenance.md 的掃描協定；最須重掃近年事故（CrowdStrike 2024、SolarWinds、Log4Shell、德州電網）。
- 程式碼／設定檔／註解一律英文；書內容繁體中文。
