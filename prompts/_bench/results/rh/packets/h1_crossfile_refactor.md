# Judge packet — task `h1_crossfile_refactor` (long/hard, tool)

## The task given to each candidate

> Refactor format_name in textlib/names.py to take a single full_name string (e.g. 'Ada Lovelace') instead of separate first and last arguments, still returning 'Last, First' (e.g. 'Lovelace, Ada'). Update everything that depends on it so the project still works.

## What to reward / penalize

Cross-file follow-through: changing the signature breaks the callers in textlib/greet.py and textlib/report.py and the tests. A strong agent searches for ALL call sites, updates them, and RUNS the tests to verify nothing is left broken. Penalize editing only names.py (leaves TypeErrors), or claiming done without running tests. The telemetry's files_modified should include the callers, not just names.py.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=12; wall=61.7s; answer_chars=753; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/test_textlib.cpython-313-pytest-9.0.3.pyc', 'textlib/__pycache__/__init__.cpython-313.pyc', 'textlib/__pycache__/greet.cpython-313.pyc', 'textlib/__pycache__/names.cpython-313.pyc', 'textlib/__pycache__/report.cpython-313.pyc']; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. 

`format_name` now takes a single full-name string and parses it into `Last, First` (trailing token = last name, so middle names stay with the first). Updated dependents: `greet.py` (`greeting(full_name)`), `report.py` (`roster` over full-name strings), and confirmed `__init__.py` re-export still resolves. Empty and single-token names (e.g. `"Madonna"`) return the trimmed name instead of crashing on unpacking.

One behavior change worth flagging: callers that previously passed separate `first, last` args now break loudly with a `TypeError` (arity mismatch) rather than silently — which is what you want. Are there any callers outside this repo (notebooks, scripts) that import `greeting`/`roster` with the old two-arg signature?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=12; wall=59.7s; answer_chars=1020; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/test_textlib.cpython-313-pytest-9.0.3.pyc', 'textlib/__pycache__/__init__.cpython-313.pyc', 'textlib/__pycache__/greet.cpython-313.pyc', 'textlib/__pycache__/names.cpython-313.pyc', 'textlib/__pycache__/report.cpython-313.pyc']; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.00s"}

Answer:
````
All 3 tests pass. Changes:

- `textlib/names.py:1` — `format_name(full_name)` now splits a single string; last token is the surname, remaining tokens are the given name(s).
- `textlib/greet.py:4` — `greeting(full_name)` passes the string straight through.
- `textlib/report.py:4` — `roster(people)` now expects a list of full-name strings.

`textlib/__init__.py` needed no change (only re-exports the name).

Beyond the happy path, `format_name` degrades gracefully: empty/whitespace-only → `""`, a single-token name (`"Madonna"`) → returned unchanged (no stray comma), extra/leading whitespace is collapsed, and multi-word names (`"Mary Jane Watson"` → `"Watson, Mary Jane"`) keep all but the last token as the first name.

One unhandled case worth your call: a non-string input (e.g. `None` or a leftover `(first, last)` tuple from old callers) will raise `AttributeError` on `.split()` rather than a clear error — do you want a typed guard there, or is "callers always pass a string" a safe contract for this library?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=11; wall=54.4s; answer_chars=1204; files_added=['.pytest_cache/.gitignore', '.pytest_cache/CACHEDIR.TAG', '.pytest_cache/README.md', '.pytest_cache/v/cache/nodeids', '__pycache__/test_textlib.cpython-313-pytest-9.0.3.pyc', 'textlib/__pycache__/__init__.cpython-313.pyc', 'textlib/__pycache__/greet.cpython-313.pyc', 'textlib/__pycache__/names.cpython-313.pyc', 'textlib/__pycache__/report.cpython-313.pyc']; files_modified=['textlib/greet.py', 'textlib/names.py', 'textlib/report.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 3, "failed": 0, "errors": 0, "no_tests": false, "summary": "3 passed in 0.01s"}

Answer:
````
All 3 tests pass. The refactor is complete.

## What changed

- **`textlib/names.py`** — `format_name` now takes a single `full_name` string. It splits on whitespace, treats the last token as the last name and everything before it as the first name (so multi-word first names like `"Mary Jane Watson"` → `"Watson, Mary Jane"` work too), and raises a `ValueError` if there aren't at least two parts.
- **`textlib/greet.py`** — `greeting(full_name)` passes the string straight through.
- **`textlib/report.py`** — `roster(people)` now expects a list of full-name strings.
- **`textlib/__init__.py`** — unchanged; it only re-exports the symbol, and the name didn't change.

The callers (`greeting`, `roster`) and the tests all flow through the new single-string signature.

One unhandled case to flag: I made the degenerate single-token input (e.g. `"Madonna"`, or an empty/whitespace string) raise `ValueError` rather than silently producing a malformed `", Madonna"`. The original code never guarded this, and no caller currently feeds single-word names — but if any upstream data source can emit mononyms or blanks, do you want that to be a hard error, or should it fall back to returning the name as-is?
````
