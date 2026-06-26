# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=8; wall=27.6s; answer_chars=474; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed `utils.py:14`: `hours + minutes` → `hours * 60 + minutes`. Verified: `1h30m`→90, `45m`→45, `2h`→120.

One unhandled edge worth flagging: the regex makes both groups optional and anchors only at the end, so an empty-after-strip string is caught by the `not s` guard — but a bare-number input like `'30'`? That fails to match (`m` is `None`) and raises correctly. What's the intended behavior for a seconds suffix like `'90s'` — silently rejected (current) or supported?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=30.4s; answer_chars=671; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed `utils.py:14` — it was `hours + minutes`, treating an hour as one minute. Now `hours * 60 + minutes`.

All pass: `1h30m`→90, `45m`→45, `2h`→120, and invalid input still raises `ValueError`. Note `45m` only looked correct before because hours was 0; `2h` was actually wrong too (returned 2).

One unhandled case worth flagging: the regex makes every component optional, so `parse_duration("")`-after-strip is caught by the `not s` guard, but a stray ordering like `"30m1h"` simply fails to match and raises — intended. Do you want `parse_duration` to also reject zero-length-after-valid quirks like `"0h0m"` (currently returns 0), or is 0 an acceptable result there?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=34.0s; answer_chars=493; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed `utils.py:14`. The function summed hours and minutes as if both were minutes; now it converts hours to minutes (`hours * 60 + minutes`). All three cases pass: `1h30m`→90, `45m`→45, `2h`→120.

One unhandled edge worth noting: the regex makes both groups optional, so a unit-less string like `'30'` raises `ValueError` (it fails `fullmatch`) rather than being parsed — correct, but is silently rejecting `'90'`-style bare-minute input the behavior you want, or should that be accepted too?
````
