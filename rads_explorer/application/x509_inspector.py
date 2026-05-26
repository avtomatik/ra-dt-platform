from cryptography import x509
from cryptography.x509 import (AttributeNotFound, ExtensionNotFound,
                               ObjectIdentifier)

from rads_explorer.api.schemas.oids import OID


class X509Inspector:

    @staticmethod
    def subject(cert: x509.Certificate, oid: ObjectIdentifier) -> str | None:
        try:
            attrs = cert.subject.get_attributes_for_oid(oid)

        except AttributeNotFound:
            return None

        return attrs[0].value if attrs else None

    @staticmethod
    def extension(cert: x509.Certificate, oid: ObjectIdentifier):
        try:
            return cert.extensions.get_extension_for_oid(oid)

        except ExtensionNotFound:
            return None

    @staticmethod
    def certificate_template_oid(cert: x509.Certificate) -> str | None:
        ext = X509Inspector.extension(
            cert,
            ObjectIdentifier(OID.CERTIFICATE_TEMPLATE),
        )

        if ext is None:
            return None

        return ext.value.template_id.dotted_string
