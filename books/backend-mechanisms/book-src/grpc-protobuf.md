# gRPC 與 Protobuf：用 IDL 定義服務

設想兩個服務之間最尋常的一次呼叫。訂單服務想問庫存服務「商品 A1 還剩幾件」。如果你用 REST，這件事的「契約」散落在好幾個地方：URL 長什麼樣（`GET /inventory/A1`？還是 `/stock?sku=A1`？），回應的 JSON 有哪些欄位、`quantity` 是數字還是字串、缺貨時回 404 還是回一個 `quantity: 0`、逾時了該怎麼分辨「真的沒貨」和「服務掛了」。這些約定沒有一個地方強制它們對齊——它寫在 Confluence、寫在某人腦裡、寫在客戶端手刻的那個 DTO 類別裡。每個消費這個 API 的團隊，都各自抄一份自己理解的版本。

只要服務數量還少，這套靠紀律維持的契約勉強能撐。但當你有幾十個服務、用三四種語言寫成、彼此每天互相呼叫上千萬次時，「契約靠各自抄」這件事會以一種很安靜的方式腐爛：庫存服務某天把 `quantity` 從整數改成「帶單位的字串」（`"5 boxes"`），它自己測試全綠、上線了；訂單服務那邊用 `parseInt` 讀這個欄位，讀出 `5`、把單位悄悄丟了，於是賣了五箱當五件。沒有人收到任何錯誤——因為這兩端之間**根本沒有一份機器能檢查的契約**。

gRPC 要解的，正是這個問題。它的核心主張很簡單：**把服務介面變成一份單一、強型別、機器可讀的定義檔，讓「契約」從口頭約定變成編譯期擋得住的東西。** 這份定義檔用的語言叫 IDL（Interface Definition Language，介面定義語言），而 gRPC 借用的 IDL 就是 Protocol Buffers（Protobuf）。要看懂 gRPC 為什麼長成今天這個樣子，得先分清楚這兩件東西到底各自負責什麼。

## Protobuf 是名詞，gRPC 是動詞

一個常見的混淆是把 gRPC 和 Protobuf 當成同一件事，或以為「gRPC 就是二進位版的 REST」。兩個都不對，而把它們分開正是理解整套機制的起點。

**Protobuf 本身只是一套序列化格式**——把一個結構化的訊息（一個 `Order`、一個 `User`）編碼成緊湊的二進位位元組，以及一套讓這份結構能隨時間演進而不破壞相容性的規則。它管的是「資料長什麼樣、怎麼變成位元組、新舊版本怎麼還能互讀」。這套編碼與相容性的機制——欄位靠號碼而非名字辨識、為什麼永不能重用 field number、向前向後相容的窄縫——本身是一個值得單獨講透的主題（見〈序列化與 schema 演進〉），本章不重講。Protobuf 也完全可以脫離 gRPC 單獨用：拿來當 Kafka 訊息的格式、拿來存檔、拿來在記憶體裡傳結構，都行。它是一個名詞——一種資料的形狀。

**gRPC 則是一套 RPC 框架**——它借 Protobuf 的 `.proto` 檔當 IDL，但比 Protobuf 多做了一整層事：它讓你在同一份 `.proto` 裡不只描述「訊息」，還描述「**服務**」——有哪些方法、每個方法收什麼、回什麼。然後一個叫 `protoc` 的編譯器（配上 gRPC 外掛）讀這份檔，**自動產生**出客戶端的 stub（呼叫端的代理物件）和伺服器端的 skeleton（待你填實作的骨架）。呼叫遠端方法寫起來就像呼叫一個本地函式：`inventory.GetStock(req)`。它是一個動詞——一個「呼叫遠端」的動作，連同那個動作底下所有的傳輸、編碼、錯誤傳遞。

把這個分工釘死：**Protobuf 定義資料與訊息，gRPC 把這些訊息接上「服務方法」與「在線上怎麼傳」。** 一份典型的 `.proto` 同時長著這兩半：

```protobuf
// 註：示意 .proto，不保證可直接編譯。
syntax = "proto3";

// --- 這一半是 Protobuf：純粹的訊息結構（名詞）---
message GetStockRequest { string sku = 1; }
message StockReply     { string sku = 1; int32 quantity = 2; }

// --- 這一半是 gRPC：服務介面（動詞）---
service Inventory {
  rpc GetStock(GetStockRequest) returns (StockReply);
}
```

那個 `service` 區塊是 gRPC 獨有的——純 Protobuf 不認得它。`protoc` 看到它，就會替你產出 `Inventory` 這個服務的客戶端 stub 與伺服器骨架。從此「訂單服務怎麼問庫存」這件事，**有了一個唯一真相來源**：這份 `.proto`。Go 寫的庫存服務、Node 寫的訂單服務、Python 寫的維運工具，全部由這同一份檔產生各自語言的型別。誰想把 `quantity` 改成字串，得先改這份檔——而改了之後，所有消費端重新產碼時，型別對不上會在**編譯期**就爆，不會等到上線後賣錯貨才發現。開場那個「五箱當五件」的事故，在這個模型裡根本到不了生產環境。

## 一次呼叫在線上到底長什麼樣

「呼叫遠端像呼叫本地函式」這句話很動聽，但對一個資深工程師來說，恰恰是這種「看起來像本地」的抽象最危險——因為它把網路藏起來了，而網路會用各種方式提醒你它的存在。要真正掌握 gRPC，你得能在腦中重放一次呼叫從客戶端到伺服器、再回來的完整旅程。我們把那個 `GetStock` 呼叫放慢看。

gRPC 的標準傳輸層**跑在 HTTP/2 上**（HTTP/3 變體在 2026 仍是實驗性、尚未標準化——gRPC-over-HTTP/3 的協定提案還在進行中，雖然部分語言實作已有 HTTP/3 支援），這不是隨便挑的——HTTP/2 的多工（一條 TCP 連線上開多個獨立編號的 stream、互不阻塞）正是 gRPC 能在單一連線上塞進大量並發呼叫的基礎（HTTP/2 本身的機制見〈HTTP/1.1、HTTP/2、HTTP/3〉）。**每一次 gRPC 呼叫，就是一個 HTTP/2 stream。** 旅程是這樣的：

```
client                                       server
  |  HEADERS frame                                |
  |   :method POST                                |
  |   :path /Inventory/GetStock                   |
  |   content-type application/grpc               |
  |   grpc-timeout 200m   (200 ms deadline)       |
  | --------------------------------------------> |
  |                                               |
  |  DATA: [0][00 00 00 04][protobuf...]          |
  | --------------------------------------------> |   server 解碼、查庫存
  |                                               |
  |              HEADERS  :status 200             |
  | <-------------------------------------------- |
  |              DATA: [0][00 00 00 06][...]      |
  | <-------------------------------------------- |
  |   TRAILERS (closing HEADERS, END_STREAM):     |
  |      grpc-status: 0   (OK)                    |
  |      grpc-message:                            |
  | <-------------------------------------------- |
```

幾個細節值得停下來看，因為它們解釋了 gRPC 後面所有的脾氣。

**第一，方法名是 URL 路徑。** `:path` 是 `/Inventory/GetStock`——服務名加方法名。gRPC 不發明新的傳輸協定，它把「呼叫哪個方法」編碼成一個 HTTP/2 的 `POST` 到一個特定路徑。所以從 HTTP/2 的角度看，每個 gRPC 呼叫都是一個再普通不過的 POST 請求。

**第二，訊息有自己的一層框（framing），疊在 HTTP/2 的框之上。** 那個 DATA frame 裡的 `[0][00 00 00 04][protobuf bytes]` 不是裸的 Protobuf——它是 gRPC 的「length-prefixed message」格式：開頭 **1 個位元組是壓縮旗標**（0 = 未壓縮、1 = 已用 `Message-Encoding` 指定的演算法壓縮），接著 **4 個位元組是大端序（big-endian）的訊息長度**，最後才是那麼多位元組的 Protobuf payload。為什麼 HTTP/2 自己已經會分 frame 了，gRPC 還要再包一層長度前綴？因為一個 HTTP/2 的 DATA frame 和「一則 gRPC 訊息」不是一對一的——一則大訊息可能被 HTTP/2 拆進多個 DATA frame，而 streaming 呼叫會在一個 stream 上連續送好幾則訊息。接收端靠這個長度前綴才知道「這一則到哪裡結束、下一則從哪裡開始」，否則它只看到一串連續的位元組，分不出邊界。這就是為什麼前面那個 `00 00 00 04` 是 4——這則查 `sku = "A1"` 的請求，Protobuf 編碼正好 4 個位元組：欄位 1 是 string，tag 是 `(1 << 3) | 2 = 0x0A`（1 byte）、長度 `0x02`（1 byte）、`"A1"` 兩個字元（2 bytes），1 + 1 + 2 = 4。接收端讀到這個 4，就知道再讀 4 個位元組湊成一則完整訊息（回應那則 `00 00 00 06` 同理：`sku = "A1"` 佔 4、`quantity = 5` 這個 int32 欄位佔 2，合計 6）。

**第三——也是最關鍵、最常被忽略的——呼叫的「成功或失敗」不在那個 `:status 200` 裡，而在最後的 trailers。** 注意伺服器先回了 `:status 200`，這只代表「HTTP 層面這個請求被正常受理了」，跟你的業務呼叫成不成功**毫無關係**。真正的 gRPC 狀態碼放在 stream 結束時的那個 **trailer**（HTTP/2 裡是一個帶 `END_STREAM` 旗標的收尾 HEADERS frame）：`grpc-status: 0` 代表 `OK`，非 0 是各種錯誤（`5` 是 `NOT_FOUND`、`4` 是 `DEADLINE_EXCEEDED`…），錯誤訊息放在 `grpc-message`。

為什麼 status 要放在**最後面**、放在訊息 body 之後？因為對 streaming 呼叫，伺服器是先送完一長串訊息、才知道整個呼叫到底成不成功——它沒辦法在開頭就決定 status，只能在尾巴補上。把狀態放 trailer，是讓「先串流資料、最後再宣告結果」這件事成為可能的設計選擇。這個看似不起眼的決定，等一下會變成 gRPC 為什麼進不了瀏覽器的根本原因。

## 四種呼叫語意：把 stream 變成型別

到目前為止講的都是「一問一答」的呼叫（unary：一次請求、一次回應）。但 gRPC 真正的招牌，是它把 HTTP/2 的雙向 stream 直接提升成**寫在型別簽章裡的四種呼叫語意**——你在 `.proto` 裡用一個 `stream` 關鍵字，就決定了產出來的 stub 是「收一個值」還是「收一條流」。

```protobuf
service Inventory {
  rpc GetStock(GetStockRequest) returns (StockReply);                 // unary
  rpc WatchStock(WatchRequest) returns (stream StockReply);           // server streaming
  rpc BulkUpdate(stream UpdateRequest) returns (BulkReply);           // client streaming
  rpc Sync(stream SyncMsg) returns (stream SyncMsg);                  // bidirectional
}
```

這四種對應到「請求是單一還是一串、回應是單一還是一串」的四個組合：

- **Unary**：一次請求、一次回應。最像傳統 RPC，也是日常呼叫的絕大多數。
- **Server streaming**：客戶端送一次請求，伺服器回**一串**訊息——客戶端持續從這條 stream 讀，直到伺服器宣告結束。適合訂閱式推送：「庫存一變就通知我」。
- **Client streaming**：客戶端送**一串**訊息、伺服器收完才回一次。適合分塊上傳後聚合：「我把這一萬筆庫存調整逐筆送給你，全收到後你回我一個總結」。
- **Bidirectional streaming**：兩個方向各自一條獨立的 stream，雙方愛什麼時候讀、什麼時候寫都行，互不阻塞。適合雙工的即時互動。

關鍵在「**互不阻塞**」這四個字，它是 bidirectional streaming 最容易被誤解的地方。兩條 stream 是**獨立**的——伺服器不必收完客戶端所有訊息才開始回，它可以邊收邊回、可以一口氣回一批再收、可以任何順序交錯。這之所以可能，正是因為底下是 HTTP/2 同一個 stream 的雙向幀流：客戶端的 DATA frame 往一個方向飛、伺服器的 DATA frame 往另一個方向飛，HTTP/2 的多工讓它們不互相排隊。它本質上給了你一條雙向、有序、型別安全的管道——很多場景下，這比自己從頭搭一套 WebSocket 協定（自訂訊息格式、自訂心跳、自訂重連）省事得多。

但這條管道有一個必須記死的邊界：**一條 gRPC stream 綁死在單一一個 HTTP/2 stream 上，而那個 HTTP/2 stream 又綁在單一一條 TCP 連線上。連線一斷，stream 就死。** gRPC 不會替你把斷掉的 streaming 呼叫接回去——它沒有「斷點續傳」這回事。一個跑了十分鐘的 bidirectional stream，網路抖一下連線斷了，你那條 stream 就結束了，已經送到一半的訊息、伺服器處理到一半的狀態，全部得由你的應用層自己決定怎麼恢復（記到哪了、從哪重來）。把 gRPC stream 當成一條「永遠可靠、會自動復原」的管道，是會在生產環境吃苦頭的假設——它是可靠的，但它的可靠只到「連線還活著」為止。

## deadline：一個會沿著呼叫鏈往下傳的時間預算

回頭看前面那個 HEADERS frame 裡的 `grpc-timeout 200m`。這是 gRPC 一個設計得相當漂亮、卻常被用錯的機制——deadline 傳播，值得單獨拆開，因為它揭示了 gRPC「把分散式呼叫當一等公民」的態度。

先釐清一個語意：gRPC 客戶端設的是 **deadline，一個絕對的時間點**——「我最多等到 12:00:00.200 為止」——而不是一個相對的「等 200 毫秒」。這個區別在多跳呼叫裡至關重要。當訂單服務帶著「200 毫秒後到期」這個 deadline 呼叫庫存服務、庫存服務又要去呼叫一個價格服務時，gRPC **不會**傻傻地把「200 毫秒」原封不動傳下去——它會把那個絕對 deadline 換算成「**從現在算起還剩多少時間**」：如果這趟呼叫已經花掉 50 毫秒了，傳給價格服務的 timeout 就是 150 毫秒，而不是 200。整條呼叫鏈共用同一個絕對截止點，每往下一跳就扣掉路上已經花掉的時間。

這個「換算成剩餘時間」的設計有個常被忽略的好處：**它對時鐘偏移（clock skew）免疫**。如果 gRPC 真的傳一個絕對時間戳「12:00:00.200」給下游，而下游那台機器的時鐘比上游快了 80 毫秒，下游就會以為已經快到期了、提早放棄。改傳「還剩 150 毫秒」這種相對量，下游用的是自己本地的時鐘從收到的那一刻起算，兩台機器的鐘對不對得齊根本不影響——這正是分散式系統裡處理時間的通用智慧（絕對時鐘不可信，見〈邏輯時鐘與排序〉）的一個具體應用。

deadline 到期時會發生什麼，也得講清楚，因為這裡藏著一個關於「合作」的真相。當 deadline 過了，客戶端會立刻放棄、把這次呼叫以 `DEADLINE_EXCEEDED`（status 4）結束。在伺服器端，gRPC 會把這個呼叫的 context 標記為已取消（呼叫變成 `CANCELLED`）——但**框架能做的僅止於「告訴你的程式它被取消了」**。它不會、也沒辦法強行中斷你伺服器端那個正在跑的函式。如果你的處理邏輯不去檢查 context 有沒有被取消、繼續悶頭把那個慢查詢跑完，那它就會**做完一整件沒有人在等結果的無用功**——客戶端早就放棄走了，你還在那邊燒 CPU、佔著資料庫連線。

這就是為什麼 deadline 是一個**合作協定，不是強制中斷**。它買到的保證是「客戶端不會等超過這個時間」，但「下游不要繼續做白工」這件事，得靠每一層伺服器自己在關鍵的阻塞點（資料庫查詢、下游呼叫、長迴圈）主動檢查 context 是否已取消、然後及早收手。設了 deadline 卻不在伺服器端尊重它，等於只買了一半的保險——你避免了客戶端傻等，卻沒避免下游資源被白白消耗（這套「把等待變成有界」的思路，整體見〈timeout、deadline 與 budget〉）。

## 為什麼瀏覽器講不了 gRPC

現在來收前面埋的那個伏筆。gRPC 在資料中心內部、服務對服務之間是主力，但有一個它至今進不去的地方：**瀏覽器無法直接講原生 gRPC。** 這不是「還沒人去做」的工程懶惰，而是一個從協定設計直接長出來的硬限制，理解它能讓你真正看懂 gRPC 把狀態放 trailer 那個決定的代價。

問題的根源就是前面那個「成功與否放在最後的 trailer 裡」的設計。gRPC 依賴 **HTTP/2 的 trailers**（body 之後才送的那個收尾 HEADERS frame）來傳 `grpc-status`。而瀏覽器給 JavaScript 用的網路 API（`fetch`、`XMLHttpRequest`）**沒有辦法讀取 HTTP/2 的 trailers，也沒辦法控制底層的二進位 framing**。瀏覽器把一個 HTTP 回應交給你時，給的是 header 加 body，它不會、也沒有 API 把「body 之後那段 trailer」交到你的 JS 手裡。歷史上其實差一點就有了——當年 gRPC 設計時，trailer 支援剛被加進 fetch 規格，但各家瀏覽器最終沒有跟進實作，這些 API 在 2019 年底正式從規格裡被移除。於是「讀 trailer」這條路，在瀏覽器裡被堵死了。

繞過去的辦法叫 **gRPC-Web**：它是一套變體協定加一個 JavaScript 客戶端函式庫，把「狀態原本在 trailer」改成「狀態編進 body 結尾的一段特殊位元組」——讓瀏覽器能用普通的 `fetch` 收完整個回應、再自己從 body 尾巴把狀態解出來。但瀏覽器送出去的這個 gRPC-Web 請求，後端的原生 gRPC 伺服器並不認得，所以中間**得有一層翻譯**把 gRPC-Web 和原生 gRPC 互相轉換。最經典的做法是擺一個 proxy（Envoy 是少數正確支援 gRPC trailer、因而能做這個翻譯的 proxy 之一）；如今多數語言也有在 gRPC 伺服器內就地翻譯的中介層（如 .NET 的 `Grpc.AspNetCore.Web`、Go 的 gRPC-Web handler 包裝），省掉那一跳獨立 proxy。

所以「瀏覽器不能直接講 gRPC」這句話，背後是一條完整的因果鏈：**為了支援 streaming，狀態必須放在訊息之後 → 所以放在 trailer → 但瀏覽器讀不到 trailer → 所以需要 gRPC-Web 變體加一層翻譯。** 這條鏈也劃出了 gRPC 的天然疆界：它是**內部服務對服務**的協定，在那裡兩端都是你能掌控的伺服器、都能講原生 HTTP/2、都認得 trailer；一旦一端是瀏覽器，這套機制的前提就破了。

## 那條長連線會騙過你的負載均衡器

gRPC 還有一個反直覺的故障模式，幾乎每個第一次大規模上 gRPC 的團隊都會踩到，而它同樣是從「跑在 HTTP/2 上」這個事實長出來的。

回想 HTTP/2 的核心好處：一條 TCP 連線上多工跑大量並發呼叫，省掉反覆建連線的成本。gRPC 把這個發揮到極致——一個 gRPC channel（客戶端到某個服務的邏輯通道）預設就維持**一條長壽命的 HTTP/2 連線**，所有的呼叫都在這條連線上的不同 stream 跑。對效能來說這很棒：連線建好就不再拆，每次呼叫只是開一個輕量的 stream。

但這個「一條長連線扛所有呼叫」的特性，會讓傳統的 **L4（傳輸層）負載均衡器形同虛設**。L4 LB 的分配單位是「連線」——它看 TCP 連線、把一條連線整個指派給某一台後端，之後這條連線上的所有東西都黏在那台。問題來了：你的 gRPC 客戶端只開了**一條**連線，那 L4 LB 就把這條連線上**全部**的呼叫——可能是每秒上萬次 RPC——全部送到**同一台**後端。其他後端在那邊閒著，這一台被打爆。LB 的儀表板上看起來連線數很均衡（每台後端各分到差不多數量的連線），但實際的請求量嚴重傾斜，因為 L4 LB 根本看不見一條連線裡跑了多少個 stream。

這個失衡還有第二層。HTTP/2 一條連線預設的並發 stream 上限（`MAX_CONCURRENT_STREAMS`）多半設在 **100** 左右——也就是說一條連線上最多 100 個呼叫同時 in-flight，第 101 個就得在客戶端**排隊**等前面的做完。所以單一連線不只造成負載傾斜，它本身還是個並發瓶頸：你以為的「高吞吐多工」，撞到這個上限就開始悄悄排隊、延遲上升。

正解是把負載均衡搬到**看得見呼叫**的層級。一條路是 **L7（應用層）負載均衡**——LB 解析 HTTP/2、以「每個請求」為單位重新挑後端，這樣同一條連線上的一萬次 RPC 才會被攤開到所有後端（L4 與 L7 的本質差異，見〈負載均衡〉）。另一條路是 **client-side 負載均衡**：gRPC 客戶端自己拿到後端清單，在內部對每個後端各開一條連線（這在 gRPC 的術語裡叫 subchannel——一個 channel 底下管著對多個後端、各自一條 HTTP/2 連線的 subchannel），再用 round-robin 之類的策略把呼叫分散到這些 subchannel 上。高吞吐的服務網格（service mesh）通常走的就是 L7／client-side 這條路。記住這條教訓的方式很簡單：**gRPC 的長連線是省連線成本的優點，但它讓「按連線分流」的 L4 LB 失去意義；要均衡 gRPC，你得在請求層級分流，不能在連線層級。**

## 為什麼是這個形狀

退一步看，gRPC 的整個樣貌，都從一個單一的決定長出來：**把服務的契約，變成一份機器可讀、強型別、能產碼的定義。**

正因為契約要強型別、要能產碼，它選了 Protobuf 當 IDL——緊湊的二進位、欄位靠號碼辨識、有明確的演進規則，讓「契約」能被編譯器檢查、能跨語言一致。正因為它要支援不只一問一答、還要 streaming，它選了 HTTP/2 當傳輸——多工的 stream 天然對應四種呼叫語意。正因為 streaming 意味著「狀態得在資料之後才能宣告」，它把 gRPC 狀態放進了 HTTP/2 的 trailer——而這個選擇，又直接決定了它進不了瀏覽器、得靠 gRPC-Web 加 proxy。正因為它把多工發揮到「一條長連線扛所有呼叫」，它讓按連線分流的 L4 LB 失效、逼著你把負載均衡上移到請求層級。連 deadline 都不只是個 timeout——它是一個沿著呼叫鏈往下傳、會自動扣掉已耗時間、對時鐘偏移免疫的時間預算。

這些特性沒有一個是任意的工程慣例。它們環環相扣，全是「我要一份能被機器檢查、能跨語言、能 streaming 的服務契約」這個目標被推到底之後，必然落到的形狀。當你下次看到一個服務的 `.proto` 檔，看到 `grpcurl` 吐出來的二進位、看到 L4 LB 後面某一台 gRPC 後端莫名其妙地比別人忙十倍——你會知道，這些都不是 bug，而是這份契約為了「機器可讀、強型別、能 streaming」所付出的、彼此牽連的代價。

## 延伸閱讀

- gRPC, "Core concepts, architecture and lifecycle"（四種呼叫語意、channel 生命週期）：https://grpc.io/docs/what-is-grpc/core-concepts/
- gRPC over HTTP/2 協定規格（length-prefixed message、trailer、grpc-status 的線上格式）：https://github.com/grpc/grpc/blob/master/doc/PROTOCOL-HTTP2.md
- gRPC, "Deadlines"（deadline 為絕對時間點、跨跳傳播換算為剩餘 timeout、對時鐘偏移免疫）：https://grpc.io/docs/guides/deadlines/
- gRPC, "Status codes and their use in gRPC"（grpc-status 碼表）：https://grpc.io/docs/guides/status-codes/
- gRPC Blog, "The state of gRPC in the browser"（為何瀏覽器需 gRPC-Web 與 proxy、trailer 限制）：https://grpc.io/blog/state-of-grpc-web/
- gRPC Blog, "gRPC on HTTP/2: Engineering a robust, high-performance protocol"（channel/subchannel、單一連線多工）：https://grpc.io/blog/grpc-on-http2/
- Protocol Buffers 官方文件（Protobuf 作為序列化格式本身）：https://protobuf.dev/
