from pathlib import Path

import pytest
from pydantic import ValidationError

from radp.config.settings import ReportingSettings, Settings


def _configure_settings_environment(monkeypatch, file_path: Path):
    values = {
        "RADP_TRANSPORT__MODE": "http",
        "RADP_TRANSPORT__CURL_PATH": "/usr/bin/curl",
        "RADP_TRANSPORT__CERT_THUMBPRINT": "a" * 40,
        "RADP_REMOTE_RA__BASE_URL": "http://ra.example.test/",
        "RADP_REMOTE_RA__CERTIFICATE_FOLDERS_FILE": str(file_path),
        "RADP_DATABASE__HOST": "localhost",
        "RADP_DATABASE__DATABASE": "radp",
        "RADP_DATABASE__USERNAME": "radp",
        "RADP_DATABASE__PASSWORD": "secret",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)


def test_projection_fields_are_parsed_as_tuple():
    settings = ReportingSettings(projection_fields="gid,serial_number,status")
    assert settings.projection_fields == ("gid", "serial_number", "status")


def test_settings_load_folders_from_toml_not_environment(
    monkeypatch, tmp_path
):
    path = tmp_path / "folders.toml"
    path.write_text(
        'certificate_folders = ["folder1", " folder2 ", "folder1"]\n'
    )
    _configure_settings_environment(monkeypatch, path)
    monkeypatch.setenv(
        "RADP_REPORTING__PROJECTION_FIELDS", "gid,serial_number"
    )
    settings = Settings(_env_file=None)
    assert settings.remote_ra.certificate_folders == ("folder1", "folder2")
    assert settings.reporting.projection_fields == ("gid", "serial_number")


def test_legacy_environment_folder_setting_is_rejected(monkeypatch, tmp_path):
    path = tmp_path / "folders.toml"
    path.write_text('certificate_folders = ["default"]\n')
    _configure_settings_environment(monkeypatch, path)
    monkeypatch.setenv("RADP_REMOTE_RA__CERTIFICATE_FOLDERS", "archive")
    with pytest.raises(ValidationError, match="certificate_folders"):
        Settings(_env_file=None)
