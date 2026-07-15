from datetime import datetime

from .base import SnapshotModel


class ValiditySnapshot(SnapshotModel):
    not_before: datetime
    not_after: datetime
