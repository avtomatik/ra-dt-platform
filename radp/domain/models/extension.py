from .base import SnapshotModel


class ExtensionSnapshot(SnapshotModel):
    oid: str
    short_name: str | None
    name: str | None
    critical: bool
    value: str
