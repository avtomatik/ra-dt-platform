from uuid import UUID

from .certificate_snapshot import CertificateSnapshot
from .repository import SnapshotRepository


class MemorySnapshotRepository(SnapshotRepository):
    def __init__(self) -> None:
        self._items: dict[UUID, CertificateSnapshot] = {}

    def get(self, certificate_id: UUID) -> CertificateSnapshot | None:
        return self._items.get(certificate_id)

    def save(self, snapshot: CertificateSnapshot) -> None:
        self._items[snapshot.certificate_id] = snapshot

    def clear(self) -> None:
        self._items.clear()
