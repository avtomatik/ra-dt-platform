from rads_explorer.api.dto.certificate import CertificateDetailDTO
from rads_explorer.certificate_domain.models.certificate import Certificate
from rads_explorer.certificate_domain.models.extension import Extension
from rads_explorer.certificate_domain.models.name_attributes import \
    NameAttributes


class CertificateMapper:
    @staticmethod
    def to_domain(dto: CertificateDetailDTO) -> Certificate:
        return Certificate(
            id=dto.id,
            name_attributes=NameAttributes.model_validate(
                dto.name_attributes.model_dump()
            ),
            serial_number=dto.serial_number,
            thumbprint=dto.thumbprint,
            not_before=dto.not_before,
            not_after=dto.not_after,
            key_not_after=dto.key_not_after,
            created_when=dto.created_when,
            status=dto.status,
            cert_request_id=dto.cert_request_id,
            subject=dto.subject,
            issuer=dto.issuer,
            user_id=dto.user_id,
            version=dto.version,
            public_key=dto.public_key,
            public_key_parameters=dto.public_key_parameters,
            public_key_oid=dto.public_key_oid,
            public_key_oid_description=dto.public_key_oid_description,
            extensions=[
                Extension.model_validate(e.model_dump())
                for e in (dto.extensions or [])
            ],
            signature=dto.signature,
            signature_oid=dto.signature_oid,
            signature_oid_description=dto.signature_oid_description,
            raw_certificate=dto.raw_certificate,
            revocation_reason=dto.revocation_reason,
            revoked_when=dto.revoked_when,
            folder=dto.folder,
        )
