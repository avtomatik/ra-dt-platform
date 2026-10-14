from radp.domain.models.certificate import Certificate
from radp.domain.oid import constants

from .models import CertificateInventoryRow


class CertificateProjection:
    @staticmethod
    def inventory(certificate: Certificate) -> CertificateInventoryRow:
        subject = certificate.subject_by_oid
        extensions = certificate.extension_by_oid
        return CertificateInventoryRow(
            ogrn=subject.get(constants.OGRN),
            organization_name=subject.get(constants.O),
            guid=subject.get(constants.GUID),
            surname=subject.get(constants.SN),
            given_name=subject.get(constants.GIVEN_NAME),
            organizational_unit_name=subject.get(constants.OU),
            title=subject.get(constants.T),
            common_name=subject.get(constants.CN),
            serial_number=certificate.metadata.serial_number,
            snils=subject.get(constants.SNILS),
            status=certificate.lifecycle.status,
            certificate_template=extensions.get(
                constants.CERTIFICATE_TEMPLATE
            ),
            revoked_when=certificate.lifecycle.revoked_when,
            not_before=certificate.metadata.not_before,
            not_after=certificate.metadata.not_after,
        )
