# maintenance.md — 大腦每晚的維護工作（id sleep）

維護本書時的權威基準。改任何基準數字，必須照「一致性基準表」全書同步，並在掃描日誌記一行。事實錨點＝`landscape-2026-06.md`（含末尾「補充」addendum）。

## 一致性基準表（各章不得另創寫法／數字／歸屬）

| 基準 | 鎖定值 | 出現章 |
|---|---|---|
| 三件維護工作 | 清除（clearance）／鞏固（consolidation）／校準（calibration）——固定三詞，清除證據最不確定 | 全書脊椎／ch01 |
| 雙歷程模型 | Borbély 1982 *Human Neurobiology*；Process S（睡眠壓力）× Process C（生理時鐘）；寫「模型」不寫「已測出兩個鐘」 | ch03 定版 |
| 睡眠分期 | AASM：N1/N2/N3（N3=慢波/深睡）＋REM；NREM 約佔 75–80% | ch02 |
| 睡眠週期 | 一夜 4–5 個；平均 ~90 分（90–110），第一週期常較短——非定鬧鐘常數 | ch02/ch15 |
| 🔥 膠淋巴爭議 | Iliff/Nedergaard 2012 提機制（依 AQP4）；Xie 等 *Science* 2013 稱睡眠時間質空間擴大 ~60%、清除增加；**2024 Miao 等 *Nat Neurosci*（Franks 團隊）反指清除減少**；**2026-06 無共識**，絕不可斷言「睡眠洗掉毒素」 | ch04 定版／ch01 預告 |
| 校準 SHY | Tononi & Cirelli 2003；清醒增強突觸、睡眠降縮；與 ASC 是競爭/互補、都別寫定論 | ch07 |
| 腺苷/咖啡因 | 腺苷促眠（A1R/A2AR），是 Process S 分子對應**之一非唯一**；咖啡因＝腺苷受體拮抗劑，半衰期 ~5–6 h（CYP1A2） | ch03/ch12 |
| 分子鐘（諾獎） | 2017 Hall/Rosbash/Young，**果蠅** per/tim；**1984 分離 period 基因；1990 Hardin/Hall/Rosbash 提 TTFL；1994 楊發現 timeless**；哺乳類 PER/CRY＋CLOCK/BMAL1（CLOCK=高橋 1997）；別把 CRY 安到果蠅 | ch07 定版 |
| 褪黑激素 | 授時/計時信號（chronobiotic）**非安眠藥**；19 試驗：縮短入睡 ~7 分、增加總睡眠 ~8 分 | ch03/ch12 |
| 天生短睡 FNSS | 傅嫈惠團隊；DEC2 2009、ADRB1 2019；某突變者 ~6.25 h 無明顯損害；**極罕、不可推論可習得** | ch13 |

## 已知脆弱事實清單（最易出錯／最該守住）

- **膠淋巴 2013 vs 2024 僵持、無共識**——標準措辭「有力但仍在爭論的假說」，絕不寫「睡眠洗腦」。
- **Walker《Why We Sleep》戲劇數字**（致癌加倍、FFI 因缺睡而死、WHO 列致癌、U 形死亡、人人需 8h）一律不引為定論。
- **諾獎是果蠅 per/tim**；TTFL=Hardin **1990**（非 1984，1984 是分離 period 基因）；MCTQ=2003。
- **腺苷是 Process S 之一非唯一**；褪黑激素非安眠藥。

## 掃描協定

1. 動基準數字 → 先改 landscape，再全書同步，記日誌。2. ASCII 圖 → `check_diagrams.py book-src`（exit 0）。3. book-src → `lint_book.py book-src`（0 errors）＋重打包。4. 重大修正需 2 獨立來源。

## 掃描日誌

- **2026-06-21 建書（P1–P5）**：起草 ch01–16＋3 附錄（Sonnet 續跑）。P1 agy 修正進 landscape：TTFL=Hardin 1990（與 1984 分離基因分開）、MCTQ=2003、多相睡眠改述為高退出 cohort（非個案）。
- **2026-06-21 P3**：lint 0 errors；diagrams exit 0（重生成 ch02 hypnogram、ch03 S/C 曲線圖達 CJK=2 對齊）；spine 16/16；glymphatic ~60%、melatonin 7/8 分、90 分週期、FNSS 6.25h 一致；ch07 TTFL 年份（1984 基因/1990 TTFL/1994 TIM）正確、果蠅 per/tim vs 哺乳類 PER/CRY 正確。
- **2026-06-21 P4**：agy 逐章審 16/16；套用驗證修正（zh-TW 用語如「尸解→大體解剖」、對齊 landscape、膠淋巴過度宣稱收斂為 hedge）。
- **⚠️ 待網路查證（未改）**：ch09「涵蓋 37 項研究的網絡後設分析…緩解率 41%/28%」agy 指應為 Furukawa 2024「13 項 RCT（823 人）」；ch05 Newbury 睡眠剝奪 meta 年份 2022 vs 2021；ch10 食慾素神經元數「70,000–80,000」vs「50,000–80,000」；ch02「~96 分鐘中位數週期（ScienceDirect 2023）」歸屬。
