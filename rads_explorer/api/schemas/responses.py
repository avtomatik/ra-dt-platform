from pydantic import Field

from .base import APIModel
from .cert_request import CertificateRequest
from .certificate import CertificateSummary
from .pages import Links
from .user import User


class CertificateRequestsResponse(APIModel):
    items: list[CertificateRequest]
    links: Links = Field(validation_alias="_links")


class CertificatesResponse(APIModel):
    items: list[CertificateSummary]
    links: Links = Field(validation_alias="_links")


class UsersResponse(APIModel):
    items: list[User]
    links: Links = Field(validation_alias="_links")
