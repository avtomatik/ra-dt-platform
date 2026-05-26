from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class HTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: str
    json_data: Any | None

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @property
    def content_type(self) -> str | None:
        for key, value in self.headers.items():
            if key.lower() == "content-type":
                return value

        return None
