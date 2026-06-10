# ch07 — 模型壓縮與加速：quantization、speculative decoding、kernels

> **本章解決什麼問題**：ch05 管好了 KV cache、ch06 把排程榨到極限之後，下一個問題是「同一張卡還能不能更快」。答案藏在三個武器裡：quantization 減少每個 token 要搬的 bytes、speculative decoding 讓每次搬運產出更多 token、kernel 優化把理論頻寬與算力真正用滿。三者全部建立在 ch02/ch03 的同一個物理事實上——decode 是 memory-bound。本章講原理、收益、代價與適用判斷；怎麼在 vLLM 上實際開這些開關是 ch08 的事，KV cache 自身的量化已在 ch05 講過。

## 從你已知的出發

這章的方法論你已經用了很多年。把 RDS CPU 尖峰降 40% 那次，你做的事情依序是：profiling 找瓶頸、改 SQL 減少不必要的工作量、把多次往返合併成批次、每改一步用數據驗證沒有改壞東西。本章三個武器跟那次優化一一對應，只是物件從資料庫換成 GPU：

- **Quantization ≈ 圖片服務把 PNG 換成 JPEG quality 85**。肉眼幾乎無損，頻寬與儲存省好幾倍——但「幾乎」兩個字是有任務相依性的：照片沒事，截圖裡的小字會糊。模型量化一模一樣：聊天沒事，數學與長推理先壞。你也碰過反向的版本：金額欄位絕不敢用 FLOAT 存——精度什麼時候能犧牲、什麼時候不能，本來就是工程判斷，不是數學定理。
- **Speculative decoding ≈ 樂觀鎖（optimistic concurrency control）**。悲觀鎖一步一停等；樂觀鎖先假設不衝突、大膽做完、提交時驗證、衝突就丟掉重做。你在 MySQL 上看過樂觀鎖的黑暗面：競爭一高，重試吃掉的資源比省下的還多，反而不如悲觀鎖。**speculative decoding 在高 batch 下收益變負，是同一個結構的故事**——這是本章最重要的反直覺重點，後面用數學講透。
- **CUDA graphs ≈ prepared statement**。每條 SQL 都重新 parse + plan 是浪費，prepare 一次、execute 一萬次才對。GPU 上每個 kernel launch 都有固定的 CPU 開銷，decode 每步要 launch 幾百個 kernel——graph capture 就是把整步「prepare」起來，之後一次 launch 重放。
- **FlashAttention ≈ 不要 materialize 那張中間結果表**。你重排過 SQL，讓資料庫不要把巨大的中間 JOIN 結果落地再讀回來。naive attention 會把 n² 的注意力矩陣寫進 HBM 再讀回來好幾趟，FlashAttention 的全部創新就是讓它從頭到尾不落地。

一張地圖把三個武器釘在同一個公式上。ch02/ch03 證明過，decode 每生成一個 token 的時間下限 ≈ 要搬的 bytes ÷ 記憶體頻寬：

```text
t_token ≈ (權重 bytes + KV bytes) / 有效頻寬

quantization          → 把分子變小（權重 bytes ÷2 ~ ÷4；KV 量化見 ch05）
speculative decoding  → 把分母變相變大（一次權重搬運產出 E 個 token）
kernels / CUDA graphs → 把「有效頻寬」推近理論值、消掉公式之外的 overhead
```

三者疊加順序有講究，章末給完整建議。先從最常用、收益最確定的開始。

## Quantization：精度是一種可以花的預算

### 原理：精度、動態範圍與 outlier

模型權重訓練完是 BF16/FP16，每個參數 2 bytes。量化就是用更少的 bits 表示同一組數字。難點不在「除以二」，在於兩個敵人：

**動態範圍 vs 解析度的取捨**。INT8 只有 256 個格子，必須配一個 scale 把浮點數映射到格子上：`q = round(x / scale)`。scale 由這組數字的最大絕對值決定——於是一個離群的大值（outlier）會把 scale 撐大，讓其他 99% 的正常值全擠在少數幾個格子裡，解析度崩潰。這就是 **outlier 問題**，量化文獻一半的篇幅都在跟它纏鬥。

LLM 的殘酷之處：權重的分布相對乖（鐘形、對稱），**activation 卻天生長 outlier**——研究發現大模型的 activation 有少數通道的數值比其他通道大上百倍，而且這些通道還很重要、不能砍。對策是把 scale 的粒度切細：per-tensor → per-channel → per-group（每 128 個權重共享一個 scale，GPTQ/AWQ 的標準做法），讓 outlier 只污染自己那一小組。

**浮點格式是另一條路**。FP8 E4M3 用 4 個 exponent bits 換來大動態範圍，格子在零附近密、遠處疏——剛好貼合權重和 activation 的分布形狀，天生比 INT8 抗 outlier。這是「FP8 幾乎免費」而 INT8 activation 量化需要 SmoothQuant 之類技巧搬運難度的根本原因。FP4 更極端：每個數只剩 16 個可能值，必須靠 microscaling（每 16~32 個元素一個高精度 scale）才能用——NVFP4（NVIDIA 私有，16 元素一個 FP8 scale）與 MXFP4（OCP 開放標準，32 元素一個 2 的冪次 scale）都是這個思路（2026-06）。

**Calibration**：大部分量化方法需要拿幾百條代表性樣本跑一遍模型，收集 activation 統計來決定 scales——GPTQ 進一步用二階資訊逐層補償量化誤差，AWQ 用 activation 大小找出「重要權重通道」加以保護。Murphy 提醒：calibration 集跟生產流量不像（用英文百科校準、上線跑中文程式碼），品質會在你的 eval 沒覆蓋的地方悄悄塌掉。

### Weight-only vs weight+activation：兩本不同的帳

這是量化決策的第一個分岔，搞混它會做出反向的選擇：

| | **W4A16（weight-only）**<br>GPTQ / AWQ INT4 | **W8A8（weight+activation）**<br>FP8 / INT8 |
|---|---|---|
| 權重存什麼 | INT4（0.5 bytes/參數） | FP8/INT8（1 byte/參數） |
| 計算用什麼 | 讀進來**反量化回 FP16 再算**，用的是 BF16 tensor core | **直接用 FP8/INT8 tensor core 算**，算力翻倍 |
| 省到哪本帳 | 容量 ÷4、權重頻寬 ÷4；**算力不省，還多付 dequant** | 容量 ÷2、頻寬 ÷2、**算力 ×2** |
| 受益場景 | memory-bound：低併發 decode、單卡裝大模型 | 全場景，尤其 compute-bound：prefill、高併發大 batch |
| 硬體需求 | 無特殊（Ampere 以上有高效 dequant kernel） | FP8 需 Hopper/Ada 以上；INT8 需 Turing 以上 |

關鍵洞察：**weight-only 量化的收益完全來自 memory-bound 的那一側**。batch 開大之後 decode 的算力佔比上升（ch06 算過），prefill 更是純 compute-bound——這時 W4A16 不但不加速，反量化的額外計算還會倒貼。ACL 2025 一份做了 50 萬次以上評測的系統性研究給出的結論與此一致：同步低併發場景 W4A16 最划算，高併發 continuous batching 場景 W8A8 全面勝出。

### 硬體支援對照（2026-06）

量化格式是硬體世代的函數，買錯卡開不了：

| 格式 | 最低硬體 | 2026-06 現況 |
|---|---|---|
| INT8 tensor core | Turing（2018）以上 | 到處都能跑，但 LLM 上已被 FP8 取代為主流 |
| INT4 weight-only（GPTQ/AWQ） | 無硬體要求（Ampere+ 有 Marlin 等高效 kernel） | 成熟，HF 上海量現成 checkpoint |
| FP8（E4M3/E5M2） | Hopper（H100）、Ada（L4/L40S）以上；AMD MI300 系亦支援 | **生產預設選項**，vLLM/SGLang/TRT-LLM 全面支援；DeepSeek 等旗艦直接用 FP8 訓練 |
| NVFP4 | Blackwell（B200/B300）專屬 | TensorRT-LLM 路徑最成熟，vLLM 支援 dense 與 MoE；NVIDIA 宣稱精度損失 <1%（廠商數字，依模型而異） |
| MXFP4 | OCP 開放格式，Blackwell 原生支援 | 代表作：gpt-oss 權重原生以 MXFP4 發布 |

表格的「最低硬體」指的是**原生 tensor core 計算**。weight-only 的 FP4 checkpoint 在更舊的卡上通常也跑得動——kernel 把 4-bit 權重讀進晶片後解壓回 BF16/FP8 再算（gpt-oss-120b 能塞進單張 H100 跑，走的就是這條路）。decode 是 memory-bound（ch02），權重縮小本身就賺到頻寬，解壓的算力開銷多半藏得進記憶體等待裡；要到 activation 也用 FP4、吃到算力那一份翻倍，才真的需要 Blackwell。

另一條平行宇宙是 **GGUF / llama.cpp 生態**：Q4_K_M、Q8_0 這些 K-quants 是為 CPU 與 Apple Silicon 設計的塊狀量化格式，跟上面的 GPU serving 棧是兩條血緣（定位見 ch08）。你的 M1 跑的就是這條線——本章動手做會用它親手驗證量化的 roofline 效應。

還有一個 2026 年的結構性轉變值得記住：**量化正在從「部署時的後處理」變成「訓練時的內建屬性」**。DeepSeek 用 FP8 訓練、gpt-oss 原生 MXFP4 發布、Kimi K2.6 原生 INT4（量化感知訓練，發布即 INT4，無 PTQ 損失）（2026-06）。對 infra 工程師的含意：拿到原生低精度 checkpoint 時，直接用官方格式，不要自作聰明再量化一次或「升回」FP16——官方格式就是品質基準本身。

### 品質評估：perplexity 不夠，免費午餐有邊界

量化論文最愛報 perplexity，但它對所有 token 取平均——少數關鍵 token 的錯誤（一步算錯的算術、一個寫反的條件判斷）會被海量無關緊要的 token 稀釋。生產決策必須用**任務型 eval**：數學（GSM8K 級以上）、程式碼、長上下文檢索、你自己業務的 golden set。

業界共識的退化順序（哪裡先壞）：**數學與多步推理最先**（誤差沿著自迴歸生成鏈逐 token 累積，鏈愈長放大愈狠——reasoning 模型的長思考鏈對量化最敏感）、**低資源語言其次**（calibration 語料多半是英文）、長尾知識與嚴格格式輸出再次；日常對話與摘要最耐操。截至我能確認的研究（2026-06）：FP8 W8A8 在 Llama 系列上「effectively lossless」、INT8 掉 1~3%、INT4 W4A16 平均上逼近 8-bit——但這些是平均數，你的尾部任務不在平均裡。

決策框架收斂成一張表：

| 你的情況 | 建議 | 代價 |
|---|---|---|
| Hopper/Ada 以上、通用流量 | **FP8 W8A8，直接上**（業界預設） | 接近零；仍要 eval gate |
| 卡數是硬約束（70B 想塞單卡） | INT4 W4A16（AWQ/GPTQ 現成 checkpoint） | 數學/推理品質風險，高 batch 吞吐打折 |
| Blackwell 卡、追極限密度 | 評估 NVFP4 | 工程還在快速演進期，eval 要做足 |
| 模型有官方低精度版（K2.6 INT4、gpt-oss MXFP4） | 用官方 checkpoint | 幾乎沒有，這是送分題 |
| 品質敏感業務（數學、法律、程式碼生成核心路徑） | FP8 為底線，INT4 需逐任務驗證 | 多花卡錢買確定性 |
| M1 / 邊緣 | GGUF Q4_K_M 起跳 | 本地玩具線，決策邏輯相同 |

## Worked example：70B 的三種精度，一張完整對照表

把 ch02 的 roofline 方法完整接過來，算 Llama-3.3-70B（70.6B 參數，dense）在 H100 SXM（80 GB、3.35 TB/s）上的三種精度。引擎可用記憶體 = 80 × 0.9（`gpu-memory-utilization`，ch06）= 72 GB/卡，每卡再保留約 4 GB 給 activation 工作區與 CUDA graphs。

**Step 1：權重記憶體。** 70.6B × bytes/參數：FP16 = **141.2 GB**、FP8 = **70.6 GB**、INT4 = **35.3 GB**。

**Step 2：卡數——「裝得下」不等於「跑得動」。** 這步藏著本例最重要的陷阱：

- **FP16**：141.2 GB > 72 GB，至少要切兩張。但 TP2 時每卡權重 70.6 GB，KV 池 = 72 − 70.6 − 4 < 0——**權重裝得下，KV 池歸零，一條請求都服務不了**。實務最低是 **TP4**：每卡 35.3 GB 權重，全機 KV 池 ≈ 4 × (72 − 35.3 − 4) ≈ **131 GB**。
- **FP8**：70.6 GB < 72 GB，單卡「裝得下」——但 KV 池同樣歸零（ch02 算 47 tok/s 那次只算了頻寬帳，這裡補上容量帳）。實務是 **TP2**（KV 池 ≈ 65 GB）或單卡 H200（ch05 的 worked example 就是這個配置）。
- **INT4**：35.3 GB，**單卡成立**，KV 池 ≈ 72 − 35.3 − 4 ≈ **33 GB**。

**Step 3：理論 decode 上限（batch=1，只算權重流量，ch02 方法）。** TP 的聚合頻寬 = 卡數 × 3.35 TB/s（忽略卡間通訊，實際更低，見 ch09）：

- FP16 TP4：13.4 TB/s ÷ 141.2 GB ≈ **95 tok/s**
- FP8 TP2：6.7 TB/s ÷ 70.6 GB ≈ **95 tok/s**
- INT4 單卡：3.35 TB/s ÷ 35.3 GB ≈ **95 tok/s**

三個配置殊途同歸。這不是巧合：bytes 和頻寬同比例縮放，比值不變。**結論值得默寫：quantization 在 batch=1 買不到更快的單請求速度——它買的是密度，同樣的速度用 1/4 的卡達成。**

**Step 4：品質與算力面。** FP8 的 tensor core 算力是 BF16 的兩倍（1,979 vs 989 TFLOPS）→ prefill 也加速、TTFT 受益；INT4 W4A16 用 BF16 算力再付 dequant 稅 → prefill 持平甚至略慢。

完整對照表：

| | FP16/BF16 | FP8（W8A8） | INT4（W4A16） |
|---|---|---|---|
| 權重記憶體 | 141.2 GB | 70.6 GB | 35.3 GB |
| 最少可行配置 | **4×H100（TP4）** | **2×H100（TP2）**或 1×H200 | **1×H100** |
| 全機 KV 池（約） | 131 GB | 65 GB | 33 GB |
| batch=1 理論 decode 上限 | ≈95 tok/s | ≈95 tok/s | ≈95 tok/s |
| prefill 算力 | 989 TFLOPS ×4 卡 | 1,979 TFLOPS ×2 卡 | 989 TFLOPS ×1 卡＋dequant 稅 |
| 品質風險 | 基準 | 幾乎無損（研究與業界共識，2026-06） | 平均近 8-bit，但數學/長推理/小語種先壞，需任務型 eval |
| 租金（H100 約 $2~3/hr 級距，2026 年中快照） | ~$8–12/hr | ~$4–6/hr | ~$2–3/hr |

三個讀法：

1. **同樣的單請求速度，4:2:1 的月帳單**——這就是「LLM serving 是 memory 的生意」在成本表上的長相。
2. **但併發容量不是 4:2:1**。FP16 TP4 的 KV 池有 131 GB，INT4 單卡只有 33 GB——拿 ch03 的數字（32k context ≈ 10.7 GB/條），前者同時服務 12 條長對話，後者 3 條。如果你的瓶頸是併發而非密度，比較該用「每美元的 goodput」而不是每美元的卡（ch13/ch16 接手這本帳）。
3. **高併發吞吐場景，FP8 幾乎全面優於 INT4**：算力翻倍、無 dequant 稅、品質風險低一級。INT4 的主場是「卡數受限」與「低併發 latency-bound」。

## Speculative decoding：用閒置的算力換 token

### 機制：draft–verify

decode 的荒謬之處 ch02 算過：batch=1 時搬 70 GB 權重只為了算 2 FLOP/byte，tensor core 利用率 0.3%。算力大量閒置——speculative decoding 就是把這些閒置算力變現的方法。

兩個角色：**draft**（便宜的猜測者）一口氣猜 γ 個 token；**target**（你真正要服務的模型）用**一次** forward 同時驗證這 γ 個位置——這一步像個迷你 prefill，γ 個 token 平行計算，權重只搬一輪。逐位置比較 draft 與 target 的機率分布，用 rejection sampling 決定接受到第幾個；被拒絕的位置由 target 的分布重新抽樣補上一個正確 token，全部接受則再白拿一個 bonus token。

```text
一般 decode：每搬一輪 70 GB 權重 → 產出 1 個 token
  [target]→t1  [target]→t2  [target]→t3  [target]→t4

speculative（γ=4）：每搬一輪權重 → 產出 1~5 個 token
  [draft×4]→ d1 d2 d3 d4
  [target 驗證 5 個位置（一次 forward）]→ 接受 d1 d2 d3、拒絕 d4、補發 t4
  → 這一步淨產出 4 個 token，權重只搬了一輪
```

數學上有個漂亮的保證：rejection sampling 讓輸出分布**與 target 單獨生成完全相同**——這不是「近似加速」，是無損加速（工程上仍受浮點不可結合性影響，見 ch03）。它沒有違反 ch03 「自迴歸必須一個一個生成」的鐵律，而是繞過它：順序性留給便宜的 draft，昂貴的 target 只做可平行的驗證。

### Acceptance rate 的數學

設每個 draft token 被接受的機率為 α（簡化為獨立同分布），一次猜 γ 個。一步「draft + 驗證」的期望產出：

```text
E[每次驗證產出的 token 數] = (1 − α^(γ+1)) / (1 − α)
```

（推導：接受前 i 個、第 i+1 個被拒的機率是 αⁱ(1−α)，產出 i+1 個；全收機率 α^γ，產出 γ+1 個。求和即得。）把數字攤開：

| α \ γ | 2 | 4 | 8 | 極限 1/(1−α) |
|---:|---:|---:|---:|---:|
| 0.6 | 1.96 | 2.31 | 2.47 | 2.5 |
| 0.7 | 2.19 | 2.77 | 3.20 | 3.33 |
| 0.8 | 2.44 | 3.36 | 4.33 | 5.0 |
| 0.9 | 2.71 | 4.10 | 6.13 | 10.0 |

兩個結構性結論。第一，**γ 有飽和點**：E 的上限是 1/(1−α)，γ 拉大收益快速遞減（第 i 個猜測活到驗證的機率是 αⁱ，指數衰減），但成本線性上升——γ 超過 4~8 幾乎都是浪費。第二，**α 是一切**：α 從 0.6 拉到 0.9，極限收益從 2.5 翻到 10。整個領域的演化史就是把 α 推高的歷史。

端到端加速比（低 batch、memory-bound 時）：`S ≈ E / (γ·c + 1)`，c 是 draft 與 target 的單步耗時比。α=0.8、γ=4、c=0.05（EAGLE 級輕量 draft）：S = 3.36 / 1.2 = **2.8×**——與公開實測的 2~2.5× 量級吻合。

### 方案光譜：把 α 推高的四代演化（2026-06）

| 方案 | draft 從哪來 | 成本 | 特性 |
|---|---|---|---|
| **n-gram / prompt lookup** | 從 context 裡找重複 n-gram 接龍，零模型 | ≈0 | α 看流量吃飯：RAG 引用、文件改寫、code edit 這類高複製率流量 α 極高，自由生成則趨近 0。免費，先試它 |
| **獨立小模型** | 同家族小模型（70B 配 1B） | 要部署、要記憶體，詞表必須相容 | 經典做法（2023），α 中等，運維兩個模型，漸被取代 |
| **EAGLE-3 / 3.1** | 接在 target hidden states 上的輕量自迴歸 head，樹狀多分支猜測 | c 極小；要訓練（SpecForge/TorchSpec 生態） | 2026 年 draft-based 的主流。EAGLE-3 學術基準報 4~6×，真實流量約 2×；EAGLE 3.1（2026-05）修長序列的 attention drift |
| **MTP（multi-token prediction）** | 模型自帶：訓練時就多一個預測下下個 token 的 head，隨權重發布 | 零額外整合 | DeepSeek 開的路（V3 報告：第二 token 接受率 85~90%）；γ=1 但 α 極高，大規模 serving 存活力最強，2026 年旗艦開源模型的標配 |

（Medusa 等多平行 head 的方案是 2024 年的過渡型，已被 EAGLE 系取代，一句話帶過。）vLLM 對 n-gram、EAGLE-3、MTP 都有支援，SGLang 的 Speculative Decoding V2 已預設開啟（2026-06；參數操作見 ch08）。

### 反直覺重點：高 batch 下收益遞減，甚至為負

這是本章必須講透的一段，因為它推翻「加速技術疊上去總是更快」的直覺，也是面試的高頻陷阱題。

**直覺版**：speculative decoding 的收益是用**閒置算力**買的。但 ch06 講過，batching 也是在用同一口井——把更多請求的 token 塞進同一輪權重搬運，本質上同樣是把 memory-bound 的閒置算力變現。低 batch 時井是滿的，spec decode 白拿；高 batch 時井已經被 batching 抽乾，spec decode 再伸手，搶的就是其他請求的算力。樂觀鎖在高競爭下輸給悲觀鎖，一模一樣的結構。

**Roofline 版**：batch B 的一個普通 decode 步，記憶體流量 ≈ 權重 + B 份 KV，計算量 ≈ 2P·B。開了 γ 步猜測的驗證步呢？計算量變成 **2P·B·(γ+1)**（每條請求驗 γ+1 個位置），記憶體流量卻幾乎不變（權重照樣搬一輪，KV 讀取由 γ+1 個 query 共享）。等效於把 arithmetic intensity 乘上 (γ+1)——**你會比原本提早 (γ+1) 倍撞上 roofline 的 compute 屋頂**。

**極限數學**：當系統徹底 compute-bound，每步耗時正比於處理的 token 數。普通 decode 每單位算力產出 1 個 token；spec decode 花 (γ+1) 個 token 的算力產出 E 個。吞吐比：

```text
compute-bound 極限下：spec decode 吞吐 / baseline 吞吐 = E / (γ+1) ≤ 1
（等號只在 α=1 成立）
```

代入數字，殘酷得很直白：

| 配置 | E | E/(γ+1) | 高 batch 極限下的吞吐變化 |
|---|---:|---:|---|
| α=0.7、γ=4（典型獨立 draft） | 2.77 | 0.55 | **−45%** |
| α=0.8、γ=4（不錯的 EAGLE） | 3.36 | 0.67 | −33% |
| α=0.9、γ=2 | 2.71 | 0.90 | −10% |
| α=0.85、γ=1（MTP） | 1.85 | 0.93 | −7% |

每一個被拒絕的 token 都是付了全價算力的廢品。低 batch 時廢品免費（反正算力閒著），高 batch 時每件廢品都排擠一個別人的正經 token。看出 MTP 的設計智慧了嗎：γ=1、α 極高，把「最壞情況的浪費」壓到 7%——**這是 γ=1 方案在大規模 serving 中存活力最強的數學原因**。也看出為什麼把 γ 開大是高併發下的自殺：γ=8 在低 batch 的表上很美，在這張表上是災難。

**實證對齊**（2026-06）：vLLM 官方 blog 的 EAGLE 3.1 on Kimi K2.6 數據——單使用者 2.03×、4 併發掉到 1.71×、16 併發 1.66×，單調遞減；學術側的系統性測量（如《Batch Speculative Decoding Done Right》《Speculative Decoding: Performance or Illusion?》）更直接量到生產引擎在高 batch 下 spec decode **低於不開的 baseline**。廠商展示永遠用 batch=1 跑分，你的生產環境不是 batch=1——這句話值得貼在牆上。

**一個重要例外（長 context）**：上面的推導假設高 batch 必然走向 compute-bound，但 ch03 講過，長 context 下 KV 讀取主宰流量、且隨 B 線性增長——系統**停留在 memory-bound**，每步的固定成本從「權重」變成「權重+大量 KV」，而驗證步照樣把這筆固定成本攤提給 E 個 token。MagicDec（2024）正是抓住這點：只要 draft 自己不付完整 KV 帳（用 sparse/截斷 KV 的 draft），長序列場景在 batch 32~256 仍量到最高 2.5× 加速。所以精確的判斷準則不是「batch 大就關」，而是：**驗證步是否 compute-bound**。

最後一個容易踩的觀測坑：spec decode 讓 token 以「一坨一坨」的節奏到達（每次驗證吐出 1~γ+1 個），平均 ITL 變好但分布變成多峰——benchmark 工具與 SLO 定義要意識到這件事（ch14）。

### 決策框架：什麼流量才划算

| 流量形態 | 建議 | 原因 |
|---|---|---|
| 低併發、latency 敏感（內部工具、code completion、付費低延遲 tier） | **開**，EAGLE-3/MTP，γ=2~4 | 算力大量閒置，2× 級收益接近免費 |
| RAG / 文件改寫 / code edit（輸出大量複製輸入） | 先試 **n-gram**，零成本 | 高複製率流量 α 天然高，不用訓練任何東西 |
| 高併發吞吐型（batch 常態 >64、短 context） | **關**，或只留 MTP（γ=1） | 驗證步 compute-bound，E/(γ+1) 數學直接判死刑 |
| 長 context 重的高併發（agentic、長文件） | 量測後再說：KV-bound 時仍可能划算 | MagicDec 機制；以「驗證步是否 compute-bound」為準 |
| 模型自帶 MTP head（DeepSeek/Kimi 系） | 預設開著，監控 acceptance | 官方訓練的 head，α 有保證，整合成本為零 |

橫切所有場景的紀律：**監控 acceptance rate**（vLLM 有對應 metrics，ch14）。α 是流量分布的函數——draft 用英文 chat 訓練、流量轉成中文程式碼，α 無聲下滑，吞吐悄悄退化，沒有任何錯誤碼。

## Attention kernels：把理論頻寬真正用出來

### FlashAttention：IO-aware 的意義

前兩個武器改的是「要做多少工作」；kernel 優化改的是「做同樣的工作要搬多少次記憶體」。最好的教材就是 attention。

naive attention 的帳：算 S = QK^T 得到 n×n 矩陣，**寫進 HBM**；讀回來做 softmax，**再寫回去**；再讀回來乘 V。對 8k 序列、64 heads 的一層：8192² × 2 bytes × 64 ≈ **8.6 GB 的中間結果**——單一序列、單一層！這些流量在數學上完全不必要，純粹是實作偷懶的代價，而且它讓 attention 在 prefill 階段也變成 memory-bound——明明 roofline 上它該是 compute-bound。

FlashAttention（2022）的全部創新一句話：**把 Q/K/V 切成小塊裝進 SM 的 shared memory，用 online softmax 邊算邊歸一化，n² 矩陣從頭到尾不落地 HBM**。這就是 IO-aware 的意思——演算法複雜度沒變（還是 O(n²) FLOPs），變的是記憶體階層之間的往返次數。你對這個套路不陌生：把計算推進資料旁邊做、不要 materialize 中間結果表，資料庫優化器三十年前就在做同一件事。

注意收益的不對稱：**FlashAttention 主要救 prefill**。decode 的 attention 每步只有一個 query token，沒有 n² 矩陣可省，瓶頸是讀 KV 本身——那是「必要流量」，kernel 救不掉（能救它的是 GQA/MLA 這類架構手段與 KV 量化，見 ch03/ch05）。decode 端的對應優化是 FlashDecoding 一類的 split-KV 技巧：把一條長 KV 切段平行處理，解決「batch 小、context 長」時 GPU 佔用不足的問題。

世代演進緊貼硬體（這正是 kernel 工程的本質）：FA-2（2023）重做平行化與 work partitioning，約 2× 於初代；FA-3（2024）綁定 Hopper 的 TMA 與 warp specialization，H100 上再快 1.5~2×，並支援 FP8；Blackwell 世代有對應的新版本（截至我能確認的資訊（2026-06），vLLM 在 Hopper 上預設 FA-3、Blackwell 上有 FA-4 與 TRT-LLM/FlashInfer kernel 等多後端並存）。**kernel 是貼著特定硬體的記憶體階層手寫的**，換一代卡就要重寫一次——這也是它值錢的原因。

### FlashInfer 與 kernel fusion

**FlashInfer** 解的是另一個層次的問題：FlashAttention 是「一個極致的 kernel」，FlashInfer 是「為 LLM serving 設計的 kernel 庫」——原生理解 paged KV（直接吃 ch05 的 block layout）、ragged batch（ch06 裡每條請求長度不一的現實）、JIT 按模型形狀特化 kernel，還覆蓋 MLA、sampling 等周邊。它拿了 MLSys 2025 的最佳論文，NVIDIA 深度投入，是 vLLM 在新硬體上的重要 attention backend（2026-06）。一句話定位：FlashAttention 證明了 IO-aware 能做到什麼，FlashInfer 把這件事工程化成 serving 的基礎設施。

**Kernel fusion** 是同一個思想的小規模版本：transformer 每層有一串小操作（RMSNorm、殘差相加、SiLU×gate……），每個若是獨立 kernel，中間 activation 就要寫出 HBM 再讀回。把相鄰操作融成一個 kernel，中間值留在 register/SMEM——每融一次省一來一回的 HBM 流量加一次 launch。手寫 fusion 是體力活，所以交給編譯器：torch.compile 自動做這類融合並生成 Triton kernel（下節）。

你大概永遠不會手寫這些 kernel，但作為 infra 工程師有三件實務責任：(1) 啟動時**確認引擎選到了對的 backend**（啟動日誌會印，選錯或 fallback 到通用路徑可能慢 2 倍而不報任何錯）；(2) 看懂「某 backend 不支援某格式/某卡 → 靜默 fallback」這類效能懸崖；(3) 維護 FlashInfer/CUDA/PyTorch/driver 的版本相容矩陣——這是 ch04 說過的、你真正會碰到 CUDA 生態的方式。

## CUDA Graphs 與 torch.compile：消掉 launch overhead

最後一個武器處理的是公式之外的開銷。一個 decode step 要 launch 幾百個 kernel，每次 launch 有微秒級的 CPU 端固定成本（構造參數、提交佇列）。70B 模型一步幾十 ms，這點開銷是噪音；但 8B 模型一步 5~6 ms（ch06 的曲線），幾百個 launch 的 CPU 時間就能跟 GPU 計算時間同量級——**GPU 開始空轉等 CPU 餵活**。症狀很有辨識度：nvidia-smi 利用率反而不高、ITL 比 roofline 推算高出一截、CPU 單核吃滿。模型越小、卡越快，這個問題越尖銳——這正是「小模型放 H100 上跑不滿」的常見原因之一。

**CUDA Graphs** 的解法就是 prepared statement：第一次把整步的幾百個 kernel 與依賴關係 capture 成一張圖，之後每步一次 launch 重放整圖，CPU 成本從「幾百次」攤平成「一次」。代價是三個約束，每個都會在生產咬人：

1. **形狀必須固定**。graph 是按確切的 batch size/序列佈局錄製的，所以引擎按 bucket capture（batch 1、2、4、8……），實際 batch 向上 padding 到最近的 bucket。bucket 沒覆蓋到的形狀 fallback 回逐 kernel 執行——「為什麼 batch 在某個區間 ITL 突然高一截」的標準答案。
2. **吃記憶體**。每張 capture 的圖都佔 HBM，這就是 ch06 提醒 `gpu-memory-utilization` 別開太貪的原因之一。
3. **吃啟動時間**。capture 在引擎啟動時做，是 cold start 帳單裡的一段（ch12 會完整解剖）。

**torch.compile** 在推論引擎裡扮演的角色是 CUDA Graphs 的搭檔而非替代：它負責圖層級的 kernel fusion 與程式碼生成（產出 Triton kernels），graphs 負責消 launch。vLLM V1 的預設形態是兩者的組合——torch.compile 編譯模型，配 **piecewise CUDA graphs**：把 attention 留在圖外（paged attention 的動態記憶體存取與圖的靜態性合不來），其餘部分 graph 化，兼顧收益與彈性；SGLang 自 0.5.10 起同樣以 piecewise 為預設（2026-06）。對你的含意：這些是引擎預設，你的工作不是「開啟」它們，而是**確認它們沒有因為某個參數組合而靜默失效**，以及在小模型場景知道往這裡查。

## 優化疊加的順序：一條務實的路徑

三個武器講完，最後的問題是順序。原則跟你做 RDS 優化時一字不差：**一次動一個變數，每步用數據驗證速度與品質，可回滾**。具體建議：

```text
Step 0  量測 baseline（ch14 方法論）：
        latency-throughput 曲線、MBU/MFU、確認瓶頸（roofline，ch02）
Step 1  確認免費項沒漏：attention backend 選對了嗎？CUDA graphs 生效了嗎？
        prefix caching 開了嗎（ch05）？——預設不是優化，但「預設失效」是負優化
Step 2  FP8（Hopper/Ada 以上）：容量、頻寬、算力三贏，品質風險最低
        → 跑任務型 eval gate，過了才算數
Step 3  還缺容量才上 INT4（或直接用官方原生低精度 checkpoint）
        → 高併發場景先 benchmark dequant 稅；eval 加測數學/推理
Step 4  最後才是 speculative decoding，而且只在流量形態合適時：
        低併發/latency-bound/高複製率 → 開；高併發 compute-bound → 關或僅 MTP
        → 監控 acceptance rate 與 goodput，不是只看 demo 的 batch=1 數字
```

為什麼是這個順序：**收益確定性遞減、風險遞增、且後面的步驟依賴前面的狀態**。最後一點最容易被忽略——量化會改變 target 的輸出分布，你的 EAGLE draft 是對著 BF16 的 target 訓練的，target 換成 INT4 之後 α 會掉；先定精度、再配 draft，順序反了就要返工。也別忘了每一步的交互：FP8 權重與 FP8 KV（ch05）是兩個獨立開關、spec decode 與 chunked prefill 共享 token budget（ch06）——疊加不是免費的線性加法。

## 故障模式與防禦

| 故障 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| 量化品質退化 | **零錯誤碼**，使用者說「變笨了」；數學/程式碼任務先壞 | 任務型 eval 基線對比；業務指標（重答率、人工升級率） | eval gate 進發布流程（ch15）；calibration 集對齊生產流量；敏感任務 FP8 底線 |
| 量化反而變慢 | 上了 INT4 吞吐不升反降 | 高併發 benchmark 對比；profiler 看 dequant kernel 佔比 | 理解 W4A16 vs W8A8 的帳；換格式前後各跑一條 latency-throughput 曲線 |
| 硬體不支援的格式 | 引擎 fallback 到模擬路徑或直接起不來 | 啟動日誌；同 config 在不同卡型上效能差數倍 | 部署前查硬體支援矩陣（FP8 需 Hopper/Ada+、NVFP4 需 Blackwell） |
| acceptance rate 漂移 | 吞吐數週內悄悄下滑，無任何錯誤 | spec decode acceptance metrics 趨勢；分流量類型看 α | 流量畫像變更（新語言/新任務）時重評 draft；告警掛在 α 上 |
| spec decode 高峰負收益 | 尖峰時段開著 spec decode 的池子 goodput 反而低 | 對比實驗：同流量開/關 spec decode 的 goodput | 高併發池關閉或僅 MTP；理解 E/(γ+1) 的數學再做容量規劃 |
| draft/target 版本錯配 | 換了 target 模型沒換 draft，α 崩到接近 0，ITL 暴增 | 部署後 α 驟降 | 部署清單把 draft 與 target 綁成同一個 artifact 版本 |
| CUDA graph bucket 失配 / capture 失敗 | 特定 batch 區間 ITL 跳高；或啟動時 OOM | ITL 按 batch size 切片；啟動日誌的 capture 清單 | 留記憶體餘裕；壓測覆蓋真實 batch 分布；升級引擎後重跑效能回歸 |
| kernel backend 靜默 fallback | 升級 CUDA/PyTorch 後整體慢 1.5~2 倍，無錯誤 | 啟動日誌 grep backend 名稱；版本升級前後 benchmark | 把「backend 斷言」寫進部署 smoke test；維護版本相容矩陣 |

共同主題你應該已經看出來了：**這一章的故障幾乎全是靜默的**。沒有 5xx、沒有 exception，只有變慢和變笨。防禦手段也因此高度一致——基線、對比、回歸測試，全是你在效能工程裡用了多年的紀律，只是把「壓測報告」換成「eval + benchmark 雙基線」。

## 動手做

### Lab 7-1 [M1]：用 llama.cpp 親手驗證量化的 roofline 效應

1. 下載同一個 8B 級模型的 Q4_K_M 與 Q8_0 兩種 GGUF（如 Hugging Face 上的 Qwen 或 Llama 系 GGUF 倉庫）。
2. 跑 `llama-bench -m model-Q8_0.gguf -m model-Q4_K_M.gguf -p 512 -n 128`，分別記錄 pp（prefill）與 tg（decode）速度。
3. 對兩個版本各丟 5 題小學數學應用題與 5 題常識問答，肉眼對比品質。

**成功標準**：tg（decode）速度比 ≈ 檔案大小的反比（Q4 約為 Q8 的 1.7~2 倍），而 pp（prefill）差距明顯小——你剛親手證明了「量化加速的是 memory-bound 的部分」；同時在數學題上觀察到 Q4 的錯誤率肉眼可見地高於 Q8（樣本小，僅作直覺校準）。

### Lab 7-2 [M1]：體驗 speculative decoding（示意）

llama.cpp 內建 speculative 工具（binary 名稱隨版本變動，以 `llama.cpp` 當前文件為準）：用同家族的小模型當 draft（如 0.5B 配 7B），對兩種 prompt 各跑一次——「逐字複述以下文章並修正錯字」（高複製率）vs「寫一首原創詩」（自由生成），對比輸出的 accepted 統計與 tok/s。

**成功標準**：複述任務的 acceptance 與加速顯著高於自由生成——α 是流量的函數，不是模型的常數。

### Lab 7-3 [租 GPU，估 $5–8]：vLLM 上 FP8 vs BF16 的誠實對比

1. 租一張 H100 或 L40S（FP8 需 Hopper/Ada 以上），起 vLLM 跑 8B 模型 BF16 baseline，用 `vllm bench serve` 量 latency-throughput 曲線。
2. 同模型換 FP8（可用線上動態量化或 llm-compressor 預量化 checkpoint），重跑同一條曲線。
3. 用 lm-eval 跑一個小型數學子集（如 GSM8K 取樣 200 題），對比兩版分數。
4. 用完即關機（成本紀律，ch08 有完整 checklist）。

**成功標準**：拿到兩條可疊放的曲線與一組 eval 分數，能用一段話回答「FP8 在我的 workload 上換到了什麼、付出了什麼」——這個「曲線+eval 雙證據」的格式就是你以後在生產做任何優化決策的模板。

### Lab 7-4 [紙上推演]：acceptance rate 與高 batch 的判決

給定 α=0.75、γ∈{1,2,4,8}：(1) 算出各 γ 的 E 與低 batch 加速比（c=0.05）；(2) 算出 compute-bound 極限下的吞吐比 E/(γ+1)；(3) 對兩種服務做出開/關與 γ 的選擇並辯護：a) 內部 code review 工具，併發 <4；b) 對外 API，尖峰 batch 128、平均 context 1k。

**成功標準**：a 選 γ=4 上下、b 選關閉（或論證 MTP γ=1 的邊際合理性）；能說出 b 如果平均 context 是 64k 答案為什麼可能反轉。

## 這個領域往哪走

短期 1~3 年的三條線。**量化收斂進訓練**：旗艦模型原生低精度發布（FP8 訓練、INT4 QAT、MXFP4）會讓「部署團隊自己做 PTQ」逐漸變成只有長尾模型才需要的技能，infra 端的工作從「怎麼量化」轉成「怎麼驗證與服務官方低精度格式」。**Speculative decoding 標準化**：MTP head 隨模型發布已成旗艦標配，draft 的訓練與分發（SpecForge/TorchSpec 生態）平台化，動態開關（按池子負載自動調 γ 甚至關閉）會進引擎排程器——你在本章學的 E/(γ+1) 數學正是那個自動決策的內核。**Kernel 自動化**：torch.compile、FlashInfer JIT、各家 DSL 持續壓縮手寫 kernel 的領域，但「會讀 roofline、會判斷 backend 對不對」的診斷能力反而更值錢——工具會生成 kernel，不會替你發現它 fallback 了。

## 自我檢核

1. Weight-only（W4A16）與 weight+activation（W8A8）各省哪幾本帳（容量/頻寬/算力）？為什麼高併發吞吐場景 W4A16 可能反而比 W8A8 慢？
2. Outlier 為什麼是 INT 量化的核心難題？per-group scaling 和 FP8 的格式設計分別從什麼角度緩解它？
3. 默寫 E = (1−α^(γ+1))/(1−α)，心算 α=0.8、γ=4 的期望產出；解釋為什麼 γ 拉大收益會飽和。
4. 用 roofline 語言完整解釋「spec decode 高 batch 負收益」：驗證步對 compute 與 memory 流量各做了什麼？compute-bound 極限下的吞吐比公式是什麼？什麼條件下這個結論會反轉？
5. 70B 模型 FP8 在單張 H100 上「裝得下」，為什麼仍然不可部署？這個檢查在容量規劃裡叫什麼帳？
6. FlashAttention 的 IO-aware 是什麼意思？為什麼它對 prefill 的收益遠大於 decode？decode 的記憶體瓶頸要靠什麼層級的手段解？
7. CUDA Graphs 解什麼問題、為什麼要求靜態形狀、piecewise capture 在妥協什麼？什麼樣的模型/硬體組合最需要它？
8. 你接手一個 70B 服務，p95 ITL 超標 30%、GPU 是 2×H100、batch 常態 8~16：說出你的優化順序與每步的驗證方法。

## 延伸閱讀

- [GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers](https://arxiv.org/abs/2210.17323) — weight-only 量化的奠基論文，理解「逐層誤差補償」的原始出處。
- [AWQ: Activation-aware Weight Quantization](https://arxiv.org/abs/2306.00978)（MLSys 2024 最佳論文）— 「保護 1% 重要權重」的思路，是目前 INT4 checkpoint 的主流做法。
- ["Give Me BF16 or Give Me Death"? Accuracy-Performance Trade-Offs in LLM Quantization](https://arxiv.org/abs/2411.02355)（ACL 2025）— 50 萬次評測撐起來的量化品質實證，本章「FP8 幾乎無損、W4A16 vs W8A8 場景劃分」的數據來源。
- [Fast Inference from Transformers via Speculative Decoding（Leviathan et al., ICML 2023）](https://arxiv.org/abs/2211.17192) — spec decode 與 rejection sampling 無損性證明的原典，acceptance rate 數學的出處。
- [EAGLE-3: Scaling up Inference Acceleration of Large Language Models](https://arxiv.org/abs/2503.01840) — 2026 年 draft-based 方案主流的技術細節。
- [EAGLE 3.1（vLLM blog, 2026-05）](https://vllm.ai/blog/2026-05-26-eagle-3-1) — 本章引用的 Kimi K2.6 併發遞減數據（2.03×→1.66×）出處，順帶展示 draft 訓練生態的現況。
- [MagicDec: Breaking the Latency-Throughput Tradeoff for Long Context Generation](https://arxiv.org/abs/2408.11049) — 「長 context 下高 batch spec decode 仍划算」這個例外的完整論證。
- [FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness](https://arxiv.org/abs/2205.14135) — IO-aware 思想的原典；讀完它你會用全新的眼光看所有 kernel。
- [FlashInfer: Efficient and Customizable Attention Engine for LLM Inference Serving](https://arxiv.org/abs/2501.01005)（MLSys 2025 最佳論文）— serving 場景 kernel 庫的設計空間，paged/ragged KV 的 kernel 層視角。
- [Introducing NVFP4（NVIDIA Developer Blog）](https://developer.nvidia.com/blog/introducing-nvfp4-for-efficient-and-accurate-low-precision-inference/) — Blackwell 世代 FP4 格式的官方說明（廠商視角，數字自行折扣）。
- [llm-compressor（vLLM project）](https://github.com/vllm-project/llm-compressor) — 自己動手做 FP8/INT4 量化 checkpoint 的標準工具，Lab 7-3 的進階路徑。
- [Accelerating PyTorch with CUDA Graphs（PyTorch blog）](https://pytorch.org/blog/accelerating-pytorch-with-cuda-graphs/) — CUDA Graphs 機制與限制最好讀的官方解說。
