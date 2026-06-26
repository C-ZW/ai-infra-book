# CLAUDE.md

專案性質：個人書《這句話無法被證明：哥德爾不完備定理的直覺與驚嘆》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣、和工作無關、純紙上推演**（2026-06 建書設定）——讀完要能對另一個工程師講清楚「自我指涉句 G 如何從說謊者悖論一步一步搭建成第一與第二不完備定理、為什麼任何夠強又一致的形式系統都說得出一個自己無法判定的真句子」。脊椎＝自我指涉句 G「G 在本系統 F 內無法被證明」，從說謊者悖論出發，歷經哥德爾編碼、對角化引理，逐層搭建至第一、第二不完備定理，再到停機問題孿生、補洞長新洞、根岑回應，收官章層層對帳。中央張力：**真理溢出證明——任何夠強又一致的形式系統，都說得出一個自己無法判定的真句子**。屬「推理六書」家族（總綱 `../_reasoning-set-design.md`）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章基準數值表**（脊椎句兩版本、三條件鐵律、HBL D1–D3、哥德爾編碼約定、Con(F) 記法、ε₀、逃得掉的反例等；改任何基準必照表全書同步）、脆弱事實清單（⚠️ 項目標 Lucas–Penrose 無共識、ω-一致 vs 一致、圖靈/Lucas 年份、Church–Turing 是論題非定理）、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體與大陸詞——遞迴不用「递归」、質數不用「素數」、演算法不用「算法」、程式不用「程序」、一致統一用「一致 consistent」不用「相容/自洽」）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、記號規範（純文字 Unicode、不依賴 LaTeX、多行推導進 ```text）、脊椎 G 落點、跨書邊界。
3. `book-src/_meta/outline.md` — 各章範圍邊界、16 章＋3 附錄的分 Part 結構、跨章基準表、全書地圖 ASCII（各 Part 首章放路線圖並標「◄ 你在這裡」），跨章主題用「（見 chNN）」帶過、不展開。

史實與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源。定理的精確陳述（三條件、ω-一致 vs 羅瑟改進、HBL 條件、Con(F) 記法）不依賴 landscape 但必須自我複核。

## 修改後，必跑（路徑相對本書根）

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄；exit 0 才算過）。
- 動到任何內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（Tier-1 閘，exit 0）→ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包。書架有變動先 `python3 ../../../tools/md-reader/build_shelf.py`。
- `web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**。

（從 book-src/_meta/ 內往上兩層再進 tools，路徑為 `../../../../tools/md-reader/`；相對本書根則為 `../../../tools/md-reader/`。）

## 慣例

- reader config `id` 是 `godel`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode（紙感米白）。
- 全書純紙上推演、零可跑程式；所有編碼示範、對角化造句、停機歸謬用 ```text ASCII（無 SVG，config `inline_images:false`）。
- 簡體詞與大陸用詞：lint 逐字元比對只抓簡體字；**大陸詞（当且仅当→若且唯若、递归→遞迴、素数→質數、算法→演算法、信息→資訊）lint 抓不到，靠 agy 逐章審＋人工**。
- 數學審查：agy（Gemini 3.5 Flash Medium）逐章重審，**裁決一律 verify-before-apply**——agy 常只看局部會誤判（如把正確的三條件陳述誣為「條件不齊」、把骨架標題當教科書格式問題），每條先自己重推/查證再改（規則見 `../_reasoning-set-design.md` §6）。
- 跨書邊界：算術基本定理（質因數分解唯一）→《乘法的原子》（ch05 招牌連結、明寫「借《乘法的原子》」）；濫用心理機制→《思考的陷阱》；形式系統真 vs 可證對照科學真 vs 已驗證→《如何不騙自己》；機械檢查味道→《把系統寫成定理》（TLA+ 書，一句呼應、不依賴）；無窮/可數不可數→《馴服無限》。姊妹書一律主題式、不寫章號。
- 程式碼（圖檢查等）、設定檔、註解一律英文；書內容繁體中文。
