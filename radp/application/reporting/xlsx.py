from datetime import datetime, timezone
from pathlib import Path

import xlsxwriter
from pydantic import BaseModel


class XLSXExporter:
    @staticmethod
    def _serialize(value):
        if isinstance(value, datetime):
            return (
                value.astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
        return value

    def export(
        self, rows: list[BaseModel], output: Path, *, sheet_name="Sheet1"
    ):
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(sheet_name)
        if not rows:
            worksheet.write(0, 0, "empty")
            workbook.close()
            return
        headers = list(rows[0].model_dump().keys())
        for column, header in enumerate(headers):
            worksheet.write(0, column, header)
        for row_index, row in enumerate(rows, start=1):
            values = row.model_dump()
            for column, header in enumerate(headers):
                worksheet.write(
                    row_index, column, self._serialize(values[header])
                )
        workbook.close()
