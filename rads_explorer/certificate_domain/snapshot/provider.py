from rads_explorer.certificate_domain.models.certificate import Certificate

from .cache import SnapshotCache
from .certificate_snapshot import CertificateSnapshot
from .factory import CertificateSnapshotFactory
from .repository import SnapshotRepository


class SnapshotProvider:
    def __init__(
        self,
        cache: SnapshotCache,
        repository: SnapshotRepository,
        factory: CertificateSnapshotFactory,
    ):
        self._cache = cache
        self._repository = repository
        self._factory = factory

    def get_or_create(self, certificate: Certificate) -> CertificateSnapshot:
        # =============================================================
        # 1. Memory cache
        # =============================================================
        cached = self._cache.get(certificate.id)
        if cached:
            return cached
        # =============================================================
        # 2. Persistent repository
        # =============================================================
        stored = self._repository.get(certificate.id)
        if stored:
            self._cache.put(stored)
            return stored
        # =============================================================
        # 3. Generate snapshot
        # =============================================================
        snapshot = self._factory.create(certificate)
        # =============================================================
        # 4. Persist snapshot
        # =============================================================
        self._repository.save(snapshot)
        # =============================================================
        # 5. Populate cache
        # =============================================================
        self._cache.put(snapshot)
        return snapshot
