import pytest

from radp.cli import build_parser


def test_sync_run_accepts_multiple_certificate_folders():
    parser = build_parser()
    args = parser.parse_args(
        ["sync", "run", "--certificate-folders", "folder/2026,archive"]
    )
    assert args.certificate_folders == ("folder/2026", "archive")
    assert args.handler.__name__ == "synchronize"


def test_sync_run_folder_override_is_optional():
    parser = build_parser()
    args = parser.parse_args(["sync", "run"])
    assert args.certificate_folders is None


def test_sync_run_rejects_empty_folder_entries():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["sync", "run", "--certificate-folders", "folder1,,folder2"]
        )
