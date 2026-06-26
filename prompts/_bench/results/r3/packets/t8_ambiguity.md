# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=36.7s; answer_chars=802; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. Replaced the `print()` calls in `app.py` with the standard `logging` module:

- Module-level `logger = logging.getLogger(__name__)` — no output config at import time, so importing `app` won't hijack the root logger (library-safe).
- Levels: `INFO` for start/done, `DEBUG` for per-order detail.
- Lazy `%`-style args so messages aren't built when the level is disabled.
- Structured context: order count, running total, final total.
- `basicConfig` with timestamps/level/name lives only under `__main__`.

I kept `process`'s behavior identical and didn't touch input handling — that's the one gap worth naming: `len(orders)` raises `TypeError` on a generator or `None`, and a non-numeric item still crashes the loop. Want me to harden the input boundary too, or is logging-only the intended scope?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=49.2s; answer_chars=2289; files_added=['__pycache__/app.cpython-313.pyc']; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. Both the normal run and a debug run with deliberately bad input behave correctly.

## What changed

Replaced the bare `print()` calls with the `logging` module:

| Before | After |
|---|---|
| `print("starting")` | `logger.info(...)` with a count |
| `print("processing " + str(o))` | `logger.debug(...)` with lazy `%` formatting + index |
| `print("done")` | `logger.info(...)` with `processed`/`skipped`/`total` summary |
| crashes on `None`/strings | logs a `WARNING` and skips, keeps going |

Key improvements:
- **Levels** — per-item noise is `DEBUG` (silent by default), lifecycle is `INFO`, bad input is `WARNING`. You can dial verbosity without code changes.
- **Module-named logger** (`logging.getLogger(__name__)`) instead of the root logger, so callers can route or silence this module independently. Config lives only in the `__main__` block — importing `app` no longer hijacks the root logger.
- **Lazy formatting** (`logger.debug("... %s", o)`) — the message string is only built if the level is enabled, and it can't blow up an unrelated log line.
- **Timestamps + level + source** in every line via the format string.

## Failure modes I deliberately handled
- `orders=None` → explicit `ValueError` instead of `TypeError: 'NoneType' is not iterable` deep in the loop.
- Non-numeric items (`'oops'`, `None`) → logged and skipped, not a crash.
- `True`/`False` excluded — in Python `bool` is a subclass of `int`, so `True + total` would silently add 1; I treat booleans as invalid input rather than letting them corrupt the total.
- A non-`len()`-able iterable (generator) → `_safe_len` returns `-1` for the log rather than throwing.

## Decisions worth confirming
I made two judgment calls you may want to override: (1) bad items are **skipped with a warning** rather than failing the whole batch — if these are financial orders, silently skipping may be the wrong default and you'd want a hard error; (2) I left the root config at `INFO`. Tell me if either should change.

One thing I did *not* address: this still logs to stdout/stderr with no rotation or structured (JSON) output. **If a downstream system parses these logs, are you relying on the human-readable format above, or do you need structured/JSON output before this goes anywhere near a log aggregator?**
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=42.8s; answer_chars=1137; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Replaced the `print()` calls in `app.py` with the `logging` module. Changes:

- Module-level `logger = logging.getLogger(__name__)` — named, so output is attributable and filterable.
- Levels: `INFO` for start/done, `DEBUG` for per-item — you can dial verbosity without code edits.
- Lazy `%`-formatting (`logger.debug("...", o)`) so messages aren't built when the level is suppressed.
- Richer context: order count, `i/len` progress, and the final total.
- `basicConfig` (timestamp + level + logger name) lives only in the `__main__` block, so importing `process` as a library doesn't hijack the root logger config.

Verified it runs (output above).

One deliberate non-change worth flagging: I kept scope to logging and did **not** add input validation. `process` still assumes `orders` is a sized, iterable, summable collection — pass a generator and `len()` raises `TypeError`; pass `None` and it dies before the first log line; pass `["a"]` and `+=` blows up mid-loop with a half-finished total and no error log. Want me to make `process` itself defensive (guard the input, log failures), or is logging-only the right boundary here?
````
