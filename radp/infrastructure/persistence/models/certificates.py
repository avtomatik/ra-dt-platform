from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CertificateRecord(Base):
    __tablename__ = "certificates"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    revoked_when: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    revocation_reason: Mapped[str | None] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    persisted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )

    @classmethod
    def from_certificate(cls, certificate) -> "CertificateRecord":
        return cls(
            id=certificate.certificate_id,
            status=certificate.lifecycle.status.value,
            revoked_when=certificate.lifecycle.revoked_when,
            revocation_reason=certificate.lifecycle.revocation_reason,
            payload=certificate.immutable_payload(),
        )
