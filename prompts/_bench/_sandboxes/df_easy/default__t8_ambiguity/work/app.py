import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def process(orders):
    logger.info("starting: %d orders", len(orders))
    total = 0
    for o in orders:
        logger.debug("processing order %s", o)
        total += o
    logger.info("done: total=%s", total)
    return total


if __name__ == "__main__":
    process([1, 2, 3])
