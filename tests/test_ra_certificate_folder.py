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

    page = asyncio.run(client.list_first_summary_page())

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


def test_summary_status_is_normalized_without_changing_full_list_payload():
    from radp.domain.models.certificate import CertificateStatus

    payload = {
        "items": [
            {
                "id": "019c9f5e-e0a1-4868-b4ba-0df61c30562a",
                "nameAttributes": {"2.5.4.3": "tsp-operator"},
                "serialNumber": "019D72F959835E028A425FE059019C9F5E",
                "thumbprint": "2390EB5C9AE861D2133D7C7990198DC5325C87CA",
                "notBefore": "2026-02-27T16:42:01+03:00",
                "notAfter": "2041-02-27T16:52:01+03:00",
                "keyNotAfter": "2029-02-27T13:52:01+00:00",
                "createdWhen": "2026-02-27T16:52:01.185192+03:00",
                "status": "Valid",
            }
        ]
    }

    class PayloadTransport:
        async def get(self, path, *, params=None, headers=None):
            return HTTPResponse(
                status_code=200,
                headers={"content-type": "application/json"},
                body="{}",
                json_data=payload,
            )

    client = RAClient(PayloadTransport(), certificate_folder="production")
    first_summary_page = asyncio.run(client.list_first_summary_page())

    assert first_summary_page.items[0].status is CertificateStatus.VALID
    assert first_summary_page.items[0].serial_number == (
        "019D72F959835E028A425FE059019C9F5E"
    )
