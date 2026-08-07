import logging

from radp.domain.snapshots.factory import CertificateSnapshotFactory
from radp.infrastructure.persistence.repositories.snapshot_repository import \
    SnapshotRepository
from radp.infrastructure.ra_api.client import RAClient

logger = logging.getLogger(__name__)


class CertificateSynchronizationService:
    def __init__(
        self,
        client: RAClient,
        snapshots: SnapshotRepository,
        factory: CertificateSnapshotFactory,
    ):
        self.client = client
        self.snapshots = snapshots
        self.factory = factory

    async def synchronize(self) -> int:
        synchronized = 0
        skipped = 0

        async for summary in self.client.iter_certificates():
            latest = self.snapshots.get_latest(summary.id)
            if latest:
                logger.debug("Certificate %s already exists", summary.id)
                skipped += 1
                continue
            logger.info("Fetching certificate %s", summary.id)
            detail_dto = await self.client.get_certificate(summary.id)
            snapshot = self.factory.create(detail_dto)
            self.snapshots.save(snapshot)
            synchronized += 1
        logger.info(
            "Synchronization finished. Created=%s skipped=%s",
            synchronized,
            skipped,
        )

        return synchronized
