# 全書大綱（內部文件，非書籍內容）

書名（工作名）：《等待的數學：排隊理論》
形態：21 章、六個 Part、4 個附錄。數學嚴謹為主的興趣書；紙上推演為主＋指定章節 Python 小實驗。
每章必須遵守 `style-guide.md` 的骨架與深度標準；歷史歸屬與時效性事實以 `landscape-2026-06.md` 為錨。

## 全書敘事弧

從「你知道 80% 使用率是警戒線，但說不出為什麼」出發 → 不用機率就能算的鐵律（Little's Law、bottleneck bounds）先給一批工具 → 要解釋「為什麼會排隊」就需要機率，把生鏽的磨利（C² 登場）→ 指數分布與 Poisson 過程是這個世界的原子 → Markov chain 給出「系統＝狀態＋轉移」的引擎 → 生滅過程把引擎接上佇列，M/M/1 誕生、hockey stick 定理化 → 多伺服器與池化的威力（Erlang 公式）→ 有限容量把 backpressure 定理化 → 可逆性與 Burke 定理打開網路之門 → 放掉指數假設：變異數的帳單（P-K）、排程的選擇與守恆、Kingman 的萬用近似、重尾把平均值的信用徹底毀掉 → 網路層級：Jackson 的驚奇、封閉系統與 MVA、product form 的邊界 → 公式到頭了，模擬接手——但模擬會騙人，方法學是門手藝 → 帶著全部工具回機房，重審 retry storm、autoscaling、batching → 地圖與下一步。

前一章的問題是後一章的動機：直覺失效（ch01）→ 不靠機率能走多遠（ch02）→ 機率工具（ch03–05）→ 狀態的數學（ch06–07）→ 第一個完整模型（ch08）→ 更多伺服器、更少容量（ch09–10）→ 為網路鋪路（ch11）→ 指數假設不真實怎麼辦（ch12–15）→ 多站系統（ch16–18）→ 公式失效怎麼辦（ch19）→ 回到系統（ch20–21）。

## 全書路線圖（基準圖；Part 首章照抄並標「◄ 你在這裡」）

```
 Part I    地圖與定律      ch01–02   直覺為什麼失效、不用機率的鐵律
     │
     ▼
 Part II   機率地基        ch03–06   工具箱、指數、Poisson、Markov chain
     │
     ▼
 Part III  生滅與經典模型  ch07–11   CTMC、M/M/1、Erlang、有限容量、Burke
     │
     ▼
 Part IV   超越指數        ch12–15   M/G/1、排程、Kingman、重尾
     │
     ▼
 Part V    佇列網路        ch16–18   Jackson、封閉與 MVA、product form 邊界
     │
     ▼
 Part VI   模擬與回到系統  ch19–21   模擬方法學、機房應用、地圖與下一步
```

## 跨章基準（一致性掃描的依據；各章不得另創數字與命名）

**貫穿範例「推播管線」**（源自讀者真實經歷：WebSocket 通知系統、~10M 訊息/月）：API 收到事件 → 推播 worker 發送。

| 元素 | 基準 | 首次出現 |
|---|---|---|
| 單 worker 基準 | E[S] = 100 ms（μ = 10 則/s）、尖峰 λ = 8 則/s、ρ = 0.8 | ch01（體感）/ch08（推導） |
| M/M/1 基準結果 | πₙ = 0.2·0.8ⁿ；E[N] = 4、E[T] = 0.5 s、E[N_Q] = 3.2、E[T_Q] = 0.4 s；T ~ Exp(μ−λ = 2)、t₉₉ = ln 100/2 ≈ 2.30 s（P99 ≈ 4.6× 平均） | ch08 |
| 使用率階梯 | E[T] = E[S]/(1−ρ)：ρ=0.5→0.2 s、0.8→0.5 s、0.9→1.0 s、0.95→2.0 s、0.99→10 s | ch01（曲線）/ch08（推導） |
| M/M/c 基準 | c = 4、λ = 32/s、μ = 10/s、a = 3.2、ρ = 0.8；Erlang-C ≈ 0.596、E[T_Q] ≈ 74.6 ms、E[T] ≈ 175 ms（**初算參考**，寫章必須獨立重算複核） | ch09 |
| 池化三連比 | 同總流量 λ = 32：4 台獨立 M/M/1（各 λ=8）E[T] = 0.5 s vs 共用佇列 M/M/4 ≈ 0.175 s vs 單台快機（μ=40）M/M/1 = 0.125 s（**初算參考**） | ch09 |
| 有限容量基準 | M/M/1/K：K = 10；兩組到達 λ = 8（正常）與 λ = 12（過載）、μ = 10 | ch10 |
| 串聯基準 | tandem 兩站：λ = 6、μ₁ = 10、μ₂ = 8 | ch11 |
| M/G/1 基準 | λ = 8/s、E[S] = 100 ms、ρ = 0.8；C²ₛ ∈ {0, 1, 10} → E[T_Q] = 0.2(1+C²ₛ) s：D→0.2 s、M→0.4 s、C²ₛ=10→2.2 s | ch12 |
| 排程基準 | 兩類工作：短（90%、E[S]=50 ms）、長（10%、E[S]=550 ms）——混合 E[S] = 100 ms、λ = 8、ρ = 0.8 不變 | ch13 |
| Kingman 基準 | M/G/1 基準加 C²ₐ = 2、C²ₛ = 1：E[T_Q] ≈ 4·0.1·(2+1)/2 = 0.6 s | ch14 |
| 重尾基準 | Pareto α = 1.5、E[S] 校準到 100 ms（變異數無限）；需要上界時用 Bounded Pareto，上界由寫章 agent 設定並複核 | ch15 |
| Jackson 基準 | 外部 λ₀ = 6/s → node1（API，μ₁=10）→ node2（推播，μ₂=8）→ 離開；node2 以 p = 0.2 把失敗送回 node1 重試。解：λ₁ = λ₂ = 7.5、ρ₁ = 0.75、ρ₂ = 0.9375、E[N] = 3+15 = 18、E[T] = 18/6 = 3.0 s。對照組 p = 0.3 → λ₁ = 8.571…、ρ₂ > 1 不穩定 | ch16 |
| 封閉網路基準 | 2 站互動式：E[S₁] = 100 ms、E[S₂] = 200 ms、think time Z = 1 s、N = 1…5 的 MVA 全表（值由寫章 agent 推導複核） | ch02（bounds）/ch17（MVA） |
| 模擬 ground truth | M/M/1 基準（E[N] = 4、E[T] = 0.5 s）作為 ch19 全部方法學示範的校準標的 | ch19 |
| 數字常數 | e ≈ 2.71828、ln 2 ≈ 0.6931、ln 100 ≈ 4.6052；數值預設 3 位有效數字 | 全書 |

**記號**：依 style-guide「數學記號規範」（E[T]/E[N] 系統，不用 L/W）。

**Python 小實驗章**：ch05、ch08、ch12、ch15、ch17、ch19、ch20（其餘章不放程式）。

**全域不涵蓋**（任何章都不展開，最多一句話＋指向延伸閱讀）：matrix-analytic 方法（PH 分布、QBD）、fluid/diffusion 極限的嚴格理論、mean-field 深論（power-of-two-choices 在 ch21 給半頁敘述）、排隊控制與 MDP、strategic queueing（賽局）、network calculus、模擬工具 API 教學、LLM serving 機制細節（指向書架上的《從後端到 AI Infra》）。

---

## Part I — 地圖與定律（ch01–02）

### ch01 — 排隊無所不在：直覺失效的地方
- **目標**：說出「ρ 接近 1 時延遲爆炸不是 bug 是數學」；畫出全書地圖；建立「隨機性本身是延遲來源」的問題意識。
- **必涵蓋**：開場場景：推播管線尖峰延遲飆升（基準數字體感版，不推導）；確定性世界 vs 隨機世界——λ<μ 為什麼還會排隊（D/D/1 不排隊的對照）；使用率階梯表（先給數字，ch08 推導兌現）；P99 vs 平均的預告；排隊理論能回答／不能回答的問題清單；Kendall 記號一瞥（地圖語言，正式定義 ch08）；全書路線圖（基準圖首次出場）；**「經驗法則的審判」清單**——全書要定理化或推翻的工程黑話（80% 警戒線、「加機器就好」、「P99 看 tail 就夠」、「retry 是免費的保險」……ch20 結案）。
- **不涵蓋**：任何推導；機率定義（ch03）。
- **橋接**：RDS CPU 80% 警戒線、k6 壓測曲線的形狀、SQS backlog 的尖峰記憶。
- **Worked example**：D/D/1 vs 叢發到達的手排時間線——同樣 λ=8、μ=10：等距到達零等待；把其中 4 個 job 擠成一團，手算每個 job 的等待時間，看等待從哪裡生出來。
- **紙上推演**：手排另一條叢發時間線；給三個系統判斷排隊理論的哪一塊管它；「為什麼 ρ<1 還會排隊」口頭重講。

### ch02 — 操作分析：不用機率的鐵律
- **目標**：能用 operational laws 從可量測量推出不可直接量測量；能做 bottleneck 分析給出吞吐上界與拐點；理解 Little's Law 的威力與精確適用條件。
- **必涵蓋**：operational analysis 世界觀（一切從可量測量出發、無分布假設）；Utilization Law；**Little's Law**：直覺論證（面積雙算圖）＋工程師嚴謹版證明（有限觀察窗）＋嚴格版指路（Stidham 1974，本書不證）＋適用條件（穩定、長期平均、與分布／排程／網路結構無關——這個「無關」是它可怕的地方）；E[N] = λE[T] 應用三連發（整個系統、只看佇列、只看伺服器——E[N_服務中] = ρ 的妙用）；Response Time Law（互動式系統、think time Z）；Forced Flow Law、visit ratio、service demand Dᵢ；bottleneck 分析與 asymptotic bounds（X ≤ 1/D_max、E[T] ≥ ΣDᵢ、拐點 N* = (ΣDᵢ+Z)/D_max）；與教科書 L/W 記號的一次性對照。
- **不涵蓋**：機率模型（ch03 起）；MVA（ch17，bounds 是它的伏筆）。
- **橋接**：「concurrent ≈ RPS × latency」這條他在容量規劃用過的公式就是 Little；k6 的 VU 是封閉系統（一句話，ch17 兌現）。
- **Worked example**：推播管線量測數據（觀察窗 60 s、完成 480 則、busy 48 s……）推出全套指標；封閉基準配置（D₁=0.1 s、D₂=0.2 s、Z=1 s）算 X ≤ 5/s 與 N* = 6.5 的 bounds 全程。
- **紙上推演**：從殘缺監控數據算出缺的指標；「升級哪台收益最大」bottleneck 決策題；找出一個 Little's Law 誤用（非穩態窗口、邊界不一致）。

## Part II — 機率地基（ch03–06）

### ch03 — 機率工具箱：把生鏽的磨利
- **目標**：把機率磨利到能跟上全書推導；建立 C²（變異係數平方）這個全書主角；幾何級數成為肌肉記憶。
- **必涵蓋**：機率空間與事件（快速）；條件機率、全機率定理（佇列推導的主力工具）；隨機變數、CDF/pdf/pmf、tail P(X>t)；期望值、LOTUS、indicator 技巧、期望值線性（不需獨立——強調）；變異數；**C² = Var/E² 正式定義**與直覺刻度（C²=0 確定性、C²=1 指數、C²>1 叢發）；常用分布速覽（Bernoulli、geometric、binomial、uniform；Pareto 留 ch15）；幾何級數 Σρⁿ = 1/(1−ρ) 與微分技巧 Σnρⁿ（推 E[N] 的引擎）；E[X] = ∫₀^∞ P(X>t) dt（tail 積分求期望，全書常用）；Markov 與 Chebyshev 不等式（tail 的第一課：平均值對 P99 承諾多少）。
- **不涵蓋**：指數分布深論（ch04）；CLT（一句話，ch19 的 CI 回收）；測度論。
- **橋接**：P99 就是 tail 的 quantile；「平均 100 ms」對 SLA 承諾了什麼——用 Markov 不等式算給看（很少）。
- **Worked example**：geometric 期望兩路算法（tail 積分 vs 級數微分）對帳；C² 計算三連發（確定性／指數／二點叢發分布）。
- **紙上推演**：條件期望分解；indicator 求期望；給一張（虛構）監控直方圖估 C²ₛ 並判斷「比指數更叢發嗎」。

### ch04 — 指數分布：排隊世界的原子
- **目標**：把無記憶性從「定義」變成「化簡推導的武器」；競賽引理熟練到反射。
- **必涵蓋**：指數分布基本量（E[S]=1/μ、C²=1）；**無記憶性**：定義、證明、為什麼是連續分布中唯一（工程師嚴謹版）；殘餘壽命在指數下＝原分布（inspection paradox 預告，一般版 ch12）；hazard rate 視角（IFR/DFR、「等越久越快來」是哪種分布的性質）；**競賽引理**：min(X₁,…,Xₖ) ~ Exp(Σλᵢ)、P(Xᵢ 最先) = λᵢ/Σλⱼ、且勝者身分與競賽時長獨立（最反直覺的一條，CTMC 的引擎，完整證明）；指數假設的誠實檢討：到達間隔常像（ch05 解釋為什麼）、服務時間常不像（ch12/15 處理）。
- **不涵蓋**：Poisson 過程（ch05）；一般分布殘餘壽命（ch12）。
- **橋接**：timeout 該不該因「已經等很久」而調整——無記憶性的回答；exponential backoff 與指數分布無關（命名玩笑一句話釐清）。
- **Worked example**：兩台 worker 都在忙（各 μ=10），你排第一：E[到你開始服務] = 1/20、E[你的總逗留] 完整推；並列「直覺會怎麼算錯」。
- **紙上推演**：無記憶性證明重講；競賽引理應用 2 題；「等越久越容易來」論證找破綻。

### ch05 — Poisson 過程：到達的標準模型【Python 實驗章】
- **目標**：三個等價定義能互推（敘述層級）；疊加／分流／條件均勻性熟練；知道為什麼大量獨立稀疏來源疊加趨向 Poisson、什麼時候不是。
- **必涵蓋**：計數過程；Poisson 過程三定義（指數間隔、獨立平穩增量＋Poisson 分布、微小區間 o(h) 刻畫）與等價性（證一個方向，其餘指路）；疊加（superposition）與分流（thinning）含證明 sketch；條件均勻性（given N(t)=n，到達時刻分布如均勻順序統計量）；Palm–Khintchine 直覺：為什麼大量獨立用戶的匯流近似 Poisson、什麼時候破（行為相關、重試迴圈、批次上游）；非齊次 Poisson（λ(t)、尖峰時段）一段。
- **不涵蓋**：PASTA（ch08）；renewal theory 全論。
- **橋接**：~10M 訊息/月的到達流長什麼樣；thinning＝按機率路由到 shard；superposition＝多個上游匯流。
- **Worked example**：λ=8/s：P(某 1 秒 ≥ 12 則) 手算（pmf 累加）；p=0.3 分流到 iOS 推播的子流參數與獨立性聲明。
- **Python 小實驗**：`random.expovariate` 疊出 Poisson 過程，驗證 N(1) 的均值≈變異數≈λ；兩條獨立流疊加後間隔的 C² ≈ 1。
- **紙上推演**：定義互推一題；條件均勻性應用；判斷三條真實到達流（人發訊息、cron 觸發、retry 流）哪些近似 Poisson、為什麼。

### ch06 — Markov chain：狀態吃掉歷史
- **目標**：能對小 chain 手解平穩分布；說清楚平穩分布存在唯一收斂的條件與直覺；建立 balance equation＝流量守恆的讀法。
- **必涵蓋**：Markov 性質＝「狀態吃掉歷史」（建模的真功夫在選狀態）；轉移矩陣、Chapman–Kolmogorov；狀態分類（不可約、週期、recurrent/transient——每個病態配一個工程例子）；平穩分布 π = πP 與解法（**明寫：實務上就是代入消去解線性方程組＋正規化，不需要矩陣代數或特徵值**——安撫生鏽的讀者）；有限不可約非週期 chain：存在、唯一、收斂（工程師嚴謹：敘述＋耦合直覺，完整證明指路）；balance equations 當「機率流量守恆」讀（cut 的觀念，生滅的伏筆）；ergodic 定理：時間平均＝期望（模擬的理論執照，ch19 回收）。
- **不涵蓋**：CTMC（ch07）；MCMC；HMM。
- **橋接**：circuit breaker 三狀態（closed/open/half-open）就是 Markov chain；TLA+ 書手畫過的狀態轉移圖（可引用不依賴）。
- **Worked example**：circuit breaker 三狀態 chain（給定轉移機率）手解 π，回答「長期有多少比例時間處於斷路」、調參數看 π 怎麼動。
- **紙上推演**：解平穩分布 2 題；判斷三個 chain 哪個沒有唯一平穩分布、為什麼；週期性陷阱題（振盪不收斂但 π 存在）。

## Part III — 生滅與經典模型（ch07–11）

### ch07 — CTMC 與生滅過程：把引擎接上時間
- **目標**：能從指數競賽組裝 CTMC；能對任意生滅過程寫 balance equations 並解出 πₙ；掌握 ergodicity 判準。
- **必涵蓋**：CTMC＝每個狀態停留指數時間＋按競賽引理跳轉（ch04 兌現）；rate diagram 為主、generator/Q 矩陣輕量帶過；global balance；**生滅過程**：定義、local balance＝相鄰 cut 的流量守恆（為什麼生滅鏈 global 與 local 一致——一維結構）；通解 πₙ = π₀·Π(λᵢ/μᵢ₊₁) 完整推導；ergodicity 條件（正規化級數收斂）與發散的物理意義；transient 行為的誠實聲明（本書主攻穩態，動態指 ch21 的 fluid 地圖）。
- **不涵蓋**：M/M/1 全套（ch08）；可逆性（ch11）；uniformization。
- **橋接**：rate diagram＝你畫過的狀態機加上速率標籤；autoscaling 的 scale-up/down 就是生與滅。
- **Worked example**：生滅通解完整推導；套用到 λₙ 隨 n 遞減的小例（admission control 的生滅模型）算 πₙ。
- **紙上推演**：寫 balance equations 並解 2 題；判斷三個生滅過程哪個 ergodic；「local balance 為什麼在生滅成立」口頭重講。

### ch08 — M/M/1：第一個完整的佇列【Python 實驗章；全書招牌章】
- **目標**：完整推導 M/M/1 全套結果且能重講每一步；hockey stick 定理化（兌現 ch01）；PASTA 從黑話變成定理。
- **必涵蓋**：M/M/1＝生滅特例；πₙ = (1−ρ)ρⁿ 推導；E[N]（幾何級數微分，ch03 兌現）；用 Little 推 E[T]、E[T_Q]、E[N_Q]（基準表全套）；**回應時間完整分布** T ~ Exp(μ−λ)（敘述＋證明 sketch）→ t₉₉ = ln 100/(μ−λ)、「M/M/1 的 P99 ≈ 4.6× 平均」；使用率階梯推導（ch01 兌現）；**PASTA**：敘述、為什麼不平凡（給一個到達看到的≠時間平均的反例：等距到達）、證明思路、指出本章哪幾步偷偷用了它；Kendall 記號正式定義；穩態的精確意義、ρ ≥ 1 時發生什麼。
- **不涵蓋**：多 server（ch09）；非指數服務（ch12）。
- **橋接**：推播管線基準數字全面兌現；「80% 警戒線」開庭——E[N]=4 可不可接受是 SLA 的事，但 0.8→0.9 延遲翻倍是定理。
- **Worked example**：基準表全套推導＋數值；ρ = 0.8 → 0.9 前後對照表（E[N]、E[T]、t₉₉）。
- **Python 小實驗**：事件驅動 M/M/1 模擬（heapq，≤40 行）驗證 E[N]≈4、E[T]≈0.5 s、P99≈2.30 s（給落點區間）。**本書 DES 骨架在此首次登場**（event list＋模擬時鐘的最小實作，講清楚迴圈在做什麼；統計方法學——warmup、CI、batch means——留 ch19）。
- **紙上推演**：πₙ 推導重講；P(N ≥ 20) 手算；「流量翻倍、機器也翻倍，延遲會怎樣」（為 ch09 池化鋪路的陷阱題）。

### ch09 — M/M/c 與 Erlang 公式：池化的威力
- **目標**：能推 M/M/c 平穩分布與 Erlang-C；能用 Erlang-B 遞迴手算；說清楚池化為什麼贏、贏多少、極限在哪。
- **必涵蓋**：M/M/c 生滅建模（μₙ = min(n,c)·μ）；平穩分布、**Erlang-C**（延遲機率）推導、E[T_Q] = ErlangC/(cμ−λ)；損失系統（loss system）概念在此先引入一段（「沒位子就走、不排隊」；完整的有限容量理論見 ch10）；M/M/c/c 與 **Erlang-B**、手算友善的遞迴式、Erlang 在哥本哈根電話交換的歷史（照 landscape）；M/M/∞ 一段；**池化三連比**（基準表：4 台獨立 vs 共用佇列 M/M/4 vs 單台快機——初算參考必須重算）與「一台快機 vs 多台慢機」的裁決（含單台快機輸的場景：故障域、搶占）；square-root staffing／QED regime：√a 緩衝為什麼夠（直覺推導，Halfin–Whitt 指路）；Erlang-B 對服務分布 insensitive 一句話預告（ch13/18 兌現）。
- **不涵蓋**：非指數服務（ch12）；abandonment（ch10）。
- **橋接**：worker pool sizing、autoscaling 目標值、3,200 條並發連線該配幾個 worker 的舊問題。
- **Worked example**：Erlang-B 遞迴手算 B(c=1…4, a=3.2) 全程 → 換算 Erlang-C ≈ 0.596 → E[T_Q] ≈ 74.6 ms；池化三連比完整數值表。
- **紙上推演**：遞迴算另一組 (c, a)；staffing 題（要 P(wait) < 0.2 至少幾台）；「拆 pool 一定變差嗎」（M/M/c 下對；埋 ch13/ch15 短工作隔離的種子）。

### ch10 — 有限容量與不耐煩：backpressure 的定理
- **目標**：能推 M/M/1/K 並解讀 blocking probability；理解丟棄／等待／逾時的本質權衡；把 bounded queue、load shedding、timeout 定理化。
- **必涵蓋**：M/M/1/K 平穩分布（有限幾何和，ρ 可以 > 1！與 ch08 對照）、blocking probability π_K、有效到達率 λ_eff = λ(1−π_K)、goodput；PASTA 在 blocking 的正確用法；throughput–latency–loss 三角（你只能選邊）；M/M/c/K 概觀；不耐煩：balking、reneging、M/M/1+M（Erlang-A）概觀（敘述層級）——timeout 的數學身分；有限母體 M/M/1//N（repairman model）一段：到達率隨在場人數下降改變一切（ch17 封閉系統伏筆）；**rate limiting 的佇列論身分**：token bucket（容忍叢發的 admission control）與 leaky bucket（流量整形＝把下游看到的 C²ₐ 壓低）一段（敘述＋小計算，ch14 的 C²ₐ 槓桿伏筆）。
- **不涵蓋**：封閉網路全論（ch17）；priority（ch13）；網路中的 blocking（ch18 一句話）。
- **橋接**：SQS visibility timeout 與 DLQ、bounded channel、nginx `max_conns`、load shedding 的數學身分；「buffer 開大一點」的審判。
- **Worked example**：K=10：λ=8（正常）與 λ=12（過載）兩組手算 π_K、λ_eff、E[T]——過載系統靠丟棄活著、而且活得有模有樣。
- **紙上推演**：推 M/M/1/K 平穩分布；「加大 buffer 能救過載嗎」計算題（不能——只是把延遲變長、丟棄變晚）；reneging 對 tail 的定性分析。

### ch11 — 可逆性與 Burke 定理：網路的鑰匙
- **目標**：理解時間反轉與可逆性；能重講 Burke 定理的證明思路與它反直覺的部分；知道這把鑰匙開了哪扇門。
- **必涵蓋**：時間反轉與反轉鏈；可逆性 ⇔ detailed balance（含怎麼猜 π 再驗證的實用技巧）；生滅過程皆可逆（證明）；**Burke 定理**：M/M/1（與 M/M/c）穩態輸出是 Poisson(λ)、且時刻 t 的狀態與 t 之前的輸出歷史獨立——這句的反直覺正面處理（「剛吐出一串 job 不代表現在比較空」）；串聯佇列：聯合分布乘積形式（基準：λ=6、μ₁=10、μ₂=8）；Burke 的極限：有 feedback 時內部流不再 Poisson（ch16 的驚奇鋪墊）。
- **不涵蓋**：Jackson 全論（ch16）；quasi-reversibility（一句話指路）。
- **橋接**：microservice 鏈「上游輸出＝下游輸入」；「對每段各自容量規劃」什麼時候合法。
- **Worked example**：tandem 基準手算：兩站各自 M/M/1、聯合 π(n₁,n₂) 乘積、E[N] 與總 E[T]。
- **紙上推演**：detailed balance 驗證；用反轉鏈引導式論證 Burke；找出「輸出獨立性」的一個直覺誤用。

## Part IV — 超越指數（ch12–15）

### ch12 — M/G/1 與 Pollaczek–Khinchine：變異數的帳單【Python 實驗章】
- **目標**：能推 P-K 平均等待公式（tagged-customer＋時間平均面積論證路線；**不使用 renewal 理論術語**，殘餘壽命用圖形面積論證講——本書沒教 renewal theory，不得假裝教過）；inspection paradox 內化；「變異數本身是延遲來源」定理化。
- **必涵蓋**：為什麼 M/G/1 不再是 CTMC（佇列長度不夠當狀態）、embedded chain 一句話、本書走 mean-value 路線；**殘餘服務時間與 inspection paradox**（一般版，ch04 兌現）：E[殘餘] = E[S²]/2E[S]、「你總是撞上長工作」的數學；**P-K 公式完整推導**：E[T_Q] = λE[S²]/(2(1−ρ)) ＝ (ρ/(1−ρ))·E[S]·(1+C²ₛ)/2；基準三連比（C²ₛ = 0/1/10 → 0.2/0.4/2.2 s）；M/D/1 等待是 M/M/1 一半的金句；transform（LST）方法的存在聲明與用途（等待分布、本書不推，指路）；busy period 概念一段。
- **不涵蓋**：排程（ch13）；G/G/1（ch14）；重尾深論（ch15）。
- **橋接**：「一支 30 秒的報表 query 拖垮整條 API」的肇事機制現在有名字了；批次大小不齊的 consumer。
- **Worked example**：基準三連比全推；inspection paradox 數值演示（90% 短／10% 長的混合，撞上的平均 vs 真平均）。
- **Python 小實驗**：M/G/1 模擬三種服務分布（deterministic／exponential／兩點 C²ₛ=10）驗證 0.2/0.4/2.2 s。
- **紙上推演**：P-K 推導重講；E[S²] 計算 2 題；「均值不變、變異數砍半，等待改善幾 %」。

### ch13 — 排程：誰先服務的代價與正義
- **目標**：能比較主要 discipline 的 E[T] 與公平性；理解 work conservation 守恆律（總量不變、分配可選）；說出 SRPT 為什麼最優、代價是什麼。
- **必涵蓋**：work conservation；**Kleinrock 守恆律**：M/G/1 非搶占且不看工作長度的 discipline（FCFS/LCFS/RANDOM）E[T_Q] 全相同——多數人第一次聽都不信，完整講；但變異數與 tail 大不同（FCFS tail 最緊的那一面）；PS：time-sharing 的理想化、E[T] 只依賴 E[S]（**insensitivity**，敘述＋指路）、slowdown 視角；SJF 與 **SRPT**：改善機制、最優性（敘述＋交換論證 sketch，完整證明指路 Schrage 1968）；「SRPT 餓死長工作？」的真相（在 M/G/1 下長工作通常也沒變差的反直覺結果，敘述層級＋條件）；M/G/1 priority：non-preemptive 公式推導、preemptive 給結果；cμ rule 一句話。
- **不涵蓋**：多 server 排程深論；公平性理論全論；LLM serving 排程（ch20 點綴）。
- **橋接**：**Node.js 單執行緒 event loop 下多請求交錯執行 ≈ PS 的工程化身**（誠實討論哪裡像、哪裡不像——run-to-completion 的 tick 粒度）；OS scheduler、「VIP 通道」的代價、K8s PriorityClass。
- **Worked example**：排程基準（短 90%/50 ms、長 10%/550 ms、λ=8）：FCFS vs 短優先 non-preemptive priority vs SJF 的 E[T] 對照表（各類與總體）。
- **紙上推演**：守恆律驗證題；priority 公式應用；「長工作開專用 pool vs 用 SRPT」決策分析（ch09 種子兌現）。

### ch14 — G/G/1 與 Kingman：工程師的萬用近似
- **目標**：能寫 Lindley recursion 並手追；能用 Kingman/VUT 公式做 back-of-envelope 並知道誤差來源；建立「V × U × T」的世界觀。
- **必涵蓋**：G/G/1 沒有解析解的誠實聲明；**Lindley recursion** W_{n+1} = max(0, W_n + S_n − A_{n+1})（手追、它就是 ch19 模擬的核心迴圈）；heavy-traffic 直覺：ρ→1 時等待趨向指數、只有前兩階矩 matter（為什麼——直覺論證，嚴格版指路）；**Kingman 近似** E[T_Q] ≈ (ρ/(1−ρ))·((C²ₐ+C²ₛ)/2)·E[S]，讀成 **VUT 公式**（Variability × Utilization × Time）——當全書工程總綱；上界版推導（工程師嚴謹）；基準數值（0.6 s）；準確度誠實帳：低 ρ、重尾、相關到達時誤差大（各給方向）；G/G/c 的 Allen–Cunneen 式擴展一段；到達相關性警告：C²ₐ 抓不到叢發的時間相關（一句話指路 MMPP/QNA）。
- **不涵蓋**：嚴格 heavy-traffic 定理；重尾（ch15）；網路分解（ch18）。
- **橋接**：容量規劃 back-of-envelope 神器；為什麼壓測要用真實 trace 重放而不是固定速率（C²ₐ 被做假）。
- **Worked example**：基準 Kingman 0.6 s 全算；「同樣的錢：把 C² 砍半 vs 把 ρ 降 0.05」收益對照（V 槓桿 vs U 槓桿）。
- **紙上推演**：Lindley 手追 6 個 job；Kingman 應用 2 題；「固定間隔到達的壓測低估等待多少」計算題。

### ch15 — 重尾：平均值會說謊【Python 實驗章】
- **目標**：理解重尾分布的數學性質如何粉碎輕尾直覺；知道哪些前面的結果在重尾下失效或變形；給 tail latency 工程一個理論地基。
- **必涵蓋**：Pareto 定義、α 與矩的存在性（α≤2 變異數無限、α≤1 連均值都沒有）；重尾三衝擊：①樣本均值不收斂的體感②inspection paradox 極端化（撞上的工作比平均長很多倍——量化）③「最大的一個吃掉總和」現象；真實世界證據（檔案大小、flow size——照 landscape，不得憑記憶引用）；M/G/1 在重尾下：E[S²] 爆炸 → P-K 爆炸 → FCFS 等待重尾化；排程的救贖：PS/SRPT 在重尾下壓倒性勝出（ch13 回收，敘述層級＋指路）；Bounded Pareto 的誠實（實務都有上界，但上界很大時行為像無界）；P99 與 mean 脫鉤：輕尾「P99≈4.6×平均」（ch08）在重尾下死掉。
- **不涵蓋**：極值理論；subexponential 嚴格理論；Tail at Scale 工程術（ch20）。
- **橋接**：「一支 query 連環撞死 DB」；長 GC pause；為什麼 P99.9 預算這麼難立。
- **Worked example**：Pareto α=1.5、E[S]=100 ms：P(S > 1 s) 對同均值指數的倍數差手算；10 個樣本含一個巨值的 running mean 漂移表。
- **Python 小實驗**：Pareto vs exponential 的 running mean 收斂對照；同均值下 max/sum 占比演示。
- **紙上推演**：矩存在性判斷；重尾 inspection paradox 計算；「拿 4.6× 規則推重尾 P99」會錯多誇張。

## Part V — 佇列網路（ch16–18）

### ch16 — Jackson 網路：乘積形式的驚奇
- **目標**：能解 traffic equations、寫出 product form、算網路級指標；能說出 Jackson 定理哪裡驚奇（feedback 下內部流非 Poisson、定理卻仍成立）。
- **必涵蓋**：開放網路、routing matrix、外部到達；**traffic equations**（流量守恆，解的存在唯一）；**Jackson 定理**：敘述、π(n₁,…,n_k) = Π πᵢ(nᵢ)、「彷彿各站獨立 M/M/1（參數 λᵢ）」的精確含義；證明路線：2 站案例驗 global balance（工程師嚴謹）、一般形指路；**驚奇正面處理**：有 feedback 時內部流不是 Poisson（Burke 失效，ch11 兌現）但乘積形式仍真——「獨立性是穩態快照的性質，不是過程的性質」；基準範例 retry feedback 全解（基準表）：p=0.2 把 ρ₂ 推到 0.9375、E[T]=3.0 s 的工程寓言；p=0.3 → ρ₂>1 系統爆炸（retry 多 10% 從穩態到不穩）；瓶頸識別與 Little on λ₀。
- **不涵蓋**：封閉網路（ch17）；BCMP／多 class（ch18）；retry storm 動態（ch20）。
- **橋接**：microservice 呼叫圖；「每個服務各自看起來健康、整體卻雪崩」的初階機制。
- **Worked example**：基準 Jackson 全解（traffic equations → ρᵢ → E[Nᵢ] → E[T]=3.0 s）；p_retry 0.2→0.3 重解看爆炸。
- **紙上推演**：另一組 routing 解 traffic equations；2 站 global balance 驗證乘積形式；「加一台 node2 vs 把 retry 率砍半」決策計算。

### ch17 — 封閉網路與 MVA：固定母體的世界【Python 實驗章】
- **目標**：理解封閉網路為什麼難（normalization constant）、MVA 怎麼繞開；能手算小型 MVA 表；理解 closed-loop 對壓測量測的含義。
- **必涵蓋**：封閉網路動機（固定 worker 池、connection pool、壓測 VU）；Gordon–Newell 乘積形式與 normalization constant G 的計算痛點（為什麼不能直接套 Jackson）；**arrival theorem**（封閉版 PASTA：到達者看到的是 N−1 母體的穩態）——MVA 的引擎；**MVA 遞迴**推導與手算（基準配置 N=1…5 全表：E[Tᵢ]、X、E[Nᵢ]）；與 ch02 asymptotic bounds 對帳（漸近線兌現、拐點 N*=6.5 的意義）；closed vs open 行為差異：封閉系統自我節流、永遠不會像開放系統那樣爆炸——所以固定 VU 的壓測天生看不到真實過載（ch19 coordinated omission 的親戚）。
- **不涵蓋**：多 class MVA（一句話）；BCMP（ch18）；近似 MVA（指路）。
- **橋接**：k6 VU 模型 vs 開放流量；DB connection pool sizing 的理論性格。
- **Worked example**：基準封閉配置 MVA 手算全表 N=1…5，對照 ch02 bounds 與拐點。
- **Python 小實驗**：MVA 遞迴 ~20 行驗證手算表；輸出 X(N) 飽和曲線（文字表格即可）。
- **紙上推演**：MVA 多推一步到 N=6；「VU 加倍≠流量加倍」解釋題；用 arrival theorem 重講遞迴每一項的來歷。

### ch18 — 網路的邊界：product form 之外
- **目標**：知道 product form 的精確邊界（BCMP 條件，敘述層級）；知道哪些常見工程特徵會打破它、打破之後的選項光譜。
- **必涵蓋**：**BCMP 定理概觀**：四種 station 類型、哪些 discipline／服務分布組合保 product form（敘述＋論文指路）；insensitivity 兌現（PS、IS、LCFS-PR 對服務分布不敏感——ch09/ch13 伏筆收攏）；**打破 product form 的工程現實**：priority、有限 buffer／blocking 網路、**fork-join——本章主角段落**（「最常見卻最難」：Promise.all／scatter-gather 的數學身分；精確解只有特例、bounds 與近似指路；E[max] 與 tail 劣化完整展開；緩解手段 hedged/tied requests 指向 ch20）、批次、同步、重試相關性；分解近似思路（每站當獨立 G/G/1、一階二階參數傳播——QNA 概觀）；「公式 → 近似 → 模擬」決策框架（接 ch19）。
- **不涵蓋**：BCMP 證明；QNA 公式全推；Petri net。
- **橋接**：fork-join＝他每天寫的 Promise.all；「scatter-gather 的 P99 由最慢分片決定」。
- **Worked example**：fork-join 扇出 n 路（各 Exp(μ)）：E[max] = H_n/μ 手推（n=2: 1.5/μ），對照單路——扇出的 tail 代價隨 H_n 成長；n=10 時 P99 劣化估算。
- **紙上推演**：判斷四個網路有沒有 product form；fork-join 劣化估算題；給一個系統選「公式／近似／模擬」並說理由。

## Part VI — 模擬與回到系統（ch19–21）

### ch19 — 模擬方法學：讓蒙地卡羅說真話【Python 實驗章；本章主體即實驗】
- **目標**：能寫一個誠實的事件驅動模擬（DES）；知道模擬騙人的四大途徑（transient 污染、輸出自相關、種子紀律、稀有事件）與對策；輸出永遠帶區間。
- **必涵蓋**：DES 機制正式化（ch08 首次登場的 event list＋模擬時鐘骨架，這裡補齊一般化細節）；Lindley recursion 當 G/G/1 模擬捷徑（ch14 兌現）；種子與可重現性紀律；**warmup／transient 污染**（從空系統起跑的偏差、Welch 法概觀）；**輸出自相關**：等待時間序列高度相關 → 樸素 CI 嚴重過窄（本章招牌陷阱，數字演示）→ batch means 與獨立 replications；CI 計算（CLT 在此回收）；稀有事件的代價：估 P99.99 要多少樣本——直接算；**驗證紀律**：先對 M/M/1 ground truth（基準表）校準、再去模擬沒有公式的東西；**coordinated omission**：固定 VU 壓測在系統變慢時自動少送請求 → tail 被系統性低估（Gil Tene；ch17 closed-loop 兌現）；simpy/ciw 存在聲明一句話。
- **不涵蓋**：工具 API；variance reduction 深論（common random numbers 一段、其餘指路）；平行模擬。
- **橋接**：他寫過的壓測腳本與「跑三次取平均」的民間統計學開庭。
- **Worked example**：同一個 M/M/1 模擬的三種處理（不丟 warmup／樸素 CI／batch means）結果對照表——方法學差異 > 隨機誤差。
- **Python 小實驗**：完整 M/M/1 DES（≤40 行）＋batch means 對 ground truth 收斂；換 Pareto 服務看收斂慢多少（ch15 兌現）。
- **紙上推演**：「這份模擬報告哪裡不可信」找碴題（內含 3 個方法學錯誤）；P99.99 樣本數計算；batch size 取捨口頭重講。

### ch20 — 把理論帶回機房：retry、autoscaling、batching【Python 實驗章】
- **目標**：用全書工具重審讀者的真實系統；ch01「經驗法則審判」清單逐條結案；retry storm 與 metastable failure 的佇列論機制說得出來。
- **必涵蓋**：**容量規劃完整 walkthrough**：推播管線從量測（λ、E[S]、C²ₐ、C²ₛ）→ 模型選擇（決策框架）→ staffing（Erlang-C／square-root）→ SLA 驗證（P99）——全書工具一次串起來；**retry storm 深論**：retry＝feedback（ch16 兌現）＋timeout 把有效服務時間膨脹 → 同一個 λ 存在「健康／崩潰」兩個自洽狀態（**metastable failures**，照 landscape 引用；小模型手算）；防禦的數學身分：exponential backoff（降 feedback 增益）、jitter（去相關、降 C²ₐ）、circuit breaker（強制離開壞平衡，ch06 兌現）、admission control（M/M/1/K，ch10 兌現）；autoscaling 的佇列論：指標選擇（ρ vs E[N] vs E[T_Q]）、滯後與震盪、square-root staffing 重訪（ch09）；**tail latency 工程**：Tail at Scale 的 hedged/tied requests 用 fork-join（ch18）與重尾（ch15）框架解讀（照 landscape 引用）；**batching 權衡**：等湊批 vs 立即發——throughput–latency frontier 小模型；LLM serving continuous batching 一段點綴（深度指向《從後端到 AI Infra》）；「經驗法則的審判」總結表（ch01 清單結案）。
- **不涵蓋**：LLM serving 機制細節（主書）；K8s HPA 操作；具體雲服務調參。
- **橋接**：整章素材直接用讀者的系統，無需另設橋接段以外的錨點。
- **Worked example**：retry 雙穩態小模型手算：給定 timeout 與 retry 規則，解出兩個自洽工作點、算「多大的擾動會從好平衡掉進壞平衡」。
- **Python 小實驗**：retry feedback 模擬：λ 緩升再緩降，觀察遲滯（上山的路與下山的路不同——metastability 體感）。
- **紙上推演**：用模板對自己現職系統做一次容量 walkthrough；重建審判表中三條的論證；「backoff 上限怎麼選」計算題。

### ch21 — 地圖與下一步
- **目標**：全書地圖收官、六條驗收主線兌現；知道沒講的世界長什麼樣、什麼問題會逼你去學；帶走後續路徑。
- **必涵蓋**：全書路線圖回收（每格標已走過、各 Part 一句話總結）；六條驗收主線逐條口頭自答總測（style-guide「驗收標準」）；**沒講的世界**各一段（定位＋什麼問題逼你去學）：matrix-analytic／PH 分布（「比指數真實、比 G 可解」的中間地帶）、fluid／diffusion 近似（過載動態與尖峰）、mean-field 與 **power-of-two-choices**（值得半頁：隨機派工 vs 問兩台選短的，尾部指數級改善——敘述＋landscape 引用）、排隊控制／MDP、strategic queueing、network calculus（worst-case 路線）；書單與路徑（照 landscape：Harchol-Balter 主推、Adan–Resing 免費、Kleinrock 經典）；「如果只帶走三個公式」：Little、VUT（Kingman/P-K 一家）、Erlang-C；下一步：把 ch20 walkthrough 套到現職系統、列出「下一個要量的數」。
- **不涵蓋**：新主題展開。
- **橋接**：回到 ch01 開場的尖峰延遲事故——現在的你會怎麼分析它。
- **Worked example**：power-of-two-choices 數值對照（random vs po2c 的佇列長度尾部；用 landscape 驗證的數字，否則標敘述層級）。
- **紙上推演**：六主線口頭自答；給三個虛構問題選工具並說理由；寫自己系統的量測清單。

## 附錄（在全部章節完成後編譯，從實際寫出的內容萃取）

### 附錄 A — 記號速查表
全書記號總表：符號、讀法、定義、首次出現章；與教科書 L/W 記號的對照表。從各章實際用過的記號 grep 彙整，不得收錄書中沒出現的。

### 附錄 B — 公式總表
本書招牌附錄。每行：模型／定律、公式、**精確適用條件**（哪些假設、哪個最常破）、首次出現章。「適用條件」欄是靈魂——沒有條件的公式表是危險品。只收書中推導過或正式敘述過的公式。

### 附錄 C — 術語表
EN–ZH–一句話定義–首次出現章。從實際內容萃取。

### 附錄 D — 延伸閱讀總地圖
彙整各章延伸閱讀＋landscape 驗證過的資源，按 Part 組織；給「如果只讀三樣」與「想更嚴格時的下一本」建議。只收 landscape 或各章已驗證的連結。

## 檔名規範

`chNN-slug.md`：
ch01-why-queueing、ch02-operational-laws、ch03-probability-toolbox、ch04-exponential、ch05-poisson-process、ch06-markov-chains、ch07-ctmc-birth-death、ch08-mm1、ch09-mmc-erlang、ch10-finite-capacity、ch11-reversibility-burke、ch12-mg1、ch13-scheduling、ch14-gg1-kingman、ch15-heavy-tails、ch16-jackson-networks、ch17-closed-networks-mva、ch18-network-limits、ch19-simulation、ch20-back-to-systems、ch21-map-and-next。
附錄：`appendix-a-notation.md`、`appendix-b-formulas.md`、`appendix-c-glossary.md`、`appendix-d-reading-map.md`。
