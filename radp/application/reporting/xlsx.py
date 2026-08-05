from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook
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
        self,
        rows: list[BaseModel],
        output: Path,
        *,
        sheet_name: str = "Sheet1",
    ):
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        if not rows:
            ws.append(["empty"])
            wb.save(output)
            return
        headers = list(rows[0].model_dump().keys())
        ws.append(headers)
        for row in rows:
            ws.append(
                [self._serialize(value) for value in row.model_dump().values()]
            )
        wb.save(output)
