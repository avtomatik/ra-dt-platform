from datetime import datetime
from typing import Any
from uuid import UUID

from .base import DomainModel


class CertificateMetadata(DomainModel):
    id: UUID
    serial_number: str
    thumbprint: str
    created_when: datetime
    not_before: datetime
    not_after: datetime
    key_not_after: datetime
    cert_request_id: str | None
    user_id: UUID | None
    folder: str | None
    raw_name_attributes: dict[str, Any]
