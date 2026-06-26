import time
import urllib.error
import urllib.request

_MAX_ATTEMPTS = 3
_BASE_DELAY = 1.0  # seconds; doubles each retry


def fetch_url(url):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to _MAX_ATTEMPTS times with exponential backoff on transient
    failures (network errors, timeouts, HTTP 5xx).  HTTP 4xx errors are not
    retried — they are caller errors and repeating them is pointless.
    """
    delay = _BASE_DELAY
    last_exc: Exception | None = None

    for attempt in range(_MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as exc:
            last_exc = exc
            if exc.code < 500:
                raise  # 4xx: not transient, do not retry
        except urllib.error.URLError as exc:
            last_exc = exc  # network failure or timeout

        if attempt < _MAX_ATTEMPTS - 1:
            time.sleep(delay)
            delay *= 2

    raise last_exc
