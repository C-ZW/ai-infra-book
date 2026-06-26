import logging
import uuid

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s trace_id=%(trace_id)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)


def process(orders, trace_id=None):
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    log = logging.LoggerAdapter(logging.getLogger(__name__), {"trace_id": trace_id})

    if not isinstance(orders, (list, tuple)):
        raise TypeError(f"orders must be a list or tuple, got {type(orders).__name__}")

    log.info("process started order_count=%d", len(orders))
    total = 0
    for i, o in enumerate(orders):
        if not isinstance(o, (int, float)):
            log.warning("skipping non-numeric order index=%d value=%r", i, o)
            continue
        log.debug("processing index=%d value=%s", i, o)
        total += o

    log.info("process finished total=%s", total)
    return total


if __name__ == "__main__":
    process([1, 2, 3])
