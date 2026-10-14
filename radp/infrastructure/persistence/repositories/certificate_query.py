from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.engine import Engine

from radp.domain.models.certificate import Certificate, CertificateLifecycle
from radp.infrastructure.persistence.models.certificates import \
    CertificateRecord


class CertificateQueryRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def count(self) -> int:
        with self._engine.connect() as connection:
            return int(
                connection.execute(
                    select(func.count()).select_from(CertificateRecord)
                ).scalar_one()
            )

    def list_first(self, limit: int = 20) -> list[Certificate]:
        return self._list(
            select(
                CertificateRecord.payload,
                CertificateRecord.status,
                CertificateRecord.revoked_when,
                CertificateRecord.revocation_reason,
            )
            .order_by(CertificateRecord.persisted_at.asc())
            .limit(limit)
        )

    def list_all(self) -> list[Certificate]:
        return self._list(
            select(
                CertificateRecord.payload,
                CertificateRecord.status,
                CertificateRecord.revoked_when,
                CertificateRecord.revocation_reason,
            )
        )

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

    def list_latest(self, limit: int = 20) -> list[Certificate]:
        return self._list(
            select(
                CertificateRecord.payload,
                CertificateRecord.status,
                CertificateRecord.revoked_when,
                CertificateRecord.revocation_reason,
            )
            .order_by(CertificateRecord.persisted_at.desc())
            .limit(limit)
        )

    def _list(self, statement) -> list[Certificate]:
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [self._hydrate(row) for row in rows]

    @staticmethod
    def _hydrate(row) -> Certificate:
        certificate = Certificate.model_validate(row["payload"])
        lifecycle = CertificateLifecycle(
            status=row["status"],
            revoked_when=row["revoked_when"],
            revocation_reason=row["revocation_reason"],
        )
        return certificate.model_copy(update={"lifecycle": lifecycle})
