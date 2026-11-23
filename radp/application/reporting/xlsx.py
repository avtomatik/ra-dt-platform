from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

import xlsxwriter

DATETIME_COLUMNS = {"revoked_when", "not_before", "not_after"}
DATETIME_NUMBER_FORMAT = "yyyy-mm-dd hh:mm:ss"


class XLSXExporter:
    """Write report rows as typed Excel cells, keeping timestamps in UTC."""

    @staticmethod
    def _excel_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            # RADP stores timestamps as UTC. Naive values at the boundary are
            # therefore interpreted as UTC rather than as host-local time.
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    def export(
        self,
        rows: list[dict[str, Any]],
        output: Path,
        *,
        columns: Sequence[str],
        sheet_name: str = "Sheet1",
    ) -> None:
        headers = list(columns)
        if not headers:
            raise ValueError("Excel report must contain at least one column.")
        header_format_options = {
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#1F4E78",
            "pattern": 1,
            "text_wrap": True,
            "valign": "vcenter",
        }
        datetime_format_options = {"num_format": DATETIME_NUMBER_FORMAT}
        with xlsxwriter.Workbook(str(output)) as workbook:
            worksheet = workbook.add_worksheet(sheet_name)
            header_format = workbook.add_format(header_format_options)
            datetime_format = workbook.add_format(datetime_format_options)
            worksheet.freeze_panes(1, 0)
            worksheet.write_row(0, 0, headers, header_format)
            for row_index, row in enumerate(rows, start=1):
                for column_index, header in enumerate(headers):
                    value = row.get(header)
                    if value is None:
                        worksheet.write_blank(row_index, column_index, None)
                    elif header in DATETIME_COLUMNS and isinstance(
                        value, datetime
                    ):
                        worksheet.write_datetime(
                            row_index,
                            column_index,
                            self._excel_datetime(value),
                            datetime_format,
                        )
                    elif isinstance(value, (int, float, bool)):
                        worksheet.write(row_index, column_index, value)
                    else:
                        # Explicit string writing prevents untrusted report data
                        # from being interpreted as an Excel formula.
                        worksheet.write_string(
                            row_index, column_index, str(value)
                        )
            for column_index, header in enumerate(headers):
                minimum_width = 20 if header in DATETIME_COLUMNS else 12
                width = min(max(len(str(header)) + 2, minimum_width), 35)
                worksheet.set_column(column_index, column_index, width)
            if rows:
                worksheet.autofilter(0, 0, len(rows), len(headers) - 1)
            else:
                worksheet.autofilter(0, 0, 0, len(headers) - 1)
            worksheet.set_row(0, 30)
