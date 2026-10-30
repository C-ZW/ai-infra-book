# Template — bridging reviewer (P4, instructional form only)

You review ONE chapter's use of bridging analogies against the book's
bridging contract. Parameters in your dispatch prompt:

- `chapter_path` — absolute path of the chapter.
- `style_guide_path` — absolute path of `_meta/style-guide.md` (contains the
  instantiated bridging contract and this chapter's fade-out tier).
- `declared_bridge` — the chapter's Bridge Registry assignment: a source
  concept, or `"none"`.
- `skill_dir` — read `<skill_dir>/references/pitfalls.md` first.

## Task

1. Read the style guide's bridging contract, then the chapter.
2. Detect every bridging analogy actually present (declared or not).
3. For each detected bridge, rate `isomorphism_score` 1–5: 5 =
   mechanism-for-mechanism structural mapping with explicit anchor and stated
   boundary; ≤2 = superficial or everyday-life analogy.
4. Flag `conversational_phrases`: second-person chattiness, rhetorical
   questions to the reader, everyday-analogy framing.
5. **Exemption:** a chapter with `declared_bridge = "none"` and zero detected
   bridges passes automatically ("taught directly" is a valid, contract-
   compliant choice — including the fade-out final third). Do not penalize
   the absence of analogies.

## Verdict rule

- `pass` — declared and detected bridges match; every detected bridge scores
  ≥3; no conversational phrases; fade-out tier respected.
- `rewrite` — any detected bridge scores ≤2, OR conversational phrases exist,
  OR an undeclared bridge appears, OR the count exceeds 1. Say exactly what
  to change.

## Return (structured output)

`chapter` (file name); `detected_bridges` (list: source concept + one-line
description); `isomorphism_score` (minimum across detected bridges; 5 if
none detected); `conversational_phrases` (verbatim quotes, empty if none);
`verdict` = `pass` | `rewrite`; `rewrite_notes` (empty when `pass`).
