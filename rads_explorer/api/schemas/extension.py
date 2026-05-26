from pydantic import Field

from .base import APIModel


class Extension(APIModel):
    oid: str
    oid_description: str | None = Field(
        None, validation_alias="oidDescription"
    )
    value: str
