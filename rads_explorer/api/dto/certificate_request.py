from datetime import datetime
from uuid import UUID

from pydantic import Field

from .base import DTOModel
from .extension import Extension
from .name_attributes import NameAttributes


class CertificateRequest(DTOModel):
    id: UUID
    name_attributes: NameAttributes = Field(validation_alias="nameAttributes")

    created_when: datetime = Field(validation_alias="createdWhen")
    resolved_when: datetime | None = Field(
        None, validation_alias="resolvedWhen"
    )
    auth_replied_when: datetime | None = Field(
        None, validation_alias="authRepliedWhen"
    )

    status: str

    user_id: UUID | None = Field(None, validation_alias="userId")
    subject: str | None = None

    creator_id: UUID | None = Field(None, validation_alias="creatorId")
    creator_name: str | None = Field(None, validation_alias="creatorName")
    creator_login: str | None = Field(None, validation_alias="creatorLogin")

    resolver_id: UUID | None = Field(None, validation_alias="resolverId")
    resolver_name: str | None = Field(None, validation_alias="resolverName")
    resolver_login: str | None = Field(None, validation_alias="resolverLogin")

    version: int = 1

    public_key: str | None = Field(None, validation_alias="publicKey")
    public_key_parameters: str | None = Field(
        None, validation_alias="publicKeyParameters"
    )
    public_key_oid: str | None = Field(None, validation_alias="publicKeyOid")
    public_key_oid_description: str | None = Field(
        None, validation_alias="publicKeyOidDescription"
    )

    signature: str | None = None
    signature_oid: str | None = Field(None, validation_alias="signatureOid")
    signature_oid_description: str | None = Field(
        None, validation_alias="signatureOidDescription"
    )

    template_oid: str | None = Field(None, validation_alias="templateOid")
    template_name: str | None = Field(None, validation_alias="templateName")
    template_display_name: str | None = Field(
        None, validation_alias="templateDisplayName"
    )

    extensions: list[Extension] | None = None

    raw_request: bytes | None = Field(None, validation_alias="rawRequest")

    folder: str | None = None

    certificate_id: UUID | None = Field(None, validation_alias="certificateId")
