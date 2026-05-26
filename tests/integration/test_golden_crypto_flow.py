import os

from rads_explorer.application.services.certificate_service import \
    CertificateService
from rads_explorer.data.export.xlsx import XLSXExporter
from rads_explorer.data.reports import ReportService


def test_golden_crypto_flow(client, detail_cache, tmp_path):
    """
    End-to-end validation:
    CryptoPro curl transport → domain services → report → XLSX export
    """

    os.environ["RADS_TRANSPORT"] = "http"

    certificate_service = CertificateService(client, detail_cache)

    reports = ReportService(certificate_service=certificate_service)

    exporter = XLSXExporter()

    # =========================================================================
    # 1. Fetch real data
    # =========================================================================
    certificates = certificate_service.list()
    assert certificates is not None
    assert len(certificates.items) > 0

    first_cert = certificates.items[0]

    detail = certificate_service.detail_by_serial(first_cert.serial_number)
    assert detail.serial_number == first_cert.serial_number
    assert detail.x509 is not None

    # =========================================================================
    # 2. Reports (REAL DATA PATH)
    # =========================================================================
    expiring = reports.expiring_certificates_report(days=365)
    certificates_inventory_report = reports.certificates_inventory_report()

    assert expiring is not None
    assert certificates_inventory_report is not None

    # =========================================================================
    # 3. XLSX Export (critical validation)
    # =========================================================================
    output_path = tmp_path / "golden_export.xlsx"

    exporter.export(expiring, output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0

    content = output_path.read_bytes()
    assert b"xl/" in content
    assert b"[Content_Types].xml" in content

    # =========================================================================
    # 4. sanity: data consistency
    # =========================================================================
    if expiring.data:
        assert isinstance(expiring.data, (list, tuple))

    print("GOLDEN FLOW OK")
