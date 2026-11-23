# 第 22 章：堆疊幀完整性與控制流保護（CFI）

第 20 章我們看過，作業系統靠分頁表實施了嚴格的 W^X（Write XOR Execute）原則：放機器碼的 `.text` 段標為唯讀可執行（`R-X`），放資料的堆疊與堆積標為可讀寫不可執行（`RW-`，基準分頁大小為 `4 KiB`）。在 **NexusPay** 的架構裡，Node.js API 閘道透過 N-API 呼叫 C 語言寫的原生模組 `libnexus-parse`，處理固定 `8 bytes` 檔頭（`magic: 2B`、`type: 2B`、`len: 4B` 無號 `uint32`）、合法負載上限 `65,536 bytes`（`64 KiB`）的 TLV 封包。

這道防線最致命的軟肋在於：分頁表雖然把程式碼頁跟資料頁分開了，卻**分不清同一張可寫堆疊頁裡面的資料到底誰是誰**。在同一個函式堆疊幀（Stack Frame）裡，用來裝封包內容的區域緩衝區、保護堆疊的 Stack Canary、呼叫端的框架指標（`Saved RBP`），以及決定函式跑完要跳回哪裡的回傳位址（`Saved RIP`），全都肩並肩擠在一起。本章不寫武器化攻擊載荷，而是站在底層架構與防禦工程的視角，把 x86_64 堆疊幀的位元組距離算清楚，並逐一拆解現代編譯器與 CPU 硬體（`_FORTIFY_SOURCE=3`、Stack Canary、Intel CET Shadow Stack、ARM PAC 與 LLVM CFI）怎麼聯手守住控制流完整性。

---

## 從你已知的出發

為什麼已經開啟了 NX（No-Execute），讓 CPU 絕對不准執行寫在堆疊上的任何一個位元組，C 語言函式裡的堆疊緩衝區溢位還是能讓程式去執行非預期的危險動作？

因為攻擊者根本不需要自己寫新指令進去——只要能改寫堆疊上的回傳位址（`Saved RIP`）或函式指標，當 CPU 執行 `ret` 或間接呼叫時，就會被騙去跳往「記憶體裡原本就具有 `R-X` 可執行權限的現成合法程式碼」（例如跳進 `libc.so.6` 現成的函式或指令片段裡）。在高階語言（TypeScript、Go、Rust）裡，陣列越界頂多拿到 `undefined` 或觸發受控的 panic，絕不會讓你碰到呼叫端的回傳位址；但在 C/C++ 的堆疊頁上，「業務資料」跟「控制流回傳位址」完全混居在同一塊可寫記憶體裡。要擋住這種「借用既有合法指令」的控制流劫持，光靠 NX 不夠，必須在編譯器與硬體層級導入**控制流完整性**（Control-Flow Integrity, CFI）。

---

## 機制與推導

### 攻擊者目標與實質影響

當 `libnexus-parse` 這類原生模組出現堆疊越界寫入或格式字串漏洞時，整個系統面臨的實質威脅可以分成三個層次：

第一是**控制流劫持**（Control-Flow Hijacking）。一旦堆疊上的 `Saved RIP` 或函式指標被覆寫，CPU 在執行 `ret` 或間接跳轉（`call rax`）時，就會脫離編譯期原本排好的控制流圖（Control-Flow Graph, CFG）。因為 `.node` 原生模組跟 Node.js 主程式共用同一個虛擬位址空間與作業系統權限，控制流只要一被拐走，輕則當場崩潰，重則在該 Worker 的權限下執行非預期的系統呼叫。

第二是**偷看堆疊上的隨機化指標與金絲雀**（Information Disclosure）。在 Linux x86_64 環境下，ASLR 為使用者空間 `mmap` 與動態庫提供了 `28 bits` 的隨機化熵值（分頁大小 `4 KiB = 4,096 bytes`，頁內低 `12 bits` 偏移固定）。如果函式有越界讀取或格式字串漏洞，攻擊者不用動手改記憶體，光把堆疊上殘留的 `Saved RIP` 與 `8-byte` Stack Canary 印出來看，就能一舉算出模組基底位址並得知當下的金絲雀密鑰。

第三是**拖垮服務可用性與交易中斷**（Denial of Service）。這一點後端架構師特別容易忽略：就算我們開滿了 Stack Canary 或 Intel CET 硬體保護，成功在 `ret` 的那一瞬間攔下了被竄改的回傳位址，防護機制的攔截手段也是呼叫 `__stack_chk_fail()`（送出 `SIGABRT`）或觸發硬體 `#CP` 例外（在 Linux 使用者態轉為 `SIGSEGV`），**當場殺掉整個 API Gateway Worker 行程**！在一個高併發的 Node.js 閘道裡，只要單一 Worker 行程被炸死，同一個行程上正在處理的其他幾十筆商戶結帳連線也會跟著無預警斷線。所以硬體跟編譯器緩解只是最後一道安全氣囊，真正的根治永遠是在入口處把邊界檢查鎖死。

---

### x86_64 堆疊幀佈局與 16-byte 對齊不變量

在 Linux x86_64（System V AMD64 ABI）裡，堆疊是由**高位址往低位址長**的。當外層函式執行 `call parse_fast_tlv` 時，CPU 硬體會先做兩件事：把 `RSP` 減去 `8 bytes`，將下一行指令的位址（`8 bytes` 的 `Saved RIP`）壓進堆疊，然後才把 `RIP` 跳到 `parse_fast_tlv` 的第一行。

進到被呼叫的子函式後，標準的函式序言（Prologue）會接著執行三步動作：
1. `push rbp`：把呼叫端的框架基底指標 `Saved RBP`（`8 bytes`）壓進堆疊（`RSP` 再減 `8`）。
2. `mov rbp, rsp`：把現在的 `RSP` 記在 `RBP` 裡，當作這個函式自己的基準座標。
3. `sub rsp, N`：把 `RSP` 往下拉 `N bytes`，騰出空間給區域變數、緩衝區跟對齊填充使用。

還記得第 20 章強調過的 **System V ABI `16-byte` 堆疊對齊不變量**嗎？**在執行任何一條 `call` 指令的前一瞬間，`RSP` 都必須是 `16` 的倍數（`RSP % 16 == 0`）**，否則進到 `printf` 或 `snprintf` 這類會用到 `movaps`（要求 16-byte 對齊的 SSE 向量指令）的函式時，CPU 當場就會拋出 `#GP` 例外崩潰。

我們把 `call` 跟 `push rbp` 對 `RSP` 餘數的影響擺在一起看，你就會明白為什麼編譯器配空間時總是湊成 `16` 的倍數：
- 呼叫端執行 `call` **之前**：`RSP % 16 == 0`。
- `call` 壓入 `8-byte` `Saved RIP` **之後**（剛踏進子函式第一行）：`RSP % 16 == 8`。
- 子函式執行 `push rbp` 壓入 `8-byte` `Saved RBP` **之後**：`RSP` 減了兩次 `8`，又重新回到了 **`RSP % 16 == 0`**（這時執行 `mov rbp, rsp`，所以 `RBP` 本身也是一個對齊 `16` 的倍數的位址）。
- 接下來，子函式執行 `sub rsp, N` 騰出區域變數空間時，只要讓 `N` 也是 `16` 的倍數（例如 `0x50 = 80 bytes`），就能保證將來在這個函式裡繼續 `call` 下游子函式時，`RSP` 依然穩穩對齊在 `16` 的倍數上！

---

### Worked Example：實算 `buf[64]` 到 `Saved RIP` 的位元組距離與 Shadow Stack 比對

我們直接拿 `libnexus-parse` 的快速路徑函式 `parse_fast_tlv()` 來做一次精確的位址推演。假設這個函式在堆疊上宣告了一個 `64 bytes` 的快速緩衝區 `uint8_t buf[64]`，而且編譯時開啟了 `-fstack-protector-strong`。

假設呼叫端在執行 `call parse_fast_tlv` 前，`RSP` 正好停在 `0x7fffffffdd00`（末兩碼 `00`，完全對齊 `16` 的倍數）。進到函式跑完 `push rbp; mov rbp, rsp; sub rsp, 0x50`（配置 `80 bytes` 局部空間）並填入 Stack Canary 之後，這塊堆疊幀從低位址到高位址的真實排列如下：

```text
=== Worked Example: parse_fast_tlv() 堆疊幀位元組佈局與硬體 Shadow Stack 攔截推導 ===

[已知條件]
- 呼叫前 RSP = 0x7fffffffdd00 (滿足 0x7fffffffdd00 % 16 == 0)
- call 壓入 Saved RIP 後 RSP = 0x7fffffffdcf8 (RSP % 16 == 8)
- push rbp; mov rbp, rsp 後 RBP = RSP = 0x7fffffffdcf0 (重新滿足 % 16 == 0)
- sub rsp, 0x50 (80 bytes) 後 RSP = 0x7fffffffdca0 (維持 % 16 == 0)

位址區間 (低 -> 高)          相對於 RBP 偏移     大小       槽位內容
------------------------------------------------------------------------------------
0x7fffffffdca0 - dca7       [rbp - 0x50]        8 bytes    對齊填充 / 區域長度變數
0x7fffffffdca8 - dce7       [rbp - 0x48]       64 bytes    buf[0..63] (資料寫入起點)
0x7fffffffdce8 - dcef       [rbp - 0x08]        8 bytes    Stack Canary (0x9a3f71c4028b5e00)
0x7fffffffdcf0 - dcf7       [rbp + 0x00]        8 bytes    Saved RBP (0x7fffffffdd40)
0x7fffffffdcf8 - dcff       [rbp + 0x08]        8 bytes    Saved RIP (0x5555555552a4)
------------------------------------------------------------------------------------

[算術距離與對齊驗算]
1. buf[0] 起始位址       = RBP - 0x48 = 0x7fffffffdcf0 - 0x48 = 0x7fffffffdca8
2. Stack Canary 起始位址 = RBP - 0x08 = 0x7fffffffdcf0 - 0x08 = 0x7fffffffdce8
   -> 從 buf[0] 到 Canary 的距離 = 0x7fffffffdce8 - 0x7fffffffdca8 = 0x40 (64 bytes)
3. Saved RIP 起始位址    = RBP + 0x08 = 0x7fffffffdcf0 + 0x08 = 0x7fffffffdcf8
   -> 從 buf[0] 到 Saved RIP 的總距離 = 64B (buf) + 8B (Canary) + 8B (Saved RBP)
                                      = 80 bytes (0x50)
   -> 位址相減驗算：0x7fffffffdcf8 - 0x7fffffffdca8 = 0x50 (80 bytes，完全吻合)
4. 整個堆疊幀總長度檢查  = 80B (sub rsp) + 8B (Saved RBP) + 8B (Saved RIP)
                         = 96 bytes (0x60 = 16 × 6，維持 16-byte 對齊不變量)

[越界寫入發生時的兩層攔截狀態]
假設程式漏檢查 hdr->len <= 64，讓一筆 len = 88 bytes 的 payload 順著 memcpy 寫入 buf[0]：
- 寫入第 1..64 bytes   (0x7fffffffdca8..dce7)：填滿合法的 buf[0..63]。
- 寫入第 65..72 bytes  (0x7fffffffdce8..dcef)：直接覆寫掉 8-byte Stack Canary！
- 寫入第 73..80 bytes  (0x7fffffffdcf0..dcf7)：覆寫掉 8-byte Saved RBP。
- 寫入第 81..88 bytes  (0x7fffffffdcf8..dcff)：剛好把 8-byte Saved RIP 完整改寫！

攔截關卡 A (軟體層 Stack Canary)：
  函式執行 ret 前，比對 [rbp - 0x08] 與 TLS 的 fs:0x28；發現第 65..72 bytes 已被改動，
  立即跳往 __stack_chk_fail() 送出 SIGABRT 中止行程。

攔截關卡 B (硬體層 Intel CET Shadow Stack)：
  即便攻擊者先透過另一處讀取漏洞偷到了 Canary 0x9a3f71c4028b5e00 並在溢位時原封不動填回
  0x7fffffffdce8..dcef (騙過關卡 A)，在開啟 Intel CET 的 CPU 上：
  - 當初執行 call 時，CPU 硬體已同步把真實回傳位址 0x5555555552a4 寫入另一塊受硬體頁表保護、
    一般指令唯讀的影子堆疊 (Shadow Stack，由 SSP 暫存器指向)。
  - 執行 ret 時，CPU 硬體直接比對資料堆疊 [0x7fffffffdcf8] 與影子堆疊 [*SSP]；
    只要兩邊差了半個 bit，當場拋出硬體 #CP (Control Protection Fault) 例外終止行程！
```

這張表把堆疊防禦的演進邏輯攤得一清二楚：因為 `buf[64]` 跟 `Saved RIP` 只隔了短短 `80 bytes`（`0x50`）而且同處一張可寫頁面上，先有編譯器在中間插一根 `8 bytes` 的 Canary 哨兵，後有 CPU 硬體乾脆在旁邊另開一塊「誰都寫不到」的影子堆疊（Shadow Stack）來對答案。

---

### 為什麼少寫一個 `"%s"` 會把整個堆疊印出來？格式字串漏洞剖析

除了直接往緩衝區越界寫入，堆疊上還有另一種常把 Canary 跟 ASLR 位址洩漏光光的經典破口：**格式字串漏洞**（Format String Bug）。

先看下面這兩行每天都會寫到的日誌程式碼，它們只差了一個 `"%s"`，安全後果卻是天壤之別：

```c
// 安全寫法：第一個參數是寫死的格式字串常數，外部輸入當作第二個資料參數
fprintf(stderr, "%s", user_controlled_tag);

// 致命漏洞：直接把外部可控字串當成第一個「格式字串 (fmt)」傳進去！
fprintf(stderr, user_controlled_tag);
```

為什麼少寫一個 `"%s"` 會出大事？這要回到 C 語言變長參數函式（Variadic Function，像 `printf`、`fprintf`、`snprintf`、`syslog`）與 System V AMD64 ABI 的底層約定：

在 C 語言裡，當你呼叫 `printf(fmt, ...)` 時，**編譯器並不會在執行期多傳一個隱藏參數告訴 `printf`：「這次我總共傳了幾個參數給你」**！`printf` 根本不知道呼叫端到底給了幾個參數，它唯一的判斷依據，就是去數第一個參數 `fmt` 字串裡面出現了幾個 `%` 佔位符（像 `%lx`、`%p`、`%s`）。

按照 System V ABI 的傳參順序，`printf` 的第 1 個參數（也就是 `fmt` 格式字串指標本身）放在 `RDI`；後面如果還有整數或指標參數，前 5 個會依序去讀 **`RSI`、`RDX`、`RCX`、`R8`、`R9`** 五個通用暫存器（如果是浮點數則讀 `XMM0`–`XMM7`），從第 6 個格式佔位符開始，它就會直接順著呼叫端的堆疊框架（`[rsp]`、`[rsp+8]`、`[rsp+16]`...）一路往高位址讀下去！

這下你想通了：當攻擊者傳入一串 `"%p.%p.%p.%p.%p.%p.%p.%p.%p"` 當作 `user_controlled_tag`，而呼叫端其實根本沒傳後面的參數時，`fprintf` 還是會照單全收——前 5 個 `%p` 先把當時留在 `RSI`、`RDX`、`RCX`、`R8`、`R9` 暫存器裡的數值印出來，第 6 個 `%p` 開始就直接把呼叫端堆疊上的局部變數、**`Stack Canary`（`[rbp-0x08]`）**，還有 **`Saved RIP`（`[rbp+0x08]`）** 一個接一個用十六進位印給攻擊者看！更糟的是，標準 C 的格式字串裡還有一個極度危險的 **`%n`** 佔位符，它的功能不是印東西，而是「把目前為止已經印出的字元總數，寫進對應參數所指向的記憶體位址裡」，直接把讀取漏洞升格成任意記憶體寫入漏洞。

要徹底消滅格式字串漏洞，規矩只有一條：**永遠不准把外部可控變數放進格式字串的位置**，並且在編譯參數強制加上 **`-Wformat -Wformat-security -Werror=format-security`**，只要有人敢寫出 `printf(var)`，編譯器當場直接報錯拒絕編譯。

---

## 故障模式與防禦

看懂了堆疊幀的脆弱點後，我們把現代 Linux 與編譯器針對堆疊與控制流設下的五道防線逐一攤開。搞清楚每一道防線「守哪裡」跟「哪裡守不住」，你才能在架構設計上排出真正的縱深防禦（Defense in Depth）。

### 防線 1：標準庫呼叫的邊界守門員 `-D_FORTIFY_SOURCE=3`

很多堆疊溢位都發生在呼叫 `memcpy`、`strcpy`、`sprintf`、`fgets` 這些標準庫函式的瞬間。當你在編譯時開啟最佳化並加上 **`-O2 -D_FORTIFY_SOURCE=3`**（需要搭配 `-O1` 以上最佳化才能讓編譯器追蹤物件大小），編譯器就會利用內建的 `__builtin_object_size` 與 **`__builtin_dynamic_object_size`**（GCC 12+ / Clang 9+ 搭配 glibc 2.34+ 起支援，連動態算出的緩衝區大小都能追蹤），算出目的端陣列的真實容量上限，並自動把你的 `memcpy(dst, src, len)` 偷換成帶邊界檢查的強化版 **`__memcpy_chk(dst, src, len, dst_size)`**。

在執行期，只要傳進去的 `len > dst_size`，`__memcpy_chk` 連一個 byte 都不會讓你寫進去，當場就會呼叫 `__chk_fail()` 印出 `buffer overflow detected` 終止訊息並中止行程。同時，開啟 FORTIFY 之後，glibc 也會在執行期拒絕執行位於可寫記憶體（`RW-`）裡的格式字串 `%n` 寫入操作。

**它的盲區在哪裡？** 如果目的緩衝區指標是跨了別的編譯單元（另一個 `.c` 檔）傳過來的，而且沒有長度資訊可以讓編譯器推算，`__builtin_dynamic_object_size` 就會回傳 `(size_t)-1`（代表「我不知道這塊緩衝區有多大」），這時強化檢查就會自動退化回普通的 `memcpy`。

### 防線 2：堆疊上的哨兵 Stack Canary（`-fstack-protector-strong`）

當第一道防線沒看出緩衝區大小（或者程式是用自己寫的 `for` 迴圈逐字元寫入陣列，沒經過 `memcpy`）時，就輪到放在 `[rbp - 0x08]` 的 Stack Canary 守住後門。

就像第 20 章與前面 Worked Example 推導過的，函式開頭從 TLS `fs:0x28` 載入 8-byte Canary（最低位元組固定為 `0x00` 以截斷非預期的 C 字串讀取），返回前若發現該槽位被改動就呼叫 `__stack_chk_fail()`。在編譯選項上，早期的 `-fstack-protector` 只保護含有 `8 bytes` 以上字元陣列的函式；現代主流發行版與我們的硬化基準一律使用 **`-fstack-protector-strong`**，只要函式裡有任何型別與大小的區域陣列、內含陣列的 `struct`，或是對區域變數取了位址（`&var`），統統都會插上 Canary。

**它的盲區在哪裡？** Canary 只在「函式準備返回時」檢查「`[rbp - 0x08]` 那一格有沒有變」。如果漏洞不是從 `buf[0]` 一路連續刷過去的線性溢位，而是**陣列索引越界寫入**（例如 `arr[user_idx] = val`），攻擊者可以直接指定 `user_idx` 跳過 Canary 那一格，精準改寫後面的 `Saved RIP`；又或者攻擊者先靠格式字串漏洞把 Canary 的值偷看清楚了，溢位時把一模一樣的 Canary 原值填回去，尾聲的 `xor` 比對就會以為天下太平而乖乖放行。

### 防線 3：CPU 硬體級的前後向雙重保護 Intel CET（`-fcf-protection=full`）

既然放在同一張可寫堆疊頁上的 Canary 有可能被跳過或偷看，Intel 從 Tiger Lake / Sapphire Rapids 世代開始，直接在 CPU 硬體裡內建了 **CET**（Control-flow Enforcement Technology），把控制流分成**後向邊緣**（Backward-edge，也就是 `ret` 返回）跟**前向邊緣**（Forward-edge，也就是間接 `call`/`jmp` 函式指標）兩路鎖死：

1. **Shadow Stack（`SHSTK`，硬體影子堆疊，鎖死 `ret` 後向邊緣）**：
   作業系統核心為每個執行緒額外配一塊獨立的影子堆疊，它的頁表帶有特殊的硬體保護屬性——**全行程裡任何普通的 `mov`、`memcpy` 或指標寫入指令，通通沒有權限寫入影子堆疊**，只有 `call` 跟 `ret` 這類控制流指令能碰它。執行 `call` 時，CPU 把回傳位址同時寫進普通資料堆疊與影子堆疊（由專屬暫存器 `SSP` 追蹤）；執行 `ret` 時，CPU 把兩邊的值同時彈出來比對。就算普通堆疊上的 Canary 被繞過、`Saved RIP` 被改掉，只要跟影子堆疊裡的值不一樣，CPU 當場拋出 **`#CP`（Control Protection Fault）** 硬體例外！
2. **Indirect Branch Tracking（`IBT`，間接分支追蹤，鎖住 `call rax` 前向邊緣）**：
   當編譯時加上 **`-fcf-protection=full`**，編譯器會在每一個合法可能被間接呼叫的函式第一行，插上一條 4 位元組的著陸標記指令 **`endbr64`**（機器碼 `f3 0f 1e fa`，在不支援 CET 的舊 CPU 上會被當成無害的 `NOP` 跳過，完全向後相容）。當 CPU 執行任何間接呼叫（`call rax`）或間接跳轉（`jmp rdx`）時，硬體內部狀態機就會切到 `WAIT_FOR_ENDBRANCH` 狀態：**如果跳過去落地看到的第一條指令不是 `endbr64`（例如攻擊者想跳進某個函式中間切出一段指令片段來用），CPU 一樣當場拋出 `#CP` 例外！**

### 防線 4：ARM64 處理器的密碼學簽章防線 ARM PAC（Pointer Authentication）

在雲端廣泛使用的 ARM64（AArch64，如 AWS Graviton 與 Apple Silicon）架構上，64 位元指標其實也只用了低 48 位元定址，高 16 位元是閒置的。ARMv8.3-A 導入的 **PAC**（Pointer Authentication）就拿這段閒置的高位元來幫回傳位址「蓋密碼學防偽印章」（編譯旗標為 **`-mbranch-protection=standard`**）：

- 在函式開頭把回傳位址 `LR`（`X30`）壓進堆疊前，先執行一條 **`paciasp`** 指令：CPU 硬體會拿放在特權暫存器裡的秘密金鑰（`APIAKey`，使用者空間程式完全讀不到），搭配當下的堆疊指標 `SP` 作為上下文修飾值（Modifier），用 QARMA 等輕量區塊加密演算法算出一組截斷的訊息驗證碼（**PAC 標籤**），直接塞進 `X30` 指標最高的那幾個閒置位元裡，再存進堆疊。
- 等函式跑完、從堆疊把 `X30` 讀回來準備返回前，再執行一條 **`autiasp`** 指令：CPU 用同一把硬體金鑰與當下的 `SP` 重新驗算一次 PAC 標籤。如果回傳位址在堆疊上被人改過，或者連 `SP` 的高度都不對，驗證就會失敗——這時 `autiasp` 會故意把 `X30` 的高位元破壞成非規範位址（Non-canonical Address），下一行一執行 `ret` 跳過去，MMU 當場就會觸發位址轉譯錯誤把行程攔下來！

### 防線 5：連函式型別簽章都核對的細粒度防線 LLVM CFI（`-fsanitize=cfi`）

看到這裡，你可能會問：有了 Intel CET 的 IBT（`endbr64`）或 ARM 的 BTI，前向的函式指標呼叫是不是就高枕無憂了？

還差最後一塊拼圖。想想看：`endbr64` 屬於**粗粒度**（Coarse-grained）的前向保護——只要跳過去的地方是「任何一個合法匯出函式的第一行（有 `endbr64`）」，CPU 就會放行。但如果程式裡有一個型別是 `int (*log_fn)(const char *)` 的日誌函式指標被越界改寫，攻擊者把它改成同一個行程裡另一個也以 `endbr64` 開頭的合法函式 `int system(const char *)` 的起點呢？因為 `system()` 的第一行也有合法的 `endbr64`，粗粒度的 IBT 是攔不住這種「李代桃僵」的！

為了堵住這個洞，Clang / LLVM 提供了編譯期**細粒度控制流完整性**（Fine-grained Forward-Edge CFI，編譯與連結需同時開啟 **`-flto -fsanitize=cfi`**，搭配連結期最佳化 LTO 取得全程式視角）。它會把全程式所有的函式按照**參數與回傳值的型別簽章**（Type Signature）分成不同的等價集合（例如 `int (*)(int, int)` 是一組，`void (*)(const char *)` 是另一組）。每次程式要透過函式指標或 C++ 虛擬表（`vtable`）做間接呼叫前，編譯器插入的檢查碼都會先核對：「目標位址不只要是合法函式的開頭，還必須屬於跟這個呼叫點型別簽章完全吻合的那張白名單表！」只要型別簽章對不上，當場就會觸發 `ud2` 非法指令中止程式。

### 五大堆疊與控制流防線全景對照表

| 防禦機制 | 編譯／連結啟用參數 | 防守位置 | 核心攔截原理 | 什麼情況下還是會被繞過（盲區） |
|---|---|---|---|---|
| **FORTIFY_SOURCE** | `-O2 -D_FORTIFY_SOURCE=3` | 標準庫資料寫入前 | 將 `memcpy`/`snprintf` 換成帶容量上限檢查的 `__*_chk` 函式 | 跨編譯單元導致編譯器算不出目的緩衝區大小，或手寫迴圈未走標準庫 |
| **Stack Canary** | `-fstack-protector-strong` | 後向（`ret` 返回前） | 比對 `[rbp-0x08]` 哨兵值與 TLS `fs:0x28` 是否一致 | 索引越界寫入直接跳過 Canary 槽位，或先靠 Info Leak 偷出 Canary 再原值填回 |
| **Intel CET Shadow Stack** | `-fcf-protection=full`（需 CPU 與 OS 支援） | 後向（`ret` 硬體比對） | `call` 時同步將回傳位址寫入硬體唯讀影子堆疊，`ret` 時雙邊比對不符即拋 `#CP` | 不保護前向的函式指標或 C++ `vtable` 間接呼叫 |
| **Intel CET IBT / ARM BTI** | `-fcf-protection=full` / `-mbranch-protection=standard` | 前向（粗粒度間接跳轉） | 強制要求 `call/jmp reg` 落點第一條指令必須是 `endbr64` 或 `bti` | 攻擊者若跳往另一個同樣以 `endbr64` 開頭的高危合法函式起點，粗粒度檢查會放行 |
| **ARM PAC** | `-mbranch-protection=standard` | 後向與指標完整性 | 用硬體金鑰與 `SP` 為 `LR` 高位元簽發 `paciasp` 密碼標籤，`autiasp` 驗不過即破壞位址 | 若金鑰與上下文相同，在特定簽章重用（Signing Gadget）條件下仍有理論替換風險 |
| **LLVM Fine-grained CFI** | `-flto -fsanitize=cfi` | 前向（細粒度型別簽章） | 在間接呼叫與 `vtable` 分派前，強制驗證目標函式是否屬於相同型別簽章集合 | 只能跳往完全相同參數與回傳型別的同集合函式；不負責後向 `ret`（需搭 Shadow Stack） |

---

## 動手做

- **難度**：入門
- **預估時間**：35 分鐘

現在我們在本地 Linux x86_64 環境寫一個模擬 `libnexus-parse` 快速路徑的良性防禦實驗（完全不需要構造攻擊 payload）。我們故意傳入一筆長度 `len = 88`（超過堆疊快速緩衝區 `fast_buf[64]`）的封包，親眼看看：
1. 開啟 `-fstack-protector-strong -fcf-protection=full -D_FORTIFY_SOURCE=3` 時，編譯器在組合語言裡植入了哪些防護指令？執行時是誰把越界寫入擋下來的？
2. 換用測試與 Fuzzing 必備的 **AddressSanitizer**（`-fsanitize=address`，簡稱 ASan）編譯時，它印出來的診斷報告有多精準？
3. 補上嚴格的入口邊界檢查後，程式怎麼安全拒收超長封包？

### 步驟 1：建立 `nexus_tlv_check.c` 對照測試檔

建一個空目錄，把下面這段程式碼存成 `nexus_tlv_check.c`。我們用一個巨集 `FIX_BOUNDS` 來切換「漏掉邊界檢查的缺陷版」與「補上雙重上限檢查的修補版」：

```c
// nexus_tlv_check.c
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define NEXUS_MAX_PAYLOAD 65536U
#define FAST_BUF_SIZE 64U

typedef struct __attribute__((packed)) {
    uint16_t magic;
    uint16_t type;
    uint32_t len;
} nexus_tlv_hdr_t;

__attribute__((noinline))
int parse_fast_tlv(const nexus_tlv_hdr_t *hdr, const uint8_t *payload) {
    uint8_t fast_buf[FAST_BUF_SIZE];

#ifdef FIX_BOUNDS
    /* 入口處一次鎖死全書基準上限 (65,536) 與局部緩衝區實際大小 (64) */
    if (hdr->magic != 0x4e58 || hdr->len > NEXUS_MAX_PAYLOAD || hdr->len > sizeof(fast_buf)) {
        fprintf(stderr, "[reject] invalid TLV packet: magic=0x%04x len=%u (max fast=%zu, tlv=%u)\n",
                hdr->magic, hdr->len, sizeof(fast_buf), NEXUS_MAX_PAYLOAD);
        return -1;
    }
#endif

    /* 當未定義 FIX_BOUNDS 時，len = 88 會直接寫爆 64-byte 的 fast_buf */
    memcpy(fast_buf, payload, hdr->len);
    printf("[ok] parsed type=0x%04x len=%u first_byte=0x%02x\n",
           hdr->type, hdr->len, hdr->len > 0 ? fast_buf[0] : 0);
    return 0;
}

int main(void) {
    nexus_tlv_hdr_t hdr = { .magic = 0x4e58, .type = 0x0001, .len = 88 };
    uint8_t dummy_payload[128];
    memset(dummy_payload, 0x41, sizeof(dummy_payload));

    return parse_fast_tlv(&hdr, dummy_payload);
}
```

### 步驟 2：編譯並觀察三種防護與診斷組態的行為

依序在終端機執行下面四組指令：

```bash
# 1. 編譯未修補的生產環境硬化版 (開 Canary + Intel CET + FORTIFY_SOURCE=3)
gcc -O2 -g -fstack-protector-strong -fcf-protection=full -D_FORTIFY_SOURCE=3 \
    nexus_tlv_check.c -o tlv_vuln_hardened
./tlv_vuln_hardened

# 2. 用 objdump 檢視 parse_fast_tlv 被植入了哪些防禦指令
objdump -d -M intel tlv_vuln_hardened | sed -n '/<parse_fast_tlv>:/,/^$/p'

# 3. 編譯未修補的 AddressSanitizer (ASan) 除錯版並執行
gcc -O1 -g -fsanitize=address -fno-omit-frame-pointer \
    nexus_tlv_check.c -o tlv_vuln_asan
./tlv_vuln_asan

# 4. 編譯補上入口檢查的修復版 (-DFIX_BOUNDS) 並驗證
gcc -O2 -g -DFIX_BOUNDS -fstack-protector-strong -fcf-protection=full \
    -D_FORTIFY_SOURCE=3 -Wformat -Wformat-security -Werror=format-security \
    nexus_tlv_check.c -o tlv_fixed
./tlv_fixed
```

### 外部靶場對照檢查點（pwn.college）

做完本地實驗後，推薦到 **pwn.college** 的 **Program Security -> Memory Errors** 模組讀讀看各關卡的靶標原始碼。這次請換個視角：不要只顧著想怎麼灌長字串進去，而是去觀察每一關的出題者是用哪種常見的 C 語言寫法失誤（像是把 `sizeof(pointer)` 當成陣列大小、用有號 `int` 接長度導致負數繞過 `< MAX_LEN` 檢查、或是 `read()` 回傳值算錯）把邊界弄破的，並在 GDB 裡用 `info frame` 跟 `x/20gx $rsp` 核對堆疊幀上各個欄位的真實距離。

---

### 參考解答

#### 1. 硬化版攔截與 `objdump` 三大防禦特徵

執行第一組未修補的 `./tlv_vuln_hardened` 時，因為我們傳入的 `len = 88` 超過了 `fast_buf` 的 `64 bytes`，程式連寫入都還沒完成（或還沒走到 `ret`），當場就被攔下來並印出：

```text
*** buffer overflow detected ***: terminated
Aborted (core dumped)
```

為什麼印的是 `buffer overflow detected` 而不是 `stack smashing detected`？答案就在第二步 `objdump -d -M intel tlv_vuln_hardened` 印出來的 `parse_fast_tlv` 組合語言裡。你會清楚看到編譯器幫這個函式穿上了三層鐵甲：
1. **第一行就是 `endbr64`**：這是 `-fcf-protection=full` 加上的 Intel CET IBT 合法間接跳轉著陸點。
2. **開頭讀 `fs:0x28`、結尾比對 `fs:0x28` 與 `__stack_chk_fail@plt`**：這是 `-fstack-protector-strong` 插進去的 Stack Canary 守衛。
3. **`call memcpy` 被換成了 `call __memcpy_chk@plt`**：因為開了 `-O2 -D_FORTIFY_SOURCE=3`，編譯器明確知道目的端 `fast_buf` 只有 `64 bytes`（會在第 4 個參數 `rcx` 傳入 `0x40`），所以當第 3 個參數 `rdx` 傳入 `88`（`0x58 > 0x40`）時，`__memcpy_chk` 在拷貝發生前就直接攔截自盡了！

   如果當時編譯沒開 FORTIFY，這筆 88 bytes 的寫入就會蓋掉 Canary，然後在函式結尾被第二層的 `__stack_chk_fail` 攔下來，印出 `stack smashing detected` 終止訊息。

#### 2. AddressSanitizer（ASan）的精準診斷報告

跑第三組 `./tlv_vuln_asan` 時，ASan 利用紅區（Redzone）與影子記憶體（Shadow Memory），在越界寫入發生的那一行直接給出了連檔名、行號、變數名稱跟越界偏移都一清二楚的報告：

```text
==PID==ERROR: AddressSanitizer: stack-buffer-overflow on address 0x7fffffffdcd0
WRITE of size 88 at 0x7fffffffdcd0 thread T0
    #0 in parse_fast_tlv nexus_tlv_check.c:27
  This frame has 1 object(s):
    [32, 96) 'fast_buf' (line 16) <== Memory access at offset 96 overflows this variable
```

報告明白告訴你：這格堆疊幀上的 `fast_buf` 範圍在偏移 `[32, 96)`（長度 `64 bytes`），而第 27 行的寫入卻要求寫 `88 bytes`，在偏移 `96` 的地方寫出界了。這也是為什麼第 29 章我們做原生模組 Fuzzing 時，一定會掛上 ASan 來抓記憶體錯誤。

#### 3. 修復版的安全降級行為

跑第四組 `./tlv_fixed` 時，注意它跟前面兩組最大的差別：**前面的 FORTIFY、Canary 跟 ASan 雖然攔住了攻擊，但代價都是整個 Worker 行程當場崩潰（`Aborted`）！** 只有補上入口邊界檢查的 `./tlv_fixed`，才能在看到 `len = 88 > 64` 時優雅地印出：

```text
[reject] invalid TLV packet: magic=0x4e58 len=88 (max fast=64, tlv=65536)
```

然後乾淨回傳錯誤碼 `-1`，讓伺服器繼續活著服務下一筆商戶請求。記住：**編譯器與硬體緩解是保命的最後防線，入口處的型別與長度檢查才是讓服務不中斷的正道。**

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別看下方解答，試著動筆算算看並回答下面 4 個問題：

1. **手算滿足 16-byte 對齊的最小 `sub rsp, N`**：在 Linux x86_64 環境下，某個 C 函式 `verify_token()` 裡面只宣告了一個局部陣列 `char token_buf[100]`，沒有其他局部變數，且編譯時開啟了 `-fstack-protector-strong`。假設該函式開頭只執行了標準的 `push rbp; mov rbp, rsp`（沒有多 `push` 其他 Callee-saved 暫存器），接著要執行 `sub rsp, N` 配空間給 `token_buf` 跟 `8-byte` Stack Canary，並確保後面呼叫子函式時符合 System V ABI 的 `16-byte` 堆疊對齊不變量。請問 `N` 的最小十進位與十六進位數值是多少？
2. **格式字串漏洞為什麼能同時打破 ASLR 跟 Stack Canary**：某段 C 語言日誌函式寫成了 `syslog(LOG_INFO, req_header)`，其中 `req_header` 是外部 HTTP 請求帶進來的字串。請從 System V AMD64 ABI 的傳參暫存器與堆疊讀取順序，說明為什麼攻擊者只要送出一串 `"%lx.%lx..."`，就能在一次請求內同時廢掉該行程的 `28-bit` ASLR 與 Stack Canary 防護？
3. **陣列索引越界寫入時，Canary 與 Intel CET Shadow Stack 誰守得住**：假設某個 C 函式沒有線性緩衝區溢位，但是有一處「未檢查正負與上限的陣列索引寫入」：`scores[user_index] = new_score;`（其中 `scores` 是放在堆疊上的局部陣列）。請問攻擊者能不能繞過 Stack Canary 直接改寫 `Saved RIP`？如果這台伺服器跑在支援並開啟 Intel CET Shadow Stack（`SHSTK`）的處理器與核心上，函式執行 `ret` 時會發生什麼事？
4. **為什麼開了 Intel CET IBT（`endbr64`）還需要 LLVM CFI**：某團隊在編譯 C++ 高頻交易模組時已經加上了 `-fcf-protection=full`，確認每個函式開頭都有 `endbr64` 指令。為什麼資安顧問還是建議他們在發布建置時加上 `-flto -fsanitize=cfi`？請舉一個 `endbr64` 攔不住、但 LLVM CFI 攔得住的具體場景。

---

### 參考解答

1. **手算滿足 16-byte 對齊的最小 `sub rsp, N`**：
   - 先算局部空間至少要裝多少東西：`100 bytes`（`token_buf[100]`）+ `8 bytes`（Stack Canary）= `108 bytes`。
   - 接著對齊 `16 bytes`：呼叫端執行 `call` 前 `RSP % 16 == 0`，`call` 壓入 `8-byte` `Saved RIP` 再加上開頭的 `push rbp`（`8-byte` `Saved RBP`），剛好減了 `16 bytes`，此時 `RSP % 16` 已經重新回到 `0`。
   - 因此，`sub rsp, N` 的 `N` 本身也必須是 `16` 的倍數，而且要大於等於 `108`。大於等於 `108` 的最小 `16` 的倍數是 $16 \times 7 = 112$，所以最小的 `N` 值為 **`112 bytes`（十六進位 `0x70`）**。
2. **格式字串漏洞為什麼能同時打破 ASLR 跟 Stack Canary**：
   - 因為 `syslog` 這類變長參數函式不知道呼叫端實際傳了幾個參數，只會照著格式字串裡的 `%lx` 個數，依序把第 2 到第 6 個參數暫存器（`RSI`、`RDX`、`RCX`、`R8`、`R9`）以及呼叫端堆疊上的槽位（`[rsp]`、`[rsp+8]`...）一個個讀出來印進日誌裡。
   - 呼叫端堆疊フレーム裡正好躺著 `8-byte` 的 **Stack Canary**（可由最低位元組為 `00` 且高 7 位元組看似高熵亂數的特徵一眼認出），以及緊跟在 `Saved RBP` 後面的 **`Saved RIP` 回傳位址**（指向呼叫端 `.text` 或 `libc` 的真實執行期位址）。只要印出這兩個值，Canary 的秘密當場曝光，拿 `Saved RIP` 減去固定符號偏移也瞬間把 `28-bit` ASLR 的未知數歸零。
3. **陣列索引越界寫入時，Canary 與 Intel CET Shadow Stack 的表現**：
   - **Stack Canary 守不住**：Canary 只在函式結尾檢查 `[rbp - 0x08]` 那一格有沒有被改掉。既然是按索引寫入 `scores[user_index] = new_score`，攻擊者只要算準 `Saved RIP` 相對於 `scores[0]` 的距離填進 `user_index`，就能直接跳過 Canary 那一格、一槍改寫 `[rbp + 0x08]` 的 `Saved RIP`，Canary 比對時完全不會發現異狀。
   - **Intel CET Shadow Stack 守得住**：因為當初進入函式執行 `call` 時，CPU 硬體已經把正牌的回傳位址同步備份在硬體唯讀的影子堆疊（Shadow Stack）裡，那個地方連 `scores[user_index]` 都寫不到。等函式執行 `ret` 的一瞬間，CPU 硬體把資料堆疊上被竄改的 `Saved RIP` 跟影子堆疊裡的正牌位址一比，發現對不上，當場就會拋出 **`#CP`（Control Protection Fault）** 硬體例外攔住控制流劫持。
4. **為什麼開了 Intel CET IBT（`endbr64`）還需要 LLVM CFI**：
   - Intel CET IBT 只是**粗粒度**的前向保護，它只管「間接呼叫跳過去的第一條指令是不是 `endbr64`」，根本不管那個函式原本是幹嘛的。
   - **具體場景**：假設程式裡有一個處理商戶回呼的函式指標 `void (*on_success)(const char *merchant_name)`，而在同一個行程裡也連結了標準庫的 `int system(const char *command)`。因為 `system()` 也是合法的公開函式，它的第一行指令同樣是 `endbr64`！如果攻擊者透過記憶體漏洞把 `on_success` 指標改寫成 `system` 的起點，並把 `merchant_name` 設成惡意 shell 指令，Intel CET IBT 看到目標第一行有 `endbr64` 就會直接放行；但若開啟了 **LLVM CFI（`-flto -fsanitize=cfi`）**，編譯器在呼叫前會檢查目標位址是否屬於 `void (*)(const char *)` 的合法目標集合，發現 `int system(const char *)` 的回傳型別與等價集合都不符，就會在跳轉前立刻攔截。

---

## 延伸閱讀

- **System V Application Binary Interface — AMD64 Architecture Processor Supplement**（https://gitlab.com/x86-psABIs/x86-64-ABI）：查閱 x86_64 堆疊幀結構、變長參數暫存器傳遞規則與 `16-byte` 堆疊對齊不變量的官方標準文件。
- **Intel 64 and IA-32 Architectures Software Developer's Manual — Control-flow Enforcement Technology (CET)**：詳細定義硬體影子堆疊（`SHSTK`）、`SSP` 暫存器、頁面保護屬性以及間接分支追蹤（`IBT` / `endbr64`）觸發 `#CP` 例外的硬體規格。
- **ARM Architecture Reference Manual — Pointer Authentication (PAC)**：說明 ARMv8.3-A 的 `APIAKey` 金鑰管理、`paciasp` / `autiasp` 指令與指標高位元 PAC 標籤的密碼學驗證流程。
- **Clang / LLVM Control Flow Integrity Documentation**（https://clang.llvm.org/docs/ControlFlowIntegrity.html）：深入介紹 `-fsanitize=cfi` 底下的 `cfi-icall`（函式指標間接呼叫）與 `cfi-vcall`（C++ 虛擬表呼叫）如何在 LTO 階段建立細粒度型別等價檢查表。
- **Red Hat Developer Blog — Enhance application security with `_FORTIFY_SOURCE=3`**（https://developers.redhat.com/articles/2022/09/17/gccs-new-fortify-level）：解析 `__builtin_dynamic_object_size` 如何把編譯期邊界檢查擴展到動態大小的緩衝區。
