import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def process(orders):
    logger.info("starting order processing", extra={"order_count": len(orders)})
    total = 0
    for o in orders:
        logger.debug("processing order", extra={"order": o})
        total += o
    logger.info("finished order processing", extra={"total": total})
    return total


if __name__ == "__main__":
    process([1, 2, 3])
