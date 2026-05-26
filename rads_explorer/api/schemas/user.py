from datetime import datetime

from pydantic import Field

from .base import APIModel
from .name_attributes import NameAttributes


class User(APIModel):
    id: str
    name_attributes: NameAttributes = Field(validation_alias="nameAttributes")

    created_when: datetime = Field(validation_alias="createdWhen")

    creator_id: str | None = Field(None, validation_alias="creatorId")
    creator_name: str | None = Field(None, validation_alias="creatorName")
    creator_login: str | None = Field(None, validation_alias="creatorLogin")

    distinguished_name: str | None = Field(
        None, validation_alias="distinguishedName"
    )
    folder: str | None = None
