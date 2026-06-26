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


def compute_checksum_logged(data: bytes) -> str:
    """Wrapper around compute_checksum that logs each call.

    Use this at call sites where observability is needed. Do NOT replace
    memoized or hot-path callers — they should keep calling compute_checksum
    directly to preserve the pure-function contract.
    """
    logger.debug(
        "compute_checksum called",
        extra={"data_len": len(data)},
    )
    result = compute_checksum(data)
    logger.debug(
        "compute_checksum returned",
        extra={"data_len": len(data), "digest": result},
    )
    return result
