import logging
import tomllib
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

from pydantic import (BaseModel, ConfigDict, Field, HttpUrl, PrivateAttr,
                      SecretStr, field_validator, model_validator)
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy import URL

from .enums import TransportMode
from .paths import BASE_DIR


def _normalize_nonempty_values(value: Any) -> tuple[str, ...]:
    """Normalize non-empty strings, preserving order and removing duplicates."""
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
    """RA endpoint settings; folder selection comes only from TOML.
    ``certificate_folders`` is a derived, read-only property. It cannot be
    provided through .env, programmatic settings or an unsupported CLI bypass.
    The default file lives alongside the application's deployed configuration,
    independently of the calling process's current working directory.
    """

    model_config = ConfigDict(extra="forbid")
    base_url: HttpUrl
    certificate_folders_file: Path = Field(
        default=BASE_DIR / "config" / "certificate-folders.toml"
    )
    root: str = "/api/ra"
    _certificate_folders: tuple[str, ...] = PrivateAttr(default=())

    @property
    def certificate_folders(self) -> tuple[str, ...]:
        return self._certificate_folders

    @model_validator(mode="after")
    def load_certificate_folders(self) -> "RemoteRaSettings":
        path = self.certificate_folders_file
        try:
            with path.open("rb") as stream:
                document = tomllib.load(stream)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            raise ValueError(
                f"Cannot read RA certificate folders from {path}: {exc}. "
                "Copy config/certificate-folders.toml.example to "
                "config/certificate-folders.toml and configure its folders."
            ) from exc
        if set(document) != {"certificate_folders"}:
            raise ValueError(
                f"Expected exactly one 'certificate_folders' array in {path}."
            )
        values = document["certificate_folders"]
        if not isinstance(values, list):
            raise ValueError(
                f"Expected a TOML array of folder names in {path}."
            )
        try:
            self._certificate_folders = _normalize_nonempty_values(values)
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
        return _normalize_nonempty_values(value)


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
