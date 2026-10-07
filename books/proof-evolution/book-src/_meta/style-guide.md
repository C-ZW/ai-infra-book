# Writing contract

## Reader and form

The book is titled **人類證明方法的演化**, subtitled **從計算、論證與實驗，到形式驗證與 AI**. Language: Traditional Chinese, Taiwan usage. Form: narrative nonfiction; general but intellectually curious reader, comfortable with high-school algebra, no assumed logic, probability, programming, or history background. Explain every new technical idea before relying on it. Code, logs, and maintainer metadata are English; book prose and reader UI are zh-TW.

The central question is: **答案看起來沒錯，還缺什麼理由？** Use the problem-led movement in `books/scientific-method/book-src/README.md` and its opening chapters as a reference for reader experience, not as wording or factual authority to copy. A plausible intuition must face a concrete obstruction before its replacement is named. Start with the problem itself, not a definition or an anecdote pasted in front of an unchanged taxonomy. “Evolution” means interacting, branching methods and institutions; it does not mean inevitable progress through a single civilization ladder. Mathematical proof is the spine. Scientific evidence, statistics, and institutional judgment are explicitly adjacent practices with different warrants, never silently equated with deductive proof.

## Narrative contract, instantiated

- Each chapter follows an active question: an initially plausible approach, its particular limit, a better argument, and a consequence that makes the next question necessary. This is not a repeated heading skeleton. Short direct questions, ordinary second-person address and local worked reasoning are appropriate; invented historical dialogue, invented author motives and biographical personalization are not.
- Every paragraph must change the reader's understanding of the active problem. A true distinction is not sufficient reason to interrupt the argument. Put alternate derivations, extensive source qualification and secondary constructions in appendices with explicit working links. Keep load-bearing hypotheses in the main proof, where they are used.
- Define a concept in its owning chapter and link back from later chapters. A short recall is allowed when it prevents a reader from losing the argument.
- Every chapter has at least one fully developed concrete case; mathematical chapters work an example step by step, distinguishing explanation, proof sketch, and complete elementary proof.
- No per-chapter target length. The 2026-10-07 revision explicitly replaces the old 4,000-character floor with an 1,800-Han-character missing-content guard in config, code and tests. This guard is not a teaching or depth certificate; do not pad to meet it. Coverage, retained proof steps and reader comprehension are separate checks.
- No bridging regime, no compulsory exercises or laboratory work. Optional reader questions must receive enough discussion to be useful.
- Historical facts and theorem hypotheses still need scrutiny. Narrative freedom does not reduce evidentiary standards.

## Prose

Use direct, readable Traditional Chinese. Prefer 動詞 over 進行／加以 + abstract noun. Avoid formulaic translations such as 透過…的方式、對於…而言、存在著、作為一個. One paragraph develops one idea; a long argument should land in a short clear sentence. Pronouns must have an obvious referent. Use 軟體、程式、資料、機率、統計顯著、演算法、形式化、驗證器. Do not write the reader's employers, résumé, or private history. Historical quotations must be brief and sourced; avoid unattributed famous sayings. Hypothetical scenes are explicitly hypothetical, never fabricated historical dialogue.

## Sources

Browse for niche, historical, technical, and time-sensitive claims. Prefer primary texts in identified editions/translations, mathematical papers, official theorem-prover documentation, original empirical studies, archival collections, and research by historians who inspect the evidence. Popular summaries may locate a source but must not carry technical claims. Do not make priority claims (“the first”) without strong evidence; distinguish a surviving text from the origin of a practice. Distinguish manuscript composition, translation, publication, later reconstruction, and disputed dating.

Use chapter-prefixed footnotes, e.g. `[^ch03-euclid-ix20]`; define every citation at the chapter's end with author, work, year (or qualified date), section/proposition where possible, URL, and one short note about what it supports. Cite next to the claim, not only in a reading list. Do not target a source count. Preserve relevant primary citations for claims that remain, and move a citation with its supporting discussion; never add a historical digression merely to fill a citation quota. Paraphrase sparingly from each source; the book's connecting reasoning and worked examples should be original. Label modern reconstructions of historical arguments. Do not invent DOI, page numbers, source quotations, accessed pages, or evidence of independent verification.

Each writer also reports retrieved sources and uncertain claims to the main editor. No personal claims of seeing an original manuscript unless an actual facsimile was opened. Contemporary chapter snapshots use 2026-10-06 as the research cutoff; a source appearing after that date is excluded.

## Mathematical register and notation

Unicode mathematics only. No LaTeX delimiters (`$$`, `\(`), no HTML, no Mermaid in chapter sources. Short derivations may use a `text` fence. Longer visual comparisons use Markdown tables. Support figures must clarify a specific spatial or procedural relationship, without replacing the continuous prose. The five static SVG figures are generated by `scripts/build-figures.py`; use standalone Markdown image paragraphs with descriptive captions. Only passive SVG in `book-src/figures/` is accepted and embedded in the offline reader. No decorative figures or font files are bundled.

| Symbol | Meaning | Owning chapter |
| --- | --- | --- |
| n, k | Integer indices; state whether zero is included | ch01 |
| A ⇒ B | Conditional implication | ch08 |
| ¬A | Negation | ch08 |
| ∀, ∃ | Universal and existential quantifiers | ch08 |
| T ⊢ φ | φ is derivable in formal theory T | ch08 |
| T ⊨ φ | φ holds in every model of T | ch08 |
| ε, δ | Positive error bound and input tolerance | ch06 |
| P(A), P(A ∣ B) | Probability and conditional probability | ch12 |
| H₀ | Null hypothesis | ch12 |
| Y(1), Y(0) | Potential outcomes under two interventions | ch13 |
| p, q | State locally whether primes, probabilities, or group parameters | local |

Always state the domain and hypotheses of a theorem. A proof under axioms is not a proof that the axioms describe nature. Numerical experiment is not a universal proof. A checked formal theorem is not automatically a correctly modeled real system. Independence from one theory is not unprovability in every theory. Gödel's results do not prove human superiority to machines or that every truth is subjective. A p-value is not P(H₀ ∣ data). Zero knowledge is a defined simulation guarantee, not a universal secrecy claim. A natural-language AI answer is not kernel-checked just because another model agreed.

## Delivery

Chapter files are `chNN-slug.md`, with exactly one H1. Use relative cross-chapter links. Footnotes come last. No TODO, TBD, pending chapter, placeholder, or promised-but-unwritten section. Use atomic replacement for source files. Keep revision decisions and actual checks in the single `verification-report.md`; do not recreate per-agent reports or state snapshots. The editor owns consistency, appendix compilation, evidence reconciliation, and honest gate statuses.
