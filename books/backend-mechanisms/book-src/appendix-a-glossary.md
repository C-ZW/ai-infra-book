# 附錄 A · 術語表

這份術語表收錄全書出現的技術名詞，每條給一兩句白話定義，並指向把它講透的那一章「（見〈章名〉）」。定義以本書的用法為準——同一個詞在不同脈絡可能有更寬的意思，這裡只取機制層面的那一面。

按主題分為十二組，方便對照閱讀；組內大致依概念出現的先後排列。

---

## 一、判斷與推動

**鋪路（paved road / golden path）**：把「對的做法」做成阻力最小的那條路——預設模板、腳手架、CI 檢查讓人不必特別努力就走對。（見〈鋪路：讓對的做法最省力〉）

**ADR（Architecture Decision Record，架構決策紀錄）**：一份短文件，記下一個決定、當時的脈絡與被否決的選項，寫給幾年後想知道「為什麼當初這樣做」的人。（見〈把決定寫下來：RFC、設計文件與 ADR〉）

**RFC（Request for Comments）**：在動工前把提案寫成文件、廣徵意見的流程；目的是把分歧攤在設計階段而非實作之後。（見〈把決定寫下來：RFC、設計文件與 ADR〉）

**strangler（絞殺者模式）**：在舊系統外圍逐步長出新實作、把流量一塊塊接過去，直到舊系統被「絞殺」殆盡，避免一次性大爆炸式重寫。（見〈漸進式遷移與淘汰：strangler 與 expand-contract〉）

**expand-contract（擴張—收縮）**：先擴張（同時支援新舊形式）、搬完資料與流量後再收縮（移除舊形式）的兩段式變更節奏，用於無痛換掉介面或結構。（見〈漸進式遷移與淘汰：strangler 與 expand-contract〉，schema 面見〈零停機 schema 遷移：expand-contract 與 backfill〉）

**技術債（technical debt）**：為了趕快交付而刻意或不慎欠下的「將來要還的工」，債務利息是日後每次改動都更慢更危險。（見〈技術債：量化、排序、何時還〉）

**YAGNI（You Aren't Gonna Need It）**：別為「將來也許用得到」的需求現在就蓋抽象；過早抽象與過早最佳化都是要付利息的成本。（見〈簡單性與過度工程：YAGNI 的兩面〉）

**可逆與不可逆決策（two-way / one-way door）**：可逆決策像能來回穿過的門，錯了走回來就好，該快；不可逆決策過去就回不來，該慢、該慎。（見〈兩扇門：可逆與不可逆決策〉）

**NIH（Not Invented Here）**：傾向自建而排斥外部現成方案的偏誤，與「過度相依、把命脈交給別人」是一體兩面的取捨。（見〈自建還是採用：相依的長期成本〉）

**fail-fast（快速失敗）**：一偵測到無法繼續就立刻、明確地報錯，而非帶著壞狀態硬撐下去；錯誤處理的四條去向之一。（見〈錯誤處理哲學：fail-fast、傳播、重試還是降級〉）

**量級估算（back-of-the-envelope estimation）**：用記得住的幾個數量級常數，快速算出一個設計大概需要多少 IOPS、記憶體、頻寬，判斷可不可行。（見〈信封背面：量級估算與容量直覺〉）

---

## 二、訊息與交付

**交付語意（delivery semantics）**：訊息系統對「一則訊息會被送達幾次」的保證，分 at-most-once（至多一次）、at-least-once（至少一次）、exactly-once（恰好一次）三種。（見〈三種交付語意：at-most、at-least、exactly-once〉）

**exactly-once（恰好一次）**：理想上每則訊息只被處理一次的保證；本書的核心觀點是傳輸層做不到真正的 exactly-once，能做到的是「at-least-once 交付 ＋ 處理端去重」。（見〈三種交付語意：at-most、at-least、exactly-once〉）

**冪等（idempotent / idempotency）**：同一個操作執行一次或多次，結果都一樣；它是把「至少一次」的重複馴服成「效果上恰好一次」的關鍵。（見〈重複是常態：冪等與去重〉）

**冪等鍵（idempotency key）**：呼叫端帶上的唯一標識，讓伺服器辨認「這是同一個請求的重試」而非新請求，據此去重。（見〈重複是常態：冪等與去重〉）

**去重（deduplication）**：在處理端記住已見過的訊息標識，把重複投遞擋掉，使重複交付不變成重複效果。（見〈重複是常態：冪等與去重〉）

**訊息順序（message ordering）**：訊息被消費的先後保證；多數系統只保證同一 partition key 內有序，跨 key 不保證全域順序。（見〈訊息順序：FIFO 與 partition key〉）

**partition key（分區鍵）**：決定一則訊息落到哪個 partition 的欄位；相同 key 的訊息進同一 partition、因而彼此有序。（見〈訊息順序：FIFO 與 partition key〉）

**重試與退避（retry / backoff）**：失敗後再試一次，並在連續重試間逐漸拉長等待（通常指數成長），避免一窩蜂同時重打。（見〈重試、退避與 jitter〉）

**jitter（抖動）**：在退避時間上加入隨機擾動，把原本會對齊的重試波峰打散，避免同步化的重試風暴。（見〈重試、退避與 jitter〉）

**DLQ（Dead Letter Queue，死信佇列）**：反覆處理失敗的訊息被移到的旁路佇列，讓主流程不被毒訊息（poison message）卡住，留待人工或補償處理。（見〈死信與毒訊息：DLQ〉）

**毒訊息（poison message）**：本身格式或內容有問題、無論重試幾次都會失敗的訊息；放任不管會無限佔住消費者。（見〈死信與毒訊息：DLQ〉）

**outbox（發件匣模式）**：把「要送出的訊息」和業務資料寫進同一個資料庫交易，再由獨立程序把它轉發出去，解決「資料庫已提交、訊息沒發出」的不一致。（見〈跨服務的交付一致：outbox 與 saga〉）

**saga**：把一個跨服務的長交易拆成一串本地交易，每步配一個補償動作，失敗時逐步回滾，用最終一致取代分散式原子提交。（見〈跨服務的交付一致：outbox 與 saga〉）

**choreography 與 orchestration（編舞 / 編排）**：saga 的兩種協調風格——編舞靠各服務監聽事件自行接力，編排靠一個中央協調者下令；前者鬆耦合難追蹤，後者好觀測但有中心。（見〈跨服務的交付一致：outbox 與 saga〉）

**Webhook**：伺服器對伺服器的回呼——當事件發生，提供方主動向訂閱方註冊的 URL 發 HTTP 請求；需自帶重試、簽章與冪等。（見〈Webhooks：伺服器對伺服器的回呼〉）

**schema 演進（schema evolution）**：在不打斷既有讀寫端的前提下改變資料格式，靠向前相容與向後相容讓新舊版本並存。（見〈序列化與 schema 演進〉）

**向前 / 向後相容（forward / backward compatibility）**：向後相容＝新程式讀得懂舊資料；向前相容＝舊程式讀得懂新資料（會略過不認得的欄位）。（見〈序列化與 schema 演進〉）

**schema registry**：集中保管訊息 schema 版本、並在生產端註冊時檢查相容性的服務，防止有人推出破壞相容的格式。（見〈序列化與 schema 演進〉）

**consumer group**：一群協同消費同一個 topic 的消費者，partition 在組內分配、各自獨佔，藉此水平擴展消費能力。（見〈Kafka：log、partition 與 consumer group〉）

**fan-out（扇出）**：一則訊息被複製分發給多個訂閱者的模式，典型如 SNS 把一則發布同時推給多個 SQS 佇列。（見〈SNS：fan-out 與 SNS→SQS〉）

---

## 三、一致性與交易

**一致性光譜（consistency spectrum）**：從最強到最弱的一連串一致性等級——線性一致、因果一致、讀己之寫、最終一致——越強越貴、越弱越能擴展。（見〈一致性光譜：線性、因果、讀己之寫、最終一致〉）

**線性一致（linearizability）**：最強的單物件一致性，效果上像所有操作都在某個瞬間原子發生、且尊重真實時間先後；讀一定看得到先前已完成的寫。（見〈一致性光譜：線性、因果、讀己之寫、最終一致〉）

**因果一致（causal consistency）**：保證有因果關係的操作對所有人都以同樣順序出現，但對無因果關聯的操作不強求全域順序。（見〈一致性光譜：線性、因果、讀己之寫、最終一致〉）

**讀己之寫（read-your-writes）**：保證一個使用者讀得到自己剛寫的東西，即使整體只是最終一致；解掉「我改了卻看不到」的常見困惑。（見〈複製延遲與讀己之寫〉）

**最終一致性（eventual consistency）**：只要停止寫入，所有副本最終會收斂到同一個值；不保證「何時」收斂，過程中可讀到舊值。（見〈一致性光譜：線性、因果、讀己之寫、最終一致〉）

**隔離級別（isolation level）**：交易之間互相「看見」彼此到什麼程度的等級（read committed、repeatable read、serializable…），等級越高、可見的並發異常越少。（見〈隔離級別與異常：dirty、phantom 到 write-skew〉）

**寫偏（write-skew）**：兩個交易各讀一份重疊資料、各自做出在單獨看來合法的寫，合起來卻違反不變量的異常；只有可序列化等級能完全擋掉。（見〈隔離級別與異常：dirty、phantom 到 write-skew〉）

**幻讀（phantom read）**：交易重跑同一個範圍查詢時，因為別的交易插入或刪除了列，多出或少了「幽靈」資料列的異常。（見〈隔離級別與異常：dirty、phantom 到 write-skew〉）

**MVCC（Multi-Version Concurrency Control，多版本並發控制）**：讓每筆資料保留多個版本，讀取讀一個一致的快照而不擋寫、寫也不擋讀，用空間換並發。（見〈MVCC：讓讀不擋寫〉）

**死結（deadlock）**：兩個以上交易各自握著對方要的鎖、互相等待而誰都動不了的僵局；資料庫靠偵測 wait-for graph 的環來打破它。（見〈鎖與死結：行鎖、gap、next-key 與 wait-for graph〉）

**next-key lock**：行鎖加上它前面那段間隙（gap）的鎖，用來在可重複讀等級下擋掉幻讀的插入。（見〈鎖與死結：行鎖、gap、next-key 與 wait-for graph〉）

**樂觀 / 悲觀並發控制（optimistic / pessimistic concurrency control）**：悲觀＝先上鎖再動，假設衝突常見；樂觀＝先動，提交時用版本或 CAS 檢查有沒有人插隊，假設衝突罕見。（見〈樂觀與悲觀並發控制：CAS、版本與 ETag〉）

**CAS（Compare-And-Swap，比較並交換）**：只有當資料仍是我先前讀到的值時才寫入的原子操作，是樂觀並發控制的基石。（見〈樂觀與悲觀並發控制：CAS、版本與 ETag〉）

**ETag**：HTTP 上代表資源某個版本的標籤，配 If-Match 做樂觀並發控制，讓「自上次讀後沒人改過」才允許寫。（見〈樂觀與悲觀並發控制：CAS、版本與 ETag〉）

**複製延遲（replication lag）**：寫入主節點後、副本反映出該寫之間的時間差；它是讀副本可能讀到舊值的根源。（見〈複製延遲與讀己之寫〉）

**分片（sharding）**：把一份大資料水平切成多片、分散到多個節點，每片獨立承載一部分資料與流量，用以突破單機容量。（見〈分片：水平切分與路由〉）

**ACID**：交易的四個保證——原子性、一致性、隔離性、持久性；傳統關聯式資料庫的招牌。（見〈一致性與交易的保證模型：ACID、BASE、CAP、PACELC〉）

**BASE**：與 ACID 對立的取向——基本可用、軟狀態、最終一致；以放寬一致性換取可用性與擴展性。（見〈一致性與交易的保證模型：ACID、BASE、CAP、PACELC〉）

**CAP 定理**：當網路分區（P）發生時，系統只能在一致性（C）與可用性（A）之間二選一；由 Brewer 提出、Gilbert-Lynch 形式化證明。（見〈一致性與交易的保證模型：ACID、BASE、CAP、PACELC〉）

**PACELC**：CAP 的延伸——分區時在 A 與 C 間取捨（PAC），沒分區時還要在延遲（L）與一致性（C）間取捨（ELC）；由 Abadi 提出。（見〈一致性與交易的保證模型：ACID、BASE、CAP、PACELC〉）

**覆蓋索引（covering index）**：包含查詢所需全部欄位的索引，讓資料庫只讀索引就能回答、不必再回表，省掉一次隨機 I/O。（見〈索引與查詢計畫：B-tree、覆蓋索引與 planner〉）

**查詢計畫（query plan）**：planner 為一句 SQL 選定的執行步驟（走哪個索引、怎麼 join、怎麼排序）；估算錯了就會走出慢計畫。（見〈索引與查詢計畫：B-tree、覆蓋索引與 planner〉）

**多租戶隔離（multitenancy）**：多個客戶（租戶）共用一套系統時的資料隔離方式，從共表加 tenant 欄、各租戶獨立 schema，到一租戶一資料庫，隔離越強、成本越高。（見〈多租戶隔離：row、schema、db-per-tenant〉）

**零停機遷移（zero-downtime migration）**：在不中斷線上服務的前提下改變資料庫結構，靠 expand-contract 與 backfill 讓新舊結構並存到切換完成。（見〈零停機 schema 遷移：expand-contract 與 backfill〉）

**backfill（回填）**：對既有資料批次補上新欄位或新結構的值，是 expand 階段把歷史資料搬到新形式的步驟。（見〈零停機 schema 遷移：expand-contract 與 backfill〉）

**SSI（Serializable Snapshot Isolation，可序列化快照隔離）**：在快照隔離上偵測讀寫衝突、必要時中止交易來達到可序列化的機制，是 PostgreSQL 的可序列化實作路線。（見〈PostgreSQL 與 MySQL：兩種隔離哲學〉）

---

## 四、儲存引擎與資料模型

**LSM-tree（Log-Structured Merge-tree）**：把寫入先累積在記憶體、再依序刷成不可變檔案、之後背景合併的儲存結構；寫快（順序寫）但讀要查多層、有寫放大。（見〈LSM-tree 與 B-tree：寫放大換讀放大〉）

**B-tree**：把資料維持在原地、就地更新的平衡樹索引結構；讀穩定但隨機寫多、會有讀放大相對較低、寫放大相對較高的另一組取捨。（見〈LSM-tree 與 B-tree：寫放大換讀放大〉）

**寫放大 / 讀放大（write / read amplification）**：一次邏輯寫（或讀）在底層實際造成多少倍的物理 I/O；LSM 與 B-tree 的核心差異就是把放大記在哪一邊。（見〈LSM-tree 與 B-tree：寫放大換讀放大〉）

**WAL（Write-Ahead Log，預寫日誌）**：在動真正的資料頁之前，先把變更追加寫進一份順序日誌；當機後靠重放這份日誌恢復，是持久性與崩潰一致的基礎。（見〈WAL：先寫日誌，再改資料〉）

**倒排索引（inverted index）**：把「詞 → 含有該詞的文件清單」這層映射建好，讓全文搜尋能跳過逐篇掃描、直接查到命中文件。（見〈倒排索引：全文搜尋的資料結構〉）

**TTL（Time To Live，存活時間）**：一筆資料自動過期失效前的存活時長；用於快取驅逐與資料保留策略。（見〈資料的生命週期：retention、TTL、軟刪除與合規刪除〉，快取面見〈驅逐：LRU、LFU、TTL 與 LRM〉）

**軟刪除（soft delete）**：不真的刪掉資料列，只標記一個 deleted 旗標，保留可復原與稽核能力；代價是查詢都得記得排除它。（見〈資料的生命週期：retention、TTL、軟刪除與合規刪除〉）

---

## 五、快取與物件儲存

**快取（cache）**：把昂貴取得的資料暫存在更快的層，換取後續讀取的延遲與後端負載下降；代價是要面對失效與不一致。（見〈快取策略：cache-aside、write-through、write-behind〉）

**cache-aside（旁路快取）**：應用先查快取、未命中才查資料庫並回填快取的模式；最常見、但寫入與失效要應用自己管。（見〈快取策略：cache-aside、write-through、write-behind〉）

**write-through / write-behind（穿透寫 / 回寫）**：穿透寫＝寫時同步更新快取與後端；回寫＝先寫快取、稍後非同步刷回後端，更快但有遺失視窗。（見〈快取策略：cache-aside、write-through、write-behind〉）

**快取雪崩（cache avalanche）**：大量快取項在同一時刻一起過期，請求瞬間全部壓到後端的失效災難。（見〈快取的失效災難：雪崩、穿透、擊穿〉）

**快取穿透（cache penetration）**：查詢一個根本不存在的鍵，快取永遠不命中、每次都打到後端的攻擊面或設計漏洞。（見〈快取的失效災難：雪崩、穿透、擊穿〉）

**快取擊穿（cache breakdown / hotspot invalidation）**：單一熱門鍵過期的瞬間，大量並發請求同時撲向後端去重建它。（見〈快取的失效災難：雪崩、穿透、擊穿〉）

**驅逐（eviction）**：快取空間滿時挑選並丟棄一些項目以騰位的策略，常見 LRU（最久未用）、LFU（最少使用）、TTL（到期）。（見〈驅逐：LRU、LFU、TTL 與 LRM〉）

**LRU / LFU（Least Recently / Frequently Used）**：兩種驅逐策略——LRU 丟最久沒被存取的，LFU 丟存取次數最少的；前者怕掃描污染，後者怕舊熱點賴著不走。（見〈驅逐：LRU、LFU、TTL 與 LRM〉）

**RDB / AOF**：Redis 的兩種持久化——RDB 是定期快照（緊湊、恢復快、但可能丟最後一段），AOF 是追加每筆寫指令的日誌（更不易丟、但檔案大恢復慢）。（見〈Redis 的內部：單執行緒、I/O threads、持久化與多重角色〉）

**物件儲存（object storage）**：以 key 存取整顆不可變物件（如 S3）的儲存，適合大 payload；常用「資料庫只存指標、大檔走物件儲存」的交接模式。（見〈物件儲存：S3 與大 payload 的交接〉）

**預簽章 URL（presigned URL）**：由後端簽發、帶時效與權限的物件儲存網址，讓客戶端直接上傳或下載大檔，繞過自家伺服器這個瓶頸。（見〈物件儲存：S3 與大 payload 的交接〉）

---

## 六、資料同步與整合

**CDC（Change Data Capture，變更資料擷取）**：從資料庫的 WAL／binlog 讀出每一筆變更、轉成事件流，讓下游不必改寫業務碼就能近即時同步。（見〈CDC：從資料庫變更長出事件流〉）

**dual-write（雙寫）**：應用在同一個流程裡分別寫資料庫和訊息系統（兩次獨立寫）的反模式；兩寫之間任何失敗都會造成不一致，正解是 outbox 或 CDC。（見〈dual-write 問題與 event-carried state transfer〉）

**event-carried state transfer（事件攜帶狀態傳遞）**：事件本身帶上消費者所需的完整資料，讓下游不必再回呼來源；與只通知「發生了某事」的 event notification 相對。（見〈dual-write 問題與 event-carried state transfer〉，兩種風格見〈事件驅動架構：event notification 與 event-carried state transfer〉）

**衝突解決（conflict resolution）**：多寫端各自改了同一筆資料、合併時的化解規則，常見 LWW（最後寫入勝）、版本向量、CRDT。（見〈衝突解決：LWW、版本向量與 CRDT〉）

**LWW（Last-Write-Wins，最後寫入勝）**：用時間戳比大小、保留較晚那筆的衝突解決法；簡單但會默默丟掉並發的另一筆寫。（見〈衝突解決：LWW、版本向量與 CRDT〉）

**CRDT（Conflict-free Replicated Data Type，無衝突複製資料型別）**：用數學性質保證多副本各自更新後一定收斂到同一狀態、無需協調的資料結構。（見〈衝突解決：LWW、版本向量與 CRDT〉）

**版本向量（version vector）**：記錄每個副本各自的更新計數，用以判斷兩個版本是「一個是另一個的後續」還是「真的並發衝突」。（見〈衝突解決：LWW、版本向量與 CRDT〉）

**對帳（reconciliation）**：定期比對兩個資料來源、找出漂移並修正的機制；是承認「再嚴密的同步也會偶爾出錯」之後的安全網。（見〈對帳：怎麼確認兩邊一致、漂移怎麼修〉）

---

## 七、網路、協定與 API

**keep-alive**：在一條 TCP 連線上連續送多個 HTTP 請求、不每次重建連線，省掉反覆握手的開銷。（見〈HTTP/1.1、HTTP/2、HTTP/3：keep-alive、多工與 QUIC〉）

**多工（multiplexing）**：在一條連線上同時並行多個請求／回應而不互相阻塞；HTTP/2 在應用層做到，但仍受 TCP 層 head-of-line blocking 拖累。（見〈HTTP/1.1、HTTP/2、HTTP/3：keep-alive、多工與 QUIC〉）

**QUIC**：建在 UDP 上、把握手與加密合併、並在傳輸層消除 head-of-line blocking 的協定，是 HTTP/3 的底層。（見〈HTTP/1.1、HTTP/2、HTTP/3：keep-alive、多工與 QUIC〉）

**gRPC**：以 Protobuf 為 IDL、跑在 HTTP/2 上的 RPC 框架，支援雙向串流與強型別契約。（見〈gRPC 與 Protobuf：用 IDL 定義服務〉）

**Protobuf（Protocol Buffers）**：Google 的二進位序列化格式與 IDL，欄位以 tag number 編碼，因而能向前後相容地演進。（見〈gRPC 與 Protobuf：用 IDL 定義服務〉，相容性見〈序列化與 schema 演進〉）

**IDL（Interface Definition Language，介面定義語言）**：用一份語言中立的契約描述服務的方法與訊息結構，再產生各語言的程式碼。（見〈gRPC 與 Protobuf：用 IDL 定義服務〉）

**連線池（connection pool）**：預先建立並重複利用一批連線，避免每次請求都付建立連線（尤其 TCP＋TLS 握手）的成本。（見〈連線池：為什麼不每次都重開連線〉，調參見〈連線池調校〉）

**負載均衡（load balancing）**：把進來的流量分散到多個後端實例的機制，分 L4（依 IP／port）與 L7（依 HTTP 內容），並靠健康檢查避開壞實例。（見〈負載均衡：L4 與 L7、演算法與健康檢查〉）

**L4 / L7 負載均衡**：L4 在傳輸層依連線資訊轉發、快但不懂內容；L7 在應用層讀得懂 HTTP、能依路徑與標頭做更聰明的路由，代價是較重。（見〈負載均衡：L4 與 L7、演算法與健康檢查〉）

**TLS / mTLS（mutual TLS，雙向 TLS）**：TLS 讓客戶端驗證伺服器身分並加密通道；mTLS 要求雙方都出示憑證、互相驗證，常用於服務間零信任通訊。（見〈TLS 與 mTLS：握手與憑證管理〉）

**服務發現（service discovery）**：在實例會動態增減的環境裡，讓呼叫方查到「現在某服務有哪些健康實例、位址是什麼」的機制。（見〈DNS 與服務發現〉）

**service mesh（服務網格）**：把重試、逾時、mTLS、流量路由等網路關注點，從應用碼下沉到每個服務旁的 sidecar 代理統一處理。（見〈Service mesh：把網路關注點下沉到 sidecar〉）

**sidecar**：與主應用同部署的輔助代理行程，攔截進出流量並代為處理網路關注點，是 service mesh 的資料面單元。（見〈Service mesh：把網路關注點下沉到 sidecar〉）

**WebSocket**：在一條長連線上做全雙工雙向通訊的協定，從 HTTP 升級而來，靠 ping-pong 維生、靠 backplane 做水平擴展。（見〈WebSocket：frame、ping-pong 與水平擴展〉）

**黏性會話（sticky session / session affinity）**：負載均衡器讓同一個客戶端的後續請求都回到同一台實例，解有狀態長連線的需求，但實例掛掉時這份親和性就失效。（見〈WebSocket：frame、ping-pong 與水平擴展〉）

**backplane（背板 / backbone）**：多台 WebSocket 伺服器之間轉發訊息的共用通道（常用 Redis Pub/Sub），讓連在不同實例的使用者也能互通。（見〈WebSocket：frame、ping-pong 與水平擴展〉）

**SSE（Server-Sent Events，伺服器發送事件）**：伺服器透過一條長 HTTP 連線單向、持續推文字事件給瀏覽器的機制；比 WebSocket 簡單，但只能單向。（見〈SSE、long-poll 與 WebTransport〉）

**long-poll（長輪詢）**：客戶端發一個請求、伺服器壓著不回直到有資料或逾時才回、回了再立刻重發的偽推送技巧。（見〈SSE、long-poll 與 WebTransport〉）

**WebRTC**：瀏覽器間點對點傳音視訊與資料的協定組合，需要信令交換連線資訊、並靠 SFU／MCU 等架構處理多方媒體轉發。（見〈WebRTC：媒體、傳輸與信令〉）

**REST**：以資源（URL）＋HTTP 動詞為核心的 API 風格，講究無狀態與統一介面；靠 OpenAPI 描述契約、靠版本化管理演進。（見〈REST 設計、版本化與 OpenAPI 契約〉）

**OpenAPI**：用機器可讀的規格描述 REST API 的端點、參數與回應結構的標準，可據此產文件、產用戶端、做契約測試。（見〈REST 設計、版本化與 OpenAPI 契約〉）

**分頁（pagination）**：把大結果集切成多頁回傳的機制，分 offset（簡單但深頁慢且會跳漏）與 cursor／keyset（穩定且深頁不退化）。（見〈分頁：offset 與 cursor/keyset、深分頁〉）

**cursor / keyset 分頁**：以「上一頁最後一筆的鍵值」為錨點往下取的分頁法，避開 offset 在深分頁與資料變動下的漏項與效能崩塌。（見〈分頁：offset 與 cursor/keyset、深分頁〉）

**GraphQL**：讓客戶端用一個查詢精確指定要哪些欄位的 API 範式，解 REST 的 over-fetch／under-fetch，代價是後端複雜度與 N+1 風險上移。（見〈REST、GraphQL 與 gRPC：三種 API 範式〉）

**API gateway（API 閘道）**：擺在後端群前面的統一入口，集中處理認證授權、限流、協定轉換與回應聚合。（見〈API gateway 的角色：authz、限流、轉換與聚合〉）

---

## 八、身分與存取

**認證與授權（authentication / authorization，AuthN / AuthZ）**：認證問「你是誰」、授權問「你能做什麼」；兩者是先後不同的關卡，常被混為一談。（見〈認證與授權：AuthN、AuthZ 與 OIDC 的位置〉）

**token 生命週期（token lifecycle）**：存取憑證從簽發、使用、過期到撤銷的全程；短 TTL 的 access token 配 refresh token，是無狀態與可撤銷之間的折衷。（見〈token 的生命週期與撤銷〉）

**refresh token**：用來換取新 access token 的長壽憑證，讓 access token 可以維持很短的有效期、縮小被盜用的視窗。（見〈token 的生命週期與撤銷〉）

**denylist（撤銷清單）**：記下「雖未過期但已被撤銷」的 token，讓無狀態 JWT 也能即時失效；代價是重新引入一次狀態查詢。（見〈token 的生命週期與撤銷〉）

**JWT（JSON Web Token）**：把宣告（claims）以 JSON 編碼、附上簽章的自帶資訊憑證，伺服器靠驗章就能信任內容、不必查庫。（見〈JWT 與簽章：結構、HS256/RS256 與 JWKS〉）

**HS256 / RS256**：JWT 的兩種簽章演算法——HS256 用對稱密鑰（簽與驗同一把），RS256 用非對稱金鑰（私鑰簽、公鑰驗），後者讓驗證方不必握有簽發密鑰。（見〈JWT 與簽章：結構、HS256/RS256 與 JWKS〉）

**JWKS（JSON Web Key Set）**：簽發方公開其驗章公鑰的端點，讓驗證方動態取得並輪替公鑰。（見〈JWT 與簽章：結構、HS256/RS256 與 JWKS〉）

**RBAC（Role-Based Access Control，角色型存取控制）**：先把權限綁到角色、再把角色指派給人的授權模型；好管理但角色數量會隨例外暴增。（見〈RBAC 與 ABAC：兩種授權模型〉）

**ABAC（Attribute-Based Access Control，屬性型存取控制）**：用主體、資源、環境的屬性即時計算是否放行的授權模型；表達力強但難審計與推理。（見〈RBAC 與 ABAC：兩種授權模型〉）

**OAuth 2.0 / OIDC（OpenID Connect）**：OAuth 是「授權」框架——讓第三方在不拿密碼的情況下代為存取資源；OIDC 在其上加一層「認證」，回答「使用者是誰」。（見〈OAuth2、OIDC 與 OAuth 2.1：grant 類型與現況〉）

**grant 類型（grant type）**：OAuth 取得 token 的幾種流程（authorization code、client credentials…）；OAuth 2.1 收斂了不安全的舊流程、強制 PKCE。（見〈OAuth2、OIDC 與 OAuth 2.1：grant 類型與現況〉）

---

## 九、並發與執行模型

**並發與平行（concurrency / parallelism）**：並發是「同時在處理多件事」的結構安排（可在單核交錯），平行是「同一瞬間真的在跑多件事」（需多核）；兩者常被混用。（見〈並發不是平行：兩個常被混用的詞〉）

**event loop**：單執行緒輪流處理一批就緒事件與回呼的迴圈，靠不阻塞地等 I/O 達成高並發；Node.js 的 libuv 分多個相位執行。（見〈event loop：單執行緒怎麼同時做很多事〉）

**阻塞 / 非阻塞 I/O（blocking / non-blocking I/O）**：阻塞＝呼叫卡住執行緒直到 I/O 完成；非阻塞＝立刻返回、之後用事件通知完成；event loop 的高並發全靠後者。（見〈阻塞與非阻塞 I/O〉）

**thread pool（執行緒池）**：預先開好一批工作執行緒重複領任務，避免頻繁建立／銷毀執行緒的成本，並把 CPU 密集或阻塞工作從 event loop 卸下。（見〈thread pool 與 worker threads：CPU 密集怎麼辦〉）

**worker thread（工作執行緒）**：真正並行執行的背景執行緒，用來跑會卡住 event loop 的 CPU 密集任務。（見〈thread pool 與 worker threads：CPU 密集怎麼辦〉）

**race condition（競態條件）**：結果取決於多個操作的交錯時序、而非邏輯本身的缺陷，因此偶發、難重現；跨 DB、cache、runtime 都會出現。（見〈race condition 與原子性：跨 DB、cache、runtime〉）

**原子性（atomicity）**：一組操作「要嘛全發生、要嘛全不發生、中間不可被別人觀察到」的性質，是擋掉競態的基本武器。（見〈race condition 與原子性：跨 DB、cache、runtime〉）

**actor 模型**：把狀態封裝在獨立的 actor 裡、只靠訊息互通、不共享記憶體的並發模型，以「無共享」迴避鎖。（見〈並發模型比較：thread、event-loop、actor、coroutine、CSP〉）

**coroutine（協程）**：可被掛起與恢復的輕量級執行單元，由 runtime 在少數執行緒上排程，用同步寫法達成非同步效率。（見〈並發模型比較：thread、event-loop、actor、coroutine、CSP〉）

**CSP（Communicating Sequential Processes）**：以 channel 傳訊協調獨立流程的並發模型（Go 的 goroutine＋channel 是代表），強調「用通訊共享記憶體，而非用共享記憶體通訊」。（見〈並發模型比較：thread、event-loop、actor、coroutine、CSP〉）

---

## 十、過載、流量控制與韌性

**背壓（backpressure）**：當下游處理不及時，把「慢下來」這個訊號逆流傳回上游、讓生產端減速，避免訊息在中間無上限地堆積到 OOM。（見〈背壓：當下游跟不上〉）

**rate limiting（限流）**：主動限制單位時間內放行的請求數，保護後端不被打爆；常見演算法 token bucket、leaky bucket。（見〈rate limiting：token bucket、leaky bucket 與分散式限流〉）

**token bucket（權杖桶）**：以固定速率往桶裡補權杖、每個請求耗一個權杖、桶空就擋的限流演算法，允許一定程度的突發。（見〈rate limiting：token bucket、leaky bucket 與分散式限流〉）

**leaky bucket（漏桶）**：請求進桶、以固定速率「漏出」處理的限流演算法，把突發流量整形成平穩輸出。（見〈rate limiting：token bucket、leaky bucket 與分散式限流〉）

**load shedding（卸載）**：過載時主動丟掉一部分請求（通常挑低優先序的），用「拒絕一些」換「服務剩下的」，避免整體一起垮。（見〈load shedding：主動丟掉一部分流量〉）

**circuit breaker（斷路器）**：偵測到對某依賴的呼叫持續失敗時就「跳閘」、快速失敗不再打它，給它喘息；分 closed、open、half-open 三態。（見〈circuit breaker：三態與半開試探〉）

**half-open（半開）**：斷路器跳閘冷卻後試放幾個請求、看依賴是否恢復的狀態；成功就闔上、失敗就再跳開。（見〈circuit breaker：三態與半開試探〉）

**retry storm（重試風暴）**：故障時大量客戶端同時重試、把本已吃緊的系統推得更深的正回饋失控。（見〈retry storm 與 metastable failure〉）

**metastable failure（亞穩定故障）**：系統被一個觸發事件踹進一個「會自我維持」的壞狀態，即使原始觸發已消失仍困在裡頭、無法自行恢復。（見〈retry storm 與 metastable failure〉）

**利用率（utilization，ρ）**：資源被佔用的比例；排隊理論告訴我們，當 ρ 逼近 1 時，等待時間會非線性地飆向無限。（見〈排隊的直覺：為什麼利用率逼近 1 會爆炸〉）

**timeout / deadline / budget（逾時 / 期限 / 預算）**：把等待變成有界——逾時限制單次呼叫的等待，deadline 設定整個請求的最終截止，budget 在多級呼叫間分配剩餘可等時間。（見〈timeout、deadline 與 budget：把等待變成有界〉）

**bulkhead（艙壁）**：把資源（執行緒、連線池）按用途隔成獨立隔艙，讓一個依賴的故障吃光自己那艙、不拖垮其他功能；得名自船的防沉艙壁。（見〈bulkhead：艙壁隔離〉）

**health check（健康檢查）**：編排器與負載均衡器用來判斷實例是否該收流量的探針，分 liveness（活著沒、否則重啟）與 readiness（準備好收流量沒）。（見〈health check：liveness 與 readiness〉）

**liveness / readiness probe（存活 / 就緒探針）**：liveness 失敗代表行程卡死、該被重啟；readiness 失敗代表暫時不該收流量、但不必重啟（如還在暖機或依賴未就緒）。（見〈health check：liveness 與 readiness〉）

**graceful shutdown（優雅關閉）**：收到終止訊號後，停止收新請求、把手上的請求做完、釋放連線與資源再退出，避免硬殺造成的請求斷頭與資料殘缺。（見〈graceful shutdown：怎麼好好地關掉一個行程〉）

**fallback（降級）**：主路徑壞掉時退到一個次優但仍可用的結果（快取舊值、預設值、簡化回應），把硬故障變成軟降級。（見〈fallback 與降級：壞掉時退到哪〉）

---

## 十一、效能與延遲

**冷啟動（cold start）**：實例或執行環境首次接到請求時，因為要載入程式、建連線、JIT 預熱而格外慢的那一段；之後暖機完才回到正常延遲。（見〈冷啟動與暖機：第一個請求為什麼那麼慢〉，Lambda 的 SnapStart 見〈Lambda：冷啟動、SnapStart、payload 與併發〉）

**長尾延遲（tail latency）**：少數最慢請求所在的延遲分布尾端，用 p99、p999 衡量；在扇出多依賴的請求裡，尾端會被放大成常態。（見〈長尾延遲：p99 從哪裡來〉）

**p99 / p999（百分位延遲）**：99%／99.9% 的請求快過的延遲值；看尾端而非平均，才看得到少數使用者真正的痛。（見〈長尾延遲：p99 從哪裡來〉，目標化見〈SLI、SLO 與 error budget：p99 與 p999〉）

**N+1 查詢（N+1 query）**：先查一筆清單（1 次）、再對清單每一項各發一次查詢（N 次）的反模式，把一個迴圈變成打爆資料庫的 N+1 趟往返。（見〈N+1 查詢：一個迴圈打爆資料庫〉）

**批次與合併（batching / coalescing）**：把多個小操作攢成一次大操作（batching），或把同時湧入的相同請求併成一次（coalescing），用一點延遲換大量吞吐與後端負載下降。（見〈批次、coalescing 與 debounce〉）

**debounce（去抖）**：把短時間內連續觸發的事件壓成最後一次才真正執行，避免重複而無意義的工作。（見〈批次、coalescing 與 debounce〉）

---

## 十二、分散式系統核心

**partial failure（部分失敗）**：分散式系統裡「一部分節點壞了、其他還活著，而且你常分不清誰壞了」的常態，是分散式之所以難的第一原理。（見〈為什麼分散式這麼難：partial failure 與失敗模型〉）

**共識（consensus）**：讓一群可能當機、訊息可能延遲的機器，對某個值（如「誰是 leader」「日誌的下一筆是什麼」）達成一致決定的問題與機制。（見〈共識：讓一群會當機的機器同意一件事〉）

**Raft**：一種好理解的共識演算法，用 leader 選舉＋日誌複製＋過半確認來維持一致的 replicated log；由 Ongaro 與 Ousterhout 於 2014 提出。（見〈共識：讓一群會當機的機器同意一件事〉）

**replicated log（複製日誌）**：所有節點按相同順序追加相同條目的日誌，是共識系統的核心抽象——只要日誌一致，重放出的狀態就一致。（見〈共識：讓一群會當機的機器同意一件事〉）

**FLP 不可能性（FLP impossibility）**：在純非同步、容許至少一個節點崩潰的模型下，沒有確定性演算法能保證一定達成共識；由 Fischer-Lynch-Paterson 於 1985 證明。（見〈共識：讓一群會當機的機器同意一件事〉）

**leader election（領袖選舉）**：在一群對等節點中選出唯一一個寫入點／協調者的過程，並要能在它失聯時安全地選出下一個。（見〈leader election：選出唯一的寫入點〉）

**分散式鎖（distributed lock）**：跨多個行程／機器協調「同一時間只有一個能進臨界區」的鎖；本質是一份有時效的租約（lease），而非永久持有。（見〈分散式鎖：Redlock、fencing token 與「鎖其實是租約」〉）

**Redlock**：Redis 提出的、用多個獨立節點過半取鎖來做分散式鎖的演算法；其安全性在時鐘與 GC 暫停下有爭議，本書講清它的成立條件。（見〈分散式鎖：Redlock、fencing token 與「鎖其實是租約」〉）

**fencing token（柵欄記號）**：取鎖時拿到的單調遞增號碼，資源端只接受號碼更大的請求，藉此擋掉「持鎖者暫停後鎖已過期、卻仍帶舊權限來寫」的危險。（見〈分散式鎖：Redlock、fencing token 與「鎖其實是租約」〉）

**租約（lease）**：帶過期時間的鎖／授權，持有者須在到期前續租，否則自動釋放——用時間上界換「持有者失聯也不會永久卡死」。（見〈分散式鎖：Redlock、fencing token 與「鎖其實是租約」〉）

**quorum（法定數）**：要求讀寫各觸及一定數量的節點（讀 R＋寫 W ＞ 節點數 N），靠鴿巢原理保證讀寫集合必然相交、讀得到最新寫。（見〈quorum：R + W > N 的鴿巢原理〉）

**邏輯時鐘（logical clock）**：不依賴可能不準的牆鐘、而是用事件計數來決定「誰在誰之前」的排序機制，如 Lamport 時鐘與向量時鐘。（見〈邏輯時鐘與排序：Lamport、向量時鐘、HLC 與 TrueTime〉）

**Lamport 時鐘**：每個事件配一個遞增計數、收訊時取兩邊較大值加一的邏輯時鐘；能給出與因果一致的全序，但無法從號碼反推兩事件是否並發。（見〈邏輯時鐘與排序：Lamport、向量時鐘、HLC 與 TrueTime〉）

**向量時鐘（vector clock）**：每個節點各記一個計數、合成一個向量的邏輯時鐘，能判斷兩事件是有因果先後還是真的並發。（見〈邏輯時鐘與排序：Lamport、向量時鐘、HLC 與 TrueTime〉）

**HLC（Hybrid Logical Clock，混合邏輯時鐘）**：把實體時間與邏輯計數揉在一起的時鐘，既接近真實時間、又保證單調與因果，兼得兩者之長。（見〈邏輯時鐘與排序：Lamport、向量時鐘、HLC 與 TrueTime〉）

**TrueTime**：Google Spanner 用的、會回傳一個「真實時間落在 \[earliest, latest] 區間」的有界誤差時鐘 API，靠等過誤差上界來達成外部一致。（見〈邏輯時鐘與排序：Lamport、向量時鐘、HLC 與 TrueTime〉）

**複製策略（replication strategy）**：副本怎麼接受寫入的範式——單主（一個寫入點）、多主（多個寫入點、要解衝突）、無主（靠 quorum 讀寫）。（見〈複製策略：單主、多主、無主〉）

**2PC（Two-Phase Commit，兩階段提交）**：跨節點原子提交的協定——協調者先問所有參與者「能不能提交」（prepare），全答能才下令提交；它能保原子，代價是協調者掛掉時參與者會阻塞。（見〈2PC 與分散式交易：原子提交與它的阻塞代價〉）

**consistent hashing（一致性雜湊）**：把節點與鍵都映射到一個雜湊環上、鍵歸給順時針下一個節點的分配法，讓節點進出時只需搬動少量鍵，而非全體重洗。（見〈consistent hashing：節點進出時少搬一點資料〉）

**virtual node（虛擬節點）**：在雜湊環上給每個實體節點放多個分身，把負載與資料分布攤得更均勻、並讓節點增減時的搬遷更平滑。（見〈consistent hashing：節點進出時少搬一點資料〉）

**gossip（流言傳播）**：每個節點週期性隨機挑幾個鄰居交換狀態，讓資訊像流言一樣在叢集中擴散，達成去中心的成員探知與狀態同步。（見〈gossip 與 anti-entropy〉）

**anti-entropy（反熵）**：背景程序持續比對副本間的差異並修補，把因丟訊或故障累積的不一致慢慢抹平，是最終一致的清道夫。（見〈gossip 與 anti-entropy〉）

**failure detection（失敗偵測）**：判斷一個遠端節點是死了還是只是慢——在非同步網路裡這兩者無法區分，逾時是唯一可用、卻必然會誤判的手段。（見〈失敗偵測：逾時是唯一手段、慢與死分不開〉）

**單調鐘 / 牆鐘（monotonic / wall clock）**：牆鐘是會被校時、回撥、跳 DST 的「日期時間」；單調鐘只會往前走、適合量時間差。量逾時與間隔該用單調鐘，記事件發生時刻才用牆鐘。（見〈時間與日期：UTC、epoch、timezone 與 DST 的應用層坑〉）

---

## 十三、架構、雲端與發布

**解耦（decoupling）**：降低元件間的相依，使一方變動不逼著另一方跟著改；本書把耦合拆成時間、空間、同步性、資料、實作五個面向。（見〈解耦：時間、空間、同步性、資料、實作五種耦合〉）

**同步 / 非同步通訊（synchronous / asynchronous communication）**：同步＝呼叫端等到回應才繼續（時間耦合）；非同步＝送出後不等、靠訊息或回呼解時間耦合，代價是流程更難追蹤。（見〈同步與非同步通訊〉）

**事件驅動架構（event-driven architecture，EDA）**：元件以發布／訂閱事件互動而非直接呼叫的架構，分 event notification（只通知）與 event-carried state transfer（事件帶狀態）兩種風格。（見〈事件驅動架構：event notification 與 event-carried state transfer〉）

**Event sourcing（事件溯源）**：把狀態存成一串不可變事件、現狀由重放事件得出，而非只存最終值；天然有完整歷史與稽核軌跡。（見〈Event sourcing 與 CQRS：狀態是不可變事件序列〉）

**CQRS（Command Query Responsibility Segregation，命令查詢職責分離）**：把寫模型（命令）與讀模型（查詢）拆開、各自最佳化，常與 event sourcing 搭配，代價是讀模型最終一致。（見〈Event sourcing 與 CQRS：狀態是不可變事件序列〉）

**durable execution（持久化執行）**：把長流程的每一步狀態持久化，讓工作流在當機後能從中斷處精確續跑而不重做已完成步驟（Temporal、Step Functions 屬此類）。（見〈durable execution：Temporal、Step Functions 與長流程〉）

**無狀態 / 有狀態（stateless / stateful）**：無狀態實例不在本機保留請求間的狀態，因此可隨意增減與替換——這正是 serverless 與水平擴展的前提；有狀態則需處理黏性與遷移。（見〈無狀態與有狀態：為什麼 serverless 要無狀態〉）

**SnapStart**：AWS Lambda 預先初始化並快照執行環境、之後從快照恢復以縮短冷啟動的機制。（見〈Lambda：冷啟動、SnapStart、payload 與併發〉）

**concurrencyPolicy**：K8s CronJob 控制「上一輪還沒跑完、下一輪排程到了」要怎麼辦的設定（Allow／Forbid／Replace）；CronJob 並不保證 exactly-once 觸發。（見〈K8s CronJob：schedule、concurrencyPolicy 與「不是 exactly-once」〉）

**blue-green 部署**：同時備好新（green）舊（blue）兩套環境、把流量整批切過去的發布法，切換快、回滾也快，代價是雙倍資源。（見〈blue-green、canary 與 rolling〉）

**canary 部署**：先把新版本放給一小撮流量試水溫、觀測無礙再逐步放大的發布法，用小爆炸半徑換早期偵錯。（見〈blue-green、canary 與 rolling〉）

**rolling 部署**：一批批替換實例、新舊版本在過程中並存的發布法；省資源，但要求新舊版本能同時運作。（見〈blue-green、canary 與 rolling〉）

**容器（container）**：用 namespace 隔離視野、cgroup 限制資源、共享主機核心的輕量隔離單元；比虛擬機輕、啟動快。（見〈Docker：容器隔離的原理〉）

**namespace / cgroup**：Linux 核心兩大容器原語——namespace 讓行程看到的資源（PID、網路、掛載）被隔離，cgroup 限制與計量它能用多少 CPU、記憶體。（見〈Docker：容器隔離的原理〉）

**Kubernetes（K8s）**：容器編排系統，以 Pod 為調度單元、Service 做穩定入口、HPA 依負載自動伸縮，用宣告式期望狀態驅動實際狀態收斂。（見〈Kubernetes：Pod、Service、HPA 與調度〉）

**HPA（Horizontal Pod Autoscaler，水平 Pod 自動伸縮）**：依 CPU、記憶體或自訂指標自動增減 Pod 數量的 K8s 控制器。（見〈Kubernetes：Pod、Service、HPA 與調度〉）

**IaC（Infrastructure as Code，基礎設施即程式碼）**：用宣告式程式碼描述基礎設施的期望狀態、由工具計算並套用差異；apply 必須冪等，反覆執行同一份碼結果一致。（見〈IaC：宣告式、漂移與冪等 apply〉）

**漂移（drift）**：實際基礎設施狀態偏離 IaC 宣告（有人手改了），是宣告式管理要持續偵測並矯正的問題。（見〈IaC：宣告式、漂移與冪等 apply〉）

**12-factor app**：一套打造可移植、可水平擴展雲端應用的十二條準則（設定走環境變數、行程無狀態、log 當事件流…）；本書檢視哪幾條在容器／serverless 時代仍成立。（見〈12-factor：哪些在容器/serverless 時代仍成立〉）

---

## 十四、可觀測性與營運文化

**三本柱（three pillars）**：可觀測性的三類訊號——metric（聚合數字、便宜耐久）、log（離散事件、細節豐富）、trace（一個請求跨服務的完整路徑）。（見〈三本柱：metric、log 與 trace〉）

**metric / log / trace（指標 / 日誌 / 追蹤）**：metric 適合看趨勢與告警、log 適合查單一事件細節、trace 適合看一個請求在分散式系統裡走過哪些服務、慢在哪。（見〈三本柱：metric、log 與 trace〉，trace 機制見〈分散式追蹤：trace context 傳播、span 與取樣〉）

**cardinality（基數）**：一個指標標籤可能值的數量；高基數標籤（如 user id、URL 帶參數）會讓時間序列數爆炸、拖垮監控系統。（見〈cardinality 爆炸：一個 label 如何拖垮監控〉）

**SLI / SLO（Service Level Indicator / Objective，服務水準指標 / 目標）**：SLI 是衡量服務品質的具體量測（如成功率、p99 延遲），SLO 是為它定的目標值（如 99.9%）。（見〈SLI、SLO 與 error budget：p99 與 p999〉）

**error budget（錯誤預算）**：SLO 留下的「允許不達標」額度（如 99.9% 對應每月約 43 分鐘）；它把可靠性變成可花用的預算，也是發布速度與穩定間的談判工具。（見〈SLI、SLO 與 error budget：p99 與 p999〉，當談判工具見〈SRE 文化：toil、error budget 當談判工具〉）

**告警疲勞（alert fatigue）**：告警太多、太吵、太常誤報，導致值班的人麻木、漏掉真正重要的那一個；好告警對症狀（使用者有感）而非對原因。（見〈告警設計：症狀 vs 原因、告警疲勞〉）

**coordinated omission（協同遺漏）**：負載測試在系統卡住時連帶停發請求，於是漏記了那些「本該發出卻被卡住」的慢樣本，使延遲統計被嚴重低估。（見〈負載測試：開放與封閉模型、coordinated omission〉）

**開放 / 封閉模型（open / closed model）**：負載產生的兩種模型——開放模型不管系統多慢都按固定速率發請求（貼近真實流量），封閉模型等上一個回了才發下一個（會自動降速、掩蓋過載）。（見〈負載測試：開放與封閉模型、coordinated omission〉）

**分散式追蹤（distributed tracing）**：給一個請求一個 trace id、在跨服務呼叫間傳播 context，把它經過的每段工作串成一棵 span 樹，看清端到端路徑與耗時。（見〈分散式追蹤：trace context 傳播、span 與取樣〉）

**span**：分散式追蹤裡代表一段具名工作的單元（如一次資料庫查詢、一次 RPC），帶起訖時間並掛在父 span 下，組成一個 trace。（見〈分散式追蹤：trace context 傳播、span 與取樣〉）

**契約測試（contract testing）**：驗證服務間「提供方的輸出」與「消費方的期待」相容的測試，讓雙方能各自獨立部署而不怕介面悄悄破裂。（見〈測試策略：unit、integration、contract、e2e〉）

**無咎事後檢討（blameless postmortem）**：事故後聚焦於「系統與流程怎麼讓錯誤發生」、而非追究個人責任的檢討文化，目的是讓人敢誠實揭露、從而真正修掉根因。（見〈事故應變與無咎事後檢討〉）

**runbook**：針對某類事故或例行操作寫好的、可照著一步步執行的處置手冊，讓凌晨被叫起來的人不必臨場推理。（見〈事故應變與無咎事後檢討〉）

**toil（重複苦工）**：可自動化、無長期價值、會隨服務規模線性增長的手動營運工作；SRE 文化主張持續用工程把它消滅。（見〈SRE 文化：toil、error budget 當談判工具〉）

**DORA 四指標**：衡量軟體交付效能的四個指標——部署頻率、變更前置時間、變更失敗率、服務恢復時間（MTTR）；前兩個量速度、後兩個量穩定。（見〈DORA 四指標〉）

**MTTR（Mean Time To Recovery，平均恢復時間）**：從服務故障到恢復的平均耗時；它衡量的不是「多久壞一次」，而是「壞了多快能救回來」。（見〈DORA 四指標〉）

**trunk-based / git-flow（主幹開發 / git-flow）**：兩種分支策略——主幹開發鼓勵頻繁併回單一主幹、配 feature flag，利於持續交付；git-flow 用長壽分支隔離功能與發布，較重、整合衝突風險高。（見〈分支與發布策略：trunk-based vs git-flow〉）
