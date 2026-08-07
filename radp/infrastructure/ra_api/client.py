from radp.infrastructure.ra_api.dto.certificate import CertificateDTO
from radp.infrastructure.ra_api.dto.pages import Page
from radp.infrastructure.transport.base import Transport

from .enums import SearchParameter
from .pagination import paginate
from .parser import parse_page, parse_response


class RAClient:
    DEFAULT_SEARCH_PARAMETER = SearchParameter.VALUE

    def __init__(
        self,
        transport: Transport,
        search_parameter: SearchParameter = DEFAULT_SEARCH_PARAMETER,
    ):
        self.transport = transport
        self.search_parameter = search_parameter

    async def _fetch_certificate_page(self, href: str) -> Page[CertificateDTO]:
        response = await self.transport.get(href)
        return parse_page(response, CertificateDTO)

    async def list_first_page(self) -> Page[CertificateDTO]:
        response = await self.transport.get("certificates")
        return parse_page(response, CertificateDTO)

    async def search_certificates(self, query: str) -> Page[CertificateDTO]:
        response = await self.transport.get(
            "certificates", params={self.search_parameter: query}
        )
        return parse_page(response, CertificateDTO)

    async def iter_certificates(self):
        first_page = await self.list_first_page()
        async for item in paginate(first_page, self._fetch_certificate_page):
            yield item

    async def list_all_certificates(self) -> list[CertificateDTO]:
        result = []
        async for item in self.iter_certificates():
            result.append(item)
        return result

    async def get_certificate(self, certificate_id: str) -> CertificateDTO:
        response = await self.transport.get(f"certificates/{certificate_id}")
        return parse_response(response, CertificateDTO)
