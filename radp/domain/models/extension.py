from .base import DomainModel


class Extension(DomainModel):
    oid: str
    short_name: str | None
    name: str | None
    critical: bool
    value: str
