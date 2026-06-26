# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=26.3s; answer_chars=144; files_added=[]; files_modified=[]; files_deleted=[]

Answer:
````
Which scripts are you targeting? The `tools/md-reader/` tools (build_reader, lint_book, etc.), the `prompts/_bench/` scripts, or something else?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=38.1s; answer_chars=676; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Changes made:

- `print()` → `logging` with `DEBUG`/`INFO`/`ERROR` levels — callers in prod can set `WARNING` to silence the per-item noise
- Timestamps and logger name in every line
- Invalid order values are caught and logged with index, value, and type instead of crashing
- `extra={}` carries structured context (order count, index, total) — a JSON handler (e.g. `python-json-logger`) picks these up as first-class fields; `basicConfig` silently ignores them, which is intentional

**Probing question:** What happens when `orders` is `None`? Right now `len(orders)` raises `TypeError` before the first log line fires — should the boundary check live here or in the caller?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=28.4s; answer_chars=910; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Changes made:

- `print()` → `logging` with level, timestamp, logger name, and correlation ID on every line
- `_CorrelationFilter` stamps a `[cid]` onto each record so all lines from one `process()` call are linkable in aggregated logs
- `correlation_id` param lets callers propagate an existing trace ID (e.g. from an HTTP request header) instead of generating a new one
- Input validated at the boundary — wrong type raises a named `TypeError`; non-numeric items are warned and skipped rather than crashing mid-loop
- `DEBUG` for per-item chatter (silent in prod by default), `INFO` for entry/exit, `WARNING` for skipped items, `ERROR` before raising

One unhandled case: `log.addFilter`/`removeFilter` isn't thread-safe — if `process()` is called concurrently, filters from different calls can bleed across. Worth considering a `logging.LoggerAdapter` instead if this runs in a thread pool or async context.
````
