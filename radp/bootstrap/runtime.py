"""Application container factory."""

from functools import lru_cache

from radp.bootstrap.container import Container
from radp.config.settings import get_settings


@lru_cache(maxsize=1)
def get_container() -> Container:
    """Return the process-wide container using validated TOML settings."""
    return Container(get_settings())
