from datetime import datetime
from uuid import UUID

from .base import DomainModel
from .name_attributes import NameAttributes


class User(DomainModel):
    id: UUID
    name_attributes: NameAttributes

    created_when: datetime

    creator_id: UUID | None = None
    creator_name: str | None = None
    creator_login: str | None = None

    distinguished_name: str | None = None

    folder: str | None = None
