import json
from pathlib import Path

from radp.application.ports.oid_repository import OIDRepositoryPort
from radp.config.paths import OID_REGISTRY_FIXTURE_PATH
from radp.domain.oid.models import OIDDefinition


class OIDRegistryLoader:
    def load(self, fixture_path: Path) -> list[OIDDefinition]:
        if not fixture_path.is_file():
            raise FileNotFoundError(
                f"OID registry fixture does not exist: {fixture_path}"
            )
        with fixture_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, list):
            raise ValueError("OID registry fixture must contain a JSON array")
        return [OIDDefinition.model_validate(item) for item in payload]


class OIDRegistryInitializer:
    def __init__(
        self,
        repository: OIDRepositoryPort,
        loader: OIDRegistryLoader | None = None,
    ) -> None:
        self.repository = repository
        self.loader = loader or OIDRegistryLoader()

    def initialize(self, fixture_path: Path | None = None) -> int:
        path = fixture_path or OID_REGISTRY_FIXTURE_PATH
        definitions = self.loader.load(path)
        changed = 0
        for definition in definitions:
            if self.repository.upsert_missing(definition):
                changed += 1
        return changed
