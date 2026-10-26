from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest

from radp.application.synchronization.certificates import \
    CertificateSynchronizer
from radp.domain.models.certificate import (CertificateLifecycle,
                                            CertificateStatus)
from radp.infrastructure.ra_api.dto.certificate import CertificateSummaryDTO


class FakeClient:
    def __init__(self, summaries, details=None):
        self.summaries = summaries
        self.details = details or {}
        self.detail_calls = []

    async def iter_certificate_summary_pages(self):
        yield SimpleNamespace(items=self.summaries)

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

    def update_lifecycle(self, certificate_id, **kwargs):
        self.updated.append((certificate_id, kwargs))


class FakeFactory:
    def __init__(self):
        self.calls = []

    def create(self, detail):
        self.calls.append(detail)
        return detail


def summary(certificate_id, status):
    return CertificateSummaryDTO(id=certificate_id, status=status)


@pytest.mark.asyncio
async def test_summary_status_is_normalized_to_domain_enum():
    parsed = summary(uuid4(), "Valid")

    assert parsed.status is CertificateStatus.VALID


@pytest.mark.asyncio
async def test_matching_statuses_skip_detail_fetch_and_x509_factory():
    certificate_id = uuid4()
    summaries = [summary(certificate_id, "Valid")]
    client = FakeClient(summaries)
    repository = FakeRepository(
        {certificate_id: CertificateLifecycle(status="VALID")}
    )
    factory = FakeFactory()

    result = await CertificateSynchronizer(
        client, repository, factory
    ).synchronize()

    assert result == 0
    assert client.detail_calls == []
    assert factory.calls == []
    assert repository.lookup_calls == [[certificate_id]]
    assert repository.updated == []
    assert repository.saved == []


@pytest.mark.asyncio
async def test_status_mismatch_fetches_detail_and_updates_lifecycle():
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

    result = await CertificateSynchronizer(
        client, repository, factory
    ).synchronize()

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


@pytest.mark.asyncio
async def test_new_certificate_fetches_detail_and_saves_full_certificate():
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

    result = await CertificateSynchronizer(
        client, repository, factory
    ).synchronize()

    assert result == 1
    assert client.detail_calls == [str(certificate_id)]
    assert repository.saved == [detail]
    assert repository.updated == []
