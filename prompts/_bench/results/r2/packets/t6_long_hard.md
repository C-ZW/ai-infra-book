# Judge packet — task `t6_long_hard` (long/hard, tool)

## The task given to each candidate

> Add a --reverse flag to cli.py that reverses the order of the output lines. Add or update a test for it. Do not change unrelated behavior.

## What to reward / penalize

Full loop with conventions: add flag matching existing argparse style, reverse correctly, add a real test, RUN the tests to verify, and avoid touching unrelated behavior (e.g. keep --upper working). Penalize unverified changes or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=39.2s; answer_chars=844; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass and the flag works end-to-end.

Changes:
- `cli.py:7` — `transform` gains a `reverse=False` param that does `lines[::-1]` (new list, no mutation of the input).
- `cli.py:18` — registered `--reverse` (`store_true`) and passed it through in `main`.
- `test_cli.py` — added `test_reverse` and `test_reverse_with_upper`.

Existing `--upper`/passthrough behavior is untouched.

One edge worth naming: `--reverse` buffers all of stdin into a list before emitting (it already did, so no regression), but reversal makes buffering inherent — on an unbounded/streaming input this holds the whole stream in memory and emits nothing until EOF. Fine for files; worth knowing if anyone pipes a `tail -f`-style source into it. Should reversal apply before or after `--upper` if a future transform makes order observable (e.g. line numbering)?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=49.7s; answer_chars=1482; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass and the CLI behaves correctly.

## Summary

I added a `--reverse` flag to `cli.py` that reverses the order of output lines.

**`cli.py`**
- Extended `transform()` with a `reverse=False` parameter; when set, it reverses line order via `lines[::-1]` (a copy — it does not mutate the caller's list). It runs *after* `upper`, so the two flags compose cleanly.
- Registered the `--reverse` argument in `main()` and passed it through to `transform()`.

**`test_cli.py`**
- `test_reverse` — reverse on its own.
- `test_upper_and_reverse` — confirms the flags combine correctly (uppercased *and* reversed).

Verified: existing `test_passthrough`/`test_upper` still pass (default behavior unchanged), and the CLI produces correct output for `--reverse`, `--upper --reverse`, and the no-flag default.

One edge worth noting on the failure side: `transform` returns the input list reference unchanged when neither flag is set (existing behavior I preserved), but the `reverse` and `upper` paths both return fresh lists — so no aliasing surprise is introduced. The one case I did *not* add explicit handling for is non-string elements in `lines` (e.g. `None`), since `transform`'s contract is "lines of text" and the `--upper` path would already fail there today; I kept that behavior identical rather than change unrelated scope.

What's the most adversarial input you expect this to face — could anything upstream ever feed `transform` something that isn't a list of strings?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=46.2s; answer_chars=654; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
Done. All 4 tests pass and the flag behaves as expected.

- `cli.py:7` — `transform` now takes `reverse=False` and reverses via `list(reversed(lines))` (non-mutating, applied after `upper`).
- `cli.py:16` — registered `--reverse` (`store_true`) and passed it through in `main`.
- `test_cli.py` — added `test_reverse` plus `test_reverse_does_not_mutate_input` to lock in that the input list isn't mutated.

Default and `--upper` paths are untouched. One edge worth noting: empty stdin yields zero lines and `--reverse` correctly prints nothing — verified by the passthrough logic, not by a dedicated test. Want me to add an explicit empty-input test case?
````
