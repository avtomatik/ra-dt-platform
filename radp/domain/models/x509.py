from datetime import datetime

from .base import SnapshotModel
from .extension import ExtensionSnapshot
from .name import DistinguishedName
from .public_key import PublicKeySnapshot


class X509Snapshot(SnapshotModel):
    version: int
    serial_number: int
    serial_number_hex: str
    issuer: DistinguishedName
    subject: DistinguishedName
    not_valid_before: datetime
    not_valid_after: datetime
    signature_algorithm_oid: str
    signature_algorithm_name: str | None
    public_key: PublicKeySnapshot
    extensions: list[ExtensionSnapshot]
    signature_hex: str
    tbs_certificate_bytes_hex: str
    der_hex: str
