# 第 23 章：堆積管理器解剖與基礎記憶體損毀原語

第 22 章拆解了堆疊框架的線性配置：區域變數隨著函式呼叫建立，隨著返回而銷毀，位址與生命週期都綁在單一呼叫鏈上。但真實的高併發網路服務不可能把所有資料都塞進固定大小的堆疊緩衝區。當 **NexusPay** 的原生模組 `libnexus-parse`（第 1 章定義的信任邊界 TB-4）同時解析多筆上限 `65,536 bytes`（`64 KiB`，加上 8 位元組檔頭共 `65,544 bytes`）的 TLV 封包，並在非同步管線間傳遞結果時，這些變長物件都必須交給動態記憶體配置器在**堆積**（heap）上管理。

堆積給了程式極大的彈性，卻也徹底改寫了記憶體安全的遊戲規則。物件的生命週期不再跟著大括號走，而是靠成對的 `malloc()` 與 `free()` 手動維護。

更致命的是，glibc 預設配置器 `ptmalloc2` 為了省空間，採用**帶內中繼資料**（in-band metadata）設計——紀錄區塊大小與鏈結關係的標頭就緊貼在使用者資料前後，甚至在物件釋放後直接拿原本存資料的空間來放雙向指標。本章不談武器化的攻擊腳本，而是從底層架構與防禦視角徹底解剖 `ptmalloc2` 的資料結構、狀態機與現代緩解機制，看穿懸垂指標（UAF）、雙重釋放（Double Free）與堆積溢位打破了哪些不變量，並學會用 GDB 與 AddressSanitizer（ASan）在本地抓出這類破口。

---

## 從你已知的出發

為什麼程式裡不過是多寫了一行 `free(buf)`，或是往 `24 bytes` 的緩衝區寫了第 `25` 個位元組，下一次呼叫完全無關的 `malloc()` 時，整個伺服器行程就會當場噴出 `SIGABRT` 崩潰，甚至讓駭客改寫相鄰物件的權限旗標？

因為在 Linux 的 C/C++ 與 `libnexus-parse` 這類原生擴充模組裡，`malloc()` 並不是每次都去敲作業系統核心的大門。如果每要 `24 bytes` 都呼叫 `brk` 或 `mmap`，系統呼叫的切換成本會把效能拖垮；要是每個小物件都獨佔一整頁（`4 KiB` 即 `4,096 bytes`），記憶體更會瞬間塞爆。

所以使用者空間裡的 **`ptmalloc2`** 扮演了記憶體批發商的角色：它先用 Arena 結構向核心批發一大塊連續虛擬記憶體，自己在裡面切成大小不一的 **Chunk**，再把釋放回來的區塊依尺寸放進不同等級的回收桶（**Bin**）裡重複利用。在 64 位元 x86_64 架構下，所有 Chunk 位址與總大小都強制對齊 `16 bytes`（`0x10`），最小區塊為 `32 bytes`（`0x20`）。由於硬體 MMU 只管得到 `4 KiB` 頁面的讀寫權限（`RW-`），同一頁裡的業務資料跟配置器的控制帳本完全沒有硬體隔離；只要你越界寫了幾個位元組，或是拿著已經歸還的舊指標繼續讀寫，塗改到的就是配置器自己的帳本。

---

## 機制與推導

### 攻擊者目標與實質影響

當研究員或攻擊者在 `libnexus-parse` 或長駐 C/C++ 服務裡抓到堆積記憶體損毀漏洞時，追求的破壞通常分成三個層次：

第一層是**擊穿 `28-bit` ASLR 的資訊洩漏**（Heap / Libc Address Disclosure）。Linux x86_64 使用者空間的堆積映射雖然有 `28 bits` 的隨機化熵值（最低 `12 bits` 為 `4 KiB` 頁內固定偏移），但只要程式能意外讀到已經釋放的 Chunk（UAF Read），原本放業務資料的位置早就被 `ptmalloc2` 換成了鏈結指標。如果這個區塊剛好是 `tcache` 回收桶裡的第一個節點，讀出來的值直接就是堆積分頁基底 `pos >> 12`；如果區塊進了 `unsorted bin`，它的 `fd` 與 `bk` 指標更會直接指向 `libc.so.6` 資料段裡的 `main_arena` 表頭。因為 `main_arena` 相對於 `libc` 基底的偏移在固定版本下是常數，攻擊者只要讀出這 `8 bytes`，就能一舉算出整個 `libc` 的真實載入位址。

第二層是**不碰控制流的業務邏輯與權限竄改**（In-Place Object Corruption）。在物件重用或相鄰堆積溢位的場景下，攻擊者根本不需要去算複雜的配置器標頭。只要覆寫同一頁裡相鄰結構體的布林驗證旗標、租戶 ID、資料長度上限或回呼指標，就能直接穿破應用程式的資料平面與授權邊界，達成第 1 章提過的跨租戶提領或帳本灌水。

第三層則是**構造可控配置與任意寫入原語**（Controlled Allocation / Arbitrary Write）。當攻擊者先拿到位址洩漏、足以滿足現代 Safe-Linking 校驗後，就能透過竄改空閒 Chunk 的尺寸標頭或串列指標，哄騙配置器在後續 `malloc()` 時回傳兩塊互相重疊的記憶體，甚至直接把目標變數的位址當成新區塊配發出來。這也是第 24 章探討進階堆積防護與標準串流結構的基礎。

在企業產品安全（Product Security）實務上，遇到這類堆積漏洞時不能只憑感覺喊「高風險」，而是要統一用 **CVSS v4.0** 向量搭配 **EPSS**（Exploit Prediction Scoring System）機率分數與 **CISA KEV** 狀態來分流。舉例來說，`libnexus-parse` 裡一個需要特定封包順序再加上額外資訊洩漏才能突破 Safe-Linking 的 UAF，在 CVSS v4.0 中會標記為具備攻擊前置需求（`AT:P`，Attack Requirements: Present），並分別評估對受影響系統（Vulnerable System）與後續系統（Subsequent System，如宿主 API 閘道）的機密性、完整性與可用性衝擊；接著再對照 EPSS 分數與 KEV 清單，決定要排入 `24 小時` 嚴重級還是 `7 天` 高危級 SLA 修補（詳見第 33 至 36 章）。

---

### `ptmalloc2` 記憶體架構與 `malloc_chunk` 佈局

為了讓多執行緒同時配置記憶體時不會卡在同一把鎖上，`ptmalloc2` 把行程的動態記憶體分成多個獨立的 **Arena**。主執行緒預設用 `main_arena`，底層靠 `brk()` 系統呼叫往高位址擴張連續資料段（開啟 ASLR 時起點會加上隨機偏移）；當多個工作執行緒同時搶鎖時，`ptmalloc2` 就會改用 `mmap()` 建立額外的 `non_main_arena`（64 位元下數量上限通常為 CPU 核心數的 `8` 倍），讓不同執行緒各自操作獨立的互斥鎖與回收桶。

每個 Arena 的最高位址端都留著一塊還沒切出去的連續空間，叫做 **Top Chunk**（俗稱 Wilderness）。當所有現成的回收桶都找不到合適區塊時，配置器就從 Top Chunk 低位址端切一塊出來，並把 Top Chunk 邊界往高處推；要是連 Top Chunk 都不夠了，才向作業系統申請擴張，或是對超過閾值（64 位元預設 `mp_.mmap_threshold` 初始值為 `128 KiB`）的大請求直接呼叫獨立的 `mmap()`。

翻開 `glibc` 原始碼（`malloc/malloc.c`），不管區塊目前正在被程式使用、還是已經釋放進回收桶，全都共用同一個 `struct malloc_chunk` 結構：

```text
  已配置 Chunk (Allocated)                     已釋放 Chunk (Freed in unsorted/small/large bin)
┌──────────────────────────────────────┐     ┌──────────────────────────────────────┐
│ +0x00: mchunk_prev_size (8 B)        │     │ +0x00: mchunk_prev_size (8 B)        │
│   (若 P=1，此槽位屬於前一個 Chunk 的 │     │   (前一個物理相鄰 Chunk 的大小)      │
│    最後 8 bytes 使用者負載！)        │     ├──────────────────────────────────────┤
├──────────────────────────────────────┤     │ +0x08: mchunk_size | A | M | P (8 B) │
├──────────────────────────────────────┤     ├──────────────────────────────────────┤
│ +0x10: 使用者資料起點 (malloc 回傳值)│     │ +0x10: fd (指向下一筆 free chunk)    │
│        ...                           │     │   (若在 tcache 則為 next 指標)       │
│        使用者負載與對齊填充          │     ├──────────────────────────────────────┤
│        (可借用下一塊的 +0x00 槽位)   │     │ +0x18: bk (指向上一筆 free chunk)    │
└──────────────────────────────────────┘     │   (若在 tcache 則為防雙釋放 key)     │
  註：tcache / fastbin 的空閒塊維持 P=1      ├──────────────────────────────────────┤
      以抑制合併，不寫入下一塊 prev_size      │ +0x20: fd_nextsize (僅 large bin)    │
                                             │ +0x28: bk_nextsize (僅 large bin)    │
                                             └──────────────────────────────────────┘
```

盯著這張圖看，有四條硬規則是拆解所有堆積行為的鑰匙：

第一，**使用者拿到的指標不是 Chunk 的起點**。呼叫 `malloc()` 回傳給你的指標 `mem`，其實指向 `malloc_chunk` 起點 `p` 往後偏移 `0x10` 的位置（跳過開頭的 `mchunk_prev_size` 與 `mchunk_size` 兩個 `8-byte` 欄位）。所以用 GDB 檢查某個指標 `mem` 的標頭時，永遠要往前減 `0x10`（也就是看 `mem - 0x10`）。

第二，**大小欄位的最低 3 個位元藏著狀態旗標**。因為所有 Chunk 的實體大小都是 `16 bytes`（`0x10`）的整數倍，換成十六進位時最後一個字（最低 4 個位元）一定都是 `0`。`ptmalloc2` 就拿最低 3 個位元（`SIZE_BITS = 0x7`）來存三個旗標，要算真實大小時再用 `size & ~0x7` 把旗標遮掉：
- **`P`（`PREV_INUSE = 0x1`）**：代表**物理位址緊鄰在前的上一個 Chunk** 是不是「不可向後合併」。當 `P == 1` 時，表示前一個區塊正在使用中，或是正待在刻意延遲合併的快取串列（像 `tcache` 或 `fastbin` 都會維持下一塊的 `P == 1`），這時配置器絕不會往前合併（backward coalescing）。只有當 `P == 0` 時，才代表前一個區塊已經釋放且允許合併，這時本區塊開頭 `+0x00` 的 `mchunk_prev_size` 才會生效，裡面存著前一個空閒區塊的真實大小。
- **`M`（`IS_MMAPPED = 0x2`）**：代表這塊記憶體不是從 Arena 切出來的，而是 `malloc()` 直接用 `mmap()` 向核心要來的獨立映射。這種區塊在 `free()` 時不會進任何回收桶，而是直接 `munmap()` 還給作業系統。
- **`A`（`NON_MAIN_ARENA = 0x4`）**：`0` 代表屬於主執行緒的 `main_arena`，`1` 代表屬於輔助執行緒的 `non_main_arena`。

第三，**空間借用（`prev_size` 借位）**。這是算堆積偏移時最容易踩坑的地方。當前面的 Chunk A 正在使用中時，緊貼在它後面的 Chunk B 標頭會標記 `P == 1`。既然 `P == 1`，Chunk B 開頭 `+0x00` 的 `mchunk_prev_size` 欄位就完全沒用處；為了省記憶體，`ptmalloc2` 直接讓 **Chunk A 的最後 `8 bytes` 使用者資料合法借住進 Chunk B 的 `mchunk_prev_size` 欄位裡**。靠著這招借位，每個已配置區塊實際上只多花了 `8 bytes`（自己的 `mchunk_size`）的標頭成本，而不是 `16 bytes`。

第四，**最小區塊限制與 `request2size` 換算公式**。一個釋放後要放進雙向鏈結回收桶的 Chunk，至少得塞得下 `mchunk_prev_size`（`8 B`）、`mchunk_size`（`8 B`）、`fd`（`8 B`）與 `bk`（`8 B`），加起來剛好是 `32 bytes`（`0x20`）。在 64 位元系統上（`SIZE_SZ = 8`、`MALLOC_ALIGNMENT = 16`、`MINSIZE = 32`），`glibc` 把呼叫端要求的長度 `req` 換算成實體 Chunk 大小的公式長這樣：

```text
request2size(req):
  若 req + 8 + 15 < 32  →  回傳 32 (0x20)
  否則                  →  回傳 (req + 8 + 15) & ~15
```

為什麼公式裡是加 `8` 而不是加 `16`？就是因為剛剛講的借位——你自己的 `16 bytes` 標頭裡，有 `8 bytes` 是向後面那塊借來的！這也解釋了為什麼不管你呼叫 `malloc(0)`、`malloc(16)` 還是 `malloc(24)`，分到的 Chunk 大小統統是 `0x20`（因為 `24 + 8 = 32`）；但只要多要 `1 byte` 變成 `malloc(25)`，`(25 + 8 + 15) & ~15 = 48 & ~15 = 0x30`，區塊大小就會當場跳一階變成 `48 bytes`。

---

### Bin 狀態機：`tcache`、`fastbin`、`unsorted`、`small` 與 `large bin`

當程式呼叫 `free()` 與 `malloc()` 時，區塊並不是隨便亂塞，而是照著一套「**執行緒快取優先、按尺寸分級、延遲合併**」的狀態機在五種回收桶之間流轉：

```text
                    free(mem) [non-mmapped]
                              │
                              ▼
         ┌──────────────────────────────────────────┐
         │ 1. 檢查 tcache (0x20..0x410 且數量 < 7)  │──[命中]──▶ 插入 tcache LIFO (維持 P=1)
         └──────────────────────────────────────────┘
                              │ [已滿或 > 0x410]
                              ▼
         ┌──────────────────────────────────────────┐
         │ 2. 檢查 fastbin (<= global_max_fast)     │──[命中]──▶ 插入 fastbin LIFO (維持 P=1)
         └──────────────────────────────────────────┘
                              │ [> global_max_fast]
                              ▼
         ┌──────────────────────────────────────────┐
         │ 3. 嘗試與物理相鄰空閒塊合併 (P==0 檢查)  │
         │    (若鄰接 Top Chunk 則直接併入 Top)     │
         └──────────────────────────────────────────┘
                              │ [未併入 Top]
                              ▼
         ┌──────────────────────────────────────────┐
         │ 4. 放入 unsorted bin 雙向環狀串列        │
         └──────────────────────────────────────────┘
                              │
             [後續 malloc() 掃描 unsorted bin]
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   [尺寸精確吻合]      [0x20..0x3f0]         [>= 0x400]
   (歸還或補入 tcache)  移入對應 small bin    移入對應 large bin
```

我們順著這張流程圖，把五種回收桶的脾氣摸清楚：

首先是第一關 **`tcache`**（Per-Thread Cache）。這是 `glibc 2.26` 為了衝高多執行緒效能加進來的執行緒專屬快取，讓每個執行緒在借還中小型物件時，連 Arena 的互斥鎖都不用拿。它總共有 **`64` 條單向 LIFO（後進先出）串列**，管轄 Chunk 大小從 **`0x20` 到 `0x410`**（每級差 `0x10`，對應使用者請求 `0` 到 `1,032 bytes` 即 `0x408`），每條串列預設最多只裝 **`7` 個區塊**（`TCACHE_FILL_COUNT = 7`）。

`tcache` 還有兩個特色：第一，它直接在使用者資料起點 `+0x10` 放 `tcache_entry` 結構，其中 `+0x10` 是經過 Safe-Linking 編碼的 `next` 指標，`+0x18` 是防雙重釋放的 `key`；第二，待在 `tcache` 裡的區塊會讓物理下一塊繼續保持 **`P == 1`**，也就是故意不觸發前後區塊合併，換取極致的快取速度。

要是某個尺寸的 `tcache` 已經裝滿 `7` 個了，小區塊就會流向第二關 **`fastbin`**。`fastbin` 在 64 位元下雖然留了 `10` 個槽位，但預設全域上限 `global_max_fast` 通常設在 **`0x80`**（即 `128 bytes`，涵蓋 `0x20` 到 `0x80` 共 7 條串列；若用 `mallopt(M_MXFAST, ...)` 調高最多可到 `0xa0`）。

它跟 `tcache` 一樣是單向 LIFO、只用 `+0x10` 的 `fd` 指標（在 `glibc 2.32+` 同樣受 Safe-Linking 保護），而且也維持 **`P == 1` 不立刻合併**。直到後面配置器遇到大塊請求（`>= 0x400`）或特定整理時機呼叫 `malloc_consolidate()` 時，才會一口氣把 `fastbin` 清空，清掉下一塊的 `P` 位元並合併送進 `unsorted bin`（或併入 Top Chunk）。

至於那些塞不進 `tcache` 與 `fastbin`（且沒緊貼著 Top Chunk）的區塊，在走完第三步的前後相鄰空閒塊合併後，會先統一進到第四關 **`unsorted bin`**（Bin 索引 1，雙向環狀串列）。這是一個很聰明的「懶惰分類」設計：剛釋放並合併完的區塊先丟在這裡，等下次有人呼叫 `malloc()` 掃描 `unsorted bin` 時，如果大小剛好吻合就直接拿走（或順手補進同尺寸的 `tcache`）；大小不合的區塊，才會在這次掃描過程中被正式歸檔到後面兩類分類桶，接著再由配置器挑出最合適的區塊（Best-Fit）或切分重用。

最後歸檔的終點就是 **`small bin`** 與 **`large bin`**：
- **`small bin`（62 條，管轄 `0x20` 到 `0x3f0`）**：每條串列裡的區塊大小一模一樣，採用雙向環狀 FIFO（先進先出，使用 `fd` 與 `bk`），取用與移除（unlink）都是常數時間 `O(1)`。
- **`large bin`（63 條，管轄 `>= 0x400`）**：每條串列涵蓋一個指數放大的尺寸範圍（例如 `0x400`–`0x430`、`0x440`–`0x470`）。為了在同一個桶子裡快速找到最接近的大小，區塊會按尺寸由大到小排序，而且除了 `+0x10`/`+0x18` 的 `fd`/`bk` 之外，還多用了 `+0x20` 的 `fd_nextsize` 與 `+0x28` 的 `bk_nextsize` 把不同尺寸的第一塊串成快速跳躍鏈。

我們直接拿 `libnexus-parse` 常配置的五種長度，實際算一遍它們在 64 位元 `ptmalloc2` 下的實體大小、標頭值（假設在 `main_arena` 且前塊使用中，故 `A=0, M=0, P=1`），以及 `tcache` 未滿與已滿 7 個時的釋放去向：

```text
[環境參數] 64-bit x86_64 glibc (SIZE_SZ=8, MALLOC_ALIGNMENT=16, MINSIZE=0x20, global_max_fast=0x80)
[算式]     chunk_size = max(0x20, (req + 8 + 15) & ~15)

1. req = 24 bytes (0x18, TLV 固定中繼資料結構)
   計算: (24 + 8 + 15) & ~15 = 47 & ~15 = 32 (0x20)
   標頭 mchunk_size: 0x20 | 0x1 = 0x21 (最後 8 bytes 借用下一塊 +0x00)
   free() 去向: tcache[idx=0] (<7 個時) -> fastbin[idx=0] (tcache 已滿時)

2. req = 25 bytes (0x19, 僅多 1 byte)
   計算: (25 + 8 + 15) & ~15 = 48 & ~15 = 48 (0x30)
   標頭 mchunk_size: 0x30 | 0x1 = 0x31
   free() 去向: tcache[idx=1] (<7 個時) -> fastbin[idx=1] (tcache 已滿時)

3. req = 1,032 bytes (0x408, tcache 覆蓋的最大請求)
   計算: (1032 + 8 + 15) & ~15 = 1055 & ~15 = 1040 (0x410)
   標頭 mchunk_size: 0x410 | 0x1 = 0x411
   free() 去向: tcache[idx=63] (<7 個時) -> 合併檢查後進 unsorted bin (tcache 已滿時)

4. req = 1,040 bytes (0x410, 剛好跨出 tcache 邊界)
   計算: (1040 + 8 + 15) & ~15 = 1063 & ~15 = 1056 (0x420)
   標頭 mchunk_size: 0x420 | 0x1 = 0x421
   free() 去向: 直接繞過 tcache 與 fastbin -> 合併檢查後進 unsorted bin (後續進 large bin)

5. req = 65,536 bytes (0x10000, NexusPay TLV 合法負載上限 64 KiB)
   計算: (65536 + 8 + 15) & ~15 = 65559 & ~15 = 65552 (0x10010)
   標頭 mchunk_size: 0x10010 | 0x1 = 0x10011 (未達 128 KiB mmap 閾值時由 Arena 切分)
   free() 去向: 直接繞過 tcache 與 fastbin -> 合併檢查後進 unsorted bin (若鄰接 Top Chunk 則併入)
```

---

### 基礎記憶體損毀原語的機制推導

看懂 `malloc_chunk` 跟回收桶怎麼共用記憶體之後，我們就能明白為什麼堆積漏洞威力這麼大：只要你的程式碼跟配置器對「這塊記憶體現在歸誰管、邊界在哪裡」產生誤會，就會立刻演變成三種經典的破壞原語。

#### 1. Use-After-Free（UAF，釋放後使用）

想像 `libnexus-parse` 正在批次解析多筆 TLV 封包，為每筆封包配置了一個 `24 bytes`（實體 Chunk 大小 `0x20`）的 `tlv_ctx_t` 結構。當其中一筆封包格式不對走進錯誤處理分支時，程式提早呼叫了 `free(ctx)`，卻忘了把外層持有的 `ctx` 指標清成 `NULL`（留下懸垂指標 Dangling Pointer）。接著外層迴圈收尾時，又拿著這個 `ctx` 讀寫了一次：

```text
  [階段 A: 正常使用]              [階段 B: 提早 free]            [階段 C: 同尺寸重配置]
  ctx ──▶ ┌──────────────┐       ctx ──▶ ┌──────────────┐       ctx ──▶ ┌──────────────┐
          │ +0x00 prev   │               │ +0x00 prev   │               │ +0x00 prev   │
          │ +0x08 size   │               │ +0x08 size   │               │ +0x08 size   │
          │ +0x10 magic  │               │ +0x10 next*  │ (Safe-Link)   │ +0x10 token* │◀─ new_obj
          │ +0x18 flags  │               │ +0x18 key    │ (tcache_key)  │ +0x18 role   │
          └──────────────┘               └──────────────┘               └──────────────┘
```

這張三階段對照圖直接揭曉了 UAF 的兩種殺傷力：

如果發生在**階段 B（區塊剛釋放、還躺在回收桶裡）**，程式透過舊指標 `ctx` 去讀第一個欄位（偏移 `+0x10`），就會觸發 **UAF 讀取（資訊洩漏）**。特別注意一個跟 Safe-Linking 有關的巧合：當某條 `tcache` 串列原本是空的（`entries[idx] == NULL`），第一個被放進去的區塊，它的 `next` 欄位會被編成 `(pos >> 12) ^ 0 = pos >> 12`。也就是說，只要讀到空 `tcache` 首個節點的前 `8 bytes`，連半點解密運算都不用做，就當場拿到堆積頁面的隨機基底位址 `pos >> 12`！要是釋放的是超過 `0x410`、直接進 `unsorted bin` 的唯一大區塊，讀 `+0x10`（`fd`）跟 `+0x18`（`bk`）更會直接洩漏 `libc.so.6` 裡 `main_arena` 的位址。

如果程式走到了**階段 C（別處又呼叫 `malloc(24)` 配置了另一個新物件 `new_obj`）**，`tcache` 的後進先出規則會把剛剛釋放的那塊記憶體原封不動交給 `new_obj`。這時舊指標 `ctx` 跟新指標 `new_obj` 指著**同一個實體位址**。只要舊邏輯透過 `ctx` 改了欄位，就等於偷改了 `new_obj` 的權限旗標或內部指標，形成**類型混淆（Type Confusion）**；要是趁階段 B 區塊還在 `tcache` 裡時就透過 `ctx` 往 `+0x10` 寫資料，改掉的則是配置器自己的 `next` 鏈結指標。

#### 2. Double Free（雙重釋放）

雙重釋放就是把同一塊已經處於空閒狀態的記憶體，又丟給 `free()` 釋放第二次。在早期沒有防護的年代，如果把區塊 `A` 連續釋放兩次（或穿插 `B` 變成 `A → B → A`），回收桶的單向串列就會打結成迴圈。接下來呼叫兩次 `malloc()`，配置器就會把**同一塊記憶體 `A` 同時發給兩個完全不相干的變數**，或是讓一塊記憶體「既由使用者拿在手上寫資料、同時又還掛在回收桶的空閒串列裡」，徹底打破所有權互斥的鐵律。

雖然現代 `glibc` 加上了 `tcache key` 與 `fasttop` 檢查，直接連續寫兩行 `free(A); free(A);` 會當場被抓包中止；但在實戰審計中，只要結合 UAF 寫入先破壞掉 `+0x18` 的 `key` 欄位，或是像第 24 章會完整推演的「趁 `tcache` 滿 7 個時送進 `unsorted bin` 合併後再釋放」，雙重釋放依然能繞過檢查製造出重疊區塊。

#### 3. Heap Buffer Overflow（堆積緩衝區溢位）

堆疊溢位瞄準的是函式返回位址 `Saved RIP`，而堆積溢位打擊的則是**物理位址緊鄰在後的下一個 Chunk（Next Chunk）**。

當寫入超出當前區塊的合法範圍（包含借用的下一塊 `+0x00` `prev_size`）時，第一個撞上的就是下一塊的 `+0x08` `mchunk_size` 與 `A/M/P` 旗標。一旦攻擊者把相鄰區塊的 `mchunk_size` 改大，配置器對區塊邊界的認知就會錯亂，在後續切分或回收時製造出重疊配置（Overlapping Chunks）；要是偽造 `P = 0` 並改寫 `mchunk_prev_size` 想誘騙配置器往前合併，現代 `glibc` 則會在合併前核對 `chunksize(prev) == prev_size(p)`（對不上就噴 `corrupted size vs. prev_size` 中止行程）。

更隱蔽的情況是：如果物理相鄰的下一塊剛好是個正在使用中的業務物件（比如裡面放著租戶 ID 或函式指標），溢位過去直接就改掉了那個物件的業務欄位，過程完全不會驚動配置器的任何檢查！

---

### 現代 `glibc` 緩解機制：Safe-Linking、`tcache key` 與 Pointer Mangling

要評估現代 Linux 服務上堆積漏洞的真實利用難度，必須搞懂 `glibc 2.29` 到 `2.34+` 陸續築起的三道防線。

#### 1. Safe-Linking（`glibc 2.32+`）

雙向串列（像 `unsorted`/`small`/`large bin`）在取出節點做 `unlink_chunk` 時，可以靠核對雙向指標 `FD->bk == p && BK->fd == p` 來確認鏈結有沒有被竄改；但單向串列（`tcache` 與 `fastbin`）為了追求極速只有一個 `next`（或 `fd`）指標，沒辦法做雙向核對。為了補上這個破口，`glibc 2.32` 導入了極為精巧的 **Safe-Linking** 巨集：

```c
#define PROTECT_PTR(pos, ptr) \
  ((__typeof (ptr)) ((((size_t) pos) >> 12) ^ ((size_t) ptr)))
#define REVEAL_PTR(ptr)  PROTECT_PTR (&ptr, ptr)
```

這裡的 `pos` 是**存放該指標的記憶體位址本身**（在 `tcache` 裡就是 `&e->next`，也就是 Chunk 的使用者資料起點 `+0x10`），而 `ptr` 是它真正要指向的下一個空閒區塊位址。因為 64 位元 Linux 分頁大小是 `4 KiB`（`2^12 bytes`），把 `pos` 往右移 `12 bits` 就會丟掉固定的頁內偏移，剛好留下帶有 `28-bit` ASLR 隨機亂數的分頁高位。拿這個隨機高位跟目標指標 `ptr` 做 XOR 再存進記憶體，一口氣達成了兩個防禦效果：

第一是**封死盲目部分覆寫（Blind Partial Overwrite）**。以前攻擊者就算不知道堆積隨機基底，也能只覆寫 `next` 指標的最後 1 到 2 個位元組，把指標微調到同一頁裡的其他位置。現在有了 Safe-Linking，指標的最低 12 bits 被 XOR 上了 `pos >> 12` 的最低 12 bits（也就是原始位址的 bits 12..23，正好是 ASLR 隨機位元！）。沒先拿到堆積位址洩漏前，連改最後 1 個位元組都是在盲猜。

第二是**強制 `16-byte` 對齊驗證**。從 `tcache` 或 `fastbin` 取出指標解碼後，`glibc` 都會檢查 `aligned_OK()`（即 `(addr & 0xf) == 0`）。如果有人沒算好 XOR 就直接寫入一個 `16-byte` 對齊的位址，經過 `REVEAL_PTR` 再跟 `pos >> 12` 做一次 XOR 後，最後一個十六進位數有 `15/16` 的機率不再是 `0`，當場觸發 `malloc(): unaligned tcache chunk detected` 終止行程。

我們直接拿真實位址做一次逐位元驗算。假設 `tcache` 裡有個空閒區塊，它的使用者資料起點是 `pos = 0x55555555a2a0`，現在它的 `next` 要指向同一頁後面另一個合法的 `16-byte` 對齊位址 `target = 0x55555555a400`，看看記憶體裡到底存了什麼：

```text
=== Worked Example: Safe-Linking 逐位元編碼與 16-byte 對齊校驗 ===

[已知輸入]
  pos    = 0x55555555a2a0   (64-bit: 0x0000_5555_5555_a2a0)
  target = 0x55555555a400   (64-bit: 0x0000_5555_5555_a400)

[步驟 1：驗證目標位址之 16-byte 對齊不變量]
  target & 0xf = 0x55555555a400 & 0xf = 0x0  (合法，滿足 MALLOC_ALIGNMENT = 16)

[步驟 2：計算混淆掩碼 pos >> 12（右移 3 個十六進位數字）]
  pos       = 0x55555555a2a0
  pos >> 12 = 0x00055555555a

[步驟 3：逐十六進位位數執行 XOR 計算 PROTECT_PTR(pos, target)]
  位數索引 (高→低):  11  10   9   8   7   6   5   4   3   2   1   0
  pos >> 12       :   0   0   0   5   5   5   5   5   5   5   5   a
  target          :   5   5   5   5   5   5   5   5   a   4   0   0
  ─────────────────────────────────────────────────────────────────
  XOR 結果        :   5   5   5   0   0   0   0   0   f   1   5   a

  檢核關鍵位數 3..0 (二進位):
    位數 3: 0x5 (0101) ^ 0xa (1010) = 0xf (1111)
    位數 2: 0x5 (0101) ^ 0x4 (0100) = 0x1 (0001)
    位數 1: 0x5 (0101) ^ 0x0 (0000) = 0x5 (0101)
    位數 0: 0xa (1010) ^ 0x0 (0000) = 0xa (1010)

  儲存於 tcache->next 之編碼值 = 0x55500000f15a

[步驟 4：驗證 glibc REVEAL_PTR 解碼還原]
  (pos >> 12) ^ 0x55500000f15a
    = 0x00055555555a ^ 0x55500000f15a
    = 0x55555555a400  (精確還原 target，且 & 0xf == 0)

[反例對照：若未洩漏 pos >> 12 而直接寫入原始位址 0x55555555a400]
  REVEAL_PTR 將計算出 0x00055555555a ^ 0x55555555a400 = 0x55500000f15a
  最低位數為 0xa (0x55500000f15a & 0xf = 0xa != 0)
  → 立即失敗於 aligned_OK() 檢查，行程當場 abort()！
```

這筆帳算完，防禦結論非常清楚：**Safe-Linking 強迫攻擊者在竄改單向串列指標前，必須先找到一個資訊洩漏漏洞拿到 `pos >> 12`**，把原本一個漏洞就能搞定的事，拉高成「資訊洩漏＋寫入損毀」的組合拳。

#### 2. `tcache key` 雙重釋放檢查（`glibc 2.29` / `2.34+`）

為了解決 `tcache` 剛推出時毫無雙重釋放防備的問題，`glibc 2.29` 在 `tcache_entry` 的第二個欄位（偏移 `+0x18`）加上了 `key` 檢查。早期版本在這裡放的是 `tcache` 管理結構自己的位址，從 `glibc 2.34` 起則改成行程啟動時隨機產生的 64 位元亂數 `tcache_key`，免得這個欄位被讀走時順便洩漏了堆積位址。

現在每次執行 `free(p)` 準備放進 `tcache` 時，`ptmalloc2` 會做兩步確認：先看 `e->key == tcache_key` 是否成立；如果相等，代表這塊記憶體很可能已經在 `tcache` 裡了（或是原本的使用者資料剛好撞上這個 64 位元亂數），這時配置器就順著該尺寸的 `tcache` 串列巡一遍（最多才 `7` 個節點，常數開銷 `O(7)` 幾乎不影響效能），只要抓到 `tmp == e`，立刻噴出 `free(): double free detected in tcache 2` 並終止行程。等到區塊被 `malloc()` 正常配發出去時，`tcache_get_n()` 會順手把 `e->key = 0` 清掉，確保正常重用後的再次釋放不會誤報。

#### 3. 雙向串列驗證與 Pointer Mangling（`PTR_MANGLE`）

在看 `glibc` 自身防護時，很多人常把保護堆積串列的 Safe-Linking 跟保護內部函式指標的 **Pointer Mangling**（`PTR_MANGLE` / `PTR_DEMANGLE`）搞混。其實這兩道防線守的東西跟依賴的秘密完全不同：

Safe-Linking 守的是堆積上的 `tcache` 與 `fastbin` 指標，它沒有另外生一把密鑰，而是直接拿**堆積位址本身的 ASLR 分頁高位 `pos >> 12`** 當作 XOR 掩碼。一旦你的程式有 UAF 讀取漏洞洩漏了堆積位址，這層保護就被看穿了。

反觀 **Pointer Mangling**，它守的是 `glibc` 內部那些活在整個行程生命週期裡、常被當成控制流跳板的核心函式指標（例如 `__exit_funcs` 裡的 `atexit` 清理函式、`setjmp`/`longjmp` 保存的暫存器與 `tls_dtor_list`）。在 x86_64 架構下，`glibc` 會在執行緒控制塊 `fs:0x30` 裡放一個獨立產生的隨機秘密值 `POINTER_GUARD`。每次執行 `PTR_MANGLE` 時，會先把函式指標跟 `fs:0x30` 做 XOR，再向左循環移位 `17 bits`（`rol 0x11`）。這意味著就算攻擊者已經洩漏了堆積與 `libc` 位址，還拿到了堆積任意寫入能力，只要讀不到執行緒區域儲存區 `fs:0x30` 裡的那把秘密鑰匙，還是沒辦法偽造 `atexit` 的函式指標。

---

## 故障模式與防禦

看懂配置器怎麼運作之後，回頭審視我們的程式碼，大多數堆積災難都來自以下三種設計盲點。

### 故障模式 1：錯誤分支提早 `free()`，卻留下懸垂指標

在 C/C++ 或 Rust `unsafe` 模組解析批次封包時，最常見的寫法就是在好幾個 `if (err) { free(buf); return -1; }` 分支裡各自釋放記憶體。只要外層結構體（像前面例子裡的 `ctx->payload`）還留著指向 `buf` 的舊位址，後面統一執行的清理函式或錯誤日誌一碰到它，馬上就變成 UAF 或 Double Free。

要堵死這個破口，必須在程式碼裡貫徹**單一所有權與釋放後立刻置空**。首先，盡量用集中的 `goto cleanup;` 出口在函式尾端統一釋放資源；其次，把裸露的 `free()` 封裝成強制清零的巨集（因為在 C 語言裡 `free(NULL)` 是標準保證的安全空操作，置空後就算不小心釋放第二次也不會出事）：

```c
#define NEXUS_SAFE_FREE(ptr) do { \
    if ((ptr) != NULL) { \
        free(ptr); \
        (ptr) = NULL; \
    } \
} while (0)
```

### 故障模式 2：把 `ptmalloc2` 的執行期檢查當成萬靈丹

很多團隊覺得升級到新版 `glibc`，有了 Safe-Linking 跟 `tcache key` 就高枕無憂了。但別忘了，配置器的這些檢查只有在「配置器自己又摸到那塊壞掉的標頭或串列指標」時才會觸發，而且觸發後的唯一動作就是呼叫 `abort()` 把整個服務行程殺掉（直接變成阻斷服務 DoS）。如果溢位覆寫的是相鄰物件的業務欄位（像帳本金額或權限旗標），沒動到 Chunk 標頭，`ptmalloc2` 根本連哼都不會哼一聲。

真正的防線是在 CI 測試與 Fuzzing 階段全面開啟 **AddressSanitizer（ASan）** 搭配 UBSan。ASan 不是靠運氣抽查，而是在虛擬記憶體裡劃出一塊**影子記憶體**（Shadow Memory），用每 `8 bytes` 程式記憶體對應 `1 byte` 影子位元組的比例（位址換算約為 `(addr >> 3) + ShadowOffset`）盯著每一次讀寫：
- 每次 `malloc()` 配置區塊的前後，ASan 都會塞進不可讀寫的警戒區（**Redzone**，影子位元組標為 `0xfa`），只要越界寫了 `1 byte`，當場就在那一條寫入指令停下來報警。
- 每次 `free()` 釋放的區塊不會馬上拿去重用，而是先關進定容量的隔離區（**Quarantine**，影子位元組標為 `0xfd`）。只要有懸垂指標敢去讀寫隔離區裡的記憶體，ASan 會立刻印出「在哪裡配置、在哪裡釋放、在哪裡偷讀寫」的完整三份呼叫堆疊。

要注意的是，ASan 大約會吃掉 `2×` 的 CPU 與記憶體開銷，所以它是給 CI 測試與第 29 章灰箱 Fuzzing 用的除錯利器，千萬別直接開著上生產環境。如果線上環境需要低開銷的抽樣防護，應該評估隨機抽樣加裝硬體保護頁的 `GWP-ASan`、ARM64 上的 `HWASan` 或硬體記憶體標記（Arm MTE）。

### 故障模式 3：高頻小物件手管生命週期，寫到沒人看得懂

當解析器在處理單一請求時，需要動態配置幾十個互相指來指去的小節點（像巢狀 TLV 語法樹），叫工程師對每一個節點手動配對 `malloc()` 與 `free()`，遲早會在某條冷門分支漏掉。

遇到這種「所有小物件跟單筆請求同生共死」的場景，最乾淨的架構解法是改用 **Arena / Region 區域配置器**：請求剛進來時先準備一塊記憶體池，解析過程中只管往後推偏移切出小物件，等這筆請求處理完畢，一次把整個 Arena 清空回收，從根源消滅個別物件的 UAF 與 Double Free。如果是長駐型物件，則可以評估換成把標頭跟使用者資料分開存放（**Out-of-Band Metadata**）的硬化配置器（像 `mimalloc` 安全模式或 `scudo`，第 24 章會詳細實測比較）。

| 防禦／偵測機制 | 運作階段 | 攔截弱點類型 | 效能開銷 | 架構限制與盲點 |
|---|---|---|---|---|
| `ptmalloc2` Safe-Linking + `key` | 生產期（預設） | 盲目單向鏈結覆寫、直接 Double Free | 極低（`< 1%`） | 不攔截相鄰業務欄位覆寫；一旦位址洩漏即可被算式繞過 |
| AddressSanitizer（ASan） | CI 測試 / Fuzzing | 堆積溢位（含 1B）、UAF、Double Free | 約 `2×` 時間與記憶體 | 隔離區容量有限，且高開銷不適合直接用於生產環境 |
| `NEXUS_SAFE_FREE` + 單一出口 | 開發期（程式碼規範） | 單執行緒 UAF、Double Free | 極低（置空指令） | 擋不住多執行緒未加鎖共用的競態 UAF 與多處別名指標 |
| Arena / Region 配置器 | 開發架構重構 | 請求內個別物件 UAF / Double Free | 極低（甚至更快） | 物件生命週期不能超過單次請求範圍，且本身不防線性溢位 |
| Hardened Allocator（Out-of-Band） | 生產期（連結替換） | 中繼資料竄改、跨級距標頭破壞 | 約 `5%–15%` | 仍無法阻止同尺寸桶內「相鄰使用者業務物件」彼此覆寫欄位 |

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

現在我們寫一支純本地執行的 C 測試程式 `nexus_heap_lab.c`，模擬 `libnexus-parse` 解析 TLV 封包時的堆積配置行為。我們會分成四步動手驗證：先用 GDB 親眼看看真實的 `malloc_chunk` 標頭與借位現象、驗算 Safe-Linking 的 XOR 編碼、用 AddressSanitizer 抓出 UAF 與 Double Free 的第一現場，最後套用 `NEXUS_SAFE_FREE` 把漏洞修好。所有操作都在本地 Linux x86_64（`glibc >= 2.34`、`gcc`、`gdb`）環境執行。

### 步驟 1：建立本地測試程式 `nexus_heap_lab.c`

把下面這段程式碼存成 `nexus_heap_lab.c`：

```c
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NEXUS_MAGIC 0x4e58

typedef struct {
    uint16_t magic;
    uint16_t type;
    uint32_t len;
    uint8_t *payload;
} nexus_pkt_ctx_t;

static uintptr_t safe_link_encode(uintptr_t pos, uintptr_t ptr) {
    return (pos >> 12) ^ ptr;
}

static uintptr_t safe_link_decode(uintptr_t pos, uintptr_t mangled) {
    return (pos >> 12) ^ mangled;
}

static void verify_safelinking_example(void) {
    uintptr_t pos = 0x55555555a2a0ULL;
    uintptr_t target = 0x55555555a400ULL;
    uintptr_t encoded = safe_link_encode(pos, target);
    uintptr_t decoded = safe_link_decode(pos, encoded);

    printf("[safelink] pos=0x%llx target=0x%llx\n",
           (unsigned long long)pos, (unsigned long long)target);
    printf("[safelink] pos>>12 = 0x%llx\n", (unsigned long long)(pos >> 12));
    printf("[safelink] encoded = 0x%llx (aligned=%s)\n",
           (unsigned long long)encoded,
           (encoded & 0xfULL) == 0 ? "yes" : "no");
    printf("[safelink] decoded = 0x%llx (aligned=%s)\n",
           (unsigned long long)decoded,
           (decoded & 0xfULL) == 0 ? "yes" : "no");
}

__attribute__((noinline))
static void inspect_tcache_layout(void) {
    uint8_t *a = (uint8_t *)malloc(24);
    uint8_t *b = (uint8_t *)malloc(24);
    uint8_t *c = (uint8_t *)malloc(25);
    if (!a || !b || !c) {
        abort();
    }
    memset(a, 0x41, 24);
    memset(b, 0x42, 24);
    memset(c, 0x43, 25);

    printf("[alloc] a=%p b=%p c=%p\n", (void *)a, (void *)b, (void *)c);
    free(a);
    free(b);
    printf("[freed] a and b placed in 0x20 tcache bin\n");

    free(c);
}

__attribute__((noinline))
static void simulate_uaf_bug(void) {
    nexus_pkt_ctx_t ctx = {
        .magic = NEXUS_MAGIC,
        .type = 0x0001,
        .len = 24,
        .payload = NULL
    };
    ctx.payload = (uint8_t *)malloc(24);
    if (!ctx.payload) {
        abort();
    }
    memcpy(ctx.payload, "NEXUS_BATCH_TLV_FRAME_01", 24);

    /* 錯誤處理提早釋放，卻忘記把 ctx.payload 清空為 NULL */
    free(ctx.payload);

    /* 懸垂指標讀取：開啟 ASan 時將精準捕獲 heap-use-after-free */
    uint64_t leaked_qword = 0;
    memcpy(&leaked_qword, ctx.payload, sizeof(leaked_qword));
    printf("[uaf-read] qword at dangling ptr = 0x%016llx\n",
           (unsigned long long)leaked_qword);
}

__attribute__((noinline))
static void simulate_double_free_bug(void) {
    uint8_t *buf = (uint8_t *)malloc(40);
    if (!buf) {
        abort();
    }
    memset(buf, 0x55, 40);
    free(buf);
    /* 重複釋放同一指標：在 glibc 2.34+ 會觸發 tcache key 檢查 */
    free(buf);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <safelink|inspect|uaf|dfree>\n", argv[0]);
        return 1;
    }
    if (strcmp(argv[1], "safelink") == 0) {
        verify_safelinking_example();
    } else if (strcmp(argv[1], "inspect") == 0) {
        inspect_tcache_layout();
    } else if (strcmp(argv[1], "uaf") == 0) {
        simulate_uaf_bug();
    } else if (strcmp(argv[1], "dfree") == 0) {
        simulate_double_free_bug();
    } else {
        fprintf(stderr, "Unknown mode: %s\n", argv[1]);
        return 1;
    }
    return 0;
}
```

### 步驟 2：用 GDB 解剖 `malloc_chunk` 標頭與 Safe-Linking

先編譯不帶 ASan 的普通版本，跑一次 `safelink` 模式核對我們在正文算過的 XOR 結果：

```bash
gcc -g -O0 -Wall -Wextra nexus_heap_lab.c -o nexus_heap_lab
./nexus_heap_lab safelink
```

接著用 GDB 載入 `./nexus_heap_lab inspect`，在 `free(a)` 之前與 `free(b)` 之後各設一個中斷點，親眼看看記憶體標頭的變化：

```gdb
gdb -q --args ./nexus_heap_lab inspect
(gdb) list inspect_tcache_layout
(gdb) break 51
(gdb) break 54
(gdb) run
# 停在第一個斷點（此時 a, b, c 皆為已配置狀態）
(gdb) x/4gx (a - 0x10)
(gdb) x/4gx (b - 0x10)
(gdb) x/4gx (c - 0x10)
# 繼續執行到第二個斷點（此時 a, b 已釋放進入 0x20 tcache bin）
(gdb) continue
(gdb) x/4gx (a - 0x10)
(gdb) x/4gx (b - 0x10)
# 驗證 b 的 next 欄位是否等於 ((uintptr_t)b >> 12) ^ (uintptr_t)a：
(gdb) p/x (((unsigned long)b >> 12) ^ (unsigned long)a)
```

看完 GDB 後，退出並在終端機執行 `./nexus_heap_lab dfree`，觀察 `glibc` 內建的 `tcache key` 防護怎麼攔截直接雙重釋放。

### 步驟 3：啟用 AddressSanitizer 抓出 UAF 與 Double Free

現在加上 `-fsanitize=address,undefined` 重新編譯，分別跑跑看 `uaf` 與 `dfree` 模式：

```bash
gcc -g -O1 -fsanitize=address,undefined nexus_heap_lab.c -o nexus_heap_asan
./nexus_heap_asan uaf
./nexus_heap_asan dfree
```

請對照 ASan 噴出的報錯畫面，找出三個關鍵資訊：錯誤種類（`heap-use-after-free` 或 `attempting double-free`）、三份呼叫堆疊（在哪行偷讀、在哪行提早釋放、當初在哪行配置），以及最底下的 Shadow bytes 圖例（`fd` 代表已釋放的隔離區、`fa` 代表堆積左側警戒區）。

### 步驟 4：套用 `NEXUS_SAFE_FREE` 修補並驗證

把 `nexus_heap_lab.c` 複製成 `nexus_heap_fixed.c`，加上我們在防禦小節寫過的 `NEXUS_SAFE_FREE` 巨集：把 `simulate_uaf_bug` 與 `simulate_double_free_bug` 裡面的 `free(ptr)` 統統換成 `NEXUS_SAFE_FREE(ptr)`，並在讀取 `ctx.payload` 前先檢查 `if (ctx.payload == NULL)`。重新用 `-fsanitize=address,undefined` 編譯並執行 `uaf` 與 `dfree`，確認兩者都能乾淨退出（回傳碼 `0`）。

### 外部靶場對照檢查點（pwn.college）

做完本地實驗後，推薦到 **pwn.college** 平台的 ***Dynamic Allocator Misuse*** 模組挑前幾關基礎題練手，檢驗自己對 `ptmalloc2` 狀態機的熟悉度：
1. **判讀空 `tcache` 首節點與 Safe-Linking**：在除錯器裡看到空閒區塊時，先自己心算 `request2size` 跟 `pos >> 12`，再用 `pwndbg` 的 `bins` 與 `vis_heap_chunks` 指令核對，印證「空桶第一個節點直接存著 `pos >> 12`」這條規律。
2. **追蹤 `tcache` 滿 7 個後的桶位切換**：當題目混合了多次釋放與不同尺寸時，拿紙筆寫下每個尺寸的 `tcache` 計數器。一旦某個尺寸釋放滿 `7` 個，第 `8` 個就會改走 `fastbin`（`<= 0x80`）或 `unsorted bin`（`> 0x80`），這時 `+0x10` 存的指標格式跟合併行為會完全改變。

---

### 參考解答

#### 1. 步驟 2（`safelink` 與 GDB 觀察結果）

執行 `./nexus_heap_lab safelink` 會印出跟我們手算完全一致的結果：

```text
[safelink] pos=0x55555555a2a0 target=0x55555555a400
[safelink] pos>>12 = 0x55555555a
[safelink] encoded = 0x55500000f15a (aligned=no)
[safelink] decoded = 0x55555555a400 (aligned=yes)
```

在 GDB 第一個斷點（剛配置完 `a`、`b`、`c`，還沒釋放）印出標頭時，會看到這樣清晰的記憶體排列（高位址隨 ASLR 變動，底下是 64 位元 `glibc 2.35+` 的典型輸出）：

```text
# a - 0x10 (請求 24 bytes -> 0x20 chunk, P=1):
0x55555555a290: 0x0000000000000000  0x0000000000000021
0x55555555a2a0: 0x4141414141414141  0x4141414141414141

# b - 0x10 (請求 24 bytes -> 0x20 chunk, P=1; 注意 +0x00 借給了 a 的最後 8 bytes!):
0x55555555a2b0: 0x4141414141414141  0x0000000000000021
0x55555555a2c0: 0x4242424242424242  0x4242424242424242

# c - 0x10 (請求 25 bytes -> 0x30 chunk, P=1; +0x00 借給了 b 的最後 8 bytes!):
0x55555555a2d0: 0x4242424242424242  0x0000000000000031
0x55555555a2e0: 0x4343434343434343  0x4343434343434343
```

你看，`b - 0x10` 開頭的 `8 bytes`（`0x55555555a2b0`）真的填滿了屬於 `a` 的 `0x4141414141414141`（第 17 到 24 個位元組）！而 `c` 只不過多要了 `1 byte`（`25 bytes`），它的 `mchunk_size` 就從 `0x21` 跳成了 `0x31`。

繼續往下跑到第二個斷點（`a` 跟 `b` 已經釋放進 `0x20` 的 `tcache`）再看一次：

```text
# a 先進空 tcache[0]，next = (pos_a >> 12) ^ 0 = 0x55555555a
0x55555555a2a0: 0x000000055555555a  0x<隨機 tcache_key>

# b 後進 tcache[0] 變成新表頭，next = (pos_b >> 12) ^ a
0x55555555a2c0: 0x000055500000f7fa  0x<相同 tcache_key>
```

`a` 的 `+0x10` 直接露出了 `pos_a >> 12`（`0x55555555a`），而 `b` 的 `+0x10` 則跟 GDB 算出來的 `((unsigned long)b >> 12) ^ (unsigned long)a` 一模一樣。兩塊的 `+0x18` 都填上了同一個 `tcache_key`，而且下一塊 `c` 的標頭依然維持 `0x31`（`P` 位元保持 `1` 不合併）。至於執行 `./nexus_heap_lab dfree`，則會當場印出 `free(): double free detected in tcache 2` 並觸發 `SIGABRT`。

#### 2. 步驟 3 與步驟 4（ASan 診斷與安全修補程式碼）

跑 `./nexus_heap_asan uaf` 時，ASan 會在 `memcpy(&leaked_qword, ctx.payload, ...)` 那一行精準攔截，印出 `ERROR: AddressSanitizer: heap-use-after-free`、`READ of size 8`，並標出目標位址的影子位元組為 `fd fd fd`（Freed heap region）；跑 `./nexus_heap_asan dfree` 則會印出 `attempting double-free`。

修補後的 `nexus_heap_fixed.c` 關鍵改法如下：

```c
#define NEXUS_SAFE_FREE(ptr) do { \
    if ((ptr) != NULL) { \
        free(ptr); \
        (ptr) = NULL; \
    } \
} while (0)

__attribute__((noinline))
static int simulate_uaf_fixed(void) {
    nexus_pkt_ctx_t ctx = {
        .magic = NEXUS_MAGIC,
        .type = 0x0001,
        .len = 24,
        .payload = NULL
    };
    ctx.payload = (uint8_t *)malloc(24);
    if (!ctx.payload) {
        return -1;
    }
    memcpy(ctx.payload, "NEXUS_BATCH_TLV_FRAME_01", 24);

    /* 釋放時同步把指標清成 NULL */
    NEXUS_SAFE_FREE(ctx.payload);

    /* 後續存取前先檢查指標是否有效 */
    if (ctx.payload == NULL) {
        printf("[fixed] payload already released; skipping read\n");
        return 0;
    }
    return 0;
}
```

同樣地，把 `simulate_double_free_bug` 裡的兩次 `free(buf)` 都換成 `NEXUS_SAFE_FREE(buf)` 後，第二次呼叫時因為 `buf` 已經是 `NULL` 而安全跳過，帶著 ASan 跑 `uaf` 跟 `dfree` 都能零錯誤過關。

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

先別往上翻，試著自己推導下面 4 個問題，算完再對答案：

1. **Chunk 大小換算與回收桶分流**：在 64 位元 x86_64 glibc（`SIZE_SZ = 8`、`MALLOC_ALIGNMENT = 16`、`global_max_fast = 0x80`、`tcache` 涵蓋 `0x20`–`0x410`）環境下，假設前一個物理相鄰 Chunk 正在使用中，程式依序呼叫了 `malloc(40)`、`malloc(41)`、`malloc(120)` 與 `malloc(500)`。請算出這四筆配置的實體 Chunk 大小、`mchunk_size` 標頭值（含 `A/M/P` 旗標），以及當對應尺寸的 `tcache` **已經裝滿 7 個**時，呼叫 `free()` 會進哪一個回收桶？
2. **Safe-Linking 逆向推算與空桶弱點**：假設你在除錯時，看到位址 `pos = 0x55555555b320` 的空閒 `tcache` 區塊裡，存放的 `tcache_entry->next` 編碼值是 `0x55500000e67b`。
   - (a) 請算出它解碼後真正指向的目標位址 `target`，並檢查 `target` 是否符合 `16-byte` 對齊。
   - (b) 如果另一個位於 `0x55555555c100` 的區塊被釋放進一條**原本完全是空的** `tcache` 串列，它偏移 `+0x10` 的 `next` 欄位會存什麼值？為什麼這讓 Safe-Linking 非常怕遇到 UAF 讀取？
3. **延遲合併的設計取捨**：為什麼被放進 `tcache` 或 `fastbin` 的兩個物理相鄰空閒區塊，不會馬上合併成一個大區塊？這跟放進 `unsorted bin` 的區塊有什麼差別？
4. **Safe-Linking 與 Pointer Mangling 的保護邊界**：假設攻擊者已經靠 UAF 讀取拿到了堆積位址與 `libc` 基底位址，也藉由堆積溢位取得了任意記憶體寫入能力（足以算出合法的 Safe-Linking 指標）。為什麼他還是沒辦法直接偽造 `glibc` 裡的 `atexit` 清理函式指標（`__exit_funcs`）來劫持控制流？

---

### 參考解答

1. **Chunk 大小換算與回收桶分流**：
   套用公式 `chunk_size = max(0x20, (req + 8 + 15) & ~15)`，且因位於主 Arena、前塊使用中，旗標為 `P = 1`（`size | 0x1`）：
   - `malloc(40)`：`(40 + 8 + 15) & ~15 = 63 & ~15 = 48 (0x30)`，`mchunk_size = 0x31`。因為 `0x30 <= 0x80`（`global_max_fast`），`tcache` 滿 7 個後會進 **fastbin**（索引 `1`）。
   - `malloc(41)`：`(41 + 8 + 15) & ~15 = 64 & ~15 = 64 (0x40)`，`mchunk_size = 0x41`。同樣 `0x40 <= 0x80`，`tcache` 滿後進 **fastbin**（索引 `2`）。
   - `malloc(120)`：`(120 + 8 + 15) & ~15 = 143 & ~15 = 128 (0x80)`，`mchunk_size = 0x81`。剛好壓在 `global_max_fast = 0x80` 邊界上，`tcache` 滿後進 **fastbin**（索引 `6`）。
   - `malloc(500)`：`(500 + 8 + 15) & ~15 = 523 & ~15 = 512 (0x200)`，`mchunk_size = 0x201`。它雖然還在 `tcache`（`<= 0x410`）管轄範圍內，但當 `tcache` 滿 7 個時，因為 `0x200 > 0x80` 進不了 `fastbin`，會先做前後相鄰空閒塊合併檢查（若緊貼 Top Chunk 就併入 Top），接著放進 **unsorted bin**。
2. **Safe-Linking 逆向推算與空桶弱點**：
   - (a) 先算掩碼 `pos >> 12 = 0x55555555b320 >> 12 = 0x00055555555b`。再拿掩碼跟編碼值做 XOR：`target = 0x00055555555b ^ 0x55500000e67b = 0x55555555b520`。檢查最後一位 `0x55555555b520 & 0xf == 0x0`，完全符合 `16-byte` 對齊。
   - (b) 當 `tcache` 串列原本為空時，舊表頭是 `NULL`（`0x0`）。套進 `PROTECT_PTR` 會算出 `(0x55555555c100 >> 12) ^ 0x0 = 0x00055555555c`。這意味著它連半點混淆都沒有，直接把頁號掩碼明文擺在 `+0x10`！只要程式裡有任何一處 UAF 讀取能讀到這個剛釋放的空桶首節點，Safe-Linking 仰賴的隨機掩碼就當場曝光。
3. **延遲合併的設計取捨**：
   - 為了讓小物件高頻借還達到極速，`tcache` 與 `fastbin` 故意不去動物理下一個區塊的 **`P` 位元（維持 `P == 1`，即 `PREV_INUSE`）**，也不去寫下一塊的 `prev_size`。既然配置器看到 `P == 1` 就認定前一塊「還在使用中」，自然不會觸發合併。
   - 反觀進到 `unsorted bin` 的區塊，在放進去之前就會立刻檢查物理前後區塊是不是空閒（看當前塊的 `P == 0` 與下下塊的 `P == 0`），當場把相鄰空閒塊融合成一大塊並清掉後塊的 `P` 位元，藉此壓低長期的記憶體碎片（而 `fastbin` 要等到 `malloc_consolidate()` 觸發時才會一次清掉 `P` 位元並合併送進 `unsorted bin`）。
4. **Safe-Linking 與 Pointer Mangling 的保護邊界**：
   - 兩者依賴的秘密來源完全不同。Safe-Linking 用的是**堆積位址本身的高位 `pos >> 12`**，所以只要洩漏了堆積位址，攻擊者就能自己算出合法的 `next` 編碼值。
   - 但 `glibc` 保護 `__exit_funcs`（`atexit` 清理函式表）用的是 **Pointer Mangling**（`PTR_MANGLE`），它的密鑰是存放在**執行緒區域儲存區（TLS）控制塊 `fs:0x30` 裡的隨機數 `POINTER_GUARD`**（XOR 後再左旋 `17 bits`）。光拿到堆積位址與 `libc` 基底位址，並不會讓你知道 `fs:0x30` 裡裝了什麼亂數；猜不出 `POINTER_GUARD`，寫進去的偽造函式指標在解碼後只會跳去無效位址崩潰。

---

## 延伸閱讀

- **GNU C Library Wiki — MallocInternals**（https://sourceware.org/glibc/wiki/MallocInternals）：glibc 官方維護的 `ptmalloc2` 資料結構、Arena 鎖機制、`tcache` 與各類 Bin 演算法第一手說明。
- **GNU C Library Manual — The GNU Allocator**（https://www.gnu.org/software/libc/manual/html_node/The-GNU-Allocator.html）：查閱 `mallopt` 調校參數與動態配置器的標準行為契約。
- **Check Point Research — Safe-Linking: Eliminating a 20 year-old malloc() exploit primitive**（https://research.checkpoint.com/2020/safe-linking-eliminating-a-20-year-old-malloc-exploit-primitive/）：Safe-Linking 原作者詳述 `(pos >> 12) ^ ptr` 設計動機、對齊檢查與邊界限制的經典技術報告。
- **LLVM / Clang Documentation — AddressSanitizer**（https://clang.llvm.org/docs/AddressSanitizer.html）：深入解析 Shadow Memory 映射算式、Redzone 與 Quarantine 如何攔截 UAF 與堆積越界。
- **pwn.college — Dynamic Allocator Misuse**（https://pwn.college/）：透過本地受控關卡反覆觀察 `ptmalloc2` chunk 佈局、Bin 轉換與 Safe-Linking 的實戰練習場。
