# 第 21 章：無原始碼逆向工程實戰

平常做程式碼審計，我們習慣打開 Git 倉庫，順著型別定義和函式呼叫一路往下追。但在真實的資安審計現場，掉到你桌上的往往不是整包原始碼，而是第三方金流商給的閉源 `.so` 動態函式庫、編譯後早就跑過 `strip -s` 拔掉除錯符號的 Node.js 原生外掛，或是跑在邊緣設備上的二進位代理程式。沒有原始碼、又沒有函式名稱，習慣看白箱原始碼的人當場就會卡住。

第 20 章我們已經摸透了 ELF 檔案結構、System V AMD64 ABI 呼叫慣例與 64 位元虛擬記憶體版圖。這一章我們就拿 **NexusPay** 系統裡被拔光除錯符號的發布版原生模組 `libnexus-parse.so` 開刀，帶你走一遍無原始碼逆向工程的完整實戰。

我們會依序拆解四個關鍵步驟：靠 ELF 拔不掉的殘留結構找回函式邊界、看懂 Ghidra 反編譯器把機器碼轉成 P-code 與類 C 程式碼的底層邏輯、從幾行組合語言反推 C 語言的 `struct` 欄位偏移與整數溢位，最後再進 GDB 用真實記憶體位址把靜態推論一錘定音。

---

## 從你已知的出發

為什麼廠商明明在發布前對 `libnexus-parse.so` 執行了 `strip -s`，把所有內部函式名稱、區域變數名稱和原始碼行號全都抹掉了，逆向工程師打開 Ghidra 還是能在半小時內把它的資料結構跟漏洞翻個底朝天？

因為 `strip -s` 拔掉的只有「給人看的名字標籤」（`.symtab` 與 DWARF `.debug_*` 區段），它**半點也動不到 CPU 與作業系統在執行期賴以維生的硬體跟 ABI 契約**。CPU 跑起來的時候，前 6 個參數照樣得乖乖放進 `rdi`、`rsi`、`rdx`、`rcx`、`r8`、`r9`；動態連結器（`ld-linux-x86-64.so.2`）要呼叫外部的 `malloc` 或 `memcpy` 時，照樣得靠動態符號表（`.dynsym`）跟 `.plt` 跳板按名索驥。

同時，編譯器為了讓程式崩潰或拋出例外時能展開呼叫堆疊（Stack Unwinding），更在 `.eh_frame` 區段裡把每一個內部函式的起點跟長度記了下來。所謂無原始碼逆向，說穿了就是順著這些藏不住的骨架，把原本的資料結構跟控制流一步步拼回來。

---

## 機制與推導

### 攻擊者目標與實質影響

不管是安全研究員還是攻擊者，花時間對沒有原始碼的二進位檔做逆向工程，要拿下的實質戰果主要有三個：

第一是**挖出閉源原生模組裡的 0-day 記憶體漏洞**。很多商用 SDK、Node.js 的 `.node` 外掛或高速封包解析器都不公開原始碼，開發者常以為「別人看不到 code 就很安全」。透過逆向還原出結構體的欄位偏移跟長度計算式，就能精準抓出裡面的整數溢位、堆疊緩衝區溢位或 Use-After-Free（UAF），算出觸發漏洞的確切位元組，為第 22 到 24 章的控制流與堆積攻防鋪路。

第二是**揪出藏在二進位檔裡的隱藏除錯指令與寫死金鑰**。工程師在開發原生模組時，很常為了方便測試，在解析器裡留一個沒寫進公開文件的特殊 `type` 或除錯後門（就像我們待會要在 `libnexus-parse.so` 裡抓到的隱藏 opcode `0x0099`），或是把加密金鑰直接寫死在 `.rodata` 區段裡。逆向分析能直接把這些隱藏分支攤在陽光下。

第三是**幫自動化 Fuzzing 畫出通關地圖**。如果對著一個私有二進位協定盲目亂丟隨機位元組，Fuzzer 有 99.9% 的測試都會卡在第一關的魔術數字（像 `magic == 0x584e`）或長度檢查。先用逆向把檔頭各欄位的偏移跟分支條件摸清楚，研究員才能寫出真正打得進深層邏輯的結構感知 Fuzzing Harness（銜接第 29 章）。

---

### Stripped Binary 的真相：哪些被拔了，哪些根本拔不掉？

很多團隊把跑過 `strip -s` 的二進位檔當成銅牆鐵壁的黑箱。但如果你用 `readelf -S` 去掃描一個 stripped 後的 `.so` 或執行檔，就會發現 ELF 格式為了讓作業系統能載入、能動態連結、能處理例外，強制留下了滿滿的破案線索：

| ELF 區段／表格 | `strip -s` 之後還在嗎？ | 逆向工程師能從裡面挖出什麼寶藏 |
|---|---|---|
| `.symtab` / `.strtab` | 被刪光了 | 原本放著所有內部 `static` 函式跟全域變數的名字 |
| `.debug_*`（DWARF 除錯資訊） | 被刪光了 | 原本放著完整的 C `struct` 型別定義、區域變數名與原始碼行號 |
| `.dynsym` / `.dynstr` | **完整保留** | 所有對外匯出的 API 名稱，以及所有從外部匯入的 `libc` 危險函式名稱 |
| `.plt` / `.got.plt` | **完整保留** | 外部函式的呼叫跳板，一查就知道哪裡呼叫了 `malloc`、`memcpy`、`system` |
| `.eh_frame` / `.eh_frame_hdr` | **完整保留** | 堆疊展開表，精準記錄了幾乎每一個內部無名函式的起始位址與位元組長度 |
| `.rodata` | **完整保留** | 唯讀常數區，躺著所有錯誤日誌字串、演算法魔術常數與 `switch` 跳躍表 |
| `.init_array` / `.fini_array` | **完整保留** | 模組載入與卸載時自動執行的初始化函式指標清單 |

先看 `.dynsym` 與 `.plt`。對動態連結的共享函式庫（`.so`）來說，只要編譯時沒開全域符號隱藏，所有對外提供服務的 API 名字都得乖乖留在 `.dynsym` 裡，否則外面的程式根本沒辦法呼叫它。

反過來看，只要這支程式透過 `.plt`（或開啟 Intel CET 後的 `.plt.sec`）去呼叫外部 `libc` 的 `malloc`、`realloc`、`memcpy`、`free`，這些匯入函式的名字與重定位綁定（`.rela.plt`）也一樣一個字都不能刪。在絕大多數沒被編譯器內聯展開的一般呼叫裡，`strip -s` 完全藏不住程式在哪些地方呼叫了危險的外部 Sink。

再看更少人注意到的 **`.eh_frame`** 區段。為了支援 C++ 例外處理，或讓除錯器在省略框架指標（`-fomit-frame-pointer`）時還能正確展開呼叫堆疊，現代 GCC 與 Clang 預設都會開啟 `-fasynchronous-unwind-tables`。

這個選項會幫程式裡的每一個函式產生一筆 **FDE**（Frame Description Entry）紀錄，裡頭白紙黑字寫著函式在 `.text` 的起始位址與位元組長度。這就是為什麼即便 `.symtab` 被拔得乾乾淨淨，Ghidra 一載入二進位檔，還是能靠 `.eh_frame` 瞬間切出九成五以上的內部函式邊界，只是暫時幫它們取名叫 `FUN_00101420` 而已。

---

### Ghidra 反編譯引擎：機器碼是怎麼變回 C 語言的？

如果只用 `objdump -d` 看純組合語言，你的大腦得自己記住現在 `eax` 是 32 位元還是 64 位元、上一行的減法有沒有影響進位旗標 `CF`、堆疊上的 `[rbp-0x18]` 到底裝了什麼。Ghidra 反編譯器（Decompiler）之所以強大，是因為它在幕後跑了一套像編譯器反向工程一樣的四階段管線，幫你把散落的機器指令重新摺疊成有 `if / else`、有迴圈、有結構體欄位的類 C 虛擬碼：

```text
  x86_64 機器碼 (.text)
         │
         ▼  [1. SLEIGH 指令語意翻譯]
    Raw P-code (把每條複雜指令拆成 register / ram / unique / const 微操作)
         │
         ▼  [2. 切分基本區塊並建立控制流圖 (CFG)]
    P-code CFG
         │
         ▼  [3. SSA 靜態單賦值轉換]
    SSA P-code (加入 MULTIEQUAL phi 節點 + INDIRECT 間接影響節點)
         │
         ▼  [4. 死碼消除、常數摺疊、型別傳播、支配樹結構化]
  類 C 虛擬碼 (還原出 if / while / switch 與 ctx->count 欄位存取)
```

看懂這四步，你才知道什麼時候該相信 Ghidra 的反編譯結果、什麼時候該切回反組譯視窗看原始指令：

#### 第一步：用 SLEIGH 把指令拆成無關硬體的 Raw P-code

x86_64 的指令有非常多「沒寫在字面上」的隱藏副作用。舉個最常在漏洞裡出現的例子：短短一行 `shl eax, 3`（把 32 位元的 `eax` 左移 3 位元，相當於乘以 8）。它除了算移位之外，在硬體上還會同時改寫進位旗標 `CF`、零旗標 `ZF`、符號旗標 `SF` 與同位旗標 `PF`，而且依照 x86_64 的鐵律，**任何對 32 位元暫存器 `eax` 的寫入，都會自動把 64 位元 `rax` 的高 32 位元全部清為零**！

如果反編譯器要針對 x86、ARM、RISC-V 各自寫一套分析引擎，早就累死了。所以 Ghidra 設計了一套叫 **SLEIGH** 的處理器描述語言，先把每條機器指令翻譯成統一的微操作序列，叫做 **P-code**。P-code 只在幾個乾淨的位址空間上做事：`ram` 代表虛擬記憶體、`register` 代表 CPU 暫存器、`const` 代表常數、`unique` 代表單條指令拆解時借用的暫存變數，而 `stack` 則代表相對於函式入口 `RSP` 的堆疊局部空間。

比方說，當 Ghidra 看到這兩行指令：
```nasm
mov eax, dword ptr [rdi+0x4]
shl eax, 3
```
它在內部其實會拆成下面這樣一串精確的 Raw P-code 微操作：
1. `INT_ADD`：先算記憶體位址 `unique_1 = RDI + 0x4`。
2. `LOAD`：從記憶體讀出 4 個 bytes 放進 `EAX = *(ram, unique_1)`。
3. `INT_ZEXT`：執行零擴充 `RAX = zext(EAX)`，把 `RAX` 的高 32 位元清成零。
4. 接著處理 `shl eax, 3`：先算出移出去的位元會不會改動進位旗標 `CF`，再跑 `INT_LEFT` 算出 32 位元移位結果 `EAX = EAX << 3`，接著根據結果更新 `ZF`（是不是變成 0）、`SF`（最高位是不是 1）等狀態旗標，最後再補一次 `INT_ZEXT` 把 `RAX` 的高 32 位元清零。

#### 第二步與第三步：切成控制流圖（CFG）並轉成 SSA 靜態單賦值

拆完 P-code 後，Ghidra 會順著條件跳躍跟無條件跳躍指令，把程式碼切成一塊塊基本區塊（Basic Block），連成控制流圖（CFG）。接著就是最關鍵的一步：把所有變數轉成 **SSA**（Static Single Assignment，靜態單賦值）形式。

在 SSA 的世界裡，每一個變數名這輩子只能被賦值一次。比方說迴圈外面的 `EAX` 叫 `EAX_1`，經過移位運算後的 `EAX` 就改名叫 `EAX_2`。這樣一來，每個數值是從哪裡生出來的、又流向了哪裡（Def-Use 鏈），一眼就能追到底。

那如果遇到 `if / else` 兩條路匯合回同一個地方，變數的值到底該聽誰的？這時 Ghidra 會在匯合點插入一個 **`MULTIEQUAL`** 節點（也就是編譯器理論裡的 $\phi$ 節點），標記「這個變數的值，取決於你是從哪一條分支走過來的」。另外，如果中間遇到了外部函式呼叫（像 `call malloc`）或是透過不明指標寫入記憶體，Ghidra 沒辦法百分之百確定這步操作會不會偷改到某塊全域記憶體或暫存器，就會插入一個 **`INDIRECT`** 節點，提醒後面的最佳化引擎：「這裡可能有間接修改或別名（Aliasing）影響，別亂做跨呼叫的假設！」

#### 第四步：消掉死碼、摺疊算式與何時別全信反編譯器

轉成 SSA 之後，前面拆出來那一堆煩人的 `CF`、`ZF`、`SF` 旗標運算怎麼辦？很簡單，Ghidra 順著 SSA 資料流往後看：如果某條指令算出來的旗標，在被下一條指令覆蓋之前，**根本沒有被任何條件跳躍（`CBRANCH`）、條件搬移（`CMOVcc`）或帶進位運算（`ADC`/`SBB`）拿去用**，這條旗標計算就是不折不扣的死碼（Dead Code），整行直接刪掉！接著再把暫存器搬移摺疊成單一算式，並用支配樹（Dominator Tree）分析把跳來跳去的分支還原成結構化的 `if / else`、`while` 與 `switch`。

但這裡要請你牢記一條實戰鐵律：**反編譯虛擬碼是拿來幫你快速找路的，到了檢查漏洞邊界的那一刻，一定要切回反組譯視窗看真正的機器指令！**

為什麼？因為 Ghidra 的類 C 畫面，高度依賴它「猜出來的變數型別與參數個數」。如果一個 4-byte 的變數還沒被你標上正確型別，Ghidra 可能先把它猜成有號的 `int` 或型別未定的 `undefined4`。這時畫面可能會跑出奇怪的 `CONCAT44`、莫名其妙的指標強制轉型，甚至把一條在 32 位元 `eax` 上會發生無號溢位回繞的左移運算，包裝得像是安全的 64 位元算式一樣。

---

### 遇到靜態連結怎麼辦？函式指紋（FLIRT / FIDB）與常數錨定

前面說過，動態連結的 `.so` 或執行檔因為有 `.dynsym` 和 `.plt`，找 `malloc` 或 `memcpy` 易如反掌。但如果今天拿到的是用 `gcc -static` 靜態連結的韌體、把整包標準庫都編進同一個檔案的 Go/Rust 執行檔，或是直接把 OpenSSL / zlib 原始碼包進專案裡編譯的模組，打開一看，`.plt` 幾乎是空的，`.text` 裡面躺著兩千多個叫 `FUN_0040xxxx` 的無名函式！

如果不先把裡面的標準庫函式認出來，你可能會花整個下午去逆向一個無名函式，最後才崩潰地發現自己只是在看 `libc` 的 `vsnprintf` 或 `SHA256_Update`。為了不浪費這種冤枉時間，逆向工具靠的是下面三招：

第一招是**遞迴下降反組譯**（Recursive Descent）。傳統的 `objdump -d` 用的是笨拙的**線性掃描**（Linear Sweep），從 `.text` 第一個 byte 一路硬解碼到底；萬一編譯器在函式中間夾了一張唯讀跳躍表或填補位元組，後面的指令就會瞬間解碼錯位。Ghidra 跟 IDA 則是用遞迴下降：從程式入口點（`_start`）、`.dynsym` 匯出函式、`.init_array` 跟 `.eh_frame` 的 FDE 清單出發，只順著真正會走到的 `call` 與跳躍目標一路展開，把資料跟指令分得清清楚楚。

第二招是**標準庫機器碼指紋比對**（IDA 的 **FLIRT** 與 Ghidra 的 **Function ID / FIDB**）。既然標準庫的 `memcpy` 或 `deflate` 也是編譯出來的，它們的機器碼長相就有跡可循。
- IDA 的 **FLIRT** 會抓每個標準庫函式開頭 32 bytes 的機器碼，把裡面會隨連結位址變動的重定位偏移遮罩成萬用字元（`..`），建成一棵前綴樹（Trie），再搭配剩餘指令的 CRC16 校驗碼與函式總長度快速比對。
- Ghidra 的 **FIDB**（`.fidbf` 簽章庫）則會把標準庫每個函式的指令流正規化（一樣遮罩掉常數位址與重定位偏移），算出整個函式的 **Full Hash**，以及結合它呼叫了哪些子函式的 **Specific Hash**。就算編譯器在函式開頭多塞了一條 Intel CET 的 `endbr64` 指令，FIDB 依然能認出「這就是標準庫的函式」並自動幫你把名字標回去。

第三招是當編譯最佳化讓簽章庫都認不出來時的殺手鐧：**字串與魔術常數錨定法**。哪怕函式名字全沒了，程式總得印錯誤訊息、總得用標準演算法的常數吧？只要去 `.rodata` 搜尋像 `"invalid tlv length"`、原始碼檔名 `__FILE__`，或是看到 `0xedb88320`（CRC32 的多項式常數）、`0x6a09e667`（SHA-256 的初始雜湊常數），對著那個常數按一下交叉引用（XREF），一秒就能認出引用它的無名函式到底是幹嘛的。

---

### 從組合語言反推 C `struct` 偏移、對齊與陣列步長

進到業務函式內部後，逆向工程最核心的手藝，就是把畫面上散落的 `[rdi + 0x4]`、`[rbx + rcx*8 + 0x10]`，還原回當初工程師寫在 `.h` 標頭檔裡的 C `struct`。

因為 x86_64 System V ABI 嚴格遵守**自然對齊**（Natural Alignment——也就是 `2-byte` 欄位必須放在 `2` 的倍數偏移、`4-byte` 放在 `4` 的倍數、`8-byte` 放在 `8` 的倍數），每種組合語言讀寫指令都在大聲告訴你那個欄位的型別：

| 你在反組譯看到的指令寫法 | 讀寫寬度 | 最常對應的 C 語言型別 | 自然對齊要求 | 看到它通常代表什麼欄位 |
|---|---|---|---|---|
| `byte ptr [reg+disp]`（搭 `movzx`） | `1 byte` | `uint8_t` / `bool` / `char` | 任何偏移皆可 | 布林旗標、單字元、狀態碼 |
| `word ptr [reg+disp]`（搭 `movzx`） | `2 bytes` | `uint16_t` | `2` 的倍數（`+0x0`, `+0x2`...） | 封包魔術數字 `magic`、opcode、Port |
| `word ptr [reg+disp]`（搭 `movsx`） | `2 bytes` | `int16_t` | `2` 的倍數 | 有號短整數、可能為負的錯誤碼 |
| `dword ptr [reg+disp]` | `4 bytes` | `uint32_t` / `int32_t` | `4` 的倍數（`+0x0`, `+0x4`, `+0x8`...） | TLV 長度 `len`、項目計數 `count` |
| `qword ptr [reg+disp]` | `8 bytes` | `void *` / `uint64_t` / `size_t` | `8` 的倍數（`+0x0`, `+0x8`, `+0x10`...） | `malloc` 回傳的緩衝區指標、函式指標 |

在拼湊結構體的時候，只要抓住三個小訣竅就能百發百中：

第一，**看偏移跳號抓出 Padding 空隙**。如果函式先讀了 `byte ptr [rdi+0x0]`（1 byte），下一個欄位卻直接跳去讀 `dword ptr [rdi+0x4]`（4 bytes），中間空出來的 `+0x1` 到 `+0x3` 那三個位元組通常不是你漏看了欄位，而是編譯器為了讓 4-byte 整數對齊 `+0x4` 自動塞進去的 Padding。

第二，**看乘法與移位抓出陣列的元素大小**。x86_64 支援 `[base + index*scale + disp]` 定址，或是先對索引做移位再拿去 `malloc`。如果你看到 `shl eax, 3`（左移 3 位，等於乘以 $2^3 = 8$）或是 `[rbx + rcx*8]`，就代表這是一個「每筆元素佔 `8 bytes`」的陣列（例如 `uint64_t` 陣列或指標陣列）；如果陣列元素是一個 `24 bytes` 的小結構體（不是 2 的次方），編譯器則常會寫成 `lea rax, [rcx + rcx*2]; shl rax, 3`（也就是先算 $3 \times \text{index}$，再乘以 $8$，合起來正好是 $24 \times \text{index}$）。

第三，**從擴充與跳躍指令抓出「有號 vs 無號」漏洞**。看到 `movzx`（Zero-Extend 零擴充）搭配 `ja` / `jb`（Above / Below），代表程式把它當成**無號整數**（Unsigned）；但如果看到 `movsx` / `movsxd`（Sign-Extend 符號擴充）或是條件跳躍用了 `jg` / `jl`（Greater / Less），就代表程式把它當成**有號整數**（Signed）！在審計封包長度檢查時，只要看到長度欄位居然用 `jg` / `jle` 來比大小，眼睛就要亮起來——因為只要傳一個最高位元為 `1` 的負數進去，就能輕鬆繞過上限檢查！

---

### Worked Example：從 18 行組合語言還原 `libnexus-parse.so` 結構體與 32 位元乘法溢位

現在我們直接上場實戰。假設你在審計 stripped 版的 `libnexus-parse.so` 時，從 `.plt` 的 `malloc@plt` 查交叉引用（XREF），追進了一個沒有名字的內部函式 `FUN_00101420`。回想一下全書基準常數：`libnexus-parse` 的 TLV 檔頭固定是 `8 bytes`（`magic: 2B`、`type: 2B`、`len: 4B` 無號 `uint32`），合法 payload 上限是 `65,536 bytes`（`64 KiB`）。

下面是你在反組譯視窗看到的 `FUN_00101420` 開頭 18 行 x86_64 組合語言（Intel 語法）：

```nasm
01: push   rbp
02: mov    rbp, rsp
03: push   rbx
04: sub    rsp, 0x8
05: mov    rbx, rdi
06: movzx  eax, word ptr [rdi]
07: cmp    ax, 0x584e
08: jne    0x101480
09: movzx  edx, word ptr [rdi+0x2]
10: cmp    dx, 0x0099
11: je     0x101490
12: mov    eax, dword ptr [rdi+0x4]
13: test   eax, eax
14: jz     0x101480
15: shl    eax, 3
16: mov    edi, eax
17: call   malloc@plt
18: mov    qword ptr [rbx+0x8], rax
```

不用通靈也不用猜，我們一行一行照著 System V ABI 跟位元算術，把這 18 行藏著的結構體、隱藏後門跟整數溢位漏洞徹底扒開來：

```text
=== Worked Example: FUN_00101420 無原始碼結構還原與 32 位元整數溢位精算 ===

[第一步：核對堆疊對齊與暫存器交接 (第 01–05 行)]
- 呼叫端執行 call 0x101420 壓入 8-byte Saved RIP 後，踏入第 01 行時 RSP % 16 == 8。
- 第 01 行 push rbp (-8B)、第 03 行 push rbx (-8B)、第 04 行 sub rsp, 0x8 (-8B)：
  總共將 RSP 往下移了 24 bytes (0x18)。因为 (8 + 24) = 32 是 16 的倍數，
  確保第 17 行執行 call malloc@plt 前完全符合 RSP % 16 == 0 的 ABI 鐵律！
- 第 05 行 mov rbx, rdi：把第 1 個參數 rdi (指向傳入結構體的指標) 備份到 Callee-saved 暫存器 rbx。
  為什麼要備份？因為第 16 行準備呼叫 malloc 時會把配置大小寫進 edi (覆蓋掉 rdi)，
  等第 17 行 malloc 回來後，第 18 行就能直接拿安全保存的 rbx 繼續存取同一個結構體！

[第二步：從記憶體運算元還原 16-byte C 結構體 (第 06–18 行)]
偏移   寬度   對應組合語言指令                推導 C 型別與名稱     欄位意義與逆向證據
-----+------+-------------------------------+---------------------+-----------------------------------------
+0x00  2 B    movzx eax, word ptr [rdi]       uint16_t magic        比對 cmp ax, 0x584e (小端序記憶體 4e 58 = "NX")
+0x02  2 B    movzx edx, word ptr [rdi+0x2]   uint16_t type         緊接 +0x02 無空隙；cmp dx, 0x0099 抓出隱藏分支!
+0x04  4 B    mov eax, dword ptr [rdi+0x4]    uint32_t count        對齊 4B 無空隙；把 TLV 4B 長度當成 8B 項目個數
+0x08  8 B    mov qword ptr [rbx+0x8], rax    uint64_t *items       對齊 8B 無空隙；用來接住 malloc 回傳的堆積指標
------------------------------------------------------------------------------------------------------------
結構體最小已知尺寸 = 2 + 2 + 4 + 8 = 16 bytes (0x10)。前 8 bytes 正好對應 8-byte TLV 檔頭。

[第三步：精算第 12–17 行的 32 位元無號乘法溢位與 ptmalloc2 配置落差]
1. 為什麼會溢位：
   第 12 行把 [rdi+0x4] 讀進 32 位元暫存器 eax，第 15 行直接對 32 位元的 eax 執行 shl eax, 3 (乘以 8)。
   在 x86_64 上，對 32 位元 eax 左移 3 位元，算的是 (count × 8) mod 2^32 (即 mod 4,294,967,296)，
   被推到第 32..34 位元的最高 3 個 bits 會直接掉出 eax 蒸發掉！
   第 16 行 mov edi, eax 只是把已經被截斷的 32 位元結果零擴充成 64 位元送給 malloc，完全救不回來。

2. 漏掉的規格上限：
   依全書基準，libnexus-parse 合法 payload 上限為 65,536 bytes (64 KiB)。
   既然每筆項目佔 8 bytes (shl eax, 3)，合法的 count 上限應該是 65,536 / 8 = 8,192 (0x2000)。
   但第 13–14 行 (test eax, eax; jz) 只檢查了 count != 0，完全沒檢查 count <= 0x2000！

3. 觸發 32 位元溢位的精確臨界值與兩種致命輸入：
   只要 count × 8 >= 2^32，就會發生 32 位元回繞。臨界點為 count >= 2^29 = 0x2000_0000 (536,870,912)。

   - 測試值 A (繞過非零檢查觸發 malloc(0))：傳入 count = 0x2000_0000 (536,870,912)
     * 第 13 行檢查：0x2000_0000 != 0 (順利通過非零檢查!)
     * 第 15 行左移：(536,870,912 × 8) mod 2^32 = 4,294,967,296 mod 4,294,967,296 = 0
     * 第 17 行結果：呼叫 malloc(0)。在 glibc ptmalloc2 中，malloc(0) 不會回傳 NULL，
       而是回傳一個最小可用堆積 chunk (含標頭總大小 0x20 = 32 bytes)。

   - 測試值 B (只配 8 bytes 卻準備寫入 4 GiB)：傳入 count = 0x2000_0001 (536,870,913)
     * 第 15 行左移：(536,870,913 × 8) mod 2^32 = 4,294,967,304 mod 4,294,967,296 = 8 (0x0000_0008)
     * 第 17 行結果：只向系統呼叫了 malloc(8) (實際同樣拿到一塊 32-byte 的最小 chunk)！
     * 後續災難：結構體 [rbx+0x4] 裡記的 count 依然是 536,870,913。後面負責填資料的迴圈只要照著
       ctx->count 往 ctx->items 寫入，就會對一塊 32-byte 的小空間硬塞 4,294,967,304 bytes (約 4 GiB)，
       當場把整個堆積寫穿！
```

把上面三步推導合起來，這 18 行沒有半個符號的機器碼，在我們眼裡就還原成了下面這段一清二楚的 C 語言程式碼：

```c
struct nexus_tlv_ctx {
    uint16_t magic;   /* +0x00: 期望 0x584e ("NX") */
    uint16_t type;    /* +0x02: 若為 0x0099 則跳往隱藏除錯分支 */
    uint32_t count;   /* +0x04: 8-byte 紀錄的筆數 (漏檢 <= 8192 上限!) */
    uint64_t *items;  /* +0x08: 指向動態配置的陣列 */
};

int FUN_00101420(struct nexus_tlv_ctx *ctx) {
    if (ctx->magic != 0x584e) return -1;
    if (ctx->type == 0x0099)  return handle_hidden_debug_opcode(ctx); /* 0x101490 */
    if (ctx->count == 0)      return -1;

    /* 致命破口：在 32 位元 uint32_t 上直接乘以 8，>= 0x20000000 即溢位回繞！ */
    uint32_t byte_len = ctx->count * 8U;
    ctx->items = (uint64_t *)malloc((size_t)byte_len);
    ...
}
```

你在 Ghidra 的 Data Type Manager 裡照這張表建好 `nexus_tlv_ctx` 結構，然後對著反編譯視窗的第一個參數 `param_1` 按右鍵選 `Retype Variable` 改成 `nexus_tlv_ctx *`，原本滿畫面的 `*(uint *)(param_1 + 4)` 就會瞬間變成乾淨好讀的 `ctx->count`！

---

### 從 Sink 倒追回 Source（XREF 逆向審計法）與 GDB 動態對位

面對一個有幾百個無名函式的 `.so` 檔，千萬別從第一個函式開始傻傻往下讀。實戰找洞用的是跟第 2 章一模一樣的 **Sink-to-Source 倒追法**：

第一步，直接打開 Ghidra 左側的 `Symbol Tree -> Imports`，鎖定最容易出事的記憶體配置與拷貝函式（`malloc`、`calloc`、`realloc`、`memcpy`、`memmove`、`strcpy`、`snprintf`）還有命令執行函式（`system`、`execve`、`popen`），按右鍵看它們的**交叉引用**（XREF），把所有呼叫點全部列出來。

第二步，站在呼叫點往回追參數（Backward Slice）。比方說你看到一處 `call memcpy@plt`，照 System V ABI，第 1 個參數 `rdi` 是目的緩衝區、第 2 個參數 `rsi` 是來源、第 3 個參數 `rdx` 是要拷貝的位元組長度。你就在 Ghidra 反編譯視窗點一下代表第 3 個參數的那個長度變數，開啟 `Highlight -> Backward Slice` 往上追：
- 這個長度是不是從外部傳進來的封包欄位算出來的？
- 它在進 `memcpy` 之前，有沒有先跟目的緩衝區的大小比過？比大小的時候用的是無號比較（`ja`/`jb`）還是誤用了有號比較（`jg`/`jl`）？
- 算配置大小的時候，有沒有像剛剛 Worked Example 那樣先在 32 位元暫存器裡溢位了一輪？

#### 為什麼靜態看完一定要進 GDB 動態驗證？怎麼換算 ASLR 位址？

光看 Ghidra 靜態反編譯，有時會遇到三個死角：一是程式用**函式指標或 C++ 虛擬表（vtable）做間接呼叫**（`call rax` 或 `call qword ptr [rbx+0x18]`），靜態根本看不出它跳去哪裡；二是編譯器開了 `-O2` 之後，把長度較小的 `memcpy` 直接**內聯展開**成 `rep movsb` 或 XMM 向量搬移指令，根本不經過 `memcpy@plt`；三是你想親眼確定自己構造的畸形封包，到底有沒有在執行期穿過重重檢查、真的把 `0x8` 送進 `malloc`。

這時候就得把 Ghidra 裡的靜態位址，換算成 GDB 裡開了 ASLR 之後的真實記憶體位址。換算公式非常簡單，只要記住「**先減靜態基底、再加動態基底**」：

1. **在 Ghidra 算出相對偏移（RVA）**：Ghidra 載入 `.so` 或 PIE 執行檔時，會自己假設一個固定的預設映像基底 `ImageBase`（通常是 `0x00100000`）。假設你在 Ghidra 裡看到那行 `call malloc@plt` 的位址是 `0x00101446`，先減去預設基底：`0x00101446 - 0x00100000 = 0x1446`。這個 `0x1446` 就是該指令相對於模組起點的固定偏移量。
2. **在 GDB 查出當下的隨機載入基底**：在 Linux 開啟 `28-bit` ASLR 的環境下，每次跑起來 `.so` 的載入基底都不一樣（但低 `12 bits` 頁內偏移永遠對齊 `0x000`）。你在 GDB 先對 `main` 下斷點把程式跑起來，等 `libnexus-parse.so` 載入後，輸入 `info proc mappings`（或 `pwndbg` 的 `vmmap`）。

   接著找出 `libnexus-parse.so` **第一筆映射**（對應檔案偏移 `Offset = 0x0` 的模組映像起點）的起始位址，假設是 `0x7ffff7fc0000`。切記一定要拿 `Offset = 0x0` 的第一筆映像起點來加，千萬別拿中間 `.text` 區段的起點去加，否則會把檔案偏移重複加兩次！
3. **相加下斷點**：直接執行 `b *(0x7ffff7fc0000 + 0x1446)`，就能一分不差地把斷點釘在那行沒有符號的指令上！

---

## 故障模式與防禦

看懂逆向分析師怎麼拆解二進位檔之後，我們同時從「審計者常踩的判讀陷阱」與「開發團隊該做的工程防禦」兩頭來收斂。

### 故障模式 1：盡信反編譯器的型別猜測，漏看有號／無號與 32 位元截斷

很多初學逆向的人打開 Ghidra，眼睛只盯著右邊的類 C 反編譯視窗，完全不看左邊的組合語言。這是非常危險的習慣！當 Ghidra 還不確定一個 4-byte 變數到底是 `int32_t` 還是 `uint32_t` 時，它可能隨手標一個 `int`。如果你只看右邊的 `if (len < 65536)`，很容易以為有做上限檢查；切回左邊反組譯視窗一看，才發現指令居然是 `cmp eax, 0x10000; jg error`（有號比較）——攻擊者只要傳入負數（例如 `0xffffffff`），就能大搖大擺繞過檢查。同樣地，32 位元 `eax` 跟 64 位元 `rax` 的截斷差異，也只有對照反組譯視窗的暫存器名字才抓得準。

### 故障模式 2：被 `-O2` 編譯最佳化騙過，漏抓內聯的 `memcpy` 與尾呼叫

正式環境的 `.so` 幾乎都是開 `-O2` 或 `-O3` 編譯的，這會帶來兩種常見的視覺陷阱：
第一是 **Tail-Call Optimization**（尾呼叫最佳化）。如果函式 A 的最後一件事就是呼叫函式 B 並直接回傳，編譯器會把原本的 `call B; ret` 改寫成一句 `jmp B`。這會讓反編譯器誤以為 A 跟 B 是同一個函式的不同分支，或者在呼叫圖上漏掉這條連線。
第二是 **`memcpy` 內聯展開**。當拷貝長度較小或編譯器覺得展開比較快時，它會直接生出 `rep movsb` 或 `movdqu` / `movups` 向量搬移指令，根本不會去呼叫 `.plt` 裡的 `memcpy`。所以如果查完 `memcpy@plt` 沒看到東西，記得還要在反組譯裡搜尋 `rep movs` 或順著資料指標讀寫往下追。

### 故障模式 3：把「不給原始碼＋`strip -s`」當成資安防線

有些商用套件或內部核心模組的負責人會說：「我們的 `.so` 沒開源，出廠前還跑了 `strip -s`，外面的人不知道裡面有個 `0x0099` 除錯模式，也不用急著修裡面的長度檢查。」

透過這一章的推導你已經看得很清楚了：在 Linux 後端與容器環境裡，為了維持執行效率與 Core Dump 除錯相容性，線上跑的幾乎都是標準的 stripped ELF（不像部分 Windows 桌面軟體會套 VMProtect 之類的商業虛擬化加殼器）。只要 `.dynsym`、`.eh_frame` 跟 `.rodata` 還在，有經驗的研究員不用半小時就能把隱藏的 `0x0099` 分支跟 `shl eax, 3` 溢位挖出來。「靠藏原始碼來防駭客」（Security through Obscurity）在原生二進位審計面前是完全不堪一擊的。

### 真正有效的二進位硬化與算術防禦

要守住原生模組，該做的是下面三件實打實的工程防禦：

1. **用溢位安全原語換掉手寫的裸乘法與裸加法**：
   在 C 語言裡，絕對不要自己寫 `malloc(count * sizeof(uint64_t))` 或 `malloc(len + 8)`。請全面改用 glibc 2.26+ 內建溢位檢查的 **`reallocarray(NULL, count, sizeof(uint64_t))`**（一旦乘法溢位就會自動設 `ENOMEM` 並回傳 `NULL`），或是用 GCC / Clang 的內建檢查函式 **`__builtin_mul_overflow(count, sizeof(uint64_t), &total_bytes)`** 與 **`__builtin_add_overflow`**。如果是用 Rust 寫 FFI 解析器，記得 Release 模式下預設整數加法也是會回繞的，一定要強制呼叫 `checked_mul` 與 `checked_add`（見第 25 章）。
2. **用 `-fvisibility=hidden` 縮減 `.dynsym` 的符號暴露面**：
   編譯 `.so` 共享函式庫時，在編譯參數加上 `-fvisibility=hidden`，然後只在真正需要給外部呼叫的那幾個公開 API 頭上標註 `__attribute__((visibility("default")))`。這樣一來，所有跨檔案的內部輔助函式都不會被塞進 `.dynsym` 動態符號表，能大幅減少外部直接從符號表看穿內部架構的機會。
3. **開滿編譯期與連結期硬化參數**：
   搭配 `-O2 -D_FORTIFY_SOURCE=3`（讓編譯器在推得出緩衝區大小的地方，自動把 `memcpy` 換成帶邊界檢查的 `__memcpy_chk`）、`-fstack-protector-strong`、`-Wl,-z,relro,-z,now`（Full RELRO）與 `-fcf-protection=full`（Intel CET），把縱深防禦一次鎖緊。

---

## 動手做

- **難度**：進階
- **預估時間**：50 分鐘

現在我們在本地 Linux 環境（需安裝 `gcc`、`binutils`、`gdb`、`python3`，選配 Ghidra）親手演練一次完整的無原始碼逆向：先編出一個跟真實環境一樣用 `-O2` 最佳化並跑過 `strip -s` 的 `libnexus-parse.so`，接著不看 `.c` 原始碼，只靠二進位工具與 GDB 揪出裡面的隱藏 `0x0099` 除錯分支與 `count * 8` 整數溢位漏洞。

> **授權與倫理邊界**：本實驗所有逆向與觸發測試，皆僅限於本地自己編譯的 NexusPay 教學靶標與授權靶場（pwn.college）。

### 步驟 1：編譯並剝除符號的 `libnexus-parse.so` 與測試載入器

建一個空目錄，放入下面這支 `nexus_parse.c`。為了模擬較大型的內部函式在 `-O2` 下沒有被整塊內聯消失，我們加上 `noinline`，但馬上就會用 `strip -s` 把所有內部函式名稱跟型別徹底抹掉：

```c
// nexus_parse.c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    uint16_t magic;
    uint16_t type;
    uint32_t count;
    uint64_t *items;
} nexus_tlv_ctx_t;

__attribute__((noinline))
static int parse_debug_opcode(nexus_tlv_ctx_t *ctx, const uint8_t *payload, size_t payload_len) {
    char trace_buf[32];
    if (ctx->count > 0 && payload_len >= ctx->count) {
        /* 隱藏除錯破口：沒檢查 count <= 32 就直接往 32-byte 的堆疊陣列拷貝！ */
        memcpy(trace_buf, payload, ctx->count);
        trace_buf[31] = '\0';
        fprintf(stderr, "[DBG] %s\n", trace_buf);
        return 1;
    }
    return -1;
}

__attribute__((noinline))
static int alloc_tlv_records(nexus_tlv_ctx_t *ctx, const uint8_t *payload, size_t payload_len) {
    if (ctx->magic != 0x584e) {
        return -1;
    }
    if (ctx->type == 0x0099) {
        return parse_debug_opcode(ctx, payload, payload_len);
    }
    if (ctx->count == 0) {
        return -1;
    }
    /* 破口：32 位元無號乘法溢位，且沒檢查 count <= 8192 (64 KiB) 上限 */
    uint32_t bytes = ctx->count * 8U;
    ctx->items = (uint64_t *)malloc((size_t)bytes);
    if (!ctx->items) {
        return -1;
    }
    if (payload_len >= 8) {
        memcpy(ctx->items, payload, 8);
    }
    return 0;
}

int nexus_parse_packet(const uint8_t *raw, size_t len) {
    if (!raw || len < 8) {
        return -1;
    }
    nexus_tlv_ctx_t ctx;
    memset(&ctx, 0, sizeof(ctx));
    memcpy(&ctx.magic, raw, 2);
    memcpy(&ctx.type, raw + 2, 2);
    memcpy(&ctx.count, raw + 4, 4);
    int rc = alloc_tlv_records(&ctx, raw + 8, len - 8);
    free(ctx.items);
    return rc;
}
```

再建立一支簡單的載入器 `harness.c`，負責讀入二進位封包檔並丟給 `libnexus-parse.so`：

```c
// harness.c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern int nexus_parse_packet(const uint8_t *raw, size_t len);

int main(int argc, char **argv) {
    if (argc < 2) return 1;
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 1;
    fseek(f, 0, SEEK_END);
    long sz = ftell(f);
    rewind(f);
    uint8_t *buf = malloc((size_t)sz);
    fread(buf, 1, (size_t)sz, f);
    fclose(f);
    int rc = nexus_parse_packet(buf, (size_t)sz);
    printf("rc=%d\n", rc);
    free(buf);
    return 0;
}
```

執行編譯並用 `strip -s` 把 `libnexus-parse.so` 的符號表拔光：

```bash
gcc -shared -fPIC -O2 -o libnexus-parse.so nexus_parse.c
strip -s libnexus-parse.so
gcc -O2 -Wl,-rpath,'$ORIGIN' -o harness harness.c -L. -lnexus-parse
```

### 步驟 2：檢視 `strip -s` 後殘留的動態符號與區段

跑下面三行指令，確認 `.symtab` 已經消失，但 `.dynsym`、`.plt`、`.eh_frame` 與 `.rodata` 依然活得好好的：

```bash
nm libnexus-parse.so
nm -D libnexus-parse.so
readelf -S libnexus-parse.so | grep -E "symtab|dynsym|eh_frame|rodata|plt"
```

### 步驟 3：用 Ghidra 或 `objdump` 從 Sink 反推結構與偏移

現在假裝你手上沒有 `nexus_parse.c`：
1. 如果你有裝 Ghidra，把 `libnexus-parse.so` 匯入，從 `Symbol Tree -> Imports` 點開 `malloc` 與 `memcpy` 的交叉引用（XREF），跳進那兩個沒有名字的 `FUN_*` 內部函式，建立一個 16-byte 的結構體套用到第一個參數 `param_1` 上。
2. 如果你只用終端機，直接跑 `objdump -d -M intel libnexus-parse.so`，搜尋 `<malloc@plt>`，往上讀 15 行指令，找出比對 `0x584e`、`0x99` 以及左移/乘以 8 的那段組合語言，並記下 `call malloc@plt` 那一行指令在檔案裡的十六進位偏移（例如 `0x11e8`）。

### 步驟 4：構造溢位封包並在 GDB 動態攔截驗證

用 Python 生出一個 `count = 0x20000001` 的畸形 TLV 封包 `overflow.tlv`，然後進 GDB 換算 ASLR 位址，把斷點精準下在 `call malloc@plt` 上，親眼確認傳給 `malloc` 的 `$edi` 是不是真的從 4 GiB 縮水成了 `0x8`！

### 外部靶場對照檢查點（pwn.college）

做完本地練習後，強烈推薦到 **pwn.college** 的 **Program Security -> Reverse Engineering** 模組挑戰。打關卡時記住四個通關訣竅：
1. **常數與小端序關卡**：看到組合語言寫 `cmp dword ptr [rsp], 0x41424344`，記得小端序在記憶體裡的字串順序是倒過來的 `"DCBA"`，別傻傻輸入 `"ABCD"`。
2. **多輪 XOR 與位元洗牌關卡**：遇到 stripped 函式對輸入做了一連串 XOR 或位移時，不要用人腦心算，直接照著反編譯出來的邏輯用 Python 寫個十行的逆運算腳本算答案。
3. **陣列步長與跳躍表關卡**：看到 `lea rax, [rdi + rdi*4]` 這類怪異算式，先在紙上寫出它是 `5 * index`，通常代表每個元素佔 `5` 或 `20 bytes` 的結構體陣列。
4. **反編譯畫面太亂時**：只要覺得 Ghidra 的型別轉型看不太懂，馬上開 GDB 把斷點設在比對指令（`cmp` / `memcmp`）那一刻，直接印出當下的暫存器跟記憶體最準。

---

### 參考解答

#### 1. 步驟 2 與步驟 3 靜態逆向結果

執行 `nm libnexus-parse.so` 會印出 `no symbols`，代表 `.symtab` 裡的 `alloc_tlv_records` 和 `parse_debug_opcode` 名字確實被抹掉了。但緊接著跑 `nm -D libnexus-parse.so`，畫面上馬上列出匯出的 `T nexus_parse_packet`，以及未定義的外部匯入符號 `U malloc`、`U memcpy`、`U fprintf`、`U free`。

順著 `malloc@plt` 與 `memcpy@plt` 的呼叫點往上追，不用原始碼也能完整抓出兩個致命漏洞：
- 在呼叫 `malloc@plt` 的無名函式裡，程式先檢查 `+0x00` 的 `uint16_t` 是否等於 `0x584e`，再檢查 `+0x02` 的 `uint16_t` 是否等於 `0x0099`；如果不是，就取出 `+0x04` 的 `uint32_t count`，直接乘以 8（`shl eax, 3` 或 `lea edi, [rax*8]`）丟進 `malloc` 的第一個參數 `edi`，並把回傳的指標存進 `+0x08`。
- 若 `+0x02` 的 `type` 剛好填了公開文件沒寫的 `0x0099`，程式就會跳進另一個呼叫 `memcpy@plt` 的無名函式：它只檢查了 `payload_len >= ctx->count`，卻完全沒檢查目的端堆疊陣列 `trace_buf` 只有 `32 bytes`，只要傳入 `count > 32` 就會直接觸發堆疊緩衝區溢位！

#### 2. 步驟 4 構造封包與 GDB 動態驗證實錄

先用一行 Python 產生 `magic = 0x584e`、`type = 0x0001`、`count = 0x20000001` 的測試封包：

```bash
python3 -c 'import struct; open("overflow.tlv", "wb").write(struct.pack("<HHI", 0x584e, 0x0001, 0x20000001) + b"A"*16)'
```

接著先用 `objdump -d -M intel libnexus-parse.so | grep "malloc@plt" -B 5` 查出 `call malloc@plt` 的相對偏移（以下假設查出來的偏移是 `0x11e8`，請替換成你機器上實際顯示的十六進位數字），然後進 `gdb -q ./harness` 實測：

```gdb
(gdb) b main
(gdb) r overflow.tlv
# 等進入 main、動態庫已載入後，查出 libnexus-parse.so 第一筆映射 (Offset 0x0) 的基底位址：
(gdb) info proc mappings
# 假設查到 libnexus-parse.so 第一筆起始位址為 0x7ffff7fc0000，加上相對偏移 0x11e8 下斷點：
(gdb) b *(0x7ffff7fc0000 + 0x11e8)
(gdb) c
# 停在 call malloc@plt 那一刻，印出傳給 malloc 的第一個參數 $edi 與結構體裡的 count：
(gdb) p/x $edi
$1 = 0x8
(gdb) x/xw $rbx+4
0x7fffffff...: 0x20000001
```

畫面鐵證如山：結構體 `+0x04` 裡面記的項目筆數明明是 `0x20000001`（五億三千多萬筆），但因為 32 位元乘以 8 發生溢位截斷，傳給 `malloc` 的 `$edi` 竟然只剩下區區 `0x8` bytes！

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

先別看下面的解答，試著用剛剛練過的逆向思維與算術規則，回答這 4 個問題：

1. **為什麼 `strip -s` 藏不住函式邊界與危險呼叫**：某家廠商在交付 `libauth.so` 之前跑了 `strip -s libauth.so`。請問為什麼 Ghidra 載入這個檔案後，依然能精準切出裡面每一個內部函式的起點跟結束位置？又為什麼審計員不用看符號表，就能一眼列出所有呼叫 `memcpy` 跟 `malloc` 的地方？
2. **看懂 Ghidra SSA 的節點與型別盲區**：當 Ghidra 把 x86_64 機器碼轉成 SSA 中間表示時，如果遇到 `if / else` 兩條路匯合，或是遇到呼叫外部函式，分別會插入 `MULTIEQUAL` 跟 `INDIRECT` 兩種節點，它們各自代表什麼意思？另外，如果審計員沒把反編譯器預設猜的 `int`（有號 32 位元）手動修正成 `uint32_t`，在看長度檢查時會漏掉什麼經典漏洞？
3. **手算 32 位元「每筆 16 bytes」乘法溢位臨界值**：假設你在逆向另一個閉源解析函式時，看到下面四行組合語言（把封包 `+0x08` 處的 4-byte 項目數 `count` 乘以 `16 bytes` 後拿去配記憶體）：
   ```nasm
   mov  eax, dword ptr [rdi+0x8]
   shl  eax, 4
   mov  edi, eax
   call malloc@plt
   ```
   請問：(a) `shl eax, 4` 代表陣列裡每一筆項目佔幾個 bytes？(b) 如果我們想讓 `shl eax, 4` 在 32 位元 `eax` 裡剛好溢位回繞成 `0x0000_0010`（只呼叫 `malloc(16)`），傳入的最小非零無號十六進位 `count` 值應該填多少？
4. **ASLR 下斷點的常見算術錯誤**：在開啟 ASLR 的 Linux 機器上用 GDB 除錯 `libnexus-parse.so` 時，某位工程師在 Ghidra（預設 `ImageBase = 0x00100000`）看到目標指令位在 `0x00101350`。他進 GDB 跑 `info proc mappings` 看到下面兩行：
   ```text
   0x7ffff7fc0000 0x7ffff7fc1000 0x1000 0x0    r--p libnexus-parse.so
   0x7ffff7fc1000 0x7ffff7fc2000 0x1000 0x1000 r-xp libnexus-parse.so
   ```
   於是他拿第二行有 `r-xp`（可執行 `.text` 片段）的起點 `0x7ffff7fc1000` 加上 `0x1350`，下了 `b *0x7ffff7fc2350`，結果斷點完全沒停在對的地方！請問他算錯在哪裡？正確的斷點位址是多少？

---

### 參考解答

1. **為什麼 `strip -s` 藏不住函式邊界與危險呼叫**：
   - `strip -s` 只刪掉了靜態符號表（`.symtab` / `.strtab`）跟 DWARF 除錯區段（`.debug_*`）。
   - 現代編譯器預設會產生 **`.eh_frame`** 堆疊展開區段，裡面的每一筆 FDE（Frame Description Entry）都精確記錄了每個內部函式在 `.text` 的起始位址與位元組長度，所以 Ghidra 不用靠符號表也能把函式邊界切得一清二楚。
   - 同時，動態連結器在執行期必須靠 **`.dynsym`**、**`.rela.plt`** 與 **`.plt`（或 `.plt.sec`）** 才能呼叫外部共享庫的函式，這些區段在 `strip -s` 後百分之百保留，所以只要對 `malloc` 或 `memcpy` 的匯入符號查交叉引用（XREF），所有未內聯的呼叫點就會全部現形。
2. **Ghidra SSA 的節點意義與有號／無號型別盲區**：
   - **`MULTIEQUAL`** 就是 SSA 的 $\phi$（phi）節點，放在多條控制流分支的匯合處，代表該變數的值取決於程式實際從哪一條前驅分支走過來；**`INDIRECT`** 則用來標記跨函式呼叫或未知指標寫入所帶來的間接資料修改與潛在別名（Aliasing）影響，防止最佳化引擎做出錯誤的跨呼叫假設。
   - 如果沒把反編譯器誤猜的有號與無號型別校準好，審計員看類 C 虛擬碼時，很容易把底層其實是用有號跳躍（`jg` / `jl`）做的長度檢查當成安全防線，漏看「傳入最高位為 1 的負數即可繞過上限檢查、進到 `memcpy(size_t)` 再變回超大無號正整數」的漏洞；或是沒看出運算其實是在 32 位元 `eax` 上先被溢位截斷了一次。
3. **手算 32 位元「每筆 16 bytes」乘法溢位臨界值**：
   - (a) `shl eax, 4` 是將數值左移 4 個位元，相當於乘以 $2^4 = 16$，代表陣列裡每一筆元素佔 **`16 bytes`**。
   - (b) 要在 32 位元 `eax`（模 $2^{32} = \text{0x1\_0000\_0000}$）左移 4 位元後剛好回繞剩下 `0x10`（16），算式就是：
     $$\text{count} \times 16 = 2^{32} + 16 = \text{0x1\_0000\_0010}$$
     兩邊同時除以 16（右移 4 位元），直接得出最小的溢位十六進位值為 **`count = 0x1000_0001`**（十進位 `268,435,457`）。當傳入 `0x1000_0001` 時，乘以 16 在 32 位元下剛好回繞成 `0x10`，只向系統要了 `malloc(16)`！
4. **ASLR 下斷點的常見算術錯誤**：
   - **錯在哪裡**：他在 Ghidra 算出的相對偏移 `0x00101350 - 0x00100000 = 0x1350`，是相對於**整個模組映像起點**（也就是檔案偏移 `Offset = 0x0`）的距離，裡面其實已經包含了 `.text` 區段本身的檔案偏移 `0x1000`。結果他又拿 GDB 裡第二行 `Offset = 0x1000` 的 `r-xp` 起點（`0x7ffff7fc1000`）去加 `0x1350`，等於把 `0x1000` 重複加了兩次，多偏了整整一頁（`4 KiB`）。
   - **正確位址**：必須拿對應檔案偏移 `Offset = 0x0` 的第一筆映射基底 `0x7ffff7fc0000` 來加：`0x7ffff7fc0000 + 0x1350 = 0x7ffff7fc1350`（或者拿 `r-xp` 的起點 `0x7ffff7fc1000` 加上扣掉區段偏移後的 `0x350`，算出來一樣是 **`0x7ffff7fc1350`**）。

---

## 延伸閱讀

- **Ghidra Software Reverse Engineering Framework & P-Code Reference Manual**（https://ghidra-sre.org/）：官方開源逆向框架與隨附的 P-code 手冊，詳細定義了 SLEIGH 語法、Raw P-code 位址空間與 SSA 反編譯管線的每一個微操作。
- **Linux Man Pages: `elf(5)`**（https://man7.org/linux/man-pages/man5/elf.5.html）：核對 ELF 區段標頭、`.dynsym`、`.rela.plt` 與 `.eh_frame` 結構定義的標準參考。
- **pwn.college — Program Security: Reverse Engineering**（https://pwn.college/）：從零開始練習常數萃取、Stripped 函式結構體還原到複雜虛擬機逆向的免費線上實戰靶場。
- **GCC Wiki — Symbol Visibility (`-fvisibility=hidden`)**（https://gcc.gnu.org/wiki/Visibility）與 **GNU C Library Manual (`reallocarray`)**：了解如何減少共享函式庫 `.dynsym` 的符號暴露，以及如何用標準庫溢位安全原語消滅整數溢位漏洞。
