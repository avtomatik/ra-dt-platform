from pathlib import Path

import pytest
from pydantic import ValidationError

from radp.config.paths import BASE_DIR
from radp.config.settings import RemoteRaSettings


def test_folder_list_can_be_loaded_from_toml(tmp_path: Path):
    path = tmp_path / "folders.toml"
    path.write_text(
        'certificate_folders = ["default", "archive", "default", "production folder/2026"]\n'
    )
    settings = RemoteRaSettings(
        base_url="https://ra.example.test/", certificate_folders_file=path
    )
    assert settings.certificate_folders == (
        "default",
        "archive",
        "production folder/2026",
    )
    assert isinstance(settings.certificate_folders, tuple)


def test_default_toml_path_is_independent_of_working_directory():
    assert RemoteRaSettings.model_fields[
        "certificate_folders_file"
    ].default == (BASE_DIR / "config" / "certificate-folders.toml")


def test_direct_folder_list_is_no_longer_accepted(tmp_path: Path):
    path = tmp_path / "folders.toml"
    path.write_text('certificate_folders = ["archive"]\n')
    with pytest.raises(ValidationError, match="certificate_folders"):
        RemoteRaSettings(
            base_url="https://ra.example.test/",
            certificate_folders_file=path,
            certificate_folders=("outside-config",),
        )


@pytest.mark.parametrize(
    "body",
    [
        "certificate_folders = []\n",
        'certificate_folders = ["default", ""]\n',
        'wrong_key = ["default"]\n',
        'certificate_folders = "default"\n',
        'certificate_folders = ["default"]\nextra = "no"\n',
        "certificate_folders = [5]\n",
        'certificate_folders = "default,archive"\n',
        "[invalid\n",
    ],
)
def test_invalid_toml_is_rejected(tmp_path: Path, body: str):
    path = tmp_path / "folders.toml"
    path.write_text(body)
    with pytest.raises(ValidationError):
        RemoteRaSettings(
            base_url="https://ra.example.test/", certificate_folders_file=path
        )


def test_missing_toml_file_fails_with_migration_instructions(tmp_path: Path):
    with pytest.raises(
        ValidationError, match="Copy config/certificate-folders.toml.example"
    ):
        RemoteRaSettings(
            base_url="https://ra.example.test/",
            certificate_folders_file=tmp_path / "missing.toml",
        )


def test_external_file_changes_are_read_by_new_settings_instance(
    tmp_path: Path,
):
    path = tmp_path / "folders.toml"
    path.write_text('certificate_folders = ["default"]\n')
    first = RemoteRaSettings(
        base_url="https://ra.example.test/", certificate_folders_file=path
    )
    path.write_text('certificate_folders = ["archive"]\n')
    second = RemoteRaSettings(
        base_url="https://ra.example.test/", certificate_folders_file=path
    )
    assert first.certificate_folders == ("default",)
    assert second.certificate_folders == ("archive",)


def test_configured_toml_folders_are_passed_to_client(tmp_path: Path):
    from radp.infrastructure.ra_api.client import RAClient

    path = tmp_path / "certificate-folders.toml"
    path.write_text('certificate_folders = ["default", "archive"]\n')
    settings = RemoteRaSettings(
        base_url="https://ra.example.test/", certificate_folders_file=path
    )
    client = RAClient(
        transport=object(), certificate_folders=settings.certificate_folders
    )
    assert client.certificate_folders == ("default", "archive")
    assert client._resolve_folder("archive") == "archive"
