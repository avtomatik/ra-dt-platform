from radp.infrastructure.ra_api.dto.certificate import (CertificateDetailDTO,
                                                        CertificateSummaryDTO)
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
        certificate_folder: str,
        search_parameter: SearchParameter = DEFAULT_SEARCH_PARAMETER,
    ):
        self.transport = transport
        self.certificate_folder = certificate_folder
        self.search_parameter = search_parameter

    async def _fetch_certificate_summary_page(
        self, href: str
    ) -> Page[CertificateSummaryDTO]:
        response = await self.transport.get(href)
        return parse_page(response, CertificateSummaryDTO)

    async def list_first_summary_page(self) -> Page[CertificateSummaryDTO]:
        response = await self.transport.get(
            "certificates", params={"folder": self.certificate_folder}
        )
        return parse_page(response, CertificateSummaryDTO)

    async def search_certificates(
        self, query: str
    ) -> Page[CertificateSummaryDTO]:
        response = await self.transport.get(
            "certificates",
            params={
                "folder": self.certificate_folder,
                self.search_parameter: query,
            },
        )
        return parse_page(response, CertificateSummaryDTO)

    async def iter_certificate_summary_pages(self):
        first_page = await self.list_first_summary_page()
        async for item in paginate(
            first_page, self._fetch_certificate_summary_page
        ):
            yield item

    async def get_certificate(
        self, certificate_id: str
    ) -> CertificateDetailDTO:
        response = await self.transport.get(f"certificates/{certificate_id}")
        return parse_response(response, CertificateDetailDTO)
