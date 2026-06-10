# ch08 — 推論引擎實戰：vLLM、SGLang、TensorRT-LLM 與選型

> **本章解決什麼問題**：ch05 講了 KV cache 怎麼管、ch06 講了排程怎麼排、ch07 講了模型怎麼壓——本章把這些機制落到你真的會操作的軟體上。讀完你會懂 vLLM V1 的架構與每個關鍵參數在轉哪顆旋鈕、會做引擎選型、並且能獨立完成「租卡 → 部署 → benchmark → 讀指標 → 關機」的完整閉環。這是 Part II 的實戰總結，也是 ch09 之後所有分散式內容的單機地基：你必須先會開好一台引擎，才談得上開一個車隊。

## 從你已知的出發

你選過資料庫。MySQL 還是 PostgreSQL 還是 DynamoDB——你知道這種選型題的正確解法從來不是看 benchmark 行銷文，而是：我的 workload 長什麼樣？我的團隊會什麼？壞掉的時候誰修得動？推論引擎的選型是同一道題，連答案的形狀都一樣：業界有一個「預設安全解」（後端世界的 PostgreSQL ≈ 推論世界的 vLLM），然後有幾個特定 workload 下值得偏離預設的例外。本章後半就是把這張例外清單寫清楚。

你也調過資料庫參數。`innodb_buffer_pool_size`、connection pool 上限、`work_mem`——你很清楚這些參數沒有「最佳值」，只有「對你的流量正確的值」，而且調錯的症狀往往出現在離參數很遠的地方（pool 太小 → 鎖等待暴漲，看起來像鎖的問題，其實是記憶體的問題）。vLLM 的參數表完全同構：`--gpu-memory-utilization` 就是你的 buffer pool size，`--max-num-seqs` 就是你的 connection pool 上限，調錯的症狀一樣會偽裝成別的問題。你在 RDS 上練出來的「從症狀反推參數」的肌肉，本章直接複用。

最後，你解剖過系統。你讀過 PostgreSQL 的架構圖——parser、planner、executor、buffer manager 各管一段，一條 SQL 進去怎麼變成磁碟 I/O。本章第一件事就是對 vLLM 做同樣的解剖：一個 HTTP 請求進去，token 怎麼出來，中間經過哪些 process、哪些佇列、哪些記憶體配置。看懂這張圖之後，引擎對你就不再是黑盒子，而是一個你能診斷、能調校、出事時知道去哪個 process 找 log 的系統——跟你對待 PostgreSQL 的方式沒有兩樣。

## vLLM 架構解剖：一個請求的一生

先講大局。vLLM 從 2025 年起經歷了一次完整的引擎世代交替：V1 架構重寫了排程器、KV cache manager 與 process 模型，到 v0.11 把 V0 程式碼全部刪除——本書寫作時（2026-06，vLLM 0.22.x）**V1 是 codebase 裡唯一的引擎**，你在網路上看到的舊文章若還在講 `AsyncLLMEngine`、swap-based preemption，那是 V0 的化石，讀的時候要帶年份意識。

### Process 模型：把 CPU 工作隔離出去

V1 最重要的架構決策是**多 process 分工**。動機很純粹：當一次 decode forward 只要 5ms 上下，任何擋在迴圈裡的 CPU 工作——HTTP 處理、tokenization、detokenization、串流回傳——都會直接吃掉吞吐。V1 的解法是把這些 CPU 工作搬到獨立 process，用 ZeroMQ（ZMQ）做 IPC，讓它們跟 GPU 的 forward **重疊執行**而不是串行排隊。你可以把它理解成你熟的 Node.js 模式：把 CPU-bound 工作丟出 event loop，main loop 只做最關鍵的那件事。

```text
┌─ Process A：API server（AsyncLLM 前端）────────────────┐
│  HTTP/SSE ↔ OpenAI 相容層（FastAPI）                    │
│  chat template 套用 → tokenize → 經 ZMQ 送進核心        │
│  經 ZMQ 收回 token id → detokenize → SSE chunk 回客戶端 │
└────────────────▲──────────────┬────────────────────────┘
          ZMQ IPC│（雙向、非同步）│
┌─ Process B：EngineCore（busy loop）─────────────────────┐
│  scheduler：每步輸出 {request_id: 本步算幾個 token}      │
│  KV cache manager：block 配置、prefix cache 查表（ch05） │
│  指揮 model executor 執行 forward                        │
└────────────────┬────────────────────────────────────────┘
                 │（TP>1 時 fan-out 到 N 個 worker process）
┌─ Process C..N：Worker（每張 GPU 一個）───────────────────┐
│  ModelRunner：準備輸入 tensor、forward、CUDA graphs(ch07)│
│  sampler 抽出下一個 token                                │
└──────────────────────────────────────────────────────────┘
```

數一下 process：單卡部署是「1 個 API server + 1 個 EngineCore + 1 個 worker」；TP=4 的部署是 1 + 1 + 4 = 6 個 process。這件事有直接的維運後果：你 `ps` 看到多個 python process 是正常的；OOM kill 掉其中一個，整組會一起死（或更糟——半死，見故障模式一節）；container 的 PID namespace 裡要允許 multiprocessing。

### 請求的一生

把 ch05/ch06 的機制串成一條時間線。一個 `POST /v1/chat/completions`（stream=true）進來之後：

1. **API server 收下 HTTP 請求**，套用模型的 chat template（把 messages 陣列展平成單一 prompt 字串），tokenize 成 token ids。這裡是純 CPU 工作，與 GPU 完全無關。
2. **經 ZMQ 把請求交給 EngineCore**，掛進 waiting 佇列。從這一刻起，請求的排隊時間開始累積——它不會出現在 GPU 指標上，只會出現在 `vllm:request_queue_time_seconds`（ch06 講過的「佇列先於資源惡化」）。
3. **scheduler 在某一步把它撈出來**：先問 KV cache manager「prefix cache 有沒有命中？」（ch05 的 hash-based block 重用——命中的部分直接掛 block、跳過計算），再為剩餘 prompt 配置 KV blocks，然後在本步的 token budget 裡分給它一個 prefill chunk。V1 排程器不區分 prefill/decode 階段，每步的決策就是一張 `{request_id: num_tokens}` 的字典（ch06）。
4. **EngineCore 把這一步的 batch 丟給 worker**，ModelRunner 準備輸入、跑 forward（decode 部分走 CUDA graphs，見 ch07）、sampler 抽出 token，結果回到 EngineCore。
5. **長 prompt 分多步算完 prefill**（chunked prefill，ch06），第一個生成 token 出現的那一步，就是 TTFT 的終點。
6. **token id 經 ZMQ 流回 API server**，detokenize 成文字、包成 SSE chunk 推給客戶端。注意分工：EOS 與 `max_tokens` 的停止判斷在 EngineCore 就能做（它看得到 token id）；但 stop string 需要看「文字」，所以在 API server 端的 output processor 判斷，命中後再回頭通知 EngineCore abort——一來一回之間可能多算一兩個 token，這是正常的。
7. **decode 迴圈每步重複 4–6**，直到停止條件成立，EngineCore 釋放它的 KV blocks（若 prefix caching 開著，blocks 進快取池等待重用而非立刻清除，ch05）。
8. **異常路徑**：客戶端 SSE 斷線時，API server 偵測到連線關閉，主動向 EngineCore 發 abort，KV blocks 即刻回收。這條路徑斷掉的後果（gateway 沒把斷線翻譯成 abort）在 ch06 的故障表講過：殭屍請求佔著 slot 生成沒人收的 token。

整條鏈路裡值得你停下來記住的一件事：**tokenize/detokenize 與 forward 是在不同 process 平行發生的**。當 GPU 在算第 N 步時，API server 同時在 detokenize 第 N−1 步的輸出、tokenize 剛到的新請求。這就是 V1 相對 V0 的吞吐紅利來源之一——不是 GPU 變快了，是 CPU 不再擋路。

## 關鍵參數完整表

下表是 2026-06、vLLM 0.22.x 時點的整理。預設值會隨版本演進，**正文記機制、預設值以你手上版本的 `vllm serve --help` 為準**——這句話不是免責聲明，是操作紀律。

| 參數 | 它在解什麼問題 | 預設（2026-06） | 調錯的症狀 |
|---|---|---|---|
| `--max-model-len` | 單一請求的 context 上限，決定「一個請求最多能吃掉多少 KV」 | 自動取模型 config（往往大得離譜，如 32k–256k） | 太大：啟動時報 KV 容量不足直接起不來，或 KV 牆大幅提前；太小：長請求被 400 拒絕 |
| `--gpu-memory-utilization` | 引擎可用的 GPU 記憶體比例（權重 + KV + workspace 全包），KV pool 大小由它倒扣出來 | 0.92（早期版本 0.9） | 太高：流量尖峰偶發 OOM crash、全部 in-flight 請求陪葬；太低：KV pool 縮水、preemption 變多 |
| `--max-num-seqs` | 同時 running 的請求數上限（ch06 的 batch B） | 1024（V1；V0 時代是 256） | 太高：ITL 墊高、KV 壓力大、preemption storm；太低：GPU 餵不飽、佇列堆積 |
| `--max-num-batched-tokens` | 每步 token budget，控制 prefill chunk 對 decode 的干擾（ch06） | V1 世代常見 8192（隨版本/硬體調整，以 `--help` 為準） | 太大：長 prompt 進來 ITL 尖刺；太小：TTFT 變差、prefill 吞吐掉 |
| `--enable-prefix-caching` | 前綴 KV 重用（ch05） | **V1 預設開啟**（用 `--no-enable-prefix-caching` 關） | 誤關：agentic/多輪流量 TTFT 暴漲、prefill 算力白燒；對比實驗忘了關：高估裸 prefill 效能 |
| `--tensor-parallel-size` | 單一模型切到幾張卡（單節點內，機制見 ch09） | 1 | 卡間只有 PCIe 還硬開 TP：all-reduce 吃掉大半收益；單卡裝得下還開 TP：純付通訊稅 |
| `--kv-cache-dtype fp8` | KV cache 減半（ch05） | `auto`（跟隨模型 dtype） | 長推理鏈/長對話品質劣化，且 5xx 看不到——要 eval 才抓得到 |
| `--quantization` | 權重量化格式；多數情況自動從 checkpoint 偵測，不用手設 | 自動偵測 | 卡不支援該格式（如 Ampere 跑 FP8）：啟動失敗或 fallback 到慢路徑，吞吐莫名其妙地差 |
| `--dtype` | 權重載入精度（FP16/BF16） | `auto` | 在不支援 BF16 的舊卡上強用：報錯或退化 |
| `--speculative-config` | speculative decoding 設定（JSON：draft model / EAGLE / n-gram，ch07） | 關 | 高 batch 流量下開啟：吞吐不升反降（驗證稅，ch07 講過的反直覺） |
| `--scheduling-policy` | `fcfs` 或 `priority`（ch06） | `fcfs` | 開 priority 但上游沒做配額：低優先權租戶餓死 |
| `--enforce-eager` | 關閉 CUDA graphs，debug 用 | 關（即 graphs 開啟） | debug 完忘記拿掉：decode 多吃一截 launch overhead，ITL 變差（量級見 ch07） |
| `--block-size` | KV block 的 token 數（ch05 的分頁粒度） | 16 上下（依硬體） | 幾乎不需要動；亂動影響 prefix cache 命中粒度與記憶體碎片 |

調參心法四條，順序有意義：

1. **先定 `--max-model-len`，依據是你流量的 p99 context，不是模型的能力上限**。模型支援 256k 不代表你要付 256k 的 KV 預算單位風險——這是新手第一坑，啟動 OOM 十之八九是它。
2. **再定 `--gpu-memory-utilization`**：給足但留餘裕（activation 尖峰與 CUDA graphs 也要記憶體）。
3. **然後用 ch06 的方法找工作點**：`max-num-seqs` 決定你貼 KV 牆多近、`max-num-batched-tokens` 決定 prefill 干擾形狀。
4. **一次只動一個參數，每動必量**（主軸二：量測 → 診斷 → 優化 → 用數據證明）。引擎參數的交互作用比 MySQL 參數更黏，不量測的調參是占卜。

## 營運介面：OpenAI 相容 API 與 /metrics

vLLM 對外的兩張臉，你都會天天打交道：

**OpenAI 相容 API**：`/v1/chat/completions`、`/v1/completions`、`/v1/models`、`/v1/embeddings`，加上 `/health`。OpenAI API 已是推論服務的 de facto 介面標準（平台層含意見 ch12），實務好處是你的客戶端、gateway、benchmark 工具全部即插即用——本章後面的 `vllm bench` 和你未來會用的 k6 腳本，打的都是同一組端點。

**`/metrics`（Prometheus 格式）**：完整的指標分類學在 ch14，但有六個名字現在就要進你的肌肉記憶，因為本章的 benchmark 與調參全靠它們：

| 指標 | 回答什麼問題 |
|---|---|
| `vllm:num_requests_running` / `vllm:num_requests_waiting` | 引擎滿了沒？佇列在堆積嗎？ |
| `vllm:kv_cache_usage_perc` | 離 KV 牆多遠？（ch05 的一級健康指標） |
| `vllm:num_preemptions_total` | 樂觀 admission 破產了幾次？（穩態應為 0，ch06） |
| `vllm:time_to_first_token_seconds` / `vllm:inter_token_latency_seconds` | TTFT 與 ITL 的 histogram，SLO 的原料 |
| `vllm:prefix_cache_hits` / `vllm:prefix_cache_queries` | 兩者相除 = prefix cache 命中率（ch05） |
| `vllm:request_queue_time_seconds` | 請求在 waiting 佇列陪葬了多久 |

## SGLang：另一個第一梯隊

SGLang（本書寫作時 v0.5.12，2026-05）是 vLLM 唯一的同量級對手。它從 RadixAttention 起家——用 radix tree 做 token 級的 prefix 重用（與 vLLM hash-based block 重用的對照在 ch05 講過）——如今長成功能完整的生產引擎：P/D 分離、wide-EP、speculative decoding（0.5.11 起 V2 預設開啟）、階層式 KV 快取（HiCache），近期版本甚至加了 Apple Silicon 原生 MLX backend（0.5.10 release notes）。專案方宣稱在生產環境驅動超過 40 萬張 GPU、採用者包括 xAI、LinkedIn、NVIDIA、AMD——數字出自專案自述，但「第一梯隊」的定位本身沒有爭議：NVIDIA 同時為 vLLM 與 SGLang 維護官方 container 與 release notes，Dynamo 和 llm-d 等上層框架也同時支援兩者。

跟 vLLM 的真實差異，2026 年年中的誠實版本：

- **功能高度趨同**。兩邊的 release notes 像在抄對方作業：你說 P/D 分離我也有，你支援 DeepSeek-V4 我隔週跟上。單看功能清單已經選不出勝負。
- **結構化輸出是 SGLang 的傳統強項**。它把 grammar 約束（JSON schema、regex，經 xgrammar 等後端）的 mask 計算與 GPU forward 重疊執行，在高比例 guided decoding 的流量下開銷明顯更低。如果你的 workload 是「每個請求都要吐合法 JSON」的 agent/工具呼叫場景，這是真實差異點。
- **Prefix 重用的粒度哲學不同**（ch05）：radix tree 是 token 級、自動發現共享前綴；對 prefix 結構複雜的 agentic 流量理論上更貼。但 vLLM V1 把 prefix caching 做到預設開啟、零命中時近零開銷，工程成熟度追平了大部分差距。
- **效能對比不要信任何單點數字**。第三方評測互有勝負，「某引擎在 H100 上快 29%」這類數字多半出自行銷性質部落格，換個 workload、換個版本就翻盤。唯一可信的 benchmark 是你自己的流量打出來的那份（方法論見 ch14）。

啟動介面對你來說幾乎是平行宇宙：`python -m sglang.launch_server --model-path Qwen/Qwen3-8B --port 30000`，一樣是 OpenAI 相容 API，一樣有 Prometheus 指標。本章所有的部署紀律與 benchmark 閉環，換成 SGLang 照走。

## TensorRT-LLM：compile 式引擎的取捨，與一次重要的轉向

TensorRT-LLM（本書寫作時 1.2.x）是 NVIDIA 的親兒子引擎，它的傳統賣點是 **ahead-of-time compile**：把模型針對特定 GPU、特定精度、特定 batch 形狀編譯成 TensorRT engine，用最佳化到牙齒的 kernel 換峰值效能。代價你可以類比 JIT vs AOT：每個「模型 × 卡型 × 配置」組合都要重新編譯（分鐘到小時級）、換模型慢、debug 難、生態封閉在 NVIDIA 硬體上。

然後 2026 年發生了一件值得寫進選型史的事：**TensorRT-LLM 1.2 把 PyTorch backend 設為預設**——`trtllm-serve` 預設不再走 TensorRT engine 編譯路徑，而是跟 vLLM/SGLang 一樣直接在 PyTorch 上跑、配自家最佳化 kernel（2026-06，TensorRT-LLM release notes）。連 NVIDIA 自己都承認了這個市場現實：在模型兩個月一版、multi-LoRA、動態流量的世界裡，「編譯一切」的彈性稅高於它買到的峰值收益。compile 路徑仍在，但已不是主旋律。

那 2026 年還什麼時候值得選它？務實清單：

- **你重度押注 NVIDIA 最新硬體的數值格式**：Blackwell 上的 NVFP4 路徑（ch07）TensorRT-LLM 最成熟，這是它最硬的差異點。
- **模型固定、流量穩定、要榨最後 10–20%**：模型半年不換、卡型統一、延遲敏感到願意付編譯與維運成本——這種「定置炮台」場景 AOT 仍有意義。
- **你已經在 NVIDIA 全家桶裡**：Dynamo、NIM、企業支援合約，整合面積最小。

反過來說，如果你的模型清單每月在變、團隊只有兩個人、或你需要跨硬體可攜性——它的工程成本曲線會教你做人。

## 本地與邊緣線：llama.cpp、Ollama、MLX

這三個工具跟上面三個引擎不在同一個賽道，搞清楚定位可以避免兩種錯誤（拿 Ollama 上生產、或拿 vLLM 跑筆電）：

- **llama.cpp**：純 C/C++ 實作 + GGUF 量化格式生態，目標是「在任何硬體上跑起來」——CPU、Apple Silicon、消費級顯卡。它有 server 模式與基本的並發處理，但它的設計中心是可攜性與低資源，不是吞吐極限。你在 ch03/ch07 的 M1 實驗用的就是它。
- **Ollama**：llama.cpp 之上的使用者體驗層——`ollama pull`、`ollama run`，模型管理像 docker image。定位是開發者本機與 demo，你 ch01 的第一次 SSE 接觸用的就是它。
- **MLX**：Apple 官方的 Apple Silicon 陣列運算框架，吃統一記憶體架構的紅利，M 系列上常是最快的本地選項；SGLang 也加了 MLX backend（2026）。定位：Mac 上的開發迴圈。

一句話總結賽道差異：vLLM/SGLang/TRT-LLM 在解「一張到一群資料中心 GPU 的吞吐與 SLO」，這三個在解「我手邊這台機器能不能跑」。前者的核心技術（continuous batching、PagedAttention、TP）後者或缺或淺，反之 GGUF 的極致量化與 CPU 路徑前者也不在乎。中間地帶（單卡小流量內部工具）兩邊都能用，看你要不要 `/metrics` 與生產級併發——通常很快就會要。

## 選型決策樹：預設選 vLLM，除非——

先講結論再講理由：**2026 年的預設答案是 vLLM**。理由不是它每項 benchmark 都贏（並沒有），而是選型題的本質是風險管理：vLLM 有最大的社群與貢獻者基數、最廣的硬體支援（NVIDIA/AMD/TPU/Trainium/CPU）、最完整的周邊生態（K8s operator、llm-d、Ray Serve、Red Hat 商業支援都以它為一級公民）、以及最高的「出事時 Google 得到答案」機率。這跟你預設選 PostgreSQL 的邏輯一模一樣——不是因為它最快，是因為它最不會讓你半夜孤立無援。

```text
你要在哪裡跑？
├─ 筆電 / 邊緣 / CPU ──────────────→ llama.cpp / Ollama / MLX
└─ 資料中心 GPU
   ├─ 流量以結構化輸出為主（JSON/grammar 佔大宗）
   │    └→ SGLang 與 vLLM 各 benchmark 一輪，常見 SGLang 勝出
   ├─ agentic、prefix 極重、且實測 vLLM 命中率不滿意
   │    └→ 試 SGLang（RadixAttention 的主場）
   ├─ 模型固定 + 全 NVIDIA + 要榨峰值或 NVFP4
   │    └→ TensorRT-LLM（付得起編譯與維運稅再來）
   ├─ 非 NVIDIA 硬體（AMD/TPU/Trainium…）
   │    └→ vLLM（支援面最廣），或硬體廠商主推的那個
   └─ 其他所有情況 ──────────────────→ vLLM
```

把例外清單再攤開成決策表，含代價欄——沒有代價欄的決策表都是行銷材料：

| 你偏離預設去選… | 什麼時候值得 | 你付出的代價 |
|---|---|---|
| SGLang | 結構化輸出重、prefix 結構複雜的 agentic 流量、且 A/B 實測有感 | 社群與周邊生態小一號；維運知識庫較薄；功能差距會隨版本來回擺動 |
| TensorRT-LLM | 模型/硬體固定的峰值場景、Blackwell NVFP4、NVIDIA 企業支援 | 編譯迴圈拖慢迭代、NVIDIA lock-in、團隊要養專門知識 |
| llama.cpp/Ollama | 本機開發、離線/邊緣、極低資源 | 沒有生產級 batching/排程/指標，上了量就見底 |
| 自己 fork / 自研 | 你是 model lab 且有專職引擎團隊 | 全部 |

兩條紀律收尾。第一，**選型決策的有效期限大約六個月**：兩大引擎功能趨同的速度極快，把選型寫進可重跑的 benchmark（ch14），而不是寫進石頭。第二，**團隊能力是真實的決策維度**：一個會修 vLLM 的工程師，比 5% 的吞吐差距值錢得多。

## 完整部署 walkthrough：從租卡到關機

這一節是本章的核心實作，對應 plan.md 的旗艦專案③。場景：在 RunPod 租一張 L4（24 GB），部署 Qwen3-8B，跑一輪 benchmark，讀懂指標，關機。Lambda 等其他平台流程同構（Lambda 的入門卡通常是 A10 24 GB，價位略高；以官網現價為準）。

### 第 0 步：成本控制紀律（先於一切技術步驟）

雲端 GPU 燒錢的方式跟你熟的 EC2 不同：單價高、而且**最大的事故不是用太兇，是忘記關**。開卡前的紀律清單：

1. **用儲值制，不綁自動扣款**：RunPod 支援預先儲值，存一筆小額（如 $25）當硬上限——錢燒完 pod 自動停，這是最可靠的 circuit breaker。
2. **看清楚 Stop 和 Terminate 的差別**：Stop 只停 GPU 計費，**磁碟 volume 繼續算錢**；Terminate 才是真的歸零。實驗結束一律 Terminate。
3. **開卡前先寫好要跑的指令**：卡跑起來的每一分鐘都在計費，腳本先在本機寫好、貼上即跑。租卡時間應該花在等模型下載和跑 benchmark，不是花在現場查文件。
4. **設鬧鐘**：物理鬧鐘。兩小時後響。比任何雲端預算警報都可靠。
5. **結束後驗屍**：回到 billing 頁面確認計費已停、餘額符合預期。這個習慣總有一天會替你抓到一台殭屍 pod。

L4 在 RunPod 的 on-demand 價格約 $0.39/hr（2026-06 快照；GPU 租價月級波動，以站上現價為準）。整個 walkthrough 含下載與三組配置的 benchmark 約 2–3 小時，GPU 費用 $1–2，加上重試與探索的餘裕，整章實驗預算抓 $5–10 很寬鬆。

### 第 1 步：租卡

RunPod console → Pods → Deploy：選 L4（Secure Cloud）、官方 PyTorch template（或直接用 `vllm/vllm-openai` container image，可省安裝步驟）、container disk 至少 50 GB（模型權重 16 GB + HF cache + 餘裕）、expose HTTP port 8000。部署後用網頁終端或 SSH 進去。UI 細節隨平台改版，但「卡型 / image / 磁碟 / 端口」四個決策點不會變。

### 第 2 步：起 vLLM

```bash
# 若用 PyTorch template 才需要裝；用 vllm-openai image 可跳過
pip install vllm

# 在 tmux 裡起服務（SSH 斷線不死）
tmux new -s vllm
vllm serve Qwen/Qwen3-8B \
  --max-model-len 8192 \
  --gpu-memory-utilization 0.90 \
  --max-num-seqs 16
```

第一次啟動要從 HuggingFace 拉 16 GB 權重，依機房網路 5–15 分鐘——這段時間就是 ch12 會講的 cold start 的其中一段，先體感記下來。啟動 log 裡值得讀的三行：模型載入後的記憶體用量、KV cache 可用 block 數（引擎用 `gpu-memory-utilization` 倒扣出來的 KV pool，ch05/ch06 的數學在這裡變成一行 log）、以及 CUDA graph capture 完成。

Smoke test：

```bash
curl -s localhost:8000/v1/models | python3 -m json.tool
curl -N localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"Qwen/Qwen3-8B","stream":true,
       "messages":[{"role":"user","content":"用一句話解釋 KV cache"}]}'
```

看到 SSE chunk 一個一個吐出來（ch01 你在 Ollama 上看過同樣的形狀），服務就活了。

### 第 3 步：benchmark

用官方內建的 `vllm bench`（已是 CLI 子命令）。流量形狀對齊 ch06 worked example：輸入 1,500、輸出 500：

```bash
vllm bench serve --model Qwen/Qwen3-8B \
  --dataset-name random \
  --random-input-len 1500 --random-output-len 500 \
  --request-rate 4 --num-prompts 200
```

`--request-rate` 是 open-loop 的到達率（為什麼 open-loop 重要、coordinated omission 是什麼坑，ch14 詳講；現在先照做）。同時開另一個 tmux pane 盯引擎狀態：

```bash
watch -n 5 "curl -s localhost:8000/metrics | \
  grep -E 'num_requests_(running|waiting)|kv_cache_usage|num_preemptions_total' | grep -v '^#'"
```

### 第 4 步：讀指標

bench 結束會輸出 throughput、TTFT、TPOT/ITL 的分位數。三個交叉判讀，全部接回 ch06 的框架：

- **`running` 持續頂著 `max-num-seqs`、`waiting` > 0** → 引擎在它的 admission 上限飽和，吞吐被你設的 16 卡住，不是卡在硬體。
- **`kv_cache_usage_perc` 接近 1.0、`num_preemptions_total` 在走動** → 撞 KV 牆了，數字會跟你用 ch03 公式手算的牆位對得上。
- **TTFT p99 遠大於 p50、且與 `request_queue_time` 同步惡化** → 排隊問題，不是計算問題。

然後改參數重跑（下一節的三組配置就是現成的實驗計畫），每輪記錄到同一張表。這就是「量測 → 診斷 → 優化 → 用數據證明」的最小完整迴圈——跟你做 RDS 優化時一模一樣，只是指標換了名字。

### 第 5 步：關機

```bash
exit
# Console → Terminate pod（不是 Stop）→ Billing 頁確認計費停止
```

## Worked example：同一張 L4、同一個 8B 模型、三組配置

把上面的閉環具體化成一份實驗計畫與預期結果。**下表為推算值、非實測**：用 ch06 的一階模型（decode 時間 ≈ 每步讀取 bytes ÷ 有效頻寬）算出，假設標在表下；你在動手做 Lab 1 的任務就是實測它、然後解釋你的量測值與推算值的偏差。

設定：L4（24 GB GDDR6、頻寬 300 GB/s 規格值，取 80% ≈ 240 GB/s 有效；FP8 為 Ada 世代原生支援）。模型 Qwen3-8B 級 dense 8B：FP16 權重 16 GB / FP8 權重 8 GB；KV 每 token 128 KB（FP16）/ 64 KB（FP8 KV）。流量同 ch06：平均 context 2,000 tokens（輸入 1,500 + 輸出 500）。activation 與 CUDA graphs 工作區估 1.5 GB。

| | 保守 | 平衡 | 激進 |
|---|---|---|---|
| 權重 | FP16（`Qwen3-8B`） | FP8（官方 FP8 checkpoint） | FP8 |
| KV dtype | FP16 | FP16 | FP8（`--kv-cache-dtype fp8`） |
| `--gpu-memory-utilization` | 0.90 | 0.90 | 0.95 |
| `--max-model-len` | 4,096 | 8,192 | 16,384 |
| `--max-num-seqs` | 16 | 40 | 96 |
| KV pool（倒扣） | ≈ 4.1 GB | ≈ 12.1 GB | ≈ 13.3 GB |
| KV 牆（@avg 2k context） | ≈ 16 併發 | ≈ 47 併發 | ≈ 104 併發 |
| 滿載每步讀取 | 16 + 4.1 ≈ 20.1 GB | 8 + 10.2 ≈ 18.2 GB | 8 + 12.3 ≈ 20.3 GB |
| 穩態 ITL（推算） | ≈ 84 ms | ≈ 76 ms | ≈ 85 ms |
| 總吞吐（推算） | ≈ 190 tok/s | ≈ 530 tok/s | ≈ 1,130 tok/s |
| 單請求體感 | ≈ 12 tok/s | ≈ 13 tok/s | ≈ 12 tok/s |
| 主要風險 | GPU 大量閒置、$/Mtok 最差 | 幾乎沒有——這就是甜蜜點的長相 | 0.95 的 OOM 餘裕極薄；FP8 KV 品質風險（ch05）；長 context 流量一來就 preemption |

四個機制成因，逐項對應前章：

1. **保守 → 平衡的 2.8 倍吞吐，全部來自「權重 FP8」這一個動作的兩條效應**。FP8 把每步的「固定成本」從 16 GB 砍到 8 GB（ch06 的攤提數學）；同時騰出的 8 GB 全數變成 KV pool（4.1 → 12.1 GB），讓 B 能從 16 升到 40。一個量化決策同時改善固定成本與撞牆點，這就是 ch07 說量化是單卡最高槓桿的原因。
2. **平衡 → 激進的吞吐再翻倍，全部來自 FP8 KV**。每 token KV 減半 → 同樣的 pool 裝下兩倍併發 → 固定成本攤提給兩倍的請求。注意 ITL 幾乎沒變（85 vs 76 ms）：因為每步讀取的總 bytes 差不多，變的是這些 bytes 服務多少人。
3. **三組的單請求體感全部是 12–13 tok/s，難看但誠實**。L4 只有 240 GB/s 有效頻寬——decode 是 memory-bound（ch03），頻寬就是天花板，參數調不出頻寬。這告訴你 L4 的定位：成本敏感的吞吐型 workload，不是低延遲產品。要體感快，換 HBM 的卡（ch02 的頻寬表、ch13 的硬體選型）。
4. **「激進」不是「更好」，是不同的風險定價**。0.95 的記憶體餘裕、FP8 KV 的品質風險、貼著 KV 牆的 preemption 暴露——benchmark 表上它全贏，generation 品質與尾延遲的帳要另外算（goodput 視角，ch06/ch14）。生產配置從「平衡」出發，拿數據說服自己之後才往右走。

## 故障模式與防禦

引擎實戰的故障跟前幾章的機制性故障（preemption storm、KV 牆，見 ch05/ch06）不同，多半發生在「引擎周邊」——啟動、相依、網路、帳單。症狀導向整理：

| 故障模式 | 症狀 | 怎麼觀測 | 防禦 |
|---|---|---|---|
| `max-model-len` 超出 KV 預算 | 啟動直接失敗，報「model's max seq len 大於可用 KV cache 容量」之類錯誤 | 啟動 log | 用流量 p99 context 設 `--max-model-len`，不是用模型上限；先用 ch03 公式手算 KV pool 夠不夠 |
| 權重下載失敗 / gated model | 啟動卡在下載、401/403、或龜速 | 啟動 log、網路流量 | 先 `huggingface-cli download` 預拉；gated model 設 `HF_TOKEN`；生產環境權重走自家儲存而非裸拉 HF（ch12） |
| CUDA / driver 版本不合 | container 起不來或 import 即炸，stack trace 指向 libcuda | `nvidia-smi` 的 driver 版本 vs image 要求的 CUDA 版本 | 用官方 image；租卡平台選明示 driver 版本的 template（ch04 的版本相容矩陣地獄，ch11 再會） |
| 量化格式與卡不相容 | 啟動失敗，或默默 fallback 慢路徑、吞吐離譜地差 | 啟動 log 的 kernel/backend 選擇訊息 | 對照 ch07 的硬體支援表（FP8 需 Ada/Hopper+、NVFP4 需 Blackwell） |
| 半死的 process 樹 | 某個 worker 被 OOM kill，API server 還活著、`/health` 看似正常但請求全 hang | process 數對不上；GPU 記憶體佔用還在但無計算活動 | liveness probe 要打真請求而非只打 `/health`（「深健康」探針，ch15）；container 內配 init 收屍 |
| crash 後 GPU 記憶體未釋放 | 重啟引擎報 OOM，`nvidia-smi` 顯示記憶體被無名 process 佔用 | `nvidia-smi` | 殺乾淨殘留 process；container 化部署天然緩解（pod 死全死） |
| chat template 錯誤 | 不報錯，但模型輸出品質詭異（格式錯亂、自問自答） | 肉眼 + eval；5xx 與延遲全部正常 | 用模型官方 chat template；升級引擎/換 checkpoint 後跑一輪煙霧 eval（ch15 的「模型變笨不報錯」） |
| 反向代理吃掉 SSE | 客戶端 TTFT 莫名變成整段回應時間（token 不流式、一次全到） | 對比直連引擎 vs 過 proxy 的行為 | 代理層關 buffering、放寬 idle timeout（你調 Nginx/KrakenD 的老本行） |
| benchmark 自欺 | 壓測數字漂亮、上線 SLO 崩 | 對照 open-loop 重測 | closed-loop/無 warmup/只看平均的測試一律重做（ch14） |
| 忘記關卡 | 信用卡帳單 | billing 頁 | 本章第 0 步的五條紀律；儲值制是最後防線 |

## 動手做

### Lab 1 [租 GPU]：完整閉環——部署、三組配置、benchmark、關機（估 $5–10）

本章的核心實驗，直接對應 plan.md 旗艦專案③。照「部署 walkthrough」流程租一張 L4，依 worked example 的三組配置各跑一輪 `vllm bench serve`（同樣的流量形狀：input 1500 / output 500 / rate 4 與 rate 16 各一次），每輪記錄：throughput、TTFT p50/p95、ITL p50/p95、`num_preemptions_total`、`kv_cache_usage_perc` 峰值。

**成功標準**：(1) 產出一張「配置 × 指標」實測表，與本章推算表並排；(2) 對每個偏差超過 ±30% 的格子寫出一句機制解釋（例如「實測吞吐低於推算，因為 rate 4 下引擎根本沒滿載——推算的是飽和值」）；(3) 指出哪一組在 rate 16 時開始 preempt，對照你手算的 KV 牆；(4) pod 已 Terminate、billing 已驗證。這張表就是你作品集的第一份引擎調參報告（ch18 的敘事模板等著它）。

### Lab 2 [M1]：用 llama.cpp 體感「引擎」與「跑模型」的差距

在 M1 上用 llama.cpp 的 server 模式起一個 8B Q4 模型，開 4 個並發 slot（`llama-server -m <model.gguf> -np 4 -c 16384`），用 k6 以 1 / 4 / 8 並發各打一輪 50 個請求。

**成功標準**：觀察到 (1) 並發 1→4 時總吞吐上升（它有基本的 batching）；(2) 並發 8 超過 slot 數後請求排隊、p95 延遲翻倍——但拿不到 preemption、KV usage、佇列深度這些指標，你只能瞎猜內部狀態。能用一段話說出「生產引擎賣的不只是吞吐，是可觀測性與可控性」，這個 lab 就值回票價。選配加分：SGLang 近期版本有 Apple Silicon MLX backend（2026），可試裝對照。

### Lab 3 [紙上推演]：三個選型題

對下面三個場景各寫 5 行內的選型決策與理由（引擎 + 關鍵理由 + 你最擔心的風險）：(a) 內部文件問答工具，10 QPS 峰值，一張 A10，團隊 2 人都是後端出身；(b) 對外 API 產品，流量 100% 是 JSON 工具呼叫，p95 TTFT < 800ms，8 張 H100；(c) 車載離線語音助理，模型固定兩年不換，硬體是車規 Orin。

**成功標準**：三題都用了「workload 形狀 → 引擎特性 → 團隊能力 → 代價」的完整鏈條，而不是「因為 X 比較快」。參考方向：(a) vLLM 預設解；(b) SGLang 與 vLLM 實測對比，結構化輸出是決勝點；(c) TensorRT-LLM 的定置炮台場景。

## 這個領域往哪走

引擎層的單點功能正在快速商品化：continuous batching、PagedAttention、prefix caching、P/D 支援——2026 年你已經很難靠「有沒有某功能」區分 vLLM 與 SGLang，連 TensorRT-LLM 都轉向 PyTorch backend 加入同一賽道。差異化正在往兩個方向移動：往下是 kernel 與數值格式的硬體貼合度（NVFP4、batch-invariant kernels），往上是路由與平台層的整合品質（誰跟 llm-d/Dynamo/IGW 接得最順，ch10/ch12）。對你的含意：學引擎要學機制與診斷方法（十年有效），參數表會過期（半年一版）；而「會用 benchmark 在兩個引擎之間做出有數據的選擇」這個能力，比押注任何一個引擎本身都耐久。

## 自我檢核

1. 畫出 vLLM V1 的 process 模型（TP=2 時共幾個 process、各做什麼），並解釋為什麼 tokenization 要放在 EngineCore 之外的 process。
2. 一個 stream=true 的 chat 請求從 HTTP 進到第一個 SSE chunk 出，依序經過哪些元件？TTFT 包含哪幾段時間？哪一段在 GPU 指標上看不到？
3. `--max-model-len` 設太大的兩種症狀是什麼？正確的設定依據是什麼？
4. 為什麼「8B FP16 換成 FP8」在 24 GB 的卡上吞吐提升遠超過 2 倍？拆出兩個機制來源（提示：固定成本 + KV pool）。
5. SGLang 相對 vLLM 最站得住腳的兩個差異點是什麼？為什麼「某引擎快 29%」這類數字不能直接拿來做選型？
6. TensorRT-LLM 1.2 把 PyTorch backend 設為預設，這個轉向說明了 compile 式引擎的什麼結構性弱點？什麼場景下 AOT compile 仍然划算？
7. 你的 vLLM `/health` 正常但所有請求 hang 住，給出至少兩個候選根因與各自的驗證方法。
8. 租卡實驗的成本紀律裡，為什麼 Terminate 和 Stop 的差別重要？為什麼建議用儲值制？

## 延伸閱讀

- [vLLM V1: A Major Upgrade to vLLM's Core Architecture（vLLM 官方 blog，2025-01）](https://vllm.ai/blog/2025-01-27-v1-alpha-release) — V1 架構的第一手設計說明：process 隔離、ZMQ、統一排程器，本章架構解剖的源頭。
- [vLLM 官方文件：Architecture Overview](https://docs.vllm.ai/en/latest/design/arch_overview/) — 元件名稱與 process 模型的權威版本，隨版本更新，讀碼前先讀它。
- [vLLM 官方文件：Engine Arguments](https://docs.vllm.ai/en/stable/configuration/engine_args/) — 本章參數表的上游事實來源；預設值以這頁（與 `--help`）為準。
- [Inside vLLM: Anatomy of a High-Throughput LLM Inference System（Aleksa Gordić）](https://www.aleksagordic.com/blog/vllm) — 第三方視角的 V1 完整解剖，配著本章「請求的一生」讀，然後就可以直接開原始碼了。
- [SGLang: Efficient Execution of Structured Language Model Programs（NeurIPS 2024）](https://arxiv.org/abs/2312.07104) — RadixAttention 與結構化輸出加速的原始論文，理解 SGLang 差異點的根。
- [SGLang GitHub](https://github.com/sgl-project/sglang) — release notes 是追蹤兩大引擎功能競賽的最佳一手材料；採用數字屬專案自述，閱讀時自帶折扣。
- [TensorRT-LLM 官方文件：PyTorch Backend 架構](https://nvidia.github.io/TensorRT-LLM/torch.html) — 1.x 世代轉向 PyTorch backend 的官方說明，理解「compile vs 彈性」取捨的現在進行式。
- [RunPod Pricing](https://www.runpod.io/pricing) — 租卡前必看；本章所有價格皆為 2026-06 快照，以此頁現價為準。
