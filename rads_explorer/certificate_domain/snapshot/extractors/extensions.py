from cryptography.x509 import Certificate

from rads_explorer.certificate_domain.snapshot.extension_snapshot import \
    CertificateExtension


class ExtensionExtractor:
    def create(self, certificate: Certificate) -> list[CertificateExtension]:
        return [
            CertificateExtension(
                oid=extension.oid.dotted_string,
                name=extension.oid._name,
                critical=extension.critical,
                value=str(extension.value),
            )
            for extension in certificate.extensions
        ]
