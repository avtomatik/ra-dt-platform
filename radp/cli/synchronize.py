import asyncio
import logging

from radp.bootstrap.runtime import get_runtime

logger = logging.getLogger(__name__)


def synchronize(_args):
    async def run():
        runtime = get_runtime()
        count = await runtime.synchronization.synchronize()
        logger.info(f"Appended {count} certificates.")

    asyncio.run(run())
