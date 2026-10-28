import argparse
import logging

from radp.bootstrap.runtime import get_container

logger = logging.getLogger(__name__)


def bootstrap(args: argparse.Namespace) -> None:
    runtime = get_container()
    if args.reset:
        runtime.database.reset()
    else:
        runtime.database.create()
    changed = runtime.bootstrap.initialize()
    logger.info(
        "Bootstrap completed. OID definitions inserted or enriched=%d", changed
    )
