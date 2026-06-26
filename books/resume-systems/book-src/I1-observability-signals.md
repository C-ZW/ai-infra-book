# I · 觀測訊號

可觀測性處理的是同一個老問題：系統在生產環境出事時，你能不能**從外部輸出推斷內部狀態**，而不必登入機器重現。本檔收六條訊號層的概念——三本柱 metric / log / trace、從 log 算 metric 的陷阱、cardinality 爆炸、SLI / SLO / error budget、告警設計、分散式追蹤。它們回答「我想要什麼程度的『可推斷性』、願意付多少儲存與基數的代價」。本檔的邊界：只談**訊號本身**（怎麼產生、怎麼聚合、怎麼不爆掉、怎麼據此告警）；測試策略、負載測試、工具地圖在領域 I 的另一檔；事故應變、SRE 文化、DORA 在領域 V。

## 三本柱 metric / log / trace

### 定義與原理

可觀測性的「三本柱」是三種互補的遙測訊號，各自在不同的維度上把系統的內部行為外顯出來：

- **Metric（指標）**：把事件聚合成隨時間變化的數字序列（time series）。本質是「在一段視窗內，某件事發生了幾次／加總多少／分布如何」。儲存成本低（一條 time series 不論承載多少請求都只是一串 `(timestamp, value)`），但**有損**——聚合的那一刻，個別事件的細節就丟了。
- **Log（日誌）**：離散的、帶時間戳的事件紀錄，通常是文字或結構化的鍵值物件。本質是「在某個時刻，發生了這一件具體的事，這是它的全部欄位」。資訊量最高、最不失真，但**量最大、最貴**，且彼此孤立（一條 log 不知道它屬於哪個請求的哪一段）。
- **Trace（追蹤）**：把「一個請求穿越多個服務」的因果路徑串成一棵樹。每段工作是一個 span，span 之間有父子關係。它回答的是 metric 與 log 都答不了的問題：「這一次慢，是慢在哪一跳？」（機制見「分散式追蹤」）

三者不是三選一，而是**同一個事件的三種投影**：一次 HTTP 請求可以同時讓 request counter +1（metric）、寫一行 access log（log）、產生一個 root span（trace）。第一原理是**資訊量與成本成反比**：metric 便宜但粗，log 貴但細，trace 補上 metric/log 都缺的「跨服務因果」維度。

### 解法空間

把三種訊號落地，常見的做法：

- **各自獨立的 pipeline**：metric 進時序資料庫（如 Prometheus）、log 進日誌系統（如 Loki／Elasticsearch）、trace 進追蹤後端（如 Jaeger／Tempo）。簡單，但三者割裂，排障時要在三個 UI 間手動跳。
- **統一的採集層**：用一個 agent／SDK 同時產生三種訊號，並在它們之間植入**關聯 ID**（把 trace_id 寫進 log、把 exemplar 從 metric 連到 trace）。OpenTelemetry 是這條路的事實標準（2026-06：traces 與 logs 規格已 stable、metrics data model 已 stable）。
- **從一種訊號衍生另一種**：例如從 structured log 聚合出 metric（見「從 log 算 metric 的陷阱」），或從 trace 抽出 RED 指標。省一套 pipeline，但繼承來源訊號的取樣／遺漏問題。
- **寬事件（wide events）流派**：放棄「先決定要哪些 metric」，改成每個請求寫一條欄位極多的結構化事件，查詢時才即席聚合。彈性最高，儲存與查詢成本最高。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Metric（時序聚合） | 固定低成本、可長期保留、適合告警與儀表板 | 「現在系統健康嗎、趨勢如何」 | 聚合即失真；高基數標籤會讓成本爆炸（見「cardinality 爆炸」） |
| Log（離散事件） | 單一事件無損、可事後任意查詢 | 「這一筆到底發生什麼、錯誤訊息是什麼」 | 量大、貴；高流量下幾乎一定要取樣；跨服務難關聯 |
| Trace（因果樹） | 跨服務延遲歸因、父子關係 | 「這次慢/錯在哪一跳、調用鏈長什麼樣」 | 幾乎一定取樣（全量太貴）；需全鏈路傳播 context 才完整 |
| 三者關聯（trace_id 貫穿） | 一個 ID 在三訊號間跳轉 | 端到端排障 | 需採集層支援注入；漏注入則退回各自孤立 |

判準：**告警與容量趨勢用 metric；根因細節用 log；跨服務延遲歸因用 trace。** 三者要靠共同的 trace_id 串起來才有「1+1+1>3」的效果。

### 何時需要

- **單體服務、低流量**：metric + log 兩本柱通常就夠；trace 的價值在「跨服務」，單體內 trace 收益遞減（用 profiler 反而更直接）。
- **微服務、請求跨多跳**：trace 從「nice to have」變成必需——沒有它，「p99 慢」這種問題在多服務拓樸下幾乎無法定位到具體那一跳。
- **over-engineering 警訊**：流量每天幾千請求卻先上全套 OTel + 三後端 + tail sampling，維運這套的成本可能超過它省下的排障時間。先 metric + structured log，trace 等到「跨服務排障真的痛」再加。

Worked example：一個服務每秒 1,000 請求。若每請求寫 1 條 access log（約 1 KB），一天就是 1000 × 86,400 × 1 KB ≈ **86 GB/天** 純 access log。同樣的流量做成 metric，只要 `http_requests_total` 一條 counter＋幾條 histogram，一天的時序資料是 **MB 等級**。這個約 4–5 個數量級的差距，正是「為什麼 metric 永遠開全量、log 與 trace 幾乎一定要取樣」的根本原因。

### 常見誤解與陷阱

- **「有 log 就有可觀測性」**：log 答不了「跨服務這次慢在哪」，也答不了「過去 30 天 p99 趨勢」。三本柱缺一就有盲區。
- **把三本柱當成三個獨立專案**：不植入共同 trace_id，排障時就退化成「在三個 UI 之間靠時間戳猜對應關係」，等於白建。
- **以為 metric 可以事後補細節**：metric 在寫入時就聚合了，事後想知道「那一秒到底是哪些 user 觸發的」——資訊已經不在了。要事後可查的細節，當下就得進 log/trace。
- **把高基數塞進 metric**：想用 metric 的便宜換 log 的細粒度（每個 user_id 一條 time series），結果是 cardinality 爆炸（見下條）。需要高基數維度的，那是 log/trace 的工作，不是 metric 的。
- **AI 輔助排障的新陷阱**：把三訊號丟給工具自動歸因，能加速找線索，但若採集層本身漏注入 trace_id 或 metric 已失真，AI 只是更快地給出**有信心的錯誤結論**；訊號品質是上游問題，再聰明的下游分析也補不回來。

### 延伸閱讀

- OpenTelemetry — Observability primer：https://opentelemetry.io/docs/concepts/observability-primer/
- OpenTelemetry — Signals（traces/metrics/logs）：https://opentelemetry.io/docs/concepts/signals/
- Google SRE Book, Ch.6 "Monitoring Distributed Systems"（四個黃金訊號 golden signals 的出處）：https://sre.google/sre-book/monitoring-distributed-systems/

## 從 log 算 metric 的陷阱

### 定義與原理

「從 log 算 metric」是一種很自然的省事做法：既然每個請求都寫了 log，何必再額外埋一個 counter？直接在日誌系統裡 `count by (status)` 或對 `latency` 欄位算分位數，就「免費」得到 metric 了。這條路在低流量下確實划算，但它把 metric 的正確性**綁死在 log 的完整性上**——而 log 偏偏是最容易被取樣、被丟、被截斷的訊號。第一原理：**聚合的正確性取決於樣本的代表性與完整性**；log 在高流量下三者都不保證。三個結構性陷阱：取樣（sampling）、遺漏（loss）、視窗（windowing）。

### 解法空間

- **直接埋指標（不經 log）**：在程式碼裡用 metric SDK 維護 counter / histogram，與 log 各走各的 pipeline。counter 是「每個事件原子 +1」，不受取樣影響。
- **全量 log + 事後聚合**：完全不取樣 log，查詢時即席算 metric。正確，但儲存成本可能無法承受。
- **取樣 log + 帶權重還原**：log 取樣時記下取樣率，聚合時用 `1/rate` 加權還原總量。能修「總量低估」，但修不了分位數與長尾的代表性。
- **結構化 log 嚴格 schema**：保證每條 log 都有 `latency_ms`、`status` 等欄位且型別一致，讓聚合不會因解析失敗而靜默漏算。
- **兩條路並行對帳**：關鍵指標同時用埋點 metric 和 log 聚合各算一份，定期比對差距，把「log 聚合」當便宜的補充而非真相來源。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 直接埋 metric | 計數精確、不受取樣影響、成本固定 | 告警、SLO、容量趨勢這類要準的數字 | 維度受限（高基數會爆）；需在程式碼裡埋點 |
| 全量 log 聚合 | 任意維度可事後算、最靈活 | 低流量、需要事後切任意維度 | 高流量下儲存成本可能不可行 |
| 取樣 log + 加權還原 | 修正總量級偏差 | 高流量下只要量級對的計數 | 分位數/長尾仍失真；尾端事件被取樣機率低 |
| metric + log 並行對帳 | 互為校驗、抓得到漂移 | 關鍵業務指標 | 兩套維護成本；需定義「差多少算異常」 |

### 何時需要

- **要拿來告警或當 SLO 的數字，一律走埋點 metric**——這種數字錯了會直接誤導決策。
- **探索性、事後才想到要看的維度**，用 log 聚合很合適：你沒辦法事先為每個未知問題埋好 metric。
- **流量小到 log 全量保留無壓力**，從 log 算 metric 是合理的省事，不必為它另起一套埋點。

Worked example：一個服務每秒 10,000 請求，log 因成本設了 **1% head sampling**（每 100 條留 1 條）。現在想從 log 算「過去 5 分鐘的錯誤率」。實際發生 3,000,000 個請求、其中 3,000 個錯誤（錯誤率 0.1%）。取樣後 log 裡約有 30,000 條請求、30 條錯誤——若**忘了用 `1/rate=100` 加權**，你算出的「錯誤數＝30」會把真實的 3,000 個錯誤低估 100 倍；而即使加權還原了總量，**p99 延遲仍然失真**：真正拖慢系統的那 0.1% 長尾請求，被 1% 取樣命中的期望只有 `3,000,000 × 0.001 × 0.01 = 30` 條，分位數估計的方差大到不可信。這就是「總量可加權修、長尾分位數修不回來」的具體形狀。

### 常見誤解與陷阱

- **取樣**：以為「log 取樣不影響算出來的比率」。比率（如錯誤率）若兩邊同率取樣大致還行，但**絕對量一定要加權還原**，否則低估；而長尾分位數（p99/p999）本質上樣本就稀，取樣後幾乎不可信。
- **遺漏**：log pipeline 在背壓時會**靜默丟棄**（buffer 滿了就丟）——而它最常在「系統出事、log 暴量」時丟，於是你最需要數據的那一刻，恰恰是數據最不完整的一刻。從 log 算出的「事故期間請求數」往往莫名偏低，就是這個原因。
- **視窗**：log 的時間戳是「事件發生時間」還是「寫入時間」？跨時區、延遲到達（late arrival）的 log 會落在錯誤的聚合視窗裡，讓「某分鐘的 QPS」忽高忽低。固定視窗邊界還會切斷跨視窗的請求。
- **解析失敗靜默漏算**：某次發版改了 log 格式，聚合的正則沒跟上，於是那一批 log 被悄悄跳過——metric 看起來「流量下降」，其實只是算不出來了。
- **把 log 聚合當 SLO 真相來源**：SLO 是要拿去談判和告警的（見「SLI / SLO / error budget」），用一個會被取樣、會被丟、會因格式漂移而漏算的來源去定它，等於把承諾建在流沙上。

### 延伸閱讀

- OpenTelemetry — Sampling（取樣對聚合的影響）：https://opentelemetry.io/docs/concepts/sampling/
- Prometheus — Instrumentation best practices（為什麼計數要用 counter 埋點）：https://prometheus.io/docs/practices/instrumentation/
- Prometheus — Histograms and summaries（分位數估計的前提）：https://prometheus.io/docs/practices/histograms/

## cardinality 爆炸

### 定義與原理

在時序系統裡，一條獨立的 time series 由「指標名 + 一組標籤鍵值（labels）」唯一決定。**Cardinality（基數）＝不同標籤組合的總數＝實際存在的 time series 條數**。爆炸的根因是組合爆炸：總基數約等於各標籤可能取值數的**乘積**。一個 `http_requests_total{method, status, endpoint, user_id}`，若 method 有 5 種、status 有 6 種、endpoint 有 50 種、user_id 有 100 萬種，理論上限是 `5 × 6 × 50 × 1,000,000 = 1.5 × 10⁹` 條 series。

為什麼這會殺死系統？時序資料庫（如 Prometheus）為了快速查詢，會把**每一條 active series 的標籤索引常駐記憶體**。series 數量直接決定記憶體佔用，而不是樣本（datapoint）數量。所以一個高基數標籤（user_id、request_id、完整 URL with query string）就足以讓記憶體從幾 GB 飆到 OOM。第一原理：**metric 的成本由基數決定，不由流量決定**——這跟直覺相反，但正是 metric 與 log 的分工線。

### 解法空間

- **不把高基數維度放進 metric 標籤**：user_id、session_id、request_id、raw URL、error message 這些天然高基數的東西，屬於 log/trace 的維度，不是 metric 的。
- **標籤值正規化／分桶**：把 `/users/12345/orders` 正規化成 route template `/users/{id}/orders`；把連續值（如金額、延遲）放進 histogram bucket 而非當標籤。
- **限制標籤值集合**：對可能無界的標籤（如 customer_tier）設白名單，未知值歸到 `other`，避免被惡意或意外的值灌爆。
- **exemplar 取代高基數標籤**：要從某條 metric 跳到具體那個慢請求，用 exemplar（在 histogram bucket 上附帶少數樣本的 trace_id）而非把 trace_id 變成標籤。
- **設防護欄**：在採集端（如 Prometheus 的 `sample_limit`、relabel drop）或 SDK 端設每指標的 series 上限，超過就丟並告警，避免單一壞指標拖垮整個系統。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 高基數維度只進 log/trace | metric 基數可控、成本可預測 | user_id/request_id 等天然無界的維度 | 失去在 metric 上直接按該維度切分的能力 |
| route template 正規化 | 把 N 個 URL 收斂成少數路由 | 含路徑參數的 HTTP 指標 | 正規化規則要維護；漏一條就漏一片基數 |
| 標籤值白名單 + other | 防無界標籤被灌爆 | 來源不可信或可能新增值的維度 | `other` 桶會把細節糊掉 |
| exemplar 連到 trace | 低基數 metric ＋按需跳到單筆 | 「p99 高，給我一個例子」 | 需後端支援 exemplar；只是樣本不是全量 |
| 採集端 series 上限 | 單一壞指標不會 OOM 整個系統 | 防呆、止血 | 觸發上限後該指標數據不完整 |

### 何時需要

- **任何用 Prometheus 類拉式時序系統的場景**，基數治理都是必修——它的記憶體模型讓基數成為硬天花板。
- **多租戶、面向終端使用者的服務**：天然有大量高基數維度（每個 user、每個 device），最容易不小心把它們塞進標籤。
- **不必過早治理的場景**：內部低流量工具、標籤維度天生有限（只有 region × status 幾種組合）時，基數根本到不了危險區，先別為它設一堆防護欄。

Worked example：某團隊在 `http_request_duration_seconds` 上加了一個 `user_id` 標籤想做 per-user 延遲分析。服務有 50 萬活躍 user，histogram 預設 10 個 bucket，再乘上 status（5 種）：`500,000 × 10 × 5 = 2.5 × 10⁷` 條 series。Prometheus 每條 active series 約佔數 KB 記憶體（含索引），保守抓 3 KB，光這一個指標就吃掉 `2.5×10⁷ × 3 KB ≈ 75 GB` 記憶體——遠超單機可用，直接 OOM。修法：拿掉 `user_id`，per-user 延遲改用 trace（用 exemplar 從 bucket 跳到具體慢請求），基數立刻掉回 `10 × 5 = 50` 條。

### 常見誤解與陷阱

- **「多加個標籤又沒多少資料」**：危險的不是資料量，是**新標籤與既有標籤的乘積**。在 1,000 條 series 的指標上加一個 1,000 取值的標籤，瞬間變 100 萬條。
- **以為刪掉標籤就立刻回收記憶體**：series 變成 inactive 後，仍會在保留期內佔用資源（要等 churn 出視窗）。高 churn（標籤值不斷出現又消失，如每次都用新 request_id）比高基數更陰險——它讓**新舊 series 同時佔記憶體**。
- **raw URL 當 endpoint 標籤**：含 query string 或路徑 ID 的 URL 是無界的；一定要正規化成 route template。
- **error message 當標籤**：錯誤訊息常含動態內容（ID、時間戳），每個都不同，等於無界基數。錯誤細節進 log，metric 只留 error type / code。
- **把基數問題當成「買更大記憶體」**：基數是組合爆炸，是指數級的；加記憶體是線性的，追不上。治理維度才是解，加硬體只是把爆炸延後。

### 延伸閱讀

- Prometheus — Naming and labels（標籤基數警告）：https://prometheus.io/docs/practices/naming/
- Prometheus — Instrumentation：do not use high cardinality labels：https://prometheus.io/docs/practices/instrumentation/#do-not-overuse-labels
- OpenTelemetry — Metrics data model（attributes 與 cardinality）：https://opentelemetry.io/docs/specs/otel/metrics/data-model/

## SLI / SLO / error budget（p99 / p999）

### 定義與原理

這三個詞是 SRE 把「可靠性」從感覺變成可談判數字的一條鏈：

- **SLI（Service Level Indicator，服務水準指標）**：一個量測「使用者體驗到的好壞」的比值，標準形式是 `好事件數 / 有效事件數`。例如「回應 < 300ms 且非 5xx 的請求 / 全部有效請求」。SLI 必須從**使用者視角**量，不是 CPU 使用率這種內部指標。
- **SLO（Service Level Objective，服務水準目標）**：對 SLI 訂的目標門檻，例如「過去 28 天，99.9% 的請求是好的」。它是**你自己對自己的承諾**，比對外的 SLA（合約，違約要賠）寬一級。
- **Error budget（錯誤預算）**：`1 − SLO`。SLO 99.9% 就是「允許 0.1% 的請求是壞的」。這 0.1% 不是失敗，是**預算**——它是「可以拿去冒險（發版、實驗、容忍小故障）」的額度。預算沒燒完，就大膽發版；燒完了，凍結變更、專心穩定。

p99 / p999 是訂 SLI 門檻時最常用的**分位數**：p99 = 99% 的請求比這個值快（等價地，最慢的 1% 比它慢）；p999 = 千分之一的尾巴。第一原理：**平均值會被長尾騙，分位數才反映「最差的那批使用者」的體驗**。

### 解法空間

- **用什麼 SLI**：可用性比（成功率）、延遲分位數（p99/p999）、新鮮度（資料延遲）、正確性（對帳一致率）、吞吐——依服務性質選。
- **怎麼量延遲分位數**：用 histogram（預先分桶、可跨副本聚合，`histogram_quantile()` 插值算分位）vs summary（在 client 端算好分位數、**不能跨實例聚合**）。本書取捨見下表。
- **視窗策略**：rolling window（過去 28 天滾動）給穩定的趨勢；calendar window（每月歸零）對齊商業週期但月初月末行為不同。
- **怎麼用 error budget 告警**：固定門檻告警（燒到剩 X% 就告）vs **burn rate alert**（看「以目前速度多久燒完」，快燒給高優先告警、慢燒給工單）。
- **多目標分層**：對同一服務訂多個 SLO（p99 < 300ms 且 p999 < 1s），分別管「一般體驗」與「最差體驗」。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Histogram 算分位數 | 可跨副本/跨時間聚合、可改算任意分位 | 多實例服務的 p99/p999 SLI | 精度取決於 bucket 邊界；窄桶才準 |
| Summary（client 端分位） | 單實例精確分位、不需後端插值 | 單實例、不需聚合 | **不能跨實例聚合**（平均多個 p99 是錯的） |
| Rolling window SLO | 趨勢平滑、無月初歸零的鋸齒 | 大多數服務 | 老故障要滾出視窗才「還預算」 |
| Burn-rate 告警 | 燒得快才吵醒人、燒得慢只開工單 | 想降告警疲勞又不漏快速燒穿 | 需調多重視窗（短窗抓急、長窗抓慢） |

### 何時需要

- **有明確使用者、可靠性會影響留存或收入的服務**：SLO 讓「要不要為穩定性踩煞車」變成看預算的客觀決定，而非拍腦袋或誰嗓門大。
- **跨團隊依賴**：上游給下游一個 SLO，下游才能合理設計自己的逾時與降級（見領域 P）。
- **over-engineering 警訊**：一個內部 cron、掛了重跑就好、沒人即時依賴它——為它訂 99.99% SLO 與 burn-rate 告警是浪費。SLO 的成本（量測、維護、值班）只有在「可靠性真的有人在乎」時才划算。

Worked example：服務月流量 1 億請求，SLO「99.9% 成功」。error budget ＝ `0.1% × 100,000,000 = 100,000` 個失敗請求／月。若某次發版引入 bug，每分鐘多 200 個失敗，則 `100,000 / 200 = 500` 分鐘 ≈ **8.3 小時**就會燒光整月預算。Burn-rate 視角：正常每分鐘該燒 `100,000 / (30×24×60) ≈ 2.3` 個，現在燒 200 個，burn rate ≈ **86×**——這種速度該立刻 page 值班，而不是等到月底才發現預算見底。對照分位數：若把 SLI 從成功率換成 p99 < 300ms，平均延遲可能只有 50ms（看起來很健康），但 p99 是 280ms、p999 是 1.2s——**平均值完全藏住了那 0.1% 體驗極差的使用者**，這正是要看分位數而非平均的理由。

### 常見誤解與陷阱

- **平均多個 p99 得到總 p99**：數學上錯的。三台副本各自的 p99 平均起來，不等於合併資料集的 p99。要正確聚合，必須用 histogram 在 bucket 層面合併後再算 `histogram_quantile()`，不能拿算好的分位數去平均。
- **把內部指標當 SLI**：CPU 80%、queue 長度——這些是原因不是症狀，使用者不在乎 CPU 多少，在乎請求成不成功、快不快。SLI 要從使用者那一端量。
- **SLO 訂成 100%**：100% 沒有 error budget，意味著任何發版風險都不能冒、任何單點故障都違約。**刻意留出不可靠的額度**正是 error budget 的價值；追求 100% 是反生產力的。
- **分位數的取樣陷阱**：若 SLI 來自取樣的 trace/log，p999 這種千分之一的尾巴本身樣本就稀，取樣後估計方差大到不可信（見「從 log 算 metric 的陷阱」）。p999 SLI 最好建在全量的 histogram 上。
- **error budget 燒完卻照常發版**：那 SLO 就只是裝飾。error budget 的整個重點是它**有牙齒**——燒完就觸發凍結變更的政策（見領域 V 的 SRE 文化），否則訂它沒意義。

### 延伸閱讀

- Google SRE Book — Service Level Objectives：https://sre.google/sre-book/service-level-objectives/
- Google SRE Workbook — Implementing SLOs（含 burn-rate alerting）：https://sre.google/workbook/implementing-slos/
- Prometheus — Histograms and summaries（為何不能平均分位數）：https://prometheus.io/docs/practices/histograms/

## 告警設計（症狀 vs 原因、告警疲勞）

### 定義與原理

告警是「系統把『需要人介入』的判斷主動推給人」的機制。它的核心矛盾是兩種錯誤的取捨：**漏報（false negative）**——真出事卻沒告，與**誤報（false positive）**——沒事卻吵醒人。把門檻調鬆會漏報，調緊會誤報，沒有免費午餐。第一原理（源自 SRE）：**好的告警對應的是「使用者正在受影響」的症狀，而不是「某個內部零件壞了」的原因**。原因有千百種、會隨架構變，症狀（請求失敗、變慢）少而穩定且直接對應使用者體驗。對症狀告警，自然涵蓋你還沒想到的故障模式。

**告警疲勞（alert fatigue）** 是這套機制的慢性病：誤報多了，人會開始無視告警、調靜音、條件反射地點掉——於是真正重要的那一條被淹沒。一個吵但大多是雜訊的告警系統，比沒有告警更危險，因為它給人「有在看」的假象。

### 解法空間

- **症狀告警（symptom-based）**：對 SLI 燒穿告警（錯誤率、延遲分位數超標），對應使用者影響。少而準。
- **原因告警降級為診斷訊號**：CPU 高、磁碟快滿、queue 堆積——這些不直接 page 人，而是進儀表板，等症狀告警觸發後拿來查根因。例外：「磁碟 30 分鐘後寫滿」這種**有前導期、不處理必出事**的原因，值得提早告（但給工單而非半夜 page）。
- **多視窗 burn-rate 告警**：用快窗（如 5 分鐘）抓急速燒穿、慢窗（如 1 小時/6 小時）抓緩慢漏血，分別對應 page / ticket，避免單一固定門檻又吵又漏（見「SLI / SLO / error budget」）。
- **分級與路由**：page（立刻吵醒）、ticket（上班看）、log-only（只記錄）三級；按嚴重度與緊急度路由，不是所有告警都 page。
- **去抖與抑制**：for duration（持續 N 分鐘才告，濾掉瞬間抖動）、依賴抑制（上游掛了就別讓下游一起狂告）、分組（同一事件的多條告警合併成一則）。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| 症狀告警（對 SLI） | 涵蓋未知故障、對應使用者影響、條目少 | 面向使用者的服務的主力告警 | 需要先有好的 SLI；只告「壞了」不告「為何壞」 |
| 原因告警（資源/零件） | 指向具體零件、利於快速定位 | 當診斷輔助、或有前導期的容量問題 | 當主力會爆量且會隨架構漂移；多數不該 page |
| 多視窗 burn-rate | 急燒快告、緩燒開單，降疲勞又不漏 | error-budget-driven 的成熟告警 | 視窗與門檻要調，初期較複雜 |
| for-duration 去抖 | 濾掉瞬間尖峰、減少誤報 | 本來就會短暫抖動的指標 | 拉長＝延後真實事件的告警，要權衡 |
| 依賴抑制/分組 | 一個根因不變成一場告警風暴 | 有明確依賴拓樸的系統 | 抑制規則錯了會把真問題也吞掉 |

### 何時需要

- **任何有值班、半夜會被吵醒的團隊**：告警設計直接決定值班的人能不能睡、會不會 burnout。這不是 nice-to-have。
- **剛上線、故障模式未知的新系統**：先上**少數症狀告警**（SLI 燒穿），別一開始就鋪滿原因告警——你還不知道哪些原因重要，鋪滿只會製造疲勞。
- **over-engineering / 反模式警訊**：為每個內部指標都設一條告警、每條都 page、門檻憑感覺定——這是製造告警疲勞的標準配方。告警要少而狠，每一條都該能回答「它響了，人現在要做什麼」。

Worked example：某團隊有 120 條告警規則，其中約 90 條是原因告警（CPU > 80%、記憶體 > 85%、某 queue > 1000…）。一個月統計：總共觸發 800 次，事後標記只有約 **40 次**對應真正需要人介入的事件——**誤報率 95%**。值班的人三週後養成「先靜音再說」的習慣，於是某次真正的資料庫連線池耗盡告警也被條反靜音，事故延誤 40 分鐘才有人處理。改法：刪掉 90 條原因告警的 page 屬性（降為儀表板/工單），只保留約 6 條症狀告警（對 SLI 的多視窗 burn-rate），page 量從每月數百降到個位數，每一條 page 都對應「使用者正在受影響」。

### 常見誤解與陷阱

- **對原因告警 page**：CPU 高不等於使用者有問題（可能只是批次任務在跑），對它 page 是誤報工廠。對症狀 page、把原因留作診斷。
- **「多告總比漏告好」**：在告警疲勞面前這是錯的。淹沒在雜訊裡的關鍵告警＝實質的漏報。**訊噪比**比覆蓋率更決定告警系統的真實價值。
- **靜態門檻撞上日夜/週期波動**：「QPS < 100 就告」在半夜本來就低流量，天天誤報。要嘛用相對基準（同比上週），要嘛只對 SLI 燒穿告警（它自帶流量歸一化）。
- **告警沒有 runbook**：一條 page 響了，值班的人不知道該做什麼——這條告警的價值大打折扣。每條 page 級告警都該連到「現在做什麼」（見領域 V 的事故應變）。
- **AI 輔助告警的新陷阱**：用工具做異常偵測/動態門檻能減少手動調參，但它會引入**不可解釋的告警**——半夜被一條「模型覺得異常」的 page 吵醒卻沒有明確症狀與 runbook，反而加重疲勞與不信任。AI 適合當「降噪/聚合/建議」的輔助，最終 page 人的判準仍應回到可解釋的使用者影響症狀。

### 延伸閱讀

- Google SRE Book — Monitoring Distributed Systems（symptom vs cause）：https://sre.google/sre-book/monitoring-distributed-systems/
- Google SRE Workbook — Alerting on SLOs（multi-window burn-rate）：https://sre.google/workbook/alerting-on-slos/
- Rob Ewaschuk — "My Philosophy on Alerting"（症狀告警原典）：https://docs.google.com/document/d/199PqyG3UsyXlwieHaqbGiWVa8eMWi8zzAn0YfcApr8Q/edit

## 分散式追蹤（trace context 傳播、span、取樣）

### 定義與原理

分散式追蹤把「一個請求穿越多個服務」的完整因果路徑重建成一棵樹。三個核心概念：

- **Trace**：一次端到端請求的全部記錄，由一個全域唯一的 `trace_id` 標識。
- **Span**：trace 樹裡的一個節點＝一段有起止時間的工作（一次 RPC、一次 DB 查詢、一段內部計算）。每個 span 有自己的 `span_id`、指向上游的 `parent_span_id`、開始/結束時間戳，以及 attributes（如 HTTP status、DB statement）。父子 span 的時間區間嵌套，就還原出「誰調用誰、各花多久」。
- **Context propagation（context 傳播）**：要把分散在 N 個服務的 span 拼成一棵樹，每個服務在往下游發請求時，必須把 `trace_id` 和當前 `span_id` **隨請求傳下去**——通常透過 HTTP header。W3C 把這個格式標準化成 **`traceparent`／`tracestate` header**（Trace Context 於 **2020-02-06 成為 W3C Recommendation**；Level 2 在 2026-06 仍是 Candidate Recommendation Draft，主要強化 trace-id 隨機性，不改 header 結構）。`traceparent` 形如 `00-<32hex trace-id>-<16hex span-id>-<2hex flags>`。

第一原理：**沒有 context 傳播，每個服務的 span 都是孤兒**——你有一堆 span 卻拼不成樹，等於沒有 trace。傳播鏈只要斷一環（某個服務沒轉發 header），那一跳之後的因果就丟了。

### 解法空間

- **傳播格式**：W3C Trace Context（`traceparent`/`tracestate`，跨廠商互通的標準）vs 各家私有格式（如 B3、Jaeger header）。混用多語言/多廠商時，標準格式才能無縫接力。
- **怎麼植入傳播**：手動在每個出站呼叫塞 header（細粒度但易漏）vs 自動 instrumentation（SDK/agent 攔截 HTTP/gRPC client 自動注入，省事但要該語言有支援）。
- **取樣決策點**：
  - **Head-based sampling（頭部取樣）**：在 root span 產生的當下就擲骰決定整條 trace 留不留（如 10%）。便宜、無狀態、低延遲，但**錯誤與慢請求只占極少數，隨機取樣大機率漏掉它們**——而那恰恰是你最想看的。
  - **Tail-based sampling（尾部取樣）**：等整條 trace 完成、看到全貌（有沒有錯、夠不夠慢）再決定留不留。能精準留下錯誤/長尾，但 collector 必須**緩衝一條 trace 的所有 span 直到完成**，且同一 trace 的 span 要路由到同一個 collector 實例，記憶體與架構成本高。
- **取樣率還原**：取樣後算 metric/統計，要記錄取樣率以加權還原（見「從 log 算 metric 的陷阱」）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| W3C Trace Context 傳播 | 跨語言/跨廠商互通 | 異質微服務、多廠商後端 | 傳播鏈斷一環就丟下游因果 |
| 自動 instrumentation | 省手動、漏埋少 | 主流框架/語言 | 非標準協定或自家 transport 仍需手動補 |
| Head-based 取樣 | 成本固定、低延遲、無狀態 | 高吞吐、只要代表性樣本 | 大機率漏掉錯誤/長尾這些最有價值的 trace |
| Tail-based 取樣 | 精準留住錯誤/慢 trace | 排障價值高、預算夠 | 需緩衝整條 trace；同 trace span 要同實例；記憶體貴 |

### 何時需要

- **請求跨 ≥ 3 個服務、且「慢/錯在哪一跳」是反覆出現的問題**：這是 trace 不可替代的場景——metric 告訴你「p99 高」，log 告訴你「這台機器這條 log」，只有 trace 把「整條鏈各跳耗時」攤開。
- **單體或極簡拓樸**：trace 收益遞減，profiler / APM 內視更直接，先別上整套追蹤基礎設施。
- **取樣策略的選擇**：流量低（每秒幾百）可以接近全量、不必取樣；高流量先上 head-based 控成本，等「老是漏掉想看的錯誤 trace」變成痛點，再評估 tail-based。**別一開始就上 tail-based**——它的架構複雜度只有在規模到了才值得。

Worked example：一個請求路徑 gateway → orders → payments → DB，p99 端到端延遲 800ms，但四個服務各自的 dashboard 都顯示「自己很健康」（各自 p99 < 250ms）。沒有 trace 時，這是個無解的羅生門——每個團隊都說不是自己。接上 trace 後，把這條 trace 的 span 攤開：gateway 自身 20ms、orders 30ms、payments **620ms**、DB 80ms（四段相加 750ms，與端到端 800ms 的差約 50ms 落在跨服務網路傳輸與序列化等不被 span 計入的縫隙）——payments 對某個外部風控 API 的調用沒設好逾時，瓶頸一目了然。取樣面：若用 head-based 10%，這條 800ms 的慢 trace 只有 10% 機率被留下；改用 tail-based「latency > 500ms 全留」，這類慢 trace 100% 保留，而正常的快 trace 仍只留 10% 控成本——這就是 tail-based 在排障上的價值所在。

### 常見誤解與陷阱

- **傳播鏈悄悄斷掉**：某個老服務、某條非 HTTP 路徑（如丟進 message queue 再被消費）沒有轉發 `traceparent`，trace 就在那裡斷成兩棵孤樹。跨非同步邊界（queue/event）的傳播最常被漏（要把 trace context 塞進訊息 metadata）。
- **以為 head-based 取樣能事後補看錯誤 trace**：head-based 在請求一開始就決定丟棄，等你發現某筆出錯想回頭看，它的 span 根本沒被記錄——錯誤 trace 的「事後可得性」是 tail-based 才有的能力。
- **取樣後直接拿 trace 數量當流量指標**：trace 是取樣的，數出來的「請求數」不是真實量；要量請求數請用全量的 counter metric。
- **span 太細或太粗**：每個函式都開 span 會爆量又難讀；整個服務只有一個 span 又看不出內部瓶頸。粒度應對齊「有意義的工作單元」（一次 RPC、一次 DB query、一段關鍵計算）。
- **clock skew 扭曲 span 時間**：span 起止時間戳來自各機器的本地時鐘，跨機器時鐘不同步會讓子 span 看起來「比父 span 還早開始」或負延遲。追蹤後端通常會用因果關係修正顯示，但底層時間仍不可全信（時鐘問題見領域 M）。

### 延伸閱讀

- W3C — Trace Context（Recommendation）：https://www.w3.org/TR/trace-context/
- OpenTelemetry — Traces / Context propagation：https://opentelemetry.io/docs/concepts/signals/traces/
- OpenTelemetry — Sampling（head vs tail）：https://opentelemetry.io/docs/concepts/sampling/
- Sigelman et al. — "Dapper, a Large-Scale Distributed Systems Tracing Infrastructure"（2010，分散式追蹤原典）：https://research.google/pubs/pub36356/
