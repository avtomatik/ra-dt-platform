from radp.infrastructure.ra_api.dto.certificate import CertificateDTO
from radp.infrastructure.ra_api.dto.pages import Page
from radp.infrastructure.transport.base import Transport

from .pagination import paginate
from .parser import parse_page, parse_response


class RAClient:
    def __init__(self, transport: Transport):
        self.transport = transport

    def _fetch_certificate_page(self, href: str) -> Page[CertificateDTO]:
        response = self.transport.get(href)
        return parse_page(response, CertificateDTO)

    def list_first_page(self) -> Page[CertificateDTO]:
        response = self.transport.get("certificates")
        return parse_page(response, CertificateDTO)

    def search_certificates(self, query: str) -> Page[CertificateDTO]:
        # =====================================================================
        # Search Options
        # =====================================================================
        # =====================================================================
        # {"filter": "test"}
        # {"q": "test"}
        # {"query": "test"}
        # {"search": "test"}
        # {"text": "test"}
        # =====================================================================
        response = self.transport.get("certificates", params={"value": query})
        return parse_page(response, CertificateDTO)

    def iter_certificates(self):
        first_page = self.list_first_page()
        yield from paginate(first_page, self._fetch_certificate_page)

    def list_all_certificates(self) -> list[CertificateDTO]:
        return list(self.iter_certificates())

    def get_certificate(self, certificate_id: str) -> CertificateDTO:
        response = self.transport.get(f"certificates/{certificate_id}")
        return parse_response(response, CertificateDTO)
