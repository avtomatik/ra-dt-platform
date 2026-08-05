from typing import Any, Mapping

import requests
from pydantic_settings import BaseSettings

from .response import HTTPResponse
from .url import build_url


class HTTPTransport:
    def __init__(self, settings: BaseSettings) -> None:
        self.settings = settings

    def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
    ) -> HTTPResponse:
        url = build_url(
            api_base_url=str(self.settings.api_base_url),
            api_root=self.settings.api_root,
            path=path,
            params=params,
        )

        response = requests.get(
            url, params=params, headers=headers, timeout=30
        )

        try:
            parsed = response.json()
        except ValueError:
            parsed = None

        return HTTPResponse(
            status_code=response.status_code,
            headers=response.headers,
            body=response.text,
            json_data=parsed,
        )
