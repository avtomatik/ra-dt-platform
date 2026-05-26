from cryptography.x509 import ObjectIdentifier
from cryptography.x509.oid import NameOID

from rads_explorer.api.schemas.certificate import CertificateDetail
from rads_explorer.api.schemas.oids import OID
from rads_explorer.data.reports_models import CertificateDetailReportRow


class CertificateDetailMapper:
    def __init__(self, inspector):
        self.inspector = inspector

    def map(
        self, certificate: CertificateDetail
    ) -> CertificateDetailReportRow:
        cert_x509 = certificate.x509

        return CertificateDetailReportRow(
            ogrn=self.inspector.subject(cert_x509, NameOID.OGRN),
            organization_name=self.inspector.subject(
                cert_x509, NameOID.ORGANIZATION_NAME
            ),
            guid=self.inspector.subject(cert_x509, ObjectIdentifier(OID.GUID)),
            surname=self.inspector.subject(cert_x509, NameOID.SURNAME),
            given_name=self.inspector.subject(cert_x509, NameOID.GIVEN_NAME),
            organizational_unit_name=self.inspector.subject(
                cert_x509, NameOID.ORGANIZATIONAL_UNIT_NAME
            ),
            title=self.inspector.subject(cert_x509, NameOID.TITLE),
            common_name=self.inspector.subject(cert_x509, NameOID.COMMON_NAME),
            serial_number=certificate.serial_number,
            snils=self.inspector.subject(cert_x509, NameOID.SNILS),
            status=certificate.status,
            certificate_template=self.inspector.certificate_template_oid(
                cert_x509
            ),
            revoked_when=certificate.revoked_when,
            not_before=cert_x509.not_valid_before_utc,
            not_after=cert_x509.not_valid_after_utc,
        )
