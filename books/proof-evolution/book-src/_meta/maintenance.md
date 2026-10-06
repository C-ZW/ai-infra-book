# Maintenance record

## Canonical recurring examples

Edit the baseline in outline.md first, then regenerate this exact block and running-examples.md.

<!-- BEGIN BASELINE -->
| ID | Exact value and meaning | Owner / reuse |
| --- | --- | --- |
| ODD | 1 + 3 + 5 + 7 + 9 = 25; the first n positive odd numbers sum to n² for positive integer n | ch01 / ch03 / ch18 |
| PRIME | 2 × 3 × 5 × 7 × 11 × 13 + 1 = 30031 = 59 × 509; the product-plus-one construction need not produce a prime | ch03 / ch18 |
| QUADRATIC | x² + 10x = 39; (x + 5)² = 64; real roots 3 and −13; positive-magnitude interpretation retains 3 | ch04 / ch05 |
| LIMIT | For f(x) = x² at x = 2, choose δ = min(1, ε/5) for ε > 0; 0 < ∣x − 2∣ < δ implies ∣x² − 4∣ < ε | ch06 / appendix-a |
| BAYES | Fictional population 10000, condition prevalence 1%, sensitivity 90%, false-positive rate 5%; expected true positives 90, false positives 495, posterior 90/585 = 2/13 ≈ 15.38% | ch12 / appendix-c |
| MULTIPLE | 20 independent true-null tests each with Type I error probability exactly 0.05: P(at least one false positive) = 1 − 0.95²⁰ ≈ 64.15% | ch13 / appendix-c |
| INTERACTIVE | Ideal binary challenges with per-round cheating bound 1/2 conditional on prior transcript, repeated 20 times: bound 2⁻²⁰ = 1/1048576 ≈ 0.00009537% | ch16 / appendix-c |
<!-- END BASELINE -->

## Fragile facts and evidence boundaries

- Historical dates: keep composition, manuscript witness, edition, translation and reconstruction distinct. Preserve the conservative Rhind dating; do not collapse conflicting catalogue/edition dates into invented precision.
- ch03: product-plus-one is not always prime; retain the separate prime-divisor argument.
- ch07: a disk image or spherical picture does not by itself verify every axiom; preserve the relative consistency background.
- ch08/ch09: keep logic completeness distinct from theory completeness and preserve effective axiomatization, consistency, arithmetic strength and standard provability conditions.
- ch11/ch13: measurement uncertainty is not identical to realized error; random estimation error is not automatically statistical bias; experimental evidence remains conditional on design and auxiliary assumptions.
- ch14/ch15: four-color announcement/publication/formalization dates differ; Flyspeck uses multiple systems with an explicit interface, and this book did not rebuild those large projects.
- ch16: the displayed simulator is an honest-verifier demonstration unless a stronger theorem is explicitly cited; soundness error is not a general secrecy guarantee.
- ch17: snapshot cutoff 2026-10-06. Selected 2024/2025 events are not an exhaustive ranking. Keep natural-language scoring distinct from formal checking, human translation from automated lemma generation, and solution judging distinct from system/process validation.
- Current project documentation URLs may evolve. Prefer pinned publications for historical claims and recheck live documentation before describing a version-specific implementation.

## Update protocol

1. Read style-guide.md, the affected outline entries and chapter footnotes before editing.
2. Reopen the primary source for changed factual claims; record actual access limits and avoid replacing an original source with a summary silently.
3. If a recurring value changes, edit outline.md first and regenerate baseline copies, then update each citing chapter and appendix.
4. Reconcile all 18 ID/file pairs, footnotes, local links and terminology; compile source index from the actual final manuscript.
5. Run the book-local deterministic gate, arithmetic checks, focused tooling tests, reader build and output checks. See scripts/README.md for commands.
6. Obtain independent review of changed arguments and record findings and resolutions. Same-model review is not an original cross-provider Tier-2 PASS.
7. Run browser-smoke.mjs where Chromium/Playwright is available. Record a missing browser as not run, not as visual validation.
8. Rebuild generated HTML after the last content edit, then update verification-report.md and one dated scan entry. Never hand-edit reader output or root bookshelf.html.

## Scan log

| Date | Mode | Scope | Result record |
| --- | --- | --- | --- |
| 2026-10-06 | Initial full book | 18 chapters, 4 appendices, preface and offline reader | See verification-report.md and state.json for the final actual checks and independent review outcomes. |
