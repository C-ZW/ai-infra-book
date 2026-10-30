# Template — source-evidence repair and adjudication support

Use for a historical narrative's Tier-2 findings when the chapter cites
actually read sources but the closed-book panel lacks the relevant passages.
This does not dismiss findings or replace the P4 re-verification gate.

Parameters: `chapter_path`, `findings_path`, `baseline_path`, `evidence_path`,
`skill_dir`, `report_path`.

1. Read `references/pitfalls.md` and the arbiter template. For EACH finding,
   first apply that template closed-book to the chapter and baseline. Do not
   browse until these initial records are written to your report. Give each
   original finding its own ID and arbiter record. Missing external evidence
   is not proof that the historical statement is false: record the limitation
   explicitly. Do not dismiss an objection on your own authority.
2. Read the current evidence notes and actually retrieve/read the missing
   primary passages and relevant independent scholarship. Use the refutation
   frame of the fact-auditor template: try to find an incompatible reading.
   Clearly distinguish exact text, later recollection, scholarly
   reconstruction, and your own explanatory reasoning. A URL alone is not
   evidence. Respect quotation limits; prefer accurate summaries with precise
   passage positions and verified bibliography.
3. Return proposed prose fixes only where the wording is incorrect,
   overbroad, or its citation misleading. For an evidence-context omission,
   supply the missing evidence, not filler in the chapter. Never fabricate a
   statement that you read an inaccessible source. If you cannot establish a
   detail, propose removing or narrowing it.
4. Write exactly ONE structured JSON report at `report_path`, atomically.
   It contains `chapter_id`, `arbiter_records` (one per finding ID, with the
   arbiter schema), `evidence_markdown` (a complete expanded source dossier,
   including existing valid evidence), `proposed_edits` (exact old/new strings
   with reasons), and `unresolved` (finding IDs and reasons).
   Do not edit chapters, state.json, evidence files, or any other file.
   The main loop applies accepted repairs and logs every finding, then reruns
   reconciliation, Tier 1 and Tier 2. No finding is cleared by this report
   alone. Reports are supporting records; all original verdicts are retained.
