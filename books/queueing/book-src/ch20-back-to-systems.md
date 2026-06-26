# ch20 — 把理論帶回機房：retry、autoscaling、batching

> **本章解決什麼問題**：前面十九章把工具一件件鍛出來——Little、生滅引擎、Erlang、P-K、Kingman/VUT、Jackson、fork-join、模擬方法學。本章是收網：用整套工具重審你機房裡每天發生的四件事——容量規劃怎麼從量測一路走到 SLA、retry 為什麼會讓同一個 λ 長出「健康」與「崩潰」兩個自洽狀態（metastable failure）、autoscaling 該盯哪個指標、batching 與 tail 工程的數學。最後把 ch01 立的「經驗法則審判」清單八條逐條宣判。這不是新理論，是讓你看見舊理論一直在你的 production 裡運行——只是以前沒有名字。ch21 接著畫全書地圖、指出沒講的世界。

## 從你已知的出發

你的整個職業生涯都在跟本書的主角打交道，只是當時沒有把它們叫做佇列模型。SQS 的 backlog 尖峰是 ch01 的局部超載；RDS CPU 的 80% 警戒線是 ch08 的 hockey stick；exponential backoff 與 DLQ 是 ch10 的 admission control 加洩壓；k6 的 VU 是 ch17 的封閉網路；你做過的 retry 限流是 ch16 的 feedback 整定。本章把這些零件接回它們所屬的定理，然後問一個你大概在值班室裡親身經歷過、但沒能用數學講清楚的問題：

**為什麼一次短暫的尖峰，可以把一個本來健康的系統永久鎖死，連尖峰過去了、流量回到正常都救不回來，非得重啟不可？**

「重啟才好」這四個字背後不是玄學，是一個有名字的數學現象——metastable failure，本章的主菜。在那之前，先把容量規劃的整條工具鏈跑一次，因為 retry storm 的崩潰平衡，恰恰是這條工具鏈裡每個量被 feedback 推到失控的結果。

## 容量規劃 walkthrough：從量測到 SLA 的一條龍

本書散落各章的工具，第一次串成一條完整的決策流程。主角還是推播管線（API 收事件 → worker 推送）。流程五步，每步都標清楚「用哪一章、最容易在哪裡翻車」。

**第一步：量測四個數。** 你真正握在手上的從來不是「Poisson 到達、指數服務」的證書，是監控系統裡的四個數字（ch14 的世界觀）：

| 量 | 怎麼量 | 推播管線值 | 章 |
|---|---|---|---|
| λ（到達率） | busy hour 的 RPS，不是全日平均 | 8 則/s（尖峰） | ch05 |
| E[S]（平均服務時間） | 完成時間的平均 | 100 ms（μ = 10） | ch08 |
| C²ₐ（到達變異） | 到達數的 Var/Mean 比，且要掃視窗大小 | 2（cron 與 retry 匯流推高） | ch03/ch14 |
| C²ₛ（服務變異） | 服務時間直方圖的 Var/E² | 先假設 1，量到再修 | ch03/ch12 |

第一個坑就在這裡：**用全日平均 λ 算 staffing，尖峰必塌**（ch09 陷阱表）。λ(t) 非平穩，要拿最忙時段當輸入。第二個坑是 C²ₐ 要掃視窗——它隨統計桶變大而上升，就是到達有時間相關（叢發）的指紋（ch14），這時你量到的數是樂觀的下限。

**第二步：選模型（決策框架）。** 不是每個系統都配 M/M/1。判準（綜合 ch08/ch09/ch12/ch14/ch19）：

```text
單一 worker？ ──是──► C²ₐ ≈ 1 且 C²ₛ ≈ 1 ? ──是──► M/M/1（ch08）精確
   │ 否                      │ 否
   ▼                         ▼
 c 台共用佇列？           C²ₐ ≈ 1、C²ₛ 任意 ? ──是──► M/G/1 / P-K（ch12）精確
   │ 是                      │ 否
   ▼                         ▼
 Erlang-C（ch09）         兩者都 ≠ 1 ──► Kingman/VUT（ch14）近似，標誤差
   │
   ▼
 有 fork-join / 重尾服務 / retry 相關性 ? ──是──► 公式只給方向，數字靠模擬（ch18/ch19）
```

推播管線是單一 worker、C²ₐ = 2 ≠ 1，落在 **Kingman/VUT** 格。一句誠實話：VUT 是羅盤與比較器，不是精算器（ch14）；要對外承諾數字，最後一步得用模擬兜底。

**第三步：算等待（VUT）。** 套 ch14 的招牌公式（讀法：等待 = 變異性 × 使用率 × 時間）：

```text
E[T_Q] ≈ (C²ₐ + C²ₛ)/2 · ρ/(1−ρ) · E[S]      ← Kingman/VUT（ch14）
       = (2 + 1)/2 · 0.8/0.2 · 0.1 s
       = 1.5 × 4 × 0.1 s = 0.6 s              ← V=1.5、U=4、T=0.1 s
E[T]   = E[T_Q] + E[S] = 0.6 + 0.1 = 0.7 s
```

注意這個 0.7 s 比 ch08 純 M/M/1 的 0.5 s 大了 40%——多出來的全是 C²ₐ = 2 那部分到達叢發的帳。**如果你拿 M/M/1 的 0.5 s 去簽 SLA，你低估的不是雜訊，是一整根變異槓桿。**

**第四步：staffing（要幾台 / 要多快）。** 假設 SLA 要求把尖峰 E[T] 壓回 0.3 s。兩條路：加機器（池化，ch09）或降變異（ch14）。先看池化——把單 worker 換成 c 台共用佇列的 M/M/c，總流量 λ = 8 不動，每台 μ = 10。用 ch09 的 √a 直覺（square-root staffing）打底：offered load a = λ/μ = 0.8，緩衝該按 √a ≈ 0.89 級開，而不是按 a 的固定比例。c = a + β√a 的最小整數解這裡 c = 2 就讓 ρ = 0.4、把等待壓垮。但若到達是 C²ₐ = 2 的叢發，Erlang-C 會樂觀——它假設 Poisson 到達——所以實務上要用 ch14 的 G/G/c 擴展（Erlang-C 值乘上 (C²ₐ+C²ₛ)/2）再驗。**這一步最容易記反的是 ch09 陷阱表那條：hash 分流不是 M/M/c，是 c 個獨立 M/M/1，同硬體 E[T] 差 2.9 倍。** 先看路由：consumer 主動領 ≈ 共用佇列；sticky 推送 ≈ 獨立佇列。

**第五步：驗 SLA 的 P99，不只平均。** 平均達標不代表尾巴達標（ch01 審判 #3）。輕尾世界 ch08 給你 M/M/1 的 P99 ≈ 4.6× 平均；但這個倍數是指數分布專屬的（ch15），C²ₛ 一大或服務重尾，P99 與平均脫鉤、4.6× 規則死。所以第五步的紀律是：**P99 一律實測或模擬，不從平均外推**（ch15/ch19）。容量規劃到這裡才算閉環——量測進、SLA 出，中間每一步都知道自己用了哪個假設、哪個假設最可能破。

這條工具鏈是 ch21「把 walkthrough 套到現職系統」的模板，紙上推演第 1 題請你親手跑一次。

## retry storm 深論：一個 λ，兩個自洽狀態

現在進主菜。前面的 walkthrough 有一個藏起來的前提：λ 是外生的、你說了算。retry 把這個前提炸掉——retry 讓系統的負載依賴它自己的延遲，於是 λ 變成內生的，而內生的迴圈會長出多個平衡。

### retry = feedback + 服務時間膨脹

ch16 已經把第一半講完了：retry 是 feedback。外部到達 λ₀ 進來，一部分失敗的請求被送回到達端重試，站內看到的有效到達率 λ_eff > λ₀，放大係數 1/(1−p) 是幾何級數和（ch16 的 p = 0.25 懸崖）。ch16 的 p 是外生常數；本章讓它內生——**p 會隨負載漂移**，這正是 ch16 結尾留給本章的那句話。

第二半是 ch16 沒講的：retry 還會**膨脹有效服務時間**。一個請求發出去、等到 timeout（比方 0.6 s）才放棄重發，這 0.6 s 裡伺服器可能已經在處理它、做了一半的白工（ch10 的 reneging：無效服務推高實際負載）。更糟的是 ch10 講過的 goodput 崩潰：當 E[T] 超過客戶端 timeout，每一件完工都沒人收貨——**throughput 不動，goodput 歸零，伺服器全力以赴地做白工**。retry storm 的崩潰態就是這個態：機器 100% 忙、產出 100% 沒用。

把兩半合起來：負載↑ → 延遲↑ → timeout 增多 → retry 增多 → 負載更↑。這是一個自我增強迴圈。自我增強迴圈的特徵是——它可以有不只一個自洽的歇腳點。

### 雙穩態小模型（手算）

嚴謹度標示：**工程師的嚴謹**。這是一個刻意設計成手算得動的 mean-field 模型，它的理想化我先全部攤開，最後一節再清算：(i) 用穩態平均值描述一個本質上是動態的過程（mean-field，忽略漲落）；(ii) retry 產生的額外負載設成跟使用率 ρ 成正比的簡單形式；(iii) 每個請求最多重試一輪。它不是定理，是一張**地圖**，用來看清「兩個平衡」這件事的骨架。

設單一伺服器 μ = 10 則/s，外部到達 λ₀（固定）。令 ρ = λ_eff/μ 是有效使用率，g = λ₀/μ 是「裸」offered load。retry 的回饋假設成：系統越忙、timeout 越多、回饋的額外負載越大，最簡單的形式是額外負載 ∝ ρ。寫成 λ_eff 的自洽方程：

```text
λ_eff = λ₀ + b·λ_eff·ρ          ← b 是 retry 增益（feedback gain）
兩邊除以 μ，用 ρ = λ_eff/μ、g = λ₀/μ：
ρ = g + b·ρ²                    ← 自洽（fixed-point）方程
整理成標準二次式：
b·ρ² − ρ + g = 0
解：ρ = (1 − √(1 − 4bg)) / (2b)   ← 下根，好平衡（健康）
   ρ = (1 + √(1 − 4bg)) / (2b)   ← 上根，臨界點（壞平衡的邊界）
```

代數結構就是雙穩態的全部祕密：**一個二次式有兩個根**。取 b = 2/3、g = 0.36（即 λ₀ = 3.6 則/s，μ = 10）：

```text
判別式 1 − 4bg = 1 − 4·(2/3)·0.36 = 1 − 0.96 = 0.04，√ = 0.2
ρ_good = (1 − 0.2)/(4/3) = 0.8/(4/3) = 0.600      ← 健康平衡
ρ_tip  = (1 + 0.2)/(4/3) = 1.2/(4/3) = 0.900      ← 臨界（不穩定）平衡
```

**自我複核（代回原式）。** 好平衡：b·ρ² − ρ + g = (2/3)(0.36) − 0.6 + 0.36 = 0.24 − 0.6 + 0.36 = 0 ✓。臨界平衡：(2/3)(0.81) − 0.9 + 0.36 = 0.54 − 0.9 + 0.36 = 0 ✓。兩個自洽工作點都對。

在 ρ_good = 0.6，系統像個正常的 M/M/1：λ_eff = 6 則/s，E[T] = 1/(μ−λ_eff) = 1/4 = 0.25 s。健康、可服務。那 ρ_tip = 0.9 是什麼？它是一道**山脊**，不是一個你會停留的地方——它把世界切成兩個盆地。低於山脊，系統滑回 ρ_good；高於山脊，迴圈失控往上跑。

### 為什麼山脊以上會崩潰

把自洽方程當成一個迭代來讀（每一輪：新負載 = 外部 + 回饋）。在 ρ_tip = 0.9 以上，回饋 b·ρ² 產生的負載超過它自己消化的速度，下一輪 ρ 更大、再下一輪更大——一路衝破 ρ = 1。一旦 ρ ≥ 1，ch08 的鐵律生效：佇列無上界成長，E[T] → ∞，timeout 全中，retry 全發，系統焊死在崩潰態。

```text
ρ_{n+1} = g + b·ρ_n²，起點 ρ = 0.92（剛過山脊）：
  0.920 → 0.924 → 0.930 → 0.936 → 0.944 → 0.954 → 0.967 → 0.983 → 1.005 → 發散
```

這就是 metastable failure 的數學骨架，照 landscape 的兩篇定錨文獻：Bronson 等人 "Metastable Failures in Distributed Systems"（HotOS 2021）給出統一框架，Huang 等人 "Metastable Failures in the Wild"（OSDI 2022）給出真實案例譜系。它們的核心區分是 **trigger（觸發）與 sustaining effect（維持效應）**：

- **trigger**：把系統暫時推過山脊的擾動——一次部署、一波尖峰、一次依賴抖動。它可以瞬間消失。
- **sustaining effect**：把系統**鎖在**壞盆地的那個自我增強迴圈——這裡就是 retry。HotOS 論文的關鍵主張是「根因是維持效應，不是觸發」：很多不同的 trigger 經由同一個迴圈，產出一模一樣的崩潰態。

這解釋了你值班室的那個謎題。**為什麼尖峰過了還救不回來？** 因為一旦被擠過 ρ_tip，系統落進壞盆地；外部 λ₀ 退回 3.6，但壞盆地在 λ₀ = 3.6 時**依然存在**（雙穩態：同一個 λ₀ 兩個平衡都自洽）。系統沒有理由自己爬回山脊那一邊——它得到的每一個訊號都說「我超載，該重試」。為什麼重啟有效？重啟把 ρ 強制歸零，丟回好盆地的引力範圍。

### 量化擾動：多大的尖峰會把你推下去

雙穩態模型回答一個你以前只能憑感覺的問題：**系統離崩潰多遠？** 答案是好平衡到山脊的距離。

```text
好平衡：ρ_good = 0.600，λ_eff = 6.0 則/s
山脊：  ρ_tip  = 0.900，λ_eff = 9.0 則/s
要崩潰，瞬間有效負載必須被推過 9.0 則/s
→ 餘裕 = 9.0 − 6.0 = 3.0 則/s，即 +50% 的瞬時負載衝擊
```

一個讓 λ_eff 短暫衝到 6 則/s 的 +50% 的擾動，系統會自己彈回；衝到超過 9 則/s，就回不來了。這個 50% 餘裕就是你的崩潰預算。它取決於兩根你能調的旋鈕：g（裸負載）越高、b（retry 增益）越大，兩個根越靠近，餘裕越薄——當 4bg → 1（判別式 → 0），兩根合而為一（saddle-node 分岔），餘裕歸零，系統在毫無預警下從「有健康平衡」變成「只剩崩潰平衡」。**ch01 審判 #4「retry 是免費的保險」在這裡正式定罪：retry 不是免費的，它買的是一個會在你最需要餘裕時把餘裕吃光的回饋迴圈。**

### 四個防禦，各自的數學身分

工程界對付 retry storm 的招式不是玄學，每一招都對應到把上面某個量往安全方向推：

| 防禦 | 動了哪個量 | 數學身分 |
|---|---|---|
| **exponential backoff** | 降 b（feedback gain） | 失敗後等越久再重試，單位時間回饋的 retry 變少，b 變小，兩根拉遠、餘裕變厚（ch16 的放大係數變小） |
| **jitter（隨機化 backoff）** | 降 C²ₐ | 同步的 retry 是一團叢發（高 C²ₐ）；加隨機抖動把它去相關、攤平，降到達變異——這是 ch14 VUT 裡的 V 槓桿，也是 ch05「retry 流不是 Poisson」的反向修補 |
| **circuit breaker** | 強制離開壞盆地 | 連續失敗就跳 open、停發請求，把 ρ 拉回 0（ch06 的三狀態 Markov chain）——它是「重啟」的自動化版，強制系統脫離壞平衡的引力 |
| **admission control** | 截斷 feedback、保 goodput | 門口限流、滿了就丟（ch10 的 M/M/1/K），讓 ρ 進不了危險區；早拒絕優於晚放棄（ch10：blocking 零等待，reneging 先白等再丟） |

backoff 與 jitter 是一對：backoff 管「多久重試一次」（降 b），jitter 管「大家別一起重試」（降 C²ₐ）。Marc Brooker 的 "Fixing retries with token buckets and circuit breakers"（2022，見延伸閱讀）把這套組合拳講成工程實作：用 token bucket 給整個服務的 retry 設一個總預算（ch10 的 token bucket），用 circuit breaker 在依賴掛掉時整段停發。**重點不是裝哪一個，是認清它們各自在攻擊雙穩態模型的哪個係數**——裝了一堆卻全在動同一個旋鈕，餘裕還是薄的。

## autoscaling 的佇列論：你在盯哪個指標

autoscaling 是把 ch07 的生與滅裝上控制迴路：scale-up 是生、scale-down 是滅（ch07 橋接）。佇列理論在這裡回答兩個它特別擅長的問題：該盯哪個指標、為什麼會震盪。

**指標選擇：ρ vs E[N] vs E[T_Q]。** 常見的三個觸發指標，數學性格完全不同：

| 指標 | 性格 | 陷阱 |
|---|---|---|
| ρ（使用率，如 CPU%） | 平滑、好量，但**對延遲是非線性的**——hockey stick（ch08）：ρ 從 0.8 到 0.9 只動 0.1，E[T] 翻倍 | 設「CPU 70% 才擴」的人沒意識到 70%→85% 這段延遲已經爆掉了。ρ 是落後指標 |
| E[N]（佇列長/在途數） | 由 Little's Law E[N] = λE[T]（ch02）直接連到延遲，比 ρ 領先 | 仍需轉換成 SLA 語言；單站好用，網路裡 E[N] 分散難聚合 |
| E[T_Q]（等待時間） | 最貼近 SLA，使用者真正感受的量 | 量測本身有 coordinated omission 問題（見下與 ch19）；尾部量測要夠樣本 |

**裁決：盯 ρ 的代價是反應慢半個 hockey stick。** 因為延遲對 ρ 是 1/(1−ρ) 的非線性，等 ρ 報警時延遲已經在曲線陡峭段。盯 E[N] 或 E[T_Q] 更接近你真正在乎的東西——但代價是這兩個量更抖、更難設穩定的閾值。

**滯後與震盪。** autoscaling 是個帶**延遲**的負反饋控制器：偵測要時間、開新 instance 要時間（冷啟動）、新 instance 暖機要時間。控制理論的老教訓——**迴路裡的延遲會把負反饋變成振盪**：負載升 → （延遲後）擴容 → 此時尖峰已過、看起來過剩 → 縮容 → 負載又來 → 再擴……來回抽搐，就是 autoscaling 的 thrashing。緩解手段（cooldown、scale-down 比 scale-up 慢、目標值留 headroom）本質上都是在控制迴路裡加阻尼。這跟前一節 retry 的回饋是同一個家族：**帶正回饋會雙穩態，帶延遲的負回饋會振盪**——兩種都是「同一個 λ 系統行為不唯一」。

**square-root staffing 重訪（ch09）。** autoscaling 在問「該開幾台」，這正是 ch09 的 √a 法則：緩衝該按 √a 級開，不是按 a 的固定比例（M/M/∞ 那把尺：忙碌台數平均 a、標準差 √a）。對 autoscaling 的含義是反直覺但重要的：**規模越大，需要的相對 headroom 越小**。一個跑 a = 4 的小服務要 a + 2√a = 8 台（100% buffer）；一個跑 a = 100 的大服務只要 a + 2√a = 120 台（20% buffer）就有同等的 P(等待)。把 autoscaling 的目標使用率設成固定的 70%，對大服務是浪費、對小服務是危險——緩衝該隨 √a 縮放，不是固定百分比。這也是 ch01 審判 #1「80% 警戒線」在 autoscaling 場景的延伸：警戒線該隨規模浮動。

## tail latency 工程：用 fork-join 與重尾讀 Tail at Scale

ch18 把 fork-join（你每天寫的 `Promise.all`）的帳算清楚了，並在緩解手段那一節留了一句：「對落後者補射或綁定取消——hedged / tied requests，見 ch20。」現在兌現。

定錨文獻是 Dean & Barroso 的 "The Tail at Scale"（CACM 2013，見 landscape）。它的核心觀察你在 ch18 已經手算過：**scatter-gather 打 n 路，整體延遲由最慢一路決定**（E[max] = H_n/μ）；單路的「百年一遇」在 n 路扇出下變成日常（10 路裡 9.6% 的請求在等某路的最慢 1%，ch18）。重尾（ch15）讓這更兇——max 由最重那路主宰，H_n 的對數仁慈消失。Tail at Scale 的兩個招式，用本書的框架讀：

**hedged requests（對沖請求）。** 原請求發出後，**等它超過 P95 預期延遲**才補發一個副本到另一台，誰先回用誰、取消其餘。佇列論讀法：你在用「再抽一個獨立樣本取 min」對抗 tail——min of 2 的尾巴遠瘦於單一樣本（這是 ch04 競賽引理的好的那一面，min ~ Exp(Σλ)）。妙處在 P95 才補發：只有 5% 的請求會觸發 hedge，額外負載 ≈ 5%（V 槓桿的微調），卻砍掉 tail 最肥的那段。代價是那 5% 的重複工作——一個 throughput 換 tail 的小額交易。

**tied requests（綁定請求）。** 同時把請求送到兩台，**每台都被告知對方是誰**；哪台**先開始處理**就通知對方取消佇列裡的副本。Tail at Scale 的關鍵洞見是：**延遲的變異主要來自佇列等待，不是處理本身**——一旦開始處理，變異就小了。所以與其像 hedge 那樣等 P95，不如一開始就兩邊排隊、誰先排到誰做、立刻取消另一邊。用本書的話：tied requests 直接攻擊 ch14 VUT 裡的 U 槓桿造成的排隊變異——它賭的是「兩條獨立佇列同時都很長」的機率，遠小於「一條佇列很長」。這比 hedge 的浪費更少（取消發生在處理開始的瞬間，不是等到 P95），是 ch18 quorum（k-of-n）思路的近親：都在用冗餘換尾部，差別只在冗餘什麼時候、被取消得多快。

一句話收束 tail 工程：**ch15 告訴你 tail 為什麼厚，ch18 告訴你扇出怎麼把 tail 放大，Tail at Scale 告訴你怎麼用冗餘把它壓回去——三者是同一個重尾故事的三幕。** 這也半兌現了 ch01 審判 #3 的後半（P99 怎麼工程化），完整結案在總表。

## batching 的權衡：等湊批 vs 立即發

batching 是另一個你天天做的決策：訊息要不要湊一批再發、DB 寫入要不要 buffer 成 bulk insert。佇列論給它一個乾淨的 throughput–latency frontier 小模型。

設每次「啟動服務」有固定開銷 K（建連線、syscall、模型載入），加上每件工作的邊際成本 c。攢一批 b 件一起處理：

```text
處理一批 b 件的時間：K + b·c
每件的攤銷服務時間：E[S](b) = K/b + c        ← 批越大，固定開銷攤越薄
有效服務率：μ(b) = 1 / E[S](b) = b / (K + b·c)
```

batching 的 throughput 紅利清楚：b↑ → E[S](b)↓ → μ(b)↑ → 同樣 λ 下 ρ = λ/μ(b) 變小，系統更穩。但 latency 的帳是雙向的：

```text
batching 的延遲 = 攢批等待 + 攤銷後的服務（＋佇列等待）
攢批等待：到達率 λ 下，攢滿 b 件平均要等 ≈ (b−1)/(2λ)    ← 第一件等最久、最後一件不等
```

於是 frontier：**小 batch 攢批等待短但 μ 低（固定開銷沒攤開，ρ 高、佇列等待長）；大 batch μ 高但攢批等待長。** 中間有個最佳 b。一個有體感的算例（K = 50 ms、c = 10 ms、λ = 8 則/s）：

| batch b | E[S](b) = K/b + c | μ(b) | ρ = λ/μ | 攢批等待 (b−1)/(2λ) |
|---|---|---|---|---|
| 1 | 60 ms | 16.7/s | 0.48 | 0 ms |
| 4 | 22.5 ms | 44.4/s | 0.18 | 188 ms |
| 8 | 16.25 ms | 61.5/s | 0.13 | 438 ms |

b = 1 完全不攢批、零攢批等待，但每件扛滿 60 ms 固定開銷（μ 低、ρ 高）。b = 8 把服務時間攤到 16 ms，但平均每件要枯等 438 ms 湊齊（第一件等最久，要枯等 (b−1)/λ = 875 ms）。**這就是 batching 的本質權衡：你在用 latency 買 throughput，匯率由固定開銷 K 決定**——K 越大（攤銷紅利越甜），值得攢的批越大。實務的 adaptive batching（湊到 b 件**或**等到 timeout，先到先發）就是在這條 frontier 上動態選點：低負載時不攢（latency 優先）、高負載時攢大（throughput 優先）。

**LLM serving 的 continuous batching（一段點綴）。** 上面的靜態 batch 有個硬傷：一批裡最快完成的工作得等最慢的一起出批（fork-join 的 join 牆，ch18）。LLM 推論的 token 生成把這個浪費放到最大——不同請求的輸出長度差很多。2022 年的 Orca（OSDI 2022，論文用語 iteration-level scheduling）與隨後 vLLM 的 PagedAttention（SOSP 2023）做的 **continuous batching**，本質是**在每個 token 步重組批次**：誰完成了就讓位、新請求隨時插隊進批，不必等整批。用本書的話，它把「靜態 batch 的 join 牆」換成「逐 step 的動態 admission」——是 ch13 排程與本節 batching 的交叉路口。截至 2026-06，continuous batching + PagedAttention 已是 LLM serving 排程的業界基線（vLLM 仍活躍維護）。**機制細節超出本書範圍**——它是書架上《從後端到 AI Infra》的主場；這裡只標出它在排隊地圖上的座標：batching frontier 與動態排程的合流。

## 經驗法則的審判：總結表（ch01 清單結案）

ch01 把八條工程黑話送上法庭、各章審理，現在逐條宣判。判決三種：**成立**（升格定理）、**有條件成立**（附精確適用範圍）、**推翻**。編號與措辭照 ch01。

| # | 工程黑話 | 判決 | 判決理由（承審章） |
|---|---|---|---|
| 1 | 「使用率不要超過 80%」 | **有條件成立** | 80 不是定理，是 hockey stick E[T]=E[S]/(1−ρ) 上「曲線開始彎」的一個整數選擇（ch08）。正確的警戒線該隨兩件事浮動：**規模**（√a 法則：大池子可跑到 95%+，小池子 60% 就危險，ch09）與**變異**（VUT：C² 越大，同樣 ρ 等待越長，警戒線要往下調，ch14）。把 80% 當固定常數，對大服務是浪費、對小服務或高變異服務是危險 |
| 2 | 「慢了就加機器」 | **有條件成立** | 加在瓶頸站才有效（ch02 bottleneck）；共用佇列的池化贏過拆分（M/M/c vs c 個 M/M/1，同硬體差 2.9 倍，ch09）。但**三種情況加機器救不了**：瓶頸在別處（ch02）、服務重尾時要換的是排程不是機器（ch13/ch15）、以及 retry storm 的崩潰態——加機器只是抬高山脊，feedback 還在（ch16/本章）。「加機器」治得了 U 槓桿，治不了 V 槓桿與壞平衡 |
| 3 | 「平均沒事就沒事；要看尾巴，盯 P99 就夠」 | **有條件成立** | 平均與 tail 在輕尾下有固定關係（M/M/1 的 P99 ≈ 4.6× 平均，ch08），重尾下徹底脫鉤（nines 從等差變等比，ch15）。而「盯 P99 就夠」本身有兩個坑：fork-join 下整體 P99 要每路交出 P99.9（ch18）；固定 VU 壓測的 coordinated omission 會系統性低估 tail（ch19）。P99 要看，但要看對——量測方法本身會騙人 |
| 4 | 「retry 是免費的保險」 | **推翻** | retry 是 feedback（ch16），把 λ 放大 1/(1−p) 倍；p 隨負載漂移時，同一個 λ 長出健康與崩潰兩個自洽平衡（metastable failure，本章）。它買的是一個會在尖峰時把崩潰餘裕吃光的迴圈。防禦（backoff 降增益、jitter 降 C²ₐ、circuit breaker 強制脫離壞盆地、admission control 截斷回饋）不是選配，是 retry 的法定隨附費用 |
| 5 | 「buffer 開大一點總沒錯」 | **推翻** | 過載下無限 buffer 只是把丟棄改名叫遲到（ch10）：blocking 地板 1−1/ρ 由流量守恆決定，再大的 buffer 都丟不少於這個量；buffer 越大只是延遲越長、丟棄越晚（bufferbloat），疊上 goodput 更難看——大 buffer 的過載系統 throughput 高、goodput 趨近 0。早丟優於晚丟（ch10） |
| 6 | 「上下游各自做容量規劃就好」 | **有條件成立** | 合法性分三級（ch18 判決）：tandem 無 feedback 且全指數時精確（Burke 定理，ch11）；一般開放網路是 QNA 式近似，誤差來源明確（ch16/ch18）；fork-join、blocking、retry 相關性之下連近似的形都不對，要換工具。「各自規劃」不是定理，是一個有名字、有適用邊界的近似 |
| 7 | 「壓測跑三次取平均就穩了」 | **推翻** | 模擬/壓測的輸出高度自相關，樸素 CI 嚴重過窄——方法學差異 > 隨機誤差，跑三次取平均是民間統計學（ch19，需 warmup + batch means + 區間）。更糟的是固定 VU 的封閉壓測天生自我節流（ch17），系統變慢時自動少送請求（coordinated omission，ch19），**看不到真實過載**——你壓的是另一個系統 |
| 8 | 「已經等這麼久了，應該快輪到了」 | **推翻** | 指數服務無記憶（ch04）：等待的歷史對剩餘等待**透露零**。重尾下更糟，是反向的——等越久，期望剩餘越長（inspection paradox，撞上的工作期望長度可達無限，ch12/ch15）。「快輪到了」這個直覺在最該信它的重尾場景錯得最離譜 |

八條結案。三條有條件成立、五條推翻——這個比例本身是本書的論點：**工程黑話多半有真實的經驗基礎，但經驗法則和定理的差別就是適用條件，而黑話在你最需要它的時候沒帶條件來。** 你現在手上每一條都帶著條件了。

## 陷阱與防禦

本章把整套工具用在真實系統上，最大的陷阱是「把模型的乾淨當成系統的真相」。

| 陷阱 | 它怎麼騙你 | 怎麼自我察覺與防禦 |
|---|---|---|
| 把雙穩態模型的數字當預測 | 本章 ρ_good = 0.6、餘裕 +50% 是 mean-field 理想化（忽略漲落、retry 負載設成線性、單輪重試）算出來的——真實系統的山脊位置會隨漲落抖動，甚至在你算出的餘裕內就被一次運氣不好的尖峰推過去 | 模型給的是**骨架與方向**（有兩個平衡、餘裕隨 b 與 g 變薄），不是精確的崩潰點。要數字去模擬（本章 Python 實驗 + ch19 方法學）；餘裕當預算管，告警設在遠低於算出的山脊處 |
| 以為裝了 backoff 就免疫 retry storm | backoff、jitter、circuit breaker、admission control 各動不同係數；只裝一種（常見：只有 backoff）只動了 b，C²ₐ 與壞盆地的存在性沒變 | 對著四防禦表逐一檢查：我的 b 降了嗎？C²ₐ 去相關了嗎？有沒有強制脫離壞平衡的機制？有沒有門口限流保 goodput？四個旋鈕缺一個，餘裕就有個缺口 |
| autoscaling 盯 ρ 當早期警報 | ρ 對延遲是 1/(1−ρ) 非線性，等 ρ 報警延遲已在 hockey stick 陡峭段；ρ 是落後指標 | 盯更接近 SLA 的 E[N] 或 E[T_Q]；留 √a 級而非固定百分比的 headroom；迴路裡加阻尼（cooldown、非對稱 scale 速率）防振盪 |
| 把 batching 紅利當白吃的午餐 | 大 batch 抬 throughput 的同時，攢批等待 (b−1)/(2λ) 線性成長，低負載時尤其痛（沒流量還硬等湊批） | batching 是 latency 換 throughput，匯率是固定開銷 K；用 adaptive batching（湊滿 b 或 timeout 先到先發）在 frontier 上隨負載動態選點 |
| 拿單站工具分析有 feedback / fork-join 的系統 | 容量 walkthrough 的每一步都假設 λ 外生、無扇出；retry 讓 λ 內生（雙穩態）、fork-join 讓 E[T] 由 max 決定——單站公式直接失效 | walkthrough 第二步的決策框架最後一格就是這個叉路：有 feedback / fork-join / 重尾，公式只給方向，數字靠模擬 |

## 紙上推演

### 題 1：對自己的系統跑一次容量 walkthrough **[25 分鐘] ★★**

挑一個你現在維護或維護過的真實服務（API、worker pool、consumer 都行）。照本章五步走一遍：

(a) 寫下你**真的能量到**的四個數（λ busy hour、E[S]、C²ₐ、C²ₛ）；量不到的標「估」並寫下你怎麼估。
(b) 用決策框架選模型，講出為什麼（哪個假設成立、哪個最可疑）。
(c) 算 E[T] 與 E[T_Q]。
(d) 給一個 SLA（P99 < ? s），判斷現在達不達標，不達標的話該動哪根槓桿（加機器 / 降 C²ₐ / 縮 E[S]）收益最大。
(e) 寫下「下一個我該量但還沒量的數」。

這題沒有標準答案——它是 ch21 的暖身，也是這本書對你唯一真正的考核。

### 題 2：重建審判表中三條的論證 **[20 分鐘] ★★**

不看總表，對空氣各講 90 秒，重建這三條的判決與理由（講完對照）：

(a) 審判 #1「80% 警戒線」為什麼是「有條件成立」而不是「成立」？兩個讓警戒線該偏離 80 的因素是什麼？
(b) 審判 #4「retry 是免費的保險」為什麼被推翻？「雙穩態」這三個字要出現在你的講稿裡。
(c) 審判 #5「buffer 開大一點」為什麼被推翻？「blocking 地板」與「goodput」要出現。

### 題 3：backoff 上限怎麼選 **[15 分鐘] ★★**

exponential backoff 通常設一個上限（cap）：第 n 次重試等 min(base·2ⁿ, cap)。

(a) 從雙穩態模型的角度，backoff 的 cap 在調哪個係數？cap 設太小（接近 base）會怎樣？設太大（比方 5 分鐘）會怎樣？
(b) 一個服務的依賴平均故障恢復時間是 30 s。從「降 feedback 增益 b」與「故障恢復後多快重新導流」的張力出發，論證 cap 該落在什麼量級，並說出設成 30 ms 與設成 5 min 各自的失敗模式。

### 推演解答

**題 2。** (a) 80 不是定理，是 hockey stick 上一個方便的整數。兩個讓它偏離的因素：**規模**——√a 法則說緩衝按 √a 級開，大池子 ρ 可以跑很熱（a=100 開 120 台 ρ=0.83 仍安全），小池子 60% 就危險；**變異**——VUT 說等待 ∝ (C²ₐ+C²ₛ)/2，高變異系統同樣 ρ 等待長得多，警戒線要往下壓。漏掉任一個都不算懂——常見錯路是只講規模、忘了變異。

(b) retry 是 feedback（站內 λ_eff = λ₀/(1−p)），而 p 隨負載漂移，使 λ_eff 的自洽方程 ρ = g + bρ² 變成二次式——**兩個根 = 兩個自洽平衡（雙穩態）**：一個健康、一個崩潰。一次尖峰把系統推過中間的山脊，就落進崩潰盆地，尖峰過了也回不來（壞平衡在原 λ₀ 下依然存在）。所以 retry 不免費，它買的是一個吃掉崩潰餘裕的回饋迴圈。加分：指出餘裕 = ρ_tip − ρ_good，隨 b、g 變大而變薄。

(c) 過載（ρ > 1）下，流量守恆規定每秒多出來的 λ−μ 件必須從某個出口離開，**blocking 地板 = 1−1/ρ**，再大的 buffer 都丟不少於這個量。大 buffer 不減少丟棄，只把丟棄延後、把延遲拉長（bufferbloat）；疊上 goodput——當 E[T] 超過 client timeout，完工沒人收貨，throughput 高而 **goodput → 0**。所以「開大 buffer」把死刑改成凌遲。常見錯路：以為 buffer 大能「吸收」過載——它吸收的是尖峰（暫態），不是持續過載（穩態）。

**題 3。** (a) cap 設定的是 backoff 能把 feedback gain b 壓到多低的**下限**——重試間隔越長，單位時間回饋的 retry 越少，b 越小、雙穩態的餘裕越厚。cap 太小（≈ base）：backoff 形同虛設，retry 幾乎原速回饋，b 沒降下來，等於沒裝防禦。cap 太大：b 確實壓得很低（好），但代價是依賴恢復後，卡在長 backoff 裡的請求要枯等一整個 cap 才重新嘗試——**可用性恢復被自己的防禦拖慢**。

(b) 張力在於：cap 要夠大才能在故障期間把 b 壓到讓系統留在好盆地（降 feedback），又要夠小才能在故障結束後及時重新導流。依賴恢復要 30 s，cap 設成 **30 ms** 的失敗模式：故障期間 backoff 幾乎沒拉開間隔（30 ms 的重試對 30 s 的故障是密集轟炸），b 沒降，retry storm 風險照舊——cap 比故障時間尺度小太多，等於沒 backoff。設成 **5 min** 的失敗模式：依賴 30 s 就恢復了，但所有請求卡在 5 分鐘的 backoff 裡，恢復後要再等將近 5 分鐘才有像樣的流量回去——你把一次 30 s 的故障放大成 5 分鐘的可用性坑。合理量級：cap 落在依賴恢復時間的同一個數量級上下（這裡 ~30 s 到 1 min），讓 backoff 在故障期間真的拉開間隔（壓 b），又不至於在恢復後拖太久。配 jitter 去相關、配 circuit breaker 在依賴明確掛掉時整段停發（比盲目 backoff 更乾脆地脫離壞盆地）。沒有單一最佳值——cap 是「故障期壓 feedback」對「恢復期快導流」的匯率，跟 ch09 的 β、ch14 的兩根槓桿一樣，是個取捨旋鈕不是常數。

### Python 小實驗：retry feedback 的遲滯

把雙穩態模型動態化：讓外部負載 λ₀ **緩緩升上去、再緩緩降回來**，觀察上山的路與下山的路**不重合**——這就是 metastability 的體感。健康態崩潰的 λ₀（上山）會高於崩潰態恢復的 λ₀（下山），中間那段是遲滯迴圈：同一個 λ₀，系統處在哪個態取決於它**怎麼來的**。

模型沿用 worked example 的 retry 回饋 ρ = g + b·ρ²（b = 0.667），加一點隨機漲落（這就是為什麼要固定種子——漲落決定上山的路具體在哪一點被推過山脊）。標準函式庫即可，≤ 40 行。

```python
import random
random.seed(42)

MU = 10.0          # service rate (jobs/s); offered load g = lam0/MU
B = 0.667          # retry gain: backlog feeds back B*rho^2 extra load
NOISE = 0.01       # stochastic jitter (this is why the seed matters)

def relax(rho, lam0):                      # one noisy step toward rho = g + B*rho^2
    target = lam0 / MU + B * rho * rho
    rho = 0.5 * rho + 0.5 * target + random.gauss(0, NOISE)
    return min(1.05, max(0.0, rho))

def ramp(lams, rho):
    out = []
    for lam0 in lams:
        for _ in range(20):                # settle at each load level
            rho = relax(rho, lam0)
        out.append(rho)
    return out, rho

up = [2.6 + 1.8 * i / 100 for i in range(101)]    # offered lam0: 2.6 -> 4.4 /s
down = up[::-1]
up_rho, rho = ramp(up, rho=0.05)                  # start cold (healthy basin)
down_rho, rho = ramp(down, rho)

def at(s, xs, t):
    i = min(range(len(s)), key=lambda k: abs(s[k] - t)); return xs[i]

print("lam0   rho_up   rho_down")
for L in [3.0, 3.4, 3.6, 3.8, 4.0]:
    print("%4.1f   %5.3f    %5.3f" % (L, at(up, up_rho, L), at(down, down_rho, L)))
```

**預期輸出**（定性形態 + 數值區間，不是精確值——換種子會微移）：

```text
lam0   rho_up   rho_down
 3.0   ~0.40    ~0.37      ← 兩路都健康（低負載，唯一平衡）
 3.4   ~0.51    ~1.05      ← 分岔：上山仍健康，下山還鎖在崩潰態
 3.6   ~0.59    ~1.05      ← 同一個 lam0，兩個態（遲滯）
 3.8   ~1.05    ~1.05      ← 上山在此附近被推過山脊、崩潰
 4.0   ~1.05    ~1.05
```

要讀出的形態：(1) **上山路在 λ₀ ≈ 3.8 附近崩潰**（接近理論的 saddle-node：4bg = 1 ⇒ g = 0.375 ⇒ λ₀ = 3.75）；(2) **下山路一旦崩潰，要降到 λ₀ ≈ 3.2 以下才恢復**——遠低於它崩潰的 3.8；(3) 中間 λ₀ ∈ (3.2, 3.8) 是**遲滯迴圈**：rho_up 健康（~0.5–0.6）而 rho_down 崩潰（~1.05），同一個負載兩個命運。這就是「為什麼尖峰過了還救不回來」的可執行版本：把 λ₀ 推上去再放回原位，系統不會自己走回家。把 NOISE 調大，上山的崩潰點會更早、更不可預測——預測時運氣的成分被你親手放大了。

誠實標示：這是 mean-field + 漲落的**示意模型**，不是事件驅動的 M/M/1 retry 模擬（那要追每個 job 的 timeout 與重發，是 ch19 的份量）。它忠實重現的是**遲滯這個定性現象**與**它對種子/漲落的敏感**，不是任何精確的崩潰閾值。要精確閾值，照 ch19 的方法學跑真模擬、帶區間。

## 自我檢核

口頭自答，講得出來才算過關：

1. 容量規劃五步是哪五步？每一步最容易翻車的地方是什麼？（提示：busy hour、模型假設、4.6× 外推、hash 分流、coordinated omission）
2. 為什麼 retry 會讓同一個 λ 有兩個自洽平衡？「二次式有兩個根」對應到系統的什麼？
3. metastable failure 的 trigger 與 sustaining effect 差在哪？為什麼「重啟才好、尖峰過了救不回來」是這個區分的直接推論？
4. 四個 retry 防禦（backoff、jitter、circuit breaker、admission control）各動雙穩態模型的哪個量？只裝一個為什麼不夠？
5. autoscaling 盯 ρ 為什麼是落後指標？盯 E[T_Q] 的代價是什麼？autoscaling 為什麼會振盪？
6. hedged 與 tied requests 差在哪？tied requests 為什麼攻擊的是排隊變異而不是服務變異？這跟 ch18 的 quorum 是什麼關係？
7. batching 在用什麼換什麼？匯率由哪個量決定？低負載時大 batch 的失敗模式是什麼？
8. 審判表八條，哪三條「有條件成立」、哪五條「推翻」？各挑一條，把它的精確適用條件講出來。

## 延伸閱讀

- Nathan Bronson et al., "Metastable Failures in Distributed Systems", *HotOS 2021* — 本章雙穩態的定錨論文；讀它把 trigger／sustaining effect 的區分內化，這是看懂大型故障的關鍵框架。開放 PDF：https://sigops.org/s/conferences/hotos/2021/papers/hotos21-s11-bronson.pdf
- Lexiang Huang et al., "Metastable Failures in the Wild", *OSDI 2022* — 前一篇的實證續集，真實案例譜系與緩解手段；讀案例研究那節，看 retry storm 在不同公司長成什麼樣。開放 PDF：https://www.usenix.org/system/files/osdi22-huang-lexiang.pdf
- Marc Brooker, "Metastability and Distributed Systems"（2021-05-24）— metastable failure 的排隊直覺入門，「stable down」狀態講得最白話；本章雙穩態的部落格版。https://brooker.co.za/blog/2021/05/24/metastable.html
- Marc Brooker, "Fixing retries with token buckets and circuit breakers"（2022-02-28）— 把 retry 放大係數與本章四防禦寫成可實作的工程方案；token bucket 給 retry 設總預算那段直接對應 ch10。https://brooker.co.za/blog/2022/02/28/retries.html
- Jeffrey Dean & Luiz André Barroso, "The Tail at Scale", *CACM* 56(2), 2013 — tail latency 工程的定錨文獻；ch01 預告、ch18 鋪墊、本章兌現——hedged／tied requests 那兩段是必讀，配 ch18 的 fork-join 帳單一起讀。https://research.google/pubs/the-tail-at-scale/
- Gil Tene, "How NOT to Measure Latency"（Strange Loop 2015）— coordinated omission 的出處談話；審判 #3 與 #7 為什麼說「P99 量測本身會騙人」，這場 talk 講得最透。https://www.youtube.com/watch?v=lJ8ydIuPFeU
- Gyeong-In Yu et al., "Orca: A Distributed Serving System for Transformer-Based Generative Models", *OSDI 2022* — continuous batching（論文用語 iteration-level scheduling）的出處；本章只當點綴，機制深度在書架上的《從後端到 AI Infra》。https://www.usenix.org/system/files/osdi22-yu.pdf
