import pytest

from radp.infrastructure.persistence.database import Database


def test_database_inspection_rejects_unknown_table(monkeypatch):
    database = Database.__new__(Database)
    monkeypatch.setattr(Database, "list_tables", lambda self: ["certificates"])
    with pytest.raises(ValueError, match="Unknown table"):
        database._load_table("does_not_exist")
