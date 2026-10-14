from typing import Any

from sqlalchemy import (Engine, MetaData, Table, create_engine, func, inspect,
                        select, text)

from .models.base import Base
from .models.certificates import CertificateRecord
from .models.oid import OIDRecord


class Database:
    """Owns the SQLAlchemy engine, schema lifecycle, and operational inspection."""

    def __init__(self, url: str, *, echo: bool = False) -> None:
        self._engine: Engine = create_engine(
            url, echo=echo, pool_pre_ping=True, future=True
        )

    @property
    def engine(self) -> Engine:
        return self._engine

    def close(self) -> None:
        self._engine.dispose()

    def ping(self) -> bool:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True

    def create(self) -> None:
        Base.metadata.create_all(self._engine)

    def drop(self) -> None:
        Base.metadata.drop_all(self._engine)

    def reset(self) -> None:
        self.drop()
        self.create()

    def list_tables(self) -> list[str]:
        return sorted(inspect(self._engine).get_table_names())

    def row_count(self, table_name: str) -> int:
        table = self._load_table(table_name)
        with self._engine.connect() as connection:
            return int(
                connection.execute(
                    select(func.count()).select_from(table)
                ).scalar_one()
            )

    def first_rows(
        self, table_name: str, limit: int = 20
    ) -> list[dict[str, Any]]:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        table = self._load_table(table_name)
        with self._engine.connect() as connection:
            rows = (
                connection.execute(select(table).limit(limit)).mappings().all()
            )
        return [dict(row) for row in rows]

    def latest_certificates(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(
                        CertificateRecord.id,
                        CertificateRecord.status,
                        CertificateRecord.revoked_when,
                        CertificateRecord.revocation_reason,
                        CertificateRecord.persisted_at,
                    )
                    .order_by(CertificateRecord.persisted_at.desc())
                    .limit(limit)
                )
                .mappings()
                .all()
            )
        return [dict(row) for row in rows]

    def oid_rows(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._engine.connect() as connection:
            rows = (
                connection.execute(
                    select(
                        OIDRecord.oid,
                        OIDRecord.short_name,
                        OIDRecord.name,
                        OIDRecord.category,
                        OIDRecord.enabled,
                        OIDRecord.updated_at,
                    )
                    .order_by(OIDRecord.oid.asc())
                    .limit(limit)
                )
                .mappings()
                .all()
            )
        return [dict(row) for row in rows]

    def _load_table(self, table_name: str) -> Table:
        if table_name not in self.list_tables():
            raise ValueError(f"Unknown table: {table_name}")
        return Table(table_name, MetaData(), autoload_with=self._engine)
