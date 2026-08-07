from radp.bootstrap.database import (create_database, drop_database,
                                     reset_database)
from radp.config.settings import Settings


def create(_args) -> None:
    settings = Settings()
    create_database(settings)


def drop(_args) -> None:
    settings = Settings()
    drop_database(settings)


def reset(_args) -> None:
    settings = Settings()
    reset_database(settings)
