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
    """
    Create a minimal banking-fraud dataset and load it into the given SQLite database.
    
    Generate in-memory pandas DataFrame tables using the project's minimal banking world generator (seed controls randomness), optionally transform them into learner-facing views, and persist the tables into the provided SQLite target. Existing tables will be dropped and recreated when `replace` is True.
    
    Parameters:
        database (str | Path | sqlite3.Connection): Filesystem path, ":memory:", or an open SQLite connection to load the tables into.
        seed (int): Seed for the dataset generator to produce deterministic data.
        learner_facing (bool): If True, transform generated tables into learner-facing views before loading.
        replace (bool): If True, drop any existing tables for the same schema before creating and inserting new ones.
    
    Returns:
        sqlite3.Connection: An open SQLite connection to the database containing the loaded tables.
    """
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
    """
    Load a mapping of table DataFrames into a SQLite database according to the project schema contract.
    
    Parameters:
        tables (Mapping[str, pd.DataFrame]): Mapping from table name to pandas DataFrame. Each DataFrame is validated against the schema (names and order of columns).
        database (str | Path | sqlite3.Connection): Target SQLite database. May be a filesystem path, the special string ":memory:", or an existing sqlite3.Connection.
        replace (bool): If True, drop any existing tables that conflict with the provided tables before creating and inserting new data.
    
    Returns:
        sqlite3.Connection: An open SQLite connection to the target database (the same object passed in when a connection was provided).
    
    Notes:
        - The operation runs inside a transaction: the function commits on success, rolls back on failure, and re-raises the encountered exception.
        - If a connection is created by this function (e.g., when given a path or ":memory:"), it will be closed on error; an externally provided sqlite3.Connection will not be closed by this function on error.
    """
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
    """
    Normalize a SQLite target into an open sqlite3.Connection and a flag indicating ownership.
    
    Parameters:
        database (str | Path | sqlite3.Connection): Either an existing SQLite connection, the string ":memory:" for an in-memory database, or a filesystem path to a SQLite database file. If a path is provided, parent directories will be created if needed.
    
    Returns:
        tuple[sqlite3.Connection, bool]: A tuple of (connection, owns_connection). `owns_connection` is `False` when the input was an existing Connection, `True` when this function opened the connection.
    """
    if isinstance(database, sqlite3.Connection):
        return database, False

    if str(database) == ":memory:":
        return sqlite3.connect(":memory:"), True

    database_path = Path(database)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(database_path), True


def _validate_tables(tables: Mapping[str, pd.DataFrame]) -> None:
    """
    Validate that the provided mapping of DataFrames matches the module's schema contract.
    
    Parameters:
        tables (Mapping[str, pd.DataFrame]): Mapping from table name to its DataFrame. Keys must be known table names from TABLE_SPECS and each DataFrame's columns (in order) must exactly match COLUMN_NAMES[table_name].
    
    Raises:
        ValueError: If any table name is not defined in TABLE_SPECS, or if a DataFrame's columns do not exactly match the expected COLUMN_NAMES for that table.
    """
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
    """
    Produce a dependency-respecting ordering of the given table names suitable for table creation and row insertion.
    
    Parameters:
        table_names (tuple[str, ...]): Tuple of requested table names (in any order). Only tables present in this tuple are considered; dependencies on tables not requested are ignored.
    
    Returns:
        tuple[str, ...]: Ordered tuple where each table appears after any other requested tables it references.
    
    Raises:
        ValueError: If a cyclic dependency is detected among the requested tables.
    """
    requested_tables = set(table_names)
    ordered: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(table_name: str) -> None:
        """
        Ensure `table_name` and any parent tables it references are visited and appended to the dependency-ordered `ordered` list.
        
        Performs a depth-first traversal of parent-table references declared in `TABLE_SPECS` so that parent tables are added before their children. Raises a ValueError if a cyclic dependency is detected.
         
        Raises:
            ValueError: If a cyclic table dependency involving `table_name` is found.
        """
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
    """
    Drop the named tables from the SQLite connection in reverse dependency order.
    
    Each name in `table_order` is dropped in reverse sequence using a safe, quoted
    identifier; reversing the creation/insertion order ensures child tables are
    dropped before their parents to avoid foreign-key constraint issues.
    
    Parameters:
        table_order (tuple[str, ...]): Table names in dependency-respecting creation
            order; tables will be dropped in the reverse of this sequence.
    """
    for table_name in reversed(table_order):
        connection.execute(f"DROP TABLE IF EXISTS {_quote_identifier(table_name)}")


def _create_tables(connection: sqlite3.Connection, table_order: tuple[str, ...]) -> None:
    """
    Create SQLite tables in the provided dependency order using the module's schema definitions.
    
    Each table is created according to TABLE_SPECS: columns are defined with their SQLite types and nullability, a single-column primary key is declared using the table's first column, and any foreign-key constraints declared in the schema are added. Identifiers are quoted when emitting the CREATE TABLE statements.
    
    Parameters:
        connection (sqlite3.Connection): An open SQLite connection used to execute DDL.
        table_order (tuple[str, ...]): Table names in dependency-respecting order (parents before children).
    """
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
    """
    Builds a SQLite column definition fragment for use in a CREATE TABLE statement.
    
    Parameters:
        column_name (str): Name of the column; will be safely quoted.
        dtype (str): Schema dtype key mapped to a SQLite type via the `SQLITE_TYPES` mapping.
        nullable (bool): Whether the column allows NULL values.
    
    Returns:
        str: A SQL fragment of the form `"<quoted_column>" <SQL_TYPE>[ NOT NULL]`.
    """
    sqlite_type = SQLITE_TYPES[dtype]
    nullability = "" if nullable else " NOT NULL"
    return f"{_quote_identifier(column_name)} {sqlite_type}{nullability}"


def _foreign_key_constraints(table_name: str) -> tuple[str, ...]:
    """
    Build FOREIGN KEY constraint clauses for the specified table using the module schema.
    
    Parameters:
        table_name (str): Name of a table present in TABLE_SPECS whose column `references`
            attributes will be turned into FOREIGN KEY constraints.
    
    Returns:
        tuple[str, ...]: SQL constraint fragments, each of the form
            `FOREIGN KEY ("child_col") REFERENCES "parent_table"("parent_col")`, with
            identifiers safely quoted.
    """
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
    """
    Insert rows from the given DataFrame mapping into the SQLite connection following the provided table order.
    
    Parameters:
        connection (sqlite3.Connection): Open SQLite connection where tables will be populated.
        tables (Mapping[str, pd.DataFrame]): Mapping from table name to DataFrame containing rows to insert. Each DataFrame's columns are inserted in the order defined by COLUMN_NAMES[table_name].
        table_order (tuple[str, ...]): Sequence of table names specifying the order to insert rows (dependencies first). Tables with empty DataFrames are skipped.
    
    Notes:
        Values are converted to SQLite-storable forms (e.g., NA/NaN to NULL, timestamps to ISO strings, Decimal to string, booleans to 0/1) before insertion.
    """
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
    """
    Normalize a Python or pandas scalar into a SQLite-storable value.
    
    Converts null-like values to None, pandas Timestamp to an ISO-formatted datetime string (space as separator), Decimal to its string representation, boolean and integer types to Python int, floating types to Python float, and returns other values unchanged.
    
    Parameters:
        value (Any): The input value to normalize.
    
    Returns:
        Any: `None` for SQL NULLs; ISO datetime string for `pd.Timestamp`; string for `Decimal`; `int` for boolean/integer types; `float` for floating types; otherwise the original value.
    """
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
    """
    Quote an SQLite identifier for safe inclusion in SQL statements.
    
    Parameters:
        identifier (str): Identifier (table or column name) to quote.
    
    Returns:
        quoted (str): The identifier wrapped in double quotes with any internal double quotes escaped by doubling.
    """
    return '"' + identifier.replace('"', '""') + '"'
