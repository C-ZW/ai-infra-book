# P4 Round-2 跨模型審查裁決與外科修補日誌（Slice New2: Ch22, Ch24, Appendix-A）

- **審查面板**：`codex:gpt-6.2-sol:medium`（Round-2 快取：`books/vuln-hunting/book-src/_meta/review-sol62-medium-cache/`）
- **負責範圍**：
  1. `ch22-stack-overflow-and-rop.md`（快取：`ch22-stack-overflow-and-rop.json`）
  2. `ch24-advanced-heap-and-allocators.md`（快取：`ch24-advanced-heap-and-allocators.json`）
  3. `appendix-a-lab-index.md`（全書 37 章完稿狀態同步）
- **基準核對**：全數嚴格對齊 `_meta/running-examples.md` 全書基準數字表，零變更基準常數。

---

## 1. `ch22-stack-overflow-and-rop.md`

### `verdict == "incorrect"` 裁決與修補（7 項全數修正）

1. **高階語言邊界保護與呼叫堆疊隔離的描述精確化**
   - **審查意見**：語言層存取規則無須依賴回傳位址與區域變數分開存放；JavaScript / TypeScript 越界讀取多得 `undefined`，Go 與 Rust 的受檢查索引才通常觸發 panic。
   - **裁決與修補**：成立。修訂第 11 行，明確說明高階語言由執行環境與編譯器維護抽象與邊界，區分 JS/TS 越界讀取（回傳 `undefined`）與 Go/Rust（觸發 panic），避免將抽象隔離表述為實體記憶體分區。
2. **行程異常終止、訊號交付與連鎖雪崩的因果邊界**
   - **審查意見**：`#CP` 為 CPU 異常，行程是否終止取決於作業系統訊號交付與預設處置；服務層是否連鎖雪崩取決於重試、流量隔離與容錯策略，非必然單向因果。
   - **裁決與修補**：成立。修訂第 30 行，明確說明 `__stack_chk_fail()`（觸發 `SIGABRT`）與 `#CP`（Linux 使用者態通常交付為 `SIGSEGV`）之預設終止行為，並將服務層雪崩限定於缺乏請求隔離或容錯降級之場景。
3. **Worked Example 堆疊幀絕對位址與局部配置位移修正**
   - **審查意見**：呼叫前 `RSP = 0x7fffffffdd00`，`call` 與 `push rbp` 共消耗 16 bytes，`RBP` 應為 `0x7fffffffdcf0`；局部配置 `0x50`（80 bytes）後配置區低端應為 `0x7fffffffdca0`。原表 `RBP` 誤植為 `dce0`，相差 `0x10`。
   - **裁決與修補**：成立。全面重算並更新 Worked Example 堆疊幀分佈表：
     - `0x7fffffffdca0 - dca7` [rbp - 0x50]：對齊填充 / 區域長度變數（8 bytes）
     - `0x7fffffffdca8 - dce7` [rbp - 0x48]：`buf[0..63]`（64 bytes）
     - `0x7fffffffdce8 - dcef` [rbp - 0x08]：Stack Canary（8 bytes）
     - `0x7fffffffdcf0 - dcf7` [rbp + 0x00]：Saved RBP（8 bytes）
     - `0x7fffffffdcf8 - dcff` [rbp + 0x08]：Saved RIP（8 bytes）
     - 驗算：`0x7fffffffdcf8 - 0x7fffffffdca8 = 0x50`（80 bytes），總幀長 `96 bytes`（16-byte 對齊），完全自洽。
4. **`memcpy` 越界行為之規範與編譯產物表述**
   - **審查意見**：超過物件大小之複製屬於 C 未定義行為，標準未保證循序寫入順序，不可直接以 C 源碼保證逐位元組覆寫結果。
   - **裁決與修補**：成立。修訂第 75 行，明確標明為「在上述典型堆疊排列與常見循序拷貝產物下」，指出超過 64 位元組即構成未定義行為的越界寫入，並分析其接連覆寫 Canary 與回傳位址之結構風險。
5. **System V AMD64 ABI 引數暫存器分類規範**
   - **審查意見**：`RDI..R9` 暫存器序列僅適用於整數類（INTEGER class）引數，浮點數使用 SSE 向量暫存器（`XMM0..XMM7`），引數序號無法單獨決定暫存器。
   - **裁決與修補**：成立。修訂第 82 行，補充「整數類（INTEGER class，如整數與指標）」之 ABI 分類前提，並補充浮點引數依 SSE 規則使用 XMM 暫存器。
6. **Stack Canary 模式範圍與保護條件修訂**
   - **審查意見**：`-fstack-protector` 亦保護含 `alloca` 之函式；`-fstack-protector-strong` 擴大至區域陣列與取址變數；Canary 偵測的是函式尾聲比對時之差異，非僅「連續寫入」。
   - **裁決與修補**：成立。修訂第 104–105 行，精確闡述基本模式（字元陣列門檻與 `alloca`）與 strong 模式（區域陣列、結構體陣列、框架取址變數）之觸發規則，並將失效邊界精準定義為「跳過 Canary 的不連續索引寫入，或洩漏原值後精確寫回」。
7. **硬體防禦表頭語意修正與動手做反組譯特徵對齊**
   - **審查意見**：Shadow Stack 與 PAC 於 `ret` 或指標使用時驗證，並非阻擋一般資料寫入；動手做編譯指令同時含 Canary、CET 與 FORTIFY，解答編號遺漏第三項特徵。
   - **裁決與修補**：成立。
     - 修訂第 127 行總表欄位為「能否在 ret / 間接分支時阻斷被竄改的控制流」，明確標示 Shadow Stack 與 PAC 的攔截時機。
     - 修訂動手做第 191 行文字為「Canary + CET + FORTIFY」對照組，並在參考解答補齊三大防禦特徵（`endbr64` 著陸標記、`fs:0x28` Canary 比對、`__memcpy_chk@plt` 強化呼叫）。

### 關鍵 `imprecise` 補強
- **W^X 分頁政策與典型權限**（第 3 行）：明確標明分頁層級原則與典型 R-X / RW- 映射。
- **NX 防禦邊界**（第 16 行）：明確阻斷「Shellcode 注入堆疊」與既有可執行映射區段重用。
- **格式字串缺陷未定義行為與洩漏機制**（第 84 行）：明確區分缺少實參的未定義行為與 ABI 讀取殘留暫存器／堆疊之現象。
- **`_FORTIFY_SOURCE=3` 條件與模式**（第 94–97 行）：標明 GCC 12 / Clang 9 與 glibc 2.34+ 動態大小推導、`(size_t)-1` 未知大小退化行為。

---

## 2. `ch24-advanced-heap-and-allocators.md`

### `verdict == "incorrect"` 裁決與修補（7 項全數修正）

1. **自訂配置器掛載途徑的非唯一性**
   - **審查意見**：移除舊全域鉤子後，除 ELF 符號介入（`LD_PRELOAD`）外，程式亦可在原始碼層直接呼叫自訂配置 API 或透過連結期指定符號。
   - **裁決與修補**：成立。修訂第 44 行，補充「除可在原始碼層直接呼叫自訂配置 API 或透過編譯器連結期指定符號外，亦可透過標準的 ELF 符號介入進行全域攔截」。
2. **`IO_validate_vtable` 邊界防護與慢速相容路徑表述**
   - **審查意見**：`IO_validate_vtable` 檢查失敗後交由慢速相容路徑處理，未通過時才終止；唯讀區段能防禦一般遵守權限的寫入，不應表述為「任何寫入原語」。
   - **裁決與修補**：成立。修訂第 62 行，改為「大幅縮減了偽造堆積 vtable 的利用空間：由於 `__libc_IO_vtables` 位於唯讀資料區段（`R--`），一般的可寫記憶體寫入原語無法修改該區段內的函式指標；若指標落在區段外，慢速路徑未通過相容驗證便會直接終止行程」。
3. **CVSS v4.0 完整向量與 EPSS 分數定義對齊**
   - **審查意見**：漏洞評級須提供完整 CVSS v4.0 向量（含權限、使用者互動等）；基準常數定義的是 EPSS 分數（`≥ 0.1`），非「百分位」。
   - **裁決與修補**：成立。修訂第 31 行，補齊完整 CVSS v4.0 向量範例（`CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:H/SC:N/SI:N/SA:N`），並將「EPSS 百分位」嚴格修正為「EPSS 分數（`≥ 0.1`）」。
4. **VMA 數量上限（`vm.max_map_count`）的作用範圍與防護頁機制**
   - **審查意見**：`vm.max_map_count` 是單一行程的 VMA 上限，不能將多個服務的 VMA 累積相加；權限變更可能分割或合併 VMA。
   - **裁決與修補**：成立。修訂第 178 行，明確說明 Linux 核心對單一行程的 VMA 數量上限，分析原生服務建立大量執行緒與區段防護頁時導致單一行程 VMA 分割攀升並逼近上限之風險。
5. **PROT_NONE 防護頁與實體 RSS 增幅的獨立衡量**
   - **審查意見**：PROT_NONE 描述虛擬存取權限，無法直接推出實體 RSS 增幅；RSS 增幅主要受內部碎片、帶外中繼資料與快取保留影響。
   - **裁決與修補**：成立。修訂第 151–153 行，將虛擬位址區間／VMA 增加與實體常駐記憶體（RSS）增長分別精準說明。
6. **跨配置器釋放的 chunk 標頭偏移與未定義行為本質**
   - **審查意見**：ptmalloc2 的 chunk 起點在 `mem - 0x10`，`mchunk_size` 在 `mem - 0x08`；跨配置器釋放違反配對契約，屬於未定義行為，無法保證單一固定中止訊息。
   - **裁決與修補**：成立。修訂第 184 行，精確標示 `mem - 0x10` 起點與 `mem - 0x08` 的 `mchunk_size` 欄位，明確指出跨配置器釋放違反契約，通常因大小或對齊檢查失敗觸發 abort（如 `munmap_chunk(): invalid pointer` 或 `corrupted size`）。
7. **動手做命令列參數名稱與 1-byte 越界語意修正**
   - **審查意見**：`alloc_bench.c` 接受的參數為 `double-free` 與 `oob`（非 `uaf-double-free` / `oob-write`）；故障模式未記錄時間延遲，而是觀察攔截時機；`a[24]` 是越界寫入，預設通過是因為落在對齊填充區。
   - **裁決與修補**：成立。
     - 修訂第 202、225、227 行任務目標與操作檢查點，將命令列參數精確同步為 `double-free` 與 `oob`，並修正為「觀察不同配置器下的攔截時機與診斷表現」。
     - 修訂第 343 行，明確說明對 24-byte 緩衝區寫入 `a[24]` 為越界寫入，預設 glibc 常因落在對齊填充區而靜默通過，ASan 則由插樁命中 Redzone 立即攔截。

### 關鍵 `imprecise` 補強
- **前言背景與章節定位**（第 5 行）：補充「閘道尖峰吞吐需求 `2,000 req/s`」，並精確交代本地容器基準測試提供之驗證程序與對照目標。

---

## 3. `appendix-a-lab-index.md`

### 完稿狀態同步與架構標籤移除
- 配合全書 37 章全數完稿，將第 119 行說明更新為全書 37 章完整實驗配置。
- 將 Part IV 與 Part VI 中原標註之 `[尚未完稿預留章節]`（`Ch22, Ch23, Ch24, Ch26, Ch27, Ch33, Ch35`）全數更新為 **`已完稿`**，並移除難度欄位中的「（規劃）」後綴，保持全書附錄與章節完成狀態完全一致。

---

## 4. 驗證與閘門結果

- `python3 tools/md-reader/lint_book.py books/vuln-hunting/book-src --lang zh-TW --config books/vuln-hunting/book-src/_meta/lint.config.json`：
  - `ch22-stack-overflow-and-rop.md`：**0 errors, 0 warnings**
  - `ch24-advanced-heap-and-allocators.md`：**0 errors, 0 warnings**
  - `appendix-a-lab-index.md`：**0 errors, 0 warnings**
- `python3 tools/md-reader/check_diagrams.py books/vuln-hunting/book-src`：**passed (0 findings)**
- 所有全書基準常數、6 個 H2 標題、首個 H3、難度／時間／參考解答格式均 100% 嚴格保留。
