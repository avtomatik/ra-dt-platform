from typing import Protocol
from uuid import UUID

from .certificate_snapshot import CertificateSnapshot


class SnapshotRepository(Protocol):
    def get(self, certificate_id: UUID) -> CertificateSnapshot | None: ...
    def save(self, snapshot: CertificateSnapshot) -> None: ...
