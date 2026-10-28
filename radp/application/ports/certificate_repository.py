from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from radp.domain.models.certificate import (Certificate, CertificateLifecycle,
                                            CertificateStatus)


class CertificateRepositoryPort(Protocol):
    def exists(self, certificate_id: UUID) -> bool: ...
    def get(self, certificate_id: UUID) -> Certificate | None: ...
    def get_lifecycles(
        self, certificate_ids: Sequence[UUID]
    ) -> Mapping[UUID, CertificateLifecycle]: ...
    def save(self, certificate: Certificate) -> None: ...
    def update_lifecycle(
        self,
        certificate_id: UUID,
        *,
        status: CertificateStatus,
        revoked_when: datetime | None,
        revocation_reason: str | None,
    ) -> None: ...
