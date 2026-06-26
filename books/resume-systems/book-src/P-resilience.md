# P · 韌性與容錯

韌性領域處理的問題是：當一個依賴變慢、變死、或部分過載時，怎麼讓「壞掉的只壞一塊、不要拖垮整個行程」，以及怎麼讓服務在上下線之間不掉資料、不丟流量。本檔含五個條目：timeout / deadline / budget（單次呼叫的等待上限與跨層預算）、bulkhead 艙壁隔離（把資源切艙，故障不蔓延）、health check（liveness / readiness——本書 health check 的 owning 條目）、graceful shutdown（行程退場時把進行中的工作收尾乾淨）、fallback · 降級（本書通用降級的 owning 條目，依賴不可用時退回次等正確的結果）。邊界：重試／退避／jitter 的做法在領域 A（本檔只引用，不重講退避公式）；circuit breaker 的三態機制在領域 E（本檔把它當「降級的觸發機制」引用）；過載側的 backpressure / load shedding / rate limiting 也在領域 E。

## timeout / deadline / budget

### 定義與原理

任何跨越行程邊界的呼叫（網路、子行程、檔案鎖）都可能永遠不回。沒有上限的等待不是「慢」，是「掛起」——一個 worker 卡在 socket recv 上不會釋放執行緒、不會釋放連線、不會釋放記憶體。**timeout** 就是替這個等待設一個硬上限：超過就放棄、回一個明確的錯誤，把資源還回去。

三個詞常被混用，但語意不同：

- **timeout（逾時）**＝相對時長：「從現在起最多等 2 秒」。它是 socket / library 層的設定，每一跳重新計時。
- **deadline（截止點）**＝絕對時間點：「最晚到 12:00:03.250 為止」。它的好處是可以**跨跳傳遞**——上游把 deadline 算出來，往下游一路帶下去，每一層只要看「現在離 deadline 還剩多少」就知道自己還能花多久。gRPC 內部正是把 timeout 轉成 deadline，再在跨服務時換回「扣掉已耗時間的剩餘 timeout」傳給下游，藉此繞開兩台機器時鐘不同步的問題（2026-06）。
- **budget（預算）**＝把一個端點的總時間預算，分配給它扇出的多個下游呼叫，使各段相加不超過對外承諾。常見的還有 **retry budget**：限制重試佔總請求的比例，避免重試風暴（見「重試、退避、jitter」，領域 A）。

第一原理：**逾時是分散式系統裡偵測「對方死了還是只是慢」的唯一手段**——你無法區分「對方崩潰」與「對方還在算、只是很慢」，只能設一個你願意等的上限，過了就當它失敗。所以 timeout 值的本質不是「對方多久會回」，而是「我願意為這個呼叫凍結多少資源」。

### 解法空間

- **固定 timeout（per-call）**：每個出站呼叫各設一個常數上限。最簡單，但每跳獨立、不會累加，多層串起來總時間可能爆掉。
- **deadline 傳遞（deadline propagation）**：入站請求帶一個 deadline，往下游所有出站呼叫一路傳。下游發現 deadline 已過就直接放棄、不浪費算力。gRPC 在 Java／Go 預設會傳，C++ 等需顯式開啟（2026-06）。
- **time budget 拆分**：對外承諾 p99 = 1s 的端點，內部扇出 A、B、C 三個下游，就把 1s 拆成「A 400ms、B 400ms、留 200ms 給序列化與餘裕」，而不是三個都設 1s。
- **連線 vs 讀取分離**：connect timeout（建連線）通常該短（毫秒級，連不上要快速失敗），read/idle timeout（等回應）按業務 p99 設。兩者混成一個值是常見錯誤。
- **可取消（cancellation）**：逾時除了「不再等」，最好還能向下游送取消訊號（gRPC cancellation、HTTP 斷連、context.Done()），讓下游也停手、別繼續燒 CPU 算一個沒人要的結果。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 固定 per-call timeout | 單跳資源不會無限凍結 | 扁平架構、單跳呼叫 | 多層串接時總時間 = 各層相加，可能遠超對外承諾 |
| deadline 傳遞 | 全鏈路共享一個截止點，過期的請求全鏈路一起放棄 | 微服務深鏈、gRPC | 需框架支援＋下游檢查 deadline；時鐘偏移要靠「剩餘 timeout」換算化解 |
| time budget 拆分 | 對外延遲承諾可被內部各段加總滿足 | 一個端點扇出多個下游 | 拆分要留餘裕（序列化、排隊、GC）；某段超支會吃掉別段的額度 |
| connect/read 分離 | 連不上快速失敗、慢回應按業務容忍 | 所有外部呼叫 | 兩個值要分開設；很多 client 預設只有一個總 timeout |

**worked example**：一個 API 端點對外承諾 p99 ≤ 1000ms。它同步呼叫服務 A 再呼叫服務 B（序列），各設 timeout = 1000ms。某次 A 卡在 950ms 才回，B 又花 900ms——總共 1850ms，遠超承諾，但兩個呼叫各自「都沒逾時」，監控看起來健康。換成 deadline 傳遞：入站帶 deadline = now + 1000ms，呼叫 A 時剩 1000ms、A 用掉 950ms 回來後剩 50ms，呼叫 B 時把「50ms」當 timeout 傳下去，B 在 50ms 內沒回就立刻 DEADLINE_EXCEEDED——整個請求準時失敗，而不是悄悄超時一倍。

### 何時需要

- **任何跨行程邊界的呼叫都該有 timeout**，沒有例外。預設無限等是最危險的設定（gRPC client 預設不設 deadline，等於可能等到天荒地老，2026-06）。
- **deadline 傳遞**在三層以上的同步呼叫鏈才值得引入；單跳系統用固定 timeout 就夠，硬上 deadline propagation 是 over-engineering。
- **time budget 拆分**在「一個對外端點扇出多個內部依賴、且有明確 SLO」時才需要刻意算；內部背景工作不必。

### 常見誤解與陷阱

- **「timeout 設大一點比較安全」**——反了。timeout 越大，一個慢依賴能凍結的資源越多、越久，過載時越容易把執行緒池／連線池吃光、引發連鎖。timeout 該設在「正常 p99 之上留一點餘裕」，不是「絕不誤殺」。
- **多層 timeout 不協調**：外層 timeout 比內層短，內層還在重試、外層已經放棄並回錯給使用者——內層的重試全是白工，還在持續加壓。原則：**外層 timeout 要 ≥ 內層 timeout × 內層重試次數**，否則重試永遠來不及完成。
- **逾時了卻沒取消下游**：client 端 timeout 只是「我不等了」，下游往往還在算。沒有 cancellation 傳遞，過載時這些「沒人要的計算」會持續燒資源。
- **把 connect timeout 和 read timeout 混為一談**：連線階段該秒級甚至更短地失敗，回應階段可能要等業務邏輯跑完，兩者量級差很多。
- **重試與 timeout 各自為政**：timeout 是單次上限，重試是再試幾次，兩者要一起算進 budget（重試的退避做法見「重試、退避、jitter」，領域 A）。

### 延伸閱讀

- gRPC, "Deadlines" — https://grpc.io/docs/guides/deadlines/
- gRPC blog, "gRPC and Deadlines" — https://grpc.io/blog/deadlines/
- Google SRE Book, "Handling Overload"（client-side throttling、retry budget）— https://sre.google/sre-book/handling-overload/

## bulkhead 艙壁隔離

### 定義與原理

bulkhead（艙壁）來自造船：船體用隔艙壁分成多個獨立水密艙，一個艙破洞進水，水不會漫到其他艙，船因此不沉。Michael Nygard 在 2007 年的《Release It!》把它引進軟體穩定性模式，與 circuit breaker、timeout 並列。

軟體裡的「進水」是**資源耗盡**。最典型的場景：一個服務有一個共用的執行緒池（或連線池），它對外呼叫 A、B、C 三個下游。某天 A 變慢，所有打 A 的請求都卡住、佔住執行緒不放，執行緒池很快被 A 的慢請求填滿——結果連只需要 B、C 的請求也拿不到執行緒、一起失敗。**A 的局部故障透過共用資源池蔓延成全域故障**。bulkhead 的解法：把資源切成幾個獨立的艙（A 一個池、B 一個池、C 一個池），A 的池滿了只影響 A，B、C 照常服務。

第一原理：**共用資源是故障傳播的管道**。隔離的代價是資源利用率下降（每個艙都要預留容量、整體用不滿），換來的是「故障被框在一個艙裡」。這是典型的保證換取捨——你用一部分閒置容量，買到「壞一塊不壞全部」。

### 解法空間

- **執行緒池隔離（thread-pool bulkhead）**：每個下游依賴一個獨立執行緒池。慢依賴只能塞滿自己的池。隔離最徹底（連阻塞都被框住），但執行緒有記憶體與切換成本，池子多了開銷大。
- **信號量隔離（semaphore bulkhead）**：不開新執行緒，用一個計數信號量限制「同時打某依賴的並發數」，超過就立即拒絕。輕量、無額外執行緒，但不能隔離阻塞（呼叫仍在原執行緒上跑），不適合會長時間阻塞的呼叫。
- **連線池分離**：給不同依賴／不同租戶開獨立的 DB／HTTP 連線池，一個用戶把連線打爆不會餓死其他人。
- **行程／實例隔離**：把高風險或高優先的工作負載拆到獨立的 deployment／node pool，物理上不共享 CPU／記憶體。最強隔離，成本也最高。
- **租戶／優先級分艙**：把「付費租戶」「免費租戶」、「線上請求」「背景批次」分到不同艙，避免一類流量餓死另一類（noisy neighbor）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 執行緒池隔離 | 慢／阻塞依賴被框在自己池中，連阻塞都不外溢 | 會阻塞、且必須隔離阻塞的同步呼叫 | 每池一組執行緒，記憶體＋context switch 開銷；池數要克制 |
| 信號量隔離 | 限制單依賴並發數、立即拒絕超額 | 非阻塞或短呼叫、想要輕量隔離 | 不隔離阻塞（呼叫仍在原執行緒），長阻塞會拖垮原池 |
| 連線池分離 | 一個依賴／租戶耗盡連線不波及其他 | 多依賴共用 DB／外部 API | 連線總數 = 各池之和，別超過後端上限 |
| 行程／實例隔離 | CPU／記憶體層級完全隔離 | 高風險或高 SLO 負載 | 成本最高、運維更複雜、資源利用率最低 |

**worked example**：一個服務有 200 條工作執行緒，同時服務「下單」與「查歷史」兩條路徑，共用同一個池。某天「查歷史」打的報表 DB 變慢，每個查歷史請求平均佔住執行緒 4 秒。若查歷史的入站速率是 60 req/s，依 Little's law 它穩態會佔用約 60 × 4 = 240 條執行緒——超過 200，整池被填滿，下單請求也排不進來、一起超時。改成 bulkhead：給「查歷史」分一個上限 50 的信號量艙，第 51 個查歷史請求直接被拒（回降級結果），下單路徑的執行緒因此最多被查歷史佔走 50 條、永遠留得住 150 條給下單。局部慢被框住，下單不受影響。

### 何時需要

- **一個服務混跑多種工作負載、且它們重要性／延遲特性差很多時**（線上 vs 批次、付費 vs 免費、關鍵路徑 vs 次要功能）——這是 bulkhead 最該出手的場景。
- **下游依賴有「可能單獨變慢」的歷史**，而它和其他呼叫共用資源池時。
- **不需要**：單一同質工作負載、只有一個下游、或流量小到資源從不接近上限——這時切艙只是徒增閒置與複雜度。

### 常見誤解與陷阱

- **以為信號量隔離能擋住阻塞**：信號量只限並發數，呼叫還是在原執行緒上阻塞。要隔離「阻塞本身」必須用獨立執行緒池。會長阻塞的呼叫用信號量艙，等於沒隔離。
- **艙切太細**：每個下游都一個專屬執行緒池，池數膨脹、每池都要留 buffer，整體資源利用率崩掉，還更難調參。隔離有邊際效益遞減，按「故障爆炸半徑」分艙、別按「依賴數量」分。
- **只切了應用層、忘了共用底層**：應用切了三個執行緒池，但它們連到同一個 DB 連線池、或同一個下游實例——底層仍是共用管道，故障照樣穿透。隔離要一路切到真正的瓶頸資源。
- **把 bulkhead 當 circuit breaker**：兩者互補不互替。bulkhead 限制「故障能佔多少資源」，circuit breaker 在偵測到故障後「直接快速失敗、不再嘗試」（三態機制見 circuit breaker，領域 E）。實務上常一起用。
- **艙滿之後沒有降級**：艙的並發到頂、請求被拒，但沒給 fallback，使用者看到的就是硬錯誤。拒絕之後要接降級（見「fallback · 降級」）。

### 延伸閱讀

- Wikipedia, "Bulkhead pattern" — https://en.wikipedia.org/wiki/Bulkhead_pattern
- Michael Nygard, *Release It!*（Stability Patterns 講義 PDF）— https://cdn.oreillystatic.com/en/assets/1/event/79/Stability%20Patterns%20Presentation.pdf
- Microsoft Azure Architecture Center, "Bulkhead pattern" — https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead

## health check（liveness / readiness）

### 定義與原理

health check 是讓編排器／負載均衡器**從外部判斷一個實例現在能不能用**的探測端點。本書在這裡 owning health check 的機制定義；分散式失敗偵測的視角見領域 J、K8s probe 的設定欄位見領域 Q，那兩處只從各自角度引用、不重講。

核心是把「活著」和「能服務」分成兩個正交的問題，對應兩種探針：

- **liveness（存活）**：這個行程是不是壞死了、需要重啟？liveness 失敗的唯一動作是**殺掉並重啟**。它要回答的是「重啟能不能救」——deadlock、記憶體無法回收、事件迴圈卡死這類「只能重來」的狀態。
- **readiness（就緒）**：這個實例現在能不能接流量？readiness 失敗的動作是**把它從負載均衡的後端摘掉**（不重啟）。它回答「現在送請求過來會不會失敗」——還在暖機、下游依賴暫時斷了、佇列積壓過深、正在優雅退場。
- **startup（啟動，K8s 特有）**：應用是不是「啟動完成」了？只在啟動期跑，沒成功前不跑 liveness／readiness，給慢啟動的應用一段不被 liveness 誤殺的窗口（2026-06）。

第一原理：**「行程在跑」不等於「行程能服務」**。一個 JVM 可以活得好好的，但它連不上 DB、所以每個請求都會失敗——這時它該被摘流量（readiness fail），但不該被重啟（重啟救不了 DB）。把這兩件事混成一個 `/health` 端點，是最常見的健康檢查設計錯誤。

### 解法空間

- **TCP 探測**：能不能建 TCP 連線。最弱——port 開著不代表應用邏輯正常。
- **HTTP 探測**：打一個 HTTP 端點看 2xx。最常用。關鍵在「這個端點檢查什麼」：是只回 200（淺），還是真的去確認關鍵依賴可用（深）。
- **exec 探測**：在容器內跑一個命令、看 exit code。適合沒有 HTTP 介面的工作負載。
- **gRPC 探測**：用 gRPC Health Checking Protocol 的標準 health service。
- **淺 vs 深 health check**：淺＝只證明行程在跑（適合 liveness）；深＝連同關鍵下游一起檢查（適合 readiness，但深 check 會放大連鎖故障，見陷阱）。
- **K8s 三探針的標準分工**：startup 罩住啟動期、liveness 管重啟、readiness 管摘流量——這是把上面語意落到設定的標準做法（欄位細節見領域 Q）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| TCP 探測 | port 可連 | 沒有 HTTP 的服務、最低限度存活 | port 開著 ≠ 應用正常，最弱 |
| 淺 HTTP（只回 200） | 行程在跑、事件迴圈沒卡死 | liveness | 不能驗業務能力；用在 readiness 會放行壞掉的實例 |
| 深 HTTP（含下游檢查） | 關鍵依賴此刻可用 | readiness | 下游抖一下會讓整批實例同時 unready；要小心連鎖（見陷阱） |
| gRPC health protocol | 標準化、與 gRPC 生態整合 | gRPC 服務 | 需 client/平台支援 |
| startup probe | 啟動期不被 liveness 誤殺 | 慢啟動應用 | K8s 特有；忘了設會在暖機時被反覆重啟 |

**worked example**：K8s 預設 readiness 探針 `periodSeconds=10`、`failureThreshold=3`、`timeoutSeconds=1`、`successThreshold=1`（2026-06）。某實例的下游 DB 連線斷了，深 readiness 開始回 503。要連續 3 次失敗、每次間隔 10 秒，才會被判 unready——也就是說最壞情況下，這個壞實例還會被送進約 3 × 10 = 30 秒的流量才被摘掉。若想更快摘流量，得把 `periodSeconds` 與 `failureThreshold` 調小，但調太敏感又會被瞬時抖動誤摘——這就是「偵測速度 vs 抗抖動」的取捨，沒有免費的快。

### 何時需要

- **任何被編排器（K8s 等）或 LB 管生命週期的服務**都該有 readiness——否則流量會被送進「還沒準備好」或「正在退場」的實例。
- **liveness 要保守**：只在「重啟確實能救」的狀態下失敗。很多服務其實不需要 liveness，或該設得非常寬鬆（見陷阱）。
- **startup**：啟動時間明顯（載入大模型、跑 migration、暖快取）的應用才需要；秒級啟動的不必。

### 常見誤解與陷阱

- **liveness 和 readiness 用同一個端點**：最常見的錯。深 health check 接到 liveness，下游 DB 一抖，liveness 就失敗，K8s 把實例**重啟**——但重啟救不了 DB，於是所有實例陸續進 CrashLoopBackOff，把一次「DB 暫時不可用」放大成「整個服務反覆重啟、徹底癱瘓」。**liveness 用淺 check（只證明行程沒卡死），readiness 才掛下游依賴**。
- **liveness 太敏感造成連鎖重啟**：probe 的 `timeoutSeconds` 太短、`initialDelaySeconds` 太短，GC 暫停或暖機就被判死亡並重啟，K8s 的重啟退避是 10s、20s、40s…上限 5 分鐘（CrashLoopBackOff），連續 10 分鐘無事才重置——一旦進這個迴圈很難自己爬出來（2026-06）。慢啟動該用 startup probe 罩住、別靠調鬆 liveness。
- **深 readiness 引發 readiness 風暴**：所有實例的 readiness 都去 ping 同一個下游，下游一慢，所有實例同時 unready，服務後端瞬間歸零、流量無處可去——比「部分實例壞掉」更糟。共用下游的 readiness 要小心，必要時讓它「下游慢但本機還能服務快取／降級結果」時仍回 ready。
- **退場時 readiness 沒先翻 false**：實例收到關閉訊號卻沒先把 readiness 設成 fail，LB 還在送新流量過來（與優雅退場銜接，見「graceful shutdown」）。
- **把 health check 當監控告警源**：health check 是給機器做「上/下線」二元決策的，不是觀測指標。健康趨勢／SLO 屬可觀測性領域（領域 I），別混用。

### 延伸閱讀

- Kubernetes, "Configure Liveness, Readiness and Startup Probes" — https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- Kubernetes, "Liveness, Readiness, and Startup Probes"（概念）— https://kubernetes.io/docs/concepts/configuration/liveness-readiness-startup-probes/
- gRPC Health Checking Protocol — https://github.com/grpc/grpc/blob/master/doc/health-checking.md

## graceful shutdown

### 定義與原理

graceful shutdown（優雅退場）解決的問題是：行程被要求結束時（部署、縮容、節點重開），**不要硬斷正在進行的工作**。硬斷的後果是丟掉處理到一半的請求（使用者看到連線重置）、留下半完成的交易、消費者沒 ack 的訊息被重投、連線洩漏。優雅退場就是把「結束」變成一個有序流程：停止收新工作 → 把手上的工作做完（或安全交還）→ 釋放資源 → 退出。

在容器世界裡這個流程由訊號驅動。以 Kubernetes 為例（2026-06）：

1. Pod 被標記終止，kubelet 啟動 `preStop` hook，**同時**開始倒數寬限期計時器；待 `preStop` 完成後才對容器主行程送 **SIGTERM**（與 preStop 並行的是寬限期計時，不是 SIGTERM）。
2. 同時，Pod 被從 Service 的 EndpointSlice 移除——但這個移除是**最終一致**的，kube-proxy 更新 iptables／外部 LB 更新後端需要時間，這段時間內仍可能有新請求打進來。
3. 給一段寬限期 `terminationGracePeriodSeconds`（**預設 30 秒**）。
4. 寬限期一到還沒退出，送 **SIGKILL** 強殺、不再等。

第一原理：**SIGTERM 是「請你收尾」的禮貌請求，SIGKILL 是「時間到了強制結束」**。你只有寬限期那麼長的時間把事情做乾淨；應用必須主動捕捉 SIGTERM 並執行退場邏輯，否則預設行為（多數 runtime 收到 SIGTERM 直接退出）就等於硬斷。

### 解法空間

- **捕捉 SIGTERM 並排空（drain）**：監聽 SIGTERM，停止 accept 新連線／停止從佇列拉新訊息，等手上的請求做完再退。
- **先翻 readiness 為 false（pre-drain）**：退場第一步先讓 readiness 探針回失敗，把自己從 LB 後端摘掉，停止「新流量流入」，再開始排空已有請求（與 health check 銜接，見「health check」）。
- **preStop sleep**：在 preStop hook 放一個短 sleep（如 `sleep 10`），給 LB／kube-proxy 時間把這個 Pod 從後端拿掉，再讓 SIGTERM 開始排空——填補上面那個「EndpointSlice 移除是最終一致」的時間差。
- **連線排空（connection draining）**：對長連線（WebSocket、gRPC stream、SSE），主動發送關閉訊號（GOAWAY、close frame）讓 client 重連到別的實例，而不是等它自然斷。
- **訊息消費者的安全交還**：消費者退場時，對「已拉未 ack」的訊息不要 ack，讓 broker 重投給別人（依賴下游冪等，見「冪等」，領域 A）。
- **設對寬限期**：`terminationGracePeriodSeconds` 要 ≥ 最長的合理請求時間 + drain 時間；長批次工作要顯式調大，否則 30 秒到就被 SIGKILL。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 捕捉 SIGTERM + drain | 進行中請求做完才退、不硬斷 | 所有長駐服務 | 不處理 SIGTERM＝預設硬斷；drain 要有自己的逾時上限 |
| 先翻 readiness false | 退場期間不再被送新流量 | 被 LB／Service 管的服務 | 摘除是最終一致，仍需 preStop sleep 補時間差 |
| preStop sleep | 補上 LB 後端更新的傳播延遲 | K8s + 外部 LB／ingress | sleep 算進寬限期，要把它計入 `terminationGracePeriodSeconds` |
| 連線排空（GOAWAY/close） | 長連線優雅遷移、不集中斷線 | WebSocket／gRPC stream／SSE | client 要會處理重連；否則只是換個地方斷 |
| 消費者不 ack 交還 | 未完成訊息被重投、不遺失 | 訊息／工作佇列消費者 | 下游必須冪等，否則重投＝重複處理 |

**worked example**：一個 HTTP 服務 p99 請求耗時 800ms，`terminationGracePeriodSeconds` 用預設 30 秒。部署時的正確退場時序：收到終止 → preStop `sleep 5`（這 5 秒內 readiness 已翻 false、kube-proxy 把它從 iptables 移除，新流量停止流入，但舊連線上的請求繼續）→ SIGTERM 觸發應用停止 accept、把已收下的請求做完（最久約 800ms）→ 全部完成後主動退出，總共約 6 秒，遠在 30 秒寬限期內，零請求被硬斷。反例：應用沒捕捉 SIGTERM，收到就立刻退出——那些正在 800ms 處理中的請求全部連線重置，使用者直接看到 5xx／連線錯誤。

### 何時需要

- **任何處理線上請求或消費佇列的長駐服務**都需要——只要它會被重新部署／縮容（也就是幾乎所有服務）。
- **批次／長任務工作者**尤其需要把寬限期調大到任務時長之上，或設計成「可中斷後重續」（與持久化工作流呼應，見領域 K）。
- **真正無狀態、單次冪等、極短的函式**（如純查詢）容忍度高，被硬斷重試即可，優雅退場的收益較低——但「捕捉 SIGTERM 早點關連線」幾乎零成本，仍建議做。

### 常見誤解與陷阱

- **以為摘流量是瞬時的**：readiness 翻 false 到「LB 真的不再送流量」之間有傳播延遲（EndpointSlice 更新、kube-proxy 改 iptables、外部 LB 同步），這段時間還會有新請求進來。少了 preStop sleep，就會在退場瞬間丟掉一批新到的請求。
- **preStop 和 SIGTERM 的關係搞錯**：K8s 不會等 preStop 跑完才送 SIGTERM 嗎？——實際上 preStop 與寬限期計時同時開始，SIGTERM 在 preStop 完成後送出；但**整個寬限期是固定的**，preStop 用掉的時間會壓縮留給 drain 的時間。preStop sleep 太長會吃掉 drain 額度。
- **drain 沒有自己的上限**：等所有請求做完才退，但若有一個請求卡死（沒設 timeout，見「timeout / deadline / budget」），drain 永遠不結束，最後被 SIGKILL 硬殺，反而比主動截斷更糟。drain 要有自己的 deadline。
- **寬限期短於最長請求**：`terminationGracePeriodSeconds` 用預設 30 秒，但有些請求要跑 60 秒——這些請求必被 SIGKILL 截斷。寬限期要對齊真實的請求時長分布。
- **忽略 SIGTERM 直接被 SIGKILL**：應用沒裝訊號處理器，等於放棄優雅退場、每次部署都在硬斷流量。預設不等於安全。
- **退場時還在啟動新工作**：收到 SIGTERM 後仍從佇列拉新訊息／接新連線，等於邊關門邊進貨，永遠關不乾淨。退場第一步必須是「停止收新工作」。

### 延伸閱讀

- Kubernetes, "Pod Lifecycle"（Termination of Pods）— https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- Google Cloud Blog, "Kubernetes best practices: terminating with grace" — https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-terminating-with-grace
- CNCF, "Decoding the pod termination lifecycle in Kubernetes" — https://www.cncf.io/blog/2024/12/19/decoding-the-pod-termination-lifecycle-in-kubernetes-a-comprehensive-guide/

## fallback · 降級

### 定義與原理

本條是本書通用降級的 owning 條目。fallback（後備／降級）解決的問題是：當主路徑失敗或不可用時，**回一個次等但仍可用的結果**，而不是把錯誤直接甩給使用者。核心信念是「部分可用 > 完全不可用」——不能給最新最準的答案時，給一個稍舊、稍粗、或功能縮水的答案，往往遠勝於一個 500。

它和容錯其他原語的分工：timeout 決定「等多久放棄」、circuit breaker 決定「要不要直接快速失敗」（三態機制見領域 E）、bulkhead 決定「故障能佔多少資源」，而 **fallback 決定「放棄／失敗之後，端給使用者什麼」**。前三者是「怎麼偵測與框住故障」，fallback 是「故障已經發生，怎麼還能交付價值」。降級層級（graceful degradation）就是把「失敗」變成一條從「完整功能」到「最小可用」連續滑落的坡，而不是一個非黑即白的懸崖。

### 解法空間

- **回快取／陳舊資料（stale-while-error）**：主資料源掛了，回上次成功的快取值。即使過期也比沒有好（快取層降級見「多層快取與優雅降級」，領域 G——那裡只講快取面、機制在本條）。
- **回預設值／靜態值**：給一個保守的常數（如風控分數預設「需人工複審」、推薦清單回熱門榜）。
- **功能降級（feature degradation）**：關掉非核心功能保住核心。如電商在推薦服務掛掉時不顯示「猜你喜歡」，但下單照常。
- **降低品質**：回低解析度、少欄位、近似結果代替完整精確結果。
- **重導到備援來源**：主供應商掛了切次要供應商（可能更貴或更慢，但能用）。
- **明確失敗（fail loud）**：對「寧可不做也不能做錯」的操作（扣款、轉帳），不降級、直接回明確錯誤——降級在這裡是反模式（見何時需要）。
- **觸發機制**：fallback 由誰觸發？常見是 circuit breaker 跳開時走 fallback、或 timeout／exception 時走 fallback、或 bulkhead 艙滿被拒時走 fallback。

### 各方案的保證與取捨

| 方案/做法 | 效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| 回快取／陳舊資料 | 主源掛了仍有（過期的）答案 | 讀多、容忍少量陳舊 | 要標明「資料可能過期」；陳舊上限要可控，別回上古資料 |
| 回預設／靜態值 | 永遠有個保守答案 | 評分、推薦、配置類 | 預設值要「安全方向」偏（寧嚴勿鬆）；別讓預設掩蓋故障 |
| 功能降級 | 核心活著、非核心暫關 | 有明確核心/非核心之分的系統 | 要事先想清楚哪些是非核心，臨場分不出來 |
| 降低品質 | 用近似換可用 | 可接受近似的計算／媒體 | 使用者要能感知是降級版，避免誤以為是真值 |
| 切備援來源 | 換一條路繼續服務 | 有等價次要供應商 | 備援也要被測試（平時沒用＝退化的備援）；成本可能更高 |
| 明確失敗（不降級） | 不會給出錯誤的「成功」 | 金流、唯一性、強一致操作 | 對這類操作降級＝資料錯誤，必須 fail loud |

**worked example**：一個商品頁同步呼叫「個人化推薦」服務。推薦服務的 SLO 是 p99 = 50ms，但偶爾抖到 2 秒。若不設降級，商品頁的延遲會被推薦服務的長尾拖著走，p99 跟著爆。加上 fallback：對推薦呼叫設 timeout = 80ms，超時就回「全站熱門 Top 10」這個每 5 分鐘刷新一次的靜態榜單。結果：推薦健康時使用者看到個人化清單；推薦抖動時，超過 80ms 的請求改顯示熱門榜（稍舊、非個人化，但秒開）。商品頁 p99 因此被自己的 80ms timeout 封頂，不再受下游長尾牽連——這是「降級換延遲穩定性」的典型交換。

### 何時需要

- **使用者體驗能接受「次等正確」的讀路徑**：推薦、搜尋補全、個性化、儀表板、非交易型展示——這些是 fallback 的主場。
- **有明確的「核心 vs 非核心」邊界**時，功能降級能在故障時保住核心交易。
- **不該降級**：涉及金錢、唯一性、授權、強一致的寫操作。對「轉帳成功了嗎」這種問題，回一個「降級的猜測」比回明確錯誤糟糕得多——這類操作要 fail loud，讓上游決定重試或人工介入。
- **over-engineering 警訊**：給一個本來就很穩、且失敗時硬報錯也無妨的內部呼叫硬塞 fallback，增加的是「故障被靜默掩蓋」的風險，得不償失。

### 常見誤解與陷阱

- **fallback 把故障藏起來**：降級成功了，使用者沒感覺，監控也沒告警——於是主路徑壞了好幾天沒人知道，直到快取也過期才爆。**降級必須伴隨可觀測性**：每次走 fallback 都該計數／告警（fallback rate 是關鍵指標，見領域 I），讓「正在降級」是顯眼的，不是無聲的。
- **fallback 路徑自己也會失敗、卻沒人測**：備援來源、降級快取平時沒人走，真出事時才發現它早就壞了／配置漂移了。fallback 路徑要被定期演練（注入故障驗證），否則就是退化的安全網。
- **降級放大負載**：主源掛了，所有請求湧向 fallback（如全打那個熱門榜的快取），把 fallback 也壓垮——降級路徑的容量要能扛住「主路徑全倒」的流量，否則只是把雪崩換個方向。
- **對寫操作／金流降級**：把「不確定成功與否」降級成「假裝成功」，是製造資料不一致的捷徑。強一致與交易操作的正解是 fail loud，不是 fallback。
- **降級沒有恢復路徑**：切到備援後，主源恢復了卻沒切回去，長期跑在次等模式（成本更高或品質更差）。降級要有「主源恢復後自動回正」的機制（circuit breaker 的 half-open 探測正是做這件事，見領域 E）。
- **靜默回「空結果」當降級**：把錯誤吞掉、回空陣列，讓上游以為「真的沒資料」——這比拋錯更危險，因為錯誤被偽裝成正常的空狀態。降級要明確標示自己是降級結果。

### 延伸閱讀

- Wikipedia, "Graceful degradation"（fault tolerance）— https://en.wikipedia.org/wiki/Fault_tolerance#Graceful_degradation
- Michael Nygard, *Release It!*（Stability Patterns，含 fallback／steady state）講義 — https://cdn.oreillystatic.com/en/assets/1/event/79/Stability%20Patterns%20Presentation.pdf
- Google SRE Book, "Addressing Cascading Failures"（degradation、graceful behavior）— https://sre.google/sre-book/addressing-cascading-failures/
