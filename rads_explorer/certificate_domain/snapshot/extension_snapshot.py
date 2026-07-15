from .base import SnapshotModel


class CertificateExtension(SnapshotModel):
    oid: str
    name: str | None
    critical: bool
    value: str
