from radp.domain.models.certificate import CertificateSnapshot
from radp.domain.oid import constants

from .models import CertificateInventoryRow


class CertificateProjection:
    @staticmethod
    def inventory(snapshot: CertificateSnapshot) -> CertificateInventoryRow:
        subject = snapshot.subject_by_oid
        extensions = snapshot.extension_by_oid
        return CertificateInventoryRow(
            ogrn=subject.get(constants.OGRN),
            organization_name=subject.get(constants.O),
            guid=subject.get(constants.GUID),
            surname=subject.get(constants.SN),
            given_name=subject.get(constants.GIVEN_NAME),
            organizational_unit_name=subject.get(constants.OU),
            title=subject.get(constants.T),
            common_name=subject.get(constants.CN),
            serial_number=snapshot.metadata.serial_number,
            snils=subject.get(constants.SNILS),
            status=snapshot.metadata.status,
            certificate_template=extensions.get(
                constants.CERTIFICATE_TEMPLATE
            ),
            revoked_when=snapshot.metadata.revoked_when,
            not_before=snapshot.metadata.not_before,
            not_after=snapshot.metadata.not_after,
        )
