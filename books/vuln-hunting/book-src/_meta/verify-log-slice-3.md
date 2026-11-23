# P4 Adjudication & Bridging Review Log — Slice 3 (Ch11–Ch15)

## [2026-11-21] ch11-ssrf-parsers-and-cache.md — fixed
claim: Node.js `url.parse()` vs WHATWG `new URL()` parser differentials (`\@` userinfo vs octal/DWORD IPv4 canonicalization), control-character stripping, DNS Rebinding TOCTOU timeline & outbound timeout vs Nginx `proxy_read_timeout`, Web Cache Poisoning `Vary` headers & Cache Buster prerequisites, Web Cache Deception 3 path confusion categories & `%2f` dot-segment normalization, `net.BlockList` CIDR validation, and Nginx dynamic route cache disabling.
book value: stated `url.parse()` treats `127.0.0.1:8080\` as userinfo; listed "4" path confusion categories for 3 items; used string prefix matching `startsWith('fe80')` for IPv6 CIDR; left `proxy_cache` enabled on `location /` in patched Nginx config; missing `### 攻擊者目標與實質影響` H3 heading under `## 機制與推導`.  verifier value: Node.js `url.parse()` normalizes `\` before splitting authority (whereas strict RFC 3986 parsers like `urllib.parse.urlsplit` treat `127.0.0.1:8080\` as userinfo, and `url.parse()` leaves octal `0177.0.0.1` / DWORD `2130706433` unnormalized while WHATWG `new URL()` canonicalizes them to `127.0.0.1`); 3 path confusion categories; binary CIDR matching via `net.BlockList`; explicit `proxy_no_cache 1; proxy_cache_bypass 1;` on dynamic `location /`.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Empirically verified in Node.js 22 that `url.parse()` normalizes `\` to `/` but leaves `0177.0.0.1` and `2130706433` unnormalized, while `new URL()` canonicalizes them to `127.0.0.1` and strict RFC 3986 parsers (`urllib.parse.urlsplit`) parse `127.0.0.1:8080\` as userinfo; confirmed `net.BlockList` handles IPv4/IPv6 CIDR and IPv4-mapped IPv6 accurately.
tiebreak: n/a
action: Added mandatory `### 攻擊者目標與實質影響` H3 under `## 機制與推導`; distinguished RFC 3986 vs WHATWG `\@` splitting and Node.js `url.parse()` vs `new URL()` octal/DWORD IPv4 canonicalization across prose, worked example, Lab 1A, and Self-Check Q1/A1; refined DNS Rebinding timeline, outbound connect timeout vs `proxy_read_timeout = 30 s`, `Vary` header correspondence, 3-item Deception count and `%2f` dot-segment description; replaced prefix checks with `net.BlockList` CIDR validation; disabled shared caching on `location /` in patched Nginx snippet.

### Bridging Review — ch11-ssrf-parsers-and-cache.md
- `declared_bridge`: `CDN/Nginx 快取鍵設計 → Web Cache Poisoning 的 Unkeyed Input`（快取機制 2/3，前段）
- `detected_bridges`: `CDN/Nginx 快取鍵設計 → Web Cache Poisoning 的 Unkeyed Input`（明確標示橋接來源與目標、成立邊界、失效邊界）
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`

---

## [2026-11-21] ch12-race-conditions-and-logic.md — fixed
claim: HTTP/2 frame composition (`HEADERS` + optional `DATA`), Single-Packet `< 1 ms` arrival jitter vs Node.js async `await` interleaving, PostgreSQL `READ COMMITTED` vs `REPEATABLE READ` snapshot creation timing & write skew protection (`SERIALIZABLE` vs `SELECT ... FOR UPDATE`), external bank payout idempotency & Fencing Token scope, and withdrawal contract requirements.
book value: stated every HTTP request consists of `HEADERS` and `DATA` frames; stated all 19 remaining requests deterministically execute `SELECT` before `UPDATE` and receive `40001` under `REPEATABLE READ`; stated `SELECT ... FOR UPDATE` on a parent row alone prevents write skew under `REPEATABLE READ`.  verifier value: `DATA` frames are only present for requests with a body; snapshot under `REPEATABLE READ` is taken at the first non-transaction-control statement, and locking a parent row without updating it does not refresh an already-taken `REPEATABLE READ` snapshot (requires `SERIALIZABLE`, `READ COMMITTED` locking before read, or actual parent-row version update).  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Under PostgreSQL MVCC, `REPEATABLE READ` freezes the snapshot at the first query; `SELECT ... FOR UPDATE` on a parent row without modifying it does not refresh the transaction's snapshot for subsequent child-row reads.
tiebreak: n/a
action: Qualified HTTP/2 `HEADERS` + `DATA` frame statement for requests with bodies; refined `< 1 ms` arrival burst and Node.js async `await` query interleaving; clarified PostgreSQL `REPEATABLE READ` first-statement snapshot semantics and write-skew prevention options in both prose and Self-Check A2; specified external payout idempotency and parameter-bound idempotency key requirements.

### Bridging Review — ch12-race-conditions-and-logic.md
- `declared_bridge`: `資料庫 Isolation Level 與樂觀鎖 → TOCTOU 與單封包雙花攻擊`（DB 交易/不變量 3/3，前段）
- `detected_bridges`: `資料庫 Isolation Level 與樂觀鎖 → TOCTOU 與單封包雙花攻擊`（明確標示成立邊界與失效邊界）
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`

---

## [2026-11-21] ch13-deserialization-and-nodejs-runtime.md — fixed
claim: Prototype pollution property lookup scope (`isAdmin` vs `role`), `child_process.spawn` non-Node binary RCE gadget (`shell` + `BASH_ENV` or `shell: "node"` + `NODE_OPTIONS`), Java `ObjectInputStream` (`readObject`) & Python `pickle` (`__reduce__`) deserialization hooks, ReDoS `keepAliveTimeout = 5 s` vs `proxy_read_timeout = 30 s` impact analysis, UTF-8 byte length check (`Buffer.byteLength`), and `safeDeepMerge` null-handling bug (`typeof null === "object"`).
book value: conflated `Object.prototype.role = "admin"` with reading `user.isAdmin`; stated `shell = "/bin/sh"` alone turns `spawn("git", ["--version"])` environment variables into command execution; stated Java `ObjectInputStream` invokes standard constructors during deserialization; checked `input.length <= 128` for a 128-byte limit; did not check `target[key] === null` before recursing in `safeDeepMerge`.  verifier value: property lookup matches by key name; non-Node `spawn` gadget requires an interpreter-evaluated env var like `BASH_ENV` with `/bin/bash` or `shell = "node"` with `NODE_OPTIONS`; Java uses `readObject()`/`readResolve()` hooks while `pickle` executes the reconstruction callable described by `__reduce__`; UTF-8 byte limit requires `Buffer.byteLength(input, 'utf8') <= 128`; `safeDeepMerge` must guard against `target[key] === null` and `Array.isArray(target[key])`.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — `typeof null === "object"` in JS causes `safeDeepMerge` to pass `null` into the recursive call if `target[key]` was initialized to `null`; `Buffer.byteLength` is required for byte-level bounding on UTF-8 strings.
tiebreak: n/a
action: Fixed property lookup correspondence (`isAdmin` vs `role`); clarified non-Node `spawn` gadget pairs (`shell: "/bin/bash"` + `BASH_ENV` or `shell: "node"` + `NODE_OPTIONS`); corrected Java `ObjectInputStream` and Python `pickle` deserialization hook descriptions; clarified `keepAliveTimeout = 5 s` vs sequential queueing past Nginx `proxy_read_timeout = 30 s` in the ReDoS worked example; added `Buffer.byteLength` check and fixed `target[key] === null || Array.isArray(target[key])` in `safeDeepMerge`.

### Bridging Review — ch13-deserialization-and-nodejs-runtime.md
- `declared_bridge`: `none`（中段，直接以 JS Prototype 鏈與書內 Ch08 匯點模型推導）
- `detected_bridges`: []
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`

---

## [2026-11-21] ch14-waf-and-defense-bypass.md — fixed
claim: Worked Example JSON padding byte count (`len(payload_tail) = 64 bytes`, total `8,273 bytes`, 17-byte safety margin), `ProcessPartial` unclosed JSON assumption, HPP table API specificity & Self-Check Q2/A2 logic, `body-parser.json()` charset behavior (`415` on `ibm037`), `trust proxy = true` leftmost XFF selection, route-aligned rate-limit key normalization, and Lab verification/patch completeness (`verify_ch14.py` & `gateway.ts`).
book value: counted `len(payload_tail)` as `65 bytes` (`Total Content-Length = 8,274 bytes`, margin `16 bytes`); stated standard `body-parser` JSON middleware silently decodes `charset=ibm037`; stated `trust proxy = true` picks "最左側未受信任的位址"; combined XFF and path-case mutation in the same loop in `verify_ch14.py`; omitted UTF-8 check, query-preserving path normalization, and `/v1/auth/otp/verify` merchant rate limiter in `gateway.ts`.  verifier value: `len(',"__proto__":{"isAdmin":true},"sort":"id; SELECT pg_sleep(5)--"}') = 64 bytes`, total `8 + 8200 + 1 + 64 = 8,273 bytes`, margin `8200 - 8183 = 17 bytes`; `body-parser.json()` rejects `ibm037` with `415`; `trust proxy = true` trusts the entire chain and selects the leftmost XFF address; separate XFF and path-case tests in `verify_ch14.py` and complete `gateway.ts`.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — Direct byte count of `payload_tail` is `1 + 11 + 1 + 16 + 1 + 6 + 1 + 26 + 1 = 64 bytes`, making total length `8,273 bytes` and uninspected tail `81 bytes`.
tiebreak: n/a
action: Corrected `len(payload_tail) = 64 bytes`, `Total Content-Length = 8,273 bytes`, offset `8,209..8,272`, and 17-byte safety margin in Worked Example; clarified `ProcessPartial` signature-scanning assumption and downstream sink condition; refined HPP table and Self-Check Q2/A2; clarified `body-parser.json()` UTF enforcement vs permissive decoders; fixed `trust proxy = true` wording; updated `verify_ch14.py` to test baseline, XFF rotation, and path-case bypass independently; completed `gateway.ts` with UTF-8 check, query-safe pathname normalization, and `merchant_id` OTP rate limiting.

### Bridging Review — ch14-waf-and-defense-bypass.md
- `declared_bridge`: `none`（中段，承接 Ch03 解析分歧與 Ch11 快取層剖析 WAF/代理對抗）
- `detected_bridges`: []
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`

---

## [2026-11-21] ch15-applied-crypto-flaws.md — fixed
claim: PKCS#7 padding byte notation (`0x01`–`0x10`), AES-CBC Padding Oracle expected query count (`128.5` per byte / `2,056` exact vs `2,048` approximation, plus confirmation query) and byte-15 `0x02 0x02` disambiguation condition (`P'_i[14] = I_i[14] ^ C'_{i-1}[14] == 0x02`), AES-GCM CTR block counter indexing (`inc_32^j(J_0)`), Forbidden Attack conditions for recovering `H` and forging tags, `Math.random()` Z3 state recovery preconditions, KDF vs password stretching distinction (Argon2id/scrypt vs HKDF), and AEAD AAD unsealing + Double-HMAC verification in code.
book value: wrote `C_j = P_j ⊕ E_K(inc_32(J_0))` without block index `j`; attributed byte-15 `0x02 0x02` ambiguity to original plaintext ending in `0x02 0x02` even when `C'_{i-1}[14]` was zeroed; conflated low-entropy password stretching (Argon2id/scrypt) with HKDF domain separation; omitted `unsealSessionCookie` showing trusted AAD reconstruction and version policy enforcement.  verifier value: block `j` uses `inc_32^j(J_0)`; `0x02 0x02` ambiguity occurs when `P'_i[14] = I_i[14] ^ C'_{i-1}[14] == 0x02` so candidate `g_2 = I_i[15] ^ 0x02` forms valid 2-byte padding; exact uniform expectation is `128.5` trials/byte (`2,056`/block, `6,168`/3 blocks, approximated as `2,048` and `6,144`); Argon2id/scrypt stretch low-entropy passwords while HKDF derives domain-separated subkeys from high-entropy keys.  flagging families: codex:gpt-6.2-sol:low
arbiter: agrees=true conf=high — All algebraic and cryptographic refinements verified closed-book and consistent with `_meta/running-examples.md`.
tiebreak: n/a
action: Fixed CTR formula to `C_j = P_j ⊕ E_K(inc_32^j(J_0))`; clarified PKCS#7 notation (`0x01`–`0x10`), exact discrete expectation (`128.5`/byte = `2,056`/block alongside `2,048` approximation), and `P'_i[14] == 0x02` disambiguation algebra; refined Forbidden Attack conditions and NIST SP 800-38D `2^32` random-nonce collision bound (`≈ 2^{-33} < 2^{-32}`); separated Argon2id/scrypt password stretching from HKDF domain separation; added `unsealSessionCookie` with trusted `expectedTenantId` AAD reconstruction and `minAcceptedVersion` check.

### Bridging Review — ch15-applied-crypto-flaws.md
- `declared_bridge`: `none`（中段，直接以協定狀態機與位元組區塊推導密碼學實作破口）
- `detected_bridges`: []
- `isomorphism_score`: 5
- `conversational_phrases`: []
- `verdict`: `pass`
