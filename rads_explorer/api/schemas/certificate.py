import base64
from datetime import datetime
from functools import cached_property

from cryptography import x509
from pydantic import Field, field_validator

from .base import APIModel
from .extension import Extension
from .name_attributes import NameAttributes


class CertificateBase(APIModel):
    id: str
    name_attributes: NameAttributes = Field(validation_alias="nameAttributes")

    serial_number: str = Field(validation_alias="serialNumber")
    thumbprint: str

    not_before: datetime = Field(validation_alias="notBefore")
    not_after: datetime = Field(validation_alias="notAfter")
    key_not_after: datetime = Field(validation_alias="keyNotAfter")
    created_when: datetime = Field(validation_alias="createdWhen")

    status: str


class CertificateSummary(CertificateBase): ...


class CertificateDetail(CertificateBase):
    cert_request_id: str | None = Field(None, validation_alias="certRequestId")
    subject: str | None = None
    issuer: str | None = None
    user_id: str | None = Field(None, validation_alias="userId")

    version: int | None = None

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

    @field_validator("raw_certificate", mode="before")
    @classmethod
    def _parse_raw_certificate(cls, value):
        if value is None:
            return None

        if isinstance(value, bytes):
            return value

        if not isinstance(value, str):
            raise TypeError("raw_certificate must be str or bytes")

        value = value.strip()

        return cls._decode_certificate(value)

    @staticmethod
    def _decode_certificate(value: str) -> bytes:
        if value.startswith("\\x"):
            return bytes.fromhex(value.replace("\\x", ""))

        if all(c in "0123456789abcdefABCDEF" for c in value):
            return bytes.fromhex(value)

        return base64.b64decode(value, validate=True)

    @cached_property
    def x509(self) -> x509.Certificate:
        if not self.raw_certificate:
            raise ValueError("Certificate is empty.")
        return x509.load_der_x509_certificate(self.raw_certificate)
