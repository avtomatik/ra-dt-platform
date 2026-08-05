from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from radp.domain.models.certificate import CertificateSnapshot

from .base import Base


class CertificateSnapshotRecord(Base):
    __tablename__ = "certificate_snapshots"

    id: Mapped[str] = mapped_column(
        String(64), primary_key=True, default=lambda: str(uuid4())
    )
    certificate_id: Mapped[str] = mapped_column(
        String(64), index=True, nullable=False
    )
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    @classmethod
    def from_snapshot(
        cls, snapshot: CertificateSnapshot
    ) -> "CertificateSnapshotRecord":
        return cls(
            certificate_id=str(snapshot.certificate_id),
            payload=snapshot.model_dump_json(),
        )
