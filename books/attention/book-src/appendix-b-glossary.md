# 附錄 B — 術語表

> 這張表把全書出現過的核心術語收成一處，給你查與複習用。每一條都是「英文（你查論文／文件時會看到的字）｜台灣慣用中譯｜一句能唸出來的白話定義｜本書第一次把它講清楚的章」。「首次出現章」指的是該詞**被定義、被解釋**的那一章，不是它在路線圖或章名裡被提前點名的地方——所以同一個詞在更前面露過臉，這裡仍標它真正落地的那一章。定義刻意寫成「能對另一個工程師唸出口」的長度，因為本書驗收靠口述；能扣三步骨架（打分→正規化→加權混合）的，就直接標它動了哪一步。按全書六個 Part 的順序分區，求好查。

## Part I — 注意力解決什麼問題（ch01–03）

| English | 中文（台灣） | 一句話定義 | 首次出現章 |
|---|---|---|---|
| attention | 注意力 | 對所有位置做一次「依相關性加權的平均」的機制——三步骨架（打分→正規化→加權混合）的統稱；本書唯一的主角。 | ch01 |
| three-step skeleton | 三步骨架 | 打分（score）→ 正規化（softmax）→ 加權混合（mix）；全書所有注意力變體的共同骨架，每個變體都只是動了其中某一步。 | ch01 |
| token | token（詞元） | 把一段文字切出來的最小處理單位；模型不直接讀字，讀的是 token 經 embedding 後的向量。 | ch01 |
| embedding | 嵌入 | 把一個 token 對映成一個學來的向量，讓模型用「向量間的關係」表示語意。 | ch01 |
| seq2seq | 序列轉序列 | encoder 把輸入序列讀進、decoder 把它解碼成輸出序列的框架（如翻譯）；注意力誕生前的主流形態。 | ch02 |
| fixed-vector bottleneck | 固定向量瓶頸 | seq2seq 把整個輸入句硬壓成一個固定維度的 context vector，長句資訊被擠爆——注意力要打破的那道牆。 | ch02 |
| context vector | context vector（脈絡向量） | encoder 壓縮整段輸入得到的那一個固定維度向量；decoder 要從它還原全部資訊，正是瓶頸所在。 | ch02 |
| RNN | RNN（循環神經網路） | 一個 token 接一個處理、把歷史塞進隱態的序列模型；循序依賴讓它難平行、長程依賴會衰減。 | ch02 |
| Bahdanau attention | Bahdanau 注意力 | 第一個 NMT 注意力（2014）：decoder 生成每個目標詞時動態加權源句各位置——三步骨架的第一個完整版本。 | ch03 |
| alignment | 對齊 | 目標端的詞「回頭查源句哪幾個位置最相關」這件事；Bahdanau 用一個對齊模型算出對齊分數。 | ch03 |
| additive attention | 加性注意力 | 打分用 `score = vᵀtanh(W[s; h])` 的小網路（Bahdanau 2014）；對到三步骨架的「打分」步。 | ch03 |
| multiplicative attention | 乘性注意力 | 打分直接用內積（Luong 2015）；現代 scaled dot-product attention 的乘性形式源於此。 | ch03 |

## Part II — 三步骨架：核心機制（ch04–08）

| English | 中文（台灣） | 一句話定義 | 首次出現章 |
|---|---|---|---|
| query | 查詢（query） | 站在「我」這個位置往外看、我想找什麼樣鄰居的向量；由輸入經 W_Q 投影得到，負責「打分」第一步。 | ch04 |
| key | 鍵（key） | 當別人在找東西時、我把自己標榜成什麼的向量；由輸入經 W_K 投影得到，與 query 算內積成分數。 | ch04 |
| value | 值（value） | 我被選中後實際交出的內容向量；由輸入經 W_V 投影得到，在「加權混合」第三步才進場。 | ch04 |
| soft dictionary lookup | 軟性字典查找 | 注意力的核心隱喻——不是 query 精確命中一個 key 取那筆 value，而是對每個 key 算相似度、按相似度混合所有 value。 | ch04 |
| learned projection | 學來的投影 | W_Q／W_K／W_V 這幾個訓練學出的矩陣，把同一個輸入向量轉成它的 query／key／value 三種身分。 | ch04 |
| dot product | 內積 | q·k = Σ qᵢkᵢ，方向越一致內積越大；本書用來當相似度分數，是「打分」步的標準作法。 | ch04 |
| similarity | 相似度 | 兩個向量「有多像」的量；注意力用內積當相似度，相似度高就是分數高。 | ch04 |
| asymmetry (query ≠ key) | 非對稱（query≠key） | query 和 key 用不同投影，使 i 看 j 的分數可以 ≠ j 看 i 的分數——表達「A 找 B 但 B 不找 A」這種有向關係所必需。 | ch04 |
| softmax | softmax | 把一排實數分數先取 exp 再正規化成和為 1 的權重分布；三步骨架的「正規化」第二步。 | ch05 |
| attention weight | 注意力權重 | softmax 輸出的那排數 αᵢ，意思是「這個位置把多少比例的注意力預算分給第 i 個 token」；非負、總和 1。 | ch05 |
| probability distribution | 機率分布 | 一排非負、和為 1 的數；softmax 的輸出真的是一個合法分布（呼應《馴服隨機》）。 | ch05 |
| argmax | argmax | 直接回傳「分數最大的是第幾個」；不可微、只看一個，正是 softmax 要平滑化的硬版本。 | ch05 |
| soft-argmax | soft-argmax | softmax 的別名讀法——argmax 的可微「軟」版：按比例看全部、放大分數差形成「軟選擇」，所以能訓練。 | ch05 |
| temperature | 溫度（temperature） | softmax 前把分數除以的 T；T→0 趨近硬 argmax（尖）、T→∞ 趨近均勻（平），就是 LLM API 那個 temperature 旋鈕。 | ch05 |
| scaled dot-product attention | 縮放點積注意力 | `Attention(Q,K,V) = softmax(QKᵀ/√d_k)·V`；Transformer 的標準注意力，先把內積分數除以 √d_k 再 softmax。 | ch06 |
| √d_k scaling | √d_k 縮放 | 把內積分數除以 √d_k 的小動作；因為 q·k 的變異數隨 d_k 成長，除 √d_k 把它拉回 ~1，避免 softmax 飽和。 | ch06 |
| softmax saturation | softmax 飽和 | 分數太大時 softmax 被推進「一個權重→1、其餘→0」的飽和區，梯度趨近 0、模型學不動——不縮放會發生的壞事。 | ch06 |
| self-attention | 自注意力 | Q、K、V 都來自同一序列、每個 token 既是查詢者也是被查者；整張注意力矩陣 QKᵀ 是 n×n。 | ch07 |
| attention matrix | 注意力矩陣 | n×n 的分數矩陣 QKᵀ，每一格是一對 token 的相似度；它的存在正是 O(n²) 的源頭。 | ch07 |
| O(n²) complexity | O(n²) 複雜度 | self-attention 對長度 n 要算 n 個 query × n 個 key 共 n² 個分數，計算與記憶體都隨 n 平方成長。 | ch07 |
| bidirectional attention | 雙向注意力 | 每個 token 都看得到全句兩邊（無遮罩）；encoder 的形態，能一次抓全句關係。 | ch07 |
| multi-head attention | 多頭注意力 | 把 d_model 切成 h 顆頭、每顆在各自子空間做完整三步骨架，輸出 concat 再過 W_O——讓模型同時抓多種關係。 | ch08 |
| head | 頭（head） | 多頭注意力裡的一路；各有自己的 W_Q/W_K/W_V，投影到 d_k=d_model/h 維，專注於一種關係（如句法、指代）。 | ch08 |
| d_model | d_model | 模型主幹向量的維度（原始 Transformer 為 512）；所有 sublayer 與 embedding 輸出皆為它，才好殘差相加。 | ch08 |
| d_k | d_k | 每顆頭裡 query／key 的維度，d_k=d_model/h（原始為 64，√d_k=8）；縮放就是除以 √d_k。 | ch08 |
| W_O (output projection) | 輸出投影 W_O | 把多頭 concat 後的向量投影回 d_model 維的矩陣；多頭注意力的收尾一步。 | ch08 |

## Part III — 補上缺的零件：位置、遮罩、跨序列、一整層（ch09–13）

| English | 中文（台灣） | 一句話定義 | 首次出現章 |
|---|---|---|---|
| positional encoding | 位置編碼 | 給每個 token 蓋一個「位置戳記」的機制；因為裸 self-attention 看不見順序，位置非外加不可。 | ch09 |
| permutation invariance | 置換不變性 | 重排輸入 token 不改變對各 token 的注意力權重——self-attention 看不見順序的根本原因（ch19 給嚴格版）。 | ch09 |
| sinusoidal positional encoding | 正弦位置編碼 | 用不同頻率的 sin/cos 算出的固定位置向量（Vaswani 2017），動機是「相對位置可由線性關係表示」且可外推。 | ch09 |
| learned absolute positional embedding | 可學習絕對位置嵌入 | 每個位置配一個訓練學出的向量（BERT／GPT-2）；與正弦編碼相對的另一條路。 | ch09 |
| RoPE (rotary position embedding) | 旋轉位置編碼 | 把 q、k 依「位置」旋轉一個角度（每對維度一個旋轉平面），旋轉後內積只依賴相對位置——2026 開源 LLM 事實標準。 | ch10 |
| relative position | 相對位置 | 「差幾步」而非「絕對在第幾格」；RoPE 之美就是旋轉後絕對位置自動消去、只剩相對位置進入分數。 | ch10 |
| ALiBi | ALiBi | 不動 embedding，直接在 q·k 分數上加一個與距離成正比的線性偏置（Press 2021）；利於長度外推。 | ch10 |
| length extrapolation | 長度外推 | 模型在比訓練更長的序列上還能運作的能力；RoPE 超出訓練長度會失真，正是 Position Interpolation／YaRN 要救的。 | ch10 |
| mask / masking | 遮罩 | 在 softmax 之前把某些位置的分數覆寫掉的加工；它動的不是公式，是送進 softmax 的那排分數。 | ch11 |
| causal mask | 因果遮罩 | 把所有「看向未來」(j>i) 的分數設成 −∞、softmax 後變 0；保證生成時第 i 個 token 只看得到 ≤i 的 token。 | ch11 |
| autoregressive | 自迴歸 | 一個 token 一個 token 往後生成、寫第 i 個時手上只有前 i 個的模式；causal mask 就是為它而設。 | ch11 |
| padding mask | padding mask（補齊遮罩） | 把為了對齊長度而補進來的空 token 遮掉（分數設 −∞），避免模型把垃圾位置算進注意力。 | ch11 |
| cross-attention | 交叉注意力 | Q 來自一個序列（decoder）、K/V 來自另一個序列（encoder）的注意力，讓目標端每個位置看遍源端——跨序列查找。 | ch12 |
| three attention types | 三種注意力 | encoder self（雙向）、decoder masked self（單向）、encoder-decoder cross（跨序列）——三種「誰查誰、能查到哪」的組合。 | ch12 |
| transformer block | transformer block（一層） | （多頭注意力＋殘差＋LayerNorm）→（FFN＋殘差＋LayerNorm）的一層結構；堆疊 N 層構成一個模型。 | ch13 |
| residual connection | 殘差連接 | 把某層的輸入直接加回它的輸出的「直通捷徑」；連同 FFN 一起，是阻止純堆 attention 秩坍縮的解藥。 | ch13 |
| LayerNorm (layer normalization) | 層正規化 | 對每個位置的向量做正規化以穩定數值的鷹架零件；transformer block 裡夾在 attention/FFN 後面。 | ch13 |
| FFN (feed-forward network) | 前饋網路 | 逐位置（position-wise）作用的兩層非線性 `max(0,xW₁+b₁)W₂+b₂`（內層 d_ff=2048）；注意力混合後的逐位置轉換。 | ch13 |
| residual stream | 殘差流 | 貫穿各層、被注意力與 FFN 不斷讀寫的主幹向量（ch21 的電路觀點裡，OV 電路把內容寫進的就是它）。 | ch13 |
| rank collapse | 秩坍縮 | 純 self-attention（無殘差無 MLP）堆深後輸出雙指數地坍縮到秩 1（Dong 2021）；殘差與 FFN 正是解藥。 | ch13 |
| encoder-only (BERT) | 純編碼器 | 雙向、用於理解的模型家族（如 BERT）。 | ch13 |
| decoder-only (GPT) | 純解碼器 | 單向、用於生成的模型家族（如 GPT）——今日主流 LLM 形態。 | ch13 |
| encoder-decoder (T5) | 編碼器-解碼器 | encoder 讀、decoder 寫、中間靠 cross-attention 連接的模型家族（如 T5），用於翻譯／摘要。 | ch13 |
| next-token prediction | 下一個 token 預測 | 用前文預測下一個 token 的訓練目標（配交叉熵 cross-entropy）；本書一句帶過的訓練鷹架。 | ch13 |

## Part IV — 為什麼是 O(n²)：效率與它的代價（ch14–16）

| English | 中文（台灣） | 一句話定義 | 首次出現章 |
|---|---|---|---|
| quadratic bottleneck | 二次方瓶頸 | O(n²) 在長 context 下的爆炸（n=1k 就 100 萬格、n=100k 就 100 億格）；所有高效注意力的共同動機。 | ch14 |
| "no index" full scan | 建不了索引的全表掃描 | 相似度不像可排序／可雜湊的鍵能靠 hash/B-tree 加速，每對 token 都得現算——這就是 attention 為何天生 O(n²)。 | ch14 |
| sparse attention | 稀疏注意力 | 只算部分 token 對（local 窗口＋少數全域）來省成本，改的是「打分」的連結結構；是近似法（Sparse Transformer/Longformer/BigBird）。 | ch15 |
| linear attention | 線性注意力 | 把 softmax(qkᵀ) 換成核函數 φ(q)φ(k)ᵀ、用結合律把 (QKᵀ)V 重排成 Q(KᵀV)，O(n²)→O(n)；改的是「正規化」步。 | ch15 |
| kernel trick | 核技巧 | 用 φ(q)·φ(k) 這種特徵映射的內積取代 softmax 核，讓矩陣乘法可重排——線性注意力省成本的關鍵。 | ch15 |
| associativity | 結合律 | 矩陣乘法 (A·B)·C = A·(B·C) 的性質；線性注意力靠它把昂貴的 n×n 中間矩陣換成便宜的 d×d。 | ch15 |
| low-rank | 低秩 | 用遠小於 n 的秩去近似注意力（如 Linformer 把 K/V 投影到低秩）；接《矩陣是動詞》SVD/低秩。 | ch15 |
| approximation (vs exact) | 近似（相對於精確） | 稀疏與線性注意力省成本的代價——結果不等於標準注意力，常在 token 級精確回憶上吃虧。 | ch15 |
| memory-bound | 記憶體受限 | 瓶頸在「搬資料」而非「算」的狀態；注意力在推論時正是 memory-bound，省搬比省算更有用。 | ch16 |
| SRAM / HBM | SRAM／HBM | GPU 記憶體的兩層：SRAM 極快極小（on-chip）、HBM 大但慢一個量級；n×n 矩陣在兩者間來回搬正是瓶頸。 | ch16 |
| FlashAttention | FlashAttention | IO-aware 的**精確**注意力（非近似）：分塊＋online softmax，不把 n×n 矩陣在 HBM 落地，砍的是搬運次數不是計算次數（Dao 2022）。 | ch16 |
| tiling | 分塊 | 把 Q/K/V 沿序列維切成小到能整個塞進 SRAM 的小塊逐塊算；FlashAttention 不實體化整張矩陣的辦法。 | ch16 |
| online softmax | online softmax | 邊掃邊更新 running max 與 running sum 來分塊算 softmax，合併結果與一次算位元級相同（減 running max 還順帶防 overflow）。 | ch16 |
| MQA (multi-query attention) | 多查詢注意力 | 所有頭共享同一份 K/V、各自 Q（Shazeer 2019）；省推論時的 KV 記憶體與頻寬，改的是頭的 K/V 結構。 | ch16 |
| GQA (grouped-query attention) | 分組查詢注意力 | 介於 MQA 與完整多頭之間，分組共享 K/V（Ainslie 2023）；被 Llama 2/3 採用。 | ch16 |
| MLA (multi-head latent attention) | 多頭潛在注意力 | 把 KV 壓到低秩潛在向量大幅省 KV cache（DeepSeek 開創）；softmax 注意力＋低秩 KV，2026 生產主流之一。 | ch16 |

## Part V — 注意力到底是什麼：理論身世（ch17–19）

| English | 中文（台灣） | 一句話定義 | 首次出現章 |
|---|---|---|---|
| kernel regression | 核迴歸 | 拿相似的鄰居加權平均來估計目標值的統計方法；attention 就是它的可學習、可微分、可平行版本（Tsai 2019）。 | ch17 |
| Nadaraya-Watson estimator | Nadaraya-Watson 估計量 | 核迴歸最經典的版本（Nadaraya 1964、Watson 1964）：query＝查詢點、key＝樣本位置、value＝樣本值、softmax＝核。 | ch17 |
| kernel function | 核函數 | 吃進「兩點的距離」吐出「相似度分數」的函數 K（距離越近分數越高，如高斯核）；attention 用的核是 exp(內積)。 | ch17 |
| conditional expectation | 條件期望 | 「在這個 query 條件下 value 的平均」；attention 的加權混合骨子裡就是它的估計（接《馴服隨機》加權平均=期望）。 | ch17 |
| associative memory | 聯想記憶 | 拿一條模糊／殘缺的線索去查容錯記憶庫、檢索出最像那筆完整模式的機制；attention 就是它的軟性可微版。 | ch18 |
| content-addressable memory | 內容定址記憶 | 不靠位址、靠「內容彼此的相似度」來取資料的記憶體；聯想記憶的關鍵詞，對到 attention 的軟性字典查找。 | ch18 |
| modern Hopfield network | 現代 Hopfield 網路 | 連續狀態的 Hopfield 更新規則，被證明與 Transformer attention 一模一樣（Ramsauer 2020）；可指數級儲存、一步檢索。 | ch18 |
| β (inverse temperature) | β（逆溫度） | 現代 Hopfield 裡控制檢索「尖銳—模糊」的參數；β 越大（溫度越低）檢索越像硬查找（接 ch05–06 的溫度）。 | ch18 |
| permutation equivariance | 置換等變 | 重排輸入則輸出跟著重排、但內容不變（SelfAttn(P·X)=P·SelfAttn(X)）；attention 把輸入當集合處理的深層身分。 | ch19 |
| set operation | 集合運算 | attention 本質是作用在「一袋無序東西」上的運算，所以對順序無感、位置非外加不可（回收 ch09）。 | ch19 |
| message passing / GNN | 訊息傳遞／GNN | self-attention＝在全連接圖上、用 softmax(q·k) 當學出來的邊權重做一輪訊息傳遞（接你做過的 gossip/聚合）。 | ch19 |
| universal approximation | 通用近似 | 在足夠頭與維度下，attention 可近似一大類序列函數的性質；本書給直覺、嚴格前提指向延伸。 | ch19 |
| Turing-completeness | 圖靈完備 | 加上精度與位置假設後 Transformer 可模擬圖靈機（Pérez et al.）；前提很多，本書明寫前提、不誇大。 | ch19 |
| sigmoid attention | sigmoid 注意力 | 把 softmax 換成 sigmoid 的注意力（Apple 2024）；softmax 替代品之一，動的是「正規化」步，⚠️ 領域演變快、softmax 多數仍領先。 | ch19 |

## Part VI — 看進黑盒與它的未來（ch20–23）

| English | 中文（台灣） | 一句話定義 | 首次出現章 |
|---|---|---|---|
| interpretability | 可解釋性 | 想搞懂「模型為什麼這樣算」的研究方向；本書分成「注意力權重算不算解釋」（ch20）與「機制可解釋性」（ch21）兩層。 | ch20 |
| attention as explanation | 注意力即解釋（論戰） | 「能不能把注意力熱圖當模型決策的解釋」這場至今未定論的嘴仗（Jain & Wallace 2019 vs Wiegreffe & Pinter 2019）。 | ch20 |
| faithfulness | 忠實性 | 解釋是否「真的反映模型內部的決策過程」（模型確實據此運作）；論戰雙方常被混在一起的兩個詞之一。 | ch20 |
| plausibility | 合理性 | 解釋是否「讓人覺得合理、符合直覺」；合理不保證忠實——越漂亮的熱圖越危險，正因為合理可能就是它被你接受的全部原因。 | ch20 |
| head specialization / pruning | 頭專門化／剪枝 | 少數「重要頭」扛大部分工作、可剪掉許多頭只損極少效能（Voita 2019 剪 48 頭中的 38 只損 0.15 BLEU）。 | ch20 |
| attention sink | attention sink | 模型把大量注意力倒給某些「不太相關」的位置（常是首個 token）當「洩壓閥」的現象；提醒熱圖未必反映語意。 | ch20 |
| mechanistic interpretability | 機制可解釋性 | 不問權重、直接把注意力頭拆成可讀「電路」來逆向理解模型在算什麼的路線（Anthropic 的 Transformer Circuits）。 | ch21 |
| QK circuit | QK 電路 | 一顆頭裡決定「看序列哪一格」的定址邏輯，併成 W_QK=W_Q·W_Kᵀ；對到三步骨架的「打分＋正規化」。 | ch21 |
| OV circuit | OV 電路 | 一顆頭裡決定「從那一格搬什麼內容過來、寫進殘差流」的搬運邏輯，併成 W_OV=W_V·W_O；對到「加權混合」。 | ch21 |
| induction head | induction head（歸納頭） | 學會「上次這個 pattern 後面接什麼就照抄」（`[A][B]…[A]→[B]`）的小程式；其出現時機對上 in-context learning 突增。 | ch21 |
| in-context learning (ICL) | 脈絡內學習 | 模型不更新權重、只靠 prompt 裡的範例就學會新任務的能力；induction head 被認為是它的機制來源（Olsson 2022）。 | ch21 |
| state space model (SSM) | 狀態空間模型 | 把整段歷史壓進一個固定大小狀態、每步只更新它的 O(n) 序列模型；挑戰 attention 的另一條路，祖宗是控制論。 | ch22 |
| fixed-size state | 固定大小狀態 | SSM 用來裝歷史的那個不隨長度成長的狀態向量；它讓 SSM O(n) 且不爆 KV，代價是細節會漏（精確回憶受損）。 | ch22 |
| S4 | S4 | 用 HiPPO 數學框架構造狀態矩陣、讓固定狀態最優記住長程歷史的 SSM（Gu, Goel & Ré 2021）；Long Range Arena SOTA。 | ch22 |
| HiPPO | HiPPO | 用正交多項式投影去逼近過去訊號的數學配方；S4 靠它設計「怎麼衰退才不丟長程資訊」。 | ch22 |
| Mamba | Mamba | 選擇性（selective）SSM——讓參數變成輸入的函數、能「該記的多記、廢話跳過」（Gu & Dao 2023）；線性時間。 | ch22 |
| SSD (state space duality) | 狀態空間對偶 | 「Transformers are SSMs」（Mamba-2，2024）證明 SSM 是因果線性注意力的特例的對偶之美（接 ch15）。 | ch22 |
| hybrid architecture | 混合架構 | 以小比例（如 1-in-8~10）注意力層保留精確回憶、其餘用 Mamba/線性層的設計（如 Jamba）；2026 的新共識。 | ch22 |
| "attention is all you need"? | 「attention is all you need」還成立嗎 | 2026-06 的誠實答案：softmax 仍主導生產級 LLM、混合是新共識、純 SSM 未稱霸，長期勝者未定論。 | ch22 |
