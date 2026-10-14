from dataclasses import dataclass
from pathlib import Path

from radp.application.ports.certificate_query import CertificateQueryPort
from radp.application.ports.database_inspection import DatabaseInspectionPort
from radp.application.ports.oid_repository import OIDRepositoryPort
from radp.config.settings import Settings
from radp.infrastructure.ra_api.client import RAClient
from radp.infrastructure.transport.curl import CurlTransport


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    message: str


class DoctorService:
    EXPECTED_TABLES = {"certificates", "oid_registry"}

    def __init__(
        self,
        settings: Settings,
        database: DatabaseInspectionPort,
        oids: OIDRepositoryPort,
        certificates: CertificateQueryPort,
        client: RAClient,
        runtime_ready: bool,
    ) -> None:
        self.settings = settings
        self.database = database
        self.oids = oids
        self.certificates = certificates
        self.client = client
        self.runtime_ready = runtime_ready

    async def run(self) -> list[CheckResult]:
        checks: list[CheckResult] = []
        checks.append(CheckResult("configuration", True, "settings loaded"))
        checks.append(self._check_database())
        checks.append(
            CheckResult(
                "oid registry", True, f"{self.oids.count()} definitions"
            )
        )
        checks.append(
            CheckResult(
                "certificates", True, f"{self.certificates.count()} records"
            )
        )
        checks.append(self._check_transport())
        checks.append(await self._check_ra())
        checks.append(
            CheckResult(
                "runtime",
                self.runtime_ready,
                (
                    "dependencies initialized"
                    if self.runtime_ready
                    else "not ready"
                ),
            )
        )
        return checks

    def _check_database(self) -> CheckResult:
        try:
            self.database.ping()
            tables = set(self.database.list_tables())
            missing = sorted(self.EXPECTED_TABLES - tables)
            if missing:
                return CheckResult(
                    "database", False, f"missing tables: {', '.join(missing)}"
                )
            return CheckResult(
                "database",
                True,
                f"connected; tables={', '.join(sorted(tables))}",
            )
        except Exception as exc:
            return CheckResult("database", False, str(exc))

    def _check_transport(self) -> CheckResult:
        try:
            mode = self.settings.transport.mode.value
            if isinstance(self.client.transport, CurlTransport):
                curl_path = Path(self.settings.transport.curl_path)
                if not curl_path.is_file():
                    return CheckResult(
                        "transport",
                        False,
                        f"curl executable not found: {curl_path}",
                    )
            return CheckResult("transport", True, f"{mode} transport ready")
        except Exception as exc:
            return CheckResult("transport", False, str(exc))

    async def _check_ra(self) -> CheckResult:
        try:
            page = await self.client.list_first_page()
            return CheckResult(
                "RA API",
                True,
                f"reachable; GET /certificates returned {len(page.items)} items",
            )
        except Exception as exc:
            return CheckResult("RA API", False, str(exc))
