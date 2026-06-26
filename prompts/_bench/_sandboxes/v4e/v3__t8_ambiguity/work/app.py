import logging
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s [%(correlation_id)s] %(message)s",
)

log = logging.getLogger(__name__)


class _CorrelationFilter(logging.Filter):
    def __init__(self, correlation_id: str) -> None:
        super().__init__()
        self.correlation_id = correlation_id

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = self.correlation_id
        return True


def process(orders, correlation_id: str | None = None) -> int:
    cid = correlation_id or str(uuid.uuid4())[:8]
    _filter = _CorrelationFilter(cid)
    log.addFilter(_filter)

    if not isinstance(orders, (list, tuple)):
        log.error("invalid input: expected list or tuple, got %s", type(orders).__name__)
        log.removeFilter(_filter)
        raise TypeError(f"orders must be a list or tuple, got {type(orders).__name__}")

    log.info("starting process: order_count=%d", len(orders))

    total = 0
    for i, o in enumerate(orders):
        if not isinstance(o, (int, float)):
            log.warning("skipping non-numeric order: index=%d value=%r", i, o)
            continue
        log.debug("processing order: index=%d value=%s", i, o)
        total += o

    log.info("process complete: total=%s", total)
    log.removeFilter(_filter)
    return total


if __name__ == "__main__":
    process([1, 2, 3])
