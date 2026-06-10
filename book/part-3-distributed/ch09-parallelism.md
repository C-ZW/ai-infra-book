# ch09 — 平行化策略：當一張卡裝不下

> **本章解決什麼問題**：ch03 算過那筆帳——70B 模型的 BF16 權重比一張 H100 還大，「單卡跑 70B」在物理上不成立；405B 與 1T 級 MoE 更不用說。本章回答「怎麼切」：TP/PP/DP/EP/SP 五種平行化各自的機制、通訊代價公式、適用場景，以及支撐它們的 NCCL 集合通訊層。讀完你要能對「給定模型＋給定硬體＋給定 SLO」做出有數字佐證的平行策略決策。這章是 Part III 的地基：ch10 的 P/D 分離建立在「prefill 與 decode 適合不同平行配置」之上，ch11 的拓撲感知排程、ch15 的 NCCL 故障處理，前提都在這裡。

## 從你已知的出發

你做過的每一個資料庫擴展決策，在這一章都有對應物——只是物理常數變了。

- **Tensor parallelism ≈ 水平 sharding，但每個 query 都是 cross-shard join**。你知道 sharding 的鐵律：切了之後最好別讓查詢跨 shard。TP 正好違反這條鐵律——它把每一層的權重矩陣切到 N 張卡上，於是**每生成一個 token、每一層**都要做一次跨卡的中間結果合併。這就是為什麼 TP 對網路的要求苛刻到只有 NVLink 等級的互連才扛得住：你不會把一個每秒 join 幾萬次的 shard 對拆到兩個 region，同理你不會把 TP 拆到兩個節點。
- **Pipeline parallelism ≈ 你的結算 pipeline**。K8s CronJobs → SQS → consumer 那套：每個 stage 做完自己的部分、把結果交給下一棒。PP 把模型的 80 層切成幾段，每段住一張卡（或一個節點），卡間只傳「接力棒」（hidden state）。吞吐由最慢的 stage 決定、pipeline 有暖機與排空的空轉（bubble）——這些你在 SQS pipeline 上都見過。
- **Data parallelism ≈ read replica**。複製整份模型，路由器分流。你用 RDS read replica 解讀流量的思路原封不動成立，連缺點都一樣：每個 replica 的快取是獨立的（這裡是 prefix cache，ch05），路由亂打會把快取命中率打碎——這個問題留給 ch10 的 KV-aware routing。
- **Expert parallelism ≈ partition by key 的熱分區問題**。MoE 的 router 按 token 把工作分發給 expert（ch03），EP 把 expert 攤到多張卡上——這就是 partition by key。而你在 DynamoDB／SQS 上被熱分區咬過的那一口，在這裡叫 hot expert：某幾個 expert 被瘋狂路由，持有它們的 GPU 變成全組的瓶頸。
- **NCCL ≈ shard 之間的 RPC 層，但比你用過的任何 RPC 都脆**。它是同步的、沒有重試、沒有 timeout 預設（有也是分鐘級）、一個參與者失蹤時其他人會永遠等下去。你的分散式直覺全部適用，但防禦工事要重建（ch15）。

一個提醒：本章只談**推論**的平行化。訓練的平行化（FSDP、ZeRO、gradient 同步那些）是另一個世界，本書不涵蓋——推論沒有 backward pass、沒有 optimizer state，問題簡化很多，但對延遲的要求嚴苛得多。

## 為什麼要切：三種動機，三種切法

「要不要平行化、怎麼平行化」不是一個問題，是三個。動機不同，正確的切法完全不同：

| 動機 | 問題長相 | 對症的切法 |
|---|---|---|
| **裝不下**（capacity） | 權重 + KV cache > 單卡 HBM。70B BF16 = 141 GB > 80 GB，無解，必須切 | TP（單節點內）、PP（跨節點）、EP（MoE） |
| **太慢**（latency） | 裝得下，但 decode 是 memory-bound（ch03），單卡 3.35 TB/s 的頻寬就是 token rate 的天花板 | TP——N 張卡聚合 N 倍頻寬，每 token 的權重讀取時間除以 N |
| **不夠多**（throughput） | 單副本的 goodput 餵不飽流量 | DP——加副本，最便宜、最該優先考慮的 scale-out |

三個推論值得先記住：

1. **「裝不下」是硬約束，另外兩個是軟約束。** 記憶體帳不過關，其他都不用談。所以每個平行決策的第一步永遠是 ch03 那三本帳：權重、KV、activation。
2. **TP 是唯一能降低單請求延遲的切法。** PP 不會讓單一 token 變快（層還是得一層層算），DP 更不會。如果你的問題是 ITL 太高，加 replica 沒有用。
3. **能用 DP 就不要用更複雜的。** DP 副本之間零通訊、故障隔離乾淨、運維面積最小。TP/PP/EP 都是在「單副本本身放不下或不夠快」時才引入的複雜度。這跟你對「能加 read replica 解決的就別動 sharding」的直覺完全一致。

實際部署幾乎都是組合拳：405B 可能是「節點內 TP8 × 跨節點 PP2」再乘上 DP 副本；DeepSeek 級 MoE 是「attention 用 DP、FFN 用 EP」。下面逐一拆解每種切法，最後再組裝回來。

## Tensor Parallelism：把每一層橫著切

### 機制：矩陣怎麼切，通訊就怎麼來

TP（tensor parallelism）把**每一層內部**的權重矩陣沿著某個維度切開，N 張卡各拿 1/N，一起算同一個 token。以 Llama-3.3-70B 的一層為例（形狀見 ch03），Megatron-LM 確立的標準切法是：

```
attention 區塊：
  W_Q / W_K / W_V：按 head 切（column-parallel）
     64 個 Q head、8 個 KV head 平分到 N 張卡 → 每卡算自己那幾個 head，不需通訊
  W_O：按行切（row-parallel）
     每卡算出部分和 → 需要一次 all-reduce 把 N 份部分和加總

FFN 區塊：
  W_gate / W_up：column-parallel（28672 維平分）→ 不需通訊
  W_down：row-parallel → 又一次 all-reduce
```

切法的巧妙在於：先 column 後 row 的配對讓中間結果**留在本卡**，整層只在兩個出口處各同步一次。代價是固定的：**每層 2 次 all-reduce，每次的 payload 是「該步處理的 token 數 × hidden size × activation 精度」**。80 層的模型，生成一個 token 要做 160 次 all-reduce——這個數字是 TP 一切性質的根源。

KV cache 也跟著 head 切：TP2 下每卡存 4 個 KV head 的 cache，TP8 下每卡存 1 個。總 KV 容量不變，但平攤到了 N 張卡的 HBM 上——這是 TP 附贈的好處：**聚合的 KV 池跟著變大**。

### 通訊代價公式

ring all-reduce 的標準結果：對 payload 為 S bytes 的一次 all-reduce，每張卡要送出（也收進）`2 × (N−1)/N × S` bytes。TP 推論的每卡通訊量：

```
每 token 每卡 TP 通訊量 = L 層 × 2 次 × 2(N−1)/N × (h × b)

Llama-3.3-70B（L=80、h=8192、activation BF16 b=2 → 每次 payload 16 KiB/token）：
  TP2：80 × 2 × 1.0 × 16 KiB = 2.5 MB/token/卡
  TP4：80 × 2 × 1.5 × 16 KiB = 3.75 MB/token/卡
  TP8：80 × 2 × 1.75 × 16 KiB = 4.4 MB/token/卡
```

2.5 MB/token 看起來不多——對 NVLink 4 的 450 GB/s（每方向，ch02）來說是 6 μs 的事。真正的殺手是**次數**：每次 collective 都有與資料量無關的啟動延遲（kernel launch、同步、協定握手，NVLink 上約幾 μs，PCIe／網路上是幾十 μs）。把任何 collective 的耗時想成：

```
T ≈ α（每次啟動延遲） + S / BW（資料量 ÷ 頻寬）
```

decode 的 payload 小（KB 級）→ **α 項主宰**：160 次 × 4 μs ≈ 0.6 ms/token，對一個 10~20 ms 的 decode step 來說是 3~6% 的稅，TP 度越高、互連越慢，稅越重。prefill 的 payload 大（一次塞幾千個 token，payload 是 MB~百 MB 級）→ **頻寬項主宰**，這時 NVLink 與 PCIe 的 10 倍頻寬差會直接反映在 TTFT 上。本章 worked example 會把這兩筆帳算給你看。

### 為什麼 TP 幾乎不出節點

把 ch02 的斷層線搬過來：節點內 NVLink 4 是 450 GB/s 每方向，跨節點 IB NDR 是 50 GB/s 每方向——9 倍；α 延遲也差一個數量級。TP 每 token 同步 160 次的性格，撞上這個斷層就是災難：通訊時間會從「個位數百分比的稅」變成「主導項」。所以業界鐵律：**TP 度 ≤ 單一 NVLink 域的卡數**（傳統 HGX 機器是 8；NVL72 機櫃把這個邊界撐到 72，見 ch02/ch17）。跨節點，用別的切法。

### TP 的適用判斷與隱藏限制

- **適用**：模型裝不進單卡、或單卡頻寬撐不住 ITL 目標時的**第一選擇**，前提是卡之間有 NVLink。vLLM 一個參數就開：`--tensor-parallel-size N`。
- **整除限制**：attention head 數、KV head 數最好能被 N 整除。Llama-3.3-70B 有 8 個 KV head，TP 開到 8 是乾淨的；開 TP16 時 KV head 不夠分，引擎會**複製** KV head——意思是 KV cache 總量不再隨 TP 變大而攤薄，你以為的容量收益憑空消失。MLA 模型（DeepSeek 系）更極端：KV 是單一 latent（ch03），TP 下整份 KV 在每卡複製一份——這是後面「DP attention」存在的根本原因。
- **報酬遞減**：TP2→TP4→TP8，每卡的權重讀取減半，但 α 稅照付、payload 的 (N−1)/N 係數還微幅上漲。經驗上 dense 模型 TP8 之後（跨出 NVLink 域之前）就接近收益盡頭。
- **吞吐視角的反直覺**：同樣 8 張卡，TP8 單副本的吞吐通常**低於** TP2 × 4 副本（通訊稅 × 排程彈性差），但 TP8 的單請求延遲更低、能跑更大的模型。延遲買吞吐，這是 TP 度的本質取捨。

## Pipeline Parallelism：把模型直著切

### 機制與通訊代價

PP（pipeline parallelism）按**層**切：80 層切成 4 個 stage，每 stage 20 層，住在一張卡或一個節點上。token 的計算像接力賽跑過 4 棒，stage 之間只傳一樣東西：該 token 算到一半的 hidden state。

```
每 token 每個 stage 邊界的 PP 通訊量 = h × b = 8192 × 2 bytes = 16 KiB
```

對比 TP 的 2.5 MB/token——**PP 的通訊量比 TP 小兩個數量級，而且每 token 每邊界只傳一次**（不是 160 次）。16 KiB 走 50 GB/s 的 IB 不到 1 μs，走 100GbE 也才幾 μs。這就是 PP 的存在理由：**它是唯一對跨節點友善的模型切法**。模型大到單節點 8 卡裝不下時（405B BF16、1T 級 MoE 的非 EP 部分），PP 是跨節點的標準答案。

### Bubble：pipeline 的空轉

PP 的代價不在通訊量，在**空轉**。單一請求跑 PP4 時，任一時刻只有一個 stage 在工作、其他三個在等——延遲沒變快（還多了 hop 延遲），算力利用率 25%。解法是 micro-batching：把 batch 切成多個 micro-batch 塞滿 pipeline，讓 4 個 stage 同時各算不同 micro-batch。訓練世界對 bubble 比例有經典公式（(S−1)/(B+S−1)，S 是 stage 數、B 是 micro-batch 數）；推論世界的好消息是 **continuous batching（ch06）天然就是 micro-batch 流**——穩態下永遠有不同請求的 token 在不同 stage 裡跑，bubble 幾乎被填滿。壞消息是兩個：

1. **延遲不降反升**：每 token 還是要序列地跑完所有層，外加 S−1 次跨 stage 傳輸延遲。PP 是吞吐型切法，對 ITL 無解。
2. **stage 不均 = 整條變慢**：吞吐由最慢 stage 決定。層數除不盡、首尾 stage 多扛 embedding/lm_head、某 stage 的卡被降頻——任何不均都直接打折。你調 SQS pipeline 時平衡各 stage consumer 數的功夫，這裡叫 stage 切分調優。

### 適用判斷

- **用**：模型跨節點才裝得下，而且互連只有一般網路或 IB（沒有跨節點 NVLink）；或者一堆沒有 NVLink 的 PCIe 卡要湊大模型（消費卡叢集、雲上廉價機型）。
- **不用**：單節點裝得下時，TP 幾乎總是更好（延遲更低、實作更成熟）。
- **組合**：大模型的標準配方是「節點內 TP × 節點間 PP」：`--tensor-parallel-size 8 --pipeline-parallel-size 2` = 2 節點 16 卡。TP 吃 NVLink 的頻寬，PP 吃 IB 的容忍度，各取所長。

## Data Parallelism：最樸素也最常用

DP（data parallelism）= 完整複製模型 N 份，各自服務不同請求。推論的 DP 比訓練簡單到幾乎無聊：**沒有 gradient 要同步，副本之間零通訊**。通訊代價公式：0。這是它最大的美德——故障隔離乾淨（一個副本死了，LB 摘掉它就好）、擴縮容是線性的、不需要任何特殊互連。

但有兩個層次要分清楚：

- **平台層 DP**：K8s 裡的 replica，gateway/LB 分流（ch12）。每個副本是獨立的 vLLM process，互不知道彼此。99% 的 scale-out 是這種，你已經會了。唯一的新問題是「每副本的 prefix cache 獨立 → 路由決定命中率」，ch10 處理。
- **引擎層 DP**（vLLM 的 `--data-parallel-size`）：多個 engine 副本被**協調地**一起跑，通常是為了跟 EP 配合——這就是 **DP attention + EP MoE** 的組合，MoE serving 的主旋律：

attention 層為什麼用 DP 而不是 TP？前面埋的伏筆收回來：MLA 模型的 KV 是單一 latent 向量，TP 切不動、只能整份複製——8 卡 TP 就是 8 份重複的 KV，HBM 直接浪費。改成 DP：每張卡跑**不同請求**的 attention（各自持有自己請求的完整 KV，不重複），到了 FFN/MoE 層再切換成 EP 把 token 分發給散在各卡的 expert。attention 權重在 MLA 架構下很小（壓縮投影矩陣），複製 N 份的代價可忽略。vLLM 與 SGLang 都已把這套組合做成一級功能（2026-06，vLLM 文件稱 DP attention 可再與 TP 組合，每個 DP engine 內含 TP-size 個 worker）。

## Expert Parallelism：MoE 專屬的切法

### 機制：all-to-all 的世界

EP（expert parallelism）只對 MoE 模型有意義（結構見 ch03）。把每層的 E 個 expert 攤到 N 張卡上（每卡 E/N 個），router 決定每個 token 去哪些 expert，於是每個 MoE 層要做兩次 **all-to-all**：

1. **dispatch**：每張卡把自己這批 token 的 hidden state 發給「持有目標 expert 的卡」；
2. **combine**：算完把結果發回原卡加權合併。

通訊量上界（假設目標 expert 全在遠端）：

```
每 token 每 MoE 層 ≈ 2 次 all-to-all × top_k × h × b

DeepSeek-V3 級（h=7168、top_k=8、58 個 MoE 層、dispatch FP8/combine BF16）：
  每 token ≈ 58 × 8 × 7168 × (1+2) bytes ≈ 10 MB
```

每 token 10 MB 的網路流量——比 dense TP 的 2.5 MB 還高,而且天生跨節點（expert 多到單節點裝不下）。這就是為什麼 DeepSeek 要自己寫 DeepEP 這種貼著 NVLink/RDMA 的 all-to-all kernel、為什麼 wide-EP 部署都要求 IB/RoCE 等級的 scale-out 網路,也是為什麼 all-to-all 與計算的 overlap（DeepSeek 的 dual-batch overlap、vLLM 的 DBO）是這個領域的核心工程。

### Wide-EP：為什麼 EP 度要開到上百

直覺上 EP 開到「expert 裝得下」就夠了,為什麼 DeepSeek 生產系統的 decode 要開到 EP144？因為 wide-EP 同時解三個問題：

1. **容量**：V3 級模型 FP8 權重 671 GB,加上 KV 與 buffer,本來就要幾十張卡。
2. **KV 池**：EP 越寬,每卡攤的 expert 權重越少,省下的 HBM 全變成 KV 池 → batch 開得更大 → decode 吞吐直接受益（ch06 的邏輯）。
3. **expert 的 batch 效率**：每卡 expert 少而流量大,每個 expert 每步收到的 token 多 → 權重讀取被攤提得更好（roofline 右移,ch02）。

公開的一手資料是 DeepSeek 自己的生產部署（2025-02 公開,H800 叢集）：**prefill 群用 EP32**（4 節點 × 8 卡為一個部署單位,每卡 9 個 routed expert + 1 個 shared expert）,**decode 群用 EP144**（18 節點 × 8 卡,每卡 2 個 routed expert + 1 個 shared expert）,公布的量測是每 H800 節點 prefill 73.7k tok/s（含 cache 命中）、decode 14.8k tok/s。注意那個關鍵設計:**prefill 與 decode 的 EP 度不一樣**——兩階段的資源畫像不同（ch03）,連平行配置都該不同,這正是 P/D 分離的核心論據之一,完整展開在 ch10。

開源引擎的支援現況（2026-06）:vLLM 的 wide-EP 已是官方支持的部署形態,`--enable-expert-parallel` 配合 DP attention,官方 blog 展示 DeepSeek 在多節點 H200 上達 2.2k tok/s/GPU（DeepEP kernel + dual-batch overlap）,並在 GB200 NVL72 上持續推進;SGLang 同樣把大規模 EP 當主打,v0.5.10 起有 Elastic EP（EP 群的彈性擴縮）。兩家在這條路線上功能高度趨同,llm-d 與 Dynamo 則在其上提供多節點編排（ch10/ch12）。

### EP 的故障面：熱 expert 與慢卡

EP 是按 token 內容路由的——這意味著負載分布**由流量內容決定**,你無法事先保證均勻。某個領域的請求湧入（全是程式碼、全是中文）,router 就是會把流量集中打到少數 expert,持有者成為全組瓶頸:all-to-all 是同步集合操作,**最慢的卡決定整步的時間**。緩解手段:redundant experts（熱 expert 多放幾份副本,DeepSeek 生產配置裡那「32 個冗餘 routed expert」就是這個）、EPLB（expert 負載均衡器,根據統計週期性重排 expert 放置,vLLM 已內建支援,2026-06）。把它想成你處理熱分區的工具箱:加副本、重新分 key、監控 skew——概念一一對應。

## Sequence Parallelism：超長 context 的切法（一節帶過）

SP/CP（sequence/context parallelism）切的不是模型,是**序列本身**:1M token 的 prefill,單卡算 O(n²) 的 attention 要算到天荒地老,於是把序列切成 N 段、N 張卡各算一段,attention 需要的跨段資訊用 ring 的方式輪轉 KV block（ring attention 是代表性做法）。通訊量級是「整份 KV 在環上轉一圈」,對超長 prefill 來說值得,對一般長度純屬浪費。

你需要知道的就三點:（1）它只解 prefill,decode 用不上;（2）它是 1M-context 時代（DeepSeek-V4、Qwen3.5 都已標配百萬級 context,2026-06）才普遍需要的武器,而 DSA/linear attention 這類架構演進正在從根上降低需求（ch17）;（3）截至我能確認的資訊（2026-06）,主流開源 serving 引擎對 SP/CP 的支援仍屬部分或實驗性質,生產上更常見的做法是 chunked prefill（ch06）＋ P/D 分離（ch10）先把長 prefill 的干擾隔離掉。知道它存在、知道什麼時候該去查它,就夠了。

## NCCL 與集合通訊：所有切法腳下的那層

上面每種切法的「通訊」,實作上幾乎都是 NCCL（NVIDIA Collective Communications Library,ch04 的名詞表提過）。它提供一組集合操作原語,幫你在「環、樹、NVSwitch、IB」這些拓撲上跑出接近線速的傳輸。把語意和代價背下來,讀任何引擎的分散式程式碼都不再陌生:

| Collective | 語意 | 每卡線上流量（ring,結果大小 S） | 推論中誰在用 |
|---|---|---|---|
| **all-reduce** | 大家各有一份,最後人人拿到總和 | 2(N−1)/N × S | TP 每層兩次（本章主角） |
| **all-gather** | 各持一片,最後人人拿到完整拼圖 | (N−1)/N × S | TP 的變體實作、權重載入 |
| **reduce-scatter** | 加總後每人只拿自己那片 | (N−1)/N × S | all-reduce 的一半（all-reduce ≡ reduce-scatter + all-gather） |
| **all-to-all** | 人人給每個人一份不同的資料 | (N−1)/N × S | EP 的 dispatch/combine |
| **broadcast** | 一人發、人人收 | ≈ S | 權重分發、同步元資料 |

三件工程上要緊的事:

1. **NCCL 是拓撲感知的**。初始化時偵測 NVLink/PCIe/IB 拓撲,自動選 ring 或 tree 演算法、決定走哪條路。`NCCL_DEBUG=INFO` 會把它看到的拓撲與選擇印出來——多卡部署起不來或慢得反常時,第一件事就是看這份輸出,確認它走的是 NVLink 而不是默默 fallback 到 PCIe 或 socket（fallback **不是錯誤,是靜默降速 10~100 倍**,這是新手最常踩的雷）。
2. **集合操作是同步屏障**。所有參與者都到齊,操作才完成。一張卡慢（降頻、ECC retry）,全組等它;一張卡死(process crash、CUDA error),全組**永遠**等它——預設行為是無限期 block 或極長的 timeout。
3. **這就是 NCCL hang 成為多卡世界最痛故障的原因**:症狀是整個 TP/EP 群的 GPU util 卡在 100%（spin-wait 也是 util）、token 輸出歸零、沒有任何 error log——對你所有「看指標找問題」的直覺都是反向欺騙。偵測、watchdog、自動處置的完整工事在 ch15,這裡先立牌子:**任何多卡部署,上線前必須先想好「NCCL hang 了我怎麼知道、誰去殺」**。

## 決策框架:模型 × 硬體 × SLO → 策略

把全章收斂成一張表。假設目標都是「生產 serving、合理 SLO」,硬體以 2026 年租用市場主流卡為基準:

| 模型 | 權重（FP8） | 推薦切法 | 為什麼 | 不要做的事 |
|---|---|---|---|---|
| **8B dense**（Llama-3.1-8B 級） | ~8 GB | **不切**。單卡（L4/A10 都夠）,流量大就平台層 DP | 權重連 24 GB 卡都裝得下,任何切法都是純開銷 | 對 8B 開 TP4「讓它更快」——通訊稅吃掉大半收益,不如把錢花在更大 batch 或更好的卡 |
| **70B dense**（Llama-3.3-70B 級） | ~71 GB | **TP2（H100/H200）或 TP4（中階卡）,單節點內**;流量大套 DP 副本 | 單卡裝不下（硬約束）;TP 同時擴 KV 池、降 ITL;8 個 KV head 整除友善 | 跨節點 TP;TP16（KV head 不夠分,KV 開始複製） |
| **405B dense**（Llama-3.1-405B 級） | ~405 GB | **TP8（單節點 8×H100/H200）**,KV 池 ≈ 640×0.9 − 405 ≈ 170 GB;若只有 PCIe 機或要更大 KV 池 → TP8 × PP2 跨兩節點 | 405 GB 剛好塞進一個 NVLink 域;PP 的 16 KiB/token 跨節點無痛 | 跨節點 TP16(IB 上 160 次/token 的 all-reduce 會讓 ITL 爆炸) |
| **1T 級 MoE**（DeepSeek-V4-Pro 1.6T/49B active、Kimi K2.6 1T/32B active 級） | 600 GB~1.6 TB | **DP attention + wide-EP**,數十到上百卡;prefill 群與 decode 群分開、EP 度不同(P/D 分離,ch10);NVL72 或多節點 IB | MLA 讓 TP 複製 KV(不可行);expert 結構天然適合 EP;wide-EP 把 HBM 還給 KV 池 | 用 TP/PP 硬扛 MoE(浪費 sparse 結構);**流量撐不滿幾十張卡就別自建——直接用 API,這是 ch16 的成本數學,不是技術問題** |

兩條貫穿的原則:**切法跟著互連走**(NVLink 域內 TP/EP、跨節點 PP/DP/EP-over-IB,斷層線就是架構線,ch02);**先過記憶體帳,再優化延遲,最後才堆吞吐**——順序反了就會出現「跑得起來但 KV 池只剩 5 GB」這種自己挖的坑。

## Worked example:70B FP8,2×H100 TP2 vs 4×L40S TP4

兩個配置服務同一個模型(Llama-3.3-70B,FP8 權重 ≈ 71 GB,KV 用 BF16),哪個划算?這題的價值在於它逼你把本章所有公式串起來算一遍。先列規格(2026-06 查證):

| | H100 SXM | L40S |
|---|---|---|
| HBM/VRAM | 80 GB HBM3 | 48 GB GDDR6 |
| 記憶體頻寬 | 3,350 GB/s | 864 GB/s |
| FP8 dense 算力 | 1,979 TFLOPS | 733 TFLOPS |
| 卡間互連 | NVLink 4:450 GB/s 每方向 | **無 NVLink**:PCIe Gen4 x16,~32 GB/s 每方向(實效抓 ~25) |
| 租價快照(2026-06,neocloud on-demand,僅供量級) | ~$2.5/hr | ~$0.8/hr |

**第 1 步:記憶體帳。**

```
2×H100 TP2:
  可用 = 80 × 0.9 × 2 = 144 GB
  權重 = 71 GB(每卡 35.5 GB)
  activation + NCCL buffer ≈ 4 GB
  KV 池 ≈ 144 − 71 − 4 ≈ 69 GB        ← 與 ch03 的數字一致

4×L40S TP4:
  可用 = 48 × 0.9 × 4 = 172.8 GB
  權重 = 71 GB(每卡 17.75 GB)
  activation + NCCL buffer ≈ 6 GB
  KV 池 ≈ 172.8 − 71 − 6 ≈ 96 GB
```

第一個反直覺:**L40S 配置的 KV 池反而大 39%**(192 GB 總容量 vs 160 GB)。以 4k context 的對話算(KV ≈ 0.33 MB × 4096 ≈ 1.35 GB/條,ch03):H100 配置容納 ~51 條,L40S 配置 ~71 條。便宜卡用「堆容量」扳回一城——先別下結論,看完速度帳再說。

**第 2 步:每 token 的 TP 通訊量。**

```
TP2(H100):80 層 × 2 次 × 2(2−1)/2 × 16 KiB = 2.5 MB/token/卡
TP4(L40S):80 層 × 2 次 × 2(4−1)/4 × 16 KiB = 3.75 MB/token/卡
```

頻寬項:H100 走 NVLink,2.5 MB ÷ 450 GB/s ≈ 6 μs,可忽略;L40S 走 PCIe,3.75 MB ÷ 25 GB/s ≈ 150 μs。α 項(160 次集合操作的啟動延遲):NVLink 上抓 ~4 μs/次 ≈ 0.6 ms;PCIe 上抓 ~25 μs/次 ≈ 4 ms。**L40S 的每 token 通訊稅 ≈ 4.2 ms,是 H100 的 7 倍**,而且大頭是 α——這就是「TP 不出 NVLink 域」鐵律的小尺度版本:TP4-over-PCIe 已經是在鐵律邊緣行走。

**第 3 步:單請求 decode 速度(batch=1 上限)。**

每個 decode step = 讀自己那份權重 shard + 通訊:

```
H100 TP2:35.5 GB ÷ 3,350 GB/s ≈ 10.6 ms,+0.6 ms 通訊 ≈ 11.2 ms → ~89 tok/s
L40S TP4:17.75 GB ÷ 864 GB/s ≈ 20.5 ms,+4.2 ms 通訊 ≈ 24.7 ms → ~40 tok/s
```

(roofline 式上限,實測通常打 7~8 折。)H100 配置的單流速度是 2.2 倍——對 ITL 敏感的互動式產品,這就是分界線。

**第 4 步:TTFT(4k token prompt 的 prefill)。**

prefill 是 compute-bound(ch03),FLOPs ≈ 2 × 70.6B × 4096 ≈ 578 TFLOPs(忽略 attention 二次項,4k 下約再加 7%):

```
H100 TP2:578 ÷ (1,979 × 2 × 0.45 MFU) ≈ 0.32 s
  通訊:每次 all-reduce payload = 4096 × 16 KiB = 64 MiB
       160 次 × 64 MiB × 1.0 ÷ 450 GB/s ≈ 0.02 s        → TTFT ≈ 0.35 s
L40S TP4:578 ÷ (733 × 4 × 0.45 MFU) ≈ 0.44 s
  通訊:160 次 × 64 MiB × 1.5 ÷ 25 GB/s ≈ 0.61 s         → TTFT ≈ 1.05 s
```

第二個殺手鐧藏在這裡:**L40S 配置的 prefill 花在 all-reduce 上的時間(0.61 s)比花在計算上的(0.44 s)還多**。prefill 的 payload 是 MB 級,通訊從 α 主宰變成頻寬主宰,PCIe 的 25 GB/s 直接現形。4 張卡的聚合算力(2,932 TFLOPS)比 2×H100(3,958)只差 26%,但 TTFT 差 3 倍——瓶頸根本不在算力。

**第 5 步:飽和吞吐(decode,全 KV 池跑滿 4k context 對話)。**

```
H100 TP2:51 條並發
  每步每卡讀:權重 35.5 + KV shard 34.5 ≈ 70 GB → 20.9 ms
  通訊(payload ×51,仍是小包+α) ≈ 0.9 ms → 每步 ≈ 21.8 ms
  吞吐 ≈ 51 ÷ 0.0218 ≈ 2,340 tok/s

4×L40S TP4:71 條並發
  每步每卡讀:權重 17.75 + KV shard 24 ≈ 41.75 GB → 48.3 ms
  通訊:payload = 71 × 16 KiB ≈ 1.1 MB/次,160 次 × 1.5 ÷ 25 GB/s ≈ 10.9 ms,+α 4 ms → 每步 ≈ 63 ms
  吞吐 ≈ 71 ÷ 0.063 ≈ 1,130 tok/s
```

**第 6 步:成本對比。**

| | 2×H100 TP2 | 4×L40S TP4 |
|---|---|---|
| 機時(2026-06 快照) | ~$5.0/hr | ~$3.2/hr |
| 單流 decode 上限 | ~89 tok/s | ~40 tok/s |
| TTFT(4k prompt) | ~0.35 s | ~1.05 s |
| 飽和 decode 吞吐上限 | ~2,340 tok/s | ~1,130 tok/s |
| 併發容量(4k 對話) | ~51 條 | ~71 條 |
| **$/M output token(飽和)** | **~$0.59** | **~$0.79** |

結論與它的邊界:這組價格快照下,**H100 配置全面勝出**——不只快,連每 token 成本都低 25%,因為 L40S 省下的租金被 PCIe 通訊稅與低頻寬吃光了。但注意三件事:(1)結論對價格敏感——L40S 在 marketplace 上低到 ~$0.5/hr 時(2026-06 的 Vast.ai 確實有),$/Mtok 會翻盤到 ~$0.49,**這張表你必須用當下的價格自己重算**,這正是 ch16 成本模型的日常;(2)上面全是 roofline 式上限,主軸二提醒你:租 2 張卡實測一次(本章 Lab 2),用數據驗證推算;(3)如果 SLO 對 TTFT/ITL 有硬要求,L40S 配置可能直接不及格——goodput 為零的便宜是最貴的便宜(ch06/ch14)。

## 故障模式與防禦

多卡把單機的故障面乘上 N,再加上「同步集合操作」這個新的單點。Murphy 巡禮:

| 故障 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| **NCCL hang**(一卡 crash/OOM,全組僵在 collective) | 整組 GPU util 100% 但 token 輸出歸零;沒有 error log;請求全部 timeout | util 高但 throughput 為零的背離(兩個指標都要收,ch14);NCCL watchdog timeout log | 設 NCCL timeout 而非無限等;深健康探針(真的生成 token 才算活,ch15);全組視為單一故障域、一起重啟 |
| **靜默 fallback 到慢路徑**(P2P 被 ACS/IOMMU 擋掉、NCCL 走了 socket) | 功能完全正常,效能差 10~100 倍;最陰險的一類 | `NCCL_DEBUG=INFO` 看實際選用的傳輸;對照本章公式算的理論值——差太多就是有事 | 部署前固定跑一次 `nccl-tests`(all_reduce_perf)留 baseline;機型/驅動變更後重跑 |
| **TP 度與模型形狀不整除** | 啟動直接報錯(好的情況);或 KV head 被複製、容量莫名比試算少(壞的情況) | 啟動 log 的 KV block 數 vs 你的紙上計算 | 切之前查 config.json:head 數、KV head 數、vocab 能否被 N 整除 |
| **慢卡拖累全組**(thermal throttle、ECC retry、壞風扇) | 整個 TP/EP 組的 step time 變長,但每張卡單看都「正常」 | DCGM 的逐卡溫度/時脈/ECC 計數;組內 per-rank 耗時分布 | 拓撲感知排程避開降級節點(ch11);DCGM 驅動的自動 cordon(ch15) |
| **EP 熱 expert** | 部分 GPU 飽和、其他閒置;吞吐遠低於卡數應有水準;特定流量內容觸發 | per-GPU 的 expert 負載分布指標;all-to-all 等待時間 | redundant experts;EPLB 週期性重平衡;容量規劃時別假設均勻分布 |
| **NVLink/IB 鏈路退化**(Xid 74、線纜故障) | 通訊耗時抖動、偶發 NCCL error;單卡指標無異常 | DCGM NVLink 錯誤計數器;IB port counter | 納入節點健康檢查;故障處置見 ch15 |
| **gpu-memory-utilization 設太滿 + TP buffer 低估** | 啟動成功,CUDA graph capture 或尖峰時 OOM | 啟動後的實際 HBM 餘量 | 多卡時 NCCL buffer/graph 各吃一份,留 5~10% 餘裕;用本章記憶體帳預算,不要試錯 |
| **PP stage 失衡** | 吞吐低於預期,某 stage 的卡 util 明顯高於其他 | per-stage util 與佇列深度 | 重切 stage(首尾 stage 記得算上 embedding/lm_head 的帳) |

共同主題:多卡故障的觀測難點在於**指標會說謊**(util 100% 可能是 spin-wait、單卡全綠但全組變慢),防禦的根基是「先有理論值,再比對實測」——本章的公式就是你的理論值產生器。

## 動手做

### Lab 1 [紙上推演]:為 405B 與 1T 級 MoE 各設計一套平行配置

**任務 A**:Llama-3.1-405B(126 層、hidden 16384、128 Q head/8 KV head、head_dim 128),FP8 權重 ≈ 405 GB。在(a)8×H100 節點(b)2× 8×H100 節點兩種硬體上各設計一套切法,算出:每卡權重 shard、KV 池總量、每 token 的 KV bytes(套 ch03 公式:2×126×8×128×2 ≈ 0.49 MB/token BF16)、能服務幾條 32k 對話、每 token 每卡的 TP 通訊量。

**任務 B**:DeepSeek-V3 級 MoE(671B total/37B active、61 層、MLA)。先回答:為什麼 TP 在這裡是錯的答案?(提示:MLA 的 KV 在 TP 下會發生什麼。)然後設計一個 DP attention + EP 的配置:16×H200(141 GB),算每卡攤幾個 expert、權重 shard、剩多少 KV 池。

**成功標準**:任務 A 中你能解釋為什麼(b)應該是 TP8×PP2 而不是 TP16;任務 B 中你能說出 wide-EP 的三個動機(容量/KV 池/expert batch 效率)並對上自己算的數字。

### Lab 2 [租 GPU]:TP2 實測 vs 單卡(估 $8–15)

1. 在 RunPod/Lambda 租 2×A100 80GB 或 2×H100(同節點、確認有 NVLink:`nvidia-smi topo -m` 看到 `NV#` 而不是 `PHB/PIX`)。
2. 跑一個單卡裝得下的模型做對照,例如 Llama-3.1-8B 或 FP8 的 32B 級模型(示意):

```bash
# 單卡 baseline
vllm serve RedHatAI/Qwen2.5-32B-Instruct-FP8-dynamic --max-model-len 8192

# TP2
vllm serve RedHatAI/Qwen2.5-32B-Instruct-FP8-dynamic --max-model-len 8192 \
  --tensor-parallel-size 2
```

3. 兩種配置各跑 `vllm bench serve`(固定 workload:input 1k/output 256、並發 1 與 32 兩檔),記錄 TTFT/ITL/throughput。
4. 收尾必做:`NCCL_DEBUG=INFO` 重啟一次,在 log 裡找出 NCCL 選用的拓撲與傳輸;對照本章公式估算 TP2 的每 token 通訊量。**用完即關機。**

**成功標準**:能回答「TP2 的 ITL 改善了多少?為什麼不是理想的 2 倍?」(答案藏在 α 稅與非權重讀取時間裡);並發 32 時 TP2 的吞吐增益與 batch=1 時有何不同、為什麼。

### Lab 3 [紙上推演]:通訊預算速算

對你在 Lab 2 用的模型,算出 TP2/TP4/TP8 在(a)NVLink 4(b)PCIe Gen5(c)IB NDR 三種互連上,decode 每 token 的通訊耗時(α 抓 NVLink 4 μs、PCIe 25 μs、IB 20 μs/次),做成 3×3 表。**成功標準**:表裡能明確圈出哪些格子是「可用」、哪些是「ITL 殺手」,並用它解釋「TP 不出節點」鐵律。

## 這個領域往哪走

短期(1–2 年)的三條線:**NVLink 域持續擴張**——NVL72 已把「TP/EP 的舒適圈」從 8 卡撐到 72 卡,Rubin 世代(H2 2026 起上雲)繼續沿這條線走,「域內 vs 域外」的斷層線不會消失,只會搬家;**wide-EP 從尖端變成商品**——vLLM/SGLang 都已把 DP attention + EP + P/D 做成官方路徑,llm-d/Dynamo 在上面鋪編排層,2027 年「部署 1T MoE」大概率是填配置而不是寫程式;**平行配置的決策自動化**——Dynamo 的 planner/AIConfigurator 這類「給定模型與 SLO,搜出平行配置」的工具正在成熟,但工具給的答案你得會驗算——本章的公式就是驗算器,這是十年不過期的那部分。

## 自我檢核

1. TP 把 Llama-3.3-70B 的一層切到 4 張卡上:哪些矩陣 column-parallel、哪些 row-parallel、all-reduce 發生在哪兩個位置?每 token 每卡的通訊量是多少 bytes(寫出公式並代入)?
2. 為什麼 TP 幾乎不跨節點,而 PP 可以?用 NVLink 4 與 IB NDR 的每方向頻寬數字、以及兩種切法的每 token 通訊量(2.5 MB vs 16 KiB)完整論證。
3. decode 與 prefill 的 all-reduce 各被 α 項還是頻寬項主宰?為什麼?這對「用 PCIe 卡做 TP」分別意味著什麼?
4. MLA 模型為什麼用 DP attention 而不是 TP attention?MoE 的 FFN 為什麼用 EP 而不是 TP?
5. DeepSeek 生產系統的 prefill 用 EP32、decode 用 EP144——為什麼兩階段的 EP 度不同?wide-EP 對 decode 吞吐的三重收益是什麼?
6. 同樣 8 張 H100,什麼情況選 TP8 單副本、什麼情況選 TP2×4 副本?各犧牲了什麼?
7. 你的 TP4 部署吞吐只有理論值的 1/20,但沒有任何 error log。列出前三個假設與各自的驗證手段。
8. 405B FP8 要部署在 16×H100(2 節點)上:寫出你的切法、每卡權重 shard、KV 池,並說明為什麼不是 TP16。

## 延伸閱讀

- Shoeybi et al., *Megatron-LM: Training Multi-Billion Parameter Language Models Using Model Parallelism*(2019)— https://arxiv.org/abs/1909.08053 。TP 的 column/row-parallel 切法與「每層兩次 all-reduce」的原典,推論世界沿用至今。
- NVIDIA NCCL User Guide:Collective Operations — https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html 。五種集合操作的官方語意定義,讀完本章再讀它,每個圖都看得懂。
- DeepSeek, *DeepSeek-V3/R1 Inference System Overview*(Open Source Week Day 6,2025-02)— https://github.com/deepseek-ai/open-infra-index/blob/main/202502OpenSourceWeek/day_6_one_more_thing_deepseekV3R1_inference_system_overview.md 。EP32 prefill/EP144 decode 生產部署的一手資料,本章 wide-EP 數字的出處。
- vLLM Blog, *vLLM Large Scale Serving: DeepSeek @ 2.2k tok/s/H200 with Wide-EP*(2025-12-17)— https://blog.vllm.ai/2025/12/17/large-scale-serving.html 。開源引擎 wide-EP 的現況基準:DeepEP、dual-batch overlap、多節點實測。
- vLLM Docs:Expert Parallel Deployment — https://docs.vllm.ai/en/latest/serving/expert_parallel_deployment/ 。DP attention + EP 的實際參數與部署形態,Lab 之外想動手跑 MoE 的起點。
- Red Hat Developer, *Scaling DeepSeek-style MoEs with vLLM and llm-d using Wide EP*(2025-09)— https://developers.redhat.com/articles/2025/09/08/scaling-deepseek-style-moes-vllm-and-llm-d-using-wide-ep 。wide-EP 的多節點編排視角,銜接 ch10/ch12。
- deepseek-ai/DeepEP — https://github.com/deepseek-ai/DeepEP 。EP all-to-all 的專用通訊庫,README 就是一堂「NVLink/RDMA 上的 all-to-all 工程」課。
- Hugging Face, *The Ultra-Scale Playbook* — https://huggingface.co/spaces/nanotron/ultrascale-playbook 。訓練視角的平行化互動教材(超出本書範圍),但 TP/PP 的視覺化是我見過最好的,看圖建直覺很值。
