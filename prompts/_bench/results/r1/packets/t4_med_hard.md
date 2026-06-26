# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=29.4s; answer_chars=660; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed. `'1h30m'` → 90, `'45m'` → 45, `'2h'` → 120, all correct.

One unhandled case still worth naming: the regex `(?:(\d+)h)?(?:(\d+)m)?$` matches the *empty* string and strings like `'h'` or `'m'` (both groups optional), but the `not s` check only guards a fully-empty input. An input like `'  '` (stripped to empty) raises correctly, yet `parse_duration('hello m')`-style junk before a valid tail won't match thanks to `fullmatch`. The sharper gap: `parse_duration('30m15h')` (reversed order) returns 15 silently instead of erroring — should the parser reject out-of-order or unit-less input rather than quietly accepting whatever the optional groups catch?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=28.7s; answer_chars=986; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed and verified.

**The bug:** `utils.py:14` returned `hours + minutes`, treating the hour count as if it were already minutes. `'1h30m'` parsed to `hours=1, minutes=30` and returned `31` instead of `90`.

**The fix:** convert hours to minutes before summing — `return hours * 60 + minutes`.

All three cases pass: `'1h30m'` → 90, `'45m'` → 45, `'2h'` → 120.

One unhandled case worth flagging while you're here: the regex uses optional groups with no anchored content, so `parse_duration('')` would slip past the regex but is caught by the `not s` guard — good. However, a whitespace-only string like `'   '` is stripped to `''` and correctly rejected, but a malformed-but-partial input like `'30'` (no unit) or `'1m30h'` (wrong order) will raise `ValueError`, which is the right behavior. The most dangerous remaining gap: `parse_duration(None)` throws an `AttributeError` on `.strip()` rather than a clean `ValueError` — do you want non-string input validated at the boundary too?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=33.2s; answer_chars=712; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed `utils.py:14`. The function summed `hours + minutes` instead of converting hours to minutes.

Verified: `'1h30m'` → 90, `'45m'` → 45, `'2h'` → 120.

One latent failure mode worth flagging: because both regex groups are optional, an input like `'1x'` or `'5'` (no unit) still passes `fullmatch` as an all-empty match and is rejected only incidentally — but `parse_duration('')` after strip is caught by the `not s` guard, while something like `parse_duration('   ')` also resolves to empty and raises correctly. The riskier gap is that a bare number with no unit, e.g. `'90'`, raises `invalid duration` rather than being treated as minutes. Do you want `'90'` to mean 90 minutes, or should it stay an error?
````
