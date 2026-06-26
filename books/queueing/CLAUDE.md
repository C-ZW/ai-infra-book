# CLAUDE.md

專案性質：個人書《等待的數學：排隊理論》（繁體中文）＋單檔離線閱讀器。非程式專案，主要產出是 `book-src/` 下的 Markdown。讀者與作者是同一人（profile 中樞見 `../../../profile/`）。本書定位：**數學嚴謹為主的興趣書**——親手推導每個主要公式、每個公式記得連適用條件一起記；工程應用是橋接錨點與點綴（ch20 收網），不是主軸；不服務 AI Infra 轉職敘事（LLM serving 只在 ch20 點綴，深度指向 `../../book/` 的《從後端到 AI Infra》）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — **跨章一致性基準表**（記號系統 E[N]/E[T]、推播管線 λ=8/μ=10、M/M/1 全套、Erlang-C 0.596、Jackson 基準 E[T]=3.0 s、ch01 審判 8 條等；改任何基準必須照表 grep 全書同步）、脆弱事實清單、掃描協定與掃描日誌。
2. `book-src/_meta/style-guide.md` — 寫作契約：繁中台灣用語（禁簡體詞）、章節骨架（從你已知的出發／陷阱與防禦／紙上推演＋推演解答／自我檢核／延伸閱讀）、數學記號規範（內文 Unicode、E[N]/E[T] 系統不用 L/W）、Python 小實驗規範（seed 42、≤40 行、輸出寫區間）、深度標準（每個公式必附適用條件）。
3. `book-src/_meta/outline.md` — 各章範圍邊界，跨章主題用「（見 chNN）」帶過、不展開；全域不涵蓋清單（matrix-analytic、fluid/diffusion、MDP、network calculus、工具 API…）。

歷史歸屬與時效性事實以 `book-src/_meta/landscape-2026-06.md` 為基準；查證後有修正：更新 landscape → 依基準表同步引用章 → maintenance.md 掃描日誌記一行。重大修正需兩個獨立來源（單一來源永不推翻基準）。

## 修改後，必跑

- 動到 ASCII 圖：`python3 ../../../tools/md-reader/check_diagrams.py book-src`（CJK=2 欄規則，exit 0 才算過）
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重新打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架
- `web/index.html` 與 `../../bookshelf.html`（專案根的書架）是產生物，**不要手改**；閱讀器的「⌂ 書架」按鈕由 build_reader 自動連到最近的上層 bookshelf.html

## 慣例

- reader config `id` 是 `queue`，全域唯一（登記簿 `../../../profile/books.json`）；使用者閱讀偏好 light mode。
- 記號鐵律：內文一律 E[N]/E[T] 系統（不用教科書的 L/W）；L/W 對照只在 ch02 與附錄 A 各出現一次。改記號要同步附錄 A。
- 簡體詞 lint 用 Python 逐字元比對（「效」「系」「准」「們」等與簡體同形或近形的字會讓 shell grep 誤報——`們` 是繁體、簡體是 `们`）；注意 `對象` 在 TW 雖可指「目標」但本書禁用，programming object 用 `物件`。
- 數學審查歷史：全書 21 章＋附錄 A/B 經 agy（Gemini 3.5 Flash High）逐章 math-only 重算（2026-06-19，見 maintenance.md 掃描日誌；唯一真錯誤是 ch20 batching 的 438 ms 標籤，已修）；改動公式或基準數字後建議用 agy 重審該章（`agy --model "Gemini 3.5 Flash (High)" -p "..."`，只驗數學、不准碰事實／連結／歸屬）。
- Python 小實驗章＝ch05、ch08、ch12、ch15、ch17、ch19、ch20；ch08 首次引入 DES 骨架、ch19 補齊一般化＋方法學。ch17 的 MVA 是確定性遞迴、刻意無 seed。
