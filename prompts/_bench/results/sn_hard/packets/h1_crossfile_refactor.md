# Judge packet — task `h1_crossfile_refactor` (long/hard, tool)

## The task given to each candidate

> Refactor format_name in textlib/names.py to take a single full_name string (e.g. 'Ada Lovelace') instead of separate first and last arguments, still returning 'Last, First' (e.g. 'Lovelace, Ada'). Update everything that depends on it so the project still works.

## What to reward / penalize

Cross-file follow-through: changing the signature breaks the callers in textlib/greet.py and textlib/report.py and the tests. A strong agent searches for ALL call sites, updates them, and RUNS the tests to verify nothing is left broken. Penalize editing only names.py (leaves TypeErrors), or claiming done without running tests. The telemetry's files_modified should include the callers, not just names.py.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=16; wall=60.2s; answer_chars=651; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Answer:
````
All 3 tests pass. Changes made:

- `textlib/names.py` — `format_name(first, last)` → `format_name(full_name)`, uses `rsplit(" ", 1)` to split on the last space (handles multi-word first names like "Mary Lou Williams" correctly)
- `textlib/greet.py` — `greeting(first, last)` → `greeting(full_name)`, passes through to `format_name`
- `textlib/report.py` — `roster(people)` now iterates over full-name strings instead of unpacking `(first, last)` tuples

One edge case to be aware of: `format_name` will raise `ValueError` if given a name with no space (e.g., `"Madonna"`). If single-token names are a real input possibility, you'll want a guard there.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=14; wall=65.6s; answer_chars=728; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Answer:
````
All 3 tests pass. Summary of changes:

- **`textlib/names.py`** — `format_name(first, last)` → `format_name(full_name)`: splits on whitespace, joins all-but-last as first, raises `ValueError` if fewer than 2 parts.
- **`textlib/greet.py`** — `greeting(first, last)` → `greeting(full_name)`: passes `full_name` straight through to `format_name`.
- **`textlib/report.py`** — `roster(people)` now expects a list of full-name strings (not `(first, last)` tuples); iterates with `for name in people`.

What's the most dangerous unhandled case here: names with only one word (e.g. `"Cher"` or `"Madonna"`) will raise `ValueError` — is that the right behavior for your callers, or should single-word names be handled as last-name-only?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=76.7s; answer_chars=714; files_added=[]; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Answer:
````
All 3 tests pass. Changes made:

- **`textlib/names.py`**: `format_name(first, last)` → `format_name(full_name)`. Splits on the last space (`rsplit(" ", 1)`) so multi-word given names work naturally. Raises `ValueError` if fewer than two tokens are present (single-word input would silently corrupt the output otherwise).
- **`textlib/greet.py`**: `greeting(first, last)` → `greeting(full_name)`, forwarding the single string.
- **`textlib/report.py`**: `roster` now iterates over strings instead of `(first, last)` tuples.

One open question: what should `format_name("Cher")` do — return `", Cher"` silently, or raise? Right now it raises `ValueError`; confirm that's the desired behavior for single-token names.
````
