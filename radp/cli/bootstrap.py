import argparse
import logging

from radp.bootstrap.initialize import initialize_runtime

logger = logging.getLogger(__name__)


def bootstrap(args: argparse.Namespace) -> None:
    initialize_runtime(reset=args.reset)
    logger.info("Initialization completed.")
