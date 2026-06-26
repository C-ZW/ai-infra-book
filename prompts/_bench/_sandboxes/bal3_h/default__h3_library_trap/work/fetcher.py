import time
import urllib.error
import urllib.request


def fetch_url(url, *, _attempts=3, _base_delay=1.0):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to _attempts times with exponential backoff on transient errors.
    """
    delay = _base_delay
    for attempt in range(1, _attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == _attempts:
                raise
            time.sleep(delay)
            delay *= 2
