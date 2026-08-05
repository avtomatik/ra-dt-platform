from .base import SnapshotModel


class DistinguishedNameAttribute(SnapshotModel):
    oid: str
    short_name: str | None
    name: str | None
    value: str
