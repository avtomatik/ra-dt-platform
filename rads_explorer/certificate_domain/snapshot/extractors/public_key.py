from cryptography.x509 import Certificate

from rads_explorer.certificate_domain.snapshot.public_key_snapshot import \
    PublicKeySnapshot


class PublicKeyExtractor:
    def create(self, certificate: Certificate) -> PublicKeySnapshot:
        public_key = certificate.public_key()
        return PublicKeySnapshot(
            algorithm=type(public_key).__name__,
            key_size=getattr(public_key, "key_size", None),
        )
