from datetime import datetime
from typing import Protocol
from uuid import UUID

from radp.domain.models.certificate import Certificate


class CertificateRepositoryPort(Protocol):
    def exists(self, certificate_id: UUID) -> bool: ...
    def get(self, certificate_id: UUID) -> Certificate | None: ...
    def save(self, certificate: Certificate) -> None: ...
    def update_lifecycle(
        self,
        certificate_id: UUID,
        *,
        status: str,
        revoked_when: datetime | None,
        revocation_reason: str | None,
    ) -> None: ...
