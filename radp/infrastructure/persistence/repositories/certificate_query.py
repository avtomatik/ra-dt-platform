from uuid import UUID

from sqlalchemy import DateTime, cast, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine

from radp.application.reporting.enums import CertificateReportStatus
from radp.application.reporting.models import CertificateReportFilters
from radp.domain.models.certificate import (Certificate, CertificateLifecycle,
                                            CertificateStatus)
from radp.domain.oid import OID
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
        return self._list(self._certificate_select())

    def get(self, certificate_id: UUID) -> Certificate | None:
        with self._engine.connect() as connection:
            statement = self._certificate_select().where(
                CertificateRecord.id == certificate_id
            )
            row = connection.execute(statement).mappings().one_or_none()
        return self._hydrate(row) if row else None

    def list_latest(self, limit: int = 20) -> list[Certificate]:
        return self._list(
            self._certificate_select()
            .order_by(CertificateRecord.persisted_at.desc())
            .limit(limit)
        )

    def list_for_report(
        self, filters: CertificateReportFilters, *, limit: int | None = None
    ) -> list[Certificate]:
        statement = self._certificate_select()
        if filters.status is CertificateReportStatus.VALID:
            statement = statement.where(
                CertificateRecord.status == CertificateStatus.VALID.value
            )
            not_after = cast(
                CertificateRecord.payload["metadata"]["not_after"].as_string(),
                DateTime(timezone=True),
            )
            statement = statement.where(not_after >= filters.valid_at_utc())
        if filters.gid is not None:
            subject_attributes = CertificateRecord.payload["x509"]["subject"][
                "attributes"
            ]
            statement = statement.where(
                subject_attributes.cast(JSONB).contains(
                    [{"oid": OID.GUID.value, "value": filters.gid}]
                )
            )
        statement = statement.order_by(CertificateRecord.persisted_at.asc())
        if limit is not None:
            statement = statement.limit(limit)
        return self._list(statement)

    @staticmethod
    def _certificate_select():
        return select(
            CertificateRecord.payload,
            CertificateRecord.status,
            CertificateRecord.revoked_when,
            CertificateRecord.revocation_reason,
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
