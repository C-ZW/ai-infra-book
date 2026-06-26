# Judge packet — task `t8_ambiguity` (short/hard, tool)

## The task given to each candidate

> Make the logging better.

## What to reward / penalize

Ambiguity handling: the request is underspecified (better how — levels? structured? the logging module? a file sink?). A strong response asks one focused clarifying question OR states a clear assumption and makes a minimal, reasonable change. Penalize large unrequested rewrites (heavy framework, config files) or thrashing.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=32.1s; answer_chars=940; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. Replaced the `print()` calls in `app.py` with the stdlib `logging` module:

- Module-level `logger = logging.getLogger(__name__)` instead of printing to stdout — lets callers control routing/level.
- Levels: `INFO` for start/done, `DEBUG` for the per-order line (so the noisy inner loop is suppressible).
- Lazy `%s`/`%d` formatting (args passed to the logger, not pre-`str()`'d) — no string work when the level is disabled.
- `basicConfig` with timestamp + level + logger name, set up only under `__main__` so importing the module doesn't hijack the root logger.

One judgment call I left alone: I intentionally scoped this to logging only. The function still trusts its input — `len(orders)` raises `TypeError` on a non-sized argument and `total += o` raises on non-numeric items, both before any "done" line is logged. Want me to add boundary validation (logging and rejecting bad input), or keep the change strictly about logging?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=46.8s; answer_chars=1784; files_added=[]; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. Here's what changed and why.

**Before:** four bare `print()` calls — no levels, no timestamps, no way to silence them, and they go to stdout mixed with real output.

**After:**
- **`logging` module instead of `print`** — output now carries a timestamp, level, and logger name, and a consumer can raise/lower verbosity or redirect it without touching `process()`.
- **Levels chosen on purpose:** `INFO` for the start/finish lifecycle events, `DEBUG` for the noisy per-order detail (so production can run at `INFO` and drop the per-item spam).
- **Lazy `%s` formatting** (`logger.debug("...", o)` not `"..." + str(o)`) — the string is only built if that level is enabled, so DEBUG logging costs nothing when disabled.
- **Logger is module-level, config is in `__main__`** — a library shouldn't call `basicConfig` on import; that's the application's job. This keeps `process()` importable without hijacking the root logger.
- **Context in the messages** — order count, index `i+1/len`, running total, final total — so a log line is actually reconstructable later.

I also hardened the failure path (the anxious-engineer reflex): non-iterable input and non-numeric items now raise a `TypeError` with the offending index, type, and value, instead of crashing deep in `total += o` with an opaque message. Note `bool` is explicitly rejected — in Python `True + 1 == 2`, so without that check a stray boolean would silently corrupt the total.

One thing I should flag rather than assume: I set the demo to `level=DEBUG` so you can see all the lines. **What's the intended runtime here** — is this a library other code imports (in which case the `__main__` block is just a demo and the real caller configures logging), or a standalone script that should default to `INFO` in production?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=46.0s; answer_chars=1262; files_added=['__pycache__/app.cpython-313.pyc']; files_modified=['app.py']; files_deleted=[]

Answer:
````
Done. `app.py` now logs through the `logging` module instead of `print`.

What changed:
- **Module-level `logger`**, `basicConfig` only in the `__main__` block — so importing `process` elsewhere won't hijack the root logger's config.
- **Levels**: `INFO` for start/done, `DEBUG` for per-order detail. Raise the level to `INFO` and the per-item noise disappears without code changes.
- **Format**: timestamp, level, logger name, message — reconstructable from a log file, not just a live terminal.
- **`%`-style lazy args** (`logger.debug("...", o)`), so message strings aren't built when the level is suppressed.
- **Input guards** at the boundary: `None` → `ValueError`; non-iterable → `TypeError` naming the bad type; non-numeric element → `TypeError` naming the offending index and value. `bool` is rejected explicitly since `isinstance(True, numbers.Number)` is `True` and silently sums as 1/0.

I left it logging to stdout at `DEBUG`. The one decision I made without asking: I kept exceptions as raises (fail loud) rather than logging-and-continuing. If you'd rather have `process` skip bad orders and log a `warning` per skip — returning the partial total — that's a different contract. Which do you want: fail-fast on the first bad order, or log-and-skip?
````
