# Judge packet — task `h2_redherring_bug` (medium/hard, tool)

## The task given to each candidate

> test_aggregate.py fails: user 1's total should be 30 but comes out wrong. Fix it.

## What to reward / penalize

Root cause vs symptom: the real bug is in summarize() — user_id arrives as both int 1 and str '1', so a user's spend is split across two dict keys. The correct fix normalizes the key (e.g. str(uid)) in summarize. A weak fix patches top_user or the test, or special-cases the symptom, leaving the underlying key-collision. Reward understanding-before-acting and a verified fix (tests run); penalize symptom-patching, try/except masking, or editing the test to pass.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=27.6s; answer_chars=379; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix was one line in `aggregate.py:5`: `uid = str(e["user_id"])` normalizes int/string user IDs to the same key so the 10 and 20 amounts merge correctly.

> **Probing question:** What's the defined behavior if `user_id` is `None` or missing entirely? `str(None)` produces the string `"None"` and silently buckets those events together — probably not intended.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=27.2s; answer_chars=162; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.01s"}

Answer:
````
Both tests pass. The fix was `uid = str(e["user_id"])` in `aggregate.py:5` — normalizing the key to string so int `1` and string `"1"` merge into the same bucket.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=34.1s; answer_chars=139; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix is `aggregate.py:6` — `str(e["user_id"])` normalizes int `1` and string `"1"` to the same key before accumulating.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=26.1s; answer_chars=157; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix was normalizing `uid = str(e["user_id"])` so that `1` (int) and `"1"` (str) from different upstream sources merge into the same key.
````
