# ch17 — 業界案例研究：誰在用、用在哪、值不值

> **本章解決什麼問題**：Part I 到 Part V 把你從「測試蓋不住」一路帶到機器證明，但有個問題從 ch01 就懸著：這套東西在工業界到底是不是玩具？本章把證據攤開——AWS、MongoDB、Azure Cosmos DB、CockroachDB 四組查證過的案例，其中包含一份罕見而珍貴的失敗報告——然後從案例裡萃取決策框架：什麼問題值得形式化、成本誠實算在哪、spec 寫完之後誰來養。最後把框架按在你自己的結算 pipeline 上，逐判準走完、給出有數字的結論。ch18 接著把整個方法版圖收成一張地圖。

你現在的位置：

```text
┌──────────────────────────────────────────────────────────────────┐
│ Part I    為什麼                                                 │
│   ch01 測試的極限 → ch02 狀態機                                  │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part II   數學地基                                               │
│   ch03 邏輯 → ch04 集合 → ch05 歸納                              │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part III  TLA+ 與時序邏輯                                        │
│   ch06 動作邏輯 → ch07 時序邏輯 → ch08 完整 spec → ch09 TLC 原理 │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part IV   協議精讀                                               │
│   ch10 互斥 → ch11 2PC → ch12 Paxos → ch13 Raft                  │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part V    證明                                                   │
│   ch14 歸納不變量 → ch15 Refinement → ch16 機器證明              │
└─────────────────────────────────┴────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────┬────────────────────────────────┐
│ Part VI   實務                                                   │  ← 你在這裡
│   ch17 業界案例 → ch18 方法地圖                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 從你已知的出發

你做過技術評估。引入新的 message broker、換一顆資料庫、決定要不要自研一個元件之前，你翻官方文件、找 production 案例、潛水論壇討論串、估導入成本，最後寫一頁「採用建議」。你也早就學會這門手藝的潛規則：vendor 部落格的成功案例要打對折，「某大廠在用」不等於「適合我們」，真正值錢的是**失敗報告**與**成本數字**——而這兩樣最稀有，因為沒人愛寫自己的失敗，寫了也沒流量。倖存者偏差讓你只看得到講台上的贏家。

本章做的就是一次你熟悉的技術評估，標的換成形式化方法。評估紀律也照舊：每個案例標注查證狀態與時點；數字綁年份；唯一一份誠實的失敗報告（MongoDB）被當成最有價值的證據細讀。還有一條本章特有的紀律——**只列查證過的案例**。網路上流傳的 TLA+ 採用者名單很長，但其中不少是傳聞滾傳聞；本書未能以原始來源確認的名字，一個都不會出現。寧缺勿錯。

另一件值得先說的事：接下來的主角你全都用過。你的結算 pipeline 跑在 SQS 上、檔案丟在 S3、表可能在 DynamoDB；你選型時評估過 MongoDB 與 CockroachDB 這類分散式資料庫。這些系統的核心協議被本書教的方法驗過——你每天其實都在消費這些驗證成果，只是發票上沒印。

最後，這個評估有個你以前沒有的優勢：讀完 Part I 到 V 的你已經付完學費。「值不值得」的算式裡，學習成本那一項對你而言已經攤提掉了。這會實質改變本章結尾那個 ROI 評估的結論。

## AWS：從一篇論文到一個工具箱

### 2011–2015：把「玩具」標籤撕掉的那篇論文

ch01 用 AWS 的證詞當開場白；現在把整份證據攤開。論文是 “How Amazon Web Services Uses Formal Methods”，發表於 *Communications of the ACM* Vol. 58 No. 4（2015 年 4 月），作者 Chris Newcombe、Tim Rath、Fan Zhang、Bogdan Munteanu、Marc Brooker、Michael Deardeuff——六位都是一線工程師，不是研究部門。開頭第一句話就把時間錨釘下：

> Since 2011, engineers at Amazon Web Services (AWS) have used formal specification and model checking to help solve difficult design problems in critical systems.

論文的核心證據是一張表（原文 Table 1，行數不含註解），值得整張搬過來：

| 系統 | 元件 | 規格規模 | 成果（原文意旨） |
|---|---|---|---|
| S3 | 容錯的低階網路演算法 | 804 行 PlusCal | 找到 2 個 bug，後續在提議的最佳化中又找到更多 |
| S3 | 資料的背景重分布 | 645 行 PlusCal | 找到 1 個 bug，又在第一版修法中找到另 1 個 |
| DynamoDB | 複寫與群組成員系統 | 939 行 TLA+ | 找到 3 個 bug，其中需要長達 35 步的 trace |
| EBS | Volume 管理 | 102 行 PlusCal | 找到 3 個 bug |
| 內部分散式鎖管理服務 | Lock-free 資料結構 | 223 行 PlusCal | 提升信心；未找到某個 liveness bug——因為沒有檢查 liveness |
| 內部分散式鎖管理服務 | 容錯的複寫與重組態演算法 | 318 行 TLA+ | 找到 1 個 bug，並驗證了一個激進的最佳化 |

三個讀法。

**第一，看行數。**六份 spec 全部落在 102～939 行之間。對照這些系統動輒數十萬行的實作，spec 不是第二份實作，是設計的 X 光片：把「規則少、交錯多」的協議核心抽出來照。這個尺寸感是後面決策框架的第一個判準。

**第二，看那個 35 步。**最深的 bug 出自 DynamoDB 的複寫與群組成員系統（注意：是 DynamoDB，不是 S3——這是被轉述最常弄錯的一格）。原文的措辭值得逐字讀：

> The shortest error trace exhibiting the bug included 35 high-level steps. … The bug had passed unnoticed through extensive design reviews, code reviews, and testing.

35 步的高階交錯，意味著設計審查、code review、測試三道防線全部翻過去了——這正是 ch01「調度不可控＋狀態空間指數」論點的工業界對照組。而且原文特別反駁了「這麼複雜的事件組合不會真的發生」：AWS 工程師在歷史上觀測過的事件組合，複雜度不輸給能觸發這個 bug 的那些。Murphy 在超大規模下不是定律，是日常。

**第三，看 S3 那行的前傳。**S3 團隊在用 TLA+ 之前，原本打算寫一支 Java 程式暴力窮舉可能的執行——原文說那本質上是 “a hard-wired form of model checking”。工程師被併發 bug 逼急了，會本能地自製模型檢查器；TLA+ 讓他們把這個輪子省下來。作者之一 Fan Zhang 從零開始，兩週內寫出兩版 spec，論文還記了一筆她「用 PlusCal 比用 TLA+ 更有生產力」——工具的人因工程是真議題，不是細節。

組織面的證詞同樣綁著 2015 這個時點：

> At the time of this writing, seven Amazon teams have used TLA+, all finding value in doing so. … Executive management actively encourages teams to write TLA+ specs for new features and other significant design changes. In annual planning, managers now allocate engineering time to TLA+.

「七個團隊」是 2015 年論文寫作時點的數字，引用時必須帶年份——十年後拿它說「Amazon 只有七個團隊在用」是讀錯，拿它說「現在有七個團隊」也是讀錯。學習曲線的證詞則是：從新進到 principal 等級的工程師都能從零學起，並在「兩到三週內拿到有用的結果」（get useful results in two to three weeks）。記住這個數字，成本帳會用到。

### 2015 之後：工具箱長大了

AWS 在 2025 年發了續篇：“Systems Correctness Practices at Amazon Web Services”（*CACM* Vol. 68 No. 6，2025 年 6 月；另有 ACM Queue 版）。先誠實交代：本書查證時點（2026-06）這篇的全文被擋在取用限制之後，多次嘗試只拿得到摘要與二手轉述（轉述指作者為 Marc Brooker 與 Ankush Desai——Brooker 正是 2015 年論文的作者之一）。所以以下細節，凡是只出自這篇文章的，一律用保守措辭；能找到第一手來源的，我直接去開了第一手來源。

文章的大方向（多個獨立轉述一致）：AWS 把正確性實務描述成一個**工具箱**，正式與半正式方法並陳——TLA+、P、程式碼級驗證、property-based testing、fuzzing、deterministic simulation、fault injection 等。TLA+ 仍在工具箱裡，但不再是唯一主角。其中兩件事查得到第一手來源：

**P language。**源自 Microsoft 的規格語言，約 2019 年起轉入 AWS 內部發展並維持開源（時點為二手轉述）。P 的官方案例頁（2026-06 開頁查證）寫得很直接：開發者把系統建模成 communicating state machines——「Amazon 開發者群體熟悉的心智模型」。最著名的應用是 S3 在 2020 年 12 月上線的 strong read-after-write consistency；官方原文：

> P was used for creating formal models of all the core distributed protocols involved in S3's strong consistency and checking that the system model satisfies the desired correctness guarantees.

S3 從最終一致性遷移到強一致性，是在不能停機的全球規模存儲上換引擎；這種「協議級、故障×併發、錯誤代價極高」的問題形狀，正是形式化方法的甜蜜點。對你這個天天寫 SQS consumer 的人，P 的「通訊狀態機」心智模型會比 TLA+ 的「全域狀態＋動作」更眼熟——兩者的取捨放在 ch18 講。

**Kani 與 Firecracker。**這是光譜的另一端：程式碼級驗證（見 ch16 的嚴謹度光譜）。Kani 是對 Rust 程式碼做模型檢查的開源工具；Firecracker（AWS Lambda 底下的 microVM）團隊用它驗證安全邊界。Kani 官方部落格的案例文（2026-06 開頁查證）給了難得的細節：驗證 I/O rate limiter 時找到 5 個 bug，包括一個捨入誤差讓 guest 可以超出配定頻寬上限約 0.01%；驗證 virtio 佇列時找到「不受信任的 guest 可以建出與 MMIO 區域部分重疊的佇列、讓 Firecracker 開機即崩潰」的 bug；最終 27 個驗證 harness 進了 CI 常駐執行。注意這些性質的形狀——「絕不 panic」「不越過頻寬上限」——是程式碼級的 invariant，跟 TLA+ 驗的設計級 invariant 是同一個概念在不同樓層的化身（見 ch02、ch14）。

**一個必須拆掉的地雷：ShardStore。**S3 的儲存節點 ShardStore 有一篇 SOSP 2021 論文 “Using Lightweight Formal Methods to Validate a Key-Value Storage Node in Amazon S3”（本書未開原文，論文存在經多來源交叉確認）。它用的是**輕量級形式化方法——Rust 參考模型加 property-based testing——不是 P，也不是 TLA+**。網路轉述極常把它算進 TLA+ 或 P 的戰績；引用 AWS 案例時，這是僅次於「35 步 bug 張冠李戴」的第二大誤植來源。

把 2015 與 2025 連起來讀，AWS 的軌跡很清楚：TLA+ 沒有退場，但它從「那個方法」變成「工具箱裡負責設計級驗證的那一格」；旁邊長出了更貼近工程師心智模型的 P、管程式碼樓層的 Kani 與輕量方法。對你的啟示不是「選哪個」，而是**分層**：設計級與程式碼級是兩個樓層的正確性，各有各的工具（ch18 的地圖會把這件事畫全）。

## MongoDB：一份誠實的失敗報告

成功案例看多了會麻痺，來看失敗的。“eXtreme Modelling in Practice”（A. Jesse Jiryu Davis、Max Hirschhorn、Judah Schvimer，*PVLDB* Vol. 13 No. 9，2020；2026-06 對照論文原文）報告了 MongoDB 的兩個案例：一個成、一個敗，而且作者把敗因解剖得毫不留情。這篇論文要解的問題正是形式化方法最大的軟肋——**spec 與實作的一致性**（conformance）：TLC 驗的是 spec，不是你的程式碼（見 ch09）；那怎麼確保程式碼真的長得像 spec？

### MBTC：二十人週買到一個教訓

第一個案例對 MongoDB Server 的複寫協議（協議本身與 Raft 同族，機制見 ch13）做 model-based trace-checking（MBTC）：在 C++ 實作裡埋 log，把真實執行的事件序列收集成 trace，再檢查每條 trace 是否為 TLA+ spec 允許的行為（行為＝狀態序列，見 ch02）。理論上這是把 spec 當成裁判、讓實作上場考試。

實際上是災難。兩位工程師投入 10 週，寫了 570 行 C++ 儀器化程式碼、改了 252 行 TLA+、外加 484 行 Python 後處理，結果 5 個手寫測試裡只有 1 個能產出通過檢查的 trace——其他 4 個的失敗不是抓到實作 bug，而是 trace 收集本身對不上 spec 的抽象層次。最痛的一段是「可見性與鎖」：要在「entry 進了 leader 的 oplog 之後、follower 能複製它之前」這個精確時刻記下事件，得跟資料庫內部的階層式鎖搏鬥——光這一項就吃掉約一個月。團隊最後取消專案，原文的結語冷靜得像驗屍報告：

> We canceled the MBTC project because we had achieved disappointingly little utility from our efforts.

更狠的是成本外推：他們估計，對下一份 spec 做同樣的事，邊際成本不會比第一份便宜多少。根因在原文第 4 節說得明白——**spec 是為了文件化與模型檢查而寫的，不是為了 trace-checking 而寫的**；RaftMongo.tla 抽象層次很高、狀態變數很少，而實作是數萬行的併發 C++，兩者之間的 abstraction gap 得用儀器化程式碼一吋一吋填。原文的判決：“MBTC is only practical if the specification is written with MBTC in mind.”

### MBTCG：四週換 4,913 個測試

第二個案例對 MongoDB Realm Sync 的 operational transformation 演算法做 model-based test-case generation（MBTCG），方向整個反過來：不檢查實作的行為，而是**把 TLC 跑出來的狀態圖直接變成測試集**。他們把約 1,000 行 C++ 的合併規則（6 種陣列操作、21 條規則）幾乎逐行轉寫成 795 行 TLA+（原文坦白：「copy-paste C++ 再手改成合法 TLA+」），再用 755 行 Golang 解析 TLC 輸出的狀態圖，生成 4,913 個 C++ 測試案例。一位工程師，四週完工。

成績單：生成的測試達成 100% 分支覆蓋（86/86）；對照組是 36 個手寫測試的 21%、AFL fuzzing 的 92%。途中 TLC 還在 ArraySwap 與 ArrayMove 的合併規則上撞出 StackOverflowError——查下去發現 C++ 原版有同一個 bug，**轉寫 spec 時把 bug 也忠實地抄過來了**，這直接促成新版實作棄用 ArraySwap。這個插曲值得玩味：spec 不是魔法，從有 bug 的程式碼轉寫出來的 spec 會繼承 bug；但窮舉式的檢查讓這顆 bug 在 spec 裡無所遁形，而它在 C++ 裡藏過了所有測試。

### 一成一敗的解剖

為什麼同一家公司、同一套方法論，結果天差地遠？論文自己的分析可以濃縮成一張對照：

| | MBTC（敗） | MBTCG（成） |
|---|---|---|
| 標的 | 數萬行併發分散式協議實作 | 約千行、輸入輸出明確的純函式 |
| spec 與實作的距離 | 高度抽象 spec vs 真實系統，鴻溝巨大 | spec 由實作逐行轉寫，距離趨近於零 |
| 接縫工程 | 儀器化、鎖、trace 後處理，貴到放棄 | 解析 TLC 輸出生成測試，一次寫完 |
| 狀態空間 | 真實執行的交錯，收不全也對不準 | 約束後可窮舉（3 客戶端、單操作、3 元素陣列） |
| 投入 | 2 人 × 10 週 | 1 人 × 4 週 |

這份報告對本章的價值有兩層。第一層是方法選擇：核心若能隔離成純函式，MBTCG 是黃金標準；核心若是活的併發系統，conformance 檢查貴到需要在寫 spec 之初就為它設計。第二層更普遍：**spec 與程式碼的同步是真實的、持續的、會吃預算的痛**，不是文件末尾一行「記得更新 spec」就能打發的——這是下面「spec 腐化」一節的主證據。

## Azure Cosmos DB：spec 存在 ≠ spec 為真

Microsoft 的 Cosmos DB 是 TLA+ 的招牌案例之一：官方 spec repo（`Azure/azure-cosmos-tla`，2026-06 開頁查證）公開了五種一致性等級——strong、bounded staleness、session、consistent prefix、eventual——的 TLA+ 規格，外加三個由簡到繁的情境模型；團隊自述「heavily relies on TLA+」。README 還連到一段 Lamport 的受訪影片，談 TLA+ 在 Cosmos DB 的應用。這裡先把人物關係說準：**Lamport 曾與 Cosmos DB 團隊合作、受訪談其 TLA+ 實踐；他不是 Cosmos DB 或其一致性協定的設計者。**把發明 TLA+ 的人寫成用 TLA+ 的每個系統的設計者，是案例轉述的另一個常見變形。

故事有趣的部分在後頭。Hackett、Rowe 與 Kuppe 的論文 “Understanding Inconsistency in Azure Cosmos DB with TLA+”（ICSE-SEIP 2023；2026-06 對照 arXiv 2210.13661 摘要）做了一件事：不站在實作者視角、改站在**使用者視角**重寫一份 spec——只描述「客戶端能觀測到什麼」。結果（摘要原文意旨）：這份 spec 比既有的任何 Cosmos DB 規格都更小、概念上更簡單，卻涵蓋了**更廣**的合法可觀測行為；其中不少行為「在 Cosmos DB 開發團隊之外此前連非正式的理解都談不上」。對使用者語意理解不足，已在依賴 Cosmos DB 的 Microsoft 產品裡造成過資料一致性錯誤；這項工作修正了兩處文件問題，並為另一個 Azure 服務先前一次高影響度的故障提供了根本解法（細節以摘要所述為準）。

這個案例的教訓比表面深一層。官方 spec 一直都在、團隊一直在用 TLA+，但 spec 是**寫給實作者看的**——它描述內部協議怎麼運作，而不是使用者會看到什麼。第三方研究者用同一個語言、換一個視角，就照出了縫隙。所以「有沒有 spec」是個太粗的問題，要問的是：**spec 的受眾是誰、它最後一次對齊現實是什麼時候、誰負責它**。一份過期或視角錯位的 spec 比沒有 spec 更危險，因為它頂著「已形式化」的權威讓人放下戒心——這是 vacuous truth 的組織版（ch03 的老朋友：看起來成立，因為你問錯了問題）。

## CockroachDB：一場 workshop 能買到什麼

最後一個案例最小，也最容易複製。CockroachDB 的 Parallel Commits 是分散式交易 commit 協議的延遲最佳化：把傳統 2PC（見 ch11）裡「先 prepare 再 commit」的兩輪往返壓成一輪，代價是引入一個「implicit commit」中間狀態——交易在所有寫入意圖就位的瞬間就算邏輯上已提交，顯式的 commit 紀錄之後補寫。你的 ch11 直覺應該立刻拉警報：**新增中間狀態＋協調者可能在任何一步故障**，這正是 2PC blocking 問題的高危地形，憑感覺設計必死。

所以他們寫了 spec。官方部落格（Nathan VanBenschoten，2019-11-07，2026-06 開頁查證）記載，團隊用 TLA+ 驗了兩條性質，名字取得教科書般工整：

- **AckImpliesCommit**（safety）：coordinator 一旦向客戶端回報提交成功，該交易必然已提交——不存在「跟客戶說好了、系統裡卻沒有」的世界。
- **ImplicitCommitLeadsToExplicitCommit**（liveness）：進入 implicit commit 狀態的交易終將進入 explicit commit，**即使 coordinator 故障**。用 ch07 的語言：這是一條 leads-to（⤳）性質，而且他們真的驗了它——對照 AWS Table 1 裡那行「沒驗 liveness 所以沒抓到 liveness bug」，這是補上另一半的示範。

spec（`ParallelCommits.tla`）就放在 CockroachDB 的 GitHub repo。背景更值得注意：這份 spec 是在請 Hillel Wayne（learntla.com 作者）帶的內部 workshop 中發展出來的。換句話說，這不是 AWS 等級的多年投入，而是「一個資料庫團隊＋一位外聘講師＋一場 workshop」的產出規模，就對一個生死攸關的新協議拿到了 safety 與 liveness 兩張保證書。對在小團隊工作的你，這是四個案例裡尺寸最接近現實的一個。

## 模式歸納：什麼問題值得形式化

把四組案例放在一起，值得寫 spec 的問題長相可以收斂成七個判準。每個判準後面都站著一個案例。

| # | 判準 | 案例根據 |
|---|---|---|
| 一 | **核心是「規則少、交錯多」的協議**：能用百行級 spec 描述的設計核心 | AWS Table 1：六份 spec 全在 102～939 行 |
| 二 | **bug 主要來自故障×併發的交錯**，測試無法控制調度 | DynamoDB 35 步 bug 穿過三道人工防線 |
| 三 | **錯誤代價高且不可逆**：資料毀損、錢、信任，而非可重試的瞬時失敗 | S3 強一致性遷移；CockroachDB 的 AckImpliesCommit |
| 四 | **最壞反例很深**：需要多步精確交錯才觸發，人腦與隨機測試都搆不到 | 35 步；Firecracker 的 virtio 重疊佇列 |
| 五 | **介入時機在設計期**：spec 最大紅利是在蓋之前想清楚；已上線系統的 spec 紅利轉為理解與文件 | AWS 高層把 spec 排進年度規劃 vs Cosmos DB 的考古式重寫 |
| 六 | **有人養 spec**：明確 owner 與同步策略，否則註定腐化 | MongoDB conformance 之痛；Cosmos DB 視角錯位 |
| 七 | **學習成本攤提得掉**：首次投入兩到三週，之後邊際成本驟降 | CACM 2015 學習曲線證詞；Fan Zhang 兩週兩版 spec |

反面清單同樣重要——這些形狀**不**值得動用 TLA+：規則多但交錯少的業務 CRUD（測試、型別、code review 的性價比更高）；效能問題（TLA+ 不談快慢，見 ch09 對 TLC 能與不能的劃界）；UI 流程；以及能隔離成小純函式的邏輯——那是 property-based testing 或 MBTCG 的地盤（MongoDB 案例的正面教材，方法光譜見 ch18）。

## 成本誠實帳

案例讀完，把帳攤開。形式化方法的成本不只「學語言」一項，完整的帳有五行：

**學習曲線。**CACM 2015 的證詞：從新進到 principal 的工程師都能從零學起，兩到三週拿到有用的結果。這個數字有兩個前提常被略過：一是「有用的結果」指第一份能跑 TLC 的 spec，不是精通；二是 AWS 有高階主管把這幾週排進年度規劃——學習時間是**編列出來的**，不是工程師用晚上擠的。你已經用這本書付掉這一行，但替團隊評估時，這行要照實列。

**寫 spec 的成本。**百行級 spec、單人數天到數週（Fan Zhang：兩週兩版；CockroachDB：一場 workshop；MongoDB MBTCG：四週含測試生成器）。便宜的前提是判準一成立——你 spec 的是協議核心，不是整個系統。

**驗證的極限。**spec 過了 TLC，買到的是「這個設計在這組參數下沒有反例」（見 ch09 的 small scope hypothesis），不是「程式碼正確」。設計與實作之間的 conformance gap 要嘛花錢驗（MongoDB 的帳單在上面）、要嘛誠實地接受為殘餘風險。多數團隊選後者——選了就寫下來，別假裝沒有。

**維護成本。**spec 不會自動跟著程式碼演化。這行的單價見下一節。

**隱藏的紅利（負成本）。**寫 spec 逼你在蓋之前把設計想清楚——ch01 的論點，四個案例全數佐證：S3 團隊省下自製模型檢查器、MongoDB 從轉寫過程揪出陳年 bug、Cosmos DB 的重寫照出連團隊都沒明說過的語意。就算 spec 寫完即丟，這份紅利已經落袋。

## spec 腐化：維運視角

你維運過的每種文件都會腐化：API 文件落後三個版本、runbook 寫著已下線的指令、架構圖畫著去年的拓撲。spec 也是文件，一樣會腐化——但它腐化得更危險，因為它頂著「已驗證」的光環。過期的 runbook 你會半信半疑，過期的 spec 你會全信。

兩個案例已經把這件事演示完了：MongoDB 想用機器逼 spec 與程式碼同步，二十人週買到「除非 spec 為此而設計，否則不可行」；Cosmos DB 的官方 spec 一直活著、團隊一直在用，第三方仍然照出了 spec 視角與使用者現實的落差。腐化不是「會不會」的問題，是「漂移速度 vs 對齊頻率」的問題——跟你管 schema migration、管 infra-as-code 的 drift 是同一道題。

對策是一條光譜，成本遞增：

| 對策 | 做法 | 成本 | 適用 |
|---|---|---|---|
| 凍結標註 | spec 註明「驗證於設計 vX／對應 commit」，過期即明示 | 近乎零 | 一次性設計驗證 |
| 流程掛鉤 | 協議級改動的 PR checklist 強制「review 並更新 spec」 | 低 | 小團隊、低頻改動 |
| MBTCG | spec 生成測試集，測試掛 CI——spec 過期測試就會說話 | 中（MongoDB：1 人 4 週） | 核心可隔離成純函式 |
| MBTC / trace checking | 實作軌跡對 spec 檢查 | 高（MongoDB：2 人 10 週仍敗） | spec 自始為此設計、多實作對齊 |
| Runtime 監控 | 生產日誌對 spec 驗證（P 生態的 PObserve 走這個方向，2026-06 僅見官方簡述，細節未查證） | 高 | 超大規模、持續驗證需求 |

維運鐵律一條：**spec 要有 owner，跟 runbook 一樣**。沒有 owner 的 spec 不是資產，是一張會誤導後人的過期地圖。團隊只有一個人？那就是你——把對齊動作掛進你自己的變更流程（本章紙上推演的題 3 就是這道題）。

## Worked example：你的結算 pipeline 值不值得寫 spec

把七個判準按在本書的貫穿範例上，從頭走到尾。評估標的（見 ch02 引入、ch08 升級）：K8s CronJobs → SQS → idempotent consumers → 入帳 ledger；at-least-once 投遞、consumer 可能 crash、redelivery、dedup 表；量級每季 10 萬～30 萬筆結算訊息。問題：**這個系統值不值得寫 TLA+ spec？**

**判準一：核心是不是百行級的協議？**是。整個 pipeline 很大（排程、拉取、業務計算、入帳、報表），但「正確性吃緊」的核心只有一塊：redelivery × dedup × 入帳的 exactly-once 語意。規則少（收訊、查 dedup、入帳、寫 dedup、ack、crash、redeliver 七八個動作）、交錯多。對照 AWS Table 1 的尺寸感，這是 EBS volume 管理（102 行）那一級的 spec，不是 DynamoDB（939 行）那一級。估計 50～150 行。✓

**判準二：bug 是否來自故障×併發交錯？**是，而且你有第一手證據：ch01 開場那個 race——dedup 檢查與入帳之間被插隊——正是這個形狀。integration test 沒辦法命令 SQS「請在 consumer 寫完 dedup、還沒 ack 的那 200 毫秒裡 redeliver 給另一個 consumer」；調度不可控，這是 ch01 的老結論。✓

**判準三：錯誤代價高且不可逆？**是——這條 pipeline 碰錢。算兩個情境。常態損耗：假設 double-pay 率十萬分之一，每季 10 萬～30 萬筆 ⇒ 每季 1～3 筆錯帳，每筆對帳＋客服＋修數抓 2～4 小時工程時間，一年燒掉約 8～48 小時，即 0.2～1.2 個人週——單看這條，連 spec 的成本都未必回得來，低頻但持續流血而已。尾部風險才是大頭：一次 deploy 引入的調度型 race 在尖峰期把錯誤率拉到千分之一 ⇒ 單季 100～300 筆錯帳，這是「全體對帳＋對外道歉」等級的事故，成本以人月與信任計。✓

**判準四：最壞反例多深？**中等深。`NoDoublePay` 的典型反例（ch08 的 v1 攤開過這類窗口）需要「consumer A 入帳→crash 落在寫 dedup 與 ack 之間→redelivery→consumer B 查 dedup 撲空→再入帳」，約 5～8 步精確交錯。不到 35 步，但已經超出 code review 可靠目視的深度，也超出非決定性測試穩定重現的能力。✓

**判準五：設計期還是考古期？**誠實說：考古期——系統已上線，最大紅利（蓋之前想清楚）已經錯過。但兩個殘值仍在：(a) pipeline 還會演化（加 DLQ、改 batch consumer、換 broker 的議題都在 backlog），每次協議級改動都是一個 mini 設計期；(b) spec 是 onboarding 與交接的高密度文件（Cosmos DB 路線的正面用法）。△——半分。

**判準六：誰養 spec？**你，而且只有你。所以策略選光譜最便宜的兩格：凍結標註＋流程掛鉤——spec 標明對應版本，協議級改動時更新並紙上重驗。明確**不**做 MBTC：MongoDB 用二十人週證明了那條路對這個規模不成立。dedup 查寫邏輯若日後隔離成純函式，可以考慮 MBTCG，但目前不是。✓（有策略即算過，策略要寫進 spec 檔頭。）

**判準七：學習成本攤提了嗎？**已攤提——你讀到 ch17 了。邊際成本不是 CACM 2015 的兩三週，是寫一份你已經在 ch02～ch15 反覆操作過的系統的 spec：抓 2～5 個工作天。✓

**結論（有數字版）：值得，但範圍嚴格限定。**只 spec「redelivery × dedup × ledger」核心（約百行、2～5 個工作天，外加每次協議級改動 0.5～1 天的維護），不 spec CronJob 排程、SQS 內部、業務計算。收益端：防住的主要不是每季 1～3 筆的常態損耗（那用對帳 job 防更便宜），而是判準三算出來的尾部事故——單次 100～300 筆錯帳、人月級清理。只要你估「未來兩年內因協議級改動引入一次這種 race」的機率高於一成，期望損失就已經超過 spec 的全部成本。而本書其實已經把答案演示完了：這份 spec 在 ch02～ch15 被一路寫出來、驗過、證過——你現在做的這個評估，是事後替一個已完成的投資補上投資備忘錄，而備忘錄說：投對了。

**誠實的反轉條款**：把同一條 pipeline 換成不碰錢的內部報表系統，判準三倒下——錯一筆的代價是重跑 job，不可逆性消失，整個 ROI 隨之瓦解。那種系統的正確答案是 idempotent consumer 的常識模式＋一個對帳 job，spec 免了。判準框架的價值不在「告訴你要寫 spec」，在於讓「不寫」也成為一個有論證的決定。

## 陷阱與防禦

讀業界案例自己的故障模式。每一條都在本章出現過實例：

| 陷阱 | 它怎麼騙你 | 防禦 |
|---|---|---|
| 倖存者偏差 | 部落格只刊成功案例，你以為方法戰無不勝 | 主動找失敗報告；MongoDB MBTC 那份比十篇成功案例值錢 |
| 張冠李戴 | 「S3 找到 35 步 bug」「ShardStore 用 TLA+」「Lamport 設計了 Cosmos DB」——全錯 | 回到原始來源；本章正文已給對照：35 步＝DynamoDB、ShardStore＝Rust＋property-based testing、Lamport＝合作與受訪 |
| 數字脫離時點 | 「七個團隊」被當成永恆事實引用 | 數字一律綁年份：「2015 年論文時點七個團隊」 |
| 有 spec＝沒問題 | 官方 spec repo 活著，就以為語意被正確理解 | 問三件事：spec 受眾是誰、最後對齊現實是何時、owner 是誰（Cosmos DB 教訓） |
| 工具只答你問的 | 「TLC 全綠」但你根本沒寫 liveness 性質——空洞的安心 | 顯式列性質清單；AWS lock manager 那行（沒驗 liveness 就沒抓到 liveness bug）與 ch07 的 fairness 警告同源 |
| 案例光環 | 「AWS 都在用，我們也要導入」 | 案例給的是判準不是結論；用七判準走自己的系統，包括走出「不值得」 |
| spec 過了＝程式碼對了 | 忘記 conformance gap，把設計驗證當實作保證 | 明寫殘餘風險；要消滅 gap 先讀 MongoDB 的帳單再決定 |

## 紙上推演

### 題 1：三個系統的 ROI 排序（[25 分鐘] ★★）

用本章七判準評估下列三個假想系統，給每個系統「值得／值得但限定範圍／不值得」的結論，並排出形式化投資的優先順序：

- **A. 內部管理後台**：CRUD＋權限＋審批表單，單一 PostgreSQL，所有交易單庫完成，使用者約 200 人。
- **B. 自研分散式鎖服務**：lease＋heartbeat＋failover，公司上百個服務依賴它做互斥。
- **C. 計費對帳 pipeline**：每日批次拉第三方帳單、與內部 ledger 對帳，錯帳會多收客戶錢；偶有並行的人工修正單。

### 推演解答

**排序：B ＞ C ＞ A。**

**B：值得，全額投資。**判準一：lease 過期、heartbeat 遺失、failover 的規則少、交錯極多——教科書級協議核心（AWS Table 1 裡就有內部鎖服務，前例直接命中）。判準二：bug 全部來自故障×時序交錯。判準三：鎖服務錯一次＝上百個依賴服務的互斥假設集體破產，代價不可逆且呈扇形放大。判準四：lease 與 failover 的反例通常要「heartbeat 延遲＋舊 leader 復活」等多步交錯，深。注意 safety 與 liveness 都要列（ch10 的互斥雙性質；別重蹈「沒驗 liveness」的覆轍）。

**C：值得但限定範圍。**判準三強命中（錢），但判準二要誠實檢查：批次拉帳→比對→出報告是序列流程，交錯少——這部分測試＋帳目守恆的對帳 invariant 就夠。唯一可能值得 spec 的窗口是「並行人工修正單 × 自動對帳」的交錯；若該窗口存在就給它一份小 spec，否則把「帳目守恆」寫成生產環境持續檢查的 invariant（形式化思維紅利，工具免了——ch18 會展開這條路）。

**A：不值得。**判準一即陣亡：規則多（權限矩陣、表單流程）但交錯少，DB 單庫交易已經買斷了互斥與原子性（你付錢給 PostgreSQL 就是在買這個）。錯誤代價低且可逆。正確投資是型別、權限測試、code review。如果硬要找形式化的影子：把審批流程畫成狀態機並檢查「不可達狀態」（ch02 的紙筆技能），十五分鐘的白板作業，不必動 TLA+。

常見錯路：看到「錢」就把 C 排第一。判準三只是七分之一；C 的交錯結構（判準二、四）比 B 淺一個量級，而 B 錯一次的爆炸半徑其實也是錢——全公司的錢。

### 題 2：抓出簡報裡的張冠李戴（[15 分鐘] ★★）

你的同事要在技術分享會上推銷形式化方法，投影片有五條主張。指出每一條是對是錯，錯的給出正確版本：

1. 「AWS S3 團隊用 TLA+ 找到一個需要 35 步才能重現的 bug。」
2. 「截至目前，Amazon 有七個團隊用過 TLA+。」
3. 「S3 的儲存節點 ShardStore 用 TLA+ 完成了驗證（SOSP 2021）。」
4. 「Lamport 設計了 Azure Cosmos DB 的一致性協定。」
5. 「CockroachDB 的 Parallel Commits 用 TLA+ 同時驗證了 safety 與 liveness 性質。」

### 推演解答

1. **錯。**35 步 bug 屬於 **DynamoDB** 的複寫與群組成員系統（CACM 2015 Table 1）。S3 的戰績是另外兩行：804 行與 645 行的 PlusCal spec、合計至少四個 bug。
2. **錯在時態。**「七個團隊」是 **2015 年論文寫作時點**的數字；拿到今天必須寫成「2015 年論文時點已有七個團隊」。脫離時點的引用會同時得罪兩邊：低估了之後的擴散，又虛構了「現在」的精確數字。
3. **錯。**ShardStore 用的是**輕量級形式化方法**：Rust 參考模型＋property-based testing，論文標題裡的 “Lightweight Formal Methods” 就是在跟重型方法劃清界線。不是 TLA+，也不是 P。
4. **錯。**Lamport 曾與 Cosmos DB 團隊**合作、受訪**談 TLA+ 的應用（官方 repo README 連結了訪談影片）；協定設計是 Cosmos DB 團隊的工作。
5. **對。**AckImpliesCommit（safety）與 ImplicitCommitLeadsToExplicitCommit（liveness）——而且後者驗的是 coordinator 故障下的 leads-to，是四組案例裡把 liveness 驗好驗滿的代表。簡報裡混一條真話，是檢驗你有沒有真的核對、還是反射性全盤喊錯。

### 題 3：spec 的同步策略（[20 分鐘] ★★★）

你的結算 pipeline spec（ch08 的 v1）已凍結標註一年。現在 backlog 排定兩個改動：(i) 加 DLQ——訊息重試三次失敗後改投 dead-letter queue，人工介入；(ii) consumer 改批次模式——一次拉 10 則訊息、逐則處理、最後一次性 ack。針對每個改動，從「(a) 不動 spec／(b) 更新 spec 並紙上重驗／(c) 建 MBTC trace-checking」中選擇，用本章證據說明理由；並回答：什麼條件成立時，(c) 才會變成正確答案？

### 推演解答

**兩個改動都選 (b)，但理由的重量不同。**

(i) DLQ 是**協議級改動**：它修改了「每則訊息的終局」——終態集合從 {已入帳} 變成 {已入帳, 進 DLQ}，`AllPaid`（ch07）的措辭必須改寫成「終會入帳**或**進 DLQ 等待人工處理」，否則 liveness 主張直接變假。同時要檢查新窗口：「第三次失敗判定」與「redelivery」的交錯會不會讓一則訊息既入帳又進 DLQ（`NoDoublePay` 的近親）。不動 spec（選 a）的後果不是中性的：spec 會從「過期」滑向「說謊」——它聲稱的終局集合跟現實不同，下一個讀者（包括一年後的你）會被一份蓋著「已驗證」章的文件誤導，這正是 Cosmos DB 教訓的個人版。

(ii) 批次 ack 改變了 crash 窗口的形狀：以前 crash 最多讓 1 則訊息處於「已處理未 ack」，現在最多 10 則——redelivery 風暴的半徑變大，dedup 表被同時打的併發度上升。協議骨架沒變，但參數與窗口變了，invariant 的驗證要重走（紙上重推 crash-在-第-k-則 的家族 scenario）。這題如果選 (a)，spec 不會「說謊」得像 (i) 那麼明顯——這正是它陰險的地方：腐化從語意邊緣開始，不從正中央。

**(c) 何時才對？**至少三個條件同時成立：核心邏輯無法隔離成純函式（否則先考慮 MBTCG，便宜一個量級）；錯誤代價或實作數量上了一個量級（例如 pipeline 要重寫成第二種語言、兩個實作都聲稱符合同一份 spec）；以及——MongoDB 的判決——**spec 願意為 trace-checking 重新設計**，抽象層次降到實作可逐事件對齊，並編列二十人週起跳的預算。一人團隊、季百萬筆以下的量級，這三條一條都不成立；選 (c) 不是嚴謹，是把 MongoDB 已經替你付過的學費再付一次。

## 自我檢核

口頭回答，講不清楚就回對應小節重讀：

1. 向同事轉述 DynamoDB 35 步 bug 的故事：bug 屬於哪個系統的哪個元件、35 步意味著什麼、為什麼它是「測試與 review 蓋不住深交錯」論點的最強工業證據？
2. 「七個團隊」這個數字，怎麼引用才誠實？再多舉一個本章裡「數字必須綁時點」的例子。
3. TLA+ 與 P 在 AWS 工具箱裡的分工是什麼？ShardStore 為什麼不能當成 TLA+ 或 P 的案例？
4. MongoDB 兩個案例一成一敗，各用一句話說出根本原因；「spec 由實作逐行轉寫」在成功案例裡扮演什麼角色、又帶來什麼風險（提示：那顆被忠實抄過去的 bug）？
5. 「官方 spec repo 存在」與「系統語意被正確理解」之間差了什麼？Cosmos DB 案例裡，第三方的 spec 為什麼能比官方的更小卻涵蓋更廣？
6. CockroachDB 驗的兩條性質各是 safety 還是 liveness？為什麼說它補上了 AWS Table 1 某一行的遺憾？
7. 七個判準裡，你會先用哪三個快速篩掉「不值得形式化」的系統？為什麼是這三個？
8. 你的結算 pipeline 評估結論裡，哪一個判準翻轉會讓整個結論反轉？反轉後的正確替代方案是什麼？

## 延伸閱讀

- **How Amazon Web Services Uses Formal Methods**（Newcombe 等六人，*CACM* Vol. 58 No. 4，2015，DOI `10.1145/2699417`）：本章 AWS 案例的原典，Table 1 與「35 步」段落必讀；學習曲線與管理層支持的段落是你替團隊寫採用建議時的現成彈藥。（2026-06 已對照 PDF 原文逐字核對）
- **Systems Correctness Practices at Amazon Web Services**（*CACM* Vol. 68 No. 6，2025-06；ACM Queue 版 Vol. 22 No. 6，`https://queue.acm.org/detail.cfm?id=3712057`）：2015 的十年後續篇，AWS 正確性工具箱的全景。（2026-06 查證時點全文受取用限制，本章僅依摘要與二手轉述引用其框架，細節改採下列第一手來源）
- **P language 官方案例頁**：`https://p-org.github.io/P/casestudies/`。S3 strong consistency 遷移如何用 P 驗證的第一手簡述，含本章引用的原文句。（2026-06 開頁查證）
- **Using Kani to Validate Security Boundaries in AWS Firecracker**（Kani 官方部落格，2023）：`https://model-checking.github.io/kani-verifier-blog/2023/08/31/using-kani-to-validate-security-boundaries-in-aws-firecracker.html`。rate limiter 與 virtio 驗證的細節與 bug 清單，程式碼級驗證長什麼樣的最佳速寫。（2026-06 開頁查證）
- **Using Lightweight Formal Methods to Validate a Key-Value Storage Node in Amazon S3**（SOSP 2021，DOI `10.1145/3477132.3483540`）：ShardStore 的輕量方法論文——讀它最重要的理由是搞清楚它**不是** TLA+ 案例。（2026-06 未開原文，存在性經多來源確認）
- **eXtreme Modelling in Practice**（Davis、Hirschhorn、Schvimer，*PVLDB* Vol. 13 No. 9，2020）：`http://vldb.org/pvldb/vol13/p1346-davis.pdf`。本章最值得精讀的一篇：§4 的 MBTC 驗屍報告與 §5 的 MBTCG 成功學，工業界少見的誠實。（2026-06 對照論文原文）
- **Understanding Inconsistency in Azure Cosmos DB with TLA+**（Hackett、Rowe、Kuppe，ICSE-SEIP 2023，arXiv `2210.13661`）：使用者視角 spec 如何照出官方 spec 的縫隙；搭配官方 repo `https://github.com/Azure/azure-cosmos-tla` 對讀。（2026-06 對照 arXiv 摘要；repo 開頁查證）
- **Parallel Commits: An Atomic Commit Protocol for Globally Distributed Transactions**（Nathan VanBenschoten，CockroachDB blog，2019-11-07）：`https://www.cockroachlabs.com/blog/parallel-commits/`。讀協議設計，更要讀文末 TLA+ 驗證一節——兩條性質的命名就是一堂「怎麼把保證說清楚」的課；協議背景見 ch11。（2026-06 開頁查證）
