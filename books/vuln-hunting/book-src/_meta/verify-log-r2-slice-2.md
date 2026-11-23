# P4 Round-2 Adjudication & Surgical-Fix Log — `slice-2` (Ch06–Ch10)

- **Reviewer Panel**: `codex:gpt-6.2-sol:medium` (`_meta/review-sol62-medium-cache/ch06..ch10.json`)
- **Adjudicator**: `p4-r2-2` (`gemini-4-argon-medium`)
- **Scope**:
  - `ch06-authorization-and-multitenancy.md`
  - `ch07-graphql-grpc-websocket.md`
  - `ch08-injection-families.md`
  - `ch09-file-parsers-and-xxe.md`
  - `ch10-browser-and-client-attacks.md`

---

## 1. `ch06-authorization-and-multitenancy.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| `### 1. 授權三元組與失效分類（API1 / API3 / API5）` vs 4-tuple formula `Policy(Subject, Action, Object, Context)` | `incorrect` | **Accepted (Genuine Defect)** | Updated H3 heading to `### 1. 授權四元組與失效分類（API1 / API3 / API5）` to match the 4-tuple definition. |
| `ValidationPipe` without `whitelist: true` (or DTO properties lacking `class-validator` decorators) retains extra fields | `incorrect` | **Accepted (Genuine Defect)** | Fixed condition logic: extra properties are retained when no runtime allowlist is active (e.g., `ValidationPipe` lacks `whitelist: true` and no explicit field mapping is used). Clarified that when `whitelist: true` IS enabled, undecorated properties are stripped (or rejected under `forbidNonWhitelisted: true`). |
| `req.path.startsWith('/v1/admin')` bypassed by case, trailing slash, or path normalization | `incorrect` | **Accepted (Genuine Defect)** | Removed the erroneous claim that appending a trailing slash defeats `startsWith('/v1/admin')`; clarified that bypasses stem from case-sensitivity mismatch (`/v1/Admin`), pre-routing path normalization (`/v1/public/../admin`), or trailing-slash prefix mismatch (`startsWith('/v1/admin/')` missing `/v1/admin`). |
| 80 endpoints across 12 Controllers "必定出現" missing Guard | `incorrect` | **Accepted (Overstatement Fix)** | Softened deterministic wording to `極易在新增或重構端點時出現忘記加 Guard 的預設放行空窗`. |
| Service layer "複合主鍵強制查詢" `(tenantId, accountId)` | `incorrect` | **Accepted (Terminology Precision)** | Updated to `租戶與資源複合條件強制查詢` (with optional composite PK / unique index at the table layer). |
| BFLA scan check phrased as "檢查是否未回傳 `403`" | `incorrect` | **Accepted (Precision Fix)** | Clarified that BFLA detection checks whether the restricted operation is not rejected (expected `403 Forbidden` without state change vs vulnerable `200 OK` with feeRate mutation). |
| Worked Example matrix completeness & R2 role description consistency (`feeRate = 0.025` scenario assumption) | `imprecise` | **Accepted (Consistency Polish)** | Explicitly labeled `feeRate = 0.025` as the scenario assumption, noted `platform_admin` alongside the 4×6 matrix, and aligned R2's role description (`查詢同租戶帳戶與匯出報表、修改帳戶 displayName 與設定 webhookUrl`) with E1/E2/E4. |
| Remaining `imprecise` items (closed-book OWASP 2019 history, PortSwigger lab metadata, general prose qualifiers) | `imprecise` | **Dismissed (Closed-Book / Pedantry)** | Verified accurate in domain fact and `_meta/landscape-2026-11.md`; no edit required. |

---

## 2. `ch07-graphql-grpc-websocket.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| GraphQL 5-level `b=4` × 20 Aliases: 20,480 / 27,280 result nodes vs 5,120 / 6,820 list-field Resolver evaluations & 2 ms query time | `incorrect` (×3) | **Accepted (Genuine Math/Model Distinction)** | Explicitly distinguished **materialized result object nodes** (`20 × 1,024 = 20,480` at level 5; `20 × 1,364 = 27,280` total across 5 levels, corresponding to `40.96 s` / `54.56 s` under a per-item lookup model) from **list-field Resolver evaluations per parent object** (`1 + 4 + 16 + 64 + 256 = 341` per alias → `5,120` at level 5 and `6,820` total across 20 aliases, corresponding to `10.24 s` / `13.64 s` at 2 ms per list query). Updated worked example, summary table, and Self-Check Answer #1 consistently. |
| ASCII diagram: `1. Reflection Service enabled? -> Leaks full .proto & RPCs` | `incorrect` | **Accepted (Precision Fix)** | Updated diagram line (preserving exact 69-char box width) to `1. Reflection Service enabled? -> Leaks service descriptors/RPCs`, matching the prose explanation of descriptors. |
| ASCII diagram: `Protobuf Wire Decoder (Tag-Length-Value Varint)` | `incorrect` | **Accepted (Protocol Precision Fix)** | Updated diagram line (preserving exact 69-char box width) to `Protobuf Wire Decoder (Field Key / Wire-Type Value & Varint)`, since Protobuf varints are tag + varint value without a length prefix. |
| WebSocket handshake Cookie attachment (`SameSite=Strict` / `Lax` wording) | `incorrect` | **Accepted (Genuine Protocol Edge Case)** | Clarified that browsers attach cookies matching the request's `Domain`, `Path`, `Secure`, expiry, and `SameSite` rules (e.g., `SameSite=None; Secure` for cross-site handshakes, and even `SameSite=Lax`/`Strict` shared cookies for same-site cross-origin subdomain handshakes). |
| Self-Check Answer #2 on Proto3 default zero value & unknown fields | `imprecise` | **Accepted (Precision Polish)** | Specified implicit-presence scalar fields (without `optional`) and unknown-field preservation during re-serialization. |
| Remaining `imprecise` items (closed-book PortSwigger lab titles, general qualifiers) | `imprecise` | **Dismissed (Closed-Book / Pedantry)** | No edit needed. |

---

## 3. `ch08-injection-families.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| "ORM 只保護了靜態欄位的值（Value）" | `incorrect` | **Accepted (Precision Fix)** | Rewrote as `ORM 的參數化機制只保護「透過參數綁定介面傳入的資料值（Value）」`, contrasting value binding against dynamic identifiers (`ORDER BY`, column/table names) and raw SQL string concatenation. |
| Worked Example Binary Search: "以 4-bit 整數值 0..15 或 ASCII 碼折半" (4 steps) & Payload template using `ASCII(...) > <mid>` while trace compares `idx ∈ [0, 15]` | `incorrect` | **Accepted (Genuine Math/Code Mismatch)** | Unified the Worked Example on the 4-bit candidate index `idx ∈ [0, 15]` (`POSITION(SUBSTRING((SELECT token FROM api_tokens LIMIT 1), 1, 1) IN '0123456789abcdef') - 1 > <mid>`), matching the 4-step trace (`mid = 7, 11, 9, 10`) and `blind_sqli_bsearch.py`. |
| "False 分支 P99 延遲上界 = 45 ms / True 分支 P99 延遲上界 = 545 ms" | `incorrect` | **Accepted (Statistical Terminology Fix)** | Replaced "P99 延遲上界" with `False 分支基線 P99 延遲 = 45 ms` and `True 分支 P99 延遲（固定平移模型）= 500 + 45 = 545 ms`. |
| `curl <user_url>` Argument Injection with space-separated `-K /etc/passwd` or `-o /app/config.json` in a single `argv` element | `incorrect` | **Accepted (Genuine CLI Parsing Detail)** | Changed to single-argument forms `--config=/etc/passwd` and `-o/app/config.json` (or `--output=/app/config.json`) that require no whitespace splitting inside a single `argv` element. |
| Self-Check Q1 & Q2 (`ORDER BY $1` scalar wording & single `userInput` vs multi-option `tar` checkpoint exploit) | `imprecise` | **Accepted (Consistency Fix)** | Updated Q2 signature to `...userFiles` (array of filenames) and noted single-argument `--use-compress-program=...` alongside `--checkpoint=1` + `--checkpoint-action=exec=...`; refined Q1 explanation of bound data values in `ORDER BY $1`. |
| Remaining `imprecise` items (closed-book PortSwigger lab titles, general qualifiers) | `imprecise` | **Dismissed (Closed-Book / Pedantry)** | No edit needed. |

---

## 4. `ch09-file-parsers-and-xxe.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| OOB XXE two-stage external DTD loading phrased as strictly mandatory ("必須採用") from the two XML rules | `incorrect` | **Accepted (Precision Fix)** | Clarified in §9.3.2 and Self-Check Answer #2 that two-stage external (or local existing) DTD loading is the standard practical design used to satisfy both `SystemLiteral` and XML 1.0 §2.8 WFC: PEs in Internal Subset constraints. |
| "在非 PHP 環境則需改用 Error-Based XXE 或 FTP 協議外帶" | `incorrect` | **Accepted (Precision Fix)** | Replaced false dichotomy with environment-dependent evaluation of supported URI schemes and error-reporting behavior. |
| `resolveSafePath()` using `fs.existsSync(candidate) && fs.lstatSync(candidate).isSymbolicLink()` misses dangling symlinks; `openat + O_NOFOLLOW` note | `incorrect` / `imprecise` | **Accepted (Genuine Code Defect)** | Replaced `fs.existsSync` checks with `fs.lstatSync(..., { throwIfNoEntry: false })` for both ancestor traversal and the target entry so dangling symlinks are detected and rejected; clarified step-by-step directory descriptor `openat(..., O_NOFOLLOW)` or Linux `openat2(..., RESOLVE_BENEATH \| RESOLVE_NO_SYMLINKS)` for concurrent TOCTOU prevention. |
| Remaining `imprecise` items (illustrative CRC-32 labeled as example checksum, closed-book CVE/PortSwigger metadata) | `imprecise` | **Dismissed (Closed-Book / Already Labeled)** | CRC-32 is already explicitly labeled `範例校驗值`; no edit needed. |

---

## 5. `ch10-browser-and-client-attacks.md`

| Finding / Claim | Reviewer Verdict | Adjudication Decision | Surgical Action Taken |
|---|---|---|---|
| "不透明來源 `Opaque Origin` 不與任何來源相等" | `incorrect` | **Accepted (Spec Precision Fix)** | Clarified that each `Opaque Origin` is equal only to itself (sharing the same internal identity), unequal to any other origin, and serializes to `"null"`. |
| "一般 Cookie 的作用域不區分 `port`（除非加上 `__Host-` 前綴鎖定當前主機與 HTTPS）" | `incorrect` | **Accepted (Genuine Spec Fix)** | Corrected: neither standard cookies nor `__Host-` cookies isolate by `port` (`__Host-` enforces `Secure`, `Path=/`, and omission of `Domain` for host-only scoping, not port scoping). |
| Worked Example byte counts: `169 bytes` for two injected tags and `43 bytes` for `https://cdn.nexuspay-static.example/libs/` | `incorrect` (×2) | **Accepted (Genuine Arithmetic Error)** | Corrected tag byte counts to `85 bytes` + `107 bytes` = `192 bytes` (`193 bytes` with 1 LF) and CDN prefix length to `41 bytes`. |
| Lab A `nexuspay-client-lab.js`: `location=` inside `<iframe srcdoc>` is subframe navigation (subject to `default-src 'self'` / `frame-src`), while reference answer called it top-level navigation; demo JWT string & JSONP route removal | `incorrect` / `imprecise` | **Accepted (Genuine Code/CSP Consistency Fix)** | Updated Lab A payload to use `top.location` (with `slice(0, 96)` on the lab JSONP endpoint) so it genuinely performs top-level navigation bypassing `default-src 'self'`, noted that the stored value is a JWT-formatted demo string, and explicitly documented removing the legacy JSONP route as the fourth defense layer. |
| Self-Check Q1 answer on cross-port Cookie attachment (`:443` vs `:8443`) | `imprecise` | **Accepted (Precision Polish)** | Clarified that `:443` and `:8443` are Cross-Origin but Same-Site; cookies attach on top-level navigation, same-site subresource loads, or `fetch()` with `credentials: "include"` (whereas default `credentials: "same-origin"` `fetch()` omits credentials on cross-origin requests). |
| Remaining `imprecise` items (closed-book Chromium release history, PortSwigger lab titles) | `imprecise` | **Dismissed (Closed-Book / Pedantry)** | No edit needed. |
