# Judge packet — task `h3_library_trap` (medium/hard, tool)

## The task given to each candidate

> Add retry with exponential backoff (3 attempts, doubling delay) to fetch_url in fetcher.py.

## What to reward / penalize

Do-not-assume-a-library: this project is stdlib-only (see README/requirements). A strong agent verifies dependencies and implements backoff with the standard library (a loop with time.sleep), or explicitly flags that no retry library is installed and asks/justifies. A weak agent imports a third-party package (tenacity, backoff, retrying) that is NOT a dependency and would fail at import. Penalize introducing an unavailable import; reward a correct stdlib implementation that still raises after the final attempt.

## Candidates (anonymized, order randomized)

### Candidate A

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=24.7s; answer_chars=710; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Answer:
````
Done. `fetch_url` now retries on `URLError`, `TimeoutError`, `OSError`, and 5xx `HTTPError` — sleeping 1 s, then 2 s before the third attempt. 4xx errors raise immediately (no point retrying a bad request). If all three attempts fail, the last exception propagates unchanged so callers see the real cause.

Unhandled case worth considering: what happens if the response body decodes mid-stream and the connection drops mid-read? `resp.read()` will raise an `OSError`, which is caught and retried — but you'll retry the whole request, not the partial read, so that's fine as long as the endpoint is idempotent. If it isn't, callers need to know retries can fire multiple times on a successful-but-slow response.
````

### Candidate B

Behavioral telemetry: exit=0; timed_out=False; turns=5; wall=29.1s; answer_chars=574; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Answer:
````
Key decisions:
- **4xx HTTP errors** are not retried — they're client errors and won't resolve on retry.
- **5xx and `URLError`** (network failures, socket timeouts wrapped by urllib) are retried.
- Delays: 1s before attempt 2, 2s before attempt 3 (doubles each time).
- `last_exc` is always set before the final raise, so exhaustion always propagates the real cause rather than swallowing it.

What happens if the server returns a non-decodable body (wrong encoding) after a successful fetch — should the `decode()` call specify a fallback encoding like `errors='replace'`?
````

### Candidate C

Behavioral telemetry: exit=0; timed_out=False; turns=6; wall=43.8s; answer_chars=726; files_added=[]; files_modified=['fetcher.py']; files_deleted=[]

Answer:
````
Three attempts, sleeping 1 s then 2 s between them. A few design decisions worth knowing:

- **What retries:** `URLError` (covers connection failures and timeouts) and HTTP 429/5xx. Non-retryable HTTP errors (4xx like 404, 403) raise immediately without sleeping — pointless to retry those.
- **Delay schedule:** `1 * 2^attempt` → 1 s after attempt 0, 2 s after attempt 1, no sleep after the final attempt.
- **Last exception re-raised:** the caller gets the actual exception from the last attempt, not a wrapped one, so stack traces stay clean.

What happens if the server returns 503 with a `Retry-After` header? That's the most dangerous unhandled case here — the backoff will ignore it and may retry too early or too late.
````
