import time
import urllib.error
import urllib.request


def fetch_url(url, *, attempts=3, base_delay=1.0):
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to *attempts* times on transient network errors, with
    exponential backoff starting at *base_delay* seconds (doubles each try).
    Raises the last exception if all attempts fail.
    """
    last_exc = None
    delay = base_delay
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except (urllib.error.URLError, OSError) as exc:
            last_exc = exc
            if attempt < attempts:
                time.sleep(delay)
                delay *= 2
    raise last_exc
