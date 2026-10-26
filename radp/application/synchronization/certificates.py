import logging

from radp.application.ports.certificate_repository import \
    CertificateRepositoryPort
from radp.domain.certificate.factory import CertificateFactory
from radp.infrastructure.ra_api.client import RAClient

logger = logging.getLogger(__name__)


class CertificateSynchronizer:
    def __init__(
        self,
        client: RAClient,
        certificates: CertificateRepositoryPort,
        factory: CertificateFactory,
    ) -> None:
        self.client = client
        self.certificates = certificates
        self.factory = factory

    async def synchronize(self) -> int:
        created = updated = unchanged = 0
        async for page in self.client.iter_certificate_summary_pages():
            summaries = page.items
            existing_by_id = self.certificates.get_lifecycles(
                [summary.id for summary in summaries]
            )
            for summary in summaries:
                existing = existing_by_id.get(summary.id)
                if existing is not None and existing.status == summary.status:
                    unchanged += 1
                    continue
                detail = await self.client.get_certificate(str(summary.id))
                current = self.factory.create(detail)
                if existing is None:
                    self.certificates.save(current)
                    created += 1
                    continue
                state = current.lifecycle
                if (
                    existing.status != state.status
                    or existing.revoked_when != state.revoked_when
                    or existing.revocation_reason != state.revocation_reason
                ):
                    self.certificates.update_lifecycle(
                        summary.id,
                        status=state.status,
                        revoked_when=state.revoked_when,
                        revocation_reason=state.revocation_reason,
                    )
                    updated += 1
                else:
                    unchanged += 1
        logger.info(
            "Synchronization finished. created=%d lifecycle_updated=%d unchanged=%d",
            created,
            updated,
            unchanged,
        )
        return created + updated
