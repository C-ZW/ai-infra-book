# write-book v3 — phase specifications

Read the phase you are about to run, fully, before acting. SKILL.md's dispatch
table and prime rule (halt-and-ask on anything not covered here) apply
throughout. `<skill>` below = this skill's directory; `<book-src>` = the book's
source dir; `<tools>` = the configured `tools_path`.

## §P0.5 — Pre-flight (fail fast, before writing anything)

- Toolchain resolves AND each tool actually runs (smoke-test with a trivial
  invocation, e.g. `--help` or a no-op — discoverable ≠ executable). Any
  missing/non-runnable tool → **HALT with diagnostics**. No manual mode.
- A linter language pack `lang/<code>.json` exists for the chosen language.
  If not, author one: it must define `skeleton_slots` AND **redefine
  `depth_unit_pattern` + depth thresholds** for that language (e.g. a `\w+`
  word matcher with a word-count floor) plus language-appropriate
  forbidden-char/vocab data. The default CJK character metric permanently
  fails the depth gate for non-CJK prose; translating strings is not enough.
- A verifier prompt matching the book's **language** is available (the bundled
  `verify_prompt.md` is domain-agnostic but zh-TW; a non-zh book needs a
  language-matched prompt file — if absent, halt and ask).
- Web access works (P1 landscape research + P2 per-chapter checks need it).
- Panel CLI smoke test: one trivial round-trip per model family
  (`codex`, `agy`) so P4 doesn't fail hours later on an absent/unauth CLI.
- `scripts/p2-write-chapters.js` and `scripts/p4-adjudicate.js` exist; the
  Workflow tool is available (else note the Agent-tool fallback from SKILL.md).
- `<book-src>/` is writable.
- Initialize `_meta/state.json` (atomic write):
  `{"form": …, "lang": …, "reader_register": …, "chapters": {}, "gates": {}}`.

## §P1 — Meta files (the book's DNA)

Create `<book-src>/_meta/`:

- **`style-guide.md`** — the writing contract:
  - Reader profile + the assume-known / teach-from-zero split; reader register.
  - Language rules.
  - **The form contract, copied from `<skill>/references/forms/<form>.md`**
    and instantiated (fill its per-book blanks). For `instructional`, the
    mandatory chapter skeleton is copied **verbatim from the language pack's
    `skeleton_slots`** (the linter enforces those slots; a diverging skeleton
    here will fail P3) and the bridging contract applies (see the form file).
  - Depth standards (≥1 worked example with real numbers per chapter for
    instructional; the form file states each form's depth expectation).
  - **Notation discipline (math/technical books):** one canonical notation
    table (symbol, meaning, first-defining chapter) and the banned aliases
    (e.g. the corpus rule "E[N]/E[T], never L/W"). Enforce mechanically:
    put each banned alias into the book's `lint.config.json` under
    `vocab_error` with its canonical replacement — the linter then blocks
    drift for free.
  - **Prose contract:** for zh-TW books, the style guide includes the rules of
    `<skill>/references/zh-prose.md` (translationese bans, rhythm rules, and
    the profile-material rule: personal history is calibration only, never
    book content). Other languages: state the equivalent register rules
    explicitly.
- **`_meta/lint.config.json`** — start from
  `<skill>/references/forms/<form>.lint.json`; for zh-TW books additionally
  merge `<skill>/references/forms/zh-prose.lint.json` ON TOP (it carries the
  language pack's own `vocab_regex_warn` entries too — deep-merge REPLACES
  lists, so using the form fragment alone would silently drop pack rules);
  then pin per-book values:
  - the exact skeleton dialect (instructional; pick ONE variant per slot),
  - **`chapter_globs` matching the book's real file naming** — MANDATORY for
    narrative/reference (topic-named files silently skip every chapter check
    otherwise; P3's count assert will catch it, fix it here first),
  - any extra book-specific vocabulary rules.
- **`outline.md`** — full TOC + per-chapter spec (goal, must-cover,
  must-NOT-cover with owning-chapter pointer, worked-example idea, lab idea
  where labs apply), plus:
  - **Spine (ALL forms)** — name the book's single running thread: one
    example, object, or organizing idea the whole book keeps returning to
    (a worked system with fixed numbers, one recurring sentence analyzed
    four ways, a pattern language, one unspoken-assumption motif…). Every
    successful book in this corpus has exactly one. Each chapter's spec says
    how it touches the spine — or explicitly why it doesn't (valid, but must
    be stated, never accidental). The base-numbers table is the spine's
    numeric shadow; the teach-test generator anchors problems to it.
  - **Base-numbers table** (ALL forms) — one row per load-bearing constant
    reused across ≥2 chapters: value, unit, owning concept, citing chapters.
    `outline.md` is the **single source of truth**; generate
    `_meta/running-examples.md` as a verbatim copy (the Tier-2 verifier reads
    its baseline there) and NEVER hand-edit the copy. P3 and P5 assert the two
    are byte-identical.
  - **Bridge Registry + fade-out schedule** (instructional only) — per the
    form contract: ≤1 bridge per chapter, "none" valid, any source ≤3 uses
    book-wide; fade-out caps are upper bounds (zero always allowed).
- **`landscape-<date>.md`** — fact baseline, ONLY when the subject has
  time-sensitive facts (versions, prices, hardware, project status). A
  research agent with web access verifies each with source URLs, marks
  unconfirmed items ⚠️. Evergreen subjects skip this file.

**GATE: present the outline (TOC + spine + base-numbers table + Bridge
Registry + fade-out where applicable) to the user and STOP for approval
before P2.**
Highest-leverage QA point; never skip. On approval, record in state.json:
`"outline_approved": {"date": …, "chapters": [ids…]}`. P2 refuses to start if
that field is absent.

## §P2 — Chapter fan-out (Workflow)

Run `scripts/p2-write-chapters.js` via the Workflow tool. Args contract (see
the script header): `skillDir`, `bookSrc`, `lang`, `form`, `templatePath`
(= `<skill>/references/templates/chapter-writer.md`), `chapters` — one entry
per planned chapter `{id, file, brief}` where `brief` is a 1–3-line pointer to
the chapter's outline entry (plus its assigned bridge source or "none" and
fade-out tier for instructional).

- The script retries each chapter ≤3 attempts (re-dispatch on null/failed; no
  timer backoff — the harness retries transient API errors internally).
- The template enforces atomic writes (agent writes `<file>.tmp`, then `mv`):
  a chapter file is always whole or absent.
- Writer agents read the meta files first, obey scope, do targeted web
  verification for their chapter, hedge unverifiable facts with a date stamp,
  and write exactly one file. Cross-chapter term consistency is P2.5's job —
  parallel siblings cannot see each other's terms.
- On return: write per-chapter statuses into state.json (`drafted` /
  `failed`). ANY chapter still `failed` after retries → report the complete
  vs. missing chapter ids and **halt** — never proceed with N−1 chapters.
- Re-running a chapter overwrites it and must re-enter every gate.
- Appendices (labs index, glossary, cheatsheets) are written AFTER §P2.5,
  compiled from what was actually written.

## §P2.5 — Cross-reference + reconciliation (sequential)

One sequential pass once all chapters exist:

1. **Reconcile (Bash):** exactly one non-empty file per planned chapter id
   from state.json's `outline_approved.chapters`; no stale extras. Mismatch =
   HARD stop.
2. **Term set:** extract the defined-term set across chapters into
   `_meta/terms.md`.
3. **Cross-reference:** rewrite missed/duplicated cross-references so each
   concept is defined once and later chapters point back.

Set chapter statuses to `reconciled`. **Re-run this section whenever a P3/P4
fix re-drafts a chapter**, before P5 — appendices and cross-references
compiled from pre-fix text are stale otherwise.

## §P3 — Quality gate, Tier 1 (deterministic)

Commands (from `<tools>`):

```
python3 gate_book.py <book-src> --lang <code> --config <book-src>/_meta/lint.config.json
python3 check_diagrams.py <book-src>
```

Plus three main-loop asserts:

- **Chapter-count assert:** linted chapter count (`lint_book.py … --json`,
  entries with `"is_chapter": true`) equals the outline chapter count. This
  kills the vacuous pass where wrong `chapter_globs` silently skip every
  chapter check.
- Cross-chapter base-number consistency against the `outline.md` table (the
  linter does not check this — grep every citing chapter).
- `_meta/running-examples.md` byte-identical to the `outline.md` table.

Fix loop: findings → targeted fix agents (one per affected file, prompt =
finding + the pitfalls file) → re-run. Record `lint_pass` per chapter and
`gates.p3` in state.json.

**GATE: gate_book exit 0 AND check_diagrams exit 0 AND chapter-count assert
holds AND base numbers reconcile AND byte-identity holds, before P4.**

## §P4 — Quality gate, Tier 2 + adjudication (cross-model)

```
python3 verify_book.py <book-src> --json --timeout 240 \
    --writer-family anthropic --config <book-src>/_meta/lint.config.json \
    --out <book-src>/_meta/verify-report.json
```

- Always pass an explicit `--timeout`. `--writer-family anthropic` is
  mandatory while the writer is any Claude model: PASS then requires ≥2
  conclusive **non-Claude** panelists.
- **Exit code is blind to WARN** — parse the JSON. Verdicts: ≥2 families
  `incorrect` → FAIL; exactly 1 `incorrect` or any `imprecise` → WARN
  (resolve, never auto-pass); <2 conclusive (after the writer-family rule) →
  INCONCLUSIVE (never a pass); else PASS.
- **Degradation:** ≥2 families must run conclusively; with only 2 providers
  reachable proceed on those 2 and record the reduced panel; with <2, Tier-2
  cannot run — halt with an explicit "unverified" status.
- **INCONCLUSIVE** (panelist errored/timed out): retry the failed panelists
  once (`--no-cache --chapters <those>`); if still <2 conclusive, HALT with a
  per-chapter quarantine report. Never hang; never auto-pass. Non-interactive
  runs: "escalate" = exit with the report.
- **Adjudication:** collect every ❌ `incorrect` and ⚠️ `imprecise` finding
  and run `scripts/p4-adjudicate.js` per `references/adjudication.md`. Append
  its records to `_meta/verify-log.md`. Apply at most 2 adjudication rounds;
  re-verify fixed chapters with `--no-cache --chapters <fixed>`; then halt
  with the quarantine report if findings remain.
- **Bridging review** (instructional form ONLY): one reviewer agent per
  chapter using `templates/bridging-reviewer.md`; reject/rewrite chapters with
  conversational phrasing or a weak analog (`isomorphism_score` ≤2); chapters
  that declare no bridge are exempt.
- **Source independence:** "independent" means distinct primary sources, not
  merely distinct models. A single source never overturns the baseline; a
  major correction needs two independent sources; one-source corrections are
  quarantined and escalated.
- **Fact audit (books WITH a `landscape-*.md`, i.e. fact-heavy subjects):**
  Tier-2 is closed-book, so external facts need their own pass. Per chapter,
  one auditor agent (`templates/fact-auditor.md`) works in a REFUTATION
  frame: it tries to disprove each load-bearing external claim via web
  search. Survives = 2 independent sources confirm; refuted = correction
  flows through the landscape/base-number discipline (edit the canonical
  table first), logged to `_meta/verify-log.md` like adjudication outcomes;
  unverifiable = hedge with a date stamp. Evergreen books (no landscape)
  skip this. (Corpus precedent: the 27-agent refutation fact-check that
  produced 490 confirmations / 24 corrections on a concept-map book.)

Record `verified` per chapter and `gates.p4` in state.json.

**GATE: Tier-2 verdict PASS under the writer-family rule (no FAIL, not
INCONCLUSIVE, every WARN resolved via adjudication); — instructional only —
every chapter clears the bridging review; — fact-heavy books only — every
fact-audit `refuted` claim resolved through the landscape/base-number
discipline. Before §P4.5 (instructional) or §P5 (other forms).**

## §P4.5 — Teach-test (instructional form only)

Measures whether each chapter TEACHES, not just whether it is correct: a
weak solver that has read only the chapter must solve a near-transfer
problem. Run `scripts/p4_5-teach-test.js` via Workflow; roles are specified
in `templates/teach-test.md`. Args: `skillDir`, `bookSrc`, `templatePath`,
`chapters` = `[{id, file, goal}]` with `goal` taken from each chapter's
outline entry; `solverModel` defaults to `haiku` — keep it weak BY DESIGN
(a strong solver masks teaching gaps with its own pretrained knowledge; the
generator role also anchors problems to the book's own numbers for the same
reason).

- Per chapter: generator (session model) → solver (weak model, chapter-only)
  → judge (session model). The verdict judges the CHAPTER, never the solver.
- A failure's `gaps` list routes the chapter to a targeted rewrite (fix
  agent with the gaps + pitfalls), then §P2.5 re-runs and the chapter
  re-enters P3 → P4 (`--no-cache --chapters`) → P4.5. At most ONE rewrite
  round; still failing → present the failures to the user for an explicit
  waiver (recorded in state.json as `gates.p4_5.waived` with the chapter ids
  and reasons) or further direction.
- Record outcomes in state.json (`gates.p4_5`).

**GATE: every chapter passes teach-test, or the user has explicitly waived
the listed failures — before P5.** (Narrative/reference forms skip this
phase for now; extending it needs a form-appropriate notion of "transfer".)

## §P5 — Package + register

- **`maintenance.md`** (mandatory):
  1. base-numbers table — generated from `outline.md` (byte-identical);
  2. fragile-facts index — the ⚠️ entries from `landscape-*.md`
     (omit for evergreen subjects), hand-curated;
  3. the scan protocol (§Update below, concretized for this book);
  4. dated scan log (first entry = creation date, mode, chapters);
  5. Bridge Registry lock (instructional only) — each chapter's approved
     bridge source or "none"; on a later profile change re-validate pinned
     sources (invalidated → rewrite queue, never silently kept).
- **Retrospective:** one agent with `templates/retrospective.md` harvests this
  run's new pitfalls; append them (dated, symptom → rule) to
  `<skill>/references/pitfalls.md`.
- **Reader config:** author the `config.json` the builder consumes — unique
  `id` across the registry, `ui_lang`, ordered chapter manifest, title;
  `"inline_images": true` when the book has generated figures; `"math": true`
  ONLY for a KaTeX-register book (see `references/figures-math.md` — adds
  ~0.6 MB, opt-in).
- **Order:** register in the book registry → build shelf → build reader
  (`build_reader.py <config.json>`) → open both.
- **Smoke:** load the built reader headless; no console 404s/errors.
- **Render check:** screenshot one text-heavy boxed diagram through the built
  reader in headless Chrome (`--force-device-scale-factor=2`,
  `index.html#<chapter-id>`) — the automated screenshot is the gate; asking
  the user to eyeball their real browser is advisory and skipped in
  non-interactive runs.
- A book-level `CLAUDE.md` pointing at the meta files and rebuild commands.
- Final state.json stamp (all chapters `verified`, gates complete).

**GATE: maintenance.md exists; base-numbers table byte-identical across
outline.md / running-examples.md / maintenance.md; ≥1 scan-log entry; §P2.5
re-run after the last chapter edit; Tier-1 clean; Tier-2 PASS; retrospective
appended — before declaring done.**

## §Update — the scan protocol

Run idempotently (one scan-log entry per run; regenerate — don't append — the
fragile-facts index). If `_meta/state.json` exists, use it for chapter lists
and gate history; a legacy book without one follows its own `maintenance.md`
protocol exactly as written — never retrofit.

1. Re-read `landscape-*.md` ⚠️ entries; re-verify each fragile fact via web.
2. For any changed base number: edit the canonical `outline.md` table →
   regenerate `running-examples.md` and the `maintenance.md` table from it
   (temp + atomic rename) → propagate into chapter bodies → re-run the §P3
   consistency + byte-identity checks. A crash mid-update is caught on the
   next run by the byte-identity assert.
3. Re-run §P3; re-run §P4 if load-bearing math/derivations changed; re-run
   §P4.5 for any instructional chapter whose explanatory content was
   rewritten (a value-only sync does not require it).
4. Append one dated scan-log line.

## §Post-reading feedback (offer, don't force)

After the reader finishes the book, optionally run a short menu interview
(chapters too shallow/unclear? labs actually done?) and fold the results into
the reader-profile source to calibrate future books.
