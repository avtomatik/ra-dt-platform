import logging
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field, HttpUrl, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL

from .enums import TransportMode


def _parse_csv_tuple(value: Any) -> tuple[str, ...]:
    """Normalize a comma-separated setting or an already parsed sequence."""
    if isinstance(value, str):
        values = value.split(",")
    elif isinstance(value, (tuple, list)):
        values = list(value)
    else:
        raise ValueError("Expected a comma-separated string or a sequence.")
    normalized: list[str] = []
    for item in values:
        if not isinstance(item, str):
            raise ValueError("Every configured value must be a string.")
        item = item.strip()
        if not item:
            raise ValueError("Configured lists must not contain empty items.")
        if item not in normalized:
            normalized.append(item)
    if not normalized:
        raise ValueError("At least one value must be configured.")
    return tuple(normalized)


class TransportSettings(BaseModel):
    mode: TransportMode
    curl_path: Path
    cert_thumbprint: SecretStr


class RemoteRaSettings(BaseModel):
    base_url: HttpUrl
    certificate_folders: Annotated[tuple[str, ...], NoDecode]
    root: str = "/api/ra"

    @field_validator("certificate_folders", mode="before")
    @classmethod
    def parse_certificate_folders(cls, value: Any) -> tuple[str, ...]:
        return _parse_csv_tuple(value)


class ReportingSettings(BaseModel):
    projection_fields: Annotated[tuple[str, ...] | None, NoDecode] = None

    @field_validator("projection_fields", mode="before")
    @classmethod
    def parse_projection_fields(cls, value: Any) -> tuple[str, ...] | None:
        if value is None:
            return None
        return _parse_csv_tuple(value)


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
            host=self.host,
            port=self.port,
            database=self.database,
            username=self.username,
            password=self.password.get_secret_value(),
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
    reporting: ReportingSettings = Field(default_factory=ReportingSettings)
    log_level: int = logging.INFO


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
