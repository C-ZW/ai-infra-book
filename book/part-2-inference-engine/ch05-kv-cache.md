# ch05 — KV Cache 管理：推論引擎的記憶體子系統

> **本章解決什麼問題**：ch03 推導過 KV cache 的數學——它是推論狀態的本體，而且大得驚人（Llama-3.3-70B 每個 token 約 320 KB）。本章回答下一個問題：這塊記憶體在引擎裡到底怎麼管。PagedAttention 解決配置浪費、prefix caching 把重複的 prefill 變成查表、FP8 KV 把每 byte 榨出兩倍容量、分層 offloading 把快取延伸到 HBM 之外。這是現代推論引擎最核心的工程創新所在，也直接餵養後面的章節：ch06 的排程器搶的就是這塊記憶體，ch10 的路由器追的就是這份快取，ch13 的 autoscaler 看的就是它的利用率。

## 從你已知的出發

你管理過三種記憶體系統，這一章只是把它們搬到 GPU 上重演一遍：

- **OS virtual memory paging**。你知道 process 看到的是連續的虛擬位址空間，實體記憶體卻是離散的 page frame，中間靠 page table 翻譯。PagedAttention 就是把這套機制原封不動抄給 KV cache：請求看到「邏輯上連續的 token 序列」，實體 HBM 上是散落的固定大小 block，中間有一張 block table。連 copy-on-write 都抄過來了。這個類比會貫穿全章。
- **InnoDB buffer pool 與 Redis**。你調過 buffer pool 大小、看過 Redis 的 `maxmemory-policy allkeys-lru` 在記憶體吃緊時逐出冷資料。Prefix caching 的世界完全一樣：一個固定大小的快取池、一個 LRU 逐出策略、一個決定生死的指標叫命中率。差別只在這裡的「一筆快取」動輒幾百 MB，而且 miss 的代價不是一次 disk read，是幾秒鐘的 GPU 滿載重算。
- **分層儲存**。你設計過「熱資料在 Redis、溫資料在 RDS、冷資料在 S3」的階層。KV offloading 是同一張圖：熱 KV 在 HBM（TB/s 級）、溫 KV 在 CPU RAM（PCIe，幾十 GB/s）、冷 KV 在 NVMe 或遠端儲存。每往下一層，容量乘一個數量級、頻寬除一個數量級。

一個你需要先翻轉的直覺：在後端世界，快取是「錦上添花」——cache miss 了不過是慢一點。在 2026 年的 LLM serving 裡，KV cache 的管理品質直接決定一張卡能服務幾個使用者、TTFT 是 0.1 秒還是 2 秒、每百萬 token 的成本差幾倍。這呼應全書第一條主軸：**LLM serving 本質上是 memory 的生意**。

## 問題定義：naive 配置會浪費 60–80% 的記憶體

先回顧 ch03 的結論：KV cache 隨 context 線性成長，每個 token 的大小由模型結構決定（2 × layers × kv_heads × head_dim × bytes）。對 Llama-3.3-70B（GQA，80 層、8 個 KV head、head_dim 128、FP16）是每 token 約 320 KB；一條 32k context 的對話約 10.5 GB（見 ch03，全書反覆引用這組數字）。

vLLM 之前的服務系統（FasterTransformer、Orca 世代）怎麼放這塊記憶體？最直觀的做法：**每個請求預先配置一塊連續的記憶體，大小按可能的最大長度算**。你一眼就能看出這會發生什麼——這正是「每個連線預先 malloc 最大 buffer」的老問題，只是單位從 KB 變成 GB。具體有三種浪費：

1. **預留浪費（reservation）**：請求最終會長到多長，事先不知道，所以按 `max_seq_len`（例如 32k）整塊預留。實際對話平均只有 2k？剩下 30k token 的空間被佔住但永遠不會用到。
2. **內部碎片（internal fragmentation）**：就算預留得準，從「現在的長度」到「最終長度」之間的空間在整個生命週期裡都是死的。
3. **外部碎片（external fragmentation）**：不同請求的預留大小不一，配置器（類 buddy allocator）切出來的洞湊不成新請求要的連續大塊——你在長時間運行的 memcached 或自己寫的 slab 配置上看過一樣的病。

vLLM 論文（SOSP 2023）量測既有系統的結果：**真正存放 token 狀態的記憶體只占 20–40%，其餘 60–80% 是上述三種浪費**。GPU 記憶體是整個系統最貴的資源（ch02），浪費 60–80% 等於把一張 H100 當三分之一張用。而 KV 容量直接決定 batch 能開多大，batch 又決定吞吐量（ch03/ch06）——所以這不是「省記憶體」的小優化，是吞吐量 2–4 倍的差距。

## PagedAttention：幫 KV cache 蓋一套虛擬記憶體

vLLM 的答案是把 OS 教科書第八章搬過來。對應關係精確到可以列表：

| OS virtual memory | PagedAttention |
|---|---|
| Page（固定大小，如 4 KB） | KV block（固定 token 數，vLLM 預設 16 tokens/block） |
| 虛擬位址空間 | 請求的邏輯 token 序列 |
| Page frame（實體記憶體） | HBM 上預先切好的實體 block pool |
| Page table | 每個請求一張 block table |
| MMU 做位址翻譯 | attention kernel 在計算時按 block table 索引 |
| Copy-on-write（fork） | 平行取樣 / beam search 的 KV 共享 |

機制本身可以用三句話講完。啟動時，引擎把扣掉權重後的 HBM（由 `gpu-memory-utilization` 控制，見 ch08）切成幾萬個固定大小的實體 block。每個請求只持有一張 block table——邏輯 block 編號 → 實體 block 編號的映射——token 一邊生成、block 一邊按需配置，**邏輯上連續、實體上散落**。attention kernel 被改寫成能透過 block table 找到散落的 K/V 來算（這就是「PagedAttention」這個 kernel 名字的由來）。

```
請求 A 的邏輯視角:  [tok 0..15][tok 16..31][tok 32..47][tok 48..]
                       │           │           │          │
block table (A):      #7          #21         #3         #44      ← 實體 block 編號
                       ↓           ↓           ↓          ↓
HBM 實體 block pool: [...][#3][...][#7][...][#21][...][#44][...]   ← 完全不連續
```

效果：預留浪費消失（用多少配多少）、外部碎片消失（所有 block 同樣大小，任何空 block 都能用）、內部碎片被壓到只剩**每個序列最後一個 block 的尾巴**——最多 `block_size − 1` 個 token，即 15 個 token、不到 5 MB。論文的數字：**浪費從 60–80% 降到 4% 以下**，吞吐量比當時的系統高 2–4 倍。今天（2026-06）所有主流引擎——vLLM、SGLang、TensorRT-LLM——都用某種形式的 paged KV，這已是業界地板而非賣點。

Block size 的取捨跟 OS page size 一樣：太小，block table 變長、kernel 索引開銷與管理 metadata 上升（極端是 SGLang 早期的 token-level、page size = 1）；太大，內部碎片與共享粒度變差（prefix 要對齊 block 邊界才能共享，見下節）。16–32 是目前的常見平衡點。

**Copy-on-write 與 fork**。平行取樣（一個 prompt 出 n 個候選回答）和 beam search 的多條分支共享同一段 prompt 的 KV。PagedAttention 的做法與 OS `fork()` 一致：子序列複製 block table 而非資料，共享的實體 block 維護 reference count；哪條分支要寫入最後一個未滿的共享 block，才觸發那一個 block 的複製。論文量測：平行取樣省 6.1–9.8% 記憶體，beam search 省 37.6–55.2%。對 infra 工程師，這個機制更重要的遺產是 reference count ＋ block 共享的基礎設施——下一節的 prefix caching 完全建立在它之上。

**類比的邊界**（面試會考）：這裡沒有 MMU 與 TLB，「位址翻譯」是 kernel 軟體查表，translation 的成本是真實存在的 kernel 開銷；沒有 demand paging——block 不會被透明地換出到磁碟再缺頁載回，swap 是排程器的顯式決策（preemption 時 recompute vs swap 的取捨，見 ch06）；也沒有硬體強制的隔離，block 歸屬全靠引擎的 bookkeeping，所以 reference count 的 bug 是真實的故障來源（見故障模式）。

### vLLM V1 的 KV cache manager（2026-06 現況）

vLLM 在 2025 年完成 V0→V1 的世代交替（v0.11 起 V1 是唯一引擎），KV cache manager 是重寫的核心之一。值得知道的工程細節：

- 所有 `KVCacheBlock` 物件在啟動時一次性預配置，避免 Python 物件建立的執行期開銷；free list 用侵入式雙向鏈結串列實作，取塊、還塊都是 O(1)。
- **Prefix caching 預設開啟**。V1 的設計讓它在命中率 0% 時吞吐量損失小於 1%，所以官方直接讓它常開（關閉要顯式傳 `--no-enable-prefix-caching`）。「快取功能便宜到可以永遠開著」是 V1 相對 V0 的重要轉變。
- 逐出是 LRU：block 釋放後回到 free queue 尾端但**保留 hash 不清資料**，重新被配置時才真正失效——同一招你在「延遲刪除」的快取設計裡用過。
- 後續版本持續往「KV 不只一種、一層」走：v0.21 引入 hybrid allocator（讓 full attention 與 sliding window / Mamba 類層共用記憶體池），v0.22 加入 multi-tier KV offloading 框架（2026-06，細節見 offloading 一節）。

## Prefix caching：把重複的 prefill 變成查表

PagedAttention 解決「怎麼放」，prefix caching 解決「怎麼重用」。觀察：KV cache 的內容只由**它之前的 token 序列**決定（ch03：每個 token 的 K/V 是該位置 hidden state 的函數，attention 只往前看）。所以兩個請求只要共享開頭的 token 序列——同一份 system prompt、同一段工具描述、同一場對話的前 N 輪——它們的 KV 在那段前綴上是**位元級相同**的，算一次就夠了。

cache hit 的收益是直接跳過命中部分的 prefill。prefill 是 compute-bound（ch03），跳過它＝省下 GPU 滿載的計算時間＝TTFT 下降、整機 prefill 容量釋放。剩下的問題是工程：怎麼快速找到「可重用的前綴」？2026 年有兩個代表答案。

### vLLM：hash-based block 重用

vLLM 把問題化約到已有的 block 結構上：每個**寫滿的** block 計算一個 hash，hash 鏈式定義——`hash(父 block 的 hash, 本 block 的 16 個 token id, extra)`——`extra` 包含 LoRA adapter ID、多模態輸入的摘要、cache salt 等會改變 KV 語義的因素。全域維護一張 hash → 實體 block 的映射表；新請求進來，沿著它的 prompt 逐 block 算 hash 查表，連續命中多少個 block，prefill 就跳過多少。命中的 block 加 reference count，誰都不用、被 LRU 逐出後才回收。

注意兩個含意：（1）共享粒度是 block——前綴要共享到第 16、32、48 個 token 這種邊界才算數，尾巴不滿一個 block 的部分重算；（2）hash 鏈保證「前綴」語義——第 N 個 block 命中蘊含前 N−1 個都命中，這就是它只能做 *prefix* caching 而非任意子串快取的原因（與 attention 的因果結構一致，不是實作偷懶）。

### SGLang：RadixAttention

SGLang（2312.07104）用的資料結構不一樣：把所有見過的 token 序列組織成一棵 **radix tree**（壓縮前綴樹），邊上是 token 片段、節點對應 KV tensor。新請求做的是樹上的最長前綴匹配，天然支援 token 級粒度的部分命中；逐出是遞迴的 LRU 葉節點淘汰。更重要的是它把**排程**也接上了快取：waiting queue 按「與樹的匹配長度」排序，讓共享前綴的請求湊在一起跑，主動把命中率推高——代價是犧牲 FCFS 的公平性，長尾請求可能被前綴熱門的請求插隊（starvation 風險，排程公平性的討論見 ch06）。2025–2026 SGLang 再疊上 HiCache（階層式 radix tree，把樹延伸到 CPU/儲存層）。

### 對照與選型

| | vLLM（hash-based） | SGLang（RadixAttention） |
|---|---|---|
| 資料結構 | 全域 hash table（block 粒度） | radix tree（token/page 粒度） |
| 匹配粒度 | block 邊界（預設 16 tokens） | 最長前綴，粒度更細 |
| 逐出 | free queue 順序的 LRU | 樹上葉節點 LRU |
| 與排程的耦合 | 低（排程器另管，見 ch06） | 高（cache-aware 排序是設計核心） |
| 嗅覺 | 把快取做成 allocator 的副作用，極簡 | 把快取當一級公民，換取更高命中率 |

實務判斷：兩者在「大量請求共享長 system prompt」的主流場景下命中率相近；SGLang 的樹在**深度分叉**的 workload（多 agent 共享部分前綴、樹狀探索）佔優。這個差異很少單獨決定引擎選型（整體選型見 ch08），但你要能在面試裡講清楚兩種設計的取捨。

### 什麼 workload 受益、證據是什麼

受益程度＝前綴重複率。排序：**agentic 迴圈 ＞ 多輪對話 ＞ RAG（共享 system prompt）＞ 單發無模板請求（≈0）**。agentic workload 是極端案例：每一輪工具呼叫都帶著完整的歷史 context 回來，第 N 輪的 prompt 有 (N−1)/N 以上是逐字重複的。而 agentic 流量正是 2025–2026 成長最快的推論型態（OpenRouter 百兆 token 研究，見 ch17）——這就是 prefix caching 從「優化」變成「產品核心」的需求面原因。

命中的經濟價值，最硬的證據是各家 API 願意為它降價多少（2026-06，折扣規則改版頻繁，引用前查當下官方價目）：Anthropic cache read 為基準輸入價的 10%（90% 折扣），cache write 有 1.25×～2× 的溢價；OpenAI 自動快取、無 write 費，折扣依模型 50–90%；Gemini 隱式快取另有顯式快取（按小時收儲存費），折扣約 75–90%；DeepSeek 的磁碟式快取是業界最深折扣，V3 世代約 90%，V4 世代有報導稱達 98% 以上——⚠️ 此數字僅見第三方來源，截至我能確認的資訊（2026-06）官方頁未直接證實。**廠商用真金白銀告訴你：命中的 token 對它們的成本接近於零**。背後就是本節的機制：命中＝跳過 prefill 計算，只剩記憶體讀取與持有成本（快取經濟學的完整展開見 ch16）。

## Worked example：一個 agentic session 的完整帳

把上面的機制換成錢和毫秒。場景：一個 coding agent，system prompt 2,000 tokens ＋ 工具描述 3,000 tokens（固定前綴 5,000）＋ 使用者任務 500 tokens；接著跑 10 輪工具迴圈，每輪模型輸出約 300 tokens 的 tool call、工具回傳約 700 tokens 的結果附回 context。模型用 Llama-3.3-70B 級別（FP8 權重約 70 GB），部署在一張 H200（141 GB HBM3e、FP8 dense 算力約 2 PFLOPS）上。

**Step 1：token 帳。** 第 i 輪請求的 prompt 長度＝5,500 ＋ (i−1)×1,000（每輪累積 300 輸出＋700 工具結果）：

- 第 1 輪 5,500、第 2 輪 6,500、……、第 10 輪 14,500。
- 10 輪總輸入 token：10×5,500 ＋ 1,000×(0+1+…+9) ＝ 55,000 ＋ 45,000 ＝ **100,000 tokens**。

**Step 2：prefill 計算量。** 無快取時每輪都從頭 prefill。用 ch03 的近似（每 token 的矩陣乘法 FLOPs ≈ 2 × 參數量；attention 的二次項在這個長度下另加一到兩成，以下忽略，故為下界）：

- 全 session prefill 計算量 ≈ 2 × 70×10⁹ × 100,000 ＝ **1.4×10¹⁶ FLOPs**。
- 假設 prefill 階段實際發揮 50% 算力（MFU 0.5，合理的工程值）：有效算力 1 PFLOPS → 全 session 純 prefill 時間 ≈ **14 GPU-秒**。

完美命中時：第 1 輪 prefill 5,500；之後每輪只需 prefill 新進的 700 個工具結果 token（自己輸出的 300 個 token 在 decode 時就已寫入 KV，天然在快取裡）。總量＝5,500 ＋ 9×700 ＝ **11,800 tokens** ≈ 1.65×10¹⁵ FLOPs ≈ **1.65 GPU-秒**。**prefill 計算量差 8.5 倍。** decode 成本兩種情況完全相同——快取只救 prefill。

**Step 3：TTFT。** 看最痛的第 10 輪（14,500 token 的 context）：

- miss：2 × 70×10⁹ × 14,500 ÷ 1×10¹⁵ ≈ **2.0 秒**，這還沒算排隊。
- hit：只 prefill 700 tokens ≈ **0.1 秒**。差 **20 倍**，而且 miss 的 TTFT 隨輪數線性惡化、hit 的近乎平坦。agentic 產品「越用越卡」與否，分界線就在這。

**Step 4：錢——自建視角。** H200 租用以 $3.5/hr 計（2026 年年中快照，級距內代表值），即約 $0.001/GPU-秒。每個 session 省 14 − 1.65 ≈ 12.3 GPU-秒 ≈ **$0.012**。月活 100 萬個這種 session：**每月省約 $12,000 的純 prefill 算力**——或者等價地說，同一個 fleet 的 prefill 容量多了 8.5 倍。對照 ch02 的 roofline 語言：你把 compute-bound 的工作直接消滅，把省下的 FLOPs 讓給別的請求。

**Step 5：錢——API 視角。** 用 Anthropic 計價模式驗算（基準輸入 $3/M、cache read $0.30/M、5 分鐘 TTL write $3.75/M；工具迴圈的輪間隔通常秒級，TTL 內）：

- 無快取：100,000 × $3/M ＝ **$0.300**／session（輸入部分）。
- 有快取：write＝第 1 輪 5,500 ＋ 每輪新增 9×1,000 ＝ 14,500 tokens × $3.75/M ≈ $0.054；read＝85,500 tokens × $0.30/M ≈ $0.026。合計 **$0.080**，省 73%。（輸出 token 3,000 × $15/M ＝ $0.045 兩種情況相同。）

**Step 6：但快取不是免費的——記憶體持有成本。** 第 10 輪結束時這個 session 的 KV 有 15,500 tokens × 320 KB ≈ **5 GB**（FP16；FP8 KV 砍半，見下節）。H200 扣掉 70 GB 權重後可用 KV 池約 60 GB——**只夠 12 個這種 session 把 KV 完整留在 HBM**。工具執行、使用者打字的空檔裡，這 5 GB 是純粹的死重。這就是下面兩節存在的原因：量化讓每 byte 裝兩倍，offloading 讓快取不必住在最貴的記憶體裡。

## KV cache 量化：FP8 KV 的收益與代價

把 KV 從 FP16/BF16 存成 FP8（每元素 1 byte），容量翻倍、讀取 KV 的記憶體流量砍半——decode 是 memory-bound（ch02/ch03），所以長 context 下這同時是容量優化與速度優化。vLLM 用 `--kv-cache-dtype fp8_e4m3`（或 `fp8_e5m2`）開啟；e4m3 精度高但動態範圍小，需要 scaling factor 配合，可用 llm-compressor 對校準資料集求 per-head scale，也可以無校準直接上（scale=1.0）。

vLLM 官方 2026-04 的量測（H100，2026-06 仍是現況的最好參考）：Llama-3.1-8B 的 ITL 隨 context 增長的斜率降到 BF16 的 54%，**約 7k tokens 是損益兩平點**——比這短的 context，FP8 的固定開銷反而讓它更慢；高負載下吞吐量約 +15%。品質面：推理類任務最多掉 1–2 分，長上下文檢索（MRCR）回復率 94–98%。

決策框架：

| 情況 | 建議 |
|---|---|
| 長 context（>8k）、KV 容量是瓶頸 | 開，這是它的主場 |
| 平均 context < 7k 的短請求流量 | 別開，沒有收益還有固定開銷 |
| `head_dim=256` 的模型且在乎 TTFT | 小心，已知 prefill 路徑有 1.6× 變慢的案例（2026-04 量測） |
| 品質敏感（數學、長鏈推理） | 先跑任務型 eval 再上線；無校準掉太多就做校準 |
| 100k+ 超長 context | 確認引擎版本含累加精度修正（vLLM 已修，舊版有累積誤差） |

Murphy 提醒：**FP8 KV 的品質退化在 5xx 裡看不到**——模型只是悄悄變笨。防線只能是 eval gate（ch15 的發布工程會展開）。另外注意 FP8 KV 與 FP8 權重量化（ch07）是獨立的決策，可以分開開關。

## 分層 offloading：當 HBM 裝不下你的快取

Worked example 算過：一張 H200 只放得下 12 個閒置 agentic session 的 KV。但 session 與 session 之間的「溫快取」——五分鐘前活躍的對話、共享的長文件——逐出就要重算，留著就佔 HBM。答案跟你做過的儲存分層一模一樣：

```
層級          容量量級      頻寬量級           誰在用
GPU HBM      80–288 GB    3–8 TB/s          活躍請求的熱 KV
CPU RAM      0.5–2 TB     ~64 GB/s (PCIe5)  分鐘級溫快取
本地 NVMe    數 TB        ~GB/s 級           小時級冷快取
遠端儲存池    無上限        看網路             跨節點共享池（→ ch10）
```

關鍵的數學直覺（完整推導見 ch10）：從 CPU RAM 載回 KV 比重算 prefill 快得多。70B 模型每 token 的 KV 是 320 KB，PCIe Gen5 x16 約 64 GB/s → 載回速率約 20 萬 tokens/s；同一張卡重算 prefill 約 7 千 tokens/s（Step 2 的數字）——**載回比重算快約 28 倍**。模型越大這個差距越大（重算成本 ∝ 參數量，KV 大小成長得慢於參數量）。所以「把溫 KV 放到便宜十倍的記憶體裡」幾乎是免費的午餐，2025–2026 整個生態都在做這件事：

- **vLLM 原生 offloading**：async connector 讓 KV 搬運與計算重疊，CPU tier 走 `cudaMemcpyAsync`/DMA；v0.12 把同一 block 各層的 KV 改成實體連續排列，單次搬運從 KB 級變 0.5–2 MB，吞吐大幅改善。官方數字：單請求 TTFT 改善 2–22 倍、高命中率併發吞吐至多 9 倍（vLLM blog，2026-01）。v0.22 進一步把它框架化成 multi-tier（含 filesystem tier）（2026-06）。
- **LMCache**（v0.4.6，2026-05）：vLLM 的 KV connector 生態裡最成熟的獨立快取層，後端涵蓋 CPU RAM、本地 SSD、Redis/Valkey、S3 相容物件儲存、Mooncake、NIXL/GDS。論文自報長 context workload 下 TTFT 降 1.9–8.1 倍。它的定位值得記住：**把 KV cache 做成引擎之外的一個獨立儲存系統**。
- **Mooncake**（Moonshot AI / Kimi）：把這個思路推到整個叢集——「KVCache-centric」架構，用 GPU 叢集裡閒置的 CPU、DRAM、SSD 組成一個分散式 KV 池，排程器圍繞「KV 在哪裡」做決策（P/D 分離部分見 ch10）。生產證據（專案方自報）：真實負載下讓 Kimi 多承接 75% 請求；模擬場景下吞吐最高 +525%；Kimi K2 以 128×H200 跑出 prefill 224k、decode 288k tokens/s（2026-06）。Mooncake 論文（FAST'25）的副標題就是宣言：*Trading More Storage for Less Computation*。
- 傳輸層的共同地基是 **NIXL**（NVIDIA 的傳輸抽象，統一 UCX/GDS/S3 等後端）——一句話帶過，跨節點 KV 搬運的工程細節屬 ch10。

什麼時候**不要**上 offloading：流量幾乎無前綴重複（命中率撐不起搬運開銷）、平均 context 很短（重算很便宜）、或 PCIe 頻寬已被其他用途吃滿。分層快取每多一層都是一層新的故障面——tier 之間的一致性、搬運佇列的 backpressure、tier 滿了之後的行為，都要有人負責（見故障模式）。

## 失效與一致性：什麼會殺死你的快取

把 KV cache 當一個正經的快取系統來問你最熟的問題：cache key 是什麼？什麼時候失效？多副本怎麼辦？

**Cache key 是 token 序列本身**（加上 LoRA ID、cache salt 等語義因素）。所以失效規則是位元級嚴格的：前綴中**任何一個 token** 變了，從那個位置起全部失效。工程含意比你想的殺傷力大——在 system prompt 開頭放當前時間戳，命中率直接歸零；工具列表的 JSON 序列化順序不穩定（hash map 遍歷順序！）、每次部署 prompt 模板悄悄改一個字、A/B 測試讓一半流量用不同開頭——都是生產環境真實發生過的「快取謀殺」。防禦規則只有一條：**穩定的內容放前面，易變的內容放後面**，並且把 prompt 模板當 schema 一樣做版本治理。

**Sampling 參數不影響 KV**。temperature、top-p 作用在 logits 之後（ch03），KV 在那之前就定了——所以不同 sampling 設定的請求可以共享快取。這是少數對你有利的物理。

**模型一動，全部陪葬**。KV 是特定權重下的中間計算結果，換模型版本、改量化格式、甚至改 TP 切法（KV 的 layout 跟著變，見 ch09）都意味著整池快取作廢。部署新版本＝全叢集冷快取＝TTFT 集體飆高一段時間。這讓 LLM 服務的 rollout 比無狀態服務多一個維度的痛（graceful rollout 的完整處理見 ch15），緩解手段是漸進式發布＋對新副本先打合成的暖機流量。

**多副本不共享快取**（除非你建了上一節的遠端共享池）。每個 replica 有自己的 HBM 快取，round-robin 負載均衡會把同一個 session 的第 N 輪打到沒有它前綴的副本上——**N 個副本下命中率天然掉到約 1/N**。這就是「有狀態的負載均衡」問題：session affinity 的直覺是對的，但快取命中的價值遠高於一般 sticky session，值得專門的 KV-aware routing——機制與 scoring 設計整章展開（見 ch10）。在本章只需要記住結論：**單機把快取做得再好，路由不配合就全白費**。

## 容量視角：KV 利用率是一級健康指標

把本章的所有機制疊起來，KV cache 池就是這個系統的「連線池＋buffer pool」合體：它的水位決定還能收多少新請求、誰會被 preempt（ch06）、什麼時候該擴容（ch13）。你在 RDS 上學到的「盯 buffer pool hit rate 與剩餘連線數」的肌肉記憶，在這裡對應三個必盯指標：

1. **KV cache 利用率**（vLLM 暴露 GPU KV 使用率指標）：長期 >90% 代表在 preemption 邊緣跳舞；持續偏低代表卡買多了或 `max-num-seqs` 設保守了。
2. **Prefix cache 命中率**（V1 暴露 queries/hits 計數器）：它是「流量形態 × 路由品質 × 模板治理」三者的乘積，緩慢下滑幾乎總是其中之一壞了。
3. **Preemption 次數**：KV 容量不足的直接證據，是比 GPU utilization 誠實得多的擴容訊號（為什麼 GPU util 會說謊，見 ch13/ch14）。

這三個指標會在 ch13 變成 autoscaling 訊號、在 ch14 進 dashboard。本章先立一個觀點：**2026 年看一個 LLM serving 團隊成不成熟，看他們的告警裡有沒有 KV 指標就知道了。**

## 故障模式與防禦

| 故障 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| 命中率緩慢下滑 | TTFT p95 爬升、prefill 占比變大，無人改過引擎 | per-replica 命中率趨勢；對照 prompt 模板的部署紀錄 | 模板版本治理；動態欄位移到 prompt 尾端；路由檢查（ch10） |
| 命中率「天生」只有 1/N | 加副本後 TTFT 反而變差 | 比較單副本 vs 多副本的命中率 | KV-aware / session-affinity 路由（ch10） |
| TTFT 雙峰分布 | p50 很美、p95 很慘，平均值毫無意義 | TTFT histogram 按 hit/miss 拆開看 | 分開設 SLI；以命中率作為輔助告警 |
| KV 池耗盡 → preemption 螺旋 | preemption 計數上升、ITL spike、重算推高負載形成正回饋 | KV 利用率 + preemption counter | 容量水位告警（如 85%）、admission control（ch06/ch13） |
| 部署 = 全快取失效 | 每次 rollout 後 TTFT 集體飆高數分鐘 | 對齊 deploy 事件與 TTFT 時間序列 | 漸進 rollout＋合成流量暖機（ch15） |
| Prompt 裡藏了易變內容 | 命中率接近 0，但「我們明明開了快取」 | 抽樣 log 比對相鄰請求的前綴 diff | prompt lint：時間戳/UUID/不穩定 JSON 序列化是頭號嫌犯 |
| FP8 KV 品質退化 | 無任何錯誤碼，使用者抱怨「變笨了」 | 任務型 eval 基線對比（5xx 看不到它） | eval gate 進發布流程；校準；對敏感層 skip |
| Offloading tier 飽和 | 開了 offloading 後 TTFT 不降反升、PCIe 流量打滿 | tier 命中率與搬運延遲指標、`nvidia-smi dmon` 的 PCIe 流量 | tier 容量 sizing；搬運與計算重疊是否生效；必要時關閉 |
| Block/reference count 洩漏（引擎 bug） | KV 使用率與活躍請求數脫鉤、只升不降，數天後開始異常 preemption | KV 利用率 vs in-flight 請求數的相關性監控 | 升級引擎版本；定期重啟的 runbook（醜但有效） |
| 跨租戶 timing side channel | 攻擊者用 TTFT 差異探測別人的 prompt 前綴（已有公開研究展示於商用 API） | 安全審查，非常規監控 | per-tenant cache salt / 隔離快取空間；共享池要有意識地評估 |

## 動手做

**Lab 1 [M1]：用模擬器觀察 prefix caching 指標（免費）**

用 llm-d-inference-sim（模擬 vLLM API 與 metrics、不需 GPU）起一個假引擎，體會「命中率作為一級指標」長什麼樣（指令為示意，旗標以 repo README 為準）：

```bash
docker run --rm -p 8000:8000 ghcr.io/llm-d/llm-d-inference-sim:latest \
  --port 8000 --model meta-llama/Llama-3.1-8B-Instruct
# 終端 2：用相同前綴打 20 次、再用隨機前綴打 20 次
for i in $(seq 20); do
  curl -s localhost:8000/v1/completions -H 'Content-Type: application/json' \
    -d '{"model":"meta-llama/Llama-3.1-8B-Instruct","prompt":"<固定的 2000 字前綴>... 任務 '$i'","max_tokens":32}' > /dev/null
done
curl -s localhost:8000/metrics | grep -i -E 'cache|prefix'
```

成功標準：能指出哪個指標是 KV 使用率、哪兩個相除是命中率，並解釋兩組流量的指標差異。進階替代：在 M1 上以 CPU 模式從原始碼跑真 vLLM（實驗性支援，編譯較費勁），用 `--no-enable-prefix-caching` 對照同一 prompt 第二次請求的 prefill 時間。

**Lab 2 [租 GPU]：開關 prefix caching 的 TTFT 對比（估 $3–5）**

租一張 L4 或 A10（2026 年年中約 $0.5–1.0/hr），跑 8B 模型：

```bash
vllm serve meta-llama/Llama-3.1-8B-Instruct --max-model-len 8192
# benchmark：用帶共享前綴的負載（旗標以你的 vLLM 版本 --help 為準）
vllm bench serve --model meta-llama/Llama-3.1-8B-Instruct \
  --dataset-name random --random-prefix-len 2048 --random-input-len 256 \
  --random-output-len 128 --num-prompts 200
# 第二輪：加 --no-enable-prefix-caching 重起 server，同樣負載再跑一次
```

成功標準：兩輪的 TTFT 中位數差距能用本章機制解釋，並能從 /metrics 的命中計數驗證第一輪確實在命中。記得用完即關機。

**Lab 3 [紙上推演]：重算 worked example**

把本章的 agentic 帳改成你的參數重算一遍：（a）換成 8B 模型（KV 每 token 128 KB）在 L4 上；（b）API 計價換成 DeepSeek 級折扣（read ≈ 原價 10%）；（c）回答：哪個變因對「快取的價值」影響最大——模型大小、輪數、還是固定前綴長度？（提示：對輪數求和的那一項是平方級的。）

## 這個領域往哪走

兩個方向值得盯。第一，**KV cache 正在從引擎內部的資料結構變成一個獨立的儲存層級**——Mooncake Store、LMCache、各家 API 把 context caching 做成商品，都是同一個趨勢：「KV 是新的 Redis」（這個論點的完整辯論見 ch17）。第二，模型架構在反向釜底抽薪：MLA、DSA 等稀疏注意力與 linear/hybrid attention 路線（DeepSeek-V4、Qwen3.5 已在生產採用，2026-06）都在壓縮或改寫 KV 的數學——如果 KV 不再隨 context 線性成長，本章的容量壓力會緩解，但 prefix 重用與分層管理的系統設計依然成立。機制會換，問題不會。

## 自我檢核

1. naive 連續配置的三種浪費各是什麼？PagedAttention 分別用什麼手段消滅它們？剩下的內部碎片上限是多少？
2. PagedAttention 與 OS paging 的類比在哪三個地方失效？（提示：MMU/TLB、demand paging、硬體隔離。）
3. block size 從 16 調到 128 會發生什麼？對命中率和管理開銷各有什麼影響？
4. vLLM 的 hash-based 與 SGLang 的 RadixAttention 各自的資料結構、匹配粒度、逐出策略是什麼？什麼 workload 會拉開兩者差距？
5. 為什麼 temperature 不影響 KV 重用、但 LoRA adapter 會？模型權重更新時會發生什麼？
6. 不看書，重算一遍本章 worked example 的 Step 1–3：10 輪 agentic 迴圈的總 prefill token 數、命中與未命中的計算量差距、第 10 輪的 TTFT 差距。
7. FP8 KV 的損益兩平點為什麼存在（約 7k tokens）？哪三種情況你會建議不要開？
8. 三個副本、round-robin 路由，prefix cache 命中率為什麼會掉到約 1/3？你有哪兩條路修它？

## 延伸閱讀

- [Efficient Memory Management for LLM Serving with PagedAttention（arXiv:2309.06180, SOSP'23）](https://arxiv.org/abs/2309.06180) — 原始論文，60–80% 浪費與 <4% 的量測出處，值得完整讀一遍的系統論文。
- [vLLM 官方文件：Automatic Prefix Caching（design doc）](https://docs.vllm.ai/en/latest/design/prefix_caching.html) — V1 的 hash 鏈、free queue 與 LRU 實作細節，本章 vLLM 部分的一手來源。
- [Fast and Expressive LLM Inference with RadixAttention and SGLang（LMSYS blog）](https://lmsys.org/blog/2024-01-17-sglang/) — RadixAttention 的最佳入門，搭配論文 [arXiv:2312.07104](https://arxiv.org/abs/2312.07104)。
- [Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving（arXiv:2407.00079, FAST'25）](https://arxiv.org/abs/2407.00079) — 把 KV cache 當叢集級儲存系統設計的代表作，含 Kimi 生產數據。
- [The State of FP8 KV-Cache and Attention Quantization in vLLM（vLLM blog, 2026-04）](https://vllm.ai/blog/2026-04-22-fp8-kvcache) — 本章 FP8 KV 數字的出處，含損益兩平點與品質量測方法。
- [Inside vLLM's New KV Offloading Connector（vLLM blog, 2026-01）](https://vllm.ai/blog/2026-01-08-kv-offloading-connector) — CPU offloading 的工程細節：DMA、layout 重排、async 搬運。
- [LMCache（GitHub）](https://github.com/LMCache/LMCache) — 獨立 KV 快取層的代表專案，README 的後端清單就是一張 offloading 生態地圖。
- [llm-d blog: KV-Cache Wins You Can See](https://llm-d.ai/blog/kvcache-wins-you-can-see) — 從平台視角看快取命中的收益，為 ch10 的 KV-aware routing 鋪路。
