from rads_explorer.api.client import RADSClient
from rads_explorer.api.schemas.certificate import (CertificateDetail,
                                                   CertificateSummary)
from rads_explorer.application.cache.certificate_details import \
    CertificateDetailCache


class CertificateService:
    def __init__(self, api_client: RADSClient, cache: CertificateDetailCache):
        self.api = api_client
        self.cache = cache

    def list(self):
        return self.api.certificates.list()

    def search(self, query: str):
        return self.api.certificates.search(query)

    def detail_by_id(self, certificate_id: str) -> CertificateDetail:
        cached = self.cache.get_by_id(certificate_id)

        if cached:
            return cached

        detail = self.api.certificates.get_by_id(certificate_id)
        self.cache.put(detail)
        return detail

    def detail_by_serial(self, serial_number: str) -> CertificateDetail:
        cached = self.cache.get_by_serial(serial_number)

        if cached:
            return cached

        detail = self.api.certificates.get_by_serial(serial_number)
        self.cache.put(detail)
        return detail

    def resolve(self, summary: CertificateSummary) -> CertificateDetail:
        return self.detail_by_id(summary.id)

    def iter_details(self):
        for summary in self.list().items:
            yield self.resolve(summary)
