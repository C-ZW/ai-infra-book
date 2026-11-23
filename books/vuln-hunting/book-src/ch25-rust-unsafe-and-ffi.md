# 第 25 章：Rust、`unsafe` 與 C FFI 邊界漏洞

前兩章拆解了 `ptmalloc2` 的堆積配置狀態機、`Safe-Linking` 與現代安全配置器。很多工程團隊在吃過 C/C++ 的 UAF 與堆積溢位苦頭後，會做一個看似一勞永逸的決定：把解析器或加解密核心用 **Rust** 重寫，再透過 **C FFI** 與 **Node.js N-API** 接回原本的後端服務。

這個方向完全正確，卻也常帶來一個極為危險的錯覺——以為「只要檔案副檔名是 `.rs`，整顆二進位模組就從此刀槍不入」。在 **NexusPay** 的架構裡，負責高速解析銀行對帳封包的 `libnexus-parse`（第 1 章定義的信任邊界 TB-4）就是這樣一條混血管線：最外層是跑在 Node.js 22 上的 TypeScript 閘道，中間透過 N-API 呼叫 Rust 原生模組，最底層又為了相容舊版硬體簽章與零拷貝效能，用 `unsafe extern "C"` 綁了 C 語言靜態函式庫。

雖然 Rust 編譯器在 `unsafe` 區塊裡還是會幫你檢查一般引用的生命週期，但只要跨界鏈路上有任何一個地方打破了 **Soundness**（健全性）前置條件——像是 `--release` 模式下的整數加法回繞、未初始化記憶體 `MaybeUninit` 誤用、跨配置器 `free()`，或是 N-API 外部緩衝區與 V8 垃圾回收器（GC）搶奪所有權——前二十四章看過的記憶體損毀原語就會在編譯器看不見的死角裡全數復活。

---

## 從你已知的出發

為什麼一段在本地跑 `cargo test` 百分之百過關、連半個編譯警告都沒有的 Rust 封包解析器，一加上 `--release` 編譯推上線，收到一筆長度欄位填了 `0xFFFF_FFF8` 的惡意 TLV 封包時，還是會當場寫穿 `ptmalloc2` 的堆積區塊？

因為兩件常被忽略的事實同時發生了：第一，Rust 為了執行期效能，在 `cargo build --release` 下預設關掉了整數溢位檢查（`overflow-checks = false`），讓 `0xFFFF_FFF8_u32 + 8` 默默回繞成 `0`，直接繞過 `<= 65,544` 的上限檢查；第二，`unsafe` 關鍵字從來不是「請編譯器幫我加強檢查指標」，而是**開發者對編譯器簽下的切結書**。你拍胸脯向編譯器保證自己已經把所有指標邊界、對齊與獨佔別名規則都顧好了，LLVM 最佳化器就會百分之百相信你的承諾，甚至大膽刪掉那些它認為「照你的保證絕不可能發生」的防禦分支。一旦這張切結書在 FFI 邊界上跳票，編譯器不但救不了你，反而會幫倒忙把小破口放大成致命的機器碼漏洞。

---

## 機制與推導

### 攻擊者目標與實質影響

當攻擊者盯上採用 Rust、`unsafe` 封裝與 C FFI 的後端原生模組（如 NexusPay 的 `libnexus-parse.node`）時，瞄準的破壞通常有三個方向：

第一是**在「Rust 絕對安全」的保護色下重現堆積溢位與控制流劫持**。正因為很多團隊相信 Rust 不會有記憶體漏洞，部署時往往省掉了額外的沙箱隔離。一旦攻擊者利用 Release 模式的整數回繞或 `unsafe` 裸指標長度失配，在共享堆積上製造出 `0x20` 最小區塊的越界寫入，就能直接套用第 23、24 章的堆積原語覆寫相鄰物件，進而接管整個 Node.js Worker 行程，偷走記憶體裡所有租戶的明文請求與金鑰。

第二是**靠未初始化記憶體與結構體填充洞偷看高熵秘密**。當 Rust 程式誤用 `MaybeUninit`，或是把帶有對齊空洞（padding bytes）的 `#[repr(C)]` 結構體直接拷貝成位元組傳回 TypeScript 層時，前一次函式呼叫留在堆疊或堆積上的 PIE 基底位址、Stack Canary 或密鑰碎片就會跟著 API 回應一起流出去，當場廢掉 ASLR 防線。

第三是**跨執行期 GC 競態引發的隱蔽 UAF 與崩潰**。當原生層把 Rust `Vec<u8>` 或 C `malloc` 配出來的記憶體，用零拷貝方式包成 Node.js `Buffer` 交給 V8 管理時，只要 Rust 背景執行緒跟 V8 垃圾回收器對「誰該在什麼時候釋放」沒有對齊，高併發下就會爆發跨執行緒 UAF 或雙重釋放，讓 API 閘道在尖峰時刻連環重啟，甚至把租戶 A 的回應資料錯發給租戶 B。

---

### Safe 與 `unsafe` 的 Soundness 契約

看這類混血程式碼時，第一件事是把 **Safety（安全性）** 跟 **Soundness（健全性）** 這兩個詞分清楚。

在 Rust 裡面，`unsafe` 關鍵字有兩種用法：一種是寫在程式碼裡的 **`unsafe { ... }` 區塊**，用來解鎖五種平時被編譯器禁止的底層動作；另一種是寫在**宣告位置**（`unsafe fn`、`unsafe trait`、`unsafe impl` 以及 Rust 2024 的 `unsafe extern`），用來向呼叫端或編譯器訂立安全契約。這五種受管制的底層動作與宣告分別是：
1. 解參考裸指標（`*const T` 與 `*mut T`）。
2. 呼叫宣告為 `unsafe` 的函式或方法（包含所有沒在 `unsafe extern` 裡特別標註 `safe` 的外部 FFI 函式）。
3. 讀寫可變靜態變數（`static mut`）。
4. 實作 `unsafe trait`（例如寫 `unsafe impl Send` 或 `Sync`，親自擔保該型別跨執行緒搬移或共享不會出事）。
5. 讀取 `union` 的欄位。

千萬別誤會一件事：**寫了 `unsafe` 絕對不會關掉借用檢查器（Borrow Checker）**。你在 `unsafe` 區塊裡面操作一般的安全引用 `&T` 與 `&mut T`，編譯器還是照樣檢查它們的生命週期；真正脫離編譯器視線的，只有裸指標跟外部 FFI 呼叫。

那什麼叫做 **Unsound（不健全）**？看看下面這段在真實專案裡到處可見的包裝函式：

```rust
// 不健全（Unsound）的包裝：表面上是 safe fn，卻把未驗證的炸彈留給呼叫端
pub fn copy_tlv_payload(dst: &mut [u8], src: *const u8, len: usize) {
    unsafe {
        std::ptr::copy_nonoverlapping(src, dst.as_mut_ptr(), len);
    }
}
```

一個沒有標記 `unsafe fn` 的普通函式，對外宣稱的契約是：「**不管外面的 Safe Rust 程式碼傳什麼合法型別的值進來，我保證絕對不會觸發未定義行為（Undefined Behavior，簡稱 UB）！**」這就叫做 **Soundness（健全性）**。

回頭看上面那段 `copy_tlv_payload`，它明明是個普通的 `pub fn`，任何一處連半個 `unsafe` 都沒寫的 Safe Rust 程式碼，都可以合法地寫出 `copy_tlv_payload(&mut buf, 0x1000 as *const u8, 999999)` 去呼叫它（因為在 Safe Rust 裡「建立裸指標」是完全合法的，只有「解參考裸指標」才需要 `unsafe`），結果當場觸發越界讀寫與記憶體崩潰！像這樣「外層沒標 `unsafe fn`，裡面卻沒把所有前置條件自己檢查完」的函式，就是標準的 **Unsound** 漏洞。

要把這個破口補起來，只有兩條路可以選：如果這個函式真的沒辦法自己確認 `src` 指的那塊記憶體有多長，那就必須老老實實宣告成 `pub unsafe fn copy_tlv_payload(...)`，並在 `/// # Safety` 文件裡寫清楚呼叫端必須保證 `src` 在 `len` 位元組內有效可讀、`len <= dst.len()` 且兩塊記憶體不重疊；反之，如果想做成真正的安全函式，就把參數改成安全切片 `src: &[u8]`，先在函式開頭檢查 `len <= src.len() && len <= dst.len()`，再直接用安全的 `dst[..len].copy_from_slice(&src[..len])`。

這也是為什麼 **Rust 2024 Edition** 特別收緊了兩條新規矩：
- 第一是**預設開啟 `unsafe_op_in_unsafe_fn` 警告**。以前只要在函式頭上掛了 `unsafe fn`，整個函式肚子裡幾百行程式碼就都能隨便解參考裸指標，不用再寫 `unsafe { ... }`，搞得審計員根本看不出哪一行才是真正踩線的地方。現在加上 `#![deny(unsafe_op_in_unsafe_fn)]` 後，就算在 `unsafe fn` 裡面，每一處真正動到裸指標或 FFI 的那一行還是得用最小的 `unsafe { ... }` 框起來。
- 第二是**強制要求寫 `unsafe extern "C" { ... }`**。這提醒每個開發者：只要你宣告了一個外部 C 函式，光是「確認 C 那邊的參數型別、對齊與呼叫慣例（ABI）跟你在 Rust 寫的一模一樣」這件事本身，就已經是一份不安全承諾了。

---

### 三類高頻 UB 破口：`&mut` 別名、`MaybeUninit` 與 Release 溢位

就算函式簽章都寫對了，只要走進 `unsafe` 區塊裡，下面這三種語意陷阱還是常讓資深工程師栽跟頭。

#### 1. `&mut` 獨佔別名違背（Aliasing Violation）

寫 C 語言的時候，只要沒加 `restrict`，拿兩個指標 `p1` 跟 `p2` 指向同一塊記憶體交替讀寫是家常便飯。但在 Rust 裡面，**任何一個 `&mut T` 在它還活著的期間，都向編譯器立下了「全天下只有我能碰這塊記憶體」的獨佔毒誓（Exclusive Aliasing）**。Rust 編譯器甚至會直接把 `&mut T` 轉成 LLVM IR 的 `noalias` 屬性交給後端最佳化。

當你在 `unsafe` 裡把一個 `&mut T` 或 `Box<T>` 轉成裸指標 `*mut T`，又從同一個位址生出第二個 `&mut T` 並交錯讀寫時（這在 Miri 的 **Stacked Borrows** 與 **Tree Borrows** 別名檢查模型裡會立刻讓借用權限標籤失效），大禍就臨頭了。對攻擊者來說，這不是什麼學術理論——LLVM 看到 `noalias` 後，會理直氣壯地認為「透過引用 A 寫資料，絕對不可能改變引用 B 讀出來的值」，於是直接把引用 B 的值快取在暫存器裡，甚至把你後面寫的邊界檢查當成「死程式碼」整段刪掉！

#### 2. `MaybeUninit<T>` 與未初始化記憶體讀取

在 C 語言裡，先在堆疊上宣告 `uint8_t buf[64];`，再把指標傳給 socket `recv()` 去填資料完全合法。但在 Rust 裡，**只要把還沒初始化的記憶體當成一般有效型別（哪怕只是讀成一個普通的 `u8` 或 `bool`）具體化出來，在語言規範上就是立即的未定義行為（UB）**！因為 LLVM 會把未初始化的值標成 `undef` 或 `poison`，編譯器有權假設拿這個值去做的 `if` 判斷永遠為真或永遠為假。

所以在 Rust 裡準備空緩衝區交給底層寫入時，必須用 `std::mem::MaybeUninit<T>` 包起來。這裡最容易踩中三個坑：
- **太早呼叫 `assume_init()`**：準備了一個 `MaybeUninit<[u8; 64]>`（或 `[MaybeUninit<u8>; 64]`），底層 C 函式明明只寫了前 `20 bytes`，程式卻偷懶對整塊 `64 bytes` 呼叫 `assume_init()`，讓後面沒寫到的 `44 bytes` 帶著堆疊上的殘留秘密混進安全切片裡（正確做法是只把確定寫入的前 `20 bytes` 子切片轉成已初始化）。
- **把未初始化緩衝區硬轉成 `&mut [u8]`**：寫出 `unsafe { std::slice::from_raw_parts_mut(buf.as_mut_ptr() as *mut u8, 64) }` 傳給標準的 `Read::read(&mut self, buf: &mut [u8])`。別忘了，拿到 `&mut [u8]` 的函式在型別上完全有權先讀 `buf[0]` 的舊值；一旦建立出指向未初始化記憶體的 `&mut [u8]`，當下就已經構成 UB（若要傳給讀取介面，應先歸零初始化，或使用接受 `&mut [MaybeUninit<u8>]` 的 `BorrowedBuf`）。
- **未初始化物件誤觸 `Drop`**：對一個還沒填好資料的 `MaybeUninit<String>`（或裡面包了 `Vec` 的結構體）不小心轉成正式型別又遇上提前 `return` 或 `panic`，Rust 解構時就會拿堆疊上的垃圾數值當成堆積位址去呼叫 `free()`。

#### 3. Release 模式的整數回繞（Wrapping）與 `as` 靜默轉型

在本地跑 `cargo test`（Debug 模式）時，只要整數加法 `a + b` 溢位，Rust 就會當場 panic 報錯（注意：如果 panic 跨過沒加 unwind 的 `extern "C"` FFI 邊界，或是專案設了 `panic = "abort"`，更會直接把整個行程殺掉）。這讓很多工程師誤以為 Rust 天生免疫整數溢位。

其實在 `cargo build --release` 下，Rust 預設把 `overflow-checks` 設為 `false`。這時所有的 `+`、`-`、`*` 基本算術，都會安安靜靜地退化成**二補數模運算回繞（Two's Complement Wrapping）**，半點警告都不會噴！

更危險的是 Rust 的 `as` 轉型運算子——它**永遠不會在執行期檢查數值範圍**。雖然把小無號數轉成大無號數（像 64 位元下的 `u32 as usize`）不會掉資料，但只要拿 `as` 去做**窄化轉型（`u64 as u32`）、同寬度的有號無號切換（`u32 as i32`），或是把負的有號數轉成大無號數（像 `-8_i32 as usize` 會先做符號延伸變成 `0xFFFF_FFFF_FFFF_FFF8`，瞬間變成天文數字）**，`as` 都會二話不說直接截斷或重新解讀位元。

---

### 實例推導：TLV `len = 0xFFFF_FFF8` 整數回繞與零位元組配置鏈

我們直接拿 NexusPay 的 `libnexus-parse` 走一遍真實的暫存器與記憶體推演。回想一下全書的基準參數：
- `libnexus-parse` 的 TLV 檔頭固定 `8 bytes`：`magic: 2B`（數值 `0x4e58`，小端序位元組為 `58 4e`，對應 ASCII `'X','N'`）、`type: 2B`、`len: 4B`（無號 32 位元整數 `u32`）。
- 合法負載（payload）上限為 `65,536 bytes`（`64 KiB`）。
- 底層 C 函式庫跑在 64 位元 x86_64 glibc `ptmalloc2` 上，最小可用 Chunk 為 `32 bytes`（`0x20`），且強制 `16-byte` 對齊。

看看下面這段在 `--release` 模式下編譯的 Rust FFI 解析函式，它是怎麼在短短二十行裡連踩四個雷的：

```rust
// 漏洞示範程式碼（於 --release 模式編譯）
#[repr(C)]
pub struct TlvHdr {
    pub magic: u16,
    pub msg_type: u16,
    pub len: u32,
}

pub unsafe extern "C" fn parse_frame_vuln(raw: *const u8, actual_avail: usize) -> *mut u8 {
    let hdr = unsafe { &*(raw as *const TlvHdr) };
    if hdr.magic != 0x4e58 {
        return std::ptr::null_mut();
    }

    // 破口 1：u32 加法在 --release 預設安靜回繞！
    let total_alloc: u32 = hdr.len + 8;

    // 破口 2：只檢查加完 8 之後的 total_alloc，沒單獨檢查 hdr.len
    if total_alloc > 65_536 + 8 {
        return std::ptr::null_mut();
    }

    // 破口 3：libc::malloc(0) 不會回傳 NULL，而是配出最小 0x20 chunk
    let out = unsafe { libc::malloc(total_alloc as libc::size_t) } as *mut u8;
    if out.is_null() {
        return std::ptr::null_mut();
    }

    // 破口 4：實際拷貝時卻拿外部收到的 actual_avail - 8 當長度！
    let copy_len = actual_avail.saturating_sub(8);
    unsafe {
        std::ptr::copy_nonoverlapping(raw.add(8), out, copy_len);
    }
    out
}
```

現在攻擊者從網路送進一筆 `520 bytes` 的特製封包（`actual_avail = 520`，前 `8 bytes` 是 TLV 檔頭，其中 `len` 填了 `0xFFFF_FFF8`，後面跟著 `512 bytes` 的可控資料）。我們直接把 CPU 暫存器與 `ptmalloc2` 堆積攤開來看：

```text
=== Worked Example: TLV len = 0xFFFF_FFF8 整數回繞至 ptmalloc2 堆積溢位鏈 ===

[1] 線路層與記憶體中前 8 bytes（x86_64 Little-Endian）：
    Offset  Bytes         欄位與值
    0x00    58 4e         magic = 0x4e58 (小端序位元組 0x58='X', 0x4e='N')
    0x02    01 00         msg_type = 0x0001
    0x04    f8 ff ff ff   len = 0xFFFF_FFF8 (uint32 十進位 = 4,294,967,288)
    0x08..  41 41 ...     512 bytes 攻擊者可控 payload (共 actual_avail = 520 bytes)

[2] 32 位元加法回繞計算（x86_64 暫存器寫入 eax 自動將高 32 位元歸零）：
    eax (hdr.len)  = 0xFFFF_FFF8  (4,294,967,288)
    add eax, 8     = 0x1_0000_0000
    32-bit 截斷後  = 0x0000_0000  (十進位 0；進位旗標 CF=1 在 --release 下被忽略)

[3] 上限檢查繞過：
    total_alloc    = 0x0000_0000 (0)
    65_536 + 8     = 0x0001_0008 (65,544)
    比較 0 > 65544 -> false！成功繞過上限防線。

    （對照另一常見變體：若 FFI 邊界把 hdr.len 用 `as i32` 轉成有號整數：
     0xFFFF_FFF8_u32 as i32 = -8
     比較 -8 > 65536 -> false！同樣直接放行。）

[4] 配置 0-byte 緩衝區與 ptmalloc2 實際堆積佈局：
    call malloc@plt (rdi = 0x0000_0000_0000_0000)
    -> glibc ptmalloc2 將 request size 0 對齊為最小可用 chunk：
       最小可用 chunk 大小 = 32 bytes (0x20)
       ┌─────────────────────────────────┬─────────────────────────────────┐
       │ +0x00: prev_size (8B)           │ +0x08: size = 0x21 (8B, P=1)    │ <- chunk 標頭 (16B)
       ├─────────────────────────────────┼─────────────────────────────────┤
       │ +0x10: user data [0..8)  (8B)   │ +0x18: user data [8..16) (8B)   │ <- out 指標位置 (16B)
       ├─────────────────────────────────┼─────────────────────────────────┤
       │ +0x20: 下一塊 chunk 的 prev_size│ +0x28: 下一塊 chunk 的 size     │ <- 越界起點！
       └─────────────────────────────────┴─────────────────────────────────┘

[5] 實際拷貝與溢位量計算：
    copy_len = actual_avail - 8 = 520 - 8 = 512 bytes (0x200)
    rdi = out (+0x10)
    rsi = raw + 8
    rdx = 0x0000_0000_0000_0200 (512 bytes)
    - 語言與 API 契約層級：malloc(0) 授予的合法可寫容量為 0 bytes，因此整段 512 bytes
      寫入全數超出合法物件邊界並構成立即未定義行為（ASan 即據此回報 0-byte region 後方寫入 512 bytes）。
    - ptmalloc2 實體佈局層級：在 0x20 (32-byte) 最小 chunk 假設下，out (+0x10) 到下一塊相鄰
      chunk 起始偏移 (+0x20) 僅相距 16 bytes (0x10)，512 bytes 寫入將跨越該邊界向後延伸
      512 - 16 = 496 bytes (0x1f0 bytes)，直接覆寫後方相鄰 chunk 的 size、tcache next 指標
      或隔壁的堆積業務物件。
```

你看，雖然整支函式是用 Rust 寫的，但因為加法回繞、有號轉型跟裸指標拷貝沒有守住（甚至開頭把 `raw` 直接轉成 `&*(raw as *const TlvHdr)` 時，如果 `raw` 位址沒對齊 4 bytes，在 Rust 裡當下就已經是未對齊解參考的 UB 了！），算出來的配置大小 `total_alloc`（`0`）跟真正寫進去的長度 `copy_len`（`512`）完全脫鉤，一舉撞穿後面的堆積區塊。

---

### C FFI ABI 錯配與跨分配器 `free`

當 Rust 跟 C 透過 `unsafe extern "C"` 傳遞結構體與指標時，除了整數算術之外，還有兩個藏得極深的結構斷層。

#### 1. `#[repr(C)]` 記憶體佈局與填充洞（Padding）資訊洩漏

Rust 預設的 `#[repr(Rust)]` 佈局是不固定的——編譯器為了省空間，完全有權把你宣告的 struct 欄位順序重新洗牌。所以只要一個結構體需要跨過 FFI 按值傳遞，或是由 Rust 跟 C 兩邊共同讀寫欄位，就一定要掛上 `#[repr(C)]`（如果只是把不透明指標 `*mut T` 傳給 C 端保管、C 端從不自己解開欄位，那才可以用預設的 `#[repr(Rust)]`；單欄位包裝則用 `#[repr(transparent)]`）。

但掛上 `#[repr(C)]` 照著 C ABI 對齊排列後，馬上會衍生出兩個資安破口：

第一個破口是**未清零的對齊填充洞（Uninitialized Padding Leak）**。假設有個跨界結構體長這樣：
`#[repr(C)] struct NexusAuditEvent { tag: u16, flags: u8, code: u32, timestamp: u64 }`
在 64 位元 x86_64 下，`tag`（`2B`）加 `flags`（`1B`）佔了偏移 `0x00..0x03`；為了讓後面 `4-byte` 的 `code` 對齊 `4` 的倍數，編譯器會在偏移 `0x03` 塞進 `1 byte` 的填充空洞（要是 `u16` 後面直接擺 `u64`，更會在偏移 `0x02..0x08` 塞進整整 `6 bytes` 的空洞）。當你在 Rust 裡用一般欄位賦值建出這個結構體時，**編譯器並不保證會把這些填充空洞清成 `0`**！如果程式後面直接把整個結構體轉成位元組切片（順帶一提，在 Rust 裡把含有未初始化填充洞的結構體直接轉成 `&[u8]` 讀取，本身就已經違反型別有效性構成 UB）或透過 `memcpy` 傳回前端，那些空洞裡夾帶的堆疊／堆積殘留位址就會原封不動外洩出去。

第二個破口是**不合法的 `bool` 與 Enum 判別值**。在 C 語言裡，非零整數都可以當成真；但在 Rust 裡，`bool` 的位元組值嚴格規定只能是 `0x00` 或 `0x01`，無欄位 `enum` 也只准出現宣告過的判別值（discriminant）。要是 C 端傳進一個沒驗證過的位元組 `0x02`，而 Rust 端直接透過裸指標解參考或 `transmute` 把它讀成 `bool`，**在產生這個 `bool` 值的那一刻就已經觸發立即 UB**——後面寫的 `match` 或 `if` 防禦分支在編譯器最佳化下隨時會失效。

#### 2. 跨分配器釋放（Cross-Allocator Free）

第 24 章提過，很多高併發後端會在 Rust 裡用 `#[global_allocator]` 換上 `jemalloc` 或 `mimalloc` 來衝高吞吐量，但同一個行程裡動態連結的 C 函式庫卻還是在用 `libc.so.6` 的 `ptmalloc2`。這時只要犯了「A 家配置、B 家釋放」的錯，堆積就會當場炸開：

```text
┌────────────────────────────────────────────────────────────────┐
│ 路徑 A：Rust (jemalloc / mimalloc) 配置 -> C (ptmalloc2) 釋放  │
│   Rust: CString::into_raw() / Box::into_raw() 傳出 ptr         │
│   C   : libc::free(ptr) 讀取 *(ptr - 8) 當作 chunk size        │
│   結果: ptmalloc2 標頭格式不符 -> 破壞空閒串列或立即 Abort     │
├────────────────────────────────────────────────────────────────┤
│ 路徑 B：C (ptmalloc2) 配置 -> Rust (jemalloc / mimalloc) 釋放  │
│   C   : char *p = malloc(64) 回傳給 Rust 呼叫端                │
│   Rust: Vec::from_raw_parts(p, 64, 64) 離開作用域觸發 Drop     │
│   結果: 跨分配器釋放損毀中繼資料 -> 後續配置重複配發同位址     │
└────────────────────────────────────────────────────────────────┘
```

更可怕的是，就算兩邊都用預設配置器，Rust 標準函式庫的 `GlobalAlloc::dealloc` 在釋放記憶體時需要同時傳入指標、大小與對齊（`Layout`），而 C 的 `free(ptr)` 只吃一個指標。把 `Box::into_raw()` 或 `Vec` 的指標直接丟給 C 的 `free()`，在語言契約上本身就是未定義行為。因此跨 FFI 邊界只有一條鐵律：**誰配出來的記憶體，就必須交回給誰提供的專屬釋放函式去回收**。

---

### Node.js N-API / `Buffer` 外部記憶體生命週期與 GC 競爭

在 NexusPay 這種「外層 Node.js + 內層 Rust/C 原生外掛」的架構裡，最難抓的漏洞往往出現在 **原生堆積** 跟 **V8 垃圾回收器（GC）** 交接棒的那一瞬間。

為了省下把大塊解析結果複製進 V8 堆積的時間，Node-API（N-API）提供了 `napi_create_external_buffer`（與 `napi_create_external_arraybuffer`）。它的玩法是「零拷貝借用」：原生模組把一塊自己配置的記憶體指標 `data`、長度 `len`，外加一個清理回呼 `finalize_cb` 交給 Node.js 包成 JS `Buffer`；等到未來某個時間點，V8 發現再也沒有任何 JS 變數指著這個 `Buffer`、啟動垃圾回收時，才會非同步呼叫你註冊的 `finalize_cb` 把那塊原生記憶體釋放掉。

聽起來很省資源，但在高併發伺服器上卻藏著三個致命陷阱：

第一個陷阱是**背景執行緒與 V8 GC 的釋放競態（Cross-Thread UAF / Double Free）**。假設原生模組為了解析大批量封包，開了背景執行緒（或 `napi_async_work`）持續讀寫某塊緩衝區，同時又已經把這個指標包成外部 `Buffer` 傳給了 JS 層。一旦前端商戶連線超過 NexusPay 的 `30 s` 逾時或主動斷線，JS 層把 `Buffer` 引用丟掉，V8 GC 就可能在下一毫秒觸發 `finalize_cb` 把這塊記憶體 `free` 掉——偏偏這時 Rust 背景執行緒手上的 `*mut u8` 還在繼續寫入，當場演變成跨執行緒 UAF！

反過來說，如果 Rust 函式把指標交給 `napi_create_external_buffer` 時，忘了用 `Box::into_raw` 或 `ManuallyDrop` 把所有權交出去，Rust 函式一返回就把記憶體釋放了，等幾秒後 V8 GC 跑 `finalize_cb` 再釋放第二次，就變成了 Double Free。

第二個陷阱是**共享切片打破 Rust `&mut` 獨佔規則**。在 Node.js 裡對 `Buffer` 呼叫 `.subarray()`（或舊版的 `.slice()`）並不會複製記憶體，而是產生另一個共享同一塊底層記憶體的新視圖。如果 JS 層把這個 `Buffer` 丟進非同步網路佇列（例如 `res.send(buf)` 交給 libuv 背景寫出），同時間又呼叫另一個原生函式把同一塊記憶體轉成 Rust 的 `&mut [u8]` 原地修改，就會發生「libuv 正在讀、Rust 拿著 `&mut` 正在寫」的資料競爭，導致商戶 A 的回應封包裡夾雜了商戶 B 的帳務資料。

第三個陷阱則是 **V8 Sandbox（Ubercage）的架構限制**（第 26 章會深入拆解）。現代 V8 為了把引擎記憶體損毀關在沙箱裡，劃出了一塊 `1 TiB` 的虛擬位址空間，規定所有 `ArrayBuffer` 的底層資料都必須住在這個沙箱位址池內。在開啟嚴格沙箱限制的執行環境（像部分新版執行期或 Electron）下，呼叫 `napi_create_external_buffer` 指向沙箱外的 Rust/C 堆積位址會直接回傳 `napi_no_external_buffers_allowed` 拒絕執行。因此，面對 NexusPay 上限僅 `65,536 bytes`（`64 KiB`）的 TLV 封包，最穩健的做法是直接用 **`napi_create_buffer_copy`** 把解析完的結果複製進 V8 沙箱內，讓原生記憶體在 FFI 返回前當場回收，一次斬斷所有 GC 生命週期糾纏。

---

## 故障模式與防禦

把前面拆解的跨界破口收斂起來，我們在寫 Rust + C FFI + N-API 模組時，必須在架構與程式碼上鎖死以下四道防線。

### 故障模式 1：`unsafe` 範圍過大與未驗證的 Safe 包裝

很多工程師寫 FFI 時，習慣在一個兩百行的解析函式開頭套一個大大的 `unsafe { ... }`，或是像前面看過的 `copy_tlv_payload` 那樣，把需要呼叫端守規矩的裸指標操作包進普通的 `pub fn` 裡。

防禦做法是**把 `unsafe` 縮到最小單行，並用型別系統鎖死不變量（Parse, Don't Validate）**：
- 在專案根目錄加上 `#![deny(unsafe_op_in_unsafe_fn)]` 並啟用 Clippy 的 `undocumented_unsafe_blocks` 檢查，強迫每個 `unsafe` 區塊前面都寫明 `// SAFETY:` 註解，逐條核對前置條件。
- 用 Newtype 模式把驗證過的長度封裝起來。例如定義 `pub struct ValidatedTlvLen(u32);`（注意上限 `65,536 = 2^16` 超過了 `u16::MAX = 65,535`，所以至少要用 `u32` 或 64 位元下的 `usize` 存），規定只有通過 `0 < len && len <= 65_536` 與實際緩衝區長度核對（`raw.len() >= 8 + len`）的建構函式才能產出這個型別，後面的配置與拷貝函式只准接收 `ValidatedTlvLen`。

### 故障模式 2：依賴 Debug 溢位檢查與濫用 `as` 轉型

只要在協定解析裡寫出 `hdr.len + 8` 或 `len as i32`，到了 `--release` 模式就是現成的整數回繞破口。

防禦鐵則是**在 FFI 與解析入口全面禁用裸算術與 `as` 窄化／有號轉型**：
- 一律改用 `usize::try_from(hdr.len)` 做型別轉換，並用 `len.checked_add(8)` 做加法，只要回傳 `None` 或 `Err` 就立刻拒絕請求（Fail-Closed）。
- 在 `Cargo.toml` 的 `[profile.release]` 區段加上 `overflow-checks = true` 當作第二層保險。不過要記住：在 `extern "C"` 函式裡絕對不能依賴 panic 來擋外部髒資料（因為跨 FFI 邊界的未攔截 panic 會直接終止整個行程），外部輸入的長度檢查永遠要用 `checked_add` 轉成正常的錯誤碼回傳。

### 故障模式 3：`#[repr(C)]` 填充洞外洩與跨配置器 `free()`

直接把 `#[repr(C)]` 結構體當成位元組切片傳出去，或是讓 C 的 `free()` 去釋放 Rust `Box`／`Vec` 配出來的記憶體，是跨語言邊界最常發生的兩大事故。

防禦做法非常明確：
- 如果 `#[repr(C)]` 結構體真的需要直接轉成位元組緩衝區外傳，必須**把每一個對齊空洞都顯式寫成欄位**（例如 `pub _pad: [u8; 3]`）並強制初始化為 `0`，同時引入 `zerocopy` 或 `bytemuck` crate，讓編譯器在編譯期靜態檢查「結構體內絕無任何隱性填充洞」。
- 嚴格執行「**誰配置、誰釋放（Same-Allocator Free）**」。C 端 `malloc` 出來的指標，必須交回給 C 函式庫導出的專屬銷毀函式（如 `nexus_c_free(ptr)`，可在 Rust 端包進一個實作 `Drop` 的結構體裡自動呼叫）；Rust 端 `Box::into_raw` 傳給 C 的指標，也必須由 Rust 導出一支 `pub unsafe extern "C" fn nexus_rust_free(ptr: *mut T)` 接回來用 `drop(Box::from_raw(ptr))` 釋放。如果效能允許，更推薦改由「呼叫端先配好輸出緩衝區傳進來填資料（Caller-Allocated Buffer）」，從根本省掉跨界轉移所有權的麻煩。

### 故障模式 4：N-API 零拷貝外部緩衝區與 GC 競態

對 `<= 65,536 bytes`（`64 KiB`）的封包還硬要用 `napi_create_external_buffer` 零拷貝，往往省不到幾微秒，卻換來隨時引爆的跨執行緒 UAF。

防禦原則是**小封包一律複製進 V8 沙箱，大封包強制用 `Arc` 引用計數綁定生命週期**：
- 在 NexusPay 這類 `64 KiB` 以內的場景，統一改用 **`napi_create_buffer_copy`**（或 `napi-rs` 預設的安全 `Buffer` 建立介面），在 FFI 返回前把資料複製進 V8 沙箱，當場釋放 Rust/C 緩衝區。
- 只有當面對數十 MB 的大型唯讀資產、確定必須零拷貝時，才用 `Arc<Vec<u8>>` 管理底層記憶體：傳給 `napi_create_external_buffer` 時呼叫 `Arc::into_raw(arc.clone())` 當作 `finalize_hint`，等 V8 GC 呼叫 `finalize_cb` 時再執行 `drop(unsafe { Arc::from_raw(hint) })` 扣減引用計數。這樣就算背景執行緒還拿著另一份 `Arc`，記憶體也絕對不會被提前釋放。

| 邊界層級 | 高風險故障模式 | 靜態 / 動態偵測手段 | 核心架構防禦 |
|---|---|---|---|
| **Rust `unsafe` 邊界** | Unsound 安全函式、`&mut` 別名違背、`MaybeUninit` 未初始化讀取 | `cargo +nightly miri test`（抓別名 UB 與未初始化讀取）、Clippy `undocumented_unsafe_blocks` | 啟用 `#![deny(unsafe_op_in_unsafe_fn)]`；用 Newtype 鎖死驗證不變量；以 `zerocopy` 取代手寫位元轉型 |
| **整數與長度算術** | Release 模式靜默回繞（`0xFFFF_FFF8 + 8 -> 0`）、`as` 有號/截斷誤判 | 結構感知 Fuzzing（見第 29 章）、`overflow-checks = true` 壓力測試 | 全面使用 `checked_add` / `try_into()`；先獨立檢查 `0 < len && len <= 65_536` 再做任何加減 |
| **Rust ↔ C ABI** | `#[repr(C)]` 填充位元組外洩、跨分配器 `free()` | `AddressSanitizer`（`ASan`）、`UndefinedBehaviorSanitizer`（`UBSan`）、`pahole` 檢查 struct padding | 顯式宣告 `_pad` 並歸零；嚴格遵守「誰配置、誰釋放」或改由呼叫端配置緩衝區 |
| **Node.js N-API** | `napi_finalize` 與背景執行緒 UAF、多 `Buffer` 共享視圖 Data Race | Node.js `--expose-gc` 壓力測試搭配 `ASan` 編譯 `.node` 外掛 | 小封包改用 `napi_create_buffer_copy`；大封包零拷貝以 `Arc` 綁定 `finalize_hint` 引用計數 |

---

## 動手做

- **難度**：進階
- **預估時間**：50 分鐘

現在我們在本地建一個 Rust + C 混血的小型靶機專案 `nexus_ffi_lab`，親手重現並修補本章講過的三類跨界漏洞：
1. 驗證 `hdr.len = 0xFFFF_FFF8` 在 `cargo test`（Debug 模式）下會因溢位而 panic，但在 `cargo test --release`（Release 模式）下卻會安靜回繞成 `0` 並繞過上限檢查！
2. 串接 C 輔助函式與 **AddressSanitizer（ASan）**，親眼抓到 `malloc(0)` 後越界寫入 `512 bytes` 的堆積溢位現場；再用 **Miri** 抓出連 ASan 都看不見的純 Rust `&mut` 別名違背與 `MaybeUninit` 未初始化讀取。
3. 用 `try_into()`、`checked_add` 與安全切片重寫出 `parse_frame_safe`，確認在 Release、ASan 與 Miri 下全數零錯誤通過。

### 步驟 1：建立 `nexus_ffi_lab` 專案與 C 輔助函式

在本地 Linux 環境（需安裝 `rustc`/`cargo`、`clang` 或 `gcc`；若要跑 Miri 可執行 `rustup +nightly component add miri`）建一個新目錄：

```bash
mkdir -p nexus_ffi_lab/src && cd nexus_ffi_lab
```

建立 `Cargo.toml` 與 `build.rs`：

```toml
# Cargo.toml
[package]
name = "nexus_ffi_lab"
version = "0.1.0"
edition = "2021"

[build-dependencies]
cc = "1.0"
```

```rust
// build.rs
fn main() {
    println!("cargo:rerun-if-changed=src/c_helper.c");
    cc::Build::new()
        .file("src/c_helper.c")
        .compile("c_helper");
}
```

接著建立 `src/c_helper.c`，模擬底層 C 函式庫收到回繞後的 `alloc_len = 0` 時，呼叫 `malloc(0)` 卻被寫入 `512 bytes` 的破口：

```c
// src/c_helper.c
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

uint8_t* c_alloc_and_copy(uint32_t alloc_len, const uint8_t* payload, size_t copy_len) {
    // 當 alloc_len 溢位回繞成 0 時，glibc malloc(0) 仍回傳最小 0x20 chunk
    uint8_t* buf = (uint8_t*)malloc((size_t)alloc_len);
    if (!buf) return NULL;
    // 若 copy_len 來自實際輸入封包長度 (512 bytes)，立即越界寫入！
    memcpy(buf, payload, copy_len);
    return buf;
}

void c_free_buf(uint8_t* ptr) {
    free(ptr);
}
```

### 步驟 2：撰寫對照漏洞版與安全版的 `src/lib.rs`

把下面這段程式碼存成 `src/lib.rs`，裡面同時放了有漏洞的 `parse_frame_vuln`、修補後的 `parse_frame_safe`，以及兩組專門給 Miri 抓的 UB 測試：

```rust
use std::mem::MaybeUninit;

const NEXUS_MAGIC: u16 = 0x4e58;
const NEXUS_MAX_PAYLOAD: usize = 65_536;

#[repr(C)]
pub struct TlvHdr {
    pub magic: u16,
    pub msg_type: u16,
    pub len: u32,
}

extern "C" {
    fn c_alloc_and_copy(alloc_len: u32, payload: *const u8, copy_len: usize) -> *mut u8;
    fn c_free_buf(ptr: *mut u8);
}

/// 漏洞版：Release 模式 `hdr.len + 8` 溢位回繞成 0，繞過上限檢查
pub unsafe fn parse_frame_vuln(raw: &[u8]) -> Option<*mut u8> {
    if raw.len() < 8 {
        return None;
    }
    let hdr = unsafe { &*(raw.as_ptr() as *const TlvHdr) };
    if hdr.magic != NEXUS_MAGIC {
        return None;
    }
    // 當 hdr.len == 0xFFFF_FFF8：
    // Debug 模式會在此 panic；Release 模式卻回繞成 0x0000_0000！
    let total_alloc: u32 = hdr.len + 8;
    if total_alloc > (NEXUS_MAX_PAYLOAD as u32) + 8 {
        return None;
    }
    let payload = &raw[8..];
    let ptr = unsafe { c_alloc_and_copy(total_alloc, payload.as_ptr(), payload.len()) };
    if ptr.is_null() { None } else { Some(ptr) }
}

/// 安全修復版：顯式檢查邊界、使用 try_into() 與 checked_add，並以標準 Vec 管理所有權
pub fn parse_frame_safe(raw: &[u8]) -> Result<Vec<u8>, &'static str> {
    if raw.len() < 8 {
        return Err("truncated header");
    }
    let magic = u16::from_le_bytes([raw[0], raw[1]]);
    if magic != NEXUS_MAGIC {
        return Err("invalid magic");
    }
    let len_u32 = u32::from_le_bytes([raw[4], raw[5], raw[6], raw[7]]);
    let len: usize = len_u32.try_into().map_err(|_| "length conversion failed")?;
    if len == 0 || len > NEXUS_MAX_PAYLOAD {
        return Err("invalid tlv length");
    }
    let total_needed = len.checked_add(8).ok_or("length overflow")?;
    if raw.len() < total_needed {
        return Err("truncated payload");
    }
    Ok(raw[8..total_needed].to_vec())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn malicious_packet() -> Vec<u8> {
        let mut pkt = Vec::with_capacity(520);
        pkt.extend_from_slice(&0x4e58u16.to_le_bytes()); // magic
        pkt.extend_from_slice(&0x0001u16.to_le_bytes()); // type
        pkt.extend_from_slice(&0xFFFF_FFF8u32.to_le_bytes()); // len = 4,294,967,288
        pkt.extend_from_slice(&[0x41u8; 512]); // 512 bytes payload
        pkt
    }

    #[test]
    fn test_safe_parser_rejects_malicious_length() {
        let pkt = malicious_packet();
        assert_eq!(parse_frame_safe(&pkt), Err("invalid tlv length"));
    }

    #[test]
    #[cfg(debug_assertions)]
    #[should_panic(expected = "attempt to add with overflow")]
    fn test_overflow_behavior_debug_panics() {
        let pkt = malicious_packet();
        unsafe {
            let _ = parse_frame_vuln(&pkt);
        }
    }

    #[test]
    #[cfg(not(debug_assertions))]
    fn test_overflow_behavior() {
        let pkt = malicious_packet();
        unsafe {
            let ptr = parse_frame_vuln(&pkt);
            assert!(ptr.is_some());
            c_free_buf(ptr.unwrap());
        }
    }

    #[test]
    #[ignore = "刻意觸發別名 UB，供 Miri 示範偵測用"]
    fn test_miri_aliasing_ub() {
        let mut val: u32 = 10;
        let ptr = &mut val as *mut u32;
        unsafe {
            let r1 = &mut *ptr;
            let r2 = &mut *ptr; // 第二個活躍 &mut 產生 Stacked Borrows 違規
            *r1 = 20;
            *r2 = 30;
        }
    }

    #[test]
    #[ignore = "刻意觸發未初始化讀取 UB，供 Miri 示範偵測用"]
    fn test_miri_uninit_ub() {
        let buf: [MaybeUninit<u8>; 8] = [MaybeUninit::uninit(); 8];
        let _leaked = unsafe { buf[0].assume_init() };
    }
}
```

### 步驟 3：實測 Debug vs Release、ASan 與 Miri

現在依序跑下面三組指令，比較輸出差異：

```bash
# 1. Debug 模式：漏洞版在加法時直接 panic（符合 should_panic），安全版正常擋下
cargo test

# 2. Release + ASan 模式：加法靜默回繞為 0，進入 C malloc(0) 後寫入 512 bytes 被 ASan 當場逮捕！
CFLAGS="-fsanitize=address,undefined -g" RUSTFLAGS="-Z sanitizer=address" \
  cargo +nightly test --release --target x86_64-unknown-linux-gnu -- test_overflow_behavior

# 3. 用 Miri 驗證安全版零錯誤，並抓出兩個純 Rust unsafe 的語意 UB
cargo +nightly miri test test_safe_parser_rejects_malicious_length
cargo +nightly miri test -- --ignored test_miri_aliasing_ub
cargo +nightly miri test -- --ignored test_miri_uninit_ub
```

### 外部靶場對照檢查點（pwn.college）

做完本地實驗後，推薦去 **pwn.college** 的 **Program Security** 課程（*Memory Errors* 與 *Dynamic Allocator Misuse* 模組），挑那種「先算長度檢查上限、再配置緩衝區並拷貝」的題目練習。審計這類程式碼時，養成一個固定動作：**永遠拿筆把「算配置大小的變數型別」跟「算拷貝長度的變數型別」畫線連起來**，看看中間有沒有夾著 `32-bit` 加法回繞或有號數轉型（`int` vs `size_t`）。

---

### 參考解答

跑完步驟 3 的三組指令，你會親眼看到三個關鍵證據：

第一，在普通 `cargo test`（Debug 模式）下，`test_overflow_behavior_debug_panics` 在走到 `let total_alloc: u32 = hdr.len + 8;` 這一行時，直接噴出 `attempt to add with overflow` panic，連後面的 C 函式都還沒進就停下來了。這就是為什麼只跑 Debug 單元測試的團隊，永遠抓不到 Release 模式的整數回繞漏洞。

第二，一旦加上 `--release` 與 ASan 執行 `test_overflow_behavior`，Rust 的 `hdr.len + 8` 就安安靜靜地回繞成 `0`，一路穿過 `total_alloc > 65544` 的檢查，把 `0` 傳進 C 語言的 `c_alloc_and_copy(0, payload, 512)`。這時 ASan 立刻噴出紅字警報：
- `ERROR: AddressSanitizer: heap-buffer-overflow`
- `WRITE of size 512 at 0x...`
- `is located 0 bytes after 0-byte region [0x..., 0x...)`
這份報告把整個犯罪現場拍得一清二楚：`malloc(0)` 配出了 `0-byte` 的合法範圍，下一行 `memcpy` 卻硬生生往後寫了 `512 bytes`！反觀我們用 `from_le_bytes`（順便解決了裸指標未對齊解參考的 UB）、`try_into()` 與 `checked_add(8)` 重寫的 `parse_frame_safe`，不管是 Debug 還是 Release 模式，都能穩穩回傳 `Err("invalid tlv length")`。

第三，當我們用 `cargo +nightly miri test` 跑後面兩個刻意寫壞的測試時：
- 在 `test_miri_aliasing_ub` 裡，雖然 `r1` 跟 `r2` 指的都是堆疊上同一個活得好好的變數 `val`（完全沒有越界，所以 ASan 根本不會報錯），Miri 卻在 `*r1 = 20;` 那一行當場攔截，印出 `Undefined Behavior: attempting a write access using <tag> ... which does not have permission`（因為建立第二個獨佔引用 `r2` 的瞬間，就把第一個獨佔引用 `r1` 的寫入權限給撤銷了）。
- 在 `test_miri_uninit_ub` 裡，Miri 則精準抓出 `using uninitialized data, but this operation requires initialized memory`。這證明了在審計 Rust `unsafe` 模組時，**ASan（管實體記憶體邊界與 C FFI）與 Miri（管 Rust 語意契約與別名模型）必須兩手並用**。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別看下方解答，試著自己推算下面 4 個真實審計場景的問題：

1. **Release 整數回繞與有號轉型算術**：假設某個 FFI 邊界函式把封包長度 `len` 宣告為 `u32`，先算了加檔頭與結尾校驗碼的總長度 `let alloc_sz: u32 = len + 24;`，接著才檢查 `if alloc_sz > 65_536 { return Err(...); }`。
   - (a) 請問攻擊者傳入的 `len` 最小要是多少（請寫出十六進位與十進位），才能讓 `alloc_sz` 在 `--release` 模式下剛好回繞成 `0` 並繞過檢查？
   - (b) 如果另一位工程師把檢查寫成 `if (len as i32) > 65_536`，請問有哪些 `u32` 範圍的 `len` 會直接繞過這道檢查？
2. **`#[repr(C)]` 結構體對齊與填充洞計算**：看看下面這個準備在 64 位元 x86_64 Linux 上透過 FFI 傳出的結構體：
   ```rust
   #[repr(C)]
   pub struct SettlementReceipt {
       pub kind: u8,        // 1 byte
       pub amount_cents: u32, // 4 bytes
       pub flags: u16,      // 2 bytes
       pub batch_seq: u64,  // 8 bytes
   }
   ```
   請算出 `size_of::<SettlementReceipt>()` 的總位元組數，並列出每一處隱藏填充洞（padding bytes）的起始偏移與長度。如果不做歸零就直接把整塊結構體記憶體複製給前端，最多會洩漏幾個位元組的堆疊／堆積殘留資料？
3. **ASan 與 Miri 的分工盲區**：為什麼一段在 `unsafe` 裡同時建立兩個指向同位址的 `&mut u64` 並交替寫入的純 Rust 程式碼，開著 `AddressSanitizer` 跑測試時完全不會報錯，但交給 `Miri` 卻會馬上被攔下來？
4. **N-API 外部緩衝區的雙重地雷**：某個原生外掛在 Rust 裡用 `Box::into_raw` 把一塊 `4,096 bytes` 的緩衝區交給 `napi_create_external_buffer`（並在 `finalize_cb` 裡呼叫 `Box::from_raw` 釋放），但同時又讓一個背景 Rust 執行緒拿著同一塊緩衝區的裸指標繼續寫入對帳結果。請問當前端 HTTP 請求因逾時被取消、觸發 V8 垃圾回收時，會引爆哪兩種記憶體安全漏洞？應該怎麼改寫才安全？

---

### 參考解答

1. **Release 整數回繞與有號轉型算術**：
   - (a) 要讓 `len + 24` 在 `32-bit` 無號整數下模 `2^32` 回繞為 `0`，最小的 `len` 就是 `2^32 - 24 = 4,294,967,296 - 24 = 4,294,967,272`，換成十六進位是 **`0xFFFF_FFE8`**。在 `--release` 下，`0xFFFF_FFE8_u32 + 24` 會回繞成 `0`，輕鬆通過 `0 <= 65_536`。
   - (b) 一旦寫成 `len as i32`，只要 `len` 的最高位元（bit 31）是 `1`——也就是從 **`0x8000_0000` 到 `0xFFFF_FFFF`**（十進位 `2,147,483,648` 到 `4,294,967,295`）這整整二十一億個數字——轉成 `i32` 後統統會變成負數（`-2,147,483,648` 到 `-1`）。任何負數跟 `65_536` 比大小都會小於 `65_536` 而被直接放行！
2. **`#[repr(C)]` 結構體對齊與填充洞計算**：
   - `kind`（`1B`，對齊 `1`）：放在偏移 `0x00`（佔 `1 byte`）。
   - 下一個欄位 `amount_cents` 是 `u32`（`4B`，對齊 `4`），所以必須從 `4` 的倍數 `0x04` 開始放；編譯器會在偏移 **`0x01..0x04` 插入 `3 bytes` 的填充洞**。
   - `amount_cents`（`4B`）：放在偏移 `0x04..0x08`。
   - `flags`（`2B`，對齊 `2`）：放在偏移 `0x08..0x0a`。
   - 下一個欄位 `batch_seq` 是 `u64`（`8B`，對齊 `8`），必須從 `8` 的倍數 `0x10`（`16`）開始放；因此編譯器會在偏移 **`0x0a..0x10` 插入 `6 bytes` 的填充洞**。
   - `batch_seq`（`8B`）：放在偏移 `0x10..0x18`。
   - 總大小 `size_of::<SettlementReceipt>()` 為 **`24 bytes`（`0x18`）**（結構體整體對齊為 `8` 的倍數）。裡頭藏了兩段未具名填充洞，加起來共有 `3 + 6 = 9 bytes`（分別在 `0x01..0x04` 與 `0x0a..0x10`），每次直接把結構體記憶體當成位元組傳出去，最多會外洩 **`9 bytes`** 的殘留位址或秘密碎片。
3. **ASan 與 Miri 的分工盲區**：
   - **ASan** 靠影子記憶體檢查的是「實體記憶體邊界與存活狀態」（有沒有讀寫到 Redzone 越界、有沒有碰已經進 Quarantine 隔離區的已釋放記憶體）。當兩個 `&mut u64` 都指向同一個合法且還活著的變數時，從實體記憶體角度看完全在界內，所以 ASan 覺得一點問題都沒有。
   - **Miri** 則是直接直譯執行 Rust 的 MIR（中階中介表示），並幫每個指標掛上來源標籤（Provenance），用 Stacked Borrows / Tree Borrows 模型盯著每筆借用的讀寫權限。只要你違背了「`&mut` 存活期間不得有別名寫入」的語言鐵律，就算記憶體完全沒越界，Miri 也會當場抓包，防止這段 UB 在經過 LLVM `noalias` 最佳化後變成機器碼漏洞。
4. **N-API 外部緩衝區的雙重地雷**：
   - **兩種漏洞**：第一是**跨執行緒 UAF**——請求取消後 JS `Buffer` 失去引用，V8 GC 執行 `finalize_cb` 呼叫 `Box::from_raw` 把那 `4,096 bytes` 釋放掉，而背景執行緒手上的裸指標還在繼續往同一個位址寫資料；第二是 **Data Race（資料競爭）**——就算還沒被 GC 回收，背景執行緒沒加同步鎖就寫入一塊已經暴露給 JS 層的記憶體，隨時會與 JS 事件迴圈的讀取撞在一起。
   - **安全改法**：因為 `4,096 bytes` 遠小於 NexusPay 的 `65,536 bytes` 基準上限，最乾淨的做法是等背景執行緒全部算完、把所有權移交回主執行緒的完成回呼（Complete Callback）後，直接呼叫 **`napi_create_buffer_copy`** 把結果複製進 V8 沙箱內的新 `Buffer`，讓 Rust 的 `Box` 當場安全回收；如果遇到真的必須零拷貝的超大唯讀緩衝區，則要在寫完之後包進 `Arc`，讓背景任務與 `finalize_cb` 各自持有一份 `Arc::into_raw` 引用計數。

---

## 延伸閱讀

- **The Rustonomicon（官方不安全 Rust 指南）**（https://doc.rust-lang.org/nomicon/）：系統性拆解 Safe 與 `unsafe` 的 Soundness 邊界、`MaybeUninit` 正確寫法、子型別型變（Variance）與 FFI 記憶體所有權原則。
- **Rust Reference — Behavior Considered Undefined & Rust 2024 Edition Guide**（https://doc.rust-lang.org/reference/behavior-considered-undefined.html 與 https://doc.rust-lang.org/edition-guide/rust-2024/index.html）：完整列出 Rust 規範定義為立即 UB 的所有條件，以及 Rust 2024 導入 `unsafe_op_in_unsafe_fn` 與 `unsafe extern` 的設計背景。
- **Ralf Jung — Stacked Borrows / Tree Borrows 與 Miri 文件**（https://github.com/rust-lang/miri）：深入理解 Rust 指標別名（Pointer Provenance）模型，看懂為什麼違反 `&mut` 獨佔規則會在 LLVM `noalias` 下變成真實漏洞。
- **Node.js Node-API（N-API）官方文件**（https://nodejs.org/api/n-api.html）：查閱 `napi_create_external_buffer`、`napi_finalize` 回呼時機，以及開啟 V8 Sandbox 時的 `napi_no_external_buffers_allowed` 限制。
- **`zerocopy` 與 `cxx` Crate 設計文件**（https://docs.rs/zerocopy 與 https://cxx.rs/）：看現代 Rust 生態怎麼用編譯期巨集靜態消滅 `#[repr(C)]` 填充洞洩漏與跨語言 ABI 錯配。
