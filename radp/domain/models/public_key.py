from .base import SnapshotModel


class PublicKeySnapshot(SnapshotModel):
    algorithm_oid: str
    algorithm_name: str
    key_size: int | None
    fingerprint_sha256: str
    pem: str
