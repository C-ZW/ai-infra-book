# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=28.1s; answer_chars=191; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Which file(s) are you referring to? The current session's working directory is `prompts/_bench/_sandboxes/…` — are you talking about the bench scripts, the md-reader tools, or something else?
````

### Candidate B

Behavioral telemetry: exit=-9; timed_out=True; turns=None; wall=180.0s; answer_chars=0; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
(empty answer)
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=30.7s; answer_chars=542; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Changes made:
- Replaced `print()` with Python's `logging` module using a named logger (`__name__`)
- Added timestamp + level to every log line via `basicConfig`
- Surfaced useful context: order count at start, total at finish
- Used `%`-style formatting (lazy — no string built if the level is filtered out)

What's the most dangerous unhandled case here: if `orders` contains a non-numeric value, `total += o` raises a `TypeError` with no log of which item caused it. Worth catching that at the boundary if callers don't guarantee the type.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=30.2s; answer_chars=621; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Changes made:

- Swapped bare `print` for `logging` with a timestamped, leveled format
- `INFO` for the entry/exit boundary (order count, total, elapsed ms) — these are always useful
- `DEBUG` for per-order detail — noisy in production, silenceable by raising the log level
- Added `time.monotonic()` so the exit log shows how long the call actually took

One open question: `orders` is trusted to contain addable values right now — if a caller passes mixed types (`[1, "two", 3]`), the `total += o` will raise a `TypeError` that's currently uncaught. Worth adding input validation if this is called from untrusted input.
````
