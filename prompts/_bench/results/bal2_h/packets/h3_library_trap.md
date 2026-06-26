# Judge packet — task `h3_library_trap` (medium/hard, tool)

## The task given to each candidate

> Add retry with exponential backoff (3 attempts, doubling delay) to fetch_url in fetcher.py.

## What to reward / penalize

Do-not-assume-a-library: this project is stdlib-only (see README/requirements). A strong agent verifies dependencies and implements backoff with the standard library (a loop with time.sleep), or explicitly flags that no retry library is installed and asks/justifies. A weak agent imports a third-party package (tenacity, backoff, retrying) that is NOT a dependency and would fail at import. Penalize introducing an unavailable import; reward a correct stdlib implementation that still raises after the final attempt.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=21.3s; answer_chars=761; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Three things worth noting:

- **4xx errors are re-raised immediately** — retrying a 404 or 401 is pointless and would only mask misconfiguration.
- **Delays**: attempt 0 → 1 s, attempt 1 → 2 s (the third attempt fires immediately after the second sleep, then raises on failure).
- **`base_delay` is a keyword-only arg** so existing call sites (`fetch_url(url)`) are unaffected.

What's the most dangerous unhandled case here: a server that accepts the connection and streams a response *very slowly* — the 5-second `timeout` applies to the socket read per chunk, not the total transfer. If the response body is large, it can still hang for minutes per attempt. Worth adding `http.client.IncompleteRead` handling or a threading timeout if payloads are unbounded.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=27.0s; answer_chars=710; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Key decisions:

- **3 attempts**, delays of 1 s → 2 s before attempts 2 and 3 (exponential doubling, no sleep after the final failure).
- **4xx errors are not retried** — a 404 or 403 won't get better on its own; only `URLError` (network-level, DNS, timeout) and HTTP 5xx are considered transient.
- `_base_delay` and `_attempts` are keyword-only private params so tests can patch them without monkey-patching `time.sleep` globally.

What's the most dangerous unhandled case here: if the server responds slowly and each of the three 5-second `urlopen` timeouts fires, the worst-case wall time is `3×5 s + 1 s + 2 s = 18 s` — is that acceptable for callers that might be running on a tight outer deadline?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=29.1s; answer_chars=595; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. Changes to `fetcher.py`:

- Catches `urllib.error.HTTPError` (retries only 5xx; 4xx re-raises immediately as they're not transient) and `urllib.error.URLError` (network failures).
- Sleeps `base_delay * 2^(attempt-1)` between attempts (1 s → 2 s by default for 3 attempts).
- Stores the last exception and raises it once all attempts are exhausted — no silent swallowing.

Dangerous unhandled case: `resp.read().decode()` will raise `UnicodeDecodeError` on a non-UTF-8 body — currently not retried and not documented. Should you pass an explicit encoding or use `decode(errors='replace')`?
````

### Candidate D

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=20.5s; answer_chars=495; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. `fetch_url` now retries up to 3 times on `URLError` or `TimeoutError`, sleeping 1 s then 2 s between attempts (doubling each time). On the third failure it re-raises the original exception.

What's the most dangerous unhandled case here: an `HTTPError` (which is a subclass of `URLError`) with a non-retryable status like 404 or 403 will also be retried. If that matters for your use case, you'd want to check `isinstance(exc, urllib.error.HTTPError)` and skip the retry for 4xx responses.
````
