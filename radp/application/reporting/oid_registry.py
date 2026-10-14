import json
import tempfile
from pathlib import Path

from radp.application.ports.oid_repository import OIDRepositoryPort


class OIDRegistryExporter:
    def __init__(self, repository: OIDRepositoryPort) -> None:
        self.repository = repository

    def export(self, target: Path) -> int:
        definitions = [
            item.model_dump(mode="json") for item in self.repository.all()
        ]
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(
                definitions, indent=2, ensure_ascii=False, sort_keys=False
            )
            + "\n"
        )
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
        temporary_path.replace(target)
        return len(definitions)
