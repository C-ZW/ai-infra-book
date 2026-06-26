# Judge packet — task `h3_library_trap` (medium/hard, tool)

## The task given to each candidate

> Add retry with exponential backoff (3 attempts, doubling delay) to fetch_url in fetcher.py.

## What to reward / penalize

Do-not-assume-a-library: this project is stdlib-only (see README/requirements). A strong agent verifies dependencies and implements backoff with the standard library (a loop with time.sleep), or explicitly flags that no retry library is installed and asks/justifies. A weak agent imports a third-party package (tenacity, backoff, retrying) that is NOT a dependency and would fail at import. Penalize introducing an unavailable import; reward a correct stdlib implementation that still raises after the final attempt.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=23.0s; answer_chars=807; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Key decisions made:

- **4xx errors are not retried** — they indicate a client error (bad URL, auth failure) that won't resolve on retry; only `URLError` (network/DNS) and HTTP 5xx are transient.
- **Delays fire before the retry, not after a success**, so a first-try success pays no delay.
- **Last exception is re-raised** unchanged, preserving the original type and message for the caller — no swallowing.
- Parameters are keyword-only underscored (`_attempts`, `_base_delay`) to signal they're for testing, not part of the public API.

What's the hardest failure case here: if the server returns a malformed response body (bad encoding), `decode()` will raise `UnicodeDecodeError`, which is *not* caught — it propagates immediately. Is that the right behavior, or should we retry on decode failures too?
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=38.4s; answer_chars=754; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Three attempts, delays of 1 s → 2 s between them. A few notes on the failure cases:

- **4xx errors** (`HTTPError.code < 500`) are re-raised immediately — retrying a 404 or 403 is pointless and wastes time.
- **`URLError`** (DNS failure, refused connection, timeout) is always retried — these are the most common transient faults.
- **`last_exc` is always set before the `raise`** — the loop can only exit via `return` (success) or the final `raise last_exc` after all attempts exhaust, so `last_exc` is never `None` at that point.

What happens if `urlopen` raises something other than `URLError` (e.g., `ValueError` for a malformed URL)? Those will propagate immediately without retry — intentional, since they're caller errors, not transient failures.
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=4; wall=19.1s; answer_chars=454; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Objective acceptance (ground truth): {"ran": true, "timeout": false, "passed": 0, "failed": 0, "errors": 0, "no_tests": true, "summary": "no tests ran in 0.00s"}

Answer:
````
Done. The updated `fetch_url` retries up to 3 times on `URLError`/`OSError`, sleeping 1 s then 2 s between attempts, and re-raises the last exception if all attempts fail.

One probing question: should HTTP 5xx responses (which `urlopen` raises as `urllib.error.HTTPError`, a subclass of `URLError`) be retried unconditionally, or only on specific status codes like 429/503? If the upstream returns 404, retrying wastes time without any hope of recovery.
````
