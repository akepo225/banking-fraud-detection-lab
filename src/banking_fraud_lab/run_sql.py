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

    sql_text = args.sql_file.read_text(encoding="utf-8")
    try:
        sql = _single_sql_statement(sql_text)
    except ValueError as error:
        parser.error(str(error))

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


def _single_sql_statement(sql: str) -> str:
    """Return one executable SQL statement or raise for unsupported scripts."""
    statements = _split_sql_statements(sql)
    if not statements:
        raise ValueError("SQL file does not contain an executable statement")
    if len(statements) > 1:
        raise ValueError(
            "run_sql supports one SQL statement per file; "
            f"found {len(statements)} statements"
        )
    return statements[0]


def _split_sql_statements(sql: str) -> tuple[str, ...]:
    """Split SQL statements while ignoring comments and quoted semicolons."""
    statements: list[str] = []
    current: list[str] = []
    index = 0
    quote: str | None = None

    while index < len(sql):
        char = sql[index]
        next_char = sql[index + 1] if index + 1 < len(sql) else ""

        if quote is not None:
            current.append(char)
            if char == quote:
                if next_char == quote:
                    current.append(next_char)
                    index += 2
                    continue
                quote = None
            index += 1
            continue

        if char in {"'", '"'}:
            quote = char
            current.append(char)
            index += 1
            continue

        if char == "-" and next_char == "-":
            index += 2
            while index < len(sql) and sql[index] not in "\r\n":
                index += 1
            continue

        if char == "/" and next_char == "*":
            index += 2
            while index + 1 < len(sql) and not (
                sql[index] == "*" and sql[index + 1] == "/"
            ):
                index += 1
            index = min(index + 2, len(sql))
            continue

        if char == ";":
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current.clear()
            index += 1
            continue

        current.append(char)
        index += 1

    statement = "".join(current).strip()
    if statement:
        statements.append(statement)
    return tuple(statements)


if __name__ == "__main__":
    raise SystemExit(main())
