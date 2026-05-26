from typing import Protocol

from rads_explorer.infrastructure.transport.response import HTTPResponse


class BaseTransport(Protocol):

    def request(
        self,
        method: str,
        path: str,
        params=None,
        json_data=None,
        headers=None,
    ) -> HTTPResponse: ...

    def get(
        self,
        path: str,
        params=None,
        headers=None,
    ) -> HTTPResponse: ...
