from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization

from radp.domain.models.attribute import DistinguishedNameAttribute
from radp.domain.models.certificate import CertificateSnapshot
from radp.domain.models.extension import ExtensionSnapshot
from radp.domain.models.metadata import CertificateMetadata
from radp.domain.models.name import DistinguishedName
from radp.domain.models.public_key import PublicKeySnapshot
from radp.domain.models.x509 import X509Snapshot
from radp.domain.snapshots.decoder import CertificateDecoder
from radp.infrastructure.persistence.repositories.oid_repository import \
    OIDRepository
from radp.infrastructure.ra_api.dto.certificate import CertificateDTO


class CertificateSnapshotFactory:
    _VERSION_MAPPING = {x509.Version.v1: 1, x509.Version.v3: 3}

    def __init__(
        self,
        oid_repository: OIDRepository,
        decoder: CertificateDecoder | None = None,
    ):
        self.oid_repository = oid_repository
        self.decoder = decoder or CertificateDecoder()

    def _build_metadata(self, dto: CertificateDTO) -> CertificateMetadata:
        return CertificateMetadata(
            id=dto.id,
            status=dto.status,
            serial_number=dto.serial_number,
            thumbprint=dto.thumbprint,
            created_when=dto.created_when,
            not_before=dto.not_before,
            not_after=dto.not_after,
            key_not_after=dto.key_not_after,
            cert_request_id=dto.cert_request_id,
            user_id=dto.user_id,
            folder=dto.folder,
            revoked_when=dto.revoked_when,
            revocation_reason=dto.revocation_reason,
            raw_name_attributes=dict(dto.name_attributes),
        )

    def _build_x509(self, cert: x509.Certificate, der: bytes) -> X509Snapshot:
        pub = cert.public_key()
        pem = pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("ascii")
        fingerprint = hashes.Hash(hashes.SHA256())
        fingerprint.update(
            pub.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
        )
        fingerprint_sha256 = fingerprint.finalize().hex()
        key_size = getattr(pub, "key_size", None)
        algorithm_oid = cert.public_key_algorithm_oid.dotted_string
        algorithm_name = cert.public_key_algorithm_oid._name
        public_key = PublicKeySnapshot(
            algorithm_oid=algorithm_oid,
            algorithm_name=algorithm_name,
            key_size=key_size,
            fingerprint_sha256=fingerprint_sha256,
            pem=pem,
        )
        return X509Snapshot(
            version=self._version_number(cert.version),
            serial_number=cert.serial_number,
            serial_number_hex=hex(cert.serial_number),
            issuer=self._build_name(cert.issuer),
            subject=self._build_name(cert.subject),
            not_valid_before=cert.not_valid_before_utc,
            not_valid_after=cert.not_valid_after_utc,
            signature_algorithm_oid=cert.signature_algorithm_oid.dotted_string,
            signature_algorithm_name=cert.signature_algorithm_oid._name,
            public_key=public_key,
            extensions=self._build_extensions(cert),
            signature_hex=cert.signature.hex(),
            tbs_certificate_bytes_hex=cert.tbs_certificate_bytes.hex(),
            der_hex=der.hex(),
        )

    @classmethod
    def _version_number(cls, version: x509.Version) -> int:
        return cls._VERSION_MAPPING[version]

    def _build_name(self, name: x509.Name) -> DistinguishedName:
        attributes = []
        for attribute in name:
            registry = self.oid_repository.get(attribute.oid.dotted_string)
            attributes.append(
                DistinguishedNameAttribute(
                    oid=attribute.oid.dotted_string,
                    short_name=registry.short_name if registry else None,
                    name=registry.name if registry else None,
                    value=attribute.value,
                )
            )
        return DistinguishedName(
            rfc4514=name.rfc4514_string(), attributes=attributes
        )

    def _build_extensions(
        self, cert: x509.Certificate
    ) -> list[ExtensionSnapshot]:
        result = []
        for extension in cert.extensions:
            registry = self.oid_repository.get(extension.oid.dotted_string)
            result.append(
                ExtensionSnapshot(
                    oid=extension.oid.dotted_string,
                    short_name=registry.short_name if registry else None,
                    name=registry.name if registry else None,
                    critical=extension.critical,
                    value=str(extension.value),
                )
            )
        return result

    def create(self, dto: CertificateDTO) -> CertificateSnapshot:
        der, cert = self.decoder.decode(dto)
        return CertificateSnapshot(
            certificate_id=dto.id,
            metadata=self._build_metadata(dto),
            x509=self._build_x509(cert, der),
        )
