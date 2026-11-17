"""Application container factory."""

from functools import lru_cache

from radp.bootstrap.container import Container
from radp.config.settings import get_settings


@lru_cache(maxsize=8)
def get_container(
    certificate_folders: tuple[str, ...] | None = None,
) -> Container:
    """Return a container, optionally overriding the configured RA folder.
    With no override, settings (including ``RADP_REMOTE_RA__CERTIFICATE_FOLDERS``
    from the environment or ``.env``) are used unchanged. An override applies
    only to this container and does not modify the environment or ``.env``.
    """
    settings = get_settings()
    if certificate_folders is not None:
        settings = settings.model_copy(
            update={
                "remote_ra": settings.remote_ra.model_copy(
                    update={"certificate_folders": certificate_folders}
                )
            }
        )
    return Container(settings)
