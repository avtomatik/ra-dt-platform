from uuid import UUID

from .base import SnapshotModel
from .metadata import CertificateMetadata
from .x509 import X509Snapshot


class CertificateSnapshot(SnapshotModel):
    certificate_id: UUID
    schema_version: int = 1
    metadata: CertificateMetadata
    x509: X509Snapshot

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
