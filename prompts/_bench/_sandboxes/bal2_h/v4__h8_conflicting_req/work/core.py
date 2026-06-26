import hashlib
import logging

logger = logging.getLogger(__name__)


def compute_checksum(data: bytes) -> str:
    """Return the SHA-256 hex digest of data.

    PURE FUNCTION — must stay free of side effects. It is memoized by callers and
    invoked inside hot retry loops; any I/O or logging here would break those
    callers and add overhead on the hot path. Do not add side effects.
    """
    return hashlib.sha256(data).hexdigest()


def logged_compute_checksum(data: bytes) -> str:
    """Call compute_checksum and log every invocation.

    Use this instead of compute_checksum when observability matters and the
    caller is NOT on a memoized or hot-retry path. The pure compute_checksum
    stays untouched so memoization and hot-path callers are unaffected.
    """
    result = compute_checksum(data)
    logger.debug(
        "compute_checksum called",
        extra={"data_len": len(data), "checksum": result},
    )
    return result
