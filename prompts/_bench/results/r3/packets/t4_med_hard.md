# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=31.2s; answer_chars=479; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed. The bug was at `utils.py:14`: `hours + minutes` treated an hour as one minute. Changed to `hours * 60 + minutes`.

All three cases pass: `1h30m`→90, `45m`→45, `2h`→120.

One edge still lurks: the regex `(?:(\d+)h)?(?:(\d+)m)?$` makes both groups optional, so `""` is caught by the `not s` guard, but a stray input like `"h"`, `"m"`, or `"30"` (no unit) — does the caller ever feed unit-less or whitespace-laden strings you'd want rejected rather than silently parsed as 0?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=28.2s; answer_chars=942; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed. The bug was on line 14 of `utils.py`:

```python
return hours + minutes        # before — treats 1h as 1 minute
return hours * 60 + minutes   # after  — converts hours to minutes
```

`parse_duration('1h30m')` now returns `90` instead of `31`. All required cases pass: `'45m'` → 45, `'2h'` → 120 (this one was also silently wrong before, returning `2`), `'1h30m'` → 90. Invalid inputs still raise `ValueError`.

One latent failure mode I checked but left alone since it's outside the ask: the regex `(?:(\d+)h)?(?:(\d+)m)?$` accepts reversed order loosely and would match an empty string if not for the `not s` guard — both still behave correctly here, but if you ever want strict validation (e.g. rejecting `'30m1h'` ordering or capping minutes at 59), that's a separate hardening pass.

Do you want me to also reject out-of-range values like `'90m'` or enforce that at least one unit is present beyond the current empty-string check?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=30.1s; answer_chars=520; files_added=['__pycache__/utils.cpython-313.pyc']; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed at `utils.py:14`: changed `hours + minutes` to `hours * 60 + minutes`. All three cases now return total minutes correctly — `1h30m → 90`, `45m → 45`, `2h → 120`.

One unhandled case worth flagging: the regex makes both groups optional, so a stray non-duration token like `"h"` or `"m"` (and the empty string, currently caught only by the `not s` guard) can slip through `fullmatch` as a zero-value match rather than raising `ValueError`. Do you want `parse_duration` to reject inputs that contain no actual digits?
````
