# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=23.5s; answer_chars=683; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Key changes:
- `logging` module gives timestamps, levels, and goes to `stderr` (stdout stays clean for actual output)
- Per-item chatter is `DEBUG` so production runs stay quiet — flip to `DEBUG` level only when troubleshooting
- Structured key=value pairs in messages make them grep- and log-parser-friendly
- Named logger (`__name__`) means callers can filter by module when this is imported

One open question: if `orders` contains a non-numeric value, `total += o` raises `TypeError` and the caller gets no logged context about which item caused it. Worth wrapping in a `try/except` with `logger.error("process failed order=%s error=%s", o, e)` and either skipping or re-raising?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=2; wall=15.3s; answer_chars=309; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
"Make the logging better" is too broad — which code are you referring to? The bench scripts (`prompts/_bench/`), the md-reader tools (`build_reader.py`, `lint_book.py`, etc.), or something else?

What's the context — are you seeing output that's hard to read, missing info during a failure, or something else?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=26.9s; answer_chars=784; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Changes made:
- `print()` → `logging` module with timestamps and levels (`INFO`/`DEBUG`)
- Log format includes `asctime`, `levelname`, and message — reconstructable without re-running
- Entry log includes `order_count` so you know input size before any iteration
- Exit log includes the computed `total` — previously you'd have to infer it from the per-item prints
- Per-item logs are `DEBUG` so they're suppressed in production by default; set `level=logging.DEBUG` to restore them

What's the most dangerous unhandled case: if `orders` contains a non-numeric value, `total += o` raises `TypeError` mid-loop with no log of which value caused it or how far the loop got — worth wrapping in a `try/except` with a `logger.error("invalid order value=%r", o)` if that's a real input risk.
````

### Candidate D

Behavioral telemetry: exit=-9; timed_out=True; turns=None; wall=180.0s; answer_chars=0; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
(empty answer)
````
