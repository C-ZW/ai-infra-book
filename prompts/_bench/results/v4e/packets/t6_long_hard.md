# Judge packet — task `t6_long_hard` (long/hard, tool)

## The task given to each candidate

> Add a --reverse flag to cli.py that reverses the order of the output lines. Add or update a test for it. Do not change unrelated behavior.

## What to reward / penalize

Full loop with conventions: add flag matching existing argparse style, reverse correctly, add a real test, RUN the tests to verify, and avoid touching unrelated behavior (e.g. keep --upper working). Penalize unverified changes or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=12; wall=31.8s; answer_chars=319; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass. Changes made:

- `cli.py`: added `reverse=False` param to `transform()` — applied after `upper` so ordering is predictable — and added `--reverse` flag to the argparser, wired into `main()`.
- `test_cli.py`: added `test_reverse` (basic order reversal) and `test_reverse_with_upper` (flag combination).
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=32.9s; answer_chars=396; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass.

**Changes:**
- `cli.py`: added `reverse=False` param to `transform()` — applies `reversed()` after `upper` — and `--reverse` flag to the argument parser.
- `test_cli.py`: added `test_reverse` (order only) and `test_reverse_with_upper` (both flags together).

What happens if stdin is empty? `reversed([])` returns an empty iterator, so the output is correctly empty — no crash.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=30.2s; answer_chars=286; files_added=[]; files_modified=['cli.py', 'test_cli.py']; files_deleted=[]

Answer:
````
All 4 tests pass. Changes:

- `cli.py`: added `reverse=False` param to `transform()` (applied after `upper`), and `--reverse` flag to the argument parser.
- `test_cli.py`: added `test_reverse` and `test_reverse_with_upper` to cover the new flag in isolation and combined with `--upper`.
````
