# graceful shutdown：怎麼好好地關掉一個行程

一個服務每天被關掉幾十次，而它從來不是因為壞了。新版本上線、節點要重開、自動縮容把多餘的副本收回去——在容器化的世界裡，「關掉一個行程」是高頻、例行、健康系統的常態動作，不是異常。正因為它太routine，很多人沒認真想過：當編排器決定收掉你這個副本的那一刻，你手上那幾十個正在跑的請求、那幾條剛從佇列拉出來還沒處理完的訊息、那些客戶端開著的長連線，會怎麼樣？

天真的答案是「行程退出，作業系統把它的資源全收回去，沒事」。在單機時代這大致說得過去——你按 Ctrl-C，shell 送個訊號，程式就沒了。但在一個前面掛著負載均衡、後面接著資料庫和訊息佇列的線上服務裡，「行程突然消失」會在四個方向同時漏水：正在處理到一半的請求，連線被硬生生重置，使用者看到 502 或 connection reset；一筆寫了一半的交易，留下一個不上不下的中間狀態；一條從佇列拉出來、處理到 80% 卻還沒 ack 的訊息，憑空蒸發或被重投；一個還握在手裡的資料庫連線、檔案鎖、分散式租約，沒人去釋放。這些都不是「服務壞了」造成的，而是「服務正常下線」時，沒有人替這些半成品收尾。

graceful shutdown 要解的就是這件事：把「結束」從一個**瞬間的斷裂**，變成一段**有序的退場**。它的形狀其實只有一句話——**先停止接新工作，把手上的工作做完或安全交還，釋放資源，然後才退出**——但這句話裡的每一個動詞，落到分散式環境裡都藏著一個會咬人的細節。

## 結束不是你說了算：訊號是一場談判

要理解退場為什麼難，得先看清楚「關掉行程」這個動作底下到底發生了什麼。在 Unix 的世界裡，沒有人能直接「殺死」一個還在跑的行程然後期待它善後——你能做的是**送一個訊號**，而訊號的本質是一場談判。

談判有兩種語氣。**SIGTERM（訊號 15）**是禮貌的那一種：它的意思是「請你停下來」。關鍵在於「請」——SIGTERM 是可以被行程**捕捉、處理、甚至忽略**的。一個寫好退場邏輯的程式，會註冊一個 SIGTERM 的處理器（handler），在收到訊號時不是立刻死，而是觸發一整套收尾流程。這正是 graceful shutdown 所有可能性的起點：你之所以能「好好地」關掉一個行程，前提是這個行程**願意聽**那聲「請」。

另一種語氣是 **SIGKILL（訊號 9）**，它不談判。SIGKILL **無法被捕捉、無法被阻擋、無法被忽略**——核心（kernel）直接把行程從排程器上抹掉，不給任何善後的機會。記憶體裡沒刷出去的東西沒了，握在手上的鎖沒釋放，正在寫的檔案停在半路。SIGKILL 是「時間到了，強制結束」。

於是整個退場機制的骨架就清楚了：**先用 SIGTERM 客氣地請你收尾，給你一段有限的時間；時間一到你還沒走，就用 SIGKILL 把你抬出去。** 這個「有限的時間」是整件事的核心參數——容器世界稱它為**寬限期（grace period）**。Kubernetes 的 `terminationGracePeriodSeconds` 預設是 **30 秒**；單純跑 `docker stop` 的話，Docker 給 Linux 容器的預設寬限期是 **10 秒**（兩者都可調，但預設值差三倍，這本身就值得記住——同一支程式在 K8s 下有 30 秒善後、在 `docker stop` 下只有 10 秒）。在這段時間內，所有的收尾都得做完，否則 SIGKILL 不會跟你商量。

這裡有一個必須講死的前提：**SIGTERM 的善後不是自動的，是你要自己寫的。** 多數 runtime 對 SIGTERM 的「預設行為」就是直接退出——等同於硬斷。如果你的程式沒有主動裝一個 SIGTERM 處理器，那麼「優雅退場」這四個字跟你毫無關係，你每一次部署都在硬斷流量，只是流量不大時你沒注意到而已。優雅退場不是一個你打開的開關，是一段你必須親手寫進程式裡的邏輯。

## 退場的正確順序：為什麼「停止收新工作」必須是第一步

假設你已經捕捉到 SIGTERM 了，接下來要做什麼？順序錯了，前面所有努力都白費。

最常見、也最致命的順序錯誤是：收到 SIGTERM 後，一邊開始把手上的請求做完，一邊**還在繼續接新連線、繼續從佇列拉新訊息**。這是邊關門邊進貨——你永遠關不乾淨，因為新工作進來的速度可能比你清舊工作的速度還快，drain（排空）這件事看不到盡頭，最後寬限期到、SIGKILL 落下，你既沒清完舊的、又斷了一批剛進來的新的，比什麼都不做還糟。

所以退場的**第一個動作必須是「止血」**：停止接受任何新工作。對一個 HTTP 服務，這意味著關掉那個還在 `accept()` 新連線的監聽 socket；對一個訊息消費者，這意味著告訴 broker「別再給我新訊息了」（取消 consumer、停止 prefetch）。只有先把進來的水龍頭關掉，「把手上的工作做完」才有一個確定的、會收斂的終點。

止血之後，才輪到 **drain**：等那些在你按下止血鈕之前就已經進來、正在處理中的工作跑完。HTTP 請求等它回完最後一個 byte，佇列訊息等它處理完並 ack。全部清空了，再釋放連線池、關閉資料庫連線、交還租約，最後乾淨地退出。

```
SIGTERM received
      |
      v
  [1] stop accepting new work     <- 止血：關 listener / cancel consumer
      |
      v
  [2] drain in-flight work        <- 把已進來的請求/訊息做完
      |
      v
  [3] release resources           <- 關連線池、釋放鎖/租約
      |
      v
  [4] exit (before SIGKILL)       <- 趕在寬限期內主動退出
```

這個順序不是風格偏好，是邏輯上的唯一解：止血必須在 drain 之前，否則 drain 不收斂；釋放資源必須在 drain 之後，否則你會在請求還沒回完時就把它要用的連線抽掉。

## 最隱蔽的漏洞：socket 關了，流量還在被導過來

到這裡，退場流程看起來已經很完整了。但分散式環境會在一個你想不到的地方捅一刀，這是整章最值得放慢看的地方。

問題出在「止血」這個動作的**作用範圍**。當你在自己的行程裡關掉監聽 socket、不再 `accept()` 新連線時，你以為「新流量止住了」。但流量不是憑空出現在你 socket 上的——它是負載均衡器或 K8s 的 Service 把它**導**過來的。而那個「把這個副本從流量分發名單裡拿掉」的動作，跟「送 SIGTERM 給你」這兩件事，是**並行發生、各走各的、誰也不等誰**的。

具體看 Kubernetes 的退場流程（2026-06）。當一個 Pod 被標記終止的那一刻，兩條獨立的軌道**同時**啟動：

- **軌道 A（資料面收斂）**：control plane 把這個 Pod 從 Service 的 EndpointSlice 裡標為 terminating。但這只是改了一筆 API 物件——真正讓流量不再進來，需要每個節點上的 kube-proxy 去更新自己的 iptables/IPVS 規則，需要外部負載均衡器去更新它的後端清單。這些更新是**最終一致**的，在小叢集裡是幾十毫秒，在大叢集或慢 LB 上可能要好幾秒。
- **軌道 B（行程收尾）**：kubelet 先跑你設定的 `preStop` hook（如果有），等 preStop 跑完，才對容器主行程送 SIGTERM。寬限期的倒數計時器，是從**標記終止那一刻**就開始走的——preStop 用掉的時間和 SIGTERM 之後的善後時間，**共用同一個寬限期**。

看出那個縫了嗎？**在軌道 A 還沒收斂完之前，軌道 B 可能已經讓你的行程開始關 socket 了。** 這段時間裡，kube-proxy 的 iptables 還指著你、LB 的後端清單還有你，新請求照樣被導過來——而你已經不 `accept()` 了。結果就是這批新請求撞上一個正在關門的 socket，連線被拒、被重置，使用者收到 5xx。最荒謬的是，這些被你硬斷的，全是**部署的瞬間才剛到的新流量**，跟你辛苦 drain 的那些舊請求毫無關係。

修補這個縫的標準手法，是在 `preStop` hook 裡放一個短暫的 sleep（比如 `sleep 5` 到 `sleep 15`）：

```yaml
lifecycle:
  preStop:
    exec:
      command: ["sh", "-c", "sleep 10"]
```

（這個 `exec` 寫法的隱藏前提是映像檔裡有 `sh` 跟 `sleep`——distroless／scratch 這類精簡映像沒有，就會悄悄失效；K8s 1.34 起把 `sleep` 動作收進原生的 lifecycle 機制、由 kubelet 直接執行而不靠容器內的 binary，2026-06 已 GA，可寫成 `preStop: { sleep: { seconds: 10 } }`。）

這個 sleep 什麼業務邏輯都不做，它唯一的作用是**拖延 SIGTERM 的到達**。在這 10 秒裡，行程還活著、還在正常服務，給軌道 A 足夠的時間把 iptables 和 LB 後端都更新乾淨；等 sleep 結束、SIGTERM 才送到、行程才開始關 socket 時，外面早就沒有人把新流量導過來了。一個常被搭配的做法是同時讓 readiness 探針開始回失敗——但要清楚，**readiness 翻 false 本身也只是「觸發」軌道 A，不是讓它瞬間完成**，所以 sleep 那段等待時間仍然省不掉。（readiness 與 liveness 的完整語意是另一個主題，見〈health check：liveness 與 readiness〉。）

這裡有個容易算錯的帳：preStop 的 sleep **算在寬限期裡**。如果你 `terminationGracePeriodSeconds` 設 30 秒、preStop 睡掉 10 秒，那麼真正留給 SIGTERM 之後 drain 的時間只剩 20 秒。sleep 設太長，會把 drain 的額度吃掉，反而讓長請求來不及收尾就被 SIGKILL。這兩段時間是在搶同一個 30 秒。

## 把帳算出來：寬限期到底夠不夠

退場時序聽起來都對，但「夠不夠時間」是個可以手算的問題，算一遍才知道你的設定有沒有埋雷。

設想一個 HTTP 服務，請求耗時的 p99 是 800 毫秒（也就是 99% 的請求在 800ms 內回完，但有 1% 的長尾更久），`terminationGracePeriodSeconds` 用預設 30 秒，preStop 放 `sleep 10`。一次正常部署的時間預算這樣分：

```
grace period budget = 30 s
  preStop sleep        : 10 s   (等資料面收斂，期間仍正常服務)
  ------ SIGTERM 在此送達 ------
  stop accepting + drain: ?      (剩 20 s 給這段)
```

SIGTERM 送到時，行程關掉 listener，剩下的就是把「sleep 期間 + 此刻之前已經收下、還在處理」的請求做完。這些請求最久的也就是長尾那條，p99 在 800ms 內、最壞的拖到 3 秒——遠遠落在剩下的 20 秒裡。所以整個退場大約 13 秒（10 秒 sleep + 約 3 秒 drain）就乾淨收場，零請求被硬斷。寬限期 30 秒綽綽有餘。

現在把一個變數換掉：假設這個服務有一類請求是同步跑一個報表，要 **45 秒**才回。寬限期還是 30 秒。算盤一打就出事——就算這個報表是 SIGTERM 送到前一瞬才剛收下、從頭開始跑，把它 drain 完也要整整 45 秒，但 SIGTERM 之後只剩 20 秒。20 秒一到，SIGKILL 落下，這個報表請求被攔腰砍斷，使用者拿到的是連線中斷。這不是「偶爾運氣不好」，是**每一次部署都會穩定砍斷所有正在跑的長請求**。

結論很硬：**寬限期必須 ≥ preStop 等待時間 + 最長的合理請求時間 + 餘裕。** 預設的 30 秒是給「請求都是亞秒級」的一般 Web 服務用的；任何有長請求、長批次、慢交易的服務，都得自己把 `terminationGracePeriodSeconds` 顯式調大到請求時長之上，否則 graceful shutdown 對你最長的那些請求根本沒生效——而它們往往正是最不該被硬斷的那些。

## drain 自己也得有個盡頭

「等手上的請求全部做完才退」聽起來是 drain 的定義，但它藏著一個會把整個退場拖進深淵的假設：**它假設每個請求最終都會結束。**

如果有一個請求卡死了呢？它在等一個沒設逾時的下游、卡在一個永遠不回的 socket recv 上——那麼「等所有請求做完」這個條件**永遠不會成立**。你的 drain 邏輯會一直等下去，等到寬限期耗盡、SIGKILL 把整個行程連同那些**本來可以好好收尾的其他請求一起**砍掉。一個卡死的請求，因為 drain 沒有自己的上限，就毀掉了所有其他請求的優雅退場。

所以 drain **必須有自己的 deadline**，而且這個 deadline 要明顯短於寬限期。一個合理的退場邏輯是：「等所有 in-flight 請求做完，**但最多只等 N 秒**；N 秒到了還有沒做完的，就放棄它們、主動退出。」這樣最壞情況下你損失的是那幾個本來就卡死的請求，而不是賠上整個行程的善後。drain 的等待，本質上和任何跨行程邊界的等待一樣，沒有上限的等待就是掛起（這正是 timeout/deadline 那一整套機制要解的問題，見〈timeout、deadline 與 budget：把等待變成有界〉）。

## HTTP 的暗坑：關掉 listener 不等於連線會結束

對 HTTP 服務，drain 還有一個比「請求卡死」更隱蔽的陷阱，藏在 HTTP/1.1 的 **keep-alive** 裡。

直覺上你會以為，呼叫 server 的「停止」方法（很多 runtime 叫它 `Server.close()` 之類）就會讓服務優雅地排空。但這類方法的實際語意通常是：**停止接受新的 TCP 連線，並等所有現有連線變成 idle（閒置）後才真正關閉。** 問題是，HTTP/1.1 的 keep-alive 連線**天生就不會自己 idle**——一個連線回完一個請求後，它故意保持開著，等同一個客戶端複用它送下一個請求。在前面掛著負載均衡器的生產環境裡，你和 LB 之間會有一大堆這種長期不關的持久連線。

於是 `Server.close()` 在等一個永遠等不到的條件：它在等連線變 idle，但 keep-alive 連線一直握著、一直「可能還有下一個請求」，所以**它會等到天荒地老**，最後一樣是被 SIGKILL 收掉。這看起來是優雅退場，實際上 keep-alive 把它變成了「優雅地卡住，然後被硬殺」。

真正的解法是主動去結束這些連線，而且要在**請求的邊界**上禮貌地結束，而不是粗暴地把連線一刀切斷。成熟的伺服器（nginx、Envoy 都這麼做）的做法是：進入退場狀態後，對每一個還在用的 keep-alive 連線，在它**下一個請求的回應**裡塞一個 `Connection: close` 標頭。這等於告訴客戶端：「這個請求我照常回給你，但回完之後請把這條連線關掉，下次要送請求請另開一條。」客戶端讀到這個標頭，就會在這次互動結束後乾淨地關掉連線，並把後續請求導去別的、還活著的副本。正在處理的請求一個都不犧牲，連線卻在一個自然的、不會丟資料的邊界上一條條退場。這就是 HTTP 層的「連線排空」——它不是等連線自己死，而是在每個請求邊界主動引導它優雅地謝幕。

## 訊息消費者：退場時「什麼都不做」反而是對的

換到訊息佇列的消費者，退場的邏輯有一個有趣的反轉。

HTTP 服務退場時，你費盡力氣是為了「把進行中的請求**做完**」。但訊息消費者退場時，對於那些已經從 broker 拉出來、卻還沒處理完的訊息，最安全的動作往往是——**什麼都別做，尤其別 ack**。

道理在訊息系統的核心契約裡：一則訊息只有在 consumer 明確 **ack（確認）**之後，broker 才認為它被成功處理、才會把它從佇列裡刪掉。反過來，如果一個 consumer 在 ack 之前就斷線了（無論是崩潰、還是連線關閉），broker 會認定這則訊息**沒被處理完**，於是把它**重新投遞**給另一個還活著的 consumer（RabbitMQ 在 channel/連線關閉時自動 requeue 未 ack 的投遞；SQS 則是 visibility timeout 一過，訊息重新對其他 consumer 可見）。

這個機制讓消費者的優雅退場變得異常乾淨：退場時，你**取消 consumer、停止拉新訊息**（止血），然後對「已經拉出來、處理到一半」的訊息，**故意不 ack 就讓連線關閉**。broker 會自動把它們交還、重投給別人。你不需要在寬限期內把這些半成品硬塞完——你只要把它們安全地「還回去」。

但這個漂亮的交還有一個**前置條件，而且是硬性的**：下游處理必須是**冪等**的。因為「不 ack 就交還」意味著這則訊息**會被處理第二次**——它在你這裡可能已經跑了 80%、產生了一些副作用（扣了庫存、發了一封信），然後又被完整地重投給另一個 consumer 從頭跑一遍。如果處理不冪等，這個「安全交還」就變成了「重複扣款、重複發信」。所以訊息消費者的優雅退場，買到的不是「絕不重複處理」，而是「絕不遺失訊息」——重複的代價，是用下游的冪等性去吸收的（冪等的定義與冪等鍵的設計是另一個主題，見〈重複是常態：冪等與去重〉）。退場時「不 ack 就交還」這招之所以成立，整個建立在「重複處理是可接受的、因為下游能去重」這個假設上；假設不成立，這招就是在製造資料錯誤。

## 容器世界的兩個 PID 1 陷阱：訊號可能根本沒到你手上

前面所有討論都默默假設了一件事：**你的程式真的收到了 SIGTERM。** 在容器裡，這個假設有兩個會無聲破掉的地方，而且它們的症狀一模一樣——你寫了完美的退場邏輯，部署時卻發現每次都是硬斷，因為那聲「請」根本沒傳到你耳朵裡。

第一個陷阱是 **PID 1 的特殊待遇**。容器裡的主行程，行程號通常是 1（PID 1，扮演 init 的角色）。而 Unix 核心對 PID 1 有一條特別規定：**核心不會對 PID 1 套用訊號的「預設動作」。** 一般行程收到 SIGTERM 而沒裝處理器時，核心的預設動作是「終止它」；但 PID 1 不一樣——如果 PID 1 沒有為 SIGTERM **明確註冊處理器**，那麼 SIGTERM 會被**直接忽略**，行程**毫無反應地繼續跑**。結果是：SIGTERM 來了、被無視，行程不退，寬限期白白流逝，最後 SIGKILL 把它硬殺。你的服務看起來「不理會優雅退場」，根因卻是核心對 PID 1 的這條冷僻規則——對一般行程，「不裝處理器」等於「收到就死」；對 PID 1，「不裝處理器」等於「收到就無視」。

第二個陷阱更刁鑽：**訊號送到了 PID 1，但 PID 1 不是你的程式。** 這發生在 Dockerfile 用 **shell 形式**（shell form）寫啟動命令時，例如 `CMD node server.js`（而不是 exec 形式的 `CMD ["node", "server.js"]`）。shell 形式會被包成 `/bin/sh -c "node server.js"`——於是真正的 PID 1 是那個 `sh`，你的 `node` 是它的子行程。當容器停止、SIGTERM 送給 PID 1 時，收到訊號的是 `sh`，而 **`sh` 預設不會把訊號轉發給它的子行程**。你的 node 在底下渾然不覺，從沒看過那聲 SIGTERM，一路跑到 SIGKILL 把整棵行程樹一起砍掉。

這兩個陷阱的共同教訓是：**優雅退場的第一步，是先確認那聲「請」真的會抵達你的程式。** 解法各有對應——用 exec 形式寫 `CMD`／`ENTRYPOINT`，讓你的程式直接當 PID 1 並親自處理訊號；或者在 PID 1 放一個極小的 init（如 tini 或 dumb-init；`docker run --init` 就是自動塞一個 tini 當 PID 1），由它正確接收訊號、轉發給子行程、並順帶回收殭屍行程。但無論用哪個解法，前提都是**先意識到訊號鏈可能在你看不見的地方斷掉**。一個完美的 SIGTERM 處理器，掛在一個收不到 SIGTERM 的行程上，是徹底的零。

## 為什麼是這個形狀

退一步看，graceful shutdown 整套機制的樣貌，都是從一個無法迴避的事實裡長出來的：**你關不掉一個你不能直接控制的行程，你只能「請」它自己關，並準備在它不聽話時強制執行。**

正因為「結束」是一場談判而非命令，所以才有 SIGTERM 那聲客氣的「請」、和 SIGKILL 那記不容商量的截止——以及夾在中間、那段你用來把事情做乾淨的寬限期。正因為善後不是自動的，所以你必須親手寫下「先止血、再 drain、後釋放」的順序，且每一步的順序都不能顛倒。正因為你身處一個資料面最終一致的分散式環境，「我關了 socket」和「外面真的不再送流量給我」之間有一道縫，所以才需要 preStop 那個看似無意義、實則在等資料面收斂的 sleep。正因為等待沒有上限就是掛起，所以連 drain 自己都得有個 deadline。也正因為訊號鏈可能在 PID 1、在 shell 包裝、在 keep-alive 連線這些你看不見的地方無聲斷掉，所以「確認那聲請真的到了」本身，就是退場邏輯的一部分。

下次你看到一次部署平滑切換、舊副本悄無聲息地退場、監控上沒有一根 5xx 的尖刺——那不是因為「關行程本來就很順」，而是因為有人把上面每一道縫都堵上了。graceful shutdown 不是一個函式呼叫，是一套關於「如何在一個你只能請求、不能命令的世界裡，好好地說再見」的紀律。

## 延伸閱讀

- Kubernetes, "Pod Lifecycle"（Termination of Pods，preStop 與寬限期的官方時序）— https://kubernetes.io/docs/concepts/workloads/pods/pod-lifecycle/
- Kubernetes, "Explore Termination Behavior for Pods And Their Endpoints"（端點移除與行程關閉並行的官方教學）— https://kubernetes.io/docs/tutorials/services/pods-and-endpoint-termination-flow/
- Google Cloud Blog, "Kubernetes best practices: terminating with grace" — https://cloud.google.com/blog/products/containers-kubernetes/kubernetes-best-practices-terminating-with-grace
- CNCF, "Decoding the pod termination lifecycle in Kubernetes: a comprehensive guide" — https://www.cncf.io/blog/2024/12/19/decoding-the-pod-termination-lifecycle-in-kubernetes-a-comprehensive-guide/
- Docker Docs, "docker container stop"（預設 10 秒寬限期與 `--time`）— https://docs.docker.com/reference/cli/docker/container/stop/
- Deni Bertović, "Containers and Signal Handling: Why You Need to Care About PID 1" — https://www.denibertovic.com/posts/containers-and-signal-handling-why-you-need-to-care-about-pid-1/
- Hynek Schlawack, "Why Your Dockerized Application Isn't Receiving Signals"（shell form 不轉發訊號）— https://hynek.me/articles/docker-signals/
- RabbitMQ, "Consumer Acknowledgements and Publisher Confirms"（未 ack 投遞在連線關閉時自動 requeue）— https://www.rabbitmq.com/docs/confirms
