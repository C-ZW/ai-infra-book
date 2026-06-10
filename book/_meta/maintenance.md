# 維護備忘（內部文件）

本書事實基準：2026-06-10（`landscape-2026.md`）。以下是寫作過程中各章作者回報的「已知脆弱點」，集中列管。

## 掃描協定（不定期執行）

本檔就是掃描的 index。執行一次掃描 =：
1. 對「月級變動」與「硬體預告」兩節逐條重新網路查證，更新 `landscape-2026.md` 並蓋新時點戳。
2. 凡基準數字有變（見一致性基準表），依表上的「引用章節」欄全數同步修改——不可只改一處。
3. 掃描後在本節底下記一行：`掃描於 YYYY-MM-DD：變更摘要 / 無變更`。
4. 建議節奏：動手做實驗前必掃對應條目；全書掃描每 1~3 個月一次即可（架構概念年級穩定，版本/價格才是月級）。

- 掃描於 2026-06-10：初版基準建立。
- 掃描於 2026-06-10（第二意見 agy/Gemini 帶網搜，抽查 8 條重大事實）：**修正 3 條**——NVIDIA×Groq 實為技術授權＋人才移轉而非股權收購（landscape/ch02/ch17/附錄B 已同步）；Cerebras 已於 2026-05-14 完成 Nasdaq IPO、上市估值 ~$56B（landscape/ch02/ch17 已同步）；TPU 8t/8i 獲 Google 官方確認、⚠️ 解除（landscape/ch17 已同步）。**確認無誤 5 條**：OpenAI 收購 Astral、Python 3.14 free-threading、Meta Muse Spark、K8s 1.36 Haru、DeepSeek-V4。

## 第二意見審查（2026-06-10，Gemini 3.5 Flash via agy）

**採納並已修正**：
- ch03 worked example 的 GB/GiB 單位混用——已加「三個刻意簡化」段（單位、block 碎片化、activation 動態性），標明 6 條為保守值、二進制重算約 7 條。
- ch06 缺 constrained decoding（structured output）對排程器的 CPU-bound 衝擊——已補一段（含防禦與監控建議）。
- ch07 FP4 表格易誤讀——已補「weight-only 在舊卡可跑（gpt-oss on H100）、原生計算才需 Blackwell」說明。

**評估後駁回（對方知識缺口或引用不存在的內容）**：
- 「llm-d 可能是幻覺專案」——錯誤。llm-d 為 2025-05 發起的真實專案（Red Hat/Google/IBM 等），研究階段有一手連結查證（landscape §4）。
- 「2026 年中社群焦點是 vLLM V2」——無任何佐證；2026-06 網路查證結果為 vLLM 0.22.x / V1 架構。
- 「ch17 表格宣稱 gpt-oss MXFP4 單張 H100 可跑是硬體常識錯誤」——書中 ch17 無此表格（引用了不存在的內容）；且該說法本身出自 OpenAI 官方（weight-only 路徑），非錯誤。

**採納為增補待辦（未修，屬深度擴充）**：
- ch09：RoCE v2 / PFC / GPUDirect RDMA 的網路層深度與 NCCL 網路面排錯（現有內容偏拓撲與通訊量帳）。
- ch11–16：非 NVIDIA 視角（ROCm/MI300 維運、TPU/XLA）偏薄——目前是有意取捨（NVIDIA 市占主導），但面向大廠面試可補一節「異質硬體的平台含意」。
- ch04：CUDA streams/events、tensor strides、PyTorch C++ 擴充——有意排除（plan.md 明言別過早鑽 kernel 層），若讀者後續走 performance 路線再補。
- ch12：eStargz 懶載入、GPUDirect Storage 可在 cold start 節補一句現況。

**第二輪（帶網搜）的增補建議（2026-06-10，評估後留檔）**：
- ch06/ch17：thinking 模型的長思考鏈對 decode 排程與 preemption 的專題——ch17 已有 reasoning 經濟學、ch06 已有 preemption 機制，缺的是兩者交叉的「為思考步驟做資源預留」一節，等業界實踐更收斂再寫。
- ch04/ch08：free-threading Python 對推論引擎 process 架構的影響（多進程 worker → 單進程多執行緒的可能演進）——目前是推測性方向，ch04 已涵蓋 free-threading 現況，引擎真的改架構時再補。
- 第二輪確認不需改的：Ingress NGINX → GIE 轉型（書本來就建立在 GIE 上）；Cerebras/LPU 生產部署（ch02/ch17 已涵蓋，數據已更新）。

## 月級變動、引用前先回查

- **版本號**：vLLM 0.22.x、SGLang 0.5.12、Dynamo 1.2、llm-d 0.6/0.7（寫作當下 GitHub 已見 0.7.0，正文用「0.6/0.7（2026 年年中）」hedge）、K8s 1.36、Kueue v0.17、LWS 0.8、KEDA v2.19/2.20。
- **GPU 租價**：全書一律「2026 年年中快照」級距（H100 ~$2.5/hr 級距）。ch01/ch03/ch08/ch09/ch13/ch16 引用。
- **API caching / batch 折扣**：caching 折扣各家來源矛盾（50–90% 區間寫法）；batch 50% 三家已查證。ch05/ch16/ch17。

## 硬體預告類（付印/引用前必回查）

- Rubin 世代、AMD MI400/Helios（H2 2026 預告）、NVLink 6 — ch02/ch17 已標「付印前回查」。（TPU 8t/8i 已於 2026-06-10 獲官方確認，移出本清單）
- Rubin CPX 擱置插曲（The Register 2026-06 一手）— ch17。

## 已知單一來源/未能完全查證（正文已 hedge）

- DeepSeek V4 cache 折扣 1/50–1/120（僅第三方）— ch05/ch17。
- NVIDIA GPU DRA driver 的 GA/experimental 狀態自相矛盾（releases vs README）— ch11。
- fake-gpu-operator 假 nvidia-smi 注入機制細節 — ch11 lab 有 fallback 說明。
- Vidur 維護動能存疑（PyPI 最後 release 2025-08）— ch13/ch18/附錄A 口徑一致：「研究級工具，可改手算」。
- xk6-sse 維護狀態、llm-d-inference-sim CLI 旗標 — 各 lab 標「以 repo README 為準」。

## 跨章一致性基準（改其中一處就要全改）

| 基準數字 | 值 | 引用章節 |
|---|---|---|
| Llama-3.3-70B KV per token | 320 KiB（BF16, GQA 8 heads） | ch01/03/05/09/10/13/17/18、附錄C |
| 32k context KV | 10.7 GB | ch03/10/13、附錄C |
| H100 SXM 規格 | 80GB / 3.35 TB/s / 989 TFLOPS BF16 dense | ch02/03/07/09、附錄C |
| Roofline 拐點（H100, BF16/FP8） | ~295 / ~590 FLOP/byte | ch02/03/07 |
| 70B 權重 | BF16 141.2 GB / FP8 71 GB / INT4 35.3 GB | ch03/07/09/12 |
| `gpu-memory-utilization` | 「0.90~0.92 隨版本」統一口徑；ch03/11 用 0.90 計算、ch08/13 用 0.92 | 2026-06-10 已修一致 |
| SLO 分位數 | ch13 容量題 p95、ch14 goodput 示範 p99——差異已在 ch14 明文標註 | 2026-06-10 已修 |

## 結構性提醒

- **網頁閱讀器（`web/index.html`）是產生物，不要手改**——由 `python3 web/build_reader.py` 從 book/ 重新打包（章節內容更新後必須重跑）。ASCII 圖改動後先跑 `python3 web/check_diagrams.py` 驗證對齊（規則：CJK=2 欄）。
- **閱讀器字型假設 Apple 平台**：對齊修正用 `size-adjust:120.4%` 把 PingFang 縮放成 Menlo 半形的 2 倍，比例是按 Menlo 算的——在沒有 Menlo/PingFang 的裝置（Windows/Android）上圖會微歪（內文不受影響）。換平台時需重算比例或改 bundle 等寬 CJK 字型（如 Sarasa Mono TC）。

- 附錄 A 的時間估計欄多為彙整者推估（非各章原文）——章節 lab 改版時附錄 A 需重新核對。
- 附錄 C 是一致性的放大器：正文公式/參數改動，C.1/C.2 必須同步。
- ch13 的 worked example 依賴 ch14（benchmark 方法論）與 ch15（drain 數學）的範圍不變。
