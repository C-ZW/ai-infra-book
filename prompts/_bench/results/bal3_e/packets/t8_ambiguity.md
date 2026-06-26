# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=24.9s; answer_chars=860; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Key changes:
- Swapped `print` for `logging` — now you get timestamps, levels, and the module name automatically.
- Used `INFO` for entry/exit boundary events and `DEBUG` for per-item loop noise (so production can silence the loop without losing the boundary signals).
- Structured key=value pairs (`count=`, `value=`, `total=`) instead of concatenated strings — grep- and splunk-friendly.
- Format string args passed separately (`%s`, not f-strings) — avoids paying string formatting cost if the level is filtered out.

Probing question: if any element of `orders` is non-numeric, `total += o` raises a `TypeError` with no logged context about *which* order caused it and what its value was — the caller only sees an undecorated exception. Should the loop catch that per-item and log `logger.error("invalid order value=%r, skipping", o)`, or let it propagate?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=12.3s; answer_chars=403; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Which logging are you referring to? There are several candidates:

1. **`build_reader.py`** — the book packager
2. **`lint_book.py`** — the linter
3. **`verify_book.py`** — the fact-checker
4. **`gate_book.py`** — the quality gate
5. **Something in `book/_meta/`** — the maintenance scan log

Or are you talking about a specific script that's been running recently where the output wasn't useful enough?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=39.3s; answer_chars=668; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Changes made:
- Replaced bare `print` calls with the `logging` module (levels: `INFO` for start/end, `DEBUG` for per-order noise)
- Added timestamps and log levels to every line via `basicConfig` format
- Added structured key=value context (`count`, `running_total`, `total`) so a log line is parseable without guessing
- Per-order lines are `DEBUG` so they don't flood production but are available when needed

What's the most dangerous unhandled case here: `orders` containing a non-numeric value will raise a `TypeError` mid-loop with no log of which order caused it. Worth adding a `try/except` around the `total += o` line if input comes from outside the process.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=25.5s; answer_chars=786; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Changes made:

- **`print` → `logging`** — structured, leveled, timestamped; `DEBUG` lines for per-item processing are suppressed at the default `INFO` level but available when needed.
- **Trace ID** — auto-generated UUID per call (or injectable from outside), threaded through every log line so a 3am failure can be correlated end-to-end.
- **Structured fields** — `key=value` tokens (`order_count`, `index`, `total`) instead of free-form strings, so they're greppable and parseable by log aggregators.
- **Input validation** — `TypeError` on a non-list, warning + skip on non-numeric entries, rather than letting `+=` blow up with a cryptic `TypeError` mid-loop.

What calls `process()` — is a trace ID being threaded in from the request layer, or does each call need to mint its own?
````
