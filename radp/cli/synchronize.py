import typer

from radp.bootstrap.runtime import get_runtime

app = typer.Typer()


@app.command()
def run():
    typer.echo("Synchronizing certificates...")
    runtime = get_runtime()
    count = runtime.synchronization.synchronize()
    typer.echo(f"Appended {count} certificates.")
