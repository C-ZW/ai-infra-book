# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=44.2s; answer_chars=882; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Replaced the ad-hoc `print()` calls in `app.py` with the standard `logging` module:

- Module-level `logger = logging.getLogger(__name__)` — lets callers control output instead of spraying to stdout.
- Levels: `INFO` for start/done, `DEBUG` for per-item detail (noise stays filterable).
- Lazy `%s` formatting (args, not string concat) — avoids formatting cost when a level is disabled.
- Contextual messages: order count, per-item running total, final total.
- `basicConfig` with timestamp + level configured only under `__main__`, not at import — so importing `app` doesn't hijack the root logger.

I kept the change scoped to logging. One thing I deliberately left alone: `process` still assumes every item is numeric — a non-numeric order raises `TypeError` mid-loop and the `done` line never logs. Want me to add input validation and an error-path log, or keep it logging-only?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=64.1s; answer_chars=1417; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. `app.py` now uses the standard `logging` module instead of `print()`.

What changed and why:
- **Named module logger** (`getLogger(__name__)`), configured only under `__main__` — so importing `process` elsewhere won't hijack the root logger's config (library best practice).
- **Levels**: lifecycle messages at `INFO`, per-order detail at `DEBUG` — the noisy per-item line is now opt-in.
- **Runtime-configurable verbosity** via `LOG_LEVEL` env var (verified at INFO and DEBUG above).
- **Timestamps + level + logger name** in every line via the formatter.
- **Lazy `%s` formatting** instead of string concatenation — args aren't rendered unless the line actually emits.
- **Boundary validation**: non-list/tuple input and non-numeric items (including `bool`, which is a sneaky `int` subclass) now raise a typed, indexed error instead of crashing mid-loop or silently summing garbage.

I kept it on the stdlib `logging` module rather than going to structured JSON logging — appropriate for a script this size. If this is headed for a service where logs get ingested by something (Datadog, CloudWatch, ELK), say so and I'll switch to JSON output with a correlation/trace id.

One unhandled case worth your call: right now a bad order *aborts the whole batch* with the partial work discarded. For real order processing, is fail-fast what you want, or should it log-and-skip the bad order and still total the rest?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=42.2s; answer_chars=1315; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. Swapped the `print()` calls for the stdlib `logging` module (`app.py`).

What changed and why:
- Module logger (`getLogger(__name__)`) instead of `print` — output now carries timestamp, level, and source, and can be routed/filtered by whatever imports it.
- Levels: `INFO` for start/finish, `DEBUG` for per-item — so the noisy per-order line can be silenced in prod by raising the level.
- Lazy `%`-formatting (`logger.debug("...", x)`) instead of string concatenation — args aren't formatted when the level is disabled.
- `basicConfig` lives under `__main__` only, so importing this module doesn't hijack the root logger of whatever uses it.

I kept it to logging and left the function's behavior untouched, since that's what you asked for.

One assumption worth flagging: I read "better" as "use the logging module," not "emit JSON for a log aggregator." If this feeds something like Datadog/CloudWatch and you need structured/JSON output, that's a different shape — want me to go that way instead?

The most dangerous unhandled case I left in place: `len(orders)` and `total += o` both assume `orders` is a sized iterable of numbers — pass `None`, a generator, or `["a"]` and it throws before any "done" log fires. Should I make `process` defensive about its input, or is that out of scope for this change?
````
