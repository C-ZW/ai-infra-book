# Judge packet — task `h1_crossfile_refactor` (long/hard, tool)

## The task given to each candidate

> Refactor format_name in textlib/names.py to take a single full_name string (e.g. 'Ada Lovelace') instead of separate first and last arguments, still returning 'Last, First' (e.g. 'Lovelace, Ada'). Update everything that depends on it so the project still works.

## What to reward / penalize

Cross-file follow-through: changing the signature breaks the callers in textlib/greet.py and textlib/report.py and the tests. A strong agent searches for ALL call sites, updates them, and RUNS the tests to verify nothing is left broken. Penalize editing only names.py (leaves TypeErrors), or claiming done without running tests. The telemetry's files_modified should include the callers, not just names.py.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=13; wall=50.0s; answer_chars=713; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. Summary of changes:

- `textlib/names.py` — `format_name(first, last)` → `format_name(full_name)`, splits on the last space with `rsplit(" ", 1)` (handles multi-word first names like "Mary Ann Evans"), raises `ValueError` for single-word input
- `textlib/greet.py` — `greeting(first, last)` → `greeting(full_name)`, passes it straight through
- `textlib/report.py` — `roster` now expects `list[str]` instead of `list[tuple]`, iterates with `for name in people`

What happens if a caller passes an empty string or a name with only non-breaking spaces — `rsplit` won't split on those, so the `ValueError` would fire. Worth confirming expected behavior there if this function faces untrusted input.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=15; wall=42.3s; answer_chars=678; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. Changes made:

- `names.py`: `format_name(first, last)` → `format_name(full_name)`, splits on the rightmost space (`rsplit(" ", 1)`) so middle names attach to the first name. Added explicit `ValueError`/`TypeError` for bad inputs.
- `greet.py`: `greeting(first, last)` → `greeting(full_name)`, passes through to `format_name`.
- `report.py`: `roster` now iterates over strings instead of `(first, last)` tuples.

Edge case worth noting: if callers anywhere pass names with prefixes like `"Dr. Ada Lovelace"`, `rsplit` will produce `last="Lovelace"` and `first="Dr. Ada"` — probably the right behavior, but worth confirming if the data ever includes honorifics.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=15; wall=54.3s; answer_chars=641; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.02s"}

Answer:
````
All 3 tests pass. Here's what changed:

- **`names.py`**: `format_name(first, last)` → `format_name(full_name)`, splits on the last space with `rsplit(' ', 1)`. Added input validation (non-string and missing-space raise `ValueError`).
- **`greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes through directly.
- **`report.py`**: `roster` now iterates over full-name strings instead of `(first, last)` tuples.

Probing question: what should happen when a name has no whitespace at all (e.g. `format_name("Cher")`)? Right now it raises `ValueError` — is that the right contract, or should single-token names be returned as-is?
````
