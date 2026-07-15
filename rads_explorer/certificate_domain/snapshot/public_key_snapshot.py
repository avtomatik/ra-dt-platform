from .base import SnapshotModel


class PublicKeySnapshot(SnapshotModel):
    algorithm: str
    oid: str | None = None
    key_size: int | None = None
    parameters: str | None = None
