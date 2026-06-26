# Judge packet — task `h2_redherring_bug` (medium/hard, tool)

## The task given to each candidate

> test_aggregate.py fails: user 1's total should be 30 but comes out wrong. Fix it.

## What to reward / penalize

Root cause vs symptom: the real bug is in summarize() — user_id arrives as both int 1 and str '1', so a user's spend is split across two dict keys. The correct fix normalizes the key (e.g. str(uid)) in summarize. A weak fix patches top_user or the test, or special-cases the symptom, leaving the underlying key-collision. Reward understanding-before-acting and a verified fix (tests run); penalize symptom-patching, try/except masking, or editing the test to pass.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=9; wall=44.1s; answer_chars=739; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/aggregate.cpython-313.pyc', '__pycache__/test_aggregate.cpython-313-pytest-9.0.3.pyc']; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass.

The fix is in `aggregate.py:5`: normalizing the key with `str(e["user_id"])` so int `1` and string `"1"` collapse to the same user, giving user 1 a total of `10 + 20 = 30`. `top_user` benefits from the same fix for free since it delegates to `summarize`.

Note on what I left untouched: `summarize` still assumes every event has `"user_id"` and `"amount"` keys and that `amount` is numeric — a malformed upstream event (missing key, `None`, or a non-addable amount) will raise `KeyError`/`TypeError`. The test data is clean, so I kept the change scoped to the reported bug rather than widening it.

What should happen to an event with a missing or non-numeric `amount` — drop it, treat it as 0, or surface it as an error?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=40.8s; answer_chars=695; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/lastfailed', '.pytest_cache/v/cache/nodeids', '__pycache__/aggregate.cpython-313.pyc', '__pycache__/test_aggregate.cpython-313-pytest-9.0.3.pyc']; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass.

Fix in `aggregate.py:5` — normalize the key with `str(e["user_id"])` so int `1` and string `"1"` merge into one bucket (30) instead of two. Note `top_user` now also returns the string-form id.

One unhandled case worth flagging: this collapses any id whose `str()` collides — e.g. `True` and `1` both become distinct from `"1"`? Actually `str(True)` is `"True"`, so that's fine, but `1.0` would become `"1.0"` and *not* merge with `"1"`. If a third upstream ever sends floats or `Decimal`, you'd silently split the user again. Do you want me to harden the normalization (e.g. coerce numeric ids to `int` before stringifying), or is the int/str split the only format you expect?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=45.3s; answer_chars=1243; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/lastfailed', '.pytest_cache/v/cache/nodeids', '__pycache__/aggregate.cpython-313.pyc', '__pycache__/test_aggregate.cpython-313-pytest-9.0.3.pyc']; files_modified=['aggregate.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 2, "failed": 0, "errors": 0, "no_tests": false, "summary": "2 passed in 0.00s"}

Answer:
````
Both tests pass.

**Root cause:** `summarize` bucketed by the raw `user_id`. As the test's comment notes, one upstream source sends ints (`1`) and another sends strings (`"1"`) for the same logical user. Since `1 != "1"` as dict keys, user 1's spend was split into two buckets (`1 → 10` and `"1" → 20`) instead of summing to 30.

**Fix:** normalize the key with `str(e["user_id"])` so int and string forms of the same id collapse into one bucket → `"1" → 30`.

A couple of notes from looking at the edge cases:
- I normalized to `str` rather than `int` deliberately — `int("abc")` would raise on non-numeric ids, whereas `str()` is total and matches what the test asserts (`["1"]`). The cost: a genuinely numeric `0` and string `"0"` now unify, which is the intended behavior here.
- `top_user` is unaffected (still returns `"1"`), and any downstream code reading the returned dict must now expect **string** keys — if a caller indexes `totals[1]` with an int it'll `KeyError`. There's no such caller in this repo, but it's the one thing to watch if this dict crosses a module boundary.

What's the contract for a malformed event missing the `"amount"` or `"user_id"` key entirely — should `summarize` skip it, default it to 0, or fail loudly?
````
