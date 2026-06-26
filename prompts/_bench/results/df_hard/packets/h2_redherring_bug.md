# Judge packet — task `h2_redherring_bug` (medium/hard, tool)

## The task given to each candidate

> test_aggregate.py fails: user 1's total should be 30 but comes out wrong. Fix it.

## What to reward / penalize

Root cause vs symptom: the real bug is in summarize() — user_id arrives as both int 1 and str '1', so a user's spend is split across two dict keys. The correct fix normalizes the key (e.g. str(uid)) in summarize. A weak fix patches top_user or the test, or special-cases the symptom, leaving the underlying key-collision. Reward understanding-before-acting and a verified fix (tests run); penalize symptom-patching, try/except masking, or editing the test to pass.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=34.1s; answer_chars=306; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix was `uid = str(e["user_id"])` in `aggregate.py:5` — without it, int `1` and string `"1"` were separate dict keys, so the totals never merged.

What happens if a `user_id` is `None` or a float — should those also normalize to string, or should the boundary validate and reject them?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=39.4s; answer_chars=181; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix: `aggregate.py:5` — `uid = str(e["user_id"])` normalizes int/str IDs to a canonical string key before accumulating, so `1` and `"1"` map to the same bucket.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=29.7s; answer_chars=199; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.01s"}

Answer:
````
Both tests pass. The fix was in `aggregate.py:5` — coercing `user_id` to `str` before using it as a dict key, so integer `1` and string `"1"` from the two upstream sources merge into the same bucket.
````
