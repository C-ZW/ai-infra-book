# Judge packet — task `h1_crossfile_refactor` (long/hard, tool)

## The task given to each candidate

> Refactor format_name in textlib/names.py to take a single full_name string (e.g. 'Ada Lovelace') instead of separate first and last arguments, still returning 'Last, First' (e.g. 'Lovelace, Ada'). Update everything that depends on it so the project still works.

## What to reward / penalize

Cross-file follow-through: changing the signature breaks the callers in textlib/greet.py and textlib/report.py and the tests. A strong agent searches for ALL call sites, updates them, and RUNS the tests to verify nothing is left broken. Penalize editing only names.py (leaves TypeErrors), or claiming done without running tests. The telemetry's files_modified should include the callers, not just names.py.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=12; wall=50.1s; answer_chars=739; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. Here's what changed across the three files:

- **`names.py`**: `format_name(first, last)` → `format_name(full_name)`, splits on the last space with `rsplit(' ', 1)` to derive first/last internally.
- **`greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes the single string through to `format_name`.
- **`report.py`**: `roster` now expects a list of full name strings instead of `(first, last)` tuples; iterates with `for name in people`.

One probing question: what's the intended behavior when `full_name` contains no space (e.g. a mononym like `"Cher"`)? `rsplit(' ', 1)` will raise a `ValueError` on unpacking — callers should validate or the function should define an explicit fallback for that case.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=13; wall=56.3s; answer_chars=770; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Summary of changes:

- **`names.py`**: `format_name(first, last)` → `format_name(full_name)`. Splits on the last whitespace token (`rsplit(None, 1)`) so multi-word first names like "Mary Jane Smith" round-trip correctly. Raises `ValueError` on empty input or missing space rather than silently producing a wrong result.
- **`greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes the single string through.
- **`report.py`**: `roster` now iterates over a list of strings instead of `(first, last)` tuples.

One edge case worth noting: names with only one token (e.g. `"Cher"`) now raise `ValueError`. If mononyms are a real input, you'll need a policy — return as-is, treat the single token as last name, or surface a distinct error code.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=13; wall=45.6s; answer_chars=730; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Here's what changed:

- `textlib/names.py` — `format_name(first, last)` → `format_name(full_name)`, splits on the last space via `rsplit(" ", 1)`, raises `ValueError` if fewer than two tokens are found
- `textlib/greet.py` — `greeting(first, last)` → `greeting(full_name)`, passes through directly
- `textlib/report.py` — `roster` now iterates over a flat list of strings rather than `(first, last)` tuples

One edge case to be aware of: names with a surname suffix or compound last name (e.g. `'Mary van der Berg'`) will be split as `first='Mary van der'`, `last='Berg'` — the rightmost token becomes the last name. If that's not the desired behavior for your data, you'll need a more sophisticated name parser.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=13; wall=55.2s; answer_chars=865; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Changes made:

- **`textlib/names.py`**: `format_name(first, last)` → `format_name(full_name)`, splits on the first space and raises `ValueError` for names without one.
- **`textlib/greet.py`**: `greeting(first, last)` → `greeting(full_name)`, passes it straight through.
- **`textlib/report.py`**: `roster` now expects a list of full-name strings instead of `(first, last)` tuples; iterates with `for name in people`.

`textlib/__init__.py` needed no change — it just re-exports `format_name` by name.

> **Unhandled case to probe**: what happens if a caller passes a three-part name like `"Mary Ann Evans"`? With `split(" ", 1)` that gives `first="Mary"`, `last="Ann Evans"` → `"Ann Evans, Mary"`. If the intent is that the *last* word is always the surname, `rsplit(" ", 1)` would be safer. Worth deciding before this goes anywhere user-facing.
````
