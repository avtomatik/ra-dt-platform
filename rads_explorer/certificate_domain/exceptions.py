class CertificateDomainError(Exception): ...


class CertificateNotFound(CertificateDomainError):
    def __init__(self, certificate_id):
        super().__init__(f"Certificate {certificate_id} not found")
