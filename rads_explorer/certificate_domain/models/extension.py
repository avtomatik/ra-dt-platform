from .base import DomainModel


class Extension(DomainModel):
    oid: str
    oid_description: str | None
    value: str
