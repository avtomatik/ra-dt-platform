from datetime import datetime
from typing import Any, Mapping
from uuid import UUID

from radp.domain.models.certificate import CertificateStatus

from .base import DTOModel


class CertificateBaseDTO(DTOModel):
    id: UUID
    name_attributes: Mapping[str, str]
    serial_number: str
    thumbprint: str
    not_before: datetime
    not_after: datetime
    key_not_after: datetime
    created_when: datetime
    status: CertificateStatus


class CertificateSummaryDTO(CertificateBaseDTO): ...


class CertificateDetailDTO(CertificateSummaryDTO):
    cert_request_id: str | None = None
    subject: str | None = None
    issuer: str | None = None
    user_id: UUID | None = None
    version: int = 3
    public_key: str | None = None
    public_key_parameters: str | None = None
    public_key_oid: str | None = None
    public_key_oid_description: str | None = None
    extensions: list[Mapping[str, Any]] | None = None
    signature: str | None = None
    signature_oid: str | None = None
    signature_oid_description: str | None = None
    raw_certificate: bytes | None = None
    revocation_reason: str | None = None
    revoked_when: datetime | None = None
    folder: str | None = None
