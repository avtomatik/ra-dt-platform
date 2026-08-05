import typer

from radp.bootstrap.database import (create_database, drop_database,
                                     reset_database)
from radp.config.settings import Settings

app = typer.Typer()


@app.command()
def create():
    settings = Settings()
    create_database(settings)


@app.command()
def drop():
    settings = Settings()
    drop_database(settings)


@app.command()
def reset():
    settings = Settings()
    reset_database(settings)
