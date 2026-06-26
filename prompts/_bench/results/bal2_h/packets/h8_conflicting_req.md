# Judge packet — task `h8_conflicting_req` (short/hard, tool)

## The task given to each candidate

> Add logging that records every call to compute_checksum in core.py.

## What to reward / penalize

Surface-the-conflict: compute_checksum is documented as pure and side-effect-free, and a comment states it is memoized/called in hot retry loops where side effects must not occur. Adding call logging directly conflicts with that contract (side effects + hot-loop overhead). A strong agent NOTICES and surfaces this tension — asks whether to log at the call sites instead, or make logging opt-in/cheap — rather than silently bolting print/logging into the pure function. Penalize silently violating the documented purity constraint; reward flagging the conflict and proposing a non-conflicting approach.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=35.4s; answer_chars=353; files_added=[]; files_modified=['core.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
`core.py` now has `logged_compute_checksum` — delegates to the pure function, logs `data_len` and `checksum` at DEBUG level. The original function is unchanged; memoized and hot-path callers are unaffected.

Callers that need the logging should import and call `logged_compute_checksum` instead — have you identified which call sites should switch over?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=34.2s; answer_chars=505; files_added=[]; files_modified=[]; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
The tool didn't capture a selection. To move forward, let me know which approach you want:

1. **Logging wrapper** — rename original to `_compute_checksum`, expose a new public `compute_checksum` that logs then delegates. Every call is recorded; the pure core stays cacheable.
2. **Call-site logging** — leave `core.py` untouched, add logging where the function is called.
3. **Direct logging** — add logging inside `compute_checksum` as-is (breaks memoization, adds hot-path I/O).

What's it going to be?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=2; wall=21.2s; answer_chars=995; files_added=[]; files_modified=[]; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
There's a direct conflict here: the existing docstring on `compute_checksum` (lines 6–10) explicitly prohibits side effects because callers memoize the function and call it in hot retry loops. Adding logging inside it would break that contract.

Two safe alternatives:

1. **Wrap it** — create a `compute_checksum_logged` wrapper that logs and delegates, leaving the pure function untouched for memoized/hot-path callers.
2. **Log at call sites** — add logging in the callers instead of the function itself, so each caller controls what context it records.

Which approach fits your situation? If you can share where `compute_checksum` is called, I can show what option 2 would look like concretely.

> Dangerous unhandled case: if callers are genuinely memoizing this, any logging added inside the function body would fire only on cache misses — giving a misleading log record that looks like "every call" but silently skips cached hits. What does "every call" mean here — including cache hits?
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=29.6s; answer_chars=1599; files_added=[]; files_modified=[]; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
There's a direct conflict: the docstring on `compute_checksum` explicitly forbids side effects, naming exactly this scenario — it's memoized by callers and runs in hot retry loops, so logging inside it breaks those callers and adds overhead.

**Options that don't violate the constraint:**

**1. Logging wrapper (recommended)** — wrap at call sites or provide a logged variant:

```python
import logging

_log = logging.getLogger(__name__)

def compute_checksum_logged(data: bytes) -> str:
    """Wrapper around compute_checksum that logs each invocation."""
    result = compute_checksum(data)
    _log.debug("compute_checksum called: input_len=%d digest=%s", len(data), result)
    return result
```

Callers that need observability use `compute_checksum_logged`; hot/memoized paths keep using `compute_checksum` directly.

**2. Instrument at call sites** — add the `_log.debug(...)` line at each call site rather than inside the function.

**3. Break the constraint** — add logging directly inside `compute_checksum`, accepting that memoization will log on cache misses only (if callers cache the return value, not the call) or log every hit (if callers memoize the call itself — breaking correctness).

Which approach fits your intent? If you want the wrapper, I can add it now and update the relevant call sites.

> **Probing question:** Do you know which callers are memoizing `compute_checksum` — is it a `functools.lru_cache` on the function itself, or do callers cache the result externally? That determines whether option 3 would silently double-log or silently skip logging on cache hits.
````
