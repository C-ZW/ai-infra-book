# P4 Round-2 Adjudication & Surgical-Fix Log — `slice-5`

- **Agent**: `p4-r2-5` (`gemini-4-argon-medium`)
- **Reviewer Cache**: `books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/` (`codex:gpt-6.2-sol:medium`)
- **Assigned Slice (`slice-5`)**:
  1. `ch21-reverse-engineering.md`
  2. `ch25-rust-unsafe-and-ffi.md`
  3. `ch28-static-and-variant-analysis.md`
  4. `ch29-fuzzing-engineering.md`
  5. `ch30-symbolic-execution-and-hybrid-fuzzing.md`

---

## 1. `ch21-reverse-engineering.md`

### `incorrect` Findings Adjudicated & Fixed (5/5)
1. **Claim**: `"「這些關鍵 Sink 的名稱與呼叫點永遠不會因為 strip -s 而消失。」"`
   - **Adjudication**: Valid technical refinement. While `.dynsym`/`.dynstr` and `.rela.plt`/`.plt` preserve symbol names and direct PLT/GOT call sites after `strip -s`, compiler-inlined calls (e.g., small `memcpy` expanded to SIMD/rep instructions) or runtime `dlsym` indirect calls do not go through a named PLT stub.
   - **Surgical Fix**: Clarified in `### Stripped Binary 的真相` and `### 函式邊界識別與標準庫指紋` that `strip -s` cannot remove dynamic symbol entries or direct call sites routed through `.plt`/`.plt.sec`/`.got` relocations, while inlined operations and `dlsym` calls require instruction-pattern or dynamic analysis.
2. **Claim**: `"「INT_LEFT 等微操作：先依移位量計算 CF、ZF、SF 等狀態旗標，再執行 EAX = EAX << 3。」"`
   - **Adjudication**: Genuine data-flow order defect. `ZF` (zero check) and `SF` (sign bit) depend on the 32-bit shifted result of `EAX << 3`, whereas `CF` is determined by the last bit shifted out of the original value.
   - **Surgical Fix**: Reordered step 4 of the Raw P-code sequence so `CF` and `EAX = EAX << 3` are evaluated first, followed by updating result-dependent flags (`ZF`, `SF`, `PF`) and `RAX = zext(EAX)`.
3. **Claim**: `"「某個 32 位元無號變數被預設推測為有號 int 或未定義寬度的 undefined4。」"`
   - **Adjudication**: Valid defect. Ghidra's `undefined4` explicitly denotes a known 4-byte (`32-bit`) width whose concrete type and signedness remain undetermined.
   - **Surgical Fix**: Updated wording to `已知寬度為 4 bytes 但具體型別與符號性尚未確定的 undefined4`.
4. **Claim**: `"「紀錄……相對位址偏移（假設 Ghidra 基底為 0x00100000，位址為 0x00101xxx，則檔內偏移即為 0x1xxx）。」"`
   - **Adjudication**: Valid ELF terminology fix. Subtracting `ImageBase` yields the Relative Virtual Address (RVA); converting to a physical file offset additionally depends on the `PT_LOAD` segment's `p_vaddr` and `p_offset`.
   - **Surgical Fix**: Renamed the difference to RVA (`相對於映像基底的相對虛擬位址偏移 RVA`) and noted `PT_LOAD` `p_vaddr`/`p_offset` mapping, and aligned Self-Check #4 to specify matching static and runtime reference bases of the same `PT_LOAD` segment.
5. **Claim**: `"「讓編譯器在能推導緩衝區大小的場景將 memcpy/strcpy 替換為附帶邊界檢查的 __memcpy_chk。」"`
   - **Adjudication**: Valid accuracy fix. `memcpy` and `strcpy` map to distinct fortified functions (`__memcpy_chk` vs. `__strcpy_chk`), and calls statically proven safe at compile time do not emit runtime check calls.
   - **Surgical Fix**: Updated the `-D_FORTIFY_SOURCE=3 -O2` bullet to distinguish `__memcpy_chk` and `__strcpy_chk` and note compile-time proof vs. runtime checking.

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Clarified SIB addressing (`[rbx + rcx*8 + 0x10]`) under a unit-stride raw index `rcx`; refined Lab Step 3 reference answer to describe the 4 candidate fields covering the observed 16-byte access range (matching `nexus_tlv_ctx_t`) and missing destination capacity check on `trace_buf[32]`.
- **Dismissed**: Closed-book nitpicks requesting live build logs or empirical surveys on `.eh_frame` FDE percentage / FLIRT CRC byte ranges / pwn.college UI syllabus paths (already covered by `_meta/landscape-2026-11.md` and instructional design).

---

## 2. `ch25-rust-unsafe-and-ffi.md`

### `incorrect` Findings Adjudicated & Fixed (7/7)
1. **Claim**: `"只要這條跨界鏈路上有任何一個 unsafe 區塊違背了 Rust 的 Soundness 不變量，或是 N-API 沒有守住外部記憶體的跨執行緒生命週期，前面二十四章出現過的所有記憶體損毀原語……都會在 Rust 編譯器完全靜默的情況下重新出現。"`
   - **Adjudication**: Valid precision fix. The compiler still enforces normal type and borrow checks inside `unsafe`, and each specific precondition violation maps to its corresponding memory corruption class.
   - **Surgical Fix**: Updated the introduction to explicitly map each violated precondition (length wrap-around/unchecked pointer copy -> OOB write/heap corruption; `MaybeUninit`/padding misuse -> uninitialized read; N-API cross-thread lifetime mismatch -> UAF) while noting that ordinary type/borrow checks still run inside `unsafe`.
2. **Claim**: `"`unsafe` 關鍵字在 Rust 語言規範中只開啟五項特定操作權限（俗稱五種超能力）"`
   - **Adjudication**: Valid syntactic distinction. Four operations are unlocked inside `unsafe { ... }` blocks, whereas implementing an `unsafe trait` uses `unsafe impl` at the declaration site (alongside `unsafe fn`, `unsafe trait`, and Rust 2024 `unsafe extern`).
   - **Surgical Fix**: Distinguished block-level operations from declaration-site contracts in the 5-item list.
3. **Claim**: `"後續所有緩衝區配置函式只接受安全型別，徹底消除重複檢查漏網之魚。"`
   - **Adjudication**: Valid refinement. A validated length newtype (`ValidatedTlvLen`) enforces the numeric protocol bound (`<= 65_536`), but the parser must still verify that the actual input buffer length is at least `8 + len`.
   - **Surgical Fix**: Added explicit mention that the parser must still check `raw.len() >= 8 + len` against the actual input buffer.
4. **Claim**: `"可用空間僅 16 bytes (0x10)，實際寫入 512 bytes (0x200)：越界寫入量 = 512 - 16 = 496 bytes (0x1f0 bytes)！"`
   - **Adjudication**: Valid distinction between language/API contract and physical allocator layout. At the language contract level, `malloc(0)` grants `0 bytes` of writable capacity (so all `512 bytes` are out of bounds, matching ASan's `0-byte region` report); at the `ptmalloc2` `0x20` minimum chunk physical layout level, `+0x10` to `+0x20` spans `16 bytes`, so a 512-byte write extends `496 bytes` (`0x1f0`) past the next chunk boundary.
   - **Surgical Fix**: Explicitly separated the language/API contract level (`0 bytes` valid capacity, 512B OOB / UB) and the `ptmalloc2` physical chunk layout level (`16 bytes` to `+0x20`, extending `496 bytes` past the adjacent chunk header).
5. **Claim**: `"只要這四個環節中的加法回繞、有號轉型與 FFI 邊界沒有守住，actual_avail 與 hdr.len 之間的落差就會把 0x20 chunk 變成任意堆積毀損的起點。"`
   - **Adjudication**: Valid scoping fix. Also noted pointer alignment precondition when casting `raw as *const TlvHdr`.
   - **Surgical Fix**: Scoped the conclusion to the memory safety defect caused by the mismatch between `total_alloc` and `copy_len`, and noted the 4-byte alignment requirement of `raw as *const TlvHdr`.
6. **Claim**: `"一旦這個結構體透過 memcpy 或 N-API Buffer::from 序列化傳出，堆疊上殘留的記憶體碎片就會跟著送出。"`
   - **Adjudication**: Valid fix. Leaking requires copying out the raw storage representation containing residual stack/heap data in unzeroed padding holes (and forming `&[u8]` over uninitialized padding in Rust is itself immediate UB).
   - **Surgical Fix**: Clarified raw storage copy vs. field-by-field serialization and noted that reading uninitialized padding as `&[u8]` in Rust violates validity invariants.
7. **Claim**: `"C 函式庫配置出的物件，只能透過該 C 函式庫導出的專屬釋放函式（例如 nexus_frame_free(ptr)）在 Rust 的 Drop trait 實作內呼叫回收"`
   - **Adjudication**: Valid refinement. Deallocation must follow the pairing contract specified by the C API (an exported teardown function or a compatible `free` from the shared C runtime heap), optionally wrapped in Rust `Drop`.
   - **Surgical Fix**: Updated `### 4. 跨分配器釋放與 FFI 指標所有權混亂` to reflect API-contract-paired deallocation and `Drop` encapsulation.

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Clarified `MaybeUninit<[u8; 64]>` partial initialization via low-level read interfaces; separated narrowing (`u64 as u32`), same-width reinterpretation (`u32 as i32`), and sign-extending widening (`i32 as usize` on 64-bit); noted scaled 32-bit offsets in V8 Sandbox; distinguished Stacked Borrows (stack) vs. Tree Borrows (tree) in Self-Check #3.
- **Dismissed**: Closed-book cross-chapter context checks (`TB-4` in Ch01) and requests for live terminal transcripts.

---

## 3. `ch28-static-and-variant-analysis.md`

### `incorrect` Findings Adjudicated & Fixed (4/4)
1. **Claim**: `"Barrier：切斷兩類已證明安全的污點路徑。"`
   - **Adjudication**: Valid precision fix. In the QL query, `AllowlistGuard` checks method name (`includes`/`has`) and argument count, and `numCall` checks callee names (`parseInt`/`Number`), which are practical engineering approximations for the target codebase rather than formal proofs of safety for arbitrary receivers.
   - **Surgical Fix**: Updated the code comment and accompanying prose to describe these barriers as codebase-specific engineering approximation models and documented the additional constraints needed for untrusted third-party repos.
2. **Claim**: `"在固定 Sink 集合並針對該程式碼庫既有的常數白名單與數值轉型模式加入 isBarrier 後，Precision 從 9.09% 提升到 50.0% 且維持了 100.0% Recall。"`
   - **Adjudication**: Genuine arithmetic attribution fix. From the baseline (`5 / 55 = 9.09%`), Step 1 restricts `isSink` to argument 0, bringing Precision to `5 / 40 = 12.50%`. With the Sink set fixed after Step 1, adding the two `isBarrier` steps (Steps 2 & 3) raises Precision from `12.50%` (`5 / 40`) to `50.0%` (`5 / 10`). Also aligned the prose description of the baseline query's method list with the final query.
   - **Surgical Fix**: Explicitly stated both the Step 1 sink-restriction effect (`9.09% -> 12.50%`) and the fixed-sink barrier effect (`12.50% -> 50.0%`), totaling `9.09% -> 50.0%`.
3. **Claim**: `"malloc(0) 配置最小區塊後，memcpy 卻讀入無號的 hdr->len（4,294,967,288 位元組），造成毀滅性堆積溢位。"`
   - **Adjudication**: Valid C standard / allocator precision fix. `malloc(0)` may return `NULL` or a non-null pointer granting `0 bytes` of writable capacity; passing `4,294,967,288` to `memcpy` on a non-null result immediately triggers out-of-bounds write UB.
   - **Surgical Fix**: Updated Self-Check #3 answer to note `malloc(0)` return semantics (`NULL` or zero-capacity pointer / `0x20` glibc chunk) and the resulting OOB write UB.
4. **Claim**: `"藉由回傳型別（Option／Result）在編譯期強制呼叫端顯式處理執行期溢位與切片邊界檢查失敗。"`
   - **Adjudication**: Valid Rust semantics fix. `Option`/`Result` require unpacking the success branch before using the inner value, but callers can still discard a return value or call `.unwrap()` unless paired with lint rules (`#![deny(unused_must_use)]`, Clippy `unwrap_used`).
   - **Surgical Fix**: Clarified that `Option`/`Result` encode failures in the type system so callers must unpack the success value, and pairing with `#![deny(unused_must_use)]` and Clippy rules enforces explicit error handling.

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Clarified that static analysis precision/performance depends on both the IR level and the analysis algorithm/abstractions/models; refined AST description (retains syntax order/branch structure, lacks execution reachability/dominance graph); aligned the Patch Diffing example's pre-patch condition to `if (sz <= 65536 + 8)` so it matches the 65,536-byte payload limit plus 8-byte header; noted two's complement implementation semantics for `(int32_t)0xFFFF_FFF8 == -8`.
- **Dismissed**: Closed-book external tool version checks (Semgrep Tree-sitter language count, CodeQL CLI packaging details) already grounded in `_meta/landscape-2026-11.md`.

---

## 4. `ch29-fuzzing-engineering.md`

### `incorrect` Findings Adjudicated & Fixed (4/4)
1. **Claim**: `"你明確寫出輸入範圍、邊界斷言與預期輸出，藉此證明程式碼在設計路徑上表現正確。"`
   - **Adjudication**: Valid software-testing distinction. Unit and property tests verify that the tested inputs satisfy the specified assertions, but finite test cases cannot exhaustively prove correctness for all inputs along a path.
   - **Surgical Fix**: Updated `## 從你已知的出發` to state `藉此驗證受測案例在設計路徑上符合指定的業務斷言（但有限的測試案例只能證明已執行的輸入點符合斷言，無法窮舉證明整條路徑或整個輸入空間對所有可能輸入皆無缺陷）`.
2. **Claim**: `"經典隨機雜湊插樁 (afl-clang-fast / trace-pc-guard 64 KiB map)"`
   - **Adjudication**: Genuine instrumentation classification fix. Classic XOR (`cur_loc ^ (prev_loc >> 1)`) is `CLASSIC` mode, whereas `trace-pc-guard` (`PCGUARD`) assigns per-edge guard IDs rather than XORing block IDs (and was listed in item `[2]` of the same diagram).
   - **Surgical Fix**: Updated `[1]` in the ASCII comparison diagram to `(CLASSIC XOR 模式：cur_loc ^ (prev_loc >> 1))` and `[2]` to `(afl-clang-lto 連續索引 / PCGUARD 獨立守衛)` while preserving exact 70-column box width, and clarified in the prose that enlarging `AFL_MAP_SIZE` to reduce collisions requires an instrumentation mode whose index space scales beyond 16-bit XOR.
3. **Claim**: `"用預設 64 KiB 位圖直接 Fuzzing 超過 10,000 條邊的大型函式庫，導致逾 6–15% 的新邊緣互相覆蓋而漏報。"`
   - **Adjudication**: Valid mathematical alignment with the chapter's own birthday-paradox table. Under the uniform 65,536-slot model, cumulative expected lost-edge ratio is `7.26%` at `E = 10,000` and `20.88%` at `E = 32,000` (exceeding 15%), while the marginal probability that a single new edge lands on an already-occupied slot after `10,000` edges (`~9,274` occupied slots) is `~14.15%`.
   - **Surgical Fix**: Stated both the batch expected collision ratio (`7.26%` to `20.88%` for `10,000`–`32,000` edges) and the marginal slot-occupancy collision probability (`14.15%` at `10,000` edges) in `### 2. 位圖碰撞盲區與過大輸入稀釋吞吐`.
4. **Claim**: `"強制 UBSan 在抓到異常的瞬間發出 SIGABRT 中止行程。"`
   - **Adjudication**: Valid compiler/runtime flag distinction. `-fno-sanitize-recover=all` disables recovery (causing termination on detected UB), while `UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1` (or `AFL_USE_UBSAN=1`) configures the runtime to terminate via `abort()` (`SIGABRT`) so AFL++ classifies it as a crash. Also clarified Self-Check Q3 so the target is compiled with `afl-clang-fast -fsanitize=address,undefined` and actually executes the signed overflow path.
   - **Surgical Fix**: Updated the UBSan section and Self-Check Q3/A3 to distinguish `-fno-sanitize-recover=all` from `abort_on_error=1` (`SIGABRT`) and specified `afl-clang-fast` plus path execution in Q3.

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Clarified hit-count bucket novelty (a seed is saved when a slot exhibits a bucket bit never seen in any prior execution); fixed the `E = 4,000` table entry from `~100.00% (e^-122)` to `~100% (1-e^-122)` (preserving exact 19-char column width) since `e^-122` is the no-collision probability.
- **Dismissed**: Closed-book requests for live benchmark logs on ASan/MSan CPU multipliers or discovery times.

---

## 5. `ch30-symbolic-execution-and-hybrid-fuzzing.md`

### `incorrect` Findings Adjudicated & Fixed (7/7)
1. **Claim**: `"無放回隨機排列平均嘗試次數（50% 候選空間）：2^31 = 2,147,483,648 次。"`
   - **Adjudication**: Genuine discrete-probability off-by-0.5 distinction. In a uniform random permutation of `N = 2^32` items without replacement, `2^31 = 2,147,483,648` is the exact 50% cumulative hit threshold, while the expected number of trials (including the winning trial) is `(N + 1) / 2 = 2,147,483,648.5`.
   - **Surgical Fix**: Updated the worked example line to state both the 50% cumulative hit threshold (`2^31 = 2,147,483,648`) and the exact expected trial count (`(2^32 + 1)/2 = 2,147,483,648.5`), both corresponding to `~4.97 天` at `5,000 exec/s`.
2. **Claim**: `"面對 if (checksum(pkt) == pkt->csum)，無論位元翻轉或 Havoc 變異，單次成功機率都只有 2^-32。"`
   - **Adjudication**: Valid probabilistic model qualification. `2^-32` is the single-trial hit probability under uniform independent sampling over the 32-bit checksum space (whereas deterministic single-bit flips from a distant seed have `0` probability of hitting the unique valid 32-bit checksum).
   - **Surgical Fix**: Qualified the `2^-32` figure with the uniform independent sampling model and noted the zero hit rate of single-step bit flips when Hamming distance > 1.
3. **Claim**: `"magic == 0x4E58（'NX'）、type == 0x0013、len == 12。"`
   - **Adjudication**: Valid endianness clarification. The 16-bit integer `0x4E58` has high byte `0x4E` (`'N'`) and low byte `0x58` (`'X'`), which serializes in little-endian wire order as `58 4e` (`"XN"`).
   - **Surgical Fix**: Clarified high/low ASCII bytes (`'N'`, `'X'`) and little-endian wire bytes (`58 4e`, `"XN"`).
4. **Claim**: `"低 16 位元經過 + 8 後必須回繞小於 4，而漏洞點恰巧就是後續用這個截斷後的低 16 位元計算緩衝區索引。"`
   - **Adjudication**: Valid consistency fix between prose and reference C code (`nexus_tlv_sym.c`). In `trigger_overflow`, the truncated low 16-bit value `((amount_delta + 8) & 0xFFFF)` is used as the `malloc(alloc_sz)` allocation size (`1–3 bytes`) prior to a fixed `8`- or `16`-byte `memcpy`, not as an array index.
   - **Surgical Fix**: Updated item 3 in the worked example to state `作為 malloc 配置尺寸（僅配置 1–3 bytes 緩衝區卻複製 8 或 16 bytes 固定長度標記資料）`.
5. **Claim**: `"切勿直接寫 sym_len <= 65536，否則有號比較會放行最高位元為 1 的超大無號長度。"`
   - **Adjudication**: Genuine API distinction between Claripy and Z3Py. In Z3Py, `<=` on `BitVec` defaults to signed comparison (`SLE`), whereas in Claripy, `<=` on `BVS` defaults to unsigned (`ULE`).
   - **Surgical Fix**: Clarified in Failure Mode #1 that while Claripy `BVS` `<=` defaults to unsigned, raw Z3Py `BitVec` `<=` defaults to signed (`SLE`), so explicitly calling `claripy.ULE(sym_len, 65536)` / `z3.ULE` prevents cross-API signedness bugs.
6. **Claim**: `"把 SHA-256 的 64 輪壓縮函式轉成 Z3 BitVec 公式並求逆像，等價於用通用 SAT 求解器暴力破解密碼學雜湊，會在 solver 內部造成指數級別的計算凍結。"`
   - **Adjudication**: Valid theoretical refinement. Bit-blasting to CNF SAT does not make CDCL search literally identical to brute-force enumeration, though inverting full 64-round SHA-256 over hundreds of thousands of coupled boolean clauses practically causes solver timeouts.
   - **Surgical Fix**: Rephrased to describe bit-blasting into hundreds of thousands of coupled boolean clauses for a cryptographic one-way hash, causing practical CDCL solver timeouts.
7. **Claim**: `"先用 clang -fsanitize=address -g nexus_tlv_sym.c -o nexus_tlv_sym_asan 編譯供驗證崩潰與 AFL++ 使用。"`
   - **Adjudication**: Valid build-command consistency fix. Plain `clang -fsanitize=address` has no AFL++ coverage instrumentation; the reference solution compiles both `nexus_tlv_sym_asan` (with `clang`) and `nexus_tlv_sym_afl` (with `afl-clang-fast`).
   - **Surgical Fix**: Updated Lab Step 2 to list both the `clang` command (`nexus_tlv_sym_asan` for standalone ASan crash verification) and the `afl-clang-fast` command (`nexus_tlv_sym_afl` for AFL++ fuzzing).

### High-Value `imprecise` Findings Resolved & Remaining Dismissals
- **Resolved**: Specified that the 32-bit checksum covers `magic`, `type`, `flags`, and `amount_delta`; unified the foreign sync directory path `-F sym_foreign` across prose, lab instructions, and reference commands; added `s.add(((amount_delta + 8) & 0xFFFF) == 1)` in `solve_tlv_z3.py` so the script deterministically outputs `amount_delta = 0x0001fff9` (`alloc_sz = 1 byte`) matching the prose walkthrough.
- **Dismissed**: Closed-book citation checks on SymCC (USENIX Security 2020), SymQEMU (NDSS 2021), QSYM (USENIX Security 2018), and angr v10 metadata (all verified against `_meta/landscape-2026-11.md`).

---

## Verification Gate Results
- `lint_book.py`: **0 errors, 0 warnings** across all chapters.
- `check_diagrams.py`: **`{"passed": true, "findings": []}`** (0 misaligned diagrams).
