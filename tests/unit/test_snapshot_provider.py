from rads_explorer.certificate_domain.snapshot.memory_cache import \
    MemorySnapshotCache
from rads_explorer.certificate_domain.snapshot.memory_repository import \
    MemorySnapshotRepository
from rads_explorer.certificate_domain.snapshot.provider import SnapshotProvider


class FakeFactory:
    def __init__(self):
        self.calls = 0

    def create(self, certificate):
        self.calls += 1
        return "snapshot"


class FakeCertificate:
    id = "certificate-id"


def test_provider_uses_factory_only_when_missing():
    cache = MemorySnapshotCache()
    repository = MemorySnapshotRepository()
    factory = FakeFactory()
    provider = SnapshotProvider(cache, repository, factory)
    certificate = FakeCertificate()
    result = provider.get_or_create(certificate)
    assert result == "snapshot"
    assert factory.calls == 1


def test_provider_uses_cache_first():
    cache = MemorySnapshotCache()
    repository = MemorySnapshotRepository()
    factory = FakeFactory()
    provider = SnapshotProvider(cache, repository, factory)
    certificate = FakeCertificate()
    cache._items[certificate.id] = "cached"
    result = provider.get_or_create(certificate)
    assert result == "cached"
    assert factory.calls == 0
