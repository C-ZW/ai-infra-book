import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def process(orders):
    logger.info("starting order processing, count=%d", len(orders))
    total = 0
    for o in orders:
        logger.info("processing order value=%s", o)
        total += o
    logger.info("finished processing, total=%d", total)
    return total


if __name__ == "__main__":
    process([1, 2, 3])
