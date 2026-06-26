import time
import urllib.error
import urllib.request


def fetch_url(url, *, _attempts=3, _base_delay=1.0):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to ``_attempts`` times (default 3) on transient network or
    HTTP 5xx errors, with exponential backoff starting at ``_base_delay``
    seconds (1 s → 2 s → give up).  Raises the last exception on exhaustion.
    """
    delay = _base_delay
    last_exc = None
    for attempt in range(1, _attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as exc:
            # Retry only on server-side transient errors; 4xx are caller bugs.
            if exc.code < 500:
                raise
            last_exc = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc

        if attempt < _attempts:
            time.sleep(delay)
            delay *= 2

    raise last_exc
