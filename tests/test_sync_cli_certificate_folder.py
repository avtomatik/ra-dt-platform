from radp.cli import build_parser


def test_sync_run_accepts_optional_certificate_folder():
    parser = build_parser()
    args = parser.parse_args(
        ["sync", "run", "--certificate-folder", "folder/2026"]
    )
    assert args.certificate_folder == "folder/2026"
    assert args.handler.__name__ == "synchronize"


def test_sync_run_folder_override_is_optional():
    parser = build_parser()
    args = parser.parse_args(["sync", "run"])
    assert args.certificate_folder is None
