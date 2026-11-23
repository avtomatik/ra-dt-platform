from datetime import datetime, timezone
from uuid import uuid4

import pytest

from radp.application.reporting.enums import CertificateClassification
from radp.application.reporting.models import REPORT_COLUMNS
from radp.application.reporting.projection import CertificateProjection
from radp.domain.models.attribute import DistinguishedNameAttribute
from radp.domain.models.certificate import Certificate, CertificateLifecycle
from radp.domain.models.extension import Extension
from radp.domain.models.metadata import CertificateMetadata
from radp.domain.models.name import DistinguishedName
from radp.domain.models.public_key import PublicKey
from radp.domain.models.x509 import X509Certificate
from radp.domain.oid import OID

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_certificate(*, with_template: bool) -> Certificate:
    certificate_id = uuid4()
    subject = DistinguishedName(
        rfc4514="CN=Test",
        attributes=[
            DistinguishedNameAttribute(
                oid=OID.GUID.value,
                short_name="GUID",
                name="GUID",
                value="gid-123",
            ),
            DistinguishedNameAttribute(
                oid=OID.CN.value,
                short_name="CN",
                name="Common Name",
                value="Test subject",
            ),
        ],
    )
    extensions = []
    if with_template:
        extensions.append(
            Extension(
                oid=OID.CERTIFICATE_TEMPLATE.value,
                short_name="CERTIFICATE_TEMPLATE",
                name="Certificate Template",
                critical=False,
                value="MSCertificateTemplate(...) ",
                template_oid="1.2.3.4",
                template_name="Corporate Signing",
            )
        )
    return Certificate(
        certificate_id=certificate_id,
        metadata=CertificateMetadata(
            id=certificate_id,
            serial_number="01AB",
            thumbprint="a" * 40,
            created_when=NOW,
            not_before=NOW,
            not_after=datetime(2030, 1, 1, tzinfo=timezone.utc),
            key_not_after=datetime(2028, 1, 1, tzinfo=timezone.utc),
            cert_request_id=None,
            user_id=None,
            folder="production",
            raw_name_attributes={},
        ),
        x509=X509Certificate(
            version=3,
            serial_number=123,
            serial_number_hex="0x7b",
            issuer=DistinguishedName(rfc4514="", attributes=[]),
            subject=subject,
            not_valid_before=NOW,
            not_valid_after=datetime(2030, 1, 1, tzinfo=timezone.utc),
            signature_algorithm_oid="1.2.3",
            signature_algorithm_name="test",
            public_key=PublicKey(
                algorithm_oid="1.2.3",
                algorithm_name="test",
                key_size=256,
                fingerprint_sha256=None,
                pem=None,
            ),
            extensions=extensions,
            signature_hex="",
            tbs_certificate_bytes_hex="",
            der_hex="",
        ),
        lifecycle=CertificateLifecycle(status="VALID"),
    )


def test_default_projection_retains_existing_inventory_columns():
    projection = CertificateProjection()
    assert projection.columns == REPORT_COLUMNS
    assert len(projection.columns) == 15


def test_projection_can_select_a_validated_subset_of_columns():
    projection = CertificateProjection(
        fields=("gid", "serial_number", "status")
    )
    row = projection.inventory(make_certificate(with_template=True))
    assert projection.select(row) == {
        "gid": "gid-123",
        "serial_number": "01AB",
        "status": "Действителен",
    }


def test_unknown_projection_field_is_rejected():
    with pytest.raises(ValueError, match="Unknown certificate projection"):
        CertificateProjection(fields=("gid", "unknown_field"))


def test_template_name_is_human_readable_and_classification_is_available():
    row = CertificateProjection().inventory(
        make_certificate(with_template=True)
    )
    assert row.certificate_template == "Corporate Signing"
    assert row.classification is CertificateClassification.CORPORATE


def test_certificate_without_template_is_classified_as_key_carrier():
    row = CertificateProjection().inventory(
        make_certificate(with_template=False)
    )
    assert row.certificate_template is None
    assert row.classification is CertificateClassification.KEY_CARRIER


def test_classification_does_not_change_existing_export_columns():
    row = CertificateProjection().inventory(
        make_certificate(with_template=True)
    )
    assert tuple(row.model_dump().keys()) == REPORT_COLUMNS


class FakeOIDResolver:
    def get(self, oid):
        from radp.domain.oid.models import OIDDefinition

        if oid == "1.2.3.4":
            return OIDDefinition(oid=oid, name="Legacy Corporate Template")
        return None


def test_legacy_040_template_value_uses_curated_oid_name():
    certificate = make_certificate(with_template=True)
    extension = certificate.x509.extensions[0].model_copy(
        update={
            "template_oid": None,
            "template_name": None,
            "value": (
                "<MSCertificateTemplate(template_id=<ObjectIdentifier(oid=1.2.3.4, "
                "name=Unknown OID)>, major_version=1, minor_version=0)>"
            ),
        }
    )
    certificate = certificate.model_copy(
        update={
            "x509": certificate.x509.model_copy(
                update={"extensions": [extension]}
            )
        }
    )
    row = CertificateProjection(oid_resolver=FakeOIDResolver()).inventory(
        certificate
    )
    assert row.certificate_template == "Legacy Corporate Template"


def test_projection_prefers_v1_template_name_when_both_extensions_exist():
    certificate = make_certificate(with_template=True)
    v1_extension = Extension(
        oid=OID.CERTIFICATE_TEMPLATE_NAME.value,
        short_name="CERTIFICATE_TEMPLATE_NAME",
        name="Microsoft Certificate Template Name",
        critical=False,
        value="historical-extension-value",
        template_name="Employee",
    )
    certificate = certificate.model_copy(
        update={
            "x509": certificate.x509.model_copy(
                update={
                    "extensions": [v1_extension, *certificate.x509.extensions]
                }
            )
        }
    )
    row = CertificateProjection(oid_resolver=FakeOIDResolver()).inventory(
        certificate
    )
    assert row.certificate_template == "Employee"
    assert row.classification is CertificateClassification.CORPORATE


def test_v2_template_with_unmapped_oid_does_not_expose_raw_oid_as_name():
    certificate = make_certificate(with_template=True)
    extension = certificate.x509.extensions[0].model_copy(
        update={"template_name": None}
    )
    certificate = certificate.model_copy(
        update={
            "x509": certificate.x509.model_copy(
                update={"extensions": [extension]}
            )
        }
    )
    row = CertificateProjection().inventory(certificate)
    assert row.certificate_template is None


def test_v2_registry_names_remain_fresh_across_reports_without_refetching_der():
    """OID catalogue edits should affect an existing certificate's next report."""
    from radp.application.reporting.certificates import \
        CertificateReportService
    from radp.domain.oid.models import OIDDefinition

    certificate = make_certificate(with_template=True)

    class MutableResolver:
        name = "Curated Name v1"
        lookups = 0

        def get(self, oid):
            self.lookups += 1
            return OIDDefinition(oid=oid, name=self.name)

    class FakeCertificateQuery:
        def list_for_report(self, filters, limit=None):
            return [certificate, certificate]

    resolver = MutableResolver()
    projection = CertificateProjection(oid_resolver=resolver)
    service = CertificateReportService(
        certificates=FakeCertificateQuery(), projection=projection
    )
    assert [
        row["certificate_template"] for row in service.project_first()
    ] == ["Curated Name v1", "Curated Name v1"]
    assert resolver.lookups == 1
    resolver.name = "Curated Name v2"
    assert [
        row["certificate_template"] for row in service.project_first()
    ] == ["Curated Name v2", "Curated Name v2"]
    assert resolver.lookups == 2
