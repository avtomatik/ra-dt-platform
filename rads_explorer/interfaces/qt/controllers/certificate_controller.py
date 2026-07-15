from PySide6.QtCore import QObject, QThread, Signal

from rads_explorer.certificate_domain.projection.report import ReportProjection


class CertificateWorker(QThread):
    result_ready = Signal(list)
    error = Signal(str)

    def __init__(self, service, snapshot_provider, query: str):
        super().__init__()
        self.service = service
        self.snapshot_provider = snapshot_provider
        self.query = query

    def run(self):
        try:
            result = self.service.search(self.query)

            rows = [
                ReportProjection.to_detail_row(
                    self.snapshot_provider.get_or_create(certificate)
                )
                for certificate in result.items
            ]

            self.result_ready.emit(rows)

        except Exception as e:
            self.error.emit(str(e))


class CertificateController(QObject):
    results_ready = Signal(list)
    error = Signal(str)

    def __init__(self, service, snapshot_provider):
        super().__init__()
        self.service = service
        self.snapshot_provider = snapshot_provider
        self.worker = None

    def search(self, query: str):
        self.worker = CertificateWorker(
            self.service, self.snapshot_provider, query
        )
        self.worker.result_ready.connect(self.results_ready.emit)
        self.worker.error.connect(self.error.emit)
        self.worker.start()
