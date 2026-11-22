import logging
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import (BaseModel, Field, HttpUrl, SecretStr, field_validator,
                      model_validator)
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
    certificate_folders: Annotated[tuple[str, ...] | None, NoDecode] = None
    certificate_folders_file: Path | None = None
    root: str = "/api/ra"

    @field_validator("certificate_folders", mode="before")
    @classmethod
    def parse_certificate_folders(cls, value: Any) -> tuple[str, ...]:
        return _parse_csv_tuple(value)

    @model_validator(mode="after")
    def resolve_certificate_folders(self) -> "RemoteRaSettings":
        # Inline environment configuration wins over the optional TOML file.
        if self.certificate_folders is not None:
            return self
        if self.certificate_folders_file is None:
            raise ValueError(
                "Set certificate_folders or certificate_folders_file for the remote RA."
            )
        path = self.certificate_folders_file
        try:
            with path.open("rb") as stream:
                document = tomllib.load(stream)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(
                f"Cannot read RA certificate folders from {path}: {exc}"
            ) from exc
        if not isinstance(document, dict) or set(document) != {
            "certificate_folders"
        }:
            raise ValueError(
                f"Expected only a 'certificate_folders' list in {path}."
            )
        try:
            self.certificate_folders = _parse_csv_tuple(
                document["certificate_folders"]
            )
        except ValueError as exc:
            raise ValueError(
                f"Invalid RA certificate folders in {path}: {exc}"
            ) from exc
        return self


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
