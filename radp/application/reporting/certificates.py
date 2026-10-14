from datetime import datetime, timezone
from pathlib import Path

from radp.application.ports.certificate_query import CertificateQueryPort
from radp.config.paths import EXPORTS_DIR

from .models import CertificateInventoryRow, ReportArtifact
from .projection import CertificateProjection
from .xlsx import XLSXExporter


class CertificateReportService:
    def __init__(
        self,
        certificates: CertificateQueryPort,
        exporter: XLSXExporter | None = None,
        exports_dir: Path = EXPORTS_DIR,
    ) -> None:
        self.certificates = certificates
        self.exporter = exporter or XLSXExporter()
        self.exports_dir = exports_dir

    def export_excel(self) -> ReportArtifact:
        generated_at = datetime.now(timezone.utc)
        filename = f"certificates_inventory_{generated_at:%Y-%m-%d-%H-%M}.xlsx"
        path = self.exports_dir / filename
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        certificates = self.certificates.list_all()
        rows = [
            CertificateProjection.inventory(certificate)
            for certificate in certificates
        ]
        self.exporter.export(rows, path, sheet_name="certificates_inventory")
        return ReportArtifact(
            name="certificates_inventory", generated_at=generated_at, path=path
        )

    def project_first(self, limit: int = 20) -> list[CertificateInventoryRow]:
        certificates = self.certificates.list_first(limit)
        return [
            CertificateProjection.inventory(certificate)
            for certificate in certificates
        ]
