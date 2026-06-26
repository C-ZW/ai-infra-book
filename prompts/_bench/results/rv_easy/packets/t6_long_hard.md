# Judge packet — task `t6_long_hard` (long/hard, tool)

## The task given to each candidate

> Add a --reverse flag to cli.py that reverses the order of the output lines. Add or update a test for it. Do not change unrelated behavior.

## What to reward / penalize

Full loop with conventions: add flag matching existing argparse style, reverse correctly, add a real test, RUN the tests to verify, and avoid touching unrelated behavior (e.g. keep --upper working). Penalize unverified changes or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=48.9s; answer_chars=734; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
Done. Tests pass (4/4) and `--reverse` works end to end.

- `cli.py:7` — `transform` gains a `reverse=False` param that reverses after the optional uppercase step.
- `cli.py:16` — registered `--reverse` flag, wired into the `transform` call.
- `test_cli.py` — added `test_reverse` and `test_reverse_with_upper`.

Default behavior is unchanged: `reverse` defaults to `False`, so existing callers and the no-flag path are untouched.

One edge worth naming: order matters in `transform` — upper runs before reverse, so `--upper --reverse` uppercases then flips. Output-line order is independent of casing, so the result is the same either way here; if you ever add an order-sensitive transform, should it run before or after the reverse?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=45.7s; answer_chars=784; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
Done. All 5 tests pass and the flag works end-to-end.

- `cli.py:7` — `transform` now takes `reverse=False`; reverses via `list(reversed(lines))`, which returns a new list and never mutates the caller's input.
- `cli.py:16` — registered `--reverse` (`store_true`) and pass `reverse=args.reverse` through.
- `test_cli.py` — added `test_reverse`, `test_reverse_with_upper`, and `test_reverse_does_not_mutate_input`.

`--upper` and passthrough behavior are unchanged. The order is upper-then-reverse, but since reversal acts on list order and upper acts per-line content, the two compose independently.

One edge case worth noting: `--reverse` reverses *line order*, not characters within a line — if you actually wanted `"abc"` → `"cba"`, that's a different feature. Which did you mean?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=37.8s; answer_chars=692; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 5 tests pass and the flag works end-to-end.

- `cli.py:7` — `transform` gained a `reverse=False` param; reverses via `list(reversed(lines))`, so it never mutates the caller's list.
- `cli.py:17` — registered `--reverse` (store_true) and threaded it through `main`.
- `test_cli.py` — added `test_reverse`, `test_reverse_does_not_mutate_input`, and `test_upper_and_reverse`.

Existing `--upper` and passthrough behavior is unchanged. One ordering decision worth flagging: with both flags, upper is applied *then* reverse (`["a","b"] → ["B","A"]`); if you intended reverse-then-upper the line content is identical either way, but I locked the order down in a test so it can't drift silently.
````
