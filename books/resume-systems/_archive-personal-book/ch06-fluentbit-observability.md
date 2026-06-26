# ch06 — FluentBit + Lua：從 log 擠出 metric 的可觀測性 pipeline

> **本章解決什麼問題**：你在 NeoBards 自建了一條「FluentBit + Lua filter 從 production log 萃取 API 回應時間 metric、輸出 S3 供 Nexon」的 pipeline。你寫得出它做了什麼，但你大概沒挖過：「從 log 反推 metric」這條路底下藏著一個會悄悄騙你的數學陷阱（p95 不能跨機器、跨視窗平均），以及一連串你當年隱性回答過的取捨——聚合放邊緣還是中心、buffer 滿了該丟還是該擋、為什麼是 S3 而不是直接進 metric 系統。這章是 Part II（NeoBards）的最後一章，也是全書「觀測」這一軸（五軸的第五軸）的第一次正式出場；完整的觀測性框架與 cardinality 深掘留給 ch15，背壓機制留給 ch14，這章只把你親手做的那條管線挖穿。

## 從你已知的出發

你當年在 NeoBards 做的這件事，履歷上是一行字：「自建 FluentBit + Lua 可觀測性 pipeline，從 production log 萃取 API 回應時間 metric，輸出 S3 供發行商 Nexon 使用」。把它展開，當年的場景大概是這樣：你的後端服務（跑在 client-managed 的基礎設施上，500K+ 使用者、10K+ CCU）每秒吐出一堆 access log，每一行裡有 endpoint、HTTP status、還有一個你最在乎的數字——這個請求花了幾毫秒。Nexon 作為發行商，想要的不是一行行的原始 log，而是「你們的 API 健不健康」這個問題的可聚合答案：p95 回應時間、錯誤率、按 endpoint 拆開的延遲。

於是你架了一條 FluentBit pipeline。FluentBit 在邊緣（每台機器、或每個 pod 旁邊）讀 log，用一段 Lua filter 把每行 log 裡的 latency 數字挖出來、做一點就地加工，再把結果寫進 S3 的某個 bucket。Nexon 那邊定期去讀那個 bucket，當成他們監控你服務的資料源。整條管線你自己搭、自己調、自己背鍋。

你當年做這件事的直覺是對的：你不想把每秒幾千行的原始 log 整包推到下游讓別人去算——那既貴又慢，而且把一個「我這邊就能算的東西」變成了跨組織的依賴。你選擇在邊緣就地把 log 嚼成 metric，只把濃縮過的結果往外送。這個直覺——**把計算推到資料產生的地方、只送結論不送原料**——是邊緣聚合（edge aggregation）的核心，也是這條管線最聰明的設計。

但你可能沒想過的是：**這條路有一個會在你背後悄悄出錯、而且不會報錯的地方**。當你在邊緣就把 p95 算好、只把那個數字送下游時，你其實已經把原始的延遲分布**丟掉了**。而 p95 這種百分位數，有一個違反直覺的性質——它**不能被平均、不能被合併**。三台機器各自算出來的 p95，平均起來不是整個機群的 p95；這一分鐘的 p95 和下一分鐘的 p95，平均起來也不是這兩分鐘的 p95。如果你的 pipeline 是「每台邊緣各自算 p95、寫進 S3，然後 Nexon 把這些數字平均」——那 Nexon 看到的「p95」是一個**沒有數學意義的數字**，而且它不會抱怨、不會噴錯，只會給你一個看起來很合理、其實是錯的答案。

這章要做的，就是把這條你親手搭的管線，從「它做了什麼」挖到「它在每一個環節上其實在權衡什麼、哪一步會悄悄錯」。我們先把「從 log 算 metric」放回可觀測性的地圖上看它的定位，再把 FluentBit 的 pipeline 每一階段拆開，然後正面對上那個百分位數的陷阱。

## 三本柱與「從 log 反推 metric」這條路

可觀測性（observability）通常被拆成三本柱：metric、log、trace。它們不是三個競品，是三種**用不同代價換不同資訊**的東西。把它們的取捨講清楚，你才知道你當年那條 pipeline 站在哪。

- **Metric（指標）**：預先聚合的數字時間序列，例如「每分鐘的 p95 回應時間」「每秒請求數」。它**便宜、可聚合、查詢快**，因為它在寫入前就把細節壓掉了——一分鐘幾千個請求，最後只剩幾個數字。代價是**低基數（low cardinality）友善、高基數會爆**：一旦你想按 user_id 拆，500K 個使用者就是 500K 條時間序列，成本失控（這個 cardinality 爆炸的深掘留 ch15）。
- **Log（日誌）**：一行行帶時間戳的事件記錄，**細節最高**——每個請求發生了什麼、帶什麼參數、走哪條路徑，都在裡面。代價是**貴又容易遺漏**：量大、儲存與查詢成本高，而且在高負載下 log 本身會被丟（buffer 滿了、磁碟滿了、取樣）。
- **Trace（追蹤）**：一個請求跨多個服務的因果鏈，回答「這 800ms 花在哪個服務、哪一段」。代價是要**全鏈路埋點**，少一段就斷。trace 與 OpenTelemetry 留 ch15。

你當年做的事，用這張地圖講，是一條很特定的路：**你沒有直接產生 metric，你產生的是 log，然後從 log 反推 metric**。你的服務沒有埋一行「我現在要報一個 latency metric 出去」的程式碼；它只是照常寫 access log，而你在 log 流的下游，用 FluentBit 把 latency 從 log 字串裡解析出來、聚合成 metric。

這條路**極其常見**，常見到很多團隊根本沒意識到自己在做一個有取捨的決定。它有兩個真實好處：一是**不用改應用程式**——你不需要去每個服務裡塞 metric 上報的程式碼，log 反正本來就在寫；二是**log 是真相的最高解析度版本**，理論上你想算什麼 metric 都能從 log 裡挖出來，不用預先決定。

但它有一個結構性的弱點，而且這個弱點正是這章的主軸：**你的 metric 的正確性，完全取決於 log 的完整性**。Metric 如果是應用程式直接埋點上報的，那個 counter 自己就是真相；但 metric 如果是從 log 反推的，那麼**只要 log 掉了一行，你的 metric 就少算了一個樣本**。在高負載——也就是你最需要正確 metric 的那一刻——log 恰恰最容易被丟（buffer 滿、取樣啟動、磁碟壓力）。於是你得到一個殘酷的反相關：**系統越是出事，你用來判斷它出事的 metric 就越不準**。這就是「我以為 vs 實際」的第一個落差：

> **我以為**：從 log 算 metric，反正 log 是最完整的真相，metric 一定準。
> **實際**：metric 的準確度被 log 的完整度封頂；log 在高負載下會被丟，所以這條路在尖峰時刻最不可信——而尖峰正是你最在乎 metric 的時候。

## FluentBit 的 pipeline：每一階段在幹嘛

FluentBit（2026-06 已是 v5.0 系列，最新約 v5.0.7／2026-06-05；v4.2 系列維護至 2026-06-30）是一個用 **C 寫的輕量日誌處理代理**。它的兄弟 Fluentd 是 **Ruby 核心＋gem plugin 生態**——**兩者都是 CNCF graduated 專案**，不是競品而是分工：Fluentd 外掛超過一千個、適合當重量級的中央 aggregator；FluentBit 內建外掛、為容器與資源受限環境的高效能設計，CNCF 自己的遷移指南（2025-10）說它每單位資源能處理的 log 量是 Fluentd 的 10–40 倍（視外掛而定）。你當年選 FluentBit 是對的：你要的是貼在邊緣、吃資源少、就地嚼 log 的那種代理，不是中央那台胖機器。

一條 FluentBit pipeline 的資料流是這樣（這張圖值得你停下來看，因為你當年搭的就是它，而每一個方框都藏著一個取捨）：

```
   你的服務寫的 access log
            │
            ▼
   ┌──────────────────┐
   │  input（tail）   │  讀 log 檔／stdout，一行變一筆 record
   └──────────────────┘
            │  原始字串
            ▼
   ┌──────────────────┐
   │  parser          │  用 regex／json 把字串拆成結構化欄位
   └──────────────────┘    （endpoint、status、latency_ms…）
            │  結構化 record
            ▼
   ┌──────────────────┐
   │  filter（Lua）   │  就地轉換／聚合：抽欄位、改值、丟棄、
   └──────────────────┘    算視窗統計——你的招牌就在這一格
            │  加工後 record
            ▼
   ┌──────────────────┐
   │  buffer          │  記憶體或檔案系統暫存，背壓的緩衝帶
   └──────────────────┘    （滿了怎麼辦？這一格決定丟或擋）
            │  成批的資料
            ▼
   ┌──────────────────┐
   │  output（S3）    │  攢夠一批就上傳，寫進 bucket 給 Nexon
   └──────────────────┘
```

逐格拆：

**input（輸入）**——通常是 `tail` 外掛，盯著 log 檔或容器 stdout，每讀到一行就生出一筆 record。一筆 record = 一個時間戳 + 一個內容（一開始就是原始字串）。這裡第一個隱藏取捨是：input 讀得多快、buffer 撐不撐得住——這牽到背壓，下面 buffer 那格細講。

**parser（解析）**——把原始字串拆成結構化欄位。access log 通常是固定格式（或 JSON），你用 regex 或 json parser 把 `endpoint`、`status`、`latency_ms`、`timestamp` 這些欄位拆出來。**這一步是「從 log 算 metric」的第一個脆弱點**：如果某些 log 行格式跟你的 regex 對不上（換了 log 格式、某條路徑印了不一樣的格式、有人塞了一個含特殊字元的 path），parser 會解析失敗，那行 log 要嘛被丟、要嘛欄位是空的——而你的 metric 就少算了這些請求。解析失敗是靜默的；你不會收到「有 3% 的 log 沒解析成功」的告警，除非你刻意去數解析失敗的計數。

**filter（過濾／轉換）**——你的主場。FluentBit 的 **Lua filter（config 名 `lua`，2026-06 確認仍受支援、無棄用標記）** 讓你寫一段 Lua 函式，對每筆 record 做任意處理：抽出你要的欄位、改值、丟掉不要的、甚至做視窗聚合。為什麼用 Lua 而不是內建的其他 filter？因為內建 filter（grep、modify、record_modifier）做的是固定動作（比對、改欄位名），而你要做的是**有邏輯的就地計算**——把 latency 字串轉成數字、按 endpoint 分組、在一個時間視窗裡累積、算出統計量。這種「需要程式邏輯」的就地加工，Lua 是 FluentBit 給你的逃生口。下一節專講為什麼 Lua filter 是這條管線的關鍵設計。

**buffer（緩衝）**——record 加工完不會一筆一筆立刻寫 S3（那會把 S3 打爆、成本爆炸），而是先攢在 buffer 裡，攢夠一批或攢夠久才一次送。buffer 是 pipeline 的**減震帶**：input 進得快、output（S3 上傳）慢的時候，差額就堆在 buffer 裡。這一格決定了「FluentBit 滿了會怎樣」——丟資料還是擋上游，下面「故障模式與防禦」細講（完整的背壓工程機制留 ch14）。

**output（輸出）**——`out_s3` 外掛把攢好的批次寫進 S3。FluentBit 的 S3 output 預設用 **multipart upload**（每攢 5 MiB 上傳一個 part），由 `total_file_size`、`upload_chunk_size`、`upload_timeout` 三個參數決定「什麼時候真的把檔案推出去」：攢夠大小就上傳，或者就算沒攢夠、只要在本地待超過 `upload_timeout` 也會送（避免資料卡在邊緣太久）。這個「大小 OR 時間，先到先送」的觸發邏輯，正是下面要算的 worked example 的關鍵——它決定了 Nexon 看到的資料有多新、批次有多大。

### 為什麼用 Lua filter：邊緣就地轉換，不把原料全送下游

把這條管線的核心決定講白：**你選擇在邊緣（Lua filter）就把 log 嚼成 metric，只把結論送下游，而不是把原始 log 整包推給 Nexon 讓他們去算**。

FluentBit 的 Lua filter 介面長這樣（示意，追邏輯用，不要求可執行）。它有兩種 callback 原型，FluentBit 依參數個數自動判斷用哪種：

```lua
-- 經典模式：3 個參數
-- tag = 這筆 record 的標籤，ts = 時間戳，record = 結構化欄位的 table
function extract_latency(tag, ts, record)
    local latency = tonumber(record["latency_ms"])
    if latency == nil then
        -- 解析不出 latency：回傳 -1 代表丟棄這筆
        return -1, ts, record
    end
    -- 回傳 code 控制後續：
    --   -1 = 丟棄這筆 record
    --    0 = 不改動，原樣放行
    --    1 或 2 = 用新的 record 取代原本的
    local out = {
        endpoint = record["endpoint"],
        status   = record["status"],
        latency_ms = latency,
    }
    return 1, ts, out
end
```

（FluentBit 也有 5 參數的 metadata-aware 模式：`(tag, ts, group, metadata, record)`，多帶 OpenTelemetry 的 resource/scope metadata，v4.0.4+ 加入——但你那條管線用經典 3 參數就夠了。）

選 Lua 就地處理的好處，逐條算清楚：

- **省下游頻寬與儲存**：每秒幾千行原始 access log；整包送下游，Nexon 要收、要存、要算。邊緣 Lua 一過濾一聚合，往外送的可能只剩每分鐘幾筆——資料量差好幾個數量級。
- **不把計算外包成跨組織依賴**：把原始 log 推給 Nexon 去算，等於「我的 API 健不健康」這個問題用別人的邏輯算。邊緣自己算，metric 的定義（什麼算一個請求、p95 怎麼定）握在你手裡，送出去的是你背書過的結論。
- **就地嚼，原料不必落地**：原始 log 裡的使用者識別、內部路徑不必外送；Lua 抽出要的欄位、其餘丟掉。

但邊緣聚合有一個代價，而且它就是這章的主軸——**你在邊緣聚合掉的東西，就再也合不回來了**。如果你在 Lua filter 裡就把每台機器、每分鐘的 p95 算出來、只送那個數字，你就把原始延遲分布丟在了邊緣。下游再也無法把多台、多視窗的數字正確合成一個整體 p95。這不是 bug，是邊緣聚合的本質取捨：**送結論很省，但結論一旦是百分位數，就不能再被聚合**。下一節正面拆這個陷阱。

## 從 log 算 metric 的四個根本問題

這條路有四個結構性問題。它們不是「你當年沒做好」，是「這條路本身就帶著」——挖穿它們，你就懂了為什麼「從 log 算 metric」是一條「常見但有陷阱」的路。

### 問題一：取樣與遺漏——log 掉一行，metric 就少一個樣本

前面說過：從 log 反推的 metric，準確度被 log 的完整度封頂。具體有兩個漏點：

- **遺漏**：log 在高負載下被丟。FluentBit buffer 滿了（mem_buf_limit 到頂、input 被暫停）、磁碟壓力、log 輪替（rotation）時 FluentBit 正好被暫停沒讀到——這些都讓 log 行直接消失。每消失一行，你的 latency metric 就少了一個樣本。
- **取樣**：有些團隊為了省成本，乾脆只收 10% 的 log（取樣）。如果你的 metric 是從這 10% 算的，那它就是基於十分之一樣本的估計。

取樣對「平均值」這種統計量影響相對溫和（10% 樣本算平均，期望值還是對的，只是抖動大一點）。但對**尾端百分位數（p99、p999）影響巨大**——因為尾端本來就是稀有事件，10% 取樣會把稀有事件再砍掉九成，p99 的估計會嚴重不穩。這章後面的 worked example 會把這個偏差算給你看。

### 問題二：百分位數不能合併——這章最重要的陷阱

這是「從 log 算 metric」最容易悄悄出錯、而且**完全不會報錯**的地方。

百分位數（p50、p95、p99）有一個違反直覺的數學性質：**它們不是可合併（mergeable）的統計量**。具體說：

- 你**不能**把三台機器各自的 p95 平均起來得到整個機群的 p95。
- 你**不能**把這一分鐘的 p95 和下一分鐘的 p95 平均起來得到這兩分鐘的 p95。

為什麼？因為 p95 是「分布裡第 95 百分位的那個值」，它取決於**整個分布的形狀**。機器 A 處理的全是快請求（p95 = 50ms），機器 B 卡住了全是慢請求（p95 = 2000ms），這兩個 p95 平均 = 1025ms 是一個**完全沒有意義的數字**——真正的機群 p95 取決於兩台各處理了多少請求、兩堆延遲混在一起後第 95 百分位落在哪，跟「1025」毫無關係。

對照一下：**可合併的統計量**（counter、sum、min、max）就沒這個問題。兩台機器各自數的請求數，加起來就是總請求數；各自的 max，取大的那個就是全域 max。這些量「自帶結合律」。但百分位數沒有——你必須**保留原始分布**（或一個可合併的近似結構：histogram、t-digest、HdrHistogram）才能正確合併。

這對你那條 pipeline 意味著一個必須當場做對的決定：

> **如果你在 Lua filter 裡就把每台、每分鐘的 p95 算成一個數字寫進 S3，然後 Nexon 把這些數字平均——那 Nexon 看到的「p95」是錯的，而且永遠不會有人收到錯誤訊息。**

正確的做法有兩條，各有取捨：

1. **邊緣不算終極 p95，只送可合併的中間結構**：在 Lua filter 裡，每個視窗不要算 p95，而是攢一個 histogram（把 latency 落進預設的 bucket，例如 0–10ms、10–50ms、50–100ms…，每個 bucket 數個數）或一個 t-digest。histogram 與 t-digest 是**可合併的**：兩個 histogram 對應 bucket 相加，就是合併後的 histogram；t-digest 也能直接相加。下游（Nexon）把多台、多視窗的 histogram 合起來，最後才從合併後的分布算 p95。這條路正確，代價是送的資料比「一個數字」大（一個 histogram 是幾十個 bucket 的計數）。
2. **把原始 latency 全送下游，p95 在中心算**：邊緣完全不聚合，把每個請求的 latency 都送出去，Nexon 那邊有完整分布、想算 p95 還是 p99 都行。這條最準，但**最貴**——資料量沒省到，等於放棄了邊緣聚合的全部好處。

這就是「聚合在邊緣 vs 在中心」的取捨的真身：**邊緣聚合省頻寬，但只能聚合可合併的量；一旦你要的是百分位數，你要嘛在邊緣送 histogram（可合併的近似），要嘛把原料送到中心算**。「在邊緣把 p95 算成一個數字送出去」是這三條裡唯一錯的——而它偏偏是最直覺、最容易手滑寫出來的那條。

> **我以為 vs 實際**：
> **我以為**：p95 就是個數字，各台算好、各視窗算好，平均一下就是整體 p95。
> **實際**：百分位數不可合併。要正確得到跨機器、跨視窗的 p95，邊緣只能送可合併的結構（histogram / t-digest）或送原始分布，絕不能送「已經算好的 p95」再去平均。

### 問題三：cardinality（基數）爆炸——預告

metric 一旦要按維度拆，維度組合數就是你要維護的時間序列數。10 個 endpoint × 5 種 status = 50 條序列還好；但一旦有人說「也按 user 拆」，500K 使用者 × 50 = 2,500 萬條序列，metric 系統成本失控、查詢變慢。你那條 pipeline 在 Lua filter 裡決定「聚合到哪些維度」時，就在隱性控制 cardinality——拆得越細下游越貴。深掘（為什麼高基數對 metric 系統致命、怎麼設計維度）留 ch15；這裡只讓你看見它藏在哪一格（filter 的分組鍵）。

### 問題四：時間視窗對齊——你算的是哪一分鐘的 p95

從 log 算 metric 要做「視窗聚合」（每分鐘算一次 p95），於是你得回答：**一筆 record 算進哪個視窗？** 用 log 裡記的事件時間（event time，請求真正發生的時刻），還是用 FluentBit 處理到它的時間（processing time）？

兩者會差很多，因為 log 從產生到被 FluentBit 讀到、處理到，中間有延遲（buffer 排隊、批次攢著）。如果你用 processing time 分視窗，那一批因為背壓延遲了 3 分鐘才被處理的 log，會全部被算進「現在這一分鐘」——讓現在這一分鐘看起來請求暴增、讓那 3 分鐘前的真實尖峰被抹平。如果你用 event time 分視窗，視窗才對得上真實發生的時間，但你得處理「遲到的 record」（一筆屬於 10:00 視窗的 log 在 10:05 才到，那個視窗早就算完送走了，這筆要補嗎？丟嗎？）。

你那條 pipeline 在 Lua filter 裡用哪個時間分視窗，決定了 Nexon 看到的尖峰是不是對得上真實時間。這是流式聚合的經典難題（event time vs processing time、watermark、遲到資料），完整理論不在本書範圍，但你要知道：**「每分鐘的 p95」這句話裡，「每分鐘」是用哪個時鐘切的，是一個你當年隱性選過的取捨**（時間與時鐘為什麼是分散式難題，見 ch13）。

## 為什麼輸出 S3，而不是直接進 metric 系統

最後一個取捨：你的 output 是 S3，Nexon 去 S3 讀。為什麼不直接把 metric 推進一個 metric 系統（CloudWatch、Prometheus、Datadog）？

把選項並排，每個輸出目標在「給 Nexon 當資料源」這件事上的位置：

| 輸出目標 | 優點 | 輸在哪 |
|---|---|---|
| **S3（你選的）** | 跨組織交接的中性介面；Nexon 用自己的工具讀、自己的節奏拉；耐久、便宜、無耦合；你只負責寫對格式 | 不是即時的（攢批才上傳，有 `upload_timeout` 的延遲）；Nexon 要自己建查詢層才能用 |
| **直接進你的 CloudWatch/Prometheus** | 即時、可告警、有現成 dashboard | metric 在你的帳號裡，Nexon 看不到，要再開跨帳號授權；耦合到你的 metric 系統 |
| **直接進 Nexon 的 metric 系統** | Nexon 直接能用 | 你得綁死 Nexon 用哪套系統、拿到他們的寫入權限——強耦合，他們換系統你就得改 |

S3 在這個跨組織場景裡是對的，理由不是「S3 多好」，而是**S3 是一個誰都能讀、誰都不擁有對方系統的中性交接點**。你寫檔案、Nexon 讀檔案，兩邊各自用自己的工具，沒有任何一方被綁進對方的技術選型。代價是延遲（批次、非即時）和「Nexon 要自己建讀取／查詢層」——但對「定期把監控資料交給發行商」這個需求，這個代價是划算的。如果這 metric 是你自己要即時告警用的，S3 就是錯的選擇（你會想要直接進一個能即時 query、能設告警的 metric 系統）。**輸出目標的選擇取決於「誰要用、用得多即時、誰擁有讀取端」**，不是哪個技術更潮。

### 為什麼不直接用 CloudWatch metric filter

這是最該被問的對照：AWS 本來就有 **CloudWatch Logs metric filter**——你把 log 送進 CloudWatch Logs，設一個 filter pattern，CloudWatch 自動從符合的 log 行抽出數值、變成 metric。聽起來正好就是你手刻 FluentBit + Lua 在做的事，為什麼不直接用它、省下自建一條 pipeline 的工？

把 CloudWatch metric filter 的真實限制攤開（這些是它「會怎麼騙你」的地方）：

- **百分位數的限制**：CloudWatch 從 metric filter 抽出的數值能給你 min/max/average/百分位統計——但有一個關鍵限制：**只要該 metric 的值可能為負，百分位統計就不可用**。latency 不會負，這條對你影響小；但這暴露了 CloudWatch metric filter 的百分位是「它幫你算」的黑箱，你無法控制它怎麼算、怎麼跨維度合併。
- **不回溯**：metric filter **只對建立之後的 log 生效**，不會回頭處理舊 log。設錯了、漏設了一個維度，過去的資料補不回來。
- **數量上限**：一個 log group 最多 **100 個 metric filter**、含 regex 的 filter pattern 每個 log group 最多 5 個。維度一多就撞牆。
- **資料落在 CloudWatch、給不了 Nexon**：這是對你那個場景的致命傷——metric filter 算出來的 metric 在**你的 CloudWatch 帳號裡**，Nexon 拿不到。要給 Nexon，你還是得想辦法把它導出去（export、跨帳號），又繞回「怎麼交接給外部組織」的問題。而 S3 一開始就是那個交接點。

（補一句現況：FluentBit 現在也支援用 **Embedded Metric Format（EMF）** 直接把 metric 送進 CloudWatch，2026-06——但那是「FluentBit → CloudWatch」這條路，跟「用 CloudWatch 自己的 log metric filter」是兩回事，而且一樣有「資料落在你帳號、給不了 Nexon」的問題。）

所以你當年自建 FluentBit + Lua 而不用 CloudWatch metric filter，是對的——但理由要說準：**不是因為 CloudWatch metric filter 做不到從 log 抽 latency（它做得到），而是因為（1）你要把結果交給外部的 Nexon，S3 是中性交接點而 CloudWatch metric 困在你帳號裡；（2）你要對「怎麼聚合、聚合成什麼」有完全的控制權，Lua 給你任意邏輯，metric filter 只給你它預設的那幾種統計**。掌控權 + 跨組織交接，這兩條是自建的真正理由，不是「CloudWatch 不行」。

## 故障模式與防禦

這條 pipeline 會怎麼壞、壞了長什麼樣、怎麼防。每一個都綁你那條 NeoBards 的 FluentBit + S3 管線。

| 故障 | 壞了長什麼樣（徵兆） | 怎麼防 / 當年的代價 |
|---|---|---|
| **buffer 滿了、input 被暫停、log 被丟** | Nexon 看到的請求數在尖峰時段不升反「平」或下凹（樣本被丟）；FluentBit 日誌出現 `[input] tail.1 paused (mem buf overlimit)` | FluentBit 預設用記憶體 buffer，`mem_buf_limit` 到頂時 input 被**暫停**——暫停期間若 log 檔輪替，那段 log 直接消失、永久丟。防禦：改用**檔案系統 buffer（`storage.type filesystem`）**，到達 mem 上限時資料寫進磁碟 chunk 而非暫停 input，換來耐久（重啟也不丟）。代價是磁碟 I/O 與空間。**這是「丟還是擋」的核心抉擇**——背壓的完整工程機制（有界佇列、阻塞、丟棄三選一）留 ch14，這裡你要記住的是：**預設行為（記憶體 buffer + 暫停）在尖峰會靜默丟 log，而尖峰正是你最需要 metric 的時候**。 |
| **parser 解析失敗，metric 靜默少算** | p95 看起來「莫名其妙地好」（慢請求那行 log 格式特殊、被解析失敗丟掉了，反而拉低了 p95）；解析失敗計數無人看 | 換了 log 格式、某條路徑印不一樣的格式、path 含特殊字元——regex 對不上就解析失敗。防禦：**為「解析失敗」本身埋一個 counter**（解析失敗也是一筆要被觀測的事件），失敗率超標就告警；Lua filter 裡對 `tonumber(latency) == nil` 的情況不要默默丟，要計數。**靜默遺漏是這條路最陰險的故障——它讓 metric 變好看，而不是變難看。** |
| **百分位數被跨機器／跨視窗平均，得到無意義的數字** | 「p95」數字看起來很合理、很平滑，但跟真實的尾延遲對不上；事故時 p95 沒反映出來 | 邊緣算好 p95、下游平均（見前文）。防禦：邊緣**不送終極 p95，送可合併的 histogram / t-digest**，下游合併後才算 p95；或把原始 latency 送中心算。**這個故障最危險的地方是它從不報錯**——你會一直相信一個假的 p95，直到某次事故對不上才發現。 |
| **S3 上傳延遲／批次太大，Nexon 看到的資料嚴重落後** | Nexon 抱怨「你們的監控資料延遲半小時」 | `out_s3` 是「攢夠 `total_file_size` 大小 OR 超過 `upload_timeout` 時間」才上傳。若兩個都設太大、且流量不夠攢滿，資料會卡在邊緣很久才上去。防禦：把 `upload_timeout` 設成 Nexon 能接受的新鮮度上限（例如 5 分鐘），讓「時間」這條觸發條件兜底，不要讓資料無限等攢滿。 |
| **單點失效：這條 pipeline 本身掛了，沒人知道** | metric 直接斷流，但因為「沒有 metric」不會觸發「metric 異常」的告警（你只告警 metric 的值，沒告警 metric 的存在） | FluentBit 行程掛了、S3 寫入權限過期、bucket policy 改了——整條管線是觀測你服務的眼睛，但**這隻眼睛自己壞了誰來觀測？** 防禦：對 pipeline 本身做**存活監控**（heartbeat / dead man's switch：S3 bucket 超過 N 分鐘沒有新檔案就告警），別只監控 metric 的值、要監控 metric 的「有沒有在來」。**觀測系統自己也需要被觀測**——這是觀測這一軸最容易留的盲點。 |

## 紙上推演

### 推演一：手追一條 access log 從原始字串到 S3 的完整變形 **[20 分鐘] ★★**

給定一行原始 access log：

```
2026-06-21T10:23:45.120Z GET /api/guild/5821/rewards 200 87ms
```

請手追它走過 input → parser → Lua filter → buffer → S3 的完整變形，並在每一步寫出 record 變成什麼樣子。然後說明：如果這條管線的目標是「每分鐘、每 endpoint 的 p95 latency」，Lua filter 在這一格**到底該輸出什麼**才能讓下游正確算出跨機器的 p95？

### 推演二：估 log 取樣 10% 對 p99 估計的偏差 **[20 分鐘] ★★★**

假設你某 endpoint 一分鐘有 10,000 個請求，延遲分布是：9,900 個落在 50–100ms，100 個是慢請求落在 800–1200ms（p99 大約落在 800ms 那一帶）。現在因為成本，log 只取樣 10%（隨機留 1,000 個請求）。請估：取樣後你還剩幾個慢請求樣本？用這 1,000 個樣本算出的 p99 會有多不穩（為什麼 p99 的估計在取樣下抖得比平均值厲害得多）？這個偏差對「用這個 p99 判斷服務健康」意味著什麼？

### 推演三：找出這條 pipeline 的單點失效 **[15 分鐘] ★★**

列出這條 FluentBit + Lua + S3 pipeline 從 log 產生到 Nexon 讀到，**至少四個**會讓 metric 悄悄變錯（而不是直接報錯）的環節。對每一個，說明：它壞了之後，Nexon 看到的數字會偏高還是偏低、變好看還是變難看？哪些故障會讓 metric「看起來變好」（因此最危險，因為沒人會去查一個變好的指標）？

### 推演解答

**推演一**：逐步變形——

1. **input（tail）**：讀到這一行，生出一筆 record：`{ts: <讀到的時間>, log: "2026-06-21T10:23:45.120Z GET /api/guild/5821/rewards 200 87ms"}`。此刻 `log` 還是整串原始字串。
2. **parser**：用 regex 把字串拆成欄位：`{timestamp: "2026-06-21T10:23:45.120Z", method: "GET", endpoint: "/api/guild/5821/rewards", status: 200, latency_ms: 87}`。**注意 `endpoint` 裡有個 guild ID `5821`**——如果你不處理，每個 guild 都是一個不同的 endpoint 值，cardinality 會爆（~5,000 公會 × 各種路徑）。你會想在這裡或下一步把 `5821` 正規化成 `:id`，變成 `/api/guild/:id/rewards`。
3. **Lua filter**：抽出 `endpoint`（正規化後）、`status`、`latency_ms`。**關鍵問題：該輸出什麼？** 如果你在這裡就試圖算 p95，你會發現你算不了——一筆 record 只有一個 latency，p95 要一整個視窗的分布。所以正確做法是：Lua filter **不在這格算終極 p95**。它有兩個正確選項：
   - (a) 直接放行帶 `latency_ms` 的乾淨 record，把聚合完全交給下游（最準、最貴）；
   - (b) 在 Lua 裡維護一個「per-(endpoint, 分鐘) 的 histogram」狀態，把這筆 87ms 落進對應 bucket（例如 50–100ms bucket +1），每分鐘吐出一筆 histogram record。下游把多台的同一分鐘 histogram 相加，再算 p95——**因為 histogram 可合併，這樣算出來的跨機器 p95 才是對的**。
   - **錯誤選項**：在 Lua 裡每台、每分鐘算一個 p95 數字吐出去——下游一平均就錯。
4. **buffer**：histogram record（或乾淨 record）攢進 buffer，等攢夠批次或 `upload_timeout`。
5. **S3**：攢夠後 multipart 上傳成一個檔案進 bucket。Nexon 讀這些檔案，把同一分鐘、跨所有機器的 histogram 合併，最後算出整個機群該 endpoint 該分鐘的 p95。

**這題的重點**：最直覺的「在 Lua 裡算 p95 送出去」是錯的；正確答案是「邊緣只送可合併的東西（histogram 或原始 latency），p95 留到合併後才算」。

**推演二**：取樣 10% 對 p99 的偏差——

原始：10,000 請求，100 個慢請求（1%，定義了 p99 那一帶）。取樣 10% 隨機留 1,000 個，**期望只剩 ~10 個慢請求樣本**（100 × 10%）。

問題出在：你現在要用這 1,000 個樣本估 p99，也就是估「第 990 名的值」——而你的慢請求樣本只有 ~10 個，p99 那條線正好落在這 ~10 個樣本裡。**10 個樣本去定一條百分位線，抖動極大**：這 10 個是隨機抽的，可能抽到 7 個或 13 個（卜瓦松抖動，標準差約 √10 ≈ 3.2，相對誤差 ~32%），抽到的那幾個慢請求具體是 850ms 還是 1100ms，p99 估計就跟著大幅跳動。對比平均值——平均值用全部 1,000 個樣本算，每個樣本都貢獻，10% 取樣下平均值期望不變、抖動小（大數法則）。

**為什麼 p99 比平均抖得多**：平均值是「所有樣本的事」，尾端百分位是「極少數稀有樣本的事」。取樣對「多數」的統計（平均、p50）幾乎無傷，對「稀有事件」的統計（p99、p999）是毀滅性的——因為它把稀有事件的樣本數再砍一個數量級，少到不足以穩定估計。

**意味著**：用 10% 取樣的 log 算出來的 p99 不可信，可能某分鐘顯示 850ms、下一分鐘 1150ms，純粹是取樣抖動不是真實變化。如果你拿這個 p99 設告警，你會被取樣噪聲不斷誤觸發（或漏觸發）。**結論**：要可信的尾延遲，要嘛別取樣（尾端不要丟），要嘛在邊緣保留完整 histogram（histogram 不丟尾端樣本、可合併），絕不要「取樣 + 從取樣算 p99」。

**推演三**：靜默變錯的單點 / 環節（至少四個）——

1. **parser 解析失敗丟掉特殊格式的慢請求** → metric **偏低、變好看**（慢請求被丟，p95/p99 下降）。最危險，因為指標「變好」沒人查。
2. **buffer 滿、input 暫停、尖峰 log 被丟** → 請求數**偏低**、尾延遲**偏低變好看**（尖峰那批慢請求最可能在 buffer 壓力下被丟）。同樣是「事故時指標反而變好」的陷阱。
3. **邊緣算 p95 後下游平均** → 數字**無意義**，可能偏高也可能偏低，但通常是「平滑得不真實」——真實尾延遲尖峰被平均抹平，**看起來變好**。
4. **時間視窗用 processing time、背壓延遲的 log 被算進錯的分鐘** → 尖峰被搬到後面的視窗、真實尖峰那分鐘**看起來變好**。
5. **pipeline 整條掛掉但只告警 metric 的值不告警 metric 的存在** → 沒有數字 = 沒有「異常的數字」= 不告警，事故全程無人知。

**哪些「看起來變好」**：1、2、3、4 都會讓指標變好看——這正是「從 log 算 metric」最陰險的共性：**它的失敗模式偏向樂觀（丟掉的往往是壞樣本），讓你誤以為系統健康**。防禦的第一原則因此是：**監控你的觀測管線本身**（解析失敗率、input 暫停事件、pipeline 存活 heartbeat），別只看它吐出來的數字。

## 自我檢核

口頭自答，講得出來才算過關：

1. 「從 log 反推 metric」相對於「應用程式直接埋點上報 metric」，多了哪一個結構性弱點？為什麼這個弱點在系統尖峰時最致命？
2. 為什麼 p95 不能跨機器平均、不能跨視窗平均？要正確得到跨機器的 p95，邊緣該送什麼出去（而不是送什麼）？
3. FluentBit pipeline 五階段（input → parser → filter → buffer → output）各在幹嘛？哪一階段是你那條管線的招牌、為什麼要用 Lua 而不是內建 filter？
4. FluentBit buffer 滿了的「預設行為」是什麼？它在尖峰會悄悄做什麼壞事？換成檔案系統 buffer 換來什麼、代價是什麼？（背壓機制細節指哪一章？）
5. 你當年選自建 FluentBit + Lua 而不用 CloudWatch metric filter——正確的理由是哪兩條？（不是「CloudWatch 做不到」這條）
6. 為什麼輸出是 S3 而不是直接進一個 metric 系統？這個選擇在什麼情況下會變成錯的？
7. 取樣 10% 對「平均 latency」和對「p99」的影響為什麼差這麼多？
8. 「從 log 算 metric」的失敗模式為什麼偏向「讓指標看起來變好」？這對你的告警設計意味著什麼？

## 延伸閱讀

- **Fluent Bit 官方手冊 — Lua filter**（https://docs.fluentbit.io/manual/data-pipeline/filters/lua）：你那段 Lua filter 的權威介面。讀「callback prototypes」（3 參數經典模式 vs 5 參數 metadata-aware）與回傳 code 的語意（-1 丟棄、0 原樣、1/2 取代）——對應本章 worked example。
- **Fluent Bit 官方手冊 — Amazon S3 output**（https://docs.fluentbit.io/manual/data-pipeline/outputs/s3）：`out_s3` 的 multipart 上傳、`total_file_size` / `upload_chunk_size` / `upload_timeout` 觸發邏輯。讀「buffering」段，理解「大小 OR 時間先到先送」如何決定 Nexon 看到資料的新鮮度。
- **Fluent Bit 官方手冊 — Buffering & backpressure**（https://docs.fluentbit.io/manual/administration/buffering-and-storage、https://docs.fluentbit.io/manual/administration/backpressure）：`mem_buf_limit`、input 暫停、檔案系統 buffer。讀懂「滿了會暫停 input 並可能丟資料」——本章「丟還是擋」抉擇的權威來源（完整背壓工程見本書 ch14）。
- **Fluent Bit 官方手冊 — Fluentd and Fluent Bit**（https://docs.fluentbit.io/manual/about/fluentd-and-fluent-bit）：C vs Ruby、內建外掛 vs gem 生態、兩者皆 CNCF graduated 的分工。理解你當年為何選 FluentBit 當邊緣代理。
- **AWS — Creating metrics from log events using filters**（https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/MonitoringLogData.html）：CloudWatch metric filter 能做與不能做。讀「百分位限制」「不回溯」「每 log group 100 個 filter 上限」——本章「為什麼不直接用 CloudWatch」對照的事實依據。
- **「你不能平均百分位數」**（概念，可搜 "you cannot average percentiles" / t-digest / HdrHistogram）：本章最重要陷阱的數學背景。理解為什麼要用可合併的 histogram / t-digest 才能正確跨節點合 p95——這是邊緣 vs 中心聚合取捨的根。

---

### 本系統五軸體檢

| 軸 | FluentBit + Lua + S3 metric pipeline 的答案與代價 |
|---|---|
| **交付** | log 行可能在 buffer 壓力下被丟（at-most-once 傾向）；丟一行 = metric 少一個樣本。代價：metric 準確度被 log 完整度封頂，尖峰最不準。 |
| **持久** | 預設記憶體 buffer，行程重啟 / input 暫停期間 log 輪替即丟；改檔案系統 buffer 才耐久。代價：耐久換磁碟 I/O。 |
| **分區** | 跨多台邊緣各自聚合，若送已算好的 p95 則無法正確合併（百分位不可合併）；須送 histogram/原始分布。代價：可合併性 vs 頻寬。 |
| **並發** | 各邊緣獨立處理自己的 log，無共享狀態、無鎖；但這也意味著跨機器的全域統計必須在下游靠可合併結構重建。 |
| **觀測** | 這條管線**本身**就是觀測工具——但它自己壞了（行程掛、解析失敗、buffer 丟）多半靜默且讓指標「變好看」。代價：必須對觀測管線本身加存活監控與解析失敗計數，否則盲點最大。 |
