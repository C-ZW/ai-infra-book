# Form contract — narrative

Deep-read form: essays a reader reads linearly for understanding, not a
reference they consult. One theme per chapter, developed fully.

## Chapter contract

- **One theme per chapter**, developed as continuous prose. NO fixed section
  skeleton — a chapter's internal structure serves its argument. (A
  six-slot template read as a cheat-sheet is precisely what this form
  forbids.)
- **Zero filler:** every paragraph either advances the theme or is cut. No
  summary-of-what-you-just-read sections, no padding transitions.
- **Cross-references are still mandatory:** each concept is defined in
  exactly one chapter; later chapters point back (P2.5 enforces this).
- **Depth floor still applies** (the linter's per-chapter depth check stays
  ON). Worked examples appear where the argument needs them (WARN-level, not
  required per chapter).
- **No bridging regime:** the bridging contract, Bridge Registry, fade-out
  schedule, and P4 bridging review do not apply to this form.
- Load-bearing claims (numbers, derivations, historical facts) are still
  Tier-2 verified — narrative is not a license for unchecked claims.

## MANDATORY per-book pin: `chapter_globs`

Narrative books often use topic-named files (`alerting.md`, not `ch07.md`).
If `chapter_globs` doesn't match the book's real naming, the linter silently
classifies every chapter as non-chapter content (skipping depth checks) and
Tier-2 finds ZERO chapters — the book passes both gates vacuously. Set
`chapter_globs` (and exclude non-chapter files via `appendix_globs`) in
`_meta/lint.config.json` at P1; P3's chapter-count assert is the backstop.

## Per-book blanks to fill in the style guide

- Reader register (specialist / general — a popular-audience book is this
  form with register "general").
- The chapter-arc principle (what orders the chapters: chronology, dependency,
  escalation…).
