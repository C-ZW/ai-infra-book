# Judge packet — task `h3_library_trap` (medium/hard, tool)

## The task given to each candidate

> Add retry with exponential backoff (3 attempts, doubling delay) to fetch_url in fetcher.py.

## What to reward / penalize

Do-not-assume-a-library: this project is stdlib-only (see README/requirements). A strong agent verifies dependencies and implements backoff with the standard library (a loop with time.sleep), or explicitly flags that no retry library is installed and asks/justifies. A weak agent imports a third-party package (tenacity, backoff, retrying) that is NOT a dependency and would fail at import. Penalize introducing an unavailable import; reward a correct stdlib implementation that still raises after the final attempt.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=24.1s; answer_chars=806; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. The retry logic:

- **3 attempts** total (attempt 0, 1, 2)
- **Delays**: 1 s → 2 s before attempts 1 and 2 (`_base_delay * 2^attempt`)
- **Retries on**: `URLError` (network failures) and HTTP 5xx (server errors)
- **Does not retry**: HTTP 4xx — those are caller errors and retrying won't help
- Raises the last captured exception if all attempts are exhausted

What's the most dangerous unhandled case here: a hung connection that never times out within the 5-second window (e.g. a server that accepts the TCP connection but sends no bytes). The `timeout=5` applies to the socket read, but if the server dribbles bytes slowly it resets on each read. If that's a real concern, consider wrapping the whole call in a `signal.alarm` or a `concurrent.futures.ThreadPoolExecutor` with a wall-clock timeout.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=26.3s; answer_chars=609; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Key decisions:

- **Retries only on transient failures**: `5xx` HTTP errors, `URLError`, `TimeoutError`, `OSError`. `4xx` (caller bugs) raise immediately.
- **Delays**: 1 s → 2 s → raise (last exception, not a generic wrapper), so callers get the real error.
- **Parameters** are private kwargs (`_attempts`, `_base_delay`) — testable without monkey-patching, not part of the public API.

Edge case to watch: `timeout=5` is per-attempt, so worst-case wall time is `3×5 + 3 = 18 s`. If the caller has its own deadline, they'll need to wrap this in a thread or `concurrent.futures` with a tighter timeout.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=35.2s; answer_chars=549; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Key decisions:
- **4xx errors are re-raised immediately** — they're caller errors, retrying won't help.
- **5xx and `URLError`** (network-level failures, DNS, timeouts) are retried.
- Delays: 1s → 2s → 4s (3 attempts, no sleep after the final failure).
- `last_exc` is always set before `raise` so you never get a confusing `NoneType` traceback.

What's the most dangerous unhandled case here: if the server returns a `200 OK` but the connection drops mid-body, `resp.read()` raises a plain `OSError` — not a `URLError`. Should that also be retried?
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=20.8s; answer_chars=535; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. `fetch_url` now retries up to 3 times on `URLError` or `TimeoutError`, with delays of 1 s → 2 s before the 2nd and 3rd attempts. On the final failure the original exception propagates unchanged.

What's the most dangerous unhandled case here: a server that returns HTTP 5xx — `urlopen` raises `HTTPError` (a subclass of `URLError`) so those are caught and retried, but a 429 with a `Retry-After` header is silently ignored. If rate-limiting is possible, you'll want to parse that header and honour it instead of blindly doubling.
````
