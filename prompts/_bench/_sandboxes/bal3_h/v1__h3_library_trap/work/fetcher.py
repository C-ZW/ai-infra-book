import time
import urllib.error
import urllib.request


def fetch_url(url, *, retries=3, base_delay=1.0):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to `retries` times on transient errors (URLError, HTTP 5xx)
    with exponential backoff starting at `base_delay` seconds (doubling each
    attempt: 1s, 2s, 4s, …). Raises the last exception if all attempts fail.
    """
    last_exc = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                raise  # 4xx errors are not retryable
            last_exc = exc
        except urllib.error.URLError as exc:
            last_exc = exc

        if attempt < retries - 1:
            time.sleep(base_delay * (2 ** attempt))

    raise last_exc
