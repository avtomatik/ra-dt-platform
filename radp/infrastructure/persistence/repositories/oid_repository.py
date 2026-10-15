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

    def upsert_missing(self, definition: OIDDefinition) -> bool:
        """Insert a definition or fill only metadata absent from an existing row.
        The database may contain curated/enriched values that are newer than the
        seed fixture. Bootstrap must never replace those values with stale or
        empty fixture fields.
        """
        values = {
            "oid": definition.oid,
            "name": definition.name,
            "short_name": definition.short_name,
            "category": definition.category,
            "description": definition.description,
            "enabled": definition.enabled,
        }
        with self._engine.begin() as connection:
            existing = (
                connection.execute(
                    select(
                        OIDRecord.oid,
                        OIDRecord.name,
                        OIDRecord.short_name,
                        OIDRecord.category,
                        OIDRecord.description,
                    ).where(OIDRecord.oid == definition.oid)
                )
                .mappings()
                .one_or_none()
            )
            if existing is None:
                connection.execute(
                    OIDRecord.__table__.insert().values(
                        **values,
                        created_at=func.current_timestamp(),
                        updated_at=func.current_timestamp(),
                    )
                )
                return True
            missing_values = {
                field: value
                for field, value in values.items()
                if field != "oid"
                and field != "enabled"
                and existing[field] is None
                and value is not None
            }
            if not missing_values:
                return False
            connection.execute(
                OIDRecord.__table__.update()
                .where(OIDRecord.oid == definition.oid)
                .values(**missing_values, updated_at=func.current_timestamp())
            )
            return True

    def ensure(self, oid: str) -> OIDDefinition:
        """Return an OID row, registering unknown OIDs with empty metadata."""
        definition = self.get(oid)
        if definition is not None:
            return definition
        with self._engine.begin() as connection:
            # ON CONFLICT makes concurrent certificate ingestion idempotent.
            from sqlalchemy.dialects.postgresql import insert as pg_insert

            statement = (
                pg_insert(OIDRecord.__table__)
                .values(
                    oid=oid,
                    enabled=True,
                    created_at=func.current_timestamp(),
                    updated_at=func.current_timestamp(),
                )
                .on_conflict_do_nothing(index_elements=[OIDRecord.oid])
            )
            connection.execute(statement)
        definition = self.get(oid)
        if (
            definition is None
        ):  # Defensive: the insert/select should be atomic enough.
            raise RuntimeError(
                f"Failed to ensure OID registry entry for {oid}"
            )
        return definition

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
