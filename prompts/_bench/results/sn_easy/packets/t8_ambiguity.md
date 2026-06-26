# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=23.1s; answer_chars=515; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Replaced `print()` with `logging`:

- `basicConfig` sets a timestamp + level format
- Start/end use `INFO`; per-item loop uses `DEBUG` (reduces noise in production, enable with `logging.DEBUG` when needed)
- Both boundary log calls include structured `extra` fields (`order_count`, `total`) so they're grep/parse-friendly

What happens if `orders` contains a non-numeric value — `total += o` will raise a `TypeError` with no log context. Worth adding a `try/except` around the loop body if that's a realistic input?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=7; wall=27.1s; answer_chars=716; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Replaced bare `print()` calls with `logging`:

- **`logging.basicConfig`** adds timestamps and level names to every line
- Per-item logs are `DEBUG` (verbose, suppressible in production by raising the level to `INFO`)
- Start/end logs are `INFO` and carry structured context: `count=`, `total=`
- Module-scoped `logger = logging.getLogger(__name__)` means the source module is identifiable when this is imported

What's the most dangerous unhandled case here: what happens if an element of `orders` isn't numeric? `total += o` will raise a `TypeError` mid-loop with no log of which order caused it or how many had already been processed. Worth adding a `try/except` around the accumulation if the input is untrusted.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=24.9s; answer_chars=719; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Replaced the bare `print` calls with `logging`:

- Uses `logging.basicConfig` with a timestamp + level + name format
- `logger = logging.getLogger(__name__)` — name scoped to the module, composable with any caller's logging config
- Start/end messages are `INFO` with structured `extra` fields (`order_count`, `total`)
- Per-order trace is `DEBUG` — won't appear at default `INFO` level, but available when needed

What's the most dangerous unhandled case here: if `orders` contains non-numeric types, `total += o` raises `TypeError` with no logging of which order caused it. Worth adding a try/except inside the loop with `logger.error("invalid order", extra={"order": o, "error": str(e)})` if mixed input is possible.
````
