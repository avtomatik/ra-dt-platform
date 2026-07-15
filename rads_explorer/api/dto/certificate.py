from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import DTOModel
from .extension import Extension
from .name_attributes import NameAttributes


class CertificateBaseDTO(DTOModel):
    id: UUID
    name_attributes: NameAttributes = Field(validation_alias="nameAttributes")

    serial_number: str = Field(validation_alias="serialNumber")
    thumbprint: str

    not_before: datetime = Field(validation_alias="notBefore")
    not_after: datetime = Field(validation_alias="notAfter")
    key_not_after: datetime = Field(validation_alias="keyNotAfter")
    created_when: datetime = Field(validation_alias="createdWhen")

    status: str


class CertificateSummaryDTO(CertificateBaseDTO): ...


class CertificateDetailDTO(CertificateBaseDTO):
    cert_request_id: str | None = Field(None, validation_alias="certRequestId")
    subject: str | None = None
    issuer: str | None = None
    user_id: UUID | None = Field(None, validation_alias="userId")

    version: int = 3

    public_key: str | None = Field(None, validation_alias="publicKey")
    public_key_parameters: str | None = Field(
        None, validation_alias="publicKeyParameters"
    )
    public_key_oid: str | None = Field(None, validation_alias="publicKeyOid")
    public_key_oid_description: str | None = Field(
        None, validation_alias="publicKeyOidDescription"
    )

    extensions: list[Extension] | None = None

    signature: str | None = None
    signature_oid: str | None = Field(None, validation_alias="signatureOid")
    signature_oid_description: str | None = Field(
        None, validation_alias="signatureOidDescription"
    )

    raw_certificate: bytes | None = Field(
        None, validation_alias="rawCertificate"
    )

    revocation_reason: str | None = Field(
        None, validation_alias="revocationReason"
    )
    revoked_when: datetime | None = Field(None, validation_alias="revokedWhen")

    folder: str | None = None
