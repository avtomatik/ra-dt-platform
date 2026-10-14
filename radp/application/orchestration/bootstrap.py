from pathlib import Path

from radp.application.ports.oid_repository import OIDRepositoryPort
from radp.bootstrap.oid_registry import OIDRegistryInitializer


class BootstrapOrchestrator:
    def __init__(
        self, oid_repository: OIDRepositoryPort, oid_fixture_path: Path
    ) -> None:
        self._oid_repository = oid_repository
        self._oid_fixture_path = oid_fixture_path

    def initialize(self) -> int:
        return OIDRegistryInitializer(self._oid_repository).initialize(
            self._oid_fixture_path
        )
