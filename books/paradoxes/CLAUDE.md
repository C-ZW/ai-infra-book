# CLAUDE.md — 《沒說出口的那句》

悖論欣賞書（繁體中文・台灣）。**面向一般讀者**（大學入門機率起點），不迴避數學推導，程式生成圖內嵌。脊椎：**每個悖論都因為一句沒說出口的假設而崩——直覺答案 → 揪出被偷渡的假設 → 嚴謹重建**。27 章 ＋ 附錄 A/B/C，分 8 個 Part。閱讀器 id：`pdox`（localStorage 命名空間，全域唯一）。

**本書不寫入任何作者個人經歷、不做職涯敘事、不假設讀者職業**（與 aiib/rsys 等個人書不同）。

## 修改 book-src/ 內容前，必讀（依序）

1. `book-src/_meta/maintenance.md` — 基準數字表（B1–B12，跨章一致鐵律，與 outline／running-examples 三方逐字相同）、**脆弱事實索引**（歷史歸屬的 ⚠️ 清單）、掃描協定、掃描日誌、Bridge Registry 鎖定、工具限制與教訓。
2. `book-src/_meta/style-guide.md` — 寫作契約：章節骨架（從你已知的出發／…／直覺的陷阱 收尾定型句「那句沒說出口的話是：__」／紙上推演／自我檢核／延伸閱讀）、全形標點、**內文禁 ```python**、深度標準、橋接契約。
3. `book-src/_meta/outline.md` — 各章 spec、範圍邊界、基準數字表（唯一真相）、Bridge Registry、fade-out。
4. `book-src/_meta/landscape-history.md` — 歷史歸屬事實基準（⚠️ 標脆弱處）。

## 修改後，必跑（皆從 `book-src/` 執行）

- 動到章節文字：`python3 ../../../../tools/md-reader/lint_book.py . --lang zh-TW --config _meta/lint.config.json`（exit 0）。**注意 lint 的簡體字盲點**：含「不是／非「」對比提示的行會抑制 forbidden-char 檢查——發佈前另跑一次獨立簡體字掃描補查。
- 動到 ASCII 圖：`python3 ../../../../tools/md-reader/check_diagrams.py .`（CJK 全形＝2 欄，exit 0）。
- 動到圖：`python3 ../../../../tools/md-reader/build_figures.py figures`（每張圖一支 `figures/chNN-*.py` → `figures/out/*.svg`；內文 `![說明](figures/out/…svg)`，**圖說內不得有 `]`、`!` 保持半形**）。
- 動到任何內容：`python3 ../../../../tools/md-reader/build_reader.py ../web/book.config.json` 重新打包。書架有變動先跑 `build_shelf.py`。
- 改基準數字：只改 `outline.md` 的基準表 → 重新同步 `running-examples.md` 與 `maintenance.md`（三方逐字相同）→ 傳播進章節 → 重跑一致性檢查。重大修正（推翻既有基準）需兩個獨立來源。
- 動到載重數學：重跑 Tier-2 六家族跨模型驗證（agy＋omp deepseek/qwen/gpt-oss/llama/glm 逐章閉卷重算；harness 在 session scratchpad 的 `verify_chapter.py`／`aggregate_verdicts.py`）。

## 慣例

- `web/index.html` 是產生物，**不要手改**；書架位置由 `../../profile/books.json` 的 `shelf_output` 決定。
- 標點一律全形中文標點；條件機率內文用半形 `|`（`P(A|B)`），數學/比例/分數保持半形。
- **內文不放任何可執行程式碼**（無 ```python、無「Python 小實驗」）；模擬「結果」用 ```text 呈現；視覺化一律用 figures/ 的程式生成圖。
- 跨書：聖彼得堡/紐康/睡美人 的效用・理性深探交叉引用《在不確定中下注》(decide)；共同知識的賽局面指向 game；不可測/無限指向 sets；意外絞刑的自我指涉呼應 godel。
