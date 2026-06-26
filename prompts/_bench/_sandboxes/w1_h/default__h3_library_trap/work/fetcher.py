import time
import urllib.error
import urllib.request


def fetch_url(url, _attempts=3, _base_delay=1):
    """Fetch a URL and return the decoded body. Stdlib only."""
    delay = _base_delay
    for attempt in range(_attempts):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except (urllib.error.URLError, OSError):
            if attempt == _attempts - 1:
                raise
            time.sleep(delay)
            delay *= 2
