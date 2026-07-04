---
name: write-book
description: Generate a technical or instructional-nonfiction book on any subject, via a gated multi-agent pipeline — calibrate to a target reader, write meta files (style guide, outline, fact baseline), fan out chapters in parallel, run a two-tier quality gate (deterministic contract lint + cross-model re-derivation of load-bearing claims), and package into an offline reader. Use when the user asks to write, create, or update/rescan a book, handbook, textbook, guide, manual, or course.
---

# write-book — engine v3

A gated multi-agent pipeline for **technical and instructional nonfiction**
(textbooks, handbooks, guides, courses, reference works). NOT for
fiction/memoir: the quality gate is a deterministic contract linter plus
cross-model re-derivation of load-bearing claims, which only make sense for
expository material. The spine: calibrate → meta files → parallel chapter
fan-out → two-tier gate → package. v3 puts control flow in Workflow scripts
and judgment in authored artifacts; the executor follows this dispatch table —
it does not improvise.

**Prime rule: any situation not covered by these specs → halt and ask the
user. Never improvise past a gate; never soften a gate a tool enforces.**

**Workflow opt-in:** these instructions direct you to call the Workflow tool
in P2 and P4. That satisfies the Workflow tool's explicit-opt-in requirement
("the user invoked a skill … whose instructions tell you to call Workflow").
If the Workflow tool is unavailable, run the same prompt templates via
parallel Agent calls with the same schemas and retry limits; if subagents are
unavailable too, halt.

## Setup

Read ONE config source, precedence: `write-book.config.{json,yaml}` at the
project root, else a `## write-book` section in the project CLAUDE.md.
Recognized keys (all optional): `tools_path`, `book_root`, `book_src_layout`,
`default_language`, `profile_path`, `arbiter_model` (leave unset — arbiter
defaults to the session model). **If no config source exists, or a key you
need next (`tools_path` for P0.5, `book_root` for P0 step 7) is absent, halt
and ask the user for it — never guess a default.** Toolchain =
`lint_book.py`, `verify_book.py`,
`gate_book.py`, `check_diagrams.py`, `build_reader.py`, `build_shelf.py` under
`tools_path`. **Missing or non-runnable toolchain at P0.5 = halt with
diagnostics. There is no manual mode; the gates are the product.**

## Engine invariants

- Code, configs, comments, logs: English. Book content + reader UI: the
  book's chosen language.
- Generated artifacts (reader HTML, bookshelf) are never hand-edited.
- `_meta/state.json` is written ONLY by you (the main loop) at phase
  boundaries, via temp file + atomic rename. Agents report through structured
  output; they never touch state.json.
- Every sub-agent works from a prompt template under `references/templates/`;
  every template makes the agent read `references/pitfalls.md`. Never compose
  a writer/arbiter/reviewer prompt from scratch.
- Tool exit codes are blind to Tier-2 WARN: all verify-result handling parses
  `--json` output.
- **Profile material is calibration input ONLY.** The reader's personal
  history, employers, projects, or résumé never appear in book content unless
  the user explicitly requests it; concrete scenarios use generalized
  settings, not the reader's own systems.
- Reference-implementation notes (bundled reader): unique reader-config `id`
  per registry; build shelf before readers; CJK diagram alignment relies on
  the reader's `wrapCJK` mechanism — never `@font-face size-adjust`.

## P0 — Calibrate (interactive)

1. **Output language first** (selects the linter language pack + reader UI
   language; no pack → see phases.md §P0.5).
2. **Form** — `instructional` (six-slot skeleton, exercises, worked examples,
   bridging regime) / `narrative` (deep-read: one theme per chapter, no fixed
   skeleton, zero filler) / `reference` (entry-based concept map, outward
   framing). Contracts: `references/forms/<form>.md`. A popular-audience book
   = `narrative` + reader register "general".
3. Reader profile: `profile_path` is a DIRECTORY — scan every readable
   document in it (top level; do not assume any specific file such as a
   résumé exists) and distill the calibration inputs: target reader,
   assume-known vs teach-from-zero, goals, reader register
   (specialist/general). If the directory is absent, ask instead.
4. Subject + target capability; scope (chapter estimate); lab budget if
   hands-on labs apply.
5. PII/publishing stance if the book may be shared (default conservative).
6. Quote expected scale: ~1 writer agent per chapter, 3×chapters Tier-2 panel
   calls, adjudication agents ≈ findings, +3 agents/chapter teach-test
   (instructional); rough tokens + wall time.
   Modes: `outline-only` (stop after P1) | `full` | `update` (phases.md
   §Update).
7. Derive a unique `<slug>` — no collision with any existing
   `<book_root>/<slug>/` directory NOR any reader-config `id` in the shelf's
   book registry (reference bundle: the `books.json` the shelf builder reads;
   check both). Check the working TITLE against registry titles too — a
   colliding title forces a rename late (it has happened); catch it here.
   Then create `<book_root>/<slug>/`.

## Dispatch

| Phase | Spec | Program | Gate (hard) |
|---|---|---|---|
| P0.5 pre-flight | phases.md §P0.5 | Bash smoke tests | every tool runnable, else HALT |
| P1 meta files | phases.md §P1 + forms/ | — | user approves outline; recorded in state.json |
| P2 chapters | phases.md §P2 | scripts/p2-write-chapters.js | every planned chapter `written` |
| P2.5 reconcile | phases.md §P2.5 | Bash asserts | exactly 1 non-empty file per planned id |
| P3 Tier-1 | phases.md §P3 | gate_book.py + check_diagrams.py | exit 0 AND linted-chapter count == outline count AND base numbers reconcile |
| P4 Tier-2 | phases.md §P4 + adjudication.md | verify_book.py --json; scripts/p4-adjudicate.js | PASS, every WARN resolved, bridging review clear (instructional only) |
| P4.5 teach-test | phases.md §P4.5 | scripts/p4_5-teach-test.js | every chapter passes, or user-waived (instructional only) |
| P5 package | phases.md §P5 | Bash sequence | maintenance.md + byte-identity + smoke + render + retrospective |

All file paths above are relative to this skill's directory
(`references/…`, `scripts/…`). Full phase specs: `references/phases.md`.
Update/rescan runs `references/phases.md §Update`. After delivery, optionally
offer the post-reading feedback interview (phases.md §Post-reading).
