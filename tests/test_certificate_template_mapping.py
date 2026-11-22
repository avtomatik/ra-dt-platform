from types import SimpleNamespace

from cryptography import x509
from cryptography.x509.oid import ObjectIdentifier

from radp.domain.certificate.factory import CertificateFactory
from radp.domain.certificate.template import (decode_legacy_template_name,
                                              decode_microsoft_template_name)
from radp.domain.oid import OID, OIDDefinition


class FakeOIDRepository:
    def __init__(self):
        self.entries = {}

    def get(self, oid):
        return self.entries.get(oid)

    def ensure(self, oid):
        definition = OIDDefinition(
            oid=oid,
            name="Corporate signing template" if oid == "1.2.3.4" else None,
        )
        self.entries[oid] = definition
        return definition


def test_microsoft_template_extension_is_normalized_to_template_metadata():
    repository = FakeOIDRepository()
    factory = CertificateFactory(repository)
    extension = x509.Extension(
        oid=ObjectIdentifier("1.3.6.1.4.1.311.21.7"),
        critical=False,
        value=x509.MSCertificateTemplate(
            template_id=ObjectIdentifier("1.2.3.4"),
            major_version=2,
            minor_version=1,
        ),
    )
    mapped = factory._build_extensions(
        SimpleNamespace(extensions=[extension])
    )[0]
    assert mapped.template_oid == "1.2.3.4"
    assert mapped.template_name == "Corporate signing template"
    assert "1.2.3.4" in repository.entries


def _der_tlv(tag: int, payload: bytes) -> bytes:
    length = len(payload)
    if length < 0x80:
        encoded_length = bytes([length])
    else:
        raw_length = length.to_bytes((length.bit_length() + 7) // 8, "big")
        encoded_length = bytes([0x80 | len(raw_length)]) + raw_length
    return bytes([tag]) + encoded_length + payload


def test_v1_template_name_decodes_microsoft_sequence_utf8string():
    name = b"Employee"
    encoded = _der_tlv(0x30, _der_tlv(0x0C, name))
    assert decode_microsoft_template_name(encoded) == "Employee"


def test_v1_template_name_accepts_deployed_bmpstring_encoding():
    name = "Сотрудник".encode("utf-16-be")
    encoded = _der_tlv(0x1E, name)
    assert decode_microsoft_template_name(encoded) == "Сотрудник"


def test_v1_template_name_rejects_malformed_or_trailing_der():
    assert decode_microsoft_template_name(b"\x30\x03\x0c\x04x") is None
    assert decode_microsoft_template_name(b"\x0c\x01x\x00") is None


def test_factory_extracts_v1_template_name_without_oid_catalog_lookup():
    repository = FakeOIDRepository()
    factory = CertificateFactory(repository)
    encoded_name = _der_tlv(0x30, _der_tlv(0x0C, b"Employee"))
    extension = x509.Extension(
        oid=ObjectIdentifier(OID.CERTIFICATE_TEMPLATE_NAME.value),
        critical=False,
        value=x509.UnrecognizedExtension(
            ObjectIdentifier(OID.CERTIFICATE_TEMPLATE_NAME.value),
            encoded_name,
        ),
    )
    mapped = factory._build_extensions(
        SimpleNamespace(extensions=[extension])
    )[0]
    assert mapped.template_oid is None
    assert mapped.template_name == "Employee"


def test_legacy_v1_extension_repr_can_be_decoded_without_refresh():
    encoded_name = _der_tlv(0x30, _der_tlv(0x0C, b"Employee"))
    legacy_value = str(
        x509.UnrecognizedExtension(
            ObjectIdentifier(OID.CERTIFICATE_TEMPLATE_NAME.value),
            encoded_name,
        )
    )
    assert decode_legacy_template_name(legacy_value) == "Employee"
