# maintenance.md — 專家是怎麼煉成的（id expert）

維護本書時的權威基準。改任何基準數字，必須照「一致性基準表」全書同步，並在掃描日誌記一行。事實錨點＝`landscape-2026-06.md`（含末尾「補充」addendum）。

## 一致性基準表（各章不得另創寫法／數字／歸屬）

| 基準 | 鎖定值 | 出現章 |
|---|---|---|
| 脊椎四問診斷表 | ①能力邊緣？②即時回饋？③哪個具體弱點？④可重複？ | ch04 定版，全書回收 |
| Ericsson 1993 小提琴 | Ericsson, Krampe & Tesch-Römer 1993, *Psychological Review* 100(3): 363–406；最佳組到 20 歲平均約 **10,000 小時**；措辭「largely（很大程度上）由練習解釋」 | ch02 定版 |
| 「一萬小時」鐵律 | 是 Ericsson 1993 最佳組到 20 歲的**平均**累積獨自練習，**非門檻、非保證、原文無「法則」** | ch02 全書 |
| Gladwell《Outliers》2008 | 「一萬小時法則」名稱與框架是 **Gladwell 造的、不是 Ericsson** | ch02/ch03 |
| Ericsson 反駁 | 《Peak》2016 明確反駁該法則；生卒 1947–2020（佛州 Tallahassee） | ch02/ch16 |
| Macnamara 2014 五領域 | 練習解釋表現變異：**遊戲 26%／音樂 21%／運動 18%／教育 4%／職業 <1%**——逐一標領域、禁給單一平均 | ch09 定版／ch08/ch10/ch16 |
| 2019 複製（Macnamara & Maitra） | *Royal Society Open Science* 6:190327；到 18 歲最佳組約 **8,224 h** 反比良好組約 **9,844 h** 少、不顯著；效應從 r≈0.70 縮到約 26% | ch03/ch09 |
| Chase–Simon chunking | 1973, *Cognitive Psychology* 4(1):55–81；隨機盤面大師優勢消失；「約 **50,000 個組塊**」是數量級估計 | ch06 定版/ch13 |
| de Groot 棋手 | 1914–2006；大師搜尋不更深、但能近乎完美重建真實盤面 | ch06 |
| 遷移術語 | **近遷移／遠遷移（near/far transfer）**，全書統一 | ch13 |

## 已知脆弱事實清單（最易出錯／最該守住）

- **Macnamara 百分比**：必逐一標領域（26/21/18/4/<1%），落差就是論點，禁用平均值帶過。
- **Gladwell ≠ Ericsson**：法則是 Gladwell 造的、Ericsson 否認——別寫成 Ericsson 自己主張。
- **天賦 vs 練習＝交互非對立**：別寫成「練習無效」或「全是天賦」。
- **8,224 vs 9,844 小時**（2019 複製）方向別寫反（最佳組反而少）。

## 掃描協定

1. 動基準數字 → 先改 landscape，再照上表全書同步，記掃描日誌。
2. 動 ASCII 圖 → `python3 ../../../tools/md-reader/check_diagrams.py book-src`（exit 0 才過）。
3. 動任何 book-src → `python3 ../../../tools/md-reader/lint_book.py book-src`（0 errors）＋重打包 reader。
4. 重大修正（推翻既有基準）需 **2 個獨立來源**。

## 掃描日誌

- **2026-06-21 建書（P1–P5）**：Opus 4.8 起草 ch01–16＋3 附錄（部分 Sonnet 續跑）。P1 self-review＋agy（Gemini 3.5 Flash Medium）修正進 landscape：§五「概念性複製」措辭、r≈0.70/48% 標為後人估計非 1993 原報。
- **2026-06-21 P3**：lint 0 errors；check_diagrams exit 0；spine 16/16；Macnamara 百分比/8224/9844/50k chunks 跨章一致。
- **2026-06-21 P4**：agy 逐章審 16/16；套用驗證過修正（zh-TW 用語、對齊 landscape）；修 landscape 草稿殘留「遠related 任務」→「遠遷移任務」。
- **⚠️ 待網路查證（本 session WebSearch 不可用，未改）**：
  - ch07：間隔練習效應量 g≈0.56–0.82 疑為 Adesope 2017「提取練習」依保留間隔的 moderator 值被掛到「間隔練習（spacing）」；landscape §四/§五此錨點原即「待補從未回填」。需查 spacing 專屬後設分析（如 Cepeda 2006）後回填並修 ch07 worked example。
  - ch08：「pseudo-expertise 溯及 Kahneman」歸屬未鎖、未證；Kahneman 的代表詞或為 illusion of validity。
  - ch09／landscape：§五「約 48% 變異」vs 0.70²=49%（agy 稱原文「49%」）；§四音樂 21% vs §五「約 23%」內部張力（23% 疑為 2019 複製「老師設計練習」值，非統合分析音樂值）。需釐清 landscape §四/§五。
