# Judge packet — task `h7_perf_optimization` (medium/hard, tool)

## The task given to each candidate

> dedupe_preserve_order in dedup.py is too slow on large inputs. Make it faster without changing its output.

## What to reward / penalize

Understand + preserve semantics + verify: the function is O(n^2) (a nested 'in result' scan); the correct fix is O(n) using a seen-set while preserving first-seen order. A strong agent keeps the output identical (order-preserving unique, handles unhashable? — inputs are hashable here) and RUNS the existing test to confirm behavior is unchanged. Penalize changing the output order/semantics, using a method that drops order (plain set()), or not verifying. Reward the linear seen-set rewrite with a test run.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=18.5s; answer_chars=234; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Answer:
````
O(n²) → O(n). The `seen` set gives O(1) membership tests so each element is touched once.

**Caveat:** items must be hashable (same requirement as before — unhashable types would have failed the list's `__eq__` loop too, just slower).
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=21.9s; answer_chars=378; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Answer:
````
O(n²) → O(n). The `seen` set makes membership checks O(1) instead of O(n), so large inputs that were quadratic are now linear.

One failure mode to confirm: items must be hashable. If `items` can contain unhashable types (dicts, lists, sets), the old O(n²) version would handle them silently while this one raises `TypeError` on `seen.add(x)`. Is that a concern for your inputs?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=18.0s; answer_chars=292; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Answer:
````
O(n²) → O(n). The `x in result` list scan was the bottleneck; `x in seen` is O(1) average for a set.

One caveat: items must be hashable. If your input contains unhashable types (dicts, lists), the set will raise `TypeError` — the original code handled those silently via equality comparison.
````
