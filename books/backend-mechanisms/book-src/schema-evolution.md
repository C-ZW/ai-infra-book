# 序列化與 schema 演進

凌晨兩點，一次再尋常不過的滾動發布（rolling deploy）正在進行。一個服務有 12 個副本，部署器一次換掉幾個，新舊版本會並存個幾分鐘。新版本對某個訊息加了一個欄位——產品經理催了三週的功能，看起來人畜無害。發布跑到一半，告警炸了：一批訂單事件在某些 consumer 上被拒收，另一些 consumer 卻把折扣金額算成了訂單金額，靜默地把帳記錯。沒有人改過任何「業務邏輯」，只是動了一下資料的形狀。

這一幕的根源，是一個資深工程師每天都在跨越、卻很少停下來想清楚的事實：**只要兩段程式要交換資料，它們之間就有一份契約——位元組怎麼排成有意義的欄位。** 而這份契約幾乎永遠不會由雙方同時換版。生產者先升、還是消費者先升；rolling deploy 期間新舊副本並存幾分鐘；一條 Kafka topic 裡躺著三個月前用舊 schema 寫下、現在才被回放的事件——在所有這些時刻，**寫資料的那一版和讀資料的那一版，不是同一版**。schema 演進這門功課要回答的，就是這個問題：當契約的兩端不同步時，怎麼讓它們仍然彼此讀得懂，或至少——壞的時候壞得吵、不要壞得安靜。

## 兩個方向，不是一個

直覺上會把相容性想成一條線：「新的能不能讀舊的」。但它其實是兩個獨立的方向，必須分開談，因為在 rolling deploy 裡你**兩個方向都會撞上**。

- **向後相容（backward compatible）**：用**新** schema 的程式，能讀**舊** schema 寫的資料。consumer 先升級、還在消化佇列裡舊版生產者留下的訊息時，靠的就是這個。
- **向前相容（forward compatible）**：用**舊** schema 的程式，能讀**新** schema 寫的資料。producer 先升級、但有些 consumer 還沒換版時，舊 consumer 必須能消化新格式——這要求它能**忽略自己不認得的東西**，而不是看到陌生欄位就翻臉。

把兩者擺在一起就看出張力了。一個 rolling deploy 期間，同一條 topic 上同時有「新 producer + 舊 consumer」（需要向前相容）和「舊 producer + 新 consumer」（需要向後相容）。要讓發布過程任何一刻都不出事，這次變更必須**同時**向前且向後相容——這叫**完全相容（full）**。而能同時滿足兩個方向的變更，集合小得驚人：基本上只剩「加一個可選欄位」和「刪一個可選欄位」。這就是為什麼老手對 schema 變更近乎神經質地保守——不是膽小，是因為「安全變更」的窗口本來就窄。

開場那個事故，正是踩在這條窄縫之外：加欄位本來安全，但有人「順手」把另一個欄位的位置改了，於是它連向後相容都不是了。要看懂這怎麼發生的，得鑽進序列化格式的底層——欄位到底是靠什麼被認出來的。

## 欄位是靠名字認，還是靠號碼認

天真的格式靠**名字**認欄位。JSON 就是這樣：`{"id": "A1", "amount": 500}`，讀的人按 key 字串找欄位。這帶來一種與生俱來的寬容——多出來一個 key？不認得，跳過。少了一個 key？當它沒給。正因如此，JSON 天然就偏向相容：加欄位、刪欄位，對一個「按名字找、找不到就算了」的 parser 來說都不致命。代價是它把欄位名一遍遍寫進每一筆訊息（體積大）、沒有型別、而且**沒有人替你擋**——相容與否全靠紀律和測試，格式本身不知道什麼叫「破壞性變更」。

二進位格式為了緊湊，把名字換成了**號碼**。這是理解 schema 演進的關鍵分水嶺，而 Protobuf 是這條路上最值得拆開看的代表。在 Protobuf 裡，每個欄位在 `.proto` 定義裡綁死一個 **field number**：

```proto
message Order {
  string id       = 1;
  int64  discount = 2;
  int64  amount   = 5;
}
```

那個 `= 1`、`= 2`、`= 5` 不是順序、不是預設值，而是這個欄位在**線上位元組（wire）裡的身分證**。欄位名 `id`、`amount` 在編譯後根本不上線——傳輸的位元組裡只有號碼。一筆 Protobuf 訊息在線上長成一串 `(tag, value)`，而 tag 這個位元組是這樣拼出來的：把 field number 左移三位、低三位塞進 **wire type**（值的物理形狀：0 = varint 整數類、1 = 64-bit、2 = 長度前綴的位元組串、5 = 32-bit；另有已棄用的 3/4 group）：

```
tag = (field_number << 3) | wire_type
```

舉個能手算的例子。`string id = 1`，字串的 wire type 是 2（length-delimited），所以它的 tag 是 `(1 << 3) | 2 = 0x0A`；後面跟一個 varint 長度、再跟 UTF-8 位元組。`int64 amount = 5`，整數走 varint、wire type 0，tag 是 `(5 << 3) | 0 = 0x28`。讀的一方掃過位元組流，每讀到一個 tag，就右移三位拿回 field number、低三位拿回 wire type，據此知道「接下來這段位元組屬於 5 號欄位、是個 varint」。**整個解碼過程從頭到尾不需要欄位名**——它認的是號碼。

這個設計一口氣解釋了 Protobuf 的全部相容規則，它們不是一串要背的戒律，而是「靠號碼認」這件事的直接推論：

- **加一個新欄位**，給它一個從沒用過的號碼——安全。舊讀者掃到不認得的號碼，知道該跳過多少位元組（wire type 告訴它值的形狀），略過就好；新讀者讀舊資料時那個號碼根本不存在，欄位取型別預設值（`int64` 是 0、`string` 是空字串）。向前向後都成立。
- **刪一個欄位**——只要那個號碼從此**永不再被任何人用**，就安全。
- **改一個欄位的號碼，或拿一個用過的號碼去指別的欄位**——災難，而且是**安靜的**災難。

## 開場那場安靜的災難，重放一遍

現在可以把凌晨兩點那一幕放慢重看。原本的 `Order` 是 `id=1, discount=2, amount=5`。有人覺得 `discount` 已經棄用、號碼又跳號很醜，於是「整理」了一下：刪掉 `discount`，再把 `amount` 從 5 號改成 2 號，讓號碼連續好看。新 schema 變成 `id=1, amount=2`。

問題是，佇列裡、log 裡、還沒被消化完的舊訊息，是用**舊** schema 寫的——它們的位元組流裡，2 號 tag 後面跟著的是 `discount` 的值。新程式拿到這串位元組，掃到 2 號 tag，它的世界裡 2 號是 `amount`，於是它若無其事地把折扣金額讀進了訂單金額。

致命的地方在於：`discount` 和 `amount` 都是 `int64`、wire type 都是 0。**wire format 沒有任何一個位元在記「這個 2 號當初是誰」**——線上只有號碼和 wire type，沒有名字、沒有版本、沒有校驗。型別還剛好一樣，連「型別對不上、解碼爆掉」這種至少會吵的失敗都不會發生。資料被解爛了，但每一筆都「成功」解析、回了 2xx、寫進了下游。等到對帳那天有人發現帳對不上，已是幾百萬筆之後。

這就是為什麼 Protobuf 的頭號鐵律是**永不重用 field number**，以及它配套的安全網——刪欄位時用 `reserved` 把號碼和名字一起封印：

```proto
message Order {
  reserved 2;            // 號碼永久退役
  reserved "discount";   // 名字也封，防有人換了個欄位又叫 discount
  string id     = 1;
  int64  amount = 5;     // 維持原號，絕不挪
}
```

`reserved 2;` 之後，任何人想再把某個欄位編號成 2，編譯期就會直接報錯——把一個本來只在「上線後、撞到舊資料時」才爆的執行期災難，提前成一個編譯不過的紅字。這正是號碼制相容性的精髓：**它把相容檢查的責任，從「線上偶然撞到」前移到「定義 schema 的當下」。**

順帶兩個容易被當小事、其實多半是破壞性變更的動作。一是**改型別**，而這裡的陷阱在於「看起來同一類的型別其實分屬不同相容群」。`int32`、`uint32`、`int64`、`uint64`、`bool` 彼此 wire 相容（都走 wire type 0 的 varint），所以 `int32 → int64` 其實是安全變更，唯一風險是舊讀者用 `int32` 讀到超過 32 位的值時會被截斷——這是 lossy，不是「解成另一個數」。真正安靜致命的是跨群改型別，最隱蔽的是 `int32 → sint32`：兩者同為 wire type 0 varint，但 `sint32`/`sint64` 走的是 zigzag 編碼、和 `int32` 系的補碼互不相容，同一串位元組會被解成**完全不同的數值**，連解碼爆掉都不會發生。安全的做法永遠是「加一個新號碼的新欄位、舊欄位 deprecate」，而不是原地改型別。二是 proto3 **拿掉了 `required`**——這不是疏漏，正是相容性的設計。一個 `required` 欄位等於宣告「所有讀者永遠都必須有這個欄位」，一旦你想刪它，任何還沒升級、仍堅持它必填的舊讀者都會拒收新資料。`required` 把一個欄位變成永遠不能演進的水泥塊，所以 proto3 索性不給你這個自找麻煩的工具。

## 一個沒人預料到的轉發坑：被丟掉的未知欄位

到這裡，「向前相容＝舊讀者忽略不認得的欄位」聽起來已經牢靠。但有一個非顯然的邊界，曾經真的咬過很多人，值得單獨講透，因為它揭示了「忽略」和「保留」是兩回事。

設想一個三段管線：服務 A 產生訊息 → 中介服務 B 收下、改一兩個欄位、再轉發 → 服務 C 消費。某天 A 升級了 schema、加了個新欄位 `currency`，但 B 還是舊版、不認得 `currency`。按向前相容的承諾，B 應該「忽略」這個未知欄位——這沒錯。但問題是：B 不只是讀，它還**反序列化成物件、改個欄位、再序列化轉發出去**。當 B 把訊息重新序列化時，那個它「忽略」掉的 `currency` 會怎樣？

如果 B 用的執行庫只是在讀的時候跳過未知欄位、**沒有把原始位元組留下來**，那麼 B 轉出去的訊息就**永久少了 `currency` 這個欄位**。C 是新版、本來認得 `currency`、也指望它在，結果收到的訊息裡它憑空消失了。A 明明寫了，C 卻讀不到——向前相容的鏈條在中間那一跳被悄悄剪斷。

這不是假想。proto3 早期版本（v3.5 之前）的行為，正是**在解析時直接丟棄未知欄位**，而非像 proto2 那樣保留。這個設計在「A→B→C 且 B 會重新序列化」的轉發場景下會默默掉資料，被回報得夠痛，於是 v3.5 把行為改回**保留未知欄位**——解析時把不認得的 `(tag, value)` 原樣存進訊息的 unknown fields 區，重新序列化時再原封不動寫回去。值得記住的是這個保證仍有破口：一旦你把 Protobuf 轉成 JSON 再轉回來（很多閘道、log 管線會這麼做），未知欄位就沒了棲身之處，照樣丟。**「忽略未知欄位」保的是「我不會因為看到它而崩潰」，不保證「我會替你把它原封帶到下一站」**——這兩件事的差別，正是這個坑的全部。

## 當格式自帶 schema：Avro 與「default 才是主角」

Protobuf 把相容性壓在「號碼」上。Avro 走了一條不同的路，值得對照著看，因為它把另一個維度推到了極致——**default 值**。

Avro 的訊息在線上**不帶欄位 tag、也不帶名字**，就是一串緊湊的值，按 schema 定義的順序排好。這比 Protobuf 還省，但代價是：**光看位元組你完全不知道它是什麼**——你必須知道**寫它的時候用的是哪份 schema（writer schema）**，才能把這串位元組切回一個個欄位。讀的時候，你手上是另一份 schema（reader schema），Avro 做一件叫 **schema resolution** 的事，把兩份 schema 對齊：

- reader 有、而 writer 沒有的欄位（reader 比較新，加了個欄位）→ 用 reader 那個欄位宣告的 **default** 值補上。
- writer 有、而 reader 沒有的欄位（writer 比較新）→ reader 直接忽略這段值。

關鍵的不對稱在第一條：**加欄位要向後相容，那個欄位就一定得有 default。** 如果你加了個新欄位卻沒給 default，舊資料（writer schema 裡沒這欄位）用新 reader 讀的時候，Avro 沒有任何值可填、又不准它瞎猜，於是**直接報錯**。Protobuf 永遠有型別預設值兜底（0、空字串），所以「加欄位忘了想 default」這個坑在 Protobuf 不存在；但在 Avro，**default 是相容性的承重牆**——少給一個 default，一次本以為安全的加欄位就會在讀舊資料時炸。

還有一個 Avro 獨有的前提常被忽略：既然解碼非得有 writer schema，那 writer schema 就**必須能被讀取端拿到**。在 Kafka 的世界這通常意味著每筆訊息裡塞一個 schema ID、讀的時候拿這個 ID 去某個地方換回完整的 writer schema——這就把我們帶到了下一個層次的機制。

## 把「相容」從口頭約定變成擋得住的閘

到目前為止，所有相容規則都還是**紀律**：你得記得別重用號碼、記得給 default、記得加欄位要可選。在一個人的服務裡，紀律也許夠。但一條 Kafka topic 上游有五個團隊在發、下游有八個團隊在收，紀律就會在某個週五下午的趕工裡破功——有人 PR 過了 review、上了線，三個月後才有人回放到那批資料時才發現格式早被改爛。

**schema registry**（Confluent Schema Registry 是最常見的一個）就是來把這份紀律**機械化**的。它是一個集中存放所有 schema 版本的服務。生產者要寫一筆訊息前，先把自己這版 schema 註冊上去，換回一個短短的 schema ID，訊息裡只帶這個 ID（而非整份 schema）；消費者拿 ID 回 registry 換完整 schema 來解碼。這順手解決了 Avro「reader 得拿得到 writer schema」的問題——大家都去 registry 拿。

但 registry 真正的價值不在存，在**擋**。註冊一個新版本時，registry 會拿它和歷史版本做相容性檢查，**不相容就拒絕註冊**——於是「破壞相容的 schema 變更」變成一個**部署前就失敗**的動作，而不是一個上線後才咬人的地雷。你在 registry 上設定這條 topic 要的相容模式（compatibility type，2026-06）：

| 模式 | 檢查什麼 | 允許的變更 | 拿來保護什麼 |
|---|---|---|---|
| BACKWARD（**預設**） | 新 schema 能讀舊資料 | 加可選欄位、刪欄位 | 新 consumer 能消化舊訊息（可從頭回放 topic） |
| FORWARD | 舊 schema 能讀新資料 | 加欄位、刪可選欄位 | 舊 consumer 能消化新訊息（producer 先升） |
| FULL | 同時向前向後 | 只能加/刪可選欄位 | rolling deploy 任一刻都安全 |
| *_TRANSITIVE | 同上，但比**所有**歷史版本 | 同上，更嚴 | 要回放任意舊資料、不只最近一版 |

這裡藏著一個極容易誤判的預設行為，務必看清。Confluent 的預設是 **BACKWARD，而且是非遞移（non-transitive）的**——它只拿新 schema 和**最近註冊的那一版**比，不和更早的版本比。這在多數情況很合理，但對「會回放很久以前資料」的場景是個陷阱：你可以走 V1→V2→V3 每一步都對「前一版」向後相容、每一步都通過檢查，但 V3 對 V1 卻**不**相容。日常消費沒事（大家都在 V2、V3 附近），可某天你把 consumer rewind 到 topic 開頭去重放 V1 時代的事件，V3 的 reader 就讀不動了——而 registry 從頭到尾沒攔你，因為你從沒讓它檢查過 V3 對 V1。要堵這個洞，得把模式設成 **BACKWARD_TRANSITIVE**，逼它每次都對**全部**歷史版本驗。Kafka 之所以把 BACKWARD（非遞移）當預設，是因為它的招牌用法是「consumer 用最新 schema 從頭讀整條 topic」——而這恰恰是 BACKWARD 保護的方向；但「能從頭讀」和「能讀到最古老那版」之間的那道縫，得你自己知道要不要補。

## 該用哪一套：判準是「對端受不受你控制」

把上面三條路擺到一起——JSON 的寬容、Protobuf 的號碼、Avro 的 default＋registry——選擇就清楚了，而選擇的軸線不是「哪個更先進」，是三個很具體的問題：**對端受不受你控制？升級同不同步？演進頻不頻繁？**

對外的 public API，三個答案都是「否」：消費者是你管不到的第三方，他們什麼時候升級、會不會嚴格解析，你無從得知。這時 JSON 的寬容與人類可讀反而是**優點**——配上端點版本化（`/v1`、`/v2`，見〈REST 設計、版本化與 OpenAPI 契約〉），讓不可控的對端能自己選版、能用瀏覽器直接看懂。對這種場景硬上 schema registry 是搞錯了戰場：你根本沒法強迫外部消費者去你的 registry 取 schema。

反過來，多團隊共用的內部事件 topic、長期保存待回放的事件流（event sourcing 的 log 一存就是好幾年，見〈Event sourcing 與 CQRS〉）、高吞吐的內部 RPC（gRPC 用 Protobuf 當 IDL 與傳輸，見〈gRPC 與 Protobuf〉）——這些場景三個答案多半都是「是」：對端是自家服務、升級你能協調、schema 一個季度改好幾次。它們值得也需要把相容性變成 CI 擋得住的東西，於是 Protobuf/Avro ＋ registry 是回得了本的投資。判準一句話：**對端越不可控、JSON 的寬容越值錢；對端越可控、強 schema ＋ registry 的「擋得住」越值錢。**

最後劃清一條常被混淆的界線。本章從頭到尾講的都是**線上協定（wire）的相容**——跨服務傳的訊息、RPC payload 怎麼在不同版本間平滑演進。這和「資料庫裡的欄位真的加一欄、改個型別、拆張表怎麼不停機」是**兩回事**——後者是儲存層的結構變更（見〈零停機 schema 遷移〉），有它自己一整套 expand-contract 與 backfill 的功課。兩者互為表裡：協定相容讓「傳輸」不破，DB 遷移讓「儲存」不停機；只顧一邊、另一邊照樣在某次發布的半路炸開。一筆資料從某個服務的記憶體、序列化上線、跨網路、再落進另一個服務的資料庫，每一段交接都是一份契約，而每一份契約都會各自演進、各自在不同步的那一刻考驗你。

## 為何是這個形狀

退一步看，整套 schema 演進的機制，都是從一個無法迴避的事實裡長出來的：**寫資料的那一版，和讀資料的那一版，永遠不保證是同一版。** rolling deploy 讓它們在同一刻並存，event log 讓它們相隔數年，跨團隊的 topic 讓它們分屬不同人的發布節奏。

正因如此，格式得在「不認得的東西」面前選擇優雅地略過，而非翻臉——所以未知欄位要能被忽略、最好還能被原樣保留。正因如此，二進位格式不敢靠會被人「順手整理」的名字認欄位，而靠一個一旦定下就絕不能動的號碼——所以有了 `reserved`、有了「永不重用」的鐵律。正因如此，光靠工程師的紀律守不住一條多人共寫的 topic，於是相容檢查被機械化、前移到註冊的那一刻——所以有了 registry 那道擋得住的閘。schema 演進不是一堆要背的最佳實踐，而是「契約兩端註定不同步」這個事實被逼到牆角後，序列化格式唯一站得住的形狀。

開場那批被靜默記錯的訂單，最終是靠 `reserved` 那一行、靠把 registry 模式調成會擋住重用號碼的設定補上的。下次當你準備對一個跨服務的訊息「順手整理」一下欄位，你會記得：線上的位元組裡沒有名字、沒有版本、沒有人替你校驗——只有號碼，以及一份你和未來每一版自己都得遵守的契約。

## 延伸閱讀

- Protocol Buffers, "Language Guide (proto 3)"（field number、`reserved`、`required` 的移除與相容規則）: https://protobuf.dev/programming-guides/proto3/
- Protocol Buffers, "Encoding"（wire format、`(field_number << 3) | wire_type` 的 tag 編碼、varint）: https://protobuf.dev/programming-guides/encoding/
- Protocol Buffers, "Proto Best Practices"（為何永不重用 field number、未知欄位的保留）: https://protobuf.dev/best-practices/dos-donts/
- Apache Avro Specification, "Schema Resolution"（writer/reader schema 對齊、default 的角色）: https://avro.apache.org/docs/1.12.0/specification/#schema-resolution
- Confluent Docs, "Schema Evolution and Compatibility"（BACKWARD/FORWARD/FULL 與 TRANSITIVE、預設模式）: https://docs.confluent.io/platform/current/schema-registry/fundamentals/schema-evolution.html
- Martin Kleppmann, *Designing Data-Intensive Applications*, Ch. 4 "Encoding and Evolution": https://dataintensive.net/
