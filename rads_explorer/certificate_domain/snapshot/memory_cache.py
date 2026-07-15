from uuid import UUID

from .cache import SnapshotCache
from .certificate_snapshot import CertificateSnapshot


class MemorySnapshotCache(SnapshotCache):
    def __init__(self) -> None:
        self._items: dict[UUID, CertificateSnapshot] = {}

    def get(self, certificate_id: UUID) -> CertificateSnapshot | None:
        return self._items.get(certificate_id)

    def put(self, snapshot: CertificateSnapshot) -> None:
        self._items[snapshot.certificate_id] = snapshot

    def clear(self) -> None:
        self._items.clear()
