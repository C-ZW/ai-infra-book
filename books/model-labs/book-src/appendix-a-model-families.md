# 附錄 A — 八家模型家族速查表

> ⚠️ **本表為截至 2026-06 的快照，版本與排名每幾個月就會過期；最新狀態請重查，判斷方法見全書（尤其 ch04 評測、ch21 五變數）。** 這是全書**最易腐壞的一頁**——表裡每一個版本號、上下文長度、GPU/TPU 數量、訓練成本、參數量級都帶日期戳，過了 2026-09 多半已不準。請把這頁當「2026-06 的一張定格照」，不是定律；要判斷一款新模型，回去用 ch03 的五變數記分卡與 ch04 的評測誠實框架自己拆，而不是背這張表的某一格。

## 怎麼讀這張表

- **無絕對排名**：本表刻意不選「誰最強」。每一格的「招牌強項」都是 reputation／consensus 層級（🟡），意思是「截至 2026-06 以…著稱」，不是「就是最好」。誰在哪個 benchmark 領先每幾個月洗一次牌（ch04），唯一穩定的是各家的**風格與取向**（ch21）。
- **信心標記**（沿用 landscape 與全書）：
  - ✅ **已確認**——有原始來源（lab blog、arXiv、有引用的 Wikipedia）或多個獨立次級來源一致。
  - 🟡 **聲譽／共識**——廣為相信、難以 A/B 證明、會隨時間漂移（如「Claude 以 coding 著稱」）。
  - ⚠️ **未證實／有爭議／單一來源／快速變動**——數字被質疑、只追得到次級彙整、或前瞻性宣布尚未出貨。
- **爭議數字一律雙呈**：凡標「自我宣稱／有爭議」者（DeepSeek 訓練成本、各家 GPU/TPU 數量、Colossus 規模、Grok 5 參數量），都同時給「主張值」與「但書」，不要把宣稱值當裸事實引用。

## 主表：八家 × 六欄（截至 2026-06）

> 「招牌技術」「算力來源」「招牌強項」三欄是相對穩定的結構性事實；「當前主要模型」「上下文長度」兩欄最易過期。

| 家 | 當前主要模型（標日期戳） | 上下文長度 | 開放/閉源（授權） | 招牌技術 | 算力來源 | 招牌強項一句話（🟡 截至 2026-06 以…著稱） |
|---|---|---|---|---|---|---|
| **OpenAI** | 🟡 GPT-5 家族；GPT-5.5 為複雜推理/coding 旗艦（released 2026-04-24），預設走「Instant」、可升「Thinking」；mini/nano 小型變體 ⚠️ 點版號命名混亂 | ⚠️ 隨變體而異，未統一公開 | 閉源（API/ChatGPT，權重不可下載） | RLHF 規模化（InstructGPT 血統）→ 開創 reasoning 範式（o1, 2024-09）；統一 router ＋ reasoning-effort 旋鈕（none/low/medium/high/xhigh）✅ | Azure（曾獨家）＋ 自建 **Stargate**（$500B/4yr、>10GW 目標，⚠️ headline 數字、有挫折） | 最廣的通用能力＋消費端霸主＋開創 reasoning。因為先發 RLHF-chat（ChatGPT）與 RL-reasoning（o1）、最深的 Azure 算力、最大用戶基數餵產品迭代。 |
| **Google DeepMind** | ✅ Gemini 3（2025-11-18）、Gemini 3.1 Pro（2026-02-19）；🟡/⚠️ Gemini 3.5 Pro 於 I/O 2026-05-19 揭露、GA 目標 2026-06、宣稱 2M-token context（截至 2026-06-09 未 GA、無獨立 benchmark） | 🟡 1.5 Pro 已實證 2M（2024）；3.5 Pro 宣稱 2M（headline ambition）。長上下文是真招牌 | 閉源 Gemini（並行開放權重 Gemma） | 原生多模態＋長上下文＋Deep Think 推理；TPU 垂直整合（DeepMind 與 TPU 工程師共同設計）✅ | **自研 TPU**（Ironwood=TPU v7，GA ~2025-11，pod 9,216 chip；TPU 8 前瞻）⚠️「10M TPU」為量級非審計 | 長上下文＋原生多模態＋深厚研究底。因為 TPU 垂直整合（自有晶片→訓最大、服務最便宜）、AlphaGo/AlphaFold 的 RL 與科學 DNA、要服務 Search 的行星級效率壓力。 |
| **Anthropic** | ✅ Claude Opus 4.8（2026-05-28）、Sonnet 4.6（2026-02-17）、Haiku 4.5（2025-10-15）；🟡 Fable 5＋Mythos 5（2026-06-09）⚠️ Fable 5 於 2026-06-23 從訂閱方案下架（報導為容量限制、非安全事件）、改用量計費，極新易變 | 未在本表統一列（隨方案/變體而異） | 閉源（Mythos 5 限 Project Glasswing） | **Constitutional AI / RLAIF**（Bai et al. 2022, arXiv:2212.08073）；interpretability 研究（sparse autoencoder、circuit tracing）✅ | **多雲**：AWS Trainium 為主（Project Rainier ~500k Trainium2、用量 >1M、up to 5GW＋$100B）＋ Google TPU（up to 1M，2025-10 deal）✅ 既非自研晶片亦非主靠 Nvidia | coding/agentic 可靠度＋安全與可解釋性縱深。因為 Constitutional AI/RLAIF 讓對齊少靠人工標註而能規模化、異常深的 interpretability 研究底、刻意的多雲（Trainium＋TPU）算力。 |
| **Meta** | ✅ Llama 4 herd（2025-04：Scout/Maverick，首個原生多模態＋MoE Llama）；⚠️ Llama 4 Behemoth（~2T）宣布未出貨、實質擱置；✅ **Muse Spark**（2026-04-08，Meta Superintelligence Labs/Alexandr Wang）——首個**閉源**前沿模型，權重不可下載 | 🟡 Llama 4 Scout 宣稱 up to 10M-token context | ⚠️ **2026 開→閉轉向**：Llama 開放權重（社群授權，>700M MAU 需另授權、原禁 EU）；前沿改走閉源（Muse Spark 不可下載） | MoE Llama＋原生多模態；Muse Spark 宣稱 parallel reasoning／「thought compression」⚠️ | ✅ 龐大 Nvidia H100 fleet（~350k H100，⚠️ 2024-era 目標）；2026 capex ⚠️ ~$115–135B | 締造了開放權重生態（Llama），2026 轉向閉源前沿（Muse Spark）。因為開放權重給了觸及/善意/研究飛輪，但前沿成本暴漲、怕對手搭便車、3B 用戶平台變現的拉力，在 2026 翻轉了戰略。⚠️ 全書最「新而意外」的轉折，標為 2026 inflection、非定局。 |
| **Mistral AI** | ✅/🟡 Mistral Large 3（2025-12，旗艦開放權重 sparse MoE ~675B total/~41B active）；🟡 Mistral Small 4（2026-03-16，統一 reasoning/vision/coding）；Mistral Forge（GTC 2026-03，企業自訓平台） | ✅ Large 3：256K context | **開放權重（Apache 2.0）**——比 Llama 授權更寬鬆 | 效率優先的 sparse MoE（~41B-dense 成本存取 675B 容量）✅ | Nvidia（歐洲主權 DC）：~13,800 GB300（巴黎，~Q2 2026）、~18,000 Grace Blackwell（法國）🟡 | 高效率、真開放（Apache-2.0）的 MoE＋歐洲主權。因為小團隊拚效率不拚蠻力、Apache-2.0 開放度差異化（對比 Llama 受限授權）、EU 對非美依賴的「主權 AI」需求。 |
| **xAI** | 🟡/⚠️ Grok 5——Musk 宣布 Q1-2026 目標、**reported ~6T params（MoE）**、宣稱「史上最大公開模型」，於 Colossus 2 訓練 ⚠️ **參數量與出貨狀態為 Musk/媒體說法，自我宣稱/有爭議** | （未公開穩定數字） | 閉源（Grok 隨 X 產品迭代） | 速度取向；native 即時 X（Twitter）語料是結構性差異化✅ | **自建 Colossus**（Memphis）⚠️ reported ~555k GPU、~2GW（Colossus 1 ~230k operational＋Colossus 2 首批）**自我宣稱/有爭議、快速變動**；5 年目標 50M「H100-等效」by ~2030（aspirational） | 後發者的加速度：速度堆規模＋即時資料＋蠻力算力。因為自建 Colossus（全球數一數二 GPU 叢集）能快速暴力訓練、特權存取 X firehose 給 Grok 對手得外接才有的即時性。 |
| **DeepSeek** | ✅ DeepSeek-V3（2024-12, arXiv:2412.19437，MoE 671B total/37B active）、R1（2025-01-20，開放權重推理，引爆市場）；🟡 DeepSeek-V4（Pro+Flash，reported 2026-04-24，MoE ~1M context，2026-05-22 起 75% V4-Pro 折扣永久化）⚠️ 次級來源、快速變動 | 🟡 V3：256K；V4：reported ~1M context | **開放權重** | **MLA（Multi-head Latent Attention，砍 KV cache）**＋ **GRPO（省掉 reward model 的 RL）**＋ MoE＋MTP＋FP8＋auxiliary-loss-free 平衡 ✅ | ⚠️ 受出口管制的 Nvidia（H800），數千張 H800 級別、保密 | 前沿級品質、開放權重、成本只是零頭。因為一疊效率發明（MLA/GRPO/MoE/MTP/FP8）源於算力稀缺（被管制的 H800）逼出的演算法巧思，把限制變護城河、重設產業成本預期。⚠️ 著名的 **~$5.6M 只是「最後一次預訓練」的 GPU 時數**（2.788M H800 GPU-hour），不含研發/薪資/硬體/失敗 run；批評者估全程 all-in ~$1.3B/$1.6B——**自我宣稱/有爭議**，雙呈勿簡化（記者常把 V3 的 $5.6M 誤掛到 R1）。 |
| **Alibaba Qwen** | ✅ Qwen3（2025，hybrid-reasoning，119 語言，0.6B→480B 全尺寸梯，含 MoE Qwen3-235B-A22B/Qwen3-30B-A3B）；🟡 Qwen3.5（2026-02-16）、Qwen3.6-Plus（2026-04-02）、Qwen3.6-35B-A3B 開放權重（2026-04-17）⚠️ 點版號每月變 | （隨尺寸/版本而異，未統一列） | **開放權重（多為 Apache 2.0）**＋ 託管 API（Model Studio） | 全尺寸梯（edge→datacenter）＋多語言（119 語言）＋hybrid reasoning（可開關 thinking）✅ | ⚠️ Alibaba Cloud，規模未公開 | 最廣的開放權重尺寸梯＋多語言縱深。因為 Alibaba Cloud 要播種生態的商業誘因（每個裝置層級都出一款）、深厚中文/亞語資料、積極開放權重釋出驅動 Hugging Face 主導性的分發策略。 |

## 兩個必讀的補充註記

- **Meta — 2026 的開→閉轉向（Muse Spark）**：這是本表唯一帶「戰略反轉」的一格，也是全書最戲劇化的個案（ch08）。Meta 七年來以「前沿開放權重」立身（Llama 締造了 fine-tune/on-prem/研究飛輪的龐大生態），但 **2026-04-08 推出的 Muse Spark 是首個閉源前沿模型，權重不可下載**，現已驅動 Meta AI app。成因（landscape）：前沿訓練成本暴漲（⚠️ 2026 capex 估 ~$115–135B）、怕中國廠商靠 Llama 搭便車、要靠 3B 用戶平台＋專有資料變現。⚠️ 標為 **2026 inflection、非定局**——是否站穩、會不會再出新的開放 Llama，都是 2026-09 前要重查的項目。對應全書「強項的影子會應驗」：送出權重＝送出部分護城河，這個 ch01 預告的影子在 2026 兌現了。

- **OpenAI — 點版號命名很亂，抓住耐久事實**：GPT-5.3 Instant / 5.4 Thinking / 5.4 Pro / 5.5 / 5.6 這些子版號在各家彙整裡彼此矛盾、每幾週變動（⚠️）。**不要把任何單一點版號當穩定事實**。耐久、可安心引用的結構性事實是三件：(1) 全部收斂進 **GPT-5 家族**（2026-02-13 退役 GPT-4 與獨立 o-series）；(2) **統一 router** 自動在「Instant（淺）」與「Thinking（深）」之間升降；(3) **reasoning-effort 旋鈕**（none/low/medium/high/xhigh）讓你按需調思考深度。記住這三件，比追任何一個點版號都耐用。

## 重查提醒（最易腐壞的格子）

> 以下每格幾乎確定在 2026-09 前過期，引用前必重查（對應 landscape 的 fragile-facts 清單）：

- 各家**當前旗艦版本號**與**排行榜名次**（每幾個月變）。
- Gemini 3.5 Pro 的 **GA 狀態**＋2M context 是否真出貨＋真實 benchmark。
- Anthropic **Fable 5 / Mythos 5**（2026-06 極新）——Fable 5 是否回到訂閱方案（2026-06-23 因容量下架）。
- Meta **Muse Spark** 閉源轉向是否站穩、是否有新開放 Llama。
- **DeepSeek V4/R2** 的定價（75% 永久折扣）與是否出新 R 線推理模型。
- **Qwen 點版號**（3.5/3.6/3.7-Max 每月變動）。
- **xAI Grok 5** 出貨狀態＋6T 參數宣稱＋Colossus GPU 數（全為 Musk/媒體來源）。
- **所有 GPU/TPU 數量級**——每一個都是爭議/自我宣稱。
- **所有 benchmark 數字/排名**——飽和又洗牌，永遠不要把某張排行榜定格進敘述。
- **DeepSeek 成本數字**——保持「$5.6M＝最後一次預訓練 GPU only；all-in ~$1.3–1.6B；有爭議」的雙呈框架，別讓「$5.6M 造出前沿模型」偷渡成裸事實。
