from .attribute import DistinguishedNameAttribute
from .base import DomainModel


class DistinguishedName(DomainModel):
    rfc4514: str
    attributes: list[DistinguishedNameAttribute]
