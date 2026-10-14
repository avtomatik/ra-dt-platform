from sqlalchemy import func, select
from sqlalchemy.engine import Engine

from radp.domain.oid.models import OIDDefinition
from radp.infrastructure.persistence.models.oid import OIDRecord


class OIDRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get(self, oid: str) -> OIDDefinition | None:
        with self._engine.connect() as connection:
            record = (
                connection.execute(
                    select(
                        OIDRecord.oid,
                        OIDRecord.name,
                        OIDRecord.short_name,
                        OIDRecord.category,
                        OIDRecord.description,
                        OIDRecord.enabled,
                    ).where(OIDRecord.oid == oid)
                )
                .mappings()
                .one_or_none()
            )
        return self._to_domain(record) if record else None

    def exists(self, oid: str) -> bool:
        with self._engine.connect() as connection:
            return (
                connection.execute(
                    select(OIDRecord.oid).where(OIDRecord.oid == oid).limit(1)
                ).first()
                is not None
            )

    def all(self) -> list[OIDDefinition]:
        with self._engine.connect() as connection:
            rows = connection.execute(
                select(
                    OIDRecord.oid,
                    OIDRecord.name,
                    OIDRecord.short_name,
                    OIDRecord.category,
                    OIDRecord.description,
                    OIDRecord.enabled,
                ).order_by(OIDRecord.oid.asc())
            ).all()
        return [self._to_domain(row) for row in rows]

    def count(self) -> int:
        from sqlalchemy import func

        with self._engine.connect() as connection:
            return int(
                connection.execute(
                    select(func.count()).select_from(OIDRecord)
                ).scalar_one()
            )

    def save(self, definition: OIDDefinition) -> None:
        values = {
            "oid": definition.oid,
            "name": definition.name,
            "short_name": definition.short_name,
            "category": definition.category,
            "description": definition.description,
            "enabled": definition.enabled,
        }
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(OIDRecord.oid)
                .where(OIDRecord.oid == definition.oid)
                .limit(1)
            ).first()
            if existing is None:
                connection.execute(
                    OIDRecord.__table__.insert().values(
                        **values,
                        created_at=func.current_timestamp(),
                        updated_at=func.current_timestamp(),
                    )
                )
            else:
                connection.execute(
                    OIDRecord.__table__.update()
                    .where(OIDRecord.oid == definition.oid)
                    .values(**values, updated_at=func.current_timestamp())
                )

    def delete(self, oid: str) -> None:
        with self._engine.begin() as connection:
            connection.execute(
                OIDRecord.__table__.delete().where(OIDRecord.oid == oid)
            )

    @staticmethod
    def _to_domain(row) -> OIDDefinition:
        mapping = row._mapping if hasattr(row, "_mapping") else row
        return OIDDefinition(
            oid=mapping["oid"],
            name=mapping["name"],
            short_name=mapping["short_name"],
            category=mapping["category"],
            description=mapping["description"],
            enabled=mapping["enabled"],
        )
