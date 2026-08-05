import json
import subprocess
from typing import Any, Mapping

from pydantic_settings import BaseSettings

from .exceptions import CurlExecutionError
from .response import HTTPResponse
from .url import build_url


class CurlTransport:
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

        cmd = [
            str(self.settings.curl_path),
            "-s",
            "-i",
            "-w",
            "\nHTTP_STATUS:%{http_code}",
            "-X",
            "GET",
            "--cert",
            self.settings.cert_thumbprint,
            url,
        ]

        cmd.append("-k")

        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])

        masked = cmd.copy()
        idx = masked.index("--cert")
        masked[idx + 1] = "***"
        print("\nCURL COMMAND:")
        print(" ".join(masked))

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30, check=False
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
