from hashlib import sha256

from cryptography.x509 import load_der_x509_certificate

from rads_explorer.certificate_domain.crypto.decoder import CertificateDecoder
from rads_explorer.certificate_domain.models.certificate import Certificate
from rads_explorer.certificate_domain.snapshot.extractors.extensions import \
    ExtensionExtractor
from rads_explorer.certificate_domain.snapshot.extractors.issuer import \
    IssuerExtractor
from rads_explorer.certificate_domain.snapshot.extractors.public_key import \
    PublicKeyExtractor
from rads_explorer.certificate_domain.snapshot.extractors.signature import \
    SignatureExtractor
from rads_explorer.certificate_domain.snapshot.extractors.subject import \
    SubjectExtractor

from .certificate_snapshot import CertificateSnapshot
from .lifecycle_snapshot import LifecycleSnapshot
from .validity_snapshot import ValiditySnapshot


class CertificateSnapshotFactory:
    def __init__(self):
        self._extensions = ExtensionExtractor()
        self._issuer = IssuerExtractor()
        self._public_key = PublicKeyExtractor()
        self._signature = SignatureExtractor()
        self._subject = SubjectExtractor()

    def create(self, certificate: Certificate) -> CertificateSnapshot:
        der = CertificateDecoder.decode(certificate.raw_certificate)
        x509 = load_der_x509_certificate(der)
        return CertificateSnapshot(
            certificate_id=certificate.id,
            serial_number=certificate.serial_number,
            version=x509.version.value,
            fingerprint_sha256=sha256(der).hexdigest(),
            subject=x509.subject.rfc4514_string(),
            issuer=x509.issuer.rfc4514_string(),
            subject_attributes=self._subject.create(x509),
            issuer_attributes=self._issuer.create(x509),
            extensions=self._extensions.create(x509),
            public_key=self._public_key.create(x509),
            signature=self._signature.create(x509),
            validity=ValiditySnapshot(
                not_before=x509.not_valid_before_utc,
                not_after=x509.not_valid_after_utc,
            ),
            lifecycle=LifecycleSnapshot(
                created_when=certificate.created_when,
                key_not_after=certificate.key_not_after,
                revoked_when=certificate.revoked_when,
            ),
            status=certificate.status,
        )
