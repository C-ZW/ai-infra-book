# Judge packet — task `h7_perf_optimization` (medium/hard, tool)

## The task given to each candidate

> dedupe_preserve_order in dedup.py is too slow on large inputs. Make it faster without changing its output.

## What to reward / penalize

Understand + preserve semantics + verify: the function is O(n^2) (a nested 'in result' scan); the correct fix is O(n) using a seen-set while preserving first-seen order. A strong agent keeps the output identical (order-preserving unique, handles unhashable? — inputs are hashable here) and RUNS the existing test to confirm behavior is unchanged. Penalize changing the output order/semantics, using a method that drops order (plain set()), or not verifying. Reward the linear seen-set rewrite with a test run.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=21.8s; answer_chars=424; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
O(n²) → O(n). The `set` tracks seen elements for O(1) lookups; `result` preserves insertion order. Output is identical.

One risk worth naming: elements must be **hashable** — this was already true with the list-membership check, but now it fails *loudly* (TypeError) rather than silently using equality fallback. Any unhashable items (e.g. dicts, lists) in the input will surface as errors here that were previously masked.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=20.8s; answer_chars=291; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
O(n²) → O(n). The `seen` set gives O(1) average membership tests; `result` list preserves insertion order. Output is identical — unhashable items (dicts, lists) would still raise `TypeError` from the `set.add`, same as before since they'd also fail `__hash__` in the old `list.__contains__`.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=17.1s; answer_chars=407; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
O(n²) → O(n). The `seen` set makes duplicate checks O(1) average instead of scanning the growing `result` list each time. Output is identical — same first-seen order.

> **What happens if items are unhashable (e.g., lists or dicts)?** The set will raise `TypeError`. The original also couldn't deduplicate them via equality alone — but if your inputs include unhashable types, the fix must account for that.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=17.2s; answer_chars=460; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
O(n²) → O(n). The `seen` set gives O(1) average-case membership tests, so each element is checked exactly once.

One sharp edge: items must be **hashable**. If `items` can contain dicts, lists, or other unhashable types, the set will raise `TypeError`. The original also failed silently on unhashable types (they'd always appear non-equal via `in` on a list), so the semantics are identical for hashable inputs — but worth confirming the input domain is clean.
````
