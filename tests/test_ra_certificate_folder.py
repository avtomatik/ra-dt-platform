import asyncio

from radp.infrastructure.ra_api.client import RAClient
from radp.infrastructure.transport.response import HTTPResponse
from radp.infrastructure.transport.url import build_url


class FakeTransport:
    def __init__(self):
        self.calls = []

    async def get(self, path, *, params=None, headers=None):
        self.calls.append((path, params, headers))
        return HTTPResponse(
            status_code=200,
            headers={"content-type": "application/json"},
            body='{"items": []}',
            json_data={"items": []},
        )


def test_collection_endpoint_receives_configured_folder():
    transport = FakeTransport()
    client = RAClient(transport, certificate_folder="production folder/2026")

    page = asyncio.run(client.list_first_page())

    assert page.items == []
    assert transport.calls == [
        ("certificates", {"folder": "production folder/2026"}, None)
    ]


def test_search_endpoint_receives_configured_folder():
    transport = FakeTransport()
    client = RAClient(transport, certificate_folder="production-folder")

    asyncio.run(client.search_certificates("Alice"))

    assert transport.calls == [
        (
            "certificates",
            {"folder": "production-folder", client.search_parameter: "Alice"},
            None,
        )
    ]


def test_folder_is_url_encoded_as_query_parameter():
    url = build_url(
        "https://example.test/api/ra/",
        "/api/ra",
        "certificates",
        params={"folder": "production folder/2026"},
    )

    assert url == (
        "https://example.test/api/ra/certificates?"
        "folder=production+folder%2F2026"
    )
