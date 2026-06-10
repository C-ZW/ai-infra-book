# ch10 — 解構推論服務：P/D 分離與 KV 路由

> **本章解決什麼問題**：ch03 證明了 prefill 是 compute-bound、decode 是 memory-bound；ch06 給了單機緩解（chunked prefill），並誠實承認它是緩解不是根治；ch09 教你把一個模型切到多張卡上。本章走到 2025–2026 大規模推論架構的主旋律：把 prefill 與 decode 拆到**不同的 GPU 池**，讓各自用最適合的硬體與平行策略跑，再用一個懂 KV cache 的路由層把流量送對地方。這也是「LLM serving 是有狀態的分散式系統」這個論點最尖銳的一章——KV cache 在哪裡，決定了請求該去哪裡。讀完你要能算出 KV 傳輸帳、能設計 xPyD 配比、能比較三家路由器的 scoring 設計，以及——同樣重要——能判斷什麼規模以下根本不該碰這套東西。

## 從你已知的出發

這一章的每個概念，你都在後端世界處理過它的同構物，只是物理常數變了。

**讀寫分離。** 你做過 RDS read replica：寫入流量與讀取流量的資源畫像不同（鎖、IO 模式、快取行為），所以拆開、各自擴縮、中間用 replication 同步狀態。P/D 分離是同一個決策模板：prefill 像「寫」（一次大量計算、產生狀態），decode 像「讀」（反覆消費狀態、頻寬敏感），兩者塞在同一台機器上互相踩踏，於是拆開。差別在於同步的「狀態」不是 binlog，是以 GB 計的 KV cache，而且必須在毫秒級搬完。

**Session affinity。** 你做過 WebSocket 多裝置同步：連線有狀態，所以 LB 要 sticky——同一個使用者盡量回到同一台，否則狀態要從 Redis 重建。KV-aware routing 是 session affinity 的高賭注版本：「狀態」是某個 replica 的 prefix cache（ch05），命中與未命中的差距不是「多查一次 Redis 的 2ms」，而是「重算 30 秒對話歷史的 prefill」對「直接開始生成」——TTFT 差 10 倍以上。黏性的價值高了兩個數量級，所以路由器值得為它做複雜得多的決策。

**Consistent hashing。** 你知道 Redis Cluster 怎麼用 hash slot 把 key 釘到節點。你的第一直覺可能是：把 prompt prefix hash 一下，consistent hashing 送到固定 replica，不就解了？這個直覺方向對、但工具錯——本章會講為什麼 prefix 不是一個可以 hash 的 opaque key（它是階層式的、多請求共享的、而且命中價值與負載均衡互相拉扯），以及業界實際收斂到的解法：**scoring，不是 hashing**。

**慢端點獨立 worker pool。** 你在 API gateway（KrakenD）做過：把慢的上游隔離到獨立連線池，免得拖垮快的。P/D 分離在叢集層面做同一件事——prefill 就是那個「慢而吃 CPU」的端點，decode 是「快而頻繁」的端點，單機混跑的干擾（ch06 算過：一個 8k prompt 讓所有人的 ITL 從 9ms 跳到 190ms+）在叢集層面用物理隔離根治。

帶著這四個錨點，新東西只有兩個：搬 KV 的物理（一筆帳，本章算給你看），和 scoring 函數的設計空間（三家的真實做法，逐一拆解）。

## 動機：干擾是結構性的，單機緩解有天花板

先把問題釘死。ch03 的結論：prefill 的 arithmetic intensity 高（一次吃進整個 prompt 的矩陣乘法），落在 roofline 的 compute-bound 一側；decode 每步只算一個 token，權重與 KV 全部重讀一遍，是深度 memory-bound。同一張 GPU 上，這兩種 workload 要的東西不一樣：prefill 要算力，decode 要頻寬與記憶體容量。

ch06 的 chunked prefill 把 prefill 切塊混進 decode batch，把「ITL 尖刺」磨平成「ITL 整體墊高一截」。但它有兩個結構性天花板：

1. **Token budget 守恆**。每一步的計算預算就那麼多，分給 prefill chunk 的每一分都在墊高 decode 的步長。prefill 吞吐與 ITL 平滑度在單機上是零和的——你只能選擇痛的形狀，不能消除痛。
2. **兩階段的最佳平行策略不同**。prefill 希望大 TP 度把單一 prompt 的延遲壓低、甚至上 SP（ch09）；decode 希望省通訊、大 batch、把 HBM 留給 KV。單機混跑時你只能選一套配置，必然對某一邊次優。

DistServe（OSDI 2024）把這個干擾量化得很徹底：在同時有 TTFT 與 TPOT（每 token 時間）雙重 SLO 的設定下，把 prefill 與 decode 拆到不同 GPU、各自選平行策略，相同硬體能多服務 **7.4 倍**請求、或把 SLO 收緊 **12.6 倍**（論文數字，下詳）。干擾不是調參問題，是資源畫像衝突的結構問題——這就是 P/D 分離（prefill/decode disaggregation）存在的理由。

值得停一秒的反直覺點：P/D 分離的收益**不是更高的總 FLOPs 利用率**——多了一次 KV 搬運，總工作量其實變多了。收益是 **goodput**：在 TTFT 與 ITL 都要達標的前提下，每張卡能扛的有效請求數。如果你只有單一寬鬆 SLO（例如內部批次任務只看吞吐），P/D 分離對你幾乎沒有價值。把這句話記住，本章結尾的「什麼時候不要用」會回收它。

## 從論文到生產：四條譜系

學術源頭一段帶過。**DistServe**（北大/UCSD，OSDI 2024）證明了 goodput 視角下分離的數學收益，並指出 KV 傳輸開銷「在現代 GPU 叢集中不足掛齒」——注意這句話的前提是有 NVLink/IB 等級的互連，本章的 worked example 會檢驗它。**Splitwise**（Microsoft，ISCA 2024 最佳論文）用 Azure 生產 trace 做了同樣論證，並率先提出**異質硬體**思路：兩階段用不同的卡，同成本同功耗下吞吐 2.35 倍、或 1.4 倍吞吐省 20% 成本（論文數字）。這兩篇 2024 年的論文，到 2025–2026 已經長成四條生產譜系：

| 系統 | 出身 | 一句話定位（2026-06） |
|---|---|---|
| **Mooncake** | Moonshot AI（Kimi） | KVCache-centric：整個架構圍繞「KV 在哪」設計，P/D 分離只是其中一環；最大規模的公開生產證據 |
| **NVIDIA Dynamo** | NVIDIA（v1.2.0，2026-06） | 引擎無關的分散式推論框架：KV router + planner + KVBM + NIXL，vLLM/SGLang/TRT-LLM 都能掛 |
| **llm-d** | Red Hat/Google/IBM 系（v0.6.0） | K8s 原生、建立在 Gateway API Inference Extension 上的「well-lit paths」——文件化、可複製的生產路徑 |
| **vLLM KV connector 生態** | vLLM 社群 | 引擎內的抽象層：NixlConnector、LMCacheConnector、MooncakeConnector…讓上面三家（與你自組的方案）都有同一個掛載點 |

逐一拆它們各自押注的洞察。

### Mooncake：把 KV cache 當成排程的第一公民

Mooncake（論文 arXiv:2407.00079，FAST'25）是 Kimi 的 serving 平台，它的核心立場寫在論文副標題裡：*Trading More Storage for Less Computation*。架構上三個重點：

- **分離的 prefill 池與 decode 池**，加上一個用 GPU 叢集裡閒置 CPU/DRAM/SSD 組成的**分散式 KV cache 池**（儲存層的部分 ch05 講過，這裡看排程面）。
- **Conductor（全域排程器）**：每個請求進來，排程器同時決定「哪個 prefill 實例算它」與「哪個 decode 實例接它」，決策依據是 KV 的位置——哪裡有它的 prefix cache、搬到哪裡最便宜。目標函數是在 TTFT 與 TBT（time between tokens，等同本書的 ITL）雙 SLO 下最大化 goodput。
- **Transfer Engine**：不用 NCCL 而是自製的 RDMA 傳輸層，支援拓撲感知路徑選擇與**多卡 NIC 頻寬聚合**；KV 採 **layer-wise 串流**——prefill 算完第一層就開始搬第一層的 KV，傳輸與計算重疊，等 prefill 全部算完時大部分 KV 已經在路上。這個 overlap 是讓「搬 KV」在延遲帳上近乎免費的關鍵工程。

生產數據（專案方自報，2026-06）：真實負載下讓 Kimi 多承接 75% 請求；Kimi K2（1T 參數 MoE）部署在 128×H200 上，以 P/D 分離 + 大規模 EP 跑出 prefill 224k tok/s、decode 288k tok/s。這是目前公開資訊裡規模最大、數據最完整的 P/D 分離生產案例。

### NVIDIA Dynamo：引擎無關的框架層

Dynamo 把 P/D 分離做成框架（v1.2.0，2026-06）：**KV router** 做 KV-aware 路由（scoring 設計下節詳拆）；**Planner** 負責 P 池與 D 池的容量規劃與動態擴縮，整合 AIConfigurator 做吞吐建模；**KVBM** 是引擎無關的 KV 分層管理；最底層的 **NIXL**（NVIDIA Inference Xfer Library）統一 UCX/GPUDirect Storage/S3 等傳輸後端——它已經成為事實上的跨節點 KV 搬運共同地基：vLLM 的 NixlConnector、Ray Serve 的 P/D pattern、Dynamo 自己都踩在它上面。

### llm-d：K8s 原生的 well-lit paths

llm-d（v0.6.0，2026-04）的差異化不在機制而在**形態**：它把 P/D 分離與智慧路由做成 Kubernetes 上文件化、經 benchmark 驗證的部署路徑（well-lit paths），路由層直接用 Gateway API Inference Extension 的 InferencePool/EPP 標準（平台層全貌見 ch12）。官方數字（專案方自報）：Path 1（prefix-cache-aware routing）在 8 pods/16×H100 下 TTFT 比 round-robin 快 57 倍；Path 2（P/D 分離）在 16×16 B200 拓撲達 50k output tok/s。AWS 已基於 llm-d 推出官方的 disaggregated inference 方案，KServe 的 LLMInferenceService 也直接建構其上（2026-06）。

值得注意的是 llm-d 文件對 P/D 分離的定位非常克制：預設路徑是 **colocated（混跑）+ 智慧路由**，P/D 分離被標為「長輸入、大模型、TTFT 被 prefill 支配」場景的進階選項。一個力推此技術的專案自己都這樣寫，本章結尾的判斷準則跟它一致。

## KV 傳輸工程：搬 10 GB 的狀態是什麼概念

P/D 分離的全部代價濃縮在一件事上：prefill 算完的 KV cache 必須搬到 decode 節點。先建立直覺，再算帳。

搬運的工程棧由下往上：物理層是 NVLink（同節點/同 NVLink 域）、InfiniBand/RoCE（跨節點 RDMA）、或普通乙太網 TCP（你不會想用，馬上證明）；中間是傳輸函式庫——NIXL 或 Mooncake Transfer Engine，負責挑路徑、聚合多張 NIC、GPU 記憶體直達（GPUDirect RDMA，不繞 CPU）；最上面是引擎的 KV connector，負責 block 對位（兩邊的 PagedAttention block table 要對得上）與 layer-wise 串流排程。

工程上三個關鍵事實：

1. **KV 是分片的**。TP4 的部署裡 KV 平均散在 4 張卡上，每張卡有自己的 NIC——搬運可以四路並行（Mooncake 的多卡頻寬聚合就是這件事）。
2. **搬運可以與計算重疊**。layer-wise 串流下，暴露在 TTFT 上的延遲只有最後一層的傳輸 + 收尾，遠小於總傳輸時間。但 overlap 隱藏的是延遲，不是頻寬佔用——NIC 被 KV 搬運吃掉的頻寬，EP 的 all-to-all（ch09）就用不到了。
3. **失敗要有出路**。傳輸失敗的正確 fallback 是「decode 節點自己重算 prefill」——這要求路由層把原始 prompt 一起帶過去，而不是只帶 KV 的引用。

### Worked example：32k context 的 KV 傳輸帳

題目：Llama-3.3-70B，一條 32k token 的對話要從 prefill 節點交接到 decode 節點。搬 KV 划算，還是讓 decode 節點重算一次 prefill 划算？逐步算。

**Step 1：要搬多少 bytes。** ch03 的公式與數字直接引用：Llama-3.3-70B（GQA，80 層、8 KV heads、head_dim 128、BF16）每 token KV = 2 × 80 × 8 × 128 × 2 = **320 KiB**。32k context：

```
32,768 tokens × 327,680 bytes ≈ 10.74 GB
```

10.74 GB。先停下來感受一下：這是「一個請求」的狀態交接量。你在後端搬過的最大 session 狀態大概是幾百 KB 的購物車——這裡是它的三萬倍，而且在 TTFT 預算（秒級）內要搬完。

**Step 2：三種網路各要多久。** 頻寬數字接 ch02（皆為每方向；實際有效頻寬以 80% 折算，傳輸層協定與 block 對位都有開銷）：

| 路徑 | 理論頻寬 | 理論時間 | 有效時間（×0.8） |
|---|---|---|---|
| NVLink 4（同節點/同域） | 450 GB/s | 23.9 ms | **約 30 ms** |
| IB NDR 400G × 1 NIC | 50 GB/s | 215 ms | **約 270 ms** |
| IB NDR 400G × 4 NIC（TP4 分片並行） | 200 GB/s | 54 ms | **約 67 ms** |
| 100GbE（TCP，無 RDMA） | 12.5 GB/s | 859 ms | **約 1.1 s** |

**Step 3：重算 prefill 要多久。** 部署假設：TP4 H100（BF16 權重 141 GB 需要至少 2 卡，TP4 是常見配置）。prefill 計算量兩項（ch03）：

- 線性項（權重相關）：2 × 70e9 × 32,768 ≈ **4.59 PFLOP**
- attention 項：4 × n² × d_model × n_layers（QKᵀ 與 ×V 各佔一半）= 4 × (32,768)² × 8,192 × 80 ≈ 2.81 PFLOP，causal mask 折半 ≈ **1.41 PFLOP**

合計約 **6.0 PFLOP**。TP4 H100 的有效算力：單卡 dense BF16 989 TFLOPS，長 prefill 的 MFU 取 70%（ch06 用過同一假設）≈ 700 TFLOPS/卡，四卡 2.8 PFLOPS（忽略 TP 通訊損耗，實務再打九折）：

```
6.0 PFLOP ÷ 2.8 PFLOPS ≈ 2.1 s
```

**Step 4：對比。**

| 方案 | 時間 | 佔重算的比例 |
|---|---|---|
| 重算 prefill | ~2,100 ms | 100% |
| NVLink 搬運 | ~30 ms | **1.4%** |
| IB 4-NIC 搬運 | ~67 ms | **3%** |
| IB 1-NIC 搬運 | ~270 ms | 13% |
| 100GbE 搬運 | ~1,100 ms | 52% |

**Step 5：crossover point。** 把它一般化成一條公式。搬運划算的條件是：

```
KV_bytes / BW_effective < Prefill_FLOPs / F_effective
→ BW_effective > KV_bytes × F_effective / Prefill_FLOPs
```

代入本題：BW > 10.74 GB ÷ 2.1 s ≈ **5.1 GB/s ≈ 41 Gb/s（有效）**。也可以用每 token 的視角驗算（兩邊的線性項都隨 token 數線性長，所以這個比值近乎與 context 長度無關）：每 token 搬 320 KB vs 每 token 重算 140 GFLOP ÷ 2.8 PFLOPS = 50 μs → 等效頻寬門檻 320 KB ÷ 50 μs = 6.4 GB/s，同一個量級。attention 的 O(n²) 項讓重算隨 context 變長越來越虧——context 越長，天平越偏向搬運。

**結論與三個推論：**

1. crossover 落在 **40–50 Gb/s 有效頻寬**——這不是「NVLink vs 重算」的選擇題，而是「資料中心級 RDMA 網路 vs 普通乙太網」的分界線。有 400G IB/RoCE，搬運比重算便宜 8–30 倍，DistServe 那句「開銷不足掛齒」成立；只有 100GbE，搬運只省一半，扣掉工程複雜度後接近白忙；25GbE 以下，重算直接獲勝，P/D 分離在物理上不成立。
2. **FP8 KV cache（ch05）讓天平再偏一倍**：bytes 砍半，搬運時間砍半，crossover 門檻降到 ~20 Gb/s。
3. 上表是「裸延遲」。加上 layer-wise overlap 後，暴露在 TTFT 上的搬運成本還能再壓——這就是為什麼 Mooncake/NIXL 都把串流重疊當成核心工程，而不是可有可無的優化。

順帶解釋了異質硬體的思路（Splitwise 的遺產）：prefill 是 compute-bound，用算力強、HBM 不用大的卡（甚至上一代卡——它們的 FLOPS 沒老多少）；decode 是 memory-bound + 容量飢渴，用 HBM 大、頻寬高的卡（H200 對 H100 算力相同、頻寬 +43%，是天生的 decode 卡，ch02 講過）。兩個池子用不同卡，採購自由度多一維；代價是兩種機型的維運與容量規劃（ch13）各自獨立，複雜度也多一維。

## xPyD：兩個池子的配比怎麼定

業界用 **xPyD** 記號表示拓撲：x 個 prefill 實例配 y 個 decode 實例（例如 4P2D）。配比定錯的症狀很直白：P 池排隊 → TTFT 崩；D 池排隊 → ITL 崩、或 KV 池滿觸發跨節點版 preemption storm。配比由流量形態決定，框架是各算各的需求：

- **P 池需求** = 入站 prompt token 速率 ÷ 單一 P 實例的 prefill 吞吐（compute-bound：有效 FLOPS ÷ 每 token 2×params FLOP）。注意要扣掉 prefix cache 命中的部分——命中的 token 不用算（ch05）。
- **D 池需求** = max(輸出 token 速率 ÷ 單實例 decode 吞吐，併發序列數 × 每序列 KV ÷ 單實例 KV 池容量)——decode 受吞吐與 KV 容量雙重約束，取較緊的那個。

快速 sketch 一個數字感（長文件 RAG：50 req/s、輸入 8k、輸出 500、無 cache 命中）：P 池需求 = 400k tok/s，單一 TP4-H100 實例約 20k tok/s（上例算過）→ 需要約 20 個 P 實例。D 池：穩態併發 ≈ 50 × (500 ÷ 30 tok/s) ≈ 830 條，每條 KV ≈ 8.5k × 320 KB ≈ 2.7 GB，單實例 KV 池約 160 GB → 容量約 60 條/實例 → 需要約 14 個 D 實例。配比 **約 10P:7D，重 prefill**。同樣的算法套到短問答（輸入 500/輸出 300）會得到 1P:2D 甚至「別分離了」；套到高 cache 命中的 agentic 流量（名目輸入巨大，但 90%+ 是命中的 prefix），有效 prefill 需求暴跌，又是另一個形狀。這個推演的完整版是本章 Lab 10-2。

兩個工程提醒。第一，**配比是流量形態的函數，而流量形態會漂移**——產品上線 agentic 功能的那一天，你的 xPyD 就過時了。靜態配比要嘛靠 Dynamo planner 這類元件動態調整（它做吞吐建模並獨立擴縮兩池），要嘛在 K8s 上把 P/D 做成兩個獨立的 Deployment 各自 autoscale（llm-d 的做法，訊號設計見 ch13）。第二，池子的整數性：小流量下「1.3 個 P 實例」只能進位成 2P，利用率直接打七折——這是小規模不要分離的數學原因之一，結尾再回收。

## KV-aware routing：有狀態的負載均衡

現在換到路由層。就算你不做 P/D 分離，只要有超過一個 replica，這個問題就存在:**每個 replica 的 prefix cache 內容不同，而路由決定命中率**。round-robin 是 cache 的天敵——同一個 session 的第二輪被送到另一台，那台沒有它的 KV，整段歷史重新 prefill。llm-d 那個「57 倍 TTFT」的對照組就是 round-robin（專案方自報，但方向毫無疑問）。

### 為什麼 session affinity 和 consistent hashing 都不夠

你的第一個方案會是 **session affinity**：sticky 到上次服務的 replica。它能解多輪對話，但解不了三件事：(1) 跨 session 的共享 prefix——同一個 system prompt + 工具描述被一萬個不同使用者共享（agentic 流量的常態，ch17），affinity 看不見這層共享；(2) replica 的 cache 會被 evict，黏過去不保證還在；(3) 熱 session 黏死一台，負載失衡沒有出口。

第二個方案是 **consistent hashing on prefix**：把 prompt 前 N 個 token hash 成 key，釘到固定 replica。比 affinity 進一步（共享 prefix 自動聚合），但還是錯在兩處:prefix 是**階層式**的——A 請求命中 B 請求的前半段也有價值，hash 一個定長前綴會把「部分命中」全部歸零；而且 hash 是無視負載的，熱 prefix（比如全公司共用的 RAG system prompt）會把一台 replica 打爆，其他閒置。

業界收斂的答案：**為每個候選 replica 打分，在 cache 命中價值與負載之間做顯式的權衡**。這是一個 scoring 問題，不是 hashing 問題。三家的真實設計：

### 三家路由器的 scoring 設計（2026-06）

**llm-d inference scheduler**（基於 Gateway API Inference Extension 的 EPP，v0.7.1）：插件化的 filter → score → pick 管線，每個 scorer 對候選 pod 給 0–1 分，加權求和。官方範例配置：`prefix-cache-scorer` 權重 3（這個 pod 上已快取的 prompt 前綴比例，有兩種實作:用路由歷史近似，或訂閱引擎 KV events 做精確索引）、`kv-cache-utilization-scorer` 權重 2（KV 池水位，越空越高分）、`queue-scorer` 權重 2（等待佇列深度）。v0.7.1 新增 active-request-scorer、no-hit-lru-scorer 等插件。設計哲學:把權衡暴露成可配置的權重，讓平台團隊按流量調。

**Dynamo KV router**：worker 透過 KVPublisher 廣播 KV cache 事件，router 端的 KVIndexer 維護一棵全域 radix tree（branch-sharded 並行結構）。路由用一條成本函數（官方文件，2026-06）：

```
cost = kv_overlap_score_weight × potential_prefill_blocks + potential_active_blocks
```

選 cost 最低的 worker。漂亮之處在於量綱統一:`potential_prefill_blocks` 是「去這台要重算多少 block 的 prefill」（cache 命中越多，這項越小），`potential_active_blocks` 是「這台已經背著多少 decode 工作」——兩項都以 KV block 計，本質上都是 GPU 時間。`kv_overlap_score_weight` 是唯一的旋鈕:prefill-heavy 流量調高（衝 TTFT），decode-heavy 調低（保 ITL、攤平負載）。

**SGLang router / model gateway**：Rust 實作，router 在本地維護一棵**近似 radix tree**——不訂閱事件，而是用「我把什麼路由到哪」的歷史去模擬每個 worker 的 cache 內容，lazy 更新、零同步開銷。決策是雙模式:負載失衡超過閾值（`balance-abs-threshold`、`balance-rel-threshold`）時退化成最短佇列模式；否則走 cache-aware，prefix 匹配率超過 `cache-threshold`（預設 0.3）就選匹配最高的 worker。官方數字（v0.4 blog，專案方自報）:cache hit rate 20% → 75%，吞吐 1.9 倍。

| | llm-d scheduler | Dynamo KV router | SGLang router |
|---|---|---|---|
| cache 視圖 | 近似（路由歷史）或精確（KV events）兩種插件 | 精確（KV events → 全域 radix tree） | 近似（本地模擬，零同步） |
| 決策形式 | 多 scorer 加權和 | 單一成本函數 | 雙模式切換（閾值觸發） |
| 權衡旋鈕 | 各 scorer 權重 | `kv-overlap-score-weight` | cache/balance 三個閾值 |
| 站位 | K8s 標準路由層（IGW/EPP） | 框架自帶，引擎無關 | SGLang 生態自帶 |

三家殊途同歸的共識值得劃線：**精確的 cache 視圖不是必需品**（SGLang 的近似樹效果就很好，llm-d 把兩種都做成插件讓你選），但**負載分量是必需品**——任何只看 cache 命中的路由器都會自毀，因為 cache affinity 的自然動力學是正回饋:命中越多的 replica 越被選中、cache 越熱、越被選中……直到它 KV 池滿、ITL 崩潰，而其他 replica 在旁邊閒著。scoring 函數裡的負載項就是這個正回饋的阻尼器。你在 ch06 看過引擎內的 preemption storm，這是它的叢集版本，只是這次點火的是路由器自己。

最後把這層放回全局:在 P/D 分離的部署裡，路由是**兩段決策**——先選 prefill 實例（cache 命中主導，因為 prefill 最貴），再選 decode 實例（KV 容量與負載主導，還要考慮「離 prefill 節點的傳輸距離」）。Mooncake 的 Conductor、Dynamo 的 router + planner 做的就是這個聯合決策。路由器在 K8s 上怎麼部署、InferencePool 怎麼配，屬 ch12；這裡你要帶走的是決策邏輯本身。

## 誠實的反面：什麼規模以下不要碰 P/D 分離

這一節是本章的剎車。P/D 分離在 2026 年有強烈的「業界主旋律」光環——Mooncake 的數據、NVIDIA 的推銷、每場 conference 的 talk——但它的收益模型有明確的前提，前提不成立時它是純負債。我給你一張**全部要打勾才考慮**的清單：

| # | 前提 | 檢驗方法 | 不滿足時 |
|---|---|---|---|
| 1 | **雙 SLO 都緊**：TTFT 與 ITL 同時有嚴格目標 | 看你的 SLO 文件——只有吞吐目標或單邊延遲目標? | 分離的全部收益（解耦兩個 SLO）不存在，colocated + chunked prefill 就是最優解 |
| 2 | **單機優化已榨乾**：chunked prefill 調過 token budget、prefix caching 已開且命中率已優化、量化已上（ch05–ch08） | 拿 ch14 的方法 benchmark 過 | 你在用分散式複雜度掩蓋單機調參債，先還債 |
| 3 | **規模夠大**：每個池子都能獨立餵飽——粗準則:總量 ≥ 16 卡、且 xPyD 推演出來的 x 和 y 都 ≥ 2 | 用本章 xPyD 框架算 | 池子整數性吃掉收益（1.3P 進位成 2P）；單池 batch 變淺，decode 吞吐反而掉。llm-d 的 P/D path 範例是 16×16 B200，不是 4 張卡 |
| 4 | **網路在 crossover 右側**：節點間有 ≥400G RDMA（IB/RoCE），理想上 GPU 各配 NIC | 本章公式:BW_eff > KV_bytes × F_eff / Prefill_FLOPs，對你的模型算一次 | 100GbE 以下搬運稅吃掉大半收益；25GbE 以下物理上不成立，重算更快 |
| 5 | **流量形態受益**：輸入顯著長於輸出（RAG、長文件、agentic 的未命中部分），或 prefill 干擾已被量測證實是 ITL 尾延遲主因 | ITL p99 尖刺與長 prompt 到達的相關性分析（ch06 教過） | 短問答流量下 prefill 本來就便宜，分離是搬石頭砸自己的 TTFT |
| 6 | **運維面積養得起**：兩種 deployment、兩套容量模型、一個傳輸層、一個有狀態路由層，全部要有人 on-call | 誠實評估團隊 | 每個新元件都是新的故障面（見下節故障表），人不夠時複雜度殺死可用性 |

我的判斷，直說:**單一 replica 到 8 卡之間的部署，P/D 分離不在你的選項清單上**；16–32 卡、雙緊 SLO、長輸入流量、有 RDMA，開始值得 PoC；到了三位數卡的規模、流量形態極端（Mooncake 那種長 context 主導的服務），它就不是選項而是必然。還有一個常被忽略的中間態:**先上 KV-aware routing，再考慮 P/D 分離**——路由層的收益（prefix cache 命中）不需要分離也能拿到，複雜度低一個量級，而且它本來就是分離架構的前置元件。llm-d 把 routing 列為 Path 1、P/D 列為 Path 2，順序就是這個意思。

## 故障模式與防禦

P/D 分離 + KV 路由比 colocated 部署多出三類故障面:傳輸層、配比、路由狀態。Murphy 清單：

| 故障 | 症狀（你會看到什麼） | 觀測訊號 | 防禦 |
|---|---|---|---|
| KV 傳輸失敗/逾時（RDMA link flap、NIXL 後端錯誤、block 對位失敗） | 零星請求 TTFT 暴增或 5xx；請求卡在「prefill 已完成、decode 未接手」 | 傳輸層錯誤計數、P→D 交接延遲的 p99、孤兒 KV 的量 | 交接設逾時預算；fallback 路徑 = decode 端重算（prompt 必須隨請求傳遞，不能只傳 KV 引用）；傳輸重試要冪等 |
| D 池 KV 池滿，P 池仍持續灌入 | decode preemption 飆升、ITL 全面惡化——ch06 的 preemption storm 跨節點版，但點火的是上游 | D 池 KV utilization、preemption rate、P→D 佇列深度 | D 端 admission control（KV 有位才接收）；P 池產出對 D 池容量做 backpressure；告警設在 KV 水位而非延遲（延遲是落後指標） |
| xPyD 配比失配（流量形態漂移） | 一個池排長隊、另一個池利用率 30%；TTFT 或 ITL 單邊惡化 | 分池的佇列深度與利用率**必須分開看板**（ch14） | planner/獨立 autoscaling（ch13）；產品上新功能（如 agentic）前重跑配比推演 |
| 路由器 cache 視圖漂移（KV events 丟失、近似樹與現實脫節） | 路由器以為命中、引擎實際 miss:路由命中預估與引擎 `prefix_cache_hit_rate` 背離 | 兩個指標的差值做對帳告警 | 索引 TTL/定期重建；事件流斷線時降級為純負載路由而非帶病決策 |
| cache affinity 熱點 | 一台 replica ITL 崩、KV 滿，其他閒置；整體 p99 由熱點決定 | per-replica 負載方差、單 replica KV 水位 | scoring 的負載項權重調高；熱 prefix 識別後允許複製到多台（用一次重算換掉熱點） |
| D 實例故障的爆炸半徑 | 該實例上所有 in-flight 串流全斷；若 P→D 綁定早、佇列深，殃及尚未開始的請求 | 實例存活 + in-flight 計數 | 交接綁定盡量晚（late binding）；斷流重試的成本意識（重試 = 全部重算，retry budget 見 ch15） |
| 路由器本身成為瓶頸/單點 | 所有請求 TTFT 均勻墊高；路由決策延遲進入請求路徑 | 路由決策耗時的 histogram（它在 critical path 上!） | scoring 計算要 O(候選數)；radix tree 操作 sharding（Dynamo 的做法）；EPP 水平擴展(ch12) |

共同主題:這套架構把「一個請求」變成「一次分散式交易」（prefill、傳輸、decode 三個參與者），你在 SQS pipeline 學到的所有紀律——冪等、逾時、補償路徑、backpressure——原封不動適用，只是補償動作從「重發訊息」變成「重算 2 秒的 prefill」，貴了很多，所以更要算著用。

## 動手做

### Lab 10-1 [M1]：用 llm-d-inference-sim 模擬 P/D 分離與路由差異

llm-d-inference-sim 可以模擬 vLLM 的延遲特性（TTFT/ITL 可配置）而不需要 GPU。目標:親手量出「路由策略」對 TTFT 的影響。

1. 起兩個 sim 實例當作兩個 replica（docker 跑兩個 port，設定相同的延遲參數、開啟模擬的 prefix cache 行為）。
2. 寫一個 50 行的 Python 路由器（FastAPI，你在 ch04 寫過同款），實作三種策略:round-robin、session sticky（按 header hash）、prefix-aware（對 prompt 前綴做最長匹配記錄，模仿 SGLang 的近似樹，加上「佇列深度超過閾值就 fallback 最短佇列」）。
3. 用 k6 打多輪對話形態的流量（同 session 重複前綴)，量三種策略的 TTFT p50/p99。
4. **成功標準**:prefix-aware 的 TTFT p99 顯著優於 round-robin；能解釋為什麼 sticky 介於兩者之間；把負載閾值調到 0（純 cache affinity），觀察熱點形成——單一 replica 佇列爆掉，p99 反超 round-robin。親眼看到那個正回饋，比讀十遍文字有用。

### Lab 10-2 [紙上推演]：為三種流量形態設計 xPyD 配比並辯護

用本章框架，對三種流量各算一份配比（硬體統一假設 TP4 H100 實例，模型 Llama-3.3-70B，數字自訂但要寫明）：

1. 短問答:輸入 500 / 輸出 300、200 req/s。
2. 長文件 RAG:輸入 16k / 輸出 500、30 req/s、prefix cache 命中率 20%。
3. Agentic:名目輸入 40k / 輸出 2k、20 req/s、prefix cache 命中率 90%（ch05 的 agentic 計算可複用）。

**成功標準**:每種形態給出 xPyD（或「不要分離」的結論）與兩行辯護；agentic 那題要能說出「名目 prefill 需求與有效 prefill 需求差 10 倍」對配比的顛覆；短問答那題的正確答案是不分離——如果你算出來要分離，回去檢查 P 池需求。

### Lab 10-3 [紙上推演]：對你自己的假想叢集算 crossover

假設你只租得起 4×A100 80GB（NVLink 域內）+ 節點間 100GbE 的雲環境，模型換成 Llama-3.1-8B（每 token KV = 128 KiB，ch03 算過）。重走一遍 worked example 的五步:8k context 的 KV 多大、各路徑搬多久、重算多久、crossover 在哪。**成功標準**:得出「8B 模型 + 小 context 下重算門檻更低、搬運更不划算」的結論並能解釋為什麼（KV bytes/token 與 FLOP/token 的比值隨模型架構變，GQA 比例、層數都影響）；順手回答:如果換成 FP8 KV，結論翻轉嗎？

## 這個領域往哪走

兩個方向值得盯。第一，**NVLink 域的擴張正在改寫 crossover 的物理**:NVL72 把 72 張卡放進同一個 450 GB/s 級的域（ch02），Rubin 世代繼續加倍（2026 H2 起）——當「跨節點」搬 KV 也能走 NVLink 級頻寬，傳輸稅趨近於零，P/D 分離從「要精算的取捨」變成「近乎免費的排程自由度」，反對它的最強論點被硬體拆掉一半。第二，路由層的標準化:Gateway API Inference Extension 已 GA、llm-d/KServe/各家 gateway 都站上去（2026-06），scoring 演算法正在變成可插拔的商品——這對你的職涯訊號是:**理解 scoring 的設計空間比會配某一家的 YAML 值錢**。至於「KV cache 會不會徹底變成一個獨立儲存層、讓 P/D 分離退化成它的一個讀寫模式」，這是 ch17 的辯題。

## 自我檢核

1. prefill 與 decode 的資源畫像衝突具體指什麼？chunked prefill 為什麼是緩解不是根治？（兩個結構性天花板）
2. 不看書，重算一遍:Llama-3.3-70B、32k context 的 KV 多大？走 400G IB 單 NIC 要多久？對比 TP4 H100 重算 prefill，結論是什麼？
3. 寫出「搬 KV vs 重算 prefill」的 crossover 公式，並說出為什麼這個比值近乎與 context 長度無關、attention 的 O(n²) 項又怎麼打破這個無關性。
4. xPyD 配比由哪兩個需求公式決定？prefix cache 命中率為什麼會顛覆配比？流量形態漂移時靠什麼機制調整？
5. 為什麼 session affinity 和 consistent hashing 都不足以做 KV-aware routing？（三個與兩個理由）
6. 寫出 Dynamo KV router 的成本函數，解釋兩項的量綱為什麼統一、唯一的旋鈕往哪邊調會發生什麼。
7. 純 cache affinity 路由的正回饋失控是怎麼發生的？路由器用什麼當阻尼器？你會設什麼告警在它失控前抓到它？
8. 面試官問:「我們有 8 張 H100 跑一個 70B 模型服務內部工具，要不要上 P/D 分離？」給出你的完整判斷過程（提示:六項前提清單，這個場景至少倒在三項上）。

## 延伸閱讀

- [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized LLM Serving（OSDI 2024）](https://arxiv.org/abs/2401.09670) — P/D 分離的奠基論文，goodput 視角與 7.4 倍數字的出處，§3 的干擾分析值得精讀。
- [Splitwise: Efficient Generative LLM Inference Using Phase Splitting（ISCA 2024）](https://arxiv.org/abs/2311.18677) — 用 Azure 生產 trace 論證分離與異質硬體，ISCA 最佳論文；「兩階段用不同卡」思路的源頭。
- [Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving（FAST'25 / arXiv:2407.00079）](https://arxiv.org/abs/2407.00079) — 最完整的生產級 P/D 分離系統論文，Conductor 排程與 Transfer Engine 的設計細節都在這。
- [NVIDIA Dynamo：KV Cache Routing 架構文件](https://github.com/ai-dynamo/dynamo/blob/main/docs/architecture/kv_cache_routing.md) — 成本函數、KVPublisher/KVIndexer 機制的一手來源，搭配 KV Router 調參指南讀。
- [Intelligent Inference Scheduling with llm-d（llm-d blog）](https://llm-d.ai/blog/intelligent-inference-scheduling-with-llm-d) — EPP scorer 管線與權重設計的官方解說，本章 3/2/2 範例配置的出處。
- [SGLang v0.4 release blog：Cache-Aware Load Balancer（LMSYS）](https://lmsys.org/blog/2024-12-04-sglang-v0-4/) — 近似 radix tree 路由器的設計與 3.8 倍命中率數據；證明「不精確的 cache 視圖也夠用」。
- [NIXL（NVIDIA Inference Xfer Library,GitHub）](https://github.com/ai-dynamo/nixl) — 跨節點 KV 搬運的共同地基，README 的後端清單就是一張傳輸路徑地圖。
- [Disaggregated Inference on AWS powered by llm-d（AWS blog）](https://aws.amazon.com/blogs/machine-learning/introducing-disaggregated-inference-on-aws-powered-by-llm-d/) — 雲商視角的 P/D 分離落地參考架構，看大廠怎麼包裝這套複雜度。
