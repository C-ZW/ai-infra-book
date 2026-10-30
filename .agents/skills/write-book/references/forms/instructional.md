# Form contract — instructional

Textbook/handbook form: the reader is taught a capability, chapter by chapter,
with a fixed skeleton the linter enforces.

## Chapter contract

- **Skeleton:** every chapter carries the language pack's `skeleton_slots`
  headings, in order. Copy them verbatim from `lang/<code>.json` into the
  style guide, and pin ONE dialect variant per slot in
  `_meta/lint.config.json` (`skeleton_slots` override) so P3 enforces exactly
  what the book uses.
- **Depth:** ≥1 worked example with real numbers per chapter (a fenced block
  with actual values worked end-to-end — not a name-dropped formula). Decision
  frameworks over tool lists; no tool named without its mechanism.
- **Exercises:** every exercise section is followed by a worked-solution
  subsection, carries a difficulty marker and a time estimate (linted at
  ERROR via this form's lint fragment).

## Bridging contract (objective, fatigue-free analogies)

- No second-person / conversational bridging; technical
  mechanism-to-mechanism only (no everyday analogies).
- ≤1 analogy per chapter; explicit anchor + boundary (name the source
  concept, state where it holds and where it breaks); bridge at first
  mention; only bridge from concepts the reader is established to know.
- **"No bridge — taught directly" is an explicit, valid choice** for chapters
  with no strong structural analog and for the fade-out's final third.
- **Bridge Registry (in outline.md):** at most one bridge source per chapter;
  dedup globally so any one source bridges ≤3 times book-wide.
- **Fade-out schedule:** front third — external analogies sparingly (cap per
  1000 words); middle third — prefer cross-references to already-defined
  in-book concepts; final third — native vocabulary only. Caps are upper
  bounds: zero analogies is always allowed.
- P4 runs the bridging review on this form only; no-bridge chapters are
  exempt.

## Per-book blanks to fill in the style guide

- The pinned skeleton dialect (one variant per slot).
- Lab budget and lab conventions, if hands-on labs apply.
- The worked-example register (what counts as "real numbers" in this domain).
