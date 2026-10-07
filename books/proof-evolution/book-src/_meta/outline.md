# Outline and canonical baseline

Title: 人類證明方法的演化
Subtitle: 從計算、論證與實驗，到形式驗證與 AI
Form: narrative. Language: zh-TW. Planned chapters: 18.
Spine: 一個人提出理由，另一個人憑什麼接受？ Each chapter tracks the claim, admissible reasons, the checking procedure, and the remaining assumptions. Chronology is approximate and interwoven with a conceptual arc. Parallel traditions are not stages of one ladder.

## Part I — Reasons become public

### ch01 — 為什麼還要證明：把「我相信」變成可檢查的理由
File: ch01-why-prove.md
Goal: distinguish a true answer, persuasive testimony, evidence, and a valid proof. Develop odd-number sums from examples to a general structural reason; state assumptions, domain, and the difference between finding and justifying. Introduce the four-question spine with readable examples. Explain why diagrams and communities matter without deciding the whole history in advance. Include the scope choice of mathematical spine and adjacent scientific practices. Do not teach formal logic (ch08), statistical inference (ch12), or rehearse all later chapters.

### ch02 — 泥板與紙草：會算、可教與理由的痕跡
File: ch02-tablets-and-algorithms.md
Goal: read ancient computational documents without confusing surviving recipes with absence of reasoning. Discuss selected Babylonian and Egyptian examples, exact versus approximate calculation, recipe generality and school practices. Work the Babylonian square-root approximation or a well-sourced quadratic reconstruction. Explicitly distinguish historians' reconstruction from surviving wording; explain evidence limits. Do not invent an inventor of proof or a universal ancient mindset; Euclid belongs to ch03.

### ch03 — 希臘的演繹秩序：圖形、反證與公理
File: ch03-greek-deduction.md
Goal: explain Euclidean deduction as an organized public dependency structure. Discuss Elements, definitions/postulates/common notions and the role/limits of diagrams; distinguish Aristotle's account from actual mathematics. Fully prove infinitely many primes (Euclid IX.20, modern notation identified) and √2 irrationality with its assumptions. Emphasize that product-plus-one need not itself be prime. Do not treat Euclid as a modern formal system or claim sole origin of proof; formalization belongs to ch08.

### ch04 — 多條理由之路：中國、印度與伊斯蘭世界
File: ch04-plural-traditions.md
Goal: compare algorithm justification, commentary, geometric explanation, and inference without assigning civilization scores. Use Liu Hui's commentary on Nine Chapters (composition/date uncertainty separated), an Indian mathematical or logical source with correctly limited scope, and al-Khwarizmi's geometric quadratic reasoning. Work x² + 10x = 39 by completing the square, noting positive magnitude domain. Distinguish transmission from unsupported direct influence. Do not compress all traditions to “practical calculation”; later symbolic algebra belongs to ch05.

## Part II — New languages and new limits

### ch05 — 字母接手圖形：代數、座標與一般性
File: ch05-algebra-and-symbols.md
Goal: show what symbolic representation makes possible and what it can hide. Discuss selected Viète/Descartes-era transformations without single-inventor mythology. Revisit quadratic domain from ch04; work extraneous roots or division-by-zero as examples of conditions lost in transformations. Show coordinate reasoning with a specific circle/line or distance calculation. Distinguish discovery notation, proof and algorithm. Infinity/limits belong to ch06.

### ch06 — 把無限說清楚：窮竭法、微積分與極限
File: ch06-infinity-and-limits.md
Goal: explain why successful calculus operations raised new proof obligations. Use Archimedes' exhaustion, Newton/Leibniz without priority adjudication, and nineteenth-century limit rigor with carefully sourced scope. Fully prove limit of x² at 2 using ε–δ, explaining quantifier order; compare pointwise/uniform or a concrete interchanging-limit risk. Avoid claiming rigorous math only began in Europe in the nineteenth century; Kerala material may appear only with substantiated source. Foundational infinity and set theory belong to ch08.

### ch07 — 可以換一套公理嗎：非歐幾何與模型
File: ch07-axioms-and-models.md
Goal: shift from a single obvious space to axiom-dependent structures. Distinguish Euclid's parallel postulate, hyperbolic alternatives, models, and relative consistency. Use a concrete disk-model explanation or spherical comparison with the correct axioms; never present a sphere as a model of all Euclid's other axioms. Explain independence is relative to an axiom system and background mathematics. Physical geometry needs empirical evidence (ch11), full logical semantics belongs to ch08.

### ch08 — 證明成為研究對象：邏輯、集合與形式系統
File: ch08-logic-and-foundations.md
Goal: explain syntax/semantics, quantifiers, valid inference, proof checking, and set-theoretic restrictions. Discuss Frege, Russell's paradox, Hilbert with precise source-backed claims. Work the unrestricted-comprehension contradiction and a tiny formal derivation. Distinguish consistency, soundness, completeness of a logic, and completeness of a theory, preparing ch09. Do not pre-state incompleteness without hypotheses or equate Russell's paradox with all set theory collapsing.

### ch09 — 不能全部完成的計畫：哥德爾與圖靈
File: ch09-incompleteness-and-computation.md
Goal: state first/second incompleteness with effective axiomatization, consistency, sufficient arithmetic and usual coding conditions; separate Gödel original stronger assumption from later Rosser refinement if naming both. Explain diagonal self-reference as proof architecture, not merely liar paradox. Give a complete elementary diagonal argument for undecidability of halting under its assumption. Distinguish first-order logic completeness from arithmetic incompleteness. No “humans beat machines” or universal nihilism. Constructivity belongs to ch10.

## Part III — Different warrants for different questions

### ch10 — 證明也能是一項構造：見證、直覺主義與程式
File: ch10-construction-and-programs.md
Goal: compare classical existence and constructive witness without treating either as defective. Introduce mathematical induction with its base/step and well-foundedness, connecting it to recursion and distinguishing it from empirical induction (ch11). Give a constructive witness example. Develop the probabilistic method through a finite-graph cut whose size is at least half the edge count by expected-value averaging; this is deductive existence, not statistical evidence (ch12). The irrational-power existence example is optional and must respect its case split and known-value subtleties. Explain intuitionistic logic, excluded middle with proper scope, and propositions-as-types through a simple conjunction/function example. Do not claim every program terminates or every type system proves every proposition. Modern proof assistant details belong to ch15.

### ch11 — 當答案必須問自然：實驗、測量與反駁
File: ch11-experiment-and-evidence.md
Goal: distinguish deductive theorem from empirical warrant; avoid a single universal scientific-method recipe. Use an original experiment/account such as Boyle's air pump or Galileo with instrument, calibration, auxiliary assumption and public replication. Explain why a failed prediction may challenge a conjunction of assumptions and why that is not license to immunize theories. Distinguish observation, controlled experiment, model prediction and explanatory inference. Statistical thresholds belong to ch12; causal inference belongs to ch13. No present-day legal/medical advice.

### ch12 — 把不確定寫進理由：機率與統計推論
File: ch12-probability-and-statistics.md
Goal: explain chance as a formal model and uncertainty as inference; Bayes/Fisher/Neyman-Pearson differences without a winners' history. Fully work the base-rate toy example from the canonical table, explicitly fictional. Explain p-values, error rates, likelihood/posterior, and the role of design; no P(H₀|data) inversion or “nonsignificant = no effect”. Sampling models and prior sensitivity matter. Causality, replication, and selection belong to ch13.

### ch13 — 是它造成的嗎：因果、重複研究與公開檢查
File: ch13-causality-and-replication.md
Goal: explain counterfactual reasoning and limits of association through a constructed confounding example. Introduce randomization, potential outcomes and a minimal causal diagram in prose/table; mention assumptions behind observational identification. Differentiate reproducibility of computation and replication with new data (terminology attributed because usage varies). Explain preregistration, multiplicity and transparent data/code as aids rather than guarantees. Derive the 20-test toy false-positive calculation with independence explicitly stated. Deductive proof remains a distinct warrant.

## Part IV — Reasons at machine scale

### ch14 — 人看不完的證明：窮舉、四顏色與證書
File: ch14-computer-assisted-proofs.md
Goal: explain finite reduction + exhaustive computation and independent checking. Discuss four-color proof generations without confusing original computer proof and later formal proof, Boolean Pythagorean triples as a possible case with scoped numbers. Work a tiny SAT unsatisfiability/resolution certificate or exhaustive finite example with an explicit reduction. Distinguish a test on many instances from an exhaustive theorem. Checkers, certificates, search costs, hardware/software assumptions and human understanding all matter. Proof-assistant kernels belong to ch15.

### ch15 — 讓每一步接受檢查：證明助理與可信核心
File: ch15-proof-assistants.md
Goal: explain how an interactive assistant elaborates tactics to checked proof objects, with a precise trusted-base account and formalization gap. Use primary publications/docs on LCF, Coq/Rocq, HOL Light, Lean and a carefully selected large formalization. A small inference example suffices; runnable Lean is not required and unexecuted code must not be labeled verified. Explain library reuse, dependencies, axioms, admitted assumptions, versions and reproducibility. Do not claim kernel checking proves the intended informal statement or physical hardware. AI search is ch17.

### ch16 — 只檢查一點，也能有把握嗎：互動證明與零知識
File: ch16-interactive-and-zero-knowledge.md
Goal: explain computational verification as a protocol, separating completeness, soundness error, zero knowledge and knowledge extraction. Work a graph-isomorphism challenge protocol and explain simulator caveat (honest-verifier example unless stronger definition actually proved). Derive 2⁻²⁰ under the right repeated-challenge assumptions. Distinguish information-theoretic/computational guarantees and cryptographic assumptions. Briefly locate NP/IP/PCP without conflating them or giving imprecise complexity theorems. Avoid deployment/security recommendations or unverifiable “ZK proves truth without any information”.

### ch17 — AI 會找理由之後：搜尋、翻譯與驗證的分工
File: ch17-ai-and-proof.md
Goal: clearly distinguish informal language-model reasoning, neural-guided symbolic search, formal proof generation and automated checking. Use a dated, primary-source-verified snapshot (cutoff 2026-10-06): AlphaGeometry/AlphaProof, IMO 2025 systems or later verified research only if source supports it. Metrics always carry problem set, constraints, time/human assistance and whether checks are formal or human. Avoid claims of universal latest/best. Work an error-prone simple conjecture and show the translation/specification boundary. Human agreement and multiple models are not mathematical certification. No speculative predictions stated as accomplished facts.

### ch18 — 什麼理由值得接受：把證明的責任交代清楚
File: ch18-responsibility-of-proof.md
Goal: a substantive final argument, not a recap. Compare several live hypothetical disagreements (mathematical claim, simulation, empirical causal claim, AI-generated formal statement), showing what artifact and objection resolve each. Return to the odd-number example and product-plus-one misconception without re-teaching their full proofs. Explain expertise, institutions, peer criticism, accessibility and division of labor. Distinguish institutional decisions under finite resources from mathematical entailment; avoid a separate legal-standards digression. Do not import jurisdiction-specific law into the mathematical argument. End on an actionable ability to identify the claim, assumptions, checking path and residual uncertainty; no empty progress rhetoric.

## Canonical recurring examples

The table between the markers is authoritative. Copies in running-examples.md and maintenance.md are generated verbatim by the root editor. Fictional probabilistic examples are pedagogical values, not empirical data.

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

## Appendices compiled after chapters

- appendix-a-methods.md — method atlas: purpose, miniature argument, assumptions and failure modes, with chapter pointers.
- appendix-b-timeline.md — qualified chronology, terminology and further reading paths, with primary-source citations and no unsupported priority claims.
- appendix-c-worked-examples.md — complete selected calculations and counterexamples; explicitly original pedagogical examples; accompany a reproducible check script if appropriate.
- appendix-d-sources.md — curated bibliography and source-reading guide compiled from actual citations; no invented references.
