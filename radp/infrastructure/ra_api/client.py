from collections.abc import AsyncIterator, Sequence

from radp.infrastructure.ra_api.dto.certificate import (CertificateDetailDTO,
                                                        CertificateSummaryDTO)
from radp.infrastructure.ra_api.dto.pages import Page
from radp.infrastructure.transport.base import Transport

from .enums import SearchParameter
from .pagination import paginate_pages
from .parser import parse_page, parse_response


class RAClient:
    DEFAULT_SEARCH_PARAMETER = SearchParameter.VALUE

    def __init__(
        self,
        transport: Transport,
        certificate_folders: Sequence[str],
        search_parameter: SearchParameter = DEFAULT_SEARCH_PARAMETER,
    ):
        # Accept a direct string defensively as one folder, not as a sequence
        # of individual characters. Normal application configuration supplies
        # a tuple parsed by Pydantic Settings.
        configured_folders = (
            (certificate_folders,)
            if isinstance(certificate_folders, str)
            else certificate_folders
        )
        folders = tuple(folder.strip() for folder in configured_folders)
        if not folders or any(not folder for folder in folders):
            raise ValueError(
                "At least one non-empty certificate folder is required."
            )
        self.transport = transport
        self.certificate_folders = tuple(dict.fromkeys(folders))
        self.search_parameter = search_parameter

    def _resolve_folder(self, folder: str | None) -> str:
        if folder is None:
            return self.certificate_folders[0]
        if folder not in self.certificate_folders:
            raise ValueError(f"Unconfigured RA certificate folder: {folder!r}")
        return folder

    async def _fetch_certificate_summary_page(
        self, href: str
    ) -> Page[CertificateSummaryDTO]:
        response = await self.transport.get(href)
        return parse_page(response, CertificateSummaryDTO)

    async def list_first_summary_page(
        self, folder: str | None = None
    ) -> Page[CertificateSummaryDTO]:
        selected_folder = self._resolve_folder(folder)
        response = await self.transport.get(
            "certificates", params={"folder": selected_folder}
        )
        return parse_page(response, CertificateSummaryDTO)

    async def search_certificates(
        self, query: str, folder: str | None = None
    ) -> Page[CertificateSummaryDTO]:
        selected_folder = self._resolve_folder(folder)
        response = await self.transport.get(
            "certificates",
            params={
                "folder": selected_folder,
                self.search_parameter: query,
            },
        )
        return parse_page(response, CertificateSummaryDTO)

    async def iter_certificate_summary_pages(
        self, folder: str | None = None
    ) -> AsyncIterator[Page[CertificateSummaryDTO]]:
        selected_folder = self._resolve_folder(folder)
        first_page = await self.list_first_summary_page(selected_folder)
        async for page in paginate_pages(
            first_page, self._fetch_certificate_summary_page
        ):
            yield page

    async def get_certificate(
        self, certificate_id: str
    ) -> CertificateDetailDTO:
        response = await self.transport.get(f"certificates/{certificate_id}")
        return parse_response(response, CertificateDetailDTO)
