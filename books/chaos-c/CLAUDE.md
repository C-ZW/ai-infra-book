# CLAUDE.md

專案性質：個人書《決定卻測不準：混沌理論的直覺與驚嘆》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**欣賞與直覺、純興趣、和工作無關、純紙上推演**（2026-06-19 建書設定）——讀完要有「原來決定論和不可預測可以同時成立」的震撼、能用自己的話對工程師轉述「Laplace 惡魔死在哪一刀」。**新增內容不得引入任何要讀者去跑的程式或 lab**；數值示範一律手算、用 ```text 表呈現。書中插圖是作者預先算好的程式生成 SVG（`book-src/figures/`），那是給讀者看的圖、不是要讀者跑的程式。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章基準數值表**（脊椎遞迴式、x*=1−1/r、分岔點 r₂=1+√6、混沌起點 r∞≈3.56995、Feigenbaum δ≈4.6692、period-3 窗口 1+√8≈3.8284、r=4 λ=ln2≈0.6931、Lorenz σ=10/ρ=28/β=8/3 與 λ≈0.9056/維度≈2.06、碎維度 Koch 1.2619 等；改任何基準必須照表全書同步）、脆弱事實清單、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體與大陸詞、「碎形」不用「分形」、「分岔」不用「分叉」、自然口語不要翻譯腔）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答／自我檢核／延伸閱讀）、記號規範（純文字 Unicode、不依賴 LaTeX、多行進 ```text）、全書脊椎（同一條遞迴式七層）、跨書邊界。
3. `book-src/_meta/outline.md` — 各章範圍邊界、跨章基準表、插圖清單，跨章主題用「（見 chNN）」帶過、不展開。

歷史與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準（含 T1–T7 直覺陷阱正確版、待考項）；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。數學內容不依賴 landscape 但必須自我複核。

## 修改後，必跑

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過）。
- 動到 SVG 生成腳本：`python3 ../../../tools/md-reader/build_figures.py book-src/figures`（exit 0）。**dense scatter（分岔圖 ch07、Feigenbaum ch08、Lyapunov ch14）務必 `rasterized=True` + `dpi=150`，否則 SVG 會膨脹到數十 MB**（建書教訓）。
- 動到任何 book 內容：`python3 ../../../tools/md-reader/lint_book.py book-src`（Tier-1 閘，exit 0）→ `python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包（`inline_images` 會把 SVG base64 內嵌；圖檔缺失會中止打包）。
- `web/index.html` 是產生物，**不要手改**。

## 慣例

- reader config `id` 是 `chaos-c`，全域唯一（localStorage 命名空間）；使用者閱讀偏好 light mode（紙感米白）。
- **本書刻意未登記到 `../../../profile/books.json`、未跑 build_shelf**（2026-06-19 建書時與另一並行流程隔離的決定，避免互相覆蓋 bookshelf.html）。閱讀器「⌂ 書架」按鈕會自動連到最近的上層 bookshelf.html（目前指向 `../../../bookshelf.html`，該書架尚未列出本書）。日後若要上書架：登記 books.json（含 `shelf_output`）再 `build_shelf.py`。
- 簡體詞與 CJK 語境半形標點用 Python 逐字元比對（shell grep 對同形字會誤報）；CJK 語境標點全形，數學式/程式/英文/小數保留半形。
- 跨書邊界：隨機/機率指向《馴服隨機》、微分方程/導數/Lorenz ODE 指向《馴服無限》、Jacobian 特徵值指向《矩陣是動詞》；本書只用自己的欣賞聲音講「為何美」、不重推公式。格式 `（見《馴服隨機》chNN）`。
- 數學審查分工：便宜模型（agy，math-only、不碰史實）逐章/逐 worked-example 重算；帶網路的較貴模型審全書事實（見記憶 `agy-per-chapter-math-review`）。改動數值或推導後建議用 agy 重算（`agy --model "Gemini 3.5 Flash (High)" -p "..."`）。
- 程式碼（圖生成腳本）、設定檔、註解一律英文；書內容繁體中文。
