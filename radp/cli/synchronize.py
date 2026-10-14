import argparse
import asyncio
import logging

from radp.bootstrap.runtime import get_runtime

logger = logging.getLogger(__name__)


def synchronize(_args: argparse.Namespace) -> None:
    count = asyncio.run(get_runtime().synchronization.run())
    logger.info("Synchronization completed. affected=%s", count)
