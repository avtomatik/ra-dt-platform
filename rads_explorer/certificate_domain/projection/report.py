from rads_explorer.certificate_domain.constants.oids import OID
from rads_explorer.certificate_domain.snapshot.certificate_snapshot import \
    CertificateSnapshot
from rads_explorer.data.reports_models import CertificateDetailReportRow


class ReportProjection:
    @staticmethod
    def to_detail_row(
        snapshot: CertificateSnapshot,
    ) -> CertificateDetailReportRow:
        return CertificateDetailReportRow(
            ogrn=snapshot.subject_by_oid.get(OID.OGRN),
            organization_name=snapshot.subject_by_oid.get(OID.O),
            guid=snapshot.subject_by_oid.get(OID.GUID),
            surname=snapshot.subject_by_oid.get(OID.SN),
            given_name=snapshot.subject_by_oid.get(OID.GIVEN_NAME),
            organizational_unit_name=snapshot.subject_by_oid.get(OID.OU),
            title=snapshot.subject_by_oid.get(OID.T),
            common_name=snapshot.subject_by_oid.get(OID.CN),
            serial_number=snapshot.serial_number,
            snils=snapshot.subject_by_oid.get(OID.SNILS),
            status=snapshot.status,
            certificate_template=snapshot.extension_by_oid.get(
                OID.CERTIFICATE_TEMPLATE
            ),
            revoked_when=snapshot.lifecycle.revoked_when,
            not_before=snapshot.validity.not_before,
            not_after=snapshot.validity.not_after,
        )
