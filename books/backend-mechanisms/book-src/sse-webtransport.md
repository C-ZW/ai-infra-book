# SSE、long-poll 與 WebTransport

一個很常見的需求：使用者按下「開始」之後，server 端有一個跑得有點久的工作——轉檔、跑報表、讓大型語言模型逐字吐字——你想把進度即時推到瀏覽器，讓畫面上的數字一格一格往上跳，或者讓文字一個 token 一個 token 浮現。方向很清楚：**事件在 server 端發生，client 不知道、也不知道該什麼時候問。**

第一反應往往是 WebSocket。它是全雙工長連線，兩端隨時能送 frame，拿來推進度當然行（它怎麼運作、怎麼水平擴展，見〈WebSocket：frame、ping-pong 與水平擴展〉）。但停一下：上面這個場景，client 對 server 其實沒什麼要即時說的——它按一次「開始」，剩下全是 server 單方向往下灌。為了一個**只需要單向推**的需求，去搭一條雙向協定，要處理升級握手、要自己做斷線重連、要在連線上層自己定義訊息邊界與恢復語意——這些功夫有一大半是白做的。

所以真正的問題不是「怎麼推」，而是「**在這個方向是單向、那個場景能容忍丟包、另一個環境連 WebSocket 都升級不上去的前提下，各該選哪條傳輸**」。HTTP 原本只會「client 問、server 答」，要把事件方向倒過來、讓 server 在沒有新請求時也能把資料寫給 client，業界長出三條 WebSocket 以外的路：long polling 把一個請求**掛住**來假裝一次推送，SSE 在一條 HTTP 連線上**持續寫**單向事件流，WebTransport 則乾脆換到 HTTP/3 底下、拿 QUIC 的多串流能力重新做傳輸。三者的機制、保證、成熟度差很遠，值得一條一條看透。

## long polling：把一個請求掛在半空

從最不像推、最像「拉」的那端開始。**短輪詢（short polling）** 是最笨但最好懂的做法：client 每隔固定間隔——比如每 3 秒——發一個普通 HTTP 請求問「有新東西嗎」，沒有就空手而回，有就拿走。它完全沒有長連線，無狀態，水平擴展毫無負擔；代價是延遲與浪費被綁死在同一個旋鈕上：間隔調短延遲就低、但空請求暴增，間隔調長省了請求、延遲就難看。一個更新很罕見的場景，每次輪詢有九成九問到的是「沒有」，這些請求純粹是燒掉的 CPU 與頻寬。

**long polling** 是對這個浪費的直接修補，而且它的聰明之處全在一個動作上：**server 收到請求後，不馬上回。** client 發出「有新東西嗎」，server 看了看，現在真的沒有——但它不回 `204 No Content`，而是**把這個請求 hold 住**，讓這條 HTTP 連線就那樣開著、掛在半空，直到兩件事其中一件發生：要嘛真的有新事件冒出來，server 立刻把它寫進這個一直沒回的回應裡、結束請求；要嘛掛到一個逾時上限（比如 30 秒）都沒事件，server 回一個空回應。client 不論收到的是事件還是空回應，**馬上再發下一個請求**，重新掛上去。

在腦中重放一遍就會發現它的精髓：一個 long-poll 請求的「掛起」期間，就等於一次推送的「等待視窗」。事件一到，掛著的那個請求立刻被喚醒回應——延遲幾乎等於事件真正發生的時刻，而不是下一次輪詢的時刻。它用標準 HTTP 的請求-回應形狀，騙出了一個近似推送的行為。

```
short polling（每 3s 問一次，事件在 t=0.5s 到）：
  req --[空]   req --[空]   req --[拿到!]
  0s           3s           6s     ← 事件 0.5s 就到了，卻等到第 6s 才被取走

long polling（請求掛住，事件一到立刻回）：
  req ----------(掛著)---------->|事件到| 回應 --> 立刻 req 再掛上
  0s                            0.5s            ← 延遲 ≈ 事件發生時刻
```

但 long polling 有兩個非顯然的代價，正是它名聲不好的地方。

第一，**它沒有真的省掉請求，只是把每個請求的壽命拉長。** 「long」是指請求被掛得久，不是指請求變少。事件低頻時這很划算——一個掛 30 秒的請求覆蓋了 30 秒的等待。但事件**高頻**時它會原形畢露：每收到一個事件就得回應、結束這個請求，client 立刻再發一個新的——於是它退化成一連串首尾相接的短請求，每個事件都付一次完整的 HTTP 請求建立成本（TCP/TLS 若沒有 keep-alive 還要重來，加上每次完整的 header 來回）。在每秒好幾則訊息的場景，long polling 的開銷比一條常駐長連線差得多。它是「事件稀疏」的最佳解，不是「事件密集」的最佳解。

第二，**server 端要同時 hold 住大量掛起的連線。** 每一個掛著的 long-poll 都佔著一個連線、一份請求上下文、一點記憶體，就那樣等著。一萬個 client 同時在 long-poll，server 就有一萬條看似閒置、其實全在等事件的連線——這對採用「一執行緒一連線」模型的傳統 server 是災難（一萬個執行緒大半在阻塞等待），對 event loop 那種非阻塞模型則只是一萬個 pending 的回應物件，吃得起但仍是實打實的記憶體。掛起連線本身是有成本的庫存。

那為什麼還留著它？因為 long polling 有一個別人都沒有的本事：**它就是普通的 HTTP 請求，沒有任何協定升級，能穿過幾乎所有中間設備。** 老舊的企業 proxy、不認得 `Upgrade` 標頭的防火牆、會把 WebSocket 握手擋下來的閘道——這些環境裡 WebSocket 連都連不上，而 long polling 跟一個慢慢回應的普通 GET 沒有任何區別，暢通無阻。所以即便在 WebSocket 普及的今天，long polling 依然作為**相容性的最後退路**活著：當更好的傳輸升級失敗，總還有它能用（一些即時函式庫正是把它當作 fallback 的底層，見〈Socket.io：fallback、rooms 與 redis-adapter〉）。

## SSE：在一條連線上一直寫下去

long polling 的尷尬在於它每次只能掛一個請求、回一筆就得重來。如果方向確定是單向的 server→client，能不能不要回一筆就斷，而是**讓 server 在同一條連線上一直寫、一筆接一筆地寫**？這就是 **Server-Sent Events（SSE）**——它由 WHATWG HTML 標準定義，瀏覽器原生支援，本質上是「一個永不結束的 HTTP 回應」。

機制簡單到可以一眼看穿。client 用原生的 `EventSource` 物件發一個普通 GET；server 不像平常那樣回完 body 就關閉，而是回一個特別的標頭、然後**讓回應體保持開著**，源源不絕地往裡寫：

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

data: {"progress": 10}\n
\n
data: {"progress": 25}\n
\n
id: 42\n
event: progress\n
data: {"progress": 50}\n
\n
```

關鍵就在 `Content-Type: text/event-stream`。它告訴瀏覽器「這不是一份會結束的文件，是一條事件流，請邊收邊解析」。格式是純文字、極簡的逐行協定，照 WHATWG 規格逐欄處理：

- **`data:`** 後面是事件內容。同一筆事件可以有多行 `data:`，解析時各行用換行接起來。
- **`event:`** 指定事件型別（不寫就是預設的 `message`），讓 client 端能分流監聽不同名字的事件。
- **`id:`** 給這筆事件一個 ID——這是恢復機制的鑰匙，待會講。
- **`retry:`** 一個整數毫秒，讓 server 告訴 client「下次斷線後等這麼久再重連」。
- **一個空行（`\n\n`）代表一筆事件結束、立刻派發。** 這是分隔符：寫滿一筆、補一個空行，瀏覽器就把累積的欄位組成一個事件丟給你的 `onmessage`。
- **以冒號開頭的行（`: ...`）是註解，整行被忽略。** 這個看似無用的設計其實是保命用的——稍後談心跳時會用到。
- 整條流**必須是 UTF-8**，沒有商量。

SSE 真正比 WebSocket 省事、也比 long polling 高明的地方，是它把兩件麻煩事**做進了瀏覽器原生實作**，你一行程式都不用寫。

**第一件是自動重連。** 連線斷了——網路抖一下、中間設備把它砍了——`EventSource` 會**自己重新發起連線**，預設等大約 3000 毫秒（規格說是「實作自訂、大約幾秒」，主流瀏覽器取 3000 ms）。server 想在尖峰時讓客戶端退避，只要在流裡寫一行 `retry: 10000`，所有 client 下次就改等 10 秒重連——不用改任何 client 程式碼。WebSocket 完全沒有這個，斷線後要不要重連、退避多久，全是你自己要寫的。

**第二件、也是更精緻的一件，是斷點續傳。** 每筆事件如果帶了 `id:`，瀏覽器會記住最後收到的那個 ID。重連時，它**自動把這個值放進 `Last-Event-ID` 請求標頭**送回去。於是 server 一看標頭就知道「這個 client 上次收到第 42 號，從第 43 號開始補給它」，斷線那幾秒漏掉的事件就能補回來。

但這裡藏著一個**最容易讓人誤判的邊界**，必須講透：`Last-Event-ID` 只是瀏覽器**把上次的 ID 還給你**——**真正的續傳邏輯，server 完全要自己實作。** 瀏覽器負責的部分到「重連時附上這個標頭」為止；server 收到之後要能依這個 ID 找出「之後發生過哪些事件」並重放，這需要 server 端**真的保存了一段事件歷史**（一個帶序號的緩衝區、或一張表）。如果 server 沒做這段——很多人沒做——那麼 `Last-Event-ID` 標頭照樣送來，但 server 看不懂、或乾脆無視，重連後只會從「此刻」開始推，**斷線期間的事件就是漏了**。SSE 給了你續傳的「協定鉤子」，沒給你續傳的「實作」。把「SSE 自動 resume」當成資料不會漏的保證，是會在重連那一刻悄悄掉資料的。

還有一個藏在 HTTP 版本裡的陷阱，是 SSE 部署時最常踩的。瀏覽器對**同一個網域**有並行連線數上限——在 **HTTP/1.1 下通常是 6**。SSE 連線是一條**長期佔著不放**的連線，於是它直接吃掉這 6 個配額裡的一個。手算一下後果就觸目驚心：使用者開了 6 個分頁、每個分頁各開一條 SSE 連到同一個網域，這 6 條就把整個網域的連線配額**用光了**。第 7 個分頁——甚至同網域的任何一張圖片、一個 API 呼叫——全部卡在那裡排隊，因為一個空閒的連線都不剩。畫面看起來就是「莫名其妙整站卡死」，而原因藏在另外幾個分頁的 SSE 上，極難一眼看出。

```
HTTP/1.1（每網域上限約 6 條連線）：
  tab1 SSE ─┐
  tab2 SSE ─┤
  tab3 SSE ─┼─ 6 條全被 SSE 佔滿
  tab4 SSE ─┤
  tab5 SSE ─┤
  tab6 SSE ─┘
  tab7 任何請求 ──> 卡住排隊（沒有可用連線）

HTTP/2（單一連線多工，常見上限約 100 streams）：
  all tabs ── 1 條 TCP/TLS 連線 ── 多條獨立 stream（6 條 SSE 只用掉 6 個）
```

解法是把 SSE 跑在 **HTTP/2** 之上。HTTP/2 把多個請求變成單一連線上的多條 stream（並行上限由雙方協商，協定本身不設硬上限，RFC 建議不低於 100、實務上多數 server 也取 100 為預設），6 條 SSE 只是 6 條 stream，離上限遠得很，問題消失。這就是「**SSE 強烈建議部署在 HTTP/2 之上**」這句忠告的具體來由——不是性能偏好，是不這麼做就會在多分頁下卡死整個網域。

最後是那個冒號註解的用途。中間的 proxy 或負載均衡器常會對「看起來閒置」的連線設逾時——好一陣子沒有任何位元組流動，就當它死了、悄悄砍掉。SSE 在事件稀疏時正好長時間沒東西可寫，剛好撞上這個逾時。解法是讓 server 每隔一段時間（比逾時短）就寫一行 `: keep-alive\n\n` 之類的註解——它在 client 端被忽略、不觸發任何事件，但在連線上製造了位元組流動，讓中間設備知道這條連線還活著、別砍。這是應用層心跳，跟 WebSocket 用 ping/pong control frame 達成同樣目的，只是手段不同。沒有它，一條安靜的 SSE 會在某個 60 秒逾時的 proxy 後面被無聲斷掉，而你的程式以為自己還連著。

SSE 的甜蜜點因此非常清楚：**方向確定是單向 server→client，要省事、要原生重連、要有續傳的鉤子。** 通知串流、任務進度、log 即時尾隨、儀表板數字、大型語言模型逐字輸出（token streaming，這正是近年 SSE 大量回潮的原因）——這些 client 對 server 沒有即時話要說的場景，SSE 都比 WebSocket 划算。client→server 那一向，照樣用普通的 HTTP 請求送就好，不需要即時。硬要在這種場景上 WebSocket，等於多做了一整套用不到的雙向協定。

## WebTransport：換到 HTTP/3 底下重新做

SSE 和 WebSocket 有一個共同的、藏在更底層的弱點，平時看不出來，丟包時才現形：它們都跑在 **TCP** 上，而 TCP 有一個叫 **head-of-line blocking（隊頭阻塞）** 的老毛病。

理解這個毛病，要先看 HTTP/2 是怎麼「多工」的。HTTP/2 在**單一一條 TCP 連線**上跑很多條邏輯 stream，看起來各自獨立。但 TCP 底下只認得**一條連續、有序的位元組流**——它根本不知道上面被切成了 100 條 stream。TCP 的鐵律是「按序交付」：第 N 個封包沒到，第 N+1、N+2…就算已經安然躺在接收緩衝區裡，也**不准交給應用層**，得等第 N 個重傳補上。於是這一幕發生了：100 條 stream 多工在一條 TCP 上，其中**某一條** stream 的一個封包掉了，TCP 為了維持有序，把後面屬於**另外 99 條毫不相干的 stream** 的資料也全部扣住，集體等那個掉的封包重傳。99 條沒事的 stream，被第 100 條的一次丟包連坐卡住。這就是 TCP 層的 head-of-line blocking——HTTP/2 把多工做到了應用層，但底下那條 TCP 的「整條按序」假設，讓多工的獨立性在丟包時破功。

**QUIC**（HTTP/3 底下的傳輸協定）就是為了拔掉這根刺而生的。它跑在 UDP 上，自帶多工與加密，而且**把「有序交付」的單位從整條連線下放到每一條 stream**：每條 stream 各自維護自己的序號與重傳，互不相干。於是同樣一個封包掉了，**只有它所屬的那一條 stream 會停下來等重傳，其他 stream 照常往應用層交付**。隊頭阻塞被限制在單條 stream 之內，不再連坐全部。

```
HTTP/2 over TCP：一條 stream 丟包，全部連坐
  stream A: ▓▓▓ x ▓▓   ← A 的某封包掉了
  stream B: ▓▓▓▓▓▓     ← B 早就到齊，卻被 TCP「按序」扣住
  stream C: ▓▓▓▓▓▓     ← C 同樣被扣住，等 A 重傳
                          全部卡住

HTTP/3 over QUIC：丟包只困住自己那條
  stream A: ▓▓▓ x ▓▓   ← A 等自己的重傳
  stream B: ▓▓▓▓▓▓ ──> 照常交付
  stream C: ▓▓▓▓▓▓ ──> 照常交付
```

**WebTransport** 就是建在 HTTP/3（QUIC）之上、開放給 Web 用的新傳輸 API，它把 QUIC 的能力直接攤給你：一條 WebTransport session 之內，你可以開很多條**獨立、可靠、有序的 stream**（彼此不會隊頭阻塞），也可以送 **datagram**——不可靠、不保證順序、不重傳、但**延遲最低**的單發訊息。同一條 session 裡，可靠與不可靠可以**混用**：把不能丟的控制訊息走 stream，把「過期就作廢、丟了也不必補」的即時狀態走 datagram。

這個「可靠/不可靠混用」是 WebTransport 真正獨到、WebSocket 給不了的東西，用一個場景就懂為什麼有用。即時遊戲裡，玩家的座標每秒更新幾十次。如果走 TCP（WebSocket），某個座標封包掉了，TCP 會固執地重傳它——可是等它補到時，早就有好幾個更新的座標到了，**那個遲到的舊座標已經沒有任何意義，重傳它純粹是浪費、還順便把後面的更新隊頭阻塞住**。對這種「只要最新、過期即廢」的資料，datagram 才是對的：丟了就丟了，下一個更新馬上覆蓋它，絕不為了一個過時的值卡住整條流。同一個遊戲裡，「玩家加入房間」「結算分數」這種不能丟的事件，則走可靠 stream。一條 session 同時供應這兩種語意——這是 WebTransport 的招牌。

代價是**成熟度**，這是 2026-06 選用它前必須誠實面對的一點。把版本狀態釘清楚：

- **標準還沒定案。** IETF 的「WebTransport over HTTP/3」目前是 **draft-15（2026-03-02 發布，Standards Track，2026-09-03 到期）**，**仍是 Internet-Draft、尚未成為 RFC**；W3C 那側的瀏覽器 API 文件也仍在 Working Draft。意思是：協定細節**還可能有破壞性變動**。
- **瀏覽器面剛剛湊齊。** Chrome（M97 起，2022）、Firefox（v114 起，2023）、Edge 早就支援；**Safari 直到 26.4（2026-03）才支援**——這一步才讓四大瀏覽器齊備、WebTransport 跨過所謂 Baseline。也就是「現在能用了，但這個『齊備』非常新」。

把這兩點合起來，務實的結論是：WebTransport **能用，但別把它當「現在就能無腦取代 WebSocket」**。生產上要把它當一個還在硬化的選項——而且因為它綁死 HTTP/3/QUIC，得想清楚**降級路徑**：使用者的網路或中間設備不支援 UDP/QUIC（有些企業網路就是把 UDP 擋了）時，連都連不上，這時你退回什麼？沒有這條退路，WebTransport 在不友善的網路下就是直接失聯。

## 三條路怎麼選

把三者擺在一起，選擇其實落在幾個很乾脆的判準上，而每個判準背後都是前面講過的機制在說話。

| 傳輸 | 方向 | 底層 | 保證 | 成熟度 | 何時選它 |
|---|---|---|---|---|---|
| long polling | server→client（模擬） | 純 HTTP | 過幾乎所有中間設備 | 老技術、穩定 | 環境連 WebSocket 都升級不上去的退路；事件低頻 |
| SSE | server→client（單向） | HTTP（建議 HTTP/2） | 原生自動重連＋`Last-Event-ID` 續傳鉤子 | 老技術、穩定 | 只需單向推、要省事；通知/進度/token streaming |
| WebTransport | 雙向 | HTTP/3（QUIC/UDP） | 多條獨立 stream＋datagram、無 TCP 隊頭阻塞、可靠/不可靠混用 | 標準未定（draft-15）、瀏覽器 2026-03 才齊備 | 要 datagram 或多串流不互卡、能上 HTTP/3、能容忍丟包換低延遲 |

先問**方向**。只需要 server 單向推，SSE 幾乎總是對的——純 HTTP、原生重連與續傳鉤子、不必處理升級握手與雙向協定，這些都是白送的。需要 client 也即時往 server 說話（雙向高頻），SSE 不夠，那是 WebSocket 的場（見〈WebSocket：frame、ping-pong 與水平擴展〉）或——若你需要 datagram 與多串流——WebTransport 的場。

再問**丟包與延遲的取捨**。絕大多數應用要的是「不能丟」，TCP 上的 SSE/WebSocket 就對。只有當資料是「過期即廢、重傳有害」的那種——即時遊戲狀態、即時媒體訊號——datagram 的「丟了就算」才反而是優點，這時 WebTransport 的混用能力勝出，但你得付得起它的不成熟與 HTTP/3 依賴。

最後問**環境**。中間設備會不會擋升級？被擋的環境裡，long polling 是唯一能無聲穿過的退路，雖然它延遲與成本都最差。能上 HTTP/3 嗎？不能的話 WebTransport 從一開始就不在選項裡。

退一步看，這三條路加上 WebSocket，全都在同一條軸上選點：**一端是「最像拉、相容性最好、但延遲與成本最差」的 long polling，另一端是「最像推、能力最強、但最不成熟」的 WebTransport。** HTTP 當初被設計成請求-回應，根本沒打算讓 server 主動說話；於是每一種「讓 server 能推」的方案，本質上都是在拿某種代價去**對抗** HTTP 這個原始形狀——long polling 拿請求壽命換、SSE 拿一條長開的回應換、WebTransport 乾脆換掉底層的 TCP。它們的差別，從頭到尾就是**為了把事件方向倒過來，你願意付哪一種代價**。

## 延伸閱讀

- WHATWG HTML Standard — Server-sent events（SSE 規格：事件流格式、`Last-Event-ID`、重連時間）：https://html.spec.whatwg.org/multipage/server-sent-events.html
- MDN — Using server-sent events（SSE 實作指南）：https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
- MDN — WebTransport API：https://developer.mozilla.org/en-US/docs/Web/API/WebTransport_API
- IETF — WebTransport over HTTP/3（draft-ietf-webtrans-http3，2026-06 仍為 Internet-Draft）：https://datatracker.ietf.org/doc/draft-ietf-webtrans-http3/
- W3C — WebTransport（Working Draft）：https://www.w3.org/TR/webtransport/
- RFC 9000 — QUIC: A UDP-Based Multiplexed and Secure Transport（QUIC 如何把有序交付下放到每條 stream、消除 TCP 隊頭阻塞）：https://www.rfc-editor.org/rfc/rfc9000.html
- RFC 9114 — HTTP/3：https://www.rfc-editor.org/rfc/rfc9114.html
