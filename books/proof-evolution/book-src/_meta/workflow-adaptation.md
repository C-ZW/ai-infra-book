# Workflow adaptation record

Date: 2026-10-06
Reference: `.claude/skills/write-book/SKILL.md`, engine v3, repository base commit `3bd1c08c3c72b6d12a71cbde572a5c2f0642d983`.

The user requested a complete book followed by a pull request and explicitly allowed improving parts of the months-old skill that no longer fit. This record distinguishes retained quality requirements from environment-specific execution changes. It does not edit the shared skill or claim that legacy gates ran.

| Legacy instruction | Execution for this book | Reason / evidence to retain |
| --- | --- | --- |
| Calibrate language and stop for outline approval | Use repo language zh-TW and narrative form; author a full outline and continue under the user's end-to-end instruction | No separate outline approval was obtained; do not fabricate one in state.json |
| Scan external personal profile directory | Use only the current request and project writing conventions | No private profile is required for this general-audience book |
| Run sibling `../tools/md-reader` toolchain | Provide book-local reproducible build/validation scripts | Sibling tooling is outside this available repository snapshot; do not claim those tools were run |
| Workflow tool chapter fan-out | Use available collaboration agents with the repository's chapter-writer template; assign disjoint chapter batches | Each chapter still follows the template's read, source, scope, and atomic-write requirements |
| Three model-family verifier panel | Independent reviewer agents, explicit mathematical recomputation, primary-source checks and deterministic validation | Same-model review is not cross-model consensus; legacy Tier-2 remains recorded as not run |
| Register in sibling profile/books.json and regenerate root shelf | Use a unique book-local reader config and deliver reader/source links through the PR | Do not hand-edit generated bookshelf.html or claim an unavailable registry was updated |
| Append retrospective rules to shared skill | Record this run's lessons in this book's metadata | Updating the global skill is outside the requested book change |

Retained: complete chapter manifest, one argument per chapter, Traditional Chinese prose, source provenance, explicit theorem assumptions, canonical examples, independent critique, reconciliation after fixes, generated reader, checks for broken links/citations, static reader integrity validation, and honest limitations. Actual browser rendering is a separate check and was not run because Chromium is unavailable.

This is a deliberately adapted workflow, not a claimed PASS of the original cross-provider P4 gate. The PR must describe the actual validation and any unresolved limitations. No runtime or reviewer failure is converted into a content-verification success.
