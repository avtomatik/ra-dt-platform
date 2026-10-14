from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import DomainModel
from .metadata import CertificateMetadata
from .x509 import X509Certificate


class CertificateLifecycle(DomainModel):
    status: str
    revoked_when: datetime | None = None
    revocation_reason: str | None = None


class Certificate(DomainModel):
    certificate_id: UUID
    metadata: CertificateMetadata
    x509: X509Certificate
    lifecycle: CertificateLifecycle = Field(
        default_factory=lambda: CertificateLifecycle(status="UNKNOWN")
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
