# 第 31 章：真實開源專案 Fuzzing 與 OSS-Fuzz 實戰

前兩章我們在單檔原始碼環境裡，拆解了 AFL++ 的 `65,536 bytes`（`64 KiB`）邊緣覆蓋率位圖、Persistent Mode 的 `5,000 exec/s` 吞吐基準，以及結合 Z3 與 angr 突破魔數與校驗和分支的混合式 Fuzzing。在那樣的受控實驗裡，從編譯到抓出第一顆 Crash 往往只要幾分鐘。

但把目標換成真實世界的開源專案後，難度立刻從演算法切換成系統工程。真實專案有著錯綜複雜的 CMake 或 Autotools 建置腳本、預設編譯成動態連結庫的相依元件、塞滿幾十個選項旗標的複合 API，以及一爆就是上千個重複檔案的 Crash 資料夾。

在 **NexusPay** 的生產架構裡，除了自家寫的 `libnexus-parse`（`8 bytes` 檔頭與 `65,536 bytes` 合法負載上限），系統也透過原生綁定或系統套件依賴了多個外部 C/C++ 與 Rust 解析庫。只要其中暴露在不可信輸入下的第三方 JSON、壓縮或協定解析套件沒跑過持續模糊測試，就會留下高風險的驗證缺口。

本章把第 29 到 30 章建立的灰箱與混合 Fuzzing 技術，正式推進到真實開源專案與 **OSS-Fuzz / ClusterFuzzLite** 持續模糊測試管線。我們會依序拆解目標挑選、建置系統改造、覆蓋率瓶頸突破、Crash 去重，以及自動化 PR 閘門建置。

---

## 從你已知的出發

團隊引入第三方開源套件時，標準流程通常是鎖定 `package.json` 或 `Cargo.toml` 版本、跑過單元測試與 SCA 已知漏洞掃描（Software Composition Analysis），只要沒查到已知 CVE 就放行上線。但在原生安全工程的眼裡，「沒有已知 CVE」完全不等於「通過了高覆蓋模糊測試」——很多時候只是還沒有人替它的邊界條件接上持續 Fuzzing。

把單機 Fuzzing 推向真實開源專案，不能只寫好一個 `LLVMFuzzerTestOneInput` 函式就收工，還得補齊四個工程環節。第一是從原始碼把受測庫（連同核心解析相依庫）帶插樁旗標重編為靜態封存檔（`.a`）並鏈結進執行檔，避開系統預編譯的未插樁 `.so` / `.dylib`。

第二是用結構化輸入映射把單一緩衝區拆成 API 旗標、模式與多階段呼叫。第三是靠 `llvm-cov` 揪出早退或魔數卡關，搭配字典與種子語料庫推開深層分支。第四則是用 **Stack Hash** 把海量重複 Crash 收斂成獨立簽章，並用 **ClusterFuzzLite** 在 PR 合併前攔截記憶體安全回歸。

---

## 機制與推導

### 攻擊者目標與實質影響

當安全研究員與攻擊者把大規模 Fuzzing 對準真實開源解析庫或協定實作時，鎖定的不只是單純讓程式閃退，而是三類具高度槓桿效應的實質突破。

首先是**透過基礎元件 0-day 橫向打穿下游多租戶平台**。一個廣泛嵌入 Node.js 原生外掛、容器基礎映像檔或 API 閘道的 C/C++ 解析庫（如 JSON、XML、影像編解碼或 HTTP 解析器），只要存在外部輸入可達的堆積越界寫入或 UAF，攻擊者就能對所有暴露相同路徑且未修補的下游服務重用漏洞原語，直接繞過應用層邏輯檢查。

其次是**專打既有 Fuzzing 的覆蓋率盲區**。許多熱門開源專案表面上「已經接入 OSS-Fuzz」，但維護者寫的 Harness 往往只呼叫最陽春的預設 API。這導致非預設旗標（如寬鬆模式、串流解析、註解支援或特定編碼分支）長期處於 `0%` 覆蓋率；攻擊者專門鎖定這類「名義已接入、實際沒跑到」的分支補寫客製 Harness，就能挖出潛伏多年的深層記憶體損毀。

第三是**把演算法複雜度與資源耗盡轉成遠端阻斷服務**。除了記憶體越界，開源解析器在深層巢狀結構或異常長度欄位下的二次方時間複雜度（Quadratic Parsing）與無上限配置，能讓後端 Worker 在極小頻寬下吃光記憶體或 CPU。對 NexusPay 這類高併發結算閘道，只要缺乏獨立配額與逾時隔離，少數惡意請求就足以長期卡死工作行程並拖垮服務可用性。

---

### 挑選高勝率開源 Fuzzing 目標的判準

GitHub 上有數百萬個儲存庫，盲目對隨機專案跑 AFL++ 只會燒光算力。實戰中評估一個 C/C++ 或 Rust 開源目標值不值得投入改造，可以交叉比對下面四個工程訊號（表中覆蓋率數值為經驗門檻，實際評估須區分公開函式覆蓋率與行覆蓋率的分母及量測組態）：

| 評估維度 | 高勝率目標特徵 | 低勝率／高阻力特徵 | 工程原因 |
|---|---|---|---|
| **輸入邊界與語言** | 處理不可信外部輸入的 C/C++ 解析器、解壓縮器、協定狀態機，或含大量 `unsafe` / C FFI 的 Rust 封裝層 | 純計算數學庫或無外部邊界的純 Safe Rust 業務邏輯 | C/C++ 原生指標與陣列操作缺少自動邊界檢查，錯誤偏移或整數溢位若影響後續配置大小、索引或拷貝長度，就可能釀成記憶體損毀 |
| **OSS-Fuzz 覆蓋現況** | 尚未接入 OSS-Fuzz，或已接入但 **OSS-Fuzz Introspector** 報告顯示公開函式覆蓋率偏低（如 `< 30%`） | 已有 10+ 個精細 Harness 且長期行覆蓋率極高（如 `> 80%`） | 淺層與標準路徑已被算力反覆洗過；沒人測到的旗標與邊緣選項才是盲區 |
| **建置與相依純度** | 支援 CMake / Meson / Cargo，不靠實體硬體驅動或複雜 GUI / DB Daemon 即可靜態編譯 | 強綁定閉源 SDK、複雜多行程 IPC 或必須啟動完整系統服務才能跑解析函式 | Harness 理想上應能在記憶體內維持 `5,000 exec/s`（全書 Persistent Mode 單核基準）；若每次迭代都要花上百毫秒初始化外部環境，吞吐量會慘跌（單次 100 ms 時僅剩 `10 exec/s`） |
| **程式碼演化訊號** | 近期剛合併重構 PR（如新增序列化格式、支援 Zero-copy / In-situ 解析模式） | 長期未更動且單元測試與既有 Fuzzing 覆蓋極高的極簡單檔工具 | 新加入的效能最佳化（特別是手動記憶體池與就地修改指標）極易打破舊有邊界不變量 |

實務上審查 NexusPay 準備導入的原生開源套件時，建議固定先做兩件事：先查專案是否在 Google OSS-Fuzz 的 `projects/` 目錄下；若已在列，直接翻開它的 `build.sh` 與 Fuzz Target 原始碼，核對究竟覆蓋了哪些 API 旗標與編譯選項。很多團隊看到「OSS-Fuzz Verified」徽章就安心引入，卻沒察覺自己線上啟用的某個非預設巨集或解析旗標，根本沒進過官方 Harness 的呼叫路徑。

---

### 處理複雜建置系統與全靜態鏈結

把真實開源專案接進 libFuzzer 或 AFL++，第一道最常卡關的門檻就是**編譯系統改造**。許多 C/C++ 專案預設產出動態函式庫（`.so`），並連結系統裡的 `/usr/lib/libz.so` 或未插樁的第三方相依，這會馬上引發兩個致命問題。

第一是**覆蓋率斷鏈**：動態載入的未插樁函式庫沒有編進 `-fsanitize=fuzzer-no-link` 探針，模糊器對它內部的分支一無所知，覆蓋率位圖永遠記不到這些邊緣轉移。第二是**Sanitizer 漏檢與執行期衝突**：主執行檔就算連了 ASan，一旦呼叫到沒插樁的動態函式庫，發生在裡面的直接越界讀寫就會因為缺少檢查探針而漏檢（除非剛好經過 ASan 攔截的標準函式）；若跨模組混用不相容的記憶體分配與釋放路徑，甚至會觸發執行期診斷異常。

OSS-Fuzz 用一套標準化的環境變數契約解決這個問題，從外層 Docker 建置環境把插樁旗標強制灌進建置系統（以下以常見的 ASan/UBSan + libFuzzer 建置組態為例，實際旗標依所選引擎與 Sanitizer 矩陣調整）：

- **`$CC` / `$CXX`**：指向支援插樁的 Clang / Clang++ 編譯器。
- **`$CFLAGS` / `$CXXFLAGS`**：放入對應的 Sanitizer 旗標（如 `-fsanitize=address,undefined`）、**`-fsanitize=fuzzer-no-link`**（只插入覆蓋率與比較探針，不連結模糊引擎的 `main` 進入點，免得編譯函式庫和內建 `main()` 的測試工具時撞名），以及常搭配的條件巨集 **`-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION`**。
- **`$LIB_FUZZING_ENGINE`**：只在最後連結 Fuzzer 可執行檔時傳入，用來提供 `main()` 迴圈與模糊引擎鏈結參數（例如 libFuzzer 下展開為 `-fsanitize=fuzzer`，在 AFL++ 下則連結 `libAFLDriver.a` 等驅動封存檔）。

改寫建置腳本（例如 `build.sh`）時，只要抓穩三項原則就能少走很多彎路。

第一是**確保受測庫靜態插樁鏈結，並關掉無關測試**：在 CMake 傳入 `-DBUILD_SHARED_LIBS=OFF`，或在 Autotools `./configure` 加上 `--enable-static --disable-shared`，把受測庫與核心相依元件編譯成靜態封存檔鏈進 Fuzzer；同時可關閉單元測試與文件編譯（如 `-DBUILD_TESTING=OFF`）縮短建置時間。

第二是**覆蓋寫死的編譯器設定**：老舊 `Makefile` 常硬編碼 `CC = gcc` 或 `CFLAGS = -O2 -Wall`，必須在呼叫 `make` 時用參數蓋掉（`make CC="$CC" CFLAGS="$CFLAGS"`），或先用 `sed` 清掉。

第三則是**謹慎隔離非決定性障礙**：真實檔案格式常帶有 CRC32 或雜湊驗證，會把純變異模糊器死死擋在門外（第 30 章已算過，盲猜 32-bit 精確值平均得花 `2^32 ≈ 4.29 × 10^9` 次）。部分開源庫會用 `#ifdef FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION` 跳過校驗和或固定隨機種子，讓執行流直衝深層解析器。

但這把雙面刃必須受控——回報前一定要在移除該巨集的標準 Release + ASan 環境下補齊有效校驗和重新驗證，並在報告寫清楚確認過的組態與前置條件。

至於 Rust 開源專案，Cargo 本身就偏好靜態連結 crate，整合起來相對單純。標準做法是執行 `cargo fuzz build -O`（透過 `cargo-fuzz` 與 `libfuzzer-sys` 注入插樁與 ASan 旗標），再把 `fuzz/target/<triple>/release/<target_name>` 複製進 `$OUT/`。

但如果專案透過 `build.rs` 另外編譯底層 C/C++ 程式碼，就得一併檢查 `CC`、`CFLAGS` 與連結設定，確保跨語言邊界同步受到插樁與 Sanitizer 保護（呼應第 25 章）。

---

### 覆蓋率瓶頸診斷、`FuzzedDataProvider` 與字典檔設計

Fuzzer 跑起來後，最常見的陷阱就是「放著跑一晚沒看到 Crash 就以為程式安全」。不看覆蓋率報告，你根本不知道 Fuzzer 是徹底掃過了整個解析器，還是跑了幾億次都在第一層 `if` 就早退。

在 LLVM 工具鏈裡，我們不會直接拿線上模糊版去算精確行覆蓋率，而是專門編譯一份 **Clang Source-Based Code Coverage** 檢查檔。編譯時改加 `-fprofile-instr-generate -fcoverage-mapping`（通常不帶 ASan 以免干擾），接著設定 `LLVM_PROFILE_FILE="target.profraw"` 並把現有語料庫（`corpus/`）一次性重播過去。

最後用 `llvm-profdata merge -sparse target.profraw -o target.profdata` 建立索引，就能透過 `llvm-cov report` 看總表，或用 `llvm-cov show -format=html` 產出逐行著色報告。

當 `llvm-cov` 顯示覆蓋率卡在 `15%–25%` 不動時，病根幾乎都落在這三種結構性瓶頸上：

第一是**輸入維度單一（Missing Parameter Fuzzing）**。真實函式常接收旗標（`flags`）、模式列舉或設定結構體，如果只把原始 `data/size` 塞進預設呼叫，等於把所有選項開關鎖死在 `0`。

標準解法是引入 `<fuzzer/FuzzedDataProvider.h>`，從同一段隨機位元組裡**確定性地切分**出控制參數與主負載。例如先用 `provider.ConsumeIntegral<uint32_t>()` 決定選項旗標（由尾端往前切），再用 `provider.ConsumeRemainingBytesAsString()` 拿剩餘內容（由前端往後取），讓模糊器跟著覆蓋率回饋同時探索旗標組合與內容。

第二是**語法關鍵字與魔數牆**。沒有字典引導時，一個 8-byte 協定關鍵字（例如 `"SETTINGS"` 或 `"infinity"`）靠隨機位元翻轉湊出來的機率微乎其微，就算單核跑 `5,000 exec/s` 也會卡在詞法分析器的前幾個比對。寫一份精簡的**字典檔**（`.dict`），把關鍵字、跳脫字元與邊界數字（如 `"NaN"`、`"-0"`、`"\u0000"`）透過 `-dict=syntax.dict` 餵給突變器，就能在單次變異裡插入完整詞元。

第三是**單向路徑鎖死（Missing Write / Serialization Path）**。許多函式庫有一半以上的程式碼都在寫入器（Serializer / Writer）、AST 走訪或結構體複製函式裡。若 Harness 解析完就直接 `free()` 收工，從頭到尾不呼叫寫出 API，序列化這半邊的程式碼覆蓋率就會永遠停在 `0%`。

#### 實戰數值推演：從 `18.00%` 停滯到 `63.00%` 覆蓋率躍升

下面展示一組真實風格的 `llvm-cov report` 診斷過程。目標是一個擁有 1,800 行可執行敘述的開源結構化資料解析庫（四個模組：`lexer.c`、`parser.c`、`options.c`、`serializer.c`），在單核 `5,000 exec/s` 下各自跑滿 2 小時（`36,000,000` 次執行）後的定量對比：

```text
=== Phase 0：原始 Harness（固定 flags = 0，無字典，無序列化寫出）===
執行 36,000,000 次後覆蓋率完全停滯（持續 90 分鐘無新增邊緣）

Filename        Regions  Missed  Cover    Lines   Missed  Cover
----------------------------------------------------------------
lexer.c             210     122  41.90%     450      261  42.00%
parser.c            380     320  15.79%     750      630  16.00%
options.c           140     133   5.00%     300      285   5.00%
serializer.c        150     150   0.00%     300      300   0.00%
----------------------------------------------------------------
TOTAL               880     725  17.61%    1800     1476  18.00%

診斷瓶頸（對照分支覆蓋率報告之待驗證假設）：
1) options.c (5.00%)：Harness 寫死 flags = 0，非預設解析旗標全數無法進入。
2) serializer.c (0.00%)：解析後直接釋放文件物件，寫入器與跳脫字元編碼完全未觸發。
3) parser.c (16.00%)：缺乏多字節語法關鍵字與數字邊界 token，卡在基礎型別判斷。

=== Phase 1：導入 FuzzedDataProvider 拆分 2 bytes 控制參數 + 解析後序列化寫出 ===
改動：ConsumeIntegral<uint16_t>() 對應解析旗標與序列化選項；解析成功後呼叫 write()

Filename        Regions  Missed  Cover    Lines   Missed  Cover
----------------------------------------------------------------
lexer.c             210      99  52.86%     450      216  52.00%
parser.c            380     272  28.42%     750      540  28.00%
options.c           140      66  52.86%     300      144  52.00%
serializer.c        150      98  34.67%     300      198  34.00%
----------------------------------------------------------------
TOTAL               880     535  39.20%    1800     1098  39.00%

量化增益：總行覆蓋率由 18.00% (+378 行) 提升至 39.00%（702 / 1800 行）。

=== Phase 2：加入 24 條語法字典（syntax.dict）與 12 個最小合法種子 ===
字典內容（24 entries）：關鍵字/註解符號/UTF-8 BOM/科學記號/極值整數/跳脫序列

Filename        Regions  Missed  Cover    Lines   Missed  Cover
----------------------------------------------------------------
lexer.c             210      36  82.86%     450       81  82.00%
parser.c            380     148  61.05%     750      300  60.00%
options.c           140      52  62.86%     300      114  62.00%
serializer.c        150      84  44.00%     300      171  43.00%
----------------------------------------------------------------
TOTAL               880     320  63.64%    1800      666  63.00%

最終結果：總行覆蓋率突破目標達 63.00%（1134 / 1800 行），較 Phase 0 提升 +45.00 個百分點
（有效覆蓋行數從 324 行擴增為 3.5 倍）。
```

這組數字說明了一個很現實的調校原則：當 `llvm-cov` 停滯在低水位（如 `18.00%`）時，硬拉長執行時間往往觸及不到未呼叫的 API 與多位元組關鍵字分支；先對照 HTML 覆蓋率報告補上 `FuzzedDataProvider` 參數切分、寫出路徑與精準字典檔，才是打開深層解析邏輯的捷徑。

---

### Crash 去重（Stack Hash）與真假陽性判別

一旦覆蓋率破關，模糊器經常在幾分鐘內吐出數百甚至上千個 Crash 檔案。但絕大多數檔案其實踩在同一處空指標解參考或同一條越界讀取上，只是前面的垃圾位元組長得不一樣。如果逐一人工打開或重複回報給上游維護者，工程時間很快就會燒乾。

**ClusterFuzz** 與 **OSS-Fuzz** 用一套基於呼叫堆疊簽章（Crash State / **Stack Hash**）的自動化去重模型，把原始 Sanitizer 呼叫堆疊濃縮成正規化故障簽章。以下用標準 Top-`k`（`k = 3`）專案框架模型看懂它的四步管線：

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    ClusterFuzz Stack Hash 去重管線                      │
├─────────────────────────────────────────────────────────────────────────┤
│  1. 原始 Sanitizer Stack Trace（ASan / UBSan / MSan）                   │
│     #0 __asan_memcpy  #1 parse_str (src/parser.c:412)  #2 parse_obj ... │
│                                │                                        │
│                                ▼                                        │
│  2. 雜訊框架過濾（Frame Filtering）                                     │
│     移除：__asan::* / __asan_memcpy / libc / libstdc++ / fuzzer::*      │
│                                │                                        │
│                                ▼                                        │
│  3. 提取 Top-k 專案框架（預設 k = 3）並正規化（Normalization）          │
│     剝除行號、記憶體位址與建置絕對路徑，僅保留函式簽章與錯誤類別        │
│     Crash State: "Heap-buffer-overflow | parse_str | parse_obj | entry" │
│                                │                                        │
│                                ▼                                        │
│  4. 計算不可逆雜湊 → Stack Hash（分桶歸檔：同一 Hash 合併為單一 Issue） │
└─────────────────────────────────────────────────────────────────────────┘
```

這四步各有明確的過濾目標。先剃除頂端的 `__asan::ReportGenericError`、`__asan_memcpy`、`strlen` 與底端的 `LLVMFuzzerTestOneInput`、`__libc_start_main` 等沒有鑑別度的執行期框架。接著保留距離錯誤點最近的 3 層專案函式（如 `parse_str` → `parse_object` → `parse_root`），這個深度剛好能區分同一個輔助函式從不同呼叫鏈傳入錯誤長度的兩種缺陷，又不至於因為深層遞迴路徑不同而把同一顆蟲拆成幾十張單。

提取完框架後，系統會剝除原始碼行號（`:412`）、位元組偏移與絕對路徑，免得開發者只是在檔案上方多加兩行註解，同一個未修漏洞就被當成新 Crash。最後把 Sanitizer 錯誤類別（如 `heap-buffer-overflow`、`heap-use-after-free`）跟這 3 層函式名稱串成 **Crash State** 字串計算雜湊，相同 Hash 就會併進同一張追蹤單（修補時仍須核對是否真為同一根因）。

去重完還不能急著發 Issue，下一步要做**真假陽性判別**（True vs False Positive Triage）。就算 ASan 噴出紅字，也常是 Harness 自己寫錯惹的禍：

- **違反 API 契約**：像 `yyjson` 的 `YYJSON_READ_INSITU` 就地解析模式，明確要求傳入可寫緩衝區並在尾端預留 `YYJSON_PADDING_SIZE` 位元組（如 `4 bytes`）的零填充空間。若 Harness 直接把緊繃的 `data` 指標塞進去，ASan 抓到的 `heap-buffer-overflow` 其實是 Harness 違約，不是函式庫的錯。
- **跨迭代全域狀態汙染**：目標庫若依賴全域快取或靜態設定，前 `1,000` 次執行改壞了全域指標，第 `4,000` 次才引爆。這時單獨拿第 `4,000` 次的檔案重播 `./fuzzer crash-xyz` 會直接過關，通常是 Harness 沒重置狀態所致。
- **合理資源邊界觸發的 OOM / Timeout**：libFuzzer 預設有 `-rss_limit_mb=2048` 與 `-timeout=25` 等保護限制。若 Harness 沒設輸入大小上限，Fuzzer 塞入上百 MB 的巨型輸入導致正常配置的 AST 撞到限制，往往只代表呼叫端沒限流；真正高價值的 DoS 缺陷，是在服務允許的大小內，靠極小輸入觸發二次方運算放大或非預期巨量記憶體配置。

確認為真陽性後，完整的上游回報與協調揭露流程（含 CVE 申請、CVSS v4.0 量化與揭露時程）會在第 33 章詳細展開。

---

### OSS-Fuzz 與 ClusterFuzzLite 整合規範

要把本地開發好的 Harness 變成長期持續的防護網，業界有兩條互通的標準架構：**OSS-Fuzz**（Google 託管、針對重要開源專案提供免費大規模算力的中央平台）與 **ClusterFuzzLite**（把同一套引擎輕量化包進專案自身的 GitHub Actions / GitLab CI，充當 PR 合併閘門與夜間掃描）。

兩者共用同一套容器化建置契約，核心就靠三個檔案。第一是 **`project.yaml`**，宣告專案語言、聯絡信箱、要啟用的 Sanitizer（如 `address`、`undefined`）與模糊引擎（`libfuzzer`）：

```yaml
homepage: "https://example.org/libtarget"
language: c++
primary_contact: "security@example.org"
main_repo: "https://github.com/example/libtarget.git"
sanitizers:
  - address
  - undefined
fuzzing_engines:
  - libfuzzer
```

第二是 **`Dockerfile`**，繼承官方基底映像檔（如 `gcr.io/oss-fuzz-base/base-builder` 或 `base-builder-rust`），裝好建置套件、複製原始碼並設定 `WORKDIR`（ClusterFuzzLite 固定放在 `.clusterfuzzlite/Dockerfile`）。

第三是 **`build.sh`**，在建置階段由容器呼叫，負責用 `$CC`、`$CXX`、`$CFLAGS`、`$CXXFLAGS` 執行靜態編譯。最後把連結 `$LIB_FUZZING_ENGINE` 後的執行檔、`.dict` 字典檔與預打包語料庫 `<fuzzer_name>_seed_corpus.zip` 全部複製進 `$OUT/`。

本地開發不用等發 PR 才能測，直接用 OSS-Fuzz 附帶的 `infra/helper.py` 就能在本地 Docker 跑通整套流程（參數依 OSS-Fuzz 版本為準）：
- `python3 infra/helper.py build_image <project>`：建置專案測試映像檔。
- `python3 infra/helper.py build_fuzzers --sanitizer address <project>`：執行 `build.sh` 並在 `$OUT/` 產出 Fuzzer 執行檔。
- `python3 infra/helper.py check_build <project>`：驗證 `$OUT/` 產物能否正常啟動與基本插樁連結狀態。
- `python3 infra/helper.py coverage <project> --corpus-dir <dir>`：改以 `--sanitizer coverage` 建置並用 `llvm-cov` 產出 HTML 覆蓋率報告。

把這三件式搬進專案的 `.clusterfuzzlite/` 目錄並接上 GitHub Actions 後，就能在每次 Pull Request 觸發 `mode: 'pr'` 的快速閘門（例如對受影響的 Fuzzer 跑 `600 秒` 變異與既有語料庫重播），同時在夜間排程跑 `mode: 'batch'` 與 `prune` 定期修剪語料庫（呼應第 29 章語料最小化原理），讓記憶體安全檢查真正卡死在 CI/CD 上。

---

## 故障模式與防禦

在真實開源專案導入 Fuzzing 與 OSS-Fuzz 時，團隊最常在以下四種故障模式上白白浪費數週，甚至得出錯誤的安全結論。

### 故障模式 1：Fuzzer 之間共用的全域狀態汙染

本地持續跑 20 分鐘後突然冒出一個嚴重的 `heap-use-after-free`，但你興奮地把 `crash-<sha1>` 樣本抽出來單獨執行 `./fuzzer crash-<sha1>` 時，程式卻安靜退出且回傳碼為 `0`，怎麼樣都重現不了。

這通常因為受測函式庫內部用了全域靜態變數（如全域設定單例、錯誤緩衝區或未清理的節點快取池），或者 Harness 自己在多次 `LLVMFuzzerTestOneInput` 呼叫間累積了跨請求狀態。由於 libFuzzer Persistent Mode 會在同一個行程內連續呼叫進入點數萬次，前幾千筆輸入留下的破損狀態，直到第 N 次才引爆。

要徹底根治，必須把受測函式改為顯式傳入獨立上下文物件（Context Handle）的無狀態呼叫，並在每次 `LLVMFuzzerTestOneInput` 結束前成對銷毀；若暫時改不動上游全域變數，除錯時應透過獨立子行程重播單筆輸入以區分單筆缺陷與跨迭代汙染。

### 故障模式 2：Harness 違反 API 前置條件製造假陽性

花了半天建置並跑出滿滿的 ASan `heap-buffer-overflow` 報告，馬上興沖沖回報給上游維護者，結果被對方秒關回覆「WontFix — 呼叫端違反緩衝區合約」。

問題出在高效能 C 解析庫為了省去拷貝，常要求呼叫端保證特定前提，例如「字串必須以 `\0` 結尾」或「就地解析（in-situ）必須在緩衝區尾端多預留 4 bytes 哨兵空間」。libFuzzer 傳給 Harness 的 `(const uint8_t *data, size_t size)` 只保證 `[data, data + size)` 可讀且不可就地改寫。

在搭配 ASan 執行時，引擎會配置剛好 `size` bytes 的獨立緩衝區，尾端緊貼著 ASan 紅區（Redzone）；一旦直接把 `data` 硬轉型交給需要 NUL 結尾或尾端填充的函式，越過 `data + size` 踏入紅區就會觸發假陽性告警。寫 Harness 前務必核對標頭檔註解，需要 `\0` 結尾就配置 `size + 1` bytes 補零，需要就地填充就先複製到 `size + PADDING_SIZE` 並清零尾端再傳入。

### 故障模式 3：未設輸入與記憶體天花板引發 OOM 噪音淹沒引擎

Fuzzer 一啟動，平均吞吐量就從數千跌到 `20 exec/s`（單次耗時 `50 ms`），而且跑沒多久就因為撞破 `-rss_limit_mb=2048` 累積了一堆 `oom-<sha1>` 與 `timeout-<sha1>` 樣本，把正常封包長度的探索資源全擠光。

部分壓縮庫、XML 展開器或 JSON 解析器支援巨型重複欄位或解壓縮放大（如 Zip Bomb / 深層陣列巢狀）。只要 Harness 沒在入口限制原始輸入長度，Fuzzer 一變異出上百 MB 的巨大樣本，單次配置釋放就拖垮整條管線。

標準防線是在 `LLVMFuzzerTestOneInput` 開頭加上合理的最大輸入檢查（如 `if (size > 1024 * 1024) return 0;`），並替支援自訂分配器的函式庫掛上帶總量上限的測試分配器，把「正常大輸入吃光記憶體」跟「極小輸入卻要求配置數 GB 記憶體」的高價值漏洞拆開追蹤。

### 故障模式 4：`FUZZING_BUILD_MODE` 巨集掩蓋真實條件或引入測試專屬崩潰

開啟 `-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION` 建置後抓到一個嚴重越界，寫成 PoC 打向線上的正式版編譯組態卻完全沒反應。

原因在於 Fuzzing 專屬條件編譯有時不只跳過 CRC32 校驗，還可能順手繞過了長度前置驗證或改走簡化的測試分支，導致該路徑在生產環境根本不可達；反過來，過度依賴這類巨集跳過簽章檢查，也會掩蓋簽章驗證函式自己藏著的緩衝區溢位。因此必須守住兩階段驗證紀律：任何靠 `FUZZING_BUILD_MODE` 挖出的 Crash，評估影響前一定要在**拿掉該巨集**、並補齊真實校驗和或簽章的標準 Release + ASan 建置上重現（若只在測試巨集下成立，回報時須如實標明）；至於加密或校驗層本身的安全，則應寫獨立且不帶跳過巨集的 Harness 專門測試。

---

## 動手做

- **難度**：進階
- **預估時間**：60 分鐘

本實驗直接拿真實開源的高效能 C 語言 JSON 解析庫 **`yyjson`**（廣泛用於 C/Node.js 生態的高速解析元件，兼具標準解析、嚴格／寬鬆旗標、`YYJSON_READ_INSITU` 就地模式與序列化寫出 API）作為實戰目標。你會從原始碼靜態建置起步，親手走過「`llvm-cov` 覆蓋率停滯診斷 → 用 `FuzzedDataProvider` 與 24 條字典檔突破瓶頸 → 撰寫 ClusterFuzzLite 設定檔」的完整開源專案 Fuzzing 工作流。

實驗全程在本地 Linux 容器或具備 Clang/LLVM 工具鏈的本地環境執行，零雲端費用；所有操作僅針對本地 clone 下來的原始碼副本。

### 操作步驟

1. **準備本地原始碼與工具鏈**：確認環境裝有 `clang`、`clang++`、`cmake`、`llvm-profdata`、`llvm-cov`（LLVM 16+ 皆可，Ubuntu/Debian 可用 `apt install clang llvm cmake git` 安裝）。從 GitHub clone `yyjson`（建議鎖定穩定 tag `0.10.0`）到本地工作目錄。
2. **靜態編譯基準與最小 Harness（Phase 0）**：用 CMake 關閉共用函式庫與測試（`-DBUILD_SHARED_LIBS=OFF -DYYJSON_BUILD_TESTS=OFF`），寫一個陽春版 Harness `fuzz_phase0.cc` 只呼叫 `yyjson_read((const char *)data, size, 0)` 與 `yyjson_doc_free(doc)`。分別編譯 `-fsanitize=address,undefined,fuzzer` 模糊測試版（跑 `60` 秒產出 `corpus_p0/`）與 `-fprofile-instr-generate -fcoverage-mapping -fsanitize=fuzzer` 覆蓋率版（重播 `corpus_p0/` 並產出 `llvm-cov` 報告），記錄總行覆蓋率。
3. **診斷瓶頸並實作高覆蓋 Harness + 字典（Phase 1 & 2）**：檢視 `llvm-cov` 報告找出 `0%` 未覆蓋模組後，改寫為進階 Harness `fuzz_advanced.cc`：引入 `<fuzzer/FuzzedDataProvider.h>` 切分 `yyjson_read_flag`（含註解、尾逗號、`Inf`/`NaN`、無效 UTF-8 等旗標）與 `yyjson_write_flag`，在解析成功時呼叫 `yyjson_write_opts` 及 `yyjson_doc_mut_copy` + `yyjson_mut_write_opts`，並實作符合 `YYJSON_PADDING_SIZE` 合約的 `YYJSON_READ_INSITU` 就地模式測試路徑。接著補上 24 條 `json.dict` 與小型合法種子再跑 `60` 秒，產出新報告量化覆蓋率提升幅度。
4. **建置 ClusterFuzzLite 設定檔**：在模擬專案根目錄建立 `.clusterfuzzlite/project.yaml`、`.clusterfuzzlite/Dockerfile`、`.clusterfuzzlite/build.sh` 與 `.github/workflows/cflite_pr.yml`，讓 PR 修改原始碼或 Harness 時能以 `mode: 'pr'` 跑 `600 秒` 回歸測試。

---

### 參考解答

#### 步驟 1–2：建立工作目錄、靜態建置與 Phase 0 基準量測

```bash
mkdir -p ~/oss-fuzz-lab && cd ~/oss-fuzz-lab
git clone --branch 0.10.0 --depth 1 https://github.com/ibireme/yyjson.git
mkdir -p harness corpus_p0 corpus_p2 coverage_p0 coverage_p2
```

建立陽春版 `harness/fuzz_phase0.cc`：

```cpp
#include <cstdint>
#include <cstddef>
#include "yyjson.h"

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size == 0 || size > 1024 * 1024) {
        return 0;
    }
    yyjson_doc *doc = yyjson_read(reinterpret_cast<const char *>(data), size, 0);
    if (doc) {
        yyjson_doc_free(doc);
    }
    return 0;
}
```

編譯模糊測試版與覆蓋率統計版（全靜態連結 `libyyjson.a` 或直接編入 `yyjson.c`）：

```bash
# 1. CMake 靜態建置示範（產出帶插樁與 Sanitizer 的 libyyjson.a）
cmake -S yyjson -B build-static \
  -DCMAKE_C_COMPILER=clang \
  -DCMAKE_C_FLAGS="-O1 -g -fsanitize=address,undefined,fuzzer-no-link" \
  -DBUILD_SHARED_LIBS=OFF \
  -DYYJSON_BUILD_TESTS=OFF
cmake --build build-static -j$(nproc)

# 2. 連結 Phase 0 模糊執行檔並跑 60 秒
clang++ -std=c++17 -O1 -g -fsanitize=address,undefined,fuzzer \
  -Iyyjson/src harness/fuzz_phase0.cc build-static/libyyjson.a -o fuzz_p0
./fuzz_p0 corpus_p0 -max_total_time=60

# 3. 編譯覆蓋率統計專用版並重播 corpus_p0
clang -O1 -fprofile-instr-generate -fcoverage-mapping -c yyjson/src/yyjson.c -o yyjson_cov.o
clang++ -std=c++17 -O1 -fprofile-instr-generate -fcoverage-mapping -fsanitize=fuzzer \
  -Iyyjson/src harness/fuzz_phase0.cc yyjson_cov.o -o fuzz_p0_cov

LLVM_PROFILE_FILE="p0.profraw" ./fuzz_p0_cov corpus_p0 -runs=0
llvm-profdata merge -sparse p0.profraw -o p0.profdata
llvm-cov report ./fuzz_p0_cov -instr-profile=p0.profdata yyjson/src/yyjson.c
llvm-cov show ./fuzz_p0_cov -instr-profile=p0.profdata \
  -format=html -output-dir=coverage_p0 yyjson/src/yyjson.c
```

打開 `coverage_p0/index.html`，可以清楚看到 `yyjson_write_opts`、`yyjson_mut_*` 以及非預設旗標分派邏輯（像 `YYJSON_READ_ALLOW_COMMENTS`、`YYJSON_READ_INSITU`）全都呈現 `0%` 紅色未覆蓋。

#### 步驟 3：撰寫進階 Harness（`FuzzedDataProvider` + `24` 條字典）

建立 `harness/fuzz_advanced.cc`：

```cpp
#include <cstdint>
#include <cstddef>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <fuzzer/FuzzedDataProvider.h>
#include "yyjson.h"

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    // 5 bytes 控制區（uint16_t + uint8_t + 2 個 bool）加上至少 1 byte JSON 負載
    if (size < 6 || size > 1024 * 1024) {
        return 0;
    }

    FuzzedDataProvider provider(data, size);

    // 切分解析旗標、寫出旗標與模式開關
    uint32_t raw_rflg = provider.ConsumeIntegral<uint16_t>();
    uint32_t raw_wflg = provider.ConsumeIntegral<uint8_t>();
    bool use_insitu   = provider.ConsumeBool();
    bool test_mut     = provider.ConsumeBool();

    // 映射合法 yyjson_read_flag 組合（避免未定義位元干擾）
    yyjson_read_flag rflg = 0;
    if (raw_rflg & (1 << 0)) rflg |= YYJSON_READ_ALLOW_COMMENTS;
    if (raw_rflg & (1 << 1)) rflg |= YYJSON_READ_ALLOW_TRAILING_COMMAS;
    if (raw_rflg & (1 << 2)) rflg |= YYJSON_READ_ALLOW_INF_AND_NAN;
    if (raw_rflg & (1 << 3)) rflg |= YYJSON_READ_NUMBER_AS_RAW;
    if (raw_rflg & (1 << 4)) rflg |= YYJSON_READ_ALLOW_INVALID_UNICODE;
    if (raw_rflg & (1 << 5)) rflg |= YYJSON_READ_BIGNUM_AS_RAW;

    std::vector<uint8_t> payload = provider.ConsumeRemainingBytes<uint8_t>();
    if (payload.empty()) {
        return 0;
    }

    yyjson_doc *doc = nullptr;
    yyjson_read_err err;

    if (use_insitu) {
        // 遵守 API 合約：就地解析必須配置額外 YYJSON_PADDING_SIZE (4 bytes) 且清零
        rflg |= YYJSON_READ_INSITU;
        std::vector<char> padded(payload.size() + YYJSON_PADDING_SIZE, 0);
        std::memcpy(padded.data(), payload.data(), payload.size());
        doc = yyjson_read_opts(padded.data(), payload.size(), rflg, nullptr, &err);
        if (doc) {
            // 注意：doc 內字串指標引用 padded，須在 padded 存活期內完成讀取與寫出
            size_t out_len = 0;
            yyjson_write_flag wflg = (raw_wflg & 1) ? YYJSON_WRITE_PRETTY : 0;
            if (raw_wflg & 2) wflg |= YYJSON_WRITE_ESCAPE_UNICODE;
            if (raw_wflg & 4) wflg |= YYJSON_WRITE_ALLOW_INF_AND_NAN;
            char *out = yyjson_write_opts(doc, wflg, nullptr, &out_len, nullptr);
            if (out) std::free(out);
            yyjson_doc_free(doc);
        }
        return 0;
    }

    // 非就地模式：傳遞複本確保原始 payload 可讀寫安全
    std::vector<char> buf(payload.begin(), payload.end());
    doc = yyjson_read_opts(buf.data(), buf.size(), rflg, nullptr, &err);
    if (doc) {
        size_t out_len = 0;
        yyjson_write_flag wflg = (raw_wflg & 1) ? YYJSON_WRITE_PRETTY : 0;
        if (raw_wflg & 2) wflg |= YYJSON_WRITE_ESCAPE_SLASHES;
        if (raw_wflg & 4) wflg |= YYJSON_WRITE_ALLOW_INVALID_UNICODE;

        char *out = yyjson_write_opts(doc, wflg, nullptr, &out_len, nullptr);
        if (out) std::free(out);

        if (test_mut) {
            yyjson_mut_doc *mdoc = yyjson_doc_mut_copy(doc, nullptr);
            if (mdoc) {
                char *mout = yyjson_mut_write_opts(mdoc, wflg, nullptr, &out_len, nullptr);
                if (mout) std::free(mout);
                yyjson_mut_doc_free(mdoc);
            }
        }
        yyjson_doc_free(doc);
    }
    return 0;
}
```

建立 24 條字典檔 `harness/json.dict`：

```text
# 24-entry JSON / JSON5 / edge-number dictionary
"{"
"}"
"["
"]"
":"
","
"true"
"false"
"null"
"NaN"
"-NaN"
"Infinity"
"-Infinity"
"//"
"/*"
"*/"
"\\u0000"
"\\uD800"
"\\uDC00"
"\\/"
"1e309"
"-0"
"18446744073709551615"
"-9223372036854775808"
```

放入小型合法種子與字典檔跑 60 秒，再對比兩份 `llvm-cov report` 輸出：

```bash
# 放入小型合法種子至 corpus_p2（尾端附 5 bytes 供 FuzzedDataProvider 切分 uint16_t + uint8_t + 2 個 bool 控制參數）
printf '{"k":[1,true,null,"v"]}\x01\x00\x01\x01\x00' > corpus_p2/seed0.bin

clang++ -std=c++17 -O1 -g -fsanitize=address,undefined,fuzzer \
  -Iyyjson/src harness/fuzz_advanced.cc build-static/libyyjson.a -o fuzz_adv
./fuzz_adv corpus_p2 -dict=harness/json.dict -max_total_time=60

clang++ -std=c++17 -O1 -fprofile-instr-generate -fcoverage-mapping -fsanitize=fuzzer \
  -Iyyjson/src harness/fuzz_advanced.cc yyjson_cov.o -o fuzz_adv_cov

LLVM_PROFILE_FILE="p2.profraw" ./fuzz_adv_cov corpus_p2 -runs=0
llvm-profdata merge -sparse p2.profraw -o p2.profdata
llvm-cov report ./fuzz_adv_cov -instr-profile=p2.profdata yyjson/src/yyjson.c
llvm-cov show ./fuzz_adv_cov -instr-profile=p2.profdata \
  -format=html -output-dir=coverage_p2 yyjson/src/yyjson.c
```

對比兩份報告，就能看到 `fuzz_adv` 因為呼叫了 `yyjson_write_opts`、`yyjson_doc_mut_copy`、`yyjson_mut_write_opts` 並打開註解、`Inf`/`NaN` 與就地解析旗標，成功覆蓋了 `fuzz_p0` 完全沒碰到的寫出與非預設旗標區塊。

#### 步驟 4：ClusterFuzzLite 設定檔範例

1. `.clusterfuzzlite/project.yaml`：
```yaml
language: c++
sanitizers:
  - address
  - undefined
fuzzing_engines:
  - libfuzzer
```

2. `.clusterfuzzlite/Dockerfile`：
```dockerfile
FROM gcr.io/oss-fuzz-base/base-builder
RUN apt-get update && apt-get install -y cmake
COPY . $SRC/yyjson
WORKDIR $SRC/yyjson
COPY .clusterfuzzlite/build.sh $SRC/
```

3. `.clusterfuzzlite/build.sh`（對應將 `harness/` 置於專案根目錄之結構）：
```bash
#!/bin/bash -eu
mkdir -p build && cd build
cmake .. -DCMAKE_C_COMPILER="$CC" -DCMAKE_C_FLAGS="$CFLAGS" \
  -DBUILD_SHARED_LIBS=OFF -DYYJSON_BUILD_TESTS=OFF
make -j$(nproc)
$CXX $CXXFLAGS -std=c++17 -I../src \
  ../harness/fuzz_advanced.cc libyyjson.a \
  $LIB_FUZZING_ENGINE -o $OUT/yyjson_fuzzer
cp ../harness/json.dict $OUT/yyjson_fuzzer.dict
```

4. `.github/workflows/cflite_pr.yml`：
```yaml
name: ClusterFuzzLite PR Fuzzing
on:
  pull_request:
    paths: ['src/**', 'harness/**', '.clusterfuzzlite/**']

permissions: read-all

jobs:
  PR:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
      - name: Build Fuzzers
        uses: google/clusterfuzzlite/actions/build_fuzzers@v1
        with:
          language: c++
          sanitizer: address
      - name: Run Fuzzers
        uses: google/clusterfuzzlite/actions/run_fuzzers@v1
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
          fuzz-seconds: 600
          mode: 'pr'
```

---

## 自我檢核

- **難度**：進階
- **預估時間**：25 分鐘

先別往下看答案，試著獨立完成下面 4 題推導與判別：

1. **靜態建置與插樁旗標衝突**：你在編譯一個 Autotools C 專案時，把 `CFLAGS="-O1 -g -fsanitize=address,fuzzer"`（直接帶 `-fsanitize=fuzzer` 而非 `-fsanitize=fuzzer-no-link`）傳給 `./configure && make`。結果編譯函式庫本體沒事，到了專案自帶的輔助測試程式階段卻噴出 `multiple definition of 'main'` 錯誤。請解釋為什麼會撞名，以及 OSS-Fuzz 如何用 `$CFLAGS` 與 `$LIB_FUZZING_ENGINE` 切開這兩個階段？
2. **覆蓋率瓶頸與字典算力換算**：某協定解析器的 `llvm-cov report` 顯示行覆蓋率卡在 `18%`，其中一個核心分支要精確比對 6-byte 的大寫 ASCII 指令字首 `"VERIFY"`。若模糊器只靠純隨機位元組變異（沒給字典檔），在單核 `5,000 exec/s` 基準吞吐下，盲猜命中這個 6-byte 精確魔數的期望嘗試次數與平均耗時各是多少？這如何解釋為何必須準備 `.dict` 字典檔？
3. **Stack Hash 去重判斷**：ClusterFuzz 在同一天收到以下三份 ASan Crash 報告，請問它們會被歸類成幾個獨立的漏洞 Issue（假設採標準 Top-`3` 專案框架與正規化規則）？請寫出每一份的 Crash State：
   - **報告 A**：`heap-buffer-overflow` → `#0 __asan_memcpy` → `#1 copy_field (parser.c:120)` → `#2 parse_tlv (parser.c:310)` → `#3 parse_batch (batch.c:45)` → `#4 LLVMFuzzerTestOneInput`
   - **報告 B**：`heap-buffer-overflow` → `#0 __asan_memcpy` → `#1 copy_field (parser.c:124)` → `#2 parse_tlv (parser.c:315)` → `#3 parse_batch (batch.c:45)` → `#4 LLVMFuzzerTestOneInput`
   - **報告 C**：`heap-use-after-free` → `#0 __asan_report_load8` → `#1 copy_field (parser.c:120)` → `#2 parse_tlv (parser.c:310)` → `#3 parse_batch (batch.c:45)` → `#4 LLVMFuzzerTestOneInput`
4. **不可重現 Crash 的排查**：你的模糊器在 Persistent Mode 連續跑了 `4,120` 次輸入後，於第 `4,121` 次觸發一個 `SEGV` 並吐出 `crash-9f8e7d`。但當你手動跑 `./fuzzer crash-9f8e7d` 單獨重播時，程式卻回傳 `0` 正常結束。請列出兩個最可能的工程原因與標準驗證步驟。

---

### 參考解答

1. **旗標衝突根因與兩階段切分**：
   - `-fsanitize=fuzzer` 會自動把 Clang 內建的 `libclang_rt.fuzzer` 靜態執行期庫連進來，而它裡面已經定義好全域進入點 `main()`（負責讀命令列參數、管理語料庫並迴圈呼叫 `LLVMFuzzerTestOneInput`）。當建置系統接著編譯專案自帶的小工具或單元測試（裡面也有自己的 `main()`）時，就會直接發生 `multiple definition of 'main'` 連結錯誤。
   - **OSS-Fuzz 解法**：編譯受測函式庫本體時，`$CFLAGS`/`$CXXFLAGS` 只放 **`-fsanitize=fuzzer-no-link`** 來插入覆蓋率與比較探針（搭配 `-fsanitize=address,undefined` 等錯誤檢查旗標），不連進模糊引擎的 `main()`。等到最後一步 `build.sh` 單獨編譯你的 Fuzzer Harness 並連結靜態庫時，才在連結命令最後補上 **`$LIB_FUZZING_ENGINE`**，把引擎與 `main()` 精準注進最終的 Fuzzer 執行檔。
2. **6-byte 精確比對期望耗時計算**：
   - 6 bytes 等於 `6 × 8 = 48 bits`，總組合數為 `2^48 = 281,474,976,710,656`（約 `2.81 × 10^14` 種）。
   - 在每次獨立均勻隨機抽取 6 bytes（有放回）的模型下，首次命中的期望嘗試次數為 `2^48 ≈ 2.81 × 10^14` 次（即使算均勻不放回抽樣，期望次數也高達 `(2^48 + 1) / 2 ≈ 1.41 × 10^14` 次）。
   - 換算成 `5,000 exec/s` 單核時間：`281,474,976,710,656 / 5,000 = 56,294,995,342.13 秒 ≈ 1,785.10 年`（以 365 天／年計；不放回半數空間也要約 `892.55 年`，四捨五入約 `893 年`）。
   - 雖然灰箱模糊器能靠 `cmp` 插樁（如 TraceCmp）拆解部分字面值，但只要該比對沒被比較回饋直接觀測到（如經雜湊查找或特定轉換），TraceCmp 就推不出來。放入包含 `"VERIFY"` 的 `.dict` 字典檔後，突變器能直接把完整詞元插進輸入裡，不用靠隨機位元翻轉去湊 48 bits。
3. **Stack Hash 去重結果**：
   - 會被歸類成 **2 個獨立 Issue**（報告 A 與 B 合併為同一個；報告 C 獨立成另一個）：
     - 先濾掉 `#0 __asan_memcpy` / `#0 __asan_report_load8`（Sanitizer 執行期框架）與 `#4 LLVMFuzzerTestOneInput`（模糊引擎入口），留下投影後的專案函式層 `copy_field` → `parse_tlv` → `parse_batch`（剛好 `k = 3` 層）。
     - **報告 A** 與 **報告 B** 雖然行號不同（`120/310` vs `124/315`），但正規化會剝除行號，且兩者錯誤類型同為 `heap-buffer-overflow`，產出的 Crash State 皆為 `heap-buffer-overflow | copy_field | parse_tlv | parse_batch`，Stack Hash 相同而合併。
     - **報告 C** 雖然 Top-3 函式名稱完全一樣，但錯誤類型是 **`heap-use-after-free`**，產出的 Crash State 不同，因此會獨立開立另一張漏洞追蹤單（越界拷貝與釋放後使用通常是不同的修補點與風險等級）。
4. **不可重現 Crash 的排查與驗證**：
   - **可能原因 A（跨迭代全域狀態汙染）**：受測函式庫內部維護了全域單例、靜態快取或未重置的全域變數；前 `4,120` 筆輸入一步步破壞了該狀態，直到第 `4,121` 筆才引爆，因此單獨跑最後一筆不會觸發。
   - **可能原因 B（未初始化記憶體或記憶體佈局依賴）**：函式庫依賴特定堆積回收順序（Accumulated Heap Layout）或讀到了殘留在未歸零緩衝區上的歷史位元組；單次執行時堆積處於乾淨初始狀態而掩蓋了缺陷。
   - **標準驗證步驟**：保存 Fuzzing 期間送入 `LLVMFuzzerTestOneInput` 的輸入序列，先在同一行程內依序重播確認是否為跨迭代狀態累積；同時用 `MemorySanitizer`（MSan）查核未初始化讀取、以 ASan 查核越界與生命週期問題，並在維持先後順序下逐步縮減前置輸入序列以鎖定汙染源頭，最後在 Harness 補上上下文重置呼叫。

---

## 延伸閱讀

1. **Google OSS-Fuzz 官方文件**：完整說明 `project.yaml`、`Dockerfile`、`build.sh` 規範、`infra/helper.py` 本地除錯流程，以及各語言（C/C++、Rust、Go、Python、JVM）的整合範例（https://google.github.io/oss-fuzz/）。
2. **ClusterFuzzLite 官方指南**：說明如何將 OSS-Fuzz 引擎輕量化整合至 GitHub Actions 與 GitLab CI 的 PR 閘門與批次修剪流程（https://google.github.io/clusterfuzzlite/）。
3. **LLVM Source-Based Code Coverage & LibFuzzer 文件**：深入查閱 `-fprofile-instr-generate`、`llvm-profdata`、`llvm-cov` 覆蓋率報告選項，以及 `FuzzedDataProvider.h` 標頭檔實作細節（https://clang.llvm.org/docs/SourceBasedCodeCoverage.html 與 https://llvm.org/docs/LibFuzzer.html）。
4. **ClusterFuzz 原始碼與去重架構**：檢視 ClusterFuzz 如何過濾 Sanitizer 堆疊框架、正規化 Top-k 函式簽章並計算 Stack Hash（https://github.com/google/clusterfuzz）。
5. **OSSF Fuzz Introspector**：OpenSSF 維護的靜態與動態覆蓋率洞察平台，可直觀查詢主流開源專案目前在 OSS-Fuzz 中的覆蓋盲區，作為挑選高勝率目標的第一手儀表板（https://github.com/ossf/fuzz-introspector）。
