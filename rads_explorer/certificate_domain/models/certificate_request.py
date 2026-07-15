from datetime import datetime
from uuid import UUID

from .base import DomainModel
from .extension import Extension
from .name_attributes import NameAttributes


class CertificateRequest(DomainModel):
    id: UUID
    name_attributes: NameAttributes

    created_when: datetime
    resolved_when: datetime | None = None
    auth_replied_when: datetime | None = None

    status: str

    user_id: UUID | None = None
    subject: str | None = None

    creator_id: UUID | None = None
    creator_name: str | None = None
    creator_login: str | None = None

    resolver_id: UUID | None = None
    resolver_name: str | None = None
    resolver_login: str | None = None

    version: int = 1

    public_key: str | None = None
    public_key_parameters: str | None = None
    public_key_oid: str | None = None
    public_key_oid_description: str | None = None

    signature: str | None = None
    signature_oid: str | None = None
    signature_oid_description: str | None = None

    template_oid: str | None = None
    template_name: str | None = None
    template_display_name: str | None = None

    extensions: list[Extension] | None = None

    raw_request: bytes | None = None

    folder: str | None = None

    certificate_id: UUID | None = None
