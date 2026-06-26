# CLAUDE.md

專案性質：個人書《注意力機制的原理：直覺、機制與理論》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**純原理與欣賞、與工作無關**（2026-06-13 訪談定案）——讀完要能用自己的話對工程師講清楚 attention 的三步骨架（打分→正規化→加權混合）與它的理論身世、故障視角、2026 現況。**不教訓練、不教部署、不刷論文**；KV/FlashAttention 的系統面指向《從後端到 AI Infra》。允許少量可讀的 NumPy/虛擬碼片段（英文、5–15 行、非 lab、不放訓練迴圈）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章基準數值表**（脊椎 it：[4,2,0]→[2,1,0]→[0.665,0.245,0.090]→輸出 (0.755,0.335)，未縮放 [0.867,0.117,0.016]；原始 Transformer d_k=64/√d_k=8/h=8/d_model=512…改任一基準必照表全書同步）、脆弱事實清單（脊椎例子出處＝Google 2017 部落格非原論文、attention 發明歸屬不選邊、attention≠解釋未定論、2026 前沿標時點、FlashAttention 精確非近似）、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體與大陸詞、禁「均值」用平均/期望值、禁歸一化用正規化、禁掩碼用遮罩）、章節骨架（從你已知的出發／故障模式與直覺陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、三步骨架回扣、跨書邊界、程式碼規範。
3. `book-src/_meta/outline.md` — 各章範圍邊界與基準表，跨章主題用「（見 chNN）」帶過、不展開。

歷史與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。數學內容不依賴 landscape 但必須自我複核（可疑處用 Python 裁決，單一模型不推翻）。

## 修改後，必跑

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，**exit 0 才算過**；目前全清。三步骨架用垂直流向圖，CJK 不放進方框牆以免欄寬塌掉）。
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**；閱讀器「⌂ 書架」由 build_reader 自動連到最近的上層 bookshelf.html。

## 慣例

- reader config `id` 是 `attn`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 簡體詞與大陸技術慣用語 lint 用 Python 逐字元比對（shell grep 對同形字會誤報）；半形標點被 CJK 夾住要轉全形（數學式/程式/英文/小數保留半形）。
- 跨書邊界：FlashAttention/KV/部署指向《從後端到 AI Infra》、線代運算指向《矩陣是動詞》、旋轉/複數（RoPE）指向《圓的影子》、softmax 即分布/期望指向《馴服隨機》；本書只用自己的原理聲音講「為何如此、為何美」。
- 數學審查分工：便宜模型（agy）math-only 逐章重算 worked example（**提醒它用完整精度指數、勿先四捨五入**）；帶網路模型審全書事實。改動數值或推導後建議用 agy 重算（`agy --model "Gemini 3.5 Flash (High)" -p "..."`）。
- 程式碼（少量、英文）、設定檔、註解一律英文；書內容繁體中文。
