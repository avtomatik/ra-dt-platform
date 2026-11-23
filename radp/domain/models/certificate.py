import re
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field

from .base import DomainModel
from .metadata import CertificateMetadata
from .x509 import X509Certificate


class CertificateStatus(StrEnum):
    """Canonical certificate status and revocation reason values."""

    AFFILIATION_CHANGED = "AFFILIATION_CHANGED"
    CA_COMPROMISE = "CA_COMPROMISE"
    CESSATION_OF_OPERATION = "CESSATION_OF_OPERATION"
    EXPIRED = "EXPIRED"
    HOLD = "HOLD"
    KEY_COMPROMISE = "KEY_COMPROMISE"
    KEY_EXPIRED = "KEY_EXPIRED"
    NOT_YET_VALID = "NOT_YET_VALID"
    REVOKED = "REVOKED"
    SUPERSEDED = "SUPERSEDED"
    VALID = "VALID"
    UNKNOWN = "UNKNOWN"
    UNSPECIFIED = "UNSPECIFIED"

    @classmethod
    def _missing_(cls, value: object):
        """Normalize external status representations."""
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        if not normalized:
            return None
        # Separate acronym prefixes from subsequent PascalCase words.
        normalized = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", normalized)
        # Separate camelCase and PascalCase word boundaries.
        normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
        # Normalize whitespace, hyphens, and repeated underscores.
        normalized = re.sub(r"[\s_-]+", "_", normalized)
        normalized = normalized.strip("_").upper()
        return cls._value2member_map_.get(normalized)


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
