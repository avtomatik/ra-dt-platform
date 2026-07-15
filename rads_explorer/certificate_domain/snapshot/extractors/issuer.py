from cryptography.x509 import Certificate

from rads_explorer.certificate_domain.snapshot.subject_attribute import \
    CertificateAttribute


class IssuerExtractor:
    def create(self, certificate: Certificate) -> list[CertificateAttribute]:
        return [
            CertificateAttribute(
                oid=attribute.oid.dotted_string,
                name=getattr(attribute.oid, "_name", None),
                value=str(attribute.value),
            )
            for attribute in certificate.issuer
        ]
