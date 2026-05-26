from rads_explorer.api.schemas.certificate import CertificateDetail


class CertificateDetailCache:
    def __init__(self):
        self._details_by_id: dict[str, CertificateDetail] = {}
        self._id_by_serial: dict[str, str] = {}

    def get_by_id(self, certificate_id: str) -> CertificateDetail | None:
        return self._details_by_id.get(certificate_id)

    def get_by_serial(self, serial_number: str) -> CertificateDetail | None:
        certificate_id = self._id_by_serial.get(serial_number)

        if certificate_id is None:
            return None

        return self.get_by_id(certificate_id)

    def put(self, detail: CertificateDetail):
        self._details_by_id[detail.id] = detail
        self._id_by_serial[detail.serial_number] = detail.id

    def clear(self):
        self._details_by_id.clear()
        self._id_by_serial.clear()
