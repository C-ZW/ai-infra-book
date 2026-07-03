# 維護與掃描（內部文件，非書籍內容）

本書《沒說出口的那句》主題以**經典悖論**為主，絕大多數是**常青（evergreen）**內容（數學結構、歷史歸屬）。沒有版本／價格／硬體這類高頻時效性事實，因此**不設 landscape-<date> 時效基準檔**；歷史歸屬的事實基準在 `_meta/landscape-history.md`，脆弱處以 ⚠️ 標記。

## 1. 基準數字表（canonical；與 `outline.md`／`running-examples.md` 三方逐字相同）

| 代號 | 數值 | 單位／意義 | 擁有概念 | 引用章節 |
|---|---|---|---|---|
| B1 | 2/3 | 蒙提霍爾：切換的獲勝機率 | 條件機率／資訊 | ch02, ch03, ch04, ch27 |
| B2 | 1/3 | 蒙提霍爾：維持原選的獲勝機率（＝1−2/3） | 條件機率 | ch02, ch03, ch27 |
| B3 | 1/1000 | 偽陽性範例：疾病盛行率 | 基率 | ch06, ch27 |
| B4 | 99% | 偽陽性範例：檢測敏感度＝特異度 | 條件機率 | ch06, ch27 |
| B5 | 9.02% | P(有病∣陽性)＝(0.001·0.99)/(0.001·0.99+0.999·0.01)≈0.0902 | 貝氏更新 | ch06, ch27 |
| B6 | 23 | 生日問題：碰撞機率首度超過 ½ 的人數 | 組合／碰撞 | ch09, ch27 |
| B7 | 50.73% | 23 人時至少一對同生日的機率＝1−(365·364·…·343)/365²³ | 組合 | ch09, ch27 |
| B8 | 1 − i/N | 公平賭局的破產機率（起始資本 i、總資本 N；對手 N−i） | 吸收馬可夫鏈 | ch10, ch27 |
| B9 | 18/38 | 美式輪盤押紅單次獲勝機率＝0.4737 | 賭局優勢 | ch10, ch11 |
| B10 | ∞ | 聖彼得堡賭局期望報酬＝Σ(n=1→∞) 2ⁿ·(1/2ⁿ)＝Σ 1＝∞ | 期望值≠價格 | ch12, ch13, ch27 |
| B11 | 100 | 紅藍眼睛：島上藍眼人數（第 100 天集體離島） | 共同知識 | ch15, ch27 |
| B12 | 30.10% | 班佛定律：首位數字為 1 的機率＝log₁₀2 | 尺度不變 | ch25, ch27 |

非 B 表但載重的招牌數字（各由所屬章自行導出、自我複核）：非傳遞骰子相鄰對 2/3、C 對 A＝5/9、B 對 D＝1/2（ch19）；聖彼得堡對數效用零財富願付價＝4 達克特（ch12）；布雷斯加邊前 1.5／後 2.0、PoA＝4/3（ch21）；紐康 CDT/EDT（ch22）。

## 2. 脆弱事實索引（fragile facts；改動或再版前務必重查，均源自 landscape-history 的 ⚠️）

- **蒙提霍爾（ch02）**：vos Savant「約一萬封信／近千位博士／約 92% 說她錯」是她**本人自述、未經第三方稽核**——書中已標「她說的規模」。日期 **1990-09-09**（勿寫 9-2）。Erdős 靠模擬才信服＝單一傳記來源（Hoffman 1998）。
- **賭徒謬誤蒙地卡羅 1913（ch11）**：連黑 26 次的故事只溯及單一現代 BBC 來源、無 1913 一手佐證——書中已留餘地。
- **熱手 Miller–Sanjurjo 2018（ch11）**：措辭必須是「1985 的證偽本身有有限樣本偏誤、效應可能真的存在」，**不得**寫「熱手已證實為真」。
- **男孩女孩（ch05）**：1/3 vs 1/2 vs 13/27 是**欠定問題**（Bar-Hillel & Falk 1982），依抽樣程序而定，非唯一定論。
- **四個「無公認解」悖論**：睡美人（ch23）、兩個信封的無界先驗版（ch13，有限版已解）、意外絞刑（ch17）、紐康（ch22）——任一方都不得寫成標準正解。
- **兩位將軍（ch18）**：第三作者 **Huber**（非 Huang）；1975 幫派版證不可能、Gray 1978 命名「將軍」。
- **辛普森（ch07）**：Yule 1903／Pearson 1899 在前、Simpson 1951 本人未用「paradox」、Blyth 1972 才命名；Berkeley 1973 申請人數 **男 8,442／女 4,321（合計 12,763）**。
- **班佛（ch25）**：法庭採認只在地院 Daubert 層級；**勿引「881 F.3d 806 (10th Cir. 2018)」為採認先例**（該上訴意見未提 Benford）。
- **巴拿赫–塔斯基（ch26）**：需超出 DC 的選擇原則、**但弱於完整 AC（Hahn–Banach 即足，Pawlikowski 1991）**；勿寫「需完整 AC」或「B-T⟺AC」；最少 **5** 片（Robinson 1947）。
- **聖彼得堡（ch12）**：首倡 Nicolaus I Bernoulli 1713、Daniel 1738 對數解、名稱源自院刊（非賭局地點）——與《在不確定中下注》(decide) 歸屬一致。
- **共同知識（ch15）**：藍眼島民包裝**無確認 originator，勿歸 Littlewood**；形式化 Friedell 1969／Lewis 1969／Aumann 1976。
- **非傳遞骰子（ch19）**：**並非每對都 2/3**——C 對 A＝5/9、B 對 D＝1/2。

## 3. 掃描協定（`update`／`rescan` 執行的具體步驟；idempotent）

1. 重讀 `landscape-history.md` 的每一條 ⚠️，用 WebSearch/WebFetch 逐一重查；有變動就更新該檔。
2. 任何基準數字（B1–B12）若需改動：改**唯一真相** `outline.md` 的基準數字表 → 由它重新生成 `_meta/running-examples.md` 與本檔第 1 節（temp 檔＋原子改名）→ 傳播進章節內文 → 重跑 P3 一致性與三方逐字相同斷言。
3. 重跑 Tier-1：`python3 ../../../../tools/md-reader/lint_book.py . --lang zh-TW --config _meta/lint.config.json`（exit 0）＋ `check_diagrams.py .`（exit 0）＋ 全書半形標點/簡體字掃描（見第 5 節工具）。
4. 若載重數學/推導有改：重跑 Tier-2 六家族驗證（agy＋omp deepseek/qwen/gpt-oss/llama/glm，逐章閉卷重算，見 scratchpad `verify_chapter.py`／`aggregate_verdicts.py`）。
5. 動到圖：`python3 ../../../../tools/md-reader/build_figures.py figures`。動到任何內容：`python3 ../../../../tools/md-reader/build_reader.py ../web/book.config.json` 重新打包（皆從 book-src 執行）。
6. 在第 4 節掃描日誌補一行。

## 4. 掃描日誌

- **2026-07-02｜建立（full）**：ch01–ch27 ＋ 附錄 A/B/C 全數寫成。Tier-1 lint 0 錯 0 警、check_diagrams 0 可疑、B1–B12 跨章一致、三方基準表逐字相同、cross-ref 0 斷。Tier-2：agy＋omp 五家族（deepseek/qwen/gpt-oss/llama/glm）逐章閉卷重算。
  - Tier-2 實際用**六家族**：agy(Gemini)＋omp deepseek-v4-pro／qwen3.5-122b／gpt-oss-120b／llama-3.3-70b／glm-5.1，逐章閉卷重算。0 FAIL（所有 FAIL 均為 pre-cleanup 舊稿的過時發現，於現稿已修）。
  - 建置期修正：landscape Berkeley 申請人數 男 12,763 → **男 8,442／女 4,321（合計 12,763）**（ch07 agent 經 R UCBAdmissions＋Science 摘要查出）；ch02 蒙地卡羅數字改為「約 33% / 約 67%」（原 33.08/66.92 與模擬不一致）；ch01–12 移除 `### Python 小實驗` 程式區塊（改用 ```text 呈現結果，使用者要求內文不放程式）；全書半形標點正規化為全形；ch02 一個混入的簡體「隨」字修正為正體。
  - P4 六家族審查採納之真實修正：ch07 分解公式權重放反（(1−w女)/w女 對調）＋兩處四捨五入（27.8→27.7、53.8→53.7）；ch06「盛行率提高 100 倍」→「10 倍」；ch09 30 天曆法累積機率 0.586458→0.586444、0.469167→0.469156；ch10 不公平版遞迴 p·q_{i-1}+q·q_{i+1}→p·q_{i+1}+q·q_{i-1}（與自身封閉解一致）、N=1000 破產機率描述、(10/9)^200/400 估算；ch14 π₂ 除法 1.161435→1.161565；ch15 xkcd 年份去除爭議、與 ch16 Kraitchik 1942 一致化；ch18 練習1解答訊息收送方向誤植；ch27 「輪盤優勢 18/38」→「押紅機率」。駁回之偽陽性：ch05／ch19／ch22 模型自陳「書中正確」；ch14 其餘四位小數截斷、ch17 蒯因詮釋、ch20 Llull 史料等皆已 hedge 或低於本書精度。ch01 補連通圖前提。

## 5. Bridge Registry 鎖定（每章的核准橋接來源；profile 改變時須逐一重驗）

ch01 none｜ch02 條件機率(讀者已知)｜ch03 ch02｜ch04 ch02｜ch05 ch02｜ch06 none｜ch07 none｜ch08 ch06｜ch09 none｜ch10 none｜ch11 ch10｜ch12 none｜ch13 ch12｜ch14 ch10｜ch15 none｜ch16 ch15｜ch17 none｜ch18 ch15｜ch19 none｜ch20 ch19｜ch21 none｜ch22 none｜ch23 ch06｜ch24 none｜ch25 none｜ch26 none｜ch27 none。
來源使用次數：ch02×3（ch03/04/05，達上限）、ch06×2（ch08/23）、ch10×2（ch11/14）、ch15×2（ch16/18）、ch19×1（ch20）。皆 ≤3。

## 6. 已知工具限制與教訓

- **lint 的簡體字盲點**：含「不是／非「」等對比提示（contrast cue）的行，forbidden-char 檢查會被抑制——真夾帶的簡體字（如 ch02「随」）會漏掉。發佈前用獨立掃描（不套 contrast 抑制）補查一次。
- **半形標點**：lint 不檢查標點寬度；批次寫章時個別 agent 若中途 API 中斷（如 ch02）可能未自我正規化，須全書掃 `(?<=CJK或全形括號)[,:;?!]` 補正（保護 `![]()`、`P(A|B)`、比例 `1:2`、程式碼）。
- **圖檔位置**：一律 `book-src/figures/*.py` → `figures/out/*.svg`；內文 `![說明](figures/out/…svg)`，圖說內**不得有 `]`**、`!` 保持半形（勿被標點正規化改成 `！[`）。
- **omp NVIDIA 模型會漂移**：批次驗證前先探活（見 repo 根 `omp-nvidia-models.md`，2026-07-01 記錄 qwen3-235b 轉 404、qwen3.5-122b 可用）。**agy 對大文件會卡死**（整本大綱），但**逐章（單章）可用**且擅長抓算術/公式錯。
