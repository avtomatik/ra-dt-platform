import typer

from radp.bootstrap.runtime import get_runtime

app = typer.Typer()


@app.command()
def excel():
    runtime = get_runtime()
    runtime.reporting.export_excel()
