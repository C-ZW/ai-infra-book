# Book maintenance

Traditional Chinese narrative nonfiction. Source: `book-src/`; generated reader: `web/index.html`. Read `_meta/maintenance.md`, `_meta/style-guide.md`, and the affected entry of `_meta/outline.md` before edits. `_meta/chapter-manifest.json` is the independent chapter list.

## Scope and publication state

The eighteen-chapter manuscript is still an editorial draft. `editorial/narrative-sample.md` is an alternative opening and three chapters, not an integrated edition. Read `editorial/README.md` before integration. Prose remains primary; a figure must clarify a specific relationship, not decorate the page. Technical test success is not evidence of reader comprehension.

## Retention policy

Keep the eight files under `_meta`: outline, style guide, dated fact baseline, canonical running examples, maintenance, chapter manifest, lint config, and `verification-report.md`. The last file is the single consolidated review record, including findings, dispositions, sources and unresolved limitations. Do not commit per-agent transcripts, hashes of every review, debug dumps or redundant state snapshots. Temporary outputs belong in `.review-output/` and are ignored. Prior detailed reports remain in Git history; do not rewrite history to remove them.

## Content and review

Preserve hypotheses, domains, evidence provenance and distinctions between proof, empirical support, historical reconstruction and author announcements. A cold review starts a new agent session, supplies only assigned manuscript and neutral reader criteria, and excludes prior conversation, author justification and earlier findings. Track actual coverage; missing content and failed tools are not PASS. Independently check proposed corrections; a reviewer can be wrong. Record the model/service and snapshot honestly, without claiming cross-provider certification.

Edit the baseline only in outline.md, then copy it byte-for-byte to running-examples.md and the marked maintenance block. Do not lower a depth gate silently to accommodate a future narrative rewrite: revise the contract and tests explicitly.

## Build

From this directory:

```sh
node scripts/build-reader.mjs
node scripts/verify.mjs --json
node scripts/browser-smoke.mjs --json
```

See `scripts/README.md` for dependencies and scope. Never edit generated HTML or the root bookshelf by hand. Code, configs and validation logs use English; book prose and UI use zh-TW. Keep reader ID `proof-evolution-2026` unique. After substantive edits, re-review affected arguments, rebuild, test and update the consolidated report. Do not present historical checks as a new run.
