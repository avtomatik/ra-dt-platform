import base64


class CertificateDecoder:
    @staticmethod
    def decode(value: bytes) -> bytes:
        return base64.b64decode(value, validate=True)
