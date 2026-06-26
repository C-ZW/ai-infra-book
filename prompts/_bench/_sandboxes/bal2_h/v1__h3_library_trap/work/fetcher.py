import time
import urllib.error
import urllib.request


def fetch_url(url, *, attempts=3, base_delay=1.0):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to *attempts* times on transient errors (URLError, HTTP 5xx),
    doubling the delay after each failure (1 s → 2 s → …).

    Raises the last exception if all attempts are exhausted.
    """
    last_exc = None
    delay = base_delay

    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as exc:
            # Only retry on server-side errors; client errors (4xx) are final.
            if exc.code < 500:
                raise
            last_exc = exc
        except urllib.error.URLError as exc:
            last_exc = exc

        if attempt < attempts:
            time.sleep(delay)
            delay *= 2

    raise last_exc
