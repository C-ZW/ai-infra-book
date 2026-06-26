# DNS 與服務發現

凌晨三點，`order-service` 的某個實例因為節點記憶體壓力被殺掉，編排器在另一台機器上拉起一個新的，給了它一個全新的 IP。這件事本身完全正常——容器世界裡實例朝生暮死是常態，不是事故。真正的問題在另一頭：此刻 `payment-service` 手上還握著那個**已經不存在的 IP**，而且接下來好幾分鐘，它每一次想呼叫訂單服務，都會把封包送向一台空無一物的位址，等到 TCP 逾時才失敗。下游沒掛，網路沒斷，DNS 也「正確」地回答了——它只是回答了一個五分鐘前才正確的答案。

這就是服務發現要解的那個看似平凡、實則棘手的問題：**在一個實例會自動擴縮、漂移、重啟的環境裡，呼叫端怎麼知道某個服務「現在」跑在哪些位址上。** 名字到位址的對應，本來是電腦網路裡最古老、最被解決過的問題——DNS 在 1980 年代就把它幹完了。麻煩的是，DNS 當年解的是一個**幾乎不變**的對應（`mit.edu` 的 IP 一年也未必換一次），而我們現在要它去追一個**每分鐘都在變**的對應。一個為「穩定」最佳化的機制，被推去處理「劇烈變動」，它的每一個設計選擇都會在這個新壓力下露出裂縫。這一章就是要看清那些裂縫長在哪、為什麼長在那裡，以及人們是怎麼一層層補上去的。

## 把問題拆開：發現其實是三件事

要看懂為什麼 DNS 在這裡會吃力，得先把「服務發現」這個籠統的詞拆成三個其實互相獨立的動作：

第一件是**註冊表（registry）**——誰是「`order-service` 有哪些實例」這個問題的真相來源。某個地方必須有一份權威名單，記著當下活著的實例與它們的位址。

第二件是**健康判定**——名單上的實例，哪些是真的還能服務的？一個剛被 OOM 殺掉的實例，在它從名單上消失之前，是一筆**有毒的資料**：位址還在、人已經死了。

第三件是**解析與分配**——呼叫端拿到一份健康名單後，怎麼從裡面挑一台來連。

這三件事可以分得很開，也可以揉成一團，而 DNS 的根本侷限，正是它把三件事**揉成一團、而且每一件都做得不夠好**。DNS 的「註冊表」是 zone file 或它背後的權威伺服器，更新要走一套為「慢」設計的傳播流程；DNS 對「健康」幾乎沒有概念——它回給你一筆 A 記錄，不代表那台機器活著，只代表「上次有人把這個對應寫進去」；至於「分配」，傳統 DNS 能做的只有把多筆 A 記錄輪流排在前頭（round-robin），一種既看不見負載、也看不見健康的盲目輪轉。把這三件事分開來看，現代服務發現的所有演化——Consul、Kubernetes 的 endpoints、service mesh 的端點推送——本質上都是在做同一件事：**把這三件被 DNS 揉在一起的事重新拆開，各自做對。**

## DNS 為什麼追不上：快取是特性，不是 bug

DNS 能擴展到全球規模、扛住每秒天文數字的查詢量，靠的就是一件事：**到處快取**。你的應用程式、它所在的作業系統、語言執行環境、區域 resolver、ISP 的遞迴伺服器——每一層都會把解析結果存下來,在一段時間內重複使用,不再回去問權威伺服器。這個分層快取是 DNS 可擴展性的全部祕密。

而控制「一筆結果可以被快取多久」的,就是每筆記錄上掛著的 **TTL（time-to-live）**。權威伺服器說「這筆 A 記錄 TTL=300」,意思是「你可以放心用五分鐘,五分鐘內別來煩我」。對一個一年才換一次 IP 的網站,這是天大的好事——一筆查詢的結果可以服務幾百萬次後續請求。

但把同一個機制套到「實例每分鐘在變」的環境,快取就從祝福變成詛咒。回到開場那一幕,具體手算一次最壞情況。假設 `order-service` 的 A 記錄 TTL 設成 300 秒,某個實例在 `t=0` 當機。最糟的情形是:有個 resolver 在 `t=0` 的前一瞬間(`t=-1` 秒)剛好查過、把這筆記錄連同那個死 IP 快取了下來。那麼這個死 IP 會在這個 resolver 的快取裡**繼續存活到 `t=299` 秒**——將近整整五分鐘。在這五分鐘裡,任何向這個 resolver 要位址、然後新建連線的 client,都可能拿到那個死 IP,把請求送進黑洞,等 TCP connect 逾時才失敗(送向一個封包被默默丟棄的死位址時,Linux 核心預設的 SYN 重送會拖到約兩分鐘才放棄,多數應用會自設較短的 connect timeout 把它壓到數十秒)。一個本該秒級恢復的故障,被 DNS 的快取硬生生拖成了分鐘級。

天真的反應是:那就把 TTL 砍短嘛,設成 15 秒,失效窗口不就從五分鐘縮到十五秒?這個方向對,但它撞上兩堵牆。

第一堵牆是**成本**:TTL 砍到 15 秒,等於把回源查詢量放大了二十倍。對一個被海量 client 依賴的熱門服務,這可能直接把你的 DNS 基礎設施打趴——而且還會引出後面要談的驚群問題。

第二堵牆更隱蔽、也更致命:**很多 client 根本不甩你的 TTL。** TTL 是權威端的「建議」,但快取發生在無數個你管不到的層裡,每一層都可能有自己的脾氣。最經典的例子是 JVM 的 DNS 快取行為:它由 `networkaddress.cache.ttl` 控制,而這個預設值歷來分兩支——**裝了 security manager 時是 `-1`,也就是「永久快取」**:一個 JVM 行程查到一次 DNS 結果後,**到行程死掉為止都不會再查第二次**,你設的 15 秒 TTL 對它形同空氣;**沒裝 security manager 時,OpenJDK 的實作預設約 30 秒**。永久快取那一支不是哪個函式庫的 bug,而是當年為了**防 DNS 欺騙**刻意做的安全選擇:既然解析結果可能被攻擊者污染,那就少查幾次、減少被污染的窗口。要留意的是時點:security manager 自 JDK 17(2021,JEP 411)起就被標記為棄用,並已在 **JDK 24(2025,JEP 486)被永久停用**——現代 JVM 行程已無法再裝上 security manager,因此**絕大多數落在「約 30 秒」那一支,而非永久快取**(2026-06)。但即使是 30 秒,故事的教訓不變:這個窗口仍握在你管不到的快取手裡,而一個為「安全」做的決定,在「需要快速故障切換」的場景裡照樣可能變成陷阱。這就是為什麼有經驗的人會說:**永遠不要把 DNS TTL 當成可靠的故障切換手段。** TTL 給人一種「失效窗口在我掌控中」的錯覺,但這個窗口其實握在一堆看不見、也改不動的快取手裡。

還有一個常被忽略的快取維度:**負面快取(negative caching)**。當你查一個不存在的名字,權威伺服器回 `NXDOMAIN`,這個「不存在」的答案**一樣會被快取**(RFC 2308),快取多久由該 zone 的 SOA 記錄裡 `MINIMUM` 欄位與 SOA 本身 TTL 取較小值決定。這帶來一個極隱蔽的故障:如果某個服務名在實例**還沒註冊好**時就被人查了一次,得到 `NXDOMAIN`,那麼即使實例下一秒就上線,這個「查無此名」的答案也會在快取裡賴著、把後來的 client 擋在門外,直到負面快取自己過期。「我明明已經部署上去了,為什麼有些 client 還是說找不到」的鬼故事,根源常在這裡。

## SRV 記錄:讓 DNS 多回答一點

純 A 記錄有個結構性的窮:它只回答「名字 → 一組 IP」,連 port 都帶不了。如果你的服務不跑在約定俗成的固定 port 上(在動態 port 分配的環境裡很常見),光有 IP 還不夠。於是有了 **SRV 記錄(RFC 2782,記錄型別碼 33)**,它把 DNS 從「名字解析器」往「服務目錄」推了一步。

一筆 SRV 記錄長這樣:

```
_service._proto.name  TTL  IN  SRV  priority  weight  port  target
```

四個欄位各有用途,而且它們悄悄把前面說的「分配」那件事的一部分塞回了 DNS 裡:

- **priority(優先級)**:數字越小越優先。client 應該先用 priority 最低的那批,連不上才退到次低的。這天然支援了主備切換——主集群 priority=10、備援集群 priority=20,主的全掛了才會打到備的。
- **weight(權重)**:**同一個 priority** 裡才比較,用來在等優先的目標間按比例分流。weight 大的應該被以更高機率選中,範圍 0–65535。
- **port**:這正是 A 記錄給不了的。
- **target**:提供服務的主機名(還要再解析一次才拿到 IP)。

SRV 比 A 記錄表達力強得多,Consul、早期的 Kubernetes、SIP/XMPP 這些協定都靠它。但它有個現實的軟肋:**普通的 HTTP client 與瀏覽器根本不查 SRV**——`getaddrinfo()` 這條最常用的解析路徑只認 A/AAAA。所以 SRV 在「能掌控 client 解析邏輯」的場景(服務間呼叫、特定協定)很有用,但你沒法靠它讓任意一個 `curl` 或瀏覽器自動享受到 priority/weight 的好處。表達力與普及度之間,SRV 卡在一個尷尬的位置。

## 三種拓樸:由誰來做負載均衡

退一步看,所有服務發現方案,差別最終落在一個問題上:**「拿到健康名單」和「從名單挑一台」這兩件事,分別在哪裡發生。** 這劃出三種拓樸,各有各的甜區。

第一種是 **client-side discovery(客戶端發現)**。client 直接去問註冊表(如 Consul)要一份健康實例清單,然後**自己做負載均衡**,挑一台連。好處是少一跳——沒有中間代理,client 直接連到後端;而且因為均衡邏輯在 client 手上,它可以用很聰明的演算法,比如 P2C(隨機抽兩台選負載較輕的)或追蹤延遲的 EWMA。代價是**每種語言都得有一套註冊表的 client SDK**,而且這套發現邏輯散在所有 client 裡,要升級就得動到每個服務。

第二種是 **server-side discovery(伺服器端發現)**。client 只認一個**穩定不變的虛擬位址**,背後由平台把流量轉發到某個健康實例。Kubernetes 的 `ClusterIP` 就是這種:Service 有個固定的虛擬 IP,Pod 怎麼來去都不影響這個 IP,kube-proxy 或 IPVS 在底層把連到這個 IP 的流量導向某個活著的 Pod。client 端無腦、語言無關——它甚至不知道後面有幾台、誰死誰活。代價是**多一跳**(流量要先到那個虛擬位址再被轉發),而且這個轉發層自己也得高可用。

第三種其實是第一種的進化版:**control plane 主動推送**。不再讓 client 去「拉」名單,而是由一個控制面(如 service mesh 的 xDS)把當前的健康端點清單**即時推**給每個 client 旁邊的代理(端點推送的完整機制,見〈Service mesh:把網路關注點下沉到 sidecar〉)。它兼得 client-side 的聰明均衡與近即時的更新,代價是綁上一整套 mesh 的複雜度。

這三種拓樸不是誰取代誰,而是**把均衡的智慧放在不同位置**的取捨:放 client 端最靈活但最分散,放平台端最省心但多一跳,放 control plane 最即時但最重。

## Kubernetes 是怎麼把這件事做對的

容器編排把「實例朝生暮死」推到了極致,也正因如此,它不得不把服務發現重做一遍——而它的解法,恰好是前面那「把三件事拆開」原則的乾淨示範。看清楚它的內部運作,就懂了為什麼它能把失效窗口從分鐘級壓到秒級。

關鍵在於 Kubernetes **不靠 DNS 的 TTL 來追蹤健康**。它把「註冊表」「健康」「解析」徹底拆開:

- **註冊表是 EndpointSlice**(它取代了早期的 Endpoints 物件;Endpoints API 自 Kubernetes v1.33(2025-04)起已棄用,EndpointSlice 才是現代叢集的真相來源):當你建一個 Service 並用 label selector 框住一組 Pod,一個 controller 會持續監看(watch)這些 Pod,把當下符合條件、且**通過 readiness probe** 的 Pod 的 IP,寫進一份叫 EndpointSlice 的物件。Pod 一掛、或 readiness 一變紅,controller **秒級**就把它從這份清單移除。這份清單才是真相,不是 DNS。
- **健康判定是 readiness probe**:一個 Pod 在 `/healthz` 回綠之前,根本不會被寫進 EndpointSlice。健康不是 DNS 的事後猜測,而是進入名單的**入場券**(probe 的 liveness/readiness 語意,見〈health check:liveness 與 readiness〉)。
- **解析有兩條路**:對普通的 `ClusterIP` Service,DNS 只回那個**穩定的虛擬 IP**——這個 IP 永遠不變,所以 DNS 快取再久也無所謂,反正轉發的活兒交給 kube-proxy 去做(這就是 server-side discovery)。對 **headless Service**(把 `clusterIP` 設成 `None`),DNS 則直接回**每個 Pod 的一筆 A 記錄**,讓 client 自己選(這就退回 client-side)。

這個設計的巧妙在於:**把「會變的東西」藏在 DNS 後面。** 普通 Service 暴露給 DNS 的是恆定的 ClusterIP,Pod 的生死變動全被 kube-proxy 與 EndpointSlice 吸收掉,DNS 那層的快取怎麼樣都不會把你帶到死 Pod。失效窗口因此不取決於 DNS TTL,而取決於 EndpointSlice 更新的速度——秒級。

但 Kubernetes 自己的 DNS(CoreDNS)也藏著一個值得拆開的數字陷阱。CoreDNS **kubernetes plugin 的基礎預設 TTL 是 5 秒**,但實務上 Kubernetes 叢集普遍把它配成 **30 秒**——這個選擇是為了和早年 dnsmasq 版的 kube-dns 行為對齊(2026-06)。30 秒聽起來和前面說的「秒級失效」有點矛盾?並不:對普通 Service,DNS 回的是恆定 ClusterIP,快取 30 秒完全無害;真正要秒級反應的健康變動,走的是 EndpointSlice 那條路,根本不經過 DNS TTL。把這兩條路分清楚,才不會被「DNS TTL 30 秒」誤導以為故障切換要等 30 秒。

## 一個藏在 resolv.conf 裡的稅:ndots:5

Kubernetes 的 DNS 還有一個極經典、極隱蔽的效能陷阱,值得手算一遍,因為它完美示範了「一個為方便設計的預設,怎麼在規模下變成隱形成本」。

Pod 裡的 `/etc/resolv.conf` 預設長這樣:

```
search my-namespace.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

`search` 這幾行是搜尋網域,讓你在 Pod 裡可以只寫 `order-service` 而不必寫完整的 `order-service.my-namespace.svc.cluster.local`——解析器會自動把搜尋網域一個個接上去試。這很方便。問題出在 `ndots:5` 這個選項。

`ndots` 的意思是:**一個名字裡的點數,要達到這個門檻,才會被當成「絕對名字」直接去查;沒達到,就先逐一套用搜尋網域。** 設成 5,意味著任何**少於 5 個點**的名字,都會先把那幾個搜尋網域全試一輪,試到 `NXDOMAIN` 為止,最後才把原名當絕對名字去查。

對叢集**內部**的短名字(`order-service`,0 個點),這個設計是對的——它本來就需要靠搜尋網域補全。但對**外部**域名,災難就來了。手算一次:你的 Pod 要連 `api.stripe.com`,這名字有 2 個點,小於 5,於是解析器忠實地照表操課:

```
1. api.stripe.com.my-namespace.svc.cluster.local  -> NXDOMAIN
2. api.stripe.com.svc.cluster.local               -> NXDOMAIN
3. api.stripe.com.cluster.local                    -> NXDOMAIN
4. api.stripe.com                                  -> 終於成功
```

**解析一個外部名字,放出了 4 次 DNS 查詢,前 3 次純屬浪費。** 在一個對外部 API 呼叫頻繁的服務裡,這直接把你的 DNS 查詢量乘上三到四倍,CoreDNS 的負載、每次連線前的解析延遲全跟著漲。而前 3 次的 `NXDOMAIN` 還會觸發前面講的負面快取,讓問題的形狀更複雜。這個成本完全是隱形的——功能上一切正常,只是慢、只是 DNS 流量莫名其妙地高。知道病根後,解法很直接:對主要打外部 API 的 Pod,把 `ndots` 調低(比如設成 2,讓 `api.stripe.com` 這種剛好 2 個點的名字直接被當絕對名查),或乾脆在程式裡用帶結尾點的完全限定名(FQDN,`api.stripe.com.`)繞過搜尋網域。一個藏在預設值裡的小數字,規模一上來就是實打實的稅。

## Consul:把健康判定請進 DNS

如果說 Kubernetes 是靠「把變動藏在虛擬 IP 後面」解決 DNS 的快取問題,那 Consul 走的是另一條路:**它讓 DNS 本身具備健康感知**,而且乾脆把 TTL 這個麻煩源頭直接設成零。

Consul 提供一個 DNS 介面(預設在 port 8600),你可以用標準 DNS 查詢去問 `order-service.service.consul`,而且——這是它和傳統 DNS 最本質的差別——**它只回那些當下通過健康檢查的實例**。一個實例如果 health check(HTTP、TCP、script、TTL、gRPC 各種形式)失敗,Consul 會立刻把它從 DNS 與 API 的回答裡剔除。健康判定不再是 DNS 的盲點,而是內建在每一筆回答裡。

而 Consul 怎麼知道誰健康?它底下跑的是一套 gossip 協定(SWIM 家族,實作叫 Serf):每個節點上的 agent 彼此用 gossip 隨機探測、傳播成員的生死狀態,形成一個去中心化的失敗偵測網(gossip 與 anti-entropy 的完整機制,見〈gossip 與 anti-entropy〉)。配合主動的 health check,Consul 對「誰活著」的判斷既快又不依賴單一中心。

至於 TTL 那個老問題,Consul 的處理乾脆得近乎暴力:**它的 DNS 回答預設 TTL 為零**,徹底禁止下游快取,逼每一次查詢都重新評估、拿到最新名單(2026-06)。這當然是個取捨——零 TTL 意味著每次解析都得真的打到 Consul,失去了 DNS 分層快取的省力,把負載全壓回註冊表。所以 Consul 也允許用 prepared query 之類的機制針對性地放寬 TTL,在「即時」與「省力」之間找平衡。但它的預設立場很清楚:**寧可貴一點,也不要因為快取而把死實例的位址交給 client。** 這恰好和傳統 DNS「寧可舊一點也要省力」的預設立場完全相反——同一個 TTL 旋鈕,兩種機制把它擰向了相反的方向,因為它們對「位址會不會變」的根本假設不同。

## 兩個總被混為一談的東西

把上面這些串起來,有兩組概念特別容易在腦中糊成一團,分清楚它們是真正理解這套機制的試金石。

**第一,服務發現不等於負載均衡。** 發現是「拿到一份健康的位址清單」,均衡是「從清單裡挑一台」。這是兩件事,只是常被同一個工具一起做掉,所以容易混。DNS round-robin 之所以是個糟糕的均衡器,正因為它試圖用「把多筆 A 記錄輪流排前面」一個動作同時幹這兩件事,結果兩件都做不好:它**看不見健康**(死實例照樣被輪到)、也**看不見負載**(打到一台已經過載的機器和打到一台閒置的機器,在它眼裡沒差別)。把這兩件事拆開,你才會去問對的問題:我的「清單從哪來、多久更新一次」(發現),以及我的「從清單挑一台的策略是什麼」(均衡)——後者的完整光譜,從 round-robin 到 least-connections 到 P2C,屬於負載均衡自己的主題(見〈負載均衡:L4 與 L7、演算法與健康檢查〉)。

**第二,DNS 解析本身是一個依賴,不是免費的瞬時操作。** 工程師很容易把「解析一個名字」當成一個不會失敗、不花時間的前置步驟,於是忘了給它逾時、忘了它也會排隊、也會慢、也會掛。但 DNS 伺服器本身可能過載、可能被網路問題拖慢,而當解析變慢,那些「看起來和 DNS 八竿子打不著」的呼叫會集體跟著變慢——因為它們在真正連線之前,都卡在解析這一步。更糟的是一種**驚群(thundering herd)**:大量 client 的 DNS 快取因為同一個 TTL **同時到期**,於是在同一瞬間一起回源查詢,把 DNS 伺服器瞬間打爆。這和快取雪崩是同一個形狀的問題,解法也類似——給 TTL 或重新查詢的時機加上一點隨機抖動(jitter),把同時到期的尖峰攤平(jitter 的機制,見〈重試、退避與 jitter〉)。把 DNS 當成「永遠瞬間回應、永遠不會失敗」的假設,是一個會在最忙的時候背叛你的假設。

## 為什麼是這個形狀

退到最遠處看,這一整章的張力,都源自一個錯配:**DNS 是為「對應幾乎不變」的世界設計的,而我們把它丟進了「對應每分鐘都在變」的世界。**

DNS 所有讓它偉大的設計——層層快取、TTL 授權下游放心用一段時間、權威傳播從容不迫——都建立在「位址很少變」這個假設上。一旦這個假設被推翻,同樣這些設計就變成了債:快取讓你看到過期的位址,TTL 被一堆你管不到的快取無視,而它對健康的全然無知,讓它一次次把死實例的位址若無其事地交到 client 手上。

於是現代服務發現做的所有事,本質上都是在**收回 DNS 當年為了可擴展性而做的妥協**。Kubernetes 把善變的部分藏到恆定的 ClusterIP 後面,讓 DNS 那層的快取再也咬不到真相;Consul 把 TTL 設成零、把健康檢查請進 DNS 的每一筆回答;service mesh 索性不等 client 來拉,把名單即時推下去。它們選的位置不同、複雜度不同,但都在回答同一個被 DNS 揉成一團、又各自做不好的問題:**誰是真相、誰還活著、該連哪一台。** 把這三件事重新拆開、各自做對,就是這整個領域演化的全部劇情。

下次你看到一個服務「明明已經部署好了,有些 client 卻還連到舊實例」,你會知道該往哪裡看:不是某段業務邏輯錯了,而是某一層快取——可能是某個 JVM 的永久 DNS 快取、可能是一筆還沒過期的負面快取、可能是一個被忽視的 `ndots` 稅——還活在五分鐘前的世界裡,而那個世界已經不在了。

## 延伸閱讀

- RFC 2782 — A DNS RR for specifying the location of services (DNS SRV):https://www.rfc-editor.org/rfc/rfc2782.txt
- RFC 2308 — Negative Caching of DNS Queries (DNS NCACHE):https://www.rfc-editor.org/rfc/rfc2308.html
- Kubernetes — DNS for Services and Pods:https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
- Kubernetes pods /etc/resolv.conf ndots:5 option and why it may affect your application performance(Marco Pracucci):https://pracucci.com/kubernetes-dns-resolution-ndots-options-and-why-it-may-affect-application-performances.html
- Consul — Configure Consul DNS behavior(含 TTL 與健康檢查):https://developer.hashicorp.com/consul/docs/discover/dns/configure
- AWS — Set the JVM TTL for DNS name lookups(JVM 永久快取與調整):https://docs.aws.amazon.com/sdk-for-java/latest/developer-guide/jvm-ttl-dns.html
