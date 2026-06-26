# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=38.3s; answer_chars=635; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed `utils.py:14`. The function added hours directly to minutes (`hours + minutes`), so `1h30m` gave `31`. Now `hours * 60 + minutes`:

- `1h30m` → 90
- `45m` → 45
- `2h` → 120

One latent gap worth flagging: because every regex group is optional, an all-empty-but-truthy input that still fullmatches (e.g. a string of only whitespace is caught by `strip()`/`not s`, but a stray match path) could return `0` silently rather than raising. The current guards cover the known inputs — do you want me to also reject zero-token inputs like `''` after strip more explicitly, or is the current `ValueError` path sufficient for your callers?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=24.2s; answer_chars=932; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed. The bug was on line 14 of `utils.py`: hours were added to minutes without converting to minutes first.

```python
return hours + minutes        # before — '1h30m' → 31
return hours * 60 + minutes   # after  — '1h30m' → 90
```

All three cases now pass: `'1h30m'` → 90, `'45m'` → 45, `'2h'` → 120.

One unhandled edge case worth flagging: the regex `(?:(\d+)h)?(?:(\d+)m)?$` uses `fullmatch` with both groups optional, so a string of pure whitespace becomes `''` after `strip()` and is correctly rejected by the `not s` guard — but a malformed input like `'30m15h'` (wrong order) or `'1.5h'` (decimal) raises `ValueError` as intended. The most dangerous remaining case: `parse_duration` assumes `s` is a string — passing `None` or an `int` will throw `AttributeError` on `.strip()` rather than a clean `ValueError`. Do you want input-type validation added at the boundary, or is the string-only contract guaranteed by callers?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=38.4s; answer_chars=591; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed `utils.py:14`. The function summed hours and minutes as if both were minutes; now it multiplies hours by 60. Verified: `1h30m`→90, `45m`→45, `2h`→120.

One unhandled case worth noting: the regex's groups are both optional, so a stray non-duration token like `'1x'` falls through to the `ValueError` (good), but a bare `'0'`... actually that also fails to match since it needs an `h`/`m` suffix — so it raises correctly. The real gap is that negative or absurdly large values aren't bounded. Do you want input validation on the upper range, or is raising on malformed input enough here?
````
