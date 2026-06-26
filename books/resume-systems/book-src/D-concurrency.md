# D · 並發與執行模型

本領域回答一件事：當一個行程要同時推進很多件事，它的執行模型給你什麼保證、又要你付什麼代價。本檔六條由淺到深：先釐清並發與平行不是同一件事（D 的第一原理），再進到 event loop 怎麼用單執行緒做並發、阻塞與非阻塞 I/O 的本質差、CPU 密集時 thread pool / worker threads 怎麼救場、共享狀態下的 race condition 與原子性（跨 DB / cache / runtime），最後把 thread / event-loop / actor / coroutine / CSP 五種並發模型並排取捨。邊界：本檔講「單機行程內」的並發機制；過載時的流量控制（背壓、限流）在領域 E，分散式多節點的協調（鎖、共識、時鐘）在領域 M。

## 並發 ≠ 平行

### 定義與原理

並發（concurrency）是「結構」：把程式拆成多個可獨立推進、彼此交錯的工作單元，描述的是「同時在處理多件事」這種**組織方式**。平行（parallelism）是「執行」：在同一個物理瞬間，多個工作單元真的在不同核心上一起跑，描述的是**同時執行**。Rob Pike 的經典一句概括是「concurrency is about dealing with lots of things at once; parallelism is about doing lots of things at once」——並發是關於結構，平行是關於執行。

關鍵在於兩者正交：一個單核心、單執行緒的 event loop（見 event loop）是**高度並發但零平行**——它在 I/O 等待的空檔切去處理別的請求，看起來同時服務上千連線，但任一瞬間 CPU 上只有一個工作在跑。反過來，一段把陣列切成四塊、丟到四核心同時運算的純計算程式碼是**平行但概念上不一定並發**（沒有交錯的獨立工作流，只是同一件事被切開）。把這兩個詞當同義詞，是並發模型選型一切誤判的起點。

第一原理：平行需要硬體（多核心），並發只需要一種「能在工作之間切換」的機制。你能在單核心上寫出極並發的程式（協作式切換），也能寫出完全不並發卻吃滿八核的程式（resize 一張大圖）。**並發是你寫程式的方式，平行是執行時恰好擁有的資源。**

### 解法空間

讓多件事「並發推進」的機制有三大類，差別在「誰決定何時切換」：

- **OS 搶佔式多工（preemptive threads / processes）**：核心用時鐘中斷強制切換執行緒。每個工作以為自己獨佔 CPU，切換對程式碼透明。真平行（多核）＋強隔離，但每次 context switch 要存/還暫存器與快取，代價約微秒級。
- **協作式切換（cooperative：event loop / coroutine）**：工作主動在「等 I/O」或 `await`／`yield` 點交出控制權，runtime 在單執行緒上輪流推進。切換極輕（函式呼叫等級），但一個工作若不肯讓出（跑死迴圈），整條線就卡死。
- **混合排程（M:N，如 Go 的 goroutine）**：把大量輕量工作（G）多工到少量 OS 執行緒（M）上，runtime 自己排程，並用搶佔補強協作式的卡死問題（見 並發模型比較）。

「要不要平行」是另一個正交決策：開幾條 OS 執行緒、`GOMAXPROCS` 設多少、event loop 配幾顆 worker——決定的是你拿幾顆核心，跟你用哪種並發結構是兩件事。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 單執行緒 event loop | 高並發、零資料競爭（同一時刻只一個工作動共享狀態） | I/O 密集、大量連線 | 任一 CPU 密集工作會卡死整條線（見 阻塞 vs 非阻塞 I/O） |
| 多執行緒（搶佔式） | 真平行、可吃滿多核 | CPU 密集、需隔離 | 共享記憶體即有 race condition（見 race condition 與原子性）；切換有成本 |
| 多行程 | 平行＋記憶體隔離（一個崩潰不拖垮別人） | 安全邊界、容錯 | 行程間通訊要序列化、貴；記憶體不共享 |
| M:N 協程排程 | 海量並發＋自動分配到多核 | 高並發＋部分 CPU 工作 | 排程器是黑箱；協作點不足會有公平性問題 |

保證的核心差異：**單執行緒模型用「沒有平行」換來「沒有資料競爭」**——這是 event loop 最大的隱性紅利。多執行緒用「真平行」換來「你得自己管同步」。沒有哪個免費。

### 何時需要

判準是工作負載的「瓶頸在哪」：

- **瓶頸在 I/O 等待**（呼叫 DB、外部 API、讀檔）：要的是並發，不是平行。單執行緒 event loop 或協程就夠，加核心幫不上忙——CPU 大半時間在閒等。
- **瓶頸在 CPU 計算**（壓縮、加密、影像處理、大量 JSON 解析）：要的是平行。單純的並發結構救不了，得真的用上多核（見 thread pool / worker threads）。
- **兩者都有**：用並發處理 I/O 海量連線，把少數 CPU 重活外送到 worker（見 並發模型比較）。

worked example：一個服務每請求要等 DB 約 20 ms（I/O）＋算約 1 ms（CPU）。單執行緒 event loop 在 20 ms 等待中能塞進約 20 個其他請求的 CPU 工作，單核理論上可達約 `1000 ms / 1 ms = 1000 req/s`——瓶頸是 CPU 那 1 ms，不是等待的 20 ms。若改成「每請求算 20 ms（CPU）＋等 1 ms」，單核就只剩約 `1000 / 20 = 50 req/s`，這時加核心（平行）才有意義。同樣的並發結構，瓶頸換邊，結論相反。

### 常見誤解與陷阱

- **「用了 async/await 就變快了」**：async 不增加 CPU 算力，只在等待空檔填入別的工作。對純 CPU 工作，async 不但不快，還多一層排程開銷。
- **「多執行緒一定比單執行緒快」**：對 I/O 密集負載，多執行緒的同步成本與 context switch 可能比單執行緒 event loop 還慢，且引入 race condition。
- **「並發程式在單核上沒意義」**：恰恰相反，I/O 密集的並發在單核上就能大幅提升吞吐——重點是重疊等待時間，不是疊加算力。
- **把「執行緒數」當「平行度」**：開 1000 條執行緒在 4 核機器上，平行度仍是 4，多出來的 996 條只是在排隊與徒增切換成本。平行度由核心數封頂。

### 延伸閱讀

- Rob Pike, "Concurrency is not Parallelism"（Go 官方部落格 talk）：https://go.dev/blog/waza-talk
- Joe Armstrong / 一般概念可參考 Wikipedia「Concurrency (computer science)」：https://en.wikipedia.org/wiki/Concurrency_(computer_science)

## event loop（單執行緒並發、libuv 相位）

### 定義與原理

event loop 是「單執行緒做並發」的核心機制：一條主執行緒不斷輪詢「有沒有就緒的事件」（連線可讀、計時器到期、I/O 完成），有就執行對應的 callback，沒有就把空閒讓給作業系統去等。它的全部魔法是——**永遠不要在主執行緒上同步阻塞地等任何東西**，所有會等待的操作都登記一個 callback 後立刻返回，等資料就緒了 OS 通知，event loop 再回頭跑 callback。如此一條執行緒就能交錯服務上千個連線。

以 Node.js 的 libuv 為例（2026-06 active LTS 為 Node 24「Krypton」），事件迴圈一輪分成數個固定相位（phase），依序循環（libuv 官方文件）：

```text
（示意，非可執行）
   ┌────────────────────────────────────────────┐
┌─>│  timers（setTimeout / setInterval 到期）   │
│  ├────────────────────────────────────────────┤
│  │  pending callbacks（延後的系統 callback）  │
│  ├────────────────────────────────────────────┤
│  │  idle / prepare（內部使用）                │
│  ├────────────────────────────────────────────┤    incoming:
│  │  poll（等並取 I/O 事件，可阻塞於此）       │<─── connections,
│  ├────────────────────────────────────────────┤      data, etc.
│  │  check（setImmediate callback）            │
│  ├────────────────────────────────────────────┤
└──┤  close callbacks（socket close 等）        │
   └────────────────────────────────────────────┘
```

關鍵 nuance：**microtask（先 `process.nextTick` 佇列、再 Promise 的 `.then`）不屬於任何 phase**——它們在「每個 callback 跑完之後、進入下一個之前」就被排空。所以一個沒完沒了的 `process.nextTick` 鏈可以餓死整個 I/O phase，連 timer 都跑不到。

### 解法空間

event loop 之所以能成立，靠的是把「等待」這件事委派出去的幾種底層機制：

- **OS 的就緒通知 API**：Linux `epoll`、BSD/macOS `kqueue`、Windows IOCP。event loop 用它一次問 OS「這 5000 個 fd 裡哪些就緒了」，不必為每個連線開執行緒。**網路 I/O 走這條路，不佔 thread pool。**
- **thread pool（libuv 預設 4 條）**：對沒有 async OS 原語的操作（檔案系統、`dns.lookup`、async crypto 如 pbkdf2/scrypt、所有 async zlib），libuv 偷偷開一個工作執行緒池去同步做，做完再把結果丟回主執行緒的迴圈（見 thread pool / worker threads；UV_THREADPOOL_SIZE 預設 4，可調至最大 1024，libuv 文件）。
- **timer 堆**：`setTimeout`/`setInterval` 註冊在 timers phase，每輪檢查有哪些到期。
- **microtask 佇列**：Promise / `nextTick`，在 callback 之間排空，優先於下一個 macrotask。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| event loop ＋ epoll/kqueue | 單執行緒服務海量並發 I/O，無資料競爭 | I/O 密集（API、proxy、即時推送） | 任何同步 CPU 重活卡死全部請求 |
| event loop ＋ libuv thread pool | 把無 async 原語的 fs/dns/crypto 變非阻塞 | 偶發的檔案/雜湊操作 | 池只有 4 條，4 個慢操作就排滿、其餘排隊 |
| `setImmediate`（check phase） | 在本輪 I/O callback 後、下輪 timers 前執行 | 讓出控制權給 I/O，切分長任務 | 與 `setTimeout(fn,0)` 觸發時機不同，別混用 |
| `process.nextTick` / Promise（microtask） | 在當前操作後立刻、先於任何 I/O | 緊接著當前邏輯的收尾 | 無限鏈會餓死 I/O 與 timer（最危險的坑） |

### 何時需要

當系統的工作是「大量連線、每個連線大半時間在等」時，event loop 是性價比最高的模型——一條執行緒、極低記憶體、無鎖。典型如 API gateway、WebSocket 推送伺服器、BFF（backend-for-frontend）聚合多個下游。

反過來，當每個請求都帶著沉重的同步計算（即時轉碼、複雜密碼學、大型報表彙整），event loop 是個陷阱：單執行緒一旦被一個請求的計算佔住，**其餘所有連線一起凍結**，p99 延遲爆炸。這時要嘛把計算外送 worker（見 thread pool / worker threads），要嘛根本選別的模型（見 並發模型比較）。

worked example：event loop 上一個請求做了一次同步 `JSON.parse` 解 50 MB 字串，耗時約 800 ms。在這 800 ms 內，主執行緒完全無法處理其他請求——若此刻有 100 個連線在線，它們全部被延遲 800 ms。把 QPS 100 的服務的 p99 從 20 ms 拉到 800+ ms，只因為一個沒讓出的同步呼叫。

### 常見誤解與陷阱

- **「event loop ＝ 慢」**：剛好相反，I/O 密集場景它通常比 thread-per-request 快又省記憶體。它慢只發生在被 CPU 工作堵住時。
- **「async 函式不會阻塞 event loop」**：async 只保證「等 I/O 時讓出」；函式裡的**同步 CPU 區段**照樣阻塞。`await` 不會魔法般切開一個 200 ms 的 `for` 迴圈。
- **「`setTimeout(fn, 0)` 會立刻執行」**：它排到下一輪 timers phase，且有最小延遲 clamp，實際可能晚數毫秒；要「盡快但讓出」用 `setImmediate`。
- **把 libuv thread pool 當無限**：預設只有 4 條。同時 5 個 `crypto.pbkdf2` 或大檔讀取，第 5 個就得排隊——這常被誤判成「Node 變慢了」（見 thread pool / worker threads）。
- **微任務餓死**：遞迴 `process.nextTick` 或 Promise 鏈會讓 event loop 永遠卡在 microtask 排空、跑不到 I/O。

### 延伸閱讀

- libuv 官方設計文件（event loop 各 phase）：https://docs.libuv.org/en/v1.x/design.html
- libuv thread pool 文件（UV_THREADPOOL_SIZE 與用途）：https://docs.libuv.org/en/v1.x/threadpool.html
- Node.js 官方「The Node.js Event Loop」指南：https://nodejs.org/en/learn/asynchronous-work/event-loop-timers-and-nexttick

## 阻塞 vs 非阻塞 I/O

### 定義與原理

阻塞與非阻塞講的是「發起一個 I/O 操作的呼叫，會不會讓發起它的執行緒停在那裡等」。**阻塞（blocking）**：`read()` 直到資料就緒才返回，期間這條執行緒什麼都不能做、被 OS 掛起。**非阻塞（non-blocking）**：`read()` 若無資料立刻返回（回 `EWOULDBLOCK`），執行緒繼續跑別的；何時有資料，靠就緒通知（`epoll`/`kqueue`）或回呼告知。

容易混淆的是還有第二個正交維度——**同步 vs 非同步**。同步＝你得自己問「好了沒」（包括非阻塞的輪詢與 readiness 模型）；非同步（completion 模型，如 Windows IOCP、Linux `io_uring`）＝你發起後 OS 在完成時主動把結果交給你。一般後端工程語境的「非阻塞 I/O」通常指「非阻塞 fd ＋ readiness 通知」這套（epoll 風格），它是 event loop 的地基（見 event loop）。

第一原理：阻塞模型下，「同時服務 N 個連線」需要 N 條執行緒（thread-per-connection），每條在自己的 `read` 上等。非阻塞模型下，一條執行緒用一次 `epoll_wait` 就能照看上萬個 fd——**用「不為等待付執行緒」換來海量並發**。

### 解法空間

要讓「等 I/O」不浪費執行緒，演化出幾種 I/O 多工模型：

- **thread-per-connection（阻塞）**：每連線一條執行緒，程式碼最直覺（線性讀寫），但連線數受執行緒數封頂，C10K 以上記憶體與切換成本爆炸。
- **`select` / `poll`（非阻塞 readiness）**：一次傳一堆 fd 問 OS 哪些就緒，但每次都要把整個 fd 集合複製進核心、且 O(n) 掃描，fd 多就慢。
- **`epoll`（Linux）/ `kqueue`（BSD/macOS）**：核心維護就緒列表，只回傳真正就緒的 fd，O(就緒數) 而非 O(總數)，這是現代高並發伺服器的標配。
- **completion-based（IOCP / `io_uring`）**：真正的非同步——提交操作後 OS 完成時回報結果，連「就緒後自己再讀」那步都省了，且能批次提交、減少系統呼叫。
- **協程包裝**：在非阻塞底層上，用協程（goroutine/coroutine）讓**程式碼長得像阻塞的線性風格**，但執行時不真的卡執行緒（見 並發模型比較）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| thread-per-connection（阻塞） | 程式碼線性好懂；強隔離 | 連線數不多（數百） | 每執行緒約佔 0.5–8 MB 堆疊，連線數一高即 OOM/切換爆炸 |
| epoll/kqueue（非阻塞 readiness） | 一條執行緒照看上萬 fd | 高並發 I/O 伺服器 | 回呼/狀態機式程式碼較難寫；CPU 工作仍會卡住該執行緒 |
| io_uring（completion） | 最少系統呼叫、可批次提交 | 極致 I/O 吞吐（新核心） | 需較新 Linux；API 複雜、生態仍在成熟 |
| 協程包裝非阻塞底層 | 線性程式碼＋非阻塞效能 | 想要可讀性又要高並發 | runtime 較重；阻塞式系統呼叫會「漏」回卡執行緒 |

### 何時需要

連線數是第一判準。連線數穩定在數百以內、且每個連線吞吐高、邏輯複雜——thread-per-connection 的可讀性紅利值得，別過早上 epoll。連線數上萬、每連線多半在閒等（聊天、推播、IoT 長連線）——非阻塞 ＋ readiness 是唯一可行解，阻塞模型會被執行緒成本壓垮。

worked example：C10K 問題的算術。用 thread-per-connection 服務 10,000 個並發連線，每條執行緒預設堆疊約 1 MB，光堆疊就要約 10 GB 記憶體，外加 10,000 條執行緒的 context switch 把 CPU 吃在排程上。改用單執行緒 ＋ epoll，10,000 個 fd 只是核心裡一張就緒列表，記憶體以 MB 計、無切換成本——這正是 Nginx、Node、Redis 都選非阻塞事件驅動的原因。

### 常見誤解與陷阱

- **「非阻塞 ＝ 非同步」**：兩者正交。非阻塞 readiness（epoll）仍是同步模型——你還是得在就緒後自己呼叫 `read`；真非同步是 completion 模型（IOCP/io_uring）。
- **「非阻塞 I/O 就不會被卡」**：非阻塞解的是「等 I/O」，解不了「算 CPU」。在 epoll 迴圈裡做一個 500 ms 的同步計算，照樣卡住其餘所有 fd（見 event loop）。
- **「把阻塞呼叫放進 event loop 沒事」**：在事件迴圈執行緒上呼叫一個阻塞的 `fs.readFileSync` 或同步 DB driver，會凍結整條線。阻塞呼叫必須外送到執行緒池或改用其非阻塞版本。
- **「DNS 是網路操作所以走 epoll」**：`getaddrinfo`（`dns.lookup`）是阻塞的 libc 呼叫，在 Node 裡走的是 thread pool 那 4 條，不是 epoll——大量 DNS 查詢會悄悄排滿 thread pool（見 event loop）。

### 延伸閱讀

- Dan Kegel, "The C10K problem"（經典文獻，I/O 模型總覽）：http://www.kegel.com/c10k.html
- Linux `epoll` man page：https://man7.org/linux/man-pages/man7/epoll.7.html
- `io_uring` 設計文件（Efficient IO with io_uring, Jens Axboe）：https://kernel.dk/io_uring.pdf

## thread pool / worker threads（CPU 密集怎麼辦）

### 定義與原理

event loop 的單執行緒在 CPU 重活面前會凍結（見 event loop）。解法不是「讓 event loop 變快」，而是**把計算搬離事件迴圈所在的那條執行緒**，讓主執行緒繼續服務 I/O，計算在別處跑。兩種「別處」：

- **thread pool（執行緒池）**：一組預先建好的工作執行緒，把「任務」丟進去由空閒執行緒撿來做，做完回報。重用執行緒、避免每任務都建/銷毀的成本。libuv 內建的就是這種，自動處理 fs/dns/crypto。
- **worker threads（工作執行緒）**：在 Node.js 裡明確開出獨立的 JS 執行緒（`worker_threads` 模組），各有自己的 V8 isolate 與 event loop，可真正平行跑 JS。你把 CPU 重活放進 worker，主執行緒丟工作、收結果。

關鍵區分：libuv thread pool 是**框架替你管的、給 C/C++ 層的 fs/crypto 用**，你不能往裡丟任意 JS；worker threads 是**你自己開的、跑你的 JS 計算**。前者預設 4 條（UV_THREADPOOL_SIZE，libuv 文件），後者數量你決定（通常對齊 CPU 核心數）。

第一原理：JS 在單一 isolate 內仍是單執行緒，要平行跑 JS 計算，唯一的路是開新的 isolate（worker thread 或子行程）。沒有捷徑，async 救不了 CPU。

### 解法空間

把 CPU 重活從 event loop 移開的辦法，按隔離強弱排：

- **worker_threads**：同行程內多 isolate，可用 `SharedArrayBuffer` 共享記憶體（零拷貝傳大資料）、`MessagePort` 傳訊息。最輕量的平行 JS。
- **cluster / 多行程**：fork 多個完整 Node 行程，各有 event loop，主要用來**水平擴展網路請求**（每行程吃一顆核），靠 OS 在多核上排程。記憶體隔離強但不共享，行程間要 IPC（官方 `worker_threads` 與 cluster 文件區分：worker threads 為 CPU 密集計算、cluster 為擴展 I/O 連線）。
- **child_process / 外部進程**：把重活丟給獨立程式（甚至別的語言），最強隔離，但啟動與序列化成本最高。
- **卸載到外部服務 / 佇列**：根本不在請求路徑上算——把任務丟進佇列，由背景 worker 機群處理（見領域 A 的訊息交付）。重活與請求脫鉤。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| libuv thread pool（預設 4） | fs/dns/crypto/zlib 自動非阻塞 | 偶發檔案/雜湊操作 | 只 4 條、不能丟任意 JS；滿了就排隊 |
| worker_threads | 真平行跑 JS、可共享記憶體 | 請求內的 CPU 重活（轉碼、解析） | 啟動約數十 ms；資料要 transfer/copy；數量過多反而搶核 |
| cluster / 多行程 | 多核擴展網路請求、記憶體隔離 | 吃滿多核的 I/O 伺服器 | 不共享記憶體；連線狀態需 sticky/backplane（見領域 C） |
| 卸載到佇列 + 背景 worker | 重活完全離開請求路徑 | 可非同步完成的長任務 | 引入交付語意/重試問題（見領域 A） |

### 何時需要

判準：**這段計算會在事件迴圈執行緒上跑超過幾毫秒嗎？** 是，就要外送；否，留在原地（外送本身有成本，得不償失）。

- 單次計算 < 1 ms（小 JSON、簡單轉換）：別動，外送的序列化與排程開銷比計算本身還大。
- 單次計算數十至數百 ms（影像縮放、加密、大批資料聚合）：用 worker_threads，避免凍結其他請求。
- 計算秒級或可延後（報表、批次 ETL）：別放請求路徑，丟佇列由背景 worker 跑（見領域 A）。

worked example：UV_THREADPOOL_SIZE 預設 4 的算術陷阱。一個 API 每請求做一次 `crypto.pbkdf2`（密碼雜湊），假設單次約 100 ms。pbkdf2 走 libuv thread pool（4 條）。若同時湧入 8 個請求，前 4 個並行各約 100 ms，後 4 個得等前面騰出執行緒，總計約 200 ms——第 5–8 個請求的延遲憑空翻倍，且這跟 event loop 沒被你的 JS 卡住無關，是 thread pool 被佔滿。把 `UV_THREADPOOL_SIZE` 調到 8（並有 ≥8 核可用）能讓 8 個請求同時做完，延遲回到約 100 ms。這是「Node 在高並發雜湊下突然變慢」最常見的真兇。

### 常見誤解與陷阱

- **「開越多 worker 越快」**：worker 數超過 CPU 核心數後，它們互相搶核、context switch 增加，吞吐反而下降。對齊核心數（或核心數 ± 1）通常最佳。
- **「worker 之間記憶體共享很便宜」**：只有 `SharedArrayBuffer` 是零拷貝；一般物件透過 `postMessage` 走結構化複製（structured clone），傳大物件會有可觀的序列化成本。
- **「worker_threads 能擴展網路吞吐」**：擴展每秒處理的網路請求數用 cluster（多行程吃多核），worker_threads 是給「單一請求內的 CPU 重活」。用錯模組是常見誤配。
- **「調大 UV_THREADPOOL_SIZE 一定更快」**：池大於可用核心數時，多出來的執行緒只是在搶 CPU、徒增切換；它解的是「並發慢操作數 > 4」的排隊問題，不是讓單一操作變快。
- **把阻塞工作塞回主執行緒收尾**：worker 算完，結果回到主執行緒若又做一次同步重活（如再 stringify 一個巨物件），等於白搬。

### 延伸閱讀

- Node.js 官方 `worker_threads` 文件：https://nodejs.org/api/worker_threads.html
- Node.js 官方 `cluster` 文件：https://nodejs.org/api/cluster.html
- libuv thread pool 設計（UV_THREADPOOL_SIZE，預設 4、最大 1024）：https://docs.libuv.org/en/v1.x/threadpool.html

## race condition 與原子性（跨 DB / cache / runtime）

### 定義與原理

race condition（競態）：多個執行單元**並發存取共享狀態**，最終結果取決於它們交錯執行的時序，於是出現「有時對、有時錯」的不確定 bug。原子性（atomicity）是它的解藥之一：一個操作要嘛完整發生、要嘛完全不發生，中途沒有其他單元能看到半成品或插隊。

最經典的競態是 **lost update（更新遺失）**：兩個單元各自「讀 → 改 → 寫」同一個值。

```text
（示意，非可執行——counter 初值 = 100）
時間 ─────────────────────────────────────────►
T1:  read 100 ───────► +1 ───────► write 101
T2:         read 100 ──────► +1 ──────► write 101
                                        結果 = 101（應為 102，一次更新遺失）
```

兩次 `+1` 只生效一次，因為兩者都讀到舊值 100。修掉它的方式都是「讓讀-改-寫變原子」或「偵測到衝突就重來」。

致命的觀念是：**原子性不是只有 multi-thread 才需要操心。** 它有三個常被忽略的層次——

- **runtime 內**（同一行程多執行緒共享記憶體）：要 mutex / atomic 指令。
- **跨 cache**（多個應用實例打同一個 Redis）：要 Redis 原子操作或 WATCH/Lua。
- **跨 DB**（多個交易改同一行）：要交易隔離級別、行鎖、或樂觀並發控制。

即使你的 Node 服務是「單執行緒」、runtime 內不會有資料競爭，只要它**跑多個實例打同一個 DB 或 Redis**，競態就從 runtime 搬到了資料層——單執行緒不是免死金牌。

### 解法空間

讓「讀-改-寫」安全的辦法，按「樂觀 vs 悲觀」與所在層次分：

- **悲觀鎖（先鎖再改）**：DB 的 `SELECT ... FOR UPDATE` 鎖住行，其他交易得等（PostgreSQL 文件）；runtime 內的 mutex；分散式鎖（見領域 M）。簡單、衝突多時穩，但有等待與死結風險。
- **樂觀並發控制（先做、提交時檢查衝突）**：帶版本號/ETag，更新時 `WHERE version = ?`，沒中就重試（CAS 思路）。衝突少時零等待，衝突多時重試風暴（見領域 B 的樂觀 vs 悲觀並發控制）。
- **單一原子操作（讓資料庫/快取替你保證）**：用 `UPDATE counter SET n = n + 1`（DB 在行鎖下原子完成）、Redis 的 `INCR`（單執行緒天然原子）取代「讀回來自己加再寫」。最省事，但只適用於能用單條原子指令表達的更新。
- **交易隔離級別**：升到 `REPEATABLE READ`/`SERIALIZABLE`，讓 DB 偵測序列化異常並中止其一（PG 用 SSI，應用須準備 retry；見領域 B）。
- **冪等化**：讓重複執行不造成額外效果，把「正確性」需求降級成「不要重複」（見領域 A 的冪等）。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| DB 原子 `UPDATE x = x + 1` | 行鎖下原子、無 lost update | 計數、餘額增減 | 僅限可用單條 SQL 表達的更新；高併發同一行成熱點 |
| `SELECT ... FOR UPDATE`（悲觀） | 鎖定行直到交易結束 | 讀後要算再寫的複雜更新 | 等待＋死結風險；預設只鎖行不擋純讀（PG READ COMMITTED） |
| 版本號 / ETag（樂觀） | 偵測衝突、無鎖等待 | 衝突率低、寫少讀多 | 衝突時要重試；重試需冪等，否則放大副作用 |
| Redis `INCR` / `INCRBY`（原子） | 單執行緒天然原子 | 跨實例計數、限流計數 | 多步邏輯仍需 WATCH/Lua；非持久化下崩潰可能丟更新 |
| Redis `WATCH`/`MULTI`/`EXEC`（CAS） | 監看的 key 被改則交易中止 | 跨實例的讀-改-寫 | 是樂觀鎖，衝突時 EXEC 回 nil 要自己重試（Redis 文件） |
| Lua 腳本（Redis） | 整段腳本原子執行 | 複雜的條件式原子更新 | 腳本內別放慢操作，會卡住整個 Redis 單執行緒 |

### 何時需要

只要有「共享的可變狀態」且「多個單元可能並發改它」，就需要某種原子性保證。判準是**衝突的後果有多嚴重、衝突有多頻繁**：

- 後果嚴重（金額、庫存、配額）：必須有明確的原子性或衝突偵測，不能「賭它不會撞」。
- 衝突頻繁（熱門商品秒殺、全域計數器）：悲觀鎖會排長隊、樂觀鎖會重試風暴——這時要嘛用單條原子指令（DB `UPDATE`/Redis `INCR`）避開讀-改-寫，要嘛把熱點打散（分片計數）。
- 衝突罕見（用戶各改自己的資料）：樂觀並發控制最划算，多數時候零等待。
- 狀態完全不共享（每請求獨立、無全域可變狀態）：不需要任何同步——這也是「無狀態服務」好擴展的根因（見領域 J）。

worked example：限流計數器的競態。一個 API 用「讀 Redis 計數 → 在應用層 +1 → 寫回」做每秒限流，10 個應用實例並發。某秒湧入 1000 個請求，這些「讀-改-寫」彼此交錯，實際寫回的最終值可能只有約 200–300（大量更新互相覆蓋），於是限流形同虛設、放行遠超上限。改用 Redis 單條 `INCR`（單執行緒原子，每次必定 +1），1000 個請求精確得到 1…1000，超過閾值準確擋下——把「應用層讀-改-寫」換成「資料層原子指令」，競態消失。

### 常見誤解與陷阱

- **「Node 單執行緒所以沒有 race condition」**：runtime 內也許沒有，但跨多實例打同一 DB/Redis、或一個 async 流程中 `await` 之間狀態被另一個流程改掉，照樣競態。`await` 是一個讓出點，等於把臨界區切開了。
- **「加了交易就安全」**：交易給的是 ACID，但**預設隔離級別擋不住 lost update / write skew**。PG 預設 READ COMMITTED、MySQL 預設 REPEATABLE READ，兩者語意不同，要的保證不對就得顯式提級（見領域 B）。
- **「Redis 操作都是原子的」**：單條指令是（單執行緒），但「`GET` 完在應用層算再 `SET`」這個組合不是——中間別的 client 會插隊，要用 `WATCH`/Lua。
- **「樂觀鎖一定比悲觀好」**：衝突率高時樂觀鎖不斷重試，可能比悲觀鎖更糟（CPU 與延遲全耗在重試）。選哪個取決於衝突率，不是教條。
- **重試不冪等**：樂觀鎖/原子失敗後重試，若重試的操作本身有副作用（再發一封信、再扣一次款），就把競態 bug 換成重複 bug（見領域 A 的冪等）。

### 延伸閱讀

- Redis 官方 Transactions 文件（WATCH/MULTI/EXEC 與 CAS）：https://redis.io/docs/latest/develop/using-commands/transactions/
- PostgreSQL 官方 Explicit Locking 文件（`SELECT FOR UPDATE` 等）：https://www.postgresql.org/docs/current/explicit-locking.html
- Martin Kleppmann, *Designing Data-Intensive Applications*, ch.7（lost update / write skew 的系統性討論）

## 並發模型比較（thread / event-loop / actor / coroutine / CSP 的取捨）

### 定義與原理

「並發模型」是一個語言/runtime 決定「並發單元是什麼、它們之間怎麼通訊、怎麼避免共享狀態出錯」的整套設計。同樣是「同時做很多事」，五大主流模型給出五種不同答案，差別歸結為兩條軸：**(1) 通訊靠共享記憶體還是靠傳訊息；(2) 切換靠 OS 搶佔還是靠協作讓出。**

- **thread（共享記憶體＋搶佔）**：並發單元是 OS 執行緒，共用同一記憶體，靠鎖/atomic 同步，OS 強制切換。最貼近硬體、真平行，但共享記憶體 ＋ 鎖是 bug 與死結溫床。
- **event-loop（單執行緒＋協作）**：並發單元是 callback/Promise，一條執行緒協作式交錯，無共享記憶體競爭（見 event loop）。極省資源，但 CPU 重活會卡死、回呼風格較難寫。
- **actor（傳訊息＋各自狀態）**：並發單元是 actor，每個 actor 私有狀態、只透過非同步訊息溝通（mailbox），不共享記憶體。天生分散式友善、容錯（監督樹），但訊息傳遞延遲、無背壓時 mailbox 會爆。代表：Erlang/Elixir、Akka。Actor model 由 Carl Hewitt 等於 1973 提出、Gul Agha 1986 形式化。
- **coroutine（協作式輕量單元）**：並發單元是協程，由 runtime 在少量 OS 執行緒上多工，程式碼長得像同步阻塞但執行時非阻塞。海量輕量並發、可讀性好，但若協程裡呼叫真阻塞的系統呼叫會「漏」回卡 OS 執行緒。代表：Go 的 goroutine（M:N 排程，見下）、Kotlin coroutine、Python asyncio。
- **CSP（透過 channel 傳訊息）**：並發單元透過具名 **channel** 同步傳值通訊，強調「不要用共享記憶體來通訊，要用通訊來共享記憶體」。CSP 由 Tony Hoare 於 1978 提出；Go 的 `goroutine + channel` 是其最知名的現代實作。與 actor 的核心差別：actor 的一等公民是「行為者」（送到具名 actor 的 mailbox），CSP 的一等公民是「通道」（送進匿名 channel，誰收不指定）。

Go 的混合排程值得單獨一提：它是 **GMP 模型**——G（goroutine）、M（OS 執行緒）、P（邏輯處理器，數量＝`GOMAXPROCS`，預設等於 CPU 核心數；Go 1.25 起改為 cgroup-aware，容器有 CPU limit 時取較小值）。runtime 把海量 G 多工到少量 M 上；Go 1.14 起加入**訊號式非同步搶佔**（sysmon 背景執行緒偵測到某 goroutine 連續跑約 10 ms 未讓出，就送 `SIGURG` 強制切換），補上純協作式「跑死迴圈卡住排程」的洞。

### 解法空間

| 模型 | 並發單元 | 通訊方式 | 切換 | 代表 runtime |
|---|---|---|---|---|
| thread | OS 執行緒 | 共享記憶體＋鎖 | OS 搶佔 | Java、C++、POSIX threads |
| event-loop | callback/Promise | 共享單執行緒記憶體 | 協作（I/O 讓出） | Node.js、Nginx、Redis |
| actor | actor | 非同步訊息（mailbox） | runtime 排程 | Erlang/Elixir、Akka |
| coroutine | 協程/goroutine | 視語言（channel 或共享） | 協作＋（Go）搶佔 | Go、Kotlin、Python asyncio |
| CSP | 行程（goroutine） | 同步 channel | 協作＋搶佔 | Go、occam |

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| thread（共享記憶體） | 真平行、最低抽象開銷 | CPU 密集、需精細控制 | 共享狀態需鎖；死結/競態風險高；執行緒貴 |
| event-loop | 海量 I/O 並發、無資料競爭、極省記憶體 | I/O 密集、大量連線 | CPU 重活卡死全線；回呼/async 風格 |
| actor | 狀態隔離、容錯（監督樹）、易分散 | 高容錯、有狀態並發、分散式 | 訊息延遲；mailbox 無界會爆；非同步難 debug |
| coroutine（如 goroutine） | 海量輕量並發＋線性可讀性＋多核 | 高並發＋混合 I/O 與 CPU | 阻塞系統呼叫會漏；channel 用錯易 deadlock |
| CSP（channel） | 通訊即同步、無共享記憶體競爭 | 管線式並發、生產者-消費者 | 無界 channel 失去背壓；select 邏輯易出錯 |

### 何時需要

模型多半由你選的語言/平台決定，但理解取捨能讓你在「同一平台內怎麼用」與「跨平台選型」時選對：

- **I/O 密集、海量連線、團隊熟 JS**：event-loop（Node）夠用且省資源；CPU 重活外送 worker（見 thread pool / worker threads）。
- **高並發＋同時有可觀的 CPU 計算、要吃滿多核**：coroutine ＋ M:N 排程（Go）最甜——線性程式碼、自動多核、搶佔保護。
- **高容錯、有狀態、節點可能掛掉要自癒、天然分散式**：actor（Elixir/Erlang）——監督樹讓「讓它崩潰再重啟」成為一等策略。
- **CPU 密集、需貼硬體精細調優、低層控制**：thread（C++/Java + 執行緒池）。
- **生產者-消費者管線、明確的資料流階段**：CSP channel 把每階段串成 pipeline，背壓靠有界 channel 自然成立。

worked example：同樣服務 50,000 個並發長連線。thread-per-connection 模型每執行緒堆疊約 1 MB，光堆疊約 50 GB ＋ 5 萬條執行緒的排程開銷——不可行。event-loop（Node）一條主執行緒 ＋ epoll 照看 5 萬 fd，記憶體以數百 MB 計，但只用單核、且任一 CPU 重活全線凍結。goroutine（Go）每個 goroutine 初始堆疊僅約 2 KB（按需成長），5 萬個約 100 MB 起，且 GMP 把它們攤到所有核心、有搶佔保護不怕單一卡死。同一個負載，三種模型的記憶體從 50 GB 到 100 MB、多核利用從 1 核到 N 核——模型選擇直接決定一個量級的差異。

### 常見誤解與陷阱

- **「actor 和 CSP 是同一回事」**：都靠傳訊息、都避免共享記憶體，但一等公民不同——actor 送給「具名的行為者」（有 mailbox、非同步），CSP 送進「匿名 channel」（誰收不指定，經典 CSP 為同步交會）。
- **「Go 的並發 ＝ CSP」**：Go 提供 channel（CSP 風）也提供 `sync.Mutex`/共享記憶體（thread 風），實務常混用，不是純 CSP。
- **「goroutine 是免費的」**：每個初始約 2 KB 不代表無限開——數百萬個仍吃記憶體與排程，且每個若各持一個 DB 連線會瞬間耗盡連線池（見領域 N 的連線池）。
- **「event-loop 模型不可能死結」**：無鎖確實不會有傳統死結，但兩個 async 流程互等對方的 Promise（A 等 B 的結果、B 等 A）照樣 deadlock。
- **「換個並發模型就能解決效能問題」**：模型決定的是「並發結構與省不省資源」，CPU 瓶頸換模型也救不了（見 並發 ≠ 平行）——先確認瓶頸在等待還是在計算，再談選模型。
- **「coroutine 永遠不會卡 OS 執行緒」**：協程在純非阻塞操作上不卡，但呼叫一個**真阻塞的 C 函式庫或系統呼叫**時會佔住底層 M；runtime 多半會補開執行緒救場，但這條協程期間就不是「免費讓出」了。

### 延伸閱讀

- C. A. R. Hoare, "Communicating Sequential Processes"（CACM 1978，CSP 原始論文）：https://dl.acm.org/doi/10.1145/359576.359585
- Carl Hewitt et al., "A Universal Modular ACTOR Formalism for Artificial Intelligence"（1973，actor model 原始論文）：https://dl.acm.org/doi/10.5555/1624775.1624804
- The Go Memory Model 與 scheduler 設計（GMP、搶佔）：https://go.dev/ref/mem
- Rob Pike, "Concurrency is not Parallelism"：https://go.dev/blog/waza-talk
