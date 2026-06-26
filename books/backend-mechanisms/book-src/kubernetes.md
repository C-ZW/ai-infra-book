# Kubernetes：Pod、Service、HPA 與調度

凌晨三點，一台 node 的電源供應器燒了。它上面跑著你的服務的三個 replica，瞬間全沒了。沒有人被叫醒，沒有 PagerDuty 響起。等你早上喝咖啡時翻監控，會看到一段幾分鐘的容量凹陷，然後一切恢復——那三個 replica 在別的 node 上重新長了出來，新的 IP、新的身分，流量自己繞了過去。沒有人按任何按鈕。

這一幕是 Kubernetes 存在的理由，也是理解它的最佳切入點。因為你該問的不是「它怎麼把容器跑起來」——那部分是 container runtime 的事（容器隔離的 namespace/cgroup 原理見〈Docker：容器隔離的原理〉）。你該問的是一個更難的問題：**在那台 node 死掉的瞬間，是誰注意到三個 replica 不見了？是誰決定要補三個回來？是誰決定補到哪些活著的 node 上？又是誰把流量從死掉的 IP 改道到新長出來的 IP？** 這四個「誰」，就是 Kubernetes 的全部。它不是一個容器啟動器，它是一套**讓現實持續向你宣告的意圖收斂**的機器。

## 命令式的死路：為什麼不能只是「啟動三個容器」

先看天真的做法為什麼撐不住。

假設你寫一個腳本：「在這三台機器上各跑一個容器」。這是命令式（imperative）的——你描述**動作**。它在你按下 enter 的那一秒是對的，但它有一個致命的時效性：**它只描述了「現在做什麼」，沒有描述「應該保持什麼」。** 那台 node 的電源燒掉時，沒有任何東西記得「本來應該有三個」。腳本早就執行完、退場了。要恢復，得有個人或某個外部監控發現少了一個、再手動跑一次補容量的腳本——而那個人此刻正在睡覺。

命令式還有一個更陰險的問題：**它不冪等。** 如果補容量的腳本在執行到一半時你不確定它成功了沒，重跑一次可能變成跑了六個容器，少跑一次又只有一個。你永遠要追蹤「現在到底是什麼狀態、我上次做到哪」，而分散式系統裡這種追蹤本身就是不可靠的（命令式 vs 宣告式的這條分野，在基礎設施層也是同一回事，見〈IaC：宣告式、漂移與冪等 apply〉）。

Kubernetes 的第一個、也是最根本的設計選擇，是把這整套翻過來：**你不下動作，你宣告狀態。** 你不說「啟動三個」，你說「我要這個 Deployment 永遠維持三個健康的 replica」。這句話被寫進叢集的一致性儲存——一個跑共識協定的 key-value store（etcd，底下是 Raft，見〈共識：讓一群會當機的機器同意一件事〉）。它是一份**期望狀態（desired state）**，不是一個指令。它不會「執行完就過期」，它**一直在那裡，是一個持續成立的事實宣告**。

宣告了之後，誰來讓它成真？

## 控制迴圈：Kubernetes 真正的引擎

答案是一群 **controller**，每一個都跑同一個三步迴圈，無窮無盡地跑：

```
loop forever:
    observe   -> 讀目前的實際狀態（叢集裡現在有幾個健康 replica？）
    diff      -> 比對期望狀態（我宣告的是幾個？）
    act       -> 採取動作把實際往期望推（少了就建，多了就刪）
```

這叫 **reconciliation loop（調和迴圈）**，是理解 Kubernetes 一切行為的鑰匙。回到開場：那台 node 死掉，它上面三個 Pod 的心跳停了；node controller 在一段逾時後把這個 node 標記為 `NotReady`，把它上面的 Pod 標記為要重建——這段逾時不是即時的：預設要等 node 心跳斷掉約 40 秒（`node-monitor-grace-period`）才標 `NotReady`，再加每個 Pod 自帶的 `unreachable` toleration 預設 300 秒，所以預設配置下從 node 死掉到開始補容量約是五分鐘量級，開場那段凹陷要壓到更短得自己調這些參數；管著那個 Deployment 的 controller 在下一輪 `observe` 時數到「健康 replica 只剩 N−3」，跟期望狀態一比對，`diff` 出缺口，於是 `act`——建立三個新的 Pod。**「自我修復」不是一個被觸發的特殊功能，它只是控制迴圈在差異出現時的自然結果。** 沒有人寫過「node 死掉時補容量」這條規則；存在的只是「實際 < 期望就補」這條恆常的調和邏輯，而 node 死掉只是讓實際 < 期望成立的眾多原因之一。

這裡要釘死一個常被忽略的後果：**控制迴圈是最終一致的，不是即時的。** 從你 apply 一份新的期望狀態，到叢集實際收斂到那個狀態，中間有延遲——觀察有週期、動作要時間、狀態要傳播。`kubectl apply` 回給你的「created」不代表「已就緒」，只代表「你的意圖已被記下」。任何「我改了 YAML 所以現在就生效了」的假設，都是在跟這個收斂延遲對賭。Kubernetes 給的保證是「**最終**會收斂到你宣告的狀態（只要它一直成立）」，不是「立刻」。

理解了這個迴圈，剩下的核心物件——Pod、Service、Scheduler、HPA——都只是「不同的 controller 在調和不同的東西」。我們一個一個拆。

## Pod：會死、且死了不復活的最小單位

Pod 是 Kubernetes 排程與部署的最小單位。它包一個或多個容器，這些容器共用同一個網路 namespace（同一個 IP、彼此可走 `localhost` 互通）與一組儲存 volume。多容器 Pod 最常見的用法是 sidecar——主容器旁邊跑一個輔助容器（收 log、當網路代理），兩者命運綁在一起、一起被排程、一起被殺。

但 Pod 最重要的性質，是一個違反直覺的設計決定：**Pod 是 ephemeral 的，而且死了不會原地復活。** 一個 Pod 掛了，控制迴圈不會「把它救回來」——它會**建一個全新的 Pod 來取代**。新 Pod 有新的名字、新的 IP、新的身分。舊的那個，從叢集的角度，徹底消失了。

這個「不原地復活、而是替換」的選擇，是整個系統可預測性的來源。如果 Pod 可以帶著一身的本地狀態掙扎著半死不活地復活，控制迴圈就得處理無窮多種「壞了一半」的中間態。而「要嘛健康、要嘛被整個替換成一個乾淨的新的」這條鐵律，讓調和邏輯變得簡單：實際狀態裡的每個 Pod 不是 `Ready` 就是該被取代，沒有薛丁格的中間地帶。

代價直接而具體：**Pod 的 IP 一直在變。** 任何一次重建——崩潰、被驅逐、滾動更新換版、被 HPA 縮掉——都會換 IP。於是你幾乎從不直接創建或依賴 Pod。你透過上層 controller（Deployment 管無狀態 replica 與滾動更新，StatefulSet 管需要穩定身分的有狀態服務）來間接管它們。而「IP 一直在變」這件事，立刻逼出下一個問題：**如果後端的 IP 隨時在漂移，前端要怎麼找到它們？**

## Service：給漂移的後端一個不動的地址

這就是 Service 解的問題，而它解的方式比表面上精巧得多。

Service 給「一組會變動的 Pod」一個**穩定的虛擬 IP（ClusterIP）**和一個 DNS 名。前端只認這個固定地址，完全不需要知道後面到底是哪三個、IP 是多少、剛剛換過沒。但這裡有個必須看清的機制問題：**這個虛擬 IP 後面沒有任何一個真實的行程在監聽。** 它不是一個 proxy 伺服器，沒有一台機器叫這個 IP。那流量怎麼到得了真正的 Pod？

關鍵在兩層。第一層是**誰算出「現在哪些 Pod 該收流量」**。Service 用一個 label selector（比如 `app=checkout`）來動態框定它的後端。一個叫 EndpointSlice controller 的 controller 跑著它自己的調和迴圈：持續觀察「哪些 Pod 匹配這個 selector **且目前是 ready 的**」，把這份名單維護成一組 **EndpointSlice** 物件（這是較新的機制，取代了早年那個會在端點數一多就拖垮 API server 的單一 Endpoints 物件；EndpointSlice 自 1.21 起為 stable，而 kube-proxy 在更早的 1.19 就已預設改讀它）。注意「且目前是 ready 的」——一個 Pod 的 readiness probe 失敗時，它的 IP 會被**從 EndpointSlice 移除**，Service 就不再把流量送給它（probe 的設定語意與健康檢查機制見〈health check：liveness 與 readiness〉，這裡只需知道「readiness 決定一個 Pod 在不在 Service 的派送名單上」）。

第二層是**這份名單怎麼變成實際的封包改道**。每個 node 上跑著一個 **kube-proxy**，它監看 EndpointSlice 的變化，並把「要送到這個 ClusterIP 的封包，隨機改寫目的地成名單裡某個真實 Pod IP」這條規則，寫進 node 的核心封包處理層。預設用 **iptables**（透過一連串 DNAT 規則）；較新的、針對大叢集效能設計的 **nftables** 模式自 1.33 起穩定，並成為官方推薦取代 iptables 與 IPVS 的方向；早年的 IPVS 模式已於 1.35 標記為 deprecated。不論哪個後端，本質一樣：**ClusterIP 是個假地址，真正發生的是封包在每個 node 的核心裡被即時改寫目的地、負載均衡到某個活著的 Pod。** 沒有中間的 proxy 跳板，這正是它為什麼快。

把兩層連起來看：一個 Pod 因為 readiness 失敗或被重建而換了 IP，EndpointSlice controller 在它的迴圈裡把名單改掉，每個 node 的 kube-proxy 在它的迴圈裡把封包規則改掉——流量自動繞過死掉的、流向活著的。**整個服務發現，就是兩個控制迴圈在追著現實跑。** 開場那句「流量自己繞了過去」，到這裡你看得到它具體是怎麼繞的了。

## 調度：把一個 Pod 放到哪台機器上

新 Pod 被創建時——不管是初次部署、HPA 擴容、還是 node 死掉後的補容量——有一個還沒回答的問題：它該跑在哪台 node 上？回答這個問題的是 **kube-scheduler**，叢集裡另一個跑調和迴圈的 controller，它專門盯一件事：「有沒有 Pod 還沒被指派 node（`spec.nodeName` 是空的）？」有的話，替它挑一台，然後把選定的 node 寫回去。

挑選分兩個階段，這個兩段式本身是個值得看懂的設計：

**第一階段：過濾（filtering / predicates）——這是個是非題。** 對每一台 node 問一串布林問題，任何一題答「否」就把它淘汰。這台 node 還有足夠的可分配 CPU 與記憶體嗎（`NodeResourcesFit`，比的是 Pod 宣告的 **requests**，不是它實際會用多少）？這台 node 被標記為 unschedulable 了嗎？Pod 要求的 volume 能在這台掛載嗎？Pod 的 nodeSelector、affinity、taint/toleration 約束容許這台嗎？跑完一輪，你得到一份「可行 node」的子集。如果這份子集是空的——沒有任何 node 同時滿足所有硬條件——這個 Pod 就卡在 `Pending`，永遠排不出去，直到有 node 騰出空間或你放寬約束。**這是最常見的「我的 Pod 為什麼一直 Pending」的根因，而它幾乎總是 requests 設太大、叢集裝不下。**

**第二階段：評分（scoring / priorities）——這是個排名題。** 在通過過濾的 node 裡，每台被一組評分函式打分（如「優先選資源最空的 node 來分散負載」「優先選已經有這個 image 的 node 來省下拉取時間」），加權加總，**分數最高的勝出**。並列時隨機選一個避免熱點。

選定之後是**綁定（binding）**：scheduler 把 `node X` 寫進這個 Pod 的 `spec.nodeName`，存回 etcd。注意——**scheduler 到此就收工了，它從不親自啟動任何容器。** 它只是做了一個決定並寫下來。真正啟動容器的是那台被選中的 node 上的 kubelet，它在自己的調和迴圈裡看到「有個 Pod 的 `nodeName` 指到我、但還沒在我這跑起來」，於是去拉 image、套上 namespace 與 cgroup、把容器跑起來。**決策（scheduler）與執行（kubelet）徹底分離，各自是獨立的控制迴圈，靠 etcd 裡的那筆 `nodeName` 當交接點。** 這種「把意圖寫進共享儲存、讓另一個迴圈去實現」的模式，你會發現它在 Kubernetes 裡無處不在——它就是控制迴圈架構的指紋。

## HPA：讓 replica 數自己追著負載跑

到這裡，replica 數還是你寫死在 Deployment 裡的固定值。**HorizontalPodAutoscaler（HPA）** 讓它變成一個會自己調整的活數字：盯著某個指標（CPU 使用率、記憶體、或自訂/外部指標），負載上來就加 replica，退去就減。它當然也是個控制迴圈，預設每 15 秒跑一輪。

它每一輪算「該有幾個 replica」的公式，乾淨到可以手算：

```
desiredReplicas = ceil( currentReplicas × currentMetric / targetMetric )
```

把真實數字代進去走一遍。一個 Deployment 設了 HPA，目標是「CPU 平均使用率 50%」，目前跑 4 個 replica，這一輪量到平均 CPU 是 80%：

```
desiredReplicas = ceil( 4 × 80 / 50 )
                = ceil( 6.4 )
                = 7
```

HPA 把 replica 拉到 7。直覺檢查一下這個數字對不對：本來 4 個 replica 扛著相當於「4 × 80% = 320 個百分點」的總負載；攤到 7 個 replica 上，每個約 `320 / 7 ≈ 45.7%`，壓回 50% 以下，穩住。公式做的就是這個反比換算——要把指標除以一個倍率，replica 就乘上同一個倍率。反過來，若這一輪量到的是 25%：

```
desiredReplicas = ceil( 4 × 25 / 50 ) = ceil( 2 ) = 2
```

縮到 2 個。

但這個乾淨公式藏著三個非顯然的細節，每一個都是真實事故的來源。

**第一，靠近目標時它刻意不動。** 如果照公式算出來的倍率非常接近 1.0（預設容差 tolerance 是 0.1，即在 ±10% 內），HPA **什麼都不做**。為什麼要有這個死區？因為指標天生會抖——CPU 在 49% 和 52% 之間來回跳是常態。沒有這個容差，HPA 會在 4 個和 5 個 replica 之間無止盡地反覆擴縮（thrashing），每次擴縮都要起 Pod、排程、暖機，光是抖動本身就把系統搞垮。容差是用「不對微小偏差反應」換「不抖動」。

**第二，scale-up 快、scale-down 慢，而且是故意的不對稱。** 突發流量打進來時你希望 HPA 立刻擴容，慢一秒都是在掉請求；但流量退去時你**不**希望它立刻縮容，因為「退去」可能只是一個短暫的低谷，縮完馬上又要擴回來，又是一輪 thrashing。所以 scale-down 預設有一個 **300 秒的穩定視窗（stabilization window）**：HPA 會回看過去 5 分鐘裡所有「該縮到幾個」的建議，**取其中最大的那個**當這一輪的目標。意思是只有當「該縮容」這件事**持續成立了整整五分鐘**，它才真的縮。突發流量退去後 replica 不會立刻掉回去——這不是 bug，是刻意的保守，用「多撐五分鐘的資源」換「不被假性低谷騙到」。

**第三，量不到指標時它往安全的方向猜。** 如果某些 Pod 剛起來、metrics 還沒收集到，HPA 不會把它們當 0 一律忽略——那會算錯。它的處理是**往保守方向偏**：在考慮 scale-down 時，假設這些缺資料的 Pod「滿載到目標值」（這樣算出來的平均偏高，就不會貿然縮容，免得縮掉其實在忙的 Pod）；在考慮 scale-up 時，假設它們「用量是 0」（這樣算出來的平均偏低，就不會貿然擴容，免得替還沒準備好的 Pod 過度反應）。兩個方向都選「讓擴縮幅度變小」的那個假設。整套 HPA 的設計哲學，到這裡看得很清楚了：**寧可反應遲鈍一點、也絕不亂動。** 因為一個會誤判而瘋狂擴縮的 autoscaler，比一個反應慢半拍的 autoscaler 危險得多。

這裡也藏著 HPA 最常見的失效：**它預設拿 CPU 當訊號，但很多服務的瓶頸根本不是 CPU。** 一個大量等待下游回應的 I/O bound 服務，過載時 CPU 可能一直很低——HPA 看著低 CPU，永遠不擴容，而請求已經在佇列裡堆積、延遲飆高、使用者超時。CPU 沒動，但服務早就垮了。對這種服務，該餵給 HPA 的訊號是佇列長度、p99 延遲、或每秒請求數這類自訂/外部指標，而不是預設的 CPU。**拿 CPU 當萬用擴容訊號，是把「機器忙不忙」誤當成「服務撐不撐得住」。**

## 它會在哪裡騙你

把上面四塊機制串起來，幾個最容易咬人的邊界情況浮出水面。它們的共同點是：**每一個都來自「控制迴圈是最終一致、有延遲」這個本性，而不是來自某個 bug。**

**CPU 限制讓你慢，記憶體限制讓你死——兩種失敗模式天差地別。** 你給 Pod 設 resource limits 時，CPU 和記憶體的超額行為**完全不對稱**，而這個不對稱坑過無數人。CPU 是可壓縮資源：超過 limit，核心的 CFS 排程器**throttle 它**——在每個排程週期（預設 100 ms）裡，一旦用光配額，這個容器在該週期剩下的時間就拿不到 CPU，被掐住、變慢，但**不會死**。記憶體是不可壓縮資源：超過 limit，沒有「慢一點」這個選項，核心的 OOM killer 直接用 SIGKILL **處決**這個容器，退出碼 137（128 + 9）。沒有 graceful、沒有 `OutOfMemoryError`、容器當場消失被重建。所以同樣是「超過 limit」，CPU 的症狀是「服務莫名變慢、p99 飆高但沒重啟」，記憶體的症狀是「Pod 反覆 OOMKilled、進入 crash loop」。把這兩個混為一談，會讓你在排查時往完全錯誤的方向找。記憶體 limit 設太低尤其陰險——它不是讓你慢，是無預警地殺，而且殺的是整個容器。

**滾動更新時，流量會打到一個正在關機的 Pod 上。** 這是 Kubernetes 裡最經典、也最容易被忽略的 race condition。當一個 Pod 要被終止（換版、縮容），兩件事**同時、非同步**發生：(a) 控制平面開始把它的 IP 從 EndpointSlice 移除、各 node 的 kube-proxy 開始更新封包規則；(b) kubelet 對它送出 SIGTERM 開始走終止流程（預設 `terminationGracePeriodSeconds` 是 30 秒，超時才 SIGKILL）。問題在於這兩件事**沒有先後保證**——(b) 可能跑得比 (a) 快。在「IP 還沒從所有 node 的 kube-proxy 規則裡清乾淨」的那個窗口裡，仍有封包被改道到這個已經開始關機、可能已經停止 accept 新連線的 Pod，client 拿到的是 connection refused。你以為「Pod 在終止前會先停止收流量」，但**端點移除的傳播和終止信號的送達是兩條獨立、不同步的迴圈**。正解不是在 Kubernetes 層解決，而是在應用層配合：收到 SIGTERM 後不要立刻關 listener，先撐一段時間繼續服務在途與殘留的請求，等 (a) 那條迴圈傳播完成（這正是 graceful shutdown 要解的事，見〈graceful shutdown：怎麼好好地關掉一個行程〉）。這個 race 是「兩個控制迴圈沒有彼此同步」的直接後果。

**probe 綠燈，不代表服務是對的。** Service 用 readiness probe 決定一個 Pod 在不在派送名單上。但 probe 探的通常只是「行程活著、能回 HTTP 200」。一個 readiness 端點若只回靜態的 200、不去檢查它依賴的資料庫連線通不通，那麼資料庫掛掉時，這個 Pod 照樣對外宣稱 ready、照樣被留在 EndpointSlice 裡收流量，然後把每一個請求都打成 500。**probe 全綠的服務，可以一邊宣稱健康、一邊算錯每一筆帳。** 反過來，liveness probe 設得太敏感、又把外部依賴綁進探測邏輯，會引發另一種災難：某個下游暫時變慢，導致一整批 Pod 的 liveness 同時失敗、同時被殺、同時重建——把一次「暫時的慢」放大成「全面的 crash loop」。liveness 該只問「我自己卡死了沒」，把「下游通不通」留給 readiness（這兩種 probe 的職責劃分為何如此，見〈health check：liveness 與 readiness〉）。

**Pod 沒有穩定身分，把狀態寄望在本地等於把狀態寄望在隨時會被格式化的硬碟上。** Deployment 管的 Pod 重建就換 IP、換名字、可寫層清空。任何寫進容器本地檔案系統的東西，隨容器銷毀而蒸發。需要跨重建存活的狀態，要外放到 volume、資料庫、物件儲存，或改用提供穩定網路身分與儲存的 StatefulSet。把 Kubernetes 的 Pod 當成一台「一直在那裡的伺服器」來用，是最深的觀念誤植——它的整個設計前提就是「Pod 可以、而且會、隨時被換掉」。

## 什麼時候不該用它

值得誠實說一句：上面這套機制的威力，是有代價的，而且代價是複雜度。網路（CNI 外掛）、儲存（CSI 外掛）、權限（RBAC）、Ingress、各式 controller……自己營運一個生產級叢集是一份全職工作量。

所以選不選 Kubernetes，判準從來不是「它先不先進」，而是「**你的規模與動態性，值不值得這套複雜度**」。三個服務、流量平穩、團隊四個人——一台 VM 配上 systemd，可能比一個 Kubernetes 叢集更可靠、更省心，因為你不需要的那些 controller 也就不會在某個凌晨用你沒讀懂的方式壞掉。反過來，三十個服務、流量起伏劇烈、一天部署好幾次、要頻繁失效轉移——這時 Kubernetes 抹平的營運成本才回得了本，那套複雜度買到的自動化才划算。把一個耦合很深的單體硬塞進 Kubernetes，你得到的不是一個現代化的系統，而是一個難搞的單體**外加**一層 Kubernetes 複雜度。**它解的是編排問題，不解你應用本身的架構問題。**

## 為什麼是這個形狀

退一步看，Pod、Service、Scheduler、HPA 看似各管各的，但它們其實是**同一個答案的四個切面**。

那個答案是：**在一個機器隨時會死、IP 隨時會變、負載隨時會變的世界裡，唯一能擴展的協調方式，是放棄「下達命令」、改成「宣告意圖 + 讓無數個控制迴圈持續把現實往意圖收斂」。** Pod 之所以死了不復活而是被替換，是為了讓「實際狀態」永遠是一組乾淨、可判定的事實，讓調和邏輯不必處理半死不活的中間態。Service 之所以是個沒有實體的虛擬 IP、靠 EndpointSlice 與 kube-proxy 兩個迴圈在背後改道，是為了讓「後端會漂移」這個必然，不洩漏給前端。Scheduler 之所以只做決定、寫下 `nodeName` 就收工、把執行丟給 kubelet，是因為「決策」和「執行」拆成兩個獨立迴圈、用共享儲存交接，整個系統才能在任何一環崩潰時各自重試、各自收斂。HPA 之所以反應遲鈍、寧可多撐五分鐘也不亂縮，是因為一個會誤判的自動化系統比一個慢半拍的危險。

這就是為什麼開場那台 node 在凌晨三點燒掉時，沒有人需要醒來。不是因為有人寫了「node 死掉時補容量」這條規則，而是因為整個系統根本沒有「事件 → 反應」這種命令式的思路。它只有一個恆常成立的事實宣告（「我要三個健康 replica」），和一群永不停歇、不知疲倦地把現實往這個事實推的迴圈。node 死掉只是讓現實偏離了事實，而把偏離拉回來，是這些迴圈醒著時唯一在做的事。理解了「一切都是控制迴圈」，你就握住了 Kubernetes 所有行為——包括它所有令人困惑的延遲、race、與最終一致性——的那把總鑰匙。

## 延伸閱讀

- Kubernetes — Pods（官方概念，Pod 的生命週期與 ephemeral 本質）: https://kubernetes.io/docs/concepts/workloads/pods/
- Kubernetes — Service（官方概念，ClusterIP 與虛擬 IP 機制）: https://kubernetes.io/docs/concepts/services-networking/service/
- Kubernetes — EndpointSlices（官方，取代 Endpoints 的端點追蹤機制）: https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/
- Kubernetes — Virtual IPs and Service Proxies（官方，kube-proxy 的 iptables/IPVS/nftables 模式）: https://kubernetes.io/docs/reference/networking/virtual-ips/
- Kubernetes — Horizontal Pod Autoscaling（官方，含 desiredReplicas 公式、tolerance、缺指標的保守處理）: https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/
- Kubernetes — Kubernetes Scheduler（官方，filtering 與 scoring 兩階段）: https://kubernetes.io/docs/concepts/scheduling-eviction/kube-scheduler/
- Kubernetes — Pod Lifecycle（官方，termination 流程、SIGTERM 與 grace period）: https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- Kubernetes — Resource Management for Pods and Containers（官方，requests/limits 與 CPU throttle vs OOM）: https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
