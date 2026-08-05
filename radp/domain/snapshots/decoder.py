import base64

from cryptography import x509

from radp.infrastructure.ra_api.dto.certificate import CertificateDTO


class CertificateDecoder:
    def decode(self, dto: CertificateDTO) -> tuple[bytes, x509.Certificate]:
        der = base64.b64decode(dto.raw_certificate, validate=True)
        cert = x509.load_der_x509_certificate(der)
        return der, cert
