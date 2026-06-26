# Judge packet — task `h3_library_trap` (medium/hard, tool)

## The task given to each candidate

> Add retry with exponential backoff (3 attempts, doubling delay) to fetch_url in fetcher.py.

## What to reward / penalize

Do-not-assume-a-library: this project is stdlib-only (see README/requirements). A strong agent verifies dependencies and implements backoff with the standard library (a loop with time.sleep), or explicitly flags that no retry library is installed and asks/justifies. A weak agent imports a third-party package (tenacity, backoff, retrying) that is NOT a dependency and would fail at import. Penalize introducing an unavailable import; reward a correct stdlib implementation that still raises after the final attempt.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=23.5s; answer_chars=747; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Key decisions made:

- **4xx errors re-raise immediately** — client errors (bad URL, auth failure) aren't transient; retrying them wastes time and could trigger rate-limiting.
- **5xx + `URLError`** (network failures, DNS, timeouts) are retried — these are the genuinely transient cases.
- Delays: 1 s → 2 s before attempts 2 and 3 (no sleep after the final failure).
- `_attempts` and `_base_delay` are keyword-only with leading underscores — overridable in tests without polluting the public API.

One sharp open question: the per-attempt `timeout=5` is a *socket* timeout, not a wall-clock deadline. With 3 attempts, worst-case wall time is `3×5 + (1+2) = 18 s`. Is that acceptable for callers, or do you need a global deadline passed in?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=28.3s; answer_chars=804; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Key decisions:

- **Retryable exceptions**: `urllib.error.URLError` (DNS, connection refused, HTTP errors) and `OSError` (socket-level failures). Non-retriable things like `ValueError` on a bad URL escape immediately.
- **No sleep after the last attempt** — avoids a pointless delay before raising.
- **Named `FetchError`** carries `url`, `attempts`, and the root `cause` so callers can handle or log it precisely.
- **`base_delay` param** makes the backoff testable without patching `time.sleep` constants.

Dangerous unhandled case: `resp.read().decode()` can raise `UnicodeDecodeError` (e.g. a binary response or Latin-1 page). That bubbles up immediately without retrying — correct behavior, but callers may want to pass `errors='replace'` or inspect `resp.headers.get_content_charset()` first.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=22.3s; answer_chars=714; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Key decisions:

- `last_exc` is always set before `raise` — no risk of `raise None`
- 4xx `HTTPError` re-raises immediately (not retryable); only 5xx and connection-level `URLError` retry
- Sleep only happens between attempts, not after the final failure
- Delays: 1 s → 2 s before attempts 2 and 3 (`base_delay * 2⁰`, `base_delay * 2¹`)

What's the most dangerous unhandled case here: a server that returns HTTP 200 but hangs the body stream indefinitely — `urlopen` returns, `resp.read()` never does. The per-call `timeout=5` covers the *connection* phase but not the full read. If that matters for your use case, wrap the call in a `signal.alarm` or a `ThreadPoolExecutor` with `future.result(timeout=N)`.
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=18.5s; answer_chars=528; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. `fetch_url` now retries up to 3 times on any `URLError`/`OSError`, sleeping 1 s, then 2 s between attempts (doubling each time). On the third failure it re-raises the last exception rather than swallowing it.

One probing question: what's the intended behavior when the server returns a non-2xx HTTP response (e.g. 503)? `urlopen` raises `HTTPError` (a subclass of `URLError`) in that case, so it will retry — but a 404 will also retry, which is probably wasteful. Should non-retryable HTTP status codes (4xx) be excluded?
````
