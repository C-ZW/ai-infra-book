# 維護手冊（內部文件，非書籍內容）

本書《正常意外：複雜系統如何崩壞》的跨章一致性基準、脆弱事實清單、結構同步雷區、掃描協定與掃描日誌。**改任何內容前先讀本檔。**

## 一、本書的「貨幣」：失敗模式語言 F1–F14

全書招牌＝一套可重用的失敗模式編號（定義在 `style-guide.md` 基準表）。三處必須永遠同步，改一處要回頭改另兩處：
1. `style-guide.md` 的 F1–F14 基準表（定義來源）。
2. `appendix-b-failure-modes.md`（每個 F 的詳目＋本書命中案例清單）。
3. `ch23` 的全書 F1–F14×案例總表。

各章 `## 故障解剖` 的「對應模式」只能引用 F1–F14、不得自創編號。要新增模式必須先在 style-guide 登記、再同步上述三處。

## 二、案例取材原則（不可違反）

刻意**排除** jserv《軟體失效案例》合集（https://hackmd.io/@sysprog/software-failure）已收的案例，**永不採為主案、也不在內文當範例引用**：Therac-25、Ariane 5、Mars Climate Orbiter、Patriot 飛彈、Pentium FDIV、AT&T 1990、北美大停電 2003、Knight Capital、Toyota 暴衝、Mars Polar Lander、787、Y2K、Ping of Death、英國郵局 Horizon、PayPal、台股熔斷、Flexcoin、PSY 計數溢位。掃描時若發現這些字串出現在 `ch*.md` / `appendix*.md`，視為迴歸錯誤、須清除（共因失效的範例改用挑戰者雙 O-ring（ch14）、單位錯誤改用金姆利（ch07）、級聯改用 Cloudflare/CrowdStrike（ch10/ch13））。

## 三、脆弱事實清單（最常被挑戰、一律 hedge，以 landscape 為準）

| 事實 | 書中寫法（hedge） | 章 |
|---|---|---|
| 車諾比死亡數 | 短期確認約 31；長期可歸因估計差異極大（約數千～數萬），給範圍、不釘單一數 | ch17 |
| 德州電網死亡／損失 | 死亡官方約 210–246 vs 研究約 700（給範圍）；損失約 800–1,300 億美元（估計） | ch12 |
| Morris 蠕蟲受影響台數 | 估約 6,000 台／約當時連網 10%（period estimate，標估計） | ch18 |
| Sleipner 損失金額 | 估計達數億美元（常見引述約 7 億，未必有單一權威出處） | ch09 |
| Schiaparelli IMU 飽和時長 | 「飽和持續超出設計預期時間」，不釘秒數（各來源約 1 秒；推進器點火約 3 秒是另一回事，勿混） | ch08 |
| 閃電崩盤歸因 | 觸發＝大型賣出演算法×HFT 撤流動性；Sarao 的 spoofing 貢獻有爭議（2010 報告不依賴他） | ch11 |
| VSE 週五收盤值 | landscape 採 524.881（McCullough 系），另有 524.811 變體；以 landscape 為準、變體於延伸閱讀註明 | ch21 |
| CrowdStrike 影響台數／損失 | 估約 850 萬台；經濟損失（如約 54 億美元）皆第三方估計、標估計 | ch13 |
| 737 MAX 權限放大 | 0.6°→2.5°、可每約 5 秒重複、無累積上限（多源一致） | ch04 |

所有死傷／金額／規模類數字一律標估計或給範圍。歷史與時效性事實以 `landscape-2026-06.md` 為事實基準；查到需修正時：更新 landscape →依本表同步引用章→同步 `appendix-a-timeline.md`（**它是數字的第二存放處，最易與章節脫鉤，務必一起改**）→在下方掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。

## 四、結構同步雷區

- **全書 ASCII 路線圖**出現在 **7 個 Part 首章＋outline 基準圖**：`ch01、ch04、ch07、ch10、ch14、ch18、ch22` ＋ `_meta/outline.md`。改路線圖須同步 8 處。
  - **連接線只能用 `▼ ▲ ◄`（不可用 `↓ ↑ ←`）**——`check_diagrams.py` 只把 `▼▲` 認作垂直連接、把裸 `↓↑` 判為「未連」而 FAIL（2026-06-13 教訓：ch04 一度用裸箭頭 FAIL）。基準圖在 outline.md，每個 Part 首章照抄、只把 `◄你在這裡` 標到該 Part。
  - Part VI 含 4 章（ch18–21，含 ch21 靜默的錯誤）；Part VII 為 ch22–23。
- **ch23 全書 F1–F14×案例總表**、**appendix-b**、**style-guide F 表**三者同步（見第一節）。
- **附錄 A 年表**是各案數字的第二存放處——landscape 數字一改，年表要同步（見第三節）。
- 章節編號：23 章。ch21＝靜默的錯誤（VSE，2026-06-13 依 agy 第二意見補入；resilience 由 ch21→ch22、finale ch22→ch23 已全書重編號）。日後再插章須做同樣的高到低 token 重編號＋更新所有 `（見 chNN）`、路線圖、附錄。

## 五、渲染與工具慣例

- 動到 ASCII 圖後（從本目錄 `books/systems-failure/` 執行）：
  `python3 ../../../tools/md-reader/check_diagrams.py book-src`（**傳目錄非單檔**；exit 0 才算過；CJK=2 欄規則）。
- 動到任何內容：`python3 ../../../tools/md-reader/build_reader.py web/book.config.json` 重打包，再 `python3 ../../../tools/md-reader/build_shelf.py` 更新書架。
- `web/index.html` 與專案根 `bookshelf.html` 是產生物，**不要手改**。
- 簡體詞 lint 用逐字元比對（shell grep 對繁簡同形字如 偏/差/線/誤 會誤報）。
- 內部註記（`⚠️ 待協調者複核`）一律不得留在成書 `ch*.md`／`appendix*.md`（會在閱讀器顯示）；P3 已全數移除，日後新增章節須再掃一次。
- 程式碼／設定檔／註解一律英文；書內容繁體中文（台灣用語、禁簡體詞、技術名詞留英文）。

## 六、掃描協定

「掃描書的時效性」＝逐案重核 landscape 的硬事實（尤以近年事故為先：CrowdStrike 2024、SolarWinds、Log4Shell、德州電網），更新後依第三節同步鏈處理。結構掃描＝跑 check_diagrams（圖）＋ grep 排除案例（取材原則）＋ grep `待協調者複核`（內部註記殘留）＋ 骨架標題 grep。

## 七、掃描日誌

- **2026-06-13｜建書**：P1–P5 完成。23 章（ch01–ch23）＋3 附錄。landscape 三輪查證（25＋8＋1=34 案，I 段案例 34＝VSE）。check_diagrams exit 0（21 圖）。簡體 0、排除案例 0、待協調者複核 0、骨架 22→23 章齊。agy 結構審＋5 WebSearch 事實抽查（于伯林根 TCAS 優先規則、閃電崩盤 W&R/Sarao、德州 4 分 37 秒、阿波羅 1202、塔科馬 flutter）全過。agy 建議補「靜默資料損毀」→補 ch21（VSE），resilience/finale 重編號為 ch22/ch23。fact baseline 三處仍可硬化：Sleipner $700M、Schiaparelli 飽和秒數、AT&T（已排除，不再使用）。
