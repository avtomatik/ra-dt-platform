import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from radp.application.reporting.xlsx import XLSXExporter

NS = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def test_datetime_columns_are_written_as_native_utc_excel_dates(
    tmp_path: Path,
):
    output = tmp_path / "report.xlsx"
    exporter = XLSXExporter()
    exporter.export(
        [
            {
                "serial_number": "01",
                "not_before": datetime(
                    2026, 11, 17, 13, 30, 0, tzinfo=timezone.utc
                ),
                "not_after": datetime(
                    2027, 11, 17, 13, 30, 0, tzinfo=timezone.utc
                ),
                "revoked_when": None,
            }
        ],
        output,
        columns=("serial_number", "not_before", "not_after", "revoked_when"),
        sheet_name="Report",
    )
    with ZipFile(output) as archive:
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        styles = ET.fromstring(archive.read("xl/styles.xml"))
    cells = {cell.attrib["r"]: cell for cell in sheet.findall(".//x:c", NS)}
    # Excel datetime values are numeric serials (not shared strings).
    assert cells["B2"].find("x:v", NS) is not None
    assert cells["B2"].attrib.get("t") != "s"
    assert float(cells["B2"].find("x:v", NS).text) > 0
    # Empty cells may be omitted by XlsxWriter rather than emitted explicitly.
    assert "D2" not in cells or cells["D2"].find("x:v", NS) is None
    custom_formats = styles.find("x:numFmts", NS)
    assert custom_formats is not None
    assert any(
        item.attrib.get("formatCode") == "yyyy-mm-dd hh:mm:ss"
        for item in custom_formats.findall("x:numFmt", NS)
    )


def test_naive_datetime_is_interpreted_as_utc():
    naive = datetime(2026, 11, 17, 13, 30, 0)
    assert XLSXExporter._excel_datetime(naive) == naive


def test_aware_non_utc_datetime_is_converted_to_utc_before_excel():
    from datetime import timedelta

    value = datetime(
        2026, 11, 17, 16, 30, 0, tzinfo=timezone(timedelta(hours=3))
    )
    assert XLSXExporter._excel_datetime(value) == datetime(
        2026, 11, 17, 13, 30, 0
    )
