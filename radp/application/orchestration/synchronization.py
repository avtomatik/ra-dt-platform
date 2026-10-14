import logging

from radp.application.synchronization.certificates import \
    CertificateSynchronizer

logger = logging.getLogger(__name__)


class SynchronizationOrchestrator:
    def __init__(self, synchronization: CertificateSynchronizer) -> None:
        self._synchronization = synchronization

    async def run(self) -> int:
        logger.info("Starting certificate synchronization")
        count = await self._synchronization.synchronize()
        logger.info("Synchronization completed. affected=%s", count)
        return count
