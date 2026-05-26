import requests

from rads_explorer.infrastructure.transport.response import HTTPResponse


class HTTPTransport:
    def __init__(self, settings):
        self.settings = settings

    def request(self, method, path, params=None, json_data=None, headers=None):
        url = self.build_url(path)

        response = requests.request(
            method,
            url,
            params=params,
            json=json_data,
            headers=headers,
            timeout=self.settings.timeout,
        )

        try:
            data = response.json()
        except ValueError:
            data = None

        return HTTPResponse(
            status_code=response.status_code,
            headers=response.headers,
            body=response.text,
            json_data=data,
        )

    def get(self, path, params=None, headers=None):
        return self.request(
            "GET",
            path,
            params=params,
            headers=headers,
        )

    def build_url(self, path):
        return (
            str(self.settings.api_base_url).rstrip("/")
            + "/"
            + path.lstrip("/")
        )
