# N · 網路與協定

本領域處理的問題是：兩個行程要在不可靠的網路上互相呼叫，要付出什麼代價、換到什麼保證。本檔含七個條目：HTTP 的三個世代（連線重用／多工／QUIC）、gRPC 怎麼拿 Protobuf 當 IDL、連線池、L4/L7 負載均衡、TLS/mTLS、DNS 與服務發現、service mesh。邊界：傳輸層之上的 API 設計（REST/版本化/分頁）在領域 H、即時雙向推送（WebSocket/SSE/WebRTC）在領域 C；本檔只管「位元組怎麼從 A 到 B、連線怎麼建立與分配」這一層。

## HTTP/1.1 · 2 · 3（keep-alive / 多工 / QUIC）

### 定義與原理

HTTP 是請求-回應的應用層協定。三個世代解的是同一件事的不同層次：**怎麼在一條（或多條）底層連線上塞進多個請求，而不讓彼此互相卡住**。

- **HTTP/1.1**（RFC 9112，原 RFC 2616/7230）引入 **keep-alive**（persistent connection）：一條 TCP 連線連續送多個請求，省掉每次重建連線的三向交握。但同一條連線上請求是**嚴格序列化**的——前一個回應沒回完，下一個請求不能發（pipelining 規格上允許但實務上幾乎沒人開，因為 server 仍須照順序回應，反而引入隊頭阻塞）。
- **HTTP/2**（RFC 9113，原 RFC 7540）引入**多工（multiplexing）**：一條 TCP 連線上開多個獨立編號的 **stream**，多個請求/回應的 frame 交錯傳輸，互不等待。解決了 HTTP/1.1 的應用層隊頭阻塞，也帶來 header 壓縮（HPACK）與 server push（後者已被主流廢棄）。
- **HTTP/3**（RFC 9114，2022-06 成為 Proposed Standard）把傳輸從 TCP 換成 **QUIC**（RFC 9000，2021-05），QUIC 跑在 UDP 上、自帶多工與加密。

關鍵第一原理是**隊頭阻塞（head-of-line blocking）發生在哪一層**：HTTP/1.1 是**應用層**隊頭阻塞；HTTP/2 消除了應用層的，但因為所有 stream 仍共用一條 TCP 連線，**一個 TCP 封包遺失會卡住該連線上所有 stream**（TCP 不知道 stream 的存在，把所有東西當一條 byte stream，遺失重傳期間後面全等）——這是**傳輸層**隊頭阻塞。HTTP/3 用 QUIC 的**每 stream 獨立遺失復原**徹底解掉它：丟包只影響該 stream（2026-06）。

### 解法空間

選哪個世代，本質是在四個維度上取捨：

- **連線重用**：1.1 keep-alive 已能省交握；2/3 在此之上再共用單一連線。
- **多工**：1.1 靠「開多條並行連線」（瀏覽器慣例每 host 約 6 條）模擬並行；2/3 靠單連線多 stream。
- **隊頭阻塞層級**：1.1 應用層／2 傳輸層（TCP）／3 無傳輸層隊頭阻塞。
- **連線建立成本**：TCP+TLS 1.3 新連線需 2-RTT（TCP 1-RTT＋TLS 1.3 交握 1-RTT）；QUIC 把傳輸與加密交握合併成新連線 **1-RTT**、復用連線 **0-RTT**（有重放風險，須謹慎）。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| HTTP/1.1 + keep-alive | 連線重用、無多工、應用層隊頭阻塞 | 簡單 REST、debug 友善（純文字）、proxy 相容性最高 | 高並行下被迫開多條連線；每連線只能一個 in-flight 請求 |
| HTTP/2 | 單連線多工、header 壓縮 | 同 host 大量小請求（API/微服務）、行動端省連線 | TCP 層隊頭阻塞在高丟包網路仍痛；單連線可能被中間設備拆 |
| HTTP/3 (QUIC) | 無傳輸層隊頭阻塞、連線遷移（換網不斷線）、0-RTT 復用 | 行動/高丟包/跨國高延遲、CDN 邊緣 | 跑 UDP，部分企業防火牆封 UDP/443；CPU 成本較高（加密在使用者態） |

### 何時需要

- **內部服務對服務、低丟包資料中心網路**：HTTP/2 的多工就夠，HTTP/3 的傳輸層好處幾乎用不到，反而吃 CPU。gRPC 預設跑 HTTP/2 正是這個原因（見 gRPC / Protobuf）。
- **面向公網、行動端、跨國、丟包率高**：HTTP/3 的每 stream 獨立復原與連線遷移有實質價值。CDN 通常已替你開好。
- **純後台批次、debug 工具、低頻呼叫**：HTTP/1.1 最省心，別為了「新」而上 2/3。

**Worked example**：一個頁面要抓 30 個小資源、RTT 100ms。HTTP/1.1 限每 host 6 條並行連線，30 個資源分 5 批、最少 5×100ms=**500ms** 才發完（未計回應）。HTTP/2 單連線 30 個 stream 一次全發出，**約 1 個 RTT（100ms）** 就全部 in-flight。但若這條 TCP 連線在傳輸中掉了 1 個封包、重傳需 1 個 RTT，HTTP/2 下這 100ms 內**全部 30 個 stream 都停**；HTTP/3 下只有踩到那個封包的 stream 停，其餘照走。

### 常見誤解與陷阱

- **「HTTP/2 多工就沒有隊頭阻塞了」**——只消了應用層的，TCP 層的還在，高丟包網路（行動/跨國）才見真章。
- **「HTTP/3 一定比 HTTP/2 快」**——資料中心內低丟包環境，HTTP/3 的傳輸優勢趨近於零，加密在使用者態反而較耗 CPU；別無腦升級。
- **「升 HTTP/2 就要少開連線、複用單一連線最好」**——單連線確實是 HTTP/2 的設計，但某些 L4 負載均衡會把單連線釘在一台後端，**反而讓負載不均**（見 service mesh 的 per-request LB）。
- **0-RTT 不是免費的**：QUIC/TLS 1.3 的 0-RTT early data 可被**重放攻擊**，只能用於冪等請求（見冪等，領域 A）。

### 延伸閱讀

- RFC 9114 — HTTP/3：https://www.rfc-editor.org/rfc/rfc9114.html
- RFC 9000 — QUIC Transport：https://www.rfc-editor.org/rfc/rfc9000.html
- RFC 9113 — HTTP/2：https://www.rfc-editor.org/rfc/rfc9113.html
- Head-of-Line Blocking in QUIC and HTTP/3: The Details（Robin Marx）：https://calendar.perfplanet.com/2020/head-of-line-blocking-in-quic-and-http-3-the-details/

## gRPC / Protobuf

### 是什麼與內部機制

gRPC 是一套**跨語言 RPC 框架**：你用 Protocol Buffers（Protobuf）的 `.proto` 檔當 **IDL（Interface Definition Language）** 同時描述「服務介面」和「訊息結構」，`protoc` 加 gRPC 外掛由 `.proto` **產生 client stub 與 server skeleton**，呼叫遠端方法寫起來像呼叫本地函式。傳輸層固定跑 **HTTP/2**，訊息以 Protobuf 二進位序列化後放進 HTTP/2 的 data frame。

gRPC 真正的招牌是它把 HTTP/2 的 stream 對應成**四種呼叫語意**：

- **Unary**：一次請求、一次回應（最像傳統 RPC）。
- **Server streaming**：一次請求、server 回一串訊息（如訂閱推送）。
- **Client streaming**：client 送一串、server 回一次（如上傳分塊聚合）。
- **Bidirectional streaming**：雙向各自一串、獨立讀寫（如雙工聊天）。

每個呼叫是一個 HTTP/2 stream；streaming 語意直接寫在 `.proto` 的方法簽章裡（`stream` 關鍵字），由產碼決定 stub 的型別。狀態以 gRPC 自己的 status code（`OK`/`NOT_FOUND`/`DEADLINE_EXCEEDED`…）放在 HTTP/2 trailer 回傳，與 HTTP status 分開（2026-06）。

> 註：以下為示意 `.proto`、不保證可跑。
>
> ```protobuf
> service OrderService {
>   rpc GetOrder(GetOrderRequest) returns (Order);                  // unary
>   rpc WatchOrders(WatchRequest) returns (stream OrderEvent);      // server streaming
> }
> message GetOrderRequest { string order_id = 1; }
> ```

Protobuf 的**序列化格式與 schema 演進規則（欄位編號、向前後相容、保留欄位）本身的機制不在此重講**（見序列化與 schema 演進，領域 A）；本條只關心 gRPC 怎麼**用**它當 IDL 與傳輸語意。

### 在哪些系統扮演什麼角色

- **內部微服務之間的同步呼叫**：gRPC 是資料中心內服務對服務呼叫的主力，因為產碼省掉手寫 client、二進位省頻寬、HTTP/2 多工省連線。
- **多語言團隊的契約中樞**：`.proto` 是唯一真相來源，Go server、Node client、Python 工具共用同一份契約，避免各自手刻 DTO 漂移。
- **streaming 場景**：把長連線推送（如進度回報、事件訂閱）寫成 server streaming，比自己搭 WebSocket 協定簡單（但瀏覽器直連需 gRPC-Web，見下）。
- **service mesh 的負載均衡單位**：gRPC 單條 HTTP/2 長連線會讓 L4 LB 失效（流量釘在一台），通常交給 L7/mesh 做 per-request 均衡（見負載均衡 L4 vs L7、service mesh）。

### 保證與限制

**保證**：強型別契約（編譯期擋掉欄位拼錯）、跨語言一致序列化、HTTP/2 多工與雙向 streaming、deadline 傳播（client 設的 deadline 隨 metadata 往下游傳，整條呼叫鏈共用一個時間預算，見 timeout / deadline / budget，領域 P）。

**限制**：

- **瀏覽器不能直接講 gRPC**——瀏覽器無法操作 HTTP/2 trailer 與底層 frame，需 **gRPC-Web** + proxy 轉換，或改用 gRPC 的 JSON transcoding。
- **人類不可讀**：二進位 payload debug 不像 REST 能直接看，需 `grpcurl` 之類工具。
- **無原生快取語意**：不像 HTTP GET 有成熟的快取/CDN 生態。
- **負載均衡反直覺**：長連線特性使 L4 LB 形同虛設（見上）。

**Worked example**：一個 `Order` 物件含 `int64 id`、`string status`（值 `"PAID"`）、`double amount`。JSON 表示約 `{"id":123456789,"status":"PAID","amount":99.5}` 約 **48 bytes**；Protobuf 用欄位編號 + varint + 長度前綴，同樣資料約 **20 bytes** 上下（省約 55–60%）。每秒 5 萬次內部呼叫、平均省 28 bytes/則，就是約 **1.4 MB/s ≈ 11 Mbps** 的內網頻寬節省，外加省去 JSON parse 的 CPU。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| gRPC (Protobuf/HTTP2) | 強型別、二進位省頻寬、雙向 streaming、deadline 傳播 | 內部微服務、多語言、streaming | 瀏覽器需 gRPC-Web；debug 較難；長連線 LB 要 L7 |
| REST/JSON over HTTP | 人類可讀、快取/CDN 生態成熟、無需產碼 | 公開 API、瀏覽器直連、低頻呼叫 | 無強型別契約（除非搭 OpenAPI）；payload 較肥 |
| GraphQL | client 自選欄位、單端點聚合 | 前端聚合多來源、欄位需求多變 | N+1 與快取複雜；非 RPC 心智模型 |
| Thrift | 與 gRPC 類似的 IDL+RPC | 既有 Thrift 生態 | 生態與動能不如 gRPC |

範式層面的 REST vs GraphQL vs gRPC 取捨從 API 設計角度更完整地比（見 API 範式對照，領域 H）；本表只從傳輸/序列化角度切。

### 常見誤解與陷阱

- **「gRPC = Protobuf」**——Protobuf 是序列化格式，gRPC 是用它當 IDL 的 RPC 框架；Protobuf 也能脫離 gRPC 單獨用（如存檔、Kafka 訊息）。
- **「gRPC 比 REST 快所以一律用 gRPC」**——對公開 API、需快取、瀏覽器直連的場景，REST 的生態優勢常勝過序列化速度。
- **「deadline 設了就安全」**——deadline 是傳播的，但下游服務若不檢查/不取消，仍可能做完無用功；deadline 是合作協定，不是強制中斷。
- **把 streaming 當無限可靠管道**——gRPC stream 建在單一 HTTP/2 連線上，連線斷則整條 stream 斷，需自己處理重連與斷點續傳，不會自動恢復。

### 延伸閱讀

- gRPC Core concepts, architecture and lifecycle：https://grpc.io/docs/what-is-grpc/core-concepts/
- gRPC over HTTP/2 協定規格：https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
- Protocol Buffers 官方文件：https://protobuf.dev/

## 連線池 connection pool

### 定義與原理

連線池是一組**預先建立、保持開啟、可重複借用**的連線（到資料庫、HTTP 後端、gRPC channel…），讓呼叫端「借一條、用完還一條」而非每次現開。它解的問題是：**建立連線很貴（TCP 三向交握 + TLS 交握 + 資料庫認證可達數十毫秒到上百毫秒），而連線本身可重用**。把這個固定成本攤平，並順帶**對下游加上連線數上限**這個天然的並發閘門。

核心語意是四件事：

- **borrow（取用）**：要連線時從池子拿一條閒置的；沒有閒置且未達上限就新建；達上限就**等待**（阻塞到逾時）或**拒絕**。
- **return（歸還）**：用完放回池子，不關閉。
- **health/validation（驗活）**：歸還或借出前可選擇性檢查連線是否還活著（如 ping），剔除被對端或中間設備悄悄關掉的死連線。
- **eviction（汰除）**：閒置超過 idle timeout 的連線被關閉回收，避免養一堆沒用的連線。

### 解法空間

- **固定大小池**：min=max，永遠維持 N 條。可預測、無擴張抖動，但離峰浪費。
- **彈性池（min/max + idle timeout）**：低載縮到 min、高載擴到 max、閒置汰除。多數函式庫預設（如各語言的 DB driver pool）。
- **每執行緒/每連線一條 vs 共享池**：共享池讓並發數 > 連線數時排隊；thread-per-connection 模型則 1:1（見並發模型比較，領域 D）。
- **等待策略**：池滿時 **borrow** 要 (a) 阻塞等到 timeout、(b) 立刻失敗（fail-fast）、(c) 視為背壓往上拒絕（見背壓，領域 E）——這是設計取捨，不是預設值。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 固定大小池 | 並發上限明確、無擴張抖動 | 穩態流量、下游連線數寶貴（如 PG） | 離峰浪費連線；尖峰若 max 設太小直接排隊 |
| 彈性池 (min/max) | 攤平建立成本、離峰省資源 | 流量有日夜波動 | 擴張瞬間有冷連線延遲；idle timeout 與下游 idle kill 要對齊 |
| 借用阻塞 + timeout | 平滑尖峰、不立刻拒絕 | 短暫尖峰可吸收 | 等待時間算進請求延遲；timeout 設太長放大隊頭阻塞 |
| 借用 fail-fast | 過載立刻可見、不堆積 | 寧可掉請求也不要 latency 爆炸 | 尖峰期錯誤率上升，需搭重試（見重試，領域 A） |

### 何時需要

- **任何到資料庫的存取**幾乎都該用池——DB 連線昂貴且數量硬上限（如 PostgreSQL 預設 `max_connections=100`，每連線還吃記憶體）。
- **高頻 HTTP/gRPC 對固定下游呼叫**：池化省交握。HTTP/2/gRPC 因單連線多工，「池」常退化成「少數幾條長連線 + 多工」，不是傳統意義的大池。
- **serverless 反而是陷阱**：每個函式實例各自開池、auto-scale 時連線數暴衝、極易打爆 DB 上限，這時要外掛**連線池中介**（如 PgBouncer 之類的 pooler）把多實例的連線收斂到一處（2026-06）。
- **不需要的場景**：低頻批次、一次性腳本、呼叫對象多變（每次不同 host）——池的攤平效益出不來。

**Worked example**：DB 連線建立含交握約 30ms，請求本身查詢約 2ms。無池：每請求 30+2=**32ms**，連線成本佔 94%。固定 20 條的池、穩態 QPS=2000：每連線每秒可服務 1/0.002=500 次查詢，20 條理論上限 **10,000 QPS**，2000 QPS 下池利用率約 20%、借用幾乎零等待。若把 max 砍到 4 條：理論上限 2000 QPS，**利用率逼近 100%**，依排隊直覺（ρ→1）借用等待時間爆炸（見排隊直覺，領域 E）——這就是池太小的代價。

### 常見誤解與陷阱

- **「池越大越好」**——池大小是**對下游的並發上限**，設太大等於把過載直接灌進 DB（連線各吃記憶體、context switch、鎖競爭），常見的反而是**池太大壓垮 DB**。max 應由下游能承受的並發回推。
- **連線洩漏**：借了不還（忘了 close、例外路徑沒釋放）會慢慢耗盡池，表現為「跑一陣子後全部請求卡在借用等待」。務必用 try-with-resources/defer 確保歸還。
- **死連線**：防火牆/LB/DB 會悄悄關掉閒置太久的連線，池裡卻還以為活著，借出去第一個查詢才爆「connection reset」。需驗活或把 pool idle timeout 設得比下游的 idle kill **更短**。
- **池上限 vs DB 上限不對齊**：N 個應用實例各開 max=20 的池，DB `max_connections=100`，6 個實例就 120 > 100，第 6 個實例的連線直接被拒。算總帳：實例數 × 每池 max ≤ DB 上限（留餘量給維運連線）。
- **本條只管機制與語意**；連線池的**調參、監控指標、暖機**（pool size 怎麼壓測、看哪些 metric）見領域 S 的連線池調校。

### 延伸閱讀

- PostgreSQL — Connection Pooling 與 `max_connections`：https://www.postgresql.org/docs/current/runtime-config-connection.html
- HikariCP — About Pool Sizing（連線池大小的經典分析）：https://github.com/brettwooldridge/HikariCP/wiki/About-Pool-Sizing
- PgBouncer 官方文件（外部 pooler）：https://www.pgbouncer.org/

## 負載均衡 L4 vs L7

### 定義與原理

負載均衡器（LB）把進來的流量分配到多個後端，目標是**讓沒有一台被打爆、有壞掉的繞過去**。分水嶺在它看到**哪一層**：

- **L4（傳輸層）**：只看 TCP/UDP 的 IP + port，按連線轉發，**不解析內容**。一旦一條連線被指派到某後端，整條連線都黏在那台。快、便宜、協定無關。
- **L7（應用層）**：解析 HTTP（path/header/cookie/method），可按 URL 路由、依請求做決策、改寫 header、終結 TLS。每個**請求**都能重新選後端。功能多、成本高。

第一原理：**L4 的分配單位是「連線」，L7 的分配單位是「請求」**。這個差異在長連線協定（HTTP/2、gRPC、WebSocket）上會放大成致命問題——L4 下一條長連線上的一萬個請求全去同一台，看起來連線數均衡、實際請求量爆炸不均。

### 解法空間

分配演算法（與 LB 在哪一層正交）：

- **Round Robin**：依序輪流。後端同質、請求同質時夠用。
- **Weighted Round Robin**：依後端容量加權。異質機型用。
- **Least Connections**：選當前連線最少的。天然適應慢後端（慢的累積連線、自動少收）。
- **Power of Two Choices (P2C)**：隨機抽兩台、選連線少的那台。用極小協調成本拿到接近 least-connections 的效果，避免「所有 LB 一起衝同一台最閒後端」的羊群效應。
- **Peak EWMA**：以指數加權移動平均追蹤每後端的延遲，選**預測延遲最低**的。對長尾敏感、適合延遲差異大的後端（Linkerd/某些 mesh 採用）。
- **Consistent Hashing**：依 key（如 user id）固定打到同一台，做 session affinity 或快取親和（機制見 consistent hashing，領域 M）。

健康檢查：

- **主動（active）**：LB 定期主動探測（如每 5s 打一次 `/healthz`），連續 N 次失敗就摘除。
- **被動（passive / outlier detection）**：觀察真實流量的錯誤/逾時，某後端連續失敗就暫時摘除（ejection），過一段時間再試放回。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| L4 LB | 高吞吐、低延遲、協定無關、連線級分配 | TCP/UDP 直通、TLS passthrough、極高吞吐 | 長連線（HTTP/2/gRPC/WS）下請求嚴重不均；無法按 path 路由 |
| L7 LB | per-request 分配、path/header 路由、TLS 終結、可改寫 | HTTP 微服務、需路由規則、gRPC per-request 均衡 | CPU/延遲成本高；要解密才能看內容 |
| 主動健康檢查 | 主動探測、可預測摘除 | 後端有現成 health endpoint | 探測頻率 vs 反應速度取捨；探測自身有成本 |
| 被動 outlier detection | 用真實流量判斷、零額外探測 | 故障難用 health endpoint 表達 | 需累積失敗樣本，反應較慢；ejection 比例要設上限免雪崩 |

### 何時需要

- **純 TCP/UDP 直通、追求極致吞吐與低延遲、不需內容路由**：用 L4（如資料庫前的代理、TLS passthrough）。
- **HTTP 微服務、需按 path/host 路由、需 per-request 均衡、需在邊緣終結 TLS**：用 L7。
- **跑 gRPC/HTTP2 而想要請求級均衡**：**必須** L7 或 client-side LB（見 service mesh、DNS 與服務發現），L4 在此基本失效。
- **過度工程警訊**：三台後端、同質、短連線 REST——L4 round robin 就夠，別急著上 service mesh 那套 per-request EWMA。

**Worked example**：100 個 client，每個對 gRPC 服務開 1 條 HTTP/2 長連線，背後 5 台後端。L4 round robin 按連線分：每台約 20 條連線，看似均衡。但若其中 10 個 client 是高頻批次、各自在自己那條連線上跑 1000 QPS，其餘 90 個各 10 QPS——這 10 條高頻連線恰好可能都落在同一台後端，那台扛 ~10,000 QPS、其餘四台合計 ~800 QPS。L4 完全看不見這個失衡（它只數連線）。換 L7 per-request 均衡後，每個 RPC 重新選後端，10,900 QPS 才會被攤成每台約 2180 QPS。

### 常見誤解與陷阱

- **「L4 比 L7 好因為快」**——快是真的，但 L4 對長連線協定的請求級失衡是隱形殺手；選層級要看協定，不是看快慢。
- **「LB 演算法選 least-connections 一定比 round robin 好」**——多個獨立 LB 各自算 least-connections 會羊群效應（一起衝最閒那台）；分散式環境 P2C 通常更穩。一句話：**好的健康檢查比好的演算法更重要**——演算法再優，健康檢查有盲點（把死後端當活的）照樣打進黑洞。
- **健康檢查探的端點太淺**：只探 TCP port 通不通、或一個永遠回 200 的 `/ping`，無法反映「DB 連不上但 HTTP 還活著」的半死狀態。readiness 應反映真實依賴（見 health check，領域 P）。
- **摘除過猛引發雪崩**：被動 ejection 沒設比例上限，一波瞬時錯誤把半數後端全摘掉、流量灌剩下一半、再被打死——連鎖摘除。務必設 `max_ejection_percent` 之類的上限。

### 延伸閱讀

- Envoy — Load Balancing（演算法、outlier detection、panic threshold）：https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/upstream/load_balancing/overview
- HAProxy — Load Balancing Algorithms：https://www.haproxy.com/glossary/what-are-load-balancing-algorithms
- The Power of Two Choices in Randomized Load Balancing（Mitzenmacher, 1996）：https://www.eecs.harvard.edu/~michaelm/postscripts/tpds2001.pdf

## TLS / mTLS（握手、憑證管理）

### 定義與原理

TLS（Transport Layer Security）在 TCP（或 QUIC 內建）之上提供三件事：**加密**（防竊聽）、**完整性**（防竄改）、**身分驗證**（防冒充）。當前現役主力是 **TLS 1.3（RFC 8446，2018-08）**，相對 1.2 的關鍵改進是**握手縮到 1-RTT**、強制前向保密（ephemeral 金鑰交換）、砍掉一堆不安全的舊 cipher suite、只留 AEAD（2026-06）。

握手的第一原理：client 在第一個訊息裡就**投機性地送出自己的 key share**，server 回 key share 後雙方各自算出共享金鑰，**一個來回就能開始加密通訊**（1-RTT）。

預設只有 **server 出示憑證**讓 client 驗證（單向）。**mTLS（mutual TLS）** 是**雙向**：client 也出示自己的憑證、server 也驗它。差別在於「誰需要證明身分」——公網 HTTPS 通常只需 client 確認 server 是真的（單向）；服務對服務則常要互相確認（mTLS），這正是 service mesh 的零信任基礎（見 service mesh）。

憑證管理是 TLS 的隱形主體：憑證有**效期**（公網 CA 效期上限 2026-03 起為 200 天、2027／2029 續降至 100／47 天；Let's Encrypt 自採更短的 90 天），到期前必須**自動輪換（rotation）**，否則服務集體掛掉。內部 mTLS 通常自建 CA、簽發短效期（小時級）憑證、由 mesh 自動輪換。

### 解法空間

- **單向 TLS（server-only）**：標準 HTTPS。client 用內建 CA 信任鏈驗 server 憑證。
- **mTLS（雙向）**：再加 client 憑證。可用於服務對服務零信任、API client 強身分、VPN-less 內網。
- **憑證信任來源**：公網用公開 CA（Let's Encrypt/商業 CA）；內網自建私有 CA（如 mesh 內建 CA、HashiCorp Vault、step-ca）。
- **撤銷**：CRL（撤銷清單，笨重）/ OCSP（線上查詢，有延遲與隱私問題）/ **短效期憑證**（用過期取代撤銷，現代 mesh 的主流做法——憑證活幾小時，壞了等它自然過期就好）。
- **TLS 終結位置**：邊緣 LB 終結（內部明文，簡單但內網不加密）/ 一路加密到後端（passthrough 或 mesh re-encrypt）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 單向 TLS 1.3 | server 身分 + 加密 + 完整性、1-RTT | 公網 HTTPS、API 對外 | 不驗 client；憑證輪換漏掉就全站掛 |
| mTLS | 雙向身分 + 加密 | 服務對服務零信任、強身分 client | 憑證管理複雜度倍增；client 憑證輪換是運維重擔 |
| 公開 CA（效期上限 200 天，2026-03 起且將續降；Let's Encrypt 採 90 天） | 瀏覽器原生信任 | 對外網域 | 須自動續簽（ACME）；忘了續＝服務中斷 |
| 私有 CA + 短效期 | 完全自控、撤銷靠過期 | 內部 mesh/服務間 | 須自建簽發與分發；client 不認你的 CA |
| 邊緣終結 TLS | 後端免處理加密、省 CPU | 內網可信、簡單拓樸 | 終結點之後是明文，不符零信任 |

### 何時需要

- **任何對外流量**：單向 TLS 是底線，沒有例外。
- **服務對服務、零信任網路、合規要求內網加密**：mTLS。但別在三個互信服務的小系統硬上 mTLS——憑證輪換的運維負擔可能超過收益，除非有 mesh 自動化（見 service mesh）。
- **強 client 身分（B2B API、IoT 裝置）**：mTLS 比 API key 更難偽造、可細到單一裝置撤銷。
- **over-engineering 警訊**：純內網、低敏感、無合規壓力的早期系統，先把單向 TLS 與憑證自動續簽做穩，mTLS 等有 mesh 再說。

**Worked example**：一個面向公網的服務用 Let's Encrypt 憑證（90 天效期），靠 ACME client 在到期前 30 天自動續簽。若續簽 cron 壞了沒人發現，**第 90 天整站 TLS 憑證過期、所有 HTTPS 連線報 `CERT_DATE_INVALID`、全部流量歸零**——這是最常見的「沉默到爆炸」事故。防禦：對「憑證剩餘天數」設告警（如 < 14 天告警），把它當 SLI（見告警設計，領域 I）。換算：1-RTT 握手在 RTT=50ms 的連線上多約 50ms 首次延遲，TLS 1.3 的 session resumption（0-RTT）可把復用連線的握手成本壓到接近零（代價是重放風險，僅限冪等請求）。

### 常見誤解與陷阱

- **「TLS 終結在 LB 就安全了」**——終結點之後若是明文內網，攻破網路即可竊聽；零信任要求一路加密或 mesh re-encrypt。
- **「mTLS 自動防一切」**——mTLS 只證明「對端持有某張被我信任的 CA 簽的憑證」，**不等於授權**；誰能做什麼仍是 AuthZ 的事（見認證 vs 授權，領域 F）。
- **憑證效期 vs 輪換頻率搞混**：90 天效期不代表 90 天才輪換一次；要在過期前留足重試餘量自動續，別卡死線。
- **「自簽憑證 = 不安全」**——自簽只是「不被公開 CA 信任」，內網自建 CA + 短效期是完全正當且更安全的做法；不安全的是把私鑰外洩或不驗憑證鏈。
- **TLS 版本協商降級**：未停用 TLS 1.0/1.1 可能被降級攻擊；現代部署應只開 1.2/1.3。

### 延伸閱讀

- RFC 8446 — TLS 1.3：https://www.rfc-editor.org/rfc/rfc8446.html
- Cloudflare — A Detailed Look at RFC 8446 (TLS 1.3)：https://blog.cloudflare.com/rfc-8446-aka-tls-1-3/
- Let's Encrypt — How It Works（ACME 自動續簽）：https://letsencrypt.org/how-it-works/

## DNS 與服務發現（service discovery）

### 定義與原理

服務發現解的問題是：**呼叫端怎麼知道「order-service」現在跑在哪些 IP:port 上**——在實例會自動擴縮、漂移、重啟的環境，這份名單時時在變。DNS 是最古老的服務發現機制（名字 → IP），但它的快取模型與「實例頻繁變動」天生矛盾。

三種模式：

- **DNS-based**：把服務名解析成一組 A/AAAA 記錄（或 SRV 帶 port）。client 拿到 IP 後自己連。簡單、語言無關，但**受制於 TTL 快取**——一個死掉的實例在 TTL 過期前仍可能被解析給 client。
- **Client-side discovery**：client 直接查 registry（如 Consul）拿健康實例清單，**自己做負載均衡**選一台。少一跳、可用 P2C/EWMA 等聰明演算法，但每種語言都要 registry client SDK。
- **Server-side discovery**：client 只認一個穩定虛擬位址（如 K8s Service 的 ClusterIP），背後由平台（kube-proxy / LB）轉發到健康實例。client 無腦、語言無關，但多一跳。

第一原理：**服務發現 = registry（誰是真相）+ 健康判定（哪些活著）+ 解析/分配（怎麼挑一台）**。DNS 把這三件揉在一起且更新慢；現代 registry（Consul / K8s endpoints）把三者拆開、更新近即時。

### 解法空間

- **靜態設定/設定檔**：把後端 IP 寫死。最簡單，但實例一變就過時——只適合極穩定的少量端點。
- **DNS + 低 TTL**：把 TTL 設到 5–30s 縮短失效窗口。改善有限，且很多 client/resolver 不尊重短 TTL（會自己多快取）。
- **K8s 內建（Service + DNS + endpoints controller）**：Pod 變動時 endpoints 近即時更新，Service 的 ClusterIP 穩定不變，kube-proxy/IPVS 轉發。容器世界的預設。
- **專用 registry（Consul / etcd / Eureka）**：服務啟動時註冊、定期心跳、registry 做健康檢查、client 或 sidecar 查詢。跨平台、跨叢集適用。
- **service mesh 的 xDS**：control plane 把端點清單即時推給每個 sidecar（見 service mesh），是 client-side discovery 的進化版。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 靜態設定 | 零依賴、可預測 | 極少數穩定端點 | 實例一變就過時；無健康感知 |
| DNS（A/SRV）| 語言無關、生態成熟 | 變動慢的服務、跨組織 | TTL 快取讓失效慢；多層快取不可控 |
| K8s Service + DNS | 端點近即時更新、ClusterIP 穩定 | 容器化微服務 | 限叢集內；跨叢集需額外方案 |
| Consul / etcd | 跨平台、主動健康檢查、KV | 混合/多叢集/VM+容器 | 自己要運維 registry 的高可用 |
| Mesh xDS push | 端點即時推送、配合 LB 策略 | 已上 mesh 的大型微服務 | 綁定 mesh 的複雜度 |

### 何時需要

- **變動慢、跨組織、被各種 client 消費**：DNS 仍是最通用解（如對外網域、第三方 API）。
- **容器化微服務、實例頻繁擴縮**：用 K8s Service 或 registry，別靠 DNS TTL 賭時效。
- **需要聰明的 client-side LB（P2C/EWMA）或跨叢集**：registry + client-side discovery 或 mesh。
- **over-engineering 警訊**：單體 + 一個資料庫，根本不需要服務發現；別為了「微服務感」硬塞 Consul。

**Worked example**：DNS A 記錄 TTL=300s，一個實例當機。在最壞情況下，client 端 resolver 與函式庫快取會讓這個死 IP **最長被解析給新連線達 5 分鐘**，期間打到死 IP 的請求全部逾時失敗。把 TTL 降到 15s 可把窗口縮到約 15s，但 (a) 增加 DNS 查詢量、(b) 不少 client 自帶更長的內部快取不甩你的 TTL。改用 K8s endpoints 時，Pod 一掛、endpoints controller 通常**秒級**把它從清單移除，失效窗口從分鐘級降到秒級——這就是「為什麼頻繁擴縮的環境不該用 DNS TTL 當健康機制」。

### 常見誤解與陷阱

- **「降低 DNS TTL 就能即時切換」**——resolver、OS、函式庫、JVM（早期預設永久快取 DNS）各有自己的快取，你的 TTL 常被無視；別把 DNS TTL 當可靠的故障切換手段。
- **「服務發現 = 負載均衡」**——發現是「拿到健康清單」，均衡是「從清單挑一台」，兩件事。DNS round-robin 把兩者混在一起且都做不好（無健康感知、TTL 慢）。
- **註冊但不註銷**：實例當機若沒主動註銷、又沒心跳超時剔除，registry 裡會殘留殭屍端點；health check 是 registry 的命脈，不是可選項。
- **DNS 解析也是依賴**：DNS server 掛了、解析變慢，會讓「看起來和網路無關」的呼叫集體變慢或失敗；DNS 查詢要有 timeout 與快取，別當它永遠瞬間回應。
- **thundering herd on cache expiry**：大量 client 的 DNS 快取同時到期、同時去查，可能瞬間打爆 DNS——加 jitter（見重試、退避、jitter，領域 A）。

### 延伸閱讀

- Kubernetes — DNS for Services and Pods：https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
- Consul — Service Discovery 概念：https://developer.hashicorp.com/consul/docs/use-case/service-discovery
- RFC 2782 — DNS SRV 記錄：https://www.rfc-editor.org/rfc/rfc2782.html

## service mesh（sidecar / Envoy）

### 定義與原理

service mesh 把「服務間通訊的橫切關注點」——**mTLS、重試、逾時、熔斷、負載均衡、流量路由、可觀測性**——從**應用程式碼裡抽出來**，下放到一層獨立的網路基礎設施。它解的問題是：當你有幾十上百個微服務，這些通訊邏輯若散落在每個服務、每種語言各刻一遍，會漂移、不一致、難治理。mesh 讓它變成**平台層的統一策略**，應用幾乎無感。

兩層架構：

- **data plane（資料面）**：實際攔截並處理流量的代理，最常見是 **Envoy**（CNCF 專案、高效能 L7 代理）。傳統做法是 **sidecar 模式**——每個 Pod 旁注入一個 Envoy，應用的所有進出流量都先經它。
- **control plane（控制面）**：下發設定給所有 data plane 代理（端點清單、路由規則、憑證、策略）。Istio 用 **xDS** 協定把這些即時推給每個 Envoy。

第一原理：**把跨服務的網路策略從「每個服務各自實作」變成「基礎設施統一執行」**，代價是**多一層代理跳轉**（延遲與資源）與**整體複雜度**。

sidecar 模式的成本（每 Pod 一個 Envoy 吃記憶體與 CPU）催生了 **sidecarless / ambient 模式**：把功能拆成節點級的 L4 代理（**ztunnel**，做 mTLS/telemetry）+ 按需的 L7 代理（**waypoint**），不再每 Pod 注入。Istio 的 ambient mode 於 **v1.24（2024-11）達 GA/Stable**（2026-06）。

### 解法空間

- **不用 mesh，函式庫做（如 client-side LB/重試函式庫）**：少一層代理、低延遲，但每種語言要各自實作、版本升級要動所有服務。
- **sidecar mesh（Istio/Linkerd 經典模式）**:每 Pod 一代理。功能最全、應用零改動，但資源開銷大、Pod 啟動鏈變長。
- **ambient / sidecarless mesh**：節點級 L4（ztunnel）+ 選用 L7（waypoint）。省資源、降延遲，L7 功能按需才加。
- **只取 mesh 的一部分**：有些團隊只要 mTLS 與可觀測，不要全套流量管理——可只啟用 L4 層。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 函式庫（無 mesh） | 無額外跳轉、低延遲 | 少數服務、單一語言 | 多語言要各自實作；升級要動所有服務 |
| sidecar mesh（Envoy） | 統一 mTLS/重試/路由/觀測、應用零改 | 大量多語言微服務、需細緻流量控制 | 每 Pod 一代理吃資源；複雜度高；多一跳延遲 |
| ambient / sidecarless | 省資源、L4 全覆蓋、L7 按需 | 想要 mTLS+觀測但嫌 sidecar 重 | 較新、L7 進階功能仍演進中；運維心智模型不同 |
| 純 L4 mesh（只 mTLS） | 零信任加密 + telemetry、最輕 | 只要加密與可見性 | 拿不到 L7 路由/重試 |

### 何時需要

- **幾十個以上的微服務、多語言、需要統一的 mTLS/重試/路由/可觀測策略**：mesh 的治理收益開始壓過複雜度。
- **零信任合規要求服務間全程 mTLS 且要自動憑證輪換**：mesh 自動化憑證是它最實在的賣點。
- **需要漸進式流量切換（canary by header/percentage）**：L7 mesh 的流量路由很適合（見 blue-green / canary / rolling，領域 Q）。
- **明顯 over-engineering**：少於約 5–10 個服務、單一語言、無零信任壓力——一個函式庫 + 一個 L7 LB 就夠，硬上 mesh 是拿巨大運維複雜度換用不到的功能。mesh 是「服務數量與治理痛點到一定規模」才回本的投資。

**Worked example**：50 個服務、每個平均 3 個 Pod = 150 個 Pod。sidecar 模式下每個 Pod 多一個 Envoy，若每 Envoy 約佔 50–100MB 記憶體與一小塊 CPU，光 sidecar 就吃掉 **約 7.5–15GB 記憶體**，且每次服務對服務呼叫多兩跳代理（出口 sidecar + 入口 sidecar），各加數百微秒到約 1ms 延遲。換 ambient 後，代理從「150 個」變成「每節點 1 個 ztunnel」（如 10 個節點 = 10 個），L4 加密的資源足跡大幅下降——這是 ambient 模式存在的根本動機（官方宣稱可省 70%+ 資源，數字依工作負載而異）。但代價是運維要理解 ztunnel/waypoint 這套新心智模型。

### 常見誤解與陷阱

- **「上了 mesh 就更可靠」**——mesh 本身是新的故障源與延遲源：sidecar 沒 ready 應用就連不出去、control plane 掛了設定推不下去、Envoy 版本升級是一次全叢集變更。它把可靠性問題**集中化**了，集中的好處與集中的風險並存。
- **「mesh 的重試讓系統更韌」**——盲目在 mesh 層開重試，疊上應用層重試，會放大成重試風暴（見 retry storm，領域 E）；mesh 重試必須與應用層協調、且只對冪等請求開。
- **sidecar 與應用的啟動/關閉順序**：應用比 sidecar 早起來、流量出不去；關閉時 sidecar 先死、應用最後幾個請求發不出。graceful shutdown 要考慮這個耦合（見 graceful shutdown，領域 P）。
- **把 mesh 當萬靈丹塞進小系統**：mesh 的價值與服務數量、語言多樣性、治理痛點成正比；規模不到位時，它純粹是負債。
- **混淆 mesh 與 API gateway**：mesh 管**東西向**（服務間）流量、API gateway 管**南北向**（外部進來）流量；兩者職責不同、常並存（見 API gateway 的角色，領域 H）。

### 延伸閱讀

- Istio — Ambient Mode Reaches GA in v1.24：https://istio.io/latest/blog/2024/ambient-reaches-ga/
- Envoy Proxy — Architecture Overview：https://www.envoyproxy.io/docs/envoy/latest/intro/arch_overview/intro/
- Istio — Dataplane modes (sidecar vs ambient)：https://istio.io/latest/docs/overview/dataplane-modes/
