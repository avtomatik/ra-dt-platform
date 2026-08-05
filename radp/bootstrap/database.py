from pydantic_settings import BaseSettings

from radp.infrastructure.persistence.database import (create_engine_from_url,
                                                      create_schema,
                                                      create_session_factory,
                                                      drop_schema)


def create_database(settings: BaseSettings):
    engine = create_engine_from_url(settings.database_url)
    create_schema(engine)


def drop_database(settings: BaseSettings):
    engine = create_engine_from_url(settings.database_url)
    drop_schema(engine)


def reset_database(settings: BaseSettings):
    engine = create_engine_from_url(settings.database_url)
    drop_schema(engine)
    create_schema(engine)


def session_factory(settings: BaseSettings):
    engine = create_engine_from_url(settings.database_url)
    return create_session_factory(engine)
