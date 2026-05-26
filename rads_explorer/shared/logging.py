import logging
import sys

DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level, format=DEFAULT_FORMAT, stream=sys.stdout, force=True
    )
