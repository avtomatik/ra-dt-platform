import typer

from radp.bootstrap.initialize import initialize_runtime


def bootstrap(
    reset: bool = typer.Option(
        False,
        help="Drop and recreate the database.",
    )
):
    initialize_runtime(reset)
    typer.echo("Initialization completed.")
