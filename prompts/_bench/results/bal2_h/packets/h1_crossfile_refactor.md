# Judge packet — task `h1_crossfile_refactor` (long/hard, tool)

## The task given to each candidate

> Refactor format_name in textlib/names.py to take a single full_name string (e.g. 'Ada Lovelace') instead of separate first and last arguments, still returning 'Last, First' (e.g. 'Lovelace, Ada'). Update everything that depends on it so the project still works.

## What to reward / penalize

Cross-file follow-through: changing the signature breaks the callers in textlib/greet.py and textlib/report.py and the tests. A strong agent searches for ALL call sites, updates them, and RUNS the tests to verify nothing is left broken. Penalize editing only names.py (leaves TypeErrors), or claiming done without running tests. The telemetry's files_modified should include the callers, not just names.py.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=40.1s; answer_chars=659; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. The changes made:

- **`names.py`**: `format_name(first, last)` → `format_name(full_name)`, using `rsplit(" ", 1)` to split on the last space (handles multi-word first names like "Mary Ann Evans").
- **`greet.py`**: `greeting(first, last)` → `greeting(full_name)`, delegates to the updated `format_name`.
- **`report.py`**: `roster` now expects a list of full-name strings instead of `(first, last)` tuples.

What's the most dangerous unhandled case here? A name with no space — `format_name("Madonna")` will raise `ValueError: not enough values to unpack`. If single-word names are ever possible in your data, you'll want an explicit guard.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=15; wall=45.2s; answer_chars=652; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Changes made:

- **`names.py`**: `format_name(first, last)` → `format_name(full_name)`, splits on the last space (`rsplit(" ", 1)`) so multi-word first names like `"Mary Jane Watson"` map correctly to `"Watson, Mary Jane"`.
- **`greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes it straight through.
- **`report.py`**: `roster` now expects a list of full-name strings instead of `(first, last)` tuples.

One unhandled case worth noting: `format_name` will raise `ValueError` on a single-token string (no space). If callers can receive names without a last name, you'll want an explicit guard and a defined fallback.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=13; wall=55.4s; answer_chars=686; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Changes made:

- `textlib/names.py`: `format_name(first, last)` → `format_name(full_name)`, splits on the last space via `rsplit(" ", 1)` and raises `ValueError` if no space is found.
- `textlib/greet.py`: `greeting(first, last)` → `greeting(full_name)`, passes it straight through.
- `textlib/report.py`: `roster` docstring and comprehension updated — was unpacking `(first, last)` tuples, now iterates plain name strings.

Worth asking: what's the intended handling of names with no last name (e.g. `"Cher"` or `"Madonna"`)? The current `ValueError` is explicit and debuggable, but if single-token names are valid in your data, you'd want a defined fallback instead.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=17; wall=43.5s; answer_chars=688; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. Changes made:

- **`textlib/names.py`**: `format_name(first, last)` → `format_name(full_name)`, using `rsplit(" ", 1)` to split on the rightmost space. Raises `ValueError` on a single-token name (no detectable last name).
- **`textlib/greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes it straight through to `format_name`.
- **`textlib/report.py`**: `roster` now iterates over full-name strings instead of `(first, last)` tuples.

Probing question: what should happen with names like `"Cher"` or `"Madonna"`? Right now `format_name` raises — is that the desired behavior, or should single-token names pass through unchanged (e.g. `"Cher"` → `"Cher"`)?
````
