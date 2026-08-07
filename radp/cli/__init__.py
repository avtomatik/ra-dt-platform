import argparse

from .bootstrap import bootstrap
from .database import create, drop, reset
from .doctor import doctor
from .export import excel
from .serve import serve
from .synchronize import synchronize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="radp",
        description="Registry Authority Data Platform",
    )
    commands = parser.add_subparsers(
        dest="command",
        required=True,
    )
    # =========================================================================
    # doctor
    # =========================================================================
    doctor_parser = commands.add_parser(
        "doctor",
        help="Check platform configuration and runtime health.",
    )
    doctor_parser.set_defaults(handler=doctor)
    # =========================================================================
    # bootstrap
    # =========================================================================
    bootstrap_parser = commands.add_parser(
        "bootstrap",
        help="Initialize the platform runtime.",
    )
    bootstrap_parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the database.",
    )
    bootstrap_parser.set_defaults(handler=bootstrap)
    # =========================================================================
    # db
    # =========================================================================
    database_parser = commands.add_parser(
        "db",
        help="Database operations.",
    )
    database_commands = database_parser.add_subparsers(
        dest="database_command",
        required=True,
    )
    create_parser = database_commands.add_parser(
        "create",
        help="Create the database schema.",
    )
    create_parser.set_defaults(handler=create)
    drop_parser = database_commands.add_parser(
        "drop",
        help="Drop the database schema.",
    )
    drop_parser.set_defaults(handler=drop)
    reset_parser = database_commands.add_parser(
        "reset",
        help="Drop and recreate the database schema.",
    )
    reset_parser.set_defaults(handler=reset)
    # =========================================================================
    # export
    # =========================================================================
    export_parser = commands.add_parser(
        "export",
        help="Export platform data.",
    )
    export_commands = export_parser.add_subparsers(
        dest="export_command",
        required=True,
    )
    excel_parser = export_commands.add_parser(
        "excel",
        help="Export certificate snapshots to Excel.",
    )
    excel_parser.set_defaults(handler=excel)
    # =========================================================================
    # sync
    # =========================================================================
    sync_parser = commands.add_parser(
        "sync",
        help="Certificate synchronization operations.",
    )
    sync_commands = sync_parser.add_subparsers(
        dest="sync_command",
        required=True,
    )
    sync_run_parser = sync_commands.add_parser(
        "run",
        help="Synchronize certificates from the RA.",
    )
    sync_run_parser.set_defaults(handler=synchronize)
    # =========================================================================
    # serve
    # =========================================================================
    serve_parser = commands.add_parser(
        "serve",
        help="Start the FastAPI application.",
    )
    serve_parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind the API server to.",
    )
    serve_parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the API server to.",
    )
    serve_parser.set_defaults(handler=serve)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.handler(args)
