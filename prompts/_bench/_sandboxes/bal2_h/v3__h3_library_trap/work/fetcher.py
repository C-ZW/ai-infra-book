import time
import urllib.error
import urllib.request


def fetch_url(url, *, _attempts=3, _base_delay=1.0):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to _attempts times on transient errors (URLError, HTTP 5xx),
    doubling the delay after each failure: 1 s, 2 s, then raises.
    """
    last_exc = None
    delay = _base_delay
    for attempt in range(1, _attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as exc:
            if exc.code < 500:
                raise  # 4xx are not transient — fail immediately
            last_exc = exc
        except urllib.error.URLError as exc:
            last_exc = exc

        if attempt < _attempts:
            time.sleep(delay)
            delay *= 2

    raise last_exc
