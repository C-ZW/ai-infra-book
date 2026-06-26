import time
import urllib.error
import urllib.request

_MAX_ATTEMPTS = 3
_BASE_DELAY = 1.0  # seconds; doubles each retry: 1s, 2s


def fetch_url(url):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to 3 attempts with exponential backoff (1 s, 2 s) on
    network-level and transient HTTP errors (5xx).  Raises the last
    exception if all attempts fail.
    """
    last_exc = None
    for attempt in range(_MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as exc:
            # Retry only on server-side transient errors.
            if exc.code < 500:
                raise
            last_exc = exc
        except urllib.error.URLError as exc:
            last_exc = exc

        if attempt < _MAX_ATTEMPTS - 1:
            time.sleep(_BASE_DELAY * (2 ** attempt))

    raise last_exc
