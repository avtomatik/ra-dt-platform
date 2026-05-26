class TransportError(Exception): ...


class CurlExecutionError(TransportError): ...


class TimeoutError(TransportError): ...


class HTTPError(TransportError):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body

        super().__init__(f"HTTP request failed: {status_code}")


class JSONDecodeError(TransportError): ...
