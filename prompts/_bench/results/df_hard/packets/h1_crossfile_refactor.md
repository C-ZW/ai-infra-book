# Judge packet — task `h1_crossfile_refactor` (long/hard, tool)

## The task given to each candidate

> Refactor format_name in textlib/names.py to take a single full_name string (e.g. 'Ada Lovelace') instead of separate first and last arguments, still returning 'Last, First' (e.g. 'Lovelace, Ada'). Update everything that depends on it so the project still works.

## What to reward / penalize

Cross-file follow-through: changing the signature breaks the callers in textlib/greet.py and textlib/report.py and the tests. A strong agent searches for ALL call sites, updates them, and RUNS the tests to verify nothing is left broken. Penalize editing only names.py (leaves TypeErrors), or claiming done without running tests. The telemetry's files_modified should include the callers, not just names.py.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=13; wall=44.4s; answer_chars=706; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. Changes made:

- `textlib/names.py` — `format_name(first, last)` → `format_name(full_name)`, splits on the last space (handles compound first names like `"Mary Jo Smith"` → `"Smith, Mary Jo"`), raises `ValueError` on empty or single-word input instead of silently returning broken output
- `textlib/greet.py` — `greeting(first, last)` → `greeting(full_name)`, passes straight through
- `textlib/report.py` — `roster` now iterates over name strings rather than `(first, last)` tuples

One unhandled case worth noting: names with honorifics or suffixes (e.g. `"Ada Lovelace Jr."`) will produce `"Jr., Ada Lovelace"` — if that's a real input shape, the split logic needs a convention for it.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=16; wall=55.9s; answer_chars=666; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. Here's what changed:

- **`names.py`**: `format_name(first, last)` → `format_name(full_name)`, using `rsplit(None, 1)` to split off the last token as the last name. Raises `ValueError` if fewer than two tokens are present.
- **`greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes it straight through.
- **`report.py`**: `roster(people)` now iterates over strings instead of unpacking `(first, last)` tuples.

One open question: `rsplit(None, 1)` on `"Ada Augusta Lovelace"` yields `first="Ada Augusta"`, `last="Lovelace"` — is that the intended behavior for multi-word first names, or should the split always be at the first space?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=36.6s; answer_chars=660; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Here's what changed across the three files:

- **`names.py`**: `format_name(first, last)` → `format_name(full_name)`, splits on the last space with `rsplit(' ', 1)` to extract first and last.
- **`greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes the full name string through to `format_name`.
- **`report.py`**: `roster` now expects a list of full name strings instead of `(first, last)` tuples.

One edge case worth noting: `rsplit(' ', 1)` treats everything before the last space as the "first" part — so `"Mary Ann Evans"` would yield `"Evans, Mary Ann"`, which is typically the right behavior for compound given names.
````
