from datetime import datetime, timezone
from uuid import uuid4

from radp.domain.models.certificate import CertificateLifecycle
from radp.infrastructure.persistence.models.certificates import \
    CertificateRecord


def test_certificate_record_keeps_lifecycle_outside_json_payload():
    certificate_id = uuid4()
    now = datetime.now(timezone.utc)
    record = CertificateRecord(
        id=certificate_id,
        status="VALID",
        revoked_when=None,
        revocation_reason=None,
        payload={
            "certificate_id": str(certificate_id),
            "metadata": {"serial_number": "123"},
            "x509": {},
        },
        persisted_at=now,
    )
    assert record.status == "VALID"
    assert "status" not in record.payload.get("metadata", {})
    assert "revoked_when" not in record.payload.get("metadata", {})
    assert CertificateLifecycle(status=record.status).status == "VALID"
