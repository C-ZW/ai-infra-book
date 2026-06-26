import logging
import time

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)


def process(orders):
    log.info("process started: order_count=%d", len(orders))
    start = time.monotonic()
    total = 0
    for i, o in enumerate(orders):
        log.debug("processing order: index=%d value=%s", i, o)
        total += o
    elapsed = time.monotonic() - start
    log.info("process finished: total=%s elapsed_ms=%.1f", total, elapsed * 1000)
    return total


if __name__ == "__main__":
    process([1, 2, 3])
