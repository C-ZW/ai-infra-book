# Judge packet — task `h7_perf_optimization` (medium/hard, tool)

## The task given to each candidate

> dedupe_preserve_order in dedup.py is too slow on large inputs. Make it faster without changing its output.

## What to reward / penalize

Understand + preserve semantics + verify: the function is O(n^2) (a nested 'in result' scan); the correct fix is O(n) using a seen-set while preserving first-seen order. A strong agent keeps the output identical (order-preserving unique, handles unhashable? — inputs are hashable here) and RUNS the existing test to confirm behavior is unchanged. Penalize changing the output order/semantics, using a method that drops order (plain set()), or not verifying. Reward the linear seen-set rewrite with a test run.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=126.8s; answer_chars=1792; files_added=['__pycache__/dedup.cpython-313.pyc']; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
Done. The fix changes the algorithm from O(n²) to O(n) while producing byte-for-byte identical output.

**What was slow:** `if x in result` is a linear scan of the growing list on every iteration — O(n²). On 20k unique items that's ~900ms.

**The fix:** maintain a `set` for O(1) membership instead of scanning the list. Result: ~1.5ms on the same input — **~588× faster**.

**The output-preservation trap I avoided:** a plain `set` only accepts hashable elements, but the original quietly handled unhashable ones (lists, dicts, sets as elements) — `dedupe_preserve_order([[1],[1],[2]])` returns `[[1],[2]]` today. So the new code keeps a try/except fallback to the original linear scan for unhashable elements. The `unhashable` guard list stays empty in the common all-hashable case, so the fast path pays nothing for it.

**Verification:** built the original O(n²) version as a reference oracle and ran 2013 equivalence checks — 13 hand-picked edge cases (the `1 == True == 1.0` equality group, `0/False/0.0`, NaN, tuples, dicts, mixed hashable/unhashable) plus 2000 fuzz cases randomly mixing ints, strings, lists, dicts, and tuples. **Zero mismatches.**

One residual behavioral edge worth naming: the original deduped purely by `__eq__`; the fast path buckets hashable items by `__hash__` first. For a correctly-implemented type these are identical, but an object that **violates the Python invariant** (equal objects with unequal hashes) could dedupe differently. That's a broken object by Python's data-model rules, not a normal input — but it's the one case where the two implementations can diverge.

Given this runs on large untrusted inputs: do you know whether the elements are always hashable in practice, or should the unhashable fallback stay as the safety net it currently is?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=57.5s; answer_chars=1088; files_added=['__pycache__/dedup.cpython-313.pyc']; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
Done. `dedup.py:5` was the culprit — `x in result` is an O(n) list scan, making the function O(n²).

The fix keeps a `seen` set for O(1) membership (hashable items) while still appending to `result` to preserve first-seen order. Unhashable items (lists, dicts) fall back to the original equality scan via `seen_unhashable`, so they don't raise `TypeError` — behavior the original supported.

Verified: identical output across empties, duplicates, falsy/equal-value collisions (`1 == 1.0 == True`), same-object vs. distinct `nan`, unhashable lists/dicts, and mixed inputs; ~52x faster on 40k items (O(n²) → O(n)).

One assumption worth naming: this splits membership into a hashable pool and an unhashable pool, so it would diverge from the original only if a *hashable* object compared `==` to an *unhashable* one already seen — which violates Python's `a == b ⇒ hash(a) == hash(b)` contract and can't occur with well-behaved objects.

What's the largest realistic input size this needs to handle — could it ever exceed memory, given `seen` now retains a reference to every distinct item?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=45.8s; answer_chars=759; files_added=['__pycache__/dedup.cpython-313.pyc']; files_modified=['dedup.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
Done. `dedup.py` now runs in O(n) instead of O(n²).

What changed: a `seen` set gives O(1) membership for hashable items, with a `seen_unhashable` list fallback so lists/dicts/sets still dedupe (and don't raise) exactly as before. Output is byte-for-byte identical — verified against the original across cross-type equality (`1==1.0==True`), `NaN` identity, unhashable and mixed inputs, plus 2000 random fuzz cases. ~31x faster at 40k elements, and the gap widens with size.

One edge case left undefended by both versions: a type whose `__eq__`/`__hash__` are mutually inconsistent (or mutated mid-iteration) could in principle dedupe differently between set and list — should I guard against that, or is consistent hashing a safe assumption for your inputs?
````
