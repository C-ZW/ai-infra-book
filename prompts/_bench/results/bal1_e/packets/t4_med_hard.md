# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=30.5s; answer_chars=594; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Bug: `return hours + minutes` should be `return hours * 60 + minutes`. `'1h30m'` was returning `31` (1+30) instead of `90`. All three cases now pass.

> **Dangerous unhandled case:** the regex `(?:(\d+)h)?(?:(\d+)m)?$` matches the empty string — both groups optional. `''` after `.strip()` is caught by the `not s` guard, but a string of spaces alone passes `not s` only after stripping, which is fine. However, a string like `'30'` (no unit) silently matches with both groups `None` and returns `0` instead of raising. Worth deciding whether bare numbers should be an error or assumed minutes.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=24.0s; answer_chars=104; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Bug was `hours + minutes` → `hours * 60 + minutes` on line 14. `'1h30m'` was returning 31 instead of 90.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=21.4s; answer_chars=114; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
`return hours + minutes` → `return hours * 60 + minutes`. The hours were never converted to minutes before adding.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=21.6s; answer_chars=204; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
The bug was on line 14: `hours + minutes` should be `hours * 60 + minutes`. The hours were never converted to minutes before addition, so `'1h30m'` returned `31` instead of `90`. All three cases now pass.
````
