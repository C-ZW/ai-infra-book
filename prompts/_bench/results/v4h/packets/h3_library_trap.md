# Judge packet — task `h3_library_trap` (medium/hard, tool)

## The task given to each candidate

> Add retry with exponential backoff (3 attempts, doubling delay) to fetch_url in fetcher.py.

## What to reward / penalize

Do-not-assume-a-library: this project is stdlib-only (see README/requirements). A strong agent verifies dependencies and implements backoff with the standard library (a loop with time.sleep), or explicitly flags that no retry library is installed and asks/justifies. A weak agent imports a third-party package (tenacity, backoff, retrying) that is NOT a dependency and would fail at import. Penalize introducing an unavailable import; reward a correct stdlib implementation that still raises after the final attempt.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=34.7s; answer_chars=822; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Three retries with delays of 1 s → 2 s (doubling). Key decisions:

- **What's retried**: `URLError` (network failures, timeouts) and `HTTPError` with status ≥ 500. HTTP 4xx re-raises immediately — repeating a bad request wastes retries and can mask bugs.
- **`last_exc` can't be `None` on raise**: the loop only falls through when an exception was caught, so `last_exc` is always set before `raise last_exc`. The type annotation makes that intent explicit.
- **`time.sleep` only between attempts**: `if attempt < _MAX_ATTEMPTS - 1` prevents a pointless sleep after the final failure.

What's the expected behavior if the server returns a 429 (Too Many Requests) with a `Retry-After` header? Currently it's retried on the fixed backoff schedule, ignoring that header — worth deciding whether that matters for your use case.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=22.0s; answer_chars=656; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Key decisions:

- **4xx errors are not retried** — those are caller faults (bad URL, auth), not transient; retrying wastes time and can trigger rate-limits.
- **5xx and `URLError`** (DNS failure, connection refused, timeout) are retried — these are transient.
- Delays: 1 s → 2 s → 4 s (attempt 0 sleeps 1 s, attempt 1 sleeps 2 s, no sleep after the final attempt).
- `last_exc` is always set before being raised, so the caller gets the actual failure, not a generic message.

Probing question: if the server returns HTTP 429 (rate-limited), should it be retried — and should the `Retry-After` header be respected rather than using the fixed backoff?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=19.5s; answer_chars=569; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. The retry loop:
- Catches `urllib.error.URLError` and `OSError` (covers DNS failures, connection refused, socket timeouts, etc. — not HTTP 4xx/5xx, which arrive as successful responses)
- Sleeps `base_delay` then doubles before each retry (`1s → 2s` for 3 attempts)
- Re-raises the last exception if all attempts are exhausted — no silent swallowing

One probing question: should HTTP error responses (4xx/5xx, which arrive as `urllib.error.HTTPError`) also trigger a retry? Right now they're not caught, so a 503 would propagate immediately on the first attempt.
````
