# Judge packet — task `h1_crossfile_refactor` (long/hard, tool)

## The task given to each candidate

> Refactor format_name in textlib/names.py to take a single full_name string (e.g. 'Ada Lovelace') instead of separate first and last arguments, still returning 'Last, First' (e.g. 'Lovelace, Ada'). Update everything that depends on it so the project still works.

## What to reward / penalize

Cross-file follow-through: changing the signature breaks the callers in textlib/greet.py and textlib/report.py and the tests. A strong agent searches for ALL call sites, updates them, and RUNS the tests to verify nothing is left broken. Penalize editing only names.py (leaves TypeErrors), or claiming done without running tests. The telemetry's files_modified should include the callers, not just names.py.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=37.9s; answer_chars=759; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Here's a summary of the changes:

- **`names.py`**: `format_name(first, last)` → `format_name(full_name)`, splits on the last space with `rsplit(" ", 1)` to handle names like "Mary Jo Blige" correctly (last word becomes last name).
- **`greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes the single string through to `format_name`.
- **`report.py`**: `roster` now iterates over a list of strings instead of `(first, last)` tuples.

What's the most dangerous unhandled case here? A `full_name` with no space (e.g. `"Cher"`) will cause `rsplit(" ", 1)` to return a single-element list, making the unpacking `first, last = ...` raise a `ValueError`. If single-name inputs are possible, that boundary needs explicit validation.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=17; wall=47.5s; answer_chars=614; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Summary of changes:

- `textlib/names.py` — `format_name(first, last)` → `format_name(full_name)`, splits on the last space via `rsplit(" ", 1)`, raises `ValueError` for single-token input
- `textlib/greet.py` — `greeting(first, last)` → `greeting(full_name)`, passes it straight through
- `textlib/report.py` — `roster` iterable changed from `(first, last)` tuples to plain name strings

One edge to watch: names with only one token (e.g. mononyms) will now raise explicitly rather than silently misbehave — decide whether that needs a fallback (e.g. `"Cher, "`) before extending the call sites.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=13; wall=48.0s; answer_chars=750; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Changes made:

- **`textlib/names.py`**: `format_name(first, last)` → `format_name(full_name)`. Uses `rsplit(None, 1)` to split on the last whitespace token (so `"Mary Ann Evans"` → `"Evans, Mary Ann"` correctly). Raises `ValueError` on empty/single-word input rather than silently producing garbage.
- **`textlib/greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes through to the refactored function.
- **`textlib/report.py`**: `roster` now expects a list of full-name strings instead of `(first, last)` tuples.

Edge case to be aware of: callers passing `(first, last)` tuples into `roster` will now get a `ValueError` instead of the old behavior — confirm no external callers use the tuple form before deploying.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=13; wall=49.1s; answer_chars=860; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. Here's what changed:

- **`textlib/names.py`**: `format_name(first, last)` → `format_name(full_name)`. Uses `rsplit(" ", 1)` so middle names stay with the first name (e.g. `"Ada Augusta Lovelace"` → `"Lovelace, Ada Augusta"`). Raises `ValueError` on a name with no space rather than silently producing a wrong result.
- **`textlib/greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes the string straight through.
- **`textlib/report.py`**: `roster` now iterates over strings instead of `(first, last)` tuples.

What's the most dangerous unhandled case? A caller passing an empty string — `format_name("")` raises `ValueError: ... got: ''`, which is fine, but callers that swallow that exception will silently drop names from rosters. Worth adding an explicit empty-string guard if `roster` is ever called with untrusted input.
````
