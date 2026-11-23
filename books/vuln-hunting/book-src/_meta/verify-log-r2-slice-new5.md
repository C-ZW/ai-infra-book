# P4 Round-2 Adjudication & Surgical-Fix Log — `slice-new-5`

- **Agent**: `p4-final-3` (`gemini-3.8-flash-high`)
- **Reviewer Cache**: `books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/` (`codex:gpt-6.2-sol:medium` / `argon-low`)
- **Assigned Slice (`slice-new-5`)**:
  1. `ch23-heap-internals-and-primitives.md`
  2. `ch26-jit-type-confusion-and-ubercage.md`
  3. `ch27-linux-kernel-exploitation.md`
  4. `ch33-disclosure-and-bug-bounty.md`
  5. `ch35-nexuspay-red-blue-capstone.md`
- **Verification Gates**:
  - `python3 tools/md-reader/lint_book.py books/vuln-hunting/book-src --lang zh-TW --config books/vuln-hunting/book-src/_meta/lint.config.json` → **PASS** (37 chapters, 0 errors, 0 warnings)
  - `python3 tools/md-reader/check_diagrams.py books/vuln-hunting/book-src` → **PASS** (0 findings)

---

## 1. `ch23-heap-internals-and-primitives.md`

### `incorrect` Findings Adjudicated & Surgically Fixed (17/17)
1. **Claim [1]**: `"區域變數隨著函式進入而壓入堆疊、隨著 ret 返回而自動收回，記憶體位址與生命週期都受限於單一呼叫鏈。"`
   - **Adjudication**: Valid distinction. Automatic local variables have lifetime and scope tied to function activation; compiler optimizations may keep them in registers or eliminate storage, and stack frame epilogue teardown occurs prior to `ret` popping the return address.
   - **Surgical Fix**: Reworded to specify local variables with automatic storage duration (`具有自動儲存期的區域變數隨著函式呼叫建立框架、隨著尾端清理與返回而失效`).
2. **Claim [2]**: `"當 libnexus-parse 必須同時處理多筆長度最高可達 65,536 bytes（64 KiB）的 TLV 封包……這些物件只能由動態記憶體配置器在堆積上配置與釋放。"`
   - **Adjudication**: Valid protocol accuracy fix. 65,536 bytes is the maximum payload size; adding the 8-byte header yields a total maximum packet size of 65,544 bytes. Dynamic heap allocation is the standard pattern for passing variable-length payloads across asynchronous pipelines.
   - **Surgical Fix**: Clarified payload maximum (`65,536 bytes` payload, `65,544 bytes` including 8-byte header) and standard dynamic heap allocation usage.
3. **Claim [3]**: `"ptmalloc2 先透過 brk 或 mmap 向作業系統核心取得大塊虛擬記憶體區域（稱為 Arena）。"`
   - **Adjudication**: Valid technical refinement. An Arena is an internal allocator management structure (containing mutexes, bins, and top chunk pointers) that manages virtual memory regions (heaps/brk data segments).
   - **Surgical Fix**: Updated wording to state that `ptmalloc2` manages virtual memory areas obtained from the kernel via Arena state structures.
4. **Claim [8]**: `"unsorted bin 的 fd/bk 指標則直接指向 libc.so.6 內的 main_arena 結構，讓攻擊者藉第 20 章推導過的固定 12-bit 頁內偏移還原整個 libc 與堆積基底位址。"`
   - **Adjudication**: Valid precision fix. The unsorted bin pointer points to the unsorted bin list head within the Arena structure in `libc.so.6`. Because its symbol offset relative to the libc base is fixed for a given libc build, leaking this pointer allows computing the full libc base address (not merely by a 12-bit page offset alone).
   - **Surgical Fix**: Clarified that `fd`/`bk` points to the unsorted bin head in `main_arena`, and because its offset relative to the libc base is fixed for a known version, it allows calculating the libc base address.
5. **Claim [13]**: `"因為所有 Chunk 總大小皆為 16 bytes（0x10）的整數倍，所以 mchunk_size 的最低 4 個位元必定為 0。"`
   - **Adjudication**: Valid bitfield representation fix. While unflagged raw physical sizes are 16-byte multiples (lowest 4 bits zero), the stored `mchunk_size` field reuses the lowest 3 bits (`0x7`) as `A`, `M`, and `P` flags.
   - **Surgical Fix**: Clarified that the unflagged raw size has lowest 4 bits as zero, and `ptmalloc2` stores size and flags together using the lowest 3 bits as status flags, restored via `size & ~0x7`.
6. **Claim [14]**: `"P == 1 表示前一個 Chunk 正在使用（或本 Chunk 為 Arena 的起點）。"`
   - **Adjudication**: Valid allocator state refinement. Chunks released into `tcache` or `fastbin` deliberately keep `P == 1` in the adjacent subsequent chunk to inhibit immediate backward consolidation.
   - **Surgical Fix**: Clarified that `P == 1` indicates the allocator considers the preceding physical chunk as in-use or in deferred-consolidation caches (`tcache`/`fastbin`), prohibiting backward coalescing.
7. **Claim [24]**: `"只有在系統呼叫 malloc_consolidate()（例如遇到超過 0x400 的大型請求或釋放大型區塊觸發整理）時，配置器才會把 fastbin 內的 Chunk 一次清空、清除對應 P 位元並合併送入 unsorted bin。"`
   - **Adjudication**: Valid accuracy fix. `malloc_consolidate()` is an internal allocator function, not a syscall; large requests `>= 0x400` trigger consolidation, and consolidated chunks may merge into unsorted bin or the Top Chunk.
   - **Surgical Fix**: Changed "系統呼叫" to "配置器內部呼叫", specified `>= 0x400`, and noted potential merging into the Top Chunk.
8. **Claim [25]**: `"如果程式在釋放一個 0x500 區塊後緊接著又請求一個 0x480 區塊，配置器在掃描 unsorted bin 時就能直接切割重用，省下放進 large bin 又立刻取出的成本。"`
   - **Adjudication**: Valid ptmalloc2 flow fix. During unsorted bin traversal in `_int_malloc`, chunks not satisfying exact match are sorted into their respective small or large bins before best-fit selection and remainder splitting.
   - **Surgical Fix**: Refined the description to explain exact-match reuse during unsorted bin scanning and sorting into small/large bins for subsequent best-fit splitting.
9. **Claim [29]**: `"假設函式為每筆封包配置一個 tlv_ctx_t（大小 0x20），另一個同尺寸的新物件 new_obj 也同屬 0x20 級距。"`
   - **Adjudication**: Valid chunk size math fix. If user request is 32 bytes (`0x20`), `request2size(32)` yields `0x30` (48 bytes). A chunk of size `0x20` corresponds to user requests `<= 24 bytes` (`0x18`).
   - **Surgical Fix**: Clarified that `tlv_ctx_t` has a request size of 24 bytes (`0x18`), which normalizes to a `0x20` chunk.
10. **Claim [30]**: `"在階段 B，如果程式透過懸垂指標 ctx 讀取 +0x10 或 +0x18，讀出的不再是應用程式欄位，而是 ptmalloc2 的指標。"`
    - **Adjudication**: Valid pointer offset and field naming fix. `ctx` points to the user data start (`chunk + 0x10`). `ctx + 0x00` reads the `next` pointer and `ctx + 0x08` reads `tcache_key`, which is a verification cookie rather than a pointer.
    - **Surgical Fix**: Distingushed chunk header offsets (`+0x10`, `+0x18`) from user pointer field offsets (`+0x00`, `+0x08`) and clarified that the second field is `tcache_key`.
11. **Claim [31]**: `"在沒有任何防護檢查的年代，若將同一塊記憶體 A 連續放入串列兩次（或穿插另一個區塊 B 形成 A → B → A），串列計數器會虛增，後續兩次 malloc() 會將同一塊記憶體同時分配給兩個看似獨立的呼叫端。"`
    - **Adjudication**: Valid LIFO queue traversal fix. For `A -> B -> A`, subsequent allocations return A, then B, then A again (the 1st and 3rd allocations return the same memory).
    - **Surgical Fix**: Corrected to state that the 1st and 3rd `malloc()` invocations return the same memory block `A`.
12. **Claim [32]**: `"向後看前塊的 P 位元與 prev_size，向前看後塊的再下一個區塊 P 位元。"`
    - **Adjudication**: Valid consolidation check direction fix. Backward consolidation inspects the *current* chunk's `P` bit and reads the *current* chunk's `prev_size` to find the previous chunk. Forward consolidation inspects the chunk following the next chunk.
    - **Surgical Fix**: Explicitly stated that backward coalescing checks the current chunk's `P` bit and `prev_size`, while forward coalescing checks the `P` bit of the chunk after next (or merges into Top).
13. **Claim [36]**: `"將 pos 右移 12 bits 會留下純粹受 ASLR 隨機化的 28-bit 分頁高位部分。"`
    - **Adjudication**: Valid bit-shift precision fix. Shifting right by 12 bits strips the 4 KiB page offset, leaving the page number (containing ASLR entropy and page prefix), rather than extracting an isolated 28-bit value.
    - **Surgical Fix**: Updated wording to state that right-shifting by 12 bits discards the 4 KiB page offset, leaving the high-order page number containing ASLR randomized bits.
14. **Claim [37]**: `"使缺乏資訊洩漏前提的盲目指標覆寫徹底失效。"`
    - **Adjudication**: Valid scoping fix. Safe-Linking drastically elevates the difficulty of blind pointer overwrites, but does not provide absolute authentication under all conceivable corruptions.
    - **Surgical Fix**: Adjusted claim to "大幅提升盲目指標覆寫難度，強制攻擊者必須先取得堆積位址洩漏".
15. **Claim [41]**: `"封裝安全釋放介面，強制在 free() 後立即將呼叫端的指標本身置為 NULL；在實驗中以 nexus_safe_free((void **)&ptr) 套用到 uint8_t * 指標。"`
    - **Adjudication**: Valid C typing and strict aliasing fix. Casting `uint8_t **` to `void **` and dereferencing violates C strict aliasing and pointer type safety.
    - **Surgical Fix**: Replaced function with a safe macro `#define NEXUS_SAFE_FREE(ptr) do { if ((ptr) != NULL) { free(ptr); (ptr) = NULL; } } while (0)` in text, lab instructions, and reference solution.
16. **Claim [42]**: `"每個 malloc() 分配區前後都會插入不可讀寫的 Redzone（影子位元組標記為負值 0xfa），任何越界 1 byte 的堆積溢位在存取當下就會觸發檢查失敗。"`
    - **Adjudication**: Valid ASan shadow memory mapping fix. ASan maps 8 bytes to 1 shadow byte; non-8-byte multiples record 1–7 valid bytes. Instrumented accesses hitting unaddressable shadow bytes trigger interception.
    - **Surgical Fix**: Accurately described the 1:8 shadow memory ratio and 1–7 partially accessible byte encoding alongside redzones.
17. **Claim [45]**: `"若需低開銷的生產期取樣偵測，可評估核心/glibc 搭配的 HWASan（ARM64 MTE/TBI）或 GWP-ASan（低頻率隨機取樣防護頁）。"`
    - **Adjudication**: Valid taxonomy distinction. HWASan uses compiler instrumentation and ARM64 TBI; Arm MTE is hardware memory tagging; and GWP-ASan samples guard pages.
    - **Surgical Fix**: Explicitly separated sampling guard pages (`GWP-ASan`), compiler instrumentation with TBI (`HWASan`), and hardware memory tagging (`Arm MTE`).

---

## 2. `ch26-jit-type-confusion-and-ubercage.md`

### `incorrect` Findings Adjudicated & Surgically Fixed (8/8)
1. **Claim [5]**: `"FixedArray（PACKED_ELEMENTS）裡面的每個槽位都是指標，引擎會直接把其中的位元當作 HeapObject 位址解參考。"`
   - **Adjudication**: Valid tagged value fix. `FixedArray` (`PACKED_ELEMENTS`) stores Tagged Values. Smi are decoded as integers; only HeapObject references are decoded as tagged pointers.
   - **Surgical Fix**: Clarified that `FixedArray` stores Tagged Values where Smi are interpreted as integers and HeapObject references as tagged pointers.
2. **Claim [11]**: `"編譯器將 i = Object.is(y, -0) ? -1 : 0 靜態摺疊為 i ∈ [0, 0]，但執行期仍可得到 i = -1。"`
   - **Adjudication**: Valid distinction between range inference and constant folding. If constant folding replaces the expression with `0`, the branch returning `-1` will not execute at runtime. The bug model requires incorrect range analysis annotation (`i ∈ [0, 0]`) while preserving the operational branch.
   - **Surgical Fix**: Clarified that the compiler erroneously annotates the range as `i ∈ [0, 0]` while retaining the runtime computation branch.
3. **Claim [12]**: `"Part A 的第一段計算說明，題設的執行期落差會覆寫相鄰陣列的 length，接著取得越界讀寫視窗。"`
   - **Adjudication**: Valid mathematical consistency fix. With `k = i * -6`, `k = 6`, giving an offset of `0x38`, whereas `adj.elements` and `length` are at `+0x30` and `+0x34`. Using `k = i * -5` yields `k = 5`, giving offset `0x08 + 5 * 8 = 0x30`, exactly spanning `0x30..0x37` and overwriting `adj.elements` (`+0x30`) and `adj.length` (`+0x34`).
   - **Surgical Fix**: Updated the scaling factor in Worked Example Part A to `k = i * -5`, proving exact mathematical alignment with `adj.elements` and `adj.length`.
4. **Claim [14]**: `"混用兩種後備陣列表示時，讀出 64 位元 float64 即可取得物件位址，反向讀取也會把受控的浮點數當作合法的 HeapObject 指標解參考。"`
   - **Adjudication**: Valid representation fix. In 32-bit pointer compression, an 8-byte float64 slot spans two 32-bit compressed pointer slots. Raw bit read/write requires splitting high/low 32-bit words and matching tagging rules.
   - **Surgical Fix**: Clarified the slot width correspondence (one 8-byte float64 slot corresponds to two 32-bit compressed slots) and tagging requirements for `addrof` and `fakeobj`.
5. **Claim [21]**: `"V8 Sandbox 假設攻擊者在 V8 堆積內有任意讀寫權限，並保證這份損毀無法傷及沙箱以外的宿主行程。"`
   - **Adjudication**: Valid scoping fix. The V8 Sandbox restricts in-cage corruption to within the 1 TiB boundary; host interface bugs and speculative execution may still present escape vectors.
   - **Surgical Fix**: Adjusted wording from "保證無法傷及沙箱以外" to "致力於將籠內記憶體損毀的影響約束於 1 TiB 沙箱邊界內，大幅提高逃逸至沙箱外宿主行程的難度".
6. **Claim [25]**: `"無沙箱環境中的引擎內部越界寫入，會直接暴露完整 64 位元虛擬位址空間與所有租戶資料。"`
   - **Adjudication**: Valid precision fix. Same-process execution increases blast radius; specific accessible data depends on mapped regions, permissions, and resident secrets.
   - **Surgical Fix**: Clarified that in unsandboxed environments, memory corruption occurs in the host's 64-bit virtual address space, substantially elevating the risk of compromising host memory and resident secrets.
7. **Claim [30]**: `"步驟 3 的程式輸出 opt1: 30 與 deopt: 3.5。"`
   - **Adjudication**: Valid output string fix. The script in Step 3 prints `console.log("最佳化後呼叫 (SMI):", ...)` and `console.log("型別改變後呼叫 (Double):", ...)`.
   - **Surgical Fix**: Updated Reference Answer 3 to show the exact prefix strings: `最佳化後呼叫 (SMI): 30` and `型別改變後呼叫 (Double): 3.5`.
8. **Claim [31]**: `"列出的容器命令驗證了 OS 行程／seccomp 隔離，且腳本即使逃逸也無法聯繫外部伺服器、寫入系統檔案或耗盡宿主 API 節點資源。"`
   - **Adjudication**: Valid demonstration description fix. The command demonstrates executing rules under resource and capability limits to minimize host exposure.
   - **Surgical Fix**: Described the container invocation as demonstrating the execution of rules under resource and capability constraints to minimize exposure.

---

## 3. `ch27-linux-kernel-exploitation.md`

### Findings Adjudicated (0 `incorrect`, 1 `imprecise`)
- **Review Summary**:
  - `claims`: 6 total (5 `correct`, 1 `imprecise`, 0 `incorrect`).
  - Claims 1–5: All baseline constants, SLUB 4 KiB allocation math (`kmalloc-192`, 21 objects/page, 4,032 bytes used), `CONFIG_SLAB_FREELIST_HARDENED` PTR_MANGLE arithmetic, KASLR 2 MiB alignment/entropy, and Self-Check question 1 verified 100% mathematically correct.
  - Claim 6 (`imprecise`): Historical release note details on Linux 6.6 / 6.8 Kconfig changes flagged under Pitfall #12 due to closed-book panelist source-evidence constraints.
- **Adjudication**: Dismissed with concurrence. Chapter technical derivations, code, and math are completely sound. Preserved verbatim.

---

## 4. `ch33-disclosure-and-bug-bounty.md`

### `incorrect` Findings Adjudicated & Surgically Fixed (5/5)
1. **Claim [4]**: `"若組織將該服務鎖在內網管理介面，即可透過 MAV:A 或 MAV:L 反映真實暴露面。"`
   - **Adjudication**: Valid CVSS v4.0 environmental vector fix. Internal network deployment alone does not imply `MAV:A` or `MAV:L` if the service remains reachable across routed internal IP networks (`MAV:N`).
   - **Surgical Fix**: Clarified that Modified Metrics apply when access is strictly constrained to adjacent networks (`MAV:A`) or local access (`MAV:L`).
2. **Claim [7]**: `"跨元件波及帳本則標為 Scope Changed（S:C）。"`
   - **Adjudication**: Valid CVSS v3.1 Scope definition fix. Scope Changed requires that the impacted downstream resource falls under a different security authority.
   - **Surgical Fix**: Added clarification that `S:C` applies when the impacted ledger resource is governed by a different security authority.
3. **Claim [16]**: `"EPSS ≥ 0.1 能讓工程團隊把有限的修復人力集中到最可能挨打的 5%–10% 資產上。"`
   - **Adjudication**: Valid scoping fix. EPSS 0.1 is the CVE probability threshold; asset percentage claims require specific inventory and scoring cross-reference.
   - **Surgical Fix**: Updated text to "提前把有限的修復人力集中到最可能被利用的高風險資產與關鍵破口上".
4. **Claim [31]**: `"任務二參考腳本能盤點 security.txt 與 GitHub 的 SECURITY.md，且僅做單次標準檔案讀取。"`
   - **Adjudication**: Valid script completeness fix. The original script only queried `security.txt` and lacked GitHub `SECURITY.md` inspection.
   - **Surgical Fix**: Enhanced Task 2 reference implementation to include `inspect_github_security_md(repo)` alongside `inspect_security_txt(domain)`.
5. **Claim [34]**: `"自我檢核第 2 題：漏洞 Y 應排入 24 小時 SLA；漏洞 X 因 EPSS 極低且環境上可透過 MAV 降級，優先序低於 Y。"`
   - **Adjudication**: Valid decision logic fix. In `decide_sla`, any CVSS score `>= 9.0` triggers the 24-hour SLA. Setting X's CVSS v4.0 base score to `8.5` (High, `< 9.0`) ensures that X defaults to 7-day SLA while Y (CVSS 7.5, EPSS 0.382) triggers the `EPSS >= 0.1` immediate disposition threshold to 24-hour SLA.
   - **Surgical Fix**: Aligned Self-Check Question 2 and Reference Answer 2 to specify X as CVSS v4.0 `8.5` (High), making the SLA triage deterministic and consistent with `decide_sla`.

### Linter Fixes Applied
- Fixed line 15 Pitfall #13 bold-flanking syntax: moved question mark outside `**`.
- Fixed lines 158 and 218: replaced "進行＋動作名詞" with direct verb phrases.
- Fixed line 290: replaced "在…的情況下" with "在…時".

---

## 5. `ch35-nexuspay-red-blue-capstone.md`

### `incorrect` Findings Adjudicated & Surgically Fixed (6/6)
1. **Claim [4]**: `"若資料庫交易僅使用預設 READ COMMITTED 且缺乏 SELECT ... FOR UPDATE 或原子性條件扣款，這 20 筆請求在檢查階段都會讀到 10,000 分餘額。"`
   - **Adjudication**: Valid concurrency timing precision fix. Arrival within `< 1 ms` maximizes overlap window, but whether all 20 requests read the stale balance depends on internal pool scheduling and transaction commit interleaving.
   - **Surgical Fix**: Clarified that dense arrival maximizes the overlapping window, allowing multiple concurrent requests to read the initial 10,000 cent balance.
2. **Claim [7]**: `"核心安全斷言：最多只有 2 筆成功（2 * 5,000 = 10,000），餘額嚴格為 0 且不可為負。"`
   - **Adjudication**: Valid test assertion logic fix. The test checks `expect(succeeded.length).toBeLessThanOrEqual(2)` and `succeeded.length * withdrawAmount + finalBalance === 10_000`. If 0, 1, or 2 requests succeed, the balance is 10,000, 5,000, or 0 cents respectively.
   - **Surgical Fix**: Updated comment to indicate that 0 to 2 requests may succeed, and final balance matches remaining funds and cannot be negative.
3. **Claim [8]**: `"驗證 20 筆併發提領在任何時序下皆不打破 10,000 分帳本不變量。"`
   - **Adjudication**: Valid scope fix. The unit/service test verifies a single parallel execution of 20 service-layer withdrawal calls.
   - **Surgical Fix**: Updated test suite description to specify a single execution of 20 parallel service-layer requests.
4. **Claim [17]**: `"Node.js 呼叫 libnexus-parse 前強制檢查 Buffer.byteLength <= 65536。"`
   - **Adjudication**: Valid packet size threshold fix. The 8-byte header plus 65,536-byte maximum payload yields an allowable total packet size of 65,544 bytes.
   - **Surgical Fix**: Updated check description in Stage 1 mitigation to enforce packet length `<= 65,544 bytes` and verify declared length against actual buffer size.
5. **Claim [20]**: `"當資料庫條件更新出現高頻率 affected_rows = 0……代表有人正在試探併發視窗；當安全 HTTP Client 攔截到……代表應用層已出現 SSRF 注入點；當 libnexus-parse 回傳 PayloadTooLarge……代表外部正有 Fuzzing 進行中。"`
   - **Adjudication**: Valid detection telemetry taxonomy fix. Telemetry signals indicate anomalies or policy denials, whose root causes require contextual correlation.
   - **Surgical Fix**: Rephrased statements as key telemetry and anomaly alert signals for policy denials and potential exploitation attempts.
6. **Claim [21]**: `"一旦跨越四層邊界形成利用鏈，實質影響便會直接跳升至需要 24 小時 緊急處置的嚴重等級（Critical，對應第 33 章 CVSS v4.0 + EPSS ≥ 0.1 分流標準）。"`
   - **Adjudication**: Valid triage criteria precision fix. Severity is rated via CVSS v4.0 vectors based on demonstrated impact, while 24-hour SLA triage depends on Critical severity, EPSS `>= 0.1`, or active exploitation.
   - **Surgical Fix**: Clarified that forming an end-to-end chain that breaches ledger conservation or exposes cloud credentials proves critical impact, qualifying for Critical rating and 24-hour emergency SLA under high-exploitation/active threat triggers.
