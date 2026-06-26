# 附錄 C — 術語表

這張表收錄全書正式引入的技術名詞——每一條的「一句話定義」都是**本書的講法**（這本書當初怎麼向你解釋它），不是字典定義。用途是查找：按英文字母 A–Z 排序，忘了某個詞在哪章登場、或它在本書脈絡下到底指什麼時，從這裡回到正文。「首次出現章」指該詞**第一次以具名概念被引入並使用**的章節（不是路線圖標籤、不是延伸閱讀的書目連結）；少數先在前章被點名、後章才正式下定義的詞，會在最後一段說明，以免你查到的章節與記憶對不上。記號系統見附錄 A、公式與其適用條件見附錄 B。

| English term | 中文 | 一句話定義（本書講法） | 首次出現章 |
|---|---|---|---|
| admission control | 准入控制 | 系統內已有 n 件工作時就以遞減機率收下新到達，把「λ 隨擁塞下降」寫進生滅過程，換來無條件的穩定性、帳單從延遲搬到 goodput。 | ch07 |
| arrival theorem | 到達定理 | 封閉網路裡接替 PASTA 的定理：抵達某站的工作看到的狀態分布，恰是「把自己抽走、剩 N−1 個工作」那個系統的穩態——MVA 遞迴的引擎。 | ch17 |
| balance equation | 平衡方程 | 平穩分布逐狀態的「機率流量守恆」讀法（流入每個狀態＝流出），在生滅這種一維結構上可爆破成逐邊平衡的 local balance。 | ch06 |
| balking | 望之卻步 | 到達者看到系統內有 n 個工作後才決定要不要加入，建模成狀態相依的到達率 λₙ。 | ch10 |
| batch means | 批次平均 | 把一條長軌跡切成幾個大批次、每批取平均當近似獨立樣本做信賴區間——對付輸出自相關讓樸素 CI 過窄的解藥。 | ch19 |
| BCMP theorem | BCMP 定理 | 把乘積形式推到極限的定理：精確劃出哪四種 station 型式與服務分布／紀律組合仍保乘積形式——product form 的邊界座標。 | ch18 |
| birth-death process | 生滅過程 | 狀態排成一條整數軸、每步只能走到隔壁（生＝+1、滅＝−1）的 CTMC，是 M/M/* 系列模型共用的舞台。 | ch07 |
| blocking probability | 阻塞機率 | 有限容量系統裡到達者撞上「系統已滿」而被拒的長期比例，由 PASTA 等於穩態 π_K。 | ch10 |
| bottleneck analysis | 瓶頸分析 | 不解任何機率模型，只靠「使用率≤1」與 Little's Law 就推出吞吐天花板 X≤1/D_max、延遲地板 E[T]≥ΣDᵢ 與排隊拐點 N* 的漸近界法。 | ch02 |
| Bounded Pareto | 有界 Pareto | 在上界處截斷的 Pareto——承認現實一定有最大值，但只要上界夠大，行為仍像無界重尾。 | ch15 |
| Burke's theorem | Burke 定理 | M/M/c 穩態的輸出流仍是 Poisson(λ)，且當下狀態與過去的離開歷史獨立——「剛吐出一串 job 不代表現在比較空」，靠時間反轉證明。 | ch11 |
| busy period | 忙期 | 從一件工作打破空系統、到系統再次清空為止的一整段忙碌時間。 | ch12 |
| circuit breaker | 斷路器 | closed／open／half-open 三狀態的故障保護器，本書拿它當第一個 Markov chain 範例：你會畫的狀態圖，加上箭頭機率與線性方程組，就能回答「長期斷路時間佔比」。 | ch06 |
| closed network | 封閉網路 | 工作在固定母體內循環、沒有外部到達的網路（固定 worker 池、connection pool、固定 VU 壓測）——天生自我節流。 | ch17 |
| competition lemma | 競賽引理 | 多條獨立指數碼錶同時起跑，最先響的時刻仍是指數（速率相加）、哪條先響的機率正比於其速率、且勝者身分與競賽時長獨立——CTMC 的組裝引擎。 | ch04 |
| continuous batching | 連續批處理 | 每個 token 步重組批次、完成者立即讓位、新請求隨時插隊進批的 LLM serving 排程，是本書排程工具的直接應用場。 | ch20 |
| coordinated omission | 協同遺漏 | 固定 VU 的封閉迴圈壓測在系統變慢時自動少送請求，於是 tail latency 被系統性地藏起來、量測比生產樂觀。 | ch19 |
| CTMC | 連續時間馬可夫鏈 | 每進一個狀態就停留指數時間、再按競賽引理跳轉的隨機過程——把 ch04 的指數競賽與 ch06 的流量守恆焊成一台機器。 | ch07 |
| C² (SCV) | 變異係數平方 | 無因次的標準化變異數 C²=Var/E²，本書的計價單位：C²=0 確定性、C²=1 指數（純隨機基準線）、C²>1 叢發。 | ch03 |
| decomposition approximation (QNA) | 分解近似 | 把網路每站當成獨立 G/G/1、只在站間傳播流量 λ 與變異性 C²ₐ／C²ₛ、逐站套 Kingman 的工程近似（Whitt 的 QNA 是其代表）。 | ch18 |
| DES | 事件驅動模擬 | 模擬時鐘直接跳到下一個事件、狀態只在事件處改變的模擬骨架——本書所有模擬都是這個骨架換零件。 | ch08 |
| detailed balance | 詳細平衡 | 穩態下每一對狀態之間 πᵢq(i→j)=πⱼq(j→i)，逐邊平衡而非只是總平衡；可逆性的等價條件，也是「先猜 π 再驗證」的實用招式。 | ch11 |
| effective arrival rate (λ_eff) | 有效到達率 | 扣掉被拒收後真正進入系統的流量 λ_eff=λ(1−π_K)，是 goodput 帳的起點。 | ch10 |
| embedded chain | 嵌入鏈 | 只在工作離開的瞬間觀察系統、那一刻構成的離散時間 Markov chain——Kendall 解 M/G/1 的另一條路（本書改走 mean-value 路線）。 | ch12 |
| ergodicity | 遍歷性 | 有限不可約非週期鏈的單一軌跡時間平均收斂到 π 期望——把監控量測升格成對穩態的無偏估計，也是模擬的理論執照。 | ch06 |
| Erlang-A | Erlang-A | 多伺服器又允許客戶等不耐而放棄的模型（M/M/c+M），給 timeout 一個數學身分；放棄是天然洩壓閥，使系統對任何負載都穩定。 | ch10 |
| Erlang-B | Erlang-B | M/M/c/c 損失系統裡到達者沒位子被擋掉的機率，靠手算友善的遞迴算，且對服務分布不敏感——Erlang 在哥本哈根電話機房的原始公式。 | ch09 |
| Erlang-C | Erlang-C | M/M/c 系統裡到達者得排隊（沒有空閒伺服器）的機率，是池化與 staffing 計算的核心量。 | ch09 |
| exponential backoff | 指數退避 | 重試間隔 2ⁿ 倍增的確定性排程——本書先拆掉它與指數「分布」的命名撞車誤會，後在 retry storm 裡當降低 feedback 增益的防禦。 | ch04 |
| FCFS | 先到先服務 | 完全按到達順序出工的非搶占紀律；在「不看長度」家族裡等待變異最小，但在 slowdown 尺度上對短工作最殘忍。 | ch08 |
| forced flow law | 強制流量定律 | 各資源的流量被整體吞吐強制鎖定 Xᵢ=Vᵢ·X，把「每站各自的 RPS」綁回系統級吞吐與訪問比。 | ch02 |
| fork-join | fork-join | 一支工作扇出成 n 份並行、join 點要等全部完成的結構（Promise.all／scatter-gather 的數學身分）；它打破乘積形式，且 tail 由最慢分片決定。 | ch18 |
| G/G/1 | G/G/1 | 到達間隔與服務時間都是任意分布的單伺服器佇列——全書第一次正面承認「沒有封閉解、公式到頭了」。 | ch14 |
| goodput | 有用吞吐 | 真正完成且被下游收貨的速率；過載或 timeout 下可能遠小於 throughput，是 admission control 換來穩定性時付出的那一欄帳。 | ch07 |
| Gordon–Newell theorem | Gordon–Newell 定理 | 封閉網路版的乘積形式定理：乘積形式倖存，但要付 normalization constant G 的買路錢。 | ch17 |
| hazard rate | 危險率 | 「已撐過 t、下一瞬間結束」的條件速率 h(t)=f(t)/P(X>t)；常數（指數）／遞增 IFR／遞減 DFR 回答「等越久是好消息還是壞消息」。 | ch04 |
| heavy traffic | 重流量 | ρ→1 的飽和邊緣，等待是一段段長征裡許多小步的累積、由中央極限定理主宰——「飽和邊緣，世界只剩前兩階矩」。 | ch14 |
| heavy-tailed | 重尾 | 尾巴衰減比指數慢的分布：往右走固定倍數、尾巴才砍固定比例，會以三種方式讓「平均」這個你最信任的數字說謊。 | ch15 |
| hedged / tied requests | 對沖／綁定請求 | 同一筆請求發給多個副本搶最快回應（對沖：等過某分位才補發；綁定：誰先開工就取消其餘）——拿 fork-join 與重尾框架解讀的 tail 工程手段。 | ch04 |
| hockey stick | 使用率曲線 | E[T]∝1/(1−ρ) 那條壓測常見的曲棍球曲線：分母是剩餘容量 1−ρ，每砍半延遲翻倍、爆炸是漸近而非踩到開關。 | ch01 |
| insensitivity | 對服務分布不敏感 | 某些結果（Erlang-B、PS、IS、LCFS-PR）只透過 E[S] 依賴服務分布，直方圖長什麼樣都不影響——一個反覆出現的「為什麼它不在乎變異數」之謎。 | ch09 |
| inspection paradox | 檢視悖論 | 隨機時刻抵達時總撞上偏長的工作（長工作在時間軸上佔更多位置），使觀察到的工作系統性比 E[S] 長——殘餘服務時間 E[S²]/(2E[S]) 的來源。 | ch12 |
| Jackson network | Jackson 網路 | 帶 feedback 的開放網路裡，內部流即使不是 Poisson、穩態聯合分布仍逐站相乘、每站彷彿獨立 M/M/1 的驚奇結果。 | ch16 |
| jitter | 抖動 | 在 backoff 間隔上加的隨機擾動，用來去相關同步重試、壓低到達的 C²ₐ。 | ch04 |
| Kendall notation | Kendall 記號 | 用 A/S/c/K/… 六欄速記一個佇列模型（到達型式／服務分布／伺服器數／容量／母體／紀律）——全書的模型門牌。 | ch08 |
| Kingman approximation | Kingman 近似 | G/G/1 等待的萬用上界 E[T_Q]≈(ρ/(1−ρ))·((C²ₐ+C²ₛ)/2)·E[S]，本書的工程總綱。 | ch14 |
| Kleinrock conservation law | Kleinrock 守恆律 | 在「非搶占、不看長度」的紀律家族裡平均等待全部相同，且 ρ 加權的等待總和是不變量——排程只能重分配等待、不能消滅它。 | ch13 |
| leaky bucket | 漏桶 | 把叢發到達以固定間隔平穩放出的整形器，效果是把下游看到的 C²ₐ 壓低，代價是流量在整形器排隊。 | ch10 |
| Lindley recursion | Lindley 遞迴 | 等待時間的精確遞迴 W_{n+1}=max(0, Wₙ+Sₙ−A_{n+1})，可直接餵 production trace，也是 ch19 模擬的核心迴圈。 | ch14 |
| Little's Law | Little's Law | 平均人數＝到達率×平均停留時間 E[N]=λE[T]；與分布、排程、網路結構全無關——這個「無關」既是它的威力也是它的盲點。 | ch02 |
| loss system | 損失系統 | 沒位子就走、不排隊的系統（M/M/c/c），Erlang 在電話交換機房的原型問題。 | ch09 |
| M/G/1 | M/G/1 | Poisson 到達、服務時間任意分布的單伺服器系統；無記憶性一失，佇列長度不再是充分狀態，本書改走 mean-value 路線。 | ch12 |
| M/M/1 | M/M/1 | Poisson 到達、指數服務、單一伺服器——第一個能完整解出來的佇列，全書後續模型都是它的變奏。 | ch08 |
| M/M/1/K | M/M/1/K | 容量上限為 K 的單伺服器系統：第一次讓 ρ>1 合法，把 backpressure、load shedding 變成可算的定理。 | ch10 |
| M/M/c | M/M/c | c 台同質伺服器共用單一佇列的系統，生滅率在 n=c 處轉折，是池化威力與 Erlang 公式的舞台。 | ch09 |
| M/M/∞ | M/M/∞ | 伺服器多到永不排隊的系統，系統內人數服從 Poisson(a)、永不過載。 | ch09 |
| Markov chain | 馬可夫鏈 | 「狀態吃掉歷史」的隨機過程：給定現在、過去對未來無額外資訊；建模的真功夫在於把狀態選到足以裝下未來。 | ch06 |
| mean-field | 平均場 | N→∞ 極限下各佇列趨於漸近獨立、用平均值描述「佇列長度≥k 的比例」演化的近似——power-of-two-choices 的分析框架，也是 retry 雙穩態模型的理想化。 | ch20 |
| memorylessness | 無記憶性 | 已等過 s 再多等 t 的機率等於剛開始等 t 的機率 P(X>s+t∣X>s)=P(X>t)，連續分布中唯指數獨有——化簡推導的武器。 | ch04 |
| metastable failure | 準穩定故障 | 同一個外部 λ₀ 下系統存在「健康」與「崩潰」兩個自洽平衡，retry 把有效服務時間膨脹後，一個夠大的擾動就能從好平衡掉進壞平衡。 | ch20 |
| MVA | 平均值分析 | 不必算 normalization constant G、靠 arrival theorem 加兩次 Little's Law 的遞迴，直接算出封閉網路均值。 | ch17 |
| normalization constant (G) | 正規化常數 | 封閉網路乘積形式裡讓機率和為 1 的那個常數 G(N)，其計算量正是封閉網路難解、要靠 MVA 繞過的痛點。 | ch17 |
| offered load | 供給負載 | 無因次的 a=λ/μ，描述工作供給相對服務能力的強度（單伺服器時即 ρ、c 台時 ρ=a/c）。 | ch07 |
| operational analysis | 操作分析 | 只從可量測的吞吐、忙碌時間、人數出發、不做任何分布假設就成立的恆等式世界觀——每章機率模型的驗算器。 | ch02 |
| Palm–Khintchine | Palm–Khintchine | 大量互相獨立又個別稀疏的到達流疊加會趨近 Poisson——解釋為什麼真實到達這麼常像 Poisson，以及什麼時候破（相關、重試、批次）。 | ch05 |
| Pareto distribution | Pareto 分布 | P(S>t)=(k/t)^α 形式的重尾分布，α 決定矩的存在性：α≤2 變異數無限、α≤1 連均值都沒有。 | ch15 |
| PASTA | PASTA | Poisson 到達看到的狀態分布等於時間平均（Poisson Arrivals See Time Averages）——全書反覆偷用的隱形定理，但「到達看到的≠時間平均」並非顯然。 | ch08 |
| Poisson process | Poisson 過程 | 描述「到達」的標準隨機過程，有三張等價臉孔（指數間隔／獨立平穩增量＋Poisson 計數／微小區間 o(h) 刻畫），一個拿來模擬、一個算數、一個建模驗證。 | ch05 |
| Pollaczek–Khinchine formula | Pollaczek–Khinchine 公式 | M/G/1 平均等待 E[T_Q]=λE[S²]/(2(1−ρ))=(ρ/(1−ρ))·E[S]·(1+C²ₛ)/2，把「變異數本身就是延遲來源」定理化。 | ch12 |
| pooling | 池化 | 多台機器共用一條佇列勝過各自獨立排隊，因為「有人等、卻有機器閒」這種低效狀態在結構上被消滅。 | ch09 |
| power-of-two-choices | power-of-two-choices | 隨機挑兩台伺服器、派給較短的那條，就能讓佇列長度尾部從幾何級改善成雙指數級——隨機派工的便宜大躍進。 | ch21 |
| processor sharing (PS) | 處理器共享 | n 個工作同時各以 1/n 速率推進的理想化 time-sharing；平均回應只依賴 E[S]（insensitivity），公平的是比例 slowdown。 | ch13 |
| product form | 乘積形式 | 網路穩態聯合分布等於各站邊際分布的乘積 π(n₁,…,n_k)=Πᵢπᵢ(nᵢ)——「獨立性是穩態快照的性質，不是過程的性質」。 | ch16 |
| QED regime | QED 制度 | c≈a+β√a 時等待機率收斂到只依 β 的常數、使用率卻爬到接近 1 的品質效率雙贏區（Halfin–Whitt）。 | ch09 |
| reneging | 等到一半放棄 | 已排隊的客戶因耐心用盡而退出（timeout 的數學身分），把死亡率改成隨在場人數上升。 | ch10 |
| residual service time | 殘餘服務時間 | 到達者看到正在服務那件工作的剩餘時間，期望為 E[S²]/(2E[S])=E[S](1+C²ₛ)/2——P-K 公式裡那筆變異數帳的來源。 | ch12 |
| response time law | 回應時間定律 | 互動式封閉系統的恆等式 E[T]=N/X−Z，把使用者數、吞吐與 think time 綁在一起。 | ch02 |
| retry storm | retry 風暴 | retry＝feedback、加上 timeout 膨脹有效服務時間，形成自我增強的負載螺旋——metastable failure 的觸發機制。 | ch20 |
| reversibility | 可逆性 | 穩態 CTMC 倒著放的錄影在統計上與正放無從區分，等價於存在分布滿足 detailed balance——打開網路理論的鑰匙。 | ch11 |
| routing matrix | 路由矩陣 | 矩陣 P=(Pᵢⱼ)，記「在站 i 完成後以機率 Pᵢⱼ 去站 j」，是把呼叫圖翻成 traffic equations 的輸入。 | ch16 |
| service demand | 服務需求 | 一個工作在某資源上消耗的總服務時間 Dᵢ=Vᵢ·E[Sᵢ]，量法是「該資源忙碌時間÷系統完成數」——bottleneck 分析的單位。 | ch02 |
| slowdown | 延遲倍數 | 定義為 T/S（回應時間除以自身服務時間，「我多揹了幾倍」）；PS 下人人相同、FCFS 下短工作揹得最重。 | ch13 |
| square-root staffing | 平方根法則 | 緩衝開 √a 量級（c≈a+β√a）就夠把等待機率壓在常數的 staffing 法則，把「pool 該開幾台」從經驗值升級成定理。 | ch09 |
| SRPT | SRPT | 任何時刻優先服務剩餘工作量最小者的搶占排程，最小化每時刻系統內工作數、因而最小化平均回應時間——代價與「餓死長工作」的真相另算。 | ch13 |
| stationary distribution | 平穩分布 | 滿足 π=πP 的分布，三重身分合一：不動點、極限分布、軌跡上的時間佔比。 | ch06 |
| superposition | 疊加 | 多條獨立 Poisson 過程合併後仍是 Poisson、速率相加——「多個上游匯流」的保結構運算。 | ch05 |
| tandem queue | 串聯佇列 | 多個 M/M/1 首尾相接，由 Burke 定理保證中間流仍是 Poisson，使穩態聯合分布呈乘積形式。 | ch11 |
| thinning | 分流 | 對 Poisson 過程每個到達獨立擲幣決定去向，每條子流仍是 Poisson 且互相獨立——「按機率路由到 shard」的保結構運算。 | ch05 |
| token bucket | token bucket | 容量 B、補充速率 r 的速率限制器：容忍 B 的叢發、長期把平均速率壓到 ≤r 的 admission control。 | ch10 |
| traffic equations | 流量方程 | 網路各站的流量守恆方程組 λᵢ=外部到達ᵢ+ΣⱼλⱼPⱼᵢ，先解這套流量帳、等待帳才說得清。 | ch16 |
| utilization law | 使用率定律 | ρ=X·E[S]，把看似獨立的監控指標（吞吐、平均服務時間、使用率）鎖死在一起。 | ch02 |
| visit ratio | 訪問比 | 一個工作平均經過某站幾次 Vᵢ，由 routing matrix 從 traffic equations 生出來——service demand 與 bottleneck 分析的因子。 | ch02 |
| VUT formula | VUT 公式 | 把 Kingman 近似讀成「等待 ≈ 變異性 × 使用率 × 時間」(Variability × Utilization × Time)，當全書的工程世界觀。 | ch14 |
| warmup / transient | 暖機／初始暫態 | 從空系統起跑的前段量測會系統性偏低，必須丟棄才能估到穩態——模擬騙人的第一條途徑。 | ch19 |
| work conservation | 工作守恆 | 未完成工作總量的時間軌跡對所有 work-conserving 紀律逐點相同、與出工順序無關——排程「總量不變、分配可選」的地基。 | ch12 |

## 編表說明：先點名、後定義的詞

下列詞在「首次出現章」之前曾被前面章節**點名或埋伏筆**，但本表的章號取它**真正下定義並使用**的章，以免一句話定義與你查到的章節對不上：

- **Kendall notation**：ch01 以 D/D/1 第一次出現並命名，**正式定義在 ch08**（本表取 ch08）。
- **inspection paradox**：ch04 在殘餘壽命處立牌預告，**一般版的定義與計量在 ch12**。
- **hedged / tied requests**：ch04 以「hedged read」紙上推演首次登場，**工程化解讀（綁定請求、Tail at Scale）在 ch20**。
- **exponential backoff／jitter**：ch04 先釐清「指數」的命名撞車，**當防禦手段展開在 ch20**。
- **insensitivity**：ch09 在 Erlang-B 處首次點名，**完整兌現在 ch13（PS）與 ch18（BCMP）**。
- **admission control／goodput**：ch07 的生滅 worked example 首次出現，**完整的丟棄三角在 ch10、retry 防禦在 ch20**。
- **VUT formula**：與 Kingman 近似同章（ch14）；其工程世界觀在 ch20、ch21 收束。
