from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient


def _configure_environment(monkeypatch):
    values = {
        "RADP_TRANSPORT__MODE": "http",
        "RADP_TRANSPORT__CURL_PATH": "/usr/bin/curl",
        "RADP_TRANSPORT__CERT_THUMBPRINT": "a" * 40,
        "RADP_REMOTE_RA__BASE_URL": "http://ra.example.test/",
        "RADP_REMOTE_RA__CERTIFICATE_FOLDERS": "production",
        "RADP_DATABASE__HOST": "localhost",
        "RADP_DATABASE__DATABASE": "radp",
        "RADP_DATABASE__USERNAME": "radp",
        "RADP_DATABASE__PASSWORD": "secret",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


class FakeReporting:
    columns = ("gid", "serial_number")

    def __init__(self, export_path: Path):
        self.export_path = export_path
        self.preview_filters = []
        self.export_filters = []

    def project_first(self, filters=None):
        self.preview_filters.append(filters)
        return [{"gid": "gid-123", "serial_number": "01"}]

    def export_excel(self, filters=None):
        self.export_filters.append(filters)
        return SimpleNamespace(
            path=self.export_path,
            name="certificates_inventory",
            generated_at=datetime.now(timezone.utc),
        )


def test_landing_preview_and_export_routes_use_expected_filters(
    monkeypatch, tmp_path
):
    _configure_environment(monkeypatch)
    from radp.bootstrap.runtime import get_container
    from radp.interfaces.api.main import create_app

    workbook = tmp_path / "report.xlsx"
    workbook.write_bytes(b"xlsx-test")
    reporting = FakeReporting(workbook)
    runtime = SimpleNamespace(reporting=reporting)
    app = create_app()
    app.dependency_overrides[get_container] = lambda: runtime
    with TestClient(app) as client:
        landing = client.get("/")
        assert landing.status_code == 200
        assert 'href="/web"' in landing.text
        assert 'href="/export/preview"' in landing.text
        assert "status=ALL" in landing.text
        assert "status=VALID" in landing.text
        web = client.get("/web")
        assert web.status_code == 200
        assert "gid-123" in web.text
        preview = client.get(
            "/export/preview?status=VALID&gid=gid-123&as_of_date=2026-11-17"
        )
        assert preview.status_code == 200
        assert "gid-123" in preview.text
        assert reporting.preview_filters[-1].status.value == "VALID"
        assert reporting.preview_filters[-1].gid == "gid-123"
        exported = client.get(
            "/export/certificates?status=VALID&gid=gid-123&as_of_date=2026-11-17"
        )
        assert exported.status_code == 200
        assert exported.content == b"xlsx-test"
        assert reporting.export_filters[-1].status.value == "VALID"
        assert reporting.export_filters[-1].gid == "gid-123"
    app.dependency_overrides.clear()
