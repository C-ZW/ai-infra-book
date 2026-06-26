import time
import urllib.error
import urllib.request


class FetchError(Exception):
    """Raised when fetch_url exhausts all retry attempts."""

    def __init__(self, url: str, attempts: int, cause: Exception) -> None:
        super().__init__(
            f"fetch_url failed after {attempts} attempt(s) for {url!r}: {cause}"
        )
        self.url = url
        self.attempts = attempts
        self.cause = cause


def fetch_url(url: str, *, max_attempts: int = 3, base_delay: float = 1.0) -> str:
    """Fetch a URL and return the decoded body. Stdlib only.

    Retries up to *max_attempts* times with exponential backoff.
    Delays: base_delay, base_delay*2, … (no sleep after the last attempt).

    Args:
        url: The URL to fetch.
        max_attempts: Total number of tries (default 3).
        base_delay: Seconds before the first retry; doubles each round.

    Raises:
        FetchError: After all attempts are exhausted.
        ValueError: If max_attempts < 1.
    """
    if max_attempts < 1:
        raise ValueError(f"max_attempts must be >= 1, got {max_attempts}")

    last_exc: Exception | None = None
    delay = base_delay

    for attempt in range(1, max_attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode()
        except (urllib.error.URLError, OSError) as exc:
            last_exc = exc
            if attempt < max_attempts:
                time.sleep(delay)
                delay *= 2

    raise FetchError(url, max_attempts, last_exc)  # type: ignore[arg-type]
