from .base import DomainModel


class DistinguishedNameAttribute(DomainModel):
    oid: str
    short_name: str | None
    name: str | None
    value: str
