import hashlib


def compute_checksum(data: bytes) -> str:
    """Return the SHA-256 hex digest of data.

    PURE FUNCTION — must stay free of side effects. It is memoized by callers and
    invoked inside hot retry loops; any I/O or logging here would break those
    callers and add overhead on the hot path. Do not add side effects.
    """
    return hashlib.sha256(data).hexdigest()
