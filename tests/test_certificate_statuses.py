import pytest

from radp.domain.models.certificate import CertificateStatus


@pytest.mark.parametrize(
    ("raw_status", "expected"),
    [
        ("AffiliationChanged", CertificateStatus.AFFILIATION_CHANGED),
        ("CACompromise", CertificateStatus.CA_COMPROMISE),
        ("CessationOfOperation", CertificateStatus.CESSATION_OF_OPERATION),
        ("Expired", CertificateStatus.EXPIRED),
        ("Hold", CertificateStatus.HOLD),
        ("KeyCompromise", CertificateStatus.KEY_COMPROMISE),
        ("KeyExpired", CertificateStatus.KEY_EXPIRED),
        ("NotYetValid", CertificateStatus.NOT_YET_VALID),
        ("Revoked", CertificateStatus.REVOKED),
        ("Superseded", CertificateStatus.SUPERSEDED),
        ("Valid", CertificateStatus.VALID),
        ("Unknown", CertificateStatus.UNKNOWN),
        ("Unspecified", CertificateStatus.UNSPECIFIED),
        ("KEY_EXPIRED", CertificateStatus.KEY_EXPIRED),
        ("key-expired", CertificateStatus.KEY_EXPIRED),
        (" Key Expired ", CertificateStatus.KEY_EXPIRED),
    ],
)
def test_certificate_status_normalization(raw_status, expected):
    assert CertificateStatus(raw_status) is expected


@pytest.mark.parametrize(
    "raw_status",
    ["", " ", "SomeUnrecognizedStatus", None, 123],
)
def test_certificate_status_rejects_unknown_values(raw_status):
    with pytest.raises(ValueError):
        CertificateStatus(raw_status)
