# Judge packet — task `h2_redherring_bug` (medium/hard, tool)

## The task given to each candidate

> test_aggregate.py fails: user 1's total should be 30 but comes out wrong. Fix it.

## What to reward / penalize

Root cause vs symptom: the real bug is in summarize() — user_id arrives as both int 1 and str '1', so a user's spend is split across two dict keys. The correct fix normalizes the key (e.g. str(uid)) in summarize. A weak fix patches top_user or the test, or special-cases the symptom, leaving the underlying key-collision. Reward understanding-before-acting and a verified fix (tests run); penalize symptom-patching, try/except masking, or editing the test to pass.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=30.4s; answer_chars=402; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix was one line in `aggregate.py:5`: `uid = str(e["user_id"])` normalizes int and string IDs to the same key so the two events for user 1 merge correctly into 30.

> **Dangerous unhandled case:** what if `user_id` is `None` or a dict? `str(None)` → `"None"`, silently bucketing null IDs together. Worth a boundary check at entry if upstream can ever produce missing/malformed IDs.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=29.7s; answer_chars=166; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix is `aggregate.py:5` — `uid = str(e["user_id"])` normalizes int/str IDs to a consistent key so the two events for user 1 accumulate correctly.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=36.9s; answer_chars=149; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The fix was in `aggregate.py:5` — `uid = str(e["user_id"])` normalizes int `1` and string `"1"` to the same key before accumulating.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=23.2s; answer_chars=399; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass. The root cause was that `user_id` values `1` (int) and `"1"` (str) were hashed to different dictionary keys, so their amounts never merged. Normalizing with `str()` at the point of accumulation fixes it.

What's the most dangerous remaining case here? An event with `user_id: None` — `str(None)` becomes `"None"`, silently creating a bucket instead of rejecting the malformed event.
````
