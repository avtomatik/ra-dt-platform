from types import SimpleNamespace

from cryptography import x509
from cryptography.x509.oid import ObjectIdentifier

from radp.domain.certificate.factory import CertificateFactory
from radp.domain.oid import OIDDefinition


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
