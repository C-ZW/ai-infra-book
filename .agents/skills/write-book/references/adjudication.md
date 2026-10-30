# Adjudication protocol (P4)

Rules for resolving Tier-2 verifier findings (every ❌ `incorrect`, every ⚠️
`imprecise`). Implemented by `scripts/p4-adjudicate.js`; this file is the
normative spec. Core principle: **the executor's (or any single agent's) own
recomputation is never the final authority for dismissing a finding.**

## Per-finding flow

1. **Arbiter** (Claude agent, session model; `templates/arbiter.md`)
   recomputes the claim closed-book from the chapter +
   `_meta/running-examples.md` baseline. No browsing. Output:
   `{agrees_with_verifier, correct_value, confidence, reasoning}`.

2. **Arbiter agrees** the book is wrong → a fix agent edits the chapter.
   If the value is a base number, it edits the `outline.md` table FIRST and
   regenerates the copies (pitfalls rule 8), then the chapter body.
   Outcome: `fixed`.

3. **Arbiter disagrees** (thinks the book is right) → never dismiss on that
   alone:
   - Finding flagged by **≥2 families** (FAIL-grade): a lone arbiter never
     mechanically overrules two independent families. Outcome: `quarantined`
     + escalation entry. No vote.
   - Flagged by **1 family**: run a **tiebreaker** — an agent that wraps ONE
     panel CLI via Bash whose family is **neither the flagging family nor
     the writer family** (writer = anthropic ⇒ flagger openai → tiebreak
     google via `agy`, flagger google → tiebreak openai via `codex exec`),
     with a claim-specific closed-book recompute prompt (quote the claim, the
     chapter's stated value, the verifier's proposed value; ask which is
     correct; require a final JSON verdict line).
     - Tiebreaker: book wrong → fix agent → `fixed`.
     - Tiebreaker: book correct → `dismissed` (tiebreak record attached).
     - Tiebreaker inconclusive / CLI failure → `quarantined`.

4. **Logging** — every finding appends one block to `_meta/verify-log.md`
   (written by the main loop from the script's returned records):

   ```
   ## [<date>] <chapter-file> — <outcome>
   claim: <claim>
   book value: <…>  verifier value: <…>  flagging families: <…>
   arbiter: agrees=<bool> conf=<…> — <one-line reasoning>
   tiebreak: <family>/<verdict> | n/a
   action: <edit summary | dismissed-with-concurrence | quarantined+escalated>
   ```

   A `dismissed` record MUST carry the tiebreaker's concurrence; a lone
   arbiter dismissal is invalid by construction.

5. **Rounds:** after fixes, re-verify the touched chapters
   (`--no-cache --chapters <fixed>`). At most **2 adjudication rounds**; then
   halt with the quarantine report. Non-interactive runs: "escalate" = exit
   with the report (claim, all verdicts, sources per finding).

6. **INCONCLUSIVE chapters are out of scope here** — a panelist
   erroring/timing out is a tool matter: the main loop retries those
   panelists once, then halts per §P4. Adjudication only handles conclusive
   findings.

7. **Source independence** (for facts, as opposed to derivations): distinct
   primary sources, not distinct models — two families citing one URL = one
   source. A major correction to the fact baseline needs two independent
   sources; single-source corrections are quarantined and escalated.
