from pydantic import Field

from .base import DTOModel
from .certificate import CertificateSummaryDTO
from .certificate_request import CertificateRequest
from .pages import Links
from .user import User


class CertificateRequestsResponse(DTOModel):
    items: list[CertificateRequest]
    links: Links | None = Field(None, validation_alias="_links")


class CertificatesResponse(DTOModel):
    items: list[CertificateSummaryDTO]
    links: Links | None = Field(None, validation_alias="_links")


class UsersResponse(DTOModel):
    items: list[User]
    links: Links | None = Field(None, validation_alias="_links")
