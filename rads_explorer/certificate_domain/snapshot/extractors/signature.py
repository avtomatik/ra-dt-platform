from cryptography.x509 import Certificate

from rads_explorer.certificate_domain.snapshot.signature_snapshot import \
    SignatureSnapshot


class SignatureExtractor:
    def create(self, certificate: Certificate) -> SignatureSnapshot:
        return SignatureSnapshot(
            oid=certificate.signature_algorithm_oid.dotted_string,
            algorithm=certificate.signature_algorithm_oid._name,
        )
