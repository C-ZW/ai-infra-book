# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=32.0s; answer_chars=139; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Bug: `return hours + minutes` was adding raw hour and minute counts together. Fixed to `return hours * 60 + minutes`. All three cases pass.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=21.1s; answer_chars=196; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
The bug was on line 14: `hours + minutes` was missing the `* 60` multiplier, so `'1h30m'` returned `31` instead of `90`. Fixed to `hours * 60 + minutes`. All three cases now return correct values.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=26.4s; answer_chars=103; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
`return hours + minutes` → `return hours * 60 + minutes`. Hours were not being converted before adding.
````
