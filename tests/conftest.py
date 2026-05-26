import pytest

from rads_explorer.api.client import RADSClient
from rads_explorer.application.cache.certificate_details import \
    CertificateDetailCache
from rads_explorer.application.services.certificate_service import \
    CertificateService
from rads_explorer.config.settings import Settings
from rads_explorer.data.reports import ReportService
from rads_explorer.infrastructure.transport.http import HTTPTransport


@pytest.fixture
def client(settings) -> RADSClient:
    transport = HTTPTransport(settings)
    return RADSClient(transport)


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def detail_cache() -> CertificateDetailCache:
    return CertificateDetailCache()


@pytest.fixture
def report_service(client, detail_cache) -> ReportService:
    return ReportService(CertificateService(client, detail_cache))
