from functools import cached_property
from uuid import UUID

from .base import SnapshotModel
from .extension_snapshot import CertificateExtension
from .lifecycle_snapshot import LifecycleSnapshot
from .public_key_snapshot import PublicKeySnapshot
from .signature_snapshot import SignatureSnapshot
from .subject_attribute import CertificateAttribute
from .validity_snapshot import ValiditySnapshot


class CertificateSnapshot(SnapshotModel):
    certificate_id: UUID
    serial_number: str
    status: str
    version: int
    fingerprint_sha256: str
    subject: str
    issuer: str
    subject_attributes: list[CertificateAttribute]
    issuer_attributes: list[CertificateAttribute]
    extensions: list[CertificateExtension]
    public_key: PublicKeySnapshot
    signature: SignatureSnapshot
    validity: ValiditySnapshot
    lifecycle: LifecycleSnapshot

    @cached_property
    def subject_by_oid(self) -> dict[str, str]:
        return {
            attribute.oid: attribute.value
            for attribute in self.subject_attributes
        }

    @cached_property
    def extension_by_oid(self) -> dict[str, str]:
        return {
            extension.oid: extension.value for extension in self.extensions
        }
