from datetime import datetime

from .base import SnapshotModel


class LifecycleSnapshot(SnapshotModel):
    key_not_after: datetime
    created_when: datetime
    revoked_when: datetime | None = None
