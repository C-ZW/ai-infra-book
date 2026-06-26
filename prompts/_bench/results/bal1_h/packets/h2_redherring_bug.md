# Judge packet — task `h2_redherring_bug` (medium/hard, tool)

## The task given to each candidate

> test_aggregate.py fails: user 1's total should be 30 but comes out wrong. Fix it.

## What to reward / penalize

Root cause vs symptom: the real bug is in summarize() — user_id arrives as both int 1 and str '1', so a user's spend is split across two dict keys. The correct fix normalizes the key (e.g. str(uid)) in summarize. A weak fix patches top_user or the test, or special-cases the symptom, leaving the underlying key-collision. Reward understanding-before-acting and a verified fix (tests run); penalize symptom-patching, try/except masking, or editing the test to pass.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=29.1s; answer_chars=448; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix was `uid = str(e["user_id"])` in `aggregate.py:5` — the int `1` and string `"1"` were hashing to different dict keys, so they accumulated separately instead of merging to 30.

> **Probing question:** what happens if `user_id` is `None` or missing from an event? `str(None)` silently produces `"None"` and it accumulates — should the boundary validate that `user_id` is a non-null int or string before it enters `summarize`?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=38.5s; answer_chars=338; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Fixed. `aggregate.py:6` — added `str()` around `e["user_id"]` so int `1` and string `"1"` merge into the same key `"1"` before accumulation.

One probing question: does anything downstream depend on the key type being int for some user IDs? If callers do `totals[1]` (int key) they'll now get a `KeyError` — worth checking all call sites.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=31.2s; answer_chars=128; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. `aggregate.py:5` — `uid = str(e["user_id"])` normalizes int and string IDs to the same key before accumulating.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=26.1s; answer_chars=412; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix was normalizing `user_id` to `str()` in `summarize` (`aggregate.py:5`), so int `1` and string `"1"` from the two upstream sources merge into the same key instead of creating separate buckets.

> **Failure mode to watch for:** any other call site that passes `user_id` as a key (e.g., for DB lookups) still sees a string — is that consistent with how downstream consumers expect the type?
````
