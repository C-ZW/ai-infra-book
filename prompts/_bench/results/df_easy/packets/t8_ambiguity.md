# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=2; wall=11.9s; answer_chars=429; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
What specifically do you want better logging on? There are several candidates here:

1. **`build_reader.py`** — the main book builder
2. **`lint_book.py`** / **`verify_book.py`** — quality gate scripts
3. **`build_shelf.py`** / `check_diagrams.py` — smaller utilities

Which script(s), and what's the pain point — too quiet (silent failures), too noisy, no timestamps, hard to correlate errors to source files, or something else?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=33.1s; answer_chars=795; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Key improvements:

- **`logging` module** instead of `print()` — output goes to stderr by default, carries timestamps and levels
- **Log levels**: `INFO` for lifecycle events, `DEBUG` for per-item detail (callers can suppress debug noise with `logging.WARNING`)
- **`%s` / `%d` formatting** instead of string concatenation — avoids building the string when the log level is filtered out
- **Named logger** (`__name__`) so the source module is identifiable in larger apps

What's the dangerous unhandled case here: if `orders` contains non-numeric values, `total += o` will raise a `TypeError` after partial accumulation — the INFO "done" log never fires and the caller gets an exception with no log of which order triggered it. Worth adding a per-item `try/except` if order values are untrusted.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=2; wall=11.5s; answer_chars=265; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Which logging are you referring to? Options:

1. **`md-reader` Python tools** (`build_reader.py`, `lint_book.py`, `verify_book.py`, etc.) — their console output/progress messages
2. **A specific script** — paste the path or name
3. **Something else in the project**
````
