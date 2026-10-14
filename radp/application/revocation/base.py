from typing import Protocol


class RevocationSource(Protocol):
    def revoked_certificates(self): ...
