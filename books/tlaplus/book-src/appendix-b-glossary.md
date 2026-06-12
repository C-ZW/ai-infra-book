# 附錄 B — 術語表

> 全書術語的 EN–ZH 對照與一句話定義，從 ch01–ch18 的實際內容萃取，依英文字母排序；書中未出現的術語不收。「首次出現」指該術語**正式登場並獲得解說**的章——個別名詞曾在更早的章節（尤其 ch01 的全景地圖）以一句話前瞻露面，不另計；一詞分「直覺版→正式版」兩階段深化者，記直覺版首次解說的章，並在定義內標注正式化的章。定義口徑以各章原文為準，這裡只是索引，細節請回到該章。

## A

- **action**（動作）｜同時含 unprimed（步前）與 primed（步後）變數的布林運算式，述說「一步」前後狀態的關係——TLA 的核心發明。｜ch06
- **AllPaid**｜結算系統的 liveness 性質名：每則訊息終會入帳（∀ m ∈ Msgs : ◇ ledger[m]）；不配 fairness 它不成立。｜ch07
- **Alloy**｜把世界建模成「集合與關係」的設計層工具：Analyzer 將約束翻成 SAT，在指定的 small scope 內窮舉結構、把反例實例畫成圖——問「存不存在壞結構」而非「會不會走到壞狀態」。｜ch18
- **Alpern–Schneider 分解定理**｜任何性質都可以寫成一條 safety 與一條 liveness 的合取。｜ch07
- **Apalache**｜符號式模型檢查器：不搬狀態、改解方程——把 Init 與 Next 編成 SMT 約束，可吃無限值域；承諾有界（找不到反例只代表「k 步之內沒有」），另可用來檢查歸納不變量。｜ch16
- **at-least-once**｜佇列的交付保證：每則訊息至少投遞一次，代價是可能重複——SQS 的 visibility timeout 重投遞即此。｜ch01
- **auxiliary variable**（輔助變數）｜為了讓 refinement mapping 寫得出來而給實作加的「只寫不讀」變數，分 history 與 prophecy 兩類；不影響協議的任何 guard 或轉移。｜ch15

## B

- **bag / multiset**（多重集）｜「元素 ↦ 正整數份數」的函數——建模 at-least-once 的訊息該用 set 還是 bag，是 ch04 的誠實選擇題。｜ch04
- **ballot**｜Paxos 多輪投票的輪次編號，全序；直覺對應 optimistic lock 的版本號。｜ch12
- **behavior**（行為）｜一條（可無限長的）狀態序列：起點是合法初始狀態，每對相鄰狀態都是某條動作規則允許的步。｜ch02
- **BFS**（廣度優先搜尋）｜TLC 主迴圈的遍歷方式：FIFO 佇列逐層展開可達狀態——因此反例 trace 天生是最短路徑。｜ch09
- **blocking**（卡死）｜協議在無人違規的情況下永遠無法前進——2PC 在 TM 故障時讓 prepared 的 RM 永遠等待（in-doubt transaction），是「不犧牲一致性」的本質代價，不是實作 bug。｜ch11
- **bound variable / free variable**（約束變數／自由變數）｜量詞自己的「迴圈變數」是約束的，scope 只在量詞之內；式子的真假取決於外層誰來填的變數，是自由的。｜ch03
- **bounded waiting**（有界等待）｜對手至多插隊一次之後自己必然進場——Peterson 給出的、比 starvation-freedom 更強的保證。｜ch10

## C

- **CompCert**｜經機器證明的 C 編譯器（以 Rocq 證明），定理是「編譯不改變程式語意」——程式碼級驗證的代表作。｜ch16
- **conformance checking**｜確保程式碼真的長得像 spec；MongoDB 用 trace-checking（MBTC）與 model-based test-case generation（MBTCG）兩招實測，結論是貴到必須在寫 spec 之初就為它設計。｜ch17
- **consensus**（共識）｜一群行程要從各自提議的值裡選定一個，要求三條：Agreement（至多選定一個值）、Validity（選定的值必須有人提議過）、Termination（終究要選定）。｜ch12
- **counterexample trace**（反例 trace）｜模型檢查器的輸出：從初始狀態走到出錯的一條具體路徑，像一份完美的 bug report；BFS 保證它最短（讀法見 ch09）。｜ch01
- **critical section**（臨界區）｜兩個 process 要共用、但不准同時進入的那段程式；進出各有 entry protocol 與 exit protocol。｜ch10

## D

- **Dafny**｜把驗證內建進程式語言：函式上寫 pre/post-condition、迴圈寫 invariant，SMT 求解器邊打字邊逐條檢查——程式碼級驗證最平易近人的入口。｜ch18
- **deadlock**（死鎖）｜沒有任何後繼（所有動作皆不 enabled）的狀態；TLC 預設把它當錯誤回報，與「系統做完了」的良性終局要分清。｜ch09
- **deadlock-freedom / starvation-freedom**｜互斥問題的兩級 liveness：前者「只要有人想進，就有人終會進去」；後者更強，「每個想進的 process 自己終會進去」。｜ch10
- **deterministic simulation testing**（DST）｜把調度變成可控輸入：整個叢集跑在同一個單執行緒模擬器裡，一切非決定性由帶種子的偽亂數供應——同一個種子可逐位元重放同一場災難（FoundationDB 路線）。｜ch18
- **DieHard**｜3 與 5 加侖壺量出 4 加侖的經典謎題 spec；示範「把目標寫成 invariant 的否定、讓反例變成解」的招式。｜ch08

## E

- **Election Safety**｜Raft 五條 safety 性質之一：一個 term 至多選出一個 leader。｜ch13
- **ENABLED**｜狀態述語：ENABLED A 在狀態 s 為真 ⟺ 存在 t 使 ⟨s, t⟩ 滿足 A——「這種步走得出去」；注意 enabled 不等於會發生。｜ch06
- **Event-B**｜把 refinement 當整個方法骨架的規格語言：從極抽象的機器逐步精化到貼近實作，每步精化自動產生 proof obligations，配套的 Rodin 平台管理整條證據鏈。｜ch18
- **exactly-once**｜「同一則訊息恰好處理一次」的語義；本書把「at-least-once＋dedup 實作了 exactly-once」這句黑話定理化，並誠實拆帳：safety 那一半（至多一次）是 refinement 定理，liveness 那一半（終將入帳）掛在 fairness 的帳上。｜ch15

## F

- **fairness**（公平性）｜加在 Spec 後面的合取項，砍小行為集合、排除「明明可以做事卻永遠拖著」的劇本——liveness 主張的必要假設，分 WF 與 SF 兩種強度；它是假設，不是機制。｜ch07
- **fingerprint**（指紋）｜TLC 給每個狀態算的 64-bit 雜湊，只存指紋以省記憶體；代價是碰撞——後到的狀態被誤判「看過了」、其後整片子圖無聲消失，所以 TLC 的紅燈永遠是真的、綠燈帶一個機率上的星號。｜ch09
- **FLP 不可能定理**｜非同步系統裡只要有一個行程可能 crash，就不存在既是確定性、又保證必然終止的共識演算法——所以 Paxos 選擇 safety 無條件、liveness 看天吃飯。｜ch12
- **formal methods**（形式化方法）｜用數學描述並驗證系統的方法總稱；全景地圖兩軸：驗哪個層次（規格層 vs 程式碼層）、怎麼驗（自動找反例 vs 人寫證明）。｜ch01
- **function**（函數）｜由定義域（domain，合法輸入的集合）與「每個輸入恰好一個值」完全決定的表——TLA+ 的世界觀：函數＝總是查得到的表。｜ch04

## H

- **history variable**（歷史變數）｜只為證明而活的輔助變數：把實作已經丟掉的歷史抄寫進狀態，讓性質寫得成狀態述語；不出現在實作中、不影響任何轉移。｜ch13

## I

- **inductive invariant**（歸納不變量）｜滿足不變量規則兩前提的述語：所有初始狀態滿足它，且從**任何**滿足它的狀態（包括不可達的）走任何一步仍滿足——全書最重要的單一概念；invariant 為真不代表 inductive。｜ch05
- **Init / Next / Spec**｜TLA+ spec 的三件套：Init 是圈出合法起始狀態的狀態述語；Next 是諸具名 action 的析取；Spec ≜ Init ∧ □[Next]_vars，一條公式圈出所有合法 behavior。｜ch06
- **INSTANCE**｜TLA+ 裡寫 refinement mapping 的語法：引入模組＝做代換（substitution），把抽象 spec 的變數用實作的狀態函數（WITH 子句）代掉。｜ch15
- **interactive theorem prover**（互動式定理證明器）｜把「證明」本身變成一種程式設計，每一步在型別檢查器監督下構造——嚴謹度光譜最右端：Lean、Rocq、Isabelle。｜ch16
- **interleaving**（交錯）｜把多個執行緒的步驟合併成一條序列、各自內部順序不變的一種調度；交錯數隨步數組合爆炸，測試只能對它抽樣。｜ch01
- **invariant**（不變量）｜在**每一個可達狀態**都為真的狀態述語——「壞事永遠不會發生」主張的標準形狀。｜ch02
- **Isabelle**｜老牌互動式定理證明器，代表作 seL4；客製版 Isabelle/TLA+ 同時是 TLAPS 的壓陣後端。｜ch16

## L

- **lasso**（套索）｜有限狀態圖上無限 behavior 的形狀：一段有限前綴＋一個循環；TLC 檢查 liveness＝找滿足 fairness 的壞 lasso，循環都住在 SCC（強連通分量）裡。｜ch09
- **Leader Append-Only**｜Raft 五條 safety 性質之一：leader 絕不改寫或刪除自己的 log，只追加。｜ch13
- **Leader Completeness**｜Raft 五條 safety 性質之一：某 term 內提交的 entry，必出現在所有更高 term 的 leader 的 log 裡。｜ch13
- **leader election**｜Raft 的選舉機制：follower 逾時轉 candidate、term 加一、投自己一票並向全體拉票，拿到過半選票就成為該 term 的 leader；投票受兩條鐵律約束。｜ch13
- **Lean 4**｜Lean FRO 維護的定理證明器兼程式語言，配協作數學庫 mathlib（從大學課程蓋到研究前沿）——深度數學端的代表。｜ch16
- **lightweight formal methods**（輕量級形式化方法）｜不上重型證明的形式化路線——如 S3 ShardStore 的 Rust 參考模型＋property-based testing；用較小成本買部分保證。｜ch17
- **liveness**（活性）｜「好事終究會發生」；違反它的證據永遠湊不齊有限版本——「再等等」永遠是合法辯護。正式定義（任何有限前綴都還有救）見 ch07。｜ch02
- **log replication**｜Raft 的強 leader 複製：所有寫入走 leader、log 單向推給 followers；entry 複製到過半且屬於 leader 當前 term，才推進 commitIndex（提交）。｜ch13
- **Log Matching**｜Raft 五條 safety 性質之一：兩份 log 若在同一 index 有同 term 的 entry，則到該 index 為止整段相同。｜ch13
- **loop invariant**（迴圈不變量）｜進迴圈前成立、每圈保持、結束時收割結論的述語——歸納不變量在單機程式裡的近親。｜ch05

## M

- **mathematical induction**（數學歸納法）｜P(0) 成立、且 ∀ n : P(n) ⇒ P(n+1)，則 P 對所有自然數成立——證明「永遠」的唯一有限手段；變體有強歸納（假設所有更小的數都成立）與結構歸納（順著歸納定義的形狀走）。｜ch05
- **model checking**（模型檢查）｜機器自動窮舉（或符號化覆蓋）狀態空間、找性質的反例；輸出反例 trace，極限是通常只能在有限的小模型上窮舉。｜ch01
- **MODULE / EXTENDS / CONSTANTS / ASSUME / VARIABLES / THEOREM**｜spec 解剖學的骨架關鍵字：模組命名與組織單位／引用哪些標準模組／哪些參數先宣告不寫死／參數必須滿足的前提／狀態由哪些變數組成／作者主張這份 spec 滿足什麼。｜ch08
- **mutual exclusion**（互斥）｜只用原子讀寫、不靠現成的鎖，保證兩個 process 不同時進入臨界區的問題；本書性質名 `MutualExclusion`：任何時刻至多一個 process 在臨界區。｜ch10

## N

- **NoDoublePay**｜結算系統的 safety 性質名：同一個 msgId 至多入帳一次——全書貫穿的 safety 範例，v1 寫成 ∀ m ∈ Msgs : ledger[m] ≤ 1。｜ch02
- **nondeterminism**（非決定性）｜一個狀態可走多條規則、沒有人決定走哪條：規格只回答「允不允許」，不回答「多常發生」、不附機率——crash 與重送都這樣建模。｜ch02

## P

- **P**｜把系統寫成一組互傳事件的 communicating state machines 的語言；spec 可執行，配套 checker 系統性探索訊息交錯與故障注入——AWS 主力工具箱成員。｜ch18
- **P2c**｜Paxos 的核心不變量（沿 Lamport 編號，蘊涵 P2 與 agreement）：發出提案 ⟨n, v⟩ 之前必須有多數集 S 作證——要嘛 S 是白紙、要嘛 v 抄自 S 中編號最高的已接受提案；phase 1/2 的每條規則都是它的影子。｜ch12
- **Paxos**｜共識問題的標準答案：ballot＋兩階段＋quorum intersection；safety 無條件成立（任何交錯、延遲、少數 crash），liveness 依賴時序假設。｜ch12
- **Paxos Commit**｜把 2PC 裡「TM 的那個決定」本身交給容錯共識：用 2F+1 個協調者跑 Paxos，拔掉單點。｜ch11
- **Peterson algorithm**｜Gary Peterson（1981）的兩 process 互斥解：旗子＋禮讓變數，兩頁論文的簡潔答案；本書第一場全狀態空間手推的主角。｜ch10
- **Phase 1 / Phase 2**｜Paxos 的兩階段：phase 1（prepare）要求 acceptor 承諾（promise）不再接受更小編號、並交出已接受的最高票；phase 2（accept）收齊多數回應後發出提案——歷史不空就只能抄最高票的值。｜ch12
- **PlusCal**｜寫在 `.tla` 註解區塊裡的演算法語言，由翻譯器轉成 TLA+ 之後才能餵給工具（翻譯產物用 pc 變數記錄「執行到哪個標籤」）；本書只要求看得懂、不要求會寫。｜ch08
- **predicate**（述語）｜帶洞的命題：填入具體值之前沒有真值；「對單一狀態非真即假的判斷句」是狀態述語。｜ch03
- **prepared**｜2PC 裡 RM 表態過「我這邊可以 commit」之後的狀態：再也不能單方面 abort，只能等 TM 的決定——blocking 的人質。｜ch11
- **proof obligation**（證明義務）｜一小句「在這些事實之下，這個斷言成立」；TLAPS 把層級證明拆成一條條義務丟給後端 prover 逐條查驗——紅一條，整份不算。｜ch16
- **property-based testing**（PBT）｜寫「對任意輸入，性質 P 成立」，框架生成幾百組輸入轟炸實作，找到反例自動 shrinking 成最小重現輸入；寫 property 的能力＝寫 invariant 的能力，但它仍是抽樣、對併發遲鈍。｜ch18
- **prophecy variable**（預言變數）｜補充「實作還沒決定的未來」的輔助變數：把未來的決定搬進現在的狀態，某些 refinement mapping 非它不可（完整理論見 Lamport–Abadi）。｜ch15
- **proposer / acceptor**｜Paxos 的兩種角色：proposer 發起提案（phase 1 拉承諾、phase 2 發 accept）；acceptor 負責投票，多數 acceptor 接受同一提案＝該值被選定。｜ch12
- **proposition**（命題）｜一個非真即假的宣告句——邏輯的原子單位。｜ch03

## Q

- **Quint**｜TLA+ 語意的現代語法外衣：有型別、語法像現代程式語言、內建模擬器，要做真正的模型檢查時接 Apalache 當後端——換的是皮，不是骨。｜ch18
- **quorum**（多數派）｜任何 ≥ 過半的子集；唯一重要的性質是任兩個 quorum 必有交集（quorum intersection）——把兩個決定綁在同一個證人身上、逼它們相等的唯一槓桿。｜ch12

## R

- **Raft**｜把 understandability 當一級需求的共識演算法：強 leader、term 邏輯時鐘、五條 safety 性質；結果與 (multi-)Paxos 等價、效率相當，但結構為了好懂而重排。｜ch13
- **record**｜定義域是欄位名的函數——JSON object 的數學形狀。｜ch04
- **refinement**（精化）｜「實作正確」的定理形狀：規格與實作都是時序公式，Impl ⇒ Spec——實作允許的行為集合是規格的子集。｜ch15
- **refinement mapping**（精化映射）｜用狀態函數把實作狀態映到規格狀態的「眼鏡」：每個實作步映成一個規格步或 stuttering——戴上它看實作，就看到規格的世界。｜ch15
- **resource manager（RM）**｜分散式交易中各自做本地工作、對「能不能 commit」表態的參與者；rmState ∈ {"working", "prepared", "committed", "aborted"}。｜ch11
- **Rocq**｜互動式定理證明器，原名 Coq（2025-03 隨 9.0 版改名，舊文獻兩名同物）；代表作 CompCert。｜ch16

## S

- **safety**（安全性）｜「壞事永遠不會發生」；違反的證據是有限的——走到第 k 步出事，當場定罪。正式定義（有限前綴刻畫）見 ch07。｜ch02
- **seL4**｜一個 microkernel 的 C 實作被 Isabelle 證明在功能上符合其抽象規格——全程式碼驗證「做得到」的存在性證明，也是成本的刻度原器（人力以人年計）。｜ch16
- **set**（集合）｜由成員資格唯一決定的「一堆東西」：對任何 x，「x ∈ S」有明確的是或否；無順序、無重複。｜ch04
- **SF / strong fairness**（強公平性）｜SF_v(A) ≜ □◇(ENABLED ⟨A⟩_v) ⇒ □◇⟨A⟩_v：反覆可做（哪怕斷斷續續）的動作終究要做——對得起反覆 crash-restart、卻總會被拉起來的 consumer。｜ch07
- **small scope hypothesis**｜經驗賭注：絕大多數設計層 bug 在很小的參數下就有反例；輸的方式已知——性質涉及「數量本身」時，小參數連反例的舞台都搭不起來，所以要把驗過的參數寫進結論。｜ch09
- **SMT**｜把命題編成約束交給求解器的自動推理路線：TLAPS 的預設後端（Z3）、Apalache 的引擎；擅長算術與基本的集合、函數推理，怕量詞層層疊的式子——搞不定就拆步驟。｜ch16
- **spec drift**（spec 腐化）｜spec 也是文件、一樣會腐化，且頂著「已驗證」光環腐化得更危險；不是「會不會」的問題，是「漂移速度 vs 對齊頻率」的維運題。｜ch17
- **specification**（規格）｜一個系統的規格＝它**允許的行為的集合**；「系統正確」＝實際發生的每一條行為都落在集合裡——規格是立法，不是執行流程的描述。｜ch02
- **SPIN / NuSMV**｜「TLC 的長輩們」：SPIN 是顯式狀態模型檢查的元老（Promela 語言、LTL 性質）；NuSMV 走符號路線（BDD），出身硬體驗證。｜ch18
- **split vote**｜多個 candidate 同時發起選舉、票數均分、無人過半，只好下一輪再來——重試碰撞的 Raft 版，用隨機化逾時（jitter）化解。｜ch13
- **starvation**（餓死）｜系統整體有進展，但某個 process 永遠等不到它要的——與 deadlock（全體卡死）並列的兩種「卡」。｜ch10
- **state**（狀態）｜給每個變數各指定一個值的一組賦值——整體快照，不是單一變數；併發 bug 多藏在「各自合理、合起來不合理」的組合裡。｜ch02
- **state explosion**（狀態爆炸）｜狀態數隨變數值域相乘、隨參與者數指數成長的現象——模型檢查的根本敵人；緩解手段：constraint、symmetry、抽象。｜ch09
- **state machine**（狀態機）｜「初始狀態＋轉移規則」的極簡結構（不是 regex 的有限自動機）；本書世界觀：一切系統都是狀態機。｜ch02
- **State Machine Safety**｜Raft 五條 safety 的端到端承諾（論文稱 the key safety property）：一台 server 在某 index apply 了某 entry，就不會有任何 server 在同一 index apply 不同的 entry。｜ch13
- **state space**（狀態空間）｜所有可能的變數賦值組合；它與「實際走得到的可達狀態」是兩回事——這個區分是 ch02 後半的主角。｜ch02
- **step**（步）｜一對前後狀態 ⟨s, t⟩；哪些步被允許由動作規則決定——前提說何時可走，效果說每一個變數變成什麼。｜ch02
- **strengthening**（強化）｜目標性質不 inductive 時，在它上面疊輔助述語讓歸納封得起來的動作；ch14 把它升級成「從卡住的歸納步讀出壞前驅、判可達性、再強化」的迴圈。｜ch05
- **stuttering**｜「什麼都不動」的步：□[Next]_vars 裡 vars′ = vars 的免責條款。允許不動不是寬鬆，是讓「實作蘊涵規格」在數學上可能成立的先決條件（ch15 兌現）。｜ch06
- **symmetry reduction**（對稱化簡）｜宣告對稱集合後，同構（互為置換）的狀態只算一次——把整條軌道坍縮成一個代表點的狀態空間緩解手段。｜ch09
- **Synod**｜single-decree Paxos 的本名：定案**一個**值的協議；Multi-Paxos＝逐 slot 各跑一個 Synod 實例來定案一串值（replicated log）。｜ch12

## T

- **TCommit**｜Lamport 的交易承諾「規格」spec：只寫「什麼叫對」（全體對結果收斂、TCConsistent），不寫怎麼做到——與 TwoPhase 構成 refinement 的活教材。｜ch11
- **TCConsistent**｜交易承諾的 safety 性質：不准有 RM aborted 的同時另一個 RM committed。｜ch11
- **temporal logic**（時序邏輯）｜對整條 behavior 說話的第三層詞彙（狀態述語談單一狀態、action 談一步）：□ 永遠、◇ 終將、⤳ 導至。｜ch07
- **term**｜Raft 的邏輯時鐘：單調遞增的整數、每個 term 至多一個 leader；訊息都蓋 term 戳章，舊 term 一律被打回票——世代編號（epoch / generation）的直覺。｜ch13
- **theorem proving**（定理證明）｜人寫證明、機器逐步查證每個推理義務；輸出是對任意參數、無限狀態都成立的定理——代價是人的腦力，且卡住時不會給你反例。｜ch01
- **Three-Phase Commit（3PC）**｜在 prepared 與 committed 之間再插一個 pre-commit 階段來換非阻塞；代價是 network partition 之下賠掉 safety——把卡死換成不一致，所以生產環境幾乎不用。｜ch11
- **TLA**（Temporal Logic of Actions）｜Lamport 的動作時序邏輯：把「一步前後關係」的 action 放進時序邏輯——TLA+ 的邏輯核心。｜ch06
- **TLA+**｜以 TLA 為邏輯核心、ZF 集合論為數學底的規格語言；一門語言配三個引擎：TLC 窮舉、Apalache 符號檢查、TLAPS 證明。｜ch01
- **TLAPS**｜TLA+ 的證明系統：proof manager 把 ⟨1⟩ 層級證明拆成一條條 proof obligation，逐條交給後端 prover（SMT／Zenon／Isabelle／LS4）查驗——能證任意參數的定理，漏格在語法上不可能。｜ch16
- **TLC**｜顯式狀態（explicit-state）模型檢查器：BFS 窮舉有限參數下的可達狀態、檢查性質、回報最短反例 trace；有限參數的窮舉 ≠ 定理。｜ch09
- **transaction manager（TM）**｜2PC 的協調者：phase 1 收集全員 prepared、phase 2 廣播決定——單點，它在收齊後、廣播前倒下就是 blocking。｜ch11
- **tuple**｜有序、定長、可重複的 ⟨…⟩；sequence 是長度不固定的 tuple，1-indexed——array 的數學形狀。｜ch04
- **Two-Phase Commit（2PC）**｜交易承諾（transaction commit）問題的經典解：phase 1 問全員「能否 commit」收 prepared，phase 2 廣播決定；不犧牲一致性，代價是 TM 故障時 blocking。｜ch11
- **TwoPhase**｜Lamport 的 2PC 協議 spec：把 TCommit 的上帝視角拆成訊息；spec 的最後一行就主張「TwoPhase 實作了 TCommit」。｜ch11
- **TypeOK**｜型別不變量：用狀態述語把每個變數的值域主張出來——TLA+ 沒有型別系統，所以它幾乎總是 spec 的第一個 invariant，而且通常自己就 inductive。｜ch08

## U–V

- **UNCHANGED**｜UNCHANGED v ≜ v′ = v 的縮寫——「沒提到的變數不是隨便，是不變」必須明寫，漏寫是 action 最常見的 bug。｜ch06
- **understandability**｜Raft 的設計目標：把「好懂」當成一級設計需求，結構為此重排——與 Paxos 對照的主軸是「複雜度被搬去哪了」。｜ch13
- **vacuous truth**（空洞為真）｜前件為假則蘊涵式整句為真——invariant「假通過」的頭號機制：連壞事的原料都沒生出來，性質當然成立。｜ch03

## W–Z

- **WF / weak fairness**（弱公平性）｜WF_v(A) ≜ ◇□(ENABLED ⟨A⟩_v) ⇒ □◇⟨A⟩_v：一個動作不可以「永遠可做卻永遠不做」——對得起一台持續健康的 consumer。｜ch07
- **ZF set theory**（ZF 集合論）｜TLA+ 的數學底：一切皆集合——數字、tuple、函數、record 原則上都能編碼成集合；直接後果是 TLA+ 沒有型別系統。｜ch04
