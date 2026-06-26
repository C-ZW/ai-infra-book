# Judge packet — task `t6_long_hard` (long/hard, tool)

## The task given to each candidate

> Add a --reverse flag to cli.py that reverses the order of the output lines. Add or update a test for it. Do not change unrelated behavior.

## What to reward / penalize

Full loop with conventions: add flag matching existing argparse style, reverse correctly, add a real test, RUN the tests to verify, and avoid touching unrelated behavior (e.g. keep --upper working). Penalize unverified changes or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=28.6s; answer_chars=453; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass. Changes made:

- `cli.py`: added `reverse=False` param to `transform()` (reverses after uppercasing if both flags given), and `--reverse` flag to the argument parser.
- `test_cli.py`: added `test_reverse` and `test_reverse_with_upper`.

What's the most dangerous unhandled case here? Empty input — `reversed([])` is fine, but worth confirming that `list(reversed([]))` returns `[]` without error. It does; Python handles it gracefully.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=31.5s; answer_chars=476; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass. Changes made:

- `cli.py`: added `reverse=False` param to `transform()` (applied after `upper` so ordering is deterministic), and `--reverse` flag to the argument parser.
- `test_cli.py`: added `test_reverse` and `test_reverse_with_upper`.

What's the most dangerous unhandled case here? Empty input — `reversed([])` is fine in Python, but worth confirming the pipeline handles zero lines without blocking on stdin indefinitely if the caller never closes it.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=34.2s; answer_chars=314; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass. Changes:

- `cli.py`: added `reverse=False` param to `transform()` (applied after `upper` so ordering is deterministic), and `--reverse` flag to the argument parser.
- `test_cli.py`: added `test_reverse` and `test_reverse_and_upper` covering the new flag in isolation and combined with `--upper`.
````
