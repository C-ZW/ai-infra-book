# Q · 部署與發布

這個領域回答的是「**新版本怎麼從你的機器走到生產、走錯了怎麼安全退回**」，以及支撐這件事的兩個基礎設施：把應用打包成可重現執行單位的容器，與把基礎設施本身寫成程式碼的 IaC。本檔含六個條目：發布策略（blue-green／canary／rolling）、Docker（容器隔離原理）、Kubernetes（核心物件）、IaC（宣告式、漂移、冪等 apply）、12-factor app（容器/serverless 時代的取捨），以及 config 與機密管理。脊椎與全書一致：每種發布方式、每個工具，都是一組「你想要什麼保證（零停機？快速回滾？低 blast radius？）、你願意付什麼代價（資源翻倍？流量切換複雜度？）」。與相鄰領域的邊界一句話：**probe 怎麼判斷一個 process 死活、graceful shutdown 怎麼不丟在途請求，這些健康檢查機制在韌性與容錯領域深講，本檔只講「Kubernetes 上 probe 設定的語意」與「發布時這些機制怎麼被用上」；冪等的定義在訊息交付領域深講，本檔的「冪等 apply」只引用、不重講定義**。

## blue-green / canary / rolling

### 定義與原理

部署的核心矛盾是：你要把執行中的系統從版本 N 換成 N+1，而**換的過程本身就是一段風險窗口**——舊的還沒退場、新的還沒驗證，這段時間任何不相容、任何 bug、任何資源不足都會打到真實流量。發布策略就是在管理這段窗口：用什麼順序把流量從舊版挪到新版、出事時退回有多快、壞掉時打到多少使用者（blast radius）。

三種主流策略對應三種不同的「窗口管理哲學」：

- **rolling（滾動更新）**：一批一批換。10 個 replica 先換 2 個、健康了再換 2 個，直到全換完。任何時刻都是新舊混跑，總容量大致維持。
- **blue-green（藍綠部署）**：開一整套全新環境（green）跑新版，舊環境（blue）原封不動。驗證 green 沒問題後，把流量一次性從 blue 切到 green。出事就把流量切回 blue，回滾≈一次路由切換。
- **canary（金絲雀）**：新版先只接一小部分流量（如 5%），盯著它的錯誤率/延遲，沒問題才逐步放大到 100%。名字來自礦工帶金絲雀下礦坑探毒氣——讓一小撮流量替全體先試錯。

三者不互斥：實務常是「canary 控制放量節奏 + rolling 控制底層 pod 替換 + 出大事時 blue-green 式整批切回」。

### 解法空間

- **重建式（recreate）**：先全停舊版、再起新版。中間有一段全停機窗口，最簡單但有 downtime；只在能接受停機（如內部批次系統）時用。
- **rolling**：上面說的分批替換。Kubernetes Deployment 的預設策略，由 `maxUnavailable`（更新時最多幾個不可用）和 `maxSurge`（最多超額起幾個）兩個旋鈕控制換的激進程度。
- **blue-green**：兩套等量環境 + 一個流量切換點（LB target group、DNS、Service selector、Ingress 權重）。切換是原子的、回滾極快，代價是**部署期間要雙倍資源**。
- **canary**：細粒度按比例放量，搭配自動分析（盯 SLI，達標才繼續放、超標自動回滾）。需要能按權重切流量的入口（service mesh、L7 LB、Ingress controller）與夠好的可觀測性才玩得起來。
- **shadow / dark launch（影子流量）**：把生產流量「複製」一份打到新版，但新版的回應丟棄、不影響使用者。純粹拿真實流量壓測新版正確性與效能，零使用者風險，代價是要處理副作用（影子請求不能真的扣款、真的寄信）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| recreate | 最簡單、無新舊混跑 | 可接受停機的內部/批次系統 | 有 downtime；不適合面向使用者的服務 |
| rolling | 零停機、資源不翻倍 | 多數無狀態 web 服務的預設 | 部署期間新舊版同時在線，必須向後相容（見下方陷阱）；回滾＝再滾一輪、不是瞬間 |
| blue-green | 回滾近乎瞬間（切流量）、新版可先完整驗證 | 高風險發布、回滾速度是硬需求 | 部署期間雙倍資源；DB schema 跨兩版共用是最大難點 |
| canary | blast radius 可控（先打小流量）、可自動化回滾 | 大流量服務、想用真實流量驗證 | 需要按權重切流量的入口＋好的 SLI 監控；放量太快等於沒 canary |
| shadow | 零使用者風險的真流量驗證 | 驗正確性/效能、不敢直接放量時 | 必須隔離副作用（不可真的寫入/扣款/外呼）；流量複製有成本 |

一個貫穿全部的硬約束：**rolling 與 canary 期間，新舊版本同時對外服務**，所以新版必須與舊版**雙向相容**——舊 client 能打新版、新版寫的資料舊版能讀。這把「資料庫 schema 怎麼在不停機下演進」直接拉進發布策略的設計（加欄位要先部署能讀新欄位的版本、再部署寫它的版本，分兩次發；零停機 schema 遷移見資料一致性與交易領域）。

**Worked example（blue-green vs canary 的 blast radius）**：一個服務每秒 2,000 次請求，新版有個 bug 會讓 1% 的請求回 500。

- 用 **rolling**（10 個 replica、`maxSurge=2`、`maxUnavailable=0`）：替換到第 5 個 replica 時，約 50% 流量打到新版，故障率 = 50% × 1% = 0.5% 的總請求出錯，即每秒約 10 筆 500。你發現問題、按下回滾，rolling 還要再滾一輪把新版換回舊版，期間錯誤持續累積。
- 用 **canary**（先放 5%）：故障率 = 5% × 1% = 0.05%，即每秒約 1 筆 500。自動分析在數十秒內偵測到錯誤率異常、自動把權重打回 0，受影響請求數比 rolling 少一個數量級。

差距不在「會不會出事」，而在「出事時打到多少人、回退多快」——這正是發布策略要買的保證。

### 何時需要

- **能接受停機 → recreate**：內部工具、夜間批次、單機 side project，沒必要上零停機的複雜度。
- **一般無狀態 web 服務 → rolling**：Kubernetes Deployment 預設、夠用、資源不翻倍。多數團隊的起點。
- **回滾速度是硬需求、且資源翻倍可接受 → blue-green**：金流、發布出錯損失大、需要「驗證完整一套再切」的場合。
- **大流量、且有像樣的可觀測性 → canary**：你有足夠流量讓 5% 也具統計意義、有 SLI 能在放量途中即時判生死。**沒有監控的 canary 等於慢動作的全面發布**——只是把炸彈引信拉長，不是拆彈。
- **over-engineering 的訊號**：每天部署一次、流量很小的服務硬上自動化 canary analysis，維運這套 pipeline 的成本遠超它擋下的風險。

### 常見誤解與陷阱

- **以為換了發布策略就不用管相容性**：rolling/canary 的零停機建立在「新舊版能共存」上。一個破壞性的 schema 變更（如直接 rename 欄位）會讓滾動期間舊 pod 讀到不認得的資料而崩——發布策略管的是流量，不管你的變更本身是否相容。
- **把 canary 當「先發一台看看」**：真 canary 要盯指標、要有放量/回滾的判準與自動化。手動發一台、人去肉眼看 dashboard、然後憑感覺全面放量，這是「有 canary 的形、沒 canary 的魂」。
- **blue-green 忽略 DB 是共用的**：應用層可以瞬間切，但 blue 和 green 通常**共用同一個資料庫**。green 跑的新版若改了 schema，blue（你準備回滾的後路）可能就讀不了了——回滾路徑被自己的 migration 切斷。schema 必須對兩版都相容，blue-green 的「秒回滾」才成立。
- **回滾不等於「沒發生過」**：流量可以切回舊版，但新版已寫進 DB／已發出的訊息／已觸發的副作用不會自動撤銷。回滾是停損，不是時光機。
- **健康檢查綠燈 ≠ 新版正確**：rolling 靠 readiness probe 判斷新 pod 能不能接流量，但 probe 通常只查「process 活著、能回 200」，不查業務邏輯對不對。probe 全綠的版本照樣可能算錯帳（probe 語意見 Kubernetes 條目本領域，機制見韌性與容錯領域）。

### 延伸閱讀

- [Kubernetes — Performing a Rolling Update（官方教學）](https://kubernetes.io/docs/tutorials/kubernetes-basics/update/update-intro/)
- [Kubernetes — Deployment 的 strategy / maxSurge / maxUnavailable（官方）](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#strategy)
- [Martin Fowler — BlueGreenDeployment](https://martinfowler.com/bliki/BlueGreenDeployment.html)
- [Martin Fowler — CanaryRelease](https://martinfowler.com/bliki/CanaryRelease.html)

## Docker（容器隔離原理（namespace / cgroup））

### 是什麼與內部機制

容器**不是輕量虛擬機**——這是理解它的起點。VM 用 hypervisor 虛擬化硬體、各跑一份完整 guest kernel；容器則是**同一個 host kernel 上的一群普通 process**，只是被 Linux kernel 的兩組原語罩住，讓它們「以為」自己獨占一台機器。這兩組原語是：

- **namespace（命名空間）= 隔離「看得到什麼」**。每種 namespace 隔離一類系統資源的「視野」。Linux 目前有八種：**pid**（process 編號，容器內第一個 process 是 PID 1，看不到 host 的其他 process）、**net**（網路堆疊，獨立的網卡、IP、路由表、iptables）、**mnt**（檔案系統掛載點，看到的是自己那份根目錄）、**uts**（主機名與 domain name）、**ipc**（System V IPC、POSIX 訊息佇列）、**user**（user/group ID 映射，容器內的 root 可映射成 host 上的非特權使用者）、**cgroup**（隱藏 host 的 cgroup 階層）、**time**（boot/monotonic 時鐘偏移，Linux 5.6 加入）。一個容器＝一組 namespace 的組合。
- **cgroup（control group）= 限制「能用多少」**。namespace 管隔離、cgroup 管資源額度：這個容器最多用 0.5 顆 CPU、512 MiB 記憶體、多少 I/O 頻寬。超過記憶體上限會被 OOM killer 殺掉。現代 Linux 用 **cgroup v2**（單一統一階層，取代 v1 的多階層），是 2026 容器執行的主流（2026-06）。

Docker 本身是上層工具與打包格式；真正建容器的是分層的執行時：你下 `docker run`，Docker daemon 交給 **containerd**（高階 runtime，管 image 拉取、解壓成 OCI bundle），containerd 再呼叫 **runc**（低階 OCI runtime）去實際 `clone()` 出帶上述 namespace 的 process、掛上 cgroup、套上 seccomp 與 capabilities，最後 `execve` 啟動你的程式（2026-06）。「Docker image」則是另一回事：一疊唯讀的檔案系統層（layer）＋一份 metadata，靠 union/overlay 檔案系統疊成容器看到的根目錄，啟動時最上面再加一層可寫層。

### 在哪些系統扮演什麼角色

- **可重現的打包單位**：把「程式 ＋ 它的所有相依（runtime、系統庫、設定）」凍進一個 image，消滅「在我機器上能跑」。CI 建一次 image，dev/staging/prod 跑的是同一份位元組。
- **Kubernetes 的執行底層**：K8s 排程的最小單位 Pod 裡跑的就是容器（見 Kubernetes 條目本領域）。
- **CI/CD 的隔離執行環境**：每個 build job 跑在乾淨容器裡，互不污染。
- **本機開發環境**：用 Compose 一鍵起 DB、cache、訊息佇列，不用在自己機器裝一堆服務。
- **安全沙箱（有限度）**：用 namespace + seccomp + 砍掉多餘 capabilities 限制不信任程式碼——但容器**共用 host kernel**，隔離強度遠不如 VM（見下方陷阱）。

### 保證與限制

保證：**環境一致性**（image 是 immutable 的，到處跑都一樣）、**process 級隔離**（各容器看不到彼此的 process/檔案/網路）、**資源額度**（cgroup 限制 CPU/記憶體，防一個容器吃垮鄰居）、**快速啟動**（沒有 guest kernel 要開機，啟動是毫秒到秒級，不是 VM 的數十秒）。

硬限制：

- **共用 kernel**：所有容器與 host 跑同一個 kernel。kernel 漏洞 = 跨容器/逃逸的潛在破口。隔離強度 < VM。多租戶跑不信任程式碼時，常在容器外再包一層（如 gVisor、Kata Containers 這類用輕量 VM/syscall 攔截補強隔離的方案）。
- **預設仍偏寬**：runc 預設套一份 seccomp profile，封掉 300 多個 syscall 裡的約 44 個（2026-06）——擋掉明顯危險的，但不是最小權限。`--privileged` 會幾乎拆光所有隔離，等於把 host 交出去。
- **記憶體限制是硬殺**：cgroup 的記憶體上限超過就 OOM kill，不像 CPU 是限速。設太低會無預警被殺。
- **不是「迷你 VM」**：沒有獨立 kernel、不能跑不同 OS kernel（Linux 容器要 Linux kernel；Docker Desktop 在 macOS/Windows 上其實是偷偷跑一個 Linux VM 再在裡面跑容器）。

**Worked example（cgroup 記憶體上限）**：你給容器設 `--memory=512m`，裡面跑一個 Node 服務。現代 Node（12+，含 20／22）預設已是 **container-aware**：它讀 cgroup 記憶體上限、把 V8 old space 設成容器上限的約一半（512 MiB 容器→約 256 MiB heap），所以多半不會再「以為自己有 2 GB」。但坑沒消失、只是換位置：(1) 老舊 runtime、或顯式把 `--max-old-space-size` 設過大時，V8 仍會無視 cgroup 一路長到撞牆；(2) heap 只是記憶體的一部分——native buffer、執行緒堆疊、其他 runtime 開銷都不算在 old space 帳上，即使 heap 守規矩、總 RSS 仍可能碰 512 MiB。一旦實體用量碰上限，host kernel 的 OOM killer 立刻把 PID 1 殺掉，容器直接消失、退出碼 137（128 + SIGKILL 的 9）：沒有 OutOfMemoryError、沒有優雅崩潰。正解是顯式對齊（`--max-old-space-size` 設成略低於容器上限、留出非 heap 開銷）並**監控 RSS 而非只看 heap**——這是「程式以為自己擁有的，跟盒子實際給的不一致」的經典坑。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Docker（containerd + runc） | 環境一致、process 級隔離、生態最大 | 開發/CI/單機與多數容器化 | 共用 kernel；隔離 < VM |
| Podman | 同 OCI 生態、daemonless、預設可 rootless | 想免常駐 daemon、偏好 rootless 的伺服器 | CLI 與 Docker 高度相容但非 100% 等價 |
| 傳統 VM（KVM 等） | 強隔離（獨立 kernel） | 多租戶跑不信任程式碼、需跑不同 OS | 啟動慢、資源開銷大、密度低 |
| 輕量 VM 沙箱（gVisor/Kata 類） | 接近 VM 的隔離 + 接近容器的啟動 | 在容器密度下要更強隔離 | 有效能/相容性取捨，非全 syscall 透明 |

Docker 與 Podman 都遵 OCI 標準（image 格式、runtime spec 通用），底層常是同一個 runc，差異在架構（有無常駐 daemon、rootless 預設）。容器 vs VM 不是誰取代誰：**容器買「密度與啟動速度」、VM 買「隔離強度與跑異質 OS」**，多租戶平台常兩者疊著用（VM 切大塊隔離、容器在 VM 裡切密度）。

### 常見誤解與陷阱

- **以為容器是輕量 VM**：最根本的誤解。沒有 guest kernel、共用 host kernel，安全邊界完全不同。把容器當 VM 來放不信任程式碼，是低估了逃逸風險。
- **容器內 root = host 上的 root（沒開 user namespace 時）**：預設情況容器裡的 UID 0 就是 host 的 UID 0。一旦逃逸，拿到的是 host root。開 user namespace 把容器 root 映射成 host 非特權使用者，能大幅縮小爆炸半徑。
- **`--privileged` 隨手加**：它幾乎拆光所有隔離（給全部 capabilities、放開 device 存取、關掉多數限制）。debug 時加了忘了拿掉，等於常態裸奔。
- **把資料寫進容器內**：容器是 ephemeral 的，可寫層隨容器銷毀而消失。狀態要寫進 volume 或外部儲存，別寫進容器自己的檔案系統（無狀態原則見雲端與編排原語領域）。
- **latest tag 當版本**：`image:latest` 不是固定版本，今天拉到的和上週可能不同——可重現性的保證被自己破壞。用明確 tag 或 digest 釘死。
- **以為 cgroup CPU 限制和記憶體限制行為一樣**：CPU 超額是限速（throttle，變慢），記憶體超額是處決（OOM kill，直接死）。兩者的失敗模式天差地別。

### 延伸閱讀

- [namespaces(7) — Linux manual page（七/八種 namespace 總覽）](https://man7.org/linux/man-pages/man7/namespaces.7.html)
- [cgroups(7) — Linux manual page](https://man7.org/linux/man-pages/man7/cgroups.7.html)
- [Open Container Initiative — Runtime Specification](https://github.com/opencontainers/runtime-spec)
- [Docker — Seccomp security profiles for Docker（官方）](https://docs.docker.com/engine/security/seccomp/)

## Kubernetes（Pod/Service/HPA 核心物件；probe 設定語意、health check 機制見領域 P）

### 是什麼與內部機制

Kubernetes 的本質是一個**宣告式的控制迴圈系統**：你不下「啟動三個容器」這種命令式指令，而是宣告「我要這個 Deployment 永遠有 3 個健康的 replica」這種**期望狀態（desired state）**，寫進 etcd（叢集的一致性 key-value 儲存）。然後一群 **controller** 持續跑「觀察實際狀態 → 比對期望狀態 → 採取行動讓兩者收斂」的迴圈（reconciliation loop）。一個 pod 掛了，實際變成 2 個，controller 看到差異、補一個回來——這個「自我修復」不是特殊功能，就是控制迴圈的自然結果。

核心物件，由內而外：

- **Pod**：排程與部署的最小單位。一個 Pod 包一個或多個共用網路 namespace（同一個 IP、可 localhost 互通）與儲存的容器。Pod 是 ephemeral 的——掛了不會原地復活，而是被**新建一個**（新 IP、新身分）。所以你幾乎不直接管 Pod，而是透過上層 controller。
- **Deployment**：管一組無狀態 Pod 的副本與滾動更新。它透過 ReplicaSet 維持 N 個 replica、並在更新時用 rolling 策略換版（見發布策略條目本領域）。有狀態服務則用 StatefulSet（穩定的網路身分與儲存）。
- **Service**：給「一組會變動的 Pod」一個穩定的虛擬 IP 與 DNS 名。Pod 的 IP 一直在變（重建就換），Service 用 label selector 動態追蹤「目前哪些 Pod 是 ready 的」，把流量負載均衡過去。它解的是「後端會漂移、前端要有固定入口」的服務發現問題。
- **HPA（HorizontalPodAutoscaler）**：依指標（CPU、記憶體、或自訂/外部指標）自動調整 replica 數。current API 是 **`autoscaling/v2`**（自 Kubernetes 1.23 GA，2026-06 仍為穩定版），支援多指標。它跑的也是控制迴圈：週期性算「目標指標 / 當前指標 → 該要幾個 replica」。

**probe（探針）設定語意**——Kubernetes 上每個容器可設三種探針，kubelet 週期性執行，決定該「重啟」還是「停止送流量」（健康檢查的機制與 liveness/readiness 設計在韌性與容錯領域深講，這裡只講 K8s 上的設定語意，2026-06）：

- **liveness probe**：問「這 process 卡死了嗎」。連續失敗 `failureThreshold` 次（預設 3）→ kubelet **殺掉容器並依 restartPolicy 重啟**。
- **readiness probe**：問「這 process 現在能接流量嗎」。失敗 → 把這個 Pod 的 IP **從 Service 的 endpoints 移除**（停止送流量，但**不重啟**）。
- **startup probe**：問「這 process 開機完成了嗎」。成功前，liveness/readiness 都暫停——專治啟動慢的應用被 liveness 在開機途中誤殺。

關鍵旋鈕：`periodSeconds`（多久探一次，預設 10s）、`failureThreshold`（連續幾次失敗才算數，預設 3）。實際反應時間 ≈ `periodSeconds × failureThreshold`。

### 在哪些系統扮演什麼角色

- **容器編排平台**：在一群機器（node）上排程容器、處理失效轉移、滾動更新、自動擴縮——把「一堆機器」抽象成「一個資源池」。
- **服務發現與負載均衡**：Service + 內建 DNS 讓服務間用名字互找，不必硬編 IP（DNS/服務發現機制見網路與協定領域）。
- **宣告式部署的承載**：IaC 把期望狀態寫成 YAML/Helm/Kustomize，apply 進叢集（見 IaC 條目本領域）。
- **自動擴縮**：HPA 依負載調 Pod 數、Cluster Autoscaler 依 Pod 需求調 node 數。
- **批次與排程**：Job（一次性）與 CronJob（定時，非 exactly-once，見雲端與編排原語領域）。

### 保證與限制

保證：**宣告式收斂**（你說期望狀態，系統持續往那收斂）、**自我修復**（Pod/node 掛了自動重建/重排）、**水平擴縮**（HPA/Cluster Autoscaler）、**滾動更新與回滾**（Deployment 內建）、**服務發現**（Service + DNS 抽象掉 Pod IP 漂移）。

限制：

- **最終一致、非即時**：控制迴圈是收斂式的，從你 apply 到實際達成有延遲。HPA 有 stabilization window 防抖、Service endpoints 更新有傳播延遲——別假設「改了就立刻生效」。
- **Pod 是 ephemeral 的**：沒有穩定身分（除非 StatefulSet）。把狀態寄望在 Pod 本地＝重建就失憶。
- **複雜度極高**：網路（CNI）、儲存（CSI）、權限（RBAC）、Ingress、各種 controller……自運維一個生產叢集是專職工作量。對小團隊常是 over-engineering。
- **probe 只查表象**：readiness/liveness 通常只查「能回 200」，查不出業務邏輯對錯（見下方陷阱）。
- **資源限制不設＝鄰居遭殃**：不設 requests/limits，一個 Pod 可能吃垮整個 node 上的鄰居（cgroup 機制見 Docker 條目本領域）。

**Worked example（HPA 算 replica 數）**：一個 Deployment 設 HPA target「CPU 平均使用率 50%」，目前 4 個 replica、實測平均 CPU 80%。HPA 的演算法是 `desiredReplicas = ceil(currentReplicas × currentMetric / targetMetric)` = `ceil(4 × 80 / 50)` = `ceil(6.4)` = **7**。它會把 replica 拉到 7，理論上把平均 CPU 壓回 `4×80/7 ≈ 46%`（低於 50%，穩住）。反過來若實測 25%，`ceil(4 × 25 / 50)` = `ceil(2)` = 2，縮到 2 個。注意：scale-up 反應快，但 scale-down 預設有 5 分鐘 stabilization window 防止抖動造成的反覆擴縮——突發流量退去後不會立刻縮回，這是刻意的保守。

### 跟替代品的取捨

| 方案/工具 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| Kubernetes | 宣告式收斂、自我修復、可移植、生態最大 | 多服務、需自動擴縮/失效轉移的中大型系統 | 運維複雜度高；小團隊常 over-engineering |
| 託管容器服務（如雲廠的 Fargate/Cloud Run 類） | 免管 node/control plane | 想要容器但不想管叢集 | 較貴、被廠商抽象綁定、彈性較低 |
| serverless（函式即服務） | 免管基礎設施、scale-to-zero | 事件驅動、突發/間歇負載 | 冷啟動、執行時間/payload 上限、無常駐狀態（見雲端與編排原語領域） |
| 直接跑 VM + systemd | 最簡單、零學習曲線 | 單體/少數服務、團隊小 | 自我修復/擴縮/服務發現全要自己拼 |

選 K8s 的判準不是「先進」，而是「你的規模與動態性是否值得這套複雜度」。3 個服務、流量平穩、團隊 4 人——一台 VM 加 systemd 可能比一個 K8s 叢集更可靠也更省心。30 個服務、流量起伏大、要頻繁部署——K8s 抹平的運維成本才回得了本。

### 常見誤解與陷阱

- **probe 綠燈以為健康**：readiness 回 200 只代表「process 活著、能回 HTTP」，不代表它能正確處理請求。一個 readiness 探 `/health`、但 `/health` 只回靜態 200 不查下游 DB 連線的服務，DB 掛了它照樣對外宣稱 ready、照樣收流量然後全 500。probe 要探到真正的就緒條件才有意義。
- **liveness probe 設太敏感引發連鎖重啟**：liveness 探的端點若依賴一個暫時變慢的下游，整批 Pod 會同時 liveness 失敗、同時被重啟，把暫時的慢拖成全面的 crash loop。liveness 該只查「自己卡死沒」，別把外部相依綁進去（這是 readiness 的活）。
- **以為 Pod 有固定 IP/身分**：Deployment 管的 Pod 重建就換 IP、換名字。需要穩定身分（如某些有狀態叢集）要用 StatefulSet，別在 Deployment 上假設 Pod 不變。
- **不設 resource requests/limits**：不設 requests，排程器無從正確 binpack；不設 limits，一個失控 Pod 吃垮 node。兩個都該設。
- **把 K8s 當銀彈**：它解的是編排問題，不解你應用本身的架構問題。把一個耦合很深的單體塞進 K8s，得到的是一個難搞的單體加一層 K8s 複雜度。
- **HPA 看 CPU 卻是 I/O bound 服務**：HPA 預設拿 CPU 當訊號，但很多服務的瓶頸是 I/O 或下游延遲，CPU 一直很低、HPA 永遠不擴，過載照樣發生。該擴的訊號（佇列長度、p99 延遲）要用自訂/外部指標餵 HPA。

### 延伸閱讀

- [Kubernetes — Pods（官方概念）](https://kubernetes.io/docs/concepts/workloads/pods/)
- [Kubernetes — Service（官方概念）](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes — Horizontal Pod Autoscaling（官方，含演算法）](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)
- [Kubernetes — Configure Liveness, Readiness and Startup Probes（官方）](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

## IaC（宣告式、漂移、冪等 apply）

### 定義與原理

IaC（Infrastructure as Code，基礎設施即程式碼）的核心主張：**基礎設施的期望狀態應該寫成可版控的程式碼，由工具負責把現實收斂到那份程式碼**——而不是靠人去 console 點按鈕、靠記憶與口耳維護。它解的問題是「**雪花伺服器**（snowflake server）」：每台機器都是手工調出來的、沒人說得清它現在是什麼狀態、壞了重建不出來、環境之間悄悄漂移。

兩種風格：

- **宣告式（declarative）**：你描述「最終要長什麼樣」（要一個 t3.medium、開 443 port、掛這顆磁碟），工具自己算出「從現狀到目標要做哪些動作」。Terraform/OpenTofu、Kubernetes manifest、CloudFormation 屬此類。
- **命令式（imperative）**：你寫「依序執行哪些步驟」（先建 VM、再裝套件、再改設定）。傳統 shell script、部分 Ansible 用法屬此類。

本書的脊椎在宣告式，因為它直接給三個保證：**冪等**（同一份程式碼 apply 幾次，結果都收斂到同一個狀態，不重複建資源——冪等的定義在訊息交付領域深講，此處只引用）、**可重現**（從零照程式碼重建出一模一樣的環境）、**可審計**（基礎設施變更走 PR/review，有歷史）。

**漂移（drift）** 是宣告式 IaC 最核心的概念之一：**實際狀態偏離了程式碼宣告的狀態**。有人手動去 console 改了個 security group、某個資源被別的系統動了——這時「程式碼說的」和「現實的」不一致。宣告式工具靠一份 **state**（記錄「我上次管到的實際狀態」）來偵測漂移：`plan` 階段把 state、真實雲端現況、程式碼三方比對，算出差異給你看；`apply` 才真的執行。

### 解法空間

- **provisioning 類（建基礎設施本身）**：Terraform / OpenTofu（宣告式、跨雲、靠 state、`plan/apply` 兩段式）、各雲廠原生（CloudFormation、ARM/Bicep 等，綁單一雲）、Pulumi（用通用程式語言寫，仍是宣告式收斂）。
- **configuration management 類（管機器內部設定）**：Ansible（agentless、push、可寫成偏宣告式的 playbook）、Chef/Puppet（agent、pull、宣告式 resource）。與 provisioning 是不同層：一個建出機器，一個管機器裡裝什麼。
- **GitOps（把 Git 當唯一真相來源）**：宣告式 manifest 放 Git，一個 controller（如 Argo CD/Flux 這類）持續把叢集實際狀態往 Git 宣告的狀態收斂、並回報漂移。等於把「宣告式收斂」變成常駐的閉迴路，而非人手動 apply。
- **漂移處理策略**：定期 `plan` 偵測（detect-only，只告警）、自動 re-apply 矯正（把現實拉回程式碼）、或反向 import（把手改的現狀吸收進程式碼）。2026 的趨勢是從「只偵測」走向「自動矯正」（2026-06）。

### 各方案的保證與取捨

| 方案/做法 | 保證 | 適用場景 | 注意事項 |
|---|---|---|---|
| 宣告式 + state（Terraform/OpenTofu 類） | 冪等、可重現、漂移可偵測、跨雲 | 管雲端基礎設施的主流選擇 | state 是單點要害（鎖、加密、誰持有）；`apply` 前不看 `plan` 等於閉眼開車 |
| 命令式 script | 直觀、零學習門檻 | 一次性、簡單的開機腳本 | 非冪等（重跑可能重複建或出錯）、無漂移概念、難重現 |
| configuration management（Ansible 類） | 管機器內設定、(偏)冪等 | 在已存在的機器上裝/設軟體 | 不負責 provision 機器本身；冪等性看 module 寫法 |
| GitOps（Argo CD/Flux 類） | 持續收斂、Git 即真相、漂移自動回報 | Kubernetes 叢集狀態管理 | 要一個常駐 controller；Git 與叢集的雙向同步邏輯要想清楚 |

授權現況需注意：Terraform 自 **2023-08 從 MPL 2.0 改為 BSL（Business Source License）1.1**，社群隨即 fork 出 **OpenTofu**（仍 MPL 2.0、由 Linux Foundation 主持），2026 已是可直接替換多數 Terraform 工作流的選項（2026-06）。選工具時這條授權分裂是真實的決策因素，不是歷史註腳。

### 何時需要

- **基礎設施會被重建/複製 → 一定要 IaC**：多環境（dev/staging/prod 要一致）、災難重建、頻繁開關環境。手工點按鈕在這些場景下必然漂移。
- **基礎設施變更要審計/協作 → 要宣告式 + 版控**：多人改、要 review、要回溯「誰在什麼時候改了什麼」。
- **一台機器、永遠手動、沒人複製 → IaC 可能 over-engineering**：一個 side project 的單台 VM，硬上 Terraform + state 管理的成本未必回本（但連這種情境，一個簡單的 provisioning script 也比純手工強）。
- **判準**：問「這個環境如果整個被刪掉，我多久能照程式碼重建出一模一樣的？」答不出來，就是該上 IaC 的訊號。

### 常見誤解與陷阱

- **手動改了 console 又跑 apply**：你在 console 手改的東西，下次 `apply` 時工具看到漂移，會**把它改回程式碼宣告的樣子**——你的手動修復被無聲覆蓋。要嘛別手改，要嘛把手改回填進程式碼。這是漂移最常見的傷人方式。
- **state 不上鎖**：兩個人同時 `apply` 同一份 state，會互相踩、把 state 寫壞，導致工具對「現實是什麼」的認知錯亂（後續 plan 全錯）。state 必須上鎖（remote backend 提供鎖）。
- **state 含機密卻沒加密**：Terraform state 會把資源屬性（可能含密碼、金鑰）以明文存進 state 檔。state 放沒加密的 bucket 或 commit 進 Git ＝洩密。
- **以為宣告式就自動冪等到任何程度**：宣告式工具對它「管得到的」資源冪等；對 provider 沒模型化的副作用（某些 provisioner 跑的 shell、外部系統的狀態）不一定冪等。`local-exec` 跑一個非冪等 script，apply 兩次就出事。
- **把 IaC 當「跑一次就好」**：IaC 的價值在「程式碼＝真相、持續收斂」。寫完 apply 一次就再也不管、之後全手改，等於退回雪花伺服器，只是多了一份過時的程式碼假裝在管。
- **AI 生成的 IaC 直接 apply**：請 AI 產一段 Terraform 很快，但它可能開了過寬的 security group、用了過時的資源寫法、或對 state 的影響沒被理解。IaC 的 `apply` 直接動真實基礎設施——`plan` 的 diff 必須由人讀懂、確認 blast radius 後才放行，這正是宣告式兩段式設計的價值所在。

### 延伸閱讀

- [Terraform — What is Infrastructure as Code with Terraform（官方）](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code)
- [OpenTofu（MPL 授權的 Terraform fork，官方）](https://opentofu.org/)
- [Terraform — Managing resource drift（官方）](https://developer.hashicorp.com/terraform/tutorials/state/resource-drift)
- [Kubernetes — Declarative Management of Kubernetes Objects（官方）](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/)

## 12-factor app

### 定義與原理

12-factor app 是 Heroku 共同創辦人 Adam Wiggins 於 **2011** 整理出的一套方法論（原文 12factor.net），把「會在 PaaS 上跑得好、好擴展、好維運的應用」歸納成十二條原則。它出現在容器與 Kubernetes 普及之前，但它定義的很多模式——把 config 從程式碼抽出、process 無狀態、log 當 stream——正好成了後來雲原生世界的預設假設。理解它的價值不在背十二條，而在看清**哪些原則是恆久的工程約束、哪些只是它那個年代（2011 的 PaaS）的具體實作建議**。

完整十二條（編號照原文）：I. 程式碼庫（一份 codebase 多份部署）、II. 相依（顯式宣告並隔離）、III. config（存在環境裡）、IV. backing services（後端服務當可替換的 attached resource）、V. build/release/run（三階段嚴格分離）、VI. processes（無狀態、share-nothing）、VII. port binding（自帶 server、靠 port 對外）、VIII. concurrency（靠 process model 水平擴展）、IX. disposability（快速啟動、優雅關閉）、X. dev/prod parity（環境盡量一致）、XI. logs（當 event stream，不自己寫檔）、XII. admin processes（一次性管理任務當 one-off process 跑）。

關鍵時效更新：**12-factor 方法論已於 2024-11 開源**（搬到 GitHub `twelve-factor/twelve-factor`、轉社群治理），目前有一個「更新版」在 `next` 分支開發中，要把這套東西刷新到 Kubernetes/GitOps/workload identity 的時代，最終會取代 12factor.net 上的舊版（2026-06）。同時 Google 等也提出「為 AI 工作負載重新思考」的延伸（如把它擴成更多因子的版本）。所以正確的態度是：**核心抽象仍站得住，但細節在 2026 確實顯老、官方自己在改**。

### 解法空間

把十二條按「在容器/serverless 時代的處境」分三類看，比逐條背更有用：

**仍然完全成立（甚至被現代平台變成預設）**：
- **III. config 存環境**：把 config 與程式碼分離的原則恆久正確。K8s 用 ConfigMap、serverless 用環境變數，都是這條的實作。
- **VI. 無狀態 process**：水平擴展、scale-to-zero、滾動更新全建立在「process 可隨時被殺/複製」上。容器與 serverless 把這條推到極致（見無狀態 vs 有狀態，雲端與編排原語領域）。
- **XI. logs 當 stream**：應用只管把 log 寫 stdout/stderr，由平台（容器 runtime、orchestrator、log agent）收集路由。容器世界這條是鐵律——應用自己寫 log 檔反而是反模式。
- **IX. disposability（快速啟動、優雅關閉）**：K8s 的 rolling update、HPA、Spot 中斷全靠 process 能秒起秒停、收到 SIGTERM 能 graceful shutdown（機制見韌性與容錯領域）。
- **V. build/release/run 分離**：對應現代的 immutable image + 不可變部署，比 2011 更被嚴格落實。

**仍成立但細節需更新**：
- **III. config「存環境變數」的具體形式**：原則對，但「一律塞環境變數」在 K8s 時代未必最佳——機密用環境變數有洩漏面（見 config 與機密管理條目本領域），常改用掛載檔案（mounted Secret）或專門的機密管理器。「config 與程式碼分離」恆久，「一定用 env var」不必死守。
- **IV. backing services 當 attached resource**：原則對，但現代多了 sidecar、service mesh、託管服務等更豐富的「attach」方式。
- **X. dev/prod parity**：容器讓這條前所未有地容易達成（dev 跑的就是 prod 的 image），算是被現代工具大幅強化的一條。

**顯出年代局限、需要補**：
- **可觀測性的缺口**：12-factor 只談 log，**完全沒提 metrics 與 traces**（三本柱見可觀測性與品質領域）。2011 年的單純 log stream 在分散式系統時代不夠用——這是它最常被點名的盲區。
- **機密管理**：config 那條把一般 config 與機密混為一談、都丟環境變數。現代把機密當獨立問題處理（輪替、最小權限、稽核），不該與一般 config 同等對待。
- **狀態與資料**：方法論假設應用無狀態、狀態全外放到 backing service，但對「有狀態服務怎麼辦」幾乎沒著墨——而現實有大量有狀態系統。

### 各方案的保證與取捨

| 原則/做法 | 在容器/serverless 時代的效果 | 適用場景 | 注意事項 |
|---|---|---|---|
| config 存環境（III） | 仍成立；config 與碼分離恆久正確 | 所有環境 | 「一律 env var」需更新——機密宜用掛載 Secret/機密管理器，別與一般 config 混用 |
| 無狀態 process（VI） | 完全成立並被推到極致 | 水平擴展、serverless | 真有狀態的部分要誠實外放，別假裝無狀態 |
| logs 當 stream（XI） | 容器世界的鐵律 | 所有容器化應用 | 只談 log 不夠——要補 metrics + traces（三本柱） |
| disposability（IX） | 完全成立 | rolling update、HPA、Spot | 沒實作 graceful shutdown 會在每次部署丟在途請求 |
| 可觀測性涵蓋 | 不足——只有 log，缺 metrics/traces | 分散式系統 | 把 12-factor 當完整觀測指引會有大盲區 |

整體判斷（屬本書觀點，非規格）：**12-factor 是「雲原生的最小公因數心智模型」**——它的抽象（無狀態、config 外置、log as stream、disposability）仍是評估一個服務「能不能在容器/K8s/serverless 上跑得好」的好 checklist；但別把它當 2026 的完整工程指南，它在可觀測性與機密管理上明顯不足，且官方自己正在改版。

### 何時需要

- **要上容器/K8s/serverless → 拿它當就緒檢查**：一個服務若違反「無狀態、config 外置、log as stream、可秒起秒停」，它在這些平台上會處處卡（無法水平擴展、部署丟資料、log 收不到）。12-factor 是「這個服務雲原生就緒了嗎」的快速體檢表。
- **設計新服務 → 拿它當預設骨架**：從一開始就無狀態、config 外置，比事後改造省太多。
- **不要當教條**：「一定要十二條全中」不是目的。一個刻意的有狀態服務（如資料庫本身）違反 VI 是天經地義，不是錯。原則是用來理解取捨的，不是用來打勾的。

### 常見誤解與陷阱

- **把它當完整的現代雲原生指南**：它沒提 metrics、traces、機密管理、有狀態服務、安全。當 checklist 起點很好，當終點會有大洞。
- **死守「config 一律環境變數」**：原則是「config 與程式碼分離」，不是「必須是 env var」。機密塞環境變數有實際洩漏面（見下一條目）；K8s 時代掛載檔案常更安全。
- **以為「無狀態」= 不能有任何狀態**：是指**應用 process 不在本地保存跨請求狀態**，狀態外放到 DB/cache/物件儲存。不是說系統不能有狀態。
- **引用一個其實在改版的「凍結標準」**：12-factor 在 2024-11 開源後正由社群更新中（2026-06），引用時別把它講成一份十多年沒動的權威定本——它的官方版本正在演進。
- **logs 當 stream 卻又自己 rotate 檔案**：應用一旦自己寫 log 檔、自己切割，就破壞了「平台收集」的前提，在容器裡反而製造問題（容器銷毀 log 就沒了）。寫 stdout/stderr 就好，收集交給平台。

### 延伸閱讀

- [The Twelve-Factor App（原方法論，12factor.net）](https://12factor.net/)
- [Twelve-Factor App Methodology is now Open Source（2024-11 開源公告）](https://12factor.net/blog/open-source-announcement)
- [twelve-factor/twelve-factor（GitHub，更新版開發中）](https://github.com/twelve-factor/twelve-factor)

## config 與機密管理

### 定義與原理

這條回答「**會隨環境而變、或不該寫進程式碼的值，要放哪、怎麼遞給應用、怎麼在不重啟的前提下換**」。它分兩個性質不同的子問題，混為一談是大坑：

- **一般 config（組態）**：feature flag、超時時間、外部服務 URL、log level 之類。會隨環境（dev/staging/prod）而變，但洩漏了不直接致命。核心需求是「與程式碼分離、可按環境注入」（12-factor 第 III 條，見上一條目）。
- **機密（secrets）**：DB 密碼、API key、私鑰、token。洩漏 = 直接被打穿。核心需求遠超過「與碼分離」——還要**加密儲存、最小權限存取、可輪替（rotation）、可稽核（誰在何時取用了哪個機密）**。

第一原理：**機密不是「比較敏感的 config」，它是一個不同的問題類別**。一般 config 的目標是「正確注入」；機密的目標是「在它必然會被洩漏的假設下，把爆炸半徑與爆炸後的修復成本壓到最小」。把兩者用同一套機制（如都塞環境變數）處理，等於用 config 的安全等級保護機密。

### 解法空間

config 的注入方式：

- **環境變數**：12-factor 的經典做法。簡單、語言無關，但不適合大型/結構化 config，且對機密有洩漏面（見下）。
- **設定檔（掛載）**：把 config 以檔案掛進容器（K8s ConfigMap volume）。適合結構化、量大的 config，可不重啟 reload（看應用是否支援 watch）。
- **集中式 config 服務**：應用啟動時（或執行中）向一個中央 config 系統拉取，支援動態更新、版控、漸進式放量。

機密的處理層級（由弱到強）：

- **明文存進程式碼/repo**：最糟，等於公開。任何進到 repo 歷史的機密都該視為已洩漏（git 歷史撤不乾淨）。
- **環境變數注入**：比寫死好，但機密以明文存在 process 環境、可能被子 process 繼承、被 crash dump/error log 帶出、被 `/proc/<pid>/environ` 讀到。
- **K8s Secret**：把機密與 ConfigMap 分開的物件。但**預設只是 base64 編碼、不是加密**——etcd 裡若沒開 encryption-at-rest，Secret 形同明文。要開 etcd 加密 + RBAC 限制誰能讀。
- **專門的機密管理器**：集中加密儲存、細粒度存取控制、**動態機密**（用時才生成、短 TTL 自動過期）、自動輪替、完整稽核日誌。是機密問題的「完整解」。
- **掛載而非環境變數**：把機密以檔案掛進容器（tmpfs，不落盤）而非塞環境變數，縮小洩漏面（環境變數的繼承/dump 問題見上）。

### 各方案的保證與取捨

| 方案/做法 | 保證（提供什麼防護） | 適用場景 | 注意事項 |
|---|---|---|---|
| 寫進程式碼/repo | 無——等於公開 | 永遠不該用於機密 | 進過 git 歷史的機密＝已洩漏，必須輪替 |
| 環境變數 | 與碼分離；無加密、無輪替、無稽核 | 一般 config、低敏感值 | 機密用它有洩漏面（子 process 繼承、dump、/proc） |
| K8s Secret（預設） | 與 ConfigMap 分離 | K8s 上的基本機密 | 預設只 base64、非加密；要另開 etcd encryption-at-rest + RBAC |
| 機密管理器（動態機密類） | 加密、最小權限、輪替、短 TTL、稽核 | 生產級機密管理 | 引入相依與運維成本；應用要改成「向它拉」 |
| 掛載檔案（tmpfs） | 縮小洩漏面（不落盤、不進環境） | 機密注入的較安全形式 | 應用要支援從檔案讀、且能 reload |

一條決策原則：**機密的理想狀態是「短命 + 用時才給 + 用完即棄 + 全程有記錄」**。靜態長命機密（一個密碼用三年、散落在十個地方）是最差的形態——它一旦洩漏，你既不知道何時被誰拿走，輪替起來又因散落各處而痛苦。

**Worked example（機密輪替的成本）**：一個系統把同一個 DB 密碼硬編在 5 個服務的環境變數裡。某天懷疑外洩要輪替：你得改 DB 密碼、同步更新這 5 個服務的環境變數、依序重新部署、且要處理「改 DB 密碼的瞬間到 5 個服務全更新完之間，用舊密碼的連線會被拒」的空窗——這是一次協調式停機。對照用動態機密：每個服務啟動時向機密管理器拿一份 TTL 1 小時的臨時憑證，輪替＝撤銷舊憑證、下次續租自動拿新的，無需改任何服務的設定、無需重新部署、無協調空窗。把「輪替一次要動幾個地方、要不要停機」當成衡量機密管理成熟度的尺，比看用了哪個工具更實在。

### 何時需要

- **任何有多環境的系統 → config 一定要外置**：硬編環境差異（prod 連到 staging 的 DB）是事故常客。
- **任何持有機密的系統（≈ 全部）→ 至少做到「與 config 分離 + 加密儲存 + 不進 repo」**：這是底線，不是進階。
- **機密多、合規要求稽核/輪替、團隊大 → 上專門機密管理器**：要回答「這個 key 上次輪替是何時、誰能讀、誰讀過」時，環境變數答不出來，就是該升級的訊號。
- **over-engineering 訊號**：一個單人 side project、兩個機密、無合規要求，硬上一整套動態機密基礎設施——維運它的成本超過它擋的風險。一個加密的、不進 repo 的設定來源就夠。

### 常見誤解與陷阱

- **以為 K8s Secret 是加密的**：預設只是 base64 編碼（人人可解），etcd 沒開 encryption-at-rest 的話形同明文。「我用了 Secret 物件」不等於「機密被保護了」。
- **機密進了 git 歷史以為刪掉 commit 就沒事**：git 歷史幾乎撤不乾淨（別人 clone 過、CI 快取過、reflog 留著）。一旦 commit 過，唯一安全假設是「已洩漏」，必須輪替那個機密，而不是改 commit。
- **機密塞環境變數又印整包 env 到 log**：很多框架在啟動或出錯時會 dump 整個環境變數方便 debug——機密就這樣進了 log，再被 log 系統長期保存、被一堆人看到。
- **config 與機密用同一機制、同一權限**：把 DB 密碼和 log level 放同一個 ConfigMap、給同一組人讀權限，等於用 config 的安全等級保護機密。兩者該分離、機密該更嚴。
- **靜態長命機密散落各處**：同一個密碼複製到十個地方、永不過期。它的問題不在「現在會不會洩」，而在「洩了你不知道、要輪替時十個地方全要動」。短命 + 集中 + 動態生成才是解。
- **AI 協作下的新洩漏面**：把含機密的設定檔、log、stack trace 貼給 AI 工具，或讓 AI 生成的程式碼把機密寫死進範例——機密就這樣離開了你的信任邊界。AI 在手邊時，「什麼能貼出去」要有明確的紅線，這是個新的、容易被忽略的洩漏管道。

### 延伸閱讀

- [The Twelve-Factor App — III. Config（store config in the environment）](https://12factor.net/config)
- [Kubernetes — Secrets（官方，含「預設僅 base64、需開 encryption at rest」）](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Kubernetes — Encrypting Confidential Data at Rest（官方）](https://kubernetes.io/docs/tasks/administer-cluster/encrypt-data/)
- [OWASP — Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
