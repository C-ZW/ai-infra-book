# ch06 — Batching 與單機排程：吞吐的來源

> **本章解決什麼問題**：ch03 證明了 decode 是 memory-bound、ch05 解決了 KV cache 怎麼存，本章回答「推論引擎為什麼快」的核心問題——continuous batching 與引擎內排程器。一張 GPU 從每秒 160 token 到每秒 6,800 token，差的不是硬體，是排程。這章也是你既有排程與 queue 直覺最能直接發揮的一章，並為 ch08 的引擎調參、ch10 的 P/D 分離、ch13 的容量規劃打地基。

## 從你已知的出發

你做過這件事：把結算 pipeline 裡一筆一筆的 `INSERT` 改成批次寫入，RDS CPU 應聲下降。原理你很清楚——每次資料庫往返有固定成本（網路 round trip、交易開銷、WAL flush），批次化把固定成本攤提到更多筆資料上。

GPU decode 的 batching 是同一件事，只是固定成本大得離譜。ch03 算過：decode 每生成一個 token，GPU 必須把**整份模型權重**從 HBM 讀進運算單元一次。8B 模型 FP16 就是 16 GB——這是每一步的「固定成本」。一次只服務一個請求，等於每次資料庫往返只 INSERT 一筆。把 128 個請求的 decode 排進同一步，權重還是只讀一次，固定成本被攤提 128 倍。這就是吞吐的來源，沒有魔法。

第二個你熟的東西：SQS consumer 的 batch 參數。你設定過 `MaxNumberOfMessages` 和 `WaitTimeSeconds`——湊滿一批就送，或等逾時就送。這正是等一下要講的 dynamic batching，LLM serving 在 2022 年之前就停在這個階段。它的問題你大概已經猜到了：批內成員必須一起進一起出，而 LLM 請求的「處理時長」變異是 1,000 倍級的（生成 10 個 token vs 生成 10,000 個 token），一起進一起出意味著所有人陪最長的那個等。

第三個：queue 理論。你在遊戲後端看過慢查詢吃光 connection pool 的事故——一條 full table scan 卡住，後面排隊的全部秒級查詢一起陪葬。這叫 head-of-line（HOL）blocking，而它惡化的速度由 Pollaczek–Khinchine 公式決定：等待時間正比於**服務時間的二階動差**，不是平均值。LLM 流量的服務時間分布是重尾中的重尾（一個 100k-token 的 RAG prompt 混在一堆 50-token 的問答裡），所以 HOL blocking 不是邊角案例，是 LLM 排程的中心問題。本章一半的篇幅都在處理它的各種化身。

把這三個直覺帶著，新東西其實只有一個：**LLM 請求是迭代的**。一個 HTTP 請求是一次性的工作；一個 LLM 請求是「先做一次大的 prefill，然後做幾十到幾千次小的 decode 迭代」。排程單位從「請求」變成「迭代」，整個排程理論的物理常數就變了。

## 從 static 到 continuous batching：三代演進

每一代解一個問題，留一個問題。

### Static batching：HPC 的遺產

最早的做法直接繼承自訓練：湊滿 N 個請求，padding 到等長，一起 forward 到全部結束。兩個致命傷：

1. **等慢者**：batch 裡有人生成 20 個 token 就完了，有人要生成 2,000 個。先完成的請求的 slot 就空轉，GPU 算力照燒，直到最慢的那個結束。有效利用率可以掉到 10% 以下。
2. **Padding 浪費**：不等長的 prompt 要 padding 到一樣長，padding token 的計算全是垃圾。

### Dynamic batching：你的 SQS 直覺

進步版：設一個湊批窗口（如 100ms）與批次大小上限，先到先湊，湊滿或逾時就發車。這解了「請求到達時間不齊」的問題，但**排程單位仍然是請求**——車開了就不能上下客。等慢者問題原封不動。

對一次性請求（圖片分類、embedding）這夠用了，NVIDIA Triton Inference Server 的 dynamic batcher 至今仍是這類 workload 的標準解。但對生成式 workload，它撞牆。

### Continuous batching：Orca 的 iteration-level scheduling

2022 年 OSDI 的 Orca 論文（首爾大學/FriendliAI）做了那個事後看來顯然、當時沒人做的事：**把排程粒度從 request 降到 iteration**。每一個 decode step 結束，排程器重新決定下一步的 batch 組成——完成的請求立刻離開、釋放資源；佇列裡的新請求立刻加入，不用等任何人。車變成了捷運：每站都能上下客。

Orca 還配了一個技術細節叫 selective batching：attention 運算因為每個請求的 context 長度不同無法直接 batch，但佔大頭的線性層（FFN、QKV projection）可以把所有請求的 token 展平成一個大矩陣一起算。這個「線性層合批、attention 各算各的」的結構，今天所有主流引擎都在用。

Orca 在 GPT-3 175B 上對 NVIDIA FasterTransformer 做出了同延遲下 36.9 倍的吞吐提升。2023 年 Anyscale 用 vLLM 重現這個機制時量到「最高 23 倍吞吐」，continuous batching 從論文變成業界預設。今天（2026-06）你找不到任何一個主流 LLM 推論引擎不是 continuous batching——這個詞已經失去區別度，差異化都在更細的地方：prefill 怎麼混（下節）、誰先誰後（排程策略節）、記憶體不夠誰倒楣（preemption 節）。

還有一塊拼圖：continuous batching 要求「隨時有請求加入」，意味著 KV cache 必須能動態、非連續地配置——這正是 ch05 PagedAttention 存在的理由。兩者是一體的：沒有 paged KV，continuous batching 的 batch size 會被記憶體碎片掐死；沒有 continuous batching，paged KV 省下的記憶體沒人用。

## 引擎迴圈：每一步都在重新排程

把引擎想成一個單執行緒 event loop（你寫 Node.js 的直覺在這裡意外地好用），核心是一個不斷重複的 step：

```text
loop:
  # 1. 排程（CPU,目標 < 1ms）
  schedule():
    - 把完成的請求移出 running、釋放 KV blocks
    - 從 waiting 佇列依策略（FCFS/priority）取請求,
      問 KV cache manager「夠不夠 blocks?」→ 夠才 admit
    - 在 token budget 內決定本步的組成：
      所有 running 請求的 decode token + 若干 prefill chunk
  # 2. 執行（GPU,毫秒級）
  forward() → 每個請求得到下一個 token 的 logits
  sample()  → 抽出 token
  # 3. 收尾
  - 把新 token 透過 streaming 回給各個 client
  - 檢查 stop 條件（EOS、max_tokens、client abort）
```

幾個值得停下來看的點：

- **admission 是用 KV blocks 當貨幣的**。一個請求能不能進 running，不是看「batch 還有沒有空位」，而是看 KV cache manager 還有沒有 free blocks 裝它的 prompt。這就是 ch05 與本章的接縫。
- **admission 是樂觀的**。排程器 admit 一個請求時，只知道它的 prompt 長度，不知道它會生成多少 token。KV 占用會隨生成持續長大，所以「admit 時夠」不代表「永遠夠」——這個樂觀假設破產時，就是 preemption（後面整節講）。
- **每一步的排程開銷必須遠小於 forward 時間**。decode 一步是幾毫秒到幾十毫秒，排程器若花 2ms 做決策，吞吐直接折損兩成。這是 vLLM V1 重寫排程器、把邏輯壓進極簡資料結構的動機之一，也是 decode 端需要 CUDA graphs 消 launch overhead 的原因（見 ch07）。
- **client 斷線必須走 abort 路徑**。SSE client 斷線（你做 WebSocket 太熟了）如果引擎不知道，這個請求會繼續占著 slot 和 KV blocks 生成沒人收的 token。引擎有 abort API，但上游 gateway 要負責把斷線翻譯成 abort——這是平台層的責任（見 ch12）。

vLLM V1（2026-06 唯一的引擎世代，V0 已在 v0.11 完全移除）的排程器有個優雅的簡化：它不再區分「prefill 階段」與「decode 階段」的請求，排程決策只是「這一步，每個請求算幾個 token」——decode 請求算 1 個，prefill 請求算一個 chunk。這個統一視角是理解下一節的最好起點。

## Worked example：batch 1→256，吞吐與 ITL 的完整曲線

紙上推演一次，數字會跟著你走完後面所有章節。

**設定**（刻意簡化，但每個簡化都標出來）：

- 硬體：H100 SXM，80 GB HBM3，理論頻寬 3.35 TB/s。取**有效頻寬 2.6 TB/s**（約理論值 78%，實測常見區間）。
- 模型：Llama-3.1-8B 級的 dense 8B，FP16 權重 = **16 GB**。32 層、GQA 8 個 KV head、head_dim 128 → KV cache = **128 KB/token**（ch03 公式算過）。
- 流量：穩態下每個請求平均 context 2,000 tokens（prompt 1,500 + 已生成 500）→ 每請求 KV = 2,000 × 128 KB = **256 MB**。
- 簡化模型：decode 一步的時間 = 該步要從 HBM 讀的 bytes ÷ 有效頻寬（純 memory-bound 假設，稍後驗證）。忽略排程與 kernel launch 開銷。

每一步要讀的資料 = 權重 16 GB（固定成本）+ B × 0.256 GB（每個請求自己的 KV，變動成本）。算出來：

| Batch B | 每步讀取 | t_step = ITL | 總吞吐 | 單請求速度 | KV 占用 |
|---:|---:|---:|---:|---:|---:|
| 1 | 16.3 GB | 6.3 ms | 160 tok/s | 160 tok/s | 0.26 GB |
| 8 | 18.0 GB | 6.9 ms | 1,150 tok/s | 144 tok/s | 2.0 GB |
| 32 | 24.2 GB | 9.3 ms | 3,440 tok/s | 108 tok/s | 8.2 GB |
| 64 | 32.4 GB | 12.5 ms | 5,140 tok/s | 80 tok/s | 16.4 GB |
| 128 | 48.8 GB | 18.8 ms | 6,820 tok/s | 53 tok/s | 32.8 GB |
| 256 | 81.5 GB | 31.4 ms | 8,160 tok/s | 32 tok/s | **65.5 GB ← 撞牆** |

畫成曲線（ITL = inter-token latency，使用者感受到的逐字輸出間隔）：

```text
吞吐 (tok/s)
8000 |                              * 256
     |                    * 128
6000 |
     |           * 64
4000 |      * 32
     |
2000 |   * 8
   0 | * 1
     +---+----+----+-----+-----+----►  batch size B
         1    8    32    64    128/256

ITL (ms)
  32 |                              * 256
     |
  24 |
     |                    * 128
  16 |
     |           * 64
   8 | *---*----* 32
     | 1   8
     +---+----+----+-----+-----+----►  batch size B
         1    8    32    64    128/256
```

甜蜜區約 B = 8~64；ITL 在 B > 64 後加速惡化。

**三個關鍵讀法**：

1. **邊際報酬遞減，但代價遞增**。B 從 1→8，吞吐 ×7.2，ITL 只 +11%——近乎免費的午餐，因為固定成本（16 GB 權重）還遠大於變動成本（2 GB KV）。B 從 32→128，吞吐只 ×2.0，ITL 卻 +102%——變動成本（KV 讀取）開始主導。甜蜜點就在固定成本與變動成本交叉的附近：本例中 B≈64（16.4 GB KV ≈ 16 GB 權重）。
2. **KV 容量撞牆點先於 roofline**。可用 KV pool：80 GB × 0.90（`gpu-memory-utilization`）− 16 GB 權重 − 約 4 GB activation/工作區 ≈ **52 GB**，除以每請求 256 MB ≈ **最多 203 個併發請求**。B=256 在物理上根本放不下——曲線最右邊那個點是虛構的，實際引擎會在 B≈200 處停止 admit、開始排隊或 preempt。注意：撞牆點完全由流量的 context 長度決定，如果平均 context 是 8k 而非 2k，每請求 KV 變 1 GB，牆提前到 B≈52。
3. **decode 幾乎永遠 memory-bound，所以甜蜜點由 SLO 決定，不由 roofline 決定**。驗算 compute 時間：每 token 約 2 × 8B = 16 GFLOP，H100 有效算力取 600 TFLOPS，則每加一個請求增加約 0.027 ms 的 compute，但增加 0.256 GB ÷ 2.6 TB/s ≈ 0.098 ms 的記憶體讀取。**KV 讀取的成長速度是 compute 的 3.6 倍**——batch 開再大，decode 也追不上 roofline 拐點（除非 context 極短）。這推翻一個常見誤解「batch 大到 compute-bound 就是最佳點」：實務上你會先撞 ITL SLO 或 KV 牆。若你的 ITL SLO 是 p95 < 20 ms，B=128（18.8 ms）已經貼著天花板，甜蜜點落在 64~128 之間。

這個簡化模型跟現實的主要偏差：真實 ITL 還要加上排程開銷與 kernel launch（CUDA graphs 處理，見 ch07）、prefill 混入的干擾（下一節）、以及每個請求 context 長度的分布而非平均。但量級與曲線形狀是對的——你在「動手做」會親手驗證。

## Chunked prefill：別讓一個長 prompt 卡住所有人

Continuous batching 解了「等慢者」，卻引入新的 HOL blocking：**prefill 與 decode 的資源畫像衝突**（ch03 證明過：prefill 是 compute-bound，decode 是 memory-bound）。

具體有多痛，接著上面的數字算：一個 8k token 的 prompt 進來，prefill 的計算量 ≈ 2 × 8B × 8,192 ≈ 131 TFLOP，以 700 TFLOPS 的有效 prefill 算力要跑約 **187 ms**。如果引擎把這個 prefill 當成一個完整 iteration 執行，batch 裡所有正在 decode 的請求這一步都要等它——**每個使用者的 ITL 從 9 ms 突然跳到 190+ ms**，逐字輸出肉眼可見地卡住一下。流量裡只要有穩定比例的長 prompt，你的 ITL p99 就會長出一根又一根的尖刺。這就是 ch10 P/D 分離要根治的干擾問題，但單機上先有一個夠好的緩解：chunked prefill。

想法來自 Sarathi-Serve（OSDI 2024）：**把 prefill 切成小塊，每一步只做一塊，跟 decode 混在同一個 batch 裡執行**。關鍵洞察是 decode 步是 memory-bound 的，GPU 的算力在 decode 步大量閒置（上面驗算過：B=128 的 decode 步，compute 只占約 3.5 ms，記憶體讀取要 18.8 ms）——把 prefill chunk 塞進這個算力空檔，接近免費。

機制上由一個 **token budget**（vLLM 的 `max-num-batched-tokens`）控制：每一步全部請求合計最多處理這麼多 token。decode 請求每個占 1 個 token，剩下的預算給 prefill chunk。vLLM V1 預設啟用 chunked prefill，且排程策略是 **decode 優先**：先排所有 decode，剩餘預算才給 prefill，塞不下就自動切塊（2026-06，vLLM 官方文件）。

Budget 的大小是一個純粹的 **ITL vs TTFT 交換**，用我們的數字走一遍 8k prompt、背景 B=128 decode 的場景：

| token budget | 8k prefill 切成 | 混合步的步長 | 背景請求 ITL | 該 prompt 的 TTFT |
|---:|---:|---:|---:|---:|
| 不切（對照） | 1 塊 | ~190 ms | **尖刺到 ~190 ms** | ~187 ms |
| 4,096 | 2 塊 | ~94 ms | 尖刺到 ~94 ms | ~190 ms |
| 2,048 | 4 塊 | ~50 ms | 尖刺到 ~50 ms | ~200 ms |
| 512 | 16+ 塊 | ~20 ms | **幾乎無感（≈19 ms）** | ~240 ms（+28%） |

（步長取 max(decode 記憶體時間, chunk 計算時間) 的近似；chunk 越小，跨 chunk 的重複開銷越多，所以 TTFT 緩慢上升。）

官方調參指引與這張表一致：**budget 調小（如 2048）保 ITL，調大（如 >8192）保 TTFT 與吞吐**——大 GPU 跑小模型時官方建議調大，因為 chunk 太小餵不飽算力。預設值隨版本演進，以你手上版本的 `vllm serve --help` 為準（本書寫作時為 vLLM 0.22.x；完整參數表見 ch08）。V1 另提供 `long_prefill_token_threshold` 與 `max_long_partial_prefills`，限制同一步裡「長 prefill」的數量，避免多個長 prompt 同時把預算吃光——本質上是給重尾分布的頭部單獨設一條 queue，你在 API gateway 做過一模一樣的事（慢端點獨立 worker pool）。

要誠實說的限制：chunked prefill 是**緩解不是根治**。混合步的步長仍然比純 decode 步長，ITL 還是會被墊高一截；而且 budget 守恆——prefill 吞吐與 decode 平滑度在單機上是零和的。流量大到一定規模，把 prefill 和 decode 拆到不同的 GPU 池才是正解，那是 ch10 的主題。

## Preemption：記憶體不夠時，誰倒楣

回到引擎迴圈裡那個樂觀假設：admit 時不知道請求會生成多少 token。穩態下 KV pool 用到 85%，然後流量裡的長對話們同時繼續長大——free blocks 歸零，而 running 裡每個請求下一步都還要新 block。某人必須把記憶體吐出來。

兩種吐法：

- **Recompute**：選一個受害者（vLLM 選 running 裡最晚到的，priority 模式下選低優先權的），直接丟掉它的所有 KV blocks，把它踢回 waiting 佇列。等記憶體鬆了，從頭 re-prefill 它的「prompt + 已生成的 token」再繼續。
- **Swap**：把受害者的 KV blocks 搬到 CPU RAM，要恢復時搬回來。

紙上比一下成本，以我們的 2k context 請求（KV 256 MB）為例：recompute 要重算 2,000 token 的 prefill ≈ 46 ms 純算力；swap 走 PCIe Gen5 x16（~64 GB/s）約 4 ms 搬出 + 4 ms 搬回。原始數學上 swap 大勝——但 **vLLM V1 的預設與唯一 preemption 路徑是 recompute**（2026-06，官方文件，理由是 V1 架構下 recompute 開銷更低）。為什麼工程上反過來選？三個原因值得你記住，因為這是「紙上最優 ≠ 系統最優」的經典案例：

1. Swap 的搬運要跟引擎迴圈同步，搬運期間 blocks 占著茅坑，且 CPU 側的 block 管理是一整套額外的狀態機；recompute 走的是「新請求 admission」這條本來就存在、被千錘百鍊的路徑，零新增複雜度。
2. 有了 chunked prefill，recompute 不會卡住別人；有了 prefix caching（ch05），受害者的 prompt 前綴若還在 cache 裡，重算可能大部分免費。
3. 「KV 搬到 CPU/SSD」這件事沒有消失，而是搬到了更通用的 KV offloading / connector 層去做（ch05 的分層、ch10 的傳輸），不再跟 preemption 這個緊急路徑綁死。

**Preemption 對尾延遲的傷害是雙重的**：受害者本人 stall——它要排隊、re-prefill，token 流中斷可達數百 ms 到秒級（使用者看到打字打到一半凍住）；同時 recompute 是憑空多出來的工作，**系統越忙，preemption 越多；preemption 越多，系統越忙**。這個正回饋你在生產環境見過它的孿生兄弟：retry storm。差別是 retry storm 的放大器在 client 端，preemption storm 的放大器在引擎自己體內。放任不管的終局是死亡螺旋，防禦工事（admission control、load shedding 的位置）在 ch13 詳談；單機層面你要知道的是：**preemption 應該是罕見事件**——監控 `vllm:num_preemptions_total` 的速率，穩態下持續非零就代表 KV 預算配置錯了，該調的是 `max-num-seqs`（少 admit 一點）或 `gpu-memory-utilization`（多給 KV 一點）。

## 排程策略：FCFS、priority 與公平性

排程器從 waiting 佇列挑人的策略，直接決定誰的 TTFT 好看、誰餓死。

**FCFS（先到先服務）**是 vLLM 的預設。優點是絕不餓死任何人、行為可預測；缺點正是開頭講的 HOL blocking——一個 100k-token 的 prefill 排在佇列頭，後面所有 50-token 的快問快答都得等它。重尾流量下，FCFS 的 TTFT p99 由流量裡最長的 prompt 決定，跟你的容量幾乎無關。這跟 OLTP 連線池被分析型查詢卡死是同構問題，解法的方向也同構：隔離（長短請求分池，ch10 的 P/D 分離與 ch12 的多池路由）或插隊（priority）。

**Priority scheduling**：vLLM V1 支援 `--scheduling-policy priority`，請求帶 priority 欄位，同優先權內以到達時間決勝（2026-06）。Priority 解 HOL 的同時引入它的經典代價：**starvation**——只要高優先權流量足夠多，低優先權請求的 TTFT 沒有上界。教科書解法是 aging（等越久優先權越高），但截至我能確認的資訊（2026-06），vLLM 內建排程器沒有 aging，餓死防禦要自己在上游做（per-tier 的配額或佇列逾時）。另一個 LLM 特有的坑：priority 搭配 preemption 意味著高優先權請求進來時，低優先權的**正在生成的**請求會被踢回去重算——插隊的不只是佇列位置，還有別人已經付過的算力。

**SLO-aware / goodput-aware 排程**是進行中的方向：排程器知道每個請求的 TTFT/ITL 目標，挑人時最大化「能在 SLO 內完成的請求數」而非單純吞吐——例如 decode 池 ITL 已貼近 SLO 時，暫緩 admit 新的長 prefill。引擎內建的這類策略還在演化中，而業界的實際走法是把這層智慧上移：單機引擎保持簡單（FCFS/priority + chunked prefill），SLO 感知做在路由層（llm-d 的 inference scheduler、Dynamo 的 planner，見 ch10/ch12）。我認為這個分層是對的——排程器每步只有不到 1ms 的決策預算，複雜的最佳化放在請求進入引擎之前做，代價更低。

一個容易被忽略的設計原則收尾：**佇列管理屬於整個系統，不只屬於引擎**。引擎的 waiting 佇列是無界的——它不會回 429。如果你讓佇列在引擎裡堆積，TTFT 會無聲地爆炸而 GPU 指標一切正常（佇列先於資源指標惡化，你在遊戲後端的尖峰日看過這個模式）。Admission control 必須做在 gateway（ch12），引擎佇列深度必須上監控（ch14）。

最後一個越來越重要、卻常被排程討論忽略的負載：**constrained decoding（structured output）**。Agentic 流量大量要求 JSON schema 或 grammar 約束的輸出（ch17），引擎要在**每個 decode step** 對 logits 套 token mask——grammar 的編譯與逐步 mask 計算發生在 CPU 端。主流引擎已把 mask 計算 overlap 進 GPU step 的空檔（xgrammar 一系，2026-06），但一個 batch 裡只要有幾條複雜 schema 的請求，CPU 端仍可能追不上 GPU 的節奏，於是**整個 batch 的 ITL 一起被拖慢**——又一個「batch 裡的請求不獨立」的例子，而且症狀很陰：全池 ITL 上升，GPU 指標一切正常（GPU 在等 CPU）。防禦：確認 grammar 編譯快取命中（首個請求付編譯成本）、把重 schema 流量隔離到獨立池（ch12）、監控 structured output 請求的占比與該類請求的 ITL 分布。這類 workload 也是引擎間差距最明顯的地方之一（SGLang 以此起家，見 ch08）。

## 三個參數，一條曲線

vLLM 的完整參數表在 ch08，但有三個參數的**系統意義**屬於本章，因為它們就是上面三節的物理量的旋鈕：

| 參數 | 控制什麼物理量 | 調大的收益 / 代價 | 調小的收益 / 代價 |
|---|---|---|---|
| `--max-num-seqs` | batch size B 的上限（同時 running 的請求數） | 吞吐↑ / ITL↑、KV 壓力↑、preemption 風險↑ | ITL↓、行為穩定 / GPU 餵不飽、佇列堆積 |
| `--max-num-batched-tokens` | 每步 token 預算（prefill chunk 的大小） | TTFT↓、prefill 吞吐↑ / ITL 尖刺↑ | ITL 平滑 / TTFT↑、長 prompt 變慢 |
| `--gpu-memory-utilization` | KV pool 的大小（撞牆點的位置） | 撞牆點後移、preemption↓ / OOM 風險↑（activation 尖峰、碎片沒餘裕） | 安全餘裕↑ / 同樣流量下更早 preempt |

三個一起看才有意義，因為它們共同決定你在 latency-throughput 曲線上的工作點：`gpu-memory-utilization` 決定牆在哪、`max-num-seqs` 決定你貼牆多近、`max-num-batched-tokens` 決定 prefill 的干擾形狀。症狀導向的速查：

- ITL p99 有尖刺、與長 prompt 到達相關 → budget 調小，或限制併發長 prefill。
- `num_preemptions_total` 穩態非零 → `max-num-seqs` 調小或 `gpu-memory-utilization` 調大。
- GPU 閒、佇列長、吞吐上不去 → `max-num-seqs` 太保守。
- 偶發 engine OOM crash → `gpu-memory-utilization` 太貪心，留餘裕。

## Goodput：滿足 SLO 的吞吐才算數

本章到處在講「吞吐 vs 延遲」的取捨，需要一個單一數字把取捨收斂成可以做決策的指標。業界（源頭是 DistServe 論文，OSDI 2024）給它的名字是 **goodput**：每秒**在 SLO 內**完成的請求數（通常再除以 GPU 數，變成 per-GPU goodput）。SLO 同時含 TTFT 與 ITL 兩條——任一條超標，這個請求對 goodput 的貢獻是零，不管它生成了多少 token。

用 worked example 的數字示範為什麼這個區分性命攸關。設 SLO 為 ITL p95 < 20 ms：

| 配置 | B 上限 | 總吞吐 | ITL | goodput 視角 |
|---|---:|---:|---:|---|
| 保守 | 64 | 5,140 tok/s | 12.5 ms | 全部達標，goodput = 吞吐 |
| 貼線 | 128 | 6,820 tok/s | 18.8 ms | 達標，但毫無餘裕——流量稍偏長 context 就翻車 |
| 貪心 | 256 | 8,160 tok/s* | 31.4 ms | **吞吐最高、goodput ≈ 0**——每個請求都超標 |

（*且 B=256 已超過 KV 牆，實際還會疊加 preemption。）

「貪心」配置在 benchmark 報告裡是冠軍，在生產環境是事故。這就是為什麼 benchmark 只報 throughput 是半個謊言，也是 ch13 容量規劃的基本面：**你採購的是 goodput，不是 throughput**。goodput 怎麼正確量測（SLO 怎麼定、coordinated omission 怎麼避開、frontier 曲線怎麼跑）是 ch14 的主題，這裡你只需要把概念裝進腦袋：從今天起，看到任何吞吐數字，第一個反射問句是「在什麼延遲約束下？」。

## 故障模式與防禦

| 故障模式 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| Preemption storm | ITL p99 突發尖刺、吞吐反而下降、使用者看到生成「凍住」 | `vllm:num_preemptions_total` 速率 > 0 且與 `vllm:kv_cache_usage_perc` ≈ 100% 同時出現 | 調小 `max-num-seqs` / 調大 KV pool；上游 admission control；prefix caching 降低 KV 壓力 |
| 長 prompt HOL（chunked prefill 失效或 budget 過大） | ITL p99 規律尖刺，時間點與長 prompt 到達吻合 | ITL histogram 的雙峰；尖刺與 prompt 長度分布做相關 | 調小 token budget；限制併發長 prefill；規模夠大上 P/D 分離（ch10） |
| 引擎佇列無聲堆積 | TTFT 爆炸但 ITL 與 GPU 指標全部正常 | `vllm:num_requests_waiting` 持續上升；排隊時間納入 tracing（ch14） | Admission control 放 gateway 回 429，別讓引擎佇列當緩衝；以佇列深度驅動擴容（ch13） |
| Priority 下的 starvation | 低優先權租戶 TTFT p99 無上界、體驗投訴 | 按 priority 分組看 TTFT 分位數 | 上游 per-tier 配額與佇列逾時；謹慎使用跨層 preemption |
| `gpu-memory-utilization` 過貪 → OOM | 流量尖峰時引擎直接 crash、pod 重啟、所有 in-flight 請求全滅 | engine OOM log；重啟事件與流量尖峰相關 | 留餘裕（activation 尖峰、CUDA graphs 也吃記憶體）；壓測時專門打長 context 流量 |
| Client 斷線不釋放 slot | running 數高但輸出 token rate 低；「忙碌但無效」 | running 請求數 vs 實際 token 輸出率的背離 | 確認 gateway 把 SSE 斷線翻譯成引擎 abort；設 max_tokens 上限 |
| Benchmark 自欺（高吞吐零 goodput） | 上線後 SLO 大面積超標，但壓測報告很漂亮 | 壓測時同時記錄延遲分位數與 SLO 達成率 | 永遠報 goodput@SLO 而非裸吞吐（方法論見 ch14） |

共同主題：這張表裡沒有一項是「模型」的問題，全部是排程與記憶體的問題——呼應全書主軸一，LLM serving 本質上是 memory 的生意。

## 動手做

### 實驗 1 [紙上推演]：把 worked example 換成你的場景

用本章的簡化模型重算一條曲線：同一張 H100，流量改成平均 context 8,000 tokens（agentic workload 的典型值），ITL SLO p95 < 25 ms。

步驟：每請求 KV = 8,000 × 128 KB = 1 GB；重算 B ∈ {1, 8, 32, 64} 的每步讀取量、ITL、吞吐；算 KV 牆（52 GB ÷ 1 GB ≈ 52 個併發）；找出 SLO 內的最大 B。

**成功標準**：你能說出「context 從 2k 變 8k，甜蜜點從 ~64 移到哪裡、牆從 ~200 移到哪裡」，並解釋為什麼長 context 流量讓 batch 的紅利急遽縮水（變動成本 4 倍，固定成本不變）。加分題：如果換成 70B FP16 模型會發生什麼？（提示：140 GB 權重，單卡裝不下——這就是 ch09 存在的理由。）

### 實驗 2 [M1]：用模擬器 + k6 重現飽和曲線

llm-d-inference-sim 是一個模擬 vLLM API 行為的輕量 server（不需要 GPU），可以設定 `max-num-seqs`、TTFT/ITL 等參數；k6 是你的主場。

```bash
# 啟動模擬器（示意,旗標以 repo README / --help 為準）
docker run -p 8000:8000 ghcr.io/llm-d/llm-d-inference-sim:latest \
  --model fake-8b --max-num-seqs 64 \
  --time-to-first-token 200 --inter-token-latency 10
```

```javascript
// k6 骨架（示意）：階梯式拉高併發,觀察吞吐何時平頂
import http from 'k6/http';
export const options = {
  scenarios: { ramp: { executor: 'ramping-vus',
    stages: [ { duration: '1m', target: 32 },
              { duration: '1m', target: 64 },
              { duration: '1m', target: 128 } ] } },
};
export default function () {
  http.post('http://localhost:8000/v1/completions', JSON.stringify({
    model: 'fake-8b', prompt: 'hello', max_tokens: 100,
  }), { headers: { 'Content-Type': 'application/json' } });
}
```

對三檔 `--max-num-seqs`（16 / 64 / 128）各跑一輪。**成功標準**：畫出三條「併發 vs 吞吐」曲線，觀察到吞吐在併發超過 `max-num-seqs` 後平頂、延遲開始線性堆積——這就是佇列堆積的形狀，跟你壓測後端服務看到的飽和曲線同構。

### 實驗 3 [租 GPU]：真 vLLM 上的三檔對比（估 $3–5）

租一張單卡（L4/A10 級即可跑 8B，約 $0.5–1.0/hr，2026 年年中快照；用完即關）：

```bash
pip install vllm
# 三檔分別啟動（每次只改 max-num-seqs: 16 / 64 / 256）
vllm serve Qwen/Qwen3-8B --max-num-seqs 64 --gpu-memory-utilization 0.90

# 官方 bench 子命令打負載
vllm bench serve --model Qwen/Qwen3-8B \
  --dataset-name random --random-input-len 1500 --random-output-len 500 \
  --request-rate 8 --num-prompts 200
# 同時在另一個終端盯指標
curl -s localhost:8000/metrics | grep -E 'num_preemptions|kv_cache_usage|num_requests_(running|waiting)'
```

**成功標準**：產出一張三檔對比表（throughput、TTFT p95、ITL p95、preemption 次數），並能指出哪一檔撞了 KV 牆（preemption 計數開始走動）、哪一檔 GPU 餵不飽（waiting 持續 > 0 但 running 遠低於上限）。記得：卡用完立刻關，先設預算警報再開卡。

## 這個領域往哪走

短期（1–2 年）內，單機排程器本身會維持「簡單而快」：每步決策預算不到 1ms，複雜度長不上去。智慧在往兩頭移動——往上移到路由層（KV-aware、SLO-aware 的請求分配，ch10/ch12），往下移到對 workload 的假設裡：agentic 流量（長 session、高 prefix 重複、機器發起的突發，見 ch17）正在讓「公平性」與「priority + preemption 的代價」從教科書議題變成計費與多租戶的核心問題（ch16）。另一條值得盯的線是 goodput-aware 的引擎內排程與更細粒度的 preemption（只踢部分 blocks 而非整個請求）——研究很多，生產落地還早。機制會變，但本章的分析框架（固定成本攤提、HOL blocking、樂觀 admission 的代價）十年內不會過期。

## 自我檢核

1. 為什麼 batching 能提升 decode 吞吐？用「固定成本 vs 變動成本」講清楚，並指出 batch 開大後是哪一項變動成本讓報酬遞減。
2. Static、dynamic、continuous batching 各解了什麼問題、留了什麼問題？Orca 的 iteration-level scheduling 改變的核心是什麼？
3. 為什麼說「decode 在長 context 流量下永遠是 memory-bound，batch 開再大也到不了 roofline 拐點」？給出每加一個請求的 compute 增量與記憶體讀取增量的比較。
4. Chunked prefill 的 token budget 調大與調小，各犧牲誰、保護誰？什麼情況下官方建議把它調大？
5. vLLM V1 的 preemption 為什麼選 recompute 而不是紙上更便宜的 swap？preemption 對尾延遲的雙重傷害是哪兩重？
6. `max-num-seqs`、`max-num-batched-tokens`、`gpu-memory-utilization` 三個參數各控制曲線的哪個物理量？給你「ITL p99 規律尖刺且與長 prompt 到達相關」的症狀，你先動哪個？
7. Throughput 與 goodput 的差別是什麼？為什麼一個 benchmark 冠軍配置可能 goodput ≈ 0？
8. 你的服務 ITL p95 從 10 ms 變成陣發性的 300 ms，GPU utilization 正常。寫出你的診斷順序（提示：至少要查 preemption 計數、KV 使用率、長 prompt 相關性三件事）。

## 延伸閱讀

- [Orca: A Distributed Serving System for Transformer-Based Generative Models（OSDI 2022）](https://www.usenix.org/conference/osdi22/presentation/yu) — continuous batching 的源頭論文，iteration-level scheduling 與 selective batching 的原始定義，值得精讀第 3、4 節。
- [Taming Throughput-Latency Tradeoff in LLM Inference with Sarathi-Serve（OSDI 2024）](https://arxiv.org/abs/2403.02310) — chunked prefill 與 stall-free batching 的論文，把本章「prefill 干擾」的量化分析做到極致。
- [DistServe: Disaggregating Prefill and Decoding for Goodput-optimized LLM Serving（OSDI 2024）](https://arxiv.org/abs/2401.09670) — goodput 一詞的出處，也是 ch10 P/D 分離的理論前導。
- [How continuous batching enables 23x throughput in LLM inference（Anyscale）](https://www.anyscale.com/blog/continuous-batching-llm-inference) — 把 Orca 機制講給工程師聽的經典部落格，benchmark 方法寫得誠實。
- [vLLM 官方文件：Optimization and Tuning](https://docs.vllm.ai/en/stable/configuration/optimization/) — 本章三個參數與 preemption 行為的第一手調參指引，版本更新快，以此為準。
- [vLLM 官方文件：Metrics 設計](https://docs.vllm.ai/en/stable/design/metrics/) — `num_preemptions_total`、`kv_cache_usage_perc` 等指標的定義與設計理由，ch14 的前菜。
- [Inside vLLM: Anatomy of a High-Throughput LLM Inference System（Aleksa Gordić）](https://www.aleksagordic.com/blog/vllm) — 對 vLLM V1 引擎迴圈與排程器最完整的第三方解剖文，讀完本章再讀它，程式碼就看得懂了。
- [5 steps to triage vLLM performance（Red Hat Developer, 2026-03）](https://developers.redhat.com/articles/2026/03/09/5-steps-triage-vllm-performance) — 用本章指標做生產診斷的實戰 runbook 範例。
