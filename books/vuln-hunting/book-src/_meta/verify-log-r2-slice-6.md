# Round-2 Tier-2 Adjudication Log — Slice 6 (Ch31, Ch32, Ch34, Ch36, Ch37)

- **Reviewer Panel**: `codex:gpt-6.2-sol:medium`
- **Adjudicator**: `p4-r2-6` (`gemini-4-argon-medium`)
- **Chapters Covered**:
  - `ch31-real-world-oss-fuzzing.md`
  - `ch32-chaining-ai-and-0day-workflow.md`
  - `ch34-appsec-engineering-and-sdlc.md`
  - `ch36-security-career-and-interviews.md`
  - `ch37-certifications-and-proof-of-work.md`

---

## 1. `ch31-real-world-oss-fuzzing.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | C/C++ 缺少語言級邊界檢查，任意指標偏移或整數溢位直接轉化為記憶體損毀 | `incorrect` | **Accepted** | 修正表格敘述為：C/C++ 原生指標與陣列操作通常缺少自動邊界檢查，錯誤偏移或整數溢位若影響後續配置大小、索引或拷貝長度，便可能造成記憶體損毀。 |
| 2 | 發生在未插樁函式庫內部的越界讀寫將因缺少編譯期檢查探針而漏檢 | `incorrect` | **Accepted** | 明確指出未插樁程式碼中的直接越界讀寫會因缺少編譯期探針而形成 ASan 檢測缺口（除非經由 ASan 攔截的標準函式或後續觸發其他可觀察錯誤，否則直接指令存取可能漏檢）。 |
| 3 | 在改寫建置腳本時，必須遵守三條硬性原則：強制靜態建置受測庫與關閉測試 | `incorrect` | **Accepted** | 釐清核心目的為確保受測庫與需一併驗證的核心相依元件以匹配的插樁與 Sanitizer 旗標編譯為靜態封存檔鏈入 Fuzzer（避免執行期誤載系統未插樁共用函式庫），並視建置需求關閉無關測試以縮短建置時間。 |
| 4 | `build.sh` 在容器建置期由基底環境執行 | `incorrect` | **Accepted** | 修正為在建立 Fuzzer 產物的容器執行階段（如執行 `build_fuzzers` 時）由基底環境呼叫，與後文 `build_image` / `build_fuzzers` 兩階段流程完全一致。 |
| 5 | 在啟用 ASan 的插樁建置下，該輸入緩衝區後方通常緊鄰 ASan 紅區，只要越過 `size` 多讀 1 byte 就會觸發 ASan 越界告警 | `incorrect` | **Accepted** | 明確區分 API 長度契約與 ASan 紅區配置：讀取 `size` 之外已超出 API 契約；在 libFuzzer 搭配 ASan 為單次輸入配置剛好 `size` bytes 獨立堆積緩衝區時，其尾端緊鄰 ASan 紅區，已插樁函式越過 `data + size` 踏入紅區即觸發告警。 |
| 6 | 放入小型合法種子至 `corpus_p2`（尾端附 4 bytes 供 `FuzzedDataProvider` 切分控制參數） | `incorrect` | **Accepted (Code Bug Fixed)** | `fuzz_advanced.cc` 依序消費 `uint16_t` (2B) + `uint8_t` (1B) + `bool` (1B) + `bool` (1B) 共 `5 bytes` 控制區。已將 `size < 4` 修正為 `size < 6`（5B 控制區 + 至少 1B 負載），並將 `seed0.bin` 尾端控制區補齊為 5 bytes（`\x01\x00\x01\x01\x00`），避免最後一次 `ConsumeBool()` 吃掉 JSON 結尾 `}`。 |
| 7 | 以 `MemorySanitizer`（MSan）或 ASan 檢查是否存在未初始化記憶體讀取，並透過二分法刪減前置輸入序列 | `incorrect` | **Accepted** | 區分 MSan（查核未初始化記憶體讀取）與 ASan（查核越界與記憶體生命週期違規）之職責，並註明在維持必要先後順序下逐步縮減前置輸入序列且於每次刪減後驗證崩潰重現。 |
| 8 | Phase 1 標題「往返序列化」、`.github/workflows/cflite_pr.yml` 缺少 `checkout`、6-byte 盲猜年數四捨五入精度 | `imprecise` | **Accepted (Refined)** | 將 Phase 1 標題精確化為「解析後序列化寫出」；於 `cflite_pr.yml` 補上 `actions/checkout@v4`；於自我檢核第 2 題補充有放回 `1,785.10 年` 與不放回 `(2^48 + 1) / 2` 約 `892.55 年`（四捨五入約 `893 年`）之精確推導。其餘純封閉式外部背景挑剔予以駁回。 |

---

## 2. `ch32-chaining-ai-and-0day-workflow.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | 嘗試次數: `16,777,216 -> 1` | `incorrect` | **Accepted** | 明確標註 `16,777,216` 為 `10.0.0.0/8` 網段的 IPv4 候選位址數（`10.0.0.0/8 候選 IP: 16,777,216 -> 1`），F1 同時揭露確切內網 IP、埠號與兩條內部路徑，消除目標位址盲猜，並將攻擊圖起點明確標為「持有低權限商戶帳號之外部攻擊者」。 |
| 2 | 只要順著邊界轉移，就能在 `20` 次併發內把 `$100.00` 帳戶變現出 `$2,000.00`（超額損失 `$1,900.00`） | `incorrect` | **Accepted** | 明確限定在該內部端點未加原子鎖與資料庫非負餘額約束的競爭情境下，單輪 `20` 次併發全部成功提交時的總出金上界為 `$2,000.00`（淨超額損失上界 `$1,900.00`）。 |
| 3 | 可搭配 `git log -n 1 --tail` 確認 `--depth 300` 已完整涵蓋 90 天區間 | `incorrect` | **Accepted (CLI Fix)** | `git log` 無 `--tail` 旗標。已修正為使用 `git clone --shallow-since="90 days ago"` 或以 `git log --reverse -n 1 --format="%h %ci"` 確認本地最舊提交時間早於 90 天前（若截斷則用 `git fetch --shallow-since="90 days ago"` 補齊）。 |
| 4 | `P_i` 輸出狀態補齊 `P_j` 前置條件與 Nginx `30 s` / Node.js `5 s` 逾時階段區分 | `imprecise` | **Accepted (Refined)** | 補充下游節點可由單一或多個前序節點加初始環境共同滿足，並明確區分上游讀取間隔逾時（Nginx `proxy_read_timeout = 30 s`）與後端持久連線回應後閒置逾時（Node.js `keepAliveTimeout = 5 s`）。其餘純語氣與封閉式史料挑剔予以駁回。 |

---

## 3. `ch34-appsec-engineering-and-sdlc.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | 強制從已驗證的請求上下文取得 `tenantId`，自動執行 `SET LOCAL app.current_tenant_id = $1` | `incorrect` | **Accepted** | 對齊正文、步驟說明與 `tenant-db.ts` 參考實作：明確說明呼叫端須傳入經認證與租戶授權中介層產出的 `AuthContext`（校驗 `tenantId` 非空），並於同一連線交易內執行參數化的 `SELECT set_config('app.current_tenant_id', $1, true)`（等效於交易作用域內的 `SET LOCAL`）。 |
| 2 | 僅允許 `https:`（或明確核准的 `http:`）與標準埠號 `80`/`443` | `incorrect` | **Accepted (Code & Prose Aligned)** | 於 `safe-http.ts` 強制檢查協定與其標準埠號之一對一配對（`https:` 必須為 `443`、`http:` 必須為 `80`），並使正文與程式碼一致。 |
| 3 | 參考實作可在 Node.js 22 執行，並以自訂 `lookup` 強制回傳已驗證 IP | `incorrect` | **Accepted (Code Bug Fixed)** | Node.js 22 在 `autoSelectFamily` / `{ all: true }` 模式下呼叫自訂 `lookup` 時要求回傳 `[{ address, family }]` 陣列。已更新 `safe-http.ts` 的 `lookup` 回呼，同時支援 `opts.all === true` 陣列格式與單一位址格式。 |
| 4 | 嚴重（Critical）表列條件包含「EPSS ≥ 0.1 / 列入 CISA KEV 觸發立即處置且確認具實質可達曝險」，與高危列 `7 天` SLA 條件重疊 | `incorrect` | **Accepted** | 重構風險分級表：明確由 CVSS v4.0 與實質業務破壞面決定嚴重度與修復 SLA（嚴重 `24 小時`、高危 `7 天`），而 `EPSS ≥ 0.1` 或列入 `CISA KEV` 則作為**立即啟動分診與處置**的觸發條件，消除漏洞 B（CVSS 7.8、EPSS 0.18）在表格中同時命中 `24 小時` 與 `7 天` 的邏輯衝突。 |
| 5 | `nexuspay-no-raw-pool-query` 禁止在 `src/services/` 下直接呼叫 `pool.query(...)` | `incorrect` | **Accepted** | 釐清 Semgrep 規則 `$POOL.query(...)` 會攔截 `src/services/` 下對連線池或用戶端物件的 `.query(...)` 呼叫，而合規的 `TenantDbClient` 僅暴露 `queryScoped(...)`，使規則語義與說明完全一致。 |
| 6 | 自我檢核第 1 題：DNS Rebinding 前置條件與 WHATWG `new URL()` 對十六進位 IPv4 之正規化行為 | `incorrect` | **Accepted** | 修正自我檢核第 1 題參考解答：(1) 指出僅檢查 `URL.hostname` 字串連一般自訂網域指向私網 IP 都無法攔截，且即便加上預檢也會被 DNS Rebinding 擊穿；(2) 指出 WHATWG `new URL()` 會將 `http://0x7f000001/` 正規化為 `127.0.0.1`，但對於 IPv6 迴路／映射位址（`[::1]`、`[::ffff:127.0.0.1]` 正規化為 `[::ffff:7f00:1]`）以及未列入三前綴的 `169.254.169.254`（含十進位 `2852039166`）、`172.16.0.0/12`、`0.0.0.0/8` 仍會直接放行。 |

---

## 4. `ch36-security-career-and-interviews.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | 任務二參考解答 SLA 分流：將「CVSS 高分 + EPSS ≥ 0.1」直接等同於 24 小時 SLA 並無條件輪換雲端憑證，將未利用的報表欄位跳脫缺陷直接歸為 7 天高危 SLA | `incorrect` | **Accepted** | 修正任務二 SLA 分流說明：先依前置條件與實質影響以 CVSS v4.0 定級，凡搭配 `EPSS ≥ 0.1` 或列入 `CISA KEV` 即觸發立即處置；確認達**嚴重**（Critical）等級者啟動 `24 小時` 嚴重 SLA 並於確認雲端憑證有曝險證據時撤銷與輪換憑證；經評定屬**高危**（High）等級者則納入 `7 天` 高危 SLA 修補並補上 CI 測試。 |
| 2 | 反向代理 `proxy_read_timeout = 30 s` 與後端 `keepAliveTimeout = 5 s` 不匹配時連線池重用問題 | `imprecise` | **Accepted (Refined)** | 明確區分反向代理的上游讀取逾時（`proxy_read_timeout = 30 s`）與後端持久連線閒置逾時（`keepAliveTimeout = 5 s`），並指明連線重用關閉競爭源於代理上游連線池閒置期限與後端 `keepAliveTimeout` 不匹配。 |

---

## 5. `ch37-certifications-and-proof-of-work.md`

| # | Finding / Claim | Panel Verdict | Adjudication Decision | Surgical Fix Applied |
|---|---|---|---|---|
| 1 | 自費買 SANS 官方課現金成本極高；除非由雇主全額報帳，否則個人自費負擔遠高於 BSCP＋OSWE | `incorrect` | **Accepted** | 修正表格敘述：無補助自費購買 SANS 官方課時現金成本極高（`$8,700+` 為 BSCP＋OSWE 合計 `$2,347` 的 `3.7` 倍以上）；除非獲得雇主高額或全額補助（以 `$8,700` 下限計，補助須超過 `$6,353` 自付額才會低於無補助的 BSCP＋OSWE），否則個人自費負擔顯著偏高。 |
| 2 | 參考解答 6 個月藍圖：**Month 3–4（120h / $0）** 在固定每週 `12 小時` 下無法容納於 2 個月（約 8.67 週 = 104h）內 | `incorrect` | **Accepted (Math Fixed)** | 將 26 週（`26 週 × 12h/週 = 312 小時`）藍圖改以精確對齊 `12h/週` 的三段連續週次呈現：**Weeks 1–6（6 週共 72h / $598 USD：68h 實驗 + 4h BSCP 應試）**、**Weeks 7–16（10 週共 120h / $0）**、**Weeks 17–26（10 週共 120h / $0）**，三階段合計 `6 + 10 + 10 = 26 週`、`72 + 120 + 120 = 312 小時`。 |
| 3 | Portfolio A（90h 未列正式應試 3h）與 Portfolio D（180h 內 132h 訓練 + 47h 45m 考試僅剩 15 分鐘寫報告）工時細項 | `imprecise` | **Accepted (Math Refined)** | 於 Portfolio A 明列 `Index 製作、模擬考與正式應試（約 3h）共 90h`；於 Portfolio D 明列 `120h 訓練 + 47h 45m 應試 + 12h 15m 報告撰寫 = 180h`（加上 `60h` 作品共 `240h`）。 |

---

## 6. Verification Gate Results

- `lint_book.py`: 0 errors, 0 warnings across all 5 chapters in `slice-6`.
- `check_diagrams.py`: 0 errors, 0 warnings across all 5 chapters in `slice-6`.
