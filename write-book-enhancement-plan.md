# write-book Skill — Enhancement Plan

**Date:** 2026-06-27
**Source:** 4 parallel read-only reviews of `.claude/skills/write-book/SKILL.md`
(lenses: usability, robustness, purity, grounding) + direct verification of the
referenced toolchain at `../tools/md-reader/`.
**Goal:** Make the skill a *pure, general* book engine that is also *executable
and correctly wired* to its real toolchain — without overfitting to one
author/topic/language/book.

All four reviewers returned `incorrect` for their lens. Findings converge on a
small number of load-bearing defects.

---

## A. Verified tool-grounding facts (evidence, not inference)

| Claim | Status | Evidence |
|---|---|---|
| `gate_book.py` crashes on every run | **CONFIRMED** | `gate_book.py:111` `lint_book.load_config(config_path)` (1 arg) vs `load_config(lang, lang_file, config_path)` (3 required) → `TypeError`. Also no `--lang`. |
| `verify_book.py` prompt is TLA+/zh-TW specific | **CONFIRMED** | `verify_prompt.md:2` "繁體中文 TLA+／形式化方法教科書"; lines 6-9 ask for reachable-state counts, □◇⇝/WF/SF, inductive Init⇒Inv, lassos. |
| Tier-2 panel is hardcoded, assumes Opus writer | **CONFIRMED** | `verify_book.py:46` `PANEL=[gpt-5.5, Gemini 3.5 Flash, Claude Sonnet 4.6]`; docstring "none of them the Opus-4.8 writer"; `--models` only subsets. |
| Tier-2 baseline read from `_meta/running-examples.md`/`maintenance.md`, not `outline.md` | **CONFIRMED** | `verify_book.py:90`. Neither file exists at P4 → empty baseline → cross-chapter numbers marked `unverifiable`. |
| Tier-2 is closed-book (no web/fact-check) | **CONFIRMED** | `verify_prompt.md:4` "從章節自身… 從零重算"; no web step. |
| Lint enforces skeleton only from the lang pack | **CONFIRMED** | `lint_book.skeleton_check` uses `cfg["skeleton_slots"]` (pack/`--config`), never style-guide/CLAUDE.md. CLAUDE.md skeleton (動手做) ≠ `zh-TW.json` slot (紙上推演). |
| Lint depth metric is CJK-only | **CONFIRMED** | `depth_unit_pattern = [一-鿿]`; copying to `en.json` → 0 units < 2500 → permanent `depth_floor` ERROR. |
| difficulty/time/worked-example are WARN, not ERROR | **CONFIRMED** | `lint_book.DEFAULT_CONFIG severity`; worked-example test = "a fenced block exists", not "real numbers". |

---

## B. Architecture (mirror the lint_book engine/pack design)

**Pure engine** (SKILL.md): the genre-neutral spine + contracts for swappable parts.
Spine = language-first calibrate → meta files → fan-out → two-tier gate → package.

**Swappable parts** (project/book-specific, never in the engine):
1. **Language pack** `lang/<code>.json` — skeleton slots, depth metric+thresholds, forbidden chars, vocab. *(exists)*
2. **Book profile / genre** *(new concept)* — instructional / narrative / reference / technical. Controls whether worked-examples, exercises, difficulty markers, labs, the bridging regime, and the landscape/maintenance (volatility) apparatus apply.
3. **Verifier prompt** `verify_prompt.md` *(new requirement)* — must match the book's topic + language, else Tier-2 verdicts are noise.
4. **Local config** *(formalized)* — canonical location, enumerated keys, machine-checkable signals.

---

## C. Critical (must fix)

### C1 — Add a blocking P4 gate; extend the P5 gate *(Robustness + Usability, convergent)*
P4 has no `GATE:` line; P5 gate checks only deliverable existence. A `FAIL`/`INCONCLUSIVE`
book ships as "done" — the most expensive step is advisory.
**Fix:** add P4 gate — "Tier-2 verdict PASS (not FAIL, not INCONCLUSIVE; resolve every WARN); on FAIL fix+re-run; on INCONCLUSIVE add panelists or escalate." Extend P5 gate to require Tier-1 clean **and** Tier-2 not FAIL/INCONCLUSIVE (or a user-approved waiver logged).

### C2 — Verifier prompt must be domain+language matched *(Grounding)*
The bundled `verify_prompt.md` is TLA+/zh-TW. Hard-gating P4 on it for any other topic
gates on noise.
**Fix (skill):** introduce a "verifier prompt template" concept mirroring the lang pack;
P1.5 confirms a topic+language-matched `verify_prompt.md` exists or authors one; otherwise
Tier-2 soft-degrades to a manual ≥2-family cross-model pass (never runs the TLA+ prompt).
**Tool-side (flag):** the shipped prompt should be parameterized/per-book, not a global default.

### C3 — Stop relying on `gate_book.py`; it crashes *(Grounding, confirmed)*
`gate_book.py` is non-functional (load_config arity; no `--lang`). I had referenced it in
both SKILL.md (P4, Setup) and CLAUDE.md.
**Fix (skill + CLAUDE.md):** use the working path — `lint_book.py <src> --lang <code>` (P3) +
`verify_book.py <src>` (P4) — and remove `gate_book.py` as the recommended orchestrator.
**Tool-side (will fix, trivial):** `gate_book.py:111` → pass `(lang, None, config_path)` and add a
`--lang` passthrough, so the orchestrator the repo's CLAUDE.md mandates actually runs.

### C4 — Stop mandating textbook structure for "any topic" *(Purity)*
Worked examples, exercises, difficulty markers, labs are mandated universally → a memoir/
reference/narrative hard-fails P3.
**Fix:** make these a **book profile** selected in P0 (swappable, like the lang pack). The pure
engine mandates only the genre-neutral spine. P3 lints the profile's contract, not a fixed one.

### C5 — Formalize the local-config contract *(Purity + Robustness, convergent)*
The "Local configuration (read first)" hook has no schema, no location precedence, and keys
gate-hardness on a freeform prose sentence.
**Fix:** one canonical location (a `## write-book` section in project CLAUDE.md **or** a named
`write-book.config.*`, with precedence); an enumerated key list (tool paths, **book-root layout**,
default language, active **book profile**, gate strictness); and **key gate-hardness on a disk
probe** — "if the toolchain is discoverable on disk, gates are hard regardless of prose."

---

## D. Important

| # | Finding (reviewer) | Fix |
|---|---|---|
| I1 | P5 packaging order contradicts "shelf before readers" (Usability) | Reorder: author reader config → register → build shelf → build reader → open. |
| I2 | Missing reader-config authoring step (Usability + Grounding) | Add P5 step: create the reader `config.json` (unique `id`, `ui_lang`, ordered chapter manifest) that `build_reader.py <config.json>` consumes. |
| I3 | `update`/scan protocol undefined (Usability) | Define a concrete scan protocol in P5 (re-read landscape ⚠️ → re-verify each fragile fact → sync base numbers across citing chapters → re-lint/verify → append dated scan-log line); P0 `update` points at it. |
| I4 | WARN tier dropped (Robustness + Grounding) | Document the full verdict rule: ≥2 incorrect→FAIL; 1 incorrect/any imprecise→WARN (resolve before pass); <2 conclusive→INCONCLUSIVE; else PASS. |
| I5 | Skeleton enforced only from lang pack (Grounding) | Make the lang pack `skeleton_slots` (or per-book `--config`) the single source of truth; style-guide copies it verbatim. |
| I6 | Base-numbers invisible to Tier-2 (Grounding) | P1 writes the base-numbers table into `_meta/running-examples.md` (where `load_baseline` reads) before P4. |
| I7 | "config pins verifier panel" is false; panel claim wrong (Grounding) | Remove "verifier panel" from pinnable list; state the panel is 3 fixed code-level families; require confirming the **writer model is not on the panel** (subset via `--models`). |
| I8 | Tier-2 mislabeled as web/fact-checking (Grounding) | Describe Tier-2 as **closed-book re-derivation** against chapter + baseline; move the web-access requirement to P1/P2 only. |
| I9 | "copy + translate a lang pack" breaks non-CJK (Grounding) | A new pack must redefine `depth_unit_pattern` + thresholds (e.g. `\w+` word floor) + language-appropriate forbidden/vocab, not just translate strings. |
| I10 | Stale/undefined running-term list across parallel batches (Robustness + Usability) | Designate `_meta/terms.md`; build it after each batch (topological batching); or run a post-fan-out cross-reference pass. |
| I11 | No planned-vs-written reconciliation; serial fallback backoff-less (Robustness) | Post-P2 gate: one non-empty file per planned chapter id from `outline.md`; serial retries reuse the exponential backoff and fail the run (never silently skip). |
| I12 | "Every chapter pinned bridge" gate contradicts fade-out/rule-5; PIN preserves invalidated bridges (Robustness + Grounding + Usability) | "≤1 bridge per chapter"; "none (native/taught-directly)" is a gate-passing value; P4 bridging review exempts no-bridge chapters; on profile change re-validate pinned sources, invalid → review queue. |
| I13 | landscape/maintenance assume a perishable topic (Purity) | Gate landscape + fragile-facts/scan machinery on a "time-sensitive facts" flag; evergreen → skip/reduce to the base-numbers table. |
| I14 | Book directory layout hard-coded (Purity) | Abstract `<book-root>`/`<book-src>` placeholders; add layout to config-pinned keys (repo's own primary book is `book/`, no `book-src/`). |
| I15 | Bridging regime presented as universal (Purity) | Bridging = optional style module (default-on for the instructional/technical profile, else absent — incl. its P4 pass and P5 gate). |
| I16 | Adjudication conflates model- with source-independence (Robustness) | "independent" = distinct primary sources; two families citing one URL = one source. |

---

## E. Minor (batch)

- **M1** P3 gate covers only lint → also require `check_diagrams.py` exit 0 + base-numbers reconcile.
- **M2** Define the base-numbers table schema in P1 (value, unit, owning concept, citing chapters).
- **M3** Move the web check before P1 (P1 landscape already needs web), or scope P1.5 to P2-onward needs.
- **M4** Broaden description triggers (handbook/textbook/guide/manual/course); keep "rescan" only once defined.
- **M5** Define `<book>`/`<slug>` and add "derive slug, create dir" as the first P1 action.
- **M6** Note difficulty/time/worked-example are WARN-only (raise via `--config` or state they're advisory; worked-example test is "fenced block exists", not "real numbers").
- **M7** P1.5 smoke-tests the panel CLIs (codex/agy round-trip), not just script presence.
- **M8** Split Conventions into "Engine invariants" vs "Reference-implementation notes"; move the CJK `wrapCJK`/Apple-font diagram detail there (keep only a genre-neutral diagram rule in the engine).
- **M9** Batch-retry granularity: track per-chapter completion; don't re-run succeeded chapters.
- **M10** Single-source-correction tie-breaker: quarantine + escalate (don't silently keep or one-source-fix).
- **M11** Web liveness (not one-shot): re-verify date-stamped hedges; panelists assert web at run start.

---

## F. Tool-side items (outside the pure skill)

- **Will fix (trivial, unblocks repo):** `gate_book.py` arity + `--lang` passthrough.
- **Flag only (larger tool redesign, not in this pass):** generalize `verify_prompt.md` to be per-book/parameterized; align `load_baseline` filename with what the skill writes; make `PANEL` configurable; add a non-CJK depth metric to the lint engine.

---

## G. Open questions for the second-opinion pass (agy)

1. Is the **book-profile** abstraction worth it, or YAGNI? (It is the largest change. Alternative: keep the skill scoped to "instructional/technical nonfiction" and say so honestly in the description, dropping the "any topic" claim.)
2. Disk-probe gate-hardness vs an explicit config boolean — which is less surprising?
3. Should the skill fix the tools (gate_book) or just route around them?
4. Anything the four lenses missed.

---

## H. Second opinion (agy / Gemini 3.5 Flash High) — reconciliation & final decisions

agy reviewed this plan + the skill. Verdicts and my decisions:

1. **Book-profile abstraction → SCRAP it (agy: YAGNI).** A deterministic linter +
   multi-model math re-derivation pipeline is structurally a *technical/instructional
   nonfiction* quality system; bolting a genre system on for fiction/memoir nobody will
   generate is over-engineering. **Decision: drop the profile system and the "any topic"
   claim. Scope the skill to technical/instructional nonfiction. "Pure" now means: not
   overfit to a specific author, topic, language, or repo — within that scope.** This
   replaces C4's heavy redesign with a one-line re-scope, drops I15, and simplifies C5.
2. **Gate-hardness → explicit config field, not pure disk-probe (agy).** **Decision:
   synthesis** — `strict_gates: true` is an explicit, machine-readable config field
   (deterministic; satisfies the Robustness lens's "don't infer from prose"); P1.5 uses the
   disk probe to *validate* the declaration (declared strict + a required tool missing →
   hard abort with diagnostics, never silent soft-degrade).
3. **Fix tools at source (agy).** **Decision: adopt.** Fix `gate_book.py`
   (arity + `--lang`); generalize `verify_prompt.md` to a domain-agnostic adversarial
   closed-book re-derivation template (the TLA+ bullets were just examples of general
   categories — numbers, derivation steps, proofs, counts, bounds — so generalizing loses
   no TLA+ precision and unblocks every other topic). This also resolves agy's "C2
   soft-degrade hangs in CI" — a generic verifier prompt always works, no human halt.
4. **Promote I9 (non-CJK depth metric) + I6 (base-numbers baseline file) to Critical**
   (agy: both are hard blockers). **Decision: adopt** → C6, C7.
5. **I10/I11 term-list (agy: batching kills parallelism).** **Decision: adopt agy's
   alternative** — keep parallel fan-out at full width; add a single **post-fan-out
   sequential cross-reference + reconciliation pass** (P2.5) that (a) asserts one non-empty
   file per planned chapter id, (b) extracts the term set, (c) rewrites missed/duplicated
   cross-references. One mechanism covers I10 + I11.
6. **Merge I12 → C4/bridging rules; demote I15** (agy). **Decision: adopt** — bridging
   stays as the technical-nonfiction house style, but "no bridge (native / taught-directly)"
   is an explicit gate-passing value.
7. **Flagged, NOT in this pass:** verify_book `--prompt` per-book flag + `load_baseline`
   filename alignment + configurable `PANEL` + a fact-extraction step for Tier-2 token
   limits (agy's token-exhaustion concern). Recorded as tool-side follow-ups.

### Final critical set (post-agy)
C1 P4+P5 gates · C2 domain-agnostic verifier prompt + honest closed-book Tier-2 ·
C3 route around + fix `gate_book.py` · C4 re-scope to technical/instructional nonfiction
(drop profile system & "any topic") · C5 formalize local-config contract with
`strict_gates` field validated by probe · C6 non-CJK depth metric · C7 base-numbers
written where the verifier reads them.

---

## I. Third review round (4 models via ./reports) — incorporated

After the enhancement landed, the skill was re-reviewed by 4 more models
(GLM-5.1 FAIL, Qwen3.5-397B FAIL, GPT-OSS-120B WARN, Llama-3.3-70B PASS) across
completeness / consistency / generality / gate-correctness / failure-handling.
Convergent defects (and a blocker advisory) drove a second enhancement pass —
20 edits to SKILL.md, all verified present, purity preserved:

| Fix | Defect closed | Where |
|---|---|---|
| `outline.md` canonical; `running-examples.md` a generated copy; **byte-identical asserted** at P3 + P5 | GLM-5.1's #1 danger: dual base-number copies drift silently, contradictory numbers pass both gates | P1, P3, P5, Update |
| Per-book `_meta/lint.config.json` raises `worked_example`/difficulty/time to **ERROR**; P3 lints with it | P3 gate was vacuous (WARN-only; "fenced block exists") — passed shallow, example-free books | P1, P3 |
| `verify_book --timeout 240`; INCONCLUSIVE → bounded retry then **halt-with-quarantine**; non-interactive "escalate" = exit, not wait | Qwen's #1: verifier hang / INCONCLUSIVE dead-end → indefinite CI block | P4 |
| Temp-file + **atomic rename** for chapter writes and the update multi-file edit | GPT-OSS's #1: partial/half-written files corrupt the source on crash/429-exhaustion | P2, Update |
| **Re-run P2.5** (reconcile + regenerate appendices) after any P3/P4 re-draft, asserted in P5 gate | Stale cross-refs/appendices after fixes | P2.5, P5 |
| Automated screenshot is the gate; human browser-confirm **advisory, skipped in CI**; + build-loads/no-404 smoke | Render check blocked non-interactive runs | P5 |
| `<3`-provider **degradation** (run on ≥2, document; `<2` → unverified halt) | 3-family panel assumed ≥3 providers | P4 |
| Manual-mode gates are **HARD** (FAIL blocks like exit 1) | Manual-mode strictness paradox left gates implicitly soft | P3, P4 |
| `_meta/.outline-approved` artifact P2 checks | P1 human gate was an unenforceable instruction | P1, P2 |
| Lang-pack authoring must define `skeleton_slots`; bounded P2 retry (3/chapter); fade-out caps are upper bounds (zero always valid); `isomorphism_score` defined; tool executability smoke-test | Assorted completeness/consistency gaps | P0.5, P1, P2, P4 |

Weighed, not blindly obeyed: the advisory's "cap escalation at 5 models" does not
map to the tool's **fixed 3-family** panel, so it became "bounded retry then halt";
the "300s timeout" became the tool's real `--timeout` default (240s, configurable).
