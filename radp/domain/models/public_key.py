from .base import SnapshotModel


class PublicKeySnapshot(SnapshotModel):
    algorithm_oid: str
    algorithm_name: str | None
    key_size: int | None
    fingerprint_sha256: str | None
    pem: str | None
