from PySide6.QtCore import QObject, QThread, Signal

from rads_explorer.application.certificate_mapper import \
    CertificateDetailMapper
from rads_explorer.application.x509_inspector import X509Inspector


class CertificateWorker(QThread):
    result_ready = Signal(list)
    error = Signal(str)

    def __init__(self, service, query: str):
        super().__init__()
        self.service = service
        self.query = query

    def run(self):
        try:
            result = self.service.search(self.query)

            inspector = X509Inspector()
            mapper = CertificateDetailMapper(inspector)

            rows = [mapper.map(c) for c in result.items]

            self.result_ready.emit(rows)

        except Exception as e:
            self.error.emit(str(e))


class CertificateController(QObject):
    results_ready = Signal(list)
    error = Signal(str)

    def __init__(self, service):
        super().__init__()
        self.service = service
        self.worker = None

    def search(self, query: str):
        self.worker = CertificateWorker(self.service, query)
        self.worker.result_ready.connect(self.results_ready.emit)
        self.worker.error.connect(self.error.emit)
        self.worker.start()
