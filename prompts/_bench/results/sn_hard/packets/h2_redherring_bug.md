# Judge packet — task `h2_redherring_bug` (medium/hard, tool)

## The task given to each candidate

> test_aggregate.py fails: user 1's total should be 30 but comes out wrong. Fix it.

## What to reward / penalize

Root cause vs symptom: the real bug is in summarize() — user_id arrives as both int 1 and str '1', so a user's spend is split across two dict keys. The correct fix normalizes the key (e.g. str(uid)) in summarize. A weak fix patches top_user or the test, or special-cases the symptom, leaving the underlying key-collision. Reward understanding-before-acting and a verified fix (tests run); penalize symptom-patching, try/except masking, or editing the test to pass.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=26.5s; answer_chars=185; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Answer:
````
Both pass. The fix was `uid = str(e["user_id"])` in `aggregate.py:6` — coercing the key to `str` before inserting into the dict so that int `1` and string `"1"` land in the same bucket.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=36.2s; answer_chars=153; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Answer:
````
`aggregate.py:5` — `uid = str(e["user_id"])` normalizes both `1` and `"1"` to the same key before accumulating, so the two events merge to a total of 30.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=40.8s; answer_chars=449; files_added=[]; files_modified=['aggregate.py']; files_deleted=[]

Answer:
````
Both tests pass. The fix was one line in `aggregate.py:5`: normalize `user_id` to `str` before using it as a dict key, so int `1` and str `"1"` merge into the same bucket.

> **Dangerous unhandled case:** what if `user_id` is `None` or a non-hashable type (e.g. a list)? `str(None)` → `"None"` silently merges all null-id events together; a list would have raised before the fix too. Should the boundary validate that `user_id` is a non-null scalar?
````
