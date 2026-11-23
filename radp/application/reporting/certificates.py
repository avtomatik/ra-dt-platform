from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from radp.application.ports.certificate_query import CertificateQueryPort
from radp.config.paths import EXPORTS_DIR

from .models import CertificateReportFilters, ReportArtifact
from .projection import CertificateProjection
from .xlsx import XLSXExporter


class CertificateReportService:
    def __init__(
        self,
        certificates: CertificateQueryPort,
        exporter: XLSXExporter | None = None,
        exports_dir: Path = EXPORTS_DIR,
        projection: CertificateProjection | None = None,
    ) -> None:
        self.certificates = certificates
        self.exporter = exporter or XLSXExporter()
        self.exports_dir = exports_dir
        self.projection = projection or CertificateProjection()

    def export_excel(
        self, filters: CertificateReportFilters | None = None
    ) -> ReportArtifact:
        self.projection.reset_oid_cache()
        generated_at = datetime.now(timezone.utc)
        suffix = uuid4().hex[:10]
        filename = (
            f"certificates_inventory_{generated_at:%Y-%m-%d-%H-%M-%S}-"
            f"{suffix}.xlsx"
        )
        path = self.exports_dir / filename
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        certificates = self.certificates.list_for_report(
            filters or CertificateReportFilters()
        )
        rows = [
            self.projection.select(self.projection.inventory(certificate))
            for certificate in certificates
        ]
        self.exporter.export(
            rows,
            path,
            columns=self.projection.columns,
            sheet_name="certificates_inventory",
        )
        return ReportArtifact(
            name="certificates_inventory", generated_at=generated_at, path=path
        )

    def project_first(
        self, limit: int = 20, filters: CertificateReportFilters | None = None
    ) -> list[dict]:
        self.projection.reset_oid_cache()
        certificates = self.certificates.list_for_report(
            filters or CertificateReportFilters(), limit=limit
        )
        return [
            self.projection.select(self.projection.inventory(certificate))
            for certificate in certificates
        ]

    @property
    def columns(self) -> tuple[str, ...]:
        return self.projection.columns
