# Maintenance record

## Canonical recurring examples

Edit outline.md first; the block below and running-examples.md must retain identical baseline bytes.

<!-- BEGIN BASELINE -->
| ID | Exact value and meaning | Owner / reuse |
| --- | --- | --- |
| ODD | 1 + 3 + 5 + 7 + 9 = 25; the first n positive odd numbers sum to n² for positive integer n | ch01 / ch18 / appendix-c |
| PRIME | 2 × 3 × 5 × 7 × 11 × 13 + 1 = 30031 = 59 × 509; the product-plus-one construction need not produce a prime | ch03 / ch18 |
| QUADRATIC | x² + 10x = 39; (x + 5)² = 64; real roots 3 and −13; positive-magnitude interpretation retains 3 | ch04 / ch05 |
| LIMIT | For f(x) = x² at x = 2, choose δ = min(1, ε/5) for ε > 0; 0 < ∣x − 2∣ < δ implies ∣x² − 4∣ < ε | ch06 / appendix-a |
| BAYES | Fictional population 10000, condition prevalence 1%, sensitivity 90%, false-positive rate 5%; expected true positives 90, false positives 495, posterior 90/585 = 2/13 ≈ 15.38% | ch12 / appendix-c |
| MULTIPLE | 20 independent true-null tests each with Type I error probability exactly 0.05: P(at least one false positive) = 1 − 0.95²⁰ ≈ 64.15% | ch13 / appendix-c |
| INTERACTIVE | Ideal binary challenges with per-round cheating bound 1/2 conditional on prior transcript, repeated 20 times: bound 2⁻²⁰ = 1/1048576 ≈ 0.00009537% | ch16 / appendix-c |
| PRIME_TEST | f(n) = n² + n + 41; all n = 0 through 39 give primes; f(40) = 1681 = 41² | ch01 / ch17 / appendix-c |
| APPROX | 1.414² = 1.999396 < 2 < 2.002225 = 1.415²; q = 30547/21600; q² = 2 − 791/466560000; 2/q − q = 791/659815200 < 0.0000012 | ch02 / appendix-c |
<!-- END BASELINE -->

## Fragile facts

Preserve the distinction between composition, manuscript, edition and reconstruction dates. Keep product-plus-one separate from primality; partial disk-model demonstrations separate from a complete model; logic completeness separate from theory completeness; effective axiomatization and arithmetic hypotheses explicit. Keep measurement uncertainty separate from error, and random estimation error separate from bias. Preserve Flyspeck's cross-system interface and the honest-verifier scope of the zero-knowledge example. AI results are dated reports, not interchangeable competition rankings or independent system audits.

Source-access limitations, earlier corrections and all current findings are consolidated in [verification-report.md](verification-report.md). That is the only retained review report, not a blanket correctness certificate.

## Update protocol

1. Read the style guide, outline and affected footnotes. Reopen primary sources for changed external claims.
2. Change canonical numbers in outline.md and regenerate the two baseline copies before changing citing prose.
3. Reconcile all 18 chapters, four appendices, links, definitions and reader manifest. Only the production manuscript is current: the alternative editorial sample was retired when the new opening was integrated. Preserve the appendix destinations of relocated derivations.
4. Run the documented build, deterministic and browser checks. Temporary JSON and screenshots go to `.review-output/`, not the source tree.
5. Obtain fresh-context review of changed arguments and reading continuity. Give reviewers only relevant manuscript and neutral criteria, not prior conclusions. Investigate findings before accepting corrections.
6. Record actual checks, access limits, dispositions and remaining work in verification-report.md. A failed or unexecuted check is not a pass. Do not retain per-agent output files or duplicate logs.

## Scan log

| Date | Mode | Scope / result |
| --- | --- | --- |
| 2026-10-06 | Initial book | 18 chapters, four appendices and reader; historical checks and limitations are summarized in verification-report.md. |
| 2026-10-06 | Retention cleanup and cold review | Removed 22 working-record files, preserved canonical baseline and build inputs, consolidated four new agent reviews; the manuscript remains a draft. |
| 2026-10-07 | Review-driven revisions | Implemented 28 dispositions, added five support figures and image checks; fresh review and actual verification are recorded in verification-report.md. |
| 2026-10-07 | Problem-led opening | Replaced introduction and ch01–ch03 in production; retained detailed derivations in appendices, retired the separate sample, added two recurring arithmetic baselines. New checks and actual review status are in verification-report.md. |
