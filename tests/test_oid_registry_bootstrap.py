import json

from radp.bootstrap.oid_registry import (OIDRegistryInitializer,
                                         OIDRegistryLoader)
from radp.domain.oid.models import OIDDefinition


class FakeOIDRepository:
    def __init__(self):
        self.records = {}

    def upsert_missing(self, definition: OIDDefinition) -> bool:
        existing = self.records.get(definition.oid)
        if existing is None:
            self.records[definition.oid] = definition
            return True
        changed = False
        values = existing.model_dump()
        incoming = definition.model_dump()
        for field in ("name", "short_name", "category", "description"):
            if values.get(field) is None and incoming.get(field) is not None:
                values[field] = incoming[field]
                changed = True
        if changed:
            self.records[definition.oid] = OIDDefinition.model_validate(values)
        return changed


def test_oid_initializer_inserts_new_entries_and_enriches_missing_metadata(
    tmp_path,
):
    fixture = tmp_path / "oid_registry.json"
    fixture.write_text(
        json.dumps(
            [
                {
                    "oid": "1.2.3",
                    "name": "Example OID",
                    "short_name": "example",
                },
                {"oid": "1.2.4", "name": "Second OID"},
            ]
        ),
        encoding="utf-8",
    )
    repository = FakeOIDRepository()
    repository.records["1.2.3"] = OIDDefinition(oid="1.2.3")
    changed = OIDRegistryInitializer(repository).initialize(fixture)
    assert changed == 2
    assert repository.records["1.2.3"].name == "Example OID"
    assert repository.records["1.2.3"].short_name == "example"
    assert repository.records["1.2.4"].name == "Second OID"


def test_oid_loader_fails_loudly_when_seed_fixture_is_missing(tmp_path):
    missing_fixture = tmp_path / "missing.json"
    try:
        OIDRegistryLoader().load(missing_fixture)
    except FileNotFoundError as exc:
        assert str(missing_fixture) in str(exc)
    else:
        raise AssertionError("missing OID seed fixture must fail bootstrap")
