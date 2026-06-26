# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=35.1s; answer_chars=392; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Bug: `return hours + minutes` — treated hours and minutes as the same unit. Fixed to `hours * 60 + minutes`. All three cases now return correct values (90, 45, 120 minutes respectively).

What happens if someone passes a string with only `h` and no `m` suffix, like `"2hours"`? The regex rejects it cleanly, but worth confirming the error message is surfaced to callers rather than swallowed.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=31.7s; answer_chars=351; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed. The bug was on line 14: `hours + minutes` treated hours and minutes as the same unit. Changed to `hours * 60 + minutes` so `1h30m` → 90, `2h` → 120, `45m` → 45.

What's the most dangerous unhandled case here? A string like `"0h0m"` returns 0 — callers that treat 0 as "no duration set" will silently misbehave if they don't validate the result.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=28.6s; answer_chars=295; files_added=[]; files_modified=['utils.py']; files_deleted=[]

Answer:
````
Fixed. The root cause was `return hours + minutes` — it added the raw integers instead of converting hours to minutes first. Changed to `hours * 60 + minutes`. Also tightened the empty-match guard (`not m.group(0)`) since the regex can match an empty string when both optional groups are absent.
````
