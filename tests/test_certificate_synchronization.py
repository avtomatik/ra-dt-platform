import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from radp.application.synchronization.certificates import (
    CertificateSynchronizer, FolderSynchronizationError)
from radp.domain.models.certificate import (CertificateLifecycle,
                                            CertificateStatus)
from radp.infrastructure.ra_api.dto.certificate import CertificateSummaryDTO


class FakeClient:
    def __init__(
        self, summaries=None, details=None, *, folders=None, failures=None
    ):
        self.summaries = summaries or []
        self.details = details or {}
        self.certificate_folders = tuple(folders or ("default",))
        self.pages_by_folder = {
            folder: self.summaries for folder in self.certificate_folders
        }
        self.failures = failures or set()
        self.folder_calls = []
        self.detail_calls = []

    async def iter_certificate_summary_pages(self, folder):
        self.folder_calls.append(folder)
        if folder in self.failures:
            raise RuntimeError(f"failure in {folder}")
        yield SimpleNamespace(items=self.pages_by_folder[folder])

    async def get_certificate(self, certificate_id):
        self.detail_calls.append(certificate_id)
        return self.details[certificate_id]


class FakeRepository:
    def __init__(self, lifecycles=None):
        self.lifecycles = lifecycles or {}
        self.lookup_calls = []
        self.saved = []
        self.updated = []

    def get_lifecycles(self, certificate_ids):
        self.lookup_calls.append(list(certificate_ids))
        return {
            key: value
            for key, value in self.lifecycles.items()
            if key in certificate_ids
        }

    def save(self, certificate):
        self.saved.append(certificate)
        self.lifecycles[certificate.certificate_id] = certificate.lifecycle

    def update_lifecycle(self, certificate_id, **kwargs):
        self.updated.append((certificate_id, kwargs))


class FakeFactory:
    def __init__(self):
        self.calls = []

    def create(self, detail):
        self.calls.append(detail)
        return detail


def summary(certificate_id, status):
    return CertificateSummaryDTO(
        id=certificate_id,
        nameAttributes={"2.5.4.3": "test-certificate"},
        serialNumber="01",
        thumbprint="test-thumbprint",
        notBefore=datetime(2026, 1, 1, tzinfo=timezone.utc),
        notAfter=datetime(2036, 1, 1, tzinfo=timezone.utc),
        keyNotAfter=datetime(2030, 1, 1, tzinfo=timezone.utc),
        createdWhen=datetime(2026, 1, 1, tzinfo=timezone.utc),
        status=status,
    )


def test_summary_status_is_normalized_to_domain_enum():
    parsed = summary(uuid4(), "Valid")
    assert parsed.status is CertificateStatus.VALID


def test_matching_statuses_skip_detail_fetch_and_x509_factory():
    certificate_id = uuid4()
    summaries = [summary(certificate_id, "Valid")]
    client = FakeClient(summaries)
    repository = FakeRepository(
        {certificate_id: CertificateLifecycle(status="VALID")}
    )
    factory = FakeFactory()
    result = asyncio.run(
        CertificateSynchronizer(client, repository, factory).synchronize()
    )
    assert result == 0
    assert client.detail_calls == []
    assert factory.calls == []
    assert repository.lookup_calls == [[certificate_id]]
    assert repository.updated == []
    assert repository.saved == []


def test_status_mismatch_fetches_detail_and_updates_lifecycle():
    certificate_id = uuid4()
    revoked_when = datetime(2026, 1, 1, tzinfo=timezone.utc)
    detail = SimpleNamespace(
        lifecycle=CertificateLifecycle(
            status="REVOKED",
            revoked_when=revoked_when,
            revocation_reason="KEY_COMPROMISE",
        )
    )
    client = FakeClient(
        [summary(certificate_id, "Revoked")],
        details={str(certificate_id): detail},
    )
    repository = FakeRepository(
        {certificate_id: CertificateLifecycle(status="VALID")}
    )
    factory = FakeFactory()
    result = asyncio.run(
        CertificateSynchronizer(client, repository, factory).synchronize()
    )
    assert result == 1
    assert client.detail_calls == [str(certificate_id)]
    assert repository.updated == [
        (
            certificate_id,
            {
                "status": CertificateStatus.REVOKED,
                "revoked_when": revoked_when,
                "revocation_reason": "KEY_COMPROMISE",
            },
        )
    ]


def test_new_certificate_fetches_detail_and_saves_full_certificate():
    certificate_id = uuid4()
    detail = SimpleNamespace(
        lifecycle=CertificateLifecycle(status="VALID"),
        certificate_id=certificate_id,
    )
    client = FakeClient(
        [summary(certificate_id, "Valid")],
        details={str(certificate_id): detail},
    )
    repository = FakeRepository()
    factory = FakeFactory()
    result = asyncio.run(
        CertificateSynchronizer(client, repository, factory).synchronize()
    )
    assert result == 1
    assert client.detail_calls == [str(certificate_id)]
    assert repository.saved == [detail]
    assert repository.updated == []


def test_all_configured_folders_are_processed_in_sequence():
    first_id, second_id = uuid4(), uuid4()
    first_detail = SimpleNamespace(
        lifecycle=CertificateLifecycle(status="VALID"), certificate_id=first_id
    )
    second_detail = SimpleNamespace(
        lifecycle=CertificateLifecycle(status="VALID"),
        certificate_id=second_id,
    )
    client = FakeClient(
        details={str(first_id): first_detail, str(second_id): second_detail},
        folders=("folder1", "folder2"),
    )
    client.pages_by_folder = {
        "folder1": [summary(first_id, "Valid")],
        "folder2": [summary(second_id, "Valid")],
    }
    repository = FakeRepository()
    synchronizer = CertificateSynchronizer(client, repository, FakeFactory())
    result = asyncio.run(synchronizer.synchronize())
    assert result == 2
    assert client.folder_calls == ["folder1", "folder2"]
    assert [item.certificate_id for item in repository.saved] == [
        first_id,
        second_id,
    ]


def test_certificate_appearing_in_multiple_folders_is_processed_once():
    certificate_id = uuid4()
    detail = SimpleNamespace(
        lifecycle=CertificateLifecycle(status="VALID"),
        certificate_id=certificate_id,
    )
    client = FakeClient(
        details={str(certificate_id): detail}, folders=("folder1", "folder2")
    )
    client.pages_by_folder = {
        "folder1": [summary(certificate_id, "Valid")],
        "folder2": [summary(certificate_id, "Valid")],
    }
    repository = FakeRepository()
    result = asyncio.run(
        CertificateSynchronizer(
            client, repository, FakeFactory()
        ).synchronize()
    )
    assert result == 1
    assert len(repository.saved) == 1
    assert client.detail_calls == [str(certificate_id)]


def test_failed_folder_does_not_prevent_remaining_folders_from_running():
    certificate_id = uuid4()
    detail = SimpleNamespace(
        lifecycle=CertificateLifecycle(status="VALID"),
        certificate_id=certificate_id,
    )
    client = FakeClient(
        details={str(certificate_id): detail},
        folders=("failed-folder", "healthy-folder"),
        failures={"failed-folder"},
    )
    client.pages_by_folder = {
        "failed-folder": [],
        "healthy-folder": [summary(certificate_id, "Valid")],
    }
    repository = FakeRepository()
    with pytest.raises(FolderSynchronizationError) as captured:
        asyncio.run(
            CertificateSynchronizer(
                client, repository, FakeFactory()
            ).synchronize()
        )
    assert set(captured.value.failed_folders) == {"failed-folder"}
    assert client.folder_calls == ["failed-folder", "healthy-folder"]
    assert len(repository.saved) == 1


def test_duplicate_certificate_within_one_page_is_processed_once():
    certificate_id = uuid4()
    detail = SimpleNamespace(
        lifecycle=CertificateLifecycle(status="VALID"),
        certificate_id=certificate_id,
    )
    duplicate_summary = summary(certificate_id, "Valid")
    client = FakeClient(
        [duplicate_summary, duplicate_summary],
        details={str(certificate_id): detail},
    )
    repository = FakeRepository()
    result = asyncio.run(
        CertificateSynchronizer(
            client, repository, FakeFactory()
        ).synchronize()
    )
    assert result == 1
    assert len(repository.saved) == 1
    assert client.detail_calls == [str(certificate_id)]
