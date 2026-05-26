import logging
from functools import lru_cache

from rads_explorer.api.client import RADSClient
from rads_explorer.application.cache.certificate_details import \
    CertificateDetailCache
from rads_explorer.application.services.cert_request_service import \
    CertificateRequestService
from rads_explorer.application.services.certificate_service import \
    CertificateService
from rads_explorer.application.services.search_service import SearchService
from rads_explorer.application.services.user_service import UserService
from rads_explorer.config.enums import TransportMode
from rads_explorer.config.settings import Settings
from rads_explorer.data.export.xlsx import XLSXExporter
from rads_explorer.data.reports import ReportService
from rads_explorer.infrastructure.transport.cryptopro_curl import \
    CryptoProCurlTransport
from rads_explorer.infrastructure.transport.http import HTTPTransport

logger = logging.getLogger(__name__)


class Container:
    def __init__(self):
        self._settings = Settings()
        self._validate_settings()

        self._transport = self._build_transport()
        self._client = RADSClient(self._transport)
        self._certificate_cache = CertificateDetailCache()

        logger.info("Transport mode: %s", self._settings.transport)
        logger.info("API base URL: %s", self._settings.api_base_url)

    def _build_transport(self):
        match self._settings.transport:
            case TransportMode.CURL:
                return CryptoProCurlTransport(self._settings)

            case TransportMode.HTTP:
                return HTTPTransport(self._settings)

            case _:
                raise ValueError(
                    f"Unsupported transport: " f"{self._settings.transport}"
                )

    def _validate_settings(self):
        if self._settings.transport == TransportMode.CURL:
            if not self._settings.api_base_url:
                raise RuntimeError("API base URL required.")
            if not self._settings.cert_thumbprint:
                raise RuntimeError("cert thumbprint required.")

    def certificate_service(self):
        return CertificateService(self._client, self._certificate_cache)

    def cert_request_service(self):
        return CertificateRequestService(self._client)

    def user_service(self):
        return UserService(self._client)

    def search_service(self):
        return SearchService(self._client)

    def report_service(self):
        return ReportService(self.certificate_service())

    def exporter(self):
        return XLSXExporter()


@lru_cache
def get_container() -> Container:
    return Container()
