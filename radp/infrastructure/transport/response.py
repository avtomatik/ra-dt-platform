from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(slots=True)
class HTTPResponse:
    status_code: int
    headers: Mapping[str, Any]
    body: str
    json_data: Any | None

    def json(self) -> Mapping[str, Any]:
        return self.json_data

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def content_type(self) -> str | None:
        for key, value in self.headers.items():
            if key.lower() == "content-type":
                return value

        return None
