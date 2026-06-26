import time
import urllib.error
import urllib.request


def fetch_url(url, *, _attempts=3, _base_delay=1.0):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to _attempts times on transient errors (URLError, HTTP 5xx)
    with exponential backoff: 1 s, 2 s, 4 s, … before each retry.
    Raises the last exception if all attempts fail.
    """
    last_exc = None
    for attempt in range(_attempts):
        if attempt:
            time.sleep(_base_delay * (2 ** (attempt - 1)))
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                raise  # 4xx — not retryable
            last_exc = exc
        except urllib.error.URLError as exc:
            last_exc = exc
    raise last_exc
