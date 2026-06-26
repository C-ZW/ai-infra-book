# 建書規劃（內部文件，/compact 後的執行依據）

## 一句話

把《保證與取捨》（id `rsys`，速查／概念地圖）的每個主題，**重寫成一本深入、敘事體的技術書**——一主題一章，讀的不是速查表而是真正能坐下來讀懂的書。

## 基本資料

- 書名：**《機制之下》**，副標「後端與分散式系統如何運作、為何如此」。
- id：`mech`（全域唯一，登記簿 `../../../profile/books.json`；建書時 fresh-read 去重）。
- 資料夾：`books/backend-mechanisms/`；book-src／web／CLAUDE.md 比照其他書。
- 語言：繁體中文（台灣用語）。reader light mode。

## 與 `rsys` 的關係

- **`rsys` 原封不動保留**、照常上架。兩本並存、互補：`rsys`＝快速查閱的地圖；`mech`＝深讀版本。
- `mech` **重用 `rsys` 已通過三方查證的內容當底子**（加深＋敘事化，不從零寫起；新增深度仍要查證）。`rsys` 的主題清單見其 `books/resume-systems/book-src/_meta/outline.md`（~150 個 `##` 概念、22 領域 A–V、8 個 Part）。

## 讀者

一般資深後端／軟體工程師（約 3–8 年實戰）：會寫程式、HTTP／資料庫／交易／並發／雲端用到工作級；**不**預設讀過分散式理論（不假設讀過 Paxos／FLP）。本書補「會用、但底下只有模糊直覺、沒系統化想透」的那層，講到機制級。不寫給完全新手、也不寫給分散式研究者。

## 章節切法

- **預設：一個 `rsys` 主題＝一章**（約 150 章）。
- **可合併**：太薄、或關係太緊、拆開反而不自然的主題，合成一章（如 at-most／at-least／exactly-once＋冪等＋去重 → 一章；Redis 內部數個點 → 一章）。合併判斷在 P1 大綱階段逐 Part 決定，最終約 ~150 章上下。
- 依 Part（領域 A–V）分組；每章一個檔＝reader 一個 doc，sidebar 即章名。

## 每章格式（這是與 `rsys` 最大的差異，務必守）

- **敘事散文**：先用情境／問題鉤住 → 把概念一路展開 → 用敘事把機制講透 → 取捨與故障模式作為「故事裡的後果」浮現 → 收在更深的「為何如此」。
- **不要**那套固定六段骨架（定義與原理／解法空間／…），**不要**把對照表當骨幹。小標是有機的、為這一章的敘事服務。
- 表格／pseudo-code 可用，但只當敘事裡的輔助元素，不是主結構。
- **無練習段**。
- **長度看主題、零填充**：深度＝把這個主題講透所需的長度。consensus 要長就長、health-check 該短就短。不准湊字數。
- 深度標竿：見 P1 產出的完整樣章（consensus），fan-out 前所有寫章 agent 以它為準。

## 沿用 `rsys` 的契約

繁中台灣用語、禁簡體詞；**不提任何個人／公司系統**（NeoBards／LetsTalk／Bahwan 等一律不准）；**禁「你以為 vs 實際」糾錯口吻**；延伸閱讀放外部真實連結、**不指向其他書**；自足；程式碼／設定／註解一律英文。

## 執行流程（P1 先做、設閘）

1. **P1 — meta＋樣章**：寫 `mech` 的 `style-guide.md`（敘事章寫作契約）＋ `outline.md`（章清單，含合併決定，從 `rsys` outline 衍生）＋沿用 `rsys` 的 `landscape-2026-06.md` 當事實底。**並寫一整章完整樣章（consensus）當深度／格式標竿。**
   - **閘：把 outline＋樣章給使用者過目、停下等核准，再 fan-out。**（最高槓桿 QA 點）
2. **P2 — 逐章 fan-out**：用 Workflow，一章一 agent，分批；每 agent 先讀 meta＋樣章＋對應 `rsys` 條目當底，寫成敘事章；自行 3–8 次 web 查證。
3. **P3 — 一致性**：lint_book（繁中、禁簡體；本書無六段骨架，skeleton 檢查不適用、改用敘事章自己的輕量檢查）＋ check_diagrams（ASCII 圖 CJK=2）＋紅線 grep（個人系統／糾錯／他書／殘留）。
4. **P4 — 三方事實查證**：比照 `rsys` 已驗證流程——Claude 逐章 holistic＋agy 逐章跨家族（Gemini Flash High，小提示／逐項展示）＋爭點 web 獨立複查；verify-before-apply（審稿發現是假設不是定論，逐條對原文複查再改）。
5. **P5 — 打包**：新 `web/book.config.json`（Part 分組）→ build_reader → build_shelf → render check（CJK box 抽查）→ 登記 `books.json`（id `mech`，防呆 fresh-read 去重）→ 寫 `maintenance.md`＋book CLAUDE.md。

## 工具與路徑（從本 book 根 `books/backend-mechanisms/` 起算）

- 工具實際在 `/Users/cheweichen/Desktop/personal/tools/md-reader/`（從 book 根算 `../../../tools/`、從 book-src 算 `../../../../tools/`；用絕對路徑最穩）。
- lint：`python3 ../../../tools/md-reader/lint_book.py book-src`；圖：`check_diagrams.py book-src`；打包：`build_reader.py web/book.config.json` → `build_shelf.py`。
- agy 操作鐵律：小提示、逐章、perl-alarm 綁時限（`perl -e 'alarm 320; exec @ARGV' agy --model "Gemini 3.5 Flash (High)" --print-timeout 6m -p "..."`），每次 `pkill -9 -f "agy --model"` 清殭屍；桌面 app 關閉時較穩；部分檔可能 content-filter 回空（由 Claude＋web 補）。

## 規模

~150 章深度敘事＋三方查證＝非常大的 fleet 工程（多個 Workflow、數小時 agent 時間）。ultracode 下進行。
