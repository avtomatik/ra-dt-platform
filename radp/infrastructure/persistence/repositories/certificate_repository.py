from datetime import datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import Engine

from radp.domain.models.certificate import Certificate, CertificateLifecycle
from radp.infrastructure.persistence.models.certificates import \
    CertificateRecord


class CertificateRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def exists(self, certificate_id: UUID) -> bool:
        with self._engine.connect() as connection:
            statement = (
                select(CertificateRecord.id)
                .where(CertificateRecord.id == certificate_id)
                .limit(1)
            )
            return connection.execute(statement).first() is not None

    def get(self, certificate_id: UUID) -> Certificate | None:
        with self._engine.connect() as connection:
            statement = select(
                CertificateRecord.payload,
                CertificateRecord.status,
                CertificateRecord.revoked_when,
                CertificateRecord.revocation_reason,
            ).where(CertificateRecord.id == certificate_id)
            row = connection.execute(statement).mappings().one_or_none()
        return self._hydrate(row) if row else None

    def save(self, certificate: Certificate) -> None:
        record = CertificateRecord.from_certificate(certificate)
        with self._engine.begin() as connection:
            connection.execute(
                CertificateRecord.__table__.insert().values(
                    id=record.id,
                    status=record.status,
                    revoked_when=record.revoked_when,
                    revocation_reason=record.revocation_reason,
                    payload=record.payload,
                )
            )

    def update_lifecycle(
        self,
        certificate_id: UUID,
        *,
        status: str,
        revoked_when: datetime | None,
        revocation_reason: str | None,
    ) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                update(CertificateRecord)
                .where(CertificateRecord.id == certificate_id)
                .values(
                    status=status,
                    revoked_when=revoked_when,
                    revocation_reason=revocation_reason,
                )
            )

    @staticmethod
    def _hydrate(row) -> Certificate:
        certificate = Certificate.model_validate(row["payload"])
        lifecycle = CertificateLifecycle(
            status=row["status"],
            revoked_when=row["revoked_when"],
            revocation_reason=row["revocation_reason"],
        )
        return certificate.model_copy(update={"lifecycle": lifecycle})
