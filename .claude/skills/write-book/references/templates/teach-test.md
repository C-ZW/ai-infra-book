# Template — teach-test (P4.5, instructional form)

Three roles in one file; your dispatch prompt names which section you follow.
Purpose: measure whether a chapter actually TEACHES — a weak model that has
read only the chapter must be able to solve a near-transfer problem. Solver
failure ≈ the chapter explains at people who already understand.

## §Generator

Parameters: `chapter_path`, `chapter_goal` (from the outline entry),
`baseline_path` (`_meta/running-examples.md`), `skill_dir` (read
`references/pitfalls.md` first).

Read the chapter and its goal. Design ONE near-transfer problem:

- It must require the chapter's specific mechanism — anchor it to the
  chapter's own notation, running example, or base numbers with CHANGED
  values (e.g. the chapter sums 1..100 → the problem sums 1..200), so that
  generic pretrained knowledge without the chapter is NOT enough to answer
  in the chapter's terms.
- It must NOT be the chapter's own exercise, and must not be solvable by
  quoting a sentence — solving requires executing the taught method.
- State it in the book's language, self-contained (the solver sees ONLY the
  problem text and the chapter).

Return (structured output): `problem` (full text shown to the solver);
`expected_approach` (the method a taught reader would use — NEVER shown to
the solver); `pass_criteria` (checkable: correct final value(s) AND evidence
the chapter's method was executed, not just the answer stated).

## §Solver

Parameters: `chapter_path`, `problem`.

You are simulating a LEARNER. Read ONLY the chapter at `chapter_path` — no
other files, no web. Then solve the problem, showing every step. Use the
method the chapter teaches; if the chapter leaves you unable to proceed at
some step, say exactly where you are stuck instead of papering over it with
outside knowledge — your stuck-point IS the test signal.

Return (structured output): `solution` (your worked steps + final answer);
`used_chapter_method` (true only if your steps follow the chapter's taught
method); `stuck_points` (list of places the chapter's explanation was
insufficient; empty if none).

## §Judge

Parameters: `chapter_path`, `problem`, `expected_approach`, `pass_criteria`,
`solver_output` (the solver's structured result).

Grade the solver against `pass_criteria`: correct result AND the chapter's
method actually executed (`used_chapter_method` must be corroborated by the
steps, not just claimed). A wrong answer, a right answer reached by outside
knowledge, or material stuck-points = the CHAPTER failed to teach — the
verdict judges the chapter, never the solver.

Return (structured output): `passed` (boolean); `gaps` (what the chapter
failed to convey, one item per gap — actionable for a rewrite; empty when
passed); `reason` (one-line verdict justification).
