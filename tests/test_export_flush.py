import pytest

from radp.cli import export as export_cli


def test_flush_removes_only_regular_xlsx_files_in_export_directory(
    tmp_path, monkeypatch
):
    exports = tmp_path / "exports"
    exports.mkdir()
    xlsx = exports / "inventory.xlsx"
    xlsx.write_text("generated", encoding="utf-8")
    uppercase_xlsx = exports / "REPORT.XLSX"
    uppercase_xlsx.write_text("generated", encoding="utf-8")
    csv = exports / "inventory.csv"
    csv.write_text("keep", encoding="utf-8")
    subdirectory = exports / "nested.xlsx"
    subdirectory.mkdir()
    outside = tmp_path / "outside.xlsx"
    outside.write_text("keep", encoding="utf-8")
    symlink = exports / "linked.xlsx"
    try:
        symlink.symlink_to(outside)
    except OSError:
        symlink = None

    monkeypatch.setattr(export_cli, "EXPORTS_DIR", exports)

    export_cli.flush(None)

    assert not xlsx.exists()
    assert not uppercase_xlsx.exists()
    assert csv.exists()
    assert subdirectory.is_dir()
    assert outside.exists()
    if symlink is not None:
        assert symlink.is_symlink()


def test_flush_is_noop_when_export_directory_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(export_cli, "EXPORTS_DIR", tmp_path / "missing")
    export_cli.flush(None)


def test_flush_raises_if_export_path_is_not_a_directory(tmp_path, monkeypatch):
    path = tmp_path / "exports"
    path.write_text("not a directory", encoding="utf-8")
    monkeypatch.setattr(export_cli, "EXPORTS_DIR", path)

    with pytest.raises(NotADirectoryError):
        export_cli.flush(None)
