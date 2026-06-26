import hashlib
import logging

logger = logging.getLogger(__name__)


def compute_checksum(data: bytes) -> str:
    """Return the SHA-256 hex digest of data."""
    digest = hashlib.sha256(data).hexdigest()
    logger.debug("compute_checksum called: input_bytes=%d digest=%s", len(data), digest)
    return digest
