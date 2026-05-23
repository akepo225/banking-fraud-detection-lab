"""Tests for loading generated banking data into SQLite."""

from pathlib import Path

import sqlite3

import pytest

from banking_fraud_lab import (
    create_minimal_banking_world_sqlite,
    generate_minimal_banking_world,
    load_tables_to_sqlite,
)
from banking_fraud_lab.schema import (
    LEARNER_FACING_TABLE_NAMES,
    PROTECTED_SCENARIO_ANSWER_KEYS,
    TABLE_NAMES,
)

EXAMPLE_SQL_FILES = (
    Path("sql/examples/00_smoke_tables.sql"),
    Path("sql/examples/01_alert_lifecycle_join.sql"),
    Path("sql/examples/02_alert_review_window.sql"),
)


def test_generated_tables_can_be_loaded_into_sqlite_database(tmp_path: Path) -> None:
    """The loader must create a local SQLite database containing generated tables."""
    tables = generate_minimal_banking_world(seed=42)
    connection = load_tables_to_sqlite(tables, tmp_path / "full_world.sqlite")

    try:
        assert _sqlite_table_names(connection) == set(TABLE_NAMES)
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        transaction_count = connection.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        assert transaction_count == len(tables["transactions"])
    finally:
        connection.close()


def test_sqlite_schema_includes_core_foreign_key_relationships(tmp_path: Path) -> None:
    """SQLite tables must preserve schema relationships needed by SQL exercises."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )

    try:
        alert_foreign_keys = _foreign_keys_for_table(connection, "alerts")
        case_foreign_keys = _foreign_keys_for_table(connection, "cases")
        suspicious_activity_fk = (
            "suspicious_activity_id",
            "suspicious_activities",
            "suspicious_activity_id",
        )
        banking_relationship_fk = (
            "banking_relationship_id",
            "banking_relationships",
            "banking_relationship_id",
        )

        assert suspicious_activity_fk in alert_foreign_keys
        assert banking_relationship_fk in alert_foreign_keys
        assert ("alert_id", "alerts", "alert_id") in case_foreign_keys
    finally:
        connection.close()


def test_default_sqlite_database_is_learner_facing(tmp_path: Path) -> None:
    """Default SQLite creation should exclude protected scenario answer keys."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )

    try:
        assert _sqlite_table_names(connection) == set(LEARNER_FACING_TABLE_NAMES)
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in _sqlite_table_names(connection)
    finally:
        connection.close()


def test_replace_removes_protected_tables_when_switching_to_learner_facing(
    tmp_path: Path,
) -> None:
    """Replacing a full internal DB with learner-facing mode must remove protected tables."""
    database_path = tmp_path / "world.sqlite"
    full_connection = create_minimal_banking_world_sqlite(
        database_path,
        seed=42,
        learner_facing=False,
    )
    try:
        assert PROTECTED_SCENARIO_ANSWER_KEYS in _sqlite_table_names(full_connection)
    finally:
        full_connection.close()

    learner_connection = create_minimal_banking_world_sqlite(
        database_path,
        seed=42,
    )
    try:
        table_names = _sqlite_table_names(learner_connection)
        assert table_names == set(LEARNER_FACING_TABLE_NAMES)
        assert PROTECTED_SCENARIO_ANSWER_KEYS not in table_names
    finally:
        learner_connection.close()


def test_loader_rejects_active_transaction_without_foreign_keys() -> None:
    """Caller-owned active transactions must already have SQLite FK checks enabled."""
    connection = sqlite3.connect(":memory:")
    connection.execute("BEGIN")

    try:
        with pytest.raises(ValueError, match="foreign_keys"):
            load_tables_to_sqlite(generate_minimal_banking_world(seed=42), connection)
        assert connection.in_transaction
    finally:
        connection.rollback()
        connection.close()


def test_loader_preserves_caller_owned_transaction_control() -> None:
    """Caller-owned connections keep transaction ownership after table loading."""
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("BEGIN")

    try:
        load_tables_to_sqlite(generate_minimal_banking_world(seed=42), connection)

        assert connection.in_transaction
        assert _sqlite_table_names(connection) == set(TABLE_NAMES)

        connection.rollback()
        assert _sqlite_table_names(connection) == set()
    finally:
        if connection.in_transaction:
            connection.rollback()
        connection.close()


def test_representative_sql_examples_execute_successfully(tmp_path: Path) -> None:
    """Learner SQL examples must run against the generated SQLite database."""
    connection = create_minimal_banking_world_sqlite(
        tmp_path / "learner_world.sqlite",
        seed=42,
    )

    try:
        for sql_file in EXAMPLE_SQL_FILES:
            rows = connection.execute(sql_file.read_text(encoding="utf-8")).fetchall()
            assert rows, f"{sql_file} returned no rows"
    finally:
        connection.close()


def _sqlite_table_names(connection: sqlite3.Connection) -> set[str]:
    """Return table names present in the SQLite database."""
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
    ).fetchall()
    return {str(row[0]) for row in rows}


def _foreign_keys_for_table(
    connection: sqlite3.Connection, table_name: str
) -> set[tuple[str, str, str]]:
    """Return child column, parent table, and parent column for one SQLite table."""
    quoted_table_name = '"' + table_name.replace('"', '""') + '"'
    rows = connection.execute(
        "PRAGMA foreign_key_list(" + quoted_table_name + ")"
    ).fetchall()
    return {(str(row[3]), str(row[2]), str(row[4])) for row in rows}
