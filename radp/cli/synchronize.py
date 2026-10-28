import argparse
import asyncio
import logging

from radp.bootstrap.runtime import get_container

logger = logging.getLogger(__name__)


def synchronize(args: argparse.Namespace) -> None:
    container = get_container(certificate_folder=args.certificate_folder)
    count = asyncio.run(container.synchronization.run())
    logger.info("Synchronization completed. affected=%s", count)
