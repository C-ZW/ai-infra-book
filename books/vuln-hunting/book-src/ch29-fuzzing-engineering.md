# 第 29 章：灰箱 Fuzzing 工程實戰

上一章我們用 CodeQL 與 Semgrep 解決了「已知漏洞模式如何在整個程式碼庫裡橫向抓出變體」的問題。但靜態分析有個天生的盲區：工程師必須事先知道危險 Sink 和邏輯破口長什麼樣子。一旦面對好幾萬行的 C/C++ 解析器、多層狀態機或跨語言 FFI 膠水層，靜態規則不是漏掉隱晦的邊界組合（例如連續三個封包互動才觸發的懸垂指標），就是噴出一堆在執行期根本走不到的假警報。

**覆蓋率導引灰箱 Fuzzing**（Coverage-Guided Greybox Fuzzing）用完全不同的思路補上這塊拼圖。它不需要人先猜漏洞在哪，而是靠編譯期插樁（Instrumentation）記錄每次輸入走過的控制流邊緣（Control-Flow Edge），把能解鎖新路徑或新迴圈次數級距的輸入留存下來繼續變異。

只要再搭配關閉錯誤恢復的 **Sanitizers**，就能在記憶體越界、UAF、未定義行為或未初始化讀取發生的那一刻當場攔截並中止行程，讓 Fuzzer 存下觸發輸入並自動縮減出最小化 PoC。本章沿用 **NexusPay** 的原生解析模組 `libnexus-parse`（`8 bytes` TLV 檔頭、合法負載上限 `65,536 bytes` / `64 KiB`），一路拆解 AFL++ 位圖設計、Persistent Mode 吞吐量調校、Sanitizers 影子記憶體機制，以及 Rust `cargo-fuzz` 搭配 `arbitrary` 的結構感知模糊測試工作流。

---

## 從你已知的出發

寫完單元測試跟屬性測試（Property-Based Testing），為什麼底層 C/Rust 解析器上線後還是會被畸形封包打崩？因為傳統測試驗證的是「合法輸入在設計路徑上能不能算出正確結果」，而有限的測試案例永遠只能覆蓋設計師想得到的幾個輸入點，根本不可能窮舉整個狀態空間。

灰箱 Fuzzing 直接把這個邏輯反過來：在不額外掛載業務斷言或差分測試（Differential Testing）參考實作時，它不管業務輸出對不對，而是用每秒數千次的極高吞吐量把半合法、畸形與邊界外的位元組灌進解析器，看哪一筆輸入能打破**記憶體安全或執行期不變量**（若在 Harness 加上輸出斷言或新舊版本比對，也能抓邏輯錯誤）。

要把 Fuzzer 的威力催到極限，就得把它當成一台**靠覆蓋率回饋驅動的狀態空間搜尋引擎**。決定它成敗的只有三個硬指標：每秒執行次數（`exec/s`）、覆蓋率訊號的解析度與碰撞率，以及偵測器（Sanitizers）能不能在不拖垮吞吐量的前提下，把微小的記憶體越界當場轉成明確的 Crash。

---

## 機制與推導

### 攻擊者目標與實質影響

當漏洞研究員或紅隊盯上後端服務底層的原生解析模組（像是 NexusPay 透過 N-API 掛載的 `libnexus-parse`、影像壓縮函式庫或自訂網路協定解碼器），導入高吞吐灰箱 Fuzzing 追求的是三個實質戰果：

第一是**自動挖出靜態審計很難看穿的深層記憶體損毀**。第 25 章我們看過 `libnexus-parse` 在 `len = 0xFFFF_FFF8` 時發生 32 位元加法回繞與 `malloc(0)` 越界寫入。在真實解析器裡，這種觸發條件往往埋在特定的 TLV `type` 順序、巢狀結構或錯誤處理分支後面，光靠肉眼看 code 很容易漏掉。灰箱 Fuzzer 配上 ASan，幾分鐘內就能把深層分支裡的堆積溢位、UAF 與雙重釋放變成可重現的二進位 PoC。

第二是**揪出不會當場崩潰、卻能串成攻擊鏈的邏輯與未初始化破口**。未初始化的堆疊讀取（靠 MSan 捕捉）與有號整數溢位（靠 UBSan 捕捉）在一般執行環境下根本不會噴 `SIGSEGV`，但它們卻是第 20 到 24 章用來偷看 ASLR 位址或繞過長度檢查的關鍵跳板。

第三是**建立規模化的 0-day 挖掘與回歸防線**。把單次找漏洞的過程固化成可持續運轉的 Harness、字典檔與最小化語料庫（Seed Corpus），每次程式碼一改動，幾分鐘內就能跑完百萬次級別的壓力測試（第 31 章會講怎麼把這套管線推上大型開源專案與 OSS-Fuzz；第 30 章則會處理卡在校驗和與魔數時的混合符號求解）。

---

### AFL++ 覆蓋率導引原理：`64 KiB` 位圖與邊緣雜湊

灰箱 Fuzzing 之所以比純隨機亂塞輸入（黑箱 Fuzzing）強得多，關鍵在於編譯器在每個基本區塊（Basic Block）入口偷偷塞進去的輕量級探針。

如果只記錄「某個函式有沒有跑過」（函式覆蓋率）或「某個基本區塊有沒有走過」（區塊覆蓋率），Fuzzer 其實看不出控制流的先後順序。所以 AFL++ 追蹤的是**邊緣覆蓋率**（Edge Coverage）——也就是控制流「從基本區塊 A 跳到基本區塊 B」這條有向邊（Edge）。

在預設組態下，AFL++ 會配置一塊固定大小為 **`65,536 bytes`（`64 KiB`）** 的共享記憶體位圖 `trace_bits`（對齊全書基準常數）。每當程式走進一個基本區塊，插樁程式碼就會執行下面這四行邏輯：

```c
// AFL++ 經典插樁邏輯（概念等效 C 表示）
// cur_loc 是編譯期替該基本區塊隨機指派的 16-bit 常數 ID (0 .. 65535)
// __afl_prev_loc 是 Thread-Local Storage (TLS) 變數
uint16_t edge_id = cur_loc ^ __afl_prev_loc;
__afl_area_ptr[edge_id]++;
__afl_prev_loc = cur_loc >> 1;
```

這短短四行程式碼，藏著三個非常巧妙的工程決策：

第一個巧思是**為什麼要把上一個位置右移一位（`cur_loc >> 1`）**？如果不右移，直接寫 `__afl_prev_loc = cur_loc`，馬上會撞上兩個大問題。

首先，因為 XOR 具有交換律（`A ^ B == B ^ A`），Fuzzer 會分不出程式是從 `A → B` 還是從 `B → A`。其次，當迴圈自己跳回自己（`A → A`）時，`A ^ A == 0`，所有自迴圈都會擠進同一個槽位 `trace_bits[0]`。把來源位址右移一位之後，`cur_loc ^ (prev_loc >> 1)` 就一舉打破了交換律與自反律。

第二個巧思是**為什麼每個槽位要用 `uint8_t` 計數器，而不是 `1-bit` 的布林值**？如果只記「有走過／沒走過」，就會漏掉「迴圈跑第 1 次沒事、跑第 9 次才溢位」的漏洞。但如果計數器太敏感，迴圈跑 100 次跟跑 101 次都被當成新路徑，語料庫馬上就被灌爆了。

所以 AFL++ 在每次執行結束後，會把每個 `uint8_t` 計數器歸納成 **8 個對數級距**（Hit-Count Buckets），剛好對應一個 byte 裡的 8 個 bit：
- Bucket 0 (`0x01`)：命中 `1` 次
- Bucket 1 (`0x02`)：命中 `2` 次
- Bucket 2 (`0x04`)：命中 `3` 次
- Bucket 3 (`0x08`)：命中 `4–7` 次
- Bucket 4 (`0x10`)：命中 `8–15` 次
- Bucket 5 (`0x20`)：命中 `16–31` 次
- Bucket 6 (`0x40`)：命中 `32–127` 次
- Bucket 7 (`0x80`)：命中 `128–255` 次

只有當某筆輸入在位圖槽位上點亮了以前從沒出現過的級距位元（不管是第一次踩進某個槽位，還是第一次把某個槽位推到新的次數級距），Fuzzer 才會認定它是「有趣種子」（Interesting Seed）並收進 Queue 裡。

第三個則是隨機雜湊帶來的副作用：**位圖碰撞飽和**。當解析器只有幾百條邊時，`65,536` 個槽位綽綽有餘；但只要目標程式連同相依函式庫的可達邊緣超過 `4,000` 條，隨機 XOR 雜湊就會開始頻繁把不同的邊撞進同一個槽位，害 Fuzzer 誤以為新輸入沒走出新路徑而直接丟掉。

```
┌──────────────────────────────────────────────────────────────────────┐
│ AFL++ 雙向控制流與碰撞免除對照                                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [1] 經典隨機雜湊插樁 (CLASSIC XOR 模式：cur_loc ^ (prev_loc >> 1))  │
│      BB_A (0x1a20) ──▶ BB_B (0x4f03): 0x4f03 ^ (0x1a20 >> 1) = 0x4213│
│      BB_B (0x4f03) ──▶ BB_A (0x1a20): 0x1a20 ^ (0x4f03 >> 1) = 0x3da1│
│      問題：若程式總邊緣數 E > 4,000，隨機雜湊極高機率出現槽位碰撞    │
│                                                                      │
│  [2] 連結時期無碰撞插樁 (afl-clang-lto 連續索引 / PCGUARD 獨立守衛)  │
│      LTO 於 Link Time 全域盤點所有邊緣，指派連續索引 0 .. E-1        │
│      並依實際邊數動態配置 AFL_MAP_SIZE（零雜湊碰撞）                 │
└──────────────────────────────────────────────────────────────────────┘
```

因此在實戰中編譯 C/C++ 目標時，只要環境支援 LLVM LTO（Link-Time Optimization），一律優先選用 **`afl-clang-lto`**（無碰撞插樁）或 **`afl-clang-fast` 的 `PCGUARD` 模式**（替每條邊分配獨立的 guard ID 並自動對應位圖大小）。如果受限於建置系統只能用 `64 KiB` 固定位圖的經典 XOR 插樁，就得緊盯 `afl-fuzz` 畫面上的 `bitmap cvg`（位圖佔用率），並在支援擴大索引空間的插樁模式下調大 `AFL_MAP_SIZE`。

---

### 吞吐量工程：從 `fork()` 到 Persistent Mode

跑 Fuzzing 時，每秒執行次數（`exec/s`）直接決定了你能在有限時間內挖多深。要看懂速度卡在哪裡，我們先比較一筆測試輸入在三種執行模式下的生命週期開銷：

最原始的是 **`fork` + `execve` 模式**。每測一筆輸入，父行程就 `fork()` 出子行程，再呼叫 `execve()` 重新載入執行檔、解析 ELF、請動態連結器 `ld-linux.so` 載入並重定位共用函式庫、跑完 C runtime 初始化，最後才終於進到可能只跑不到 `10 μs` 的解析函式。光前面的啟動開銷就要好幾毫秒，單核每秒只能跑幾十到一百多次。

進階一點的是 **Forkserver 模式**（標準 AFL++ `fork()`）。目標行程先把動態連結和 `_init` 全部跑完，在踏進 `main()` 之前停在 Forkserver 迴圈裡透過管線待命。之後每測一筆輸入，Forkserver 只要呼叫一次 `fork()`，靠作業系統的 Copy-on-Write（COW）複製行程空間，跑完再由 `waitpid()` 回收。這招省掉了 `execve` 與動態連結，但每次還是得複製頁表、建立與銷毀核心 `task_struct`，單核吞吐量通常會卡在 **`200–600 exec/s`**。

最快的是 **Persistent Mode**（`__AFL_LOOP` + 共享記憶體輸入）。面對像 `libnexus-parse` 這種純記憶體解析器，只要在同一個子行程裡包一層迴圈，並用 `__AFL_FUZZ_INIT()` 讓 Fuzzer 把變異好的位元組直接寫進共享記憶體指標 `__AFL_FUZZ_TESTCASE_BUF` 即可。每次迭代只要呼叫解析函式、清掉暫存狀態與位圖，就能把 `fork()` 跟檔案 I/O 成本攤平一萬倍，把單核吞吐量推上 **`5,000 exec/s` 以上**（全書基準常數）。

先看一段標準的 Persistent Mode 骨架：

```c
#include <stdint.h>
#include <stddef.h>

__AFL_FUZZ_INIT();

int nexus_parse_tlv(const uint8_t *buf, size_t len);

int main(void) {
#ifdef __AFL_HAVE_MANUAL_CONTROL
    __AFL_INIT(); // 把 forkserver 延後到昂貴的初始化完成之後再啟動
#endif
    unsigned char *buf = __AFL_FUZZ_TESTCASE_BUF;

    // 單一子行程連跑 10,000 筆輸入後才重新 fork 一次
    while (__AFL_LOOP(10000)) {
        int len = __AFL_FUZZ_TESTCASE_LEN;
        nexus_parse_tlv(buf, (size_t)len);
        // 注意：若被測函式有改動全域狀態或靜態快取，必須在這裡歸零重置！
    }
    return 0;
}
```

寫 Persistent Mode 有兩個眉角一定要顧好。

第一，`__AFL_LOOP(10000)` 不是無限迴圈。子行程每跑滿 10,000 次就會主動退出，讓 Forkserver 重新 `fork()` 一個乾淨的子行程出來，這樣就算程式裡有微小的記憶體洩漏，也不會一路累積到把 RAM 吃光（前提當然是單輪洩漏不會在 10,000 次內就先把記憶體塞爆）。

第二，如果被測函式會改動全域變數（例如累加封包計數器或錯誤旗標），卻忘了在迴圈結尾重置，同一筆輸入在第 1 次跑跟在第 500 次跑就會走進不同分支。這時 `afl-fuzz` 面板上的 `stability` 指標就會摔到 `90%` 以下，讓 Fuzzer 被混亂的覆蓋率訊號搞瞎。

---

### 實例推導：吞吐量計算與 `64 KiB` 位圖雜湊碰撞量化

我們直接拿 NexusPay 的 `libnexus-parse` 測試場景來算一筆帳：一邊比較跑完一百萬次變異所需的時間，另一邊用生日悖論（Birthday Paradox）與期望佔用率，算出 `64 KiB`（`M = 65,536` 個槽位）位圖在不同邊緣規模下會漏掉多少覆蓋率訊號。

```text
=== Worked Example：Fuzzing 吞吐量與 64 KiB 位圖碰撞數值推導 ===

[Part A] 跑滿 N = 1,000,000（10^6）次變異執行的單核時間對比

  1. 標準 fork() 模式（基準吞吐 R_fork = 200 exec/s，單次耗時 5.0 ms）：
     T_fork = 1,000,000 / 200 = 5,000 秒
            = 5,000 / 60      = 83.33 分鐘（約 83.3 分鐘，即 1 小時 23 分 20 秒）

  2. Persistent Mode（基準吞吐 R_pers = 5,000 exec/s，單次耗時 0.2 ms）：
     T_pers = 1,000,000 / 5,000 = 200 秒
            = 200 / 60          = 3.33 分鐘（約 3.3 分鐘，即 3 分 20 秒）

  3. 加速倍率與單日探索規模：
     加速比 = 5,000 / 200 = 25.0 倍
     24 小時（86,400 秒）總變異數：
       - fork() 模式       : 200 × 86,400   = 17,280,000 次（1.73 × 10^7）
       - Persistent Mode   : 5,000 × 86,400 = 432,000,000 次（4.32 × 10^8）

[Part B] 64 KiB 位圖（M = 65,536 個槽位）在 E 條邊緣下的雜湊碰撞估算

  假設各邊緣 ID 彼此獨立且均勻隨機分布於 M = 65,536 個槽位：
  - 至少發生 1 次碰撞的機率：
    P(collision >= 1) ≈ 1 - exp(-E × (E - 1) / (2 × M))
  - 期望被佔用的不重複槽位數：
    E[occupied] = M × (1 - (1 - 1/M)^E) ≈ M × (1 - exp(-E / M))
  - 期望因碰撞而「互覆蓋／遺失」的邊緣數：
    E[lost] = E - E[occupied]

  逐規模實算結果（M = 65,536）：
  +----------+-------------------+--------------+-------------------+----------------+
  | 邊緣數 E | P(collision >= 1) | 期望佔用槽位 | 期望遺失邊緣數    | 覆蓋訊號損失率 |
  +----------+-------------------+--------------+-------------------+----------------+
  |      100 |  7.27% (0.0727)   |        99.92 |    0.08 條        |  0.08%         |
  |      500 | 85.10% (0.8510)   |       498.10 |    1.90 條        |  0.38%         |
  |    1,000 | 99.95% (0.9995)   |       992.42 |    7.58 條        |  0.76%         |
  |    2,000 | ~100.00%          |     1,969.81 |   30.19 條        |  1.51%         |
  |    4,000 | ~100% (1-e^-122)  |     3,880.40 |  119.60 條        |  2.99%         |
  |    8,000 | ~100.00%          |     7,531.05 |  468.95 條        |  5.86%         |
  |   16,000 | ~100.00%          |    14,196.67 | 1,803.33 條       | 11.27%         |
  |   32,000 | ~100.00%          |    25,318.00 | 6,682.00 條       | 20.88%         |
  +----------+-------------------+--------------+-------------------+----------------+

  工程判讀：
  - 在 E = 1,000 的小型解析器中，雖然出現「至少 1 次碰撞」的機率已達 99.95%
    （更小的 E = 100 或 500 則分別為 7.27% 與 85.10%），但 E <= 1,000 時平均預期共槽損失的
    邊緣不超過 7.58 條（0.76%），64 KiB 位圖仍能維持高靈敏度。
  - 當 E = 4,000 時，期望碰撞損失逼近 120 條邊緣（佔用率 ~5.9%，損失率 ~3%）；
    一旦大型函式庫達到 E = 32,000，整批邊緣的期望共槽比例超過五分之一（20.88%，約 6,682 條），
    顯著降低新邊緣的辨識度。此時應切換至 afl-clang-lto（無碰撞連續索引）或搭配 PCGUARD 調大 AFL_MAP_SIZE。
```

---

### Sanitizers 原理與開銷：ASan、UBSan 與 MSan

如果只有 Fuzzer 拼命往深處鑽，卻沒有偵測器在旁邊盯著記憶體狀態，很多致命漏洞根本不會當場暴雷。比如越界多寫了 `1 byte` 到下一個 heap chunk 的對齊填充區，或是讀了未初始化的 `4 bytes` 堆疊殘留值，CPU 執行起來連一聲 `SIGSEGV` 都不會吭，Fuzzer 就會把這筆已經踩中漏洞的黃金輸入當成正常案例放生。這就是為什麼灰箱 Fuzzing 一定要掛上 **Sanitizers**。

#### 1. AddressSanitizer（ASan）

ASan 的兩大支柱是**影子記憶體**（Shadow Memory）與**紅區投毒**（Redzone Poisoning）。在 64 位元 Linux 位址空間裡，每 **`8 bytes`** 連續的應用程式記憶體，都會固定映射到 **`1 byte`** 的影子記憶體，位址換算公式很單純：`(Addr >> 3) + ShadowOffset`（例如常見的固定偏移 `0x7fff8000`）。

這個影子 byte 記錄了對應那 `8 bytes` 的健康狀態：
- 值為 `0`：代表這 `8 bytes` 全部可以合法讀寫。
- 值為 `1..7`：代表只有前 `k` 個位元組能碰（用來標記未滿 `8 bytes` 對齊的物件尾巴）。
- 負值（最高位元為 `1`，例如 `0xfa` 代表堆積左紅區、`0xfb` 是堆積右紅區、`0xfd` 是已釋放的堆積隔離區、`0xf1` 到 `0xf3` 是堆疊邊界紅區）：代表嚴禁觸碰的毒化區。

編譯器會在每一次記憶體讀寫指令前塞進極短的檢查指令（同時攔截常見的 `libc` 記憶體操作函式）：把目標位址右移 3 位加上偏移量，去讀對應的 1-byte shadow 值；只要非零且超出合法長度，就呼叫 `__asan_report_loadN` 或 `__asan_report_storeN` 印出詳細堆疊並 `abort()`。

除此之外，ASan 還會替換系統的 `malloc` 與 `free`，在每個區塊前後包上紅區，並把 `free()` 掉的區塊放進容量有限的**隔離佇列**（Quarantine，預設約 `256 MiB`）延後重用。只要區塊還沒被擠出隔離佇列，任何 UAF 讀寫一摸到 `0xfd` 毒化區就會當場現形。

ASan 的代價是執行速度大約慢 **`2×`**（常見落在 `1.5×–2.5×`）、實體 RAM 消耗變為 **`2×–3×`**，而且啟動時會在虛擬位址空間預留高達幾十 TB 的影子空間。所以在那些預設會用 `RLIMIT_AS` 限制子行程虛擬記憶體上限的 `afl-fuzz` 版本或組態裡，跑 ASan 目標一定要加上 `-m none` 解除上限，否則子行程一啟動就會因為 `mmap` 失敗直接死掉。

#### 2. UndefinedBehaviorSanitizer（UBSan）

在 C/C++ 標準裡，有號整數溢位（Signed Integer Overflow）、位移超過型別寬度、未對齊指標解參考跟空指標解參考，統統叫做未定義行為（UB）。編譯器在開最佳化時，有權直接假設「UB 絕對不會發生」，甚至因此把工程師寫在後面的事後溢位檢查整段刪掉（例如認定有號整數 `x + 1 > x` 永遠為真）。

UBSan 會在編譯期針對這些危險運算塞入執行期斷言。它的速度非常快，CPU 開銷通常只多 **`1.05×–1.25×`**，也幾乎不多吃記憶體，非常適合跟 ASan 一起打開（`-fsanitize=address,undefined`；如果想連非標準 UB 但超常釀災的無號整數回繞一起抓，Clang 還可以多加 `-fsanitize=unsigned-integer-overflow`）。

不過 UBSan 有一個超容易踩的坑：**預設編譯出來的 UBSan 是可恢復模式（recoverable），撞到溢位時只會在 stderr 印一行 `runtime error:`，然後讓程式繼續往下跑**！這樣一來，Fuzzer 根本不知道剛剛出事了。

所以在編譯 Fuzzing 目標時，一定要加上 `-fno-sanitize-recover=all` 關掉恢復機制，並在執行期配上 `UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1`（或用 `AFL_USE_UBSAN=1` 自動帶入）。這會逼 runtime 在抓到錯誤的當下直接 `abort()` 送出 `SIGABRT`，Fuzzer 才會把它收進 Crash 資料夾。

#### 3. MemorySanitizer（MSan）

ASan 能管「這個位址能不能碰」，卻管不到「這塊合法記憶體在讀出來之前，到底有沒有先賦值初始化」。而在第 20 到 24 章裡，駭客用來打穿 ASLR 的資訊洩漏（Info Leak）漏洞，十之八九都是從忘了清零的堆疊陣列或 `struct` 對齊空洞漏出來的。

MSan 用了跟應用程式 **`1:1` 等比例**的影子記憶體，精確追蹤**每一個 bit** 有沒有被初始化；如果再加上 `-fsanitize-memory-track-origins=2` 追查未初始化的值是從哪裡配出來的，還會再多吃一份 origin shadow memory。

也因為這樣，MSan 的開銷是三者中最大的（大約慢 **`2.5×–3×` CPU**、多吃 **`2×–3×` RAM**），而且有兩條鐵律：第一，它跟 ASan **水火不容**，絕對不能同時開，必須另外編譯一顆獨立的 MSan 測試目標；第二，所有連結進來的 C/C++ 函式庫（連同 `libc++`、`zlib` 等）都必須全部用 MSan 重新編譯插樁。只要中間呼叫到任何一個沒插樁的外部函式並讀取它寫出來的緩衝區，MSan 因為沒看到外部函式去更新影子記憶體，就會瘋狂誤報未初始化讀取。

| Sanitizer | 抓什麼漏洞 | 影子記憶體比例 | 常見效能代價 | 實戰 Fuzzing 必設組態 |
|---|---|---|---|---|
| **ASan** | 堆疊／堆積／全域越界、UAF、Double Free | `8:1`（每 8B 映射 1B） | `~2×` CPU、`2×–3×` RAM | `afl-fuzz -m none`；可配 `ASAN_OPTIONS=abort_on_error=1:symbolize=0` 提速 |
| **UBSan** | 有號整數溢位、非法位移、空指標／未對齊解參考 | 無（純指令檢查） | `~1.1×–1.25×` CPU | 必加 `-fno-sanitize-recover=all` 或 `UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1` |
| **MSan** | 讀取未初始化的堆疊／堆積記憶體（Info Leak 根源） | `1:1`（位元級追蹤） | `~2.5×–3×` CPU、`2×–3×` RAM | 與 ASan 互斥；所有相依 C/C++ 函式庫都必須用 MSan 重編 |

---

### Rust 結構感知 Fuzzing：`cargo-fuzz` 與 `arbitrary`

當測試目標從純 C 換成 NexusPay 的 Rust + C FFI 解析模組 `libnexus-parse` 時，很多人會習慣性地把隨機位元組切片 `&[u8]` 直接往解析函式裡塞。但如果協定本身有嚴格的檔頭格式，這樣硬撞的效率非常差。

回想一下 `libnexus-parse` 的 TLV 格式：
- `0..2`：`magic` 固定是 `0x4e58`
- `2..4`：`msg_type`（例如 `0x0001` 認證、`0x0002` 對帳明細、`0x0003` 批次交易）
- `4..8`：`len`（`u32`，合法上限 `<= 65,536 bytes`）
- `8..8+len`：負載資料

要是只餵隨機位元組，光是 `2 bytes` 的 `magic` 就有 `65,536` 種組合，盲猜中 `0x4e58` 就得白白浪費一堆算力。就算靠字典檔（Dictionary）過了檔頭這關，只要變異時隨便改動幾個 byte 害 `len` 跟實際封包長度對不上，多封包串接（Batch TLV）狀態機在第一個封包就會直接報錯退回，永遠走不進第 2、第 3 個 TLV 互相影響的深層狀態。

在 Rust 生態系裡，**`cargo-fuzz`** 底層接的是 LLVM 的 **`libFuzzer`**。跟 AFL++ 不同，`libFuzzer` 天生就是在同一個行程裡跑 Persistent Loop 的引擎，採用 LLVM `SanitizerCoverage`（`inline-8bit-counters` 與 `pc-table`），會照實際的基本區塊與邊緣數量動態配置計數器陣列，不會撞上固定 `64 KiB` 位圖的雜湊碰撞天花板。

此外，它預設結合了 Rust nightly 的 `-Zsanitizer=address`，能直接抓出 `unsafe` 區塊與 C FFI 跨界時的記憶體損毀。

為了跨越結構化檔頭的阻礙，我們會搭配 **`arbitrary`** crate 一起用。它的核心元件 `Unstructured<'a>` 做法很聰明：把 `libFuzzer` 餵進來的那串隨機 `&[u8]` 當成一個**確定性的熵池**（Entropy Pool），照著你定義的型別一段一段切出位元組，組裝成結構永遠合法（或是受控半畸形）的 Rust 資料結構：

```rust
use arbitrary::{Arbitrary, Unstructured};

#[derive(Arbitrary, Debug)]
pub enum NexusMsgType {
    Auth = 0x0001,
    LedgerEntry = 0x0002,
    BatchSettlement = 0x0003,
    DebugExtension = 0x00ff,
}

#[derive(Debug)]
pub struct FuzzTlvFrame {
    pub magic: u16,
    pub msg_type: NexusMsgType,
    pub declared_len: u32,
    pub payload: Vec<u8>,
}

// 客製化 Arbitrary：大部分時候維持合法格式以深入狀態機，同時保留邊界異常（如 len 回繞）
impl<'a> Arbitrary<'a> for FuzzTlvFrame {
    fn arbitrary(u: &mut Unstructured<'a>) -> arbitrary::Result<Self> {
        // 95% 機率給合法 magic 0x4e58，留 5% 機率測非法 magic 分支
        let magic = if u.ratio(19, 20)? { 0x4e58 } else { u.arbitrary()? };
        let msg_type: NexusMsgType = u.arbitrary()?;
        let payload: Vec<u8> = u.arbitrary()?;

        // 80% 機率讓 declared_len 對齊 payload.len()，20% 機率塞入 0xFFFF_FFF8 等極端長度
        let declared_len = if u.ratio(4, 5)? {
            payload.len() as u32
        } else {
            *u.choose(&[0, 1, 65_536, 65_537, 0xFFFF_FFF8, 0xFFFF_FFFF])
                .unwrap_or(&0)
        };

        Ok(Self { magic, msg_type, declared_len, payload })
    }
}
```

這種「結構化序列化＋受控邊界注入」的混合寫法威力極大。因為 `libFuzzer` 變異的是底層充當熵池的 `&[u8]`，經過 `Unstructured` 轉譯之後，原本隨機的位元翻轉或片段拼接（Crossover），就自動升級成了「換一個 `msg_type`」、「把 `payload` 加長減短」或「多串一顆 TLV 封包」，再也不會因為歪了一個 bit 就整包作廢。

實務上最穩的做法是同時養兩支 Fuzz Target：一支直接拿原始 `&[u8]` 砸最外層的入口函式（抓表層截斷與解析錯誤），另一支用 `Arbitrary` 產生多封包串流（專攻深層狀態機與 FFI 邊界）。

---

### 語料庫工程與 Crash 根因分類：`afl-cmin`、`afl-tmin` 與去重

當 Fuzzer 跑出幾百萬次執行之後，真正決定工程效率的，是你怎麼整理「輸入語料庫」（Seed Corpus）與「滿坑滿谷的 Crash 檔案」。

首先是**初始種子與字典檔（Dictionary）的準備**。千萬別隨手塞幾百個幾十 KB 的大檔案進去，檔案越大，`havoc` 變異跑一輪的時間就越久，每個關鍵 byte 被翻轉的機率也會被稀釋。

最理想的初始語料庫，是由 **5 到 20 個極小（`< 1 KiB`）且涵蓋不同功能路徑的合法樣本**組成，例如各個 `msg_type`、空負載、單封包與雙封包串接各放一個。接著再寫一份小巧的字典檔（像 `nexus.dict`），把魔數跟協定常數列進去（例如 `magic="\x58\x4e"`、`max_len="\x00\x00\x01\x00"`），啟動時加上 `afl-fuzz -x nexus.dict`，讓 Fuzzer 直接把多位元組常數整塊塞進輸入流。

再來是 **`afl-cmin`（語料庫集合最小化）**。當你從線上撈了 `5,000` 個初始樣本，或把好幾台機器的 `queue/` 合併起來準備跑回歸時，裡面一定有大半樣本走過的路徑完全重疊。`afl-cmin` 會對整批語料庫收集邊緣位圖，再用貪婪集合覆蓋（Greedy Set Cover）演算法，在**保留 100% 相同總覆蓋率**的前提下，挑出檔案最小、跑得最快的一小群菁英子集。

至於 **`afl-tmin`（單一測試案例最小化）**，對付的則是單一檔案。Fuzzer 撞出來的 Crash 檔案（像 `id:000000,sig:06,...`）常夾雜好幾百 bytes 與漏洞無關的雜訊。`afl-tmin` 會針對**這一個檔案**做分塊歸零與位元組刪減（Delta Debugging 變體）：只要刪掉某段資料後程式仍觸發同樣的崩潰訊號就繼續砍（砍完記得比對 ASan stack trace 確認根因沒變）；若拿來縮減一般種子，則確保刪減前後的邊緣覆蓋雜湊不變。

最後是 **Crash 去重與根因分流**。同一個漏洞（例如第 25 章的 `len + 8` 回繞）在幾分鐘內就會噴出好幾百個 Crash 檔案。千萬別一個個手動打開看，應該直接拿 ASan 符號化後頂端的 3 到 5 層 Call Stack 算雜湊自動去重（可用 `afl-collect` 或 Python 腳本抓 `ERROR: AddressSanitizer:` 類別跟 `#0` 到 `#3` 的函式名稱）。

排修補與分析優先順序時，**Heap/Stack Out-of-Bounds Write** 跟 **Use-After-Free** 永遠排第一（直接對應第 22 到 24 章的控制流劫持與堆積利用）；**Out-of-Bounds Read / Uninitialized Read** 排第二（用來偷 ASLR 位址）；而單純讀寫 `0x0000_0000` 附近的空指標解參考，在使用者空間通常只能造成 DoS 重啟，優先序可以往後放。

---

## 故障模式與防禦

把灰箱 Fuzzing 搬進真實開發流程時，不管你是「跑了一整晚卻什麼都沒挖到」而產生安全假象，還是在修補漏洞時踩坑，最常遇到的就是下面這五種故障模式。

### 故障模式 1：狀態污染讓覆蓋率失真（Unstable Harness）

很多團隊為了衝出 `5,000+ exec/s` 的高吞吐量打開了 Persistent Mode，卻忘了在每次迴圈結束時把解析器裡的全域計數器、靜態快取、`errno` 或忘記釋放的堆積指標清乾淨。結果同一筆輸入在第 1 輪跑跟在第 100 輪跑走出完全不同的分支，不僅讓 `afl-fuzz` 畫面上的 `stability` 指標一路狂掉，還害 Fuzzer 把毫無意義的狀態波動當成新覆蓋率存進語料庫。

要解決這個問題，被測函式在每一輪迭代都必須做到**無狀態（Stateless per iteration）**——所有暫存物件跟全域旗標在離開 `__AFL_LOOP` 單輪迭代前都要徹底釋放並歸零。如果底層相依函式庫死綁著全域狀態實在改不動，那就只能調小 `__AFL_LOOP(1000)` 的次數，或開啟 `AFL_PERSISTENT_RECORD` 把導致崩潰的前置迭代序列一起錄下來，並把 `stability >= 98%` 當成驗收 Harness 的硬指標。

### 故障模式 2：位圖碰撞盲區與巨型種子拖垮吞吐量

有些工程師拿著預設的 `64 KiB` 經典 XOR 位圖，直接去測一個有 `10,000` 到 `32,000` 條邊的大型函式庫。照前面算過的均勻雜湊模型，整批邊緣裡平均會有 `7.26%` 到 `20.88%` 因為撞進同一個槽位而互相蓋掉；尤其當 Fuzzer 已經走過 `10,000` 條邊（約佔 `9,274` 個槽位）之後，下一條新邊有高達 `14.15%` 的機率直接掉進已佔用槽位裡，沒跨過新的命中次數級距就被直接忽視。

另一個常見慘劇則是把幾 MB 的大檔案丟進初始種子，害單次解析時間拉長到幾十毫秒，吞吐量從 `5,000 exec/s` 當場摔成 `50 exec/s`。正確做法是：編譯 C/C++ 目標時優先改用 `afl-clang-lto` 消滅雜湊碰撞；初始語料庫先用 `afl-cmin` 去重與 `afl-tmin` 瘦身，並透過 `-t` 鎖死單次執行逾時（如 `50 ms`），同時在 Harness 入口擋掉超過協定上限的超大輸入。

### 故障模式 3：Sanitizer 旗標漏配導致「踩中漏洞卻不崩潰」

明明開了 UBSan（甚至加了 `-fsanitize=unsigned-integer-overflow`），卻漏加 `-fno-sanitize-recover=all`，結果程式踩到整數溢位只印了一行警告就若無其事地繼續跑；或是在測 Rust FFI 時只跑預設的 `cargo test`，沒有替底層 C 靜態庫掛上 ASan，結果 C 函式裡的 `heap-buffer-overflow` 剛好寫進 `ptmalloc2` chunk 尾端的對齊填充區（例如 `0x20` chunk 沒用到的尾巴），半點 Crash 都沒冒出來。

要堵住這個盲區，請把 `-fsanitize=address,undefined -fno-sanitize-recover=all` 列為編譯 Fuzzing 目標的標準配備。如果是跨 Rust/C FFI 的專案，必須透過 `cc` crate 或建置腳本，確保 C 程式碼與 Rust 端（`-Zsanitizer=address`）共用同一份 ASan runtime，並且另外編一顆純 MSan 的目標專門抓未初始化讀取。

### 故障模式 4：修補只貼狗皮膏藥，且沒把 PoC 收進 CI 回歸

很多團隊替 `libnexus-parse` 寫了 20 個正常流程的單元測試就覺得萬無一失，從來沒把 Fuzzing Harness 放進 CI 或夜間排程；更糟的是，當 Fuzzer 真的抓出整數溢位 Crash 後，開發者只在最外層包一個 `try/catch` 或硬擋某個特定長度，根本沒去修底層的加法溢位（例如改用 `checked_add`）。

正確的防禦紀律是：每當 Fuzzer 挖出一顆最小化 PoC（經 `afl-tmin` 縮減後通常只有幾十個 bytes），就把它永久收編進單元測試的回歸語料庫（Regression Corpus）裡。每次發 PR 時，都在 CI 裡跑一段短時間的回歸驗證（例如用 `libFuzzer` 的 `-runs=10000` 或掛上第 31 章會介紹的 `ClusterFuzzLite`），並在原始碼裡用安全算術型別與明確的邊界檢查把病根徹底拔除。

### 故障模式 5：只拿隨機位元組撞大門，卡死在表層格式檢查

面對多層封包協定時，如果只用最陽春的隨機 `&[u8]` 去撞，Fuzzer 跑了一整晚覆蓋率還是死死卡在 `12%`（全部被檔頭的 `magic` 或校驗和擋在門外），團隊卻看面板上 `0 crashes` 就開心地宣布「測完了、沒漏洞」。

所以每次跑完 Fuzzing，一定要看覆蓋率報告（第 31 章會教你用 `llvm-cov` 逐行檢查）。只要發現測試全部卡在第一層檔頭驗證，就馬上補齊字典檔、把外層封包解析跟內層狀態機拆開來測，並替深層邏輯寫好 `Arbitrary` 結構感知 Harness。如果擋在前面的是 CRC32 或複雜校驗公式，光靠隨機變異絕對穿不過去，這時就要請出第 30 章的混合符號求解（Hybrid Fuzzing）來破關了。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

現在我們用本地 Linux 容器，親手替 NexusPay 的 `libnexus-parse`（同時涵蓋 C 語言版與 Rust 結構感知版）打造一套雙軌灰箱 Fuzzing 實驗環境：

1. 用 **AFL++（`afl-clang-fast` + ASan + UBSan）** 搭配 **Persistent Mode（`__AFL_LOOP`）**，編譯一個藏有多層 TLV 狀態機與整數回繞漏洞的 C 解析器，實測比較 `fork()` 與 Persistent Mode 的 `exec/s` 差距，並在幾秒鐘內把觸發 ASan / UBSan 的 Crash 挖出來。
2. 搭配字典檔、`afl-tmin` 與 `afl-cmin` 做語料庫去重與 PoC 瘦身，把原本幾百 bytes 的變異檔案濃縮成十幾個 bytes 的最小觸發輸入。
3. 用 **`cargo-fuzz` + `arbitrary`** 替 Rust 版 `libnexus-parse` 寫一支結構感知 Harness，輕鬆跨過 `magic == 0x4e58` 檢查，直接打穿深層多封包狀態機的切片越界 panic（若對應到 `unsafe` 或 FFI 裸指標寫入就是直接的記憶體越界 Crash）。

### 環境準備

請準備一個本地 Linux 容器（可以直接拉官方的 `aflplusplus/aflplusplus:latest` Docker 映像檔，或用 `ubuntu:24.04` 自己裝 `afl++`、`clang`、`llvm`、`rustup` 與 `cargo-fuzz`，零雲端費用）。

開跑前，確認容器或宿主機已經設好 `echo core > /proc/sys/kernel/core_pattern`；如果容器沒有權限改 `/proc/sys`，只要在跑 `afl-fuzz` 時加上環境變數 `AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1` 就不會被擋下來。

### 操作步驟

1. 建一個工作目錄 `nexus_fuzz_lab`，寫一支暗藏兩個典型漏洞的 `nexus_parser.c`：
   - **漏洞 A（深層整數回繞與堆積溢位）**：當 `magic == 0x4e58` 且 `type == 0x0002` 時，程式用 32 位元無號整數計算 `alloc_len = hdr.len + 8`。只要 `alloc_len <= 65536 + 8`（也就是 `65,544 bytes`），就呼叫 `malloc(alloc_len)` 並把後面剩下的負載拷貝進去（最多拷貝 `256 bytes`）。
   - **漏洞 B（多封包狀態機越界寫入）**：當連續收到兩顆 TLV 封包，第一顆 `type == 0x0001` 會先配置一塊 `16 bytes` 的暫存區；緊接著第二顆 `type == 0x0003` 且負載第一個 byte 為 `0x7f` 時，程式沒檢查索引上限，就直接往暫存區偏移位置寫入 `4 bytes`。
2. 分別編譯出 `fuzz_fork`（傳統從 `stdin` 讀入、不包 `__AFL_LOOP`）與 `fuzz_pers`（啟用 `__AFL_FUZZ_INIT()` 與 `__AFL_LOOP(10000)`），兩邊都加上 `-fsanitize=address,undefined -fno-sanitize-recover=all`。
3. 建好極簡初始種子跟 `nexus.dict` 字典檔，先看一眼 `fuzz_fork` 的 `exec/s`，再換 `fuzz_pers` 全速開跑，收割 `out_pers/default/crashes/` 裡冒出來的崩潰樣本。
4. 用 `afl-tmin` 把其中一顆 Crash 檔案縮到最小，再開 `ASAN_OPTIONS=symbolize=1` 單獨重播一次，看懂 Stack Trace 抓出的病根。
5. 接著建 `nexus_rust_fuzz` 目錄，跑 `cargo fuzz init` 並加入 `arbitrary` 相依套件，寫出結構化 TLV 串流的 Fuzz Target（需使用 Rust `nightly` 工具鏈，例如執行 `cargo +nightly fuzz run fuzz_tlv_stream`）。

### 外部靶場對照檢查點（pwn.college）

做完本地實驗後，推薦到 [pwn.college](https://pwn.college/) 的 **Software Exploitation / Program Security** 挑一題檔案或協定解析器的二進位挑戰。試著不要一開始就埋頭用肉眼逐行看反編譯碼，而是先寫個小巧的 Fuzzing Harness 配上 ASan 在本地快速撞出 Crash 輸入，再拿這顆熱騰騰的 PoC 進 GDB 看它死在哪一行。

實測時如果遇到下面兩個常見卡點，可以這樣秒解：
- 如果 `afl-fuzz` 一啟動就噴 `Fork server handshake failed` 或當場 OOM，八成是忘了加 `-m none`（記得 ASan 需要預留超大的虛擬記憶體空間）。
- 如果畫面跳出 `no instrumentation detected`，請檢查編譯時是不是真的有用 `afl-clang-fast`，還有程式是不是在進入 `__AFL_INIT()` 之前就因為參數檢查失敗而提前 `exit(0)` 了。

---

### 參考解答

#### 步驟 1：建立含多層 TLV 狀態機與 Persistent Harness 的 C 目標

先建好實驗資料夾：

```bash
mkdir -p nexus_fuzz_lab/seeds && cd nexus_fuzz_lab
```

接著寫入 `nexus_parser.c`。這裡我們用 `-DPERSISTENT_MODE` 巨集讓同一份原始碼可以切換編譯成傳統 `fork()` 版與 Persistent Mode 版，方便直接對照兩邊的速度差距：

```c
#include <stdint.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#ifdef PERSISTENT_MODE
__AFL_FUZZ_INIT();
#endif

typedef struct __attribute__((packed)) {
    uint16_t magic;
    uint16_t type;
    uint32_t len;
} tlv_hdr_t;

#define NEXUS_MAGIC 0x4e58
#define NEXUS_MAX_PAYLOAD 65536

static int process_stream(const uint8_t *data, size_t size) {
    // 每次迭代都重新歸零的區域狀態（確保 Persistent Mode 的 stability 穩定）
    uint8_t *session_scratch = NULL;
    size_t offset = 0;
    int pkt_count = 0;

    while (offset + sizeof(tlv_hdr_t) <= size && pkt_count < 8) {
        tlv_hdr_t hdr;
        memcpy(&hdr, data + offset, sizeof(tlv_hdr_t));
        if (hdr.magic != NEXUS_MAGIC) {
            break;
        }
        size_t remain = size - (offset + sizeof(tlv_hdr_t));
        const uint8_t *payload = data + offset + sizeof(tlv_hdr_t);

        if (hdr.type == 0x0001) {
            // 初始化 session 暫存緩衝區（16 bytes）
            if (!session_scratch) {
                session_scratch = (uint8_t *)calloc(1, 16);
            }
            size_t step = (hdr.len <= remain) ? hdr.len : remain;
            if (step > 16) step = 16;
            if (session_scratch && step > 0) {
                memcpy(session_scratch, payload, step);
            }
            offset += sizeof(tlv_hdr_t) + step;
        } else if (hdr.type == 0x0002) {
            // 漏洞 A：uint32_t 加法回繞（當 len = 0xFFFFFFF8 時 alloc_len = 0）
            uint32_t alloc_len = hdr.len + 8;
            if (alloc_len <= NEXUS_MAX_PAYLOAD + 8) {
                uint8_t *buf = (uint8_t *)malloc(alloc_len);
                if (buf && remain > 0) {
                    size_t copy_sz = remain > 256 ? 256 : remain;
                    memcpy(buf, payload, copy_sz); // alloc_len=0 時觸發 ASan heap-buffer-overflow
                }
                free(buf);
            }
            break;
        } else if (hdr.type == 0x0003) {
            // 漏洞 B：多封包狀態機觸發的寫入越界
            if (session_scratch && remain >= 2 && payload[0] == 0x7f) {
                uint8_t idx = payload[1]; // 忘了檢查 idx <= 12
                // 只要 idx >= 13，寫入 4 bytes 就會直接衝出 16-byte 的 session_scratch！
                uint32_t val = 0xdeadbeef;
                memcpy(session_scratch + idx, &val, sizeof(val));
            }
            offset += sizeof(tlv_hdr_t) + (remain > 4 ? 4 : remain);
        } else {
            break;
        }
        pkt_count++;
    }

    free(session_scratch);
    return 0;
}

int main(void) {
#ifdef PERSISTENT_MODE
#ifdef __AFL_HAVE_MANUAL_CONTROL
    __AFL_INIT();
#endif
    unsigned char *buf = __AFL_FUZZ_TESTCASE_BUF;
    while (__AFL_LOOP(10000)) {
        int len = __AFL_FUZZ_TESTCASE_LEN;
        if (len > 0) {
            process_stream(buf, (size_t)len);
        }
    }
#else
    uint8_t buf[8192];
    ssize_t n = read(STDIN_FILENO, buf, sizeof(buf));
    if (n > 0) {
        process_stream(buf, (size_t)n);
    }
#endif
    return 0;
}
```

#### 步驟 2：編譯對照目標、字典檔與初始種子

```bash
# 編譯標準 fork() 版與 Persistent Mode 版（同時打開 ASan + UBSan 並關閉恢復）
AFL_USE_ASAN=1 AFL_USE_UBSAN=1 afl-clang-fast -O2 -g \
  -fno-sanitize-recover=all nexus_parser.c -o fuzz_fork

AFL_USE_ASAN=1 AFL_USE_UBSAN=1 afl-clang-fast -O2 -g -DPERSISTENT_MODE \
  -fno-sanitize-recover=all nexus_parser.c -o fuzz_pers

# 建一顆極簡合法種子（magic=0x4e58, type=0x0001, len=4, payload="test"）
printf '\x58\x4e\x01\x00\x04\x00\x00\x00test' > seeds/seed_01.bin

# 寫一份字典檔（幫突變器快速湊出 magic、type 與回繞邊界值）
cat <<'EOF' > nexus.dict
magic="\x58\x4e"
type1="\x01\x00"
type2="\x02\x00"
type3="\x03\x00"
wrap_len="\xf8\xff\xff\xff"
trigger="\x7f"
EOF
```

#### 步驟 3：實測吞吐量差距並用 `afl-tmin` 縮小 Crash

```bash
# 1) 先用標準 fork() 跑 15 秒看基準速度（通常落在 150–400 exec/s 左右）
AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
  timeout 15s afl-fuzz -m none -i seeds -o out_fork -x nexus.dict -- ./fuzz_fork || true

# 2) 換上 Persistent Mode（單核輕鬆衝上 5,000+ exec/s，幾秒內就會在 crashes 資料夾看到戰果）
AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 \
  timeout 30s afl-fuzz -m none -i seeds -o out_pers -x nexus.dict -- ./fuzz_pers || true

# 3) 挑出第一顆 Crash 樣本，交給 afl-tmin 瘦身成最小 PoC
ls -lh out_pers/default/crashes/
CRASH_FILE=$(ls out_pers/default/crashes/id:* | head -n 1)
afl-tmin -m none -i "$CRASH_FILE" -o poc_min.bin -- ./fuzz_fork

# 4) 印出最小化 PoC 的十六進位內容，並餵給 fuzz_fork 看 ASan 診斷報告
xxd poc_min.bin
ASAN_OPTIONS=symbolize=1 ./fuzz_fork < poc_min.bin
```

跑完第 4 步，你會看到 `poc_min.bin` 被縮到只剩短短 `10–18 bytes`（例如觸發漏洞 A 的樣本只有 `9–12 bytes`，其中 `type=0x0002`，小端序的 `len` 欄位則落在 `f8 ff ff ff` 附近，也就是無號 32 位元整數 `0xfffffff8`），接著 ASan 會直接指認 `nexus_parser.c` 裡面的 `memcpy` 發生了 `ERROR: AddressSanitizer: heap-buffer-overflow`。如果你想順手練一下語料庫集合去重，可以把好幾個種子放進 `raw_corpus/`，執行 `afl-cmin -m none -i raw_corpus -o min_corpus -- ./fuzz_fork` 看看它怎麼剔除重複樣本。

#### 步驟 4：Rust `cargo-fuzz` + `arbitrary` 結構感知 Fuzzing

接著我們切到 Rust 環境，建立一個新的函式庫專案：

```bash
cargo new --lib nexus_rust_fuzz && cd nexus_rust_fuzz
```

在 `Cargo.toml` 裡加上 `arbitrary` 相依套件（實際跑的時候記得先裝好 `cargo install cargo-fuzz` 與 `rustup toolchain install nightly`）：

```toml
[package]
name = "nexus_rust_fuzz"
version = "0.1.0"
edition = "2021"

[dependencies]
arbitrary = { version = "1", features = ["derive"] }
```

把待測的 NexusPay 多封包狀態解析器寫進 `src/lib.rs`：

```rust
pub const NEXUS_MAGIC: u16 = 0x4e58;

pub fn parse_tlv_sequence(mut input: &[u8]) -> Result<Vec<u8>, &'static str> {
    let mut state_buf = [0u8; 16];
    let mut has_session = false;

    while input.len() >= 8 {
        let magic = u16::from_le_bytes([input[0], input[1]]);
        let msg_type = u16::from_le_bytes([input[2], input[3]]);
        let len = u32::from_le_bytes([input[4], input[5], input[6], input[7]]) as usize;
        if magic != NEXUS_MAGIC {
            return Err("bad magic");
        }
        let rest = &input[8..];
        if len > rest.len() {
            return Err("truncated");
        }
        let payload = &rest[..len];

        match msg_type {
            0x0001 => {
                has_session = true;
                let n = payload.len().min(16);
                state_buf[..n].copy_from_slice(&payload[..n]);
            }
            0x0003 if has_session && payload.len() >= 2 && payload[0] == 0x7f => {
                let idx = payload[1] as usize;
                // 沒檢查邊界就切 slice 寫入（在 Safe Rust 會觸發 Panic DoS；若換成 FFI 裸指標就是記憶體溢位）
                state_buf[idx..idx + 4].copy_from_slice(&[0xde, 0xad, 0xbe, 0xef]);
            }
            _ => {}
        }
        input = &rest[len..];
    }
    Ok(state_buf.to_vec())
}
```

初始化 `cargo fuzz` 並新增一支結構感知 Harness `fuzz_tlv_stream`：

```bash
cargo +nightly fuzz init
cargo +nightly fuzz add fuzz_tlv_stream
```

確認 `fuzz/Cargo.toml` 裡面有加上 `arbitrary = { version = "1", features = ["derive"] }`，然後把下面這段程式碼寫進 `fuzz/fuzz_targets/fuzz_tlv_stream.rs`：

```rust
#![no_main]
use arbitrary::Arbitrary;
use libfuzzer_sys::fuzz_target;
use nexus_rust_fuzz::{parse_tlv_sequence, NEXUS_MAGIC};

#[derive(Arbitrary, Debug)]
struct PacketOp {
    msg_type: u16,
    payload: Vec<u8>,
}

fuzz_target!(|ops: Vec<PacketOp>| {
    let mut wire = Vec::new();
    for op in ops.into_iter().take(6) {
        // 把結構化操作序列化成必定通過魔數與長度檢查的 TLV 封包（負載上限 <= 65,536 bytes）
        let t = match op.msg_type % 4 {
            0 => 0x0001u16,
            1 => 0x0002u16,
            2 => 0x0003u16,
            _ => op.msg_type,
        };
        let capped_len = op.payload.len().min(65_536);
        wire.extend_from_slice(&NEXUS_MAGIC.to_le_bytes());
        wire.extend_from_slice(&t.to_le_bytes());
        wire.extend_from_slice(&(capped_len as u32).to_le_bytes());
        wire.extend_from_slice(&op.payload[..capped_len]);
    }
    let _ = parse_tlv_sequence(&wire);
});
```

開跑結構感知 Fuzzing：

```bash
cargo +nightly fuzz run fuzz_tlv_stream -- -max_total_time=15
```

因為每一顆封包的 `magic` 跟 `len` 都已經由 Harness 自動對齊了，Fuzzer 完全不會在檔頭浪費時間，通常 **1 到 3 秒內**就會湊出 `[0x0001] -> [0x0003, payload=[0x7f, idx>=13]]` 的兩步狀態機組合，當場觸發切片越界 panic 並把 PoC 存進 `fuzz/artifacts/`（想再瘦身還可以接著跑 `cargo +nightly fuzz tmin`）。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別急著往下看答案，試著親手算算看並回答下面 4 個問題：

1. **AFL++ 邊緣雜湊與自迴圈計算**：假設某個解析函式裡有兩個基本區塊，編譯期配到的隨機 ID 分別是 `BB_X = 0x3600` 與 `BB_Y = 0x1500`。請算出控制流從 `BB_X → BB_Y`、反向從 `BB_Y → BB_X`，以及 `BB_X → BB_X` 自迴圈時，寫入 `trace_bits` 位圖的十六進位索引各是多少？接著，如果一套大型協定庫總共有 `16,000` 條可達邊緣，卻只用預設的 `64 KiB`（`65,536` 個槽位）位圖，平均大約會漏掉多少條邊緣？該換哪個編譯器模式才能徹底根治？
2. **吞吐量差距與虛擬記憶體限制**：某個二進位解碼器在傳統 `fork()` 模式下每秒只能跑 `400 exec/s`，改寫成 Persistent Mode 之後衝上 `5,000 exec/s`。如果上線前的安全檢查要求跑滿 `6,000,000`（`6 × 10^6`）次變異測試，兩種模式各要跑幾分鐘？另外，為什麼幫目標掛上 ASan 之後，跑 `afl-fuzz` 時常常得加上 `-m none`？
3. **Sanitizer 漏抓與誤報陷阱**：團隊用 `afl-clang-fast -fsanitize=address,undefined` 編譯了一支 C 解析器並跑了一整晚 AFL++。事後看覆蓋率報告，發現測試早就走過一行有號 32 位元整數乘法溢位的程式碼（但該數值沒有拿去配置記憶體，所以沒撞出後續越界），為什麼 `afl-fuzz` 面板上的 Crash 數卻還是 `0`？反過來說，如果這支程式還有一處「把沒初始化的堆疊 `struct` 緩衝區直接回傳給呼叫端」的資訊洩漏破口，ASan 抓得到嗎？換成對應的 Sanitizer 時，編譯第三方相依函式庫有什麼硬性規定？
4. **語料庫瘦身與單檔縮減的抉擇**：跑完兩天 Fuzzing 後，你手上有兩個目錄要整理：一邊是從四個 worker 節點收集來的 `3,500` 個 `queue/` 種子檔；另一邊是一顆長達 `2,400 bytes`、會觸發 `heap-use-after-free` 的 Crash 樣本。請問這兩邊要分別派 `afl-cmin` 還是 `afl-tmin` 上場？這兩支工具在砍檔案時，各自死守的「不變量」是什麼？

---

### 參考解答

1. **邊緣雜湊計算與碰撞損失**：
   - `BB_X → BB_Y`：`cur_loc = 0x1500`，`prev_loc >> 1 = 0x3600 >> 1 = 0x1b00`，索引為 `0x1500 ^ 0x1b00 = 0x0e00`。
   - `BB_Y → BB_X`：`cur_loc = 0x3600`，`prev_loc >> 1 = 0x1500 >> 1 = 0x0a80`，索引為 `0x3600 ^ 0x0a80 = 0x3c80`。
   - `BB_X → BB_X`（自迴圈）：`cur_loc = 0x3600`，`prev_loc >> 1 = 0x1b00`，索引為 `0x3600 ^ 0x1b00 = 0x2d00`（多虧了右移一位，不會退化成 `0x0000`）。
   - 當槽位數 `M = 65,536`、總邊緣數 `E = 16,000` 時，預期佔用的不重複槽位數約為 `65,536 × (1 - e^(-16000 / 65536)) ≈ 14,196.67` 個，也就是平均會有 **`16,000 - 14,196.67 ≈ 1,803` 條邊緣（約 `11.27%`）因為雜湊碰撞而互相覆蓋遺失**。根治方法是改用 **`afl-clang-lto`**（在連結期替每條邊分配連續無碰撞的索引）或用 `PCGUARD` 模式搭配調大 `AFL_MAP_SIZE`。
2. **執行時間換算與 `-m none` 的原因**：
   - 傳統 `fork()` 模式（`400 exec/s`）：`6,000,000 / 400 = 15,000 秒 = 250 分鐘`（`4 小時 10 分鐘`）。
   - Persistent Mode（`5,000 exec/s`）：`6,000,000 / 5,000 = 1,200 秒 = 20 分鐘`（整整快了 `12.5 倍`）。
   - **為什麼要加 `-m none`**：ASan 在行程一啟動時，就會呼叫 `mmap` 在 64 位元虛擬位址空間裡預約一大塊影子記憶體（動輒十幾 TB 的虛擬位址空間，雖然沒真正寫入前不會佔用實體 RAM）。在那些預設會對子行程設下 `RLIMIT_AS` 虛擬位址上限的 `afl-fuzz` 組態下，不加 `-m none` 解開限制，程式連影子空間都配不出來就會當場啟動失敗。
3. **UBSan 預設不中止與 MSan 的相依限制**：
   - **為什麼沒抓到有號溢位**：UBSan 預設編譯出來是「可恢復模式」（recoverable），踩到有號整數溢位時只會往 stderr 印一行錯誤訊息，然後繼續往下跑，不會送出任何崩潰訊號，Fuzzer 自然以為平安無事。編譯時必須加上 **`-fno-sanitize-recover=all`**，並在執行期設定 **`UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1`**（或編譯時加 `AFL_USE_UBSAN=1`），逼程式在踩中 UB 的瞬間呼叫 `abort()` 送出 `SIGABRT`，Fuzzer 才會把它記為 Crash。
   - **未初始化讀取**：ASan 只管記憶體位址合不合法，**管不到合法位址裡面的值有沒有先初始化**。要抓這種 Info Leak 破口，必須另外編譯一顆開啟 **MemorySanitizer（`-fsanitize=memory`）** 的執行檔（不能跟 ASan 同時開）；而且所有連結進來的第三方 C/C++ 函式庫也必須全部用 MSan 重新編譯插樁，否則只要讀到未插樁函式寫出的緩衝區，就會噴出一堆假警報。
4. **`afl-cmin` 與 `afl-tmin` 的分工與不變量**：
   - 對 **`3,500` 個 `queue/` 種子檔**要用 **`afl-cmin`**：它負責在「**整批語料庫合併起來的總邊緣覆蓋率一模一樣**」的不變量下，挑出檔案最小、跑最快的一小群檔案，把路徑重疊的冗餘種子全部砍掉。
   - 對 **`2,400 bytes` 的單一 Crash 檔案**要用 **`afl-tmin`**：它負責針對單一檔案做位元組刪減與歸零，死守的不變量是「**刪減後的檔案餵進目標程式，依然會觸發崩潰退出訊號**」（縮減完記得再核對一次 ASan stack trace，確認還是同一個 UAF 根因；如果拿它來縮減普通種子，不變量則是維持相同的邊緣覆蓋雜湊）。

---

## 延伸閱讀

1. **AFL++ 官方文件（Fuzzing in Depth / Persistent Mode / Sanitizers）**：完整收錄 `afl-clang-lto`、`__AFL_LOOP`、`__AFL_FUZZ_INIT`、`CMPLOG` 與多核平行化調校指南（https://aflplus.plus/docs/）。
2. **Google Sanitizers 設計論文與文件（ASan / MSan / UBSan）**：Konstantin Serebryany 等人詳述 `8:1` 影子記憶體映射、紅區投毒與 MSan 位元級追蹤開銷的原始設計（https://github.com/google/sanitizers/wiki）。
3. **Rust Fuzz Book（`cargo-fuzz` 與 `arbitrary` 官方指南）**：涵蓋結構感知 Fuzzing、`Unstructured` 設計模式、Fuzzing `unsafe` Rust 程式碼以及 `libFuzzer` 旗標調校（https://rust-fuzz.github.io/book/）。
4. **LLVM LibFuzzer & SanitizerCoverage 官方文件**：說明 `inline-8bit-counters`、內建字典推導、語料庫合併（`-merge=1`）與 Crash 去重機制（https://llvm.org/docs/LibFuzzer.html）。
