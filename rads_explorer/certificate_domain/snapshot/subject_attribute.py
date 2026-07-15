from .base import SnapshotModel


class CertificateAttribute(SnapshotModel):
    oid: str
    name: str | None
    value: str
