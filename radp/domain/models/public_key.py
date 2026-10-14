from .base import DomainModel


class PublicKey(DomainModel):
    algorithm_oid: str
    algorithm_name: str | None
    key_size: int | None
    fingerprint_sha256: str | None
    pem: str | None
