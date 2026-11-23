# 第 30 章：符號執行、約束求解與混合式 Fuzzing

上一章我們用 **AFL++** 的 `65,536 bytes`（`64 KiB`）邊緣覆蓋率位圖配上 `5,000 exec/s` 的 Persistent Mode，幫 C 與 Rust 解析器建起了高吞吐量的灰箱變異迴圈。只要擋在前面的條件是單純的長度比較或幾個獨立 byte，突變器靠位元翻轉跟字典檔，幾分鐘內就能把淺層路徑全部掃平。

但真實世界的二進位解析器，哪會讓所有分支都這麼好進？在 **NexusPay** 的原生模組 `libnexus-parse`（第 20 到 25 章）裡，除錯與特權結算分支通常鎖在好幾道條件關卡後面：`8 bytes` 的 TLV 檔頭不只要對準魔數 `magic == 0x4E58`、特定的 `type` 與旗標遮罩，最後還得通過一個把檔頭（`magic`、`type`）跟核心負載（`flags`、`amount_delta`）攪在一起算出來的 32 位元校驗和。

對純隨機或覆蓋率導引的 Fuzzer 來說，只要改動前面受校驗的欄位卻沒跟著重算校驗值，這關就永遠過不去。單靠 `5,000 exec/s` 無放回逐一盲猜一個 32 位元精確等式，最壞得跑完 `4.29 × 10^9` 次執行，足足要燒掉單核將近 `10 天` 的時間，而且這十天裡 `64 KiB` 覆蓋率位圖連半點漸進回饋都不會給。

要打破這道死牆，就得請出自動化漏洞挖掘的另一顆引擎：**符號執行**（Symbolic Execution）、**SMT 約束求解**（Satisfiability Modulo Theories）與**混合式 Fuzzing**（Hybrid Fuzzing）。

我們不再拿盲猜的位元組去硬撞條件判斷，而是把輸入宣告成代數符號，順著執行路徑把沿途所有 `if` 條件收集成聯立方程式，直接丟給 **Z3** 的位元向量求解器反解出通關輸入。最後再靠 **angr** 與 **SymCC / SymQEMU** 把這些「通關鑰匙」即時餵回給 AFL++，讓高吞吐量突變器得以衝進深層狀態機裡。

---

## 從你已知的出發

為什麼 CodeQL 看得到深層的危險 Sink、AFL++ 每秒能跑五千次測試，兩個人加起來卻還是拿一行 `if (checksum(pkt) == pkt->csum)` 沒輒？因為靜態資料流分析雖然能一眼看穿整張控制流圖（CFG），但它對執行期變數採取過度近似（over-approximation），算不出多條複雜的位元算術在真實記憶體裡到底能不能同時成立。

反觀灰箱 Fuzzing 跑的雖然是貨真價實的機器碼，卻對「條件為什麼不成立」一無所知。面對 32 位元校驗和，固定其他欄位時只有唯一一個合法值，均勻獨立抽樣一次猜中的機率只有 `2^-32`，單步翻轉幾個 bit 更是連邊都摸不著。

就算打開編譯期的比較拆分（像是 `afl-clang-lto` 的 CMPLOG / Redqueen 或 Laf-Intel），Fuzzer 也只能把「常數跟單一輸入欄位的直接比對」（例如 `magic == 0x4E58`）拆成一個個 byte 慢慢湊。一旦條件變成多變數的非線性組合（例如把旗標旋轉移位後加上負載乘積，再對 `2^32` 取餘數），輸入跟比較指令不再有一對一的直覺關係，CMPLOG 就會徹底失去方向。

這正是符號執行登場的時刻：它用跟真實 CPU 一模一樣的位元運算語意，把沿途每一道分支條件都寫成固定寬度的位元向量（Bit-Vector）代數方程式，把「覆蓋率卡關」直接變成「代數方程組求解」。

---

## 機制與推導

### 攻擊者目標與實質影響

當漏洞研究員或攻擊者把符號執行與混合式 Fuzzing 搬上檯面時，目的並不是要幫整套系統做形式化數學證明（像 Coq 或 TLA+ 那種定理證明是另一個世界的事），而是為了拿到三個能直接變現的實戰成果：

第一是**在幾十毫秒內擊穿魔數、旗標遮罩與校驗和閘門**。不管是私有 RPC 協定、VPN 封包解碼器，還是像 `libnexus-parse` 這種高價值的原生解析模組，都很喜歡把內部管理指令或複雜狀態機藏在魔數與 32 位元校驗和後面。符號引擎能在 `< 50 ms` 內直接解出合法的通關封包，把原本躲在深處的高危匯點（像整數溢位回繞或堆積 UAF）直接拉進攻擊半徑裡。

第二是**把「走得到漏洞」精準升級成「可利用原語」**。有時候光是走進漏洞函式還不會崩潰。研究員可以直接把利用條件寫進 SMT 約束裡——例如強迫 `len + 8` 在 32 位元無號加法下剛好回繞成 `0`（也就是第 25 章的 `0xFFFF_FFF8`），或是強迫兩個相鄰的記憶體配置剛好落進同一個 `0x20` 的 tcache bin 尺寸區間——讓求解器直接吐出一顆自帶精準記憶體破壞效果的 PoC。

第三是**解開灰箱 Fuzzer 的覆蓋率死鎖，大幅壓縮 0-day 挖掘時間**。純符號執行跑得太慢，純 Fuzzing 又撞不破數學關卡。混合式架構讓符號引擎只專心破解卡住 AFL++ 的那幾個硬骨頭分支，解出具體種子後立刻丟回共享佇列，接著再交由 AFL++ 用 `5,000 exec/s` 的全速把關卡後面的幾百條深層分支一網打盡。

---

### 符號執行原理：符號狀態與路徑條件（Path Constraints）

先看這段簡單的 C 語言檔頭檢查：

```c
uint16_t magic = *(uint16_t *)buf;
if (magic == 0x4E58) {
    // 進入深層解析
}
```

程式正常執行時，暫存器跟記憶體裡裝的都是確定的**具體數值**（concrete values，比如 `0x10`）。但在符號執行裡，我們會把外部輸入（不管是 `stdin`、封包緩衝區還是命令列參數）宣告成未知的**符號變數**（Symbolic Variables，記為 `α_0, α_1, ..., α_{n-1}`），程式裡所有算出來的值，全都變成由這些符號組成的抽象語法樹（AST）。

在任何一個時間點，符號執行引擎手上的狀態都可以用一個三元組 `(pc, σ, π)` 來表示：
- **`pc`（Program Counter）**：目前準備執行的指令位址（或中介碼 IR 的位置）。
- **`σ`（Symbolic Store）**：記錄每個變數、暫存器或記憶體位址目前對應到哪一條**符號算式**的狀態表。比如輸入的前兩個 byte 是符號 `α_0` 跟 `α_1`，跑完上面的小端序 16 位元讀取後，`σ[magic]` 裡面裝的就是 `Concat(α_1, α_0)`。
- **`π`（Path Constraint，路徑條件）**：一路累積下來的布林邏輯合取式（AND 條件），記載著「程式要從起點一路走到現在這個 `pc`，輸入必須同時滿足哪些條件」。剛起步時還沒遇到任何分支，所以 `π = true`。

當執行流撞上一個條件分支 `if (cond)` 時，符號執行引擎不像真實 CPU 只挑一邊走，而是把兩邊的可能都攤開來，向背後的 SMT 求解器發出兩個詢問：
1. **True 分支走得通嗎？** 詢問 `SAT(π ∧ cond)`。如果有解，就複製出一份新狀態，把它的路徑條件更新成 `π' = π ∧ cond`，然後把 `pc` 移到 True 分支。
2. **False 分支走得通嗎？** 詢問 `SAT(π ∧ ¬cond)`。如果有解，就複製出另一份新狀態，把路徑條件設為 `π'' = π ∧ ¬cond`，並把 `pc` 移到 False 分支。

如果某一邊被求解器判定為 `UNSAT`（無解，例如前面已經走過 `len <= 65536`，後面又冒出一個 `if (len > 100000)`），引擎就會當場把這條死路剪掉（prune），半點算力都不會浪費。

#### 靜態符號執行（SSE）與動態／Concolic 執行（DSE）

實戰中，符號執行分成兩條流派，怎麼選完全取決於你的目標有沒有複雜的系統呼叫跟外部函式庫相依：

第一種是**純靜態符號執行**（Static Symbolic Execution, SSE）。它完全不靠具體輸入，從程式起點開始一路對所有控制流做符號分叉（像是不加引導的 `angr` 全路徑探索或 KLEE 預設模式）。這種做法概念最純粹，拿來對付獨立的小函式非常好用；但只要一撞上系統呼叫、外部 `.so` 函式庫或成千上萬條分支，狀態數量就會瞬間失控。

第二種是**動態符號執行／混合具體符號執行**（Dynamic / Concolic Execution, DSE）。它會先拿一顆**具體的種子輸入**（concrete seed），在真實環境或半模擬環境裡實實在在跑完一條路徑，同時在旁邊偷偷記下這條路上所有變數對應的符號算式與分支條件 `π = b_1 ∧ b_2 ∧ ... ∧ b_m`。跑完之後，挑出路途上某個還沒去過的岔路 `b_i`，把前面的條件保留、單獨把最後一步反轉成 `b_1 ∧ ... ∧ b_{i-1} ∧ ¬b_i`，送進 SMT 求解器算出能走進那條新岔路的輸入。

Concolic 最迷人的地方就是「只要具體程式跑得完，它就絕對不會因為看不懂外部函式庫而卡死」。萬一途中碰到太複雜的系統呼叫或沒辦法轉成符號的指令，它可以直接從當下的具體記憶體裡把真實數值讀出來（這叫具體化 concretization）繼續往下走。雖然具體化會犧牲掉該數值跟原始輸入之間的部分代數關聯，卻換來了極強的實戰存活率。現在主流的混合式 Fuzzer（像 QSYM、SymCC、SymQEMU）幾乎清一色都是走 Concolic 架構。

---

### SMT 求解器與 Z3 `BitVec`：為何不能用數學整數

收集好路徑條件 `π` 之後，負責把代數算式變回具體攻擊位元組的幕後功臣，就是 **SMT 求解器**（Satisfiability Modulo Theories Solver），而目前業界最常用的主力就是微軟開源的 **Z3**。

傳統的布林 SAT 求解器（如 MiniSat、CaDiCaL）靠 DPLL 與 CDCL（Conflict-Driven Clause Learning）演算法，只能解純布林變數組成的邏輯公式（CNF）。SMT 則是在 SAT 核心上面加掛了專門處理各種資料結構的理論求解器（Theory Solvers），像是無量化位元向量理論 `QF_BV`、陣列理論 `QF_ABV` 以及線性算術。

當你把一條 `BitVec` 方程式丟給 Z3 時，Z3 會先在字元層級做代數化簡（例如把 `x ^ x` 消成 `0` 或做常數摺疊），接著透過 **Bit-Blasting** 把每個 32 位元的加法器、乘法器跟位移電路打散成底層布林邏輯閘，最後交給 CDCL SAT 引擎算出每個 bit 該填 `0` 還是 `1`。

用 Z3 寫漏洞求解腳本時，新手最容易踩到的大地雷就是把 `z3.Int` 跟 `z3.BitVec` 搞混。

先看下面這兩行 Z3Py 寫法的天壤之別：

```python
# 錯誤示範：用數學無限精度整數 Int，永遠解不出 32 位元溢位回繞！
x_math = Int('x')      # x_math >= 0 且 x_math + 8 == 0 必為 UNSAT

# 正確示範：用固定 32 位元的 BitVec，精準重現 C 語言 uint32_t 模 2^32 回繞
x_bv = BitVec('x', 32) # 0xFFFF_FFF8 + 8 == 0 為 SAT！
```

`z3.Int` 代表的是**數學課本上的無限精度整數**（ℤ），在它的世界裡，`x >= 0` 而且 `x + 8 == 0` 永遠是無解（`UNSAT`），因為數學整數根本不會溢位回繞；而且 `Int` 也不支援 `&`、`^` 或位元旋轉這些二進位操作。

相反地，`z3.BitVec('x', 32)` 代表的就是**固定 32 位元的 CPU 暫存器或 C 語言的 `uint32_t` / `int32_t`**，所有加減乘法天生都在模 `2^32` 的環上運作。這讓它能一模一樣地重現第 25 章的整數回繞（`0xFFFF_FFF8 + 8 == 0` 馬上解出 `SAT`）。

還有一個千萬要小心的細節：在 Z3 裡面，直接寫 `<`、`<=`、`>`、`>=` 跟右移 `>>`，預設全部都是**有號（Signed）運算**！要表達 C 語言裡的無號比較，一定要明確呼叫 `ULT`、`ULE`、`UGT`、`UGE`；要表達無號邏輯右移，則要呼叫 `LShR(x, n)`。

要是把無號右移隨手寫成 `>>`，當最高位元（bit 31）是 `1` 的時候，右移左邊空出來的位元會全部補上 `1` 而不是 `0`，算出來的魔數跟校驗和就會完全歪掉。

#### 實戰端到端推導：純 Fuzzing 9.94 天 vs Z3 `BitVec` < 50 ms

我們直接拿 `libnexus-parse` 裡一條負責解析「特權結算補償封包」的深層分支來實算一遍（TLV 檔頭維持第 20 章基準：`magic: 2B`、`type: 2B`、`len: 4B` `uint32`，合法 payload 上限 `65,536 bytes`）。這條分支要求輸入至少 `20 bytes`（`8 bytes` 檔頭加上 `12 bytes` 負載），而且必須連闖四關才能走進底層的記憶體配置程式碼：

1. **檔頭魔數與型別**：`magic == 0x4E58`（高低位元組對應 ASCII `'N'` 與 `'X'`，小端序檔案前兩個 byte 為 `58 4e`）、`type == 0x0013`、`len == 12`。
2. **負載 `flags`（`uint32`）**：低 16 位元必須是 `0x0002`（開啟補償模式），高 16 位元必須是 `0x8001`（特權簽章旗標）。
3. **負載 `amount_delta`（`uint32`）**：高 16 位元必須是 `0x0001`，而且低 16 位元加上 `8` 之後必須回繞到小於 `4`（也就是 `((amount_delta + 8) & 0xFFFF) < 4`）。漏洞就出在後面直接拿這個截斷後的低 16 位元去呼叫 `malloc`，結果只配了 `1–3 bytes` 的小緩衝區，卻硬拷貝了 `8` 或 `16 bytes` 的固定標記資料進去。
4. **負載 `csum`（`uint32`）**：32 位元混合校驗和必須滿足 `csum == (((magic_type ^ rotl32(flags, 7)) + amount_delta * 0x9E3779B1) mod 2^32)`，其中 `magic_type = (magic << 16) | type`。

下面我們把純灰箱 Fuzzing 硬撞的時間成本，跟 Z3 `BitVec` 直接求解的過程擺在一起算個清楚：

```text
=== 1. 純灰箱 Fuzzing 暴力嘗試成本（假設 magic/type/len 已被字典或種子命中）===
目標空間：僅計算單一 32 位元校驗和等式 csum == expected(flags, amount_delta)
候選空間大小 N = 2^32 = 4,294,967,296（約 4.29 × 10^9）次
AFL++ 單核 Persistent Mode 基準吞吐率 R = 5,000 exec/s

- 無放回完整枚舉最壞嘗試次數：4,294,967,296 次（亦等於獨立有放回均勻隨機抽樣的期望嘗試次數 1/p = 2^32）
  耗時 = 4,294,967,296 / 5,000 = 858,993.46 秒
       = 858,993.46 / 86,400 ≈ 9.94 天（約 9.9 天）
- 無放回隨機排列 50% 累積命中門檻：2^31 = 2,147,483,648 次（含命中當次的期望次數為 (2^32 + 1)/2 = 2,147,483,648.5 次）
  耗時 = 2,147,483,648 / 5,000 = 429,496.73 秒
       = 429,496.73 / 86,400 ≈ 4.97 天
  （若為獨立有放回抽樣，累積命中率達 50% 則需 ln(2) × 2^32 ≈ 2.977 × 10^9 次，約 6.89 天）
（註：若在檔頭已通過的前提下，三個 32 位元負載欄位 flags、amount_delta、csum 皆採獨立均勻隨機抽樣，
  由於 flags 僅 1 解、amount_delta 僅 4 解（0x0001FFF8..0x0001FFFB）、csum 隨前兩者唯一決定，
  單次同時命中全部分支的聯合機率僅為 (1 × 4 × 1) / 2^96 = 2^-94 < 2^-80，單核盲猜實務上永遠無法突破。）

=== 2. Z3 BitVec 約束求解推導（單次求解 < 50 ms）===
設定 32 位元符號向量：
  magic_type   = (0x4E58 << 16) | 0x0013 = 0x4E580013
  flags        = BitVec("flags", 32)
  amount_delta = BitVec("amount_delta", 32)
  csum         = BitVec("csum", 32)

路徑條件 π：
  C1: (flags & 0xFFFF) == 0x0002
  C2: LShR(flags, 16) == 0x8001
  C3: (amount_delta & 0xFFFF0000) == 0x00010000
  C4: ULT((amount_delta + 8) & 0xFFFF, 4)        # 無號小於 4，鎖定低 16 位元回繞（合法低 16 位元為 0xFFF8..0xFFFB）
  C5: csum == (magic_type ^ ((flags << 7) | LShR(flags, 25))) + (amount_delta * 0x9E3779B1)

逐項代數求解與數值驗證（mod 2^32）：
  由 C1 ∧ C2 → flags = 0x80010002
  由 C3 ∧ C4 → 選取讓回繞後低 16 位元等於 1（對應最小正配置尺寸 1 byte）的候選解 0xFFF9
              （0xFFF9 + 8 = 0x10001 → & 0xFFFF = 1 < 4；其餘合法低 16 位元為 0xFFF8、0xFFFA、0xFFFB）
              amount_delta = 0x0001FFF9
  計算 rotl32(0x80010002, 7)：
    (0x80010002 << 7) & 0xFFFFFFFF = 0x00800100
    0x80010002 >> 25               = 0x00000040
    rotl32(0x80010002, 7)          = 0x00800140
  計算 magic_type ^ rotl32(flags, 7)：
    0x4E580013 ^ 0x00800140        = 0x4ED80153
  計算乘法項（mod 2^32）：
    0x0001FFF9 × 0x9E3779B1        = 0x00013C6A_9FDDAC29
    截斷低 32 位元                  = 0x9FDDAC29
  計算最終校驗和：
    csum = (0x4ED80153 + 0x9FDDAC29) mod 2^32 = 0xEEB5AD7C（十進位 4,004,883,836）

總結：Z3 在 32 位元位元向量理論（QF_BV）下透過字元級簡化與 bit-blasting，
從建立求解器到解出模型耗時 < 50 ms；相較於 9.94 天完整枚舉（或有放回抽樣期望時間），加速超過 1.7 × 10^7 倍。
```

這個數字對比把符號執行的定位講得一清二楚：它不是拿來取代 Fuzzer 高速變異的，而是用 `< 50 ms` 的代數計算，一舉炸開原本會困住 Fuzzer 整整十天的數學路障。

---

### 狀態爆炸（Path Explosion）與緩解策略

既然符號執行連 32 位元校驗和都能秒殺，那為什麼我們不乾脆用它把整個 `libnexus-parse` 或 Linux 核心從頭到尾掃一遍？因為會撞上符號執行最大的天敵：**狀態爆炸**（Path Explosion）。

想像一個解析迴圈，每讀進一個 byte 就做一次 `if/else` 判斷。只要路途上有 `k` 個彼此獨立的分支，路徑總數就會以指數 `O(2^k)` 暴增。才讀到第 `30` 個符號 byte，場上活著的狀態就已經飆到 `2^30 = 1,073,741,824` 個；而在 `libnexus-parse` 允許的 `65,536 bytes` 負載上限裡，隨便跑幾百圈迴圈，分裂出來的符號狀態樹就能把幾百 GiB 的伺服器記憶體吃得一乾二淨。

除了單純的 `if/else` 分叉，實戰中還有三個會讓狀態瞬間爆炸的放大器：

第一個是**符號指標與陣列索引**（Symbolic Memory Dereference）。當程式寫出 `table[sym_idx]` 時，引擎讀出來的不再是一個固定數值，而是一棵「如果 `sym_idx == 0` 就是 A、如果 `sym_idx == 1` 就是 B……」的龐大 `ITE`（If-Then-Else）條件樹；要是連寫入的目標位址都是符號化的（`*sym_ptr = val`），引擎甚至可能被迫替所有合法的記憶體分頁都分裂出一個平行狀態。

第二個是**一頭栽進外部函式與系統呼叫裡**。如果沒幫 `malloc`、`memcpy`、`strlen` 寫好精簡的符號摘要模型，符號執行器一腳踩進 glibc 的 `ptmalloc2`（第 23 章）或是用 SSE2/AVX2 向量指令寫的 `strlen` 迴圈裡，馬上就會在裡面檢查 `16-byte` 對齊跟 tcache bin 指標的幾十個分支中迷路。

第三個則是**密碼學單向雜湊函數**（Cryptographic One-Way Functions）。像 AES、SHA-256 或 HMAC，設計初衷就是要讓雪崩效應與代數複雜度最大化。如果你把完整 64 輪的 SHA-256 壓縮函式硬轉成 Z3 `BitVec` 公式叫它求逆像，就等於叫通用 CDCL SAT 求解器在幾十萬條死死咬在一起的布林子句裡硬解密碼學原像，只會讓 solver 卡死到天荒地老。

面對這些爆炸源，靠加記憶體是救不了的，實戰中我們靠的是下面五招工程控制策略：

| 爆炸來源 | 怎麼壓下來 | 底層機制與工程取捨 |
|---|---|---|
| 指數級分支累積 | **Concolic 單路徑反轉** | 先拿具體種子跑完 1 條主路徑，再挑沒去過的岔路反轉求解，讓記憶體消耗維持在線性的 `O(深度)` 而不是 `O(2^深度)`。 |
| 菱形分支重複探索 | **路徑合併（State Merging / Veritesting）** | 當 `if-else` 兩條路又匯合回同一個基本區塊時，把兩個狀態合而為一，變數值改用 SMT 的 `ITE(cond, v1, v2)` 表達；路徑變少了，但單次送給 Z3 的公式會變大。 |
| 外部函式庫內部迴圈 | **SimProcedures / 環境模型化** | 在 PLT/GOT 入口直接攔截 `strlen`、`memcpy`、`strcmp`、`malloc` 等常見函式，改用簡潔的符號前置／後置條件函式代替，絕不跳進 glibc 機器碼裡。 |
| 長度未知的符號迴圈 | **Loop Bounding 與目標導向探索** | 硬性限制單一迴圈最多只能展開幾次（例如 `64` 次），並配合靜態 CFG 最短距離優先挑離 Sink 最近的狀態跑，同時把錯誤返回區塊通通設進 `avoid`。 |
| 雜湊與 HMAC 驗簽 | **Harness 繞過與符號隔離** | 在內部分析或 Fuzzing Harness 裡先用編譯巨集把密碼學驗簽 stub 掉（留到上線前再單獨測驗簽模組），把寶貴的求解算力留給業務解析與線性校驗和。 |

---

### `angr` 架構與 ELF 二進位符號求解

當我們手邊沒有原始碼、只能面對一顆 stripped ELF 二進位檔（延續第 21 章的逆向場景）時，Python 生態系裡的 **`angr`**（到了 2026 年已推進到 v10 系列，需搭配 Python 3.12+）是最成熟的符號執行利器。不過要是把 `angr` 當成黑盒子無腦呼叫 `explore()`，十之八九會卡在記憶體耗盡或什麼都搜不到。要駕馭它，得先摸透它內部四層管線是怎麼接力運作的：

第一層是**二進位載入器 CLE**（CLE Loads Everything）。它負責讀進 ELF 檔頭、各個區段（`.text`、`.rodata`、`.got`）跟相依的 `.so`，在記憶體裡搭出模擬的虛擬位址空間。

這裡最容易踩的坑就是 **PIE（Position Independent Executable）基底位址**：用現代 `gcc` 預設編出來的 PIE 執行檔，在 Ghidra 或 `objdump` 看到的位址常從 `0x0` 或 `0x100000` 起跳，但 `angr` 載入 PIE 主程式時預設會掛在 **`0x400000`**。只要兩邊基底沒對齊，`find=` 的目標位址就永遠走不到。

第二層是**中介碼舉升引擎 PyVEX**。x86_64 有上千條指令，還有一堆隱含的狀態旗標（`ZF`/`CF`/`OF`）跟重疊暫存器（`al`/`ax`/`eax`/`rax`），直接對機器碼寫符號規則太容易出包。所以 `angr` 借用了 Valgrind 的 **VEX IR**，先把每個基本區塊（IRSB）翻譯成與硬體平台無關的 SSA（靜態單賦值）中介碼，把所有條件旗標怎麼算的都攤開來寫清楚，讓同一套求解核心能通吃 x86_64 與 ARM64。

第三層是**符號運算後端 Claripy**。`angr` 不會直接把 Z3 API 寫死在邏輯裡，而是透過 **Claripy** 這層薄皮來管理符號位元向量（`claripy.BVS("name", bits)`）、具體數值（`claripy.BVV(val, bits)`）與 AST 快取，等到真的需要判斷分支有沒有解的時候，才把累積的路徑條件 `state.solver.constraints` 轉交給底層的 Z3。

第四層則是**模擬管理器（`SimulationManager`）與 `SimProcedures`**。在預設設定下，`angr` 會把常見的 glibc 函式（像是 `printf`、`malloc`、`memcmp`、`read`）偷換成用 Python 寫好的 `SimProcedure` 摘要模型，免得引擎一頭栽進 `ptmalloc2` 裡面出不來。

而 `SimulationManager` 就像個調度總管，負責管理 `active`（還在跑的）、`found`（走到目標的）、`avoid`（踩進死路的）跟 `deadended`（走到終點的）這幾個狀態籃子（stash）。

看看下面這段針對 `libnexus-parse` 測試檔寫的最小化求解腳本，怎麼一次把 PIE 基底對齊、`20 bytes` 符號 `stdin` 與錯誤分支剪枝全部串起來：

```python
import angr
import claripy

# 明確對齊 PIE 基底位址，確保跟 objdump / Ghidra 看到的偏移量一致
BASE = 0x400000
proj = angr.Project("./nexus_tlv_sym", main_opts={"base_addr": BASE}, auto_load_libs=False)

# 用相對偏移加上基底算出執行期位址（假設漏洞點在 0x1380，提早報錯退出在 0x1290 與 0x12b5）
FIND_ADDR = BASE + 0x1380
AVOID_ADDRS = [BASE + 0x1290, BASE + 0x12b5]

# 建立 20 bytes（160 bits）的符號輸入，掛到程式的 stdin 上
pkt_bytes = [claripy.BVS(f"b_{i}", 8) for i in range(20)]
sym_stdin = claripy.Concat(*pkt_bytes)

# 打開 LAZY_SOLVES：延後到真正需要剪枝或抵達 find 時才呼叫 Z3，省下大量中途查詢開銷
state = proj.factory.entry_state(
    stdin=angr.SimFileStream(name="stdin", content=sym_stdin, has_end=True),
    add_options={angr.options.LAZY_SOLVES},
)

simgr = proj.factory.simulation_manager(state)
simgr.explore(find=FIND_ADDR, avoid=AVOID_ADDRS)

if simgr.found:
    hit = simgr.found[0]
    raw_pkt = hit.solver.eval(sym_stdin, cast_to=bytes)
    print(f"Found trigger ({len(raw_pkt)}B): {raw_pkt.hex(' ')}")
```

注意程式碼裡的 `LAZY_SOLVES` 選項。在分支很多的解析器裡，如果每遇到一個 `if` 就當場叫 Z3 檢查一次，光行程間通訊跟公式序列化的時間就飽了；打開 `LAZY_SOLVES` 後，引擎會先悶著頭把條件記下來，等到真的踩進目標點或遇到關鍵剪枝點時才一次算總帳，通常能讓搜尋速度翻上好幾倍。

---

### 混合式 Fuzzing：AFL++ 與符號／Concolic 引擎的雙向閉環

單獨跑 `angr` 的短板非常明顯：因為它是在 Python 直譯器裡一步步模擬 VEX IR，執行速度比原生機器碼慢了好幾個數量級，光走過幾十層巢狀解析可能就要花掉幾十分鐘。反過來，純灰箱 AFL++ 雖然有每秒 `5,000 exec/s` 的狂暴速度，卻又被 32 位元校驗和擋在門外。

**混合式 Fuzzing**（Hybrid Fuzzing，早年由 Driller 開創先河，現在實戰的主力則是 **AFL++ 搭配 QSYM、SymCC 或 SymQEMU**）就是把這兩個人湊成一對互補的搭檔，接成一個非同步的雙向迴圈：

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    AFL++ 灰箱變異節點（5,000 exec/s）                   │
│  - 維持 64 KiB 邊緣覆蓋率位圖，高速執行 bit-flip / havoc / splice 變異  │
│  - 產出新覆蓋邊緣的種子寫入：out/fuzzer01/queue/id:*                    │
└───────────────┬─────────────────────────────────────────▲───────────────┘
                │ (1) 監控新種子或覆蓋率停滯佇列          │ (4) Foreign Sync
                ▼                                         │     (-F sym_out)
┌─────────────────────────────────────────────────────────┴───────────────┐
│              Concolic / 符號求解節點（SymCC / SymQEMU / angr）          │
│  - 重放具體種子，沿途追蹤符號運算式與分支條件 π = b_1 ∧ ... ∧ b_m       │
│  - 鎖定「僅單側被覆蓋」的分支，送出 π_prefix ∧ ¬b_i 給 Z3 BitVec (<50ms)│
│  - 解出新通關輸入寫入：out/sym_sync/queue/id:000000,orig:sym            │
└─────────────────────────────────────────────────────────────────────────┘
```

#### 為何 SymCC 與 SymQEMU 成為混合式 Fuzzing 主力

在挑選混合式引擎時，看懂工具底層是怎麼插樁的，就能根據手上有沒有原始碼挑對武器：

如果你**有 C/C++ 原始碼**，首選是 **SymCC**。它完全拋棄了笨重的直譯器，直接做成一個 Clang/LLVM 的編譯期 Pass。當你用 `symcc` 編譯目標程式時，編譯器會在每一條算術跟比較指令旁邊，**直接嵌進建立符號算式的原生 C++ 函式呼叫**。跑一筆測試輸入時，目標程式是以接近原生機器碼的全速在跑，只針對真正沾到符號輸入的變數建立 AST，而且只在需要反轉未覆蓋分支的那一刻呼叫 Z3。

如果你**只有 stripped ELF 二進位檔**（就像第 21 章的閉源韌體或第三方 `.so`），那就換 **SymQEMU** 上場。它把符號追蹤做進了 QEMU 的 TCG（Tiny Code Generator）動態二進位轉譯層裡：當 QEMU 把目標基本區塊翻譯成宿主機機器碼時，順手塞入符號運算輔助指令，直接甩開了 `angr` 那層 Python 直譯器的速度包袱。

至於 **QSYM**，則是另一款專為混合式 Fuzzing 打造的快速二進位轉譯 Concolic 引擎。它的特色是敢於「不求完美」——當整條路徑累積的約束條件太龐大、害 Z3 解不出來時，它會主動丟掉前面不相關的舊約束，改用樂觀求解（Optimistic Solving）先猜出一組解再說，換取極高的種子產出速度。

把這些符號引擎接進 AFL++ 更是出奇地簡單。現代 AFL++ 原生支援用 `-F <foreign_sync_dir>` 參數去監看外部工具產出種子的資料夾（早期版本則是開多個 `-S` 次級目錄互相讀取）。只要符號引擎把算好 32 位元校驗和的新封包丟進 `sym_foreign/`，AFL++ 在幾秒鐘的同步週期內就會自動把它吸進自己的語料庫裡，接著馬上對校驗和後面的深層欄位展開每秒 `5,000 exec/s` 的猛烈突變。

---

## 故障模式與防禦

把符號執行跟混合式 Fuzzing 推上真實專案時，之所以會跑不出結果，通常不是因為數學公式無解，而是栽在下面這四種工程組態與防禦盲點上。

### 故障模式 1：符號記憶體與間接跳轉引發狀態癱瘓

當解析器裡出現 `handler_table[pkt->type]()`（函式指標表跳轉）或是 `malloc(pkt->len)`，而且傳進去的 `type` 跟 `len` 是完全沒限制範圍的符號變數時，`angr` 會為了涵蓋所有可能的值而試圖一口氣分裂出上萬個狀態，幾十秒內就會把記憶體撐爆並觸發作業系統的 OOM Kill。

要避免這種慘劇，在啟動搜尋前一定要先替輸入長度或關鍵欄位加上無號上界約束。比如照著 `libnexus-parse` 的規格，明確加上無號比較 `state.solver.add(claripy.ULE(sym_len, 65536))`（原生 Z3Py 的 `BitVec` 直接寫 `sym_len <= 65536` 會被當成有號比較 `SLE`，反而放進最高位元為 `1` 的超大無號長度，因此統一寫 `ULE` 最保險）。

同時記得善用 `SimProcedures` 限制配置器回傳的尺寸範圍，或是加上 `state.options.add(angr.options.CONCRETIZE)` 把非核心的陣列索引直接具體化。

### 故障模式 2：非線性運算與未設限迴圈讓 Z3 當場凍死

有時候腳本跑到 `simgr.explore()` 就整個停住不動了，一看 `top` 發現單核 CPU 100% 全卡在 Z3 的 `bit-blaster` 裡面。這種狀況最常發生在引擎一頭撞進展開了 `65,536` 次的 CRC32 查表迴圈、64 位元浮點數轉換，或是真正的密碼學驗簽函式。

對付這種卡死有兩條鐵律：第一，永遠要替求解器設下硬性的單次逾時上限（在 Z3 裡設 `solver.set("timeout", 2000)` 毫秒；在 `angr` 裡設 `state.solver._solver.timeout = 2000`）；第二，在混合 Fuzzing 的 Harness 裡，先用編譯期巨集把 HMAC 或 TLS 簽章驗證函式替換成永遠回傳通過的 stub，把 Z3 的寶貴算力全部留給後面的業務狀態機。

### 故障模式 3：PIE 基底沒對齊或 I/O 餵錯地方導致假性無解（Zero Found）

明明用肉眼看反編譯碼已經確定有一條能走到 Crash 的路，`angr` 跑完所有狀態後 `simgr.found` 卻還是空的。這通常出在三個低級失誤：
1. `find` 位址直接照抄 Ghidra 裡的相對偏移，忘了加上 `proj.loader.main_object.mapped_base`（也就是 `0x400000`）。
2. 目標程式明明是從命令列參數指定的檔案（`argv[1]`）或網路 socket `recv()` 讀封包，腳本卻把符號變數塞進 `stdin`。
3. 程式呼叫 `fread` 時要求的緩衝區比你宣告的符號輸入還大，結果提早撞上 EOF 走進錯誤處理分支。

遇到 `Zero Found` 時，最快的除錯動作是：先拿一顆**已知能通過前幾關檢查的具體合法輸入**餵進 `angr` 做單步追蹤，看著 `simgr.active[0].addr` 有沒有乖乖走進你預期的函式裡。等確定基底位址跟輸入管道完全對準之後，再換回符號變數開跑。

### 故障模式 4：防禦者迷思——以為靠「私有格式＋魔數＋自創校驗和」就能擋住駭客

很多後端或韌體團隊心裡常抱著一種僥倖：只要我們不公開內部二進位協定的規格書，在檔頭塞個 `0x4E58` 魔數、再自己發明一套左移右移加乘法的校驗和，外面的攻擊者就算逆向看不懂完整邏輯，也絕對湊不出合法封包打進深層程式碼。

這正是典型的「靠隱匿求安全」（Security by Obscurity）。看完這一章的實算你就知道，任何靠位元運算與固定多項式拼出來的校驗關卡，在反編譯器（第 21 章）加上 Z3 與 `angr` 面前，只是一層 `< 50 ms` 就會被捅破的窗戶紙。真正能守住跨信任邊界解析器的，只有三條硬性工程防線：
1. **把格式校驗跟記憶體配置徹底脫鉤**：就算封包通過了校驗和，後面每一個長度欄位在拿去配記憶體前，還是得老老實實檢查上限（`len <= 65_536`）並用 `checked_add` 防止整數溢位。
2. **核心解析器改用記憶體安全語言**：盡量用 Safe Rust 的切片來寫解析邏輯，避開第 25 章提過的 `unsafe` 裸指標陷阱。
3. **自己先跑混合式 Fuzzing**：把「AFL++ 搭配 SymCC/Z3」放進自家的夜間測試排程裡，在攻擊者動手之前先把躲在校驗和後面的崩潰挖出來修掉。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

這個實驗完全在本地 Linux 容器（或 Linux x86_64 虛擬機）裡進行，零雲端費用。我們要親手寫一支模擬 `libnexus-parse` 深層校驗分支的 C 程式 `nexus_tlv_sym.c`，先看看為什麼純 AFL++ 會被 32 位元校驗和死死擋在門外，接著分別用 **Z3 `BitVec`** 跟 **`angr`** 在幾十毫秒內算出 `20 bytes` 的通關輸入，最後再把這顆種子餵回給 AFL++，親眼見證覆蓋率瞬間跳升並抓出深層 Crash。

### 操作步驟

1. **準備本地環境**：在裝有 `gcc`、`clang` 與 Python 3.12+ 的 Linux 環境裡裝好求解套件：
   ```bash
   pip install z3-solver angr
   # 如果要做最後一步的混合回灌，請確認環境裡也有 afl-clang-fast 與 afl-fuzz（AFL++ 4.x）
   ```
2. **撰寫並編譯測試目標 `nexus_tlv_sym.c`**：
   這支程式有兩道關卡：第一關先檢查 `8 bytes` 的 TLV 檔頭（`magic == 0x4E58`、`type == 0x0013`、`len == 12`）；第二關接著檢查 `flags`、`amount_delta` 的低 16 位元回繞條件，還有 32 位元混合校驗和 `csum`。一旦全部過關，程式就會在 `trigger_overflow()` 裡面因為把截斷後的低 16 位元拿去配記憶體，當場觸發堆積越界寫入。
   - 先用 `clang -O1 -g -fsanitize=address nexus_tlv_sym.c -o nexus_tlv_sym_asan` 編出單獨驗證崩潰用的 ASan 版，再用 `afl-clang-fast -O1 -g -fsanitize=address nexus_tlv_sym.c -o nexus_tlv_sym_afl` 編出給 AFL++ 跑的插樁版。
   - 接著用 `gcc -O1 -no-pie -o nexus_tlv_sym_bin nexus_tlv_sym.c` 編出一顆不帶 ASan 的乾淨 ELF 執行檔給 `angr` 分析（實戰小撇步：跑符號執行時一定要避開 ASan 插樁，否則引擎光去追蹤 ASan 那堆影子記憶體檢查指令就累死了；永遠拿乾淨的二進位檔來求解，解出輸入後再丟給 ASan 執行檔去抓崩潰）。
3. **步驟 A — 寫 `solve_tlv_z3.py` 直接求解**：用 `z3.BitVec` 把前面「機制與推導」算過的那五條約束條件寫進去，把解出來的 `20 bytes` 封包存成 `z3_seed.bin`，然後執行 `./nexus_tlv_sym_asan < z3_seed.bin` 看 ASan 報錯。
4. **步驟 B — 寫 `solve_tlv_angr.py` 從二進位反解**：假設你手上根本沒有 `csum` 計算公式的原始碼，只能用 `nm` 或 `objdump -d nexus_tlv_sym_bin` 查出崩潰函式 `trigger_overflow` 的位址，請寫腳本叫 `angr` 直接從 ELF 機器碼自動搜出這 `20 bytes` 並存成 `angr_seed.bin`。
5. **步驟 C — 回灌 AFL++ 完成混合閉環**：
   - 先放一顆只有檔頭 `magic` 對、後面全填 `0` 的普通種子，啟動 `afl-fuzz` 並掛上 `-F sym_foreign` 外部同步目錄，觀察它的路徑數是不是完全卡死。
   - 把剛剛算出來的 `angr_seed.bin` 複製進外部同步目錄並改名為 `sym_foreign/id:000000,orig:angr`，看看 `afl-fuzz` 面板上的 `saved_crashes` 與覆蓋率怎麼瞬間突破。

### 外部靶場對照檢查點（pwn.college）

跑通本地實驗後，可以到 **pwn.college — Program Security / Reverse Engineering** 挑幾題 Symbolic Execution 相關的挑戰練手。在打靶場時，重點盯緊三件事：`claripy.BVS` 宣告的符號長度有沒有跟程式讀取的長度對齊、PIE 執行檔的基底偏移有沒有加對，以及有沒有把提早失敗的 `puts("Wrong!")` 分支塞進 `avoid` 清單裡幫引擎省力氣。

---

### 參考解答

#### 1. 目標原始碼 `nexus_tlv_sym.c`

```c
// nexus_tlv_sym.c
// 編譯 ASan 版：clang -O1 -g -fsanitize=address nexus_tlv_sym.c -o nexus_tlv_sym_asan
// 編譯 AFL++ 版：afl-clang-fast -O1 -g -fsanitize=address nexus_tlv_sym.c -o nexus_tlv_sym_afl
// 編譯純 ELF（供 angr）：gcc -O1 -no-pie nexus_tlv_sym.c -o nexus_tlv_sym_bin
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef struct __attribute__((packed)) {
    uint16_t magic;
    uint16_t type;
    uint32_t len;
} tlv_hdr_t;

typedef struct __attribute__((packed)) {
    uint32_t flags;
    uint32_t amount_delta;
    uint32_t csum;
} settle_body_t;

static inline uint32_t rotl32(uint32_t x, unsigned int r) {
    return (x << r) | (x >> (32 - r));
}

__attribute__((noinline))
void trigger_overflow(uint32_t amount_delta, const uint8_t *extra, size_t extra_len) {
    // 漏洞點：拿低 16 位元 + 8 截斷後的值當配置大小，結果只配了極小空間卻硬塞固定長度的標記資料
    uint16_t alloc_sz = (uint16_t)((amount_delta + 8U) & 0xFFFFU);
    if (alloc_sz == 0) alloc_sz = 1;
    char *buf = (char *)malloc(alloc_sz);
    if (!buf) return;

    // 當 alloc_sz < 4（例如 0x0001FFF9 + 8 回繞後低 16 位元為 1），下面的 memcpy 當場寫爆堆積！
    uint8_t marker[16] = {0x4E, 0x58, 0x50, 0x32, 0x41, 0x42, 0x43, 0x44,
                          0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C};
    if (extra_len > 0 && extra[0] == 0xAA) {
        // 留給 AFL++ 在跨過校驗和之後繼續變異解鎖的次級深層分支
        memcpy(buf, marker, sizeof(marker));
    } else {
        memcpy(buf, marker, 8);
    }
    free(buf);
}

int main(void) {
    uint8_t raw[64];
    ssize_t n = read(STDIN_FILENO, raw, sizeof(raw));
    if (n < (ssize_t)(sizeof(tlv_hdr_t) + sizeof(settle_body_t))) {
        return 1;
    }

    tlv_hdr_t hdr;
    memcpy(&hdr, raw, sizeof(hdr));
    if (hdr.magic != 0x4E58 || hdr.type != 0x0013 || hdr.len != 12) {
        return 2;
    }

    settle_body_t body;
    memcpy(&body, raw + sizeof(hdr), sizeof(body));

    if ((body.flags & 0xFFFFU) != 0x0002U) return 3;
    if ((body.flags >> 16) != 0x8001U) return 4;
    if ((body.amount_delta & 0xFFFF0000U) != 0x00010000U) return 5;
    if (((body.amount_delta + 8U) & 0xFFFFU) >= 4U) return 6;

    uint32_t magic_type = ((uint32_t)hdr.magic << 16) | (uint32_t)hdr.type;
    uint32_t expected = (magic_type ^ rotl32(body.flags, 7)) + (body.amount_delta * 0x9E3779B1U);
    if (body.csum != expected) {
        return 7;
    }

    size_t tail = (size_t)n - (sizeof(hdr) + sizeof(body));
    trigger_overflow(body.amount_delta, raw + sizeof(hdr) + sizeof(body), tail);
    return 0;
}
```

#### 2. Z3 `BitVec` 求解腳本 `solve_tlv_z3.py`

```python
# solve_tlv_z3.py
import struct
import time
from z3 import BitVec, LShR, Solver, ULT, sat

t0 = time.perf_counter()
s = Solver()

flags = BitVec("flags", 32)
amount_delta = BitVec("amount_delta", 32)
csum = BitVec("csum", 32)

magic = 0x4E58
ptype = 0x0013
plen = 12
magic_type = (magic << 16) | ptype  # 0x4E580013

s.add((flags & 0xFFFF) == 0x0002)
s.add(LShR(flags, 16) == 0x8001)
s.add((amount_delta & 0xFFFF0000) == 0x00010000)
s.add(ULT((amount_delta + 8) & 0xFFFF, 4))
# 鎖定回繞後的低 16 位元剛好等於 1（對應 alloc_sz = 1 byte，唯一解為 0x0001FFF9）
s.add(((amount_delta + 8) & 0xFFFF) == 1)

rotl_flags = (flags << 7) | LShR(flags, 25)
expected = (magic_type ^ rotl_flags) + (amount_delta * 0x9E3779B1)
s.add(csum == expected)

assert s.check() == sat
m = s.model()
elapsed_ms = (time.perf_counter() - t0) * 1000

f_val = m[flags].as_long()
a_val = m[amount_delta].as_long()
c_val = m[csum].as_long()

pkt = struct.pack("<HHIIII", magic, ptype, plen, f_val, a_val, c_val)
with open("z3_seed.bin", "wb") as fp:
    fp.write(pkt)

print(f"Solved in {elapsed_ms:.2f} ms")
print(f"flags={f_val:#010x} amount_delta={a_val:#010x} csum={c_val:#010x}")
print(f"packet ({len(pkt)}B): {pkt.hex(' ')}")
```

跑完這支腳本，畫面會在幾十毫秒內印出 `flags=0x80010002`、`amount_delta=0x0001fff9`、`csum=0xeeb5ad7c`，產出的 `20 bytes` 封包內容是 `58 4e 13 00 0c 00 00 00 02 00 01 80 f9 ff 01 00 7c ad b5 ee`。把它餵進 `./nexus_tlv_sym_asan < z3_seed.bin`，ASan 馬上就會抓到 `AddressSanitizer: heap-buffer-overflow`（往大小只有 `1 byte` 的堆積區塊寫入了 `8 bytes`）。

#### 3. `angr` 無原始碼二進位求解腳本 `solve_tlv_angr.py`

接著試試不看算式，直接讓 `angr` 自己從 `nexus_tlv_sym_bin` 找路走到 `trigger_overflow`：

```python
# solve_tlv_angr.py
import angr
import claripy

proj = angr.Project("./nexus_tlv_sym_bin", auto_load_libs=False)

# 從符號表查出目標函式位址（如果是 stripped binary，就改填反組譯看到的位址）
target_sym = proj.loader.find_symbol("trigger_overflow")
FIND_ADDR = target_sym.rebased_addr

# 宣告 20 bytes 的符號輸入並掛到 stdin
sym_bytes = [claripy.BVS(f"b_{i}", 8) for i in range(20)]
sym_stdin = claripy.Concat(*sym_bytes)

state = proj.factory.entry_state(
    stdin=angr.SimFileStream(name="stdin", content=sym_stdin, has_end=True),
    add_options={angr.options.LAZY_SOLVES},
)

simgr = proj.factory.simulation_manager(state)
# 想再提速的話，可以把 main 裡面 return 2..7 的位址放進 avoid=[...]
simgr.explore(find=FIND_ADDR)

if simgr.found:
    hit = simgr.found[0]
    solved = hit.solver.eval(sym_stdin, cast_to=bytes)
    with open("angr_seed.bin", "wb") as fp:
        fp.write(solved)
    print(f"angr solved ({len(solved)}B): {solved.hex(' ')}")
else:
    print("No path found; check stdin length or PIE base alignment.")
```

#### 4. 回灌 AFL++ 與覆蓋率躍升驗證

```bash
# 1. 準備一顆只對齊檔頭、後面全填 0 的普通起始種子，以及外部同步資料夾
mkdir -p in_seeds out_afl sym_foreign
python3 -c 'open("in_seeds/init.bin", "wb").write(b"\x58\x4e\x13\x00\x0c\x00\x00\x00" + b"\x00" * 12)'

# 2. 啟動 AFL++ 並用 -F 掛載外部符號引擎的輸出資料夾
afl-fuzz -i in_seeds -o out_afl -F sym_foreign -- ./nexus_tlv_sym_afl

# 3. 開另一個終端機，把剛剛解出來的通關種子照 AFL++ 佇列命名規則丟進 sym_foreign：
cp angr_seed.bin sym_foreign/id:000000,orig:angr
```

把 `id:000000,orig:angr` 丟進去之後，盯著 `out_afl/default/fuzzer_stats` 或面板看：幾秒鐘內 AFL++ 就會把這顆種子吸進去，當場衝進 `trigger_overflow` 撞出第一顆 Crash（`saved_crashes >= 1`），而且緊接著就會對第 `20` 個 byte 之後的尾端資料展開高速變異，一下子就翻出 `extra[0] == 0xAA` 那條寫入 `16 bytes` 的次級路徑！

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別看下面的參考解答，試著動筆推算下面 4 道題目：

1. **Z3 `BitVec` 的有號右移陷阱與十六進位反推**：在 Z3Py 裡宣告一個 32 位元符號變數 `v = BitVec('v', 32)`，我們希望它同時滿足兩個無號整數條件：高 16 位元右移後等於 `0xCAFE`（也就是 `(v >> 16) == 0xCAFE`），而且低 16 位元加上 `0x20` 之後在 16 位元內剛好回繞成 `0x0008`（也就是 `((v & 0xFFFF) + 0x20) & 0xFFFF == 0x0008`）。
   (a) 為什麼在 Python 裡直接寫 `s.add((v >> 16) == 0xCAFE)`，Z3 會直接回你 `unsat`？應該改成哪個函式才對？
   (b) 修正之後，滿足這兩條約束的唯一 32 位元十六進位數值 `v` 是多少？
2. **兩道獨立 32 位元關卡的盲猜成本**：假設某個二進位封包通過檔頭檢查後，後面連續擋著兩道彼此獨立的 32 位元精確檢查：第一關先比對 `token == 0x1337_C0DE`，過關後第二關再比對 `crc32(body) == pkt_crc`。如果 AFL++ 以基準速度 `5,000 exec/s` 單核盲猜（沒開字典也沒開 CMPLOG），光靠無放回枚舉撞破第一關跟第二關，各自的最壞時間是多少天？為什麼這種串聯關卡會讓純變異 Fuzzer 徹底絕望，對 Z3 來說卻只是把兩條等式放在一起解？
3. **迴圈分叉的狀態爆炸實算**：有一段解析子網路遮罩的迴圈，會固定讀取 `24 bytes` 的符號緩衝區 `buf`，每一圈都檢查 `if (buf[i] == '.')` 並分叉出兩條路（假設中途都不會提前 return）。請問純靜態符號執行（SSE）跑完這 24 圈之後，最多會分裂出多少個葉節點狀態？如果改用 **State Merging**（路徑合併）跟 **Concolic Execution**，它們各自是用什麼代價把這個天文數字壓下來的？
4. **混合式 Fuzzing 的分工與語料庫塞車**：既然 SymCC / `angr` 這麼會解條件，為什麼當它解開校驗和之後，我們不讓符號引擎乾脆一路把後面的程式碼全部跑完，而是要把種子丟回給 AFL++？反過來說，如果外部符號節點沒做過濾，每秒鐘把上百顆「其實都只走過同一條淺層路徑」的種子狂塞進 AFL++ 的 `-F` 同步資料夾，會把 AFL++ 害成什麼樣子？

---

### 參考解答

1. **Z3 `BitVec` 右移陷阱與數值反推**：
   - **(a)** 在 Z3Py 裡面，`BitVec` 的 `>>` 運算子預設做的是**算術右移（Arithmetic Shift Right, `AShr`）**。因為目標值 `0xCAFE` 的最高位元（對應 32 位元下的 bit 31）是 `1`，算術右移 16 位時，左邊空出來的 16 個 bit 會全部被補上 `1`，算出來變成 `0xFFFFCAFE`，跟無號常數 `0x0000CAFE` 永遠不可能相等，所以必定回傳 `unsat`。正確寫法是改用無號邏輯右移 **`LShR(v, 16) == 0xCAFE`**。
   - **(b)** 先算低 16 位元：由 `(low + 0x20) ≡ 0x0008 (mod 65,536)`，可以反推 `low = (0x0008 - 0x0020) mod 65,536 = 65,536 - 24 = 65,512 = 0xFFE8`。再把高 16 位元的 `0xCAFE` 拼上去，唯一解就是 **`0xCAFE_FFE8`**（驗算：`0xFFE8 + 0x20 = 0x10008`，取低 16 位元 `& 0xFFFF` 剛好是 `0x0008`）。
2. **串聯 32 位元關卡的定量對比**：
   - **盲猜耗時**：單一 32 位元精確等式有 `2^32 = 4,294,967,296` 種可能，在 `5,000 exec/s` 下無放回枚舉的最壞時間是 `4,294,967,296 / 5,000 = 858,993.46 秒 ≈ 9.94 天`（50% 命中門檻也要 `4.97 天`）。Fuzzer 必須先花將近 10 天撞破第一關 `token`（讓位圖亮起新邊緣、把種子存進佇列），才能開始撞第二關 `crc32`，兩關串起來最壞得花掉約 **`19.88 天`**——而且這還建立在「Fuzzer 在變異後面 `body` 時，剛好都沒動到前面已經猜對的 `token`」的理想前提下；要是 `havoc` 變異同時把兩邊一起打亂，聯合機率會掉到 `2^-64`，幾百萬年都猜不中。
   - **為什麼 Z3 不怕**：AFL++ 的 `64 KiB` 位圖只看得到「分支過了沒」，在過關之前不會給任何「還差幾個 bit」的提示；而 Z3 是把兩條等式同時塞進路徑條件 `π` 裡做位元向量聯立求解，一次查詢就能同時算出兩邊的答案。
3. **24 圈迴圈的狀態數與緩解取捨**：
   - **狀態總數**：24 次獨立的二元分叉，若不剪枝最多會長出 **`2^24 = 16,777,216`（約 `1,678 萬`）個路徑狀態**，光狀態物件本身就足以塞爆一般機器的記憶體。
   - **兩種緩解策略的代價交換**：
     - **State Merging（路徑合併）**：把原本分散在 `1,678 萬` 個平行狀態的記憶體開銷，壓進**單一狀態裡超肥大的 SMT `ITE`（If-Then-Else）條件樹**；雖然記憶體不爆了，但最後丟給 Z3 的那條巨型公式還是可能讓求解器算到逾時。
     - **Concolic Execution（動態具體符號執行）**：放棄一次把整棵狀態樹養在記憶體裡，每次跟著一顆具體種子只跑一條路，沿途只記下線性的 `k = 24` 個分支條件（空間複雜度瞬間降回 `O(k)`），事後再挑單一分支反轉求解；代價是它能走多遠要看初始種子與 Fuzzer 搭檔給不給力，沒辦法像純靜態符號執行那樣一次把所有數學可達的路徑全摸遍。
4. **混合式架構的分工與語料庫衛生**：
   - **為什麼過關後要交還給 AFL++**：一旦跨過那道卡死人的校驗和，後面的解析程式碼通常有成百上千條簡單的長度分支、迴圈跟記憶體拷貝。符號引擎每走一步都要做 IR 轉譯跟建立 AST，速度比 AFL++ 的 `5,000 exec/s` 慢了好幾個數量級；把通關種子交還給 AFL++，才能用極低的單次執行成本把後面的淺層越界與空指標瞬間掃光。
   - **狂塞重複種子的下場**：如果外部符號節點不先做覆蓋率去重，每秒把上百顆沒有點亮任何新邊緣的廢種子塞進同步目錄，AFL++ 的佇列排程器（Queue Scheduler）與能量分配（Power Schedule）就會被這堆冗餘種子塞爆，把大量寶貴的變異時間浪費在重跑一模一樣的路徑上。所以符號節點在把種子寫進 `-F` 目錄前，一定要先確認它真的踩到了新邊緣，並定期用 `afl-cmin` 幫語料庫減肥。

---

## 延伸閱讀

1. **Z3 Theorem Prover 與 Z3Py 官方指南**：涵蓋 `BitVec`、`LShR`、`ULT` 與位元向量理論 `QF_BV` 的完整語法與調校選項（https://microsoft.github.io/z3guide/ 與 https://github.com/Z3Prover/z3）。
2. **angr 官方技術文件（CLE / PyVEX / Claripy / SimulationManager）**：拆解二進位載入重定位、VEX IR 舉升、SimProcedures 撰寫與記憶體模型選項（https://docs.angr.io/）。
3. **SymCC 與 SymQEMU 專案論文與原始碼（EURECOM S3）**：深入理解編譯期 LLVM Pass 插入符號運算（USENIX Security 2020）與 QEMU TCG 動態二進位符號轉譯（NDSS 2021）如何突破傳統直譯式引擎瓶頸（https://github.com/eurecom-s3/symcc 與 https://github.com/eurecom-s3/symqemu）。
4. **QSYM（USENIX Security 2018）**：專為混合式 Fuzzing 設計的 Concolic 引擎論文與實作，重點閱讀其「樂觀約束鬆弛（Optimistic Solving）」與指令級剪枝設計（https://github.com/sslab-gatech/qsym）。
5. **AFL++ 進階整合文件（Foreign Sync 與 CMPLOG）**：對照學習純灰箱比較值追蹤（CMPLOG/Redqueen）的適用邊界，以及如何透過 `-F` 參數與外部 Concolic 求解器協作（https://aflplus.plus/docs/fuzzing_in_depth/）。
