from typing import Protocol
from uuid import UUID

from .certificate_snapshot import CertificateSnapshot


class SnapshotCache(Protocol):
    def get(self, certificate_id: UUID) -> CertificateSnapshot | None: ...
    def put(self, snapshot: CertificateSnapshot) -> None: ...
