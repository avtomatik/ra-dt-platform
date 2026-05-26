from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook

from rads_explorer.data.reports import Report


class CellSerializer:
    @staticmethod
    def serialize(value):
        if isinstance(value, datetime):
            return (
                value.astimezone(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z")
            )
        return value


class XLSXExporter:
    def export(self, report: Report, output: Path):
        wb = Workbook()
        ws = wb.active
        ws.title = report.name

        data = report.data

        # =====================================================================
        # LIST REPORTS
        # =====================================================================
        if isinstance(data, list):
            if len(data) == 0:
                ws.append(["empty"])
            else:
                first = data[0]

                ws.append(list(asdict(first).keys()))

                for item in data:
                    row = [
                        CellSerializer.serialize(v)
                        for v in asdict(item).values()
                    ]
                    ws.append(row)

        # =====================================================================
        # DICT REPORTS
        # =====================================================================
        elif isinstance(data, dict):
            ws.append(["key", "value"])
            for k, v in data.items():
                ws.append([k, CellSerializer.serialize(v)])

        wb.save(output)
