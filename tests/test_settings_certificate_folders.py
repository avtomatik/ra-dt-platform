import pytest

from radp.config.settings import RemoteRaSettings, ReportingSettings, Settings


def test_single_folder_is_parsed_as_one_tuple_entry():
    settings = RemoteRaSettings(
        base_url="http://ra.example.test/api/ra/",
        certificate_folders="production",
    )
    assert settings.certificate_folders == ("production",)


def test_multiple_folders_are_parsed_and_whitespace_is_normalized():
    settings = RemoteRaSettings(
        base_url="http://ra.example.test/api/ra/",
        certificate_folders="folder1, folder2,folder3",
    )
    assert settings.certificate_folders == ("folder1", "folder2", "folder3")


def test_duplicate_folders_are_removed_preserving_order():
    settings = RemoteRaSettings(
        base_url="http://ra.example.test/api/ra/",
        certificate_folders="folder1,folder2,folder1",
    )
    assert settings.certificate_folders == ("folder1", "folder2")


@pytest.mark.parametrize("value", ["", " ", "folder1,,folder2", ",folder1"])
def test_empty_folder_entries_are_rejected(value):
    with pytest.raises(ValueError):
        RemoteRaSettings(
            base_url="http://ra.example.test/api/ra/",
            certificate_folders=value,
        )


def test_projection_fields_are_parsed_as_tuple():
    settings = ReportingSettings(projection_fields="gid,serial_number,status")
    assert settings.projection_fields == ("gid", "serial_number", "status")


def test_settings_reads_comma_separated_folder_environment_value(monkeypatch):
    monkeypatch.setenv("RADP_TRANSPORT__MODE", "http")
    monkeypatch.setenv("RADP_TRANSPORT__CURL_PATH", "/usr/bin/curl")
    monkeypatch.setenv("RADP_TRANSPORT__CERT_THUMBPRINT", "a" * 40)
    monkeypatch.setenv("RADP_REMOTE_RA__BASE_URL", "http://ra.example.test/")
    monkeypatch.setenv(
        "RADP_REMOTE_RA__CERTIFICATE_FOLDERS", "folder1,folder2"
    )
    monkeypatch.setenv(
        "RADP_REPORTING__PROJECTION_FIELDS", "gid,serial_number"
    )
    monkeypatch.setenv("RADP_DATABASE__HOST", "localhost")
    monkeypatch.setenv("RADP_DATABASE__DATABASE", "radp")
    monkeypatch.setenv("RADP_DATABASE__USERNAME", "radp")
    monkeypatch.setenv("RADP_DATABASE__PASSWORD", "secret")
    settings = Settings(_env_file=None)
    assert settings.remote_ra.certificate_folders == ("folder1", "folder2")
    assert settings.reporting.projection_fields == ("gid", "serial_number")
