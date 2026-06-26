# cardinality 爆炸：一個 label 如何拖垮監控

某天有人開了一個再正常不過的 pull request。服務的延遲儀表板上想多一個視角——按使用者切分，看看是不是某些大客戶的請求特別慢。改動只有一行：在既有的 `http_request_duration_seconds` histogram 上，多掛一個 `user_id` label。code review 過了，沒有人覺得有什麼好攔的——不過就是多帶一個欄位，連新的指標都沒加。它合進主幹、隨著下一次部署上線。

接下來幾個小時，監控系統的記憶體曲線開始一路往上爬，不回頭。先是查詢變慢，儀表板載入要轉好幾秒；接著抓取（scrape）開始逾時；最後 Prometheus 行程被 kernel 的 OOM killer 收掉、重啟、再被填滿、再被收掉。諷刺的是，**最先瞎掉的，正是你用來看「系統現在好不好」的那隻眼睛**——出事的時候，你連 dashboard 都打不開。

把這件事拆開，會看到一個違反直覺、但一旦理解就再也忘不掉的事實：**在時序系統裡，一個指標的成本不是由它承載多少流量決定的，而是由它的 cardinality（基數）決定的。** 那一行 `user_id` 沒有讓任何一個請求變多，卻可能讓監控的記憶體需求漲上幾個數量級。要看懂這是怎麼發生的，得先弄清楚「一條 time series」到底是什麼。

## 一條 time series，是被 label 組合定義出來的

時序資料庫存的不是「指標」，而是 **time series**——一串隨時間變化的 `(timestamp, value)`。問題的核心在於：一條 time series 是由什麼**唯一決定**的？答案是**指標名，加上一整組 label 的鍵值。** 下面這些在資料庫眼中是四條**互不相同**的 series：

```
http_requests_total{method="GET",  status="200", endpoint="/checkout"}
http_requests_total{method="GET",  status="500", endpoint="/checkout"}
http_requests_total{method="POST", status="200", endpoint="/checkout"}
http_requests_total{method="POST", status="200", endpoint="/cart"}
```

指標名相同，但只要任何一個 label 的值不同，就是一條全新的 series，各自有獨立的儲存、獨立的索引項。於是「這個指標佔多少資源」這個問題，等價於「它展開成多少條 series」。而這個展開，是一個**乘積**：

> 總 series 數 ≈ 各 label 可能取值數的**相乘**。

`method` 有 5 種、`status` 有 6 種、`endpoint` 有 50 種，這個指標就是 `5 × 6 × 50 = 1,500` 條 series——還在可控範圍。但乘法是無情的：只要其中**任何一個 label 的取值集合是無界的**，整個乘積就跟著無界。把 `user_id` 加進去，假設有 100 萬個活躍使用者，理論上限瞬間變成 `5 × 6 × 50 × 1,000,000 = 1.5 × 10⁹`——十五億條 series。這不是流量漲了十五億倍，請求數一筆都沒多；漲的是**這個指標在資料庫裡攤開後的形狀**。

這就是 cardinality 爆炸的全部數學：它是**組合爆炸**。危險的從來不是「這個 label 本身有多少值」，而是它**與既有 label 相乘**的結果。在一個只有 1,000 條 series 的指標上，加一個區區 1,000 種取值的 label，下一刻就是一百萬條。每個獨立看都「不過幾千個值」的 label，相乘之後是天文數字。

## 為什麼多幾條 series 就能殺死整個系統

光是 series 變多，為什麼會直接 OOM？這要看時序資料庫——以 Prometheus 為最典型的代表——在記憶體裡到底放了什麼。

Prometheus 把最近一段時間（約 1 至 3 小時）正在寫入的資料保存在一個叫 **head block** 的記憶體結構裡。每隔約兩小時，head 裡的資料才被壓實、寫成磁碟上的持久區塊。關鍵在於：為了讓「給我所有 `status="500"` 的 series」這類查詢能快，Prometheus 為 label 維護了一個**倒排索引**——對每一個 `label=value` 對，記下所有含這個對的 series 清單。而**每一條 active series，連同它在索引裡的條目，都常駐記憶體。**

所以記憶體佔用幾乎正比於 **active series 的條數**，而**不是**樣本（datapoint）的數量。一條 series 不論它一秒被寫一次還是一小時被寫一次，佔的索引成本是一樣的。經驗上，每條 active series 連同索引大約吃 **1 至 3 KB** 記憶體（實務上常用約 3 KB 估，視 label 長度與查詢負載而定，行程實際 RSS 可能再翻倍）。換算成一句好記的法則：**每一百萬條 active series，大約要 3 到 4 GB 記憶體**，這還只是 head block 本身，不算查詢時的開銷。

現在回頭算那條 `user_id`。它掛在一個 histogram 上，而 histogram 有個容易被忽略的性質——它**本身就是一台 cardinality 放大器**。一個 classic histogram 不是一條 series：每個分桶邊界 `le` 都是一條獨立的累積計數 series（含一定會有的 `le="+Inf"` 那條），外加 `_sum` 和 `_count` 兩條。一個 `le` 值總共 10 條（含 `+Inf`）的 histogram，每一組 label 組合會展開成 `10 + 2 = 12` 條 series——若你定義的是 10 個有限邊界，再加 `+Inf` 就是 `11 + 2 = 13` 條，邊界數怎麼算下面取 12 為例。於是把它和 `user_id`（50 萬活躍使用者）、`status`（5 種）相乘：

```
50 萬 user_id × 12 條 histogram series × 5 種 status
  = 500,000 × 12 × 5
  = 3 × 10⁷  條 series
```

三千萬條 series。每條保守抓 3 KB：

```
3 × 10⁷ 條 × 3 KB ≈ 9 × 10⁷ KB ≈ 90 GB 記憶體
```

光是**這一個指標**，就要吃掉九十 GB——而且這只是 head block 的純索引底線（用前面那條 3 KB/series 直算），把前面提過的 RSS 翻倍算進去，實際還要再乘上約一倍——遠超任何單機能給的量。行程在被填滿的途中就被 OOM killer 收掉了。一行 review 時看起來人畜無害的 `user_id`，代價是這個。而修法只要把 `user_id` 拿掉，這個指標立刻塌回 `12 × 5 = 60` 條 series——3×10⁷ 對 60，差了約 50 萬倍，**近六個數量級**。per-user 的延遲分析不是不能做，而是它根本不該用 metric 的 label 來做（後面會講該用什麼）。

這個算術解釋了一條看似武斷、其實精準的官方建議。Prometheus 的儀表化指南直接給了門檻：**單一指標的 cardinality 盡量壓在 10 以下，全系統超過這個數的指標只該有屈指可數的幾個；任何一個指標 cardinality 過 100、或有長成那麼大的潛力，就該停下來重新設計，而不是塞進監控系統。**「10」聽起來小得離譜，但理解了乘法和 histogram 的放大效應，你就知道這個數字一點都不保守——因為它指的是**單一指標自己那幾個 label 的乘積**，而這個乘積還會再被部署的實例數、分桶數繼續乘上去。

## churn：比高基數更陰險的那一種

到這裡，cardinality 還像是個靜態的數字——某個指標就是有那麼多 series。但真實系統裡，最難纏的不是「基數高」，而是**基數一直在變**。這種現象叫 **churn（流失）**：series 不斷地出現又消失。

想像你不是用 `user_id`，而是用 `request_id` 當 label——每一個請求都有一個全新、唯一的 request_id。從某一秒的快照看，active series 數量也許不算嚇人；但下一秒，這批 request_id 全部不再有新資料寫入、變成 inactive，又湧進一整批全新的 series。這就是高 churn。

它陰險在哪？因為 series 變 inactive **不等於**記憶體立刻被釋放。那些剛剛還在寫、現在不再寫的 series，仍然留在 head block 裡，要等到下一次壓實、被擠出記憶體視窗，才真正釋放。於是在那個約兩小時的視窗內，**新湧入的 series 和剛死掉的舊 series 同時佔著記憶體**。高 churn 的可怕之處正在這裡：它讓你的記憶體佔用，不取決於「任一瞬間活著多少 series」，而取決於「**一個視窗內前後總共出現過多少不同的 series**」。一個瞬時基數看起來很溫和、但 churn 極高的指標（每個請求換一個新標籤值），可能比一個瞬時基數固定、不流動的高基數指標更快把你的記憶體撐爆。

這也順手戳破一個常見的誤判：「我把那個壞 label 刪掉了，記憶體怎麼還是高？」因為被你刪掉的 series 不會立刻消失，它們得 churn 出那個保留視窗才會回收。止血和退燒之間，隔著一個壓實週期的延遲。

## 哪些 label 是地雷：無界性，而不是「現在有幾個值」

既然爆炸來自「無界的 label 撞上乘法」，那麼治理的第一原則就清楚了：**判斷一個 label 該不該進 metric，看的不是它此刻有幾個值，而是它的取值集合是否有界、會不會無限長出新值。** 幾類經典地雷，它們的共同點都是**無界**：

- **天然唯一的識別碼**：`user_id`、`session_id`、`request_id`、`order_id`。值的數量等於實體的數量，隨業務無上限地長。
- **原始 URL 當 endpoint**：`/users/12345/orders` 這種含路徑參數、含 query string 的完整路徑是無界的——每個 ID 都是一個新值。它必須被正規化成 **route template**：`/users/{id}/orders`。少正規化一條路由，就漏掉一整片基數。
- **錯誤訊息當 label**：`error message` 常內嵌動態內容（ID、時間戳、輸入片段），幾乎每筆都不同，等於無界。錯誤的**類型／代碼**（`error_type`、`code`）是有界的、可以當 label；錯誤的**訊息全文**屬於 log，不屬於 metric。
- **任何來自外部、你不控制其取值範圍的東西**：User-Agent 全文、客戶端 IP、第三方傳回的任意欄位。一個惡意或單純出包的呼叫端，可以靠灌入大量不同的值，把你的監控系統當成攻擊面打爆。

反過來，安全的 label 都有一個共性：**取值集合小、固定、可枚舉**——`method`（HTTP 動詞就那幾個）、`status`（狀態碼有限）、`region`（機房數量固定）、正規化後的 `route`。判準不是「現在資料庫裡有幾個值」，而是「**這個維度有沒有一個它永遠不會超過的上界**」。沒有上界的，就是地雷，無論它今天看起來多溫和。

那連續的數值——金額、延遲毫秒數——怎麼辦？它們也是無界的，但有專門的去處：**histogram 的分桶**。把延遲放進 `le="0.1"`、`le="0.5"`、`le="1"` 這種預先定義的桶，而不是把每個毫秒值當 label。連續量用分桶收斂成有限的幾條 series，這正是 histogram 存在的理由之一。

## 高基數的需求並沒有消失，它只是換了一個訊號去承載

講到這裡有個張力：那位開 PR 的人想看「per-user 延遲」，這需求是真實且合理的。cardinality 治理不是叫你別問這種問題，而是把它**導到對的訊號上**。三種觀測訊號的分工，本質就是一條基數的分界線（三者的互補關係，見〈三本柱：metric、log 與 trace〉）。

metric 便宜，是因為它在寫入的當下就把個別事件聚合掉了——代價是它**承受不起高基數**。log 和 trace 正相反：它們保留個別事件的完整細節，**高基數是它們的常態**——每一條 log 本來就帶著它那一筆的 `user_id`、`request_id`、完整 URL，這毫無問題，因為它們不為每個唯一值維護一條常駐記憶體的索引 series。所以那條鐵律是：

> **需要按高基數維度切分的分析，是 log 與 trace 的工作，不是 metric 的。**

但這留下一個實際的縫隙：你在 metric 上看到「p99 延遲飆高」，想知道「**到底是哪一筆**慢」——而 metric 為了便宜，恰恰把「哪一筆」聚合掉了。把 `user_id` 塞回 label 去補這個縫，就是爆炸的開端。正確的橋是 **exemplar**：在 histogram 的某個 bucket 上，附帶**少數幾筆**樣本請求的 `trace_id`（exemplar 是 OpenMetrics 帶進來的概念，Prometheus 2.26 起可儲存與查詢，但須以 `--enable-feature=exemplar-storage` 顯式開啟、預設關閉，且只存在一個固定大小的記憶體環形緩衝區裡）。指標本身維持低基數，但每個 bucket 上掛著一兩個「範例請求」的指標——你在儀表板上看到那根高 bucket，點下去就跳到一條真實的慢請求 trace。

關鍵差別在於量級：exemplar 是**每個 bucket 幾筆樣本**，是常數級的附加成本；把 `trace_id` 當 label 則是**每個唯一 trace 一條 series**，是爆炸級的。同樣是「從聚合數字跳到具體個案」，一個用樣本指標、一個用無界索引，命運天差地別。「p99 高，給我一個例子」這個需求，exemplar 答得起，label 答不起。

## 防護欄：因為光靠紀律一定會破防

到目前為止談的都是「設計時別放錯 label」。但任何系統的安全姿態，都不能假設每一個 commit 都做對了——開場那行 `user_id` 就是過了 review 才上線的。所以成熟的監控系統會在**採集邊界**架硬性防護欄，讓「單一個壞指標」沒辦法拖垮整個系統。

Prometheus 這側有兩個層次的閘門，值得分清楚它們攔在哪裡、各自的失敗模式是什麼：

- **`metric_relabel_configs`**：在抓取後、寫入儲存前，對**每一個樣本**套用規則，可以 drop 掉某些 label 或整條 series。這是收斂基數的主力——例如把無界的原始路徑改寫成 route template、丟掉某些用不到的 histogram 桶。它的代價要記在心上：規則對**每個樣本每次抓取**都跑一遍，一條寫得笨的 regex 掛在五萬樣本的 job 上，會燒掉看得見的 CPU。
- **`sample_limit`**：對單次抓取設一個樣本數上限，套完 relabel 之後若仍超過，**整次抓取直接判失敗**。這是一道止損閘——一個爆掉的指標會讓那個 target 的抓取整個失敗，於是它**只毒到自己那個 target**，不會滲進儲存、把全系統的記憶體吃光。

注意第二道閘的取捨：它用「**犧牲這個 target 的可觀測性**」換「**保住整個監控系統的存活**」。觸發上限的那個 target，這段時間是沒有數據的——你失去了它的能見度。但相對於整個 Prometheus OOM、所有服務同時瞎掉，這是划算的隔離。**寧可一個 target 暫時看不見，也不要整隻監控的眼睛一起瞎**——這個取捨的形狀，和限流、艙壁隔離是同一個家族：在邊界丟掉一部分，保住核心不被拖垮。

不同生態系把這道防線架在不同的位置，失敗模式也跟著不同，這個對照本身很有啟發：

| 機制 | 防線位置 | 超限時的行為 |
|---|---|---|
| Prometheus `sample_limit` | 抓取時、per-target | 整次抓取失敗，該 target 這輪無數據 |
| Prometheus `metric_relabel_configs` | 抓取後、寫入前 | 主動 drop/改寫 label，把基數壓掉 |
| OpenTelemetry SDK 基數上限 | 應用端 SDK 聚合時 | 預設 2000，超過的歸進一個合成的 overflow 資料點 |

最後那一列是個很值得停下來看的對比。OpenTelemetry 的 metrics SDK 預設每個指標有 **2000** 的 cardinality 上限；一旦某個指標的不同屬性組合超過 2000，超出的那些**不會被丟棄**，而是被併進一個帶有 `otel.metric.overflow=true` 屬性的合成資料點裡——測量值守恆（不重複計、不漏計），但你**失去了區分它們的能力**：超限之後出現的新組合，全部糊成同一個 overflow 桶。這是另一種哲學——Prometheus 的 `sample_limit` 是「超了就讓整次抓取失敗、大聲報錯」，OpenTelemetry 的 overflow 是「超了就靜默地把細節糊掉、但保住總量」。前者吵、後者安靜，各有各的陷阱：吵的那個你會立刻知道出事，但會丟整個 target 的數據；安靜的那個系統不會掛，但你可能很久都沒發現某個指標的後半段細節已經全進了 overflow 桶、再也分不開。

## 加記憶體永遠追不上組合爆炸

每次出 cardinality 事故，總有人問同一句：「那加大記憶體不就好了？」這個直覺值得認真駁倒，因為它指向了問題的本質。

cardinality 是**組合爆炸**——它是各維度取值數的乘積，每多一個無界 label、每漲一個量級的取值，series 數量就跳一個或好幾個數量級。而加記憶體是**線性**的：你頂多把機器從 64 GB 換到 128 GB，翻一倍。**用線性的資源去追指數級的增長，方向上就追不上**——你今天加倍撐過去，明天多一個 region、多一批使用者、某個呼叫端開始灌新值，乘積又把你頂破。加硬體不是解，只是把爆炸的時刻往後推了一格，同時讓下一次爆得更貴。

真正的解永遠在**治理維度**這一側：砍掉無界 label、正規化路徑、把高基數需求導去 log/trace、用 exemplar 接回個案、在採集邊界架防護欄。這些動作改變的是那個乘積的因數本身，而不是去買一個更大的容器來裝這個注定會溢出的乘積。

值得一提的是，這場拉鋸也在從工具層被改善。Prometheus 的 **native histogram** 用指數分桶、把一整個分布表示成**單一條 series**（而非 classic histogram 那種一個 `le` 一條 series 的展開），大幅壓掉了 histogram 自帶的那層基數放大——當你需要按 label partition histogram 時，這個差別尤其明顯。但工具的改進改變的是**乘積裡某個因數的大小**，沒有、也無法廢掉乘法本身：只要你還往 label 裡塞無界的維度，再省的 histogram 也擋不住那個無界因數把整個乘積拉爆。

## 為什麼是這個形狀

退一步看，cardinality 爆炸不是某個工具的實作瑕疵，而是從一個**根本的設計選擇**裡長出來的必然後果。

時序系統之所以便宜、之所以能用幾 MB 存下一個服務一整天的請求量趨勢，正是因為它在寫入的當下就**把個別事件聚合成了 series**——它不為每一筆請求留一條記錄，只為每一種「label 組合」留一條隨時間走的曲線。這個聚合是它全部的成本優勢來源。但同一個設計選擇，也精準地定義了它的死穴：**它的成本錨定在「有多少種組合」，而不是「有多少筆事件」。** 高基數正是「組合多到爆」的另一個名字。便宜和易爆，是同一枚硬幣的兩面——你沒辦法只要前者、不要後者。

所以那條把 `user_id` 塞進 label 的修改之所以致命，不是因為它做錯了什麼罕見的事，而是因為它**誤解了自己在跟哪一種訊號打交道**：它把一個 log/trace 才承受得起的高基數需求，交給了一個成本由組合數決定的訊號去扛。理解了這個形狀，你看 metric 的 label 設計時就會有一種近乎本能的警覺——每加一個 label，心裡先過一遍那個乘法，先問一句「這個維度有上界嗎」。守住這條線，那隻用來看系統的眼睛，才不會在你最需要它的時候，第一個瞎掉。

## 延伸閱讀

- Prometheus — Instrumentation best practices（"do not overuse labels"，含 cardinality 盡量壓在 10 以下、過 100 重新設計的準則）: https://prometheus.io/docs/practices/instrumentation/#do-not-overuse-labels
- Prometheus — Metric and label naming（label 基數警告）: https://prometheus.io/docs/practices/naming/
- Prometheus — Configuration（`sample_limit`、`metric_relabel_configs` 的語意）: https://prometheus.io/docs/prometheus/latest/configuration/configuration/
- Prometheus — Storage / TSDB（head block、壓實與保留，理解記憶體為何錨定 active series）: https://prometheus.io/docs/prometheus/latest/storage/
- Prometheus — Native histograms（用單一 series 表示分布、壓低 histogram 自帶的基數放大）: https://prometheus.io/docs/specs/native_histograms/
- OpenTelemetry — Metrics SDK（cardinality limit 預設 2000 與 `otel.metric.overflow` 合成資料點）: https://opentelemetry.io/docs/specs/otel/metrics/sdk/
- OpenMetrics 1.0 specification（exemplars：把 metric bucket 連到 trace 的格式）: https://prometheus.io/docs/specs/om/open_metrics_spec/
- Cloudflare — How Cloudflare runs Prometheus at scale（per-series 記憶體與 churn 的實戰量測）: https://blog.cloudflare.com/how-cloudflare-runs-prometheus-at-scale/
