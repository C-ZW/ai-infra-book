# 第 26 章：JS 引擎 JIT 類型混淆與 V8 Ubercage 沙箱架構

第 25 章我們看過了 Rust 與 C FFI 在 `libnexus-parse` 原生邊界上的記憶體破口。回到更上層的 Node.js 執行時期，很多人心裡還是抱著一個假設：只要業務邏輯留在純 JavaScript 或 TypeScript 裡，沒有碰任何 C/C++ 或 `unsafe` 模組，V8 引擎就會靠垃圾回收與邊界檢查替我們守住記憶體安全。

在 **NexusPay** 的產品演進中，這項假設正直接承受考驗。為了讓企業商戶自訂風控規則與 Webhook 過濾條件，團隊打算在規則引擎內嵌入一個受控的 JavaScript 執行環境（基於 V8 Isolate）。

但別忘了，V8 本身是一套用 C++ 寫成的大型系統，為了讓動態弱型別語言跑出接近編譯語言的吞吐量，它內建了 **Maglev** 與 **TurboFan** 等即時編譯器（JIT）。JIT 會在執行期對物件形狀與數值區間做出大膽假設，並順手拿掉機器碼裡重複的檢查。只要編譯器的區間推算出現一道裂縫，純 JavaScript 輸入就能打破型別不變量，把記憶體損毀帶進引擎底層。這正是現代 V8 必須引入 **V8 Sandbox**（專案代號 **Ubercage**）的原因——但就算有了 Ubercage，作業系統層級的行程隔離在伺服器端依然不可取代。

---

## 從你已知的出發

為什麼一段連 `require` 都沒呼叫、百分之百純數字與陣列運算的 JavaScript 函式，跑了幾萬次之後，竟然能直接讀寫 V8 引擎底層的 C++ 堆積記憶體？

因為動態語言的彈性與極致效能天生互斥。JavaScript 陣列沒有限定元素型別，V8 沒辦法在編譯期就決定記憶體偏移，只能先靠直譯器觀察資料流，再靠**猜測性最佳化**（Speculative Optimization）賭這個函式「接下來收到的陣列都長一樣、索引值都不會越界」。

為了贏得效能，TurboFan 的**範圍分析**（Range Analysis）會把「它推算一定不會越界」的防護檢查（Guard）直接從機器碼裡拔掉。一旦編譯器算錯數值範圍（比如漏算了 `-0`），原本該攔住越界的檢查早就不見了，純 JS 陣列立刻變成可以越界讀寫相鄰記憶體的破口。本章前半段會拆解**類型混淆**（Type Confusion）與**邊界檢查消除**（Bounds Check Elimination）怎麼打破 V8 的型別不變量；後半段則看 **V8 Sandbox**（Ubercage）如何把記憶體損毀關進 `1 TiB`（`2^40` bytes）的位址空間籠子裡，以及為什麼在 NexusPay 這種多租戶後端平台上，依然不能把 V8 Isolate 當成安全邊界。

---

## 機制與推導

### 攻擊者目標與實質影響

當攻擊者盯上允許執行自訂 JS 腳本的 V8 執行環境時，他們能拿到多少控制權，完全取決於底層的隔離強度：

第一層目標是打破受管語言的型別與邊界隔離。在正常情況下，純 JS 跑在垃圾回收堆積上，根本摸不到原始記憶體位址。但只要觸發 JIT 編譯器的型別假設錯誤或消掉邊界檢查，攻擊者不用呼叫任何原生模組，就能把 JS 物件參考跟未封裝的 64 位元浮點數混在一起讀寫，或是跨出陣列長度上限，直接掌控 V8 堆積。

第二層目標是在沒開沙箱的伺服器端直接打穿宿主行程。這點對後端特別致命：主流官方發行的伺服器端 Node.js（包含 v22 與 v24 二進位檔）預設都沒有開啟 V8 Sandbox 與指標壓縮。一旦惡意腳本在這種環境拿到引擎越界寫入能力，破壞就會直接發生在宿主行程的 64 位元虛擬位址空間裡，不僅能偷看同行程記憶體裡的資料庫憑證與多租戶帳本，甚至能竄改宿主堆疊返回位址（見第 22 章）或覆寫 N-API 原生模組（如第 25 章的 `libnexus-parse`）結構。

第三層則是與 V8 Sandbox 的正面交鋒。在現代瀏覽器或啟用 Ubercage 的執行時期裡，V8 堆積用位元算術鎖死了對籠外位址的直接定址，讓攻擊者沒辦法單靠改壞一個堆積指標就去寫宿主堆疊或 C++ 函式指標。攻擊者被迫另外尋找沙箱逃逸路徑（例如攻擊宿主綁定的外部指標介面或 `TrustedSpace` 邊界缺陷），這也說明了為什麼後端系統必須再疊上作業系統行程與 `seccomp-bpf` 隔離。

---

### V8 動態物件記憶體佈局：Tagged Pointer、Map 與 Elements Kind

要看懂 JIT 為什麼會把型別搞混，得先看看 V8 在記憶體裡怎麼分辨「這是一串數字」還是「這是一個記憶體位址」。

#### Tagged Pointer 與 Smi 編碼

JavaScript 沒有區分 32 位元整數與 64 位元浮點數，全部都叫 `number`。為了不讓每一個小整數（像迴圈計數器 `i` 或陣列長度 `4`）都在堆積上配置一個物件，V8 採用了 **Tagged Pointer**（標記指標）設計。因為堆積物件在記憶體裡至少會對齊 `4-byte`（開啟指標壓縮時）或 `8-byte`，位址的最低位元永遠是 `0`，V8 就把這個最低位元拿來當型別標籤：

```text
32-bit 壓縮槽位 (Pointer Compression 啟用時，單槽 4 bytes):
┌───────────────────────────────────────────────────────────┬───┐
│                   31-bit 有號整數值 (例: 30 << 1 = 0x3c)  │ 0 │ ──► Smi (小整數，最低位元 = 0)
└───────────────────────────────────────────────────────────┴───┘
┌───────────────────────────────────────────────────────────┬───┐
│                   31-bit 堆積對齊偏移位址                 │ 1 │ ──► HeapObject 指標 (最低位元 = 1)
└───────────────────────────────────────────────────────────┴───┘
```

當最低位元是 `0` 時，代表這是一個 **Smi**（Small Integer，小整數）。在啟用 32 位元指標壓縮（Pointer Compression）的環境下，31 位元有號整數會左移 `1` 位元存放，例如整數 `30` 會編成 `30 << 1 = 0x0000_003c`。而在未壓縮的 64 位元設定（如標準 Node.js 建置）中，Smi 則放在高 32 位元、低 32 位元填 `0`（例如 `30` 編成 `0x0000_001e_0000_0000`）。不管是哪一種，CPU 只要看最低位元是不是 `0`，一個指令週期就能認出它是整數。

反過來，當最低位元是 `1` 時，代表這是一個 **HeapObject 指標**。任何配置在 V8 堆積上的物件，它的真實對齊位址都會加上 `1` 變成標記指標；引擎要解參考讀取欄位時，會先減掉 `1` 還原回真實記憶體位址。

#### Map（Hidden Class）與屬性偏移

JavaScript 物件沒有靜態類別定義，所以 V8 會幫形狀相同的物件共用一個 **Map**（也稱為 Hidden Class 或 Shape）。任何 `HeapObject` 的第一個欄位（偏移 `+0x00`）一定是指向自身 `Map` 的標記指標。

這個 `Map` 裡記了該物件的實例類型（像 `JS_OBJECT_TYPE` 或 `JS_ARRAY_TYPE`）、實例大小、`DescriptorArray`（屬性名稱與槽位偏移對照表），還有當物件動態新增屬性時要跳去哪個新 `Map` 的轉移樹（Transition Tree）。

#### Elements Kind（元素種類）與單向轉移階梯

如果是 `JSArray` 陣列物件，除了它自己頭部的 `map`、`properties`、`elements` 與 `length` 四個欄位外，真正的陣列元素其實放在 `elements` 指標指向的後備陣列（Backing Store）裡。V8 用 **Elements Kind** 來標記後備陣列的儲存格式：

| Elements Kind | 後備儲存區結構 | 單一元素寬度 | 記憶體中儲存的內容 |
|---|---|---|---|
| `PACKED_SMI_ELEMENTS` | `FixedArray` | 指標寬度（壓縮 `4B` / 原生 `8B`） | 緊密排列的標記後 Smi，無空洞 |
| `PACKED_DOUBLE_ELEMENTS` | `FixedDoubleArray` | 固定 `8 bytes` | **未封裝的 64 位元 IEEE 754 `float64`**，無 tag |
| `PACKED_ELEMENTS` | `FixedArray` | 指標寬度（壓縮 `4B` / 原生 `8B`） | Tagged Pointer（浮點數需封裝為 `HeapNumber`） |
| `HOLEY_*` 變體 | 同上對應陣列 | 同上 | 空缺槽位填入特殊標記值 `<the_hole>` |

Elements Kind 只能順著固定的階梯**單向升級**。一開始宣告 `[1, 2, 3]` 時是緊密的 `PACKED_SMI_ELEMENTS`；一旦推入浮點數 `1.5`，就會升級成 `PACKED_DOUBLE_ELEMENTS`；再推入字串 `"x"`，又會轉移成通用指標陣列 `PACKED_ELEMENTS`。如果出現跳號賦值留下空洞，則會不可逆地變成 `HOLEY_*`。

注意看表格裡的第二列與第三列，這裡藏著整個 V8 最核心的安全不變量：`FixedDoubleArray` 裡面的每 8 個位元組都是**純數值位元**（raw `double`），引擎讀寫它時完全不會檢查 Tagged Pointer 標籤；但 `FixedArray`（`PACKED_ELEMENTS`）裡面放的卻是**標記值**（Tagged Values），最低位元為 `1` 就會被當成堆積物件指標去解參考。只要 JIT 編譯器把這兩種陣列的 `Map` 或 `ElementsKind` 搞混，純浮點數跟記憶體指標之間的界線就會當場崩潰。

---

### V8 多層 JIT 管線、猜測性最佳化與範圍分析

為了同時顧好啟動速度跟最高執行效能，現代 V8 引擎設計了四層執行管線：

```text
JS 原始碼 ──▶ Ignition（位元碼直譯器 + Feedback Vector 收集執行期型別）
                │
                ├─▶ Sparkplug（基線非最佳化編譯器，快速產出機器碼）
                │
                ├─▶ Maglev（中階 SSA 最佳化編譯器，低延遲平衡效能）
                │
                └─▶ TurboFan（頂層最佳化編譯器：Sea-of-Nodes / Turboshaft）
                      ├─ Typer & Range Analysis（推導數值區間 [min, max]）
                      ├─ Check Elimination（消除冗餘 CheckMaps / CheckBounds）
                      └─ Lowering & CodeGen（產出無保護檢查的原生機器碼）
```

程式碼剛跑起來時，Ignition 直譯器會在每次讀寫屬性或陣列元素時，透過 Inline Cache（IC）把實際看過的 `Map` 跟型別記進 Feedback Vector。等某個函式被呼叫夠多次、變成熱點進入 **Maglev** 或 **TurboFan** 時，編譯器就會根據前面收集到的紀錄產出專門化的中間表示（IR），並在開頭放進兩個關鍵的保護節點（Guards）：

第一個是 **`CheckMaps`**。它負責檢查傳入物件的 `Map` 指標是不是跟當初假設的一模一樣；如果執行期突然傳進來不同形狀或不同 `ElementsKind` 的物件，就會立刻觸發 **Eager Deoptimization**（急切去最佳化），丟掉最佳化棧幀，安全退回 Ignition 直譯器慢慢跑。

第二個是 **`CheckBounds`**，負責在存取陣列前確認索引值符合無號範圍 `0 <= index < length`。

問題是，如果在一個密集迴圈裡每次讀寫陣列都要跑一次 `CheckMaps` 與 `CheckBounds`，CPU 分支預測與比對還是太慢了。所以 TurboFan 的 **Typer** 階段會執行**範圍分析**（Range Analysis），幫運算圖上的每個節點算出一個靜態數值區間 `Range(min, max)`，以及額外的型別旗標（例如有沒有可能是 `NaN`、包不包含負零 `MinusZero`）。

接著走到 **Check Elimination**（檢查消除階段）。當編譯器看到 `CheckBounds(idx, len)` 節點時，如果前面的靜態區間推論已經保證：

```text
idx.min >= 0   AND   idx.max < len.min
```

編譯器就會認定這個邊界檢查一輩子都不可能失敗，**直接把 `CheckBounds` 節點從 IR 裡刪掉**。最後生出來的原生機器碼在讀寫 `arr[idx]` 時，就只剩下一條單純的位址加法與記憶體存取指令，再也沒有任何長度把關。

#### 類型混淆與越界原語是怎麼成形的？

所謂的 Range Analysis 漏洞（常稱為 **Typer Bug**），說穿了就是**編譯器在靜態推算出來的數值區間，跟 JavaScript 實際跑出來的值對不上**。

先看一段把 `-0`（負零）邊界特性放大的概念程式碼：

```javascript
function trigger(y) {
  // 假設編譯器在前面推論 y 的區間是 Range(0, 0)，卻漏標了 MinusZero (-0) 旗標
  // Object.is(-0, -0) 在執行期會回傳 true！
  let i = Object.is(y, -0) ? -1 : 0; 
  let k = i * -5;
  return arr[k];
}
```

在 JavaScript 的 IEEE 754 浮點數規範裡，`-0 === +0` 是 `true`，但 `Object.is(-0, -0)` 也是 `true`。歷史上不少 V8 漏洞，都出在某個數學運算（如 `Math.expm1`、`Math.sign` 或特定乘法降階）可能產出 `-0`，但 Typer 卻只把結果標為 `Range(0, 0)` 而忘了加上 `MinusZero` 旗標。

結果編譯器在編譯 `Object.is(y, -0)` 時，看著 `Range(0, 0)` 以為它永遠不可能等於 `-0`，便推論變數 `i` 的區間是 `[0, 0]`、乘上 `-5` 之後的索引 `k` 也是 `[0, 0]`，開心地把 `arr[k]` 的 `CheckBounds` 給刪了；偏偏到了執行期傳入 `-0` 時，真正跑出來的 `i` 是 `-1`、`k` 是 `+5`。

一旦這道裂縫打開，在引擎記憶體層面就會一步步演變成三個標準的概念原語（Conceptual Primitives）：

第一步是**越界讀寫**（OOB R/W）。靠著被消掉邊界檢查的索引算術，直接讀寫緊貼在後備陣列（`FixedArray` / `FixedDoubleArray`）後面的記憶體欄位。最常見的手法是直接把相鄰另一個 `JSArray` 的 `length` 欄位改大，讓原本長度只有 `4` 的合法陣列瞬間變成可以合法讀寫幾千個槽位的「超大視窗」。

第二步是 **`addrof` 概念原語**（洩漏物件位址）。當一個 `PACKED_DOUBLE_ELEMENTS` 浮點數陣列可以越界讀到後面 `PACKED_ELEMENTS` 物件陣列的槽位時，只要用浮點數的視角去讀那個放了物件參考的槽位，就能把物件的 Tagged Pointer 位址當成 64 位元 `float64` 數字讀出來。

第三步是 **`fakeobj` 概念原語**（偽造物件指標）。反過來，先把算好的位元樣式當成浮點數寫進後備儲存區，再透過被混淆的物件陣列視角去讀那個槽位；只要最低位元是 `1`，V8 就會把它當成真的 `HeapObject` 指標去解參考。

理解了這三個概念原語，我們就不用去背那些繁瑣的武器化腳本，而是把目光放到更關鍵的架構問題上：如果我們直接假設攻擊者已經在 V8 堆積裡拿到了這三個原語，現代引擎跟作業系統要怎麼把傷害鎖死？

---

### Worked Example：Range Analysis `[0, 0]` vs `-1` 與 Ubercage `32-bit` 壓縮偏移算術

我們直接用一組完整的十六進位記憶體佈局與算式，把剛剛講的兩件事算清楚：Part A 先算編譯器誤判 `[0, 0]` 與執行期 `-1` 怎麼在壓縮指標堆積上精準覆寫相鄰陣列的 `length`；Part B 接著算為什麼開啟 **V8 Sandbox**（Ubercage）之後，籠子裡被改壞的 `32-bit` 壓縮偏移永遠摸不到籠子外面的宿主堆疊返回位址。

```text
========================================================================
Part A：Range Analysis [0, 0] vs 執行期 -1 的邊界消除與偏移計算
========================================================================
假設 V8 堆積啟用 32-bit 指標壓縮（單一物件槽位寬度 4 bytes）：
- 目標陣列 arr  = [1.1, 2.2, 3.3, 4.4]  (PACKED_DOUBLE_ELEMENTS, length = 4)
- 相鄰陣列 adj  = [10, 20, 30, 40]      (PACKED_SMI_ELEMENTS,     length = 4)

1. 堆積緊鄰配置（假設 GC 依序線性配置 FixedDoubleArray 與 adj JSArray）：
   [elements_base + 0x00]  arr 後備儲存區 map 壓縮指標 (4 bytes)
   [elements_base + 0x04]  arr 後備儲存區 length Smi = 0x00000008 (即 4 << 1, 4 bytes)
   [elements_base + 0x08]  arr[0] = 1.1 (8 bytes, float64)
   [elements_base + 0x10]  arr[1] = 2.2 (8 bytes, float64)
   [elements_base + 0x18]  arr[2] = 3.3 (8 bytes, float64)
   [elements_base + 0x20]  arr[3] = 4.4 (8 bytes, float64)
   ---------------------------------------------------------------------
   [elements_base + 0x28]  adj JSArray map 壓縮指標 (4 bytes)
   [elements_base + 0x2c]  adj JSArray properties 壓縮指標 (4 bytes)
   [elements_base + 0x30]  adj JSArray elements 壓縮指標 (4 bytes)
   [elements_base + 0x34]  adj JSArray length Smi = 0x00000008 (4 bytes)

2. 編譯器 Typer 推論錯誤與 CheckBounds 消除：
   假設某個數值邊界處理遺漏了 -0（MinusZero）型別位元：
   - 靜態推論值 y ∈ Range(0, 0)（無 MinusZero 旗標）
   - 衍生變數 i = Object.is(y, -0) ? -1 : 0  ──▶ 編譯器錯誤標註區間 i ∈ [0, 0]（保留原運算分支）
   - 索引運算 k = i * -5                    ──▶ 編譯器推論區間 k ∈ [0, 0]
   - CheckBounds(k, arr.length = 4)：
     檢查 k.min >= 0 (0 >= 0) 且 k.max < 4 (0 < 4) ──▶ 恆真，CheckBounds 遭移除！

3. 執行期落差與記憶體偏移命中：
   - 若直接以未縮放的 i = -1 寫入 arr[i]：
     寫入位址 = elements_base + 0x08 + (-1) * 8 = elements_base + 0x00
     ──▶ 直接覆寫 arr 後備儲存區自身的 map + length 8-byte 檔頭。
   - 若以縮放後的 k = (-1) * (-5) = +5 寫入 arr[k]：
     寫入位址 = elements_base + 0x08 + 5 * 8 = elements_base + 0x30
     （64-bit 寫入涵蓋 0x30..0x37，低 32 位元覆寫 adj.elements [+0x30]，高 32 位元直接覆寫 adj.length [+0x34]！）
   - 原先 adj.length 為 Smi 4 (0x0000_0008)；若寫入的高 32 位元為 0x0000_2000，
     Smi 解碼後 0x0000_2000 >> 1 = 4,096，adj 隨即取得跨越相鄰物件的越界讀寫視窗。

========================================================================
Part B：V8 Sandbox (Ubercage) 1 TiB 與 32-bit 壓縮偏移算術邊界
========================================================================
設定宿主行程 64 位元虛擬記憶體佈局（Linux x86_64）：
- cage_base          = 0x0000_2000_0000_0000
- cage_size          = 1 TiB = 2^40 bytes = 0x0100_0000_0000 bytes
- Ubercage 合法位址  = [0x0000_2000_0000_0000, 0x0000_20ff_ffff_ffff]
- 宿主堆疊 Saved RIP = 0x0000_7fff_e410_2a88  (位於籠外，見 Ch22)
- 宿主原生函式位址   = 0x0000_5555_5568_4200  (位於籠外 libnexus-parse / libc)

驗證 1：32-bit 壓縮指標（Pointer Compression 子籠 4 GiB）最大可定址範圍
- 壓縮指標 p_32 為 uint32，最大值 = 0xffff_ffff (= 2^32 - 1 = 4,294,967,295)
- 解壓縮位址 = cage_base + uint64(p_32)
               = 0x0000_2000_0000_0000 + 0x0000_0000_ffff_ffff
               = 0x0000_2000_ffff_ffff
  ──▶ 永遠落在 Ubercage 前 4 GiB 區間內，遠小於 0x0000_20ff_ffff_ffff。

驗證 2：籠內 ArrayBuffer 使用之 40-bit SandboxedPtr 最大可定址範圍
- SandboxedPtr 將 40-bit 偏移存於 64-bit 欄位高 40 位元（右移 24 位元解碼）：
  offset_40 = raw_u64 >> 24，最大值 = 0x00ff_ffff_ffff (= 2^40 - 1)
- 解碼後位址 = cage_base + offset_40
               = 0x0000_2000_0000_0000 + 0x0000_00ff_ffff_ffff
               = 0x0000_20ff_ffff_ffff
  ──▶ 就算在籠內任意竄改 raw_u64 為 0xffff_ffff_ffff_ffff，仍無法跨出籠頂！

驗證 3：計算到達宿主堆疊 Saved RIP 所需的相對偏移
- delta_stack = 0x0000_7fff_e410_2a88 - 0x0000_2000_0000_0000
              = 0x0000_5fff_e410_2a88
- 有效位元寬度：0x5fff... 最高位元為 bit 46，需至少 47 bits 才能編碼。
  因為 47 bits > 40 bits (SandboxedPtr) 且 47 bits > 32 bits (壓縮指標)，
  任何籠內已損毀的壓縮指標或 SandboxedPtr，在數學上都無法編碼出宿主堆疊或
  libc/libnexus-parse 的虛擬位址，徹底阻斷「堆內寫壞一個指標就直接覆寫 RIP」的路徑。
```

---

### V8 Sandbox（Ubercage）隔離架構與籠外安全邊界

從上面 Part B 的位元算術就能看出 **V8 Sandbox**（Ubercage）的設計哲學：與其奢望「把幾百萬行 C++ 寫的 V8 引擎修到永遠沒有半個記憶體漏洞」，不如**直接假設攻擊者已經在 V8 堆積裡面拿到任意讀寫能力，然後靠硬性的位元寬度限制，把所有破壞死死關在 `1 TiB` 的沙箱籠子裡**。

為了把這個 `1 TiB`（`2^40` bytes）的籠子關緊，V8 團隊把沙箱內部所有的原始 64 位元裸指標全部拔掉，換成三道轉接防線：

```text
1 TiB V8 Sandbox (Ubercage) [0x0000_2000_0000_0000 .. 0x0000_20ff_ffff_ffff]
  ├─ JSArray / HeapObject（32-bit 壓縮偏移，僅能定址 4 GiB 子區）
  │    ├─ 指向籠內後備陣列 ──▶ cage_base + uint64(p_32)
  │    ├─ ArrayBuffer 後備 ──▶ cage_base + (raw_u64 >> 24) [40-bit]
  │    ├─ 外部 C++ 物件參考 ──▶ 32-bit EPT Handle（索引 + Type Tag）
  │    └─ 可執行機器碼參考  ──▶ 32-bit CPT Handle / Trusted Pointer
  │
  ▼ （籠內指標無法直接定址籠外記憶體，必須經過受保護間接表）
  ├─ ExternalPointerTable（EPT，位於籠外受保護記憶體）
  │    └─ 比對預期 Type Tag 相符後，才解參考真實 64-bit C++ 指標
  └─ TrustedSpace & CodePointerTable（CPT，位於籠外隔離區）
       └─ 隔離 JIT Code 物件與 BytecodeArray，阻斷籠內寫入竄改指令
```

第一道防線是 **ExternalPointerTable**（EPT）。V8 經常需要跟宿主環境的 C++ 物件（例如瀏覽器 DOM 或 Node.js C++ 綁定物件）互動。以前 JS 包裝物件裡面直接存了一個指向 C++ 物件的 64 位元裸指標，只要改掉那個指標就能劫持 C++ 虛函式表（vtable）。

現在有了 Ubercage，真實的 64 位元裸指標全部搬到籠子外面的 `ExternalPointerTable` 集中保管；籠子裡的 JS 物件只拿到一個 `32-bit` 的索引號碼牌（Handle），而且表格裡的每一格都綁了嚴格的型別標籤（Type Tag）。就算攻擊者在籠內亂改號碼牌，也只能指到同一張表裡現有的槽位，而且型別標籤對不上時當場就會報錯中止。

第二道防線是 **TrustedSpace 與 CodePointerTable**（CPT）。JIT 編譯出來的機器碼入口、程式碼中繼資料（`Code` 物件）還有直譯器的位元碼（`BytecodeArray`）如果放在籠子裡，攻擊者只要改寫位元碼或程式碼指標，就能直接控制執行流。所以 Ubercage 把這些敏感結構通通移出 `1 TiB` 沙箱，放進獨立的 **TrustedSpace**，籠內物件同樣只能透過 `CodePointerTable` 的號碼牌間接呼叫。

第三道防線則是針對 `ArrayBuffer` 與 WebAssembly 記憶體的 **`SandboxedPtr`**。因為大型 `ArrayBuffer` 可能會超過 `4 GiB` 指標壓縮子籠的大小，它們會被配置在 `1 TiB` 沙箱的其餘區段裡，並強制透過「右移 `24` 位元」加上 `cage_base` 的算術來解碼。不管你把那 64 個位元改成什麼數字，右移 `24` 位元後最多就是 `40 bits`，在數學上絕對跨不出 `[cage_base, cage_base + 2^40 - 1]` 這座籠子。

#### 為什麼 V8 Isolate + Ubercage 還是不能取代作業系統行程隔離？

回到 NexusPay 的商戶規則引擎場景。很多架構師看到這裡會問：「既然 V8 可以開獨立的 Isolate，現在又有 Ubercage，那我們能不能直接在 Node.js API 閘道行程裡面開一個 Isolate 來跑商戶寫的腳本？」

答案是**絕對不行**，有三個非常現實的工程原因：

第一個原因是**伺服器端 Node.js 的預設編譯組態根本沒開 Ubercage**。官方發行的 Node.js（包含我們等一下會在實驗裡驗證的 Node.js v24）為了相容龐大的 N-API 與 C++ 原生外掛生態系，預設編譯旗標把 **`v8_enable_sandbox`** 和 **`v8_enable_pointer_compression`** 都設成了 **`0`**。

這意味著你在標準 Node.js 裡不管是用 `node:vm` 還是預設編譯的 `isolated-vm`，**底層完全沒有那座 1 TiB 的籠子**，V8 堆積跟你的主程式共用同一個毫無遮攔的 64 位元位址空間。

第二個原因是**同行程的 CPU 推測執行側通道**（Speculative Side-Channels）。就算你特地自己重新編譯了一版開啟 V8 Sandbox 的執行時期，Ubercage 終究只是一層「攔截非法指標寫入」的軟體記憶體沙箱。

只要不信任腳本跟你的多租戶帳本、JWT 私鑰住在同一個作業系統行程的虛擬位址空間裡，攻擊者還是有機會利用 Spectre 這類微架構推測執行側通道，跨過軟體邊界偷看同行程裡的機密記憶體。這也是為什麼連催生出 Ubercage 的 Chromium 瀏覽器，都依然把 **Site Isolation**（不同網站拆成不同 OS 行程）當成不可退讓的底線。

第三個原因則是**宿主綁定介面與資源競爭**。你每開放一個宿主 C++ 函式給商戶腳本呼叫，就是在 EPT 上開了一道跨界橋樑；只要綁定介面有一點生命週期瑕疵，沙箱就可能被穿破。更別提如果商戶腳本跑了一個死迴圈或瘋狂配置記憶體，放在同一個行程裡就會直接卡死或拖垮主服務。

---

## 故障模式與防禦

在審查支援自訂腳本或動態規則的後端系統時，我們最常看到團隊踩進下面四個坑。

### 故障模式 1：把 `node:vm` 當成安全沙箱

很多開發者看到 Node.js 內建了 `node:vm` 模組，又有 `vm.runInNewContext()`，就以為它能安全隔離不信任的程式碼。其實 Node.js 官方文件開頭就白紙黑字寫了：`node:vm` 不是安全機制。

看看下面這行連記憶體漏洞都不用找、純靠 JavaScript 原型鏈就能打穿 `node:vm` 的經典寫法：

```javascript
// 在 node:vm 的沙箱上下文裡，順著建構子原型鏈直接拿回宿主環境的 process
const hostProcess = this.constructor.constructor("return process")();
```

因為 `node:vm` 跟主行程共用同一個 V8 Isolate 堆積與事件迴圈，只要順著傳入物件的 `.constructor.constructor` 摸回宿主的 `Function` 建構子，一秒鐘就能拿到 `process.env` 裡的資料庫密碼與 `child_process`。

### 故障模式 2：讓多租戶主服務跟不信任腳本住在同一個 OS 行程

有些團隊知道 `node:vm` 不安全，於是改用 `isolated-vm` 在同一個 Node.js 行程裡開出獨立的 `v8::Isolate`。這樣確實擋掉了原型鏈逃逸，但如果這個 Isolate 還是跑在 NexusPay 的主 API 閘道或帳務 Worker 行程裡面，該行程的記憶體裡依然躺著資料庫連線、JWT 私鑰（第 4 章）以及其他商戶的交易資料。在標準 Node.js 預設關閉 Ubercage 的前提下，一旦 V8 爆出一個 JIT 0-day，整台主服務跟所有租戶的機密就會一起陪葬。

### 故障模式 3：為了幾行簡單的商業判斷，白白打開整套 JIT 編譯器

商戶寫的風控或折扣規則，九成以上都只是像 `tx.amount > 10000 && tx.country !== 'US'` 這種跑一次不到幾微秒的簡單邏輯。為了這幾行判斷，團隊卻預設開啟了包含 Maglev 與 TurboFan 在內的整套 JIT 編譯管線，等於平白無故把幾十萬行最容易出 Typer Bug 的複雜 C++ 編譯器程式碼暴露給外部輸入。

### 故障模式 4：Worker 行程裡留了太多內建模組與系統呼叫權限

就算把規則引擎拆到了獨立的 Worker 行程，如果這個行程還是能隨意呼叫 `fs`、`net`、`http` 模組，而且容器本身沒有限制網路與系統呼叫，那麼攻擊者一旦突破 JS 引擎拿到原生執行權，馬上就能在內網橫向掃描或讀寫宿主檔案系統。

### 縱深防禦設計決策

要幫 NexusPay 的規則引擎建立真正扛得住攻擊的防線，我們應該按照「砍掉非必要 JIT ＋ 引擎沙箱 ＋ 作業系統行程隔離」三層架構來收緊：

| 防禦層級 | 具體控制措施 | 攔截的威脅與不變量 | 工程取捨與代價 |
|---|---|---|---|
| **1. 引擎與語法層** | 優先改用沒有 JIT 的表達式引擎（如 CEL / JSONLogic）或編譯成 Wasm；如果非跑 JS 不可，加上 V8 **`--jitless`** 旗標 | `--jitless` 會徹底關掉 Maglev 與 TurboFan 的機器碼生成，從根源砍掉所有 Range Analysis 與 Check Elimination 類型的 JIT 漏洞 | 執行速度會退回 Ignition 直譯器水準（純密集迴圈會變慢），但對一般商業規則判斷幾乎感覺不到差異 |
| **2. 執行時期沙箱層** | 使用明確開啟 **V8 Sandbox**（`v8_enable_sandbox=true`）的獨立執行時期來跑規則 Worker，並把暴露給 Isolate 的宿主 API 砍到最少 | 就算直譯器或執行時期底層出現未修補的記憶體錯誤，指標破壞也會被鎖在 `1 TiB` 的 Ubercage 籠子裡 | 需要自己維護開啟沙箱旗標的客製化建置，或改用專用的嵌入式 V8 執行時期 |
| **3. OS 行程與核心層** | 把腳本丟進無狀態的獨立 Worker 行程（裡面不放任何金鑰與 DB 連線），搭配 Linux Namespaces、`cgroups` 資源限額與 **seccomp-bpf** 系統呼叫白名單 | 就算 V8 沙箱被完全穿破、攻擊者拿到 Worker 裡的 RCE，他也沒有網路、不能寫檔案、不能呼叫 `execve`，而且記憶體裡半把私鑰都沒有 | 多了一趟跨行程 IPC 序列化的延遲（通常 `< 1 ms`），以及管理 Worker 行程池的成本 |

---

## 動手做

- **難度**：進階
- **預估時間**：45 分鐘

這次實驗我們不用任何危險的攻擊腳本，完全靠官方 Node.js v24（V8 13.6+）內建的原生診斷旗標與 Docker 容器隔離參數，帶你親眼看一看 V8 物件的 `Map`、Elements Kind 單向升級、TurboFan 的猜測性最佳化與去最佳化（Deoptimization），並動手驗證標準 Node.js 的 V8 Sandbox 預設狀態與 `--jitless` 容器隔離。

### 步驟 1：檢查本地 Node.js 的 V8 建置安全旗標

打開終端機執行下面這行指令，看看你手上的 Node.js 執行時期有沒有開啟 V8 Sandbox（Ubercage）與指標壓縮（Pointer Compression）：

```bash
node -p "JSON.stringify({
  node: process.version,
  v8: process.versions.v8,
  v8_enable_sandbox: process.config.variables.v8_enable_sandbox,
  v8_enable_pointer_compression: process.config.variables.v8_enable_pointer_compression
}, null, 2)"
```

看一下印出來的數字：幾乎所有官方發行的 Node.js 都會顯示 `v8_enable_sandbox: 0` 與 `v8_enable_pointer_compression: 0`。這兩個 `0` 就是最直接的證據，告訴你標準 Node.js 行程內部並沒有 Ubercage 幫你兜底。

### 步驟 2：用 `--allow-natives-syntax` 與 `%DebugPrint` 觀察 Map 與 Elements Kind 轉移

接著我們打開 V8 的原生內部語法旗標，觀察同一個 `JSArray` 在依序推入浮點數與字串之後，它的 `Map` 位址、Elements Kind 以及底層後備陣列會發生什麼變化：

```bash
node --allow-natives-syntax -e '
const a = [1, 2, 3];
console.log("=== 階段 1：純小整數 ===");
%DebugPrint(a);

a.push(1.5);
console.log("=== 階段 2：推入浮點數後 ===");
%DebugPrint(a);

a.push("x");
console.log("=== 階段 3：推入字串後 ===");
%DebugPrint(a);
'
```

跑完之後，請從輸出畫面裡找出三個關鍵變化：
1. 看 `map` 那一行的位址跟括號裡的名稱，是不是一路從 `PACKED_SMI_ELEMENTS` 變成 `PACKED_DOUBLE_ELEMENTS`，最後變成 `PACKED_ELEMENTS`。
2. 看 `elements` 指向的後備陣列型別，怎麼從 `FixedArray[3]` 換成放原始浮點數的 `FixedDoubleArray`，最後又換回把浮點數包裝成 `<HeapNumber 1.0>` 物件指標的 `FixedArray`。
3. 看 `Map` 物件底下的 `transitions` 與 `back pointer` 欄位，確認 V8 是怎麼把這條單向升級路徑串起來的。

### 步驟 3：用 `--trace-opt` 與 `--trace-deopt` 觀察猜測性最佳化與 `wrong map` 退回

現在我們寫一個簡單的 `readWeight` 函式，先餵給它整數陣列並強迫 TurboFan 把它編譯成最佳化機器碼，接著突然傳一個浮點數陣列進去，看看 `CheckMaps` 防護節點會怎麼反應：

```bash
node --allow-natives-syntax --trace-opt --trace-deopt -e '
function readWeight(table, idx) {
  return table[idx] * 1.0;
}
const smiArr = [10, 20, 30, 40];
const dblArr = [1.5, 2.5, 3.5, 4.5];

%PrepareFunctionForOptimization(readWeight);
readWeight(smiArr, 0);
readWeight(smiArr, 1);
%OptimizeFunctionOnNextCall(readWeight);
console.log("最佳化後呼叫 (SMI):", readWeight(smiArr, 2));

// 傳入不同 ElementsKind 的陣列，打破 CheckMaps 猜測假設
console.log("型別改變後呼叫 (Double):", readWeight(dblArr, 2));
'
```

### 步驟 4：驗證 `--jitless` 與 OS 行程／seccomp 隔離（NexusPay 規則 Worker 模型）

最後我們模擬 NexusPay 的防禦架構：把不信任的規則腳本丟進一個獨立的 Worker 容器，同時加上 `--jitless` 關掉整個 JIT 管線，並拔掉網路、寫入權限與所有 Linux Capabilities：

```bash
# 1) 驗證 --jitless 模式確實停用 JIT 編譯（不會產生任何 TURBOFAN_JS / MAGLEV 編譯輸出）
node --allow-natives-syntax --trace-opt --jitless -e '
function rule(x) { return x > 10000; }
%PrepareFunctionForOptimization(rule);
rule(500);
%OptimizeFunctionOnNextCall(rule);
console.log("jitless result:", rule(15000));
'

# 2) 使用無網路、唯讀根檔案系統、零 Capabilities 與行程數上限的隔離容器執行規則運算
docker run --rm --network=none --read-only \
  --cap-drop=ALL --security-opt=no-new-privileges \
  --pids-limit=32 --memory=128m --cpus=0.5 \
  node:24-alpine node --jitless -e '
    const input = { amount: 15000, limit: 10000 };
    console.log(JSON.stringify({ allow: input.amount <= input.limit }));
  '
```

### 外部靶場對照檢查點（pwn.college）

跑完本地實驗後，如果你想在真實 Linux 環境下進一步測試作業系統沙箱與系統呼叫過濾，推薦到免費教學平台 **pwn.college** 的 **System Security / Sandboxing** 相關模組練習。你可以親手試試看怎麼用 `seccomp-bpf` 白名單把 `execve`、`socket` 與 `openat` 鎖死，體會一下為什麼就算語言層沙箱被突破，作業系統層的最後一道鐵門還是能把攻擊者困在原地。

---

### 參考解答

#### 1. 步驟 1 實測輸出與解析

在標準 Node.js `v24.22.3`（V8 `13.6.233.17-node.63`）上跑出來的結果如下：

```json
{
  "node": "v24.22.3",
  "v8": "13.6.233.17-node.63",
  "v8_enable_sandbox": 0,
  "v8_enable_pointer_compression": 0
}
```

看到 `v8_enable_sandbox: 0` 就代表這份官方 Node.js 二進位檔在編譯時**根本沒有啟用 Ubercage**。如果團隊直接把商戶腳本放在主 API 閘道行程裡面跑，一旦踩中執行時期的記憶體漏洞，主行程裡所有的 64 位元記憶體位址就會毫無遮攔地暴露出來。

#### 2. 步驟 2 `%DebugPrint` 的三個階段變化

在階段 1 裡，`map` 顯示為 `Map[32](PACKED_SMI_ELEMENTS)`，`elements` 則是 `FixedArray[3]`，裡面直接放著小整數 `1`、`2`、`3`。

到了階段 2 執行完 `a.push(1.5)` 後，`map` 換成了新的 `Map[32](PACKED_DOUBLE_ELEMENTS)`，而且 `elements` 被重新配置成 **`FixedDoubleArray`**。這時候槽位 `0..3` 存的不再是 Tagged Value，而是未封裝的 64 位元 `float64` 原始位元（`1`、`2`、`3`、`1.5`），多出來的預留空間則填上 `<the_hole>`。

等到階段 3 執行 `a.push("x")` 後，`map` 再次升級為 `Map[32](PACKED_ELEMENTS)`，`elements` 又換回 `FixedArray`。最關鍵的變化是：原本那幾個浮點數現在全都被迫單獨打包（Box）成堆積上的物件 `<HeapNumber 1.0>`、`<HeapNumber 1.5>`，陣列槽位裡改存指向它們的 Tagged Pointer，槽位 `4` 則存著 `<String[1]: #x>` 的指標。這清楚證明了 `FixedDoubleArray` 跟 `FixedArray` 在底層記憶體裡的格式完全不同。

#### 3. 步驟 3 `--trace-opt` 與 `--trace-deopt` 輸出解析

執行後終端機會印出類似下面的追蹤紀錄：

```text
[manually marking ... <JSFunction readWeight> for optimization to TURBOFAN_JS, ...]
[compiling method ... <JSFunction readWeight> (target TURBOFAN_JS), ...]
[completed compiling ... <JSFunction readWeight> (target TURBOFAN_JS) - took 0.834, 13.416, 0.209 ms]
最佳化後呼叫 (SMI): 30
[bailout (kind: deopt-eager, reason: wrong map): begin. deoptimizing ... <JSFunction readWeight>, ...]
型別改變後呼叫 (Double): 3.5
```

注意看倒數第二行的 `kind: deopt-eager, reason: wrong map`。TurboFan 在編譯 `readWeight` 的時候，看過前面兩次 `smiArr` 的紀錄，就大膽假設傳進來的 `table` 永遠都會是 `PACKED_SMI_ELEMENTS` 的那個 `Map`。所以當最後一行突然傳進 `PACKED_DOUBLE_ELEMENTS` 的 `dblArr` 時，機器碼開頭的 `CheckMaps` 防護節點馬上發現 `Map` 對不上，立刻觸發 `deopt-eager` 退回直譯器，避免把 `FixedDoubleArray` 裡面的 `float64` 原始位元當成 Smi 整數來讀。反過來說，如果編譯器因為 Bug 漏放或誤刪了這道檢查，類型混淆就發生了。

#### 4. 步驟 4 `--jitless` 與容器隔離驗證

第一段指令加上 `--jitless` 之後，就算我們硬是呼叫了 `%OptimizeFunctionOnNextCall(rule)`，畫面上也完全不會出現任何 `compiling method ... TURBOFAN_JS` 的訊息，證明整個 JIT 編譯管線已經被徹底關掉。

第二段 Docker 指令則透過 `--network=none`（拔掉所有對外網路介面）、`--read-only`（唯讀根檔案系統）、`--cap-drop=ALL`、`--pids-limit=32` 與 `--memory=128m`，把規則運算鎖在一個既沒有金鑰、也動不了宿主系統的極簡無狀態容器裡。

---

## 自我檢核

- **難度**：進階
- **預估時間**：20 分鐘

先別看底下的解答，試著動筆算算看下面 4 個問題：

1. **Tagged Pointer 與後備陣列混淆**：在開啟 32 位元指標壓縮的 V8 環境裡，小整數 `-15` 用 Smi 編碼，跟把 `-15.0` 包裝成 `<HeapNumber -15.0>` 的物件指標，它們在記憶體裡的最低位元（Bit 0）分別是什麼？為什麼如果 JIT 編譯器搞錯 `Map`，把 `PACKED_DOUBLE_ELEMENTS` 的 `FixedDoubleArray` 槽位當成 `PACKED_ELEMENTS` 的 `FixedArray` 槽位來讀寫，會直接打破記憶體安全？
2. **Range Analysis 與越界偏移實算**：假設有個函式要讀取長度為 `6` 的浮點數陣列 `buf[idx]`（後備陣列為 `FixedDoubleArray`，開頭檔頭固定 `8 bytes`，每個元素寬 `8 bytes`）。如果 TurboFan 的 Typer 誤判 `idx` 的靜態區間是 `[0, 5]`，但執行期傳入特殊輸入卻能讓 `idx` 變成 `7`，請問編譯時 `CheckBounds` 會不會被刪掉？寫入 `buf[7]` 時，相對於後備陣列起點 `elements_base` 的十六進位偏移量是多少？如果緊貼在 `buf` 後備陣列（總大小 `8 + 6 × 8 = 56 bytes = 0x38`）後面的是一個相鄰的 `JSArray`（`map` 在 `+0x38`、`properties` 在 `+0x3c`、`elements` 在 `+0x40`、`length` 在 `+0x44`），寫入 `buf[7]` 會直接蓋掉哪兩個欄位？
3. **Ubercage 位址解碼與 EPT 型別標籤**：沿用正文設定（`cage_base = 0x0000_2000_0000_0000`，Ubercage 大小 `1 TiB = 2^40` bytes）。如果攻擊者在籠內把某個 `ArrayBuffer` 的 64 位元 `SandboxedPtr` 欄位改成 `0xdead_beef_cafe_0000`，經過右移 `24` 位元解碼並加上 `cage_base` 之後，實際算出來的虛擬位址是多少？這個位址有沒有跳出 Ubercage 的範圍？另外，`ExternalPointerTable`（EPT）明明已經把真實 C++ 指標移到籠子外面了，為什麼每個表項還非得檢查 Type Tag 不可？
4. **NexusPay 架構審查**：為了省下管理獨立容器的麻煩，有同事提議直接在 NexusPay 的 Node.js 主 API 閘道行程裡面，用 `vm.runInNewContext(merchantRule, { tx })` 搭配啟動參數 `--jitless` 來跑商戶自訂規則，理由是「關掉 JIT 就沒有 JIT 漏洞了」。請指出這個做法的兩個致命破口。

---

### 參考解答

1. **Tagged Pointer 位元特徵與混淆風險**：
   - 在 32 位元指標壓縮下，所有 Smi 小整數都是左移 1 位元存放，所以最低位元（Bit 0）永遠是 **`0`**；而指向堆積物件 `<HeapNumber -15.0>` 的 Tagged Pointer，則是對齊位址加 1，最低位元永遠是 **`1`**。
   - `FixedDoubleArray` 裡面存的是完全沒加標籤的 64 位元 IEEE 754 `float64` 原始位元，這 64 個位元（包含最低位元要填 `0` 還是 `1`）完全可以由腳本裡的浮點數值自由控制。一旦引擎誤用 `PACKED_ELEMENTS`（`FixedArray`）的視角去讀寫它，就會把攻擊者湊出來的浮點數位元直接當成 `HeapObject` 記憶體指標去解參考（`fakeobj`），或是把原本不該外洩的真實物件位址當成普通浮點數讀出來（`addrof`）。

2. **Range Analysis 與越界偏移實算**：
   - **`CheckBounds` 會被刪掉**。因為陣列長度是 `6`，編譯器檢查靜態區間 `[0, 5]` 時發現 `idx.min >= 0`（`0 >= 0`）且 `idx.max < 6`（`5 < 6`）恆成立，在 Check Elimination 階段就會直接把邊界檢查拔掉。
   - **偏移量與命中欄位**：`FixedDoubleArray` 的元素從 `+0x08` 開始排。當執行期 `idx = 7` 時，寫入位址是 `elements_base + 0x08 + 7 × 8 = 8 + 56 = 64 bytes = +0x40`（一次 64 位元浮點數寫入會蓋過 `+0x40 .. +0x47` 共 8 bytes）。對照相鄰 `JSArray` 的佈局，這刀下去會剛好同時覆寫掉它的 **`elements` 指標**（`+0x40`，4 bytes）與 **`length` 長度**（`+0x44`，4 bytes）。

3. **Ubercage 位址解碼與 EPT Type Tag**：
   - **解碼計算**：先把 `0xdead_beef_cafe_0000` 右移 `24` 位元（也就是砍掉最後 6 個十六進位字元），得到 40 位元偏移量 `0x0000_00de_adbe_efca`；接著加上 `cage_base`（`0x0000_2000_0000_0000`），算出來是 **`0x0000_20de_adbe_efca`**。因為 Ubercage 的合法範圍是 `0x0000_2000_0000_0000` 到 `0x0000_20ff_ffff_ffff`，這個位址**依然乖乖待在 `1 TiB` 的籠子裡面**，根本摸不到籠外記憶體。
   - **為什麼 EPT 需要 Type Tag**：雖然真實指標放在籠外的表格裡，但籠子裡的 JS 物件還是握有 32 位元的索引號碼牌（Handle）。如果沒有 Type Tag，攻擊者只要在籠子裡把 A 物件（原本指到 C++ `TypeA`）的號碼牌改成 B 物件（指到 C++ `TypeB`）的號碼牌，宿主 C++ 程式碼查表拿回指標時就會把 `TypeB` 當成 `TypeA` 來呼叫，直接在籠子外面製造出全新的 C++ 類型混淆。

4. **主行程跑 `node:vm` + `--jitless` 的兩個致命破口**：
   - **破口一（`node:vm` 根本防不住原型鏈逃逸）**：要攻破 `node:vm` 完全不需要靠 JIT 漏洞。商戶腳本只要寫一行 `this.constructor.constructor("return process")()`，就能順著原型鏈直接拿回宿主行程的 `process` 物件，把環境變數裡的私鑰跟檔案系統讀光光。
   - **破口二（共用主行程位址空間與事件迴圈）**：把不可信腳本放在主 API 閘道行程裡，只要商戶寫一個 `while (true) {}` 死迴圈，整個 Node.js 單執行緒事件迴圈就會當場卡死，造成全站阻斷服務（DoS）；而且主行程記憶體裡放滿了其他租戶的敏感帳務資料，沒有拆到獨立的無狀態 OS Worker 行程並加上 `cgroups` 與 `seccomp-bpf`，就沒有真正的安全隔離。

---

## 延伸閱讀

- **V8 Official Blog — *The V8 Sandbox***（https://v8.dev/blog/sandbox）：V8 團隊親自詳述 Ubercage 的威脅模型、`1 TiB` 虛擬位址空間保留、`ExternalPointerTable` 與 `TrustedSpace` 的架構演進。
- **V8 Official Blog — *Elements kinds in V8* 與 *Pointer Compression in V8***（https://v8.dev/blog/elements-kinds 與 https://v8.dev/blog/pointer-compression）：深入了解 `PACKED_SMI_ELEMENTS`、`PACKED_DOUBLE_ELEMENTS` 的轉移階梯，以及 32 位元指標壓縮與 Tagged Pointer 的編碼細節。
- **V8 Official Blog — *Maglev — V8’s Fastest Optimizing JIT***（https://v8.dev/blog/maglev）：看懂 Maglev 怎麼卡在 Sparkplug 與 TurboFan 之間做 SSA 猜測性最佳化。
- **Node.js 官方文件 — *VM (executing JavaScript)* 與 *Security Best Practices***（https://nodejs.org/api/vm.html 與 https://nodejs.org/en/learn/getting-started/security-best-practices）：官方針對 `node:vm` 為何不能當作安全沙箱的明確警告，以及後端執行時期的權限收緊指南。
- **Google Project Zero Technical Blog**（https://googleprojectzero.blogspot.com/）：收錄多篇針對現代 JS 引擎 Range Analysis、Check Elimination 與沙箱邊界防護的實戰分析。
