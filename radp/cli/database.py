import argparse
import json
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from radp.bootstrap.runtime import get_container


def create(_args: argparse.Namespace) -> None:
    get_container().database.create()


def drop(_args: argparse.Namespace) -> None:
    get_container().database.drop()


def reset(_args: argparse.Namespace) -> None:
    get_container().database.reset()


def tables(_args: argparse.Namespace) -> None:
    for table in get_container().database.list_tables():
        print(table)


def stats(_args: argparse.Namespace) -> None:
    inspection = get_container().database
    for table in inspection.list_tables():
        print(f"{table}: {inspection.row_count(table)}")


def inspect_table(args: argparse.Namespace) -> None:
    rows = get_container().database.first_rows(args.table, args.limit)
    _print_json(rows)


def latest_certificates(args: argparse.Namespace) -> None:
    rows = get_container().database.latest_certificates(args.limit)
    _print_json(rows)


def oid_registry(args: argparse.Namespace) -> None:
    rows = get_container().database.oid_rows(args.limit)
    _print_json(rows)


def _print_json(value) -> None:
    print(
        json.dumps(value, indent=2, ensure_ascii=False, default=_json_default)
    )


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal)):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    raise TypeError(
        f"Object of type {type(value).__name__} is not JSON serializable"
    )
