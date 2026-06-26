# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=43.9s; answer_chars=1226; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. `app.py:1` now uses the `logging` module instead of `print()`:

- **Module-level logger** (`getLogger(__name__)`) — libraries shouldn't print; callers control output.
- **Levels**: lifecycle events at `INFO`, per-item noise at `DEBUG`.
- **Lazy `%` formatting** (`logger.debug("...", o)`) — args only render if the level is enabled, and no string concatenation that explodes on non-str types.
- **`basicConfig` only under `__main__`** — configuring handlers at import time would hijack logging for anyone who imports `process`.
- Final line now reports the count and total. Behavior is otherwise unchanged.

One thing I deliberately did *not* change: `process` still assumes `orders` is a sized iterable of numbers. `len(orders)` raises `TypeError` on a generator, and `total += o` raises on a non-numeric element — both before any "done" log fires. If `process` is meant to accept arbitrary iterables or untrusted input, the logging should sit inside validation/`try`-`except` so a mid-loop failure is recorded rather than crashing silently into a traceback.

Do you want me to keep this as a pure logging swap, or harden `process` against malformed `orders` (generators, empty input, non-numeric items) while I'm here?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=57.0s; answer_chars=1293; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Verified at both levels. Same total (`6`), behavior unchanged.

**What changed**
- **Real `logging`, not `print`** — a module-level `logger`, so output can be silenced, raised, reformatted, or routed (file/JSON/aggregator) without touching `process()`.
- **Levels** — start/finish are `INFO`; per-item noise is `DEBUG` (hidden by default, shown via `LOG_LEVEL=DEBUG`).
- **Lazy `%` formatting** — `logger.debug("...%r", o)` only builds the string if DEBUG is enabled, instead of always concatenating.
- **Context** — order count and final total are logged, so a run is reconstructable from the log alone. Timestamps + level + logger name on every line.
- **Config lives in `__main__`** — the library function only emits records; the entry point decides where they go. Verbosity is controlled by the `LOG_LEVEL` env var.

**Deliberately left out** (since you said "logging," not "make it bulletproof"): I kept `process()`'s contract identical. The biggest *unhandled* hazard is still there — `len(orders)` raises `TypeError` if `orders` is `None` or a generator, and `total += o` raises on a non-numeric item, both before any error gets logged.

Want me to add input validation + an exception-logging path (`logger.exception(...)`) around that, or keep this scoped strictly to the logging swap?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=45.8s; answer_chars=976; files_added=['__pycache__/app.cpython-313.pyc']; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. Changes:

- Replaced `print()` with the stdlib `logging` module — a named `orders` logger, with levels (`info`/`debug`/`error`) and timestamped formatted output configured at the entrypoint, not in library code.
- Structured context via `extra=` (counts, indices, totals) instead of string concatenation.
- The loop now validates each item and **skips + logs** non-numbers instead of crashing — the original `total += o` would have thrown on any non-numeric order. Note `True` is excluded too, since `bool` is an `int` subclass.

Verified: happy path logs with timestamps; `[1, 'x', 2, True, 3.5]` logs two skips and returns `6.5` instead of raising.

One deliberate scope call: library code doesn't call `basicConfig` (only the `__main__` block does), which is why the bad-input test prints bare messages — the caller owns handler config. If you'd rather this emit JSON lines for ingestion (Datadog/CloudWatch/etc.), that's a different formatter — want me to switch it?
````
