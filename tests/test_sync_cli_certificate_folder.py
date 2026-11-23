import pytest

from radp.cli import build_parser


def test_sync_uses_toml_configuration_without_folder_arguments():
    parser = build_parser()
    args = parser.parse_args(["sync", "run"])
    assert args.handler.__name__ == "synchronize"


def test_old_folder_override_is_no_longer_accepted():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["sync", "run", "--certificate-folders", "archive"])
