from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, HttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from .enums import TransportMode


class TransportSettings(BaseModel):
    mode: TransportMode
    curl_path: Path
    cert_thumbprint: SecretStr


class RemoteRaSettings(BaseModel):
    base_url: HttpUrl
    root: str = "/api/ra"


class DatabaseSettings(BaseModel):
    driver: str = "postgresql"
    host: str
    port: int = 5432
    name: str
    user: str
    password: SecretStr
    connect_timeout: int = 5

    @property
    def url(self) -> str:
        name = quote(self.name, safe="")
        user = quote(self.user, safe="")
        password = quote(self.password.get_secret_value(), safe="")
        return f"postgresql+psycopg://{user}:{password}@{self.host}:{self.port}/{name}"


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
