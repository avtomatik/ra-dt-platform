from dataclasses import dataclass

from rads_explorer.api.dto.certificate import CertificateSummaryDTO
from rads_explorer.api.dto.certificate_request import CertificateRequest
from rads_explorer.api.dto.user import User


@dataclass
class Dataset:
    cert_requests: list[CertificateRequest]
    certificates: list[CertificateSummaryDTO]
    users: list[User]
