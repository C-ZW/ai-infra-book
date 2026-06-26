import time
import urllib.error
import urllib.request


def fetch_url(url, *, _attempts=3, _base_delay=1.0):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to _attempts times on transient errors, doubling the delay
    after each failure (1 s → 2 s → 4 s by default).
    """
    delay = _base_delay
    last_exc = None
    for attempt in range(_attempts):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except (urllib.error.URLError, OSError) as exc:
            last_exc = exc
            if attempt < _attempts - 1:
                time.sleep(delay)
                delay *= 2
    raise last_exc
