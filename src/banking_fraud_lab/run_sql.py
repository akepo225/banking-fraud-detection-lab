"""Run learner SQL examples against a local SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any


def main(argv: Sequence[str] | None = None) -> int:
    """Execute one SQL file against a SQLite database and print returned rows."""
    parser = argparse.ArgumentParser(
        description="Run one Banking Fraud Detection Lab SQL example."
    )
    parser.add_argument("database", type=Path, help="SQLite database path.")
    parser.add_argument("sql_file", type=Path, help="SQL file to execute.")
    args = parser.parse_args(argv)

    if not args.database.exists():
        parser.error(f"SQLite database does not exist: {args.database}")
    if not args.sql_file.exists():
        parser.error(f"SQL file does not exist: {args.sql_file}")

    sql = args.sql_file.read_text(encoding="utf-8")
    with sqlite3.connect(args.database) as connection:
        cursor = connection.execute(sql)
        rows = cursor.fetchall()
        columns = tuple(description[0] for description in cursor.description or ())
        row_count = cursor.rowcount

    if columns:
        print("\t".join(columns))
        for row in rows:
            print("\t".join(_format_cell(value) for value in row))
    else:
        print(f"Rows affected: {row_count}")
    return 0


def _format_cell(value: Any) -> str:
    """Format one SQLite value for tab-separated console output."""
    if value is None:
        return ""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


if __name__ == "__main__":
    raise SystemExit(main())
