from pathlib import Path

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from .enums import TransportMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="RADP_", env_file=".env")

    ###########################################################################
    # Transport
    ###########################################################################
    curl_path: Path
    cert_thumbprint: str
    transport: TransportMode

    ###########################################################################
    # Remote RA
    ###########################################################################
    api_base_url: HttpUrl
    api_root: str = "/api/ra"

    ###########################################################################
    # Database
    ###########################################################################
    database_driver: str = "postgres"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "radp"
    database_user: str = "postgres"
    database_password: str = "postgres"

    ###########################################################################
    # Logging
    ###########################################################################
    log_level: str = "INFO"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://"
            f"{self.database_user}:"
            f"{self.database_password}@"
            f"{self.database_host}:"
            f"{self.database_port}/"
            f"{self.database_name}"
        )
