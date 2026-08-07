import asyncio
import json
import logging
import re
from typing import Any, Mapping

from pydantic_settings import BaseSettings

from .exceptions import CurlExecutionError
from .response import HTTPResponse
from .url import build_url

logger = logging.getLogger(__name__)


class CurlTransport:
    TIMEOUT_SECONDS = 30

    def __init__(self, settings: BaseSettings) -> None:
        self.settings = settings

    async def get(
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
        command = [
            str(self.settings.curl_path),
            "-s",
            "-S",
            "-i",
            "-w",
            "\nHTTP_STATUS:%{http_code}",
            "-X",
            "GET",
            "--cert",
            self.settings.cert_thumbprint,
            "-k",
            url,
        ]

        if headers:
            for key, value in headers.items():
                command.extend(["-H", f"{key}: {value}"])

        masked = command.copy()
        idx = masked.index("--cert")
        masked[idx + 1] = "***"
        logger.info("CURL COMMAND: %s", " ".join(masked))
        logger.info("Executing curl request %s", url)

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError as exc:
                process.kill()
                await process.wait()
                raise CurlExecutionError(
                    f"curl request timeout after "
                    f"{self.TIMEOUT_SECONDS} seconds"
                ) from exc
        except OSError as exc:
            raise CurlExecutionError(f"cannot execute curl: {exc}") from exc
        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")
        if process.returncode != 0:
            raise CurlExecutionError(
                f"curl exited with code {process.returncode}\n"
                f"STDOUT:\n{stdout_text}\n"
                f"STDERR:\n{stderr_text}"
            )
        return self._parse_response(stdout_text)

    def _parse_response(self, raw: str) -> HTTPResponse:
        response_raw, status_raw = self._split_status(raw)
        try:
            status_code = int(status_raw.strip())
        except ValueError as exc:
            raise CurlExecutionError(
                f"Invalid HTTP status code: {status_raw!r}"
            ) from exc
        headers_block, body = self._split_response(response_raw)
        parsed_json = None
        if body:
            try:
                parsed_json = json.loads(body)
            except json.JSONDecodeError:
                logger.info(
                    "Response body is not JSON for HTTP status %s", status_code
                )
        return HTTPResponse(
            status_code=status_code,
            headers=self._parse_headers(headers_block),
            body=body,
            json_data=parsed_json,
        )

    @classmethod
    def _split_response(cls, raw: str) -> tuple[str, str]:
        matches = list(re.finditer(r"(?m)^HTTP/\d(?:\.\d)?\s+\d{3}\b", raw))
        if not matches:
            raise CurlExecutionError(
                "Cannot find HTTP response headers in curl output"
            )
        response_start = matches[-1].start()
        header_start = response_start
        separator_match = re.search(r"\r?\n\r?\n", raw[response_start:])
        if separator_match is None:
            raise CurlExecutionError("Missing HTTP header/body separator")
        separator_start = response_start + separator_match.start()
        body_start = response_start + separator_match.end()
        headers = raw[header_start:separator_start]
        body = raw[body_start:]
        return headers, body

    @staticmethod
    def _parse_headers(block: str) -> dict[str, str]:
        headers: dict[str, str] = {}
        for line in block.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()
        return headers

    @staticmethod
    def _split_status(raw: str) -> tuple[str, str]:
        marker = "HTTP_STATUS:"
        try:
            response_raw, status_raw = raw.rsplit(marker, 1)
        except ValueError as exc:
            raise CurlExecutionError(
                "Cannot find curl HTTP status marker"
            ) from exc
        return response_raw, status_raw
