import logging
from uuid import UUID

from radp.application.ports.certificate_repository import \
    CertificateRepositoryPort
from radp.domain.certificate.factory import CertificateFactory
from radp.infrastructure.ra_api.client import RAClient

logger = logging.getLogger(__name__)


class FolderSynchronizationError(RuntimeError):
    """Raised after all folders have been attempted when one or more failed."""

    def __init__(self, failed_folders: dict[str, Exception]) -> None:
        self.failed_folders = failed_folders
        names = ", ".join(sorted(failed_folders))
        super().__init__(f"Synchronization failed for RA folder(s): {names}")


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
        failed_folders: dict[str, Exception] = {}
        processed_ids: set[UUID] = set()
        for folder in self.client.certificate_folders:
            folder_created = folder_updated = folder_unchanged = 0
            logger.info(
                "Starting certificate synchronization for folder=%s", folder
            )
            try:
                async for page in self.client.iter_certificate_summary_pages(
                    folder
                ):
                    # Deduplicate across pages and folders. The RA may expose the
                    # same certificate through more than one folder. Mark each ID
                    # only after it has been handled successfully, so a failed
                    # detail request can be retried if another folder also lists it.
                    summaries = [
                        summary
                        for summary in page.items
                        if summary.id not in processed_ids
                    ]
                    if not summaries:
                        continue
                    existing_by_id = self.certificates.get_lifecycles(
                        [summary.id for summary in summaries]
                    )
                    for summary in summaries:
                        if summary.id in processed_ids:
                            continue
                        existing = existing_by_id.get(summary.id)
                        if (
                            existing is not None
                            and existing.status == summary.status
                        ):
                            folder_unchanged += 1
                            processed_ids.add(summary.id)
                            continue
                        detail = await self.client.get_certificate(
                            str(summary.id)
                        )
                        current = self.factory.create(detail)
                        if existing is None:
                            self.certificates.save(current)
                            folder_created += 1
                            processed_ids.add(summary.id)
                            continue
                        state = current.lifecycle
                        if (
                            existing.status != state.status
                            or existing.revoked_when != state.revoked_when
                            or existing.revocation_reason
                            != state.revocation_reason
                        ):
                            self.certificates.update_lifecycle(
                                summary.id,
                                status=state.status,
                                revoked_when=state.revoked_when,
                                revocation_reason=state.revocation_reason,
                            )
                            folder_updated += 1
                        else:
                            folder_unchanged += 1
                        processed_ids.add(summary.id)
            except Exception as exc:
                failed_folders[folder] = exc
                logger.exception(
                    "Certificate synchronization failed for folder=%s; "
                    "continuing with remaining folders",
                    folder,
                )
            finally:
                created += folder_created
                updated += folder_updated
                unchanged += folder_unchanged
                logger.info(
                    "Folder synchronization finished. folder=%s created=%d "
                    "lifecycle_updated=%d unchanged=%d",
                    folder,
                    folder_created,
                    folder_updated,
                    folder_unchanged,
                )
        logger.info(
            "Synchronization finished. folders=%d failed_folders=%d "
            "created=%d lifecycle_updated=%d unchanged=%d",
            len(self.client.certificate_folders),
            len(failed_folders),
            created,
            updated,
            unchanged,
        )
        if failed_folders:
            raise FolderSynchronizationError(failed_folders)
        return created + updated
