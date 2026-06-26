# M · 共識與複製

分散式系統的核心難題是：多台機器在「部分故障、訊息會延遲遺失、各自時鐘不一致」的環境下，怎麼對「某件事發生了」達成可靠的一致認定。本檔處理這條主線上的六個概念：**分散式失敗模型**（為什麼分散式比單機難的第一原理）、**共識 consensus**（Raft / Paxos 怎麼讓一組節點同意一份 replicated log）、**leader election**（共識協定怎麼選出唯一寫入點）、**quorum**（R + W > N 這種「多數重疊」式一致）、**複製策略**（單主 / 多主 / 無主三種把資料複製到多節點的範式）、**2PC 與分散式交易**（跨資源原子提交與它的阻塞代價）。協調用的時鐘、邏輯排序、分散式鎖、consistent hashing、gossip 留在本領域另一檔；一致性模型與隔離級別的「資料庫操作面後果」屬領域 B；冪等定義屬領域 A，本檔只引用。

## 分散式失敗模型

### 定義與原理

單機程式只有兩種狀態：整個行程在跑，或整個行程掛了（fail-stop）——你不會遇到「一半的記憶體還活著、另一半已死」。分散式系統的第一原理是 **partial failure（部分失敗）**：在一群協作的節點中，任一節點、任一條網路連線、任一段訊息，都可能**獨立地**失敗，而系統的其餘部分繼續運作、對此一無所知。你發出一個請求，沒收到回應——你**無法區分**這四種情況：請求在路上丟了、對方還在處理、對方處理完了但回應在路上丟了、對方整個掛了。在非同步網路（訊息延遲無上界）裡，這個區分**原則上不可能**做到。

失敗模型由弱到強分三層：

- **crash-stop（fail-stop）**：節點要麼正確運作，要麼直接停掉、不再參與，且**停了就不回來**。最樂觀的模型。
- **crash-recovery**：節點可能崩潰後**重啟回來**，記憶體狀態全失（只剩持久化到磁碟的部分），帶著「失憶」重新加入。這是真實系統的常態——所以協定必須假設「一個沉默的節點可能稍後帶著舊認知復活」。
- **Byzantine（拜占庭）**：節點可能**任意行為**——傳送矛盾訊息給不同對端、偽造資料、甚至惡意配合。最悲觀的模型。

為什麼 partial failure 比 fail-stop 難？因為 fail-stop 下「沒回應」＝「死了」，你可以據此安全地做決定（接手、重試、報錯）。partial failure 下「沒回應」是**多義的**，任何「假設它死了」而採取的行動（例如接手它的工作）都可能在它其實還活著時造成**雙重執行**或**腦裂（split-brain）**。逾時（timeout）是你唯一能用的偵測手段，但逾時只能告訴你「它沒在我等的時間內回應」，永遠無法證明「它死了」——這是失敗偵測的根本侷限（見領域 J 的「失敗偵測」）。

### 解法空間

面對 partial failure，工程上的應對不是「消除它」（消不掉），而是**選一個失敗模型假設、據此設計**：

- **假設 crash-stop，用逾時 + 重試 + 冪等**：最常見的工作級做法。承認「沒回應可能是死也可能是慢」，所以重試，並用冪等（見領域 A 的「冪等」）讓重複執行無害。
- **假設 crash-recovery，狀態持久化 + epoch/term 防陳舊**：把關鍵決定寫進持久日誌（WAL，見領域 O），復活的節點靠遞增的世代編號（term/epoch）被識別為「上一輪的」而拒絕其陳舊指令。
- **用共識協定吸收 partial failure**：把「達成一致」這件事外包給 Raft/Paxos（見「共識 consensus」），它們的安全性證明就建立在 crash-recovery + 非同步網路之上，只要多數節點存活就能繼續。
- **針對 Byzantine 才用 BFT 協定**：拜占庭容錯（如 PBFT、區塊鏈共識）成本高——需要 **n ≥ 3m + 1** 個節點才能容忍 m 個惡意節點（Lamport-Shostak-Pease 1982 證明的下界）。一般企業內部系統（節點都是自己人、只會崩潰不會說謊）**不需要**付這個代價。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 假設 crash-stop | 最簡單；逾時即視為死 | 節點不會復活、或復活也無害的無狀態服務 | 真實節點會復活；「沉默＝死」會誤判慢節點 |
| 假設 crash-recovery | 容忍崩潰後復活、失憶 | 絕大多數有狀態的後端 / 共識系統 | 必須持久化 + 用 term/epoch 排除陳舊復活者 |
| 共識協定（Raft/Paxos） | 多數存活即安全進展 | 需要強一致的中樞（leader 選舉、metadata、鎖） | 少數派被擋（無法寫入）；延遲＝多數確認的 RTT |
| BFT（n≥3m+1） | 容忍惡意/任意行為節點 | 互不信任的多方、開放網路、區塊鏈 | 節點數與訊息複雜度暴增；企業內網過度設計 |

### 何時需要

**幾乎所有跨機器的後端都需要把 crash-recovery 當預設假設**——一旦你的系統有多個行程協作、且任一個會重啟，「沉默的節點可能帶著舊狀態復活」就是必須處理的真實情況。**Byzantine 模型**只在「參與節點可能說謊或被攻陷、且後果嚴重」時才值得：跨組織的去中心化帳本、開放的多方計算。把 BFT 套用在「全是自家機房、互相信任」的內部系統上，是典型的 over-engineering——你付出 3 倍以上的節點與訊息成本，去防一個在你威脅模型裡不存在的敵人。

worked example：一個 3 節點叢集，每節點年故障率約 5%（單節點可用性 95%）。若系統設計成「任一節點掛就整體不可用」（fail-stop 串聯），整體可用性 ≈ 0.95³ ≈ 85.7%。若改成「多數存活即可服務」（共識，容忍 1 個故障），整體不可用＝同時 ≥2 個掛，機率 ≈ C(3,2)·0.05²·0.95 + 0.05³ ≈ 0.007125 + 0.000125 ≈ 0.725%，可用性 ≈ 99.28%。同樣三台機器，把失敗模型從「全活才行」換成「多數活就行」，把停機從約 14.3% 壓到約 0.73%。

### 常見誤解與陷阱

- **「逾時到了就一定死了」**：最危險的假設。逾時只代表「沒在我等的窗口內回應」。在它其實活著時就接手它的工作 → split-brain、雙寫。任何「接手」動作必須配 fencing（見「分散式鎖」，本領域另一檔）或共識，不能單憑逾時。
- **把 partial failure 當 all-or-nothing**：以為「網路斷了就是兩邊都知道斷了」。實際上分區（partition）時，兩邊各自可能都以為對方死了、自己是唯一活著的——這正是 split-brain 的溫床。
- **重試卻不冪等**：承認 partial failure 就會重試，但重試一個非冪等操作（扣款、發貨）會在「請求其實成功了、只是回應丟了」時造成重複。重試的前提是冪等（見領域 A）。
- **誤用 Byzantine**：把「節點可能回傳錯資料（因為 bug）」當成 Byzantine 而上 BFT。bug 導致的錯誤不是惡意對手，用測試、校驗和、對帳（見領域 L）解，比 BFT 便宜得多。

### 延伸閱讀

- Fischer, Lynch, Paterson, "Impossibility of Distributed Consensus with One Faulty Process", JACM 32(2):374-382, 1985（FLP 不可能性，partial failure 下共識的根本侷限）: https://dl.acm.org/doi/10.1145/3149.214121
- Lamport, Shostak, Pease, "The Byzantine Generals Problem", ACM TOPLAS 4(3):382-401, 1982（n≥3m+1 下界）: https://dl.acm.org/doi/10.1145/357172.357176

## 共識 consensus

### 定義與原理

共識（consensus）解的問題：**一組節點，在部分故障與不可靠網路下，對「某個值」達成不可推翻的一致決定**。這個「值」在實務上通常不是單一數字，而是**一份 replicated log（複製日誌）裡下一筆要追加的條目**——也就是「狀態機複製（state machine replication）」：所有節點對同一份指令序列達成一致，按同序套用，於是所有節點的狀態收斂相同。「對 log 的下一個位置放什麼達成共識」反覆做，就構成了一個強一致的複製系統。

共識協定必須同時滿足三個性質：**agreement**（所有正確節點決定同一個值）、**validity/integrity**（決定的值來自某個被提議的值，不憑空捏造）、**termination**（最終會決定，不會永遠卡住）。FLP 不可能性（Fischer-Lynch-Paterson 1985）證明了：在完全非同步的網路裡，只要有一個節點可能崩潰，就**沒有**確定性協定能同時保證這三者——因為你永遠無法區分「崩潰的節點」和「很慢的節點」。實務協定靠引入**逾時（部分同步假設）**繞過：放棄「在最壞情況下保證 termination」，換取「在網路最終穩定下保證 termination」，但**任何時候都不犧牲 agreement**（安全性絕不妥協，活性靠運氣與逾時）。

### 解法空間

達成共識的主流協定家族：

- **Paxos**（Lamport，"The Part-Time Parliament", ACM TOCS 16(2):133-169, 1998）：理論上的奠基者。單值 Paxos（Synod）以 proposer/acceptor/learner 角色、兩階段（prepare/accept）＋ proposal number 達成單一值共識；**Multi-Paxos** 把它擴展成連續 log，並用穩定 leader 省掉每筆的 prepare 階段。以難懂著稱。
- **Raft**（Ongaro-Ousterhout，"In Search of an Understandable Consensus Algorithm", USENIX ATC 2014）：刻意為「可理解」設計，把共識拆成三個相對獨立的子問題——**leader election、log replication、safety**。功能上等價於 Multi-Paxos、效率相當，但結構更清楚，是近十年新系統的主流選擇。
- **Zab（ZooKeeper Atomic Broadcast）**：ZooKeeper 專用，為「穩定 leader 廣播有序更新」這個特例最佳化，與 Paxos 同類但獨立設計。
- **Viewstamped Replication（VR）**：與 Paxos 同期、思路相近的早期協定，近年重新受重視。
- **BFT 共識（PBFT、各式區塊鏈協定）**：把共識推廣到容忍惡意節點，代價是更多節點與訊息輪次。

### 各方案的保證與取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Paxos / Multi-Paxos | 多數存活下安全 + 最終進展 | 理論基準；Google Chubby/Spanner 等 | 規格留白多、難正確實作；論文不直接給工程藍圖 |
| Raft | 同 Multi-Paxos，且強 leader、log 不允許空洞 | 多數新系統的預設（見下方實作） | 強 leader ＝寫入吞吐受單 leader 上限約束 |
| Zab | 為 ZooKeeper 的有序廣播最佳化 | 協調服務（watch、有序事件） | 與通用共識耦合在 ZooKeeper，不獨立取用 |
| BFT 共識 | 容忍 m 個惡意節點（n≥3m+1） | 互不信任多方、公鏈 | 訊息複雜度高、節點數多、延遲大 |

實作映射（2026-06）：**etcd**（Kubernetes 的後端儲存）、**Consul**、**TiKV** 用 Raft；**Kafka** 自 KRaft 起以 Raft 取代 ZooKeeper 做 controller metadata 的共識（KRaft 在新版已是預設）；**ZooKeeper** 用 Zab；Google **Chubby/Spanner** 用 Paxos 系。

### 何時需要

共識**昂貴**——每個決定都要等過半節點持久化並確認（一個跨可用區的 RTT 量級），且少數派被擋住無法寫入。所以共識只用在「**少量、關鍵、必須全域唯一一致**」的決定上：**誰是 leader、叢集成員資格、分片路由表、分散式鎖的持有者、設定的當前版本**。它**不該**用在高吞吐的業務資料路徑上——你不會讓每筆使用者請求都跑一輪共識。

worked example：一個 5 節點 Raft 叢集，quorum＝3。假設每次寫入需 leader 把條目持久化、平行送給其餘 4 個 follower、收到任意 2 個 follower 的 ack（湊滿含 leader 的 3）。若節點間單程網路延遲 1 ms、fsync 約 5 ms，一次提交延遲 ≈ max(本地 fsync 5ms, 1ms 送出 + follower fsync 5ms + 1ms ack) ≈ 約 7 ms。即使吞吐做到單 leader 每秒上萬筆，這個延遲下限決定了「每筆使用者交易都走共識」在高 QPS 下不可行——共識管的是 metadata，不是 payload。

### 常見誤解與陷阱

- **「共識＝強一致＝慢，所以避開它」**：誤把共識當成所有跨機操作都要付的稅。正解是「把需要共識的決定縮到最小集合」，其餘走複製/quorum/最終一致。
- **以為 Raft「等價 Multi-Paxos」就等於兩者可互換實作**：等價指的是達成的保證等價，不代表你能隨意混用其工程細節。Raft 的「log 不允許空洞、強 leader」是它可理解性的來源，也是它的約束。
- **自己手刻共識**：Paxos 規格留白極多、Raft 看似簡單但邊角（log 截斷、成員變更、快照、term 持久化）多到容易出安全性漏洞。生產上幾乎總是用成熟函式庫/系統（etcd、其 raft 函式庫等），不自刻。
- **誤以為共識能在網路分區時兩邊都繼續寫**：共識在分區時**只允許多數派那一邊進展**，少數派停寫。這是 CAP 裡選 C 棄 A 的具體呈現（見領域 B 的 CAP/PACELC）。
- **把「leader 還在」當成「leader 一定收到了我的寫」**：寫入只有在被多數持久化後才算 committed；leader 在 commit 前崩潰，該寫可能丟失，client 必須靠「未收到成功回應就重試 + 冪等」處理。

### 延伸閱讀

- Ongaro, Ousterhout, "In Search of an Understandable Consensus Algorithm", USENIX ATC 2014: https://raft.github.io/raft.pdf
- Raft 官方網站（含視覺化、實作清單）: https://raft.github.io/
- Lamport, "The Part-Time Parliament", ACM TOCS 16(2):133-169, 1998: https://lamport.azurewebsites.net/pubs/lamport-paxos.pdf
- Lamport, "Paxos Made Simple", 2001: https://lamport.azurewebsites.net/pubs/paxos-simple.pdf

## leader election

### 定義與原理

許多複製協定（尤其 Raft、Multi-Paxos、主從複製）需要一個**唯一的 leader（主節點）**：所有寫入經由它排序，避免多個節點同時對同一份 log 寫入造成衝突。**leader election** 解的問題：在沒有中央仲裁者、且節點會崩潰/復活、訊息會延遲的環境下，**選出且只選出一個 leader，並在它失效時自動換人**。難點不在「選出一個」，而在「**保證任一時刻最多一個有效 leader**」——若兩個節點同時自認 leader（split-brain），各自接受寫入，資料就分岔了。

Raft 的機制是教科書範例：時間切成遞增的 **term（任期，邏輯時鐘）**，每個 term 至多一個 leader。每個 follower 維持一個**隨機化的 election timeout**（典型 150–300 ms），收到 leader 心跳（空的 AppendEntries）就重置；逾時沒收到，就遞增自己的 term、轉為 candidate、向所有人發 RequestVote。**每個節點在一個 term 內只投一票**，candidate 收到**過半票**即成為該 term 的 leader。隨機化逾時是關鍵：它讓節點不會同時超時開選（避免持續 split vote／平票），通常一個節點先超時、先拿到多數、先發心跳壓住其他人。term 號則保證舊 leader 復活時，它的陳舊 term 會被拒絕——它一看到更高的 term 就自動退位成 follower。

### 解法空間

- **共識內建的選舉（Raft term + 隨機逾時 + 多數投票）**：選舉與 log 安全性綁在一起（Raft 還要求「只有 log 夠新的 candidate 才可能當選」，確保已 committed 的條目不丟）。最穩，但要整套共識。
- **靠外部協調服務搶租約（lease）**：把選 leader 外包給 ZooKeeper/etcd——所有候選者去搶建同一個 ephemeral key／lock，搶到者持有有時限的 **lease（租約）**並定期續租，沒續到就釋放、觸發重選。應用層不必自己實作共識。
- **Bully / Ring 等經典演算法**：以節點 ID 大小或環狀傳遞選出 leader。理論教材常見，但對 partial failure 的處理較弱，生產少用。
- **固定/手動指定 + 故障切換**：主從資料庫常見——主由設定指定，故障時由哨兵/operator 提升某個 replica。簡單，但切換決策本身需要防 split-brain（見陷阱）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Raft 內建選舉 | 每 term 至多一 leader + 不丟 committed log | 自身就是共識系統 | 須完整共識；選舉期間（typ. 數百 ms）無 leader、寫入暫停 |
| 外部 lease（ZK/etcd） | 至多一持租者（在時鐘假設成立下） | 應用層要選 leader 但不想自刻共識 | 依賴外部服務可用；lease 過期判定受時鐘漂移影響 |
| Bully / Ring | 邏輯上選出唯一 leader | 教學、受控環境 | 對訊息遺失/分區韌性弱 | 
| 主從 + 哨兵切換 | 故障時提升 replica | 傳統關聯式/Redis 主從 | 切換邏輯本身要防雙主；需 fencing |

### 何時需要

需要 leader election 的訊號是「**這個角色必須全域唯一**」：唯一的寫入排序者、唯一的排程觸發者、唯一的某資源協調者。若你的工作天生可由多個 worker 平行無協調地做（無狀態、冪等、無需排序），就**不要**引入 leader——它增加選舉延遲、複雜度與單點瓶頸。常見落點：資料庫主節點、分散式工作排程器的「誰來觸發」、有狀態服務的 primary。

worked example：Raft 叢集 election timeout 設 [150, 300] ms、心跳間隔 50 ms。leader 崩潰後，follower 平均約 (150+300)/2 ≈ 225 ms 才超時開選，加一輪 RequestVote 往返（~1–2 ms）與成為 leader 後首個心跳，故障切換的「無 leader 寫入暫停窗」典型在約 150–300 ms 量級。若把 election timeout 設太小（如 20 ms），網路抖動就頻繁誤判 leader 死亡、反覆改選（election storm）；設太大（如 5 s），故障切換變慢、可用性下降。150–300 ms 是論文以實驗權衡出的範圍。

### 常見誤解與陷阱

- **split-brain（雙主）**：最核心的失敗。網路分區後，舊 leader 在少數派側仍自認是 leader 並繼續接寫，新 leader 在多數派側選出——兩邊都寫。防法：寫入必須驗證「我仍持有當前 term/lease 的多數認可」，且接手者要用 fencing token 讓舊 leader 的陳舊寫入被下游拒絕（見「分散式鎖」，本領域另一檔）。
- **以為「持有 lease」＝「現在仍是 leader」**：lease 是過去某刻拿到的，到你執行寫入時可能已因 GC 暫停、時鐘跳動而過期、別人已接手。lease 必須配 fencing，不能只靠「我記得我有 lease」。
- **election timeout 不隨機化**：所有節點同時超時 → 持續平票、選不出 leader。隨機化是打破對稱的關鍵。
- **選舉與資料新鮮度脫鉤**：若允許 log 落後的節點當選，已 committed 的資料會被它的舊 log 覆蓋而丟失。Raft 的「投票限制」（只投給 log 至少和自己一樣新的 candidate）正是防這個。
- **把 leader 當成永不換**：leader 會因 GC 暫停、網路抖動被誤判而換人；系統其餘部分必須容忍 leader 隨時更替、寫入短暫不可用，不能假設 leader 恆定。

### 延伸閱讀

- Raft 論文第 5.2 節（Leader election）: https://raft.github.io/raft.pdf
- Raft 視覺化（觀察隨機逾時與選舉）: https://raft.github.io/
- Lamport, "Paxos Made Simple"（distinguished proposer 的角色）: https://lamport.azurewebsites.net/pubs/paxos-simple.pdf

## quorum（R + W > N）

### 定義與原理

quorum（法定數）是一種**不靠單一 leader、靠「多數重疊」達成一致**的複製機制，常見於無主（leaderless）複製。把資料複製到 **N** 個副本，每次寫入要求至少 **W** 個副本確認成功才算成功，每次讀取至少向 **R** 個副本查詢。核心不等式：

**R + W > N**

它的威力來自鴿巢原理：任一組「W 個寫過的副本」和任一組「R 個讀的副本」**必然至少有一個交集**——因為 W + R 個位置擠進 N 個槽，超過 N 就一定有重疊。那個交集副本持有最新的寫，於是讀取**至少看得到最新版本**（再靠版本號/時間戳在 R 個回應中挑出最新的）。這保證了「讀得到最近一次成功的寫」，而**不需要每個副本都同步**——只要多數派重疊即可。

另一條相關不等式 **W > N/2**（寫 quorum 過半）保證**兩次寫之間也重疊**，避免兩個並行寫各自只達到不重疊的副本集而都「成功」、造成無法定序的衝突。

### 解法空間

quorum 是個參數可調的旋鈕，不同 (N, R, W) 給不同取捨：

- **R + W > N（嚴格 quorum）**：保證讀寫重疊、讀得到最新寫。N=3,W=2,R=2 是經典平衡點。
- **W=N, R=1（讀最佳化）**：寫要所有副本、讀只要一個。讀快寫慢，且任一副本掛了就無法寫。
- **W=1, R=N（寫最佳化）**：寫只要一個、讀要全部。寫快讀慢，寫的耐久性差（那一個副本掛了就丟）。
- **R + W ≤ N（放寬 quorum）**：故意不保證重疊，換更高可用與更低延遲，接受最終一致——讀可能讀到舊值，靠讀修復（read repair）與反熵（anti-entropy，本領域另一檔）背景收斂。
- **sloppy quorum + hinted handoff**（Dynamo 式）：分區時，把寫暫存到「本該負責的節點以外的健康節點」上（hinted handoff），先湊滿 W 保住可用性，待原節點恢復再交還。提升可用性，但會**犧牲嚴格 quorum 的重疊保證**。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| R+W>N（如 N3W2R2） | 讀必見最新成功寫 | 要可調一致性的無主儲存 | 並行寫仍可能衝突，需版本向量 + 衝突解決 |
| W=N, R=1 | 讀極快、強讀一致 | 讀多寫極少 | 任一副本不可用即無法寫；寫延遲＝最慢副本 |
| W=1, R=N | 寫極快 | 寫多、可容忍丟失 | 耐久性弱；讀要等最慢副本 |
| R+W≤N（放寬） | 高可用、低延遲、最終一致 | 可容忍讀到舊值的場景 | 讀可能舊；靠 read repair / anti-entropy 收斂 |
| sloppy quorum | 分區時仍可寫 | 極高可用優先（Dynamo 式） | 「W 個確認」可能不含正規副本，重疊保證被打破 |

### 何時需要

quorum 適合**無主、要在一致性與可用性間細調**的場景：Dynamo 式 KV（Cassandra、Riak）、需要「多數確認才算數」的去中心化複製。若你已經有 leader-based 共識（Raft），leader 路徑本身就含 quorum（過半 ack 才 commit），不必另設 R/W。若你的資料就放單一強一致資料庫、靠它的交易保證，也不需要手調 quorum——這是無主複製特有的旋鈕。

worked example：N=3、W=2、R=2，R+W=4>3，重疊保證成立。寫入 key=`x` 到副本 {A,B}（C 暫時沒收到），寫成功。隨後讀取向 {B,C} 查：B 持新值（versioned，較高時間戳/向量）、C 持舊值，讀端比對版本取 B 的新值——正確讀到最新。對照 N=3、W=1、R=1：R+W=2≤3，寫只到 A、讀只問 C，兩者無交集，讀到舊值。可用性算術：N=3,W=2 時寫需 2/3 副本健康，能容忍 1 個故障；若把 W 設成 3，任一副本故障就無法寫——這就是為什麼 W 過大會傷可用性。

### 常見誤解與陷阱

- **以為 R+W>N＝線性一致（強一致）**：不是。它只保證「讀到的版本集合含最新成功寫的版本」，但仍可能讀到尚未收斂的並行寫、或在 sloppy quorum 下完全失去重疊。它是「能讀到最新」而非「全域單一最新」。要線性一致仍需共識。
- **忽略並行寫衝突**：R+W>N 解決「讀寫重疊」，不解決「兩個 client 同時寫不同值」。並行寫需要版本向量（vector clock）或 LWW 等衝突解決策略（見領域 L 的「衝突解決」），否則靜默丟更新。
- **把 sloppy quorum 當嚴格 quorum**：開了 hinted handoff 以求高可用，卻仍假設「W 個確認＝多數正規副本確認」——分區下這個假設破裂，讀可能讀不到剛寫的值。要清楚自己用的是嚴格還是 sloppy。
- **R/W 設定與耐久性混淆**：W=1 寫很快，但若那個副本在複製給其他副本前崩潰，這筆寫就丟了。低 W 換來的低延遲，代價是耐久性窗口。
- **以為 quorum 數字越大越安全**：W、R 拉高會犧牲可用性與延遲；安全與可用是此消彼長，要按業務對「讀到舊值」的容忍度選點。

### 延伸閱讀

- DeCandia 等, "Dynamo: Amazon's Highly Available Key-value Store", SOSP 2007（R/W/N、sloppy quorum、hinted handoff 出處）: https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf
- Apache Cassandra 一致性等級文件（quorum 在生產的可調呈現）: https://cassandra.apache.org/doc/latest/cassandra/architecture/dynamo.html

## 複製策略

### 定義與原理

複製（replication）＝把同一份資料保存在多個節點上，目的有三：**容錯**（一個副本掛了還有別的）、**讀擴展**（讀分散到多副本）、**就近服務**（副本放使用者附近降延遲）。難點全在「**多個副本怎麼保持一致、寫入由誰主導、衝突怎麼處理**」。按「誰能接受寫入」這個維度，複製範式分三類，這是本書複製策略的 owning 條目——機制在此深講一次，領域 B 的「複製延遲」「分片」只講其一致性後果與 DB 操作面。

- **單主（single-leader / primary-backup）**：只有一個 leader 接受寫入，依序把變更（複製日誌）傳給 follower。**所有寫經單一定序點**，所以避免了寫衝突；讀可分散到 follower（但有複製延遲）。
- **多主（multi-leader）**：多個節點都能接受寫入（典型用於多資料中心、各區一個 leader），彼此非同步互相複製。寫入就近、可用性高，但**同一筆資料可能在兩地被並行改**，產生衝突需解決。
- **無主（leaderless，Dynamo 式）**：沒有 leader，client（或協調者）直接對多個副本讀寫，靠 quorum（見「quorum」）保證重疊、靠版本與 read repair 收斂。對節點故障最寬容。

### 解法空間

複製的同步性與衝突處理各有選擇：

- **同步 vs 非同步 vs 半同步複製（單主內部）**：同步＝leader 等 follower 確認才回 client（不丟資料但慢、follower 掛就阻塞）；非同步＝leader 寫完就回（快、但 leader 崩潰時未複製的寫會丟）；半同步＝至少一個 follower 同步、其餘非同步（折衷）。
- **單主的故障切換**：leader 掛了提升某 follower（見「leader election」）；非同步複製下切換可能丟失「leader 已回 client 但未複製」的寫。
- **多主的衝突解決**：LWW（last-write-wins，丟資料但簡單）、版本向量、CRDT（保證收斂、語意受限）——機制見領域 L 的「衝突解決」。
- **無主的讀寫修復**：read repair（讀到不一致就順手修）＋ anti-entropy（背景比對修補，本領域另一檔）。
- **複製拓樸**：鏈式、星狀、全互聯（多主下影響衝突傳播與延遲）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 單主 + 同步複製 | 不丟已確認的寫、無寫衝突 | 強耐久性優先、單區 | follower 慢/掛則寫阻塞；延遲＝最慢同步副本 |
| 單主 + 非同步複製 | 寫低延遲、無寫衝突 | 多數 OLTP 主從 | 切換時可能丟未複製的寫；follower 有複製延遲 |
| 多主 | 各區就近寫、高可用 | 多資料中心、離線優先 | 並行寫衝突必須解（LWW/向量/CRDT）；收斂前不一致 |
| 無主（quorum） | 可調一致性、對節點故障寬容 | Dynamo 式 KV | 需版本 + read repair；sloppy quorum 削弱保證 |

### 何時需要

**預設從單主開始**——它無寫衝突、心智模型最簡單，覆蓋絕大多數需求；讀擴展用 follower、容錯用故障切換。**多主**只在「**多個地理區都要能本地寫、且能接受最終一致與衝突解決成本**」時才值得（跨洲低延遲寫、行動裝置離線編輯後同步）——衝突解決的複雜度被嚴重低估，不要為了「看起來更高可用」就上多主。**無主**適合「**極高可用、可調一致性、KV 型資料**」且團隊願意處理版本與修復機制的場景。錯配的代價：把多主用在「其實只有一個寫入區」上，徒增衝突風險而無收益。

worked example：單主非同步複製，leader 每秒寫 5,000 筆、複製管線把變更傳給跨區 follower，跨區網路延遲 80 ms。某瞬間 leader 崩潰，此時「已寫入 leader 但尚未送達 follower」的窗口約等於 80 ms 的在途量 ≈ 5,000 × 0.08 ≈ 400 筆。若這些寫的 client 已收到成功回應，故障切換到該 follower 後這 400 筆**消失**（client 以為成功、實際丟了）。這就是非同步複製「切換丟資料」的具體量；要消除它得用同步/半同步複製，代價是每筆寫多付一個跨區 RTT。

### 常見誤解與陷阱

- **以為 follower 讀＝即時資料**：單主下 follower 有複製延遲，讀 follower 可能讀到舊值，甚至「寫完立刻讀自己寫的卻讀不到」（讀己之寫違反）。需要時要讀 leader 或做 read-your-writes 路由（一致性後果見領域 B）。
- **多主下低估衝突**：以為「衝突很罕見」。一旦兩地並行改同一鍵，LWW 會靜默丟掉一邊的更新；計數器、集合這類資料用 LWW 會錯，需要 CRDT 或顯式合併。
- **非同步複製＝可能丟資料，卻當成不會丟**：只要 leader 在複製前崩潰，「已對 client 確認」的寫就可能在切換後消失。要「絕不丟已確認寫」必須付同步複製的延遲代價。
- **把複製當備份**：複製是即時同步，刪錯/寫壞會**即時同步到所有副本**。複製防的是節點故障，不防邏輯錯誤與誤刪——那需要時間點備份（見領域 O 的資料生命週期）。
- **混淆複製與分片**：複製是「同一份資料多副本」（解容錯/讀擴展），分片是「不同資料切到不同節點」（解寫擴展/容量）。兩者正交、常同時用（每個分片再各自複製）；分片的一致性與路由面見領域 B。

### 延伸閱讀

- DeCandia 等, "Dynamo: Amazon's Highly Available Key-value Store", SOSP 2007（無主複製原型）: https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf
- PostgreSQL 高可用、負載平衡與複製官方文件（單主同步/非同步的工程呈現）: https://www.postgresql.org/docs/current/high-availability.html

## 2PC 與分散式交易

### 定義與原理

分散式交易要解的問題：**一筆操作跨越多個獨立資源（多個資料庫、或 DB + 訊息佇列），要嘛全部生效、要嘛全部不生效（原子性），不能一半成功一半失敗**。單機交易的 ACID 由單一引擎保證；跨資源就沒有共同引擎了，需要一個協定協調各方一起提交或一起回滾。

**兩階段提交（2PC, Two-Phase Commit）**是經典方案，由一個 **coordinator（協調者）** 主導兩個階段：

1. **prepare（投票）階段**：coordinator 問所有 participant「你能提交嗎？」。每個 participant 做完所有檢查、把變更寫入持久日誌但**先不提交**，鎖住相關資源，回覆 **yes（prepared）** 或 **no**。回了 yes 就進入「**不確定（in-doubt）**」狀態——它承諾「之後 coordinator 叫我 commit 我就一定能 commit」，因此**不能單方面反悔**。
2. **commit/abort（決定）階段**：只要有一個回 no（或逾時），coordinator 決定 abort，通知所有人回滾；全部 yes 才決定 commit，通知所有人提交。

關鍵安全性質：一旦有 participant 回了 yes，它就**不能自己決定**，必須等 coordinator 的最終裁決。這帶來 2PC 的致命弱點——**阻塞（blocking）**。

### 解法空間

跨資源達成一致提交/或繞過它的辦法：

- **2PC（含 XA）**：強原子性，但 coordinator 是單點、會阻塞（見保證取捨）。XA 是 2PC 的標準化介面（多數關聯式 DB、部分訊息中介支援）。
- **3PC（三階段提交，Skeen 1981）**：在 prepare 與 commit 間插一個 pre-commit 階段，理論上消除 2PC 的阻塞——但**只在「無網路分區、僅節點崩潰」的同步假設下成立**，分區時仍可能不一致，且多一輪訊息更慢，生產極少用。
- **共識式原子提交**：把 coordinator 的決定本身用 Raft/Paxos 複製（如 Spanner 的 2PC over Paxos groups），讓「決定」不因 coordinator 單點崩潰而丟失，緩解阻塞。
- **saga（補償交易）**：放棄全域原子性，把長交易拆成一串本地交易，每步配一個「補償動作」回退已完成的步驟，靠最終一致替代原子提交（機制與 choreography/orchestration 取捨見領域 A 的「outbox/saga」）。
- **outbox + 事件**：用本地交易把「業務變更 + 待發事件」原子寫入同一 DB，再非同步可靠投遞，避開跨資源的 dual-write（見領域 A、L）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 2PC / XA | 跨資源原子提交（強一致） | 少數參與者、同機房、低頻關鍵交易 | coordinator 崩潰 → in-doubt participant 鎖資源無限阻塞；同步、慢 |
| 3PC | 同步無分區下不阻塞 | 理論/受控環境 | 分區下仍可能不一致；多一輪訊息；幾無生產採用 |
| 2PC over Paxos | coordinator 決定不丟（緩解阻塞） | 跨分片強一致 DB | 實作複雜；延遲＝多輪共識 + 2PC |
| saga + 補償 | 最終一致、無全域鎖 | 跨微服務長流程 | 中間態可見、補償邏輯難寫且要冪等 |
| outbox + 事件 | 本地原子 + 可靠投遞 | DB 變更要可靠發事件 | 最終一致；消費端要去重（見領域 A） |

### 何時需要

2PC 適合「**參與者少、同機房、低頻但必須原子**」的關鍵操作（如一筆橫跨兩個內部 DB 的資金移轉），且你能接受它在 coordinator 故障時鎖住資源等待人工/恢復。**跨微服務、跨網際網路、高頻**的場景**不要用 2PC**——同步阻塞與單點會在規模下變成系統性風險，改用 saga / outbox / 事件驅動的最終一致（見領域 A、K）。判準：你是否真的需要「同一瞬間全有或全無」的強原子性，還是「最終都會一致、中間態短暫可見」就夠？絕大多數業務流程是後者。

worked example：3 個 participant 的 2PC，每段網路單程 2 ms、各自 prepare 的 fsync 5 ms。正常路徑延遲 ≈ prepare（2ms 送 + 5ms fsync + 2ms 回 ≈ 9ms）+ commit（2 + 5 + 2 ≈ 9ms）≈ 18 ms，期間 3 個 participant 全程持有資源鎖。現在設想 coordinator 在收齊 3 個 yes、剛要送 commit 前崩潰：3 個 participant 都停在 in-doubt，**各自鎖住的資料行無限期鎖住**，直到 coordinator 從持久日誌恢復重發決定（可能數秒～人工介入的數分鐘）。在這段時間，任何想碰這些行的交易全部阻塞——這就是「2PC 的阻塞」具體長什麼樣，也是它在高吞吐下不可接受的原因。

### 常見誤解與陷阱

- **以為 2PC 不會阻塞**：2PC 的核心弱點就是阻塞——coordinator 在「決定」階段崩潰，回了 yes 的 participant 進退不得（不能自行 commit 也不能 abort），鎖住資源等到天荒地老。這不是實作 bug，是協定本身的性質。
- **把 3PC 當「解決了阻塞的 2PC」直接上**：3PC 只在「無網路分區」假設下不阻塞；真實網路會分區，此時 3PC 可能不一致。它換來的「不阻塞」有前提，不是免費。
- **以為「exactly-once 提交＝exactly-once 交付」**：2PC 解的是跨資源的原子提交，不等於跨網路的訊息只送一次。交付語意是另一回事（見領域 A 的交付語意）。
- **saga 的補償當成「就是反向 SQL」**：補償要處理「中間態已被別人看到/依賴」的情況，且補償本身要冪等、要能重試——它比「DELETE 剛才 INSERT 的」複雜得多。
- **忽略 in-doubt 交易的運維成本**：用 XA/2PC 的系統，DBA 必須懂得處理卡住的 in-doubt 交易（手動 commit/rollback、辨識哪些鎖該放）；這是 2PC 隱藏的長期維運稅。
- **把冪等定義在這裡重講**：2PC 的恢復、saga 的補償都依賴冪等，但冪等的定義與冪等鍵生命週期屬領域 A，本條只引用、不重述。

### 延伸閱讀

- Gray, Lamport, "Consensus on Transaction Commit", ACM TODS 31(1):133-160, 2006（把原子提交與共識統一看待）: https://lamport.azurewebsites.net/pubs/consensus-on-transaction-commit.pdf
- Skeen, "Nonblocking Commit Protocols", ACM SIGMOD 1981（3PC 的源頭）: https://dl.acm.org/doi/10.1145/582318.582339
- X/Open XA 規格（分散式交易的標準介面）: https://pubs.opengroup.org/onlinepubs/009680699/toc.pdf
