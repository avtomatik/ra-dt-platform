from .base import SnapshotModel


class SignatureSnapshot(SnapshotModel):
    oid: str
    algorithm: str | None = None
