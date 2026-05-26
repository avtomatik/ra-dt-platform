def test_report_generation(report_service):
    report = report_service.expiring_certificates_report(365)

    assert report.name.startswith("expiring")
    assert report.data is not None
