import json

from radp.application.reporting.oid_registry import OIDRegistryExporter
from radp.domain.oid.models import OIDDefinition


class FakeOIDRepository:
    def all(self):
        return [
            OIDDefinition(oid="2.5.4.3", name="commonName"),
            OIDDefinition(oid="1.2.840.113549.1.1.1", name="rsaEncryption"),
        ]


def test_oid_export_is_deterministic(tmp_path):
    target = tmp_path / "oid_registry.json"
    count = OIDRegistryExporter(FakeOIDRepository()).export(target)
    assert count == 2
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload[0]["oid"] == "2.5.4.3"
    assert target.read_text(encoding="utf-8").endswith("\n")
