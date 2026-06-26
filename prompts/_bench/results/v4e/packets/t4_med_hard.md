# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=22.8s; answer_chars=139; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Bug was `hours + minutes` on line 14 — missing the `* 60` factor. `'1h30m'` returned `31` instead of `90`. Fixed to `hours * 60 + minutes`.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=24.4s; answer_chars=413; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Bug was `hours + minutes` instead of `hours * 60 + minutes` — `'1h30m'` was returning 31 instead of 90. Fixed at `utils.py:14`.

> **Probing question:** What should `parse_duration` return for `'0h0m'`, `'0m'`, or an empty-hours-only string like `'h30m'`? The regex allows both groups to be absent simultaneously (matching the empty string), and `'h30m'` won't match at all — are those edge cases handled to spec?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=23.1s; answer_chars=139; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
The bug was on line 14: `hours + minutes` → `hours * 60 + minutes`. `'1h30m'` now returns `90`, and `'45m'`/`'2h'` still return `45`/`120`.
````
