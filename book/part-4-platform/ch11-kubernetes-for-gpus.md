# ch11 — Kubernetes 上的 GPU：排程、共享與節點生命週期

> **本章解決什麼問題**：Part II 與 Part III 講完了引擎與多卡推論本身，從本章開始進入平台層。第一個問題就是地基：K8s 怎麼把 GPU 當資源管？這是你既有 K8s 功力的主場延伸——但 GPU 把你熟悉的資源模型撕開了一個洞：它是整數、不可超賣、不可分割、排程器看不見它的內部。本章講清楚這個洞（device plugin 模型）、業界怎麼繞（time-slicing/MPS/MIG）、以及 2026 年正在發生的根本修復（DRA）。後面 ch12 的推論平台、ch13 的 autoscaling 都蓋在這層地基上。

## 從你已知的出發

你在 EKS 上管過生產叢集，所以這些直覺你都有：requests/limits 是 cgroup 層的流量管制，CPU 可以超賣（requests 總和 > 節點容量，靠 throttling 兜底）、memory 超賣會換來 OOMKill、scheduler 用 requests 做 bin-packing 決策。整套哲學的前提是：**資源是連續可分割的流量**，內核可以在毫秒尺度上對它做時間切片與仲裁。

GPU 不是流量，是**一台完整的計算機**（ch02 講過：自己的記憶體、自己的排程器、自己的故障模式）。把一張 GPU 交給容器，比較像把整台實體機借出去，而不是分配 0.5 個 CPU。所以 K8s 對 GPU 的資源語意退化回整數：`nvidia.com/gpu: 1`，要嘛整張給你，要嘛沒有。沒有 throttling、沒有超賣、沒有「先給你用、忙起來再搶回來」。你過去十年累積的「資源利用率靠超賣堆上去」的直覺，在這裡第一步就失效。

第二個橋接：你寫過 idempotent consumer——從 SQS 拉訊息、對照目標狀態、把現實收斂過去。K8s operator 的 reconcile loop 是同一個模式（ch04 講過），而本章你會看到一整個 operator 軍團（GPU Operator、MIG Manager、Kueue、LWS controller）各自 reconcile 一小塊 GPU 現實。讀它們的故障，就是讀「reconcile 卡住」的各種姿勢。

第三個：你在遊戲後端見過 connection pool 被慢查詢吃光的事故——資源是整數槽位、被佔住就是佔住、後面的請求只能排隊。GPU 叢集的日常就是這個事故的放大版：64 個槽位、每個槽位被佔住的時間以小時或天計、而且「釋放一個槽位」可能意味著殺掉一個跑了三天的訓練 job。排程、配額、搶占在這個物理下全部要重新校準——這正是全書主軸三：分散式直覺成立，物理常數變了。

## GPU 資源模型：為什麼 `nvidia.com/gpu` 是個不透明整數

### Device plugin 機制一頁解剖

K8s 本身不認識 GPU。認識 GPU 的是 **device plugin**：一個跑在每個 GPU 節點上的 DaemonSet，透過 Unix socket（`/var/lib/kubelet/device-plugins/`）向 kubelet 註冊，實作兩個核心 gRPC 介面：

```text
ListAndWatch()  → 回報裝置 ID 清單與健康狀態（streaming）
                  kubelet 據此向 API server 宣告 capacity: nvidia.com/gpu: 8
Allocate(IDs)   → Pod 排定後，kubelet 要求 plugin 準備指定裝置
                  plugin 回傳要注入容器的 env（NVIDIA_VISIBLE_DEVICES）、
                  device nodes、mounts
```

注意責任切分，這是理解一切限制的鑰匙：

- **Scheduler 只會數數**。它看到的是「這個節點宣告 8 個 `nvidia.com/gpu`、已用 5 個」，做整數加減法。它不知道那是 H100 還是 T4、不知道哪幾張在同一個 NVLink domain、不知道哪張快壞了。
- **挑哪一張卡是 kubelet（device manager）在節點上的本地決策**，scheduler 完全不參與。device plugin 能做的拓撲最佳化（盡量挑同一 PCIe switch 下的卡）只是 best-effort 的本地啟發式。
- **Extended resource 的語意是硬性整數**：requests 必須等於 limits（其實你只能寫 limits），不可超賣、不可寫 0.5。

### 根本限制清單

把 device plugin 模型的天花板列清楚，等一下 DRA 每一條都要對著解：

| # | 限制 | 後果 |
|---|------|------|
| 1 | 資源是不透明整數 | 無法表達「要一張 ≥40GB 的卡」；裝置屬性只能靠 node label（GFD）+ nodeSelector 在**節點層級**近似，同節點異質 GPU 幾乎無法表達 |
| 2 | 不可分割、不可超賣 | 一個 notebook 占一整張 H100；利用率問題只能靠外掛 hack（下一節三件套） |
| 3 | Scheduler 看不到裝置 | 無法做裝置層級拓撲決策（「給我同一 NVLink domain 的 4 張」做不到）；跨節點的 rack/IB locality 更不用說 |
| 4 | 裝置不能跨 Pod 共享 | 一張卡一次配給一個容器，沒有「claim 由多個 Pod 共用」的一級語意 |
| 5 | 健康語意貧乏 | 某張卡 unhealthy → capacity 整數減一，但哪張壞、為什麼壞、上面的 Pod 怎麼辦，全在 API 之外 |
| 6 | 重新配置要翻桌 | 改 MIG 切法 = 清空節點上所有 GPU Pod、重設、重啟 plugin；不是宣告式操作 |

對照你熟的 CPU/memory 模型，差異不是程度問題，是哲學問題：CPU/memory 是 kernel 仲裁的連續流量，GPU 是使用者空間裡一台被整台出借的機器。K8s 1.0 時代的 extended resource API 從來沒打算承載後者，業界硬是用了八年。

## NVIDIA GPU Operator：全家桶解剖

裸裝一個 GPU 節點要手動對齊五、六層元件，GPU Operator 把它們全部 operator 化。你需要知道每個元件做什麼，因為**它們壞掉的症狀完全不同**：

| 元件 | 做什麼 | 壞了的典型症狀 |
|------|--------|----------------|
| **driver daemonset** | 以容器形式裝載 kernel driver（免烤進 AMI） | 節點上所有 CUDA 程式死亡；`nvidia-smi` 連不上 driver |
| **container toolkit** | 配置 container runtime（注入 device nodes、driver libs） | Pod 起得來但容器內看不到 GPU：`Failed to initialize NVML` |
| **device plugin** | 上一節講的，宣告與配置 `nvidia.com/gpu` | 節點 capacity 歸零 → 新 Pod 全部 Pending，但**既有 Pod 正常**（這個不對稱是診斷關鍵） |
| **GFD（GPU Feature Discovery）** | 把 GPU 屬性打成 node label（`nvidia.com/gpu.product` 等） | nodeSelector 永遠匹配不到 → Pending；症狀跟缺卡很像但原因完全不同 |
| **NFD（Node Feature Discovery）** | GFD 的前置，發現節點硬體特徵 | 同上游故障 |
| **DCGM + DCGM-exporter** | GPU 健康與遙測 → Prometheus（ch14 主場） | 監控盲區：卡在壞你看不見 |
| **MIG Manager** | 宣告式管理 MIG 切分（看 node label `nvidia.com/mig.config` 行動） | 改 profile 卡死在 pending：節點上還有 GPU Pod 沒清空 |
| **validator** | 每個環節裝完後跑冒煙測試 | 它本身 CrashLoop 通常代表上面某層沒就位 |

維運上最重要的一句話：**這是一條串聯的依賴鏈**（driver → toolkit → plugin → GFD），鏈上任何一環的版本不相容都以「最下游的元件 CrashLoopBackOff」呈現。診斷永遠從鏈的上游開始查。

另外，從 GPU Operator 近期版本開始，NVIDIA 的 DRA driver 也作為元件漸進整合進 chart（2026-06），這是下面 DRA 一節的伏筆。

## 共享技術三件套：time-slicing、MPS、MIG

Device plugin 不可分割，但「一個 dev notebook 占一整張 H100」在財務上不可辯護（成本帳見 ch16）。業界的三條繞路，本質完全不同：

| | **Time-slicing** | **MPS** | **MIG** |
|---|---|---|---|
| 本質 | 對 scheduler 謊報：一張卡宣告成 N 個 replicas，CUDA context 輪流跑 | NVIDIA 的多行程共享伺服器：多個 client 的 kernel **並行**共駐 | **硬體層分割**：SM、記憶體、L2、頻寬實體切開 |
| 算力隔離 | 無（時間片輪轉，互相干擾） | 部分（可設每 client 的 SM 比例，但是軟性的） | 硬隔離（SM slice 專屬） |
| 記憶體隔離 | **無**——一個 Pod OOM 或炸掉 CUDA context，同卡所有人陪葬 | 部分（Volta+ 有獨立位址空間、可設記憶體上限；但 fatal fault 仍可能拖垮整個 MPS server 上的所有 client） | 硬隔離（記憶體 slice 專屬、錯誤隔離到 instance） |
| 粒度 | 任意 N（謊報幾個都行） | 任意比例 | 固定 profile 表（下表） |
| 額外開銷 | context switch 開銷；延遲不可預測 | 低（kernel 真並行） | 近零，但切分本身有資源損耗（7 切只得 7×1g.10gb=70GB<80GB） |
| 動態性 | 改 ConfigMap 重啟 plugin | 行程級 | 改切法要清空節點（A100/H100 世代）|
| 適用 | dev/notebook、突發性小負載、demo | 推論小模型多副本、延遲敏感但信任同租戶 | **多租戶**、平台對外賣算力、SLA 場景 |
| 反模式 | 任何生產 serving | 不互信的租戶 | 大模型（一個 instance 裝不下 70B）|

H100 80GB 的 MIG profile 表（2026-06，依 NVIDIA MIG User Guide）：

| Profile | SM 比例 | 記憶體 | 每卡最多幾個 |
|---|---|---|---|
| `1g.10gb` | 1/7 | ~10 GB | 7 |
| `1g.20gb` | 1/7 | ~20 GB | 4 |
| `2g.20gb` | 2/7 | ~20 GB | 3 |
| `3g.40gb` | 3/7 | ~40 GB | 2 |
| `4g.40gb` | 4/7 | ~40 GB | 1 |
| `7g.80gb` | 7/7 | ~80 GB | 1 |

兩個 LLM serving 視角的關鍵點，廠商文件不會幫你劃重點：

1. **MIG 切的不只是容量，連 HBM 頻寬也跟著 memory slice 等比切**。ch03 證明過 decode 是 memory-bound，所以一個 `3g.40gb` instance 上的 8B 模型，decode 上限大約就是整卡的一半——不是「小模型用小切片就賺到」這麼單純，要回 roofline 算過才知道划不划算。
2. **time-slicing 的危險在 LLM 場景被放大**：推論引擎（vLLM）預設會吃掉 `gpu-memory-utilization`（預設 0.90~0.92，隨版本演進，見 ch08）比例的整卡記憶體當 KV cache（ch05/ch08）。兩個 vLLM 共享一張 time-sliced 卡 = 兩個都以為自己擁有九成以上的記憶體 = 必然 OOM。time-slicing 只該出現在 dev namespace。

K8s 介接方式：time-slicing 與 MPS 都是 device plugin 的 sharing config（ConfigMap）；MIG 則由 MIG Manager 看 node label 宣告式切分，device plugin 以兩種策略曝露——`single`（全節點同款切片，仍叫 `nvidia.com/gpu`）或 `mixed`（曝露 `nvidia.com/mig-3g.40gb` 這類獨立資源名）。`mixed` 靈活但會讓你的 quota 與排程邏輯多出 N 種資源名要管。

```yaml
# time-slicing 設定（示意）：把一張卡謊報成 4 個
apiVersion: v1
kind: ConfigMap
metadata:
  name: time-slicing-config
data:
  any: |-
    version: v1
    sharing:
      timeSlicing:
        resources:
        - name: nvidia.com/gpu
          replicas: 4
```

## DRA：把裝置變成排程器的一級公民

這是本章在 2026 年的重點演進。**DRA（Dynamic Resource Allocation）核心 API 已在 K8s 1.34（2025-08）GA**（`resource.k8s.io/v1`），1.35 設立的 AI Conformance program 把 DRA 列為第一個 MUST 要求，1.36 持續擴充功能集；OpenShift 4.21 已 GA、GKE 已提供 DRA 裝置管理（2026-06）。方向已經沒有懸念：DRA 是 device plugin 的繼任者。

### 四個物件、一個關鍵設計

DRA 的物件模型借鏡了你最熟的 PV/PVC/StorageClass 三角，幾乎可以逐字對應：

```
driver ──發布──► ResourceSlice（裝置庫存與屬性：UUID/型號/記憶體/拓撲/健康；≈ PV）
                      ▲
                      │ 讀庫存、用 CEL 評估
                 Scheduler ──配置決策──► ResourceClaim（使用者的裝置請求；≈ PVC）
                                             ▲      │
                 spec.resources.claims 引用  │      │ 引用
                                    Pod ─────┘      ▼
                                       DeviceClass（管理員定義：分類與預設選擇器；≈ StorageClass）

（ResourceClaimTemplate：模板物件，替每個 Pod 實例自動生成一份專屬的 ResourceClaim）
```

- **ResourceSlice**：driver 把每張卡的屬性發布成 API 物件——UUID、型號、記憶體、NVLink/PCIe 拓撲、健康狀態。裝置第一次在 K8s API 裡有了「長相」。
- **DeviceClass**：管理員定義裝置類別與預設過濾條件。
- **ResourceClaim / ResourceClaimTemplate**：workload 對裝置的請求，是一級物件，有獨立生命週期，**可以被多個容器、甚至多個 Pod 共享**。
- **關鍵設計是 structured parameters**：claim 的選擇條件用 CEL 表達式寫在 API 物件裡，**scheduler 自己就能評估**，不需要在排程路徑上 round-trip 詢問 driver。這讓裝置配置決策從 kubelet 的本地黑箱，搬進了 scheduler 的全局視野。

```yaml
# DRA 請求骨架（resource.k8s.io/v1，2026-06；CEL 屬性名依 driver 而異，示意）
apiVersion: resource.k8s.io/v1
kind: ResourceClaimTemplate
metadata:
  name: two-h100-same-domain
spec:
  spec:
    devices:
      requests:
      - name: gpus
        exactly:
          deviceClassName: gpu.nvidia.com
          allocationMode: ExactCount
          count: 2
          selectors:
          - cel:
              expression: >-
                device.attributes['gpu.nvidia.com'].productName.matches('H100') &&
                device.capacity['gpu.nvidia.com'].memory.compareTo(quantity('79Gi')) >= 0
---
apiVersion: v1
kind: Pod
metadata:
  name: tp2-worker
spec:
  resourceClaims:
  - name: gpus
    resourceClaimTemplateName: two-h100-same-domain
  containers:
  - name: vllm
    image: vllm/vllm-openai
    resources:
      claims:
      - name: gpus      # 不再是 nvidia.com/gpu: 2
```

### 逐條回收前面的限制清單

| Device plugin 的限制 | DRA 怎麼解 |
|---|---|
| 1. 不透明整數 | ResourceSlice 曝露完整屬性，claim 用 CEL 按屬性選（「≥40GB 的任何卡」「只要 H100」），同節點異質 GPU 自然表達 |
| 2. 不可分割 | partitionable devices 讓 MIG 切片成為可宣告的一級資源（動態切分，免翻桌）；consumable capacity 更進一步允許按量（如記憶體 GB）請求共享——兩者 2026-06 仍在 alpha/beta 演進中 |
| 3. Scheduler 看不到裝置 | structured parameters 讓 scheduler 直接做裝置層級決策，「同一 NVLink domain 的 2 張」可以表達；多節點 NVLink（GB200 NVL72 的 IMEX）由 NVIDIA driver 的 **ComputeDomain** 物件表達 |
| 4. 不能跨 Pod 共享 | ResourceClaim 是一級物件，多 Pod 可引用同一 claim |
| 5. 健康語意貧乏 | 裝置健康進入 API（device taints 等機制演進中），壞卡可以被精確標記與排除 |
| 6. 重新配置翻桌 | 配置是宣告式 claim 的滿足過程，driver 可動態建立 MIG instance 來滿足 claim |

### 過渡期的誠實評估（2026-06）

- **API 已穩，生態未滿**。NVIDIA 的 GPU DRA driver（已移交至 kubernetes-sigs，更名 `dra-driver-nvidia-gpu`）裡，ComputeDomain（多節點 NVLink）先一步達到正式支援——因為 GB200 NVL72 這種 rack-scale 機器（ch02）沒有 DRA 幾乎沒法在 K8s 上正確表達；單卡 GPU allocation plugin 較晚，v25.12 的 release notes 宣告其 GA，但截至我能確認的資訊（2026-06），Helm chart 的預設啟用狀態與文件描述仍在變動，部署前以 repo 當下的 README 為準。
- **生產主流仍是 device plugin**。我的建議：新叢集規劃時把 DRA 當 12–24 個月內的必然，現在就避免把「`nvidia.com/gpu` 整數」假設焊死在你的平台 API 與 quota 工具裡；但今天的生產 serving 還是走 device plugin 這條人最多的路。
- **Murphy 視角**：DRA 把配置決策搬進 scheduler，也把故障面搬了過去——以前查 kubelet 與 plugin 日誌，現在狀態分散在 ResourceSlice/ResourceClaim/scheduler events 三處；driver 與 K8s 版本的相容矩陣多了一個軸。新機制不會減少故障，只是換地方。

## 排程器生態：default scheduler 之上還缺什麼

Default scheduler 做的是「一個 Pod 找一個節點」的單體決策。GPU 叢集還需要三種它不提供的東西：

**1. 配額與佇列（誰可以用多少、超額了排隊）**——這是 **Kueue** 的領域。Kueue（v0.17.0，2026-03）不替換 scheduler，而是在 workload 進入排程前做 admission：

- `ClusterQueue` 定義配額（`nominalQuota`），多個 ClusterQueue 組成 `cohort` 互相**借用**閒置配額（`borrowingLimit` 限制能多借多少、`lendingLimit` 保留底線不外借——兩者在 v0.17 達 stable）。
- **搶占**：`reclaimWithinCohort` 讓配額擁有者把被借走的卡搶回來；`withinClusterQueue: LowerPriority` 處理隊內優先級。
- **Gang admission（all-or-nothing）**：`waitForPodsReady` 確保一個多 Pod workload 要嘛全進、要嘛全退回佇列重排——這是防止下面講的 gang deadlock 的關鍵。
- **Topology-Aware Scheduling（TAS）**：用 `kueue.x-k8s.io/podset-required-topology` annotation 要求整個 workload 落在同一拓撲域（同節點/同 rack），對接 ch09 講的「TP 不出 NVLink domain」物理。

**2. Gang scheduling（一組 Pod 同生共死）**——為什麼必要：一個 TP8 推論 job 需要 8 卡。兩個這樣的 job 同時到達一個只剩 12 卡的叢集，default scheduler 逐 Pod 排程，完全可能各給 6 卡——兩個 job 都永遠湊不齊、誰也不放手。這是分散式系統教科書的 deadlock，發生在排程層。**Volcano** 是這個領域的元老（HPC 血統，gang/fair-share/隊列），在訓練場景仍常見；推論平台這邊，Kueue 的 gang admission + LWS（下節）是 2026 年 K8s 原生的主流組合。

**3. 拓撲感知**——三個尺度：
- 節點內：8 卡機上挑 4 張卡跑 TP4，挑同一 NVSwitch 平面 vs 跨 PCIe，效能差距可觀（ch09 的 all-reduce 數學）；device plugin 時代只能 best-effort，DRA 時代可表達。
- 跨節點：PP/多節點 EP 的 worker 要落在同一 IB leaf switch 下；用 node label（rack/superpod topology label）+ TAS。
- Rack-scale：NVL72 世代「72 卡一個 NVLink domain」直接改寫「節點」的定義，ComputeDomain 就是為此而生。

### Bin-packing vs spread：碎片化是錢

你的無狀態服務直覺是 spread（抗節點故障）。GPU 叢集常常要反過來：

```text
8 節點 × 8 卡，每節點被 1 個單卡 dev pod 占住（spread 的結果）：

node1 [X·······]  node2 [X·······]  ...  node8 [X·······]

帳面：64 卡用了 8 張，「利用率 12%，還有 56 張可用」
現實：一個 8 卡 gang job 永遠 Pending——沒有任何節點湊得出 8 張
```

這叫 **GPU 碎片化**：叢集有卡，但湊不出形狀。碎掉的卡是付了錢買不到產能的卡（成本帳見 ch16）。防禦三件組：

1. **Bin-packing scoring**：把 scheduler 對 GPU 資源的評分策略改成 `MostAllocated`（塞滿一台再開下一台），犧牲一點故障域分散換完整節點的供給。
2. **大小分池**：單卡的零碎負載（dev、小模型）與整機負載（TP8、訓練)分 node pool，互不污染。
3. **Gang + 佇列**：湊不齊就排隊等，而不是先占住一部分卡釀 deadlock。

```yaml
# 第二 scheduler 的 bin-packing profile（示意）
apiVersion: kubescheduler.config.k8s.io/v1
kind: KubeSchedulerConfiguration
profiles:
- schedulerName: binpack-gpu
  pluginConfig:
  - name: NodeResourcesFit
    args:
      scoringStrategy:
        type: MostAllocated
        resources:
        - name: nvidia.com/gpu
          weight: 5
        - name: cpu
          weight: 1
```

## 多節點推論的部署原語：LWS

一個 70B TP4 副本是「一個 Pod 用 4 卡」，Deployment 就夠。但 405B 或大 MoE 的一個「副本」橫跨多節點（ch09/ch10）——比如 2 節點 16 卡 PP2×TP8——這時 K8s 的內建 workload 物件全部不夠用：

- Deployment：副本之間無關係，無法表達「這 2 個 Pod 是同一個模型實例」。
- StatefulSet：有穩定身分，但沒有「leader + workers 成組」語意、沒有組級 gang 排程、沒有「一個成員死了整組重啟」的故障語意——而多節點推論一個 worker 掛掉，整個實例就廢了（NCCL 世界的連坐，ch15）。

**LeaderWorkerSet（LWS，v0.8.0，2026-01）** 就是為此造的原語：把「1 leader + N workers」當成一個複製單位，提供組級的啟動順序（leader 先起、把位址注入 workers）、組級重啟、配合 Kueue 做整組 gang admission（Kueue 已原生支援 LWS workload）。

```yaml
# LWS 骨架（示意）：每個副本 = 2 節點 × 8 卡
apiVersion: leaderworkerset.x-k8s.io/v1
kind: LeaderWorkerSet
metadata:
  name: llama-405b
spec:
  replicas: 2            # 2 個模型實例
  leaderWorkerTemplate:
    size: 2              # 每實例 1 leader + 1 worker
    restartPolicy: RecreateGroupOnPodRestart   # 一人死全組重啟
    leaderTemplate:
      spec:
        containers:
        - name: vllm
          resources: { limits: { nvidia.com/gpu: 8 } }
    workerTemplate:
      spec:
        containers:
        - name: vllm
          resources: { limits: { nvidia.com/gpu: 8 } }
```

LWS 之上怎麼跑 vLLM/SGLang 的多節點 serving、router 怎麼接，是 ch12 的事。

## 節點生命週期：GPU 節點是寵物，假裝不了牛

**健康檢測迴路**。GPU 的硬體故障率遠高於 CPU（ch02 講過 Xid 家族與 MTBF 現實）。生產叢集的標準迴路是：DCGM 持續跑健康檢查 → 偵測到 ECC double-bit、Xid 79（fallen off the bus）等致命錯誤 → 自動 cordon + drain + 開 ticket。實作上是 DCGM-exporter 指標 + 告警驅動自動化，或 node-problem-detector 自訂 plugin；device plugin 也會把壞卡標 unhealthy 讓 capacity 減一，但如前述，這個訊號太粗，節點級的自動隔離還是要自己組。沒有這條迴路的下場：壞卡留在池子裡，工作負載排上去、CUDA error、重試、又排上去——你在 ch15 會看到這個模式的完整屍檢。

**版本相容矩陣**。一個 GPU 節點上至少四層要對齊：kernel driver ↔ CUDA runtime（容器內）↔ NCCL ↔ 框架（PyTorch/vLLM）。driver 是節點級單例、其他三層是 workload 級，這個不對稱是維運地獄的根源：升級 driver 是全節點事件（驅動換掉，跑著的 CUDA 程式全部報廢），而不同團隊的 image 各自鎖著不同的 CUDA 版本。CUDA 的 minor version compatibility 給了一些緩衝（新 driver 跑舊 CUDA runtime 通常可以），但反向不行。紀律：driver 版本當成基礎設施規格管理（IaC 釘版本、canary node pool 先升、相容矩陣進 CI 檢查），永遠不讓「自動升級」碰 GPU 節點。

**Node pool 升級策略**。GPU 節點的 drain 比你習慣的貴兩個數量級：上面跑的可能是分鐘級的 streaming 請求（drain 預算要照 p99.9 請求時長設計，ch15 有完整數學）、或是殺了就損失數小時進度的訓練 job。可行做法：surge 升級（先擴後縮，但 GPU 節點貴且常常缺貨，surge 容量不一定租得到）、按 node pool 分批、配合 Kueue 把 batch 負載 requeue 到別處。「GPU 節點當牛養」是 2026 年仍未實現的理想，承認它們是寵物，把照顧流程自動化，比假裝它們是牛實際。

## Worked example：64 卡叢集的三租戶配額設計

**場景**：8 節點 × 8 H100（節點內 NVLink，跨節點 IB）。三個租戶：

- **team-chat**（產品）：70B FP8、TP4 副本（每副本 4 卡）。穩態 5 副本 = 20 卡，尖峰 6 副本 = 24 卡。
- **team-api**（產品）：8B 單卡副本 × 12 穩態，尖峰 16；外加 embedding 服務。
- **research**：訓練與評估 batch job，形狀從單卡到 8 卡 gang 不等，吞吐導向，可被搶占。

**配額分配**：team-chat nominal 24、team-api nominal 16、research nominal 24，合計 64。設計原則：

1. **產品隊的 nominal 按尖峰配**，不是穩態——GPU 沒有超賣兜底，尖峰借不到就是 SLO 事故（autoscaling 的訊號與時序見 ch13）。
2. **產品隊穩態用不滿的部分（chat 閒 4 卡、api 閒 4 卡）就是 research 夜間的金礦**：research 可借到 48 卡（nominal 24 + borrowingLimit 24）。
3. **借來的卡是有條件的**：產品隊配 `reclaimWithinCohort: Any`，流量回來時無條件搶回；research 配 `reclaimWithinCohort: Never`——只當債務人，不當搶匪。
4. **research 保底**：`lendingLimit: 16` 保證自己手上永遠留 8 卡做不可中斷的實驗。

優先級三層：`prod-critical`（1000）> `prod-batch`（500）> `research-default`（100）。搶占順序由低往高倒著死。

YAML 骨架（Kueue v1beta1；註：上游已引入 v1beta2、v1beta1 走向棄用（2026-06），套用前先 `kubectl api-resources` 確認你叢集的版本）：

```yaml
apiVersion: kueue.x-k8s.io/v1beta1
kind: ResourceFlavor
metadata:
  name: h100
spec:
  nodeLabels:
    nvidia.com/gpu.product: NVIDIA-H100-80GB-HBM3
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: cq-team-chat
spec:
  cohort: shared-h100
  namespaceSelector:
    matchLabels: { team: chat }
  preemption:
    reclaimWithinCohort: Any          # 流量回來，無條件搶回被借走的配額
    withinClusterQueue: LowerPriority
  resourceGroups:
  - coveredResources: ["nvidia.com/gpu"]
    flavors:
    - name: h100
      resources:
      - name: "nvidia.com/gpu"
        nominalQuota: 24
        borrowingLimit: 8             # 極端尖峰可再借 8（誰閒借誰）
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: ClusterQueue
metadata:
  name: cq-research
spec:
  cohort: shared-h100
  namespaceSelector:
    matchLabels: { team: research }
  preemption:
    reclaimWithinCohort: Never        # 只借不搶
    withinClusterQueue: LowerPriority
  resourceGroups:
  - coveredResources: ["nvidia.com/gpu"]
    flavors:
    - name: h100
      resources:
      - name: "nvidia.com/gpu"
        nominalQuota: 24
        borrowingLimit: 24            # 夜間最多膨脹到 48
        lendingLimit: 16              # 保底 8 卡永不外借
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: LocalQueue
metadata:
  name: lq-research
  namespace: research
spec:
  clusterQueue: cq-research
---
apiVersion: kueue.x-k8s.io/v1beta1
kind: WorkloadPriorityClass
metadata:
  name: research-default
value: 100
---
# namespace 級硬上限：防止任何配置錯誤讓單一租戶吃光叢集
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gpu-hard-cap
  namespace: research
spec:
  hard:
    requests.nvidia.com/gpu: "48"     # nominal 24 + borrowingLimit 24
```

research 的 8 卡 gang job 再加兩道保險：Kueue 的 `waitForPodsReady`（all-or-nothing，防 gang deadlock）與 TAS annotation 要求落在同一節點：

```yaml
# research 的 Job pod template（節選，示意）
metadata:
  annotations:
    kueue.x-k8s.io/podset-required-topology: kubernetes.io/hostname
spec:
  priorityClassName: research-default
  containers:
  - resources: { limits: { nvidia.com/gpu: 8 } }
```

**走一遍一天的劇本**：23:00 產品流量退潮，chat 縮到 4 副本（16 卡）、api 縮到 10 卡——叢集閒出 14 卡；research 佇列裡的 job 依序 admit，借滿到 38 卡上下。07:30 流量回升，chat 的第 6 副本要 4 卡但叢集滿載 → Kueue 依 `reclaimWithinCohort` 挑 research 借用中、優先級最低的 workload evict（整組 gang 一起退，不會殺半套）→ 4 卡釋放 → 產品副本就位。research job 回佇列等下一個低谷。**設計的隱含前提是 research workload 必須可中斷**（checkpoint 紀律），這是借用方案的社會契約：借到的算力本來就是會被收走的算力。

最後一個誠實註記：Kueue 管「誰先進、用多少」極好，但 serving 副本是長駐 Pod，它的容量主要由 ch13 的 autoscaling 管理；這套方案裡 Kueue 的主要客戶是 research 與兩個產品隊的 batch 類負載，產品 serving 的保障來自 nominal 配額 + 搶占權的組合。

## 故障模式與防禦

| 故障 | 症狀 | 怎麼觀測 | 防禦 |
|------|------|----------|------|
| device plugin 崩潰 | 新 Pod 全部 Pending（`Insufficient nvidia.com/gpu`），既有 Pod 卻正常；`nvidia-smi` 看卡明明都在 | `kubectl describe node` 看 Capacity/Allocatable 歸零；plugin DaemonSet 日誌 | 對「節點 GPU capacity 突降」設告警；plugin 升級走 canary |
| driver/CUDA 不相容 | 容器 CrashLoop：`CUDA driver version is insufficient for CUDA runtime version` | 容器日誌 + 節點 driver 版本比對 | 相容矩陣進 CI；driver 版本 IaC 釘死；canary node pool |
| toolkit/runtime 配置壞 | Pod Running 但容器內 `Failed to initialize NVML` | validator pod 狀態；toolkit 日誌 | GPU Operator validator 常開；節點上線冒煙測試 |
| GFD/NFD label 缺失 | Pending，但原因是 nodeSelector 匹配不到（跟缺卡長得很像） | `kubectl get node --show-labels` 對照 Pod 的 selector | 把關鍵 label 存在性納入節點 readiness 檢查 |
| MIG 重切卡死 | `mig.config` label 改了但狀態停在 pending | MIG Manager 日誌：等待節點清空 | 重切流程綁 drain 自動化；用 `mixed` 策略前想清楚資源名爆炸 |
| time-slicing 連坐 OOM | 同卡多個 Pod 同時死；dmesg 有 Xid | DCGM/dmesg + 同節點 Pod 死亡時間相關性 | time-slicing 限 dev namespace；生產一律 MIG 或整卡 |
| GPU 碎片化 | 大 gang job 永遠 Pending，帳面利用率卻很低 | 每節點 free GPU 直方圖（不是叢集總和！） | bin-packing scoring、大小負載分池、gang admission |
| gang deadlock | 兩個多卡 job 各占一半資源互等，叢集假死 | 多個 job 長期 partial running | Kueue `waitForPodsReady` / Volcano gang；禁止裸 Pod 搶多卡 |
| preemption storm | 高優先負載觸發連鎖搶占；被殺的推論 Pod 重啟要重載權重（分鐘級），服務真空 | eviction events 突增 + 容量曲線 | 搶占代價意識：headroom 留足（ch13）、低優先層用 `preemptionPolicy: Never` 的中間層緩衝、checkpoint 紀律 |
| 壞卡迴圈 | 某節點上的 job 反覆 CUDA error → 重排 → 又錯 | 同一節點的失敗率異常集中；DCGM Xid 計數 | DCGM 健康檢查 → 自動 cordon/drain 迴路（ch15 詳） |

共同主題：GPU 世界的故障訊號常常**長得跟排程問題一模一樣**（都是 Pending/CrashLoop），而排程問題又常常是錢的問題（碎片化）。診斷的第一步永遠是分清楚：是沒有卡、看不到卡、還是湊不出形狀。

## 動手做

### Lab：用 kind + KWOK + fake-gpu-operator 搭一座 64 卡模擬叢集 **[M1]**

本章重頭戲，對應 plan.md 旗艦專案①的地基。零 GPU 費用，在 M1 上模擬出本章 worked example 的那座 64 卡叢集，親手觀察排程、碎片化、配額借用與搶占。後續 ch12/ch13/ch14 的實驗都長在這座叢集上，值得把它做成一鍵 `setup.sh`。

策略是雙層模擬：**kind 真節點 + fake-gpu-operator** 提供高擬真層（真的 device plugin 流程、假 `nvidia-smi`、DCGM 指標）；**KWOK 假節點**提供規模層（湊滿 8 節點 64 卡，只為餵 scheduler）。要懂的限制：KWOK 節點上的 Pod 是被 kwok controller「宣告成 Running」的，不真執行——所以 DaemonSet（含 device plugin）在 KWOK 節點上也是假的，64 卡的 capacity 要直接寫進假節點的 status。這個限制本身就是教材：你會被迫分清楚「device plugin 宣告資源」與「節點 status 有資源」是兩件事。

**Step 0 — 工具**（已有 Docker/colima 環境）：

```bash
brew install kind kubectl helm
# kwok 用 manifest 安裝進叢集即可，不需本機 binary
```

**Step 1 — kind 叢集**：1 control-plane + 2 worker（這 2 個是高擬真 GPU 節點）。

```bash
cat <<EOF | kind create cluster --name gpu-sim --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
- role: control-plane
- role: worker
- role: worker
EOF
```

**Step 2 — fake-gpu-operator**（v0.0.x 系列，活躍維護中，2026-06）：標記節點、用 Helm 裝，topology 設成每節點 8 張 H100。

```bash
kubectl label node gpu-sim-worker gpu-sim-worker2 \
  run.ai/simulated-gpu-node-pool=default

helm upgrade -i fake-gpu-operator \
  oci://ghcr.io/run-ai/fake-gpu-operator/fake-gpu-operator \
  --namespace gpu-operator --create-namespace \
  --set topology.nodePools.default.gpuProduct=NVIDIA-H100-80GB-HBM3 \
  --set topology.nodePools.default.gpuCount=8
```

**成功標準**：`kubectl describe node gpu-sim-worker` 出現 `nvidia.com/gpu: 8`；部署一個 requests `nvidia.com/gpu: 2` 的測試 Deployment 能排上去，exec 進 Pod 跑 `nvidia-smi` 看到假的 H100 清單（fake-gpu-operator 注入的模擬器；若你的 image 太精簡看不到，換 ubuntu 基底）。順手看一眼它的 DCGM exporter 假指標——ch14 會接 Prometheus。

**Step 3 — KWOK 擴規模**：裝 kwok controller 與 stages，然後造 6 個假 GPU 節點，湊滿 8×8=64。

```bash
KWOK_REPO=kubernetes-sigs/kwok
LATEST=$(curl -s https://api.github.com/repos/${KWOK_REPO}/releases/latest | jq -r .tag_name)
kubectl apply -f https://github.com/${KWOK_REPO}/releases/download/${LATEST}/kwok.yaml
kubectl apply -f https://github.com/${KWOK_REPO}/releases/download/${LATEST}/stage-fast.yaml

for i in $(seq 0 5); do
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Node
metadata:
  name: kwok-gpu-${i}
  annotations:
    kwok.x-k8s.io/node: fake
  labels:
    type: kwok
    nvidia.com/gpu.product: NVIDIA-H100-80GB-HBM3
spec:
  taints:
  - key: kwok.x-k8s.io/node
    value: fake
    effect: NoSchedule
status:
  allocatable: { cpu: "64", memory: 512Gi, nvidia.com/gpu: "8", pods: "110" }
  capacity:    { cpu: "64", memory: 512Gi, nvidia.com/gpu: "8", pods: "110" }
EOF
done
```

**成功標準**：`kubectl get nodes` 看到 9 個節點；對假負載加上 toleration 後，requests 64 卡的總量可以全數排上。注意我們給假節點上了 taint——這是模擬叢集的衛生習慣，防止真元件（如 Prometheus）被排到假節點上「假裝運行」，這種靜默的假成功是模擬環境最陰的故障模式。

**Step 4 — 碎片化實驗**：先用 podAntiAffinity（或手動 nodeName）把 8 個單卡 Pod 一節點一個撒開，再提交一個 8 卡 Pod。

**成功標準**：8 卡 Pod Pending，event 顯示 `0/9 nodes are available: ... Insufficient nvidia.com/gpu`——同時 `kubectl describe nodes | grep -A2 'nvidia.com/gpu'` 顯示叢集還有 56 張閒卡。把這兩個輸出截圖並排，就是「碎片化是什麼」的完美教材。然後部署上面那個 `MostAllocated` 的第二 scheduler，把單卡 Pod 換成 `schedulerName: binpack-gpu` 重撒一次，驗證它們聚到最少的節點上、8 卡 Pod 立刻可排。

**Step 5 — Kueue 配額與搶占**：裝 Kueue，套用 worked example 的全套 YAML（三個 ClusterQueue、cohort、優先級）。然後演那場「夜間借卡、白天搶回」的戲：

1. 以 research 身分提交一批 8 卡 Job（帶 `kueue.x-k8s.io/queue-name: lq-research`），讓它借用到 40+ 卡。
2. 以 team-chat 身分提交高優先 workload 把配額需求頂回 24。
3. 觀察：`kubectl get workloads -A` 與 events——research 的 workload 被 evict（整組、不是殺一半）、requeue，chat 的 workload admit。

**成功標準**：能用 `kubectl describe clusterqueue cq-research` 的 `flavorsUsage` 講出借用量的變化曲線；能指著 event 時間軸說明 reclaim 的因果鏈。

**Step 6（選做）— MIG 模擬**：fake-gpu-operator 支援基本的 MIG 資源模擬（2026-06，功能標註為 basic），把一個 node pool 的 topology 改成 MIG profile、用 `nvidia.com/mig-3g.40gb` 資源名部署小負載，體驗 `mixed` 策略下 quota 與 nodeSelector 的管理面積膨脹。

整個 lab 估半天到一天。最有價值的產出不是叢集本身，而是你把每一步「預期 vs 實際」寫下來的紀錄——模擬器與真叢集的差異清單（KWOK Pod 不真跑、fake nvidia-smi 沒有真功耗、沒有真 NVLink 拓撲），就是你對「這套機制的本體 vs 表象」理解程度的測驗。

### 紙上推演：MIG 的 roofline 帳 **[紙上推演]**

用 ch02/ch03 的方法算：8B 模型 FP16 放在 H100 的 `3g.40gb` instance（約 1/2 記憶體頻寬）上，decode 理論 token rate 上限是整卡的幾成？同一張卡切 2 個 `3g.40gb` 跑兩個 8B 副本，總吞吐跟整卡跑一個大 batch 的 8B 比，誰贏？贏多少？（提示：答案取決於 batch size 是否已經把整卡推到 compute-bound——這題做完，你對「要不要切 MIG」就有決策框架了。）

## 這個領域往哪走

- **DRA 全面接管是時間問題**：AI Conformance 把 DRA 列為 MUST、主要發行版陸續 GA，未來 1–2 年新叢集會以 DRA 為預設資源模型，device plugin 進入長尾維護。值得押注的理解是物件模型與 structured parameters 的設計，不是某個 driver 的安裝細節。
- **「可分割、可計量」的 GPU 語意**（partitionable devices、consumable capacity）成熟後，GPU 會第一次擁有接近 CPU/memory 的請求語意——屆時 quota、bin-packing、共享技術三件套的邊界都會重畫。
- **排程的單位在變大**：NVL72 之後 rack 是新的「節點」，ComputeDomain 這類「一組互連硬體」的抽象會越來越重要；電力與功耗作為排程約束（power-aware scheduling）也開始進入視野（ch17）。

## 自我檢核

1. Device plugin 模型下，為什麼 GPU 不可超賣、requests 必須等於 limits？scheduler 與 kubelet 在一次 GPU 配置中各做了什麼決策、各看不到什麼？
2. 面試官給你三個場景：20 人的 data science notebook 平台、一個 8B 模型要跑 12 個低延遲副本、對外賣 GPU 算力的多租戶平台——time-slicing/MPS/MIG 各選哪個？說出每個選擇的隔離邊界與代價。
3. DRA 的四個物件（ResourceSlice/DeviceClass/ResourceClaim/ResourceClaimTemplate）分別由誰建立、誰消費？structured parameters 解了 device plugin 的哪一條根本限制，為什麼這讓拓撲感知排程變得可能？
4. 叢集帳面還有 56 張閒卡，一個 8 卡 job 卻 Pending 了三小時。給出你的診斷步驟（看什麼指令的什麼輸出），以及三種預防機制。
5. 用 Kueue 的 `nominalQuota`/`borrowingLimit`/`lendingLimit`/`reclaimWithinCohort` 解釋「研究隊夜間借卡、產品隊白天搶回」怎麼實現。借用方案對研究隊的 workload 形態提出了什麼隱含要求？
6. 為什麼 LLM serving Pod 被 preempt 的代價遠高於一般 web 服務的 Pod？這對 priority class 與 headroom 設計有什麼含意？
7. GPU 節點的 driver 升級為什麼不能像一般 node pool 一樣滾動了事？至少列出三層需要對齊的版本，以及一個安全的升級流程。
8. StatefulSet 拿來部署一個 2 節點 16 卡的推論實例，會在哪三個地方不夠用？LWS 各用什麼機制補上？

## 延伸閱讀

- [Kubernetes 官方文件：Dynamic Resource Allocation](https://kubernetes.io/docs/concepts/scheduling-eviction/dynamic-resource-allocation/) — DRA 物件模型與 CEL selector 的權威定義，讀完本章後對照 API 細節的第一站。
- [Kubernetes v1.34 DRA GA 公告](https://kubernetes.io/blog/2025/09/01/kubernetes-v1-34-dra-updates/) 與 [v1.36 DRA 更新](https://kubernetes.io/blog/2026/05/07/kubernetes-v1-36-dra-136-updates/) — 官方視角的演進路線，後者也介紹了 AI Conformance 與 DRA 的關係。
- [NVIDIA GPU Operator 文件](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/) — 全家桶每個元件的安裝與配置細節，特別是 GPU sharing（time-slicing/MPS）與 DRA driver 整合章節。
- [NVIDIA MIG User Guide](https://docs.nvidia.com/datacenter/tesla/mig-user-guide/) — profile 表、切分規則與限制的一手來源。
- [Kueue 官方文件](https://kueue.sigs.k8s.io/docs/) — ClusterQueue/cohort/preemption/TAS 的概念文件寫得意外地好，本章 worked example 的所有欄位語意都能在這裡查證。
- [LeaderWorkerSet 文件](https://lws.sigs.k8s.io/) — 多節點推論部署原語的設計動機與 API。
- [KWOK](https://kwok.sigs.k8s.io/) 與 [run-ai/fake-gpu-operator](https://github.com/run-ai/fake-gpu-operator) — 本章 lab 的兩塊地基；fake-gpu-operator 的 README 含 DRA 與 ComputeDomain 模擬的最新支援狀態。
- [kubernetes-sigs/dra-driver-nvidia-gpu](https://github.com/NVIDIA/k8s-dra-driver-gpu) — NVIDIA GPU 的 DRA driver（原 NVIDIA org，已移交 kubernetes-sigs），追蹤 GPU allocation 與 ComputeDomain 支援進度的源頭。
