from .base import DomainModel


class Extension(DomainModel):
    oid: str
    short_name: str | None
    name: str | None
    critical: bool
    value: str
    # Populated for Microsoft Certificate Template Information extensions.
    # Defaults preserve compatibility with certificate JSONB payloads stored
    # before these fields were introduced.
    template_oid: str | None = None
    template_name: str | None = None
