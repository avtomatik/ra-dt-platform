from datetime import datetime, timezone

from sqlalchemy import select

from radp.domain.oid.models import OIDDefinition
from radp.infrastructure.persistence.models.oid import OIDRecord


class OIDRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get(self, oid: str) -> OIDDefinition | None:
        with self.session_factory() as session:
            record = session.scalar(
                select(OIDRecord).where(OIDRecord.oid == oid)
            )
            return self._to_domain(record) if record else None

    def exists(self, oid: str) -> bool:
        with self.session_factory() as session:
            return (
                session.scalar(
                    select(OIDRecord.oid).where(OIDRecord.oid == oid)
                )
                is not None
            )

    def all(self) -> list[OIDDefinition]:
        with self.session_factory() as session:
            records = session.scalars(
                select(OIDRecord).order_by(OIDRecord.oid)
            )
            return [self._to_domain(record) for record in records]

    def save(self, definition: OIDDefinition) -> None:
        now = datetime.now(timezone.utc)
        with self.session_factory() as session:
            record = session.get(OIDRecord, definition.oid)
            if record is None:
                record = OIDRecord(oid=definition.oid, created_at=now)
                session.add(record)
            record.name = definition.name
            record.short_name = definition.short_name
            record.category = definition.category
            record.description = definition.description
            record.enabled = definition.enabled
            record.updated_at = now
            session.commit()

    def delete(self, oid: str) -> None:
        with self.session_factory() as session:
            record = session.get(OIDRecord, oid)
            if record:
                session.delete(record)
                session.commit()

    @staticmethod
    def _to_domain(record: OIDRecord) -> OIDDefinition:
        return OIDDefinition(
            oid=record.oid,
            name=record.name,
            short_name=record.short_name,
            category=record.category,
            description=record.description,
            enabled=record.enabled,
        )
