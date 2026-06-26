import logging

logger = logging.getLogger(__name__)


def process(orders):
    logger.info("starting process", extra={"order_count": len(orders)})
    total = 0
    for i, o in enumerate(orders):
        if not isinstance(o, (int, float)):
            logger.error(
                "skipping invalid order value",
                extra={"index": i, "value": repr(o), "type": type(o).__name__},
            )
            continue
        logger.debug("processing order", extra={"index": i, "value": o})
        total += o
    logger.info("process complete", extra={"order_count": len(orders), "total": total})
    return total


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s %(levelname)s %(name)s %(message)s %(extra)s"
        if False
        else "%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )
    process([1, 2, 3])
