# API 閘道對照：ALB、API Gateway、KrakenD、Kong

桌上擺著一個再普通不過的需求：一個對外的 HTTPS 入口，後面是一群微服務。請求進來要驗 token、要擋住把你打爆的流量、要依路徑導到對的後端、有時還要把三個後端的回應併成一個。橫切關注該集中在入口層，這件事本身已經有定論（見〈API gateway 的角色〉）。現在問題變得很具體：**這個盒子，到底放什麼？**

市面上掛著「API 閘道」名號的東西多到讓人麻木——AWS 的 ALB、AWS 的 API Gateway、KrakenD、Kong，光這四個就常被排在同一張比較表裡，欄位填滿「支援限流：是／否」「支援轉換：是／否」的勾叉。但這張表會誤導人。它把四個**形狀根本不同**的東西，壓平成同一個尺度上的強弱競品，好像挑閘道像挑手機、看規格表勾最多的那個就贏。

真相是，這四個盒子的差異不在功能多寡，而在**它們是什麼**：一個是負載均衡器被當閘道用、一個是雲廠的全託管服務、一個是無狀態的設定編譯器、一個是 NGINX 上長出來的外掛宿主。功能可以補，但「它是什麼」決定了你半夜被叫起來時面對的是哪一種麻煩。要看清楚這點，最好的辦法不是讀規格表，而是**拿同一個請求，看它穿過這四個盒子時，各自發生了什麼**。

## 為什麼一張勾叉表會騙你

先說清楚這張表錯在哪，否則後面講的一切都會被「那不就是功能差異嗎」帶偏。

勾叉表預設了一個前提：所有閘道都在做同一件事，只是做得多或少。按這個前提，ALB 那一欄會很難看——「限流：否」「per-request 轉換：否」「細粒度授權：否」，三個叉。於是你會得到一個荒謬的結論：ALB 是「功能最弱的閘道」。

但 ALB 根本不想當功能完整的閘道。它是一台 L7 負載均衡器（負載均衡的 L4/L7 機制見〈負載均衡〉），它的工作是把流量穩穩地、低延遲地、便宜地分到一群後端上。它「不做轉換」不是缺陷，是**刻意的克制**——一台每秒要過幾萬個請求的負載均衡器，如果在資料路徑上對每個請求跑一套 Velocity 模板去重塑 JSON，它就不再是負載均衡器了，它會變慢、變貴、變得難以預測。ALB 的三個叉，是它為了「在純路由場景下延遲最低、成本最低」付的代價，不是它輸了。

所以正確的問法不是「誰功能多」，而是**「我這個請求真正需要在入口層發生什麼，而我願意為此付什麼」**。把這個問題想清楚，四個盒子各自的位置就浮出來了。我們一個一個看。

## 第一個盒子：ALB——把閘道當路由器

一個 `POST /orders` 帶著 `Authorization: Bearer …` 打進 ALB。ALB 做的事，可以完整地列出來，而且短得驚人：

它在 HTTPS listener 上終結 TLS（把加密解開），然後拿請求的 host、path、header 去比對你設定的一串 **listener rule**——`if path == /orders/* then forward to target-group-orders`。比中了，就把這個（已解密的）請求轉給目標群裡一個健康的後端。健康與否由 ALB 持續對後端打健康檢查決定（見〈health check〉）。就這樣。請求的 body 它原封不動轉過去，回應也原封不動轉回來。

值得停下來看的是它**沒做**什麼。那個 `Bearer` token，ALB 預設**看都不看**——它不驗簽、不查 introspection，後端收到的還是原始 token，得自己驗。ALB 確實有一個內建的驗證能力：在 HTTPS listener 上掛 `authenticate-oidc` 或 `authenticate-cognito` 動作，它就會攔住未登入的請求、把使用者重導到 IdP 跑完 OAuth 流程、驗完把使用者資訊塞進 `X-AMZN-OIDC-*` 系列 header 再轉給後端。聽起來很像閘道在做的事，但這裡有兩個容易踩空的邊界：

第一，它做的是**認證（你是誰）**，不是**授權（你能做什麼）**。ALB 確認了「這個人登入了、他是 user 9」，但「user 9 能不能改這筆訂單」是業務規則，ALB 不碰——後端還是得自己讀 JWT 裡的 claim 去判。把細粒度授權外包給 ALB 是落空的。

第二，那個塞進 header 的使用者 claim 是有大小上限的：**如果 IdP 回來的 claim 加 access token 超過 11 KB，ALB 直接回 client 一個 HTTP 500、並把 `ELBAuthUserClaimsSizeExceeded` 這個 metric 加一**。一個塞了太多 group/role 的企業 IdP，會讓一部分使用者在登入後莫名其妙拿到 500，而錯誤訊息裡完全看不出是 claim 撐爆了——你得去翻那個 metric 才知道。這是 ALB 內建驗證最隱蔽的故障模式。

至於限流，ALB **原生沒有**。你想擋住「同一個 IP 每秒打 1000 次」這種流量，ALB 自己做不到，得在它前面掛 AWS WAF、用 rate-based rule 去擋。也沒有 per-request 的 request/response 轉換、沒有 Lambda authorizer 那種掛自訂驗證邏輯的鉤子——這些都是 API Gateway 的領域，不是 ALB 的。

所以 ALB 的真實定位是：**當你要的就是「把 L7 流量穩穩分給一群容器或 EC2」、而 authn/限流/轉換你打算在別處做（後端自己、或前面的 WAF、或乾脆不需要）時，ALB 是延遲最低、單位成本最低的入口。** 它的計費走 LCU（Load Balancer Capacity Unit）——一個小時內取「新連線數、活躍連線數、處理位元組數、規則評估數」四個維度的最高者來算，在高吞吐下平均到每個請求的成本很低。它常常不是唯一的入口，而是 API Gateway 後面、或 EKS/ECS 服務對外的那一層純路由。

## 第二個盒子：API Gateway——把閘道外包給雲廠

同一個 `POST /orders`，這次打進 AWS API Gateway。畫面完全不同。

API Gateway 是 AWS 全託管的閘道，它把「閘道層該做的橫切關注」打包成你用設定就能開的功能：在請求進到後端之前，它可以驗 token（JWT authorizer 驗簽、或 Lambda authorizer 跑你自己的驗證碼、或 IAM）、套限流、用 usage plan 對不同的 API key 計量配額、用 VTL（Velocity Template Language）mapping template 把請求和回應重塑成另一個形狀。後端（常常是一個 Lambda）收到的，是一個已經驗過身、被整形過的乾淨請求。

這裡最值得手算到底的，是**限流**——因為它的預設值藏著一個會讓人半夜踩雷的陷阱。

API Gateway 的 REST API 有一個**帳戶層、每個 Region** 的預設限流：穩定速率 **10,000 RPS**、burst（token bucket 的桶容量）**5,000**。它用的就是 token bucket：桶裡的 token 以每秒 10,000 的速率補充，每個請求消耗一個 token，桶最大裝 5,000 個（允許短暫突刺）；token 取光了，後續請求就吃 `429 Too Many Requests`。注意這幾個關鍵字——**「帳戶層」「每個 Region」「所有 REST API 合計」**。這個 10,000 不是某一支 API 的額度，是你這個帳戶在這個 Region 裡**全部 REST API 加起來**的合計。（還有個易漏的點：較新的 Region，如開普敦、米蘭、雅加達、阿聯酋等，預設較低，是 2,500 RPS / 1,250 burst。）

把這個陷阱演一遍。你上線一支 serverless API，平時 200 RPS，離 10,000 遠得很，看起來毫無風險。但同一個帳戶、同一個 Region 裡，另有一個批次作業偶爾會衝到 9,000 RPS。兩者相加 9,200，還沒事；可是當批次衝到 9,900、你的 API 正好來了 200，合計 10,100——**超了**。於是你那支平時只有 200 RPS、八竿子打不著上限的低流量 API，會莫名其妙開始回 429。你盯著自己 API 的 CloudWatch，流量明明很低，卻在限流，怎麼看都看不懂——因為瓶頸根本不在你這支 API，在隔壁那個吃掉共用桶的批次作業。

要堵這個漏，不能只靠帳戶層預設，得在 stage/method 設 per-stage throttle，或對第三方用 usage plan 設 per-key 限制，把不同 API 的流量彼此**隔離**開（這正是艙壁的思路，見〈bulkhead〉）。API Gateway 套用限流是有優先序的：先看 usage plan 裡的 per-client/per-method 限制，再看 per-stage 限制，再落到帳戶層，最後才是 AWS 自己跨帳戶的 Regional 上限。你設的隔離規則之所以有效，是因為它們排在帳戶層那個共用桶之前先擋。

還有一個措辭上的硬事實，官方文件講得很白：**這些限流是 best-effort 的目標值，不是保證上限。** token bucket 在某些情況下會被突破，AWS 明說「應該把它當成 target、而非 guaranteed ceiling」。換句話說，你不能拿 API Gateway 的限流當「絕對擋住 10,001 個就一個都不放過」的安全閥——它是流量整形，不是嚴格閘門。

API Gateway 自己也分兩種，而且**這兩種的差異本身就是一個取捨的縮影**。**REST API** 功能最完整：VTL 轉換、usage plan、API key、私有端點全有。**HTTP API** 較新、刻意做薄：支援 JWT authorizer、延遲較低，**價格約便宜七成**——以 2026-06 的訂價，HTTP API 約 $1.00 / 百萬次請求，REST API 約 $3.50 / 百萬次，一個 100M 次/月的 API 光閘道費就差約 $250/月。代價是 HTTP API **沒有** VTL 完整轉換（只有簡單的 header/query/path 參數對映）、沒有 usage plan、沒有 API key。所以判準很乾淨：要 VTL 轉換 / usage plan / API key，用 REST API；只要便宜快速的 proxy 加簡單 JWT 驗證，用 HTTP API。多花的那七成價錢，買的就是那幾個 REST API 獨有的功能；用不到，就是純浪費。

API Gateway 的整個性格是：**你不維運任何東西，AWS 幫你扛高可用、扛擴展、扛打補丁；代價是更高的單位成本、多一層延遲、以及綁死在 AWS 上。** 它和 Lambda 組 serverless API 時幾乎是預設搭配。

## 第三個盒子：KrakenD——閘道是一份被編譯的設定

換 KrakenD。同一個請求進來，但你得先理解一件根本不同的事：**KrakenD 啟動時，讀一份 JSON 設定檔，就跑了。** 它是用 Go 寫的、無狀態（stateless）、宣告式（declarative）的閘道，**沒有 runtime database**。沒有控制面資料庫、沒有需要同步的叢集狀態、沒有「管理 API 去動態改設定」這回事。設定就是那份 JSON；要改設定，就改檔案、重新部署一份新的 KrakenD。

這個「無狀態」不是行銷詞，它有具體的後果。因為每個 KrakenD 實例都是「同一份 JSON 編出來的、彼此完全等價的純函數」，水平擴展就退化成最簡單的形式——多開幾個一模一樣的實例擺在負載均衡器後面就好，它們之間不需要協調、不需要選 leader、不需要對齊任何共享狀態。部署一個 KrakenD 叢集的心智負擔，幾乎等於部署一個無狀態的 web app。這是它跟 Kong 最大的分水嶺，後面會看到。

KrakenD 的招牌能力是**原生 API 聚合（native API aggregation）**——這也是同一個請求在 KrakenD 裡會發生最有趣的事。設想前端要顯示一個訂單詳情頁，需要「訂單 + 買家 + 三個品項」。在沒有聚合的世界，前端得自己打 `GET /orders/1`、`GET /users/9`、再三個 `GET /products/{id}`，五次往返。KrakenD 讓你在設定裡宣告一個對外端點 `GET /order-detail/1`，背後綁三個（或更多）後端呼叫：

```jsonc
// KrakenD endpoint config (示意，非完整)
{
  "endpoint": "/order-detail/{id}",
  "method": "GET",
  "backend": [
    { "url_pattern": "/orders/{id}",   "group": "order" },
    { "url_pattern": "/users/{user}",  "group": "buyer" },
    { "url_pattern": "/products?ids={pids}", "group": "items" }
  ]
}
```

KrakenD 收到一個外部請求，**平行**打這幾個後端，把回應併成一個 JSON 回給 client，過程中還能過濾欄位（後端回 50 個欄位、只保留前端要的 5 個）、重新命名、攤平結構。一次外部往返，背後是並行的多個內部呼叫。對「閘道層就是要把多後端拼成一個對外回應、而且要極高吞吐」的場景（典型的 BFF），KrakenD 是這四個裡最契合的。

但這裡有個治理上的事實必須講精確，因為它常被講錯。**捐給基金會的不是整個 KrakenD，而是它的核心 framework**——那個 framework 於 2021-05 捐成由 **Linux Foundation** 主持的 **Lura Project**；KrakenD 的 Community 與 Enterprise 版，是 Lura 這個 engine 的兩個實作。兩個常見的口誤要避開：一是說「KrakenD 是 CNCF 專案」——錯，是 **Linux Foundation，不是 CNCF**，兩者不可混用；二是說「KrakenD 仍是一家獨立開源公司」——也不準確，KrakenD（公司）於 **2025-08 被 Shop Circle 收購**，團隊與路線維持、Lura framework 續留 Linux Foundation，但「獨立公司」這個前提在 2025 之後已經不成立（2026-06）。

KrakenD 還有一個它引以為傲、但你選型時必須當成限制看的特性：**它沒有 runtime plugin 系統。** 這不是說它不能擴充——它支援啟動時編入的 Go plugin，只是這些 plugin 在服務啟動、開始收請求之前就載入定死，不在執行期動態掛載。它的高效能、可預測，部分正來自「不在執行期動態載入第三方外掛」這個克制——一切都在那份靜態 JSON 裡定死、啟動時編好。這個「啟動時編入 vs 執行期掛載」的分界，跟下一個盒子恰好是光譜的兩端。

## 第四個盒子：Kong——閘道是 NGINX 上的外掛宿主

最後是 Kong。要理解 Kong 在同一個請求上做什麼，得先看它**站在誰肩膀上**：Kong 建在 **NGINX + OpenResty** 之上。OpenResty 不是 NGINX 的 fork，而是一套把 Lua（透過 `lua-nginx-module`）嵌進 NGINX 的整合工具鏈。Kong 的核心邏輯——路由、安全、管理——是用 **Lua** 寫的，掛在 NGINX 處理一個請求的生命週期各個 phase 上。

於是 Kong 的請求路徑長這樣：一個請求進來，NGINX 接住，然後在「驗證階段」「轉換階段」「回應階段」等各個 phase，依序執行你掛上去的一串 **plugin**——每個 plugin 就是一個掛進某個 phase 的 Lua 模組。要加認證？掛 auth plugin。要限流？掛 rate-limiting plugin。要記 log、轉換 header、做 A/B？各有 plugin。**Kong 的整個價值主張就是這個 plugin 生態**：它不像 KrakenD 把能力編進靜態設定，而是讓你用一堆可插拔的 Lua 模組，在執行期拼裝出你要的閘道行為。要 KrakenD 沒有的那種「靠社群外掛拼出各種能力」，Kong 的生態最廣。

代價直接寫在它的形狀裡：**Kong 的控制面有狀態。** 它的設定（哪些 route、哪些 plugin、什麼參數）存在一個資料庫裡——這裡有個 2026 必須講對的事實：**Kong 從 3.4 起移除了 Cassandra 支援，PostgreSQL 是現在唯一官方支援的資料庫**（早年文件裡的「PostgreSQL 或 Cassandra」已過時）。所以自架一個 DB 模式的 Kong，你扛的不只是 Kong 本身，還有那台 PostgreSQL 控制面的高可用、備份、升級。

Kong 也提供一個 **DB-less（宣告式）模式**——把整份設定寫成一個 YAML，Kong 啟動時讀進記憶體，不連資料庫。這把 Kong 拉得比較靠近 KrakenD 那種無狀態形態，部署簡單很多。但要小心一個常見的誤解：**DB-less 不等於「沒有任何狀態問題」**。它移除的是 PostgreSQL 控制面，但宣告式設定在多個節點間的同步、plugin 在執行期自己維護的狀態（例如限流計數），這些仍然要顧。DB-less 簡化的是控制面，不是消滅了一切狀態考量。

Kong 的真實定位是：**當你要一個 plugin 可插拔、能跨雲／自架、生態成熟的閘道，而且願意維運它（DB 模式還得顧 PostgreSQL）時。** 它和 KrakenD 是「自架閘道」這個區間裡兩種相反的哲學——一個用靜態設定換可預測與極簡部署，一個用動態外掛換無限可擴展。

## 真正的分水嶺：誰半夜被叫起來

把四個盒子在同一個請求上的行為攤開後，那張勾叉表想表達的「功能差異」其實是表層。**真正決定選型的，是兩條更深的軸——而它們都跟「半夜出事時，是誰、面對什麼」有關。**

第一條軸是**託管 vs 自架**。ALB 和 API Gateway 是 AWS 全託管：你不維運任何東西，高可用、擴展、打補丁都是 AWS 的事；代價是綁死在 AWS、計費隨流量走、行為由雲廠決定（連限流是不是「保證」都是它說了算）。KrakenD 和 Kong 可以自架：跨雲、可掌控、行為你能讀原始碼搞懂；代價是升級、高可用、出事時的待命，全是你的。閘道坐在所有對外流量的必經點上，它掛了就是全系統掛了——它必須比它保護的後端更可靠（見〈health check〉）。所以「誰來保證這個必經點不掛」這件事，託管是把它交給 AWS，自架是攬到自己身上。半夜 PostgreSQL 控制面掛了，KrakenD 的人不會被叫起來（它根本沒有 DB），Kong DB 模式的人會。

第二條軸是**有狀態 vs 無狀態的控制面**。這條軸把自架的兩個分了開：KrakenD 無 runtime DB、啟動讀 JSON，水平擴展近乎免費；Kong 的 DB 模式有 PostgreSQL 控制面，換來的是 plugin 生態與動態管理，付出的是運維面。這不是「誰比較好」，是「你願意用運維複雜度去換可插拔，還是用功能克制去換部署簡單」。

純路由、不要 per-request authz/轉換，ALB 延遲最低成本最低；要 throttling + authz + 轉換 + 計量、又願意綁 AWS、不想維運，API Gateway；要跨雲自架 + 把多後端聚合成一個回應，KrakenD；要跨雲自架 + 靠 plugin 生態拼裝，且願意維運控制面，Kong。一張表收尾，但請記得它只是前面那串敘事的速查，不是骨幹：

| 盒子 | 它到底是什麼 | 入口層做什麼 | 不做什麼／邊界 | 真正的代價 |
|---|---|---|---|---|
| AWS ALB | L7 負載均衡器 | 路由、TLS 終結、健康檢查、OIDC/Cognito 認證 | 無原生限流（靠 WAF）、無 per-request 轉換、只 authn 不 authz | 綁 AWS；claim >11KB 回 500 |
| AWS API Gateway | 全託管閘道 | 限流、authz、VTL 轉換、usage plan/API key | 帳戶層限流是 best-effort 目標、非保證 | 較貴、多一層延遲、綁 AWS |
| KrakenD | 無狀態設定編譯器（Go） | 原生多後端聚合、宣告式路由 | 無 runtime plugin、改設定要重部署 | 治理屬 Lura/LF，公司屬 Shop Circle（2025+） |
| Kong | NGINX/OpenResty 上的 plugin 宿主 | 可插拔 Lua plugin 拼裝一切 | DB 模式要顧 PostgreSQL（3.4 起無 Cassandra） | 自架運維面；DB-less 仍有狀態考量 |

## 為什麼是這四種形狀

退一步看，這四個盒子不是「同一個東西的四種品質」，而是**對「閘道層該承擔多少、由誰承擔」這個問題，四種不同的回答**。

ALB 回答「盡量少」——閘道就該是一台快而便宜的路由器，橫切關注留給別人；它的克制換來延遲與成本的下限。API Gateway 回答「全包，但給雲廠」——你不想碰運維，就把整個入口層外包出去，付溢價買「不用半夜起床」。KrakenD 回答「自架，但讓它無狀態」——閘道是一份能被編譯、能被無腦複製的純設定，用功能上的克制換部署上的極簡。Kong 回答「自架，且讓它無限可插拔」——閘道是 NGINX 上的一個外掛宿主，用運維上的複雜換能力上的開放。

勾叉表之所以騙人，是因為它把這四種回答壓進同一個「功能多寡」的尺度，於是看起來像在比強弱。但你真正在選的，從來不是「哪個功能最多」，而是「在我的流量、我的雲、我的團隊待命能力下，我要把入口層這個必經點的責任，放在哪一邊」。功能能補、能加 plugin、能搭 WAF；但「它是什麼、誰扛它」這件事，在選型那一刻就定下來了，之後很難改。

下次有人遞給你一張閘道比較表、要你勾出「最強」的那個，你會知道該先把表翻過來，問一個它沒有欄位的問題：這個請求進來，我到底需要在入口發生什麼——以及，它出事的那個半夜，我希望面對的是 AWS 的 support case，還是一台我自己的 PostgreSQL。

## 延伸閱讀

- AWS, "Throttle requests to your REST APIs"（帳戶層 token bucket 限流、best-effort 目標的官方說明）: https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-request-throttling.html
- AWS, "Choosing between REST APIs and HTTP APIs"（兩種 API Gateway 的功能與取捨）: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-vs-rest.html
- AWS, "Authenticate users using an Application Load Balancer"（ALB 的 OIDC/Cognito 認證、X-AMZN-OIDC-* header、11KB claim 上限）: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-authenticate-users.html
- KrakenD, "Open Source"（Lura Project 與 Linux Foundation 治理）: https://www.krakend.io/open-source/
- Linux Foundation, "Open Source API Gateway KrakenD Becomes Linux Foundation Project"（2021 捐贈 framework 為 Lura）: https://www.linuxfoundation.org/press/press-release/open-source-api-gateway-krakend-becomes-linux-foundation-project
- Kong, "Why We're Deprecating Cassandra Support"（3.4 起 PostgreSQL 為唯一支援資料庫）: https://konghq.com/blog/product-releases/cassandra-support-deprecated
- Kong Gateway 官方文件（NGINX/OpenResty/Lua plugin 架構、DB-less 模式）: https://docs.konghq.com/gateway/
