# 第 24 章：現代堆積防護與安全分配器架構

第 23 章拆解了 `glibc` 預設配置器 `ptmalloc2` 的帶內標頭、五種回收桶狀態機，以及 `Safe-Linking` 與 `tcache key` 的運作原理。不過，摸透單一配置器的內部規則只是防禦拼圖的一半。從 `glibc 2.34` 開始，上游正式拔掉了存在幾十年的全域可寫鉤子（`__free_hook` 與 `__malloc_hook`），並強化了標準 I/O 串流虛函式表（`vtable`）的邊界檢查。

與此同時，越來越多高併發後端服務開始用 `jemalloc` 或開啟安全模式的 `mimalloc`（`MI_SECURE=4`）換掉預設的 `ptmalloc2`，從架構源頭斬斷「溢位幾個位元組就能塗改配置器標頭」的風險。

本章延續 **NexusPay** 的原生解析模組 `libnexus-parse`（第 1 章定義的信任邊界 TB-4，API 閘道尖峰吞吐量 `2,000 req/s`），完全站在**防禦工程與配置器選型**的角度出發。我們先看 `glibc 2.34+` 為什麼拔掉全域鉤子並導入 `_IO_vtable_check`，再用一個 10 步狀態機實際推演為什麼就算有了 `tcache key`（單桶上限 `7` 個），一旦跟 `unsorted bin` 的前後合併交互作用，懸垂指標還是能製造出重疊區塊（overlapping chunks）。

接著我們橫向對比 `ptmalloc2`、`jemalloc` 與 `mimalloc` 安全模式在帶外標頭隔離、防護頁（guard page）、空閒串列加密與效能開銷上的取捨，最後在本地容器親手跑一次基準測試，實測這幾套方案在吞吐量與漏洞攔截能力上的真實表現。

---

## 從你已知的出發

把系統底層的 `glibc` 升級到 `2.34` 以上，確認 `__free_hook` 與 `__malloc_hook` 都已經拔除、`Safe-Linking` 與 `tcache key` 也都預設開啟了，為什麼原生模組裡一個不起眼的重複釋放 Bug，還是能讓不同租戶的結算資料在記憶體裡疊在一起互相覆寫？

因為拔掉全域鉤子，只是封死了「隨手改一個全域指標就能在下次 `free()` 時跳去執行任意指令」的快速捷徑，卻沒有改變 `ptmalloc2` 把控制標頭跟業務資料混放在同一塊可讀寫（`RW-`）頁面裡的底層架構。

更關鍵的是，`tcache key` 只檢查「目前還待在 `tcache` 裡」的那 `7` 個區塊。只要某個尺寸的 `tcache` 剛好塞滿 `7` 個，第 `8` 個釋放的區塊就會轉進 `unsorted bin` 並跟隔壁的空閒塊融合成一大塊，這時它身上根本不會有 `tcache_key`。一旦應用程式因為懸垂指標又把這個已經被合併的舊位址釋放了一次，配置器就會把同一段記憶體重複發給兩個活著的業務物件，不用碰任何一個函式指標，就能直接穿破多租戶隔離。

---

## 機制與推導

### 攻擊者目標與實質影響

當防禦團隊評估 `libnexus-parse` 這類原生服務在現代 `glibc` 環境下的堆積風險時，必須看清楚攻擊者在沒了 `__free_hook` 之後，依然能靠破壞堆積不變量達成的三種實質殺傷力：

第一是**靜默的跨物件業務資料污染**。當懸垂指標或雙重釋放在 `ptmalloc2` 裡製造出重疊區塊時，兩個合法的業務結構體就會共用同一段實體記憶體。攻擊者根本不用去劫持什麼控制流，只要正常修改其中一個物件的字串或 TLV 負載，就會同步改掉另一個物件的租戶 ID、金額驗證旗標或緩衝區長度上限，直接擊穿第 1 章定義的帳本安全不變量。

第二是**轉向剩餘可寫執行期結構的間接控制流劫持**。當二進位檔開啟 Full RELRO 且 `glibc 2.34+` 拔掉配置器全域鉤子後，`.got.plt` 跟 `__free_hook` 確實都寫不動了。但 `libc` 肚子裡還有不少可寫的執行期狀態結構——像是標準 I/O 串流 `FILE` 物件的內部指標、或是執行緒區域儲存區（TLS）裡的解構函式表。只要攻擊者先靠重疊區塊湊出任意位址讀寫原語，還是會把準星轉向這些資料結構來奪取控制流。

第三是**高併發閘道的連鎖崩潰（DoS）**。在尖峰流量高達 `2,000 req/s` 的 NexusPay 閘道上，只要被塗改的堆積標頭撞上 `ptmalloc2` 的一致性檢查（像 `corrupted size vs. prev_size` 或 `double free detected in tcache 2`），配置器就會立刻呼叫 `abort()` 把整個 Worker 行程殺掉。跟優雅回傳錯誤碼不同，整個行程反覆崩潰會瞬間抽乾上游連線池，引發骨牌式的重啟風暴。

在實務風險分流上，這類記憶體損毀問題一樣要完整評定 **CVSS v4.0** 向量（例如僅造成高可用性衝擊時為 `CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H/SC:N/SI:N/SA:N`），並對照 **EPSS** 機率分數（注意是 `0` 到 `1` 的機率分數，別跟百分位搞混）來排定修補順序。依照全書基準，具備網路可達性與高衝擊的漏洞應排入高危級 SLA（`7 天`）修補；如果能進一步達成任意程式碼執行、波及後續系統安全（如 `SC:H/SI:H`），或是 EPSS 分數 `>= 0.1`、被列入 CISA KEV 清單，就必須立刻升級到嚴重級 SLA（`24 小時` 內處置，詳見第 33 至 36 章）。

---

### `glibc 2.34+` 為何移除 `__free_hook` 並強化 `_IO_vtable_check`

在 `glibc 2.33` 與更早的版本裡，`malloc/malloc.c` 對外提供了一組全域函式指標：`__malloc_hook`、`__free_hook`、`__realloc_hook`、`__memalign_hook` 與 `__after_morecore_hook`。當初設計這組鉤子的好意，是讓除錯工具或記憶體分析器不用重編譯程式，就能直接攔截每一次配置與釋放。

但放在現代系統安全與高併發環境下看，這個設計同時踩了兩個大雷：

第一個大雷是**在可寫資料段放了一顆定時炸彈**。這些鉤子變數本身必須允許執行期動態修改，所以它們住在 `libc.so.6` 的 `.bss`／`.data` 可寫區段（權限 `RW-`）。就算你的主程式乖乖開了 Full RELRO 把自己的 GOT 表鎖成唯讀，只要行程裡有任何一個 `8-byte` 任意寫入漏洞，攻擊者把目標函式位址寫進 `__free_hook`，等程式下一次呼叫 `free(buf)` 時，就會直接把 `buf` 當成第一個參數跳去執行目標函式，連堆疊都不用碰。

第二個大雷是**拖慢熱路徑與執行緒安全隱患**。每次程式呼叫 `malloc()` 或 `free()`，一進門都得先去讀那個全域變數看是不是 `NULL`。在多執行緒高併發環境下，這不僅平白多出快取讀取成本，要是在執行期間動態改寫鉤子，更會引發無解的資料競爭（Data Race）。

所以在 2021 年 8 月釋出的 `glibc 2.34` 中，官方把這組全域鉤子從預設執行路徑與公開標頭檔裡徹底拔除，只把除錯攔截功能獨立成 `libc_malloc_debug.so`（需要除錯時才用 `LD_PRELOAD` 手動掛載）。如果線上服務想換用別套配置器，正統做法是在編譯連結期直接指定符號，或是用標準的 ELF 符號介入（Symbol Interposition，像透過 `LD_PRELOAD` 整套覆寫 `malloc`/`free`）。

除了拔掉配置器鉤子，另一個常被堆積漏洞波及的苦主是 C 標準函式庫的 I/O 串流結構 `struct _IO_FILE_plus`。每個打開的檔案或標準串流（`stdin`、`stdout`、`stderr`）在記憶體裡都是一個 `_IO_FILE_plus` 結構，而在它的尾端（x86_64 偏移 `+0xd8`）放著一個指向虛函式表 `const struct _IO_jump_t *vtable` 的指標，負責分派 `fclose`、`fflush`、`_IO_overflow` 等底層操作。

以前如果發生堆積溢位或任意寫入，攻擊者可以在堆積上自己偽造一張假的函式表，再把 `FILE` 物件的 `vtable` 指過去。為了斬斷這條路，`glibc`（自 `2.24` 起引入，並在後續版本持續收緊）在每次透過 `vtable` 呼叫函式前，都會先跑一次 `IO_validate_vtable(vtable)` 檢查：

```text
  _IO_FILE_plus->vtable
         │
         ▼
  IO_validate_vtable(vtable)
    ├── 計算 section_len = __stop___libc_IO_vtables - __start___libc_IO_vtables
    ├── 檢查 (uintptr_t)vtable - (uintptr_t)__start___libc_IO_vtables < section_len ?
    │     ├── [是] 落於唯讀區段 __libc_IO_vtables (R--) 內 → 允許分派呼叫
    │     └── [否] 落於區段外 → 呼叫 _IO_vtable_check()
    │                             ├── 檢查是否為合法相容外掛註冊表
    │                             └── 否則立即中止 (Fatal error: invalid stdio handle)
```

這道檢查之所以有效，是因為合法的跳躍表全部集中放在 `libc.so.6` 的 `__libc_IO_vtables` 唯讀區段（`R--`）裡。攻擊者沒辦法改寫唯讀區段裡的函式指標；要是把 `vtable` 指到區段外面的堆積位址，又會被 `_IO_vtable_check()` 當場抓包並印出 `Fatal error: invalid stdio handle` 中止行程。

不過，站在防禦架構師的角度，我們必須看穿這道檢查的**邊界在哪裡**：`IO_validate_vtable` 檢查的只是「`vtable` 位址有沒有落在 `__libc_IO_vtables` 這個區段的頭尾範圍內」，它**並沒有核對這個 `FILE` 物件是不是真的指向自己型別對應的那張表起點**。這意味著如果攻擊者已經能任意塗改 `_IO_FILE_plus` 的內部欄位，還是有機會把 `vtable` 微調指向同一個唯讀區段裡的其他合法跳躍表（例如寬字元串流專用的 `_IO_wfile_jumps`）來觸發非預期的間接呼叫。因此，光靠 `libc` 自己的局部檢查，絕對取代不了配置器層級的結構隔離。

---

### 狀態機實例推導：`tcache` 滿載與 `unsorted bin` 合併導致的重疊區塊

既然有了第 23 章講的 `tcache key`，對還在 `tcache` 裡的區塊連續呼叫兩次 `free()` 會立刻被擋下來，那是不是代表雙重釋放在現代 `ptmalloc2` 裡已經沒威脅了？

答案是否定的。只要一個區塊經歷了「**`tcache` 剛好滿 7 個 → 第 8 個進 `unsorted bin` → 跟隔壁空閒塊前後合併**」這套標準狀態轉換，`tcache key` 的保護前提就會被巧妙繞過。

我們直接拿 `libnexus-parse` 批次配置與釋放 TLV 緩衝區的場景，一步步推演這個 10 步狀態機。假設在 64 位元 x86_64 環境下（`glibc 2.34+`），`main_arena` 剛初始化完，`Top Chunk` 起點在 `0x55555555b000`。套用第 23 章的 `request2size` 公式：
- 呼叫 `malloc(0xf8)`（`248 bytes`），實體 Chunk 大小為 `(248 + 8 + 15) & ~15 = 0x100` bytes（`256 bytes`）。
- 呼叫 `malloc(0x118)`（`280 bytes`），實體 Chunk 大小為 `(280 + 8 + 15) & ~15 = 0x120` bytes（`288 bytes`）。
- 呼叫 `malloc(0x18)`（`24 bytes`），實體 Chunk 大小為 `(24 + 8 + 15) & ~15 = 0x20` bytes（`32 bytes`）。

```text
=== Worked Example: 10-step tcache(7) + unsorted bin coalescing state machine ===

前置假設：x86_64 glibc 2.34+，tcache[0x100] 上限為 7 個槽位，Top Chunk = 0x55555555b000。
註：malloc 回傳的使用者指標 mem = chunk_addr + 0x10。

步驟 | 呼叫操作                | tcache[0x100] 狀態      | unsorted bin 狀態              | 關鍵 Chunk 標頭與物理佈局變化
-----+-------------------------+-------------------------+--------------------------------+--------------------------------------------------
  1  | x[0..6] = malloc(0xf8)  | 空 (0/7)                | 空                             | 連續切出 7 塊 0x100：0x55555555b000..b600 (P=1)
     | (連續配置 7 次)         |                         |                                | Top 推進至 0x55555555b700
  2  | prev   = malloc(0xf8)   | 空 (0/7)                | 空                             | prev   @ 0x55555555b700 (size=0x101, P=1)
     | victim = malloc(0xf8)   |                         |                                | victim @ 0x55555555b800 (size=0x101, P=1)
     | guard  = malloc(0x18)   |                         |                                | guard  @ 0x55555555b900 (size=0x21, P=1；防與Top合併)
     |                         |                         |                                | Top 推進至 0x55555555b920
  3  | free(x[0]) .. free(x[6])| 滿 (7/7):               | 空                             | 7 塊依序進入 tcache (LIFO 頂端為 x[6]=...b600)
     | (釋放前 7 塊緩衝區)     | [b600,b500,...,b000]    |                                | tcache 區塊維持下一塊 P=1，不觸發物理合併
  4  | free(prev)              | 滿 (7/7)                | [prev: ...b700 (0x100)]        | tcache 已滿且 0x100 > 0x80 (fastbin 上限)，
     |                         |                         |                                | prev 進入 unsorted bin；victim->P 被清為 0，
     |                         |                         |                                | victim->prev_size 寫入 0x100
  5  | free(victim)            | 滿 (7/7)                | [coalesced: ...b700 (0x200)]   | tcache 已滿，victim 進入 unsorted bin 前檢查 P==0，
     |                         |                         |                                | 與 prev 向後合併為單一 0x200 區塊 (...b700..b900)！
     |                         |                         |                                | guard->prev_size = 0x200, guard->P = 0
  6  | slot = malloc(0xf8)     | 剩 6/7:                 | [coalesced: ...b700 (0x200)]   | 從 tcache[0x100] 彈出 x[6] (...b600)
     | (應用程式配置新區塊)    | [b500,b400,...,b000]    |                                | tcache[0x100] 騰出 1 個空位！
  7  | free(victim) [誤用Bug]  | 滿 (7/7):               | [coalesced: ...b700 (0x200)]   | 應用程式錯誤路徑持有懸垂指標 victim (...b810) 再次釋放：
     | (懸垂指標雙重釋放)      | [b800,b500,...,b000]    |                                | ...b808 的舊 size 仍為 0x100 且該處無 tcache_key，
     |                         |                         |                                | 因 tcache[0x100] 僅 6/7，...b800 成功塞入 tcache！
  8  | big = malloc(0x118)     | 滿 (7/7):               | [rem: ...b820 (0xe0)]          | 請求 0x120 繞過 tcache[0x100]，從 unsorted bin
     |                         | [b800,b500,...,b000]    |                                | 切出 ...b700..b820 (0x120) 給 big，
     |                         |                         |                                | 剩餘 0xe0 (...b820..b900) 留回 unsorted bin
  9  | overlap = malloc(0xf8)  | 剩 6/7:                 | [rem: ...b820 (0xe0)]          | 從 tcache[0x100] 頂端彈出 ...b800，
     |                         | [b500,b400,...,b000]    |                                | 回傳使用者指標 0x55555555b810 給 overlap
 10  | [狀態稽核：不變量破壞]  | 6/7                     | [rem: ...b820 (0xe0)]          | big     擁有 [0x55555555b710, 0x55555555b820)
     |                         |                         |                                | overlap 擁有 [0x55555555b810, 0x55555555b910)
     |                         |                         |                                | 兩者重疊於 [0x55555555b810, 0x55555555b820) (16 B)，
     |                         |                         |                                | 且 overlap 涵蓋 unsorted bin 剩餘區塊標頭 ...b820！
```

仔細看步驟 5 到步驟 9 的轉折，就能看穿 `ptmalloc2` 帶內標頭的兩個結構性死穴：

第一，**為什麼步驟 7 的第二次 `free(victim)` 沒有被 `tcache key` 攔住？** 因為在步驟 5 第一次釋放 `victim` 時，`tcache[0x100]` 剛好是滿的（`7/7`）。所以 `victim` 當初根本沒進過 `tcache`，而是直接去了 `unsorted bin`，它偏移 `+0x18` 的位置從頭到尾都沒有被寫入 `tcache_key`！等到步驟 6 有人領走一塊、`tcache[0x100]` 變成 `6/7` 騰出一個空位時，步驟 7 再次釋放 `victim`，配置器一看 `key` 不相等，就高高興興地把它收進 `tcache` 了。

第二，**為什麼合併成大區塊後，舊標頭還能騙過配置器？** 在步驟 5 把 `prev`（`...b700`）跟 `victim`（`...b800`）合併成一塊 `0x200` 的大區塊時，`ptmalloc2` 只改了大區塊開頭 `0x55555555b708` 的 `size`（改成 `0x201`）跟尾巴 `guard` 的 `prev_size`（改成 `0x200`），**卻不會順手把夾在肚子中間 `0x55555555b808` 的舊 `size`（`0x100`）清掉**。結果就是同一塊 `...b800` 記憶體，既是大區塊 `...b700..b900` 的後半段，同時又掛在 `tcache[0x100]` 的最頂端！步驟 8 跟步驟 9 連續兩次正常的 `malloc()`，就把重疊的記憶體分別發給了 `big` 跟 `overlap` 兩個活生生的業務指標。

---

### 現代安全分配器對照：`ptmalloc2` vs `jemalloc` vs `mimalloc` 安全模式

既然 `ptmalloc2` 的帶內標頭與合併殘留是歷史包袱，最治本的防禦思路就是換掉使用者空間的配置器。下面我們把 `ptmalloc2`（`glibc 2.34+`）、高併發服務常用的 `jemalloc`（Redis / FreeBSD 採用），以及微軟設計的 `mimalloc` 安全模式（`MI_SECURE=4`）擺在一起正面對決：

| 架構維度 | `ptmalloc2`（`glibc 2.34+`） | `jemalloc` | `mimalloc` 安全模式（`MI_SECURE=4`） |
|---|---|---|---|
| **中繼資料位置** | **帶內（In-band）**：`mchunk_size` 緊貼使用者資料，釋放後直接把 `fd/bk` 寫進資料區 | **帶外（Out-of-band）**：小物件靠獨立的 Extent / Slab 位元圖紀錄空閒槽位 | **帶外（Out-of-band）**：頁面標頭 `mi_page_t` 集中放在 `mi_segment_t` 區段開頭，與資料分離 |
| **線性越界防護** | 同 Arena 相鄰區塊間無防護頁；越界 `1 byte` 就能改到下一塊的 `mchunk_size` 與 `P` 位元 | 同 Slab 內的小物件無防護頁（相鄰業務資料仍可能互相覆寫），但不會撞壞配置器的尺寸與位元圖標頭 | **支援硬體防護頁**：在區段尾端與分頁邊界配置 `PROT_NONE` 防護頁，跨頁越界當場觸發 `SIGSEGV` |
| **空閒串列保護** | `tcache`/`fastbin` 用 `(pos >> 12) ^ ptr`；`unsorted`/`small`/`large` bin 則是明文雙向指標 | 小物件用位元圖（bitmap）挑最低位址配發，沒有帶內單向指標串列可供偽造 | **獨立密鑰加密＋隨機化**：每個頁面用獨立亂數密鑰編碼空閒串列指標，並隨機打亂配發順序 |
| **UAF 與雙重釋放偵測** | `tcache` 靠 `tcache_key` 比對，但跨桶合併後會漏接（如前面 10 步狀態機的步驟 7） | 靠位元圖狀態檢查可抓出部分重複釋放，但預設沒有延遲隔離區（quarantine） | `MI_SECURE=4` 加上頁面標頭校驗碼、釋放時嚴格檢查與隨機延遲重用，大幅拉高 UAF 利用失敗率 |
| **高併發開銷（相對基準）** | 基準線（`1.0x`），`tcache` 命中約 `15–25 ns` | 吞吐約 `0.95x–1.10x`，多執行緒下的記憶體碎片率與常駐記憶體（RSS）明顯低於 `ptmalloc2` | 標準模式極快；開啟 `MI_SECURE=4` 約多出 `5%–15%` 延遲與較多的 `PROT_NONE` 虛擬記憶體映射 |

把這三套配置器放回 **NexusPay** 的 `2,000 req/s` 線上環境，我們直接動手算一筆資源帳，看看換用安全配置器到底要付多少代價：

```text
=== Worked Example: NexusPay 2,000 req/s 場景下的配置器資源與開銷推算 ===

系統假設：
- NexusPay 閘道以 4 個原生 Worker 處理 2,000 req/s → 單 Worker 平均負載 500 req/s。
- 每筆請求經 libnexus-parse 進行 TLV 解析與帳本組裝，平均觸發 12 次小型配置（24 B ~ 256 B，平均請求 96 B）。
- 單 Worker 配置頻率 = 500 req/s × 12 allocs/req = 6,000 alloc+free/s（全閘道 24,000 alloc+free/s）。

1. ptmalloc2 帶內開銷（平均請求 96 B）：
   - 實際 chunk 大小 = (96 + 8 + 15) & ~15 = 112 bytes（專屬標頭 8 B + 對齊填充 8 B）。
   - 空間開銷率 = (112 - 96) / 96 = 16.7%。
   - 6,000 次/秒 × 20 ns/次 = 120,000 ns/s = 0.12 ms/s CPU 時間（佔單核 0.012%）。

2. mimalloc MI_SECURE=4 防護成本：
   - 帶外頁面標頭與隨機化/加密空閒串列，使單次 alloc+free 增加約 10%–15% CPU 指令（假設 25 ns/次）。
   - 6,000 次/秒 × 25 ns/次 = 150,000 ns/s = 0.15 ms/s CPU 時間（僅增加 0.03 ms/s，可忽略不計！）。
   - 虛擬位址空間與 RSS 影響：配置 PROT_NONE 防護頁會增加行程的 VMA 數量（可於 /proc/self/maps 觀察），
     防護頁本身只佔虛擬位址區間不吃實體 RAM；而整體常駐記憶體（RSS）受帶外標頭與快取策略影響，
     在典型安全配置器實務中常見約 5%–12% 的 RSS 增長。

3. AddressSanitizer (ASan) 開發/測試期配置對照（切勿直接上生產環境）：
   - 影子記憶體（Shadow Memory）固定保留 1/8 虛擬位址空間（12.5%）。
   - 每個小物件前後加插 Redzone（至少 16–32 bytes），96 B 請求膨脹至 128 B 以上（開銷 >33%）。
   - 全域隔離區（Quarantine，預設 256 MiB 上限）刻意延後釋放，導致實體 RSS 常態性暴增 2x–3x，
     且每次記憶體讀寫均插入影子檢查指令，整體吞吐下降約 1.8x–2.5x（CPU 成本暴增 80%–150%）。
```

這筆帳算完，架構選型的結論一目了然：**在 `2,000 req/s` 的生產環境直接開 `AddressSanitizer` 會讓記憶體跟 CPU 當場爆表，絕對不可行**；但改用 `LD_PRELOAD` 掛載 `mimalloc` 安全模式（`MI_SECURE=4`）或 `jemalloc`，單核每秒只多花 `0.03 ms` 的 CPU 時間，卻能瞬間把帶內 `mchunk_size` 覆寫與 `unsorted bin` 合併重疊這整類結構破口連根拔起。

---

## 故障模式與防禦

在把現代堆積防護推上生產環境時，工程團隊最常在下面三個地方跌倒。

### 故障模式 1：以為升上 `glibc 2.34+` 就對堆積漏洞免疫了

有些團隊把基底容器換成 Ubuntu 22.04 或 24.04（`glibc 2.35+`）後，看到 `__free_hook` 沒了、`Safe-Linking` 也開了，就放心地把 C/C++ 原生模組的記憶體安全審查砍掉。這完全忽略了兩件事：第一，只要程式裡有像前面 10 步狀態機那樣的懸垂指標或溢位，**攻擊者根本不用碰任何 `libc` 控制結構，光靠重疊區塊就能直接覆寫隔壁物件的帳本金額與租戶 ID**；第二，只要配上一處資訊洩漏，Safe-Linking 的 `(pos >> 12) ^ ptr` 就能被精準反推。

因此，`glibc` 內建的緩解機制只能當作「拉高攻擊成本的最後一道減速帶」，絕不能當成安全邊界。凡是負責解析外部不可信輸入的原生元件，都必須搭配 CI 階段的 ASan + Fuzzing（第 29 章）以及生產期的安全配置器或沙箱隔離。

### 故障模式 2：沒調 `vm.max_map_count` 就在容器裡直上 `MI_SECURE=4`

Linux 核心對單一行程能擁有的虛擬記憶體區域（VMA）數量設了硬上限（預設通常是 `vm.max_map_count = 65530`）。當你開啟 `mimalloc` 的 `MI_SECURE=4` 模式時，它為了隔離不同頁面，會頻繁呼叫 `mprotect()` 安插權限為 `PROT_NONE` 的硬體防護頁。

在 Linux 核心眼裡，一段連續映射只要中間夾了一頁不同的權限，就會分裂成三個獨立的 VMA！當高併發服務開了幾十個執行緒與大量記憶體區段時，VMA 數量會快速逼近 `65,530` 上限，最後讓後續的 `mmap()` 直接噴出 `ENOMEM` 失敗。

要上線 `MI_SECURE=4`，一定要先在壓測環境觀察 `/proc/<pid>/maps | wc -l` 的峰值，並在宿主機或 Kubernetes 節點啟動腳本裡調高核心參數（例如 `sysctl -w vm.max_map_count=262144`）。

### 故障模式 3：同一個行程裡混用兩套配置器 ABI（跨配置器 `free`）

在大型專案裡很容易踩到這個地雷：主程式用預設的 `glibc` 連結，但某個動態載入的 `.so` 外掛卻靜態連結了 `jemalloc` 或 `mimalloc`；結果外掛用 `mimalloc` 的 `malloc()` 配出一塊緩衝區交給主程式，主程式用完後卻呼叫 `glibc` `ptmalloc2` 的 `free(mem)` 去釋放它。

這時災難就發生了：`ptmalloc2` 的 `free(mem)` 會習慣性地往回看 `mem - 0x08` 的位置找 `mchunk_size` 標頭，但 `mimalloc` 跟 `jemalloc` 都是帶外標頭設計，`mem - 0x08` 放的根本不是 `ptmalloc2` 認識的標頭（甚至是上一個物件的尾巴）！這種跨配置器釋放輕則當場觸發 `munmap_chunk(): invalid pointer` 崩潰，重則把別家配置器的記憶體塞進自己的 `tcache` 裡，製造出極難除錯的記憶體重疊（第 25 章會專門拆解 Rust 與 C FFI 之間的跨配置器釋放陷阱）。

守住這關的鐵則是**全行程統一配置器符號**，或是嚴格遵守「誰配置、誰釋放」。如果決定用 `mimalloc` 或 `jemalloc` 保護整個服務，就透過全域執行檔連結或容器層級的 `LD_PRELOAD` 一次接管 `malloc`、`calloc`、`realloc`、`free`、`aligned_alloc` 全套符號，並在 CI 裡用 ASan 跑過所有跨模組測試。

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

現在我們寫一支純防禦性的 C 語言基準測試程式 `alloc_bench.c`，在本地 Linux 容器裡讓三種配置器組態同場較勁：
1. 系統預設的 **`glibc 2.34+` `ptmalloc2`**
2. 透過 `LD_PRELOAD` 掛載的 **`mimalloc` 安全模式（`MI_SECURE=4`）**
3. 編譯期開啟的 **AddressSanitizer（`-fsanitize=address`）**

我們要實測兩件事：第一是模擬 NexusPay 高頻混合配置（`200,000` 次）時的**吞吐量與記憶體 RSS 開銷**；第二是當程式發生**跨桶合併後的雙重釋放**與 **`1-byte` 越界寫入**時，哪一套配置器能當場攔截、哪一套會被悄悄放過。

### 步驟 1：準備本地 Linux 容器與編譯 `MI_SECURE=4`

如果你的電腦是 macOS 或還沒裝 `mimalloc`，直接用本地 Docker 開一個乾淨的 Ubuntu 24.04 容器（零雲端費用），並從原始碼編譯開啟完整 `MI_SECURE=4` 防護頁的 `libmimalloc-secure.so`：

```bash
docker run --rm -it -v "$PWD":/work -w /work ubuntu:24.04 bash
apt-get update && apt-get install -y gcc g++ cmake git time

git clone --depth 1 https://github.com/microsoft/mimalloc.git /tmp/mimalloc
cmake -B /tmp/mimalloc/build -S /tmp/mimalloc -DMI_SECURE=4
cmake --build /tmp/mimalloc/build -j$(nproc)
# 編譯好的安全配置器位於 /tmp/mimalloc/build/libmimalloc-secure.so
```

### 步驟 2：建立基準與防禦測試程式 `alloc_bench.c`

把下面這段程式碼存成 `alloc_bench.c`。裡面實作了三個子命令：`bench`（混合配置 `24 B`、`248 B`、`4,080 B` 共 `200,000` 次）、`double-free`（重現我們在 Worked Example 推導過的 10 步跨桶合併後雙重釋放），以及 `oob`（對 `24-byte` 緩衝區越界寫入第 `25` 個位元組）：

```c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

static double elapsed_ms(struct timespec a, struct timespec b) {
    return (b.tv_sec - a.tv_sec) * 1000.0 + (b.tv_nsec - a.tv_nsec) / 1e6;
}

static void run_bench(int iters) {
    const size_t sizes[3] = {24, 248, 4080};
    void *ring[64] = {0};
    struct timespec t0, t1;
    clock_gettime(CLOCK_MONOTONIC, &t0);

    for (int i = 0; i < iters; i++) {
        int slot = i & 63;
        if (ring[slot]) {
            free(ring[slot]);
        }
        size_t sz = sizes[i % 3];
        uint8_t *p = (uint8_t *)malloc(sz);
        if (!p) abort();
        p[0] = (uint8_t)(i & 0xff);
        p[sz - 1] = (uint8_t)((i >> 8) & 0xff);
        ring[slot] = p;
    }
    for (int i = 0; i < 64; i++) {
        free(ring[i]);
    }

    clock_gettime(CLOCK_MONOTONIC, &t1);
    double ms = elapsed_ms(t0, t1);
    printf("[bench] iters=%d, elapsed=%.2f ms, throughput=%.0f ops/s\n",
           iters, ms, (iters / (ms / 1000.0)));
}

static void test_double_free_after_coalesce(void) {
    void *tcache_fill[7];
    for (int i = 0; i < 7; i++) tcache_fill[i] = malloc(0xf8);
    void *prev = malloc(0xf8);
    void *victim = malloc(0xf8);
    void *guard = malloc(0x18);

    for (int i = 0; i < 7; i++) free(tcache_fill[i]);
    free(prev);
    free(victim); /* 與 prev 在 unsorted bin 合併 */

    void *slot = malloc(0xf8); /* 騰出 1 個 tcache 槽位 */
    printf("[test] triggering stale free(victim) after coalescing...\n");
    free(victim); /* 防禦測試點：觀察配置器是否即時攔截 */

    free(slot);
    free(guard);
    printf("[test] completed without immediate abort!\n");
}

static void test_oob_1byte(void) {
    uint8_t *a = (uint8_t *)malloc(24);
    uint8_t *b = (uint8_t *)malloc(24);
    printf("[test] writing 1 byte past end of 24-byte allocation...\n");
    a[24] = 0x41; /* 越界寫入第 25 個位元組 */
    free(a);
    free(b);
    printf("[test] completed without immediate abort!\n");
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <bench|double-free|oob>\n", argv[0]);
        return 1;
    }
    if (strcmp(argv[1], "bench") == 0) {
        run_bench(200000);
    } else if (strcmp(argv[1], "double-free") == 0) {
        test_double_free_after_coalesce();
    } else if (strcmp(argv[1], "oob") == 0) {
        test_oob_1byte();
    }
    return 0;
}
```

### 步驟 3：編譯並執行三組對照實驗

依序編譯標準版與 ASan 版，並用 `/usr/bin/time -v` 量測三種組態的耗時、最大常駐記憶體（Maximum RSS）以及漏洞攔截表現：

```bash
# 1. 編譯標準版與 ASan 版
gcc -O2 -Wall alloc_bench.c -o bench_std
gcc -O2 -g -fsanitize=address -fno-omit-frame-pointer alloc_bench.c -o bench_asan

# 2. 效能與記憶體 RSS 量測
/usr/bin/time -v ./bench_std bench
LD_PRELOAD=/tmp/mimalloc/build/libmimalloc-secure.so /usr/bin/time -v ./bench_std bench
/usr/bin/time -v ./bench_asan bench

# 3. 雙重釋放與 1-byte 越界攔截對照
./bench_std double-free
LD_PRELOAD=/tmp/mimalloc/build/libmimalloc-secure.so ./bench_std double-free
./bench_asan double-free

./bench_std oob
LD_PRELOAD=/tmp/mimalloc/build/libmimalloc-secure.so ./bench_std oob
./bench_asan oob
```

### 外部靶場對照檢查點（pwn.college）

做完本地基準測試後，可以對照 **pwn.college** 平台 ***Dynamic Allocator Misuse*** 模組裡關於區塊合併（coalescing）與重疊配置的關卡，只聚焦在用 GDB 觀察 `tcache` 滿載後進入 `unsorted bin` 時，`prev_size`、`P` 位元與舊標頭的變化，體會為什麼帶內標頭設計這麼難防住跨桶狀態轉換。

---

### 參考解答

跑完上面三組指令，你會觀察到非常鮮明的三組結果：

第一是**吞吐量與記憶體 RSS 的巨大反差**。在 `bench` 模式下，預設 `glibc`（`bench_std`）與掛載 `MI_SECURE=4` 的耗時都只有十幾到數十毫秒（`MI_SECURE=4` 通常只多出 `5%–15%` 的時間），完全能輕鬆扛起線上 `2,000 req/s` 的流量；反觀 `bench_asan` 不僅執行時間拉長了 `1.8x–2.5x`，`Maximum resident set size` 更因為隔離區（Quarantine）延遲釋放與影子記憶體開銷而暴增好幾倍。

第二是**跨桶合併雙重釋放（`double-free` 模式）的攔截差異**。直接跑 `./bench_std double-free` 時，畫面居然真的印出了 `[test] completed without immediate abort!`！這親手證實了我們在 10 步狀態機推導的結論：因為 `victim` 在第一次釋放時已經在 `unsorted bin` 裡跟 `prev` 合併了，身上沒有 `tcache_key`，所以當 `tcache` 空出位置後再次 `free(victim)`，預設的 `ptmalloc2` 當下根本抓不到！

反觀掛載 `MI_SECURE=4`（靠帶外頁面狀態與加密串列檢查）以及 `./bench_asan double-free`（靠隔離區狀態追蹤）時，都在第二次呼叫 `free(victim)` 的那一刻當場攔截並報錯中止。

第三是**細微越界寫入（`oob` 模式）的防禦分工**。對 `malloc(24)` 配置的緩衝區寫入第 `25` 個位元組（`a[24] = 0x41`）時，因為寫到的位置剛好落在對齊填充或借位區，還沒跨過 `4 KiB` 硬體防護頁，所以無論是預設 `glibc` 還是 `MI_SECURE=4` 都會安靜跑完。

唯獨編譯期插樁的 `./bench_asan oob` 會在 `a[24] = 0x41` 執行的瞬間命中 Redzone 影子位元組，立刻印出 `heap-buffer-overflow` 的精確行號。這清楚告訴我們：**CI 測試期的 ASan 與生產期的 `MI_SECURE=4` 不是二選一，而是互補的兩道防線**——在 CI 用 ASan 抓出細微的 `1-byte` 越界，在生產環境用 `MI_SECURE=4` 守住配置器標頭與高併發效能。

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

先別看下面的解答，試著用本章學到的狀態機與配置器架構回答這 4 個問題：

1. **移除全域鉤子後的殘餘風險**：為什麼專案把底層升級到 `glibc 2.34+`（移除了 `__free_hook` 與 `__malloc_hook`）並開啟了 Full RELRO 後，依然不能宣稱「堆積記憶體損毀已經沒辦法被利用」？請從業務資料面與執行期結構面各舉一個理由。
2. **`_IO_vtable_check` 的檢查盲區**：`glibc` 的 `IO_validate_vtable` 是怎麼確認 `FILE` 串流物件的 `vtable` 指標合不合法的？如果攻擊者已經能覆寫 `_IO_FILE_plus` 結構的內容，這道檢查還留了什麼可趁之機？
3. **重疊區塊的尺寸推算**：回想我們推演過的 10 步狀態機，如果把一開始配置的尺寸從 `malloc(0xf8)`（實體 Chunk `0x100`）改成 `malloc(0x88)`（`136 bytes`）：
   - (a) 請問 `malloc(0x88)` 換算出的實體 Chunk 大小是多少？它有超過預設的 `global_max_fast`（`0x80`）嗎？
   - (b) 當 `tcache` 該尺寸已經塞滿 `7` 個後，依序釋放相鄰的 `prev` 與 `victim`（大小皆與 `malloc(0x88)` 相同），它們合併後的單一 `unsorted bin` 區塊總大小是多少？為什麼接著騰出一個 `tcache` 空位後再次呼叫 `free(victim)` 不會觸發 `tcache_key` 報錯？
4. **安全配置器上線實務**：為什麼高併發服務在生產環境應該選 `mimalloc`（`MI_SECURE=4`）或 `jemalloc` 而不是直接開 `AddressSanitizer`？另外，在 Kubernetes 容器裡啟用 `MI_SECURE=4` 前，為什麼一定要先檢查宿主機的 `vm.max_map_count`？

---

### 參考解答

1. **移除全域鉤子後的殘餘風險**：
   - **業務資料面**：只要應用程式發生重疊配置或相鄰堆積溢位，兩個業務物件就會共用或緊鄰在同一頁可讀寫（`RW-`）記憶體裡。攻擊者完全不用碰任何 `libc` 鉤子，直接覆寫相鄰物件的租戶 ID、金額或權限旗標，就能打破業務安全不變量。
   - **執行期結構面**：雖然 `.got.plt`（Full RELRO）與 `__free_hook` 沒得寫了，但 `libc` 內部仍有標準 I/O 串流（`_IO_FILE_plus`）與執行緒區域儲存區（TLS）解構表等可寫資料結構；搭配資訊洩漏與任意寫入原語，依然存在控制流劫持風險。
2. **`_IO_vtable_check` 的檢查盲區**：
   - `IO_validate_vtable` 檢查的是 `vtable` 指標有沒有落在 `libc.so.6` 的唯讀區段 `__libc_IO_vtables` 起訖位址範圍內（若落在區段外且未通過 `_IO_vtable_check` 外掛註冊表檢查，就當場 abort）。
   - **盲區**：它只管「指在這個唯讀區段裡面就行」，卻沒有驗證該指標是不是真的對準這個 `FILE` 物件應有的那張跳躍表起點（例如 `_IO_file_jumps`）。因此攻擊者只要能改寫 `_IO_FILE_plus` 欄位，還是能把 `vtable` 指到同區段裡的其他合法跳躍表（像 `_IO_wfile_jumps`）或偏移位置，觸發非預期的內部函式呼叫。
3. **重疊區塊的尺寸推算**：
   - (a) 套用公式 `(136 + 8 + 15) & ~15 = 159 & ~15 = 144 (0x90)` bytes。因為 `0x90 > 0x80`（超過預設 `global_max_fast`），所以當 `tcache[0x90]` 滿 7 個後，它不會進 `fastbin`，而是直接走合併檢查進 `unsorted bin`。
   - (b) `prev`（`0x90`）與 `victim`（`0x90`）在 `unsorted bin` 向後合併後，會融合成一個大小為 `0x90 + 0x90 = 0x120`（`288 bytes`）的空閒區塊。因為 `victim` 第一次釋放時沒進過 `tcache`，它的 `+0x18` 欄位從沒被寫過 `tcache_key`，而且合併時 `ptmalloc2` 也沒清空夾在中間的 `victim` 舊標頭（`0x90`），所以騰出空位後再次 `free(victim)` 就能順利滑進 `tcache[0x90]`。
4. **安全配置器上線實務**：
   - **為何不開 ASan 上線**：ASan 需要保留 `12.5%` 虛擬位址當影子記憶體、在每個物件前後塞 Redzone，還用預設 `256 MiB` 的隔離區延遲釋放，會讓 CPU 延遲暴增 `80%–150%`、實體記憶體 RSS 翻倍（`2x–3x`）；而 `MI_SECURE=4` 透過帶外標頭、加密隨機化空閒串列與防護頁，只多花約 `5%–15%` 的配置時間（在 `2,000 req/s` 下單核每秒僅多 `0.03 ms`）。
   - **為何要調 `vm.max_map_count`**：`MI_SECURE=4` 會頻繁配置權限為 `PROT_NONE` 的防護頁來隔離記憶體區段，這會把原本連續的虛擬記憶體映射切碎成大量獨立的 VMA。如果不先調高 Linux 核心的 `vm.max_map_count`（預設常為 `65530`），高併發服務很容易因為 VMA 數量撞頂而導致後續 `mmap()` 報 `ENOMEM` 失敗。

---

## 延伸閱讀

- **glibc 2.34 Release Notes & Malloc Hook Removal**（https://sourceware.org/pipermail/libc-alpha/2021-August/129718.html）：GNU C Library 官方釋出公告與 `malloc/malloc.c` 修改紀錄，說明拔除 `__malloc_hook`／`__free_hook` 並拆出 `libc_malloc_debug.so` 的背景。
- **Microsoft `mimalloc` Security Documentation (`MI_SECURE`)**（https://microsoft.github.io/mimalloc/）：詳列 `MI_SECURE` 的 Guard Pages、加密空閒串列、頁面隨機化與標頭校驗碼實作細節。
- **Jason Evans — A Scalable Concurrent malloc(3) Implementation for FreeBSD**（`jemalloc` 架構論文）：深入解析帶外 Extent／Slab 位元圖管理如何壓低多執行緒碎片並隔離配置器標頭。
- **第 25 章〈Rust、`unsafe` 與 C FFI 邊界漏洞〉**：延續本章討論的跨配置器邊界，拆解當 Rust、C 與 Node.js N-API 混用不同配置器時，如何防範跨配置器 `free()` 與 `unsafe` 生命週期錯亂。
