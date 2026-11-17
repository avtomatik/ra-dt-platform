import re
from collections.abc import Sequence

from radp.application.ports.oid_repository import OIDRepositoryPort
from radp.domain.models.certificate import Certificate
from radp.domain.oid import OID

from .enums import CERTIFICATE_STATUS_LABELS, CertificateClassification
from .models import REPORT_COLUMNS, CertificateInventoryRow


class CertificateProjection:
    """Map the domain certificate into a configurable inventory projection.
    The default projection preserves the complete RADP inventory column set.
    ``fields`` may select a validated subset without changing domain models or
    database persistence. Filtering is deliberately handled by PostgreSQL.
    """

    _LEGACY_TEMPLATE_OID_PATTERN = re.compile(
        r"template_id=<ObjectIdentifier\(oid=([^,)\s]+)"
    )

    def __init__(
        self,
        fields: Sequence[str] | None = None,
        oid_resolver: OIDRepositoryPort | None = None,
    ) -> None:
        selected = tuple(fields) if fields is not None else REPORT_COLUMNS
        if not selected:
            raise ValueError("A certificate projection must contain columns.")
        unknown = sorted(set(selected) - set(REPORT_COLUMNS))
        if unknown:
            raise ValueError(
                "Unknown certificate projection field(s): "
                + ", ".join(unknown)
            )
        if len(selected) != len(set(selected)):
            raise ValueError("Certificate projection fields must be unique.")
        self.fields = selected
        self.oid_resolver = oid_resolver
        self._template_name_cache: dict[str, str | None] = {}

    @property
    def columns(self) -> tuple[str, ...]:
        return self.fields

    def _template_name(self, extension) -> str | None:
        if extension.template_name:
            return extension.template_name
        template_oid = extension.template_oid
        if template_oid is None:
            # 0.4.0 persisted str(MSCertificateTemplate(...)) in Extension.value.
            # Read that legacy representation so existing rows can benefit from
            # a curated OID registry name without a forced certificate refresh.
            match = self._LEGACY_TEMPLATE_OID_PATTERN.search(extension.value)
            template_oid = match.group(1) if match else None
        if template_oid is None or self.oid_resolver is None:
            return None
        if template_oid not in self._template_name_cache:
            definition = self.oid_resolver.get(template_oid)
            self._template_name_cache[template_oid] = (
                (definition.name or definition.description)
                if definition is not None
                else None
            )
        return self._template_name_cache[template_oid]

    def inventory(self, certificate: Certificate) -> CertificateInventoryRow:
        subject = certificate.subject_by_oid
        template_extension = next(
            (
                extension
                for extension in certificate.x509.extensions
                if extension.oid == OID.CERTIFICATE_TEMPLATE.value
            ),
            None,
        )
        template_name = (
            self._template_name(template_extension)
            if template_extension is not None
            else None
        )
        classification = (
            CertificateClassification.CORPORATE
            if template_extension is not None
            else CertificateClassification.KEY_CARRIER
        )
        return CertificateInventoryRow(
            ogrn=subject.get(OID.OGRN.value),
            organization_name=subject.get(OID.O.value),
            gid=subject.get(OID.GUID.value),
            surname=subject.get(OID.SN.value),
            given_name=subject.get(OID.GIVEN_NAME.value),
            organizational_unit_name=subject.get(OID.OU.value),
            title=subject.get(OID.T.value),
            common_name=subject.get(OID.CN.value),
            serial_number=certificate.metadata.serial_number,
            snils=subject.get(OID.SNILS.value),
            status=CERTIFICATE_STATUS_LABELS[certificate.lifecycle.status],
            certificate_template=template_name,
            revoked_when=certificate.lifecycle.revoked_when,
            not_before=certificate.metadata.not_before,
            not_after=certificate.metadata.not_after,
            classification=classification,
        )

    def select(self, row: CertificateInventoryRow) -> dict:
        return row.model_dump(include=set(self.fields))
