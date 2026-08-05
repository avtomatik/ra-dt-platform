from uuid import UUID

from sqlalchemy import desc, select

from radp.domain.models.certificate import CertificateSnapshot
from radp.infrastructure.persistence.models.certificates import \
    CertificateSnapshotRecord


class SnapshotRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_latest(self, certificate_id: UUID) -> CertificateSnapshot | None:
        with self.session_factory() as session:
            stmt = (
                select(CertificateSnapshotRecord)
                .where(
                    CertificateSnapshotRecord.certificate_id
                    == str(certificate_id)
                )
                .order_by(desc(CertificateSnapshotRecord.persisted_at))
                .limit(1)
            )
            record = session.scalar(stmt)
            return (
                CertificateSnapshot.model_validate_json(record.payload)
                if record
                else None
            )

    def save(self, snapshot: CertificateSnapshot) -> None:
        with self.session_factory() as session:
            session.add(CertificateSnapshotRecord.from_snapshot(snapshot))
            session.commit()

    def list_all(self) -> list[CertificateSnapshot]:
        with self.session_factory() as session:
            records = session.scalars(select(CertificateSnapshotRecord))
            return [
                CertificateSnapshot.model_validate_json(record.payload)
                for record in records
            ]

    def list_first(self, limit: int = 20) -> list[CertificateSnapshot]:
        with self.session_factory() as session:
            records = (
                session.query(CertificateSnapshotRecord)
                .order_by(CertificateSnapshotRecord.persisted_at)
                .limit(limit)
                .all()
            )
            return [
                CertificateSnapshot.model_validate_json(record.payload)
                for record in records
            ]

    def list_all_latest(self) -> list[CertificateSnapshot]: ...
