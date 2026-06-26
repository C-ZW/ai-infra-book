# Judge packet — task `h7_perf_optimization` (medium/hard, tool)

## The task given to each candidate

> dedupe_preserve_order in dedup.py is too slow on large inputs. Make it faster without changing its output.

## What to reward / penalize

Understand + preserve semantics + verify: the function is O(n^2) (a nested 'in result' scan); the correct fix is O(n) using a seen-set while preserving first-seen order. A strong agent keeps the output identical (order-preserving unique, handles unhashable? — inputs are hashable here) and RUNS the existing test to confirm behavior is unchanged. Penalize changing the output order/semantics, using a method that drops order (plain set()), or not verifying. Reward the linear seen-set rewrite with a test run.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=20.8s; answer_chars=542; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
Replaced the O(n²) `x in result` list scan with a parallel `seen` set for O(1) membership checks, making the overall function O(n). Output is identical — the list preserves insertion order, the set only gates duplicates.

> **Potential failure mode to consider:** items must be hashable to be stored in a set. If your input ever contains unhashable types (lists, dicts, sets), this will raise `TypeError`. The original code worked with those types because list membership uses `==` rather than hashing — if that matters, a fallback is needed.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=19.2s; answer_chars=564; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
`x in result` was an O(n) scan on a list, making the loop O(n²). Switching to a `set` for membership tests makes each lookup O(1), so the whole function is O(n) — with identical output.

One failure mode to be aware of: items must be **hashable**. If `items` ever contains lists, dicts, or other unhashable types, `seen.add(x)` will raise `TypeError`. The original had the same constraint implicitly (unhashable types can't be compared with `==` in a meaningful way for dedup), so this doesn't regress behavior — but worth confirming your input is always hashable.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=19.9s; answer_chars=342; files_added=[]; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
O(n²) → O(n). The `set` provides O(1) average membership tests; the list still tracks insertion order. Output is identical.

One edge case to confirm: if `items` contains unhashable elements (e.g. `list`, `dict`), the `set` will raise `TypeError` — whereas the original silently handled them. Worth checking if that's possible in your inputs.
````
