# Maintenance — 維護手冊（內部文件）

本書事實基準時點 **2026-06**。歷史歸屬與時效性事實以 `_meta/landscape-2026-06.md` 為錨；改任何跨章基準必須照下表全書同步，並在本檔掃描日誌記一行。重大修正（推翻既有基準）需兩個獨立來源。

## 跨章一致性基準表

改動下列任何數字／命名，必須 grep 全書同步所有引用章：

| 基準 | 值 | 出現章 |
|---|---|---|
| 記號系統 | E[N]/E[T] 系統（非 L/W）；λ μ ρ=λ/(cμ) a=λ/μ；C²ₐ C²ₛ；S/T/T_Q/N/N_Q；單字母下標用 Unicode、多字母用底線 | 全書；L/W 對照僅 ch02＋附錄 A |
| 推播管線單 worker | E[S]=100 ms（μ=10/s）、尖峰 λ=8/s、ρ=0.8 | ch01（體感）、ch08（推導） |
| M/M/1 基準結果 | πₙ=0.2·0.8ⁿ；E[N]=4、E[T]=0.5 s、E[N_Q]=3.2、E[T_Q]=0.4 s；T~Exp(2)、t₉₉=ln100/2≈2.30 s（P99≈4.6×平均） | ch08；引用 ch03/ch07/ch10/ch19 |
| 使用率階梯 | E[T]=E[S]/(1−ρ)：0.5→0.2、0.8→0.5、0.9→1.0、0.95→2.0、0.99→10 s | ch01、ch08 |
| M/M/c 基準 | c=4、λ=32/s、μ=10/s、a=3.2、ρ=0.8；Erlang-C≈0.596、E[T_Q]≈74.6 ms、E[T]≈175 ms（Erlang-B 遞迴 B(1..4,3.2)=0.762/0.549/0.369/0.228） | ch09；引用 ch14（×1.5≈112 ms）、ch16 |
| 池化三連比 | 同 λ=32：4 台獨立 M/M/1 各 λ=8 → 0.5 s；共用 M/M/4 → 0.175 s；單台快機 μ=40 → 0.125 s | ch09 |
| 有限容量基準 | M/M/1/K：K=10、μ=10；λ=8 → π_K=0.0235、λ_eff=7.81、E[T]=0.380 s；λ=12 → π_K=0.193、λ_eff=9.69、E[T]=0.693 s | ch10 |
| 串聯基準（tandem） | λ=6、μ₁=10、μ₂=8 → ρ₁=0.6、ρ₂=0.75、E[N₁]=1.5、E[N₂]=3、E[T]=0.75 s | ch11；對照 ch16 |
| M/G/1 基準 | λ=8、E[S]=100 ms、ρ=0.8；C²ₛ∈{0,1,10} → E[T_Q]=0.2/0.4/2.2 s、E[T]=0.3/0.5/2.3 s、E[N]=2.4/4.0/18.4 | ch12；引用 ch13/ch14 |
| 排程基準混合 | 短 90%/E[S]=50 ms、長 10%/E[S]=550 ms；混合 E[S]=100 ms、λ=8、ρ=0.8；二點 C²ₛ=10 分布＝50 ms w.p.40/41＋2,100 ms w.p.1/41 | ch03（存在示範）、ch04、ch12（基準）、ch13 |
| Kingman 基準 | M/G/1 基準＋C²ₐ=2、C²ₛ=1 → E[T_Q]≈4·0.1·(2+1)/2=0.6 s；上界版≈0.825 s | ch14；ch10 借用整形算例 0.4→0.2 s |
| 重尾基準 | Pareto α=1.5、k=E[S](α−1)/α=33.3 ms（=1/30 s）、E[S]=100 ms（變異數無限）；P(S>1 s)=0.00609≈同均值指數的134×；Bounded Pareto 上界階梯 p∈{10,100,1000 s} | ch15；引用 ch19（Pareto 服務模擬） |
| Jackson 基準 | λ₀=6/s → node1(μ₁=10) → node2(μ₂=8)，node2 以 p=0.2 回 node1；解 λ₁=λ₂=7.5、ρ₁=0.75、ρ₂=0.9375、E[N]=18、E[T]=3.0 s；p=0.3 → ρ₂≈1.07>1 爆炸；懸崖 p*=0.25 | ch16 |
| 封閉網路 MVA 基準 | 2 站、E[S₁]=100 ms、E[S₂]=200 ms（訪次各 1）、Z=1 s；X(1)=0.769、X(5)=3.311（E[T]=0.510 s）、X(6)=3.766、漸近 X→5/s、拐點 N*=6.5 | ch02（bounds）、ch17（MVA 全表） |
| fork-join 基準 | n 路各 Exp(μ)：E[max]=Hₙ/μ；H₂=1.5、H₄=2.083、H₁₀=2.929；n=10 P99≈0.690 s（無排隊理想化、獨立近似） | ch18 |
| 模擬 ground truth | M/M/1 基準（E[N]=4、E[T]=0.5 s、P99≈2.30 s）為 ch19 全部方法學的校準標的 | ch19 |
| ch01「經驗法則審判」清單 | 8 條編號，ch20 總結表逐條宣判（3 條附條件成立：#1/#2/#6；5 條推翻：#3/#4/#5/#7/#8） | ch01 立、ch20 結 |
| 數字常數 | e≈2.71828、ln2≈0.6931、ln100≈4.6052；數值預設 3 位有效數字 | 全書 |

## 脆弱事實清單（最容易過期／出錯的點）

1. **歷史歸屬（landscape §2）**：Kingman 有**兩篇**（1961 PCPS 短註、1962 JRSS-B 一般化＋1962 Biometrika 變異數）；Schrage 1968 是 Letter to the Editor；BCMP 是 JACM 22(2):248–260 四作者；Pollaczek 1930／Khinchine 1932 兩人各自貢獻。引歸屬前一律對 landscape，禁憑記憶。
2. **landscape 兩個 ⚠️ 未驗證項**：(a) Khinchine 1932 的 Matematicheskii Sbornik 卷期頁（僅 Wikipedia 引用鏈）；(b) square-root staffing 的「Erlang 1924」年份（來源只說「long-existing rule of thumb」）。全書措辭已避開硬斷言（ch09/ch14 寫「可上溯至 Erlang」不帶年份）——掃描時確認沒有章節把這兩項寫成硬事實。
3. **教科書版次陷阱**：Harchol-Balter 2013 主教科書**無免費 PDF**（她明言 Kindle 版會弄亂數學）；她 2024《Introduction to Probability for Computing》才是免費全書。《Fundamentals of Queueing Theory》第 5 版作者序改為 Shortle/Thompson/Gross/Harris——舊習慣寫「Gross & Harris」對現行版是錯的。
4. **強時效連結（2026-06）**：simpy 4.1.2（2026-05）、ciw 3.2.7（2025-12）、vLLM v0.22.1（2026-06）——版本號別寫死精確日期，掃描時更新。continuous batching＋PagedAttention 已是 LLM serving 業界基線（ch20 點綴，深度指 aiib）。
5. **個人頁／課程頁易腐**：Adan–Resing（TU/e 個人 subdomain，canonical URL 會 301 轉 iadan.win.tue.nl）、CMU ~harchol 的免費 PDF、Kelly《Reversibility and Stochastic Networks》作者頁（全書統一用 `~fpk1/rsn.html`，**勿**用 `~frank/BOOKS/kelly_book.html`——兩者皆 200 但已選定前者）。下次掃描開頁抽查；考慮在仍可解析時 vendored 一份本機備份。
6. **章驗證但不在 landscape 的連結**：附錄 D 有約 40 條連結是寫章 agent 自行查證、未進 landscape（已標「章驗證」）。掃描時優先 HTTP 抽查這批（尤其 Flatto–Hahn 1984 無 URL、Sevcik–Mitrani ACM 對 bot 回 403）。
7. **4.6× 與 4.64× 的撞名**：ch08 的「P99≈4.6×平均」（ln100 截尾）與 ch15 的重尾每多一個 9 分位 ×4.64（10^(2/3)）數字相近但意義不同——ch15 已自行點明是巧合撞名，**非錯誤**，勿「順手統一」。
8. **附錄 A/C 的「首次出現章」**用「正式定義章」而非「字面首次提及」（前向引用如 πₙ ch03 預告/ch08 定義、inspection paradox ch04 指數特例/ch12 一般版、Kendall ch01 提及/ch08 定義）——兩附錄卷末有編表說明。改動符號或術語使用後需抽查重驗。

## 結構提醒

- 章節骨架六標題（從你已知的出發／陷阱與防禦／紙上推演＋推演解答／自我檢核／延伸閱讀）是一致性掃描的 grep 對象，改標題格式前先想清楚。
- 全書路線圖在 Part 首章 ch01、ch03、ch07、ch12、ch16、ch19 共 6 張（ch21 收尾再放一張全走過版）——改章名要同步七處。
- Python 小實驗章＝ch05、ch08、ch12、ch15、ch17、ch19、ch20；規範：標準函式庫優先、`random.seed(42)`、每段 ≤40 行、預期輸出寫成「理論值 X、模擬值落在區間」而非假裝精確。
- 內文數學符號一律 Unicode；程式碼與註解一律英文。
- 簡體詞 lint 注意「效」「系」「准」等兩岸同形字會誤報；用 Python 逐字元比對、不要用 shell grep 的 byte-matching（`對象` 在 TW 可指「目標」但本書禁用，改 `主角`/`物件`）。
- **圖的渲染對齊與來源對齊是兩個故障域**：`check_diagrams.py` 只驗源碼的欄數學（CJK=2 模型）；渲染端由 build_reader 的 `wrapCJK` span 機制保證（勿改回 @font-face size-adjust——WebKit 對 local() 忽略它，Safari 會塌、Chrome 看起來正常）。改動閱讀器或圖之後：headless Chrome 截一張中文多的框圖＋使用者瀏覽器目視各驗一次。

## 掃描協定（「掃描書的時效性」＝執行本節）

1. 重驗 landscape 的 ⚠️ 條目（Khinchine 1932 卷期、square-root staffing 年份）——維持 hedge，勿硬斷言。
2. 工具版本掃一輪（simpy、ciw、vLLM／continuous batching 業界狀態），依「脆弱事實」第 4 條措辭更新。
3. 開頁抽查易腐連結（Adan–Resing、CMU ~harchol、Kelly 作者頁）＋附錄 D 的「章驗證」批次 HTTP 抽查。
4. 有修正 → 更新 landscape ＋依基準表同步引用章 ＋ 本檔日誌記一行；動到 ASCII 圖跑 `check_diagrams.py`；重打包（見書級 CLAUDE.md）。

## 掃描日誌

- **2026-06-12**：成書 P0–P1。P0 校準（goals 快速確認不變、語言＝繁中、定位＝數學嚴謹為主、規模＝21 章）；landscape 由研究 agent 建立（約 30 次查證，每個免費 PDF／課程連結實際 fetch 確認）；style-guide／outline 定稿；大綱經 agy（Gemini 3.1 Pro High）結構＋數學審查（MATH PASS，結構 4 項建議全採納：ch08 先introduce DES 骨架、ch10 加 rate limiting、ch18 升 fork-join 為主角段、ch06 安撫線代焦慮、ch13 接 Node.js event loop、ch12 不用 renewal 術語），使用者於大綱關卡核准。
- **2026-06-19**：P2 完成 21 章＋4 附錄（章節 fan-out 分三批；ch19–21 因 session 限額隔日重跑）。P3 一致性：骨架 21/21、Python 章 7/7、簡體 lint 修 1 處（ch20 對象→主角）、check_diagrams exit 0（38 圖）、跨章基準數字交叉核對一致、Kelly 連結統一（ch16 → fpk1）、章首標題與 outline 對齊、跨章引用全在範圍。P4a：agy（Gemini 3.5 Flash High）逐章 math-only 審查（含附錄 A/B）22 PASS＋1 真 FAIL（ch20 batching：438 ms 標成「第一件」應為「平均每件」，第一件實為 875 ms），已修正並改寫為兼列平均與最大值；重跑確認 PASS，零誣告（延續既有 agy 分工記錄）。
- **2026-06-19（P4b）**：獨立第二意見（Claude general-purpose＋網路）：結構審 A1 依賴完整／A3 敘事回收全兌現（ch01 審判 8 條→ch20 總結表、ch11 Burke→ch16、ch02 bounds→ch17、ch04 競賽引理→ch07）／A4 無 scope 違規／A5 骨架 21/21 皆 PASS；唯一硬不一致 A6＝QNA 首次出現章（附錄 B 標 ch18＝定義處、附錄 C 標 ch14＝首次點名）已統一為 ch18。事實抽查 17 項全 CONFIRMED（Little/Burke/Kingman 三篇/Schrage Letter/Reiser–Lavenberg/BCMP 四作者/Jackson/Wolff PASTA/Pollaczek 1930/Tail at Scale/metastable HotOS+OSDI/po2c Mitzenmacher+Vvedenskaya/simpy 4.1.2/ciw 3.2.7），零 WRONG；兩個 landscape ⚠️（Khinchine 1932 卷期、Erlang 1924 年份）確認書中皆已正確 hedge（ch12 只給年份語言、ch09 寫「可上溯至 Erlang 的年代」不帶年份）。P5：reader（id=queue）建妥、books.json 登記、bookshelf 重建（16 書）、headless Chrome 渲染抽查（ch07/ch16 路線圖、ch06 框圖、ch16 網路 feedback 框）框線對齊無塌陷。
