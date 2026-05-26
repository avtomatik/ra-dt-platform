from dataclasses import dataclass

from rads_explorer.api.schemas.cert_request import CertificateRequest
from rads_explorer.api.schemas.certificate import CertificateSummary
from rads_explorer.api.schemas.user import User


@dataclass
class Dataset:
    cert_requests: list[CertificateRequest]
    certificates: list[CertificateSummary]
    users: list[User]
