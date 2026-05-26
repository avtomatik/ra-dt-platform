from pathlib import Path

from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from .enums import TransportMode


class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_prefix="RADS_", env_file=".env")

    # =========================================================================
    # General
    # =========================================================================
    env: str

    # =========================================================================
    # Transport
    # =========================================================================
    curl_path: Path
    cert_thumbprint: str

    transport: TransportMode

    timeout: int = 30
    verify_tls: bool = False

    # =========================================================================
    # API
    # =========================================================================
    api_base_url: HttpUrl
    api_version: str = "1.0"

    # =========================================================================
    # Logging
    # =========================================================================
    log_level: str = "INFO"
    log_dir: Path = Path("./logs")
    http_log_dir: Path = Path("./logs/http")

    # =========================================================================
    # Development
    # =========================================================================
    debug_http: bool = False
    save_raw_responses: bool = False
