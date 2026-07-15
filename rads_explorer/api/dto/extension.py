from pydantic import Field

from .base import DTOModel


class Extension(DTOModel):
    oid: str
    oid_description: str | None = Field(
        None, validation_alias="oidDescription"
    )
    value: str
