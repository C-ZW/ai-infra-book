# C · 即時傳輸

本領域解的問題：當資料要從伺服器**主動推**到 client、或多方要**即時互傳**時，HTTP 的請求-回應模型不夠用，要選一條長連線傳輸與一套擴展架構。本檔含六條：兩條問題型（推 vs 拉的全景、長連線的連線狀態與水平擴展），四條工具型（WebSocket、SSE/long-poll/WebTransport 三者對照、Socket.io、WebRTC）。邊界：底層 HTTP/1.1 · 2 · 3 與 QUIC 的協定機制、負載均衡 L4 vs L7、TLS 握手屬網路與協定（領域 N）；本檔只談「即時雙向/推送」這層怎麼選、各給什麼保證、擴展時哪裡會塌。

## server→client 推送全景（推 vs 拉）

### 定義與原理

HTTP 的原始模型是 client 拉（request）、server 回（response），server 無法在沒有請求時主動送東西給 client。但很多場景要的是相反方向：新訊息到了、訂單狀態變了、股價跳動了——server 知道，client 不知道，且 client 不知道「該什麼時候問」。推送（push）要解的就是這個資訊方向倒轉的問題：讓 server 端發生的事件，能在「事件發生後的可接受延遲內」抵達 client。

第一原理是：推與拉的差別，本質是**「誰決定傳輸時機」**。拉是 client 決定（我什麼時候問），推是 server 決定（我什麼時候送）。純 HTTP 給不了「server 決定時機」這件事，因為連線是 client 開的、用完就還；所以所有推送方案，要嘛是「維持一條長連線讓 server 隨時能寫」，要嘛是「用反覆的拉模擬推」。理解這一點，下面整張選項地圖就清楚了：它們全在「延遲低 vs 連線成本低」這條軸上選點。

### 解法空間

從「最像拉」到「最像推」，連續光譜：

- **短輪詢（short polling）**：client 每隔固定間隔發一次普通 HTTP 請求問「有沒有新東西」。機制最簡單，無長連線；延遲＝輪詢間隔，浪費＝大量「沒有新東西」的空請求。
- **長輪詢（long polling）**：client 發請求後，server **不立刻回**，hold 住直到有新事件（或逾時）才回應；client 收到後立刻再發下一個請求。用一次請求的「掛起」模擬一次推送。
- **Server-Sent Events（SSE）**：一條長連線、`text/event-stream`，server 端可在這條連線上**單向**持續寫多筆事件給 client；瀏覽器原生 `EventSource` 自動重連。
- **WebSocket**：升級後的全雙工長連線，兩端都能隨時送 frame（見 WebSocket 條目）。
- **WebTransport**：建在 HTTP/3（QUIC）上的新傳輸，提供多條 stream＋datagram、解決 head-of-line blocking（見 SSE / long-poll / WebTransport 條目）。
- **第三方推送通道**：如行動裝置的 APNs/FCM、瀏覽器 Web Push——把「維持連線」外包給平台，server 只丟訊息給推送服務。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 短輪詢 | 延遲上界＝輪詢間隔；零長連線、無狀態、極易擴展 | 更新罕見、延遲容忍秒級以上（如每 30s 查一次狀態） | 大量空請求；要低延遲就得縮短間隔，請求量爆炸 |
| 長輪詢 | 比短輪詢延遲低（事件一到就回）；走標準 HTTP、過所有 proxy | 中低頻事件、不想引入 WebSocket 基建 | 每次事件後要重連，高頻時等同連環請求；server 要 hold 大量掛起連線 |
| SSE | server→client 單向串流、自動重連、可 resume（`Last-Event-ID`） | 只需 server 推（通知、進度、log 串流），不需 client→server 即時回 | 單向；HTTP/1.1 下受瀏覽器每網域連線數上限（通常 6）拖累 |
| WebSocket | 全雙工、低延遲、frame 開銷小 | 雙向高頻互動（聊天、協作、遊戲、即時下單） | 連線有狀態，水平擴展要 sticky session＋backplane（見下一條） |
| WebTransport | 多 stream＋datagram、無 head-of-line blocking、可不可靠混用 | 高頻、可容忍丟包的串流（遊戲、即時媒體訊號） | 標準與瀏覽器支援仍在成熟期（2026-06，見對照條目） |

worked example：一個股價看板，1,000 個 client、每檔股票平均 2 秒更新一次。**短輪詢**若要 1 秒延遲，得每秒輪詢一次＝1,000 req/s，其中約一半（更新間隔 2s）是「沒有新資料」的空回應，浪費一半。**SSE/WebSocket** 改成事件驅動：1,000 條長連線，每次價格變動才推，server 出口推送訊息數＝實際變動數（每個 client 的訂閱項每 2s 更新一次→約 1,000 筆/2s＝500 筆/s），且延遲降到亞秒級。代價是要養 1,000 條常駐連線的記憶體與檔案描述子。

### 何時需要

- **更新頻率低、延遲容忍秒級以上**：短輪詢就夠，別上 WebSocket（過度工程）。
- **只需 server 單向推**：SSE 比 WebSocket 簡單（走純 HTTP、原生重連），優先選它。
- **需要 client→server 也即時**（雙向高頻）：WebSocket。
- **可容忍丟包但要極低延遲、且能用 HTTP/3 基建**：考慮 WebTransport。
- **行動端背景推播**：用平台推送（APNs/FCM），自己維持連線在 App 被殺後也送不到。

### 常見誤解與陷阱

- **「即時就一定要 WebSocket」**：很多「即時」其實是單向推，SSE 足夠且省一半複雜度（不必處理升級握手、不必自己做重連）。
- **長輪詢不是「沒有輪詢」**：它仍是一連串請求，只是每個請求被 hold；高頻事件下它退化成連環短輪詢，連線建立成本一個都沒省。
- **忽略中間設備**：proxy／負載均衡器可能對 idle 長連線設逾時（如 60s）而悄悄斷線；SSE/WebSocket 都需要應用層心跳（SSE 送 comment line `:\n`、WebSocket 送 ping）維持與偵測。
- **把推送的「保證」想成可靠投遞**：推送通道只保證「連著時送得到」，client 離線那段的事件會漏；要不漏，得在連線上層補 resume/補拉機制（如 SSE 的 `Last-Event-ID`、或重連後拉一次快照）。

### 延伸閱讀

- WHATWG HTML Standard — Server-sent events：https://html.spec.whatwg.org/multipage/server-sent-events.html
- MDN — Using server-sent events：https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
- RFC 6455 — The WebSocket Protocol：https://www.rfc-editor.org/rfc/rfc6455

## 連線狀態與水平擴展（sticky session / backplane）

### 定義與原理

無狀態 HTTP 請求可以打到任何一台後端，因為每個請求自帶全部上下文。長連線（WebSocket/SSE）打破這個前提：一條連線**綁在一台特定 server 上**，這台 server 記著「這條連線屬於哪個使用者、訂閱了哪些主題、在哪些房間」——這是 in-memory 的連線狀態。問題立刻來了：(1) 負載均衡器後面有 N 台 server，使用者重連可能落到別台，狀態不在那；(2) 要推給「房間 A 的所有人」時，這些人的連線散在不同 server 上，單台不知道別台有誰。

第一原理：長連線把**「請求無狀態」換成了「連線有狀態」**，於是水平擴展從「無腦加機器」變成「要解決連線歸屬與跨節點廣播」。兩個正交的子問題：**連線歸屬**（同一條/同一使用者的連線怎麼穩定落到能服務它的節點）與**跨節點扇出**（一個事件怎麼送達散在各節點的目標連線）。

### 解法空間

連線歸屬：

- **sticky session（session affinity）**：負載均衡器用 cookie 或 source IP hash，把同一 client 後續連線導回同一台 server，讓 in-memory 狀態仍在。
- **無狀態化連線**：把連線狀態外移到共享存放（Redis/DB），任一節點都能服務任一連線——代價是每次操作多一跳。
- **連線層做 routing**：用一致性雜湊（見 consistent hashing，領域 M）把「使用者→負責節點」算出來，client 直連對的節點。

跨節點扇出（backplane / pub-sub 背板）：

- **pub/sub backplane**：每台 server 訂閱一個共享 pub/sub（Redis Pub/Sub、Kafka、NATS…）；要廣播時 publish 一筆，所有 server 收到後各自推給「自己這台上」的目標連線。
- **集中式狀態服務**：所有連線狀態與路由放一個專責服務（如 presence/registry），扇出時查它得知目標在哪些節點。
- **直接節點對節點**：節點間互相知道彼此，目標明確時點對點轉發（mesh，節點多時連線數爆炸）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| sticky session | 連線回到同台、in-memory 狀態可用、改動最小 | 連線狀態只關乎單台、無需跨節點廣播 | 負載傾斜（重連集中到熱點台）；該台掛了狀態全失、得重建；擴縮容時既有連線不會自動重平衡 |
| 連線狀態外移 | 任一節點可服務任一連線、節點無狀態好擴縮 | 大規模、節點頻繁增減、要彈性 | 每次操作多一次 Redis/DB 往返；外部存放成為新的單點與瓶頸 |
| pub/sub backplane | 跨節點廣播；節點水平擴展、互不直連 | 房間/頻道廣播（聊天室、協作） | 每筆廣播被 fan-out 到全部節點（即使該節點無目標連線），N 大時 backplane 成瓶頸 |
| 一致性雜湊 routing | 目標節點可計算、扇出只送該節點、不全廣播 | 超大規模、要省掉全節點廣播 | 實作複雜；節點增減時 key 重新分配、連線需遷移 |

worked example：聊天系統 4 台 server、每台 25,000 條 WebSocket 連線（共 10 萬）。一個 5,000 人的大房間發一則訊息：用 **Redis Pub/Sub backplane**，發訊節點 publish 1 筆，4 台各收 1 筆，各自把訊息推給「自己這台上、屬於該房間」的連線（平均每台約 1,250 條）——backplane 上是 1 publish → 4 deliver，跟房間大小無關。對照若**沒有 backplane、節點間 mesh 直送**：發訊節點要找出其他 3 台各有哪些目標連線並逐台轉發，且 4 台兩兩相連＝6 條節點間連線，加到 10 台就 45 條，連線數隨節點數平方成長。

### 何時需要

- **單台撐得下全部連線**：不需要 backplane，連狀態都在本機，最簡單（但單點，掛了全斷）。
- **多台但每條連線彼此獨立**（如純 server→單一 client 推送、無跨用戶廣播）：sticky session 夠用。
- **要跨節點廣播**（房間、頻道、presence）：必須上 backplane。
- **連線數大到單一 backplane 扇出成瓶頸**：才上一致性雜湊 routing 把廣播範圍縮到目標節點，否則是過度工程。

### 常見誤解與陷阱

- **「有了 sticky session 就高可用」**：sticky 只解「回到同台」，不解「同台掛了」。該台一掛，上面所有連線狀態蒸發，client 全部重連、且若狀態沒外移就得整個重建。
- **backplane 把「每則訊息」放大成「每節點一份」**：一則房間訊息在 backplane 上是 1 筆，但被 deliver 到每一台（即使某台沒有該房間的人）。節點數很多、訊息很頻時，這個無差別 fan-out 自己會變成瓶頸——這正是要上 sharded pub/sub 或一致性雜湊 routing 的時機。
- **用 Redis Pub/Sub 當 backplane 卻期待可靠投遞**：Redis Pub/Sub 是 fire-and-forget、at-most-once，backplane 那一跳本身不持久化；節點短暫斷開 Redis 期間的廣播會漏（要不漏得改用 Streams 類持久化背板，見 Socket.io 條目）。
- **擴縮容忘了既有連線**：加一台新 server，既有連線不會自動搬過去重平衡；要嘛等自然斷線重連、要嘛主動驅趕（drain）讓 client 重連分散。縮容（移除一台）則要 graceful drain，否則該台連線被硬斷。

### 延伸閱讀

- MDN — Writing WebSocket servers（含連線生命週期）：https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers
- Socket.IO — Redis adapter（backplane 的一個具體實作）：https://socket.io/docs/v4/redis-adapter/
- RFC 6455 — The WebSocket Protocol：https://www.rfc-editor.org/rfc/rfc6455

## WebSocket（frame / ping-pong / RFC 6455）

### 是什麼與內部機制

WebSocket 是 **RFC 6455**（2011）定義的全雙工長連線協定。連線從一個普通 HTTP 請求開始，帶 `Upgrade: websocket` 與 `Sec-WebSocket-Key` 標頭，server 回 `101 Switching Protocols` 並回算 `Sec-WebSocket-Accept`（把 client key 接上固定 GUID 後 SHA-1＋base64）。握手完成後，這條 TCP 連線（通常在 TLS 上，`wss://`）就脫離 HTTP 語意，改用 WebSocket 的 **frame** 協定，兩端都能隨時送。

frame 結構（精簡示意，非可執行）：

```
 0               1               2               3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 ...
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| op   |M| Payload len |  Extended payload length ...  |
|I|S|S|S| code |A|   (7 bit)   |  (16 or 64 bit, if 126/127)   |
|N|V|V|V|(4bit)|S|             |                               |
| |1|2|3|      |K|             |                               |
+-+-+-+-+------+-+-------------+-------------------------------+
| Masking-key (4 bytes, client→server only)  | Payload data... |
+--------------------------------------------+-----------------+
```

關鍵欄位：**opcode**（`0x0` continuation／`0x1` text／`0x2` binary／`0x8` close／`0x9` ping／`0xA` pong）；**FIN** 標示是否為訊息最後一個 frame（一則大訊息可切多個 frame，第一個帶 opcode、後續用 `0x0` continuation）；**MASK**＝client→server 的 frame **一律遮罩**（用 32-bit masking key 對 payload 逐位元組 XOR，防中間 proxy 把 payload 誤判成可快取的 HTTP、即快取毒害 cache poisoning），**server→client 一律不遮罩**。

**ping/pong** 是 control frame（opcode `0x9`／`0xA`），payload **必須 ≤ 125 bytes、不可分片**：一端送 ping，對端**必須**儘快回一個帶相同 payload 的 pong。它用來做心跳（偵測對端是否還活著、量 RTT）與保活（讓中間設備別把連線當 idle 砍掉）。close frame（`0x8`）攜帶可選的 2-byte 狀態碼（如 `1000` 正常關閉、`1001` going away），啟動關閉握手。

### 在哪些系統扮演什麼角色

- **雙向即時互動**：聊天、多人協作編輯（游標/編輯廣播）、線上遊戲狀態同步、即時下單/交易看板——任何 client→server 也要低延遲的場景。
- **server 推送主幹**：很多即時通知/presence 系統底層用 WebSocket（雖然單向推 SSE 也行，但已有 WebSocket 基建時就一併用）。
- **作為更上層框架的傳輸**：Socket.io、GraphQL subscriptions、各種「即時」SDK 多以 WebSocket 為首選 transport（見 Socket.io 條目）。

### 保證與限制

保證：握手後**全雙工**、frame 開銷極小（小訊息 header 僅 2–14 bytes，相比每次 HTTP 請求的完整 header 省很多）、訊息邊界由 frame 保留（不像裸 TCP 要自己切）。

限制（RFC 6455 本身**不**規範的部分，往往是坑）：

- **不保證投遞可靠性之上的語意**：底層 TCP 保證位元組有序不丟（連線存活期間），但**不保證「應用層收到並處理了」**；連線一斷，未送達/未處理的訊息就沒了，要可靠得自己在上層補 ack/重送。
- **不規範重連**：斷線後要不要重連、怎麼補回斷線期間的訊息，全是應用層的事。
- **不規範水平擴展**：sticky session＋backplane 是部署慣例，協定不管（見連線狀態與水平擴展條目）。
- **不內建心跳頻率**：ping/pong 機制有，但「多久 ping 一次、多久沒 pong 算死」要自己定。

worked example：一條閒置 WebSocket 連線，server 每 30 秒送一個 0-payload ping（frame 約 2 bytes header＋0 payload，server→client 不遮罩），client 回 2-byte header＋4-byte masking key 的 pong——一次心跳往返不到 20 bytes。10 萬條連線每 30s 一次心跳＝約 3,333 次/s，頻寬可忽略；真正的成本不是頻寬而是**每條連線常駐的記憶體**（緩衝區＋連線物件，視 runtime 每條數 KB 到數十 KB）與檔案描述子上限——10 萬條就要把 OS 的 `ulimit -n` 與 ephemeral port／記憶體都算進容量規劃。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| WebSocket | 全雙工、低開銷、瀏覽器原生 | client↔server 雙向高頻 | 連線有狀態、擴展要 backplane；自己處理重連 |
| SSE | server→client 單向、原生自動重連＋resume | 只需 server 推 | 單向；HTTP/1.1 下受每網域連線數上限 |
| long polling | 走純 HTTP、過所有舊 proxy | 環境不支援 WebSocket 時的退路 | 高頻退化成連環請求、延遲與成本都差 |
| WebTransport | 多 stream＋datagram、無 HOL blocking | 要 HTTP/3、可容丟包的串流 | 支援度仍在成熟（2026-06） |

選擇判準：只需單向推→SSE；雙向→WebSocket；要 datagram/多串流且能上 HTTP/3→WebTransport（見對照條目）。

### 常見誤解與陷阱

- **「WebSocket 訊息一定不丟」**：TCP 不丟是「連線活著時」；連線一斷，已寫進 OS 緩衝但對端沒讀的、以及應用層還沒處理的，全都沒了。要 at-least-once 得在 WebSocket 之上自己做 ack/序號/重送。
- **忘記 client frame 必遮罩**：自己寫 server 解析時若沒處理 masking、或自己寫 client 沒遮罩，會直接違反 RFC 被對端關閉。用成熟函式庫就不必煩，但裸實作常踩。
- **把 ping/pong 當可選**：少了應用層心跳，中間負載均衡器/代理會把 idle 連線靜默砍掉，client 以為還連著、訊息黑洞。心跳同時是保活與死亡偵測。
- **不限制 frame/訊息大小**：RFC 允許 64-bit payload length（理論到 EB 級），不設上限就是記憶體 DoS 入口——一個惡意 client 宣告超大 frame 就能撐爆緩衝。永遠在 server 設 max frame/message size。
- **以為一則訊息＝一個 frame**：大訊息會被切成多個 frame（FIN=0 的 continuation），應用層要組裝；只看單 frame 會拿到半截。

### 延伸閱讀

- RFC 6455 — The WebSocket Protocol：https://www.rfc-editor.org/rfc/rfc6455
- MDN — Writing WebSocket servers（frame 解析實作）：https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_servers
- WebSocket.org — WebSocket Protocol guide：https://websocket.org/guides/websocket-protocol/

## SSE / long-poll / WebTransport（三者對照）

### 是什麼與內部機制

三者都是「WebSocket 以外」的 server→client（或雙向）即時通道，機制與成熟度差很大：

**long polling**：client 發一個普通 HTTP 請求，server **不立即回**，把它 hold 在伺服器端直到有新事件或逾時才回應；client 收到後立刻再發下一個。沒有任何新協定，純 HTTP 玩法；用「掛起一個請求」模擬一次推送。

**Server-Sent Events（SSE）**：由 WHATWG HTML 標準定義。server 回應 `Content-Type: text/event-stream` 並保持連線開著，在這條連線上以純文字格式持續寫事件，每筆形如 `data: ...\n\n`，可帶 `id:`（事件 ID）、`event:`（事件型別）、`retry:`（重連間隔毫秒）。瀏覽器原生 `EventSource` API 自動解析並**自動重連**；重連時把上次收到的 `id` 放進 `Last-Event-ID` 請求標頭，server 可據此**從斷點續傳**。預設重連間隔 3000 毫秒（可被 `retry:` 覆寫）。**單向**（server→client）；client→server 仍走普通 HTTP 請求。

**WebTransport**：建在 **HTTP/3（QUIC）** 之上的新傳輸 API。QUIC 在 UDP 上自帶多工與加密，所以 WebTransport 一條 session 內可開多條**獨立 stream**（可靠、有序）＋送 **datagram**（不可靠、無序、低延遲），彼此不互相阻塞——解決了 TCP 上多工的 **head-of-line（HOL）blocking**（TCP 一個封包丟了，後面所有資料都得等它重傳）。

### 在哪些系統扮演什麼角色

- **long polling**：相容性退路——環境（老舊 proxy、企業防火牆）不允許 WebSocket 升級時的 fallback（Socket.io 即把它當最後一層 fallback，見該條目）。
- **SSE**：server 單向推的主力——通知串流、任務進度、log 即時尾隨、AI 文字逐字輸出（token streaming）、儀表板數字推送。原生重連＋resume 讓它在「只推不收」的場景比 WebSocket 省事。
- **WebTransport**：要極低延遲且可容丟包的串流——即時遊戲狀態、即時媒體的訊號/資料通道、需要多條獨立 stream 不互卡的場景。

### 保證與限制

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| long polling | 走純 HTTP、過幾乎所有中間設備；無需協定升級 | 相容性退路、低頻事件 | 高頻退化成連環請求；每次事件後重建請求；server 要 hold 大量掛起連線 |
| SSE | server→client 單向串流、自動重連、`Last-Event-ID` resume；純 HTTP | 只需推、要簡單與斷線續傳 | 單向；HTTP/1.1 下受瀏覽器每網域連線上限（通常 6）——多分頁會卡，HTTP/2 下改為多工（預設上限約 100 streams）緩解 |
| WebTransport | 多獨立 stream＋datagram、可靠/不可靠混用、無 HOL blocking | HTTP/3 環境、低延遲容丟包串流 | 標準與支援仍在成熟期（見下） |

時效（2026-06）：**WebTransport 的 W3C 文件仍是 Working Draft**、IETF 的 WebTransport over HTTP/3 對應草案為 draft-15（2026-03，仍在 Working Group Last Call），尚未成為 RFC；瀏覽器面在 **2026-03 隨 Safari 26.4 支援後達到主流瀏覽器（Chrome/Edge/Firefox/Safari）齊備**的 baseline。即「能用了，但標準仍可能有破壞性變動」。SSE 與 long polling 是成熟穩定的老技術。

worked example：HTTP/1.1 下用 SSE 做即時通知，瀏覽器對同一網域**並行連線上限約 6**。使用者開了 6 個分頁、每個分頁各開一條 SSE 連線，就把這個網域的連線配額用光，第 7 個分頁的任何 HTTP 請求（連同載入圖片、API 呼叫）全被卡住排隊。改用 **HTTP/2**：所有分頁的 SSE 與一般請求共用同一條連線多工，預設可達約 100 條並行 stream，6 個分頁＝6 條 stream，遠在上限內，問題消失。這就是「SSE 強烈建議跑在 HTTP/2 之上」的具體原因。

### 跟替代品的取捨

對照 WebSocket（見 WebSocket 條目）：

- 只要 **server 單向推**：SSE 勝 WebSocket——純 HTTP、原生重連＋resume、無需升級握手、無需自己處理連線狀態的雙向協定。
- 要 **client↔server 雙向**：WebSocket 勝 SSE（SSE 只能單向）。
- 要 **多條獨立 stream／datagram／無 HOL**：WebTransport 勝兩者，但成熟度與相容性是現階段代價。
- **環境不支援長連線升級**：long polling 是唯一能過的退路，但延遲與成本最差。

### 常見誤解與陷阱

- **「SSE 不能雙向所以沒用」**：很多場景 client→server 用普通 HTTP 請求就夠（不需即時），只有 server→client 需要即時——這正是 SSE 的甜蜜點，硬上 WebSocket 反而多做雙向協定的功。
- **SSE 在 HTTP/1.1 的連線數上限被忽略**：上面 worked example 的 6 連線卡死問題，部署在 HTTP/1.1 時很常見；務必跑在 HTTP/2 之上。
- **long polling 被當成「省連線」**：它不是省，是把一條長連線換成一連串請求；高頻時每次事件都重建一次 HTTP 請求，CPU/延遲都更差。
- **把 WebTransport 當「現在就能無腦上的 WebSocket 替代」**：2026-06 它標準未定稿、雖主流瀏覽器都支援但仍可能有破壞性變動，生產要評估降級路徑（無 HTTP/3 時退回什麼）。
- **SSE resume 不是萬靈丹**：`Last-Event-ID` 能續傳的前提是 server 真的保存了事件歷史並能依 ID 回放；若 server 沒實作這段，重連只會從「此刻」開始，斷線期間的事件照漏。

### 延伸閱讀

- WHATWG HTML Standard — Server-sent events：https://html.spec.whatwg.org/multipage/server-sent-events.html
- W3C — WebTransport（Working Draft）：https://www.w3.org/TR/webtransport/
- IETF — WebTransport over HTTP/3（draft-ietf-webtrans-http3）：https://datatracker.ietf.org/doc/draft-ietf-webtrans-http3/
- MDN — WebTransport API：https://developer.mozilla.org/en-US/docs/Web/API/WebTransport_API

## Socket.io（fallback / rooms / redis-adapter）

### 是什麼與內部機制

Socket.IO 是一套在 WebSocket 之上的即時通訊**函式庫**（client＋server），不是協定本身——它定義自己的封包格式，跑在底層 Engine.IO 提供的 transport 上。當前主程式庫為 **v4.x**（2026-06，最新約 4.8.3）。它補上裸 WebSocket 沒有的一整套應用層能力：

- **transport fallback**：建立連線時優先用 WebSocket；v4.7+ 也支援 WebTransport；若都不可用（被 proxy 擋等），退回 **HTTP long-polling**。連線先以 polling 起手再「升級」到 WebSocket，確保在惡劣網路環境下也連得上。
- **自動重連**：斷線後以指數退避自動重連，並有 heartbeat（Engine.IO 層的 ping/pong，注意這是**應用層**心跳，跟 RFC 6455 的 ping/pong control frame 不同層）。
- **rooms 與 namespaces**：room 是 server 端的「連線分組」抽象——`socket.join("room-A")` 後，`io.to("room-A").emit(...)` 只廣播給該組；namespace 是邏輯通道隔離（`/chat`、`/admin` 各自一套 room 與事件）。
- **acknowledgements**：`emit` 可帶 callback，對端處理完回呼——在 fire-and-forget 之上做請求-回應語意。

多節點水平擴展靠 **adapter**：單機版 adapter 把 room 成員存在記憶體，多節點時換成 **`@socket.io/redis-adapter`**（2026-06 約 v8.x），用 **Redis Pub/Sub** 當 backplane 在多台 Socket.IO server 間廣播封包——一台 `io.to("room-A").emit` 會 publish 到 Redis，其他節點收到後各自推給自己這台上屬於 room-A 的連線（見連線狀態與水平擴展條目）。新部署另可用 Redis 7.0 **sharded Pub/Sub** 的 sharded adapter（用 `createShardedAdapter()`），或用 **Redis Streams adapter** 處理斷線重續、避免 Redis 短暫斷開時丟封包。

### 在哪些系統扮演什麼角色

- **聊天/協作/通知**：rooms 天然對應「聊天室」「文件」「使用者私有頻道」；廣播一行搞定。
- **要相容性保底的即時功能**：fallback 機制讓它在企業防火牆、老舊 proxy 後仍能連上（裸 WebSocket 可能被擋）。
- **快速落地**：自動重連、ack、分組廣播都內建，省掉自己在裸 WebSocket 上重造這些輪子。

### 保證與限制

保證：跨惡劣網路的**連得上**（多 transport fallback）、斷線**自動重連**、分組**廣播**、可選的 **ack** 語意、多節點**跨實例 fan-out**（透過 adapter）。

限制：

- **非標準協定**：Socket.IO client 只能連 Socket.IO server，不能用裸 `WebSocket` 連（封包格式是它自己的）。鎖定這套生態。
- **ack 不是可靠投遞**：ack 只告訴你「對端的 callback 跑了」；連線在送達前斷掉、或對端處理到一半崩潰，訊息仍可能漏——要嚴格交付語意得自己加序號/持久化（交付語意見領域 A）。
- **redis-adapter 的 backplane 繼承 Redis Pub/Sub 的 at-most-once**：節點與 Redis 短暫斷開期間的廣播會漏（這正是 Streams adapter 存在的理由）。
- **room 成員狀態多在記憶體**：節點掛了，該節點上的 room 成員資訊隨之消失，靠重連重建。

worked example：3 台 Socket.IO server、用 `@socket.io/redis-adapter`，一個 500 人房間發一則訊息。發訊節點執行 `io.to("room").emit(msg)`：本地直接推給自己這台的成員，同時 **publish 1 筆到 Redis**；另外 2 台各收到這 1 筆，各自推給自己這台屬於該房間的成員（平均每台約 167 條本地連線）。Redis 上的成本是 1 publish → 2 跨節點 deliver，與房間 500 人的大小無關——backplane 只負責「跨節點那一跳」，真正的 500 次推送發生在各節點本地。若改用 sharded Pub/Sub，廣播只發到負責該 channel 的 shard，進一步降低大規模下的 Redis 扇出壓力。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Socket.IO | fallback＋重連＋rooms＋ack＋adapter 擴展 | 要快速落地、需相容性保底的即時功能 | 非標準協定、鎖生態；ack≠可靠投遞 |
| 裸 WebSocket | 標準協定、最小開銷、無鎖定 | 要極致控制/最小依賴、自己造輪子可接受 | 重連/分組/擴展全要自己做（見 WebSocket 條目） |
| SSE | server 單向、原生重連＋resume | 只需單向推 | 單向、不雙向（見對照條目） |

選擇判準：要在惡劣網路下「一定連得上」且不想自己做重連/分組/多節點廣播 → Socket.IO；要標準協定、最小依賴、願意自己造這些 → 裸 WebSocket；只需單向推 → SSE。

### 常見誤解與陷阱

- **「Socket.IO 就是 WebSocket」**：不是。它是 WebSocket 之上的函式庫＋自有封包協定，client/server 必須成對，不能用瀏覽器原生 `WebSocket` 連 Socket.IO server。
- **多節點忘了裝 adapter**：不裝 adapter 直接多開節點，`io.to(room).emit` 只會送到「碰巧連在這台」的成員，別台的人收不到——典型「本機測好好的、上線後一半人收不到訊息」。
- **以為 ack 等於送達保證**：ack 是 callback 執行的回呼，不是端到端可靠投遞；要 at-least-once 得在上層加序號/去重（見領域 A）。
- **redis-adapter 期待持久化**：Pub/Sub backplane 那一跳是 at-most-once，Redis 重啟或節點短暫失聯會漏廣播；要韌性用 Streams adapter。
- **sticky session 仍然需要**：即使有 redis-adapter 解決廣播，HTTP long-polling fallback 階段的多個請求必須回到同一節點，否則握手會錯亂——所以負載均衡器仍要開 sticky session。

### 延伸閱讀

- Socket.IO — Redis adapter：https://socket.io/docs/v4/redis-adapter/
- Socket.IO — Redis Streams adapter：https://socket.io/docs/v4/redis-streams-adapter/
- @socket.io/redis-adapter（npm）：https://www.npmjs.com/package/@socket.io/redis-adapter

## WebRTC（媒體/傳輸/信令三塊；SFU vs MCU vs mesh）

### 是什麼與內部機制

WebRTC 讓瀏覽器/App 之間直接傳即時音視訊與任意資料，**不經應用伺服器中轉媒體**（信令除外）。它不是單一協定而是一組標準的集合，理解它最好拆成**三塊互相獨立的責任**：

**1. 媒體（media）**：擷取（`getUserMedia` 拿攝影機/麥克風）、編解碼（VP8/VP9/AV1/H.264 視訊、Opus 音訊）、透過 `RTCPeerConnection` 收送。媒體走 RTP/SRTP（加密的即時傳輸）。

**2. 傳輸（transport）/ NAT 穿透**：兩端多半在 NAT/防火牆後，沒有公開可直連的位址。靠 **ICE** 框架解決：
- **STUN**（RFC 8489，obsoletes RFC 5389）：讓 client 問「我經過 NAT 後對外看起來是哪個 IP:port」，拿到自己的公開映射 candidate。
- **TURN**（RFC 8656，obsoletes RFC 5766）：當雙方無法直連（典型是 **symmetric NAT**，其對外映射是「依目的地而異」的，STUN 探到的映射對真正對端不適用）時，改走一台 **TURN relay** 中繼所有媒體。
- ICE（RFC 8445，obsoletes RFC 5245）蒐集雙方所有 candidate（host／STUN 反射／TURN relay），兩兩配對做連通性檢查，選一條通的。coturn 是事實上的開源 TURN/STUN server。

**3. 信令（signaling）**：WebRTC **刻意不規範信令**——「怎麼把我的連線資訊送到對方」由你自己決定（多半用 WebSocket）。要交換的是 **SDP**（Session Description Protocol）的 offer/answer：描述各自的媒體能力、編碼、ICE candidate。一端產生 offer、經你的信令通道送給對端、對端回 answer，雙方據此建立 `RTCPeerConnection`。

時效（2026-06）：**WebRTC: Real-Time Communication in Browsers** 自 2021-01 成為 W3C Recommendation，W3C 於 **2025 重新發布納入 candidate amendments 的更新版 Recommendation**，故標準持續現行、未被取代。

### 在哪些系統扮演什麼角色

- **視訊/語音通話與會議**：一對一通話、多人會議。
- **即時媒體串流**：低延遲直播、雲端遊戲畫面串流（用其 datagram/媒體通道）。
- **P2P 資料通道**：`RTCDataChannel` 可傳任意資料（檔案、遊戲狀態），走 SCTP-over-DTLS，可配置可靠/有序與否——不限於音視訊。

多方拓樸（多人時媒體怎麼走）三選一：

```
mesh（每人連其他所有人，無 server）
  A───B
  │ × │     N 人＝N×N 連線、每人上傳 N-1 份
  C───D

SFU（server 選擇性轉發、不解碼，每人上傳 1 份）
  A ──┐
  B ──┼── SFU ──> 各自收 N-1 份原始流
  C ──┘

MCU（server 解碼後混流成一路，每人收 1 份）
  A ──┐
  B ──┼── MCU ──> 各收 1 路合成畫面
  C ──┘
```

- **mesh**：每人與其他所有人直接 P2P 連，無媒體 server。N×N 連線、每人要上傳 N-1 份自己的流——上傳頻寬隨人數爆炸，僅適合極小群（約 ≤4–5 人）。
- **SFU（Selective Forwarding Unit）**：一台 server 收每人**一份**上傳流，**選擇性轉發**給其他人（不解碼不混流）。每人上傳 1 份、下載 N-1 份。擴展性最佳，是多人會議主流。
- **MCU（Multipoint Control Unit）**：server 把所有人的流**解碼、混成一個合成畫面再重新編碼**，每人只上傳 1 份、只下載 1 份合成流——client 端最省，但 server CPU 極重（每路會議都要轉碼）。Jitsi Videobridge（JVB）是 SFU。

### 保證與限制

保證：**端到端加密**（SRTP/DTLS 強制）、**低延遲**（UDP-based、為即時最佳化）、**P2P 直連可能性**（直連時媒體不經你的 server，省頻寬與成本）、瀏覽器原生（免裝外掛）。

限制：

- **NAT 穿透不保證直連成功**：symmetric NAT 等情境必須走 TURN relay，這時媒體經你的 server、頻寬成本回來了。實務上約有可觀比例（視網路環境，常見估計 1–2 成）的連線需要 TURN。
- **信令要自己做**：標準不給，連線交換 SDP 的整套機制是你的責任。
- **多方擴展要選拓樸**：mesh 撐不了多人，得自建/採用 SFU 或 MCU——這是一塊有狀態、吃頻寬/CPU 的伺服器基建。
- **不是「可靠訊息匯流排」**：媒體預設容丟包換低延遲；`RTCDataChannel` 可設可靠，但 WebRTC 整體是為即時、非為保證投遞設計。

worked example（拓樸頻寬對照）：4 人會議、每路視訊 1 Mbps。
- **mesh**：每人上傳給其他 3 人＝3 Mbps 上傳、下載 3 人＝3 Mbps 下載；無 server，但若擴到 10 人，每人上傳 9 Mbps，家用上行直接塞爆。
- **SFU**：每人只上傳 1 份給 SFU＝**1 Mbps 上傳**（與人數無關），下載 N-1＝3 Mbps；SFU server 進 4 Mbps、出 4×3＝12 Mbps（轉發不轉碼，CPU 輕）。10 人時每人上傳仍是 1 Mbps，client 上行不爆——這就是 SFU 勝 mesh 的關鍵：上傳成本不隨人數成長。
- **MCU**：每人上傳 1 Mbps、下載**只 1 Mbps**（合成流），client 最省；但 server 要把 4 路解碼＋混流＋重新編碼，CPU 隨會議路數與人數線性爆，且混流引入額外延遲。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| mesh（P2P） | 無媒體 server、延遲最低、成本最省 | 1對1、極小群（≤4–5 人） | 上傳隨人數爆炸、不可擴展 |
| SFU | 上傳固定 1 份、擴展性最佳、不轉碼 CPU 輕 | 多人會議（主流，5–100+ 人） | 下載仍 N-1；要自建/採用 SFU 基建 |
| MCU | client 端上下行都最省（各 1 份） | client 頻寬/算力極受限、需固定合成版面 | server 轉碼 CPU 極重、成本高、增延遲 |
| WebSocket＋server 中轉 | 走 TCP、過 proxy 容易、實作簡單 | 非媒體的即時資料、不在意 P2P/超低延遲 | 媒體走它頻寬與延遲都遠差於 WebRTC |

選擇判準：1對1 或極小群→mesh；多人會議要擴展→SFU；client 端極受限且要固定合成畫面→MCU。商用託管（如各家 RTE 平台）vs 自架開源（如 Jitsi/coturn）的取捨是成本與掌控度：自架零授權費但要自己營運 SFU＋TURN 基建，商用按量計費但省營運。

### 常見誤解與陷阱

- **「WebRTC 是 P2P 所以不用 server」**：只有**媒體在直連成功時**不經 server；**信令一定要 server**、**TURN relay 在直連失敗時也要 server**、**多人幾乎都要 SFU/MCU server**。把 WebRTC 當「零伺服器」會在 NAT 穿透與多人時翻車。
- **沒部署 TURN**：只靠 STUN，symmetric NAT 後的使用者會連不上（媒體建不起來）；生產級 WebRTC **必須**有 TURN（coturn）兜底，這是最常被漏掉的一塊。
- **以為 mesh 能撐多人**：4 人勉強，8 人每人上傳 7 份，家用上行直接崩——多人務必上 SFU。
- **混淆 SFU 與 MCU**：SFU 只轉發（不解碼、CPU 輕、保留各路原始流可做版面）；MCU 混流（解碼重編、CPU 重、client 只收一路）。選錯會把成本壓在錯的地方（SFU 壓頻寬、MCU 壓 server CPU）。
- **用 GitHub release tag 判斷開源元件是否停更**：某些 WebRTC 開源元件的 tagged release 頁可能停在一兩年前，但 `master` 分支的 commits 仍活躍——只看 release 頁會誤判已停維護，要看 commit 活動。
- **把信令通道的安全當成媒體的安全**：媒體有 SRTP/DTLS 強制加密，但 SDP 信令是你自己的通道，若信令沒上 TLS，candidate/能力資訊會外洩——信令安全要自己保證。

### 延伸閱讀

- W3C — WebRTC: Real-Time Communication in Browsers（Recommendation）：https://www.w3.org/TR/webrtc/
- RFC 8445 — Interactive Connectivity Establishment (ICE)：https://www.rfc-editor.org/info/rfc8445/
- RFC 8489 — Session Traversal Utilities for NAT (STUN)：https://www.rfc-editor.org/rfc/rfc8489.html
- RFC 8656 — Traversal Using Relays around NAT (TURN)：https://www.rfc-editor.org/rfc/rfc8656.html
- coturn — 開源 TURN/STUN server：https://github.com/coturn/coturn
