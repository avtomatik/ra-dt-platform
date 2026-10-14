import argparse

from .bootstrap import bootstrap
from .database import (create, drop, inspect_table, latest_certificates,
                       oid_registry, reset, stats, tables)
from .doctor import doctor
from .export import excel
from .oid import export_registry
from .serve import serve
from .synchronize import synchronize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="radp", description="Registry Authority Data Platform"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    # Convenient top-level aliases for common database inspection commands.
    # The canonical, grouped form (`radp db tables`, etc.) remains available.
    top_tables = commands.add_parser("tables", help="List database tables.")
    top_tables.set_defaults(handler=tables)

    top_stats = commands.add_parser(
        "stats", help="Show row counts for all tables."
    )
    top_stats.set_defaults(handler=stats)

    top_inspect = commands.add_parser(
        "inspect", help="Show rows from a database table."
    )
    top_inspect.add_argument("--table", required=True)
    top_inspect.add_argument("--limit", type=int, default=20)
    top_inspect.set_defaults(handler=inspect_table)

    top_latest = commands.add_parser(
        "latest-certificates", help="Show the latest certificate records."
    )
    top_latest.add_argument("--limit", type=int, default=20)
    top_latest.set_defaults(handler=latest_certificates)

    top_oids = commands.add_parser("oids", help="Show OID registry contents.")
    top_oids.add_argument("--limit", type=int, default=20)
    top_oids.set_defaults(handler=oid_registry)

    doctor_parser = commands.add_parser(
        "doctor", help="Run live configuration and runtime health checks."
    )
    doctor_parser.set_defaults(handler=doctor)

    bootstrap_parser = commands.add_parser(
        "bootstrap", help="Initialize the platform."
    )
    bootstrap_parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the database before initialization.",
    )
    bootstrap_parser.set_defaults(handler=bootstrap)

    db_parser = commands.add_parser(
        "db", help="Database administration and inspection."
    )
    db_commands = db_parser.add_subparsers(
        dest="database_command", required=True
    )

    db_create = db_commands.add_parser("create", help="Create the schema.")
    db_create.set_defaults(handler=create)

    db_drop = db_commands.add_parser("drop", help="Drop the schema.")
    db_drop.set_defaults(handler=drop)

    db_reset = db_commands.add_parser(
        "reset", help="Drop and recreate the schema."
    )
    db_reset.set_defaults(handler=reset)

    db_tables = db_commands.add_parser("tables", help="List database tables.")
    db_tables.set_defaults(handler=tables)

    db_stats = db_commands.add_parser(
        "stats", help="Show row counts for all tables."
    )
    db_stats.set_defaults(handler=stats)

    db_inspect = db_commands.add_parser(
        "inspect", help="Show the first N rows of a table."
    )
    db_inspect.add_argument("--table", required=True)
    db_inspect.add_argument("--limit", type=int, default=20)
    db_inspect.set_defaults(handler=inspect_table)

    db_latest = db_commands.add_parser(
        "latest-certificates", help="Show the latest certificate records."
    )
    db_latest.add_argument("--limit", type=int, default=20)
    db_latest.set_defaults(handler=latest_certificates)

    db_oids = db_commands.add_parser(
        "oids", help="Show OID registry contents."
    )
    db_oids.add_argument("--limit", type=int, default=20)
    db_oids.set_defaults(handler=oid_registry)

    export_parser = commands.add_parser(
        "export", help="Generate runtime reports."
    )
    export_commands = export_parser.add_subparsers(
        dest="export_command", required=True
    )

    excel_parser = export_commands.add_parser(
        "excel", help="Export certificate inventory to XLSX."
    )
    excel_parser.set_defaults(handler=excel)

    oid_parser = commands.add_parser("oid", help="OID registry operations.")
    oid_commands = oid_parser.add_subparsers(dest="oid_command", required=True)

    oid_export = oid_commands.add_parser(
        "export", help="Export enriched DB OID registry to the seed JSON."
    )
    oid_export.set_defaults(handler=export_registry)

    sync_parser = commands.add_parser(
        "sync", help="Certificate synchronization operations."
    )
    sync_commands = sync_parser.add_subparsers(
        dest="sync_command", required=True
    )
    sync_run = sync_commands.add_parser(
        "run", help="Synchronize certificates from the RA."
    )
    sync_run.set_defaults(handler=synchronize)

    serve_parser = commands.add_parser(
        "serve", help="Start the FastAPI application."
    )
    serve_parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind the API server to."
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
    result = args.handler(args)
    if isinstance(result, int):
        raise SystemExit(result)
