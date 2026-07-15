from dataclasses import dataclass
from datetime import datetime, timezone

from rads_explorer.certificate_domain.projection.report import ReportProjection


@dataclass
class Report:
    name: str
    generated_at: datetime
    data: object


class ReportService:
    def __init__(self, certificate_service, snapshot_provider):
        self.certificate_service = certificate_service
        self.snapshot_provider = snapshot_provider

    def _get_mapped_certificates(self, certificates):
        return [
            ReportProjection.to_detail_row(
                self.snapshot_provider.get_or_create(certificate)
            )
            for certificate in certificates
        ]

    def certificates_inventory_report(self):
        return Report(
            name="certificates_inventory",
            generated_at=datetime.now(timezone.utc),
            data=self.build_certificates_inventory(),
        )

    def build_first_page_view(self):
        return self.certificate_service.list_page()

    def build_certificates_inventory(self):
        return self._get_mapped_certificates(
            self.certificate_service.iter_details()
        )
