# Judge packet — task `t4_med_hard` (medium/hard, tool)

## The task given to each candidate

> parse_duration('1h30m') returns the wrong value in utils.py. Find and fix the bug. It must still handle '45m' and '2h' correctly afterward.

## What to reward / penalize

Full loop: understand the bug (hours not multiplied by 60), make a minimal correct fix, and VERIFY by running the tests (test_utils.py / pytest). Penalize claiming it's fixed without running tests, or scope creep.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=-9; timed_out=True; turns=None; wall=300.9s; answer_chars=0; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
(empty answer)
````

### Candidate B

Behavioral telemetry: exit=-9; timed_out=True; turns=None; wall=301.0s; answer_chars=0; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
(empty answer)
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=12; wall=280.1s; answer_chars=1405; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
The code and tests look correct in the current state — `parse_duration('1h30m')` returns 90, `'45m'` → 45, `'2h'` → 120, and all three tests pass.

I do see one latent bug worth calling out: the regex matches the **empty string** (both groups optional → `groups=(None, None)`). The `not s` guard catches `""` after strip, but it means a string like `" "` (all whitespace) raises `ValueError` — which is fine — yet there's no guard for a case where both groups match but contribute zero (e.g. `"0h0m"` → 0, which may or may not be intended).

The real subtle edge-case vulnerability is that the regex accepts inputs where **neither group matched** but the string isn't empty — impossible with `fullmatch` (it must consume the full string), but if this regex were ever used with `match()` instead of `fullmatch()`, any leading `\d+h` could match and the trailing garbage would be silently ignored.

**No bug exists in the current code for the inputs described.** All three assertions hold:

```
parse_duration('1h30m') == 90   ✓
parse_duration('45m')   == 45   ✓
parse_duration('2h')    == 120  ✓
```

What does the caller that's seeing the "wrong value" actually receive — is it a different Python environment, a different `utils.py` on a path, or a different invocation of the function? That's the most dangerous unverified assumption here: the file I'm reading may not be the one actually being executed.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=10; wall=212.4s; answer_chars=987; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
All three test cases pass with the current code — `parse_duration('1h30m')` correctly returns `90`, `'45m'` returns `45`, and `'2h'` returns `120`. The implementation is correct as written.

Here's what I verified:

- The regex `(?:(\d+)h)?(?:(\d+)m)?$` with `fullmatch` correctly captures both groups for `'1h30m'`
- Group 1 → hours (`1`), Group 2 → minutes (`30`)  
- `hours * 60 + minutes` = `60 + 30` = `90` ✓
- The `not s` guard before `not m` correctly handles the edge case where an empty string would produce a non-`None` match (both groups optional)

There is no bug to fix in `utils.py`. All three tests in `test_utils.py` pass clean.

If you're seeing a wrong value in your environment, it may be worth checking whether there's a different `utils.py` being imported (e.g., a stale `.pyc` in `__pycache__`, or a shadowing module on `sys.path`):

```bash
python3 -c "import utils; import inspect; print(inspect.getfile(utils))"
```

What specific wrong value were you observing?
````
