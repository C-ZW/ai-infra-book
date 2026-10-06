# Narrative revision workbench

## Status — 2026-10-06

Reader feedback: the manuscript does not read like a complete story, lacks flow, and is difficult to understand. PR #1 is now a draft. The initial manuscript is not accepted as publication-ready merely because its technical checks passed.

`narrative-sample.md` contains a rewritten opening and three consecutive sample chapters. It is an editorial alternative, not a replacement for `book-src/`, not a new complete edition, and not included in the production reader manifest. The full eighteen-chapter manuscript and its generated reader remain unchanged.

## Diagnosis from the initial manuscript

The opening chapter combines an example, multiple proofs, qualifications about generality, diagram reliability, logical implication, testimony, and historical method. Individually defensible paragraphs interrupt rather than develop the reader's immediate question. The outline often lists coverage obligations instead of identifying the problem that makes the next chapter necessary. Defining a term at first use is insufficient when the reader has not yet encountered the need for it.

The original per-chapter minimum length is not an acceptance criterion for this sample. Keeping every chapter above a fixed character count would preserve the wrong constraint. Shortening alone is also insufficient: a successful rewrite must retain the decisive inferential steps.

## Proposed editorial contract

Begin with a concrete problem. Let an initially reasonable approach make progress, expose its limitation, and introduce a new method at the point where it becomes useful. Give the reader a consequential result before expanding the scope. Chapter transitions must inherit an unresolved question, not merely announce the next topic.

Put necessary theorem hypotheses next to the argument where they matter. Move tangential historiographical qualifications and alternative derivations to notes or designated supporting sections. This does not authorize fabricated dialogue, invented motives, false priority claims, missing proof steps, or treating conceptual succession as historical transmission.

Use one central case per chapter unless a second case performs a necessary contrasting role. Introduce notation after the operation it abbreviates is understood. A final statement of limitations must not repeatedly restart the chapter after its main result.

## What this sample changes

- Chapter 1 follows one stone arrangement from calculation to a reusable reason, then asks how that reason can survive its speaker.
- Chapter 2 carries the square into a surviving tablet, contrasts a retained value with a retained procedure, and leaves open whether a sufficiently good approximation can become an exact fraction.
- Chapter 3 answers that question through the square-root-of-two contradiction, then makes dependency ordering concrete through the opening construction in Euclid.

The sample defers the second odd-sum proof, the detailed square-root interval estimate, the iterative approximation algorithm, and the full prime-infinitude proof. Those topics are still available in the unchanged original manuscript. Before integration, the full outline must explicitly retain, relocate or remove each item; silently leaving cross-references and baseline ownership pointing to deleted explanations is not acceptable.

## Scope of checks

The sample's arithmetic examples were recalculated, including the exact rational identity for the tablet value. Finite regression checks do not constitute universal proofs. General arguments were reread by the author; no independent reviewer or cross-provider gate was run for this sample.

The conversation's standalone HTML rendition was checked for unique IDs, resolved local anchors and absence of external rendering dependencies. Chromium rendered injected HTML with networking disabled at desktop and mobile widths; chapter anchors and footnote return links worked, with no horizontal overflow or page errors. This was a `set_content` render check, not a `file://` navigation test. That HTML is a sample delivery, not the repository's production reader.

Historical sources and their access limitations were carried forward from the initial manuscript, not newly reverified. The sample says so in its notes. Initial full-book check reports and review hashes certify only their recorded initial files; they must not be presented as validation of the sample.

## Before replacing the production manuscript

Agree on the desired reading experience from a continuous sample. Rebuild the full chapter arc, including the relationship between mathematical proof and empirical evidence. Then rewrite and read sequentially, reconcile deferred material and cross-references, obtain fresh factual/argument review, rebuild the reader, and rerun the applicable production checks. A successful build is not evidence that a reader can follow the story.
