import json
import subprocess
from typing import Any, Mapping
from urllib.parse import urlencode

from rads_explorer.config.settings import Settings
from rads_explorer.infrastructure.transport.exceptions import \
    CurlExecutionError
from rads_explorer.infrastructure.transport.response import HTTPResponse


class CryptoProCurlTransport:
    def __init__(self, settings: Settings):
        self.settings = settings

    def request(
        self,
        method: str,
        path: str,
        params: Mapping[str, Any] | None = None,
        json_data: Mapping[str, Any] | None = None,
        headers: Mapping[str, Any] | None = None,
    ) -> HTTPResponse:

        url = self.build_url(path, params)

        cmd = [
            str(self.settings.curl_path),
            "-s",
            "-i",
            "-w",
            "\nHTTP_STATUS:%{http_code}",
            "-X",
            method.upper(),
            "--cert",
            self.settings.cert_thumbprint,
            url,
        ]

        if not self.settings.verify_tls:
            cmd.append("-k")

        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])

        if json_data is not None:
            cmd.extend(
                [
                    "-H",
                    "Content-Type: application/json",
                    "-d",
                    json.dumps(json_data),
                ]
            )

        if self.settings.debug_http:
            masked = cmd.copy()
            idx = masked.index("--cert")
            masked[idx + 1] = "***"
            print("\nCURL COMMAND:")
            print(" ".join(masked))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.settings.timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise CurlExecutionError("curl request timeout") from exc

        if result.returncode != 0:
            raise CurlExecutionError(
                f"curl exited with code {result.returncode}\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        raw = result.stdout

        try:
            response_raw, status_raw = raw.rsplit("HTTP_STATUS:", 1)
        except ValueError as exc:
            raise CurlExecutionError("Cannot parse curl response") from exc

        status_code = int(status_raw.strip())

        headers_block, body = self._split_response(response_raw)

        parsed_json = None

        if body:
            try:
                parsed_json = json.loads(body)
            except json.JSONDecodeError:
                pass

        return HTTPResponse(
            status_code=status_code,
            headers=self._parse_headers(headers_block),
            body=body,
            json_data=parsed_json,
        )

    def get(self, path, params=None, headers=None) -> HTTPResponse:
        return self.request(
            method="GET", path=path, params=params, headers=headers
        )

    def build_url(self, path: str, params=None) -> str:
        base = str(self.settings.api_base_url).rstrip("/")
        path = path.lstrip("/")
        url = f"{base}/{path}"

        if params:
            url += "?" + urlencode(params, doseq=True)
        return url

    def _split_response(self, raw: str) -> tuple[str, str]:
        assert raw.startswith(
            "HTTP/1."
        ), "Expected an HTTP response produced by curl -i"

        separator = "\n\n"

        assert separator in raw, "Missing HTTP header separator."

        headers, body = raw.split(separator, 1)

        return headers, body or ""

    def _parse_headers(self, block: str):
        result = {}

        for line in block.splitlines():
            if ":" not in line:
                continue

            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()

        return result
