# 附錄A — 動手實驗總表

> 全書 18 章共 52 個實驗：23 個 **[M1]**（免費）、6 個 **[租 GPU]**（章內標注合計約 $29–51）、23 個 **[紙上推演]**（零成本）。本附錄把它們重組成三條漸進軌道＋一份紙上推演合集。每列標注來源章節、目標、硬體、成本、時間與成功標準摘要；具體指令骨架、故障排除與完整成功標準以各章「動手做」原文為準。成本皆為各章 2026-06 價格快照；時間欄除 ch11、ch14 Lab 3 為章內標注外，其餘是本附錄的估計值。

## 建議執行順序

1. **紙上推演邊讀邊做，不要堆積**。零成本、零環境，而且它們是後面花錢實驗的驗算器——先會手算 KV 牆（ch03/ch06），再去租卡看 preemption 計數，你才知道實測數字對不對。
2. **Track 1 本地模型系列照章節順序走**（ch01→ch08）：建立 TTFT/ITL 體感，練熟 llama.cpp 與 k6——這兩樣是之後所有 benchmark 的工具底。
3. **Track 1 模擬叢集系列以 ch11 為地基**：64 卡模擬叢集做成一鍵 `setup.sh`，ch13/ch15 的實驗直接長在上面；ch05/ch06/ch14 的 sim 實驗只需 docker，可提前獨立做。
4. **Track 2 租卡實驗集中打**：等 Track 1 的腳本全部演練過再開卡，並照表後的「併 session 建議」省錢。
5. **Track 3 收尾**：P/D 路由、平台組裝、可靠性演練全是免費模擬，先做完；唯一的多卡實測（ch09）放在最後一次租卡。
6. **ch17/ch18 的實驗對齊求職時程**：流量畫像、履歷翻譯、模擬面試、開源迴圈，在開始投遞前完成。

## 成本控制紀律（開卡前默念）

- **先寫好再開卡**：指令、benchmark 腳本、記錄表格全部在 M1 上演練過才租卡。計費時間裡只跑實驗，不查文件。
- **Terminate，不是 Stop**：Stop 通常仍收儲存費；每次做完到 billing 頁面確認歸零（ch08 的閉環把這列入成功標準）。
- **儲值制＋預算警報**：用可儲值的平台（RunPod/Vast 級距），先設警報再開卡（ch06/ch08）。
- **一次 session 一個目標**：開卡前寫下「這次要帶走哪張表」，拿到就關機。
- **用對等級的卡**：8B 模型用 L4/A10（約 $0.5–1.0/hr）就夠；只有 FP8 對比（ch07）需要 Hopper/Ada 以上，多卡實測（ch09）才需要同節點 NVLink。

## Track 1【M1 免費】

硬體全程 M1 MacBook，成本 $0。

### 本地模型系列（對應 plan.md 模組一）

| 來源 | 實驗 | 目標 | 時間 | 成功標準（摘要） | plan.md |
|---|---|---|---|---|---|
| ch01 Lab 2 | Ollama + SSE streaming 觀察 | 親手量 TTFT/ITL，體感 cold start 與 prefill/decode 分野 | 1h | 不看書答出：TTFT/ITL 是什麼、長 prompt 為何只拖慢 TTFT、首次請求為何特別慢 | 模組一 |
| ch02 Lab 2-2 | llama-bench 驗證 decode 上限公式 | 用統一記憶體頻寬驗證「上限＝頻寬÷模型大小」，反推 MBU | 1–2h | Q4/Q8 tok/s 比值與檔案大小反比誤差 <20%；有效頻寬落在規格 50–80% | 模組一 |
| ch03 Lab 1 | llama-bench 量 prefill/decode 不對稱 | pp 與 tg 差 1–2 個數量級的實測 | 1h | 能用 arithmetic intensity 解釋差距；decode 達理論值 60–85% 並能解釋缺口 | 模組一 |
| ch03 Lab 3 | tokenizer 十分鐘體感 | 三種文本的 chars/token 比 | 0.5h | 能說出 token 計量對中英文「不公平」與 gateway 計量的含意 | 模組一 |
| ch04 Lab 4-1 | FastAPI streaming proxy + k6 | 寫出 OpenAI-compatible SSE proxy 並打併發 | 2–3h | 20 VU 零 5xx；log 整理出 TTFT p50/p95，能解釋 TTFT 隨併發上升的原因 | 模組一 |
| ch04 Lab 4-2 | py-spy 抓 blocking bug | flame graph 定位被佔住的 event loop | 1h | 指出 sleep frame 與占比；改 async 後吞吐恢復且能解釋 | 模組一 |
| ch07 Lab 7-1 | Q4 vs Q8 量化對比 | 驗證「量化加速的是 memory-bound 部分」＋品質肉眼校準 | 1–2h | tg 比 ≈ 大小反比、pp 差距明顯小；Q4 數學錯誤率可見較高 | 模組一 |
| ch07 Lab 7-2 | speculative decoding 體感 | 複述 vs 原創兩種任務的 acceptance 差異 | 1h | 複述任務的 acceptance 與加速顯著較高——α 是流量的函數 | 模組一 |
| ch08 Lab 2 | llama-server 並發體感 | 「引擎」與「跑模型」的差距 | 1–2h | 並發 1→4 吞吐升、8 開始排隊；能講出生產引擎賣的是可觀測性與可控性 | 模組一 |
| ch17 Lab 2 | 量自己的 agentic 流量畫像 | 從 coding agent 用量算 input:output 比、cache 價值、KV 峰值 | 1h | 產出流量畫像表＋三條「會改變哪些設計決策」 | 模組六 |

### 模擬叢集系列（對應 plan.md 模組二，旗艦專案①）

| 來源 | 實驗 | 目標 | 時間 | 成功標準（摘要） | plan.md |
|---|---|---|---|---|---|
| ch05 Lab 1 | llm-d-inference-sim 觀察 prefix caching 指標 | 把「命中率作為一級指標」摸一遍 | 1h | 指出 KV 使用率指標、哪兩個指標相除是命中率，解釋兩組流量的差異 | 模組二 |
| ch06 實驗 2 | sim + k6 飽和曲線 | 三檔 `max-num-seqs`（16/64/128）的併發-吞吐曲線 | 1–2h | 看到吞吐在併發超過 max-num-seqs 後平頂、延遲線性堆積 | 模組二 |
| ch11 Lab | kind+KWOK+fake-gpu-operator 64 卡模擬叢集 | 旗艦①地基：排程、碎片化、bin-packing、Kueue 配額與搶占、MIG（選做） | 半天–1天 | 碎片化重現（56 閒卡仍 Pending）且 binpack 後可排；能用 event 講出 Kueue 借用-回收因果鏈 | 模組二｜旗艦① |
| ch14 Lab 1 | sim + Prometheus + Grafana 全套監控 | 六面板 dashboard＋「飽和」「cache 退化」兩種事故演練 | 2–4h | 兩種事故都能在 30 秒內定位到正確的層 | 模組二｜旗艦① |
| ch14 Lab 2 | k6 SSE benchmark 腳本 | open vs closed loop、coordinated omission | 2h | 展示兩種模式 p99 差異並解釋；驗證 chunk 數 ≠ completion_tokens | 模組二 |
| ch18 Lab 3 | 第一個開源迴圈（llm-d-inference-sim 或常用專案的 docs） | issue→溝通→PR→review 完整生命週期 | 數天（零碎） | 收到至少一輪 maintainer 實質回饋並完成修改 | 模組五/六 |

## Track 2【單卡租用】— 總預算 $30–50

對應 plan.md 模組四（旗艦專案③）。章內標注合計 $21–36，預算餘量留給重跑與失誤。前置條件：Track 1 的腳本與記錄表已演練。

| 來源 | 實驗 | 目標 | 硬體 | 成本 | 時間 | 成功標準（摘要） | plan.md |
|---|---|---|---|---|---|---|---|
| ch05 Lab 2 | prefix caching 開關 TTFT 對比 | 量化 cache 命中的 TTFT 價值 | L4/A10 | $3–5 | 2h | 兩輪 TTFT 中位數差距能用機制解釋；/metrics 驗證確實命中 | 模組四 |
| ch06 實驗 3 | `max-num-seqs` 三檔（16/64/256）對比 | 找 KV 牆與「餵不飽」區 | L4/A10 | $3–5 | 2h | 三檔對比表；指出哪檔 preemption 計數走動、哪檔 waiting>0 但 running 偏低 | 模組四 |
| ch08 Lab 1 | 部署＋三組配置＋benchmark 完整閉環 | 旗艦③核心：實測表 vs 推算表並排 | L4 | $5–10 | 3–4h | 配置×指標表；偏差 >±30% 的格子有機制解釋；指出哪組撞 KV 牆；billing 歸零 | 模組四｜旗艦③ |
| ch07 Lab 7-3 | FP8 vs BF16 誠實對比 | 「曲線＋eval 雙證據」的優化決策模板 | H100/L40S | $5–8 | 3h | 兩條可疊放曲線＋GSM8K 取樣分數；一段話講清換到什麼、付出什麼 | 模組四｜旗艦③ |
| ch14 Lab 3 | latency-throughput frontier | goodput@SLO 的完整量測 | H100/A100 | $5–8 | 2–3h | frontier 圖＋goodput 數字＋offered/achieved 對照；指出無效（飽和）點 | 模組四｜旗艦③ |

**併 session 建議**：ch05 Lab 2 與 ch06 實驗 3 用同級卡（L4/A10）跑同級 8B 模型，可併成一次租卡（先跑 ch06 三檔、再跑 ch05 兩輪，約 3–4 小時、$4–6 帶走兩章的數據）。ch07 與 ch14 需要較貴的卡，各自獨立 session、目標單一。

## Track 3【多卡／進階】— 總預算 $30–60

對應 plan.md 模組五（旗艦專案④）。先把免費的進階模擬全部做完；唯一必花錢的是 ch09 的 TP2 實測（$8–15），預算餘量留給多卡機型加價、NCCL 排錯時間，以及（選做）把 ch08 的閉環在 TP2 配置上重跑一輪當旗艦④的量化素材。

| 來源 | 實驗 | 目標 | 硬體 | 成本 | 時間 | 成功標準（摘要） | plan.md |
|---|---|---|---|---|---|---|---|
| ch10 Lab 10-1 | sim×2＋自寫 50 行路由器 | round-robin / sticky / prefix-aware 的 TTFT 差異；熱點失控重現 | M1 | $0 | 2–3h | prefix-aware 的 p99 顯著優；閾值調 0 後熱點爆掉、p99 反超 round-robin | 模組五｜旗艦④ |
| ch12 實驗 1 | kind + GIE gateway + sim 體驗 InferencePool | gateway→EPP→pod 的路由實跑 | M1 | $0 | 2–4h | 畫出實際路徑並以 EPP log 佐證；負載導流有效；答出 fail-open/closed 並驗證 | 模組五｜旗艦④ |
| ch12 實驗 2 | nginx SSE buffering 偵錯演練 | 量化「buffer 不改吞吐、只毀 streaming 體感」 | M1 | $0 | 1h | 修復前後各一段逐 token 到達時間戳 | 模組五 |
| ch13 Lab 1 | KEDA 佇列驅動 autoscaling 全迴路 | 量 T_react、用自己的數據驗證 headroom 公式 | M1 | $0 | 2–3h | 指出「佇列堆積→新 replica 就緒」的時間差；minReplica 2→4 對 p95 的改善 | 模組二→五｜旗艦① |
| ch15 實驗 1 | kill pod 與 preStop drain 演練 | 暴力 vs 優雅下線的 client 端對比 | M1 | $0 | 1–2h | 優雅版零傷亡；grace period 數字能用時長分布公式推出 | 模組五｜旗艦④ |
| ch15 實驗 2 | 親手製造 retry storm | 兩道防禦前後的 offered load vs goodput 曲線 | M1 | $0 | 1–2h | 第一輪 goodput 過載後下降、第二輪持平，能解釋機制 | 模組五｜旗艦④ |
| ch16 實驗 2 | token-denominated rate limiter | reserve/settle 兩階段限流＋noisy neighbor 隔離 | M1 | $0 | 2–4h | tenant-B 收到 429 而 tenant-A p95 不受影響；斷線 settle 對帳正確；Redis 故障行為如設計 | 模組五｜旗艦④ |
| ch09 Lab 2 | TP2 實測 vs 單卡 | TP 的 ITL 收益與 α 稅；NCCL 拓撲確認 | 2×A100 80GB 或 2×H100（同節點 NVLink） | $8–15 | 2–3h | 能答「ITL 為何不是理想的 2 倍」；並發 1 與 32 的增益差異及原因；用完即關 | 模組五｜旗艦④ |

## 【紙上推演】合集（零成本，邊讀邊做）

對應 plan.md 模組三的效能建模能力（旗艦專案②的素材庫）與模組六的求職產出。注意：ch13 Lab 3 的 Vidur 維護動能存疑（2026-06），章內已建議可改手算。

| 來源 | 題目 | 產出 | 時間 | plan.md |
|---|---|---|---|---|
| ch01 Lab 1 | 自己的技能遷移矩陣 | 一頁表格（ch18 改履歷直接複用） | 1h | 模組六 |
| ch02 Lab 2-1 | 三張卡 roofline 拐點＋70B decode 上限 | 拐點、理論 tok/s、H200 對 prefill/decode 的不對稱提升 | 1h | 模組三 |
| ch03 Lab 2 | 三模型 KV 公式（8B/70B/MLA） | 每 token KV、128k 帳單、69 GB 池的併發數 | 1h | 模組三 |
| ch04 Lab 4-3 | 讀 vLLM forward 推 tensor shape | 找出 GQA 的 head 數分岔與 KV cache 入口 | 1h | 模組一 |
| ch05 Lab 3 | 重算 agentic prefix cache 帳 | 變因敏感度結論（輪數那項是平方級） | 0.5–1h | 模組三 |
| ch06 實驗 1 | 8k context 重算 batch 曲線 | 甜蜜點與 KV 牆的位移 | 1h | 模組三 |
| ch07 Lab 7-4 | acceptance rate 與高 batch 判決 | 兩種服務的 γ 選擇與辯護 | 1h | 模組三 |
| ch08 Lab 3 | 三個引擎選型題 | 各 5 行的「workload→引擎→團隊→代價」決策鏈 | 1h | 模組四 |
| ch09 Lab 1 | 405B 與 1T 級 MoE 平行配置設計 | 切法、記憶體帳、每 token 通訊量 | 1.5h | 模組三 |
| ch09 Lab 3 | TP 通訊預算 3×3 表 | 「TP 不出節點」的數字論證 | 0.5h | 模組三 |
| ch10 Lab 10-2 | 三種流量形態的 xPyD 配比 | 配比＋辯護（短問答的正解是不分離） | 1h | 模組五 |
| ch10 Lab 10-3 | 搬 KV vs 重算的 crossover | 8B＋小 context 下結論為何翻轉 | 1h | 模組三 |
| ch11 紙上推演 | MIG 的 roofline 帳 | 「要不要切 MIG」的決策框架 | 0.5h | 模組二 |
| ch12 實驗 3 | 「5 團隊 20 模型」平台設計文件 | 一頁架構＋冷啟動策略＋故障預判（ch18 面試題的書面草稿） | 2h | 模組六｜旗艦④ |
| ch13 Lab 2 | RAG workload 容量規劃 | 卡數、headroom、月成本三個數字 | 1.5h | 模組三｜旗艦② |
| ch13 Lab 3 | 配置空間搜索（Vidur 或手算） | 三配置對照表＋「什麼新資訊會讓我改變主意」 | 2h | 模組三｜旗艦② |
| ch15 實驗 3 | 「凌晨三點 TTFT 告警」判斷樹 | 同事可盲走的 runbook | 1.5h | 模組五 |
| ch16 實驗 1 | build vs buy 決算 | 三案月成本＋crossover＋200 字建議書 | 2h | 模組六 |
| ch16 實驗 3 | 內部價卡設計 | 三費率可驗算回全成本＋headroom 歸屬辯護 | 1h | 模組五 |
| ch17 Lab 1 | 「P/D 分離會不會被硬體淘汰」辯論 | 正反各 200 字＋有改變立場條件的裁決 | 1h | 模組六 |
| ch17 Lab 3 | hybrid attention 重算 KV 帳 | 驗證「KV 減約 75%」量級 | 1h | 模組三 |
| ch18 Lab 1 | 履歷翻譯三條 bullet | 每個關鍵字可被追問三層 | 1h | 模組六 |
| ch18 Lab 2 | 45 分鐘模擬面試（錄音） | 六段全覆蓋、容量數學正確的作答 | 1.5h | 模組六 |

## 旗艦專案對應總覽

| plan.md 旗艦專案 | 核心實驗 | 補充素材 |
|---|---|---|
| ① 模擬推論叢集 | ch11 Lab（地基）、ch13 Lab 1（autoscaling 進階） | ch05 Lab 1、ch06 實驗 2、ch14 Lab 1/2 |
| ② 配置權衡研究 | ch13 Lab 2/3 | ch02 Lab 2-1、ch03 Lab 2、ch06 實驗 1、ch09 Lab 1/3 |
| ③ vLLM 推論優化 | ch08 Lab 1（量測→診斷→優化→驗證閉環） | ch05 Lab 2、ch06 實驗 3、ch07 Lab 7-3、ch14 Lab 3 |
| ④ 多模型／多節點平台 | ch12 實驗 1＋實驗 3、ch10 Lab 10-1 | ch09 Lab 2、ch15 實驗 1/2、ch16 實驗 2、ch18 Lab 3 |

最後三個省工提示：ch02 Lab 2-2、ch03 Lab 1、ch07 Lab 7-1 共用同一組 GGUF 檔（8B 的 Q4_K_M 與 Q8_0），下載一次、一個下午連做三章；模擬叢集是資產不是耗材——ch11 搭好的 `gpu-sim` 直接承載 ch13，ch12 的 `igw-lab` 直接承載 ch15，砍掉重練是最大的隱性時間成本；所有租卡實驗的產出物（對比表、frontier 圖、billing 截圖）當場存檔——它們就是 ch18 作品集的素材，關機之後就沒有第二次了。
