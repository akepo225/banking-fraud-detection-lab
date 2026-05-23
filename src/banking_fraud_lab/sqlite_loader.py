"""SQLite loading utilities for generated banking fraud lab datasets."""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from banking_fraud_lab.generators import (
    build_learner_facing_views,
    generate_minimal_banking_world,
)
from banking_fraud_lab.schema import (
    COLUMN_NAMES,
    TABLE_NAMES,
    TABLE_SPECS,
)

SQLITE_TYPES = {
    "string": "TEXT",
    "datetime64[ns]": "TEXT",
    "int64": "INTEGER",
    "bool": "INTEGER",
    "Decimal": "NUMERIC",
}


def create_minimal_banking_world_sqlite(
    database: str | Path | sqlite3.Connection,
    *,
    seed: int = 42,
    learner_facing: bool = True,
    replace: bool = True,
) -> sqlite3.Connection:
    """Generate the minimal banking world and load it into a SQLite database."""
    tables = generate_minimal_banking_world(seed=seed)
    if learner_facing:
        tables = build_learner_facing_views(tables)
    return load_tables_to_sqlite(tables, database, replace=replace)


def load_tables_to_sqlite(
    tables: Mapping[str, pd.DataFrame],
    database: str | Path | sqlite3.Connection,
    *,
    replace: bool = True,
) -> sqlite3.Connection:
    """Load generated tables into SQLite using the project schema contract."""
    _validate_tables(tables)
    connection, owns_connection = _connect(database)
    table_order = _ordered_table_names(tuple(tables))

    try:
        connection.execute("PRAGMA foreign_keys = ON")
        if replace:
            _drop_tables(connection, table_order)
        _create_tables(connection, table_order)
        _insert_tables(connection, tables, table_order)
        connection.commit()
    except Exception:
        connection.rollback()
        if owns_connection:
            connection.close()
        raise

    return connection


def _connect(database: str | Path | sqlite3.Connection) -> tuple[sqlite3.Connection, bool]:
    if isinstance(database, sqlite3.Connection):
        return database, False

    if str(database) == ":memory:":
        return sqlite3.connect(":memory:"), True

    database_path = Path(database)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(database_path), True


def _validate_tables(tables: Mapping[str, pd.DataFrame]) -> None:
    unknown_tables = set(tables) - set(TABLE_SPECS)
    if unknown_tables:
        raise ValueError(f"Unknown generated tables: {sorted(unknown_tables)}")

    for table_name, frame in tables.items():
        expected_columns = COLUMN_NAMES[table_name]
        if tuple(frame.columns) != expected_columns:
            raise ValueError(
                f"{table_name} columns do not match schema contract: "
                f"expected {expected_columns}, got {tuple(frame.columns)}"
            )


def _ordered_table_names(table_names: tuple[str, ...]) -> tuple[str, ...]:
    requested_tables = set(table_names)
    ordered: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(table_name: str) -> None:
        if table_name in visited:
            return
        if table_name in visiting:
            raise ValueError(f"Cyclic table dependency involving {table_name}")

        visiting.add(table_name)
        for column in TABLE_SPECS[table_name].columns:
            if column.references is None:
                continue
            parent_table = column.references.split(".", maxsplit=1)[0]
            if parent_table in requested_tables:
                visit(parent_table)
        visiting.remove(table_name)
        visited.add(table_name)
        ordered.append(table_name)

    for table_name in TABLE_NAMES:
        if table_name in requested_tables:
            visit(table_name)

    return tuple(ordered)


def _drop_tables(connection: sqlite3.Connection, table_order: tuple[str, ...]) -> None:
    for table_name in reversed(table_order):
        connection.execute(f"DROP TABLE IF EXISTS {_quote_identifier(table_name)}")


def _create_tables(connection: sqlite3.Connection, table_order: tuple[str, ...]) -> None:
    for table_name in table_order:
        table_spec = TABLE_SPECS[table_name]
        column_definitions = [
            _sqlite_column_definition(column.name, column.dtype, column.nullable)
            for column in table_spec.columns
        ]
        primary_key_column = table_spec.columns[0].name
        constraints = [f"PRIMARY KEY ({_quote_identifier(primary_key_column)})"]
        constraints.extend(_foreign_key_constraints(table_name))
        definition_sql = ",\n  ".join((*column_definitions, *constraints))
        connection.execute(
            f"CREATE TABLE {_quote_identifier(table_name)} (\n  {definition_sql}\n)"
        )


def _sqlite_column_definition(column_name: str, dtype: str, nullable: bool) -> str:
    sqlite_type = SQLITE_TYPES[dtype]
    nullability = "" if nullable else " NOT NULL"
    return f"{_quote_identifier(column_name)} {sqlite_type}{nullability}"


def _foreign_key_constraints(table_name: str) -> tuple[str, ...]:
    constraints = []
    for column in TABLE_SPECS[table_name].columns:
        if column.references is None:
            continue
        parent_table, parent_column = column.references.split(".", maxsplit=1)
        constraints.append(
            "FOREIGN KEY "
            f"({_quote_identifier(column.name)}) "
            f"REFERENCES {_quote_identifier(parent_table)}({_quote_identifier(parent_column)})"
        )
    return tuple(constraints)


def _insert_tables(
    connection: sqlite3.Connection,
    tables: Mapping[str, pd.DataFrame],
    table_order: tuple[str, ...],
) -> None:
    for table_name in table_order:
        frame = tables[table_name]
        if frame.empty:
            continue
        columns = COLUMN_NAMES[table_name]
        quoted_columns = ", ".join(_quote_identifier(column_name) for column_name in columns)
        placeholders = ", ".join("?" for _ in columns)
        rows = [
            tuple(_sqlite_value(value) for value in row)
            for row in frame.itertuples(index=False, name=None)
        ]
        connection.executemany(
            f"INSERT INTO {_quote_identifier(table_name)} "
            f"({quoted_columns}) VALUES ({placeholders})",
            rows,
        )


def _sqlite_value(value: Any) -> Any:
    if value is None:
        return None
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat(sep=" ")
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, np.bool_ | bool):
        return int(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    return value


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'
