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
    """Call compute_checksum and log every invocation.

    Use this instead of compute_checksum when call-site observability is needed.
    Do NOT use inside memoized paths or hot retry loops — the logging overhead
    and side-effect apply on every call here.
    """
    result = compute_checksum(data)
    logger.debug(
        "compute_checksum called",
        extra={"input_length": len(data), "digest": result},
    )
    return result
