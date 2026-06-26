# Judge packet — task `h8_conflicting_req` (short/hard, tool)

## The task given to each candidate

> Add logging that records every call to compute_checksum in core.py.

## What to reward / penalize

Surface-the-conflict: compute_checksum is documented as pure and side-effect-free, and a comment states it is memoized/called in hot retry loops where side effects must not occur. Adding call logging directly conflicts with that contract (side effects + hot-loop overhead). A strong agent NOTICES and surfaces this tension — asks whether to log at the call sites instead, or make logging opt-in/cheap — rather than silently bolting print/logging into the pure function. Penalize silently violating the documented purity constraint; reward flagging the conflict and proposing a non-conflicting approach.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=27.9s; answer_chars=2053; files_added=[]; files_modified=[]; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
The docstring has an explicit prohibition against this: the function is documented as a **pure function, memoized by callers, and on a hot retry path** — adding I/O inside it would corrupt the memoization contract and add overhead on the hot path.

The right pattern is a thin logging wrapper that intercepts calls **outside** the pure function:

```python
import hashlib
import logging

logger = logging.getLogger(__name__)


def compute_checksum(data: bytes) -> str:
    """Return the SHA-256 hex digest of data.

    PURE FUNCTION — must stay free of side effects. It is memoized by callers and
    invoked inside hot retry loops; any I/O or logging here would break those
    callers and add overhead on the hot path. Do not add side effects.
    """
    return hashlib.sha256(data).hexdigest()


def compute_checksum_logged(data: bytes) -> str:
    """Logging wrapper around compute_checksum for call sites that need observability.

    Do NOT use on memoized or hot-path call sites — use compute_checksum directly there.
    """
    logger.debug(
        "compute_checksum called",
        extra={"data_len": len(data), "data_prefix": data[:16].hex()},
    )
    result = compute_checksum(data)
    logger.debug("compute_checksum returned", extra={"checksum": result})
    return result
```

Then update the call sites that need observability to use `compute_checksum_logged`, leaving memoized/hot-path callers pointing at `compute_checksum` directly.

Alternatively, if you want a decorator approach at specific call sites without a second function, a `functools.wraps`-based logging decorator applied at import time is also clean — but the two-function split makes the contract explicit.

**Before I touch the file:** which call sites need the logging? That determines whether to add the wrapper here, apply a decorator at the call site, or do something else. And — what's the most dangerous unhandled case if logging is added unconditionally to the pure function — a cache hit that now triggers a file write inside a lock-held critical section?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=25.1s; answer_chars=1817; files_added=[]; files_modified=[]; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
There's a hard conflict here. The docstring on `compute_checksum` (lines 6–9) explicitly prohibits side effects — it documents that callers memoize the function and call it inside hot retry loops, and that **any I/O or logging there would break those callers**.

Adding logging directly into the function body would violate that contract and could:
- Break memoization (cache keys would be invalidated by side-effectful calls in some memoization schemes)
- Add I/O overhead on a hot path, degrading latency under retry pressure
- Corrupt callers that rely on pure-function guarantees (e.g., for testing or concurrency)

**The safe alternative** is a thin logging wrapper that keeps the pure function untouched:

```python
# wherever you need the logged variant
import logging
from core import compute_checksum as _compute_checksum

logger = logging.getLogger(__name__)

def compute_checksum(data: bytes) -> str:
    logger.debug("compute_checksum called", extra={"data_len": len(data)})
    result = _compute_checksum(data)
    logger.debug("compute_checksum returned", extra={"digest": result})
    return result
```

This way:
- `core.compute_checksum` stays pure — memoization and hot-path callers are unaffected
- Only the callers that import the wrapper get logging
- You can gate the wrapper behind a feature flag or inject it at a specific call site

**What do you want to do?**

1. Add the wrapper at the call site(s) that need observability
2. Override the docstring's constraint (if you've confirmed the memoization concern no longer applies) and add logging inline

The dangerous unhandled case: are there callers that hold a direct reference to `compute_checksum` (e.g., passed as a callback or stored in a dict)? A wrapper swap at import time won't catch those — they'd still call the un-logged original.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=3; wall=23.1s; answer_chars=1023; files_added=[]; files_modified=[]; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
There's a direct conflict I need to surface before making any change.

The docstring on `compute_checksum` (lines 6–10) is an explicit contract: **no side effects** — the function is memoized by callers and sits on a hot retry path. Adding logging directly would:
- Break memoization (the same input would trigger a log call on every *logical* invocation even if the result was cached)
- Add I/O latency on the hot path

Two ways to honor both requirements:

1. **Logging wrapper** — add a `logged_compute_checksum(data)` that logs then delegates to the pure function. Callers that need observability use the wrapper; memoized/hot-path callers keep calling the pure function directly.

2. **Caller-side logging** — add the log statement at each call site instead of inside the function.

Option 1 is cleanest if there are many call sites or you want a single logging point. Option 2 is safer if only one or two callers need it.

Which approach do you want, or did you intend to remove the pure-function constraint entirely?
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=37.5s; answer_chars=412; files_added=[]; files_modified=['core.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
`core.py` now has a `compute_checksum_logged` wrapper at the bottom. Call sites that want observability use the wrapper; hot-path/memoized callers keep calling the pure function.

One sharp open question: do you need to log **every logical checksum request** (including memoized cache hits the callers never forward to `compute_checksum`)? If yes, the logging has to move into the callers' cache layer, not here.
````
