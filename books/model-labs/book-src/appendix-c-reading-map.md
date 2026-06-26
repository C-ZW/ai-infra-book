# 附錄 C — 延伸閱讀地圖

這份地圖把全書 21 章引用過的真實連結，依**主題與閱讀路徑**重新排好，方便你「想深挖某一格」時直接找對源頭。每條都標了**為什麼讀、讀哪一段、它支撐哪一章**。連結全部來自各章 `## 延伸閱讀` 與本書內部基準檔 `landscape-2026-06` 的「Master source list」，沒有憑空生出的網址。

**先講最重要的一句話：時效性連結會失效。** 版本號、價格、GPU 數量、排行榜名次每幾個月就洗一次牌（landscape Part 3 列了 12 條最易過期的事實）；本書是**截至 2026-06** 的快照。所以這份地圖的用法不是「背網址」，而是：**記住作者與主題，連結爛了就用作者名＋論文名去找最新版**。原始論文（arXiv、lab 官方部落格）最耐久，二手彙整（tech-press、aggregator）最易爛——優先點前者。

兩把「耐久的思考工具」貫穿全書，讀任何新材料時都先架上：

- **ch04〈評測判讀〉**——任何「X 在某 benchmark 第一」的新聞，先用這章的污染／飽和／三角驗證濾一遍，再決定信不信。
- **ch21〈五變數總帳〉**——看到任何新模型發表，先用這張記分卡（資料／後訓練·對齊／算力·基礎設施／研究文化·品味／產品取向）自己歸因，別等別人下結論。

框架耐久、數字會爛——這兩章是你讀完書後唯一需要隨身帶的東西。

---

## 只讀 5 樣的最短路徑（耐久一手論文優先）

如果你只想讀 5 樣東西，讀這 5 篇——它們是全書因果鏈的承重牆，而且都是不會幾個月就過期的一手論文：

1. **〈Attention Is All You Need〉(2017)** — https://arxiv.org/abs/1706.03762 ——全書那張「共用藍圖」的本尊。讀摘要與圖 1，親眼確認它真的是一篇任何人都能下載的公開論文。
2. **Chinchilla, "Training Compute-Optimal LLMs" (2022)** — https://proceedings.neurips.cc/paper_files/paper/2022/file/c1e2faff6f588870935f114ebe04a3e5-Paper-Conference.pdf ——「模型是養出來的」與 scaling laws 的最佳實例：同樣算力、餵飽的小模型贏。
3. **InstructGPT (RLHF), Ouyang et al. (2022)** — https://arxiv.org/abs/2203.02155 ——對齊演化線的起點，ChatGPT「聽話、好用」性格的方法源頭。
4. **OpenAI, "Learning to reason with LLMs" (o1, 2024-09)** — https://openai.com/index/learning-to-reason-with-llms/ ——reasoning 範式（test-time compute）的第一手起點，2024 年底以來最大的範式轉移。
5. **DeepSeek-V3 Technical Report (2024)** — https://arxiv.org/abs/2412.19437 ——「效率即護城河」最被引用的一手報告（MLA、MoE、FP8）；同時是 ch11「560 萬美金正確讀法」的原始出處。

讀完這 5 篇，你已經握住全書四個主張的硬證據；其餘按下面主題挑著補。

---

## 地基：架構與 scaling（支撐 ch01／ch02／ch03／ch16）

模型是「養」出來的、架構是公開的同一張藍圖——這一組是全書地基。

- **〈Attention Is All You Need〉(Vaswani et al., 2017，arXiv:1706.03762)** — https://arxiv.org/abs/1706.03762 ——那張共用藍圖。讀摘要與架構圖即可，重點是體會「全世界都站在這同一篇論文上」。（ch01／ch03／ch21）
- **維基百科〈Attention Is All You Need〉** — https://en.wikipedia.org/wiki/Attention_Is_All_You_Need ——想快速掌握歷史地位、八位作者、後續影響，比讀原文輕鬆。（ch01）
- **Kaplan et al., "Scaling Laws for Neural Language Models" (2020)** — https://arxiv.org/abs/2001.08361 ——「投入 vs loss 跨七個數量級的直線」，「先畫線再砸錢」的全部底氣；也是 ch19「能力沿曲線長出來、所以需要事後可解釋性」的接點。（ch02／ch19）
- **Hoffmann et al., "Training Compute-Optimal LLMs"（Chinchilla, NeurIPS 2022)** — https://proceedings.neurips.cc/paper_files/paper/2022/file/c1e2faff6f588870935f114ebe04a3e5-Paper-Conference.pdf ——讀「等比放大」結論與 Chinchilla(70B) 打贏 Gopher(280B) 的對照。（ch02／ch03／ch20）
- **Epoch AI, "Chinchilla scaling: a replication attempt"** — https://epoch.ai/publications/chinchilla-scaling-a-replication-attempt ——對 Chinchilla 確切擬合提出質疑的複現研究；讀它養成「連奠基定律都該被重測」的態度。（ch02）
- **GQA: "Training Generalized Multi-Query Transformer Models"（Ainslie et al., 2023，arXiv:2305.13245)** — https://arxiv.org/abs/2305.13245 ——近乎業界預設的 attention 省 KV cache 招數（query head 共享 KV head）；和 DeepSeek 的 MLA 對照讀，就懂「省 KV cache 有兩條路」。（ch01／ch16，landscape §架構共通）

---

## 對齊演化：RLHF → Constitutional AI → RLVR/GRPO（支撐 ch07／ch15）

「人類標註 → AI 自評 → 可驗證獎勵」這條「越來越少人工、越來越多可自動化訊號」的線。

- **InstructGPT, Ouyang et al.（OpenAI, 2022-03，arXiv:2203.02155)** — https://arxiv.org/abs/2203.02155 ——這條演化線的起點。讀「三步配方」（SFT → reward model → PPO RL）那張圖，與「1.3B 勝過 175B」這個對齊威力的硬證據。（ch05／ch15）
- **Constitutional AI, Bai et al.（Anthropic, 2022-12，arXiv:2212.08073)** — https://arxiv.org/abs/2212.08073 ——演化線第二站。讀 abstract 與「SL-CAI 自我批評→自我修正」「RL-CAI/RLAIF」兩段，建立「給憲法讓模型自評」的迴路；它解決了 RLHF 標註不可規模化的瓶頸。（ch03／ch07／ch15）
- **DeepSeekMath, Shao et al.（DeepSeek, 2024，arXiv:2402.03300)** — https://arxiv.org/abs/2402.03300 ——**GRPO 的首次登場**，RLVR 配方的關鍵零件。讀它怎麼論證「拿掉 critic、用組內相對排名」既省記憶體又有效。（ch11／ch15）
- **Tulu 3, Lambert et al.（Ai2, 2024，arXiv:2411.15124)** — https://arxiv.org/abs/2411.15124 ——RLVR 被明確命名與系統化的開放後訓練配方；讀它理解 RLVR 是一條可複用的方法、不只是 DeepSeek 的偏方。（ch15）
- **DeepSeek-R1 技術報告（"Incentivizing Reasoning Capability in LLMs via RL"，2025-01，arXiv:2501.12948)** — https://arxiv.org/abs/2501.12948 ——這條線「便宜起飛」最有名的實證：靠可驗證獎勵＋GRPO 把推理能力 RL 出來。（ch14／ch15／ch18／ch20）

---

## 推理範式：o1 之後的範式轉移（支撐 ch05／ch14）

「想久一點＝更聰明」的第二條 scaling 軸（test-time compute）怎麼開始、怎麼變成標配。

- **OpenAI, "Learning to reason with LLMs"（o1 發表，2024-09)** — https://openai.com/index/learning-to-reason-with-llms/ ——範式的第一手起點。讀那張「效能同時隨 train-time RL 與 test-time compute 上升」的圖——那就是「第二條 scaling 軸」的全部證據。（ch05／ch14／ch20）
- **維基百科 "Reasoning model"** — https://en.wikipedia.org/wiki/Reasoning_model ——一頁讀完 o1→R1→各家跟進的時間線與 test-time compute 的中性定義。會持續更新，版本資訊以 landscape 日期戳為準。（ch14）
- **"Don't Overthink It: A Survey of Efficient R1-style Large Reasoning Models" (2025)** — https://arxiv.org/pdf/2508.02120 ——專講 reasoning 的「影子」：overthinking 如何讓成本與延遲暴增、甚至讓答案變差。對你這種會算 p99 與單位成本的人，最該帶走的一篇。（ch14）

---

## 效率與成本：用算法挑戰「訓練很貴」（支撐 ch11／ch16）

DeepSeek 把「前沿模型一定很貴」這個共識打出一個洞——但數字要會讀。

- **DeepSeek-V3 Technical Report（arXiv:2412.19437)** — https://arxiv.org/abs/2412.19437 ——560 萬／278.8 萬 H800 小時的**原始出處**。直接讀它對成本的措辭：寫的是「最後一次預訓練 run 的 GPU 成本」，不是「總造價」——破除迷思最有力的就是回到一手文件。（ch02／ch03／ch11／ch13／ch16／ch20）
- **DeepSeek-V2 論文（arXiv:2405.04434)** — https://arxiv.org/abs/2405.04434 ——**MLA 的首次登場**。讀「low-rank KV joint compression」那段，對照你《從後端到 AI Infra》的 KV cache 章，理解它怎麼把最貴的那塊記憶體壓進低維潛在空間。（ch11）

> 補充：ch11 還引了 Ben Thompson 的 Stratechery〈DeepSeek FAQ〉與當時 NVIDIA 股價 −17% 的同期報導，把「560 萬到底算什麼、市場為什麼恐慌過頭」講得很清楚——這兩條屬二手分析／新聞，連結易變，建議用「Stratechery DeepSeek FAQ 2025」直接搜當前版本。

---

## 算力：GPU、TPU、自研晶片與能源天花板（支撐 ch06／ch10／ch16）

「算力是抄不走的那一格」——自有矽與自建叢集是用資本和時間砌的牆。

- **Ironwood: The first Google TPU for the age of inference（blog.google)** — https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/ ——TPU v7 的 pod 規模（9,216 顆）、HBM 與光交換互連的官方介紹。讀「pod 怎麼串成一台機器」那段，理解互連才是叢集真天花板。⚠️ 性能對比帶廠商口味，當方向不當精確值。（ch06／ch16／ch20）
- **Anthropic and Amazon expand collaboration for up to 5 gigawatts of new compute（anthropic.com)** — https://www.anthropic.com/news/anthropic-amazon-compute ——一手確認 Project Rainier（近 50 萬顆 Trainium2、Anthropic 用 >100 萬顆）與 5 GW／十年 1,000 億的協議；理解「押替代矽、多雲分散」這條路。（ch16，landscape master list）
- **Announcing the Stargate Project（openai.com, 2025-01)** — https://openai.com/index/announcing-the-stargate-project/ ——4 年 5,000 億美金、10 GW＋ 的算力企圖。對照「英國 Stargate 因能源成本喊停」的後續一起讀，體會資本支出黑洞與能源天花板如何同時箝制競賽。⚠️ 頭條數字皆為宣稱值，當企圖讀。（ch05／ch16）
- **xAI, "Colossus"（官方頁)** — https://x.ai/colossus ——Colossus 的第一手官方敘事。讀它怎麼描述「建得多快、多大」，再對照「⚠️ 自我宣稱、變動快」的但書——這正是練習「分辨公司自述與經驗證事實」的最佳教材。（ch10）
- **NVIDIA Newsroom, "Spectrum-X Ethernet … xAI Colossus"** — https://nvidianews.nvidia.com/news/spectrum-x-ethernet-networking-xai-colossus ——供應商視角的 Colossus：讀「互連怎麼把十萬級 GPU 串起來」，建立「叢集不只是堆卡、互連才是關鍵工程」的直覺。注意是 Nvidia 行銷稿，數字帶 vendor 色彩。（ch10）
- **Epoch AI（compute trends）** — https://epoch.ai/ ——把單一家的算力放進產業趨勢、用經過方法學處理的指標（能源／瓦數／有效算力）去看的可信來源；對照各家未經審計的自我宣稱數字，體會為什麼「響亮的數字」要打折。（ch10／ch16／ch18／ch20）

> 補充：ch16 另引了 Introl（Colossus 555k GPU／2 GW）、The Register（xAI 自抽渦輪發電的能源影子）、Data Center Frontier〈The Gigawatt Bottleneck〉（電網併網排隊數年、變壓器交期四年）、AWS〈Project Rainier〉啟用報導——都是二手新聞／產業整理，連結較易變，建議用標題關鍵字搜當前版本。

---

## 可解釋性：模型的神經科學（支撐 ch07／ch19）

「我們連自己造的東西都看不全懂」——這是多家共推的研究戰線，不是一家的事。

- **Templeton et al., "Scaling Monosemanticity"（Anthropic, 2024，從 Claude 3 Sonnet 抽特徵)** — https://transformer-circuits.pub/ ——「模型的神經科學」與 Golden Gate Claude 的源頭。讀它怎麼用稀疏自編碼器把糊在一起的神經元拆成可解讀「特徵」。（ch07／ch19）
- **Anthropic, circuit tracing / attribution graphs（約 2025-03)** — https://transformer-circuits.pub/2025/july-update/index.html ——可解釋性的下一步：不只找特徵，而是追蹤資訊怎麼流過模型、畫出電路圖。讀它對「看不全懂」這件事的誠實面對。（ch07／ch19／ch20）
- **A Survey on Sparse Autoencoders（arXiv:2503.05613)** — https://arxiv.org/html/2503.05613v3 ——SAE 的產業級綜述。讀它印證「OpenAI、Google DeepMind、學界都在跑 SAE」，以及這條路線當前的能耐與**侷限**（別過度推銷成熟度）。（ch19）
- **"Sparse Autoencoders Find Highly Interpretable Features in Language Models"（OpenReview)** — https://openreview.net/forum?id=F76bwRSLeK ——從「神經元是一團糊（多義性）」出發，建立「為什麼需要 SAE 去拆特徵」的直覺。（ch19）
- **OpenAI/Anthropic 的 SAE 研究對照整理（Arize AI)** — https://arize.com/blog/llm-interpretability-and-sparse-autoencoders-openai-anthropic/ ——把兩家 SAE 工作放一起對照的可信整理；建立「可解釋性是多家共推的戰線」這個立場。（ch19）

---

## 評測判讀：為什麼排行榜會騙人（支撐 ch04）

進任何「誰最強」討論前的防身術。

- **GSM1k: "A Careful Examination of LLM Performance on Grade School Arithmetic"（Scale AI, 2024，arXiv:2405.00332)** — https://arxiv.org/abs/2405.00332 ——污染從猜測變數字的招牌個案。讀「new benchmark」與「overfitting」兩節，看他們怎麼用全新題集量出最多 13% 的掉分。（ch04）
- **"A Survey on Data Contamination for Large Language Models"（2025，arXiv:2502.14425)** — https://arxiv.org/abs/2502.14425 ——把污染型態與偵測方法整理成地圖。挑「detection methods」一節，建立「換新題重測」之外的驗污手段。（ch04）
- **LMArena（前 Chatbot Arena / LMSYS)** — https://lmarena.ai/ ——親手去看 live 排行榜，注意每個 Elo 旁的 ± 信賴區間，感受「重疊的名次差別在統計上不存在」。（ch04）

---

## 資料暗河：版權、資料牆與合成資料（支撐 ch08／ch18）

最不透明、卻最關鍵的一格的當代爭議。

- **Epoch AI, "Will we run out of data?"** — https://epoch.ai/ ——「資料牆」的原始推估（高品質公開人類文字 ~2026–2028 耗盡）。讀它怎麼把資料牆從口號變成可檢驗推估，以及為什麼 overtrain 會改變這個時間點。（ch18／ch20）
- **Harvard Law Review — NYT v. OpenAI 評析** — https://harvardlawreview.org/blog/2024/04/nyt-v-openai-the-timess-about-face/ ——版權訴訟法律爭點（合理使用、核心主張為何被放行）的可信整理。讀「為什麼核心侵權主張沒被駁回」那段。（ch18，landscape master list）
- **Meta, "Introducing Muse Spark"（Meta Superintelligence Labs, 2026-04)** — https://about.fb.com/news/2026/04/introducing-muse-spark-meta-superintelligence-labs/ ——閉源轉向的第一手宣告，也是「資料牆讓專有用戶資料變稀缺護城河」的活例。讀「為什麼從開放轉閉源、權重不可下載」那段，對照 ch08「2026 轉折、非定局」的但書。（ch08／ch13／ch18）

> 補充：ch18 還引了 Shumailov et al. 2024〈AI models collapse …〉(Nature)——模型崩塌的權威論證，與 natlawreview/Jones Walker 對「OpenAI 被令交出 2,000 萬筆 ChatGPT 紀錄」的同期法律評析。前者建議用作者名＋Nature 搜原文，後者屬法律新聞、連結最易變。

---

## 開源 vs 閉源與各家一手材料（支撐 ch08／ch09／ch12／ch13／ch17）

「開放權重 ≠ 開源 ≠ 透明」——以各家官方公告為證物讀這場路線之爭。

- **Meta AI, "The Llama 4 herd"（2025-04)** — https://ai.meta.com/blog/llama-4-multimodal-intelligence/ ——開放權重旗艦的第一手起點（Scout／Maverick／Behemoth），也是 Meta 第一個原生多模態 MoE。讀它附帶的社群授權，親眼看 700M MAU 與 EU 限制那條「繩子」。（ch08／ch13／ch17）
- **Qwen Team, "Qwen3: Think Deeper, Act Faster"（qwenlm.github.io, 2025)** — https://qwenlm.github.io/blog/qwen3/ ——全尺寸階梯（0.6B→235B）、119 種語言、MoE 與 Apache 2.0 的第一手出處。讀「模型陣容」與「多語言」兩段。（ch12／ch13）
- **Mistral AI, "Introducing Mistral 3"（Mistral Large 3, 2025-12)** — https://mistral.ai/news/mistral-3/ ——讀「675B 總 / 41B 啟用」的稀疏 MoE 與 Apache 2.0 宣告，建立「大容量小帳單」的直覺。（ch09）
- **Mistral AI, "Introducing Mistral Small 4"（2026-03-16)** — https://mistral.ai/news/mistral-small-4/ ——讀「把 Magistral／Pixtral／Devstral 合併成一個」與 `reasoning_effort` 旋鈕，看效率品味怎麼貫徹到小模型與多模態。（ch09／ch17）
- **SAP News, "SAP and Mistral AI: European Sovereign AI"（2025-11)** — https://news.sap.com/2025/11/sap-mistral-ai-new-alliance-european-sovereign-ai/ ——讀「主權 AI」如何從口號變成政府／企業採購，體會產品取向怎麼壓出技術選擇。（ch09）
- **NTIA — Risks & Benefits of Dual-Use Foundation Models with Widely Available Weights** — https://www.ntia.gov/programs-and-initiatives/artificial-intelligence/open-model-weights-report ——美國官方對「開放權重的安全與濫用」的系統性評估；讀它平衡「開放 ＝ 安全」的迷思。（ch13）
- **Wikipedia, "Claude (language model)"** — https://en.wikipedia.org/wiki/Claude_(language_model) ——版本與時間線的彙整對照。⚠️ 持續更新、每幾個月過期，Fable 5／Mythos 5 極新極易變。（ch07）
- **Wikipedia, "Gemini (language model)"** — https://en.wikipedia.org/wiki/Gemini_(language_model) ——Gemini 版本／長上下文時間線的彙整對照，同樣 ⚠️ 易過期，數字以 landscape 日期戳為準。（ch06，landscape master list）

> 補充：這一束裡 ch06 還引了 cloud.google 的 Gemini 1.5 Pro 2M context 開發者部落格、deepmind.google／nobelprize.org 的 2024 諾貝爾化學獎（AlphaFold）、Gemini 技術報告（storage.googleapis 的 deepmind-media PDF）；ch12 引了 DataCamp〈Qwen3〉與 imseankim 的 Hugging Face open model rankings；ch08 引了 TechCrunch〈Meta debuts Muse Spark〉。這些是各家部落格／二手彙整，連結較易變，建議用標題關鍵字搜當前版本。

---

## 跨書接點（你書架上的另外兩本）

- **《從後端到 AI Infra》——KV cache、prefill/decode、長序列成本那幾章**：本書多次用它當錨點（MLA 砍 KV cache、長上下文／影片＝超長序列成本）。想把成因鏈算到工程的底，那本是另一半。（ch01／ch11／ch16／ch17／ch21）
- **《馴服隨機：機率與統計》——抽樣偏誤、信賴區間、為什麼小樣本排名不可靠那幾章**：本書 ch04 的評測判讀只喚醒、不重講；想追根究柢回那本的抽樣與信賴區間章節。（ch04／ch21）

---

## 編纂說明（給未來重掃的你）

- 本附錄只收**各章 `## 延伸閱讀` 實際寫過**＋**landscape master list 已驗證**的連結，去重後依主題重排；沒有新增任何各章未引用的網址。
- **未附穩定 URL 而以名稱帶過的條目**（Stratechery DeepSeek FAQ、IG 股價報導、Introl／The Register／Data Center Frontier 的算力新聞、AWS Project Rainier 啟用報導、Gemini 技術報告 PDF、cloud.google／deepmind.google 部落格、Nature 模型崩塌論文、natlawreview 法律評析、DataCamp／imseankim 彙整、TechCrunch Muse Spark）**沒有逐條鏈進這份地圖**，改在各主題的「補充」段以可搜尋的標題保留——因為它們屬二手新聞或會搬家的部落格，URL 最易爛，列死網址反而誤導。要追時用標題關鍵字搜當前版本。
- landscape master list 裡 **Anthropic Fable 5／Mythos 5 公告**（https://www.anthropic.com/news/claude-fable-5-mythos-5）屬 Part 3 的 ⚠️ 最易過期事實，且各章正文已用 Wikipedia〈Claude〉條目作版本對照，故未另列為延伸閱讀；重掃時若它仍在線，可補進「開源 vs 閉源與各家一手材料」一束。
- 重掃優先級：所有 lab 部落格與 Wikipedia 條目（版本會變）＞二手彙整（會搬家）＞arXiv 一手論文（最穩定，幾乎只需確認還在線）。
