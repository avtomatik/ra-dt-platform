from .attribute import DistinguishedNameAttribute
from .base import SnapshotModel


class DistinguishedName(SnapshotModel):
    rfc4514: str
    attributes: list[DistinguishedNameAttribute]
