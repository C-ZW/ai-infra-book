# Judge packet — task `t6_long_hard` (long/hard, tool)

## The task given to each candidate

> Add a --reverse flag to cli.py that reverses the order of the output lines. Add or update a test for it. Do not change unrelated behavior.

## What to reward / penalize

Full loop with conventions: add flag matching existing argparse style, reverse correctly, add a real test, RUN the tests to verify, and avoid touching unrelated behavior (e.g. keep --upper working). Penalize unverified changes or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=50.3s; answer_chars=951; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
Done. All 3 tests pass and the flag works as expected.

- `cli.py:7` — `transform` now takes `reverse=False`, applied after `upper` via `list(reversed(lines))`.
- `cli.py:16` — registered `--reverse` (`store_true`), wired into the `transform` call at `cli.py:20`.
- `test_cli.py` — added `test_reverse`.

Default behavior is unchanged: with no flag, output order is identical to before.

One edge worth naming: ordering of `--upper --reverse` is fixed (uppercase then reverse), which is order-independent for these two ops, so no surprise there. The one assumption baked in — that the whole stream fits in memory — was already true of the original (`reversed` needs the full list), so this adds no new failure mode. If a future flag needed streaming, that's where reverse would force buffering. Should `--reverse` also have a CLI-level integration test (via `main`/stdin), or is the `transform`-level unit test sufficient for your suite's conventions?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=52.5s; answer_chars=1347; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
Done. All 5 tests pass and the CLI behaves correctly.

## What changed

**`cli.py`**
- `transform()` gained a `reverse=False` parameter that returns `list(reversed(lines))` — building a new list rather than mutating the caller's input (so it's safe regardless of how the caller reuses `lines`).
- Added `--reverse` as a `store_true` flag, passed through in `main()`.

**`test_cli.py`** — added three tests:
- `test_reverse` — the core behavior.
- `test_reverse_does_not_mutate_input` — guards the non-mutation failure mode.
- `test_upper_and_reverse` — confirms the flags compose (upper applied element-wise, then order reversed).

Existing `test_passthrough` and `test_upper` still pass, and the no-flag / `--upper`-only paths are byte-for-byte unchanged.

One ordering decision worth naming: when both flags are set, the output reverses the *already-uppercased* lines. Since `--upper` is element-wise it can't conflict with `--reverse`, so the two are independent and the result is the same either way — but if a future flag is order-*dependent* (e.g. `--sort` or `--dedupe`), the sequence in which `transform` applies operations will start to matter and these tests won't catch a wrong ordering. Do you want me to pin the operation order down with an explicit comment or a `--sort`-style precedence test now, before someone adds that next flag?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=42.2s; answer_chars=435; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/cli.cpython-313.pyc', '__pycache__/test_cli.cpython-313-pytest-9.0.3.pyc']; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
Done. Both pass.

- `cli.py:7` — `transform` gains a `reverse=False` param that reverses line order (applied after `--upper`, so each is independent).
- `cli.py:17` — registered the `--reverse` flag and threaded it into `transform`.
- `test_cli.py` — added `test_reverse` and `test_upper_and_reverse`.

All 4 tests pass; `--reverse` and `--upper --reverse` verified against real stdin. Existing passthrough/upper behavior is untouched.
````
