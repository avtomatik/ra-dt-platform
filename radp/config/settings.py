from pathlib import Path

from pydantic import BaseModel, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

from .enums import TransportMode


class TransportSettings(BaseModel):
    mode: TransportMode
    curl_path: Path
    cert_thumbprint: SecretStr


class RemoteRaSettings(BaseModel):
    base_url: HttpUrl
    certificate_folder: str
    root: str = "/api/ra"


class DatabaseSettings(BaseModel):
    host: str
    port: int = 5432
    database: str
    username: str
    password: SecretStr
    connect_timeout: int = 5

    @property
    def url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.username,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.database,
        )


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_prefix="RADP_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )
    transport: TransportSettings
    remote_ra: RemoteRaSettings
    database: DatabaseSettings
    log_level: str = "INFO"
