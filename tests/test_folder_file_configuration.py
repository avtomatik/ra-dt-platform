from pathlib import Path

import pytest
from pydantic import ValidationError

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


def test_explicit_csv_folders_override_file(tmp_path: Path):
    # The file need not exist when a direct list is configured.
    settings = RemoteRaSettings(
        base_url="https://ra.example.test/",
        certificate_folders="production,archive",
        certificate_folders_file=tmp_path / "missing.toml",
    )
    assert settings.certificate_folders == ("production", "archive")


@pytest.mark.parametrize(
    "body",
    [
        "certificate_folders = []\n",
        'certificate_folders = ["default", ""]\n',
        'wrong_key = ["default"]\n',
        'certificate_folders = "default"\nextra = "no"\n',
        "certificate_folders = [5]\n",
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


def test_missing_folder_settings_or_file_fails(tmp_path: Path):
    with pytest.raises(ValidationError):
        RemoteRaSettings(base_url="https://ra.example.test/")
    with pytest.raises(ValidationError):
        RemoteRaSettings(
            base_url="https://ra.example.test/",
            certificate_folders_file=tmp_path / "missing",
        )
