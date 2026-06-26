import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def process(orders):
    logger.info("process started order_count=%d", len(orders))
    total = 0
    for o in orders:
        logger.debug("processing order=%s running_total=%s", o, total)
        total += o
    logger.info("process finished total=%s", total)
    return total


if __name__ == "__main__":
    process([1, 2, 3])
