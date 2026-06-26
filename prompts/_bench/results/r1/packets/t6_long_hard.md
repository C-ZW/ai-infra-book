# Judge packet — task `t6_long_hard` (long/hard, tool)

## The task given to each candidate

> Add a --reverse flag to cli.py that reverses the order of the output lines. Add or update a test for it. Do not change unrelated behavior.

## What to reward / penalize

Full loop with conventions: add flag matching existing argparse style, reverse correctly, add a real test, RUN the tests to verify, and avoid touching unrelated behavior (e.g. keep --upper working). Penalize unverified changes or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=50.8s; answer_chars=827; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
Done. Added `--reverse` to `cli.py` and tests in `test_cli.py`.

- `transform()` gained a `reverse=False` param that reverses lines via `list(reversed(lines))` — applied after `--upper`, and it returns a new list rather than mutating the caller's input.
- `main()` wires up the `--reverse` argparse flag and passes it through.
- Tests: `test_reverse` plus `test_reverse_does_not_mutate_input`; all 4 pass, and the e2e check confirms `--reverse` and `--upper --reverse` work.

The most dangerous unhandled case: `--upper` and `--reverse` compose order-dependently only if upper ever changed line *count* — it doesn't, so output is identical either way today. But if someone later adds a filtering transform (e.g. `--grep`), should `--reverse` run before or after that filter, and is that ordering contract written down anywhere?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=41.0s; answer_chars=1073; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass and the flag works end-to-end. Here's what I changed:

**`cli.py`**
- `transform()` gained a `reverse=False` param; when set, it returns the lines reversed. Applied *after* `upper`, though order is immaterial since reversing doesn't alter line content.
- Added `--reverse` argument (`store_true`) and threaded `reverse=args.reverse` into the `transform()` call.

**`test_cli.py`**
- `test_reverse` — confirms `["a","b","c"]` → `["c","b","a"]`.
- `test_upper_and_reverse` — confirms the two flags compose correctly.

Verified: default passthrough (no flags) and `--upper`-only behavior are unchanged.

One unhandled edge worth naming: `reversed()` materializes the whole input into memory before emitting anything — fine for typical stdin, but on an unbounded or multi-GB stream `--reverse` will buffer the entire input (the existing code already does this via the list comprehension, so this isn't a regression, just an inherited ceiling). Should `--reverse` carry a documented input-size assumption, or is streaming-scale input out of scope for this tool?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=51.5s; answer_chars=860; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
Done. All 4 tests pass and the flag works.

Changes:
- `cli.py:7` — `transform` now takes `reverse=False`, applying `list(reversed(lines))` (returns a new list, doesn't mutate the caller's input).
- `cli.py:17` — registered `--reverse` (store_true) and threaded it into the `transform` call.
- `test_cli.py` — added `test_reverse` plus `test_reverse_does_not_mutate_input` to guard against in-place mutation.

`--upper` behavior is untouched; the two flags compose (upper then reverse).

One unhandled edge worth naming: with empty stdin, `transform` returns `[]` and nothing prints — fine. But note ordering is fixed as upper-then-reverse; if a caller ever expected reverse-then-upper the output content is identical, so it doesn't matter here — should `--reverse` instead reverse the *raw* input before any other transform if more transforms are added later?
````
