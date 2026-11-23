# 第 20 章：二進位執行環境與記憶體佈局

前十九章看過的後端漏洞，大多發生在有執行期保護傘的環境裡。Node.js 的陣列與物件交給 V8 管理，SQL 查詢靠驅動程式參數化送進 PostgreSQL，容器則由 Linux 核心的 Namespaces 與 cgroups 隔開。但只要系統為了衝高吞吐量、壓低延遲而跨過 FFI 邊界，跳進 C、C++ 或 `unsafe` Rust 編譯出的原生機器碼，情況就徹底變了。

在 **NexusPay** 架構裡，API 閘道為了高速解析二進位銀行對帳封包，透過 N-API 掛載了原生解析模組 `libnexus-parse`。第 1 章把這道交界標為信任邊界 TB-4：封包有著固定 `8 bytes` 的檔頭（`magic: 2B`、`type: 2B`、`len: 4B` 無號 `uint32`），規定合法負載上限為 `65,536 bytes`（`64 KiB`）。

一旦這串位元組被送進原生函式，受托管環境的自動邊界檢查與型別標籤就瞬間消失，記憶體裡只剩下虛擬位址、暫存器與冰冷的位元組。這正是 Part IV 的起點——在進入無原始碼逆向（第 21 章）、控制流保護（第 22 章）與堆積攻防（第 23–24 章）之前，我們得先看清楚 ELF 執行檔怎麼被載入記憶體，以及現代作業系統與編譯器設下的四道防線到底守在哪裡。

---

## 從你已知的出發

為什麼 Linux 核心明明有虛擬記憶體頁表（Page Table）和 CPU 的記憶體管理單元（MMU）把關，還把每一張 `4 KiB` 分頁嚴格標上讀、寫、執行權限（R/W/X），C 語言寫的解析器還是會因為多寫十幾個位元組就被駭客劫持控制流？

因為頁表只管「跨行程隔離」和「整張頁面的讀寫執行權限」，它**完全看不懂同一張可讀寫頁面裡面的資料代表什麼意義**。在同一個 64 位元行程裡，回傳位址（`Saved RIP`）、Stack Canary 與局部陣列，全都擠在同一張可讀寫（`RW-`）的堆疊頁面上；而全域函式指標表（像 Partial RELRO 下的 `.got.plt`）也同樣躺在可寫頁面上。

只要原生程式碼漏了一道長度檢查，攻擊者根本不需要突破核心的頁表隔離，光在同一個行程內部越界寫入，就能直接篡改控制流與全域狀態。

---

## 機制與推導

### 攻擊者目標與實質影響

當攻擊者在 `libnexus-parse` 這類原生二進位模組裡抓到記憶體漏洞時，追求的絕不只是把程式搞崩潰，而是三種層次的實質破壞：

第一是**劫持控制流與任意程式碼執行**（Arbitrary Code Execution）。攻擊者會設法覆寫堆疊上的回傳位址、堆積上的函式指標，或是動態連結表的槽位，把指令指標暫存器（`RIP`）拐去執行自己挑選的指令序列。

別忘了，Node.js 透過 N-API 載入的 `.node` 原生外掛，跟 Node.js 主程式共用同一個行程位址空間。一旦 `libnexus-parse` 被拿到任意程式碼執行，就等於拿下了整個 API Gateway Worker 的作業系統與容器權限；就算只拿到越界讀取能力，也能偷看同一個 Worker 記憶體裡其他商戶正在處理的請求、環境變數與資料庫憑證。

第二是**偷取行程記憶體裡的敏感資訊與記憶體指標**（Information Disclosure）。就算沒辦法立刻改寫 `RIP`，只要有一處越界讀取或忘了清零的結構體填充（Struct Padding），就能把相鄰租戶的資料、金鑰碎片或記憶體指標外洩給呼叫端。只要外洩的指標能夠對上某個已載入模組（像 `libc` 或主程式）裡面的已知固定偏移符號，攻擊者一減就能算出該模組的隨機化基底位址，拿到下一階段精準攻擊的入場券。

第三是**當作跨層攻擊鏈的跳板**。拿到容器內行程的系統呼叫控制權後，攻擊者就能往外打擊同節點的其他弱點（串聯第 17 章的容器逃逸與第 18 章的雲端憑證竊取），或者配合第 21 章的逆向分析，為第 22 至 24 章的控制流與堆積利用鋪平道路。

---

### ELF 格式雙重視角：區段與載入片段

Linux 上的可執行檔、共享函式庫（`.so`）與 Node.js 原生外掛（`.node`）全部採用 **ELF**（Executable and Linkable Format）格式。初學 ELF 最容易搞混的地方，是它為了伺候兩種不同的對象，在同一個檔案裡塞了兩套目錄：**連結視角**（Linking View）的 Section Header Table 是給編譯器、連結器與反組譯工具看的；**執行視角**（Execution View）的 Program Header Table 則是給 Linux 核心與動態連結器在啟動程式時看的。

```text
ELF 檔案實體佈局                          載入後的虛擬記憶體映射
┌──────────────────────────────────┐     ┌────────────────────────────────┐
│ ELF Header (Elf64_Ehdr, 64 B)    │     │                                │
│  e_type: ET_EXEC / ET_DYN        │     │ PT_LOAD #1 (flags: R-X)        │
├──────────────────────────────────┤     │  .init / .plt / .text          │
│ Program Header Table (執行視角)  │ ──▶ │  (對齊 4 KiB 頁，唯讀可執行)   │
│  PT_LOAD (R-X), PT_LOAD (RW-)    │     ├────────────────────────────────┤
│  PT_INTERP, PT_DYNAMIC           │     │ PT_LOAD #2 (flags: R--)        │
│  PT_GNU_STACK, PT_GNU_RELRO      │ ──▶ │  .rodata / .eh_frame           │
├──────────────────────────────────┤     ├────────────────────────────────┤
│ .text, .plt, .rodata             │     │ PT_LOAD #3 (flags: RW-)        │
│ .data, .got, .got.plt, .bss      │ ──▶ │  .init_array / .got (RELRO)    │
│ .dynamic, .dynsym, .symtab       │     │  .got.plt / .data / .bss       │
├──────────────────────────────────┤     └────────────────────────────────┘
│ Section Header Table (連結視角)  │      註：.bss 在檔案中不佔位元組 (NOBITS)
└──────────────────────────────────┘      載入時依 memsz - filesz 補零擴展
```

#### ELF Header 關鍵欄位與為什麼 `strip` 不影響執行

打開任何一個 64 位元 ELF 檔案，最開頭的 64 位元組固定是 `Elf64_Ehdr` 檔頭。看安全防線時，我們最關心裡面的三個欄位：

第一個是 `e_ident[0..3]`，固定放著魔術數字 `0x7f 'E' 'L' 'F'`。

第二個是 `e_type`，決定這支檔案能不能被放到隨機位址執行。傳統沒開位址隨機化的執行檔會標成 `ET_EXEC`（數值 `2`），編譯時就寫死了固定的虛擬載入位址；而共享函式庫（`.so`）與現代開啟 **PIE**（Position Independent Executable）的主執行檔，型別全都是 `ET_DYN`（數值 `3`）。

標為 `ET_DYN` 代表核心載入器可以照分頁對齊規則，把它丟到隨機挑選的基底位址上執行。如果你想區分一支 `ET_DYN` 到底是主執行檔還是一般 `.so`，只要看它有沒有 `PT_INTERP` 片段，或檢查動態表 `DT_FLAGS_1` 裡有沒有 `DF_1_PIE` 旗標就一清二楚了。

第三組是 `e_phoff` 與 `e_shoff`，分別紀錄 Program Header Table（執行視角）與 Section Header Table（連結視角）在檔案裡的偏移位置。

很多人第一次做逆向時會納悶：為什麼對執行檔跑了 `strip -s`，甚至故意把整個 Section Header Table 抹掉，程式照樣能跑？原因就在這裡——Linux 核心的 `load_elf_binary()` 在執行 `execve(2)` 載入程式時，**只看 ELF Header 和 Program Headers（像 `PT_LOAD` 這些載入片段），根本不看 Section Headers**。

不過，只要這支程式還需要呼叫外部動態庫（例如 `libc.so.6`），`PT_DYNAMIC` 片段指到的動態表，以及 `DT_SYMTAB`、`DT_STRTAB` 指向的 `.dynsym` 與 `.dynstr` 動態符號資料就絕對不能砍，因為動態連結器（`ld-linux-x86-64.so.2`）在執行期得靠它們才能按名字找到外部函式。

#### 五個核心區段與 PLT/GOT 延遲綁定的安全代價

在靜態看 code 或用 GDB 追記憶體時，下面五組區段構成了程式的骨架，而它們在執行期能不能寫、能不能執行，全看自己被打包進哪一個 `PT_LOAD` 載入片段：

首先是放機器碼的 **`.text`**（歸在 `R-X` 唯讀可執行片段）與放唯讀字串常數的 **`.rodata`**（現代連結器預設獨立歸在 `R--` 唯讀不可執行片段）。

接著是放全域與靜態變數的 **`.data` 與 `.bss`**，兩者都落在 `RW-` 可讀寫片段。差別在於已經給定非零初值的變數會放在 `.data`，實實在在佔用磁碟檔案空間；而未初始化或初值為零的變數則歸入 `.bss`（標記為 `SHT_NOBITS`），在檔案裡不佔半個位元組，只靠 `PT_LOAD` 標頭裡 `p_memsz > p_filesz` 的差額，通知核心在載入記憶體時多配一塊空間並自動填零。

最後一組是負責外部函式呼叫的 **`.plt`**（Procedure Linkage Table，位在 `R-X` 程式碼片段）與 **`.got` / `.got.plt`**（Global Offset Table，存放外部變數與外部函式在執行期的真實虛擬位址）。

為什麼呼叫一個簡單的 `memcpy`，不直接跳過去，還要繞過 `.plt` 和 `.got.plt` 兩張表？因為一支大型程式可能連結了上千個外部函式，但單次跑起來只會用到其中十幾個。為了不讓程式每次啟動都花大把時間把所有符號解析完，傳統 ELF 動態連結設計了 **Lazy Binding**（延遲綁定）：

```text
首次呼叫 memcpy@plt：
  call memcpy@plt
   └─▶ jmp qword ptr [memcpy@got.plt]   (初始值竟然指回 .plt 下一行指令!)
        └─▶ push reloc_index (推入重定位索引)
             └─▶ jmp .plt[0]            (跳進 ld.so 的 _dl_runtime_resolve)
                  └─▶ 查出 libc 裡 memcpy 的真實位址，寫回 [memcpy@got.plt]，再跳過去執行

第二次以後呼叫 memcpy@plt：
  call memcpy@plt
   └─▶ jmp qword ptr [memcpy@got.plt]   (裡頭已經是真實位址，一跳就進 libc 的 memcpy!)
```

看懂這段跳板流程，你馬上就能抓出它留下的安全破口：**為了讓 `_dl_runtime_resolve` 在程式跑一半時還能把查到的真實位址寫回去，`.got.plt` 所在的記憶體分頁在執行期就必須保持可寫（`RW-`）！** 這意味著，只要攻擊者透過漏洞拿到任意位址寫入的能力，去把 `[memcpy@got.plt]` 裡面的函式指標偷換成別的位址，下一秒程式只要一呼叫 `memcpy`，控制流就會乖乖跳進攻擊者指定的陷阱裡。這也是後面我們討論 Partial RELRO 與 Full RELRO 時最核心的攻防焦點。

---

### 64 位元行程虛擬記憶體佈局與頁權限

當核心把 ELF 執行檔和動態連結器映射進記憶體後，一個 64 位元 x86_64 行程的虛擬位址空間會長成什麼樣？

先看硬體定址的鐵律：**Canonical Address**（規範位址）。雖然指標長度是 64 位元，但在主流的 4 層分頁架構下，CPU 其實只拿低 48 位元來定址，而且硬性規定最高 16 位元（bits 48..63）必須原封不動複製第 47 位元（符號擴展；若是開啟 5 層分頁 `LA57` 的機器則用低 57 位元，最高 7 位元必須複製第 56 位元）。這條硬體規則把 64 位元位址切成了三塊：

最底下是**使用者空間**（User Space），第 47 位元為 `0`，範圍從 `0x0000_0000_0000_0000` 到 `0x0000_7fff_ffff_ffff`，總共 `128 TiB`。

最頂端是**核心空間**（Kernel Space），第 47 位元為 `1`，範圍從 `0xffff_8000_0000_0000` 到 `0xffff_ffff_ffff_ffff`。這些分頁的頁表項目（PTE）沒有開啟 `U/S`（User）權限，一般應用程式（Ring 3）只要敢碰就會立刻觸發頁面錯誤（Page Fault）。

夾在兩者中間、從 `0x0000_8000_0000_0000` 到 `0xffff_7fff_ffff_ffff` 的巨大斷層，就叫做**非規範空洞**（Non-canonical Hole）。只要程式不小心把指標算壞、解參考到這段空洞裡的任何位址，CPU 連頁表都不用查，當場就會拋出硬體例外（一般定址觸發 `#GP` General Protection Fault，透過堆疊暫存器存取則觸發 `#SS` Stack-Segment Fault），接著被 Linux 核心轉成 `SIGSEGV` 或 `SIGBUS` 訊號直接殺掉行程。

在我們能碰的 `128 TiB` 使用者空間裡，從低位址到高位址的典型排列如下。開啟 ASLR 與 PIE 之後，每個獨立映射區塊的起點都會隨機偏移，但同一個模組內部的各區段相對距離永遠固定：

```text
低位址  0x0000_0000_0000_0000
         │  (未映射的 NULL 頁保護區，一抓到空指標解參考就立刻崩潰)
         ▼
        ┌────────────────────────────────────────────┐  PIE (ET_DYN) 基底約 0x5555...
        │ 主執行檔 .text (R-X) / .rodata (R--)       │  (若未開 PIE 則常固定在 0x400000)
        │         .got.plt / .data / .bss (RW-)      │
        ├────────────────────────────────────────────┤
        │ [heap] (brk/sbrk 動態擴張，往高位址長)(RW-)│
        ├────────────────────────────────────────────┤
        │                ↕ 未映射空洞                │
        ├────────────────────────────────────────────┤
        │ mmap 區域 (往低位址長)                     │
        │  - libc.so.6 / libnexus-parse.so (R-X/RW-) │
        │  - 大型匿名 mmap 配置 / 執行緒堆疊         │
        ├────────────────────────────────────────────┤
        │ [vvar] (R--) / [vdso] (R-X)                │  加速 gettimeofday 等系統呼叫
        ├────────────────────────────────────────────┤
        │ [stack] (高往低生長，向下擴張) (RW-)       │  主執行緒堆疊，由 RSP 指向頂端
        └────────────────────────────────────────────┘  頂端附近約 0x7fff_ffff_e000
高(User) 0x0000_7fff_ffff_ffff
════════════════════════════════════════════════════════ 規範位址邊界
高(Kern) 0xffff_8000_0000_0000 .. 0xffff_ffff_ffff_ffff (Ring 0 核心空間)
```

圖裡的每一個區塊，都是以 `4 KiB`（`4,096 bytes = 0x1000`）為最小分頁單位，靠頁表項目（PTE）控制 **R**（讀）、**W**（寫）與 **X**（執行，在硬體上對應 PTE 第 63 位元的 `NX/XD` Execute-Disable 位元，設為 `1` 就禁止執行）。一個健康的現代行程必須徹底落實 **W^X** 原則：放程式碼的 `.text` 只能是 `R-X`，不准在執行期偷改機器碼；放資料的 `[heap]`、`[stack]` 與 `.data` 只能是 `RW-`，就算被塞進了惡意位元組，CPU 也不准把它當成指令執行。

---

### x86_64 System V ABI、堆疊幀與 ARM64 呼叫慣例對照

平常在後端看報錯，我們看的是美化過的 Stack Trace；但在機器碼的世界裡，函式跟函式之間根本不知道對方的參數叫什麼名字，全靠處理器與作業系統定好的 **ABI**（Application Binary Interface）來交接參數、保管暫存器與對齊堆疊。

#### x86_64 System V AMD64 ABI 的三條鐵律

Linux 與 macOS 的 x86_64 環境都遵守 System V ABI，逆向與除錯時必須把下面三條規則背得滾瓜爛熟：

第一是**誰負責傳參數與接回傳值**。前 6 個整數或指標參數，固定依序放進 `RDI`、`RSI`、`RDX`、`RCX`、`R8`、`R9` 六個暫存器；第 7 個以後的參數才會從右到左壓進堆疊。函式跑完的回傳值則放在 `RAX`（如果是 128 位元回傳值會搭配 `RDX`）。這裡要小心一個小陷阱：如果是直接發動 Linux **系統呼叫**（`syscall` 指令），第 4 個參數不是用 `RCX`，而是改用 `R10`，因為 `syscall` 這條硬體指令自己會拿 `RCX` 去備份使用者態的下一行位址 `RIP`。

第二是**暫存器誰用完誰得還**。暫存器分成兩派：一派叫 **Caller-saved**（呼叫者保存，又叫易失暫存器），包含 `RAX`、`RCX`、`RDX`、`RSI`、`RDI`、`R8` 到 `R11`，被呼叫的子函式可以隨便覆寫它們，不用負責還原；另一派叫 **Callee-saved**（被呼叫者保存），包含 `RBX`、`RBP`、`R12` 到 `R15`（以及堆疊頂端 `RSP`）。如果子函式裡面會動到這些暫存器，就必須在開頭（Prologue）先把它們 `push` 存進堆疊，等要返回前（Epilogue）再 `pop` 還原回去。

第三是**最容易讓初學者踩雷的 `16-byte` 堆疊對齊不變量**。System V ABI 硬性規定：**在執行 `call` 指令的前一瞬間，堆疊指標 `RSP` 必須是 `16` 的倍數（`RSP % 16 == 0`）**。

我們順著指令走一次算術就明白了：
- 執行 `call target` **之前**，`RSP % 16 == 0`。
- `call` 指令會自動把 8 位元組的回傳位址（`Saved RIP`）壓進堆疊（`RSP -= 8`），所以當程式剛跳進 `target` 的第一條指令時，**`RSP % 16` 必定等於 `8`**。
- 接著，子函式開頭通常會執行一句 `push rbp`（再減 `8 bytes`），這時 `RSP` 就重新回到了 `RSP % 16 == 0` 的對齊狀態！接下來只要子函式用 `sub rsp, N` 配置局部變數空間時，讓所有的 `push` 加上 `N` 的總位移量維持讓下一層 `call` 之前仍然是 `16` 的倍數，這條對齊鏈就不會斷。

為什麼少對齊 8 個位元組都不行？因為現代 `glibc` 和編譯器在跑 `printf`、`memcpy` 或浮點運算時，會大量使用 `movaps`（Move Aligned Packed Single-Precision）這類 128 位元的 SSE/XMM 向量指令。`movaps` 有個壞脾氣：只要它碰到的記憶體位址不是 `16` 的倍數（末一碼不是 `0`），CPU 當場就會拋出 `#GP` 硬體例外把行程炸掉。

#### 跟雲端常見的 ARM64（AArch64 AAPCS64）比一比

現在許多雲端生產環境都跑在 AWS Graviton 或 Apple Silicon 這類 ARM64 處理器上。當你切換到 AArch64（AAPCS64 規範）審計二進位檔時，有三個地方跟 x86_64 明顯不同：

一是**傳參暫存器變多了**。前 8 個整數或指標參數依序放在 `X0` 到 `X7`，回傳值一樣放在 `X0`。

二是**回傳位址不直接壓堆疊，而是先放 `X30`（Link Register, `LR`）**。ARM64 呼叫函式用的 `bl`（Branch with Link）指令，不會自動把回傳位址寫進堆疊，而是直接存進 `X30` 暫存器。如果被呼叫的是一個不再呼叫別人的葉子函式（Leaf Function），編譯器往往會直接把回傳位址留在 `X30` 裡，**根本不寫進堆疊**！這時就算該函式裡面有局部陣列溢位，也改不到它自己的回傳位址；只有當函式還得呼叫別的子函式時，才會在開頭執行 `stp x29, x30, [sp, #-N]!`，把框架指標（`X29`/`FP`）跟回傳位址（`X30`/`LR`）一起存進堆疊。

三是**硬體直接強制檢查 `SP` 的 16-byte 對齊**。在 ARM64 上，根本不用等到執行向量指令，只要你拿未對齊 `16 bytes` 的堆疊指標 `SP` 去存取記憶體，CPU 硬體（由系統控制暫存器 `SCTLR_EL1.SA0` 與 `SA` 控制，Linux 預設全開）當場就會拋出對齊錯誤（Alignment Fault）。

---

### `libnexus-parse` 的記憶體視角：8-byte TLV 檔頭與堆疊佈局

現在把鏡頭拉回 NexusPay 的 `libnexus-parse` C 基準版。全書基準規定它的 TLV 封包檔頭固定是 `8 bytes`：`2 bytes` 的魔術數字 `magic`（固定為 `0x4e58`，也就是 ASCII 的 `'N'` `'X'`）、`2 bytes` 的型別 `type`，以及 `4 bytes` 的無號整數長度 `len`（合法上限 `65,536 bytes`）。

我們直接看這段 C 結構與解析函式在 64 位元 x86_64（小端序 Little-Endian）機器上的真實長相：

```c
// libnexus-parse C baseline 結構與堆疊幀示範
// 編譯環境：Linux x86_64 System V ABI (Little-Endian, 8-byte ptr, 16-byte stack align)
#include <stdint.h>
#include <string.h>

struct nexus_tlv_hdr {
    uint16_t magic;  // offset +0x00, 2 bytes (期望 0x4e58)
    uint16_t type;   // offset +0x02, 2 bytes
    uint32_t len;    // offset +0x04, 4 bytes (合法範圍 0..65536)
};                   // sizeof(struct nexus_tlv_hdr) = 8 bytes, align = 4

int parse_tlv_frame(const uint8_t *raw_buf, size_t raw_len) {
    struct nexus_tlv_hdr hdr;
    uint8_t local_copy[16];
    const uint8_t *payload_ptr;
    ...
}
```

假設外部送來一筆合法封包：`magic = 0x4e58`、`type = 0x0001`、`len = 64`（`0x00000040`），總長度 `72 bytes`，並呼叫 `parse_tlv_frame(pkt_ptr, 72)`。假設在執行 `call parse_tlv_frame` 之前，`RSP` 正好對齊在 `0x7fff_ffff_e100`，那麼進到函式裡面時，暫存器、記憶體位元組與堆疊幀會像下面這樣一格一格排開：

```text
[1] System V ABI 暫存器狀態 (剛踏入 parse_tlv_frame 第一條指令時)
    RDI = pkt_ptr (指標寬度 8 bytes, 例如 0x5555555592a0)
    RSI = 72      (0x48, raw_len)
    RSP = 0x7fff_ffff_e0f8  <-- call 指令壓入 8-byte Saved RIP，此時 RSP % 16 == 8

[2] 8-byte TLV 檔頭在記憶體裡的 Little-Endian 位元組排列 (位址 0x5555555592a0)
    偏移     位址                 位元組 (Hex)   對應欄位 (Little-Endian 小端序解讀)
    +0x00    0x5555555592a0       58 4e          magic = 0x4e58 (低位元組 0x58 在前!)
    +0x02    0x5555555592a2       01 00          type  = 0x0001
    +0x04    0x5555555592a4       40 00 00 00    len   = 0x00000040 (十進位 64)
    +0x08    0x5555555592a8       ...            payload 起始位元組 (共 64 bytes)

[3] parse_tlv_frame 執行完序言 (push rbp; mov rbp, rsp; sub rsp, 0x30)、寫入 Canary 並填好變數後的典型堆疊幀
    (總配置 48 bytes = 0x30，使 RSP = 0x7fff_ffff_e0c0，重新維持 16-byte 對齊)

    低位址  0x7fff_ffff_e0c0  [RSP]      對齊保留 / 暫存空間 (8 bytes)
            0x7fff_ffff_e0c8             payload_ptr (8-byte pointer, 0x5555555592a8)
            0x7fff_ffff_e0d0             local_copy[0..15] (16 bytes)
            0x7fff_ffff_e0e0             hdr (8 bytes: 58 4e 01 00 40 00 00 00)
            0x7fff_ffff_e0e8             Stack Canary (8 bytes: 例如 0x9a3f71c4028b5100)
            0x7fff_ffff_e0f0  [RBP]      Saved RBP (8 bytes，呼叫者的框架基底)
    高位址  0x7fff_ffff_e0f8  [RBP+0x08] Saved RIP (8 bytes，函式結束後的返回位址)
```

盯著這張真實位址地圖，有三個在實戰除錯時天天會碰到的細節：

第一是**小端序（Little-Endian）的視覺反差**。x86_64 與主流 ARM64 都是小端序，也就是「最低有效位元組放在最低的記憶體位址」。所以整數 `0x4e58` 躺在記憶體裡，用單一位元組印出來會是 `58 4e`；`0x00000040` 印出來則是 `40 00 00 00`。剛開始看 hex dump 時，千萬別把高低位元組看反了。

第二是**結構體欄位順序怎麼影響 Padding（填充空隙）**。在 `struct nexus_tlv_hdr` 裡，`magic`（2B，偏移 `+0`）、`type`（2B，偏移 `+2`）和 `len`（4B，偏移 `+4`）剛好各自對齊自身寬度的倍數，緊密湊成 `8 bytes`，沒有半個位元組的浪費。

但要是有工程師隨手把宣告順序寫成 `uint16_t magic; uint32_t len; uint16_t type;`，編譯器為了讓 4-byte 的 `len` 對齊 `+4` 的倍數，就會在 `magic` 後面偷塞 `2 bytes` 的空白填充，最後在 `type` 尾巴再補 `2 bytes` 讓整個結構對齊 4 的倍數。結果一個 `8 bytes` 的結構當場腫成 `12 bytes`，不光跟網路封包格式對不上，那些沒被初始化的填充空隙還會在回傳資料時把堆疊上的髒東西洩漏出去。

第三是**緩衝區跟控制資料的幾何距離**。你看堆疊上的 `local_copy`（從 `0x7fff_ffff_e0d0` 開始），它往高位址寫入時，如果沒有鎖死 `16 bytes` 的上限：寫超過 `16 bytes` 就會蓋掉隔壁的 `hdr`（`+0x10`）；寫超過 `24 bytes` 就會撞上 `Stack Canary`（`+0x18`）；寫超過 `40 bytes` 就會直接把 `Saved RIP`（`+0x28`）給覆寫掉。

---

### 四大現代二進位緩解機制與算術邊界

如果回到二十年前沒有防護的年代，攻擊者只要把一段機器碼（Shellcode）塞進剛剛那個 `local_copy` 陣列，再把 `Saved RIP` 改成 `0x7fff_ffff_e0d0`，函式一返回就會開始執行攻擊者的指令。為了堵死這條路，現代 Linux（如 Ubuntu 24.04 與 Debian 12 的預設工具鏈）築起了四道聯防，但每一道防線都有它守得住跟守不住的精確邊界。

#### 1. NX（No-Execute / DEP）：資料頁不准當指令跑

編譯器與連結器會在 ELF 的 `PT_GNU_STACK` 標頭裡把堆疊標記為 `RW`（不可執行），核心載入時就會把堆疊、堆積（`[heap]`）與資料段（`.data` / `.bss`）對應頁表項目的第 63 位元 `NX/XD` 設成 `1`。

只要 `RIP` 敢跳進這些標為 `RW-` 的資料頁抓指令，CPU 的 MMU 當場就會觸發頁面權限錯誤，由核心送出 `SIGSEGV` 殺掉行程。這招徹底廢掉了「把 Shellcode 寫進堆疊或堆積直接執行」的老路；但它的盲點也很清楚——**如果攻擊者不自己寫新指令，而是把 `Saved RIP` 導向記憶體裡原本就具有 `R-X` 權限的合法程式碼（像是 `libc.so.6` 裡面的 `system()` 或現成的指令片段 ROP gadgets），NX 就完全不會警報**。

#### 2. ASLR 與 PIE：把記憶體地圖打亂，以及 `28-bit` 熵值實算

既然攻擊者想借用現成的程式碼，作業系統就乾脆每次啟動都把記憶體位址打亂，這就是 **ASLR**（Address Space Layout Randomization，由 `/proc/sys/kernel/randomize_va_space` 控制：`0` 是全關，`1` 是隨機化堆疊、`mmap` 與 PIE 主程式，`2` 是現代預設值，連 `brk` 管理的 `[heap]` 也一起隨機化）。

但這裡有個許多團隊都踩過的大坑：**光靠作業系統開 ASLR 還不夠，主執行檔自己必須編譯成 PIE（`-fPIE -pie`，產出 `ET_DYN`）！** 如果編譯主程式時加了 `-no-pie`（產出 `ET_EXEC`），就算系統開了 `randomize_va_space = 2`，主程式的 `.text`、`.plt` 和 `.got.plt` 還是會釘死在固定的虛擬位址（通常是 `0x400000` 附近），攻擊者連洩漏位址都省了，直接拿主程式裡的固定位址就能動手。

那麼，當系統全開 ASLR + PIE 時，為什麼攻擊者從來不硬猜 64 位元位址，而是非得先找一個資訊洩漏漏洞？我們直接照全書基準模型（Linux x86_64 使用者空間 `mmap` 與堆積的典型隨機化熵為 **`28 bits`**，分頁大小為 **`4 KiB = 4,096 bytes`**）把帳算清楚：

因為所有 ELF 模組的載入基底都必須對齊 `4 KiB`（`2^12 = 0x1000`）的分頁邊界，**所以任何一個固定符號的虛擬位址，它最低的 `12 bits`（也就是十六進位的最後 3 碼，例如 `0x...6f0`）不管重開幾萬次都永遠不會變！** 頁級隨機化只會改變分頁以上的 `28 bits`。下面我們實際算算看，要硬猜中這 `28 bits` 得花多少時間：

```text
========================================================================
Worked Example：64 位元 28-bit ASLR 空間暴力猜測成本推導
========================================================================
已知基準規格：
  - 分頁大小 = 4 KiB = 4,096 bytes (最低 12 bits 頁內偏移固定不變)
  - Linux x86_64 mmap / 堆積典型 ASLR 隨機化熵 = 28 bits
  - 假設攻擊者每秒可發起猜測請求率 = 1,000 req/s

步驟 1：計算所有可能的頁對齊基底數量 N
  N = 2^28 = 268,435,456 個可能位址

步驟 2A：假設位址空間不會因為猜錯而重新隨機化 (例如未重新 execve 的 pre-fork 架構)
  - 不重複線性猜測（含猜中當次）的期望嘗試次數：
      E[tries] = (N + 1) / 2 = 268,435,457 / 2 = 134,217,728.5 次 (約 1.34 億次)
  - 在 1,000 req/s 速率下的期望耗時：
      T_fixed = 134,217,728.5 / 1,000 ≈ 134,217.73 s ≈ 1.34 × 10^5 s
      換算天數 = 134,217.73 / 86,400 ≈ 1.5534 天 ≈ 1.55 天

步驟 2B：假設每次猜錯都導致子行程 SIGSEGV 崩潰，並由 execve 重新洗牌位址 (現代常見架構)
  - 每次猜測都是獨立的伯努利試驗，單次命中機率 p = 1 / 2^28
  - 幾何分布下的期望嘗試次數：
      E[tries_reexec] = 1 / p = 2^28 = 268,435,456 次 (約 2.68 億次)
  - 在 1,000 req/s 速率下的期望耗時 (還沒算進行程重啟的冷卻時間)：
      T_reexec = 268,435,456 / 1,000 = 268,435.456 s ≈ 2.68 × 10^5 s ≈ 3.11 天

對照：32 位元舊系統 (假設僅 16-bit ASLR，N = 2^16 = 65,536)：
  - 期望耗時只需 32,768.5 / 1,000 ≈ 32.8 秒 (不重洗牌) 或 65,536 / 1,000 ≈ 65.5 秒 (每次重洗牌)，
    一分鐘左右就能在實戰中硬撞出來。

算術結論：
  在開啟 PIE 與 28-bit ASLR 的 64 位元服務上，硬猜隨機化基底平均要打 1.34 億到 2.68 億次請求，
  耗時 1.55 天到 3.11 天，而且會在目標伺服器上炸出上億次 SIGSEGV 崩潰告警！
  相反地，只要攻擊者先找到一個「資訊洩漏 (Info Leak)」破口，偷出目標模組裡任何一個已知偏移的指標，
  拿洩漏位址減去固定的區段與頁內偏移，就能在 O(1) 一次請求內把 28-bit 的未知數直接歸零。
========================================================================
```

#### 3. Stack Canary（堆疊金絲雀）：擋在回傳位址前的哨兵

開啟 `-fstack-protector-strong`（現代主流預設值）或 `-fstack-protector-all` 後，編譯器會在含有局部陣列或對局部變數取址的函式開頭加一段防護。

它會從執行緒局部儲存（TLS）暫存器 `fs:0x28`（x86_64 Linux 的 `__stack_chk_guard`，在行程啟動時由核心透過輔助向量 `AT_RANDOM` 餵入亂數初始化）讀出一個 `8-byte` 的隨機值，塞進堆疊上「局部緩衝區」與「`Saved RBP` / `Saved RIP`」正中間。

等函式準備執行 `ret` 返回前，再把這個槽位的值拿出來跟 `fs:0x28` 對答案；只要發現不一致，就知道剛剛發生了越界寫入，立刻跳進 `__stack_chk_fail` 發出 `SIGABRT` 自殺，絕不執行後面那條會跳去歪路的 `ret`。

這裡有一個非常精巧的細節：**glibc 產生的 64 位元 Stack Canary，最低有效位元組（小端序放在最低位址的第一個 byte）永遠固定是 `0x00`**（例如 `0x9a3f71c4028b5100`）。

為什麼要故意犧牲 8 個位元的隨機性填 `0x00`？因為在 C 語言裡，字串是靠 `\0`（`0x00`）結尾的。如果程式不小心寫出了沒補 `\0` 的字串印出漏洞（像 `printf("%s", local_buf)`），印到 Canary 的第一個位元組 `0x00` 時就會自動停住，當作天然的煞車皮。

但反過來說，如果程式有「定長越界讀取」，或者有一個「剛好能多寫 1 個 byte（Off-by-one）」的破口，讓攻擊者先把那個 `0x00` 蓋成普通字元 `'A'`，接著再呼叫 `printf("%s", local_buf)`，後面那 7 個隨機位元組的 Canary 就會連帶被一口氣印出來！

#### 4. RELRO（Relocation Read-Only）：把動態連結表鎖成唯讀

前面看過，Lazy Binding 為了在執行期填寫函式位址，把 `.got.plt` 留成了可寫狀態。**RELRO** 就是為了保護 `.init_array`、`.fini_array`、`.dynamic` 和 GOT 表不被任意寫入篡改而設計的，分成三種等級：

如果設成 **No RELRO**（`-Wl,-z,norelro`），整塊重定位表與 `.got.plt` 在程式跑起來之後全都是 `RW-` 可讀寫的，隨便一個任意寫入漏洞就能改寫函式指標。

如果是許多編譯器預設的 **Partial RELRO**（`-Wl,-z,relro`），連結器會把啟動時就能算好的 `.init_array`、`.fini_array`、`.dynamic` 以及非延遲綁定的 `.got` 集中放進 `PT_GNU_RELRO` 片段，由動態連結器在跳進 `main()` 之前呼叫 `mprotect` 鎖成 `R--` 唯讀；**但是為了保留 Lazy Binding，負責外部函式跳轉的 `.got.plt` 依然留在保護區外面，在執行期照樣是 `RW-` 可寫的！**

要真正封死 GOT 覆寫攻擊，就必須開啟 **Full RELRO**（`-Wl,-z,relro,-z,now`）。多了 `-z,now`（寫入 `DT_BIND_NOW` 或 `NOW` 旗標）之後，動態連結器會在程式啟動階段就一口氣把所有外部函式的真實位址全查好填進 `.got.plt`，接著把包含 `.got` 與 `.got.plt` 在內的整張表統統鎖進 `PT_GNU_RELRO` 變成 `R--` 唯讀。雖然啟動時會多花一點點解析符號的時間，但對於長駐在記憶體裡的後端微服務或 `libnexus-parse` 外掛來說，這點啟動成本完全微不足道，卻能徹底拔掉 `.got.plt` 被篡改的風險。

---

## 故障模式與防禦

看懂了 ELF 載入跟四大防線的運作原理後，我們回頭檢查實際專案在編譯和部署原生模組時，最常因為哪些設定疏忽而讓防線破功。

### 故障模式 1：主程式忘了開 PIE，拖垮整套 ASLR

有些團隊把 `libnexus-parse.so` 編譯成了位置無關程式碼（`-fPIC`），作業系統也開了 `randomize_va_space = 2`，卻在編譯 C/C++ 主執行檔時順手加了 `-no-pie`（產出 `ET_EXEC`）。結果就是共享函式庫雖然每次都在隨機位址，主執行檔自己的 `.text` 與 `.plt` 卻永遠釘在 `0x400000`。一旦發生堆疊溢位，攻擊者根本不需要管 `libc` 在哪裡，光拿主程式裡固定位址的指令片段（ROP gadgets）跟 PLT 呼叫就能直接拼出攻擊鏈。

### 故障模式 2：手寫組合語言漏標 `.note.GNU-stack`，害整個行程的 NX 被關掉

在寫密碼學加速或高效能編解碼模組時，工程師偶爾會在 C/Rust 專案裡混入手寫的 `.S` 組合語言檔。如果那個 `.S` 檔尾巴忘了加上一行 `.section .note.GNU-stack,"",@progbits`（而且連結時也沒強制加上 `-Wl,-z,noexecstack`），傳統連結器就會保守地以為「這個模組需要在堆疊上執行指令」，進而把生出來的執行檔或 `.so` 的 `PT_GNU_STACK` 標成恐怖的 **`RWE`**（可讀、可寫、可執行）！這會導致新版 glibc 直接拒絕載入該模組，或者在允許載入的環境裡把整個行程的堆疊變成可執行，一舉廢掉 NX 防線。

### 故障模式 3：以為預設編譯就是 Full RELRO

很多資安檢核表只寫了「確認開啟 RELRO」，工程師跑工具看到 `Partial RELRO` 就打勾過關。就像前面拆解過的，Partial RELRO 下面的 `.got.plt` 根本還是可寫的（`RW-`）。只要程式裡有一個任意位址寫入或格式化字串漏洞，攻擊者照樣能去改寫 `free@got.plt` 或 `memcpy@got.plt`。要鎖死 `.got.plt`，連結參數一定要明確加上 `-Wl,-z,relro,-z,now`。

### 故障模式 4：C 結構體的 Padding 空隙沒清零就往外送

假設你在 C 裡面宣告了一個要回傳給 Node.js 或寫進 Socket 的回應結構體，裡面因為欄位對齊夾了 `4 bytes` 的編譯器填充空隙（Padding）。如果你在堆疊上宣告了這個結構體 `struct resp r;`，只對具名欄位賦值（`r.code = 200; r.len = 64;`），然後就直接 `send(fd, &r, sizeof(r), 0)` 把整塊結構送出去——注意，**C 語言對欄位賦值時，絕對不會幫你把中間的 Padding 位元組清成零！** 那 `4 bytes` 裡面裝的，就是上一個函式留在堆疊上的殘留資料（常常正好是半截 Stack Canary 或 `libc` 指標），就這樣白白送給了外部呼叫端。

### 故障模式 5：Pre-fork 多行程架構不呼叫 `execve`，讓 28-bit ASLR 與 Canary 當場失效

有些傳統 C 網路服務為了省下建立行程的開銷，會在主行程 `main()` 初始化完之後，直接用 `fork()` 生出一群 Worker 子行程來接請求，而且子行程 crash 之後主行程又繼續 `fork()` 新的出來（沒有呼叫 `execve()` 重新載入執行檔）。

這是二進位防護最致命的架構陷阱！因為 `fork()` 的語意就是「完整複製父行程當下的虛擬記憶體空間與 TLS」，**這代表所有 `fork()` 出來的子行程，它們的 ASLR 基底位址跟 `fs:0x28` 裡的 Stack Canary 長得一模一樣！**

原本在 `28-bit` ASLR 與 `56-bit` 隨機 Canary 保護下要猜上億次的不可能任務，在這種 Pre-fork 架構下，攻擊者只要每次故意多寫 1 個 byte 去試探 Canary：猜錯了子行程崩潰、猜對了子行程正常回傳，一個 byte 最多試 256 次。

7 個隨機 byte **最壞只要試 `256 × 7 = 1,792` 次**就能把整根 Canary 摸出來，接著再用同樣手法把 `Saved RIP` 也一併試探出來！因此，凡是遇到子行程異常崩潰重啟，架構上一定要透過 `fork() + execve()` 重新洗牌隨機數與記憶體映射。

### 原生模組上線前強制硬化檢核表

| 防禦目標 | 編譯／連結／系統強制參數 | 用 `readelf` / 系統檢查的合格特徵 | 一眼抓出的危險訊號 |
|---|---|---|---|
| **NX（資料不可執行）** | 連結加 `-Wl,-z,noexecstack`；手寫 `.S` 必加 `.note.GNU-stack` | `readelf -l` 看到 `GNU_STACK` 的 Flags 為 `RW` | Flags 出現 `RWE` |
| **PIE + 完整 ASLR** | 執行檔加 `-fPIE -pie`、動態庫加 `-fPIC`；系統 `randomize_va_space = 2` | `readelf -h` 的 Type 為 `DYN`（執行檔在 `readelf -d` 另有 `FLAGS_1: PIE`） | 執行檔 Type 為 `EXEC` |
| **Stack Canary** | 編譯加 `-fstack-protector-strong`（高風險解析器用 `-fstack-protector-all`） | `readelf -s` 可以查到 `__stack_chk_fail` 符號 | 找不到 `__stack_chk_fail` |
| **Full RELRO** | 連結加 `-Wl,-z,relro,-z,now` | `readelf -l` 有 `GNU_RELRO`，且 `readelf -d` 有 `(BIND_NOW)` 或 `NOW` | 缺 `GNU_RELRO` 或沒看到 `NOW` |
| **防 Padding 洩漏** | 跨邊界傳出前改用逐欄序列化，或先 `memset(&s, 0, sizeof(s))` 並加 `-ftrivial-auto-var-init=zero` | 用 `pahole` 檢查無意外空隙；所有外傳緩衝區先清零 | 局部結構體沒 `memset` 就整塊 `memcpy`/`send` 出去 |

---

## 動手做

- **難度**：入門至進階
- **預估時間**：50 分鐘

現在我們親手寫一個 `libnexus-parse` 的最小 C 基準程式，分別用「全關保護」跟「現代硬化」兩組參數編譯，再用 `readelf`、`objdump` 與 `gdb` 驗證剛剛學到的每一條硬體與記憶體規則。本實驗在本地 Linux x86_64 環境（原生 Linux、WSL2 或 `ubuntu:24.04` Docker 容器）就能跑，需要安裝 `gcc`、`binutils`（含 `readelf`、`objdump`）與 `gdb`。

### 步驟 1：建立 `nexus_parse.c` 並編譯兩組對照執行檔

建立 `nexus_parse.c`，裡面實作了固定 `8-byte` 的 TLV 檔頭（`magic = 0x4e58`、合法 `len <= 65536`）以及在堆疊上做局部複製的 `parse_tlv_frame` 函式：

```c
// nexus_parse.c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NEXUS_MAGIC 0x4e58
#define NEXUS_MAX_PAYLOAD 65536

struct nexus_tlv_hdr {
    uint16_t magic;
    uint16_t type;
    uint32_t len;
};

__attribute__((noinline))
int parse_tlv_frame(const uint8_t *raw_buf, size_t raw_len) {
    struct nexus_tlv_hdr hdr;
    uint8_t local_copy[16] = {0};
    const uint8_t *payload_ptr;

    if (raw_len < sizeof(struct nexus_tlv_hdr)) {
        return -1;
    }
    memcpy(&hdr, raw_buf, sizeof(hdr));
    if (hdr.magic != NEXUS_MAGIC || hdr.len > NEXUS_MAX_PAYLOAD) {
        return -2;
    }
    if (raw_len < sizeof(hdr) + (size_t)hdr.len) {
        return -3;
    }

    payload_ptr = raw_buf + sizeof(hdr);
    size_t preview = hdr.len < sizeof(local_copy) ? hdr.len : sizeof(local_copy);
    if (preview > 0) {
        memcpy(local_copy, payload_ptr, preview);
    }

    printf("[nexus-parse] magic=0x%04x type=0x%04x len=%u preview0=0x%02x\n",
           hdr.magic, hdr.type, hdr.len, preview > 0 ? local_copy[0] : 0);
    return 0;
}

int main(void) {
    uint8_t pkt[72];
    memset(pkt, 0x41, sizeof(pkt));

    struct nexus_tlv_hdr hdr = {
        .magic = NEXUS_MAGIC,
        .type  = 0x0001,
        .len   = 64
    };
    memcpy(pkt, &hdr, sizeof(hdr));

    void *heap_probe = malloc(32);
    printf("[maps] main=%p heap=%p stack=%p printf=%p\n",
           (void *)main, heap_probe, (void *)&pkt, (void *)printf);

    int rc = parse_tlv_frame(pkt, sizeof(pkt));
    free(heap_probe);
    return rc == 0 ? 0 : 1;
}
```

接著用下面兩道指令，分別編出關掉所有防護的 `nexus_vuln` 與全開防護的 `nexus_hardened`：

```bash
# 1. 無保護版（關 Canary、開放堆疊可執行、關 PIE、關 RELRO）
gcc -g -O0 -fno-stack-protector -z execstack -no-pie -Wl,-z,norelro \
    nexus_parse.c -o nexus_vuln

# 2. 現代硬化版（開 Strong Canary、NX、PIE、Full RELRO）
gcc -g -O2 -fstack-protector-strong -fPIE -pie -Wl,-z,relro,-z,now \
    nexus_parse.c -o nexus_hardened
```

### 步驟 2：用 `readelf` 比對 ELF 結構並實測 ASLR 低 12 bits 不變性

先跑 `readelf` 看看兩支檔案的 ELF 標頭與載入片段差在哪裡：

```bash
readelf -h nexus_vuln | grep -E "Type:|Entry"
readelf -l nexus_vuln | grep -E "GNU_STACK|GNU_RELRO" -A 1

readelf -h nexus_hardened | grep -E "Type:|Entry"
readelf -l nexus_hardened | grep -E "GNU_STACK|GNU_RELRO" -A 1
readelf -d nexus_hardened | grep -E "BIND_NOW|FLAGS"
```

接著連續執行兩次 `./nexus_hardened`，仔細比對畫面印出來的四個記憶體位址（`main`、`heap`、`stack`、`printf`），看看哪些位元變了、哪些位元動都沒動。

### 步驟 3：進 GDB 驗證 ABI 傳參、16-byte 對齊、小端序與 Canary

用 `gdb -q ./nexus_hardened` 載入硬化版程式，在 `parse_tlv_frame` 的第一條機器指令設下斷點（注意要用 `break *parse_tlv_frame` 才能停在還沒跑 Prologue 的第一行指令），檢查剛踏進函式時的 `RDI`、`RSI`、`$rsp % 16` 的餘數、`$rdi` 指到的 `8-byte` TLV 檔頭位元組順序，以及寫入堆疊的 Stack Canary 值。

### 外部靶場對照檢查點（pwn.college）

做完本地實驗後，推薦到開源系統安全平台 [pwn.college](https://pwn.college/) 挑組合語言、GDB 除錯與記憶體佈局的基礎關卡練手。初學者在靶場最容易卡關的三個盲點，正好就是我們今天推導的重點：
1. 把 `x/gx` 印出來的 64 位元整數跟 `x/8bx` 印出來的逐位元組小端序排列搞混。
2. 在剛進函式第一行指令時，忘了 `call` 已經把 `Saved RIP` 壓在 `[rsp]` 上，誤把 `[rsp]` 當成第一個局部變數。
3. 手動跳轉呼叫 `libc` 的 `printf` 或 `system` 前，忘了確定 `RSP` 有沒有對齊 `16` 的倍數，結果死在 `movaps` 的對齊檢查上。

---

### 參考解答

#### 1. `readelf` 與 ASLR 實測結果

跑完 `readelf` 會看到非常鮮明的對比：`nexus_vuln` 的 Type 是 `EXEC`（固定位址）、`GNU_STACK` 帶著危險的 `RWE` 旗標，而且完全沒有 `GNU_RELRO`；反觀 `nexus_hardened` 的 Type 是 `DYN`（PIE 位置無關執行檔）、`GNU_STACK` 只有 `RW`、具備 `GNU_RELRO` 片段，而且 `.dynamic` 表裡明確標著 `BIND_NOW`（或 `FLAGS_1: NOW`），代表連 `.got.plt` 也在進入 `main()` 前鎖成唯讀了。

再看連續跑兩次 `./nexus_hardened` 的輸出：

```text
第 1 次：[maps] main=0x55a8c421b0c0 heap=0x55a8e93f12a0 stack=0x7ffd8a4c1b10 printf=0x7f93a12606f0
第 2 次：[maps] main=0x561b398400c0 heap=0x561b61d092a0 stack=0x7fff19c24630 printf=0x7f1e88e606f0
```

請盯著 `main` 跟 `printf` 的最後三碼看：不管重跑幾次，前面的高位頁基底怎麼亂跳，`main` 的結尾永遠是 `0c0`、`printf` 的結尾永遠是 `6f0`！這就親眼證實了我們前面算的：因為模組映射必須對齊 `4 KiB`（`0x1000`）分頁邊界，符號位址最低的 `12 bits`（十六進位末 3 碼）頁內偏移是完全固定不變的（至於 `stack` 局部變數，因為 Linux 核心除了頁級隨機化之外，還會在初始堆疊頂端額外加一層次頁級的隨機位移，所以連末 3 碼也會跟著變）。

#### 2. GDB 斷點驗證實錄

在 GDB 裡停在 `*parse_tlv_frame` 第一條指令時的標準檢查流程如下：

```gdb
(gdb) break *parse_tlv_frame
(gdb) run
(gdb) info registers rdi rsi rsp
# 驗證剛踏進函式時，因 call 剛壓入 8-byte Saved RIP，($rsp % 16) 必定等於 8：
(gdb) print $rsp % 16
$1 = 8
(gdb) x/gx $rsp
# 檢視 RDI 指向的 8-byte TLV 檔頭在記憶體裡的小端序排列：
(gdb) x/8bx $rdi
0x7fff...: 0x58  0x4e  0x01  0x00  0x40  0x00  0x00  0x00
```

你可以清楚看到，`magic = 0x4e58` 在記憶體裡真的排成 `0x58 0x4e`，而 `len = 64`（`0x40`）則排成 `0x40 0x00 0x00 0x00`。接著用 `disassemble parse_tlv_frame` 找到那行 `mov rax, QWORD PTR fs:0x28`，用 `nexti` 單步走過它之後印出 `info registers rax`，就會看到像 `0x9a3f71c4028b5100` 這樣最後兩碼固定為 `00` 的 Stack Canary 哨兵值。

---

## 自我檢核

- **難度**：入門至進階
- **預估時間**：20 分鐘

先別看答案，試著用這一章建立的記憶體地圖與算術規則，回答下面 4 個實戰問題：

1. **為什麼跳過 `call` 直接跳進 `libc` 函式會當場崩潰**：在 x86_64 Linux 上，假設某支程式發生堆疊溢位，呼叫端利用 `ret` 指令把控制流直接拐到 `libc` 裡某個函式的第一行指令（沒有經過正常的 `call` 指令）。為什麼程式常常會在該函式內部的 `movaps` 指令處觸發 `SIGSEGV` 崩潰？如果同樣的堆疊未對齊發生在 ARM64（AArch64）伺服器上，硬體報錯的時機有什麼不同？
2. **Partial RELRO 的防護盲區**：資安掃描工具對一支 C 語言寫的微服務顯示 `RELRO: Partial RELRO`。請問此時該行程的 `.got` 與 `.got.plt` 哪一個已經鎖成唯讀、哪一個還能寫入？為什麼編譯器預設不乾脆把兩個都鎖死？
3. **從單一洩漏指標反推 `libc` 基底位址**：假設某個 64 位元服務因為未清零的 Struct Padding，在回應裡不小心洩漏出一個確定指向 `libc` 內部 `puts` 函式的指標 `0x7f8b4c280ed0`。你手邊查到目標伺服器使用的 `libc.so.6` 檔案裡，`puts` 相對於 `libc` 起點的固定偏移是 `0x80ed0`。請算出這個行程當下 `libc` 的載入基底位址是多少？為什麼光看洩漏位址的最後三碼 `ed0`，就能幫我們快速確認目標是不是同一個版本的 `libc`？
4. **抓出 Pre-fork 架構的安全假設破綻**：某位系統架構師拍胸脯保證：「我們的 64 位元 C 解析服務開了 `28-bit` ASLR 跟 Stack Canary，而且為了極致效能採用父行程 `fork()` Worker 的架構（Worker 崩潰後由父行程立刻再 `fork()` 一個補上）。就算裡面有堆疊緩衝區溢位，駭客也得猜上億次才可能成功！」請指出這段話裡最致命的兩個破綻。

---

### 參考解答

1. **為什麼跳過 `call` 會死在 `movaps`**：
   - x86_64 System V ABI 規定在執行 `call` 之前 `RSP % 16 == 0`，`call` 把 8 位元組的回傳位址壓進堆疊後，進到函式第一行時 `RSP % 16` 應該是 `8`；這樣函式開頭執行 `push rbp`（再減 8）之後，函式內部的堆疊框架才會剛好回到 `16` 的倍數。如果略過 `call`、直接靠 `ret` 跳進函式第一行，進去時的 `RSP % 16` 反而是 `0`，等它自己跑完 `push rbp` 後內部框架就歪了 `8 bytes`（變成 `mod 16 == 8`）。後面只要一跑到要求記憶體位址必須 16-byte 對齊的 SSE 指令 `movaps [rsp + offset], xmm0`，CPU 就會當場拋出 `#GP` 例外導致 `SIGSEGV`（這也是第 22 章會提到、為什麼有時得多墊一個單純的 `ret` 指令來把 8 位元組對齊補回來的原因）。
   - 如果換到 **ARM64（AArch64）** 上，因為 Linux 預設開啟了使用者態（EL0）硬體層級的 `SP` 16-byte 對齊檢查（`SCTLR_EL1.SA0`），根本不用等到跑向量指令，只要任何一條普通載入或儲存指令拿未對齊 `16 bytes` 的 `SP` 當基底去碰記憶體，CPU 當場就會拋出 Alignment Fault。
2. **Partial RELRO 的防護盲區**：
   - 在 `Partial RELRO` 下，`.init_array`、`.fini_array`、`.dynamic` 和非延遲綁定的 **`.got` 已經鎖成唯讀（`R--`）**，但負責外部函式跳轉的 **`.got.plt` 依然是可讀寫（`RW-`）** 的。
   - 預設不鎖死 `.got.plt`，是為了保留 **Lazy Binding**（延遲綁定）的啟動速度優勢——等程式第一次真的呼叫某個外部函式時，才讓動態連結器去查位址並寫回 `.got.plt`。要徹底鎖死它，連結時必須加上 `-Wl,-z,relro,-z,now` 開啟 **Full RELRO**。
3. **從單一洩漏指標反推 `libc` 基底位址**：
   - 拿洩漏出來的執行期真實位址減去固定偏移：`0x7f8b4c280ed0 - 0x80ed0 = 0x7f8b4c200000`。算出來的基底位址最後三碼必定是 `000`（對齊 `4 KiB = 0x1000` 分頁邊界）。
   - 因為頁級 ASLR 只會隨機打亂 `4 KiB` 分頁以上的 `28 bits`，分頁內的低 `12 bits`（十六進位最後三碼 `ed0`）完全由該函式在 `libc.so.6` 檔案裡的固定偏移決定，怎麼重開都不會變。所以實戰中看到洩漏指標的末三碼是 `ed0`，就能立刻拿來核對候選 `libc` 版本裡 `puts` 的偏移末三碼是不是也是 `ed0`。
4. **Pre-fork 架構的兩個致命破綻**：
   - 第一個破綻是**只 `fork()` 不 `execve()` 會讓所有子行程共用同一套隨機數**。`fork()` 出來的 Worker 完美複製了父行程的記憶體映射與 TLS，所以每個子行程的 ASLR 位址跟 Stack Canary 完全一樣！只要漏洞允許每次多塞 1 個 byte 去試探 Canary，猜錯頂多弄死一個 Worker，父行程又會立刻 `fork()` 一個一模一樣的新 Worker 出來讓攻擊者繼續試。7 個未知的 Canary 位元組最壞只要試 `256 × 7 = 1,792` 次就能全猜出來，根本不用上億次。
   - 第二個破綻是**忽略了資訊洩漏（Info Leak）漏洞**。就算每次崩潰都乖乖重新 `execve()` 洗牌，只要服務裡有另一處越界讀取或沒清零的 Struct Padding 能洩漏出半個指標，攻擊者發 `1` 筆請求就能算出基底位址，完全不必跟 `28-bit` ASLR 硬碰硬。

---

## 延伸閱讀

- **System V Application Binary Interface — AMD64 Architecture Processor Supplement**（https://gitlab.com/x86-psABIs/x86-64-ABI）：查閱 x86_64 暫存器傳參順序、Caller/Callee-saved 保存責任與 `16-byte` 堆疊對齊不變量的第一手官方規格。
- **Procedure Call Standard for the Arm 64-bit Architecture (AAPCS64)**（https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst）：對照 ARM64 的 `X0`–`X7` 傳參、`X30`（`LR`）回傳位址管理與硬體 `SP` 對齊規則。
- **Linux Man Pages: `elf(5)`, `proc_pid_maps(5)`, `ld.so(8)`**（https://man7.org/linux/man-pages/man5/elf.5.html）：深入了解 ELF 區段與載入片段結構、`/proc/<pid>/maps` 格式以及動態連結器 `LD_BIND_NOW` 的底層行為。
- **Red Hat Security Blog — Hardening ELF Binaries Using Relocation Read-Only (RELRO)**（https://www.redhat.com/en/blog/hardening-elf-binaries-using-relocation-read-only-relro）：清楚比較 Partial RELRO 與 Full RELRO 在區段佈局、啟動耗時與防禦邊界上的實務取捨。
- **pwn.college System Security Platform**（https://pwn.college/）：透過免費的互動式系統安全靶場，親手練習組合語言判讀、小端序記憶體檢視與 GDB 斷點除錯。
