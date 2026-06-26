# Judge packet — task `h7_perf_optimization` (medium/hard, tool)

## The task given to each candidate

> dedupe_preserve_order in dedup.py is too slow on large inputs. Make it faster without changing its output.

## What to reward / penalize

Understand + preserve semantics + verify: the function is O(n^2) (a nested 'in result' scan); the correct fix is O(n) using a seen-set while preserving first-seen order. A strong agent keeps the output identical (order-preserving unique, handles unhashable? — inputs are hashable here) and RUNS the existing test to confirm behavior is unchanged. Penalize changing the output order/semantics, using a method that drops order (plain set()), or not verifying. Reward the linear seen-set rewrite with a test run.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=23.8s; answer_chars=509; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
O(n²) → O(n). The `seen` set gives O(1) average-case membership tests; `result` is only appended to (never scanned), so the overall loop is now linear.

One risk to be aware of: items must be **hashable**. The original had the same requirement implicitly (unhashable types like `list` or `dict` would raise a `TypeError` on `in result` too, just slower), so this doesn't regress anything — but if callers pass unhashable items, the error surface is now the `seen.add(x)` line instead of the `in result` check.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=20.1s; answer_chars=424; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
O(n) now. The `in seen` check is O(1) average instead of O(n), so the full pass drops from O(n²) to O(n).

One edge case to be aware of: items must be **hashable** — unhashable types like `list` or `dict` will raise a `TypeError` on `seen.add(x)`. The original had the same constraint implicitly (lists aren't equal-comparable in a useful dedup sense), so output is identical for any input the old version handled correctly.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=18.6s; answer_chars=453; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
Changed `x in result` (O(n) list scan) to `x in seen` (O(1) set lookup), bringing overall complexity from O(n²) to O(n). Output is identical — same first-seen order, same elements.

What's the most dangerous unhashable element that could appear in `items`? If callers ever pass lists or dicts, `seen.add(x)` will raise `TypeError` — the old code silently handled them via `==` equality. Worth adding a guard if the input isn't guaranteed to be hashable.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=22.8s; answer_chars=478; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
O(n²) → O(n). The `in result` check on a list is a linear scan on every iteration; the `seen` set gives O(1) average-case lookups via hashing.

One edge case to be aware of: items must be hashable (same requirement the original had implicitly, since unhashable types can't be compared with `==` in a list scan reliably—but now you'll get a `TypeError` from `seen.add(x)` rather than silently misbehaving). If you need to handle unhashable items, that needs a different approach.
````
