# 附錄 A — 名詞速查表

> 這張表是把你履歷上那一排名詞，逐一翻成「真面目」的索引。每一列三欄：**名詞**、**一句話真面目（含與你舊記憶的落差）**、**深掘章**。它只收書裡實際挖過的名詞，不收沒出現的；每條的「真面目」都對應某一章的機制級拆解，想看完整推演就翻那一章。
>
> 用法：面試前、或你又對某個熟悉名詞「憑記憶」答出一個版本／預設值時，回來掃這張表——確認你講的是「查證過的」還是「2021 年記得的」。時效性事實標「（2026-06）」，並以 `_meta/landscape-2026-06.md` 為錨。
>
> 表分九類：資料庫／交易、即時通訊、訊息與佇列、執行時與並發、雲端原語、身分與存取、快取、觀測、時間與失敗。最後另立一張**老化事實表**——這是本書的招牌，把「你當年記的 X、現在是 Y、何時變的」攤開講。**那些事實你當年多半沒記錯，是世界後來變了**，所以年份比結論更重要。

---

## 一、資料庫、交易與一致性

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| 行鎖 / 意向鎖 | 鎖是兩層協議；交易**持有鎖的時間，就是別人等待的時間**——RDS CPU 被尖峰推高，常常不是算力不夠，是鎖等待＋重複掃描。 | ch03 |
| 交易拆解 | 拆短交易能降鎖競爭，但你那一刀**切掉的是原子性**：能拆的是彼此獨立的步驟，不能拆的是「要嘛全成、要嘛全不成」的約束。 | ch03 / ch11 |
| 批次化 | N 次往返變 1 次，省的是**往返＋鎖持有時間雙重收益**；但批次太大會反咬——交易變長、鎖範圍擴大。 | ch03 |
| gap lock / next-key lock | InnoDB 的 Repeatable Read 下，鎖不只鎖既有的列，還鎖「列前方的間隙」（record＋前方 gap），所以**連「插入」都會被卡**——這不是你印象中「只鎖到的那幾行」。 | ch03 / ch11 |
| 隔離級別（isolation level） | 四級各防一種異常（dirty / non-repeatable / phantom）；重點是**兩大資料庫的預設不一樣**：PostgreSQL 是 Read Committed、MySQL/InnoDB 是 Repeatable Read。 | ch03 / ch11 |
| Repeatable Read（PG vs MySQL） | 同名不同物：PG 的 RR 其實是 **Snapshot Isolation、不上鎖、不防 write skew**；MySQL 的 RR 是 **locking＋MVCC 混合、用 next-key lock 防 phantom**。把兩者當同一種東西是最常見的坑。 | ch11 |
| write skew | 兩個交易各自在自己的快照下都合法，**合起來卻違反約束**——snapshot isolation 結構上擋不住它，要真擋只能升到 Serializable。 | ch11 |
| Serializable / SSI | PG 用 Serializable Snapshot Isolation 追讀寫相依、偵測危險結構就中止交易；代價是**你的應用必須準備 retry**，它比其他級別貴。 | ch11 |
| MVCC | 「讀不擋寫、寫不擋讀」靠的是留多版本、不覆寫舊資料；代價是**舊版本要有人清，長交易會讓它清不掉而膨脹**。 | ch11 |
| deadlock 偵測 | 不是靠你避免，是資料庫**在等待圖裡找環、挑一個犧牲者回滾**；所以「同樣的查詢、不同的鎖獲取順序」差很多。 | ch03 / ch11 |
| read replica / 複製延遲 | 非同步複製＝**主庫不等 replica**；剛寫完主庫立刻去 replica 讀，可能讀不到自己剛寫的——**讀己之寫（read-your-writes）會破裂**。「把讀全導去 replica」會悄悄打破這個假設。 | ch11 |
| 最終一致（eventual consistency） | 沒有分散式交易時的預設形狀：若無新更新，副本**最終**收斂，但中間態可見（公會發了獎、背包還沒到）。它不是 bug，是你用一致性換可用與延遲的選擇。 | ch04 / ch11 |
| CAP / PACELC | CAP **Brewer 提猜想（2000）、Gilbert-Lynch 證明（2002）**，是兩組人別混；PACELC（**Abadi，2010 部落格、2012 論文**）補上 CAP 的盲點：**就算網路正常，一致與延遲也得二選一**。 | ch02 / ch11 |

## 二、即時通訊（WebSocket / WebRTC）

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| WebSocket | RFC 6455 定義的全雙工長連線；關鍵是**連線狀態綁死在某一台機器**，所以橫向擴展要 sticky session（session affinity）＋ pub/sub backplane——RFC 本身不管擴展，那是部署慣例。 | ch07 / ch02 |
| Redis Pub/Sub | **不是訊息佇列**：fire-and-forget、at-most-once、**完全無持久化**，訊息只送給「發布當下正連線」的訂閱者，離線者永久錯過、無重送、無痕跡。能做即時通知，**不能**做保證送達。 | ch07 / ch01 / ch17 |
| Redis Streams | Pub/Sub 的反面：持久 append-only log、consumer group、`XACK` 達 at-least-once、未確認的留在 Pending Entries List 可重讀。要「離線重連後收得到」走這條，不是 Pub/Sub。 | ch07 / ch17 |
| 多裝置同步 / 離線補發 | Pub/Sub 只管「在線即時」那一段；同一用戶多端、已讀狀態、離線補發**必須另走一條路**（拉取 / Streams / DB）——這是一致性問題，不是扇出問題。 | ch07 / ch11 |
| WebRTC | **不是一個協定，是一套**：媒體（SRTP）、傳輸（ICE/DTLS）、信令（規格刻意不定、你自己挑）三塊分開。標準自 2021 W3C Recommendation 起持續有效（2025-03 amended）。 | ch08 |
| 信令（signaling） | WebRTC 規格**刻意留白**——offer/answer（SDP）怎麼交換是你的事；LetsTalk 用 Socket.io 傳 SDP。所以「信令要自己做」不是疏漏，是設計。 | ch08 |
| ICE / STUN / TURN | ICE 是 NAT 穿透的整體框架；STUN 幫你問「我從外面看起來是什麼位址」；**symmetric NAT 下 STUN 探到的映射對真正的對端不適用 → 退回 TURN relay**（媒體繞中繼，成本與延遲都上升）。RFC：STUN 8489、TURN 8656、ICE 8445（舊編號 5389/5766/5245 已被取代）。 | ch08 |
| SFU / MCU / mesh | 群組通話為什麼非要伺服器：mesh＝N² 條流不可擴展、MCU＝伺服器混流但 CPU 貴、**SFU＝只轉發不轉碼**。Jitsi Videobridge（JVB）是 **SFU**。 | ch08 |
| FCM 缺口 | 自建 WebSocket 通知是為了補 **FCM 在中國等市場不可用**的缺口；自建相對於 FCM 放棄了系統級喚醒、省電、平台級離線佇列——這是取捨不是純技術勝利。 | ch07 |

## 三、訊息、佇列與交付語意

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| at-most-once / at-least-once / exactly-once | 交付保證「不掉」和「不重」**只能挑一個**（ack 可能丟，送方分不清沒到還是 ack 丟了）。所謂 **exactly-once *交付* 是幻覺**；你能買到的最好是「at-least-once＋冪等去重」拼出的 exactly-once *處理*。 | ch02 / ch10 |
| SQS Standard | **at-least-once、可能重複、best-effort 排序**——「會重」是規格保證會發生的事，不是 bug。AWS 官方明文要你把 consumer 設計成冪等。 | ch04 / ch10 / ch18 |
| SQS FIFO | exactly-once *processing*＋嚴格排序，靠一個**只有 5 分鐘的去重窗口**撐起來，且有吞吐上限。它不是物理上送一次，是「送很多次、5 分鐘內幫你去重」。 | ch10 / ch18 |
| visibility timeout | consumer 取走訊息後的「隱身期」；**到期未刪除就重投**——這正是「同一筆被處理多次」的主要來源之一（另一個是 consumer 重啟）。 | ch04 / ch18 |
| DLQ（死信佇列） | 重試到上限仍失敗的訊息的去處；它讓「毒訊息」不會無限重投卡住佇列，是你該設對的旋鈕之一。 | ch18 |
| 冪等鍵（idempotency key） | 把「至少一次」收斂成「效果上剛好一次」的安全帶；正解是**用唯一約束讓「宣告我做了這筆」成為原子操作**（如 `INSERT ... ON CONFLICT DO NOTHING`），不是 check-then-act（有 race window）。去重窗口有限，鍵不能永遠記著。 | ch04 / ch10 |
| 跨服務最終一致（補償 / 重試 / 對帳） | 沒有分散式交易時，四服務（guild/player/inventory/mail）靠重試把「部分失敗」變「重來一次」、補償「反做」、對帳兜底——三層都會漏，所以三層都要。 | ch04 / ch11 |
| SNS | 扇出（fan-out）是本職；**推（push）**對比 SQS 的**拉（pull）**。招牌模式是 SNS → 多個 SQS。SNS FIFO 存在但不能直接投給 email/SMS/Lambda，須先經 SQS。 | ch18 |
| K8s CronJob | **不保證 exactly-once**——官方明說「某些情況下 job 可能被建立兩次、或一次都不建立」，所以 job 必須冪等。漏跑/重疊受 `concurrencyPolicy`、`startingDeadlineSeconds` 影響。 | ch04 / ch13 |
| Bull / BullMQ | delayed job 靠 **Redis sorted set（score＝執行時間）＋ worker 輪詢到期**實作，所以重啟存活、不佔行程記憶體。**Bull 已進維護模式，BullMQ 是現役後繼者**（見老化事實表）。 | ch09 / ch12 |

## 四、執行時與並發（Node / event loop）

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| 單執行緒 / event loop | Node 是**單執行緒並發（交錯不是同時）**——一個同步重運算或沒 await 的大迴圈，會讓**所有**並發請求一起變慢，這才是「CPU 瓶頸」的真身。 | ch05 / ch12 |
| libuv 相位 | event loop 不是一個迴圈是一圈相位：**timers → pending → idle/prepare → poll → check → close**；setTimeout 只在走到 timers 相位才觸發，所以**本就不精確**。 | ch12 / ch05 |
| microtask（nextTick / Promise） | 在每個相位之間／每個 macrotask 之後排空，**先 `process.nextTick` 再 Promise**；把 nextTick 當飯吃會**餓死 I/O**。 | ch12 |
| thread pool（UV_THREADPOOL_SIZE） | 預設 **4**，給 fs、dns（`getaddrinfo`）、async crypto、zlib——**但 network I/O 不走 pool**，它走 OS 的 epoll/kqueue/IOCP，在 loop 自己那條執行緒上完成。不是「所有東西都在主執行緒」也不是「所有東西都用 pool」。 | ch12 / ch05 |
| 記憶體洩漏（Node 典型） | 不是神祕的；典型四源：閉包持有、**event listener 沒移除**、快取無上限、全域 Map 只增不減。在 3,200 並發下，沒移除的 listener 會線性長。 | ch05 |
| 負載測試（開放 vs 封閉模型） | 固定速率壓測會**低估真實尖峰**：封閉模型（等回應才送下一個）會被你的系統自己節流，掩蓋過載；開放模型（固定到達率）才逼近真實流量、會暴露「協調遺漏」。 | ch05 |
| flame graph | 自上而下找「寬條」＝最花時間的呼叫；它告訴你 CPU 時間花在哪，不是告訴你為什麼慢。 | ch05 |

## 五、雲端原語（AWS / 閘道）

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| Lambda | 事件驅動、**每次呼叫都是一張白紙（無狀態是前提）**；最大 timeout 900s（15 分鐘）、預設併發 1,000/region。長連線（WebSocket）或跨呼叫本地狀態用 Lambda 是逆風飛行。 | ch18 |
| 冷啟動 / SnapStart / provisioned concurrency | 拿掉長駐換來冷啟動；SnapStart 用快照去除約 70–90% init latency，**但不支援 Node.js**（見老化事實表）——Node 降冷啟動只能靠 provisioned concurrency 或把初始化做輕。 | ch18 |
| ALB | L7 負載均衡，**不看你 request 裡寫什麼**；做 host/path/header 路由，但不做 per-request 轉換、原生限流（要搭 WAF）。純 L7 路由到容器/EC2 且不需 per-request auth/transform 時用它，成本與延遲都低。 | ch18 |
| API Gateway（HTTP vs REST API） | per-request 的治理層：限流、auth（JWT / Lambda authorizer / IAM）、轉換、usage plans。**HTTP API 較新、約便宜 70%、延遲低但功能少**；要 VTL transform / usage plans / API keys 才用 REST API。 | ch18 |
| KrakenD | Go 寫的**無狀態、宣告式** API Gateway，無 runtime DB，招牌是 **native API aggregation（合併多後端回應）**；對照 Kong（NGINX/OpenResty＋Lua plugin、控制面有 DB）。治理歸屬易講錯（見老化事實表）。 | ch18 |

## 六、身分與存取（JWT / OAuth2 / RBAC）

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| OAuth2 | **是授權框架，不是登入**——它回答「這個 app 能對這些資源做什麼」，不回答「使用者是誰」。把 access token 當「使用者是誰」的證明用，是 token substitution 攻擊的土壤。 | ch16 |
| OIDC（OpenID Connect） | 真正做**登入（認證）**的是它：疊在 OAuth2 上的身分層，多發一張 **ID token**（JWT）裝「你是誰」。你當年叫的「OAuth 登入」，其實是 OIDC 在登入、OAuth 在授權。 | ch16 |
| JWT | stateless / self-contained——有效性只看簽章對不對、過期沒，**驗證不查資料庫**。**預設只簽不加密（JWS），payload 是公開可讀的**，別把祕密放進去。 | ch01 / ch16 |
| 無狀態撤銷困境 | JWT 一簽出去**過期前都有效**，所以「登出 / 封禁」很難即時生效（access token 典型 15–60 分鐘窗口）。要即時撤銷得加黑名單（denylist）每次查——但那一查就把「不查資料庫」的賣點還回去了。 | ch01 / ch16 |
| access token vs refresh token | 兩張票兩種職責：access **短命、無狀態高效驗證**；refresh **長命、可撤銷可輪替**。這個拆分不是慣例，是被「JWT 難撤銷」逼出來的設計。 | ch16 |
| PKCE | 一次性的 code_verifier/code_challenge，把「授權碼被攔截後拿去換 token」堵死；OAuth 2.1 方向是**所有**用 authorization code 的 client（含有後端的）都要搭。 | ch16 |
| RBAC vs ABAC | RBAC＝role/permission 模型（你做過的那種 `role` 欄位＋middleware）；ABAC＝按屬性即時判斷。**把所有權限塞進 JWT** 會在「權限變了但 token 還沒過期」時反咬你。 | ch16 |
| token introspection（RFC 7662） | opaque / 可撤銷 token 的做法：resource server 向 authorization server **即時查 active 狀態**——用即時性換掉本地自驗的效率，正是無狀態的反面。 | ch16 |
| HS256 vs RS256 | 對稱（HS256，共享一把密鑰）vs 非對稱（RS256，私鑰簽、公鑰驗）；**多服務驗 token 時 RS256 只需分發公鑰**，HS256 把同一把密鑰散到每個服務是金鑰管理的負擔。 | ch16 |

## 七、快取與 Redis 內部

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| Redis 單執行緒 | **指令執行永遠單執行緒**（原子、不用鎖）；Redis 6+ 的 threaded I/O 只卸載網路讀寫、**不平行化指令**。所以**一個慢命令（`KEYS *`、大 `SORT`）阻塞所有人**。 | ch17 |
| RDB vs AOF | RDB＝週期性快照（crash 可能丟「上次快照之後」的全部）；AOF＝指令日誌（fsync everysec，crash 最多丟約 1 秒）。**「當快取」和「當資料庫」要不同設定**——BullMQ 這種用 Redis 存 job 的，官方建議開 AOF。 | ch17 / ch09 |
| eviction（驅逐策略） | key 滿了 Redis 丟誰：`noeviction`（**預設**）、allkeys-lru/lfu 等。「快取就是會掉」要當成設計前提，不是意外。 | ch17 |
| 快取雪崩 / 穿透 / 擊穿 | 三種失效災難：雪崩＝大量 key 同時過期、穿透＝查不存在的 key 一路打到 DB、擊穿＝熱 key 過期瞬間並發回源。防禦是 TTL 抖動 / 空值快取 / 鎖或預熱。 | ch17 |
| 多層 cache / graceful degradation | 多層降級（記憶體 → S3 → local）的關鍵不是「有幾層」，是**每層失效時往哪退、退化有沒有被觀測到**——悄悄降級＝盲區。 | ch17 / ch20 |
| 快取與源不一致 | 快取與 DB 遲早不同步（這是 ch11 一致性在快取層的化身）；問題不是「會不會」，是「在你哪個系統悄悄發生、你發不發現得到」。 | ch17 / ch11 |

## 八、觀測性

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| metric / log / trace 三本柱 | 同一件事的三種視角：metric 便宜可聚合但**低基數**、log 高細節但貴且易遺漏、trace 跨服務因果但要全鏈埋點。問題決定該用哪個，不是三選一全上。 | ch06 / ch15 |
| 從 log 反推 metric | 常見但有陷阱的一條路（FluentBit + Lua 就是）：取樣與遺漏（log 掉一行 metric 就少一個樣本）、**百分位數不能合併**（不能把各機 p95 平均成總 p95）、時間視窗對齊。 | ch06 / ch15 |
| FluentBit pipeline（Lua filter） | input → parser → filter（Lua）→ buffer → output（S3）；用 Lua filter 是為了**在邊緣就地轉換/聚合，不把原始 log 全送下游**。buffer 滿了要面對背壓（丟還是擋）。 | ch06 |
| cardinality（基數）爆炸 | per-user / per-endpoint 維度會讓時間序列數量爆掉、metric 系統成本失控——**高基數對 metric 是毒藥，卻是 observability 的全部意義**，這個張力是觀測設計的核心。 | ch06 / ch15 |
| p99 / p999（尾延遲） | 看尾不看平均：平均被大量快請求拉低、掩蓋少數慢請求；使用者體感的是尾巴。（尾延遲的數學在《等待的數學》。） | ch15 |
| SLI / SLO / error budget | 把「夠好」變成一個數字：SLI 是量到的指標、SLO 是你承諾的目標、error budget 是你允許壞掉的額度。告警要報症狀不報原因（「CPU 高」是壞告警）。 | ch15 |

## 九、時間、持久化與失敗

| 名詞 | 一句話真面目（含與舊記憶的落差） | 深掘章 |
|---|---|---|
| 牆鐘 vs 單調鐘 | 你電腦裡有兩個時鐘：牆鐘（wall clock）**會被 NTP 往回校正、會往回跳**；單調鐘（monotonic）只增不減。**量延遲、量逾時一定用單調鐘**，用牆鐘可能算出負延遲的荒謬結果。 | ch13 |
| 排程時間語意 | 「該在 T 執行」是一句滿是坑的話：漏跑、重疊、時區、補跑——CronJob 的 `startingDeadlineSeconds` 與 delayed job 補跑是同一類問題。 | ch13 / ch09 / ch04 |
| 持久化是主動的 / fsync | 記憶體裡的東西（setTimeout、in-flight 訊息、未 flush 的 buffer）**重啟即蒸發，而且沒有錯誤日誌**；要持久必須主動寫外部儲存並付 fsync 的代價。 | ch13 / ch02 |
| 失敗模型（crash-stop / 拜占庭） | crash-stop＝壞了就停（多數系統的假設）；拜占庭＝壞了還亂講話。**逾時是分散式系統唯一的失敗偵測手段，而它分不清「慢」和「死」**——太短誤殺、太長卡死。 | ch13 |
| 背壓（backpressure） | 下游慢了，把壓力往上游傳的機制（有界佇列 / 阻塞 / 丟棄三選一）；Node stream 的 `highWaterMark` 就是它的具體化。**「無界佇列」是最危險的設計**——延遲無限長、記憶體爆。 | ch14 |
| token bucket vs leaky bucket | token bucket **容忍突發**（保護平均速率）、leaky bucket **整形成平滑**（保護瞬時速率）；選哪個看你保護的是平均還是瞬時。 | ch14 |
| load shedding | 過載時**主動丟低優先請求保住核心**；加大 buffer 救不了過載（只是把延遲拖更長），這是反直覺但關鍵的一點。 | ch14 |
| circuit breaker | 三態（closed / open / half-open）強迫系統離開壞平衡：偵測到下游一直失敗就**直接快速失敗**，不再把請求往火坑送。 | ch14 |
| retry storm / metastable failure | 重試會**放大流量**，小尖峰能滾成雪崩；更陰的是 metastable failure——**移除觸發因素後系統仍卡在壞平衡回不來**。所以退避＋jitter 兩個都不能少。 | ch14 |

---

## 老化事實表（當年 vs 2026）

> 本書的招牌。下面每一條，**你當年多半沒記錯**——是世界在你離開後變了。年份比結論更重要：它區分「你一直記錯」和「你記得對、後來被偷偷改掉」。面試前若要引用版本／狀態／授權，回來核對這張表，並以 landscape 為錨。

| 名詞 | 你當年記的（2019–2024） | 2026-06 的實際狀況 | 何時變的 | 深掘章 |
|---|---|---|---|---|
| Twilio Programmable Video | 「要 EOL 了，所以選 Jitsi 才對」 | **仍是現役產品**——2024-03 確曾宣布停運，但已公開撤回；「因為 Twilio 要關」這個選型理由**已不成立**，要改用純成本／自架掌控／開源授權論述 | 2024-10-21 官方撤回 | ch08 |
| Bull（job queue） | 用 Bull 做 delayed job、它是主線 | **Bull 已進維護模式（只修 bug）**，**BullMQ**（TypeScript 重寫、Taskforce.sh 維護）是現役後繼者；新專案用 BullMQ。注意：**別說「BullMQ 屬於 Redis」**——它只是以 Redis 為儲存後端 | 約 2019 起 BullMQ 接棒 | ch09 |
| Redis 授權 | BSD 授權的開源軟體 | **三授權（RSALv2 / SSPLv1 / AGPLv3，三選一）**，只有 AGPLv3 是 OSI 認可開源；社群 fork 出 **Valkey**（BSD-3、Linux Foundation），主要 distro 與雲端已普遍轉向——你今天在 AWS 開「Redis 相容」託管快取，預設給的很可能是 Valkey | 2024-03 改授權、2024 起 Valkey fork、2025-05 Redis 8 加 AGPLv3 | ch17 |
| Redis 版本 | 大概停在 7.x | 已是 **8.x**（小版本高頻變動，講「已 8.x」即可，別綁死單一版本號） | Redis 8 GA（2025-05） | ch17 |
| Node.js active LTS | 大概是 18 / 20 | **Node 24（codename "Krypton"）**；Node 22（"Jod"）已降為 maintenance LTS、26 是 current | Node 24 轉 active LTS（2025-10-28） | ch12 / ch05 |
| Clinic.js | 趁手的 Node 效能診斷工具 | **已停止積極維護**（官方 README 自承「not being actively maintained」，可能與新版 Node 不相容）；四工具（Doctor/Flame/Bubbleprof/Heap Profiler）定位仍在，但別當現役主力 | 最後正式 release v13.0.0（2023-06-28） | ch05 |
| k6 | 叫「k6」、印象是 Apache/MIT 授權 | 正式名 **Grafana k6**、**授權是 AGPLv3**（包進對外服務有傳染性條款，公司情境會被法務問到） | Grafana 2021 收購、系列產品改 AGPLv3 | ch05 |
| OAuth 2.1 | 「出了、把這些標準化了」 | **仍是 IETF Internet-Draft（draft-15，2026-03 發布），尚未成為 RFC**；別寫成「2.1 標準／RFC」。方向明確：PKCE 對所有 auth code client 強制、移除 implicit/ROPC、redirect URI 精確比對 | 仍在 draft 階段 | ch16 |
| SQS 單則訊息上限 | 256 KB | **1 MiB（1,048,576 bytes）**——你當年記的 256 KB 是對的，是世界後來變的；但大訊息仍是反模式，超大物件用 Extended Client Library 放 S3（最大 2 GB） | 2025-08-04 | ch18 |
| Lambda 非同步 payload 上限 | 256 KB | **1 MB**（同步呼叫仍是 6 MB）；又一個「曾經對、2025 下半年才變」的數字，別跟 SQS 的 1 MiB 搞混（一個是訊息上限、一個是 invoke payload） | 2025-10-24 | ch18 |
| Lambda SnapStart | 印象裡「只有 Java」 | Java / **Python（3.12+）/ .NET（8+）皆已 GA**，但 **Node.js 至今不支援**——Node 降冷啟動只能靠 provisioned concurrency 或把初始化做輕 | Python/.NET 2024-11 GA | ch18 |
| KrakenD 治理歸屬 | 一家獨立開源公司 | **公司被 Shop Circle 收購**；且捐給基金會的是其核心 framework「**Lura**」、給的是 **Linux Foundation（不是 CNCF）**——三點（哪個被捐、捐給誰、公司被誰收）任一說錯就露餡 | Lura 捐 LF（2021-05）、公司被收購（2025-09） | ch18 |
| Fluent Bit 版本 | v3.x / v4.x | 已達 **v5.0 系列**（v4.2 維護至 2026-06-30）；**Lua filter 確定未棄用**、仍受支援 | v5.0 系列（2026） | ch06 |
| Prisma query engine | 用 Rust query engine | **Prisma 7 起改走 TypeScript/WASM query compiler（去 Rust）為預設**（查詢更快、bundle 大幅縮小） | Prisma 7（2025-11-19） | （書中未深掘，附錄補記） |

---

> 三件帶走的事：①「真面目」這欄的價值在落差，不在定義——你會用早就會了，這本書補的是「它在你看不見的地方怎麼背叛你」。②老化事實表的每一條，先問「這是我查證過的，還是 2021 年記得的？」③要看完整推演就翻深掘章；全系統 × 五軸的總表在附錄 B，延伸閱讀總地圖在附錄 C。
