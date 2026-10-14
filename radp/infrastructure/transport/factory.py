from radp.config.enums import TransportMode
from radp.config.settings import Settings

from .curl import CurlTransport
from .http import HTTPTransport


def create_transport(settings: Settings):
    match settings.transport.mode:
        case TransportMode.CURL:
            return CurlTransport(settings)
        case TransportMode.HTTP:
            return HTTPTransport(settings)
        case _:
            raise ValueError(
                f"Unsupported transport: {settings.transport.mode}"
            )
