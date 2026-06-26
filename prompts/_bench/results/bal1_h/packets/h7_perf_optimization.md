# Judge packet — task `h7_perf_optimization` (medium/hard, tool)

## The task given to each candidate

> dedupe_preserve_order in dedup.py is too slow on large inputs. Make it faster without changing its output.

## What to reward / penalize

Understand + preserve semantics + verify: the function is O(n^2) (a nested 'in result' scan); the correct fix is O(n) using a seen-set while preserving first-seen order. A strong agent keeps the output identical (order-preserving unique, handles unhashable? — inputs are hashable here) and RUNS the existing test to confirm behavior is unchanged. Penalize changing the output order/semantics, using a method that drops order (plain set()), or not verifying. Reward the linear seen-set rewrite with a test run.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=20.3s; answer_chars=324; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
O(n²) → O(n). The `set` tracks seen items for O(1) average membership tests; the list preserves insertion order.

One caveat: items must be **hashable**. If the caller ever passes unhashable types (e.g. lists, dicts), this will raise `TypeError` where the old code silently handled them — is that a case you need to support?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=20.6s; answer_chars=392; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
O(n²) → O(n). The `seen` set makes membership checks O(1) average, so the loop runs in linear time overall. Output is identical — `seen` is only used for the guard; `result` still collects items in first-seen order.

One sharp edge: items must be **hashable** for set membership. If the list can contain dicts, lists, or other unhashable types, you'd need a fallback — is that a concern here?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=18.7s; answer_chars=452; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
Changed from O(n²) to O(n) by tracking seen elements in a `set` (O(1) average-case lookup) instead of scanning `result` (O(n) per element). Output is identical — same first-seen order, same deduplication semantics.

One probing question: does `items` ever contain unhashable elements (e.g., lists, dicts)? If so, `set.add` will raise a `TypeError` — the original O(n²) list-scan would have silently handled them, so you'd need a fallback for that case.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=23.3s; answer_chars=352; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
O(n²) → O(n). The `seen` set makes membership checks O(1) average instead of scanning the growing `result` list each iteration.

One caveat: items must be **hashable**. If `items` can contain dicts, lists, or other unhashable types, this will raise `TypeError` where the original silently worked. Worth checking your call sites if that's a possibility.
````
