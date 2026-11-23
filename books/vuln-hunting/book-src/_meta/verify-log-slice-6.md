# P4 Adjudication & Bridging Review Log — slice-6 (`ch31`, `ch32`, `ch34`, `ch36`, `ch37`)

## Bridging Review Summary (Fade-out Tier: Final Third `ch25–ch37`, Declared Bridge: `"none"`)

| Chapter | Declared Bridge | Detected Bridges | Isomorphism Score | Conversational / Everyday Analogies | Verdict | Notes |
|---|---|---|---|---|---|---|
| `ch31-real-world-oss-fuzzing.md` | `none` | none | 5 (exempt) | none | `pass` | Pure domain vocabulary (SanitizerCoverage, ASan, `FuzzedDataProvider`, `llvm-cov`, Stack Hash, OSS-Fuzz/ClusterFuzzLite). |
| `ch32-chaining-ai-and-0day-workflow.md` | `none` | none | 5 (exempt) | none | `pass` | Pure security domain terms (Capability Dependency Graph, Source-to-Sink, deterministic kill-switch, Hub Node). |
| `ch34-appsec-engineering-and-sdlc.md` | `none` | none | 5 (exempt) | none | `pass` | Replaced colloquial "打地鼠式修補" with domain term "單點被動修補與反覆回歸（Reactive Patching & Regression）"; zero everyday analogies. |
| `ch36-security-career-and-interviews.md` | `none` | none | 5 (exempt) | none | `pass` | Pure security engineering, threat modeling, and career assessment terminology. |
| `ch37-certifications-and-proof-of-work.md` | `none` | none | 5 (exempt) | none | `pass` | Pure security certification, signal-theory, and Proof-of-Work evaluation terminology. |

---

## Adjudication Log Entries

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: 只要其中任何一個第三方 JSON、壓縮或 TLS 解析套件沒經過持續模糊測試驗證，供應商程式碼就會變成整個服務最脆弱的信任破口；「沒有已知 CVE」往往只代表「還沒有人把模糊測試引擎接上去」；只要被挖出一個堆積越界寫入或 UAF，攻擊者就能利用同一份 PoC 同時攻擊成千上萬套未修補的線上服務。
book value: Over-absolute causal assertions equating absence of fuzzing/CVEs or single memory bugs with universal exploitability across all downstream deployments.  verifier value: Qualify by input reachability, configuration, and verification gap.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Missing continuous fuzzing indicates a verification gap on reachable parsing surfaces, not automatically the single most vulnerable point or identical exploitability across every downstream deployment.
tiebreak: n/a
action: Qualified statements in intro, `## 從你已知的出發`, and `### 攻擊者目標與實質影響` to bound claims by untrusted input reachability, configuration, and verification gaps.

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: 建置隔離與靜態鏈結：把外部函式庫的動態相依（`.so` / `.dylib`）改造成全靜態插樁二進位檔；`-fsanitize=fuzzer-no-link`——這個旗標只插入 SanitizerCoverage 邊緣探針與 Sanitizer 檢查，不連結 `main()`；過重環境初始化會讓吞吐量跌破 `10 exec/s`。
book value: Stated static linking alone adds probes and attributed ASan/UBSan checks to `-fsanitize=fuzzer-no-link`.  verifier value: Target libraries must be recompiled from source with instrumentation and statically linked; `-fsanitize=fuzzer-no-link` adds fuzzing coverage instrumentation without linking the fuzzer engine `main()`, while ASan/UBSan are enabled by their respective flags; `10 exec/s` corresponds to an example 100 ms per-iteration initialization cost.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Relinking an uninstrumented binary statically does not add probes; `-fsanitize=fuzzer-no-link` only provides fuzzer coverage/cmp instrumentation without `main()`.
tiebreak: n/a
action: Clarified source recompilation with instrumentation + static archive linking, separated `-fsanitize=fuzzer-no-link` from `-fsanitize=address,undefined`, and added the explicit 100 ms per-execution calculation for `10 exec/s`.

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: 由於 `FuzzedDataProvider` 遵循一致的消費順序（部分整數從緩衝區尾端切取、變長字串從前端切取），模糊器的覆蓋率引導突變依然能穩定保留有效參數前綴；若 Harness 解析成功後就直接 `free()` 結束，整條序列化與邊界檢查路徑覆蓋率永遠是 `0%`。
book value: Claimed `FuzzedDataProvider` guarantees unchanging parameter prefixes across mutations and that all boundary-check coverage is 0% without serialization calls.  verifier value: `FuzzedDataProvider` consumes integrals from the tail and remaining bytes from the front deterministically per input; omitting write calls leaves write-exclusive code paths at 0% coverage.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `ConsumeIntegral` pulls from the tail of the buffer in LLVM's implementation, which also conflicted with the lab text saying flags were taken from the front.
tiebreak: n/a
action: Aligned prose and lab description with LLVM `FuzzedDataProvider` tail-integral / front-payload consumption semantics and scoped `0%` coverage to serializer-exclusive code paths.

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: libFuzzer 傳給 Harness 的 `const uint8_t *data` 是一個緊密貼合 `size` 邊界的獨立分配區塊（後方緊鄰 ASan 紅區 Redzone），哪怕只多讀 1 byte 就會立刻被 ASan 攔截；真正的資源耗盡漏洞必須是「極小輸入（如幾 KB）就能觸發級數級記憶體暴增或無限迴圈」；20 exec/s 下每次配置與釋放就消耗數百毫秒。
book value: Over-stated unconditional 1-byte ASan interception, required exponential memory growth or infinite loops for DoS, and paired 20 exec/s (50 ms average) with hundreds of milliseconds on every execution.  verifier value: ASan interception requires instrumented code reading past `[data, data+size)` into the heap redzone; quadratic time/CPU amplification within allowed input bounds also constitutes DoS; 20 exec/s equals 50 ms average per execution (with multi-hundred-ms spikes on large inputs).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — 20 exec/s is 50 ms/exec on average; quadratic parsing is already cited earlier in the chapter as a valid DoS vector.
tiebreak: n/a
action: Refined ASan redzone condition to instrumented code, included quadratic amplification in DoS criteria, and reconciled `20 exec/s` (`50 ms` average) with large-sample latency spikes.

## [2026-11-21] ch31-real-world-oss-fuzzing.md — fixed
claim: 動手做與自我檢核：`git clone` 未鎖定 `0.10.0` tag；`corpus_p2` 未寫入小型合法種子步驟；正文稱呼叫 `yyjson_val_write` 但程式碼呼叫 `yyjson_write_opts`；`harness/` 與 `.clusterfuzzlite/build.sh` 的 `fuzz/` 路徑不一致；字典插入變異幾毫秒 100% 穿透分支；`afl-tmin` 或 `-runs=1` 收斂多輸入狀態序列。
book value: Unpinned `git clone`, missing seed creation command, `yyjson_val_write` name mismatch, `harness/` vs `fuzz/` path mismatch in ClusterFuzzLite script, and imprecise sequence-minimization instructions.  verifier value: Pin `--branch 0.10.0`, create `corpus_p2/seed0.bin`, match `yyjson_write_opts` / `yyjson_doc_mut_copy` / `yyjson_mut_write_opts`, align `harness/` paths in `build.sh` and `cflite_pr.yml`, and describe sequence recording + binary-search prefix reduction for cross-iteration state pollution.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — All six items in the lab and self-check solutions were genuine consistency defects.
tiebreak: n/a
action: Added `--branch 0.10.0`, added `printf ... > corpus_p2/seed0.bin`, updated function names to `yyjson_write_opts`, aligned `harness/` paths across `build.sh` and `cflite_pr.yml`, and fixed Self-Check #2 and #4 explanations.

## [2026-11-21] ch32-chaining-ai-and-0day-workflow.md — fixed
claim: 若缺乏利用鏈思維，這四份各自不起眼的發現會被丟進低優先級待辦清單；兩段原語必須共用同一個連線生命週期、同一個會話或可重複觸及的目標端點；這條路徑上的所有低危節點在風險評估上就會同步鎖定為最高終點等級。
book value: Counted 4 findings where 3 were listed; required shared connection/session/endpoint universally for context continuity; claimed every low-severity node's standalone rating is locked to the chain's terminal severity.  verifier value: 3 findings listed in that paragraph; context continuity requires prior output/state to remain valid in the next step's required execution context; remediation priority targets the validated chain while individual node base scores remain distinct.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Paragraph 3 listed 3 items (hostname leak, blind internal forwarding, unauthenticated internal API), and info-leak chaining across endpoints does not require sharing the same TCP connection or session.
tiebreak: n/a
action: Corrected "這四份" to "這三項", generalized Context Continuity and Temporal Window Compatibility rules, and distinguished whole-chain remediation priority from individual node CVSS ratings.

## [2026-11-21] ch32-chaining-ai-and-0day-workflow.md — fixed
claim: 沒有 `F1` 時，`F2` 必須盲猜兩千四百萬位址空間中的目標；淨超額資金損失 = 200,000 - 10,000 = 190,000 分 ($1,900.00，達初始餘額 20 倍)；在 < 1 ms 視窗內打破餘額 <= 10,000 分不變量。
book value: Stated `10.0.0.0/8` has 24 million addresses (actual: `2^24 = 16,777,216` ≈ 1,678 萬), labeled `190,000` as 20x of `10,000` (actual: `200,000` is 20x, `190,000` excess is 19x), and wrote `餘額 <= 10,000 分` instead of `累計出金 <= 初始可用餘額 10,000 分`.  verifier value: `10.0.0.0/8` is `16,777,216` addresses; total payout `200,000` is 20x initial balance while net excess `190,000` is 19x; invariant broken is cumulative payout `<= 10,000` cents under `< 1 ms` arrival jitter.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Pure arithmetic: `190,000 / 10,000 = 19` (while `200,000 / 10,000 = 20`), and `2^24 = 16,777,216` (1,678 萬, not 2,400 萬).
tiebreak: n/a
action: Fixed `20x` vs `19x` wording in the Worked Example, corrected `10.0.0.0/8` prose to `16,777,216` (約 1,678 萬), and updated F3 invariant notation to `累計出金 <= 10,000 分`.

## [2026-11-21] ch32-chaining-ai-and-0day-workflow.md — fixed
claim: CodeQL / Semgrep / AST 抽取所有 Source-to-Sink 路徑；防守方只要用最低成本切斷依賴圖上最關鍵的一條邊，整條 Critical 攻擊鏈就會瞬間坍塌成無害的孤立雜訊；在進入 `libnexus-parse` 配置前先確認 `len <= 65_536` 且改用飽和／檢查加法。
book value: Claimed static tools extract all paths, cutting one edge turns remaining nodes into harmless noise, and equated saturating addition with checked addition.  verifier value: Static queries extract candidate flows within modeled scope; cutting a required edge blocks paths depending on that edge while residual defects still require remediation; enforce `len <= 65,536` and `checked_add(8)` (max valid total `65,544 bytes`) plus buffer length verification.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Saturating addition clamps to `u32::MAX` instead of rejecting overflow, whereas `checked_add(8)` after `len <= 65_536` bounds total size to `65,544 bytes`.
tiebreak: n/a
action: Scoped static extraction in the pipeline diagram, refined chain-cutting defense claims, and specified `len <= 65_536` + `checked_add(8)` (`65,544 bytes` max) + buffer bounds verification.

## [2026-11-21] ch32-chaining-ai-and-0day-workflow.md — fixed
claim: 本實驗要求你在純本地離線隔離環境中完成流程，並以 `git clone --depth 300 <REPO_URL>` 與 `semgrep scan --config auto` 作為操作步驟；用 `rg` 在完整倉庫搜尋該 `target_fn` 的所有上游呼叫端；已固定限制 `payload_len <= 65_536` 且型別為 `usize`（64 位元下不可能溢位）。
book value: Paired offline environment requirement with live remote URLs/`--config auto`, claimed text search (`rg`) finds all callers, and claimed `payload_len <= 65_536` alone prevents `offset + payload_len` overflow for 64-bit `usize`.  verifier value: Separate online preparation/cloning from offline testing with local rules (`--config ./local-rules.yaml`); combine `rg` with LSP symbol resolution/manual inspection for indirect calls; bound both `offset` and `payload_len` (and verify `offset + payload_len <= buf.len()`) to rule out `usize` overflow.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — In 64-bit Rust, `offset + payload_len` can still overflow if `offset` is near `usize::MAX` unless `offset` is also bounded or `checked_add` is used.
tiebreak: n/a
action: Clarified preparation vs offline execution in the lab, replaced `--config auto` with local rule config, added LSP/call-graph verification alongside `rg`, bounded both `offset <= 1_048_576` and `payload_len <= 65_536` in the sample audit note, and refined Self-Check #1, #3, #4 answers.

## [2026-11-21] ch34-appsec-engineering-and-sdlc.md — fixed
claim: Worked Example ROI 與 Self-Check #2：高訊號規則每日觸發檢查的假警報率控制在 2%（以同等 100 次規則觸發基數或對應 100 PRs/天估算）；80 小時 ÷ 7.0 小時/天 ≈ 11.43 個工作天；立即將誤報率 `30%` 的通用啟發式規則從「PR 阻斷」降級為「非同步背景掃描」，停止每日消耗團隊 `7.5` 小時分診假警報。
book value: Mixed alert count and PR count denominators, omitted net break-even after amortizing the 4 hr/month maintenance cost, and implied moving alerts to async scanning makes the 7.5 hours of triage disappear without filtering.  verifier value: Pin Scenario B denominator to 100 alerts/day at 2% false-positive rate for PR-stage comparison, report both gross break-even (`11.43` days) and net break-even after `0.2 hr/day` maintenance (`80 / 6.8 ≈ 11.76` workdays), and note that async background scanning must prune/filter noisy rules rather than shifting 7.5 hr/day unchanged to AppSec.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `80 / (7.0 - 4/20) = 80 / 6.8 = 11.76` workdays, and shifting unfiltered alerts from PR to background only changes who triages them unless noisy rules are disabled/filtered.
tiebreak: n/a
action: Clarified the 100-alert baseline denominator in Scenario B, added both gross (`11.43` days) and net (`11.76` days) break-even figures, and updated Self-Check #2 to specify pruning/filtering noisy rules in async mode.

## [2026-11-21] ch34-appsec-engineering-and-sdlc.md — fixed
claim: 可達性分析與 SLA 決策（正文、SLA 表與自我檢核第 3 題）：唯有「生產環境可達」且「具備實戰利用機率（EPSS `≥ 0.1` 或列入 KEV）」才觸發 24 小時或 7 天 SLA；漏洞 A（`CVSS 9.1`, `EPSS 0.42`, `devDependencies`）直接排入常規維護；漏洞 B（`CVSS 7.8`, `EPSS 0.18`）啟動 7 天或 24 小時 SLA。
book value: Made production reachability a prerequisite before triggering immediate triage on `EPSS >= 0.1` / KEV, creating a literal conflict with the base-numbers table and the chapter's own SLA table on Vulnerability A.  verifier value: Per `_meta/running-examples.md`, `EPSS >= 0.1` or CISA KEV triggers immediate action/triage (`立即處置`); during immediate triage, verify production and build/CI exposure—if confirmed unreachable in production image and unexposed in CI/build, document the non-reachability exception to downgrade to routine maintenance; for Vulnerability B (`CVSS 7.8`, `EPSS 0.18`, reachable), trigger immediate action with a `7 天` High SLA (or `24 小時` only if confirmed to meet Critical criteria).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Reconciling `EPSS >= 0.1` immediate triage with reachability verification and documented non-exposure downgrade makes the chapter 100% consistent with `_meta/running-examples.md`.
tiebreak: n/a
action: Updated the SCA reachability section, the SLA governance table, and Self-Check #3 answer so `EPSS >= 0.1` / KEV always triggers immediate triage first, followed by reachability/build-exposure verification and either `24 小時` (Critical), `7 天` (High), or documented non-exposure exception downgrade.

## [2026-11-21] ch34-appsec-engineering-and-sdlc.md — fixed
claim: 動手做參考解答：`safeFetch(rawUrl, options)` 與 `safeHttpGet(rawUrl)` 命名與埠號檢查不一致、IPv6 正規化不完整；`TenantDbClient` 使用兩次獨立 `this.pool.query` 呼叫 `set_config(..., true)` 與查詢，在自動提交與連線池下無法保證同一交易與同一連線；Semgrep 規則未涵蓋匯入語句。
book value: `safeHttpGet` lacked `80`/`443` port enforcement and hex IPv4-mapped IPv6 handling; `TenantDbClient` ran `set_config(..., true)` outside an explicit `BEGIN...COMMIT` transaction on a checked-out client; `.semgrep/paved-road.yaml` only matched calls.  verifier value: Implement `safeFetch(rawUrl, options)` (with `safeHttpGet` alias), enforce standard ports `80`/`443`, normalize IPv6 (including hex `::ffff:0:0/96`), check out a single client via `pool.connect()` and wrap `set_config(..., true)` + query in `BEGIN ... COMMIT` / `ROLLBACK`, and add import patterns to `.semgrep/paved-road.yaml`.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — In PostgreSQL, `set_config(setting, value, true)` (`is_local = true`) takes effect only for the current transaction; calling `pool.query` twice in autocommit mode loses the setting immediately and may even hit two different connections.
tiebreak: n/a
action: Rewrote `safe-http.ts`, `tenant-db.ts`, `.semgrep/paved-road.yaml`, and the `tsx` test assertions to enforce ports `80`/`443`, normalize IPv6 addresses, execute `BEGIN` + `set_config` + query + `COMMIT` on a single checked-out client, and test the exact SQL transaction sequence.

## [2026-11-21] ch36-security-career-and-interviews.md — fixed
claim: Worked Example（45 分鐘 NexusPay 白板面試）與任務二解答：導入 Paved Road 資料庫封裝層強制注入 `req.auth.tenant_id` 即可消滅 BOLA；非同步巡檢「總儲值 - 總提領 != 當前餘額」；解析器子行程收到 `SIGSEGV` 或單次配置失敗（`len > 65,536`）保留崩潰樣本；監控 Worker 對私網 DNS/TCP 連線嘗試任何一次觸發即視為高確定性入侵指標；攻擊鏈 3 缺少 CSV/報表公式注入之輸出層防禦。
book value: Equated tenant scoping alone with full BOLA prevention (ignoring intra-tenant object authorization), omitted initial balance (`10,000` cents) from the ledger reconciliation equation, conflated pre-allocation length rejection (`len > 65,536`) with allocator failure/crash, and omitted CSV formula neutralization in Task 2's defense section.  verifier value: Combine tenant scoping with object-level authorization checks; reconcile `期初餘額 + 已入帳淨變動 (總儲值 - 總提領) == 當前餘額`; monitor oversized-input rejections, allocation failures, and crash signals separately; treat private-IP connection attempts as high-priority investigation signals; add CSV formula prefix neutralization (`=`, `+`, `-`, `@`).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Since NexusPay test accounts start with an initial balance of `10,000` cents, `總儲值 - 總提領 != 當前餘額` would false-alarm before any transaction unless initial balance (`期初餘額`) is included.
tiebreak: n/a
action: Updated the 45-minute Whiteboard Worked Example and Task 2 reference solution to include object-level authorization alongside `tenant_id`, include `期初餘額` in ledger reconciliation, separate length-rejection metrics from crash sample collection, and include CSV formula neutralization.

## [2026-11-21] ch36-security-career-and-interviews.md — fixed
claim: 動手做預估時間為 60 分鐘，任務一標為 20 分鐘，任務二標為「45 分鐘 NexusPay 白板 Threat Modeling 計時模擬（40 分鐘）」；自我檢核第 4 題將已指定為可跨租戶利用的 P0（24 小時 SLA）允許以 Risk Acceptance 壓定 7 天內根治期限。
book value: Header total `60 分鐘` and Task 2 header `(40 分鐘)` conflicted with the 45-minute timer (`5 + 15 + 15 + 10 = 45` min, total `20 + 45 = 65` min); Self-Check #4 allowed deferring an active cross-tenant P0 to a 7-day SLA.  verifier value: Set Task 2 to `45 分鐘` and total lab time to `65 分鐘`; in Self-Check #4, enforce the `24 小時` Critical SLA for P0 cross-tenant vulnerabilities (requiring immediate mitigation/isolation within 24 hours rather than deferring an unmitigated P0 for 7 days).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `5 + 15 + 15 + 10 = 45` minutes plus Task 1's `20` minutes equals `65` minutes; and per `_meta/running-examples.md`, Critical (P0) vulnerabilities have a mandatory `24 小時` SLA.
tiebreak: n/a
action: Fixed Task 2 duration to `45 分鐘` and total lab duration to `65 分鐘`, updated Self-Check #4 answer to uphold the `24 小時` Critical SLA, and marked resume/interview metrics and career weight tables as illustrative models.

## [2026-11-21] ch37-certifications-and-proof-of-work.md — fixed
claim: 軸線一標題「24–72 小時實戰上機考 vs. 選擇題背誦考」與表內 BSCP（4 小時）、CKS（2 小時）、CPTS（10 天 = 240 小時）時長不符；第 1 層與開頭對 GHSA/NVD 編號與 Proof of Work 的描述過度絕對；Worked Example 中 Portfolio C「單位訊號成本：極低（僅為 Portfolio A 的 6.8%，Portfolio B 的 34.2%），技術說服力最高」。
book value: Heading said `24–72 小時` while table listed `2h` to `10d`; `598 / 8,700 = 6.8736%` was truncated to `6.8%` instead of rounded to `6.9%` and labeled "單位訊號成本" when it is the cash cost ratio (and C tied with D at `9.5/10` on tech confidence).  verifier value: Change heading to `限時實戰上機考（2 小時至 10 天）vs. 選擇題與混合題型考`; clarify that GHSA/CVE numbers and PoW links must be verified for discoverer credit, root cause, and patch merger; report `598 / 8,700 ≈ 6.9%` as cash cost ratio and note C ties with D at `9.5/10` in the illustrative tech-product score.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `598 / 8700 = 0.0687356...` which rounds to `6.9%`, and `598 / 1749 = 0.3419...` (`34.2%`), both of which are pure cash cost ratios.
tiebreak: n/a
action: Updated Axis 1 heading to `2 小時至 10 天`, added credit/root-cause/patch verification requirements to PoW Pyramid Layer 1–3, corrected `6.8%` to `6.9%` (`現金成本比較`), and noted C and D tie at `9.5/10` for tech-product technical confidence.

## [2026-11-21] ch37-certifications-and-proof-of-work.md — fixed
claim: 動手做與自我檢核：參考人物自費預算上限 `$800` USD，已花 `$598` USD 後建議評估補考 AWS Security Specialty（`$300` USD，合計 `$898` USD 超支 `$98` USD）；自我檢核第 3 題稱「傳入 10 MB 空字串」；自我檢核第 4 題稱補 OSCP（`$1,749` USD）或 CISSP（`$749` USD）即可同時打通 HR 濾網與技術關卡且為最低成本。
book value: Unexplained `$98` budget overrun (`$598 + $300 = $898 > $800`), self-contradictory `"10 MB 空字串"` (empty string has 0 length), and over-absolute claim that buying OSCP/CISSP guarantees passing technical rounds at minimum cost.  verifier value: State explicitly that adding the `$300` exam beyond the `$800` cap (`$202` remaining) requires `$98` additional budget, employer sponsorship, or existing Burp license savings; change `"10 MB 空字串"` to `"10 MB 空白字元（whitespace）"`; note OSCP exam-only option (`~$1,699`) and CISSP annual maintenance (`$135/yr`) and distinguish HR eligibility screening from technical evaluation.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `$598 + $300 = $898` exceeds `$800` by `$98`, and an empty string cannot be 10 MB.
tiebreak: n/a
action: Added explicit `$98` budget arithmetic in the 6-month blueprint, replaced `"10 MB 空字串"` with `"10 MB 空白字元（whitespace）"` and bounded the Self-DoS threat model in Self-Check #3, and refined Self-Check #4 to include exam-only/maintenance cost details and separate HR screening from technical evaluation.
