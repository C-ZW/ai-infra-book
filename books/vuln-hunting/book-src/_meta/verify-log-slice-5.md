# P4 Adjudication & Bridging Review Log — slice-5

- **Agent**: `p4-adj-5` (`gemini-4-argon-medium`)
- **Date**: `2026-11-21`
- **Assigned Chapters**:
  - `ch21-reverse-engineering.md`
  - `ch25-rust-unsafe-and-ffi.md`
  - `ch28-static-and-variant-analysis.md`
  - `ch29-fuzzing-engineering.md`
  - `ch30-symbolic-execution-and-hybrid-fuzzing.md`

---

## [2026-11-21] ch21-reverse-engineering.md — fixed

- **claim**: 「第 05 行將第一個參數 `rdi` 備份至 callee-saved 暫存器 `rbx`，代表整個函式後續皆以 `rdi` 或 `rbx` 作為同一個結構體指標的基底位址。」
  - **book value**: `rdi` 與 `rbx` 全程皆為原結構體指標
  - **verifier value**: 前段以 `rdi` 讀取原物件，第 16 行 `mov edi, eax` 覆寫 `rdi` 傳遞 `malloc` 大小，呼叫後改由 `rbx` 存取原基底
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 第 16 行寫入 `edi` 會將 `rdi` 改為 `malloc` 參數並清零高 32 位元，故呼叫後僅 `rbx` 保存原基底位址。
  - **tiebreak**: `n/a`
  - **action**: 修正第 173 行，明確區分呼叫前使用 `rdi`、第 16 行覆寫 `edi`、呼叫後由 `rbx` 存取結構體基底。

- **claim**: 「函式並未在移位前將數值擴充為 64 位元（例如 `movsxd`/`mov eax` 後在 `rdi` 上做 `shl rdi, 3`）。」
  - **book value**: 括號示例混入有號擴充 `movsxd` 且未交代暫存器搬移至 `rdi`
  - **verifier value**: 對無號 `uint32_t` 欄位應做數值保持的零擴充（如 `mov edi, dword ptr [rdi+0x4]` 零擴充至 `rdi` 後再做 `shl rdi, 3`）
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — `count` 為 `uint32_t`，使用 `movsxd` 會將 bit 31 符號擴充而破壞無號數值。
  - **tiebreak**: `n/a`
  - **action**: 修正第 191 行，改為 `mov edi, dword ptr [rdi+0x4]` 零擴充至 `rdi` 後執行 `shl rdi, 3`，同時釐清 `65,536 / 8 = 8,192` 的固定 `8-byte` 項目數換算前提、候選結構佈局與局部擬碼描述。

- **claim**: 「在 glibc `ptmalloc2` 中，`malloc(0)` 不會回傳 `NULL`，而是配置一個最小可用 chunk（總計 `0x20 = 32 bytes`，扣掉 `8-byte` chunk header 後僅剩 `24 bytes` 可用寫入空間）。」
  - **book value**: 無條件斷言不回傳 `NULL` 且將配置器內部尺寸當成呼叫端可寫空間
  - **verifier value**: 配置成功時回傳最小 `32-byte` chunk，且零長度請求在語言契約上不應寫入資料
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 補上「當配置成功時」前提，並區分 `0x20 = 32 bytes` 實體 chunk 大小與語言契約上的零長度不可寫入要求。
  - **tiebreak**: `n/a`
  - **action**: 修正第 194–195 行，明確標註配置成功前提、語言契約零長度不可寫入，以及後續寫入迴圈屬未包含於 18 行配置片段的填充邏輯。

- **claim**: 「旗標 P-code 如果沒有被後續任何條件跳躍（`CBRANCH`）讀取，整條旗標計算會被直接刪去。」
  - **book value**: 僅檢查 `CBRANCH`
  - **verifier value**: 旗標亦可供 `CMOVcc`、`SETcc`、`ADC`/`SBB` 等指令讀取，須在後續資料流無任何可觀察用途時才可刪除
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 死碼消除依據 Def-Use 鏈上無任何讀取者，而非僅限條件跳躍。
  - **tiebreak**: `n/a`
  - **action**: 修正第 81–94 行，補齊 Raw P-code 兩次 32 位元寫入的高位清零與旗標步驟、`INDIRECT` 節點定義，以及死碼消除涵蓋 `CBRANCH`/`CMOVcc`/`SETcc`/`ADC`/`SBB` 等所有讀取。

- **claim**: 「所有標準庫與第三方共用函式庫的呼叫都必須經過 `.plt`」以及「透過 XREF 即可直接反查所有呼叫點」。
  - **book value**: 絕對化「所有呼叫都必須經過 `.plt`」
  - **verifier value**: 排除內聯、`-fno-plt` 經 GOT 間接呼叫與 `dlsym` 後，直接呼叫外部匯入函式通常經由 `.plt` 或 `.got`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 章內後文即有提及內聯與 `dlsym`，前文與自我檢核應排除內聯與間接呼叫以保持自洽。
  - **tiebreak**: `n/a`
  - **action**: 修正第 108 行與第 485 行，限定為未內聯的外部匯入函式直接呼叫點。

- **claim**: 「`movzx` 代表原始碼使用無號型別……`movsx` 與 `movsxd` 則明確揭露原始碼是 `int8_t`、`int16_t` 或 `int32_t`。」
  - **book value**: 擴充指令唯一決定原始碼宣告型別
  - **verifier value**: 擴充指令反映該次運算的無號／有號擴充語意，可能源於顯式轉型或整數提升，需結合條件分支與資料流推定候選型別
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — C 整數提升與顯式轉型亦會產生對應擴充指令，應表述為推斷有號／無號運算與候選型別的強力線索。
  - **tiebreak**: `n/a`
  - **action**: 修正第 137 行，精確化擴充指令與資料流型別推定的關係。

- **claim**: 「查出該函式庫可執行區段或檔案映射的起始基底位址……即可算出精準的執行期斷點位址。」
  - **book value**: 將「可執行區段起點」與「檔案映射起始基底位址」混為一談
  - **verifier value**: Ghidra RVA 以映像基底（檔案偏移 `0x0` 的首個 `PT_LOAD` 映射起點）為參照，不可直接加到檔案偏移非零的 `.text` 可執行區段起點上
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 若取 `.text` 區段起點（例如檔案偏移 `+0x1000`）再加上 RVA `0x1446`，會重複加上 `0x1000`。
  - **tiebreak**: `n/a`
  - **action**: 修正第 247–248 行與第 487–488 行，明確指定取對應檔案偏移 `0x0` 的首個 `PT_LOAD` 映像起始基底位址。

- **bridging_review**:
  - **declared_bridge**: `"none"`
  - **detected_bridges**: `[]`（直接以第 20 章 ELF 區段與 System V ABI 切入）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`

---

## [2026-11-21] ch25-rust-unsafe-and-ffi.md — fixed

- **claim**: "`magic = 0x4e58 ('N','X')`，線路位元組為 `58 4e`。"
  - **book value**: `58 4e` 標示為 `('N','X')`
  - **verifier value**: 小端序數值 `0x4e58` 在記憶體／線路位元組為 `58 4e`，對應 ASCII `0x58 = 'X'`、`0x4e = 'N'`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — `0x58` 為 `'X'`、`0x4e` 為 `'N'`，小端序位元組 `58 4e` 依序為 `'X','N'`。
  - **tiebreak**: `n/a`
  - **action**: 修正第 98 行與第 147 行，明確標示小端序位元組 `0x58='X', 0x4e='N'`，並修正第 100 行 `ptmalloc2` `malloc(0)` 最小 chunk 與語言契約說明。

- **claim**: "例如定義 `struct ValidatedTlvLen(u16)`（上限鎖死 `<= 65_536` 且通過邊界檢查才能建構）。"
  - **book value**: `struct ValidatedTlvLen(u16)`
  - **verifier value**: `u16::MAX` 為 `65,535`，無法容納基準合法上限 `65,536`，須使用 `u32` 或 `usize`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — `65,536 = 2^16` 超出 `u16` 最大值 `65,535`。
  - **tiebreak**: `n/a`
  - **action**: 修正第 256 行，改為 `struct ValidatedTlvLen(u32)` 並加註 `65,536` 超出 `u16::MAX` 的位元寬度理由。

- **claim**: "呼叫 `unsafe` 函式或方法（包含所有 FFI 外部函式）。" 及 "Rust 2024 要求即使在 `unsafe fn` 內部，每一處不安全操作也必須顯式包進細粒度的 `unsafe { ... }` 區塊。"
  - **book value**: 「包含所有 FFI 外部函式」且將 `unsafe_op_in_unsafe_fn` 預設警告寫成硬性細粒度強制
  - **verifier value**: `unsafe extern` 區塊中未顯式標註為 `safe` 的外部函式才需 `unsafe` 呼叫；`unsafe_op_in_unsafe_fn` 在 Rust 2024 預設為警告，加上 `#![deny(unsafe_op_in_unsafe_fn)]` 才阻止編譯
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 與同節後文描述的 `pub safe fn` 及 `unsafe_op_in_unsafe_fn` lint 等級對齊。
  - **tiebreak**: `n/a`
  - **action**: 修正第 37–63 行，同時補齊 `copy_tlv_payload` 的來源有效性與不重疊契約。

- **claim**: "任何型別只要進入「讀取未初始化位元組」的狀態，本身就是立即的 UB——哪怕你讀的是 `u8` 也一樣。"
  - **book value**: 未區分 `MaybeUninit<T>` 合法保存／搬移與具現化為需要已初始化的型別值
  - **verifier value**: 將未初始化位元組當作需要已初始化的有效型別值（如 `u8`、`bool`）讀取會造成立即 UB，`MaybeUninit<T>` 則可合法保存未初始化儲存
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 精確區分 `MaybeUninit<T>` 與已初始化型別具現化，並同步修正 Stacked/Tree Borrows 與 LLVM `noalias` 敘述。
  - **tiebreak**: `n/a`
  - **action**: 修正第 72–85 行。

- **claim**: "在本地 `cargo test` 與 `cargo run`（Debug Profile）時，`a + b` 一旦溢位就會觸發 panic 並直接中止行程。"、"Rust 的 `as` 運算子在語意上是無條件截斷或重新解釋位元（lossy cast），永遠不會失敗。"、"只要經過 C ABI（`extern \"C\"`）或 Node.js N-API，Rust 的型別標籤、切片長度與分配器隔離資訊都會全部剝除。"
  - **book value**: Debug panic 直接中止行程、`as` 永遠是 lossy cast、經過 FFI 資訊全部剝除
  - **verifier value**: Debug 溢位觸發執行緒 panic（是否中止行程視 panic 策略與 FFI 邊界而定）；`as` 拓寬可保值，窄化或有號性切換才會截斷或重解讀；裸指標本身不帶切片長度與分配器資訊，須由 FFI 介面顯式傳遞
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 三處文字精確化後更符合 Rust 語言與 ABI 規範。
  - **tiebreak**: `n/a`
  - **action**: 修正第 15 行、第 87–90 行與第 262 行。

- **claim**: "任何跨越 FFI 的 struct 都必須顯式加上 `#[repr(C)]`。" 及 "若 C 端回傳一個未被驗證的整數直接 `transmute` 或透過指標轉型成 Rust `bool` 或 `enum`（例如收到 `0x02`），Rust 在後續 `match` 分支最佳化時會假設「絕對只有這幾個值」並刪除安全分支，直接觸發 UB。"
  - **book value**: 未排除不透明指標（opaque pointer），且把無效 `bool`/`enum` 的 UB 發生時機寫成後續 `match` 時
  - **verifier value**: 需按值傳遞或兩端共同讀寫欄位的 struct 須加 `#[repr(C)]`（不透明指標目標可維持私有佈局）；產生無效 `bool`/`enum` 值的當下即直接觸發語言層級 UB
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — Rust Validity Invariant 規定產生非法 `bool`（如 `0x02`）當下即為立即 UB。
  - **tiebreak**: `n/a`
  - **action**: 修正第 199–205 行。

- **claim**: "分別比較 `cargo test`（Debug）與 `cargo test --release`（Release）的結果差異。"、"Miri 會立即攔截並輸出……（兩個 UB 放在同一個測試）"、"使用 `checked_add`、`try_into()` 與安全的切片邊界重構解析器"
  - **book value**: `parse_frame_safe` 使用 `as usize` 而非 `try_into()`；Debug 模式跳過 `parse_frame_vuln`；兩個 Miri UB 寫在同一個測試函式內（第一個中止後第二個不會執行）
  - **verifier value**: `parse_frame_safe` 改用 `try_into()`；新增 `#[cfg(debug_assertions)] #[should_panic]` 測試實際驗證 Debug 溢位 panic；將兩個 Miri UB 拆成兩個獨立測試函式 `test_miri_aliasing_ub` 與 `test_miri_uninit_ub`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 拆開測試並改用 `try_into()` 後，程式碼與實驗步驟完全一致且可獨立驗證。
  - **tiebreak**: `n/a`
  - **action**: 修正第 311 行、第 410–518 行。

- **bridging_review**:
  - **declared_bridge**: `"none"`（後三分之一 Ch25–Ch37 全面淡出）
  - **detected_bridges**: `[]`（純用資安與 Rust/FFI 原生詞彙）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`

---

## [2026-11-21] ch28-static-and-variant-analysis.md — fixed

- **claim**: 「到達 `buildOrderClause(input)` 時該條件並不成立。」及「`if (!ALLOWED.includes(field))` 裡沒有 `return` 或 `throw`，它的 `False` 分支（即 `ALLOWED.includes(field) == false`）執行完 `auditLog.warn` 後仍然會匯流回 `pool.query(...)`。」
  - **book value**: 到達呼叫時條件「並不成立」；將 `if (!ALLOWED.includes(field))` 在 `includes == false` 時的分支稱為 `if` 的 `False` 分支
  - **verifier value**: 兩條分支匯流後，到達呼叫時白名單條件「不一定成立」；當 `ALLOWED.includes(field)` 為 `false` 時，取反後的 `if (!...)` 條件為 `true`，故進入的是 `if` 的真分支
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 布林取反後，`includes == false` 對應 `if` 條件為 `true`（真分支），匯流後條件未受支配（不一定成立）。
  - **tiebreak**: `n/a`
  - **action**: 修正第 84 行與第 766 行，同時在第 97 行釐清 SSA 無分支範例直接使用 `q_2`、匯流點才插入 `φ` 節點。

- **claim**: 「第一條抓 NestJS/Express 中常見的未驗證租戶邊界（BOLA，見第 6 章）或未參數化查詢。」及「第二條抓 `libnexus-parse` C FFI 解析器裡對 `8 bytes` TLV 檔頭 `len` 做加法溢位後才比對 `65,536 bytes` 上限的經典模式。」
  - **book value**: 正文前導文字將第一條 SQLi 規則說成兼抓 BOLA，將第二條長度污點規則說成只抓加法後比對
  - **verifier value**: 正文第一條 Semgrep 規則抓的是未淨化 HTTP 輸入流入原生 SQL 命令字串（BOLA 規則在「動手做」實作）；第二條規則追蹤未經 `> 65536` 上限守衛淨化便流入 `malloc`/`memcpy` 的外部 `hdr->len`
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 讓前導文字與下方緊接的 YAML 規則語意完全吻合。
  - **tiebreak**: `n/a`
  - **action**: 修正第 121 行。

- **claim**: 「CodeQL 引擎……計算出每一條從 `Source`……抵達 `Sink`……的路徑，並透過 `PathGraph` 輸出完整逐行跳轉軌跡。」
  - **book value**: 「計算出每一條路徑」
  - **verifier value**: 遞迴不動點演算判斷分析模型中 `Source` 到 `Sink` 是否存在未受 `Barrier` 阻斷的可達污點關係，並提供用於解釋命中的流向軌跡
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 含迴圈或多重分支的圖可能存在任意多條路徑，CodeQL 計算的是可達關係與代表路徑圖。
  - **tiebreak**: `n/a`
  - **action**: 修正第 198 行。

- **claim**: 「只消除了『語意上確定不可能造成字串結構逃逸』的路徑（參數陣列位置、整數轉型、白名單成員檢核）。」及「輸入經過 `parseInt(..., 10)` 或 `Number(...)` 強轉為數值（頂多變成 `NaN` 或整數，無法注入 SQL 關鍵字）。」
  - **book value**: `Number(...)` 頂多變成 `NaN` 或整數；`AllowlistGuard` 未說明接收者須為受控白名單常數
  - **verifier value**: `Number(...)` 可產生有限數值（含浮點數）、`Infinity` 或 `NaN`（無法夾帶引號或任意 SQL 語法，但業務範圍與整數性仍需驗證）；`AllowlistGuard` 在跨未知專案使用時需約束接收者為唯讀白名單常數
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 補充 `Number(...)` 值域與 `AllowlistGuard` 接收者約束說明，並修正「動手做」`listSettlementsSafeParseInt` 中把 `req.user.tenantId` 字面插值的寫法為 `$1` 參數綁定。
  - **tiebreak**: `n/a`
  - **action**: 修正第 238 行、第 344 行與第 486 行。

- **claim**: 「同步提交一條高精度規則進 CI/CD，等於把一次性人工修復轉化為全組織永久生效的不變量檢查，阻斷同類漏洞在未來 PR 中回流。」及「改以 Rust 安全切片與 `checked_add`……將『長度溢位』從執行時期隱患收斂為型別系統與編譯期檢查的一部分。」及「NIST SARIF v2.1.0 規範」
  - **book value**: 過度絕對的「永久生效阻斷」；把執行期 `checked_add` 說成編譯期檢查；把 OASIS SARIF 標為 NIST
  - **verifier value**: 規則在其涵蓋範圍與持續執行的專案內攔截回歸樣態；`checked_add` 與安全切片在執行期檢查算術與範圍，並透過回傳型別（`Option`/`Result`）在編譯期強制呼叫端處理失敗；SARIF v2.1.0 為 OASIS 標準
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 三處皆做精確化修正。
  - **tiebreak**: `n/a`
  - **action**: 修正第 30 行、第 404 行與第 802 行。

- **bridging_review**:
  - **declared_bridge**: `"none"`
  - **detected_bridges**: `[]`（純用靜態分析與資安領域原生詞彙）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`

---

## [2026-11-21] ch29-fuzzing-engineering.md — fixed

- **claim**: 「Sanitizers 在記憶體越界、UAF、未定義行為或未初始化讀取發生的當下立即中止行程並產出最小化 PoC。」、「Fuzzing……不驗證『合法輸入是否產生正確結果』。」、「區塊覆蓋率（Block Coverage）只記錄『某個函式是否執行過』。」
  - **book value**: 將 Sanitizer 診斷、行程中止與 PoC 最小化混為單一步驟；排除差分／屬性 Fuzzing；把函式覆蓋率誤寫為區塊覆蓋率
  - **verifier value**: Sanitizer（關閉錯誤恢復後）發出診斷並中止行程，Fuzzer 保存觸發輸入後再由縮減工具最小化；僅監測崩潰的傳統 Fuzzing 不驗證業務輸出，但結合斷言或差分測試即可驗證；记录函式是否執行的是函式覆蓋率（Function Coverage），區塊覆蓋率則記錄基本區塊（Basic Block）
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 三處基本定義均精確修正。
  - **tiebreak**: `n/a`
  - **action**: 修正第 5 行、第 13 行與第 31 行。

- **claim**: 「若程式總邊緣數 E > 4,000，隨機雜湊必出現槽位覆蓋碰撞。」及「在 E <= 1,000 的小型解析器中，雖然出現『至少 1 次碰撞』的機率已達 99.95%，但實際損失的邊緣不到 8 條（0.76%）。」
  - **book value**: `E > 4,000` 寫成「必出現」碰撞；`E <= 1,000` 寫成碰撞率皆達 `99.95%` 且實際損失不到 8 條
  - **verifier value**: `E = 4,000 < 65,536` 時無碰撞機率約 `e^-122`（極高機率碰撞，唯 `E > 65,536` 才依鴿籠原理必然碰撞）；`99.95%` 與期望共槽 `7.58` 條（`0.76%`）是 `E = 1,000` 時的獨立均勻模型期望值
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 區分鴿籠原理必然性與生日模型高機率／期望值，並補上「各邊緣 ID 彼此獨立且均勻隨機分布」前提。
  - **tiebreak**: `n/a`
  - **action**: 修正第 67 行與第 142–170 行。

- **claim**: 「Linux 核心必須建立新行程」是「傳統重新啟動（execve 模式）」中 execve 的作用，以及「Persistent Mode……就能徹底消滅 fork() 與系統呼叫開銷」並能跑滿 10,000 次「不致 OOM」。
  - **book value**: 將 `fork` 建立行程歸給 `execve`；稱 Persistent Mode「徹底消滅 `fork()` 與系統呼叫」及保證不致 OOM
  - **verifier value**: 傳統模式由 `fork()` 建立子行程再由 `execve()` 置換程式映像；Persistent Mode 每批（如 10,000 次）仍重新 `fork()` 一次，是將行程建立與 I/O 開銷攤薄萬倍，並限制單輪微小洩漏的跨輪累積
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 修正系統呼叫分工與攤薄描述。
  - **tiebreak**: `n/a`
  - **action**: 修正第 83–113 行。

- **claim**: ASan 影子記憶體「在每一次記憶體讀取與寫入指令前」都檢查，隔離佇列則「確保任何 UAF 都會命中 0xfd 毒化區」；「必須加 -m none」；「整數回繞或有號溢位只印一行警告便繼續執行」，而「UBSAN_OPTIONS=abort_on_error=1」可單獨使可恢復的檢查終止；「afl-tmin……確保每次刪減後依然觸發相同 Crash。」
  - **book value**: 絕對化 ASan 隔離佇列對所有 UAF 的保證；未提 `halt_on_error=1` 與無號回繞需 `-fsanitize=unsigned-integer-overflow`；把 `afl-tmin` 保留崩潰退出訊號等同於保證相同根因
  - **verifier value**: ASan 檢查受插樁存取與攔截函式，有限容量的隔離佇列只能攔截尚未被移出重用的 UAF；UBSan 執行期終止需 `-fno-sanitize-recover=all` 或 `UBSAN_OPTIONS=halt_on_error=1:abort_on_error=1`（無號回繞非標準 C UB，需額外開啟 `unsigned-integer-overflow`）；`afl-tmin` 保留崩潰退出條件，縮減後應再核對 stack trace 確認根因未偏移
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 逐項精確化 Sanitizer 與 `afl-tmin` 機制。
  - **tiebreak**: `n/a`
  - **action**: 修正第 187–206 行、第 284 行、第 303 行與第 633–638 行。

- **claim**: 「若 alloc_len <= 65536 則 malloc(alloc_len) 並拷貝實際封包殘餘位元組。」、「觸發缺陷 A 時檔案長度約 9–12 bytes，type=0x0002 且 len=0xf8ffffff 附近」、Rust Harness「序列化為合法 TLV 封包」並觸發「FFI 邊界 Crash」與「輸出最小化的 artifact 檔案」。
  - **book value**: 檢查點寫 `alloc_len <= 65536`（程式碼為 `65536 + 8`）；將小端序位元組 `f8 ff ff ff` 寫成十六進位數值 `0xf8ffffff`；Rust Harness 未限制 `payload.len() <= 65536` 且把 Safe Rust 切片 panic 寫成 FFI Crash 與自動最小化
  - **verifier value**: 檢查點對齊 `65536 + 8`（`65,544 bytes`）與 256-byte 拷貝上限；區分小端序檔案位元組 `f8 ff ff ff` 與解碼後無號整數 `0xfffffff8`；在 Rust Harness 中將序列化負載上限鎖定 `<= 65,536 bytes`，並精確描述為觸發切片邊界 panic（搭配 `cargo fuzz tmin` 縮減）
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 全數對齊程式碼與位元組序。
  - **tiebreak**: `n/a`
  - **action**: 修正第 327 行、第 339 行、第 501 行與第 583–605 行。

- **bridging_review**:
  - **declared_bridge**: `"none"`
  - **detected_bridges**: `[]`（純用 Fuzzing 與二進位安全原生詞彙）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`

---

## [2026-11-21] ch30-symbolic-execution-and-hybrid-fuzzing.md — fixed

- **claim**: "只要修改任何一個位元組，校驗和就會立即失效。" 及 "凡是觸發 Crash 的輸入都是 100% 真陽性。" 及 "Concolic 的關鍵優勢在於「永遠不會因為找不到環境狀態而卡死」。"
  - **book value**: 未限定為「受校驗保護的欄位位元組」；將 Crash 直接等同 100% 目標漏洞真陽性；絕對化 Concolic 永遠不會卡死
  - **verifier value**: 修改受校驗算式涵蓋的檔頭與核心負載欄位位元組會使校驗和失效（尾端 `extra` 位元組未納入算式）；Crash 代表真實可重現的執行期異常（排除 Harness 或環境設定問題後即確認為目標缺陷）；Concolic 在具體執行能正常跑完時，可藉由具體化（concretization）跨過缺乏符號模型的外部函式
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 三處語意收斂至嚴密表述。
  - **tiebreak**: `n/a`
  - **action**: 修正第 5 行、第 16 行與第 60 行。

- **claim**: "均勻隨機期望嘗試次數（50% 機率命中）：2^31 = 2,147,483,648 次。"、"由 C3 ∧ C4 → 選取合法最小邊界低 16 位元 0xFFF9。"、"0x0001FFF9 × 0x9E3779B1 = 0x00013C6C_9FDDAC29。"
  - **book value**: 將無放回隨機排列平均次數 `2^31`（50% 候選空間）與有放回隨機抽樣期望次數（`2^32`）混寫；稱 `0xFFF9` 為最小合法低 16 位元（實際 `0xFFF8..0xFFFB` 皆滿足 `< 4`，`0xFFF9` 對應最小正配置尺寸 `1 byte`）；64 位元完整乘積高 32 位元誤寫為 `0x00013C6C`
  - **verifier value**: 明確區分「無放回完整枚舉最壞／有放回抽樣期望 `2^32` 次（`9.94 天`）」、「無放回隨機排列平均 `2^31` 次（`4.97 天`）」與「有放回累積命中率 50% 之 `ln(2) × 2^32` 次（`6.89 天`）」，並寫出三欄位獨立均勻抽樣聯合機率 `(1 × 4 × 1) / 2^96 = 2^-94 < 2^-80`；註明合法低 16 位元為 `0xFFF8..0xFFFB`（選取讓回繞後等於 `1` 的 `0xFFF9`）；修正完整 64 位元乘積為 `0x0001FFF9 × 0x9E3779B1 = 0x00013C6A_9FDDAC29`（低 32 位元 `0x9FDDAC29` 與 `csum = 0xEEB5AD7C` 完全不變）
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 驗算 `0x0001FFF9 * 0x9E3779B1 = 131065 * 2654435761 = 347898612935465 = 0x00013C6A_9FDDAC29`，低 32 位元仍為 `0x9FDDAC29`。
  - **tiebreak**: `n/a`
  - **action**: 修正第 94–137 行。

- **claim**: "依照 libnexus-parse 規格加入 state.solver.add(sym_len <= 65536)。" 及 "Concolic Execution 只在單一具體執行路徑上保留 32 個線性分支點並逐一嘗試反轉，記憶體僅維持 O(32) 級別。"
  - **book value**: 在 Claripy/Z3 位元向量上直接用有號 `<=` 限制無號長度 `sym_len`；將單路徑分支紀錄 `O(k)` 直接簡寫為總記憶體 `O(32)`
  - **verifier value**: 位元向量無號上限約束應使用 `claripy.ULE(sym_len, 65536)`（避免最高位元為 1 的超大無號長度在有號比較下被當成負數放行）；明確說明單次具體執行的線性分支條件紀錄為 `O(k)`（`k = 32`），連同單路徑符號狀態遠小於 `O(2^k)` 狀態樹
  - **flagging families**: `codex:gpt-6.2-sol:low`
  - **arbiter**: `agrees=true conf=high` — 與本章強調的 `ULT`/`ULE` 無號位元向量比較規則完全一致。
  - **tiebreak**: `n/a`
  - **action**: 修正第 252 行與第 512 行。

- **bridging_review**:
  - **declared_bridge**: `"none"`
  - **detected_bridges**: `[]`（純用符號執行、SMT 與二進位安全原生詞彙）
  - **isomorphism_score**: `5`
  - **conversational_phrases**: `[]`
  - **verdict**: `pass`
