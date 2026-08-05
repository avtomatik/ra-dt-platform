from typing import Any, Mapping, Protocol

from .response import HTTPResponse


class Transport(Protocol):
    def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
    ) -> HTTPResponse: ...
