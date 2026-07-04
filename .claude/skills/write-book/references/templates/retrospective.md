# Template — retrospective (P5)

You harvest this book run's new pitfalls so future runs (possibly by a
different model, with no memory of this session) don't re-hit them.
Parameters in your dispatch prompt:

- `book_src` — the finished book's source directory.
- `skill_dir` — the write-book skill directory.
- `run_notes` — pointers the main loop gives you: `_meta/verify-log.md`,
  gate re-run history from `_meta/state.json`, and anything it flagged
  during the run.

## Task

1. Read `<skill_dir>/references/pitfalls.md` — the existing rules. Your job
   is NEW entries only; never duplicate or rephrase an existing rule.
2. Read the run evidence: `_meta/verify-log.md` (adjudication outcomes,
   dismissed false positives, quarantines), `_meta/state.json` (chapters that
   needed >1 attempt or re-entered gates), and the `run_notes`.
3. Extract candidate pitfalls. A pitfall is a **reusable** symptom→rule pair:
   it must be actionable for a FUTURE book (tooling quirks, gate blind spots,
   prompt/CLI failure modes, formatting traps). Book-specific content issues
   (a wrong number, a weak chapter) are NOT pitfalls — those live in the
   book's own maintenance.md.
4. Be selective: 0 new entries is a valid result; 1–3 is typical. Quality
   over count.

## Return (structured output)

`entries`: a list of strings, each already in the pitfalls format
`- [YYYY-MM-DD] <symptom> → <rule>` (use today's date); empty list if
nothing qualifies. `rationale`: one line per entry on why it generalizes.
The MAIN LOOP appends them to pitfalls.md — you do not write to the skill
directory.
