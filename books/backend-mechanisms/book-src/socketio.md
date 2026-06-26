# Socket.io：fallback、rooms 與 redis-adapter

你接到一個看似簡單的需求：在產品裡加一個聊天室。瀏覽器原生就有 `WebSocket`，握手、傳 frame，文件十頁就讀完了（WebSocket 協定本身的 frame、ping-pong 與遮罩，見〈WebSocket：frame、ping-pong 與水平擴展〉）。你寫了個 demo，本機跑得漂亮——直到把它丟上線。

第一通客訴來自一個坐在公司防火牆後面的使用者：他的 WebSocket 升級握手被代理擋了，連都連不上。第二通來自手機在電梯裡掉訊號的使用者：連線斷了，重連之後那十秒的訊息全部消失，他的對話出現一個無聲的洞。第三通最詭異——你加開了第二台 server 分攤負載之後，一個房間裡有一半的人收不到另一半的人發的訊息，而且「收不到」的那一半隨機飄移。三通客訴，三個完全不同層次的問題：**連得上嗎、斷線怎麼補、跨機器怎麼廣播**。Socket.io 存在的理由，就是它把這三件事一次打包，讓你不必在裸 WebSocket 上把這三個輪子各重造一遍。

但「打包」是有代價的。Socket.io 不是 WebSocket，它在 WebSocket 之上疊了自己的一層協定；它給你的每一個方便，底下都藏著一個你遲早要看懂的機制，否則上面那三通客訴只會換個形式回來。這一章把這層皮剝開，看清楚它到底替你做了什麼、又把哪些難題只是搬到了別處。

## 它根本不是一個 WebSocket

第一個要扭正的直覺：Socket.io 的 client **不能**用瀏覽器原生的 `new WebSocket(url)` 連上 Socket.io 的 server，反之亦然。它們講的不是同一種話。Socket.io 是一套**函式庫**（client 一半、server 一半），定義了自己的封包格式，這層封包再跑在一個叫 **Engine.IO** 的底層連線之上。WebSocket 只是 Engine.IO 可以選用的其中一種 transport——不是全部。

這個分層是理解後面一切的鑰匙，值得先畫清楚：

```
Socket.io  layer:  namespaces / rooms / events / acknowledgements
Engine.IO  layer:  one logical connection, transport upgrade, heartbeat
transport  layer:  HTTP long-polling  |  WebSocket  |  WebTransport
```

上面那層管「語意」（你 emit 一個 `chat message` 事件、廣播給某個 room、要不要 ack）；中間 Engine.IO 那層管「維持一條邏輯連線」——不管底下實際是哪種 transport、升級到哪裡、心跳怎麼跳；最底下才是真正搬位元組的 transport。這三種 transport 不是平起平坐的預設選項：下一節會看到，預設總是先用 long-polling 起手，WebSocket 是主要的升級目標，而 WebTransport（v4.7+ 才加入、走 HTTP/3、目前除 Safari 外的主流瀏覽器都支援）是「有就更好」的可選升級項，不是主力。把這三層分開，下面每一個機制各自落在哪層就清楚了，也才能解釋為什麼 Socket.io 在某些地方的行為和裸 WebSocket 截然不同。

## 為什麼不直接開 WebSocket：那通連不上的客訴

回到第一通客訴。理論上 WebSocket 是雙向即時通訊的最佳解，frame 開銷小、延遲低。但「理論上最佳」和「實務上一定連得上」是兩回事。WebSocket 的升級握手是一個帶 `Upgrade: websocket` 標頭的特殊 HTTP 請求，而世界上有大量的中間設備——企業代理、防毒軟體、某些老舊的負載均衡器——會看不懂這個升級、或乾脆把它擋掉。對這些環境裡的使用者，裸 WebSocket 不是「比較慢」，是**根本連不上**。

Socket.io 的解法叫 **transport fallback**，而它的具體做法常和直覺相反：**它預設先用 HTTP long-polling 起手，連上之後才「升級」到 WebSocket。** 為什麼是退而求其次的 long-polling 先上？因為 long-polling 就是一連串普通的 HTTP 請求（一個長掛的 GET 收資料、短促的 POST 送資料），幾乎能穿過所有中間設備——它是「最可能成功」的 transport。先用最可靠的方式把連線建起來、確保使用者一定連得上，再悄悄試著換到更好的 WebSocket。連不上 WebSocket（被擋了）就一直留在 long-polling，連得上就升級，使用者全程無感。

升級的那一刻有一個精巧的小協定，值得看清楚，因為它解釋了 Socket.io 一個容易被忽略的行為。client 在 long-polling 連著的同時，背地裡開一條 WebSocket，往這條新 transport 送一個 payload 是字串 `"probe"` 的 PING 封包試水溫；server 回一個 `"probe"` 的 PONG，證明這條新路通了。確認通了之後，client 才把舊的 long-polling transport 切成唯讀、清空送出緩衝，最後送一個 `upgrade` 封包正式切換；server 這頭則對還掛在那裡的舊 long-polling GET 回一個 `noop` 封包，逼它返回、把舊 transport 乾淨收掉。整個過程的關鍵是：**升級期間兩條 transport 短暫並存，而且共用同一個 session id**——不是斷掉重連，是同一條邏輯連線換了底層的腿。這也是為什麼 Socket.io 的連線即使「換了 transport」，你的 room 歸屬、事件監聽都不會掉。

這個 fallback 買到的是**相容性保底**：在最惡劣的網路環境下也連得上。代價是協定變複雜了、而且——下一節會看到——它在水平擴展時硬生生塞給你一個額外的約束。

## 心跳：誰在 ping 誰，以及那個容易記反的方向

長連線都有同一個敵人：**沉默的死亡**。連線可能在你不知情的時候斷了——對端崩潰、網路中斷、中間設備把一條 idle 連線靜默砍掉——而 TCP 不會主動告訴你。如果不主動探測，server 會抱著一堆早就死掉的「殭屍連線」，白佔記憶體和檔案描述子；client 則以為自己還連著，發出去的訊息掉進黑洞。

Socket.io 用 Engine.IO 層的心跳解決這件事，而它的方向和很多人記的相反，務必記準：**是 server 主動發 PING，client 回 PONG**（這和 RFC 6455 WebSocket 協定本身那個任一端都可發起的 ping/pong control frame 不是同一層東西——Engine.IO 的心跳是應用層的封包，跑在任何 transport 之上，連 long-polling 都有）。機制是這樣：server 每隔 `pingInterval`（預設 **25000 毫秒**）送一個 PING；client 收到後必須在 `pingTimeout`（預設 **20000 毫秒**）內回一個 PONG。server 沒等到 PONG，就判定這條連線死了、關掉它。反過來，client 若在 `pingInterval + pingTimeout` 內（預設 25 + 20 = 45 秒）連一個 PING 都沒收到，也判定 server 那頭沒了、主動斷開重連。

這兩個數字不是裝飾，它們直接決定了你的系統「多快發現一條死連線」和「多容易誤殺一條活連線」。把 `pingTimeout` 設太短，一個剛好卡在 GC 暫停或網路抖動裡的健康 client 會被誤判死亡、被迫重連，製造出一波本來不必要的重連風暴；設太長，死連線會在 server 上滯留更久，佔著資源、也讓「使用者其實已經離線」這件事更晚才被偵測到。預設的 25/20 是一個在這兩種失敗之間取的折衷，不是金科玉律——一個訊號普遍不穩的行動端場景，可能就需要把 timeout 放寬，容忍更多抖動、換取更少誤殺。

## rooms：一個只活在記憶體裡的分組

聊天室的核心動作是「廣播給一群人」——房間 A 的訊息只發給房間 A 的人。Socket.io 的 **room** 就是為這個而生的抽象：`socket.join("room-A")` 把一條連線加進一個分組，`io.to("room-A").emit("msg", data)` 就只把訊息送給這個分組裡的所有連線。一行搞定，乾淨利落。

但要真正搞懂 room、尤其要搞懂它在多機器下為什麼會出問題，你得先知道一件樸素到容易被忽略的事：**room 在預設情況下，只是一張存在單台 server 記憶體裡的對照表**——「哪些 socket id 屬於哪個 room」。它沒有持久化、沒有跨機器、就是一個 in-memory 的 `Map`。這個事實是後面一切擴展難題的根源。

room 還有一個常被忽略的細節：每條連線一建立，就自動加入一個**以它自己的 socket id 命名的私有 room**。這不是冷知識——它正是 `io.to(someSocketId).emit(...)`「對單一使用者私訊」能運作的底層原理：私訊其實就是廣播給一個只有一個成員的 room。理解了「room 只是 in-memory 的成員表」「每個人自己也是一個 room」，你就握住了 Socket.io 廣播模型的全部本質。

與 room 平行的還有 **namespace**（`/chat`、`/admin`）——那是邏輯通道的隔離，每個 namespace 各有自己一套 room 與事件，共用底層那條實體連線。room 是「同一個 namespace 內把人分組」，namespace 是「把不同用途的通訊分開」，兩個維度正交。

現在，把「room 只活在單台記憶體裡」這件事，和第三通客訴接起來。

## 第二台 server 一加，一半的人就消失了

那通最詭異的客訴——加開第二台 server 後,房間裡一半的人收不到另一半發的訊息——現在有了精確的解釋。

設想兩台 Socket.io server，前面一個負載均衡器。房間 `lobby` 有 4 個人：Alice、Bob 連在 server 1，Carol、Dave 連在 server 2。Alice 發一則訊息，她連的 server 1 執行 `io.to("lobby").emit(msg)`。問題來了：server 1 的記憶體裡，`lobby` 這張對照表只記得 **Alice 和 Bob**——它根本不知道 Carol、Dave 的存在，因為那兩個人的連線狀態在 server 2 的記憶體裡，是另一台機器的另一張表。於是這則訊息只送到了 Bob。Carol 和 Dave 不是「沒收到」，是 server 1 從來不知道該送給他們。

```
        load balancer
        /            \
   server 1          server 2
   lobby: {A, B}     lobby: {C, D}     <- two separate in-memory maps
       |                  |
   A emits  ----> io.to("lobby").emit reaches only B
   C, D on server 2 are invisible to server 1
```

這不是 bug，是「狀態在記憶體、記憶體不跨機器」的必然後果。長連線把 HTTP 那種「請求無狀態、可打到任何一台」的舒適前提，換成了「連線有狀態、綁死在一台」（這個從無狀態到有狀態的根本轉換，是所有長連線水平擴展的共同難題，見〈WebSocket：frame、ping-pong 與水平擴展〉）。要讓 server 1 的廣播也能抵達 server 2 上的人，你需要一條讓兩台機器互通有無的管道——一個 **backplane（背板）**。這就是 adapter 登場的地方。

## redis-adapter：用 Pub/Sub 當背板

Socket.io 把「room 成員存哪、廣播怎麼跨機器扇出」這件事抽象成一個可抽換的元件——**adapter**。預設的 adapter 把一切存在記憶體（就是上面壞掉的那個）。多機器部署時，你換上 `@socket.io/redis-adapter`（v8.x，2026-06 當時最新約 8.3.0），它用 **Redis Pub/Sub** 把多台 server 串成一個整體。

機制簡單得漂亮：每台 server 都訂閱 Redis 上的一組頻道。當 server 1 執行 `io.to("lobby").emit(msg)`，redis-adapter 做兩件事——把訊息推給**自己這台**屬於 lobby 的本地連線（Alice、Bob），同時把這個廣播 **publish 一筆到 Redis**。server 2 訂閱著同一個頻道，收到這筆 publish，於是它也對**自己這台**屬於 lobby 的本地連線（Carol、Dave）做一次本地推送。四個人都收到了。

這裡有一個常被誤解、但對容量規劃至關重要的點：**backplane 上的流量和房間人數無關，只和節點數有關。** 把數字算出來就清楚了。三台 Socket.io server，一個 500 人的房間，某人發一則訊息。發訊那台的 redis-adapter：對自己這台的本地成員直接推送，**另外 publish 1 筆到 Redis**；其餘兩台各收到這 1 筆，各自對自己這台的本地成員推送。Redis 上的成本是 **1 次 publish → 2 次跨節點 deliver**——和房間裡是 500 人還是 5 個人**毫無關係**。那 500 次真正的訊息推送，是發生在三台機器各自的本地、推給它們各自手上的連線（平均每台約 167 條）。

換句話說，**backplane 只負責「跨節點那一跳」，扇出到末端連線的重活在各節點本地完成**。Redis 看到的永遠是「每則廣播 × 節點數」，而不是「每則廣播 × 房間人數」。這個區分決定了你該擔心什麼：當房間很大、節點很少時，瓶頸在各節點本地的推送；當節點很多、廣播很頻繁時，瓶頸才轉移到 Redis 的 publish 扇出——因為每一則廣播，即使某台節點上**一個**該房間的成員都沒有，它還是會收到那筆 publish、白白處理一次。這就是「無差別 fan-out」：節點規模一大，背板自己會變成瓶頸。

針對這個，新部署可以改用 Redis 7.0 引入的 **sharded Pub/Sub**（透過 redis-adapter 的 `createShardedAdapter()`，此能力在 adapter v8.2.0 加入，需 Redis 7.0+）：廣播只送到負責該 channel 的 shard，而不是廣播到整個 Redis 叢集的每個節點，把大規模下的扇出壓力切散。但這是規模到了才需要的最佳化——小叢集上單一 Redis Pub/Sub 綽綽有餘，過早上 sharded 是徒增複雜。

## 那條看似乾淨的背板，其實會漏

redis-adapter 解決了「跨機器收不到」，但它解決的方式繼承了一個你必須清醒看待的弱點：**Redis Pub/Sub 是 fire-and-forget、at-most-once，它不持久化任何東西。**（Redis Pub/Sub 與 Streams 的交付語意差異，是 owning 在別處的主題，見〈Redis Pub/Sub 與 Streams：交付語意的取捨〉。）

具體會怎麼壞？想像某台 server 和 Redis 之間的連線抖了一下——只是兩秒鐘的網路打嗝。在這兩秒內，別的 server 經由這個背板廣播出去的所有訊息，這台暫時失聯的 server **永遠收不到**，因為 Pub/Sub 對「發佈當下沒在線訂閱」的訊息不做任何保留、沒有 replay。那兩秒內，連在這台 server 上的所有使用者，會無聲無息地漏掉那段時間房間裡發生的一切。沒有報錯、沒有缺口提示，就是少了幾則訊息。對聊天這種場景，這也許可以忍；對「協作編輯」或「即時下單」這種少一則就出事的場景，這個無聲的洞是不可接受的。

這正是 **`@socket.io/redis-streams-adapter`** 存在的理由。它把背板從 Pub/Sub 換成 **Redis Streams**——一個持久化的 append-only log。訊息被 `XADD` 進 stream、帶著遞增的 offset；某台 server 和 Redis 短暫斷開後重連，它能從自己**上次讀到的 offset** 之後繼續讀，把斷線那段漏掉的廣播補回來，不丟封包。代價當然有：Streams 要持久化、要記 offset、比 Pub/Sub 重——你用吞吐和儲存，換背板那一跳的可靠性。選哪個，就是「這條跨機器的廣播路徑，漏一則訊息能不能忍」這個問題的答案。

## acknowledgement 不是送達保證

Socket.io 還給了你一個誘人的東西：`emit` 可以帶一個 callback，對端處理完會回呼它。看起來就像「請求-回應」，於是很容易產生一個危險的錯覺：**收到 ack ＝訊息可靠送達了**。

不是。ack 只告訴你一件很窄的事：**對端的那個 callback 跑過了**。它沒告訴你的事多得多。如果連線在訊息送達之前就斷了，你根本不會收到 ack——但你也無從知道訊息到底是「沒送到」還是「送到了、對端處理了、只是 ack 在回程斷線裡丟了」。後者尤其要命：對端可能已經把這則訊息當成新訂單處理了，而你因為沒收到 ack，重送了一次。沒有 ack，不代表沒處理；有 ack，也只代表 callback 執行過，不代表那個處理是持久的、不會在對端隨後的崩潰裡蒸發。

換句話說，ack 給你的是「盡力而為的回執」，不是端到端的交付保證。要真正的 at-least-once，你得在 Socket.io 之上自己疊一層——給每則訊息一個序號、對端持久化後才算數、重連後比對序號補齊缺口、用冪等鍵擋掉重送造成的重複處理（交付語意與冪等是 owning 在別處的整套主題，見〈三種交付語意：at-most、at-least、exactly-once〉與〈重複是常態：冪等與去重〉）。Socket.io 故意不替你做這件事，因為「可靠到什麼程度」是業務決定，不是函式庫能替你拍板的。它給你傳輸，交付語意要你自己掙。

## 斷線那十秒：connection state recovery 與它沒辦法救你的時候

第二通客訴——電梯裡掉訊號、重連後漏掉那十秒——是另一個獨立的問題。redis-adapter 解決的是「同一時刻跨機器收不到」，但它救不了「我這條連線斷了一段時間、斷線期間的訊息怎麼補回來」。這需要一個不同的機制：**connection state recovery（連線狀態復原）**。

它的運作和 Streams 背板異曲同工，但作用在「單一 client 的重連」這個維度。開啟後，server 發給 client 的每個封包都帶一個遞增的 **offset**；client 在本地記住自己**最後處理到的 offset**。連線斷掉、又在容許的時間窗（`maxDisconnectionDuration`）內重連時，client 把自己的私有 session id 和「我最後讀到 offset X」一起送回去，server 試著把這條連線的狀態（它在哪些 room、漏了哪些事件）整個還原、並把 offset X 之後的事件重播給它。電梯那十秒的訊息，就這樣補回來了——前提是復原成功。

而「前提是復原成功」這句話，是這個機制最重要的部分，必須講透：**connection state recovery 明確地不保證一定成功。** 官方文件直白地說它「will not always be successful」。斷線超過 `maxDisconnectionDuration`、server 在這期間重啟丟了狀態、或其他種種情況，復原都會失敗，client 會被當成一條全新連線接進來——它漏掉的那段就真的漏了。所以這個機制給你的是「常見的短暫斷線能無痛補回」，不是「斷線不丟訊息」的鐵保證；**你的應用層仍然必須處理「復原失敗」的分支**——通常是重連後主動拉一次最新快照，把可能漏掉的洞填平。把它當成「啟用就不丟訊息」是會出事的誤解。

這裡藏著一個極其容易踩、而且和前面的選擇直接打架的 edge case，務必記死：**connection state recovery 與預設的 redis Pub/Sub adapter 不相容。** 原因正是前面說的——Pub/Sub 不持久化，沒有可供重播的歷史，自然無從復原。能搭配 connection state recovery 的，是本機內建 adapter、**Redis Streams adapter**、或 MongoDB adapter 這些**有持久化 log** 的背板。也就是說，當你既要多機器擴展、又要可靠的斷線復原時，那個「省事」的 redis Pub/Sub adapter 同時擋了你兩條路（背板會漏、且不支援 state recovery），你被推著走向 Streams adapter。這不是巧合——它是「持久化」這個共同前提在兩個不同維度上的同一個身影。

## sticky session：那個就算上了 Redis 也躲不掉的約束

到這裡有個很自然、也很危險的誤會：「我已經上了 redis-adapter，跨機器廣播解決了，那負載均衡器就可以隨便把請求丟到任何一台了吧？」

不行。這裡要把兩個被解決的問題分清楚。redis-adapter 解決的是**廣播扇出**——讓一則訊息能抵達散在各台 server 上的目標連線。它**沒有**解決**連線歸屬**——一條連線本身（尤其是它的狀態）還是綁在某一台 server 上。而 Socket.io 的 fallback 機制，讓「連線歸屬」變成一個比裸 WebSocket 更硬的約束。

回想連線是怎麼建立的：Socket.io 預設**先用 HTTP long-polling 起手**。而 long-polling 不是一條連線，是**一連串獨立的 HTTP 請求**——一個 GET 收、一個 POST 送、再一個 GET、再一個 POST……這些請求各自獨立地經過負載均衡器。問題來了：建立連線的握手過程橫跨好幾個這樣的請求，而握手產生的 session 狀態存在**接到第一個請求那台 server 的記憶體**裡。如果負載均衡器把同一個 client 的後續握手請求輪流丟到不同的 server，第二台 server 收到一個它從沒見過 session id 的請求，只能回一個錯誤——握手永遠完不成，連線根本建不起來。

所以負載均衡器**必須**開 **sticky session（session affinity）**：用 cookie 或 source IP，把同一個 client 的所有請求釘在同一台 server 上。這不是效能最佳化，是**正確性的硬前提**——尤其在 long-polling 那段。一個極其常見、又極難一眼看穿的生產事故就是：開發者上了 redis-adapter、以為擴展問題全解了，卻忘了開 sticky session，結果一部分使用者（那些剛好沒升級成 WebSocket、停在 long-polling 的）會間歇性地連不上或連上又掉，症狀飄忽、難以重現。redis-adapter 和 sticky session 解的是兩個正交的問題，**兩個都要，缺一不可**。

## 為什麼是這個形狀

退一步看 Socket.io 的整個樣貌，它其實是同一句話的反覆迴響：**長連線把無狀態的舒適，換成了有狀態的麻煩；而狀態，是擋在水平擴展前面的那座山。**

fallback 是因為「連得上」不能假設，所以退一步用最笨但最通的 long-polling 起手——而這一步又反過來逼出了 sticky session 的硬約束。room 是個方便的廣播抽象，但它只是一張 in-memory 的成員表，於是一跨機器就需要 adapter 這條背板把各台的記憶體縫起來。背板用 Pub/Sub 換來簡單，卻欠下「會漏」的債，於是有了 Streams adapter 用持久化把債還上。ack 看起來像送達保證，其實只是回執，真正的可靠交付得你自己在上面疊。斷線復原能補回常見的短暫掉線，但它不是鐵保證、而且和不持久化的背板天生不容。

每一個方便的背後，都是同一個「狀態該存在哪、怎麼跨機器、漏了怎麼辦」的問題換了張臉再出現一次。Socket.io 的價值，不在於它消滅了這些難題——它消滅不了，那是長連線的物理——而在於它把這些難題收進一組有預設答案、又能逐層掀開的旋鈕：先用最保守的 fallback 確保連得上，再讓你按自己的可靠性需求，一層一層決定要不要把 Pub/Sub 換成 Streams、要不要開 state recovery、要不要自己疊交付語意。看懂了這層皮底下每個旋鈕在調什麼，你才不會在第四通客訴打來時，又從第一格開始重新驚訝。

## 延伸閱讀

- Socket.IO — How it works（分層、transport、handshake 全景）: https://socket.io/docs/v4/how-it-works/
- Socket.IO — The Engine.IO protocol（heartbeat、transport upgrade 的封包級規格）: https://socket.io/docs/v4/engine-io-protocol/
- Socket.IO — Redis adapter（Pub/Sub 背板與 sharded adapter）: https://socket.io/docs/v4/redis-adapter/
- Socket.IO — Redis Streams adapter（持久化背板、斷線重續）: https://socket.io/docs/v4/redis-streams-adapter/
- Socket.IO — Connection state recovery（offset 重播與其限制）: https://socket.io/docs/v4/connection-state-recovery
- @socket.io/redis-adapter（npm，版本與相依）: https://www.npmjs.com/package/@socket.io/redis-adapter
- RFC 6455 — The WebSocket Protocol（底層 transport 之一的協定本身）: https://www.rfc-editor.org/rfc/rfc6455
