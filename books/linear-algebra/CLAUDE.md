# CLAUDE.md

專案性質：個人書《矩陣是動詞：線性代數作為空間變換的直覺與驚嘆》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**幾何優先、純興趣、和工作無關**（2026-06-13 訪談定案）——核心主張「矩陣不是數字表格、是一個對空間做事的動詞」；讀完要有「複雜只是座標沒選對」的數學之美震撼、能用自己的話對工程師轉述。**不刷計算、不背公式**；計算一律服務「看見變換做了什麼」。**每章至少一張程式生成幾何圖**（ch01–ch21；ch22 收官用 ASCII 路線圖＋對帳表），這是本書與《馴服隨機》最大的不同、與《圓的影子》同源。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章基準數值表**（脊椎矩陣 S=[[2,1],[1,2]] 七層、配角矩陣、det=3、特徵值 3/1、最小平方 a=2/3 b=1/2、PageRank 0.85、PC1 75%…改任何基準必須照表全書同步）、脆弱事實清單（三個 Jordan、高斯消去早於高斯、行列式早於矩陣、|λ₂|≤c、Leibniz/九章年代衝突、David Lay 版次未釘死）、圖片機制、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（**行＝column／列＝row、與大陸相反**；特徵值非本徵；禁簡體大陸詞）、章節骨架（從你已知的出發／直覺的陷阱／紙上推演＋推演解答＋動手生圖／自我檢核／延伸閱讀）、記號規範（純文字 Unicode、不依賴 LaTeX、矩陣進 ```text）、脊椎 S 七層、配角矩陣、圖片機制與固定腳本樣板、跨書邊界。
3. `book-src/_meta/outline.md` — 各章範圍邊界與基準表，跨章主題用「（見 chNN）」帶過、不展開。

歷史與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。數學內容不依賴 landscape 但必須自我複核（矩陣運算尤其易錯，解出特徵向量/方程要代回驗算）。

## 修改後，必跑（注意本書比《馴服隨機》多一步：先生圖）

- 動到 ASCII 圖/矩陣 ```text 排版：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過）。
- **動到任何 figure 腳本或新增圖**：先 `python3 ../../../tools/md-reader/build_figures.py book-src/figures`（跑出所有 `figures/out/*.svg`、`ch20 *.png`）。缺圖會讓 build_reader 直接 warn 中止。
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包（config `inline_images:true` 把 `figures/out/` 圖 base64 內嵌、保持單檔離線），書架有變動再 `python3 ../../../tools/md-reader/build_shelf.py`。
- `web/index.html` 與 `../../bookshelf.html`（專案根書架）是產生物，**不要手改**；閱讀器「⌂ 書架」由 build_reader 自動連到最近的上層 bookshelf.html。

## 慣例

- reader config `id` 是 `linalg`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- **圖內所有文字一律英文/數學記號**（matplotlib 對中文是豆腐框）；繁中 caption 寫在 markdown 的 `![caption](...)` alt 文字裡。figure 腳本＝該章 `### 動手生圖` 的 Python 小實驗，內嵌版與 `.py` 必須逐字一致。變換類圖要畫底層方格網變形前後＋`set_aspect("equal")`＋特徵/基向量顯色。
- 簡體/大陸詞 lint 用 Python 逐字元比對（shell grep 對同形字會誤報）；已知繁簡同形誤報：**「不准」的「准」是繁中正字**（准許/不准），非簡體；旋/弧/存/象/麼等亦同形。
- 數學審查分工：便宜模型（agy）math-only 逐項重算、不准碰史實/用詞；帶網路的模型審史實與結構（見記憶 `agy-per-chapter-math-review`）。改動數值或推導後建議用 agy 重算（`agy --model "Gemini 3.5 Flash (High)" -p "只驗數學…"`）；agy 偽陽性多，採納前自己複核。
- 跨書邊界：旋轉複特徵值的「為何 e^{iθ} 是旋轉」指向《圓的影子》ch07–08；馬可夫世界觀/共變異統計意義指向《馴服隨機》ch21/ch10；導數即線性近似軟連結《馴服無限》；本書只用幾何聲音講「變換做了什麼」、不重推鄰書。跨書引用用《》格式、不寫死檔名路徑。
- 程式碼（figure 腳本）、設定檔、註解一律英文；書內容繁體中文。
