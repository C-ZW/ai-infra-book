---
name: write-book
description: Generate a personal book calibrated to the owner's profile, via a gated multi-agent pipeline (profile check, meta files, chapter fan-out, consistency pass, second opinion, reader packaging). Use when the user asks to write/create a book for themselves on any topic, or to update/rescan an existing book.
---

# write-book

Pipeline for producing personal books. The reader is always the owner; all
calibration comes from the profile hub. Process learned and validated on
`ai-infra-book` (2026-06).

## Paths (all relative to the current project root — never hard-code absolute paths)

Project root = the repo this skill lives in (resolve upward to the git root if
the session starts in a subdirectory).

- New books live in: `<project>/books/<slug>/` (each with its own CLAUDE.md;
  all books are kept inside the current project — owner's decision,
  2026-06-12; `books/tlaplus/` is the working example)
- Profile hub: `../profile/` (sibling of the project; read its README.md
  first — it defines freshness + interview + PII rules)
- Tools: `../tools/md-reader/`
- Registry: `../profile/books.json`; web entry (bookshelf): `<project>/bookshelf.html`
  (location set by the registry's `shelf_output` field; reader configs do NOT
  hard-code a shelf link — build_reader auto-links the nearest ancestor
  bookshelf.html, so build the shelf before the readers)

## Conventions (non-negotiable)

- Code/configs/comments/logs: English. Book content + reader UI: the book's language.
- Reader config `id` must be unique across `books.json` (localStorage namespace).
- Generated artifacts (reader HTML, bookshelf) are never hand-edited.
- Diagram rendering contract: CJK=2 columns is enforced by build_reader's
  `wrapCJK` span mechanism — never via `@font-face size-adjust` (WebKit
  ignores it on `local()` fonts; Safari breaks while Chrome looks fine, so
  Chrome-only verification is insufficient). See tools README.

## P0 — Calibrate (cheap, interactive)

1. Read all profile files. Apply freshness rules from profile README
   (`goals.md` is confirmed every run; stale files trigger a **diff
   interview**: menu-driven via AskUserQuestion, deltas only, <5 min).
2. **The first question of any book setup MUST be the output language**
   (繁體中文 / English / other), regardless of profile defaults.
3. Then confirm via menus: topic + target capability, scope (chapters
   estimate), lab budget if hands-on labs apply. PII policy comes from
   `profile/preferences.md` (currently: always allowed for personal
   books; re-confirm only if the book may be published).
4. Quote expected scale before proceeding (agents count, rough token cost,
   wall time). Modes: `outline-only` (stop after P1), `full`, `update`
   (run an existing book's maintenance scan protocol instead).

## P1 — Meta files (the book's DNA)

Create `<book>/book-src/_meta/`:
- `style-guide.md` — writing contract: reader profile (generated from
  profile hub: the "assume known / teach from zero" split comes from
  skills.md), language rules, mandatory chapter skeleton (bridge-in,
  failure-modes section, hands-on labs with cost tags, self-check,
  further reading), depth standards (≥1 worked example with real numbers
  per chapter, decision frameworks, no tool name-dropping without
  mechanism).
- `outline.md` — full TOC + per-chapter spec: goal, must-cover,
  must-NOT-cover (with pointer to owning chapter), bridge ideas, worked
  example idea, lab idea. Cross-chapter base numbers declared once.
- `landscape-<date>.md` — fact baseline: spawn a research agent with web
  access to verify the current state of every fast-moving claim area
  (versions, prices, hardware, project status), with source URLs and ⚠️
  on unconfirmed items. Chapters must treat this file as the fact anchor.

**GATE: present the outline to the user and STOP for approval before P2.**
This is the highest-leverage QA point; never skip it.

## P2 — Chapter fan-out

- One general-purpose agent per chapter, in parallel batches of ~6.
- Each agent prompt: read the three meta files first; obey scope
  boundaries; do 3-8 targeted web verifications for its own chapter;
  hedge unverifiable facts with a date stamp; write exactly one file.
- Appendices (labs index, glossary, cheatsheets) run AFTER chapters and
  compile from what was actually written (Grep the real sections).

## P3 — Consistency pass (coordinator, scripted where possible)

- Cross-chapter number consistency (the base-numbers table from outline).
- Language lint (no simplified-Chinese variants when zh-TW).
- Skeleton completeness per chapter (grep required section headers).
- `check_diagrams.py <book-src>` for ASCII diagram alignment (CJK=2 rule).
- Fix findings directly; record anything deferred.

## P4 — Second opinion + adjudication

- Have an independent model **with web access** review: structure gaps,
  spot-check ~8 fact-base claims, verify one worked example's math.
  (Lesson learned: a reviewer without web access produces confident false
  accusations — always grant web.)
- Adjudicate: a single source never overturns the fact baseline; require
  two independent verifications for major corrections. Record verdicts.

## P5 — Package + register

- `maintenance.md` in `_meta/`: fragile-facts index, base-numbers table,
  scan protocol with dated scan log, structural reminders.
- Reader config (`ui_lang` = chosen language, unique `id`) →
  `build_reader.py`; register in `books.json` (incl. profile_date used);
  `build_shelf.py`; open both for the user.
- **Render check (not just `check_diagrams.py`)**: screenshot at least one
  CJK-heavy boxed diagram through the built reader with headless Chrome
  (`--force-device-scale-factor=2`, navigate to `index.html#<chapter-id>`)
  and eyeball the box borders; then ask the owner to confirm one diagram in
  their actual browser. The source column math and the rendered result are
  separate failure domains (Safari vs Chrome font handling differs).
- Book-level CLAUDE.md pointing at the meta files and rebuild commands.

## Post-reading exit interview (offer, don't force)

After the owner finishes reading, run a 5-minute menu interview (which
chapters too shallow/unclear, were labs actually done) and write results
back to `profile/preferences.md` (+ bump `last_verified`).
