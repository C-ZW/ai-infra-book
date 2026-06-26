# Judge packet — task `h2_redherring_bug` (medium/hard, tool)

## The task given to each candidate

> test_aggregate.py fails: user 1's total should be 30 but comes out wrong. Fix it.

## What to reward / penalize

Root cause vs symptom: the real bug is in summarize() — user_id arrives as both int 1 and str '1', so a user's spend is split across two dict keys. The correct fix normalizes the key (e.g. str(uid)) in summarize. A weak fix patches top_user or the test, or special-cases the symptom, leaving the underlying key-collision. Reward understanding-before-acting and a verified fix (tests run); penalize symptom-patching, try/except masking, or editing the test to pass.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=26.3s; answer_chars=191; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The bug was in `aggregate.py:5` — `user_id` was used as-is, so int `1` and string `"1"` landed in separate buckets. Normalizing to `str()` at ingestion merges them correctly.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=27.4s; answer_chars=216; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix is one line in `aggregate.py:6`: `uid = str(e["user_id"])` normalizes the id before using it as a dict key, so `1` and `"1"` from the two upstream sources collapse into the same `"1"` bucket.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=40.8s; answer_chars=444; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. One-line fix in `aggregate.py:5`: `uid = str(e["user_id"])` — coerces int/str variants of the same ID to a single canonical key before accumulating.

> ⚠️ Probing question: what happens if `user_id` is `None` or a dict (malformed event)? `str(None)` becomes the literal string `"None"` and silently groups all null-ID events together — is that the intended behavior, or should the function raise on invalid IDs at the boundary?
````
