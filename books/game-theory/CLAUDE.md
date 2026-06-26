# CLAUDE.md

專案性質：個人書《當理性互相碰撞：賽局理論的直覺與驚嘆》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣、和工作無關、純紙上推演**（2026-06 建書設定）——讀完要能對另一個工程師講清楚「囚徒困境 (背叛,背叛) 為何穩定卻雙輸、合作如何被重複/聲譽/演化/機制設計救回」。脊椎＝同一張囚徒困境報酬矩陣 T,R,P,S=5,3,1,0，被重看七層。中央張力：**個體理性 vs 集體理性**。屬「推理六書」家族（總綱 `../_reasoning-set-design.md`）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章基準數值表**（脊椎矩陣 5/3/1/0、grim δ≥1/2 與 TFT δ≥2/3 不可混、機制設計罰則 f≥2、PoA 4/3、公共財 4/3 等；改任何基準必照表全書同步）、脆弱事實清單、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體與大陸詞——賽局不用「博弈」、若且唯若不用「當且僅當」、負載平衡不用「均衡」、序貫統一不用序列、展開式不用擴展式）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、記號規範（純文字 Unicode、不依賴 LaTeX、多行進 ```text）、脊椎七層落點、跨書邊界。
3. `book-src/_meta/outline.md` — 各章範圍邊界、跨章基準表、史實骨幹，跨章主題用「（見 chNN）」帶過、不展開。

史實與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源。賽局數學（報酬、均衡、δ 門檻、ESS 比例）不依賴 landscape 但必須自我複核。

## 修改後，必跑（路徑相對本書根）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄；exit 0 才算過。ch04 兩格報酬矩陣帶 │ 側註欄會被標 suspicious 但 exit 0，屬可接受非框線圖）。
- 動到任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（Tier-1 閘，exit 0）→ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包。書架有變動先 `python3 ../../../tools/md-reader/build_shelf.py`。
- `web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**。

## 慣例

- reader config `id` 是 `game`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode（紙感米白）。
- 全書純紙上推演、零可跑程式；報酬矩陣／賽局樹用 ```text ASCII（無 SVG，config `inline_images:false`）。
- 簡體詞與大陸用詞：lint 逐字元比對只抓簡體字；**大陸詞（當且僅當、流水線、灰度、序貫、覆盤…）lint 抓不到，靠 agy 逐章審＋人工**。
- 數學審查：agy（Gemini 3.5 Flash Medium）逐章重審，**裁決一律 verify-before-apply**——agy 常只看局部會誤判（如把正確的 TFT 偏離報酬 7.7/14.6 誣為錯、把骨架 ★/分鐘當教科書化），每條先自己重算/查證再改（規則見 `../_reasoning-set-design.md` §6、記憶 `agy-per-chapter-math-review`）。
- 跨書邊界：單人理性/期望效用→《在不確定中下注》、混合策略期望值與機率→《馴服隨機》、策略情境的非理性偏好→《思考的陷阱》；姊妹書一律主題式、不寫章號。
- 程式碼（圖檢查等）、設定檔、註解一律英文；書內容繁體中文。
