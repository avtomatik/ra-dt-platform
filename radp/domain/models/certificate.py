from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from .base import DomainModel
from .metadata import CertificateMetadata
from .x509 import X509Certificate


class CertificateStatus(StrEnum):
    """Canonical status values used by the domain and persistence layer."""

    VALID = "VALID"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"

    @classmethod
    def _missing_(cls, value: object):
        # The RA API currently returns values such as "Valid". Normalize
        # casing and surrounding whitespace at the DTO/domain boundary.
        if isinstance(value, str):
            return cls._value2member_map_.get(value.strip().upper())
        return None


class CertificateLifecycle(DomainModel):
    status: CertificateStatus
    revoked_when: datetime | None = None
    revocation_reason: str | None = None


class Certificate(DomainModel):
    certificate_id: UUID
    metadata: CertificateMetadata
    x509: X509Certificate
    lifecycle: CertificateLifecycle = Field(
        default_factory=lambda: CertificateLifecycle(
            status=CertificateStatus.UNKNOWN
        )
    )

    def immutable_payload(self) -> dict:
        return self.model_dump(mode="json", exclude={"lifecycle"})

    @property
    def subject_by_oid(self) -> dict[str, str]:
        return {
            attribute.oid: attribute.value
            for attribute in self.x509.subject.attributes
        }

    @property
    def extension_by_oid(self) -> dict[str, str]:
        return {
            extension.oid: extension.value
            for extension in self.x509.extensions
        }
