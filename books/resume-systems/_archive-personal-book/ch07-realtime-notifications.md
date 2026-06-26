# ch07 — 即時通知系統：WebSocket + Redis Pub/Sub 的扇出與多裝置同步

> **本章解決什麼問題**：這是 Part III「LetsTalk：即時通訊」的第一章，把你履歷上那句「自提自建即時通知系統（WebSocket + Redis Pub/Sub，~3,200 並發連線、~10M 訊息/月，補上 FCM 在中國等市場不可用的缺口）」從工作級熟練挖到機制級。前面 Part II 你重走了 NeoBards 的分散式戰場；現在回到 LetsTalk，從你親手撐起的那條長連線開始。本章只挖「在線即時推送」這一段：訊息怎麼從一台 WS server 跨到另一台、為什麼 Redis Pub/Sub 能做即時卻不能做保證送達、多裝置與離線補發為什麼必須另走一條路。後面 ch08 接視訊、ch09 接排程；Redis 內部與 Streams 的深掘留給 ch17，多裝置已讀同步的一致性模型留給 ch11。

```
 Part I    開場與透鏡   ch01-02   把履歷讀成系統地圖、五個故障問句
     |
     v
 Part II   NeoBards     ch03-06   RDS -40%、結算 pipeline、剖析、可觀測性
     |
     v
 Part III  LetsTalk     ch07-09   即時通知、WebRTC、排程訊息          ◄ 你在這裡
     |
     v
 Part IV   橫切老問題   ch10-18   交付/一致/並發/時間/背壓/觀測/身分/快取/雲端
     |
     v
 Part V    收官         ch19-20   面試級敘事、地圖與下一步
```

## 從你已知的出發

當年在 LetsTalk，你做了一個在那個時間點不算流行、現在回頭看相當有膽識的決定：不外包推送，自己提案、自己建一套即時通知系統。理由很實際——你們的主力市場有中國，而 FCM（Firebase Cloud Messaging）在中國的長城防火牆後面根本連不上（2026-06，這個事實沒變，Google 服務自 2014 年起被牆，FCM、Firestore 都不可達）。你不能把「使用者收不收得到通知」這件事，押在一條對你的核心市場根本斷掉的鏈路上。

所以你搭了一套：手機 App 開一條 WebSocket 長連線到你的後端，後端把「誰在哪台機器上」這件事，靠 Redis Pub/Sub 在多台 WS server 之間串起來。規模你記得很清楚——**~3,200 並發連線、~10M 訊息/月**，500K+ 註冊使用者裡同時在線的那一小撮，分散在你那幾台 ECS 後面。訊息進來，找到收件人在哪台，推過去。聽起來很直接，你也確實讓它跑起來了。

這套東西在你腦子裡的形狀，大概是這樣：「WebSocket 是雙向的，Redis Pub/Sub 是訊息匯流排，發到 channel，訂閱的那台收到，推給用戶。」這個心智模型**讓系統跑起來綽綽有餘**，但它藏了三個你當年大概沒停下來細想的東西：

第一，那條 WebSocket 連線的「狀態」到底綁在哪？為什麼長連線跟無狀態的 HTTP 請求不一樣，不能隨便往任何一台機器丟？

第二——這是最致命的——**Redis Pub/Sub 根本不是訊息佇列**。它是 fire-and-forget、at-most-once、零持久化。發出去的那一刻，只送給「此刻正連著」的訂閱者；任何一個訂閱者那一瞬間斷線，那則訊息對它就**永遠消失**了，沒有 replay、沒有 buffer、沒人記得它存在過。你的系統能跑，是因為「在線即時通知」剛好容忍這種損失；但只要你以為它幫你「保證送達」，你就在一個會悄悄掉訊息的地基上蓋房子。

第三，「使用者 B 有手機又有平板」這件事，你的 Pub/Sub 架構其實**完全不負責**。多裝置同步、已讀狀態、平板斷線時錯過的那則訊息怎麼補——這些都不是 Pub/Sub 能解的，得另外走一條路。你當年大概是走了（DB 拉取、未讀計數），但你可能沒把「為什麼即時這條路和補發那條路必須分開」這件事，講成一句清楚的話。

這一章就是來把這三件事挖穿的。

## WebSocket：那條長連線的狀態，綁死在某一台機器上

先把機制攤開。你用 WebSocket 用到很熟，但「它底下怎麼從一個 HTTP 請求變成一條全雙工長連線」這一步，值得你停下來重看，因為**擴展的難處全藏在這一步裡**。

WebSocket 由 **RFC 6455** 定義（2026-06 仍是現行標準）。它不是另起爐灶的協定，而是「劫持」一個普通的 HTTP 連線：

```
Client                                    Server
  │                                          │
  │  GET /ws HTTP/1.1                         │
  │  Host: letstalk.example                   │
  │  Upgrade: websocket                       │   ① HTTP upgrade 請求
  │  Connection: Upgrade                      │      （走的是 80/443，
  │  Sec-WebSocket-Key: dGhlIHNhbXBsZQ==      │       穿得過防火牆與代理）
  │  Sec-WebSocket-Version: 13                │
  │ ────────────────────────────────────────►│
  │                                          │
  │  HTTP/1.1 101 Switching Protocols         │   ② 握手成功，
  │  Upgrade: websocket                       │      同一條 TCP 連線
  │  Connection: Upgrade                      │      升級成全雙工
  │  Sec-WebSocket-Accept: s3pPLMBiTxa…       │
  │ ◄────────────────────────────────────────│
  │                                          │
  │ ═══════════ 全雙工 frame 雙向流動 ═══════════ │   ③ 之後不再是
  │                                          │      請求/回應，
  │ ◄═══ frame（server→client，不 mask）═════ │      兩端隨時可推
  │ ════ frame（client→server，masked）═════► │
  │                                          │
  │ ◄═══ ping（opcode 0x9）═══════════════════ │   ④ 心跳：
  │ ════ pong（opcode 0xA）═════════════════► │      確認連線還活著
```

幾個你可能沒留意的規格細節，每一個都有它的理由：

- **client→server 的 frame 一律 masked**（用一個 32-bit masking key 對 payload 做 XOR）；**server→client 則 MUST NOT mask**。這不是加密——masking key 就明文寫在 frame 裡，誰都解得開。它的目的是防「快取污染攻擊」：早年有中間代理會把 WebSocket 的 frame 內容誤判成 HTTP 回應拿去快取，masking 讓 payload 在線上看起來像隨機位元組，騙不過代理（這就是 RFC 6455 §10.3 的設計動機）。你寫業務時從不碰這層，但它解釋了為什麼 WebSocket library 一定要區分 client/server 角色。
- **ping/pong 是 control frame**（opcode 0x9 / 0xA），payload ≤ 125 bytes、不可分片，專門做心跳。為什麼需要心跳？因為一條 TCP 連線**「斷掉」和「閒著沒講話」在作業系統那層長得一模一樣**——對端拔網路線、手機進電梯、NAT 表項超時，你這邊的 socket 可能還傻傻地以為連著。沒有應用層心跳，你會累積一堆「幽靈連線」：佔著記憶體、算進你的並發數、但推什麼過去都石沉大海。你那 ~3,200 並發連線裡，任何時刻都有一小撮其實已經死了只是還沒被發現——心跳的間隔，決定了你多久發現。

挖到這裡，**擴展的核心難題就現形了**：HTTP 是無狀態的，一個請求打到哪台機器都行，所以你可以拿任何 load balancer 隨便輪詢分流。但 **WebSocket 是 stateful、long-lived 的**——「使用者 B 的那條連線」是一個具體的、活在**某一台特定 WS server 的記憶體裡**的物件（一個 socket file descriptor、一些 session 狀態）。

這就帶出兩個直接後果：

1. **sticky session（session affinity）幾乎是強制的**。一旦 B 跟 server-2 握完手、連線建立，後續這條連線的所有 frame 都必須走 server-2，不能中途被 LB 改派到 server-3——server-3 上根本沒有這條 socket。所以你的 ALB/LB 得認得這條連線、把它釘在 server-2 上。

2. **「發訊息給 B」這件事，發起的那一端根本不知道 B 在哪台機器上**。當 A 從 server-1 進來一則「給 B」的訊息，而 B 連在 server-2——server-1 手上沒有 B 的 socket。這就是為什麼你需要一個跨機器的「後台匯流排（backplane）」把訊息送到正確那台。你選的那個 backplane，就是 Redis Pub/Sub。

> **我以為 vs 實際**：你大概記得「WebSocket 可以橫向擴展，多開幾台就好」。可以，但 RFC 6455 **本身完全不規範擴展**——sticky session + pub/sub backplane 是部署架構的慣例，不是協定給你的。協定只管「一條連線」；「一萬條連線怎麼分散到多台、跨台怎麼找人」全是你自己要解的工程問題。你當年解了，但它從來不是 WebSocket「附帶」給你的。

## Redis Pub/Sub 當扇出層：訊息怎麼跨機器找到正確那台

現在來看你的 backplane。拓樸長這樣：

```
            ┌─────────────────────────────────────────────┐
            │ Redis（Pub/Sub）：發進來就廣播給            │
            │ 「此刻正訂閱」的所有 WS server，由各機過濾  │
            └──────┬───────────────┬───────────────┬──────┘
                   │               │               │
               SUB │           PUB │           SUB │
                   │               │               │
            ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
            │ WS server-1 │ │ WS server-2 │ │ WS server-3 │
            │ 持有 A C D  │ │ 持有 B手機  │ │ 持有 B平板  │
            └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
            sticky │        sticky │        sticky │
            ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐
            │ 用戶 A      │ │ B 的手機    │ │ B 的平板    │
            └─────────────┘ └─────────────┘ └─────────────┘
```

A 要發給 B，但 server-1 不知道 B 在哪。流程是這樣：

1. A 的訊息從 server-1 進來。server-1 不去找 B 的 socket（它沒有），而是 `PUBLISH` 到一個 channel。channel 怎麼命名是設計關鍵——典型做法是**以收件人為 key**，例如 `user:B` 這個 channel。
2. Redis 收到 `PUBLISH user:B {訊息}`，立刻把它**廣播給此刻所有 `SUBSCRIBE user:B` 的訂閱者**。
3. 哪幾台訂閱了 `user:B`？取決於你的訂閱策略。最簡單粗暴的做法是**每台 WS server 訂閱所有 channel（或一個全域 channel），各機自己過濾**——「這則是給 B 的，我手上有 B 嗎？有就推，沒有就丟」。server-2（B 的手機）和 server-3（B 的平板）發現自己手上有 B，推過去；server-1 沒有，丟掉。

這就是「Pub/Sub 廣播 + 各機過濾」。它能 work，但你得清楚它的代價——**廣播是「發給所有訂閱者，由訂閱者自己決定要不要」**。如果你用一個全域 channel，那每一則訊息都會被**送到每一台 WS server**，哪怕收件人只在其中一台。這個「扇出放大」在小規模看不出來，到了熱門群組就會咬你（後面 worked example 會算給你看）。

更精緻的做法是 **per-user channel**（`user:B`）+ 各 server 動態 `SUBSCRIBE`/`UNSUBSCRIBE`：B 一連上 server-2，server-2 就 `SUBSCRIBE user:B`；B 斷線就 `UNSUBSCRIBE`。這樣 Redis 只把 `user:B` 的訊息送給真正持有 B 的那幾台，省掉無謂廣播——代價是你得維護「誰訂閱了誰」的動態狀態，且訂閱數會很大（理論上每個在線用戶一個 channel）。這是個典型的取捨：**全域 channel 簡單但浪費頻寬，per-user channel 省頻寬但管理複雜**。

> **如果你今天用 Socket.io（2026-06）**：你不用自己手刻這套廣播+過濾。`@socket.io/redis-adapter`（當前 v8.x）就是把這件事封裝起來——你呼叫 `io.to("user:B").emit(...)`，adapter 底下就是「在本機推給匹配的 client，同時 `PUBLISH` 到 Redis channel，其他 Socket.io server `SUBSCRIBE` 收到後各自推給自己手上匹配的 client」。它**依賴的正是 Redis Pub/Sub 廣播**——所以你接下來要懂的那個「Pub/Sub 致命真相」，Socket.io 一樣逃不掉，只是把它藏在抽象底下。Redis 7.0+ 另有 **sharded Pub/Sub**（`SPUBLISH`/`SSUBSCRIBE`），把 channel 按 hash slot 綁到特定 shard、不再全 cluster 廣播，正是為了解上面那個「全域廣播放大」的問題；Socket.io 也有對應的 sharded adapter。但這是 cluster 規模的優化，你當年 ~3,200 並發的單 Redis 還碰不到那個瓶頸。

## Pub/Sub 的致命真相：它能做即時通知，但不能做保證送達

這一段值得你停下來，因為這是整個系統最容易被記錯、也最容易出事的地方。

**Redis Pub/Sub 是 fire-and-forget、at-most-once、零持久化的。**（2026-06，這個語意從來沒變過，是設計本質。）拆開講：

- **fire-and-forget**：`PUBLISH` 把訊息推給「此刻正連著的訂閱者」，然後**立刻忘記它存在過**。Redis 不記錄這則訊息、不追蹤誰收到了、不等任何 ack。`PUBLISH` 的回傳值只告訴你「此刻有幾個 client 收到了」——`PUBLISH user:B msg` 回傳 0，意思就是「B 此刻沒人訂閱，這則訊息我直接丟了」，而且**它不會報錯**。
- **at-most-once**：一則訊息最多送達一次，也可能一次都不送達。沒有重試、沒有 redelivery。
- **零持久化**：訊息**不寫任何地方**。沒有 log、沒有 buffer、沒有 replay。訂閱者斷線的那段期間，所有發給它的訊息**永久消失**，重連後也補不回來——它得重新 `SUBSCRIBE`，而 `SUBSCRIBE` 只讓它收到**之後**的新訊息。

把這三點合起來看，一個關鍵推論浮現：**Redis Pub/Sub 沒有「收件匣」的概念**。它是一根管子，不是一個信箱。訊息流過管子的那一瞬間你不在管口接著，就沒了。

這直接解釋了你系統的能力邊界：

| | Pub/Sub 能 | Pub/Sub 不能 |
|---|---|---|
| 在線即時推送 | ✅ B 此刻連著，立刻收到 | |
| 保證送達 | | ❌ B 斷線 0.5 秒，那則訊息永遠不會到 |
| 離線補發 | | ❌ 沒持久化，補不出來 |
| 順序保證 | 單一 channel 內 FIFO（同一 Redis 連線） | ❌ 跨 channel、跨重連無保證 |
| 已讀回執 | | ❌ Pub/Sub 不知道誰讀了什麼 |

> **我以為 vs 實際**：這是本書 ch01 就拿來打臉的第一個例子——「Redis Pub/Sub 是訊息佇列」。**它不是。** 訊息佇列（SQS、RabbitMQ、Redis Streams）會把訊息存著、追蹤誰處理了沒、沒 ack 就重投。Pub/Sub 全部沒有。如果你當年心裡某個角落覺得「訊息發進 Redis 就安全了」，那是把 Pub/Sub 當成它不是的東西。你的系統能跑得好，恰恰是因為「在線即時通知」這個 use case **本來就容忍掉訊息**——錯過的通知不是世界末日，重要的訊息本體你另有持久化（DB）兜底。Pub/Sub 在這裡是對的工具，但**只對在這一段**。

那真正的訊息——使用者之間的對話內容——靠什麼保證不丟？靠你**先把它寫進 DB（持久化），再用 Pub/Sub 推一個「你有新訊息」的即時信號**。DB 是真相來源（source of truth），Pub/Sub 只是「叮」一聲的門鈴。門鈴沒響（Pub/Sub 掉了），訊息還在 DB 裡，使用者下次拉取或重連時照樣拿得到。這個「持久層 + 即時信號層分離」的架構，是即時通訊系統的標準骨架——你當年大概是這樣做的（不然 10M 訊息/月早就掉到天怒人怨），但你可能沒把它講成這句清楚的設計原則。

## 多裝置同步與離線補發：必須另走一條路

現在把「B 有手機又有平板」這件事正面拆開。這是你的架構裡 Pub/Sub **完全幫不上忙**的部分。

多裝置的本質問題是：**同一個邏輯收件人（user B），對應多條物理連線**（手機一條、平板一條，甚至可能在不同 WS server 上，如前面拓樸圖 server-2 / server-3）。要把一則訊息「送達 user B」，意味著要送達 B **所有在線的裝置**。

如果你用 per-user channel（`user:B`），這件事 Pub/Sub 順手就做了——手機和平板都 `SUBSCRIBE user:B`，一次 `PUBLISH` 兩端都收到。漂亮。**但這只覆蓋「兩端此刻都在線」這一種情況**。一旦平板斷線（進地鐵、App 被系統殺背景、網路抖一下），它在 `user:B` 上的訂閱就沒了，這期間發的訊息它**永久錯過**——而手機那邊收得好好的。於是 B 拿起平板，發現對話「少了一段」，中間那幾則手機上有、平板上沒有。

這就是為什麼**離線補發必須另走一條路，而且這條路一定不能是 Pub/Sub**。可選的路有幾條，各有取捨：

| 補發方案 | 機制 | 代價 |
|---|---|---|
| **拉取（DB pull）** | 裝置重連時，帶上「我最後收到的訊息 ID / 時間戳」，向 DB 要「之後的所有訊息」 | 簡單、可靠（DB 是真相來源）；但是「拉」不是「推」，重連那一刻有延遲；要設計好游標 |
| **Redis Streams** | 用 Streams（持久 append-only log + consumer group）取代/補強 Pub/Sub，未讀訊息留在 Pending Entries List，重連後可重讀 | at-least-once、有持久化、能 replay；但更重、要管 consumer group、要 `XACK`，且記憶體成本（見 ch17） |
| **離線推送（FCM/APNs/自建）** | 裝置完全離線（App 沒開），走作業系統級推送把通知喚醒 | 這正是你補 FCM 缺口要解的；見下一節 |

注意這三條路的共同點：**它們都有持久化**。DB 有、Streams 有、FCM 的雲端佇列有。**只有 Pub/Sub 沒有**——這正是為什麼補發不能靠它。

> **跨章指路**：「平板補回那段後，兩端的已讀狀態怎麼對齊、誰算數」——這是**一致性問題**，不是推送問題，留給 ch11（一致性、隔離級別與複製延遲）挖；Redis Streams 的內部與 Pub/Sub 的對照留給 ch17（快取與 Redis 內部）。這裡你只要記住一句話：**Pub/Sub 只管「在線即時」那一段，前後兩端（離線補發、已讀同步）都得另接持久層。**

## FCM 缺口：為什麼要自建，自建放棄了什麼

最後回到你當初做這整套的動機——補 FCM 在中國不可用的缺口。這裡有兩層要分清楚，因為它們解的是**不同的問題**。

**WebSocket + Pub/Sub 解的是「App 開著、連線活著」時的即時推送。** 但手機 App 大部分時間不是開著的——使用者把它切到背景、鎖屏、進 Doze 模式（Android 的省電休眠）。這時候你那條 WebSocket 連線會被作業系統**無情地砍掉或凍結**（為了省電，OS 不會讓背景 App 一直握著長連線）。連線一斷，你的 Pub/Sub 推什麼都到不了——這正是上一節「離線」的極端版：不只是網路抖，是 OS 主動把你斷了。

這就是 FCM 這類**作業系統級推送**存在的理由。它怎麼解這個 WebSocket 解不了的問題？

- **單一系統級長連線**：FCM 不是讓每個 App 各開一條連線，而是**整支手機（Google Play services）只維持一條到 Google 的持久連線**，所有 App 的推送都共用它。這條連線是系統管的、OS 允許它在背景活著——這是普通 App 拿不到的特權。
- **系統級喚醒**：高優先級訊息可以**喚醒 Doze 中的裝置**（喚醒 radio），讓通知即時跳出來；普通優先級則排隊等裝置自己醒來時順帶送（2026-06）。
- **離線佇列（store-and-forward）**：裝置離線時，FCM 把訊息**存在 Google 雲端，最長約 4 週**，裝置重連後依序補送。這是一個你 WebSocket 系統沒有的、由平台白送你的持久收件匣。

把這三點合起來，你就懂了**你自建放棄了什麼**——當 FCM 在中國不可用、你被迫自建時，你失去的不是「推送」這個動作，而是上面三項**作業系統特權**：

| 維度 | FCM（你失去的） | 你的自建 WebSocket（你能做的） |
|---|---|---|
| **電量** | OS 級單一共用連線，省電 | 你的 App 自己維持長連線，背景被 OS 砍、耗電，要靠各種 keep-alive 黑魔法續命 |
| **系統級喚醒** | 高優先級可喚醒 Doze 中的裝置 | ❌ App 在背景被凍結時，你叫不醒它 |
| **離線佇列** | 雲端存 ~4 週、重連補送 | ❌ Pub/Sub 零持久化（所以你得自己用 DB 拉取補上，見上一節） |

這就是「補 FCM 缺口」的真實代價結構：**在中國市場，你別無選擇，必須自建，因為 FCM 根本連不上；但自建換來的是「在線時即時」，換不回「離線時 OS 替你喚醒、替你存著」。** 所以一套完整的方案，往往是**混合的**：在線靠你的 WebSocket、離線靠各市場可用的推送通道（中國用本地廠商通道如極光/JPush、廠商推送，海外才是 FCM/APNs）。你當年補的不是「整個 FCM」，而是「FCM 斷掉的那塊在線即時」——這個邊界要講清楚，不然面試官一句「那離線推送你怎麼辦」就把你問住了。

> **嚴謹度標示**：「FCM 雲端佇列約 4 週」「高優先級喚醒 Doze」是 Firebase 官方文件記載的行為（2026-06），屬平台保證。但「App 背景連線會被 OS 砍」的精確時機（多久、什麼條件）是 OS 與廠商定制的行為，各家 Android（尤其中國廠商的深度定制 ROM）差很大——這是**常見實作行為**而非規格保證，你當年踩過的那些「某品牌手機背景就是收不到」的坑，根源都在這裡。

## 故障模式與防禦

這個系統會怎麼壞、壞了長什麼樣、怎麼防。至少看懂前三個，每一個你當年都可能遇過。

**故障 1：訂閱者斷線那一瞬間的訊息，永久消失（Pub/Sub at-most-once）。**
- **怎麼壞**：B 的手機正在重連（換 wifi、進電梯出來），那 0.8 秒裡 A 發了三則訊息，`PUBLISH user:B` 時 B 的訂閱已經沒了，Redis 直接丟，回傳 0。
- **長什麼樣**：B 重連後對話「跳號」，少了中間那幾則；但**沒有任何錯誤日誌**——Pub/Sub 丟訊息是靜默的，`PUBLISH` 回 0 不是錯誤。這是最陰險的一點：你的監控大概看不到。
- **怎麼防**：**訊息本體必走 DB 持久化**，Pub/Sub 只當「叮」的信號。重連後用「最後收到的訊息 ID」向 DB 拉取補齊。**不要把 Pub/Sub 當送達保證**——它從來不是。（你當年大概做對了 DB 兜底；本書要你能講清楚「為什麼這層不能省」。）

**故障 2：幽靈連線堆積（心跳缺失或間隔太長）。**
- **怎麼壞**：對端硬斷（拔網路、手機沒電、NAT 表項超時），TCP 沒走正常 FIN，你這邊的 socket 還以為活著。沒有應用層 ping/pong，你發現不了。
- **長什麼樣**：並發連線數虛高（你以為 3,200 在線，實際可能只有 2,900 活著），記憶體被死連線佔著，推給「在線」用戶的訊息石沉大海卻不報錯。
- **怎麼防**：應用層 ping/pong 心跳 + idle timeout（一定時間沒收到 pong 就主動關連線、清狀態）。心跳間隔是個取捨：**太短耗電耗頻寬（尤其行動裝置），太長則死連線存活太久**。

**故障 3：廣播扇出放大壓垮 Redis（熱門群組 / 全域 channel）。**
- **怎麼壞**：你用全域 channel「廣播 + 各機過濾」，或一個 10K 成員的熱門群一則訊息要扇出給所有人。每則訊息被送到每一台 WS server（甚至在 Redis cluster 下被廣播到每個節點），訊息量 = 原始量 × 扇出倍數。
- **長什麼樣**：Redis CPU/網路飆高、`PUBLISH` 延遲上升、所有 channel 的即時性一起變差（Redis 命令執行是單執行緒的，一個重操作卡住全部，見 ch17）。
- **怎麼防**：per-user/per-room channel 取代全域廣播（讓 Redis 只送給真正相關的訂閱者）；cluster 規模用 Redis 7+ sharded Pub/Sub（`SPUBLISH`）把廣播限制在 owning shard；超大群（10K+）考慮不走「逐人扇出」而是「客戶端輪詢/拉取」模型。

**故障 4：sticky session 破裂導致連線亂飄。**
- **怎麼壞**：LB 沒設好 session affinity，或某台 WS server 重啟，連線被重新分派；新機器上沒有這條 socket 的狀態。
- **長什麼樣**：連線頻繁掉線重連、用戶體感「一直在轉圈」、訂閱狀態錯亂。
- **怎麼防**：LB 層做 sticky session；WS server 滾動更新時要有 graceful drain（讓舊連線自然斷、客戶端重連到新機器），別硬殺。**接受「連線會重連」是常態**，把重連後的狀態恢復（重新訂閱、拉取漏掉的訊息）做紮實——這比追求「連線永不斷」務實得多。

**故障 5：背景 App 連線被 OS 砍，使用者「收不到通知」（FCM 缺口的反面）。**
- **怎麼壞**：App 切背景，OS（尤其中國廠商 ROM）凍結/砍掉你的 WebSocket，你的即時推送到不了。
- **長什麼樣**：使用者抱怨「App 沒開就收不到訊息」，且因廠商而異（某些品牌特別嚴重）。
- **怎麼防**：在線靠 WebSocket，**離線必須有獨立的 OS 級推送通道兜底**（海外 FCM/APNs、中國本地廠商推送）。這正是「自建補 FCM 缺口」之所以只能補「在線那一段」的根因——離線喚醒是 OS 特權，你的應用層連線拿不到。

## 紙上推演

### 推演題 1：手追「A 發給 B，B 有手機+平板兩端、平板剛好斷線」的完整路徑 **[20 分鐘]** ★★

把這條訊息從 A 按下送出，追到 B 兩端最終各自的狀態。設定：採 per-user channel（`user:B`）；A 連 server-1、B 手機連 server-2、B 平板連 server-3；訊息本體寫 DB。請逐步寫出：(a) 訊息怎麼從 server-1 到達手機與平板；(b) 平板在 `PUBLISH` 那一刻剛斷線，它那份去哪了；(c) 平板重連後怎麼補回。

### 推演題 2：估「熱門群 10K 成員一次廣播」對 Pub/Sub 扇出的訊息放大 **[15 分鐘]** ★★

一個 10,000 成員的群，假設此刻 30% 在線（3,000 人），分散在 5 台 WS server 上（平均每台 600 人）。一則群訊息發出。比較兩種架構下 Redis 要處理的「訊息投遞次數」：(a) 全域 channel「廣播 + 各機過濾」（每台都收到、自己過濾）；(b) per-room channel，5 台都 `SUBSCRIBE room:X`。再想：哪一種的數字會隨「WS server 台數」增長，哪一種隨「在線人數」增長？

### 推演題 3：判斷「Pub/Sub 換成 Streams 能解決什麼、代價是什麼」 **[15 分鐘]** ★★★

有人提議把通知層的 Redis Pub/Sub 全換成 Redis Streams。列出：(a) 換了能解決前面哪幾個故障；(b) 為此付出哪些代價；(c) 你會不會換，理由是什麼。

### 推演解答

**題 1 解答：**

(a) **訊息到達兩端的路徑**：A 的訊息進 server-1。server-1 做兩件事，順序很重要——**先把訊息本體寫進 DB（持久化，這是真相來源）**，再 `PUBLISH user:B {新訊息信號}`。Redis 把它廣播給此刻所有 `SUBSCRIBE user:B` 的訂閱者。手機在 server-2、平板在 server-3，兩台都訂閱了 `user:B` ⟹ 兩台都收到 ⟹ 各自透過自己持有的 WebSocket 推給手機 / 平板。手機那端：收到，顯示。

(b) **平板那份去哪了**：關鍵在「`PUBLISH` 是 fire-and-forget，只送給此刻正連著的訂閱者」。平板在 `PUBLISH` 那一刻已經斷線 ⟹ server-3 上平板的 socket 沒了，server-3 可能已經 `UNSUBSCRIBE user:B`（如果你做了動態訂閱），或 server-3 收到了但發現手上的平板 socket 已死、推不出去。**無論哪種，平板那份就這樣消失了**——Redis 不會記得它、不會重投、不報錯。此刻系統狀態：DB 有這則訊息（持久）、手機顯示了、平板沒有。**訊息本體沒丟（在 DB），丟的只是「平板的即時推送」那一下。**

(c) **平板重連後怎麼補**：平板重連，重新 `SUBSCRIBE user:B`（只能收到**之後**的新訊息，補不回剛才那則）。所以補發**不能靠 Pub/Sub**——平板重連時要帶上「我最後收到的訊息 ID / 時間戳」，向 **DB 拉取**「之後的所有訊息」，把缺的那段補齊。補完，兩端一致。

**這題的核心**：訊息分兩層——**持久層（DB，保證不丟）+ 即時信號層（Pub/Sub，盡力即時、允許丟）**。Pub/Sub 掉的那一下不致命，因為 DB 兜底 + 重連拉取補上。**常見錯路**：以為「`PUBLISH` 出去 = 送達」，於是不做 DB 持久化、不做重連拉取——那平板那則就真的永久消失了。當年的你如果系統穩定跑了 10M 訊息/月，幾乎可以肯定你做了 DB 兜底；本書要你能把「為什麼這層省不得」一口氣講清楚。

**題 2 解答：**

設投遞次數 = Redis 為了把這「一則」群訊息送出去，總共要往訂閱者推送幾次。

(a) **全域 channel 廣播 + 各機過濾**：訊息發到全域 channel，Redis 把它送給**每一台訂閱的 WS server**（5 台）⟹ **5 次跨機投遞**（每台收到後再在本機把訊息分發給自己手上的在線成員，那是 server 本機的事，不算 Redis 的投遞）。這個數字 = **WS server 台數**，跟在線人數無關。看起來很省？陷阱在「各機過濾」——每台都收到**全部**訊息流（包括跟它一個成員都不相關的訊息），server 本機要做大量「這則跟我無關」的丟棄；在 Redis cluster 下，全域 channel 還會被**廣播到每個 cluster 節點**，放大更嚴重。

(b) **per-room channel（`room:X`）**：5 台持有該群成員的 server 都 `SUBSCRIBE room:X`，Redis 把訊息送給這 5 台 ⟹ 也是 **5 次**。但差別在：Redis **只把 `room:X` 的訊息送給訂閱了 `room:X` 的台**，不訂閱的台（手上沒這群成員的）完全不收——沒有「各機過濾」的浪費。

**隨什麼增長**：兩種架構下 Redis 的跨機投遞次數都 ≈ **持有在線成員的 WS server 台數**（這題裡都是 5）。真正的差別是**「不相關的台收不收得到訊息」**：全域 channel 下**所有**台都收到所有訊息（隨總台數增長、且每台承受全部訊息流）；per-room 下**只有相關的台**收到（隨「該群分佈在幾台」增長）。所以當你有很多群、很多台時，全域 channel 的浪費是 O(總訊息量 × 總台數)，per-room 是 O(總訊息量 × 平均每訊息相關台數)——後者小得多。**這就是為什麼故障 3 的防禦是「per-room/per-user channel 取代全域廣播」。** 注意：本題只算「Redis 跨機投遞」這一層的放大；連線數本身的排隊與容量數學（3,000 人同時在線對單機的壓力）屬排隊理論，見《等待的數學》（queue）。

**題 3 解答：**

(a) **Streams 能解的故障**：主要是**故障 1（斷線期間訊息消失）**。Streams 持久化（append-only log）+ consumer group + Pending Entries List，訂閱者斷線期間的訊息**留在 log 裡**，重連後可重讀（`XREADGROUP`）、未 `XACK` 的會留在 PEL 可被重新接手 ⟹ **at-least-once**，不再靜默掉訊息。等於把「離線補發」這條路也收進 Redis 自己（不必另走 DB 拉取那麼明顯地分兩層）。

(b) **代價**：① **更重**——要管 consumer group、要 `XACK` 確認、未確認訊息累積在 PEL 要處理；② **記憶體成本**——log 持久存在 Redis 記憶體裡，要設 `MAXLEN` 修剪，否則無限增長（Pub/Sub 零儲存，Streams 反過來什麼都存）；③ **at-least-once ⟹ 可能重複** ⟹ 又回到冪等問題（消費端要去重，見 ch10）；④ 心智負擔——從「發了就忘」變成「要追蹤每個 consumer 讀到哪」。

(c) **換不換**：我的判斷是——**通知的「即時信號」這一層不換，繼續用 Pub/Sub**（它就該是 fire-and-forget 的廉價門鈴）；**真正需要持久與補發的訊息本體，本來就該在 DB / 專門的訊息儲存**。把 Streams 硬塞進「即時門鈴」這層，是用一個重工具解一個本來就允許丟的問題，徒增記憶體與複雜度。Streams 真正的甜蜜點是「需要持久 + at-least-once + 多消費者協作」的場景（任務佇列、事件溯源），不是「在線即時通知」。**常見錯路**：看到「Pub/Sub 會掉訊息」就反射性想換 Streams——但「會掉訊息」對即時通知這個 use case 是**可接受的**（DB 兜底），不是 bug。先問「我這層真的需要不丟嗎」，再決定要不要付 Streams 的代價。

## 自我檢核

口頭自答，講得出來才算過關：

1. 為什麼 WebSocket 連線必須 sticky 到某一台機器，而 HTTP 請求可以隨便分流？這個差別的根源是什麼？（提示：狀態活在哪）
2. A 從 server-1 發訊息給連在 server-2 的 B，server-1 手上沒有 B 的 socket——這則訊息是怎麼跨機器找到 B 的？「廣播 + 各機過濾」和「per-user channel」差在哪？
3. 用一句話講清楚「Redis Pub/Sub 為什麼能做即時通知卻不能做保證送達」。`PUBLISH` 回傳 0 代表什麼、為什麼這很危險？
4. 你的對話訊息（10M/月）靠什麼保證不丟？Pub/Sub 在這個架構裡扮演什麼角色、不扮演什麼角色？
5. B 的平板斷線期間錯過的訊息，重連後怎麼補？為什麼這條補發的路一定不能是 Pub/Sub？三條補發路（DB 拉取 / Streams / OS 推送）的共同點是什麼？
6. 你當年自建補 FCM 缺口，自建相對於 FCM **放棄了哪三項**？為什麼這三項是「作業系統特權」、你的應用層連線拿不到？
7. 「熱門群 10K 成員一次廣播」對 Redis 的扇出放大，在全域 channel 和 per-room channel 下分別隨什麼增長？防禦是什麼？
8. 換成今天（2026-06），你會用 Socket.io + `@socket.io/redis-adapter` 還是繼續手刻？adapter 把什麼藏起來了、又改變了哪個底層事實沒？（提示：它依賴的還是 Pub/Sub 廣播）

## 延伸閱讀

- **RFC 6455 — The WebSocket Protocol**（https://www.rfc-editor.org/rfc/rfc6455）：讀 §5（frame 格式、masking、opcode）與 §5.5（ping/pong control frame）。你用 WebSocket 多年，但 client→server 為什麼一律 masked、心跳為什麼是 control frame 而非業務訊息，答案都在這裡。注意 §1.1 明說協定不規範擴展——sticky session 是你的事。
- **Redis Pub/Sub 官方文件**（https://redis.io/docs/latest/develop/pubsub/）：讀「fire and forget」與和 Streams 對照的段落。把「at-most-once、無持久化、離線訂閱者永久錯過」這幾句官方原文背下來，這是你系統能力邊界的法律條文。順帶看 `SPUBLISH`/`SSUBSCRIBE`（sharded Pub/Sub，Redis 7+）解全域廣播放大。
- **Redis Streams 用例文件**（https://redis.io/docs/latest/develop/use-cases/streaming/）：讀 consumer group 與 Pending Entries List。這是「離線補發要持久」那條路在 Redis 內的選項，與 Pub/Sub 的精確對照（at-least-once + `XACK` vs at-most-once + fire-and-forget）。深掘留 ch17。
- **Socket.IO Redis adapter 文件**（https://socket.io/docs/v4/redis-adapter/）：讀它怎麼用 Pub/Sub 在多節點間廣播封包。看清楚「`io.to(room).emit` ⟹ 本機推 + `PUBLISH` 到 Redis ⟹ 其他 server `SUBSCRIBE` 收到再推」——你當年手刻的東西，它幫你封裝了，但底層依賴的 Pub/Sub 限制一字不變。
- **Firebase「Send messages to Android」官方說明**（https://firebase.blog/posts/2025/04/fcm-on-android/ 與 https://firebase.google.com/docs/cloud-messaging/android-message-priority）：讀 Doze 模式下高/普通優先級的差別、雲端佇列（離線約 4 週）。這是你「自建放棄了什麼」的官方依據——OS 級喚醒與離線佇列是平台特權，自建拿不到。
- **AppInChina「Does Firebase Work in China?」**（https://appinchina.co/does-firebase-work-in-china/）：印證你當年的前提——FCM 在中國被長城防火牆擋住、標準推送 SDK 失效（2026-06 仍然如此），以及本地替代通道（極光/JPush 等）的存在。這解釋了你為什麼非自建不可。

---

### 本系統五軸體檢

| 軸 | 即時通知系統（WebSocket + Redis Pub/Sub）在這一軸的答案與代價 |
|---|---|
| **交付（delivery）** | Pub/Sub = **at-most-once**：訂閱者斷線期間的訊息**靜默永久丟失**，`PUBLISH` 回 0 不報錯。靠「DB 持久化訊息本體 + Pub/Sub 只當即時信號 + 重連拉取補發」把交付保證從 Pub/Sub 移到 DB。 |
| **持久（durability）** | Pub/Sub **零持久化**——WS server 重啟、連線斷、Redis 重啟，in-flight 的推送全失憶。真相來源在 DB；連線本身不持久（接受重連是常態，做好重連恢復）。 |
| **分區（consistency）** | 多裝置（手機/平板）+ 離線補發 ⟹ 各端看到的對話**最終一致**，靠重連拉取對齊；已讀同步是另一個一致性問題（見 ch11）。Pub/Sub 只保在線那一段的即時。 |
| **並發（concurrency）** | ~3,200 並發長連線分散在多台 WS server，sticky session 釘住每條連線；跨機找人靠 Redis Pub/Sub 廣播。扇出放大（熱門群/全域 channel）是並發壓力的放大器——per-room channel / sharded Pub/Sub 防之。 |
| **觀測（observability）** | **最弱的一軸**：Pub/Sub 掉訊息是**靜默的**（`PUBLISH` 回 0 非錯誤），幽靈連線讓「在線數」虛高。要監控：真實活躍連線數（心跳驗證）、`PUBLISH` 觸達 0 的比例、重連拉取補發的訊息量（補太多 = 即時層在大量掉訊息的徵兆）。 |
