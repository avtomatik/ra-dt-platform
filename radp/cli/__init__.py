import typer

from .bootstrap import bootstrap
from .database import app as database_app
from .doctor import doctor
from .export import app as export_app
from .serve import serve
from .synchronize import app as synchronize_app

app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

app.add_typer(database_app, name="db")
app.command(name="doctor")(doctor)
app.add_typer(export_app, name="export")
app.command(name="bootstrap")(bootstrap)
app.command(name="serve")(serve)
app.add_typer(synchronize_app, name="sync")
