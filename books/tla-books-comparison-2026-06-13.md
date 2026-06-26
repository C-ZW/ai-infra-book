<!--
產生方式：Claude Code 多代理人工作流（Workflow tool, ultracode）。
- Phase 1（Sonnet ×44）：tlaplus 21 檔＋tla-theory 23 檔逐章獨立客觀評估（不跨書比較，避免錨定偏誤）。
- Phase 2（Opus ×8）：八面向跨書評審，每位實際讀≥兩書各 2 章、要求證據導向。
- Phase 3（Opus ×8）：八個載重章節獨立數學驗證（對抗式重算）；總計 98 correct / 3 imprecise / 1 incorrect / 2 unverifiable。
- Phase 4（Opus ×1）：綜合計分與報告。
- 客觀指標（字數/圖數/對齊/簡體 lint）由 main loop 以 check_diagrams.py 與字元統計實測。
- 公平性：所有 agent 被指示只評內容、忽略「哪個 model 寫的」之後設資訊（tla-theory 為 Opus 產出，與評審同模型，已明確防偏）。
- main loop 抽查確認：tla-theory ch07「Req×2」單步、tlaplus ch13 Timeout guard 矛盾兩處 line-level 指控屬實。
共 61 個 agent、約 3.35M subagent tokens。
-->

# TLA+／形式化方法雙書比較報告：《把系統寫成定理》vs《正確性的數學》

> 產生日期：2026-06-13　·　**本報告由多代理人工作流產生**（量化指標、逐章評估、八面向跨書評審、獨立數學驗證四套材料綜合）

---

## TL;DR

**勝者：tlaplus《把系統寫成定理》。信心 8/10。**

一句話理由：兩本都是高水準的理論派 TLA+ 書，但 tlaplus 在「可練性（附完整解答＋難度標示）、敘事弧、深度交叉驗算、主題廣度」四個對自學者收益最大的維度明顯領先，且最硬的客觀證據——獨立數學驗證——對 tlaplus 載重章節**零 incorrect**，而 tla-theory 有兩處錯落在它正在教的核心語義概念上。

八面向 tlaplus **全勝或打平**（七勝一平，無一面向落後）。差距集中在「紙上演練」（9 對 6.5）與「深度與 worked example」（9 對 7.5）兩項；「故障模式視角」打成 9 對 9。

---

## 一、兩本書定位與規格對照

| 項目 | tlaplus《把系統寫成定理》 | tla-theory《正確性的數學》 |
|---|---|---|
| 定位 | 理論派＋協議精讀＋業界案例（廣覆蓋） | 純理論派、深專題（窄而深） |
| 章數＋附錄 | 18 章＋3 附錄 | 20 章＋3 附錄 |
| 脊椎範例 | 單一：SQS 結算 pipeline（v0→v1 演化） | 雙脊椎：Lock（互斥）＋Msg（冪等消費者） |
| 協議精讀 | 有：Peterson / 2PC / Paxos / Raft（4 章） | 無 |
| 業界案例 | 有：AWS / MongoDB / Cosmos DB / CockroachDB＋ROI | 無 |
| 純理論專章 | refinement / 機器證明壓在 Part V 三章 | refinement 三章（含 history/prophecy/assume-guarantee）、fairness 專章、模組化/INSTANCE、PlusCal translation |
| 共同骨架契約 | 從你已知的出發→核心機制→故障模式→紙上演練（附解答）→自我檢核→延伸閱讀；每章帶數字 worked example | 同左 |
| 目標讀者 | 同一位 6+ 年資深後端工程師（SQS／idempotent／分散式交易／DB lock 為肌肉記憶，TLA+ 近乎從零） | 同左 |

---

## 二、客觀量化指標（材料一，main loop 實測）

| 指標 | tlaplus | tla-theory |
|---|---|---|
| 章數 | 18 | 20 |
| 內容檔數（章＋附錄） | 21 | 23 |
| 中文字數（CJK） | 144,575 | 91,622 |
| 每檔平均字數 | 6,885 | 3,984 |
| ASCII 圖數 | 22 | 50 |
| 圖對齊可疑數（check_diagrams） | 0 | 0 |
| 簡體詞命中（lint） | 0 | 0 |

解讀：tlaplus 圖較少但每章更厚（≈1.7 倍字數）；tla-theory 圖多、架構圖先行密度高但每章較短。兩本 check_diagrams 皆 exit 0、簡體 lint 皆 0——**基礎工程品質兩本都過關**（lint 的 0 是工具層；逐章人工審另發現少數簡體/不一致，見第四節）。

---

## 三、八面向計分卡

| 面向 | tlaplus | tla-theory | Winner |
|---|---|---|---|
| 1. 教學設計與橋接 | 9 | 8 | tlaplus |
| 2. 數學與邏輯正確性／嚴謹 | 8.7 | 8 | tlaplus |
| 3. 文筆與繁中台灣用語 | 8.7 | 8.3 | tlaplus |
| 4. 深度與 worked example | 9 | 7.5 | tlaplus |
| 5. 結構、敘事弧與跨章一致性 | 9 | 8 | tlaplus |
| 6. 紙上演練與自我檢核 | 9 | 6.5 | tlaplus |
| 7. 主題涵蓋廣度與取捨 | 8.5 | 8 | tlaplus |
| 8. 故障模式視角（陷阱與防禦） | 9 | 9 | tlaplus（微弱） |
| **總分（8 項合計）** | **70.9** | **63.3** | **tlaplus** |
| **平均** | **8.86** | **7.91** | **tlaplus** |

---

## 四、各面向評析

### 1. 教學設計與橋接（9 vs 8，tlaplus）
兩本的橋接都屬高水準、都錨在後端肌肉記憶、都避免空洞類比，差距是程度而非有無。tlaplus 的「具體濃度」更高：反覆點名讀者真實系統的特定失效模式（ch06 把 SQS receive/delete 兩步間的 race 引出 Fetch/Settle 拆分；ch07 用「on-call 兩種事故長相」與「queue depth 連續 30 分鐘 > 0 的告警逼近無限未來」釘住 safety/liveness；K8s 拉起 pod = SF）。tla-theory 的橋接也極漂亮（ch06 reducer→before-after predicate＋「JS spread 自動沿用 vs TLA+ 預設放任」是全書系最強的單一觀念轉換），但更常停在資料結構／語言層的對照，對 SQS／分散式實戰的對位密度稍低。tlaplus 另以單一脊椎貫穿全書，概念遞進有連續工程脈絡。

### 2. 數學與邏輯正確性／嚴謹（8.7 vs 8，tlaplus）
兩本層級證明、□/◇/⇝ 語義、[A]_v 允許 stutter、歸納不變量、CTI 強化、vacuous truth 都處理到位，且都明文以「每步可口頭說理、禁止顯然」為基準。tlaplus 在兩維度略勝：**深度**（ch14 TwoPhase 的 8×8=64 份義務完整矩陣＋條款審計＋假證明清算，是入門/中階書罕見的承重級嚴謹；tla-theory 最深證明是 ch19 對任意 n 的 Lock 互斥，乾淨但規模小一截、活性只到骨架）；**核心語義不出錯**（tla-theory 有兩處錯落在它正在教的概念正中心，詳見第六節）。

### 3. 文筆與繁中台灣用語（8.7 vs 8.3，tlaplus）
兩書都寫出流暢道地的繁中台灣文，英文術語都原樣保留並與中文順接。次面向互有勝負：**無簡體詞硬標準**——tla-theory 較乾淨（全書僅 1 處裸「算法」、「非同步」零漏寫）；tlaplus 有 3 處（2 次裸「算法」＋1 次「異步」）且內部不一致。**清晰不冗＋文采**——tlaplus 意象更鮮明、金句密度更高（ch12「□[Next]_vars 是允許清單，不是待辦清單」「p2 被迫成為 x 的傳聲筒」）。四項子標準中 tlaplus 取三、tla-theory 取一（無簡體），故 tlaplus 微幅領先。

### 4. 深度與 worked example（9 vs 7.5，tlaplus）
兩本每章都有帶具體數字的 worked example、都無灌水，tla-theory 守紀律值得肯定。差距在「深度厚度與交叉驗算密度」：tlaplus 在同一例子上反覆加壓（ch09 的 41 狀態用三條獨立路徑對帳＋第三度 BFS 進度複核＋推 state explosion 通式算到 1.25×10⁸＋逐字讀真 TLC trace＋Burnside 數對稱軌道；ch08 把白板題推到狀態空間＋最短性＋唯一性；ch16 逐行精讀真實 .tla 證明檔）。tla-theory 同類 example 紮實（ch18 Lock 8 狀態三步對帳、ch11 CTI 強化、ch19 任意 n 歸納），但規模與交叉驗算層數普遍少一檔，較少「同一例子多路複核」與「真實 trace/證明檔精讀」。

### 5. 結構、敘事弧與跨章一致性（9 vs 8，tlaplus）
**跨章一致性（防漂移）**：tla-theory 機制略勝——把 Lock/Msg 抽到單一 running-examples 真相源、15/20 章逐字複製，比 tlaplus 的命名自律更工程化（兩者實測都無狀態數漂移：41 與 8/20/48 都跨章對得上）。**敘事弧**：tlaplus 明顯更強——18/18 章皆有「本章解決什麼問題」開場塊（tla-theory 為 0/20，改用 Part 標籤＋地圖塊），全書貫穿「欠債→還債/伏筆→兌現」裝置 50 處，v0→v1 是真正會推進回收的故事線；協議精讀（2PC→Paxos→Raft）形成複雜度搬家的次敘事弧並在 ch15 收口。敘事弧是本面向主軸，故 tlaplus 勝。

### 6. 紙上演練與自我檢核（9 vs 6.5，tlaplus）——差距最大
三個可檢項：**(1) 解答完整度＋常見錯路**：tlaplus 每題附與正文同級的完整層級證明＋主動補常見錯路與反向自測（ch05 題1 方向反推坑、ch10 題3 親手改壞 Peterson 再推反例）；tla-theory 系統性以「成功標準」取代完整解答，缺可逐字對帳的參照證明，且個別成功標準本身邏輯有瑕。**(2) 難度/時間標示**：tlaplus 全書標 ★/★★/★★★＋分鐘數；tla-theory 全書零標示。**(3) 自我檢核深度**：兩本打平（tla-theory ch19 達 10 題、問法精準）。tlaplus 拿下最核心的兩項，且這兩項恰是「能不能照著練到手藝」的決定性指標。信心高（結構性、全書一致，不依賴抽樣）。

### 7. 主題涵蓋廣度與取捨（8.5 vs 8，tlaplus）
兩本取捨都內部自洽，方向不同。tlaplus 走廣覆蓋：理論主題（歸納不變量、refinement 含 history/prophecy 與 Abadi-Lamport 完備性、機器證明）是 tla-theory 的 superset，再加四個協議精讀與業界案例（ch17 含 AWS Table 1、ROI 框架）。tla-theory 走深專題：refinement 三章、fairness 專章、PlusCal-as-sugar、**assume-guarantee**（對寫微服務契約的本人其實更對口，是 tlaplus 被低估的覆蓋缺口）。本面向核心字眼是「廣度」，tlaplus 在維持理論深度下多覆蓋兩個高價值維度且為真材實料，略勝。

### 8. 故障模式視角（9 vs 9，tlaplus 微弱）
兩本都極強、都真正兌現「症狀→為什麼→怎麼在紙上抓」且可動手（找 witness、造 CTI、手畫餓死 behavior、刪 fairness 子句做切割練習）。tla-theory 的 fairness 故障模式（ch10「WF 空洞滿足→p1 餓死」）判準甚至更銳利。tlaplus 以「脊椎一致性＋跨章兌現＋陷阱類型覆蓋廣度」微弱勝出——vacuous truth 三次跨章現身（ch03→ch07→ch14），並因有協議精讀與證明高峰而觸及高階陷阱（inductive 卻無用、歸納步偷用可達性、64 格漏格）。winner 對讀者實際收益影響有限。

---

## 五、量化體型補充
- tlaplus：144,575 字／每檔 6,885 字／22 圖——厚章、文字承載深度。
- tla-theory：91,622 字／每檔 3,984 字／50 圖——薄章、架構圖先行密度高。

tla-theory 較短多為「精煉」而非灌水（對 lasso 用無界系統的張力、TLAPS liveness 支援有限都主動揭露，是誠實加分）；但在「深度厚度」這個面向核心指標上確實薄一層。

---

## 六、數學正確性專節（材料四：八項獨立數學驗證的最硬證據）

**tlaplus**（驗了 ch05、ch08、ch09、ch14 共數十條載重論斷）：**全部 correct，零 incorrect、零 imprecise。** 含規模無關性（額外驗 3×2、3×3 配置）、41 狀態三路對帳、64 格封閉矩陣、DieHard 16 狀態＋最短性＋唯一性、可達通式算到 1.25×10⁸ 等。唯一「unverifiable」者皆為跨章引用的 TLC 計數（如 ch09 的 v0 對照數、ch14 的 72/五萬），屬無法在本章內重算，非錯誤。可信度極高。

**tla-theory**（驗了 ch08、ch11、ch18、ch19）：ch11、ch18 **全部 correct**（ch18 的 Lock 8/20/48、型別上界 27、N(n)=2^(n-1)(n+2)、Msg K=2 為 5 個含 ⟨0,否⟩ 不可達等全部重算成立，可信度極高；ch11 的 MutEx「看似對但不歸納→強化→重證」全弧線成立）。ch08、ch19 各有瑕疵，逐條列出如下：

### Incorrect（真錯，須修）
1. **tla-theory · ch08 · 症狀一第 1 點**：宣稱「□Next 連 behavior 都湊不出來……Lock 從 Init 出發頂多走有限步就到無事可做的狀態（如 s3）」。**錯在**：此 Lock 無任何可達死狀態（lock=p⇒pc[p]=crit 為不變式，任一非全閒置狀態必有 action enabled；s3 全 idle 仍可 Request——文中括號自己也承認）。故「□Next 連 behavior 都湊不出來」對 Lock 為假，存在無窮 □Next behavior。**正確值**：□Next 之所以錯，是它排除了「從起點永遠 stutter」這條 behavior（對任何 spec 都成立、不需死狀態），而非「系統會卡死」。本章選錯了 illustration 機制（正解應同演練 3）。

### Imprecise（措辭/歸因不精確，結論不變，宜修）
2. **tla-theory · ch08 · 症狀二**：把「漏下標 □[Next] 被 SANY 擋下」歸為「level-checking（見 ch18）」。**不精確**：缺下標屬語法/文法層錯誤，level-checking 是檢查 prime/temporal 階層的另一語意階段，兩者是 SANY 前端不同 phase。被擋是真的，phase 名稱張冠李戴。
3. **tla-theory · ch11 · MutEx 反例隱含前提**：CTI 用相異 p、q 隱含需 |Proc|≥2，敘述未明說。**本章 Proc={p1,p2} 已滿足，不影響結論**，屬次要隱含前提。
4. **tla-theory · ch19 · Release 那步歸因**：（行182）寫「由歸納假設 (C2)…沒有別的 q 在 crit」，但「無其他 q 在 crit」實際靠 (C1)＋lock 單值性導出，(C2) 只刻畫 pc[lock]=crit。歸因略不精確，**結論與整體歸納步成立**。
5. **tla-theory · ch19 · lasso 存在性**：鴿籠直覺方向正確但略簡化（嚴格存在性需與性質自動機取積後在接受循環上論證），作為教學直覺與存在性論斷皆成立。

### 額外（不在四項硬驗證內，但逐章評估與我抽讀核實的實質錯誤）
- **tla-theory · ch07（line 163，已核實）**：壞 behavior 表把 s0→s1 標為「Req×2」（兩 process 在單一步同時 idle→wait），TLA+ 交錯語義下非法，書卻只把 s3 標「非法步」、把 s0→s1 當合法放行——**這是在教「合法 behavior 步」的章節裡把概念本身教錯**，比措辭瑕疵更傷。正確做法：拆成兩步 Wait，或改用從 crit 直接造一步非法 Acquire 的更短反例。
- **tla-theory · ch18**：BFS 回邊標籤錯——s4-Rel(p1) 應回 s0（非 s1）、s5-Rel(p2) 應回 s0（非 s2）。總狀態數 8 正確，但讀者手畫時對不上。
- **tla-theory · ch19**：MLive「lasso」建在無界 Msg 系統（inflight[m2] 單調遞增永不重複），不構成 lasso，與該章鴿籠定義自相矛盾。
- **tla-theory · ch13 / ch14**：兩處「成功標準」邏輯有瑕會引讀者到錯路（ch13 演練3「inflight≥1 永遠成立」忽略 Process 後降至 0；ch14 演練1 五步 trace 末態兩 process 在 grab 而非 crit）。
- **tla-theory · ch16**：Abadi-Lamport 卷號標 TCS 81(2)，疑為 82(2)（1991），待核 DOI。

對照 **tlaplus** 的實質錯誤（皆非四項硬驗證章節，由逐章評估標出）：
- **ch13（嚴 7，技術事實錯）**：題2 解答「Timeout 沒有前置條件」與同章 spec 的 Timeout guard（state[i]∈{Follower,Candidate}）直接矛盾——Leader 須先 Restart/UpdateTerm 降位。**這是真技術錯，須修。**
- **ch08（已核實）**：line151 散文「(3,5) 四個非自環動作的落點 (0,5)、(3,0)」與 line194 封閉表（顯示 (3,5) 只有兩個非自環落點）矛盾，應為「兩個」。
- **ch01**：第2題提款建模歧義＋直接引用 counter 論證未重推（跳步）。
- **散體簡體/不一致**：ch02/ch09 兩處裸「算法」、ch18「異步」。

**結論**：兩本各有實質錯誤，但**性質不同**。tlaplus 的錯多為散文/表格不一致或單章技術滑，底層形式物件仍正確；tla-theory 的兩處核心錯（ch07 Req×2、ch19 lasso）落在它正在教的語義概念正中心，**在「教這個概念的章節裡把概念本身教錯」更傷**。這是本報告判 tlaplus 在「數學正確性」面向勝出的關鍵硬證據。

---

## 七、兩本書各自優缺點

### tlaplus《把系統寫成定理》
**優點**
- 單一演化脊椎（SQS v0→v1）貫穿全書，敘事弧與「欠債/還債」張力最強。
- 深度厚、交叉驗算密度高；獨立數學驗證對載重章節零 incorrect。
- 紙上演練體例最完整（難度星級＋時間＋完整解答＋常見錯路）。
- 協議精讀梯度（Peterson→2PC→Paxos→Raft）＋業界 ROI，覆蓋面是 tla-theory superset。
- 文采與金句密度高。

**缺點**
- ch13 Timeout guard 技術事實錯（須修）。
- ch08 散文「四個非自環」與封閉表矛盾、ch01 第2題建模歧義跳步。
- 3 處簡體/不一致（算法×2、異步×1）。
- 收尾章 ch18 深度偏淺、AI 數字與部落格 URL 可查驗性弱。

### tla-theory《正確性的數學》
**優點**
- 無簡體詞硬標準更乾淨、內部一致性高。
- 防漂移機制更工程化（單一 running-examples 真相源、逐字複製）。
- 純理論專題深化（refinement 三章、fairness 專章、PlusCal-as-sugar）；assume-guarantee 對寫微服務契約者更對口。
- 故障模式段落格式最工整、fairness 判準銳利。
- 自我檢核題量大、問法精準。

**缺點**
- ch07 Req×2、ch19 無界 lasso 兩處核心語義概念出錯（最傷）。
- 練習普遍只給「成功標準」無完整解答、全書零難度/時間標示。
- 個別成功標準邏輯有瑕（ch13/ch14）；ch18 回邊標籤錯。
- 主題廣度較窄（無協議精讀/業界案例）、深度較薄。

---

## 八、最終建議（給作者／讀者本人）

**以 tlaplus 為主線。** 它八面向全勝或打平，且在自學者收益最大的四維度（可練性、敘事弧、深度交叉驗算、主題廣度）明顯領先，載重章節數學零 incorrect。

**出版前 tlaplus 必修：**
1. ch13 題2 解答「Timeout 沒有前置條件」→ 改為「Leader 須先 Restart/UpdateTerm 降位才能 Timeout」（與 spec guard 一致）。
2. ch08 line151「(3,5) 四個非自環動作」→ 改「兩個非自環動作」（與 line194 封閉表一致）。
3. ch01 第2題提款：把 3 步模型明寫成 r:=balance / check / balance:=r-80 並重推 18/20（勿直接套 counter 論證）。
4. ch02/ch09 裸「算法」→「演算法」；ch18「異步」→「非同步」。

**從 tla-theory 移植三項長處到 tlaplus：**
1. 把 running example 抽到單一「真相源檔」治理（防漂移比命名自律更可靠，可在 _meta 建一致性基準表強制逐字複製）。
2. 新增一節 assume-guarantee／開放系統契約（E⇒M、E⊳M、循環依賴 induction-over-time）——對寫微服務契約的本人高度對口，補上 tlaplus 的覆蓋缺口。
3. 借鏡 tla-theory ch10 fairness 故障模式的三段式判準（「有沒有別的 action 能把它的 guard 從真變假」）強化 tlaplus ch07。

**若保留 tla-theory 作姊妹篇，必修：** ch07 Req×2（改兩步 Wait 或更短反例）、ch19 無界 lasso（改在加界 inflight≤K 有限系統演示或明標「概念示意」）、ch18 回邊標籤（Rel 回 s0）、ch13/ch14 兩處有瑕成功標準；並全面補上練習完整書寫解答與難度/時間標示，否則自學者缺對帳錨點。

---

*評審紀律聲明：本報告只評內容本身，忽略任何「哪個 model 寫的」之後設資訊；所有判斷以四套客觀材料＋對 ch07.md line163、ch08-complete-specs.md line151/194 的原文抽查為依據。*
