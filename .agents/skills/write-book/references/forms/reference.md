# Form contract — reference

Entry-based concept-map form (e.g. a field's concepts organized into domains,
multiple entries per file). The reader consults it; order within a part is
navigational, not narrative.

## Entry contract

- **Per-entry required slots, defined in the style guide** (not by the
  linter's chapter skeleton — that is OFF for this form). A typical entry:
  concept definition → the solution space it belongs to → what guarantees
  each option gives up / keeps → when to use which. Define the exact slot
  list per book in style-guide.md; P4's structural spot-check reviews against
  it.
- **Outward framing:** define concepts and trade-offs on their own terms.
  Never frame as reader-error correction ("you think X, but actually…" is
  banned phrasing).
- Each concept is defined in exactly one entry; other entries cross-reference
  it (P2.5 enforces).
- Load-bearing claims (guarantees, bounds, defaults, version facts) are
  Tier-2 verified like any other form.

## MANDATORY per-book pin: `chapter_globs`

Reference books almost never use `ch*.md` naming (files are per-domain or
per-part). Set `chapter_globs` to the book's real naming and exclude
non-entry files via `appendix_globs` in `_meta/lint.config.json` at P1 —
otherwise the linter and Tier-2 silently see zero chapters (vacuous pass).
P3's chapter-count assert is the backstop; for this form the assert compares
against the outline's planned FILE count.

## Per-book blanks to fill in the style guide

- The entry slot list (see above).
- Part/domain organization and the entry-ordering rule within a part.
- Reader register.
