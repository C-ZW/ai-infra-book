---
name: write-book
description: Generate a technical or instructional-nonfiction book on any subject, via a gated multi-agent pipeline — calibrate to a target reader, write meta files (style guide, outline, fact baseline), fan out chapters in parallel, run a two-tier quality gate (deterministic contract lint + cross-model re-derivation of load-bearing claims), and package into an offline reader. Use when the user asks to write, create, or update/rescan a book, handbook, textbook, guide, manual, or course.
---

# write-book

A reusable pipeline for **technical and instructional nonfiction** (textbooks,
handbooks, guides, courses, reference works). It is NOT for fiction/memoir/prose:
the quality gate is built on a deterministic contract linter and cross-model
re-derivation of load-bearing claims, which only make sense for expository
material with checkable structure and facts.

The pipeline calibrates to a **target reader**, writes the book's meta files,
fans chapters out to parallel agents, then puts the result through a two-tier
quality gate before packaging. That gate (deterministic lint → cross-model
verification) is the spine of P3–P4 — apply it; never hand-roll header greps or
single-model reviews.

**Engine/config split.** This file is the general engine; it assumes no specific
author, reader, subject, or language. Concrete values (tool paths, default
language, gate strictness, book layout) live in *local configuration* and
*swappable packs*, read at runtime — same pattern as the bundled linter's
language packs. Where a concrete tool/path is named below it is the **bundled
reference implementation**; discover it at runtime, fall back as described.

## Setup (discover, don't hard-code)

- **Local configuration (read first):** see the contract below. It pins the
  concretes and the gate-strictness switch for this project.
- **Book layout:** sources live under `<book-root>/<slug>/` with meta files in
  `<book-src>/_meta/`. `<book-root>` and the `<book-src>` layout are configurable
  (some projects put a single book at the repo root with no `<slug>` level).
- **Reader profile (optional):** a calibration source describing the target reader
  (known domains, goals, language, preferences). If absent, calibrate
  interactively in P0 and persist the answers for future runs.
- **Toolchain (discover):** an offline-reader builder, a deterministic linter
  (language-independent engine + swappable `lang/<code>.json` packs), a
  cross-model verifier, and a diagram checker. The reference bundle exposes
  `lint_book.py`, `verify_book.py`, `gate_book.py` (orchestrates the two),
  `check_diagrams.py`, `build_reader.py`, `build_shelf.py`.
- **Library shelf (optional):** when maintaining more than one book, register each
  in a registry and build a bookshelf page.

### Local configuration contract

The engine reads ONE config source, in this precedence:
1. a `write-book.config.{json,yaml}` (or a `## write-book` section in the project
   `CLAUDE.md`) at the project root — the config file wins if both exist.

Recognized keys (all optional; the engine uses defaults when a key is absent):
- `tools_path` — directory holding the toolchain.
- `book_root`, `book_src_layout` — where book sources + `_meta` live.
- `default_language` — `lang/<code>.json` pack code; also the reader UI language.
- `profile_path` — reader-profile calibration source.
- `strict_gates` — `true` | `false`. **The hard/soft switch** (below).

**Gate strictness.** Gates are HARD (a failing or un-runnable gate blocks the
pipeline) when `strict_gates: true`, OR when it is unset and the toolchain is
discoverable on disk. Gates run in **manual mode** (defined in P3/P4, never
silently skipped) only when no toolchain is discoverable and `strict_gates` is
not true. P0.5 validates this: `strict_gates: true` with a required tool missing
is a hard abort, not a soft fallback.

## Conventions

**Engine invariants (always):**
- Code, configs, comments, logs: English. Book content + reader UI: the book's
  chosen language.
- The first calibration question is always the output language (P0).
- Generated artifacts (reader HTML, bookshelf) are never hand-edited.

**Reference-implementation notes (apply when using the bundled reader/registry):**
- Each reader config `id` is unique across the registry (it namespaces per-book
  reading-progress storage).
- Build the shelf before the readers (a reader auto-links the nearest ancestor
  `bookshelf.html`).
- CJK fixed-width diagrams (bundled Apple-platform reader only): it enforces CJK =
  2 columns via its `wrapCJK` span mechanism — never `@font-face size-adjust`
  (WebKit ignores it on `local()` fonts, so Safari breaks while Chrome looks fine).
  The 2-column ratio assumes Apple Menlo+PingFang; a reader on other platforms or
  fonts must define its own ratio. See the tools README.

## P0 — Calibrate (cheap, interactive)

1. **Output language first.** Selects the linter language pack and reader UI
   language. (No language pack for it yet? See P0.5.)
2. Reader profile: read the profile source if present; else ask for target reader,
   prior-knowledge baseline (assume-known vs teach-from-zero), and goals.
3. Confirm via menus: subject + target capability, scope (chapter estimate), lab
   budget if hands-on labs apply.
4. PII / publishing: if the book may be shared or published, confirm what
   identifying material is allowed; default conservative.
5. Quote expected scale (agent count, rough token cost, wall time). Modes:
   `outline-only` (stop after P1), `full`, `update` (run the scan protocol in P5).
6. Derive a unique `<slug>` from the subject and create `<book-root>/<slug>/`.

## P0.5 — Pre-flight (fail fast, before writing)

- Toolchain resolves AND each tool actually runs (smoke-test with a trivial
  invocation, e.g. `--help` — discoverable ≠ executable), or the manual-mode
  fallback is acknowledged per the strictness rule. If `strict_gates: true`, a
  missing or non-runnable tool aborts here.
- A linter language pack exists for the chosen language. If not, author one — a new
  pack must define `skeleton_slots` (the chapter skeleton P1/P3 enforce) AND
  **redefine `depth_unit_pattern` and the depth thresholds** for that language
  (e.g. a `\w+` word matcher with a word-count floor) plus language-appropriate
  forbidden-char/vocab data. The default CJK character-count metric permanently
  fails the depth gate for non-CJK prose; translating strings alone is not enough.
- A verifier prompt that matches the book's **subject and language** is available
  (the bundled `verify_prompt.md` is a domain-agnostic template; supply a
  language-matched one for non-default languages).
- Web access is available (needed for the P1 landscape and P2 per-chapter checks).
- If the verifier is present, smoke-test its panel CLIs (a trivial round-trip per
  model family) so P4 doesn't fail hours later on an absent/unauth CLI.
- `<book-src>/` is writable.

## P1 — Meta files (the book's DNA)

Create `<book-src>/_meta/`:

- `style-guide.md` — the writing contract:
  - Reader profile + the assume-known / teach-from-zero split.
  - Language rules.
  - **Mandatory chapter skeleton — copied verbatim from the language pack's
    `skeleton_slots`** (the linter enforces those slots and nothing else; a
    skeleton written here that diverges from the pack will fail the lint).
  - Depth standards (≥1 worked example with real numbers per chapter, decision
    frameworks, no tool name-dropping without mechanism). The linter's default
    worked-example/difficulty/time checks are WARN-only and its worked-example test
    is just "a fenced block exists", so an exit-0 gate would pass shallow,
    example-free books. So P1 also writes a per-book lint config
    `_meta/lint.config.json` raising `worked_example` (and difficulty/time) to
    ERROR; P3 runs the linter with `--config _meta/lint.config.json` so the gate
    actually enforces depth. (Confirming "real numbers" beyond a fenced block stays
    a human/P4 check.)
  - **Bridging contract** (objective, fatigue-free analogies): no second-person /
    conversational bridging; technical mechanism-to-mechanism only (no everyday
    analogies); ≤1 analogy per chapter; explicit anchor + boundary (name the
    source concept, state where it holds and breaks); bridge at first mention;
    only bridge from concepts the reader is established to know. **"No bridge —
    taught directly" is an explicit, valid choice** for chapters with no strong
    structural analog and for the fade-out's final third.

- `outline.md` — full TOC + per-chapter spec (goal, must-cover, must-NOT-cover
  with owning-chapter pointer, worked-example idea, lab idea), plus:
  - **Base-numbers table** — one row per load-bearing constant reused across ≥2
    chapters: value, unit, owning concept, citing chapters. `outline.md` is the
    **single source of truth**; generate `_meta/running-examples.md` as a verbatim
    copy of this table (the Tier-2 verifier reads its baseline from there) and
    NEVER hand-edit the copy. P3 and P5 assert the two are byte-identical, so the
    mirrors cannot drift.
  - **Bridge Registry** — assign each chapter at most one bridge source; "none" is
    valid. Dedup globally so any one source bridges ≤3 times book-wide.
  - **Fade-out schedule** — front third: external analogies sparingly (cap per
    1000 words); middle third: prefer cross-references to already-defined in-book
    concepts; final third: native vocabulary only. These caps are upper bounds:
    zero analogies is always allowed, so a "no bridge — taught directly" chapter
    never violates the schedule.

- `landscape-<date>.md` — fact baseline, **only when the subject has time-sensitive
  facts** (versions, prices, hardware, project status). A research agent with web
  access verifies them with source URLs and ⚠️ on unconfirmed items; chapters
  treat it as the fact anchor. Evergreen subjects (most math, theory, history)
  skip this file.

**GATE: present the outline (TOC + base-numbers table + Bridge Registry +
fade-out) to the user and STOP for approval before P2.** Highest-leverage QA
point; never skip it. On approval, write `_meta/.outline-approved` (date + the
approved chapter list); P2 refuses to start if that marker is absent, so the human
gate is enforced by an artifact, not just an instruction.

## P2 — Chapter fan-out

- One writing agent per chapter, parallel batches (default ~6; configurable). On
  HTTP 429 back off exponentially (2ⁿ s); a serial fallback retries each chapter
  with the same backoff, up to **3 attempts per chapter**, then fails the run with
  a report of which chapter ids are complete vs missing — never silently skips.
  Track per-chapter completion and retry only the chapters that failed.
- **Atomic writes:** each agent writes to a temp file and renames into place only
  on successful completion, so a chapter file is always whole or absent — a
  crashed/partial write leaves no half-file. Re-running a chapter overwrites it and
  must re-enter the gates.
- Each agent: meta files first; obey scope; do targeted web verifications for its
  chapter; hedge unverifiable facts with a date stamp; honour the bridging
  contract + its fade-out tier (its assigned bridge source, or none); write
  exactly one file. (Cross-chapter term consistency is handled in P2.5, not during
  the parallel draft — siblings cannot see each other's just-defined terms.)
- **Topic-based books** (standalone entries, not a chapter arc): fan out one agent
  per entry; define the entry's required slots in `style-guide.md` so the linter
  checks them in place of the chapter skeleton.
- Appendices (labs index, glossary, cheatsheets) run AFTER P2.5 and compile from
  what was actually written.

## P2.5 — Cross-reference + reconciliation (sequential)

A single sequential pass once all chapters exist (keeps P2 at full parallel
width):
1. **Reconcile:** assert exactly one non-empty file per planned chapter id from
   `outline.md` (no missing chapters, no stale extras from retried runs). Any
   mismatch is a HARD stop — never proceed with N−1 chapters.
2. **Term set:** extract the defined-term set across all chapters into
   `_meta/terms.md`.
3. **Cross-reference:** rewrite missed or duplicated cross-references so each
   concept is defined once and later chapters point back (the fade-out's
   middle-third contract).

**Re-run P2.5 whenever a P3/P4 fix re-drafts a chapter**, before P5 — appendices
and cross-references compiled from pre-fix text are otherwise stale.

## P3 — Quality gate, Tier 1 (deterministic)

- `lint_book.py <book-src> --lang <code> --config _meta/lint.config.json` (or
  `gate_book.py <book-src> --lang <code> --config _meta/lint.config.json` without
  `--verify`): skeleton slots in
  order, exercise→solution pairing, per-chapter depth floor, worked-example (raised
  to ERROR by the per-book config), forbidden-character + blocked-vocabulary.
- `check_diagrams.py <book-src>` — ASCII diagram alignment.
- Cross-chapter base-number consistency against the `outline.md` table (the linter
  does **not** check this — do it here, across every citing chapter), AND assert
  `_meta/running-examples.md` is byte-identical to the `outline.md` table.
- **Manual mode** (no linter): still a HARD gate — run an explicit checklist
  (skeleton slots in order, ≥1 worked example with real numbers per chapter, no
  forbidden chars, no banned vocab), record a pass/fail per chapter, and a FAIL
  blocks exactly as the tool's exit 1 would. Manual mode changes how the gate runs,
  never whether it blocks.
- Fix findings directly; record anything deferred.
- **GATE: `lint_book.py` (with the per-book config) exits 0 AND `check_diagrams.py`
  exits 0 AND base numbers reconcile across every citing chapter AND
  `_meta/running-examples.md` is identical to the `outline.md` table, before P4.**

## P4 — Quality gate, Tier 2 + adjudication (cross-model)

- `verify_book.py <book-src> --timeout 240` (or `gate_book.py <book-src> --lang
  <code> --verify`): a panel of **three different model families re-derives each
  chapter's load-bearing computations/proofs from scratch, closed-book** (from the
  chapter + the `_meta/running-examples.md` baseline — it does NOT browse or
  fact-check; web belongs to P1/P2). Always pass an explicit `--timeout` (default
  240s) so a hung provider cannot stall the run. Confirm the **writer model is not
  on the panel** (subset with `--models` if it is), or cross-family independence
  collapses. **Degradation:** the rule needs ≥2 families to run conclusively; if
  only 2 providers are reachable, proceed on those 2 and record the reduced panel;
  with <2 reachable, Tier-2 cannot run — halt with an explicit "unverified" status,
  never a silent pass.
- **Verdict rule (mirror the tool):** ≥2 families `incorrect` → FAIL; exactly 1
  `incorrect` or any `imprecise` → **WARN** (resolve before passing, do not
  auto-pass); fewer than 2 conclusive → INCONCLUSIVE (never a pass); else PASS.
- **Risk-prioritized:** math-intensive books get a full pass first; very large
  books subset the heaviest chapters; the rest get a structural + spot-check pass.
- **Bridging review** (separate model pass): the reviewer model rates each declared
  bridge's structural similarity to its source as `isomorphism_score` 1–5 (5 =
  mechanism-for-mechanism, ≤2 = superficial) and emits `{detected_bridges,
  isomorphism_score, conversational_phrases}`; reject/rewrite chapters with
  conversational phrasing or a weak (≤2) analog — but **exempt chapters that declare
  no bridge** (taught-directly / fade-out final third are valid).
- **Manual mode** (no verifier): Tier-2 has NO valid single-agent equivalent —
  spawn **≥2 independent reviewer sub-agents of different model families** (this is
  automatable, not a human step) using the domain-matched verifier prompt; only
  halt if cross-model review is impossible in the environment.
- **Adjudicate:** "independent" means **distinct primary sources**, not merely
  distinct models (two families citing one URL = one source). A single source
  never overturns the baseline; a major correction needs two independent sources.
  A flagged error with only one corroborating source → quarantine the chapter and
  escalate (current value, proposed value, the source) to the user; record it.
- **GATE: Tier-2 verdict is PASS (no FAIL, not INCONCLUSIVE, every WARN resolved)
  and every chapter clears the bridging review, before P5. On FAIL, fix the flagged
  derivations and re-run. On INCONCLUSIVE (a panelist errored/timed out), retry the
  failed panelists once; if still <2 conclusive, HALT with a per-chapter quarantine
  report — never hang waiting, never auto-pass. In non-interactive runs, "escalate"
  means exit with that report, not block on a human.**

## P5 — Package + register

- **`maintenance.md` (mandatory deliverable):**
  1. base-numbers table — from `outline.md`.
  2. fragile-facts index — the ⚠️ entries from `landscape-*.md` (empty/omitted for
     evergreen subjects), hand-curated.
  3. **scan protocol** (the concrete steps `update` runs — see below).
  4. dated scan log (first entry = creation date, mode, chapters).
  5. **Bridge Registry lock** — record each chapter's approved bridge source (or
     "none"). On a later profile change, re-validate every pinned source against
     the new known-set; a source no longer reader-known goes to a rewrite queue,
     not silently kept. Re-bind only unpinned chapters, counting pinned uses
     against the ≤3 budget.
- **Author the reader config** the builder consumes: a `config.json` with a unique
  `id`, `ui_lang`, the ordered chapter manifest, and title.
- **Order:** register the book in the registry → build the shelf → build the reader
  (`build_reader.py <config.json>`, so it links the existing shelf) → open both.
- **Build smoke check:** load the built reader (headless) and confirm it opens with
  no console 404s/errors before declaring the bundle done.
- **Render check (beyond `check_diagrams.py`):** screenshot one text-heavy boxed
  diagram through the built reader in headless Chrome
  (`--force-device-scale-factor=2`, `index.html#<chapter-id>`) — this automated
  screenshot is the gate. Asking the user to confirm in their real browser is
  advisory and is **skipped in non-interactive/CI runs** (source math and rendered
  output are separate failure domains, so keep it for interactive runs).
- A book-level `CLAUDE.md` pointing at the meta files and rebuild commands.
- **GATE: `maintenance.md` exists; the base-numbers table is byte-identical across
  `outline.md`, `_meta/running-examples.md`, and `maintenance.md`; ≥1 scan-log
  entry; P2.5 was re-run after the last chapter edit; Tier-1 clean; and Tier-2 PASS
  — before declaring done.**

## Update mode — the scan protocol

`update`/`rescan` runs these concrete steps (also written into each book's
`maintenance.md`), idempotently (one scan-log entry per run; regenerate, don't
append, the fragile-facts index):
1. Re-read the `landscape-*.md` ⚠️ entries; re-verify each fragile fact via web.
2. For any changed base number, edit the canonical `outline.md` table, then
   regenerate `_meta/running-examples.md` and the `maintenance.md` table from it
   (temp-file + atomic rename) and propagate into chapter bodies; then re-run the
   P3 consistency + byte-identity checks. A crash mid-update is caught on the next
   run because the P3/P5 byte-identity assertion fails until all copies match.
3. Re-run P3; re-run P4 if load-bearing math/derivations changed.
4. Append one dated scan-log line.

## Post-reading feedback (offer, don't force)

After the reader finishes, optionally run a short menu interview (which chapters
too shallow/unclear, were labs actually done) and fold results into the
reader-profile source for better calibration of future books.
