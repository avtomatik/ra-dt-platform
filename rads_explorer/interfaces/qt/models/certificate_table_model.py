from dataclasses import asdict

from PySide6.QtCore import QAbstractTableModel, Qt


class CertificateTableModel(QAbstractTableModel):
    def __init__(self, rows=None):
        super().__init__()
        self._rows = rows or []
        self._columns = (
            list(asdict(self._rows[0]).keys()) if self._rows else []
        )

    def set_data(self, rows):
        self.beginResetModel()
        self._rows = rows
        self._columns = list(asdict(rows[0]).keys()) if rows else []
        self.endResetModel()

    def rowCount(self, parent=None):
        return len(self._rows)

    def columnCount(self, parent=None):
        return len(self._columns)

    def data(self, index, role):
        if not index.isValid():
            return None

        if role == Qt.DisplayRole:
            row = self._rows[index.row()]
            col = self._columns[index.column()]
            return str(getattr(row, col))

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return self._columns[section]
