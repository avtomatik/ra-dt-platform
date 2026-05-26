from PySide6.QtWidgets import (QHBoxLayout, QLabel, QLineEdit, QMainWindow,
                               QMessageBox, QPushButton, QTableView, QTextEdit,
                               QVBoxLayout, QWidget)

from rads_explorer.interfaces.qt.controllers.certificate_controller import \
    CertificateController
from rads_explorer.interfaces.qt.models.certificate_table_model import \
    CertificateTableModel


class MainWindow(QMainWindow):
    def __init__(self, certificate_service):
        super().__init__()

        self.setWindowTitle("RADS Explorer - Certificate Console")
        self.resize(1200, 700)

        self.controller = CertificateController(certificate_service)
        self.controller.results_ready.connect(self.on_results)
        self.controller.error.connect(self.on_error)

        self.model = CertificateTableModel()

        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        # ===================== SEARCH BAR =====================
        search_row = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search certificates (CN, serial_number, thumbprint...)"
        )

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search)

        search_row.addWidget(self.search_input)
        search_row.addWidget(self.search_btn)

        layout.addLayout(search_row)

        # ===================== TABLE =====================
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.clicked.connect(self.on_row_selected)

        layout.addWidget(self.table)

        # ===================== DETAILS =====================
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Select a certificate to view details")

        layout.addWidget(QLabel("Details"))
        layout.addWidget(self.details)

    def search(self):
        query = self.search_input.text().strip()
        if not query:
            return

        self.search_btn.setEnabled(False)
        self.details.setText("Loading...")

        self.controller.search(query)

    def on_results(self, rows):
        self.search_btn.setEnabled(True)
        self.model.set_data(rows)

    def on_error(self, msg):
        self.search_btn.setEnabled(True)
        QMessageBox.critical(self, "Error", msg)

    def on_row_selected(self, index):
        row = self.model._rows[index.row()]

        self.details.setText(
            f"""
Serial: {row.serial_number}
CN: {row.common_name}
Organization: {row.organization_name}
SNILS: {row.snils}
Status: {row.status}
Valid from: {row.not_before}
Valid to: {row.not_after}
"""
        )
