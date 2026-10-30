# Local book toolchain

This project-local implementation replaces the missing sibling directory
`../tools/md-reader`. Python 3.10+ is required. The six main commands use only
the standard library; model verification additionally requires authenticated
panel CLIs. No profile directory is read.

The reader and shelf templates were recovered from this repository's existing
generated HTML. They retain the paper theme, settings, search, CJK wrapping,
chapter navigation, shelf hiding/list controls and browser-local position.
The embedded marked v12.0.2 parser retains its MIT copyright notice.
The quality-check implementations are reconstructed, not recovered originals;
see their code and tests for the precise checks.

## Commands

Run from the project root:

```sh
python3 tools/md-reader/lint_book.py BOOK_SRC --lang zh-TW --json
python3 tools/md-reader/check_diagrams.py BOOK_SRC
python3 tools/md-reader/gate_book.py BOOK_SRC --lang zh-TW
python3 tools/md-reader/verify_book.py BOOK_SRC --writer-family openai --timeout 240 --json --out REPORT.json
python3 tools/md-reader/build_shelf.py
python3 tools/md-reader/build_reader.py web/book.config.json
python3 -m unittest discover -s tools/md-reader/tests -v
node tools/md-reader/tests/test_workflow.mjs
```

All tools support `--help`. Lint/gate/verify load `_meta/lint.config.json`
automatically if present; `--config FILE` overrides it. Lists replace lists
when configs are deep-merged. Book-specific `chapter_globs` must select the
actual chapter files. Metadata and appendices are excluded from chapter
counts. Zero chapters is an error. `depth_min` counts prose CJK characters,
excluding code and URLs; default floor: 2,500. Narrative and reference form
fragments disable instructional-only checks without disabling depth.
Vocabulary warnings require editorial judgment, not automatic replacement.

Tier 1 checks depth, required headings and order, solution/example markers,
language vocabulary and simple box widths. It does not prove examples are
correct or diagrams legible. Source accuracy, cross-references, base-number
identity and rendered visual inspection remain separate write-book gates.

## Independent verification

`panel.json` contains explicit family/command pairs. Commands are argument
arrays, never shell strings. `{prompt}` is substituted as one argument; when
absent, the prompt is sent on stdin. `{output}` names a temporary result file
for CLIs that write their final response separately. Other output goes through
strict JSON/schema validation. Each invocation runs in a temporary directory;
providers are instructed to use no tools and to modify no files.

The bundled commands select Google and Anthropic models explicitly via `agy`;
`codex` uses its configured OpenAI model. If you change a command, make sure
the configured family matches the actual underlying provider. A different
model name from the same provider is not an independent family. To check
availability/authentication with real calls:

```sh
python3 tools/md-reader/verify_book.py --smoke --timeout 45 --out /tmp/book-panel-smoke.json
```

Normal verification requires an explicit `--writer-family`. PASS requires
two conclusive families other than the writer's. Empty claims, malformed JSON,
timeouts, CLI errors and too few independent families cannot pass. Errors are
not cached. Successful panel responses are cached by provider command, prompt,
chapter, baseline and config hashes. `--no-cache` bypasses them; `--chapters`
selects exact filenames or stems, and rejects unmatched selections.
Optional `_meta/source-evidence/<chapter-stem>.md` notes are included in each
chapter's closed-book context and cache key. They must record actually read
source passages, not just the writer's assertions, and do not replace source
research or adjudication.

Inspect the report's `verdict`, not just the process exit code. WARN exits 0
for compatibility with the engine contract but requires adjudication before
publication. FAIL and INCONCLUSIVE exit 1. `gate_book.py --verify` only accepts
PASS and also requires `--writer-family`. Timeouts terminate the process
group, including CLI children. CLI diagnostics are not copied into reports.
Closed-book panels check reasoning; primary-source fact research remains
mandatory for historical claims.

## Registry and offline builds

`books.json` is project-local. Each book entry has `id`, `title`, and a `config`
path relative to the registry. The `shelf_output` path is also relative to the
registry. The builder rejects duplicate IDs/titles and missing manifest files.
Book configs use `groups` with ordered `files`, or `dir` plus `pattern`, all
relative to the config file. `output` is relative to that config. Keep IDs
globally unique because they namespace browser-local reading preferences.

Build the shelf before readers. `--registry FILE` selects another registry;
`--output FILE` produces a preview. With `inline_images: true`, Markdown image
paths become embedded data URLs; remote images fail an offline build. The
reader embeds its Markdown parser and requires no server or CDN. Unicode math
is supported; `math: true` fails explicitly because KaTeX assets are not
bundled. Do not declare KaTeX support until the renderer and fonts are vendored.

Generated readers and shelves are never edited by hand. Edit the source
Markdown/config/templates and rebuild. Existing books are not reverified just
because this toolchain is installed.
