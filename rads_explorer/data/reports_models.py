from dataclasses import dataclass
from datetime import datetime


@dataclass
class CertificateDetailReportRow:
    ogrn: str | None
    organization_name: str | None
    guid: str | None

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
