from typing import Any, Mapping

from radp.config.settings import Settings

from .response import HTTPResponse
from .url import build_url


class HTTPTransport:
    TIMEOUT_SECONDS = 30

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def get(
        self,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
    ) -> HTTPResponse:
        url = build_url(
            api_base_url=str(self.settings.remote_ra.base_url),
            api_root=self.settings.remote_ra.root,
            path=path,
            params=params,
        )
        # Import the optional HTTP transport dependency only when this
        # backend is actually used. CryptoPro curl deployments and CLI help
        # should not need to import httpx2 as a module-level side effect.
        import httpx2

        async with httpx2.AsyncClient(timeout=self.TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers=headers)
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
