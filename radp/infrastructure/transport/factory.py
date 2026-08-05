from pydantic_settings import BaseSettings

from radp.config.enums import TransportMode

from .curl import CurlTransport
from .http import HTTPTransport


def create_transport(settings: BaseSettings):
    match settings.transport:
        case TransportMode.CURL:
            return CurlTransport(settings)
        case TransportMode.HTTP:
            return HTTPTransport(settings)
        case _:
            raise ValueError(f"Unsupported transport: {settings.transport}")
