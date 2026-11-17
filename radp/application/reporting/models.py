from datetime import date, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .enums import CertificateClassification, CertificateReportStatus


class CertificateInventoryRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    ogrn: str | None
    organization_name: str | None
    gid: str | None
    surname: str | None
    given_name: str | None
    organizational_unit_name: str | None
    title: str | None
    common_name: str | None
    serial_number: str
    snils: str | None
    status: str
    certificate_template: str | None
    revoked_when: datetime | None
    not_before: datetime
    not_after: datetime
    # Classification is available to reporting post-processing without changing
    # the existing inventory workbook column contract.
    classification: CertificateClassification = Field(
        default=CertificateClassification.KEY_CARRIER, exclude=True
    )


REPORT_COLUMNS = tuple(
    name
    for name, field in CertificateInventoryRow.model_fields.items()
    if not field.exclude
)


class CertificateReportFilters(BaseModel):
    status: CertificateReportStatus = CertificateReportStatus.ALL
    gid: str | None = None
    as_of_date: date | None = None

    @field_validator("gid")
    @classmethod
    def normalize_gid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("GID must not be empty when supplied.")
        return normalized

    def valid_at_utc(self) -> datetime:
        """Return the inclusive UTC validity cutoff for VALID report queries."""
        from datetime import time, timezone

        effective_date = self.as_of_date or datetime.now(timezone.utc).date()
        return datetime.combine(effective_date, time.min, tzinfo=timezone.utc)


class ReportArtifact(BaseModel):
    name: str
    generated_at: datetime
    path: Path
