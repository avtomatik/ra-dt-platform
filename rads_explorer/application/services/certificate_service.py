from rads_explorer.api.client import RADSClient
from rads_explorer.api.dto.certificate import CertificateSummaryDTO
from rads_explorer.application.cache.certificate_details import \
    CertificateDetailCache
from rads_explorer.application.mappers.certificate import CertificateMapper
from rads_explorer.certificate_domain.models.certificate import Certificate


class CertificateService:
    def __init__(self, api_client: RADSClient, cache: CertificateDetailCache):
        self.api = api_client
        self.cache = cache

    def list_page(self):
        return self.api.certificates.list_page()

    def iter_all(self):
        yield from self.api.certificates.iter_all()

    def list_all(self):
        return self.api.certificates.list_all()

    def search(self, query: str):
        return self.api.certificates.search(query)

    def detail_by_id(self, certificate_id: str) -> Certificate:
        cached = self.cache.get_by_id(certificate_id)
        if cached:
            return CertificateMapper.to_domain(cached)
        dto = self.api.certificates.get_by_id(certificate_id)
        self.cache.put(dto)
        return CertificateMapper.to_domain(dto)

    def detail_by_serial(self, serial_number: str) -> Certificate:
        cached = self.cache.get_by_serial(serial_number)
        if cached:
            return CertificateMapper.to_domain(cached)
        dto = self.api.certificates.get_by_serial(serial_number)
        self.cache.put(dto)
        return CertificateMapper.to_domain(dto)

    def resolve(self, summary: CertificateSummaryDTO) -> Certificate:
        return self.detail_by_id(summary.id)

    def iter_details(self):
        for summary in self.iter_all():
            yield self.resolve(summary)
