# Retrospective — 2026-10-06

This record is local to this book. It does not revise the repository's shared write-book skill or invent an approval that did not occur.

## What worked

An explicit eighteen-chapter manifest and a shared baseline made parallel authoring reviewable. Each author owned a disjoint batch; a different author then read the batch, attempted counterexamples and checked selected original sources. The root editor reconciled findings and maintained the shared state. Source-access limits were retained alongside conclusions rather than compressed into a blanket verification label.

Long-form chapters benefited from requiring a complete mathematical case, its assumptions and a failure mode. This produced substantive comparisons: a product-plus-one number need not itself be prime; a high-precision ancient value does not identify its generating algorithm; a formal theorem can still encode the wrong real-world requirement. The final chapter could reuse these responsibilities in new cases instead of summarizing eighteen headings.

## Lessons for a later run

1. **Separate dependency availability from functionality.** Resolving Playwright did not mean a Chromium executable existed. A real launch or explicit executable check must precede any claim about browser rendering. Static parsing, JavaScript syntax checks and visual inspection are separate results.
2. **Give every chapter its own anchor namespace.** Footnotes and duplicate headings otherwise collide in a single-file reader. Verify all generated IDs, outgoing fragments and repeated-reference backlinks, not just the source Markdown.
3. **Preserve the strength of the evidence label.** A paper and the same authors' project page are usually one originating report. Direct support for what a report says is useful, but does not establish independent replication or satisfy a stricter two-origin rule.
4. **Review after expansion and after corrections.** Chapter length is only a completeness check. The final reread must cover added paragraphs and confirm the final file digest; an earlier review cannot silently certify later material.
5. **Qualify competition and publication claims.** Event year, early publication, journal volume, time allowance, human translation and system audit describe different things. A compact comparison table should not erase those distinctions.
6. **Keep build tools portable and bounded.** Vendoring one existing MIT-licensed parser made this book reproducible without the absent sibling toolchain. It did not justify changing the shared skill, another book or the root generated shelf.
7. **Prefer reproducible corrections over ceremonial verdicts.** Small fixes to a summand, a subtracted quantity, a boundary case or a quantifier often improve a proof more than a broad PASS label. Preserve the exact issue, correction, reread and remaining limitation.

## Remaining opportunities

A later environment with Chromium can execute the included browser smoke script and record desktop, mobile, print and keyboard results. A separate human or genuinely different model-family review could broaden editorial independence. Neither is claimed in this run. Future AI chapters should be updated through the dated source protocol in `maintenance.md`, without retroactively changing the dates or scope of earlier case studies.
